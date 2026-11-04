"""Checks a recording of the Trial scene (tools/story/record_music.gd on res://src/trial/trial_play.tscn): the dungeon plays one unbroken stretch of music from the
clock's first beat, so the recorded drums must line up with the pack's drum loop at the same delay in every block (no restarts, no drift) while the mix changes with
the kind of block (ambient or phrase).

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
    events = info.get("events", [])
    voices = [v for v in info.get("voices", []) if v["voice"] in ("drums", "bass", "other")]
    print(f"voices started: {[(v['voice'], round(v['target'], 3)) for v in voices]} (one group for the whole visit)")
    delays = []
    last = len(rec) / rate - s0 - 1.0
    exits = [float(e["t"]) for e in events if e["kind"] == "exit"]
    if exits:
        last = min(last, min(exits) - 0.5)  # the music fades out after the exit
    k = 0
    while (k + 1) * 16 * BEAT < last:
        a = k * 16 * BEAT + 0.8  # skip the gain ramp at the block start
        ln = int(6 * BEAT * rate)
        i0 = int(round((s0 + a) * rate))
        idx = np.arange(int(a * rate), int(a * rate) + ln)
        d, c = xcorr(rec[i0:i0 + ln + int(0.1 * rate)], loop[np.mod(idx, len(loop))], rate, 0.3)
        delays.append(d * 1000.0)
        kinds = [e for e in events if e["kind"] == "phrase" and int(e["block"]) == k]
        print(f"block {k}: drums delay {d * 1000:+7.2f} ms, correlation {c:.2f}" + ("  (phrase block)" if kinds else ""))
        k += 1
    if delays:
        print(f"delay across blocks: spread {max(delays) - min(delays):.2f} ms over {len(delays)} blocks")
    ok = len(delays) >= 3 and max(delays) - min(delays) < 10.0 and len(voices) == 3
    print("RESULT", "ok" if ok else "CHECK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
