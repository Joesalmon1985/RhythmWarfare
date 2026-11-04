"""The Ward's procedural pixel textures (docs/STORY_25D_ART_DIRECTION.md 1 and 2.D): grim, institutional, green.

Green glazed tiles with grout, grime and rust streaks under a dado line; peeling painted plaster; pipes along the walls; dark red floor tiles with
grout and a wet sheen; worn lino; steel doors with peeling paint and a barred hatch; a radiator; barred windows onto a moonlit sky with bare trees;
padded cells; cracked plaster ceilings with fluorescent tubes; one warm office. Everything is drawn on a (material, shade) canvas and quantised to
the material's palette ramp with ordered dithering (pixeltex.quantise), so it reads as hand-placed pixels.

`build()` returns the opaque tiles {id: (rgb, metres)} (tiles.procedural writes them, replacing the baked tile of the same id). The billboard props
(`thing_*`, RGBA with a transparent background) are written here directly into assets/story/mental_hospital/textures/, because pixeltex.save writes
RGB; their ids and metres are listed in tiles.MENTAL_HOSPITAL so the manifest picks them up. Deterministic: every random value comes from a seed.
"""
from __future__ import annotations

import os

import numpy as np

from . import lib
from . import pixeltex as px

# ---- palettes (dark to light) ---------------------------------------------------------------------------------------------------------------------

PAL = {
    "tile": px.ramp("#0b1712", "#13241b", "#1c3326", "#264232", "#32543f", "#41684e", "#567e62", "#7a9c80"),
    "paint": px.ramp("#0f1813", "#18251d", "#223127", "#2d3f32", "#3a4e3f", "#4a5f4d", "#5d725d"),
    "plaster": px.ramp("#2a2a22", "#3c3b30", "#504e40", "#666352", "#7d7966"),
    "rust": px.ramp("#1c0f08", "#2e190c", "#432511", "#583318", "#6e4420", "#86582a"),
    "steel": px.ramp("#0c1011", "#151b1d", "#20292b", "#2d3739", "#3e4a4a", "#56625f", "#737f78", "#98a29a"),
    "grout": px.ramp("#060807", "#0d110e", "#151a16"),
    "red": px.ramp("#120605", "#1f0a08", "#2e100c", "#3f1711", "#511f16", "#63291c", "#783627"),
    "sheen": px.ramp("#3a4a44", "#56706a", "#7e9c92", "#a8c4b6"),
    "wood": px.ramp("#140c07", "#20140b", "#2e1d10", "#3e2816", "#50351d", "#644426"),
    "brick": px.ramp("#140a08", "#1f100b", "#2c1710", "#3a1f15", "#4a291b", "#5a3322"),
    "stone": px.ramp("#0e100f", "#171a18", "#212522", "#2c312d", "#3a403a", "#4b524a"),
    "lino": px.ramp("#121813", "#1a221b", "#232e24", "#2d3a2e", "#384739", "#455646"),
    "pad": px.ramp("#24231b", "#353326", "#4a4734", "#615c44", "#7a7457", "#948c6c", "#aaa182"),
    "warm": px.ramp("#2a1e10", "#3e2d18", "#554022", "#6e542e", "#88693a", "#a3804a"),
    "sky": px.ramp("#020605", "#06100c", "#0a1a14", "#11261d", "#193428", "#244534"),
    "night": px.ramp("#0a1612", "#12241c", "#1a3428", "#244836", "#305c46", "#3e7258"),
    "cloud": px.ramp("#0c1a14", "#16291f", "#21392b", "#2f4c3a"),
    "moon": px.ramp("#7e9c86", "#b4d0b2", "#dcefd2", "#f4fbe8"),
    "black": px.ramp("#030404", "#080a09", "#0e1110"),
    "brass": px.ramp("#2a1a08", "#4a3010", "#6e4c1a", "#94702c", "#bc9a48"),
    "glass": px.ramp("#0e1a16", "#1a2c26", "#2a4038", "#3e5a50", "#6a8a7e", "#a4c0b4"),
    "liquid": px.ramp("#1e2410", "#323a16", "#4a521e", "#646a28", "#868a3a"),
    "cloth": px.ramp("#141816", "#1f2522", "#2b322e", "#38403b", "#48514a", "#5c665e"),
    "linen": px.ramp("#38392f", "#4e4f42", "#666656", "#80806c", "#9c9a84"),
    "chalk": px.ramp("#0c1410", "#132019", "#1b2c23", "#6e7e72", "#a6b2a6"),
    "light": px.ramp("#5a3a10", "#a06a20", "#e0a440", "#ffd27a", "#fff0c4"),
    "cold": px.ramp("#3c5a50", "#6e9686", "#b4d8c8", "#eafff4"),
    "art_r": px.ramp("#3a120c", "#6a2616", "#9a4422", "#c06838"),
    "art_b": px.ramp("#0e1a2c", "#1c3050", "#2e4a70", "#4a6c90"),
    "art_y": px.ramp("#3a2c0a", "#6a5216", "#9a7c26", "#c4a03e"),
    "art_p": px.ramp("#24142a", "#3e2446", "#5c3a64", "#7c5884"),
    "plastic_t": px.ramp("#0e1e1e", "#18302e", "#244440", "#325a54", "#467468", "#5e8e80"),
    "plastic_b": px.ramp("#262218", "#3a3424", "#504832", "#685e42", "#827656", "#9a8e6c"),
    "plastic_u": px.ramp("#0e1622", "#182436", "#24344a", "#32465e", "#465c74", "#5e7488"),
}
NAMES = list(PAL)


class Canvas:
    """A (material, shade) canvas: draw masks in painter's order, then quantise each material with its palette."""

    def __init__(self, n: int, w: int | None = None):
        self.h, self.w = n, (w or n)
        self.mat = np.full((self.h, self.w), -1, np.int32)
        self.sh = np.zeros((self.h, self.w), np.float32)
        self.y, self.x = np.mgrid[0:self.h, 0:self.w].astype(np.float32)

    def put(self, mask, mat: str, shade) -> None:
        m = np.asarray(mask, bool)
        self.mat[m] = NAMES.index(mat)
        s = shade if np.ndim(shade) else np.full((self.h, self.w), float(shade), np.float32)
        self.sh[m] = np.asarray(s, np.float32)[m]

    def shade(self, mask, delta) -> None:
        m = np.asarray(mask, bool)
        d = delta if np.ndim(delta) else np.full((self.h, self.w), float(delta), np.float32)
        self.sh[m] += np.asarray(d, np.float32)[m]

    # shapes (masks)
    def rect(self, x0, y0, x1, y1):
        return (self.x >= x0) & (self.x < x1) & (self.y >= y0) & (self.y < y1)

    def ell(self, cx, cy, rx, ry):
        return ((self.x - cx) / max(rx, 0.01)) ** 2 + ((self.y - cy) / max(ry, 0.01)) ** 2 <= 1.0

    def seg(self, x0, y0, x1, y1, w):
        dx, dy = x1 - x0, y1 - y0
        L2 = max(dx * dx + dy * dy, 1e-6)
        t = np.clip(((self.x - x0) * dx + (self.y - y0) * dy) / L2, 0, 1)
        d = np.hypot(self.x - (x0 + t * dx), self.y - (y0 + t * dy))
        return d <= w * 0.5

    def rgb(self, dither: float = 1.0) -> np.ndarray:
        out = np.zeros((self.h, self.w, 3), np.uint8)
        for i, name in enumerate(NAMES):
            m = self.mat == i
            if m.any():
                out[m] = _quant(self.sh, PAL[name], dither)[m]
        return out

    def rgba(self) -> np.ndarray:
        return np.dstack([self.rgb(), np.where(self.mat >= 0, 255, 0).astype(np.uint8)])


def _quant(shade, pal, dither: float = 1.0):
    h, w = shade.shape
    k = len(pal) - 1
    b = px.BAYER8[np.arange(h)[:, None] % 8, np.arange(w)[None, :] % 8]
    i = np.clip(np.round(np.clip(shade, 0, 1) * k + b * dither), 0, k).astype(int)
    return (pal[i] * 255 + 0.5).astype(np.uint8)


