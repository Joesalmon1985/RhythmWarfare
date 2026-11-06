"""THROWAWAY (M2.1 spike, part d): pre-rendered tails.
   python offline_tails.py <repo> <packs> <spike folder>
1. The pairs that can occur: every edge of docs/parallel-development/graph/narrative_graph_target.json between two track scenes of content/run/track_scenes.json, every track of
   the outgoing scene (first choice and alternates) against every track of the incoming one, planned by the decision table of MUSIC_TRANSITIONS.md 4.2 (metadata from content/music/tracks).
   For each blend: the exits (the end of every departure lap of the outgoing plan) and so the distinct tails (outgoing track, exit, rate, W). Storage for linger stems or one baked mix.
2. Renders with ffmpeg (rubberband, atempo) of the lingering stems of two real tails: wall time, and quality measured numerically against the source."""
import json, math, os, subprocess, sys, time
from collections import defaultdict
import numpy as np, soundfile as sf
from scipy import signal

REPO, PACKS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SR = 48000
LAP_BARS = 16


def meta(tid):
    p = os.path.join(REPO, "content/music/tracks", tid + ".json")
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def plan(tid, entry="drop1", lead=16, max_laps=12, doors=2):
    d = meta(tid)
    if d is None:
        return None
    bpm = float(d["tempo"]["bpm"]); fd = float(d["tempo"]["first_downbeat_s"]); dur = float(d["duration_s"])
    bar = 240.0 / bpm
    total = int(math.floor((dur - fd) / bar + 1e-6))
    drops = [s for s in d["sections"] if s["role"] == "drop"]
    bar_of = lambda t: int(round((t - fd) / bar))
    if entry == "start":
        eb, dropbar = 0, (bar_of(drops[0]["start_s"]) if drops else 0)
    elif drops:
        dd = drops[1] if entry == "drop2" and len(drops) > 1 else drops[0]
        dropbar = bar_of(dd["start_s"]); eb = dropbar - lead
    else:
        dropbar = 16; eb = 0
    eb = max(eb, 0)
    if total - eb < LAP_BARS:
        eb = max(total - LAP_BARS, 0)
    fit = (total - eb) // LAP_BARS
    half = (dur * 0.5 - fd) / bar
    laps = max(int(round((half - eb) / LAP_BARS)), 2) if entry != "drop2" else max((total - 2 - eb) // LAP_BARS, 2)
    laps = max(1, min(min(laps, max_laps), fit))
    stems = [v["key"] for v in d["voices"]] + ["backing"]
    return dict(id=tid, bpm=bpm, fd=fd, bar=bar, dur=dur, E=eb, L=dropbar - eb, laps=laps, doors=min(doors, laps), entry_t=fd + eb * bar,
                grid_ok=float(d["tempo"].get("drift_ms_max", 0) or 0) <= 20.0, linger=[k for k in stems if k in ("other", "vocals")], stems=stems)


def cents(x):
    return 1200 * math.log2(x)


ts = json.load(open(os.path.join(REPO, "content/run/track_scenes.json"), encoding="utf-8"))
scenes = {}
for path, nodes in ts["paths"].items():
    for node, a in nodes.items():
        lst = [(a["track"], a.get("entry", "drop1"))] + [(x["track"], x.get("entry", "drop1")) for x in a.get("alternates", [])]
        scenes[path + "/" + node] = [p for p in (plan(t, e) for t, e in lst) if p is not None]
g = json.load(open(os.path.join(REPO, "docs/parallel-development/graph/narrative_graph_target.json"), encoding="utf-8"))
edges = sorted({(e["from"], e["to"]) for e in g["edges"] if e["from"] in scenes and e["to"] in scenes and e["from"] != e["to"]})
modes = defaultdict(int)
tails = {}
pairs = set()
cents_hist = []
for a, b in edges:
    for o in scenes[a]:
        for i in scenes[b]:
            rho = i["bpm"] / o["bpm"]
            c = cents(rho)
            pairs.add((o["id"], i["id"]))
            if i["L"] < 5:
                modes["cut (short lead-in)"] += 1
                continue
            if abs(c) <= 50 and o["grid_ok"] and i["grid_ok"]:
                for k in range(o["doors"], o["laps"] + 1):
                    exit_t = o["entry_t"] + k * LAP_BARS * o["bar"]
                    R = (o["dur"] - exit_t) / o["bar"]
                    W = min(12, i["L"] - 4, int(math.floor(R)) - 1)
                    if o["id"] == i["id"]:
                        W = min(W, 4)
                    if W < 2:
                        modes["echo_out (window under 2)"] += 1
                        continue
                    modes["blend"] += 1
                    cents_hist.append(c)
                    key = (o["id"], k, round(rho, 5), W)
                    tails[key] = dict(out=o["id"], exit_lap=k, rho=rho, W=W, seconds=W * 240.0 / i["bpm"], linger=len(o["linger"]), stems=len(o["stems"]))
            else:
                modes["echo_out" + (" (grid)" if abs(c) <= 50 else "")] += 1
n_tails = len(tails)
secs = sum(t["seconds"] for t in tails.values())
linger_secs = sum(t["seconds"] * t["linger"] for t in tails.values())
# bitrates: the packs' own Vorbis (measured on the files here), and a phone encoding at 128 kb/s a stereo stem (an assumption: ruling 24's re-encode is not specified yet)
br = []
for tid in ["chase_status_no_problem_original_mix", "stimpy_party_last_sounds", "unglued_telefonik"]:
    for f in os.listdir(os.path.join(PACKS, tid, "stems")):
        if f.endswith(".ogg"):
            p = os.path.join(PACKS, tid, "stems", f)
            br.append(os.path.getsize(p) * 8 / sf.info(p).duration)
pc_bps = float(np.median(br))
res = {"edges_between_track_scenes": len(edges), "track_pairs": len(pairs), "transitions_by_mode": dict(modes), "distinct_tails": n_tails,
       "tail_seconds_one_mix": secs, "tail_seconds_linger_stems": linger_secs, "pack_vorbis_kbps_median": pc_bps / 1000,
       "storage_mb": {"linger_stems_pack_quality": linger_secs * pc_bps / 8 / 1e6, "one_baked_mix_pack_quality": secs * pc_bps / 8 / 1e6,
                      "linger_stems_128k": linger_secs * 128000 / 8 / 1e6, "one_baked_mix_128k": secs * 128000 / 8 / 1e6},
       "cents_abs_median": float(np.median(np.abs(cents_hist))) if cents_hist else None, "cents_abs_max": float(np.max(np.abs(cents_hist))) if cents_hist else None}
packs_total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(PACKS) if os.path.basename(dp) == "stems" for f in fs if f.endswith(".ogg"))
res["packs_stems_total_gb"] = packs_total / 1e9
print("TAILS edges between track scenes %d, track pairs %d, transitions by mode %s" % (len(edges), len(pairs), dict(modes)))
print("TAILS distinct tails (outgoing track, exit lap, rate, W): %d, %.0f s of tail in all; |cents| of blends median %.1f max %.1f" % (n_tails, secs, res["cents_abs_median"] or 0, res["cents_abs_max"] or 0))
print("TAILS storage: linger stems at pack quality (%.0f kb/s) %.0f MB, one baked mix per tail %.0f MB; at 128 kb/s: %.0f MB and %.0f MB; the packs' stems now: %.2f GB" % (
    pc_bps / 1000, res["storage_mb"]["linger_stems_pack_quality"], res["storage_mb"]["one_baked_mix_pack_quality"], res["storage_mb"]["linger_stems_128k"], res["storage_mb"]["one_baked_mix_128k"], res["packs_stems_total_gb"]))

