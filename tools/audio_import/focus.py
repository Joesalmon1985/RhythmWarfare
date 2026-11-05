"""Which voice is the player's at each moment (the focus), decided from the separated stems (format v2).

1. Loudness as heard. Each voice is weighted by half the A-weighting curve in dB (about the ear's equal-loudness
   contour at loud listening levels, ISO 226 near 80 phon: -15 dB at 50 Hz, -10 dB at 100 Hz, 0 at 1 kHz,
   +0.6 dB at 3 kHz), so the sub-bass, which carries most of the power in this music, does not win by power
   alone. Per bar, each voice's share of the summed weighted power of the voices is its perceived share.
2. Units. Each section is cut into 8-bar phrases from its first bar (a remainder under 4 bars joins the phrase
   before it), so stretches start and end on the phrase lines the sections sit on.
3. Prominence per unit and voice (in dB): 10 log10(perceived share), plus up to ACT_DB for how busy the part
   is (playable events per beat, full at one a beat), plus up to MOTION_DB for movement (the share of
   consecutive events that change height: another pitch, or another drum sound), plus ENTRY_DB if the voice
   has just come in (at least 10 dB louder than in the unit before). A voice is eligible only with a perceived
   share of at least MIN_SHARE (never a barely audible voice) and at least half a playable event per bar on
   average, sounding (an event starting, or a held note running on) in at least half of the unit's bars
   (enough to make a part; a bass of long held notes counts).
4. Stretches by dynamic programming over the units: every unit given to a voice costs how far its prominence
   is below the unit's leader; a stretch must cover at least min_bars bars; a change of voice costs
   SWITCH_DB (hysteresis: no flicker on small differences); a unit with an eligible voice left without focus
   costs GAP_DB; and every further unit a stretch keeps while another eligible voice is within CLOSE_DB of it
   costs FATIGUE_DB, so where two voices are close for a long time (a drop where drums and bass both drive)
   the focus is handed between them phrase by phrase, and where one voice clearly leads it keeps it.
   Units with no eligible voice are gaps (nothing to play).
5. Overrides: a fixed voice for the whole track, or a voice (or none) for a section id or a time range.

Rules added so that there is always something to play where there is music (version 0.3):
6. Fallback where nobody is eligible. A unit where no voice passes step 3 (a breakdown on held strings, say)
   is judged again with relaxed rules: a voice with at least RELAXED_MIN_SHARE of the perceived power whose
   level in the unit is no more than FLOOR_DB under the loudest unit of the whole recording (the floor on how
   quiet a focus voice may be), counting as playable every event that is audible by level (MIN_REL_DB,
   MIN_OWN_DB in chart.py) and strong for that unit (at least RELAXED_LOCAL of the median strength of that
   voice's events there, and at least RELAXED_MIN_STRENGTH). Such a stretch is marked relaxed and the chart
   uses the same relaxed test for it (relaxed_playable()). Only units with no voice even then are gaps.
7. Separation. A voice whose stem separated badly (sep_quality under 0.85: its attacks follow the drum hits,
   or its envelope moves with another stem) loses up to SEP_DB of prominence, so a cleanly separated voice is
   preferred when the two are close.
8. Variety. Every unit a voice keeps the focus beyond MAX_RUN_BARS in one stretch costs LONG_DB when another
   voice is eligible there, so a voice that leads a whole drop hands over for a phrase. In a breakdown a drums
   voice loses BREAKDOWN_DRUMS_DB when a pitched voice is eligible there (the melody or the vocal is the part
   to play, not the ticking hats).
"""
from __future__ import annotations

import numpy as np

from audio_io import mono

