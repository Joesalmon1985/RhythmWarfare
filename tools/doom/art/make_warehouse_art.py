"""The Warehouse's own art (docs/doom/scenes/warehouse.md, stage D polish): surfaces drawn in code toward the painting
(`art/reference/doom_worlds/Cobalt Warehouse Dance Floor-1.png`) and props cut from it.

    python -I tools/doom/art/make_warehouse_art.py      writes assets/story/doom_warehouse/textures/wh_*.png and docs/shots/doom/warehouse/art_sheet.png

Tiles are 256 px for the renderer's 2 m repeat (128 texels per metre, the style guide's density): wet steel walkway with cobalt reflections and puddle gloss baked in, a
drain grating, the dance floor's LED dots under a wet sheen, riveted steel and brick walls in three variants each (so no wall repeats one tile), the bar's warm brick and the
lounge's velvet, a truss-and-glazing roof, the speaker plinths' faces and the lit cube. Every ramp is ordered-dithered; highlights are dithered, never flat.
Props (`wh_p_*`) are CUT from the painting (rectangles or a traced polygon, nearest-neighbour, alpha 0/255): the treble-clef banner, the hanging speaker, the bar's back shelf,
its counter and copper lamp, the stage's window onto the night city (the guide painted out), the lounge's lamp and pelmet; the rest are drawn: spotlight beams (additive),
the flight case, the sofa, the plant. The railing tile (`wh_railing`, 128 px, 1 m, alpha) is the painting's riveted steel half-wall with a copper top rail.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_bar_art import BAYER, hexc, ramp  # noqa: E402  (the shared pixel-painting primitives)


def noise(h, w, seed, cell=4, octaves=3):
    """Value noise, smooth (bicubic between the lattice values, tileable by wrapping): blobs, not the squares of a nearest upsample."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = max(1, cell // (2 ** o))
        gh, gw = max(1, h // c), max(1, w // c)
        g = rng.random((gh, gw))
        g3 = np.tile(g, (3, 3))
        big = np.array(Image.fromarray((g3 * 255).astype(np.uint8)).resize((gw * 3 * c, gh * 3 * c), Image.BICUBIC)).astype(float) / 255.0
        out += big[gh * c:gh * c + h, gw * c:gw * c + w] * amp
        tot += amp
        amp *= 0.5
    return out / tot

ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "assets", "story", "doom_warehouse", "textures")
SHEET = os.path.join(ROOT, "docs", "shots", "doom", "warehouse", "art_sheet.png")
PAINT = os.path.join(ROOT, "art", "reference", "doom_worlds", "Cobalt Warehouse Dance Floor-1.png")
N = 256

STEEL = ["#0b0d1c", "#151a33", "#212a4d", "#2e3b6a", "#41548c", "#5f78b4", "#8aa4dc"]
COBALT = ["#060a24", "#0c1650", "#16258a", "#2440c8", "#3f66f0", "#7fa0ff", "#c8d8ff"]
BRICK_C = ["#100c18", "#1e1626", "#2e2234", "#423040", "#5a404c", "#74545a"]
WARM_BRICK = ["#140a08", "#2a140e", "#462216", "#64321c", "#864826", "#a86236"]
COPPER = ["#2a1208", "#5a2a12", "#8f4a1c", "#c47a34", "#e6a455", "#ffd58a"]
VELVET = ["#12040a", "#2a0a14", "#46101e", "#621a28", "#842838", "#a83e46"]


def save(name, arr, alpha=None):
    os.makedirs(OUT, exist_ok=True)
    if alpha is None:
        im = Image.fromarray(arr.astype(np.uint8), "RGB")
    else:
        im = Image.fromarray(np.dstack([arr.astype(np.uint8), (np.asarray(alpha) > 0.5).astype(np.uint8) * 255]), "RGBA")
    im.save(os.path.join(OUT, name + ".png"))
    return im


def grid():
    return np.mgrid[0:N, 0:N]


