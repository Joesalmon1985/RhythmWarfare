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
    """An RGBA billboard canvas: paint palette-quantised shapes, unpainted pixels stay transparent."""

    def __init__(self, n: int = N):
        self.n = n
        self.rgb = np.zeros((n, n, 3), np.uint8)
        self.a = np.zeros((n, n), np.uint8)

    def paint(self, mask, pal, shade) -> None:
        m = np.asarray(mask, bool)
        layer = q(shade, pal, shape=(self.n, self.n))
        self.rgb[m] = layer[m]
        self.a[m] = 255

    def col(self, mask, hexc: str) -> None:
        m = np.asarray(mask, bool)
        self.rgb[m] = (px.hexc(hexc) * 255 + 0.5).astype(np.uint8)
        self.a[m] = 255

    def rgba(self) -> np.ndarray:
        return np.dstack([self.rgb, self.a])


def save_rgba(path: str, rgba: np.ndarray) -> None:
    from PIL import Image
    Image.fromarray(rgba, "RGBA").save(path, optimize=False, compress_level=9)


def stretch_rows(m: np.ndarray, k: int) -> np.ndarray:
    return np.repeat(m, k, axis=0)


# ---- walls -----------------------------------------------------------------------------------------------------------------------------------------------

def brick_wall(n=N, rows=16, cols=4, seed=11, pal=BRICK, grime=0.6, rust=0.35, soot_top=0.0) -> np.ndarray:
    x, y = px.grid(n)
    sh, mort = px.bricks(n, rows=rows, cols=cols, seed=seed, wear=0.45)
    g = px.grime(n, seed + 1, grime)
    sh = sh - 0.4 * g - soot_top * np.clip(1 - y / (n * 0.5), 0, 1)
    out = q(sh, pal)
    mo = q(0.55 - 0.5 * g + (px.noise(n, 4, seed + 3) - 0.5) * 0.5, MORTAR)
    out = put(out, mort > 0.5, mo)
    if rust > 0:
        r = px.rust(n, seed + 2, rust)
        out = put(out, dmask(r * 0.9) & (mort < 0.5), q(px.noise(n, 5, seed + 4) * 0.8, RUST))
    # efflorescence and old paint flecks: a few pale specks
    out = put(out, px.speckle(n, 0.004, seed + 5) > 0.5, q(np.full((n, n), 0.9), MORTAR))
    return out


def steel_shade(n, x0, x1, seed, horizontal=False):
    """An I-beam's shading across its width: a lit flange, a dark web, a shadowed flange."""
    x, y = px.grid(n)
    a = y if horizontal else x
    w = x1 - x0
    u = (a - x0) / w
    sh = 0.42 + 0.3 * (u < 0.16) - 0.18 * (u > 0.84) - 0.1 * ((u > 0.3) & (u < 0.7)) + (px.noise(n, 6, seed) - 0.5) * 0.25
    return sh


