#!/usr/bin/env python3
"""Before / after contact sheets from two folders of tools/art/audit_capture.sh frames (the same scenes, the same moments).

    python tools/art/compare_sheet.py <before_dir> <after_dir> <out_dir> [--tags a24,mid] [--name compare]

One row per scene found in both folders, in the order of the runs (content/run/run.json, then the paths): for each tag, the before frame then the after frame.
Writes <out_dir>/<name>_<group>.jpg per group (main, gospel, squadron, ember). Thumbnails 400 x 225 (box filter), labelled.
"""
import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TW, TH = 400, 225
PAD = 6
LAB = 18


def scenes():
    out = []
    r = json.load(open(os.path.join(ROOT, "content/run/run.json"), encoding="utf-8"))
    for n in r["nodes"]:
        out.append(("main", n["id"].replace(".", "_")))
    for p in ("gospel", "squadron", "ember"):
        r = json.load(open(os.path.join(ROOT, "content/paths", p, "run.json"), encoding="utf-8"))
        for n in r["nodes"]:
            out.append((p, p + "__" + n["id"].replace(".", "_")))
    return out


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    before, after, out = a[0], a[1], a[2]
    tags = ["a24", "mid"]
    name = "compare"
    for i, x in enumerate(sys.argv):
        if x == "--tags":
            tags = sys.argv[i + 1].split(",")
        if x == "--name":
            name = sys.argv[i + 1]
    tags = [t for t in tags if t]
    os.makedirs(out, exist_ok=True)
    groups = {}
    for g, sid in scenes():
        if all(os.path.exists(os.path.join(d, "%s__%s.jpg" % (sid, t))) for d in (before, after) for t in tags):
            groups.setdefault(g, []).append(sid)
    for g, ids in groups.items():
        cols = 2 * len(tags)
        sheet = Image.new("RGB", (cols * (TW + PAD) + PAD, len(ids) * (TH + LAB + PAD) + PAD), (40, 40, 46))
        d = ImageDraw.Draw(sheet)
        for r, sid in enumerate(ids):
            for k, t in enumerate(tags):
                for j, (lab, src) in enumerate((("before", before), ("after", after))):
                    im = Image.open(os.path.join(src, "%s__%s.jpg" % (sid, t))).convert("RGB").resize((TW, TH), Image.BOX)
                    x = PAD + (2 * k + j) * (TW + PAD)
                    y = PAD + r * (TH + LAB + PAD)
                    d.text((x, y + 2), "%s %s  %s" % (sid, t, lab), fill=(255, 220, 140) if j else (220, 220, 220))
                    sheet.paste(im, (x, y + LAB))
        p = os.path.join(out, "%s_%s.jpg" % (name, g))
        sheet.save(p, quality=82, optimize=True)
        print("sheet", p, len(ids), "scenes")


if __name__ == "__main__":
    main()
