#!/usr/bin/env python3
"""Contact sheets of the squadron story's people: `python3 tools/story/squadron_wardrobe_preview.py [--out DIR] [--wear airman,clerk] [--zoom 2] [--per 3]`.

Dresses `--per` invented actors (default 3) of every wear and variant (tools/story/art/wardrobe.py `squadron`, chapter `airfield`, cast together so the room
rule applies) and draws each at the full level of detail (LOD 1) in: idle (front, with the prop that wear usually holds), a three-quarter walk, a salute, writing
with a clipboard, a recoil, and the faces fear, anger, laugh and grief (the head enlarged). One PNG per wear in DIR (default: the system temp folder), and
`all_squadron.png` with a small standing figure of every actor for the whole cast at a glance. Reads assets/story/people_poses.json; builds nothing in the repo.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, ROOT)
from tools.story.art import people, wardrobe  # noqa: E402

BG = (104, 98, 90)
LABEL = (240, 236, 224)
WEAR_VARIANTS = {"airman": "abc", "officer": "abc", "clerk": "abc", "surgeon": "abc", "quartermaster": "abc", "gunner": "abc", "mp": "abc", "civilian_city": "abcd",
                 "fisherman": "abc", "patient": "abc"}
NAMES = {"airman": {"a": "plain airman", "b": "ground crew", "c": "pilot"}, "officer": {"a": "colonel", "b": "aide", "c": "chaplain"},
         "clerk": {"a": "waistcoat", "b": "cardigan", "c": "eyeshade"}, "surgeon": {"a": "scrub cap", "b": "bare head", "c": "bald"},
         "quartermaster": {"a": "apron", "b": "apron+cap", "c": "bald"}, "gunner": {"a": "helmet", "b": "helmet+scarf", "c": "helmet+freckles"},
         "mp": {"a": "mp", "b": "mp shades", "c": "mp"}, "civilian_city": {"a": "man", "b": "woman", "c": "child", "d": "singer"},
         "fisherman": {"a": "yellow oilskin", "b": "dark+sou'wester", "c": "jersey"}, "patient": {"a": "bandage", "b": "sling", "c": "plaster"}}
# the prop each wear usually holds in the story (the orchestrator sets `prop` on the actor)
HELD = {("clerk", "a"): "stamp", ("clerk", "b"): "stamp", ("clerk", "c"): "stamp", ("quartermaster", "a"): "egg", ("quartermaster", "b"): "egg",
        ("quartermaster", "c"): "egg", ("officer", "a"): "medal", ("officer", "b"): "clipboard", ("civilian_city", "d"): "hat", ("surgeon", "a"): "clipboard",
        ("surgeon", "b"): "clipboard", ("surgeon", "c"): "clipboard"}


def load_poses():
    return json.load(open(os.path.join(ROOT, "assets", "story", "people_poses.json"), encoding="utf-8"))


def pose_of(poses, state, which=0.5):
    st = poses["states"][state]
    fr = st["frames"]
    return dict(zip(poses["keys"], fr[min(len(fr) - 1, int(len(fr) * which))]))


def to_rgba(idx, pal_row):
    pal = np.array(pal_row, np.uint8)
    out = np.zeros(idx.shape + (4,), np.uint8)
    m = idx > 0
    out[m] = pal[(idx[m] & 127)]
    out[..., 3] = np.where(m, 255, 0)
    return out


def render(spec, poses, state, facing, lod, held, face, pal, which=0.5):
    img, piv, hand = people.render_frame(spec, pose_of(poses, state, which), state, facing, lod, held, face, int(spec.get("seed", 0)))
    return to_rgba(img, pal), piv


def paste(sheet, im, x, y, piv, zoom):
    """Paste an RGBA frame so its pivot (feet) lands at (x, y), scaled by `zoom` (nearest)."""
    pil = Image.fromarray(im, "RGBA")
    pil = pil.resize((pil.width * zoom, pil.height * zoom), Image.NEAREST)
    sheet.alpha_composite(pil, (int(x - piv[0] * zoom), int(y - piv[1] * zoom)))


def head_crop(im, zoom):
    """The head of a standing frame: the top rows of its pixels, enlarged."""
    ys = np.nonzero(im[..., 3])[0]
    x_ = np.nonzero(im[..., 3])[1]
    top = ys.min()
    h = max(18, int(im.shape[0] * 0.14))
    sub = im[top:top + h]
    cols = np.nonzero(sub[..., 3].any(axis=0))[0]
    if len(cols) == 0:
        return Image.new("RGBA", (1, 1))
    pil = Image.fromarray(sub[:, cols.min():cols.max() + 1], "RGBA")
    return pil.resize((pil.width * zoom, pil.height * zoom), Image.NEAREST)


def cast_for(wears, per):
    actors = []
    for w in wears:
        for v in WEAR_VARIANTS[w]:
            for i in range(1, per + 1):
                actors.append({"id": f"sq_{w}_{v}_{i}", "wear": w, "variant": v, "archetype": "groover", "art": "night_one", "view": "main"})
    return actors, wardrobe.cast_chapter("airfield", actors)


def make_sheets(out_dir, wears, per=3, zoom=2, faces=("fear", "anger", "laugh", "grief")):
    poses = load_poses()
    actors, cast = cast_for(wears, per)
    os.makedirs(out_dir, exist_ok=True)
    cw, ch = 62 * zoom, 130 * zoom
    cols = ["idle", "walk 3/4", "salute", "write", "recoil"] + list(faces)
    fw = 34 * zoom * 2
    paths = []
    allcells = []
    for w in wears:
        rows = [(a, cast[a["id"]]) for a in actors if a["wear"] == w]
        W = 150 + 5 * cw + len(faces) * fw
        H = 24 + len(rows) * (ch + 14)
        sheet = Image.new("RGBA", (W, H), BG + (255,))
        d = ImageDraw.Draw(sheet)
        for k, name in enumerate(cols):
            d.text((150 + (k * cw if k < 5 else 5 * cw + (k - 5) * fw) + 4, 6), name, fill=LABEL)
        for r_, (a, spec) in enumerate(rows):
            y0 = 24 + r_ * (ch + 14)
            pal = people.palette_row(spec["colours"])
            v = a["variant"]
            held = HELD.get((w, v), "")
            d.text((6, y0 + 6), f"{a['id'][3:]}\n{NAMES[w][v]}\nh {spec['height']:.2f} w {spec['width']:.2f}\nhair {spec['hair']['style']}", fill=LABEL)
            base = y0 + ch - 6
            cells = [("idle", 0, held, "neutral"), ("walk", 1, "", "neutral"), ("salute", 0, "", "resolve"), ("write", 0, "clipboard", "neutral"), ("recoil", 0, "", "fear")]
            for k, (st, fc, hd, fa) in enumerate(cells):
                im, piv = render(spec, poses, st, fc, 1, hd, fa, pal, 0.3 if st == "walk" else 0.5)
                paste(sheet, im, 150 + k * cw + cw // 2, base, piv, zoom)
            im0, _ = render(spec, poses, "idle", 0, 1, "", "neutral", pal)
            for k, fa in enumerate(faces):
                im, _ = render(spec, poses, "idle", 0, 1, "", fa, pal)
                hc = head_crop(im, zoom * 2)
                sheet.alpha_composite(hc, (150 + 5 * cw + k * fw + (fw - hc.width) // 2, y0 + 8))
            allcells.append((a, spec, pal))
        path = os.path.join(out_dir, f"squadron_{w}.png")
        sheet.convert("RGB").save(path)
        paths.append(path)
    # the whole cast, small, standing in a row per wear
    zoom_s = 1
    cell = 54
    per_row = 12
    rows_n = sum((len(WEAR_VARIANTS[w]) * per + per_row - 1) // per_row for w in wears)
    big = Image.new("RGBA", (per_row * cell, rows_n * 126 + 8), BG + (255,))
    y = 0
    for w in wears:
        grp = [c for c in allcells if c[0]["wear"] == w]
        for i, (a, spec, pal) in enumerate(grp):
            im, piv = render(spec, poses, "idle", 0, 1, HELD.get((w, a["variant"]), ""), "neutral", pal)
            paste(big, im, (i % per_row) * cell + cell // 2, y + (i // per_row) * 126 + 118, piv, zoom_s)
        y += ((len(grp) + per_row - 1) // per_row) * 126
    path = os.path.join(out_dir, "all_squadron.png")
    big.convert("RGB").save(path)
    paths.append(path)
    return paths


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(tempfile.gettempdir(), "squadron_wardrobe"))
    ap.add_argument("--wear", default="", help="comma separated wears (default: all ten)")
    ap.add_argument("--zoom", type=int, default=2)
    ap.add_argument("--per", type=int, default=3, help="actors per wear and variant")
    a = ap.parse_args()
    wears = [w for w in a.wear.split(",") if w] or list(WEAR_VARIANTS)
    for p in make_sheets(a.out, wears, a.per, a.zoom):
        print(p)


if __name__ == "__main__":
    main()
