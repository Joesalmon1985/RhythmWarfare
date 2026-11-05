"""The Mission Count's harbour art world (docs/THREE_PATHS_AND_FACES_PLAN.md 5): a cold blue night cut by white searchlight beams (quay, boat with one warm gold lantern, net sheds, a
stone cell with a latch window and a moonlight shaft), and the NEUTRAL COAST, the only saturated place of the whole path (golden sand, turquoise sea, cobalt sky, bright pines, blue and
white paint). The count board, the broken radio and the aircraft door are the briefing hut again (khaki, dust, white glare, warm bulbs).

`DRAW = {id: fn}`; every fn() takes no argument and returns a uint8 array: surfaces and ceilings (n, n, 3), the sky (64, 256, 3), billboards (128, 128, 4) or (128, 256, 4) for the wide
props, hard alpha except the beam and the birds. Deterministic: seeded generators only, no clock, nothing downloaded.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from .pixeltex import BAYER8, bricks, grid, grime, hexc, noise, quantise, ramp, speckle

# ---- palettes (dark to light) ------------------------------------------------------------------------------------------------------------------
STONEB = ramp("#05080e", "#0b111b", "#141c2a", "#1e293b", "#2c3b52", "#41567a")      # cold night stone
MORT = ramp("#02040a", "#070c14", "#0d1522")
PLK = ramp("#06060a", "#100f12", "#1c1a1c", "#2a2624", "#3b342e", "#52483c")            # wet dark planks
POOL = ramp("#060e1a", "#0c1c34", "#142e52", "#1f4678", "#336ca8", "#6aa0d4", "#d8f0ff")
ROPE = ramp("#16110a", "#33281a", "#54432a", "#7a6340", "#a08a5c", "#c4ae80")
WEED = ramp("#030d0a", "#07201a", "#0e3a28", "#176040", "#278a54", "#3fb06c")
IRONN = ramp("#04060a", "#0b0f16", "#161d29", "#252f40", "#394860", "#566a8a")
STRAW = ramp("#1a1306", "#3a2a0e", "#6a4e1c", "#9c7a30", "#c8a44c", "#e8cc78")
NIGHT = ramp("#02050c", "#060d1e", "#0c1a38", "#162c54", "#244a7c", "#4a7cb0", "#a8c8e8", "#eef6ff")
SAND = ramp("#9a6222", "#bc7f2e", "#da9e3c", "#eebb52", "#f9d472", "#fff0a4")
GRASS = ramp("#12400e", "#1f6c14", "#34a01e", "#5cc830", "#98ec50", "#d4ff84")
HAZE = ramp("#a8d8e0", "#c8e8ec", "#e2f4f0", "#f6fbee", "#fffbe0")
COBALT = ramp("#0a2cb0", "#1248d0", "#1e64e8", "#3a84f6", "#78b0ff", "#c2dcff", "#ffffff")
WARMG = ramp("#ffd060", "#ffe486", "#fff2b8", "#fffbe0")
KHAKI = ramp("#241c0e", "#40341a", "#64542c", "#8a7642", "#b09c5e", "#d4c288", "#f0e4b8")
WOODN = ramp("#07050a", "#150e10", "#271a14", "#3c281c", "#563a26", "#744e32")
WOODB = ramp("#2c1608", "#4e2a10", "#764219", "#a2622a", "#c8863e", "#e8aa5c")
GOLDL = ramp("#5a2c06", "#a0600e", "#dc9a22", "#ffc84a", "#ffe690", "#fffadc")
GREYB = ramp("#0a0c10", "#181c22", "#2a3038", "#3e4650", "#566068", "#76828a")
BLUEG = ramp("#0c1a30", "#1c3a6c", "#2e64b0", "#4890e0", "#8cc0ff", "#dcf0ff")
TURQ = ramp("#04607a", "#08889c", "#14b0b8", "#34d0c8", "#7ae8d8", "#c8fff0")
PAINTW = ramp("#6a7a88", "#9aa8b4", "#c8d4dc", "#eaf0f2", "#ffffff")
PAINTB = ramp("#0a2a70", "#1244b0", "#1c62dc", "#3888f0", "#78b8ff")
TRUNK = ramp("#2a1408", "#4a2810", "#70401a", "#9a5c28", "#c4823e")
PINEG = ramp("#0c3a10", "#17601a", "#25901f", "#3cc02c", "#74e850", "#b8ff86")
ORANGE = ramp("#8a3408", "#c85a14", "#f08828", "#ffb050", "#ffe2a0")
LGLASS = ramp("#0c1c34", "#1c3c70", "#3a70b8", "#74b0f0", "#c4e4ff")
TARP = ramp("#050a12", "#0d1622", "#18283a", "#243a52", "#35506c")
NETN = ramp("#070b0c", "#101a18", "#1c2c28", "#2c4238", "#425c4c", "#5e7c68")
NETD = ramp("#4a3a14", "#7a6224", "#a8883a", "#d0ac52", "#f0d078")


def _rs(seed: int) -> np.random.RandomState:
    return np.random.RandomState(seed)


def fnoise(shape, scale: float, seed: int, octaves: int = 3) -> np.ndarray:
    n = max(shape)
    return noise(n, scale, seed, octaves)[: shape[0], : shape[1]]


def wd(a: np.ndarray, c: float, n: float) -> np.ndarray:
    """Wrapped signed distance on a ring of length n."""
    return (a - c + n / 2) % n - n / 2


def col3(h: str) -> np.ndarray:
    return (hexc(h) * 255 + 0.5).astype(np.uint8)


def bay(shape) -> np.ndarray:
    return BAYER8[np.arange(shape[0])[:, None] % 8, np.arange(shape[1])[None, :] % 8] + 0.5


class Cv:
    """An RGBA canvas (h x w) whose shapes are masks (rasterised by PIL without antialiasing), shaded by palette ramps with ordered dither."""

    def __init__(self, h: int = 128, w: int = 128, opaque: bool = False):
        self.h, self.w = h, w
        self.rgb = np.zeros((h, w, 3), np.uint8)
        self.a = np.full((h, w), 255 if opaque else 0, np.uint8)
        self.y, self.x = np.mgrid[0:h, 0:w].astype(np.float32)
        self.b = bay((h, w))

    def _m(self, fn) -> np.ndarray:
        im = Image.new("L", (self.w, self.h), 0)
        fn(ImageDraw.Draw(im))
        return np.asarray(im) > 0

    def poly(self, pts) -> np.ndarray:
        return self._m(lambda d: d.polygon([(float(p[0]), float(p[1])) for p in pts], fill=255))

    def line(self, pts, w: int = 1) -> np.ndarray:
        return self._m(lambda d: d.line([(float(p[0]), float(p[1])) for p in pts], fill=255, width=w, joint="curve"))

    def rect(self, x0, y0, x1, y1) -> np.ndarray:
        return (self.x >= x0) & (self.x < x1) & (self.y >= y0) & (self.y < y1)

    def ell(self, cx, cy, rx, ry) -> np.ndarray:
        return ((self.x + 0.5 - cx) / rx) ** 2 + ((self.y + 0.5 - cy) / ry) ** 2 <= 1.0

    def ring(self, cx, cy, rx, ry, t) -> np.ndarray:
        return self.ell(cx, cy, rx, ry) & ~self.ell(cx, cy, rx - t, ry - t * ry / rx)

    def paint(self, mask, shade, pal, dither: float = 1.0) -> None:
        sh = shade if isinstance(shade, np.ndarray) else np.full((self.h, self.w), float(shade), np.float32)
        k = len(pal) - 1
        i = np.clip(np.round(np.clip(sh, 0, 1) * k + (self.b - 0.5) * dither), 0, k).astype(int)
        col = (pal[i] * 255 + 0.5).astype(np.uint8)
        self.rgb[mask] = col[mask]
        self.a[mask] = 255

    def solid(self, mask, colour) -> None:
        self.rgb[mask] = col3(colour) if isinstance(colour, str) else np.asarray(colour, np.uint8)
        self.a[mask] = 255

    def lit(self, mask, base=0.5, amp=0.3, pal=None, dither: float = 1.0, tilt=(0.6, 0.4), seed=None, grain=0.0):
        """Bevel-style shade over a mask: light from the upper left across its bounding box."""
        ys, xs = np.nonzero(mask)
        if len(ys) == 0:
            return np.zeros((self.h, self.w), np.float32)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        u = np.clip((self.x - x0) / max(x1 - x0, 1), 0, 1)
        v = np.clip((self.y - y0) / max(y1 - y0, 1), 0, 1)
        sh = base + amp * (0.5 - tilt[0] * u - tilt[1] * v) * 1.6
        if grain and seed is not None:
            sh = sh + (fnoise((self.h, self.w), 5, seed, 2) - 0.5) * grain
        if pal is not None:
            self.paint(mask, sh, pal, dither)
        return sh

    def hs(self, x0, x1, base=0.5, amp=0.35) -> np.ndarray:
        """A cylinder's left-lit shade across x0..x1."""
        u = np.clip((self.x - x0) / max(x1 - x0, 1), 0, 1)
        return base + amp * (0.6 - u) + 0.1 * np.sin(u * np.pi)

    def vs(self, y0, y1, base=0.5, amp=0.35) -> np.ndarray:
        u = np.clip((self.y - y0) / max(y1 - y0, 1), 0, 1)
        return base + amp * (0.6 - u) + 0.1 * np.sin(u * np.pi)

    def outline(self, k: float = 0.42) -> None:
        a = self.a > 0
        p = np.pad(a, 1, constant_values=True)
        edge = a & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
        self.rgb[edge] = (self.rgb[edge].astype(np.float32) * k).astype(np.uint8)

    def glow(self, cx, cy, r, bright, dim, power: float = 1.6, over: bool = False, squash: float = 1.0) -> None:
        """A dithered halo on transparent (or, with over, any) pixels: hard alpha, bright centre fading out."""
        d = np.sqrt((self.x - cx) ** 2 + ((self.y - cy) / squash) ** 2) / r
        s = np.clip(1 - d, 0, 1) ** power
        m = (s > self.b * 0.95) & (d < 1)
        if not over:
            m &= self.a == 0
        t = np.clip(s * 1.4, 0, 1)[..., None]
        c = (col3(dim) * (1 - t) + col3(bright) * t).astype(np.uint8)
        self.rgb[m] = c[m]
        self.a[m] = 255

    def tint_light(self, mask, strength, colour="#ffffff") -> None:
        """Lighten existing pixels of a mask towards a colour with dither (a shaft of light on a wall)."""
        s = np.clip(strength, 0, 1) if isinstance(strength, np.ndarray) else np.full((self.h, self.w), strength, np.float32)
        m = mask & (self.a > 0) & (s > self.b * 0.9)
        t = np.clip(s * 1.2, 0, 1)[..., None]
        c = (self.rgb.astype(np.float32) * (1 - t * 0.7) + col3(colour).astype(np.float32) * t * 0.7).astype(np.uint8)
        self.rgb[m] = c[m]

    def out(self) -> np.ndarray:
        return np.dstack([self.rgb, self.a])


def wline(cv: Cv, pts, w: int = 1) -> np.ndarray:
    """A polyline that wraps around the tile edges (draws it at -n, 0, +n)."""
    m = np.zeros((cv.h, cv.w), bool)
    for ox in (-cv.w, 0, cv.w):
        for oy in (-cv.h, 0, cv.h):
            m |= cv.line([(p[0] + ox, p[1] + oy) for p in pts], w)
    return m


def wpoly(cv: Cv, pts) -> np.ndarray:
    m = np.zeros((cv.h, cv.w), bool)
    for ox in (-cv.w, 0, cv.w):
        for oy in (-cv.h, 0, cv.h):
            m |= cv.poly([(p[0] + ox, p[1] + oy) for p in pts])
    return m


def _put(base: np.ndarray, mask, colour) -> None:
    base[mask] = col3(colour) if isinstance(colour, str) else colour


# ============================================================================================================================================
# SURFACES
# ============================================================================================================================================