def wall_panel() -> np.ndarray:
    """The main floor's walls (3.2 m a repeat): soot-black brick, a riveted steel stanchion, a conduit and cable tray, cables looping."""
    n = N
    x, y = px.grid(n)
    out = brick_wall(n, rows=22, cols=4, seed=21, grime=0.75, rust=0.3)
    out = (out.astype(np.float32) * 0.85).astype(np.uint8)
    col = (x >= 6) & (x < 24)
    sh = steel_shade(n, 6, 24, 22)
    rv = ((np.abs(x - 8) < 1) | (np.abs(x - 21) < 1)) & ((y % 16) < 1.5)
    sh = np.where(rv, 0.95, sh)
    steel = q(sh, STEEL)
    steel = put(steel, dmask(px.rust(n, 23, 0.55) * 0.9), q(px.noise(n, 4, 24) * 0.7, RUST))
    out = put(out, col, steel)
    # conduit pipes and a cable tray across the wall
    for y0, y1 in ((30, 34), (36, 39)):
        m = (y >= y0) & (y < y1)
        u = (y - y0) / (y1 - y0)
        out = put(out, m, q(0.75 - 0.6 * u + (px.noise(n, 8, y0) - 0.5) * 0.2, STEEL))
    clips = ((x % 32) < 2) & (y >= 29) & (y < 40)
    out = put(out, clips, q(np.full((n, n), 0.2), STEEL))
    tray = (y >= 72) & (y < 75)
    out = put(out, tray, q(np.full((n, n), 0.55) + (px.noise(n, 4, 25) - 0.5) * 0.3, STEEL))
    cab = np.zeros((n, n), bool)
    for i, (yy, d, ph) in enumerate(((75, 10, 0), (75, 16, 1), (76, 7, 2))):
        x0 = (i * 43) % n
        m = sag(n, yy, d, 1.3, 0, n)
        cab |= np.roll(m, x0, 1)
    out = put(out, cab, q(np.full((n, n), 0.08), STEEL))
    out = put(out, cab & (np.roll(cab, 1, 0) == False), q(np.full((n, n), 0.3), STEEL))  # noqa: E712
    return out


def wall_brick() -> np.ndarray:
    """Tunnel, entrance and old walls: red-brown brick, sooty, rust bleeding from old fixings."""
    n = N
    x, y = px.grid(n)
    out = brick_wall(n, rows=16, cols=4, seed=11, grime=0.65, rust=0.45)
    # two old wall plugs with rust tears running down
    for fx, fy in ((34, 20), (96, 70)):
        out = put(out, (np.abs(x - fx) < 1.5) & (np.abs(y - fy) < 1.5), q(np.full((n, n), 0.1), STEEL))
        tear = (np.abs(x - fx - 0.5 * np.sin(y * 0.3)) < 1.2) & (y > fy) & (y < fy + 26)
        out = put(out, tear & dmask(1 - (y - fy) / 30.0), q(np.full((n, n), 0.45), RUST))
    return out


def wall_speaker() -> np.ndarray:
    """A speaker stack (2 m a repeat, four 1 m boxes): horns over 18-inch woofers, scuffed cabinets with steel corners."""
    n = N
    x, y = px.grid(n)
    lx, ly = x % 64, y % 64
    top = y < 64
    sh = 0.45 + (px.noise(n, 8, 31) - 0.5) * 0.3
    out = q(sh, CAB)
    edge = (lx < 2) | (ly < 2) | (lx > 61) | (ly > 61)
    out = put(out, edge, q(np.full((n, n), 0.05), CAB))
    corner = ((lx < 7) | (lx > 56)) & ((ly < 7) | (ly > 56)) & ((np.minimum(lx, 63 - lx) + np.minimum(ly, 63 - ly)) < 9)
    out = put(out, corner, q(0.7 - 0.02 * (lx + ly) % 0.3, SILVER))
    # woofers (bottom row)
    cx, cy = lx - 31.5, ly - 31.5
    r = np.hypot(cx, cy)
    woof = (~top) & (r < 26)
    cone = 0.25 + 0.35 * (r / 26.0) - 0.2 * (np.abs(r - 24) < 1.5) + 0.25 * ((cx + cy) < -10) * (r > 14) * 0.6
    cone = np.where(r < 8, 0.65 - 0.04 * r + 0.2 * ((cx + cy) < -4), cone)
    out = put(out, woof, q(cone, CONE))
    out = put(out, (~top) & (np.abs(r - 27.5) < 1.2), q(np.full((n, n), 0.75), CONE))
    bolts = (~top) & (np.abs(r - 28.5) < 1) & (((np.degrees(np.arctan2(cy, cx)) + 360) % 45) < 6)
    out = put(out, bolts, q(np.full((n, n), 0.8), SILVER))
    # horns (top row): a flared mouth with a throat, two small tweeters beside
    hx, hy = lx - 31.5, ly - 26
    horn = top & (np.abs(hx) < 22 - 0.0 * hy) & (np.abs(hy) < 15)
    depth = np.maximum(np.abs(hx) / 22.0, np.abs(hy) / 15.0)
    out = put(out, horn, q(0.05 + 0.55 * depth ** 2, CONE))
    out = put(out, top & (np.abs(hx) < 4) & (np.abs(hy) < 3), q(np.full((n, n), 0.0), CONE))
    for tx in (14, 49):
        t = top & (np.hypot(lx - tx, ly - 52) < 5)
        out = put(out, t, q(0.6 - 0.08 * np.hypot(lx - tx, ly - 52), CONE))
    # a strip of gaffer and a stencil on one box, dust on the tops
    out = put(out, (ly > 2) & (ly < 4) & top & (lx > 8) & (lx < 56), q(np.full((n, n), 0.3), CONE))
    out = put(out, rect(n, 70, 4, 92, 9) & dmask(np.full((n, n), 0.7)), q(np.full((n, n), 0.75), SILVER))
    return out


