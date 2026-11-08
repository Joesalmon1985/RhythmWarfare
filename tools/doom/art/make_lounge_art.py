"""The Chill-out Lounge's own textures and props (docs/doom/scenes/lounge.md): assets/story/doom_lounge/textures/*.png, 128 px tiles (and a few sprites), PLACEHOLDER pixel art
made procedurally (ordered-dither ramps), toward the painting `art/reference/doom_worlds/Mustard octagonal lounge of three routes-2.png`.

    python -I tools/doom/art/make_lounge_art.py        writes the PNGs and docs/shots/doom/lounge/art_sheet.png (the contact sheet of everything)

Walls: wall_stone (brown stone blocks), wall_sofa (mustard tufted upholstery), wall_curtain (maroon velvet folds), wall_wood (dark panelling), wall_copper (copper tiles), wall_table, wall_street
(wet concrete), wall_blue (blue glass panels), wall_beam (dark timber with gold inlay), wall_marble.  Floors: floor_marble, floor_rug_red / _cream / _orange, floor_sofa, floor_table, floor_wood,
floor_street, floor_blue, floor_curtain.  Ceilings: ceil_beam, ceil_street.  Decals (wall pictures): deco_studs (gold studded acoustic panel), deco_vinyl, deco_sconce, deco_bottles, deco_beads.
Things (billboards): thing_plant (a palm in a copper pot), thing_lamp (the mushroom table lamp), thing_vase, thing_cushion, thing_cushion_b.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = os.path.join(ROOT, "assets", "story", "doom_lounge", "textures")
SHEET = os.path.join(ROOT, "docs", "shots", "doom", "lounge", "art_sheet.png")
S = 128
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
YY, XX = np.mgrid[0:S, 0:S]
RNG = np.random.default_rng(8)


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def noise(scale, seed):
    """Tileable value noise 0..1 at a grid of `scale` cells."""
    r = np.random.default_rng(seed)
    g = r.random((scale, scale))
    ys, xs = np.mgrid[0:S, 0:S] / S * scale
    y0, x0 = np.floor(ys).astype(int) % scale, np.floor(xs).astype(int) % scale
    y1, x1 = (y0 + 1) % scale, (x0 + 1) % scale
    fy, fx = ys - np.floor(ys), xs - np.floor(xs)
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    return (g[y0, x0] * (1 - fx) + g[y0, x1] * fx) * (1 - fy) + (g[y1, x0] * (1 - fx) + g[y1, x1] * fx) * fy


def quant(field, cols, dither=0.55):
    """Map a 0..1 field onto a colour ramp with ordered dithering."""
    ramp = np.array([hexc(c) for c in cols], float)
    n = len(ramp)
    f = np.clip(field, 0, 1) * (n - 1) + (BAYER[YY % 4, XX % 4] - 0.5) * dither
    idx = np.clip(np.round(f).astype(int), 0, n - 1)
    return ramp[idx].astype(np.uint8)


def save(name, rgb, alpha=None):
    os.makedirs(OUT, exist_ok=True)
    if alpha is None:
        Image.fromarray(rgb.astype(np.uint8), "RGB").save(os.path.join(OUT, name + ".png"))
    else:
        a = np.where(alpha, 255, 0).astype(np.uint8)
        Image.fromarray(np.dstack([rgb.astype(np.uint8), a]), "RGBA").save(os.path.join(OUT, name + ".png"))


MUSTARD = ["#3a2a0c", "#6b4a12", "#a47a1c", "#d0a22c", "#f0cc58"]
BROWN = ["#1e1410", "#3a2a22", "#5a4436", "#7d6450", "#a08468"]
RED = ["#2a0c0a", "#561a12", "#8a2e18", "#b84a24", "#e07a3c"]
CREAM = ["#5a4a3a", "#8a7658", "#b8a07a", "#d8c8a0", "#f0e6c4"]
COPPER = ["#3a1a0a", "#74371a", "#b0612c", "#dc8c42", "#ffc070"]
WOOD = ["#1a0f0a", "#33201a", "#54362a", "#7a5036", "#a47448"]
BLUE = ["#0a1030", "#142266", "#2438b0", "#3c64ff", "#80a8ff"]
STREET = ["#141a24", "#26303e", "#3c4a5e", "#5e7088", "#90a4c0"]  # round 2: a step lighter (the rain street read as one dark grey)


def blocks(seed, bw=64, bh=32, cols=BROWN, mortar=0.18):
    r = np.random.default_rng(seed)
    row = YY // bh
    off = (row % 2) * (bw // 2)
    cx = (XX + off) // bw
    tone = r.random((S // bh + 1, S // bw + 2))[row % (S // bh), cx % (S // bw)]
    lx, ly = (XX + off) % bw, YY % bh
    edge = (lx < 2) | (ly < 2)
    shade = (ly / bh) * 0.25
    f = 0.30 + tone * 0.4 + noise(16, seed) * 0.25 - shade * 0.4
    f = np.where(edge, mortar, f)
    f = np.where((lx >= bw - 2) | (ly >= bh - 1), f * 0.8, f)
    return quant(f, cols)


def tufted(seed, cols=MUSTARD, cell=32):
    lx, ly = XX % cell - cell / 2 + 0.5, YY % cell - cell / 2 + 0.5
    d = np.abs(lx) + np.abs(ly)
    pillow = 1 - np.clip(d / (cell * 0.62), 0, 1)
    seam = (np.abs(np.abs(lx) + np.abs(ly) - cell * 0.5) < 1.2)
    # the diamond lattice: pillows are the cells centred on the lattice's corners, so shift by half a cell
    lx2, ly2 = (XX + cell // 2) % cell - cell / 2 + 0.5, (YY + cell // 2) % cell - cell / 2 + 0.5
    d2 = np.abs(lx2) + np.abs(ly2)
    pillow = 1 - np.clip(d2 / (cell * 0.5), 0, 1)
    f = 0.22 + pillow * 0.55 + noise(32, seed) * 0.18 + (-ly2 / cell) * 0.12
    f = np.where(np.abs(d2 - cell * 0.5) < 1.1, 0.08, f)
    out = quant(f, cols)
    btn = (lx * lx + ly * ly) < 2.6  # a button at each lattice crossing
    out[btn] = hexc(cols[0])
    return out


OXBLOOD = ["#12040a", "#2c0a12", "#4a1420", "#6c1e2a", "#94303a"]  # stage D: the painting's curtains are deep oxblood velvet in shadow (the first pass read orange)


def curtain(seed, cols=OXBLOOD):
    f = 0.5 + 0.38 * np.sin(XX / S * 2 * math.pi * 8 + noise(8, seed) * 2.0) + (noise(24, seed + 1) - 0.5) * 0.2
    f = f * (0.8 + 0.2 * (1 - YY / S))
    return quant(f * 0.9, cols)


def planks(seed, cols=WOOD, h=16, horizontal=True):
    c = YY if horizontal else XX
    a = XX if horizontal else YY
    plank = c // h
    r = np.random.default_rng(seed).random(S // h + 1)
    grain = noise(32, seed + 3)
    f = 0.25 + r[plank % (S // h)] * 0.35 + grain * 0.3 + 0.1 * np.sin(a / S * 2 * math.pi * 3 + plank)
    f = np.where(c % h == 0, 0.08, f)
    return quant(f, cols)


def tiles(seed, ca, cb, tile=32, gloss=True):
    chk = ((XX // tile) + (YY // tile)) % 2
    f = np.where(chk == 0, 0.30, 0.52) + noise(16, seed) * 0.22 + (noise(48, seed + 5) - 0.5) * 0.10
    vein = np.abs(np.sin((XX + YY * 0.6) / S * 2 * math.pi * 3 + noise(6, seed + 2) * 6)) < 0.05
    f = np.where(vein, f + 0.22, f)
    f = np.where((XX % tile == 0) | (YY % tile == 0), 0.1, f)
    if gloss:
        f = f + 0.18 * np.exp(-(((XX % tile) - tile * 0.28) ** 2 + ((YY % tile) - tile * 0.28) ** 2) / 90.0)
    out = quant(f, ca)
    sel = chk == 1
    out[sel] = quant(f, cb)[sel]
    return out


def weave(seed, cols):
    f = 0.4 + noise(64, seed) * 0.35 + 0.15 * (((XX % 4 < 2) ^ (YY % 4 < 2)).astype(float)) + (noise(8, seed + 1) - 0.5) * 0.2
    return quant(f, cols, 0.7)


def copper_tiles(seed):
    cell = 16
    lx, ly = XX % cell, YY % cell
    f = 0.35 + noise(16, seed) * 0.3 + 0.3 * (1 - ly / cell) * (1 - lx / cell)
    f = np.where((lx == 0) | (ly == 0), 0.06, f)
    f = np.where((lx == 1) | (ly == 1), f + 0.2, f)
    return quant(f, COPPER, 0.4)


def beam_ceiling(seed):
    f = 0.35 + noise(24, seed) * 0.25
    bw = (XX % 64 < 8) | (YY % 64 < 8)
    f = np.where(bw, 0.62 + noise(40, seed + 1) * 0.2, f)
    f = np.where(((XX % 64 == 8) | (YY % 64 == 8)) & bw, 0.1, f)
    out = quant(f, WOOD)
    gold = ((XX % 64 == 3) | (YY % 64 == 3)) & bw  # a gold inlay line down each beam
    out[gold] = hexc("#d6a23a")
    return out


def street(seed, wall=False):
    if wall:
        f = 0.2 + noise(32, seed) * 0.35 + 0.12 * np.sin(XX / S * 2 * math.pi * 4)
        f = np.where(XX % 64 < 2, 0.06, f)
        f = np.where((YY % 48 < 2), f * 0.5, f)
        pipe = (XX > 96) & (XX < 104)
        f = np.where(pipe, 0.55 + 0.25 * np.sin(YY / 4.0), f)
        out = quant(f, STREET)
        return out
    f = 0.2 + noise(24, seed) * 0.3
    puddle = noise(5, seed + 7) > 0.58
    f = np.where(puddle, 0.55 + noise(64, seed + 2) * 0.2, f)
    f = np.where((XX % 64 < 2) | (YY % 64 < 2), 0.08, f)
    return quant(f, STREET)


def blue_deck(seed, wall=False):
    deep = ["#03040c", "#060a1e", "#0c1640", "#16287a", "#2a4cd0", "#7aa0ff"]
    if wall:  # round 2: DARK cobalt glass (the lead: the stage-D tile still read as a bright striped box): near-black panes, one thin diagonal streak, the LED strip at the foot
        f = 0.40 + noise(12, seed) * 0.14
        glass = (XX % 64 > 2) & (YY % 128 > 2)
        streak = (np.abs(((XX + YY // 5) % 128) - 70) < 2) & glass
        f = np.where(glass, f + 0.10 * (1 - (YY % 128) / 128.0), 0.02)
        f = np.where(streak, f + 0.40, f)
        f = np.where((YY % 128 > 122) & (YY % 128 < 125), 0.92, f)  # the LED strip along the foot
        lights = (noise(32, seed + 5) > 0.72) & (XX % 6 < 3) & (YY % 8 < 3) & glass  # the city's lit windows beyond the glass, as the painting's passage shows
        f = np.where(lights, 0.9, f)
        return quant(f, deep)
    f = 0.30 + noise(24, seed) * 0.16  # round 2: a dark wet deck, the LED strip's reflection a thin line
    f = np.where((XX % 64 < 2) | (YY % 64 < 2), 0.04, f)
    f = np.where((YY % 128 > 62) & (YY % 128 < 64), 0.8, f)
    return quant(f, deep)


def marble_wall(seed):
    return blocks(seed, 128, 64, BROWN, 0.12)


# --- sprites (RGBA) ----------------------------------------------------------------------------------------------------------------------------------------------------

def blank(w=S, h=S):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def shaded_ellipse(img, box, cols, light=(-0.5, -0.6)):
    w, h = int(box[2] - box[0]), int(box[3] - box[1])
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([0, 0, w - 1, h - 1], fill=255)
    a = np.array(m) > 127
    yy, xx = np.mgrid[0:h, 0:w]
    nx, ny = (xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)
    v = 0.55 - (nx * light[0] + ny * light[1]) * 0.45
    ramp = np.array([hexc(c) for c in cols], float)
    idx = np.clip(np.round((v + (BAYER[yy % 4, xx % 4] - 0.5) * 0.4) * (len(cols) - 1)).astype(int), 0, len(cols) - 1)
    rgb = ramp[idx].astype(np.uint8)
    layer = np.dstack([rgb, np.where(a, 255, 0).astype(np.uint8)])
    img.alpha_composite(Image.fromarray(layer, "RGBA"), (int(box[0]), int(box[1])))


def outline(img, col="#120a08"):
    a = np.array(img)[..., 3] > 0
    grown = np.array(Image.fromarray((a * 255).astype(np.uint8)).filter(__import__("PIL.ImageFilter", fromlist=["MaxFilter"]).MaxFilter(3))) > 127
    ring = grown & ~a
    arr = np.array(img)
    arr[ring] = (*hexc(col), 255)
    return Image.fromarray(arr, "RGBA")


def plant():
    w, h = 128, 192
    img = blank(w, h)
    d = ImageDraw.Draw(img)
    # the pot: a copper urn
    pot = Image.new("RGBA", (64, 56), (0, 0, 0, 0))
    pm = Image.new("L", (64, 56), 0)
    ImageDraw.Draw(pm).polygon([(6, 0), (58, 0), (62, 14), (54, 52), (10, 52), (2, 14)], fill=255)
    a = np.array(pm) > 127
    yy, xx = np.mgrid[0:56, 0:64]
    v = 0.4 + 0.45 * np.exp(-((xx - 22) ** 2) / 120.0) + 0.1 * np.sin(yy / 3.0) - 0.2 * (xx / 64.0)
    ramp = np.array([hexc(c) for c in COPPER], float)
    idx = np.clip(np.round((v + (BAYER[yy % 4, xx % 4] - 0.5) * 0.3) * 4).astype(int), 0, 4)
    pot = Image.fromarray(np.dstack([ramp[idx].astype(np.uint8), np.where(a, 255, 0).astype(np.uint8)]), "RGBA")
    img.alpha_composite(pot, (32, 136))
    d.rectangle([30, 134, 96, 140], fill=hexc("#dc8c42"))
    # the fronds: dark-to-light green leaves fanning out
    greens = ["#0c2410", "#17401a", "#2a6a24", "#4e9a2e", "#8cc84a"]
    r = np.random.default_rng(4)
    for k in range(13):
        ang = math.radians(-75 + k * 12.5 + r.uniform(-4, 4))
        ln = r.uniform(70, 112)
        bx, by = 64, 138
        pts = []
        for t in np.linspace(0, 1, 14):
            x = bx + math.sin(ang) * ln * t + math.sin(ang) * 0.0
            y = by - math.cos(ang) * ln * t * 0.9 + (t ** 2) * ln * 0.32 * abs(math.sin(ang))
            pts.append((x, y))
        wid = 11
        poly = []
        for i, (x, y) in enumerate(pts):
            ww = wid * math.sin(math.pi * min(1.0, (i + 1) / len(pts))) + 1
            poly.append((x - ww, y))
        for i, (x, y) in reversed(list(enumerate(pts))):
            ww = wid * math.sin(math.pi * min(1.0, (i + 1) / len(pts))) + 1
            poly.append((x + ww, y))
        lm = Image.new("L", (w, h), 0)
        ImageDraw.Draw(lm).polygon(poly, fill=255)
        la = np.array(lm) > 127
        yy, xx = np.mgrid[0:h, 0:w]
        v = 0.25 + 0.5 * (k % 3) / 2.0 + 0.2 * np.sin((xx + yy) / 5.0) * 0.4 + 0.2 * (1 - yy / h)
        ramp = np.array([hexc(c) for c in greens], float)
        idx = np.clip(np.round((v + (BAYER[yy % 4, xx % 4] - 0.5) * 0.35) * 4).astype(int), 0, 4)
        layer = np.dstack([ramp[idx].astype(np.uint8), np.where(la, 255, 0).astype(np.uint8)])
        img.alpha_composite(Image.fromarray(layer, "RGBA"))
        ImageDraw.Draw(img).line(pts, fill=hexc("#8cc84a"), width=1)
    return outline(img)


def lamp():
    w = h = 64
    img = blank(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([28, 44, 36, 56], fill=hexc("#b0612c"))  # the stem
    d.ellipse([18, 52, 46, 62], fill=hexc("#dc8c42"))  # the base
    shaded_ellipse(img, (6, 14, 58, 52), ["#8a3a10", "#d86a1a", "#ffa030", "#ffd070", "#fff0b0"], light=(0, 0.3))
    img = img.copy()
    arr = np.array(img)
    arr[40:52, :, 3] = np.where(np.arange(w)[None, :] < 0, 0, arr[40:52, :, 3])
    return outline(Image.fromarray(arr, "RGBA"), "#2a1004")


def vase():
    w = h = 64
    img = blank(w, h)
    d = ImageDraw.Draw(img)
    r = np.random.default_rng(2)
    for k in range(18):  # red and orange sprays
        a = math.radians(-60 + k * 7 + r.uniform(-4, 4))
        ln = r.uniform(26, 44)
        x, y = 32 + math.sin(a) * ln, 34 - math.cos(a) * ln
        d.line([(32, 36), (x, y)], fill=hexc("#3a5a1a"), width=1)
        for j in range(3):
            d.ellipse([x - 2 + r.uniform(-3, 3), y - 2 + r.uniform(-3, 3), x + 2, y + 2], fill=hexc(["#e8501c", "#ff8a2c", "#c02c14"][j % 3]))
    d.polygon([(24, 38), (40, 38), (44, 60), (20, 60)], fill=hexc("#8a8a90"))
    d.polygon([(26, 38), (30, 38), (28, 60), (22, 60)], fill=hexc("#c8c8d0"))
    return outline(img)


def cushion(a_, b_, c_):
    w = h = 64
    img = blank(w, h)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 8, 60, 56], radius=10, fill=hexc(a_))
    for k in range(4):  # a block pattern
        d.rectangle([8 + k * 12, 14 + (k % 2) * 8, 16 + k * 12, 24 + (k % 2) * 8], fill=hexc(b_))
        d.ellipse([10 + k * 11, 34 + (k % 2) * 4, 22 + k * 11, 46 + (k % 2) * 4], fill=hexc(c_))
    d.rounded_rectangle([4, 8, 60, 56], radius=10, outline=hexc("#3a1808"), width=2)
    d.line([(8, 12), (50, 10)], fill=hexc("#fff0c0"), width=1)
    return img


# --- decals --------------------------------------------------------------------------------------------------------------------------------------------------------

def studs():
    """A gold pyramid-studded acoustic panel in a dark frame (96 x 128, taller than wide)."""
    w, h = 96, 128
    img = np.zeros((h, w, 3), np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    cell = 16
    lx, ly = xx % cell, yy % cell
    # a pyramid: four faces lit from the top left
    top = (ly < lx) & (ly < cell - lx)
    left = (lx < ly) & (lx < cell - ly)
    right = (lx > ly) & (lx > cell - ly)
    cols = {"top": hexc("#f0c850"), "left": hexc("#c89030"), "right": hexc("#7a5416"), "bottom": hexc("#5a3a0c")}
    img[:] = cols["bottom"]
    img[top] = cols["top"]
    img[left] = cols["left"]
    img[right] = cols["right"]
    img[(lx == 0) | (ly == 0)] = hexc("#3a2406")
    frame = (xx < 4) | (xx >= w - 4) | (yy < 4) | (yy >= h - 4)
    img[frame] = hexc("#2a1a0e")
    img[(xx == 4) | (yy == 4)] = hexc("#6a4a2a")
    return img, np.ones((h, w), bool)


def vinyl():
    w = h = 96
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot(xx - w / 2 + 0.5, yy - h / 2 + 0.5)
    img = np.zeros((h, w, 3), np.uint8)
    img[:] = hexc("#2a1a10")
    rec = r < 44
    groove = 0.5 + 0.5 * np.sin(r * 1.8)
    img[rec] = np.where(groove[..., None] > 0.5, hexc("#17171f"), hexc("#0c0c12")).astype(np.uint8)[rec]
    label = r < 15
    img[label] = hexc("#d8782c")
    img[r < 3] = hexc("#2a1a10")
    img[(r >= 15) & (r < 16)] = hexc("#8a4a14")
    # a lit highlight arc
    arc = (np.abs(r - 30) < 2.5) & (xx < w / 2) & (yy < h / 2)
    img[arc] = hexc("#6a6a88")
    frame = (xx < 3) | (xx >= w - 3) | (yy < 3) | (yy >= h - 3)
    img[frame] = hexc("#6a4a2a")
    return img, np.ones((h, w), bool)


def sconce():
    """A brass wall lamp with a glowing amber globe (64 x 96, emissive)."""
    w, h = 64, 96
    img = blank(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([26, 56, 38, 94], fill=hexc("#a07028"))
    d.rectangle([28, 56, 31, 94], fill=hexc("#d8a848"))
    d.rectangle([20, 70, 44, 76], fill=hexc("#c89030"))
    shaded_ellipse(img, (8, 4, 56, 56), ["#a84a10", "#e88a20", "#ffb840", "#ffd878", "#fff4c8"], light=(0, 0.2))
    d = ImageDraw.Draw(img)
    for k in range(3):  # the globe's facets
        d.arc([8 + k * 6, 4, 56 - k * 6, 56], 90, 270, fill=hexc("#d87a18"))
    return outline(img, "#2a1004"), None


def bottles():
    """A lit shelf of bottles and a few records (128 x 96)."""
    w, h = 128, 96
    img = blank(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w - 1, h - 1], fill=hexc("#2a1a10"))
    r = np.random.default_rng(6)
    for row in range(3):
        y = 28 + row * 30
        d.rectangle([2, y, w - 3, y + 3], fill=hexc("#8a6030"))
        x = 6
        while x < w - 14:
            bh = int(r.integers(14, 24))
            bw = int(r.integers(5, 9))
            col = ["#8a3a10", "#c8861e", "#2a6a3a", "#e0b04a", "#7a2a2a"][int(r.integers(0, 5))]
            d.rectangle([x, y - bh, x + bw, y - 1], fill=hexc(col))
            d.rectangle([x + 1, y - bh, x + 2, y - 1], fill=hexc("#fff0c0"))
            d.rectangle([x + bw // 2 - 1, y - bh - 4, x + bw // 2 + 1, y - bh], fill=hexc(col))
            x += bw + int(r.integers(3, 6))
    d.rectangle([0, 0, w - 1, h - 1], outline=hexc("#6a4a2a"), width=2)
    return img, None


def beads():
    """A bead curtain: strands of amber beads on dark (64 x 128)."""
    w, h = 64, 128
    img = blank(w, h)
    d = ImageDraw.Draw(img)
    r = np.random.default_rng(9)
    for x in range(3, w, 8):
        for y in range(2, h, 5):
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=hexc(["#e8a030", "#c06820", "#ffd070", "#8a4a18"][int(r.integers(0, 4))]))
        d.line([(x, 0), (x, h)], fill=hexc("#5a3a14"))
    return img, None


def coffer_panel():
    """Round 2: the painting's warm coffered panelling (it replaces the gold studded panels, which read as gold cubes): a dark timber frame, two columns of four sunk coffers,
    each with a lit upper-left bevel, a shadowed lower-right one and a gold bead round its field; 96 x 192, lit from above."""
    w, h = 96, 192
    yy, xx = np.mgrid[0:h, 0:w]
    v = 0.42 + (np.random.default_rng(41).random((h, w)) - 0.5) * 0.08 - 0.15 * (yy / h)
    cols = ["#140a06", "#2a160c", "#462614", "#6a3c1e", "#90562a", "#c08040", "#f0c060"]
    for cx in (8, 50):
        for cy in range(8, h - 8, 46):
            lx, ly = xx - cx, yy - cy
            box = (lx >= 0) & (lx < 38) & (ly >= 0) & (ly < 40)
            bev = np.minimum(np.minimum(lx, ly), np.minimum(37 - lx, 39 - ly))
            v = np.where(box & (bev < 5) & ((lx < 5) | (ly < 5)) & (lx < 38 - ly * 0.95), 0.66, v)
            v = np.where(box & (bev < 5) & ((lx >= 33) | (ly >= 35)) & ~((lx < 5) | (ly < 5)), 0.18, v)
            field = box & (bev >= 5)
            v = np.where(field, 0.3 + 0.12 * (1 - ly / 40.0), v)
            v = np.where(box & (bev == 5), 0.9, v)  # the gold bead
    f = np.clip(v, 0, 1) * (len(cols) - 1) + (BAYER[yy % 4, xx % 4] - 0.5) * 0.55
    ramp = np.array([hexc(c) for c in cols], np.uint8)
    img = ramp[np.clip(np.round(f).astype(int), 0, len(cols) - 1)]
    return img, np.ones((h, w), bool)


def coffer_frieze():
    """Round 2: the frieze of coffers under the vault, over each face of the octagon (the painting's warm panelling above the arches): 640 x 128, five coffers between
    two gold-edged beams."""
    one, _ = coffer_panel()
    tile = one[8:54, 8:88]  # a row of two coffers from the panel
    w, h = 640, 128
    img = np.zeros((h, w, 3), np.uint8)
    row = np.concatenate([tile] * (w // tile.shape[1] + 1), axis=1)[:, :w]
    big = np.array(Image.fromarray(row).resize((w, 92), Image.NEAREST))
    img[18:110] = big
    yy, xx = np.mgrid[0:h, 0:w]
    beam = (yy < 18) | (yy >= 110)
    bv = 0.5 + 0.3 * (1 - np.abs((yy % 110) - 9) / 9.0)
    ramp = np.array([hexc(c) for c in ["#1a0e08", "#33200f", "#543418", "#7a4e24", "#a06a34"]], np.uint8)
    bi = ramp[np.clip(np.round(np.clip(bv, 0, 1) * 4 + (BAYER[yy % 4, xx % 4] - 0.5) * 0.6).astype(int), 0, 4)]
    img[beam] = bi[beam]
    img[(yy == 17) | (yy == 110)] = hexc("#e0b04a")
    return img, np.ones((h, w), bool)


def pilaster():
    """Round 2: a carved stone pilaster with a brass capital and base (the painting's columns between the arches): 64 x 448, a flat decal on each corner of the octagon."""
    w, h = 64, 448
    yy, xx = np.mgrid[0:h, 0:w]
    v = 0.45 + 0.25 * np.cos((xx - 22) / 64.0 * np.pi) + (np.random.default_rng(43).random((h, w)) - 0.5) * 0.1
    v = np.where((xx % 16) < 2, v - 0.25, v)  # flutes
    cols = ["#140e0a", "#2a2018", "#463626", "#62503a", "#82684c", "#a88a66"]
    ramp = np.array([hexc(c) for c in cols], np.uint8)
    img = ramp[np.clip(np.round(np.clip(v, 0, 1) * 5 + (BAYER[yy % 4, xx % 4] - 0.5) * 0.6).astype(int), 0, 5)]
    brass = ["#3a2406", "#7a5416", "#c89030", "#f0c850", "#fff0a0"]
    br = np.array([hexc(c) for c in brass], np.uint8)
    for y0, y1 in ((0, 36), (h - 28, h)):
        bv = 0.4 + 0.5 * (1 - np.abs(yy - (y0 + y1) / 2.0) / ((y1 - y0) / 2.0)) * np.cos((xx - 22) / 64.0 * np.pi)
        bi = br[np.clip(np.round(np.clip(bv, 0, 1) * 4 + (BAYER[yy % 4, xx % 4] - 0.5) * 0.6).astype(int), 0, 4)]
        m = (yy >= y0) & (yy < y1)
        img[m] = bi[m]
    return img, np.ones((h, w), bool)


def polish():
    """Stage D polish (docs/briefs/DOOM_POLISH_BRIEF.md): the main surfaces redrawn at 256 px for the renderer's 2 m repeat (128 texels per metre) and toward the painting:
    warm carved stone in three variants (wall_stone, _b, _c: one per piece, so no wall repeats one tile), polished marble with veins and the lamps' gloss baked in, the rug
    in the painting's oxblood and rust with cream stripes (the first pass read orange), a coffered timber ceiling with gold inlay drawn coarse (it is seen at grazing angles).
    Foreground pieces CUT from the painting (alpha 0/255, nearest-neighbour): the near sofa with its patterned cushion and the two palms at the frame's edges."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import make_warehouse_art as wa
    N = wa.N
    yy, xx = np.mgrid[0:N, 0:N]
    STONE = ["#1a120e", "#2e221a", "#463426", "#5e4834", "#7a5e44", "#987858"]
    out = {"wall_stone": wa.tile_brick_wall(301, STONE, "#120c08", bh=32, bw=96), "wall_stone_b": wa.tile_brick_wall(302, STONE, "#120c08", bh=32, bw=80),
           "wall_stone_c": wa.tile_brick_wall(303, STONE, "#120c08", bh=64, bw=112)}
    v = 0.45 + (wa.noise(N, N, 304, 32, 3) - 0.5) * 0.3
    vein = np.abs(np.sin((xx + yy * 0.7) / 23.0 + wa.noise(N, N, 305, 64, 2) * 7)) < 0.06
    v[vein] += 0.18
    v[(xx % 128 < 2) | (yy % 128 < 2)] = 0.08
    img = wa.ramp(np.clip(v, 0, 1), ["#1a1410", "#2e241c", "#4a3a2c", "#6a5440", "#8e7458", "#b49a78"], 0.8)
    out["floor_marble"] = wa.sheen(img, wa.noise(N, N, 306, 32, 2), ["#8a6a48", "#d0a46a"], 0.74)
    def pile(seed, cols):
        f = 0.45 + (wa.noise(N, N, seed, 2, 2) - 0.5) * 0.5 + (wa.noise(N, N, seed + 1, 32, 2) - 0.5) * 0.25
        return wa.ramp(np.clip(f, 0, 1), cols, 1.0)
    out["floor_rug_red"] = pile(307, ["#1c0606", "#3a0c0a", "#5e1810", "#822a18", "#a24020"])
    out["floor_rug_orange"] = pile(309, ["#2a0a06", "#4e160c", "#743012", "#9a4a1c", "#bc6428"])
    out["floor_rug_cream"] = pile(311, ["#4a3a2a", "#7a6448", "#a8906a", "#cbb690", "#e6d6b0"])
    v = 0.3 + (wa.noise(N, N, 313, 8) - 0.5) * 0.2
    img = wa.ramp(v, ["#0e0806", "#1e120c", "#301e14", "#46301e"], 0.7)
    beam = ((xx % 128) < 28) | ((yy % 128) < 28)
    bv = 0.45 + 0.3 * (1 - np.minimum(xx % 128, yy % 128) / 28.0) + (wa.noise(N, N, 314, 4) - 0.5) * 0.2
    bim = wa.ramp(np.clip(bv, 0, 1), ["#1a0e08", "#33200f", "#543418", "#7a4e24", "#a06a34"], 0.8)
    img[beam] = bim[beam]
    inlay = (((xx % 128) == 30) | ((yy % 128) == 30)) & ~beam
    img[inlay] = hexc("#e0b04a")
    out["ceil_beam"] = img
    for k, a in out.items():
        save(k, a)
    paint = os.path.join(ROOT, "art", "reference", "doom_worlds", "Mustard octagonal lounge of three routes-2.png")
    cuts = {
        "lg_p_sofa": ((30, 684, 1450, 941), [(35, 830), (60, 760), (111, 700), (311, 688), (367, 738), (544, 793), (567, 843), (667, 825), (833, 836), (1111, 841), (1333, 825),
                                              (1445, 840), (1445, 941), (33, 941)]),
        "lg_p_palm_l": ((0, 470, 270, 735), [(0, 480), (120, 470), (220, 520), (268, 600), (262, 700), (200, 735), (0, 735)]),
        "lg_p_palm_r": ((1330, 580, 1672, 941), [(1600, 580), (1672, 585), (1672, 941), (1520, 941), (1400, 880), (1332, 760), (1420, 650)]),
    }
    Image.fromarray(wa.spr_halo(), "RGBA").save(os.path.join(OUT, "lg_halo.png"))  # round 2: the sconces' and lamps' glow (additive), the Warehouse's halo
    for k, (box, poly) in cuts.items():
        rgb, al = wa.cut(box, poly, paint=paint)
        if k.startswith("lg_p_palm"):  # a palm: only its leaves and pot, not the room behind (the room is darker and less green than the leaves)
            r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
            al &= (g > r * 0.85) | ((r + g + b) < 60)
        save(k, rgb, al)


def main():
    os.makedirs(OUT, exist_ok=True)
    tex = {}
    tex["wall_stone"] = blocks(1, 64, 32, BROWN)
    tex["wall_marble"] = marble_wall(2)
    tex["wall_sofa"] = tufted(3)
    tex["wall_curtain"] = curtain(4)
    tex["wall_wood"] = planks(5, WOOD, 16, False)
    tex["wall_copper"] = copper_tiles(6)
    tex["wall_table"] = planks(7, WOOD, 32, True)
    tex["wall_street"] = street(8, True)
    tex["wall_blue"] = blue_deck(9, True)
    tex["wall_beam"] = beam_ceiling(10)
    tex["floor_marble"] = tiles(11, ["#1e1612", "#3a2a22", "#5e4a3a", "#8a7058", "#b8a080"], ["#2a1c14", "#4c3426", "#7a5a40", "#a88a66", "#d8c298"])
    tex["floor_rug_red"] = weave(12, RED)
    tex["floor_rug_cream"] = weave(13, CREAM)
    tex["floor_rug_orange"] = weave(14, ["#4a1a08", "#8a3410", "#c85a1c", "#f08a30", "#ffb860"])
    tex["floor_sofa"] = tufted(15, MUSTARD, 64)
    tex["floor_table"] = planks(16, ["#2a160e", "#4a2a1a", "#74442a", "#a06a3c", "#d09a58"], 64, True)
    tex["floor_wood"] = planks(17, WOOD, 16, True)
    tex["floor_street"] = street(18)
    tex["floor_blue"] = blue_deck(19)
    tex["floor_curtain"] = weave(20, RED)
    tex["ceil_beam"] = beam_ceiling(21)
    tex["ceil_street"] = street(22, True)
    for k, v in tex.items():
        save(k, v)
    sp = {"thing_plant": plant(), "thing_lamp": lamp(), "thing_vase": vase(), "thing_cushion": cushion("#c85a2c", "#8a2a14", "#e8b860"), "thing_cushion_b": cushion("#7a3a28", "#c8861e", "#3a5a4a")}
    for k, im in sp.items():
        im.save(os.path.join(OUT, k + ".png"))
    polish()
    for k, (rgb, alpha) in {"deco_studs": studs(), "deco_vinyl": vinyl(), "deco_coffer": coffer_panel(), "deco_frieze": coffer_frieze(), "deco_pilaster": pilaster()}.items():
        save(k, rgb)
    for k, fn in (("deco_sconce", sconce), ("deco_bottles", bottles), ("deco_beads", beads)):
        im, _a = fn()
        im.save(os.path.join(OUT, k + ".png"))
    # the contact sheet
    names = sorted(f[:-4] for f in os.listdir(OUT) if f.endswith(".png"))
    cols = 6
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 136, rows * 152), (24, 20, 30))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        im = Image.open(os.path.join(OUT, n + ".png")).convert("RGBA")
        im.thumbnail((128, 128), Image.NEAREST)
        bg = Image.new("RGBA", im.size, (60, 56, 70, 255))
        bg.alpha_composite(im)
        x, y = (i % cols) * 136 + 4, (i // cols) * 152 + 4
        sheet.paste(bg.convert("RGB"), (x, y + 14))
        d.text((x, y), n, fill=(230, 230, 240))
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    sheet.save(SHEET)
    print("wrote %d textures and sprites to %s and %s" % (len(names), OUT, SHEET))


if __name__ == "__main__":
    sys.exit(main())
