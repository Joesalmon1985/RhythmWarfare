"""The Underworld's three guides (docs/doom/scenes/underworld.md), billboard sprites 256 px tall in the Warehouse guides' sheet layout (idle 1, available 5, selected 2, committed 2), written to
assets/story/doom_underworld/textures/:

  * `floor` (left: the braided woman in the magenta top and silver trousers): CROPPED from the painting (`Three Paths Across the Basalt Abyss-4.png`, 286 px tall there);
  * `dock` (right: the broad bald man in the long green coat with the yellow armband): CROPPED from the Mothership painting (`Mothership Ringwalk Over the Void-7.png`, 335 px tall there), the
    same character; the Underworld painting's figure is cut by a rock and the crates, so its own crop would lose the feet;
  * `mothership` (ahead: the tall pale lilac figure with a white crest in a purple robe): PROCEDURAL (78 px tall in the painting, too small to crop): make_guides.py's figure with a robe to the ankles, a
    crest and a cape, finished with `finish` (a warm rim, sequins dithered on the robe's trim).

    python -I tools/doom/art/make_underworld_guides.py     also writes docs/shots/doom/underworld/guides_sheet.png

The crop (`crop_figure`, also used by tools/doom/art/make_mothership_guides.py): a hand-traced outline of the figure in the painting's pixels (a polygon, about 40 points), refined by colour: a pixel in the
outline's 3 px edge band whose colour is nearer the surround (the median of the pixels just outside) than the figure's own interior is dropped, then a flood from the box's corners removes what
is connected to the surround through such pixels; the mask is cleaned with one erosion and one dilation, scaled nearest-neighbour to the sheet height and given a 1 px ink outline. The four states
are small edits of the one crop: `available` a lamp-lit warm rim on the figure's lit edge (5 frames, the rim and a 1 px bob breathe), `selected` a brighter rim and the outstretched hand raised,
`committed` the figure turned away into its doorway (mirrored, the rim on the far edge, a shade darker). No ring, no beacon.
"""
from __future__ import annotations

import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_guides as mg  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

ROOT = mg.ROOT
OUT = os.path.join(ROOT, "assets", "story", "doom_underworld", "textures")
SHEET = os.path.join(ROOT, "docs", "shots", "doom", "underworld", "guides_sheet.png")
H = mg.H
FIG_H = 236  # the figure's height in the 256 px sheet (the procedural guides stand 235 px tall)
FEET = 252
UW_PAINTING = os.path.join(ROOT, "art", "reference", "doom_worlds", "Three Paths Across the Basalt Abyss-4.png")
MS_PAINTING = os.path.join(ROOT, "art", "reference", "doom_worlds", "Mothership Ringwalk Over the Void-7.png")

# hand-traced outlines in the painting's pixels; `hand` is the box of the outstretched hand (raised for `selected`); `lit` the side the warm rim falls on (+1 right, -1 left)
FLOOR_FIG = dict(painting=UW_PAINTING, lit=1, hand=(205, 362, 260, 395), poly=[
    (137, 328), (150, 322), (165, 329), (175, 341), (174, 371), (182, 379), (225, 380), (238, 368), (259, 375), (249, 387), (200, 393), (186, 402), (183, 420), (189, 443), (193, 467),
    (193, 500), (184, 543), (176, 570), (186, 600), (179, 610), (131, 610), (129, 590), (139, 565), (132, 512), (129, 478), (135, 455), (123, 446), (111, 425), (112, 405), (116, 385),
    (119, 360), (127, 338)])
DOCK_FIG = dict(painting=MS_PAINTING, lit=-1, band=6, key=[(1420, 450, 1455, 520), (1440, 560, 1460, 600), (1622, 540, 1640, 600), (1520, 560, 1528, 580)], key_dist=40, hand=(1390, 315, 1440, 350), poly=[
    (1392, 330), (1402, 321), (1418, 317), (1432, 327), (1470, 326), (1500, 311), (1512, 299), (1514, 282), (1526, 270), (1546, 268), (1556, 281), (1557, 293), (1572, 301), (1592, 321),
    (1608, 344), (1613, 380), (1612, 470), (1609, 520), (1601, 537), (1587, 540), (1587, 575), (1584, 598), (1575, 605), (1538, 605), (1532, 590), (1532, 562), (1520, 556), (1519, 580),
    (1506, 586), (1461, 586), (1460, 572), (1477, 548), (1477, 538), (1461, 528), (1461, 480), (1473, 420), (1479, 395), (1483, 356), (1450, 352), (1430, 348), (1410, 345), (1395, 342)])


