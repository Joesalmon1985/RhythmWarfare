"""The measured figures of one scene change played by tools/music/transition_pair.gd with RW_PAIR_CAPTURE=<folder> (muted, captured buses), numerically from the audio itself.

   python analyse_transition_pair.py <folder> [<folder> ...]      (numpy, scipy, soundfile; the packs named in pair.json must be on this PC)

Song time of a capture frame f of bus X: p(f) = clock + (f - pushed_X) / 48000, from the frame row (clock position and every capture's frame count, read together under AudioServer.lock)
nearest before f. What a group SHOULD hold at p: the incoming entry_t + (p - T); the tail out_t(T) + rate (p - T) after T (rate 1 before). What it HOLDS: 0.5 s windows of its slot bus
(band 1 to 8 kHz) cross-correlated against its stems mixed (at the logged tail gains, resampled at the rate) over +-60 ms. late_ms > 0: the audio is later than the cues (the output latency is
not in it: it delays every sound alike). Figures:
  incoming   cue time against audio time of the incoming group, from T on
  tail       the same for the tail (while it is loud enough), and tail minus incoming in the same windows (the flam, if any)
  silence    the tail bus after the floor (peak), and the last moment it is above -60 dBFS against the incoming drop (in incoming bars)
  limiter    RunTrack before and after its limiter in the first 4 incoming bars (peak in, reduction max and p95), and over 4 bars of the outgoing alone before T
"""
import json, os, re, sys
import numpy as np, soundfile as sf
from scipy import signal

SR = 48000
SOS = signal.butter(4, [1000, 8000], btype="bandpass", fs=SR, output="sos")
SLOTS = ["RunTrackA", "RunTrackB"]


class Pair:
    def __init__(self, F):
        self.F = F
        self.j = json.loads(re.sub(r"nan", "NaN", open(os.path.join(F, "pair.json")).read()))  # (Godot writes a NaN as nan)
        self.labels = self.j["labels"]
        self.rows = np.array(self.j["rows"], float)
        self.cap = {l: np.fromfile(os.path.join(F, l + ".f32"), dtype=np.float32).reshape(-1, 2) for l in self.labels}
        lk = self.j["lock"][0]
        self.T = float(lk["boundary"])
        self.plan = lk["plan"]
        self.recipe = lk["recipe"]
        log = self.j["track_log"]
        sa = [x for x in log if x["kind"] == "start" and x["track"] == self.j["a"]["track"]][0]
        self.out_t_T = float(sa["track_t"]) + (self.T - float(sa["t"]))
        self.in_start = [x for x in log if x["kind"] == "start" and x["track"] == self.j["b"]["track"]][0]
        tails = [x for x in log if x["kind"] == "tail"]
        self.tail = tails[0] if tails else None
        self.a_slot = SLOTS[int(self.tail["slot"])] if self.tail else SLOTS[int(sa.get("slot", 0))]
        self.b_slot = SLOTS[int(self.in_start.get("slot", 1))]
        self.rate = float(self.recipe.get("rate", 1.0))
        self.bar_in = 240.0 / float(self.plan["incoming_bpm"])
        self.tg = self.j["tails"]

    def col(self, label):
        return self.rows[:, 1 + self.labels.index(label)]

    def f_of(self, label, p):
        cp = self.rows[:, 0]
        i = max(np.searchsorted(cp, p, side="right") - 1, 0)
        return int(round(self.col(label)[i] + (p - cp[i]) * SR))

    def p_of(self, label, f):
        c = self.col(label)
        i = max(np.searchsorted(c, f, side="right") - 1, 0)
        return self.rows[i, 0] + (f - c[i]) / SR


def read_stems(side, t0, t1):
    res = {}
    for s in side["stems"]:
        a0, a1 = int(round(t0 * SR)), int(round(t1 * SR))
        x, _ = sf.read(os.path.join(side["dir"], s["stem"]), start=max(a0, 0), stop=max(a1, 1), dtype="float32", always_2d=True)
        if a0 < 0:
            x = np.vstack([np.zeros((-a0, 2), np.float32), x])
        res[s["key"]] = x
    return res


def resample_at(x, r, n):
    k = np.arange(n) * r
    i = np.floor(k).astype(int)
    fr = (k - i)[:, None]
    i = np.clip(i, 0, len(x) - 2)
    return x[i] * (1 - fr) + x[i + 1] * fr


def band(x):
    return signal.sosfiltfilt(SOS, x.sum(axis=1) if x.ndim == 2 else x)


