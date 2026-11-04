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
    """Float RGBA canvas (rows = y, top down)."""

    def __init__(self, n: int, fill=None):
        self.n = n
        self.rgb = np.zeros((n, n, 3), np.float32)
        self.a = np.zeros((n, n), np.float32)
        if fill is not None:
            self.rgb[:] = C(fill) if isinstance(fill, str) else fill
            self.a[:] = 1.0
        self.y, self.x = np.mgrid[0:n, 0:n].astype(np.float32)

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

def ceil_tile() -> np.ndarray:
    """Suspended ceiling, 4 x 4 tiles of 0.6 m a repeat: speckled mineral tiles, T-bar grid, one louvred light panel, one square air vent."""
    n = 128
    c = Canvas(n, "#323d5c")
    nz = px.noise(n, 10, 41)
    c.rgb *= (0.9 + 0.2 * nz)[..., None]
    c.put(px.speckle(n, 0.10, 42) > 0, "#262e48")
    c.put(px.speckle(n, 0.04, 43) > 0, "#46527a")
    lx, ly = c.x % 32, c.y % 32
    c.put((lx < 1) | (ly < 1), "#1a2036")
    c.put(((lx == 1) | (ly == 1)), "#56648c")
    # light panel across two tiles (dim: the night lights are off, a faint cold glow)
    pan = c.box(34, 2, 95, 31)
    c.put(pan, "#7f9cc8")
    c.put(pan & (((c.x - 34) % 6) == 0), "#5e7aa8")
    c.put(pan & (((c.y - 2) % 7) == 0), "#5e7aa8")
    c.put(c.box(34, 2, 95, 4), "#a8c4ea")
    c.put(c.box(33, 1, 96, 2) | c.box(33, 31, 96, 32) | c.box(33, 1, 34, 32) | c.box(95, 1, 96, 32), "#2a3250")
    # a second, unlit panel diagonal from it (a broken tube reads as night)
    pan2 = c.box(2, 66, 31, 95)
    c.put(pan2, "#4a5a80")
    c.put(pan2 & (((c.x - 2) % 6) == 0), "#3a4868")
    # square air vent: concentric slats
    cx, cy = 112, 112
    d = np.maximum(np.abs(c.x - cx), np.abs(c.y - cy))
    vent = d <= 13
    c.put(vent, "#2a3250")
    c.put(vent & (d % 4 == 0), "#56648c")
    c.put(vent & (d % 4 == 1), "#141a2c")
    c.put(d <= 3, "#0e1220")
    return c.rgb8()


