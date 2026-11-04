"""Synthesises the two choice-window effects of the continuous run: assets/run/riser.wav and assets/run/fall.wav (own work, no samples).

    python tools/content/make_run_effects.py

Both last exactly 16 beats at 174 BPM (the choice window, beats 49 to 64). The riser is band-limited noise and a sine sweep climbing
and swelling to the downbeat; the fall is the same material descending and thinning out. Deterministic (seeded noise).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, SAMPLE_RATE, write_wav  # noqa: E402

BEATS = 16
N = int(round(BEATS * 60.0 / 174.0 * SAMPLE_RATE))


def sweep(f0: float, f1: float, curve: float) -> np.ndarray:
    t = np.linspace(0.0, 1.0, N)
    f = f0 * (f1 / f0) ** (t ** curve)
    phase = 2 * np.pi * np.cumsum(f) / SAMPLE_RATE
    return np.sin(phase)


def band_noise(f0: float, f1: float, rng: np.random.Generator, curve: float) -> np.ndarray:
    """White noise through a moving band: crude but smooth (an FFT-domain gate that slides in frequency per chunk)."""
    out = np.zeros(N)
    win = 4096
    hop = win // 2
    w = np.hanning(win)
    for i in range(0, N - win, hop):
        p = i / N
        centre = f0 * (f1 / f0) ** (p ** curve)
        spec = np.fft.rfft(rng.standard_normal(win) * w)
        f = np.fft.rfftfreq(win, 1 / SAMPLE_RATE)
        gain = np.exp(-((np.log2(np.maximum(f, 1.0) / centre)) ** 2) / (2 * 0.6 ** 2))
        out[i:i + win] += np.fft.irfft(spec * gain, win) * w
    return out / (np.abs(out).max() + 1e-9)


def stereo(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    d = int(0.0007 * SAMPLE_RATE)
    return np.stack([x, np.roll(x, d)], axis=1)


def main() -> None:
    rng = np.random.default_rng(174)
    t = np.linspace(0.0, 1.0, N)
    rise_env = t ** 2.2
    riser = (0.7 * band_noise(250, 9000, rng, 1.0) + 0.5 * sweep(180, 2400, 1.2)) * rise_env
    riser[-int(0.02 * SAMPLE_RATE):] *= np.linspace(1, 0, int(0.02 * SAMPLE_RATE))  # clean cut just before the downbeat
    fall_env = (1.0 - t) ** 1.6 * np.minimum(1.0, t * 40)
    fall = (0.7 * band_noise(7000, 200, rng, 0.8) + 0.5 * sweep(2200, 70, 0.9)) * fall_env
    for name, x in (("riser", riser), ("fall", fall)):
        x = x / (np.abs(x).max() + 1e-9) * 0.5
        write_wav(ROOT / "assets" / "run" / f"{name}.wav", stereo(x, rng).astype(np.float32))
        print("wrote", name, f"{N / SAMPLE_RATE:.3f} s")


if __name__ == "__main__":
    main()
