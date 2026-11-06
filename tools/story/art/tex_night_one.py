"""Night One's procedural pixel textures and billboard props (docs/STORY_25D_ART_DIRECTION.md 1 and 2.D): a 90s warehouse rave in warm amber and magenta.

`build()` returns the opaque tiles {id: (rgb uint8 (n, n, 3), metres per repeat)} that `tiles.procedural` writes after the Godot bake (an id the bake also
makes is replaced: brick, panels, speakers, bar, toilets; a new id is added: the corridor, the cubicle walls, the chill-out banner, the ceilings).
The billboard props (`thing_*`, RGBA with a cut-out edge) cannot go through `pixeltex.save` (RGB), so `build()` writes them itself with `save_rgba`; their ids
are listed in `tiles.NIGHT_ONE` so the manifest picks them up. Everything is drawn in numpy at tile size, quantised to small palette ramps with 8 x 8 ordered
dithering; every random value comes from a seeded generator, so the same code gives the same bytes.
"""
from __future__ import annotations

import os

import numpy as np

from . import lib
from . import pixeltex as px

N = 128
OUT = os.path.join(lib.ROOT, "assets", "story", "night_one", "textures")

# ---- palettes (dark to light) --------------------------------------------------------------------------------------------------------------------------
BRICK = px.ramp("#110a10", "#22111a", "#371b20", "#4e2724", "#66362a", "#7f4830", "#96603a")
MORTAR = px.ramp("#120d13", "#221a20", "#33292d", "#443739")
RUST = px.ramp("#2e130c", "#55240e", "#7c3c14", "#a2581c", "#c47a2c")
SOOT = px.ramp("#08060a", "#140f14", "#1e1820")
STEEL = px.ramp("#0e0c12", "#1c1922", "#2c2834", "#423b48", "#5c525e", "#7e6e72", "#a88a6e")
DECK = px.ramp("#08070b", "#110f16", "#1a1720", "#25202c", "#322a38")
CONC = px.ramp("#0c0a0e", "#17141a", "#221e25", "#2e2930", "#3b353b", "#4a4248", "#5a5054")
WOOD = px.ramp("#120a08", "#1f110c", "#2e1a10", "#3f2414", "#52301a", "#683e20", "#80502a")
CARPET = px.ramp("#0e050b", "#1a0812", "#270c1b", "#351224", "#44182c")
AMBER = px.ramp("#3a1e0e", "#6a3c14", "#9c621e", "#d08e2c", "#f4bc4a")
MAGENTA = px.ramp("#2e0a22", "#5c1244", "#8e1c66", "#c42a8a", "#f04aaa")
TEAL = px.ramp("#0a2028", "#0f3a44", "#16585e", "#24807e")
PLATE = px.ramp("#0e0c12", "#18151d", "#231f29", "#302a36", "#403846", "#554a58", "#6e6068")
CAB = px.ramp("#08070a", "#110f14", "#1a171e", "#24202a", "#2f2a36")
CONE = px.ramp("#040306", "#0c0a10", "#16131a", "#221e28", "#322c38", "#4a4252", "#6a5e6c")
TILE = px.ramp("#36433f", "#4d5c55", "#66766c", "#829084", "#9eab9c", "#bcc6b4", "#d6dcc8")
GROUT = px.ramp("#141a16", "#232a24", "#343b33", "#474d43")
GRIMEP = px.ramp("#1a1a10", "#2a2818", "#3c3820", "#4e4628")
FLOORD = px.ramp("#0e1214", "#171d20", "#20282b", "#2a3336")
FLOORL = px.ramp("#3c4442", "#525a56", "#6a726a", "#848a80", "#9ca096")
PAINT = px.ramp("#121a1a", "#1b2524", "#25302e", "#303c38", "#3d4a44", "#4c5850")
LAM = px.ramp("#1a080e", "#2a0e16", "#3a141e", "#4c1c28", "#5e2632", "#72323e")
CEILP = px.ramp("#262824", "#363932", "#484b42", "#5c5e54", "#706f64", "#848070")
PURPLE = px.ramp("#0e0816", "#180e24", "#241632", "#301e40", "#3e284e", "#4c325c")
GLASS = px.ramp("#0a0c14", "#141a26", "#1e2a38", "#2c3e4c", "#40586a", "#5e7c8c")
NIGHT = px.ramp("#05060f", "#0a0c1c", "#121428", "#1c1a34", "#2a1e3a", "#3c2440")
WHITE = px.ramp("#5a5c58", "#7c7e78", "#9ea09a", "#c2c2bc", "#e4e2da")
SILVER = px.ramp("#2a2a32", "#4a4a54", "#707078", "#9a9aa2", "#c8c8ce")
VELOUR = px.ramp("#14060a", "#260a12", "#3a101a", "#4e1822", "#62222c", "#7a3036")
GREEN = px.ramp("#04200e", "#0a3a1a", "#12602a", "#1e8a3c", "#3cc060")
# the redraw at 100 to 128 texels a metre (docs/art/STYLE_GUIDE.md 4 and 7): brick toward the guide's mauve brick #634e60, steel rusted like Rave.png's trusses
BRICKM = px.ramp("#16080f", "#24111a", "#341a24", "#45242c", "#563034", "#683e3c", "#7c5046", "#8e6450")
SOOTB = px.ramp("#0c070c", "#160d14", "#21141b", "#2d1b22", "#3a2429", "#4a2f31")
TRUSS = px.ramp("#110b0f", "#21151a", "#33201f", "#4a2e24", "#64402a", "#805632", "#9c6e3e", "#ba8a52")
MESH = px.ramp("#050407", "#0c0a10", "#16131b", "#221e28", "#2f2a36", "#40394a")
PAINTG = px.ramp("#0f1614", "#17211e", "#202d29", "#2b3a34", "#374840", "#45574d")
UVDYE = [px.ramp("#2a0820", "#5c1244", "#9a1e72", "#d02e94", "#f45ab8"), px.ramp("#2a1406", "#6a3810", "#a8621a", "#dc9028", "#f6c25a"),
         px.ramp("#061c22", "#0c3a44", "#14646a", "#20908e", "#4ac4b8"), px.ramp("#140a2a", "#2c1658", "#4c2a90", "#7448c4", "#9c74e8")]


# ---- helpers ----------------------------------------------------------------------------------------------------------------------------------------------

def grid(h: int, w: int | None = None):
    w = h if w is None else w
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return x, y


def bayer(shape) -> np.ndarray:
    return px.BAYER8[np.arange(shape[0])[:, None] % 8, np.arange(shape[1])[None, :] % 8]


def dmask(f: np.ndarray) -> np.ndarray:
    """A dithered mask from a 0..1 coverage field (0.5 gives every other pixel)."""
    return (np.asarray(f, np.float32) + bayer(np.shape(f))) > 0.5


def q(shade, pal, dither: float = 1.0, shape=None) -> np.ndarray:
    shade = np.asarray(shade, np.float32)
    if shape is not None:
        shade = np.broadcast_to(shade, shape).astype(np.float32)
    return px.quantise(shade, pal, dither)


def put(base: np.ndarray, mask, layer: np.ndarray) -> np.ndarray:
    out = base.copy()
    m = np.asarray(mask, bool)
    out[m] = layer[m]
    return out


def rect(n, x0, y0, x1, y1, w=None):
    x, y = grid(n, w)
    return (x >= x0) & (x < x1) & (y >= y0) & (y < y1)


def ell(n, cx, cy, rx, ry, w=None):
    x, y = grid(n, w)
    return ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0


def seg(n, x0, y0, x1, y1, wd=1.0, w=None):
    x, y = grid(n, w)
    dx, dy = x1 - x0, y1 - y0
    t = np.clip(((x + 0.5 - x0) * dx + (y + 0.5 - y0) * dy) / max(dx * dx + dy * dy, 1e-6), 0, 1)
    return np.hypot(x + 0.5 - (x0 + t * dx), y + 0.5 - (y0 + t * dy)) <= wd * 0.5


def sag(n, y0, depth, wd=1.2, x0=0.0, x1=None, phase=0.0):
    """A cable hanging between x0 and x1 (sinus sag), mask."""
    x, y = grid(n)
    x1 = n if x1 is None else x1
    u = np.clip((x - x0) / max(x1 - x0, 1), 0, 1)
    yy = y0 + depth * np.sin(np.pi * u) + phase
    return (np.abs(y - yy) < wd * 0.5 + 0.1) & (x >= x0) & (x < x1)


FONT = {
    "A": "010101111101101", "B": "110101110101110", "C": "011100100100011", "D": "110101101101110", "E": "111100110100111",
    "F": "111100110100100", "G": "011100101101011", "H": "101101111101101", "I": "111010010010111", "J": "001001001101010",
    "K": "101101110101101", "L": "100100100100111", "M": "101111101101101", "N": "101111111101101", "O": "010101101101010",
    "P": "110101110100100", "R": "110101110101101", "S": "011100010001110", "T": "111010010010010", "U": "101101101101111",
    "V": "101101101101010", "W": "101101101111101", "Y": "101101010010010", "X": "101101010101101", "2": "110001010100111",
    "3": "110001010001110", "4": "101101111001001", "9": "111101111001111", "+": "000010111010000", "!": "010010010000010",
    " ": "000000000000000", "<": "001010100010001", "?": "110001010000010",
}


def text_mask(n, s: str, x: int, y: int, scale: int = 1, slant: float = 0.0, w=None) -> np.ndarray:
    """A 3 x 5 pixel lettering mask (a scrawl when slanted)."""
    m = np.zeros((n, n if w is None else w), bool)
    cx = x
    for ch in s:
        g = FONT.get(ch.upper(), FONT[" "])
        for i, bit in enumerate(g):
            if bit == "1":
                r, c = divmod(i, 3)
                yy = y + r * scale
                xx = cx + c * scale + int(round(slant * (4 - r)))
                m[max(yy, 0):max(yy + scale, 0), max(xx, 0):max(xx + scale, 0)] = True
        cx += 4 * scale
    return m


