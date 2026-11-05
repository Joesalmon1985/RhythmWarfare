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


def _thumbs(cues: list[dict]) -> dict:
    """Consecutive presses (by start time, within a stretch): other thumb / same thumb other pad / same pad."""
    alt = same_thumb = same_pad = 0
    for a, b in zip(cues, cues[1:]):
        if b.get("stretch") != a.get("stretch"):
            continue
        if a["pad"] == b["pad"]:
            same_pad += 1
        elif (a["pad"] - 1) // 2 == (b["pad"] - 1) // 2:
            same_thumb += 1
        else:
            alt += 1
    n = max(alt + same_thumb + same_pad, 1)
    return {"other_thumb": round(alt / n, 3), "same_thumb_other_pad": round(same_thumb / n, 3),
            "same_pad": round(same_pad / n, 3), "pairs": alt + same_thumb + same_pad}


def _dist_ms(ts: np.ndarray, o: np.ndarray) -> np.ndarray:
    if not len(ts) or not len(o):
        return np.array([])
    i = np.searchsorted(o, ts)
    return np.minimum(np.abs(ts - o[np.clip(i, 0, len(o) - 1)]), np.abs(ts - o[np.clip(i - 1, 0, len(o) - 1)])) * 1000


def drop_identity(tj: dict, rich: dict) -> dict | None:
    """The first two drops compared bar for bar: the share of one drop's cues that have a cue in the other at the
    same offset from the drop's start (within 15 ms) with the same pad and voice, per chart."""
    drops = [s for s in tj["sections"] if s["role"] == "drop"]
    if len(drops) < 2:
        return None
    a, b = drops[0], drops[1]
    span = min(a["end_s"] - a["start_s"], b["end_s"] - b["start_s"])
    off = b["start_s"] - a["start_s"]
    out = {"drops": [a["id"], b["id"]], "compared_s": round(span, 2),
           "focus_a": [(round(f["start_s"] - a["start_s"], 2), f["voice"]) for f in tj["focus"]
                       if a["start_s"] - 1e-3 <= f["start_s"] < a["start_s"] + span],
           "focus_b": [(round(f["start_s"] - b["start_s"], 2), f["voice"]) for f in tj["focus"]
                       if b["start_s"] - 1e-3 <= f["start_s"] < b["start_s"] + span]}
    for d, cues in tj["charts"].items():
        ca = [c for c in cues if a["start_s"] <= c["t"] < a["start_s"] + span]
        cb = [c for c in cues if b["start_s"] <= c["t"] < b["start_s"] + span]

        def match(x, others, sh):
            ts = np.array([o["t"] - sh for o in others])
            if not len(ts):
                return False
            j = int(np.argmin(np.abs(ts - x["t"])))
            o = others[j]
            return bool(abs(ts[j] - x["t"]) <= 0.015 and o["pad"] == x["pad"] and o["voice"] == x["voice"])
        ma = int(sum(match(x, cb, off) for x in ca))
        mb = int(sum(match(x, ca, -off) for x in cb))

        def voice_at(t):
            return next((f["voice"] for f in tj["focus"] if f["start_s"] <= t < f["end_s"]), None)
        sa = [x for x in ca if voice_at(x["t"] + off) == x["voice"]]
        sb = [x for x in cb if voice_at(x["t"] - off) == x["voice"]]
        out[d] = {"cues_a": len(ca), "cues_b": len(cb), "a_in_b": round(ma / max(len(ca), 1), 3),
                  "b_in_a": round(mb / max(len(cb), 1), 3),
                  "same_focus_cues_a": len(sa), "same_focus_a_in_b": round(int(sum(match(x, cb, off) for x in sa)) / max(len(sa), 1), 3),
                  "same_focus_cues_b": len(sb), "same_focus_b_in_a": round(int(sum(match(x, ca, -off) for x in sb)) / max(len(sb), 1), 3)}
    return out


