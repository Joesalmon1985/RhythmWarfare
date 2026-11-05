"""Stage 4: how well each stem separated, which four parts become voices, and which pad each gets.

Every voice is built from the separated stems by complementary operations only (a stem as it is, a band split
whose two halves are x_low and x - x_low, a harmonic/percussive split whose halves are H and x - H, or the sum of
two stems), and the backing is the recording minus the four voices, so the pack is an exact partition of the
recording before encoding.
"""
from __future__ import annotations

import itertools

import numpy as np

from analysis import band_filter, onset_envelope, pick_onsets
from audio_io import db, frame_rms, mono

KIND_OF_STEM = {"drums": "drums", "bass": "bass", "vocals": "vocal", "other": "melodic", "guitar": "melodic",
                "piano": "melodic"}
LABELS = {"drums": "Drums", "bass": "Bass", "vocals": "Vocals", "other": "Synths", "guitar": "Guitar",
          "piano": "Keys", "kick": "Kick", "tops": "Tops", "lead": "Lead", "pads": "Pads"}


# ---------------------------------------------------------------- complementary splits

def split_band(x: np.ndarray, rate: int, fc: float) -> tuple[np.ndarray, np.ndarray]:
    low = np.stack([band_filter(x[:, c], rate, None, fc) for c in range(x.shape[1])], 1)
    return low, (x - low).astype(np.float32)


def split_hpss(x: np.ndarray, margin: float = 2.0) -> tuple[np.ndarray, np.ndarray]:
    import librosa
    out = []
    for c in range(x.shape[1]):
        S = librosa.stft(x[:, c], n_fft=4096, hop_length=1024)
        H, _ = librosa.decompose.hpss(S, margin=margin)
        out.append(librosa.istft(H, hop_length=1024, length=len(x)))
    h = np.stack(out, 1).astype(np.float32)
    return h, (x - h).astype(np.float32)


# ---------------------------------------------------------------- separation report

def stem_report(mix: np.ndarray, stems: dict[str, np.ndarray], rate: int, sections: list[dict] | None = None,
                drum_onsets: np.ndarray | None = None) -> dict:
    """Numbers behind the separation assessment.

    energy_share: stem energy / recording energy. active_share: share of 0.5 s frames where the stem is within
    25 dB of the recording and above its own -35 dB (re its 95th percentile). env_corr: correlation of 50 ms
    dB envelopes between stems (high positive = the same thing heard in two stems). band_leak: share of stem
    energy in a band it should not carry. transient_bleed: how much more of the stem's onset strength falls
    within 15 ms of strong drum hits than chance (1.0 = chance; drums leaking in, or a part locked to the
    kick). by_section: share of the recording's energy each stem carries in each section."""
    mm = mono(mix)
    tot = float((mix.astype(np.float64) ** 2).sum())
    resid = mix - sum(stems.values())
    rep: dict = {"residual_db": round(float(10 * np.log10((resid.astype(np.float64) ** 2).sum() / tot)), 1),
                 "stems": {}}
    mixf = db(frame_rms(mm, rate, 0.5))
    envs = {}
    for k, x in stems.items():
        xm = mono(x)
        f = db(frame_rms(xm, rate, 0.5))
        p95 = np.percentile(f, 95)
        act = (f > mixf - 25) & (f > p95 - 35)
        envs[k] = db(frame_rms(xm, rate, 0.05))
        spec = np.abs(np.fft.rfft(xm))
        freqs = np.fft.rfftfreq(len(xm), 1.0 / rate)
        p = spec ** 2
        ptot = p.sum() or 1.0
        bands = {"sub_lt60": float(p[freqs < 60].sum() / ptot), "low_60_250": float(p[(freqs >= 60) & (freqs < 250)].sum() / ptot),
                 "mid_250_2k": float(p[(freqs >= 250) & (freqs < 2000)].sum() / ptot),
                 "high_gt2k": float(p[freqs >= 2000].sum() / ptot)}
        rep["stems"][k] = {"energy_share": round(float((x.astype(np.float64) ** 2).sum() / tot), 4),
                           "active_share": round(float(act.mean()), 3),
                           "peak": round(float(np.abs(x).max()), 3),
                           "bands": {b: round(v, 3) for b, v in bands.items()}}
        del spec, p
    keys = list(stems)
    rep["env_corr"] = {f"{a}-{b}": round(float(np.corrcoef(envs[a], envs[b])[0, 1]), 3)
                       for a, b in itertools.combinations(keys, 2)}
    rep["wave_corr"] = {f"{a}-{b}": round(float(np.corrcoef(mono(stems[a]), mono(stems[b]))[0, 1]), 3)
                        for a, b in itertools.combinations(keys, 2)}
    if drum_onsets is not None and len(drum_onsets):
        dur = len(mm) / rate
        cover = min(1.0, len(drum_onsets) * 0.03 / dur)
        bleed = {}
        for k, x in stems.items():
            if k == "drums":
                continue
            env = onset_envelope(mono(x), rate)
            tt = np.arange(len(env)) * 256 / rate
            idx = np.searchsorted(drum_onsets, tt)
            near = np.minimum(np.abs(tt - drum_onsets[np.clip(idx, 0, len(drum_onsets) - 1)]),
                              np.abs(tt - drum_onsets[np.clip(idx - 1, 0, len(drum_onsets) - 1)])) < 0.015
            bleed[k] = round(float(env[near].sum() / (env.sum() or 1.0) / max(cover, 1e-6)), 2)
        rep["transient_bleed"] = bleed
    if sections:
        rep["by_section"] = {}
        for s in sections:
            a, b = int(s["start_s"] * rate), int(s["end_s"] * rate)
            t = float((mix[a:b].astype(np.float64) ** 2).sum()) or 1.0
            rep["by_section"][s["id"]] = {k: round(float((x[a:b].astype(np.float64) ** 2).sum() / t), 3)
                                          for k, x in stems.items()}
    return rep


