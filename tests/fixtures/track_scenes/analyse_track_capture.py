"""Cue time against the audio itself, from a capture of the RunTrack bus (tests/fixtures/track_scenes/measure_track_audio.gd with RW_MEASURE_CAPTURE=<folder>).

   python analyse_track_capture.py <folder>        (numpy, scipy, soundfile; the packs named in the log must be on this PC)

Song time of capture frame f: p(f) = clock + (f - pushed) / rate, from the frame log row (clock position and the capture's frame count, read together under AudioServer.lock) nearest
before f. A group started (or sought) at song time t0 on track time track_t0 should hold track time track_t0 + (p - t0) at song time p: that is where the engine puts its cues. Every 2 s
a 0.5 s window of the capture (band 1 to 8 kHz) is cross-correlated against the pack's stems mixed at their gains, over +-80 ms: late_ms > 0 means the audio is later than the cues. The
output latency is not in it (it delays every sound alike; calibration is for that)."""
import json, os, re, sys
import numpy as np, soundfile as sf
from scipy import signal

F = sys.argv[1]
SR = 48000
SOS = signal.butter(4, [1000, 8000], btype="bandpass", fs=SR, output="sos")
log = json.loads(re.sub(r"\bnan\b", "NaN", open(os.path.join(F, "run_track.json")).read()))  # (Godot writes a NaN as nan)
capx = np.fromfile(os.path.join(F, "run_track.f32"), dtype=np.float32).reshape(-1, 2)
rows = np.array(log["rows"], float)
print("CAPTURE driver %s, output latency %.2f ms, %d frames (%.1f s), discarded %d" % (log["driver"], log["output_latency"] * 1000, len(capx), len(capx) / SR, log["discarded"]))
off = rows[:, 1] / SR - rows[:, 0]
print("CAPTURE clock against capture frames: spread %.3f ms (0 means the two counters ran together)" % ((off.max() - off.min()) * 1000))


def f_of(p):
    i = max(np.searchsorted(rows[:, 0], p, side="right") - 1, 0)
    return int(round(rows[i, 1] + (p - rows[i, 0]) * SR))


def p_of(f):
    i = max(np.searchsorted(rows[:, 1], f, side="right") - 1, 0)
    return rows[i, 0] + (f - rows[i, 1]) / SR


def read(dir_, stem, t0, t1):
    a0 = int(round(t0 * SR)); a1 = int(round(t1 * SR))
    x, _ = sf.read(os.path.join(dir_, "stems", stem + ".ogg"), start=max(a0, 0), stop=a1, dtype="float32", always_2d=True)
    if a0 < 0:
        x = np.vstack([np.zeros((-a0, 2), np.float32), x])
    return x


starts = [x for x in log["log"] if x["kind"] == "start"]
segs = log["log"]
results = []
end_p = p_of(len(capx) - 1)
for k, s in enumerate(segs):
    t0 = float(s["t"]); tt0 = float(s["track_t"])
    t_end = float(segs[k + 1]["t"]) if k + 1 < len(segs) else end_p
    start = next((x for x in reversed(starts) if float(x["t"]) <= t0 + 1e-6 and x["track"] == s["track"]), None)
    if start is None:
        continue
    dir_ = log["dirs"].get(s["track"], "")
    stems = list(zip(start["stems"], start["gains"]))
    win, m = int(0.5 * SR), int(0.08 * SR)
    rs = []
    p = t0 + 0.8
    while p + 0.6 < t_end:
        f0 = f_of(p)
        if f0 < 0 or f0 + win > len(capx):
            break
        pp = p_of(f0)
        tau = tt0 + (pp - t0)
        ref = None
        for key, g in stems:
            x = read(dir_, key, tau - 0.08, tau + 0.5 + 0.08) * g
            ref = x if ref is None else ref + x
        cw = signal.sosfiltfilt(SOS, capx[f0:f0 + win].sum(axis=1))
        rw = signal.sosfiltfilt(SOS, ref.sum(axis=1))[: win + 2 * m]
        if np.std(cw) > 1e-5 and len(rw) == win + 2 * m:
            c = signal.correlate(rw, cw, mode="valid", method="fft")
            j = int(np.argmax(c))
            d = 0.5 * (c[j - 1] - c[j + 1]) / (c[j - 1] - 2 * c[j] + c[j + 1]) if 0 < j < len(c) - 1 else 0.0
            pk = c[j] / (np.linalg.norm(rw[j:j + win]) * np.linalg.norm(cw) + 1e-12)
            rs.append((pp, -((j + d) - m) / SR * 1000.0, pk))
        p += 2.0
    good = [r for r in rs if r[2] > 0.5]
    if len(good) >= 2:
        a = np.array([r[1] for r in good]); ts = np.array([r[0] for r in good])
        slope = np.polyfit(ts, a, 1)[0] * 100
        results.append(dict(kind=s["kind"], track=s["track"], t=t0, lateness_ms_logged=s.get("lateness_ms"), n=len(good), mean_ms=float(a.mean()), min_ms=float(a.min()), max_ms=float(a.max()), drift_ms_per_100s=float(slope), span_s=float(ts[-1] - ts[0])))
        print("CAPTURE %s %s at t=%.3f (logged lateness %.2f ms): %d windows over %.1f s, audio late against the cues mean %.3f ms, min %.3f, max %.3f, drift %.3f ms per 100 s" % (
            s["kind"], s["track"], t0, float(s.get("lateness_ms", 0)), len(good), ts[-1] - ts[0], a.mean(), a.min(), a.max(), slope))
    else:
        print("CAPTURE %s %s at t=%.3f: too few windows (%d)" % (s["kind"], s["track"], t0, len(rs)))
json.dump(results, open(os.path.join(F, "run_track_analysis.json"), "w"), indent=1)