# ---- 2. renders
def flux(m, hop=48, nfft=1024):
    f, t, Z = signal.stft(m, fs=SR, nperseg=nfft, noverlap=nfft - hop, boundary=None, padded=False)
    mag = np.log1p(100 * np.abs(Z))
    d = np.maximum(np.diff(mag, axis=1), 0).sum(axis=0)
    return d - d.mean()


def flux_lag_ms(a, b, hop=48, max_ms=60):
    fa, fb = flux(a, hop), flux(b, hop)
    n = min(len(fa), len(fb)); fa, fb = fa[:n], fb[:n]
    c = signal.correlate(fa, fb, mode="full", method="fft"); lags = np.arange(-n + 1, n)
    keep = np.abs(lags * hop / SR * 1000) <= max_ms
    j = int(np.argmax(np.where(keep, c, -np.inf)))
    d = 0.5 * (c[j - 1] - c[j + 1]) / (c[j - 1] - 2 * c[j] + c[j + 1]) if 0 < j < len(c) - 1 else 0
    return (lags[j] + d) * hop / SR * 1000


def logspec_cents(m, lo=150, hi=5000):
    f, t, Z = signal.stft(m, fs=SR, nperseg=8192, noverlap=6144)
    P = (np.abs(Z) ** 2).mean(axis=1)
    cc = np.arange(0, int(1200 * np.log2(hi / lo)))
    return np.log(np.interp(lo * 2 ** (cc / 1200), f, P) + 1e-12)


def pitch_cents(x, ref, maxc=120):
    a, b = logspec_cents(x), logspec_cents(ref)
    a, b = a - a.mean(), b - b.mean()
    best, bv = 0, -1e18
    for s in range(-maxc, maxc + 1):
        v = (np.dot(a[s:], b[:len(b) - s]) if s >= 0 else np.dot(a[:s], b[-s:])) / (len(a) - abs(s))
        if v > bv:
            bv, best = v, s
    return best


