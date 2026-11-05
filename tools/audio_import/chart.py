"""Stage 5: from each voice's audio to cues a player presses, as three nested charts (easy in normal in hard).

1. events(): what the voice plays. Onsets with strength, refined to the steepest energy rise; for sustained
   kinds (bass, melodic, vocal) also note changes heard as chroma changes, and the note length (how long the
   voice stays within 12 dB of the note's peak before the next note). Every event records how loud the voice is
   there and how loud the voice is against the whole recording, so cues never land where the voice is silent or
   buried.
2. rank(): a score per event: strength, audibility, metric position, and how regularly the same position in the
   2-bar cycle is played across the section (this is what makes patterns repeat when the music repeats). Drum
   events are labelled kick/snare/hat from band energy; the kit's backbone (kick and snare) ranks above hats.
3. select(): per section and voice, the strongest recurring positions (see pattern_pick) up to a budget that depends on the section role and
   difficulty, with a minimum spacing per voice. Hard is chosen from all events, normal from hard, easy from
   normal.
4. resolve(): all four pads together obey the contract's playability rules (checked by the validator's own
   rule function); a conflict keeps the higher-ranked cue, and holds are shortened (or become taps) to make room.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from analysis import band_filter, onset_envelope, pick_onsets, refine_onset
from audio_io import db, frame_rms, mono
from validate_track import playability_violations

DIFFICULTIES = ("hard", "normal", "easy")
# total cues per beat over all four pads in a drop; other roles scale this down
BUDGET = {"hard": 1.3, "normal": 0.75, "easy": 0.4}
ROLE_FACTOR = {"drop": 1.0, "build": 0.7, "other": 0.6, "breakdown": 0.5, "intro": 0.45, "outro": 0.45}
# per voice: max cues per beat and minimum spacing in beats, per difficulty
VOICE_CAP = {"hard": 0.9, "normal": 0.5, "easy": 0.25}
MIN_GAP = {"hard": 0.5, "normal": 0.5, "easy": 1.0}
PRIORITY = {"drums": 2.2, "bass": 1.1, "vocal": 0.9, "melodic": 0.9}
SNAP_MS = 6.0          # an event this close to a 16th grid line is placed on the line
MIN_REL_DB = -24.0     # voice level within 24 dB of the whole recording at the event
MIN_OWN_DB = -30.0     # and within 30 dB of the voice's own loud level
MIN_ATTACK = 0.4       # melodic/vocal onsets weaker than this (flux / the voice's 99th pct) are not cued: on
                       # Go Back only 14-27% of those below 0.3 were confirmed by an independent onset detector,
                       # 70-98% of those at 0.4 and above
HOLD_MIN_BEATS = 1.0   # a sustained note becomes a hold only if it lasts at least a beat


@dataclass
class Grid:
    bpm: float
    first_downbeat: float
    beats_per_bar: int = 4
    beats: np.ndarray | None = None  # explicit beat times when the tempo is not constant

    @property
    def beat_s(self) -> float:
        return 60.0 / self.bpm

    def position(self, t: np.ndarray) -> np.ndarray:
        """Beats since the first downbeat (float)."""
        if self.beats is not None and len(self.beats) > 1:
            k = np.interp(t, self.beats, np.arange(len(self.beats)), left=np.nan, right=np.nan)
            lo = (t - self.beats[0]) / self.beat_s
            hi = len(self.beats) - 1 + (t - self.beats[-1]) / self.beat_s
            k = np.where(t < self.beats[0], lo, np.where(t > self.beats[-1], hi, k))
            d0 = (self.first_downbeat - self.beats[0]) / self.beat_s
            return k - round(d0)
        return (np.asarray(t) - self.first_downbeat) / self.beat_s

    def time_of(self, pos: np.ndarray) -> np.ndarray:
        if self.beats is not None and len(self.beats) > 1:
            d0 = round((self.first_downbeat - self.beats[0]) / self.beat_s)
            k = np.asarray(pos, dtype=float) + d0
            n = len(self.beats) - 1
            inside = np.interp(k, np.arange(n + 1), self.beats)
            return np.where(k < 0, self.beats[0] + k * self.beat_s,
                            np.where(k > n, self.beats[-1] + (k - n) * self.beat_s, inside))
        return self.first_downbeat + np.asarray(pos) * self.beat_s


@dataclass
class Event:
    t: float
    strength: float
    rel_db: float
    own_db: float
    length: float = 0.0
    kind: str = ""          # kick / snare / hat for drums, onset / change for others
    pos: float = 0.0        # beats since the first downbeat, at the 16th it is nearest
    dev_ms: float = 0.0     # event minus that 16th, ms
    score: float = 0.0
    audible: bool = True
    extra: dict = field(default_factory=dict)


def _level(env_db: np.ndarray, hop_s: float, t: float, span: float) -> float:
    a = int(t / hop_s)
    b = max(a + 1, int((t + span) / hop_s))
    return float(env_db[a:b].max()) if a < len(env_db) else -200.0


def events(x: np.ndarray, mix: np.ndarray, rate: int, kind: str, grid: Grid) -> list[Event]:
    xm = mono(x).astype(np.float32)
    mm = mono(mix).astype(np.float32)
    env = onset_envelope(xm, rate)
    times, strength = pick_onsets(xm, rate, env=env, min_gap=0.06 if kind == "drums" else 0.09)
    hop_s = 0.005
    vdb = db(frame_rms(xm, rate, hop_s, 0.02))
    mdb = db(frame_rms(mm, rate, hop_s, 0.02))
    loud = float(np.percentile(vdb, 95))
    evs: list[Event] = []
    for t, s in zip(times, strength):
        lv = _level(vdb, hop_s, t, 0.06)
        lm = _level(mdb, hop_s, t, 0.06)
        evs.append(Event(t=float(t), strength=float(s), rel_db=lv - lm, own_db=lv - loud, kind="onset"))
    if kind == "drums":
        _label_drums(xm, rate, evs)
    elif kind == "bass":
        evs = bass_notes(xm, rate, times, vdb, mdb, loud, hop_s, grid)
    else:
        evs = _add_note_changes(xm, rate, evs, vdb, mdb, loud, hop_s, grid)
        _note_lengths(evs, vdb, hop_s, len(xm) / rate)
    pos = grid.position(np.array([e.t for e in evs])) if evs else np.array([])
    for e, p in zip(evs, pos):
        q = np.round(p * 4) / 4
        e.pos = float(q)
        e.dev_ms = float((p - q) * grid.beat_s * 1000)
        e.audible = e.rel_db >= MIN_REL_DB and e.own_db >= MIN_OWN_DB
        if kind in ("melodic", "vocal") and e.kind == "onset" and e.strength < MIN_ATTACK:
            e.audible = False  # sounding, but no clear attack to press on (filter movement inside a held sound)
    return evs


def _label_drums(xm: np.ndarray, rate: int, evs: list[Event]) -> None:
    """kick / snare / hat from the energy just after each hit in three bands, each relative to that band's
    loudest moment within 5 s (so a quieter intro kit is judged on its own terms). The 150-2500 Hz band holds
    the kick's body as well as the snare, so a kick is a hit whose sub band is near its local peak and not far
    below its body band; a snare is loud in both the body and the top; everything else is a hat or ghost."""
    from scipy.ndimage import maximum_filter1d
    bands = {"kick": (None, 150.0), "snare": (150.0, 2500.0), "hat": (5000.0, None)}
    hop = 0.005
    lv = {}
    for name, (lo, hi) in bands.items():
        e = db(frame_rms(band_filter(xm, rate, lo, hi), rate, hop, 0.03))
        ref = maximum_filter1d(e, size=int(10.0 / hop), mode="nearest")
        lv[name] = np.array([_level(e, hop, ev.t, 0.04) - ref[min(int(ev.t / hop), len(ref) - 1)] for ev in evs])
    for i, ev in enumerate(evs):
        k, s, h = lv["kick"][i], lv["snare"][i], lv["hat"][i]
        ev.extra = {"kick_db": round(float(k), 1), "snare_db": round(float(s), 1), "hat_db": round(float(h), 1)}
        if k > -10 and k - s > -8:
            ev.kind = "kick"
        elif s > -12 and h > -12:
            ev.kind = "snare"
        else:
            ev.kind = "hat"


def bass_notes(xm, rate, onsets, vdb, mdb, loud, hop_s, grid: Grid) -> list[Event]:
    """Notes of a bass line by pitch (pyin at 11 kHz, 23 ms frames), not by amplitude: a held sub or reese
    pumps with the kick's sidechain, and those swells are not notes. A note starts where the pitch moves by
    at least 0.75 semitone and stays there for 70 ms, or where the bass comes back after a rest; a glide
    counts once, at its start. The start is placed on an amplitude attack within 15 ms if there is one,
    else on the 16th line within 40 ms (a legato change has no edge), else where the pitch changed. Length
    runs to the next note or rest."""
    import librosa
    sr = 11025
    hop = 256
    y = librosa.resample(xm, orig_sr=rate, target_sr=sr)
    f0, voiced, _ = librosa.pyin(y, fmin=28, fmax=400, sr=sr, frame_length=2048, hop_length=hop)
    fr = hop / sr
    midi = librosa.hz_to_midi(np.where(voiced, f0, np.nan))
    lvl = np.array([_level(vdb, hop_s, k * fr, fr) for k in range(len(midi))])
    on = (lvl >= loud - 25) & ~np.isnan(midi)
    from scipy.ndimage import median_filter
    m = median_filter(np.nan_to_num(midi, nan=0.0), size=3)
    stable = int(round(0.07 / fr))
    notes = []  # [start_frame, end_frame, pitch]
    cur = None
    k = 0
    while k < len(m):
        if not on[k]:
            if cur:
                cur[1] = k
                notes.append(cur)
                cur = None
            k += 1
            continue
        if cur is None:
            cur = [k, k + 1, m[k]]
        else:
            ref = float(np.median(m[max(cur[0], k - 13):k]))  # the note's pitch over the last 0.3 s follows slow drift
            seg = m[k:k + stable]
            if (abs(m[k] - ref) >= 0.9 and len(seg) == stable and np.ptp(seg) < 0.75 and on[k:k + stable].all()
                    and abs(float(np.median(seg)) - ref) >= 0.9 and abs(m[min(k + 1, len(m) - 1)] - m[max(k - 2, 0)]) >= 0.9):
                cur[1] = k
                notes.append(cur)
                cur = [k, k + 1, float(np.median(seg))]
            # else a glide, a wobble or a detuned reese drifting: it stays inside the current note
        k += 1
    if cur:
        cur[1] = len(m)
        notes.append(cur)
    evs = []
    for a, b, p in notes:
        t = max(0.0, (a - 0.5) * fr)
        if (b - a) * fr < 0.06:
            continue
        near = onsets[np.abs(onsets - t) <= 0.015] if len(onsets) else []
        if len(near):
            t = float(near[np.argmin(np.abs(near - t))])
        else:
            q = round(grid.position(np.array([t]))[0] * 4) / 4
            tq = float(grid.time_of(np.array([q]))[0])
            if abs(tq - t) <= 0.04:
                t = tq
        lv = _level(vdb, hop_s, t, 0.08)
        lm = _level(mdb, hop_s, t, 0.08)
        e = Event(t=t, strength=float(np.clip((lv - loud + 20) / 20, 0, 1.2)), rel_db=lv - lm, own_db=lv - loud,
                  kind="note", length=float(b * fr - t))
        e.extra["pitch"] = round(float(p), 1)
        evs.append(e)
    return evs


def _add_note_changes(xm, rate, evs, vdb, mdb, loud, hop_s, grid: Grid) -> list[Event]:
    """Legato note changes have no attack: add chroma-change peaks that are not near an onset, placed on the
    nearest 16th when within 40 ms of it (the change itself has no sharp edge to place it on)."""
    import librosa
    hop = 1024
    C = librosa.feature.chroma_stft(y=xm, sr=rate, n_fft=8192, hop_length=hop)
    e = np.sqrt((C ** 2).sum(0)) + 1e-9
    Cn = C / e
    nov = np.r_[0.0, 1.0 - (Cn[:, 1:] * Cn[:, :-1]).sum(0)]
    nov = np.convolve(nov, np.ones(3) / 3, mode="same")
    fps = rate / hop
    rms = librosa.feature.rms(y=xm, frame_length=2048, hop_length=hop)[0]
    nov[db(rms) < loud - 25] = 0.0
    pk = librosa.util.peak_pick(nov, pre_max=4, post_max=4, pre_avg=12, post_avg=4,
                                delta=max(0.05, float(np.percentile(nov, 90))), wait=int(0.15 * fps))
    ts = np.array([e.t for e in evs])
    out = list(evs)
    for k in pk:
        t = k / fps
        if len(ts) and np.min(np.abs(ts - t)) < 0.08:
            continue
        p = grid.position(np.array([t]))[0]
        q = round(p * 4) / 4
        tq = float(grid.time_of(np.array([q]))[0])
        if abs(tq - t) < 0.04:
            t = tq
        lv = _level(vdb, hop_s, t, 0.06)
        lm = _level(mdb, hop_s, t, 0.06)
        out.append(Event(t=t, strength=float(min(1.0, nov[k] / (np.percentile(nov, 99) or 1.0))) * 0.8,
                         rel_db=lv - lm, own_db=lv - loud, kind="change"))
    out.sort(key=lambda e: e.t)
    return out


def _note_lengths(evs: list[Event], vdb: np.ndarray, hop_s: float, dur: float) -> None:
    for i, e in enumerate(evs):
        nxt = evs[i + 1].t if i + 1 < len(evs) else dur
        a = int(e.t / hop_s)
        b = max(a + 1, int(nxt / hop_s))
        seg = vdb[a:b]
        if not len(seg):
            continue
        peak = seg[: max(1, int(0.08 / hop_s))].max()
        below = np.nonzero(seg < peak - 12.0)[0]
        # ignore dips shorter than 40 ms
        end = len(seg)
        for j in below:
            if np.all(seg[j:j + int(0.04 / hop_s)] < peak - 12.0):
                end = j
                break
        e.length = float(end * hop_s)


# ---------------------------------------------------------------- ranking

def metric_weight(pos: float, dev_ms: float) -> float:
    if abs(dev_ms) > 40:
        return 0.3
    f = pos % 4
    if abs(f) < 1e-6:
        return 1.0
    if abs(f - 2) < 1e-6:
        return 0.9
    if abs(f - round(f)) < 1e-6:
        return 0.8
    if abs(f * 2 - round(f * 2)) < 1e-6:
        return 0.6
    return 0.4


def rank(evs: list[Event], kind: str, sections: list[dict], beats_per_bar: int = 4) -> None:
    """Score every event 0..1 (see module doc)."""
    if not evs:
        return
    s = np.array([e.strength for e in evs])
    r = np.array([e.rel_db for e in evs])
    s_pct = np.argsort(np.argsort(s)) / max(len(s) - 1, 1)
    r_pct = np.argsort(np.argsort(r)) / max(len(r) - 1, 1)
    cycle = 2 * beats_per_bar * 4  # 16ths in a 2-bar cycle
    sec_of = _section_index(evs, sections)
    recur = np.zeros(len(evs))
    for si in set(sec_of):
        idx = [i for i, x in enumerate(sec_of) if x == si]
        if not idx:
            continue
        slots = np.array([int(round(evs[i].pos * 4)) % cycle for i in idx])
        cycles = np.array([int(np.floor(evs[i].pos * 4 / cycle)) for i in idx])
        n_cycles = max(1, cycles.max() - cycles.min() + 1)
        hist = np.zeros(cycle)
        for sl, i in zip(slots, idx):
            hist[sl] += min(1.0, evs[i].strength) if evs[i].audible else 0.0
        hist = hist / n_cycles
        for sl, i in zip(slots, idx):
            recur[i] = min(1.0, hist[sl])
    prev_t = -10.0
    for i, e in enumerate(evs):
        m = metric_weight(e.pos, e.dev_ms)
        if kind == "drums":
            bonus = {"snare": 1.0, "kick": 0.7, "hat": 0.3}.get(e.kind, 0.5)
            score = 0.25 * s_pct[i] + 0.10 * r_pct[i] + 0.35 * recur[i] + 0.15 * m + 0.15 * bonus
        else:
            phrase = 1.0 if e.t - prev_t > 0.6 else 0.0
            held = min(1.0, e.length / 0.7)
            score = 0.30 * s_pct[i] + 0.15 * r_pct[i] + 0.25 * recur[i] + 0.10 * m + 0.10 * phrase + 0.10 * held
        if e.kind == "change":
            score *= 0.9
        e.score = float(score)
        e.extra["recur"] = round(float(recur[i]), 3)
        if e.audible:
            prev_t = e.t


def _section_index(evs: list[Event], sections: list[dict]) -> list[int]:
    out = []
    for e in evs:
        k = 0
        for i, s in enumerate(sections):
            if s["start_s"] <= e.t < s["end_s"]:
                k = i
                break
        out.append(k)
    return out


# ---------------------------------------------------------------- selection

@dataclass
class Cue:
    t: float
    pad: int
    dur: float
    conf: float
    score: float
    voice: str
    natural: float = 0.0  # note length before any shortening
    ev: Event | None = None
    prio: float = 0.0  # score weighted by the voice's priority: decides cross-pad conflicts

    def as_json(self) -> dict:
        return {"t": round(self.t, 4), "pad": self.pad, "dur": round(self.dur, 3), "conf": round(self.conf, 2)}


def cue_time(e: Event, grid: Grid) -> float:
    if abs(e.dev_ms) <= SNAP_MS:
        return float(grid.time_of(np.array([e.pos]))[0])
    return e.t


def confidence(e: Event, sep_quality: float) -> float:
    a = np.clip((e.rel_db - MIN_REL_DB) / 18.0, 0, 1)
    g = 1.0 if abs(e.dev_ms) <= 15 else 0.6
    return float(np.clip(0.15 + 0.3 * sep_quality + 0.25 * min(1.0, e.strength) + 0.2 * a + 0.1 * g, 0, 1))


CYCLE_BEATS = {"drums": 4, "bass": 8, "melodic": 16, "vocal": 16}


def pattern_pick(evs: list[Event], quota: int, gap_beats: float, cycle_beats: int, B: float) -> list[Event]:
    """Choose positions in the repeating cycle (2 bars for drums and bass, 4 bars for melodic and vocal parts),
    best first by how strongly and how regularly the part plays there (summed score / number of cycles), then
    take every event at those positions: the same pattern in every cycle where the part plays it. Positions
    closer than gap_beats (cyclically) are not combined. Leftover budget goes to the best remaining events
    (accents and one-off phrases), still keeping gap_beats between the voice's cues."""
    if quota <= 0 or not evs:
        return []
    n16 = cycle_beats * 4
    gap16 = int(round(gap_beats * 4))
    by_slot: dict[int, list[Event]] = {}
    for e in evs:
        by_slot.setdefault(int(round(e.pos * 4)) % n16, []).append(e)
    first = min(e.pos for e in evs)
    last = max(e.pos for e in evs)
    n_cycles = max(1.0, (last - first) / cycle_beats)
    slot_score = {sl: sum(e.score for e in es) / n_cycles for sl, es in by_slot.items()}
    chosen_slots: list[int] = []
    count = 0
    for sl in sorted(slot_score, key=lambda k: -slot_score[k]):
        if count >= quota:
            break
        if any(min((sl - c) % n16, (c - sl) % n16) < gap16 for c in chosen_slots):
            continue
        if count + len(by_slot[sl]) > quota * 1.2 and count > 0:
            continue
        chosen_slots.append(sl)
        count += len(by_slot[sl])
    picked: list[Event] = []
    for e in sorted((e for sl in chosen_slots for e in by_slot[sl]), key=lambda e: -e.score):
        if all(abs(e.t - p.t) >= gap_beats * B - 1e-6 for p in picked):
            picked.append(e)
    for e in sorted(evs, key=lambda e: -e.score):
        if len(picked) >= quota:
            break
        if e not in picked and all(abs(e.t - p.t) >= gap_beats * B - 1e-6 for p in picked):
            picked.append(e)
    return picked