def floor_quay(n: int = 128):
    """Wet dark quay: a band of stone setts and a band of planks, puddles holding the blue night, a coil of rope or two."""
    x, y = grid(n)
    rng = _rs(611)
    # setts: rows 12 px, 6 stones a row, every other row shifted half a stone
    rh, sw = 12.0, n / 6.0
    r = np.floor(y / rh)
    off = (r % 2) * sw * 0.5
    c = np.floor(((x + off) % n) / sw)
    tone = rng.rand(6, 7).astype(np.float32)
    t = tone[r.astype(int) % 6, c.astype(int) % 7]
    ly = y - r * rh
    lx = ((x + off) % n) - c * sw
    mort = (ly < 1.4) | (lx < 1.4)
    corner = ((lx < 3) & (ly < 3.4)) | ((lx > sw - 2.2) & (ly > rh - 2.4))
    sett = 0.3 + 0.2 * t + 0.12 * ((ly < 3.4) & ~mort) - 0.1 * (ly > rh - 2.5) + (noise(n, 6, 612) - 0.5) * 0.18 - 0.1 * corner
    sett = np.where(mort, 0.04, sett)
    # planks: 4 boards of 14 px across the bottom 56 px, joints staggered
    py = y - 72
    pr = np.floor(py / 14.0)
    poff = rng.rand(4) * n
    px = (x + poff[np.clip(pr, 0, 3).astype(int)]) % n
    plt_ = rng.rand(4)[np.clip(pr, 0, 3).astype(int)]
    joint = ((py % 14.0) < 1.3) | (px < 1.3)
    grain = np.sin(x * 0.55 + noise(n, 14, 613) * 9.0 + pr * 2.0) * 0.07 + (noise(n, 4, 614) - 0.5) * 0.12
    plank = 0.3 + 0.16 * plt_ + grain - 0.22 * joint + 0.08 * ((py % 14.0) > 11)
    is_plank = y >= 72
    shade = np.where(is_plank, plank, sett)
    rgb = np.where(is_plank[..., None], quantise(np.clip(plank, 0, 1), PLK), quantise(np.clip(sett, 0, 1), STONEB))
    rgb = rgb.copy()
    # nail heads on the planks
    for yy in (72 + 7, 72 + 21, 72 + 35, 72 + 49):
        for xx in range(6, n, 21):
            rgb[int(yy) % n, int(xx + yy) % n] = col3("#6a7a90")
    # puddles
    v = noise(n, 26, 615, 3)
    pud = v > 0.7
    edge = pud & ~(np.roll(pud, 1, 0) & np.roll(pud, -1, 0) & np.roll(pud, 1, 1) & np.roll(pud, -1, 1))
    streak = noise(n, 12, 616, 2)
    ps = 0.18 + 0.3 * streak + 0.22 * np.clip((v - 0.7) * 8, 0, 1) * (noise(n, 5, 617) > 0.45)
    prgb = quantise(np.clip(ps, 0, 1), POOL)
    rgb = np.where(pud[..., None], prgb, rgb)
    rgb[edge] = col3("#0a1424")
    sparkle = speckle(n, 0.01, 618) > 0
    rgb[sparkle & pud] = col3("#f0faff")
    # a rope coil on the planks, a small one on the setts
    cv = Cv(n, n, True)
    cv.rgb[:] = rgb
    for cx, cy, rr in ((40, 100, 15), (100, 34, 10)):
        dx, dy = wd(x, cx, n), wd(y, cy, n) * 1.55
        d = np.sqrt(dx * dx + dy * dy)
        ang = np.arctan2(dy, dx)
        m = (d < rr) & (d > rr * 0.32)
        strand = 0.5 + 0.28 * np.sin(d * 1.9) * np.sign(np.sin(ang * 14 + d * 0.5) + 0.3) * 0.6 + 0.2 * np.sin(d * 1.9) - 0.18 * (d / rr) + 0.12 * (dx + dy < 0)
        shadow = (np.sqrt(wd(x, cx + 2, n) ** 2 + (wd(y, cy + 3, n) * 1.55) ** 2) < rr + 1) & ~m
        cv.rgb[shadow] = (cv.rgb[shadow] * 0.5).astype(np.uint8)
        cv.paint(m, strand, ROPE)
        cv.rgb[(d <= rr * 0.32)] = col3("#05070c")
    return cv.rgb


def wall_quay(n: int = 128):
    """Cold dark harbour wall: wet ashlar in blue night light, green weed at the foot, an iron mooring ring on its staple."""
    x, y = grid(n)
    sh, mort = bricks(n, rows=6, cols=3, mortar=1, seed=621, wear=0.5)
    sh = 0.2 + sh * 0.5
    # a cold light from the upper right, wet darkness creeping up from the weed
    lightp = np.exp(-(((wd(x, 86, n)) / 46.0) ** 2 + ((y - 24) / 40.0) ** 2))
    sh += lightp * 0.2
    sh -= 0.18 * np.clip((y - 70) / 40.0, 0, 1)
    sh += (grime(n, 622, 0.5, drip=True) - 0.2) * -0.18
    wet = (noise(n, 9, 623, 2) > 0.66) & (y > 60) & (mort < 0.5)
    sh = np.where(wet, sh - 0.12, sh)
    rgb = quantise(np.clip(sh, 0, 1), STONEB)
    rgb = np.where(((mort > 0.5))[..., None], quantise(np.full((n, n), 0.45, np.float32) - 0.25 * np.clip((y - 60) / 60.0, 0, 1), MORT), rgb)
    cv = Cv(n, n, True)
    cv.rgb[:] = rgb
    # weed: ragged fronds up from the base
    rng = _rs(624)
    height = 18 + 14 * noise(n, 12, 625, 2) + 6 * np.sin(x * 0.9) * (noise(n, 3, 626) > 0.4)
    weed = y > (n - height)
    fr = noise(n, 3, 627, 2)
    cv.paint(weed, 0.12 + 0.4 * fr + 0.18 * ((y - (n - height)) / height) * -1, WEED, 0.7)
    streaks = (fr > 0.7) & weed & (y < n - 8)
    cv.rgb[streaks] = col3("#278a54")
    # iron ring on a staple
    cx, cy = 44, 50
    cv.paint(cv.rect(cx - 5, cy - 18, cx + 5, cy - 8), 0.45, IRONN)
    cv.paint(cv.ell(cx, cy - 18, 8, 3), 0.4, IRONN)
    rm = cv.ring(cx, cy, 12, 12, 4)
    cv.paint(rm, 0.6 + 0.35 * np.clip(1 - (cv.x - cx + cv.y - cy) / 24, 0, 1) - 0.2 * (cv.y > cy + 4), IRONN)
    cv.rgb[cv.ring(cx, cy, 12, 12, 1) & (cv.x < cx) & (cv.y < cy)] = col3("#9ab4d6")
    cv.rgb[cv.ell(cx, cy + 18, 11, 3) & (cv.y > cy + 14)] = (cv.rgb[cv.ell(cx, cy + 18, 11, 3) & (cv.y > cy + 14)] * 0.55).astype(np.uint8)
    return cv.rgb


def floor_cell(n: int = 128):
    """Cold stone cell floor: big flags, a round drain with a grate, a straw heap and a damp patch."""
    x, y = grid(n)
    sh, mort = bricks(n, rows=2, cols=2, mortar=2, seed=631, wear=0.6)
    sh = 0.18 + sh * 0.42 + (noise(n, 5, 632) - 0.5) * 0.12
    # damp patch
    dpm = np.sqrt(wd(x, 30, n) ** 2 + (wd(y, 100, n) * 1.3) ** 2) + (noise(n, 10, 633) - 0.5) * 16
    damp = dpm < 18
    sh = np.where(damp, sh - 0.1, sh)
    rgb = quantise(np.clip(sh, 0, 1), STONEB)
    rgb = np.where((mort > 0.5)[..., None], quantise(np.full((n, n), 0.2, np.float32), MORT), rgb)
    cv = Cv(n, n, True)
    cv.rgb[:] = rgb
    sheen = damp & (noise(n, 4, 634) > 0.62)
    cv.rgb[sheen] = col3("#4c6a92")
    # the drain
    cx, cy = 30, 36
    cv.paint(cv.ell(cx, cy, 13, 13), 0.4, IRONN)
    cv.rgb[cv.ell(cx, cy, 10, 10)] = col3("#02040a")
    for k in range(-3, 4):
        bar = cv.rect(cx + k * 3 - 1, cy - 10, cx + k * 3 + 1, cy + 10) & cv.ell(cx, cy, 10, 10)
        cv.rgb[bar] = col3("#3c4a60")
    cv.rgb[cv.ring(cx, cy, 13, 13, 1.5) & (cv.x < cx + 4) & (cv.y < cy + 4)] = col3("#5c7090")
    # straw heap
    rng = _rs(635)
    cx, cy = 92, 92
    for i in range(70):
        ang = rng.rand() * np.pi
        L = 5 + rng.rand() * 7
        px = cx + rng.randn() * 11
        py = cy + rng.randn() * 8
        seg = cv.line([(px, py), (px + np.cos(ang) * L, py - np.sin(ang) * L * 0.6)], 1)
        cv.rgb[seg] = col3(["#7a5c22", "#a8842e", "#c8a44c", "#5a4216"][int(rng.rand() * 4)])
    return cv.rgb


def wall_cell(n: int = 128):
    """Damp grey stone blocks, tally scratches in fives, a pale smear of moonlight, drips running down."""
    x, y = grid(n)
    sh, mort = bricks(n, rows=6, cols=3, mortar=1, seed=641, wear=0.7)
    sh = 0.22 + sh * 0.45
    sm = np.exp(-(wd(x + y, 70, n) / 12.0) ** 2) * (0.55 + 0.45 * noise(n, 14, 642))
    sh += sm * 0.3
    sh -= grime(n, 643, 0.6, drip=True) * 0.22
    rgb = quantise(np.clip(sh, 0, 1), STONEB)
    rgb = np.where((mort > 0.5)[..., None], quantise(np.full((n, n), 0.4, np.float32), MORT), rgb)
    cv = Cv(n, n, True)
    cv.rgb[:] = rgb
    rng = _rs(644)
    # tally marks: four strokes and a slash, in groups, every stroke a little off true
    for gx, gy, cnt in ((22, 30, 5), (60, 36, 5), (96, 44, 3), (30, 84, 5), (74, 92, 2)):
        for k in range(cnt):
            if k < 4:
                x0 = gx + k * 4 + rng.rand()
                a = [(x0, gy + rng.rand() * 2), (x0 + rng.rand() * 1.4 - 0.7, gy + 11 + rng.rand() * 2)]
            else:
                a = [(gx - 2, gy + 9), (gx + 16, gy + 2)]
            ln = cv.line(a, 1)
            sh_ = np.roll(np.roll(ln, 1, 0), 1, 1)
            cv.rgb[sh_ & ~ln] = col3("#05080e")
            cv.rgb[ln] = col3("#8da2bf")
    # drips: a dark thread down from a joint, a bright bead at the end
    for dx in (14, 52, 88, 116):
        top = int(rng.rand() * 50) + 10
        ln = int(18 + rng.rand() * 26)
        cv.rgb[top:top + ln, dx] = (cv.rgb[top:top + ln, dx] * 0.55).astype(np.uint8)
        cv.rgb[top + ln: top + ln + 2, dx] = col3("#7ea0cc")
    return cv.rgb


def ceil_cell(n: int = 64):
    """A dark vaulted stone ceiling: groin ribs crossing, with a single iron ring where they meet."""
    x, y = grid(n)
    sh, mort = bricks(n, rows=8, cols=4, mortar=1, seed=651, wear=0.4)
    sh = 0.14 + sh * 0.3
    d1 = np.abs(wd(x - y, 0, n))
    d2 = np.abs(wd(x + y, 0, n))
    rib = np.minimum(d1, d2) * 0.7071
    ribm = rib < 4.0
    sh = np.where(ribm, 0.38 + 0.25 * (1 - rib / 4.0) + (noise(n, 5, 652) - 0.5) * 0.15, sh)
    # the web darkens towards the middle of each bay
    sh -= 0.08 * (1 - np.clip(rib / 16.0, 0, 1)) * -1
    rgb = quantise(np.clip(sh, 0, 1), STONEB)
    rgb = np.where(((mort > 0.5) & ~ribm)[..., None], quantise(np.full((n, n), 0.3, np.float32), MORT), rgb)
    cv = Cv(n, n, True)
    cv.rgb[:] = rgb
    cx = cy = 32
    cv.paint(cv.rect(cx - 7, cy - 7, cx + 7, cy + 7), 0.3, IRONN)
    cv.rgb[cv.ell(cx, cy, 6, 6)] = col3("#02040a")
    rm = cv.ring(cx, cy + 1, 6, 6, 2)
    cv.paint(rm, 0.5 + 0.3 * (cv.x < cx) * (cv.y < cy), IRONN)
    cv.rgb[cv.rect(cx - 1, cy - 8, cx + 1, cy - 5)] = col3("#566a8a")
    return cv.rgb


