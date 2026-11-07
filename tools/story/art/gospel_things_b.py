"""Gospel adventure billboard props, part B (docs/STORY_25D_ART_DIRECTION.md 2.D): boats and nets, baskets, tables, lanterns, pack animals, workshop and camp props.

`build(out_dir)` writes every sprite as `<name>.png` (RGBA, hard 0/255 cut-out alpha, a mid-tone DAYLIGHT paint: the engine multiplies a sprite by the room's light, so
nothing is painted dark or blown out) and returns {name: {"size": [w, h], "blend": ""}}. Sunlit, dusty and warm: ochre, terracotta, olive, undyed wool, weathered timber,
wicker, clay, hemp, iron, bronze. Every subject stands with its base on the bottom row, centred, a few transparent pixels of margin. Self-contained (numpy + Pillow):
shapes are boolean masks painted through small colour ramps with 8x8 ordered dithering and a darker edge of the local colour, the look of tex_hospital / tex_night_one.
Deterministic: every random value comes from a seeded generator, so the same code gives the same bytes. `python -m tools.story.art.gospel_things_b <out_dir>`.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

# ---- palette ramps (dark to light) ------------------------------------------------------------------------------------------------------------------------

BAYER8 = (np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38],
                    [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
                    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]], np.float32) + 0.5) / 64.0 - 0.5


def hx(c: str) -> np.ndarray:
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def R(*cols) -> np.ndarray:
    return np.stack([hx(c) for c in cols])


WOOD = R("#3e2a1c", "#5e4128", "#7e5a38", "#9c7648", "#bc9462")          # warm timber
WEATH = R("#4e4034", "#6c5a46", "#8a7660", "#a89478", "#c4b296")         # weathered grey timber
DWOOD = R("#2e2018", "#4a3424", "#664830", "#82603e", "#9c7650")         # dark seasoned wood
CLAY = R("#6a3822", "#8c4e2e", "#ab6a40", "#c88a5a", "#dcaa7a")          # terracotta pots
TAN = R("#6e5434", "#8e7048", "#ae8e5e", "#c8aa78", "#dec498")           # sandy / buff clay
WICKER = R("#704c1e", "#946a2c", "#b88c42", "#d4aa5c", "#e6c47c")
BREAD = R("#74441e", "#9c6428", "#c08440", "#dca458", "#efc880")
STONE = R("#6a604c", "#8a7e66", "#a99d82", "#c6bb9e", "#ddd3b6")         # white limestone in sun
IRON = R("#2c2a2e", "#46444a", "#625f68", "#807d88", "#a29fa8")
BRONZE = R("#5e4018", "#8a5e26", "#b4843a", "#d4a64e", "#ecc874")
SILVER = R("#5c6a76", "#808e98", "#a4b0b8", "#c8d0d4", "#e4e8ea")
HEMP = R("#6c5c34", "#8e7a46", "#b09a5c", "#cdb978", "#e0d094")
WOOL = R("#8a7e68", "#a99d84", "#c4b89e", "#dcd2ba", "#eee6d0")
RED = R("#58171a", "#7a2420", "#9e3a2e", "#bc5640", "#d4745a")
OCHRE = R("#7a5a1c", "#a07a26", "#c49a36", "#dcb64e", "#ecd070")
OLIVE = R("#454c24", "#626c32", "#808c44", "#a0ac5c", "#bcc67c")
CORK = R("#8a6a3c", "#b08a52", "#d0aa70", "#e8c890", "#f4dca8")
STRAW = R("#7a5e22", "#98792e", "#b4943e", "#ccb056", "#dcc676")
DONK = R("#55555a", "#74747a", "#928f8e", "#b0aba4", "#cfc9bd")
CAMEL = R("#8a6a44", "#a8885a", "#c4a674", "#dcc490", "#ecd8a8")
WATER = R("#2c5a8a", "#3a76a8", "#5894c2", "#80b4d8", "#b4d8ec")
FLAME = R("#a82c14", "#d85a1c", "#f08c2c", "#fcc44c", "#fff0a8")
TENT = R("#2a211b", "#3e3128", "#54443a", "#6e5a4a", "#8a7360")
CLOTH = R("#6a2a24", "#8e3c30", "#b0553e", "#c87454", "#dc9272")
CREAM = R("#8e8468", "#b0a688", "#cfc4a4", "#e6dcc0", "#f2ead2")
SOIL = R("#5a4630", "#7a6244", "#9a8058", "#b89c70")


def quant(shade: np.ndarray, pal: np.ndarray, dither: float = 0.8) -> np.ndarray:
    h, w = shade.shape
    b = BAYER8[np.arange(h)[:, None] % 8, np.arange(w)[None, :] % 8]
    k = len(pal) - 1
    i = np.clip(np.round(np.clip(shade, 0, 1) * k + b * dither), 0, k).astype(int)
    return (pal[i] * 255 + 0.5).astype(np.uint8)


def vnoise(h: int, w: int, sx: float, sy: float | None = None, seed: int = 1, octaves: int = 2) -> np.ndarray:
    """Value noise 0..1 with cell size sx x sy (anisotropic grain when they differ)."""
    sy = sx if sy is None else sy
    rng = np.random.RandomState(seed)
    out = np.zeros((h, w), np.float32)
    amp = tot = 1.0
    tot = 0.0
    amp = 1.0
    for o in range(octaves):
        cx, cy = max(sx / 2 ** o, 1.0), max(sy / 2 ** o, 1.0)
        gw, gh = int(w / cx) + 3, int(h / cy) + 3
        g = rng.rand(gh, gw).astype(np.float32)
        im = Image.fromarray(g, "F").resize((int(gw * cx), int(gh * cy)), Image.BILINEAR)
        out += np.asarray(im)[:h, :w] * amp
        tot += amp
        amp *= 0.5
    return out / tot


class Spr:
    """An RGBA billboard canvas. Masks are built with rect / ell / poly / seg, painted through a ramp with `paint`, flat colours with `fill`."""

    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), np.uint8)
        self.a = np.zeros((h, w), bool)
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        self.xc, self.yc = x + 0.5, y + 0.5

    # -- masks
    def rect(self, x0, y0, x1, y1):
        return (self.xc > x0) & (self.xc < x1) & (self.yc > y0) & (self.yc < y1)

    def ell(self, cx, cy, rx, ry):
        return ((self.xc - cx) / rx) ** 2 + ((self.yc - cy) / ry) ** 2 <= 1.0

    def poly(self, pts):
        im = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(im).polygon([(float(px), float(py)) for px, py in pts], fill=255)
        return np.asarray(im) > 0

    def seg(self, x0, y0, x1, y1, w0=1.5, w1=None):
        w1 = w0 if w1 is None else w1
        dx, dy = x1 - x0, y1 - y0
        t = np.clip(((self.xc - x0) * dx + (self.yc - y0) * dy) / max(dx * dx + dy * dy, 1e-6), 0, 1)
        d = np.hypot(self.xc - (x0 + t * dx), self.yc - (y0 + t * dy))
        return d <= (w0 + (w1 - w0) * t) * 0.5

    def path(self, pts, w0=1.5, w1=None):
        """A tapered polyline of capsules."""
        w1 = w0 if w1 is None else w1
        n = len(pts) - 1
        m = np.zeros((self.h, self.w), bool)
        for i in range(n):
            a = w0 + (w1 - w0) * i / n
            b = w0 + (w1 - w0) * (i + 1) / n
            m |= self.seg(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], a, b)
        return m

    def vase(self, cx, prof, lin=False):
        """A body of revolution: prof = [(y, radius), ...] top to bottom, cosine-smoothed between the control points."""
        ys = np.array([p[0] for p in prof], np.float32)
        rs = np.array([p[1] for p in prof], np.float32)
        yy = self.yc[:, 0]
        k = np.clip(np.searchsorted(ys, yy, side="right") - 1, 0, len(ys) - 2)
        t = np.clip((yy - ys[k]) / np.maximum(ys[k + 1] - ys[k], 1e-6), 0, 1)
        if not lin:
            t = (1 - np.cos(np.pi * t)) / 2
        r = rs[k] + (rs[k + 1] - rs[k]) * t
        r = np.where((yy >= ys[0]) & (yy <= ys[-1]), r, 0)[:, None]
        return (np.abs(self.xc - cx) <= r) & (r > 0.4)

    # -- shading fields
    def cyl(self, cx, r, lo=0.1, hi=0.98):
        u = np.clip((self.xc - cx) / max(r, 0.5), -1, 1)
        return hi - (hi - lo) * (u + 1) / 2 + 0.1 * np.clip(u - 0.7, 0, 1) / 0.3

    def lit(self, cx, cy, rx, ry, base=0.55, k=0.5):
        return base + k * (0.6 * (cy - self.yc) / ry + 0.4 * (cx - self.xc) / rx)

    def vgrad(self, y0, y1, a, b):
        return a + (b - a) * np.clip((self.yc - y0) / max(y1 - y0, 1e-6), 0, 1)

    def hgrad(self, x0, x1, a, b):
        return a + (b - a) * np.clip((self.xc - x0) / max(x1 - x0, 1e-6), 0, 1)

    # -- painting
    def paint(self, mask, pal, shade=0.5, edge=1, dither=0.8):
        m = np.asarray(mask, bool)
        sh = np.broadcast_to(np.asarray(shade, np.float32), (self.h, self.w))
        layer = quant(sh, pal, dither)
        self.rgb[m] = layer[m]
        self.a |= m
        if edge:
            up = np.zeros_like(m)
            dn = np.zeros_like(m)
            lf = np.zeros_like(m)
            rt = np.zeros_like(m)
            up[1:] = m[:-1]
            dn[:-1] = m[1:]
            lf[:, 1:] = m[:, :-1]
            rt[:, :-1] = m[:, 1:]
            b = m & ~(up & dn & lf & rt)
            self.rgb[b] = (pal[edge - 1] * 255 + 0.5).astype(np.uint8)

    def fill(self, mask, col):
        m = np.asarray(mask, bool)
        self.rgb[m] = (hx(col) * 255 + 0.5).astype(np.uint8)
        self.a |= m

    def dot(self, x, y, col):
        self.fill(self.rect(x, y, x + 1, y + 1), col)

    def rgba(self) -> np.ndarray:
        return np.dstack([self.rgb, np.where(self.a, 255, 0).astype(np.uint8)])


class Xf:
    """Scaled drawing for a figure defined in its own units: ground at y = 0, up is negative, x centred on 0."""

    def __init__(self, s: Spr, ox: float, gy: float, k: float):
        self.s, self.ox, self.gy, self.k = s, ox, gy, k

    def X(self, x):
        return self.ox + x * self.k

    def Y(self, y):
        return self.gy + y * self.k

    def ell(self, cx, cy, rx, ry):
        return self.s.ell(self.X(cx), self.Y(cy), rx * self.k, ry * self.k)

    def seg(self, x0, y0, x1, y1, w0=2.0, w1=None):
        w1 = w0 if w1 is None else w1
        return self.s.seg(self.X(x0), self.Y(y0), self.X(x1), self.Y(y1), max(w0 * self.k, 1.3), max(w1 * self.k, 1.3))

    def path(self, pts, w0=2.0, w1=None):
        w1 = w0 if w1 is None else w1
        return self.s.path([(self.X(x), self.Y(y)) for x, y in pts], max(w0 * self.k, 1.3), max(w1 * self.k, 1.3))

    def poly(self, pts):
        return self.s.poly([(self.X(x), self.Y(y)) for x, y in pts])

    def rect(self, x0, y0, x1, y1):
        return self.s.rect(self.X(x0), self.Y(y0), self.X(x1), self.Y(y1))

    def light(self, cx, cy, rx, ry, base=0.55, k=0.5):
        return self.s.lit(self.X(cx), self.Y(cy), rx * self.k, ry * self.k, base, k)


def shift(m: np.ndarray, dx: int, dy: int) -> np.ndarray:
    out = np.zeros_like(m)
    ys, yd = (slice(0, m.shape[0] - dy), slice(dy, m.shape[0])) if dy >= 0 else (slice(-dy, m.shape[0]), slice(0, m.shape[0] + dy))
    xs, xd = (slice(0, m.shape[1] - dx), slice(dx, m.shape[1])) if dx >= 0 else (slice(-dx, m.shape[1]), slice(0, m.shape[1] + dx))
    out[yd, xd] = m[ys, xs]
    return out


def dmask(s: Spr, f) -> np.ndarray:
    """A dithered mask from a 0..1 coverage field."""
    return (np.broadcast_to(np.asarray(f, np.float32), (s.h, s.w)) + BAYER8[np.arange(s.h)[:, None] % 8, np.arange(s.w)[None, :] % 8]) > 0.5


# ---- shared drawing pieces --------------------------------------------------------------------------------------------------------------------------------

def flame(s: Spr, cx: float, by: float, h: float, w: float, seed: int = 1, tongues: int = 3) -> None:
    """A flame: a main tongue and smaller side tongues, red edge, orange body, yellow and pale core."""
    rng = np.random.RandomState(seed)
    specs = [(0.0, 1.0, 1.0)]
    if tongues > 1:
        specs += [(-w * 0.28, 0.62, 0.55), (w * 0.28, 0.72, 0.6)]
    if tongues > 3:
        specs += [(-w * 0.1, 0.8, 0.5)]
    layers = [(1.0, "#c4401c"), (0.74, "#f07a24"), (0.5, "#fcb83c"), (0.28, "#fff0a8")]
    for k, col in layers:
        m = np.zeros((s.h, s.w), bool)
        for off, hh, ww in specs:
            ph = rng.rand() * 6
            hgt = h * hh
            t = np.clip((by - s.yc) / hgt, 0, 1.2)
            sway = np.sin(t * 5.0 + ph) * w * 0.18 * t
            half = w * 0.5 * ww * k * (np.clip(1 - t, 0, 1) ** 0.75) * (0.55 + 0.45 * np.sin(np.clip(t * 3.0, 0, 1.5) + 0.3))
            tip = (by - s.yc) <= hgt * (0.55 + 0.45 * k) if k < 1 else (by - s.yc) <= hgt
            m |= (np.abs(s.xc - (cx + off + sway)) <= half) & tip & (s.yc <= by)
        s.fill(m, col)


def loaf(s: Spr, cx, cy, rx=8.0, ry=4.5, seed=1) -> None:
    """A round flat loaf with scored top."""
    m = s.ell(cx, cy, rx, ry)
    s.paint(m, BREAD, s.lit(cx, cy, rx, ry, 0.62, 0.55), edge=1)
    for i, dx in enumerate((-0.45, 0.0, 0.45)):
        s.fill(s.seg(cx + dx * rx - 1.2, cy - ry * 0.55, cx + dx * rx + 1.2, cy + ry * 0.15, 1.1) & m, "#7a4a22")


def fish_diag(s: Spr, x, y, L, ang, flip=False) -> None:
    """A small silver fish lying along an angle (head at (x, y), tail pointing away)."""
    c, sn = math.cos(ang), math.sin(ang)
    hx_, hy_ = x, y
    tx, ty = x + c * L, y + sn * L
    body = s.seg(hx_, hy_, tx, ty, L * 0.32, L * 0.1)
    tail = s.poly([(tx - c * 1, ty - sn * 1), (tx + c * L * 0.28 - sn * L * 0.2, ty + sn * L * 0.28 + c * L * 0.2),
                   (tx + c * L * 0.28 + sn * L * 0.2, ty + sn * L * 0.28 - c * L * 0.2)])
    ys = np.array([hy_, ty])
    s.paint(tail, SILVER, 0.4, edge=1)
    s.paint(body, SILVER, s.vgrad(min(hy_, ty) - L * 0.2, max(hy_, ty) + L * 0.2, 0.3, 0.95), edge=1)
    s.dot(int(round(hx_ + c * 1.2 + sn * 0.2)) - 0, int(round(hy_ - 0.4)), "#2a3038")


def wicker_shade(s: Spr, row_h=3, tw=4, base=0.55, amp=0.28, y0=0.0) -> np.ndarray:
    """A basket-weave shade field: rows of staggered woven strands."""
    row = np.floor((s.yc - y0) / row_h)
    off = (row % 2) * (tw / 2)
    ph = ((s.xc + off) % tw) / tw
    f = base + amp * (0.5 - np.abs(ph - 0.5) * 2) * 0.9 - amp * 0.5
    f = f - 0.18 * (((s.yc - y0) % row_h) < 1)
    return f


def table_slab(s: Spr, x0, x1, tt, legs=True, apron=7, shade_k=1.0) -> int:
    """A long trestle table of weathered boards (legs, stretcher, top). Returns the y a thing stands on (the top surface)."""
    H = s.h
    gy = H - 1
    xl, xr = x0 + 15, x1 - 15
    if legs:
        for xc in (xl, xr):
            lm = s.seg(xc - 3, tt + apron - 1, xc - 12, gy, 5.5, 5.0) | s.seg(xc + 3, tt + apron - 1, xc + 12, gy, 5.5, 5.0)
            s.paint(lm, WEATH, s.cyl(xc, 14, 0.15, 0.9) * 0.8 + 0.1, edge=1)
            s.paint(s.rect(xc - 9, gy - 17, xc + 9, gy - 14), WEATH, 0.45, edge=1)
        s.paint(s.rect(xl + 4, gy - 25, xr - 4, gy - 21), WEATH, s.vgrad(gy - 25, gy - 21, 0.8, 0.3), edge=1)
    # top surface (lit strip), then the front board with end grain
    nz = vnoise(s.h, s.w, 14, 2, 31)
    surf = s.rect(x0 + 2, tt - 4, x1 - 2, tt)
    s.paint(surf, WEATH, 0.78 + (nz - 0.5) * 0.4, edge=2)
    front = s.rect(x0, tt, x1, tt + apron)
    s.paint(front, WEATH, 0.58 + (nz - 0.5) * 0.35 - 0.12 * ((s.yc - tt) > apron - 2), edge=1)
    for sx in (x0 + (x1 - x0) * 0.27, x0 + (x1 - x0) * 0.58, x0 + (x1 - x0) * 0.83):
        s.fill(s.rect(round(sx), tt, round(sx) + 1, tt + apron - 1), "#4a4036")
    s.fill(s.rect(x0, tt + 2, x0 + 2, tt + apron), "#675a4a")
    return tt - 1


# ---- the sprites ------------------------------------------------------------------------------------------------------------------------------------------

def thing_boat() -> np.ndarray:
    s = Spr(192, 96)
    xc = s.xc
    t = np.clip((xc - 97) / 85.0, -1.05, 1.05)
    at = np.abs(t)
    top = 55 - 27 * at ** 2.5 * np.where(t > 0, 1.0, 0.75)
    bot = 91 - np.where(t > 0, 59, 51) * at ** 2.7
    span = np.maximum(bot - top, 1)
    k = (s.yc - top) / span
    hull = (s.yc >= top) & (s.yc <= bot) & (xc > 12) & (xc < 183)
    # mast, furled sail and rigging (the hull covers the mast foot)
    s.paint(s.seg(92, 7, 92, 62, 4.5, 5.5), WOOD, s.cyl(92, 3, 0.2, 0.95), edge=1)
    s.paint(s.seg(48, 24, 96, 20.5, 8, 9.5) | s.seg(96, 20.5, 146, 24, 9.5, 8), WOOL, 0.55, edge=1)
    sail = s.seg(48, 24, 96, 20.5, 8, 9.5) | s.seg(96, 20.5, 146, 24, 9.5, 8)
    sail_y = 21.5 + np.clip(np.abs(xc - 97) / 49, 0, 1) * 2.5
    sh = 0.78 - 0.55 * np.clip((s.yc - (sail_y - 4.5)) / 9.0, 0, 1)
    fold = ((xc * 0.9 + s.yc * 1.6) % 9) < 1.2
    s.paint(sail, WOOL, sh - 0.14 * fold, edge=1)
    for (px0, py0, pw, col) in ((60, 21, 11, "#b0553e"), (112, 22, 12, "#c49a36"), (84, 19, 8, "#8a7e68")):
        pm = s.rect(px0, py0, px0 + pw, py0 + 6) & sail
        s.fill(pm, col)
        s.fill(pm & ((xc - px0) % 3 < 1) & ((s.yc < py0 + 1.5) | (s.yc > py0 + 4.5)), "#5a4630")
    for rx_ in (56, 80, 112, 136):
        s.paint(s.rect(rx_, sail_y - 5, rx_ + 2.5, sail_y + 5) & sail, HEMP, 0.45, edge=0)
    s.paint(s.rect(90, 17, 95, 25), HEMP, 0.5, edge=1)
    s.fill(s.seg(92, 8, 181, 31, 1.3), "#7a6a3e")
    s.fill(s.seg(92, 8, 14, 38, 1.3), "#7a6a3e")
    s.paint(s.ell(92, 7, 3, 2.4), WOOD, 0.8, edge=1)
    # keel blocks
    for bx in (58, 118):
        s.paint(s.rect(bx, 85, bx + 13, 96), WEATH, s.hgrad(bx, bx + 13, 0.8, 0.3), edge=1)
    # hull: timber, pale worn stripe, terracotta antifouling below
    grain = vnoise(s.h, s.w, 16, 2.2, 41)
    plank = np.floor(k * 5.2)
    ptone = np.array([0.0, 0.12, -0.06, 0.1, -0.1, 0.05, 0.0])[np.clip(plank.astype(int), 0, 6)]
    shd = 0.7 - 0.3 * k + (grain - 0.5) * 0.45 + ptone
    s.paint(hull, WOOD, shd, edge=1)
    low = hull & (k > 0.8)
    s.paint(low, CLAY, 0.45 + (grain - 0.5) * 0.5 - 0.3 * (k - 0.8) / 0.2, edge=0)
    stripe = hull & (k > 0.3) & (k < 0.5)
    worn = grain > 0.68
    s.paint(stripe & ~worn, CREAM, 0.72 - 0.35 * (k - 0.3) / 0.2 + (grain - 0.5) * 0.4, edge=0)
    for kk in (0.12, 0.3, 0.5, 0.64, 0.8):
        yline = top + span * kk
        s.fill(hull & (np.abs(s.yc - yline) < 0.62), "#3e2a1c")
    s.paint(hull & (s.yc < top + 3.2), DWOOD, s.vgrad(0, 1, 0.9, 0.9) - 0.15 * (s.yc > top + 2), edge=0)
    s.fill(hull & (s.yc < top + 1.1), "#a8855a")
    for nx_ in range(26, 176, 14):
        ny_ = float(np.interp(nx_, [12, 183], [0, 1]))
        yy = 55 - 27 * abs((nx_ - 97) / 85) ** 2.5 * (1.0 if nx_ > 97 else 0.75)
        s.dot(nx_, int(yy + 6), "#3e2a1c")
    # outline of the whole hull
    sil = hull
    edge = sil & ~(shift(sil, 1, 0) & shift(sil, -1, 0) & shift(sil, 0, 1) & shift(sil, 0, -1))
    s.fill(edge, "#3e2a1c")
    # prow post with a curl, stern post
    s.paint(s.path([(176, 38), (184, 27), (186, 21)], 5.0, 3.5), DWOOD, 0.55, edge=1)
    s.paint(s.ell(186, 20, 3, 3), WOOD, 0.7, edge=1)
    s.paint(s.path([(15, 44), (11, 36), (11, 32)], 4.5, 3.5), DWOOD, 0.55, edge=1)
    # coil of rope on the shore in front of the hull
    for (cy, rx, ry, base) in ((91, 15, 5.2, 0.5), (87, 13, 4.5, 0.62)):
        o = s.ell(131, cy, rx, ry)
        s.paint(o, HEMP, base + 0.2 * np.sin((np.hypot((s.xc - 131) / rx, (s.yc - cy) / ry)) * 14) + 0.1, edge=1)
        s.fill(s.ell(131, cy, rx * 0.34, ry * 0.34), "#4a3a1c")
    s.paint(s.path([(143, 90), (152, 92), (160, 90)], 2.2), HEMP, 0.6, edge=1)
    return s.rgba()


def thing_boat_far() -> np.ndarray:
    s = Spr(64, 40)
    xc = s.xc
    # water: a lens of cobalt ripples under the boat
    wm = s.ell(32, 35.6, 29, 4.4)
    s.paint(wm, WATER, 0.5 + 0.3 * (vnoise(40, 64, 5, 2, 7) - 0.5) + 0.3 * ((s.yc - 31) < 0) , edge=0)
    for i, (rx_, ry_) in enumerate(((10, 33.5), (28, 36.5), (44, 34), (54, 36))):
        s.fill(s.rect(rx_, ry_, rx_ + 6, ry_ + 1) & wm, "#c4dcea")
    t = np.clip((xc - 32) / 22.0, -1.05, 1.05)
    at = np.abs(t)
    top = 27 - 8 * at ** 2.4
    bot = 34 - 11 * at ** 1.8
    hull = (s.yc >= top) & (s.yc <= bot) & (xc > 9) & (xc < 55)
    s.paint(hull, WOOD, 0.75 - 0.5 * (s.yc - top) / np.maximum(bot - top, 1), edge=1)
    s.fill(hull & (np.abs(s.yc - (top + (bot - top) * 0.35)) < 0.7), "#cfc4a4")
    s.paint(s.seg(33, 6, 33, 28, 2.2), WOOD, 0.6, edge=1)
    sail = s.poly([(35, 7), (35, 24), (52, 24), (48, 21), (42, 14)])
    s.paint(sail, WOOL, s.hgrad(35, 52, 0.95, 0.5) - 0.1 * ((s.xc * 0.4 + s.yc) % 6 < 1), edge=1)
    s.fill(s.seg(33, 7, 12, 27, 1.1), "#7a6a3e")
    return s.rgba()


def thing_nets() -> np.ndarray:
    s = Spr(96, 96)
    xc, yc = s.xc, s.yc
    # poles in a mound of stones
    for px_, lean in ((9, 1.0), (87, -1.0)):
        s.paint(s.seg(px_ - lean * 1, 92, px_ + lean * 0.5, 6, 7.0, 5.0), WEATH, s.cyl(px_, 4.0, 0.15, 0.95), edge=1)
        s.paint(s.seg(px_ + lean * 0.5, 6, px_ - lean * 3, 1.5, 3.0, 2.0), WEATH, 0.6, edge=1)
        s.paint(s.seg(px_ + lean * 0.5, 9, px_ + lean * 4.5, 3.5, 3.0, 2.0), WEATH, 0.7, edge=1)
    for (sx, sy, rx, ry, tone) in ((7, 92, 5.5, 3.2, 0.5), (15, 93, 4.5, 2.6, 0.65), (81, 92, 5.5, 3.2, 0.55), (89, 93, 4, 2.6, 0.7)):
        s.paint(s.ell(sx, sy, rx, ry), STONE, 0.3 + tone * 0.6 - 0.3 * (yc - sy) / ry * 0.5, edge=1)
    u = np.clip((xc - 10) / 76.0, 0, 1)
    ropey = 15 + 9 * np.clip(np.sin(np.pi * u), 0, 1) ** 1.2
    hem = 62 + 11 * np.sin(np.pi * u) + 4 * np.sin(u * 17) + 3 * np.sin(u * 6.3 + 1)
    netm = (yc > ropey) & (yc < hem) & (xc > 11) & (xc < 85)
    holes = s.ell(40, 46, 7, 6) | s.ell(66, 55, 6, 5) | s.ell(24, 40, 3.5, 3.5)
    P = 6
    lat = ((np.floor(xc) + np.floor(yc)) % P < 1.5) | ((np.floor(xc) - np.floor(yc)) % P < 1.5)
    net = netm & lat & ~holes
    # a heavier, darker second layer on the folds
    fold = vnoise(96, 96, 14, 10, 51) > 0.55
    shade = 0.58 + 0.18 * (xc < 40) - 0.2 * fold
    s.fill(shift(net, 1, 1) & ~net, "#4a3a1c")
    s.paint(net, HEMP, shade, edge=0)
    knots = netm & ~holes & ((np.floor(xc) + np.floor(yc)) % P < 1) & ((np.floor(xc) - np.floor(yc)) % P < 1)
    s.fill(knots, "#e0d094")
    # top rope, corks and lead weights
    s.paint(s.path([(10, 14.5), (28, 20.5), (48, 24), (68, 20.5), (86, 14.5)], 3.0), HEMP, 0.6, edge=1)
    for cxk in range(14, 84, 9):
        uu = (cxk - 10) / 76.0
        cy = 15 + 9 * math.sin(math.pi * uu) ** 1.2 + 3.5
        s.paint(s.ell(cxk, cy, 3.1, 2.8), CORK, s.lit(cxk, cy, 3.1, 2.8, 0.6, 0.6), edge=1)
    for wx in range(16, 82, 11):
        uu = (wx - 10) / 76.0
        hy = 62 + 11 * math.sin(math.pi * uu) + 4 * math.sin(uu * 17) + 3 * math.sin(uu * 6.3 + 1)
        s.paint(s.ell(wx, hy + 1.5, 2.0, 2.2), IRON, 0.6, edge=1)
    return s.rgba()


def thing_fishrack() -> np.ndarray:
    s = Spr(96, 72)
    # frame
    for px_ in (6, 48, 90):
        s.paint(s.seg(px_, 70, px_, 3, 5.0, 4.5), WEATH, s.cyl(px_, 2.5, 0.15, 0.9), edge=1)
    for px_, d in ((6, 1), (90, -1)):
        s.paint(s.seg(px_ + d * 10, 70, px_ + d * 1, 50, 3.0), WEATH, 0.55, edge=1)
    rails = (9, 27, 45)
    for ry in rails:
        s.paint(s.rect(1, ry - 1.5, 95, ry + 1.5), WEATH, s.vgrad(ry - 1.5, ry + 1.5, 0.85, 0.35), edge=1)
    rng = np.random.RandomState(14)
    for ri, ry in enumerate(rails):
        for i in range(10):
            fx = 13 + i * 7.9 + (ri % 2) * 3
            if i == 9 and ri % 2:
                continue
            L = 11 + rng.rand() * 2.5
            cy = ry + 1.5 + L * 0.5
            body = s.ell(fx, cy + 1, 2.7, L * 0.5 - 1.5)
            tail = s.poly([(fx - 1, ry + 1.5), (fx + 1, ry + 1.5), (fx + 2.3, ry + 4.2), (fx - 2.3, ry + 4.2)])
            s.paint(body, SILVER, s.hgrad(fx - 2.7, fx + 2.7, 0.98, 0.3) - 0.12 * (s.yc < cy - L * 0.2) * 0.5, edge=1)
            s.paint(tail, SILVER, 0.45, edge=1)
            s.dot(int(fx), int(cy + L * 0.5 - 2.2), "#2a3038")
            s.fill(s.rect(fx + 0.4, cy - 1, fx + 1.5, cy + 2), "#56677a")
    return s.rgba()


def wicker_basket(s: Spr, cx, rim_y, rim_rx, base_y, base_rx, rim_ry, handles=True) -> None:
    body = s.vase(cx, [(rim_y, rim_rx), (rim_y + (base_y - rim_y) * 0.35, rim_rx * 0.93), (base_y - 2, base_rx), (base_y, base_rx * 0.8)])
    if handles:
        for sd in (-1, 1):
            hx_ = cx + sd * (rim_rx + 0.5)
            ring = s.ell(hx_, rim_y - 1, 3.4, 5.2) & ~s.ell(hx_, rim_y - 1, 1.6, 3.4)
            s.paint(ring, WICKER, 0.6, edge=1)
    s.paint(s.ell(cx, rim_y, rim_rx + 0.5, rim_ry + 0.5), WICKER, 0.55, edge=1)
    s.paint(s.ell(cx, rim_y + 0.5, rim_rx - 2.2, rim_ry - 1.3), WICKER, 0.0, edge=0)
    s.fill(s.ell(cx, rim_y + 0.6, rim_rx - 2.4, rim_ry - 1.4), "#3e2c18")
    u = np.clip((s.xc - cx) / base_rx, -1.2, 1.2)
    wv = wicker_shade(s, 3, 4, 0.55, 0.3, rim_y)
    s.paint(body & (s.yc > rim_y), WICKER, wv + 0.28 - 0.38 * (u + 1) / 2 * 1.0, edge=1)


def thing_basket() -> np.ndarray:
    s = Spr(40, 40)
    wicker_basket(s, 20, 12, 15.5, 40, 10.5, 4.6)
    # front lip over the interior
    lip = s.ell(20, 12, 16, 5.2) & ~s.ell(20, 12, 13.4, 3.4) & (s.yc > 12)
    s.paint(lip, WICKER, 0.78, edge=0)
    s.paint(s.rect(5, 12, 35, 15) & s.vase(20, [(12, 15.5), (40, 10.5)]), WICKER, 0.75, edge=0)
    return s.rgba()


def thing_basket_full() -> np.ndarray:
    s = Spr(48, 48)
    wicker_basket(s, 24, 27, 18.5, 48, 12.5, 5.2, handles=False)
    # back half of the rim is already there; pile the loaves and fish, then the front lip over them
    for (lx, ly, rx, ry) in ((16, 22, 8.5, 4.6), (32, 22, 8.5, 4.6), (24, 17, 8.5, 4.8), (11, 14.5, 7, 4), (36, 15, 7, 4), (24, 10, 8, 4.6)):
        loaf(s, lx, ly, rx, ry)
    fish_diag(s, 35, 24, 9, -0.55)
    fish_diag(s, 13, 25, 9, 3.6)
    fish_diag(s, 22, 25, 9, -1.1)
    lip = s.ell(24, 27, 19, 5.6) & ~s.ell(24, 27, 17, 3.5) & (s.yc > 27)
    s.paint(lip, WICKER, 0.78, edge=0)
    s.paint(s.rect(5.5, 27, 42.5, 30) & s.vase(24, [(27, 18.5), (48, 12.5)]), WICKER, 0.75, edge=0)
    return s.rgba()


def thing_table() -> np.ndarray:
    s = Spr(128, 64)
    table_slab(s, 3, 125, 64 - 44)
    return s.rgba()


def clay_bowl(s: Spr, cx, by, rx, ry_h, content=None) -> None:
    """A clay bowl standing on y = by: a half-round body under an elliptical rim, optionally filled."""
    body = s.vase(cx, [(by - ry_h, rx), (by - ry_h * 0.45, rx * 0.86), (by - 0.5, rx * 0.5)])
    s.paint(body, CLAY, s.cyl(cx, rx, 0.12, 0.95), edge=1)
    s.paint(s.ell(cx, by - ry_h, rx + 0.3, 2.0), CLAY, 0.75, edge=1)
    if content:
        s.fill(s.ell(cx, by - ry_h + 0.2, rx - 1.6, 1.1), content)


def jug(s: Spr, cx, by, h, w, pal=CLAY) -> None:
    body = s.vase(cx, [(by - h, w * 0.3), (by - h * 0.78, w * 0.26), (by - h * 0.5, w * 0.5), (by - h * 0.2, w * 0.42), (by - 0.6, w * 0.3)])
    hd = s.ell(cx + w * 0.52, by - h * 0.55, w * 0.34, h * 0.28) & ~s.ell(cx + w * 0.52, by - h * 0.55, w * 0.17, h * 0.17) & (s.xc > cx + w * 0.2)
    s.paint(hd, pal, 0.5, edge=1)
    s.paint(body, pal, s.cyl(cx, w * 0.5, 0.12, 0.95), edge=1)
    s.fill(s.rect(cx - w * 0.3, by - h * 0.62, cx + w * 0.3, by - h * 0.6), "#5a2e1a")


def oil_lamp(s: Spr, cx, by) -> None:
    s.paint(s.poly([(cx - 5, by), (cx + 4, by), (cx + 6, by - 3), (cx - 6, by - 4)]), CLAY, 0.6, edge=1)
    s.paint(s.poly([(cx + 4, by - 3), (cx + 9, by - 5), (cx + 9, by - 4), (cx + 5, by - 1)]), CLAY, 0.6, edge=1)
    s.paint(s.ell(cx - 1, by - 4.2, 5, 1.6), CLAY, 0.8, edge=1)
    s.fill(s.ell(cx + 9, by - 8.5, 1.5, 3.2), "#f08c2c")
    s.fill(s.ell(cx + 9, by - 8, 0.8, 2), "#fff0a8")


def cup(s: Spr, cx, by, w=5.0, h=6.0) -> None:
    body = s.vase(cx, [(by - h, w * 0.55), (by - h * 0.3, w * 0.45), (by - 0.5, w * 0.35)], lin=True)
    s.paint(body, CLAY, s.cyl(cx, w * 0.55, 0.15, 0.95), edge=1)
    s.fill(s.rect(cx - w * 0.45, by - h, cx + w * 0.45, by - h + 1), "#3a2012")


def thing_table_meal() -> np.ndarray:
    s = Spr(128, 72)
    top = table_slab(s, 3, 125, 72 - 44)
    clay_bowl(s, 20, top, 8.5, 7, "#7a8c3c")
    for (lx, ly, rx) in ((38, top - 3.6, 9), (36, top - 9.0, 8), (52, top - 3, 8.5)):
        loaf(s, lx, ly, rx, 4.2)
    oil_lamp(s, 68, top)
    jug(s, 86, top, 20, 14)
    cup(s, 100, top, 5.2, 6.5)
    cup(s, 107, top, 5.2, 6.5)
    clay_bowl(s, 117, top, 7, 6, "#a08040")
    return s.rgba()


def coin_stack(s: Spr, cx, by, n, w=8, bronze=True) -> None:
    for i in range(n):
        y0 = by - (i + 1) * 2.0
        pal = BRONZE if (bronze ^ (i % 3 == 2)) else SILVER
        s.paint(s.rect(cx - w / 2, y0, cx + w / 2, y0 + 2.0), pal, s.hgrad(cx - w / 2, cx + w / 2, 0.95, 0.4), edge=0)
        s.fill(s.rect(cx - w / 2, y0 + 1.5, cx + w / 2, y0 + 2.0), "#5e4018" if pal is BRONZE else "#56677a")
    top = by - n * 2.0
    s.paint(s.ell(cx, top, w / 2, 1.3), BRONZE if bronze else SILVER, 0.95, edge=0)


def balance(s: Spr, cx, by) -> None:
    s.paint(s.rect(cx - 5, by - 2, cx + 5, by), BRONZE, 0.5, edge=1)
    s.paint(s.rect(cx - 1, by - 22, cx + 1, by - 2), BRONZE, 0.6, edge=1)
    s.paint(s.seg(cx - 14, by - 23, cx + 14, by - 25, 2.0), BRONZE, 0.8, edge=1)
    s.paint(s.ell(cx, by - 24, 2.2, 2.2), BRONZE, 0.9, edge=1)
    for sx, sy in ((cx - 14, by - 23), (cx + 14, by - 25)):
        pyy = sy + 8
        s.fill(s.seg(sx, sy, sx - 6, pyy, 0.9) | s.seg(sx, sy, sx + 6, pyy, 0.9), "#8a5e26")
        s.paint(s.poly([(sx - 7, pyy), (sx + 7, pyy), (sx + 4, pyy + 2.6), (sx - 4, pyy + 2.6)]), BRONZE, 0.75, edge=1)


def thing_table_coins() -> np.ndarray:
    s = Spr(112, 72)
    H = 72
    tt = H - 42
    gy = H - 1
    for xc in (18, 94):
        s.paint(s.seg(xc - 3, tt + 10, xc - 11, gy, 5.5, 5), WEATH, 0.6 * s.cyl(xc, 14, 0.2, 0.9) + 0.1, edge=1)
        s.paint(s.seg(xc + 3, tt + 10, xc + 11, gy, 5.5, 5), WEATH, 0.6 * s.cyl(xc, 14, 0.2, 0.9) + 0.1, edge=1)
        s.paint(s.rect(xc - 8, gy - 14, xc + 8, gy - 11), WEATH, 0.45, edge=1)
    # cloth: lit top, a hanging front with folds, ochre border, scalloped hem and tassels
    s.paint(s.rect(3, tt - 4, 109, tt), RED, 0.85, edge=2)
    fold = 0.55 + 0.22 * np.sin(s.xc * 0.62) + 0.1 * np.sin(s.xc * 1.7)
    hem = tt + 12 + 1.6 * np.abs(np.sin(s.xc * 0.55))
    front = (s.xc > 2) & (s.xc < 110) & (s.yc >= tt) & (s.yc < hem)
    s.paint(front, RED, fold - 0.12 * (s.yc - tt) / 12.0, edge=1)
    s.paint(front & (s.yc > tt + 2) & (s.yc < tt + 4), OCHRE, 0.72, edge=0)
    s.paint(front & (s.yc > tt + 8) & (s.yc < tt + 9.6), OCHRE, 0.6, edge=0)
    for tx in range(6, 108, 6):
        yy = tt + 12.5 + 1.6 * abs(math.sin(tx * 0.55))
        s.fill(s.rect(tx, yy, tx + 1.3, yy + 3), "#dcb64e")
    top = tt - 1.5
    coin_stack(s, 14, top, 5, 8, True)
    coin_stack(s, 25, top, 3, 8, False)
    coin_stack(s, 36, top, 7, 8, True)
    coin_stack(s, 48, top, 4, 8, False)
    coin_stack(s, 58, top, 2, 8, True)
    balance(s, 84, top)
    for (lx, ly, col) in ((66, top + 0.5, BRONZE), (70, top - 1, SILVER), (100, top, BRONZE), (104, top + 0.8, SILVER)):
        s.paint(s.ell(lx + 3, ly, 3.1, 1.3), col, 0.9, edge=1)
    return s.rgba()


def thing_table_over() -> np.ndarray:
    """The table knocked over onto its back and canted: the slab lies on the ground tilted up to the right, both trestles stick up and out, coins and a bowl have rolled away."""
    s = Spr(128, 72)
    th = math.radians(11)
    d = (math.cos(th), -math.sin(th))
    n = (-math.sin(th), -math.cos(th))
    ox, oy = 7.0, 68.0

    def P(u, v):
        return (ox + u * d[0] + v * n[0], oy + u * d[1] + v * n[1])
    for (u0, tone) in ((86, 0.5), (22, 0.62)):
        a1, a2 = P(u0 - 5, 6), P(u0 + 5, 6)
        b1, b2 = P(u0 - 13, 41), P(u0 + 13, 41)
        s.paint(s.seg(a1[0], a1[1], b1[0], b1[1], 6.0, 5.0), WEATH, tone * 0.9 + 0.1, edge=1)
        s.paint(s.seg(a2[0], a2[1], b2[0], b2[1], 6.0, 5.0), WEATH, tone + 0.2, edge=1)
        c1, c2 = P(u0 - 9, 26), P(u0 + 9, 26)
        s.paint(s.seg(c1[0], c1[1], c2[0], c2[1], 3.4), WEATH, 0.5, edge=1)
    e1, e2 = P(22, 22), P(86, 22)
    s.paint(s.seg(e1[0], e1[1], e2[0], e2[1], 4.2), WEATH, 0.7, edge=1)
    slab = s.poly([P(-2, 0), P(112, 0), P(112, 8), P(-2, 8)])
    nz = vnoise(72, 128, 14, 2, 33)
    s.paint(slab, WEATH, 0.62 + (nz - 0.5) * 0.4 + 0.2 * (n[0] * 0 + 1) * (s.yc < 0), edge=1)
    for uu in (30, 62, 92):
        a, b = P(uu, 0), P(uu, 8)
        s.fill(s.seg(a[0], a[1], b[0], b[1], 1.1), "#4a4036")
    a, b = P(0, 4), P(110, 4)
    s.fill(s.seg(a[0], a[1], b[0], b[1], 0.9), "#6e6250")
    for (cx, cy, pal) in ((8, 71, BRONZE), (15, 70, SILVER), (24, 71, BRONZE), (40, 70, SILVER), (52, 71, BRONZE), (66, 70, BRONZE),
                          (78, 71, SILVER), (92, 70, BRONZE), (100, 71, SILVER)):
        s.paint(s.ell(cx, cy, 3.2, 1.3), pal, 0.9, edge=1)
    for (cx, cy) in ((34, 68), (72, 66), (108, 67)):
        s.paint(s.ell(cx, cy, 2.8, 2.8), BRONZE, s.lit(cx, cy, 2.8, 2.8, 0.7, 0.6), edge=1)
    bowl = s.poly([(104, 71), (126, 71), (124, 58), (112, 56)]) & ~s.ell(126, 64, 5, 8)
    s.paint(bowl, CLAY, s.hgrad(104, 126, 0.95, 0.3), edge=1)
    s.paint(s.ell(113, 61, 10, 4.4), CLAY, 0.75, edge=1)
    s.fill(s.ell(113, 61.5, 7.6, 2.8), "#3a2012")
    return s.rgba()


def thing_lantern() -> np.ndarray:
    s = Spr(32, 56)
    s.paint(s.seg(16, 54, 16, 22, 5.0, 4.0), WOOD, s.cyl(16, 2.5, 0.15, 0.9), edge=1)
    s.paint(s.rect(10, 53, 22, 56), WEATH, 0.6, edge=1)
    s.paint(s.rect(10, 20, 22, 23), IRON, 0.6, edge=1)
    glass = s.poly([(10, 21), (22, 21), (23, 9), (9, 9)])
    gl = 1.0 - np.hypot((s.xc - 16) / 9.0, (s.yc - 15.5) / 8.0)
    s.paint(glass, OCHRE, 0.45 + gl * 0.6, edge=1)
    s.fill(s.ell(16, 15.5, 2.2, 3.4), "#fff0a8")
    s.fill(s.ell(16, 17, 1.2, 2.2), "#fffbd8")
    for fx in (9.5, 16, 22.5):
        s.paint(s.rect(fx - 0.7, 9, fx + 0.7, 21), IRON, 0.5, edge=0)
    s.paint(s.poly([(7, 9), (25, 9), (21, 4), (11, 4)]), IRON, s.vgrad(4, 9, 0.8, 0.4), edge=1)
    s.paint(s.ell(16, 2.4, 3.2, 2.4) & ~s.ell(16, 2.8, 1.4, 1.2), IRON, 0.6, edge=1)
    return s.rgba()


def donkey(s: Spr, ox, gy, k, panniers=True, bundle=True, pal=DONK) -> None:
    """A grey donkey in side view facing right (units: ground at 0, ~74 tall), drawn through a scale k."""
    f = Xf(s, ox, gy, k)
    # far legs first (darker)
    for (x0, x1) in ((9, 8), (-22, -21)):
        s.paint(f.path([(x0, -26), (x1 + 1, -12), (x1, 0)], 5.0, 3.6), pal, 0.28, edge=1)
        s.paint(f.rect(x1 - 2.2, -3.6, x1 + 2.2, 0), IRON, 0.35, edge=0)
    # tail
    s.paint(f.path([(-25, -40), (-30, -30), (-29, -19)], 3.0, 2.6), pal, 0.3, edge=1)
    s.paint(f.ell(-29, -17, 2.6, 4.4), IRON, 0.35, edge=1)
    # body and neck
    body = f.ell(-1, -33, 26, 12.5) | f.poly([(14, -42), (24, -60), (33, -57), (31, -34)])
    s.paint(body, pal, f.light(-1, -33, 26, 15, 0.52, 0.6) + 0.1 * (s.yc > f.Y(-28)) * 0, edge=1)
    s.paint(f.ell(2, -25, 20, 4.5) & body, pal, 0.8, edge=0)
    # head, muzzle, ears, mane
    s.paint(f.path([(28, -56), (36, -53), (42, -46)], 10.0, 7.0), pal, f.light(36, -52, 10, 8, 0.55, 0.5), edge=1)
    s.paint(f.ell(43, -45, 5.2, 4.4), pal, 0.85, edge=1)
    s.paint(f.poly([(25, -59), (24, -75), (30, -73), (31, -59)]), pal, 0.4, edge=1)
    s.paint(f.poly([(29, -58), (31, -72), (35, -70), (34, -56)]), pal, 0.55, edge=1)
    s.fill(f.poly([(27, -61), (26, -72), (28, -71), (29, -61)]), "#b88c86")
    s.fill(f.path([(15, -45), (24, -59), (30, -58)], 2.6, 2.0), "#46444a")
    s.dot(int(f.X(37)), int(f.Y(-54)), "#2a2018")
    s.dot(int(f.X(46)), int(f.Y(-46)), "#46444a")
    # blanket + load
    if panniers:
        s.paint(f.rect(-14, -48, 8, -38), RED, 0.55, edge=1)
        s.fill(f.rect(-14, -45, 8, -44), "#dcb64e")
        for (bx, by_) in ((-14, -2), ):
            bm = f.rect(-17, -43, 5, -12)
            wv = wicker_shade(s, 3, 4, 0.5, 0.3, f.Y(-43))
            s.paint(bm, WICKER, wv + 0.15 + 0.1 * (s.xc < f.X(-6)), edge=1)
            s.paint(f.rect(-17, -43, 5, -40), WICKER, 0.8, edge=1)
            s.fill(f.rect(-13, -45, -11.5, -12), "#8e7a46")
            s.fill(f.rect(-1.5, -45, 0, -12), "#8e7a46")
    if bundle:
        s.paint(f.ell(-4, -52, 14, 7.5), WOOL, f.light(-4, -52, 14, 8, 0.6, 0.6), edge=1)
        s.fill(f.rect(-5, -59, -3, -46), "#8e7a46")
    # near legs
    for (x0, x1) in ((17, 16), (-14, -12)):
        s.paint(f.path([(x0, -28), (x1 - 0.5, -13), (x1, 0)], 5.6, 3.8), pal, s.cyl(f.X(x0), 3, 0.2, 0.95) * 0.7 + 0.15, edge=1)
        s.paint(f.rect(x1 - 2.4, -3.8, x1 + 2.4, 0), IRON, 0.4, edge=0)


def thing_donkey() -> np.ndarray:
    s = Spr(96, 80)
    donkey(s, 42, 79, 1.0)
    return s.rgba()


def camel(s: Spr, ox, gy, k, load=True) -> None:
    """A one-humped camel in side view facing right (units: ground at 0, ~80 tall)."""
    f = Xf(s, ox, gy, k)
    pal = CAMEL
    for (x0, x1) in ((8, 9), (-20, -19)):
        s.paint(f.path([(x0, -30), (x0 + 2, -16), (x1, 0)], 5.6, 3.4), pal, 0.28, edge=1)
    s.paint(f.path([(-28, -46), (-33, -36), (-32, -26)], 3.2, 2.2), pal, 0.35, edge=1)
    body = f.ell(-1, -40, 27, 12.5) | f.ell(-18, -39, 10, 13)
    s.paint(body, pal, f.light(-1, -40, 27, 15, 0.52, 0.6), edge=1)
    s.paint(f.ell(-5, -55, 9.5, 9), pal, f.light(-5, -56, 9, 9, 0.6, 0.6), edge=1)
    s.paint(f.path([(18, -46), (24, -56), (28, -64), (32, -70)], 11.0, 6.0), pal, f.light(25, -58, 9, 14, 0.52, 0.5), edge=1)
    s.paint(f.path([(31, -72), (39, -72), (47, -68)], 8.0, 5.5), pal, f.light(38, -72, 9, 5, 0.55, 0.5), edge=1)
    s.paint(f.ell(47, -68, 3.4, 3.0), pal, 0.8, edge=1)
    s.paint(f.poly([(30, -75), (29, -81), (33, -76)]), pal, 0.4, edge=1)
    s.dot(int(f.X(37)), int(f.Y(-73.5)), "#2a2018")
    if load:
        s.paint(f.ell(-5, -64, 15, 8.5), CLOTH, f.light(-5, -64, 15, 9, 0.58, 0.55), edge=1)
        s.paint(f.poly([(-17, -50), (9, -50), (11, -33), (-18, -33)]), RED, 0.5 + 0.12 * (np.floor((s.xc - ox) / max(3 * k, 1)) % 2), edge=1)
        s.fill(f.rect(-18, -46, 10, -44.5), "#dcb64e")
        s.paint(f.ell(-17, -29, 6.5, 8.5), WOOL, f.light(-17, -29, 6.5, 8.5, 0.6, 0.6), edge=1)
        s.paint(f.ell(10, -29, 6.5, 8.5), WOOL, f.light(10, -29, 6.5, 8.5, 0.6, 0.6), edge=1)
    for (x0, x1) in ((15, 14), (-16, -15)):
        s.paint(f.path([(x0, -30), (x0 + 2, -16), (x1, 0)], 6.0, 3.6), pal, s.cyl(f.X(x0 + 1), 3, 0.2, 0.95) * 0.7 + 0.15, edge=1)
        s.paint(f.rect(x1 - 2.8, -3.0, x1 + 2.8, 0), TAN, 0.3, edge=0)


def thing_caravan() -> np.ndarray:
    s = Spr(224, 96)
    # far to near along the line: small and hazy, so the animals are drawn in a few scales and washed toward the dust colour afterwards
    camel(s, 28, 95, 0.76)
    donkey(s, 76, 95, 0.66, panniers=True, bundle=True)
    camel(s, 122, 95, 0.74)
    donkey(s, 162, 95, 0.62, panniers=True, bundle=False)
    camel(s, 194, 95, 0.58)
    haze = hx("#d8c6a0")
    m = s.a
    s.rgb[m] = ((s.rgb[m].astype(np.float32) / 255 * 0.66 + haze * 0.34) * 255 + 0.5).astype(np.uint8)
    return s.rgba()


def straw_strokes(s: Spr, mask, n, seed, ang=0.0, spread=0.5, L0=4.0, L1=7.0, pal=STRAW, lo=1) -> None:
    """Short straw strokes at random places inside a mask (the hay look)."""
    rng = np.random.RandomState(seed)
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return
    for _ in range(n):
        i = rng.randint(len(ys))
        x, y = xs[i] + 0.5, ys[i] + 0.5
        a = ang + (rng.rand() - 0.5) * 2 * spread
        L = L0 + rng.rand() * (L1 - L0)
        c = pal[lo + rng.randint(len(pal) - lo)]
        m = s.seg(x, y, x + math.cos(a) * L, y + math.sin(a) * L, 1.2) & mask
        s.rgb[m] = (c * 255 + 0.5).astype(np.uint8)


def spoke_wheel(s: Spr, cx, cy, r) -> None:
    ring = s.ell(cx, cy, r, r)
    s.paint(ring, IRON, 0.5, edge=1)
    s.paint(s.ell(cx, cy, r - 2.2, r - 2.2), WOOD, 0.5, edge=1)
    inner = s.ell(cx, cy, r - 5.0, r - 5.0)
    s.a &= ~inner
    for i in range(8):
        a = i * math.pi / 4 + 0.2
        sp = s.seg(cx, cy, cx + math.cos(a) * (r - 3), cy + math.sin(a) * (r - 3), 3.0, 2.4)
        s.paint(sp, WOOD, 0.58 + 0.2 * math.cos(a - 2.3), edge=1)
    s.paint(s.ell(cx, cy, 4.6, 4.6), WOOD, s.lit(cx, cy, 5, 5, 0.6, 0.7), edge=1)
    s.paint(s.ell(cx, cy, 1.6, 1.6), IRON, 0.5, edge=0)


def thing_cart() -> np.ndarray:
    s = Spr(128, 96)
    for (y0, y1, tone) in ((61, 93, 0.5), (57, 90, 0.68)):
        s.paint(s.seg(40, y0, 3, y1, 4.6, 3.6), WOOD, tone, edge=1)
    nz = vnoise(96, 128, 12, 2, 61)
    bed = s.rect(24, 46, 106, 64)
    s.paint(bed, WOOD, 0.56 + (nz - 0.5) * 0.4 - 0.2 * (s.yc > 60), edge=1)
    for yy in (51, 56, 60):
        s.fill(s.rect(24, yy, 106, yy + 1), "#3e2a1c")
    s.paint(s.rect(24, 62, 106, 66), DWOOD, 0.5, edge=1)
    for xx in (30, 100):
        s.paint(s.rect(xx - 2, 40, xx + 2, 64), DWOOD, 0.55, edge=1)
    mound = (s.ell(64, 44, 43, 21) & (s.yc < 49)) | s.rect(28, 44, 100, 49)
    base = 0.28 + 0.3 * s.lit(64, 44, 43, 21, 0.4, 0.55) - 0.14 * (vnoise(96, 128, 7, 5, 62) > 0.55)
    s.paint(mound, HEMP, base, edge=1)
    lat = ((np.floor(s.xc) + np.floor(s.yc)) % 5 < 1.2) | ((np.floor(s.xc) - np.floor(s.yc)) % 5 < 1.2)
    s.paint(mound & lat, HEMP, 0.74 - 0.25 * (vnoise(96, 128, 9, 6, 63) > 0.55), edge=0)
    drape = s.poly([(96, 44), (108, 46), (110, 70), (104, 74), (99, 62)])
    s.paint(drape, HEMP, 0.3, edge=1)
    s.paint(drape & lat, HEMP, 0.74, edge=0)
    for (cx, cy) in ((30, 36), (44, 26), (58, 22), (74, 26), (88, 34), (50, 33), (67, 31), (81, 40), (37, 43), (104, 52), (106, 62)):
        s.paint(s.ell(cx, cy, 3.4, 3.1), CORK, s.lit(cx, cy, 3.4, 3.1, 0.6, 0.6), edge=1)
    s.paint(s.path([(28, 40), (50, 28), (72, 28), (96, 40)], 1.8), HEMP, 0.35, edge=0)
    spoke_wheel(s, 64, 76, 20)
    s.paint(s.rect(60, 66, 68, 70), IRON, 0.5, edge=1)
    out = s.rgba()
    return np.roll(out, 8, axis=1)


def thing_brazier() -> np.ndarray:
    s = Spr(40, 64)
    for (x0, x1, tone) in ((11, 4.5, 0.38), (29, 35.5, 0.38), (20, 20, 0.6)):
        s.paint(s.seg(x0, 41, x1, 62, 3.4, 3.0), IRON, tone, edge=1)
    s.paint(s.seg(8, 53, 32, 53, 1.8), IRON, 0.5, edge=1)
    for fx in (4.5, 20, 35.5):
        s.paint(s.ell(fx, 62.5, 2.4, 1.2), IRON, 0.5, edge=0)
    bowl = s.vase(20, [(30, 17.5), (36, 15), (42, 6.5)])
    s.paint(bowl, IRON, s.cyl(20, 17, 0.12, 0.8), edge=1)
    s.paint(s.ell(20, 30, 17.8, 3.4), IRON, 0.7, edge=1)
    emb = s.ell(20, 30.2, 15.8, 2.4)
    s.paint(emb, FLAME, 0.2 + 0.5 * vnoise(64, 40, 3, 2, 71), edge=0)
    flame(s, 20, 30, 27, 22, seed=5)
    return s.rgba()


def thing_torch() -> np.ndarray:
    s = Spr(24, 64)
    s.paint(s.seg(12, 63, 12, 24, 4.4, 3.4), WOOD, s.cyl(12, 2.2, 0.15, 0.95), edge=1)
    head = s.ell(12, 27, 5.4, 7.2)
    s.paint(head, TENT, s.lit(12, 27, 5.4, 7.2, 0.5, 0.6), edge=1)
    for yy in (23.5, 27.5, 31):
        s.paint(s.rect(6.6, yy, 17.4, yy + 1.4) & head, HEMP, 0.5, edge=0)
    flame(s, 12, 23, 20, 13, seed=9)
    return s.rgba()


def thing_bowl_set() -> np.ndarray:
    s = Spr(48, 56)
    s.paint(s.seg(5, 33, 24, 54.5, 3.6, 3.2), WOOD, 0.45, edge=1)
    s.paint(s.seg(24, 33, 5, 54.5, 3.6, 3.2), WOOD, 0.62, edge=1)
    s.paint(s.rect(2, 53, 28, 56), WOOD, 0.5, edge=1)
    s.paint(s.rect(3, 31, 26, 34), WOOD, s.vgrad(31, 34, 0.9, 0.4), edge=1)
    body = s.vase(14.5, [(24, 15.5), (28, 14), (34, 7)])
    s.paint(body, TAN, s.cyl(14.5, 15, 0.12, 0.95), edge=1)
    s.paint(s.ell(14.5, 24, 16, 3.6), TAN, 0.8, edge=1)
    s.paint(s.ell(14.5, 24.4, 13.4, 2.4), WATER, 0.7 + 0.2 * np.sin(s.xc * 1.3), edge=0)
    s.fill(s.rect(10, 24, 15, 25), "#b4d8ec")
    s.fill(s.rect(19, 23, 22, 24), "#80b4d8")
    s.paint(s.poly([(1.5, 24), (6, 24), (7, 38), (2.5, 40)]), WOOL, 0.55 + 0.2 * (np.floor(s.xc) % 2), edge=1)
    jug(s, 36, 55, 27, 13, TAN)
    return s.rgba()


def thing_bench() -> np.ndarray:
    s = Spr(96, 40)
    for (x0, x1) in ((12, 8), (82, 86)):
        s.paint(s.seg(x0, 22, x1, 39, 8.5, 9.5), WEATH, s.cyl(x0, 5.5, 0.1, 0.85) * 0.8 + 0.1, edge=1)
    s.paint(s.rect(14, 30, 80, 34), WEATH, 0.45, edge=1)
    nz = vnoise(40, 96, 14, 2, 81)
    s.paint(s.rect(4, 13, 93, 17), WEATH, 0.8 + (nz - 0.5) * 0.4, edge=2)
    seat = s.rect(1, 17, 95, 25)
    s.paint(seat, WEATH, 0.58 + (nz - 0.5) * 0.4 - 0.15 * (s.yc > 22), edge=1)
    s.fill(s.rect(1, 17, 3, 25), "#675a4a")
    s.fill(s.rect(93, 17, 95, 25), "#675a4a")
    s.fill(s.rect(58, 17, 59, 22), "#4a4036")
    for (kx, ky) in ((26, 21), (76, 22)):
        s.fill(s.ell(kx, ky, 1.6, 1.0), "#4a4036")
    for nx_ in (12, 82):
        s.dot(nx_, 20, "#a39379")
    return s.rgba()


def thing_stool() -> np.ndarray:
    s = Spr(32, 32)
    s.paint(s.seg(8.5, 14, 4.5, 31, 3.6, 3.0), WEATH, 0.45, edge=1)
    s.paint(s.seg(23.5, 14, 27.5, 31, 3.6, 3.0), WEATH, 0.7, edge=1)
    s.paint(s.seg(16, 14, 16, 31, 4.0, 3.4), WEATH, s.cyl(16, 2, 0.15, 0.9), edge=1)
    s.paint(s.rect(3, 9, 29, 14) & (s.ell(16, 9, 13, 5.5) | s.rect(3, 9, 29, 13)), WEATH, s.cyl(16, 13, 0.15, 0.85) * 0.8 + 0.12, edge=1)
    s.paint(s.ell(16, 9.2, 13, 3.0), WEATH, 0.82, edge=1)
    s.paint(s.ell(16, 9.2, 12.6, 2.7), WEATH, 0.85 + 0.1 * (vnoise(32, 32, 3, 3, 91) - 0.5), edge=0)
    return s.rgba()


def thing_hay() -> np.ndarray:
    s = Spr(64, 48)
    bale = s.rect(25, 13, 62, 48)
    s.paint(bale, STRAW, 0.45 + 0.25 * (vnoise(48, 64, 5, 5, 101) - 0.5) - 0.22 * (s.yc > 42), edge=1)
    straw_strokes(s, bale, 170, 102, 0.0, 0.5, 4, 8, STRAW, 0)
    s.paint(s.rect(25, 9, 62, 15), STRAW, 0.9, edge=2)
    straw_strokes(s, s.rect(26, 9, 61, 15), 40, 103, 0.0, 0.3, 3, 6, STRAW, 2)
    for bx in (35, 53):
        s.paint(s.rect(bx, 9, bx + 2.4, 48), HEMP, 0.45, edge=1)
    heap = s.poly([(2, 48), (5, 38), (11, 30), (18, 26), (25, 31), (30, 38), (34, 48)]) | s.ell(16, 40, 15, 8)
    heap &= (s.yc < 48) & (s.xc > 1)
    s.paint(heap, STRAW, 0.5 + 0.3 * s.lit(16, 40, 16, 14, 0.4, 0.6), edge=1)
    straw_strokes(s, heap, 130, 104, -1.57, 1.0, 4, 9, STRAW, 0)
    for (x, y, a, L) in ((9, 30, -2.2, 7), (21, 26, -1.2, 7), (4, 40, 3.5, 6), (30, 36, -0.6, 6), (14, 25, -1.8, 5)):
        m = s.seg(x, y, x + math.cos(a) * L, y + math.sin(a) * L, 1.2)
        s.rgb[m] = (STRAW[3] * 255 + 0.5).astype(np.uint8)
        s.a |= m
    return s.rgba()


def thing_workbench() -> np.ndarray:
    s = Spr(128, 72)
    gy = 71
    for (x0, x1) in ((14, 12), (114, 116)):
        s.paint(s.seg(x0, 44, x1, gy, 9, 10), WOOD, s.cyl(x0, 5.5, 0.1, 0.85) * 0.8 + 0.05, edge=1)
    s.paint(s.rect(18, 58, 110, 62), WOOD, 0.45, edge=1)
    nz = vnoise(72, 128, 16, 2, 111)
    s.paint(s.rect(5, 33, 123, 37), WOOD, 0.85 + (nz - 0.5) * 0.35, edge=2)
    s.paint(s.rect(4, 37, 124, 46), WOOD, 0.58 + (nz - 0.5) * 0.35 - 0.15 * (s.yc > 43), edge=1)
    for sx in (44, 90):
        s.fill(s.rect(sx, 37, sx + 1, 46), "#3e2a1c")
    s.paint(s.rect(5, 39, 14, 55), DWOOD, 0.5, edge=1)
    s.paint(s.rect(3, 46, 11, 49), IRON, 0.6, edge=1)
    s.paint(s.rect(2, 44, 5, 51), IRON, 0.5, edge=1)
    s.paint(s.rect(22, 29.5, 74, 34), WOOD, 0.8 + (vnoise(72, 128, 12, 2, 112) - 0.5) * 0.4, edge=1)
    s.fill(s.rect(22, 33.4, 74, 34.4), "#7e5a38")
    s.paint(s.rect(22, 29.5, 24.5, 34), WOOD, 0.95, edge=0)
    s.paint(s.rect(80, 28, 104, 34.5), WOOD, s.vgrad(28, 34, 0.85, 0.45), edge=1)
    s.paint(s.rect(80, 33.6, 104, 35), IRON, 0.5, edge=0)
    s.paint(s.poly([(84, 28), (94, 28), (98, 24), (88, 23)]), WOOD, 0.75, edge=1)
    s.paint(s.poly([(97, 28), (100, 28), (101, 22), (98, 22)]), WOOD, 0.7, edge=1)
    s.fill(s.rect(90, 28, 92, 31), "#a29fa8")
    s.paint(s.seg(108, 33.2, 122, 31.6, 2.6), WOOD, 0.7, edge=1)
    s.paint(s.rect(104, 25.5, 115, 34.5), WOOD, s.vgrad(25, 34, 0.9, 0.35), edge=1)
    s.fill(s.rect(104, 28, 115, 29), "#5e4128")
    s.paint(s.poly([(121, 71), (124, 71), (114, 40), (106, 42)]), IRON, s.hgrad(106, 124, 0.9, 0.5), edge=1)
    s.fill(s.poly([(121, 70.5), (124, 70.5), (123.2, 66), (120.2, 66)]), "#a29fa8")
    s.paint(s.poly([(106, 42), (114, 40), (116, 34), (107, 35)]), DWOOD, 0.6, edge=1)
    s.fill(s.ell(111, 38.5, 1.5, 1.5), "#9c7650")
    for (cx, cy, r) in ((40, 31, 3.0), (30, 69, 3.0), (46, 66, 3.6), (58, 70, 3.0), (74, 67, 3.6), (88, 70, 3.0), (98, 66, 3.0), (66, 63, 3.0), (6, 69, 3.4),
                        (94, 31, 2.6), (60, 28, 2.4)):
        ring = s.ell(cx, cy, r, r * 0.8) & ~s.ell(cx, cy, r * 0.5, r * 0.4) & ~s.rect(cx, cy - r, cx + r + 1, cy - r * 0.1)
        s.fill(ring, "#e6d2a0")
        s.fill(ring & (s.yc > cy), "#c8aa78")
    return s.rgba()


def thing_planks() -> np.ndarray:
    s = Spr(64, 96)
    rng = np.random.RandomState(121)
    lean = 8.0
    pals = (WOOD, WEATH, WOOD, DWOOD, WEATH, WOOD, WEATH)
    for i in range(6, -1, -1):
        bx = 2 + i * 6.8
        top = 5 + rng.rand() * 14
        pm = s.poly([(bx, 92), (bx + 9, 92), (bx + 9 + lean, top), (bx + lean, top)])
        grain = vnoise(96, 64, 2.5, 22, 122 + i)
        tone = 0.5 + rng.rand() * 0.25
        s.paint(pm, pals[i], tone + (grain - 0.5) * 0.45 + 0.12 * (s.xc < bx + 3 + (92 - s.yc) * lean / 87), edge=1)
        s.fill(pm & (s.yc < top + 1.6), "#bfb094")
        if rng.rand() > 0.4:
            ky = rng.randint(30, 80)
            kx = bx + 4.5 + (92 - ky) * lean / 87
            s.fill(s.ell(kx, ky, 1.5, 2.2), "#3e2a1c")
    for (y0, x0, x1, pal) in ((83, 5, 56, WEATH), (87.5, 3, 60, WOOD)):
        s.paint(s.rect(x0, y0, x1, y0 + 4.6), pal, 0.65 + (vnoise(96, 64, 12, 2, int(y0)) - 0.5) * 0.4, edge=1)
        s.fill(s.rect(x0, y0 + 0.5, x0 + 2, y0 + 4), "#bfb094")
    s.paint(s.rect(3, 92, 60, 96), WEATH, 0.5 + (vnoise(96, 64, 10, 2, 129) - 0.5) * 0.4, edge=1)
    s.fill(s.rect(3, 92.5, 5, 95.5), "#bfb094")
    return s.rgba()


def amphora(s: Spr, cx, top, bot, rmax, pal=CLAY, handles=True, band=True) -> None:
    """A two-handled clay amphora standing on a small foot, y from top to bot (a lip, a narrow neck, a round belly)."""
    h = bot - top
    prof = [(top, rmax * 0.46), (top + h * 0.05, rmax * 0.46), (top + h * 0.075, rmax * 0.34), (top + h * 0.2, rmax * 0.3), (top + h * 0.38, rmax * 0.86),
            (top + h * 0.52, rmax), (top + h * 0.72, rmax * 0.82), (top + h * 0.9, rmax * 0.4), (bot - h * 0.04, rmax * 0.4), (bot - h * 0.02, rmax * 0.52),
            (bot, rmax * 0.52)]
    body = s.vase(cx, prof)
    if handles:
        for sd in (-1, 1):
            hnd = s.path([(cx + sd * rmax * 0.3, top + h * 0.15), (cx + sd * rmax * 0.78, top + h * 0.16), (cx + sd * rmax * 0.95, top + h * 0.34),
                          (cx + sd * rmax * 0.9, top + h * 0.42)], 2.8)
            s.paint(hnd, pal, 0.5 + 0.2 * (sd < 0), edge=1)
    s.paint(body, pal, s.cyl(cx, rmax, 0.1, 0.95), edge=1)
    s.fill(s.rect(cx - rmax * 0.5, top + h * 0.045, cx + rmax * 0.5, top + h * 0.075) & body, "#5a2e1a")
    if band:
        for (yy, col) in ((top + h * 0.5, "#4a2616"), (top + h * 0.56, "#4a2616"), (top + h * 0.7, "#dcb64e")):
            s.fill(s.rect(cx - rmax, yy, cx + rmax, yy + 1.2) & body, col)


def thing_jar() -> np.ndarray:
    s = Spr(32, 48)
    amphora(s, 16, 2, 48, 11.5, CLAY)
    return s.rgba()


def thing_jars() -> np.ndarray:
    s = Spr(64, 56)
    amphora(s, 14, 3, 56, 10.5, TAN)
    # a squat wide-mouthed storage pot
    pot = s.vase(38, [(24, 12), (26, 12.5), (31, 12), (42, 15), (53, 12.5), (56, 8.5)])
    s.paint(pot, CLAY, s.cyl(38, 15, 0.1, 0.95), edge=1)
    s.paint(s.ell(38, 24.4, 12.6, 2.6), CLAY, 0.82, edge=1)
    s.fill(s.ell(38, 25, 10, 1.8), "#3a2012")
    s.fill(s.rect(26, 38, 51, 39.2) & pot, "#4a2616")
    s.fill(s.rect(26, 42, 51, 43.2) & pot, "#dcb64e")
    # a small jug with a loop handle, mouth tied with cloth
    jug(s, 53, 56, 28, 12, TAN)
    return s.rgba()


def thing_spears() -> np.ndarray:
    s = Spr(48, 96)
    for xx in (5, 43):
        s.paint(s.rect(xx - 2, 22, xx + 2, 93), WOOD, s.hgrad(xx - 2, xx + 2, 0.9, 0.35), edge=1)
        s.paint(s.rect(xx - 3, 19.5, xx + 3, 23), WOOD, 0.8, edge=1)
    for yy in (38, 82):
        s.paint(s.rect(3, yy, 45, yy + 4), WOOD, s.vgrad(yy, yy + 4, 0.8, 0.35), edge=1)
    s.paint(s.rect(2, 92, 46, 96), WEATH, 0.55, edge=1)
    for i, xx in enumerate((14, 21.5, 29, 36.5)):
        top = 6 + (i % 2) * 3
        s.paint(s.rect(xx - 1.2, top + 10, xx + 1.2, 93), WOOD, s.hgrad(xx - 1.2, xx + 1.2, 0.95, 0.35), edge=1)
        head = s.poly([(xx, top - 1), (xx + 3.4, top + 6), (xx + 1.4, top + 12), (xx - 1.4, top + 12), (xx - 3.4, top + 6)])
        s.paint(head, BRONZE, s.hgrad(xx - 3.4, xx + 3.4, 0.95, 0.4), edge=1)
        s.fill(s.rect(xx - 0.3, top + 2, xx + 0.4, top + 10), "#ecc874")
        s.paint(s.rect(xx - 2, top + 12, xx + 2, top + 15), BRONZE, 0.5, edge=1)
        s.fill(s.rect(xx - 1.2, top + 17, xx + 1.2, top + 18), "#8e7a46")
        s.fill(s.rect(xx - 1.2, top + 19.5, xx + 1.2, top + 20.5), "#8e7a46")
    # round shield hung on the rack: planked face, bronze rim and boss, no device
    cx, cy, r = 24, 62, 15.5
    s.paint(s.ell(cx, cy, r, r), BRONZE, s.lit(cx, cy, r, r, 0.55, 0.4), edge=1)
    face = s.ell(cx, cy, r - 2.6, r - 2.6)
    s.paint(face, WOOD, 0.5 + 0.35 * (vnoise(96, 48, 14, 3, 131) - 0.5) + 0.2 * s.lit(cx, cy, r, r, 0.0, 0.5), edge=1)
    for dx in (-8, -3, 3, 8):
        s.fill(s.rect(cx + dx, cy - 11, cx + dx + 0.8, cy + 11) & face, "#3e2a1c")
    s.paint(s.ell(cx, cy, 4.6, 4.6), BRONZE, s.lit(cx, cy, 4.6, 4.6, 0.65, 0.7), edge=1)
    return s.rgba()


def thing_tent() -> np.ndarray:
    s = Spr(160, 112)
    W = 160
    # interior seen through the open front: shade, a woven mat, bedding
    inside = s.rect(17, 52, 143, 112)
    s.paint(inside, TENT, 0.2 + 0.2 * s.vgrad(52, 112, 0.0, 1.0) + 0.08 * (vnoise(112, 160, 10, 8, 141) - 0.5), edge=0)
    s.paint(s.rect(40, 100, 122, 111), CLOTH, 0.55 + 0.2 * (np.floor(s.xc / 5) % 2), edge=1)
    s.fill(s.rect(40, 104, 122, 105), "#dcb64e")
    s.paint(s.ell(100, 99, 12, 5) & (s.yc < 102), WOOL, 0.3, edge=1)
    # the roof: woven strips of goat hair sagging between the pole and the guy points
    sag = 6 * np.clip(1 - np.abs((s.xc - 80) / 76.0), 0, 1)
    roof = s.poly([(3, 64), (14, 44), (40, 26), (80, 10), (120, 26), (146, 44), (157, 64), (150, 70), (130, 62), (80, 54), (30, 62), (10, 70)])
    strip = np.floor(s.xc / 7)
    nz = vnoise(112, 160, 5, 18, 142)
    tone = 0.45 + 0.12 * np.sin(strip * 2.3) + (nz - 0.5) * 0.35
    top_lit = 0.18 * np.clip((60 - s.yc) / 50.0, 0, 1)
    s.paint(roof, TENT, tone + top_lit - 0.12 * (s.xc > 80), edge=1)
    for xx in range(7, 154, 7):
        s.fill(roof & (s.xc >= xx) & (s.xc < xx + 1) & (s.yc < 56), "#2a211b")
    # front lip (a heavier border) and side walls
    lip = s.poly([(10, 64), (30, 58), (80, 52), (130, 58), (150, 64), (150, 70), (130, 64), (80, 58), (30, 64), (10, 70)])
    s.paint(lip, TENT, 0.62 + (nz - 0.5) * 0.3, edge=1)
    s.paint(s.rect(2, 64, 17, 108), TENT, 0.4 + (nz - 0.5) * 0.3 + 0.1 * (np.floor(s.yc / 6) % 2), edge=1)
    s.paint(s.rect(143, 64, 158, 108), TENT, 0.34 + (nz - 0.5) * 0.3 + 0.1 * (np.floor(s.yc / 6) % 2), edge=1)
    s.paint(s.rect(2, 106, 158, 112), STONE, 0.4 + (nz - 0.5) * 0.5, edge=1)
    s.fill(s.rect(2, 106, 17, 112), "#6a604c")
    s.fill(s.rect(143, 106, 158, 112), "#6a604c")
    s.paint(s.rect(17, 108, 143, 112), SOIL, 0.55, edge=1)
    # the front pole, topped with a peg, and guy ropes to pegs
    s.paint(s.rect(78, 7, 82.4, 111), WOOD, s.hgrad(78, 82.4, 0.95, 0.3), edge=1)
    s.paint(s.ell(80.2, 6, 3.2, 3.0), WOOD, 0.75, edge=1)
    for (x0, y0, x1, y1) in ((5, 62, 3, 105), (155, 62, 157, 105), (22, 44, 8, 72)):
        s.fill(s.seg(x0, y0, x1, y1, 1.2), "#b09a5c")
    for (px_, py_) in ((3, 105), (157, 105)):
        s.paint(s.rect(px_ - 1.5, py_, px_ + 1.5, py_ + 6), WOOD, 0.6, edge=1)
    return s.rgba()


def thing_dais() -> np.ndarray:
    s = Spr(128, 96)
    # the platform: limestone blocks, a lit top edge, a band of deep red cloth along the front
    nz = vnoise(96, 128, 7, 5, 151)

    def blocks(x0, x1, y0, y1, rowh, seed):
        rng = np.random.RandomState(seed)
        base = s.rect(x0, y0, x1, y1)
        row = np.floor((s.yc - y0) / rowh)
        off = (row % 2) * 13
        col = np.floor((s.xc - x0 + off) / 26)
        tone = rng.rand(12, 8)[np.clip(row.astype(int), 0, 11), np.clip(col.astype(int), 0, 7)]
        sh = 0.5 + 0.26 * tone + (nz - 0.5) * 0.3 - 0.1 * (((s.yc - y0) % rowh) > rowh - 1.5)
        s.paint(base, STONE, sh, edge=1)
        seam_h = ((s.yc - y0) % rowh) < 1
        seam_v = ((s.xc - x0 + off) % 26) < 1
        s.fill(base & (seam_h | seam_v), "#6a604c")
    blocks(4, 124, 56, 84, 9.5, 152)
    s.paint(s.rect(2, 52, 126, 58), STONE, 0.9 + (nz - 0.5) * 0.2, edge=2)
    s.fill(s.rect(2, 52, 126, 53), "#ddd3b6")
    blocks(30, 98, 84, 96, 12, 153)
    s.paint(s.rect(28, 82, 100, 86), STONE, 0.92, edge=2)
    s.fill(s.rect(28, 82, 100, 83), "#ddd3b6")
    # red cloth band along the front with a gold border and a few folds
    fold = 0.55 + 0.2 * np.sin(s.xc * 0.5) + 0.08 * np.sin(s.xc * 1.4)
    band = s.rect(8, 62, 120, 78)
    s.paint(band, RED, fold - 0.12 * (s.yc - 62) / 16.0, edge=1)
    s.fill(band & (s.yc >= 64) & (s.yc < 65.2), "#dcb64e")
    s.fill(band & (s.yc >= 75) & (s.yc < 76.2), "#dcb64e")
    # the plain judgement seat: a high back, arms, a seat board, square legs
    cx = 64
    for sd in (-1, 1):
        s.paint(s.rect(cx + sd * 14 - 2.5, 6, cx + sd * 14 + 2.5, 56), DWOOD, s.hgrad(cx + sd * 14 - 2.5, cx + sd * 14 + 2.5, 0.9, 0.35), edge=1)
        s.paint(s.rect(cx + sd * 14 - 3.2, 3, cx + sd * 14 + 3.2, 7), DWOOD, 0.8, edge=1)
    s.paint(s.rect(cx - 14, 14, cx + 14, 38), DWOOD, 0.5 + 0.3 * (vnoise(96, 128, 4, 12, 154) - 0.5), edge=1)
    for yy in (18, 28):
        s.paint(s.rect(cx - 14, yy, cx + 14, yy + 3), DWOOD, 0.7, edge=1)
    s.paint(s.rect(cx - 18, 36, cx - 12, 52), DWOOD, 0.6, edge=1)
    s.paint(s.rect(cx + 12, 36, cx + 18, 52), DWOOD, 0.4, edge=1)
    s.paint(s.rect(cx - 19, 33, cx - 8, 37), DWOOD, 0.9, edge=1)
    s.paint(s.rect(cx + 8, 33, cx + 19, 37), DWOOD, 0.85, edge=1)
    s.paint(s.rect(cx - 15, 42, cx + 15, 48), DWOOD, 0.75, edge=1)
    s.paint(s.rect(cx - 15, 48, cx + 15, 53), DWOOD, 0.5, edge=1)
    s.paint(s.rect(cx - 14, 53, cx - 9, 57), DWOOD, 0.4, edge=1)
    s.paint(s.rect(cx + 9, 53, cx + 14, 57), DWOOD, 0.4, edge=1)
    s.paint(s.rect(cx - 13, 42, cx + 13, 44), OCHRE, 0.5, edge=0)
    return s.rgba()


def thing_wall_low() -> np.ndarray:
    """A low dry-stone field wall: rounded stones of different sizes, unmortared, a broken top line."""
    s = Spr(128, 48)
    rng = np.random.RandomState(161)
    rows = [(36.0, 48.0), (25.0, 36.5), (14.5, 26.0), (6.0, 15.5)]
    back = s.rect(2, 12, 126, 48)
    s.paint(back, STONE, 0.04 + 0.1 * (vnoise(48, 128, 5, 5, 162) - 0.5), edge=0)
    for ri, (ya, yb) in enumerate(rows):
        x = -rng.rand() * 14 + (ri % 2) * 6
        top_row = ri == len(rows) - 1
        while x < 128:
            w = 13 + rng.rand() * 15
            x0, x1 = max(x + 0.7, 2), min(x + w - 0.7, 126)
            if x1 - x0 < 5:
                x += w
                continue
            y0 = ya + 0.7 + (rng.rand() * 5.5 if top_row else rng.rand() * 1.5)
            y1 = yb - 0.4
            rx, ry = (x1 - x0) / 2, (y1 - y0) / 2
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            m = (np.abs((s.xc - cx) / rx) ** 3.0 + np.abs((s.yc - cy) / ry) ** 3.0 <= 1.0) & (s.xc > 2) & (s.xc < 126)
            pal = STONE if rng.rand() > 0.22 else TAN
            tone = 0.5 + rng.rand() * 0.3
            s.paint(m, pal, tone + 0.3 * s.lit(cx, cy, rx, ry, 0.0, 0.5) + (vnoise(48, 128, 4, 4, int(abs(x) * 7 + ya) % 99991) - 0.5) * 0.18, edge=1)
            x += w
    # the back fill only shows between stones; trim it under the lowest stone tops
    return s.rgba()


def thing_fence() -> np.ndarray:
    s = Spr(96, 48)
    nz = vnoise(48, 96, 3, 14, 171)
    posts = ((9, 8, 4.6), (35, 5, 4.2), (62, 7, 4.8), (88, 10, 4.4))
    for (px_, top, w) in posts:
        s.paint(s.poly([(px_ - w, 47), (px_ + w, 47), (px_ + w, top + 3), (px_ + w * 0.2, top - 2), (px_ - w, top + 2)]), WEATH,
                s.cyl(px_, w, 0.15, 0.9) * 0.7 + 0.12 + (nz - 0.5) * 0.3, edge=1)
        s.fill(s.rect(px_ - 1, top + 6, px_ - 0.2, top + 12), "#4e4034")
    for (ry, tilt, x0, x1) in ((16, 1.0, 2, 92), (31, -0.8, 3, 93)):
        rail = s.poly([(x0, ry), (x1, ry + tilt), (x1, ry + tilt + 5.4), (x0, ry + 5.4)])
        s.paint(rail, WEATH, 0.72 + (vnoise(48, 96, 12, 2, 172 + ry) - 0.5) * 0.4 - 0.3 * (s.yc > ry + 4 + (s.xc / 96) * tilt), edge=1)
        s.fill(s.rect(x0, ry, x0 + 2, ry + 5) & rail, "#c4b296")
        for (px_, _, _) in posts:
            s.dot(int(px_), int(ry + 2.5 + tilt * px_ / 96), "#4e4034")
    return s.rgba()


def thing_door() -> np.ndarray:
    """A plank door in a limestone frame, 1.0 x 2.0 m at 112 texels per metre: it stands where the old wall_door tile carried one (the carpenter's yard, the Capernaum street)."""
    s = Spr(112, 224)
    nz = vnoise(224, 112, 3, 40, 181, 3)
    # the frame: two jambs of alternating blocks, a monolith lintel, a worn threshold step
    for k, y0 in enumerate(range(30, 214, 30)):
        for xa, xb in ((2, 20), (92, 110)):
            ext = 0 if k % 2 == 0 else 3
            m = s.rect(xa - (ext if xa < 50 else 0), y0, xb + (0 if xa < 50 else ext), min(y0 + 29, 214))
            s.paint(m, STONE, 0.58 + 0.18 * (k % 2) + (nz - 0.5) * 0.3 + 0.1 * (s.xc < xa + 4) - 0.14 * (s.xc > xb - 4), edge=1)
    s.paint(s.rect(0, 6, 112, 30), STONE, 0.7 + (nz - 0.5) * 0.3 - 0.2 * (s.yc > 24), edge=1)
    s.paint(s.rect(4, 214, 108, 224), STONE, 0.62 + (nz - 0.5) * 0.3 - 0.2 * (s.yc > 220), edge=1)
    # the leaf: four planks with grain, a dark gap between them, two iron straps with studs, a ring pull
    leaf = s.rect(20, 30, 92, 214)
    pw = 18.0
    plank = np.floor((s.xc - 20) / pw)
    tone = np.random.RandomState(182).rand(8).astype(np.float32)[np.clip(plank, 0, 7).astype(int)]
    grain = vnoise(224, 112, 2.2, 60, 183, 3)
    sh = 0.42 + (tone - 0.5) * 0.3 + (grain - 0.5) * 0.4 + 0.1 * (((s.xc - 20) % pw) < 3) - 0.14 * (((s.xc - 20) % pw) > pw - 3)
    sh -= 0.2 * np.exp(-np.clip(s.yc - 30, 0, None) / 8.0)
    s.paint(leaf, DWOOD, sh, edge=1)
    s.fill(leaf & (((s.xc - 20) % pw) < 1.2), "#1e140e")
    for sy in (52, 160):
        strap = s.rect(20, sy, 92, sy + 9)
        s.paint(strap, IRON, 0.5 + 0.25 * (s.yc < sy + 2) - 0.2 * (s.yc > sy + 7), edge=1)
        for rx in range(26, 92, 18):
            s.dot(rx, sy + 4, "#a29fa8")
            s.dot(rx + 1, sy + 4, "#46444a")
    s.paint(s.ell(80, 124, 6, 6) & ~s.ell(80, 124, 3.6, 3.6), IRON, 0.62, edge=1)
    s.paint(s.rect(77, 117, 83, 121), IRON, 0.6, edge=1)
    return s.rgba()


def thing_column() -> np.ndarray:
    """A fluted stone column of the Temple colonnade, 0.8 m across the base and 4.6 m tall at 112 texels per metre, with echinus and abacus above and a torus base below."""
    s = Spr(96, 516)
    cx = 48.0
    nz = vnoise(516, 96, 4, 60, 191, 3)
    y0, y1 = 64, 452
    hw = 30.0 - 5.0 * (s.yc - y0) / (y1 - y0) * -1.0  # a slight entasis: wider at the foot
    hw = 26.0 + 4.0 * np.clip((s.yc - y0) / (y1 - y0), 0, 1)
    shaft = (np.abs(s.xc - cx) <= hw) & (s.yc >= y0) & (s.yc < y1)
    u = np.clip((s.xc - cx) / hw, -1, 1)
    th = np.arcsin(u)
    t = (th / 0.5236) % 1.0
    groove = 1 - np.abs(2 * t - 1)
    lamb = np.clip(np.cos(th + 0.65), 0, 1)
    sh = 0.22 + 0.66 * lamb - 0.16 * groove ** 1.3 + (nz - 0.5) * 0.12
    s.paint(shaft, STONE, sh, edge=1)
    for ya, yb, w, tone in ((44, 64, 33, 0.55), (28, 44, 38, 0.65), (10, 28, 42, 0.72)):
        m = s.rect(cx - w, ya, cx + w, yb)
        s.paint(m, STONE, tone + (nz - 0.5) * 0.2 - 0.14 * (s.xc > cx + w * 0.55) + 0.08 * (s.yc < ya + 3), edge=1)
    for ya, yb, w, tone in ((452, 466, 34, 0.55), (466, 490, 38, 0.65), (490, 516, 42, 0.5)):
        m = s.rect(cx - w, ya, cx + w, yb)
        s.paint(m, STONE, tone + (nz - 0.5) * 0.2 - 0.14 * (s.xc > cx + w * 0.55) + 0.08 * (s.yc < ya + 3), edge=1)
    return s.rgba()


def thing_crenels() -> np.ndarray:
    """A run of merlons for the top of the city wall: 0.6 m blocks with 0.4 m gaps, 8 m long and 0.5 m high at 112 texels per metre."""
    w, h = 896, 56
    s = Spr(w, h)
    nz = vnoise(h, w, 20, 8, 201, 3)
    for x0 in range(0, w, 112):
        m = s.rect(x0 + 22, 0, x0 + 90, h)
        s.paint(m, STONE, 0.6 + (nz - 0.5) * 0.3 + 0.12 * (s.xc < x0 + 28) - 0.16 * (s.xc > x0 + 82) - 0.1 * (s.yc > 46), edge=1)
        s.fill(m & (s.yc == 27), "#6a604c")
    return s.rgba()


THINGS_ORDER: list[str] = []
SPECS: dict[str, tuple] = {}


def _reg(name, fn, w, h):
    SPECS[name] = (fn, w, h)
    THINGS_ORDER.append(name)


_reg("thing_boat", thing_boat, 192, 96)
_reg("thing_boat_far", thing_boat_far, 64, 40)
_reg("thing_nets", thing_nets, 96, 96)
_reg("thing_fishrack", thing_fishrack, 96, 72)
_reg("thing_basket", thing_basket, 40, 40)
_reg("thing_basket_full", thing_basket_full, 48, 48)


_reg("thing_table", thing_table, 128, 64)
_reg("thing_table_meal", thing_table_meal, 128, 72)
_reg("thing_table_coins", thing_table_coins, 112, 72)
_reg("thing_table_over", thing_table_over, 128, 72)
_reg("thing_lantern", thing_lantern, 32, 56)
_reg("thing_donkey", thing_donkey, 96, 80)
_reg("thing_caravan", thing_caravan, 224, 96)


_reg("thing_cart", thing_cart, 128, 96)
_reg("thing_brazier", thing_brazier, 40, 64)
_reg("thing_torch", thing_torch, 24, 64)
_reg("thing_bowl_set", thing_bowl_set, 48, 56)
_reg("thing_bench", thing_bench, 96, 40)
_reg("thing_stool", thing_stool, 32, 32)
_reg("thing_hay", thing_hay, 64, 48)
_reg("thing_workbench", thing_workbench, 128, 72)
_reg("thing_planks", thing_planks, 64, 96)


_reg("thing_jar", thing_jar, 32, 48)
_reg("thing_jars", thing_jars, 64, 56)
_reg("thing_spears", thing_spears, 48, 96)
_reg("thing_tent", thing_tent, 160, 112)
_reg("thing_dais", thing_dais, 128, 96)
_reg("thing_wall_low", thing_wall_low, 128, 48)
_reg("thing_fence", thing_fence, 96, 48)
_reg("thing_door", thing_door, 112, 224)
_reg("thing_column", thing_column, 96, 516)
_reg("thing_crenels", thing_crenels, 896, 56)


def build(out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    info = {}
    for name in THINGS_ORDER:
        fn, w, h = SPECS[name]
        rgba = fn()
        assert rgba.shape == (h, w, 4), (name, rgba.shape)
        Image.fromarray(rgba, "RGBA").save(os.path.join(out_dir, name + ".png"), optimize=False, compress_level=9)
        info[name] = {"size": [w, h], "blend": ""}
    return info


if __name__ == "__main__":
    print(len(build(sys.argv[1])), "sprites")