def sheen(img, wet, cols, thresh=0.62, seed=0):
    """Wet gloss baked in: where the wet mask is high the surface takes the reflected light (cols: dim, bright) through the ordered dither."""
    yy, xx = grid()
    d = BAYER[yy % 4, xx % 4]
    a = (wet > thresh) & (d < (wet - thresh) * 3.0)
    img[a] = hexc(cols[0])
    b = (wet > thresh + 0.12) & (d < (wet - thresh - 0.12) * 3.0)
    img[b] = hexc(cols[1])
    return img


# --- floors ------------------------------------------------------------------------------------------------------------------------------------------------------------

def tile_walk():
    """The steel-plated walkway: 1 m plates with seams and rivets, a diamond tread, wet: cobalt reflections streaked toward the floor and puddle gloss."""
    yy, xx = grid()
    v = 0.36 + (noise(N, N, 3, 16) - 0.5) * 0.25 + (noise(N, N, 4, 3) - 0.5) * 0.12
    tread = ((xx + yy) % 12 < 2) | ((xx - yy) % 12 < 2)
    v += np.where(tread, 0.07, 0.0)
    seam = (xx % 128 < 2) | (yy % 128 < 2)
    v[seam] = 0.08
    v[(xx % 128 == 2) | (yy % 128 == 2)] += 0.12
    img = ramp(v, STEEL, 1.0)
    for px in (8, 64, 120):
        for py in (8, 64, 120):
            for ox in (0, 128):
                for oy in (0, 128):
                    x, y = px + ox, py + oy
                    img[y - 1:y + 2, x - 1:x + 2] = hexc("#1a2140")
                    img[y - 1, x - 1] = hexc("#7d93cc")
    wet = noise(N, N, 7, 32, 2) * 0.7 + noise(N, N, 8, 8, 2) * 0.3
    streak = (np.sin(xx / 5.0 + noise(N, N, 9, 16)[yy, xx] * 4) > 0.82) & (wet > 0.45)
    img[streak & (BAYER[yy % 4, xx % 4] < 0.3)] = hexc("#2a44b8")
    return sheen(img, wet, ["#2f4cc8", "#7f9cf0"], 0.66)


def tile_grate():
    """The drain grating along the fence: steel bars over dark water with a cobalt glint."""
    yy, xx = grid()
    img = np.zeros((N, N, 3), np.uint8)
    img[:] = hexc("#05081a")
    water = noise(N, N, 12, 8)
    img[(water > 0.62) & (BAYER[yy % 4, xx % 4] < 0.4)] = hexc("#1c2c80")
    bars = (xx % 16 < 6)
    cross = (yy % 64 < 6)
    shade = 0.45 + 0.35 * (1 - (xx % 16) / 6.0) + (noise(N, N, 13, 3) - 0.5) * 0.25
    metal = ramp(np.clip(shade, 0, 1), STEEL[1:], 0.8)
    m = bars | cross
    img[m] = metal[m]
    img[(xx % 16 == 0) & bars & (BAYER[yy % 4, xx % 4] < 0.6)] = hexc("#9fb6f0")
    return img


def tile_dance():
    """The dance floor: dark wet tiles with blue LED dots (the painting's glowing discs) and their pools reflected in the wet."""
    yy, xx = grid()
    v = 0.16 + (noise(N, N, 21, 16) - 0.5) * 0.18
    v[(xx % 64 < 2) | (yy % 64 < 2)] = 0.02
    img = ramp(v, COBALT[:4], 0.9)
    rng = np.random.default_rng(22)
    for cy in range(16, N, 32):
        for cx in range(16, N, 32):
            jx, jy = cx + int(rng.integers(-3, 4)), cy + int(rng.integers(-3, 4))
            b = 0.55 + rng.random() * 0.45
            d = np.hypot(xx - jx, (yy - jy) * 1.2)
            pool = (d < 11) & (BAYER[yy % 4, xx % 4] < (1 - d / 11.0) * b)
            img[pool] = hexc("#2440c8")
            img[(d < 6) & (BAYER[yy % 4, xx % 4] < b)] = hexc("#3f66f0")
            img[(d < 3.2)] = hexc("#7fa0ff")
            img[(d < 1.5)] = hexc("#c8d8ff")
    wet = noise(N, N, 23, 32, 2)
    return sheen(img, wet, ["#16258a", "#3f66f0"], 0.66)


