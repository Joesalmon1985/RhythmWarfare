"""Check a recording of the running story scene (tools/story/record_music.gd) against the chapter's cues and stems.

    python tools/story/check_music.py <recording base> [pack_dir]      # <base>.wav and <base>.json from record_music.gd

For every eight-bar lap of the recording it models what the Music bus should carry (the lap's phase decides: drum loop +
Synth backing in a drums phase, bass loop + Synth in a bass phase, every one at the gain the level program says), finds
the delay that best lines the model up with the recording (cross-correlation), and reports

  * the delay per lap: it must be the same in every lap (the loops do not drift against the song clock, or each other);
  * how much of the recording the model explains (the supplied recordings are what is audible);
  * for drums laps, the mix coefficients of the drum loop and the Synth backing separately (both audible);
  * for each drum cue, the recorded transient against the cue's time (kicks and snares, in ms, per lap).
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


def xcorr_delay(rec: np.ndarray, model: np.ndarray, rate: int, max_s: float) -> tuple[int, float]:
    """Samples of delay (rec lags model) and the correlation coefficient there."""
    n = 1 << int(np.ceil(np.log2(len(rec) + len(model))))
    c = np.fft.irfft(np.fft.rfft(rec, n) * np.conj(np.fft.rfft(model, n)), n)
    m = int(max_s * rate)
    lags = np.concatenate([np.arange(0, m), np.arange(-m, 0)])
    vals = np.concatenate([c[:m], c[n - m:]])
    k = int(np.argmax(vals))
    lag = int(lags[k])
    # parabolic refinement around the peak, in samples
    i = lag % n
    y0, y1, y2 = c[(i - 1) % n], c[i], c[(i + 1) % n]
    d = y0 - 2 * y1 + y2
    frac = 0.5 * (y0 - y2) / d if d else 0.0
    norm = np.sqrt((rec ** 2).sum() * (model ** 2).sum()) + 1e-12
    return lag, float(y1 / norm), frac


def main() -> int:
    base = Path(sys.argv[1])
    pack = ROOT / (sys.argv[2] if len(sys.argv) > 2 else "songs/story_n1_warehouse")
    rec, rate = read_pcm(base.with_suffix(".wav"))
    info = json.loads(base.with_suffix(".json").read_text())
    level = json.loads((pack / "level.json").read_text())
    loops = {k: resampled(pack / v["file"], rate) for k, v in level["recorded_music"]["stems"].items()}
    modes = {k: v["mode"] for k, v in level["recorded_music"]["stems"].items()}
    L = len(next(iter(loops.values())))
    lap_s = L / rate
    s0 = float(info["started_wall"])
    phases = level["phases"]
    tpb = 3840
    print(f"recording {len(rec) / rate:.1f} s at {rate} Hz, song started at wall {s0:.3f} s, loop {lap_s:.4f} s")
    tick_s = 60.0 / (174 * 960)
    laps = int((len(rec) / rate - s0 - 1.0) // lap_s)
    rows = []
    for k in range(laps):
        mode = next(p["mode"] for p in phases if p["start_tick"] <= k * 8 * tpb < p["end_tick"])
        stems = [n for n, m in modes.items() if m in ("always", mode)]
        a = int(round((s0 + k * lap_s) * rate))
        seg = rec[a - int(0.3 * rate):a + L + int(0.3 * rate)]
        model = sum(loops[n] for n in stems)
        lag, corr, frac = xcorr_delay(seg, model, rate, 0.5)
        # lag is relative to the segment, which starts 0.3 s early
        delay_ms = (lag - 0.3 * rate + frac) / rate * 1000.0
        # least-squares mix of the individual stems at that delay
        d = int(round(lag - 0.3 * rate))
        win = rec[a + d:a + d + L]
        cols = np.stack([loops[n] for n in stems], axis=1)
        coef, res, *_ = np.linalg.lstsq(cols[:len(win)], win[:len(cols)], rcond=None)
        fit = cols[:len(win)] @ coef
        explained = 1.0 - float(((win[:len(fit)] - fit) ** 2).sum() / ((win[:len(fit)] ** 2).sum() + 1e-12))
        rows.append((k, mode, delay_ms, corr, dict(zip(stems, [round(float(c), 3) for c in coef])), explained))
        print(f"lap {k:2d} {mode:5s} delay {delay_ms:+8.2f} ms  corr {corr:.3f}  mix {dict(zip(stems, np.round(coef, 3)))}  model explains {explained * 100:5.1f}% of the signal")
    delays = np.array([r[2] for r in rows])
    ks = np.array([r[0] for r in rows])
    slope = np.polyfit(ks, delays, 1)[0] if len(ks) > 1 else 0.0
    print(f"\ndelay across laps: min {delays.min():+.2f} ms, max {delays.max():+.2f} ms, spread {delays.max() - delays.min():.2f} ms, drift {slope:+.3f} ms per lap")
    # per-cue check in drums laps: the recorded transient against the cue time, using the lap delay
    cues = level["recorded_music"]["cues"]
    errs = []
    env = np.sqrt(np.convolve(rec ** 2, np.ones(int(0.001 * rate)) / int(0.001 * rate), "same"))
    for k, mode, delay_ms, *_ in rows:
        if mode != "drums":
            continue
        for fam in ("kick", "snare"):
            for tick, _dur, pad in cues[fam]:
                t = s0 + k * lap_s + tick * tick_s + delay_ms / 1000.0
                i0, i1 = int((t - 0.025) * rate), int((t + 0.025) * rate)
                if i0 < 1 or i1 >= len(env):
                    continue
                seg = np.log(env[i0:i1] + 1e-4)
                d3 = seg[int(0.003 * rate):] - seg[:-int(0.003 * rate)]
                j = int(np.argmax(d3))
                errs.append((k, fam, ((i0 + j) / rate - t) * 1000.0))
    if errs:
        e = np.array([x[2] for x in errs])
        print(f"{len(e)} drum cues in {len({x[0] for x in errs})} drums laps: recorded transient minus cue time (after the lap's delay) mean {e.mean():+.1f} ms, "
              f"max |err| {np.abs(e).max():.1f} ms")
    ok = (delays.max() - delays.min() < 5.0) and all(r[5] > 0.9 for r in rows)
    print("RESULT", "ok" if ok else "CHECK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
