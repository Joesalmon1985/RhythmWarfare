#!/usr/bin/env python3
"""The art kit of the three new raves (Magic, Dinosaurs, Transport): what their generators (tools/story/build_<theme>_rave.py) draw with. PLACEHOLDER art in the brief's sense: procedural, drawn with the
project's pixel kit (tools/story/art/bedsit_draw.py, pixeltex.py), legible and themed but not hand-finished; the Doom worlds' own tiles (assets/story/doom_lounge, doom_underworld, doom_dock on
feature/doom-layout-worlds) are borrowed and recoloured where they fit.

    Art(theme)       the folder assets/story/rave_<theme>/: textures/, sprites/ (the activities' sheets), source/chars (tools/story/rave_people.py), manifest.json
    tiles            tileable 128 px floors and walls from a palette ramp and a pattern
    sprites          counters, cabinets, racks, decks, consoles, hatches, vehicles drawn from boxes and a palette
    sky, pieces, knob_sheet, manifest
"""
from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

from art import pixeltex as px  # noqa: E402
from art.bedsit_draw import Cv, ramp  # noqa: E402

N = 128
MOTHERSHIP = os.path.join(ROOT, "assets", "story", "mothership")


class Art:
    def __init__(self, theme: str):
        self.theme = theme
        self.name = "rave_" + theme
        self.dir = os.path.join(ROOT, "assets", "story", self.name)
        self.tex = os.path.join(self.dir, "textures")
        os.makedirs(self.tex, exist_ok=True)
        self.made = {}  # texture name -> (w, h, metres)

    def tile(self, name: str, rgb: np.ndarray, metres: float = 2.0) -> None:
        Image.fromarray(rgb, "RGB").save(os.path.join(self.tex, name + ".png"), optimize=False, compress_level=9)
        self.made[name] = (rgb.shape[1], rgb.shape[0], metres)

    def sprite(self, name: str, cv: Cv) -> None:
        cv.save(os.path.join(self.tex, name + ".png"))
        self.made[name] = (cv.w, cv.h, 1.0)

    def image(self, name: str, im: Image.Image, metres: float = 1.0) -> None:
        im.save(os.path.join(self.tex, name + ".png"), optimize=False, compress_level=9)
        self.made[name] = (im.width, im.height, metres)

    def borrow(self, src_dir: str, names: dict, metres: float = 2.0) -> None:
        """Doom tiles copied under new names: {new: (old, hue_degrees, saturation, value)}; a plain string is a straight copy."""
        for new, spec in names.items():
            old, hue, sat, val = (spec, 0, 1.0, 1.0) if isinstance(spec, str) else spec
            im = Image.open(os.path.join(src_dir, old + ".png")).convert("RGBA")
            if hue or sat != 1.0 or val != 1.0:
                im = hsv(im, hue, sat, val)
            self.image(new, im, metres if im.width >= 96 and im.height >= 96 and im.width == im.height else 1.0)

    def copy_mothership(self, names: list) -> None:
        for n in names:
            im = Image.open(os.path.join(MOTHERSHIP, "textures", n + ".png"))
            self.image(n, im)


def hsv(im: Image.Image, hue: float, sat: float, val: float) -> Image.Image:
    a = np.asarray(im.convert("RGBA")).astype(np.float32) / 255.0
    rgb = a[..., :3]
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(m & (mx == r), ((g - b) / np.where(m, d, 1)) % 6, h)
    h = np.where(m & (mx == g), (b - r) / np.where(m, d, 1) + 2, h)
    h = np.where(m & (mx == b), (r - g) / np.where(m, d, 1) + 4, h)
    h = (h / 6.0 + hue / 360.0) % 1.0
    s = np.where(mx > 1e-6, d / np.where(mx > 1e-6, mx, 1), 0) * sat
    v = mx * val
    s, v = np.clip(s, 0, 1), np.clip(v, 0, 1)
    i = np.floor(h * 6).astype(int) % 6
    f = h * 6 - np.floor(h * 6)
    p, q, t = v * (1 - s), v * (1 - f * s), v * (1 - (1 - f) * s)
    out = np.zeros_like(rgb)
    for k, (rr, gg, bb) in enumerate([(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)]):
        sel = i == k
        out[..., 0] = np.where(sel, rr, out[..., 0])
        out[..., 1] = np.where(sel, gg, out[..., 1])
        out[..., 2] = np.where(sel, bb, out[..., 2])
    res = np.dstack([out, a[..., 3]])
    return Image.fromarray((res * 255 + 0.5).astype(np.uint8), "RGBA")


