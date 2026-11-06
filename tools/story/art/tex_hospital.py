"""The Hospital's procedural pixel textures (docs/STORY_25D_ART_DIRECTION.md 1 and 2.D): a night ward, blue, with warm corridor spill.

`build()` returns {tile_id: (rgb uint8 (n, n, 3), metres per repeat)} for tools/story/art/tiles.py (`procedural`): an id of a baked tile replaces it, a new one is
added. The billboard props (`thing_*`, RGBA with a cut-out) are written here directly into assets/story/hospital/textures (pixeltex.save writes RGB only) and are
listed with their metres in tiles.HOSPITAL. Everything is drawn in numpy at tile size and posterised with 8x8 ordered dithering; every random value is seeded.

Wall tiles are laid out top-down from the ceiling (StoryWorld maps v = 0 to the top of a wall), so a tile whose metres equal its room's height puts the skirting on
the floor: wall_ward 2.7 (the ward), wall_dayroom 2.2, wall_door and wall_station 2.6 (the corridor), wall_vending_wall and wall_cafe 4.8 (the cafeteria).
"""
from __future__ import annotations

import os

import numpy as np

from . import lib
from . import pixeltex as px

OUT = os.path.join(lib.ROOT, "assets", "story", "hospital", "textures")


# ---- small drawing kit ----------------------------------------------------------------------------------------------------------------------------------

def C(h: str) -> np.ndarray:
    return px.hexc(h)


def dith(img: np.ndarray, levels: int = 22) -> np.ndarray:
    """Float RGB 0..1 -> uint8, posterised per channel with the 8x8 Bayer matrix (the pixel look)."""
    h, w = img.shape[:2]
    b = px.BAYER8[np.arange(h)[:, None] % 8, np.arange(w)[None, :] % 8][..., None]
    v = np.clip(img, 0, 1) * (levels - 1) + b
    return (np.clip(np.round(v), 0, levels - 1) / (levels - 1) * 255 + 0.5).astype(np.uint8)


class Canvas:
    """Float RGBA canvas (rows = y, top down). `k` draws the same picture on a k times finer pixel grid: coordinates stay in the 128-unit design space (x, y are the
    design coordinates of each pixel's centre, so k = 1 is the plain integer grid), the output is n * k pixels square."""

    def __init__(self, n: int, fill=None, k: int = 1):
        self.k = k
        self.base = n
        self.n = n * k
        self.rgb = np.zeros((self.n, self.n, 3), np.float32)
        self.a = np.zeros((self.n, self.n), np.float32)
        if fill is not None:
            self.rgb[:] = C(fill) if isinstance(fill, str) else fill
            self.a[:] = 1.0
        yy, xx = np.mgrid[0:self.n, 0:self.n].astype(np.float32)
        self.x = (xx + 0.5) / k - 0.5
        self.y = (yy + 0.5) / k - 0.5

    def nz(self, scale: float, seed: int, octaves: int = 3) -> np.ndarray:
        """px.noise on the design grid, repeated k times each way (so the grain scales with the picture)."""
        f = px.noise(self.base, scale, seed, octaves)
        return np.kron(f, np.ones((self.k, self.k), np.float32)) if self.k > 1 else f

    def put(self, mask, col, alpha: float = 1.0):
        m = mask.astype(np.float32) * alpha if mask.dtype != np.float32 else mask * alpha
        c = C(col) if isinstance(col, str) else np.asarray(col, np.float32)
        if c.ndim == 1:
            c = c[None, None, :]
        self.rgb = self.rgb * (1 - m[..., None]) + c * m[..., None]
        self.a = np.maximum(self.a, (mask > 0).astype(np.float32) if alpha >= 0.5 else self.a)

    def rect(self, x0, y0, x1, y1, col, alpha: float = 1.0):
        self.put((self.x >= x0) & (self.x < x1) & (self.y >= y0) & (self.y < y1), col, alpha)

    def box(self, x0, y0, x1, y1):
        return (self.x >= x0) & (self.x < x1) & (self.y >= y0) & (self.y < y1)

    def disc(self, cx, cy, r, col, alpha: float = 1.0):
        self.put((self.x - cx) ** 2 + (self.y - cy) ** 2 <= r * r, col, alpha)

    def ring(self, cx, cy, r0, r1, col):
        d = (self.x - cx) ** 2 + (self.y - cy) ** 2
        self.put((d <= r1 * r1) & (d >= r0 * r0), col)

    def glow(self, cx, cy, r, col, k: float = 0.6):
        """Additive soft glow (no alpha change)."""
        d = np.sqrt((self.x - cx) ** 2 + (self.y - cy) ** 2) / r
        g = np.clip(1 - d, 0, 1) ** 2 * k
        self.rgb = self.rgb + C(col)[None, None, :] * g[..., None]

    def line(self, pts, col, w: float = 1.0):
        m = np.zeros((self.n, self.n), bool)
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
            for t in np.linspace(0, 1, steps):
                xx, yy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                m |= (np.abs(self.x - xx) < w * 0.5 + 0.01) & (np.abs(self.y - yy) < w * 0.5 + 0.01)
        self.put(m, col)

    def shade(self, mask, k):
        """Multiply the colour under mask by k (a field or a number)."""
        kk = k if np.ndim(k) else np.full((self.n, self.n), k, np.float32)
        self.rgb = np.where(mask[..., None], self.rgb * kk[..., None], self.rgb)

    def rgb8(self, levels: int = 22) -> np.ndarray:
        return dith(self.rgb, levels)

    def rgba8(self, levels: int = 22) -> np.ndarray:
        out = np.zeros((self.n, self.n, 4), np.uint8)
        out[..., :3] = dith(self.rgb, levels)
        out[..., 3] = np.where(self.a >= 0.5, 255, 0).astype(np.uint8)
        return out


def save_rgba(tid: str, rgba: np.ndarray) -> None:
    from PIL import Image
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, tid + ".png"), optimize=False, compress_level=9)


def lerpc(a: str, b: str, t):
    t = np.asarray(t, np.float32)[..., None]
    return C(a) * (1 - t) + C(b) * t


# ---- surfaces -------------------------------------------------------------------------------------------------------------------------------------------
# Every surface is a 128 px tile over 1.0 to 1.3 m (98 to 128 texels a metre; the style guide asks for 96 to 160): one texel is about one internal pixel at 3 m, the grain of the
# baked people. A tile that small repeats often and a wall tile repeats up the wall too (StoryWorld lays v from the ceiling down), so no tile carries a single landmark: the
# architecture is periodic (rails, panes, panels, chevrons), and the landmarks that matter (doors, machines, the TV, the windows) are stage sprites or other props.

CEIL = px.ramp("#1c2440", "#262f4e", "#303b5e", "#3b4870", "#485682")


def q(shade, pal, dither: float = 1.0):
    return px.quantise(np.asarray(shade, np.float32), pal, dither)


def put(base, mask, layer):
    out = base.copy()
    m = np.asarray(mask, bool)
    layer = np.asarray(layer, np.uint8)
    out[m] = np.broadcast_to(layer, out.shape)[m]
    return out


def col8(h: str) -> np.ndarray:
    return (px.hexc(h) * 255 + 0.5).astype(np.uint8)


