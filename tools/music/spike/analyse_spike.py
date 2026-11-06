"""THROWAWAY (M2.1 spike): measures the captures of tools/music/spike/transition_spike.gd against the stems decoded here (libsndfile), numerically.
   python analyse_spike.py <spike folder> [names...]  -> prints one line per figure and writes <folder>/analysis.json

For a capture frame f of bus X, the song time (the clock's mix position) is p(f) = cp + (f - pushed_X) / sr, from the frame log row nearest before f (cp and pushed were read together under
AudioServer.lock). The content a group SHOULD have at p is its plan: tail tau(p) = out_t_at_T + (p - T) * r after T (r = 1 before), incoming entry_t + (p - T). The content it HAS is found by
cross-correlating 0.5 s windows of the capture (band 1 to 8 kHz, both sides) against the stems mixed at the logged gains, resampled at the rate, over +-60 ms. late_ms > 0: the audio is later
than the clock says (in song time, the output latency excluded: it is common to every sound)."""
import json, os, sys, time
import numpy as np, soundfile as sf
from scipy import signal

SR = 48000
F = sys.argv[1]
ONLY = sys.argv[2:]
SOS = signal.butter(4, [1000, 8000], btype="bandpass", fs=SR, output="sos")
out = {}


def cap(name, bus):
    a = np.fromfile(os.path.join(F, "%s.%s.f32" % (name, bus)), dtype=np.float32).reshape(-1, 2)
    return a


def stems(pack, t0, t1):
    """{key: stereo array of source seconds t0..t1} (zero-padded before 0)."""
    res = {}
    for s in pack["stems"]:
        path = os.path.join(pack["dir"], s["stem"])
        a0, a1 = int(round(t0 * SR)), int(round(t1 * SR))
        pad = max(0, -a0)
        x, sr = sf.read(path, start=max(a0, 0), stop=a1, dtype="float32", always_2d=True)
        assert sr == SR
        if pad:
            x = np.vstack([np.zeros((pad, 2), np.float32), x])
        res[s["key"]] = x
    return res


class Plan:
    def __init__(self, log):
        self.log = log
        self.T = log["T"]
        e = log["exp"]
        self.e = e
        fr = np.array([r[:9] for r in log["frames"]], float)
        self.fr = fr
        self.col = {"SpikeA": 4, "SpikeB": 5, "SpikeSumPre": 6, "SpikeSumPost": 7}
        self.paused = []
        ev = log["events"]
        for i, x in enumerate(ev):
            if x["kind"] == "pause":
                self.paused.append(x["wall"])

    def p_of(self, bus, f):
        """Song time of capture frame f of `bus` (from the last row whose pushed count is <= f and whose clock is running)."""
        c = self.fr[:, self.col[bus]]
        i = np.searchsorted(c, f, side="right") - 1
        i = max(i, 0)
        return self.fr[i, 1] + (f - c[i]) / SR, i

    def f_of(self, bus, p):
        """First capture frame at song time p (the clock runs: no pause near p)."""
        c = self.fr[:, self.col[bus]]
        cp = self.fr[:, 1]
        i = np.searchsorted(cp, p, side="right") - 1
        i = max(i, 0)
        return int(round(c[i] + (p - cp[i]) * SR))


def mono_band(x):
    m = x.sum(axis=1) if x.ndim == 2 else x
    return signal.sosfiltfilt(SOS, m)


def resample_at(x, r, n):
    """x played at rate r: output sample k is source sample k * r (linear interpolation), n samples."""
    k = np.arange(n) * r
    i = np.floor(k).astype(int)
    fr = (k - i)[:, None]
    i = np.clip(i, 0, len(x) - 2)
    return x[i] * (1 - fr) + x[i + 1] * fr


def lag_of(capw, ref, margin):
    """Lag (samples, sub-sample) at which ref[margin + lag : ...] best matches capw; and the normalised peak."""
    c = signal.correlate(ref, capw, mode="valid", method="fft")  # length 2*margin+1; index j means ref[j:j+n] ~ capw
    j = int(np.argmax(c))
    if 0 < j < len(c) - 1:
        y0, y1, y2 = c[j - 1], c[j], c[j + 1]
        d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) if (y0 - 2 * y1 + y2) != 0 else 0.0
    else:
        d = 0.0
    seg = ref[j:j + len(capw)]
    nrm = float(c[j] / (np.linalg.norm(seg) * np.linalg.norm(capw) + 1e-12))
    return (j + d) - margin, nrm