MIN_SHARE = 0.10
MIN_EVENTS_PER_BAR = 0.5
PLAYABLE_STRENGTH = 0.25
ACT_DB = 3.0
MOTION_DB = 2.0
ENTRY_DB = 2.0
CLOSE_DB = 6.0
SWITCH_DB = 1.0
FATIGUE_DB = CLOSE_DB + 2 * SWITCH_DB
GAP_DB = 12.0
PHRASE_BARS = 8
INF = 1e9
RELAXED_MIN_SHARE = 0.20
RELAXED_LOCAL = 0.6
RELAXED_MIN_STRENGTH = 0.08
FLOOR_DB = 30.0
SEP_DB = 4.0
SEP_OK = 0.85
MAX_RUN_BARS = 24
LONG_DB = 12.0
BREAKDOWN_DRUMS_DB = 6.0


def relaxed_playable(evs: list) -> list:
    """Events of one voice in one unit (or stretch) that are playable under the relaxed rules (module doc, 6):
    audible by level, and strong for the place they are in."""
    from chart import MIN_OWN_DB, MIN_REL_DB
    lv = [e for e in evs if e.rel_db >= MIN_REL_DB and e.own_db >= MIN_OWN_DB]
    if not lv:
        return []
    ref = float(np.median([e.strength for e in lv])) or 1e-6
    return [e for e in lv if e.strength >= max(RELAXED_MIN_STRENGTH, RELAXED_LOCAL * ref)]


def sep_penalty(q: float | None) -> float:
    return 0.0 if q is None else SEP_DB * float(np.clip((SEP_OK - q) / 0.25, 0.0, 1.0))


def half_a_weight(f: np.ndarray) -> np.ndarray:
    """Magnitude response of half the A-weighting curve in dB (normalised to 0 dB at 1 kHz)."""
    f2 = np.asarray(f, float) ** 2
    ra = (12194.0 ** 2 * f2 ** 2) / ((f2 + 20.6 ** 2) * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2)) * (f2 + 12194.0 ** 2))
    return np.sqrt(ra / 0.79433)


def perceived_bar_power(x: np.ndarray, rate: int, edges: np.ndarray) -> np.ndarray:
    """Mean weighted power of mono x in each bar [edges[i], edges[i+1])."""
    m = mono(x).astype(np.float64)
    X = np.fft.rfft(m)
    X *= half_a_weight(np.fft.rfftfreq(len(m), 1.0 / rate))
    y = np.fft.irfft(X, len(m))
    c = np.concatenate([[0.0], np.cumsum(y * y)])
    a = np.clip((np.asarray(edges[:-1]) * rate).astype(int), 0, len(m))
    b = np.clip((np.asarray(edges[1:]) * rate).astype(int), 0, len(m))
    return (c[b] - c[a]) / np.maximum(b - a, 1)


def make_units(sections: list[dict], edges: np.ndarray, phrase: int = PHRASE_BARS) -> list[tuple[int, int]]:
    """(first bar, end bar) of every phrase unit."""
    nb = len(edges) - 1
    cuts = sorted({0, nb, *[int(np.argmin(np.abs(edges - s["start_s"]))) for s in sections]})
    units = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        if b <= a:
            continue
        starts = list(range(a, b, phrase))
        parts = [(s, min(s + phrase, b)) for s in starts]
        if len(parts) > 1 and parts[-1][1] - parts[-1][0] < phrase // 2:
            last = parts.pop()
            parts[-1] = (parts[-1][0], last[1])
        units.extend(parts)
    return units


def parse_overrides(specs: list[str], sections: list[dict], voices: list[str]) -> list[tuple[float, float, str | None]]:
    """'drop1=bass', '77.2-132.4=drums', 'breakdown1=none' -> (start_s, end_s, voice or None)."""
    out = []
    for spec in specs or []:
        where, _, who = spec.partition("=")
        who = who.strip()
        if who not in voices and who != "none":
            raise ValueError(f"focus override {spec!r}: voice must be one of {voices} or none")
        sec = next((s for s in sections if s["id"] == where.strip()), None)
        if sec:
            a, b = sec["start_s"], sec["end_s"]
        else:
            try:
                a, b = (float(v) for v in where.split("-"))
            except ValueError:
                raise ValueError(f"focus override {spec!r}: {where!r} is neither a section id "
                                 f"({[s['id'] for s in sections]}) nor a time range like 77.2-132.4") from None
        out.append((a, b, None if who == "none" else who))
    return out