def tile_boards(seed=31, pal=None):
    """Planks (the bar floor, the stage): grain, knots, dark gaps, a worn shine."""
    yy, xx = grid()
    rng = np.random.default_rng(seed)
    v = np.zeros((N, N))
    for c in range(8):
        base = 0.38 + rng.random() * 0.3
        g = noise(N, 32, seed + c, 3)
        for x in range(32):
            v[:, c * 32 + x] = base + 0.12 * np.sin(np.arange(N) / 7.0 + g[:, x] * 6) + (g[:, x] - 0.5) * 0.25
        v[:, c * 32] = 0.04
        cut = int(rng.integers(0, N))
        v[cut:cut + 2, c * 32:c * 32 + 32] = 0.06
    img = ramp(np.clip(v, 0, 1), pal or ["#140a08", "#2a1610", "#44261a", "#603822", "#7e4c2c", "#a06a40"], 0.9)
    return sheen(img, noise(N, N, seed + 50, 32, 2), ["#8a5a34", "#d09a5a"], 0.68)


def tile_carpet():
    """The lounge rug: oxblood ground, a gold and indigo medallion border, worn pile."""
    yy, xx = grid()
    v = 0.45 + (noise(N, N, 41, 2) - 0.5) * 0.3
    img = ramp(v, VELVET, 1.0)
    u, w = (xx % 64) - 32, (yy % 64) - 32
    diamond = (np.abs(u) + np.abs(w))
    img[(diamond % 16 < 2) & (BAYER[yy % 4, xx % 4] < 0.7)] = hexc("#c08a3a")
    img[(diamond < 6)] = hexc("#2a2a6a")
    img[(diamond < 3)] = hexc("#e0b04a")
    img[((xx % 128 < 4) | (yy % 128 < 4)) & (BAYER[yy % 4, xx % 4] < 0.8)] = hexc("#1a1440")
    return img


# --- walls -------------------------------------------------------------------------------------------------------------------------------------------------------------