def describe_stem(name: str, s: dict, rep: dict) -> str:
    """A musician's sentence from the numbers (the numbers stay in the report next to it)."""
    e, a, b = s["energy_share"], s["active_share"], s["bands"]
    parts = [f"carries {100 * e:.1f}% of the energy, sounding in {100 * a:.0f}% of the track"]
    corr = [(k, v) for k, v in rep["env_corr"].items() if name in k.split("-") and v > 0.5]
    if corr:
        parts.append("moves with " + ", ".join(k.replace(name, "").strip("-") for k, _ in corr) +
                     " (envelope correlation > 0.5: shared material or leakage)")
    bleed = rep.get("transient_bleed", {}).get(name)
    if name == "bass" and b["high_gt2k"] > 0.02:
        parts.append(f"some top end in the bass ({100 * b['high_gt2k']:.1f}% above 2 kHz: drum clicks or growl harmonics)")
    if name in ("vocals", "other") and b["sub_lt60"] > 0.05:
        parts.append(f"sub-bass leaking in ({100 * b['sub_lt60']:.1f}% below 60 Hz)")
    if name == "drums" and b["sub_lt60"] > 0.25:
        parts.append(f"heavy sub ({100 * b['sub_lt60']:.0f}% below 60 Hz: kick, or bass caught in the drums)")
    if bleed is not None:
        if bleed > 2.0:
            parts.append(f"its attacks line up with the drum hits {bleed:.1f}x more than chance (drum bleed or a part locked to the kit)")
        else:
            parts.append(f"little drum bleed (attack coincidence {bleed:.1f}x chance)")
    return "; ".join(parts) + "."


# ---------------------------------------------------------------- voice choice

def viable(s: dict) -> bool:
    return s["active_share"] >= 0.25 and s["energy_share"] >= 0.004


