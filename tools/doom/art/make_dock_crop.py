"""Guide sprites CROPPED from the concept paintings (lead ruling 36, docs/briefs/DOOM_POLISH_BRIEF.md step 6), shared by the Dock, the Balcony and the Booth.

    python -I tools/doom/art/make_dock_crop.py preview <who>     writes <scratch>/crop_<who>.png (the mask and the four states, 3x) for looking

A guide that the painting shows at least 180 px tall is cut out of it, not redrawn:
  1. the mask: inside the figure's box, a pixel is "surround" when its colour is close (RGB distance) to the colours sampled on the box's border (its surround); a flood from the
     border and the corners over surround pixels marks the background, everything the flood cannot reach is the figure; `cut` rectangles/polygons are forced to background and
     `keep` ones to the figure (the painter's hints where the surround has the figure's colours); a small erosion then dilation cleans the edge, and only the largest connected
     piece is kept;
  2. the scale: nearest-neighbour to the sheet's figure height (alpha 0 or 255 only, style guide section 6), feet on the sheet's bottom row (or `foot_gap` rows above it, where
     the painting hides the legs behind a prop the scene puts in front), centred;
  3. the states (the Warehouse guides' layout: idle 1, available 5, selected 2, committed 2): idle is the crop; available a lamp-lit rim (the edge pixels lifted toward the lamp
     colour, five steps of a slow pulse); selected a brighter rim and the beckoning hand box raised a few pixels; committed the figure turned away (mirrored) and a step dimmer.
No ring, no beacon, no outline colour: the state is in the figure's own light and pose (ruling 35b).
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
REF = os.path.join(ROOT, "art", "reference", "doom_worlds")
SHEET = (160, 256)
FRAMES = {"idle": 1, "available": 5, "selected": 2, "committed": 2}

# who: painting, box (x0, y0, x1, y1 in painting pixels), colour tolerance, cut / keep shapes (rects (x0, y0, x1, y1) or polygons [(x, y), ...] in painting pixels),
#      figure height in the sheet (px), hand box (painting px) raised when selected, lamp colour of the rim, foot_gap (rows left empty under the cut, for a hidden lower body)
CROPS = {
    "underworld_dock7": dict(src="Rainy Dock of Three Paths-7.png", box=(1170, 200, 1482, 668), cut=[], keep=[], h=200, foot_gap=40, hand=(1420, 450, 1480, 495), lamp="#ff8a40",
                             band=4, drop=[("#3a3a52", 36), ("#5a5a72", 40), ("#7a7a90", 40)], poly=[(1252, 226), (1262, 212), (1290, 206), (1298, 246), (1320, 254), (1342, 246), (1380, 214), (1402, 222), (1404, 262), (1380, 290), (1352, 300), (1350, 330),
                                           (1365, 372), (1385, 420), (1395, 452), (1430, 458), (1462, 456), (1480, 470), (1476, 490), (1440, 492), (1400, 488), (1390, 520),
                                           (1408, 580), (1402, 660), (1268, 664), (1210, 650), (1196, 600), (1192, 548), (1180, 500), (1178, 420), (1188, 368), (1230, 340),
                                           (1278, 318), (1272, 290), (1262, 262)]),
    "floor_dock": dict(src="Rainy Rhythm Club Loading Dock-6.png", box=(115, 345, 352, 715), cut=[], keep=[], h=232, hand=(300, 420, 348, 462), lamp="#ffc070", drop=[("#1a28a0", 120), ("#2a40e0", 120), ("#101850", 60)],
                       poly=[(178, 358), (200, 356), (215, 368), (222, 395), (232, 430), (270, 440), (300, 438), (325, 428), (345, 436), (340, 452), (300, 458), (250, 458), (235, 465),
                             (232, 495), (241, 520), (246, 580), (244, 640), (248, 700), (240, 708), (205, 705), (178, 705), (170, 690), (168, 640), (170, 580), (160, 560), (152, 520),
                             (150, 470), (140, 450), (126, 445), (124, 400), (140, 398), (150, 420), (160, 430), (165, 395), (168, 370)]),
    "balcony_booth": dict(src="Rhythm Booth, Three Hidden Routes-5.png", box=(118, 230, 248, 480), cut=[(224, 365, 248, 480), (229, 300, 248, 338)], keep=[], h=232, hand=(118, 285, 145, 318), lamp="#c8d8ff", lit="right",
                          drop=[("#4a5878", 50), ("#6a7898", 50)],
                          poly=[(162, 238), (185, 236), (205, 244), (212, 268), (212, 284), (222, 300), (228, 330), (240, 342), (242, 362), (228, 362), (222, 380), (220, 415), (205, 422),
                                (203, 460), (210, 472), (185, 474), (178, 462), (170, 474), (155, 472), (158, 440), (160, 420), (140, 418), (138, 380), (142, 330), (132, 330), (128, 312),
                                (122, 300), (124, 290), (140, 290), (150, 284), (152, 262), (155, 246)]),
    "mothership_booth": dict(src="Rhythm Booth, Three Hidden Routes-5.png", box=(905, 270, 1008, 486), cut=[], keep=[], h=236, hand=(912, 330, 940, 352), lamp="#e0c8ff",
                             poly=[(955, 277), (965, 276), (978, 284), (975, 300), (980, 312), (984, 330), (988, 380), (990, 420), (996, 470), (996, 482), (918, 482), (922, 450), (926, 410),
                                   (932, 370), (936, 350), (925, 350), (916, 347), (918, 339), (935, 334), (940, 318), (948, 308), (944, 286)]),
    "dock_booth": dict(src="Rhythm Booth, Three Hidden Routes-5.png", box=(1412, 232, 1642, 698), cut=[(1614, 560, 1645, 700)], keep=[], h=236, hand=(1414, 326, 1470, 366), lamp="#ffc878",
                       poly=[(1540, 242), (1560, 238), (1574, 250), (1576, 280), (1600, 292), (1622, 305), (1634, 340), (1636, 420), (1634, 520), (1628, 600), (1615, 620), (1612, 690),
                             (1560, 692), (1555, 670), (1545, 692), (1500, 692), (1504, 650), (1508, 615), (1500, 580), (1500, 470), (1502, 380), (1496, 365), (1460, 362), (1424, 362),
                             (1418, 352), (1440, 342), (1452, 330), (1464, 342), (1500, 336), (1525, 312), (1535, 295), (1536, 268)]),
}


def _dist(a, b):
    return np.sqrt(((a.astype(np.int32) - b.astype(np.int32)) ** 2).sum(-1))


def _shape_mask(shape, size, off):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    if len(shape) == 4 and not isinstance(shape[0], (tuple, list)):
        x0, y0, x1, y1 = shape
        d.rectangle([x0 - off[0], y0 - off[1], x1 - off[0], y1 - off[1]], fill=255)
    else:
        d.polygon([(x - off[0], y - off[1]) for x, y in shape], fill=255)
    return np.array(m) > 0


def _flood(cand, seeds, img=None, step=None):
    """Flood over the True pixels of `cand` from the seed mask (4-connected); with `img` and `step`, a step to a neighbour also needs their colours within `step` (an edge stops it)."""
    h, w = cand.shape
    done = np.zeros_like(cand)
    stack = list(zip(*np.nonzero(seeds & cand)))
    for y, x in stack:
        done[y, x] = True
    while stack:
        y, x = stack.pop()
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= yy < h and 0 <= xx < w and cand[yy, xx] and not done[yy, xx] and (img is None or np.abs(img[yy, xx] - img[y, x]).sum() <= step):
                done[yy, xx] = True
                stack.append((yy, xx))
    return done


def _erode(m, n=1):
    for _ in range(n):
        p = np.pad(m, 1)
        m = p[1:-1, 1:-1] & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return m


def _dilate(m, n=1):
    for _ in range(n):
        p = np.pad(m, 1)
        m = p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return m


def _largest(m):
    lab = np.zeros(m.shape, np.int32)
    best, best_n, k = 0, 0, 0
    for y, x in zip(*np.nonzero(m)):
        if lab[y, x]:
            continue
        k += 1
        comp = _flood(m & (lab == 0), np.pad(np.ones((1, 1), bool), ((y, m.shape[0] - y - 1), (x, m.shape[1] - x - 1))))
        lab[comp] = k
        n = int(comp.sum())
        if n > best_n:
            best, best_n = k, n
    return lab == best


def _refine(a, p, band=5, win=7):
    """The outline polygon's edge settled by colour: every pixel within `band` of the polygon's edge goes to the figure or the surround, whichever of the two (its sure pixels
    just inside, beyond the band, and just outside) holds the nearer colour in a (2 win + 1) square round it."""
    a = a.astype(np.int32)
    sure_in = _erode(p, band)
    sure_out = ~_dilate(p, band)
    band_m = ~sure_in & ~sure_out
    out = p.copy()
    h, w = p.shape
    for y, x in zip(*np.nonzero(band_m)):
        ya, yb, xa, xb = max(0, y - win - band), min(h, y + win + band + 1), max(0, x - win - band), min(w, x + win + band + 1)
        c = a[y, x]
        fi = a[ya:yb, xa:xb][sure_in[ya:yb, xa:xb]]
        fo = a[ya:yb, xa:xb][sure_out[ya:yb, xa:xb]]
        if len(fi) == 0 or len(fo) == 0:
            continue
        di = np.abs(fi - c).sum(-1).min()
        do = np.abs(fo - c).sum(-1).min()
        out[y, x] = di <= do
    return out


def mask_of(spec):
    im = np.array(Image.open(os.path.join(REF, spec["src"])).convert("RGB"))
    x0, y0, x1, y1 = spec["box"]
    a = im[y0:y1, x0:x1]
    h, w, _ = a.shape
    if "poly" in spec:  # the outline traced from the painting, its edge settled by colour (the surround's colours against the figure's)
        p = _shape_mask(spec["poly"], (w, h), (x0, y0))
        fig = _refine(a, p, spec.get("band", 5))
        for col, tol in spec.get("drop", []):  # the surround's own colours where the outline is generous (a blue doorway between braids and wall)
            fig &= np.abs(a.astype(np.int32) - _hexc(col).astype(np.int32)).sum(-1) > tol
        for s in spec["cut"]:
            fig &= ~_shape_mask(s, (w, h), (x0, y0))
        for s in spec["keep"]:
            fig |= _shape_mask(s, (w, h), (x0, y0))
        fig = _dilate(_erode(fig, 1), 1)
        return a, _largest(fig)
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    pal = border[:: max(1, len(border) // 160)]  # the surround's colours
    near = np.full((h, w), 1e9)
    for c in pal:
        near = np.minimum(near, _dist(a, c[None, None, :]))
    cand = near < spec["tol"]
    seeds = np.zeros((h, w), bool)
    seeds[0, :] = seeds[-1, :] = seeds[:, 0] = seeds[:, -1] = True
    for s in spec.get("seed", []):  # extra background seeds inside the box (painting px)
        seeds[s[1] - y0, s[0] - x0] = True
    for s in spec["cut"]:
        cand |= _shape_mask(s, (w, h), (x0, y0))
    bg = _flood(cand, seeds, a.astype(np.int32), spec.get("step", 60))
    fig = ~bg
    for s in spec["cut"]:
        fig &= ~_shape_mask(s, (w, h), (x0, y0))
    for s in spec["keep"]:
        fig |= _shape_mask(s, (w, h), (x0, y0))
    fig = _dilate(_erode(fig, 1), 1)
    fig = _largest(fig)
    return a, fig


def crop(spec):
    """The figure as an RGBA image at the painting's scale, trimmed to its bounds, and its hand box in that image's pixels."""
    a, fig = mask_of(spec)
    ys, xs = np.nonzero(fig)
    t, b, l, r = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([a, np.where(fig, 255, 0).astype(np.uint8)])[t:b, l:r]
    hx0, hy0, hx1, hy1 = spec.get("hand", (0, 0, 0, 0))
    ox, oy = spec["box"][0] + l, spec["box"][1] + t
    return Image.fromarray(rgba, "RGBA"), (hx0 - ox, hy0 - oy, hx1 - ox, hy1 - oy)


def to_sheet(spec):
    fig, hand = crop(spec)
    W, H = SHEET
    gap = spec.get("foot_gap", 0)
    k = spec["h"] / fig.height
    nw, nh = max(1, round(fig.width * k)), spec["h"]
    if nw > W - 2:  # too wide for the sheet (an arm flung out): scale to the width instead
        k = (W - 2) / fig.width
        nw, nh = W - 2, max(1, round(fig.height * k))
    small = fig.resize((nw, nh), Image.NEAREST)
    a = np.array(small)
    a[..., 3] = np.where(a[..., 3] >= 128, 255, 0)
    small = Image.fromarray(a, "RGBA")
    out = Image.new("RGBA", SHEET, (0, 0, 0, 0))
    ox, oy = (W - nw) // 2, H - gap - nh
    out.paste(small, (ox, oy), small)
    hb = tuple(int(round(v * k)) for v in hand)
    return out, (hb[0] + ox, hb[1] + oy, hb[2] + ox, hb[3] + oy)


def _hexc(s):
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def _rim(img, lamp, amt, side="left"):
    """Lift the figure's edge pixels (and one more row in, at a lower weight) toward the lamp colour, on the lit side (dithered: every other pixel of the inner row)."""
    a = np.array(img).astype(np.float32)
    m = a[..., 3] > 0
    edge = m & ~_erode(m, 1)
    inner = _erode(m, 1) & ~_erode(m, 2)
    yy, xx = np.indices(m.shape)
    cx = xx[m].mean() if m.any() else m.shape[1] / 2
    lit_side = (xx <= cx + 6) if side == "left" else (xx >= cx - 6)
    dither = ((xx + yy) % 2) == 0
    c = _hexc(lamp)
    for sel, w in ((edge & lit_side & dither, amt), (edge & lit_side & ~dither, amt * 0.6), (inner & lit_side & dither, amt * 0.35)):
        a[sel, :3] = a[sel, :3] * (1 - w) + c * w
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def _raise(img, box, dy):
    """The beckoning hand: the figure's pixels inside the box move up dy rows (the rows they leave are cleared where the box is outside the body's core)."""
    if box[2] <= box[0] or dy <= 0:
        return img
    out = img.copy()
    x0, y0, x1, y1 = [max(0, v) for v in box]
    part = img.crop((x0, y0, x1, y1))
    clear = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    out.paste(clear, (x0, y0))
    out.paste(part, (x0, y0 - dy), part)
    return out