def box(n, x0, y0, x1, y1):
    y, x = np.mgrid[0:n, 0:n]
    return (x >= x0) & (x < x1) & (y >= y0) & (y < y1)


def ceil_tile() -> np.ndarray:
    """Suspended ceiling, 2 x 2 tiles of 0.64 m a repeat: speckled mineral tiles, a T-bar grid, one louvred panel (cold and dim at night), one smoke detector."""
    n = 128
    x, y = px.grid(n)
    sh = 0.5 + (px.noise(n, 6, 41) - 0.5) * 0.4 + (px.speckle(n, 0.12, 42) - px.speckle(n, 0.12, 43)) * 0.2
    out = q(sh, CEIL)
    lx, ly = x % 64, y % 64
    out = put(out, (lx < 1) | (ly < 1), col8("#141a30"))
    out = put(out, (lx == 1) | (ly == 1), col8("#4a5886"))
    out = put(out, (lx == 62) | (ly == 62), col8("#1e2644"))
    pan = box(n, 8, 8, 56, 56)
    shp = 0.55 + 0.25 * (((y - 8) % 6) < 2) - 0.2 * (((y - 8) % 6) >= 4)
    out = put(out, pan, q(shp, px.ramp("#41547c", "#56709c", "#6d8ac0", "#8aa8d8")))
    out = put(out, pan & ((x - 8) % 24 == 0), col8("#34456a"))
    out = put(out, box(n, 7, 7, 57, 8) | box(n, 7, 56, 57, 57) | box(n, 7, 7, 8, 57) | box(n, 56, 7, 57, 57), col8("#202843"))
    d = np.hypot(x - 96, y - 96)
    out = put(out, d <= 6, col8("#aab4cc"))
    out = put(out, d <= 4.2, col8("#6e7894"))
    out = put(out, d <= 1.6, col8("#e8eef8"))
    out = put(out, (np.abs(x - 99.5) < 0.9) & (np.abs(y - 93) < 0.9), col8("#ff5a4a"))
    return out


