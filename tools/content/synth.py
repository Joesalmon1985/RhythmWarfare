"""Placeholder renders: one clip part played by one sound, synthesised from the clip's MIDI.

Every placeholder is plain synthesis (no samples), deterministic for a given clip MIDI and sound, and labelled as a
placeholder wherever it is used. A render is the clip's musical length plus one tail bar, 48 kHz stereo 16-bit, the
same shape the owner's Ableton exports must have (docs/CONTENT_TO_RENDER.md).
"""
from __future__ import annotations

import math
import zlib

import numpy as np

from common import SAMPLE_RATE, TAIL_BARS, bars_to_frames, tick_to_sample

SR = SAMPLE_RATE


def _hz(pitch: float) -> float:
    return 440.0 * 2.0 ** ((pitch - 69) / 12.0)


def _vel(v: int) -> float:
    return 0.55 + 0.45 * (v / 127.0)


def _noise(rng: np.random.Generator, n: int, lo: float, hi: float) -> np.ndarray:
    x = rng.standard_normal(n)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1.0 / SR)
    w = max((hi - lo) * 0.15, 50.0)
    mask = 1.0 / (1.0 + np.exp(-(f - lo) / w)) * (1.0 - 1.0 / (1.0 + np.exp(-(f - hi) / w)))
    out = np.fft.irfft(spec * mask, n)
    p = float(np.max(np.abs(out)))
    return out / p if p > 0 else out


