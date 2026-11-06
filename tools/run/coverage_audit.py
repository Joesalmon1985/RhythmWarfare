"""The touch-coverage audit's summariser (docs/parallel-development/coverage/baseline.md).

    godot --headless --path . -s tools/run/coverage_audit.gd -- --run=main --aspect=16:9 --pad=36 --out=C:/Users/joesa/rw-audio-work/coverage/main_169_36.jsonl
    python tools/run/coverage_audit.py f1.jsonl f2.jsonl ... [--detail=16:9/36] [--out=table.md]

Reads the "COV {...}" lines (or bare JSON lines) of coverage_audit.gd. Each line is one scene at one configuration (aspect, pad size); a later line for the same
(config, run, scene) replaces an earlier one. For every configuration it writes totals per run and overall; for the --detail configuration (default: the first) also one row per scene.

Per scene (a sample is one beat of active play; see the .gd header for the definition):
  touch mean / median      coverage of the world rectangle by the union of all touch regions, over all samples (nothing selectable = 0)
  >=50%                    share of samples with touch coverage of at least 50%
  sel                      share of samples with anything selectable (at least one hotspot on show)
  choice mean, >=25%       coverage by hotspots that lead somewhere; share of samples at 25% or more
  vis hs / vis all         union of the drawn objects of the hotspots on show / of all things and people of the picture
  min target               smallest touch target in px over all samples with something on show (the larger of ring diameter and rectangle short side)
  hs                       hotspots on show per sample, min-max (over all samples, 0 included)
  ratio, pad, noobj        hotspots whose touch region exceeds 1.5 x their visible object (area), touching a pad rectangle, and with no drawn object to compare to
PASS needs all of: >=50% touch in at least 80% of samples; >=25% choice coverage in at least 80% of samples; no touch region over 1.5 x its object (area); smallest target at least 88 px;
no overlap with a pad. A scene with no samples with a hotspot on show fails the targets by definition.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
from collections import defaultdict

RUN_ORDER = ["main", "gospel", "squadron", "ember"]
RUN_TITLE = {"main": "Main run", "gospel": "Gospel", "squadron": "Squadron", "ember": "Ember"}
T_TOUCH = 0.50
T_SHARE = 0.80
T_CHOICE = 0.25
T_RATIO = 1.5
T_PX = 88.0


def read(paths):
    data = {}
    order = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("COV "):
                    line = line[4:]
                if not line.startswith("{"):
                    continue
                d = json.loads(line)
                if "scene" not in d or "touch" not in d:
                    continue
                cfg = "%s/%d" % (d["aspect"], d["pad_pct"])
                if cfg not in order:
                    order.append(cfg)
                data[(cfg, d["run"], d["scene"])] = d
    return data, order


def med(xs):
    return statistics.median(xs) if xs else 0.0


def scene_stats(d):
    touch = [x / 1000.0 for x in d["touch"]]
    choice = [x / 1000.0 for x in d["choice"]]
    n = d["n"]
    tg = [x for x in d["tgt"] if x >= 0]
    hs = d["hs"]
    ratio_bad = sorted(i for i, h in hs.items() if h["ratio"] > T_RATIO)
    lin_bad = sorted(i for i, h in hs.items() if h["ratio_lin"] > T_RATIO)
    pad_bad = sorted(i for i, h in hs.items() if h["pad"] > 0)
    noobj = sorted(i for i, h in hs.items() if h["noobj"] > 0 and h["noobj"] == h["n"] - h["edge"] and h["n"] > h["edge"])
    s = {
        "N": len(touch),
        "touch": touch, "choice": choice, "n": n,
        "vis_hs": [x / 1000.0 for x in d["vis_hs"]], "vis_all": [x / 1000.0 for x in d["vis_all"]],
        "touch_mean": statistics.fmean(touch) if touch else 0.0,
        "touch_med": med(touch),
        "ge50": sum(1 for x in touch if x >= T_TOUCH) / len(touch) if touch else 0.0,
        "sel": sum(1 for x in n if x > 0) / len(n) if n else 0.0,
        "touch_med_sel": med([t for t, k in zip(touch, n) if k > 0]),
        "choice_mean": statistics.fmean(choice) if choice else 0.0,
        "choice_ge25": sum(1 for x in choice if x >= T_CHOICE) / len(choice) if choice else 0.0,
        "vis_hs_mean": statistics.fmean(x / 1000.0 for x in d["vis_hs"]) if d["vis_hs"] else 0.0,
        "vis_all_mean": statistics.fmean(x / 1000.0 for x in d["vis_all"]) if d["vis_all"] else 0.0,
        "min_px": min(tg) if tg else None,
        "n_min": min(n) if n else 0, "n_max": max(n) if n else 0,
        "ratio_bad": ratio_bad, "lin_bad": lin_bad, "pad_bad": pad_bad, "noobj": noobj,
        "hs": hs,
    }
    ok_touch = s["ge50"] >= T_SHARE
    ok_choice = s["choice_ge25"] >= T_SHARE
    ok_ratio = not ratio_bad
    ok_px = s["min_px"] is not None and s["min_px"] >= T_PX
    ok_pad = not pad_bad
    s["checks"] = {"touch": ok_touch, "choice": ok_choice, "ratio": ok_ratio, "px": ok_px, "pad": ok_pad}
    s["pass"] = all(s["checks"].values())
    return s


def pct(x):
    return "%.1f%%" % (100.0 * x)


def totals(rows):
    """Pooled over all samples of the scenes in `rows` (each a scene_stats dict) plus the scene counts."""
    touch = [x for r in rows for x in r["touch"]]
    choice = [x for r in rows for x in r["choice"]]
    n = [x for r in rows for x in r["n"]]
    visa = [x for r in rows for x in r["vis_all"]]
    vish = [x for r in rows for x in r["vis_hs"]]
    sel_touch = [t for t, k in zip(touch, n) if k > 0]
    px = [r["min_px"] for r in rows if r["min_px"] is not None]
    return {
        "scenes": len(rows), "samples": len(touch), "passing": sum(1 for r in rows if r["pass"]),
        "touch_mean": statistics.fmean(touch) if touch else 0.0, "touch_med": med(touch), "touch_med_sel": med(sel_touch),
        "sel": sum(1 for x in n if x > 0) / len(n) if n else 0.0,
        "ge50": sum(1 for x in touch if x >= T_TOUCH) / len(touch) if touch else 0.0,
        "choice_mean": statistics.fmean(choice) if choice else 0.0, "choice_ge25": sum(1 for x in choice if x >= T_CHOICE) / len(choice) if choice else 0.0,
        "vis_hs": statistics.fmean(vish) if vish else 0.0, "vis_all": statistics.fmean(visa) if visa else 0.0,
        "min_px": min(px) if px else None, "scene_ok": {k: sum(1 for r in rows if r["checks"][k]) for k in ("touch", "choice", "ratio", "px", "pad")},
        "scene_med_of_means": med([r["touch_mean"] for r in rows]), "scene_med_of_med_sel": med([r["touch_med_sel"] for r in rows]),
    }


def total_row(label, t):
    return "| %s | %d | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d / %d |" % (
        label, t["scenes"], t["samples"], pct(t["touch_mean"]), pct(t["touch_med"]), pct(t["touch_med_sel"]), pct(t["sel"]), pct(t["ge50"]),
        pct(t["choice_mean"]), pct(t["choice_ge25"]), pct(t["vis_hs"]), pct(t["vis_all"]),
        ("%d px" % t["min_px"]) if t["min_px"] is not None else "n/a", t["passing"], t["scenes"])


TOTAL_HEAD = ("| | scenes | samples | touch mean | touch median | median while selectable | any selectable | at least 50% | choice mean | choice at least 25% | visual (hotspot objects) | visual (all things and people) | smallest target | scenes passing |\n"
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
SCENE_HEAD = ("| run | scene | samples | touch mean | median | at least 50% | any selectable | choice mean | choice at least 25% | vis hs | vis all | min target | hs on show | ratio over 1.5 | pad overlap | no object | result |\n"
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")


def scene_row(run, scene, s):
    failed = [k for k, v in s["checks"].items() if not v]
    return "| %s | %s | %d | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d-%d | %d | %d | %d | %s |" % (
        run, scene, s["N"], pct(s["touch_mean"]), pct(s["touch_med"]), pct(s["ge50"]), pct(s["sel"]), pct(s["choice_mean"]), pct(s["choice_ge25"]), pct(s["vis_hs_mean"]), pct(s["vis_all_mean"]),
        ("%d px" % s["min_px"]) if s["min_px"] is not None else "n/a", s["n_min"], s["n_max"], len(s["ratio_bad"]), len(s["pad_bad"]), len(s["noobj"]),
        "PASS" if s["pass"] else "FAIL (" + ", ".join(failed) + ")")


def main(argv):
    paths = [a for a in argv if not a.startswith("--")]
    opts = dict(a[2:].split("=", 1) for a in argv if a.startswith("--") and "=" in a)
    if not paths:
        print(__doc__)
        return 2
    data, order = read(paths)
    detail = opts.get("detail", order[0] if order else "")
    detail = detail.replace("/", "/")
    out = []
    for cfg in order:
        rows_by_run = defaultdict(list)
        for (c, run, scene), d in data.items():
            if c == cfg:
                rows_by_run[run].append((scene, scene_stats(d)))
        out.append("### Configuration %s (aspect / pad size %%)\n" % cfg)
        out.append(TOTAL_HEAD)
        allrows = []
        for run in RUN_ORDER:
            if run in rows_by_run:
                rs = [s for _, s in rows_by_run[run]]
                allrows += rs
                out.append(total_row(RUN_TITLE[run], totals(rs)))
        if allrows:
            out.append(total_row("**All**", totals(allrows)))
            t = totals(allrows)
            out.append("")
            out.append("Scenes meeting each target: touch >=50%% in 80%% of samples %d of %d; choice >=25%% in 80%% of samples %d; no region over 1.5 x its object %d; smallest target >=88 px %d; no pad overlap %d. "
                       "Median over scenes of the scene's mean touch coverage: %s; of the scene's median while selectable: %s." % (
                           t["scene_ok"]["touch"], t["scenes"], t["scene_ok"]["choice"], t["scene_ok"]["ratio"], t["scene_ok"]["px"], t["scene_ok"]["pad"], pct(t["scene_med_of_means"]), pct(t["scene_med_of_med_sel"])))
        out.append("")
        if cfg == detail:
            out.append("#### Per scene, %s\n" % cfg)
            out.append(SCENE_HEAD)
            for run in RUN_ORDER:
                for scene, s in rows_by_run.get(run, []):
                    out.append(scene_row(run, scene, s))
            out.append("")
            # hotspots over the ratio, and what the hotspots are made of
            offenders = []
            kinds = defaultdict(lambda: [0, 0, 0])  # anchor -> [hotspots, with an object, over 1.5]
            for run in RUN_ORDER:
                for scene, s in rows_by_run.get(run, []):
                    for hid, h in s["hs"].items():
                        k = kinds[h["anchor"] + "/" + h["arch"]]
                        k[0] += 1
                        if h["noobj"] < h["n"] - h["edge"]:
                            k[1] += 1
                        if h["ratio"] > T_RATIO:
                            k[2] += 1
                            offenders.append((h["ratio"], run, scene, hid, h))
            out.append("#### Hotspots by anchor and archetype, %s\n" % cfg)
            out.append("| anchor / archetype | hotspots seen | with a drawn object to compare | touch area over 1.5 x object |\n|---|---|---|---|")
            for k in sorted(kinds):
                out.append("| %s | %d | %d | %d |" % (k, *kinds[k]))
            out.append("")
            offenders.sort(key=lambda x: -x[0])
            out.append("#### Largest touch-to-object ratios (area), %s (top 15)\n" % cfg)
            out.append("| ratio | run | scene | hotspot | anchor | touch px2 | object px2 | radius_m |\n|---|---|---|---|---|---|---|---|")
            for ratio, run, scene, hid, h in offenders[:15]:
                out.append("| %.1f | %s | %s | %s | %s/%s | %d | %d | %.2f |" % (ratio, run, scene, hid, h["anchor"], h["arch"], h["tarea"], h["varea"], h["radius_m"]))
            out.append("")
    text = "\n".join(out) + "\n"
    if "out" in opts:
        with open(opts["out"], "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