def _dim(img, k):
    a = np.array(img).astype(np.float32)
    a[..., :3] *= k
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def states(spec):
    """{state: [frames]} for the guide: idle 1, available 5, selected 2, committed 2 (see the module doc)."""
    base, hand = to_sheet(spec)
    lamp = spec.get("lamp", "#ffd090")
    side = spec.get("lit", "left")
    out = {"idle": [base]}
    out["available"] = [_rim(_dim(base, 1.06), lamp, w, side) for w in (0.25, 0.32, 0.4, 0.32, 0.25)]
    out["selected"] = [_rim(_raise(_dim(base, 1.14), hand, dy), lamp, 0.5, side) for dy in (4, 7)]
    turned = base.transpose(Image.FLIP_LEFT_RIGHT)
    out["committed"] = [_dim(turned, 0.92), _dim(turned, 0.84)]
    return out


def write(spec, out_dir, who):
    n = 0
    for st, frames in states(spec).items():
        for i, im in enumerate(frames):
            im.save(os.path.join(out_dir, "guide_%s_%s_%d.png" % (who, st, i)))
            n += 1
    return n


def preview(name, out):
    spec = CROPS[name]
    a, fig = mask_of(spec)
    vis = a.copy()
    vis[~fig] = (vis[~fig] * 0.25).astype(np.uint8) + np.array([0, 60, 0], np.uint8)
    st = states(spec)
    row = [st["idle"][0], st["available"][2], st["selected"][1], st["committed"][0]]
    W, H = SHEET
    sheet = Image.new("RGBA", (W * 4 * 2, H * 2), (40, 40, 60, 255))
    for i, im in enumerate(row):
        big = im.resize((W * 2, H * 2), Image.NEAREST)
        sheet.paste(big, (i * W * 2, 0), big)
    m = Image.fromarray(vis)
    canvas = Image.new("RGB", (sheet.width + m.width + 10, max(sheet.height, m.height)), (20, 20, 30))
    canvas.paste(m, (0, 0))
    canvas.paste(sheet.convert("RGB"), (m.width + 10, 0))
    canvas.save(out)
    print("wrote", out)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "preview":
        preview(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.environ.get("TEMP", "."), "crop_%s.png" % sys.argv[2]))
