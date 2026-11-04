#!/usr/bin/env python3
"""Contact sheets of the baked people: `python3 tools/story/figure_sheets.py [chapter...] [--out docs/shots/story]`.

docs/shots/story/figures_<chapter>.jpg: every actor of the chapter at front-row size (the full-size sheet frame, one sheet pixel shown as 2 x 2), in the state
they are most often seen in (their own activity, else the dance), lit by a neutral light, with their id and look underneath, beside a crop of
pixelexample/Rave.png (the owner's figure reference) at the same scale. Reads only the built sheets (assets/story/<chapter>/people/).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CHAPTERS = ("night_one", "mothership", "underworld", "hospital", "mental_hospital")
ZOOM = 2
BG = (24, 18, 36)


def load(chapter):
    d = os.path.join(ROOT, "assets", "story", chapter, "people")
    doc = json.load(open(os.path.join(d, "people.json"), encoding="utf-8"))
    pages = [np.array(Image.open(os.path.join(ROOT, "assets", "story", chapter, p))) for p in doc["pages"]]
    pal = np.array(Image.open(os.path.join(ROOT, "assets", "story", chapter, doc["palette"])).convert("RGBA"))
    return doc, pages, pal


def frame_img(doc, pages, pal, row, fidx):
    f = doc["frames"][fidx * 9:fidx * 9 + 9]
    pg, x, y, w, h, px, py = f[:7]
    idx = pages[pg][y:y + h, x:x + w]
    out = np.zeros((h, w, 4), np.uint8)
    m = idx > 0
    out[m] = pal[row][(idx[m] & 127)]
    out[..., 3] = np.where(m, 255, 0)
    return Image.fromarray(out, "RGBA"), (px, py)


def pick_state(actor, cdata):
    st = actor["states"]
    lock = str(cdata.get("activity", ""))
    if lock and lock in st:
        return lock
    for k in ("dance", "drink", "chat", "idle"):
        if k in st:
            return k
    return sorted(st)[0]


def sheet(chapter, out_dir):
    doc, pages, pal = load(chapter)
    data = json.load(open(os.path.join(ROOT, "content", "story", chapter + ".json"), encoding="utf-8"))
    by_id = {str(a["id"]): a for a in data["actors"]}
    cells = []
    for aid in [str(a["id"]) for a in data["actors"] if str(a["id"]) in doc["actors"]]:
        a = doc["actors"][aid]
        st = pick_state(a, by_id[aid])
        e = a["states"][st]
        n = e[1]
        lst = e[2] or e[3] or e[4]
        im, piv = frame_img(doc, pages, pal, a["row"], lst[min(n - 1, n // 3)])
        cells.append((aid, st, by_id[aid], im, piv))
    cw = 70 * ZOOM
    ch = 165 * ZOOM
    cols = 16
    rows = (len(cells) + cols - 1) // cols
    ref = Image.open(os.path.join(ROOT, "pixelexample", "Rave.png")).convert("RGB")
    # the reference is about 440 pixel-art pixels wide drawn at 4x: shown at the sheets' own pixel scale (ZOOM per art pixel)
    rc = ref.crop((180, 230, 1600, 700))
    rc = rc.resize((int(rc.width / 4 * ZOOM), int(rc.height / 4 * ZOOM)), Image.NEAREST)
    W = max(cols * cw, 600) + rc.width + 30
    H = max(rows * (ch + 24), rc.height + 40) + 40
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    dr.text((10, 8), f"{chapter}: {len(cells)} actors, full-size sheet frames (1 sheet pixel = {ZOOM}x{ZOOM}), unlit", fill=(220, 210, 240))
    for i, (aid, st, cd, im, piv) in enumerate(cells):
        cx = (i % cols) * cw
        cy = 30 + (i // cols) * (ch + 24)
        big = im.resize((im.width * ZOOM, im.height * ZOOM), Image.NEAREST)
        ox = cx + cw // 2 - piv[0] * ZOOM
        oy = cy + ch - piv[1] * ZOOM
        img.paste(big, (int(ox), int(oy)), big)
        dr.text((cx + 3, cy + ch + 2), f"{aid}", fill=(200, 190, 220))
        dr.text((cx + 3, cy + ch + 12), f"{cd.get('archetype', '')} {st}"[:16], fill=(140, 130, 170))
    rx = W - rc.width - 10
    img.paste(rc, (rx, 30))
    dr.text((rx, 30 + rc.height + 6), "reference: pixelexample/Rave.png (crop, at the same pixel scale)", fill=(200, 190, 220))
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"figures_{chapter}.jpg")
    img.save(path, quality=88)
    print(path, img.size)


def main(argv):
    out = os.path.join(ROOT, "docs", "shots", "story")
    chs = []
    i = 1
    while i < len(argv):
        if argv[i] == "--out":
            out = argv[i + 1]
            i += 2
            continue
        chs.append(argv[i])
        i += 1
    for c in chs or CHAPTERS:
        if os.path.exists(os.path.join(ROOT, "assets", "story", c, "people", "people.json")):
            sheet(c, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
