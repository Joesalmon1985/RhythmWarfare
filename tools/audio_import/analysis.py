"""Stage 2 and 3: onsets, a constant-tempo grid fitted to the whole track, the downbeat, and sections.

Everything works on mono float arrays at one sample rate. Times are seconds from sample 0.
"""
from __future__ import annotations

import numpy as np

from audio_io import db, frame_rms, mono

HOP = 256  # onset envelope hop at 44.1 kHz = 5.8 ms


# ---------------------------------------------------------------- onsets

def band_filter(x: np.ndarray, rate: int, lo: float | None, hi: float | None) -> np.ndarray:
    """Zero-phase FFT brick band of mono x (only used for analysis, never for stems)."""
    if lo is None and hi is None:
        return x
    n = len(x)
    f = np.fft.rfftfreq(n, 1.0 / rate)
    X = np.fft.rfft(x)
    m = np.ones_like(f)
    if lo is not None:
        m *= 1.0 / (1.0 + (lo / np.maximum(f, 1e-3)) ** 8)
    if hi is not None:
        m *= 1.0 / (1.0 + (f / hi) ** 8)
    return np.fft.irfft(X * m, n).astype(np.float32)


def onset_envelope(x: np.ndarray, rate: int, hop: int = HOP, fmin: float | None = None,
                   fmax: float | None = None) -> np.ndarray:
    """Log-mel spectral flux (librosa), one value per hop, frame k centred at k*hop/rate."""
    import librosa
    kw = {}
    if fmin is not None:
        kw["fmin"] = fmin
    if fmax is not None:
        kw["fmax"] = fmax
    S = librosa.feature.melspectrogram(y=mono(x).astype(np.float32), sr=rate, n_fft=2048, hop_length=hop,
                                       n_mels=96, **kw)
    return librosa.onset.onset_strength(S=librosa.power_to_db(S, ref=1.0, top_db=None), sr=rate,
                                        hop_length=hop, lag=1, max_size=3)