def gains_at(log, t):
    g = log["gains"]
    if not g:
        return None
    ts = np.array([x[0] for x in g])
    i = max(np.searchsorted(ts, t, side="right") - 1, 0)
    return g[i][1]


def track_lag(pl, bus, which, t_from, t_to, step=0.5, win=0.5, margin_s=0.06, gain_fn=None):
    """[(song t, late_ms, peak)] for group `which` (a: tail, b: incoming) on `bus`."""
    e = pl.e
    T = pl.T
    capx = cap(e["name"], bus)
    r = e["rate"]
    pack = e["out"] if which == "a" else e["inc"]
    res = []
    n = int(win * SR)
    m = int(margin_s * SR)
    t = t_from
    cache = {}
    while t + win <= t_to:
        f0 = pl.f_of(bus, t)
        p0, _ = pl.p_of(bus, f0)
        if f0 < 0 or f0 + n > len(capx):
            t += step
            continue
        if which == "a":
            rr = r if p0 >= T else 1.0
            tau0 = e["out_t_at_T"] + (p0 - T) * (r if p0 >= T else 1.0)
        else:
            rr = 1.0
            tau0 = e["in_entry_t"] + (p0 - T)
        src_t0 = tau0 - margin_s * rr
        st = stems(pack, src_t0, src_t0 + (win + 2 * margin_s) * rr + 0.01)
        gl = gain_fn(p0) if gain_fn else None
        mix = None
        for i, s in enumerate(pack["stems"]):
            g = (gl[i] if gl is not None else s["gain"])
            x = st[s["key"]] * g
            mix = x if mix is None else mix + x
        ref = resample_at(mix, rr, n + 2 * m)
        capw = mono_band(capx[f0:f0 + n])
        refm = mono_band(ref)
        if np.std(capw) < 1e-5:
            t += step
            continue
        lag, pk = lag_of(capw, refm, m)
        # ref[m + lag] matches capture start: the capture holds content tau0 + lag * rr / SR -> it is AHEAD by lag*rr/SR of content, i.e. early in time by lag / SR
        late_ms = -lag / SR * 1000.0
        res.append((round(p0, 3), round(late_ms, 3), round(pk, 3)))
        t += step
    return res


def summary(rows, label):
    if not rows:
        print("ANALYSE", label, "no windows")
        return {}
    a = np.array([r[1] for r in rows]); pk = np.array([r[2] for r in rows]); ts = np.array([r[0] for r in rows])
    good = pk > 0.5
    if good.sum() >= 2:
        slope = np.polyfit(ts[good], a[good], 1)[0] * 100.0
    else:
        slope = float("nan")
    s = {"n": int(len(a)), "n_good": int(good.sum()), "mean_ms": float(np.mean(a[good])) if good.any() else None, "min_ms": float(a[good].min()) if good.any() else None,
         "max_ms": float(a[good].max()) if good.any() else None, "drift_ms_per_100s": float(slope), "peak_median": float(np.median(pk))}
    print("ANALYSE %s: %d windows (%d with peak > 0.5): late mean %.3f ms, min %.3f, max %.3f, drift %.3f ms per 100 s, median peak %.2f" % (
        label, s["n"], s["n_good"], s["mean_ms"] or 0, s["min_ms"] or 0, s["max_ms"] or 0, slope, s["peak_median"]))
    return s


def flux(x, hop=48, nfft=1024):
    m = x.sum(axis=1) if x.ndim == 2 else x
    f, t, Z = signal.stft(m, fs=SR, nperseg=nfft, noverlap=nfft - hop, boundary=None, padded=False)
    mag = np.log1p(100 * np.abs(Z))
    d = np.maximum(np.diff(mag, axis=1), 0).sum(axis=0)
    return d - d.mean()


def flux_lag(capx, ref, max_ms=150, hop=48):
    a, b = flux(capx, hop), flux(ref, hop)
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    c = signal.correlate(a, b, mode="full", method="fft")
    lags = np.arange(-n + 1, n)
    keep = np.abs(lags * hop / SR * 1000) <= max_ms
    j = np.argmax(np.where(keep, c, -np.inf))
    if 0 < j < len(c) - 1:
        y0, y1, y2 = c[j - 1], c[j], c[j + 1]
        d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)
    else:
        d = 0
    return (lags[j] + d) * hop / SR * 1000.0  # > 0: capture later than ref


