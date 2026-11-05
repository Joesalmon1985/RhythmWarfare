"""The Mission Count's airfield art, first half (tools/paths/squadron_tex_owner.json "airfield_a"): the huts, tents, offices, hangar and bomber interior surfaces and the
props that stand in them. Bleached khaki, olive drab, orange dust, a white-blue sky; interiors under warm bulbs; the bomber green-black under instrument lamps.

`DRAW = {id: fn}`: every fn() takes no arguments and returns a uint8 array (see tex_squadron.py for the contract). Surfaces are drawn straight at 64 px, tileable;
billboards are 128 x 128 RGBA (the bomber 256 x 128) with a hard alpha, a darker one-pixel outline of the local colour, and their feet on the bottom edge. Deterministic: seeded generators only.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from .pixeltex import BAYER8, grid, hexc, noise, quantise, ramp, speckle

# ---- palettes (dark to light) --------------------------------------------------------------------------------------------------------------
KHAKI = ramp("#3e3626", "#5c5238", "#7e7048", "#a39463", "#c4b583", "#e0d5a6")
OLIVE = ramp("#181a14", "#2a2d20", "#403f2c", "#58573a", "#747250", "#908e64")
ORANGE = ramp("#4e2812", "#7a431c", "#a15e29", "#c27a3c", "#dc9c5a", "#efc486")
WOOD = ramp("#4a3a26", "#6a5638", "#8a7448", "#aa9262", "#c7b080", "#e0cea0")
DARKWOOD = ramp("#150e08", "#271a10", "#3c2a18", "#563c22", "#755531", "#947244")
STEEL = ramp("#101316", "#20252a", "#343b41", "#4d565c", "#6c7476", "#929794")
CONCRETE = ramp("#34342f", "#4a4a43", "#63625a", "#7f7e72", "#9d9b8b", "#bcb9a4")
GBLACK = ramp("#030705", "#08100c", "#0e1914", "#16251d", "#203629", "#2f4d38")
CANVAS = ramp("#5e5038", "#806f4e", "#a38f68", "#c4b48a", "#ddd0a6", "#efe6c4")
PLASTER = ramp("#5e5430", "#7e7040", "#9f8f55", "#bfae6c", "#d8c887", "#ece0a8")
DADO = ramp("#08120c", "#10200f", "#1a3118", "#274824", "#37602f")
SKY = ramp("#7a9fc0", "#98b9d4", "#b6d0e3", "#d3e3ee", "#eaf1f4", "#fbfcf6")
BRASS = ramp("#3a2a0c", "#6e5018", "#a8802a", "#d6ac44", "#f0d278")
RED = ramp("#2a0a08", "#561210", "#8a1c16", "#b8301f", "#d8553a")
GLASS = ramp("#26343a", "#42585e", "#6a8a90", "#9ab6b8", "#cfe0dc", "#f2f8f2")
PAPER = ramp("#6a604a", "#93896a", "#bdb391", "#dad1b0", "#eee7ca", "#fbf7e4")
RUST = ramp("#2a1208", "#4e2410", "#7a3a16", "#a45a24")
WARM = ramp("#6a3a10", "#a8641c", "#e0982c", "#f6c860", "#fff0b0")
OIL = ramp("#0e0c08", "#1c1710", "#2c2418", "#3e3422")
GRASS = ramp("#5e5a22", "#8c8736", "#b7ad56", "#dccf88")
PEBBLE = ramp("#6a5a46", "#8a7660", "#b09a7c", "#cdb898")
STRAW = ramp("#6a5418", "#9c8228", "#c8aa44", "#e6cf6e")
RAWWOOD = ramp("#3c3428", "#5a4e3c", "#7c6e56", "#a09274")
PINK = ramp("#5a3a2a", "#7e5640", "#a37860", "#c49a80")
LAMP = ramp("#16301f", "#344a26", "#5e6a30", "#8a8238")
EARTH = ramp("#6a4a2c", "#8a6a44", "#b99668", "#d9bb90")
CREAM = ramp("#5a5030", "#7e7244", "#a49866", "#c8bc8a", "#e2d8aa", "#f2ecc8")
LINOGREEN = ramp("#14281a", "#203a24", "#2e5034", "#406a44", "#58865a")


def _R(seed: int) -> np.random.RandomState:
    return np.random.RandomState(seed)


def _ov(rgb, mask, col):
    c = (hexc(col) * 255).astype(np.uint8) if isinstance(col, str) else np.asarray(col, np.uint8)
    out = rgb.copy()
    out[mask] = c
    return out


def _lay(rgb, mask, shade, pal):
    """Paint `shade` through `pal` onto rgb where mask."""
    out = rgb.copy()
    shade = np.asarray(shade, np.float32)
    if shade.ndim == 0:
        shade = np.full(mask.shape, float(shade), np.float32)
    col = quantise(np.clip(shade, 0, 1), pal)
    out[mask] = col[mask]
    return out


def _dith(n: int, level) -> np.ndarray:
    """A bool ordered-dither field: True with probability `level` (0..1 array or scalar)."""
    b = BAYER8[np.arange(n)[:, None] % 8, np.arange(n)[None, :] % 8] + 0.5
    return b < np.asarray(level)


class WM:
    """A tileable bool mask drawn with PIL on a 3 x 3 canvas and folded back, so shapes crossing the tile edge wrap."""

    def __init__(self, n: int):
        self.n = n
        self.im = Image.new("L", (3 * n, 3 * n), 0)
        self.d = ImageDraw.Draw(self.im)

    def _o(self, pts):
        return [(px + self.n, py + self.n) for px, py in pts]

    def line(self, pts, w=1):
        self.d.line(self._o(pts), fill=255, width=w)

    def poly(self, pts):
        self.d.polygon(self._o(pts), fill=255)

    def ellipse(self, cx, cy, rx, ry):
        self.d.ellipse([cx - rx + self.n, cy - ry + self.n, cx + rx + self.n, cy + ry + self.n], fill=255)

    def rect(self, x0, y0, x1, y1):
        self.d.rectangle([x0 + self.n, y0 + self.n, x1 + self.n - 1, y1 + self.n - 1], fill=255)

    def mask(self) -> np.ndarray:
        n = self.n
        a = np.asarray(self.im) > 0
        out = np.zeros((n, n), bool)
        for i in range(3):
            for j in range(3):
                out |= a[i * n:(i + 1) * n, j * n:(j + 1) * n]
        return out


def _wd(a, c, n):
    return (a - c + n / 2) % n - n / 2


def _rand(n, seed):
    return _R(seed).rand(n, n).astype(np.float32)


# ---- surfaces ----------------------------------------------------------------------------------------------------------------------------------

def ceil_beams():
    """A plank ceiling under one dark beam: staggered end joints, a cobweb in the beam's corner, a brown stovepipe stain."""
    n = 64
    x, y = grid(n)
    row = (y // 8).astype(int)
    ly = y % 8
    r = _R(11)
    tone = r.rand(8).astype(np.float32)[row]
    off = r.randint(0, 32, 8)[row]
    nz = noise(n, 8, 12)
    grain = np.sin(y * 1.3 + noise(n, 16, 13) * 10.0 + tone * 6) * 0.06
    jx = (x + off) % 32
    sh = 0.5 + 0.22 * (tone - 0.5) + grain + (nz - 0.5) * 0.2
    sh = sh - 0.34 * (ly == 0) - 0.34 * (jx < 1) - 0.06 * (ly == 7)
    d = np.sqrt((_wd(x, 52, n) / 9.0) ** 2 + (_wd(y, 40, n) / 12.0) ** 2)
    stain = np.clip(1.15 - d, 0, 1) * (0.7 + 0.3 * nz)
    sh = sh - 0.22 * stain - 0.16 * ((d > 0.85) & (d < 1.05))
    rgb = quantise(np.clip(sh, 0, 1), WOOD)
    rgb = _lay(rgb, stain > 0.3, 0.3 + 0.3 * stain + (nz - 0.5) * 0.3, ramp('#3a2a14', '#5c4220', '#7e5c30', '#9a7440'))
    rgb = _ov(rgb, (ly == 4) & ((jx == 3) | (jx == 28)), "#2a2018")
    bx0, bx1 = 22, 36
    bm = (x >= bx0) & (x < bx1)
    u = (x - bx0) / (bx1 - bx0)
    bs = 0.34 - 0.18 * u + 0.1 * (x < bx0 + 2) + (noise(n, 10, 14) - 0.5) * 0.14 + np.sin(x * 2.2 + y * 0.07) * 0.03
    rgb = _lay(rgb, bm, bs, DARKWOOD)
    shadow = (x >= bx1) & (x < bx1 + 5)
    rgb = _lay(rgb, shadow, sh - 0.22 - 0.05 * (x - bx1), WOOD)
    rgb = _ov(rgb, (y % 32 == 8) & ((x == 26) | (x == 31)), "#7a7a70")
    w = WM(n)
    cx, cy = bx1, 6
    for ang in (0.1, 0.6, 1.1, 1.5):
        w.line([(cx, cy), (cx + 16 * np.cos(ang), cy + 16 * np.sin(ang))])
    for rad in (5, 9, 13):
        w.line([(cx + rad * np.cos(a), cy + rad * np.sin(a) * 0.9) for a in np.linspace(0.05, 1.55, 6)])
    rgb = _ov(rgb, w.mask() & _dith(n, 0.7), "#c8c6b6")
    return rgb


def ceil_canvas():
    """A tent roof lit from above: bright cream canvas, a stitched panel seam, a twisted rope along the ridge, a rope loop, soft folds."""
    n = 64
    x, y = grid(n)
    nz = noise(n, 24, 21, 2)
    fold = np.sin((x / n) * 2 * np.pi * 2 + nz * 3.0) * 0.07
    weave = ((x + y) % 2) * 0.035 + ((x // 2 + y // 2) % 2) * 0.02
    sh = 0.7 + fold + weave + (noise(n, 6, 22) - 0.5) * 0.12
    sh = sh - 0.06 * (np.abs(_wd(x, 0, n)) < 3)
    dx32 = _wd(x, 32, n)
    seam = np.abs(dx32) < 1.0
    stitch = (np.abs(dx32) >= 1.0) & (np.abs(dx32) < 2.0) & (y % 3 == 0)
    sh = np.where(seam, sh - 0.3, sh)
    sh = np.where(stitch, sh - 0.2, sh)
    sh = sh + 0.1 * ((dx32 < -1) & (dx32 > -4)) - 0.1 * ((dx32 > 1) & (dx32 < 4))
    rgb = quantise(np.clip(sh, 0, 1), CANVAS)
    dx0 = _wd(x, 0, n)
    rope = np.abs(dx0) < 2.6
    tw = 0.5 + 0.35 * np.sin((y * 0.9) + dx0 * 1.6)
    rgb = _lay(rgb, rope, 0.18 + 0.4 * tw + 0.1 * (dx0 < 0), DARKWOOD)
    rgb = _lay(rgb, (dx0 >= 2.6) & (dx0 < 4.5), sh - 0.2, CANVAS)
    w = WM(n)
    w.ellipse(32, 46, 6, 4)
    w2 = WM(n)
    w2.ellipse(32, 46, 3, 2)
    ring = w.mask() & ~w2.mask()
    rgb = _lay(rgb, ring, 0.3 + 0.35 * tw, DARKWOOD)
    rgb = _ov(rgb, speckle(n, 0.01, 23) > 0.5, "#9d8c68")
    return rgb


def ceil_fuselage():
    """Curved aircraft ceiling: dark green-black ribs every 16 px, two stringers, a three-wire loom clipped along the crown."""
    n = 64
    x, y = grid(n)
    nz = noise(n, 12, 31)
    u = (x % 16) / 5.0
    rib = (x % 16) < 5
    cyl = 0.62 - 0.3 * u + 0.12 * np.sin(u * np.pi)
    sh = np.where(rib, cyl, 0.1 + (nz - 0.5) * 0.14)
    sh = sh + (nz - 0.5) * 0.1 - 0.05 * (((x % 16) >= 5) & ((x % 16) < 8))
    for yy in (12, 46):
        s = (y >= yy) & (y < yy + 3)
        sh = np.where(s, 0.34 + 0.12 * (y == yy) - 0.1 * (y == yy + 2) + (nz - 0.5) * 0.1, sh)
    rgb = quantise(np.clip(sh, 0, 1), GBLACK)
    rgb = _ov(rgb, (x % 16 == 2) & ((y % 8) == 4), "#4e6a58")
    for col, base in (("#3a2a24", 28), ("#363420", 30), ("#242c32", 32)):
        wy = base + 1.8 * np.sin((x % 32) / 32 * np.pi)
        rgb = _ov(rgb, np.abs(y - wy) < 0.8, col)
    clip_x = np.abs(_wd(x % 32, 0, 32)) < 1.5
    rgb = _ov(rgb, clip_x & (y >= 25) & (y <= 36), "#10161a")
    rgb = _ov(rgb, clip_x & (y == 26), "#5a6a62")
    rgb = _lay(rgb, (noise(n, 10, 32) > 0.72) & (sh < 0.2), 0.1, GBLACK)
    return rgb


def ceil_hangar():
    """A dim corrugated iron roof, a truss across it with a zigzag brace, rust blooming at the lap."""
    n = 64
    x, y = grid(n)
    nz = noise(n, 10, 41)
    prof = np.sin((x % 8) / 8 * 2 * np.pi)
    sh = 0.36 + 0.13 * prof + (nz - 0.5) * 0.2 + 0.04 * (_R(42).rand(n)[x.astype(int)] - 0.5)
    rgb = quantise(np.clip(sh, 0, 1), STEEL)
    rs = np.clip((noise(n, 12, 43, 3) - 0.58) * 3.0, 0, 1) * (0.5 + 0.5 * (prof > 0))
    rgb = _lay(rgb, rs > 0.5, 0.1 + 0.4 * rs + (nz - 0.5) * 0.3, RUST)
    rgb = _lay(rgb, np.abs(_wd(y, 6, n)) < 1, 0.18 + 0.2 * (y == 5), STEEL)
    w = WM(n)
    w.rect(0, 28, 64, 31)
    w.rect(0, 44, 64, 47)
    for k in range(4):
        w.line([(k * 16, 31), (k * 16 + 8, 44), (k * 16 + 16, 31)], 2)
    tm = w.mask()
    ts = 0.42 + 0.14 * (np.abs(_wd(y, 28, n)) < 1) - 0.1 * ((y % 16) > 12) + (nz - 0.5) * 0.12
    rgb = _lay(rgb, tm, ts, STEEL)
    rgb = _lay(rgb, (~tm) & np.roll(tm, 3, 0) & (y > 31), sh - 0.2, STEEL)
    rgb = _ov(rgb, tm & ((x % 16) == 8) & ((y == 29) | (y == 45)), "#8e8e86")
    rgb = _lay(rgb, tm & (noise(n, 6, 45) > 0.72), 0.2, RUST)
    return rgb


def ceil_plaster():
    """Yellowed plaster: a ringed water stain, a plaster rose round a bare bulb socket, a hairline crack."""
    n = 64
    x, y = grid(n)
    nz = noise(n, 18, 51, 3)
    sh = 0.64 + (nz - 0.5) * 0.28 + (noise(n, 4, 52) - 0.5) * 0.06
    d = np.sqrt((_wd(x, 12, n) / 13.0) ** 2 + (_wd(y, 14, n) / 9.0) ** 2)
    stain = np.clip(1.2 - d, 0, 1)
    ring = (d > 0.85) & (d < 1.0)
    sh = sh - 0.2 * stain - 0.2 * ring
    rgb = quantise(np.clip(sh, 0, 1), PLASTER)
    wm = ramp('#6a5224', '#8a6c30', '#aa8a44', '#c4a25a')
    rgb = _lay(rgb, (stain > 0.25) & ~ring, 0.35 + 0.4 * stain + (nz - 0.5) * 0.2, wm)
    rgb = _lay(rgb, ring, 0.25, wm)
    dx, dy = _wd(x, 40, n), _wd(y, 40, n)
    r = np.sqrt(dx ** 2 + dy ** 2)
    rs = 0.62 + 0.22 * np.cos(r * 1.35) - 0.3 * (r > 9.5) + 0.1 * ((dx + dy) < 0)
    rgb = _lay(rgb, r < 11, rs, PLASTER)
    rgb = _lay(rgb, (r < 11) & (r >= 10), 0.18, PLASTER)
    rgb = _lay(rgb, r < 4.5, 0.4 + 0.1 * (dx < 0), STEEL)
    rgb = _ov(rgb, r < 3.2, "#fff0b8")
    rgb = _ov(rgb, r < 1.8, "#ffffe8")
    w = WM(n)
    w.line([(2, 56), (9, 52), (14, 53), (22, 47), (26, 49), (33, 43)])
    rgb = _ov(rgb, w.mask(), "#5a4a2a")
    return rgb


def floor_boards():
    """Worn pale boards laid along x: dark gaps, staggered joints, nails, boot scuffs, dust in the cracks."""
    n = 64
    x, y = grid(n)
    row = (y // 8).astype(int)
    ly = y % 8
    r = _R(61)
    tone = r.rand(8).astype(np.float32)[row]
    off = r.randint(0, 64, 8)[row]
    jx = (x + off) % 64
    nz = noise(n, 10, 62)
    grain = np.sin(y * 1.9 + noise(n, 20, 63) * 12.0 + tone * 8.0) * 0.05
    wear = noise(n, 14, 64, 3)
    sh = 0.58 + 0.2 * (tone - 0.5) + grain + (nz - 0.5) * 0.14 + (wear - 0.5) * 0.12
    sh = sh + 0.07 * (ly == 1) - 0.07 * (ly == 7)
    gap = (ly == 0) | (jx < 1)
    sh = np.where(gap, 0.0, sh)
    rgb = quantise(np.clip(sh, 0, 1), WOOD)
    rgb = _ov(rgb, (ly == 0) & _dith(n, 0.35), "#9a8a6a")
    nail = (jx == 3) | (jx == 60)
    rgb = _ov(rgb, (ly == 4) & nail, "#3a2c1c")
    rgb = _ov(rgb, (ly == 3) & nail, "#bba684")
    w = WM(n)
    q = _R(65)
    for _ in range(9):
        px, py = q.randint(0, n), q.randint(0, n)
        w.line([(px, py), (px + q.randint(4, 11), py + q.randint(-2, 3))])
    rgb = _lay(rgb, w.mask() & (ly > 1), 0.55 + (nz - 0.5) * 0.3, DARKWOOD)
    rgb = _lay(rgb, (noise(n, 6, 66) > 0.7) & ~gap, sh + 0.18, WOOD)
    return rgb


def floor_concrete():
    """Stained hangar concrete: expansion joints along the tile edges, an oil stain, a crack, scattered straw, dust."""
    n = 64
    x, y = grid(n)
    nz = noise(n, 14, 71, 3)
    sh = 0.5 + (nz - 0.5) * 0.4 + (noise(n, 4, 72) - 0.5) * 0.14 + (_rand(n, 73) - 0.5) * 0.08
    oil = np.clip((noise(n, 20, 74, 3) - 0.56) * 5.0, 0, 1)
    sh = sh - 0.2 * oil
    rgb = quantise(np.clip(sh, 0, 1), CONCRETE)
    rgb = _lay(rgb, oil > 0.35, 0.3 + 0.5 * (1 - oil) + (nz - 0.5) * 0.3, ramp('#1a1812', '#2c2a22', '#403d32', '#575446'))
    jx = (np.abs(_wd(x, 0, n)) < 1.0) | (np.abs(_wd(y, 0, n)) < 1.0)
    jl = ((_wd(x, 0, n) == -1) | (_wd(y, 0, n) == -1)) & ~jx
    rgb = _ov(rgb, jx, "#1c1b18")
    rgb = _ov(rgb, jl & _dith(n, 0.7), "#b6b3a0")
    w = WM(n)
    w.line([(8, 20), (13, 24), (12, 30), (20, 34), (24, 42), (32, 45), (37, 53)])
    rgb = _ov(rgb, w.mask(), "#25241f")
    q = _R(75)
    w = WM(n)
    for _ in range(16):
        px, py, a, L = q.randint(0, n), q.randint(0, n), q.rand() * 6.28, q.randint(4, 9)
        w.line([(px, py), (px + L * np.cos(a), py + L * np.sin(a))])
    rgb = _lay(rgb, w.mask() & ~jx, 0.45 + 0.5 * _rand(n, 76), STRAW)
    rgb = _ov(rgb, speckle(n, 0.02, 77) > 0.5, "#c9c5ae")
    return rgb


def floor_dust():
    """Packed orange dust and gravel with two tyre tracks (chevron tread) and two tufts of dry grass."""
    n = 64
    x, y = grid(n)
    nz = noise(n, 16, 81, 4)
    sh = 0.55 + (nz - 0.5) * 0.4 + (_rand(n, 82) - 0.5) * 0.1
    for cx in (15, 43):
        dx = _wd(x, cx, n)
        chev = ((y + np.abs(dx)) % 5) < 2
        sh = np.where(np.abs(dx) < 6, sh - 0.14 - 0.1 * chev, sh)
        edge = (np.abs(dx) >= 6) & (np.abs(dx) < 8)
        sh = np.where(edge, sh + 0.12 * (dx < 0) - 0.04, sh)
    rgb = quantise(np.clip(sh, 0, 1), ORANGE)
    q = _R(83)
    w = WM(n)
    for _ in range(34):
        w.ellipse(q.randint(0, n), q.randint(0, n), q.choice([0.6, 1.0, 1.4]), q.choice([0.6, 0.9]))
    pebble = w.mask()
    rgb = _lay(rgb, np.roll(np.roll(pebble, 1, 0), 1, 1) & ~pebble, sh * 0.5, ORANGE)
    rgb = _lay(rgb, pebble, 0.2 + 0.6 * _rand(n, 84), PEBBLE)
    w = WM(n)
    for (tx, ty) in ((57, 22), (6, 51)):
        for k, a in enumerate(np.linspace(-0.9, 0.9, 7)):
            L = 7 + (k % 3) * 2
            w.line([(tx, ty), (tx + L * np.sin(a), ty - L * np.cos(a))])
    rgb = _lay(rgb, w.mask(), 0.3 + 0.6 * _rand(n, 85), GRASS)
    return rgb


def floor_lino():
    """Cracked cream-and-green linoleum in 16 px squares, scuffed, with worn patches and grime."""
    n = 64
    x, y = grid(n)
    cx, cy = (x // 16).astype(int), (y // 16).astype(int)
    green = ((cx + cy) % 2) == 1
    t = _R(91).rand(4, 4).astype(np.float32)[cy, cx]
    nz = noise(n, 12, 92, 3)
    lx, ly = x % 16, y % 16
    sh = 0.58 + 0.16 * (t - 0.5) + (nz - 0.5) * 0.22 + (_rand(n, 93) - 0.5) * 0.07
    sh = sh + 0.08 * ((lx == 1) | (ly == 1)) - 0.08 * ((lx == 15) | (ly == 15))
    grout = (lx == 0) | (ly == 0)
    rgb = quantise(np.clip(sh, 0, 1), CREAM)
    rgb = np.where(green[..., None], quantise(np.clip(sh - 0.02, 0, 1), LINOGREEN), rgb)
    rgb = _ov(rgb, grout, "#2a2418")
    wear = (noise(n, 12, 94, 3) > 0.7) & ~grout & _dith(n, 0.5)
    rgb = _lay(rgb, wear, 0.3 + 0.4 * _rand(n, 95), ramp("#5a4a2e", "#7e6a40", "#a48c58"))
    q = _R(96)
    w = WM(n)
    for (x0, y0) in ((6, 10), (40, 38)):
        pts = [(x0, y0)]
        for _ in range(5):
            pts.append((pts[-1][0] + q.randint(3, 8), pts[-1][1] + q.randint(-3, 6)))
        w.line(pts)
    rgb = _ov(rgb, w.mask(), "#1c1810")
    w2 = WM(n)
    for _ in range(10):
        px, py = q.randint(0, n), q.randint(0, n)
        w2.line([(px, py), (px + q.randint(3, 8), py + q.randint(-1, 2))])
    rgb = _lay(rgb, w2.mask() & ~grout, 0.25 + 0.2 * _rand(n, 97), ramp("#2a2012", "#4a3a20", "#6a5630"))
    return rgb


def floor_metal():
    """Dark aircraft floor: bar grating, one strip of diamond tread plate between two angle rails, oil stains."""
    n = 64
    x, y = grid(n)
    nz = noise(n, 12, 101, 3)
    bar = (y % 4) < 2
    grat = bar | ((x % 8) < 2)
    gsh = np.where(grat, 0.5 + 0.2 * (((y % 4) == 0) & bar) - 0.15 * (((y % 4) == 1) & bar), 0.04) + (nz - 0.5) * 0.12
    strip = (y >= 22) & (y < 46)
    lx, ly = (x % 8) - 3.5, (y % 8) - 3.5
    a = (np.abs(lx) + np.abs(ly * 2.2)) < 3.7
    lx2, ly2 = ((x + 4) % 8) - 3.5, ((y + 4) % 8) - 3.5
    b = (np.abs(lx2) + np.abs(ly2 * 2.2)) < 3.7
    loz = a | b
    ssh = 0.28 + 0.34 * loz + 0.2 * (loz & (lx < 0) & (ly < 0.5)) + (nz - 0.5) * 0.14
    sh = np.where(strip, ssh, gsh)
    rgb = quantise(np.clip(sh, 0, 1), STEEL)
    rail = ((y >= 20) & (y < 22)) | ((y >= 46) & (y < 48))
    rgb = _lay(rgb, rail, 0.7 - 0.45 * (y >= 46), STEEL)
    rgb = _ov(rgb, rail & (x % 16 == 4) & (y == 21), "#a7aaa2")
    oil = np.clip((noise(n, 14, 102, 3) - 0.58) * 5.0, 0, 1)
    rgb = _lay(rgb, (oil > 0.4) & _dith(n, 0.1 + 0.6 * oil), 0.4 + 0.3 * (1 - oil), ramp("#0a0a08", "#16130d", "#26200f"))
    return rgb


def wall_berm():
    """Stacked sandbags (16 x 8 pillows, staggered) in two stacks with a band of packed orange earth between, dry grass on the earth."""
    n = 64
    x, y = grid(n)
    nz = noise(n, 10, 111, 3)
    row = (y // 8).astype(int)
    off = (row % 2) * 8
    bx = (x + off) % 16
    ly = y % 8
    u = (bx - 7.5) / 8.0
    v = (ly - 3.5) / 4.0
    inside = (np.abs(u) ** 3.2 + np.abs(v) ** 2.4) < 1.0
    bag_t = _R(112).rand(8, 5).astype(np.float32)[row, (((x + off) // 16).astype(int)) % 5]
    sh = 0.62 + 0.16 * (bag_t - 0.5) - 0.25 * v - 0.14 * u + (nz - 0.5) * 0.2 + ((x + y) % 2) * 0.03
    bags = quantise(np.clip(sh, 0, 1), KHAKI)
    gap = quantise(np.clip(0.04 + (nz - 0.5) * 0.1, 0, 1), KHAKI)
    rgb = np.where(inside[..., None], bags, gap)
    rgb = _ov(rgb, inside & (ly == 3) & (np.abs(u) < 0.5) & (bx % 2 == 0) & (bag_t > 0.5), "#5c5238")
    band = (y >= 32) & (y < 48)
    es = 0.5 + (nz - 0.5) * 0.5 + (_rand(n, 113) - 0.5) * 0.14 - 0.2 * ((y >= 32) & (y < 34)) + 0.12 * ((y >= 34) & (y < 36))
    rgb = _lay(rgb, band, es, ORANGE)
    q = _R(114)
    w = WM(n)
    for _ in range(26):
        w.ellipse(q.randint(0, n), q.randint(33, 47), 0.8, 0.6)
    rgb = _lay(rgb, w.mask() & band, 0.3 + 0.6 * _rand(n, 115), EARTH)
    w = WM(n)
    for (tx, ty) in ((12, 36), (41, 36), (55, 36)):
        for a in np.linspace(-0.8, 0.8, 5):
            L = 6 + int(abs(a) < 0.5) * 3
            w.line([(tx, ty), (tx + L * np.sin(a), ty - L * np.cos(a))])
    rgb = _lay(rgb, w.mask(), 0.35 + 0.55 * _rand(n, 116), GRASS)
    rgb = _lay(rgb, (noise(n, 6, 117) > 0.62) & ~band & inside, sh + 0.2, KHAKI)
    return rgb


def wall_bomber():
    """Riveted aircraft interior panels, green-black, a lighter ribbed strip across the middle, warm lamp scuffs."""
    n = 64
    x, y = grid(n)
    nz = noise(n, 12, 121, 3)
    px, py = x % 32, y % 32
    sh = 0.3 + (nz - 0.5) * 0.18 + 0.14 * (px < 2) + 0.1 * (py < 2) - 0.12 * (px > 29) - 0.1 * (py > 29)
    seam = (px == 0) | (py == 0)
    sh = np.where(seam, 0.0, sh)
    strip = (y >= 26) & (y < 38)
    rib = y % 3
    ssh = 0.5 + 0.2 * (rib == 0) - 0.18 * (rib == 2) + (nz - 0.5) * 0.12
    sh = np.where(strip, ssh, sh)
    rgb = quantise(np.clip(sh, 0, 1), GBLACK)
    rgb = _ov(rgb, (y == 25) | (y == 38), "#05090a")
    riv = ((px % 4 == 2) & ((py == 3) | (py == 29))) | ((py % 4 == 2) & ((px == 3) | (px == 29)))
    riv &= ~strip
    rgb = _ov(rgb, np.roll(riv, 1, 0) & ~riv & ~seam & ~strip, "#050a08")
    rgb = _ov(rgb, riv, "#5a7360")
    sc = np.clip(1.0 - np.sqrt((_wd(x, 14, n) / 12.0) ** 2 + (_wd(y, 12, n) / 8.0) ** 2), 0, 1) + \
        np.clip(1.0 - np.sqrt((_wd(x, 48, n) / 9.0) ** 2 + (_wd(y, 52, n) / 7.0) ** 2), 0, 1)
    sc = sc * (0.55 + 0.7 * noise(n, 5, 122))
    rgb = _lay(rgb, _dith(n, sc * 0.9) & ~seam & ~strip, 0.5 + 0.3 * sc, LAMP)
    rgb = _ov(rgb, (_rand(n, 123) < 0.012) & ~seam, "#6a8a70")
    return rgb


def wall_hangar():
    """Corrugated iron, olive-drab paint worn through to orange metal on the ridges, rust streaks from the bolts at the sheet lap."""
    n = 64
    x, y = grid(n)
    nz = noise(n, 10, 131, 3)
    prof = np.cos((x % 8) / 8.0 * 2 * np.pi + 0.6)
    sh = 0.5 + 0.36 * prof + (nz - 0.5) * 0.18 + (_R(132).rand(n)[x.astype(int)] - 0.5) * 0.06
    sh = sh + 0.2 * (np.abs(_wd(y, 32, n)) < 1.0) - 0.4 * ((y >= 33) & (y < 37))
    rgb = quantise(np.clip(sh, 0, 1), OLIVE)
    colk = _R(139).rand(n).astype(np.float32)[x.astype(int)]
    cph = _R(140).rand(n).astype(np.float32)[x.astype(int)]
    vert = 0.5 + 0.5 * np.sin(2 * np.pi * (y / n * 2 + cph))
    wear = np.clip((colk - 0.7) * 5.0, 0, 1) * np.clip((vert - 0.55) * 3.0, 0, 1) * np.clip(prof * 1.4 + 0.6, 0, 1)
    rgb = _lay(rgb, wear > 0.3, 0.3 + 0.3 * prof + 0.2 * wear + (nz - 0.5) * 0.3, ORANGE)
    streak = np.zeros((n, n), bool)
    for bxp in range(3, n, 8):
        L = _R(134 + bxp).randint(6, 24)
        streak |= ((x == bxp) & (y >= 31) & (y < 31 + L)) | ((x == bxp + 1) & (y >= 31) & (y < 31 + L // 2))
    streak |= (x % 8 == 3) & (y > 36) & (noise(n, 6, 135) > 0.55) & (_rand(n, 136) < 0.8)
    rgb = _lay(rgb, streak, 0.3 + 0.5 * _rand(n, 137), RUST)
    bolts = (y == 30) & (x % 8 == 3)
    rgb = _ov(rgb, np.roll(bolts, 1, 1) | np.roll(bolts, 1, 0), "#2a2a22")
    rgb = _ov(rgb, bolts, "#b8b2a0")
    return rgb


def wall_hut():
    """Bleached khaki vertical planks: gaps, nails, flaking paint showing grey wood, dust streaks."""
    n = 64
    x, y = grid(n)
    col = (x // 8).astype(int)
    lx = x % 8
    tone = _R(141).rand(8).astype(np.float32)[col]
    nz = noise(n, 12, 142, 3)
    grain = np.sin(x * 1.3 + noise(n, 16, 143) * 9.0 + tone * 5.0) * 0.05
    sh = 0.68 + 0.18 * (tone - 0.5) + grain + (nz - 0.5) * 0.18 + 0.08 * (lx == 1) - 0.08 * (lx == 7)
    gap = lx == 0
    sh = np.where(gap, 0.0, sh)
    rgb = quantise(np.clip(sh, 0, 1), KHAKI)
    peel = (noise(n, 9, 144, 3) > 0.7) & ~gap & (_dith(n, 0.85) | (noise(n, 4, 148) > 0.5))
    rgb = _lay(rgb, peel, 0.3 + 0.35 * noise(n, 3, 145) + grain * 2, RAWWOOD)
    stk = (_R(146).rand(8)[col] < 0.5) & (noise(n, 8, 147) > 0.45) & ~gap
    rgb = _lay(rgb, stk & ~peel & _dith(n, 0.4), sh - 0.25, KHAKI)
    nail = ((y == 4) | (y == 33)) & (lx == 4)
    rgb = _ov(rgb, np.roll(nail, 1, 1) | np.roll(nail, 1, 0), "#c8bc92")
    rgb = _ov(rgb, nail, "#40362a")
    return rgb


def wall_office():
    """Yellowed plaster over a dark-green painted dado with a thin dark rail between; the plaster has peeled in patches."""
    n = 64
    x, y = grid(n)
    nz = noise(n, 14, 151, 3)
    sh = 0.62 + (nz - 0.5) * 0.3 + (noise(n, 3, 152) - 0.5) * 0.08
    top = y < 34
    rgb = quantise(np.clip(sh, 0, 1), PLASTER)
    peel = (noise(n, 12, 153, 3) > 0.7) & top
    rgb = _lay(rgb, peel, 0.3 + 0.5 * noise(n, 4, 154), PINK)
    rgb = _lay(rgb, np.roll(peel, 1, 0) & ~peel & top, sh + 0.25, PLASTER)
    st = (np.abs(_wd(x, 44, n)) < 1.0) & (y < 30) & (noise(n, 7, 155) > 0.35)
    rgb = _lay(rgb, st, 0.35, PLASTER)
    rgb = _ov(rgb, y == 34, "#a8a060")
    rgb = _ov(rgb, (y == 35) | (y == 36), "#0e1a10")
    rgb = _ov(rgb, y == 37, "#050a06")
    dm = y >= 38
    ds = 0.42 + (nz - 0.5) * 0.2 + 0.18 * np.sin(x * 0.4 + nz * 3) * (y > 40) + 0.08 * ((y >= 38) & (y < 40))
    rgb = _lay(rgb, dm, ds, DADO)
    rgb = _lay(rgb, (noise(n, 5, 156) > 0.8) & dm, 0.5 + 0.3 * _rand(n, 157), ramp("#4a3a24", "#7a6a46", "#a89a6a"))
    rgb = _ov(rgb, y == 63, "#050a06")
    return rgb


def wall_tent():
    """Dirty cream canvas: a stitched seam down each panel join, soft vertical folds, a rope loop with a hanging cord, a faint red-brown stain."""
    n = 64
    x, y = grid(n)
    nz = noise(n, 20, 161, 3)
    dx0 = _wd(x, 0, n)
    fold = np.sin(dx0 / n * 2 * np.pi * 4 + nz * 2.5) * 0.09
    weave = ((x + y) % 2) * 0.03 + ((x // 2 + (y // 2)) % 2) * 0.025
    sh = 0.66 + fold + weave + (nz - 0.5) * 0.18 + (noise(n, 5, 162) - 0.5) * 0.06
    d = np.sqrt((_wd(x, 46, n) / 10.0) ** 2 + (_wd(y, 44, n) / 7.0) ** 2)
    stain = np.clip(1.1 - d, 0, 1)
    sh = sh - 0.2 * stain * (0.6 + 0.4 * noise(n, 4, 163)) - 0.1 * ((d > 0.8) & (d < 0.95))
    seam = np.abs(dx0) < 1.0
    stitch = (np.abs(dx0) > 1.0) & (np.abs(dx0) < 2.0) & (y % 4 < 2)
    sh = np.where(seam, sh - 0.22, sh)
    sh = np.where(stitch, sh - 0.12, sh)
    sh = sh + 0.1 * ((dx0 < -1) & (dx0 > -4)) - 0.08 * ((dx0 > 1) & (dx0 < 4))
    rgb = quantise(np.clip(sh, 0, 1), CANVAS)
    rgb = _lay(rgb, stain > 0.4, 0.25 + 0.4 * stain, ramp("#4a2c20", "#6e4630", "#94664a", "#b08a68"))
    w = WM(n)
    w.ellipse(24, 16, 5, 5)
    w2 = WM(n)
    w2.ellipse(24, 16, 2.5, 2.5)
    ring = w.mask() & ~w2.mask()
    cord = (np.abs(_wd(x, 24, n) + 0.5 * np.sin(y * 0.3)) < 1.4) & (y >= 5) & (y < 11)
    tw = 0.5 + 0.4 * np.sin(y * 0.9 + x)
    rgb = _lay(rgb, (np.roll(ring, 1, 1) | np.roll(cord, 2, 1)) & ~(ring | cord) & _dith(n, 0.7), sh - 0.2, CANVAS)
    rgb = _lay(rgb, ring | cord, 0.15 + 0.4 * tw, DARKWOOD)
    rgb = _ov(rgb, (y >= 2) & (y < 5) & (np.abs(_wd(x, 24, n)) < 2.0), "#2a1e12")
    rgb = _ov(rgb, speckle(n, 0.012, 164) > 0.5, "#a49878")
    return rgb


def sky_day():
    """A bleached white-blue Mediterranean strip: deeper blue overhead, almost white haze at the horizon (bottom), thin cloud streaks, film grain. Wraps horizontally."""
    h, w = 64, 256
    big = noise(256, 40, 171, 3)
    yy = np.arange(h, dtype=np.float32)[:, None]
    xx = np.arange(w, dtype=np.float32)[None, :]
    base = (yy / (h - 1)) ** 1.15
    s1 = noise(256, 60, 172, 3)[(np.arange(h) * 5) % 256][:, :w]
    s2 = noise(256, 90, 173, 2)[(np.arange(h) * 7 + 40) % 256][:, :w]
    cloud = np.clip((s1 - 0.52) * 5.0, 0, 1) * np.clip(1.0 - np.abs(yy - 30) / 26.0, 0, 1) + \
        np.clip((s2 - 0.55) * 5.0, 0, 1) * np.clip(1.0 - np.abs(yy - 14) / 14.0, 0, 1) * 0.8
    sh = 0.12 + 0.72 * base + (big[:h, :w] - 0.5) * 0.12 + 0.3 * cloud
    sh = sh + 0.2 * np.clip((yy - 44) / 20.0, 0, 1) + (_R(174).rand(h, w) - 0.5) * 0.07
    d = np.sqrt((_wd(xx, 180, 256) / 60.0) ** 2 + ((yy - 40) / 26.0) ** 2)
    sh = sh + 0.22 * np.clip(1.0 - d, 0, 1) ** 1.5
    b = BAYER8[np.arange(h)[:, None] % 8, np.arange(w)[None, :] % 8]
    k = len(SKY) - 1
    i = np.clip(np.round(np.clip(sh, 0, 1) * k + b), 0, k).astype(int)
    return (SKY[i] * 255 + 0.5).astype(np.uint8)


# ---- billboards --------------------------------------------------------------------------------------------------------------------------------

class S:
    """A prop canvas (128 x 128, or 256 x 128 for the wide ones): masks painted through a palette ramp with ordered dither; the alpha is hard."""

    def __init__(self, w: int = 128, h: int = 128):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), np.uint8)
        self.a = np.zeros((h, w), np.uint8)
        self.x, self.y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))

    # masks
    def _pil(self, fn) -> np.ndarray:
        im = Image.new("L", (self.w, self.h), 0)
        fn(ImageDraw.Draw(im))
        return np.asarray(im) > 0

    def rect(self, x0, y0, x1, y1):
        return (self.x >= x0) & (self.x < x1) & (self.y >= y0) & (self.y < y1)

    def ell(self, cx, cy, rx, ry):
        return ((self.x + 0.5 - cx) / rx) ** 2 + ((self.y + 0.5 - cy) / ry) ** 2 <= 1.0

    def poly(self, pts):
        return self._pil(lambda d: d.polygon([tuple(p) for p in pts], fill=255))

    def line(self, pts, w=1):
        return self._pil(lambda d: d.line([tuple(p) for p in pts], fill=255, width=w))

    def nz(self, scale, seed, octaves=3):
        n = max(self.w, self.h)
        return noise(n, scale, seed, octaves)[:self.h, :self.w]

    # shading fields
    def hs(self, x0, x1, base=0.55, amp=0.4):
        """A cylinder's shade across x0..x1, lit from the left."""
        u = np.clip((self.x - x0) / max(x1 - x0, 1), 0, 1)
        return base + amp * (0.45 - u) + 0.1 * np.sin(u * np.pi)

    def vs(self, y0, y1, base=0.55, amp=0.3):
        v = np.clip((self.y - y0) / max(y1 - y0, 1), 0, 1)
        return base + amp * (0.4 - v)

    def bev(self, m, d=1, amt=0.14):
        off = np.zeros(m.shape, np.float32)
        for k in range(1, d + 1):
            w = 1.0 if k == 1 else 0.5
            off += amt * w * (m & ~_shift(m, -k, -k))
            off -= amt * w * (m & ~_shift(m, k, k))
        return off

    # painting
    def paint(self, mask, shade, pal, dither=1.0):
        sh = np.asarray(shade, np.float32)
        if sh.ndim == 0:
            sh = np.full((self.h, self.w), float(sh), np.float32)
        col = quantise(np.clip(sh, 0, 1), pal, dither)
        self.rgb[mask] = col[mask]
        self.a[mask] = 255

    def solid(self, mask, colour):
        c = (hexc(colour) * 255).astype(np.uint8) if isinstance(colour, str) else np.asarray(colour, np.uint8)
        self.rgb[mask] = c
        self.a[mask] = 255

    def dither(self, level):
        b = BAYER8[np.arange(self.h)[:, None] % 8, np.arange(self.w)[None, :] % 8] + 0.5
        return b < np.asarray(level)

    def edge(self, amt=0.5):
        """A one-pixel darker outline of the local colour along the silhouette (drawn inside the shape so the footprint is unchanged)."""
        m = self.a > 0
        inner = _shift(m, -1, 0) & _shift(m, 1, 0) & _shift(m, 0, -1) & _shift(m, 0, 1)
        border = m & ~inner
        # image borders count as outside only for pixels that are not on the sprite's rim
        self.rgb[border] = (self.rgb[border].astype(np.float32) * amt).astype(np.uint8)

    def dust(self, mask, y_from, y_to, seed, amt=0.8):
        """Orange dust blown onto the lower part of a shape: dithered, denser towards y_to."""
        t = np.clip((self.y - y_from) / max(y_to - y_from, 1), 0, 1)
        f = self.nz(3, seed, 2)
        lvl = t * amt * (0.6 + 0.8 * f)
        self.paint(mask & self.dither(lvl), 0.25 + 0.6 * f, ORANGE)

    def rgba(self) -> np.ndarray:
        return np.dstack([self.rgb, self.a])


def _shift(m: np.ndarray, dx: int, dy: int) -> np.ndarray:
    """out[y, x] = m[y + dy, x + dx], False outside (no wrap)."""
    h, w = m.shape
    out = np.zeros_like(m)
    ys0, ys1 = max(0, -dy), min(h, h - dy)
    xs0, xs1 = max(0, -dx), min(w, w - dx)
    out[ys0:ys1, xs0:xs1] = m[ys0 + dy:ys1 + dy, xs0 + dx:xs1 + dx]
    return out


DIGITS = {"0": "111101101101111", "1": "010110010010111", "2": "111001111100111", "3": "111001111001111", "4": "101101111001001",
          "5": "111100111001111", "7": "111001010010010", "8": "111101111101111", "9": "111101111001111"}


def _digits(sp: S, text: str, x0: int, y0: int, scale: int) -> np.ndarray:
    m = np.zeros((sp.h, sp.w), bool)
    for k, ch in enumerate(text):
        bits = DIGITS[ch]
        for i, b in enumerate(bits):
            if b == "1":
                cx, cy = x0 + k * (3 * scale + scale) + (i % 3) * scale, y0 + (i // 3) * scale
                m[cy:cy + scale, cx:cx + scale] = True
    return m


def thing_board():
    """The mission board: a cork board in a plank frame on two posts, a hand-drawn island map with red pins and strings, pinned notes, a slate with a painted tally."""
    sp = S()
    for x0 in (22, 96):
        m = sp.rect(x0, 98, x0 + 9, 128)
        sp.paint(m, sp.hs(x0, x0 + 9, 0.5, 0.5) + sp.nz(4, 201) * 0.1, DARKWOOD)
    frame = sp.rect(6, 6, 122, 108)
    inner = sp.rect(13, 13, 115, 101)
    fr = frame & ~inner
    gr = np.sin(sp.x * 0.5 + sp.nz(9, 202) * 8) * 0.06
    sp.paint(fr, 0.6 + gr + sp.bev(frame, 2, 0.12) + sp.bev(inner, 1, -0.1) * -1, DARKWOOD)
    sp.paint(frame & ~inner & sp.rect(6, 6, 122, 8), 0.8, DARKWOOD)
    cork = ramp("#5a3c20", "#7a5430", "#9a7040", "#b88a52", "#cca466")
    f = sp.nz(2, 203, 2)
    sp.paint(inner, 0.5 + (f - 0.5) * 0.7 + (_R(204).rand(sp.h, sp.w) - 0.5) * 0.3, cork)
    # the map: pale sea paper with an island
    sea = ramp("#6e8286", "#8aa0a0", "#a8bcb6", "#c4d4c8", "#dce6d6")
    paper = sp.rect(18, 19, 80, 94)
    sp.paint(paper, 0.62 + (sp.nz(8, 205) - 0.5) * 0.3 + sp.bev(paper, 1, 0.12), sea)
    sp.paint(paper & (((sp.x + sp.y * 2) % 11) < 1) & (sp.nz(5, 206) > 0.5), 0.3, sea)  # wave marks
    island = (sp.ell(50, 56, 17, 12) | sp.ell(37, 64, 9, 8) | sp.ell(62, 45, 9, 7) | sp.ell(30, 47, 6, 5) | sp.ell(56, 70, 8, 5)) & paper
    land = ramp("#5c4a2c", "#8a7442", "#b49a5a", "#d2bc7c", "#e6d49c")
    sp.paint(island, 0.55 + (sp.nz(5, 207) - 0.5) * 0.6 + sp.bev(island, 1, 0.12), land)
    coast = island & ~(_shift(island, 1, 0) & _shift(island, -1, 0) & _shift(island, 0, 1) & _shift(island, 0, -1))
    sp.solid(coast, "#4a3a22")
    for (ax, ay, bx, by) in ((22, 84, 34, 76), (34, 76, 44, 78)):
        pass
    route = sp.line([(24, 30), (36, 36), (44, 32), (58, 38), (66, 30)], 1) & sp.dither(0.5)
    sp.solid(route & paper & ~island, "#7a2a22")
    # pinned notes
    for (x0, y0, x1, y1, seed) in ((86, 18, 110, 40, 208), (90, 44, 112, 56, 209)):
        n_ = sp.rect(x0, y0, x1, y1)
        sp.paint(n_, 0.7 + (sp.nz(4, seed) - 0.5) * 0.2 + sp.bev(n_, 1, 0.1), PAPER)
        for ly in range(y0 + 5, y1 - 2, 4):
            sp.solid(sp.rect(x0 + 3, ly, x1 - 3 - (ly * 7 % 6), ly + 1), "#8a8068")
    # strings and pins
    pins = [(50, 52), (36, 64), (62, 44), (30, 47), (84, 30), (96, 50)]
    for (a, b) in ((0, 1), (0, 2), (2, 3), (0, 4), (2, 5), (1, 3)):
        sp.solid(sp.line([pins[a], pins[b]], 1), "#c4b890" if (a + b) % 2 else "#b02a22")
    for (px, py) in pins:
        sp.solid(sp.ell(px + 0.5, py + 1.5, 3.2, 3.2), "#3a2414")
        sp.paint(sp.ell(px, py, 3, 3), sp.hs(px - 3, px + 3, 0.6, 0.6), RED)
        sp.solid(sp.rect(px - 1, py - 1, px, py), "#f4b0a0")
    # the slate with a tally of missions
    slate = sp.rect(86, 62, 118, 98)
    sp.paint(slate, 0.5, DARKWOOD)
    face = sp.rect(89, 65, 115, 95)
    sp.paint(face, 0.3 + (sp.nz(3, 210) - 0.5) * 0.3, ramp("#1a2220", "#2a3634", "#3a4846", "#4e5e5a"))
    dg = _digits(sp, "14", 92, 71, 3)
    sp.solid(dg, "#ece6c8")
    sp.solid(_shift(dg, -1, -1) & ~dg & sp.dither(0.4), "#a8a48c")
    sp.solid(sp.rect(91, 90, 113, 91) & sp.dither(0.6), "#8c8c78")  # the chalk smudge
    sp.edge(0.45)
    return sp.rgba()


def thing_bomber_nose():
    """An invented twin-engine bomber nose-on at three-quarter: glazed nose, two radial engines under olive-drab cowls, a faded patch, dusty tyres. 256 x 128."""
    sp = S(256, 128)
    # tail fin behind
    fin = sp.poly([(120, 6), (136, 6), (146, 26), (144, 56), (116, 56), (114, 24)])
    sp.paint(fin, 0.34 + sp.hs(114, 146, 0, 0.3) * 0.5 + sp.nz(6, 301) * 0.1 + sp.bev(fin, 1, 0.1), OLIVE)
    # wing
    wing = sp.poly([(4, 72), (34, 60), (222, 60), (252, 72), (248, 80), (8, 80)])
    sp.paint(wing, 0.62 - (sp.y - 60) * 0.02 + (sp.nz(9, 302) - 0.5) * 0.2 + sp.bev(wing, 1, 0.1), OLIVE)
    sp.paint(wing & (sp.y > 76), 0.18, OLIVE)
    sp.paint(sp.rect(24, 62, 48, 68) & wing, 0.88, ramp("#5a5a38", "#7a7a4a", "#9a9a62", "#b4b478"))  # faded wing patch
    # fuselage
    fus = sp.ell(128, 78, 38, 32)
    sp.paint(fus, 0.62 + sp.hs(90, 166, 0, 0.55) * 0.9 + (sp.nz(8, 303) - 0.5) * 0.12 + sp.bev(fus, 1, 0.1), OLIVE)
    patch = sp.ell(108, 60, 16, 10) & fus & (sp.nz(3, 304) > 0.3)
    sp.paint(patch, 0.55 + (sp.nz(2, 305) - 0.5) * 0.5, ramp("#5a6038", "#7e8450", "#a0a468", "#bcbd82"))
    sp.paint(sp.line([(128, 52), (128, 62)], 1), 0.1, OLIVE)
    # glazed nose
    gl = sp.ell(128, 86, 25, 21)
    diag = (sp.x - 108 + sp.y - 70) / 60.0
    sp.paint(gl, 0.75 - diag * 0.7 + (sp.nz(4, 306) - 0.5) * 0.12, GLASS)
    for k, a in enumerate((-0.9, -0.3, 0.3, 0.9)):
        sp.solid(sp.line([(128, 66), (128 + 28 * np.sin(a), 66 + 28 * np.cos(a))], 1) & gl, "#2a3220")
    for ry in (78, 88, 98):
        sp.solid(sp.line([(104, ry), (128, ry + 3), (152, ry)], 1) & gl, "#2a3220")
    sp.solid(sp.ell(128, 86, 25, 21) & ~sp.ell(128, 86, 23.5, 19.6), "#262c1c")
    sp.solid(sp.rect(114, 74, 118, 77), "#f2f8ee")
    sp.solid(sp.rect(116, 77, 120, 79), "#cfe0dc")
    # engines
    for cx in (60, 196):
        cy = 80
        rear = sp.ell(cx + (5 if cx < 128 else -5), cy + 3, 25, 24)
        sp.paint(rear, 0.28 + sp.hs(cx - 25, cx + 25, 0, 0.3) + 0.1, OLIVE)
        cowl = sp.ell(cx, cy, 25, 25)
        dxy = np.sqrt((sp.x - (cx - 9)) ** 2 + (sp.y - (cy - 9)) ** 2) / 36.0
        sp.paint(cowl, 0.86 - dxy * 0.85 + (sp.nz(7, 310 + cx) - 0.5) * 0.15, OLIVE)
        lip = cowl & ~sp.ell(cx, cy, 21.5, 21.5)
        sp.paint(lip, 0.5 + 0.35 * (sp.x < cx) * (sp.y < cy) - 0.2 * (sp.x > cx + 5), STEEL)
        mouth = sp.ell(cx, cy, 18, 18)
        sp.paint(mouth, 0.08 + 0.12 * (np.sqrt((sp.x - cx) ** 2 + (sp.y - cy) ** 2) / 18.0), STEEL)
        for k in range(9):
            a = k / 9.0 * 6.2832
            px, py = cx + 11.5 * np.cos(a), cy + 11.5 * np.sin(a)
            cyl = sp.ell(px, py, 3.2, 3.2)
            sp.paint(cyl, 0.7 - 0.5 * ((sp.x - px) + (sp.y - py) > 1), STEEL)
        sp.paint(sp.ell(cx, cy, 6, 6), sp.hs(cx - 6, cx + 6, 0.55, 0.6) + 0.1, STEEL)
        sp.solid(sp.rect(cx - 3, cy - 3, cx - 1, cy - 1), "#dcdcd0")
        for a in (-1.5708, 0.5236, 2.618):
            tipx, tipy = cx + 34 * np.cos(a), cy + 34 * np.sin(a)
            bl = sp.poly([(cx - 3 * np.sin(a), cy + 3 * np.cos(a)), (tipx - 2.5 * np.sin(a), tipy + 2.5 * np.cos(a)),
                          (tipx + 2.5 * np.sin(a), tipy - 2.5 * np.cos(a)), (cx + 3 * np.sin(a), cy - 3 * np.cos(a))])
            sp.paint(bl & ~sp.ell(cx, cy, 6, 6), 0.1 + 0.1 * (bl & (sp.x < cx)) + 0.18 * _shift(~bl, 1, 1), ramp("#0c0e08", "#1c2012", "#30361e"))
            sp.solid(sp.ell(tipx, tipy, 2.5, 2.5) & bl & (sp.y > cy + 5), "#b8a428")
    sp.paint(sp.rect(36, 62, 44, 66) & sp.ell(60, 80, 25, 25), 0.95, ramp("#5a6038", "#7e8450", "#a0a468", "#bcbd82"))
    # undercarriage
    for cx in (60, 196, 128):
        top = 104 if cx != 128 else 108
        sp.paint(sp.rect(cx - 2, top - 14, cx + 2, top), sp.hs(cx - 2, cx + 2, 0.5, 0.5), STEEL)
        wr = 9 if cx != 128 else 6
        wh = 15 if cx != 128 else 11
        tire = sp.ell(cx, 127 - wh, wr, wh)
        rub = ramp("#080808", "#141412", "#222220", "#34342e")
        sp.paint(tire, 0.3 + sp.hs(cx - wr, cx + wr, 0, 0.5) * 0.6 + (sp.nz(3, 320 + cx) - 0.5) * 0.2, rub)
        sp.paint(sp.ell(cx, 127 - wh, wr * 0.45, wh * 0.45), 0.5 + 0.3 * (sp.x < cx), STEEL)
        sp.dust(tire, 127 - wh, 128, 330 + cx, 1.6)
    sp.paint(sp.ell(128, 112, 14, 3) & (sp.y > 111) & False, 0.2, STEEL)
    sp.edge(0.45)
    return sp.rgba()


def thing_certificate():
    """A framed certificate on a wall: gilt ornate frame, a blank cream sheet with a ruled panel and ruled lines, a red ribbon seal; no text."""
    sp = S()
    frame = sp.rect(16, 4, 112, 124)
    inner = sp.rect(27, 15, 101, 113)
    ring = frame & ~inner
    stripe = ((sp.x + sp.y) % 6) < 3
    sp.paint(ring, 0.55 + 0.2 * stripe * (((sp.x < 24) | (sp.x > 103) | (sp.y < 12) | (sp.y > 116))) + sp.bev(frame, 2, 0.16) - sp.bev(inner, 1, 0.1) + (sp.nz(4, 401) - 0.5) * 0.15, BRASS)
    for (cx, cy) in ((16, 4), (112, 4), (16, 124), (112, 124)):
        c = sp.rect(cx - 7 + (7 if cx == 16 else 0), cy - 7 + (7 if cy == 4 else 0), cx + 7 + (7 if cx == 16 else 0), cy + 7 + (7 if cy == 4 else 0)) & frame
        sp.paint(c, 0.8 + sp.bev(c, 1, 0.12), BRASS)
        sp.solid(sp.rect(cx + (7 if cx == 16 else -7) - 1, cy + (7 if cy == 4 else -7) - 1, cx + (7 if cx == 16 else -7) + 2, cy + (7 if cy == 4 else -7) + 2) & frame, "#5a4010")
    sp.solid(inner & ~sp.rect(28, 16, 100, 112), "#3a2a10")
    sheet = sp.rect(28, 16, 100, 112)
    sp.paint(sheet, 0.72 + (sp.nz(5, 402) - 0.5) * 0.3 + sp.bev(sheet, 1, -0.1) * 0 + ((sp.x < 31) * 0.0), PAPER)
    sp.solid(sp.rect(28, 16, 100, 18), "#6a604a")  # the mount's shadow
    # a ruled inner border and a flourish band
    sp.solid(sp.rect(33, 21, 95, 22) | sp.rect(33, 107, 95, 108) | sp.rect(33, 21, 34, 108) | sp.rect(94, 21, 95, 108), "#8a1c16")
    for k in range(7):
        sp.solid(sp.ell(44 + k * 6.7, 30, 2.5, 1.5) | sp.rect(42 + k * 6.7, 33, 46 + k * 6.7, 34), "#4a5a78")
    sp.solid(sp.rect(54, 38, 74, 40) | sp.rect(58, 42, 70, 43), "#6a7a98")
    for ly in range(50, 80, 6):
        sp.solid(sp.rect(40, ly, 88, ly + 1) & sp.dither(0.85), "#8a96b0")
    sp.solid(sp.rect(40, 80, 64, 81), "#8a96b0")
    # the seal
    for tx in (-9, 3):
        t = sp.poly([(64 + tx, 92), (64 + tx + 6, 92), (64 + tx + 9, 106), (64 + tx + 5, 104), (64 + tx + 1, 106)])
        sp.paint(t, 0.5 + (sp.x - 56) * 0.01, RED)
    seal = sp.ell(64, 90, 10, 10)
    sp.paint(seal, 0.55 + 0.35 * (1 - np.sqrt((sp.x - 61) ** 2 + (sp.y - 87) ** 2) / 14.0) + sp.bev(seal, 1, 0.1), RED)
    sp.solid(sp.ell(64, 90, 6, 6) & ~sp.ell(64, 90, 4.5, 4.5), "#7a1812")
    sp.solid(sp.rect(62, 86, 64, 88), "#e88a78")
    sp.edge(0.4)
    return sp.rgba()


def thing_cot_empty():
    """An empty army cot, side-on: canvas bed on crossed wooden legs, a grey blanket folded square, a pillow, a kit bag at the foot, a pair of boots beside it."""
    sp = S()
    canvas = ramp("#4a4a30", "#666a42", "#808656", "#9ca06c", "#b4b684")
    wood = DARKWOOD
    # legs (crossed)
    for lx in (18, 90):
        sp.paint(sp.line([(lx, 86), (lx + 14, 122)], 4), sp.hs(lx, lx + 14, 0.5, 0.4), wood)
        sp.paint(sp.line([(lx + 14, 86), (lx, 122)], 4), sp.hs(lx, lx + 14, 0.4, 0.4), wood)
    sp.paint(sp.rect(14, 116, 108, 119), 0.3, wood)
    # the bed: front face, top face, end face
    front = sp.rect(8, 76, 100, 88)
    top = sp.poly([(8, 76), (22, 66), (114, 66), (100, 76)])
    end = sp.poly([(100, 76), (114, 66), (114, 78), (100, 88)])
    sp.paint(front, 0.5 + (sp.nz(5, 501) - 0.5) * 0.25 + 0.06 * ((sp.x % 6) < 1), canvas)
    sp.paint(top, 0.72 + (sp.nz(5, 502) - 0.5) * 0.25, canvas)
    sp.paint(end, 0.32, canvas)
    sp.paint(sp.rect(8, 86, 100, 90), sp.hs(0, 1, 0.4, 0), wood)
    sp.solid(sp.rect(8, 87, 100, 88), "#0e0804")
    # blanket box (folded square) and pillow
    bl = ramp("#3a3c3c", "#585c5a", "#787c78", "#98a09a", "#b6bdb6")
    bf = sp.rect(54, 62, 100, 74)
    bt = sp.poly([(54, 62), (64, 55), (110, 55), (100, 62)])
    be = sp.poly([(100, 62), (110, 55), (110, 67), (100, 74)])
    sp.paint(bt, 0.78 + (sp.nz(3, 503) - 0.5) * 0.25, bl)
    sp.paint(bf, 0.58 + (sp.nz(3, 504) - 0.5) * 0.2, bl)
    sp.paint(be, 0.3, bl)
    for ly in (65, 68, 71):
        sp.solid(sp.rect(54, ly, 100, ly + 1), "#4c504e")
    sp.solid(sp.rect(54, 62, 100, 63), "#c4cac2")
    pil = sp.poly([(14, 64), (20, 58), (44, 58), (48, 64), (44, 70), (18, 70)])
    pt = sp.poly([(16, 66), (22, 58), (46, 58), (48, 62), (42, 68), (20, 68)])
    sp.paint(pil, 0.78 + 0.2 * (sp.x < 28) - 0.1 * (sp.y > 64) + (sp.nz(3, 505) - 0.5) * 0.15, PAPER)
    # the kit bag at the foot: an olive duffel stood against the end
    bag = sp.rect(108, 70, 126, 122) & (sp.ell(117, 71, 9, 5) | sp.rect(108, 71, 126, 120) | sp.ell(117, 120, 9, 4))
    sp.paint(bag, sp.hs(107, 127, 0.55, 0.55) + (sp.nz(4, 506) - 0.5) * 0.2 + 0.05 * ((sp.y % 8) < 1), OLIVE)
    sp.solid(sp.rect(111, 70, 123, 72), "#16180e")
    sp.solid(sp.line([(117, 66), (117, 71)], 3), "#a89a6a")
    sp.solid(sp.rect(108, 96, 126, 98) & bag, "#8a7a52")
    # boots
    leather = ramp("#120c08", "#241a12", "#3a2a1c", "#54402c", "#6e563c")
    for bx in (20, 42):
        boot = sp.poly([(bx, 98), (bx + 11, 98), (bx + 12, 112), (bx + 25, 114), (bx + 29, 120), (bx + 28, 124), (bx - 1, 124)])
        sp.paint(boot, 0.5 + sp.bev(boot, 1, 0.18) + 0.2 * (sp.y < 104) * (sp.x < bx + 5) + (sp.nz(3, 507 + bx) - 0.5) * 0.2, leather)
        sp.solid(sp.rect(bx - 1, 121, bx + 29, 124) & boot, "#0a0806")
        sp.solid(sp.rect(bx + 2, 106, bx + 9, 107) | sp.rect(bx + 2, 110, bx + 9, 111), "#9a9078")  # laces
    sp.dust(sp.rect(90, 100, 128, 128) & (sp.a > 0), 106, 128, 508, 0.5)
    sp.edge(0.45)
    return sp.rgba()


def thing_cot_ward():
    """An iron hospital cot with a white sheet and grey blanket, barred head and foot ends, and a bedside crate with a tin mug."""
    sp = S()
    iron = ramp("#0e0e10", "#1c1c20", "#2c2c32", "#44444c", "#66666e")
    # end frames with bars
    def endframe(x0, x1, ytop):
        m = sp.rect(x0, ytop, x1, 118)
        bars = ((sp.x - x0) % 4 < 2)
        rails = sp.rect(x0, ytop, x1, ytop + 3) | sp.rect(x0, 84, x1, 87) | sp.rect(x0, 112, x1, 115)
        posts = sp.rect(x0, ytop, x0 + 3, 120) | sp.rect(x1 - 3, ytop, x1, 120)
        keep = m & (bars | rails | posts)
        sp.paint(keep, sp.hs(x0, x1, 0.55, 0.3) + 0.15 * (sp.y < ytop + 3), iron)
        sp.paint(sp.ell(x0 + 1.5, ytop - 1, 3, 3) | sp.ell(x1 - 1.5, ytop - 1, 3, 3), 0.8, ramp("#403820", "#7e6a30", "#b8a050"))
    endframe(6, 20, 44)
    endframe(82, 94, 66)
    # mattress, sheet, blanket
    ts = sp.rect(18, 82, 84, 96)
    sheet = sp.rect(18, 80, 86, 94)
    sp.paint(sheet, 0.82 + (sp.nz(4, 551) - 0.5) * 0.3 + 0.05 * ((sp.y % 5) < 1), PAPER)
    top = sp.poly([(18, 80), (26, 74), (92, 74), (86, 80)])
    sp.paint(top, 0.9 + (sp.nz(4, 552) - 0.5) * 0.2, PAPER)
    bl = ramp("#383a3a", "#585c5a", "#787c78", "#989f9a", "#b4bab2")
    blk = sp.rect(46, 78, 86, 94)
    sp.paint(blk, 0.6 + (sp.nz(3, 553) - 0.5) * 0.25 + 0.08 * ((sp.y % 6) < 1) + sp.bev(blk, 1, 0.1), bl)
    sp.paint(sp.poly([(46, 78), (54, 72), (92, 72), (86, 78)]), 0.78 + (sp.nz(3, 554) - 0.5) * 0.2, bl)
    sp.solid(sp.rect(46, 84, 86, 85), "#4a4e4c")
    pil = sp.ell(31, 76, 12, 5)
    sp.paint(pil, 0.88 + 0.1 * (sp.x < 28) + (sp.nz(3, 555) - 0.5) * 0.2, PAPER)
    sp.paint(sp.rect(16, 94, 88, 98), 0.4, iron)
    # legs, casters
    for lx in (22, 78):
        sp.paint(sp.rect(lx, 98, lx + 3, 116), sp.hs(lx, lx + 3, 0.5, 0.5), iron)
        sp.paint(sp.ell(lx + 1.5, 119, 4, 4), 0.35, ramp("#0a0a0a", "#1a1a1a", "#2e2e2e"))
        sp.solid(sp.rect(lx, 116, lx + 3, 118), "#6a6a70")
    # the bedside crate and tin mug
    crate = sp.rect(98, 88, 126, 124)
    row = ((sp.y - 88) // 9).astype(int)
    tone = _R(556).rand(6).astype(np.float32)[np.clip(row, 0, 5)]
    sp.paint(crate, 0.55 + 0.2 * (tone - 0.5) + (sp.nz(5, 557) - 0.5) * 0.2 - 0.3 * (((sp.y - 88) % 9) < 1) + sp.bev(crate, 1, 0.14), WOOD)
    sp.paint(sp.rect(98, 88, 126, 92), 0.78, WOOD)
    sp.solid(sp.rect(98, 120, 126, 124) & sp.dither(0.5), "#b8884a")
    sp.paint(sp.line([(100, 92), (124, 122)], 3) & crate, 0.35, WOOD)
    mug = sp.rect(105, 74, 117, 88)
    sp.paint(mug, sp.hs(105, 117, 0.65, 0.5), ramp("#4a5058", "#7a8288", "#a8aeb0", "#d0d4d0", "#f2f4ee"))
    sp.paint(sp.ell(111, 74.5, 6, 2), 0.2, STEEL)
    sp.solid(sp.ell(111, 74.5, 6, 2) & ~sp.ell(111, 74.5, 4.5, 1.2), "#dcdcd4")
    hd = sp.ell(120, 80, 4.5, 5) & ~sp.ell(120, 80, 2, 3)
    sp.paint(hd, 0.6, ramp("#4a5058", "#7a8288", "#a8aeb0"))
    sp.dust(sp.rect(0, 108, 128, 128) & (sp.a > 0), 112, 128, 558, 0.6)
    sp.edge(0.4)
    return sp.rgba()


def _crate(sp: S, x0, y0, x1, y1, seed, stencil=True):
    """A slatted wooden crate seen face on: planks, a frame with a cross brace, nail heads, an optional blank painted square."""
    m = sp.rect(x0, y0, x1, y1)
    row = ((sp.y - y0) // 7).astype(int)
    tone = _R(seed).rand(24).astype(np.float32)[np.clip(row, 0, 23)]
    sh = 0.52 + 0.22 * (tone - 0.5) + (sp.nz(5, seed + 1) - 0.5) * 0.2 + np.sin(sp.x * 0.6 + sp.nz(9, seed + 2) * 6) * 0.04
    sh = sh - 0.28 * (((sp.y - y0) % 7) < 1)
    sp.paint(m, sh, WOOD)
    fr = m & ~sp.rect(x0 + 4, y0 + 4, x1 - 4, y1 - 4)
    sp.paint(fr, 0.42 + (sp.nz(4, seed + 3) - 0.5) * 0.2 + sp.bev(m, 1, 0.16), WOOD)
    br = sp.line([(x0 + 4, y1 - 4), (x1 - 4, y0 + 4)], 4) & m
    sp.paint(br, 0.4 + 0.12 * (sp.y < sp.x * 0 + (y0 + y1) / 2), WOOD)
    sp.solid(sp.line([(x0 + 4, y1 - 4), (x1 - 4, y0 + 4)], 1) & m & sp.dither(0.3) & False, "#000000")
    for (nx, ny) in ((x0 + 2, y0 + 2), (x1 - 3, y0 + 2), (x0 + 2, y1 - 3), (x1 - 3, y1 - 3)):
        sp.solid(sp.rect(nx, ny, nx + 1, ny + 1), "#2a2014")
    if stencil:
        cx, cy = (x0 + x1) // 2 - 6, (y0 + y1) // 2 - 3
        sp.solid(sp.rect(cx, cy, cx + 12, cy + 12) & ~sp.rect(cx + 2, cy + 2, cx + 10, cy + 10), "#2e3820")
        sp.solid(sp.rect(cx + 4, cy + 4, cx + 8, cy + 8), "#2e3820")


def thing_crate_stack():
    """A stack of supply crates stencilled with blank painted squares, a tarp half over them tied with rope, an egg basket on top."""
    sp = S()
    _crate(sp, 4, 84, 62, 126, 601)
    _crate(sp, 64, 84, 124, 126, 611)
    _crate(sp, 18, 44, 80, 84, 621)
    _crate(sp, 82, 56, 118, 84, 631, False)
    # tarp over the right side
    tarp = sp.poly([(66, 40), (108, 44), (122, 62), (126, 96), (120, 116), (96, 104), (84, 86), (70, 62)])
    fold = np.sin((sp.x * 0.5 + sp.y * 0.35) * 1.4 + sp.nz(8, 641) * 5) * 0.14
    sp.paint(tarp, 0.5 + fold + (sp.nz(4, 642) - 0.5) * 0.2 + sp.bev(tarp, 1, 0.14), OLIVE)
    sp.solid(sp.line([(70, 56), (116, 98)], 1) & tarp, "#1a1e10")
    # rope round the stack
    rope = sp.line([(78, 38), (84, 84), (92, 126)], 2) | sp.line([(8, 100), (62, 100), (124, 104)], 2)
    sp.paint(rope, 0.45 + 0.3 * (((sp.x + sp.y) % 4) < 2), ramp("#3a2c18", "#6a5230", "#a08a58", "#c8b682"))
    # egg basket on the middle crate
    bk = sp.ell(40, 42, 17, 8) | sp.rect(24, 30, 57, 42)
    wick = ramp("#4a3016", "#7a5628", "#a8803c", "#cca862")
    sp.paint(sp.ell(40, 29, 16, 5) & ~sp.ell(40, 29, 12, 3), 0.8, wick)
    for (ex, ey) in ((30, 25), (37, 23), (44, 24), (51, 26), (34, 28), (42, 28)):
        sp.paint(sp.ell(ex, ey, 3.4, 4.2), 0.6 + 0.4 * (sp.x < ex), ramp("#8a7a60", "#bcae90", "#e4d8bc", "#f8f2e0"))
    sp.paint(bk & (sp.y > 29), 0.55 + 0.25 * (((sp.x + sp.y) % 3) < 1) - 0.2 * (((sp.x - sp.y) % 6) < 1) + sp.hs(23, 58, 0, 0.3) * 0.7 + (sp.nz(3, 651) - 0.5) * 0.15, wick)
    sp.paint(sp.ell(40, 29, 16.5, 5.5) & ~sp.ell(40, 29, 13, 3.4) & (sp.y >= 28), 0.75, wick)
    sp.paint(sp.line([(26, 30), (30, 14), (40, 8), (50, 14), (54, 30)], 2), 0.55, wick)
    sp.dust(sp.rect(0, 100, 128, 128) & (sp.a > 0), 104, 128, 652, 0.7)
    sp.edge(0.45)
    return sp.rgba()


def thing_desk_lamp():
    """A green-shaded desk lamp on a brass-and-black base, with a warm dithered cone of light falling to the desk."""
    sp = S()
    cone = sp.poly([(46, 62), (76, 56), (118, 122), (10, 126)])
    t = np.clip((sp.y - 58) / 66.0, 0, 1)
    lvl = 0.78 * (1 - t) ** 0.8 + 0.1
    edge_fade = np.clip(1.0 - np.abs((sp.x - 63 - (sp.y - 58) * 0.0) / (10 + t * 56.0)), 0, 1)
    sp.paint(cone & sp.dither(lvl * (0.5 + 0.7 * edge_fade)), 0.95 - 0.5 * t + 0.1 * edge_fade, WARM)
    # base and stem
    base = sp.ell(66, 118, 22, 7)
    sp.paint(base, sp.hs(44, 88, 0.45, 0.6) + 0.1, ramp("#0a0c0c", "#18201c", "#2a3630", "#3e4e44"))
    sp.paint(sp.ell(66, 114, 20, 5) & (sp.y < 117), 0.55 + 0.35 * (sp.x < 60), ramp("#0a0c0c", "#18201c", "#2a3630", "#3e4e44"))
    enamel = ramp("#050808", "#0e1612", "#1a2822", "#2c3e36", "#46605a")
    sp.paint(sp.rect(63, 82, 68, 114), sp.hs(63, 68, 0.5, 0.8), enamel)
    sp.paint(sp.line([(65, 84), (54, 56)], 4), 0.5 + 0.3 * (sp.x < 60), enamel)
    sp.paint(sp.ell(65, 84, 4, 4), sp.hs(61, 69, 0.55, 0.6), BRASS)
    sp.paint(sp.rect(60, 98, 70, 101), 0.55, BRASS)
    # the shade, a tilted green dome
    shade = sp.poly([(40, 56), (50, 34), (68, 30), (82, 40), (76, 58), (62, 60)])
    g = ramp("#0c2014", "#16361f", "#244e2c", "#386a3c", "#58905a")
    d = (sp.x - 44 + sp.y - 34) / 60.0
    sp.paint(shade, 0.8 - d * 0.9 + (sp.nz(4, 701) - 0.5) * 0.1 + sp.bev(shade, 1, 0.12), g)
    sp.paint(sp.line([(40, 56), (76, 58)], 3), 0.3, g)
    sp.solid(sp.poly([(46, 44), (52, 38), (56, 40), (50, 48)]) & shade, "#8ac08a")
    sp.paint(sp.ell(60, 58, 14, 3) & (sp.y > 57), 0.95, WARM)
    sp.solid(sp.rect(56, 58, 66, 60), "#fffbe0")
    sp.edge(0.5)
    return sp.rgba()


def thing_desk_office():
    """A big battered office desk from the front: blotter, inkwell, piles of forms, an in-tray and an out-tray; drawer pedestals either side of the kneehole."""
    sp = S()
    # the pedestals and kneehole
    for (x0, x1) in ((8, 46), (82, 120)):
        ped = sp.rect(x0, 78, x1, 124)
        sp.paint(ped, 0.5 + (sp.nz(5, 801 + x0) - 0.5) * 0.22 + sp.bev(ped, 1, 0.14) + sp.hs(x0, x1, 0, 0.1), DARKWOOD)
        for k, (y0, y1) in enumerate(((81, 94), (96, 109), (111, 122))):
            dr = sp.rect(x0 + 3, y0, x1 - 3, y1)
            sp.paint(dr, 0.62 + (sp.nz(4, 810 + k + x0) - 0.5) * 0.2 + sp.bev(dr, 1, 0.18) + np.sin(sp.x * 0.6 + k) * 0.03, DARKWOOD)
            hx = (x0 + x1) // 2
            sp.paint(sp.rect(hx - 4, (y0 + y1) // 2 - 1, hx + 4, (y0 + y1) // 2 + 2), 0.7 + 0.2 * (sp.y < (y0 + y1) // 2), BRASS)
            sp.solid(sp.rect(hx - 3, (y0 + y1) // 2 + 2, hx + 3, (y0 + y1) // 2 + 3), "#0a0604")
    knee = sp.rect(46, 78, 82, 124)
    sp.paint(knee, 0.12 + (sp.nz(5, 820) - 0.5) * 0.08, DARKWOOD)
    sp.paint(sp.rect(52, 88, 76, 124), 0.28 + (sp.nz(5, 821) - 0.5) * 0.1 + sp.bev(sp.rect(52, 88, 76, 124), 1, 0.1), DARKWOOD)
    # the top: seen slightly from above
    top = sp.poly([(14, 62), (114, 62), (124, 76), (4, 76)])
    sp.paint(top, 0.7 + (sp.nz(6, 822) - 0.5) * 0.25 + np.sin(sp.x * 0.35 + sp.nz(8, 823) * 7) * 0.04, DARKWOOD)
    sp.paint(sp.rect(4, 76, 124, 82), 0.4 + 0.2 * (sp.y < 78) + (sp.nz(5, 824) - 0.5) * 0.15, DARKWOOD)
    sp.solid(sp.rect(4, 81, 124, 82), "#0a0604")
    sp.solid(sp.rect(30, 70, 31, 73) | sp.rect(92, 66, 93, 69), "#2a1a0c")  # a gouge or two
    # the blotter and inkwell
    bl = sp.poly([(40, 64), (88, 64), (92, 74), (36, 74)])
    sp.paint(bl, 0.5 + (sp.nz(4, 825) - 0.5) * 0.2, ramp("#10281a", "#1c3c26", "#2a5436", "#3c6e48"))
    for (px, py) in ((40, 64), (88, 64), (36, 74), (92, 74)):
        sp.solid(sp.rect(px - 1, py - 1, px + 1, py + 1) & bl, "#a8802a")
    sp.solid(sp.rect(52, 67, 70, 68) & sp.dither(0.5), "#d8d0b0")
    sp.paint(sp.ell(100, 72, 5, 2.5), 0.2, STEEL)
    ink = sp.rect(97, 62, 103, 72) | sp.ell(100, 62, 3, 2)
    sp.paint(ink, sp.hs(97, 103, 0.35, 0.7) * 0.6, ramp("#08080c", "#14141c", "#24242e", "#3c3c48"))
    sp.solid(sp.line([(102, 62), (108, 48)], 2), "#d8d0b0")
    sp.solid(sp.line([(107, 50), (109, 46)], 2), "#a8802a")
    # in-tray (left) with papers, a tall pile of forms (middle), out-tray (right)
    def tray(x0, x1, ytop, seed):
        base = sp.rect(x0, 66, x1, 74)
        sp.paint(base, 0.4 + sp.bev(base, 1, 0.14), STEEL)
        paper_h = _R(seed)
        yy = 66
        k = 0
        while yy > ytop:
            yy -= 3
            off = int(paper_h.randint(-2, 3))
            pr = sp.rect(x0 + 2 + off, yy, x1 - 2 + off, yy + 3) & (sp.y < 67)
            sp.paint(pr, 0.8 + 0.1 * (k % 2) + (sp.nz(3, seed + k) - 0.5) * 0.15, PAPER)
            sp.solid(sp.rect(x0 + 2 + off, yy + 2, x1 - 2 + off, yy + 3), "#8a8268")
            k += 1
        sp.paint(sp.rect(x0, 56, x0 + 2, 74) | sp.rect(x1 - 2, 56, x1, 74), 0.5, STEEL)
    tray(10, 40, 34, 830)
    tray(92, 122, 52, 860)
    pile = sp.rect(46, 14, 62, 66)
    ys = 66
    pr = _R(840)
    k = 0
    while ys > 14:
        ys -= 4
        off = int(pr.randint(-2, 3))
        p = sp.rect(46 + off, ys, 62 + off, ys + 4) & (sp.y < 67)
        sp.paint(p, 0.78 + 0.12 * (k % 2) + (sp.nz(3, 840 + k) - 0.5) * 0.15, PAPER)
        sp.solid(sp.rect(46 + off, ys + 3, 62 + off, ys + 4), "#8a8268")
        k += 1
    sp.solid(sp.rect(54, 30, 60, 31) | sp.rect(54, 38, 58, 39), "#5a6a88")
    sp.dust(sp.rect(0, 108, 128, 128) & (sp.a > 0), 112, 128, 870, 0.4)
    sp.edge(0.4)
    return sp.rgba()


def thing_door_office():
    """A heavy panelled office door in dark green paint: a frosted (blank) glass panel, two raised panels, a brass handle, a worn threshold."""
    sp = S()
    dg = ramp("#08160e", "#10261a", "#1a3a24", "#284e32", "#3a6a44")
    jamb = sp.rect(14, 0, 114, 128)
    sp.paint(jamb, 0.5 + (sp.nz(5, 901) - 0.5) * 0.2 + sp.hs(14, 114, 0, 0.1) + sp.bev(jamb, 2, 0.12), DARKWOOD)
    leaf = sp.rect(22, 8, 106, 124)
    sp.paint(leaf, 0.46 + (sp.nz(5, 902) - 0.5) * 0.2 + np.sin(sp.y * 0.5 + sp.nz(9, 903) * 4) * 0.03 + sp.bev(leaf, 2, 0.12), dg)
    chip = (sp.nz(4, 904) > 0.74) & leaf & sp.dither(0.7)
    sp.paint(chip, 0.4 + 0.3 * sp.nz(2, 905), ramp("#3a2a18", "#6a5234", "#8e7850"))
    # glass
    gl = sp.rect(34, 18, 94, 56)
    sp.solid(gl.copy() | sp.rect(32, 16, 96, 58), "#050e08")
    sp.paint(gl, 0.7 - (sp.x + sp.y - 52) / 150.0 + (_R(906).rand(sp.h, sp.w) - 0.5) * 0.18 + 0.22 * (((sp.x + sp.y) % 9) < 2), GLASS)
    sp.solid(sp.rect(34, 18, 94, 19) | sp.rect(34, 18, 35, 56), "#d8e6e0")
    sp.solid(sp.rect(64, 18, 65, 56), "#3a4c3c")
    # raised panels
    for (y0, y1) in ((64, 94), (100, 120)):
        p = sp.rect(34, y0, 94, y1)
        sp.paint(p, 0.5 + (sp.nz(4, 910 + y0) - 0.5) * 0.15, dg)
        sp.paint(p & ~sp.rect(38, y0 + 4, 90, y1 - 4), 0.5, dg)
        sp.solid(sp.rect(34, y0, 94, y0 + 1) | sp.rect(34, y0, 35, y1), "#3e6a48")
        sp.solid(sp.rect(34, y1 - 1, 94, y1) | sp.rect(93, y0, 94, y1), "#04100a")
        sp.paint(sp.rect(38, y0 + 4, 90, y1 - 4), 0.38 + (sp.nz(4, 915 + y0) - 0.5) * 0.15, dg)
    # handle
    sp.paint(sp.rect(90, 70, 97, 90), 0.6 + 0.3 * (sp.x < 93), BRASS)
    sp.paint(sp.ell(93.5, 82, 5, 5), sp.hs(88, 99, 0.6, 0.7), BRASS)
    sp.solid(sp.rect(92, 76, 94, 79), "#fff0b8")
    sp.solid(sp.rect(93, 72, 94, 74), "#0a0604")
    sp.paint(sp.rect(14, 122, 114, 128), 0.3 + (sp.nz(4, 920) - 0.5) * 0.2, DARKWOOD)
    sp.dust(sp.rect(0, 100, 128, 128) & (sp.a > 0), 108, 128, 921, 0.5)
    sp.edge(0.45)
    return sp.rgba()


def thing_door_open_light():
    """An open wooden door with blinding white daylight beyond; the leaf has swung inward and shows as a wooden wedge down the left of the doorway."""
    sp = S()
    jamb = sp.rect(16, 0, 112, 128)
    sp.paint(jamb, 0.5 + (sp.nz(5, 951) - 0.5) * 0.2 + sp.bev(jamb, 2, 0.12), DARKWOOD)
    hole = sp.rect(26, 8, 102, 124)
    glare = np.clip(1.0 - np.minimum.reduce([sp.x - 26, 101 - sp.x, sp.y - 8, 123 - sp.y]) / 14.0, 0, 1)
    wash = ramp("#c8d4d0", "#e4ece8", "#f6f9f4", "#ffffff")
    sh = 0.78 + (sp.nz(8, 952) - 0.5) * 0.2 - glare * 0.35 + 0.22 * (sp.y < 60) * 0.0
    sp.paint(hole, sh, wash)
    # faint washed-out world: a pale sky band and a bleached ground band
    sp.paint(hole & (sp.y > 76) & (sp.y < 96) & sp.dither(0.35), 0.3, ramp("#e8d8a8", "#f2e6bc", "#faf2d4"))
    sp.paint(hole & (sp.y > 96), 0.55 + (sp.nz(4, 953) - 0.5) * 0.3, ramp("#f0e2b8", "#f8eecc", "#fffae0"))
    sp.paint(hole & (sp.y < 30) & sp.dither(0.3), 0.2, ramp("#d0e0ea", "#e0ecf2"))
    for k in range(3):  # glare streaks
        sp.solid(sp.line([(40 + k * 22, 10), (30 + k * 22, 120)], 1) & hole & sp.dither(0.3) & False, "#ffffff")
    # the leaf, swung inward: near edge on the left, shorter far edge
    leaf = sp.poly([(26, 8), (56, 20), (56, 112), (26, 124)])
    pl = ((sp.x - 26) // 6).astype(int)
    tone = _R(954).rand(8).astype(np.float32)[np.clip(pl, 0, 7)]
    sp.paint(leaf, 0.42 + 0.2 * (tone - 0.5) + (sp.nz(5, 955) - 0.5) * 0.18 - 0.28 * (((sp.x - 26) % 6) < 1) + 0.1 * (sp.x < 32), WOOD)
    sp.solid(sp.line([(56, 20), (56, 112)], 2), "#f2f4ec")  # light along the leaf's free edge
    sp.paint(sp.rect(26, 40, 40, 44) & leaf, 0.3, STEEL)
    sp.paint(sp.rect(26, 92, 40, 96) & leaf, 0.3, STEEL)
    sp.paint(sp.rect(40, 66, 55, 69) & leaf, 0.5, ramp("#3a2a0c", "#a8802a", "#f0d278"))
    sp.paint(sp.ell(50, 78, 2.4, 2.4), 0.7, BRASS)
    # a spill of light on the floor, dithered
    spill = sp.poly([(28, 124), (100, 124), (122, 128), (6, 128)])
    sp.paint(spill & sp.dither(0.55), 0.95, ramp("#f0e2b8", "#fffae0", "#ffffff"))
    sp.dust(sp.rect(0, 112, 128, 128) & (sp.a > 0) & ~spill, 118, 128, 956, 0.3)
    sp.edge(0.5)
    return sp.rgba()


def thing_drip_stand():
    """An iron drip stand on a five-leg base with casters: a glass bottle of clear fluid hung upside down, a drip chamber and a looping tube."""
    sp = S()
    iron = ramp("#0e1012", "#1e2226", "#34393e", "#555c62", "#7e868a")
    for (x1, y1) in ((26, 120), (102, 120), (40, 124), (88, 124)):
        sp.paint(sp.line([(64, 110), (x1, y1 - 4)], 4), 0.5, iron)
        sp.paint(sp.ell(x1, y1 + 1, 4, 4), 0.35, ramp("#0a0a0a", "#1a1a1a", "#303030"))
        sp.solid(sp.rect(x1 - 1, y1 - 3, x1 + 1, y1 - 1), "#70767a")
    sp.paint(sp.ell(64, 108, 7, 5), 0.6, iron)
    sp.paint(sp.rect(62, 10, 66, 110), sp.hs(62, 66, 0.55, 0.9), iron)
    sp.paint(sp.rect(44, 10, 84, 13), 0.65 + 0.2 * (sp.y < 11), iron)
    sp.paint(sp.line([(46, 12), (46, 22)], 2) | sp.line([(82, 12), (82, 22)], 2), 0.6, iron)
    # the bottle: neck up on the hook
    sp.paint(sp.rect(60, 14, 68, 22), 0.3 + 0.3 * (sp.x < 63), ramp("#1a0e0a", "#3a2418", "#5a3a28"))
    bottle = sp.rect(48, 24, 80, 66) & (sp.ell(64, 25, 15, 6) | sp.rect(48, 26, 80, 62) | sp.ell(64, 62, 16, 5))
    sp.paint(bottle, 0.62 + 0.25 * (sp.x < 54) - 0.22 * (sp.x > 74) + (sp.nz(4, 1001) - 0.5) * 0.1, GLASS)
    fluid = bottle & (sp.y > 34)
    sp.paint(fluid, 0.55 + 0.3 * (sp.x < 56) - 0.15 * (sp.x > 74), ramp("#4a7c98", "#6a9cb4", "#8ebcd0", "#b8dce8"))
    sp.solid(sp.rect(50, 34, 78, 35) & bottle, "#e8f4f4")
    sp.paint(sp.rect(54, 40, 74, 52), 0.82 + (sp.nz(3, 1002) - 0.5) * 0.15, PAPER)
    sp.solid(sp.rect(54, 44, 74, 45) & sp.dither(0.5), "#8a8068")
    sp.solid(sp.rect(52, 26, 54, 34), "#f8fcfa")
    sp.solid(sp.rect(48, 62, 80, 66) & ~bottle, "#000000") if False else None
    # the drip chamber and tube
    sp.paint(sp.rect(60, 66, 68, 70), 0.3, ramp("#1a0e0a", "#3a2418", "#5a3a28"))
    ch = sp.rect(59, 70, 69, 84) & (sp.ell(64, 70, 5, 2) | sp.rect(59, 71, 69, 83) | sp.ell(64, 83, 5, 2))
    sp.paint(ch, 0.7 + 0.2 * (sp.x < 62), GLASS)
    sp.solid(sp.rect(63, 76, 65, 78), "#9ccae0")
    tube = sp.line([(64, 84), (64, 90), (78, 96), (92, 94), (96, 102), (90, 112), (84, 108)], 2)
    sp.paint(tube, 0.7 + 0.2 * (sp.y < 98), ramp("#5a6a68", "#8aa0a0", "#b4c8c4", "#dcecea"))
    sp.paint(sp.rect(59, 88, 70, 92), 0.55, ramp("#2a6a4a", "#3a8a5e", "#5ab084"))
    sp.edge(0.45)
    return sp.rgba()


def thing_emergency_box():
    """A red steel emergency control box: a warning triangle (a bolt, no letters), a pull handle behind a wire guard, a conduit down to the floor."""
    sp = S()
    sp.paint(sp.rect(61, 108, 67, 128), sp.hs(61, 67, 0.55, 0.7), STEEL)
    sp.paint(sp.rect(58, 108, 70, 112), 0.6, STEEL)
    box = sp.rect(18, 8, 110, 112)
    sp.paint(box, 0.58 + (sp.nz(5, 1051) - 0.5) * 0.2 + sp.bev(box, 2, 0.16) + 0.05 * (sp.y < 20), RED)
    dent = (sp.nz(4, 1052) > 0.72) & box
    sp.paint(dent & sp.dither(0.6), 0.18 + 0.1 * sp.nz(2, 1053), ramp("#8a8078", "#b0a89a", "#c8bfae"))  # chipped to bare paint
    for (rx, ry) in ((24, 14), (104, 14), (24, 106), (104, 106)):
        sp.paint(sp.ell(rx, ry, 2.4, 2.4), 0.8 - 0.4 * (sp.x > rx), STEEL)
    # warning triangle
    tri = sp.poly([(64, 16), (88, 56), (40, 56)])
    sp.solid(tri, "#10100a")
    inner = sp.poly([(64, 23), (82, 52), (46, 52)])
    sp.paint(inner, 0.7 + 0.2 * (sp.x < 60), ramp("#8a6a0c", "#c89a14", "#e8c02c", "#f8dc58"))
    bolt = sp.poly([(66, 29), (57, 43), (63, 43), (60, 51), (71, 37), (65, 37), (68, 29)])
    sp.solid(bolt, "#10100a")
    # the handle bay behind a wire guard
    bay = sp.rect(30, 64, 98, 104)
    sp.paint(bay, 0.1, ramp("#0a0405", "#1a0808", "#2c0e0c"))
    sp.solid(bay & ~sp.rect(31, 65, 97, 103), "#c8c4b6")
    sp.paint(sp.rect(62, 70, 66, 92), 0.6, STEEL)
    sp.paint(sp.rect(44, 88, 84, 96), sp.vs(88, 96, 0.9, 0.9), ramp("#8a6a0c", "#c89a14", "#e8c02c", "#f8f0a8"))
    sp.solid(sp.rect(44, 88, 84, 89), "#fffce0")
    mesh = bay & (((sp.x % 5) < 1) | ((sp.y % 5) < 1))
    sp.solid(mesh, "#aaa89a")
    sp.solid(bay & ~sp.rect(31, 65, 97, 103) & False, "#aaa89a")
    sp.dust(sp.rect(0, 108, 128, 128) & (sp.a > 0), 110, 128, 1054, 0.4)
    sp.edge(0.4)
    return sp.rgba()


def thing_filing_cabinet():
    """Two grey steel filing cabinets: the left one has its top drawer open with papers spilling out, the right is closed and dented."""
    sp = S()
    cab = ramp("#262b2c", "#424a4a", "#5e6868", "#7c8884", "#9ca69e", "#bcc2b6")

    def body(x0, y0, x1, y1, seed, drawers):
        m = sp.rect(x0, y0, x1, y1)
        sp.paint(m, 0.5 + sp.hs(x0, x1, 0, 0.1) + (sp.nz(5, seed) - 0.5) * 0.14 + sp.bev(m, 2, 0.12), cab)
        dh = (y1 - y0 - 4) // drawers
        for k in range(drawers):
            yy = y0 + 3 + k * dh
            d = sp.rect(x0 + 3, yy, x1 - 3, yy + dh - 2)
            sp.paint(d, 0.58 + (sp.nz(4, seed + 1 + k) - 0.5) * 0.12 + sp.bev(d, 1, 0.16), cab)
            hx = (x0 + x1) // 2
            sp.solid(sp.rect(hx - 8, yy + dh // 2 - 1, hx + 8, yy + dh // 2 + 2), "#12161a")
            sp.paint(sp.rect(hx - 7, yy + dh // 2 + 2, hx + 7, yy + dh // 2 + 3), 0.9, cab)
            lab = sp.rect(hx - 6, yy + 3, hx + 6, yy + 8)
            sp.solid(lab, "#2a2e30")
            sp.paint(sp.rect(hx - 5, yy + 4, hx + 5, yy + 7), 0.82, PAPER)
        return m

    body(68, 44, 122, 124, 1101, 3)
    body(4, 30, 58, 124, 1111, 4)
    # the open top drawer: dark cavity, papers standing up out of it, a few spilled over the front
    sp.solid(sp.rect(8, 33, 54, 52), "#0a0c0c")
    sp.paint(sp.rect(8, 33, 54, 35), 0.3, cab)
    rr = _R(1121)
    for k in range(6):
        px = 10 + k * 7
        top = 12 + int(rr.randint(0, 14))
        t = int(rr.randint(-3, 4))
        p = sp.poly([(px, 42), (px + 9, 42), (px + 9 + t, top), (px + t, top)])
        sp.paint(p, 0.7 + 0.14 * (k % 2) + (sp.nz(3, 1130 + k) - 0.5) * 0.12 + sp.bev(p, 1, 0.12), PAPER)
        sp.solid(sp.rect(px + t, top, px + 9 + t, top + 1), "#6a604a")
        for ly in range(top + 5, 40, 5):
            sp.solid(sp.rect(px + 2 + t, ly, px + 7 + t, ly + 1) & p & sp.dither(0.6), "#8a96b0")
    front = sp.rect(6, 50, 56, 60)
    sp.paint(front, 0.7 + sp.bev(front, 1, 0.16), cab)
    sp.solid(sp.rect(26, 54, 38, 57), "#12161a")
    for (sx, sy, w) in ((14, 58, 14), (36, 60, 12)):
        p = sp.poly([(sx, sy - 2), (sx + w, sy - 2), (sx + w + 2, sy + 12), (sx + 2, sy + 14)])
        sp.paint(p, 0.85 + (sp.nz(3, 1140 + sx) - 0.5) * 0.1, PAPER)
        sp.solid(sp.rect(sx + 2, sy + 4, sx + w - 2, sy + 5) & p, "#8a96b0")
    # a few more sheets down on the floor
    for (sx, sy) in ((60, 118), (12, 120)):
        sp.paint(sp.poly([(sx, sy), (sx + 14, sy - 2), (sx + 18, sy + 4), (sx + 3, sy + 6)]), 0.85, PAPER)
    sp.dust(sp.rect(0, 108, 128, 128) & (sp.a > 0), 112, 128, 1150, 0.5)
    sp.edge(0.4)
    return sp.rgba()


def thing_flak_burst():
    """A soft flak burst: a white-yellow core in an orange fireball with a ragged edge, a brown-black smoke puff round and below it, a spray of tiny sparks. Straight colour with a soft alpha, for additive blending."""
    n = 128
    x, y = np.meshgrid(np.arange(n, dtype=np.float32), np.arange(n, dtype=np.float32))
    cx, cy = 64.0, 62.0
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    f = noise(n, 22, 1201, 3)
    g = noise(n, 11, 1202, 3)
    # smoke: ragged and lumpy, heavier below
    sm = np.clip(1.0 - d / (50.0 * (0.62 + 0.7 * f) + 4 * (y - cy) / n * 4), 0, 1)
    smoke_a = np.clip(sm * 2.6, 0, 1) * 0.85
    rgb = np.zeros((n, n, 3), np.float32)
    smoke_pal = ramp("#120e0c", "#2a221c", "#4a3c30", "#6e5a46")
    ps = quantise(np.clip(0.2 + 0.5 * g * sm + 0.2 * (1 - (x + y) / 256.0), 0, 1), smoke_pal).astype(np.float32)
    rgb = ps
    alpha = smoke_a.copy()
    # fire
    fire = np.clip(1.0 - d / (30.0 * (0.7 + 0.6 * g)), 0, 1)
    fire_pal = ramp("#5a1404", "#b4300a", "#f0780f", "#ffbc3c", "#fff2b0", "#ffffff")
    pf = quantise(np.clip(fire ** 0.8 * 1.05 + (g - 0.5) * 0.1, 0, 1), fire_pal).astype(np.float32)
    fa = np.clip(fire * 2.4, 0, 1)
    rgb = rgb * (1 - fa[..., None]) + pf * fa[..., None]
    alpha = np.maximum(alpha, fa)
    # sparks
    rr = np.random.RandomState(1203)
    out_rgb = rgb.copy()
    for k in range(34):
        a = rr.rand() * 6.2832
        r = 26 + rr.rand() * 36
        px, py = int(cx + r * np.cos(a)), int(cy + r * np.sin(a))
        if 1 <= px < n - 1 and 1 <= py < n - 1:
            col = np.array([255, 220, 120] if k % 3 else [255, 150, 50], np.float32)
            out_rgb[py, px] = col
            alpha[py, px] = 1.0
            if k % 4 == 0:
                tx, ty = int(cx + (r - 3) * np.cos(a)), int(cy + (r - 3) * np.sin(a))
                out_rgb[ty, tx] = col * 0.8
                alpha[ty, tx] = max(alpha[ty, tx], 0.8)
    # keep the very edge empty
    alpha = np.where(alpha < 0.06, 0, alpha)
    return np.dstack([np.clip(out_rgb, 0, 255).astype(np.uint8), (alpha * 255 + 0.5).astype(np.uint8)])


def thing_fuel_drums():
    """Three olive fuel drums (two in front, one behind) with a hand pump on the middle one, orange dust at their feet."""
    sp = S()

    def drum(x0, x1, ytop, ybot, seed):
        cx, rx, ry = (x0 + x1) / 2, (x1 - x0) / 2, 6
        body = sp.rect(x0, ytop + ry, x1, ybot - ry)
        top = sp.ell(cx, ytop + ry, rx, ry)
        bot = sp.ell(cx, ybot - ry, rx, ry)
        m = body | top | bot
        sh = sp.hs(x0, x1, 0.55, 0.6) + (sp.nz(4, seed) - 0.5) * 0.18
        sp.paint(m, sh + 0.04 * (((sp.x + sp.y) % 5) < 1), OLIVE)
        h = ybot - ytop
        for fy in (ytop + ry + h * 0.22, ytop + ry + h * 0.5, ybot - ry - h * 0.12):
            hoop = sp.ell(cx, fy, rx, ry) & body.__or__(sp.ell(cx, fy, rx, ry)) & (sp.y > fy - 1) & (sp.y < fy + 3)
            sp.paint(hoop & m, sh + 0.14, OLIVE)
            sp.solid(sp.ell(cx, fy + 3, rx, ry) & ~sp.ell(cx, fy + 1.5, rx, ry) & (sp.y > fy + 2.5) & m & (sp.y < fy + 5), "#0e1008")
        sp.paint(top & (sp.y <= ytop + ry + 1), 0.7 + 0.2 * ((sp.x - cx) < 0) + (sp.nz(3, seed + 1) - 0.5) * 0.2, OLIVE)
        sp.solid(top & ~sp.ell(cx, ytop + ry + 1, rx - 1.5, ry - 1.5), "#1c200f")
        sp.paint(sp.ell(cx - rx * 0.4, ytop + ry, 3, 2), 0.3, STEEL)
        sp.paint(sp.ell(cx + rx * 0.35, ytop + ry, 2, 1.5), 0.6, STEEL)
        rs = (sp.nz(5, seed + 2) > 0.66) & m & (sp.y > ytop + ry + 3)
        sp.paint(rs, 0.25 + 0.5 * sp.nz(2, seed + 3), RUST)
        wn = (sp.nz(6, seed + 4) > 0.72) & m & sp.dither(0.6) & (sp.y > ytop + ry + 3)
        sp.paint(wn, 0.45 + 0.4 * sp.nz(2, seed + 5), ORANGE)
        return m

    drum(24, 62, 24, 94, 1301)
    d1 = drum(4, 42, 56, 126, 1311)
    d2 = drum(44, 82, 56, 126, 1321)
    # the hand pump on the middle drum
    steel = STEEL
    sp.paint(sp.rect(60, 36, 66, 62), sp.hs(60, 66, 0.55, 0.8), steel)
    body = sp.rect(52, 18, 74, 38)
    sp.paint(body, 0.55 + sp.bev(body, 1, 0.2) + (sp.nz(4, 1331) - 0.5) * 0.15, ramp("#1a2028", "#2c3844", "#44525e", "#6a7882", "#92a0a6"))
    sp.paint(sp.rect(56, 12, 70, 18), 0.6, steel)
    sp.paint(sp.line([(70, 24), (100, 10)], 3), 0.6, steel)
    sp.paint(sp.ell(103, 9, 4, 4), 0.55, ramp("#3a0a08", "#8a1c16", "#c43a28"))
    sp.paint(sp.line([(52, 30), (44, 38), (44, 50)], 3), 0.5, steel)
    hose = sp.line([(74, 32), (92, 40), (100, 62), (96, 90), (92, 112), (100, 122)], 4)
    sp.paint(hose, 0.35 + 0.35 * (sp.x < 94), ramp("#0a0c08", "#1a2014", "#2c3820", "#445030"))
    sp.paint(sp.rect(96, 118, 112, 124) & sp.dither(0.5), 0.5, ORANGE)
    # a jerrycan-less ground: dust at the feet
    sp.dust((sp.a > 0), 96, 128, 1341, 0.85)
    sp.edge(0.45)
    return sp.rgba()


def thing_hangar_front():
    """The front of a corrugated store hangar: a low gable, olive-drab iron rusting at the bolts, a big sliding door ajar on the dark with crates inside."""
    sp = S()
    wall = sp.rect(6, 34, 122, 128)
    gable = sp.poly([(4, 36), (64, 6), (124, 36)])
    prof = np.cos((sp.x % 6) / 6.0 * 6.2832 + 0.6)
    ws = 0.5 + 0.3 * prof + (sp.nz(6, 1401) - 0.5) * 0.2
    sp.paint(wall | gable, ws + 0.06 * (sp.y < 40), OLIVE)
    sp.paint(sp.line([(4, 36), (64, 6), (124, 36)], 4), 0.8 - 0.2 * (sp.x > 64), ramp("#2a2a26", "#4a4a44", "#6e6e66", "#8e8e84"))
    sp.paint(sp.rect(4, 34, 124, 38), 0.45 + 0.3 * (sp.y < 36), STEEL)
    ru = (sp.nz(8, 1402) > 0.62) & (wall | gable) & sp.dither(0.7)
    sp.paint(ru, 0.2 + 0.6 * sp.nz(2, 1403), RUST)
    for sx in range(14, 120, 22):
        L = int(_R(1404 + sx).randint(8, 30))
        sp.paint(sp.rect(sx, 40, sx + 2, 40 + L) & wall, 0.25 + 0.4 * sp.nz(2, sx), RUST)
    sp.paint(sp.rect(56, 17, 72, 26), 0.12, STEEL)
    sp.solid(sp.rect(56, 17, 72, 18) | sp.rect(56, 17, 57, 26), "#6a6a62")
    # the doorway: dark inside, crates
    door = sp.rect(34, 52, 96, 128)
    sp.paint(door, 0.06 + 0.1 * np.clip((sp.y - 60) / 60.0, 0, 1) + (sp.nz(5, 1405) - 0.5) * 0.05, ramp("#040404", "#0c0c0a", "#181612", "#2a251c"))
    for (cx0, cy0, cx1, cy1, s) in ((40, 98, 66, 128, 1410), (58, 84, 82, 112, 1420), (74, 104, 94, 128, 1430)):
        cr = sp.rect(cx0, cy0, cx1, cy1) & door
        row = ((sp.y - cy0) // 6).astype(int)
        t = _R(s).rand(10).astype(np.float32)[np.clip(row, 0, 9)]
        sp.paint(cr, 0.28 + 0.12 * (t - 0.5) - 0.18 * (((sp.y - cy0) % 6) < 1) + sp.bev(cr, 1, 0.1) + (sp.nz(4, s) - 0.5) * 0.1, WOOD)
    sp.paint(sp.rect(88, 56, 92, 60), 0.9, WARM) if False else None
    # the sliding door ajar: it covers the left half
    leaf = sp.rect(30, 50, 68, 128)
    lp = np.cos((sp.x % 6) / 6.0 * 6.2832 + 0.6)
    sp.paint(leaf, 0.46 + 0.3 * lp + (sp.nz(6, 1440) - 0.5) * 0.2 + sp.bev(leaf, 1, 0.14), OLIVE)
    sp.paint(leaf & (sp.nz(5, 1441) > 0.6) & sp.dither(0.7), 0.3 + 0.5 * sp.nz(2, 1442), RUST)
    sp.paint(sp.rect(30, 60, 68, 63) | sp.rect(30, 110, 68, 113), 0.4 + 0.2 * (sp.y < 62), STEEL)
    sp.paint(sp.rect(62, 82, 66, 98), 0.7 + 0.2 * (sp.x < 64), STEEL)
    sp.solid(sp.rect(68, 52, 69, 128), "#050505")
    sp.paint(sp.rect(68, 52, 72, 128) & door & sp.dither(0.6), 0.1, STEEL)
    # the rail above and rollers
    sp.paint(sp.rect(24, 44, 104, 49), 0.5 + 0.3 * (sp.y < 46), STEEL)
    for rx in (36, 56, 78):
        sp.paint(sp.ell(rx, 51, 3, 3), 0.6, STEEL)
    sp.paint(sp.rect(94, 52, 98, 128), 0.5 + 0.3 * (sp.x < 96), STEEL)
    sp.dust(sp.rect(0, 100, 128, 128) & (sp.a > 0), 104, 128, 1450, 1.2)
    sp.edge(0.4)
    return sp.rgba()


def thing_instrument_panel():
    """An aircraft instrument panel: round dials with green-lit ticks and needles, a compass rose, indicator lamps and a row of toggle switches on a green-black panel."""
    sp = S()
    panel = sp.rect(2, 6, 126, 122)
    sp.paint(panel, 0.4 + (sp.nz(6, 1501) - 0.5) * 0.18 + sp.bev(panel, 2, 0.14) + (_R(1502).rand(sp.h, sp.w) - 0.5) * 0.05, GBLACK)
    for (sx, sy) in ((7, 11), (121, 11), (7, 117), (121, 117)):
        sp.paint(sp.ell(sx, sy, 2.4, 2.4), 0.7 - 0.3 * (sp.x > sx), STEEL)
        sp.solid(sp.rect(sx - 1, sy, sx + 1, sy + 1), "#1a2020")
    green = "#7af0a0"

    def dial(cx, cy, r, ang, seed, ticks=9):
        sp.paint(sp.ell(cx, cy, r + 3, r + 3), sp.hs(cx - r - 3, cx + r + 3, 0.55, 0.7) * 0.9, STEEL)
        sp.paint(sp.ell(cx, cy, r, r), 0.12 - 0.05 * (sp.x > cx), ramp("#020604", "#06100a", "#0c1c12"))
        for k in range(ticks):
            a = np.radians(135 + k * 270 / (ticks - 1))
            px, py = cx + (r - 2.5) * np.cos(a), cy + (r - 2.5) * np.sin(a)
            sp.solid(sp.ell(px, py, 1.1, 1.1), green if k % 3 == 0 else "#3aa862")
        a = np.radians(ang)
        sp.solid(sp.line([(cx, cy), (cx + (r - 3) * np.cos(a), cy + (r - 3) * np.sin(a))], 1), "#c8ffd8")
        sp.solid(sp.ell(cx, cy, 2, 2), "#10281a")
        sp.solid(sp.rect(cx, cy, cx + 1, cy + 1), green)
        sp.solid(sp.line([(cx - r * 0.6, cy - r * 0.55), (cx - r * 0.3, cy - r * 0.8)], 1) & sp.dither(0.5), "#4a6a58")  # glass glint

    dial(30, 32, 16, 200, 1, 9)
    dial(64, 32, 16, 300, 2, 11)
    dial(98, 32, 16, 20, 3, 9)
    dial(20, 76, 11, 250, 4, 7)
    dial(108, 76, 11, 330, 5, 7)
    # compass in the middle
    cx, cy = 64, 78
    sp.paint(sp.ell(cx, cy, 20, 20), sp.hs(cx - 20, cx + 20, 0.55, 0.7) * 0.9, STEEL)
    sp.paint(sp.ell(cx, cy, 16, 16), 0.1, ramp("#020604", "#06100a", "#0c1c12"))
    sp.solid(sp.ell(cx, cy, 16, 16) & ~sp.ell(cx, cy, 15, 15) & (sp.x < cx), "#2a5a3a")
    for k in range(16):
        a = np.radians(k * 22.5)
        L0 = 12 if k % 4 else 10
        sp.solid(sp.line([(cx + L0 * np.cos(a), cy + L0 * np.sin(a)), (cx + 14.5 * np.cos(a), cy + 14.5 * np.sin(a))], 1), green if k % 4 == 0 else "#3aa862")
    sp.solid(sp.poly([(cx, cy - 9), (cx + 3, cy), (cx, cy + 9), (cx - 3, cy)]), "#2a6a42")
    sp.solid(sp.poly([(cx, cy - 9), (cx + 3, cy), (cx - 3, cy)]), "#d8442a")
    sp.solid(sp.ell(cx, cy, 2, 2), "#c8ffd8")
    # lamps
    for (lx, ly, col, glow) in ((42, 62, "#ff5a3a", "#8a1c10"), (86, 62, "#ffc23a", "#8a6410"), (64, 53, "#7af0a0", "#1a6a3a")):
        sp.solid(sp.ell(lx, ly, 4.4, 4.4), "#05080a")
        sp.solid(sp.ell(lx, ly, 3, 3), col)
        sp.solid(sp.rect(lx - 2, ly - 2, lx - 1, ly - 1), "#fff4dc")
        sp.solid(sp.ell(lx, ly, 7, 7) & ~sp.ell(lx, ly, 4.4, 4.4) & sp.dither(0.25), glow)
    # switches
    for k in range(8):
        sx = 14 + k * 14
        sp.solid(sp.rect(sx - 3, 106, sx + 3, 116), "#0a1010")
        up = k % 3 != 1
        lv = sp.line([(sx, 111), (sx, 104 if up else 118)], 2)
        sp.paint(lv & sp.rect(0, 98, 128, 121), 0.8, STEEL)
        sp.solid(sp.ell(sx, 104 if up else 117, 2, 2), "#c8c4b0")
    sp.solid(sp.rect(10, 97, 118, 98), "#05090a")
    sp.solid(sp.rect(10, 98, 118, 99) & sp.dither(0.4), "#2f4d38")
    # a lamp-green wash on the panel's lower left (dithered)
    sp.paint(panel & sp.dither(np.clip(0.3 - (sp.x + (128 - sp.y)) / 260.0, 0, 1)) & (sp.rgb.sum(2) < 90), 0.5, LAMP)
    sp.edge(0.4)
    return sp.rgba()


def thing_jeep():
    """An open dusty utility jeep, olive and unmarked, seen from the side: folded windscreen, seats, a spare wheel on the tail, dust on the tyres and sills."""
    sp = S()
    body = sp.poly([(8, 94), (10, 80), (44, 77), (50, 73), (102, 73), (114, 80), (118, 100), (10, 104)])
    sp.paint(body, 0.58 + sp.vs(72, 104, 0, 0.5) * 0.6 + (sp.nz(6, 1601) - 0.5) * 0.14 + sp.bev(body, 1, 0.14), OLIVE)
    sp.paint(sp.rect(10, 80, 46, 83), 0.9, OLIVE)
    sp.solid(sp.line([(46, 77), (46, 96)], 1), "#10140a")
    sp.paint(sp.rect(52, 82, 100, 98), 0.45, OLIVE)
    sp.solid(sp.rect(52, 82, 100, 83), "#8a9a5a")
    sp.solid(sp.rect(54, 88, 62, 91), "#10140a")
    sp.solid(sp.rect(6, 82, 12, 100), "#10140a")
    for gy in range(84, 100, 3):
        sp.solid(sp.rect(7, gy, 11, gy + 1), "#6a6a60")
    sp.paint(sp.ell(13, 80, 3.4, 3.4), 0.8, ramp("#3a3a30", "#8a8a78", "#dcdcc4", "#fffcec"))
    sp.paint(sp.rect(4, 102, 22, 106), 0.6, STEEL)
    seat = ramp("#1c1a10", "#3a3822", "#58563a", "#7a7a52")
    sp.paint(sp.rect(66, 58, 80, 80), 0.4 + (sp.nz(4, 1602) - 0.5) * 0.2 + 0.2 * (sp.x < 70), seat)
    sp.paint(sp.rect(88, 56, 100, 80), 0.4 + (sp.nz(4, 1603) - 0.5) * 0.2 + 0.2 * (sp.x < 92), seat)
    sp.solid(sp.line([(62, 72), (56, 58)], 2), "#1a1c14")
    sp.solid(sp.ell(55, 56, 5, 2) & ~sp.ell(55, 56, 3, 1), "#12140c")
    sp.paint(sp.poly([(48, 73), (58, 48), (62, 48), (56, 73)]), 0.5, STEEL)
    sp.paint(sp.poly([(52, 71), (59, 51), (61, 51), (57, 71)]), 0.8 - (sp.y - 51) * 0.01, GLASS)
    sp.paint(sp.line([(58, 48), (80, 48)], 2), 0.55, STEEL)
    sp.paint(sp.ell(118, 88, 6, 13), sp.hs(112, 124, 0.4, 0.6), ramp("#0a0a08", "#181816", "#2a2a26", "#404038"))
    sp.paint(sp.ell(118, 88, 3, 6.5), 0.6 + 0.3 * (sp.x < 118), STEEL)
    rub = ramp("#080807", "#141412", "#222220", "#383832")
    for wx in (36, 94):
        sp.solid(sp.ell(wx, 104, 18, 18) & (sp.y < 106), "#050505")
        t = sp.ell(wx, 110, 15, 15)
        sp.paint(t, 0.4 + sp.hs(wx - 15, wx + 15, 0, 0.5) * 0.5 + (sp.nz(3, 1610 + wx) - 0.5) * 0.15, rub)
        tread = t & ~sp.ell(wx, 110, 12.5, 12.5)
        sp.paint(tread & (((sp.x + sp.y) % 4) < 2), 0.8, rub)
        sp.paint(sp.ell(wx, 110, 7, 7), sp.hs(wx - 7, wx + 7, 0.5, 0.7), OLIVE)
        sp.paint(sp.ell(wx, 110, 2.6, 2.6), 0.7, STEEL)
        sp.dust(t, 114, 126, 1620 + wx, 0.9)
    sp.dust(body & (sp.y > 90), 90, 104, 1630, 0.9)
    sp.paint(body & (sp.nz(4, 1631) > 0.66) & sp.dither(0.4) & (sp.y < 90), 0.7, ORANGE)
    sp.edge(0.45)
    return sp.rgba()


def thing_kitchen_hatch():
    """A serving hatch cut in a plaster wall: a shutter propped open on a stick above it, a warm kitchen lamp and a pot glimpsed inside, steam, a ladle on a nail, a bucket on the floor."""
    sp = S()
    wall = sp.rect(4, 6, 124, 126)
    sp.paint(wall, 0.6 + (sp.nz(6, 1701) - 0.5) * 0.3 + sp.bev(wall, 2, 0.1), PLASTER)
    st = (sp.nz(4, 1702) > 0.7) & wall & sp.dither(0.5)
    sp.paint(st, 0.4, ramp("#6a5224", "#8a6c30", "#aa8a44"))
    hole = sp.rect(24, 38, 104, 92)
    sp.paint(hole, 0.1 + 0.1 * (sp.nz(5, 1703)), ramp("#0a0604", "#1a0e08", "#2c1a0c", "#44280e"))
    sp.paint(sp.rect(24, 38, 104, 42) | sp.rect(24, 38, 28, 92), 0.1, ramp("#06040a", "#120e0a"))
    # the lamp
    lamp_glow = np.sqrt((sp.x - 80) ** 2 + (sp.y - 56) ** 2)
    sp.paint(hole & sp.dither(np.clip(1.4 - lamp_glow / 26.0, 0, 1)), 0.8 - lamp_glow / 40.0, WARM)
    sp.solid(sp.line([(80, 42), (80, 50)], 1), "#10100c")
    sp.solid(sp.poly([(72, 58), (88, 58), (84, 50), (76, 50)]), "#2a3a2a")
    sp.solid(sp.ell(80, 60, 3.4, 3.4), "#fffbe0")
    sp.solid(sp.ell(80, 60, 5.5, 5.5) & ~sp.ell(80, 60, 3.4, 3.4) & sp.dither(0.5), "#f6c860")
    # a shelf with a pot, and hanging pans
    sp.paint(sp.rect(28, 76, 66, 79), 0.5, DARKWOOD)
    pot = sp.rect(34, 64, 58, 76) | sp.ell(46, 64, 12, 2)
    sp.paint(pot, 0.35 + sp.hs(34, 58, 0, 0.5) * 0.5, ramp("#101012", "#262a2e", "#40464c", "#6a7278"))
    sp.solid(sp.rect(30, 66, 34, 68) | sp.rect(58, 66, 62, 68), "#1a1c20")
    # steam
    rr = _R(1704)
    for k in range(7):
        sx, sy = 40 + k * 9 + int(rr.randint(-3, 4)), 60 - (k * 11) % 24
        puff = sp.ell(sx, sy, 5 + k % 3, 4)
        sp.paint(puff & sp.dither(0.55) & hole, 0.8, ramp("#8a8478", "#b8b2a2", "#e0dccc"))
    sp.paint(sp.ell(48, 40, 14, 10) & ~hole & sp.dither(0.5) & wall, 0.9, ramp("#d8d0a8", "#ece4c0", "#fbf6e0"))
    # counter sill
    sill = sp.rect(18, 92, 110, 100)
    sp.paint(sill, 0.55 + 0.25 * (sp.y < 94) + (sp.nz(5, 1705) - 0.5) * 0.2, DARKWOOD)
    sp.solid(sp.rect(18, 99, 110, 100), "#0a0604")
    # the shutter, propped up on a stick
    sh = sp.poly([(26, 38), (102, 38), (118, 12), (12, 12)])
    pl = ((sp.y - 12) // 6).astype(int)
    tn = _R(1706).rand(6).astype(np.float32)[np.clip(pl, 0, 5)]
    sp.paint(sh, 0.4 + 0.18 * (tn - 0.5) + (sp.nz(5, 1707) - 0.5) * 0.16 - 0.25 * (((sp.y - 12) % 6) < 1) + sp.bev(sh, 1, 0.12), WOOD)
    sp.solid(sp.line([(26, 38), (102, 38)], 2), "#12100a")
    sp.paint(sp.rect(106, 24, 110, 92), sp.hs(106, 110, 0.5, 0.6), DARKWOOD)
    sp.paint(sp.rect(104, 20, 112, 26), 0.5, STEEL)
    # a ladle on a nail
    sp.solid(sp.ell(14, 28, 1.6, 1.6), "#3a3a3a")
    sp.paint(sp.line([(14, 30), (14, 70)], 2), 0.6, STEEL)
    sp.paint(sp.ell(14, 76, 6, 5) & (sp.y > 72), sp.hs(8, 20, 0.5, 0.7), STEEL)
    sp.solid(sp.ell(14, 73, 6, 1.6) & False, "#0a0a0a")
    # the bucket on the floor
    bk = sp.poly([(92, 104), (118, 104), (114, 126), (96, 126)])
    sp.paint(bk, sp.hs(92, 118, 0.55, 0.7) + (sp.nz(4, 1708) - 0.5) * 0.15, STEEL)
    sp.paint(sp.rect(92, 104, 118, 107), 0.8, STEEL)
    sp.solid(sp.rect(94, 104, 116, 105), "#0a0c0e")
    sp.solid(sp.line([(94, 104), (105, 90), (116, 104)], 1), "#2a2e32")
    sp.paint(sp.rect(94, 114, 116, 116), 0.3, STEEL)
    sp.dust(sp.rect(0, 112, 128, 128) & (sp.a > 0), 116, 128, 1709, 0.5)
    sp.edge(0.4)
    return sp.rgba()


DRAW = {k: v for k, v in sorted(globals().items()) if callable(v) and k.startswith(("ceil_", "floor_", "wall_", "sky_", "thing_")) and v.__module__ == __name__}