def choose_voices(mix: np.ndarray, stems: dict[str, np.ndarray], rate: int, rep: dict) -> dict:
    """Four voices and the backing from the stems, with the reasons.

    1. Stems that are active for at least a quarter of the track and carry at least 0.4% of the energy are
       candidates, best first by active share times sqrt(energy share). The best four become voices.
    2. If fewer than four qualify, split the strongest candidate that splits into two viable parts: drums into
       kick (below 150 Hz) and tops, then the melodic stem into harmonic (pads) and percussive (lead/stabs)
       halves. If still short, two weak stems are merged into one voice.
    3. Everything not in a voice (stems left over and the separation residual) is the backing."""
    st = rep["stems"]
    cand = sorted((k for k in stems if viable(st[k])),
                  key=lambda k: -st[k]["active_share"] * np.sqrt(st[k]["energy_share"]))
    reasons = {k: f"{k}: active {100 * st[k]['active_share']:.0f}%, energy {100 * st[k]['energy_share']:.1f}%"
               for k in stems}
    voices: dict[str, dict] = {}
    for k in cand[:4]:
        voices[k] = {"audio": stems[k], "from": [k], "op": "stem", "kind": KIND_OF_STEM.get(k, "melodic")}
    notes = [f"voice {k}: Demucs stem as it is ({reasons[k]})" for k in voices]
    splits = [("drums", "band", 150.0, ("kick", "tops")), ("other", "hpss", None, ("pads", "lead"))]
    for src, op, arg, names in splits:
        if len(voices) >= 4 or src not in voices:
            continue
        x = stems[src]
        a, b = split_band(x, rate, arg) if op == "band" else split_hpss(x)
        sub = stem_report(mix, {names[0]: a, names[1]: b}, rate)["stems"]
        if viable(sub[names[0]]) and viable(sub[names[1]]):
            kind = voices.pop(src)["kind"]
            voices[names[0]] = {"audio": a, "from": [src], "op": f"{op}_low" if op == "band" else "hpss_harmonic", "kind": kind}
            voices[names[1]] = {"audio": b, "from": [src], "op": f"{op}_high" if op == "band" else "hpss_percussive", "kind": kind}
            notes.append(f"split {src} into {names[0]} and {names[1]} ({op}): both halves active")
    if len(voices) < 4:
        weak = sorted((k for k in stems if k not in voices and not any(k in v["from"] for v in voices.values())),
                      key=lambda k: -st[k]["active_share"])
        if len(weak) >= 2:
            a, b = weak[:2]
            voices[f"{a}_{b}"] = {"audio": stems[a] + stems[b], "from": [a, b], "op": "merge", "kind": "melodic"}
            notes.append(f"merged weak stems {a} and {b} into one voice")
    used = {s for v in voices.values() for s in v["from"]}
    backing_from = [k for k in stems if k not in used]
    for k in backing_from:
        notes.append(f"backing gets {k} ({reasons[k]}; not chosen as a voice)")
    backing = mix - sum(v["audio"] for v in voices.values())
    return {"voices": voices, "backing": backing.astype(np.float32), "backing_from": backing_from + ["residual"],
            "notes": notes}


def co_occurrence(events: dict[str, np.ndarray], beat_s: float, window_beats: float = 0.5,
                  count: bool = False) -> dict[tuple, float]:
    """For each voice pair, how often one voice's events have an event of the other within window_beats: as the
    larger of the two shares (count=False), or as the larger of the two counts (count=True: the number of presses
    that could not both be kept if the two voices shared a thumb)."""
    out = {}
    for a, b in itertools.combinations(sorted(events), 2):
        ea, eb = np.sort(events[a]), np.sort(events[b])
        if not len(ea) or not len(eb):
            out[(a, b)] = 0.0
            continue
        def near(x, y):
            i = np.searchsorted(y, x)
            d = np.minimum(np.abs(x - y[np.clip(i, 0, len(y) - 1)]), np.abs(x - y[np.clip(i - 1, 0, len(y) - 1)]))
            hit = d < window_beats * beat_s
            return float(hit.sum() if count else hit.mean())
        out[(a, b)] = max(near(ea, eb), near(eb, ea))
    return out


ORDER = ("drums", "kick", "tops", "bass", "vocals", "other", "lead", "pads", "guitar", "piano")


def assign_pads(keys: list[str], co: dict[tuple, float]) -> tuple[dict[str, int], dict]:
    """Split the four voices into two thumbs so the pairs sharing a thumb clash least (co: pair -> overlap), then order: the thumb
    holding the first voice in ORDER is the left thumb, and within a thumb the earlier voice in ORDER is the
    outer pad (1 or 4 is 'outer' only in name; the order is just stable)."""
    def c(a, b):
        return co.get((a, b), co.get((b, a), 0.0))
    rank = {k: (ORDER.index(k) if k in ORDER else len(ORDER)) for k in keys}
    ks = sorted(keys, key=lambda k: rank[k])
    best = None
    for partner in ks[1:]:
        left = [ks[0], partner]
        right = [k for k in ks if k not in left]
        cost = c(*left) + c(*right)
        if best is None or cost < best[0]:
            best = (cost, left, right)
    cost, left, right = best
    left.sort(key=lambda k: rank[k])
    right.sort(key=lambda k: rank[k])
    pads = {left[0]: 1, left[1]: 2, right[0]: 3, right[1]: 4}
    pairs = {f"{a}+{b}": round(c(a, b), 3) for a, b in itertools.combinations(ks, 2)}
    return pads, {"same_thumb_cost": round(cost, 3), "pair_overlap": pairs,
                  "left_thumb": left, "right_thumb": right}