def avg_logspec_cents(x, lo=150, hi=5000):
    m = x.sum(axis=1) if x.ndim == 2 else x
    f, t, Z = signal.stft(m, fs=SR, nperseg=8192, noverlap=6144)
    P = (np.abs(Z) ** 2).mean(axis=1)
    cents = np.arange(0, int(1200 * np.log2(hi / lo)))
    fq = lo * 2 ** (cents / 1200)
    return np.log(np.interp(fq, f, P) + 1e-12)


def pitch_offset_cents(x, ref, maxc=120):
    a, b = avg_logspec_cents(x), avg_logspec_cents(ref)
    a, b = a - a.mean(), b - b.mean()
    best, bc = None, -1e18
    for s in range(-maxc, maxc + 1):
        if s >= 0:
            v = np.dot(a[s:], b[:len(b) - s])
        else:
            v = np.dot(a[:s], b[-s:])
        v /= (len(a) - abs(s))
        if v > bc:
            bc, best = v, s
    return best


def clicks(capx, refx, lo_hz=6000, win=96):
    """Click measure: the largest excess of high-band energy (>lo_hz) in 2 ms frames over the median of the 40 ms around it, capture against a reference (dB)."""
    sos = signal.butter(4, lo_hz, btype="highpass", fs=SR, output="sos")

    def ex(x):
        h = signal.sosfilt(sos, x.sum(axis=1) if x.ndim == 2 else x)
        n = len(h) // win
        e = (h[:n * win].reshape(n, win) ** 2).mean(axis=1) + 1e-14
        med = signal.medfilt(e, 21)
        return 10 * np.log10(e / (med + 1e-14))
    a, b = ex(capx), ex(refx)
    return float(a.max()), float(b.max()), float(np.percentile(a, 99.9)), float(np.percentile(b, 99.9))