def _env(n: int, attack: float = 0.005, release: float = 0.03, sustain: float = 0.85) -> np.ndarray:
    a = max(1, min(int(attack * SR), n // 2))
    r = max(1, min(int(release * SR), n // 2))
    e = np.full(n, sustain)
    d = min(int(0.06 * SR), n)
    e[:d] = sustain + (1.0 - sustain) * np.exp(-np.arange(d) / (0.02 * SR))
    e[:a] *= np.linspace(0.0, 1.0, a, endpoint=False)
    e[n - r:] *= np.linspace(1.0, 0.0, r)
    return e


def kick(rng: np.random.Generator, vel: int, p: dict) -> np.ndarray:
    pitch = float(p.get("pitch", 1.0))
    decay = float(p.get("decay", 0.085))
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    freq = (45.0 + 115.0 * np.exp(-t / 0.013)) * pitch
    body = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t / decay)
    if p.get("drive", 0.0):
        body = np.tanh(body * (1.0 + 4.0 * float(p["drive"]))) / math.tanh(1.0 + 4.0 * float(p["drive"]))
    click = np.zeros(n)
    cn = int(0.002 * SR)
    click[:cn] = rng.standard_normal(cn) * np.linspace(1, 0, cn) * float(p.get("click", 0.35))
    return (body + click) * 0.9 * _vel(vel)


def snare(rng: np.random.Generator, vel: int, p: dict) -> np.ndarray:
    kind = p.get("kind", "snare")
    tone_hz = float(p.get("tone", 190.0))
    if kind == "rim":
        n = int(0.07 * SR)
        t = np.arange(n) / SR
        x = _noise(rng, n, 1500, 6000) * np.exp(-t / 0.012) * 0.7 + np.sin(2 * np.pi * 420 * t) * np.exp(-t / 0.01) * 0.5
        return x * 0.55 * _vel(vel)
    n = int(0.2 * SR)
    t = np.arange(n) / SR
    lo, hi = (1800.0, 9000.0) if kind == "crack" else (1200.0, 7500.0)
    noise = _noise(rng, n, lo, hi) * np.exp(-t / (0.03 if kind == "crack" else 0.045))
    if kind == "clap":
        burst = np.zeros(n)
        for k in range(3):
            off = int(0.011 * k * SR)
            burst[off:] += noise[:n - off] * (0.6 if k < 2 else 1.0)
        noise = burst / max(float(np.max(np.abs(burst))), 1e-9)
    tone = np.sin(2 * np.pi * tone_hz * t) * np.exp(-t / 0.04)
    return (noise * 0.8 + tone * 0.6) * 0.8 * _vel(vel)


def bass_note(pitch: int, vel: int, n: int, p: dict) -> np.ndarray:
    """A sustained bass voice for n samples plus a short release (the tail)."""
    rel = int(0.06 * SR)
    total = n + rel
    t = np.arange(total) / SR
    f = _hz(pitch)
    wave = p.get("wave", "sine")
    if wave == "reese":
        x = sum(np.sign(np.sin(2 * np.pi * f * d * t)) * 0.25 for d in (0.995, 1.005)) + 0.6 * np.sin(2 * np.pi * f * t)
    elif wave == "growl":
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 4.0 * t)
        x = np.sin(2 * np.pi * f * t) + lfo * 0.45 * np.sin(2 * np.pi * f * 2 * t + 0.6 * np.sin(2 * np.pi * f * t))
    elif wave == "saw":
        x = sum(((-1) ** (k + 1)) * np.sin(2 * np.pi * f * k * t) / k for k in range(1, 7)) * 0.6 + 0.5 * np.sin(np.pi * f * t)
    elif wave == "triangle":
        x = sum(((-1) ** ((k - 1) // 2)) * np.sin(2 * np.pi * f * k * t) / (k * k) for k in (1, 3, 5, 7)) * 0.9
    else:
        x = np.sin(2 * np.pi * f * t) + 0.12 * np.sin(4 * np.pi * f * t)
    env = np.ones(total)
    a = int(0.008 * SR)
    env[:a] = np.linspace(0, 1, a, endpoint=False)
    env[n:] = np.linspace(1, 0, rel)
    return x * env * 0.62 * _vel(vel)


def hat(rng: np.random.Generator, vel: int, open_: bool) -> np.ndarray:
    n = int((0.2 if open_ else 0.035) * SR)
    t = np.arange(n) / SR
    return _noise(rng, n, 6000, 15000) * np.exp(-t / (0.05 if open_ else 0.009)) * 0.3 * _vel(vel)


def pad(pitches: list[int], n: int) -> np.ndarray:
    t = np.arange(n) / SR
    x = np.zeros(n)
    for p in pitches:
        f = _hz(p)
        x += np.sin(2 * np.pi * f * 1.001 * t) + np.sin(2 * np.pi * f * 0.999 * t) + 0.25 * np.sin(4 * np.pi * f * t)
    fade = max(1, min(int(0.06 * SR), n // 2))
    env = np.ones(n)
    env[:fade] = np.linspace(0, 1, fade, endpoint=False)
    env[n - fade:] = np.linspace(1, 0, fade)
    return x * env * (0.1 / math.sqrt(max(len(pitches), 1)))


def _add(buf: np.ndarray, start: int, sig: np.ndarray) -> None:
    if start >= len(buf):
        return
    n = min(len(sig), len(buf) - start)
    buf[start:start + n] += sig[:n]


PERCUSSION = {42: "closed", 44: "closed", 46: "open"}


def render_part(part: str, notes: list[dict], bars: int, synth: dict, seed_text: str) -> np.ndarray:
    """Render one clip part (kick, snare, bass or other) with one sound. Returns mono float frames covering the
    clip's bars plus one tail bar."""
    total = bars_to_frames(bars + TAIL_BARS)
    buf = np.zeros(total, dtype=np.float64)
    rng = np.random.default_rng(zlib.crc32(seed_text.encode()))
    kind = synth.get("type", part)
    if kind == "kick":
        for n in notes:
            _add(buf, tick_to_sample(n["tick"]), kick(rng, n["velocity"], synth))
    elif kind == "snare":
        for n in notes:
            _add(buf, tick_to_sample(n["tick"]), snare(rng, n["velocity"], synth))
    elif kind == "bass":
        shift = int(synth.get("octave", 0)) * 12
        for n in notes:
            s0 = tick_to_sample(n["tick"])
            s1 = tick_to_sample(n["tick"] + n["duration_ticks"])
            _add(buf, s0, bass_note(n["pitch"] + shift, n["velocity"], s1 - s0, synth))
    else:  # accompaniment: GM hats on 42/44/46, everything else is a sustained pad chord per onset
        chords: dict[int, list[dict]] = {}
        for n in notes:
            if n["pitch"] in PERCUSSION:
                _add(buf, tick_to_sample(n["tick"]), hat(rng, n["velocity"], PERCUSSION[n["pitch"]] == "open"))
            else:
                chords.setdefault(n["tick"], []).append(n)
        for tick, group in chords.items():
            end = max(g["tick"] + g["duration_ticks"] for g in group)
            s0, s1 = tick_to_sample(tick), tick_to_sample(end)
            _add(buf, s0, pad(sorted({g["pitch"] for g in group})[:6], max(s1 - s0, 1)))
    gain = float(synth.get("gain", 1.0))
    out = np.tanh(buf * gain) * 0.5
    return out.astype(np.float32)