def ceil_night_blue(n: int = 64):
    """A painted cold night sky: searchlight smears crossing it, a few stars, high thin cloud."""
    x, y = grid(n)
    base = 0.2 + 0.07 * noise(n, 24, 661, 3)
    b1 = np.exp(-(wd(x + 2 * y, 22, n) / 9.0) ** 2) * 0.3
    b2 = np.exp(-(wd(2 * x + y, 46, n) / 6.0) ** 2) * 0.24
    cl = noise(n, 22, 662, 3)
    cl = cl[(np.arange(n) * 3 % n)[:, None], np.arange(n)[None, :]]
    cloud = np.clip((cl - 0.5) * 2.4, 0, 1) * 0.28
    sh = base + b1 + b2 + cloud
    rgb = quantise(np.clip(sh, 0, 1), NIGHT, 0.9)
    st = speckle(n, 0.012, 663) > 0
    rgb[st] = col3("#cfe2ff")
    st2 = speckle(n, 0.004, 664) > 0
    rgb[st2] = col3("#ffffff")
    return rgb


def ceil_sky_day(n: int = 64):
    """A bright saturated cobalt sky, soft white clouds, a warm sun glow: the only saturated sky of the path."""
    x, y = grid(n)
    base = 0.22 + 0.12 * noise(n, 30, 671, 3)
    v = noise(n, 32, 672, 3)
    dn = np.roll(np.roll(v, 2, 0), 2, 1)
    dens = np.clip((v - 0.52) * 4.5, 0, 1)
    lit = np.clip((v - dn) * 9, -1, 1) * 0.12
    sh = np.where(dens > 0, base + 0.15 + 0.62 * dens + lit, base)
    sh = np.clip(sh, 0, 1)
    rgb = quantise(sh, COBALT)
    dx, dy = wd(x, 44, n), wd(y, 20, n)
    g = np.exp(-(dx * dx + dy * dy) / (2 * 7.0 ** 2)) * 0.8
    m = g > (bay((n, n)) * 0.85)
    wrm = quantise(np.clip(g * 1.5, 0, 1), WARMG)
    rgb = np.where(m[..., None], wrm, rgb)
    return rgb


def floor_sand(n: int = 128):
    """Warm bright golden sand: wind ripples, tiny shells, a pair of footprints, a line of dry seaweed."""
    x, y = grid(n)
    warp = noise(n, 36, 681, 3)
    rip = np.sin((y / n * 7 + warp * 1.6) * 2 * np.pi)
    sh = 0.6 + 0.1 * rip + (noise(n, 5, 682) - 0.5) * 0.2 + (noise(n, 2, 683, 2) - 0.5) * 0.12
    rgb = quantise(np.clip(sh, 0, 1), SAND)
    cv = Cv(n, n, True)
    cv.rgb[:] = rgb
    # speckle grain
    cv.rgb[speckle(n, 0.03, 684) > 0] = col3("#fff0a4")
    cv.rgb[speckle(n, 0.025, 685) > 0] = col3("#bc7f2e")
    # footprints: heel and ball and five toes, a darker dent with a bright rim to the lower right
    for fx, fy, flip in ((34, 38, 1), (50, 66, -1)):
        parts = [(fx, fy + 9, 3.4, 4.2), (fx, fy - 1, 4.2, 6.0)]
        toes = [(fx - 4 * flip, fy - 9, 1.4), (fx - 2 * flip, fy - 11, 1.6), (fx + 1 * flip, fy - 11.5, 1.5), (fx + 3.5 * flip, fy - 10, 1.4), (fx + 5.5 * flip, fy - 7, 1.1)]
        dent = np.zeros((n, n), bool)
        for cx, cy, rx, ry in parts:
            dent |= cv.ell(cx, cy, rx, ry)
        for cx, cy, r in toes:
            dent |= cv.ell(cx, cy, r, r)
        rim = np.roll(np.roll(dent, 1, 0), 1, 1) & ~dent
        cv.rgb[rim] = col3("#fff0a4")
        cv.paint(dent, 0.2 + 0.1 * (cv.y > fy), SAND)
    # shells
    rng = _rs(686)
    for i in range(9):
        sx, sy = int(rng.rand() * (n - 4)), int(rng.rand() * (n - 4))
        c = ["#ffe4d6", "#ffffff", "#f6b8a0", "#fff6e8"][i % 4]
        cv.rgb[sy:sy + 2, sx:sx + 3] = col3(c)
        cv.rgb[sy + 2, sx + 1:sx + 4] = col3("#9a6222")
    # a wavy line of dry seaweed
    yy = 104 + 6 * np.sin(x / n * 2 * np.pi * 2) + (noise(n, 8, 687) - 0.5) * 10
    lump = (np.abs(y - yy) < 1.2 + 2.4 * noise(n, 4, 688)) & (noise(n, 3, 689) > 0.42)
    cv.paint(lump, 0.2 + 0.7 * noise(n, 2, 690), ramp("#2c260c", "#4c3e14", "#6a5a22", "#8c7a38"))
    sd = np.roll(np.roll(lump, 1, 0), 2, 1) & ~lump
    cv.rgb[sd] = col3("#9a6222")
    return cv.rgb


def wall_dunes(n: int = 128):
    """Bright sandy dunes with tufts of green marram grass under a white wall of sea haze: saturated and warm."""
    x, y = grid(n)
    cv = Cv(n, n, True)
    hz = 0.2 + 0.7 * np.clip(y / 46.0, 0, 1) ** 0.9 + (noise(n, 24, 701, 2) - 0.5) * 0.18
    cv.rgb[:] = quantise(np.clip(hz, 0, 1), HAZE)
    # a faint turquoise sea line in the haze
    sea = (y > 40) & (y < 45)
    cv.paint(sea, 0.45 + 0.3 * (y - 40) / 5.0 + (noise(n, 6, 702) - 0.5) * 0.3, TURQ)
    ridge = 52 + 6 * np.sin(x / n * 2 * np.pi * 2 + 1.0) + 3 * np.sin(x / n * 2 * np.pi * 5 + 0.4)
    ridge2 = 82 + 8 * np.sin(x / n * 2 * np.pi * 3 + 2.4) + 3 * np.sin(x / n * 2 * np.pi * 7)
    far = y > ridge
    near = y > ridge2
    rip = np.sin((x * 0.25 + y * 0.18 + noise(n, 20, 703) * 5)) * 0.06
    slope = np.gradient(ridge, axis=1) * 0.5
    sf = 0.5 + 0.35 * np.clip(1 - (y - ridge) / 30.0, 0, 1) - 0.4 * np.clip(slope, 0, 1) + rip + (noise(n, 5, 704) - 0.5) * 0.14
    cv.paint(far, sf, SAND)
    slope2 = np.gradient(ridge2, axis=1) * 0.5
    sn = 0.58 + 0.3 * np.clip(1 - (y - ridge2) / 34.0, 0, 1) - 0.35 * np.clip(slope2, 0, 1) + rip * 1.5 + (noise(n, 5, 705) - 0.5) * 0.14
    cv.paint(near, sn, SAND)
    cv.rgb[(speckle(n, 0.02, 706) > 0) & far] = col3("#fff0a4")
    # marram tufts: fans of green blades
    rng = _rs(707)
    tufts = [(16, 0, 14), (50, 0, 11), (86, 0, 15), (112, 0, 10), (30, 1, 20), (72, 1, 24), (104, 1, 18)]
    for tx, layer, L in tufts:
        by = (ridge2[0, int(tx)] if layer else ridge[0, int(tx)]) + 3 + (6 if layer else 0)
        for k in range(9):
            ang = (k - 4) * 0.2 + rng.randn() * 0.06
            ln = L * (0.65 + 0.5 * rng.rand()) * (1 - abs(k - 4) * 0.06)
            tip = (tx + np.sin(ang) * ln + rng.randn() * 2.5, by - np.cos(ang) * ln)
            mid = (tx + np.sin(ang) * ln * 0.5, by - np.cos(ang) * ln * 0.55)
            m = wline(cv, [(tx + (k - 4) * 0.7, by), mid, tip], 1 + (layer and k % 2 == 0))
            sh = 0.2 + 0.7 * (1 - np.clip((by - cv.y) / max(ln, 1), 0, 1)) * 0.0 + 0.1 * (k % 3) + 0.4 * np.clip((by - cv.y) / max(ln, 1), 0, 1)
            cv.paint(m, np.full((n, n), 0.25 + 0.15 * (k % 3), np.float32) + 0.45 * np.clip((by - cv.y) / max(ln, 1), 0, 1), GRASS)
    return cv.rgb


def sky_harbour():
    """A cold blue night strip, 256 x 64, wrapping once around: deep navy to a paler horizon, a few small stars, thin high cloud, a pale smear of moon glow."""
    h, w = 64, 256
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    t = y / (h - 1)
    base = 0.1 + 0.42 * t ** 1.5
    cl = noise(256, 40, 711, 3)[:h * 4, :w]
    cl = cl[(np.arange(h) * 4)[:, None], np.arange(w)[None, :]]
    cloud = np.clip((cl - 0.52) * 2.8, 0, 1) * 0.2 * (0.3 + t)
    mx, my = 170, 22
    dx = wd(x, mx, w)
    glow = np.exp(-((dx / 40.0) ** 2 + ((y - my) / 18.0) ** 2)) * 0.5
    streak = np.exp(-((dx / 90.0) ** 2 + ((y - my - 14) / 5.0) ** 2)) * 0.18 * noise(256, 16, 712, 2)[:h, :w]
    sh = base + cloud + glow + streak
    rgb = quantise(np.clip(sh, 0, 1), NIGHT, 0.9)
    b = bay((h, w))
    st = (speckle(256, 0.012, 713)[:h, :w] > 0) & (t < 0.7)
    rgb[st] = col3("#cfe2ff")
    st2 = (speckle(256, 0.004, 714)[:h, :w] > 0) & (t < 0.6)
    rgb[st2] = col3("#ffffff")
    # a small moon core
    core = (np.sqrt((dx) ** 2 + (y - my) ** 2) < 3.2)
    rgb[core] = col3("#f4f8ff")
    rgb[core & (dx > 0.5) & (y > my)] = col3("#bcd0ea")
    return rgb


# ============================================================================================================================================
# BILLBOARDS: the night harbour and the cell
# ============================================================================================================================================
RUSTR = ramp("#1e0a04", "#3e1608", "#6a2a0e", "#964016", "#c0622a")
BARS = ramp("#04060a", "#0c1018", "#1a2230", "#2e3a4e", "#4a5c78", "#7890b4")


def _rope_band(c: Cv, cx, cy, rx, ry, t, seed=0):
    """A front-facing rope turn around a post: the lower arc of an ellipse, twisted strands."""
    band = c.ell(cx, cy, rx, ry) & ~c.ell(cx, cy - t, rx, ry)
    sh = 0.5 + 0.3 * np.sin(c.x * 0.95 + seed) - 0.15 * ((c.y - cy) / ry) + 0.12 * (c.x < cx)
    c.paint(band, sh, ROPE)
    return band


def thing_bollard():
    """An iron mooring bollard on a wet stone footing, a coil of rope wound round it and its tail on the quay."""
    c = Cv()
    foot = c.ell(64, 116, 54, 9)
    c.paint(foot, 0.35 + 0.3 * (c.x < 60) + (fnoise((128, 128), 3, 801) - 0.5) * 0.3, STONEB)
    c.paint(c.ell(64, 112, 40, 6), c.hs(24, 104, 0.45, 0.4), IRONN)
    body = c.poly([(42, 114), (86, 114), (80, 66), (48, 66)])
    c.paint(body, c.hs(42, 86, 0.55, 0.5) + (fnoise((128, 128), 4, 802) - 0.5) * 0.12, IRONN)
    rst = (fnoise((128, 128), 6, 803, 3) > 0.62) & body
    c.paint(rst, 0.35 + 0.4 * fnoise((128, 128), 2, 804), RUSTR)
    lip = c.ell(64, 64, 33, 8)
    c.paint(lip, c.hs(31, 97, 0.5, 0.5), IRONN)
    dome = c.ell(64, 56, 27, 22) & (c.y < 62)
    c.paint(dome, c.hs(37, 91, 0.6, 0.55) + 0.15 * np.clip(1 - (c.y - 36) / 24, 0, 1), IRONN)
    c.solid(c.ell(52, 38, 5, 2.2), "#9ab4d6")
    c.solid(c.ell(48, 42, 2, 1.2), "#c8dcf4")
    # rope: three turns and the tail laid across the quay
    for cy in (84, 94, 104):
        _rope_band(c, 64, cy, 26, 7, 4, cy)
    tail = c.line([(88, 98), (104, 102), (114, 110), (104, 118), (86, 120)], 5)
    c.paint(tail, 0.5 + 0.3 * np.sin(c.x * 0.9 + c.y * 0.4), ROPE)
    c.solid(c.line([(88, 100), (104, 104)], 1), "#c4ae80")
    # the blue night rim on the right
    rim = body & (c.x > 78 - (c.y - 66) * 0.12) & (c.y > 70)
    c.solid(rim & (c.x % 2 == 0) & (c.y % 2 == 0), "#566a8a")
    c.outline()
    return c.out()