def analyse(name):
    log = json.load(open(os.path.join(F, name + ".json")))
    e = log["exp"]
    pl = Plan(log)
    T = pl.T
    res = {"driver": log["driver"], "output_latency_ms": log["output_latency"] * 1000, "mem": log["mem"], "discarded": log["discarded"]}
    fr = pl.fr
    off = fr[:, 4] / SR - fr[:, 1]
    res["map_spread_ms"] = float((off.max() - off.min()) * 1000)
    ft = fr[:, 8][1:]
    res["frame_ms_max"] = float(ft.max()); res["frame_ms_p99"] = float(np.percentile(ft, 99))
    print("ANALYSE ---- %s (%s, %s): capture map spread %.3f ms (pauses move it), frames max %.1f ms p99 %.1f ms" % (name, e["mode"], log["driver"], res["map_spread_ms"], res["frame_ms_max"], res["frame_ms_p99"]))
    bev = [x for x in log["events"] if x["kind"] == "boundary"]
    if bev:
        res["boundary"] = bev[0]
        print("ANALYSE boundary call: now %.4f ttnm %.2f ms late %.2f ms" % (bev[0]["now"], bev[0]["ttnm"] * 1000, bev[0]["late"] * 1000))
    mode = e["mode"]
    if mode == "identity":
        # the outgoing alone at rate 1, PitchShift (pitch 1.0) switched on at T: its latency against the plain group before T
        rows_pre = track_lag(pl, "SpikeA", "a", 0.3, T - 0.05, step=0.25)
        res["a_before_T"] = summary(rows_pre, "tail before T (no effect)")
        capx = cap(name, "SpikeA")
        f0 = pl.f_of("SpikeA", T + 0.5)
        n = int(4.0 * SR)
        p0, _ = pl.p_of("SpikeA", f0)
        tau0 = e["out_t_at_T"] + (p0 - T)
        st = stems(e["out"], tau0, tau0 + 4.0)
        ref = sum(st[s["key"]] * s["gain"] for s in e["out"]["stems"])
        lat_flux = flux_lag(capx[f0:f0 + n], ref)
        # raw cross-correlation over +-100 ms as well (the shifter at 1.0 should keep the waveform close)
        m = int(0.1 * SR)
        st2 = stems(e["out"], tau0 - 0.1, tau0 + 4.0 + 0.1)
        ref2 = sum(st2[s["key"]] * s["gain"] for s in e["out"]["stems"])
        lag, pk = lag_of(mono_band(capx[f0:f0 + n]), mono_band(ref2), m)
        res["pitchshift_identity"] = {"latency_ms_flux": lat_flux, "latency_ms_xcorr": -lag / SR * 1000, "xcorr_peak": pk}
        print("ANALYSE PitchShift at pitch 1.0 (fft 2048, oversampling 4): latency %.2f ms by onset flux, %.2f ms by waveform (peak %.2f)" % (lat_flux, -lag / SR * 1000, pk))
    if mode in ("blend", "echo_out"):
        gfn = lambda p: gains_at(log, p)
        end_a = T + e["complete_s"] - 0.1
        rows_a_pre = track_lag(pl, "SpikeA", "a", 0.5, T - 0.05, step=0.25)
        rows_a = track_lag(pl, "SpikeA", "a", T + 0.02, end_a, step=0.5, gain_fn=gfn) if not e.get("pitch_shift") else []
        rows_b = track_lag(pl, "SpikeB", "b", T + 0.02, T + e["post_s"] - 0.1, step=0.5)
        res["a_before_T"] = summary(rows_a_pre, "tail before T")
        if rows_a:
            res["a_after_T"] = summary(rows_a, "tail after T (rate %.6f, %.1f cents)" % (e["rate"], e["cents"]))
        res["b"] = summary(rows_b, "incoming from T")
        res["rows"] = {"a_pre": rows_a_pre, "a": rows_a, "b": rows_b}
        if rows_b:
            print("ANALYSE incoming first window (play(from) accuracy, Q6): late %.3f ms at t=%.3f" % (rows_b[0][1], rows_b[0][0]))
        if rows_a and rows_b:
            # tail beat against the incoming beat: the difference of their lateness in the same windows
            da = {r[0]: r[1] for r in rows_a if r[2] > 0.5}
            dd = [(t, da[t] - lb) for (t, lb, pk) in rows_b if t in da and pk > 0.5]
            if dd:
                arr = np.array([x[1] for x in dd])
                res["tail_minus_incoming_ms"] = {"mean": float(arr.mean()), "max_abs": float(np.abs(arr).max()), "n": len(arr)}
                print("ANALYSE tail beat minus incoming beat: mean %.3f ms, max |.| %.3f ms over %d windows" % (arr.mean(), np.abs(arr).max(), len(arr)))
        if e.get("pitch_shift"):
            capx = cap(name, "SpikeA")
            f0 = pl.f_of("SpikeA", T + 0.3)
            n = int(2.2 * SR)  # the drums are in for 2 bars: onsets to align
            p0, _ = pl.p_of("SpikeA", f0)
            tau0 = e["out_t_at_T"] + (p0 - T) * e["rate"]
            st = stems(e["out"], tau0, tau0 + 2.5 * e["rate"] + 0.1)
            ref = resample_at(sum(st[s["key"]] * s["gain"] for s in e["out"]["stems"]), e["rate"], n)
            lat = flux_lag(capx[f0:f0 + n], ref)
            res["pitchshift_latency_ms_flux"] = lat
            print("ANALYSE PitchShift pitch %.4f on the tail at rate %.4f: tail later than the rate-only reference by %.2f ms (onset flux)" % (1 / e["rate"], e["rate"], lat))
            # pitch of the tail against the source at rate 1, linger stems, bars 2 to 10
            f1 = pl.f_of("SpikeA", T + 2.2 * e["bar_in"])
            n2 = int(6 * e["bar_in"] * SR)
            p1, _ = pl.p_of("SpikeA", f1)
            tau1 = e["out_t_at_T"] + (p1 - T) * e["rate"]
            st2 = stems(e["out"], tau1, tau1 + n2 / SR * e["rate"])
            src = sum(st2[k] for k in ("other", "vocals") if k in st2)
            res["pitchshift_pitch_cents"] = pitch_offset_cents(capx[f1:f1 + n2], src)
            print("ANALYSE PitchShift tail pitch against the source: %+d cents (0 is the aim; rate only would be %+.1f)" % (res["pitchshift_pitch_cents"], e["cents"]))
        if not e.get("pitch_shift") and mode == "blend":
            capx = cap(name, "SpikeA")
            f1 = pl.f_of("SpikeA", T + 2.2 * e["bar_in"])
            n2 = int(6 * e["bar_in"] * SR)
            p1, _ = pl.p_of("SpikeA", f1)
            tau1 = e["out_t_at_T"] + (p1 - T) * e["rate"]
            st2 = stems(e["out"], tau1, tau1 + n2 / SR * e["rate"])
            src = sum(st2[k] for k in ("other", "vocals") if k in st2)
            res["tail_pitch_cents"] = pitch_offset_cents(capx[f1:f1 + n2], src)
            print("ANALYSE tail pitch against the source (pitch_scale only): %+d cents (expected %+.1f)" % (res["tail_pitch_cents"], e["cents"]))
        # Q7: clicks at the step of the rate and in the fades: capture of the tail against the same stems mixed with SMOOTH per-sample gains (no chunk steps), rate 1 runs only
        if e["rate"] == 1.0 and not e.get("effects", True):
            capx = cap(name, "SpikeA")
            f0 = pl.f_of("SpikeA", T - 0.5)
            n = int((1.0 + 1.6 * e["bar_in"]) * SR)
            p0, _ = pl.p_of("SpikeA", f0)
            lag_ms = np.median([r[1] for r in rows_a_pre[-4:]])
            tau0 = e["out_t_at_T"] + (p0 - T) - lag_ms / 1000.0
            st = stems(e["out"], tau0, tau0 + n / SR + 0.01)
            ts = p0 + np.arange(n) / SR
            ref = np.zeros((n, 2))
            for i, s in enumerate(e["out"]["stems"]):
                g = np.array([0.0])
                kind = "linger" if s["key"] in ("other", "vocals") else "rhythm"
                b = np.clip((ts - T) / e["bar_in"], 0, None)
                if kind == "linger":
                    g = np.cos(np.pi / 2 * np.clip(b, 0, 1))
                else:
                    g = np.cos(np.pi / 2 * np.clip(b / 0.125, 0, 1))
                g = np.where(ts < T, 1.0, g) * s["gain"]
                ref += st[s["key"]][:n] * g[:, None]
            c = clicks(capx[f0:f0 + n], ref)
            resid = capx[f0:f0 + n] - ref
            res["clicks"] = {"capture_max_db": c[0], "smooth_ref_max_db": c[1], "capture_p999_db": c[2], "smooth_ref_p999_db": c[3],
                             "residual_rms_db_rel": float(10 * np.log10((resid ** 2).mean() / ((ref ** 2).mean() + 1e-12)))}
            print("ANALYSE Q7 half-beat cut and 1-bar fade (rate 1, no effects): high-band (>6 kHz) excess, capture max %.1f dB p99.9 %.1f dB; smooth reference max %.1f dB p99.9 %.1f dB; residual %.1f dB under the signal" % (
                c[0], c[2], c[1], c[3], -res["clicks"]["residual_rms_db_rel"]))
        if mode == "blend" and not e.get("pitch_shift") and e.get("pauses", 0) == 0:
            # Q7 for the rate step at T: high-band excess of the tail capture around T against the same span before
            capx = cap(name, "SpikeA")
            fT = pl.f_of("SpikeA", T)
            seg = capx[fT - int(0.3 * SR): fT + int(0.3 * SR)]
            c = clicks(seg, seg)
            res["rate_step_click_db"] = c[0]
            print("ANALYSE rate step at T: high-band excess max %.1f dB in the 0.6 s around T (a click shows as a spike of 10 dB or more)" % c[0])
        # Q8: the limiter in the first 4 bars after T
        pre = cap(name, "SpikeSumPre"); post = cap(name, "SpikeSumPost")
        f0 = pl.f_of("SpikeSumPre", T); f1 = pl.f_of("SpikeSumPre", T + 4 * e["bar_in"])
        fb = pl.f_of("SpikeSumPre", max(T - 2.5, 0.2))
        w = int(0.01 * SR)

        def pk_db(x):
            n = len(x) // w
            return 20 * np.log10(np.abs(x[:n * w]).reshape(n, w, 2).max(axis=(1, 2)) + 1e-9)
        a, b = pk_db(pre[f0:f1]), pk_db(post[f0:f1])
        red = a - b
        res["limiter"] = {"peak_pre_dbfs": float(a.max()), "peak_post_dbfs": float(b.max()), "max_reduction_db": float(red.max()), "p95_reduction_db": float(np.percentile(red, 95)),
                          "pct_10ms_windows_reducing_over_1db": float((red > 1).mean() * 100), "peak_pre_before_T_dbfs": float(pk_db(pre[fb:f0]).max())}
        print("ANALYSE Q8 limiter, first 4 incoming bars: peak into the limiter %+.2f dBFS (the outgoing alone before T %+.2f), out %+.2f; reduction max %.2f dB, p95 %.2f dB, %.1f%% of 10 ms windows over 1 dB" % (
            a.max(), res["limiter"]["peak_pre_before_T_dbfs"], b.max(), red.max(), np.percentile(red, 95), res["limiter"]["pct_10ms_windows_reducing_over_1db"]))
        # the floor: the tail bus after complete_t (echo repeats included)
        capx = cap(name, "SpikeA")
        ff = pl.f_of("SpikeA", T + e["complete_s"] + 0.05)
        tailpart = capx[ff:]
        res["after_floor_peak_dbfs"] = float(20 * np.log10(np.abs(tailpart).max() + 1e-12)) if len(tailpart) else None
        print("ANALYSE tail bus after the floor (complete_t + 50 ms to the end): peak %s dBFS" % ("%.1f" % res["after_floor_peak_dbfs"] if res["after_floor_peak_dbfs"] is not None else "-"))
        if e.get("pauses", 0):
            # Q1: the offsets between pauses
            ev = log["events"]
            res["pauses"] = []
            print("ANALYSE Q1 %d pause cycles: windows between them (tail late, incoming late, difference) in ms:" % e["pauses"])
            rows_a2 = track_lag(pl, "SpikeA", "a", T + 0.02, end_a, step=0.25, win=0.25, gain_fn=gfn)
            rows_b2 = track_lag(pl, "SpikeB", "b", T + 0.02, end_a, step=0.25, win=0.25)
            res["rows_q1"] = {"a": rows_a2, "b": rows_b2}
            da = {r[0]: r for r in rows_a2}
            seq = [(t, da[t][1], lb, da[t][1] - lb) for (t, lb, pk) in rows_b2 if t in da and pk > 0.4 and da[t][2] > 0.4]
            for x in seq:
                print("ANALYSE   t=%.2f tail %.3f incoming %.3f diff %.3f" % x)
            res["q1_seq"] = seq
    out[name] = res


