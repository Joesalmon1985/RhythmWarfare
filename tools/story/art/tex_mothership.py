"""The Mothership's procedural pixel textures (docs/STORY_25D_ART_DIRECTION.md 2.A, 2.D): cold cyan hull, the planet's glow, an alien rave in a spaceship.

`build()` returns {tile_id: (rgb uint8 (n, n, 3), metres_per_repeat)}; tools/story/art/tiles.py writes them after the Godot bake (an id that the bake also makes is
replaced, a new id is added). The billboard props (`thing_*`, RGBA: specimen tubes, the probe arm, the exam table, consoles, the captain's chair, pressure suits,
pipes, plants, the lounge bar, the planet) are written here as RGBA PNGs straight into the chapter's textures directory, because tiles.py saves RGB; their ids and
metres are listed in tiles.MOTHERSHIP so the manifest picks them up. Everything is drawn in numpy with tools/story/art/pixeltex.py and quantised to small palette
ramps with ordered dithering. Deterministic: every random value comes from a seeded generator.
"""
from __future__ import annotations

import os

import numpy as np

from . import pixeltex as pt

N = 128

# ---- palettes (dark to light) ------------------------------------------------------------------------------------------------------------------------
HULL = pt.ramp("#03050b", "#08101c", "#0e1b2c", "#15293d", "#1f3a50", "#2d5266", "#43717f", "#6797a0", "#9cc6c8")
DARK = pt.ramp("#020308", "#060b15", "#0b1522", "#112032", "#1a2f44")
CYAN = pt.ramp("#06222c", "#0b4656", "#117c8c", "#1fb6c2", "#5ee8ea", "#c4fff8")
CORE = pt.ramp("#021410", "#05302a", "#0a5848", "#12907a", "#30d0a8", "#90ffd8", "#eafff6")
AMBER = pt.ramp("#2a1804", "#6a3e08", "#b87012", "#f0a828", "#ffe08a")
RED = pt.ramp("#1c0306", "#4e080c", "#951414", "#e0301c", "#ff7a4a", "#ffd8b0")
HAZ = pt.ramp("#171206", "#4a3a0c", "#94741a", "#d8b02a", "#f8e070")
MED = pt.ramp("#21363c", "#3d5a60", "#62868a", "#8eb2b2", "#b6d6d2", "#d8f0ea", "#f2fffb")
STEEL = pt.ramp("#0c141c", "#1b2a36", "#2e4452", "#4a6672", "#6f8f98", "#9ebcc0", "#d2ecec")
SPACE = pt.ramp("#010208", "#030614", "#060c22", "#0a1532", "#0e2242", "#123050")
PLANET = pt.ramp("#03061a", "#081032", "#0d1f52", "#123a70", "#14607e", "#1e8c9a", "#3cb8b4", "#78dcc8", "#bcf2dc", "#f0fff2")
PLANT = pt.ramp("#04140e", "#0a2e22", "#145238", "#20804e", "#40b468", "#9ae8a0")
VIOLET = pt.ramp("#0e0618", "#22103a", "#3c1c60", "#5c2e8a", "#8a52b8", "#c494e8")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT_DIR = os.path.join(ROOT, "assets", "story", "mothership", "textures")


# ---- small drawing helpers -----------------------------------------------------------------------------------------------------------------------------

def _g(n: int = N):
    return pt.grid(n)


def rect(x, y, x0, y0, x1, y1):
    return (x >= x0) & (x < x1) & (y >= y0) & (y < y1)


def ellipse(x, y, cx, cy, rx, ry):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0


def seg(x, y, x0, y0, x1, y1, w):
    """Distance mask of a thick line segment."""
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy + 1e-6
    t = np.clip(((x - x0) * dx + (y - y0) * dy) / L2, 0, 1)
    px, py = x0 + t * dx, y0 + t * dy
    return (x - px) ** 2 + (y - py) ** 2 <= w * w


def cyl(x, cx, r):
    """A vertical cylinder's shade across x (lit from the left), 0..1."""
    u = np.clip((x - cx) / max(r, 1e-3), -1, 1)
    return np.clip(0.62 - 0.42 * u - 0.25 * u * u + 0.18 * np.exp(-((u + 0.45) * 4) ** 2), 0, 1)


def paint(rgb, mask, shade, pal, dither=1.0):
    q = pt.quantise(np.broadcast_to(np.asarray(shade, np.float32), mask.shape).astype(np.float32), pal, dither)
    m = mask > 0.5 if mask.dtype != bool else mask
    rgb[m] = q[m]


def stars(n_w, n_h, seed, density=0.012):
    rng = np.random.RandomState(seed)
    s = np.zeros((n_h, n_w), np.float32)
    k = int(n_w * n_h * density)
    xs, ys, br = rng.randint(0, n_w, k), rng.randint(0, n_h, k), rng.rand(k)
    s[ys, xs] = 0.35 + 0.65 * br ** 2
    big = br > 0.93  # a few bright stars with a cross
    for x0, y0 in zip(xs[big], ys[big]):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            s[(y0 + dy) % n_h, (x0 + dx) % n_w] = max(s[(y0 + dy) % n_h, (x0 + dx) % n_w], 0.5)
    return s


class Sprite:
    """An RGBA billboard drawn shape by shape; alpha is on or off (the world draws things with an alpha scissor)."""

    def __init__(self, n: int = N):
        self.n = n
        self.rgb = np.zeros((n, n, 3), np.uint8)
        self.a = np.zeros((n, n), np.uint8)
        self.x, self.y = _g(n)

    def fill(self, mask, shade, pal, dither=1.0):
        mask = mask.astype(bool)
        paint(self.rgb, mask, shade, pal, dither)
        self.a[mask] = 255

    def dots(self, pts, col):
        c = (pt.hexc(col) * 255).astype(np.uint8)
        for px, py in pts:
            if 0 <= px < self.n and 0 <= py < self.n:
                self.rgb[py, px] = c
                self.a[py, px] = 255

    def rgba(self):
        return np.dstack([self.rgb, self.a])


def save_rgba(tid: str, rgba: np.ndarray) -> None:
    from PIL import Image
    os.makedirs(OUT_DIR, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT_DIR, tid + ".png"), optimize=False, compress_level=9)


# ---- hull, deck, ceiling --------------------------------------------------------------------------------------------------------------------------------

def wall_hull():
    """Hull plates with seams and rivets, a glowing conduit with brackets, a grille, grime running down."""
    x, y = _g()
    sh, seam = pt.panels(N, 2, seed=41)
    g = pt.grime(N, seed=42, amount=0.55)
    sh = sh * 0.8 + 0.08 - g * 0.25
    # a louvred grille in the lower right plate
    gr = rect(x, y, 74, 80, 120, 116)
    sh = np.where(gr, 0.18 + 0.35 * ((y % 4) < 1.5), sh)
    sh = np.where(rect(x, y, 73, 79, 121, 80) | rect(x, y, 73, 116, 121, 117), 0.75, sh)
    # a small stencilled panel number on the upper left plate
    sh = np.where(rect(x, y, 10, 10, 26, 18) & ((x + y) % 3 == 0), sh + 0.15, sh)
    rgb = pt.quantise(sh, HULL)
    rgb[seam > 0.5] = (HULL[0] * 255).astype(np.uint8)
    # the conduit: a glass tube of light along the wall, held by brackets every half tile
    c = np.abs(y - 56) < 3.5
    glow = 0.55 + 0.45 * np.cos((y - 56) / 3.5 * 1.4) + (pt.noise(N, 6, 43) - 0.5) * 0.3
    paint(rgb, c, glow, CYAN)
    br = c & ((x % 64) < 5)
    paint(rgb, br | (rect(x, y, 0, 51, 128, 52)) | rect(x, y, 0, 61, 128, 62), 0.55 + 0.3 * ((x % 64) < 2), STEEL)
    # cables dropping under the conduit
    cab = pt.cables(N, 2, seed=44) > 0.5
    cab &= y > 62
    paint(rgb, cab, 0.2, DARK)
    return rgb