def trim() -> np.ndarray:
    """The truss over the stage openings: a steel lattice girder every half metre against the dark roof."""
    n = N
    sh, m = px.truss(32, 41)
    sh = np.tile(sh, (4, 4))
    m = np.tile(m, (4, 4))
    out = q(0.3 + (px.noise(n, 16, 42) - 0.5) * 0.3, DECK)
    x, y = px.grid(n)
    lit = 0.35 + 0.35 * sh + 0.25 * ((y % 32) < 6)
    return put(out, m > 0.5, q(lit, STEEL))


def bar_front() -> np.ndarray:
    """The back bar behind the bartender (2.4 m, floor to ceiling): mirror and shelves of bottles, the back counter with a till, lit fridges below."""
    n = N
    x, y = px.grid(n)
    rng = np.random.RandomState(51)
    out = q(0.15 + (px.noise(n, 6, 52) - 0.5) * 0.2, WOOD)
    # mirror back with amber smears
    mir = (y >= 7) & (y < 62)
    msh = 0.35 + 0.25 * np.sin((x + y * 0.8) * 0.09) ** 8 + (px.noise(n, 16, 53) - 0.5) * 0.3
    out = put(out, mir, q(msh, px.ramp("#120a12", "#22121a", "#3a2018", "#64381c", "#9a5e28")))
    # shelves and bottles
    for sy in (26, 44, 61):
        xx = 1
        while xx < n - 4:
            w = int(rng.randint(3, 6))
            h = int(rng.randint(9, 15))
            hue = rng.randint(0, 5)
            pal = [px.ramp("#0a2a14", "#14522a", "#2a8a48"), px.ramp("#3a1a06", "#7a3c0c", "#c07a1c"),
                   px.ramp("#30343a", "#7a8a94", "#d0dce4"), px.ramp("#0a1a3a", "#1a3a7a", "#4a7ad0"),
                   px.ramp("#3a0a10", "#7a1620", "#c0303a")][hue]
            body = (x >= xx) & (x < xx + w) & (y >= sy - h + 4) & (y < sy)
            neck = (x >= xx + w // 2 - 1) & (x < xx + w // 2 + 1) & (y >= sy - h) & (y < sy - h + 4)
            out = put(out, body | neck, q(0.35 + 0.4 * ((x - xx) < 1.5), pal))
            lab = body & (y >= sy - h // 2 - 2) & (y < sy - 2) & ((rng.rand() < 0.7))
            out = put(out, lab, q(np.full((n, n), 0.9), WHITE))
            xx += w + int(rng.randint(1, 3))
        out = put(out, (y >= sy) & (y < sy + 2), q(np.full((n, n), 0.8), WOOD))
        out = put(out, (y == sy + 2), q(np.full((n, n), 0.0), WOOD))
    # back counter top with a till and a stack of glasses
    out = put(out, (y >= 62) & (y < 66), q(0.6 + 0.3 * (y < 63), WOOD))
    out = put(out, rect(n, 84, 50, 102, 62), q(0.3 + 0.2 * (y < 54), STEEL))
    out = put(out, rect(n, 87, 52, 99, 55), q(np.full((n, n), 0.9), GREEN))
    for gx in range(20, 40, 5):
        out = put(out, rect(n, gx, 54, gx + 4, 62), q(0.45 + 0.4 * (x == gx), GLASS))
    # fridges with lit shelves of bottles (left half), wooden cupboards (right half)
    fr = (y >= 68) & (y < 124) & (x < 62)
    fx = x % 31
    inside = fr & (fx > 2) & (fx < 29) & (y > 70) & (y < 121)
    out = put(out, fr, q(np.full((n, n), 0.55), STEEL))
    glow = 0.55 + 0.35 * ((y - 70) % 13 < 2)
    out = put(out, inside, q(glow + (px.noise(n, 4, 54) - 0.5) * 0.2, px.ramp("#1c2830", "#3a5a64", "#6a9aa0", "#b0e0dc")))
    bott = inside & (((x * 7) // 5) % 3 == 0) & ((y - 70) % 13 > 4) & ((y - 70) % 13 < 12)
    out = put(out, bott, q(np.full((n, n), 0.3), px.ramp("#2a1a08", "#6a3a10", "#a0601c")))
    cup = (y >= 68) & (y < 124) & (x >= 64)
    cx = (x - 64) % 32
    out = put(out, cup, q(0.4 + 0.25 * (cx < 2) - 0.2 * (cx > 29) + np.sin(y * 0.6 + x * 0.05) * 0.06, WOOD))
    out = put(out, cup & (np.abs(cx - 26) < 1.5) & (np.abs(y - 94) < 2), q(np.full((n, n), 0.9), AMBER))
    out = put(out, (y >= 124), q(np.full((n, n), 0.05), WOOD))
    return out


def wall_bar() -> np.ndarray:
    """The bar's other walls (2.4 m): flyers pasted over brick, a dado rail, dark wood panelling to the floor."""
    n = N
    x, y = px.grid(n)
    out = brick_wall(n, rows=20, cols=4, seed=61, grime=0.5, rust=0.2)
    rng = np.random.RandomState(62)
    flyers = [("RAVE", MAGENTA), ("ACID", AMBER), ("PLUR", TEAL), ("DJ", WHITE), ("XTC", MAGENTA), ("4AM", AMBER)]
    spots = [(4, 8), (30, 16), (58, 6), (82, 18), (104, 8), (44, 38)]
    for (word, pal), (fx, fy) in zip(flyers, spots):
        w, h = int(rng.randint(18, 24)), int(rng.randint(22, 28))
        m = rect(n, fx, fy, fx + w, fy + h)
        tear = (px.noise(n, 3, int(fx)) > 0.72) & ((np.abs(x - fx) < 3) | (np.abs(y - fy - h) < 3))
        m &= ~tear
        out = put(out, m, q(0.35 + 0.45 * (y - fy) / h, pal))
        out = put(out, m & text_mask(n, word, fx + 2, fy + 3), q(np.full((n, n), 0.0), CAB))
        circ = m & (np.hypot(x - fx - w * 0.5, y - fy - h * 0.62) < 5)
        out = put(out, circ, q(np.full((n, n), 0.95), pal))
        lines = m & (y > fy + h - 7) & (y % 2 == 0) & (x > fx + 2) & (x < fx + w - 3)
        out = put(out, lines, q(np.full((n, n), 0.05), pal))
    out = put(out, (y >= 70) & (y < 74), q(0.75 - 0.15 * (y - 70), WOOD))
    pan = y >= 74
    px_ = x % 21
    out = put(out, pan, q(0.35 + 0.2 * (px_ < 2) - 0.15 * (px_ > 18) + (px.noise(n, 12, 63) - 0.5) * 0.25 - 0.2 * px.grime(n, 64, 0.5), WOOD))
    out = put(out, (y >= 120), q(np.full((n, n), 0.08), WOOD))
    return out


def wall_door() -> np.ndarray:
    """The street end of the tunnel (3 m a repeat, 2 m high): steel doors propped open on a wet night street under sodium light."""
    n = N
    x, y = px.grid(n)
    out = brick_wall(n, rows=16, cols=6, seed=71, grime=0.7, rust=0.5)
    hole = rect(n, 30, 5, 98, 85)
    sky = 0.05 + 0.75 * np.clip((y - 5) / 50.0, 0, 1) ** 1.5
    street = q(sky, NIGHT)
    stars = (px.speckle(n, 0.012, 72) > 0.5) & (y < 30)
    street = put(street, stars, q(np.full((n, n), 1.0), WHITE))
    bld = ((y > 26 + 10 * ((x // 9) % 3)) & (y < 66)) | ((x > 70) & (x < 86) & (y > 18) & (y < 66))
    street = put(street, bld, q(np.full((n, n), 0.08), NIGHT))
    win = bld & (x % 5 < 2) & (y % 6 < 3) & (px.noise(n, 3, 73) > 0.55)
    street = put(street, win, q(0.6 + 0.4 * px.noise(n, 2, 74), AMBER))
    road = y >= 66
    refl = 0.15 + 0.6 * np.clip(1 - np.abs(x - 64) / 20.0, 0, 1) * (np.sin(y * 1.7) * 0.5 + 0.5) * ((y - 66) / 20.0)
    street = put(street, road, q(refl, px.ramp("#0a0810", "#1a1418", "#3a2414", "#7a4a18", "#c0782c")))
    post = (np.abs(x - 64) < 1) & (y > 26) & (y < 70)
    street = put(street, post, q(np.full((n, n), 0.1), STEEL))
    lamp = ell(n, 64.5, 25, 4, 2.5)
    street = put(street, lamp, q(np.full((n, n), 1.0), AMBER))
    halo = (np.hypot(x - 64, (y - 26) * 1.2) < 14) & ~lamp & ~bld
    street = put(street, halo & dmask(np.clip(1 - np.hypot(x - 64, y - 26) / 14.0, 0, 1) * 0.6), q(np.full((n, n), 0.55), AMBER))
    out = put(out, hole, street)
    for d0, d1 in ((30, 38), (90, 98)):  # the two doors folded back against the reveals
        m = rect(n, d0, 5, d1, 85)
        out = put(out, m, q(0.3 + 0.2 * (x == d0) + (px.noise(n, 5, d0) - 0.5) * 0.3, px.ramp("#141a18", "#22302a", "#30443a", "#46584c")))
    out = put(out, rect(n, 28, 3, 100, 5) | rect(n, 28, 3, 30, 86) | rect(n, 98, 3, 100, 86), q(np.full((n, n), 0.5), STEEL))
    return out


def wall_corridor() -> np.ndarray:
    """The long corridor to the toilets (2.4 m): pipes under the ceiling, grimy painted plaster, a maroon band, white tiles to the floor."""
    n = N
    x, y = px.grid(n)
    g = px.grime(n, 81, 0.8)
    out = q(0.55 - 0.45 * g + (px.noise(n, 10, 82) - 0.5) * 0.3, PAINT)
    scuff = (px.noise(n, 5, 83) > 0.7) & (y > 40)
    out = put(out, scuff, q(np.full((n, n), 0.15), PAINT))
    for y0, y1, pal in ((2, 6, STEEL), (7, 10, RUST)):
        m = (y >= y0) & (y < y1)
        out = put(out, m, q(0.8 - 0.65 * (y - y0) / (y1 - y0), pal))
    out = put(out, ((x % 42) < 2) & (y < 11), q(np.full((n, n), 0.15), STEEL))
    out = put(out, sag(n, 12, 3, 1.2, 0, n), q(np.full((n, n), 0.05), STEEL))
    sh, gr = px.tiles(n, count=16, grout=1, seed=84, gloss=0.25)
    tl = q(sh - 0.5 * g, TILE)
    tl = put(tl, gr > 0.5, q(0.6 - 0.6 * g, GROUT))
    tl = put(tl, dmask(g * 0.9), q(0.6 * np.ones((n, n)), GRIMEP))
    out = put(out, y >= 66, tl)
    out = put(out, (y >= 63) & (y < 66), q(0.4 + 0.3 * (y == 63), LAM))
    return out


def toilet_tile() -> np.ndarray:
    """Toilet walls (1.5 m): glazed tiles gone yellow, black grout, grime running down, a cracked and a missing tile."""
    n = N
    x, y = px.grid(n)
    sh, gr = px.tiles(n, count=8, grout=1, seed=91, gloss=0.35)
    g = px.grime(n, 92, 0.8)
    out = q(sh - 0.45 * g, TILE)
    out = put(out, gr > 0.5, q(0.65 - 0.7 * g, GROUT))
    out = put(out, dmask(g * 0.8) & (gr < 0.5), q(0.5 + 0.5 * px.noise(n, 4, 93), GRIMEP))
    out = put(out, seg(n, 33, 17, 44, 30, 1.0) | seg(n, 44, 30, 40, 31, 1.0), q(np.full((n, n), 0.1), GROUT))
    out = put(out, rect(n, 97, 65, 112, 80), q(0.3 + 0.4 * px.noise(n, 3, 94), MORTAR))
    return out


def toilet_floor() -> np.ndarray:
    """Toilet floor (1.5 m): small black and grey tiles, dirt in the grout, wet patches catching the tube light."""
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
    """The cubicle fronts (2.6 m, floor to ceiling): a dark gap over the partitions, laminate scrawled on, the gap above the floor."""
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
    """The chill-out room (2.6 m): brick painted aubergine, a tie-dye cloth hung from a pole, soft folds and tassels."""
    n = N
    x, y = px.grid(n)
    out = brick_wall(n, rows=18, cols=4, seed=141, pal=PURPLE, grime=0.4, rust=0.0)
    cloth = (x >= 28) & (x < 100) & (y >= 14) & (y < 92 + 3 * np.sin(x * 0.5))
    r = np.hypot(x - 64, (y - 52) * 1.2) + 3 * np.sin(np.arctan2(y - 52, x - 64) * 6)
    band = (r // 6).astype(int) % 4
    fold = 0.15 * np.sin((x - 28) * 0.45)
    col = np.zeros((n, n, 3), np.uint8)
    for i, pal in enumerate((MAGENTA, AMBER, TEAL, px.ramp("#1e0a3a", "#3c1872", "#6a32b0", "#9a5ae0"))):
        layer = q(0.55 + fold + (np.abs((r % 6) - 3) < 1) * 0.15, pal)
        col = put(col, band == i, layer)
    out = put(out, cloth, col)
    out = put(out, (y >= 11) & (y < 14) & (x >= 24) & (x < 104), q(0.8 - 0.25 * (y - 11), WOOD))
    tass = (y >= 92) & (y < 97 + (x % 4)) & (x >= 28) & (x < 100) & (x % 4 == 1)
    out = put(out, tass, q(np.full((n, n), 0.7), AMBER))
    return out


# ---- floors and ceilings ---------------------------------------------------------------------------------------------------------------------------------

def floor_dark() -> np.ndarray:
    """Warehouse concrete (3 m): a power-floated slab, cracks, spilt drinks, gum, a saw-cut joint every 1.5 m."""
    n = N
    x, y = px.grid(n)
    sh = 0.5 + (px.noise(n, 32, 151, 4) - 0.5) * 0.5 + (px.noise(n, 4, 152) - 0.5) * 0.2
    blot = px.noise(n, 20, 153, 4)
    sh = sh - 0.35 * np.clip((blot - 0.58) * 4, 0, 1)
    out = q(sh, CONC)
    crack = (np.abs(px.noise(n, 26, 154, 3) - 0.5) < 0.008)
    out = put(out, crack, q(np.full((n, n), 0.0), CONC))
    joint = ((x % 64) < 1) | ((y % 64) < 1)
    out = put(out, joint, q(np.full((n, n), 0.05), CONC))
    out = put(out, px.speckle(n, 0.006, 155) > 0.5, q(np.full((n, n), 0.9), CONC))
    return out


def floor_boards() -> np.ndarray:
    """The bar's floor (2 m): dark boards, sticky with beer, worn pale along the bar."""
    n = N
    sh, joint = px.planks(n, count=8, seed=161)
    g = px.grime(n, 162, 0.6, drip=False)
    out = q(sh - 0.35 * g, WOOD)
    out = put(out, dmask(np.clip(px.noise(n, 16, 163, 3) - 0.6, 0, 1) * 3), q(np.full((n, n), 0.15), WOOD))
    return out


def floor_carpet() -> np.ndarray:
    """Club carpet (2 m): maroon with amber diamonds, teal squiggles and magenta dots, burnt and worn through in patches."""
    n = N
    x, y = px.grid(n)
    wear = np.clip((px.noise(n, 28, 171, 4) - 0.5) * 2.5, 0, 1)
    out = q(0.5 + (px.noise(n, 3, 172) - 0.5) * 0.4 + 0.3 * wear, CARPET)
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
    """Stage and balcony decking (2 m): steel chequer plate, worn bright on the ridges, a gaffered cable run."""
    n = N
    x, y = px.grid(n)
    lx, ly = x % 8, y % 8
    alt = ((x // 8) + (y // 8)) % 2 == 0
    a = np.where(alt, lx - ly, lx + ly - 7)
    ridge = (np.abs(a) < 1.2) & (np.abs(np.where(alt, lx + ly - 7, lx - ly)) < 4.5)
    sh = 0.45 + (px.noise(n, 16, 181, 3) - 0.5) * 0.35 - 0.25 * px.grime(n, 182, 0.5, drip=False)
    out = q(sh, PLATE)
    out = put(out, ridge, q(sh + 0.3, PLATE))
    out = put(out, ridge & np.roll(ridge == False, -1, 0), q(sh - 0.25, PLATE))  # noqa: E712
    tape = (y >= 88) & (y < 98)
    out = put(out, tape, q(0.25 + 0.1 * (y == 88) + (px.noise(n, 3, 183) - 0.5) * 0.15, CAB))
    out = put(out, (np.abs(y - 93 - 0.0) < 1.6) & tape & (x % 5 < 4), q(np.full((n, n), 0.0), CAB))
    out = put(out, sag(n, 20, 30, 1.6, 0, n), q(np.full((n, n), 0.05), CAB))
    return out


def ceil_truss() -> np.ndarray:
    """The warehouse roof (4 m): black corrugated decking crossed by lattice girders, cables slung between them."""
    n = N
    x, y = px.grid(n)
    out = q(0.35 + 0.25 * np.sin(x * 2 * np.pi / 8) + (px.noise(n, 16, 191) - 0.5) * 0.3, DECK)
    sh, m = px.truss(64, 192)
    band = np.zeros((n, n), np.float32)
    bm = np.zeros((n, n), bool)
    band[32:96, :] = np.tile(sh, (1, 2))
    bm[32:96, :] = np.tile(m, (1, 2)) > 0.5
    shv, mv = sh.T, m.T
    vband = np.zeros((n, n), np.float32)
    vm = np.zeros((n, n), bool)
    vband[:, 32:96] = np.tile(shv, (2, 1))
    vm[:, 32:96] = np.tile(mv, (2, 1)) > 0.5
    out = put(out, vm, q(0.25 + 0.5 * vband, STEEL))
    out = put(out, bm, q(0.35 + 0.55 * band, STEEL))
    cab = sag(n, 8, 10, 1.2, 0, n) | sag(n, 100, 14, 1.2, 0, n)
    out = put(out, cab, q(np.full((n, n), 0.0), STEEL))
    return out


def ceil_low() -> np.ndarray:
    """Low ceilings of the bar, chill-out room and entrance (2 m): black-painted joists over boards, a pipe and a cable."""
    n = N
    x, y = px.grid(n)
    bx = x % 32
    boards = q(0.4 + 0.2 * ((y % 16) < 1) * -1 + (px.noise(n, 8, 201) - 0.5) * 0.3, DECK)
    joist = bx < 9
    out = put(boards, joist, q(0.45 + 0.35 * (bx < 2) - 0.25 * (bx > 6), STEEL))
    pipe = (np.abs(y - 80) < 3)
    out = put(out, pipe, q(0.75 - 0.25 * (y - 77) / 3.0, RUST))
    out = put(out, sag(n, 40, 5, 1.2, 0, n), q(np.full((n, n), 0.0), CAB))
    return out


def ceil_stair() -> np.ndarray:
    """The tunnel's ceiling is the underside of the steel stair (2 m): treads with amber light leaking between them, two stringers."""
    n = N
    x, y = px.grid(n)
    ty = y % 16
    out = q(0.35 + 0.4 * (ty < 3) - 0.2 * (ty > 12) + (px.noise(n, 6, 211) - 0.5) * 0.3, STEEL)
    out = put(out, ty == 14, q(np.full((n, n), 0.85), AMBER))
    out = put(out, dmask(px.rust(n, 212, 0.5) * 0.8), q(px.noise(n, 4, 213) * 0.6, RUST))
    for s0 in (10, 108):
        m = (x >= s0) & (x < s0 + 10)
        out = put(out, m, q(steel_shade(n, s0, s0 + 10, 214), STEEL))
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


SPRITES = {
    "thing_decks": thing_decks, "thing_pendant": thing_pendant, "thing_bulb": thing_bulb, "thing_sink": thing_sink,
    "thing_dryer": thing_dryer, "thing_tube": thing_tube, "thing_toilet": thing_toilet, "thing_firedoor": thing_firedoor, "thing_exit_sign": thing_exit_sign,
    "thing_sofa": thing_sofa, "thing_lavalamp": thing_lavalamp, "thing_bulbs": thing_bulbs, "thing_truss_tower": thing_truss_tower, "thing_bin": thing_bin,
    "thing_rail": thing_rail,
}


def write_sprites(out_dir: str = OUT) -> list:
    os.makedirs(out_dir, exist_ok=True)
    for tid, fn in sorted(SPRITES.items()):
        save_rgba(os.path.join(out_dir, tid + ".png"), fn())
    return sorted(SPRITES)


def build() -> dict:
    """The opaque tiles {id: (rgb, metres)}; the RGBA props are written to the textures folder as a side effect (ids listed in tiles.NIGHT_ONE)."""
    write_sprites()
    return {
        "wall_brick": (wall_brick(), 2.0),
        "wall_panel": (wall_panel(), 3.2),
        "wall_speaker": (wall_speaker(), 2.0),
        "wall_bar": (wall_bar(), 2.4),
        "bar_front": (bar_front(), 2.4),
        "wall_door": (wall_door(), 3.0),
        "trim": (trim(), 2.0),
        "toilet_tile": (toilet_tile(), 1.5),
        "toilet_floor": (toilet_floor(), 1.5),
        "cubicle_door": (cubicle_door(), 2.6),
        "cubicle_wall": (cubicle_wall(), 1.2),
        "wall_corridor": (wall_corridor(), 2.4),
        "wall_chill": (wall_chill(), 2.6),
        "ceil_wc": (ceil_wc(), 1.2),
        "floor_dark": (floor_dark(), 3.0),
        "floor_boards": (floor_boards(), 2.0),
        "floor_carpet": (floor_carpet(), 2.0),
        "floor_stage": (floor_stage(), 2.0),
        "ceil_truss": (ceil_truss(), 4.0),
        "ceil_low": (ceil_low(), 2.0),
        "ceil_stair": (ceil_stair(), 2.0),
    }