# ---------------------------------------------------------------------------------------------------------------------------------------- tiles
def grid(n=N):
    return px.grid(n)


def q(shade, pal):
    return px.quantise(np.clip(shade, 0, 1), pal)


def mosaic(pal_cols, cells=4, seed=1, grout="#1a1038", hue_cycle=None):
    """Glazed tiles; with hue_cycle (a list of ramps) every tile takes one of them: an iridescent floor."""
    sh, g = px.tiles(N, cells, 1, seed, 0.5)
    x, y = grid()
    s = N / cells
    k = ((y // s).astype(int) * 3 + (x // s).astype(int) * 2 + (np.random.RandomState(seed).randint(0, 7, (cells, cells))[(y // s).astype(int) % cells, (x // s).astype(int) % cells])) % len(hue_cycle or [0])
    if hue_cycle:
        out = np.zeros((N, N, 3), np.uint8)
        for i, p in enumerate(hue_cycle):
            out[k == i] = q(sh, p)[k == i]
    else:
        out = q(sh, pal_cols)
    out[g > 0.5] = (px.hexc(grout) * 255).astype(np.uint8)
    return out


def ground(pal, scale=10, seed=1, speck=None, speck_pal=None, density=0.02):
    """Noise ground (moss, rock, sand) with optional speckles (flowers, grit)."""
    sh = px.noise(N, scale, seed, 4) * 0.9 + (px.noise(N, 3, seed + 1) - 0.5) * 0.2
    out = q(sh, pal)
    if speck is not None:
        m = px.speckle(N, density, seed + 5) > 0.5
        cols = np.array([px.hexc(c) * 255 for c in speck], np.uint8)
        idx = np.random.RandomState(seed + 6).randint(0, len(cols), (N, N))
        out[m] = cols[idx][m]
    return out


def facets(pal, seed=1, n=6, edge="#2a1860"):
    """Crystal facets: a Voronoi of n cells each shaded by its own tone, light edges."""
    rng = np.random.RandomState(seed)
    pts = rng.rand(n * n, 2) * N
    x, y = grid()
    best = np.full((N, N), 1e9, np.float32)
    second = np.full((N, N), 1e9, np.float32)
    cell = np.zeros((N, N), int)
    for i, (cx, cy) in enumerate(pts):
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                d = np.sqrt((x - cx - ox) ** 2 + (y - cy - oy) ** 2)
                closer = d < best
                second = np.where(closer, best, np.minimum(second, d))
                cell = np.where(closer, i, cell)
                best = np.where(closer, d, best)
    tone = rng.rand(n * n)[cell]
    sh = 0.25 + 0.55 * tone + 0.25 * np.clip(1 - (second - best) / 4.0, 0, 1) * (0.4 - 0.4 * tone)
    out = q(sh, pal)
    out[(second - best) < 1.3] = (px.hexc(edge) * 255).astype(np.uint8)
    return out


def curtain(pal, folds=8, seed=1, trim=None):
    x, y = grid()
    ph = np.sin(x / N * folds * 2 * math.pi + (px.noise(N, 24, seed) - 0.5) * 1.2)
    sh = 0.5 + 0.38 * ph * 0.9 + (px.noise(N, 6, seed + 2) - 0.5) * 0.12
    out = q(sh, pal)
    if trim:
        out[(y < 5) | (y > N - 6)] = (px.hexc(trim) * 255).astype(np.uint8)
    return out


def starfield(pal, seed=1, density=0.012, cols=("#ffffff", "#ffe27a", "#7ff0ff")):
    sh = px.noise(N, 40, seed, 3) * 0.5
    out = q(sh, pal)
    m = px.speckle(N, density, seed + 3) > 0.5
    c = np.array([px.hexc(k) * 255 for k in cols], np.uint8)
    idx = np.random.RandomState(seed + 4).randint(0, len(cols), (N, N))
    out[m] = c[idx][m]
    return out


def planks(pal, seed=1, boards=8, vertical=False):
    x, y = grid()
    a = x if vertical else y
    s = N / boards
    r = (a // s).astype(int)
    tone = np.random.RandomState(seed).rand(boards)[r % boards]
    grain = px.noise(N, 16, seed + 2)
    sh = 0.35 + 0.3 * tone + (grain - 0.5) * 0.25
    out = q(sh, pal)
    out[(a % s) < 1] = (pal[0] * 255).astype(np.uint8)
    return out


def inlay(out, kind, col, width=2):
    """A line pattern on a tile (rings, diamonds, a cross) in colour col."""
    x, y = grid()
    c = N / 2
    if kind == "rings":
        r = np.sqrt((x - c) ** 2 + (y - c) ** 2)
        m = (np.abs(r - 20) < width) | (np.abs(r - 44) < width) | (np.abs(r - 60) < width)
    elif kind == "diamond":
        m = (np.abs(np.abs(x - c) + np.abs(y - c) - 50) < width) | (np.abs(np.abs(x - c) + np.abs(y - c) - 24) < width)
    else:
        m = (np.abs(x - c) < width) | (np.abs(y - c) < width)
    out[m] = (px.hexc(col) * 255).astype(np.uint8)
    return out


def band(pal, col_line, seed=1, h=64):
    """A trim band (64 x 64): a lit moulding with a line of studs."""
    x, y = np.mgrid[0:h, 0:h].astype(np.float32)[::-1]
    sh = 0.5 + 0.3 * np.cos((y - h / 2) / (h / 2) * 1.4) + (px.noise(h, 6, seed) - 0.5) * 0.15
    out = px.quantise(np.clip(sh, 0, 1), pal)
    stud = ((x % 16) < 3) & (np.abs(y - h / 2) < 2.5)
    out[stud] = (px.hexc(col_line) * 255).astype(np.uint8)
    return out


# ---------------------------------------------------------------------------------------------------------------------------------------- skies and the soft pieces
def sky(path: str, stops: list, stars=0.0, glow=None, seed=1, w=256, h=64, bands=None) -> None:
    """A cylinder sky 256 x 64: vertical gradient through `stops` (top to bottom hex colours), optional stars, a horizon glow [(x, strength, colour)] and cloud bands (periodic)."""
    cols = [px.hexc(c) for c in stops]
    t = np.linspace(0, 1, h)[:, None]
    k = t * (len(cols) - 1)
    i = np.clip(np.floor(k).astype(int), 0, len(cols) - 2)
    f = k - i
    img = np.zeros((h, w, 3), np.float32)
    for r in range(h):
        img[r, :] = cols[i[r, 0]] * (1 - f[r, 0]) + cols[i[r, 0] + 1] * f[r, 0]
    xx = np.arange(w)[None, :]
    if bands:
        for (y0, amp, col, sc) in bands:
            nz = px.noise(max(w, h), sc, seed + int(y0))[:h, :w]
            m = np.clip(1 - np.abs(np.arange(h)[:, None] - y0) / (h * 0.18), 0, 1) * np.clip((nz - 0.35) * 2.2, 0, 1) * amp
            img = img * (1 - m[..., None]) + px.hexc(col) * m[..., None]
    if glow:
        for (gx, strength, col) in glow:
            d = np.minimum(np.abs(xx - gx), w - np.abs(xx - gx)) / (w * 0.14)
            m = np.clip(1 - d, 0, 1) ** 2 * strength * np.clip(t * 1.3 - 0.15, 0, 1)
            img = img * (1 - m[..., None]) + px.hexc(col) * m[..., None]
    if stars:
        rng = np.random.RandomState(seed)
        for _ in range(int(w * h * stars)):
            sx, sy = rng.randint(0, w), rng.randint(0, int(h * 0.7))
            img[sy, sx] = np.maximum(img[sy, sx], px.hexc(["#ffffff", "#cfe8ff", "#ffe9a8"][rng.randint(0, 3)]))
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8), "RGB").save(path, optimize=False, compress_level=9)


def soft(w: int, h: int, fn) -> Image.Image:
    """An RGBA image from fn(x, y) -> (r, g, b, a) arrays in 0..1 over normalised coordinates 0..1."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r, g, b, a = fn(xx / w, yy / h)
    return Image.fromarray((np.clip(np.dstack([r, g, b, a]), 0, 1) * 255).astype(np.uint8), "RGBA")


def piece_beams(col, n=3, w=256, h=192):
    """Light beams fanning down from the top: n shafts."""
    c = np.array(px.hexc(col))
    def fn(x, y):
        a = np.zeros_like(x)
        for k in range(n):
            cx = (k + 0.5) / n
            half = 0.04 + 0.12 * y
            a = np.maximum(a, np.clip(1 - np.abs(x - cx - (cx - 0.5) * 0.5 * y) / half, 0, 1) ** 1.5 * (1 - y * 0.55) * 0.75)
        return c[0] + 0 * x, c[1] + 0 * x, c[2] + 0 * x, a
    return soft(w, h, fn)


def piece_ring(col, col2, w=256, h=96):
    """Two glowing elliptical rings (a stage ring)."""
    c1, c2 = np.array(px.hexc(col)), np.array(px.hexc(col2))
    def fn(x, y):
        d = np.sqrt(((x - 0.5) / 0.5) ** 2 + ((y - 0.5) / 0.5) ** 2)
        a1 = np.clip(1 - np.abs(d - 0.93) / 0.07, 0, 1)
        a2 = np.clip(1 - np.abs(d - 0.62) / 0.06, 0, 1) * 0.8
        a = np.maximum(a1, a2)
        m = a1 / np.maximum(a1 + a2, 1e-3)
        return c1[0] * m + c2[0] * (1 - m), c1[1] * m + c2[1] * (1 - m), c1[2] * m + c2[2] * (1 - m), a
    return soft(w, h, fn)


def piece_dome(col, w=192, h=160):
    """A translucent dome / aurora curtain: a bright rim and a faint body."""
    c = np.array(px.hexc(col))
    def fn(x, y):
        d = np.sqrt(((x - 0.5) / 0.5) ** 2 + ((y - 1.0) / 1.0) ** 2)
        body = (d < 1) * 0.22 * (1 - d * 0.5)
        rim = np.clip(1 - np.abs(d - 0.97) / 0.045, 0, 1) * 0.9
        a = np.maximum(body, rim) * (y < 0.995)
        return c[0] + 0 * x, c[1] + 0 * x, c[2] + 0 * x, a
    return soft(w, h, fn)


def piece_curtain(cols, w=256, h=128):
    """Soft vertical colour curtains (an aurora, fire sheets): bands of the colours in `cols` fading downward."""
    cs = [np.array(px.hexc(c)) for c in cols]
    def fn(x, y):
        k = np.clip((x * len(cs)).astype(int), 0, len(cs) - 1)
        r = sum(cs[i][0] * (k == i) for i in range(len(cs)))
        g = sum(cs[i][1] * (k == i) for i in range(len(cs)))
        b = sum(cs[i][2] * (k == i) for i in range(len(cs)))
        a = (0.55 + 0.35 * np.sin(x * 40 + y * 3)) * np.clip(1 - y, 0, 1) ** 1.3 * np.clip(y * 8, 0, 1) * 0.8
        return r, g, b, a
    return soft(w, h, fn)


def piece_glow(col, w=192, h=96):
    c = np.array(px.hexc(col))
    def fn(x, y):
        d = np.sqrt(((x - 0.5) / 0.5) ** 2 + ((y - 0.5) / 0.5) ** 2)
        return c[0] + 0 * x, c[1] + 0 * x, c[2] + 0 * x, np.clip(1 - d, 0, 1) ** 1.6 * 0.7
    return soft(w, h, fn)


def knob_sheet(body: list, glow: str, strain="#ffd23f", ring_on="#7cf0d0", ring_off="#2b2040", indicator="#ffffff", off_ind="#d8c8e8") -> Cv:
    """The bass knob's four frames in one row (stuck, straining, free, up), 40 x 40 each: the Space rave's, in the theme's colours."""
    sheet = Cv(160, 40)
    pal = ramp(*body)
    for i, (ang, lit, jitter) in enumerate([(-40, False, 0), (-34, False, 2), (10, True, 0), (62, True, 0)]):
        f = Cv(40, 40)
        f.paint(f.ell(2, 2, 38, 38), pal, f.dome(18, 18, 18, 18), edge=True)
        a = math.radians(ang - 90)
        cx, cy = 20 + jitter, 20
        f.flat(f.line((cx, cy), (cx + 14 * math.cos(a), cy + 14 * math.sin(a)), 4), indicator if lit else off_ind)
        for k in range(8):
            b = math.radians(-135 + k * 38.5 - 90)
            f.flat(f.ell(20 + 18 * math.cos(b) - 1, 20 + 18 * math.sin(b) - 1, 20 + 18 * math.cos(b) + 1, 20 + 18 * math.sin(b) + 1), ring_on if (lit and k <= 2 + 2 * (i - 2)) else ring_off)
        if i == 1:
            f.flat(f.rect(0, 18, 3, 22), strain)
            f.flat(f.rect(37, 18, 40, 22), strain)
        sheet.stamp(f, i * 40, 0)
    return sheet


def split_knob(art: Art, sheet: Cv, prefix: str) -> None:
    art.sprite(prefix + "_sheet", sheet)
    im = sheet.image()
    for i in range(4):
        art.image("%s_%d" % (prefix, i), im.crop((i * 40, 0, i * 40 + 40, 40)))


# ---------------------------------------------------------------------------------------------------------------------------------------- sprites
def counter(w=128, h=128, body=("#2a1840", "#5a3a8a", "#8a60c8", "#c8a0ff"), top="#ffe27a", front=None, items=None) -> Cv:
    """A bar / cloakroom counter seen from the front: a slab on a plinth, a lit top edge, optional front panel colour and `items` (callable(cv)) standing on it."""
    c = Cv(w, h)
    pal = ramp(*body)
    y0 = int(h * 0.50)
    c.paint(c.rrect(4, y0, w - 4, h - 6, 4), pal, c.lit((4, y0, w - 4, h - 6), 0.5, 0.45))
    c.flat(c.rect(2, y0 - 6, w - 2, y0 + 3), top, edge=True, edge_col="#14102e")
    c.paint(c.rect(10, y0 + 14, w - 10, h - 12), ramp(*[body[0], body[1], body[2]]), c.lit((10, y0 + 14, w - 10, h - 12), 0.4, 0.3), edge=True)
    if front:
        c.flat(c.rect(14, y0 + 18, w - 14, h - 16), front)
        for k in range(1, 4):
            c.flat(c.rect(14 + k * (w - 28) // 4 - 1, y0 + 18, 14 + k * (w - 28) // 4 + 1, h - 16), body[0])
    c.flat(c.rect(6, h - 8, w - 6, h - 3), body[0])
    if items:
        items(c, y0 - 6)
    return c


def cabinet(w=96, h=128, body=("#1a1030", "#3a2468", "#6a48a8", "#a888e0"), shelf="#ffe27a", items=None) -> Cv:
    """A tall shelf unit: frame, four shelves, `items` (callable(cv, shelf_ys)) on them."""
    c = Cv(w, h)
    pal = ramp(*body)
    c.paint(c.rrect(4, 4, w - 4, h - 4, 3), pal, c.lit((4, 4, w - 4, h - 4), 0.5, 0.4))
    c.flat(c.rect(9, 10, w - 9, h - 10), body[0])
    ys = [10 + k * (h - 24) // 4 for k in range(1, 5)]
    for y in ys:
        c.flat(c.rect(8, y, w - 8, y + 3), shelf, edge=True, edge_col=body[0])
    if items:
        items(c, ys)
    return c


def rack(w=128, h=128, post="#7a5a3a", rail="#c8a050", cols=("#ff7ad8", "#7ff0ff", "#ffe27a", "#b48cff", "#8fffd0"), shape="cape") -> Cv:
    """A coat rail: two posts, a bar and hanging garments (shape cape | coat | vest)."""
    c = Cv(w, h)
    c.flat(c.rect(6, 12, 12, h - 4), post, edge=True, edge_col="#14102e")
    c.flat(c.rect(w - 12, 12, w - 6, h - 4), post, edge=True, edge_col="#14102e")
    c.flat(c.rect(4, 14, w - 4, 20), rail, edge=True, edge_col="#14102e")
    n = 6
    for k in range(n):
        x = 16 + k * (w - 32) // n
        col = cols[k % len(cols)]
        if shape == "vest":
            c.flat(c.poly([(x, 22), (x + 14, 22), (x + 16, 74), (x - 2, 74)]), col, edge=True, edge_col="#14102e")
            c.flat(c.rect(x + 1, 40, x + 13, 44), "#e8f4ff")
        else:
            c.flat(c.poly([(x, 22), (x + 16, 22), (x + 22, 92), (x - 6, 92)]), col, edge=True, edge_col="#14102e")
            c.flat(c.rect(x + 6, 22, x + 10, 94), tuple_mix(col, "#000000", 0.25))
    return c


def tuple_mix(a: str, b: str, t: float) -> str:
    ca, cb = px.hexc(a), px.hexc(b)
    m = ca + (cb - ca) * t
    return "#%02x%02x%02x" % tuple(int(v * 255) for v in m)


def deck(w=96, h=56, body=("#1a1240", "#2c2368", "#43399a", "#6a5fd0"), lip="#8cf6e0", platter="#242434", hub="#ff4fc8", keys=("#7cf0d0", "#7cf0d0", "#ffd23f", "#ff4fc8")) -> Cv:
    """The DJ deck seen from the dance floor (the Space rave's, in the theme's colours): two platters and a mixer with the stuck knob in the middle."""
    c = Cv(w, h)
    c.paint(c.rrect(0, 14, w, h, 3), ramp(*body), c.lit((0, 14, w, h), 0.5, 0.4))
    c.flat(c.rect(1, 14, w - 1, 17), lip)
    for cx in (22, 74):
        c.paint(c.ell(cx - 15, 18, cx + 15, 48), ramp("#101018", platter, "#3b3b55"), c.dome(cx, 33, 15, 15))
        c.flat(c.ell(cx - 3, 31, cx + 3, 37), hub)
    c.flat(c.rect(40, 20, 56, 52), body[0], edge=True, edge_col="#05030f")
    for i, col in enumerate(keys):
        c.flat(c.rect(42, 23 + i * 6, 54, 26 + i * 6), col)
    c.flat(c.ell(44, 44, 52, 52), "#a8a8c0", edge=True, edge_col="#3b3b55")
    return c


def console(w=128, h=128, body=("#1a1030", "#3a2468", "#6a48a8", "#a888e0"), screen="#7ff0ff", lamp="#ffe27a") -> Cv:
    c = Cv(w, h)
    c.paint(c.poly([(14, 118), (24, 56), (104, 56), (114, 118)]), ramp(*body), c.lit((14, 56, 114, 118), 0.5, 0.4))
    c.paint(c.poly([(20, 56), (30, 30), (98, 30), (108, 56)]), ramp(body[0], body[1], body[2]), c.lit((20, 30, 108, 56), 0.45, 0.3))
    c.flat(c.rect(38, 36, 90, 52), "#0a0820", edge=True, edge_col=body[3])
    c.flat(c.rect(42, 40, 86, 48), screen)
    for k in range(5):
        c.flat(c.ell(34 + k * 15, 66, 42 + k * 15, 74), [lamp, "#ff4fc8", "#7cf0d0", lamp, "#ff7a3a"][k], edge=True, edge_col="#14102e")
    c.flat(c.rect(30, 84, 98, 90), body[3])
    return c


def hatch_door(w=48, h=84, frame=("#3a3a14", "#7a6a1c", "#d8b02a", "#f2d66a"), glass=("#142840", "#1f4468", "#2f6a96", "#4a90c0"), lamp="#58ff9c", glow=None) -> Cv:
    """The way home: a door standing in the hub's alcove (a billboard): frame, a lit panel, a lamp."""
    c = Cv(w, h)
    c.paint(c.rrect(0, 0, w, h, 4), ramp(*frame), c.lit((0, 0, w, h), 0.5, 0.4))
    c.paint(c.rrect(5, 5, w - 5, h - 5, 3), ramp(*glass), c.lit((5, 5, w - 5, h - 5), 0.5, 0.4))
    if glow:
        c.flat(c.ell(w // 2 - 12, 22, w // 2 + 12, 58), glow)
        c.flat(c.ell(w // 2 - 7, 28, w // 2 + 7, 50), "#ffffff")
    c.flat(c.ell(w // 2 - 3, 8, w // 2 + 3, 12), lamp)
    c.flat(c.rect(w - 14, h // 2, w - 9, h // 2 + 12), frame[3], edge=True, edge_col="#14102e")
    return c


def outline_poly(c: Cv, pts, col, edge="#14102e"):
    c.flat(c.poly(pts), col, edge=True, edge_col=edge)


def vehicle(w, h, hull, glass, wheel="#101018", stripe=None, kind="car") -> Cv:
    """A side-on vehicle (kind car | bus | coach): a body, windows, two wheels, an optional stripe."""
    c = Cv(w, h)
    pal = ramp(*hull)
    if kind == "bus":
        c.paint(c.rrect(2, 6, w - 2, h - 12, 6), pal, c.lit((2, 6, w - 2, h - 12), 0.5, 0.4))
        for k in range(5):
            c.paint(c.rrect(8 + k * (w - 24) // 5, 12, 8 + k * (w - 24) // 5 + (w - 30) // 5, 30, 2), ramp(*glass), c.lit((8, 12, w, 30), 0.5, 0.3))
        c.paint(c.rect(w - 22, 12, w - 6, 40), ramp(*glass), c.lit((w - 22, 12, w - 6, 40), 0.5, 0.3))
    else:
        c.paint(c.poly([(4, h - 14), (10, h * 0.45), (w * 0.28, h * 0.3), (w * 0.62, h * 0.3), (w - 8, h * 0.52), (w - 4, h - 14)]), pal, c.lit((0, h * 0.3, w, h), 0.5, 0.45))
        c.paint(c.poly([(w * 0.3, h * 0.34), (w * 0.34, h * 0.14), (w * 0.58, h * 0.14), (w * 0.66, h * 0.34)]), ramp(*glass), c.lit((w * 0.3, h * 0.14, w * 0.66, h * 0.34), 0.5, 0.3))
    if stripe:
        c.flat(c.rect(4, int(h * 0.62), w - 4, int(h * 0.62) + 4), stripe)
    for cx in (int(w * 0.24), int(w * 0.76)):
        c.paint(c.ell(cx - 11, h - 24, cx + 11, h), ramp(wheel, "#242434", "#3b3b55"), c.dome(cx, h - 12, 11, 11))
        c.flat(c.ell(cx - 3, h - 15, cx + 3, h - 9), "#c8c8d8")
    return c


# ---------------------------------------------------------------------------------------------------------------------------------------- the manifest
def stage_sprites() -> dict:
    """The Mothership's stage sprites that every rave's maps use (woofer, fixture, disco ball, glow), by res:// path."""
    m = json.load(open(os.path.join(MOTHERSHIP, "manifest.json"), encoding="utf-8"))
    out = {}
    for k in ("woofer", "fixture", "disco_ball", "glowstick", "glow"):
        e = dict(m["stage"]["sprites"][k])
        e["file"] = "res://assets/story/mothership/" + e["file"]
        out[k] = e
    return out


def write_manifest(art: Art, archetypes: dict, tex_names: list, pieces: list) -> None:
    """assets/story/<art>/manifest.json: the themed rigs, the shared stage sprites, the theme's pieces and the map textures."""
    tex = {n: {"file": "textures/%s.png" % n, "size": [art.made[n][0], art.made[n][1]], "metres": art.made[n][2]} for n in tex_names}
    man = {"version": 1, "level": art.name, "px_scale_note": "texture px x px_scale = design px",
           "archetypes": archetypes, "silhouettes": {},
           "stage": {"layers": [], "sprites": stage_sprites(), "pieces": pieces},
           "textures": tex, "people": {}}
    with open(os.path.join(art.dir, "manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1)
        fh.write("\n")


def piece_entry(pid: str, file: str, anim="pulse", blend="mix", size=(256, 128)) -> dict:
    return {"id": pid, "file": "textures/%s.png" % file, "pos": [0, 0], "size": list(size), "px_scale": 1.0, "pivot": [size[0] / 2, size[1]], "anim": anim, "z": "behind", "blend": blend}