def ceil_hull():
    """Ceiling plates, vents and a strip of cold light."""
    x, y = _g()
    sh, seam = pt.panels(N, 4, seed=51)
    sh = sh * 0.6 + 0.05 - pt.grime(N, seed=52, amount=0.4, drip=False) * 0.2
    vent = rect(x % 64, y % 64, 6, 38, 58, 58)
    sh = np.where(vent, 0.12 + 0.3 * ((x % 4) < 1.5), sh)
    rgb = pt.quantise(sh, HULL)
    rgb[seam > 0.5] = (HULL[0] * 255).astype(np.uint8)
    strip = rect(x, y, 0, 12, 128, 18)
    paint(rgb, strip, 0.75 + 0.25 * ((x % 16) > 1) - 0.4 * (np.abs(y - 15) > 1.6), CYAN)
    return rgb


def _hexcells(n, cols, rows, seed, yscale):
    x, y = _g(n)
    cw, rh = n / cols, n / rows
    rng = np.random.RandomState(seed)
    best = np.full((n, n), 1e9, np.float32)
    second = np.full((n, n), 1e9, np.float32)
    cell = np.zeros((n, n), np.int32)
    tones = rng.rand(cols * rows).astype(np.float32)
    for j in range(rows):
        for i in range(cols):
            cx, cy = (i + 0.5 * (j % 2)) * cw, j * rh
            dx = (x - cx + n / 2) % n - n / 2
            dy = ((y - cy + n / 2) % n - n / 2) * yscale
            d = np.sqrt(dx * dx + dy * dy)
            closer = d < best
            second = np.where(closer, best, np.minimum(second, d))
            cell = np.where(closer, j * cols + i, cell)
            best = np.where(closer, d, best)
    return best, second - best, cell, tones


def floor_hex():
    """Hex deck plates: bevelled cells, dark seams with a few running cyan, a bolt in each, scuffs."""
    x, y = _g()
    d1, gap, cell, tones = _hexcells(N, 4, 6, 61, 1.3)
    t = tones[cell]
    seam = gap < 1.6
    sh = 0.38 + 0.18 * t + 0.16 * np.clip(1 - (gap - 1.6) / 3.0, 0, 1) - 0.12 * (d1 / 16.0)
    sh += (pt.noise(N, 10, 62) - 0.5) * 0.18
    sh -= pt.grime(N, seed=63, amount=0.45, drip=False) * 0.25
    sh = np.where(d1 < 1.5, 0.85, np.where(d1 < 2.6, 0.18, sh))
    rgb = pt.quantise(sh, HULL)
    lit_cells = tones > 0.72
    glow = seam & (lit_cells[cell])
    rgb[seam] = (HULL[0] * 255).astype(np.uint8)
    paint(rgb, glow, 0.35 + 0.4 * pt.noise(N, 5, 64), CYAN)
    return rgb


