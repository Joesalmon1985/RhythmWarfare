#!/usr/bin/env python3
"""Does converting a pack stem from WAV to Ogg Vorbis keep it sample-exact? (docs/REPO_SIZE.md, Part 2.) Run BEFORE converting anything.

    python3 tools/content/ogg_check.py [--q 7] [--bass-q 9] [--limit N] [<pack> ...]      default: one pack per family

Encodes each stem of each pack to Ogg (ffmpeg libvorbis) in a scratch folder, lets Godot decode it (tools/content/ogg_probe.gd: once, and looping),
and checks against the WAV:
  a. length: the stream's stated length equals the WAV's frame count; the one-shot decode produces exactly that many frames; the loop's second lap
     equals its first lap bit for bit (the period the engine uses); the step across the seam (last frame to first frame) is no bigger than the
     biggest step inside the loop.
  b. timing: the lag of the decode against the WAV by cross-correlation, in frames (at most 1), and the lag of each of the 24 strongest transients.
  c. bass: energy 30..250 Hz of the decode against the WAV, in dB (within 0.3 dB).
Exit status 1 when any check fails; the table says which.
"""
import json
import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GODOT = os.environ.get("GODOT") or os.path.expandvars("%USERPROFILE%/Downloads/Godot_v4.5.1-stable_win64.exe/Godot_v4.5.1-stable_win64_console.exe")
FAMILY_PICK = ["gospel_entry", "ember_e00_orchard", "squadron_c01", "dd_part1", "lv1_warehouse", "cold_fusion"]


def read_wav(p):
    with wave.open(str(p), "rb") as w:
        assert w.getsampwidth() == 2, "16-bit only"
        a = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, w.getnchannels()).astype(np.float64) / 32768.0
        return a if a.shape[1] == 2 else np.repeat(a, 2, axis=1)


def band_energy(x, rate, lo, hi):
    m = x.mean(axis=1)
    sp = np.abs(np.fft.rfft(m)) ** 2
    f = np.fft.rfftfreq(len(m), 1.0 / rate)
    return float(sp[(f >= lo) & (f <= hi)].sum())


def xcorr_lag(a, b, maxlag=64):
    """The shift s (frames) such that b[i + s] is a[i], from the peak of the cross-correlation, refined by a parabola."""
    x, y = a.mean(axis=1), b.mean(axis=1)
    n = min(len(x), len(y))
    x, y = x[:n], y[:n]
    scores = {}
    for s in range(-maxlag, maxlag + 1):
        if s >= 0:
            scores[s] = float(np.dot(x[: n - s], y[s:n]))
        else:
            scores[s] = float(np.dot(x[-s:n], y[: n + s]))
    best = max(scores, key=scores.get)
    if best - 1 in scores and best + 1 in scores:
        c0, c1, c2 = scores[best - 1], scores[best], scores[best + 1]
        d = c0 - 2 * c1 + c2
        if d != 0:
            return best + 0.5 * (c0 - c2) / d
    return float(best)


def transient_lags(a, b, k=24, win=96):
    x = np.abs(np.diff(a.mean(axis=1), prepend=0.0))
    idx = []
    work = x.copy()
    for _ in range(k):
        i = int(work.argmax())
        if work[i] <= 0:
            break
        idx.append(i)
        work[max(0, i - 2000): i + 2000] = 0
    out = []
    for i in idx:
        if i - win < 0 or i + win + 8 >= len(a) or i + win + 8 >= len(b):
            continue
        out.append(xcorr_lag(a[i - win: i + win], b[i - win: i + win], 8))
    return out


def main():
    args = sys.argv[1:]
    q = int(args[args.index("--q") + 1]) if "--q" in args else 7
    bq = int(args[args.index("--bass-q") + 1]) if "--bass-q" in args else 9
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 0
    skip = {args.index(o) + 1 for o in ("--q", "--bass-q", "--limit") if o in args}
    packs = [a for i, a in enumerate(args) if not a.startswith("--") and (i + 1) not in skip and i not in skip] or FAMILY_PICK
    work = Path(tempfile.mkdtemp(prefix="ogg_check_"))
    srcs = []
    for p in packs:
        for stem in ("drums", "bass", "other"):
            w = ROOT / "songs" / "packs" / p / "loops" / f"{stem}.wav"
            if w.exists():
                srcs.append((f"{p}__{stem}", w, stem))
    if limit:
        srcs = srcs[:limit]
    (work / "ogg").mkdir()
    sizes = {}
    for name, w, stem in srcs:
        o = work / "ogg" / f"{name}.ogg"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(w), "-c:a", "libvorbis", "-q:a", str(bq if stem == "bass" else q), str(o)], check=True)
        sizes[name] = (w.stat().st_size, o.stat().st_size)
    subprocess.run([GODOT, "--headless", "--path", str(ROOT), "-s", "tools/content/ogg_probe.gd", "--", str(work / "ogg"), str(work / "dec")], check=True, capture_output=True)
    bad = 0
    print(f"{'stem':34s} {'frames':>7s} {'once':>7s} {'lap2=1':>6s} {'seam':>5s} {'lag':>6s} {'trans lag':>9s} {'30-250 dB':>9s} {'KB wav>ogg':>12s}")
    for name, w, stem in srcs:
        src = read_wav(w)
        info = json.loads((work / "dec" / f"{name}.json").read_text())
        once = np.fromfile(work / "dec" / f"{name}.once.f32", dtype="<f4").reshape(-1, 2).astype(np.float64)
        loop = np.fromfile(work / "dec" / f"{name}.loop.f32", dtype="<f4").reshape(-1, 2).astype(np.float64)
        n, L = len(src), info["L"]
        len_ok = L == n
        once_ok = len(once) == n
        lap_ok = len(loop) == 2 * L and bool(np.array_equal(loop[:L], loop[L:2 * L]))
        step_in = float(np.abs(np.diff(loop[:L], axis=0)).max())
        step_seam = float(np.abs(loop[L] - loop[L - 1]).max()) if len(loop) > L else 9.0
        seam_ok = step_seam <= max(step_in, 1e-9)
        lag = xcorr_lag(src, loop[:L])
        tl = transient_lags(src, loop[:L]) or [0.0]
        tmax = max(abs(t) for t in tl)
        e0, e1 = band_energy(src, 48000, 30, 250), band_energy(loop[:L], 48000, 30, 250)
        db = 10 * np.log10(max(e1, 1e-30) / max(e0, 1e-30)) if e0 > 0 else 0.0
        ok = len_ok and once_ok and lap_ok and seam_ok and abs(lag) <= 1.0 and tmax <= 1.0 and (abs(db) <= 0.3 or stem != "bass")
        bad += 0 if ok else 1
        why = [t for t, c in (("length", len_ok), ("one-shot frames", once_ok), ("lap", lap_ok), ("seam", seam_ok), ("lag", abs(lag) <= 1.0), ("transients", tmax <= 1.0), ("bass", abs(db) <= 0.3 or stem != "bass")) if not c]
        print(f"{name:34s} {n:7d} {len(once):7d} {'yes' if lap_ok else 'NO':>6s} {'ok' if seam_ok else 'NO':>5s} {lag:6.2f} {tmax:9.2f} {db:9.3f} {sizes[name][0] // 1024:5d}>{sizes[name][1] // 1024:<5d} {','.join(why)}")
    print(f"{len(srcs) - bad}/{len(srcs)} stems pass (frames equal, one-shot exact, lap 2 = lap 1, seam, lag <= 1 frame, bass band within 0.3 dB)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