def _noise(n, scale, seed, octaves=3, w=None):
    """Tileable noise; for a non-square canvas, tile a square field."""
    v = px.noise(n, scale, seed, octaves)
    if w and w != n:
        v = np.tile(v, (1, w // n + 1))[:, :w]
    return v


def _streaks(c: Canvas, xs, y0s, lengths, seed, width=2.0):
    """Rust/grime streaks running down from points: a 0..1 field."""
    rng = np.random.RandomState(seed)
    f = np.zeros((c.h, c.w), np.float32)
    for x0, y0, L in zip(xs, y0s, lengths):
        L = L * (0.35 + 0.65 * rng.rand())
        wob = np.sin(c.y * 0.35 + rng.rand() * 6) * 0.6
        dx = np.abs(((c.x - x0 - wob + c.w / 2) % c.w) - c.w / 2)
        t = (c.y - y0) / max(L, 1)
        wid = width * (1.0 - 0.6 * np.clip(t, 0, 1))
        m = (dx < wid) & (t >= 0) & (t <= 1)
        f = np.maximum(f, np.where(m, (1 - np.clip(t, 0, 1)) * (1 - dx / (wid + 0.01) * 0.5), 0))
    return f


# ---- wall pieces ----------------------------------------------------------------------------------------------------------------------------------

def _glazed(c: Canvas, region, tw, th, seed, stagger=True, base=0.5):
    """Glazed rectangular tiles with grout in a region; returns the grout mask."""
    r = np.floor(c.y / th)
    off = (r % 2) * (tw / 2) if stagger else 0
    lx = (c.x + off) % tw
    ly = c.y % th
    col = np.floor(((c.x + off) % c.w) / tw)
    rng = np.random.RandomState(seed)
    tone = rng.rand(64, 64).astype(np.float32)
    t = tone[r.astype(int) % 64, col.astype(int) % 64]
    grout = (lx < 1) | (ly < 1)
    sh = base + 0.1 * (t - 0.5) + 0.18 * ((lx < 2) | (ly < 2)) - 0.1 * ((lx > tw - 2) | (ly > th - 2))
    sh += 0.16 * np.clip(1 - (lx + ly * 2) / (tw * 0.5), 0, 1)  # the glaze catches the light at the upper left
    sh += (_noise(c.h, 16, seed + 1, w=c.w) - 0.5) * 0.16
    chip = (_noise(c.h, 5, seed + 2, w=c.w) > 0.8) & region
    c.put(region, "tile", sh)
    c.put(region & chip, "plaster", 0.35 + 0.3 * t)  # chipped glaze shows the body
    c.put(region & grout, "grout", 0.4 + 0.4 * t)
    return region & grout


def _plaster(c: Canvas, region, seed, base=0.5):
    """Painted plaster, peeling to bare plaster in patches, with water stains."""
    n1 = _noise(c.h, 20, seed, 4, w=c.w)
    sh = base + (n1 - 0.5) * 0.35 + (_noise(c.h, 4, seed + 3, w=c.w) - 0.5) * 0.12
    c.put(region, "paint", sh)
    peel = (_noise(c.h, 10, seed + 5, 3, w=c.w) > 0.7) & region
    edge = (_noise(c.h, 10, seed + 5, 3, w=c.w) > 0.66) & region & ~peel
    c.put(peel, "plaster", 0.45 + (n1 - 0.5) * 0.5)
    c.shade(edge, 0.25)  # the lifted edge of the paint catches light
    stain = _noise(c.h, 26, seed + 9, 3, w=c.w)
    c.shade(region & (stain > 0.62), -0.22)


def _pipe_h(c: Canvas, yc, r, seed, mat="steel", brackets=32, rusty=0.5):
    """A horizontal pipe along the wall, centre row yc, radius r px, with brackets and rust; returns its mask."""
    u = (c.y - yc) / r
    m = np.abs(u) <= 1.0
    sh = 0.62 - 0.38 * u + 0.25 * (np.sqrt(np.clip(1 - u * u, 0, 1)) - 0.6)
    c.put(m, mat, sh)
    rs = (_noise(c.h, 6, seed, w=c.w) > 1 - rusty * 0.45) & m
    c.put(rs, "rust", 0.3 + 0.5 * np.clip(1 - u, 0, 1) * 0.5)
    br = (np.abs(((c.x + brackets / 2) % brackets) - brackets / 2) < 1.6) & (np.abs(c.y - yc) <= r + 1.5)
    c.put(br, "steel", 0.3 - 0.15 * (c.y > yc))
    return m | br


def _skirting(c: Canvas, y0):
    m = c.y >= y0
    c.put(m, "black", 0.6 - (c.y - y0) * 0.05)
    c.put(m & (c.y < y0 + 1), "tile", 0.2)


def _grime_low(c: Canvas, y_top, seed, amount=0.35):
    """Rising damp: darker towards the floor."""
    g = np.clip((c.y - y_top) / max(c.h - y_top, 1), 0, 1) * amount
    g *= 0.6 + 0.8 * _noise(c.h, 18, seed, w=c.w)
    c.sh -= g


def _rust_streaks(c: Canvas, xs, y0, length, seed, width=1.8):
    f = _streaks(c, xs, [y0] * len(xs), [length] * len(xs), seed, width)
    m = (f > 0.3) & (px.speckle(c.h, 0.85, seed + 1)[:, :c.w] > 0.5)
    target = m & (c.mat != NAMES.index("black"))
    c.put(target, "rust", 0.05 + 0.4 * f)


def ward_wall(n, metres, seed, dado_m=1.25, pipes=((0.22, 0.07), (0.38, 0.045)), tile_wh=(16, 8), streak_xs=None, skirt=True):
    """The Ward's wall: green glazed tile up to a dado, peeling painted plaster above, pipes under the ceiling, rust streaks from the brackets."""
    c = Canvas(n)
    ppm = n / metres
    y_dado = n - dado_m * ppm
    _plaster(c, c.y < y_dado, seed)
    _glazed(c, c.y >= y_dado + 3, tile_wh[0], tile_wh[1], seed + 1)
    rail = (c.y >= y_dado) & (c.y < y_dado + 3)
    c.put(rail, "tile", np.where(c.y < y_dado + 1, 0.85, 0.25))
    for k, (ym, rm) in enumerate(pipes):
        _pipe_h(c, ym * ppm, max(rm * ppm, 2.0), seed + 10 + k, rusty=0.6)
    xs = streak_xs if streak_xs is not None else [n * 0.25 - 1, n * 0.75 - 1, n * 0.08, n * 0.56]
    _rust_streaks(c, xs, pipes[0][0] * ppm + 3 if pipes else y_dado, n * 0.5, seed + 20)
    _rust_streaks(c, [n * 0.4, n * 0.9], y_dado + 3, n * 0.25, seed + 21, width=1.4)
    if skirt:
        _skirting(c, n - max(int(0.1 * ppm), 3))
    _grime_low(c, y_dado - 6, seed + 30, 0.3)
    return c


def _door(c: Canvas, x0, x1, y_top, y_bot, seed, number=None, hatch=True, paint="paint", warm_hatch=False):
    """A steel door with peeling paint, a frame, a barred hatch, a handle and a rusty kick plate."""
    frame = c.rect(x0 - 3, y_top - 3, x1 + 3, y_bot)
    c.put(frame, "steel", 0.28 + 0.1 * (c.x < x0 - 1))
    slab = c.rect(x0, y_top, x1, y_bot)
    nn = _noise(c.h, 10, seed, w=c.w)
    c.put(slab, paint, 0.42 + (nn - 0.5) * 0.3 + 0.12 * (c.x < x0 + 2) - 0.12 * (c.x > x1 - 3))
    peel = slab & (_noise(c.h, 7, seed + 1, w=c.w) > 0.66)
    c.put(peel, "steel", 0.45 + (nn - 0.5) * 0.4)
    c.put(peel & (_noise(c.h, 5, seed + 2, w=c.w) > 0.62), "rust", 0.45)
    # panels pressed into the slab
    mid = (x0 + x1) / 2
    for (py0, py1) in ((y_top + (y_bot - y_top) * 0.42, y_top + (y_bot - y_top) * 0.47),):
        c.shade(c.rect(x0 + 3, py0, x1 - 3, py1), -0.18)
    if hatch:
        hx0, hx1 = mid - (x1 - x0) * 0.22, mid + (x1 - x0) * 0.22
        hy0, hy1 = y_top + (y_bot - y_top) * 0.12, y_top + (y_bot - y_top) * 0.3
        c.put(c.rect(hx0 - 1, hy0 - 1, hx1 + 1, hy1 + 1), "steel", 0.2)
        inner = c.rect(hx0, hy0, hx1, hy1)
        if warm_hatch:
            c.put(inner, "light", 0.35 + 0.3 * (c.y - hy0) / max(hy1 - hy0, 1))
        else:
            c.put(inner, "black", 0.5 + 0.5 * (c.y - hy0) / max(hy1 - hy0, 1))
        bars = inner & ((np.floor(c.x - hx0) % 4) < 1)
        c.put(bars, "steel", 0.55)
    # handle and lock
    hx = x1 - 5
    hy = y_top + (y_bot - y_top) * 0.52
    c.put(c.rect(hx - 1, hy - 4, hx + 2, hy + 4), "steel", 0.35)
    c.put(c.rect(hx - 4, hy - 1, hx + 2, hy + 1), "steel", 0.85)
    c.put(c.rect(hx - 1, hy + 6, hx + 2, hy + 9), "brass", 0.5)
    # kick plate
    kp = c.rect(x0 + 1, y_bot - (y_bot - y_top) * 0.1, x1 - 1, y_bot)
    c.put(kp, "steel", 0.4 + (nn - 0.5) * 0.3)
    c.put(kp & (_noise(c.h, 4, seed + 7, w=c.w) > 0.55), "rust", 0.4)
    if number is not None:
        ny = y_top + (y_bot - y_top) * 0.05
        c.put(c.rect(mid - 4, ny, mid + 4, ny + 4), "plaster", 0.75)
        for k in range(number):
            c.put(c.rect(mid - 3 + k * 2, ny + 1, mid - 2 + k * 2, ny + 3), "black", 0.2)


def _radiator(c: Canvas, x0, x1, y0, y1, seed):
    """A cast-iron column radiator with a pipe and a valve."""
    m = c.rect(x0, y0, x1, y1)
    fin = (np.floor(c.x - x0) % 4)
    sh = 0.32 + 0.3 * (fin < 1) - 0.18 * (fin == 3) + 0.2 * (c.y < y0 + 2) - 0.15 * (c.y > y1 - 3)
    c.put(m, "steel", sh)
    c.put(m & (fin == 3), "black", 0.4)
    c.put(m & (_noise(c.h, 5, seed, w=c.w) > 0.72), "rust", 0.4)
    c.put(c.rect(x0 + 1, y1, x0 + 3, y1 + 4) | c.rect(x1 - 3, y1, x1 - 1, y1 + 4), "steel", 0.2)
    c.put(c.rect(x1, y1 - 6, x1 + 6, y1 - 3), "steel", 0.5)
    c.put(c.rect(x1 + 3, y1 - 9, x1 + 6, y1 - 6), "rust", 0.6)


def _barred_window(c: Canvas, x0, x1, y0, y1, seed, cols=4, rows=5, moon=None, trees=True, sky_shift=0):
    """A window of small panes in a steel grid with bars, onto a moonlit sky with bare trees and clouds."""
    W, H = x1 - x0, y1 - y0
    win = c.rect(x0, y0, x1, y1)
    fy = (c.y - y0) / max(H, 1)
    sky = 0.3 + 0.6 * fy
    if moon is not None:
        sky += 0.35 * np.clip(1 - np.hypot(c.x - moon[0], c.y - moon[1]) / (W * 0.5), 0, 1)  # the sky is lighter round the moon
    sky += (_noise(c.h, 12, seed, w=c.w) - 0.5) * 0.12
    c.put(win, "night", sky)
    clouds = win & (_noise(c.h, 18, seed + 1, 4, w=c.w) + fy * 0.1 > 0.6)
    c.put(clouds, "cloud", 0.3 + (_noise(c.h, 6, seed + 2, w=c.w) - 0.3))
    stars = win & (px.speckle(c.h, 0.012, seed + 3)[:, :c.w] > 0.5) & (fy < 0.6) & ~clouds
    c.put(stars, "moon", 0.35)
    if moon is not None:
        mx, my, mr = moon
        halo = c.ell(mx, my, mr * 2.4, mr * 2.4) & win
        c.put(halo & ~c.ell(mx, my, mr, mr), "cloud", 0.95 - np.hypot(c.x - mx, c.y - my) / (mr * 2.4) * 0.6)
        disc = c.ell(mx, my, mr, mr) & win
        c.put(disc, "moon", 0.95 - 0.35 * ((c.x - mx + c.y - my) / (2 * mr) + 0.5) + (_noise(c.h, 4, seed + 4, w=c.w) - 0.5) * 0.4)
    if trees:
        rng = np.random.RandomState(seed + 5)
        ground = y1 - H * 0.18
        hill = win & (c.y > ground + np.sin(c.x * 0.08 + seed) * 2)
        c.put(hill, "black", 0.6)
        for k in range(3):
            tx = x0 + W * (0.15 + 0.35 * k) + rng.rand() * 6
            top = y0 + H * (0.25 + rng.rand() * 0.25)
            c.put(win & c.seg(tx, ground + 2, tx + rng.randn(), top, 2.2), "black", 0.7)
            for b in range(5):
                by = top + (ground - top) * (0.1 + 0.15 * b)
                ang = (-1) ** b * (0.6 + rng.rand() * 0.7)
                L = 4 + rng.rand() * 7
                c.put(win & c.seg(tx, by, tx + np.sin(ang) * L, by - np.cos(abs(ang)) * L, 1.2), "black", 0.8)
    # the steel grid and the bars
    gx = W / cols
    gy = H / rows
    lx = (c.x - x0) % gx
    ly = (c.y - y0) % gy
    grid = win & ((lx < 1.5) | (ly < 1.5))
    c.put(grid, "steel", 0.22 + 0.15 * (lx < 0.8))
    bars = win & (np.abs(((c.x - x0) % (gx / 2)) - gx / 4) < 0.8)
    c.put(bars, "black", 0.9)
    c.put(c.rect(x0 - 3, y0 - 3, x1 + 3, y0) | c.rect(x0 - 3, y1, x1 + 3, y1 + 3) | c.rect(x0 - 3, y0, x0, y1) | c.rect(x1, y0, x1 + 3, y1), "steel", 0.3)
    c.put(c.rect(x0 - 5, y1 + 3, x1 + 5, y1 + 5), "plaster", 0.45)  # sill


# ---- the tiles ------------------------------------------------------------------------------------------------------------------------------------

def t_wall_mint():
    """The day room (3.0 m): tile to 1.3 m, peeling green plaster, two pipes under the ceiling."""
    return ward_wall(128, 3.0, 101, dado_m=1.3).rgb()


def t_wall_dado():
    """The dormitory (2.2 m): low tile, plaster, one pipe."""
    return ward_wall(128, 2.2, 111, dado_m=1.05, pipes=((0.16, 0.05),)).rgb()


def t_tx_tile():
    """The treatment room (walls and ceiling, 2.3 m): small green tile floor to ceiling, rusty, one pipe."""
    n = 128
    c = Canvas(n)
    _glazed(c, c.y >= 0, 12, 12, 121, stagger=False, base=0.55)
    _pipe_h(c, 10, 3.0, 122, rusty=0.8)
    _rust_streaks(c, [20, 60, 98, 118], 13, 80, 123, width=2.2)
    _rust_streaks(c, [40, 84], 60, 50, 124, width=1.6)
    c.sh -= np.clip(_noise(n, 24, 125, 4) - 0.55, 0, 1) * 0.8
    _grime_low(c, 80, 126, 0.3)
    return c.rgb()


def _red_floor(n, count, seed, wet=0.5, dark=0.0, drain=False):
    c = Canvas(n)
    s = n / count
    lx, ly = c.x % s, c.y % s
    rng = np.random.RandomState(seed)
    tone = rng.rand(count, count).astype(np.float32)
    t = tone[(c.y // s).astype(int) % count, (c.x // s).astype(int) % count]
    sh = 0.5 + 0.22 * (t - 0.5) + 0.16 * ((lx < 2) | (ly < 2)) - 0.14 * ((lx > s - 2) | (ly > s - 2)) - dark
    sh += (_noise(n, 12, seed + 1) - 0.5) * 0.22
    sh -= np.clip(px.grime(n, seed + 2, 0.6, drip=False), 0, 1) * 0.35
    c.put(c.y >= 0, "red", sh)
    cracked = (rng.rand(count, count) > 0.82)[(c.y // s).astype(int) % count, (c.x // s).astype(int) % count]
    crack = cracked & (np.abs((lx - ly * 0.8) - s * 0.15 - np.sin(ly * 0.9) * 1.2) < 0.7)
    c.put(crack, "grout", 0.5)
    grout = (lx < 1) | (ly < 1)
    c.put(grout, "grout", 0.6 + 0.3 * _noise(n, 6, seed + 3))
    wetf = _noise(n, 22, seed + 4, 3)
    sheen = (wetf > 1 - wet * 0.5) & ~grout & (((lx < 3) & (ly < 3)) | (px.speckle(n, 0.07, seed + 5) > 0.5))
    c.put(sheen, "sheen", 0.2 + 0.6 * (wetf - (1 - wet * 0.5)) / max(wet * 0.5, 0.01))
    if drain:
        d = c.ell(n / 2, n / 2, 7, 7)
        c.put(d, "steel", 0.35)
        c.put(d & ((c.x.astype(int) % 3) == 0), "black", 0.3)
        c.put(d & ~c.ell(n / 2, n / 2, 5.5, 5.5), "rust", 0.5)
    return c.rgb()


def t_floor_check():
    """The day room floor: dark red tiles, grout, a wet sheen."""
    return _red_floor(128, 8, 131, wet=0.6)


def t_tx_floor():
    """The treatment room floor: smaller, darker red tiles round a drain."""
    return _red_floor(64, 6, 141, wet=0.8, dark=0.08, drain=True)


def t_floor_wood():
    """Worn institutional lino (corridor, dormitory, office): a scuffed path, seams, cigarette burns."""
    n = 128
    c = Canvas(n)
    nn = _noise(n, 18, 151, 4)
    sh = 0.5 + (nn - 0.5) * 0.3 + (_noise(n, 3, 152) - 0.5) * 0.12
    path = np.exp(-((c.x - n / 2) / (n * 0.28)) ** 2)  # the worn track down the middle (the corridor runs along x, but lino has no direction)
    sh -= 0.12 * path * (0.5 + nn)
    c.put(c.y >= 0, "lino", sh)
    tiles = ((c.x % 32) < 1) | ((c.y % 32) < 1)
    c.put(tiles, "lino", 0.12)
    burns = px.speckle(n, 0.004, 153) > 0.5
    c.put(burns, "black", 0.5)
    scuff = (np.abs(np.sin(c.x * 0.3 + c.y * 0.05 + nn * 8)) < 0.04) & (_noise(n, 10, 154) > 0.55)
    c.put(scuff, "lino", 0.75)
    patch = c.rect(70, 40, 100, 70)
    c.put(patch, "lino", 0.3 + (nn - 0.5) * 0.2)
    c.put(patch & ~c.rect(71, 41, 99, 69), "black", 0.4)
    wetf = _noise(n, 24, 155)
    c.put((wetf > 0.7) & (px.speckle(n, 0.06, 156) > 0.5), "sheen", 0.15)
    return c.rgb()


def t_floor_art():
    """The art room floor: worn lino spattered with paint (the residents' colours are the warmth)."""
    n = 128
    c = Canvas(n)
    nn = _noise(n, 18, 161, 4)
    c.put(c.y >= 0, "lino", 0.55 + (nn - 0.5) * 0.35)
    c.put(((c.x % 32) < 1) | ((c.y % 32) < 1), "lino", 0.15)
    rng = np.random.RandomState(162)
    for k in range(26):
        cx, cy, r = rng.rand() * n, rng.rand() * n, 1 + rng.rand() * 3.5
        mat = ["art_r", "art_b", "art_y", "art_p", "plaster"][k % 5]
        blob = c.ell(cx, cy, r, r * (0.6 + rng.rand() * 0.6))
        for dx in (-n, 0, n):
            for dy in (-n, 0, n):
                blob = blob | c.ell(cx + dx, cy + dy, r, r)
        c.put(blob, mat, 0.45 + rng.rand() * 0.3)
        for j in range(3):
            sx, sy = cx + rng.randn() * r * 2.5, cy + rng.randn() * r * 2.5
            c.put(c.ell(sx % n, sy % n, 0.8, 0.8), mat, 0.5)
    return c.rgb()


def _ceiling(n, seed, tubes=False, panels=True):
    c = Canvas(n)
    nn = _noise(n, 20, seed, 4)
    c.put(c.y >= 0, "plaster", 0.42 + (nn - 0.5) * 0.3)
    if panels:
        s = n / 4
        c.put(((c.x % s) < 1.5) | ((c.y % s) < 1.5), "steel", 0.2)
        rng = np.random.RandomState(seed + 1)
        miss = rng.rand(4, 4) > 0.86
        hole = miss[(c.y // s).astype(int) % 4, (c.x // s).astype(int) % 4] & ((c.x % s) >= 1.5) & ((c.y % s) >= 1.5)
        c.put(hole, "black", 0.3 + 0.3 * _noise(n, 4, seed + 2))
        dot = (px.speckle(n, 0.08, seed + 7) > 0.5) & ~hole
        c.shade(dot, -0.12)
    stain = _noise(n, 28, seed + 3, 3)
    c.shade((stain > 0.6) & (c.mat == NAMES.index("plaster")), -0.25)
    ring = (np.abs(stain - 0.6) < 0.012) & (c.mat == NAMES.index("plaster"))
    c.put(ring, "rust", 0.1)
    crack = np.abs(_noise(n, 16, seed + 4, 2) - 0.5) < 0.012
    c.put(crack & (c.mat == NAMES.index("plaster")), "black", 0.4)
    if tubes:
        for x0 in (n * 0.18,):
            hous = c.rect(x0, n * 0.1, x0 + 10, n * 0.9)
            c.put(hous, "steel", 0.35)
            c.put(c.rect(x0 + 2, n * 0.12, x0 + 4, n * 0.88) | c.rect(x0 + 6, n * 0.12, x0 + 8, n * 0.88), "cold", 0.75 + 0.25 * np.sin(c.y * 0.2) ** 2)
            c.put(c.rect(x0 + 2, n * 0.55, x0 + 4, n * 0.6), "black", 0.4)  # a dead stretch of tube
    return c.rgb()


def t_ceil_tile():
    return _ceiling(128, 171)


def t_ceil_pale():
    """Corridor, office and dormitory ceiling: stained panels with a fluorescent tube fitting (the flicker is in the map's `animated`)."""
    return _ceiling(128, 181, tubes=True)


def t_pad_tile():
    """The padded cell: buttoned, stained cream padding."""
    n = 64
    c = Canvas(n)
    s = n / 2
    lx, ly = c.x % s, c.y % s
    d = np.hypot(lx - s / 2, ly - s / 2) / (s / 2)
    sh = 0.62 - 0.25 * d ** 2 + 0.12 * ((lx + ly) < s * 0.7)
    sh += (_noise(n, 8, 191) - 0.5) * 0.15
    c.put(c.y >= 0, "pad", sh)
    seams = (lx < 1.5) | (ly < 1.5)
    c.put(seams, "pad", 0.12)
    btn = np.hypot(lx - s / 2, ly - s / 2) < 1.6
    c.put(btn, "pad", 0.05)
    stain = _noise(n, 14, 192, 3)
    c.put((stain > 0.62) & ~seams, "pad", sh - 0.25)
    c.put((stain > 0.72) & ~seams, "rust", 0.35)
    tear = c.seg(40, 8, 50, 20, 1.2)
    c.put(tear, "linen", 0.8)
    return c.rgb()


def t_wall_cdoor():
    """Corridor south wall (2.7 m): a locked steel door, then tile and a radiator under the pipe."""
    n = 128
    m = 2.7
    c = ward_wall(n, m, 201, dado_m=1.2, pipes=((0.14, 0.06),), streak_xs=[90, 118])
    ppm = n / m
    _door(c, 14, 50, n - 2.05 * ppm, n - 3, 202, number=3)
    _radiator(c, 74, 108, n - 0.9 * ppm, n - 0.2 * ppm, 203)
    return c.rgb()


def t_wall_cdoor2():
    """Corridor north wall (2.7 m): another locked door, a fire-hose reel box, a notice."""
    n = 128
    m = 2.7
    c = ward_wall(n, m, 211, dado_m=1.2, pipes=((0.14, 0.06), (0.26, 0.035)), streak_xs=[30, 100])
    ppm = n / m
    _door(c, 70, 106, n - 2.05 * ppm, n - 3, 212, number=2)
    box = c.rect(16, n - 1.9 * ppm, 40, n - 1.25 * ppm)
    c.put(box, "art_r", 0.25 + 0.15 * (c.x < 18))
    c.put(c.ell(28, n - 1.58 * ppm, 7, 7) & box, "black", 0.5)
    c.put(c.ell(28, n - 1.58 * ppm, 2, 2), "steel", 0.6)
    note = c.rect(46, n - 1.95 * ppm, 58, n - 1.6 * ppm)
    c.put(note, "plaster", 0.7 + (_noise(n, 3, 213) - 0.5) * 0.3)
    c.put(note & ((c.y.astype(int) % 3) == 0) & (c.x > 47) & (c.x < 56), "black", 0.3)
    return c.rgb()


def t_wall_door():
    """A steel door with peeling paint in a tiled wall (the day room door, 3.0 m)."""
    n = 128
    m = 3.0
    c = ward_wall(n, m, 221, dado_m=1.3, pipes=((0.22, 0.07),), streak_xs=[110])
    ppm = n / m
    _door(c, 38, 90, n - 2.1 * ppm, n - 3, 222, number=1)
    return c.rgb()


def t_wall_office():
    """The one warm room: wood panelling, yellowed plaster, a calendar, a shelf of files (2.7 m)."""
    n = 128
    m = 2.7
    ppm = n / m
    c = Canvas(n)
    yd = n - 1.0 * ppm
    nn = _noise(n, 16, 231, 4)
    c.put(c.y < yd, "warm", 0.55 + (nn - 0.5) * 0.3)
    c.shade((c.y < yd) & (_noise(n, 26, 232, 3) > 0.62), -0.2)
    pan = c.y >= yd
    c.put(pan, "wood", 0.5 + 0.2 * np.sin(c.x * 0.6 + nn * 6) * 0.5 + (nn - 0.5) * 0.2)
    c.put(pan & ((c.x % 32) < 1.5), "wood", 0.1)
    c.put(c.rect(0, yd, n, yd + 2), "wood", 0.85)
    shelf_y = n - 1.95 * ppm
    c.put(c.rect(10, shelf_y, 80, shelf_y + 2), "wood", 0.7)
    rng = np.random.RandomState(233)
    x = 12
    while x < 76:
        w = 3 + rng.randint(3)
        h = 10 + rng.randint(7)
        mat = ["art_r", "art_b", "wood", "plaster", "art_y", "cloth"][rng.randint(6)]
        c.put(c.rect(x, shelf_y - h, x + w, shelf_y), mat, 0.3 + rng.rand() * 0.3)
        c.put(c.rect(x, shelf_y - h, x + 1, shelf_y), mat, 0.7)
        x += w + (1 if rng.rand() < 0.8 else 4)
    cal = c.rect(92, n - 2.0 * ppm, 112, n - 1.45 * ppm)
    c.put(cal, "plaster", 0.85)
    c.put(c.rect(92, n - 2.0 * ppm, 112, n - 1.86 * ppm), "art_r", 0.5)
    c.put(cal & ((c.x.astype(int) % 4) == 0) & ((c.y.astype(int) % 4) == 0) & (c.y > n - 1.84 * ppm), "black", 0.3)
    _pipe_h(c, 6, 2.5, 234, rusty=0.4)
    _grime_low(c, yd, 235, 0.2)
    return c.rgb()


def t_wall_end():
    """The office's back wall: a window with half-open blinds onto the night, a filing cabinet, a shelf of jars."""
    n = 128
    m = 3.0
    ppm = n / m
    c = Canvas(n)
    nn = _noise(n, 16, 241, 4)
    c.put(c.y >= 0, "warm", 0.55 + (nn - 0.5) * 0.3)
    yd = n - 1.0 * ppm
    c.put(c.y >= yd, "wood", 0.45 + (nn - 0.5) * 0.25)
    c.put(c.rect(0, yd, n, yd + 2), "wood", 0.85)
    _barred_window(c, 20, 76, 22, 62, 242, cols=2, rows=2, moon=(64, 32, 4), trees=True)
    bl = c.rect(20, 22, 76, 42) & ((c.y.astype(int) % 3) < 2)
    c.put(bl, "plaster", 0.55 + 0.25 * ((c.y.astype(int) % 3) == 0))
    cab = c.rect(86, n - 1.3 * ppm, 116, n - 2)
    c.put(cab, "steel", 0.45 + (nn - 0.5) * 0.2)
    for k in range(3):
        y0 = n - 1.3 * ppm + 2 + k * (1.3 * ppm - 4) / 3
        c.put(c.rect(88, y0, 114, y0 + 1), "black", 0.4)
        c.put(c.rect(98, y0 + 5, 104, y0 + 7), "brass", 0.6)
    sy = n - 2.15 * ppm
    c.put(c.rect(84, sy, 120, sy + 2), "wood", 0.6)
    for k, x in enumerate((86, 93, 100, 108, 114)):
        jar = c.rect(x, sy - 9 + (k % 2) * 2, x + 5, sy)
        c.put(jar, "glass", 0.55)
        c.put(jar & (c.y > sy - 5), "liquid", 0.5 + 0.1 * k)
        c.put(c.rect(x, sy - 10 + (k % 2) * 2, x + 5, sy - 9 + (k % 2) * 2), "brass", 0.5)
    return c.rgb()


def t_wall_window():
    """The day room's tall barred window onto the moon (3.0 m)."""
    n = 128
    c = ward_wall(n, 3.0, 251, dado_m=1.3, pipes=((0.1, 0.05),), streak_xs=[4, 124])
    _barred_window(c, 14, 114, 12, 82, 252, cols=5, rows=4, moon=(84, 30, 7))
    return c.rgb()


def t_wall_awindow():
    """The art room's big gridded window wall (4.6 m): steel grid, moon, clouds and bare trees beyond."""
    n = 128
    c = ward_wall(n, 4.6, 261, dado_m=1.0, pipes=(), streak_xs=[2, 126])
    _barred_window(c, 8, 120, 6, 88, 262, cols=6, rows=6, moon=(92, 24, 8))
    return c.rgb()


def t_wall_dwindow():
    """The dormitory alcove (1.8 m): a barred window over a radiator."""
    n = 128
    c = ward_wall(n, 1.8, 271, dado_m=0.7, pipes=(), streak_xs=[6, 122])
    _barred_window(c, 18, 110, 10, 60, 272, cols=4, rows=3, moon=(40, 24, 6))
    _radiator(c, 36, 92, 86, 112, 273)
    return c.rgb()


def t_wall_slit():
    """The quiet room's slit window (0.9 m): bars over the moonlit sky."""
    n = 64
    c = Canvas(n)
    _plaster(c, c.y >= 0, 281)
    _barred_window(c, 6, 58, 6, 52, 282, cols=2, rows=2, moon=(40, 18, 5), trees=False)
    return c.rgb()


def t_wall_art():
    """The art room walls (4.6 m): plaster with the residents' paintings pinned up (the warmth), pipes high, tile below."""
    n = 128
    m = 4.6
    ppm = n / m
    c = ward_wall(n, m, 291, dado_m=1.0, pipes=((0.3, 0.08), (0.48, 0.05)), streak_xs=[20, 70, 110])
    rng = np.random.RandomState(292)
    spots = [(8, 1.5, 22, 18), (36, 1.7, 18, 24), (60, 1.4, 26, 20), (92, 1.8, 20, 16), (14, 2.5, 16, 14), (70, 2.6, 22, 16), (100, 2.45, 18, 20)]
    for k, (x, hm, w, h) in enumerate(spots):
        y1 = n - hm * ppm
        y0 = y1 - h
        pap = c.rect(x, y0, x + w, y1)
        c.put(pap, "linen", 0.65 + (_noise(n, 4, 293 + k) - 0.5) * 0.3)
        a, b = ["art_r", "art_b", "art_y", "art_p"][k % 4], ["art_y", "art_r", "art_b", "art_p"][(k + 1) % 4]
        cx, cy = x + w * (0.3 + rng.rand() * 0.4), y0 + h * (0.3 + rng.rand() * 0.4)
        c.put(c.ell(cx, cy, w * 0.25, h * 0.25) & pap, a, 0.5 + 0.2 * rng.rand())
        c.put(c.seg(x + 2, y1 - 3, x + w - 2, y1 - 4 - rng.rand() * h * 0.3, 2) & pap, b, 0.55)
        if k % 3 == 0:  # a face: two eyes and a mouth
            c.put((c.ell(cx - 2, cy - 1, 0.8, 0.8) | c.ell(cx + 2, cy - 1, 0.8, 0.8) | c.rect(cx - 2, cy + 2, cx + 2, cy + 3)) & pap, "black", 0.3)
        c.put(c.rect(x + w / 2 - 1, y0 - 1, x + w / 2 + 1, y0 + 1), "steel", 0.8)  # the drawing pin
    return c.rgb()


def t_wall_brick():
    """The courtyard walls (3.2 m): dark brick, a stone coping, a drainpipe, rust and damp."""
    n = 128
    m = 3.2
    c = Canvas(n)
    sh, mort = px.bricks(n, rows=16, cols=6, seed=301, wear=0.5)
    c.put(c.y >= 0, "brick", sh)
    c.put(mort > 0.5, "grout", 0.8)
    c.put(c.y < 7, "stone", 0.5 + (_noise(n, 6, 302) - 0.5) * 0.4 - 0.25 * (c.y > 5))
    dp = c.rect(100, 7, 106, n)
    c.put(dp, "steel", 0.25 + 0.35 * (c.x < 102))
    c.put(dp & ((c.y.astype(int) % 32) < 3), "steel", 0.6)
    c.put(dp & (_noise(n, 5, 303) > 0.6), "rust", 0.45)
    _rust_streaks(c, [103, 30, 64], 8, 90, 304, width=2.5)
    c.sh -= px.grime(n, 305, 0.7) * 0.35
    _grime_low(c, 70, 306, 0.4)
    moss = (c.y > n - 14) & (_noise(n, 5, 307) > 0.58)
    c.put(moss, "tile", 0.25)
    return c.rgb()


def t_wall_archdoor():
    """The courtyard stage's back wall (3.0 m): a heavy steel door under a brick arch, a caged lamp above."""
    n = 128
    c = Canvas(n)
    sh, mort = px.bricks(n, rows=16, cols=6, seed=311, wear=0.5)
    c.put(c.y >= 0, "brick", sh)
    c.put(mort > 0.5, "grout", 0.8)
    arch = c.rect(36, 40, 92, n) | c.ell(64, 40, 28, 18)
    c.put(arch, "stone", 0.35)
    _door(c, 40, 88, 30, n - 2, 312, number=None, hatch=True, paint="steel")
    c.put(c.ell(64, 40, 24, 14) & (c.y < 40), "steel", 0.3)
    c.put(c.ell(64, 40, 24, 14) & (c.y < 40) & ((c.x.astype(int) % 6) < 1), "black", 0.5)
    _rust_streaks(c, [44, 84], 40, 70, 313, width=2)
    c.sh -= px.grime(n, 314, 0.6) * 0.3
    return c.rgb()


def t_floor_paving():
    """The courtyard: dark wet flagstones with moss in the joints and puddles catching the sky."""
    n = 128
    c = Canvas(n)
    sh, mort = px.bricks(n, rows=4, cols=3, mortar=2, seed=321, wear=0.6)
    c.put(c.y >= 0, "stone", sh * 0.9)
    c.put(mort > 0.5, "grout", 0.5)
    c.put((mort > 0.5) & (_noise(n, 5, 322) > 0.55), "tile", 0.2)
    pud = _noise(n, 30, 323, 3)
    pm = pud > 0.62
    c.put(pm, "sky", 0.55 + (pud - 0.62) * 2)
    c.put(pm & (px.speckle(n, 0.04, 324) > 0.5), "sheen", 0.3)
    c.put((np.abs(pud - 0.62) < 0.01), "sheen", 0.15)
    return c.rgb()


def t_floor_dais():
    """The stages: old scuffed boards with dark joints and nail heads."""
    n = 64
    c = Canvas(n)
    sh, joint = px.planks(n, count=6, seed=331)
    c.put(c.y >= 0, "wood", sh * 0.9)
    c.put(joint > 0.5, "black", 0.5)
    nails = (((c.x.astype(int) % 32) == 3) | ((c.x.astype(int) % 32) == 28)) & ((c.y.astype(int) % 11) == 5)
    c.put(nails, "steel", 0.6)
    c.sh -= px.grime(n, 332, 0.5, drip=False) * 0.25
    return c.rgb()


def t_wall_speaker():
    """An old PA cabinet built into the wall: cloth grille, tape on a tear."""
    n = 64
    c = Canvas(n)
    c.put(c.y >= 0, "wood", 0.3 + (_noise(n, 10, 341) - 0.5) * 0.2)
    gr = c.rect(6, 6, 58, 58)
    c.put(gr, "cloth", 0.3 + 0.25 * (((c.x + c.y).astype(int) % 2) == 0))
    for cy, r in ((22, 13), (46, 9)):
        c.shade(c.ell(32, cy, r, r) & gr, -0.15)
        c.shade(c.ell(32, cy, r * 0.35, r * 0.35) & gr, -0.1)
    c.put(c.rect(40, 50, 54, 54), "plaster", 0.7)
    return c.rgb()


def t_wall_led():
    """The day room's stage wall when the screen is off: a chalk board with a timetable."""
    n = 64
    c = Canvas(n)
    c.put(c.y >= 0, "chalk", 0.25 + (_noise(n, 12, 351) - 0.5) * 0.2)
    rng = np.random.RandomState(352)
    for k in range(6):
        y = 10 + k * 8
        x0 = 6 + rng.randint(4)
        c.put(c.rect(x0, y, x0 + 18 + rng.randint(22), y + 1), "chalk", 0.85)
    c.put(c.rect(0, 0, n, 3) | c.rect(0, n - 3, n, n), "wood", 0.4)
    return c.rgb()


def t_sky_moon():
    """The sky strip (256 x 64): a green-black night, clouds, the moon, bare trees on the skyline, bars (the courtyard's barred sky)."""
    c = Canvas(64, 256)
    fy = c.y / 64.0
    c.put(c.y >= 0, "sky", 0.15 + 0.8 * fy + (_noise(64, 12, 361, w=256) - 0.5) * 0.1)
    cl = _noise(64, 16, 362, 4, w=256) + fy * 0.15
    c.put(cl > 0.62, "cloud", 0.2 + (cl - 0.62) * 2.5)
    st = px.speckle(64, 0.004, 363)[:, :64] > 0.5  # a few faint stars: one texel of the sky is a big square on screen
    st = np.tile(st, (1, 4))
    c.put(st & (cl < 0.55) & (fy < 0.5), "cloud", 0.7)
    halo = c.ell(190, 14, 6, 6)
    c.put(halo & ~c.ell(190, 14, 2.3, 2.3), "cloud", 0.95 - np.hypot(c.x - 190, c.y - 14) / 6 * 0.7)
    c.put(c.ell(190, 14, 2.3, 2.3), "moon", 0.8)
    rng = np.random.RandomState(364)
    sky_line = 56 + np.sin(c.x * 0.05) * 2 + np.sin(c.x * 0.13) * 1.2
    c.put(c.y > sky_line, "black", 0.5)
    for k in range(9):
        tx = 10 + k * 28 + rng.rand() * 10
        top = 30 + rng.rand() * 14
        c.put(c.seg(tx, 60, tx, top, 1.8), "black", 0.6)
        for b in range(5):
            by = top + (58 - top) * (0.05 + 0.15 * b)
            s = (-1) ** b
            L = 3 + rng.rand() * 6
            c.put(c.seg(tx, by, tx + s * L, by - L * 0.8, 1.0), "black", 0.7)
    for x in range(0, 256, 16):
        c.put(c.rect(x, 0, x + 1, 64), "black", 0.2)
    c.put(c.rect(0, 0, 256, 1) | c.rect(0, 30, 256, 31), "black", 0.2)
    return c.rgb(dither=0.0)


# ---- billboard props (RGBA 128 x 128, written here) ----------------------------------------------------------------------------------------------

def _legs(c: Canvas, pts, mat="steel", w=2.2, sh=0.45):
    for (x0, y0, x1, y1) in pts:
        c.put(c.seg(x0, y0, x1, y1, w), mat, sh)


def p_chair(plastic: str, seed: int):
    """A moulded shell chair on splayed steel legs (the reference's lined-up waiting chairs)."""
    c = Canvas(128)
    _legs(c, [(44, 84, 36, 124), (84, 84, 92, 124), (54, 86, 52, 120), (74, 86, 76, 120)], w=2.6, sh=0.5)
    _legs(c, [(40, 106, 88, 106)], w=1.6, sh=0.35)
    half = 24 + (74 - c.y) * 0.12  # the shell widens towards the top
    back = (np.abs(c.x - 64) < half) & (c.y < 74) & (c.y > 30)
    back &= ~((c.y < 38) & (np.abs(c.x - 64) > half - 8) & (np.hypot(np.abs(c.x - 64) - (half - 8), c.y - 38) > 8))
    seat = c.ell(64, 80, 34, 9)
    m = back | seat
    sh = 0.55 + 0.25 * np.clip(1 - np.hypot(c.x - 52, c.y - 40) / 40, 0, 1) - 0.25 * (c.y > 80) + (_noise(128, 8, seed) - 0.5) * 0.15
    c.put(m, plastic, sh)
    c.put(m & (c.x > 86), plastic, sh - 0.25)
    c.put(m & (_noise(128, 5, seed + 1) > 0.78), plastic, 0.2)  # scuffs
    c.put(c.seg(36, 76, 92, 76, 1.5) & m, plastic, 0.85)
    return c.rgba()


def p_bed(seed=401):
    """An iron bed: tall barred head, lower foot, thin striped mattress, a grey blanket."""
    c = Canvas(128)
    # head (left) and foot (right) frames
    for x0, top in ((8, 26), (114, 50)):
        c.put(c.rect(x0, top, x0 + 4, 124), "steel", 0.35 + 0.25 * (c.x < x0 + 2))
        c.put(c.rect(x0 - 1, top - 2, x0 + 5, top + 1), "steel", 0.6)
    for k in range(5):
        x = 13 + k * 0.0
    bars_h = c.rect(12, 30, 26, 66) & ((c.x.astype(int) % 4) == 0)
    c.put(bars_h | c.rect(8, 28, 26, 31) | c.rect(8, 64, 26, 67), "steel", 0.4)
    c.put(c.rect(8, 28, 30, 31), "steel", 0.4)
    c.put(c.rect(12, 30, 14, 66) | c.rect(16, 30, 18, 66) | c.rect(20, 30, 22, 66) | c.rect(24, 30, 26, 66), "steel", 0.42)
    c.put(c.rect(102, 52, 118, 55) | (c.rect(102, 55, 114, 72) & ((c.x.astype(int) % 4) == 2)), "steel", 0.42)
    # rail and springs
    c.put(c.rect(10, 80, 118, 84), "steel", 0.4 + 0.25 * (c.y < 81))
    c.put(c.rect(12, 84, 116, 87) & ((c.x.astype(int) % 3) == 0), "steel", 0.3)
    # mattress and blanket
    mat = c.rect(12, 70, 116, 81)
    c.put(mat, "linen", 0.55 + 0.15 * ((c.x.astype(int) % 6) < 2) - 0.2 * (c.y > 78))
    c.put(c.ell(26, 68, 11, 5), "linen", 0.8 - 0.3 * (c.y > 69))
    bl = c.rect(40, 66, 114, 82) | c.ell(40, 74, 4, 8)
    c.put(bl, "cloth", 0.5 + (_noise(128, 6, seed) - 0.5) * 0.4 - 0.25 * (c.y > 79))
    c.put(c.rect(40, 66, 114, 68), "cloth", 0.75)
    c.put(c.rect(40, 66, 114, 82) & (_noise(128, 4, seed + 1) > 0.8), "rust", 0.25)
    # castors
    for x in (10, 116):
        c.put(c.ell(x, 124, 3, 3), "black", 0.5)
    return c.rgba()


def p_surgical_lamp(seed=411):
    """The surgical lamp: a ceiling arm and a big dome with five bulbs glowing under it (seen a little from below)."""
    c = Canvas(128)
    c.put(c.rect(61, 0, 67, 30), "steel", 0.35 + 0.3 * (c.x < 63))
    c.put(c.ell(64, 30, 7, 5), "steel", 0.55)
    c.put(c.seg(64, 30, 64, 46, 5), "steel", 0.4)
    dome = c.ell(64, 72, 54, 30) & (c.y < 74)
    c.put(dome, "steel", 0.3 + 0.45 * np.clip(1 - np.hypot(c.x - 44, c.y - 52) / 60, 0, 1))
    c.put(dome & (_noise(128, 6, seed) > 0.72), "rust", 0.35)
    rim = c.ell(64, 74, 56, 16) & ~c.ell(64, 74, 50, 12)
    c.put(rim, "steel", 0.6)
    under = c.ell(64, 74, 50, 12)
    c.put(under, "steel", 0.15)
    for (bx, by) in ((40, 74), (64, 70), (88, 74), (52, 79), (76, 79)):
        c.put(c.ell(bx, by, 7, 4.5), "light", 0.75 + 0.25 * np.clip(1 - np.hypot(c.x - bx, c.y - by) / 6, 0, 1))
        c.put(c.ell(bx, by, 7.5, 5) & ~c.ell(bx, by, 7, 4.5), "brass", 0.5)
    c.put(c.ell(64, 74, 4, 3), "steel", 0.7)  # the handle
    return c.rgba()


def p_steel_table(seed=421):
    """A steel treatment table: perforated top with a raised lip, a pedestal with taps and pipes, rust."""
    c = Canvas(128)
    top = c.rect(6, 52, 122, 60)
    nn = _noise(128, 6, seed)
    c.put(c.rect(4, 48, 124, 52), "steel", 0.8)
    c.put(top, "steel", 0.55 + (nn - 0.5) * 0.3)
    c.put(top & ((c.x.astype(int) % 5) == 2) & ((c.y.astype(int) % 3) == 1), "black", 0.4)
    c.put(c.rect(4, 60, 124, 66), "steel", 0.3 - 0.1 * (c.y > 63))
    ped = c.rect(40, 66, 88, 116)
    c.put(ped, "steel", 0.35 + 0.2 * (c.x < 46) - 0.15 * (c.x > 82) + (nn - 0.5) * 0.25)
    c.put(ped & (_noise(128, 5, seed + 1) > 0.66), "rust", 0.4 + (nn - 0.5))
    c.put(c.rect(44, 76, 84, 77) | c.rect(44, 96, 84, 97), "black", 0.3)
    c.put(c.rect(30, 116, 98, 124), "steel", 0.28)
    c.put(c.seg(88, 80, 104, 80, 3) | c.seg(104, 80, 104, 100, 3), "steel", 0.5)
    c.put(c.ell(104, 102, 3, 2), "brass", 0.55)
    c.put(c.seg(40, 90, 26, 90, 3) | c.seg(26, 90, 26, 116, 3), "steel", 0.45)
    c.put(c.rect(4, 48, 124, 66) & (_noise(128, 4, seed + 2) > 0.8), "rust", 0.5)
    # straps
    for x in (36, 92):
        c.put(c.rect(x, 50, x + 6, 66), "wood", 0.45)
        c.put(c.rect(x + 1, 56, x + 5, 59), "brass", 0.6)
    return c.rgba()


def p_easel(variant: int):
    """A wooden easel with a resident's canvas (a face under a moon, or a garden)."""
    c = Canvas(128)
    _legs(c, [(44, 124, 60, 8), (84, 124, 68, 8), (64, 124, 64, 70)], mat="wood", w=4, sh=0.55)
    c.put(c.rect(36, 82, 92, 86), "wood", 0.6)
    can = c.rect(34, 16, 94, 80)
    c.put(c.rect(32, 14, 96, 82), "wood", 0.35)
    c.put(can, "linen", 0.7)
    if variant == 0:
        c.put(can & (c.y < 50), "art_b", 0.25 + (c.y - 16) / 34 * 0.4)
        c.put(c.ell(78, 28, 6, 6), "art_y", 0.85)
        c.put(c.ell(56, 54, 14, 18) & can, "art_p", 0.55)
        c.put(c.ell(51, 50, 2, 2) | c.ell(61, 50, 2, 2), "black", 0.2)
        c.put(c.seg(50, 62, 62, 60, 2), "art_r", 0.6)
        c.put(can & (c.y > 72), "art_r", 0.35)
    else:
        c.put(can & (c.y < 46), "art_y", 0.55 + (46 - c.y) / 30 * 0.3)
        c.put(can & (c.y >= 46), "tile", 0.55 + (_noise(128, 6, 431) - 0.5) * 0.4)
        for k in range(5):
            c.put(c.ell(42 + k * 11, 58 + (k % 2) * 6, 3, 3), ["art_r", "art_p", "art_y", "art_r", "art_b"][k], 0.7)
        c.put(c.ell(70, 30, 8, 8), "art_r", 0.75)
    c.put(c.rect(34, 16, 94, 80) & (_noise(128, 3, 432 + variant) > 0.85), "linen", 0.45)  # drips and smudges
    return c.rgba()


def p_jars(seed=441):
    """A rusty steel shelf unit with specimen jars, bottles and a ledger."""
    c = Canvas(128)
    frame = c.rect(10, 8, 14, 126) | c.rect(114, 8, 118, 126)
    c.put(frame, "steel", 0.4)
    c.put(c.rect(10, 8, 118, 126) & ~frame, "black", 0.55)
    rng = np.random.RandomState(seed)
    for k, sy in enumerate((40, 76, 112)):
        c.put(c.rect(10, sy, 118, sy + 4), "steel", 0.5 + 0.3 * (c.y < sy + 1))
        x = 16
        while x < 108:
            w = 9 + rng.randint(6)
            h = 18 + rng.randint(10)
            if x + w > 112:
                break
            if rng.rand() < 0.75:
                jar = c.rect(x, sy - h, x + w, sy)
                c.put(jar, "glass", 0.4 + 0.35 * (c.x < x + 2) - 0.15 * (c.x > x + w - 2))
                lvl = sy - h * (0.3 + rng.rand() * 0.5)
                c.put(jar & (c.y > lvl) & (c.x > x) & (c.x < x + w - 1), "liquid", 0.35 + 0.4 * rng.rand())
                if rng.rand() < 0.5:  # something floating
                    c.put(c.ell(x + w / 2, (lvl + sy) / 2, w * 0.22, h * 0.15), "plaster", 0.45)
                c.put(c.rect(x - 1, sy - h - 3, x + w + 1, sy - h), "brass" if rng.rand() < 0.5 else "steel", 0.45)
                c.put(c.rect(x + 2, sy - h * 0.55, x + w - 2, sy - h * 0.35), "linen", 0.7)
            else:
                c.put(c.rect(x, sy - h - 4, x + w, sy), ["wood", "art_r", "cloth"][rng.randint(3)], 0.4 + 0.2 * rng.rand())
            x += w + 2 + rng.randint(3)
    c.put(c.rect(10, 8, 118, 126) & (_noise(128, 5, seed + 1) > 0.78) & (c.mat == NAMES.index("steel")), "rust", 0.45)
    return c.rgba()


def p_phone(seed=451):
    """A black rotary phone on a little steel cabinet with a notepad."""
    c = Canvas(128)
    cab = c.rect(30, 70, 98, 124)
    c.put(cab, "steel", 0.4 + (_noise(128, 6, seed) - 0.5) * 0.3)
    c.put(c.rect(26, 66, 102, 71), "steel", 0.65)
    c.put(c.rect(36, 82, 92, 84) | c.rect(36, 102, 92, 104), "black", 0.3)
    c.put(c.rect(60, 90, 68, 93) | c.rect(60, 110, 68, 113), "brass", 0.5)
    c.put(cab & (_noise(128, 4, seed + 1) > 0.75), "rust", 0.45)
    body = c.ell(62, 62, 22, 10) & (c.y < 66) | c.rect(40, 58, 84, 66)
    c.put(body, "black", 0.5 + 0.4 * np.clip(1 - np.hypot(c.x - 54, c.y - 56) / 18, 0, 1))
    dial = c.ell(62, 58, 9, 5)
    c.put(dial, "plaster", 0.6)
    for k in range(10):
        a = k * 0.55 + 0.4
        c.put(c.ell(62 + np.cos(a) * 6.5, 58 + np.sin(a) * 3.5, 1.1, 0.8), "black", 0.2)
    c.put(c.ell(62, 58, 2, 1.4), "art_r", 0.5)
    hand = c.ell(62, 46, 26, 5) | c.ell(40, 50, 6, 5) | c.ell(84, 50, 6, 5)
    c.put(hand, "black", 0.55 + 0.4 * (c.y < 44))
    c.put(c.seg(84, 62, 92, 68, 1.4), "black", 0.3)  # the cord
    c.put(c.rect(76, 62, 96, 66) & (c.x > 86), "linen", 0.7)
    return c.rgba()


def p_radiator(seed=461):
    """A cast-iron radiator on legs, with a valve and a pipe running down to the floor."""
    c = Canvas(128)
    _radiator(c, 10, 110, 50, 112, seed)
    c.put(c.rect(116, 40, 120, 126), "steel", 0.45)
    c.put(c.rect(110, 104, 120, 108), "steel", 0.5)
    c.put(c.rect(4, 56, 10, 59), "steel", 0.5)
    return c.rgba()


def p_fan(seed=471):
    """A big wall fan in a square steel housing with a guard grille (the reference's extractor)."""
    c = Canvas(128)
    hous = c.rect(8, 8, 120, 120)
    c.put(hous, "steel", 0.35 + 0.2 * (c.x < 12) + 0.15 * (c.y < 12) - 0.2 * (c.x > 116))
    c.put(hous & (_noise(128, 6, seed) > 0.72), "rust", 0.4)
    ring = c.ell(64, 64, 50, 50)
    c.put(ring, "black", 0.35)
    ang = np.arctan2(c.y - 64, c.x - 64)
    r = np.hypot(c.x - 64, c.y - 64)
    blade = ring & (np.cos(3 * (ang - r * 0.02)) > 0.45) & (r > 8)
    c.put(blade, "steel", 0.45 + 0.25 * np.cos(3 * (ang - r * 0.02)))
    c.put(c.ell(64, 64, 9, 9), "steel", 0.65)
    grille = ring & ((np.abs(np.sin(r * 0.42)) < 0.18) | (np.abs(c.x - 64) < 0.8) | (np.abs(c.y - 64) < 0.8))
    c.put(grille, "steel", 0.7)
    for (x, y) in ((14, 14), (114, 14), (14, 114), (114, 114)):
        c.put(c.ell(x, y, 2, 2), "steel", 0.85)
    return c.rgba()


def p_clock(seed=481):
    """The wall clock: a steel ring, a yellowed face, hands stopped at ten to four."""
    c = Canvas(128)
    c.put(c.ell(64, 64, 56, 56), "steel", 0.5 + 0.3 * ((c.x + c.y) < 110))
    face = c.ell(64, 64, 48, 48)
    c.put(face, "linen", 0.75 - np.hypot(c.x - 64, c.y - 64) / 48 * 0.3 + (_noise(128, 8, seed) - 0.5) * 0.2)
    for k in range(12):
        a = k * np.pi / 6
        L = 8 if k % 3 == 0 else 4
        c.put(c.seg(64 + np.sin(a) * 44, 64 - np.cos(a) * 44, 64 + np.sin(a) * (44 - L), 64 - np.cos(a) * (44 - L), 3 if k % 3 == 0 else 2), "black", 0.2)
    for a, L, w in ((-0.53 + np.pi * 2 / 3 * 0 + 4 * np.pi / 6 * 0 + 2.09, 26, 4.5), (-1.05 + 1.05 * 0 - 0.0 + np.pi * 2 * 50 / 60 - 1.05 + 1.05, 38, 3)):
        c.put(c.seg(64, 64, 64 + np.sin(a) * L, 64 - np.cos(a) * L, w), "black", 0.15)
    c.put(c.ell(64, 64, 3, 3), "art_r", 0.5)
    c.put(face & c.seg(40, 30, 70, 60, 1), "linen", 0.95)  # a crack in the glass
    return c.rgba()


def p_cagelamp(seed=491):
    """The warm caged wall lamp (a bulkhead with an amber bulb behind bars)."""
    c = Canvas(128)
    c.put(c.rect(54, 10, 74, 22), "steel", 0.4)
    c.put(c.rect(60, 22, 68, 30), "steel", 0.5)
    glass = c.ell(64, 70, 26, 40) & (c.y > 30)
    c.put(glass, "light", 0.55 + 0.45 * np.clip(1 - np.hypot(c.x - 60, c.y - 66) / 26, 0, 1))
    cage = glass & ((np.abs(c.x - 64) % 9 < 1.8) | ((c.y.astype(int) % 16) < 2))
    c.put(cage, "brass", 0.35)
    c.put(c.rect(40, 106, 88, 114), "steel", 0.45)
    c.put(c.rect(46, 26, 82, 32), "brass", 0.5)
    return c.rgba()


def p_tube(seed=501):
    """A hanging fluorescent fitting: two chains, a dented housing, two tubes (one dead at the end)."""
    c = Canvas(128)
    for x in (24, 104):
        c.put(c.rect(x - 1, 0, x + 1, 56) & ((c.y.astype(int) % 4) < 3), "steel", 0.5)
    c.put(c.rect(6, 56, 122, 64), "steel", 0.4 + 0.3 * (c.y < 58))
    c.put(c.rect(10, 64, 118, 70), "cold", 0.85 + 0.15 * np.sin(c.x * 0.4) ** 2)
    c.put(c.rect(92, 64, 118, 70), "cold", 0.25)
    c.put(c.rect(6, 56, 122, 70) & (_noise(128, 5, seed) > 0.8), "rust", 0.4)
    return c.rgba()


def p_cabinet(seed=511):
    """A steel drawer cabinet, rust round the handles."""
    c = Canvas(128)
    body = c.rect(24, 8, 104, 124)
    nn = _noise(128, 8, seed)
    c.put(body, "steel", 0.42 + (nn - 0.5) * 0.25 + 0.15 * (c.x < 28) - 0.15 * (c.x > 100))
    for k in range(5):
        y = 12 + k * 22
        c.put(c.rect(28, y + 20, 100, y + 21), "black", 0.3)
        c.put(c.rect(56, y + 8, 72, y + 11), "steel", 0.8)
        c.put(c.rect(58, y + 3, 70, y + 7), "linen", 0.6)
        c.put(c.ell(64, y + 12, 10, 5) & (nn > 0.45), "rust", 0.45)
    c.put(body & (_noise(128, 4, seed + 1) > 0.8), "rust", 0.35)
    return c.rgba()


def p_trolley(seed=521):
    """An instrument trolley: two steel trays, bottles, a kidney dish, castors."""
    c = Canvas(128)
    for x in (22, 106):
        c.put(c.rect(x - 2, 46, x + 2, 118), "steel", 0.5)
    for y in (46, 92):
        c.put(c.rect(16, y, 112, y + 5), "steel", 0.6 + 0.2 * (c.y < y + 1))
    c.put(c.rect(30, 32, 38, 46), "glass", 0.55)
    c.put(c.rect(30, 38, 38, 46), "liquid", 0.5)
    c.put(c.rect(42, 28, 48, 46), "art_b", 0.4)
    c.put(c.ell(76, 44, 16, 4) & (c.y < 46), "steel", 0.8)
    c.put(c.seg(58, 44, 72, 40, 1.4) | c.seg(80, 42, 96, 38, 1.2), "steel", 0.95)
    c.put(c.rect(30, 82, 60, 92), "linen", 0.65)
    c.put(c.rect(30, 82, 60, 92) & (_noise(128, 3, seed) > 0.75), "art_r", 0.3)
    for x in (22, 106):
        c.put(c.ell(x, 122, 4, 4), "black", 0.5)
    return c.rgba()


def p_sink(seed=531):
    """A cracked enamel wall sink with brass taps and a rusty trap."""
    c = Canvas(128)
    c.put(c.rect(26, 40, 102, 66), "plaster", 0.75 - 0.3 * (c.y > 60))
    c.put(c.rect(30, 40, 98, 46), "plaster", 0.95)
    c.put(c.seg(50, 48, 60, 64, 1), "black", 0.4)
    for x in (48, 80):
        c.put(c.rect(x - 2, 28, x + 2, 40), "brass", 0.55)
        c.put(c.rect(x - 5, 26, x + 5, 29), "brass", 0.75)
    c.put(c.rect(60, 66, 68, 96), "steel", 0.45)
    c.put(c.ell(64, 98, 7, 5), "rust", 0.5)
    c.put(c.rect(60, 100, 68, 126), "steel", 0.4)
    c.put(c.rect(26, 40, 102, 66) & (_noise(128, 4, seed) > 0.8), "rust", 0.4)
    return c.rgba()


def p_wheelchair(seed=541):
    """An old wheelchair parked against the wall."""
    c = Canvas(128)
    big = c.ell(54, 96, 28, 28) & ~c.ell(54, 96, 24, 24)
    c.put(big, "black", 0.5)
    c.put(c.ell(54, 96, 22, 22) & ~c.ell(54, 96, 20, 20), "steel", 0.55)
    for k in range(6):
        a = k * np.pi / 6
        c.put(c.seg(54 - np.cos(a) * 22, 96 - np.sin(a) * 22, 54 + np.cos(a) * 22, 96 + np.sin(a) * 22, 1), "steel", 0.4)
    c.put(c.ell(100, 118, 6, 6), "black", 0.5)
    c.put(c.seg(36, 28, 40, 80, 3) | c.seg(40, 80, 100, 80, 3) | c.seg(96, 80, 100, 116, 3), "steel", 0.55)
    c.put(c.rect(40, 30, 50, 72) | c.rect(44, 66, 96, 76), "cloth", 0.35)
    c.put(c.seg(30, 26, 40, 28, 3), "black", 0.5)
    c.put(c.rect(40, 30, 96, 80) & (_noise(128, 4, seed) > 0.8) & (c.mat == NAMES.index("cloth")), "rust", 0.3)
    return c.rgba()


PROPS = {
    "thing_chair": lambda: p_chair("plastic_t", 551),
    "thing_chair_b": lambda: p_chair("plastic_b", 552),
    "thing_chair_c": lambda: p_chair("plastic_u", 553),
    "thing_bed": p_bed,
    "thing_lamp": p_surgical_lamp,
    "thing_table": p_steel_table,
    "thing_easel": lambda: p_easel(0),
    "thing_easel_b": lambda: p_easel(1),
    "thing_jars": p_jars,
    "thing_phone": p_phone,
    "thing_radiator": p_radiator,
    "thing_fan": p_fan,
    "thing_clock": p_clock,
    "thing_cagelamp": p_cagelamp,
    "thing_tube": p_tube,
    "thing_cabinet": p_cabinet,
    "thing_trolley": p_trolley,
    "thing_sink": p_sink,
    "thing_wheelchair": p_wheelchair,
}

TILES = {
    "wall_mint": (t_wall_mint, 3.0), "wall_dado": (t_wall_dado, 2.2), "tx_tile": (t_tx_tile, 2.3), "floor_check": (t_floor_check, 2.0),
    "tx_floor": (t_tx_floor, 1.2), "floor_wood": (t_floor_wood, 3.0), "floor_art": (t_floor_art, 3.0), "ceil_tile": (t_ceil_tile, 2.5),
    "ceil_pale": (t_ceil_pale, 2.5), "pad_tile": (t_pad_tile, 1.2), "wall_cdoor": (t_wall_cdoor, 2.7), "wall_cdoor2": (t_wall_cdoor2, 2.7),
    "wall_door": (t_wall_door, 3.0), "wall_office": (t_wall_office, 2.7), "wall_end": (t_wall_end, 3.0), "wall_window": (t_wall_window, 3.0),
    "wall_awindow": (t_wall_awindow, 4.6), "wall_dwindow": (t_wall_dwindow, 1.8), "wall_slit": (t_wall_slit, 0.9), "wall_art": (t_wall_art, 4.6),
    "wall_brick": (t_wall_brick, 3.2), "wall_archdoor": (t_wall_archdoor, 3.0), "floor_paving": (t_floor_paving, 3.0), "floor_dais": (t_floor_dais, 2.0),
    "wall_speaker": (t_wall_speaker, 2.0), "wall_led": (t_wall_led, 3.0), "sky_moon": (t_sky_moon, 1.0),
}


def write_props(out_dir: str) -> list:
    """Write the RGBA billboard props (tiles.MENTAL_HOSPITAL lists their ids)."""
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    for pid, fn in sorted(PROPS.items()):
        Image.fromarray(fn(), "RGBA").save(os.path.join(out_dir, pid + ".png"), optimize=False, compress_level=9)
    return sorted(PROPS)


def build() -> dict:
    write_props(os.path.join(lib.ROOT, "assets", "story", "mental_hospital", "textures"))
    return {tid: (fn(), metres) for tid, (fn, metres) in TILES.items()}


if __name__ == "__main__":  # a preview sheet: python3 -m art.tex_mental_hospital /tmp/out.png (from tools/story)
    import sys
    from PIL import Image, ImageDraw
    items = [(k, Image.fromarray(fn())) for k, (fn, _) in TILES.items()] + [(k, Image.fromarray(fn(), "RGBA")) for k, fn in PROPS.items()]
    S = 192
    W = 8
    sheet = Image.new("RGB", (W * S, ((len(items) + W - 1) // W) * (S + 14)), (60, 0, 60))
    d = ImageDraw.Draw(sheet)
    for i, (k, im) in enumerate(items):
        im = im.convert("RGBA")
        sz = (S, S) if im.size[0] == im.size[1] else (S, S // 4)
        im = im.resize(sz, Image.NEAREST)
        x, y = (i % W) * S, (i // W) * (S + 14)
        sheet.paste(im, (x, y + 14), im)
        d.text((x + 2, y + 1), k, fill=(255, 255, 255))
    sheet.save(sys.argv[1] if len(sys.argv) > 1 else "/tmp/tex_mh.png")