def unit_table(power: dict[str, np.ndarray], events: dict[str, list], units: list[tuple[int, int]],
               edges: np.ndarray, beat_s: float, quality: dict[str, float] | None = None,
               kinds: dict[str, str] | None = None, sections: list[dict] | None = None) -> list[dict]:
    """Per unit and voice: perceived share, playable events, rate, motion, entry, prominence, eligibility
    (strict, else relaxed: module doc, 6 to 8)."""
    keys = list(power)
    P = np.array([power[k] for k in keys])
    quality = quality or {}
    kinds = kinds or {}
    loudest = 10 * np.log10(max(float(P.sum(0).max()) if P.size else 0.0, 1e-20))
    rows = []
    prev_db = None
    for (a, b) in units:
        t0, t1 = edges[a], edges[b]
        nbars = b - a
        beats = (t1 - t0) / beat_s
        pw = P[:, a:b].mean(1)
        share = pw / max(pw.sum(), 1e-20)
        lvl = 10 * np.log10(pw + 1e-20)
        role = None
        if sections:
            mid = (t0 + t1) / 2
            role = next((s["role"] for s in sections if s["start_s"] <= mid < s["end_s"]), None)
        row = {"bars": [a, b], "start_s": float(t0), "end_s": float(t1), "role": role, "voices": {}}

        def judge(pl):
            # a bar counts as played if a playable event starts in it or a held note runs through it
            covered = np.zeros(nbars, bool)
            for e in pl:
                i0 = int(np.searchsorted(edges, e.t, side="right")) - 1
                i1 = int(np.searchsorted(edges, e.t + max(e.length, 0.0), side="left"))
                covered[max(i0 - a, 0):min(i1 - a, nbars)] = True
            return len(pl) >= MIN_EVENTS_PER_BAR * nbars and covered.sum() >= nbars / 2

        for i, k in enumerate(keys):
            inside = [e for e in events.get(k, []) if t0 <= e.t < t1]
            pl = [e for e in inside if e.audible and e.strength >= PLAYABLE_STRENGTH]
            strict = share[i] >= MIN_SHARE and judge(pl)
            relaxed = False
            if not strict and share[i] >= RELAXED_MIN_SHARE and lvl[i] >= loudest - FLOOR_DB:
                rp = relaxed_playable(inside)
                if judge(rp):
                    relaxed, pl = True, rp
            hs = [e.height for e in pl if np.isfinite(e.height)]
            motion = float(np.mean(np.abs(np.diff(hs)) >= 0.5)) if len(hs) > 2 else 0.0
            rate = len(pl) / max(beats, 1e-9)
            entry = prev_db is not None and lvl[i] >= prev_db[i] + 10.0
            pen = sep_penalty(quality.get(k))
            score = (10 * np.log10(max(share[i], 1e-6)) + ACT_DB * min(1.0, rate) + MOTION_DB * motion
                     + (ENTRY_DB if entry else 0.0) - pen)
            row["voices"][k] = {"share": round(float(share[i]), 3), "events": len(pl), "rate": round(rate, 2),
                                "motion": round(motion, 2), "entry": bool(entry), "score": round(float(score), 2),
                                "eligible": bool(strict), "relaxed": relaxed, "sep_penalty": round(pen, 2)}
        # relaxed eligibility only counts where no voice is eligible by the strict rules
        if not any(v["eligible"] for v in row["voices"].values()):
            for v in row["voices"].values():
                v["eligible"] = v["relaxed"]
        else:
            for v in row["voices"].values():
                v["relaxed"] = False
        # a breakdown: a pitched voice is the part to play rather than ticking drums
        if role == "breakdown" and any(v["eligible"] and kinds.get(k, "drums") != "drums"
                                       for k, v in row["voices"].items()):
            for k, v in row["voices"].items():
                if kinds.get(k) == "drums":
                    v["score"] = round(v["score"] - BREAKDOWN_DRUMS_DB, 2)
                    v["breakdown_penalty"] = BREAKDOWN_DRUMS_DB
        prev_db = lvl
        rows.append(row)
    return rows