def lsd_db(y, src, rho, hop_s=0.05, nfft=4096, lo=300, hi=12000):
    """Log-spectral distance (dB, per-frame mean removed) between output y and the source at the matching musical position (source time = output time x rho)."""
    win = np.hanning(nfft); fq = np.fft.rfftfreq(nfft, 1 / SR); band = (fq >= lo) & (fq <= hi)
    d = []
    u = nfft / SR
    while (u + nfft / SR) < len(y) / SR and (u * rho + nfft / SR) < len(src) / SR:
        a = int(u * SR - nfft // 2); b = int(u * rho * SR - nfft // 2)
        A = 10 * np.log10(np.abs(np.fft.rfft(y[a:a + nfft] * win))[band] ** 2 + 1e-10)
        B = 10 * np.log10(np.abs(np.fft.rfft(src[b:b + nfft] * win))[band] ** 2 + 1e-10)
        if B.mean() > -60:
            A -= A.mean(); B -= B.mean()
            d.append(np.sqrt(np.mean((A - B) ** 2)))
        u += hop_s
    return float(np.mean(d))


def sharp(m):
    """Transient sharpness: the 99th percentile of onset flux over its median."""
    f = flux(m) + 1e-9
    f = f - f.min()
    return float(np.percentile(f, 99) / (np.median(f) + 1e-9))


cases = [("chase_status_no_problem_original_mix", 76.817, 172.0 / 174.9997, 12, 172.0), ("unglued_telefonik", 66.976, 176.9999 / 172.0003, 12, 176.9999)]
renders = []
os.makedirs(os.path.join(OUT, "tails"), exist_ok=True)
for tid, t0, rho, W, in_bpm in cases:
    out_s = W * 240.0 / in_bpm
    src_s = out_s * rho
    for stem in ("other", "vocals"):
        p = os.path.join(PACKS, tid, "stems", stem + ".ogg")
        x, _ = sf.read(p, start=int(t0 * SR), stop=int((t0 + src_s + 0.5) * SR), dtype="float32", always_2d=True)
        src = x.sum(axis=1)
        for method, af in (("rubberband", "rubberband=tempo=%.6f:pitchq=quality:transients=crisp" % rho), ("rubberband_smooth", "rubberband=tempo=%.6f:pitchq=quality:transients=smooth:window=long" % rho),
                           ("atempo", "atempo=%.6f" % rho)):
            dst = os.path.join(OUT, "tails", "%s.%s.%s.ogg" % (tid, stem, method))
            c0 = time.time()
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "%.4f" % t0, "-t", "%.4f" % src_s, "-i", p, "-af", af, "-c:a", "libvorbis", "-q:a", "6", dst], capture_output=True, text=True)
            wall = time.time() - c0
            if r.returncode != 0:
                print("RENDER failed", method, r.stderr[:300]); continue
            y, _ = sf.read(dst, dtype="float32", always_2d=True)
            ym = y.sum(axis=1)
            # timing: the render against the source resampled to the output time line (pitch_scale-like timing, correct by construction), at the start and at the end
            from fractions import Fraction
            fr = Fraction(1 / rho).limit_denominator(3000)
            ref = signal.resample_poly(src, fr.numerator, fr.denominator)
            n3 = int(3.0 * SR)
            lag_start = flux_lag_ms(ym[:n3], ref[:n3])
            m_end = min(len(ym), len(ref))
            lag_end = flux_lag_ms(ym[m_end - n3:m_end], ref[m_end - n3:m_end])
            rec = dict(track=tid, stem=stem, method=method, rho=rho, cents_asked=cents(rho), render_s=wall, out_s=len(ym) / SR, expected_out_s=out_s,
                       pitch_cents=pitch_cents(ym, src), lag_start_ms=lag_start, lag_end_ms=lag_end, lsd_db=lsd_db(ym, src, rho), sharp_ratio=sharp(ym) / sharp(src), bytes=os.path.getsize(dst))
            renders.append(rec)
            print("RENDER %s %s %-17s %.0f cents: %.2f s to render %.1f s, length %.3f s (asked %.3f), pitch %+d cents, onsets %+.2f ms at the start %+.2f ms at the end, LSD %.2f dB, transient sharpness x%.2f" % (
                tid[:12], stem, method, cents(rho), wall, src_s, len(ym) / SR, out_s, rec["pitch_cents"], lag_start, lag_end, rec["lsd_db"], rec["sharp_ratio"]))
        # the pitch_scale-only tail for comparison (the same LSD, which includes the pitch change itself)
        ref = signal.resample_poly(src, *(lambda f: (f.numerator, f.denominator))(__import__("fractions").Fraction(1 / rho).limit_denominator(3000)))
        renders.append(dict(track=tid, stem=stem, method="pitch_scale (resampled, for comparison)", lsd_db=lsd_db(ref, src, rho), pitch_cents=pitch_cents(ref, src), sharp_ratio=sharp(ref) / sharp(src)))
        print("RENDER %s %s %-17s: pitch %+d cents, LSD %.2f dB, transient sharpness x%.2f" % (tid[:12], stem, "pitch_scale only", renders[-1]["pitch_cents"], renders[-1]["lsd_db"], renders[-1]["sharp_ratio"]))
res["renders"] = renders
json.dump(res, open(os.path.join(OUT, "offline_tails.json"), "w"), indent=1, default=float)
