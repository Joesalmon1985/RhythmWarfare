#!/usr/bin/env python3
"""Contact sheets of the art audit from the raw frames of tools/art/audit_capture.sh.

    python tools/art/audit_sheets.py <raw_dir> <out_dir> [<extra_dir>]

Writes (JPEG, quality 82):
  world_<world>.jpg     one row per scene of the world: a24 | mid | win (the scene a few seconds in, later, the hotspot window)
  joins_<group>.jpg     one row per scene: end | nx0 | nx3 (the last moment of a scene, the first moments of the next: the joins)
  ui.jpg, entrances.jpg, passage.jpg, bassment.jpg, wide_20x9.jpg   from the frames of tools/art/audit_extra.sh (<extra_dir>)
Thumbnails are 400 x 225 (a 1280 x 720 frame scaled by 5/16, box filter), labelled with the frame name.
Worlds are read from content/run/run.json and content/paths/<id>/run.json.
"""
import json
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TW, TH = 400, 225
PAD = 6
LAB = 18


def worlds():
    out = []  # (prefix, world, [scene ids])
    r = json.load(open(os.path.join(ROOT, "content/run/run.json"), encoding="utf-8"))
    order = []
    by = {}
    for n in r["nodes"]:
        w = n["world"]
        if w not in by:
            by[w] = []
            order.append(w)
        by[w].append(n["id"])
    for w in order:
        out.append(("", w, by[w]))
    for p in ("gospel", "squadron", "ember"):
        r = json.load(open(os.path.join(ROOT, "content/paths", p, "run.json"), encoding="utf-8"))
        order, by = [], {}
        for n in r["nodes"]:
            w = n["world"]
            if w not in by:
                by[w] = []
                order.append(w)
            by[w].append(n["id"])
        for w in order:
            out.append((p + "__", p + "_" + w, by[w]))
    return out


def grid(src, names, path, title, cols=3):
    """A plain grid of named frames (no tags), cols per row."""
    rows = [names[i:i + cols] for i in range(0, len(names), cols)]
    W = PAD + cols * (TW + PAD)
    H = 28 + len(rows) * (TH + LAB + PAD) + PAD
    img = Image.new("RGB", (W, H), (18, 16, 24))
    d = ImageDraw.Draw(img)
    d.text((PAD, 6), title, fill=(235, 235, 245))
    y = 28
    for r in rows:
        for c, name in enumerate(r):
            x = PAD + c * (TW + PAD)
            f = os.path.join(src, name + ".jpg")
            d.text((x, y + 2), name, fill=(200, 200, 215))
            if os.path.exists(f):
                im = Image.open(f).convert("RGB")
                th = int(TW * im.height / im.width)
                img.paste(im.resize((TW, th), Image.BOX).crop((0, 0, TW, min(TH, th))), (x, y + LAB))
            else:
                d.text((x + 10, y + LAB + 10), "missing", fill=(220, 90, 90))
        y += TH + LAB + PAD
    img.save(path, quality=82, optimize=True, progressive=True)
    print("sheet", path)


def sheet(raw, rows, tags, path, title):
    cols = len(tags)
    W = PAD + cols * (TW + PAD)
    H = 28 + len(rows) * (TH + LAB + PAD) + PAD
    img = Image.new("RGB", (W, H), (18, 16, 24))
    d = ImageDraw.Draw(img)
    d.text((PAD, 6), title, fill=(235, 235, 245))
    y = 28
    n = 0
    for name in rows:
        for c, tag in enumerate(tags):
            x = PAD + c * (TW + PAD)
            f = os.path.join(raw, "%s__%s.jpg" % (name, tag))
            d.text((x, y + 2), "%s  %s" % (name, tag), fill=(200, 200, 215))
            if os.path.exists(f):
                im = Image.open(f).convert("RGB")
                im = im.resize((TW, int(TW * im.height / im.width)), Image.BOX)
                img.paste(im.crop((0, 0, TW, min(TH, im.height))), (x, y + LAB))
                n += 1
            else:
                d.rectangle((x, y + LAB, x + TW - 1, y + LAB + TH - 1), outline=(120, 40, 40))
                d.text((x + 10, y + LAB + 10), "missing", fill=(220, 90, 90))
        y += TH + LAB + PAD
    img.save(path, quality=82, optimize=True, progressive=True)
    print("sheet", path, n, "frames")


def main():
    raw, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    groups = {}
    for pre, w, ids in worlds():
        rows = [pre + i.replace(".", "_") for i in ids]
        sheet(raw, rows, ["a24", "mid", "win"], os.path.join(out, "world_%s.jpg" % w), "World %s: a few seconds in | later | hotspot window" % w)
        g = pre.rstrip("_") or "main"
        groups.setdefault(g, []).extend(rows)
    for g, rows in groups.items():
        sheet(raw, rows, ["end", "nx0", "nx3"], os.path.join(out, "joins_%s.jpg" % g), "Joins (%s): last moment of the scene | 0.3 s into the next | 3 s into the next" % g)
    if len(sys.argv) > 3:
        ex = sys.argv[3]
        have = sorted(f[:-4] for f in os.listdir(ex) if f.endswith(".jpg"))
        pick = lambda pre: [n for n in have if n.startswith(pre)]
        grid(ex, ["home_screen", "home_chapters"] + pick("state_") + pick("doorwalk_"), os.path.join(out, "ui.jpg"),
             "UI: main menu, chapters, a hotspot in each state (before, selected, committed, success, failure, the wizard), a door walk")
        ent = []
        for q in ("gospel", "squadron", "ember"):
            ent += ["portal_%s__%s" % (q, t) for t in ("lit", "selected", "end", "nx0", "nx3", "nx10")]
        grid(ex, ent, os.path.join(out, "entrances.jpg"), "Quest entrances: lit | selected | last moment | into the path 0.3 s | 3 s | 10 s (gospel, squadron, ember)", cols=6)
        order = ["m2_0", "m1_0", "m0_55", "m0_3", "0_05", "0_3", "0_75", "1_5", "3_0", "6_0"]
        grid(ex, ["passage_wh_ms__" + o for o in order] + ["passage_uw_ward__" + o for o in ("m0_55", "0_05", "0_75", "3_0")],
             os.path.join(out, "passage.jpg"), "The passage between worlds: Warehouse exit -> Mothership (-2 s .. +6 s), Underworld exit -> Ward", cols=5)
        grid(ex, pick("bassment_"), os.path.join(out, "bassment.jpg"), "The Bassment: every zone's first passage, a few beats in | the window open", cols=4)
        grid(ex, pick("wide_"), os.path.join(out, "wide_20x9.jpg"), "20:9 (1600 x 720): a few seconds in | the window", cols=4)


if __name__ == "__main__":
    main()