def write(c, val_stats: dict, val_report) -> dict:
    from layout import rank_corr
    an = c.jload("analysis.json")
    vj = c.jload("voices.json")
    ch = c.jload("charts.json")
    fj = c.jload("focus.json")
    ej = c.jload("events.json")
    tj = json.loads((c.pack / "track.json").read_text())
    B = 60.0 / tj["tempo"]["bpm"]
    dur = tj["duration_s"]
    out: dict = {"id": c.id, "input": c.src.name, "timings_s": c.timings}
    g = an["grid"]
    out["tempo"] = {"bpm": round(g["bpm"], 4), "vs_174": an["vs_174"], "first_downbeat_s": round(an["first_downbeat_s"], 4),
                    "candidates": an["tempo_candidates"]["candidates"], "constant": an["constant_tempo"],
                    "residual_ms_median_abs": g["residual_ms_median_abs"], "residual_ms_rms": g["residual_ms_rms"],
                    "drift_ms_max_abs": g["drift_ms_max_abs"], "drift_ms_first_last": g["drift_ms_first_last"],
                    "bpm_halves": [g["bpm_first_half"], g["bpm_second_half"]],
                    "share_of_drum_onset_weight_on_grid": g["share_on_grid"],
                    "downbeat": an["downbeat"], "confidence": tj["tempo"]["confidence"]}
    out["sections"] = an["sections"]
    out["separation"] = {"model": c.model, **{k: v for k, v in an["stem_report"].items()}}
    from voices import describe_stem
    out["separation"]["words"] = {k: describe_stem(k, s, an["stem_report"]) for k, s in an["stem_report"]["stems"].items()}
    out["voices"] = vj
    out["focus"] = {"options": fj["options"], "timeline": fj["timeline"], "gaps": fj["gaps"], "stretches": []}
    ons = {v["key"]: independent_onsets(c.pack / v["stem"]) for v in tj["voices"]}
    events = ej["events"]
    lay = {x["stretch"]: x for x in ch["layouts"]}
    for si, f in enumerate(fj["focus"]):
        k = f["voice"]
        beats = (f["end_s"] - f["start_s"]) / B
        aud = [e for e in events[k] if e["aud"] and f["start_s"] <= e["t"] < f["end_s"] - 0.25 * B and e["t"] >= 1.0]
        ss = np.array([e["s"] for e in aud])
        thr = float(np.percentile(ss, 75)) if len(ss) else 0.0
        strong = {round(e["t"], 4) for e in aud if e["s"] >= thr}
        row = {"i": si, "voice": k, "start_s": f["start_s"], "end_s": f["end_s"], "bars": f["bars"],
               "sections": f["sections"], "share": f["share"], "runner_up": f["runner_up"],
               "runner_up_share": f["runner_up_share"], "why": f["why"], "layout": lay.get(si), "charts": {}}
        for d, cues in ch["charts"].items():
            cs = [x for x in cues if x["stretch"] == si]
            hs = [x["h"] for x in cs if x["h"] is not None]
            ps = [x["pad"] for x in cs if x["h"] is not None]
            dist = _dist_ms(np.array([x["t"] for x in cs]), ons[k])
            row["charts"][d] = {
                "cues": len(cs), "holds": sum(1 for x in cs if x["dur"] > 0), "per_beat": round(len(cs) / beats, 3),
                "per_s": round(len(cs) / (f["end_s"] - f["start_s"]), 3),
                "strong_cued": round(sum(1 for x in cs if x["ev_t"] in strong) / max(len(strong), 1), 3),
                "strong": len(strong),
                "pads": [sum(1 for x in cs if x["pad"] == p) for p in (1, 2, 3, 4)],
                "height_pad_rank_corr": None if (r := rank_corr(hs, ps)) is None else round(r, 3),
                "thumbs": _thumbs(cs),
                "attack_ms_p50_p95": _q(dist), "attack_within_20ms": round(float((dist <= 20).mean()), 3) if len(dist) else None,
            }
        out["focus"]["stretches"].append(row)
    diffs = {}
    for d, cues in tj["charts"].items():
        rich = ch["charts"][d]
        dd = {"count": len(cues), "per_s": round(len(cues) / dur, 3)}
        span = sum(f["end_s"] - f["start_s"] for f in tj["focus"])
        dd["per_beat_of_focus"] = round(len(cues) / (span / B), 3)
        dd["holds"] = sum(1 for x in cues if x["dur"] > 0)
        dd["thumbs"] = _thumbs(rich)
        per_voice = {}
        for v in tj["voices"]:
            k = v["key"]
            cs = [x for x in rich if x["voice"] == k]
            dist = _dist_ms(np.array([x["t"] for x in cs]), ons[k])
            per_voice[k] = {"cues": len(cs), "holds": sum(1 for x in cs if x["dur"] > 0),
                            "to_independent_onset_ms_p50_p95": _q(dist),
                            "share_within_20ms": round(float((dist <= 20).mean()), 3) if len(dist) else None,
                            "on_grid_share": round(float(np.mean([abs(x["dev_ms"]) <= 20 for x in cs])), 3) if cs else None,
                            "conf_p10_p50_p90": _q([x["conf"] for x in cs], (10, 50, 90)),
                            "kinds": {kk: sum(1 for x in cs if x["kind"] == kk) for kk in sorted({x["kind"] for x in cs})}}
        dd["voices"] = per_voice
        hs = [x["h"] for x in rich if x["h"] is not None]
        dd["two_pads_together"] = int(np.sum(np.diff([x["t"] for x in cues]) < 0.03)) if len(cues) > 1 else 0
        diffs[d] = dd
        _ = hs
    out["charts"] = diffs
    out["drop_identity"] = drop_identity(tj, ch)
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
    L.append(f"tempo {t['bpm']} BPM ({t['vs_174']['ratio']:.4f} x 174); first downbeat {t['first_downbeat_s']} s; "
             f"constant={t['constant']}; confidence {t['confidence']}")
    L.append(f"  grid residual median {t['residual_ms_median_abs']} ms, rms {t['residual_ms_rms']} ms; 8-bar window drift max "
             f"{t['drift_ms_max_abs']} ms; halves {t['bpm_halves']}")
    L.append("sections:")
    for s in r["sections"]:
        L.append(f"  {s['id']:<11} {s['role']:<9} {s['start_s']:8.2f} - {s['end_s']:8.2f}  {s['bars']:3d} bars  drive {s['intensity_db']} dB")
    sp = r["separation"]
    L.append(f"separation {sp['model']}: stems minus recording {sp['residual_db']} dB")
    for k, w in sp["words"].items():
        L.append(f"  {k}: {w}")
    fo = r["focus"]
    L.append(f"focus (options {fo['options']}):")
    L.append(f"  timeline in bars: {fo['timeline']}")
    for g in fo["gaps"]:
        L.append(f"  gap {g['start_s']:7.2f}-{g['end_s']:7.2f} ({g['bars']} bars, {', '.join(g['sections'])}): {g['why']}")
    for s in fo["stretches"]:
        lay = s["layout"] or {}
        L.append(f"  [{s['i']:2d}] {s['voice']:<7} {s['start_s']:7.2f}-{s['end_s']:7.2f} bars {s['bars']:3d} "
                 f"({', '.join(s['sections'])}): perceived share {s['share']:.0%}, runner-up {s['runner_up']} "
                 f"{(s['runner_up_share'] or 0):.0%}; why: {'; '.join(sorted(set(s['why'])))}")
        L.append(f"       sounds (height:presses->pad) " + " ".join(f"{x['height']}:{x['presses']}->{x['pad']}" for x in lay.get("sounds", []))
                 + f"; same-thumb cost {lay.get('same_thumb_cost')}, height inversions {lay.get('height_inversions')}"
                 + (f"; {lay['split']}" if lay.get("split") else ""))
        for d in ("easy", "normal", "hard"):
            x = s["charts"][d]
            th = x["thumbs"]
            L.append(f"       {d:<6} {x['cues']:4d} cues {x['per_beat']:.2f}/beat ({x['holds']} holds) pads {x['pads']} | "
                     f"strong cued {x['strong_cued']:.0%} of {x['strong']} | height~pad rho {x['height_pad_rank_corr']} | "
                     f"next press other thumb {th['other_thumb']:.0%}, same thumb {th['same_thumb_other_pad']:.0%}, same pad "
                     f"{th['same_pad']:.0%} | attack p50/p95 {x['attack_ms_p50_p95']} ms")
    for d, dd in r["charts"].items():
        L.append(f"chart {d}: {dd['count']} cues, {dd['per_s']}/s, {dd['per_beat_of_focus']}/beat of focus time, "
                 f"{dd['holds']} holds; two pads together {dd['two_pads_together']}; thumbs {dd['thumbs']}")
        for k, x in dd["voices"].items():
            L.append(f"  {k:<8} {x['cues']:4d} cues ({x['holds']} holds) | to independent onset p50/p95 "
                     f"{x['to_independent_onset_ms_p50_p95']} ms, <=20ms {x['share_within_20ms']} | on grid {x['on_grid_share']} "
                     f"| conf p10/50/90 {x['conf_p10_p50_p90']} | kinds {x['kinds']}")
    L.append(f"drops compared: {r['drop_identity']}")
    L.append(f"validation: {r['validation']}")
    L.append(f"timings (s): {r['timings_s']}")
    return "\n".join(L) + "\n"