def lag_of(capw, ref, m):
    c = signal.correlate(ref, capw, mode="valid", method="fft")
    j = int(np.argmax(c))
    d = 0.0
    if 0 < j < len(c) - 1:
        y0, y1, y2 = c[j - 1], c[j], c[j + 1]
        den = y0 - 2 * y1 + y2
        d = 0.5 * (y0 - y2) / den if den != 0 else 0.0
    seg = ref[j:j + len(capw)]
    return (j + d) - m, float(c[j] / (np.linalg.norm(seg) * np.linalg.norm(capw) + 1e-12))


def gains_at(pr, p):
    if not pr.tg:
        return None
    ts = [x[0] for x in pr.tg]
    i = max(np.searchsorted(ts, p, side="right") - 1, 0)
    return pr.tg[i][1]


def lags(pr, which, t_from, t_to, step=0.5, win=0.5, ms=0.06):
    label = pr.a_slot if which == "a" else pr.b_slot
    capx = pr.cap[label]
    side = pr.j["a"] if which == "a" else pr.j["b"]
    n, m = int(win * SR), int(ms * SR)
    out = []
    t = t_from
    while t + win <= t_to:
        f0 = pr.f_of(label, t)
        if f0 < 0 or f0 + n > len(capx):
            t += step
            continue
        p0 = pr.p_of(label, f0)
        if which == "a":
            rr = pr.rate if p0 >= pr.T else 1.0
            tau0 = pr.out_t_T + (p0 - pr.T) * rr
            gl = gains_at(pr, p0) if p0 >= pr.T else None
        else:
            rr = 1.0
            tau0 = float(pr.in_start["track_t"]) + (p0 - pr.T)
            gl = None
        src0 = tau0 - ms * rr
        st = read_stems(side, src0, src0 + (win + 2 * ms) * rr + 0.01)
        mix = None
        for s in side["stems"]:
            g = float(s["gain"]) * (float(gl.get(s["key"], 1.0)) if gl else 1.0)
            x = st[s["key"]] * g
            mix = x if mix is None else mix + x
        ref = band(resample_at(mix, rr, n + 2 * m))
        capw = band(capx[f0:f0 + n])
        if np.std(capw) < 1e-5 or np.std(ref) < 1e-6:
            t += step
            continue
        lag, pk = lag_of(capw, ref, m)
        out.append((round(p0, 3), -lag / SR * 1000.0, pk))
        t += step
    return out


def summ(rows, label):
    good = [r for r in rows if r[2] > 0.5]
    if len(good) < 1:
        print("PAIRFIG %s: no window correlates (%d tried)" % (label, len(rows)))
        return None
    a = np.array([r[1] for r in good])
    print("PAIRFIG %s: %d windows: audio late against the cues mean %.3f ms, min %.3f, max %.3f" % (label, len(good), a.mean(), a.min(), a.max()))
    return {"n": len(good), "mean": float(a.mean()), "min": float(a.min()), "max": float(a.max())}


def pk_db(x, w):
    n = len(x) // w
    return 20 * np.log10(np.abs(x[:n * w]).reshape(n, w, 2).max(axis=(1, 2)) + 1e-9)