def thing_quay_lamp():
    """A dim blue-glass lantern on a cast-iron post, its small cold glow dithered round it."""
    c = Cv()
    c.paint(c.rect(42, 114, 86, 124), c.hs(42, 86, 0.5, 0.45), IRONN)
    c.paint(c.poly([(50, 114), (78, 114), (69, 96), (59, 96)]), c.hs(50, 78, 0.5, 0.5), IRONN)
    c.paint(c.rect(60, 50, 68, 98), c.hs(60, 68, 0.55, 0.55), IRONN)
    c.paint(c.rect(56, 92, 72, 96), 0.6, IRONN)
    c.paint(c.rect(57, 62, 71, 65), 0.65, IRONN)
    c.paint(c.line([(68, 74), (82, 68), (86, 74)], 2), 0.5, IRONN)
    # lantern: pyramid roof, tapering glass, cage bars
    c.paint(c.rect(50, 46, 78, 52), c.hs(50, 78, 0.5, 0.5), IRONN)
    glass = c.poly([(54, 46), (74, 46), (80, 20), (48, 20)])
    d = np.sqrt((c.x - 64) ** 2 + ((c.y - 33) * 1.2) ** 2)
    c.paint(glass, np.clip(1.05 - d / 24, 0, 1) ** 0.8, LGLASS, 0.9)
    c.paint(c.poly([(44, 20), (84, 20), (64, 4)]), c.hs(44, 84, 0.5, 0.55), IRONN)
    c.paint(c.rect(60, 0, 68, 6), 0.5, IRONN)
    c.paint(c.rect(44, 18, 84, 22), c.hs(44, 84, 0.55, 0.5), IRONN)
    for (x0, x1) in (((54, 48)), ((64, 64)), ((74, 80))):
        c.paint(c.line([(x0, 46), (x1, 20)], 1), 0.35, IRONN)
    c.outline()
    c.glow(64, 33, 44, "#aad4ff", "#1c3a70", 2.2, over=False)
    return c.out()


def thing_searchlight():
    """A searchlight on a lattice steel tower at a quay head: a big round lamp, its long wide white-blue beam thrown up and across."""
    c = Cv()
    # tower: four legs seen as two, cross braces
    for (x0, x1) in ((24, 44), (84, 66)):
        c.paint(c.line([(x0, 124), (x1, 66)], 5), 0.45 + 0.2 * (x0 < 50), IRONN)
    c.paint(c.line([(52, 124), (52, 66)], 3), 0.3, IRONN)
    for yy, xa, xb in ((112, 28, 80), (96, 31, 77), (80, 35, 73)):
        c.paint(c.rect(xa - 3, yy - 1, xb + 3, yy + 2), 0.5, IRONN)
    for (ya, yb, xa, xb, xc, xd) in ((112, 96, 28, 80, 31, 77), (96, 80, 31, 77, 35, 73)):
        c.paint(c.line([(xa, ya), (xd, yb)], 2), 0.4, IRONN)
        c.paint(c.line([(xb, ya), (xc, yb)], 2), 0.4, IRONN)
    c.paint(c.rect(26, 120, 82, 126), 0.55, IRONN)
    c.paint(c.rect(32, 62, 76, 69), c.vs(62, 69, 0.55, 0.6), IRONN)
    c.paint(c.rect(46, 56, 58, 64), 0.4, IRONN)
    # lamp drum, pointing up and to the right
    ang = np.deg2rad(-42)
    dv = np.array([np.cos(ang), np.sin(ang)])
    nv = np.array([-dv[1], dv[0]])
    cen = np.array([50.0, 46.0])
    L, R = 34.0, 15.0
    back, front = cen - dv * L / 2, cen + dv * L / 2
    drum = c.poly([back + nv * R, front + nv * R, front - nv * R, back - nv * R])
    lat = (c.x - cen[0]) * nv[0] + (c.y - cen[1]) * nv[1]
    c.paint(drum, 0.5 + 0.4 * (-lat / R) * -1 * -1 + 0.1, GREYB)
    c.paint(drum & (np.abs((c.x - back[0]) * dv[0] + (c.y - back[1]) * dv[1] - 8) < 1.3), 0.15, GREYB)
    c.paint(drum & (np.abs((c.x - back[0]) * dv[0] + (c.y - back[1]) * dv[1] - 22) < 1.3), 0.15, GREYB)
    # the lens: an ellipse face-on to the beam
    lens = c.poly([front + nv * R * np.cos(t) + dv * 5 * np.sin(t) for t in np.linspace(0, 2 * np.pi, 40)])
    rim = c.poly([front + nv * (R + 2) * np.cos(t) + dv * 6.4 * np.sin(t) for t in np.linspace(0, 2 * np.pi, 40)])
    c.paint(rim, 0.55, GREYB)
    c.solid(lens, "#f4fbff")
    c.solid(lens & (c.x < front[0] - 4), "#cfe6ff")
    # a pale halo ring round the lamp and the beam: dither pixels only where the sprite is still empty
    c.outline()
    bd = (c.x - front[0]) * dv[0] + (c.y - front[1]) * dv[1]
    bl = (c.x - front[0]) * nv[0] + (c.y - front[1]) * nv[1]
    half = 9 + np.clip(bd, 0, None) * 0.3
    inside = (bd > 3) & (np.abs(bl) < half) & (c.a == 0)
    s = np.clip(1 - np.abs(bl) / half, 0, 1) ** 0.7 * np.clip(1 - bd / 150.0, 0, 1) ** 0.6
    m = inside & (s * 1.05 > c.b)
    col = (col3("#6a9ad8") * (1 - np.clip(s * 1.3, 0, 1)[..., None]) + col3("#f4fbff") * np.clip(s * 1.3, 0, 1)[..., None]).astype(np.uint8)
    c.rgb[m] = col[m]
    c.a[m] = 255
    c.glow(front[0], front[1], 22, "#ffffff", "#5a8ad0", 1.6)
    return c.out()


def thing_beam():
    """A soft wide white-blue searchlight beam as a tall cone, additive-looking: a glowing core, faint rays, a few dust motes; transparent elsewhere."""
    h = w = 128
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    t = (h - 1 - y) / (h - 1)  # 0 at the foot, 1 at the top
    half = 7 + t * 52
    s = (x - 63.5) / half
    prof = np.exp(-(s * s) * 2.4)
    rays = 0.88 + 0.12 * np.sin(s * 9 + 1.0) + 0.06 * np.sin(s * 23)
    vert = (1 - t ** 1.7 * 0.78) * np.clip((h - 1 - y) / 6.0 + 0.2, 0, 1)
    nz = fnoise((h, w), 5, 811, 2)
    a = prof * rays * vert * (0.9 + 0.2 * nz)
    a = np.clip(a * 0.78, 0, 1)
    mote = (speckle(128, 0.012, 812) > 0) & (np.abs(s) < 0.9)
    a = np.where(mote, np.clip(a + 0.35, 0, 1), a)
    rgb = np.zeros((h, w, 3), np.float32)
    core = np.clip(prof ** 3, 0, 1)[..., None]
    rgb[:] = np.array([170, 205, 255], np.float32) * (1 - core) + np.array([255, 255, 255], np.float32) * core
    alpha = (a * 255).astype(np.uint8)
    alpha[a < 0.03] = 0
    return np.dstack([rgb.astype(np.uint8), alpha])


