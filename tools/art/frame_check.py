#!/usr/bin/env python3
"""Value range and palette drift of the captured picture, per world, against the references (docs/art/STYLE_GUIDE.md, sections 1 and 2).

    python tools/art/frame_check.py <raw_dir> [--refs pixelexample]

Reads the frames of tools/art/audit_capture.sh (<scene>__<tag>.jpg), keeps only the picture (the top 62 % of the frame: the pad strip and the
HUD bars are cut, and the top 12 % too, where the HUD bars sit), and prints per world: the luminance at the 5th, 50th and 95th percentile,
the mean saturation, the share of near-black pixels (luminance under 0.04, "crushed") and of near-white ones (over 0.85, "blown"), and the
mean hue of the lit pixels. The same numbers for the three references come first. A world is flagged:
  DARK     median luminance under 0.08         BLOWN    more than 4 % of the picture over 0.85
  FLAT     p95 - p5 under 0.25 (no range)      CRUSH    more than 35 % under 0.04
  GARISH   mean saturation over 0.62
The thresholds are derived from the references (median 0.14 to 0.21, p95 0.41 to 0.68, saturation 0.35 to 0.5).
"""
import colorsys
import glob
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def measure(paths, crop=True):
    px = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        if crop:
            w, h = im.size
            im = im.crop((0, int(h * 0.12), w, int(h * 0.62)))
        im = im.resize((im.width // 4, im.height // 4), Image.BOX)
        px.append(np.asarray(im).reshape(-1, 3).astype(np.float32) / 255.0)
    a = np.concatenate(px)
    lum = 0.2126 * a[:, 0] + 0.7152 * a[:, 1] + 0.0722 * a[:, 2]
    mx, mn = a.max(1), a.min(1)
    sat = (mx - mn) / np.maximum(mx, 1e-3)
    lit = a[lum > 0.15]
    hue = ""
    if len(lit):
        m = lit.mean(0)
        hh, _, _ = colorsys.rgb_to_hsv(*m)
        hue = "#%02x%02x%02x h%03d" % (int(m[0] * 255), int(m[1] * 255), int(m[2] * 255), int(hh * 360))
    p5, p50, p95 = np.percentile(lum, [5, 50, 95])
    r = {"p5": p5, "p50": p50, "p95": p95, "sat": float(sat.mean()), "crush": float((lum < 0.04).mean()), "blown": float((lum > 0.85).mean()), "hue": hue}
    fl = []
    if p50 < 0.08:
        fl.append("DARK")
    if p95 - p5 < 0.25:
        fl.append("FLAT")
    if r["blown"] > 0.04:
        fl.append("BLOWN")
    if r["crush"] > 0.35:
        fl.append("CRUSH")
    if r["sat"] > 0.62:
        fl.append("GARISH")
    r["flags"] = ",".join(fl)
    return r


def worlds():
    out = []
    r = json.load(open(os.path.join(ROOT, "content/run/run.json"), encoding="utf-8"))
    for n in r["nodes"]:
        out.append(("", n["world"], n["id"]))
    for p in ("gospel", "squadron", "ember"):
        r = json.load(open(os.path.join(ROOT, "content/paths", p, "run.json"), encoding="utf-8"))
        for n in r["nodes"]:
            out.append((p + "__", p + "_" + n["world"], n["id"]))
    return out


def row(name, r):
    return "%-22s %5.2f %5.2f %5.2f  %4.2f  %5.1f%% %5.1f%%  %-16s %s" % (name, r["p5"], r["p50"], r["p95"], r["sat"], 100 * r["crush"], 100 * r["blown"], r["hue"], r["flags"])


def main():
    raw = sys.argv[1]
    refs = os.path.join(ROOT, "pixelexample")
    print("%-22s %5s %5s %5s  %4s  %6s %6s  %-16s %s" % ("picture", "p5", "p50", "p95", "sat", "crush", "blown", "lit mean", "flags"))
    for f in ("Rave", "Hospital", "InsaneAsylum"):
        print(row("ref " + f, measure([os.path.join(refs, f + ".png")], crop=False)))
    by = {}
    for pre, w, sid in worlds():
        by.setdefault(w, []).extend(glob.glob(os.path.join(raw, "%s%s__[am]*.jpg" % (pre, sid.replace(".", "_")))))
    for w, paths in by.items():
        if paths:
            print(row(w, measure(paths)))


if __name__ == "__main__":
    main()