def select(voice_events: dict[str, list[Event]], pads: dict[str, int], kinds: dict[str, str],
           sections: list[dict], grid: Grid, duration: float, sep_quality: dict[str, float],
           pool: dict[str, set] | None, diff: str) -> list[Cue]:
    """Pick cues per section and voice up to the budget, best score first, keeping the voice's own spacing.
    pool (voice -> event times allowed) restricts the choice to a harder chart's cues."""
    B = grid.beat_s
    chosen: list[Cue] = []
    for sec in sections:
        beats = (sec["end_s"] - sec["start_s"]) / B
        total = BUDGET[diff] * ROLE_FACTOR.get(sec["role"], 0.6) * beats
        avail = {}
        for v, evs in voice_events.items():
            ok = [e for e in evs if e.audible and sec["start_s"] <= e.t < sec["end_s"]
                  and 1.0 <= e.t <= duration - 0.6 and (pool is None or round(e.t, 4) in pool[v])]
            avail[v] = ok
        w = {v: PRIORITY.get(kinds[v], 1.0) * np.sqrt(len(ok) / max(beats, 1)) for v, ok in avail.items()}
        wsum = sum(w.values()) or 1.0
        for v, ok in avail.items():
            quota = int(round(min(total * w[v] / wsum, VOICE_CAP[diff] * beats)))
            for e in pattern_pick(ok, quota, MIN_GAP[diff], CYCLE_BEATS.get(kinds[v], 8), B):
                chosen.append(Cue(t=cue_time(e, grid), pad=pads[v], dur=0.0, conf=confidence(e, sep_quality.get(v, 0.5)),
                                  score=e.score, voice=v, natural=e.length, ev=e,
                                  prio=e.score * PRIORITY.get(kinds[v], 1.0)))
    chosen.sort(key=lambda c: (c.t, c.pad))
    return chosen


