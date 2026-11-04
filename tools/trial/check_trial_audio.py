"""Checks a recording of the Trial scene (tools/story/record_music.gd on res://src/trial/trial_play.tscn): for every phrase attempt the recorded drums must line
up with the pack's drum loop started at the attempt's start time, with the same delay every time (the clock never restarts and the voices do not drift).

    python tools/trial/check_trial_audio.py <recording base>
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
BEAT = 60.0 / 174.0


def read_pcm(path):
    with wave.open(str(path), "rb") as w:
        ch, rate, n = w.getnchannels(), w.getframerate(), w.getnframes()
        a = np.frombuffer(w.readframes(n), "<i2").astype(np.float64) / 32768.0
    return a.reshape(-1, ch).mean(axis=1), rate


def xcorr(rec, model, rate, max_s):
    n = 1 << int(np.ceil(np.log2(len(rec) + len(model))))
    c = np.fft.irfft(np.fft.rfft(rec, n) * np.conj(np.fft.rfft(model, n)), n)
    m = int(max_s * rate)
    lags = np.concatenate([np.arange(0, m), np.arange(-m, 0)])
    vals = np.concatenate([c[:m], c[n - m:]])
    k = int(np.argmax(vals))
    norm = np.sqrt((rec ** 2).sum() * (model ** 2).sum()) + 1e-12
    return lags[k] / rate, float(vals[k] / norm)


def main() -> int:
    base = Path(sys.argv[1])
    rec, rate = read_pcm(base.with_suffix(".wav"))
    info = json.loads(base.with_suffix(".json").read_text())
    td = json.loads((ROOT / "content/trial/passages.json").read_text())
    pid = td["music"]["audio"]
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "d.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(ROOT / "songs/packs" / pid / "loops/drums.wav"), "-ar", str(rate), "-ac", "1", str(out)], check=True)
        loop, _ = read_pcm(out)
    s0 = float(info["started_wall"])
    attempts = [e for e in info.get("events", []) if e["kind"] == "attempt"]
    delays = []
    for a in attempts:
        q = float(a["start"])
        if a["family"] != "drums":
            continue
        i0 = int(round((s0 + q + 0.7) * rate))
        ln = int(6 * BEAT * rate)
        if i0 + ln + int(0.2 * rate) > len(rec):
            continue
        idx = np.arange(int(0.7 * rate), int(0.7 * rate) + ln)
        model = loop[np.mod(idx, len(loop))]
        d, c = xcorr(rec[i0:i0 + ln + int(0.1 * rate)], model, rate, 0.25)
        delays.append(d * 1000.0)
        print(f"attempt at song {q:7.3f} s (passage {a['passage']}, choice {a['choice']}): drums delay {d * 1000:+7.2f} ms, correlation {c:.2f}")
    if delays:
        print(f"delay across attempts: spread {max(delays) - min(delays):.2f} ms over {len(delays)} attempts")
    ok = len(delays) >= 2 and max(delays) - min(delays) < 15.0
    print("RESULT", "ok" if ok else "CHECK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