def tile_steel_wall(seed):
    """Riveted steel panels (three variants by seed): 1 m panels with rivet rows, rust weeping from the seams, a cool sheen on the upper left of each panel."""
    yy, xx = grid()
    rng = np.random.default_rng(seed)
    v = np.zeros((N, N))
    pw = [64, 128, 85][seed % 3]
    for py in range(0, N, 128):
        for px in range(0, N, pw):
            b = 0.32 + rng.random() * 0.18
            ly, lx = yy[py:py + 128, px:px + pw] - py, xx[py:py + 128, px:px + pw] - px
            v[py:py + 128, px:px + pw] = b + 0.14 * (1 - ly / 128.0) * (1 - lx / max(1, pw)) + 0.02
    v += (noise(N, N, seed, 4) - 0.5) * 0.16
    edge_x = (xx % pw < 2)
    edge_y = (yy % 128 < 2)
    v[edge_x | edge_y] = 0.06
    v[(xx % pw == 2) | (yy % 128 == 2)] += 0.14
    img = ramp(v, STEEL, 1.0)
    for x0 in range(0, N, pw):
        for y in range(6, N, 12):
            for x in (x0 + 5, x0 + pw - 6):
                if 0 < x < N - 1:
                    img[y, x] = hexc("#0e1226")
                    img[y - 1, x - 1] = hexc("#8aa4dc")
    rust = noise(N, N, seed + 3, 8)
    drip = (rust > 0.6) & ((yy % 128) > 4) & (np.abs((xx % pw) - pw // 2) > pw // 3) & (BAYER[yy % 4, xx % 4] < (rust - 0.6) * 2.5)
    img[drip] = hexc("#5a3020")
    return img


def tile_brick_wall(seed, pal=BRICK_C, mortar="#0c0a12", moss=False, bh=16, bw=48):
    """Brick with mortar variation: bricks of varied value and chipped corners, mortar joints that thin and thicken, soot and stains (three variants by seed)."""
    yy, xx = grid()
    rng = np.random.default_rng(seed)
    v = np.zeros((N, N))
    for r in range(N // bh):
        off = (r % 2) * (bw // 2) + int(rng.integers(-3, 4))
        for c in range(-1, N // bw + 2):
            x0, y0 = c * bw + off, r * bh
            b = 0.30 + rng.random() * 0.42
            for y in range(y0, y0 + bh):
                ly = y - y0
                for x in range(x0, x0 + bw):
                    lx = x - x0
                    joint = ly < 2 + (1 if (x * 7 + r) % 11 == 0 else 0) or lx < 2
                    v[y % N, x % N] = 0.05 if joint else b + 0.10 * (1 - ly / bh) - 0.05 * (lx / bw)
    v += (noise(N, N, seed + 1, 3) - 0.5) * 0.2
    soot = noise(N, N, seed + 2, 32, 2)
    v -= np.clip(soot - 0.55, 0, 1) * 0.6
    img = ramp(v, pal, 1.0)
    img[v <= 0.06] = hexc(mortar)
    if moss:
        m = (noise(N, N, seed + 4, 8) > 0.68) & (yy > N * 0.55) & (BAYER[yy % 4, xx % 4] < 0.5)
        img[m] = hexc("#2c3a1c")
    return img


def tile_velvet():
    """The lounge's walls: oxblood velvet in vertical pleats with a damask figure, lit from the upper left."""
    yy, xx = grid()
    pleat = 0.5 + 0.28 * np.sin(xx / 32.0 * 2 * math.pi) + 0.08 * np.sin(xx / 8.0)
    v = pleat + (noise(N, N, 51, 3) - 0.5) * 0.15 - 0.12 * (yy / N)
    img = ramp(v, VELVET, 1.0)
    u, w = (xx % 64) - 32, (yy % 96) - 48
    figure = (np.abs(np.abs(u) - 10 + np.abs(w) * 0.4) < 2) & (np.abs(w) < 30)
    img[figure & (BAYER[yy % 4, xx % 4] < 0.6)] = hexc("#a0563a")
    return img


def tile_roof():
    """The roof seen from below, drawn coarse (it is 10 m up and seen at grazing angles, where fine lines shimmer): dark glazing with the night's blue in big soft panes,
    a heavy truss chord and two webs, wide purlins; dithered sheen on the steel's lower edges only."""
    yy, xx = grid()
    v = 0.3 + (noise(N, N, 61, 64, 2) - 0.5) * 0.35
    img = ramp(v, ["#020309", "#04061a", "#081030", "#0e1a48", "#16285e"], 0.6)
    steel = (yy % 128 < 24) | ((xx % 128) < 12) | ((np.abs(((xx + yy) % 128) - 64) < 9) & ((yy % 128) < 64))
    sv = 0.3 + 0.25 * ((yy % 128) / 24.0).clip(0, 1) + (noise(N, N, 63, 16, 2) - 0.5) * 0.15
    sim = ramp(np.clip(sv, 0, 1), ["#05060e", "#0b0e1e", "#141a33", "#1e2748"], 0.6)
    img[steel] = sim[steel]
    edge = ((yy % 128) >= 20) & ((yy % 128) < 24) & (BAYER[yy % 4, xx % 4] < 0.5)
    img[edge] = hexc("#2e3b6a")
    return img


def tile_low_ceiling(pal):
    """The bar's and lounge's ceilings: dark timber joists over boards."""
    yy, xx = grid()
    v = 0.3 + (noise(N, N, 71, 4) - 0.5) * 0.2 + 0.1 * np.sin(yy / 6.0)
    joist = (xx % 64) < 14
    v[joist] = 0.5 + (noise(N, N, 72, 3)[joist] - 0.5) * 0.2 + 0.2 * (1 - (xx[joist] % 64) / 14.0)
    v[(xx % 64) == 14] = 0.02
    return ramp(v, pal, 0.9)


def tile_trim():
    """Step faces: steel with a copper nosing and rivets."""
    yy, xx = grid()
    v = 0.35 + (noise(N, N, 81, 4) - 0.5) * 0.2
    img = ramp(v, STEEL, 0.9)
    nose = yy < 24
    cv = 0.55 + 0.4 * (1 - yy / 24.0)
    cim = ramp(np.clip(cv, 0, 1), COPPER, 0.8)
    img[nose] = cim[nose]
    img[24:26, :] = hexc("#0b0d1c")
    for x in range(8, N, 32):
        img[40:42, x:x + 2] = hexc("#8aa4dc")
    return img


def tile_speaker():
    """A speaker plinth's face: a steel box with two cones, a bass port and an amber light strip along its foot (the painting's floor lights)."""
    img = tile_steel_wall(91)
    yy, xx = grid()
    for cx in (64, 192):
        for (cy, r) in ((80, 34), (176, 22)):
            d = np.hypot(xx - cx, yy - cy)
            cone = d < r
            cv = 0.15 + 0.5 * (d / r) + (noise(N, N, 92, 2) - 0.5) * 0.1
            cim = ramp(np.clip(cv, 0, 1), ["#05060c", "#0e1222", "#1c2440", "#2e3b6a", "#5f78b4"], 0.8)
            img[cone] = cim[cone]
            img[(np.abs(d - r) < 1.5)] = hexc("#8aa4dc")
            img[d < r * 0.22] = hexc("#2e3b6a")
    strip = (yy > 226) & (yy < 240)
    amber = (xx % 16 < 10) & strip
    img[strip] = hexc("#2a1208")
    img[amber] = hexc("#ffb24a")
    img[amber & (yy > 230) & (yy < 236)] = hexc("#ffe0a0")
    return img


def tile_cube():
    """The lit cube on the pedestal: red-magenta equaliser bars behind a grille."""
    yy, xx = grid()
    img = np.zeros((N, N, 3), np.uint8)
    img[:] = hexc("#2a0610")
    rng = np.random.default_rng(101)
    for c in range(16):
        h = int(40 + rng.random() * 180)
        x0 = c * 16 + 2
        for y in range(N - h, N - 4, 6):
            t = (N - y) / float(N)
            col = "#ff3a5c" if t < 0.5 else ("#ff7a5a" if t < 0.75 else "#ffd0a0")
            img[y:y + 4, x0:x0 + 11] = hexc(col)
    img[(xx % 16 == 0) | (yy % 6 == 5)] = (np.array(img[(xx % 16 == 0) | (yy % 6 == 5)]) * 0.35).astype(np.uint8)
    img[(yy < 6) | (yy > N - 6) | (xx < 4) | (xx > N - 5)] = hexc("#5a5a6a")
    return img


def tile_railing():
    """The fence round the floor, 1 m: the painting's riveted steel half-wall (two panels per 1 m tile) with a copper top rail; the slot under the rail and the posts' gaps
    are transparent (alpha), so the floor shows through a little as in the painting."""
    w, h = 128, 128
    yy, xx = np.mgrid[0:h, 0:w]
    v = 0.36 + (noise(h, w, 111, 4) - 0.5) * 0.18 + 0.12 * (1 - yy / h)
    v[(xx % 64) < 3] = 0.6
    v[(xx % 64) == 3] = 0.08
    img = ramp(v, STEEL, 1.0)
    for x0 in (0, 64):
        for y in range(30, 124, 12):
            for x in (x0 + 8, x0 + 56):
                img[y, x] = hexc("#0e1226")
                img[y - 1, x - 1] = hexc("#8aa4dc")
    rust = (noise(h, w, 112, 6) > 0.66) & (yy > 60) & (BAYER[yy % 4, xx % 4] < 0.4)
    img[rust] = hexc("#5a3020")
    rail = yy < 12
    cv = 0.35 + 0.6 * (1 - np.abs(yy - 4) / 6.0)
    cim = ramp(np.clip(cv, 0, 1), COPPER, 0.8)
    img[rail] = cim[rail]
    img[(yy < 3) & (BAYER[yy % 4, xx % 4] < 0.5)] = hexc("#ffd58a")
    alpha = np.ones((h, w))
    alpha[(yy >= 12) & (yy < 22) & ((xx % 64) > 4)] = 0.0  # the slot under the rail
    img[(yy >= 22) & (yy < 24)] = hexc("#0b0d1c")
    return img, alpha


# --- props cut from the painting ---------------------------------------------------------------------------------------------------------------------------------------

def cut(box, poly=None, scale=1.0, keep_dark=None, paint=None):
    """A piece of the painting: box (x0, y0, x1, y1); poly (painting pixels) its outline (alpha), else the whole box; scaled nearest-neighbour."""
    im = Image.open(paint or PAINT).convert("RGB")
    x0, y0, x1, y1 = box
    piece = im.crop(box)
    a = Image.new("L", piece.size, 255 if poly is None else 0)
    if poly is not None:
        ImageDraw.Draw(a).polygon([(x - x0, y - y0) for x, y in poly], fill=255)
    rgb = np.array(piece)
    al = np.array(a) > 127
    if keep_dark is not None:  # drop the near-black surround inside the outline (a lamp hanging in the dark)
        al &= rgb.astype(int).sum(axis=2) > keep_dark
    if scale != 1.0:
        sz = (max(1, int(round(piece.width * scale))), max(1, int(round(piece.height * scale))))
        rgb = np.array(Image.fromarray(rgb).resize(sz, Image.NEAREST))
        al = np.array(Image.fromarray((al * 255).astype(np.uint8)).resize(sz, Image.NEAREST)) > 127
    return rgb, al


def prop_window():
    """The stage backdrop: the window onto the night city with the moon and the water tower; the guide standing in front of it in the painting is painted out with the
    skyline from beside her."""
    im = np.array(Image.open(PAINT).convert("RGB"))
    box = (996, 228, 1252, 372)
    win = im[box[1]:box[3], box[0]:box[2]].copy()
    gx0, gx1 = 1092 - box[0], 1168 - box[0]
    gy0 = 266 - box[1]
    city = im[box[1]:box[3], 1060:1092]
    src = np.concatenate([city, city[:, ::-1], city], axis=1)[:, :gx1 - gx0]  # the skyline between the tower and her, repeated
    win[gy0:, gx0:gx1] = src[gy0:, :]
    return np.array(Image.fromarray(win).resize((win.shape[1] * 2, win.shape[0] * 2), Image.NEAREST)), None


def spr_beam(w=160, h=256):
    """A spotlight shaft (additive, soft: the one soft thing allowed), cobalt, widening downward, dithered dust motes in it."""
    yy, xx = np.mgrid[0:h, 0:w]
    half = 4 + (w / 2 - 6) * (yy / h)
    d = np.abs(xx - w / 2) / half
    a = np.clip(1 - d, 0, 1) ** 1.5 * (0.25 + 0.75 * (1 - yy / h) ** 0.6)
    rgb = np.zeros((h, w, 3), np.uint8)
    rgb[:] = hexc("#4a6cff")
    mote = (noise(h, w, 121, 2) > 0.8) & (d < 0.8)
    rgb[mote] = hexc("#c8d8ff")
    out = np.dstack([rgb, (np.clip(a * 1.2, 0, 1) * 255).astype(np.uint8)])
    return out


def spr_case():
    """A flight case: black ply, aluminium edges and corners, two latches."""
    w, h = 96, 64
    yy, xx = np.mgrid[0:h, 0:w]
    v = 0.25 + (noise(h, w, 131, 3) - 0.5) * 0.15
    img = ramp(v, ["#07080e", "#11131e", "#1c2030", "#2a3044"], 0.8)
    edge = (xx < 4) | (xx > w - 5) | (yy < 4) | (yy > h - 5) | (np.abs(yy - h // 2) < 2)
    ev = 0.5 + 0.4 * (1 - yy / h)
    eim = ramp(np.clip(ev, 0, 1), STEEL[2:], 0.8)
    img[edge] = eim[edge]
    for (cx, cy) in ((4, 4), (w - 5, 4), (4, h - 5), (w - 5, h - 5)):
        img[max(0, cy - 4):cy + 5, max(0, cx - 4):cx + 5] = hexc("#9aa6c8")
    for cx in (28, 68):
        img[h // 2 - 5:h // 2 + 5, cx - 4:cx + 4] = hexc("#c8d0e8")
        img[h // 2 - 1:h // 2 + 1, cx - 2:cx + 2] = hexc("#2a3044")
    return img, np.ones((h, w))


def spr_plant():
    """A potted plant: broad dark leaves catching the amber and the cobalt, a copper pot."""
    w, h = 96, 128
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    rng = np.random.default_rng(141)
    leaves = []
    for k in range(14):
        a = math.radians(-160 + k * 23 + rng.integers(-8, 8))
        L = 30 + rng.integers(0, 22)
        bx, by = w / 2, 86
        tx, ty = bx + math.cos(a) * L, by - abs(math.sin(a)) * L - 10
        d.polygon([(bx, by), (tx - 6, ty + 4), (tx, ty), (tx + 6, ty + 6)], fill=255)
        leaves.append((tx, ty))
    al = np.array(m) > 127
    yy, xx = np.mgrid[0:h, 0:w]
    v = 0.35 + 0.35 * (1 - yy / 90.0) + (noise(h, w, 142, 3) - 0.5) * 0.3
    img = ramp(np.clip(v, 0, 1), ["#08140c", "#11281a", "#1c4026", "#2c5c30", "#4a7a3a", "#7aa04a"], 1.0)
    vein = (np.abs(xx - w / 2) < 1) & al
    img[vein] = hexc("#0a160c")
    pot = (yy >= 84) & (np.abs(xx - w / 2) < 18 - (yy - 84) * 0.12)
    pv = 0.5 + 0.35 * (1 - np.abs(xx - w / 2 + 6) / 18.0)
    pim = ramp(np.clip(pv, 0, 1), COPPER, 0.8)
    img[pot] = pim[pot]
    al |= pot
    return img, al


def spr_sofa():
    """The lounge's tufted oxblood sofa (front view): a rolled-arm Chesterfield, buttons dithered in."""
    w, h = 192, 96
    yy, xx = np.mgrid[0:h, 0:w]
    al = np.zeros((h, w), bool)
    al[20:88, 14:w - 14] = True
    al[34:92, 0:24] = True
    al[34:92, w - 24:] = True
    v = 0.45 + 0.25 * (1 - yy / h) + (noise(h, w, 151, 2) - 0.5) * 0.2
    tuft = ((xx % 16 - 8) ** 2 + (yy % 14 - 7) ** 2) < 6
    v[tuft & (yy < 56)] -= 0.25
    v[(yy >= 56) & (yy < 60)] = 0.15
    img = ramp(np.clip(v, 0, 1), VELVET, 1.0)
    img[tuft & (yy < 56) & ((xx % 16) == 8) & ((yy % 14) == 7)] = hexc("#ffb070")
    for x0 in (0, w - 24):
        img[34:38, x0:x0 + 24] = hexc("#c0584a")
    img[88:92, 14:w - 14] = hexc("#2a1208")
    img[88:96, 20:28] = hexc("#5a3a1c")
    img[88:96, w - 28:w - 20] = hexc("#5a3a1c")
    al[88:96, 20:28] = True
    al[88:96, w - 28:w - 20] = True
    return img, al


PROPS = {  # name: (function or painting cut args)
    "wh_p_banner": dict(box=(381, 147, 440, 330)),
    "wh_p_banner_b": dict(box=(1365, 175, 1418, 335)),
    "wh_p_speaker": dict(box=(484, 170, 556, 295), poly=[(486, 178), (530, 171), (555, 180), (555, 290), (520, 294), (486, 282)]),
    "wh_p_backbar": dict(box=(56, 262, 140, 378)),
    "wh_p_counter": dict(box=(64, 504, 186, 658)),
    "wh_p_lamp_cu": dict(box=(52, 242, 134, 322), poly=[(86, 242), (98, 242), (100, 262), (120, 276), (133, 300), (128, 320), (58, 320), (54, 300), (66, 276), (84, 262)]),
    "wh_p_lamp_lg": dict(box=(1496, 328, 1568, 438), poly=[(1515, 330), (1550, 330), (1566, 375), (1542, 381), (1540, 436), (1522, 436), (1520, 381), (1498, 375)]),
    "wh_p_pelmet": dict(box=(1436, 165, 1672, 330)),
    "wh_p_case": dict(box=(0, 700, 145, 941), poly=[(0, 708), (132, 708), (144, 720), (144, 941), (0, 941)]),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    made = []
    tiles = {
        "wh_walk": tile_walk(), "wh_grate": tile_grate(), "wh_dance": tile_dance(), "wh_boards": tile_boards(), "wh_stage_boards": tile_boards(33, ["#0a0a14", "#14141f", "#20202e", "#2e2e40", "#40405a", "#5a5a7a"]),
        "wh_carpet": tile_carpet(), "wh_steel_a": tile_steel_wall(1), "wh_steel_b": tile_steel_wall(2), "wh_steel_c": tile_steel_wall(3),
        "wh_brick_a": tile_brick_wall(11), "wh_brick_b": tile_brick_wall(12, moss=True), "wh_brick_c": tile_brick_wall(13),
        "wh_bar_brick": tile_brick_wall(21, WARM_BRICK, "#0e0806"), "wh_velvet": tile_velvet(), "wh_roof": tile_roof(),
        "wh_ceil_bar": tile_low_ceiling(WARM_BRICK[:5]), "wh_ceil_lounge": tile_low_ceiling(["#0e0406", "#1e0a0c", "#341414", "#4c2018", "#683222"]),
        "wh_trim": tile_trim(), "wh_speaker": tile_speaker(), "wh_cube": tile_cube(),
    }
    for k, v in tiles.items():
        made.append(save(k, v))
    rgb, a = tile_railing()
    made.append(save("wh_railing", rgb, a))
    for k, kw in PROPS.items():
        rgb, al = cut(**kw)
        made.append(save(k, rgb, al))
    rgb, _ = prop_window()
    made.append(save("wh_p_window", rgb))
    beam = spr_beam()
    im = Image.fromarray(beam, "RGBA")
    im.save(os.path.join(OUT, "wh_p_beam.png"))
    made.append(im)
    for k, fn in (("wh_p_case2", spr_case), ("wh_p_plant", spr_plant), ("wh_p_sofa", spr_sofa)):
        rgb, al = fn()
        made.append(save(k, rgb, al))
    cols = 8
    cell = 128
    rows = (len(made) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell), (14, 12, 34))
    for i, im in enumerate(made):
        t = im.convert("RGBA").copy()
        t.thumbnail((cell, cell), Image.NEAREST)
        sheet.paste(t, ((i % cols) * cell, (i // cols) * cell), t)
    os.makedirs(os.path.dirname(SHEET), exist_ok=True)
    sheet.save(SHEET)
    print("wrote %d textures and props to %s, sheet %s" % (len(made), OUT, SHEET))


if __name__ == "__main__":
    sys.exit(main())
