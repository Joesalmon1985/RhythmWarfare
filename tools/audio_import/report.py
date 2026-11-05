"""The evidence for a pack, written next to it as report.json and report.txt (numbers only; no audio).

Cue alignment is measured against onsets detected independently of the charting (librosa's default onset
detector with backtracking, run on the decoded Ogg stem of the voice as the game will play it), so a cue that sits
on a snapped grid line or on a legato note change shows its real distance from an audible attack.
"""
from __future__ import annotations

import json

import numpy as np

from audio_io import PACK_RATE, db, decode, frame_rms, mono


def _q(a, ps=(50, 95)):
    return [round(float(np.percentile(a, p)), 1) for p in ps] if len(a) else None


def independent_onsets(path, rate=PACK_RATE) -> np.ndarray:
    import librosa
    x, _ = decode(path, rate=rate)
    y = mono(x)
    on = librosa.onset.onset_detect(y=y, sr=rate, hop_length=256, units="time", backtrack=False)
    return np.asarray(on)


def write(c, val_stats: dict, val_report) -> dict:
    an = c.jload("analysis.json")
    vj = c.jload("voices.json")
    ch = c.jload("charts.json")
    tj = json.loads((c.pack / "track.json").read_text())
    B = 60.0 / tj["tempo"]["bpm"]
    dur = tj["duration_s"]
    pad_key = {v["pad"]: v["key"] for v in tj["voices"]}
    out: dict = {"id": c.id, "input": c.src.name, "timings_s": c.timings}
    g = an["grid"]
    out["tempo"] = {"bpm": round(g["bpm"], 4), "vs_174": an["vs_174"], "first_downbeat_s": round(an["first_downbeat_s"], 4),
                    "candidates": an["tempo_candidates"]["candidates"], "constant": an["constant_tempo"],
                    "residual_ms_median_abs": g["residual_ms_median_abs"], "residual_ms_rms": g["residual_ms_rms"],
                    "drift_ms_max_abs": g["drift_ms_max_abs"], "drift_ms_first_last": g["drift_ms_first_last"],
                    "bpm_halves": [g["bpm_first_half"], g["bpm_second_half"]],
                    "share_of_drum_onset_weight_on_grid": g["share_on_grid"],
                    "downbeat": an["downbeat"], "confidence": tj["tempo"]["confidence"]}
    if g["bpm_first_half"] and g["bpm_second_half"]:
        n_beats = dur / B
        out["tempo"]["far_end_ms_if_first_half_tempo"] = round(
            1000 * n_beats * abs(60 / g["bpm_first_half"] - 60 / g["bpm"]), 1)
    out["sections"] = an["sections"]
    out["separation"] = {"model": c.model, **{k: v for k, v in an["stem_report"].items()}}
    from voices import describe_stem
    out["separation"]["words"] = {k: describe_stem(k, s, an["stem_report"]) for k, s in an["stem_report"]["stems"].items()}
    out["voices"] = vj
    # independent onsets per voice from the encoded stems
    ons = {v["key"]: independent_onsets(c.pack / v["stem"]) for v in tj["voices"]}
    evs = ch["events"]
    diffs = {}
    for d, cues in tj["charts"].items():
        rich = ch["charts"][d]
        dd = {"count": len(cues), "per_s": round(len(cues) / dur, 3), "per_beat": round(len(cues) / (dur / B), 3)}
        per_voice = {}
        for p in (1, 2, 3, 4):
            k = pad_key[p]
            cs = [x for x in cues if x["pad"] == p]
            ts = np.array([x["t"] for x in cs])
            o = ons[k]
            if len(ts) and len(o):
                i = np.searchsorted(o, ts)
                dist = np.minimum(np.abs(ts - o[np.clip(i, 0, len(o) - 1)]), np.abs(ts - o[np.clip(i - 1, 0, len(o) - 1)])) * 1000
            else:
                dist = np.array([])
            aud = [e for e in evs[k] if e["aud"]]
            ss = np.array([e["s"] for e in aud])
            thr = np.percentile(ss, 75) if len(ss) else 0
            strong = [e["t"] for e in aud if e["s"] >= thr]
            chosen = {x["ev_t"] for x in rich if x["voice"] == k}
            per_voice[k] = {
                "pad": p, "cues": len(cs), "holds": sum(1 for x in cs if x["dur"] > 0),
                "per_min": round(len(cs) / dur * 60, 1), "per_beat": round(len(cs) / (dur / B), 3),
                "to_independent_onset_ms_p50_p95": _q(dist),
                "share_within_20ms": round(float((dist <= 20).mean()), 3) if len(dist) else None,
                "strong_onsets_cued": round(sum(1 for t in strong if round(t, 4) in chosen) / max(len(strong), 1), 3),
                "conf_p10_p50_p90": _q([x["conf"] for x in cs], (10, 50, 90)),
                "kinds": {kk: sum(1 for x in rich if x["voice"] == k and x["kind"] == kk) for kk in {x["kind"] for x in rich}},
                "on_grid_share": round(float(np.mean([abs(x["dev_ms"]) <= 20 for x in rich if x["voice"] == k])), 3) if cs else None,
            }
        dd["voices"] = per_voice
        # sections
        rows = []
        for s in tj["sections"]:
            beats = (s["end_s"] - s["start_s"]) / B
            row = {"id": s["id"], "role": s["role"], "start_s": s["start_s"], "end_s": s["end_s"]}
            inside = [x for x in cues if s["start_s"] <= x["t"] < s["end_s"]]
            row["per_beat"] = round(len(inside) / beats, 3)
            for p in (1, 2, 3, 4):
                row[pad_key[p]] = round(sum(1 for x in inside if x["pad"] == p) / beats, 3)
            rows.append(row)
        dd["sections"] = rows
        ts = np.array([x["t"] for x in cues])
        pairs = {}
        for i in range(len(cues) - 1):
            j = i + 1
            while j < len(cues) and cues[j]["t"] - cues[i]["t"] < 0.03:
                a, b = sorted((pad_key[cues[i]["pad"]], pad_key[cues[j]["pad"]]))
                pairs[f"{a}+{b}"] = pairs.get(f"{a}+{b}", 0) + 1
                j += 1
        dd["two_pads_together"] = {"count": sum(pairs.values()), "pairs": pairs,
                                   "share_of_cues": round(2 * sum(pairs.values()) / max(len(cues), 1), 3)}
        held = 0
        for x in cues:
            if x["dur"] > 0:
                held += sum(1 for y in cues if y["pad"] != x["pad"] and x["t"] < y["t"] < x["t"] + x["dur"])
        dd["cues_during_another_pads_hold"] = held
        confs = np.array([x["conf"] for x in cues])
        dd["conf_hist"] = {f"{lo:.1f}-{lo + 0.1:.1f}": int(((confs >= lo) & (confs < lo + 0.1 + (1e-9 if lo > 0.85 else 0))).sum())
                           for lo in np.arange(0, 1.0, 0.1)}
        diffs[d] = dd
    out["charts"] = diffs
    # cue rate against section energy
    lv = an["bar_levels"]
    edges = np.array(an["bar_edges"])
    mixdb = []
    for s in an["sections"]:
        a, b = s["bar_start"] if "bar_start" in s else None, None
        m = (edges[:-1] >= s["start_s"] - 1e-6) & (edges[:-1] < s["end_s"] - 1e-6)
        mixdb.append(float(np.mean([np.mean(np.array(v)[m]) for v in lv.values()])))
    rates = [r["per_beat"] for r in diffs["normal"]["sections"]]
    out["rate_vs_energy"] = {"section_mean_stem_db": [round(x, 1) for x in mixdb], "normal_per_beat": rates,
                             "pearson": round(float(np.corrcoef(mixdb, rates)[0, 1]), 3) if len(rates) > 2 else None}
    out["validation"] = {"violations": len(val_report.errors), "first": val_report.errors[:10],
                         **{k: v for k, v in val_stats.items() if k != "lengths"}}
    (c.pack / "report.json").write_text(json.dumps(out, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    (c.pack / "report.txt").write_text(text(out))
    print(text(out))
    return out


def text(r: dict) -> str:
    L = []
    t = r["tempo"]
    L.append(f"== {r['id']}  ({r['input']})")
    L.append(f"tempo {t['bpm']} BPM ({t['vs_174']['ratio']:.4f} x 174, {t['vs_174']['ratio_87']:.4f} x 87); first downbeat "
             f"{t['first_downbeat_s']} s; constant={t['constant']}; confidence {t['confidence']}")
    L.append(f"  grid residual median {t['residual_ms_median_abs']} ms, rms {t['residual_ms_rms']} ms; 8-bar window drift max "
             f"{t['drift_ms_max_abs']} ms (first/last {t['drift_ms_first_last']}); halves {t['bpm_halves']}; "
             f"far-end error if the first half's tempo were used: {t.get('far_end_ms_if_first_half_tempo')} ms")
    L.append(f"  candidates {t['candidates']}; downbeat phase scores {t['downbeat']['scores']} conf {t['downbeat']['confidence']}")
    L.append("sections:")
    for s in r["sections"]:
        L.append(f"  {s['id']:<11} {s['role']:<9} {s['start_s']:8.2f} - {s['end_s']:8.2f}  {s['bars']:3d} bars  drive {s['intensity_db']} dB")
    sp = r["separation"]
    L.append(f"separation {sp['model']}: stems minus recording {sp['residual_db']} dB")
    for k, w in sp["words"].items():
        L.append(f"  {k}: {w}")
    L.append(f"  envelope corr {sp['env_corr']}")
    L.append(f"  drum-attack coincidence (x chance) {sp.get('transient_bleed')}")
    L.append("  share of the recording's energy by section: " + "; ".join(
        f"{sid} " + " ".join(f"{k} {100 * v:.0f}%" for k, v in d.items()) for sid, d in sp.get("by_section", {}).items()))
    v = r["voices"]
    L.append("voices: " + ", ".join(f"pad {x['pad']} {k} ({x['op']} of {'+'.join(x['from'])}, sep q {x['sep_quality']})"
                                     for k, x in sorted(v["voices"].items(), key=lambda kv: kv[1]["pad"])))
    L.append(f"  backing from {v['backing_from']}; thumbs L {v['pads']['left_thumb']} R {v['pads']['right_thumb']}; "
             f"pair overlap {v['pads']['pair_overlap']}")
    for n in v["notes"]:
        L.append(f"  - {n}")
    for d, dd in r["charts"].items():
        L.append(f"chart {d}: {dd['count']} cues, {dd['per_s']}/s, {dd['per_beat']}/beat; two pads together "
                 f"{dd['two_pads_together']}; cues during another pad's hold {dd['cues_during_another_pads_hold']}")
        for k, x in dd["voices"].items():
            L.append(f"  pad {x['pad']} {k:<8} {x['cues']:4d} cues ({x['holds']} holds) {x['per_min']:5.1f}/min "
                     f"{x['per_beat']:.3f}/beat | to independent onset p50/p95 {x['to_independent_onset_ms_p50_p95']} ms, "
                     f"<=20ms {x['share_within_20ms']} | strong onsets cued {x['strong_onsets_cued']} | conf p10/50/90 "
                     f"{x['conf_p10_p50_p90']} | kinds {x['kinds']} | on grid {x['on_grid_share']}")
        L.append("  per section (cues/beat: all, " + ", ".join(dd["voices"]) + "):")
        for s in dd["sections"]:
            L.append(f"    {s['id']:<11} {s['per_beat']:.3f}  " + "  ".join(f"{s[k]:.3f}" for k in dd["voices"]))
        L.append(f"  conf histogram {dd['conf_hist']}")
    L.append(f"cue rate vs section energy (normal): {r['rate_vs_energy']}")
    L.append(f"validation: {r['validation']}")
    L.append(f"timings (s): {r['timings_s']}")
    return "\n".join(L) + "\n"
