#!/usr/bin/env python3
"""Zoomed head sheets of the baked people: `python3 tools/story/face_sheets.py <tag> [chapter...] [--zoom 8] [--out docs/shots/faces]`.

docs/shots/faces/<chapter>_<tag>.jpg: for every actor of the chapter, the head cropped from the built sheets (assets/story/<chapter>/people/) and shown
magnified (nearest neighbour, one sheet pixel = `zoom` x `zoom`, unlit) in the face states the actor has: neutral (idle), happy (dance / chat), cheer and
sad, front and three-quarter (the walk, or the actor's own side state), the back, then the half and quarter levels of detail of the idle front (each at
the same zoom, so they show as the small heads they are). The tag is a free label (`before`, `after`). The head is located from the actor's wardrobe spec
and the dumped pose (people.Body), so the crop follows a leaning or bobbing head; everything shown is the shipped sheet pixels.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from art import people, wardrobe  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
CHAPTERS = ("night_one", "mothership", "underworld", "hospital", "mental_hospital")
BG = (24, 18, 36)
CELL_BG = (40, 34, 56)

# (label, candidate states, facing, lod): the first state the actor has is shown
COLUMNS = [
    ("neutral", ("idle", "stare", "watch", "walk"), 0, 1),
    ("happy", ("dance", "chat", "clap", "wave", "toast"), 0, 1),
    ("cheer", ("cheer", "hands_up", "solo"), 0, 1),
    ("sad", ("sad", "rock"), 0, 1),
    ("3/4", ("walk", "chat", "watch", "serve", "pace"), 1, 1),
    ("back", ("walk", "watch", "pace"), 2, 1),
    ("lod2", ("idle", "walk"), 0, 2),
    ("lod4", ("idle", "walk"), 0, 4),
]


def load(chapter):
    d = os.path.join(ROOT, "assets", "story", chapter, "people")
    doc = json.load(open(os.path.join(d, "people.json"), encoding="utf-8"))
    pages = [np.array(Image.open(os.path.join(ROOT, "assets", "story", chapter, p))) for p in doc["pages"]]
    pal = np.array(Image.open(os.path.join(ROOT, "assets", "story", chapter, doc["palette"])).convert("RGBA"))
    return doc, pages, pal


def head_crop(doc, pages, pal, row, fidx, spec, pose, state, fc, lod):
    """The head of one frame as an RGBA image (a box around the head centre, rig -> image through the frame's pivot)."""
    f = doc["frames"][fidx * 9:fidx * 9 + 9]
    pg, x, y, w, h, px, py = f[:7]
    idx = pages[pg][y:y + h, x:x + w]
    S = people.H0 / lod * float(spec.get("height", 1.0))
    b = people.Body(spec, pose, S, fc, state)
    hx, hy = b.head_c
    half_w = int(round(b.head_w * 0.95 + 2))
    half_h = int(round(b.head_h * 0.8 + 2))
    cx, cy = px + hx, py + hy - b.head_h * 0.1
    x0, y0 = int(round(cx)) - half_w, int(round(cy)) - half_h
    out = np.zeros((2 * half_h, 2 * half_w, 4), np.uint8)
    out[..., :3] = CELL_BG
    out[..., 3] = 255
    for r in range(2 * half_h):
        for c in range(2 * half_w):
            ix, iy = x0 + c, y0 + r
            if 0 <= ix < w and 0 <= iy < h and idx[iy, ix] > 0:
                out[r, c] = pal[row][idx[iy, ix] & 127]
    return Image.fromarray(out, "RGBA")


def sheet(chapter, tag, out_dir, zoom):
    doc, pages, pal = load(chapter)
    data = json.load(open(os.path.join(ROOT, "content", "story", chapter + ".json"), encoding="utf-8"))
    poses = json.load(open(os.path.join(ROOT, "assets", "story", "people_poses.json"), encoding="utf-8"))
    keys = poses["keys"]
    cast = wardrobe.cast_chapter(chapter, data["actors"])
    ids = [str(a["id"]) for a in data["actors"] if str(a["id"]) in doc["actors"]]
    by_id = {str(a["id"]): a for a in data["actors"]}
    # one full-size head cell: the largest box any head needs at lod 1
    cw, chh = 0, 0
    rows = []
    for aid in ids:
        a = doc["actors"][aid]
        spec = cast[aid]
        cells = []
        for label, cands, fc, lod in COLUMNS:
            im = None
            for st in cands:
                e = a["states"].get(st)
                if not e or e[2 + fc] is None:
                    continue
                pst = "dance_s%d" % a["style"] if st == "dance" else st
                cyc = poses["states"].get(pst)
                if cyc is None:
                    continue
                n = e[1]
                li = people.LODS.index(lod)
                fidx = e[2 + fc][li * n + 0]
                pose = dict(zip(keys, cyc["frames"][0]))
                base = "dance" if st.startswith("dance") else st
                im = head_crop(doc, pages, pal, a["row"], fidx, spec, pose, base, fc, lod)
                break
            cells.append((label, im))
            if im is not None and lod == 1:
                cw, chh = max(cw, im.width), max(chh, im.height)
        rows.append((aid, cells))
    cw, chh = cw * zoom, chh * zoom
    gap = 6
    per_line = 2  # two actors side by side
    line_w = len(COLUMNS) * (cw + gap) + 90
    W = per_line * line_w + 20
    lines = (len(rows) + per_line - 1) // per_line
    H = 40 + lines * (chh + 30)
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    dr.text((10, 8), f"{chapter} faces ({tag}): heads from the built sheets, 1 sheet pixel = {zoom}x{zoom}, unlit. Columns: "
            + ", ".join(c[0] for c in COLUMNS), fill=(220, 210, 240))
    for i, (aid, cells) in enumerate(rows):
        ox = 10 + (i % per_line) * line_w
        oy = 34 + (i // per_line) * (chh + 30)
        arch = str(by_id[aid].get("archetype", ""))
        dr.text((ox, oy + 4), aid, fill=(220, 210, 240))
        dr.text((ox, oy + 18), arch[:12], fill=(150, 140, 180))
        for k, (label, im) in enumerate(cells):
            x = ox + 90 + k * (cw + gap)
            dr.rectangle((x, oy, x + cw - 1, oy + chh - 1), fill=CELL_BG)
            if im is not None:
                big = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
                img.paste(big, (x + (cw - big.width) // 2, oy + (chh - big.height) // 2))
            dr.text((x + 2, oy + chh + 2), label, fill=(140, 130, 170))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{chapter}_{tag}.jpg")
    img.save(path, quality=90)
    print(path, img.size)
    return path


def main(argv):
    out = os.path.join(ROOT, "docs", "shots", "faces")
    zoom = 8
    args = []
    i = 1
    while i < len(argv):
        if argv[i] == "--out":
            out = argv[i + 1]
            i += 2
            continue
        if argv[i] == "--zoom":
            zoom = int(argv[i + 1])
            i += 2
            continue
        args.append(argv[i])
        i += 1
    if not args:
        print(__doc__)
        return 2
    tag, chs = args[0], args[1:]
    for c in chs or CHAPTERS:
        if os.path.exists(os.path.join(ROOT, "assets", "story", c, "people", "people.json")):
            sheet(c, tag, out, zoom)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