def refine_onset(x: np.ndarray, rate: int, t: float, before: float = 0.035, after: float = 0.015) -> float:
    """Move a coarse onset time to the steepest rise of a 1 ms-hop, 3 ms-window log energy envelope nearby."""
    a = max(0, int((t - before - 0.005) * rate))
    b = min(len(x), int((t + after + 0.005) * rate))
    if b - a < int(0.01 * rate):
        return t
    seg = x[a:b].astype(np.float64)
    hop = max(1, rate // 1000)
    win = 3 * hop
    c = np.concatenate([[0.0], np.cumsum(seg * seg)])
    idx = np.arange(0, len(seg) - win, hop)
    e = 10 * np.log10((c[idx + win] - c[idx]) / win + 1e-12)
    if len(e) < 4:
        return t
    e = np.convolve(e, np.ones(3) / 3, mode="same")
    d = np.diff(e)
    k = int(np.argmax(d[1:-1])) + 1
    return (a + idx[k] + win) / rate


def pick_onsets(x: np.ndarray, rate: int, env: np.ndarray | None = None, hop: int = HOP, min_gap: float = 0.05,
                rel_delta: float = 0.08, refine: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Onset times (s) and strengths (envelope peak / the envelope's 99th percentile) of mono x."""
    import librosa
    if env is None:
        env = onset_envelope(x, rate, hop)
    scale = float(np.percentile(env, 99)) or 1.0
    fps = rate / hop
    w = lambda s: max(1, int(round(s * fps)))  # noqa: E731
    pk = librosa.util.peak_pick(env, pre_max=w(0.03), post_max=w(0.03), pre_avg=w(0.10), post_avg=w(0.03),
                                delta=rel_delta * scale, wait=w(min_gap))
    times = pk * hop / rate
    strength = env[pk] / scale
    if refine:
        xm = mono(x)
        times = np.array([refine_onset(xm, rate, t) for t in times])
    return times, strength


# ---------------------------------------------------------------- tempo and grid

def comb_score(t: np.ndarray, w: np.ndarray, bpms: np.ndarray, harmonics=(1, 2, 4)) -> np.ndarray:
    """Phase coherence of weighted onsets at the beat, 8th and 16th of each tempo (0 to 1)."""
    out = np.zeros(len(bpms))
    tot = w.sum() or 1.0
    for i in range(0, len(bpms), 512):
        f = bpms[i:i + 512, None] / 60.0
        s = 0.0
        for k in harmonics:
            s = s + np.abs((w[None] * np.exp(2j * np.pi * k * f * t[None])).sum(1)) / tot
        out[i:i + 512] = s / len(harmonics)
    return out


def tempo_candidates(t: np.ndarray, w: np.ndarray, lo: float = 60.0, hi: float = 200.0,
                     prefer: tuple[float, float] = (110.0, 200.0)) -> dict:
    """Best tempo in [lo, hi] by a coarse then fine comb sweep, with its half and double; picks the reading
    inside `prefer` (drum and bass is written at 160 to 180, felt in half time at 80 to 90)."""
    coarse = np.arange(lo, hi, 0.05)
    sc = comb_score(t, w, coarse)
    b0 = coarse[int(np.argmax(sc))]
    fine = np.arange(b0 - 0.1, b0 + 0.1, 0.001)
    b = float(fine[int(np.argmax(comb_score(t, w, fine)))])
    cands = {}
    for name, v in (("found", b), ("half", b / 2), ("double", b * 2)):
        cands[name] = {"bpm": round(v, 3), "score": round(float(comb_score(t, w, np.array([v]))[0]), 4)}
    chosen = next((c["bpm"] for c in cands.values() if prefer[0] <= c["bpm"] <= prefer[1]), b)
    return {"chosen_bpm": chosen, "candidates": cands}


def fit_grid(t: np.ndarray, w: np.ndarray, bpm: float, sub: int = 4, tol_s: float = 0.025,
             iters: int = 4) -> dict:
    """Weighted least-squares constant grid t = t0 + n * P/sub over every onset near a grid line.

    Returns bpm (float), t0 (time of some grid line, not yet the downbeat), residual statistics and the
    windowed drift of the onsets against the fitted grid."""
    P = 60.0 / bpm
    step = P / sub
    ph = np.angle((w * np.exp(2j * np.pi * t / step)).sum())
    t0 = (ph / (2 * np.pi)) * step % step
    keep = np.ones(len(t), bool)
    for _ in range(iters):
        n = np.round((t - t0) / step)
        dev = t - (t0 + n * step)
        keep = np.abs(dev) < tol_s
        if keep.sum() < 8:
            break
        A = np.stack([np.ones(keep.sum()), n[keep]], 1)
        sw = np.sqrt(w[keep])
        a, b = np.linalg.lstsq(A * sw[:, None], t[keep] * sw, rcond=None)[0]
        t0, step = float(a), float(b)
        tol_s = max(0.012, min(tol_s, 4 * float(np.sqrt(np.average(dev[keep] ** 2, weights=w[keep])))))
    n = np.round((t - t0) / step)
    dev = t - (t0 + n * step)
    keep = np.abs(dev) < max(tol_s, 0.02)
    bpm_fit = 60.0 / (step * sub)
    beat = step * sub
    # which of the `sub` grid lines in a beat is the beat: the one carrying the most onset weight
    ph = np.mod(n, sub).astype(int)
    load = np.array([w[keep & (ph == k)].sum() for k in range(sub)])
    t0 = (t0 + int(np.argmax(load)) * step) % beat
    # drift: the phase of the onsets against the fitted grid in 8-bar windows (circular mean at the grid-line
    # rate, unwrapped across windows, so a slow tempo slide shows even when it passes a whole 16th)
    win = 32 * beat
    drift = []
    if len(t):
        raw = []
        for s in np.arange(0, t.max() + 1e-9, win):
            m = (t >= s) & (t < s + win)
            if m.sum() < 8:
                continue
            z = (w[m] * np.exp(2j * np.pi * (t[m] - t0) / step)).sum()
            if abs(z) / w[m].sum() < 0.3:
                continue
            raw.append((s, np.angle(z), int(m.sum())))
        if raw:
            un = np.unwrap([r[1] for r in raw]) / (2 * np.pi) * step
            drift = [(round(float(r[0]), 2), round(1000 * float(u), 2), r[2]) for r, u in zip(raw, un)]
    half = len(t) // 2
    halves = []
    for m in (keep & (np.arange(len(t)) < half), keep & (np.arange(len(t)) >= half)):
        if m.sum() > 16:
            A = np.stack([np.ones(m.sum()), n[m]], 1)
            halves.append(60.0 / (np.linalg.lstsq(A, t[m], rcond=None)[0][1] * sub))
    dw = [d[1] for d in drift]
    return {
        "bpm": float(bpm_fit), "t0": float(t0), "beat_s": float(beat),
        "onsets_used": int(keep.sum()), "onsets_total": int(len(t)),
        "share_on_grid": round(float(w[keep].sum() / max(w.sum(), 1e-9)), 3),
        "residual_ms_median_abs": round(1000 * float(np.median(np.abs(dev[keep]))) if keep.any() else 0.0, 2),
        "residual_ms_rms": round(1000 * float(np.sqrt(np.average(dev[keep] ** 2, weights=w[keep]))) if keep.any() else 0.0, 2),
        "drift_windows_ms": drift,
        "drift_ms_max_abs": round(max((abs(x) for x in dw), default=0.0), 2),
        "drift_ms_first_last": [dw[0], dw[-1]] if dw else None,
        "bpm_first_half": round(halves[0], 4) if len(halves) == 2 else None,
        "bpm_second_half": round(halves[1], 4) if len(halves) == 2 else None,
    }


def constant_tempo_ok(grid: dict, tol_ms: float = 12.0) -> bool:
    return grid["drift_ms_max_abs"] <= tol_ms and grid["share_on_grid"] >= 0.5


def beat_strengths(env: np.ndarray, rate: int, hop: int, beats: np.ndarray, radius_s: float = 0.03) -> np.ndarray:
    fps = rate / hop
    r = max(1, int(radius_s * fps))
    out = np.zeros(len(beats))
    for i, b in enumerate(beats):
        k = int(round(b * fps))
        if 0 <= k < len(env):
            out[i] = env[max(0, k - r):k + r + 1].max()
    return out


def find_downbeat(beats: np.ndarray, kick: np.ndarray, snare: np.ndarray, energy_db: np.ndarray,
                  beats_per_bar: int = 4) -> dict:
    """Bar phase (index of the first downbeat among beats[0:4]).

    Two cues, both normalised: (1) phrase changes, i.e. jumps of energy summed over the next and previous
    bar, land on bar lines; (2) the kick lands on beat 1 more than the snare does (backbeat on 2 and 4)."""
    n = len(beats)
    B = beats_per_bar
    jump = np.zeros(n)
    for k in range(B, n - B):
        jump[k] = max(0.0, energy_db[k:k + B].mean() - energy_db[k - B:k].mean())
    jump = jump ** 2
    ks = kick / (kick.max() or 1.0) - snare / (snare.max() or 1.0)
    scores = []
    for p in range(B):
        idx = np.arange(p, n, B)
        scores.append((jump[idx].sum() / (jump.sum() or 1.0), ks[idx].mean()))
    sj = np.array([s[0] for s in scores])
    sk = np.array([s[1] for s in scores])
    sk = (sk - sk.min()) / ((sk.max() - sk.min()) or 1.0)
    total = 0.6 * sj / (sj.max() or 1.0) + 0.4 * sk
    order = np.argsort(-total)
    conf = float((total[order[0]] - total[order[1]]) / (total[order[0]] or 1.0))
    return {"phase": int(order[0]), "scores": [round(float(v), 3) for v in total],
            "jump_share": [round(float(v), 3) for v in sj], "kick_minus_snare": [round(float(v), 3) for v in sk],
            "confidence": round(conf, 3)}


# ---------------------------------------------------------------- sections

ROLES = ("intro", "build", "drop", "breakdown", "outro", "other")


def bar_levels(stems: dict[str, np.ndarray], rate: int, bars: np.ndarray) -> dict[str, np.ndarray]:
    """dB RMS of each stem in each bar [bars[i], bars[i+1])."""
    out = {}
    for k, x in stems.items():
        m = mono(x).astype(np.float64)
        c = np.concatenate([[0.0], np.cumsum(m * m)])
        a = np.clip((bars[:-1] * rate).astype(int), 0, len(m))
        b = np.clip((bars[1:] * rate).astype(int), 0, len(m))
        out[k] = db(np.sqrt((c[b] - c[a]) / np.maximum(b - a, 1)))
    return out


def segment(levels: dict[str, np.ndarray], bars: np.ndarray, min_bars: int = 8, kernel: int = 8,
            phrase: int = 8, rel_thresh: float = 0.25) -> list[int]:
    """Section boundaries (bar indices) from a checkerboard novelty on per-bar stem levels; boundaries that
    fall within 2 bars of an 8-bar phrase line move onto it."""
    keys = sorted(levels)
    F = np.stack([np.maximum(levels[k], levels[k].max() - 50.0) for k in keys], 1)
    F = (F - F.mean(0)) / (F.std(0) + 1e-6)
    nb = len(F)
    nov = np.zeros(nb)
    for i in range(1, nb):
        a = F[max(0, i - kernel):i].mean(0)
        b = F[i:min(nb, i + kernel)].mean(0)
        nov[i] = np.linalg.norm(a - b)
    thr = rel_thresh * nov.max()
    cand = [i for i in range(1, nb) if nov[i] >= thr and nov[i] == nov[max(1, i - min_bars // 2):i + min_bars // 2 + 1].max()]
    cand.sort(key=lambda i: -nov[i])
    chosen: list[int] = []
    for i in cand:
        j = i
        r = i % phrase
        if r <= 2:
            j = i - r
        elif phrase - r <= 2:
            j = i + phrase - r
        j = min(max(j, 1), nb - 1)
        if all(abs(j - c) >= min_bars for c in chosen) and j >= min_bars // 2 and nb - j >= min_bars // 2:
            chosen.append(j)
    return sorted(chosen)


def label_sections(levels: dict[str, np.ndarray], bounds: list[int], bars: np.ndarray,
                   drive_keys: tuple[str, ...]) -> list[dict]:
    """Roles from intensity: drive = mean dB of the rhythm stems (drums, bass) relative to their loudest bar.
    Loudest sections are drops; quiet ones after a drop and before another are breakdowns; the section right
    before a drop that is louder than the one before it is a build; quiet sections before the first drop are
    intro and after the last drop outro."""
    nb = len(bars) - 1
    edges = [0, *bounds, nb]
    keys = [k for k in drive_keys if k in levels] or list(levels)
    drive = np.mean([levels[k] - np.percentile(levels[k], 95) for k in keys], 0)
    secs = []
    for a, b in zip(edges[:-1], edges[1:]):
        secs.append({"bar_start": a, "bar_end": b, "intensity": float(np.median(drive[a:b]))})
    imax = max(s["intensity"] for s in secs)
    for s in secs:
        s["is_drop"] = s["intensity"] >= imax - 4.0
    drops = [i for i, s in enumerate(secs) if s["is_drop"]]
    first, last = (drops[0], drops[-1]) if drops else (len(secs), -1)
    for i, s in enumerate(secs):
        if s["is_drop"]:
            role = "drop"
        elif i < first:
            role = "build" if (i == first - 1 and i > 0 and s["intensity"] > secs[i - 1]["intensity"] + 2) else "intro"
        elif i > last:
            role = "outro"
        else:
            nxt = secs[i + 1] if i + 1 < len(secs) else None
            role = "build" if (nxt and nxt["is_drop"] and i > 0 and s["intensity"] > secs[i - 1]["intensity"] + 2
                               and not secs[i - 1]["is_drop"]) else "breakdown"
        s["role"] = role
    counts: dict[str, int] = {}
    out = []
    for s in secs:
        counts[s["role"]] = counts.get(s["role"], 0) + 1
        out.append({"id": f"{s['role']}{counts[s['role']]}", "role": s["role"], "bar_start": s["bar_start"],
                    "bar_end": s["bar_end"], "intensity_db": round(s["intensity"], 1)})
    return out