def lino(n: int, base: str, light: str, seam: int, seed: int, sheen: float = 0.28, fleck: str = "#5a70a8", tiles_two: tuple | None = None) -> np.ndarray:
    """Glossy sheet lino: mottle, faint welded seams, flecks and a soft diagonal sheen that tiles."""
    c = Canvas(n, base)
    mot = px.noise(n, 12, seed, 4)
    if tiles_two:
        ch = px.checker(n, n // seam)
        c.rgb = lerpc(tiles_two[0], tiles_two[1], ch)
    c.rgb *= (0.85 + 0.3 * mot)[..., None]
    c.put(px.speckle(n, 0.05, seed + 1) > 0, fleck, 0.6)
    c.put(px.speckle(n, 0.03, seed + 2) > 0, "#0c1020", 0.5)
    s = (np.cos(2 * np.pi * (c.x + c.y * 0.6) / n) * 0.5 + 0.5) ** 6
    s2 = (np.cos(2 * np.pi * (c.x * 2 - c.y) / n + 1.3) * 0.5 + 0.5) ** 10
    c.rgb = c.rgb + C(light)[None, None, :] * (s * sheen + s2 * sheen * 0.5)[..., None]
    sm = (c.x % seam < 1) | (c.y % seam < 1)
    c.put(sm, "#0e1428", 0.55)
    return c.rgb8(26)


def wall_ward() -> np.ndarray:
    """The ward: dimmed colour blocks and a triangle mosaic like the reference, a wall light bar, sockets, a skirting. 2.7 m tall, ceiling at the top."""
    n = 128
    c = Canvas(n, "#2c3858")
    c.rgb *= (0.92 + 0.12 * px.noise(n, 16, 51))[..., None]
    c.rect(0, 0, n, 3, "#1c2440")
    # colour block columns
    blocks = [(4, 12, 17, 56, "#7a6a2e"), (17, 12, 30, 56, "#6e2c38"), (4, 56, 30, 76, "#4e5878"), (4, 76, 17, 112, "#7a6a2e"), (17, 76, 30, 112, "#2a5a60")]
    for x0, y0, x1, y1, col in blocks:
        c.rect(x0, y0, x1, y1, col)
    c.rect(4, 12, 30, 13, "#8890b0", 0.4)
    for x0 in (7, 20):
        c.rect(x0, 62, x0 + 6, 69, "#c8ccd8")
        c.rect(x0 + 2, 64, x0 + 3, 67, "#20263a")
    c.rect(30, 12, 31, 112, "#141a2c")
    # a wall light bar (dim cold glow)
    c.rect(38, 34, 66, 38, "#a8c8f0")
    c.rect(38, 38, 66, 39, "#3a4a70")
    c.glow(52, 40, 22, "#3a5a90", 0.35)
    # the triangle mosaic panel
    pal = ["#6e2c38", "#2a5a60", "#7a6a2e", "#4a3a6e", "#2e4a7e", "#3e4a68", "#5a3a5e", "#2c6a5a"]
    rng = np.random.RandomState(52)
    cs = 13
    x0p, y0p, x1p, y1p = 72, 10, 124, 114
    lx, ly = (c.x - x0p), (c.y - y0p)
    inside = c.box(x0p, y0p, x1p, y1p)
    gi, gj = np.floor(lx / cs).astype(int), np.floor(ly / cs).astype(int)
    up = np.where((gi + gj) % 2 == 0, (lx % cs) > (ly % cs), (lx % cs) + (ly % cs) < cs)
    tri = (gi * 7 + gj * 13 + up.astype(int) * 3) % 97
    cols = np.stack([C(pal[rng.randint(len(pal))]) for _ in range(97)])
    col = cols[np.clip(tri, 0, 96)]
    shade = 0.8 + 0.25 * px.noise(n, 6, 53)
    c.rgb = np.where(inside[..., None], col * shade[..., None], c.rgb)
    c.put(c.box(x0p - 1, y0p - 1, x1p + 1, y0p) | c.box(x0p - 1, y1p, x1p + 1, y1p + 1) | c.box(x0p - 1, y0p, x0p, y1p) | c.box(x1p, y0p, x1p + 1, y1p), "#141a2c")
    # skirting and a bed-head rail
    c.rect(0, 84, 72, 87, "#56648a")
    c.rect(0, 87, 72, 88, "#141a2c")
    c.rect(0, 118, n, 128, "#1a2038")
    c.rect(0, 118, n, 119, "#4a5678")
    c.put(px.grime(n, 54, 0.25) > 0.4, "#141a2c", 0.3)
    return c.rgb8()


def wall_dayroom() -> np.ndarray:
    """The day room: a broad zig-zag band of warm colours over a wooden dado, a framed picture. 2.2 m tall."""
    n = 128
    c = Canvas(n, "#2e3a5c")
    c.rgb *= (0.92 + 0.12 * px.noise(n, 16, 61))[..., None]
    c.rect(0, 0, n, 3, "#1c2440")
    band = (c.y > 30) & (c.y < 62)
    zz = (np.abs(((c.x % 32) - 16)) + c.y) % 32
    cols = [C("#7a5a2e"), C("#2a5a60"), C("#6e3442"), C("#3a4a7a")]
    idx = ((np.floor(zz / 8)).astype(int) + (np.floor(c.x / 32)).astype(int)) % 4
    col = np.stack(cols)[idx]
    c.rgb = np.where(band[..., None], col * (0.85 + 0.25 * px.noise(n, 5, 62))[..., None], c.rgb)
    c.rect(0, 29, n, 30, "#5a6890")
    c.rect(0, 62, n, 63, "#141a2c")
    # picture frame
    c.rect(84, 8, 116, 27, "#5a4a3a")
    c.rect(86, 10, 114, 25, "#2a4a5a")
    c.rect(86, 18, 114, 25, "#2a4a34")
    c.disc(106, 14, 3, "#c8b870")
    # dado rail and wood panelling below
    c.rect(0, 74, n, 78, "#6a5a48")
    c.rect(0, 78, n, 79, "#141a2c")
    wood = (c.y >= 79)
    c.rgb = np.where(wood[..., None], lerpc("#3a3040", "#4a3a44", px.noise(n, 8, 63)) , c.rgb)
    c.put(wood & (c.x % 32 == 0), "#20182a")
    c.put(wood & (c.x % 32 == 1), "#5a4a52")
    c.rect(0, 120, n, 128, "#1a1a2c")
    return c.rgb8()


def wall_window() -> np.ndarray:
    """The ward window, one repeat across the 5 m wall (only the top 2.7 m show): night sky, the moon, trees, venetian blinds, a radiator under the sill."""
    n = 128
    c = Canvas(n, "#2c3858")
    c.rgb *= (0.92 + 0.12 * px.noise(n, 16, 71))[..., None]
    c.rect(0, 0, n, 2, "#1c2440")
    wx0, wy0, wx1, wy1 = 6, 6, 122, 47
    win = c.box(wx0, wy0, wx1, wy1)
    t = np.clip((c.y - wy0) / (wy1 - wy0), 0, 1)
    sky = lerpc("#06102a", "#1e3266", t)
    c.rgb = np.where(win[..., None], sky, c.rgb)
    rng = np.random.RandomState(72)
    for _ in range(26):
        sx, sy = rng.randint(wx0, wx1), rng.randint(wy0, wy0 + 22)
        c.put(c.box(sx, sy, sx + 1, sy + 1) & win, "#c8d4ff", 0.8)
    # moon with a halo
    c.glow(26, 16, 14, "#4a6aa8", 0.7)
    c.disc(26, 16, 5.2, "#e8eeff")
    c.disc(27.5, 17, 1.4, "#b8c4e0")
    c.disc(24, 14.5, 1, "#c8d2ea")
    # trees: a ragged canopy line, darker in front
    nz = px.noise(n, 7, 73, 3)
    top = 26 + nz[0] * 0 + 10 * px.noise(n, 18, 74, 2)[20] - 8 * np.exp(-((np.arange(n) - 60) / 10.0) ** 2) - 6 * np.exp(-((np.arange(n) - 98) / 8.0) ** 2)
    trees = win & (c.y > top[c.x.astype(int)] + (nz - 0.5) * 4)
    c.put(trees, "#0c1a2a")
    c.put(trees & (px.speckle(n, 0.12, 75) > 0) & (c.y < top[c.x.astype(int)] + 6), "#2a4a6a")
    c.put(win & (c.y > 40), "#081420")
    # blinds: pane two half down, pane three all the way, slats lit by the moon with dark gaps
    for x0, x1, y1 in ((46, 82, 26), (86, 120, 45)):
        sl = c.box(x0, wy0, x1, y1)
        ph = (c.y - wy0) % 3
        c.put(sl & (ph < 2), "#7a92c0")
        c.put(sl & (ph == 0), "#9ab0d8")
        c.put(c.box(x0, y1 - 1, x1, y1 + 1), "#c0d0f0")
        c.put(c.box(x0 + 4, wy0, x0 + 5, y1) | c.box(x1 - 5, wy0, x1 - 4, y1), "#4a5a80")
    # frame and mullions
    for xm in (44, 84):
        c.rect(xm, wy0, xm + 2, wy1, "#5a6a90")
    c.put(c.box(wx0 - 2, wy0 - 2, wx1 + 2, wy0) | c.box(wx0 - 2, wy0, wx0, wy1) | c.box(wx1, wy0, wx1 + 2, wy1), "#5a6a90")
    c.rect(wx0 - 3, wy1, wx1 + 3, wy1 + 3, "#8a9ac0")
    c.rect(wx0 - 3, wy1 + 3, wx1 + 3, wy1 + 4, "#141a2c")
    # radiator
    rad = c.box(20, 52, 108, 64)
    c.put(rad, "#4a5678")
    c.put(rad & (c.x % 4 == 0), "#2a3250")
    c.put(rad & (c.x % 4 == 1), "#6a7aa0")
    c.rect(0, 64, n, 69, "#1a2038")
    c.rect(0, 64, n, 65, "#4a5678")
    c.rect(0, 69, n, n, "#2c3858")
    return c.rgb8()


def wall_curtain() -> np.ndarray:
    """The privacy curtain round the bed: soft folds in hospital blue, a rail with hooks, a hem."""
    n = 64
    x, y = px.grid(n)
    fold = 0.5 + 0.32 * np.sin(2 * np.pi * x / 16) + 0.12 * np.sin(2 * np.pi * x / 8 + 0.7)
    fold += (px.noise(n, 8, 81) - 0.5) * 0.15
    rgb = px.quantise(fold, px.ramp("#142640", "#1e3a5a", "#2a4e72", "#3a6488", "#5280a4"))
    c = Canvas(n)
    c.rgb = rgb.astype(np.float32) / 255
    c.rect(0, 0, n, 3, "#5a6a88")
    for k in range(4):
        c.rect(k * 16 + 6, 3, k * 16 + 9, 6, "#8a9ab8")
    c.rect(0, 60, n, 64, "#1a3048")
    return c.rgb8()


def wall_door() -> np.ndarray:
    """The corridor wall, 2.6 m: a ward door with a lit window slit (the room beyond), a bumper rail, a notice board, a coloured dado."""
    n = 128
    c = Canvas(n, "#323e60")
    c.rgb *= (0.92 + 0.12 * px.noise(n, 16, 91))[..., None]
    c.rect(0, 0, n, 3, "#1c2440")
    c.rect(0, 78, n, 122, "#2a4a5a")
    c.rgb = np.where(c.box(0, 78, n, 122)[..., None], c.rgb * (0.9 + 0.15 * px.noise(n, 8, 92))[..., None], c.rgb)
    c.rect(0, 72, n, 76, "#7a88a8")
    c.rect(0, 76, n, 78, "#141a2c")
    # door frame and leaf
    c.rect(16, 22, 78, 128, "#8a96b4")
    c.rect(20, 26, 74, 128, "#5a4434")
    c.rgb = np.where(c.box(20, 26, 74, 128)[..., None], c.rgb * (0.85 + 0.3 * px.noise(n, 5, 93))[..., None], c.rgb)
    c.rect(46, 26, 48, 128, "#2a2024")
    c.rect(28, 38, 38, 70, "#1a1418")
    c.rect(29, 39, 37, 69, "#d8a860")
    c.rect(29, 39, 37, 45, "#f0c880")
    c.rect(56, 38, 66, 70, "#1a1418")
    c.rect(57, 39, 65, 69, "#9a7448")
    c.rect(40, 74, 44, 78, "#c8ccd8")
    c.rect(50, 74, 54, 78, "#c8ccd8")
    c.rect(20, 112, 74, 122, "#7a8298")
    # room number plate
    c.rect(82, 30, 96, 36, "#c8ccd8")
    c.rect(84, 32, 94, 34, "#2a3250")
    # notice board
    c.rect(98, 28, 124, 60, "#4a3a2e")
    c.rect(100, 30, 122, 58, "#6a5a40")
    c.rect(102, 33, 110, 44, "#c8c8c0")
    c.rect(112, 32, 120, 40, "#c0a870")
    c.rect(106, 46, 118, 56, "#a8b8c8")
    c.rect(0, 122, n, n, "#1a2038")
    c.rect(0, 122, n, 123, "#4a5678")
    return c.rgb8()


def wall_station() -> np.ndarray:
    """The nurses' station: a warm purple wall, notice boards, a rota, a phone; lit by the station lamps."""
    n = 128
    c = Canvas(n, "#4a2e5a")
    c.rgb *= (0.92 + 0.14 * px.noise(n, 14, 101))[..., None]
    c.rect(0, 0, n, 3, "#2a1a34")
    c.rect(10, 26, 48, 54, "#c8b898")
    c.rect(12, 28, 46, 52, "#e8dcc0")
    for k in range(5):
        c.rect(15, 31 + k * 4, 40 - (k % 2) * 8, 33 + k * 4, "#7a6a5a")
    c.rect(58, 24, 90, 56, "#c8b898")
    c.rect(60, 26, 88, 54, "#d8c8a8")
    c.rect(62, 28, 72, 40, "#e8e0d0")
    c.rect(75, 29, 86, 38, "#c89878")
    c.rect(64, 43, 84, 51, "#a8c8d8")
    c.rect(98, 18, 124, 40, "#141018")
    c.rect(100, 20, 122, 38, "#2a4a6a")
    c.rect(100, 20, 122, 24, "#4a7aa0")
    c.rect(104, 56, 110, 70, "#e8e0d0")
    c.rect(105, 58, 109, 62, "#2a2028")
    c.rect(0, 78, n, 82, "#7a5a68")
    c.rect(0, 82, n, 122, "#3a2440")
    c.rect(0, 122, n, n, "#20142a")
    return c.rgb8()


def wall_counter() -> np.ndarray:
    """A wooden counter front (cafeteria serving counter, the TV shelf): a lit lip, panels, a dark kick."""
    n = 64
    c = Canvas(n, "#6a4a30")
    c.rgb *= (0.85 + 0.3 * px.noise(n, 6, 111))[..., None]
    grain = np.sin(c.y * 0.9 + px.noise(n, 10, 112) * 6) * 0.06
    c.rgb += grain[..., None]
    c.rect(0, 0, n, 6, "#c8a878")
    c.rect(0, 6, n, 8, "#2a1a14")
    for x0 in (2, 22, 42):
        c.rect(x0, 12, x0 + 18, 54, "#5a3e28")
        c.rect(x0, 12, x0 + 18, 13, "#8a6a48")
    c.rect(0, 56, n, n, "#1e1612")
    return c.rgb8()


def wall_vending() -> np.ndarray:
    """The cafeteria's back wall, 4.8 m: a menu board high up, four vending machines at the bottom with lit windows of products."""
    n = 128
    c = Canvas(n, "#26365a")
    c.rgb *= (0.9 + 0.14 * px.noise(n, 14, 121))[..., None]
    c.rect(0, 0, n, 3, "#141c34")
    # menu board
    c.rect(14, 22, 114, 46, "#3a2a20")
    c.rect(16, 24, 112, 44, "#141c1c")
    rng = np.random.RandomState(122)
    for row in range(4):
        x = 20
        while x < 104:
            w = rng.randint(3, 9)
            c.rect(x, 27 + row * 4, min(x + w, 106), 28 + row * 4, "#c8d0b8" if row else "#e8c870")
            x += w + 2
    c.rect(0, 70, n, 72, "#4a5a80")
    # machines
    pal = ["#e85a4a", "#f0c040", "#4ac0e0", "#60d070", "#e070c0", "#f09040"]
    for i, x0 in enumerate((4, 34, 68, 98)):
        body = "#7a2a34" if i % 2 == 0 else "#2a3a6a"
        c.rect(x0, 76, x0 + 26, 128, "#141824")
        c.rect(x0 + 1, 77, x0 + 25, 127, body)
        c.rect(x0 + 1, 77, x0 + 25, 78, "#c8ccd8")
        wx0, wx1, wy0, wy1 = x0 + 3, x0 + 18, 80, 112
        c.rect(wx0, wy0, wx1, wy1, "#bfeaff" if i % 2 == 0 else "#ffe6b0")
        for r in range(5):
            yy = wy0 + 2 + r * 6
            c.rect(wx0, yy + 4, wx1, yy + 5, "#5a6a80")
            for k in range(4):
                c.rect(wx0 + 1 + k * 4, yy, wx0 + 3 + k * 4, yy + 4, pal[(i * 3 + r * 2 + k) % len(pal)])
        c.rect(x0 + 19, 82, x0 + 24, 96, "#1a1e2a")
        c.rect(x0 + 20, 84, x0 + 23, 86, "#60ff90")
        for k in range(3):
            c.rect(x0 + 20, 88 + k * 3, x0 + 23, 89 + k * 3, "#c8ccd8")
        c.rect(x0 + 4, 116, x0 + 18, 122, "#0a0c14")
    return c.rgb8()


def wall_cafe() -> np.ndarray:
    """The cafeteria walls, 4.8 m: tall windows onto the night garden over a tiled dado."""
    n = 128
    c = Canvas(n, "#283a5e")
    c.rgb *= (0.9 + 0.14 * px.noise(n, 14, 131))[..., None]
    c.rect(0, 0, n, 3, "#141c34")
    rng = np.random.RandomState(132)
    for x0 in (14, 74):
        x1, y0, y1 = x0 + 40, 16, 82
        win = c.box(x0, y0, x1, y1)
        t = np.clip((c.y - y0) / (y1 - y0), 0, 1)
        c.rgb = np.where(win[..., None], lerpc("#06102a", "#1a2c5a", t), c.rgb)
        for _ in range(8):
            sx, sy = rng.randint(x0, x1), rng.randint(y0, y0 + 30)
            c.put(c.box(sx, sy, sx + 1, sy + 1), "#c8d4ff", 0.7)
        nz = px.noise(n, 6, 133 + x0)
        c.put(win & (c.y > 60 + nz * 10), "#0a1622")
        c.rect(x0 + 19, y0, x0 + 21, y1, "#6a7aa0")
        c.rect(x0, 48, x1, 50, "#6a7aa0")
        c.put(c.box(x0 - 2, y0 - 2, x1 + 2, y0) | c.box(x0 - 2, y0, x0, y1) | c.box(x1, y0, x1 + 2, y1), "#6a7aa0")
        c.rect(x0 - 3, y1, x1 + 3, y1 + 3, "#9aa8c8")
    # tiled dado
    t_sh, g = px.tiles(n, 16, 1, 134, 0.3)
    dado = c.box(0, 94, n, 124)
    tile = lerpc("#3a4a70", "#5a6c94", t_sh)
    c.rgb = np.where(dado[..., None], np.where(g[..., None] > 0.5, C("#1c2440"), tile), c.rgb)
    c.rect(0, 92, n, 94, "#2a8a8a")
    c.rect(0, 124, n, n, "#141c30")
    return c.rgb8()


def floor_cafe() -> np.ndarray:
    """Cafeteria floor: small glossy tiles, cream and teal by day, blue at night."""
    n = 64
    ch = px.checker(n, 4)
    c = Canvas(n)
    c.rgb = lerpc("#4a5878", "#1e3a4c", ch)
    c.rgb *= (0.88 + 0.25 * px.noise(n, 10, 141))[..., None]
    s = (np.cos(2 * np.pi * (c.x + c.y) / n) * 0.5 + 0.5) ** 6
    c.rgb += C("#7a9ac8")[None, None, :] * (s * 0.18)[..., None]
    c.put((c.x % 16 < 1) | (c.y % 16 < 1), "#141c30", 0.8)
    return c.rgb8()


def wall_brick() -> np.ndarray:
    """The hospital seen from the garden, 6 m a repeat (the top 3 m show): moonlit brick, one warm lit window, one dark one with the moon in it."""
    n = 128
    sh, mort = px.bricks(n, 24, 8, 1, 151, 0.4)
    rgb = px.quantise(sh, px.ramp("#1e1828", "#2c2236", "#3a2c44", "#4a3a54", "#5c4a66"))
    c = Canvas(n)
    c.rgb = rgb.astype(np.float32) / 255
    c.put(mort > 0.5, "#141826")
    for x0, lit in ((12, True), (76, False)):
        x1, y0, y1 = x0 + 40, 12, 44
        c.rect(x0 - 2, y0 - 2, x1 + 2, y1 + 3, "#7a7a8a")
        if lit:
            c.rect(x0, y0, x1, y1, "#f0b860")
            c.rgb = np.where(c.box(x0, y0, x1, y1)[..., None], c.rgb * (0.8 + 0.3 * (1 - (c.y - y0) / 32))[..., None], c.rgb)
            c.rect(x0 + 4, y0 + 10, x0 + 9, y1, "#9a6a40")
            c.disc(x0 + 30, y0 + 16, 4, "#7a4a30")
            c.rect(x0 + 26, y0 + 20, x0 + 34, y1, "#7a4a30")
        else:
            c.rect(x0, y0, x1, y1, "#0c1630")
            c.rect(x0, y0, x1, y0 + 10, "#162450")
            c.disc(x0 + 12, y0 + 9, 3, "#8aa0d0")
        c.rect(x0 + 19, y0, x0 + 21, y1, "#7a7a8a")
        c.rect(x0, y0 + 15, x1, y0 + 17, "#7a7a8a")
        c.rect(x0 - 3, y1 + 2, x1 + 3, y1 + 4, "#9a9aaa")
    c.rect(64, 0, 67, n, "#2a2e3c")
    c.rect(64, 0, 65, n, "#4a5068")
    return c.rgb8()


def wall_hedge() -> np.ndarray:
    """A clipped hedge with the night sky above it (3 m a repeat: the hedge is the lower 1.7 m)."""
    n = 64
    c = Canvas(n)
    t = c.y / 28.0
    c.rgb = lerpc("#060e26", "#14224c", np.clip(t, 0, 1))
    rng = np.random.RandomState(161)
    for _ in range(6):
        sx, sy = rng.randint(0, n), rng.randint(0, 20)
        c.rect(sx, sy, sx + 1, sy + 1, "#a8b8e8")
    top = 27 + 3 * px.noise(n, 6, 162, 2)[0][c.x.astype(int)]
    hedge = c.y > top
    lv = px.noise(n, 3, 163, 2)
    leaf = px.quantise(np.clip(lv * 0.9 + 0.35 - (c.y - 28) / n * 0.6, 0, 1), px.ramp("#08141a", "#0e2228", "#163232", "#20443e", "#305a50"))
    c.rgb = np.where(hedge[..., None], leaf.astype(np.float32) / 255, c.rgb)
    c.put(hedge & (c.y < top + 2) & (px.speckle(n, 0.4, 164) > 0), "#4a7a78")
    return c.rgb8()


def floor_stone() -> np.ndarray:
    """Garden flagstones under the moon, moss and grass in the joints."""
    n = 128
    sh, mort = px.bricks(n, 5, 3, 2, 171, 0.5)
    rgb = px.quantise(sh * 0.9 + 0.05, px.ramp("#1e2434", "#2a3246", "#384258", "#48546c", "#5c6a84"))
    c = Canvas(n)
    c.rgb = rgb.astype(np.float32) / 255
    moss = (mort > 0.5) | ((px.noise(n, 5, 172) > 0.72) & (px.grime(n, 173, 0.6, False) > 0.3))
    c.put(moss, "#16302a")
    c.put(moss & (px.speckle(n, 0.3, 174) > 0), "#2a4a3a")
    return c.rgb8()


def wall_quiet() -> np.ndarray:
    """The quiet corridor: pale panels gone grey-blue in the dark, a handrail, a scuffed dado. 2.4 m."""
    n = 64
    c = Canvas(n, "#3a4868")
    c.rgb *= (0.9 + 0.15 * px.noise(n, 10, 181))[..., None]
    c.rect(0, 0, n, 2, "#1c2440")
    c.put((c.x % 32) == 0, "#28324c")
    c.put((c.x % 32) == 1, "#4e5c80")
    c.rect(0, 38, n, 41, "#7a88a8")
    c.rect(0, 41, n, 42, "#141a2c")
    c.rect(0, 42, n, 60, "#2c3a50")
    c.put(c.box(0, 42, n, 60) & (px.grime(n, 182, 0.5) > 0.35), "#1e2838", 0.6)
    c.rect(0, 60, n, n, "#161c2c")
    return c.rgb8()


def wall_tv() -> np.ndarray:
    """The TV alcove: soft striped wallpaper, a framed seaside print, a dado rail. 3 m a repeat."""
    n = 128
    c = Canvas(n)
    st = (c.x % 12) < 6
    c.rgb = np.where(st[..., None], C("#34406a")[None, None, :], C("#2c3860")[None, None, :])
    c.rgb *= (0.92 + 0.12 * px.noise(n, 14, 191))[..., None]
    c.rect(0, 0, n, 3, "#1c2440")
    c.rect(8, 16, 40, 40, "#6a5a3a")
    c.rect(10, 18, 38, 38, "#2e4a7a")
    c.rect(10, 30, 38, 38, "#1e5a6a")
    c.rect(10, 34, 38, 38, "#8a7a5a")
    c.disc(30, 23, 3, "#e8d090")
    c.rect(0, 84, n, 88, "#6a5a48")
    c.rect(0, 88, n, 128, "#262a44")
    c.rect(0, 122, n, n, "#141828")
    return c.rgb8()


def trim() -> np.ndarray:
    """A step edge: a worn nosing strip on top, a dark riser."""
    n = 64
    c = Canvas(n, "#262e46")
    c.rgb *= (0.85 + 0.3 * px.noise(n, 8, 201))[..., None]
    c.rect(0, 0, n, 4, "#8a96b4")
    c.rect(0, 4, n, 6, "#0e1222")
    c.put(px.speckle(n, 0.05, 202) > 0, "#3a4462")
    return c.rgb8()


def sky_night() -> np.ndarray:
    """The 256 x 64 sky strip: deep blue gradient, stars, a big moon with a halo, a far tree line low down."""
    w, h = 256, 64
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    t = np.clip(y / 50.0, 0, 1)
    rgb = C("#020614")[None, None, :] * (1 - t[..., None]) + C("#1a2a5a")[None, None, :] * t[..., None]
    rng = np.random.RandomState(211)
    for i in range(110):
        sx, sy = rng.randint(0, w), rng.randint(0, 40)
        rgb[sy, sx] = C("#e8eeff") if i % 4 == 0 else C("#7a8ac0")
    for mx in (64, 192):  # a moon a half turn apart, so a garden view either way meets one
        d = np.sqrt((x - mx) ** 2 + (y - 14) ** 2)
        rgb += C("#3a5aa0")[None, None, :] * (np.clip(1 - d / 13, 0, 1) ** 2 * 0.6)[..., None]
        moon = d <= 4.6
        rgb[moon] = C("#eef2ff")
        rgb[(d <= 4.6) & ((x - mx) + (y - 14) > 2.5)] = C("#c0cce8")
        rgb[(np.abs(x - mx + 1) < 1) & (np.abs(y - 13) < 1)] = C("#b8c4e0")
    tl = 40 + 5 * px.noise(256, 9, 212, 3)[7][:w] - 3
    tl = np.concatenate([tl, tl])[:w]
    trees = y > tl[x.astype(int)]
    rgb[trees] = C("#050a14")
    b = px.BAYER8[np.arange(h)[:, None] % 8, np.arange(w)[None, :] % 8][..., None]
    v = np.clip(rgb, 0, 1) * 23 + b
    return (np.clip(np.round(v), 0, 23) / 23 * 255 + 0.5).astype(np.uint8)


# ---- billboards (RGBA) ----------------------------------------------------------------------------------------------------------------------------------

def th_monitor() -> np.ndarray:
    """A bedside heart monitor on its pole: grey casing, a dark screen with the green trace, numbers, a pump module below."""
    c = Canvas(128)
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


def th_bed() -> np.ndarray:
    """A hospital bed side-on: head and foot boards, half rails, a blanket over the mattress, a pillow, wheels. Fills the lower half."""
    c = Canvas(128)
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
    c.put(bl & ((c.x.astype(int) % 12) == 0), "#4a6aa0")
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


def th_drip() -> np.ndarray:
    """A drip stand: a bag of fluid on the hook, the line down, a five-legged base on castors."""
    c = Canvas(128)
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


def th_desk() -> np.ndarray:
    """The nurses' station desk: a warm wooden front, a lit counter top, a computer screen, a lamp, files."""
    c = Canvas(128)
    c.rect(2, 52, 126, 58, "#e8c890")
    c.rect(2, 57, 126, 59, "#5a3a20")
    front = c.box(4, 59, 124, 120)
    c.put(front, "#a87444")
    c.rgb = np.where(front[..., None], c.rgb * (0.82 + 0.3 * px.noise(128, 6, 221))[..., None] + (np.sin(c.y * 0.8) * 0.03)[..., None], c.rgb)
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


def th_tree() -> np.ndarray:
    """A garden tree at night: a dark rounded canopy with a moonlit rim, a trunk."""
    c = Canvas(128)
    c.rect(58, 76, 70, 128, "#1a1414")
    c.rect(58, 76, 61, 128, "#3a3438")
    c.line([(64, 92), (48, 70)], "#1a1414", 3.0)
    c.line([(64, 86), (82, 66)], "#1a1414", 3.0)
    nz = px.noise(128, 5, 231, 3)
    blobs = [(64, 40, 34), (40, 60, 24), (88, 58, 26), (62, 70, 22), (50, 30, 20), (80, 30, 20)]
    m = np.zeros((128, 128), bool)
    for bx, by, r in blobs:
        m |= ((c.x - bx) ** 2 + (c.y - by) ** 2) <= (r * (0.85 + 0.3 * nz)) ** 2
    light = np.clip(((64 - c.x) + (40 - c.y)) / 80.0 + 0.4 + (nz - 0.5) * 0.6, 0, 1)
    col = px.quantise(light, px.ramp("#06100e", "#0c1c1c", "#14302c", "#22463e", "#3a6660"))
    c.put(m, col.astype(np.float32) / 255)
    c.a = np.maximum(c.a, m.astype(np.float32))
    return c.rgba8()


def th_lamppost() -> np.ndarray:
    """A garden lamp post with a warm lantern."""
    c = Canvas(128)
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


def th_chair() -> np.ndarray:
    """A day-room armchair seen from behind (they face the TV): padded back, arms, legs."""
    c = Canvas(128)
    c.rect(30, 30, 98, 86, "#3a5a8a")
    c.rgb = np.where(c.box(30, 30, 98, 86)[..., None], c.rgb * (0.85 + 0.3 * px.noise(128, 6, 241))[..., None], c.rgb)
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


def th_bench() -> np.ndarray:
    """A garden bench: wooden slats, cast-iron ends."""
    c = Canvas(128)
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


def th_vending() -> np.ndarray:
    """One vending machine: a lit window of snacks, a keypad, the tray."""
    c = Canvas(128)
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


def th_tv() -> np.ndarray:
    """The day-room television: a late-night programme glowing blue."""
    c = Canvas(128)
    c.rect(8, 28, 120, 98, "#0c1018")
    c.rect(12, 32, 116, 92, "#3a6ac0")
    t = np.clip((c.y - 32) / 60, 0, 1)
    scr = c.box(12, 32, 116, 92)
    c.rgb = np.where(scr[..., None], lerpc("#5a8ae0", "#2a4a90", t), c.rgb)
    c.put(scr & (c.y > 70), "#2a6a5a")
    c.disc(90, 46, 6, "#f0e8b0")
    c.rect(40, 54, 48, 72, "#e8d0c0")
    c.disc(44, 50, 4, "#e8d0c0")
    c.put(scr & (c.y % 3 == 0), "#000000", 0.18)
    c.rect(58, 98, 70, 108, "#141820")
    c.rect(44, 108, 84, 112, "#141820")
    return c.rgba8()


def th_door_lit() -> np.ndarray:
    """Double doors at the end of the quiet corridor, light beyond them through the windows and the gap."""
    c = Canvas(128)
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

def th_mic() -> np.ndarray:
    """A bandstand microphone (128 px, 1.5 m): a brass-footed stand, the boom, a silver ball mic with a warm lamp-reflection, the lead looping across the boards."""
    c = Canvas(128)
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
    # the map's billboards name these two by their wall ids (tests check the cafeteria's machines and the day room's TV by them), so the props carry those
    # ids and the walls showing them swap to the *_wall tiles through the map's `animated` swap (StoryWorld swaps surfaces only, never billboards)
    "wall_vending": th_vending, "wall_tv": th_tv,
}