def resolve(cues: list[Cue], beat_s: float, duration: float, hold_kinds: set[str], kinds: dict[str, str]) -> list[Cue]:
    """Make the chart playable across all pads: taps first in score order, then holds as long as the rules and
    the note allow, then a final check with the validator's rule function, dropping the lowest-scored offender
    until there is nothing to drop."""
    B = beat_s
    keep: list[Cue] = []
    for c in sorted(cues, key=lambda c: -c.prio):
        c.dur = 0.0
        if not playability_violations([x.as_json() for x in sorted(keep + [c], key=lambda x: (x.t, x.pad))], 60.0 / B):
            keep.append(c)
    keep.sort(key=lambda c: (c.t, c.pad))
    # holds
    for i, c in enumerate(keep):
        if kinds.get(c.voice) not in hold_kinds or c.natural < HOLD_MIN_BEATS * B:
            continue
        limit = min(c.natural, duration - 0.5 - c.t)
        thumb = (c.pad - 1) // 2
        for d in keep[i + 1:]:
            if d.pad == c.pad:
                limit = min(limit, d.t - c.t - 0.25 * B - 0.005)
                break
        for d in keep[i + 1:]:
            if d.pad != c.pad and (d.pad - 1) // 2 == thumb:
                limit = min(limit, d.t - c.t - 0.005)
                break
        if limit >= max(0.5 * B, HOLD_MIN_BEATS * B * 0.75):
            c.dur = float(np.floor(limit * 100) / 100)
    for _ in range(len(keep) + 1):
        v = playability_violations([x.as_json() for x in keep], 60.0 / B)
        if not v:
            break
        idx = {i for (i, _msg) in v}
        worst = min(idx, key=lambda i: keep[i].prio)
        if keep[worst].dur > 0:
            keep[worst].dur = 0.0
        else:
            keep.pop(worst)
    return keep


def build_charts(voice_events: dict[str, list[Event]], pads: dict[str, int], kinds: dict[str, str],
                 sections: list[dict], grid: Grid, duration: float, sep_quality: dict[str, float]) -> dict[str, list[Cue]]:
    hold_kinds = {"bass", "melodic", "vocal"}
    charts: dict[str, list[Cue]] = {}
    pool = None
    for diff in DIFFICULTIES:
        cues = select(voice_events, pads, kinds, sections, grid, duration, sep_quality, pool, diff)
        cues = resolve(cues, grid.beat_s, duration, hold_kinds, kinds)
        charts[diff] = cues
        pool = {v: {round(c.ev.t, 4) for c in cues if c.voice == v} for v in voice_events}
    return charts