def heart(n, cx, cy, r, w=None):
    x, y = grid(n, w)
    u, v = (x + 0.5 - cx) / r, -(y + 0.5 - cy) / r
    return (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0


def wrap_mask(m: np.ndarray, dx: int, dy: int) -> np.ndarray:
    return np.roll(np.roll(m, dy, 0), dx, 1)


class Sprite:
    """An RGBA billboard canvas: paint palette-quantised shapes, unpainted pixels stay transparent. Square (n) or w x h."""

    def __init__(self, n: int = N, h: int | None = None):
        self.n = n  # the width
        self.h = n if h is None else h
        self.rgb = np.zeros((self.h, n, 3), np.uint8)
        self.a = np.zeros((self.h, n), np.uint8)

    def paint(self, mask, pal, shade) -> None:
        m = np.asarray(mask, bool)
        layer = q(shade, pal, shape=(self.h, self.n))
        self.rgb[m] = layer[m]
        self.a[m] = 255

    def col(self, mask, hexc: str) -> None:
        m = np.asarray(mask, bool)
        self.rgb[m] = (px.hexc(hexc) * 255 + 0.5).astype(np.uint8)
        self.a[m] = 255

    def edge(self, k: float = 0.72) -> None:
        """The style guide's edge (section 6): the outermost ring of opaque pixels one step darker than their own colour, no outline colour."""
        a = self.a > 0
        rim = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
        rim[0, :] |= a[0, :]
        rim[-1, :] |= a[-1, :]
        rim[:, 0] |= a[:, 0]
        rim[:, -1] |= a[:, -1]
        self.rgb[rim] = (self.rgb[rim].astype(np.float32) * k).astype(np.uint8)

    def rgba(self) -> np.ndarray:
        return np.dstack([self.rgb, self.a])


def grid2(w: int, h: int):
    """x, y of a w x h canvas (h rows)."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    return x, y


def noise2(w: int, h: int, scale: float, seed: int, octaves: int = 3) -> np.ndarray:
    """Value noise on a w x h canvas (cropped from a square field; sprites need not tile)."""
    n = max(w, h)
    return px.noise(n, scale, seed, octaves)[:h, :w]


def box(w, h, x0, y0, x1, y1):
    x, y = grid2(w, h)
    return (x >= x0) & (x < x1) & (y >= y0) & (y < y1)


def oval(w, h, cx, cy, rx, ry):
    x, y = grid2(w, h)
    return ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0


def line2(w, h, x0, y0, x1, y1, wd=1.0):
    x, y = grid2(w, h)
    dx, dy = x1 - x0, y1 - y0
    t = np.clip(((x + 0.5 - x0) * dx + (y + 0.5 - y0) * dy) / max(dx * dx + dy * dy, 1e-6), 0, 1)
    return np.hypot(x + 0.5 - (x0 + t * dx), y + 0.5 - (y0 + t * dy)) <= wd * 0.5


def droop(w, h, x0, x1, y0, depth, wd=1.2):
    """A cable hanging between (x0, y0) and (x1, y0), sagging `depth` pixels in the middle."""
    x, y = grid2(w, h)
    u = np.clip((x - x0) / max(x1 - x0, 1), 0, 1)
    yy = y0 + depth * np.sin(np.pi * u)
    return (np.abs(y - yy) < wd * 0.5 + 0.1) & (x >= x0) & (x < x1)


def save_rgba(path: str, rgba: np.ndarray) -> None:
    from PIL import Image
    Image.fromarray(rgba, "RGBA").save(path, optimize=False, compress_level=9)


def stretch_rows(m: np.ndarray, k: int) -> np.ndarray:
    return np.repeat(m, k, axis=0)


# ---- walls -----------------------------------------------------------------------------------------------------------------------------------------------
# Every surface is a 128 px tile (check_assets: tiles are square, at most 128 px) over 1.0 to 1.3 m, so 98 to 128 texels a metre (STYLE_GUIDE 7): one texel is about one
# internal pixel at 3 m, the grain of the baked people. A tile that small repeats often, so no tile carries a single strong landmark (a poster, a fixing, a
# blotch): the wear is many small marks, the low-frequency grime is weak, and the per-brick and per-board tones do the variation.

def brick_field(n=N, rows=14, cols=4, seed=11, pal=BRICKM, grime=0.5, rust=0.25, burnt=0.12, mortar_lift=0.0) -> np.ndarray:
    """Old warehouse brick at 1 m a tile (14 courses of 71 mm, 4 headers of 25 cm): each brick its own tone, sand grain, a lit top edge and a shadowed foot
    (light from the upper left), chipped arrises, burnt clinkers, soot and lime bloom, mortar raked back and dirty."""
    x, y = px.grid(n)
    sh, mort = px.bricks(n, rows=rows, cols=cols, seed=seed, wear=0.55)
    bh, bw = n / rows, n / cols
    r = np.floor(y / bh)
    off = (r % 2) * bw * 0.5
    lx = ((x + off) % n) % bw
    ly = y - r * bh
    c = np.floor(((x + off) % n) / bw)
    rng = np.random.RandomState(seed + 20)
    burn = (rng.rand(rows, cols + 1) < burnt)[r.astype(int) % rows, c.astype(int) % (cols + 1)]
    sh = sh + 0.07 * (lx < 2.5) - 0.08 * (lx > bw - 2.5)  # the header's left arris catches the light, its right one is in shadow
    sh = sh + (px.speckle(n, 0.10, seed + 21) - px.speckle(n, 0.10, seed + 22)) * 0.16  # sand grain
    g = px.grime(n, seed + 1, grime) * 0.7 + 0.3 * np.clip((px.noise(n, 6, seed + 9) - 0.55) * 3, 0, 1) * grime
    sh = sh - 0.3 * g - 0.22 * burn
    out = q(sh, pal)
    mo = q(0.42 + mortar_lift - 0.45 * g + (px.noise(n, 4, seed + 3) - 0.5) * 0.45 + 0.25 * (ly < 0.6), MORTAR)
    out = put(out, mort > 0.5, mo)
    if rust > 0:  # rust and iron bleeding from old fixings, along the bed joints
        rr = px.rust(n, seed + 2, rust)
        out = put(out, dmask(rr * 0.75) & (mort < 0.5), q(0.25 + px.noise(n, 5, seed + 4) * 0.5, RUST))
    bloom = dmask(np.clip((px.noise(n, 10, seed + 6, 3) - 0.62) * 2.5, 0, 1)) & (mort < 0.5)  # lime bloom (efflorescence)
    out = put(out, bloom & dmask(np.full((n, n), 0.35)), q(np.full((n, n), 0.8), MORTAR))
    out = put(out, px.speckle(n, 0.003, seed + 5) > 0.5, q(np.full((n, n), 0.95), MORTAR))
    return out


def wall_brick() -> np.ndarray:
    """Tunnel, entrance and old walls (1.0 m): mauve-brown brick, sooty, rust bleeding along the courses, a few burnt headers."""
    return brick_field(N, rows=14, cols=4, seed=11, grime=0.55, rust=0.35, burnt=0.14)


def wall_panel() -> np.ndarray:
    """The main floor's walls (1.28 m): brick painted black once and blistered by twenty years of smoke machines; the paint flakes off in patches to the
    brick under it, soot runs down from the beams, a thin conduit clipped along the wall."""
    n = N
    x, y = px.grid(n)
    base = brick_field(n, rows=18, cols=4, seed=21, pal=BRICKM, grime=0.7, rust=0.15, burnt=0.15)
    sh, mort = px.bricks(n, rows=18, cols=4, seed=21, wear=0.5)
    flake = 0.6 * px.noise(n, 7, 23, 3) + 0.4 * px.noise(n, 3, 27, 2)
    painted = flake < 0.5  # the black paint left on
    blist = (np.abs(flake - 0.5) < 0.02)  # the paint's lifted edge catches the light
    paint = q(0.68 + 0.35 * (sh - 0.5) - 0.25 * mort - 0.35 * px.grime(n, 24, 0.7) + (px.speckle(n, 0.08, 25) - 0.5) * 0.2, SOOTB)
    out = put(base, painted, paint)
    out = put(out, blist & (mort < 0.5), q(np.full((n, n), 0.85), SOOTB))
    return out


def wall_speaker() -> np.ndarray:
    """A speaker cabinet (1.0 m a tile, so a wall is a stack of them): black-painted ply worn to the wood on the arrises, steel corners, a horn over a
    perforated steel grille with the 15-inch cone dim behind the mesh, a strip of gaffer with the channel scrawled on it."""
    n = N
    x, y = px.grid(n)
    nz = px.noise(n, 8, 31)
    out = q(0.55 + (nz - 0.5) * 0.3 - 0.2 * px.grime(n, 32, 0.5, drip=False), CAB)
    gap = (x < 2) | (y < 2)  # the joint between two cabinets
    out = put(out, gap, q(np.full((n, n), 0.0), CAB))
    arris = ((x >= 2) & (x < 4)) | ((y >= 2) & (y < 4))
    wear = dmask(np.clip((px.noise(n, 3, 33) - 0.35) * 2, 0, 1))
    out = put(out, arris & wear, q(0.45 + 0.4 * px.noise(n, 2, 34), WOOD))
    out = put(out, ((x >= n - 3) | (y >= n - 3)) & ~gap, q(np.full((n, n), 0.08), CAB))
    for cx in (2, n - 12):  # steel corners with a rivet
        for cy in (2, n - 12):
            m = rect(n, cx, cy, cx + 10, cy + 10)
            out = put(out, m, q(0.55 + 0.3 * ((x - cx) + (y - cy) < 6) - 0.2 * ((x - cx) + (y - cy) > 14), SILVER))
            out = put(out, (np.abs(x - cx - 5) < 1.2) & (np.abs(y - cy - 5) < 1.2), q(np.full((n, n), 0.15), SILVER))
    # the horn: a rectangular flare, its walls lit from the upper left, the throat black
    hx0, hx1, hy0, hy1 = 16, 112, 12, 46
    horn = rect(n, hx0, hy0, hx1, hy1)
    u = (x - (hx0 + hx1) / 2) / ((hx1 - hx0) / 2)
    v = (y - (hy0 + hy1) / 2) / ((hy1 - hy0) / 2)
    d = np.maximum(np.abs(u), np.abs(v))
    wall = 0.08 + 0.55 * d ** 2.2 + 0.15 * ((u < 0) & (np.abs(u) > np.abs(v))) + 0.12 * ((v < 0) & (np.abs(v) >= np.abs(u))) - 0.12 * ((v > 0) & (np.abs(v) >= np.abs(u)))
    out = put(out, horn, q(wall, CONE))
    out = put(out, horn & (d < 0.16), q(np.full((n, n), 0.0), CONE))
    out = put(out, horn & ((np.abs(u - v * 2.8) < 0.035) | (np.abs(u + v * 2.8) < 0.035)) & (d > 0.18), q(np.full((n, n), 0.45), CONE))  # the flare's folds
    out = put(out, rect(n, hx0 - 2, hy0 - 2, hx1 + 2, hy0) | rect(n, hx0 - 2, hy0, hx0, hy1), q(np.full((n, n), 0.62), CONE))
    # the grille: perforated steel over the cone
    gx0, gx1, gy0, gy1 = 10, 118, 54, 120
    gr = rect(n, gx0, gy0, gx1, gy1)
    cx, cy = (gx0 + gx1) / 2, (gy0 + gy1) / 2 + 1
    rr = np.hypot(x - cx, (y - cy) * 1.0)
    cone = 0.15 + 0.4 * np.clip(rr / 30.0, 0, 1) * (rr < 31) + 0.35 * (np.abs(rr - 31) < 1.5) - 0.1 * (rr > 33) + 0.35 * (rr < 6) + 0.15 * ((x - cx + y - cy) < -12) * (rr < 30)
    mesh = q(0.3 + 0.55 * cone, MESH)
    holes = ((x % 3) == 1) & ((y % 3) == 1)
    out = put(out, gr, mesh)
    out = put(out, gr & holes, q(0.05 + 0.5 * cone, CONE))
    out = put(out, gr & dmask(px.grime(n, 35, 0.6, drip=False) * 0.7), q(np.full((n, n), 0.15), MESH))  # dust in the mesh
    out = put(out, (rect(n, gx0 - 2, gy0 - 2, gx1 + 2, gy1 + 2) & ~gr), q(0.5 + 0.3 * ((y < gy0) | (x < gx0)), MESH))
    # gaffer strip with the channel scrawled on it
    tape = rect(n, 40, 48, 76, 53)
    out = put(out, tape, q(0.62 + 0.15 * (y == 48), WHITE))
    out = put(out, tape & text_mask(n, "SUB2", 43, 48), q(np.full((n, n), 0.05), CAB))
    return out


def trim() -> np.ndarray:
    """The truss over the stage openings (1.0 m): a rusted box-truss girder at the top of the tile (the strip is 0.4 to 1 m deep), round chords, zig-zag lacing,
    bolted plates at the nodes, a cable tied along the lower chord, the dark roof behind."""
    n = N
    x, y = px.grid(n)
    out = q(0.25 + (px.noise(n, 16, 41) - 0.5) * 0.15 + 0.06 * np.sin(x * 2 * np.pi / 12), PLATE)
    t0, t1, b0, b1 = 6, 13, 44, 51  # the chords

    def chord(y0, y1):
        u = (y - y0) / (y1 - y0)
        return rect(n, 0, y0, n, y1), 0.85 - 0.75 * u + 0.15 * (u < 0.2) + (px.noise(n, 5, int(y0)) - 0.5) * 0.25

    lace = np.zeros((n, n), bool)
    for k in range(4):  # 32 px bays, diagonals alternating
        xa = k * 32
        if k % 2 == 0:
            lace |= seg(n, xa, t1, xa + 32, b0, 3.0)
        else:
            lace |= seg(n, xa, b0, xa + 32, t1, 3.0)
    lace |= (np.abs(x % 64 - 0.5) < 1.6) & (y >= t1) & (y < b0)
    lsh = 0.5 + 0.25 * (np.roll(lace, 1, 1) == False) - 0.2 * (np.roll(lace, -1, 1) == False)  # noqa: E712
    out = put(out, lace, q(lsh + (px.noise(n, 4, 42) - 0.5) * 0.3, TRUSS))
    for y0, y1 in ((t0, t1), (b0, b1)):
        m, s = chord(y0, y1)
        out = put(out, m, q(s, TRUSS))
    node = ((x % 32 < 4) | (x % 32 > 28)) & (((y >= t0 - 1) & (y < t1 + 1)) | ((y >= b0 - 1) & (y < b1 + 1)))
    out = put(out, node, q(0.5 + 0.3 * (x % 32 > 28), STEEL))
    out = put(out, node & ((x % 32 == 1) & ((y == t0 + 2) | (y == b0 + 2))), q(np.full((n, n), 0.95), STEEL))
    rr = px.rust(n, 43, 0.6)
    out = put(out, dmask(rr * 0.8) & (lace | (y < b1)) & (y >= t0), q(0.2 + 0.4 * px.noise(n, 3, 44), RUST))
    out = put(out, sag(n, b1 + 1, 7, 1.3, 0, 64) | sag(n, b1 + 1, 4, 1.3, 64, n), q(np.full((n, n), 0.05), CAB))  # a cable tied along the bottom chord
    out = put(out, rect(n, 0, 70, n, 72) & dmask(np.full((n, n), 0.4)), q(np.full((n, n), 0.45), DECK))  # the roof's purlin far behind
    return out


def bar_front() -> np.ndarray:
    """The back bar (1.2 m a tile, three glass shelves to the tile): a smoky mirror behind, bottles of every shape with labels and a lit edge, an amber LED
    strip under each shelf, a row of optics on some, glasses stacked upside down on others."""
    n = N
    x, y = px.grid(n)
    rng = np.random.RandomState(51)
    mir = 0.25 + 0.2 * np.sin((x + y * 0.8) * 0.07) ** 8 + (px.noise(n, 16, 53) - 0.5) * 0.35 - 0.2 * px.grime(n, 52, 0.6, drip=False)
    out = q(mir, px.ramp("#0e080e", "#1c1018", "#2e1a1a", "#4a2a1c", "#704220", "#9a6230"))
    bottle_pals = [px.ramp("#06180c", "#0e3a1c", "#1c6030", "#3a9050", "#8ad0a0"), px.ramp("#2a1004", "#5a2a08", "#94500e", "#c8801e", "#f2c060"),
                   px.ramp("#1e2228", "#4a5660", "#7a8a94", "#b0c0c8", "#e8f0f4"), px.ramp("#08142e", "#14306a", "#2a58b0", "#5a8ae0", "#a8c8ff"),
                   px.ramp("#2a060c", "#5a1018", "#901c28", "#c83a40", "#f08a80"), px.ramp("#1a1406", "#3e3210", "#6a5a1c", "#a08a30", "#d8c060")]
    shelves = (42, 85, 127)
    for si, sy in enumerate(shelves):
        top = sy - 42
        xx = 1 + int(rng.randint(0, 3))
        kind = si % 3
        while xx < n - 3:
            if kind == 2 and rng.rand() < 0.5:  # pint glasses stacked upside down
                w = 5
                h = int(rng.randint(8, 11))
                g = rect(n, xx, sy - h, xx + w, sy)
                out = put(out, g, q(0.35 + 0.35 * (x == xx) + 0.25 * (y == sy - h), GLASS))
                xx += w + 1
                continue
            shape = int(rng.randint(0, 4))
            w = [4, 5, 7, 4][shape]
            h = [26, 20, 16, 30][shape] - int(rng.randint(0, 6))
            h = min(h, sy - top - 4)
            pal = bottle_pals[int(rng.randint(0, len(bottle_pals)))]
            body = rect(n, xx, sy - int(h * 0.68), xx + w, sy)
            sh_ = [0.3, 0.45, 0.4, 0.35][shape]
            neck_w = 2 if w < 6 else 3
            nx = xx + (w - neck_w) // 2
            neck = rect(n, nx, sy - h, nx + neck_w, sy - int(h * 0.68))
            shoulder = rect(n, xx + 1, sy - int(h * 0.68) - 2, xx + w - 1, sy - int(h * 0.68))
            m = body | neck | shoulder
            lit = sh_ + 0.45 * (x == xx + 1) - 0.18 * (x == xx + w - 1) + 0.1 * (y > sy - 4)
            out = put(out, m, q(lit, pal))
            out = put(out, rect(n, nx, sy - h - 1, nx + neck_w, sy - h + 1), q(np.full((n, n), 0.75), SILVER if rng.rand() < 0.6 else AMBER))
            if rng.rand() < 0.8:  # a label
                ly0 = sy - int(h * 0.5)
                lab = rect(n, xx, ly0, xx + w, ly0 + max(3, int(h * 0.22)))
                lp = [WHITE, AMBER, px.ramp("#3a0a10", "#c0303a", "#f08a80"), WHITE][int(rng.randint(0, 4))]
                out = put(out, lab, q(0.55 + 0.3 * (x == xx), lp))
                out = put(out, lab & (y == ly0 + 1) & (x % 2 == 0) & (x > xx) & (x < xx + w - 1), q(np.full((n, n), 0.05), CAB))
            xx += w + int(rng.randint(1, 3))
        if si == 0:  # optics: bottles upside down in brackets at the top shelf's front
            for ox in range(6, n - 6, 21):
                out = put(out, rect(n, ox, top + 3, ox + 6, top + 15), q(0.35 + 0.4 * (x == ox + 1), bottle_pals[(ox // 21) % 6]))
                out = put(out, rect(n, ox + 1, top + 15, ox + 5, top + 19), q(0.7 + 0.2 * (x == ox + 1), SILVER))
        out = put(out, (y >= sy - 1) & (y <= sy) if sy < n - 1 else (y >= n - 2), q(0.7 + 0.25 * (y == sy - 1), GLASS))
        led = (y == (sy + 1) % n)
        out = put(out, led, q(0.75 + 0.25 * ((x % 4) < 2), AMBER))
        glow = (y > (sy + 1) % n) & (y < (sy + 6) % n) if sy < n - 1 else (y >= 0) & (y < 4)
        out = put(out, glow & dmask(np.clip(1 - ((y - (sy + 1) % n) % n) / 6.0, 0, 1) * 0.6), q(np.full((n, n), 0.45), AMBER))
    out = put(out, (x < 2) | (x >= n - 1), q(np.full((n, n), 0.2), WOOD))  # the uprights of the shelving bay
    return out


def wall_bar() -> np.ndarray:
    """The bar's other walls (1.2 m): brick fly-posted the way a promoter does it, the same flyer in rows, paste wrinkles, torn down to older layers in
    places, tags over them."""
    n = N
    x, y = px.grid(n)
    out = brick_field(n, rows=17, cols=4, seed=61, grime=0.45, rust=0.15, burnt=0.08)
    rng = np.random.RandomState(62)
    flyers = [("RAVE", MAGENTA, 2, 4, 28, 38), ("ACID", AMBER, 33, 2, 28, 36), ("PLUR", TEAL, 64, 6, 26, 34), ("4AM", WHITE, 94, 3, 30, 40),
              ("XTC", MAGENTA, 6, 66, 26, 34), ("DJ", AMBER, 37, 62, 24, 30), ("RAVE", TEAL, 66, 68, 28, 36), ("ACID", MAGENTA, 98, 70, 26, 34)]
    for word, pal, fx, fy, w, h in flyers:
        m = rect(n, fx, fy, fx + w, fy + h)
        tear = (px.noise(n, 3, fx + fy * 7) > 0.66) & ((np.abs(x - fx) < 4) | (np.abs(y - fy - h) < 5) | (np.abs(x - fx - w) < 3))
        m &= ~tear
        wrinkle = 0.08 * (np.abs(((x - fx) + (y - fy) * 0.3) % 11 - 5) < 1)
        sh = 0.12 + 0.3 * (y - fy) / h - wrinkle - 0.3 * px.grime(n, fx + 5, 0.6) + (px.speckle(n, 0.1, fx + 3) - 0.5) * 0.15
        out = put(out, m, q(sh, pal))
        out = put(out, m & text_mask(n, word, fx + 3, fy + 4), q(np.full((n, n), 0.0), CAB))
        circ = m & (np.abs(np.hypot(x - fx - w * 0.5, y - fy - h * 0.58) - 6) < 1.6)
        out = put(out, circ, q(np.full((n, n), 0.6), pal))
        lines = m & (y > fy + h - 8) & (y % 2 == 0) & (x > fx + 3) & (x < fx + w - 4)
        out = put(out, lines, q(np.full((n, n), 0.05), pal))
        under = tear & rect(n, fx, fy, fx + w, fy + h) & (px.noise(n, 2, fx + 9) > 0.5)  # an older poster's paper in the torn corners
        out = put(out, under, q(np.full((n, n), 0.35), WHITE))
    tags = np.zeros((n, n), bool)
    for _ in range(3):
        x0, y0 = rng.rand() * (n - 40), 30 + rng.rand() * 60
        pts = [(x0, y0)]
        a = rng.rand() * 6.28
        for _ in range(9):
            a += (rng.rand() - 0.5) * 3.0
            pts.append((pts[-1][0] + abs(np.cos(a)) * 4 + 0.8, pts[-1][1] + np.sin(a) * 4))
        for (a0, b0), (a1, b1) in zip(pts, pts[1:]):
            tags |= seg(n, a0, b0, a1, b1, 1.4)
    out = put(out, tags, q(np.full((n, n), 0.02), CAB))
    return out


def wall_door() -> np.ndarray:
    """The street end of the tunnel (2.0 m, the opening's own wall segment; brick to either side): steel doors folded back in a brick reveal, a wet night
    street under one sodium lamp, terraces with a few lit windows, a puddle carrying the lamp."""
    n = N
    x, y = px.grid(n)
    out = brick_field(n, rows=28, cols=8, seed=71, grime=0.7, rust=0.4)
    hole = rect(n, 12, 10, 116, n)
    sky = 0.05 + 0.6 * np.clip((y - 10) / 60.0, 0, 1) ** 1.6
    street = q(sky, NIGHT)
    street = put(street, (px.speckle(n, 0.01, 72) > 0.5) & (y < 34), q(np.full((n, n), 0.75), WHITE))
    roof = 48 + 6 * ((x // 11) % 3) - 4 * ((x // 23) % 2)
    bld = (y > roof) & (y < 96)
    chim = ((x % 23) > 17) & ((x % 23) < 20) & (y > roof - 5) & (y <= roof)
    street = put(street, bld | chim, q(0.05 + 0.08 * ((x // 11) % 2), NIGHT))
    win = bld & ((x % 7) < 3) & ((y % 9) > 2) & ((y % 9) < 6) & (px.noise(n, 3, 73) > 0.58)
    street = put(street, win, q(0.55 + 0.4 * px.noise(n, 2, 74), AMBER))
    road = y >= 96
    refl = 0.1 + 0.55 * np.clip(1 - np.abs(x - 72) / 14.0, 0, 1) * ((np.sin(y * 1.9) * 0.5 + 0.5) ** 2) * ((y - 96) / 32.0) + 0.06 * (px.noise(n, 6, 75) - 0.5)
    street = put(street, road, q(refl, px.ramp("#08060c", "#16121a", "#2c1e18", "#5a3816", "#a86a26", "#e8a848")))
    kerb = (y >= 96) & (y < 98)
    street = put(street, kerb, q(np.full((n, n), 0.35), CONC))
    post = (np.abs(x - 72) < 1) & (y > 40) & (y < 98)
    street = put(street, post, q(0.15 + 0.2 * (x < 72), STEEL))
    street = put(street, rect(n, 69, 38, 76, 41), q(np.full((n, n), 0.3), STEEL))
    lamp = ell(n, 72.5, 42, 3.5, 2.2)
    halo = (np.hypot(x - 72, (y - 43) * 1.3) < 16) & ~lamp & ~post
    street = put(street, halo & dmask(np.clip(1 - np.hypot(x - 72, (y - 43) * 1.3) / 16.0, 0, 1) * 0.55), q(np.full((n, n), 0.5), AMBER))
    street = put(street, lamp, q(np.full((n, n), 1.0), AMBER))
    out = put(out, hole, street)
    for d0, d1, s in ((12, 24, 1), (104, 116, -1)):  # the doors folded back against the reveals, the push bars catching the street light
        m = rect(n, d0, 10, d1, n)
        out = put(out, m, q(0.3 + 0.15 * (x == d0) + (px.noise(n, 5, d0) - 0.5) * 0.3 - 0.25 * px.grime(n, d0 + 1, 0.6), px.ramp("#121816", "#1e2a24", "#2c3c34", "#3e5046", "#566a5c")))
        out = put(out, rect(n, d0 + 2, 70, d1 - 2, 73), q(np.full((n, n), 0.75), SILVER))
        out = put(out, rect(n, d0 + 3, 26, d1 - 3, 44), q(0.25 + 0.15 * ((x + y) % 4 == 0), GLASS))
    out = put(out, rect(n, 10, 7, 118, 10) | rect(n, 10, 7, 12, n) | rect(n, 116, 7, 118, n), q(0.45 + 0.3 * ((x < 11) | (y < 8)), STEEL))
    return out


def wall_corridor() -> np.ndarray:
    """The long corridor to the toilets (1.2 m): brick painted institutional green long ago, grimy to shoulder height, the paint peeling to the brick in
    patches, scuffed by the queue, a sticker or two."""
    n = N
    x, y = px.grid(n)
    base = brick_field(n, rows=17, cols=4, seed=81, grime=0.5, rust=0.2, burnt=0.05)
    sh, mort = px.bricks(n, rows=17, cols=4, seed=81, wear=0.4)
    g = px.grime(n, 82, 0.8)
    paint = q(0.62 + 0.25 * (sh - 0.5) - 0.3 * mort - 0.45 * g + (px.noise(n, 10, 83) - 0.5) * 0.25, PAINTG)
    peel = px.noise(n, 12, 84, 4)
    out = put(base, peel < 0.62, paint)
    out = put(out, (np.abs(peel - 0.62) < 0.02) & (mort < 0.5), q(np.full((n, n), 0.95), PAINTG))
    scuff = dmask(np.clip((px.noise(n, 5, 85) - 0.6) * 2.5, 0, 1)) & (peel < 0.62)
    out = put(out, scuff, q(np.full((n, n), 0.12), PAINTG))
    rng = np.random.RandomState(86)
    for i in range(2):
        sx, sy = int(rng.randint(8, n - 16)), int(rng.randint(10, n - 16))
        pal = [MAGENTA, AMBER][i]
        out = put(out, rect(n, sx, sy, sx + 9, sy + 6), q(0.5 + 0.35 * (y == sy), pal))
    return out


def toilet_tile() -> np.ndarray:
    """Toilet walls (1.0 m): eight glazed tiles a metre gone yellow, black grout, grime running down, a cracked and a chipped tile."""
    n = N
    x, y = px.grid(n)
    sh, gr = px.tiles(n, count=8, grout=1, seed=91, gloss=0.35)
    g = px.grime(n, 92, 0.75)
    out = q(sh - 0.45 * g, TILE)
    out = put(out, gr > 0.5, q(0.6 - 0.7 * g, GROUT))
    out = put(out, dmask(g * 0.75) & (gr < 0.5), q(0.5 + 0.5 * px.noise(n, 4, 93), GRIMEP))
    out = put(out, seg(n, 34, 18, 44, 28, 1.0) | seg(n, 44, 28, 41, 30, 1.0), q(np.full((n, n), 0.1), GROUT))
    out = put(out, rect(n, 98, 66, 106, 74) & dmask(np.full((n, n), 0.7)), q(0.3 + 0.4 * px.noise(n, 3, 94), MORTAR))
    return out


def toilet_floor() -> np.ndarray:
    """Toilet floor (1.0 m): black and grey tiles of 12.5 cm, dirt in the grout, wet patches catching the tube light."""
    n = N
    x, y = px.grid(n)
    s = 16
    chk = (((x // s) + (y // s)) % 2) == 1
    dirt = px.noise(n, 20, 101, 4)
    lt = q(0.55 + (px.noise(n, 6, 102) - 0.5) * 0.3 - 0.5 * np.clip(dirt - 0.5, 0, 1), FLOORL)
    dk = q(0.5 + (px.noise(n, 6, 103) - 0.5) * 0.4, FLOORD)
    out = np.where(chk[..., None], dk, lt)
    gr = ((x % s) < 1) | ((y % s) < 1)
    out = put(out, gr, q(np.full((n, n), 0.4), GROUT))
    out = put(out, dmask(np.clip(dirt - 0.45, 0, 1) * 2.0), q(0.4 + 0.6 * px.noise(n, 3, 104), GRIMEP))
    wet = (px.noise(n, 26, 105, 3) > 0.62) & (px.speckle(n, 0.08, 106) > 0.5)
    out = put(out, wet, q(np.full((n, n), 1.0), FLOORL))
    return out


def ceil_wc() -> np.ndarray:
    """Toilet and corridor ceilings (1.2 m): a nicotine-stained drop ceiling, water rings, a sagging tile."""
    n = N
    x, y = px.grid(n)
    sh = 0.55 + (px.noise(n, 4, 111) - 0.5) * 0.35 - 0.3 * (px.speckle(n, 0.12, 112))
    stain = px.noise(n, 30, 113, 4)
    sh = sh - 0.5 * np.clip((stain - 0.5) * 3, 0, 1) - 0.4 * (np.abs(stain - 0.62) < 0.012)
    out = q(sh, CEILP)
    bar = ((x % 64) < 2) | ((y % 64) < 2)
    out = put(out, bar, q(0.85 - 0.5 * ((x % 64) == 1) - 0.5 * ((y % 64) == 1), STEEL))
    out = put(out, rect(n, 66, 66, 128, 128) & dmask(np.clip((y - 66) / 80.0, 0, 1)), q(np.full((n, n), 0.15), CEILP))
    return out


def partition(n=N, gap_top=0, seed=121, post=True, words=(), dense=1.0) -> np.ndarray:
    """A cubicle partition panel in chipped burgundy laminate, scratched and written on."""
    x, y = px.grid(n)
    rng = np.random.RandomState(seed)
    out = q(0.5 + (px.noise(n, 12, seed) - 0.5) * 0.35 - 0.3 * px.grime(n, seed + 1, 0.6), LAM)
    chips = px.noise(n, 3, seed + 2) > 0.8
    out = put(out, chips, q(np.full((n, n), 0.6), MORTAR))
    sc = np.zeros((n, n), bool)
    for _ in range(int(26 * dense)):  # keys dragged across the laminate
        x0, y0 = rng.rand() * n, gap_top + 8 + rng.rand() * (n - gap_top - 24)
        a = rng.rand() * np.pi
        L = 6 + rng.rand() * 18
        sc |= seg(n, x0, y0, x0 + np.cos(a) * L, y0 + np.sin(a) * L * 0.4, 0.8)
    out = put(out, sc, q(np.full((n, n), 0.95), LAM))
    tags = np.zeros((n, n), bool)
    for _ in range(int(6 * dense)):  # marker tag scrawls
        x0, y0 = rng.rand() * (n - 30), gap_top + 14 + rng.rand() * (n - gap_top - 50)
        a, pts = rng.rand() * 6.28, [(x0, y0)]
        for i in range(int(rng.randint(5, 12))):  # a pen that loops and doubles back: a tag, not a wave
            a += (rng.rand() - 0.5) * 3.2
            L = 2 + rng.rand() * 5
            pts.append((pts[-1][0] + abs(np.cos(a)) * L * 0.9 + 0.6, pts[-1][1] + np.sin(a) * L))
        wd = 1.0 + rng.rand() * 0.8
        for (a0, b0), (a1, b1) in zip(pts, pts[1:]):
            tags |= seg(n, a0, b0, a1, b1, wd)
    out = put(out, tags, q(np.full((n, n), 0.0), CAB))
    for word, wx, wy, pal, sl in words:
        out = put(out, text_mask(n, word, wx, wy, 1, sl), q(np.full((n, n), 0.9), pal))
    hx, hy = int(rng.randint(10, n - 20)), int(gap_top + rng.randint(30, 60))
    out = put(out, heart(n, hx, hy, 4.5) & ~heart(n, hx, hy, 3.2), q(np.full((n, n), 0.8), MAGENTA))
    for _ in range(int(4 * dense)):  # stickers
        sx, sy = int(rng.randint(4, n - 12)), int(gap_top + rng.randint(16, n - gap_top - 30))
        pal = [MAGENTA, AMBER, TEAL, WHITE][int(rng.randint(0, 4))]
        out = put(out, rect(n, sx, sy, sx + 7, sy + 5), q(0.5 + 0.4 * (y == sy), pal))
    if post:
        out = put(out, x < 4, q(0.55 + 0.35 * (x == 1) - 0.4 * (x == 3), SILVER))
    return out


def cubicle_door() -> np.ndarray:
    """The cubicle fronts (2.6 m, floor to ceiling, so the gaps fall where they are): a dark gap over the partitions, laminate scrawled on, the gap above the floor."""
    n = N
    x, y = px.grid(n)
    out = partition(n, gap_top=10, seed=121, words=[("PLUR", 18, 40, AMBER, 0.3), ("K+J", 74, 60, WHITE, -0.4), ("ACID", 50, 92, TEAL, 0.5)])
    out = put(out, (x >= 4) & (np.abs(x - 96) < 1.5) & (np.abs(y - 66) < 5), q(np.full((n, n), 0.8), SILVER))
    out = put(out, y < 10, q(0.1 + 0.1 * (y > 7), CAB))
    out = put(out, y >= 120, q(np.full((n, n), 0.05), CAB))
    out = put(out, (y >= 10) & (y < 12), q(np.full((n, n), 0.7), SILVER))
    return out


def cubicle_wall() -> np.ndarray:
    """Inside a cubicle (1.2 m a repeat, so the writing is hand-sized up close): every inch of laminate written on, a coat hook."""
    n = N
    x, y = px.grid(n)
    out = partition(n, gap_top=0, seed=131, post=False, dense=1.8,
                    words=[("RAVE ON", 8, 22, MAGENTA, 0.4), ("DJ ? 4 EVA", 40, 48, WHITE, -0.3), ("WHERE AM I", 14, 76, AMBER, 0.6),
                           ("<3", 100, 30, MAGENTA, 0.0), ("SORTED", 70, 96, TEAL, -0.5)])
    out = put(out, rect(n, 92, 52, 95, 58) | rect(n, 92, 56, 98, 58), q(np.full((n, n), 0.75), SILVER))
    return out


def wall_chill() -> np.ndarray:
    """The chill-out room (1.3 m): every wall draped in UV tie-dye cloth, hung in loose vertical folds; the dye bands swirl and bleed into one another,
    the folds shade them (light from the upper left), the cloth's weave shows as a fine dither."""
    n = N
    x, y = px.grid(n)
    # a tileable swirl: two periodic fields bent by noise
    a = 2 * np.pi * x / n
    b = 2 * np.pi * y / n
    warp = (px.noise(n, 32, 141, 3) - 0.5) * 5.0
    f = np.sin(a * 2 + b * 1 + warp) + 0.8 * np.sin(a * 1 - b * 2 + warp * 0.7) + 0.5 * np.sin(a * 3 + b * 3 - warp)
    band = np.floor((f + 2.3) / 4.6 * 8).astype(int) % 4
    t = ((f + 2.3) / 4.6 * 8) % 1.0
    fold = np.sin(2 * np.pi * x / n * 3 + 0.6 * np.sin(2 * np.pi * y / n)) * 0.5 + 0.5  # three folds a tile
    sh = 0.2 + 0.32 * fold + 0.18 * (np.abs(t - 0.5) < 0.2) - 0.12 * (t < 0.12) + (px.speckle(n, 0.12, 142) - 0.5) * 0.12
    out = np.zeros((n, n, 3), np.uint8)
    for i, pal in enumerate(UVDYE):
        out = put(out, band == i, q(sh, pal))
    bleed = (t < 0.1) | (t > 0.9)  # the dye's dark bleed line between bands
    out = put(out, bleed & dmask(np.full((n, n), 0.55)), q(sh * 0.4, PURPLE))
    deep = fold < 0.07  # the inside of a fold
    out = put(out, deep, q(np.full((n, n), 0.15), PURPLE))
    return out


# ---- floors and ceilings ---------------------------------------------------------------------------------------------------------------------------------

def floor_dark() -> np.ndarray:
    """Warehouse concrete (1.28 m): a power-floated slab polished by feet, hairline cracks, spilt drinks drying sticky, flattened gum, fag ends."""
    n = N
    x, y = px.grid(n)
    sh = 0.5 + (px.noise(n, 24, 151, 4) - 0.5) * 0.35 + (px.noise(n, 4, 152) - 0.5) * 0.25 + (px.speckle(n, 0.12, 156) - 0.5) * 0.18
    blot = px.noise(n, 18, 153, 4)
    sh = sh - 0.3 * np.clip((blot - 0.6) * 4, 0, 1)
    out = q(sh, CONC)
    crack = (np.abs(px.noise(n, 22, 154, 3) - 0.5) < 0.007)
    out = put(out, crack, q(np.full((n, n), 0.0), CONC))
    out = put(out, np.roll(crack, 1, 0) & ~crack, q(np.full((n, n), 0.75), CONC))
    gum = px.speckle(n, 0.0025, 155) > 0.5
    out = put(out, gum | np.roll(gum, 1, 1), q(np.full((n, n), 0.92), CONC))
    rng = np.random.RandomState(157)
    for _ in range(1):  # a fag end
        cx, cy = int(rng.randint(2, n - 6)), int(rng.randint(2, n - 3))
        out = put(out, rect(n, cx, cy, cx + 4, cy + 1), q(np.full((n, n), 0.9), WHITE))
        out = put(out, rect(n, cx + 4, cy, cx + 5, cy + 1), q(np.full((n, n), 0.6), AMBER))
    return out


def floor_boards() -> np.ndarray:
    """The bar's floor (1.0 m): eight boards of 12.5 cm, dark with old varnish, sticky with beer, worn pale along the grain."""
    n = N
    x, y = px.grid(n)
    sh, joint = px.planks(n, count=8, seed=161)
    g = px.grime(n, 162, 0.55, drip=False)
    worn = np.clip((px.noise(n, 20, 164, 3) - 0.55) * 2.5, 0, 1)
    out = q(sh - 0.3 * g + 0.2 * worn + (px.speckle(n, 0.06, 165) - 0.5) * 0.1, WOOD)
    out = put(out, joint > 0.5, q(np.full((n, n), 0.02), WOOD))
    out = put(out, dmask(np.clip(px.noise(n, 14, 163, 3) - 0.62, 0, 1) * 3), q(np.full((n, n), 0.12), WOOD))
    nails = ((x % 64) == 5) & ((y % 16) == 8) | ((x % 64) == 37) & ((y % 16) == 8)
    out = put(out, nails, q(np.full((n, n), 0.1), STEEL))
    return out


def floor_carpet() -> np.ndarray:
    """Club carpet (1.0 m): maroon with amber diamonds, teal squiggles and magenta dots every 25 cm, burnt, flattened and worn through in patches."""
    n = N
    x, y = px.grid(n)
    wear = np.clip((px.noise(n, 22, 171, 4) - 0.5) * 2.5, 0, 1)
    out = q(0.5 + (px.noise(n, 3, 172) - 0.5) * 0.4 + 0.3 * wear + (px.speckle(n, 0.15, 174) - 0.5) * 0.15, CARPET)
    lx, ly = (x % 32) - 15.5, (y % 32) - 15.5
    d = np.abs(lx) + np.abs(ly)
    dia = (d > 9) & (d < 12)
    sq = (np.abs(((y + 16) % 32) - 16 - 4 * np.sin(((x + 16) % 32) * 0.4)) < 1.2) & (np.abs(((x + 16) % 32) - 16) < 12)
    dot = d < 3
    keep = ~dmask(wear * 0.8)
    out = put(out, dia & keep, q(0.55 + 0.2 * (lx < 0), AMBER))
    out = put(out, sq & keep & ~dia, q(np.full((n, n), 0.6), TEAL))
    out = put(out, dot & keep, q(np.full((n, n), 0.7), MAGENTA))
    burns = px.speckle(n, 0.003, 173) > 0.5
    out = put(out, burns | np.roll(burns, 1, 1), q(np.full((n, n), 0.0), CAB))
    return out


def floor_stage() -> np.ndarray:
    """Stage and balcony decking (1.0 m): steel chequer plate with 6 cm lozenges, the ridges worn bright where feet go, dirt packed between them, scuffs."""
    n = N
    x, y = px.grid(n)
    lx, ly = x % 8, y % 8
    alt = ((x // 8) + (y // 8)) % 2 == 0
    a = np.where(alt, lx - ly, lx + ly - 7)
    ridge = (np.abs(a) < 1.2) & (np.abs(np.where(alt, lx + ly - 7, lx - ly)) < 4.5)
    worn = np.clip((px.noise(n, 18, 184, 3) - 0.45) * 2.0, 0, 1)
    sh = 0.42 + (px.noise(n, 12, 181, 3) - 0.5) * 0.3 - 0.25 * px.grime(n, 182, 0.5, drip=False) + (px.speckle(n, 0.08, 185) - 0.5) * 0.15
    out = q(sh, PLATE)
    out = put(out, ridge, q(sh + 0.22 + 0.25 * worn, PLATE))
    out = put(out, ridge & np.roll(ridge == False, -1, 0), q(sh - 0.25, PLATE))  # noqa: E712
    out = put(out, dmask(np.clip((px.noise(n, 10, 186) - 0.6) * 2.5, 0, 1)) & ~ridge, q(np.full((n, n), 0.3), RUST))
    scuffs = np.zeros((n, n), bool)
    rng = np.random.RandomState(187)
    for _ in range(5):
        x0, y0 = rng.rand() * n, rng.rand() * n
        ang = rng.rand() * np.pi
        scuffs |= seg(n, x0, y0, x0 + np.cos(ang) * 10, y0 + np.sin(ang) * 3, 1.0)
    out = put(out, scuffs, q(np.full((n, n), 0.08), PLATE))
    return out


def ceil_truss() -> np.ndarray:
    """The warehouse roof (1.28 m): corrugated decking with a rib every 12 cm, a rusted I-beam purlin across it, a cable tray, drips of rust from the bolts."""
    n = N
    x, y = px.grid(n)
    rib = np.sin(y * 2 * np.pi / 16)
    out = q(0.3 + 0.18 * rib + 0.08 * (rib > 0.85) + (px.noise(n, 16, 191) - 0.5) * 0.25 - 0.2 * px.grime(n, 192, 0.5, drip=False), PLATE)
    out = put(out, dmask(px.rust(n, 193, 0.4) * 0.6), q(0.2 + 0.3 * px.noise(n, 4, 194), RUST))
    b0, b1 = 52, 70  # the purlin's flange, running along z
    beam = (x >= b0) & (x < b1)
    u = (x - b0) / (b1 - b0)
    bsh = 0.62 - 0.12 * ((u > 0.25) & (u < 0.75)) + 0.25 * (u < 0.12) - 0.3 * (u > 0.88) + (px.noise(n, 6, 195) - 0.5) * 0.25
    out = put(out, beam, q(bsh, TRUSS))
    out = put(out, beam & dmask(px.rust(n, 196, 0.6) * 0.8), q(0.3 + 0.3 * px.noise(n, 3, 197), RUST))
    bolts = beam & ((y % 32) < 2) & ((np.abs(x - b0 - 3) < 1) | (np.abs(x - b1 + 4) < 1))
    out = put(out, bolts, q(np.full((n, n), 0.95), STEEL))
    drip = (np.abs(x - b1 - 2) < 1) & ((y % 32) < 14) & dmask(1 - ((y % 32) / 14.0))
    out = put(out, drip, q(np.full((n, n), 0.4), RUST))
    tray = (x >= 100) & (x < 106)
    out = put(out, tray, q(0.4 + 0.3 * (x == 100) + 0.15 * ((y % 8) < 1), STEEL))
    out = put(out, (x >= 101) & (x < 105) & ((y % 5) < 2), q(np.full((n, n), 0.05), CAB))
    return out


def ceil_low() -> np.ndarray:
    """Low ceilings of the bar, chill-out room and entrance (1.2 m): three black-painted joists a tile over boards, a cable clipped along them, cobwebs."""
    n = N
    x, y = px.grid(n)
    span = n / 3.0
    bx = x - np.floor(x / span) * span
    boards = q(0.3 - 0.2 * ((y % 16) < 1) + (px.noise(n, 8, 201) - 0.5) * 0.3 + (px.speckle(n, 0.08, 202) - 0.5) * 0.15, PLATE)
    joist = bx < 10
    out = put(boards, joist, q(0.42 + 0.35 * (bx < 2) - 0.25 * (bx > 7) + (px.noise(n, 5, 203) - 0.5) * 0.2, STEEL))
    clip = joist & ((y % 64) > 40) & ((y % 64) < 43)
    cab = (np.abs(bx - 11.5) < 1.0)
    out = put(out, cab, q(np.full((n, n), 0.02), CAB))
    out = put(out, clip & (bx > 8), q(np.full((n, n), 0.7), WHITE))
    web = (bx > 10) & (bx < 18) & (((y % 64) < 6) | ((y % 64) > 58)) & dmask(np.clip(1 - (bx - 10) / 8.0, 0, 1) * 0.35)
    out = put(out, web, q(np.full((n, n), 0.55), MORTAR))
    return out


def ceil_stair() -> np.ndarray:
    """The tunnel's ceiling is the underside of the steel stair (1.0 m): treads of 25 cm with amber light from the club leaking through the gaps, rust."""
    n = N
    x, y = px.grid(n)
    ty = y % 32
    out = q(0.32 + 0.35 * (ty < 4) - 0.2 * (ty > 26) + (px.noise(n, 6, 211) - 0.5) * 0.3 + 0.1 * ((x % 8) < 1), STEEL)
    out = put(out, (ty == 29) | (ty == 30), q(0.7 + 0.3 * (ty == 30), AMBER))
    out = put(out, dmask(px.rust(n, 212, 0.5) * 0.8), q(px.noise(n, 4, 213) * 0.6, RUST))
    out = put(out, (ty == 28) & dmask(np.full((n, n), 0.5)), q(np.full((n, n), 0.4), AMBER))
    return out


def wall_led() -> np.ndarray:
    """The booth's LED wall when it is off (StoryWorld swaps in its own image while it plays): black modules in a steel frame, the dead RGB diodes faintly
    coloured. Its metres stay 3.0: the runtime screen (story_world_fx.gd LED_W x LED_H) is laid out on that width."""
    n = N
    x, y = px.grid(n)
    out = q(0.15 + (px.noise(n, 6, 221) - 0.5) * 0.15, MESH)
    di = ((x % 3) == 1) & ((y % 3) == 1)
    hue = ((x // 3) + (y // 3)) % 3
    for i, c in enumerate(("#3a0e22", "#0e2a24", "#14183a")):
        out = put(out, di & (hue == i), q(np.full((n, n), 0.5), px.ramp("#060508", c)))
    frame = ((x % 32) < 1) | ((y % 32) < 1)
    out = put(out, frame, q(np.full((n, n), 0.45), STEEL))
    return out


# ---- billboard props (RGBA) ------------------------------------------------------------------------------------------------------------------------------

def thing_decks() -> np.ndarray:
    """The decks seen from the floor, drawn for a 2.4 x 1.3 m occluder: a flight-cased table, two turntables and a mixer on top, a water bottle on the
    left, a pint and an ashtray with a curl of smoke on the right, cables looping down the front."""
    n = N
    sp = Sprite(n)
    x, y = px.grid(n)
    top = 44
    case = rect(n, 2, top, 126, 124)
    sp.paint(case, PLATE, 0.35 + 0.15 * ((x % 42) < 2) + (px.noise(n, 10, 221) - 0.5) * 0.3)
    sp.paint(rect(n, 2, top, 126, top + 3) | rect(n, 2, 120, 126, 124) | (case & ((x < 4) | (x > 123))), SILVER, 0.55 + 0.3 * (y == top))
    for cx in (2, 122):
        for cy in (top, 118):
            sp.paint(rect(n, cx, cy, cx + 5, cy + 6), SILVER, np.full((n, n), 0.9))
    sp.paint(rect(n, 20, 70, 34, 80), MAGENTA, np.full((n, n), 0.7))  # stickers on the case
    sp.paint(rect(n, 90, 86, 100, 96) & ~text_mask(n, "XX", 90, 88), AMBER, np.full((n, n), 0.6))
    sp.col(rect(n, 90, 86, 100, 96) & text_mask(n, "XX", 90, 88), "#1a0c08")
    for t0 in (12, 76):  # turntables: plinth, platter edge, a red start light
        sp.paint(rect(n, t0, top - 7, t0 + 40, top), CAB, 0.5 + 0.3 * (y == top - 7))
        sp.paint(rect(n, t0 + 4, top - 10, t0 + 34, top - 7), CONE, 0.2 + 0.05 * (x % 3))
        sp.col(rect(n, t0 + 2, top - 3, t0 + 4, top - 1), "#ff3030")
        sp.paint(seg(n, t0 + 34, top - 12, t0 + 26, top - 18, 1.5), SILVER, np.full((n, n), 0.8))
    sp.paint(rect(n, 54, top - 9, 74, top), CAB, 0.45)
    for kx in range(56, 73, 4):
        sp.paint(rect(n, kx, top - 12, kx + 2, top - 9), SILVER, np.full((n, n), 0.7))
    sp.col(rect(n, 58, top - 5, 70, top - 4), "#30ff60")
    # water bottle (left)
    bt = rect(n, 4, top - 30, 11, top) | rect(n, 6, top - 34, 9, top - 30)
    sp.paint(bt, px.ramp("#3a5a7a", "#7aa6c8", "#c8e8ff"), 0.4 + 0.5 * (x < 6))
    sp.paint(rect(n, 4, top - 18, 11, top - 11), px.ramp("#1a3a8a", "#3a6ad0"), 0.5 + 0.4 * (y == top - 18))
    sp.col(rect(n, 6, top - 36, 9, top - 34), "#e0e8f0")
    # pint (right): glass with beer and a head, then an ashtray with a cigarette and smoke
    pint = rect(n, 110, top - 22, 119, top)
    sp.paint(pint, px.ramp("#5a2a08", "#a0600e", "#d8962a", "#f4c050"), 0.3 + 0.5 * (x < 112) + 0.2 * (y > top - 6))
    sp.paint(rect(n, 110, top - 25, 119, top - 21), WHITE, 0.7 + 0.3 * (y == top - 25))
    sp.paint(rect(n, 96, top - 4, 108, top), SILVER, 0.4 + 0.4 * (y == top - 4))
    sp.paint(rect(n, 100, top - 6, 106, top - 4), WHITE, np.full((n, n), 0.9))
    sp.col(rect(n, 99, top - 6, 100, top - 4), "#ff6a20")
    smoke = (np.abs(x - 99 - 3 * np.sin((y - top) * 0.25)) < 1.2 + (top - y) * 0.06) & (y < top - 6) & (y > top - 34)
    sp.paint(smoke & dmask(np.clip((y - (top - 34)) / 30.0, 0, 1) * 0.7), SILVER, np.full((n, n), 0.75))
    # cables over the front edge
    for x0, x1, d in ((26, 48, 14), (60, 70, 22), (82, 108, 10)):
        sp.paint(sag(n, top + 1, d, 1.8, x0, x1), CAB, np.full((n, n), 0.0))
    return sp.rgba()


def thing_pendant() -> np.ndarray:
    """A bar pendant (64 px): a cord, an enamel cone shade, the warm bulb under it."""
    n = 64
    sp = Sprite(n)
    x, y = px.grid(n)
    sp.paint((np.abs(x - 31.5) < 0.6) & (y < 30), CAB, np.full((n, n), 0.1))
    w = 3 + (y - 30) * 0.8
    shade = (np.abs(x - 31.5) < w) & (y >= 30) & (y < 46)
    sp.paint(shade, px.ramp("#1a0c08", "#4a2410", "#8a4a18", "#c07a2a"), 0.3 + 0.6 * ((x - 31.5) < -w * 0.4))
    sp.paint(ell(n, 32, 47, 5, 3), px.ramp("#ffd890", "#fff4d0"), np.full((n, n), 0.8))
    return sp.rgba()


def thing_bulb() -> np.ndarray:
    """A bare bulb on a flex (64 px), for the entrance."""
    n = 64
    sp = Sprite(n)
    x, y = px.grid(n)
    sp.paint((np.abs(x - 31.5) < 0.6) & (y < 34), CAB, np.full((n, n), 0.1))
    sp.paint(rect(n, 29, 34, 35, 38), SILVER, np.full((n, n), 0.5))
    sp.paint(ell(n, 32, 43, 5, 6), px.ramp("#ffc860", "#ffe8a8", "#fffbe8"), 1 - np.hypot(x - 31, y - 41) / 7)
    return sp.rgba()


def thing_sink() -> np.ndarray:
    """A wash basin under a mirror (1.9 m tall): a scratched mirror with a dull reflection, a cracked basin, one tap, the trap pipe."""
    n = N
    sp = Sprite(n)
    x, y = px.grid(n)
    sp.paint(rect(n, 26, 2, 102, 54), SILVER, 0.5 + 0.3 * ((x < 28) | (y < 4)))
    mir = rect(n, 29, 5, 99, 51)
    msh = 0.3 + 0.2 * (y / 51.0) + 0.35 * (np.abs(((x - y * 0.7) % 40) - 6) < 2.5) + (px.noise(n, 10, 241) - 0.5) * 0.2
    sp.paint(mir, GLASS, msh)
    sp.paint(mir & text_mask(n, "SMILE", 46, 18, 2, 0.4), CAB, np.full((n, n), 0.05))
    sp.paint(mir & dmask(px.grime(n, 242, 0.7) * 0.7), GRIMEP, np.full((n, n), 0.5))
    bas = rect(n, 30, 66, 98, 72) | (ell(n, 64, 72, 32, 12) & (y >= 72))
    sp.paint(bas, WHITE, 0.75 - 0.4 * np.clip((y - 66) / 18.0, 0, 1) + 0.15 * (x < 40))
    sp.paint(seg(n, 50, 76, 58, 82, 1.0), WHITE, np.full((n, n), 0.0))
    sp.paint(rect(n, 61, 58, 66, 66) | rect(n, 61, 58, 72, 61), SILVER, 0.7 + 0.2 * (y < 60))
    sp.paint(rect(n, 61, 84, 66, 112) | rect(n, 61, 108, 84, 112), SILVER, 0.45 + 0.3 * (x < 63))
    return sp.rgba()


def thing_dryer() -> np.ndarray:
    """A hand dryer (64 px): a scuffed white box, the nozzle, a warning sticker."""
    n = 64
    sp = Sprite(n)
    x, y = px.grid(n)
    sp.paint(rect(n, 12, 10, 52, 46), WHITE, 0.75 - 0.4 * (y / 46.0) - 0.4 * px.grime(n, 251, 0.6))
    sp.paint(rect(n, 26, 46, 38, 52), SILVER, 0.35)
    sp.paint(rect(n, 20, 18, 30, 24), AMBER, np.full((n, n), 0.8))
    sp.paint(rect(n, 12, 10, 52, 12), WHITE, np.full((n, n), 1.0))
    return sp.rgba()


def thing_tube() -> np.ndarray:
    """A fluorescent fitting (64 px): the batten and a tube burning a sickly green-white."""
    n = 64
    sp = Sprite(n)
    x, y = px.grid(n)
    sp.paint(rect(n, 2, 27, 62, 31), SILVER, 0.4 + 0.3 * (y == 27))
    sp.paint(rect(n, 4, 31, 60, 35), px.ramp("#a8f0d0", "#e8fff4", "#ffffff"), 0.6 + 0.4 * (y == 32))
    sp.paint(rect(n, 2, 31, 4, 35) | rect(n, 60, 31, 62, 35), SILVER, 0.3)
    return sp.rgba()


def thing_toilet() -> np.ndarray:
    """A cubicle's toilet (2.2 m tall): a high cistern with its pull chain, the flush pipe, a pan with a black seat, the last of the paper."""
    n = N
    sp = Sprite(n)
    x, y = px.grid(n)
    sp.paint(rect(n, 48, 8, 80, 22), px.ramp("#141c18", "#24302a", "#3a4a40", "#56685a"), 0.65 - 0.4 * (y - 8) / 14.0 - 0.3 * px.grime(n, 261, 0.7))
    sp.paint(rect(n, 46, 20, 51, 25) | rect(n, 77, 20, 82, 25), RUST, 0.4)
    sp.paint((np.abs(x - 78.5) < 0.6) & (y >= 22) & (y < 64) & ((y % 3) < 2), SILVER, np.full((n, n), 0.7))
    sp.paint(ell(n, 79, 66, 2.5, 3), CAB, np.full((n, n), 0.3))
    sp.paint(rect(n, 62, 22, 66, 92), SILVER, 0.4 + 0.3 * (x < 63))
    seat = ell(n, 64, 96, 24, 6)
    sp.paint(seat, CAB, 0.35 + 0.3 * (y < 94))
    sp.paint(ell(n, 64, 96, 16, 3.5), CONE, np.full((n, n), 0.05))
    pan = (np.abs(x - 64) < 22 - (y - 100) * 0.35) & (y >= 100) & (y < 126)
    sp.paint(pan, WHITE, 0.7 - 0.35 * (np.abs(x - 64) / 22.0) - 0.3 * px.grime(n, 262, 0.6))
    sp.paint(rect(n, 100, 78, 104, 82), SILVER, np.full((n, n), 0.6))
    sp.paint(rect(n, 102, 82, 112, 90), WHITE, 0.85)
    sp.paint(rect(n, 104, 90, 108, 102) & dmask(np.full((n, n), 0.6)), WHITE, np.full((n, n), 0.8))
    return sp.rgba()


def thing_firedoor() -> np.ndarray:
    """The fire door at the end of the corridor (2.1 m): grey-green steel, a wired-glass vision panel, the push bar, a kick plate, a wedge of light under it."""
    n = N
    sp = Sprite(n)
    x, y = px.grid(n)
    sp.paint(rect(n, 22, 6, 106, 128), STEEL, np.full((n, n), 0.5))
    door = rect(n, 26, 10, 102, 126)
    sp.paint(door, PAINT, 0.6 + 0.2 * (x < 30) - 0.35 * px.grime(n, 271, 0.7) + (px.noise(n, 8, 272) - 0.5) * 0.2)
    win = rect(n, 50, 26, 78, 52)
    sp.paint(win, GLASS, 0.25 + 0.15 * (y - 26) / 26.0)
    sp.paint(win & (((x - 50) % 6 == 0) | ((y - 26) % 6 == 0)), SILVER, np.full((n, n), 0.5))
    sp.paint(rect(n, 30, 70, 98, 76), SILVER, 0.6 + 0.3 * (y == 70))
    sp.paint(rect(n, 28, 108, 100, 124), SILVER, 0.35 + 0.15 * ((x + y) % 7 == 0))
    sp.paint(rect(n, 26, 125, 102, 128), AMBER, np.full((n, n), 0.9))
    return sp.rgba()


def thing_exit_sign() -> np.ndarray:
    """A lit fire exit sign (64 px): a green box, a white running figure, a door and an arrow. No lettering."""
    n = 64
    sp = Sprite(n)
    x, y = px.grid(n)
    sp.paint(rect(n, 2, 18, 62, 46), GREEN, 0.75 + 0.2 * (y < 20))
    w = "#f0fff4"
    sp.col(ell(n, 22, 23, 2.5, 2.5), w)
    sp.col(seg(n, 22, 26, 19, 34, 2.5) | seg(n, 19, 34, 14, 42, 2.0) | seg(n, 19, 34, 25, 38, 2.0) | seg(n, 25, 38, 23, 44, 2.0)
           | seg(n, 21, 28, 27, 31, 1.8) | seg(n, 21, 28, 15, 30, 1.8), w)
    sp.col(rect(n, 32, 22, 36, 44) | rect(n, 32, 22, 46, 24) | rect(n, 44, 22, 46, 44), w)
    sp.col(seg(n, 48, 33, 58, 33, 2.0) | seg(n, 58, 33, 54, 29, 2.0) | seg(n, 58, 33, 54, 37, 2.0), w)
    return sp.rgba()


def thing_sofa() -> np.ndarray:
    """A knackered velour sofa (1.5 m): deep back, rolled arms, sagging cushions, a cushion thrown askew, a cigarette burn."""
    n = N
    sp = Sprite(n)
    x, y = px.grid(n)
    nz = (px.noise(n, 6, 281) - 0.5) * 0.2
    back = rect(n, 12, 52, 116, 90) & ~(ell(n, 12, 52, 6, 6) & (x < 12)) & ~(ell(n, 116, 52, 6, 6) & (x > 116))
    sp.paint(back, VELOUR, 0.45 + 0.25 * (y < 58) - 0.15 * (np.abs(((x - 12) % 35) - 17) > 15) + nz)
    sp.paint(rect(n, 16, 86, 112, 100), VELOUR, 0.6 + 0.2 * (y < 89) - 0.3 * (np.abs(((x - 16) % 32) - 16) > 14) + nz)
    for ax in (4, 104):
        arm = rect(n, ax, 72, ax + 20, 112) | ell(n, ax + 10, 74, 10, 6)
        sp.paint(arm, VELOUR, 0.4 + 0.3 * (y < 76) + 0.15 * (x < ax + 6) + nz)
    sp.paint(rect(n, 8, 100, 120, 116), VELOUR, 0.3 + nz)
    sp.paint(rect(n, 12, 116, 18, 124) | rect(n, 110, 116, 116, 124), WOOD, np.full((n, n), 0.4))
    cush = ell(n, 84, 80, 12, 9)
    sp.paint(cush, AMBER, 0.4 + 0.3 * (y < 78) + nz)
    sp.col(ell(n, 40, 92, 1.5, 1.2), "#0a0406")
    return sp.rgba()


def thing_lavalamp() -> np.ndarray:
    """A lava lamp on a side table (64 px, 0.9 m): a chrome base, magenta wax rising in orange-lit fluid."""
    n = 64
    sp = Sprite(n)
    x, y = px.grid(n)
    sp.paint(rect(n, 14, 40, 50, 44), WOOD, 0.7 + 0.2 * (y == 40))
    sp.paint(rect(n, 17, 44, 20, 64) | rect(n, 44, 44, 47, 64), WOOD, np.full((n, n), 0.35))
    base = (np.abs(x - 31.5) < 3 + (y - 30) * 0.45) & (y >= 30) & (y < 40)
    sp.paint(base, SILVER, 0.5 + 0.4 * (x < 31))
    body = (np.abs(x - 31.5) < 6 - np.abs(y - 20) * 0.18) & (y >= 8) & (y < 30)
    sp.paint(body, px.ramp("#6a1a0c", "#b0401a", "#e8742a"), 0.5 + 0.3 * (x < 30))
    wax = body & (ell(n, 31, 13, 3, 3) | ell(n, 33, 24, 4, 3.5) | ell(n, 29, 19, 2, 2))
    sp.paint(wax, MAGENTA, 0.7 + 0.3 * (x < 31))
    sp.paint((np.abs(x - 31.5) < 2.5) & (y >= 4) & (y < 8), SILVER, 0.6)
    return sp.rgba()


def thing_bulbs() -> np.ndarray:
    """A festoon of bulbs (2.4 m): a black flex slung across the chill-out room with warm bulbs hanging from it."""
    n = N
    sp = Sprite(n)
    x, y = px.grid(n)
    wire = sag(n, 40, 16, 1.2, 0, n)
    sp.paint(wire, CAB, np.full((n, n), 0.1))
    for i, bx in enumerate(range(8, n, 16)):
        wy = 40 + 16 * np.sin(np.pi * (bx + 0.5) / n)
        sp.paint(rect(n, bx - 1, wy, bx + 1, wy + 3), CAB, np.full((n, n), 0.2))
        pal = [AMBER, MAGENTA, AMBER, px.ramp("#2a2a10", "#c0a040", "#fff0b0")][i % 4]
        sp.paint(ell(n, bx, wy + 6, 2.5, 3.2), pal, 1.0 - np.hypot(x - bx + 0.8, y - wy - 5) / 5.0 + 0.2)
    return sp.rgba()


def thing_truss_tower() -> np.ndarray:
    """A ground-supported truss tower (6.4 m): two chords and zig-zag lacing, a base plate, a clamp light bracket halfway up."""
    n = N
    sp = Sprite(n)
    x, y = px.grid(n)
    chords = ((x >= 58) & (x < 60)) | ((x >= 68) & (x < 70))
    zz = np.abs(((y % 10) / 10.0) * 8 - (x - 60)) < 1.0
    zz |= np.abs((1 - (y % 10) / 10.0) * 8 - (x - 60)) < 0.7
    lace = zz & (x >= 60) & (x < 68)
    m = (chords | lace) & (y < 124)
    sp.paint(m, STEEL, 0.4 + 0.45 * (x == 58) + 0.2 * (x == 68) - 0.1 * lace + (px.noise(n, 6, 291) - 0.5) * 0.2)
    sp.paint(rect(n, 50, 124, 78, 128), STEEL, 0.3 + 0.3 * (y == 124))
    sp.paint(rect(n, 52, 40, 76, 42), STEEL, 0.6)
    sp.paint(rect(n, 72, 42, 78, 50), CAB, 0.4)
    sp.col(rect(n, 73, 49, 77, 51), "#ffd060")
    return sp.rgba()


def thing_bin() -> np.ndarray:
    """A corridor bin overflowing with plastic cups and a water bottle (64 px, 0.9 m)."""
    n = 64
    sp = Sprite(n)
    x, y = px.grid(n)
    body = (np.abs(x - 31.5) < 13 - (y - 30) * 0.08) & (y >= 30) & (y < 62)
    sp.paint(body, STEEL, 0.35 + 0.3 * (x < 22) + 0.15 * ((y % 6) < 1) - 0.2 * px.grime(n, 301, 0.6))
    sp.paint(rect(n, 17, 28, 47, 31), STEEL, 0.75)
    for cx, cy, a in ((22, 24, 0.3), (30, 20, -0.4), (38, 25, 0.5), (34, 27, 0.0)):
        cup = seg(n, cx, cy, cx + a * 8, cy + 8, 4.5)
        sp.paint(cup, WHITE, 0.6 + 0.3 * (x < cx))
    sp.paint(seg(n, 41, 14, 37, 28, 4.0), px.ramp("#3a5a7a", "#7aa6c8", "#c8e8ff"), 0.6)
    return sp.rgba()


def thing_rail() -> np.ndarray:
    """A length of balcony rail for a 2.0 x 1.1 m occluder: a scuffed steel handrail, a mid rail, posts, a kick plate, a cable tie-wrapped along it."""
    n = N
    sp = Sprite(n)
    x, y = px.grid(n)
    sp.paint(rect(n, 0, 4, n, 12), STEEL, 0.85 - 0.08 * (y - 4) + (px.noise(n, 6, 311) - 0.5) * 0.2)
    sp.paint(rect(n, 0, 60, n, 65), STEEL, 0.6 - 0.08 * (y - 60))
    sp.paint((rect(n, 0, 12, 5, 128) | rect(n, 123, 12, 128, 128)), STEEL, 0.55 + 0.3 * ((x == 1) | (x == 124)))
    sp.paint(rect(n, 0, 112, n, 128), PLATE, 0.35 + 0.3 * (y == 112) + (px.noise(n, 4, 312) - 0.5) * 0.3)
    sp.paint(sag(n, 12, 6, 2.0, 5, 123), CAB, np.full((n, n), 0.0))
    sp.paint(rect(n, 40, 112, 70, 120) & dmask(np.full((n, n), 0.8)), AMBER, np.full((n, n), 0.7))
    return sp.rgba()

def thing_wizard() -> np.ndarray:
    """The wizard who runs the Bassment (128 px, 1.6 m): the trial's own wizard portrait (assets/trial/art/wizard.png) cut out, reduced to a 48-colour ramp
    (it was a resampled crop of 2000 colours) and edged one step darker, with no coloured halo (STYLE_GUIDE 6). The people pipeline's wizard replaces him later (A2)."""
    from PIL import Image
    im = Image.open(os.path.join(lib.ROOT, "assets", "trial", "art", "wizard.png")).convert("RGBA").resize((N, N), Image.NEAREST)
    rgba = np.array(im, np.uint8)
    a = rgba[..., 3] > 127
    pal = Image.fromarray(rgba[..., :3], "RGB").quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB")
    sp = Sprite(N)
    sp.rgb = np.array(pal, np.uint8)
    sp.a = np.where(a, 255, 0).astype(np.uint8)
    sp.rgb[~a] = 0
    sp.edge()
    return sp.rgba()


def thing_headphones() -> np.ndarray:
    """A pair of DJ headphones hung by their cable (64 px, 0.5 m): a steel band, two fat amber cups with a magenta ring, the coiled lead."""
    n = 64
    sp = Sprite(n)
    x, y = px.grid(n)
    band = (np.hypot(x + 0.5 - 32, y + 0.5 - 30) < 22) & (np.hypot(x + 0.5 - 32, y + 0.5 - 30) > 18) & (y < 30)
    sp.paint(band, STEEL, 0.55 + 0.3 * (x < 30))
    for cx in (10, 54):
        sp.paint(ell(n, cx, 36, 7, 10), CAB, 0.45 + 0.25 * (x < cx))
        sp.paint(ell(n, cx, 36, 5, 8), AMBER, 0.5 + 0.35 * (x < cx) - 0.2 * (y > 38))
        sp.paint(ell(n, cx, 36, 2.5, 4), MAGENTA, 0.8)
    sp.paint(sag(n, 44, 12, 1.4, 10, 54) | seg(n, 32, 8, 32, 12, 2.0), CAB, np.full((n, n), 0.2))
    sp.paint(sag(n, 48, 6, 1.0, 8, 24), CAB, np.full((n, n), 0.15))
    return sp.rgba()


def thing_crack() -> np.ndarray:
    """A crack split open in the wall (128 px, 2.0 m): a jagged fissure running top to bottom, its lips of brick bent out, hell-light the colour of a forge pouring through,
    a spill of rubble at the foot. The Underworld door at the club entrance."""
    n = N
    sp = Sprite(n)
    x, y = px.grid(n)
    rng = np.random.RandomState(1701)
    pts = [(64.0, 2.0)]
    for k in range(1, 13):
        pts.append((64 + rng.uniform(-11, 11), 2 + k * 9.4))
    dist = np.full((n, n), 99.0, np.float32)
    wid = np.zeros((n, n), np.float32)
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        dx, dy = x1 - x0, y1 - y0
        t_ = np.clip(((x + 0.5 - x0) * dx + (y + 0.5 - y0) * dy) / (dx * dx + dy * dy), 0, 1)
        d = np.hypot(x + 0.5 - (x0 + t_ * dx), y + 0.5 - (y0 + t_ * dy))
        wd = 4.6 + 4.2 * np.sin(np.pi * (y0 + t_ * dy) / 124.0)  # half width: pinched at both ends
        better = d - wd < dist - wid
        dist = np.where(better, d, dist)
        wid = np.where(better, wd, wid)
    inside = dist - wid
    core = inside < 0
    lips = (inside >= 0) & (inside < 8.0)
    glow = px.ramp("#3a0a08", "#8a200e", "#d8561c", "#ff9a2c", "#fff0a0")
    sp.paint(lips, BRICK, 0.22 + 0.5 * (1 - inside / 8.0) * (0.6 + 0.4 * (px.noise(n, 5, 1702) > 0.45)) + 0.2 * (x < 64))
    sp.paint(core, glow, 0.5 + 0.5 * np.clip(-inside / 4.0, 0, 1) - 0.12 * (px.noise(n, 4, 1703)))
    sp.paint(core & (-inside > 3.0), glow, 0.97)
    for cx, cy, r in ((46, 119, 6), (56, 122, 4), (74, 120, 6), (86, 123, 3), (64, 117, 4), (38, 124, 3)):
        sp.paint(ell(n, cx, cy, r, r * 0.7), BRICK, 0.35 + 0.4 * (x < cx))
    sp.paint(ell(n, 64, 124, 18, 3) & dmask(np.full((n, n), 0.45)), glow, 0.55)
    return sp.rgba()


def thing_booth_radio() -> np.ndarray:
    """The portal to the Mission Count (128 px, 0.9 m): a battered olive military radio set on a crate, a dial with a lit needle, a coiled headset lead, a crackle of
    amber static over it, a handle on top (nothing written on it)."""
    n = N
    sp = Sprite(n)
    x, y = px.grid(n)
    OLIVE = px.ramp("#0c0e08", "#1c2014", "#2e3420", "#444c2c", "#5e683a", "#7e8a4c")
    sp.paint(rect(n, 30, 84, 98, 128), WOOD, 0.35 + 0.3 * (x < 40) + 0.1 * (px.noise(n, 6, 1801) > 0.5))  # the crate
    sp.paint(rect(n, 30, 84, 98, 87), WOOD, 0.8)
    sp.paint(rect(n, 24, 30, 104, 84), OLIVE, 0.45 + 0.35 * (x < 34) + 0.1 * (px.noise(n, 5, 1802) > 0.55))  # the set
    sp.paint(rect(n, 24, 30, 104, 33), OLIVE, 0.85)
    sp.paint(rect(n, 40, 20, 88, 24), STEEL, 0.6)  # the handle
    sp.paint(rect(n, 40, 20, 44, 30) | rect(n, 84, 20, 88, 30), STEEL, 0.5)
    sp.paint(rect(n, 32, 40, 72, 62), CAB, 0.15)  # the dial window
    sp.paint(rect(n, 34, 42, 70, 60), AMBER, 0.55 + 0.4 * (x < 52))
    sp.paint(seg(n, 52, 58, 62, 44, 1.6), CAB, 0.1)
    for cx in (84, 94):  # two knobs
        sp.paint(ell(n, cx, 46, 5, 5), STEEL, 0.6 + 0.3 * (x < cx))
    sp.paint(rect(n, 78, 60, 100, 74), CAB, 0.2)  # a speaker grille
    for gy in range(62, 74, 3):
        sp.paint(rect(n, 80, gy, 98, gy + 1), OLIVE, 0.3)
    sp.paint(sag(n, 78, 24, 1.3, 26, 8) | sag(n, 80, 20, 1.3, 10, 26), CAB, np.full((n, n), 0.2))  # the headset lead
    rng = np.random.RandomState(1803)  # a crackle of static round the dial
    for _ in range(26):
        cx, cy = int(rng.randint(14, 114)), int(rng.randint(12, 70))
        sp.paint(seg(n, cx, cy, cx + int(rng.randint(-5, 6)), cy + int(rng.randint(-5, 6)), 1.0), AMBER, 0.95)
    return sp.rgba()


def thing_bomber_shadow() -> np.ndarray:
    """The bomber's shadow on the booth wall (128 px, 2.6 m): a dark twin-engined silhouette seen from the front, wide wings, two engines, the glazed nose, drawn in
    near-black violet with a thin magenta rim so it reads against the club's wall without being a light."""
    n = N
    sp = Sprite(n)
    x, y = px.grid(n)
    sil = (ell(n, 64, 66, 10, 22) | rect(n, 4, 54, 124, 64) | ell(n, 30, 62, 9, 11) | ell(n, 98, 62, 9, 11) | rect(n, 56, 28, 72, 48) | ell(n, 64, 74, 7, 14))
    sil &= ~(rect(n, 4, 54, 8, 60) & (x < 6))
    edge = sil & (np.roll(~sil, 1, axis=1) | np.roll(~sil, -1, axis=1) | np.roll(~sil, 1, axis=0))
    sp.paint(sil, PURPLE, 0.12 + 0.12 * (px.noise(n, 5, 1811) > 0.5))
    sp.paint(edge & (x > 64), MAGENTA, 0.35)
    sp.paint(ell(n, 64, 74, 3, 5), MAGENTA, 0.4)  # the nose glass catches the club's light
    return sp.rgba()


# ---- the Warehouse's props at the world's grain (stage sprites, PNG in processed/) ------------------------------------------------------------------------
# A billboard tile in textures/ may be at most 128 px (check_assets), so a 2.4 m deck or a 6.4 m truss tower came out at 20 to 53 texels a metre: magnified
# blocks next to the fine people. These are drawn at 120 to 130 texels a metre at their real size and written as stage sprites (manifest stage.sprites,
# `processed/<id>.png`, any size), which the map's things and occluders name. stage.py registers them; the old 2D sprites (woofer, fixture, disco ball, the
# rear silhouettes) are redrawn here as pixels at the same design size, so nothing that reads their pivots changes.

PPM = 128  # texels a metre of the props


def _shade_lr(x, x0, x1, lit=0.25, dark=0.2):
    """Light from the upper left across a body from x0 to x1: brighter at the left, darker at the right."""
    u = np.clip((x - x0) / max(x1 - x0, 1), 0, 1)
    return lit * (1 - u) - dark * u


def prop_woofer():
    """The pumping cone in front of a stack (1.6 m, 192 px; was an SVG target of rings): an 18-inch cone with a foam surround, the dust cap catching the
    light, a steel basket ring with bolts, mounted on a square of black baffle."""
    w = h = 192
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    c = 95.5
    r = np.hypot(x - c, y - c)
    ang = np.arctan2(y - c, x - c)
    lit = -np.cos(ang + np.pi * 0.25)  # 1 on the upper left
    sp.paint(r < 94, CAB, 0.35 + 0.15 * lit * (r > 86) + (noise2(w, h, 10, 301) - 0.5) * 0.2)
    sp.paint((r >= 84) & (r < 90), SILVER, 0.35 + 0.3 * lit)
    bolts = (np.abs(r - 87) < 2.2) & ((((ang + np.pi) / (2 * np.pi) * 8) % 1.0) < 0.06)
    sp.paint(bolts, SILVER, np.full((h, w), 0.95))
    sp.paint((r >= 74) & (r < 84), CONE, 0.35 + 0.3 * lit * np.sin(np.clip((r - 74) / 10, 0, 1) * np.pi))  # the foam surround: a half roll
    cone = (r < 74) & (r >= 22)
    sp.paint(cone, CONE, 0.18 + 0.35 * ((r - 22) / 52.0) + 0.18 * lit * ((r - 22) / 52.0) + (px.speckle(max(w, h), 0.06, 302)[:h, :w] - 0.5) * 0.1)
    sp.paint(cone & (np.abs(r - 48) < 1.0), CONE, np.full((h, w), 0.08))
    sp.paint(r < 22, CONE, 0.45 + 0.4 * lit * np.clip(r / 22.0, 0, 1) + 0.25 * (np.hypot(x - c + 8, y - c + 8) < 6))
    sp.edge()
    return sp.rgba()


def prop_fixture():
    """A par can on a yoke (0.8 m, 66 x 104): a black can lit along its left side, the yoke, a clamp to the truss above, the lens glowing white-gold."""
    w, h = 66, 104
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    sp.paint(box(w, h, 24, 0, 42, 8), STEEL, 0.5 + 0.3 * (x < 28))  # clamp
    sp.paint(box(w, h, 31, 8, 35, 18), STEEL, np.full((h, w), 0.45))
    yoke = (box(w, h, 6, 18, 60, 22) | box(w, h, 6, 18, 10, 56) | box(w, h, 56, 18, 60, 56))
    sp.paint(yoke, CAB, 0.45 + 0.35 * (x < 9) + 0.2 * (y < 20))
    can = box(w, h, 12, 26, 54, 92)
    sp.paint(can, CAB, 0.3 + _shade_lr(x, 12, 54, 0.45, 0.25) + 0.1 * ((y % 10) < 1))
    sp.paint(oval(w, h, 33, 56, 4, 4) | oval(w, h, 8, 52, 4, 4) | oval(w, h, 58, 52, 4, 4), SILVER, np.full((h, w), 0.7))
    sp.paint(box(w, h, 10, 90, 56, 96), SILVER, 0.4 + 0.3 * (x < 20))
    sp.paint(oval(w, h, 33, 97, 21, 6), CAB, np.full((h, w), 0.1))
    lens = oval(w, h, 33, 97, 17, 4.5)
    sp.paint(lens, px.ramp("#806030", "#e8c070", "#fff0c8", "#fffbea"), 0.55 + 0.45 * (np.hypot(x - 28, (y - 96) * 3) < 8))
    sp.edge()
    return sp.rgba()


def prop_disco_ball():
    """The mirror ball (1.3 m with its chain, 106 x 166): a lattice of square mirror tiles, each tile lit by its own facing, a few flaring in the beams."""
    w, h = 106, 166
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    cx, cy, R = 52.5, 113.0, 46.0
    sp.paint(box(w, h, 51, 0, 54, cy - R + 2) & ((y % 4) < 3), STEEL, 0.55 + 0.3 * (x < 52))  # chain
    sp.paint(box(w, h, 46, 4, 59, 12), CAB, 0.4 + 0.3 * (x < 50))  # motor
    dx, dy = (x + 0.5 - cx) / R, (y + 0.5 - cy) / R
    rr = dx * dx + dy * dy
    ball = rr <= 1.0
    z = np.sqrt(np.clip(1 - rr, 0, 1))
    lon = np.arctan2(dx, z)
    lat = np.arcsin(np.clip(dy, -1, 1))
    tile_u = np.floor(lon / (np.pi / 14))
    tile_v = np.floor(lat / (np.pi / 14))
    gridl = ((lon / (np.pi / 14)) % 1.0 < 0.14 * (1 + rr)) | ((lat / (np.pi / 14)) % 1.0 < 0.14 * (1 + rr))
    rng = np.random.RandomState(311)
    tone = rng.rand(40, 40)
    t = tone[(tile_u.astype(int) + 20) % 40, (tile_v.astype(int) + 20) % 40]
    facing = np.clip(-0.55 * dx - 0.6 * dy + 0.6 * z, 0, 1)
    sh = 0.15 + 0.55 * facing + 0.35 * (t - 0.5)
    sp.paint(ball, px.ramp("#140c24", "#2a2048", "#4a4278", "#7a74a8", "#b8b4d8", "#eceaf8"), sh)
    sp.paint(ball & gridl, px.ramp("#0a0614", "#1c1430"), 0.3 + 0.4 * facing)
    flare = ball & ~gridl & (t > 0.93)
    sp.paint(flare, px.ramp("#ff9ad0", "#ffffff"), 0.6 + 0.4 * facing)
    cyan = ball & ~gridl & (t < 0.04)
    sp.paint(cyan, px.ramp("#2fb6c8", "#bff6ff"), 0.7)
    sp.edge()
    return sp.rgba()


def prop_truss_tower():
    """A ground-supported box-truss tower (6.4 m, 40 x 820): two round chords, zig-zag lacing every half metre, a base plate with bolts, a sleeve block,
    rust at the welds, a par can clamped halfway up."""
    w, h = 40, 820
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    c0, c1 = 6, 34  # the two chords' centres
    lace = np.zeros((h, w), bool)
    bay = 64
    for k in range(0, h // bay + 1):
        y0 = k * bay
        lace |= line2(w, h, c0, y0, c1, y0 + bay // 2, 2.2) | line2(w, h, c1, y0 + bay // 2, c0, y0 + bay, 2.2)
        lace |= box(w, h, c0, y0 - 1, c1, y0 + 1)
    lace &= y < h - 14
    sp.paint(lace, TRUSS, 0.4 + 0.2 * (x < 20) + (noise2(w, h, 6, 321) - 0.5) * 0.3)
    for cc in (c0, c1):
        ch = (np.abs(x - cc) < 3) & (y < h - 14)
        sp.paint(ch, TRUSS, 0.62 + 0.3 * (x < cc - 1) - 0.3 * (x > cc + 1) + (noise2(w, h, 5, 322 + cc) - 0.5) * 0.25)
    sp.paint(dmask(np.clip((noise2(w, h, 8, 323) - 0.55) * 3, 0, 1)) & (lace | (np.abs(x - c0) < 3) | (np.abs(x - c1) < 3)) & (y < h - 14),
             RUST, 0.3 + 0.4 * noise2(w, h, 3, 324))
    for sy in (256, 512):  # sleeve blocks where the sections join
        sp.paint(box(w, h, 0, sy - 5, w, sy + 5), STEEL, 0.55 + 0.3 * (y < sy - 3) - 0.2 * (x > 30))
    sp.paint(box(w, h, 0, h - 14, w, h), STEEL, 0.4 + 0.3 * (y < h - 12))
    sp.paint(box(w, h, 4, h - 10, 8, h - 7) | box(w, h, 32, h - 10, 36, h - 7), SILVER, np.full((h, w), 0.9))
    sp.paint(box(w, h, 22, 380, 36, 386), STEEL, np.full((h, w), 0.5))  # clamp and a par can
    sp.paint(box(w, h, 24, 386, 38, 410), CAB, 0.35 + 0.3 * (x < 27))
    sp.paint(box(w, h, 24, 410, 38, 413), px.ramp("#806030", "#ffd890"), np.full((h, w), 0.9))
    sp.edge()
    return sp.rgba()


def _cabinet(sp, w, h, x0, y0, x1, y1, kind, seed):
    """One speaker box into a sprite: black ply worn on the arrises, steel corners, a horn (kind 'horn') or a grille over a cone (kind 'bass')."""
    x, y = grid2(w, h)
    m = box(w, h, x0, y0, x1, y1)
    sp.paint(m, CAB, 0.42 + (noise2(w, h, 8, seed) - 0.5) * 0.3)
    arr = m & ~box(w, h, x0 + 2, y0 + 2, x1 - 2, y1 - 2)
    sp.paint(arr & dmask(np.clip((noise2(w, h, 3, seed + 1) - 0.4) * 2, 0, 1)), WOOD, 0.45 + 0.3 * noise2(w, h, 2, seed + 2))
    sp.paint(box(w, h, x0, y1 - 2, x1, y1) | box(w, h, x1 - 2, y0, x1, y1), CAB, np.full((h, w), 0.05))
    for cx in (x0, x1 - 8):
        for cy in (y0, y1 - 8):
            sp.paint(box(w, h, cx, cy, cx + 8, cy + 8), SILVER, 0.5 + 0.3 * ((x - cx) + (y - cy) < 5))
    iw, ih = x1 - x0, y1 - y0
    if kind == "horn":
        hx0, hx1, hy0, hy1 = x0 + 10, x1 - 10, y0 + 10, y1 - 10
        u = (x - (hx0 + hx1) / 2) / ((hx1 - hx0) / 2)
        v = (y - (hy0 + hy1) / 2) / ((hy1 - hy0) / 2)
        d = np.maximum(np.abs(u), np.abs(v))
        hm = box(w, h, hx0, hy0, hx1, hy1)
        sp.paint(hm, CONE, 0.06 + 0.55 * d ** 2.2 + 0.15 * ((u < 0) & (np.abs(u) > np.abs(v))) + 0.1 * ((v < 0) & (np.abs(v) >= np.abs(u))) - 0.1 * ((v > 0) & (np.abs(v) >= np.abs(u))))
        sp.paint(hm & (d < 0.15), CONE, np.full((h, w), 0.0))
    else:
        gx0, gx1, gy0, gy1 = x0 + 7, x1 - 7, y0 + 7, y1 - 7
        g = box(w, h, gx0, gy0, gx1, gy1)
        cx, cy = (gx0 + gx1) / 2, (gy0 + gy1) / 2
        rr = np.hypot(x - cx, y - cy)
        R = min(gx1 - gx0, gy1 - gy0) * 0.45
        cone = 0.15 + 0.4 * np.clip(rr / R, 0, 1) * (rr < R) + 0.35 * (np.abs(rr - R) < 1.5) + 0.3 * (rr < R * 0.2)
        sp.paint(g, MESH, 0.3 + 0.5 * cone)
        sp.paint(g & ((x % 3) == 1) & ((y % 3) == 1), CONE, 0.05 + 0.5 * cone)
        sp.paint(box(w, h, gx0 - 2, gy0 - 2, gx1 + 2, gy1 + 2) & ~g, MESH, 0.45 + 0.3 * ((y < gy0) | (x < gx0)))


def prop_stack():
    """The floor's speaker stacks (an occluder 0.9 x 2.3 m, 116 x 294): a bass bin, a mid box and a horn box, gaffered together, a light on the top box."""
    w, h = 116, 294
    sp = Sprite(w, h)
    _cabinet(sp, w, h, 0, 190, w, h, "bass", 331)
    _cabinet(sp, w, h, 0, 96, w, 190, "bass", 332)
    _cabinet(sp, w, h, 0, 18, w, 96, "horn", 333)
    x, y = grid2(w, h)
    sp.paint(box(w, h, 30, 186, 70, 194), WHITE, 0.6 + 0.2 * (y == 186))
    sp.paint(box(w, h, 36, 4, 66, 18), CAB, 0.35 + 0.3 * (x < 40))  # a par can lying on the top
    sp.paint(box(w, h, 66, 6, 70, 16), px.ramp("#806030", "#ffd890"), np.full((h, w), 0.9))
    sp.edge()
    return sp.rgba()


def prop_stack_pair():
    """The booth's stacks (2.0 x 2.6 m, 256 x 333): two columns of bass bins under horns, scuffed and stencilled."""
    w, h = 256, 333
    sp = Sprite(w, h)
    for i, x0 in enumerate((0, 128)):
        _cabinet(sp, w, h, x0, 213, x0 + 128, h, "bass", 341 + i)
        _cabinet(sp, w, h, x0, 100, x0 + 128, 213, "bass", 343 + i)
        _cabinet(sp, w, h, x0, 6, x0 + 128, 100, "horn", 345 + i)
    sp.edge()
    return sp.rgba()


def prop_decks():
    """The decks seen from the floor (an occluder 2.4 x 1.3 m, 288 x 156): a flight-cased table, two turntables with a record on each and a mixer between,
    a water bottle and a towel on the left, a pint and an ashtray with a smoking cigarette on the right, cables looping down the front, stickers."""
    w, h = 288, 156
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    top = 62
    case = box(w, h, 2, top, w - 2, h)
    sp.paint(case, PLATE, 0.32 + 0.12 * ((x % 96) < 3) + (noise2(w, h, 10, 351) - 0.5) * 0.3 - 0.2 * np.clip((y - top) / (h - top), 0, 1))
    sp.paint(box(w, h, 2, top, w - 2, top + 4) | box(w, h, 2, h - 5, w - 2, h) | (case & ((x < 6) | (x >= w - 6))), SILVER, 0.5 + 0.3 * (y < top + 2))
    for cx in (2, w - 12):  # ball corners
        for cy in (top, h - 12):
            sp.paint(box(w, h, cx, cy, cx + 10, cy + 12), SILVER, 0.6 + 0.3 * ((x - cx) + (y - cy) < 6))
    for bx in (60, 170):  # butterfly catches
        sp.paint(box(w, h, bx, top + 8, bx + 14, top + 16), SILVER, 0.55 + 0.3 * (y < top + 10))
    sp.paint(box(w, h, 22, 92, 50, 108), MAGENTA, 0.55 + 0.2 * (y < 94))  # stickers
    sp.paint(box(w, h, 206, 100, 228, 114), AMBER, 0.5)
    sp.paint(box(w, h, 206, 100, 228, 114) & text_mask(h, "XX", 210, 104, w=w), CAB, np.full((h, w), 0.05))
    sp.paint(box(w, h, 120, 120, 160, 128), WHITE, 0.55)
    sp.paint(box(w, h, 120, 120, 160, 128) & text_mask(h, "RW 92", 122, 122, w=w), CAB, np.full((h, w), 0.05))
    for t0 in (24, 176):  # turntables: plinth, platter with a record, tonearm, start light
        sp.paint(box(w, h, t0, top - 12, t0 + 88, top), CAB, 0.4 + 0.3 * (y < top - 10) + _shade_lr(x, t0, t0 + 88, 0.1, 0.1))
        rec = oval(w, h, t0 + 40, top - 13, 34, 5)
        sp.paint(rec, CONE, 0.15 + 0.25 * (np.abs(((x - t0) % 7) - 3) < 1))
        sp.paint(oval(w, h, t0 + 40, top - 13, 9, 2), MAGENTA, 0.7)
        sp.paint(line2(w, h, t0 + 80, top - 26, t0 + 62, top - 16, 2.0), SILVER, np.full((h, w), 0.8))
        sp.paint(box(w, h, t0 + 78, top - 28, t0 + 84, top - 18), SILVER, np.full((h, w), 0.6))
        sp.col(box(w, h, t0 + 4, top - 5, t0 + 8, top - 2), "#ff3a30")
    sp.paint(box(w, h, 116, top - 18, 172, top), CAB, 0.45 + 0.2 * (y < top - 16))  # the mixer: faders and knobs
    for kx in range(120, 170, 7):
        sp.paint(box(w, h, kx, top - 24, kx + 3, top - 18), SILVER, np.full((h, w), 0.75))
        sp.col(box(w, h, kx, top - 12, kx + 3, top - 11), ["#30ff60", "#30ff60", "#ffd040", "#ff4040"][((kx - 120) // 7) % 4])
    # water bottle and a towel (left)
    sp.paint(box(w, h, 6, top - 44, 18, top) | box(w, h, 9, top - 50, 15, top - 44), px.ramp("#2a4a6a", "#6a9ac0", "#c0e4ff", "#f0faff"), 0.35 + 0.5 * (x < 9))
    sp.paint(box(w, h, 6, top - 30, 18, top - 20), px.ramp("#1a3a8a", "#3a6ad0"), 0.5 + 0.4 * (y == top - 30))
    sp.col(box(w, h, 9, top - 53, 15, top - 50), "#e0e8f0")
    towel = box(w, h, 2, top - 2, 24, top + 36) & ~((x > 14) & (y > top + 20 + (x - 14)))
    sp.paint(towel, WHITE, 0.45 + 0.3 * (x < 8) - 0.2 * ((y - top) % 8 < 1))
    # pint and ashtray (right)
    pint = box(w, h, 262, top - 36, 278, top)
    sp.paint(pint, px.ramp("#5a2a08", "#a0600e", "#d8962a", "#f4c050"), 0.3 + 0.5 * (x < 265) + 0.15 * (y > top - 8))
    sp.paint(box(w, h, 262, top - 41, 278, top - 35), WHITE, 0.7 + 0.3 * (y == top - 41))
    sp.paint(box(w, h, 234, top - 6, 256, top), SILVER, 0.4 + 0.4 * (y == top - 6))
    sp.paint(box(w, h, 240, top - 9, 252, top - 6), WHITE, np.full((h, w), 0.9))
    sp.col(box(w, h, 238, top - 9, 240, top - 6), "#ff6a20")
    smoke = (np.abs(x - 239 - 4 * np.sin((y - top) * 0.2)) < 1.2 + (top - y) * 0.05) & (y < top - 9) & (y > top - 58)
    sp.paint(smoke & dmask(np.clip((y - (top - 58)) / 50.0, 0, 1) * 0.6), SILVER, np.full((h, w), 0.75))
    for x0, x1, d in ((40, 96, 24), (130, 158, 38), (186, 250, 18), (100, 128, 12)):  # cables over the front
        sp.paint(droop(w, h, x0, x1, top + 2, d, 2.2), CAB, np.full((h, w), 0.0))
    sp.edge()
    return sp.rgba()


def prop_rail():
    """The balcony rail (an occluder 2.0 x 1.1 m, 256 x 140): a scuffed steel handrail, a mid rail, posts with base flanges, a chequer kick plate, a
    cable tie-wrapped along the top, a laminate pass and a glow stick hung on it."""
    w, h = 256, 140
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    sp.paint(box(w, h, 0, 4, w, 13), STEEL, 0.85 - 0.07 * (y - 4) + (noise2(w, h, 6, 361) - 0.5) * 0.2)
    sp.paint(box(w, h, 0, 66, w, 72), STEEL, 0.65 - 0.08 * (y - 66))
    for px0 in (0, 124, w - 8):
        sp.paint(box(w, h, px0, 13, px0 + 8, 122), STEEL, 0.5 + 0.3 * (x < px0 + 2) - 0.25 * (x >= px0 + 6))
    sp.paint(box(w, h, 0, 118, w, h), PLATE, 0.32 + 0.3 * (y == 118) + 0.15 * (((x + y) % 6) == 0) + (noise2(w, h, 4, 362) - 0.5) * 0.3)
    sp.paint(dmask(np.clip((noise2(w, h, 6, 363) - 0.55) * 3, 0, 1)) & (box(w, h, 0, 4, w, 13) | box(w, h, 0, 118, w, h)), RUST, 0.35)
    sp.paint(droop(w, h, 8, 124, 14, 5, 2.0) | droop(w, h, 132, 248, 14, 7, 2.0), CAB, np.full((h, w), 0.0))
    ties = ((x % 22) < 2) & (y >= 12) & (y < 16)
    sp.paint(ties, WHITE, np.full((h, w), 0.6))
    sp.paint(line2(w, h, 70, 13, 66, 30, 1.0) | line2(w, h, 70, 13, 76, 30, 1.0), CAB, np.full((h, w), 0.1))  # a laminate on a lanyard
    sp.paint(box(w, h, 64, 30, 78, 48), WHITE, 0.6 + 0.3 * (y < 33))
    sp.paint(box(w, h, 66, 36, 76, 40), MAGENTA, 0.7)
    sp.paint(box(w, h, 190, 13, 193, 36), px.ramp("#20a060", "#a0ffc0"), 0.9)  # a glow stick tied on
    sp.edge()
    return sp.rgba()


def prop_radio():
    """The Mission Count's entrance on the stage at the booth's corner (1.2 m, 144 x 144; the herald pass put it at [2.8, -6.6]): an olive WW2 field radio standing on an ammunition crate, its canvas strap hanging,
    the dial glowing the Squadron's gold (#ffd25a) with the needle across it, two bakelite knobs, a morse key and a headset on the crate, a whip aerial."""
    w = h = 144
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    OLIVE = px.ramp("#0e1008", "#1c2212", "#2c341c", "#3e4826", "#525e32", "#6a7840", "#86944e")
    GOLD = px.ramp("#3a2a08", "#8a6418", "#d8a838", "#ffd25a", "#fff0b0")
    # the crate (0.45 m): planks, rope handle, a stencil
    cr = box(w, h, 22, 88, 122, h)
    sp.paint(cr, WOOD, 0.38 + _shade_lr(x, 22, 122, 0.2, 0.15) - 0.2 * (((y - 88) % 14) < 1) + (noise2(w, h, 6, 371) - 0.5) * 0.25)
    sp.paint(box(w, h, 22, 88, 122, 92), WOOD, 0.75)
    sp.paint(box(w, h, 22, 88, 28, h) | box(w, h, 116, 88, 122, h), WOOD, 0.55)
    sp.paint(box(w, h, 50, 108, 94, 122) & text_mask(h, "AMMO", 54, 110, 2, w=w), OLIVE, np.full((h, w), 0.85))
    sp.paint(droop(w, h, 98, 114, 98, 6, 2.0), px.ramp("#3a2c18", "#8a7048"), np.full((h, w), 0.7))
    # the set (0.5 m wide)
    body = box(w, h, 28, 30, 116, 88)
    sp.paint(body, OLIVE, 0.42 + _shade_lr(x, 28, 116, 0.3, 0.2) + 0.15 * (y < 33) + (noise2(w, h, 5, 372) - 0.5) * 0.2 - 0.2 * px.grime(max(w, h), 373, 0.5)[:h, :w])
    sp.paint(box(w, h, 28, 30, 116, 32) | box(w, h, 28, 30, 30, 88), OLIVE, np.full((h, w), 0.85))
    sp.paint(dmask(np.clip((noise2(w, h, 4, 374) - 0.6) * 3, 0, 1)) & body, STEEL, 0.6)  # paint chipped to the metal
    for bx in (34, 108):  # latches
        sp.paint(box(w, h, bx - 2, 48, bx + 4, 58), SILVER, 0.6 + 0.3 * (y < 50))
    sp.paint(box(w, h, 40, 38, 84, 62), CAB, np.full((h, w), 0.1))  # the dial window, lit from within
    dial = box(w, h, 42, 40, 82, 60)
    sp.paint(dial, GOLD, 0.6 + 0.35 * (np.hypot(x - 62, y - 52) < 12) - 0.15 * (y > 56))
    sp.paint(dial & ((x % 4) == 0) & (y < 45), GOLD, np.full((h, w), 0.2))
    sp.paint(line2(w, h, 56, 58, 70, 42, 1.4), CAB, np.full((h, w), 0.1))
    for kx in (94, 106):
        sp.paint(oval(w, h, kx, 44, 5, 5), CAB, 0.45 + 0.4 * (x < kx - 1) * (y < 44))
        sp.paint(oval(w, h, kx, 44, 1.5, 1.5), SILVER, np.full((h, w), 0.8))
    sp.paint(box(w, h, 88, 62, 112, 82), CAB, np.full((h, w), 0.2))  # speaker grille
    sp.paint(box(w, h, 88, 62, 112, 82) & ((y % 3) == 0), OLIVE, np.full((h, w), 0.35))
    sp.col(box(w, h, 46, 70, 50, 74), "#ff4030")  # power lamp
    sp.paint(box(w, h, 54, 70, 80, 80), OLIVE, 0.3 + 0.2 * (y == 70))
    sp.paint(box(w, h, 40, 22, 104, 26) | box(w, h, 40, 22, 44, 30) | box(w, h, 100, 22, 104, 30), STEEL, 0.55 + 0.3 * (y < 23))  # handle
    sp.paint(line2(w, h, 108, 30, 128, 2, 1.4), SILVER, np.full((h, w), 0.6))  # whip aerial
    sp.paint(droop(w, h, 28, 46, 80, 26, 3.0), px.ramp("#2a2414", "#6a5a38", "#9a8a5a"), 0.6)  # strap hanging off the side
    sp.paint(box(w, h, 6, 82, 22, 86) | oval(w, h, 9, 92, 4, 6) | oval(w, h, 19, 92, 4, 6), CAB, 0.35 + 0.3 * (x < 9))  # headset hung on the crate's edge
    sp.paint(droop(w, h, 12, 40, 98, 18, 1.4), CAB, np.full((h, w), 0.05))
    sp.edge()
    return sp.rgba()


def prop_ember_glass():
    """The Ember Road's entrance in the bar (0.83 x 1.59 m, 104 x 200; the table top at 1.0 m): a tall steel poseur table, on it a straight pint glass holding a live coal that glows
    the Ember's orange (#ff7a20), sparks lifting off it, its light on the table top and the rim of the glass."""
    w, h = 104, 200
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    EMB = px.ramp("#3a0c04", "#8a2408", "#d8501a", "#ff7a20", "#ffb060", "#fff0c0")
    top = 74
    sp.paint(oval(w, h, 52, top, 46, 6), STEEL, 0.4 + 0.35 * (y < top - 2) + 0.35 * (np.hypot(x - 52, (y - top + 2) * 3) < 18))
    sp.paint(box(w, h, 6, top, 98, top + 3), STEEL, 0.25)
    sp.paint(box(w, h, 48, top + 3, 56, h - 8), STEEL, 0.45 + 0.35 * (x < 50) - 0.2 * (x > 54))
    sp.paint(oval(w, h, 52, h - 5, 26, 4), STEEL, 0.35 + 0.3 * (y < h - 6))
    sp.paint(oval(w, h, 52, top - 1, 20, 3) & ~oval(w, h, 52, top - 1, 9, 2), EMB, np.full((h, w), 0.45))  # the ember's light on the steel
    gl = box(w, h, 42, top - 34, 62, top - 1)
    sp.paint(gl, GLASS, 0.35 + 0.35 * (x < 44) + 0.25 * (x > 59))
    inside = box(w, h, 44, top - 31, 60, top - 2)
    sp.paint(inside, EMB, 0.35 + 0.3 * (y > top - 14))
    coal = oval(w, h, 52, top - 9, 7, 6)
    cn = noise2(w, h, 3, 381)
    sp.paint(coal, EMB, 0.55 + 0.45 * (cn > 0.5) - 0.3 * (np.abs(cn - 0.5) < 0.05))
    sp.paint(box(w, h, 42, top - 35, 62, top - 33), px.ramp("#ffb060", "#fff0c0"), 0.8)  # the rim catches the glow
    rng = np.random.RandomState(382)
    for _ in range(9):  # sparks rising
        sx, sy = 52 + rng.randint(-10, 11), top - 36 - rng.randint(0, 50)
        sp.paint(box(w, h, sx, sy, sx + 1 + (rng.rand() < 0.3), sy + 1), EMB, np.full((h, w), 0.8 + 0.2 * rng.rand()))
    sp.paint(box(w, h, 66, top - 10, 76, top - 1), SILVER, 0.5 + 0.3 * (y == top - 10))  # a beer mat and a lighter
    sp.paint(box(w, h, 20, top - 3, 34, top - 1), MAGENTA, 0.5)
    sp.edge()
    return sp.rgba()


def prop_cellar_hatch():
    """The wizard's way down (1.0 m, 128 x 128): a cellar hatch in the corridor floor with its iron-strapped lid propped up, the ladder's rails rising out of
    it, torch light (#ffb050) welling up from the Bassment and catching the lid's underside, a chain and a padlock hanging open."""
    w = h = 128
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    TORCH = px.ramp("#3a1404", "#8a3a0c", "#d07a24", "#ffb050", "#ffe0a0")
    # the opening seen at a slant: a dark trapezoid lit from below
    hole = (y >= 104) & (y < 120) & (np.abs(x - 64) < 50 + (y - 104) * 0.5)
    sp.paint(hole, TORCH, 0.25 + 0.7 * np.clip(1 - np.abs(x - 64) / 54.0, 0, 1) * np.clip((y - 104) / 14.0, 0.3, 1))
    frame = ((y >= 100) & (y < 104) & (np.abs(x - 64) < 52)) | ((y >= 120) & (y < 124) & (np.abs(x - 64) < 60))
    sp.paint(frame, STEEL, 0.45 + 0.3 * (y < 102))
    # the lid, hinged at the far edge and propped up toward us
    lid = (y >= 18) & (y < 100) & (np.abs(x - 64) < 34 + (y - 18) * 0.04)
    lsh = 0.32 + _shade_lr(x, 24, 104, 0.15, 0.15) + 0.35 * np.clip((y - 50) / 42.0, 0, 1)  # the underside lit by the glow below
    sp.paint(lid, WOOD, lsh - 0.12 * (((x - 24) % 16) < 1) + (noise2(w, h, 6, 391) - 0.5) * 0.2)
    for sy in (26, 74):
        sp.paint(lid & (y >= sy) & (y < sy + 5), STEEL, 0.4 + 0.3 * (y == sy) + 0.25 * np.clip((y - 50) / 42.0, 0, 1))
        sp.paint(lid & (y >= sy + 1) & (y < sy + 3) & ((x % 12) == 3), SILVER, np.full((h, w), 0.9))
    sp.paint(line2(w, h, 100, 104, 96, 62, 3.0), STEEL, 0.4)  # the prop bar
    for rx in (40, 84):  # ladder rails rising out of the hole
        sp.paint(box(w, h, rx, 84, rx + 4, 120), STEEL, 0.4 + 0.4 * (x < rx + 1) + 0.25 * np.clip((y - 100) / 20.0, 0, 1))
    sp.paint(box(w, h, 40, 90, 88, 92), STEEL, np.full((h, w), 0.5))
    sp.paint(droop(w, h, 14, 32, 100, 10, 2.0) & ((x % 3) < 2), SILVER, np.full((h, w), 0.6))
    sp.paint(box(w, h, 27, 108, 33, 115), AMBER, 0.6)
    sp.edge()
    return sp.rgba()


def prop_flight_cases():
    """Flight cases stacked out of the way (1.0 m, 128 x 128): two black cases with aluminium edges, ball corners, butterfly catches, stencils and gaffer."""
    w = h = 128
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    for (x0, y0, x1, y1, seed, word) in ((8, 64, 124, h, 401, "DECKS"), (20, 18, 110, 64, 402, "MIC")):
        m = box(w, h, x0, y0, x1, y1)
        sp.paint(m, PLATE, 0.32 + _shade_lr(x, x0, x1, 0.15, 0.15) + (noise2(w, h, 8, seed) - 0.5) * 0.25)
        sp.paint(m & ~box(w, h, x0 + 3, y0 + 3, x1 - 3, y1 - 3), SILVER, 0.5 + 0.3 * ((y < y0 + 2) | (x < x0 + 2)))
        sp.paint(m & (np.abs(y - (y0 + y1) / 2) < 1.5), SILVER, np.full((h, w), 0.55))
        for cx in (x0, x1 - 7):
            for cy in (y0, y1 - 7):
                sp.paint(box(w, h, cx, cy, cx + 7, cy + 7), SILVER, 0.65 + 0.3 * ((x - cx) + (y - cy) < 4))
        sp.paint(box(w, h, x0 + 10, y0 + 8, x0 + 10 + 4 * len(word) + 3, y0 + 15), WHITE, 0.55)
        sp.paint(box(w, h, x0 + 10, y0 + 8, x0 + 10 + 4 * len(word) + 3, y0 + 15) & text_mask(h, word, x0 + 12, y0 + 9, w=w), CAB, np.full((h, w), 0.05))
    sp.edge()
    return sp.rgba()


def prop_mop_bucket():
    """A mop bucket by the bar (0.75 m, 96 x 96): a yellow wheeled bucket with its wringer, grey water, the mop handle leaning out, a wet patch."""
    w = h = 96
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    YEL = px.ramp("#2a2006", "#6a5010", "#a88420", "#d8b030", "#f4d860")
    sp.paint(oval(w, h, 48, 91, 40, 4), px.ramp("#141216", "#2a2a34"), np.full((h, w), 0.6))
    body = (y >= 46) & (y < 86) & (np.abs(x - 48) < 30 - (y - 46) * 0.1)
    sp.paint(body, YEL, 0.45 + _shade_lr(x, 18, 78, 0.3, 0.25) - 0.15 * ((y % 9) < 1))
    sp.paint(box(w, h, 20, 44, 76, 48), YEL, 0.85)
    sp.paint(box(w, h, 22, 46, 74, 50), px.ramp("#2a2a24", "#5a5a48"), 0.5)
    sp.paint(box(w, h, 56, 30, 74, 46), STEEL, 0.4 + 0.3 * (y < 32))  # the wringer
    sp.paint(line2(w, h, 40, 50, 18, 2, 3.0), WOOD, 0.6)  # the mop handle
    sp.paint(oval(w, h, 40, 48, 8, 3), WHITE, 0.4)
    for wx in (24, 72):
        sp.paint(oval(w, h, wx, 88, 4, 4), CAB, 0.3)
    sp.edge()
    return sp.rgba()


def prop_crates():
    """Beer crates of empties stacked by the bar (0.75 m, 112 x 96): red plastic crates with hand holes, brown bottles' necks showing."""
    w, h = 112, 96
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    RED = px.ramp("#2a0608", "#5a0e12", "#8a1a1c", "#b82a26", "#e05040")
    for y0, x0 in ((50, 4), (6, 10)):
        m = box(w, h, x0, y0 + 10, x0 + 100, y0 + 46)
        sp.paint(m, RED, 0.42 + _shade_lr(x, x0, x0 + 100, 0.2, 0.2) + 0.15 * ((y - y0) % 12 < 1))
        sp.paint(m & ((x - x0) % 12 < 2), RED, np.full((h, w), 0.2))
        sp.paint(box(w, h, x0 + 40, y0 + 16, x0 + 60, y0 + 22), CAB, np.full((h, w), 0.05))  # hand hole
        for bx in range(x0 + 6, x0 + 96, 12):
            sp.paint(box(w, h, bx, y0, bx + 5, y0 + 10), px.ramp("#2a1004", "#6a3010", "#b06a28"), 0.4 + 0.4 * (x == bx))
            sp.paint(box(w, h, bx + 1, y0, bx + 4, y0 + 2), SILVER, np.full((h, w), 0.6))
    sp.edge()
    return sp.rgba()


def prop_coffee_table():
    """The chill-out room's low table (1.1 x 0.55 m, 144 x 72): a scratched cable drum used as a table, an ashtray heaped full, a bottle of water, two cans,
    a flyer and a tea light."""
    w, h = 144, 72
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    sp.paint(oval(w, h, 72, 24, 66, 10), WOOD, 0.5 + 0.25 * (y < 22) + (noise2(w, h, 8, 411) - 0.5) * 0.3)
    sp.paint(box(w, h, 22, 26, 122, 64), WOOD, 0.3 + _shade_lr(x, 22, 122, 0.2, 0.2) - 0.15 * (((x - 22) % 10) < 1))
    sp.paint(oval(w, h, 72, 66, 54, 6), WOOD, np.full((h, w), 0.2))
    sp.paint(box(w, h, 40, 10, 62, 18), SILVER, 0.4 + 0.3 * (y < 12))
    sp.paint(box(w, h, 43, 7, 58, 11) & dmask(np.full((h, w), 0.7)), WHITE, np.full((h, w), 0.7))
    sp.paint(box(w, h, 80, 0, 88, 20), px.ramp("#2a4a6a", "#6a9ac0", "#c0e4ff"), 0.4 + 0.4 * (x < 82))
    for cx in (96, 104):
        sp.paint(box(w, h, cx, 8, cx + 6, 20), [MAGENTA, SILVER][cx == 104], 0.5 + 0.3 * (x == cx))
    sp.paint(box(w, h, 20, 18, 36, 24), AMBER, 0.6)
    sp.paint(box(w, h, 112, 14, 118, 20), WHITE, 0.6)
    sp.col(box(w, h, 114, 12, 116, 14), "#ffd060")
    sp.edge()
    return sp.rgba()


SIL_SCALE = 128.0 / 52.0  # design units per pixel of a rear silhouette: the busts at the baked people's grain (about 62 px a metre)


def prop_silhouette(kind: str, up: bool) -> np.ndarray:
    """A rear-row figure from behind (head and shoulders, the old SVG shapes' sizes): a dark fill dithered toward the fog, the hair's own shape, one pixel
    of cyan rim on the left and magenta on the right from the club's beams, arms up on the drop."""
    s = 1.0 / SIL_SCALE
    w = 52
    h = 59 if up else 47
    top = 140 if up else 112
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    X = (x + 0.5) / s - 64.0  # design units, origin bottom centre
    Y = (y + 0.5) / s - top
    sw = {"a": 38, "b": 30, "c": 44}[kind]
    hr = {"a": (16, 19), "b": (14, 17), "c": (18, 20)}[kind]
    torso = (Y > -50) & (Y < 4) & (np.abs(X) < sw - 6 * np.clip((Y + 50) / -1.0, 0, 1) - 8 * np.clip(-(Y + 26) / 24.0, 0, 1))
    neck = (np.abs(X) < 9) & (Y > -60) & (Y <= -46)
    head = ((X / hr[0]) ** 2 + ((Y + 74) / hr[1]) ** 2) <= 1.0
    hair = np.zeros_like(head)
    if kind == "a":
        hair = ((X / (hr[0] + 1)) ** 2 + ((Y + 79) / (hr[1] - 2)) ** 2 <= 1.0) & (Y < -74)
    elif kind == "b":
        hair = (((X - 1) / 8) ** 2 + ((Y + 94) / 8) ** 2 <= 1.0) | ((X > 6) & (X < 22) & (Y > -82) & (Y < -50 - (X - 6) * 0.5))
    else:
        hair = ((Y < -78) & (Y > -102) & (np.abs(X) < 20)) | ((Y > -82) & (Y < -74) & (X < -16) & (X > -38))  # a cap and its peak
    arms = np.zeros_like(head)
    if up:
        for sd in (-1, 1):
            ax0, ay0, ax1, ay1 = sd * 26, -40, sd * 48, -116
            dx, dy = ax1 - ax0, ay1 - ay0
            t = np.clip(((X - ax0) * dx + (Y - ay0) * dy) / (dx * dx + dy * dy), 0, 1)
            arms |= np.hypot(X - (ax0 + t * dx), Y - (ay0 + t * dy)) < 6.5
            arms |= np.hypot(X - ax1 * 1.02, Y - ay1 - 4) < 7
    body = torso | neck | head | hair | arms
    SIL = px.ramp("#0a0618", "#110a22", "#181030", "#20163a")
    sp.paint(body, SIL, 0.35 + 0.25 * (hair | (Y < -90)) * 0.0 + 0.3 * np.clip(-(Y + 20) / 80.0, 0, 1) + (px.speckle(64, 0.2, 421 + ord(kind))[:h, :w] - 0.5) * 0.25)
    sp.paint(hair, SIL, np.full((h, w), 0.05))
    left = body & ~np.roll(body, 1, 1)
    right = body & ~np.roll(body, -1, 1)
    topr = body & ~np.roll(body, 1, 0)
    sp.paint(left | (topr & (X < 0)), px.ramp("#0f3a44", "#2fb6c8"), np.full((h, w), 0.6))
    sp.paint(right | (topr & (X >= 0)), px.ramp("#5c1244", "#c23a8a"), np.full((h, w), 0.6))
    return sp.rgba()


PROPS = {  # id -> (drawing, pivot as a fraction of the size or None, metres the sprite's height stands for)
    "prop_truss_tower": prop_truss_tower, "prop_stack": prop_stack, "prop_stack_pair": prop_stack_pair, "prop_decks": prop_decks,
    "prop_rail": prop_rail, "prop_radio": prop_radio, "prop_ember_glass": prop_ember_glass,
    "prop_cellar_hatch": prop_cellar_hatch, "prop_flight_cases": prop_flight_cases, "prop_mop_bucket": prop_mop_bucket, "prop_crates": prop_crates,
    "prop_coffee_table": prop_coffee_table,
}


def write_props(out_dir: str) -> dict:
    """Write the props and the redrawn 2D sprites as PNGs into out_dir (the chapter's processed/ folder); returns {sprites: {...}, silhouettes: {...}}
    entries for the manifest (file relative to the chapter folder, pivot in texture pixels, px_scale = design px a texture px)."""
    os.makedirs(out_dir, exist_ok=True)
    sprites = {}
    for sid, fn in sorted(PROPS.items()):
        a = fn()
        save_rgba(os.path.join(out_dir, sid + ".png"), a)
        sprites[sid] = {"file": f"processed/{sid}.png", "pivot": [a.shape[1] / 2.0, float(a.shape[0])], "px_scale": 1.0}
    # the old 2D sprites at their old design size (texture px x px_scale = design px), now pixels
    a = prop_woofer()
    save_rgba(os.path.join(out_dir, "woofer.png"), a)
    sprites["woofer"] = {"file": "processed/woofer.png", "pivot": [96.0, 96.0], "px_scale": round(106.0 / 192.0, 6), "radius": 50}
    a = prop_fixture()
    save_rgba(os.path.join(out_dir, "fixture.png"), a)
    k = 62.0 / 104.0
    sprites["fixture"] = {"file": "processed/fixture.png", "pivot": [33.0, round(2.0 / k, 3)], "px_scale": round(k, 6), "lens": [0, 51]}
    a = prop_disco_ball()
    save_rgba(os.path.join(out_dir, "disco_ball.png"), a)
    k = 100.0 / 166.0
    sprites["disco_ball"] = {"file": "processed/disco_ball.png", "pivot": [53.0, round(2.0 / k, 3)], "px_scale": round(k, 6), "radius": 28, "ball_centre": [0, 66]}
    sils = {}
    for kind in ("a", "b", "c"):
        e = {}
        for state in ("idle", "up"):
            a = prop_silhouette(kind, state == "up")
            fn = f"sil_{kind}_{state}.png"
            save_rgba(os.path.join(out_dir, fn), a)
            top = 140 if state == "up" else 112
            e[state] = {"file": f"processed/{fn}", "pivot": [26.0, round(top / SIL_SCALE, 3)], "px_scale": round(SIL_SCALE, 6)}
        e["height"] = 100
        sils[f"sil_{kind}"] = e
    return {"sprites": sprites, "silhouettes": sils}


SPRITES = {
    "thing_decks": thing_decks, "thing_pendant": thing_pendant, "thing_bulb": thing_bulb, "thing_sink": thing_sink,
    "thing_dryer": thing_dryer, "thing_tube": thing_tube, "thing_toilet": thing_toilet, "thing_firedoor": thing_firedoor, "thing_exit_sign": thing_exit_sign,
    "thing_sofa": thing_sofa, "thing_lavalamp": thing_lavalamp, "thing_bulbs": thing_bulbs, "thing_truss_tower": thing_truss_tower, "thing_bin": thing_bin,
    "thing_rail": thing_rail, "thing_wizard": thing_wizard, "thing_headphones": thing_headphones, "thing_crack": thing_crack,
    "thing_booth_radio": thing_booth_radio, "thing_bomber_shadow": thing_bomber_shadow,  # the Mission Count portal in the booth
}


def write_sprites(out_dir: str = OUT) -> list:
    os.makedirs(out_dir, exist_ok=True)
    for tid, fn in sorted(SPRITES.items()):
        save_rgba(os.path.join(out_dir, tid + ".png"), fn())
    return sorted(SPRITES)


def build() -> dict:
    """The opaque tiles {id: (rgb, metres)}; the RGBA props are written to the textures folder as a side effect (ids listed in tiles.NIGHT_ONE)."""
    write_sprites()
    return {  # metres a repeat: 128 px over 1.0 to 1.3 m is 98 to 128 texels a metre (the style guide's 96 to 160); the exceptions say why
        "wall_brick": (wall_brick(), 1.0),
        "wall_panel": (wall_panel(), 1.28),
        "wall_speaker": (wall_speaker(), 1.0),
        "wall_bar": (wall_bar(), 1.2),
        "bar_front": (bar_front(), 1.2),
        "wall_door": (wall_door(), 2.0),  # the street seen through the tunnel's end: one 2 x 2 m picture on its own wall segment (64 px/m, a view, not a surface)
        "trim": (trim(), 1.0),
        "toilet_tile": (toilet_tile(), 1.0),
        "toilet_floor": (toilet_floor(), 1.0),
        "cubicle_door": (cubicle_door(), 2.6),  # the partitions' gaps sit at the floor and the ceiling of a 2.6 m room: one repeat floor to ceiling (49 px/m)
        "cubicle_wall": (cubicle_wall(), 1.2),
        "wall_corridor": (wall_corridor(), 1.2),
        "wall_chill": (wall_chill(), 1.3),
        "ceil_wc": (ceil_wc(), 1.2),
        "floor_dark": (floor_dark(), 1.28),
        "floor_boards": (floor_boards(), 1.0),
        "floor_carpet": (floor_carpet(), 1.0),
        "floor_stage": (floor_stage(), 1.0),
        "ceil_truss": (ceil_truss(), 1.28),
        "ceil_low": (ceil_low(), 1.2),
        "ceil_stair": (ceil_stair(), 1.0),
        "wall_led": (wall_led(), 3.0),  # replaced at runtime by the LED screen, which story_world_fx.gd lays out over 3 m (LED_W): the metres must stay
    }
