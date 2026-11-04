"""Checks a recording of the seamless entry and exit (tools/story/record_music.gd on res://src/run/run_play.tscn with RW_TRIAL_ENTER=1 and RW_TRIAL_LEAVE_AT=<s>):
the Warehouse plays, the wizard is chosen, the dungeon's pack enters on a downbeat, the dungeon is left and the Warehouse pack re-enters on a downbeat. One music group per
stretch, never restarted: each group's drums must line up with its pack's drum loop at the same delay in every block, and the delay before the transitions, in the dungeon
and after them must agree.

    python tools/trial/check_transition_audio.py <recording base>
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


def loop_of(pack, rate):
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "d.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(ROOT / "songs/packs" / pack / "loops/drums.wav"), "-ar", str(rate), "-ac", "1", str(out)], check=True)
        return read_pcm(out)[0]


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
    music = json.loads((ROOT / "content/story/music.json").read_text())
    nodes = music.get("nodes", music)
    if isinstance(nodes, list):
        nodes = {n["id"]: n for n in nodes}
    trial = json.loads((ROOT / "content/trial/passages.json").read_text())
    s0 = float(info["started_wall"])
    drums = [v for v in info["voices"] if v["voice"] == "drums"]
    print("music groups (drums voices):", [(v["node"], round(v["target"], 3), round(v["lateness_ms"], 1)) for v in drums])
    end = len(rec) / rate - s0 - 1.0
    all_delays = []
    for i, v in enumerate(drums):
        node = str(v["node"])
        pack = trial["music"]["audio"] if node == "trial" else nodes.get(node, {}).get("audio")
        if pack is None:
            print("no pack for", node)
            continue
        loop = loop_of(pack, rate)
        t0 = float(v["target"])
        t1 = float(drums[i + 1]["target"]) - 1.0 if i + 1 < len(drums) else end
        delays = []
        a0 = int(round((s0 + t0) * rate))  # the drums alone from the group's own downbeat: the same measurement check_run_audio.py makes per phase
        if a0 + int(8 * BEAT * rate) < len(rec):
            seg = rec[a0 - int(0.3 * rate):a0 + int(8 * BEAT * rate)]
            idx = np.arange(a0 - int(0.3 * rate), a0 - int(0.3 * rate) + len(seg)) - a0
            mod = np.where(idx >= 0, loop[np.mod(idx, len(loop))], 0.0)
            d0, _ = xcorr(seg, mod, rate, 0.4)
            delays.append(d0 * 1000.0)
        k = 1
        while t0 + (k + 1) * 16 * BEAT < t1:
            a = k * 16 * BEAT + 0.8
            ln = int(6 * BEAT * rate)
            i0 = int(round((s0 + t0 + a) * rate))
            idx = np.arange(int(a * rate), int(a * rate) + ln)
            d, c = xcorr(rec[i0:i0 + ln + int(0.1 * rate)], loop[np.mod(idx, len(loop))], rate, 0.3)
            delays.append(d * 1000.0)
            k += 1
        if delays:
            print(f"group {i} ({node}, {pack}) from {t0:.2f}s: {len(delays)} blocks, delay {np.mean(delays):+.1f} ms, spread {max(delays) - min(delays):.1f} ms")
        all_delays.extend(delays)
    spread = max(all_delays) - min(all_delays) if all_delays else 999.0
    print(f"delay across all groups before, in and after the transitions: spread {spread:.1f} ms over {len(all_delays)} blocks")
    ok = len(drums) >= 3 and spread < 12.0
    print("RESULT", "ok" if ok else "CHECK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