def floor_dais():
    """Tread plate (raised diamonds) with worn bright edges: the ramps, the dais and the helm."""
    x, y = _g()
    u, v = (x + y) % 8, (x - y) % 8
    bump = (np.abs(u - 4) < 1.2) & ((x // 4 + y // 4) % 2 == 0) | (np.abs(v - 4) < 1.2) & ((x // 4 + y // 4) % 2 == 1)
    sh = 0.42 + (pt.noise(N, 12, 71) - 0.5) * 0.25 - pt.grime(N, seed=72, amount=0.5, drip=False) * 0.25
    sh = np.where(bump, sh + 0.28, sh)
    wear = pt.noise(N, 6, 73) > 0.66
    sh = np.where(wear & bump, sh + 0.2, sh)
    rgb = pt.quantise(np.clip(sh, 0, 1), STEEL)
    return rgb


def trim():
    """A band of hull lip with a row of running LEDs."""
    n = 64
    x, y = _g(n)
    sh = 0.35 + 0.35 * (y < 4) - 0.2 * (y > n - 5) + (pt.noise(n, 8, 81) - 0.5) * 0.2
    sh = np.where((y % 16) < 1, 0.1, sh)
    rgb = pt.quantise(np.clip(sh, 0, 1), HULL)
    led = (np.abs(y - 32) < 3) & ((x % 8) < 4)
    paint(rgb, led, 0.65 + 0.35 * ((x % 16) < 8), CYAN)
    paint(rgb, (np.abs(y - 32) < 3) & ((x % 32) >= 28) & ((x % 8) < 4), 0.7, VIOLET)
    paint(rgb, (np.abs(y - 32) < 5) & ~led & (np.abs(y - 32) >= 3), 0.15, DARK)
    return rgb


# ---- windows, the planet, the sky ----------------------------------------------------------------------------------------------------------------------

def _glass(w, h, seed, glow_from_bottom=0.5):
    x, y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    neb = pt.noise(N, 40, seed, 4)
    neb = np.tile(neb, (int(np.ceil(h / N)), int(np.ceil(w / N))))[:h, :w]
    sh = 0.08 + glow_from_bottom * (y / h) ** 2.2 + (neb - 0.5) * 0.22
    s = stars(w, h, seed + 1)
    sh = np.maximum(sh, s)
    return np.clip(sh, 0, 1)


def wall_window(seed=91, glow=0.42):
    """A bay of glass on the stars with the planet's cold light rising from below, a header and mullions, a reflection streak."""
    x, y = _g()
    sh = _glass(N, N, seed, glow)
    refl = (np.abs((x + y * 0.6) % 128 - 70) < 3) | (np.abs((x + y * 0.6) % 128 - 78) < 1)
    sh = np.where(refl, np.maximum(sh, 0.32), sh)
    rgb = pt.quantise(sh, PLANET[:7])
    # frame: header, sill and two mullions per bay with rivet heads
    fr = (y < 7) | (y >= N - 5) | ((x % 64) < 5)
    fsh = 0.45 + 0.25 * ((x % 64) < 1.5) + 0.2 * (y < 2) - 0.2 * ((y > 4) & (y < 7))
    fsh = np.where(((y % 16) == 8) & ((x % 64) == 2), 0.95, fsh)
    paint(rgb, fr, fsh, HULL)
    paint(rgb, rect(x, y, 0, 7, 128, 8) | ((x % 64) == 5), 0.2, CYAN)  # a cyan seal lit by the planet
    return rgb


def wall_planet():
    """The deck's and the gallery's great windows: more glow (the planet is just below the frame), fewer mullions."""
    x, y = _g()
    sh = _glass(N, N, 95, 0.75)
    rgb = pt.quantise(sh, PLANET[:8])
    fr = (y < 6) | ((x % 128) < 6)
    fsh = 0.5 + 0.25 * ((x % 128) < 2) + 0.2 * (y < 2)
    paint(rgb, fr, fsh, HULL)
    paint(rgb, rect(x, y, 0, 6, 128, 7) | ((x % 128) == 6), 0.25, CYAN)
    return rgb


def _planet_disc(w, h, cx, cy, r, seed, light=(-0.8, -0.38, 0.3)):
    """A lit sphere: bands and clouds, a dithered terminator, the night side, an atmosphere rim. Returns (shade 0..1 on PLANET, mask, rim mask)."""
    x, y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    u, v = (x - cx) / r, (y - cy) / r
    rr = u * u + v * v
    inside = rr <= 1.0
    z = np.sqrt(np.clip(1 - rr, 0, 1))
    L = np.array(light, np.float32)
    L /= np.linalg.norm(L)
    lam = np.clip(u * L[0] + v * L[1] + z * L[2], 0, 1)
    tilt = v + 0.18 * u  # tilted bands
    lat = np.arcsin(np.clip(tilt, -1, 1))
    nz = pt.noise(N, 18, seed, 4)
    nz = np.tile(nz, (int(np.ceil(h / N)), int(np.ceil(w / N))))[:h, :w]
    band = 0.5 + 0.5 * np.sin(lat * 9.0 + nz * 3.2)
    storms = np.clip((pt.noise(N, 9, seed + 2, 3) - 0.62) * 4, 0, 1)
    storms = np.tile(storms, (int(np.ceil(h / N)), int(np.ceil(w / N))))[:h, :w]
    sh = 0.06 + 0.82 * lam ** 0.8 + (band - 0.5) * 0.16 * (lam > 0.05) + storms * 0.12 * lam
    sh = sh + 0.22 * np.clip(1 - z, 0, 1) ** 3 * (lam > 0.02)  # limb brightening on the day side
    rim = (rr > 1.0) & (rr <= (1.0 + 2.6 / r) ** 2)
    return np.clip(sh, 0, 1), inside, rim, lam


def thing_planet():
    """The planet as a billboard seen through the big windows: an ice giant, lit from the upper left, banded, with an atmosphere rim."""
    s = Sprite()
    r = 56.0
    sh, inside, rim, lam = _planet_disc(N, N, 64, 64, r, 101)
    s.fill(inside, sh, PLANET)
    x, y = s.x, s.y
    u, v = (x - 64) / r, (y - 64) / r
    lit_side = np.clip(-(u * 0.8 + v * 0.38) / np.sqrt(u * u + v * v + 1e-6), 0, 1)
    s.fill(rim, 0.45 + 0.55 * lit_side, CYAN)
    # a thin ring seen nearly edge on, in front of the disc on the lower half
    ring = (np.abs((y - 64) - 0.22 * (x - 64)) < 1.6) & (np.abs(x - 64) < 63)
    s.fill(ring & ~inside, 0.55 + 0.35 * ((x.astype(int) // 3) % 2), PLANET[3:])
    return s.rgba()


def sky_space():
    """The sky strip (256 x 64, wraps once, seen through the open ceilings): deep space and a faint cyan nebula with sparse, dim stars. No planet here: one
    sky pixel is about two metres at the sky's distance, so a disc would read as a blocky silhouette; the planet is a billboard in the windows instead."""
    w, h = 256, 64
    x, y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    nz = np.tile(pt.noise(N, 30, 111, 4), (1, 2))[:h, :w]
    nebula = np.clip(1 - np.abs(y - 30 - 10 * np.sin(x / w * 2 * np.pi * 2)) / 22, 0, 1) * nz
    sh = 0.1 + 0.3 * (y / h) + nebula * 0.45
    rgb = pt.quantise(np.clip(sh, 0, 1) * 0.6, SPACE, dither=0.6)
    rng = np.random.RandomState(112)
    for _ in range(70):
        sx, sy, b = rng.randint(0, w), rng.randint(0, h), rng.rand()
        rgb[sy, sx] = (pt.ramp("#1c2c48", "#3e5a7c", "#7898b8")[int(b * 2.99)] * 255).astype(np.uint8)
    return rgb


# ---- the reactor -------------------------------------------------------------------------------------------------------------------------------------

def floor_grate():
    """Catwalk grating over the reactor well: steel bars and the green-cyan glow of the core far below through the gaps."""
    x, y = _g()
    glow = 0.25 + 0.55 * pt.noise(N, 20, 121, 3) + 0.15 * pt.noise(N, 5, 122)
    rgb = pt.quantise(np.clip(glow * 0.75, 0, 1), CORE)
    bars = ((x % 8) < 2) | ((y % 8) < 2)
    beams = ((x % 64) < 5) | ((y % 64) < 5)
    bsh = 0.45 + 0.25 * (((x % 8) < 1) | ((y % 8) < 1)) - pt.grime(N, seed=123, amount=0.5, drip=False) * 0.3
    paint(rgb, bars, bsh, STEEL)
    paint(rgb, beams, 0.3 + 0.3 * (((x % 64) < 1) | ((y % 64) < 1)) + 0.4 * (((x % 64) == 2) & ((y % 16) == 8)), STEEL)
    return rgb


def wall_tube():
    """The reactor well's walls: coolant tubes of glowing fluid in glass, banded with steel, pipes and cables between, dark plating."""
    x, y = _g()
    sh, seam = pt.panels(N, 2, seed=131, rivets=False)
    rgb = pt.quantise(sh * 0.5, HULL)
    rgb[seam > 0.5] = (HULL[0] * 255).astype(np.uint8)
    rng = np.random.RandomState(132)
    for cx in (32, 96):
        tube = np.abs(x - cx) < 15
        flow = pt.noise(N, 10, 133 + cx)
        bub = pt.speckle(N, 0.03, 134 + cx) * (np.abs(x - cx) < 9)
        tsh = cyl(x, cx, 15) * 0.75 + flow * 0.3 + bub * 0.4
        paint(rgb, tube, tsh, CORE)
        hl = (np.abs(x - (cx - 7)) < 1) & tube
        paint(rgb, hl, 0.95, CORE)
        band = tube & (((y + cx) % 64) < 6)
        paint(rgb, band, cyl(x, cx, 16) * 0.9, STEEL)
        paint(rgb, band & (((y + cx) % 64) == 3) & ((x % 6) == 0), 0.9, AMBER)
    pipe = np.abs(x - 64) < 4
    paint(rgb, pipe, cyl(x, 64, 4) * 0.8, STEEL)
    paint(rgb, pipe & ((y % 32) < 3), 0.85, STEEL)
    for px in (2, 125):
        paint(rgb, np.abs(x - px) < 2, cyl(x, px, 2) * 0.5, STEEL)
    return rgb


def ceil_hazard():
    """The reactor's ceiling: plates with a hazard-striped crash beam and a run of pipes."""
    x, y = _g()
    sh, seam = pt.panels(N, 2, seed=141)
    rgb = pt.quantise(sh * 0.55, HULL)
    rgb[seam > 0.5] = (HULL[0] * 255).astype(np.uint8)
    beam = rect(x, y, 0, 8, 128, 26)
    stripe = ((x + y) // 8) % 2 == 0
    paint(rgb, beam & stripe, 0.75 - 0.3 * pt.grime(N, seed=142, amount=0.6), HAZ)
    paint(rgb, beam & ~stripe, 0.1, DARK)
    for py in (70, 86, 100):
        p = np.abs(y - py) < 5
        paint(rgb, p, 0.75 - 0.6 * np.abs(y - py) / 5 + 0.15 * ((x % 48) < 4), STEEL)
    return rgb


# ---- the bridge --------------------------------------------------------------------------------------------------------------------------------------

def wall_console():
    """Bridge consoles (metres equal to the bridge's height, so the desk sits at a desk's height): hull above, screens with traces, rows of tiny lights,
    the desk lip, cabinets below."""
    x, y = _g()
    sh, seam = pt.panels(N, 2, seed=151)
    rgb = pt.quantise(sh * 0.55, HULL)
    rgb[seam > 0.5] = (HULL[0] * 255).astype(np.uint8)
    paint(rgb, rect(x, y, 0, 30, 128, 36), 0.25 + 0.3 * ((x % 6) < 2), DARK)  # cable tray
    paint(rgb, rect(x, y, 0, 42, 128, 45), 0.8, CYAN)  # a light band
    rng = np.random.RandomState(152)
    for sx in (4, 68):
        scr = rect(x, y, sx, 50, sx + 56, 82)
        paint(rgb, rect(x, y, sx - 2, 48, sx + 58, 84), 0.4, STEEL)
        grid_ = (((x - sx) % 8) == 0) | (((y - 50) % 8) == 0)
        paint(rgb, scr, 0.12 + 0.12 * grid_, DARK)
        ph = rng.rand() * 6
        tr = np.abs(y - (66 + 9 * np.sin((x - sx) / 5.0 + ph) * np.sin((x - sx) / 17.0 + ph))) < 0.9
        paint(rgb, scr & tr, 0.85, CYAN)
        bars = scr & (y > 74) & ((x - sx) % 4 < 2) & (y > 82 - 8 * rng.rand(N)[x.astype(int)])
        paint(rgb, bars, 0.75, AMBER)
    desk = rect(x, y, 0, 86, 128, 98)
    paint(rgb, desk, 0.3 + 0.12 * ((y - 86) / 12), STEEL)
    cols = ["#ff4a3a", "#48ff8a", "#ffc23a", "#5ee8ff", "#ff6ae0", "#e8f8ff"]
    for row in (88, 91, 94):
        for cx in range(3, 128, 4):
            if rng.rand() < 0.72:
                c = (pt.hexc(cols[rng.randint(len(cols))]) * 255).astype(np.uint8)
                rgb[row, cx] = c
                if rng.rand() < 0.3 and cx + 1 < N:
                    rgb[row, cx + 1] = c
    paint(rgb, rect(x, y, 0, 98, 128, 101), 0.85, STEEL)
    cab = rect(x, y, 0, 101, 128, 128)
    csh = 0.32 - 0.12 * (((x % 32) < 1) | ((x % 32) > 30)) + 0.1 * ((y > 106) & (y < 116) & ((y % 3) == 0) & ((x % 32) > 8) & ((x % 32) < 24))
    paint(rgb, cab, csh - 0.15 * (y > 122), HULL)
    return rgb


def floor_bridge():
    """The bridge deck: dark polished plates with cyan inlays and scuffs."""
    x, y = _g()
    sh, seam = pt.panels(N, 2, seed=161, rivets=False)
    sh = sh * 0.45 + 0.1 + 0.12 * np.clip(1 - np.abs((x - y) % 128 - 64) / 20, 0, 1) - pt.grime(N, seed=162, amount=0.4, drip=False) * 0.2
    rgb = pt.quantise(np.clip(sh, 0, 1), HULL)
    rgb[seam > 0.5] = (HULL[0] * 255).astype(np.uint8)
    inlay = ((np.abs(x - 32) < 1) | (np.abs(y - 96) < 1)) & ((x + y) % 3 != 0)
    paint(rgb, inlay, 0.55, CYAN)
    return rgb


# ---- the medical bay ---------------------------------------------------------------------------------------------------------------------------------

def med_tile():
    """Clean glazed wall tiles (metres equal to the bay's height): a teal stripe at hand height, a little grime at the skirting."""
    x, y = _g()
    sh, grout = pt.tiles(N, 6, 1, seed=171, gloss=0.45)
    row = (y // (N / 6)).astype(int)
    sh = sh * 0.7 + 0.3
    sh -= np.clip((y - 110) / 18, 0, 1) * 0.25 * pt.noise(N, 6, 172)
    rgb = pt.quantise(np.clip(sh, 0, 1), MED)
    paint(rgb, (row == 3) & (grout < 0.5), np.clip(sh - 0.2, 0, 1), CYAN[1:])
    rgb[grout > 0.5] = (MED[2] * 255).astype(np.uint8)
    paint(rgb, rect(x, y, 0, 122, 128, 128), 0.3, STEEL)  # skirting
    return rgb


def med_ceil():
    """The bay's ceiling: tiles with two sterile light panels."""
    x, y = _g()
    sh, grout = pt.tiles(N, 4, 1, seed=181, gloss=0.2)
    rgb = pt.quantise(sh * 0.7 + 0.15, MED)
    rgb[grout > 0.5] = (MED[1] * 255).astype(np.uint8)
    for (px, py) in ((0, 0), (64, 64)):
        pan = rect(x, y, px + 4, py + 4, px + 60, py + 28)
        paint(rgb, pan, 0.85 + 0.15 * (((x - px) % 8) > 1), pt.ramp("#9ad8d8", "#d8fff8", "#ffffff"))
        paint(rgb, rect(x, y, px + 3, py + 3, px + 61, py + 4) | rect(x, y, px + 3, py + 28, px + 61, py + 29), 0.4, STEEL)
    return rgb


def med_floor():
    """Sheet flooring in clean sterile squares, a drain, faint scuffs."""
    x, y = _g()
    sh, grout = pt.tiles(N, 4, 1, seed=191, gloss=0.15)
    sh = sh * 0.6 + 0.12 * (((x // 32) + (y // 32)) % 2) + 0.1 - pt.grime(N, seed=192, amount=0.3, drip=False) * 0.2
    rgb = pt.quantise(np.clip(sh, 0, 1), MED[:6])
    rgb[grout > 0.5] = (MED[1] * 255).astype(np.uint8)
    dr = (x - 64) ** 2 + (y - 64) ** 2
    paint(rgb, dr < 70, 0.15 + 0.4 * (((x + y) % 3) == 0), STEEL)
    paint(rgb, (dr >= 70) & (dr < 90), 0.6, STEEL)
    return rgb


# ---- the airlock -------------------------------------------------------------------------------------------------------------------------------------

def _hazard(x, y):
    return ((x + y) // 6) % 2 == 0


def wall_hatch():
    """The airlock's heavy door (metres equal to the airlock's height, so the door stands on the floor and is 2.2 m tall; centred on the 4 m wall):
    a hazard-striped frame, a steel leaf with bolts, the locking wheel, a porthole, a stencil and the beacon's housing above."""
    x, y = _g()
    sh, seam = pt.panels(N, 2, seed=201)
    rgb = pt.quantise(sh * 0.55 - pt.grime(N, seed=202, amount=0.5) * 0.15, HULL)
    rgb[seam > 0.5] = (HULL[0] * 255).astype(np.uint8)
    cx = 80
    xx = (x - cx + 64) % 128 - 64  # centred on u = 0.625 of the tile, wrapping
    top = 50
    frame = (np.abs(xx) < 32) & (y > top - 6)
    paint(rgb, frame & _hazard(x, y), 0.7 - 0.25 * pt.grime(N, seed=203, amount=0.7), HAZ)
    paint(rgb, frame & ~_hazard(x, y), 0.08, DARK)
    leaf = (np.abs(xx) < 26) & (y > top)
    corner = (np.abs(xx) > 18) & (y < top + 8) & (((np.abs(xx) - 18) ** 2 + (y - top - 8) ** 2) > 64)
    leaf &= ~corner
    lsh = 0.45 - 0.2 * (np.abs(xx) / 26) ** 2 + (pt.noise(N, 8, 204) - 0.5) * 0.2 - pt.grime(N, seed=205, amount=0.5) * 0.2
    paint(rgb, leaf, lsh, STEEL)
    paint(rgb, leaf & (np.abs(xx) < 0.8), 0.05, DARK)  # the split between the two halves
    bolts = leaf & (np.abs(xx) > 21) & (np.abs(xx) < 24) & ((y % 10) < 2)
    paint(rgb, bolts, 0.9, STEEL)
    ph = xx ** 2 + (y - (top + 16)) ** 2
    paint(rgb, (ph < 64) & (ph >= 36), 0.75, STEEL)
    paint(rgb, ph < 36, 0.25 + 0.4 * (y < top + 14) * ((xx + y) % 5 == 0), PLANET[:6])
    wy = top + 50
    wd = np.sqrt(xx ** 2 + (y - wy) ** 2)
    ring = np.abs(wd - 12) < 2
    ang = np.arctan2(y - wy, xx)
    spokes = ((wd < 12) & (np.abs(np.sin(ang * 3)) < 0.18 * 12 / np.maximum(wd, 1))) | (wd < 3)
    paint(rgb, ring | spokes, 0.85 - 0.5 * ((y - wy) / 14), RED[1:])
    paint(rgb, rect(xx, y, -10, top - 22, 10, top - 10), 0.3 + 0.3 * (y == top - 22), STEEL)  # the beacon's housing
    paint(rgb, (y > top - 4) & (y < top - 1) & (np.abs(xx) < 22) & ((xx // 4) % 2 == 0), 0.95, MED)  # stencil
    paint(rgb, rect(xx, y, 34, 70, 44, 90), 0.35, STEEL)  # the door control
    paint(rgb, rect(xx, y, 36, 73, 42, 77), 0.9, RED)
    paint(rgb, rect(xx, y, 36, 81, 42, 85), 0.7, pt.ramp("#08301a", "#40ff80", "#d0ffd8"))
    return rgb


def wall_sofa():
    """Quilted padding with buttoned tufts, in deep violet with a cyan piping: the lounge bays' walls and the bay's padded exam booth."""
    x, y = _g()
    u, v = (x + y) % 32, (x - y) % 32
    du, dv = np.minimum(u, 32 - u), np.minimum(v, 32 - v)
    puff = np.clip(np.minimum(du, dv) / 8.0, 0, 1)
    sh = 0.2 + 0.45 * puff + 0.12 * ((x - y) % 32 < 16) * puff + (pt.noise(N, 10, 351) - 0.5) * 0.12 - pt.grime(N, seed=352, amount=0.35) * 0.15
    rgb = pt.quantise(np.clip(sh, 0, 1), VIOLET)
    tuft = (((x % 32) - 16) ** 2 + ((y % 32) - 16) ** 2 < 3) | (((x % 32)) ** 2 + ((y % 32)) ** 2 < 3)
    paint(rgb, tuft, 0.05, DARK)
    paint(rgb, rect(x, y, 0, 0, 128, 3) | rect(x, y, 0, 125, 128, 128), 0.6, CYAN)
    return rgb


def wall_shelf():
    """Specimen shelving behind the exam table: steel shelves of jars, each lit from within (metres equal to the table's room)."""
    x, y = _g()
    sh, seam = pt.panels(N, 2, seed=361, rivets=False)
    rgb = pt.quantise(sh * 0.4, HULL)
    rng = np.random.RandomState(362)
    pals = [CORE, CYAN, VIOLET, CORE, AMBER]
    for sy in (40, 70, 100):
        paint(rgb, rect(x, y, 0, sy, 128, sy + 3), 0.75 - 0.4 * (y > sy + 1), STEEL)
        cx = 3
        while cx < 120:
            w = rng.randint(7, 12)
            h = rng.randint(12, 22)
            jar = rect(x, y, cx, sy - h, cx + w, sy)
            pal = pals[rng.randint(len(pals))]
            paint(rgb, jar, cyl(x, cx + w / 2, w / 2) * 0.7 + 0.15, pal)
            if rng.rand() < 0.6:
                paint(rgb, ellipse(x, y, cx + w / 2, sy - h / 2, w / 4, h / 5), 0.1, DARK)  # something in the jar
            paint(rgb, rect(x, y, cx - 1, sy - h - 3, cx + w + 1, sy - h), 0.7, STEEL)
            cx += w + rng.randint(2, 5)
    paint(rgb, rect(x, y, 0, 0, 3, 128) | rect(x, y, 125, 0, 128, 128), 0.5, STEEL)
    paint(rgb, rect(x, y, 0, 8, 128, 10), 0.85, CYAN)
    return rgb


def wall_airlock():
    """The airlock's side walls (metres equal to its height): dark plates, a red light strip, pressure pipes with a valve and a gauge, a hazard band at the
    skirting."""
    x, y = _g()
    sh, seam = pt.panels(N, 2, seed=211)
    rgb = pt.quantise(sh * 0.55 - pt.grime(N, seed=212, amount=0.6) * 0.15, HULL)
    rgb[seam > 0.5] = (HULL[0] * 255).astype(np.uint8)
    paint(rgb, rect(x, y, 0, 8, 128, 12), 0.75 + 0.2 * ((x % 8) < 4), RED)
    for px in (10, 20):
        p = np.abs(x - px) < 3.5
        paint(rgb, p, cyl(x, px, 3.5) * 0.85, STEEL)
        paint(rgb, p & ((y % 40) < 3), 0.9, STEEL)
    v = (x - 15) ** 2 + (y - 60) ** 2
    paint(rgb, v < 30, 0.7 - 0.3 * (v > 12), RED[1:])
    g = (x - 40) ** 2 + (y - 40) ** 2
    paint(rgb, g < 40, 0.85, MED)
    paint(rgb, (g < 40) & seg(x, y, 40, 40, 44, 37, 0.8), 0.1, DARK)
    paint(rgb, (g >= 40) & (g < 56), 0.5, STEEL)
    band = rect(x, y, 0, 104, 128, 116)
    paint(rgb, band & _hazard(x, y), 0.7 - 0.3 * pt.grime(N, seed=213, amount=0.7), HAZ)
    paint(rgb, band & ~_hazard(x, y), 0.08, DARK)
    paint(rgb, rect(x, y, 0, 116, 128, 128), 0.25, STEEL)
    return rgb


def floor_airlock():
    """The airlock's deck: worn tread plate with a hazard border."""
    x, y = _g()
    rgb = floor_dais()
    rgb = (rgb.astype(np.float32) * 0.8).astype(np.uint8)
    band = (y < 10) | (y >= N - 10)
    paint(rgb, band & _hazard(x, y), 0.7 - 0.35 * pt.grime(N, seed=221, amount=0.7, drip=False), HAZ)
    paint(rgb, band & ~_hazard(x, y), 0.08, DARK)
    return rgb


# ---- props (RGBA billboards) -------------------------------------------------------------------------------------------------------------------------

def thing_tube(variant=0):
    """A specimen tube: steel caps, glass, glowing fluid with bubbles and something floating in it."""
    s = Sprite()
    x, y = s.x, s.y
    pal = CORE if variant == 0 else VIOLET
    body = (np.abs(x - 64) < 21) & (y >= 14) & (y < 112)
    flow = pt.noise(N, 9, 231 + variant)
    s.fill(body, cyl(x, 64, 21) * 0.6 + flow * 0.25 + 0.05, pal)
    # the specimen
    if variant == 0:
        sp = ellipse(x, y, 64, 46, 9, 11) | ellipse(x, y, 64, 70, 6, 15) | seg(x, y, 64, 62, 52, 80, 2) | seg(x, y, 64, 62, 76, 78, 2)
        s.fill(sp & body, 0.12 + 0.08 * (x < 62), DARK)
        s.dots([(60, 45), (68, 45)], "#c4fff0")
    else:
        sp = ellipse(x, y, 64, 58, 13, 13)
        s.fill(sp & body, 0.75 - 0.5 * np.sqrt((x - 60) ** 2 + (y - 54) ** 2) / 14, MED)
        s.fill(ellipse(x, y, 66, 58, 6, 6), 0.4, CYAN)
        s.fill(ellipse(x, y, 67, 58, 3, 3), 0.0, DARK)
        for k in range(4):
            s.fill(seg(x, y, 64, 70, 54 + 7 * k, 98, 1.3) & body, 0.25, VIOLET)
    bub = (pt.speckle(N, 0.04, 233 + variant) > 0.5) & (np.abs(x - 64) < 16) & body
    s.fill(bub, 0.95, pal)
    s.fill(body & (np.abs(x - 51) < 1.2), 0.98, MED)  # a highlight on the glass
    cap = (np.abs(x - 64) < 25) & (y >= 4) & (y < 16)
    s.fill(cap, cyl(x, 64, 25) * 0.9, STEEL)
    base = (np.abs(x - 64) < 27) & (y >= 110) & (y < 126)
    s.fill(base, cyl(x, 64, 27) * 0.8 - 0.15 * (y > 120), STEEL)
    s.fill(base & (y == 115) & ((x % 6) < 2), 0.8, CYAN)
    s.fill((np.abs(x - 64) < 3) & (y < 4), 0.4, STEEL)
    return s.rgba()


def thing_probe_arm():
    """The probe arm over the exam table: a ceiling mount, two jointed segments, a lamp dome with a ring of light, three probes."""
    s = Sprite()
    x, y = s.x, s.y
    s.fill(rect(x, y, 48, 0, 80, 6), 0.4, STEEL)
    s.fill(seg(x, y, 64, 4, 94, 34, 4), 0.55, STEEL)
    s.fill(seg(x, y, 94, 34, 66, 70, 3.5), 0.6, STEEL)
    for jx, jy in ((64, 5), (94, 34)):
        s.fill((x - jx) ** 2 + (y - jy) ** 2 < 36, 0.8 - 0.5 * ((x - jx + y - jy) > 0), STEEL)
    s.fill(seg(x, y, 66, 32, 92, 40, 1), 0.3, RED)  # a hose
    dome = ellipse(x, y, 64, 80, 26, 13) & (y < 84)
    s.fill(dome, 0.3 + 0.5 * (y < 74) * (x < 60), STEEL)
    s.fill(rect(x, y, 38, 82, 90, 87), 0.95 - 0.3 * (np.abs(x - 64) > 18), CYAN)
    for px, tip in ((54, 106), (64, 116), (74, 106)):
        s.fill(seg(x, y, 64 + (px - 64) * 0.4, 87, px, tip, 1.1), 0.75, STEEL)
        s.fill((x - px) ** 2 + (y - tip) ** 2 < 5, 0.9, RED[2:])
    return s.rgba()


def thing_exam_table():
    """The exam table: a pale padded top with restraint straps, a steel slab, a pedestal and base."""
    s = Sprite()
    x, y = s.x, s.y
    s.fill(rect(x, y, 6, 52, 122, 62) & ~((x < 10) & (y < 55)) & ~((x > 117) & (y < 55)), 0.75 - 0.25 * (y > 58), MED)
    for sx in (40, 84):
        s.fill(rect(x, y, sx, 51, sx + 6, 63), 0.2, VIOLET)
        s.fill(rect(x, y, sx + 2, 56, sx + 4, 58), 0.9, STEEL)
    s.fill(rect(x, y, 2, 62, 126, 72), 0.6 - 0.3 * (y > 68), STEEL)
    s.fill(rect(x, y, 4, 70, 124, 71) & ((x % 6) < 3), 0.9, CYAN)
    s.fill(rect(x, y, 54, 72, 74, 116), cyl(x, 64, 10) * 0.7, STEEL)
    s.fill(rect(x, y, 32, 114, 96, 124), 0.35 + 0.3 * (y < 116), STEEL)
    s.fill(seg(x, y, 74, 90, 104, 116, 1.2), 0.2, DARK)  # a cable to the floor
    return s.rgba()


def thing_monitor():
    """A vitals monitor on a wheeled stand: a heartbeat trace and two readouts."""
    s = Sprite()
    x, y = s.x, s.y
    s.fill(rect(x, y, 34, 10, 94, 54), 0.35, STEEL)
    scr = rect(x, y, 38, 14, 90, 50)
    s.fill(scr, 0.1 + 0.06 * (((x % 6) == 0) | ((y % 6) == 0)), DARK)
    beat = ((x - 38) % 26)
    trace = 32 - np.where((beat > 9) & (beat < 12), 13, np.where((beat >= 12) & (beat < 14), -6, 0))
    s.fill(scr & (np.abs(y - trace) < 1.1) & (x < 86), 0.85, pt.ramp("#08301a", "#40ff80", "#d0ffd8"))
    s.fill(rect(x, y, 42, 42, 54, 46), 0.8, AMBER)
    s.fill(rect(x, y, 72, 42, 86, 46), 0.8, CYAN)
    s.fill(rect(x, y, 61, 54, 67, 112), cyl(x, 64, 3) * 0.7, STEEL)
    s.fill(seg(x, y, 64, 112, 40, 122, 2) | seg(x, y, 64, 112, 88, 122, 2), 0.45, STEEL)
    s.fill(((x - 40) ** 2 + (y - 123) ** 2 < 10) | ((x - 88) ** 2 + (y - 123) ** 2 < 10), 0.15, DARK)
    return s.rgba()


def thing_cabinet():
    """A medicine cabinet: a steel carcass, glass doors, shelves of vials and jars."""
    s = Sprite()
    x, y = s.x, s.y
    s.fill(rect(x, y, 20, 6, 108, 124), 0.45, STEEL)
    inner = rect(x, y, 26, 12, 102, 96)
    s.fill(inner, 0.12 + 0.1 * (x < 64), DARK)
    rng = np.random.RandomState(241)
    pals = [CYAN, CORE, VIOLET, AMBER, RED]
    for sy in (36, 62, 94):
        s.fill(rect(x, y, 26, sy, 102, sy + 2), 0.7, STEEL)
        cx = 29
        while cx < 96:
            w = rng.randint(4, 8)
            hgt = rng.randint(8, 18)
            jar = rect(x, y, cx, sy - hgt, cx + w, sy)
            s.fill(jar, 0.4 + 0.5 * (x < cx + 2), pals[rng.randint(len(pals))])
            s.fill(rect(x, y, cx, sy - hgt - 2, cx + w, sy - hgt), 0.9, MED)
            cx += w + rng.randint(1, 4)
    s.fill(rect(x, y, 63, 12, 65, 96), 0.6, STEEL)
    s.fill(inner & (np.abs((x + y) % 40 - 8) < 1.5), 0.85, MED)  # glass glints
    s.fill(rect(x, y, 26, 100, 102, 120), 0.3 + 0.2 * ((y % 6) < 1), STEEL)
    s.fill(rect(x, y, 60, 108, 68, 111), 0.85, STEEL)
    return s.rgba()


def thing_screen():
    """A folding privacy screen: three pale cyan panels on a steel frame."""
    s = Sprite()
    x, y = s.x, s.y
    for i, px in enumerate((10, 46, 82)):
        pan = rect(x, y, px, 14, px + 36, 112)
        fold = (pt.noise(N, 6, 251 + i) - 0.5) * 0.25 + 0.15 * np.sin((x - px) / 3.0)
        s.fill(pan, 0.62 + fold - 0.12 * i, MED)
        s.fill(rect(x, y, px, 12, px + 36, 16) | rect(x, y, px, 110, px + 36, 114) | rect(x, y, px, 12, px + 2, 124) | rect(x, y, px + 34, 12, px + 36, 124),
               0.55, STEEL)
    return s.rgba()


def thing_bunk():
    """A recovery bunk: a low frame, pale sheets, a pillow, a folded blanket."""
    s = Sprite()
    x, y = s.x, s.y
    s.fill(rect(x, y, 4, 70, 124, 80), 0.5, STEEL)
    s.fill(rect(x, y, 6, 80, 12, 118) | rect(x, y, 116, 80, 122, 118), 0.4, STEEL)
    s.fill(rect(x, y, 6, 56, 122, 72), 0.8 - 0.3 * (y > 66) + (pt.noise(N, 5, 261) - 0.5) * 0.2, MED)
    s.fill(ellipse(x, y, 24, 54, 16, 7), 0.92 - 0.3 * (y > 55), MED)
    s.fill(rect(x, y, 80, 54, 118, 70), 0.55 + 0.15 * ((y % 4) < 2), CYAN[:4])
    s.fill(rect(x, y, 2, 40, 7, 80), 0.6, STEEL)
    return s.rgba()


def thing_surglamp():
    """The surgical lamp over the bay: a stem, a wide dish, a ring of white light."""
    s = Sprite()
    x, y = s.x, s.y
    s.fill(rect(x, y, 61, 0, 67, 54), cyl(x, 64, 3) * 0.8, STEEL)
    dish = ellipse(x, y, 64, 72, 44, 20) & (y < 78)
    s.fill(dish, 0.25 + 0.5 * (y < 62) * (x < 64), STEEL)
    s.fill(ellipse(x, y, 64, 78, 40, 6), 0.9 - 0.3 * (np.abs(x - 64) > 28), MED)
    for k in (-24, -8, 8, 24):
        s.fill(ellipse(x, y, 64 + k, 78, 5, 3), 1.0, MED)
    return s.rgba()


def thing_pipes():
    """A bundle of reactor pipes: three vertical runs with flanges, a valve wheel, a gauge, rust."""
    s = Sprite()
    x, y = s.x, s.y
    rus = pt.rust(N, 271, 0.5)
    for cx, r in ((40, 10), (64, 8), (86, 12)):
        p = np.abs(x - cx) < r
        s.fill(p, cyl(x, cx, r) * 0.8 - 0.2 * rus, STEEL)
        s.fill(p & (rus > 0.6), 0.5, AMBER[:3])
        fl = (np.abs(x - cx) < r + 3) & ((y + cx) % 40 < 4)
        s.fill(fl, cyl(x, cx, r + 3) * 0.9, STEEL)
    w = np.sqrt((x - 86) ** 2 + (y - 62) ** 2)
    s.fill((np.abs(w - 11) < 1.8) | ((w < 11) & ((np.abs(x - 86) < 1.2) | (np.abs(y - 62) < 1.2))), 0.8, RED[1:])
    g = (x - 40) ** 2 + (y - 90) ** 2
    s.fill(g < 64, 0.85, MED)
    s.fill((g < 64) & seg(x, y, 40, 90, 45, 86, 0.8), 0.05, DARK)
    s.fill((g >= 64) & (g < 90), 0.45, STEEL)
    s.fill(rect(x, y, 26, 120, 102, 128), 0.3, STEEL)
    return s.rgba()


def thing_cables():
    """Cables hanging in loops from the reactor's gantry, with a junction box."""
    s = Sprite()
    x, y = s.x, s.y
    s.fill(rect(x, y, 0, 0, 128, 6), 0.4 + 0.3 * ((x % 16) < 2), STEEL)
    rng = np.random.RandomState(281)
    for k in range(6):
        x0, x1 = rng.randint(0, 60), rng.randint(68, 128)
        sag = 40 + rng.rand() * 70
        t = np.clip((x - x0) / max(x1 - x0, 1), 0, 1)
        yy = 5 + sag * np.sin(np.pi * t)
        m = (np.abs(y - yy) < 1.5) & (x >= x0) & (x <= x1)
        pal = [DARK, VIOLET, RED, DARK, AMBER, DARK][k]
        s.fill(m, 0.35 if pal is not DARK else 0.6, pal)
    s.fill(rect(x, y, 56, 60, 74, 78), 0.45, STEEL)
    s.dots([(60, 64), (64, 64), (68, 64)], "#48ff8a")
    return s.rgba()


def thing_console():
    """A bridge console desk seen from the front: a slanted face of tiny lights, a screen, a pedestal."""
    s = Sprite()
    x, y = s.x, s.y
    scr = rect(x, y, 22, 22, 106, 58)
    s.fill(rect(x, y, 18, 18, 110, 62), 0.45, STEEL)
    s.fill(scr, 0.12 + 0.08 * (((x % 8) == 0) | ((y % 8) == 0)), DARK)
    tr = np.abs(y - (40 + 10 * np.sin((x - 22) / 6.0) * np.cos((x - 22) / 19.0))) < 1
    s.fill(scr & tr, 0.85, CYAN)
    s.fill(scr & (y > 50) & ((x % 5) < 3) & (y > 58 - (x * 7 % 9)), 0.75, AMBER)
    face = rect(x, y, 6, 64, 122, 84)
    s.fill(face, 0.3 + 0.15 * ((y - 64) / 20), STEEL)
    rng = np.random.RandomState(291)
    cols = ["#ff4a3a", "#48ff8a", "#ffc23a", "#5ee8ff", "#ff6ae0"]
    s.dots([(cx, cy) for cy in (68, 72, 76, 80) for cx in range(10, 120, 4) if rng.rand() < 0.65], cols[0])
    for cy in (68, 72, 76, 80):
        for cx in range(11, 120, 4):
            if rng.rand() < 0.6:
                s.dots([(cx, cy)], cols[rng.randint(len(cols))])
    s.fill(rect(x, y, 4, 84, 124, 88), 0.85, STEEL)
    s.fill(rect(x, y, 40, 88, 88, 124), 0.25 + 0.1 * ((y % 5) == 0), HULL)
    s.fill(rect(x, y, 30, 122, 98, 127), 0.4, STEEL)
    return s.rgba()


def thing_captain():
    """The captain's chair: a tall winged back, armrests with controls, a pedestal."""
    s = Sprite()
    x, y = s.x, s.y
    back = ellipse(x, y, 64, 40, 30, 36) & (y < 72)
    s.fill(back, 0.55 - 0.35 * np.abs(x - 64) / 30 - 0.1 * (y > 50), VIOLET)
    s.fill(back & (np.abs(x - 64) < 2) & (y > 14), 0.95, CYAN)  # a glowing seam down the back
    s.fill((((x - 40) ** 2 + (y - 18) ** 2) < 30) | (((x - 88) ** 2 + (y - 18) ** 2) < 30), 0.8, AMBER)
    s.fill(rect(x, y, 34, 70, 94, 84), 0.45 - 0.2 * (y > 78), VIOLET)
    for ax in (22, 92):
        s.fill(rect(x, y, ax, 62, ax + 14, 72), 0.6, STEEL)
        s.dots([(ax + 3, 66), (ax + 7, 66), (ax + 11, 66)], "#ff4a3a")
        s.dots([(ax + 5, 69), (ax + 9, 69)], "#48ff8a")
    s.fill(rect(x, y, 58, 84, 70, 116), cyl(x, 64, 6) * 0.7, STEEL)
    s.fill(ellipse(x, y, 64, 120, 30, 6), 0.35, STEEL)
    return s.rgba()


def thing_suit():
    """A pressure suit hung on the airlock wall: a bubble helmet, a puffy torso with a chest pack, gloves, boots."""
    s = Sprite()
    x, y = s.x, s.y
    s.fill(rect(x, y, 62, 0, 66, 10), 0.4, STEEL)  # the hook
    torso = ellipse(x, y, 64, 56, 22, 26)
    s.fill(torso, 0.7 - 0.4 * (x - 44) / 44 + (pt.noise(N, 5, 301) - 0.5) * 0.15, MED)
    s.fill(rect(x, y, 54, 46, 74, 62), 0.4, STEEL)
    s.dots([(58, 50), (62, 50), (66, 50)], "#ff4a3a")
    s.dots([(70, 50)], "#48ff8a")
    for side in (-1, 1):
        arm = seg(x, y, 64 + side * 20, 40, 64 + side * 28, 80, 7)
        s.fill(arm, 0.65 - 0.25 * side, MED)
        s.fill(seg(x, y, 64 + side * 28, 80, 64 + side * 29, 86, 6), 0.3, AMBER)
        leg = seg(x, y, 64 + side * 9, 78, 64 + side * 11, 112, 8)
        s.fill(leg, 0.6 - 0.25 * side, MED)
        s.fill(rect(x, y, 64 + side * 11 - 9, 110, 64 + side * 11 + 9, 122), 0.3, STEEL)
        s.fill(seg(x, y, 64 + side * 20, 66, 64 + side * 20, 72, 6), 0.35, HAZ)  # stripes on the arms
    s.fill(rect(x, y, 44, 76, 84, 82), 0.4, HAZ)
    helm = (x - 64) ** 2 + (y - 22) ** 2
    s.fill(helm < 196, 0.3 + 0.5 * ((x < 60) & (y < 18)), PLANET[2:8])
    s.fill((helm >= 196) & (helm < 256), 0.7, STEEL)
    return s.rgba()


def thing_wheel():
    """The hatch's locking wheel, seen face on."""
    s = Sprite()
    x, y = s.x, s.y
    d = np.sqrt((x - 64) ** 2 + (y - 64) ** 2)
    ang = np.arctan2(y - 64, x - 64)
    ring = np.abs(d - 50) < 7
    s.fill(ring, 0.75 - 0.4 * (y - 64) / 60 + 0.15 * (np.abs(d - 47) < 1.5), RED)
    spokes = (d < 50) & (np.abs(np.sin(ang * 2)) < 3.5 / np.maximum(d, 1))
    s.fill(spokes, 0.6, STEEL)
    s.fill(d < 12, 0.85 - 0.5 * (x + y > 128), STEEL)
    s.fill(ring & ((np.round(ang / (np.pi / 6)) * (np.pi / 6) - ang) ** 2 < 0.004), 0.25, RED)
    return s.rgba()


def thing_warn():
    """The red warning beacon over the airlock door: a caged dome on a bracket."""
    s = Sprite()
    x, y = s.x, s.y
    s.fill(rect(x, y, 40, 84, 88, 100), 0.35, STEEL)
    dome = ellipse(x, y, 64, 84, 22, 30) & (y < 84)
    s.fill(dome, 0.95 - 0.5 * np.sqrt((x - 56) ** 2 + (y - 66) ** 2) / 26, RED)
    cage = dome & (((x - 42) % 9 < 1.5) | (np.abs(y - 70) < 1.2))
    s.fill(cage, 0.3, STEEL)
    return s.rgba()


def thing_plant():
    """An alien plant in a steel planter: fat glowing bulbs on curling stems."""
    s = Sprite()
    x, y = s.x, s.y
    rng = np.random.RandomState(311)
    for k in range(7):
        bx = 64 + (k - 3) * 11 + rng.randint(-3, 4)
        tipy = 18 + rng.randint(0, 40)
        bend = (k - 3) * 6
        for t in np.linspace(0, 1, 24):
            px = bx + bend * t * t
            py = 92 - (92 - tipy) * t
            s.fill((x - px) ** 2 + (y - py) ** 2 < 6 - 3 * t, 0.35 + 0.2 * t, PLANT)
        tx, ty = bx + bend, tipy
        s.fill(ellipse(x, y, tx, ty, 6, 8), 0.95 - 0.5 * np.sqrt((x - tx + 2) ** 2 + (y - ty + 2) ** 2) / 8, CYAN if k % 2 else VIOLET)
    for k in range(5):
        lx = 40 + k * 12
        s.fill(ellipse(x, y, lx, 90, 10, 4) & (y < 92), 0.45 + 0.1 * k % 2, PLANT)
    s.fill(rect(x, y, 34, 92, 94, 124) & ~((y > 116) & ((x < 38) | (x > 90))), 0.55 - 0.3 * (x - 34) / 60, STEEL)
    s.fill(rect(x, y, 34, 98, 94, 100), 0.8, CYAN)
    return s.rgba()


def thing_bar():
    """The lounge bar: a curved counter with a glowing front, glasses and bottles on it."""
    s = Sprite()
    x, y = s.x, s.y
    front = rect(x, y, 2, 64, 126, 122)
    s.fill(front, 0.3 + 0.15 * np.sin(x / 9.0) ** 2, VIOLET)
    s.fill(front & ((y % 12) < 2), 0.8, CYAN)
    s.fill(rect(x, y, 0, 58, 128, 66), 0.75 - 0.3 * (y > 62), STEEL)
    s.fill(rect(x, y, 2, 120, 126, 126), 0.15, DARK)
    rng = np.random.RandomState(321)
    pals = [CYAN, CORE, VIOLET, AMBER]
    cx = 10
    while cx < 116:
        if rng.rand() < 0.5:  # a bottle
            h = rng.randint(18, 28)
            s.fill(rect(x, y, cx, 58 - h + 8, cx + 6, 58), 0.4 + 0.4 * (x < cx + 2), pals[rng.randint(4)])
            s.fill(rect(x, y, cx + 2, 58 - h, cx + 4, 58 - h + 8), 0.5, STEEL)
            cx += 9
        else:  # a glass
            s.fill(rect(x, y, cx, 48, cx + 5, 58) & ~rect(x, y, cx + 1, 48, cx + 4, 52), 0.85, MED)
            s.fill(rect(x, y, cx + 1, 52, cx + 4, 57), 0.7, pals[rng.randint(4)])
            cx += 8
    return s.rgba()


# ---- the chapter's set ---------------------------------------------------------------------------------------------------------------------------------

THINGS = {
    "thing_planet": thing_planet, "thing_tube": lambda: thing_tube(0), "thing_tube2": lambda: thing_tube(1), "thing_probe_arm": thing_probe_arm,
    "thing_exam_table": thing_exam_table, "thing_monitor": thing_monitor, "thing_cabinet": thing_cabinet, "thing_screen": thing_screen, "thing_bunk": thing_bunk,
    "thing_surglamp": thing_surglamp, "thing_pipes": thing_pipes, "thing_cables": thing_cables, "thing_console": thing_console, "thing_captain": thing_captain,
    "thing_suit": thing_suit, "thing_wheel": thing_wheel, "thing_warn": thing_warn, "thing_plant": thing_plant, "thing_bar": thing_bar,
}


def build() -> dict:
    """{tile_id: (rgb, metres)} for tiles.py; the RGBA props are written here (see the module note)."""
    for tid, fn in sorted(THINGS.items()):
        save_rgba(tid, fn())
    return {
        "wall_hull": (wall_hull(), 2.5),
        "ceil_hull": (ceil_hull(), 2.5),
        "floor_hex": (floor_hex(), 2.5),
        "floor_dais": (floor_dais(), 2.0),
        "trim": (trim(), 2.0),
        "wall_window": (wall_window(), 4.0),
        "wall_planet": (wall_planet(), 5.0),
        "sky_space": (sky_space(), 1.0),
        "floor_grate": (floor_grate(), 2.5),
        "wall_tube": (wall_tube(), 2.5),
        "ceil_hazard": (ceil_hazard(), 2.5),
        "wall_console": (wall_console(), 4.2),
        "floor_bridge": (floor_bridge(), 3.0),
        "med_tile": (med_tile(), 2.2),
        "med_ceil": (med_ceil(), 2.0),
        "med_floor": (med_floor(), 2.0),
        "wall_hatch": (wall_hatch(), 3.2),
        "wall_airlock": (wall_airlock(), 3.2),
        "wall_sofa": (wall_sofa(), 3.0),
        "wall_shelf": (wall_shelf(), 2.4),
        "floor_airlock": (floor_airlock(), 2.0),
    }
