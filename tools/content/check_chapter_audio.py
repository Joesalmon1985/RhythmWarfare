"""Check a recording of a chapter that plays a RENDERED arrangement pack (songs/story_<chapter>_<n>, whole-chapter stems) against the pack's stems.

    RW_STORY_CHAPTER=hospital RW_AUTOPLAY=perfect RW_RUN_SEED=0 godot --headless --path . -s tools/story/record_music.gd -- user://rec <seconds longer than the chapter>
    python tools/content/check_chapter_audio.py <recording base> songs/story_hospital_1

tools/story/check_music.py models an 8-bar lap of a looping pack; a rendered pack is one lap the length of the chapter with the stem gains changing inside it, so this check
fits every 2-bar window of the recording as the sum of the three stems (each from its position in the song) and compares the least-squares gain of each stem with the gain the
transport logged. The recording is made against the wall clock by a dummy audio driver whose pace is not exactly the wall's, so the window delays are first fitted by a line
(delay = c0 + c1 * song time, taken from the windows a single stem explains best) and the recording is resampled along it; what is checked after that is that the stems sit on that
line (residual delay under one mix chunk of 6 ms: no drift of any stem against the song or each other), the gains agree with the log (0.12) and every window is explained above 97 %.
RESULT ok when all three hold. Prints the fitted pace as well (c1), which is the recorder's, not the game's: the same pace appears for the chapter's own pack.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BAR_S = 4 * 60.0 / 174.0
CHUNK_MS = 6.0


def read_pcm(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        ch, rate, n = w.getnchannels(), w.getframerate(), w.getnframes()
        a = np.frombuffer(w.readframes(n), "<i2").astype(np.float64) / 32768.0
    return a.reshape(-1, ch).mean(axis=1), rate


def resampled(path: Path, rate: int) -> np.ndarray:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "x.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-ar", str(rate), "-ac", "1", str(out)], check=True)
        return read_pcm(out)[0]


def xcorr(a: np.ndarray, b: np.ndarray, rate: int, max_s: float) -> tuple[float, float]:
    """Delay of `a` against `b` in samples (parabolic refinement) and the normalised peak."""
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    c = np.fft.irfft(np.fft.rfft(a, n) * np.conj(np.fft.rfft(b, n)), n)
    m = int(max_s * rate)
    lags = np.concatenate([np.arange(0, m), np.arange(-m, 0)])
    vals = np.concatenate([c[:m], c[n - m:]])
    k = int(np.argmax(vals))
    lag = int(lags[k])
    i = lag % n
    y0, y1, y2 = c[(i - 1) % n], c[i], c[(i + 1) % n]
    d = y0 - 2 * y1 + y2
    return lag + (0.5 * (y0 - y2) / d if d else 0.0), float(vals[k] / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def best_stem_delay(seg: np.ndarray, parts: dict[str, np.ndarray], pad: int, rate: int, max_s: float) -> tuple[float, float]:
    """(delay in samples, correlation) of the stem that matches the window best (a muted stem correlates with nothing)."""
    best = (0.0, -1.0)
    for part in parts.values():
        lag, r = xcorr(seg, np.pad(part, (0, max(0, len(seg) - len(part)))), rate, max_s)
        if r > best[1]:
            best = (lag - pad, r)
    return best


def main() -> int:
    base, pack = Path(sys.argv[1]), ROOT / sys.argv[2]
    rec, rate = read_pcm(base.with_suffix(".wav"))
    info = json.loads(base.with_suffix(".json").read_text())
    level = json.loads((pack / "level.json").read_text())
    stems = {k: resampled(pack / v["file"], rate) for k, v in level["recorded_music"]["stems"].items()}
    log = info["log"]
    song = np.array([e["song"] for e in log])
    wall = np.array([e["wall"] for e in log])
    gains = {k: np.array([e["gains"].get(k, 0.0) for e in log]) for k in stems}
    live = song < song.max() - 1e-6  # the song clock stops at the end of the chapter
    slope, icpt = np.polyfit(song[live], wall[live], 1)
    L = len(next(iter(stems.values())))
    chapter_s = L / rate
    win = int(2 * BAR_S * rate)
    pad = int(0.1 * rate)
    starts = []
    t = 0.5
    while t + 2 * BAR_S < min(chapter_s, song[-1]) - 0.5:
        starts.append(t)
        t += 2 * BAR_S
    # pass 1: delay of each window within +-0.3 s; keep the clear ones and fit a line through them
    first = []
    for t in starts:
        s0, w0 = int(t * rate), int(round((info['started_wall'] + t) * rate))
        seg = rec[w0 - pad:w0 + win + pad]
        d, r = best_stem_delay(seg, {k: v[s0:s0 + win] for k, v in stems.items()}, pad, rate, 0.3)
        first.append((t, d / rate * 1000.0, r))
    if '--debug' in sys.argv:
        print([(round(t, 1), round(d, 1), round(r, 2)) for t, d, r in first])
    clear = [(t, d) for t, d, r in first if r > 0.5]
    if len(clear) < 4:
        print("RESULT CHECK: fewer than four windows correlate clearly; the recording does not match the pack")
        return 1
    ts, ds = np.array([c[0] for c in clear]), np.array([c[1] for c in clear])
    keep = np.ones(len(ts), bool)
    for _ in range(4):  # a line through the windows that agree, dropping the ones a muted stem or a repeated loop pulled away
        c1, c0 = np.polyfit(ts[keep], ds[keep], 1)  # delay_ms = c0 + c1 * t
        keep = np.abs(ds - (c0 + c1 * ts)) < 25.0
        if keep.sum() < 4:
            print("RESULT CHECK: the window delays do not lie on a line; the recording does not match the pack")
            return 1
    pace = 1.0 + c1 / 1000.0
    # pass 2: warp the recording onto the song's time along the line (a no-op when the recorder keeps the wall's pace), then check every window against the stems
    t_song = np.arange(0, chapter_s, 1.0 / rate)
    t_rec = info["started_wall"] + t_song + (c0 + c1 * t_song) / 1000.0
    warped = np.interp(t_rec * rate, np.arange(len(rec)), rec, left=0.0, right=0.0)
    rows = []
    for t in starts:
        s0 = int(t * rate)
        seg = warped[s0 - pad:s0 + win + pad]
        d, r = best_stem_delay(seg, {k: v[s0:s0 + win] for k, v in stems.items()}, pad, rate, 0.15)
        a = warped[s0 + int(round(d)):s0 + int(round(d)) + win]
        cols = np.stack([stems[k][s0:s0 + win] for k in stems], axis=1)[:len(a)]
        coef = np.linalg.lstsq(cols, a[:len(cols)], rcond=None)[0]
        fit = cols @ coef
        explained = 1.0 - float(((a[:len(fit)] - fit) ** 2).sum() / ((a[:len(fit)] ** 2).sum() + 1e-12))
        at = lambda x: {k: float(np.interp((info["started_wall"] + x - icpt) / slope, song, gains[k])) for k in stems}  # noqa: E731  (the log is on the song clock)
        exp, e0, e1 = at(t + BAR_S), at(t - 0.7), at(t + 2 * BAR_S + 0.7)  # 0.7 s of slack: the song clock is not exactly the audio's
        if any(abs(e0[k] - e1[k]) > 0.05 for k in stems):
            continue  # a stem switch falls inside this window (a phase boundary): no single mix to fit
        rows.append((t, d / rate * 1000.0, dict(zip(stems, coef)), exp, explained))
    resid = np.array([r[1] for r in rows])
    print(f"recording {len(rec) / rate:.1f} s, chapter pack {pack.name}: {chapter_s:.1f} s, {len(rows)} two-bar windows without a stem switch inside (of {len(starts)}); recorder pace {pace:.5f} of the song clock (delay {c0:+.1f} ms + {c1:+.2f} ms per s)")
    bad = 0
    for t, d, coef, exp, ex in rows:
        diff = max(abs(coef[k] - exp[k]) for k in coef if exp[k] > 0.05 or coef[k] > 0.05)
        ok = ex > 0.97 and diff < 0.12
        bad += 0 if ok else 1
        print(f"  t {t:6.1f} s  residual delay {d:+6.2f} ms  fit " + " ".join(f"{k} {coef[k]:.2f}/{exp[k]:.2f}" for k in coef) + f"  explains {ex * 100:5.1f}%  {'ok' if ok else 'CHECK'}")
    spread = float(resid.max() - resid.min())
    print(f"residual delay across the chapter: min {resid.min():+.2f} ms, max {resid.max():+.2f} ms, spread {spread:.2f} ms (limit {CHUNK_MS:g}); windows outside the fit: {bad}")
    ok = spread < CHUNK_MS and bad == 0
    print("RESULT", "ok" if ok else "CHECK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