def crop_figure(fig):
    """The figure cut out of its painting at the painting's resolution: (RGBA image of the figure's bounding box, the box)."""
    src = np.array(Image.open(fig["painting"]).convert("RGB")).astype(np.int32)
    xs, ys = [p[0] for p in fig["poly"]], [p[1] for p in fig["poly"]]
    pad = 8
    x0, y0, x1, y1 = min(xs) - pad, min(ys) - pad, max(xs) + pad + 1, max(ys) + pad + 1
    rgb = src[y0:y1, x0:x1]
    h, w = rgb.shape[:2]
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).polygon([(x - x0, y - y0) for x, y in fig["poly"]], fill=255)
    inside = np.array(m) > 127
    inner = np.array(m.filter(ImageFilter.MinFilter(2 * fig.get("band", 3) + 1))) > 127  # the figure's sure interior (the band is its edge, `band` px, 3 by default)
    outer = ~(np.array(m.filter(ImageFilter.MaxFilter(7))) > 127)  # the sure surround
    band = inside & ~inner
    sur = np.median(rgb[outer].reshape(-1, 3), axis=0) if outer.any() else np.zeros(3)
    fig_mean = rgb[inner].reshape(-1, 3).mean(axis=0)
    # per band pixel: nearer the local surround (the median of the sure-surround pixels in a 9 px window) than the figure? then it is surround
    drop = np.zeros_like(band)
    for y, x in zip(*np.nonzero(band)):
        ya, yb, xa, xb = max(0, y - 4), min(h, y + 5), max(0, x - 4), min(w, x + 5)
        o = outer[ya:yb, xa:xb]
        loc = np.median(rgb[ya:yb, xa:xb][o].reshape(-1, 3), axis=0) if o.any() else sur
        c = rgb[y, x]
        if np.abs(c - loc).sum() < 0.6 * np.abs(c - fig_mean).sum() and np.abs(c - loc).sum() < 60:
            drop[y, x] = True
    if fig.get("key"):  # a colour key: anything inside the outline the colour of the surround's sample boxes (the floor seen between the legs) is surround
        smp = np.concatenate([src[b[1]:b[3], b[0]:b[2]].reshape(-1, 3) for b in fig["key"]])[::7]
        smp = smp[smp.sum(axis=1) >= fig.get("key_min", 260)]  # (the samples' shadows are left out: they match the coat's)
        for c0 in range(0, h, 16):
            blk = rgb[c0:c0 + 16].reshape(-1, 1, 3)
            dist = np.abs(blk - smp[None, :, :]).sum(axis=2).min(axis=1).reshape(rgb[c0:c0 + 16].shape[:2])
            drop[c0:c0 + 16] |= inside[c0:c0 + 16] & (dist < fig.get("key_dist", 36))
    keep = inside & ~drop
    # the flood from the corners: surround that reaches into the band through dropped pixels goes
    seen = ~keep
    stack = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    flood = np.zeros_like(keep)
    while stack:
        y, x = stack.pop()
        if y < 0 or x < 0 or y >= h or x >= w or flood[y, x] or not seen[y, x]:
            continue
        flood[y, x] = True
        stack.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    keep = ~flood & inside
    km = Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
    keep = (np.array(km) > 127) & inside
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = rgb.astype(np.uint8)
    out[..., 3] = np.where(keep, 255, 0)
    im = Image.fromarray(out, "RGBA")
    bb = im.getbbox()
    return im.crop(bb), (x0 + bb[0], y0 + bb[1])