def lino(base: str, light: str, seam: int, seed: int, sheen: float = 0.2, fleck: str = "#5a70a8", two: tuple | None = None) -> np.ndarray:
    """Sheet vinyl tiles, 128 px over 1.28 m: a mottle, welded seams every `seam` px, flecks and a soft diagonal sheen that tiles."""
    n = 128
    x, y = px.grid(n)
    b = px.hexc(base)
    shade = 0.5 + (px.noise(n, 12, seed, 4) - 0.5) * 0.5
    if two:
        ch = px.checker(n, n // seam)
        cols = np.where(ch[..., None] > 0.5, px.hexc(two[1])[None, None], px.hexc(two[0])[None, None])
    else:
        cols = np.broadcast_to(b, (n, n, 3))
    rgb = cols * (0.7 + 0.6 * shade)[..., None]
    rgb = np.where(px.speckle(n, 0.05, seed + 1)[..., None] > 0, rgb * 0.6 + px.hexc(fleck) * 0.4, rgb)
    rgb = np.where(px.speckle(n, 0.03, seed + 2)[..., None] > 0, rgb * 0.5, rgb)
    s = (np.cos(2 * np.pi * (x + y * 0.5) / n) * 0.5 + 0.5) ** 6
    s2 = (np.cos(2 * np.pi * (x * 2 - y) / n + 1.3) * 0.5 + 0.5) ** 10
    rgb = rgb + px.hexc(light)[None, None, :] * (s * sheen + s2 * sheen * 0.5)[..., None]
    sm = (x % seam < 1) | (y % seam < 1)
    rgb = np.where(sm[..., None], rgb * 0.45, rgb)
    sm2 = (x % seam == 1) | (y % seam == 1)  # the lit lip of the seam, upper left light
    rgb = np.where(sm2[..., None], np.clip(rgb * 1.18, 0, 1), rgb)
    return dith(rgb, 26)


def floor_cafe() -> np.ndarray:
    """Cafeteria floor: glazed tiles 0.32 m square, teal and slate at night, a wet shine."""
    n = 128
    x, y = px.grid(n)
    ch = px.checker(n, 4)
    rgb = np.where(ch[..., None] > 0.5, px.hexc("#1e3a4c")[None, None], px.hexc("#4a5878")[None, None])
    rgb = rgb * (0.82 + 0.3 * px.noise(n, 10, 141))[..., None]
    s = (np.cos(2 * np.pi * (x + y) / n) * 0.5 + 0.5) ** 6
    rgb = rgb + px.hexc("#7a9ac8")[None, None] * (s * 0.2)[..., None]
    lx, ly = x % 32, y % 32
    rgb = np.where(((lx < 1) | (ly < 1))[..., None], px.hexc("#141c30")[None, None] * 0.9, rgb)
    rgb = np.where(((lx == 1) | (ly == 1))[..., None], np.clip(rgb * 1.2, 0, 1), rgb)
    rgb = np.where((px.speckle(n, 0.04, 142) > 0)[..., None], rgb * 0.6, rgb)
    return dith(rgb, 26)


def floor_stone() -> np.ndarray:
    """Garden flagstones under the moon (0.43 x 0.64 m a stone), moss and grass in the joints, each stone its own tone and a lit edge."""
    n = 128
    sh, mort = px.bricks(n, 3, 2, 2, 171, 0.5)
    sh = np.clip(sh * 0.9 + 0.05 + (px.speckle(n, 0.1, 175) - px.speckle(n, 0.1, 176)) * 0.12, 0, 1)
    out = q(sh, px.ramp("#1e2434", "#2a3246", "#384258", "#48546c", "#5c6a84"))
    moss = (mort > 0.5) | ((px.noise(n, 5, 172) > 0.74) & (px.grime(n, 173, 0.6, False) > 0.3))
    out = put(out, moss, q(0.3 + px.noise(n, 3, 177) * 0.5, px.ramp("#10241e", "#16302a", "#22402e", "#2e5238")))
    out = put(out, moss & (px.speckle(n, 0.3, 174) > 0), col8("#2a4a3a"))
    return out


def floor_wood() -> np.ndarray:
    """Pine boards 0.16 m wide over a repeat of 1.28 m, each board its own tone, grain and a staggered joint (the old baked crop was a 2D rug)."""
    n = 128
    x, y = px.grid(n)
    cnt = 8
    s = n / cnt
    r = np.floor(y / s).astype(int)
    rng = np.random.RandomState(181)
    off = (rng.rand(cnt) * n).astype(int)
    tone = rng.rand(cnt)
    jx = (x.astype(int) + off[r]) % n
    joint = ((y % s) < 1) | (jx < 1)
    grain = np.sin(x * 0.35 + px.noise(n, 12, 182) * 7.0 + r * 1.7) * 0.5 + 0.5
    sh = 0.35 + 0.25 * tone[r] + 0.12 * grain + (px.noise(n, 6, 183) - 0.5) * 0.2 - 0.3 * joint + 0.12 * (((y % s) >= 1) & ((y % s) < 2.5))
    return q(np.clip(sh, 0, 1), px.ramp("#1c1626", "#2c2234", "#3e3040", "#544250", "#6c5662"))


def _bands(n, rail_y, top_pal, bot_pal, seed, seam_top=64, seam_bot=64, grain=0.25):
    """The wall of a corridor: paint above a rail, a dado below it, panel joints; periodic in both directions (the rail repeats every 1.3 m up the wall)."""
    x, y = px.grid(n)
    top = y < rail_y
    shp = 0.5 + (px.noise(n, 14, seed) - 0.5) * grain * 2 + (px.speckle(n, 0.08, seed + 1) - px.speckle(n, 0.08, seed + 2)) * 0.14
    shp = shp - 0.12 * (x % seam_top < 1.5) + 0.08 * ((x % seam_top >= 1.5) & (x % seam_top < 3))
    shb = 0.5 + (px.noise(n, 9, seed + 3) - 0.5) * grain * 2 + (px.speckle(n, 0.08, seed + 4) - px.speckle(n, 0.08, seed + 5)) * 0.14
    shb = shb - 0.14 * (x % seam_bot < 1.5) + 0.07 * ((x % seam_bot >= 1.5) & (x % seam_bot < 3))
    scuff = (px.grime(n, seed + 6, 0.8, False) > 0.42) & ~top
    shb = np.where(scuff, shb - 0.22, shb)
    return np.where(top[..., None], q(shp, top_pal), q(shb, bot_pal))


def wall_door() -> np.ndarray:
    """The corridor wall (1.3 m a repeat, 2 up the 2.6 m wall): pale paint over a teal dado, a bumper rail at 0.9 m and a picture rail at 2.2 m, panel joints."""
    n = 128
    x, y = px.grid(n)
    out = _bands(n, 39, px.ramp("#232e4c", "#2c3858", "#364466", "#415076", "#4e5e88"), px.ramp("#142a36", "#1c3a48", "#264a5a", "#325c6e", "#406e80"), 91, 64, 64)
    out = put(out, (y >= 36) & (y < 39), col8("#1a2238"))
    out = put(out, (y >= 39) & (y < 45), q(0.45 + 0.4 * (y < 41) - 0.35 * (y >= 43), px.ramp("#3a465c", "#6a7894", "#8a96b4", "#aab4cc")))
    out = put(out, (y >= 45) & (y < 47), col8("#0e1426"))
    return out


def wall_station() -> np.ndarray:
    """The nurses' station walls (1.3 m): warm purple paint, a wooden slat dado lit by the station lamps, a rail."""
    n = 128
    x, y = px.grid(n)
    out = _bands(n, 39, px.ramp("#2a1a38", "#3a2448", "#4a2e5a", "#5c3a6e", "#6e4a82"), px.ramp("#20142a", "#2e1c3a", "#3c2848", "#4c3458", "#5a4068"), 101, 64, 32, 0.2)
    slat = ((x % 16) < 1.5)
    wood = 0.45 + 0.25 * (np.floor(x / 16) % 3) / 2.0 + 0.1 * np.sin(y * 0.5 + x * 0.1) + (px.noise(n, 8, 105) - 0.5) * 0.15
    wood = np.where(slat, 0.1, wood)
    out = put(out, y >= 47, q(np.clip(wood, 0, 1), px.ramp("#2a1a1e", "#4a2c26", "#6e4632", "#8c5e3e", "#a8764a")))
    out = put(out, (y >= 39) & (y < 45), q(0.4 + 0.45 * (y < 41) - 0.3 * (y >= 43), px.ramp("#4a2a30", "#8a5a62", "#c48a82", "#e8b8a0")))
    out = put(out, (y >= 45) & (y < 47), col8("#180e16"))
    return out


def wall_quiet() -> np.ndarray:
    """The quiet corridor (1.2 m a repeat, 2 up the 2.4 m wall): pale panels gone grey-blue in the dark, a timber handrail, a scuffed dado."""
    n = 128
    x, y = px.grid(n)
    out = _bands(n, 44, px.ramp("#2a3650", "#344260", "#3e4e6e", "#4a5a7c", "#58698c"), px.ramp("#1c2638", "#26324a", "#303e58", "#3c4c68", "#485a78"), 181, 64, 64, 0.3)
    out = put(out, (y >= 40) & (y < 44), col8("#202b42"))
    out = put(out, (y >= 44) & (y < 50), q(0.35 + 0.5 * (y < 46) - 0.3 * (y >= 48), px.ramp("#3a2e24", "#6a5a44", "#8e7a5c", "#b09a76")))
    out = put(out, (y >= 50) & (y < 52), col8("#0e141f"))
    return out


def wall_ward() -> np.ndarray:
    """The ward (1.3 m a repeat, 2 up the 2.7 m wall): the reference's colour blocks stacked in one column, a calm strip, a mosaic of large triangles, all dimmed toward the
    night's blue so the wall stays a backdrop for the beds and people."""
    n = 128
    x, y = px.grid(n)
    out = q(0.5 + (px.noise(n, 14, 51) - 0.5) * 0.3 + (px.speckle(n, 0.08, 52) - px.speckle(n, 0.08, 53)) * 0.12, px.ramp("#1e2946", "#283454", "#324064", "#3c4c74", "#485a84"))
    veil = px.hexc("#2c3a60")
    blocks = ["#7a6a2e", "#6e2c38", "#2a5a60", "#4e5878"]
    bi = (y // 32).astype(int) % 4
    colmask = x < 36
    for i, hexv in enumerate(blocks):
        ly = y % 32
        sh = 0.55 + (px.noise(n, 8, 54 + i) - 0.5) * 0.25 + 0.18 * (ly < 2) - 0.2 * (ly > 29) - 0.1 * (x < 2) + 0.1 * ((x > 2) & (x < 4))
        r0 = px.hexc(hexv) * 0.82 + veil * 0.12
        pal = np.stack([r0 * 0.55, r0 * 0.75, r0 * 0.9, r0 * 1.05, np.clip(r0 * 1.25, 0, 1)])
        out = put(out, colmask & (bi == i), q(np.clip(sh, 0, 1), pal))
    out = put(out, colmask & (y % 32 < 1), col8("#10162a"))
    out = put(out, x == 36, col8("#10162a"))
    out = put(out, x == 37, col8("#46547c"))
    pal_t = ["#5e2c3c", "#2a5258", "#6a5e30", "#443a68", "#2e4672", "#3a4662", "#503a5a", "#2c5e54"]
    mx0, cs = 64, 32
    lx, ly = (x - mx0) % cs, y % cs
    gi, gj = np.floor((x - mx0) / cs).astype(int), np.floor(y / cs).astype(int)
    up = np.where((gi + gj) % 2 == 0, lx > ly, lx + ly < cs)
    idx = (gi * 7 + gj * 13 + up.astype(int) * 3) % len(pal_t)
    inside = x >= mx0
    cols = np.stack([px.hexc(c) * 0.85 + veil * 0.1 for c in pal_t])
    shade = (0.8 + 0.3 * px.noise(n, 8, 53) + 0.1 * (lx + ly < 3))[..., None]
    out = put(out, inside, dith(np.clip(cols[idx] * shade, 0, 1), 20))
    edge = inside & (((lx == ly) & up) | ((lx + ly == cs - 1) & ~up) | (lx == 0) | (ly == 0))
    out = put(out, edge, col8("#1a2038"))
    out = put(out, (x == 127) | (x == mx0), col8("#10162a"))
    return out


def wall_dayroom() -> np.ndarray:
    """The day room (1.1 m a repeat, 2 up the 2.2 m wall): chevron wallpaper in four dimmed warm and teal bands."""
    n = 128
    x, y = px.grid(n)
    zz = (np.abs((x % 32) - 16) + y) % 32
    band = np.floor(zz / 8).astype(int)
    idx = (band + np.floor(x / 32).astype(int)) % 4
    out = np.zeros((n, n, 3), np.uint8)
    for i, hexv in enumerate(("#7a5a2e", "#2a5a60", "#6e3442", "#3a4a7a")):
        b = px.hexc(hexv)
        pal = np.stack([b * 0.5, b * 0.7, b * 0.85, b * 1.0, np.clip(b * 1.2, 0, 1)])
        sh = 0.5 + (px.noise(n, 7, 62 + i) - 0.5) * 0.35 + 0.18 * ((zz % 8) < 1.5) - 0.2 * ((zz % 8) > 6) + (px.speckle(n, 0.1, 66 + i) - px.speckle(n, 0.1, 70 + i)) * 0.14
        out = put(out, idx == i, q(np.clip(sh, 0, 1), pal))
    return put(out, (zz % 8) < 0.7, col8("#161c34"))


def _pane(n, x0, y0, x1, y1, seed, stars=7, blind=0.0):
    """A night window pane: deep indigo glass, a few pixel stars, a moonlit reflection streak, venetian blinds drawn `blind` of the way down."""
    x, y = px.grid(n)
    pane = box(n, x0, y0, x1, y1)
    t = np.clip((y - y0) / max(y1 - y0, 1), 0, 1)
    sh = 0.25 + 0.55 * t + (px.noise(n, 18, seed) - 0.5) * 0.18
    out = q(sh, px.ramp("#050c22", "#0a163a", "#10224e", "#1a3266", "#284480"))
    rng = np.random.RandomState(seed)
    st = np.zeros((n, n), bool)
    for _ in range(stars):
        sx, sy = rng.randint(x0 + 2, x1 - 2), rng.randint(y0 + 2, y0 + (y1 - y0) // 2)
        st[sy, sx] = True
    refl = (np.abs(((x - x0) * 1.0 + (y - y0) * 0.7) % 40 - 8) < 2.2) & pane
    out = put(out, refl, col8("#243a70"))
    out = put(out, st & pane, col8("#d8e2ff"))
    if blind > 0:
        by = y0 + (y1 - y0) * blind
        ph = (y - y0) % 4
        out = put(out, pane & (y < by), q(0.35 + 0.35 * (ph < 2) + 0.2 * (ph == 0), px.ramp("#34426a", "#4a5a88", "#6a7eae", "#8aa0cc")))
        out = put(out, box(n, x0, int(by) - 1, x1, int(by) + 2), col8("#aebcdc"))
    return out, pane


def wall_window() -> np.ndarray:
    """The ward's window wall (1.3 m a repeat, 2 up the wall): two panes 0.4 m wide in a pale frame, one with its blind drawn most of the way."""
    n = 128
    out = q(0.5 + (px.noise(n, 14, 71) - 0.5) * 0.3, px.ramp("#1e2946", "#283454", "#324064", "#3c4c74"))
    fr = col8("#5a6a90")
    for (x0, x1, bl, seed) in ((10, 58, 0.7, 72), (70, 118, 0.0, 73)):
        pane_img, pane = _pane(n, x0, 6, x1, 122, seed, 8, bl)
        out = put(out, pane, pane_img)
        out = put(out, box(n, x0 - 4, 2, x1 + 4, 6) | box(n, x0 - 4, 122, x1 + 4, 126) | box(n, x0 - 4, 2, x0, 126) | box(n, x1, 2, x1 + 4, 126), fr)
        out = put(out, box(n, x0 - 4, 2, x1 + 4, 3) | box(n, x0 - 4, 2, x0 - 3, 126), col8("#8a9ac0"))
        out = put(out, box(n, x0 - 4, 125, x1 + 4, 126) | box(n, x1 + 3, 2, x1 + 4, 126), col8("#26304c"))
    return out


def wall_cafe() -> np.ndarray:
    """The cafeteria's glazed wall (1.3 m a repeat, 3.7 up the 4.8 m wall): one broad pane per repeat in a teal-grey frame, night and stars behind it."""
    n = 128
    out = q(0.5 + (px.noise(n, 14, 131) - 0.5) * 0.3, px.ramp("#1c2844", "#26335a", "#304068", "#3a4c78"))
    pane_img, pane = _pane(n, 6, 6, 124, 122, 132, 12, 0.0)
    out = put(out, pane, pane_img)
    fr = col8("#5c7690")
    out = put(out, box(n, 0, 0, 128, 6) | box(n, 0, 122, 128, 128) | box(n, 0, 0, 6, 128) | box(n, 124, 0, 128, 128), fr)
    out = put(out, box(n, 0, 0, 128, 1) | box(n, 0, 0, 1, 128), col8("#9ab4c8"))
    out = put(out, box(n, 0, 127, 128, 128) | box(n, 127, 0, 128, 128), col8("#243444"))
    out = put(out, box(n, 62, 6, 66, 122), fr)
    return out


def wall_vending() -> np.ndarray:
    """The cafeteria's back wall (1.28 m a repeat): glazed wall tiles 0.16 m, cream-blue with a teal accent course; the lit machines stand in front of it."""
    n = 128
    t_sh, g = px.tiles(n, 8, 1, 134, 0.3)
    course = (np.floor(np.mgrid[0:n, 0:n][0] / 16).astype(int) % 4) == 3
    base = np.where(course[..., None], px.hexc("#1f6a72")[None, None], px.hexc("#6a7ea8")[None, None])
    out = dith(base * (0.3 + 0.55 * t_sh)[..., None], 22)
    return put(out, g > 0.5, col8("#141c30"))


def wall_vending_wall() -> np.ndarray:
    """The same tiled wall in the machines' glow (the swap frame): warmer and a little lighter."""
    n = 128
    t_sh, g = px.tiles(n, 8, 1, 134, 0.3)
    course = (np.floor(np.mgrid[0:n, 0:n][0] / 16).astype(int) % 4) == 3
    base = np.where(course[..., None], px.hexc("#2a8a92")[None, None], px.hexc("#8a96b8")[None, None])
    out = dith(base * (0.34 + 0.6 * t_sh)[..., None], 22)
    return put(out, g > 0.5, col8("#1c2640"))


def wall_tv() -> np.ndarray:
    """The TV alcove wallpaper (1.3 m a repeat): soft vertical stripes with a diamond sprig, deep blue."""
    n = 128
    x, y = px.grid(n)
    st = (x % 16) < 8
    sh = 0.42 + 0.08 * st + (px.noise(n, 12, 191) - 0.5) * 0.2 + (px.speckle(n, 0.08, 192) - px.speckle(n, 0.08, 193)) * 0.1
    out = q(np.clip(sh, 0, 1), px.ramp("#1a2244", "#232d58", "#2c386a", "#36447c", "#42528e"))
    d = np.abs(((x + 8) % 32) - 16) + np.abs(((y + 8) % 32) - 16)
    out = put(out, d < 3, col8("#5a6aa0"))
    return put(out, (d >= 3) & (d < 4), col8("#1a2244"))


def wall_tv_wall() -> np.ndarray:
    """The alcove wallpaper under the screen's glow (the swap frame): the same pattern lit blue."""
    out = wall_tv().astype(np.float32) * np.array([0.92, 1.04, 1.16], np.float32) + np.array([4, 8, 14], np.float32)
    return np.clip(out, 0, 255).astype(np.uint8)


def wall_counter() -> np.ndarray:
    """A wooden counter front, 1 m square (cafeteria serving counter, the TV shelf): a lit lip, three raised panels, a dark kick."""
    n = 128
    x, y = px.grid(n)
    grain = np.sin(y * 0.55 + px.noise(n, 12, 112) * 7.0) * 0.5 + 0.5
    sh = 0.42 + 0.14 * grain + (px.noise(n, 7, 111) - 0.5) * 0.25
    out = q(np.clip(sh, 0, 1), px.ramp("#2a1a12", "#44301e", "#5e4228", "#7a5a38", "#946e46"))
    out = put(out, y < 12, q(0.5 + 0.3 * (y < 4) - 0.2 * (y > 9), px.ramp("#7a5a38", "#a88458", "#c8a878", "#e0c498")))
    out = put(out, (y >= 12) & (y < 16), col8("#1c120c"))
    for x0 in (4, 44, 84):
        pan = box(n, x0, 24, x0 + 38, 108)
        ps = 0.3 + 0.14 * grain + (px.noise(n, 7, 113) - 0.5) * 0.2 + 0.14 * (y < 27)
        out = put(out, pan, q(np.clip(ps, 0, 1), px.ramp("#241610", "#36241a", "#4c3624", "#654a32")))
        out = put(out, box(n, x0, 24, x0 + 38, 25) | box(n, x0, 24, x0 + 1, 108), col8("#a07a50"))
        out = put(out, box(n, x0, 107, x0 + 38, 108) | box(n, x0 + 37, 24, x0 + 38, 108), col8("#140c08"))
    return put(out, y >= 112, col8("#18100c"))


def wall_curtain() -> np.ndarray:
    """The privacy curtain round the bed (1.3 m a repeat): soft folds in hospital blue, four to a repeat, the weave."""
    n = 128
    x, y = px.grid(n)
    fold = 0.5 + 0.34 * np.sin(2 * np.pi * x / 32) + 0.1 * np.sin(2 * np.pi * x / 16 + 0.7) + (px.noise(n, 12, 81) - 0.5) * 0.14
    fold = fold + 0.04 * np.sin(2 * np.pi * y / 8)
    return q(np.clip(fold, 0, 1), px.ramp("#102238", "#1a3250", "#264668", "#366080", "#4c7c9c"))


def wall_brick() -> np.ndarray:
    """The hospital seen from the garden (1.28 m a repeat): moonlit plum brick in courses of 0.08 m, one dark window per repeat with the moon in it, a stone sill."""
    n = 128
    sh, mort = px.bricks(n, 16, 6, 1, 151, 0.4)
    sh = np.clip(sh + (px.speckle(n, 0.1, 152) - px.speckle(n, 0.1, 153)) * 0.14, 0, 1)
    out = q(sh, px.ramp("#1e1828", "#2c2236", "#3a2c44", "#4a3a54", "#5c4a66"))
    out = put(out, mort > 0.5, col8("#141826"))
    x0, y0, x1, y1 = 34, 20, 94, 90
    out = put(out, box(n, x0 - 3, y0 - 3, x1 + 3, y1 + 3), col8("#6a6a7e"))
    glass, pane = _pane(n, x0, y0, x1, y1, 154, 4, 0.0)
    out = put(out, pane, glass)
    x, y = px.grid(n)
    lamp = pane & (y > y0 + 28)  # a bedside lamp behind the curtain: the lower half of the pane glows amber, the curtain edges stay dark
    t = np.clip((y - y0 - 28) / (y1 - y0 - 28), 0, 1)
    warm = q(0.25 + 0.6 * t + (px.noise(n, 10, 155) - 0.5) * 0.15, px.ramp("#1a1218", "#3a2418", "#6a4226", "#a46a34", "#d49a54"))
    out = put(out, lamp & (x > x0 + 6) & (x < x1 - 6), warm)
    out = put(out, lamp & ((x <= x0 + 6) | (x >= x1 - 6)), q(0.3 + 0.2 * (px.noise(n, 6, 156)), px.ramp("#10142a", "#1a2040", "#262e58")))
    out = put(out, box(n, x0 + 28, y0, x0 + 32, y1) | box(n, x0, y0 + 30, x1, y0 + 34), col8("#6a6a7e"))
    out = put(out, box(n, x0 - 6, y1 + 3, x1 + 6, y1 + 8), col8("#8a8a9c"))
    out = put(out, box(n, x0 - 6, y1 + 8, x1 + 6, y1 + 9), col8("#1a1c2c"))
    return put(out, box(n, x0 + 6, y0 + 6, x0 + 10, y0 + 10), col8("#9ab0e0"))


def wall_hedge() -> np.ndarray:
    """A clipped yew hedge (1.3 m a repeat): leaf clusters in five greens, a cut-flat sheen, shadow in the depths."""
    n = 128
    lv = px.noise(n, 5, 163, 3)
    lf = (px.speckle(n, 0.18, 165) - px.speckle(n, 0.18, 166)) * 0.18
    out = q(np.clip(lv * 0.85 + 0.12 + lf, 0, 1), px.ramp("#08141a", "#0e2228", "#163232", "#20443e", "#305a50"))
    return put(out, px.speckle(n, 0.03, 164) > 0, col8("#4a7a78"))


def trim() -> np.ndarray:
    """A step edge (1.0 m a repeat): a worn nosing strip on top, a dark riser with a kick line."""
    n = 128
    x, y = px.grid(n)
    sh = 0.4 + (px.noise(n, 8, 201) - 0.5) * 0.4 + (px.speckle(n, 0.06, 202) - px.speckle(n, 0.06, 203)) * 0.12
    out = q(np.clip(sh, 0, 1), px.ramp("#141a2e", "#1e2640", "#2a3452", "#36425e"))
    out = put(out, y < 9, q(0.4 + 0.45 * (y < 3) - 0.2 * (y > 6), px.ramp("#4a5878", "#6a789c", "#8a98b8", "#b0bcd4")))
    out = put(out, (y >= 9) & (y < 12), col8("#0a0e1c"))
    return put(out, (y > 60) & (y < 62), col8("#0e1424"))


def sky_night() -> np.ndarray:
    """The 256 x 64 sky strip kept for the tile list (the map's sky is the wider processed/sky_night_wide.png from hp_pix): one moon, pixel stars, a tree line."""
    from . import hp_pix
    return hp_pix.sky_strip(256, 64, 211, ((128, 15),))


# ---- billboards (RGBA) ----------------------------------------------------------------------------------------------------------------------------------

def th_monitor(k: int = 1) -> np.ndarray:
    """A bedside heart monitor on its pole: grey casing, a dark screen with the green trace, numbers, a pump module below."""
    c = Canvas(128, k=k)
    c.rect(36, 10, 96, 54, "#7a8498")
    c.rect(36, 10, 96, 12, "#a8b2c4")
    c.rect(94, 12, 96, 54, "#4a5266")
    c.rect(40, 14, 84, 46, "#03100a")
    trace = [(40, 30), (47, 30), (49, 28), (51, 30), (54, 30), (56, 18), (58, 38), (60, 30), (66, 30), (68, 27), (71, 30), (76, 30), (78, 20), (80, 36), (82, 30), (84, 30)]
    c.line(trace, "#5aff96", 1.2)
    c.rect(40, 38, 84, 39, "#2a8a5a")
    c.line([(40, 42), (50, 41), (60, 43), (70, 41), (84, 42)], "#3ab0e0", 1.0)
    c.rect(86, 16, 93, 20, "#5aff96")
    c.rect(86, 23, 93, 27, "#5aff96")
    c.rect(86, 30, 93, 33, "#ffd060")
    c.rect(86, 36, 93, 39, "#60c0ff")
    for k in range(4):
        c.rect(42 + k * 6, 48, 46 + k * 6, 51, "#2a3040")
    c.rect(78, 48, 81, 51, "#5aff96")
    c.rect(84, 48, 87, 51, "#ffb040")
    c.rect(62, 54, 68, 128, "#8a94a8")
    c.rect(62, 54, 63, 128, "#c0c8d8")
    c.rect(50, 70, 80, 92, "#6a7488")
    c.rect(52, 72, 66, 84, "#0a1a12")
    c.rect(53, 74, 64, 76, "#60ff90")
    c.rect(53, 79, 60, 81, "#60ff90")
    c.rect(68, 74, 78, 77, "#c8ccd8")
    c.line([(80, 80), (90, 86), (96, 100), (98, 128)], "#5a6478", 1.0)
    c.rect(48, 122, 82, 126, "#3a4050")
    return c.rgba8()


def th_bed(k: int = 1) -> np.ndarray:
    """A hospital bed side-on: head and foot boards, half rails, a blanket over the mattress, a pillow, wheels. Fills the lower half."""
    c = Canvas(128, k=k)
    c.rect(4, 58, 11, 106, "#9aa4b8")
    c.rect(5, 62, 10, 90, "#2e4a7a")
    c.rect(117, 70, 124, 106, "#9aa4b8")
    c.rect(118, 74, 123, 92, "#2e4a7a")
    c.rect(11, 84, 117, 94, "#d8e0ec")
    c.rect(10, 76, 34, 86, "#eef2f8")
    c.rect(10, 84, 34, 86, "#b8c4d8")
    bl = c.box(30, 80, 116, 100) & (c.y >= 80 + 2 * np.sin((c.x - 30) / 9.0))
    c.put(bl, "#5a7ab8")
    c.put(bl & (c.y < 83 + 2 * np.sin((c.x - 30) / 9.0)), "#7a9ad0")
    c.put(bl & ((np.floor(c.x + 0.5).astype(int) % 12) == 0), "#4a6aa0")
    c.rect(36, 76, 104, 78, "#c8d0dc")
    c.rect(36, 78, 38, 88, "#c8d0dc")
    c.rect(102, 78, 104, 88, "#c8d0dc")
    c.rect(36, 86, 104, 87, "#8a94a8")
    c.rect(8, 100, 120, 106, "#4a5266")
    c.rect(8, 100, 120, 101, "#8a94a8")
    for wx in (16, 112):
        c.rect(wx - 1, 106, wx + 2, 116, "#5a6478")
        c.disc(wx, 119, 4.5, "#1e2230")
        c.disc(wx, 119, 1.6, "#8a94a8")
    return c.rgba8()


def th_drip(k: int = 1) -> np.ndarray:
    """A drip stand: a bag of fluid on the hook, the line down, a five-legged base on castors."""
    c = Canvas(128, k=k)
    c.rect(63, 8, 66, 120, "#a8b2c4")
    c.rect(63, 8, 64, 120, "#d8e0ec")
    c.rect(48, 7, 82, 9, "#a8b2c4")
    c.rect(48, 9, 50, 13, "#a8b2c4")
    c.rect(42, 13, 56, 38, "#c8e4f0")
    c.rect(43, 22, 55, 37, "#8ac8e0")
    c.rect(42, 13, 56, 15, "#e8f4fa")
    c.rect(48, 38, 50, 44, "#c8e4f0")
    c.line([(49, 44), (52, 70), (58, 96), (54, 128)], "#a8d0e0", 1.0)
    c.rect(66, 70, 76, 84, "#5a6478")
    c.rect(68, 72, 74, 76, "#60ff90")
    c.line([(64, 118), (44, 124)], "#8a94a8", 2.0)
    c.line([(65, 118), (86, 124)], "#8a94a8", 2.0)
    c.line([(64, 119), (64, 125)], "#8a94a8", 2.0)
    for wx in (44, 64, 86):
        c.disc(wx, 125, 2.2, "#1e2230")
    return c.rgba8()


def th_desk(k: int = 1) -> np.ndarray:
    """The nurses' station desk: a warm wooden front, a lit counter top, a computer screen, a lamp, files."""
    c = Canvas(128, k=k)
    c.rect(2, 52, 126, 58, "#e8c890")
    c.rect(2, 57, 126, 59, "#5a3a20")
    front = c.box(4, 59, 124, 120)
    c.put(front, "#a87444")
    c.rgb = np.where(front[..., None], c.rgb * (0.82 + 0.3 * c.nz(6, 221))[..., None] + (np.sin(c.y * 0.8) * 0.03)[..., None], c.rgb)
    for x0 in (8, 48, 88):
        c.rect(x0, 66, x0 + 34, 112, "#8a5c34")
        c.rect(x0, 66, x0 + 34, 67, "#c89a64")
    c.rect(4, 120, 124, 126, "#2a1a10")
    c.rect(82, 26, 112, 48, "#141820")
    c.rect(84, 28, 110, 46, "#8ac8f0")
    c.rect(84, 28, 110, 31, "#c8e8ff")
    c.rect(95, 48, 99, 52, "#2a3040")
    c.rect(88, 51, 106, 52, "#2a3040")
    c.rect(20, 30, 22, 52, "#3a3040")
    c.line([(21, 30), (30, 24)], "#3a3040", 2.0)
    c.rect(26, 20, 38, 26, "#5a4a3a")
    c.glow(32, 30, 16, "#ffc070", 0.5)
    c.rect(44, 44, 62, 52, "#e8e4d8")
    c.rect(46, 40, 60, 44, "#c8b080")
    c.rect(66, 46, 76, 52, "#5a8ac8")
    return c.rgba8()


def th_clock() -> np.ndarray:
    """A round wall clock (64 px)."""
    c = Canvas(64)
    c.disc(32, 32, 28, "#2a3040")
    c.disc(32, 32, 25, "#e8ecf2")
    for k in range(12):
        a = k * np.pi / 6
        r0 = 20 if k % 3 else 17
        c.line([(32 + np.sin(a) * r0, 32 - np.cos(a) * r0), (32 + np.sin(a) * 23, 32 - np.cos(a) * 23)], "#2a3040", 1.6)
    c.line([(32, 32), (32 + 9, 32 - 6)], "#141820", 2.4)  # ten past two, the small hours
    c.line([(32, 32), (32 + 4, 32 - 17)], "#141820", 1.6)
    c.line([(32, 32), (32 - 8, 32 + 14)], "#c83030", 1.0)
    c.disc(32, 32, 2, "#c83030")
    return c.rgba8()


def th_exit() -> np.ndarray:
    """A green emergency exit sign with the running figure and an arrow (64 px)."""
    c = Canvas(64)
    c.rect(2, 18, 62, 46, "#c8ccd8")
    c.rect(4, 20, 60, 44, "#18c060")
    c.rect(4, 20, 60, 23, "#60f0a0")
    c.disc(18, 25, 2.5, "#f0fff4")
    c.line([(18, 28), (16, 35), (12, 40)], "#f0fff4", 2.0)
    c.line([(16, 35), (21, 38), (22, 42)], "#f0fff4", 2.0)
    c.line([(12, 30), (18, 29), (23, 32)], "#f0fff4", 2.0)
    c.rect(26, 22, 30, 42, "#f0fff4")
    c.rect(27, 23, 29, 41, "#18c060")
    c.line([(36, 32), (54, 32)], "#f0fff4", 3.0)
    c.line([(48, 26), (54, 32), (48, 38)], "#f0fff4", 2.5)
    return c.rgba8()


def th_nightlight() -> np.ndarray:
    """A low wall night light: a small plate with a warm glowing lens (64 px)."""
    c = Canvas(64)
    c.rect(18, 18, 46, 46, "#5a6478")
    c.rect(18, 18, 46, 20, "#a8b2c4")
    c.rect(22, 22, 42, 42, "#ffc860")
    c.rect(22, 22, 42, 26, "#fff0c0")
    c.rect(22, 38, 42, 42, "#e09a30")
    return c.rgba8()


def th_tree(k: int = 1) -> np.ndarray:
    """A garden tree at night: a dark rounded canopy with a moonlit rim, a trunk."""
    c = Canvas(128, k=k)
    c.rect(58, 76, 70, 128, "#1a1414")
    c.rect(58, 76, 61, 128, "#3a3438")
    c.line([(64, 92), (48, 70)], "#1a1414", 3.0)
    c.line([(64, 86), (82, 66)], "#1a1414", 3.0)
    nz = c.nz(5, 231, 3)
    blobs = [(64, 40, 34), (40, 60, 24), (88, 58, 26), (62, 70, 22), (50, 30, 20), (80, 30, 20)]
    m = np.zeros((c.n, c.n), bool)
    for bx, by, r in blobs:
        m |= ((c.x - bx) ** 2 + (c.y - by) ** 2) <= (r * (0.85 + 0.3 * nz)) ** 2
    light = np.clip(((64 - c.x) + (40 - c.y)) / 80.0 + 0.4 + (nz - 0.5) * 0.6, 0, 1)
    col = px.quantise(light, px.ramp("#06100e", "#0c1c1c", "#14302c", "#22463e", "#3a6660"))
    c.put(m, col.astype(np.float32) / 255)
    c.a = np.maximum(c.a, m.astype(np.float32))
    return c.rgba8()


def th_lamppost(k: int = 1) -> np.ndarray:
    """A garden lamp post with a warm lantern."""
    c = Canvas(128, k=k)
    c.rect(62, 30, 67, 124, "#1e2230")
    c.rect(62, 30, 63, 124, "#4a5068")
    c.rect(56, 118, 73, 128, "#1e2230")
    c.rect(54, 26, 75, 30, "#1e2230")
    c.rect(56, 10, 73, 26, "#ffd890")
    c.rect(58, 12, 71, 24, "#fff0c8")
    c.rect(64, 10, 65, 26, "#8a7040")
    c.rect(52, 6, 77, 10, "#1e2230")
    c.rect(61, 2, 68, 6, "#1e2230")
    return c.rgba8()


def th_chair(k: int = 1) -> np.ndarray:
    """A day-room armchair seen from behind (they face the TV): padded back, arms, legs."""
    c = Canvas(128, k=k)
    c.rect(30, 30, 98, 86, "#3a5a8a")
    c.rgb = np.where(c.box(30, 30, 98, 86)[..., None], c.rgb * (0.85 + 0.3 * c.nz(6, 241))[..., None], c.rgb)
    c.rect(30, 30, 98, 34, "#5a7aaa")
    c.rect(36, 40, 92, 41, "#2a4a76")
    c.rect(36, 56, 92, 57, "#2a4a76")
    c.rect(22, 62, 32, 92, "#6a4a30")
    c.rect(96, 62, 106, 92, "#6a4a30")
    c.rect(22, 62, 32, 64, "#9a7450")
    c.rect(96, 62, 106, 64, "#9a7450")
    c.rect(30, 86, 98, 92, "#2a3a5a")
    c.rect(28, 92, 34, 124, "#4a3420")
    c.rect(94, 92, 100, 124, "#4a3420")
    return c.rgba8()


def th_bench(k: int = 1) -> np.ndarray:
    """A garden bench: wooden slats, cast-iron ends."""
    c = Canvas(128, k=k)
    for y0 in (52, 60, 68):
        c.rect(6, y0, 122, y0 + 6, "#7a5a38")
        c.rect(6, y0, 122, y0 + 1, "#a8845a")
    for y0 in (82, 88):
        c.rect(2, y0, 126, y0 + 5, "#8a6a42")
        c.rect(2, y0, 126, y0 + 1, "#b8946a")
    for x0 in (10, 110):
        c.rect(x0, 48, x0 + 6, 124, "#1e2230")
        c.line([(x0 + 3, 92), (x0 - 4 if x0 < 64 else x0 + 10, 108)], "#1e2230", 3.0)
    return c.rgba8()


def th_vending(k: int = 1) -> np.ndarray:
    """One vending machine: a lit window of snacks, a keypad, the tray."""
    c = Canvas(128, k=k)
    c.rect(28, 6, 100, 128, "#141824")
    c.rect(30, 8, 98, 126, "#8a2a34")
    c.rect(30, 8, 98, 18, "#c83a44")
    c.rect(36, 10, 92, 16, "#f0e0c0")
    c.rect(34, 22, 80, 100, "#c8eeff")
    pal = ["#e85a4a", "#f0c040", "#4ac0e0", "#60d070", "#e070c0", "#f09040"]
    for r in range(6):
        y = 25 + r * 12
        c.rect(34, y + 9, 80, y + 10, "#6a7a90")
        for k in range(5):
            c.rect(36 + k * 9, y + 1, 42 + k * 9, y + 9, pal[(r * 2 + k) % len(pal)])
    c.rect(82, 26, 96, 70, "#1a1e2a")
    c.rect(84, 28, 94, 34, "#60ff90")
    for k in range(3):
        for j in range(2):
            c.rect(84 + j * 6, 38 + k * 6, 88 + j * 6, 42 + k * 6, "#c8ccd8")
    c.rect(86, 60, 92, 66, "#2a2e3a")
    c.rect(36, 106, 92, 118, "#0a0c14")
    return c.rgba8()


def th_tv(k: int = 1) -> np.ndarray:
    """The day-room television: a late-night programme glowing blue."""
    c = Canvas(128, k=k)
    c.rect(8, 28, 120, 98, "#0c1018")
    c.rect(12, 32, 116, 92, "#3a6ac0")
    t = np.clip((c.y - 32) / 60, 0, 1)
    scr = c.box(12, 32, 116, 92)
    c.rgb = np.where(scr[..., None], lerpc("#5a8ae0", "#2a4a90", t), c.rgb)
    c.put(scr & (c.y > 70), "#2a6a5a")
    c.disc(90, 46, 6, "#f0e8b0")
    c.rect(40, 54, 48, 72, "#e8d0c0")
    c.disc(44, 50, 4, "#e8d0c0")
    c.put(scr & (np.floor(c.y + 0.5).astype(int) % 3 == 0), "#000000", 0.18)
    c.rect(58, 98, 70, 108, "#141820")
    c.rect(44, 108, 84, 112, "#141820")
    return c.rgba8()


def th_door_lit(k: int = 1) -> np.ndarray:
    """Double doors at the end of the quiet corridor, light beyond them through the windows and the gap."""
    c = Canvas(128, k=k)
    c.rect(8, 4, 120, 128, "#6a7898")
    c.rect(12, 8, 116, 128, "#ffe0a0")
    c.rect(14, 10, 63, 128, "#3a4a6a")
    c.rect(65, 10, 114, 128, "#3a4a6a")
    c.rect(24, 24, 52, 64, "#ffd890")
    c.rect(76, 24, 104, 64, "#ffd890")
    c.rect(24, 24, 52, 30, "#fff0c8")
    c.rect(76, 24, 104, 30, "#fff0c8")
    c.rect(20, 76, 58, 80, "#c8ccd8")
    c.rect(70, 76, 108, 80, "#c8ccd8")
    c.rect(14, 112, 63, 124, "#8a96b0")
    c.rect(65, 112, 114, 124, "#8a96b0")
    return c.rgba8()


def th_plant() -> np.ndarray:
    """A potted plant (64 px)."""
    c = Canvas(64)
    c.rect(22, 44, 42, 62, "#7a4a30")
    c.rect(20, 42, 44, 46, "#9a6040")
    nz = px.noise(64, 4, 251, 2)
    m = (((c.x - 32) / 18) ** 2 + ((c.y - 28) / 18) ** 2 < 1) & (nz > 0.32)
    col = px.quantise(np.clip(nz + (32 - c.y) / 60, 0, 1), px.ramp("#0a1a14", "#14302a", "#22483c", "#3a6650"))
    c.put(m, col.astype(np.float32) / 255)
    return c.rgba8()

def th_mic(k: int = 1) -> np.ndarray:
    """A bandstand microphone (128 px, 1.5 m): a brass-footed stand, the boom, a silver ball mic with a warm lamp-reflection, the lead looping across the boards."""
    c = Canvas(128, k=k)
    c.rect(62, 30, 66, 116, "#a8b2c4")
    c.rect(62, 30, 63, 116, "#d8e0ec")
    c.disc(64, 118, 11, "#7a5a28")
    c.disc(64, 116, 11, "#c8963c")
    c.rect(54, 116, 74, 119, "#7a5a28")
    c.line([(64, 34), (74, 22)], "#a8b2c4", 3.0)
    c.disc(78, 16, 9, "#6a7488")
    c.disc(77, 15, 8, "#c4ccdc")
    c.disc(74, 12, 3, "#ffffff", 0.9)
    c.rect(70, 14, 86, 15, "#4a5266")
    c.rect(70, 18, 86, 19, "#4a5266")
    c.line([(64, 120), (40, 124), (24, 120)], "#1e2230", 2.0)
    c.glow(78, 16, 22, "#ffd890", 0.35)
    return c.rgba8()


THINGS = {
    "thing_monitor": th_monitor, "thing_bed": th_bed, "thing_drip": th_drip, "thing_desk": th_desk, "thing_clock": th_clock, "thing_exit": th_exit,
    "thing_nightlight": th_nightlight, "thing_tree": th_tree, "thing_lamppost": th_lamppost, "thing_chair": th_chair, "thing_bench": th_bench,
    "thing_door_lit": th_door_lit, "thing_plant": th_plant, "thing_mic": th_mic,
}
# The props that stand taller than 1.3 m in the map are drawn again on a finer grid as stage sprites (hp_pix.write_props, same ids, same design): k times the pixels, so
# 100 to 140 texels a metre at the size the map gives them. These 128 px files stay as the tile list's fallback (the manifest's textures section needs them).
BIG = {"thing_monitor": (th_monitor, 2), "thing_bed": (th_bed, 2), "thing_drip": (th_drip, 2), "thing_desk": (th_desk, 2), "thing_tree": (th_tree, 4),
       "thing_lamppost": (th_lamppost, 3), "thing_door_lit": (th_door_lit, 2), "thing_mic": (th_mic, 2), "wall_vending": (th_vending, 2), "wall_tv": (th_tv, 2)}


def build() -> dict:
    for tid, fn in sorted(THINGS.items()):
        save_rgba(tid, fn())
    return {  # metres a repeat: 128 px over 1.0 to 1.3 m is 98 to 128 texels a metre (the style guide's 96 to 160)
        "ceil_tile": (ceil_tile(), 1.28),
        "floor_ward": (lino("#1c2848", "#5a7ac0", 32, 301), 1.28),
        "floor_check": (lino("#2a2a4a", "#c8a070", 32, 302, 0.16, "#6a6a98", ("#2c2e50", "#262848")), 1.28),
        "floor_lino": (lino("#203450", "#6a8ab8", 32, 303, 0.16, "#6a8aa0"), 1.28),
        "floor_cafe": (floor_cafe(), 1.28),
        "floor_stone": (floor_stone(), 1.28),
        "floor_wood": (floor_wood(), 1.28),
        "wall_ward": (wall_ward(), 1.3),
        "wall_dayroom": (wall_dayroom(), 1.1),
        "wall_window": (wall_window(), 1.3),
        "wall_curtain": (wall_curtain(), 1.3),
        "wall_door": (wall_door(), 1.3),
        "wall_station": (wall_station(), 1.3),
        "wall_counter": (wall_counter(), 1.0),
        "wall_vending": (wall_vending(), 1.28),
        "wall_vending_wall": (wall_vending_wall(), 1.28),
        "wall_cafe": (wall_cafe(), 1.3),
        "wall_brick": (wall_brick(), 1.28),
        "wall_hedge": (wall_hedge(), 1.3),
        "wall_quiet": (wall_quiet(), 1.2),
        "wall_tv": (wall_tv(), 1.3),
        "wall_tv_wall": (wall_tv_wall(), 1.3),
        "trim": (trim(), 1.0),
        "sky_night": (sky_night(), 1.0),
    }