names = ONLY or [f[:-5] for f in sorted(os.listdir(F)) if f.endswith(".json") and f not in ("experiments.json", "analysis.json")]
for n in names:
    if os.path.exists(os.path.join(F, n + ".SpikeA.f32")):
        t0 = time.time()
        analyse(n)
json.dump(out, open(os.path.join(F, "analysis.json" if not ONLY else "analysis_%s.json" % "_".join(ONLY)), "w"), indent=1, default=float)


def hf_ratio(capx, refx, lo_hz=6000, win=96):
    """Per 2 ms frame, high-band (> lo_hz) energy of the capture over that of a reference made offline with smooth gains (dB): a click is energy the reference does not have."""
    sos = signal.butter(4, lo_hz, btype="highpass", fs=SR, output="sos")

    def en(x):
        h = signal.sosfilt(sos, x.sum(axis=1) if x.ndim == 2 else x)
        n = len(h) // win
        return (h[:n * win].reshape(n, win) ** 2).mean(axis=1)
    a, b = en(capx), en(refx)
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    keep = b > 1e-9
    r = 10 * np.log10((a[keep] + 1e-14) / (b[keep] + 1e-14))
    where = (np.nonzero(keep)[0][r > 3] * win / SR).round(3).tolist()
    lvl = 10 * np.log10(a[keep][r > 3] / (np.median(a[: n // 6]) + 1e-14) + 1e-14) if (r > 3).any() else np.array([-200.0])
    return {"where_s": where, "excess_level_db_max": float(lvl.max()), "max_db": float(r.max()), "p999_db": float(np.percentile(r, 99.9)), "median_db": float(np.median(r)), "frames_over_3db": int((r > 3).sum()), "frames": int(len(r))}


def step_check(name, span_bars=None):
    """Q7: the tail's own capture around T against the stems mixed offline with smooth per-sample gains (the recipe's curves) and the rate switched exactly at T."""
    log = json.load(open(os.path.join(F, name + ".json")))
    e = log["exp"]; pl = Plan(log); T = pl.T
    capx = cap(name, "SpikeA")
    t0 = T - 0.4
    t1 = T + (span_bars or 1.6) * e["bar_in"]
    rows = track_lag(pl, "SpikeA", "a", 0.5, T - 0.05, step=0.25)
    lag_ms = float(np.median([r[1] for r in rows[-4:]]))
    f0 = pl.f_of("SpikeA", t0); f1 = pl.f_of("SpikeA", t1)
    n = f1 - f0
    p0, _ = pl.p_of("SpikeA", f0)
    ts = p0 + np.arange(n) / SR
    r = e["rate"]
    rows_post = track_lag(pl, "SpikeA", "a", T + 0.02, T + 1.5, step=0.25, win=0.25, gain_fn=lambda p: gains_at(log, p))
    lag_post = float(np.median([x[1] for x in rows_post])) if rows_post else lag_ms
    tau = np.where(ts < T, e["out_t_at_T"] + (ts - T) - lag_ms / 1000.0, e["out_t_at_T"] + (ts - T) * r - lag_post / 1000.0 * r)
    st = stems(e["out"], tau[0] - 0.01, tau[-1] + 0.01)
    base = tau[0] - 0.01
    ref = np.zeros((n, 2))
    b = np.clip((ts - T) / e["bar_in"], 0, None)
    for s in e["out"]["stems"]:
        x = st[s["key"]]
        # band-limited resampling (scipy resample_poly) piecewise: rate 1 before T, the tail's rate after
        from fractions import Fraction
        nb = int(np.sum(ts < T))
        i0 = int(round((tau[0] - base) * SR))
        y0 = x[i0:i0 + nb]
        iT = int(round((tau[nb] - base) * SR)) if nb < n else len(x)
        fr_ = Fraction(1 / r).limit_denominator(3000)
        y1 = signal.resample_poly(x[iT:], fr_.numerator, fr_.denominator, axis=0) if nb < n else np.zeros((0, 2))
        y = np.vstack([y0, y1])[:n]
        if len(y) < n:
            y = np.vstack([y, np.zeros((n - len(y), 2))])
        kind = "bass" if s["key"] == "bass" else ("linger" if s["key"] in ("other", "vocals") else "rhythm")
        if e["mode"] == "blend":
            g = {"bass": np.cos(np.pi / 2 * np.clip(b, 0, 1)), "rhythm": np.cos(np.pi / 2 * np.clip(b / 2, 0, 1))}.get(kind, np.where(b < 2, 1.0, np.cos(np.pi / 2 * np.clip((b - 2) / (e["W"] - 2), 0, 1))))
        else:
            g = np.cos(np.pi / 2 * np.clip(b, 0, 1)) if kind == "linger" else np.cos(np.pi / 2 * np.clip(b / 0.125, 0, 1))
        g = np.where(ts < T, 1.0, g) * s["gain"]
        ref += y * g[:, None]
    if e["mode"] == "blend":  # the high-pass the tail bus runs from T (20 Hz rising to 250 Hz over 4 bars) only touches the low end: compare above 6 kHz
        pass
    h = hf_ratio(capx[f0:f1], ref)
    print("ANALYSE Q7 %s: tail capture against smooth offline gains, %.1f s around T (rate step %.1f cents, recipe %s): high band per 2 ms, max %+.1f dB, p99.9 %+.1f dB, median %+.1f dB, %d of %d frames over +3 dB" % (
        name, (f1 - f0) / SR, e.get("cents", 0), e["mode"], h["max_db"], h["p999_db"], h["median_db"], h["frames_over_3db"], h["frames"]))
    print("ANALYSE    frames over +3 dB at (s from T):", [round(x + t0 - T, 3) for x in h["where_s"]][:40], "; loudest of them %.1f dB against the median high band before T" % h["excess_level_db_max"])
    return h


if os.environ.get("RW_STEP_CHECK"):
    q7 = {}
    for n in os.environ["RW_STEP_CHECK"].split(","):
        q7[n] = step_check(n)
    json.dump(q7, open(os.path.join(F, "analysis_q7.json"), "w"), indent=1)