def build() -> dict:
    for tid, fn in sorted(THINGS.items()):
        save_rgba(tid, fn())
    return {
        "ceil_tile": (ceil_tile(), 2.4),
        "floor_ward": (lino(128, "#1c2848", "#5a7ac0", 64, 301), 2.0),
        "floor_check": (lino(128, "#2a2a4a", "#c8a070", 64, 302, 0.22, "#6a6a98", ("#2c2e50", "#262848")), 2.0),
        "floor_lino": (lino(128, "#203450", "#6a8ab8", 64, 303, 0.22, "#6a8aa0"), 2.0),
        "wall_ward": (wall_ward(), 2.7),
        "wall_dayroom": (wall_dayroom(), 2.2),
        "wall_window": (wall_window(), 5.0),
        "wall_curtain": (wall_curtain(), 1.5),
        "wall_door": (wall_door(), 2.6),
        "wall_station": (wall_station(), 2.6),
        "wall_counter": (wall_counter(), 2.0),
        "wall_vending_wall": (wall_vending(), 4.8),
        "wall_cafe": (wall_cafe(), 4.8),
        "floor_cafe": (floor_cafe(), 1.6),
        "wall_brick": (wall_brick(), 6.0),
        "wall_hedge": (wall_hedge(), 3.0),
        "floor_stone": (floor_stone(), 3.0),
        "wall_quiet": (wall_quiet(), 2.4),
        "wall_tv_wall": (wall_tv(), 3.0),
        "trim": (trim(), 2.0),
        "sky_night": (sky_night(), 1.0),
    }