def analyse(F):
    pr = Pair(F)
    res = {"driver": pr.j["driver"], "mode": str(pr.plan["mode"]), "rate": pr.rate, "cents": float(pr.recipe.get("cents", 0.0)), "T": pr.T, "complete_t": float(pr.plan["complete_t"]),
           "tail_gain_db": float(pr.recipe.get("tail_gain_db", 0.0))}
    print("PAIRFIG ---- %s: %s -> %s, %s, rate %.6f (%+.1f cents), driver %s, tail %.1f dB" % (os.path.basename(F), pr.j["a"]["track"], pr.j["b"]["track"], res["mode"], pr.rate, res["cents"], res["driver"], res["tail_gain_db"]))
    after = float(pr.rows[-1, 0])
    rb = lags(pr, "b", pr.T + 0.05, min(after - 0.6, pr.T + 30.0))
    res["incoming"] = summ(rb, "incoming group from T (cue time against its audio)")
    ra_pre = lags(pr, "a", max(0.5, pr.T - 8.0), pr.T - 0.55)
    res["outgoing_before_T"] = summ(ra_pre, "outgoing group before T")
    if pr.tail:
        ra = lags(pr, "a", pr.T + 0.05, float(pr.plan["complete_t"]) - 0.6, step=0.25)
        res["tail"] = summ(ra, "tail after T (at its rate)")
        rb2 = {r[0]: r for r in lags(pr, "b", pr.T + 0.05, float(pr.plan["complete_t"]) - 0.6, step=0.25)}
        dd = [(r[0], r[1] - rb2[r[0]][1]) for r in ra if r[2] > 0.5 and r[0] in rb2 and rb2[r[0]][2] > 0.5]
        if dd:
            arr = np.array([x[1] for x in dd])
            res["tail_minus_incoming_ms"] = {"mean": float(arr.mean()), "max_abs": float(np.abs(arr).max()), "n": len(arr), "first_2_bars": [x for x in dd if x[0] < pr.T + 2 * pr.bar_in]}
            print("PAIRFIG tail beat minus incoming beat: mean %.3f ms, max |.| %.3f ms over %d windows (%d in the first 2 bars)" % (arr.mean(), np.abs(arr).max(), len(arr), len(res["tail_minus_incoming_ms"]["first_2_bars"])))
        tailcap = pr.cap[pr.a_slot]
        ff = pr.f_of(pr.a_slot, float(pr.plan["complete_t"]) + 0.03)
        part = tailcap[ff:]
        res["after_floor_peak_dbfs"] = float(20 * np.log10(np.abs(part).max() + 1e-12)) if len(part) else None
        fT = pr.f_of(pr.a_slot, pr.T)
        x = np.abs(tailcap[fT:]).max(axis=1)
        loud = np.nonzero(x > 10 ** (-60 / 20))[0]
        last_p = pr.p_of(pr.a_slot, fT + int(loud[-1])) if len(loud) else pr.T
        drop_t = float(pr.recipe.get("drop_t", pr.T))
        res["tail_last_above_60db_t"] = last_p
        res["silent_bars_before_drop"] = (drop_t - last_p) / pr.bar_in
        print("PAIRFIG silence: tail bus after the floor peak %s dBFS; last above -60 dBFS at t=%.3f, %.2f incoming bars before the drop (t=%.3f; the rule: 4)" % (
            "%.1f" % res["after_floor_peak_dbfs"] if res["after_floor_peak_dbfs"] is not None else "-", last_p, res["silent_bars_before_drop"], drop_t))
    pre, post = pr.cap["RunTrackPre"], pr.cap["RunTrackPost"]
    w = int(0.01 * SR)
    f0, f1 = pr.f_of("RunTrackPre", pr.T), pr.f_of("RunTrackPre", pr.T + 4 * pr.bar_in)
    g0, g1 = pr.f_of("RunTrackPost", pr.T), pr.f_of("RunTrackPost", pr.T + 4 * pr.bar_in)
    a, b = pk_db(pre[f0:f1], w), pk_db(post[g0:g1], w)
    n = min(len(a), len(b))
    red = a[:n] - b[:n]
    bar_out = 240.0 / float(pr.plan["outgoing_bpm"])
    h0, h1 = pr.f_of("RunTrackPre", pr.T - 4 * bar_out), f0
    k0, k1 = pr.f_of("RunTrackPost", pr.T - 4 * bar_out), g0
    a2, b2 = pk_db(pre[h0:h1], w), pk_db(post[k0:k1], w)
    n2 = min(len(a2), len(b2))
    red2 = a2[:n2] - b2[:n2]
    res["limiter"] = {"peak_in_dbfs": float(a.max()), "reduction_max_db": float(red.max()), "reduction_p95_db": float(np.percentile(red, 95)), "pct_windows_over_1db": float((red > 1).mean() * 100),
                      "before_T_peak_in_dbfs": float(a2.max()), "before_T_reduction_max_db": float(red2.max()), "before_T_reduction_p95_db": float(np.percentile(red2, 95))}
    L = res["limiter"]
    print("PAIRFIG limiter, first 4 incoming bars: peak in %+.2f dBFS, reduction max %.2f dB, p95 %.2f dB, %.1f%% of 10 ms windows over 1 dB; the 4 outgoing bars before T: peak in %+.2f, reduction max %.2f, p95 %.2f" % (
        L["peak_in_dbfs"], L["reduction_max_db"], L["reduction_p95_db"], L["pct_windows_over_1db"], L["before_T_peak_in_dbfs"], L["before_T_reduction_max_db"], L["before_T_reduction_p95_db"]))
    json.dump(res, open(os.path.join(F, "analysis.json"), "w"), indent=1, default=float)
    return res


for F in sys.argv[1:]:
    analyse(F)