def thing_cell_door():
    """A heavy iron-banded cell door in a stone arch: a small grille with a guard's lantern glow behind it, a big lock."""
    c = Cv()
    arch = c.rect(10, 34, 118, 126) | c.ell(64, 36, 54, 32)
    c.paint(arch, 0.4 + 0.2 * (c.x < 64) + (fnoise((128, 128), 5, 821) - 0.5) * 0.25, STONEB)
    joints = ((c.y % 16) < 1) | (((c.x + (c.y // 16) * 17) % 34) < 1)
    c.paint(arch & joints, 0.12, STONEB)
    door = c.rect(24, 36, 104, 126) | (c.ell(64, 40, 40, 22) & (c.y < 40))
    pl = np.floor((c.x - 24) / 10.0)
    tone = _rs(822).rand(10)[np.clip(pl, 0, 9).astype(int)]
    grain = np.sin(c.y * 0.35 + pl * 3.0 + fnoise((128, 128), 8, 823) * 6) * 0.07
    c.paint(door, 0.34 + 0.22 * tone + grain + 0.15 * (c.x < 52) - 0.12 * ((c.x - 24) % 10 < 1), WOODN)
    c.paint(door & ((c.x - 24) % 10 < 1), 0.05, WOODN)
    # iron bands, rivets, hinge knuckles
    for y0, y1 in ((62, 70), (104, 112)):
        band = c.rect(24, y0, 104, y1)
        c.paint(band, c.vs(y0, y1, 0.55, 0.6), IRONN)
        for rx in range(30, 102, 12):
            c.solid(c.ell(rx, (y0 + y1) / 2, 1.6, 1.6), "#7890b4")
    for yy in (66, 108):
        c.paint(c.ell(26, yy, 4, 6), 0.7, IRONN)
    c.paint(c.rect(94, 36, 104, 126), c.hs(94, 104, 0.5, 0.5), IRONN)
    # the grille and the lantern glow behind it
    c.paint(c.rect(46, 22, 82, 52), 0.3, IRONN)
    c.solid(c.rect(50, 26, 78, 48), "#6a3a08")
    g = np.clip(1 - np.sqrt(((c.x - 64) / 15.0) ** 2 + ((c.y - 38) / 12.0) ** 2), 0, 1)
    c.paint(c.rect(50, 26, 78, 48), 0.25 + 0.9 * g, GOLDL)
    for bx in (57, 64, 71):
        c.solid(c.rect(bx - 1, 24, bx + 1, 50), "#0c1018")
        c.solid(c.rect(bx - 1, 24, bx, 50), "#2e3a4e")
    c.solid(c.rect(48, 36, 80, 38), "#0c1018")
    # a big box lock: hasp, plate, shackle, keyhole
    c.paint(c.rect(62, 78, 100, 84), c.vs(78, 84, 0.55, 0.6), IRONN)
    c.paint(c.ring(82, 84, 9, 10, 3), 0.6, IRONN)
    lock = c.rect(70, 84, 94, 104)
    c.paint(lock, c.hs(70, 94, 0.55, 0.5), IRONN)
    c.solid(c.ell(82, 91, 3.3, 3.3), "#02040a")
    c.solid(c.rect(81, 92, 83, 99), "#02040a")
    c.solid(c.rect(71, 85, 73, 103), "#7890b4")
    c.outline()
    c.glow(64, 38, 40, "#ffcf60", "#6a3a10", 2.4, over=False)
    # amber spill over the stone and wood around the grille
    sp = np.clip(1 - np.sqrt((c.x - 64) ** 2 + ((c.y - 38) * 1.2) ** 2) / 34.0, 0, 1) ** 1.5 * 0.9
    c.tint_light(door | arch, sp, "#ffb440")
    return c.out()


def thing_bunk():
    """A plank bunk against a scratched stone wall: a grey blanket and pillow on the lower bed, a tin cup on the upper plank."""
    c = Cv()
    wall = c.rect(2, 4, 126, 126)
    sh, mort = bricks(128, rows=8, cols=4, mortar=1, seed=831, wear=0.5)
    c.paint(wall, 0.2 + sh * 0.4 + (fnoise((128, 128), 6, 832) - 0.5) * 0.1, STONEB)
    c.paint(wall & (mort > 0.5), 0.3, MORT)
    rng = _rs(833)
    for gx, gy in ((78, 12), (96, 22)):
        for k in range(4):
            x0 = gx + k * 3
            c.solid(c.line([(x0, gy), (x0 + 0.6, gy + 10)], 1), "#6a7e9c")
        c.solid(c.line([(gx - 2, gy + 9), (gx + 12, gy + 1)], 1), "#6a7e9c")
    # posts, upper plank and the bed's frame
    for px in (10, 110):
        c.paint(c.rect(px, 38, px + 9, 126), c.hs(px, px + 9, 0.5, 0.6) + (fnoise((128, 128), 3, 834) - 0.5) * 0.2, WOODN)
        c.paint(c.rect(px - 2, 122, px + 11, 126), 0.5, WOODN)
    up = c.rect(10, 54, 120, 63)
    c.paint(up, c.vs(54, 63, 0.55, 0.7) + np.sin(c.x * 0.5) * 0.04, WOODN)
    c.paint(c.rect(10, 62, 120, 65), 0.15, WOODN)
    c.paint(c.rect(10, 94, 120, 103), c.vs(94, 103, 0.6, 0.7), WOODN)
    c.paint(c.rect(10, 102, 120, 106), 0.15, WOODN)
    c.paint(c.rect(10, 94, 120, 95), 0.9, WOODN)
    for jx in (46, 88):
        c.solid(c.rect(jx, 94, jx + 1, 103), "#0a0705")
    # a thin straw mattress on the upper plank, a tin cup on it
    c.paint(c.rect(18, 48, 100, 54) & (c.y > 48 + 1.5 * np.sin(c.x * 0.3)), 0.4 + 0.4 * fnoise((128, 128), 2, 835), STRAW)
    cup = c.poly([(97, 33), (111, 33), (109, 48), (99, 48)])
    c.paint(cup, c.hs(97, 111, 0.55, 0.6), GREYB)
    c.paint(c.ell(104, 33, 7, 2), 0.2, GREYB)
    c.solid(c.line([(111, 36), (116, 38), (116, 43), (109, 45)], 2), "#566068")
    c.solid(c.line([(98, 36), (99, 46)], 1), "#cfe0f0")
    # grey blanket humped over a body-length lump with fold lines, a pillow at the head
    topy = 80 - 7 * np.clip(np.sin(np.clip((c.x - 24) / 74.0, 0, 1) * np.pi), 0, 1) ** 1.3 + 2.5 * np.sin(c.x * 0.22)
    blanket = (c.x >= 22) & (c.x < 100) & (c.y > topy) & (c.y < 96)
    folds = np.sin(c.x * 0.4 + c.y * 0.15) * 0.1 + (fnoise((128, 128), 4, 836) - 0.5) * 0.2
    c.paint(blanket, 0.58 + 0.35 * np.clip(1 - (c.y - topy) / 14, 0, 1) + folds + 0.1 * (c.x < 50), GREYB)
    c.solid(blanket & (c.y > 90), "#0c0e12")
    stripe = blanket & (np.abs(c.y - (topy + 7)) < 1.1)
    c.solid(stripe, "#2a3038")
    pillow = c.ell(32, 86, 13, 8) & (c.y < 96)
    c.paint(pillow, 0.55 + 0.4 * np.clip(1 - (c.y - 78) / 14, 0, 1) - 0.12 * (c.x > 36), GREYB)
    c.paint(c.ell(32, 85, 9, 4) & (c.y < 86), 0.9, GREYB)
    c.outline()
    return c.out()


def thing_window_latch():
    """A small barred cell window high in a stone wall, a rusty iron latch on its frame, a thin shaft of cold moonlight slanting down."""
    c = Cv()
    wall = c.rect(2, 2, 126, 126)
    sh, mort = bricks(128, rows=8, cols=3, mortar=1, seed=841, wear=0.6)
    c.paint(wall, 0.2 + sh * 0.42 + (fnoise((128, 128), 6, 842) - 0.5) * 0.12, STONEB)
    c.paint(wall & (mort > 0.5), 0.3, MORT)
    # the reveal, the recess with a night sky, the sill
    rev = c.rect(40, 20, 90, 80) | (c.ell(65, 22, 25, 14) & (c.y < 22))
    c.paint(rev, c.hs(40, 90, 0.3, 0.3), STONEB)
    rec = c.rect(48, 28, 82, 74) | (c.ell(65, 28, 17, 10) & (c.y < 28))
    skyg = 0.25 + 0.5 * np.clip((c.y - 18) / 56.0, 0, 1)
    c.paint(rec, skyg, NIGHT)
    c.solid(rec & (speckle(128, 0.012, 843) > 0), "#cfe2ff")
    c.paint(c.rect(36, 80, 94, 86), c.vs(80, 86, 0.6, 0.7), STONEB)
    c.paint(c.rect(36, 84, 94, 87), 0.1, STONEB)
    # iron bars and a cross bar
    for bx in (54, 65, 76):
        c.paint(c.rect(bx - 1.5, 18, bx + 1.5, 76), c.hs(bx - 1.5, bx + 1.5, 0.5, 0.8), IRONN)
    c.paint(c.rect(46, 44, 84, 47), c.vs(44, 47, 0.5, 0.8), IRONN)
    # the latch: a rusted plate on the right of the frame, a pivoting bar with a hook and bolts
    c.paint(c.rect(86, 38, 96, 58), c.hs(86, 96, 0.4, 0.5) + (fnoise((128, 128), 3, 844) - 0.5) * 0.3, RUSTR)
    c.paint(c.rect(72, 45, 98, 49), c.vs(45, 49, 0.4, 0.7), RUSTR)
    c.paint(c.poly([(96, 45), (101, 45), (101, 56), (96, 56)]), 0.45, RUSTR)
    c.paint(c.ring(70, 47, 6, 6, 2), 0.6, RUSTR)
    for bx, by in ((89, 41), (93, 41), (89, 55), (93, 55)):
        c.solid(c.ell(bx, by, 1.6, 1.6), "#c0622a")
    c.solid(c.rect(90, 49, 91, 62), "#3e1608")
    c.paint(wall & (grime(128, 845, 0.8, True) > 0.55), 0.1, STONEB)
    c.outline()
    # the moon shaft: from the opening down and to the left across the wall
    p1 = np.array([48.0, 76.0])
    shaft = c.poly([(48, 80), (84, 80), (62, 126), (6, 126)])
    u = np.clip((c.y - 80) / 46.0, 0, 1)
    lat = np.clip(1 - np.abs((c.x - (66 - u * 30)) / (22 - 6 * u)), 0, 1)
    c.tint_light(shaft, lat * (0.95 - 0.5 * u), "#cfe4ff")
    c.glow(65, 46, 30, "#9ec4f0", "#1c3a70", 2.4, over=False)
    return c.out()


def thing_fishing_boat():
    """A small wooden fishing boat low in black water: stubby mast with a swinging lantern giving one warm gold glow, nets heaped on the bow, a tarpaulin aft, lapping ripples."""
    c = Cv(128, 256)
    H, W = 128, 256
    # hull
    sheer = lambda x: 62 + 18 * (1 - np.cos(np.clip((x - 30) / 100.0, 0, 1.6) * np.pi * 0.5)) * 0.9 - np.clip((x - 170) / 60.0, 0, 1) * 8
    gun = [(x, sheer(x)) for x in range(30, 232, 10)]
    hull = c.poly(gun + [(230, 96), (160, 101), (80, 100), (46, 94)])
    yy = c.y - np.array([sheer(x) for x in range(W)])[None, :]
    stk = (yy % 8) < 1.0
    c.paint(hull, 0.36 + 0.14 * np.sin(c.x * 0.18) + (fnoise((H, W), 4, 851) - 0.5) * 0.18 - 0.2 * stk + 0.08 * (yy < 4) + 0.12 * ((yy % 8) > 6), WOODN)
    c.solid(hull & (np.abs(yy - 12) < 1.5) & (c.x > 40) & (c.x < 222), "#27405e")
    rail = hull & (yy < 3.5)
    c.paint(rail, 0.7 + (fnoise((H, W), 3, 852) - 0.5) * 0.2, WOODN)
    # nets heaped on the bow, with cork floats
    heap = c.ell(84, 70, 31, 15) & (c.y < sheer(84) + 3)
    mesh = (((c.x + c.y) % 6) < 1.3) | (((c.x - c.y) % 6) < 1.3)
    c.paint(heap, 0.18 + 0.25 * fnoise((H, W), 5, 853, 2) + 0.4 * mesh * (c.y < 72) + 0.1 * (c.x < 80), NETN)
    c.paint(heap & mesh, 0.55 + 0.3 * (c.y < 62), NETN)
    for fx, fy in ((64, 66), (78, 60), (96, 62), (108, 70), (70, 74), (90, 72)):
        c.paint(c.ell(fx, fy, 3.4, 3.0), c.hs(fx - 3.4, fx + 3.4, 0.6, 0.7), STRAW)
    # tarpaulin humped over the stern
    tarp = c.poly([(166, 78), (172, 64), (186, 54), (206, 52), (222, 62), (230, 74), (228, 80), (166, 82)])
    c.paint(tarp, 0.3 + 0.4 * np.clip(1 - (c.y - 52) / 24, 0, 1) + 0.12 * np.sin(c.x * 0.45 + c.y * 0.1) + 0.1 * (c.x < 190), TARP)
    c.solid(tarp & (np.abs(((c.x - 190) * 0.18 + c.y * 0.3) % 6) < 0.6) & (c.y > 56), "#08101a")
    for lx in (186, 210):
        c.paint(c.line([(lx, 54), (lx + 6, 80)], 2), 0.5, ROPE)
    # mast, boom with a furled sail, stays
    c.paint(c.poly([(121, 14), (127, 14), (129, 82), (119, 82)]), c.hs(119, 129, 0.5, 0.7), WOODN)
    c.paint(c.line([(122, 44), (176, 38)], 3), 0.55, WOODN)
    furl = c.line([(124, 48), (170, 41)], 7)
    c.paint(furl, 0.4 + 0.3 * np.sin(c.x * 0.7), TARP)
    c.solid(c.line([(124, 15), (30, 62)], 1), "#0c1018")
    c.solid(c.line([(124, 15), (230, 70)], 1), "#0c1018")
    c.paint(c.line([(124, 26), (150, 26)], 2), 0.5, WOODN)
    c.paint(c.rect(120, 12, 128, 16), 0.8, WOODN)
    # the lantern
    lx, ly = 151, 28
    c.solid(c.line([(lx, 27), (lx + 1, 35)], 1), "#0c1018")
    lan = c.rect(lx - 5, 35, lx + 6, 49)
    c.paint(lan, 0.3 + 0.8 * np.clip(1 - np.sqrt(((c.x - lx) / 7.0) ** 2 + ((c.y - 43) / 8.0) ** 2), 0, 1), GOLDL)
    c.solid(c.rect(lx - 6, 33, lx + 7, 36), "#1a2230")
    c.solid(c.rect(lx - 6, 48, lx + 7, 51), "#1a2230")
    c.solid(c.rect(lx, 36, lx + 1, 48), "#2a1604")
    c.paint(c.poly([(lx - 6, 33), (lx + 7, 33), (lx + 1, 29)]), 0.5, IRONN)
    # black water in front, lapping ripples
    ytop = 93 + 1.6 * np.sin(c.x * 0.16) + 1.2 * np.sin(c.x * 0.41)
    water = c.ell(128, 100, 124, 28) & (c.y > ytop)
    c.paint(water, 0.12 + 0.18 * fnoise((H, W), 8, 854, 2) * (c.y - 93) / 30.0, ramp("#010206", "#040910", "#08121e", "#0e1e30", "#18304a"))
    rip = water & (((c.y + np.floor(c.x / 18) * 2) % 5) < 1) & (fnoise((H, W), 7, 855, 2) > 0.45)
    c.solid(rip, "#1e3a58")
    rip2 = water & (((c.y + 2 + np.floor(c.x / 14) * 3) % 7) < 1) & (fnoise((H, W), 9, 856, 2) > 0.58)
    c.solid(rip2, "#32608a")
    c.solid(water & (np.abs(c.y - ytop) < 1.0) & (fnoise((H, W), 4, 857, 2) > 0.45), "#2e5278")
    # gold reflection of the lantern
    refl = water & (np.abs(c.x - 151) < 3 + (c.y - 94) * 0.5) & (((c.y - 94) % 4) < 1.5) & (fnoise((H, W), 3, 858, 2) > 0.3)
    c.solid(refl, "#c8902a")
    c.solid(refl & (np.abs(c.x - 151) < 2 + (c.y - 94) * 0.2), "#ffd868")
    c.outline()
    c.glow(lx, 43, 46, "#fff0a0", "#7a4a10", 2.0, over=False)
    sp = np.clip(1 - np.sqrt((c.x - lx) ** 2 + (c.y - 43) ** 2) / 40.0, 0, 1) ** 1.4 * 0.95
    c.tint_light(hull | heap | tarp, sp, "#ffbe50")
    return c.out()


def thing_nets():
    """Fishing nets hung to dry on a rack of two posts, hung with cork floats, a heap of net on the ground."""
    c = Cv()
    for px in (8, 112):
        c.paint(c.rect(px, 16, px + 9, 126), c.hs(px, px + 9, 0.5, 0.6) + (fnoise((128, 128), 3, 861) - 0.5) * 0.2, WOODN)
        c.paint(c.rect(px - 2, 122, px + 11, 126), 0.5, WOODN)
    c.paint(c.rect(6, 22, 122, 30), c.vs(22, 30, 0.6, 0.7), WOODN)
    # the hanging net: diamond mesh with ragged scalloped hem
    hem = 88 + 10 * np.abs(np.sin(c.x * 0.09 + 0.5)) + 4 * np.sin(c.x * 0.31)
    hang = (c.x > 18) & (c.x < 110) & (c.y >= 30) & (c.y < hem)
    mesh = (((c.x + c.y) % 8) < 2) | (((c.x - c.y) % 8) < 2)
    fold = fnoise((128, 128), 10, 862, 3)
    c.paint(hang & mesh, 0.35 + 0.6 * fold + 0.15 * (c.x < 60) - 0.2 * (c.y > 80), NETN)
    knots = hang & ((((c.x + c.y) % 8) < 2) & (((c.x - c.y) % 8) < 2))
    c.solid(knots, "#5e7c68")
    # cork floats along the headline
    for fx in range(26, 108, 11):
        c.paint(c.ell(fx, 36, 4.0, 5.0), c.hs(fx - 4, fx + 4, 0.6, 0.8), STRAW)
        c.solid(c.rect(fx - 4, 35, fx + 4, 36), "#4a3a14")
    # a heap of net on the ground
    heap = c.ell(64, 116, 52, 14) & (c.y > 98)
    c.paint(heap, 0.16 + 0.2 * fnoise((128, 128), 4, 863) + 0.1 * (c.x < 60), NETN)
    c.paint(heap & mesh, 0.4 + 0.45 * fnoise((128, 128), 5, 864) + 0.1 * (c.x < 60), NETN)
    for fx, fy in ((34, 108), (86, 110), (106, 114), (52, 118)):
        c.paint(c.ell(fx, fy, 3.6, 3.2), c.hs(fx - 3.6, fx + 3.6, 0.6, 0.8), STRAW)
    c.outline()
    return c.out()


# ============================================================================================================================================
# BILLBOARDS: the briefing hut again (khaki, dust, white glare, warm bulbs)
# ============================================================================================================================================
REDP = ramp("#3a0606", "#6a0e0e", "#a01818", "#d02c2c", "#f05a4a")
PAPER = ramp("#7c7258", "#aaa088", "#d0c8aa", "#eee8d0", "#fffaf0")
OLIVE = ramp("#1c2014", "#2c3220", "#444c2e", "#5e6a3e", "#808c54", "#a4b072")
DUST = ramp("#8a7448", "#b09a62", "#d0ba80", "#e8d8a4", "#fff2cc")
TIN = ramp("#2c3036", "#4a5058", "#6e747c", "#9aa0a6", "#c8ccd0")


def _digit(c: Cv, d: str, x0, y0, w, h, t):
    """A painted digit as a mask: strokes of width t."""
    if d == "4":
        pts = [[(x0 + w * 0.72, y0), (x0 + 1, y0 + h * 0.64), (x0 + w, y0 + h * 0.64)], [(x0 + w * 0.72, y0 + 2), (x0 + w * 0.72, y0 + h)]]
    elif d == "7":
        pts = [[(x0, y0 + t * 0.5), (x0 + w, y0 + t * 0.5), (x0 + w * 0.34, y0 + h)]]
    elif d == "6":
        pts = [[(x0 + w, y0 + t * 0.4), (x0 + t * 0.4, y0 + t * 0.4), (x0 + t * 0.4, y0 + h - t * 0.4), (x0 + w - t * 0.4, y0 + h - t * 0.4), (x0 + w - t * 0.4, y0 + h * 0.5), (x0 + t * 0.4, y0 + h * 0.5)]]
    else:
        pts = [[(x0, y0), (x0 + w, y0 + h)]]
    m = np.zeros((c.h, c.w), bool)
    for p in pts:
        m |= c.line(p, int(t))
    return m


def thing_count_board():
    """The mission count: a big plank board on two posts with an enormous painted number in white, the last digit still wet and dripping, an old crossed-out number below, a paint pot and brush on a ledge."""
    c = Cv()
    for px in (16, 100):
        c.paint(c.rect(px, 98, px + 11, 126), c.hs(px, px + 11, 0.5, 0.6) + (fnoise((128, 128), 3, 901) - 0.5) * 0.2, KHAKI)
    board = c.rect(4, 4, 124, 100)
    pl = np.floor((c.x - 4) / 20.0)
    tone = _rs(902).rand(7)[np.clip(pl, 0, 6).astype(int)]
    grain = np.sin(c.y * 0.3 + pl * 2.0 + fnoise((128, 128), 9, 903) * 5) * 0.06
    c.paint(board, 0.3 + 0.2 * tone + grain + 0.1 * (c.y < 40) - 0.1 * (c.y > 70) + (fnoise((128, 128), 3, 904) - 0.5) * 0.12, KHAKI)
    c.paint(board & ((c.x - 4) % 20 < 1), 0.04, KHAKI)
    c.paint(c.rect(4, 4, 124, 8) | c.rect(4, 96, 124, 100), 0.18, KHAKI)
    for nx in (12, 112):
        for ny in (12, 90):
            c.solid(c.ell(nx, ny, 1.6, 1.6), "#241c0e")
    # the old number, faded and struck through
    old = _digit(c, "4", 12, 78, 11, 16, 3) | _digit(c, "6", 28, 78, 11, 16, 3)
    c.paint(old, 0.6 + 0.25 * fnoise((128, 128), 2, 905), PAPER)
    strike = c.line([(8, 96), (44, 78)], 3) | c.line([(8, 78), (44, 96)], 2)
    c.paint(strike & board, 0.45, REDP)
    # the new number: the 4 dry and chipped, the 7 fresh and wet
    four = _digit(c, "4", 12, 10, 44, 56, 12)
    seven = _digit(c, "7", 66, 10, 46, 56, 12)
    chips = (fnoise((128, 128), 3, 906, 2) > 0.68)
    c.paint(four & ~chips, 0.62 + 0.22 * fnoise((128, 128), 3, 907, 2) + 0.12 * (c.x < 36), PAPER)
    c.paint(four & chips, 0.3, KHAKI)
    c.paint(seven, 0.9 + 0.1 * (c.y < 24) - 0.12 * (c.x > 100), PAPER)
    c.solid(seven & (np.abs(c.x - 74) < 1.2) & (c.y > 14) & (c.y < 30), "#ffffff")
    for dx, yb, ln in ((78, 62, 20), (85, 62, 9), (104, 20, 14), (94, 20, 7)):
        c.solid(c.rect(dx, yb, dx + 3, yb + ln), "#f4f0e0")
        c.solid(c.ell(dx + 1.5, yb + ln + 1.5, 2.4, 3.2), "#ffffff")
    # ledge, paint pot and brush
    c.paint(c.rect(4, 100, 124, 108), c.vs(100, 108, 0.55, 0.7), KHAKI)
    c.paint(c.rect(4, 107, 124, 110), 0.15, KHAKI)
    pot = c.rect(90, 90, 114, 101)
    c.paint(pot, c.hs(90, 114, 0.55, 0.6), TIN)
    c.solid(c.ell(102, 90, 12, 3.2), "#fffaf0")
    c.solid(c.rect(94, 92, 96, 101) & (c.y < 98), "#f4f0e0")
    c.paint(c.line([(106, 91), (118, 74)], 3), 0.5, KHAKI)
    c.solid(c.line([(105, 91), (109, 85)], 4), "#fffaf0")
    c.paint(c.line([(50, 98), (76, 95)], 4), 0.5, KHAKI)
    c.solid(c.line([(76, 95), (84, 94)], 5), "#fffaf0")
    c.outline()
    return c.out()


def thing_radio_broken():
    """A smashed military radio set on a crate: dented grey case, a dangling headset cable, one valve still glowing orange, a few sparks."""
    c = Cv()
    crate = c.rect(12, 86, 114, 126)
    c.paint(crate, 0.35 + 0.25 * ((np.floor((c.y - 86) / 10) % 2) * 0.5) + 0.12 * (c.x < 40) + (fnoise((128, 128), 4, 911) - 0.5) * 0.2, KHAKI)
    c.paint(crate & (((c.y - 86) % 10) < 1), 0.05, KHAKI)
    c.paint(c.rect(12, 86, 20, 126) | c.rect(106, 86, 114, 126), c.hs(12, 20, 0.45, 0.4) - 0.1, KHAKI)
    c.solid(c.ell(16, 94, 1.5, 1.5), "#241c0e")
    c.solid(c.ell(110, 118, 1.5, 1.5), "#241c0e")
    case = c.rect(24, 40, 104, 87)
    c.paint(case, 0.5 + 0.3 * np.clip(1 - (c.x - 24) / 80, 0, 1) - 0.12 * (c.y > 78), GREYB)
    c.paint(c.rect(24, 40, 104, 44), 0.8, GREYB)
    panel = c.rect(30, 48, 98, 80)
    c.paint(panel, 0.22 + 0.1 * c.vs(48, 80, 0.4, 0.4), GREYB)
    # dial with a cracked glass, knobs and a dented corner
    c.paint(c.ell(50, 64, 14, 14), 0.3, GREYB)
    c.paint(c.ell(50, 64, 11, 11), 0.85 - 0.3 * ((c.x - 50) + (c.y - 64) > 6), PAPER)
    c.solid(c.line([(41, 56), (50, 64), (58, 74)], 1), "#202428")
    c.solid(c.line([(50, 64), (55, 53)], 1), "#202428")
    c.solid(c.line([(50, 64), (60, 62)], 1), "#202428")
    c.solid(c.line([(50, 64), (50, 54)], 1), "#b01818")
    for kx, ky in ((78, 58), (90, 58), (78, 72), (90, 72)):
        c.paint(c.ell(kx, ky, 5, 5), c.hs(kx - 5, kx + 5, 0.55, 0.7), TIN)
        c.solid(c.line([(kx, ky), (kx + 2, ky - 3)], 1), "#1a1e22")
    dent = c.poly([(24, 40), (52, 40), (40, 52), (24, 60)])
    c.paint(dent & case, 0.12, GREYB)
    c.solid(c.line([(24, 60), (40, 52), (52, 40)], 1), "#9aa0a6")
    c.paint(c.poly([(88, 84), (104, 74), (104, 87), (92, 87)]), 0.1, GREYB)
    for sx, sy in ((26, 80), (100, 42)):
        c.solid(c.ell(sx, sy, 1.5, 1.5), "#c8ccd0")
    # the valve on top still glowing
    c.paint(c.rect(80, 34, 92, 41), 0.4, GREYB)
    c.paint(c.ell(86, 26, 6, 11) & (c.y < 36), 0.2 + 0.9 * np.clip(1 - np.sqrt(((c.x - 86) / 6.0) ** 2 + ((c.y - 28) / 9.0) ** 2), 0, 1), ramp("#5a1a04", "#c85a10", "#ff9a20", "#ffd060", "#fff4c0"))
    c.solid(c.line([(86, 20), (86, 34)], 1), "#fff4c0")
    # the headset cable dangling from the case, the earphone at its end
    cab = c.line([(24, 70), (12, 76), (7, 92), (12, 106), (22, 112), (28, 120)], 2)
    c.paint(cab, 0.4, GREYB)
    c.solid(cab & (c.x % 3 == 0), "#566068")
    c.paint(c.ell(30, 122, 6, 4), 0.35, GREYB)
    c.solid(c.ell(29, 121, 3, 2), "#6e747c")
    c.outline()
    c.glow(86, 28, 24, "#ffc040", "#7a2a06", 2.2, over=False)
    for sx, sy in ((100, 30), (106, 24), (72, 22), (96, 14), (68, 34)):
        c.solid(c.rect(sx, sy, sx + 2, sy + 2), "#ffe890")
    c.solid(c.line([(94, 36), (104, 28)], 1), "#ffd060")
    c.solid(c.line([(78, 30), (68, 24)], 1), "#ffd060")
    return c.out()


def thing_order_paper():
    """A table with a single sheet of paper bearing a huge red stamp bar over ruled wavy lines (no text), an ink pad and a lamp with a warm bulb."""
    c = Cv()
    top = c.poly([(24, 58), (104, 58), (124, 100), (4, 100)])
    c.paint(top, 0.45 + 0.3 * np.clip((c.y - 58) / 42, 0, 1) * 0.5 + 0.08 * np.sin(c.y * 0.9 + c.x * 0.05) + (fnoise((128, 128), 4, 921) - 0.5) * 0.15, WOODB)
    c.paint(c.rect(4, 100, 124, 110), c.vs(100, 110, 0.6, 0.8), WOODB)
    c.paint(c.rect(4, 109, 124, 112), 0.15, WOODB)
    for lx in (10, 108):
        c.paint(c.rect(lx, 112, lx + 10, 126), c.hs(lx, lx + 10, 0.45, 0.6), WOODB)
    # the sheet, a trapezoid on the table
    def edge(y, side):
        t = (y - 62) / 36.0
        return (36 - 10 * t) if side == 0 else (90 + 10 * t)
    paper = c.poly([(36, 62), (90, 62), (100, 98), (26, 98)])
    c.paint(paper, 0.8 + 0.12 * (c.x < 62) - 0.1 * (c.y > 90) + (fnoise((128, 128), 3, 922) - 0.5) * 0.1, PAPER)
    # the huge red stamp bar and its smudge
    bar = c.poly([(34, 66), (92, 66), (95, 76), (31, 76)])
    c.paint(bar & paper, 0.55 + 0.35 * fnoise((128, 128), 2, 923, 2) + 0.1 * (c.x < 60), REDP)
    c.paint(c.poly([(60, 76), (66, 76), (64, 80), (58, 80)]) & paper, 0.4, REDP)
    # ruled body of wavy lines
    for k in range(5):
        yy = 82 + k * 3.4
        pts = []
        for xx in np.linspace(edge(yy, 0) + 3, edge(yy, 1) - 3, 14):
            pts.append((xx, yy + 0.9 * np.sin(xx * 0.7 + k * 1.3)))
        if k == 4:
            pts = pts[:8]
        c.solid(c.line(pts, 1) & paper, "#6a6458")
    # ink pad
    pad = c.poly([(96, 66), (116, 66), (122, 80), (96, 80)])
    c.paint(pad, 0.25, GREYB)
    c.paint(c.poly([(99, 68), (114, 68), (118, 77), (99, 77)]), 0.5 + 0.3 * (c.x < 108), REDP)
    # lamp: a base, a pole, an arm and a conical shade over the paper with a warm bulb
    c.paint(c.ell(14, 80, 11, 4), 0.5, IRONN)
    c.paint(c.rect(11, 38, 15, 80), c.hs(11, 15, 0.55, 0.6), IRONN)
    c.paint(c.line([(13, 40), (30, 26)], 3), 0.5, IRONN)
    shade = c.poly([(22, 18), (50, 18), (60, 36), (14, 34)])
    c.paint(shade, c.hs(14, 60, 0.45, 0.6), ramp("#14201a", "#243c30", "#3a5e48", "#5a8a68", "#88b890"))
    c.solid(c.rect(22, 16, 50, 19), "#14201a")
    bulb = c.ell(37, 37, 6, 4.5)
    c.solid(bulb, "#fff0b0")
    c.solid(c.ell(37, 37, 3, 2.4), "#ffffff")
    c.outline()
    c.glow(37, 38, 40, "#ffe8a0", "#8a5a14", 1.9, over=False, squash=0.9)
    sp = np.clip(1 - np.sqrt((c.x - 40) ** 2 + ((c.y - 44) * 1.4) ** 2) / 54.0, 0, 1) ** 1.2 * 0.9
    c.tint_light(top | paper, sp, "#ffd890")
    return c.out()


def thing_aircraft_door():
    """The hut's open east door framing the bomber that waits outside, engines turning: a white sun glare, dust, a doorway of dusty planks."""
    c = Cv()
    frame = c.rect(2, 2, 126, 126)
    pl = np.floor((c.x - 2) / 8.0)
    tone = _rs(931).rand(16)[np.clip(pl, 0, 15).astype(int)]
    c.paint(frame, 0.3 + 0.2 * tone + (fnoise((128, 128), 4, 932) - 0.5) * 0.15 + 0.06 * (c.y < 20), KHAKI)
    c.paint(frame & ((c.x - 2) % 8 < 1), 0.05, KHAKI)
    op = c.rect(16, 14, 112, 120)
    # outside: glare sky, hazy ground
    g = np.clip(1 - np.sqrt(((c.x - 92) / 60.0) ** 2 + ((c.y - 28) / 40.0) ** 2), 0, 1)
    skyg = 0.62 + 0.38 * g + 0.1 * np.clip((c.y - 14) / 80, 0, 1) * 0
    sky = ramp("#9ec8e8", "#cde4f2", "#e8f2f6", "#fbfbf0", "#ffffff")
    c.paint(op, skyg, sky)
    gy = 86 + 1.5 * np.sin(c.x * 0.3)
    ground = op & (c.y > gy)
    c.paint(ground, 0.35 + 0.5 * np.clip((c.y - gy) / 30, 0, 1) + 0.15 * fnoise((128, 128), 5, 933, 2), DUST)
    c.paint(op & (c.y > gy - 6) & (c.y <= gy), 0.88 - 0.4 * (gy - c.y) / 6 * 0 , ramp("#e8dcb0", "#f6efd0", "#fffaf0"))
    # the bomber nose on: tail fin behind, a wide wing, four engines with spinning discs, glazed nose
    c.paint(c.poly([(64, 34), (60, 62), (68, 62)]), 0.5, OLIVE)
    c.paint(c.rect(50, 55, 78, 59), 0.45, OLIVE)
    wing = c.poly([(18, 65), (64, 60), (110, 65), (110, 75), (64, 73), (18, 75)])
    for ex in (30, 98, 48, 80):
        c.paint(c.line([(ex, 72), (ex, 98)], 3), 0.4, OLIVE)
        c.paint(c.ell(ex, 100, 6, 4), 0.2, IRONN)
        disc = c.ell(ex, 69, 12, 12)
        c.paint(disc & (c.x % 2 == 0) & (c.y % 2 == 0), 0.3, OLIVE)
        c.paint(disc & ~c.ell(ex, 69, 11, 11), 0.35, OLIVE, 0.5)
    c.paint(wing, c.vs(60, 75, 0.55, 0.7) - 0.08 * (c.x > 80), OLIVE)
    for ex in (30, 48, 80, 98):
        c.paint(c.ell(ex, 70, 5.5, 8), c.hs(ex - 5.5, ex + 5.5, 0.5, 0.7), OLIVE)
        c.solid(c.ell(ex, 70, 2.4, 2.4), "#d4dcb0")
        c.solid(c.ell(ex - 1, 69, 1, 1), "#ffffff")
    fus = c.ell(64, 80, 12, 17)
    c.paint(fus, c.hs(52, 76, 0.55, 0.6), OLIVE)
    c.paint(c.ell(64, 74, 8, 7), 0.8 - 0.3 * (c.x > 66), ramp("#1c2c3a", "#3a5a78", "#78a4c8", "#cde4f2"))
    c.solid(c.line([(58, 72), (70, 72)], 1), "#1c2014")
    c.solid(c.line([(64, 67), (64, 81)], 1), "#1c2014")
    wing = c.poly([(18, 65), (110, 65), (110, 75), (18, 75)])
    # a glint on the leading edge, dust blowing off the ground
    c.solid(c.line([(20, 66), (40, 64)], 1) & wing, "#e8f2f6")
    rng = _rs(934)
    for i in range(70):
        px, py = int(rng.randint(16, 112)), int(rng.randint(96, 120))
        if rng.rand() < 0.7:
            c.rgb[py, px] = col3("#d0ba80")
            c.a[py, px] = 255
    # inner jambs in shadow
    c.paint(c.rect(16, 14, 22, 120), 0.12, KHAKI)
    c.paint(c.rect(16, 14, 112, 19), 0.15, KHAKI)
    c.paint(c.rect(2, 120, 126, 126), c.vs(120, 126, 0.5, 0.5), KHAKI)
    c.outline()
    return c.out()


# ============================================================================================================================================
# BILLBOARDS: the neutral coast, the only saturated place
# ============================================================================================================================================

def thing_pine_umbrella():
    """A tall umbrella pine: a flat saturated-green crown of needle clumps on a warm brown leaning trunk, bright in the sun."""
    c = Cv()
    # trunk first: curved, tapering, flared at the root, with branches into the crown
    path = [(66, 126), (62, 100), (66, 76), (62, 54), (64, 40)]
    ws = [14, 10, 8, 7, 6]
    for (p, q, wa, wb) in zip(path[:-1], path[1:], ws[:-1], ws[1:]):
        c.paint(c.line([p, q], int((wa + wb) / 2)), c.hs(p[0] - 7, p[0] + 7, 0.55, 0.9), TRUNK)
    c.paint(c.poly([(54, 126), (80, 126), (70, 112), (62, 112)]), c.hs(54, 80, 0.5, 0.7), TRUNK)
    bark = c.line([(60, 120), (59, 96), (62, 70)], 1) | c.line([(68, 118), (69, 90), (66, 62)], 1)
    c.solid(bark, "#2a1408")
    c.solid(c.line([(61, 112), (60, 82)], 1), "#c4823e")
    for (p, q) in (((63, 56), (28, 38)), ((64, 52), (100, 38)), ((65, 62), (90, 46)), ((62, 60), (40, 48))):
        c.paint(c.line([p, q], 4), 0.5, TRUNK)
    # the crown: clumps painted back to front, each lit from the upper left
    clumps = [(64, 24, 30, 14, 0.5), (28, 34, 24, 12, 0.5), (100, 34, 24, 12, 0.5), (44, 28, 22, 12, 0.7), (86, 28, 22, 12, 0.7),
              (14, 42, 12, 8, 0.6), (114, 42, 12, 8, 0.6), (64, 36, 26, 10, 0.75), (36, 40, 16, 8, 0.8), (92, 40, 16, 8, 0.8), (64, 18, 22, 10, 1.0)]
    nz = fnoise((128, 128), 3, 941, 2)
    for cx, cy, rx, ry, lv in clumps:
        m = c.ell(cx, cy, rx, ry)
        u = (c.x - cx) / rx
        v = (c.y - cy) / ry
        sh = 0.3 + 0.35 * lv + 0.25 * (-u * 0.5 - v * 0.8) + (nz - 0.5) * 0.35
        c.paint(m, sh, PINEG)
        edge = m & ~c.ell(cx, cy, rx - 1.3, ry - 1.3) & (c.y > cy)
        c.paint(edge, 0.12 + 0.2 * nz, PINEG, 0.5)
    # needle flecks catching the sun along the top
    rng = _rs(942)
    crown = c.a > 0
    for i in range(90):
        px, py = int(rng.randint(6, 122)), int(rng.randint(6, 52))
        if crown[py, px] and not crown[max(py - 2, 0), px]:
            c.rgb[py, px:px + 3] = col3("#d4ff9a")
        elif crown[py, px] and rng.rand() < 0.3 and py < 40:
            c.rgb[py, px] = col3("#98ec50")
    c.paint(c.ell(64, 126, 26, 4), 0.55, SAND)
    c.outline(0.38)
    return c.out()


def thing_shore_boat():
    """The small fishing boat hauled up on the sand in bright sun: blue and white paint, gold nets drying over the side, an oar, a bright buoy."""
    c = Cv(128, 256)
    H, W = 128, 256
    mound = c.ell(128, 118, 120, 16) & (c.y > 98)
    c.paint(mound, 0.5 + 0.35 * np.clip(1 - (c.y - 98) / 20, 0, 1) - 0.15 * (c.x > 200) + (fnoise((H, W), 4, 951) - 0.5) * 0.2, SAND)
    c.solid(mound & (speckle(256, 0.04, 952)[:H, :W] > 0), "#fff0a4")
    # hull
    top = [(24, 46), (40, 58), (70, 68), (110, 73), (150, 74), (190, 72), (226, 64)]
    hull = c.poly(top + [(224, 88), (200, 102), (150, 108), (90, 106), (52, 98), (34, 78)])
    sheer = np.interp(np.arange(W), [p[0] for p in top], [p[1] for p in top])[None, :]
    yy = c.y - sheer
    stripe_w = hull & (yy < 11)
    c.paint(hull, 0.35 + 0.4 * np.clip(1 - (c.y - 60) / 46, 0, 1) + 0.1 * np.sin(c.x * 0.1) + 0.1 * ((yy % 9) > 7) - 0.14 * ((yy % 9) < 1), PAINTB)
    c.paint(stripe_w, 0.62 + 0.3 * np.clip(1 - yy / 11, 0, 1) - 0.08 * (c.x > 180) + 0.1 * ((yy % 9) > 7) * 0, PAINTW)
    c.solid(hull & (np.abs(yy - 11) < 1.0), "#1c62dc")
    c.paint(hull & (yy < 2.5), 0.8, WOODB)
    c.solid(c.line([(24, 46), (36, 62)], 1), "#ffe2a0")
    # a mast stub with a rope coil, a bright orange buoy hung at the bow
    c.paint(c.rect(120, 26, 127, 74), c.hs(120, 127, 0.55, 0.7), WOODB)
    for cy in (46, 51, 56):
        _rope_band(c, 123.5, cy, 6, 3, 2, cy)
    c.paint(c.ell(46, 76, 7, 7), c.hs(39, 53, 0.6, 0.7) + 0.0, ORANGE)
    c.solid(c.ell(44, 73, 1.8, 1.8), "#fff2cc")
    c.solid(c.line([(46, 69), (44, 62)], 1), "#8a5a28")
    # gold nets dried over the starboard side and heaped on the sand
    mesh = (((c.x + c.y) % 7) < 1.4) | (((c.x - c.y) % 7) < 1.4)
    drape = c.poly([(148, 68), (200, 68), (204, 92), (190, 104), (160, 100), (150, 86)])
    c.paint(drape & mesh, 0.35 + 0.55 * fnoise((H, W), 6, 953, 2) + 0.1 * (c.x < 170), NETD)
    heap = c.ell(176, 108, 24, 8) & (c.y > 100)
    c.paint(heap, 0.3 + 0.3 * fnoise((H, W), 3, 954), NETD)
    c.paint(heap & mesh, 0.7, NETD)
    for fx, fy in ((156, 70), (170, 72), (186, 72), (200, 90)):
        c.paint(c.ell(fx, fy, 3.2, 3.2), c.hs(fx - 3, fx + 3, 0.6, 0.7), ORANGE)
    # an oar lying on the sand, a shadow under the keel
    oar = c.line([(60, 108), (130, 114), (176, 118)], 3)
    c.paint(oar, 0.55 + 0.25 * (c.y < 112), WOODB)
    c.paint(c.poly([(206, 112), (236, 108), (240, 114), (206, 120)]), 0.6, WOODB)
    c.solid(c.line([(176, 118), (206, 116)], 3), "#e8aa5c")
    sh = c.ell(138, 111, 96, 3.5) & (c.y > 107) & ~hull
    c.paint(sh, 0.2 + 0.2 * fnoise((H, W), 3, 955), SAND)
    c.outline(0.45)
    return c.out()


def thing_birds():
    """A loose flock of white gulls in flight against the sky, wings at different beats; transparent background."""
    c = Cv()

    def gull(cx, cy, s, ph, d):
        # wings: shoulder -> elbow -> tip, the elbow lifted by the beat
        for side in (-1, 1):
            sh = (cx + side * 3 * s, cy - 1 * s)
            el = (cx + side * 11 * s, cy - (4 + 7 * ph) * s)
            tip = (cx + side * 23 * s, cy + (2 - 6 * ph) * s)
            w1 = max(2, int(3.2 * s))
            m1 = c.line([sh, el], w1)
            m2 = c.line([el, tip], max(2, int(2.6 * s)))
            c.solid(m1 | m2, "#ffffff")
            under = (m1 | m2) & (c.y > np.minimum(sh[1], tip[1]) + 1.2 * s) & (c.y > cy - 2 * s)
            c.solid(under & ((c.x + c.y) % 2 == 0), "#d4dee8")
            end = c.line([(el[0] + (tip[0] - el[0]) * 0.62, el[1] + (tip[1] - el[1]) * 0.62), tip], max(2, int(2.4 * s)))
            c.solid(end, "#3a424e")
        c.solid(c.ell(cx, cy + 0.5 * s, 5.5 * s, 3 * s), "#ffffff")
        c.solid(c.ell(cx, cy + 2 * s, 4.5 * s, 1.5 * s), "#c4d0dc")
        c.solid(c.ell(cx + d * 6 * s, cy - 0.5 * s, 2.6 * s, 2.2 * s), "#ffffff")
        c.solid(c.poly([(cx - d * 5 * s, cy), (cx - d * 12 * s, cy + 1 * s), (cx - d * 11 * s, cy + 3.5 * s), (cx - d * 4 * s, cy + 3 * s)]), "#e8eef4")
        bx = int(cx + d * 8.4 * s)
        c.solid(c.rect(bx, int(cy), bx + 2, int(cy) + 1.5), "#ff9a20")
        c.solid(c.ell(cx + d * 6.6 * s, cy - 1 * s, 0.7, 0.7), "#101418")

    for (cx, cy, s, ph, d) in ((34, 30, 1.3, 0.8, 1), (84, 20, 1.0, -0.3, 1), (92, 56, 1.4, 0.3, -1), (44, 68, 0.95, -0.8, 1), (18, 92, 0.75, 0.5, -1), (72, 96, 0.8, 0.9, 1), (108, 108, 0.6, -0.5, -1), (40, 112, 0.6, 0.2, 1), (112, 24, 0.6, 0.7, -1)):
        gull(cx, cy, s, ph, d)
    c.outline(0.62)
    return c.out()


def thing_sunshade():
    """A faded orange-and-white beach sunshade over a little table with a turquoise jug and two cups."""
    c = Cv()
    # table, pole and legs
    c.paint(c.line([(40, 98), (30, 124)], 3), 0.5, WOODB)
    c.paint(c.line([(88, 98), (98, 124)], 3), 0.35, WOODB)
    c.paint(c.line([(64, 98), (64, 124)], 3), 0.45, WOODB)
    c.paint(c.ell(64, 126, 34, 3), 0.6, SAND)
    c.paint(c.rect(62, 46, 67, 100), c.hs(62, 67, 0.55, 0.7), PAINTW)
    top = c.ell(64, 94, 38, 7)
    c.paint(top, 0.7 + 0.2 * (c.x < 64) - 0.2 * ((c.y - 94) / 7), WOODB)
    c.paint(c.rect(26, 94, 102, 98) & ~c.ell(64, 98, 38, 7) | (c.ell(64, 96, 38, 7) & (c.y > 95) & ~c.ell(64, 92, 38, 7)), 0.3, WOODB)
    c.paint(c.ell(64, 94, 36, 5.4), 0.78 + 0.15 * (c.x < 60), ramp("#a2622a", "#c8863e", "#e8aa5c", "#ffd488"))
    # jug (turquoise) and two cups (white with a blue band)
    jug = c.ell(44, 84, 8, 10)
    c.paint(jug, c.hs(36, 52, 0.55, 0.7), TURQ)
    c.paint(c.rect(41, 70, 48, 77), c.hs(41, 48, 0.55, 0.7), TURQ)
    c.paint(c.ell(44.5, 70, 4.5, 1.6), 0.25, TURQ)
    c.paint(c.ring(53, 84, 4.5, 5.5, 1.8), 0.5, TURQ)
    c.solid(c.line([(41, 79), (41, 86)], 1), "#c8fff0")
    for cx in (80, 92):
        cup = c.poly([(cx - 5, 83), (cx + 5, 83), (cx + 3.5, 94), (cx - 3.5, 94)])
        c.paint(cup, c.hs(cx - 5, cx + 5, 0.75, 0.5), PAINTW)
        c.paint(cup & (np.abs(c.y - 87.5) < 1.5), 0.55, PAINTB)
        c.paint(c.ell(cx, 83, 5, 1.5), 0.3, PAINTW)
    # the canopy: a dome with a scalloped hem, radial stripes, faded
    edge = 50 + 4.5 * np.sqrt(np.clip(1 - (((c.x - 4) % 15) - 7.5) ** 2 / 7.5 ** 2, 0, 1))
    dome = c.ell(64, 54, 62, 46) & (c.y < edge) & (c.y < 54 + 8)
    theta = np.arctan2(c.x - 64, (c.y + 6) * 1.1)
    stripe = np.floor((theta + 1.35) / 0.3).astype(int) % 2
    lit = 0.62 - 0.32 * np.clip((c.x - 20) / 100, 0, 1) - 0.18 * np.clip((c.y - 36) / 18, 0, 1) + (fnoise((128, 128), 4, 961) - 0.5) * 0.1
    c.paint(dome & (stripe == 0), lit, ORANGE)
    c.paint(dome & (stripe == 1), lit + 0.25, PAINTW)
    c.solid(dome & (np.abs(((theta + 1.35) / 0.3) % 1) < 0.04) & (c.y > 16), "#8a3408")
    c.solid(c.rect(62, 0, 66, 10), "#f08828")
    c.solid(c.ell(64, 4, 3, 3), "#ffb050")
    hem = dome & (c.y > edge - 2)
    c.solid(hem & (stripe == 0), "#c85a14")
    c.outline(0.5)
    return c.out()


def thing_wooden_post():
    """A weathered wooden jetty post with a bright blue painted top and a coil of rope, its mate a little shorter behind a sagging line."""
    c = Cv()
    WEATH = ramp("#2a2218", "#4a4034", "#6e6454", "#948a76", "#b4aa94")
    c.paint(c.ell(64, 125, 58, 4), 0.6, SAND)
    # the short mate on the right
    c.paint(c.rect(96, 68, 116, 126), c.hs(96, 116, 0.55, 0.75) + (fnoise((128, 128), 3, 971) - 0.5) * 0.15, WEATH)
    c.paint(c.rect(96, 68, 116, 84), c.hs(96, 116, 0.65, 0.7), PAINTB)
    c.paint(c.ell(106, 68, 10, 3), 0.9, PAINTB)
    # the tall main post
    post = c.rect(28, 20, 68, 126)
    gx = np.sin(c.x * 0.9 + fnoise((128, 128), 6, 972) * 8)
    c.paint(post, c.hs(28, 68, 0.55, 0.75) + 0.06 * gx + (fnoise((128, 128), 3, 973) - 0.5) * 0.2, WEATH)
    c.solid(post & (fnoise((128, 128), 10, 974, 2) > 0.8) & (c.y > 50), "#2a2218")
    for kx, ky0, ky1 in ((38, 60, 84), (56, 96, 120), (46, 104, 124)):
        c.solid(c.line([(kx, ky0), (kx + 1, ky1)], 1), "#2a2218")
    paint = post & (c.y < 50 + 3.5 * np.sin(c.x * 0.6) + 2 * np.sin(c.x * 1.7))
    c.paint(paint, c.hs(28, 68, 0.62, 0.65) + (fnoise((128, 128), 4, 975) - 0.5) * 0.12, PAINTB)
    chip = paint & (fnoise((128, 128), 3, 976, 2) > 0.72)
    c.paint(chip, 0.55, WEATH)
    c.paint(c.ell(48, 20, 20, 4.5), 0.8, PAINTB)
    c.solid(c.ell(40, 19, 6, 1.4), "#b8dcff")
    c.solid(c.line([(30, 26), (30, 46)], 1), "#78b8ff")
    # the rope coil around the post, tail hanging, a swag to the shorter post
    for cy in (70, 76, 82, 88):
        _rope_band(c, 48, cy, 22, 5, 3, cy)
    c.solid(c.line([(30, 70), (30, 88)], 1), "#0a0705")
    tail = c.line([(60, 90), (64, 104), (72, 112), (66, 120)], 3)
    c.paint(tail, 0.5 + 0.3 * np.sin(c.y * 0.9), ROPE)
    swag = [(68, 74)]
    for k in range(1, 9):
        t = k / 8.0
        swag.append((68 + t * 30, 74 + 14 * np.sin(t * np.pi) + 4 * t))
    c.paint(c.line(swag, 3), 0.55 + 0.3 * np.sin(c.x * 0.8), ROPE)
    c.paint(c.ell(100, 80, 3, 3), 0.5, ROPE)
    c.outline(0.45)
    return c.out()


_NAMES = ["floor_quay", "wall_quay", "floor_cell", "wall_cell", "ceil_cell", "ceil_night_blue", "ceil_sky_day", "floor_sand", "wall_dunes", "sky_harbour"]
_NAMES += [k for k in ("thing_bollard", "thing_quay_lamp", "thing_searchlight", "thing_beam", "thing_cell_door", "thing_bunk", "thing_window_latch", "thing_fishing_boat", "thing_nets",
                       "thing_count_board", "thing_radio_broken", "thing_order_paper", "thing_aircraft_door", "thing_pine_umbrella", "thing_shore_boat", "thing_birds", "thing_sunshade",
                       "thing_wooden_post") if k in globals()]
DRAW = {k: globals()[k] for k in _NAMES}