def _outline(im, col=(18, 10, 24)):
    a = np.array(im)
    al = a[..., 3] > 127
    grown = np.array(Image.fromarray((al * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 127
    ring = grown & ~al
    a[ring, :3] = col
    a[ring, 3] = 255
    return Image.fromarray(a, "RGBA")


def _rim(im, side, strength, col=(255, 196, 120)):
    """A lamp-lit rim: the figure's pixels within 2 px of its edge on `side` (+1 right, -1 left) pulled toward a warm colour, dithered (style guide: dithered highlights)."""
    a = np.array(im).astype(np.float32)
    al = a[..., 3] > 127
    h, w = al.shape
    edge = np.zeros_like(al)
    for k in (1, 2):
        sh = np.zeros_like(al)
        if side > 0:
            sh[:, :-k] = al[:, k:]
        else:
            sh[:, k:] = al[:, :-k]
        edge |= al & ~sh
    yy, xx = np.mgrid[0:h, 0:w]
    dith = mg.BAYER[yy % 4, xx % 4] < strength
    sel = edge & dith
    for c in range(3):
        a[..., c][sel] = a[..., c][sel] * (1 - strength * 0.8) + col[c] * strength * 0.8
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")


def _shift_region(im, box, dy):
    """The pixels of the figure inside box (sheet pixels) moved up by dy (the outstretched hand raised); the hole they leave is cleared."""
    a = np.array(im)
    x0, y0, x1, y1 = [int(v) for v in box]
    part = a[y0:y1, x0:x1].copy()
    a[y0:y1, x0:x1][part[..., 3] > 127] = 0
    for y in range(y1 - y0):
        ty = y0 + y - dy
        if 0 <= ty < a.shape[0]:
            row = part[y]
            m = row[..., 3] > 127
            a[ty, x0:x1][m] = row[m]
    return Image.fromarray(a, "RGBA")


def crop_frames(fig):
    """The ten frames {state: [RGBA]} of a cropped guide: the sheet is the figure's width plus 8 px, 256 tall, feet on row FEET."""
    im, (ox, oy) = crop_figure(fig)
    k = FIG_H / float(im.height)
    fw, fh = max(1, round(im.width * k)), FIG_H
    small = im.resize((fw, fh), Image.NEAREST)
    W = fw + 10
    W += W % 2
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    left = (W - fw) // 2
    base.alpha_composite(small, (left, FEET - fh))
    hx0, hy0, hx1, hy1 = fig["hand"]
    hand = (left + (hx0 - ox) * k - 2, FEET - fh + (hy0 - oy) * k - 2, left + (hx1 - ox) * k + 2, FEET - fh + (hy1 - oy) * k + 2)
    hand = (max(0, hand[0]), max(0, hand[1]), min(W, hand[2]), min(H, hand[3]))
    lit = fig["lit"]
    out = {"idle": [_outline(base)]}
    out["available"] = []
    for i in range(5):
        f = _rim(base, lit, [0.45, 0.6, 0.75, 0.6, 0.45][i])
        if i in (1, 2, 3):  # a 1 px breath
            f = Image.fromarray(np.roll(np.array(f), -1, axis=0), "RGBA")
        out["available"].append(_outline(f))
    out["selected"] = [_outline(_rim(_shift_region(base, hand, dy), lit, 0.95, (255, 226, 160))) for dy in (6, 10)]
    turned = base.transpose(Image.FLIP_LEFT_RIGHT)
    dark = np.array(turned).astype(np.float32)
    dark[..., :3] *= 0.86
    turned = Image.fromarray(dark.astype(np.uint8), "RGBA")
    out["committed"] = [_outline(_rim(turned, -lit, s)) for s in (0.5, 0.7)]
    return out


def finish(im, robe=None, sequins=("#f0e0ff", "#c8a0f0")):
    """The procedural figure brought toward the sprite standard: a warm lamp rim on its right edge, a cool one on its left, and sequins dithered over the pixels of the `robe` colour."""
    im = _rim(_rim(im, 1, 0.55), -1, 0.3, (150, 160, 255))
    if robe is None:
        return im
    a = np.array(im)
    rc = np.array(mg.hexc(robe))
    near = (np.abs(a[..., :3].astype(int) - rc).sum(axis=2) < 70) & (a[..., 3] > 127)
    h, w = near.shape
    yy, xx = np.mgrid[0:h, 0:w]
    hsh = ((xx // 2) * 73856093 ^ yy * 19349663) % 997 / 997.0
    for i, c in enumerate(sequins):
        s = near & (hsh >= i * 0.025) & (hsh < (i + 1) * 0.025)
        a[s, :3] = mg.hexc(c)
    return Image.fromarray(a, "RGBA")


MOTHERSHIP = dict(skin="#cbb8dc", hair="#f4f0ff", top="#6a2c8e", vest="#3a1a52", trousers="#6a2c8e", shoes="#140c1e", accent="#e8c8ff", curly=False, moustache=False, glasses=False)


def mothership(state, i):
    """The Underworld's Mothership guide: the tall pale lilac figure of the painting, a white crest of spikes, a purple robe to the ankles with a cape, a silver collar."""
    base = dict(mg.GUIDES["bar"])
    mg.GUIDES["bar"] = {**base, **MOTHERSHIP}
    try:
        im = mg.draw_guide("bar", state, i)
    finally:
        mg.GUIDES["bar"] = base
    p = mg.poses(state, i)
    cx = int(mg.CX + p["lean"] * 0.4 + p["tilt"])
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    robe, robe_d, crest, silver = mg.hexc("#6a2c8e"), mg.hexc("#3a1458"), mg.hexc("#f4f0ff"), mg.hexc("#c8c0dc")
    d.polygon([(cx - 26, 84), (cx - 40, 246), (cx - 20, 250), (cx - 14, 120)], fill=robe_d)  # the cape behind the left side
    d.polygon([(cx - 22, 140), (cx + 22, 140), (cx + 30, 246), (cx - 30, 246)], fill=robe)  # the robe's skirt over the legs
    for x in range(cx - 28, cx + 30, 6):
        d.line([(x, 150), (x + (x - cx) // 6, 246)], fill=robe_d)
    d.rectangle([cx - 30, 242, cx + 30, 246], fill=silver)
    d.polygon([(cx - 14, 78), (cx + 14, 78), (cx + 8, 90), (cx - 8, 90)], fill=silver)  # the collar
    for k in range(-3, 4):  # the crest: white spikes over the head
        d.polygon([(cx + k * 5 - 3, 30), (cx + k * 5 + 3, 30), (cx + k * 7, 8 + abs(k) * 4)], fill=crest)
    im = _over(im, lay)
    a = np.array(im)  # the mouth: a smile (corners up) over the base figure's
    a[61:68, cx - 6:cx + 7, :3] = mg.hexc(MOTHERSHIP["skin"])
    for k in range(-5, 6):
        a[66 - int(round(2 * (k / 5.0) ** 2)), cx + k, :3] = (120, 40, 70)
    im = Image.fromarray(a, "RGBA")
    return finish(_outline(im), robe="#6a2c8e")


def _over(im, lay):
    """lay drawn over im where lay is opaque, except over the head and arms (kept from im where im's pixel is skin)."""
    a, b = np.array(im), np.array(lay)
    skin = (np.abs(a[..., :3].astype(int) - np.array(mg.hexc(MOTHERSHIP["skin"]))).sum(axis=2) < 90) & (a[..., 3] > 127)
    put = (b[..., 3] > 127) & ~skin
    a[put] = b[put]
    return Image.fromarray(a, "RGBA")


def frames(who):
    if who == "mothership":
        return {st: [mothership(st, i) for i in range(n)] for st, n in mg.FRAMES.items()}
    return crop_frames(FLOOR_FIG if who == "floor" else DOCK_FIG)


def write_sheet(rows, path, bg):
    """rows: [{state: [frames]}]: one row per guide, the frames in state order, each cell as wide as the widest frame."""
    cw = max(f.width for r in rows for fs in r.values() for f in fs)
    cols = sum(mg.FRAMES.values())
    sheet = Image.new("RGBA", (cols * cw, len(rows) * H), bg)
    for r, fr in enumerate(rows):
        x = 0
        for st in mg.FRAMES:
            for f in fr[st]:
                sheet.alpha_composite(f, (x * cw + (cw - f.width) // 2, r * H))
                x += 1
    sheet.convert("RGB").resize((sheet.width // 2, sheet.height // 2), Image.NEAREST).save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    rows, n = [], 0
    for who in ["mothership", "floor", "dock"]:
        fr = frames(who)
        for st, fs in fr.items():
            for i, im in enumerate(fs):
                im.save(os.path.join(OUT, "guide_%s_%s_%d.png" % (who, st, i)))
                n += 1
        rows.append(fr)
    write_sheet(rows, SHEET, (40, 8, 8, 255))
    print("wrote %d sprites to %s and the sheet %s" % (n, OUT, SHEET))


if __name__ == "__main__":
    sys.exit(main())
