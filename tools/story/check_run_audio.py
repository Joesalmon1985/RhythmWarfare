"""Check a recording of the continuous run (tools/story/record_music.gd on res://src/run/run_play.tscn) against what the engine said it played.

    python tools/story/check_run_audio.py <recording base>

For every phase on an untreated level it fits each 16-beat block of the recording as a mix of the drum loop (from the phase downbeat), the
bass and Synth loops (from the reveal beat the engine reported: a delayed reveal moves their origin) and the riser or fall, and compares the
fitted coefficients with the gains of the mix stage in force. Treated levels (filters, distortion) are only checked for their delay. It also
reports the delay per phase: the same value in every phase and across a world change means the voices are on the clock and nothing drifts.
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


def tiled(loop: np.ndarray, start: int, length: int, origin: int) -> np.ndarray:
    """`length` samples from absolute sample `start` of a loop that began at sample `origin` (zeros before it)."""
    idx = np.arange(start, start + length) - origin
    out = np.where(idx >= 0, loop[np.mod(idx, len(loop))], 0.0)
    return out


def xcorr_delay(rec: np.ndarray, model: np.ndarray, rate: int, max_s: float) -> float:
    n = 1 << int(np.ceil(np.log2(len(rec) + len(model))))
    c = np.fft.irfft(np.fft.rfft(rec, n) * np.conj(np.fft.rfft(model, n)), n)
    m = int(max_s * rate)
    lags = np.concatenate([np.arange(0, m), np.arange(-m, 0)])
    vals = np.concatenate([c[:m], c[n - m:]])
    k = int(np.argmax(vals))
    i = int(lags[k]) % n
    y0, y1, y2 = c[(i - 1) % n], c[i], c[(i + 1) % n]
    d = y0 - 2 * y1 + y2
    return (int(lags[k]) + (0.5 * (y0 - y2) / d if d else 0.0)) / rate


def main() -> int:
    base = Path(sys.argv[1])
    rec, rate = read_pcm(base.with_suffix(".wav"))
    info = json.loads(base.with_suffix(".json").read_text())
    run = json.loads((ROOT / "content/run/run.json").read_text())
    music = {n["id"]: n for n in json.loads((ROOT / "content/story/music.json").read_text())["nodes"]}
    nodes = {n["id"]: n for n in run["nodes"]}
    stages = run["stages"]
    s0 = float(info["started_wall"])
    events = info.get("events", [])
    starts = [e for e in events if e["kind"] == "phase_start"]
    rev = {int(e["t"] / BEAT // 64): e for e in events if e["kind"] == "reveal"}
    mixes = [e for e in events if e["kind"] == "mix"]
    windows = [e for e in events if e["kind"] == "route_window"]
    loops: dict = {}

    def pack_loops(pid: str) -> dict:
        if pid not in loops:
            d = ROOT / "songs/packs" / pid
            pk = json.loads((d / "pack.json").read_text())
            loops[pid] = {k: resampled(d / v, rate) for k, v in pk["stems"].items()}
        return loops[pid]

    fx = {k: resampled(ROOT / "assets/run" / f"{k}.wav", rate) for k in ("riser", "fall")}
    gain_fx = 10 ** (run["effects"]["gain_db"] / 20.0)
    print(f"recording {len(rec) / rate:.1f} s at {rate} Hz; song started at wall {s0:.3f}; {len(starts)} phases in the log")
    delays = []
    bad = 0
    voice_off: dict = {}
    for ph in starts:
        n = int(round(float(ph["t"]) / BEAT / 64))
        node = nodes[ph["node"]]
        mu = music[ph["node"]]
        treated = mu["treatment"] != "none"
        t0 = float(ph["t"])
        if s0 + t0 + 64 * BEAT > len(rec) / rate:
            break
        loops_ = pack_loops(mu["audio"])
        a = int(round((s0 + t0) * rate))
        # delay from the drums-alone first block
        seg = rec[a - int(0.3 * rate):a + int(8 * BEAT * rate)]
        mod = tiled(loops_["drums"], a - int(0.3 * rate), len(seg), a)
        d = xcorr_delay(seg, mod, rate, 0.4)
        delays.append(d * 1000.0)
        print(f"phase {ph['phase']} {ph['node']:14s} treatment {mu['treatment']:10s} delay {d * 1000.0:+7.2f} ms")
        if treated:
            continue
        ad = a + int(round(d * rate))
        r_ev = rev.get(n - 0, None)
        reveal_beat = None
        for e in events:
            if e["kind"] == "reveal" and t0 - 1e-6 <= float(e["t"]) < t0 + 64 * BEAT:
                reveal_beat = float(e["beat"])
        for b in range(4):
            mix = [m for m in mixes if t0 + b * 16 * BEAT - 1e-6 <= float(m["t"]) < t0 + (b + 1) * 16 * BEAT - 1e-6]
            stage = int(mix[0]["stage"]) if mix else None
            if stage is None:
                continue
            g = stages[stage]["gains"]
            skip = int(0.7 * rate)
            lo = ad + int(b * 16 * BEAT * rate) + skip
            ln = int(16 * BEAT * rate) - skip - int(0.3 * rate)
            comps: dict = {"drums": (loops_["drums"], ad)}
            if reveal_beat is not None and b * 16 >= reveal_beat:
                borigin = ad + int(round(reveal_beat * BEAT * rate))
                comps["bass"] = (loops_["bass"], borigin)
                comps["other"] = (loops_["other"], borigin)
            if b == 3:
                eff = "riser" if stage == 3 else "fall"
                comps[eff] = (fx[eff], ad + int(48 * BEAT * rate))
            shift = {k: 0 for k in comps}  # samples each voice sits from its nominal start (found below)
            y = rec[lo:lo + ln]
            for _ in range(3):
                cols = [tiled(comps[k][0], lo, ln, comps[k][1] + shift[k]) for k in comps]
                m_ = np.stack(cols, axis=1)
                coef, *_ = np.linalg.lstsq(m_, y, rcond=None)
                for ci, k in enumerate(comps):
                    if k == "drums":
                        continue
                    resid = y - m_ @ coef + coef[ci] * m_[:, ci]
                    dly = xcorr_delay(resid, m_[:, ci], rate, 0.03)
                    shift[k] += int(round(dly * rate))
            names = list(comps)
            for k in names:
                if k not in ("drums",):
                    voice_off.setdefault(k, []).append(shift[k] / rate * 1000.0)
            fit = m_ @ coef
            expl = 1.0 - float(((y - fit) ** 2).sum() / ((y ** 2).sum() + 1e-12))
            exp = {k: g[k] for k in names if k in g}
            exp.update({k: gain_fx for k in names if k in ("riser", "fall")})
            got = dict(zip(names, [round(float(c), 2) for c in coef]))
            ok = all(abs(got[k] - exp[k]) < 0.12 for k in exp) and expl > 0.9
            if not ok:
                bad += 1
            print(f"   block {b + 1} stage {stage} ({stages[stage]['label']:14s}) fitted {got}  expected {exp}  explains {expl * 100:5.1f}%  {'ok' if ok else 'CHECK'}")
        if reveal_beat is None:
            print("   no reveal in this phase (bass never entered)")
        else:
            print(f"   bass and synth started from beat {reveal_beat:g} of the phase")
    for k, v in voice_off.items():
        print(f"{k:6s} sits {min(v):+.1f} to {max(v):+.1f} ms from its nominal start relative to the drums ({len(v)} blocks measured)")
    if delays:
        print(f"delay per phase: min {min(delays):+.2f} ms, max {max(delays):+.2f} ms, spread {max(delays) - min(delays):.2f} ms")
    ok = bool(delays) and max(delays) - min(delays) < 6.0 and bad == 0
    print("RESULT", "ok" if ok else "CHECK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