def decide(rows: list[dict], keys: list[str], min_bars: int = 8, fixed: str | None = None,
           overrides: list[tuple[float, float, str | None]] | None = None) -> list[str | None]:
    """The voice (or None) of every unit, by the dynamic programme of the module doc."""
    U = len(rows)
    states = [*keys, None]
    cost = np.zeros((U, len(states)))
    close = np.zeros((U, len(states)))
    others = np.zeros((U, len(states)))  # another voice is eligible in the unit
    for u, r in enumerate(rows):
        el = {k: v for k, v in r["voices"].items() if v["eligible"]}
        top = max((v["score"] for v in el.values()), default=0.0)
        forced = None
        mid = (r["start_s"] + r["end_s"]) / 2
        if fixed is not None:
            forced = fixed if r["voices"][fixed]["events"] >= 4 else "none"
        for a, b, who in overrides or []:
            if a <= mid < b:
                forced = "none" if who is None or r["voices"][who]["events"] < 4 else who
        for s, k in enumerate(states):
            if forced is not None:
                cost[u, s] = 0.0 if (k == forced or (k is None and forced == "none")) else INF
                continue
            if k is None:
                cost[u, s] = GAP_DB if el else 0.0
            elif k in el:
                # a tiny tie-break: the earlier unit of a close pair goes to the leader
                cost[u, s] = (top - el[k]["score"]) * (1 + 1e-4 * (U - u))
                close[u, s] = float(any(w != k and el[w]["score"] >= el[k]["score"] - CLOSE_DB for w in el))
                others[u, s] = float(any(w != k for w in el))
            else:
                cost[u, s] = INF
    bars = [r["bars"][1] - r["bars"][0] for r in rows]
    min_bars = max(2, int(min_bars))

    def solve(min_b):
        best = np.full((U + 1, len(states)), INF)
        back: dict = {}
        best[0, len(states) - 1] = 0.0  # start as if after a gap
        for i in range(1, U + 1):
            for j in range(i - 1, -1, -1):
                nb = sum(bars[j:i])
                for s, k in enumerate(states):
                    if k is not None and nb < min_b:
                        continue
                    seg = cost[j:i, s].sum()
                    if seg >= INF:
                        continue
                    if k is not None:
                        seg += FATIGUE_DB * close[j + 1:i, s].sum()
                        run = np.cumsum([0, *bars[j:i - 1]])  # bars held before each unit of the stretch
                        seg += LONG_DB * float(sum(others[j + q, s] for q in range(i - j) if run[q] >= MAX_RUN_BARS))
                    for p in range(len(states)):
                        if (p == s and j > 0) or best[j, p] >= INF:
                            continue
                        c = best[j, p] + seg + (SWITCH_DB if (k is not None and states[p] is not None) else 0.0)
                        if c < best[i, s] - 1e-12:
                            best[i, s] = c
                            back[(i, s)] = (j, p)
        return best, back

    best, back = solve(min_bars)
    if best[U].min() >= INF:  # forced pieces shorter than the minimum: allow single units
        best, back = solve(2)
    s = int(np.argmin(best[U]))
    out: list[str | None] = [None] * U
    i = U
    while i > 0:
        j, p = back[(i, s)]
        for u in range(j, i):
            out[u] = states[s]
        i, s = j, p
    return out


