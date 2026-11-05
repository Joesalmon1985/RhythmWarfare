"""The Ember Road's surface textures (docs/THREE_PATHS_AND_FACES_PLAN.md section 6): every floor / wall / ceiling / sky id of tools/story/art/ember_spec.py TILES,
drawn procedurally in numpy at tile size (64 or 128 px; sky 256 x 64), tileable, quantised onto small palette ramps with 8 x 8 ordered dithering.

`build(art)` writes assets/story/<art>/textures/<id>.png for the surfaces of one of the four art folders (orchard, birch_hall, deep_halls, ash_land) and returns
{id: {"file", "size", "metres"}}. Billboards (thing_* / piece_*) are drawn elsewhere (tex_ember_things.py) and are never touched here.
Run `python -m tools.story.art.tex_ember_tiles` from the repository root to build all four.

Deterministic (seeded generators, no clock), no external art, no letters / runes / symbols anywhere. Walls are tileable sideways; walls with a built-in
vertical structure (inn panelling, doors, windows, the fence, the falls) keep a sensible top and bottom instead.
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image

try:
    from .pixeltex import BAYER8, hexc, quantise, ramp
    from .ember_spec import ARTS, TILES
except ImportError:  # run as a plain script
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from pixeltex import BAYER8, hexc, quantise, ramp  # type: ignore
    from ember_spec import ARTS, TILES  # type: ignore

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REG: dict = {}


def tex(art: str, tid: str):
    def deco(fn):
        REG.setdefault(art, {})[tid] = fn
        return fn
    return deco


# ---- noise ----------------------------------------------------------------------------------------------------------------------------------------

def _rng(seed: int) -> np.random.RandomState:
    return np.random.RandomState(seed)


def grid2(h: int, w: int):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return x, y


def pn_at(fx: np.ndarray, fy: np.ndarray, cy: int, cx: int, seed: int) -> np.ndarray:
    """One octave of periodic value noise sampled at fractional lattice coordinates (cells wrap in both directions)."""
    g = _rng(seed).rand(cy, cx).astype(np.float32)
    x0f, y0f = np.floor(fx), np.floor(fy)
    tx, ty = fx - x0f, fy - y0f
    x0, y0 = x0f.astype(int) % cx, y0f.astype(int) % cy
    x1, y1 = (x0 + 1) % cx, (y0 + 1) % cy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
    return ((g[y0, x0] * (1 - tx) + g[y0, x1] * tx) * (1 - ty) + (g[y1, x0] * (1 - tx) + g[y1, x1] * tx) * ty).astype(np.float32)


def pnc(h: int, w: int, cy: int, cx: int, seed: int, octaves: int = 3) -> np.ndarray:
    """Periodic noise 0..1 with cy x cx lattice cells at the first octave (anisotropic when cy != cx)."""
    x, y = grid2(h, w)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cyo, cxo = max(1, cy * 2 ** o), max(1, cx * 2 ** o)
        out += pn_at(x / w * cxo, y / h * cyo, cyo, cxo, seed + 31 * o) * amp
        tot += amp
        amp *= 0.5
    return out / tot


def pnr(h: int, w: int, scale: float, seed: int, octaves: int = 3) -> np.ndarray:
    return pnc(h, w, max(1, round(h / scale)), max(1, round(w / scale)), seed, octaves)


def nz(n: int, scale: float, seed: int, octaves: int = 3) -> np.ndarray:
    return pnr(n, n, scale, seed, octaves)


def wnoise(h: int, w: int, cy: int, cx: int, seed: int, amp: float = 1.0, octaves: int = 3) -> np.ndarray:
    """Domain-warped periodic noise: swirled, roiling smoke."""
    x, y = grid2(h, w)
    ox = pnc(h, w, cy, cx, seed + 101, 2) - 0.5
    oy = pnc(h, w, cy, cx, seed + 202, 2) - 0.5
    out = np.zeros((h, w), np.float32)
    a, tot = 1.0, 0.0
    for o in range(octaves):
        cyo, cxo = cy * 2 ** o, cx * 2 ** o
        out += pn_at(x / w * cxo + ox * amp * 2 ** o, y / h * cyo + oy * amp * 2 ** o, cyo, cxo, seed + 31 * o) * a
        tot += a
        a *= 0.5
    return out / tot


def speck(h: int, w: int, density: float, seed: int) -> np.ndarray:
    return _rng(seed).rand(h, w) < density


def grid(n: int):
    return grid2(n, n)


def rpts(h: int, w: int, count: int, seed: int, mind: float = 0.0):
    rng = _rng(seed)
    pts = []
    tries = 0
    while len(pts) < count and tries < count * 80:
        tries += 1
        p = (rng.rand() * w, rng.rand() * h)
        if mind > 0:
            ok = True
            for q in pts:
                dx = abs(p[0] - q[0])
                dx = min(dx, w - dx)
                dy = abs(p[1] - q[1])
                dy = min(dy, h - dy)
                if dx * dx + dy * dy < mind * mind:
                    ok = False
                    break
            if not ok:
                continue
        pts.append(p)
    return pts


def worley(h: int, w: int, pts, ay: float = 1.0):
    """Cellular noise over a torus: (f1, f2, id of nearest point). pts is a list of (x, y) pixel positions."""
    x, y = grid2(h, w)
    f1 = np.full((h, w), 1e9, np.float32)
    f2 = np.full((h, w), 1e9, np.float32)
    ids = np.zeros((h, w), np.int32)
    for k, (px, py) in enumerate(pts):
        dx = np.abs(x - px)
        dx = np.minimum(dx, w - dx)
        dy = np.abs(y - py)
        dy = np.minimum(dy, h - dy)
        d = np.sqrt(dx * dx + (dy * ay) ** 2)
        c = d < f1
        f2 = np.where(c, f1, np.minimum(f2, d))
        ids = np.where(c, k, ids)
        f1 = np.where(c, d, f1)
    return f1, f2, ids


def jpts(h: int, w: int, cy: int, cx: int, seed: int, jit: float = 0.7, stagger: bool = False):
    rng = _rng(seed)
    pts = []
    for j in range(cy):
        for i in range(cx):
            ox = 0.5 * (j % 2) if stagger else 0.0
            pts.append(((i + 0.5 + ox + (rng.rand() - 0.5) * jit) * w / cx % w, (j + 0.5 + (rng.rand() - 0.5) * jit) * h / cy % h))
    return pts


# ---- colour ---------------------------------------------------------------------------------------------------------------------------------------

def pq(shade: np.ndarray, pal: np.ndarray, d: float = 0.8) -> np.ndarray:
    return quantise(np.clip(shade, 0, 1), pal, d)


def col(hexs: str) -> np.ndarray:
    return (hexc(hexs) * 255 + 0.5).astype(np.uint8)


def put(rgb: np.ndarray, mask: np.ndarray, hexs: str) -> np.ndarray:
    out = rgb.copy()
    out[np.asarray(mask, bool)] = col(hexs)
    return out


def tint(rgb: np.ndarray, hexs: str, amt) -> np.ndarray:
    a = np.clip(np.asarray(amt, np.float32), 0, 1)[..., None]
    return (rgb.astype(np.float32) * (1 - a) + hexc(hexs) * 255 * a + 0.5).astype(np.uint8)


def sel(mask: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.where(np.asarray(mask, bool)[..., None], a, b)


def shift(m: np.ndarray, dy: int, dx: int) -> np.ndarray:
    return np.roll(np.roll(m, dy, 0), dx, 1)


class Layer:
    """Shapes stamped with torus wrap-around onto a coverage mask and a 0..1 shade, then quantised through one palette."""

    def __init__(self, h: int, w: int | None = None):
        self.h, self.w = h, (w or h)
        self.m = np.zeros((self.h, self.w), bool)
        self.v = np.zeros((self.h, self.w), np.float32)

    def _g(self, x0, y0, x1, y1):
        ys = np.arange(int(np.floor(y0)), int(np.ceil(y1)) + 1)
        xs = np.arange(int(np.floor(x0)), int(np.ceil(x1)) + 1)
        gy = ys[:, None].astype(np.float32) + np.zeros((1, len(xs)), np.float32)
        gx = xs[None, :].astype(np.float32) + np.zeros((len(ys), 1), np.float32)
        return gx, gy, np.ix_(ys % self.h, xs % self.w)

    def _put(self, ix, mask, val):
        self.m[ix] = self.m[ix] | mask
        self.v[ix] = np.where(mask, val, self.v[ix])

    def ell(self, cx, cy, rx, ry, v0, v1=None, ang=0.0, light=(-0.7, -0.7)):
        r = max(rx, ry) + 1
        gx, gy, ix = self._g(cx - r, cy - r, cx + r, cy + r)
        dx, dy = gx - cx, gy - cy
        ca, sa = np.cos(ang), np.sin(ang)
        u, v = dx * ca + dy * sa, -dx * sa + dy * ca
        m = (u / rx) ** 2 + (v / ry) ** 2 <= 1.0
        if v1 is None:
            val = np.full(m.shape, v0, np.float32)
        else:
            b = np.clip(0.5 + 0.7 * (dx * light[0] + dy * light[1]) / r, 0, 1)
            val = v0 + (v1 - v0) * b
        self._put(ix, m, val)

    def disc(self, cx, cy, r, v0, v1=None, light=(-0.7, -0.7)):
        self.ell(cx, cy, r, r, v0, v1, 0.0, light)

    def seg(self, x0, y0, x1, y1, w, v0, v1=None):
        vx, vy = x1 - x0, y1 - y0
        ll = max(vx * vx + vy * vy, 1e-6)
        r = w / 2 + 1
        gx, gy, ix = self._g(min(x0, x1) - r, min(y0, y1) - r, max(x0, x1) + r, max(y0, y1) + r)
        t = np.clip(((gx - x0) * vx + (gy - y0) * vy) / ll, 0, 1)
        d = np.hypot(gx - (x0 + t * vx), gy - (y0 + t * vy))
        m = d <= w / 2
        val = v0 if v1 is None else v0 + (v1 - v0) * t
        self._put(ix, m, val)

    def rect(self, x0, y0, x1, y1, v0, v1=None):
        gx, gy, ix = self._g(x0, y0, x1 - 1, y1 - 1)
        m = (gx >= x0) & (gx < x1) & (gy >= y0) & (gy < y1)
        val = v0 if v1 is None else v0 + (v1 - v0) * np.clip((gy - y0) / max(y1 - y0 - 1, 1), 0, 1)
        self._put(ix, m, val)

    def tri(self, p0, p1, p2, v0, v1=None):
        xs = [p0[0], p1[0], p2[0]]
        ys = [p0[1], p1[1], p2[1]]
        gx, gy, ix = self._g(min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1)

        def side(a, b):
            return (gx - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (gy - b[1])
        d1, d2, d3 = side(p0, p1), side(p1, p2), side(p2, p0)
        m = ~(((d1 < 0) | (d2 < 0) | (d3 < 0)) & ((d1 > 0) | (d2 > 0) | (d3 > 0)))
        val = v0 if v1 is None else v0 + (v1 - v0) * np.clip((gy - min(ys)) / max(max(ys) - min(ys), 1), 0, 1)
        self._put(ix, m, val)

    def apply(self, rgb: np.ndarray, pal: np.ndarray, d: float = 0.7) -> np.ndarray:
        return np.where(self.m[..., None], pq(self.v, pal, d), rgb)


def masonry(h: int, w: int, row_h, seed: int, wmin: int, wmax: int):
    """Courses of stones of random width: returns (id, lx, ly, sw, sh) arrays; every row wraps exactly across the width."""
    rng = _rng(seed)
    sid = np.zeros((h, w), np.int32)
    lx = np.zeros((h, w), np.float32)
    ly = np.zeros((h, w), np.float32)
    sw = np.zeros((h, w), np.float32)
    sh = np.zeros((h, w), np.float32)
    y, k = 0, 0
    for rh in row_h:
        widths, tot = [], 0
        while tot < w:
            ww = int(rng.randint(wmin, wmax + 1))
            if w - (tot + ww) < wmin:
                ww = w - tot
            widths.append(ww)
            tot += ww
        x = int(rng.randint(0, w))
        rows = np.arange(y, y + rh)
        for ww in widths:
            xs = (np.arange(ww) + x) % w
            ix = np.ix_(rows, xs)
            sid[ix] = k
            lx[ix] = np.arange(ww)[None, :]
            ly[ix] = np.arange(rh)[:, None]
            sw[ix] = ww
            sh[ix] = rh
            x = (x + ww) % w
            k += 1
        y += rh
    return sid, lx, ly, sw, sh


def tone_of(sid: np.ndarray, seed: int) -> np.ndarray:
    return _rng(seed).rand(int(sid.max()) + 1).astype(np.float32)[sid]


def starfield(h: int, w: int, seed: int, count: int, fade=None):
    """Single-pixel stars of a few brightnesses plus a handful with a small cross: returns an index map 0..4 (0 none)."""
    rng = _rng(seed)
    out = np.zeros((h, w), np.int8)
    for _ in range(count):
        x, y = int(rng.randint(0, w)), int(rng.randint(0, h))
        if fade is not None and rng.rand() > fade(y):
            continue
        r = rng.rand()
        lv = 1 if r < 0.55 else 2 if r < 0.85 else 3 if r < 0.96 else 4
        out[y, x] = max(out[y, x], lv)
        if lv == 4:
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                out[(y + dy) % h, (x + dx) % w] = max(out[(y + dy) % h, (x + dx) % w], 2)
    return out


STAR_PAL = ramp("#000000", "#3c4a78", "#7a8cc0", "#c4d4f0", "#ffffff")


def stamp_stars(rgb: np.ndarray, st: np.ndarray, pal: np.ndarray = STAR_PAL) -> np.ndarray:
    m = st > 0
    out = rgb.copy()
    out[m] = (pal[st[m].astype(int)] * 255 + 0.5).astype(np.uint8)
    return out


# =================================================================================================================================================
# ORCHARD: deep greens, harvest gold, amber lamplight, warm timber; the ford is blue-black with silver
# =================================================================================================================================================
O_GRASS = ramp("#07140a", "#102a12", "#1c4616", "#2f6a1c", "#58861f", "#8da02c", "#c9b347")
O_LEAF = ramp("#2a1606", "#5a3410", "#8a5614", "#b8801e", "#dcae38", "#f4dc6c")
O_APPLE = ramp("#3a0606", "#780f0c", "#b02216", "#dc4228", "#f68c52", "#ffd0a0")
O_DIRT = ramp("#140b06", "#2a1a0e", "#46301a", "#664626", "#866236", "#a88450")
O_STONE = ramp("#16130f", "#2a2620", "#443e34", "#625a4c", "#83796a", "#aca08c")
O_OAK = ramp("#140a04", "#2c1a0a", "#4a2e12", "#6c4519", "#8f6226", "#b8873a")
O_WATER = ramp("#010309", "#050a1a", "#0a1630", "#112a4a", "#1e4468", "#3c6c92", "#b4d2e8", "#f4faff")
O_MUD = ramp("#070b09", "#101812", "#1c281c", "#2e3c2a", "#455238", "#646c4c")
O_HEDGE = ramp("#02080a", "#071a0c", "#0d2e14", "#17481e", "#276a28", "#3f8c34", "#74b44a")
O_PLASTER = ramp("#2c2218", "#54442e", "#826c48", "#b09868", "#d4c08c", "#f0e2b4")
O_TIMBER = ramp("#0a0603", "#1a0f07", "#2e1c0d", "#47301a", "#654628", "#86602f")
O_GREYWOOD = ramp("#14110e", "#2a2622", "#44403a", "#625c52", "#827a6c", "#a49c8a")
O_REED = ramp("#01050b", "#041020", "#0a2030", "#12384a", "#1c5662", "#2c7a7c", "#5aa8a4", "#c4e4e2")
O_SMOKE = ramp("#1c1408", "#3c2a10", "#684c1c", "#98742c", "#c29c44", "#e4c46c")
O_FIRE = ramp("#1a0804", "#4a1608", "#8a3010", "#cc5a14", "#f09a2c", "#ffe080")
O_PEWTER = ramp("#16171a", "#2c2e34", "#4a4e58", "#707684", "#9aa2b2", "#cfd6e2")
O_LEAD = ramp("#050608", "#10131a", "#20242e", "#363c48")
O_GLASS = ramp("#010206", "#050a16", "#0a1428", "#142640", "#26446a", "#5880a8")
O_HERB = ramp("#0e1a0c", "#1e3416", "#34522a", "#56753a", "#82965a", "#aab67c")
O_SKY = ramp("#0a0824", "#161040", "#2a1658", "#4c2268", "#7e2e70", "#b04864", "#dc7448", "#f4a63a", "#ffcf5c", "#fff0a0")
O_NIGHT = ramp("#010208", "#04061a", "#0a0e2c", "#141c44", "#202e60")


@tex("orchard", "floor_grass")
def floor_grass(n):
    rng = _rng(111)
    sh = 0.10 + 0.40 * nz(n, 10, 101, 3) + 0.30 * np.clip((nz(n, 22, 102, 2) - 0.5) * 3.2, 0, 1)
    rgb = pq(sh, O_GRASS, 0.9)
    L = Layer(n)
    for x, y in rpts(n, n, 26, 103, 4):  # dark tuft shadows
        L.seg(x, y, x + rng.uniform(-1, 1), y - rng.randint(3, 5), 1.3, 0.04)
    rgb = L.apply(rgb, O_GRASS)
    L = Layer(n)
    for x, y in rpts(n, n, 52, 104, 3):  # bright blades
        L.seg(x, y, x + rng.uniform(-1.2, 1.2), y - rng.randint(3, 6), 1.1, 0.55 + 0.4 * rng.rand())
    rgb = L.apply(rgb, O_GRASS)
    L = Layer(n)
    for x, y in rpts(n, n, 12, 105, 9):  # fallen leaves
        L.ell(x, y, rng.uniform(2.4, 3.4), rng.uniform(1.3, 1.9), 0.30 + 0.2 * rng.rand(), 0.85, rng.uniform(0, 3.14))
    rgb = L.apply(rgb, O_LEAF, 0.6)
    D = Layer(n)
    L = Layer(n)
    for k, (x, y) in enumerate(rpts(n, n, 3, 106, 18)):  # windfall apples with a ground shadow
        D.ell(x + 1.5, y + 1.8, 3.6, 2.2, 0.02)
        L.disc(x, y, 3.0, 0.38, 0.96)
        L.m[int(y) % n, int(x) % n] = True
    rgb = D.apply(rgb, O_GRASS)
    rgb = L.apply(rgb, O_APPLE, 0.5)
    return rgb


@tex("orchard", "floor_lane")
def floor_lane(n):
    rng = _rng(121)
    x, y = grid(n)
    w = nz(n, 16, 122, 2)
    rut = np.cos(2 * np.pi * (y / n * 2) + (w - 0.5) * 2.4)
    sh = 0.36 + 0.28 * nz(n, 6, 123, 3) - 0.20 * np.clip(rut, 0, 1) + 0.12 * np.clip(-rut, 0, 1)
    sh += 0.14 * speck(n, n, 0.06, 124) - 0.14 * speck(n, n, 0.05, 125)
    rgb = pq(sh, O_DIRT, 0.9)
    D = Layer(n)
    L = Layer(n)
    for px, py in rpts(n, n, 22, 126, 5):
        rx, ry = rng.uniform(1.4, 3.2), rng.uniform(1.0, 2.0)
        D.ell(px + 1, py + 1.3, rx + 0.5, ry + 0.4, 0.02)
        L.ell(px, py, rx, ry, 0.36 + 0.14 * rng.rand(), 0.92, rng.uniform(0, 3.14))
    rgb = D.apply(rgb, O_DIRT)
    return L.apply(rgb, O_STONE, 0.6)


@tex("orchard", "floor_ford")
def floor_ford(n):
    x, y = grid(n)
    f1, f2, ids = worley(n, n, jpts(n, n, 7, 7, 131, 0.8))
    pebble = 0.10 + 0.20 * _rng(132).rand(49)[ids] - 0.10 * (f2 - f1 < 1.4) + 0.012 * f1
    wy = nz(n, 20, 133, 2)
    a = np.sin(2 * np.pi * (3 * y / n + (wy - 0.5) * 0.9))
    br = pnc(n, n, 12, 2, 134, 2)
    ln = np.clip(1 - np.abs(a) / 0.16, 0, 1) * (br > 0.42)
    a2 = np.sin(2 * np.pi * (5 * y / n + (nz(n, 20, 135, 2) - 0.5) * 1.1 + 0.3))
    ln2 = np.clip(1 - np.abs(a2) / 0.10, 0, 1) * (pnc(n, n, 10, 3, 136, 2) > 0.58)
    sh = pebble * 0.85 + 0.70 * ln + 0.38 * ln2
    sh = np.where(ln > 0.8, 0.94, sh)
    return pq(sh, O_WATER, 0.7)


@tex("orchard", "floor_bank")
def floor_bank(n):
    rng = _rng(141)
    sh = 0.22 + 0.30 * nz(n, 9, 142, 3)
    f1, f2, ids = worley(n, n, jpts(n, n, 6, 6, 143, 0.9))
    sh += 0.0
    rgb = pq(sh, O_MUD, 0.9)
    wet = np.clip((nz(n, 16, 144, 2) - 0.55) * 5, 0, 1)  # wet sheen patches
    rgb = tint(rgb, "#3a5a62", wet * 0.35)
    D = Layer(n)
    L = Layer(n)
    for px, py in rpts(n, n, 17, 145, 5):
        rx, ry = rng.uniform(1.8, 3.6), rng.uniform(1.3, 2.4)
        D.ell(px + 0.8, py + 1.2, rx + 0.6, ry + 0.5, 0.02)
        L.ell(px, py, rx, ry, 0.30 + 0.12 * rng.rand(), 0.88, rng.uniform(0, 3.14))
    rgb = D.apply(rgb, O_MUD)
    rgb = L.apply(rgb, O_STONE * np.array([0.78, 0.92, 0.95], np.float32), 0.6)
    R = Layer(n)
    for px, py in rpts(n, n, 6, 146, 10):  # reed stubs
        for k in range(rng.randint(2, 4)):
            ox = k * 2 - 2
            R.seg(px + ox, py, px + ox + rng.uniform(-1, 1), py - rng.randint(3, 6), 1.8, 0.3, 0.72)
    return R.apply(rgb, O_REED, 0.5) if False else R.apply(rgb, O_HERB, 0.5)


@tex("orchard", "floor_boards")
def floor_boards(n):
    rng = _rng(151)
    x, y = grid(n)
    ph = 16
    row = (y // ph).astype(int)
    off = rng.randint(0, n, 4)
    jx = (x + off[row]) % n
    ptone = rng.rand(4, 3)
    seg = (jx // (n / 2.0)).astype(int) % 2  # two boards per row with butt joints
    t = ptone[row, seg]
    grain = pnc(n, n, 30, 2, 152, 2)
    sh = 0.38 + 0.20 * t + (grain - 0.5) * 0.46
    stain = np.clip((nz(n, 18, 153, 3) - 0.60) * 6, 0, 1)
    edge = np.abs(nz(n, 18, 153, 3) - 0.60) < 0.016
    sh = sh - 0.26 * stain - 0.2 * edge
    joint = ((y % ph) < 1) | ((jx % (n / 2.0)) < 1)
    sh = np.where(joint, 0.02, sh)
    sh = np.where(((y % ph) == 1) & ~joint, sh + 0.14, sh)
    rgb = pq(sh, O_OAK, 0.8)
    L = Layer(n)
    for k in range(4):
        for j in range(2):
            jxp = (-off[k] + j * n / 2.0) % n
            for dy in (3, 12):
                L.rect(jxp + 3, k * ph + dy, jxp + 4, k * ph + dy + 1, 0.05)
    for kx, ky in ((20, 24), (50, 52)):  # knots
        L.ell(kx, ky, 3.4, 2.2, 0.12)
        L.ell(kx, ky, 1.8, 1.1, 0.34)
        L.ell(kx, ky, 0.8, 0.5, 0.05)
    return L.apply(rgb, O_OAK, 0.5)


@tex("orchard", "floor_flags")
def floor_flags(n):
    pts = jpts(n, n, 4, 4, 161, 0.95)
    f1, f2, ids = worley(n, n, pts)
    edge = f2 - f1
    tone = _rng(162).rand(16)[ids]
    sh = 0.16 + 0.22 * tone + 0.16 * np.clip(edge / 7.0, 0, 1) + (nz(n, 6, 163, 3) - 0.5) * 0.26 + 0.02 * speck(n, n, 0.08, 164)
    sh = sh - 0.1 * ((edge < 3.2) & (edge >= 1.6))
    rgb = pq(sh, O_STONE * 0.62, 0.9)
    glow = np.clip((nz(n, 7, 165, 2) - 0.38) * 2.6, 0, 1)
    crack = edge < 1.15
    warm = pq(0.10 + 0.78 * glow, O_FIRE, 0.7)
    rgb = sel(crack, warm, rgb)
    rim = (edge >= 1.15) & (edge < 2.6)
    rgb = tint(rgb, "#b04a14", rim * glow * 0.30)
    return rgb


@tex("orchard", "wall_hedge")
def wall_hedge(n):
    rng = _rng(171)
    rgb = pq(0.08 + 0.18 * nz(n, 12, 172, 3), O_HEDGE, 0.8)

    def leaves(rgb, passes, seed, count, golden=0.0):
        rng = _rng(seed)
        L = Layer(n)
        G = Layer(n)
        for p in passes:
            for _ in range(count):
                x, y = rng.rand() * n, rng.rand() * n
                ang = rng.uniform(0, 3.14)
                rx, ry = rng.uniform(3.4, 5.2), rng.uniform(1.8, 2.8)
                b = p + rng.uniform(-0.05, 0.06)
                tgt = G if rng.rand() < golden else L
                tgt.ell(x, y, rx, ry, b - 0.05, b + 0.20, ang)
                tgt.seg(x - np.cos(ang) * rx, y - np.sin(ang) * rx, x + np.cos(ang) * rx, y + np.sin(ang) * rx, 0.9, b - 0.14)
        rgb = L.apply(rgb, O_HEDGE, 0.55)
        return G.apply(rgb, O_LEAF * np.array([0.7, 0.85, 0.5], np.float32), 0.55) if golden else rgb

    rgb = leaves(rgb, (0.10, 0.22), 173, 150)
    # bramble canes weaving through, with thorns
    cane = Layer(n)
    thorn = Layer(n)
    for k, (y0, amp, kk, ph) in enumerate(((30, 9, 1, 0.5), (74, 12, 2, 2.0), (108, 7, 1, 4.0))):
        pts = [(xx, y0 + amp * np.sin(2 * np.pi * kk * xx / n + ph)) for xx in range(0, n + 1, 3)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            cane.seg(ax, ay, bx, by, 2.4, 0.46, 0.26)
        for xx in range(4, n, 11):
            yy = y0 + amp * np.sin(2 * np.pi * kk * xx / n + ph)
            thorn.seg(xx, yy, xx + rng.choice([-2.5, 2.5]), yy + rng.choice([-3, 3]), 1.0, 0.9)
    rgb = cane.apply(rgb, ramp("#0c060a", "#2a1420", "#4e2c34", "#7a4c48"), 0.5)
    rgb = thorn.apply(rgb, ramp("#0c060a", "#2a1420", "#4e2c34", "#7a4c48", "#b09080", "#e8d0c0"), 0.4)
    rgb = leaves(rgb, (0.34, 0.50, 0.64), 174, 160, golden=0.07)
    H = Layer(n)
    S = Layer(n)
    for x, y in rpts(n, n, 11, 175, 18):
        S.disc(x + 1, y + 1, 3.0, 0.02)
        H.disc(x, y, 2.4, 0.42, 0.98)
    rgb = S.apply(rgb, O_HEDGE)
    return H.apply(rgb, O_APPLE, 0.5)


@tex("orchard", "wall_cottage")
def wall_cottage(n):
    x, y = grid(n)
    post_w, beam_h = 10, 10
    px = (x % 64) < post_w
    py = (y % 64) < beam_h
    timber = px | py
    # plaster panels (lit by warm evening light, brighter towards the top left of each panel)
    lx, ly = x % 64 - post_w, y % 64 - beam_h
    pw = 64 - post_w
    sh = 0.66 + 0.18 * nz(n, 10, 181, 3) + 0.14 * (1 - np.clip((lx + ly) / (2 * pw), 0, 1)) - 0.06
    shadow = (np.clip(1 - ly / 6.0, 0, 1) * (ly >= 0)) + (np.clip(1 - (pw - lx) / 5.0, 0, 1) * 0) + np.clip(1 - lx / 4.0, 0, 1) * (lx >= 0) * 0.7
    sh = sh - 0.32 * np.clip(shadow, 0, 1) * (~timber)
    # wattle behind flaked plaster
    fl = (nz(n, 22, 182, 3) > 0.60) & ~timber
    fl &= (lx > 3) & (ly > 3) & (lx < pw - 3) & (ly < pw - 3)
    edge_top = fl & ~shift(fl, 1, 0)
    edge_left = fl & ~shift(fl, 0, 1)
    edge_bot = fl & ~shift(fl, -1, 0)
    sh = np.where(fl, 0.34 + 0.12 * nz(n, 4, 183, 2), sh)
    rgb = pq(sh, O_PLASTER, 0.8)
    rods = fl & (((y % 7) < 2) | ((x % 13) < 1))
    rgb = sel(rods, pq(np.full((n, n), 0.82, np.float32) + 0.1 * nz(n, 3, 184, 2), O_TIMBER, 0.6), rgb)
    rgb = sel(fl & ~rods, pq(0.42 + 0.2 * nz(n, 3, 188, 2), O_TIMBER, 0.6), rgb)
    rgb = put(rgb, edge_top | edge_left, "#f6ecc8")
    rgb = put(rgb, edge_bot, "#40301c")
    # braces in two panels: diagonal from the lower left to the upper right
    br = Layer(n)
    for ox, oy in ((0, 0), (64, 64)):
        x0, y0 = ox + post_w, oy + beam_h
        br.seg(x0 + 2, y0 + pw - 2, x0 + pw - 2, y0 + 2, 9, 0.5)
    brm = br.m & ~timber
    # timber: grain and bevel
    gr = np.where(px & ~py, pnc(n, n, 2, 40, 185, 2), pnc(n, n, 40, 2, 186, 2))
    tsh = 0.30 + 0.35 * gr
    tsh += 0.18 * (((x % 64) < 1) & px) + 0.18 * (((y % 64) < 1) & py)
    tsh -= 0.22 * (((x % 64) == post_w - 1) & px) + 0.22 * (((y % 64) == beam_h - 1) & py & ~px)
    trgb = pq(tsh, O_TIMBER, 0.7)
    rgb = sel(timber, trgb, rgb)
    brsh = 0.26 + 0.30 * pnc(n, n, 14, 14, 187, 2) - 0.2 * (np.abs((x + y) % 64 - 31) > 0) * 0
    rgb = sel(brm, pq(brsh, O_TIMBER, 0.7), rgb)
    nails = ((x % 64 == 4) | (x % 64 == 5)) & ((y % 16) == 6) & (y % 64 >= beam_h)
    rgb = put(rgb, nails, "#080402")
    return rgb


@tex("orchard", "wall_fence")
def wall_fence(n):
    rng = _rng(191)
    x, y = grid(n)
    # night hedge behind, dark
    rgb = pq(0.12 + 0.28 * nz(n, 8, 192, 3) * (1 - 0.5 * np.clip(y / 38, 0, 1)), O_HEDGE, 0.9)
    L = Layer(n)
    for _ in range(40):  # leaf flecks behind the rails
        L.ell(rng.rand() * n, rng.rand() * 36, 2.4, 1.3, 0.12, 0.34, rng.uniform(0, 3.14))
    rgb = L.apply(rgb, O_HEDGE, 0.6)
    # posts
    P = np.zeros((n, n), bool)
    for cx in (14, 46):
        P |= (x >= cx - 4) & (x < cx + 4) & (y >= 1) & (y < 40)
    gy = pnc(n, n, 2, 30, 193, 2)
    psh = 0.34 + 0.36 * gy
    pxl = (x - 10) % 32
    psh += 0.2 * (pxl < 1.5) - 0.24 * (pxl >= 6.5)
    rgb = sel(P, pq(psh, O_GREYWOOD, 0.7), rgb)
    rgb = put(rgb, P & (y < 3) & (y >= 1), "#b4ac98")
    # rails in front of the posts
    for (ya, yb) in ((9, 17), (22, 30)):
        R = (y >= ya) & (y < yb)
        gx = pnc(n, n, 40, 3, 194 + ya, 2)
        rsh = 0.34 + 0.34 * gx + 0.2 * (y == ya) - 0.26 * (y == yb - 1) - 0.14 * (y == yb - 2)
        rgb = sel(R, pq(rsh, O_GREYWOOD, 0.7), rgb)
        for cx in (3, 29):  # split cracks near the rail ends
            rgb = put(rgb, R & (np.abs(x - cx) < 1) & (y == ya + 3), "#18140f")
    # drystone base
    sid, lx, ly, sw, sh = masonry(26, n, [9, 9, 8], 195, 9, 17)
    tone = tone_of(sid, 196)
    cx = (lx + 0.5) / sw
    cyy = (ly + 0.5) / sh
    puff = 1 - 1.6 * ((cx - 0.5) ** 2 + (cyy - 0.5) ** 2)
    ssh = 0.28 + 0.22 * tone + 0.30 * puff + 0.16 * (lx < 1.5) * 0 - 0.1 * (nz(26, 5, 197, 2)[:, :1] * 0)
    ssh += (pnr(26, n, 4, 198, 2) - 0.5) * 0.24
    mort = (lx < 1) | (ly < 1)
    srgb = pq(ssh, O_STONE, 0.8)
    srgb = put(srgb, mort, "#0c0a08")
    srgb = put(srgb, ((ly >= 1) & (ly < 2) & ~mort) | ((lx >= 1) & (lx < 2) & ~mort & (ly > 1)), "#b0a490")
    srgb = tint(srgb, "#2c4a22", np.clip((pnr(26, n, 7, 199, 2) - 0.62) * 4, 0, 1) * (cyy < 0.6) * 0.6)
    rgb[38:] = srgb
    return rgb


@tex("orchard", "wall_reeds")
def wall_reeds(n):
    rng = _rng(201)
    x, y = grid(n)
    mist = pnc(n, n, 4, 2, 202, 3)
    rgb = pq(0.10 + 0.20 * mist + 0.10 * nz(n, 12, 203, 2), O_REED, 0.9)

    def reeds(rgb, count, wd, v0, v1, seed, hi=False):
        rng = _rng(seed)
        L = Layer(n)
        for i in range(count):
            x0 = (i + rng.rand() * 0.9) * n / count
            amp, kk, ph = rng.uniform(0.6, 2.4), 1, rng.uniform(0, 6.28)
            v = rng.uniform(v0, v1)
            ys = np.arange(n)
            xs = x0 + amp * np.sin(2 * np.pi * kk * ys / n + ph)
            for yy in range(0, n, 2):
                xa, xb = xs[yy], xs[(yy + 2) % n]
                L.seg(xa, yy, xb + (0 if yy + 2 < n else 0), yy + 2.0, wd, v, v - 0.05)
            if hi:
                H = np.round(xs - wd / 2 + 0.6).astype(int) % n
                L.v[ys, H] = np.minimum(v + 0.30, 0.98)
            for _ in range(2):  # a leaf blade leaning off the stem
                yy = rng.randint(0, n)
                s = rng.choice([-1, 1])
                L.seg(xs[yy], yy, xs[yy] + s * rng.uniform(5, 9), yy - rng.uniform(8, 16), 1.2, v - 0.02, v + 0.08)
        return L.apply(rgb, O_REED, 0.6)

    rgb = reeds(rgb, 44, 2.0, 0.16, 0.30, 202)
    rgb = tint(rgb, "#1c4a62", (pnc(n, n, 5, 2, 205, 2) - 0.45) * 0.55)
    rgb = reeds(rgb, 26, 3.0, 0.32, 0.50, 206)
    rgb = reeds(rgb, 13, 4.0, 0.46, 0.64, 207, hi=True)
    L = Layer(n)
    for cx_, cy_ in ((30, 40), (88, 84), (112, 22)):  # bulrush heads
        L.ell(cx_, cy_, 2.6, 8.5, 0.12, 0.5)
        L.seg(cx_, cy_ + 7, cx_, cy_ + 20, 1.6, 0.4)
    rgb = L.apply(rgb, ramp("#05080a", "#1a1410", "#3a2a1c", "#6a5238", "#a89070"), 0.5)
    # silver glints
    m = speck(n, n, 0.006, 208) & (pnc(n, n, 3, 3, 209, 1) > 0.5)
    return put(rgb, m, "#d8ecee")


@tex("orchard", "wall_inn")
def wall_inn(n):
    rng = _rng(211)
    x, y = grid(n)
    split = 62
    # smoke-yellow plaster, darkest where the smoke gathers under the beams (top) and stained in blotches
    sh = 0.50 + 0.20 * nz(n, 10, 212, 3) - 0.28 * np.clip(1 - y / 26, 0, 1) - 0.12 * np.clip((nz(n, 22, 213, 3) - 0.6) * 4, 0, 1)
    sh += 0.10 * np.clip(1 - np.abs(y - 40) / 18, 0, 1)
    rgb = pq(sh, O_SMOKE, 0.8)
    # oak panelling with fielded panels
    pan = y >= split + 6
    lxp = x % 32
    ly = y - (split + 6)
    ph = n - (split + 6)
    fx = (lxp >= 5) & (lxp < 27)
    fy = (ly >= 5) & (ly < ph - 5)
    field = fx & fy
    base = 0.34 + 0.22 * pnc(n, n, 40, 2, 214, 2)
    stile = base + 0.10 * (lxp < 1) - 0.16 * (lxp >= 31)
    fsh = base - 0.10 + 0.0
    fsh = fsh + 0.20 * (((lxp == 5) | (ly == 5)) & field) - 0.20 * (((lxp == 26) | (ly == ph - 6)) & field)
    psh = np.where(field, fsh, stile)
    prgb = pq(psh * 0.92 - 0.04, O_OAK, 0.8)
    prgb = put(prgb, (lxp == 0) & pan, "#0a0502")
    rgb = sel(pan, prgb, rgb)
    # dado rail
    rail = (y >= split) & (y < split + 6)
    rsh = 0.42 + 0.3 * pnc(n, n, 2, 40, 215, 2) + 0.2 * (y == split) - 0.25 * (y == split + 5)
    rgb = sel(rail, pq(rsh, O_OAK, 0.7), rgb)
    rgb = put(rgb, (y == split + 6) & True, "#07040a")
    # shadow cast by the rail on the panelling
    rgb = tint(rgb, "#000000", pan * np.clip(1 - (y - split - 6) / 4.0, 0, 1) * 0.45)
    # pegs, pewter mugs, herbs
    S = Layer(n)
    L = Layer(n)
    for cx in (22, 64, 106):
        S.ell(cx + 2, 40 + 2, 6, 7, 0.0)
        L.seg(cx, 30, cx, 33, 3, 0.2)
        L.ell(cx, 42, 5.0, 6.5, 0.18, 0.95)
        L.rect(cx - 5, 36, cx + 5, 38, 0.65, 0.5)
        L.ell(cx + 6, 42, 3.0, 3.8, 0.35, 0.8)
        L.ell(cx + 6, 42, 1.6, 2.4, 0.0)
        L.rect(cx - 3, 38, cx - 1, 49, 0.9)
    rgb = S.apply(rgb, O_SMOKE * 0.4)
    rgb = L.apply(rgb, O_PEWTER, 0.6)
    H = Layer(n)
    Sh = Layer(n)
    for bx, by in ((40, 10), (88, 10)):
        Sh.ell(bx + 2, by + 14, 6, 14, 0.0)
        for k in range(14):
            ox = rng.uniform(-5, 5)
            ln = rng.uniform(16, 26)
            H.seg(bx + ox * 0.3, by, bx + ox, by + ln, 1.8, 0.35 + 0.5 * rng.rand(), 0.2 + 0.4 * rng.rand())
        H.rect(bx - 3, by, bx + 3, by + 3, 0.2)
    rgb = Sh.apply(rgb, O_SMOKE * 0.4)
    rgb = H.apply(rgb, O_HERB, 0.6)
    return rgb


@tex("orchard", "wall_inn_door")
def wall_inn_door(n):
    rng = _rng(221)
    x, y = grid(n)
    pw = 16
    pid = (x // pw).astype(int)
    tone = rng.rand(8)[pid]
    lx = x % pw
    grain = pnc(n, n, 3, 56, 222, 3)
    sh = 0.30 + 0.22 * tone + (grain - 0.5) * 0.5 + 0.1 * (lx < 1.5) - 0.2 * (lx >= pw - 1.5)
    sh = np.where(lx == pw - 1, 0.0, sh)
    rgb = pq(sh, O_OAK, 0.8)
    # grain knots
    K = Layer(n)
    for kx, ky in ((24, 36), (72, 86), (104, 20)):
        K.ell(kx, ky, 3.0, 5.0, 0.10)
        K.ell(kx, ky, 1.4, 3.0, 0.32)
    rgb = K.apply(rgb, O_OAK, 0.5)
    # iron straps with studs
    for (ya, yb) in ((13, 25), (56, 66), (101, 113)):
        S = (y >= ya) & (y < yb)
        ssh = 0.30 + 0.28 * pnc(n, n, 6, 28, 223 + ya, 2) + 0.28 * (y == ya) - 0.2 * (y == yb - 1)
        rgb = sel(S, pq(ssh, ramp("#07080b", "#12141a", "#20242c", "#343a46", "#586072", "#8890a4"), 0.7), rgb)
    L = Layer(n)
    for (ya, yb) in ((13, 25), (56, 66), (101, 113)):
        for xx in range(8, n, 16):
            L.disc(xx, (ya + yb) / 2, 2.2, 0.35, 1.0)
    rgb = L.apply(rgb, ramp("#07080b", "#12141a", "#20242c", "#343a46", "#586072", "#aab0c4"), 0.4)
    # ring handle
    ring = Layer(n)
    ring.disc(96, 76, 7.5, 0.55, 0.9)
    ring.disc(96, 76, 5.3, 0.0)
    ring.disc(96, 69, 3.4, 0.3, 0.8)
    rgb = ring.apply(rgb, ramp("#07080b", "#12141a", "#20242c", "#343a46", "#586072", "#aab0c4"), 0.4)
    Sd = Layer(n)
    Sd.ell(98, 80, 8, 7, 0.0)
    # lamplight spilling under the door
    g = np.clip((y - 104) / 24.0, 0, 1) ** 1.6
    rgb = tint(rgb, "#f29a30", g * 0.55)
    gap = y >= 123
    gsh = 0.35 + 0.65 * np.clip((y - 123) / 4.0, 0, 1) + (nz(n, 6, 227, 2) - 0.5) * 0.2
    rgb = sel(gap, pq(gsh, O_FIRE, 0.6), rgb)
    return rgb


@tex("orchard", "wall_inn_window")
def wall_inn_window(n):
    rng = _rng(231)
    x, y = grid(n)
    sh = 0.46 + 0.22 * nz(n, 10, 232, 3) - 0.28 * np.clip(1 - y / 22, 0, 1) - 0.10 * np.clip((nz(n, 22, 233, 3) - 0.6) * 4, 0, 1)
    rgb = pq(sh, O_SMOKE, 0.8)
    for x0 in (14, 74):
        fx0, fy0, fx1, fy1 = x0 - 5, 25, x0 + 37, 105  # outer frame
        gx0, gy0, gx1, gy1 = x0, 31, x0 + 32, 91  # glass 32 x 60
        fr = (x >= fx0) & (x < fx1) & (y >= fy0) & (y < fy1)
        gl = (x >= gx0) & (x < gx1) & (y >= gy0) & (y < gy1)
        tsh = 0.32 + 0.3 * pnc(n, n, 12, 12, 234 + x0, 2) + 0.2 * ((x == fx0) | (y == fy0)) - 0.2 * ((x == fx1 - 1) | (y == fy1 - 1))
        rgb = sel(fr, pq(tsh, O_TIMBER, 0.7), rgb)
        # sill: pale stone ledge
        sill = (y >= fy1) & (y < fy1 + 5) & (x >= fx0 - 3) & (x < fx1 + 3)
        ssh = 0.5 + 0.2 * (y == fy1) - 0.3 * (y == fy1 + 4) + (nz(n, 4, 235, 2) - 0.5) * 0.2
        rgb = sel(sill, pq(ssh, O_STONE, 0.7), rgb)
        rgb = tint(rgb, "#000000", (y >= fy1 + 5) * (y < fy1 + 9) * (x >= fx0) * (x < fx1) * 0.4)
        # leaded diamond panes over night glass
        u, v = (x - gx0) / 8.0, (y - gy0) / 12.0
        a, b = np.floor(u + v), np.floor(u - v)
        f1 = (u + v) % 1
        f2 = (u - v) % 1
        lead = (np.minimum(f1, 1 - f1) < 0.075) | (np.minimum(f2, 1 - f2) < 0.075)
        glass = 0.18 + 0.14 * np.clip(1 - (y - gy0) / 50.0, 0, 1) + 0.03 * ((a + b) % 2)
        glass = glass + 0.5 * np.clip(1 - np.abs((u * 8 + (y - gy0) * 0.8) % 40 - 8) / 2.0, 0, 1) * 0.35
        gsh = np.where(lead, 0.05, glass)
        grgb = pq(gsh, O_GLASS, 0.6)
        grgb = sel(lead, pq(0.2 + 0.2 * (nz(n, 3, 236, 2)), O_LEAD, 0.6), grgb)
        if x0 == 14:
            cu, cv = 2.0, 2.5
            dist = np.abs(u - cu) * 0.9 + np.abs(v - cv) * 0.75
            lit = (a == 4) & (b == -1) & ~lead
            warm = pq(0.55 + 0.45 * np.clip(1 - dist / 0.9, 0, 1), O_FIRE, 0.4)
            grgb = sel(lit, warm, grgb)
            nb = ((((a == 3) | (a == 5)) & (b == -1)) | ((a == 4) & ((b == 0) | (b == -2)))) & ~lead
            grgb = tint(grgb, "#c4742a", nb * 0.26)
        # shadow inside the recess top / left
        grgb = tint(grgb, "#000000", ((y < gy0 + 3) | (x < gx0 + 2)) * 0.5)
        rgb = sel(gl, grgb, rgb)
        # frame inner bevel
        rgb = put(rgb, fr & ~gl & ((x == gx0 - 1) | (y == gy0 - 1)) & (x >= gx0 - 1) & (y >= gy0 - 1) & (x <= gx1) & (y <= gy1), "#0a0502")
    return rgb


@tex("orchard", "ceil_beams")
def ceil_beams(n):
    rng = _rng(241)
    x, y = grid(n)
    by = (y % 32) < 15
    sh = 0.50 + 0.20 * nz(n, 8, 242, 3) - 0.1 * np.clip((nz(n, 14, 243, 3) - 0.55) * 4, 0, 1)
    rgb = pq(sh, O_SMOKE * 0.8, 0.8)
    lyy = y % 32
    gr = pnc(n, n, 24, 2, 244, 2)
    bsh = 0.18 + 0.28 * gr + 0.18 * (lyy < 1) * 0 - 0.1 * (lyy >= 12) + 0.14 * (lyy < 2)
    bsh -= 0.12 * (nz(n, 10, 245, 3) > 0.7)
    rgb = sel(by, pq(bsh, O_TIMBER, 0.8), rgb)
    rgb = put(rgb, (lyy == 15), "#050302")
    rgb = tint(rgb, "#000000", (~by) * np.clip(1 - (lyy - 15) / 4.0, 0, 1) * 0.5)
    # hanging herb bundles, seen from below as sprays from a tied point
    S = Layer(n)
    H = Layer(n)
    for bx, byy in ((10, 24), (42, 25), (53, 56)):
        for k in range(10):
            ang = rng.uniform(-1.2, 1.2)
            ln = rng.uniform(4, 7)
            H.seg(bx, byy, bx + np.sin(ang) * ln, byy + np.cos(ang) * ln * 0.8 + 1, 1.5, 0.35 + 0.5 * rng.rand(), 0.2 + 0.3 * rng.rand())
        H.disc(bx, byy, 1.6, 0.15)
    return H.apply(rgb, O_HERB, 0.6)


def _night_ceiling(n, seed, base_pal, cloud_hex, nstar, cloud_cut=0.56):
    x, y = grid(n)
    sh = 0.10 + 0.20 * nz(n, 20, seed, 3)
    rgb = pq(sh, base_pal, 0.9)
    cl = np.clip((pnc(n, n, 5, 2, seed + 1, 3) - cloud_cut) * 5, 0, 1)
    thin = np.clip(1 - np.abs(pnc(n, n, 9, 2, seed + 2, 2) - 0.5) / 0.07, 0, 1)
    rgb = tint(rgb, cloud_hex, cl * 0.34 + thin * 0.20)
    st = starfield(n, n, seed + 3, nstar)
    st[(cl > 0.5) | (thin > 0.4)] = np.where(st[(cl > 0.5) | (thin > 0.4)] > 2, 1, 0)
    return stamp_stars(rgb, st)


@tex("orchard", "ceil_stars")
def ceil_stars(n):
    return _night_ceiling(n, 251, O_NIGHT, "#6070a8", 150)


@tex("orchard", "sky_dusk")
def sky_dusk():
    h, w = 64, 256
    x, y = grid2(h, w)
    warp = (pnc(h, w, 3, 4, 261, 3) - 0.5) * 0.08
    t = np.clip(y / (h - 1) + warp, 0, 1)
    sh = 0.02 + 0.98 * t ** 1.15
    cl = np.clip((pnc(h, w, 9, 6, 262, 3) - 0.50) * 3.2, 0, 1) * np.clip((y - 14) / 22.0, 0, 1) * np.clip((62 - y) / 10.0, 0, 1)
    thin = np.clip(1 - np.abs(pnc(h, w, 14, 5, 263, 2) - 0.5) / 0.05, 0, 1) * (y > 22) * (y < 58)
    # clouds are darker violet bodies lit amber along their lower edge
    up = cl > 0.35
    lower_edge = up & ~shift(up, -1, 0)
    lower_edge2 = up & ~shift(up, -2, 0)
    sh_c = sh - 0.32 * cl
    sh_c = np.where(lower_edge | lower_edge2, sh + 0.12, sh_c)
    sh_c = np.where(thin > 0.5, sh - 0.20, sh_c)
    rgb = pq(sh_c, O_SKY, 0.9)
    st = starfield(h, w, 264, 56, fade=lambda yy: 0.95 if yy < 8 else (0.35 if yy < 16 else 0.0))
    st[(cl > 0.25)] = 0
    return stamp_stars(rgb, st)


# =================================================================================================================================================
# BIRCH HALL: white, silver, pale grey-blue, birch-bark white with dark marks; the pass is snow and slate
# =================================================================================================================================================
B_BARK = ramp("#262a32", "#586270", "#8a96a4", "#b8c2cc", "#dce4ea", "#f2f6f8", "#ffffff")
B_WOOD = ramp("#4a4036", "#807262", "#a89a86", "#cfc2ae", "#e8dfcf", "#f8f3e8")
B_SNOW = ramp("#26344e", "#4c6488", "#7c98bc", "#aec4e0", "#d8e6f4", "#ffffff")
B_SLATE = ramp("#05080e", "#101822", "#1e2c3c", "#30445a", "#4a627c", "#6c88a6")
B_PLASTER = ramp("#343e52", "#626e88", "#929eb4", "#bcc6d6", "#dde4ee", "#f8fafc")
B_SILVER = ramp("#262c36", "#565e70", "#8a94a8", "#bcc6d6", "#e6edf6", "#ffffff")
B_ICE = ramp("#06101e", "#142c4a", "#2c5886", "#68a4d0", "#b8e0f6", "#ffffff")
B_ROCK = ramp("#010206", "#04060c", "#080c16", "#0e1624", "#16243a", "#26405e", "#4a7ca8", "#b0d6f0")
B_SKY = ramp("#68768e", "#8898b0", "#a8b6c8", "#c4cfdc", "#e0e7ef", "#f7f9fb")


@tex("birch_hall", "floor_birch")
def floor_birch(n):
    rng = _rng(311)
    x, y = grid(n)
    bx, by = (x // 16).astype(int), (y // 16).astype(int)
    horiz = ((bx + by) % 2) == 0
    sx, sy = ((x % 16) // 4).astype(int), ((y % 16) // 4).astype(int)
    strip = np.where(horiz, sy, sx)
    tone = rng.rand(4, 4, 4)[by % 4, bx % 4, strip]
    gh = pnc(n, n, 24, 3, 312, 2)
    gv = pnc(n, n, 3, 24, 313, 2)
    grain = np.where(horiz, gh, gv)
    sh = 0.62 + 0.18 * tone + (grain - 0.5) * 0.22 + 0.06 * np.cos(2 * np.pi * (x + y) / n)
    edge = np.where(horiz, (y % 4) == 3, (x % 4) == 3)
    hi = np.where(horiz, (y % 4) == 0, (x % 4) == 0)
    sh = np.where(edge, sh - 0.30, np.where(hi, sh + 0.10, sh))
    rgb = pq(sh, B_WOOD, 0.7)
    inlay = ((x % 32) == 0) | ((y % 32) == 0)
    shade = (((x % 32) == 1) | ((y % 32) == 1) | ((x % 32) == 31) | ((y % 32) == 31)) & ~inlay
    rgb = sel(shade, pq(sh - 0.32, B_WOOD, 0.4), rgb)
    rgb = sel(inlay, pq(0.82 + 0.15 * (grain - 0.5), B_SILVER, 0.5), rgb)
    return rgb


@tex("birch_hall", "floor_snow")
def floor_snow(n):
    rng = _rng(321)
    sh = 0.58 + 0.22 * nz(n, 12, 322, 3) - 0.20 * np.clip((nz(n, 20, 323, 3) - 0.55) * 4, 0, 1)
    sh += 0.08 * speck(n, n, 0.07, 324) - 0.08 * speck(n, n, 0.05, 325)
    rgb = pq(sh, B_SNOW, 0.9)
    D = Layer(n)
    L = Layer(n)
    prints = [(10, 18), (26, 30), (42, 14), (56, 26), (18, 50), (36, 56), (52, 46)]
    for k, (px, py) in enumerate(prints):
        yo = -2.6 if k % 2 == 0 else 2.6
        D.ell(px + 1, py + yo + 1, 5.0, 3.0, 0.95)
        D.ell(px - 7.0, py + yo + 1, 2.6, 2.2, 0.95)
        L.ell(px, py + yo, 5.0, 3.0, 0.30, 0.52)
        L.ell(px - 8.0, py + yo, 2.6, 2.2, 0.30, 0.52)
    rgb = D.apply(rgb, B_SNOW, 0.3)
    rgb = L.apply(rgb, B_SNOW * np.array([0.72, 0.76, 0.84], np.float32), 0.5)
    g = Layer(n)
    for gx, gy in rpts(n, n, 9, 326, 5):
        g.rect(gx, gy, gx + 1, gy + 1, 1.0)
        if rng.rand() < 0.5:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                g.rect(gx + dx, gy + dy, gx + dx + 1, gy + dy + 1, 0.8)
    return g.apply(rgb, B_SNOW, 0.0)


@tex("birch_hall", "floor_snow_rock")
def floor_snow_rock(n):
    x, y = grid(n)
    field = nz(n, 16, 331, 4)
    snow = field > 0.47
    rock_sh = 0.40 + 0.42 * pnc(n, n, 16, 3, 332, 2) + (nz(n, 5, 333, 2) - 0.5) * 0.3
    f1, f2, _ = worley(n, n, jpts(n, n, 3, 3, 334, 0.9))
    rock_sh = np.where((f2 - f1) < 1.1, 0.02, rock_sh)
    rgb = pq(rock_sh, B_SLATE, 0.85)
    srgb = pq(0.64 + 0.22 * nz(n, 9, 335, 3) + 0.08 * speck(n, n, 0.06, 336), B_SNOW, 0.9)
    near_rock = ~snow & (shift(snow, 1, 0) | shift(snow, -1, 0) | shift(snow, 0, 1) | shift(snow, 0, -1))
    edge_snow = snow & (~shift(snow, 1, 0) | ~shift(snow, 0, 1) | ~shift(snow, -1, 0) | ~shift(snow, 0, -1))
    rgb = sel(snow, srgb, rgb)
    rgb = put(rgb, edge_snow, "#f4f8ff")
    rgb = put(rgb, near_rock, "#070b12")
    rgb = tint(rgb, "#16243c", snow * (~shift(snow, 2, 0) | ~shift(snow, 0, 2)) * 0.5)
    return rgb


@tex("birch_hall", "wall_birch")
def wall_birch(n):
    rng = _rng(341)
    x, y = grid(n)
    widths = [18, 20, 16, 22, 17, 19, 16]
    x0s = np.cumsum([0] + widths[:-1])
    rgb = np.zeros((n, n, 3), np.uint8)
    rgb[:] = col("#0a0c12")
    streak = pnc(n, n, 26, 3, 342, 3)
    L = Layer(n)
    H = np.zeros((n, n), bool)
    for ti, (x0, wd) in enumerate(zip(x0s, widths)):
        u = np.clip((x - x0) / wd, 0, 0.999)
        inside = (x >= x0) & (x < x0 + wd)
        cyl = np.clip(np.cos((u - 0.30) * 2.0), 0, 1) ** 0.7
        b = 0.14 + 0.82 * cyl
        sh = b + (streak - 0.5) * 0.26 + 0.05 * rng.randn()
        peel = (pnc(n, n, 5, 4, 343 + ti, 3) > 0.74)
        sh = np.where(peel, sh + 0.1, sh)
        sh = np.where(((x - x0) < 1) | ((x - x0) >= wd - 1.5), sh * 0.3, sh)
        rgb = sel(inside, pq(sh, B_BARK, 0.8), rgb)
        for _ in range(13):  # dark horizontal marks that follow the curve of the trunk
            yy = rng.uniform(0, n)
            mw = rng.uniform(0.28, 0.75) * wd
            mx = x0 + rng.uniform(0.08, 0.92) * wd - mw / 2
            mx = np.clip(mx, x0 + 2, x0 + wd - 2 - mw)
            hh = rng.choice([1.2, 1.6, 2.4])
            for px in np.arange(mx, mx + mw, 1.0):
                uu = (px - x0) / wd
                cv = (uu - 0.5) ** 2 * 5
                L.rect(px, yy + cv, px + 1, yy + cv + hh, 0.0)
        hx = int(x0 + 0.20 * wd)  # silver highlight, broken
        for yy in range(n):
            if pn_at(np.array([yy / 6.0]), np.array([0.0]), 1, 22, 344 + ti)[0] > 0.38:
                H[yy, hx % n] = True
    rgb = put(rgb, L.m, "#20242c")
    return put(rgb, H & ~L.m, "#ffffff")


@tex("birch_hall", "wall_hall")
def wall_hall(n):
    x, y = grid(n)
    sh = 0.66 + 0.16 * nz(n, 10, 351, 3) + 0.05 * (pnc(n, n, 30, 3, 352, 2) - 0.5)
    sh -= 0.20 * np.clip((nz(n, 24, 353, 3) - 0.58) * 4, 0, 1)
    sh -= 0.10 * np.clip(1 - np.abs(y - 100) / 28.0, 0, 1)
    rgb = pq(sh, B_PLASTER, 0.8)
    rgb = tint(rgb, "#7e96c0", 0.10 * nz(n, 30, 354, 2))
    band = (y >= 40) & (y < 72)
    rgb = sel(band, pq(sh - 0.14, B_PLASTER, 0.8), rgb)
    for yy, c in ((40, "#e8eef8"), (41, "#aab6cc"), (70, "#aab6cc"), (71, "#e8eef8"), (44, "#c4cedc"), (67, "#c4cedc")):
        rgb = put(rgb, y == yy, c)
    rgb = tint(rgb, "#1a2236", ((y == 42) | (y == 69)) * 0.5)
    S = Layer(n)
    L = Layer(n)
    stem = Layer(n)
    for xx in range(0, n + 1, 2):
        yy = 56 + 3.2 * np.sin(2 * np.pi * xx / 32)
        yy2 = 56 + 3.2 * np.sin(2 * np.pi * (xx + 2) / 32)
        stem.seg(xx, yy, xx + 2, yy2, 1.6, 0.35, 0.55)
    for k in range(16):
        lx = k * 8 + 3
        sgn = 1 if k % 2 == 0 else -1
        sy = 56 + 3.2 * np.sin(2 * np.pi * lx / 32)
        ang = sgn * 0.75
        cx, cy = lx + 5.0, sy - sgn * 5.5
        S.ell(cx + 1.4, cy + 1.4, 7.4, 3.3, 0.0, None, ang)
        L.ell(cx, cy, 7.4, 3.3, 0.42, 1.0, ang)
        L.seg(lx, sy, cx, cy, 1.0, 0.4)
    rgb = S.apply(rgb, B_PLASTER * 0.42, 0.3)
    rgb = stem.apply(rgb, B_SILVER, 0.6)
    rgb = L.apply(rgb, B_SILVER, 0.6)
    return rgb


@tex("birch_hall", "wall_hall_door")
def wall_hall_door(n):
    rng = _rng(361)
    x, y = grid(n)
    pw = 8
    pid = (x // pw).astype(int)
    tone = rng.rand(16)[pid]
    lx = x % pw
    grain = pnc(n, n, 3, 60, 362, 3)
    sh = 0.50 + 0.16 * tone + (grain - 0.5) * 0.34 + 0.1 * (lx < 1) - 0.20 * (lx >= pw - 1)
    leaf = x % 64
    sh = np.where((leaf == 0) | (leaf == 63) | (lx == pw - 1), sh - 0.34, sh)
    rgb = pq(sh, B_WOOD, 0.8)
    for (ya, yb) in ((12, 22), (58, 68), (104, 114)):  # silver bands
        S = (y >= ya) & (y < yb)
        ssh = 0.42 + 0.25 * pnc(n, n, 4, 30, 363 + ya, 2) + 0.5 * (y == ya) - 0.42 * (y >= yb - 2)
        rgb = sel(S, pq(ssh, B_SILVER, 0.6), rgb)
    L = Layer(n)
    for (ya, yb) in ((12, 22), (58, 68), (104, 114)):
        for xx in range(8, n, 16):
            L.disc(xx, (ya + yb) / 2 - 0.5, 2.3, 0.5, 1.0)
    rgb = L.apply(rgb, B_SILVER, 0.4)
    R = Layer(n)
    for cx in (55, 119):
        R.disc(cx, 70, 6.5, 0.7, 1.0)
        R.disc(cx, 70, 4.2, 0.0)
        R.disc(cx, 70, 3.0, 0.1)
        R.disc(cx, 62, 2.2, 0.6, 1.0)
    rgb = R.apply(rgb, B_SILVER, 0.4)
    g = np.clip((y - 102) / 26.0, 0, 1) ** 1.5
    rgb = tint(rgb, "#cfe2ff", g * 0.5)
    gap = y >= 123
    rgb = sel(gap, pq(0.7 + 0.3 * np.clip((y - 123) / 4.0, 0, 1) + (nz(n, 6, 364, 2) - 0.5) * 0.16, B_SNOW, 0.5), rgb)
    return rgb


@tex("birch_hall", "wall_rock_snow")
def wall_rock_snow(n):
    x, y = grid(n)
    warp = np.round((pnc(n, n, 3, 2, 372, 2) - 0.5) * 14).astype(int)
    wy = (y.astype(int) + warp) % n
    bounds = np.cumsum([26, 22, 30, 24, 26])
    starts = np.concatenate([[0], bounds[:-1]])
    idx = np.minimum(np.searchsorted(bounds, wy, side="right"), 4)
    local = wy - starts[idx]
    fac = np.array([1.0, 0.6, 1.3, 0.8, 1.1])[idx]
    depth = (2.0 + 8.0 * pnc(n, n, 1, 7, 373, 2)) * fac
    snow = local < depth
    face = 0.20 + 0.40 * pnc(n, n, 2, 28, 374, 3) + (nz(n, 6, 375, 2) - 0.5) * 0.3
    f1, f2, _ = worley(n, n, jpts(n, n, 4, 6, 376, 0.9))
    face = np.where((f2 - f1) < 0.9, face - 0.22, face)
    face = np.where((local >= depth) & (local < depth + 4), face - 0.18, face)
    rgb = pq(face, B_SLATE, 0.8)
    ssh = 0.78 + 0.16 * nz(n, 8, 377, 2) - 0.42 * (local >= depth - 2.2) - 0.1 * (local < 1)
    rgb = sel(snow, pq(ssh, B_SNOW, 0.7), rgb)
    patch = (~snow) & (nz(n, 9, 378, 3) > 0.70)
    rgb = sel(patch, pq(0.55 + 0.25 * nz(n, 4, 379, 2), B_SNOW, 0.7), rgb)
    return put(rgb, (local == 0) & snow, "#ffffff")


@tex("birch_hall", "wall_cave")
def wall_cave(n):
    rng = _rng(381)
    x, y = grid(n)
    base = nz(n, 20, 382, 4)
    sh = 0.10 + 0.22 * base + 0.03 * (pnc(n, n, 20, 4, 383, 2))
    gx = np.roll(base, -1, 1) - np.roll(base, 1, 1)
    ridge = np.clip(1 - np.abs(base - 0.5) / 0.035, 0, 1)
    lit = ridge * (gx < 0)
    sh = sh + 0.50 * lit + 0.16 * ridge
    rgb = pq(sh, B_ROCK, 0.7)
    fr = speck(n, n, 0.30, 384) & (nz(n, 14, 385, 2) > 0.68)
    rgb = put(rgb, fr, "#a8cce8")
    rgb = put(rgb, fr & speck(n, n, 0.3, 386), "#ffffff")
    LD = Layer(n)
    IC = Layer(n)
    for ly, seed in ((32, 387), (96, 388)):  # ledges with icicles
        mask_x = pnc(n, n, 1, 6, seed, 2)[0] > 0.30
        for xx in range(n):
            if mask_x[xx]:
                th = 3 + int(2 * pn_at(np.array([xx / 5.0]), np.array([0.0]), 1, 26, seed + 3)[0] * 2)
                LD.rect(xx, ly, xx + 1, ly + th, 0.30, 0.0)
                LD.rect(xx, ly, xx + 1, ly + 1, 0.95)
        xx = 3
        while xx < n:
            if mask_x[xx % n]:
                ln = rng.randint(5, 17)
                hw = rng.uniform(1.6, 3.2)
                IC.tri((xx - hw, ly + 3), (xx + hw, ly + 3), (xx + rng.uniform(-0.6, 0.6), ly + 3 + ln), 0.95, 0.35)
                IC.seg(xx - hw * 0.5, ly + 3, xx - hw * 0.2, ly + 3 + ln * 0.7, 1.0, 1.0)
            xx += int(rng.randint(5, 9))
    rgb = LD.apply(rgb, B_ICE, 0.6)
    return IC.apply(rgb, B_ICE, 0.5)


@tex("birch_hall", "ceil_hall")
def ceil_hall(n):
    rng = _rng(391)
    x, y = grid(n)
    sh = 0.72 + 0.14 * nz(n, 8, 392, 3)
    rgb = pq(sh, B_PLASTER, 0.8)
    tx = ((x % 32) >= 12) & ((x % 32) < 20)  # cross-ties along y
    tsh = 0.40 + 0.2 * pnc(n, n, 20, 2, 393, 2) + 0.3 * ((x % 32) == 12) - 0.3 * ((x % 32) == 19)
    rgb = sel(tx, pq(tsh, B_WOOD, 0.7), rgb)
    ry = (y % 32) < 13  # birch log rafters along x: round, white, dark marks
    ly = y % 32
    cyl = np.clip(np.cos((ly / 13.0 - 0.42) * 2.2), 0, 1) ** 0.7
    rsh = 0.12 + 0.84 * cyl + (pnc(n, n, 30, 3, 394, 2) - 0.5) * 0.24
    rgb = sel(ry, pq(rsh, B_BARK, 0.8), rgb)
    L = Layer(n)
    for r0 in (0, 32):
        for _ in range(7):
            xx = rng.uniform(0, n)
            wd = rng.uniform(4, 11)
            yy = r0 + rng.uniform(2, 10)
            L.rect(xx, yy, xx + wd, yy + rng.choice([1, 1, 2]), 0.0)
    rgb = put(rgb, L.m, "#20242c")
    rgb = tint(rgb, "#000000", (~ry) * np.clip(1 - (ly - 13) / 4.0, 0, 1) * 0.40)
    return put(rgb, ly == 13, "#2a3244")


@tex("birch_hall", "ceil_overcast")
def ceil_overcast(n):
    rng = _rng(401)
    w = wnoise(n, n, 3, 3, 402, 0.7, 3)
    sh = 0.22 + 0.62 * np.clip((w - 0.25) * 1.5, 0, 1)
    rgb = pq(sh, B_SKY, 0.9)
    L = Layer(n)
    for _ in range(130):
        x0, y0 = rng.uniform(0, n), rng.uniform(0, n)
        ln = rng.uniform(3, 6)
        L.seg(x0, y0, x0 + ln * 0.3, y0 + ln, 1.0, 0.9 + 0.1 * rng.rand())
    return L.apply(rgb, ramp("#8a98b0", "#c4cedc", "#ffffff"), 0.0)


@tex("birch_hall", "sky_snow")
def sky_snow():
    h, w = 64, 256
    x, y = grid2(h, w)
    cl = pnc(h, w, 5, 6, 411, 4)
    stk = pnc(h, w, 9, 3, 412, 3)
    t = y / (h - 1)
    sh = 0.62 + 0.18 * t + (cl - 0.5) * 0.30 + (stk - 0.5) * 0.14
    rgb = pq(sh, B_SKY, 0.9)
    band = np.exp(-((y - 30) / 9.0) ** 2) * (0.35 + 0.4 * pnc(h, w, 2, 5, 413, 2))
    rgb = tint(rgb, "#7c9ac8", band * 0.55)
    xs = np.arange(w)  # distant ridges along the bottom edge, periodic
    far = 6 + 7 * pn_at(xs / w * 7, np.zeros(w), 1, 7, 414) + 3 * pn_at(xs / w * 18, np.zeros(w), 1, 18, 415)
    near = 2 + 6 * pn_at(xs / w * 5, np.zeros(w), 1, 5, 416) + 2.5 * pn_at(xs / w * 24, np.zeros(w), 1, 24, 417)
    fm = y > (h - 1 - far[None, :])
    nm = y > (h - 1 - near[None, :])
    rgb = put(rgb, fm, "#7e90ae")
    rgb = tint(rgb, "#d8e4f4", fm * (y < (h - far[None, :] + 1.5)) * 0.8)
    rgb = sel(nm, pq(0.10 + 0.22 * pnc(h, w, 6, 24, 418, 2), B_SLATE, 0.8), rgb)
    return tint(rgb, "#f0f6ff", nm * (y < (h - near[None, :] + 1.2)) * 0.9)


# =================================================================================================================================================
# DEEP HALLS: black-blue, wet slate, one cold white-cyan light; the falls are black rock, white water and mist
# =================================================================================================================================================
D_STONE = ramp("#010208", "#050914", "#0b1222", "#14203a", "#22344e", "#385470", "#6890a8", "#c4f4ff")
D_WATER = ramp("#000102", "#02050a", "#050c18", "#0a1a2e", "#14304a", "#2a5878", "#8ac8dc", "#eafdff")
D_PLANK = ramp("#040306", "#0d0b10", "#1a1519", "#2a2226", "#3c3238", "#554a50", "#7a7078")
D_MOSS = ramp("#030806", "#0a1a12", "#14301c", "#245a2c", "#3c8038", "#68a850")
D_FALL = ramp("#03060c", "#0a1424", "#16304a", "#2c5878", "#68a0c0", "#b8e0f0", "#f6ffff")
D_NIGHT = ramp("#000106", "#02040e", "#060b1c", "#0e1730", "#1a2a48")


@tex("deep_halls", "floor_deep")
def floor_deep(n):
    x, y = grid(n)
    sid, lx, ly, sw, sh_ = masonry(n, n, [16, 16, 16, 16], 511, 16, 28)
    tone = tone_of(sid, 512)
    cx, cy = (lx + 0.5) / sw, (ly + 0.5) / sh_
    puff = 1 - 1.4 * ((cx - 0.5) ** 2 + (cy - 0.5) ** 2)
    sheen = np.clip(1 - np.abs(((x + y * 0.7) % 64) - 22) / 12.0, 0, 1)
    sh = 0.20 + 0.20 * tone + 0.16 * puff + (nz(n, 5, 513, 3) - 0.5) * 0.18 + 0.20 * sheen * puff
    sh += 0.26 * ((lx < 1.5) & (ly > 1)) * (tone > 0.35) + 0.30 * ((ly >= 1) & (ly < 2.5) & (lx > 1)) * (tone > 0.5)
    rgb = pq(sh, D_STONE, 0.85)
    mort = (lx < 1) | (ly < 1)
    rgb = put(rgb, mort, "#010208")
    wet = speck(n, n, 0.004, 514) & ~mort
    rgb = put(rgb, wet, "#6ac4dc")
    rgb = put(rgb, wet & shift(wet, 0, 1), "#d8faff")
    return rgb


@tex("deep_halls", "floor_bridge")
def floor_bridge(n):
    x, y = grid(n)
    sid, lx, ly, sw, sh_ = masonry(n, n, [22, 20, 22], 521, 26, 36)
    tone = tone_of(sid, 522)
    cx, cy = (lx + 0.5) / sw, (ly + 0.5) / sh_
    puff = 1 - 1.2 * ((cx - 0.5) ** 2 + (cy - 0.5) ** 2)
    wear = np.exp(-(((y - 32) / 11.0) ** 2))
    sh = 0.22 + 0.16 * tone + 0.12 * puff + 0.16 * wear + (nz(n, 5, 523, 3) - 0.5) * 0.2 * (1 - 0.6 * wear)
    sh += 0.24 * ((lx < 1.5) & (ly > 1)) * (tone > 0.3)
    rgb = pq(sh, D_STONE, 0.85)
    rgb = put(rgb, ((lx < 1) | (ly < 1)), "#010208")
    wornglint = (wear > 0.6) & speck(n, n, 0.012, 524)
    rgb = put(rgb, wornglint, "#7ab8cc")
    d = np.minimum(y, n - 1 - y)
    moss = d < (3.5 + 9.0 * (nz(n, 9, 525, 3) - 0.25))
    msh = 0.25 + 0.5 * nz(n, 4, 526, 3) + 0.2 * (d > 4) * 0 - 0.1
    rgb = sel(moss, pq(msh, D_MOSS, 0.8), rgb)
    return put(rgb, moss & speck(n, n, 0.01, 527), "#a8f0b8")


@tex("deep_halls", "floor_lake")
def floor_lake(n):
    x, y = grid(n)
    base = 0.07 + 0.07 * nz(n, 16, 531, 3)
    w1 = nz(n, 20, 532, 2)
    a = np.sin(2 * np.pi * (2 * y / n + (w1 - 0.5) * 0.7))
    br = pnc(n, n, 10, 2, 533, 2)
    ln = np.clip(1 - np.abs(a) / 0.14, 0, 1) * (br > 0.44)
    sh = base + 0.30 * ln
    band = np.exp(-(((y - 30) / 8.0) ** 2))
    a2 = np.sin(2 * np.pi * (6 * y / n + (nz(n, 20, 534, 2) - 0.5) * 0.8))
    d2 = np.clip(1 - np.abs(a2) / 0.55, 0, 1) * (pnc(n, n, 6, 6, 535, 2) > 0.40) * band
    sh = sh + 0.80 * d2
    return pq(sh, D_WATER, 0.7)


@tex("deep_halls", "floor_wet_rock")
def floor_wet_rock(n):
    x, y = grid(n)
    f1, f2, ids = worley(n, n, jpts(n, n, 4, 4, 542, 0.9))
    plate = 0.10 + 0.18 * _rng(544).rand(16)[ids] + 0.14 * nz(n, 6, 543, 3)
    sh = np.where((f2 - f1) < 1.3, 0.0, plate + 0.10 * np.clip((f2 - f1) / 8.0, 0, 1))
    sh += 0.16 * ((f2 - f1 >= 1.3) & (f2 - f1 < 2.4)) * (nz(n, 5, 545, 2) > 0.45)
    rgb = pq(sh, D_STONE, 0.85)
    fld = nz(n, 26, 546, 3)
    pud = fld > 0.56
    streak = np.clip(1 - np.abs(((x * 0.5 + y * 2.0) % 24) - 8) / 1.6, 0, 1) * (nz(n, 8, 548, 2) > 0.45)
    psh = 0.30 + 0.14 * nz(n, 5, 547, 2) + 0.30 * streak + 0.2 * np.clip((fld - 0.56) * 8, 0, 1) * 0
    rgb = sel(pud, pq(psh, D_WATER, 0.6), rgb)
    rim = pud & (~shift(pud, 1, 0) | ~shift(pud, 0, 1))
    rgb = put(rgb, rim, "#8ad0e8")
    rgb = put(rgb, ~pud & shift(pud, -1, 0), "#000104")
    near = shift(pud, 2, 0) | shift(pud, -2, 0) | shift(pud, 0, 2) | shift(pud, 0, -2) | shift(pud, 3, 3) | shift(pud, -3, -3)
    sp = speck(n, n, 0.10, 549) & near & ~pud
    rgb = put(rgb, sp, "#e4f8ff")
    return rgb


@tex("deep_halls", "floor_boardwalk")
def floor_boardwalk(n):
    rng = _rng(561)
    x, y = grid(n)
    ph = 8
    row = (y // ph).astype(int)
    off = rng.randint(0, n, 8)
    jx = (x + off[row]) % n
    tone = rng.rand(8, 2)[row, (jx // 32).astype(int) % 2]
    grain = pnc(n, n, 40, 3, 562, 2)
    ly = y % ph
    sh = 0.36 + 0.24 * tone + (grain - 0.5) * 0.30 - 0.22 * (ly >= ph - 2) + 0.14 * (ly == 1)
    worn = np.exp(-(((x - 30) / 6.0) ** 2))
    sh = sh * (1 - 0.2 * worn) + 0.28 * worn * (0.4 + 0.6 * (grain)) * 0.5
    rgb = pq(sh, D_PLANK, 0.8)
    joint = (ly == 0) | ((jx % 32) < 1)
    rgb = put(rgb, joint, "#020104")
    rope = worn > 0.3
    fib = rope & ((x + y) % 4 == 0)
    rgb = sel(fib, pq(sh + 0.28, D_PLANK, 0.5), rgb)
    nails = ((jx % 32) == 3) | ((jx % 32) == 29)
    rgb = put(rgb, nails & ((ly == 3) | (ly == 4)) & (ly < ph), "#7e8c96")
    wet = (grain > 0.68) & (ly >= 2) & (ly < 4) & (nz(n, 10, 563, 2) > 0.5)
    rgb = tint(rgb, "#7ab8cc", wet * 0.45)
    sp = speck(n, n, 0.008, 564)
    rgb = put(rgb, sp, "#e8fcff")
    return rgb


@tex("deep_halls", "wall_deep")
def wall_deep(n):
    x, y = grid(n)
    sid, lx, ly, sw, sh_ = masonry(n, n, [40, 48, 40], 571, 52, 76)
    tone = tone_of(sid, 572)
    ph = 2 * np.pi * (lx + 1.0) / 8.0
    flute = np.cos(ph)  # ridge 1, groove -1 (period 8)
    inner = (lx >= 4) & (lx < sw - 4)
    fl = np.where(inner, flute, 0.0)
    sh = 0.34 + 0.22 * tone + 0.22 * fl + (nz(n, 6, 573, 3) - 0.5) * 0.14
    lit = inner & (((lx + 1) % 8) == 2)  # cold edge light on the left of each ridge
    sh = np.where(lit, sh + 0.30, sh)
    # damp: pale runs falling from the joints and some flutes
    wet = (pnc(n, n, 2, 44, 574, 3) > 0.72) & (ly < sh_ * 0.8)
    sh = np.where(wet, sh + 0.16, sh)
    rgb = pq(sh, D_STONE, 0.85)
    mort = (lx < 1.5) | (ly < 1.5)
    rgb = put(rgb, mort, "#010208")
    rgb = put(rgb, ((ly >= 1.5) & (ly < 2.5) & (lx >= 1.5)), "#385470")
    rgb = tint(rgb, "#000000", (ly > sh_ - 4) * np.clip((ly - (sh_ - 4)) / 4.0, 0, 1) * 0.35)
    drip = speck(n, n, 0.01, 575) & wet
    return put(rgb, drip, "#8ad8ec")


@tex("deep_halls", "wall_deep_arch")
def wall_deep_arch(n):
    x, y = grid(n)
    sid, lx, ly, sw, sh_ = masonry(n, n, [21, 21, 22, 21, 21, 22], 581, 22, 34)
    tone = tone_of(sid, 582)
    sh = 0.24 + 0.16 * tone + (nz(n, 6, 583, 3) - 0.5) * 0.18 + 0.22 * ((lx < 1.5) & (ly > 1.5)) + 0.20 * ((ly >= 1.5) & (ly < 2.5))
    rgb = pq(sh, D_STONE, 0.85)
    rgb = put(rgb, (lx < 1) | (ly < 1), "#010208")
    dx, dy = x - 64, y - 58
    upper = dy < 0
    r = np.where(upper, np.hypot(dx, dy), np.abs(dx))
    inside = r < 35
    ring = (r >= 35) & (r < 44)
    ang = np.arctan2(-dy, dx)  # 0..pi on the upper half
    seg = np.floor(ang / (np.pi / 9)).astype(int)
    rid = np.where(upper, seg, 100 + (y // 14).astype(int) * 2 + (dx > 0))
    rtone = _rng(584).rand(400)[rid % 400]
    rsh = 0.38 + 0.2 * rtone + 0.20 * ((r - 35) < 1.5) * 0 + (nz(n, 4, 585, 2) - 0.5) * 0.16
    rrgb = pq(rsh, D_STONE, 0.85)
    joint = np.where(upper, (np.abs(ang / (np.pi / 9) - np.round(ang / (np.pi / 9))) < 0.05), ((y % 14) == 0))
    rrgb = put(rrgb, joint & ring, "#010208")
    rrgb = put(rrgb, ring & (r < 36.5), "#4a6a88")
    rgb = sel(ring, rrgb, rgb)
    depth = 0.02 + 0.06 * (nz(n, 12, 586, 3)) + 0.05 * np.clip((y - 40) / 80.0, 0, 1)
    ish = np.where(inside, depth, 0)
    irgb = pq(ish, D_STONE, 0.5)
    edge_l = inside & (r > 31.5) & (dx < 0) & upper
    edge_l |= inside & (r > 32) & (dx < -26)
    irgb = tint(irgb, "#2a4a68", edge_l * 0.45)
    irgb = tint(irgb, "#000000", inside * (r > 32) * (dx > 0) * 0.3)
    return sel(inside, irgb, rgb)


@tex("deep_halls", "wall_rock_wet")
def wall_rock_wet(n):
    x, y = grid(n)
    base = nz(n, 22, 591, 4)
    sh = 0.05 + 0.20 * base + 0.06 * pnc(n, n, 8, 12, 592, 3)
    gx = np.roll(base, -1, 1) - np.roll(base, 1, 1)
    ridge = np.clip(1 - np.abs(base - 0.5) / 0.05, 0, 1)
    sh = sh + 0.30 * ridge * (gx < 0) + 0.08 * ridge
    gl = pnc(n, n, 3, 60, 593, 2)
    brk = pnc(n, n, 10, 3, 594, 2)
    glist = (gl > 0.66) & (brk > 0.42)
    rgb = pq(sh, D_STONE, 0.8)
    gsh = pq(0.45 + 0.5 * (gl - 0.66) * 3, D_WATER, 0.5)
    rgb = sel(glist, gsh, rgb)
    vein = (np.abs(nz(n, 30, 595, 3) - 0.5) < 0.010) & (pnc(n, n, 4, 4, 597, 2) > 0.52)
    rgb = put(rgb, vein, "#6a8498")
    rgb = put(rgb, vein & speck(n, n, 0.3, 596), "#c4dce8")
    return rgb


@tex("deep_halls", "wall_falls")
def wall_falls(n):
    x, y = grid(n)
    s = pnc(n, n, 4, 38, 601, 3)  # vertical streak field; periodic in y so a downward scroll loops
    s2 = pnc(n, n, 2, 70, 602, 2)
    water = np.clip((s - 0.34) * 3.4, 0, 1)
    rock = 0.06 + 0.16 * nz(n, 8, 603, 3) + 0.12 * (pnc(n, n, 3, 24, 604, 2) > 0.74)
    sh = np.where(water > 0.08, 0.34 + 0.50 * water + 0.14 * (s2 - 0.5), rock)
    foam = (s2 > 0.70) & (water > 0.5)
    sh = np.where(foam, 0.97, sh)
    mist = 0.10 * pnc(n, n, 3, 3, 605, 2)
    sh = sh + mist * (1 - water * 0.6)
    rgb = pq(sh, D_FALL, 0.8)
    rgb = put(rgb, speck(n, n, 0.012, 606) & (water < 0.6), "#e4f8ff")
    return rgb


@tex("deep_halls", "ceil_black")
def ceil_black(n):
    sh = 0.03 + 0.13 * nz(n, 14, 611, 4)
    rgb = pq(sh, D_STONE, 0.9)
    fl = speck(n, n, 0.012, 612)
    rgb = put(rgb, fl, "#1c2c44")
    return put(rgb, fl & speck(n, n, 0.15, 613), "#3a5472")


@tex("deep_halls", "ceil_stars")
def ceil_stars_deep(n):
    x, y = grid(n)
    rgb = pq(0.12 + 0.30 * nz(n, 20, 621, 3), D_NIGHT, 0.9)
    mist = wnoise(n, n, 2, 3, 622, 1.1, 3)
    m = np.clip((mist - 0.50) * 3.2, 0, 1)
    rgb = tint(rgb, "#b4d0e4", m * 0.34)
    wisp = np.zeros((n, n), np.float32)
    st = starfield(n, n, 624, 210)
    st[(m > 0.45) | (wisp > 0.4)] = 0
    return stamp_stars(rgb, st, ramp("#000000", "#4a6a8c", "#90b4d0", "#d4ecfa", "#ffffff"))


@tex("deep_halls", "sky_falls")
def sky_falls():
    h, w = 64, 256
    x, y = grid2(h, w)
    t = y / (h - 1)
    sh = 0.05 + 0.30 * t ** 1.6 + (pnc(h, w, 4, 6, 631, 3) - 0.5) * 0.06
    rgb = pq(sh, D_NIGHT, 0.9)
    rgb = tint(rgb, "#1c3050", np.clip((t - 0.45) * 0.9, 0, 1) * 0.55)
    up = pnc(h, w, 2, 14, 632, 3)  # mist rising: soft columns
    bank = pnc(h, w, 3, 5, 633, 3)
    m = np.clip((up * 0.8 + bank * 0.6 - 0.44) * 1.6, 0, 0.8) * np.clip((t - 0.40) * 2.0, 0, 1) ** 1.2
    st = starfield(h, w, 634, 330, fade=lambda yy: 0.95 - 0.55 * yy / 64.0)
    st[m > 0.18] = 0
    rgb = stamp_stars(rgb, st, ramp("#000000", "#4a6a8c", "#90b4d0", "#d4ecfa", "#ffffff"))
    rgb = tint(rgb, "#c8dcec", m * 0.85)
    return tint(rgb, "#eef8ff", np.clip((t - 0.9) * 6, 0, 1) * 0.45 * (0.6 + 0.4 * bank))


# =================================================================================================================================================
# ASH LAND: marsh teal and green on black; black stone and bronze; ash grey and dull red; red rock lit from within, black pool, white shaft
# =================================================================================================================================================
A_TEAL = ramp("#010605", "#04140f", "#082a24", "#0e463c", "#18685a", "#2a9078", "#5cc8a0", "#b8f8d8")
A_REEDK = ramp("#010403", "#03100c", "#061e18", "#0c342a", "#165040", "#24705a")
A_GREEN = ramp("#010a04", "#06200c", "#0e4016", "#1e7a24", "#44b83a", "#9cf070", "#e8ffc0")
A_MUD = ramp("#020403", "#080d0a", "#101812", "#1c261c", "#2c3626", "#424c36")
A_PLANK = ramp("#08060a", "#14100e", "#241c18", "#382c24", "#52443a", "#6e5e50")
A_BASALT = ramp("#030304", "#0a0a0e", "#14151b", "#222530", "#363b48", "#525a6c", "#7c8698")
A_ASH = ramp("#101012", "#222226", "#3a3a40", "#56565c", "#74747a", "#96969a", "#bcbcc0")
A_BRONZE = ramp("#0e0602", "#24100a", "#42240c", "#64400e", "#8a5c18", "#b08030", "#d8b060")
A_VERD = ramp("#04100c", "#0e2c22", "#1c5240", "#38806a", "#68b090", "#a4dcc0")
A_RED = ramp("#0c0302", "#2a0806", "#561006", "#8a2010", "#c0381a", "#ec6a28", "#ffa850")
A_GLOW = ramp("#0e0202", "#3a0804", "#7a1206", "#c02a0a", "#f26014", "#ffa830", "#ffe48a", "#fffbe0")
A_REDROCK = ramp("#0e0808", "#221414", "#3c2420", "#5a3a32", "#785244", "#96705c")
A_OBS = ramp("#000001", "#030308", "#08080e", "#10101a", "#1a1a28", "#2a2a3c", "#444458", "#7a7a94")
A_CANVAS = ramp("#18181a", "#32322f", "#504f48", "#706f64", "#908f82", "#b4b2a2")
A_CAV = ramp("#010102", "#06060a", "#0e0e14", "#1a1c26", "#2c3040", "#48546a", "#80929e", "#cfe0e8")
A_IRON = ramp("#050506", "#101014", "#1e1f26", "#30323c", "#484c5a", "#6e7488")
A_STAIR = ramp("#08090a", "#161719", "#26282c", "#3c3f44", "#575b62", "#787c84")
A_SMOKE = ramp("#080606", "#181414", "#2e2626", "#4c3a38", "#745654", "#9c7c78", "#c4a8a4")
A_POOL = ramp("#000001", "#010306", "#030a10", "#06141e", "#0e2a3a", "#1c4a62", "#8ab8cc", "#f4ffff")
A_PEBBLE = ramp("#1a1a1c", "#3a3a3e", "#6a6a70", "#9c9ca2", "#cacace", "#ececee")
A_CLINK = ramp("#0a0608", "#1c1214", "#322422", "#4c3a34", "#6a5248")
A_SKY = ramp("#050304", "#140a0a", "#2a1414", "#4a201a", "#74301e", "#a04424", "#cc6a34", "#f0a050")


def column(n: int, xc, half):
    """Per-row column shapes (a trunk or reed that wraps vertically): returns (mask, u in -1..1)."""
    x, y = grid(n)
    dx = x - np.asarray(xc, np.float32)[:, None]
    dx = (dx + n / 2) % n - n / 2
    hh = np.asarray(half, np.float32)[:, None]
    return np.abs(dx) < hh, dx / hh


@tex("ash_land", "floor_marsh")
def floor_marsh(n):
    rng = _rng(711)
    x, y = grid(n)
    wy = nz(n, 20, 712, 2)
    a = np.sin(2 * np.pi * (3 * y / n + (wy - 0.5) * 0.9))
    ln = np.clip(1 - np.abs(a) / 0.16, 0, 1) * (pnc(n, n, 12, 2, 713, 2) > 0.44)
    a2 = np.sin(2 * np.pi * (6 * y / n + (nz(n, 20, 714, 2) - 0.5) * 1.1 + 0.2))
    ln2 = np.clip(1 - np.abs(a2) / 0.10, 0, 1) * (pnc(n, n, 10, 3, 715, 2) > 0.58)
    sh = 0.08 + 0.18 * nz(n, 14, 716, 3) + 0.46 * ln + 0.28 * ln2
    rgb = pq(sh, A_TEAL, 0.7)
    R = Layer(n)
    S = Layer(n)
    for cx, cy in ((12, 24), (40, 14), (50, 52), (22, 56)):  # reed clumps
        S.ell(cx, cy + 1, 8, 2.0, 0.02)
        for k in range(8):
            dx = (k - 3.5) * 1.8
            R.seg(cx + dx * 0.4, cy, cx + dx * 1.5 + rng.uniform(-1, 1), cy - rng.uniform(8, 14), 1.6, 0.28 + 0.05 * (k % 3), 0.74)
    rgb = S.apply(rgb, A_TEAL)
    rgb = R.apply(rgb, A_TEAL, 0.5)
    g = Layer(n)
    h = Layer(n)
    for k, (px, py) in enumerate(rpts(n, n, 10, 717, 6)):  # bioluminescent specks
        g.rect(px, py, px + 1, py + 1, 0.95)
        if k % 2 == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                h.rect(px + dx, py + dy, px + dx + 1, py + dy + 1, 0.30)
    rgb = h.apply(rgb, A_GREEN, 0.0)
    return g.apply(rgb, A_GREEN, 0.0)


@tex("ash_land", "floor_mud")
def floor_mud(n):
    rng = _rng(721)
    x, y = grid(n)
    base = nz(n, 9, 722, 3)
    gx = np.roll(base, -1, 1) - np.roll(base, 1, 1)
    sh = 0.14 + 0.42 * base + 0.22 * np.clip(-gx * 9, 0, 1) - 0.16 * np.clip(gx * 9, 0, 1) + 0.2 * (nz(n, 14, 727, 2) > 0.66)
    rgb = pq(sh, A_MUD, 0.85)
    P = Layer(n)
    for (x0, y0, x1, y1) in ((4, 10, 44, 21), (22, 40, 62, 52)):  # sunken planks
        P.rect(x0, y0, x1, y1, 0.0)
    pl = P.m
    grain = pnc(n, n, 24, 3, 723, 2)
    psh = 0.40 + 0.34 * grain - 0.2 * (nz(n, 3, 724, 2) > 0.7)
    top = pl & ~shift(pl, 1, 0)
    psh = np.where(top, psh + 0.3, psh)
    cover = nz(n, 7, 725, 3) > 0.58  # mud lying over the planks
    wood = pl & ~cover
    rgb = sel(wood, pq(psh, A_PLANK, 0.8), rgb)
    gl = Layer(n)
    for px, py in rpts(n, n, 8, 726, 6):
        gl.rect(px, py, px + 1, py + 1, 0.9)
        gl.rect(px + 1, py, px + 2, py + 1, 0.4)
    return gl.apply(rgb, A_GREEN, 0.0)


@tex("ash_land", "wall_reed")
def wall_reed(n):
    rng = _rng(731)
    x, y = grid(n)
    rgb = pq(0.28 + 0.30 * pnc(n, n, 3, 2, 732, 3) + 0.10 * nz(n, 14, 733, 2), A_TEAL, 0.9)

    def reeds(rgb, count, wd, v0, v1, seed, amp=1.6):
        rr = _rng(seed)
        L = Layer(n)
        for i in range(count):
            x0 = (i + rr.rand() * 0.9) * n / count
            a, ph = rr.uniform(0.5, amp), rr.uniform(0, 6.28)
            v = rr.uniform(v0, v1)
            ys = np.arange(n)
            xs = x0 + a * np.sin(2 * np.pi * ys / n + ph)
            for yy in range(0, n, 2):
                L.seg(xs[yy], yy, xs[(yy + 2) % n] + (0 if yy + 2 < n else 0), yy + 2.0, wd, v, v - 0.04)
        return L.apply(rgb, A_REEDK, 0.6)

    rgb = reeds(rgb, 46, 1.6, 0.30, 0.46, 734)
    fog = np.clip((pnc(n, n, 6, 2, 735, 3) - 0.40) * 2.2, 0, 1)
    rgb = tint(rgb, "#4aa890", fog * 0.40)
    G = Layer(n)  # a few faint green lights deep inside
    H = Layer(n)
    for px, py in ((20, 30), (84, 64), (104, 112), (50, 96), (122, 20)):
        G.rect(px, py, px + 1, py + 1, 0.9)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            H.rect(px + dx, py + dy, px + dx + 1, py + dy + 1, 0.35)
        H.rect(px - 2, py, px - 1, py + 1, 0.15)
        H.rect(px + 2, py, px + 3, py + 1, 0.15)
    rgb = H.apply(rgb, A_GREEN, 0.0)
    rgb = G.apply(rgb, A_GREEN, 0.0)
    # dead trunks
    yy = np.arange(n)
    for (x0, wd, ph, seed) in ((34, 9.0, 0.7, 736), (92, 11.0, 2.2, 737)):
        xc = x0 + 1.8 * np.sin(2 * np.pi * yy / n + ph)
        half = wd / 2 + 1.0 * np.sin(2 * np.pi * 2 * yy / n + ph)
        m, u = column(n, xc, half)
        gr = pnc(n, n, 2, 40, seed, 3)
        sh = 0.20 + 0.62 * np.clip(0.55 - 0.5 * u * 1.0, 0, 1) ** 1.1 + (gr - 0.5) * 0.34
        sh = np.where(np.abs(u) > 0.82, sh * 0.5, sh)
        crack = (pnc(n, n, 14, 3, seed + 5, 2) > 0.72) & (np.abs(u) < 0.7)
        ring_ = (np.arange(n)[:, None] % 17) == 0
        tr = pq(sh - 0.22 * crack - 0.2 * ring_, A_BASALT * np.array([0.9, 1.0, 1.05], np.float32), 0.8)
        tr = tint(tr, "#5ad0b0", (np.abs(u + 0.78) < 0.12) * 0.55)
        rgb = sel(m, tr, rgb)
    rgb = reeds(rgb, 14, 3.4, 0.14, 0.30, 738, 2.2)
    return rgb


@tex("ash_land", "wall_obsidian")
def wall_obsidian(n):
    rng = _rng(741)
    x, y = grid(n)
    sid, lx, ly, sw, sh_ = masonry(n, n, [42, 44, 42], 742, 50, 78)
    tone = tone_of(sid, 743)
    cx, cy = lx / sw, ly / sh_
    diag = cx * 0.7 + cy * 0.7
    g1 = np.clip(1 - np.abs(diag - (0.50 + 0.2 * tone)) / 0.07, 0, 1)
    g2 = np.clip(1 - np.abs(diag - (0.80 - 0.2 * tone)) / 0.18, 0, 1)
    px, py = (rng.rand(40) * 0.8 + 0.1), (rng.rand(40) * 0.8 + 0.1)
    pi = (sid % 40)
    dd = np.hypot((cx - px[pi]) * sw, (cy - py[pi]) * sh_)
    conch = 0.5 + 0.5 * np.cos(dd * 0.55)
    sh = 0.34 + 0.18 * tone + 0.60 * g1 * (0.6 + 0.4 * tone) + 0.24 * g2 + 0.07 * conch + (nz(n, 8, 744, 2) - 0.5) * 0.07
    sh -= 0.10 * ((lx > sw - 4) | (ly > sh_ - 4))
    rgb = pq(sh, A_OBS, 0.7)
    seam = (lx < 1) | (ly < 1)
    rgb = put(rgb, seam, "#000001")
    rgb = put(rgb, ((lx >= 1) & (lx < 2) | (ly >= 1) & (ly < 2)) & ~seam & (tone > 0.2), "#3a3a52")
    reds = (np.abs(diag - (0.60 + 0.2 * tone)) < 0.014) & (tone > 0.5) & ~seam
    reds |= (np.abs(cx * 0.4 - cy * 0.9 - (0.1 * tone)) < 0.012) & (tone < 0.28) & ~seam
    reds &= pnc(n, n, 6, 6, 745, 2) > 0.34
    rgb = put(rgb, reds, "#a8261a")
    rgb = put(rgb, reds & (pnc(n, n, 8, 8, 746, 2) > 0.62), "#ff6a3a")
    return rgb


@tex("ash_land", "wall_gate")
def wall_gate(n):
    rng = _rng(751)
    x, y = grid(n)
    pw = 16
    pid = (x // pw).astype(int)
    tone = rng.rand(8)[pid]
    lx = x % pw
    grain = pnc(n, n, 3, 50, 752, 3)
    sh = 0.34 + 0.24 * tone + (grain - 0.5) * 0.34 + 0.14 * (lx < 1.5) - 0.2 * (lx >= pw - 1)
    rgb = pq(sh, A_BASALT, 0.8)
    rgb = put(rgb, lx == pw - 1, "#010102")
    for yb in (38, 102):  # two thin iron cross-bands
        S = (y >= yb) & (y < yb + 6)
        rgb = sel(S, pq(0.38 + 0.2 * pnc(n, n, 4, 20, 753 + yb, 2) + 0.4 * (y == yb) - 0.3 * (y == yb + 5), A_IRON, 0.7), rgb)
    for sx in (10, 42, 74, 106):  # vertical bronze straps, 12 wide, repeating every 32
        u = (x - sx) / 12.0
        m = (u >= 0) & (u < 1)
        ssh = 0.14 + 0.26 * (1 - np.clip(u * 1.1, 0, 1)) + 0.22 * pnc(n, n, 24, 3, 754 + sx, 2) - 0.14 * (u > 0.85)
        ssh = np.where((u >= 0) & (u < 0.09), ssh + 0.3, ssh)
        brz = pq(ssh, A_BRONZE, 0.7)
        brz = tint(brz, "#38806a", np.clip((pnc(n, n, 5, 3, 755 + sx, 2) - 0.56) * 4, 0, 1) * 0.6)
        rgb = sel(m, brz, rgb)
        rgb = tint(rgb, "#000000", ((u >= 1) & (u < 1.25)) * 0.5)
    L = Layer(n)
    V = Layer(n)
    for sx in (10, 42, 74, 106):
        for yy in range(8, n, 16):
            L.disc(sx + 6, yy, 2.7, 0.35, 1.0)
            if rng.rand() < 0.7:
                V.seg(sx + 6, yy + 3, sx + 6 + rng.uniform(-0.5, 0.5), yy + 3 + rng.uniform(5, 11), 1.6, 0.8, 0.25)
    rgb = V.apply(rgb, A_VERD, 0.5)
    return L.apply(rgb, A_BRONZE, 0.4)


@tex("ash_land", "floor_basalt")
def floor_basalt(n):
    f1, f2, ids = worley(n, n, jpts(n, n, 4, 4, 761, 0.28, stagger=True))
    edge = f2 - f1
    tone = _rng(762).rand(16)[ids]
    sh = 0.16 + 0.18 * tone + 0.14 * np.clip((edge - 2) / 5.0, 0, 1) + (nz(n, 5, 763, 3) - 0.5) * 0.14
    rgb = pq(sh, A_BASALT, 0.8)
    drift = np.clip((nz(n, 14, 764, 3) - 0.66) * 5, 0, 1)
    rgb = tint(rgb, "#8a8a90", drift * 0.30 * (edge > 2))
    jn = edge < 2.6
    jsh = 0.26 + 0.30 * nz(n, 4, 765, 3) + 0.14 * speck(n, n, 0.12, 766)
    rgb = sel(jn, pq(jsh, A_ASH, 0.8), rgb)
    return put(rgb, edge < 0.8, "#2e2e34")


@tex("ash_land", "floor_stair")
def floor_stair(n):
    rng = _rng(771)
    x, y = grid(n)
    ly = y % 16
    row = (y // 16).astype(int)
    jx = rng.randint(6, 58, 4)
    seg = (x >= jx[row]).astype(int)
    tone = rng.rand(4, 2)[row, seg]
    wear = np.exp(-(((x - 32 + 20 * (seg - 0.5) * 0) / 18.0) ** 2))
    sh = 0.42 + 0.16 * tone + (nz(n, 5, 772, 3) - 0.5) * 0.22 - 0.06 * wear
    sh = np.where(ly < 2, sh + 0.30, sh)
    sh = np.where((ly >= 12) & (ly < 16), sh - 0.10 - 0.07 * (ly - 12), sh)
    rgb = pq(sh, A_STAIR, 0.8)
    rgb = put(rgb, (ly == 15), "#030304")
    rgb = put(rgb, (x == jx[row]) & (ly > 1) & (ly < 12), "#050506")
    stain = np.clip((nz(n, 14, 773, 3) - 0.70) * 6, 0, 1) * (ly > 1)
    rgb = tint(rgb, "#38806a", stain * 0.32)
    rgb = tint(rgb, "#a0a0a4", speck(n, n, 0.10, 774) * (ly > 8) * 0.8)
    return rgb


@tex("ash_land", "wall_cliff")
def wall_cliff(n):
    rng = _rng(781)
    x, y = grid(n)
    base = pnc(n, n, 4, 20, 782, 4)
    sh = 0.14 + 0.34 * base + (pnc(n, n, 2, 40, 784, 3) - 0.5) * 0.2
    gy = np.roll(base, -1, 1) - np.roll(base, 1, 1)
    sh = sh + 0.12 * np.clip(-gy * 9, 0, 1)
    rgb = pq(sh, A_IRON * np.array([0.9, 0.95, 1.05], np.float32), 0.8)
    crack = np.abs(pnc(n, n, 3, 14, 785, 3) - 0.5) < 0.014
    rgb = put(rgb, crack, "#020203")
    V = Layer(n)
    for (sx, sy, ln, wd) in ((22, 6, 70, 5), (60, 30, 52, 4), (100, 0, 90, 6), (84, 78, 40, 3)):  # green stains below the bells' hanging points
        V.ell(sx, sy, wd * 0.9, 3.0, 0.82, 0.55)
        for yy in range(int(ln)):
            t = yy / ln
            ww = wd * (1 - 0.5 * t) * (0.7 + 0.5 * pn_at(np.array([yy / 4.0]), np.array([sx / 30.0]), 1, 26, 786)[0])
            V.rect(sx - ww / 2 + 1.0 * np.sin(yy / 9.0), sy + yy, sx + ww / 2 + 1.0 * np.sin(yy / 9.0), sy + yy + 1, 0.72 * (1 - 0.7 * t))
    vm = V.m
    rgb = np.where(vm[..., None], pq(V.v * (0.6 + 0.5 * pnc(n, n, 6, 6, 787, 2)), A_VERD, 0.7), rgb)
    for (bx, by) in ((36, 92), (96, 38)):  # iron ring bolts
        B = Layer(n)
        B.rect(bx - 6, by - 6, bx + 6, by + 6, 0.5, 0.25)
        rgb = B.apply(rgb, A_IRON, 0.5)
        R = Layer(n)
        R.disc(bx, by + 9, 7.2, 0.7, 0.95)
        R.disc(bx, by + 9, 4.8, 0.0)
        R.disc(bx, by - 3, 2.0, 0.9)
        rgb = R.apply(rgb, A_IRON, 0.4)
        rgb = put(rgb, (np.abs(x - bx) < 4.9) & (np.abs(y - (by + 9)) < 4.8) & (np.hypot(x - bx, y - by - 9) < 4.8), "#101014")
        rs = (x > bx - 3) & (x < bx + 2) & (y > by + 14) & (y < by + 30)
        rgb = tint(rgb, "#6a2a10", rs * np.clip(1 - (y - by - 14) / 16.0, 0, 1) * 0.8)
    return rgb


@tex("ash_land", "wall_ash_dune")
def wall_ash_dune(n):
    rng = _rng(791)
    x, y = grid(n)
    warp = (pnc(n, n, 3, 2, 792, 3) - 0.5) * 0.9
    ph = (y / n * 4 + warp) % 1.0
    sh = 0.80 - 0.62 * ph ** 0.65 + (pnc(n, n, 40, 3, 793, 2) - 0.5) * 0.18
    sh += 0.06 * np.where(ph < 0.06, 3.0, 0.0)
    rgb = pq(sh, A_ASH, 0.85)
    L = Layer(n)
    for _ in range(26):
        px, py = rng.uniform(0, n), rng.uniform(0, n)
        rx, ry = rng.uniform(2.5, 5.5), rng.uniform(1.6, 3.0)
        L.ell(px + 0.8, py + 1.2, rx + 0.5, ry + 0.4, 0.0)
    rgb = L.apply(rgb, A_CLINK * 0.5)
    C = Layer(n)
    for _ in range(26):
        px, py = rng.uniform(0, n), rng.uniform(0, n)
        rx, ry = rng.uniform(2.5, 5.5), rng.uniform(1.6, 3.0)
        C.ell(px, py, rx, ry, 0.10, 0.80, rng.uniform(0, 3.14))
    rgb = C.apply(rgb, A_CLINK, 0.6)
    g = np.clip(np.cos(2 * np.pi * (y - 106) / n), 0, 1) ** 1.6
    low = np.clip(1.0 - sh * 1.0, 0, 1)
    rgb = tint(rgb, "#c02a10", g * (0.10 + 0.6 * low) * 0.6)
    glow = speck(n, n, 0.10, 794) & (g > 0.4) & (sh < 0.45)
    rgb = put(rgb, glow, "#e0480c")
    return rgb


@tex("ash_land", "floor_ash")
def floor_ash(n):
    f1, f2, ids = worley(n, n, jpts(n, n, 3, 3, 801, 0.85))
    edge = f2 - f1
    tone = _rng(802).rand(9)[ids]
    sh = 0.36 + 0.16 * tone + (nz(n, 5, 803, 3) - 0.5) * 0.26 + 0.12 * np.clip((edge - 1.5) / 6.0, 0, 1)
    sh -= 0.12 * ((edge >= 1.3) & (edge < 2.5))
    sh += 0.10 * speck(n, n, 0.10, 804) - 0.10 * speck(n, n, 0.08, 805)
    rgb = pq(sh, A_ASH, 0.85)
    crack = edge < 1.3
    glow = np.clip(0.25 + 0.9 * (nz(n, 6, 806, 2) - 0.35), 0, 1)
    crgb = pq(0.12 + 0.62 * glow, A_RED, 0.7)
    rgb = sel(crack, crgb, rgb)
    return rgb


@tex("ash_land", "floor_red_rock")
def floor_red_rock(n):
    x, y = grid(n)
    base = nz(n, 7, 811, 4)
    gx = np.roll(base, -1, 1) - np.roll(base, 1, 1)
    sh = 0.20 + 0.52 * base + 0.14 * np.clip(-gx * 8, 0, 1) + (nz(n, 3, 812, 2) - 0.5) * 0.14
    rgb = pq(sh, A_REDROCK, 0.9)
    f1, f2, _ = worley(n, n, jpts(n, n, 3, 3, 813, 0.9))
    rgb = put(rgb, ((f2 - f1) < 0.8) & (nz(n, 8, 818, 2) > 0.45), "#0a0404")
    ash = np.clip((nz(n, 10, 814, 3) - 0.62) * 5, 0, 1)
    rgb = sel(ash > 0.35, pq(0.36 + 0.34 * nz(n, 3, 815, 2) + 0.1 * speck(n, n, 0.15, 816), A_ASH, 0.85), rgb)
    return put(rgb, speck(n, n, 0.01, 817), "#d6b6a0")


@tex("ash_land", "wall_vent")
def wall_vent(n):
    x, y = grid(n)
    f1, f2, ids = worley(n, n, jpts(n, n, 4, 4, 821, 0.9))
    edge = f2 - f1
    heat = np.clip(1 - edge / 7.0, 0, 1) ** 1.7
    mod = 0.55 + 0.45 * nz(n, 9, 822, 3)
    crust = 0.06 + 0.12 * nz(n, 4, 823, 3) + 0.04 * _rng(824).rand(16)[ids]
    sh = crust + 0.92 * heat * mod
    sh = np.where(edge < 1.6, np.maximum(sh, 0.70 + 0.28 * mod), sh)
    veins = np.clip(1 - np.abs(nz(n, 26, 825, 3) - 0.5) / 0.018, 0, 1)
    sh = np.maximum(sh, 0.60 * veins * (0.5 + 0.5 * nz(n, 6, 826, 2)))
    rgb = pq(sh, A_GLOW, 0.8)
    return put(rgb, speck(n, n, 0.004, 827) & (edge > 3), "#ff8a3a")


@tex("ash_land", "floor_vent")
def floor_vent(n):
    f1, f2, ids = worley(n, n, jpts(n, n, 4, 4, 831, 0.9))
    edge = f2 - f1
    heat = np.clip(1 - edge / 3.2, 0, 1) ** 2.0
    mod = 0.5 + 0.5 * nz(n, 8, 832, 3)
    crust = 0.04 + 0.14 * nz(n, 4, 833, 3) + 0.03 * _rng(834).rand(16)[ids]
    sh = crust + 0.70 * heat * mod
    sh = np.where(edge < 1.2, np.maximum(sh, 0.62 + 0.2 * mod), sh)
    rgb = pq(np.minimum(sh, 0.84), A_GLOW, 0.8)
    rim = (edge > 2.2) & (edge < 3.4)
    return put(rgb, speck(n, n, 0.006, 835) & rim, "#ff7a28")


@tex("ash_land", "ceil_hot")
def ceil_hot(n):
    f = nz(n, 11, 841, 4)
    crust = f > 0.41
    heat = np.clip((0.46 - f) * 6.0, 0, 1)
    sh = np.where(crust, 0.03 + 0.14 * nz(n, 4, 842, 2) + 0.14 * np.clip((f - 0.41) * -6 + 0.3, 0, 1), 0.26 + 0.50 * heat * (0.6 + 0.4 * nz(n, 5, 843, 2)))
    rim = crust & (shift(~crust, 1, 0) | shift(~crust, 0, 1) | shift(~crust, -1, 0) | shift(~crust, 0, -1))
    sh = np.where(rim, 0.30 + 0.16 * nz(n, 3, 844, 2), sh)
    rgb = pq(sh, A_GLOW, 0.8)
    return put(rgb, speck(n, n, 0.012, 845) & ~crust, "#ffe48a")


@tex("ash_land", "ceil_smoke")
def ceil_smoke(n):
    w = wnoise(n, n, 3, 3, 851, 1.0, 4)
    s = pnc(n, n, 12, 3, 852, 3)
    sh = 0.10 + 0.86 * np.clip((w - 0.28) * 1.9, 0, 1) - 0.32 * np.clip((s - 0.58) * 4, 0, 1)
    rgb = pq(sh, A_SMOKE, 0.9)
    dark = np.clip(1 - np.abs(wnoise(n, n, 5, 2, 853, 1.2, 2) - 0.5) / 0.05, 0, 1)
    return tint(rgb, "#0a0404", dark * 0.55)


@tex("ash_land", "ceil_mist_teal")
def ceil_mist_teal(n):
    w = wnoise(n, n, 3, 4, 861, 0.9, 4)
    s = pnc(n, n, 10, 2, 862, 3)
    sh = 0.20 + 0.60 * np.clip((w - 0.25) * 1.5, 0, 1) - 0.28 * np.clip((s - 0.56) * 4, 0, 1)
    rgb = pq(sh, A_TEAL, 0.9)
    G = Layer(n)
    H = Layer(n)
    for px, py in rpts(n, n, 9, 863, 14):
        G.rect(px, py, px + 1, py + 1, 0.95)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            H.rect(px + dx, py + dy, px + dx + 1, py + dy + 1, 0.32)
    rgb = H.apply(rgb, A_GREEN, 0.0)
    return G.apply(rgb, A_GREEN, 0.0)


@tex("ash_land", "wall_cavern")
def wall_cavern(n):
    x, y = grid(n)
    f1, f2, ids = worley(n, n, jpts(n, n, 4, 7, 871, 0.8), ay=0.55)
    edge = f2 - f1
    tone = _rng(872).rand(28)[ids]
    sh = 0.12 + 0.20 * tone + (nz(n, 6, 873, 3) - 0.5) * 0.16 + 0.10 * np.clip(edge / 6.0, 0, 1)
    sh = np.where(edge < 1.0, 0.0, sh)
    lit = (edge >= 1.0) & (edge < 2.0) & (tone > 0.70)
    sh = np.where(lit, sh + 0.30, sh)
    rgb = pq(sh, A_CAV, 0.8)
    gl = pnc(n, n, 2, 56, 874, 2)
    brk = pnc(n, n, 9, 3, 875, 2)
    streak = (gl > 0.62) & (brk > 0.36)
    rgb = sel(streak, pq(0.55 + 1.2 * (gl - 0.62) + 0.1 * brk, A_CAV, 0.5), rgb)
    return put(rgb, speck(n, n, 0.004, 876) & (edge > 2), "#cfe0e8")


@tex("ash_land", "floor_cavern")
def floor_cavern(n):
    rng = _rng(881)
    sh = 0.16 + 0.16 * nz(n, 16, 882, 3) + 0.05 * (nz(n, 3, 883, 2) - 0.5)
    rgb = pq(sh, A_CAV, 0.85)
    D = Layer(n)
    P = Layer(n)
    for px, py in rpts(n, n, 15, 884, 7):
        rx, ry = rng.uniform(1.6, 3.4), rng.uniform(1.2, 2.4)
        a = rng.uniform(0, 3.14)
        D.ell(px + 1.2, py + 1.5, rx + 0.5, ry + 0.4, 0.0, None, a)
        P.ell(px, py, rx, ry, 0.30 + 0.2 * rng.rand(), 0.95, a)
    rgb = D.apply(rgb, A_CAV * 0.4)
    return P.apply(rgb, A_PEBBLE, 0.6)


@tex("ash_land", "floor_pool")
def floor_pool(n):
    x, y = grid(n)
    dx = np.abs(x - 31.5)
    dx = np.minimum(dx, n - dx)
    dy = np.abs(y - 31.5)
    dy = np.minimum(dy, n - dy)
    d = np.hypot(dx, dy)
    env = np.clip(1 - d / 30.0, 0, 1)
    rr = (d % 8.0) / 8.0
    ring = np.clip(1 - np.abs(rr - 0.5) / 0.14, 0, 1)
    sh = 0.08 + 0.10 * nz(n, 14, 891, 3) + 0.62 * ring * env ** 0.6 + 0.07 * (nz(n, 6, 892, 2) > 0.62)
    rgb = pq(sh, A_POOL, 0.7)
    hl = pnc(n, n, 1, 16, 893, 2)[0] > 0.56
    hl2 = pnc(n, n, 1, 11, 894, 2)[0] > 0.60
    rgb = put(rgb, (y == 20) & hl[None, :], "#f4ffff")
    rgb = put(rgb, (y == 21) & hl2[None, :], "#8ab8cc")
    rgb = put(rgb, (y == 19) & (hl & hl2)[None, :], "#5a8aa0")
    return rgb


@tex("ash_land", "ceil_cavern")
def ceil_cavern(n):
    rng = _rng(901)
    sh = 0.10 + 0.20 * nz(n, 8, 902, 3)
    rgb = pq(sh, A_CAV, 0.85)
    for px, py in rpts(n, n, 6, 903, 16):
        L = Layer(n)
        L.disc(px, py, 8.2, 0.14, 0.26)
        L.disc(px - 0.4, py - 0.4, 5.6, 0.28, 0.46)
        L.disc(px - 0.7, py - 0.7, 3.4, 0.48, 0.68)
        L.disc(px - 1.0, py - 1.0, 1.6, 0.80, 0.95)
        rgb = L.apply(rgb, A_CAV, 0.4)
    return put(rgb, speck(n, n, 0.01, 904), "#2c3040")


@tex("ash_land", "floor_camp")
def floor_camp(n):
    rng = _rng(911)
    sh = 0.34 + 0.22 * nz(n, 5, 912, 3) + 0.10 * (nz(n, 14, 913, 2) - 0.5)
    sh += 0.14 * speck(n, n, 0.10, 914) - 0.10 * speck(n, n, 0.08, 915)
    rgb = pq(sh, A_ASH, 0.85)
    D = Layer(n)
    L = Layer(n)
    for (px, py, a) in ((14, 18, 0.3), (36, 40, -0.4), (52, 14, 2.9), (20, 50, 0.6), (50, 52, 3.5)):
        c, s_ = np.cos(a), np.sin(a)
        D.ell(px + 1, py + 1, 5.6, 3.2, 0.95, None, a)
        D.ell(px - 8.0 * c + 1, py - 8.0 * s_ + 1, 3.0, 2.4, 0.95, None, a)
        L.ell(px, py, 5.6, 3.2, 0.10, 0.28, a)
        L.ell(px - 8.0 * c, py - 8.0 * s_, 3.0, 2.4, 0.10, 0.28, a)
    rgb = D.apply(rgb, A_ASH, 0.3)
    rgb = L.apply(rgb, A_ASH, 0.5)
    E = Layer(n)
    H = Layer(n)
    for px, py in rpts(n, n, 7, 916, 6):
        E.rect(px, py, px + 1, py + 1, 0.80)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            H.rect(px + dx, py + dy, px + dx + 1, py + dy + 1, 0.30)
    rgb = H.apply(rgb, A_GLOW, 0.0)
    return E.apply(rgb, A_GLOW, 0.0)


@tex("ash_land", "wall_tent")
def wall_tent(n):
    x, y = grid(n)
    weave = 0.04 * (((x + y) % 2) == 0) + 0.03 * ((x % 3) == 0) - 0.03 * ((y % 3) == 0)
    fold = np.sin(2 * np.pi * (x / 64.0) + 1.4 * (pnc(n, n, 2, 2, 921, 2) - 0.5))
    sh = 0.48 + weave + 0.12 * fold + (nz(n, 12, 922, 3) - 0.5) * 0.12 - 0.12 * np.clip((nz(n, 22, 923, 3) - 0.62) * 4, 0, 1)
    rgb = pq(sh, A_CANVAS, 0.8)
    seam = (x % 32) < 2
    rgb = put(rgb, ((x % 32) == 0), "#18181a")
    rgb = sel((x % 32) == 1, pq(sh - 0.12, A_CANVAS, 0.5), rgb)
    rgb = put(rgb, ((x % 32) == 3) & ((y % 4) < 2), "#c8c6b2")
    dxy = np.minimum(np.abs(x - 96) , n - np.abs(x - 96))
    dyy = np.minimum(np.abs(y - 100), n - np.abs(y - 100))
    g = np.clip(1 - np.hypot(dxy, dyy) / 78.0, 0, 1) ** 1.5
    rgb = tint(rgb, "#d0381a", g * 0.22)
    # two diagonal ropes
    for (sgn, c0) in ((1, 20), (1, 84)):
        t = (x + sgn * y - c0) % n
        t = np.minimum(t, n - t)
        rope = t < 2.2
        tw = ((x - sgn * y) // 3) % 2  # twist
        rsh = 0.22 + 0.2 * tw - 0.14 * (t > 1.4)
        rgb = sel(rope, pq(rsh, A_CLINK, 0.6), rgb)
        shadow = (t >= 2.2) & (t < 3.6)
        rgb = tint(rgb, "#000000", shadow * 0.30)
    # stakes with rope loops
    S = Layer(n)
    K = Layer(n)
    for (sx, sy) in ((44, 96), (108, 22)):
        S.rect(sx - 3, sy, sx + 3, sy + 20, 0.55, 0.18)
        S.rect(sx - 3, sy, sx + 3, sy + 2, 0.95)
        K.rect(sx - 4, sy + 7, sx + 4, sy + 10, 0.4, 0.2)
    rgb = S.apply(rgb, A_PLANK, 0.5)
    rgb = K.apply(rgb, A_CLINK, 0.5)
    return rgb


@tex("ash_land", "sky_ash")
def sky_ash():
    h, w = 64, 256
    x, y = grid2(h, w)
    t = y / (h - 1)
    wn = wnoise(h, w, 3, 5, 931, 1.0, 4)
    s = np.clip((wn - 0.30) * 2.0, 0, 1)
    glow = t ** 1.15
    str_ = pnc(h, w, 8, 4, 932, 3)
    sh = 0.06 + 0.88 * glow * (1 - 0.82 * s) + 0.30 * (1 - glow) * s * (wn) + (str_ - 0.5) * 0.08
    sh += 0.14 * np.clip((str_ - 0.62) * 3, 0, 1) * glow
    rgb = pq(sh, A_SKY, 0.9)
    rgb = tint(rgb, "#8c7e78", s * (1 - glow) * 0.30 * (wn))
    dark = np.clip((wnoise(h, w, 4, 6, 933, 1.0, 3) - 0.56) * 4, 0, 1) * np.clip((t - 0.25) * 2.5, 0, 1)
    return tint(rgb, "#070304", dark * 0.72)


# @@NEXT@@


# =================================================================================================================================================
# build
# =================================================================================================================================================

def _render(art: str, tid: str):
    kind, px, metres, _brief = TILES[art][tid]
    fn = REG[art][tid]
    arr = fn() if kind == "sky" else fn(px)
    want = (64, 256) if kind == "sky" else (px, px)
    if arr.shape != (want[0], want[1], 3) or arr.dtype != np.uint8:
        raise ValueError(f"{art}/{tid}: drew {arr.shape} {arr.dtype}, wanted {want} RGB uint8")
    return arr, kind, metres


def build(art: str) -> dict:
    """Draw every surface (floor / wall / ceil / sky) of one art folder and return {id: {file, size, metres}}."""
    if art not in ARTS:
        raise KeyError(art)
    out_dir = os.path.join(ROOT, "assets", "story", art, "textures")
    os.makedirs(out_dir, exist_ok=True)
    section = {}
    for tid in sorted(TILES[art]):
        arr, _kind, metres = _render(art, tid)
        im = Image.fromarray(arr, "RGB")
        im.save(os.path.join(out_dir, tid + ".png"), optimize=False, compress_level=9)
        section[tid] = {"file": f"textures/{tid}.png", "size": [im.width, im.height], "metres": metres}
    return dict(sorted(section.items()))


def main() -> int:
    for art in ARTS:
        sec = build(art)
        print(f"{art}: {len(sec)} surface textures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
