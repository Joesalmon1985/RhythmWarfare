"""Gospel adventure (Life of Jesus), billboard "things" A: sunlit, dusty, warm props for the 2.5D world.

`build(out_dir)` writes every sprite below as `<name>.png` (RGBA, exact size) and returns {name: {"size": [w, h], "blend": "" | "add" | "mix"}}.
Same pixel look as tex_hospital / tex_night_one: mid-tone shaded forms, 8x8 ordered-dither posterise, a darker edge of the local colour, no pure black or
white. Painted in DAYLIGHT mid-tones (the engine multiplies a sprite by the room's light). "solid" sprites have alpha 0 or 255 only; (add)/(mix) sprites
use graded alpha. Subjects stand on the bottom row, horizontally centred. Self-contained (numpy + Pillow only), deterministic (every random value seeded).
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

BAYER8 = (np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38],
                    [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
                    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]], np.float32) + 0.5) / 64.0 - 0.5

SPRITES: dict = {}


def sprite(name: str, w: int, h: int, blend: str = ""):
    def deco(fn):
        SPRITES[name] = (w, h, blend, fn)
        return fn
    return deco


# ---- kit ------------------------------------------------------------------------------------------------------------------------------------------------

def hx(c) -> np.ndarray:
    if not isinstance(c, str):
        return np.asarray(c, np.float32)
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def ramp(*cols) -> np.ndarray:
    return np.stack([hx(c) for c in cols])


def blur(a: np.ndarray, s: float) -> np.ndarray:
    """Gaussian blur of a 2D float array (zero outside)."""
    if s <= 0:
        return a
    r = int(math.ceil(s * 3))
    k = np.exp(-(np.arange(-r, r + 1) ** 2) / (2.0 * s * s)).astype(np.float32)
    k /= k.sum()
    h, w = a.shape
    p = np.pad(a.astype(np.float32), ((0, 0), (r, r)))
    o = sum(k[i] * p[:, i:i + w] for i in range(2 * r + 1))
    p = np.pad(o, ((r, r), (0, 0)))
    return sum(k[i] * p[i:i + h, :] for i in range(2 * r + 1))


def vnoise(w: int, h: int, scale: float, seed: int, octaves: int = 3) -> np.ndarray:
    """Smooth value noise 0..1."""
    rng = np.random.RandomState(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gw = max(2, int(round(w / scale * 2 ** o)) + 1)
        gh = max(2, int(round(h / scale * 2 ** o)) + 1)
        g = rng.rand(gh, gw).astype(np.float32)
        out += np.asarray(Image.fromarray(g).resize((w, h), Image.BILINEAR), np.float32) * amp
        tot += amp
        amp *= 0.5
    return out / tot


def erode(m: np.ndarray) -> np.ndarray:
    p = np.pad(m, 1, constant_values=True)
    return m & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]


def dilate(m: np.ndarray) -> np.ndarray:
    p = np.pad(m, 1, constant_values=False)
    return m | p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]


LIGHT = np.array([-0.5, -0.6, 0.62], np.float32)
LIGHT /= np.linalg.norm(LIGHT)


class Cv:
    """Float RGB + alpha canvas, y down. Masks come from the primitives, painting is by mask."""

    def __init__(self, w: int, h: int, seed: int = 1):
        self.w, self.h, self.seed = w, h, seed
        self.rgb = np.zeros((h, w, 3), np.float32)
        self.a = np.zeros((h, w), np.float32)
        self.y, self.x = np.mgrid[0:h, 0:w].astype(np.float32)
        self.rng = np.random.RandomState(seed)

    # masks
    def box(self, x0, y0, x1, y1):
        return (self.x >= x0) & (self.x < x1) & (self.y >= y0) & (self.y < y1)

    def ell(self, cx, cy, rx, ry):
        return ((self.x - cx) / rx) ** 2 + ((self.y - cy) / ry) ** 2 <= 1.0

    def _im(self):
        im = Image.new("L", (self.w, self.h), 0)
        return im, ImageDraw.Draw(im)

    def poly(self, pts):
        im, d = self._im()
        d.polygon([(float(a), float(b)) for a, b in pts], fill=255)
        return np.asarray(im) > 0

    def line(self, pts, w=1):
        im, d = self._im()
        d.line([(float(a), float(b)) for a, b in pts], fill=255, width=max(1, int(round(w))), joint="curve")
        return np.asarray(im) > 0

    def taper(self, pts, w0, w1):
        """A stroke through pts whose width runs w0 -> w1 (round brush, drawn along a dense walk)."""
        im, d = self._im()
        pts = [(float(a), float(b)) for a, b in pts]
        seg = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
        tot = max(sum(seg), 1e-6)
        acc = 0.0
        for i, sl in enumerate(seg):
            n = max(1, int(sl * 2))
            for j in range(n + 1):
                t = j / n
                px_, py_ = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
                r = (w0 + (w1 - w0) * (acc + sl * t) / tot) * 0.5
                if r < 0.7:
                    d.point((int(round(px_)), int(round(py_))), fill=255)
                else:
                    d.ellipse([px_ - r + 0.5, py_ - r + 0.5, px_ + r - 0.5, py_ + r - 0.5], fill=255)
            acc += sl
        return np.asarray(im) > 0

    def bez(self, p0, p1, p2, n=24):
        out = []
        for i in range(n + 1):
            t = i / n
            out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
        return out

    # painting
    def paint(self, mask, col):
        c = hx(col) if isinstance(col, str) else np.asarray(col, np.float32)
        if c.ndim == 1:
            c = c[None, None, :]
        self.rgb = np.where(mask[..., None], np.broadcast_to(c, self.rgb.shape), self.rgb)
        self.a = np.where(mask, 1.0, self.a).astype(np.float32)

    def rpaint(self, mask, field, pal, dither=0.9):
        """Paint mask with palette `pal` chosen by a 0..1 field (ordered dither between steps)."""
        k = len(pal) - 1
        b = BAYER8[np.arange(self.h)[:, None] % 8, np.arange(self.w)[None, :] % 8]
        i = np.clip(np.round(np.clip(np.nan_to_num(field), 0, 1) * k + b * dither), 0, k).astype(int)
        self.paint(mask, pal[i])

    def sphere(self, cx, cy, rx, ry, pal, bias=0.0, gain=1.0, jit=None, mask=None):
        m = self.ell(cx, cy, rx, ry)
        if mask is not None:
            m = m & mask
        nx, ny = (self.x - cx) / rx, (self.y - cy) / ry
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
        s = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
        f = 0.55 + s * 0.5 * gain + bias
        if jit is not None:
            f = f + jit
        self.rpaint(m, f, pal)
        return m

    def edge(self, mask, k=0.66):
        inner = mask & ~erode(mask)
        self.rgb = np.where(inner[..., None], self.rgb * k, self.rgb)

    def silhouette_edge(self, k=0.64):
        self.edge(self.a >= 0.5, k)

    def speck(self, mask, col, density, seed):
        r = np.random.RandomState(seed).rand(self.h, self.w) < density
        self.paint(mask & r, col)

    def glow(self, cx, cy, r, col, k=0.6, mask=None):
        d = np.sqrt((self.x - cx) ** 2 + (self.y - cy) ** 2) / r
        g = np.clip(1 - d, 0, 1) ** 2 * k
        if mask is not None:
            g = g * mask
        self.rgb = self.rgb + hx(col)[None, None, :] * g[..., None] * (self.a[..., None] >= 0.5)

    def tint(self, mask, col, amt):
        self.rgb = np.where(mask[..., None], self.rgb * (1 - amt) + hx(col)[None, None, :] * amt, self.rgb)

    def mul(self, mask, k):
        kk = np.asarray(k, np.float32)
        if kk.ndim == 2:
            kk = kk[..., None]
        self.rgb = np.where(mask[..., None], self.rgb * kk, self.rgb)

    def haze(self, col, amt, lift=0.0):
        """Aerial perspective: mix solid pixels toward a haze colour (lower contrast)."""
        m = self.a >= 0.5
        mean = self.rgb[m].mean(axis=0) if m.any() else self.rgb.mean(axis=(0, 1))
        flat = self.rgb * 0.7 + mean[None, None, :] * 0.3
        self.rgb = np.where(m[..., None], flat * (1 - amt) + hx(col)[None, None, :] * amt + lift, self.rgb)

    def vgrad(self, y0, y1):
        return np.clip((self.y - y0) / max(y1 - y0, 1e-6), 0, 1)


def dith(img: np.ndarray, levels: int = 24) -> np.ndarray:
    h, w = img.shape[:2]
    b = BAYER8[np.arange(h)[:, None] % 8, np.arange(w)[None, :] % 8][..., None]
    v = np.clip(img, 0, 1) * (levels - 1) + b
    return (np.clip(np.round(v), 0, levels - 1) / (levels - 1) * 255 + 0.5).astype(np.uint8)


def bleed(rgb: np.ndarray, solid: np.ndarray, it: int = 4) -> np.ndarray:
    """Spread edge colour into the transparent pixels (no dark fringes if the engine filters)."""
    rgb = rgb.copy()
    have = solid.copy()
    for _ in range(it):
        p = np.pad(rgb, ((1, 1), (1, 1), (0, 0)))
        ph = np.pad(have, 1)
        acc = np.zeros_like(rgb)
        cnt = np.zeros(have.shape, np.float32)
        for dy, dx in ((0, 1), (2, 1), (1, 0), (1, 2)):
            nb = ph[dy:dy + have.shape[0], dx:dx + have.shape[1]]
            acc += p[dy:dy + have.shape[0], dx:dx + have.shape[1]] * nb[..., None]
            cnt += nb
        fill = (~have) & (cnt > 0)
        rgb = np.where(fill[..., None], acc / np.maximum(cnt, 1)[..., None], rgb)
        have = have | fill
    return rgb


def finish_solid(c: Cv, levels: int = 24) -> np.ndarray:
    solid = c.a >= 0.5
    rgb = bleed(np.clip(c.rgb, 0.07, 0.95), solid)
    out = np.zeros((c.h, c.w, 4), np.uint8)
    out[..., :3] = dith(np.clip(rgb, 0.07, 0.95), levels)
    out[..., 3] = np.where(solid, 255, 0)
    return out


def finish_soft(rgb: np.ndarray, a: np.ndarray, levels: int = 24, qa: int = 32) -> np.ndarray:
    """RGB (h, w, 3) float + alpha float -> RGBA8 with the alpha posterised (ordered dither) so the soft light keeps a pixel look."""
    h, w = a.shape
    b = BAYER8[np.arange(h)[:, None] % 8, np.arange(w)[None, :] % 8]
    aq = np.clip(np.round(np.clip(a, 0, 1) * (qa - 1) + b * 0.8), 0, qa - 1) / (qa - 1)
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = dith(np.clip(rgb, 0.0, 0.97), levels)
    out[..., 3] = np.round(aq * 255).astype(np.uint8)
    return out


# palettes (daylight mid-tones)
WOOL = ramp("#9c927c", "#c0b8a2", "#ddd5c0", "#efe9d8", "#f6f1e4")
STONE = ramp("#8c7d62", "#ad9c7a", "#c9b894", "#dfd0ac", "#ede2c4")
STONE_PALE = ramp("#9a8d72", "#b9ab8c", "#d3c6a6", "#e6dbbd", "#f2e9cf")
OCHRE = ramp("#7e5a2c", "#a67a3a", "#c8964a", "#dcb468", "#ebcf8c")
THATCH = ramp("#6a4e26", "#8c6c34", "#b08c44", "#cfaa58", "#e6c878")
WOOD = ramp("#4a3220", "#6a4a2c", "#87603a", "#a27a4c", "#b8905e")
WOOD_DARK = ramp("#2e2016", "#463020", "#5e4128", "#765436", "#8c6844")
OLIVE_SIL = ramp("#4c5a4a", "#68766a", "#8a9a86", "#b0bca6", "#ced6bf")
GREEN_DRY = ramp("#4e5a2c", "#6a7a38", "#8a9a4c", "#a8b866", "#c4cf86")
STRAW = ramp("#8a6e32", "#aa8c44", "#c8aa58", "#dec274", "#efd890")
ROCK = ramp("#5e5648", "#7d7260", "#9c8e76", "#b9a88a", "#d2c2a0")
GREY_STONE = ramp("#7a7c80", "#9a9c9c", "#b8b8b4", "#d0d0c8", "#e2e2da")
HAZE_BLUE = "#84a6d0"


# ==== SPRITES ====
def strands(c: Cv, mask, n, cols, seed, lmin=4, lmax=9, ang=(-70, 70), base_ang=0.0):
    """Short straw / grass strands scattered over a mask (drawn in colours cols, clipped to mask)."""
    rng = np.random.RandomState(seed)
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return
    for i in range(n):
        k = rng.randint(len(ys))
        x0, y0 = float(xs[k]), float(ys[k])
        a = math.radians(base_ang + rng.uniform(*ang))
        ln = rng.uniform(lmin, lmax)
        m = c.line([(x0, y0), (x0 + math.sin(a) * ln, y0 - math.cos(a) * ln)], 1) & mask
        c.paint(m, cols[rng.randint(len(cols))])


@sprite("thing_stable", 160, 128)
def th_stable():
    c = Cv(160, 128, 11)
    x, y = c.x, c.y
    rng = c.rng
    roof_top = lambda xx: 8 + np.clip((xx - 18) * (20.0 / 132), 0, 22)
    # back wall: dark timber boards lit by the lamp
    inner = c.box(14, 44, 146, 124)
    d = np.hypot(x - 88, y - 70)
    glow = np.clip(1 - d / 66.0, 0, 1) ** 1.5
    idx = np.floor((x - 14) / 8).astype(int)
    tone = np.random.RandomState(3).rand(40)[np.clip(idx, 0, 39)]
    grain = (vnoise(160, 128, 3.0, 5, 2) - 0.5) * 0.18
    f = 0.14 + 0.62 * glow + tone * 0.10 + grain - 0.12 * (((x - 14) % 8) < 1)
    c.rpaint(inner, f, WOOD_DARK)
    # floor of trodden earth and straw
    floor = c.box(6, 112, 154, 128)
    ff = 0.42 + 0.35 * glow + (vnoise(160, 128, 4.0, 7, 2) - 0.5) * 0.4
    c.rpaint(floor, ff, ramp("#5e4a2c", "#7a6038", "#98794a", "#b8955a", "#d0aa68"))
    strands(c, floor, 90, [hx("#d8b866"), hx("#b8944c"), hx("#e8cc80")], 21, 3, 7, (-80, 80), 70)
    # manger trestle legs and trough
    for lx in (50, 96):
        c.paint(c.line([(lx, 108), (lx + 10, 126)], 3), "#4a3220")
        c.paint(c.line([(lx + 10, 108), (lx, 126)], 3), "#5a3e26")
        c.paint(c.box(lx - 1, 124, lx + 13, 127), "#3a2818")
    trough = c.poly([(40, 92), (112, 92), (106, 111), (46, 111)])
    tf = 0.78 - 0.5 * ((y - 92) / 19.0) + (vnoise(160, 128, 5.0, 9, 2) - 0.5) * 0.2 - 0.14 * (((y - 92) % 6) < 1)
    c.rpaint(trough, tf, WOOD)
    c.edge(trough, 0.6)
    c.rpaint(c.box(38, 90, 114, 94), 0.85 - 0.3 * ((x - 38) / 76.0), WOOD)
    c.edge(c.box(38, 90, 114, 94), 0.6)
    # straw heaped in the trough
    heap = c.ell(76, 91, 33, 10) & (y < 93)
    hf = 0.45 + 0.4 * (1 - (y - 81) / 12.0) + (vnoise(160, 128, 3.0, 12, 2) - 0.5) * 0.5
    c.rpaint(heap, hf, STRAW)
    strands(c, heap | c.box(48, 80, 104, 83) & c.ell(76, 91, 35, 13), 70, [hx("#efd890"), hx("#dec274"), hx("#a8863e")], 31, 4, 9, (-75, 75), 70)
    # hay bundle (a tied sheaf) at the right
    sheaf = c.poly([(112, 123), (115, 99), (124, 90), (133, 99), (137, 123)])
    sf = 0.62 + 0.25 * np.sin(x * 1.7) * 0.5 + (vnoise(160, 128, 2.5, 14, 2) - 0.5) * 0.5 - 0.25 * ((x - 112) / 25.0) + 0.1
    c.rpaint(sheaf, sf, STRAW)
    strands(c, c.box(108, 86, 140, 100), 26, [hx("#e6cc7c"), hx("#c8aa58")], 41, 5, 9, (-40, 40), 0)
    band = c.box(113, 107, 137, 110) & sheaf
    c.paint(band, "#8a6030")
    c.paint(band & (y < 108), "#a8793c")
    c.edge(sheaf, 0.62)
    # posts, header beam, braces
    for x0, x1, top in ((8, 19, 30), (141, 152, 36)):
        pm = c.box(x0, top, x1, 128)
        pf = 0.78 - 0.5 * ((x - x0) / (x1 - x0)) + (vnoise(160, 128, 6.0, int(x0), 2) - 0.5) * 0.3 + 0.15 * (((x + y * 0.15) % 5) < 1)
        c.rpaint(pm, pf, WOOD)
        c.edge(pm, 0.6)
    beam = c.box(6, 40, 154, 49)
    c.rpaint(beam, 0.8 - 0.55 * ((y - 40) / 9.0) + (vnoise(160, 128, 8.0, 8, 2) - 0.5) * 0.3, WOOD)
    c.edge(beam, 0.6)
    for brace in ([(19, 66), (19, 49), (34, 49)], [(141, 66), (141, 49), (126, 49)]):
        bm = c.poly(brace)
        c.rpaint(bm, 0.35 + 0.0 * x, WOOD)
        c.edge(bm, 0.6)
    # lamp: chain and lantern
    c.paint(c.line([(88, 49), (88, 57)], 1), "#6a5030")
    lant = c.box(84, 58, 92, 70)
    c.paint(lant, "#f6dc9c")
    c.paint(c.box(87, 61, 89, 67), "#fff4cc")
    c.paint(c.box(84, 58, 85, 70) | c.box(91, 58, 92, 70) | c.box(84, 69, 92, 71), "#6a4a28")
    c.paint(c.poly([(83, 58), (93, 58), (88, 53)]), "#6a4a28")
    # roof of thatch with a ragged fringe
    base_y = 54
    fr = np.repeat(np.random.RandomState(17).rand(80), 3)[:160]
    fringe = (y >= base_y) & (y < base_y + 1.5 + fr[np.clip(x.astype(int), 0, 159)] * 5.5) & (x >= 2) & (x < 158)
    roof = c.poly([(18, 8), (150, 28), (158, base_y), (2, base_y)]) | fringe
    v = np.clip((y - roof_top(x)) / (base_y + 3 - roof_top(x)), 0, 1)
    strand_t = np.random.RandomState(19).rand(90)[(x.astype(int) // 2) % 90]
    rf = 0.9 - 0.52 * v ** 1.1 + (strand_t - 0.5) * 0.28 + (1 - x / 160.0) * 0.1
    course = (v * 5.0) % 1.0
    rf = rf - 0.2 * (course < 0.09) + 0.07 * ((course > 0.09) & (course < 0.22))
    rf = rf + (vnoise(160, 128, 3.0, 23, 2) - 0.5) * 0.2
    c.rpaint(roof, rf, THATCH)
    cap = roof & (y < roof_top(x) + 3.5)
    c.rpaint(cap, 0.28 + (vnoise(160, 128, 2.0, 25, 2) - 0.5) * 0.5, THATCH)
    c.edge(roof, 0.58)
    # shadow under the eave, lamp glow on everything below the roof
    sh = np.clip(1 - (y - 55) / 14.0, 0, 1)
    c.mul(inner & ~roof & ~beam & (y > 49) & (y < 70), 1 - 0.42 * sh)
    c.glow(88, 66, 60, "#ffb248", 0.45, mask=(~roof & (y > 50)).astype(np.float32))
    # a few stones at the post feet, loose straw in front
    for sx, sy, rx, ry in ((6, 125, 5, 3), (21, 126, 4, 2), (146, 125, 5, 3), (155, 126, 4, 2)):
        c.sphere(sx, sy, rx, ry, ROCK, mask=y < 128)
    strands(c, c.box(4, 121, 156, 128), 40, [hx("#e8cc80"), hx("#c8aa58")], 51, 3, 6, (-85, 85), 80)
    c.silhouette_edge(0.7)
    return finish_solid(c)


@sprite("thing_star", 128, 128, "add")
def th_star():
    n = 128
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    dx, dy = xx - 63.5, yy - 63.5
    I = np.zeros((n, n), np.float32)

    def ray(deg, L, wid, wgt, pw=1.5):
        a = math.radians(deg)
        al = dx * math.cos(a) + dy * math.sin(a)
        pe = np.abs(-dx * math.sin(a) + dy * math.cos(a))
        t = np.clip(al / L, 0, 1)
        wd = wid * (1 - t) ** 0.9 + 0.55
        return wgt * (1 - t) ** pw * np.exp(-(pe / wd) ** 1.6) * (al >= 0) * (al <= L)

    for deg in (0, 90, 180, 270):
        I += ray(deg, 62, 3.4, 1.0)
        I += ray(deg, 62, 8.0, 0.22, 2.2)
    for deg in (45, 135, 225, 315):
        I += ray(deg, 38, 2.6, 0.8)
        I += ray(deg, 40, 6.0, 0.16, 2.2)
    r = np.hypot(dx, dy)
    I += np.exp(-(r / 6.5) ** 2) * 1.1 + np.exp(-(r / 19.0) ** 2) * 0.42
    I = np.clip(I, 0, 1)
    t = np.clip(I * 1.15, 0, 1)[..., None]
    lo, mid, hi = hx("#ff9c34"), hx("#ffd664"), hx("#fff4cc")
    col = np.where(t < 0.55, lo + (mid - lo) * (t / 0.55), mid + (hi - mid) * np.clip((t - 0.55) / 0.45, 0, 1))
    return finish_soft(col, I)


def wool_body(c: Cv, bumps, seed, pal=WOOL):
    rng = np.random.RandomState(seed)
    for cx, cy, rx, ry, bias in bumps:
        jit = (vnoise(c.w, c.h, 3.0, int(rng.randint(1000)), 2) - 0.5) * 0.18
        c.sphere(cx, cy, rx, ry, pal, bias=bias, gain=1.3, jit=jit)


@sprite("thing_sheep", 48, 40)
def th_sheep():
    c = Cv(48, 40, 61)
    leg = "#54443a"
    for lx in (14, 19):
        c.paint(c.box(lx, 27, lx + 3, 40), "#46382f")
    for lx in (28, 33):
        c.paint(c.box(lx, 27, lx + 3, 40), leg)
    for lx in (14, 19, 28, 33):
        c.paint(c.box(lx, 37, lx + 3, 40), "#2e231d")
    # tail
    wool_body(c, [(7, 20, 3.5, 3.5, -0.05)], 1)
    # head (dark face, small ear)
    head = c.ell(42, 19.5, 4.6, 6.4)
    c.rpaint(head, 0.7 - 0.35 * (c.x - 36) / 9.0, ramp("#3a2e28", "#54443a", "#6e5c4e", "#86705e"))
    c.paint(c.ell(38.6, 18.5, 3.0, 1.6) & ~c.ell(42, 19.5, 3.2, 4), "#5a4a40")
    c.paint(c.ell(45, 23.5, 1.9, 2.4), "#8a7462")
    c.paint(c.box(43, 18, 44, 19), "#e8dcc4")
    c.paint(c.box(45, 23, 46, 24), "#2e231d")
    # body wool
    wool_body(c, [(14, 22, 9, 8, -0.12), (23, 23, 10, 8.5, -0.14), (31, 22, 8, 8, -0.1), (18, 15.5, 8, 7, 0.0), (26, 15, 8.5, 7, 0.02),
                  (12, 17, 5.5, 5.5, 0.0), (32.5, 16.5, 5.0, 5.2, 0.0), (22, 11, 7, 5, 0.06)], 2)
    wool_body(c, [(40, 12.5, 4.2, 3.2, 0.02)], 3)
    c.silhouette_edge(0.7)
    return finish_solid(c)


@sprite("thing_sheep_lie", 48, 32)
def th_sheep_lie():
    c = Cv(48, 32, 62)
    c.paint(c.ell(39, 29.5, 4.2, 2.0), "#46382f")
    wool_body(c, [(7, 24, 3.5, 3.5, -0.08)], 4)
    head = c.ell(42.5, 21.5, 4.4, 5.8)
    c.rpaint(head, 0.7 - 0.35 * (c.x - 37) / 9.0, ramp("#3a2e28", "#54443a", "#6e5c4e", "#86705e"))
    c.paint(c.ell(39.3, 19, 3.0, 1.5) & ~c.ell(42.5, 20.5, 3.2, 3.6), "#5a4a40")
    c.paint(c.ell(45.6, 24.2, 1.8, 2.2), "#8a7462")
    c.paint(c.box(44, 19, 45, 20), "#e8dcc4")
    wool_body(c, [(15, 23, 9, 8, -0.12), (24, 23.5, 10.5, 8, -0.14), (32, 24, 8, 7.5, -0.1), (19, 16, 8, 6.5, 0.0), (27, 15.5, 8.5, 6.5, 0.03),
                  (13, 18, 5.5, 5.5, 0.0), (23, 12, 7, 4.5, 0.07), (34.5, 18.5, 4.6, 4.8, 0.0)], 5)
    wool_body(c, [(40.5, 14.5, 4.0, 3.2, 0.02)], 6)
    c.silhouette_edge(0.7)
    return finish_solid(c)


def flame(c: Cv, cx, by, hgt, wid, sway, col, wob=1.0):
    t = (by - c.y) / hgt
    cen = cx + sway * t ** 2 + wob * np.sin(t * 8.0 + cx) * t
    hw = wid * np.clip(1 - t, 0, 1) ** 0.85 * (0.55 + 0.45 * np.minimum(1, t * 5))
    m = (t >= 0) & (t <= 1) & (np.abs(c.x - cen) <= hw)
    c.paint(m, col)
    return m


@sprite("thing_fire", 48, 64)
def th_fire():
    c = Cv(48, 64, 71)
    cx, cy = 24, 58
    stones = []
    for i in range(11):
        ang = i / 11 * 2 * math.pi + 0.3
        stones.append((cx + 19 * math.cos(ang), cy + 5.5 * math.sin(ang), math.sin(ang)))
    rng = np.random.RandomState(72)
    sizes = rng.uniform(0.9, 1.15, 11)
    for (sx, sy, s), k in zip(stones, sizes):
        if s < 0:
            c.sphere(sx, sy - 1, 4.5 * k, 3.2 * k, ramp("#4a4238", "#665c4c", "#82745e", "#9c8c72", "#b4a286"), bias=-0.05)
    # ash bed and two logs
    c.paint(c.ell(24, 56.5, 14, 4), "#3a3028")
    for p0, p1, w in (((9, 58), (36, 52), 4), ((13, 52), (40, 58), 4)):
        lm = c.line([p0, p1], w)
        c.rpaint(lm, 0.4 + 0.3 * (c.y < (p0[1] + p1[1]) / 2 - 0.5), WOOD_DARK)
        c.edge(lm, 0.6)
    # flames: outer red-orange, orange, yellow, pale core
    tongues = [(24, 56, 46, 10, 3, "c"), (15, 56, 28, 6.5, -5, "l"), (33, 56, 32, 7, 5, "r"), (20, 56, 20, 5, -3, "s"), (28, 56, 22, 5, 4, "s2")]
    for scale, col in ((1.0, "#d4502a"), (0.78, "#f08a2c"), (0.52, "#ffc43a"), (0.3, "#fff0a8")):
        for fx, fy, hg, wd, sw, _ in tongues:
            hh = hg * (0.5 + 0.5 * scale)
            flame(c, fx, fy - (1 - scale) * 3, hh, wd * scale, sw * scale, col)
    for (sx, sy) in ((18, 8), (30, 14), (27, 4), (14, 20)):
        c.paint(c.box(sx, sy, sx + 1, sy + 1), "#ffb03a")
    # stones in front
    for (sx, sy, s), k in zip(stones, sizes):
        if s >= 0:
            c.sphere(sx, sy, 4.8 * k, 3.4 * k, ramp("#4a4238", "#665c4c", "#82745e", "#9c8c72", "#b4a286"), bias=0.0)
    c.silhouette_edge(0.7)
    return finish_solid(c)


def anoise(w: int, h: int, sx: float, sy: float, seed: int, octaves: int = 2) -> np.ndarray:
    """Value noise with different feature sizes along x and y (streaks)."""
    rng = np.random.RandomState(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gw = max(2, int(round(w / sx * 2 ** o)) + 1)
        gh = max(2, int(round(h / sy * 2 ** o)) + 1)
        g = rng.rand(gh, gw).astype(np.float32)
        out += np.asarray(Image.fromarray(g).resize((w, h), Image.BILINEAR), np.float32) * amp
        tot += amp
        amp *= 0.5
    return out / tot


def dome(mask: np.ndarray, sigma: float, k: float = 3.0) -> np.ndarray:
    """Rounded-form light 0..1 for any mask (blurred height field lit from the upper left)."""
    hgt = blur(mask.astype(np.float32), sigma)
    gy, gx = np.gradient(hgt)
    nx, ny = -gx * sigma * k, -gy * sigma * k
    n = np.sqrt(nx * nx + ny * ny + 1.0)
    s = (nx * LIGHT[0] + ny * LIGHT[1] + LIGHT[2]) / n
    return np.clip((s + 0.15) / 1.1, 0, 1)


BARK = ramp("#3e3328", "#5a4a3a", "#7a6650", "#9a8468", "#b4a084")
PALM = ramp("#3a5224", "#4e6a2c", "#688638", "#86a448", "#a4c262")
TRUNK = ramp("#5a4636", "#765c44", "#947660", "#b09478", "#c8ae92")
CYP = ramp("#1e3426", "#2a4630", "#3a5c3c", "#4e7448", "#6a8e5c")
REED = ramp("#4a5a2a", "#667a36", "#86963e", "#a6b050", "#c4c870")
SHRUB = ramp("#4e4228", "#6a5c34", "#887848", "#a49462", "#bcad7e")


@sprite("thing_palm", 96, 176)
def th_palm():
    c = Cv(96, 176, 81)
    x, y = c.x, c.y
    rng = np.random.RandomState(82)
    wid = lambda t: 5.8 + 5.5 * max(0.0, 1 - t * 9) ** 2 + 3.2 * (1 - t)
    ys = np.arange(62, 176)
    tt = (175 - ys) / 113.0
    cxs = 46 + 7 * tt + 3 * np.sin(tt * 3.0)
    hws = np.array([wid(t) * 0.5 for t in tt])
    cx_y = np.interp(y[:, 0], ys, cxs)[:, None] * np.ones((1, 96), np.float32)
    hw_y = np.interp(y[:, 0], ys, hws)[:, None] * np.ones((1, 96), np.float32)
    trunk = (np.abs(x - cx_y) <= hw_y) & (y >= 62) & (y <= 175)
    u = np.clip((x - cx_y) / np.maximum(hw_y, 1e-3), -1, 1)
    nz = np.sqrt(1 - u * u)
    lam = u * LIGHT[0] + nz * LIGHT[2]
    ring = np.floor(y / 3.4)
    rfrac = (y / 3.4) % 1.0
    f = 0.42 + 0.5 * lam + 0.06 * (ring % 2) - 0.2 * (rfrac < 0.22) + 0.07 * ((rfrac > 0.22) & (rfrac < 0.5))
    f += (vnoise(96, 176, 3.0, 83, 2) - 0.5) * 0.18
    c.rpaint(trunk, f, TRUNK)
    c.edge(trunk, 0.6)
    C = (51.0, 62.0)
    c.sphere(C[0], C[1] + 1, 6.5, 5.0, TRUNK)
    fronds = [(-140, 30, 26, 0), (140, 30, 26, 0), (-108, 42, 20, 1), (108, 42, 20, 1), (-78, 45, 24, 1), (80, 46, 24, 1), (-48, 44, 14, 2),
              (52, 44, 14, 2), (-20, 38, 8, 2), (24, 38, 9, 2), (4, 30, 4, 2)]
    for th, L, D, layer in fronds:
        a = math.radians(th)
        dr = (math.sin(a), -math.cos(a))
        p1 = (C[0] + dr[0] * L * 0.62, C[1] + dr[1] * L * 0.62 - L * 0.28)
        p2 = (C[0] + dr[0] * L, C[1] + dr[1] * L + D)
        pts = c.bez(C, p1, p2, 28)
        shade = 0.28 + 0.22 * layer
        c.paint(c.taper(pts, 2.2, 1.0), "#7a8a44" if layer > 0 else "#56662e")
        for k in range(3, len(pts) - 1):
            s = k / (len(pts) - 1)
            tx, ty = pts[k + 1][0] - pts[k - 1][0], pts[k + 1][1] - pts[k - 1][1]
            tl = math.hypot(tx, ty) or 1.0
            tx, ty = tx / tl, ty / tl
            px_, py_ = -ty, tx
            ln = (2.5 + 8.5 * (1 - s) ** 0.55 * min(1.0, s * 5.0)) * (0.8 if layer == 0 else 1.0)
            for sd in (1, -1):
                dx = tx * 0.5 + px_ * sd * 0.85
                dy = ty * 0.5 + py_ * sd * 0.85 + 0.55
                nl = math.hypot(dx, dy)
                dx, dy = dx / nl, dy / nl
                e = (pts[k][0] + dx * ln, pts[k][1] + dy * ln)
                fld = shade + 0.35 * (-dy) + rng.uniform(-0.12, 0.12) + 0.1 * (1 - s)
                m = c.line([pts[k], e], 1)
                c.rpaint(m, np.full((176, 96), fld, np.float32), PALM, 0.0)
    c.paint(c.line([(48, 62), (47, 72)], 1), "#6a5028")
    c.paint(c.line([(52, 62), (54, 71)], 1), "#6a5028")
    for dx, dy, col in ((44, 68, "#b8601c"), (47, 72, "#8a4416"), (50, 69, "#d68a2c"), (53, 74, "#b8601c"), (56, 69, "#8a4416"), (46, 77, "#d68a2c"),
                        (51, 78, "#b8601c"), (55, 77, "#d68a2c"), (42, 74, "#8a4416"), (49, 83, "#8a4416")):
        c.paint(c.ell(dx, dy, 1.8, 2.7), col)
        c.paint(c.box(dx - 1, dy - 2, dx, dy - 1), "#e8b050")
    return finish_solid(c)


@sprite("thing_reeds", 64, 80)
def th_reeds():
    c = Cv(64, 80, 91)
    rng = np.random.RandomState(92)
    blades = []
    for i in range(18):
        bx = 32 + rng.uniform(-13, 13)
        h = rng.uniform(26, 62)
        lean = (bx - 32) * rng.uniform(0.5, 1.4) + rng.uniform(-6, 6)
        blades.append((bx, h, lean, rng.rand()))
    blades.sort(key=lambda b: -b[1])
    for bx, h, lean, tone in blades:
        pts = c.bez((bx, 79), (bx + lean * 0.25, 79 - h * 0.6), (bx + lean, 79 - h), 30)
        m = c.taper(pts, 3.0, 0.6)
        c.rpaint(m, 0.25 + 0.5 * tone - 0.28 * ((c.x - bx) > lean * 0.1 + 1.2), REED, 0.6)
    for i, (bx, top, lean) in enumerate(((22, 18, -3), (28, 10, -1), (36, 15, 3), (42, 24, 5), (32, 22, 0))):
        pts = c.bez((bx, 79), (bx + lean * 0.3, 50), (bx + lean, top), 20)
        c.paint(c.line(pts, 1), "#7c8a48")
        hx_, hy_ = bx + lean, top
        head = c.ell(hx_, hy_ + 5, 2.3, 6.2)
        nxs = (c.x - hx_) / 2.3
        c.rpaint(head, 0.55 - 0.4 * nxs + 0.12 * ((c.y + hx_) % 3 < 1), ramp("#3a2214", "#5a361c", "#7a4a26", "#98623a"), 0.5)
        c.paint(c.line([(hx_, hy_ - 2), (hx_, hy_ - 6)], 1), "#8a9650")
    for bx, h, lean in ((24, 22, -8), (40, 26, 9), (31, 18, -2), (36, 14, 4)):
        pts = c.bez((bx, 79), (bx + lean * 0.3, 79 - h * 0.6), (bx + lean, 79 - h), 20)
        c.rpaint(c.taper(pts, 3.2, 0.6), np.full((80, 64), 0.45, np.float32), REED, 0.0)
    c.silhouette_edge(0.72)
    return finish_solid(c)


def boulder(c: Cv, cx, base, w, h, seed, pal=ROCK, bands=5, tilt=0.12, rough=0.14, sig=None):
    rng = np.random.RandomState(seed)
    n = 13
    pts = []
    for i in range(n + 1):
        a = math.pi * (1 - i / n)
        r = 1 + rng.uniform(-rough, rough)
        pts.append((cx + (w / 2) * math.cos(a) * (0.98 + rng.uniform(-rough, rough) * 0.5), base - h * (math.sin(a) ** 0.42) * r))
    pts = [(cx - w / 2 * 1.02, base + 1)] + pts + [(cx + w / 2 * 1.02, base + 1)]
    m = c.poly(pts)
    sg = sig if sig is not None else min(w, h) * 0.2
    lit = dome(m, sg)
    v = c.y + tilt * c.x + (vnoise(c.w, c.h, max(6.0, h / 3), seed + 1, 2) - 0.5) * h * 0.18
    bh = h / bands
    bi = np.floor(v / bh)
    tone = np.random.RandomState(seed + 2).rand(200)[(bi.astype(int) % 200)]
    fr = (v / bh) % 1.0
    f = 0.12 + 0.78 * lit + (tone - 0.5) * 0.22 - 0.17 * (fr < 0.11) + 0.06 * ((fr > 0.11) & (fr < 0.3))
    f += (vnoise(c.w, c.h, 3.0, seed + 3, 2) - 0.5) * 0.18
    c.rpaint(m, f, pal)
    c.paint(m & (np.random.RandomState(seed + 4).rand(c.h, c.w) < 0.025) & (lit > 0.3), pal[0])
    for k in range(2 if w < 80 else 3):
        sx = cx + rng.uniform(-w * 0.25, w * 0.25)
        sy = base - h * rng.uniform(0.35, 0.8)
        cp = [(sx, sy)]
        for j in range(5):
            cp.append((cp[-1][0] + rng.uniform(-3, 3) * w / 60, cp[-1][1] + rng.uniform(2, 5) * h / 50))
        c.paint(c.line(cp, 1) & m, pal[0])
    c.edge(m, 0.6)
    return m


@sprite("thing_rock_a", 64, 48)
def th_rock_a():
    c = Cv(64, 48, 101)
    boulder(c, 32, 47, 58, 42, 101, bands=4)
    return finish_solid(c)


@sprite("thing_rock_b", 96, 72)
def th_rock_b():
    c = Cv(96, 72, 102)
    boulder(c, 52, 70, 80, 62, 102, bands=5)
    boulder(c, 20, 71, 34, 24, 103, bands=3, tilt=-0.1)
    return finish_solid(c)


@sprite("thing_rock_c", 128, 112)
def th_rock_c():
    c = Cv(128, 112, 104)
    boulder(c, 58, 108, 108, 98, 104, bands=7)
    boulder(c, 106, 111, 40, 30, 105, bands=3, tilt=-0.1)
    boulder(c, 14, 111, 22, 12, 106, bands=2)
    return finish_solid(c)


def twig_clouds(c: Cv, clouds, seed, pal=OLIVE_SIL, leaf_light="#d6e0c4", leaf_dark="#46584a"):
    rng = np.random.RandomState(seed)
    for (cx, cy, rx, ry) in clouds:
        m = np.zeros((c.h, c.w), bool)
        for j in range(7):
            ox, oy = rng.uniform(-0.7, 0.7) * rx, rng.uniform(-0.6, 0.5) * ry
            m |= c.ell(cx + ox, cy + oy, rx * rng.uniform(0.35, 0.6), ry * rng.uniform(0.45, 0.75))
        m |= c.ell(cx, cy, rx * 0.78, ry * 0.7)
        lit = dome(m, min(rx, ry) * 0.55)
        f = 0.18 + 0.72 * lit + (vnoise(c.w, c.h, 4.0, int(rng.randint(10000)), 2) - 0.5) * 0.26
        f -= 0.16 * np.clip((c.y - cy) / ry, 0, 1)
        c.rpaint(m, f, pal)
        ys, xs = np.nonzero(m)
        for i in range(int(len(ys) * 0.05) + 12):
            k = rng.randint(len(ys))
            a = math.radians(rng.uniform(-50, 50) + (0 if rng.rand() < 0.5 else 180))
            ln = rng.uniform(2.0, 3.6)
            x0, y0 = float(xs[k]), float(ys[k])
            lm = c.line([(x0, y0), (x0 + math.cos(a) * ln, y0 + math.sin(a) * ln)], 1)
            ff = f[ys[k], xs[k]]
            c.paint(lm, leaf_light if (rng.rand() < 0.35 + 0.5 * ff) else leaf_dark)
        c.edge(m, 0.72)


def gnarl(c: Cv, mask, seed, sigma, twist=0.5, pal=BARK):
    lit = dome(mask, sigma)
    st = np.sin((c.y * 0.42 + c.x * twist) + vnoise(c.w, c.h, 9.0, seed, 2) * 7.0)
    f = 0.1 + 0.8 * lit + st * 0.12 + (vnoise(c.w, c.h, 2.5, seed + 1, 2) - 0.5) * 0.2
    c.rpaint(mask, f, pal)
    c.edge(mask, 0.58)


def olive_tree(c: Cv, s: float, ox: float, seed: int, young: bool = False):
    P = lambda px_, py_: (ox + px_ * s, py_ * s)
    if not young:
        clouds = [(60, 30, 30, 17), (28, 52, 25, 15), (98, 50, 26, 16), (64, 58, 22, 12), (15, 84, 15, 10), (113, 80, 16, 10), (44, 76, 14, 9), (84, 72, 15, 9)]
        left = [(60, 159), (52, 142), (58, 122), (47, 102), (40, 82), (36, 64), (30, 56)]
        right = [(70, 159), (78, 140), (71, 122), (82, 102), (90, 84), (96, 66), (100, 58)]
        branches = [([(47, 102), (30, 94), (16, 86)], 6, 3), ([(82, 102), (100, 94), (113, 84)], 6, 3), ([(40, 82), (50, 70), (60, 58)], 5, 2),
                    ([(90, 84), (80, 72), (66, 60)], 5, 2), ([(36, 64), (48, 44), (60, 34)], 5, 2), ([(96, 66), (84, 48), (66, 34)], 5, 2),
                    ([(40, 82), (38, 72), (30, 62)], 4, 2), ([(90, 84), (92, 70), (98, 58)], 4, 2)]
        w_l, w_r = (26, 9), (24, 8)
    else:
        clouds = [(48, 24, 30, 17), (26, 46, 22, 14), (76, 44, 22, 14), (50, 50, 18, 11), (86, 70, 8, 6)]
        left = [(56, 159), (50, 136), (52, 112), (44, 88), (38, 62), (34, 46)]
        right = [(66, 159), (68, 134), (64, 110), (66, 90), (72, 66), (80, 50)]
        branches = [([(44, 88), (30, 74), (22, 56)], 4, 2), ([(66, 90), (60, 72), (52, 52)], 4, 2), ([(72, 66), (86, 56), (92, 46)], 3, 1.5),
                    ([(38, 62), (44, 46), (50, 30)], 3, 1.5), ([(52, 112), (66, 100), (72, 86)], 3, 1.5)]
        w_l, w_r = (16, 7), (14, 6)
    back = clouds[:max(2, len(clouds) // 2 + 1)]
    front = clouds[len(back):]
    sc = lambda cl: (ox + cl[0] * s, cl[1] * s, cl[2] * s, cl[3] * s)
    twig_clouds(c, [sc(k) for k in back], seed + 1)
    ml = c.taper([P(*p) for p in left], w_l[0] * s, w_l[1] * s)
    mr = c.taper([P(*p) for p in right], w_r[0] * s, w_r[1] * s)
    flare = c.poly([P(40, 159.9), P(50, 148), P(78, 148), P(90, 159.9)])
    hole = c.ell(ox + 64 * s, 130 * s, 4.2 * s, 15 * s)
    gnarl(c, mr, seed + 2, 5 * s, 0.5)
    gnarl(c, ml | flare, seed + 3, 6 * s, 0.4)
    c.paint(hole & (ml | mr | flare), "#2c2218")
    for pts, w0, w1 in branches:
        bm = c.taper([P(*p) for p in pts], w0 * s, max(w1 * s, 1.0))
        c.rpaint(bm, np.full((c.h, c.w), 0.45, np.float32), BARK, 0.0)
    twig_clouds(c, [sc(k) for k in front], seed + 4)


@sprite("thing_olive", 128, 160)
def th_olive():
    c = Cv(128, 160, 111)
    olive_tree(c, 1.0, 0, 111)
    return finish_solid(c)


@sprite("thing_olive_small", 96, 112)
def th_olive_small():
    c = Cv(96, 112, 112)
    olive_tree(c, 0.7, 2, 211, young=True)
    return finish_solid(c)


@sprite("thing_cypress", 56, 144)
def th_cypress():
    c = Cv(56, 144, 121)
    x, y = c.x, c.y
    t = np.clip((y - 3) / 126.0, 0, 1)
    wob = (vnoise(56, 144, 5.0, 122, 2) - 0.5) * 4.0
    hw = 21.5 * (t ** 0.62) * (1 - 0.5 * t ** 5) + wob * np.clip(t * 4, 0, 1)
    cx = 28 + 0.8 * np.sin(y * 0.05)
    foliage = (np.abs(x - cx) <= hw) & (y >= 3) & (y <= 130)
    trunk = c.box(25, 124, 31, 144)
    c.rpaint(trunk, 0.7 - 0.5 * ((x - 25) / 6), BARK)
    u = np.clip((x - cx) / np.maximum(hw, 1), -1, 1)
    lam = u * LIGHT[0] + np.sqrt(1 - u * u) * LIGHT[2]
    strk = anoise(56, 144, 2.6, 9.0, 123, 2)
    f = 0.1 + 0.55 * lam + (strk - 0.5) * 0.55 - 0.12 * np.clip((y - 90) / 40.0, 0, 1)
    f += 0.07 * np.sin(y * 0.7 + x * 0.5)
    c.rpaint(foliage, f, CYP)
    c.edge(foliage, 0.62)
    c.edge(trunk, 0.6)
    return finish_solid(c)


@sprite("thing_bush", 64, 56)
def th_bush():
    c = Cv(64, 56, 131)
    rng = np.random.RandomState(132)
    ends = []
    for i in range(16):
        ang = math.radians(rng.uniform(-64, 64))
        L = rng.uniform(24, 46)
        x0 = 32 + rng.uniform(-6, 6)
        pts = c.bez((x0, 55), (x0 + math.sin(ang) * L * 0.4, 55 - L * 0.55), (x0 + math.sin(ang) * L, 55 - math.cos(ang) * L), 14)
        c.paint(c.taper(pts, 2.4, 0.8), "#6a5438" if i % 2 else "#54402a")
        ends.append(pts)
        if i % 2 == 0:
            q = pts[9]
            tip = (q[0] + rng.uniform(-10, 10), q[1] - rng.uniform(6, 12))
            c.paint(c.line([q, tip], 1), "#6a5438")
    puffs = []
    for pts in ends:
        for idx in (-1, -3, -6):
            q = pts[idx]
            if q[1] > 40:
                continue
            for j in range(2):
                if rng.rand() < 0.35:
                    continue
                puffs.append((q[0] + rng.uniform(-4, 4), q[1] + rng.uniform(-3, 4), rng.uniform(2.4, 4.2), rng.uniform(2.2, 3.4)))
    puffs.sort(key=lambda p: p[1])
    for px_, py_, rx, ry in puffs:
        jit = (vnoise(64, 56, 2.5, int(abs(px_ * 7 + py_) * 10) % 100000, 2) - 0.5) * 0.4
        c.sphere(px_, py_, rx, ry, SHRUB, bias=-0.05 - 0.002 * py_, gain=1.2, jit=jit)
    c.silhouette_edge(0.7)
    return finish_solid(c)


@sprite("thing_grass", 48, 32)
def th_grass():
    c = Cv(48, 32, 141)
    rng = np.random.RandomState(142)
    bl = []
    for i in range(30):
        bx = min(max(24 + rng.normal(0, 8), 6), 42)
        h = rng.uniform(10, 28) * (1 - abs(bx - 24) / 40)
        lean = (bx - 24) * rng.uniform(0.2, 0.9) + rng.uniform(-4, 4)
        bl.append((bx, h, lean, rng.rand()))
    bl.sort(key=lambda b: -b[1])
    pal = ramp("#7a6a38", "#9a8a4a", "#b8a65c", "#d0c078", "#e2d493")
    for bx, h, lean, tone in bl:
        pts = c.bez((bx, 31), (bx + lean * 0.2, 31 - h * 0.6), (bx + lean, 31 - h), 14)
        m = c.taper(pts, 2.6, 0.5)
        c.rpaint(m, 0.15 + 0.7 * tone - 0.2 * ((c.x - bx) > lean * 0.2 + 0.8), pal, 0.5)
    for bx, h, lean in ((18, 12, -5), (30, 14, 6), (24, 9, 1)):
        pts = c.bez((bx, 31), (bx + lean * 0.2, 31 - h * 0.6), (bx + lean, 31 - h), 14)
        c.paint(c.taper(pts, 2.2, 0.5), "#8a9a4a")
    c.paint(c.ell(24, 31, 7, 2), "#6a5a34")
    c.silhouette_edge(0.75)
    return finish_solid(c)


@sprite("thing_flowers", 64, 40)
def th_flowers():
    c = Cv(64, 40, 151)
    rng = np.random.RandomState(152)
    for i in range(26):
        bx = rng.uniform(6, 58)
        h = rng.uniform(7, 17)
        lean = rng.uniform(-6, 6)
        pts = c.bez((bx, 39), (bx + lean * 0.2, 39 - h * 0.6), (bx + lean, 39 - h), 12)
        c.rpaint(c.taper(pts, 2.2, 0.5), np.full((40, 64), 0.25 + 0.6 * rng.rand(), np.float32), REED, 0.0)
    cols = [("#f0ece0", "#e8a830"), ("#f2c842", "#c88a20"), ("#c8402e", "#f2c842"), ("#f0ece0", "#e8a830"), ("#f2c842", "#a86a1c"), ("#d8503a", "#f2d868")]
    for i in range(14):
        bx = min(8 + (i * 4.0) + rng.uniform(-2, 2), 57)
        top = rng.uniform(5, 26)
        lean = rng.uniform(-4, 4)
        pts = c.bez((bx, 39), (bx + lean * 0.3, 39 - (39 - top) * 0.5), (bx + lean, top), 12)
        c.paint(c.line(pts, 1), "#5e7a30")
        hx_, hy_ = int(round(bx + lean)), int(round(top))
        pc, cc = cols[i % len(cols)]
        c.paint(c.box(hx_ - 2, hy_, hx_ + 3, hy_ + 1) | c.box(hx_, hy_ - 2, hx_ + 1, hy_ + 3) | c.box(hx_ - 1, hy_ - 1, hx_ + 2, hy_ + 2), pc)
        c.paint(c.box(hx_, hy_, hx_ + 1, hy_ + 1), cc)
    c.silhouette_edge(0.78)
    return finish_solid(c)


def jag(pts, amp, seed, step=4.0):
    """Densify a polyline and wobble it (rocky outlines)."""
    rng = np.random.RandomState(seed)
    out = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
        for i in range(n):
            t = i / n
            out.append((x0 + (x1 - x0) * t + rng.uniform(-amp, amp) * 0.5, y0 + (y1 - y0) * t + rng.uniform(-amp, amp)))
    out.append(pts[-1])
    return out


def ashlar(c: Cv, mask, y0, pal, form=None, ch=8, bw=18, seed=1, base=0.62, var=0.09, x0=0.0):
    """Dressed stone courses over a mask: staggered blocks, each its own tone, mortar lines, a lit top edge. `form` is an extra 0..1 light field."""
    rng = np.random.RandomState(seed)
    r = np.floor((c.y - y0) / ch).astype(int)
    ry = (c.y - y0) - r * ch
    bwr = rng.choice([bw - 3, bw, bw + 3], 400)
    offr = rng.uniform(0, bw, 400)
    rr = np.clip(r, 0, 399)
    bwv = bwr[rr % 400].astype(np.float32)
    u = (c.x - x0 + offr[rr % 400])
    bi = np.floor(u / bwv).astype(int)
    rx = u - bi * bwv
    tone = rng.rand(400, 64)[rr % 400, bi % 64]
    f = base + (tone - 0.5) * var * 2
    if form is not None:
        f = f + (form - 0.5) * 0.9
    f = f - 0.28 * (ry < 1) - 0.28 * (rx < 1) + 0.07 * ((ry >= 1) & (ry < 2.5)) - 0.06 * (ry > ch - 2)
    f = f + (vnoise(c.w, c.h, 5.0, seed + 5, 2) - 0.5) * 0.16 + (anoise(c.w, c.h, 3.0, 14.0, seed + 6, 2) - 0.5) * 0.14
    c.rpaint(mask, f, pal)


def crenels(c: Cv, x0, x1, ytop, mw, gap, mh, pal, seed, form=None):
    """A battlement row standing on y = ytop (merlons rise to ytop - mh)."""
    xs = x0 + 2
    ms = np.zeros((c.h, c.w), bool)
    while xs + mw <= x1 - 1:
        ms |= c.box(xs, ytop - mh, xs + mw, ytop)
        xs += mw + gap
    f = 0.58 - 0.18 * ((c.x - x0) / max(x1 - x0, 1)) + 0.0 * c.y
    f = f + 0.12 * (c.y < ytop - mh + 2) - 0.1 * (((c.x - x0 - 2) % (mw + gap)) > mw - 2.5)
    c.rpaint(ms, f, pal)
    c.edge(ms, 0.66)
    return ms


@sprite("thing_hill_mount", 256, 96)
def th_hill_mount():
    c = Cv(256, 96, 161)
    x, y = c.x, c.y
    xs = np.arange(256)
    rng = np.random.RandomState(162)
    H = 20 + 38 * np.exp(-(((xs - 138) / 82.0) ** 2)) + 7 * np.sin(xs / 19.0 + 1.0) + 5 * np.sin(xs / 7.3 + 2) + 12 * np.exp(-(((xs - 40) / 36.0) ** 2))
    top = 96 - H
    mask = y >= top[None, :][0][np.clip(x.astype(int), 0, 255)]
    lit = dome(mask, 20.0, 2.2)
    terr = np.sin((y - top[np.clip(x.astype(int), 0, 255)]) * 0.55 + vnoise(256, 96, 10.0, 163, 2) * 8) * 0.07
    f = 0.25 + 0.65 * lit + terr + (vnoise(256, 96, 4.0, 164, 3) - 0.5) * 0.3
    pal = ramp("#667f55", "#7b9164", "#92a672", "#a8b886", "#bccb9a")
    c.rpaint(mask, f, pal)
    # scrub and a few paler dry patches
    dry = mask & (vnoise(256, 96, 9.0, 165, 2) > 0.62)
    c.rpaint(dry, f + 0.05, ramp("#8c8a56", "#a09a62", "#b4ac74", "#c8c088", "#d8d09a"))
    for i in range(90):
        sx = rng.uniform(4, 252)
        sy = rng.uniform(top[int(sx)] + 3, 94)
        c.paint(c.box(sx, sy, sx + rng.choice([2, 3, 3, 4]), sy + 2) & mask, "#4c6640" if rng.rand() < 0.75 else "#5e5a38")
    # tiny sheep
    for sx, sy in ((92, 70), (98, 73), (106, 69), (150, 62), (155, 65), (200, 76), (206, 74), (60, 82)):
        sy = max(sy, top[sx] + 4)
        c.paint(c.box(sx, sy, sx + 3, sy + 2), "#e2ded0")
        c.paint(c.box(sx, sy + 2, sx + 3, sy + 3), "#8c8878")
    # a faint worn path winding up
    for i in range(40):
        t = i / 40
        px_ = 120 + 30 * math.sin(t * 3.0) + t * 6
        py_ = 94 - t * 44
        c.paint(c.box(px_, py_, px_ + 6 - 3 * t, py_ + 1) & mask, "#b2aa7c")
    c.haze(HAZE_BLUE, 0.3, 0.02)
    return finish_solid(c)


@sprite("thing_hill_far", 256, 112)
def th_hill_far():
    c = Cv(256, 112, 171)
    x, y = c.x, c.y
    prof = jag([(0, 112), (30, 88), (58, 62), (63, 40), (70, 25), (110, 23), (150, 25), (183, 24), (190, 42), (196, 62), (226, 90), (255, 106), (255, 112)], 2.2, 172, 6)
    mask = c.poly(prof + [(255, 112), (0, 112)])
    cliff_l = c.poly([(55, 70), (63, 40), (70, 25), (110, 23), (150, 25), (183, 24), (190, 42), (200, 72), (150, 66), (90, 64)]) & mask
    lit = dome(mask, 13.0, 2.6)
    # strata on the cliff band, scree dither below
    v = y + 0.05 * x + (vnoise(256, 112, 14.0, 173, 2) - 0.5) * 8
    band = np.floor(v / 7.0)
    tone = np.random.RandomState(174).rand(80)[band.astype(int) % 80]
    fr = (v / 7.0) % 1.0
    fc = 0.2 + 0.6 * lit + (tone - 0.5) * 0.22 - 0.16 * (fr < 0.12) + 0.06 * ((fr > 0.12) & (fr < 0.3))
    fc += (anoise(256, 112, 2.5, 14.0, 175, 2) - 0.5) * 0.3
    pal = ramp("#74685a", "#8c7f6a", "#a3957a", "#baa98a", "#cebc9a")
    c.rpaint(mask, fc, pal)
    scree = mask & ~cliff_l
    sf = 0.28 + 0.55 * lit + (vnoise(256, 112, 3.0, 176, 3) - 0.5) * 0.5
    c.rpaint(scree, sf, ramp("#7a6e5c", "#948670", "#ab9b80", "#c2b194", "#d6c5a6"))
    rng = np.random.RandomState(177)
    for i in range(240):
        sx, sy = rng.uniform(0, 255), rng.uniform(40, 111)
        c.paint(c.box(sx, sy, sx + rng.choice([1, 2, 2, 3]), sy + 1) & scree, "#675c4c" if rng.rand() < 0.6 else "#d6c8aa")
    # sparse scrub on the lower slope
    for i in range(40):
        sx, sy = rng.uniform(0, 255), rng.uniform(86, 111)
        c.paint(c.box(sx, sy, sx + 3, sy + 2) & scree, "#6a6a3c")
    c.haze(HAZE_BLUE, 0.28, 0.02)
    return finish_solid(c)


def far_block(c: Cv, x0, y0, x1, y1, pal, tone, side=3, rng=None, win=True):
    box = c.box(x0, y0, x1, y1)
    f = 0.58 + tone - 0.22 * ((c.x - x0) / max(x1 - x0, 1)) - 0.12 * ((c.y - y0) / max(y1 - y0, 1))
    c.rpaint(box, f, pal, 0.6)
    if side:
        c.rpaint(c.box(x1 - side, y0, x1, y1), f - 0.3, pal, 0.5)
    c.rpaint(c.box(x0, y0, x1, y0 + 2), f + 0.28, pal, 0.5)
    c.edge(box, 0.7)
    if rng is not None and win:
        nwin = rng.randint(0, 3)
        for k in range(nwin):
            wx = x0 + 3 + k * 6 + rng.randint(0, 2)
            wy = y0 + 4 + rng.randint(0, max(1, int((y1 - y0) / 3)))
            if wx + 2 < x1 - side - 1 and wy + 3 < y1 - 1:
                c.paint(c.box(wx, wy, wx + 2, wy + 3), "#5a4c48")
        if rng.rand() < 0.4:
            dx = x0 + 3 + rng.randint(0, max(1, int(x1 - x0 - 8)))
            c.paint(c.box(dx, y1 - 5, dx + 3, y1), "#4e4038")


def tiny_palm(c: Cv, px_, base, h, seed):
    rng = np.random.RandomState(seed)
    c.paint(c.line([(px_, base), (px_ + 1, base - h)], 2), "#6e5a44")
    top = (px_ + 1, base - h)
    for a in (-80, -45, -10, 25, 55, 85):
        ar = math.radians(a)
        L = rng.uniform(7, 10)
        c.paint(c.taper([top, (top[0] + math.sin(ar) * L * 0.7, top[1] - math.cos(ar) * L * 0.5), (top[0] + math.sin(ar) * L, top[1] - math.cos(ar) * L * 0.2 + 3)], 2.0, 0.8), "#4a6a34" if a % 2 else "#5a7a3c")


@sprite("thing_town_far", 256, 96)
def th_town_far():
    c = Cv(256, 96, 181)
    rng = np.random.RandomState(182)
    pal = STONE_PALE
    ground = 95
    rows = 7
    for k in range(rows):
        yb = 40 + k * 8.5
        half = 126 * math.sqrt(max(0.0, 1 - ((ground - yb) / 62.0) ** 2))
        xs = 128 - half
        xe = 128 + half
        if k == rows - 1:
            xs, xe = 0, 256
        cx = xs + rng.uniform(0, 6)
        while cx < xe - 8:
            w = rng.randint(11, 22)
            h = rng.randint(8, 15)
            w = min(w, int(xe - cx))
            far_block(c, int(cx), int(yb - h), int(cx + w), int(yb + 4 if k < rows - 1 else 96), pal, rng.uniform(-0.07, 0.09), 3 if rng.rand() < 0.6 else 0, rng)
            if rng.rand() < 0.35:
                # a small roof-top stair block or parapet bump
                c.paint(c.box(cx + 2, yb - h - 3, cx + 2 + rng.randint(4, 7), yb - h), "#c9b894")
                c.edge(c.box(cx + 2, yb - h - 3, cx + 8, yb - h), 0.75)
            cx += w - rng.randint(0, 3)
    tiny_palm(c, 46, 86, 24, 183)
    tiny_palm(c, 208, 82, 28, 184)
    c.haze(HAZE_BLUE, 0.27, 0.02)
    return finish_solid(c)


@sprite("thing_city_far", 256, 112)
def th_city_far():
    c = Cv(256, 112, 191)
    rng = np.random.RandomState(192)
    pal = STONE_PALE
    # back terraces of houses behind the wall
    cx = 0
    while cx < 254:
        w = rng.randint(12, 24)
        h = rng.randint(14, 30)
        far_block(c, cx, 76 - h, cx + w, 84, pal, rng.uniform(-0.1, 0.06), 3, rng)
        cx += w - 1
    # two tall slender towers
    for tx, ty, tw in ((38, 34, 12), (104, 30, 13), (232, 38, 12)):
        far_block(c, tx, ty, tx + tw, 84, pal, 0.02, 3, rng, win=False)
        c.paint(c.box(tx + 3, ty + 5, tx + 5, ty + 9), "#5a4c48")
        crenels(c, tx - 1, tx + tw + 1, ty, 3, 2, 3, pal, 5)
    # the temple: podium, colonnade, two stepped roofs, a warm gilded edge
    far_block(c, 118, 66, 226, 86, pal, 0.0, 0, None)
    far_block(c, 126, 36, 218, 66, pal, 0.05, 0, None)
    inner = c.box(131, 42, 213, 66)
    c.rpaint(inner, 0.12 + 0.2 * ((c.y - 42) / 24.0), ramp("#4a3e36", "#665848", "#84725c", "#9e8a70"), 0.5)
    for cxp in range(132, 213, 6):
        c.rpaint(c.box(cxp, 42, cxp + 3, 66), 0.88 - 0.35 * ((c.x - cxp) / 3.0), pal, 0.5)
    far_block(c, 124, 30, 220, 37, pal, 0.1, 0, None)
    far_block(c, 150, 18, 196, 31, pal, 0.06, 0, None)
    c.rpaint(c.box(150, 18, 196, 21), 0.8 + 0.0 * c.x, ramp("#a8803a", "#c49a48", "#dcb668", "#ecd08c", "#f6e4b0"), 0.5)
    for cxp in range(154, 194, 5):
        c.paint(c.box(cxp, 22, cxp + 2, 30), "#d2c2a0")
    # the wall, five square towers and a gate
    wall = c.box(0, 78, 256, 112)
    ashlar(c, wall, 78, pal, None, ch=6, bw=13, seed=193, base=0.58, var=0.07)
    c.mul(wall, 0.96)
    c.edge(c.box(0, 78, 256, 80), 0.72)
    crenels(c, 0, 256, 78, 5, 4, 4, pal, 6)
    for tx in (8, 66, 122, 180, 234):
        tw = 18
        tm = c.box(tx, 56, tx + tw, 112)
        ashlar(c, tm, 56, pal, ((c.x - tx) / tw * -0.35 + 0.78) * 0 + 0.55 - 0.22 * ((c.x - tx) / tw), ch=6, bw=9, seed=tx, base=0.6, var=0.06, x0=tx)
        c.edge(tm, 0.68)
        c.paint(c.box(tx + 7, 66, tx + 9, 73), "#5a4c48")
        crenels(c, tx - 1, tx + tw + 1, 56, 4, 3, 4, pal, tx)
    c.paint(c.poly([(150, 112), (150, 98), (154, 92), (160, 90), (166, 92), (170, 98), (170, 112)]), "#4a3c32")
    c.edge(c.poly([(150, 112), (150, 98), (154, 92), (160, 90), (166, 92), (170, 98), (170, 112)]), 0.7)
    c.haze(HAZE_BLUE, 0.26, 0.02)
    return finish_solid(c)


@sprite("thing_citygate", 256, 192)
def th_citygate():
    c = Cv(256, 192, 201)
    x, y = c.x, c.y
    pal = STONE_PALE
    # silhouette masses
    L = c.box(4, 30, 86, 192)
    R = c.box(170, 30, 252, 192)
    M = c.box(80, 50, 176, 192)
    body = L | R | M
    # lighting form: each mass rounded a little (lit on its left, shaded on its right)
    def form_for(x0, x1):
        u = np.clip((c.x - x0) / (x1 - x0), 0, 1)
        return 0.78 - 0.34 * u
    ashlar(c, L, 30, pal, form_for(4, 86), ch=8, bw=19, seed=202, base=0.6, var=0.08)
    ashlar(c, R, 30, pal, form_for(170, 252), ch=8, bw=19, seed=203, base=0.6, var=0.08)
    ashlar(c, M & ~L & ~R, 50, pal, form_for(80, 176) * 0.0 + 0.62, ch=8, bw=19, seed=204, base=0.6, var=0.08)
    # string courses and corbels under the battlements
    for (x0, x1, yb) in ((4, 86, 30), (170, 252, 30), (86, 170, 50)):
        sh = c.box(x0, yb, x1, yb + 5)
        c.rpaint(sh, 0.18 + 0.1 * ((c.y - yb) / 5.0), pal)
        for kx in range(x0 + 4, x1 - 4, 10):
            c.rpaint(c.box(kx, yb + 5, kx + 5, yb + 9), 0.4 + 0.0 * c.x, pal)
        c.rpaint(c.box(x0, yb + 9, x1, yb + 10), 0.28, pal)
    for (x0, x1) in ((4, 86), (170, 252)):
        crenels(c, x0, x1, 30, 11, 5, 10, pal, x0)
    crenels(c, 86, 170, 50, 11, 5, 9, pal, 7)
    # tower openings: arrow slits and a small arched window
    for tx in (22, 56, 190, 224):
        for sy in (62, 118):
            c.paint(c.box(tx, sy, tx + 3, sy + 14), "#2c2420")
            c.paint(c.box(tx, sy + 12, tx + 3, sy + 14), "#241c18")
            c.paint(c.box(tx - 1, sy - 1, tx + 4, sy), "#a8997a")
    for tx in (36, 206):
        win = c.box(tx, 86, tx + 10, 102) | c.ell(tx + 5, 86, 5, 5)
        c.paint(win, "#33291f")
        c.edge(win, 0.5)
        c.paint(c.box(tx - 1, 102, tx + 11, 104), "#a89878")
    # a projecting string course across the whole face a third of the way down
    for (x0, x1) in ((4, 86), (170, 252)):
        c.rpaint(c.box(x0, 150, x1, 152), 0.9, pal)
        c.rpaint(c.box(x0, 152, x1, 154), 0.22, pal)
    # base plinth (darker, bigger courses)
    plinth = c.box(4, 176, 86, 192) | c.box(170, 176, 252, 192) | c.box(80, 180, 176, 192)
    ashlar(c, plinth, 176, ramp("#7c705a", "#9a8c72", "#b6a888", "#ccbe9c", "#ddd0ae"), None, ch=8, bw=26, seed=205, base=0.5, var=0.08)
    # the arch: dark passage first
    cx, cy, R0 = 128.0, 112.0, 28.0
    opening = ((c.x >= cx - R0) & (c.x < cx + R0) & (c.y >= cy)) | (((c.x - cx) ** 2 + (c.y - cy) ** 2) <= R0 * R0) & (c.y < cy)
    opening &= c.y < 192
    d = np.abs(c.x - cx) / R0
    pf = 0.1 + 0.18 * np.clip(1 - d, 0, 1) ** 1.2 + 0.18 * np.clip((c.y - 120) / 70.0, 0, 1) * (1 - d * 0.6) + (vnoise(256, 192, 6.0, 206, 2) - 0.5) * 0.06
    c.rpaint(opening, pf, ramp("#241a14", "#34261c", "#4a3626", "#624832", "#7a5c3e"), 0.7)
    # a faint lit street far down the passage
    far = c.box(118, 140, 138, 168) | c.ell(128, 140, 10, 8)
    far &= opening
    c.rpaint(far, 0.3 + 0.5 * ((c.y - 140) / 28.0) * 0.0 + 0.12 * (1 - np.abs(c.x - 128) / 10), ramp("#4a3a2a", "#6a5238", "#8c7048", "#a8895a"), 0.6)
    # ground inside the passage: trodden earth
    gnd = opening & (c.y > 172)
    c.rpaint(gnd, 0.35 + 0.35 * ((c.y - 172) / 20.0) + (vnoise(256, 192, 3.0, 207, 2) - 0.5) * 0.2, ramp("#5a4630", "#76603e", "#94784c", "#b09060", "#c8a874"), 0.8)
    # voussoirs (radial stones) and jamb courses around the arch
    ang = np.degrees(np.arctan2(c.y - cy, c.x - cx))  # -180..0 over the top
    dist = np.hypot(c.x - cx, c.y - cy)
    ring = (dist >= R0) & (dist < R0 + 9) & (c.y < cy)
    vi = np.floor((ang + 180) / 12.857).astype(int)
    vt = np.random.RandomState(208).rand(20)[np.clip(vi, 0, 19) % 20]
    vf = ((ang + 180) % 12.857) / 12.857
    f = 0.74 + (vt - 0.5) * 0.14 - 0.3 * ((vf < 0.07) | (vf > 0.93)) + 0.1 * ((dist - R0) < 2) - 0.1 * ((dist - R0) > 7)
    f += 0.18 * ((np.abs(ang + 90) < 6.0) & (dist > R0 + 2))
    c.rpaint(ring, f, pal)
    jam = ((c.x >= cx - R0 - 9) & (c.x < cx - R0) | (c.x >= cx + R0) & (c.x < cx + R0 + 9)) & (c.y >= cy) & (c.y < 192)
    r8 = np.floor((c.y - cy) / 8)
    jt = np.random.RandomState(209).rand(40)[r8.astype(int) % 40]
    jf = 0.7 + (jt - 0.5) * 0.14 - 0.3 * (((c.y - cy) % 8) < 1) + 0.1 * (((c.y - cy) % 8) < 2.5) - 0.18 * (c.x > cx)
    c.rpaint(jam & ~plinth, jf, pal)
    c.edge(opening, 0.4)
    c.edge(ring, 0.7)
    # inner shadow down the right jamb inside the opening
    c.mul(opening & (c.x > cx + R0 - 5), 0.8)
    c.mul(opening & (c.y < cy - R0 + 10) & (c.y < cy), 0.85)
    # open double doors, swung back against the passage sides
    for side in (-1, 1):
        hx0 = cx + side * (R0 - 0.5)
        fx = cx + side * (R0 - 12)
        pts = [(hx0, cy - 4), (fx, cy + 10), (fx, 186), (hx0, 191.5)]
        dm = c.poly(pts) & opening
        u = np.clip(np.abs(c.x - hx0) / 12.0, 0, 1)
        df = 0.6 - 0.28 * u + 0.1 * (((c.x - 1000 * (side < 0)) % 3) < 1) + (vnoise(256, 192, 4.0, 210 + side, 2) - 0.5) * 0.2
        c.rpaint(dm, df, WOOD)
        # iron straps and studs
        for sy in (cy + 18, cy + 50):
            sm = dm & (np.abs(c.y - (sy + (np.abs(c.x - hx0) / 12.0) * 6)) < 2)
            c.paint(sm, "#3a3632")
            c.paint(sm & (((c.x * 2).astype(int)) % 5 == 0) & (c.y < sy + 6), "#6a645c")
        c.edge(dm, 0.55)
    # keystone mark above the arch: a simple stone relief block
    c.rpaint(c.box(cx - 5, cy - R0 - 13, cx + 5, cy - R0 - 3), 0.92, pal)
    c.edge(c.box(cx - 5, cy - R0 - 13, cx + 5, cy - R0 - 3), 0.7)
    c.paint(c.box(cx - 1, cy - R0 - 11, cx + 1, cy - R0 - 5), "#8c7d62")
    # worn rubble at the foot
    for sx, sy, rx, ry in ((12, 190, 6, 3), (30, 191, 4, 2), (72, 191, 5, 2), (176, 191, 5, 2), (232, 190, 6, 3), (246, 191, 4, 2)):
        c.sphere(sx, sy, rx, ry, ROCK, mask=y < 192)
    c.silhouette_edge(0.62)
    return finish_solid(c)


PLASTER = ramp("#a8793f", "#c3955a", "#d8b072", "#e6c890", "#f0d8a8")
CROSSW = ramp("#2c1e14", "#43301f", "#5a4128", "#73533a", "#8a6848")
PALE_ROCK = ramp("#9c9078", "#b8ab8e", "#d0c4a4", "#e2d8b8", "#f0e8cc")
TERRA = ramp("#7a3c24", "#9c5030", "#bc6a40", "#d4865a", "#e4a27a")
BLUE_SHUT = ramp("#34506c", "#46688a", "#5c82a6", "#7898ba", "#94b0cc")


def plaster_patch(c: Cv, mask, pts, seed, wall_mask=None):
    """A patch of ochre plaster with a chipped edge over a masonry wall (pts = rough outline)."""
    rng = np.random.RandomState(seed)
    m = c.poly(jag(pts + [pts[0]], 3.0, seed, 4)) & mask
    f = 0.55 + (vnoise(c.w, c.h, 7.0, seed + 1, 3) - 0.5) * 0.6 + 0.12 * (1 - (c.x - c.x[0, 0]) / c.w)
    c.rpaint(m, f, PLASTER)
    # exposed stone showing through
    holes = m & (vnoise(c.w, c.h, 5.0, seed + 2, 2) > 0.7) & erode(erode(m))
    c.rpaint(holes, 0.45 + (vnoise(c.w, c.h, 2.0, seed + 3, 2) - 0.5) * 0.4, STONE)
    # thickness: lit on the top-left rim, a shadow below-right
    rim = m & ~erode(m)
    c.mul(rim, 0.7)
    sh = dilate(m) & ~m & dilate(np.roll(np.roll(m, 1, 0), 1, 1))
    c.mul(sh & wall_mask if wall_mask is not None else sh, 0.78)
    return m


@sprite("thing_house_a", 128, 128)
def th_house_a():
    c = Cv(128, 128, 301)
    x, y = c.x, c.y
    body = c.box(10, 30, 118, 128)
    ashlar(c, body, 30, STONE_PALE, 0.62 - 0.14 * ((c.x - 10) / 108.0), ch=7, bw=15, seed=302, base=0.6, var=0.1, x0=10)
    plaster_patch(c, body, [(12, 34), (58, 32), (66, 52), (48, 74), (20, 70), (12, 56)], 303, body)
    plaster_patch(c, body, [(80, 92), (118, 88), (118, 128), (94, 128), (84, 114)], 304, body)
    plaster_patch(c, body, [(62, 62), (80, 60), (84, 76), (66, 80)], 305, body)
    # parapet and roof edge, drain spout
    par = c.box(6, 20, 122, 33)
    ashlar(c, par, 20, STONE_PALE, 0.7 - 0.0 * c.x, ch=6, bw=17, seed=306, base=0.62, var=0.07)
    c.rpaint(c.box(6, 20, 122, 23), 0.95, STONE_PALE)
    c.mul(c.box(10, 33, 118, 38), 1 - 0.3 * np.clip(1 - (c.y - 33) / 5.0, 0, 1))
    c.edge(par, 0.62)
    c.paint(c.box(94, 29, 100, 35), "#5a4a3a")
    c.paint(c.box(94, 29, 100, 31), "#8a7860")
    # door: stone lintel, jambs, dark plank door, ring
    c.rpaint(c.box(43, 74, 79, 82), 0.85 - 0.3 * ((c.y - 74) / 8.0), STONE_PALE)
    c.edge(c.box(43, 74, 79, 82), 0.62)
    door = c.box(48, 82, 74, 128)
    df = 0.5 - 0.3 * ((c.x - 48) / 26.0) + 0.14 * (((c.x - 48) % 6.5) < 1) * -1 + (anoise(128, 128, 1.5, 12.0, 307, 2) - 0.5) * 0.3
    c.rpaint(door, df, WOOD_DARK)
    c.paint(c.box(48, 100, 74, 102), "#2c2420")
    c.paint(c.box(48, 116, 74, 118), "#2c2420")
    c.paint(c.ell(65, 108, 2.6, 2.6) & ~c.ell(65, 108, 1.4, 1.4), "#8a8478")
    c.paint(c.box(64, 105, 66, 106), "#b0a898")
    c.edge(door, 0.5)
    c.mul(door & (c.y < 88), 0.8)
    c.rpaint(c.box(43, 82, 48, 128) | c.box(74, 82, 79, 128), 0.78 - 0.25 * ((c.x > 60)), STONE_PALE)
    c.rpaint(c.box(42, 124, 80, 128), 0.72, STONE_PALE)
    c.edge(c.box(42, 124, 80, 128), 0.62)
    # window: dark opening, cobalt-faded shutters, sill
    c.paint(c.box(86, 50, 108, 78), "#2a211c")
    for x0 in (86, 97):
        sh = c.box(x0, 50, x0 + 11, 78)
        lf = 0.56 - 0.3 * ((c.x - x0) / 11.0) + 0.16 * (((c.y - 50) % 4) < 1.3) * -1 + 0.1 * (((c.y - 50) % 4) > 2.5)
        c.rpaint(sh, lf, BLUE_SHUT)
        c.paint(c.box(x0, 63, x0 + 11, 65), "#3a5470")
        c.edge(sh, 0.6)
    c.paint(c.box(97, 50, 98, 78), "#241c18")
    c.paint(c.box(95, 55, 97, 57), "#2a211c")  # the leaf stands a little ajar
    c.rpaint(c.box(83, 78, 111, 82), 0.9 - 0.3 * ((c.y - 78) / 4.0), STONE_PALE)
    c.rpaint(c.box(84, 46, 110, 50), 0.85, STONE_PALE)
    c.edge(c.box(83, 78, 111, 82), 0.62)
    c.edge(c.box(84, 46, 110, 50), 0.62)
    # a terracotta jar by the door
    jar = c.ell(28, 117, 7.5, 9.5) | c.box(24, 106, 33, 109)
    nxj = (c.x - 28) / 7.5
    c.rpaint(jar, 0.64 - 0.45 * nxj + 0.1 * (c.y < 112), TERRA)
    c.paint(c.box(25, 104, 32, 107), "#9c5030")
    c.paint(c.box(26, 105, 31, 106), "#2a1c16")
    c.paint(c.box(20, 114, 36, 115), "#7a3c24")
    c.edge(jar, 0.6)
    c.silhouette_edge(0.66)
    return finish_solid(c)


@sprite("thing_house_b", 128, 112)
def th_house_b():
    c = Cv(128, 112, 311)
    x, y = c.x, c.y
    body = c.box(6, 36, 88, 112)
    ashlar(c, body, 36, STONE_PALE, 0.64 - 0.12 * ((c.x - 6) / 82.0), ch=7, bw=14, seed=312, base=0.6, var=0.1, x0=6)
    plaster_patch(c, body, [(8, 62), (30, 58), (36, 74), (26, 100), (8, 96)], 313, body)
    plaster_patch(c, body, [(64, 92), (88, 90), (88, 112), (70, 112)], 314, body)
    # outside stair: a solid stepped mass climbing to the roof
    steps = 10
    pts = [(124, 112), (124, 105)]
    for i in range(steps):
        xr = 124 - i * 3.6
        yt = 105 - i * 7.2
        pts += [(xr, yt), (xr - 3.6, yt)]
        if i < steps - 1:
            pts.append((xr - 3.6, yt - 7.2))
    pts = [(124, 112), (124, 105)]
    for i in range(steps):
        xr = 124 - i * 3.5
        yt = 105 - i * 7.2
        pts += [(xr, yt), (xr - 3.5, yt)]
        pts += [(xr - 3.5, yt - 7.2)]
    pts = pts[:-1] + [(88, 112)]
    stair = c.poly(pts)
    # tread / riser shading
    tr = (c.x - 88) / 36.0
    stepy = np.floor((105.0 - c.y + 7.2) / 7.2)
    sf = 0.6 - 0.16 * tr + (vnoise(128, 112, 4.0, 315, 2) - 0.5) * 0.16
    top_edge = stair & ~np.roll(stair, -1, 0)  # tread: pixels whose upper neighbour is empty
    tread = stair & (~np.roll(stair, 1, 0) | ~np.roll(stair, 2, 0))
    ashlar(c, stair, 36, STONE_PALE, 0.5 - 0.1 * tr + 0.0 * c.y, ch=7, bw=11, seed=319, base=0.55, var=0.08, x0=88)
    c.rpaint(tread, sf + 0.3, STONE_PALE)
    c.mul(stair & (c.x < 91), 0.7)
    c.rpaint(c.box(121, 105, 125, 112), 0.3, STONE_PALE)
    c.edge(stair, 0.62)
    # roof edge
    par = c.box(2, 28, 92, 38)
    ashlar(c, par, 28, STONE_PALE, 0.7 - 0.0 * c.x, ch=5, bw=17, seed=316, base=0.62, var=0.07)
    c.rpaint(c.box(2, 28, 92, 31), 0.95, STONE_PALE)
    c.mul(c.box(6, 38, 88, 43), 1 - 0.3 * np.clip(1 - (c.y - 38) / 5.0, 0, 1))
    c.edge(par, 0.62)
    # arched door
    door = c.box(30, 78, 52, 112) | c.ell(41, 78, 11, 9)
    df = 0.55 - 0.3 * ((c.x - 30) / 22.0) + 0.14 * (((c.x - 30) % 5.5) < 1) * -1 + (anoise(128, 112, 1.5, 12.0, 317, 2) - 0.5) * 0.3
    c.rpaint(door, df, WOOD)
    c.paint(door & (np.abs(c.y - 92) < 1.2), "#2c2420")
    c.paint(door & (np.abs(c.y - 104) < 1.2), "#2c2420")
    c.paint(c.ell(46, 98, 2.0, 2.0) & ~c.ell(46, 98, 1.0, 1.0), "#8a8478")
    c.edge(door, 0.5)
    arch = (c.ell(41, 78, 15, 13) & ~c.ell(41, 78, 11, 9) & (c.y <= 78)) | (c.box(26, 78, 30, 112) | c.box(52, 78, 56, 112))
    c.rpaint(arch, 0.82 - 0.25 * (c.x > 41), STONE_PALE)
    c.edge(arch, 0.62)
    c.rpaint(c.box(25, 109, 57, 112), 0.7, STONE_PALE)
    # windows
    c.paint(c.box(12, 52, 24, 66), "#2a211c")
    c.rpaint(c.box(12, 52, 18, 66), 0.56 - 0.3 * ((c.x - 12) / 6.0) + 0.1 * (((c.y - 52) % 3) < 1) * -1, BLUE_SHUT)
    c.edge(c.box(12, 52, 18, 66), 0.6)
    c.rpaint(c.box(10, 66, 26, 69), 0.85, STONE_PALE)
    c.rpaint(c.box(10, 49, 26, 52), 0.85, STONE_PALE)
    c.paint(c.box(66, 50, 78, 64), "#2a211c")
    for bx in (68, 72, 76):
        c.paint(c.box(bx, 50, bx + 1, 64), "#6a4a2c")
    c.rpaint(c.box(64, 64, 80, 67), 0.85, STONE_PALE)
    c.rpaint(c.box(64, 47, 80, 50), 0.85, STONE_PALE)
    for b in (c.box(10, 66, 26, 69), c.box(10, 49, 26, 52), c.box(64, 64, 80, 67), c.box(64, 47, 80, 50)):
        c.edge(b, 0.62)
    # bracket and hanging basket
    c.paint(c.line([(60, 72), (74, 72)], 1), "#3a3430")
    c.paint(c.line([(60, 72), (60, 78)], 1), "#3a3430")
    c.paint(c.line([(74, 72), (68, 83)], 1), "#5a5248")
    c.paint(c.line([(74, 72), (80, 83)], 1), "#5a5248")
    bas = c.ell(74, 85, 8.5, 5.5) & (c.y >= 83)
    c.rpaint(bas, 0.6 - 0.35 * ((c.x - 74) / 8.5) - 0.18 * (((c.x + c.y) % 3) < 1), ramp("#5a4020", "#7e5a30", "#a07c46", "#bc9a60"), 0.6)
    c.edge(bas, 0.6)
    rng = np.random.RandomState(318)
    for px_, py_, rx, ry in ((68, 82, 4, 3.4), (74, 80, 4.5, 3.8), (80, 82, 4, 3.4), (71, 79, 3, 2.6), (78, 79, 3, 2.6)):
        c.sphere(px_, py_, rx, ry, ramp("#3e5a26", "#56762e", "#729440", "#90b254", "#aecb70"))
    for k in range(7):
        sx = 66 + k * 2.4
        c.paint(c.line([(sx, 87), (sx + rng.uniform(-1, 1), 87 + rng.uniform(5, 12))], 1), "#648a36")
    for fx, fy, col in ((68, 78, "#d8503a"), (72, 76, "#f0ece0"), (77, 77, "#d8503a"), (81, 80, "#f2c842"), (70, 81, "#f2c842"), (75, 80, "#d8503a")):
        c.paint(c.box(fx, fy, fx + 2, fy + 2), col)
    c.silhouette_edge(0.66)
    return finish_solid(c)


def column(c: Cv, cx, ytop, ybot, hw_bot, hw_top, cap_h, base_h, cap_ext, seed, flutes=9, pal=STONE_PALE):
    """A fluted limestone column drawn over [ytop, ybot]: abacus + echinus capital, tapering shaft with flutes, torus base and plinth."""
    sy0, sy1 = ytop + cap_h, ybot - base_h
    t = np.clip((c.y - sy0) / max(sy1 - sy0, 1), 0, 1)
    hw = hw_top + (hw_bot - hw_top) * t + 0.9 * np.sin(t * math.pi)
    shaft = (np.abs(c.x - cx) <= hw) & (c.y >= sy0) & (c.y < sy1)
    u = np.clip((c.x - cx) / np.maximum(hw, 1e-3), -1, 1)
    th = np.arcsin(u)
    lam = u * LIGHT[0] + np.sqrt(1 - u * u) * LIGHT[2]
    fl = np.sin(th * flutes * 1.0 * 2.0 + 0.0)
    f = 0.38 + 0.52 * lam + 0.06 * fl - 0.13 * (np.abs(fl) > 0.93)
    drum = (c.y - sy0) % (max(sy1 - sy0, 1) / 4.0)
    f = f - 0.12 * (drum < 1)
    f = f + (vnoise(c.w, c.h, 5.0, seed, 2) - 0.5) * 0.14 + (anoise(c.w, c.h, 2.0, 18.0, seed + 1, 2) - 0.5) * 0.1
    c.rpaint(shaft, f, pal)
    c.edge(shaft, 0.64)
    # capital: neck, echinus, abacus
    ec_top, ec_bot = ytop + 6, sy0 - 3
    ecm = c.poly([(cx - cap_ext, ec_top), (cx + cap_ext, ec_top), (cx + hw_top + 1.5, ec_bot), (cx - hw_top - 1.5, ec_bot)])
    ef = 0.62 - 0.4 * ((c.x - cx) / cap_ext) + 0.0 * c.y - 0.1 * ((c.y - ec_top) / max(ec_bot - ec_top, 1))
    c.rpaint(ecm, ef, pal)
    c.edge(ecm, 0.64)
    c.rpaint(c.box(cx - hw_top - 1, ec_bot, cx + hw_top + 2, sy0), 0.34 - 0.0 * c.x, pal)
    ab = c.box(cx - cap_ext - 2, ytop, cx + cap_ext + 2, ytop + 6)
    c.rpaint(ab, 0.86 - 0.35 * ((c.y - ytop) / 6.0) - 0.15 * ((c.x - cx) / (cap_ext + 2)), pal)
    c.edge(ab, 0.62)
    c.mul(c.box(cx - cap_ext, ytop + 6, cx + cap_ext + 1, ytop + 9), 0.8)
    # base: torus on a plinth
    tor = c.ell(cx, sy1 + base_h * 0.38, hw_bot + 3.2, base_h * 0.34) & (c.y < sy1 + base_h * 0.7)
    c.rpaint(tor, 0.78 - 0.5 * ((c.y - (sy1 + base_h * 0.05)) / (base_h * 0.6)) - 0.15 * ((c.x - cx) / (hw_bot + 3)), pal)
    c.edge(tor, 0.62)
    pl = c.box(cx - hw_bot - 5, ybot - base_h * 0.34, cx + hw_bot + 5, ybot)
    c.rpaint(pl, 0.78 - 0.22 * ((c.x - cx) / (hw_bot + 5)) - 0.12 * ((c.y - (ybot - base_h * 0.34)) / (base_h * 0.34)), pal)
    c.edge(pl, 0.62)
    c.mul(c.box(cx - hw_bot - 3, sy1, cx + hw_bot + 4, sy1 + 2), 0.78)


@sprite("thing_pillar", 48, 192)
def th_pillar():
    c = Cv(48, 192, 321)
    column(c, 24, 3, 191, 11.5, 9.8, 26, 20, 13.5, 322)
    # weathering: a stain and a fine crack
    c.mul(c.box(14, 60, 34, 192) & (vnoise(48, 192, 14.0, 323, 2) > 0.62), 0.9)
    c.paint(c.line([(27, 96), (26, 102), (28, 108), (27, 113)], 1) & c.box(15, 90, 33, 120) & (c.a >= 0.5), "#7a6c52")
    return finish_solid(c)


@sprite("thing_temple_front", 256, 160)
def th_temple_front():
    c = Cv(256, 160, 331)
    x, y = c.x, c.y
    # shadowed interior: dressed back wall, dim and warm, with a deep doorway
    inner = c.box(6, 40, 250, 144)
    ff = 0.3 + 0.34 * np.clip((y - 40) / 100.0, 0, 1) + (vnoise(256, 160, 6.0, 332, 2) - 0.5) * 0.12
    ashlar(c, inner, 40, ramp("#3e342c", "#54483a", "#6c5c48", "#867458", "#9e8a6c"), ff, ch=9, bw=21, seed=333, base=0.55, var=0.06)
    door = c.box(112, 72, 144, 144)
    c.rpaint(door, 0.12 + 0.1 * (1 - np.abs(c.x - 128) / 16.0), ramp("#241c18", "#342820", "#463628", "#5a4632"), 0.5)
    c.rpaint(c.box(106, 66, 150, 72), 0.55, ramp("#5a4c3c", "#76644e", "#917c60", "#aa9374"))
    c.edge(c.box(106, 66, 150, 72), 0.6)
    for nx in (44, 188):
        c.paint(c.box(nx, 84, nx + 20, 124), "#3a2e26")
        c.edge(c.box(nx, 84, nx + 20, 124), 0.55)
    # floor (polished slabs) in shadow
    fl = c.box(6, 136, 250, 146)
    c.rpaint(fl, 0.25 + 0.3 * ((c.y - 136) / 10.0), ramp("#4a3e32", "#645644", "#7e6c54", "#9a8668"), 0.5)
    # columns (six)
    for i in range(6):
        column(c, 26 + i * 40.8, 38, 144, 9.0, 7.6, 16, 13, 10.5, 340 + i, flutes=7)
    # entablature: architrave, frieze with groove marks, cornice
    arch = c.box(2, 26, 254, 38)
    c.rpaint(arch, 0.8 - 0.35 * ((c.y - 26) / 12.0) + (vnoise(256, 160, 6.0, 334, 2) - 0.5) * 0.1, STONE_PALE)
    c.rpaint(c.box(2, 36, 254, 38), 0.2, STONE_PALE)
    c.edge(arch, 0.62)
    fr = c.box(2, 14, 254, 26)
    c.rpaint(fr, 0.74 - 0.0 * c.x + (vnoise(256, 160, 5.0, 335, 2) - 0.5) * 0.1, STONE_PALE)
    for gx in range(8, 254, 12):
        c.rpaint(c.box(gx, 15, gx + 2, 25), 0.3, STONE_PALE)
        c.rpaint(c.box(gx + 3, 15, gx + 4, 25), 0.9, STONE_PALE)
    c.edge(fr, 0.62)
    corn = c.box(0, 6, 256, 14)
    c.rpaint(corn, 0.92 - 0.45 * ((c.y - 6) / 8.0), STONE_PALE)
    c.rpaint(c.box(0, 12, 256, 16), 0.24, STONE_PALE)
    c.edge(c.box(0, 6, 256, 16), 0.62)
    c.mul(c.box(8, 38, 248, 46), 1 - 0.4 * np.clip(1 - (c.y - 38) / 8.0, 0, 1))
    # steps of the stylobate
    for k, (x0, x1, y0, y1) in enumerate(((8, 248, 144, 149), (4, 252, 149, 154), (0, 256, 154, 160))):
        st = c.box(x0, y0, x1, y1)
        c.rpaint(st, 0.8 - 0.0 * c.x + (vnoise(256, 160, 6.0, 336 + k, 2) - 0.5) * 0.12, STONE_PALE)
        c.rpaint(c.box(x0, y0, x1, y0 + 2), 0.98, STONE_PALE)
        c.rpaint(c.box(x0, y1 - 2, x1, y1), 0.3, STONE_PALE)
        c.edge(st, 0.64)
    c.silhouette_edge(0.62)
    return finish_solid(c)


@sprite("thing_stairs", 160, 96)
def th_stairs():
    c = Cv(160, 96, 351)
    x, y = c.x, c.y
    ytop, ybot = 14, 96
    le = lambda yy: 32 - (yy - ytop) / (ybot - ytop) * 18
    re = lambda yy: 128 + (yy - ytop) / (ybot - ytop) * 18
    # cheek walls (sloped sides), drawn first
    for side in (-1, 1):
        if side < 0:
            pts = [(16, 3), (34, 3), (34, ytop), (14, 96), (0, 96)]
        else:
            pts = [(144, 3), (126, 3), (126, ytop), (146, 96), (160, 96)]
        cm = c.poly(pts)
        ashlar(c, cm, 3, STONE_PALE, 0.6 - 0.1 * side * ((c.x - 80) / 80.0), ch=7, bw=12, seed=352 + side, base=0.58, var=0.08)
        c.edge(cm, 0.62)
        cap = c.poly([(pts[0][0], 3), (pts[1][0], 3), (pts[1][0], 7), (pts[0][0] + 0, 8)])
        c.rpaint(cap, 0.95, STONE_PALE)
    # the flight: treads and risers
    nsteps = 9
    sh = (ybot - ytop) / nsteps
    for i in range(nsteps):
        y0 = ytop + i * sh
        y1 = y0 + sh
        m = (c.y >= y0) & (c.y < y1) & (c.x >= le(c.y)) & (c.x < re(c.y))
        ry = c.y - y0
        riser = ry >= 3.2
        f = np.where(riser, 0.4 - 0.14 * ((ry - 3.2) / max(sh - 3.2, 1)), 0.94)
        f = f + (vnoise(160, 96, 5.0, 353 + i, 2) - 0.5) * 0.14 - 0.07 * np.exp(-((c.x - 80) / 24.0) ** 2)
        f = f - 0.28 * (ry < 0.9)
        f = f + 0.0 * c.x
        c.rpaint(m, f, STONE_PALE)
    # the portico threshold at the top: floor slab and a dark door sill
    land = c.box(34, 3, 126, ytop)
    c.rpaint(land, 0.82 - 0.2 * ((c.y - 3) / (ytop - 3)) + (vnoise(160, 96, 6.0, 360, 2) - 0.5) * 0.1, STONE_PALE)
    c.paint(c.box(34, 3, 126, 5), "#4a4034")
    c.rpaint(c.box(34, 5, 126, 7), 0.4, STONE_PALE)
    for px_ in (34, 116):
        pm = c.box(px_, 0, px_ + 10, 7)
        c.rpaint(pm, 0.7 - 0.0 * c.x, STONE_PALE)
        c.edge(pm, 0.62)
    c.silhouette_edge(0.64)
    return finish_solid(c)


@sprite("thing_tomb", 192, 144)
def th_tomb():
    c = Cv(192, 144, 361)
    x, y = c.x, c.y
    prof = jag([(0, 144), (0, 76), (14, 60), (32, 42), (64, 30), (100, 24), (138, 30), (166, 40), (184, 58), (192, 78), (192, 144)], 3.0, 362, 5)
    rock = c.poly(prof)
    lit = dome(rock, 18.0, 2.4)
    v = y + 0.1 * x + (vnoise(192, 144, 16.0, 363, 2) - 0.5) * 10
    band = np.floor(v / 9.0)
    tone = np.random.RandomState(364).rand(60)[band.astype(int) % 60]
    fr = (v / 9.0) % 1.0
    f = 0.25 + 0.6 * lit + (tone - 0.5) * 0.2 - 0.15 * (fr < 0.1) + 0.06 * ((fr > 0.1) & (fr < 0.3))
    f += (anoise(192, 144, 3.0, 10.0, 365, 2) - 0.5) * 0.2 + (vnoise(192, 144, 3.0, 366, 2) - 0.5) * 0.12
    c.rpaint(rock, f, PALE_ROCK)
    c.edge(rock, 0.66)
    rng = np.random.RandomState(367)
    for k in range(4):
        sx, sy = rng.uniform(20, 170), rng.uniform(40, 100)
        cp = [(sx, sy)]
        for j in range(6):
            cp.append((cp[-1][0] + rng.uniform(-3, 3), cp[-1][1] + rng.uniform(2, 6)))
        c.paint(c.line(cp, 1) & rock, "#8a7c62")
    # dressed square face around the doorway
    face = c.box(52, 50, 140, 130)
    ff = 0.72 - 0.2 * ((c.x - 52) / 88.0) + (anoise(192, 144, 2.0, 8.0, 368, 2) - 0.5) * 0.2 - 0.18 * (((c.y - 50) % 10) < 1)
    c.rpaint(face, ff, PALE_ROCK)
    c.edge(face, 0.7)
    # lintel slab, the opening, its reveals
    lint = c.box(68, 54, 124, 64)
    c.rpaint(lint, 0.92 - 0.4 * ((c.y - 54) / 10.0), PALE_ROCK)
    c.edge(lint, 0.62)
    op = c.box(74, 64, 118, 126)
    c.rpaint(op, 0.1 + 0.12 * ((c.y - 64) / 62.0) + 0.06 * (1 - np.abs(c.x - 96) / 22.0), ramp("#241c1a", "#342824", "#46362e", "#5a463a"), 0.5)
    c.rpaint(c.box(74, 64, 78, 126), 0.72, PALE_ROCK)
    c.rpaint(c.box(114, 64, 118, 126), 0.34, PALE_ROCK)
    c.mul(c.box(78, 64, 114, 72), 0.8)
    c.edge(op, 0.45)
    # ground in front with the worn groove channel
    gnd = c.box(0, 124, 192, 144)
    gf = 0.45 + 0.35 * ((y - 124) / 20.0) + (vnoise(192, 144, 4.0, 369, 3) - 0.5) * 0.35
    c.rpaint(gnd, gf, ramp("#7a6a50", "#968462", "#b0a07a", "#c8b894", "#dccdaa"))
    for k in range(70):
        sx, sy = rng.uniform(0, 190), rng.uniform(126, 143)
        c.paint(c.box(sx, sy, sx + rng.choice([1, 2, 3]), sy + 1), "#7a6a50" if rng.rand() < 0.5 else "#d8c9a6")
    ch = c.box(34, 129, 158, 139) | c.ell(34, 134, 5, 5) | c.ell(158, 134, 5, 5)
    cf = 0.3 + 0.28 * ((y - 129) / 10.0) + 0.1 * np.exp(-((y - 135) / 2.2) ** 2) + (vnoise(192, 144, 5.0, 370, 2) - 0.5) * 0.15
    c.rpaint(ch, cf, ramp("#4a3e2e", "#665842", "#84735a", "#a08c70", "#bca98a"))
    c.mul(ch & (y < 133), 0.62)
    lip = c.box(34, 139, 158, 142)
    c.rpaint(lip, 0.92 - 0.2 * ((c.y - 139) / 3.0), PALE_ROCK)
    c.edge(ch, 0.58)
    # dry shrubs at the foot of the rock
    for bx, by, sc in ((20, 140, 1.0), (172, 138, 1.1), (148, 142, 0.7)):
        for (dx, dy, rx, ry) in ((0, 0, 9, 6), (-8, 3, 6, 4.5), (8, 2, 6.5, 5), (-2, -6, 6, 5), (5, -5, 5, 4)):
            jit = (vnoise(192, 144, 2.5, int(bx * 3 + dx * 7 + 200) % 9999, 2) - 0.5) * 0.4
            c.sphere(bx + dx * sc, by + dy * sc - 3 * sc, rx * sc, ry * sc, ramp("#4a5a2e", "#667a3a", "#84984a", "#a0b25e", "#bccb7c"), bias=-0.04, gain=1.2, jit=jit)
    c.silhouette_edge(0.64)
    return finish_solid(c)


@sprite("thing_stone_closed", 96, 96)
def th_stone_closed():
    c = Cv(96, 96, 371)
    x, y = c.x, c.y
    cx, cy, R = 48.0, 46.0, 42.0
    dx, dy = (x - cx), (y - cy)
    r = np.hypot(dx, dy) / R
    disc = r <= 1.0
    # chips knocked from the rim
    for ang, rr in ((200, 5.0), (320, 3.5), (45, 3.0)):
        a = math.radians(ang)
        disc &= ~c.ell(cx + math.cos(a) * R, cy + math.sin(a) * R, rr, rr * 0.8)
    ang = np.arctan2(dy, dx)
    bevel = r > 0.86
    lit_rim = 0.5 + 0.38 * np.cos(ang - math.radians(-135))
    face = 0.66 + 0.12 * (-(dx + dy) / (R * 1.4)) + (vnoise(96, 96, 5.0, 372, 3) - 0.5) * 0.2
    # dressing marks: faint radial grooves from the hub and a couple of rings
    rad = 0.5 + 0.5 * np.cos(ang * 18.0 + r * 3.0)
    face = face - 0.07 * (rad > 0.9) * ((r > 0.18) & (r < 0.84))
    face = face - 0.1 * (np.abs(r - 0.52) < 0.012) - 0.08 * (np.abs(r - 0.7) < 0.012)
    f = np.where(bevel, lit_rim, face)
    f = f - 0.18 * ((r > 0.84) & (r < 0.87))
    hub = r < 0.17
    f = np.where(hub, 0.4 - 0.3 * (r < 0.08) + 0.1 * (-(dx + dy) / 10.0) * (r < 0.17), f)
    c.rpaint(disc, f, GREY_STONE)
    c.paint(disc & (r < 0.075), "#3a3836")
    c.edge(disc, 0.6)
    # the groove it stands in: a stone trough with a worn lip
    trough = c.box(2, 83, 94, 96)
    c.rpaint(trough, 0.84 - 0.55 * np.clip((y - 83) / 13.0, 0, 1) ** 0.8 + (vnoise(96, 96, 4.0, 373, 2) - 0.5) * 0.12, PALE_ROCK)
    c.rpaint(c.box(2, 83, 94, 86), 0.97, PALE_ROCK)
    c.paint(c.box(2, 88, 94, 89), "#7a6c52")
    c.edge(trough, 0.62)
    c.paint(c.box(6, 90, 8, 93), "#8a7c62")
    c.paint(c.box(40, 91, 44, 92), "#8a7c62")
    c.paint(c.box(78, 90, 82, 92), "#8a7c62")
    c.silhouette_edge(0.62)
    return finish_solid(c)


@sprite("thing_stone_rolled", 96, 72)
def th_stone_rolled():
    c = Cv(96, 72, 381)
    x, y = c.x, c.y
    th = math.radians(-12)
    ca, sa = math.cos(th), math.sin(th)
    a_, b_ = 39.0, 24.0
    F = (43.0, 34.0)
    V = (6.0, 11.5)

    def ellipse_at(ox, oy, k=1.0):
        px_, py_ = x - ox, y - oy
        u = (px_ * ca + py_ * sa) / (a_ * k)
        v = (-px_ * sa + py_ * ca) / (b_ * k)
        return u, v

    rim = np.zeros((72, 96), bool)
    for i in range(0, 25):
        t = i / 24.0
        u, v = ellipse_at(F[0] + V[0] * t, F[1] + V[1] * t)
        rim |= (u * u + v * v) <= 1
    u, v = ellipse_at(*F)
    r = np.sqrt(u * u + v * v)
    face = r <= 1
    # a ground heap of dust and pebbles it came to rest on
    c.paint(c.ell(48, 69.5, 40, 4.0) & (y >= 62), "#a88a58")
    # rim (the stone's thickness): darker, turning away to the lower right
    rf = 0.46 + 0.26 * (1 - (x - 6) / 84.0) + (anoise(96, 72, 12.0, 2.0, 382, 2) - 0.5) * 0.25 - 0.14 * (((y - 0.35 * x) % 5) < 1)
    c.rpaint(rim & ~face, rf, GREY_STONE)
    c.mul(rim & ~face & (y > 56), 0.88)
    # face: the same dressed stone, now seen at a slant
    ang = np.arctan2(v, u)
    bevel = r > 0.86
    lit_rim = 0.5 + 0.4 * np.cos(ang - math.radians(-140))
    fcol = 0.68 + 0.14 * (-(u + v) / 2.0) + (vnoise(96, 72, 5.0, 383, 3) - 0.5) * 0.2
    rad = 0.5 + 0.5 * np.cos(ang * 18.0 + r * 3.0)
    fcol = fcol - 0.07 * (rad > 0.9) * ((r > 0.18) & (r < 0.84)) - 0.1 * (np.abs(r - 0.52) < 0.014)
    f = np.where(bevel, lit_rim, fcol) - 0.18 * ((r > 0.84) & (r < 0.87))
    f = np.where(r < 0.17, 0.4 - 0.3 * (r < 0.08), f)
    c.rpaint(face, f, GREY_STONE)
    c.paint(face & (r < 0.075), "#3a3836")
    c.edge(face, 0.6)
    c.edge(rim | face, 0.6)
    for sx, sy, rx, ry in ((6, 69, 4, 2), (88, 69, 5, 2.4), (14, 70, 3, 1.5)):
        c.sphere(sx, sy, rx, ry, ROCK, mask=y < 72)
    c.silhouette_edge(0.62)
    return finish_solid(c)


@sprite("thing_cross", 40, 96)
def th_cross():
    c = Cv(40, 96, 391)
    x, y = c.x, c.y
    rng = np.random.RandomState(392)
    j = lambda p: (p[0] + rng.uniform(-0.6, 0.6), p[1] + rng.uniform(-0.5, 0.5))
    # stones heaped at the foot
    for sx, sy, rx, ry in ((10, 92, 6, 3.4), (30, 92.5, 6.5, 3.2), (20, 94, 5, 2.4), (5, 94, 4, 2), (35, 94, 4, 2)):
        c.sphere(sx, sy, rx, ry, ROCK, mask=y < 96)
    post = c.poly([j((16, 3)), j((20, 1)), j((24.5, 3)), j((24, 24)), j((24.4, 60)), j((24, 90)), j((16, 90)), j((15.6, 60)), j((16.4, 24))])
    pf = 0.66 - 0.5 * ((c.x - 15.6) / 9.0) + (anoise(40, 96, 1.4, 14.0, 393, 2) - 0.5) * 0.5
    pf = pf + 0.1 * (np.sin(c.y * 0.35 + c.x) > 0.8) * -1
    c.rpaint(post, pf, CROSSW)
    c.edge(post, 0.6)
    beam = c.poly([j((3, 20.5)), j((10, 19)), j((30, 19.5)), j((37, 21)), j((37.5, 28)), j((30, 28.6)), j((10, 28.2)), j((2.5, 27.4))])
    bf = 0.72 - 0.5 * ((c.y - 19.0) / 9.5) + (anoise(40, 96, 14.0, 1.4, 394, 2) - 0.5) * 0.5
    c.rpaint(beam, bf, CROSSW)
    c.edge(beam, 0.58)
    # an adze-cut notch and a couple of cracks
    c.paint(c.line([(20, 30), (19, 36), (20, 44)], 1) & post, "#2a1c12")
    c.paint(c.line([(8, 23), (13, 24), (16, 23)], 1) & beam, "#2a1c12")
    c.paint(c.line([(25, 22), (30, 23), (34, 22)], 1) & beam, "#2a1c12")
    c.silhouette_edge(0.6)
    return finish_solid(c)


@sprite("thing_dove", 96, 96, "add")
def th_dove():
    n = 96
    c = Cv(n, n, 401)
    x, y = c.x, c.y
    lo, hi = hx("#bfae90"), hx("#fff6e2")
    rgb_d = np.zeros((n, n, 3), np.float32)
    dove = np.zeros((n, n), bool)

    def put(mask, shade, edge=0.8):
        """Paint a feather / body part with a 0..1 shade, keep a dimmer rim so the layers read."""
        nonlocal rgb_d, dove
        col = lo + (hi - lo) * np.clip(shade, 0, 1)[..., None]
        rim = mask & ~erode(mask)
        col = np.where(rim[..., None], col * edge, col)
        rgb_d = np.where(mask[..., None], col, rgb_d)
        dove |= mask

    # tail: a short fan rising behind the body
    for ang, L, s in ((-20, 17, 0.45), (20, 17, 0.45), (0, 21, 0.6)):
        a = math.radians(ang)
        fm = c.taper([(51, 41), (51 + math.sin(a) * L * 0.6 + 3, 41 - math.cos(a) * L * 0.7), (51 + math.sin(a) * L + 5, 41 - math.cos(a) * L)], 7.0, 3.0)
        put(fm, s + 0.2 * (c.y - 20) / 30.0)
    # wings raised in a V: nine overlapping feathers each side, outer ones drawn first so the inner ones lie on top
    specs = {-1: ((-88, 26), (-80, 31), (-72, 35), (-63, 38), (-54, 40), (-45, 40), (-36, 38), (-27, 35), (-18, 31)),
             1: ((84, 24), (76, 29), (68, 33), (59, 36), (50, 38), (41, 38), (32, 36), (23, 33), (14, 29))}
    shoulders = {-1: (44.0, 51.0), 1: (53.0, 51.0)}
    for side in (-1, 1):
        sh = shoulders[side]
        for i, (th, L) in enumerate(specs[side]):
            a = math.radians(th)
            tip = (sh[0] + math.sin(a) * L, sh[1] - math.cos(a) * L)
            mid = (sh[0] + math.sin(a) * L * 0.5 + side * 1.5, sh[1] - math.cos(a) * L * 0.5 + 3.5)
            fm = c.taper([sh, mid, tip], 10.5, 3.2)
            tt = i / (len(specs[side]) - 1)
            along = np.clip(np.hypot(c.x - sh[0], c.y - sh[1]) / L, 0, 1)
            put(fm, 0.5 + 0.28 * tt + 0.22 * (1 - along) - 0.1 * (side > 0) + 0.12 * (c.y < sh[1] - 12) * (c.x < sh[0]))
        cov = c.ell(sh[0] + side * 5.5, sh[1] - 5, 8.0, 9.5)
        put(cov, 0.82 - 0.1 * (side > 0) + 0.16 * ((c.x < 50) & (c.y < 42)))
    # body (teardrop heading downward), neck and head with a small beak
    body = c.taper([(50, 42), (48.5, 53), (46.5, 62)], 13.5, 8.5)
    put(body, 0.64 + 0.3 * np.clip((52 - c.x) / 12.0, -0.5, 1) * 0.6 + 0.1 * (c.y < 52))
    head = c.ell(45.5, 67.5, 5.4, 5.2)
    put(head, 0.86 - 0.35 * ((c.x - 40) / 11.0) * 0.5, 0.78)
    beak = c.poly([(41, 70), (46, 71), (42, 79)])
    dove |= beak
    rgb_d = np.where(beak[..., None], hx("#ffc866"), rgb_d)
    rgb_d = np.where(c.ell(44.0, 66, 0.7, 0.7)[..., None], hx("#7a5c30"), rgb_d)
    a_d = np.clip(blur(dove.astype(np.float32), 0.7) * 1.3, 0, 1)
    a_d = np.where(dove, 1.0, a_d)
    # soft rays of light from above and a faint halo
    a_r = np.zeros((n, n), np.float32)
    for ang, wd, wt in ((-40, 2.6, 0.14), (-24, 3.2, 0.2), (-11, 2.4, 0.16), (0, 3.6, 0.26), (11, 2.6, 0.16), (24, 3.2, 0.2), (40, 2.6, 0.14)):
        a = math.radians(ang)
        ox, oy = 48 - math.sin(a) * 8, -8.0
        al = (x - ox) * math.sin(a) + (y - oy) * math.cos(a)
        pe = np.abs((x - ox) * math.cos(a) - (y - oy) * math.sin(a))
        w_ = wd + 0.07 * al
        a_r += wt * np.exp(-(pe / w_) ** 2) * np.clip(1 - al / 105.0, 0, 1) ** 1.2 * np.clip(al / 6.0, 0, 1)
    rr = np.hypot(x - 48, y - 50)
    a_r += 0.2 * np.exp(-(rr / 30.0) ** 2) + 0.1 * np.exp(-(rr / 14.0) ** 2)
    a_r *= np.clip((n - 1 - y) / 12.0, 0, 1) * np.clip(np.minimum(x, n - 1 - x) / 8.0, 0, 1)
    a_r = np.clip(a_r, 0, 0.7)
    rgb_r = hx("#ffe6a0")[None, None, :] + 0.0 * x[..., None]
    P = rgb_d * a_d[..., None] + rgb_r * a_r[..., None] * (1 - a_d[..., None])
    A = np.clip(a_d + a_r * (1 - a_d), 0, 1)
    rgb = P / np.maximum(A, 1e-4)[..., None]
    return finish_soft(rgb, A, qa=48)


CLOUD = ramp("#212f36", "#32454d", "#485f69", "#637d86", "#869fa5")


@sprite("thing_storm_cloud", 256, 96, "mix")
def th_storm_cloud():
    w, h = 256, 96
    c = Cv(w, h, 411)
    x, y = c.x, c.y
    rng = np.random.RandomState(412)
    xs = np.arange(w)
    env = 0.28 + 0.5 * np.sin(np.pi * np.clip((xs - 6) / 244.0, 0, 1)) ** 0.8
    for pk, ph, pw in ((60, 0.55, 26), (128, 0.9, 30), (200, 0.65, 26), (96, 0.35, 16), (170, 0.4, 18)):
        env = env + ph * 0.42 * np.exp(-(((xs - pk) / pw) ** 2))
    env = np.clip(env, 0, 1.0)
    puffs = []
    for i in range(150):
        px_ = rng.uniform(8, 248)
        top = 70 - 60 * env[int(px_)]
        py_ = rng.uniform(top + 6, 66)
        r = rng.uniform(8, 17)
        puffs.append((px_, py_, r * 1.15, r * 0.9))
    puffs.sort(key=lambda p: p[1])
    # broad underside mass
    base_edge = 70 + 7 * (vnoise(w, h, 9.0, 413, 2) - 0.5) * 2
    for px_, py_, rx, ry in puffs:
        bias = -0.12 - 0.5 * np.clip((py_ - 30) / 50.0, 0, 1)
        jit = (vnoise(w, h, 4.0, int(px_ * 13 + py_) % 99999, 2) - 0.5) * 0.3
        c.sphere(px_, py_, rx, ry, CLOUD, bias=bias + 0.0, gain=1.3, jit=jit)
    cloud = c.a >= 0.5
    # ragged base: cut with a wavering edge and hang a few tatters below it
    cut = y < (base_edge + 3 * np.sin(x * 0.9) + 2 * np.sin(x * 2.3 + 1.0))
    m = cloud & cut
    for k in range(9):
        tx = rng.uniform(14, 242)
        ty = rng.uniform(64, 72)
        wisp = c.ell(tx, ty, rng.uniform(7, 15), rng.uniform(3, 6))
        m |= wisp & cloud
        c.rpaint(wisp & ~m, 0.18 + 0.0 * x, CLOUD)
        m |= wisp & (y > 58) & (y < 82)
    # darken the belly
    belly = np.clip((y - 44) / 30.0, 0, 1)
    rgb = c.rgb * (1 - 0.38 * belly)[..., None]
    rgb = np.where(m[..., None] & ~cloud[..., None], hx("#1c2830")[None, None, :], rgb)
    rgb = rgb + hx("#8fb0b4")[None, None, :] * (0.05 * np.clip(1 - (y - 14) / 30.0, 0, 1) * (x < 140) * 1.0)[..., None]
    a = blur(m.astype(np.float32), 1.1)
    a = np.clip(a * 1.35 - 0.12, 0, 1) * 0.96
    # soft ragged fade along the very bottom
    a *= np.clip((base_edge + 14 - y) / 12.0, 0, 1)
    return finish_soft(rgb, a, qa=24)


@sprite("thing_rain", 128, 128, "mix")
def th_rain():
    n = 128
    rng = np.random.RandomState(421)
    A = np.zeros((n, n), np.float32)
    for i in range(96):
        x0, y0 = rng.uniform(0, n), rng.uniform(0, n)
        L = rng.uniform(7, 17)
        al = rng.uniform(0.45, 0.85)
        sl = -0.27
        for s in np.arange(0, L, 0.5):
            t = s / L
            px_, py_ = int(round(x0 + sl * s)) % n, int(round(y0 + s)) % n
            A[py_, px_] = max(A[py_, px_], al * (0.3 + 0.7 * t))
        if rng.rand() < 0.3:
            px_, py_ = int(round(x0 + sl * L + 1)) % n, int(round(y0 + L)) % n
            A[py_, px_] = max(A[py_, px_], al * 0.6)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    rgb = np.zeros((n, n, 3), np.float32) + hx("#b6d0ea")
    rgb = rgb + (hx("#e0eefa") - hx("#b6d0ea"))[None, None, :] * np.clip(A * 1.2 - 0.5, 0, 1)[..., None]
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = dith(rgb, 24)
    out[..., 3] = np.round(np.clip(A, 0, 1) * 255).astype(np.uint8)
    return out


@sprite("thing_lightning", 96, 192, "add")
def th_lightning():
    w, h = 96, 192
    c = Cv(w, h, 431)
    rng = np.random.RandomState(432)
    pts = [(50.0, 0.0)]
    cx = 50.0
    yy = 0.0
    while yy < 184:
        yy += rng.uniform(10, 20)
        cx = float(np.clip(cx + rng.uniform(-13, 13) + (46 - cx) * 0.12, 30, 66))
        pts.append((cx, min(yy, 186)))
        if rng.rand() < 0.5 and yy < 150:
            pts.append((cx + rng.uniform(-5, 5), min(yy + rng.uniform(2, 5), 186)))
    pts[-1] = (46.0, 187.0)
    branches = []
    for idx, ln in ((2, 3), (4, 3), (6, 2)):
        if idx < len(pts):
            p = pts[idx]
            d = 1 if rng.rand() < 0.5 else -1
            b = [p]
            for k in range(ln):
                b.append((b[-1][0] + d * rng.uniform(5, 10), b[-1][1] + rng.uniform(8, 15)))
            branches.append(b)
    core = c.line(pts, 2)
    for b in branches:
        core |= c.line(b, 1)
    thick = c.line(pts, 4)
    for b in branches:
        thick |= c.line(b, 2)
    k1 = blur(thick.astype(np.float32), 1.6) * 2.0
    k2 = blur(thick.astype(np.float32), 5.5) * 3.0
    k3 = blur(thick.astype(np.float32), 11.0) * 4.0
    I = np.clip(core * 1.0 + k1 * 0.55 + k2 * 0.5 + k3 * 0.32, 0, 1)
    edge_fade = np.clip(np.minimum(c.x, w - 1 - c.x) / 10.0, 0, 1) * np.clip((h - 1 - c.y) / 8.0, 0, 1)
    I = I * edge_fade
    t = np.clip(I * 1.1, 0, 1)[..., None]
    lo, mid, hi = hx("#5a7cf0"), hx("#a8c4ff"), hx("#f2f6ff")
    col = np.where(t < 0.5, lo + (mid - lo) * (t / 0.5), mid + (hi - mid) * np.clip((t - 0.5) / 0.5, 0, 1))
    return finish_soft(col, I, qa=40)


def sky_dark(amax, seed):
    w, h = 128, 64
    yy = np.arange(h, dtype=np.float32)[:, None] * np.ones((1, w), np.float32)
    t = yy / (h - 1)
    top, bot = hx("#241432"), hx("#42265a")
    rgb = top[None, None, :] * (1 - t[..., None]) + bot[None, None, :] * t[..., None]
    a = amax * np.clip((h - 1 - yy) / (0.3 * h), 0, 1)
    a = a * a * (3 - 2 * a / max(amax, 1e-6)) if False else a
    s = np.clip((h - 1 - yy) / (0.3 * h), 0, 1)
    a = amax * (s * s * (3 - 2 * s))
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = np.round(np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    out[..., 3] = np.round(a * 255).astype(np.uint8)
    return out


@sprite("thing_sky_dark1", 128, 64, "mix")
def th_sky_dark1():
    return sky_dark(0.35, 1)


@sprite("thing_sky_dark2", 128, 64, "mix")
def th_sky_dark2():
    return sky_dark(0.60, 2)


@sprite("thing_sky_dark3", 128, 64, "mix")
def th_sky_dark3():
    return sky_dark(0.82, 3)


@sprite("thing_waves", 128, 32, "mix")
def th_waves():
    w, h = 128, 32
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    A = np.zeros((h, w), np.float32)
    rng = np.random.RandomState(441)
    two_pi = 2 * math.pi
    lines = ((6.0, 1.0, 3, 1.1, 0.8), (12.0, 1.4, 4, 1.5, 2.1), (19.0, 1.8, 3, 2.0, 4.0), (27.0, 2.2, 4, 2.6, 5.3))
    for (y0, amp, nw, thick, ph) in lines:
        yc = y0 + amp * np.sin(two_pi * nw * xx / w + ph) + 0.25 * amp * np.sin(two_pi * (nw * 2) * xx / w + ph * 2)
        scal = 0.7 + 0.6 * np.abs(np.sin(np.pi * xx * (nw * 2) / w + ph))
        d = yy - yc
        core = (d > -thick * 0.5 * scal) & (d < thick * 0.5 * scal)
        gap = np.sin(two_pi * 3 * xx / w + ph * 3) + np.sin(two_pi * 7 * xx / w + ph) > -1.55
        wash = (d > thick * 0.5 * scal) & (d < thick * 0.5 * scal + 5.0)
        A = np.maximum(A, wash * 0.14)
        A = np.maximum(A, (core & gap) * 0.92)
        # bubbles trailing behind the foam
        bub = (rng.rand(h, w) < 0.02) & (d > thick * 0.5 + 0.5) & (d < thick + 5.0)
        A = np.maximum(A, bub * 0.6)
    rgb = np.zeros((h, w, 3), np.float32) + hx("#eef4f0")
    rgb = np.where((A < 0.3)[..., None], hx("#bfd8d8")[None, None, :], rgb)
    return finish_soft(rgb, A, qa=14)


# ==== END SPRITES ====


def build(out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    info = {}
    for name, (w, h, blend, fn) in SPRITES.items():
        rgba = fn()
        assert rgba.shape == (h, w, 4) and rgba.dtype == np.uint8, (name, rgba.shape)
        Image.fromarray(rgba, "RGBA").save(os.path.join(out_dir, name + ".png"), optimize=False, compress_level=9)
        info[name] = {"size": [w, h], "blend": blend}
    return info


if __name__ == "__main__":
    build(sys.argv[1])