def stretches(rows: list[dict], choice: list[str | None], fixed: str | None,
              overrides: list | None, sections: list[dict]) -> tuple[list[dict], list[dict]]:
    """Merge consecutive units of one voice into stretches; each with why it went to its voice."""
    out, gaps = [], []
    u = 0
    while u < len(rows):
        k = choice[u]
        v = u
        while v + 1 < len(rows) and choice[v + 1] == k:
            v += 1
        a, b = rows[u]["start_s"], rows[v]["end_s"]
        secs = [s["id"] for s in sections if min(b, s["end_s"]) - max(a, s["start_s"]) > 0.5]
        if k is None:
            gaps.append({"start_s": round(a, 4), "end_s": round(b, 4), "bars": rows[v]["bars"][1] - rows[u]["bars"][0],
                         "bar_range": [rows[u]["bars"][0], rows[v]["bars"][1]],
                         "sections": secs,
                         "why": "forced" if (fixed or overrides) and any(
                             any(r["voices"][x]["eligible"] for x in r["voices"]) for r in rows[u:v + 1])
                         else "no voice loud enough with a playable part, even by the relaxed rules"})
        else:
            reasons = []
            for r in rows[u:v + 1]:
                vv = r["voices"]
                el = {x: y for x, y in vv.items() if y["eligible"]}
                lead = max(el, key=lambda x: el[x]["score"]) if el else None
                if not vv[k]["eligible"]:
                    reasons.append("forced")
                elif vv[k].get("relaxed"):
                    reasons.append("no voice passes the strict rules here; the most prominent audible one (relaxed rules)")
                elif lead == k:
                    second = max((x for x in el if x != k), key=lambda x: el[x]["score"], default=None)
                    if second is None:
                        reasons.append("only voice with a part")
                    else:
                        reasons.append(f"most prominent ({el[k]['score'] - el[second]['score']:.1f} dB over {second})")
                elif el[lead]["score"] - el[k]["score"] <= CLOSE_DB:
                    reasons.append(f"handed over from {lead} ({el[lead]['score'] - el[k]['score']:.1f} dB behind, within {CLOSE_DB:.0f})")
                else:
                    reasons.append(f"{el[lead]['score'] - el[k]['score']:.1f} dB behind {lead}")
            if fixed or overrides:
                mids = [(r["start_s"] + r["end_s"]) / 2 for r in rows[u:v + 1]]
                if fixed or any(o[0] <= m < o[1] for m in mids for o in overrides or []):
                    reasons = [f"forced on the command line; automatic would say: {x}" for x in reasons]
            # perceived share over the stretch, weighted by bar count, and the runner-up
            w = np.array([r["bars"][1] - r["bars"][0] for r in rows[u:v + 1]], float)
            sh = {x: float(np.average([r["voices"][x]["share"] for r in rows[u:v + 1]], weights=w)) for x in rows[u]["voices"]}
            ru = max((x for x in sh if x != k), key=lambda x: sh[x], default=None)
            out.append({"start_s": round(a, 4), "end_s": round(b, 4), "voice": k,
                        "relaxed_spans": [[round(r["start_s"], 4), round(r["end_s"], 4)] for r in rows[u:v + 1]
                                          if r["voices"][k].get("relaxed")],
                        "bars": rows[v]["bars"][1] - rows[u]["bars"][0], "bar_range": [rows[u]["bars"][0], rows[v]["bars"][1]],
                        "sections": secs, "share": round(sh[k], 3), "runner_up": ru,
                        "runner_up_share": round(sh[ru], 3) if ru else None, "why": reasons})
        u = v + 1
    return out, gaps


def short_timeline(focus: list[dict], gaps: list[dict]) -> str:
    """'other 0-24, drums 24-32, (none) 32-40, ...' in bars from the first bar line."""
    items = [(f["bar_range"][0], f["bar_range"][1], f["voice"]) for f in focus]
    items += [(g["bar_range"][0], g["bar_range"][1], "(none)") for g in gaps]
    return ", ".join(f"{k} {a}-{b}" for a, b, k in sorted(items))
