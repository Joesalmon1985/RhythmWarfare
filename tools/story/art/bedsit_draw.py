"""Small pixel-painting kit for the bedsit art (tools/story/art/tex_bedsit.py): numpy canvases, PIL masks, palette ramps, ordered dither.

Everything is drawn at the style guide's density (BEDSIT_PPM = 160 texels per metre), with hard alpha (0 or 255), light from the upper left, and a one-pixel darker
edge round every shape. No anti-aliasing anywhere: shapes are PIL masks with fill only, colours come from `quantise` onto a ramp with the 8x8 Bayer dither.
Deterministic: every random value comes from a seeded generator.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from . import pixeltex as px

PPM = 160  # texels per metre


def m2px(m: float) -> int:
    return int(round(m * PPM))


def ramp(*cols):
    return px.ramp(*cols)


def lerp_ramp(a: str, b: str, n: int = 6):
    """An n-step ramp from colour a to colour b."""
    ca, cb = px.hexc(a), px.hexc(b)
    return np.stack([ca + (cb - ca) * i / (n - 1) for i in range(n)])


def fnoise(h: int, w: int, scale: float, seed: int, octaves: int = 3) -> np.ndarray:
    """Smooth value noise 0..1 over an h x w canvas (not tileable)."""
    rng = np.random.RandomState(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(scale / (2 ** o), 1.0)
        gh, gw = int(h / s) + 3, int(w / s) + 3
        g = rng.rand(gh, gw).astype(np.float32)
        im = Image.fromarray(g, "F").resize((int(gw * s), int(gh * s)), Image.BICUBIC)
        out += np.asarray(im, np.float32)[:h, :w] * amp
        tot += amp
        amp *= 0.5
    return np.clip(out / tot, 0, 1)


def stretched(h: int, w: int, sx: float, sy: float, seed: int) -> np.ndarray:
    """Anisotropic noise (wood grain: long in x when sx is large)."""
    rng = np.random.RandomState(seed)
    gh, gw = int(h / sy) + 3, int(w / sx) + 3
    g = rng.rand(gh, gw).astype(np.float32)
    im = Image.fromarray(g, "F").resize((int(gw * sx), int(gh * sy)), Image.BICUBIC)
    return np.clip(np.asarray(im, np.float32)[:h, :w], 0, 1)


def speckle(h: int, w: int, density: float, seed: int) -> np.ndarray:
    return np.random.RandomState(seed).rand(h, w) < density


class Cv:
    """An RGBA canvas. Shapes are masks; `paint` fills a mask with a shaded, dithered ramp and a darker edge."""

    def __init__(self, w: int, h: int, fill=None):
        self.w, self.h = w, h
        self.a = np.zeros((h, w, 4), np.uint8)
        if fill is not None:
            self.a[..., :3] = (px.hexc(fill) * 255).astype(np.uint8)
            self.a[..., 3] = 255
        self.yy, self.xx = np.mgrid[0:h, 0:w].astype(np.float32)

    # ---- masks ----
    def _mask(self, draw_fn) -> np.ndarray:
        im = Image.new("L", (self.w, self.h), 0)
        draw_fn(ImageDraw.Draw(im))
        return np.asarray(im) > 127

    def rect(self, x0, y0, x1, y1):
        return self._mask(lambda d: d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=255))

    def ell(self, x0, y0, x1, y1):
        return self._mask(lambda d: d.ellipse([x0, y0, x1 - 1, y1 - 1], fill=255))

    def poly(self, pts):
        return self._mask(lambda d: d.polygon([(float(x), float(y)) for x, y in pts], fill=255))

    def line(self, p0, p1, width=1):
        return self._mask(lambda d: d.line([p0, p1], fill=255, width=width))

    def lines(self, pts, width=1):
        return self._mask(lambda d: d.line([tuple(p) for p in pts], fill=255, width=width))

    def rrect(self, x0, y0, x1, y1, r):
        return self._mask(lambda d: d.rounded_rectangle([x0, y0, x1 - 1, y1 - 1], radius=r, fill=255))

    # ---- shading fields ----
    def lit(self, box, base=0.55, spread=0.35, noise=0.0, seed=1) -> np.ndarray:
        """Light from the upper left across the box (x0, y0, x1, y1): bright at the top left, dark at the bottom right."""
        x0, y0, x1, y1 = box
        u = np.clip((self.xx - x0) / max(x1 - x0, 1), 0, 1)
        v = np.clip((self.yy - y0) / max(y1 - y0, 1), 0, 1)
        s = base + spread * (0.5 - (u * 0.45 + v * 0.55))
        if noise:
            s = s + (fnoise(self.h, self.w, 5, seed) - 0.5) * noise
        return s

    def round_x(self, x0, x1, base=0.55, spread=0.5) -> np.ndarray:
        """A cylinder standing upright between x0 and x1, lit from the left."""
        u = np.clip((self.xx - x0) / max(x1 - x0, 1) * 2 - 1, -1, 1)
        return base + spread * (-0.55 * u + 0.45 * np.sqrt(np.clip(1 - u * u, 0, 1)) - 0.25)

    def round_y(self, y0, y1, base=0.55, spread=0.5) -> np.ndarray:
        v = np.clip((self.yy - y0) / max(y1 - y0, 1) * 2 - 1, -1, 1)
        return base + spread * (-0.55 * v + 0.45 * np.sqrt(np.clip(1 - v * v, 0, 1)) - 0.25)

    def dome(self, cx, cy, rx, ry, base=0.55, spread=0.6) -> np.ndarray:
        """A sphere/ellipsoid lit from the upper left."""
        u = (self.xx - cx) / max(rx, 1)
        v = (self.yy - cy) / max(ry, 1)
        r2 = np.clip(u * u + v * v, 0, 1)
        nz = np.sqrt(1 - r2)
        return base + spread * (-0.5 * u - 0.5 * v + 0.6 * nz - 0.35)

    # ---- painting ----
    def paint(self, mask, pal, shade=None, edge=True, dither=1.0, edge_col=None, alpha=255):
        """Fill `mask` with ramp `pal` (n x 3, dark to light) by `shade` (0..1 field; default mid), dithered, with a 1 px edge a step darker than the local colour."""
        if shade is None:
            shade = np.full((self.h, self.w), 0.5, np.float32)
        rgb = px.quantise(shade, pal, dither)
        m = mask & True
        self.a[m, :3] = rgb[m]
        self.a[m, 3] = alpha
        if edge:
            e = m & ~self._erode(m)
            if edge_col is None:
                dark = (rgb.astype(np.float32) * 0.62)
                self.a[e, :3] = dark[e].astype(np.uint8)
            else:
                self.a[e, :3] = (px.hexc(edge_col) * 255).astype(np.uint8)

    def flat(self, mask, col, edge=False, edge_col=None):
        self.a[mask, :3] = (px.hexc(col) * 255).astype(np.uint8)
        self.a[mask, 3] = 255
        if edge:
            e = mask & ~self._erode(mask)
            c = edge_col if edge_col else col
            self.a[e, :3] = (px.hexc(c) * 255 * (1.0 if edge_col else 0.6)).astype(np.uint8)

    def dots(self, pts, col, r=0):
        for (x, y) in pts:
            if r <= 0:
                if 0 <= int(y) < self.h and 0 <= int(x) < self.w:
                    self.a[int(y), int(x), :3] = (px.hexc(col) * 255).astype(np.uint8)
                    self.a[int(y), int(x), 3] = 255
            else:
                self.flat(self.ell(x - r, y - r, x + r + 1, y + r + 1), col)

    def erase(self, mask):
        self.a[mask] = 0

    def tint(self, mask, col, amount):
        """Mix a colour into what is already there (only where opaque)."""
        m = mask & (self.a[..., 3] > 0)
        c = px.hexc(col) * 255
        self.a[m, :3] = (self.a[m, :3].astype(np.float32) * (1 - amount) + c * amount).astype(np.uint8)

    def shade_mul(self, mask, k):
        m = mask & (self.a[..., 3] > 0)
        self.a[m, :3] = np.clip(self.a[m, :3].astype(np.float32) * k, 0, 255).astype(np.uint8)

    def stamp(self, other: "Cv", x: int, y: int):
        """Draw another canvas on this one (alpha 0/255)."""
        h, w = other.h, other.w
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, self.w), min(y + h, self.h)
        if x1 <= x0 or y1 <= y0:
            return
        sub = other.a[y0 - y:y1 - y, x0 - x:x1 - x]
        m = sub[..., 3] > 0
        dst = self.a[y0:y1, x0:x1]
        dst[m] = sub[m]

    @staticmethod
    def _erode(m):
        e = m.copy()
        e[1:, :] &= m[:-1, :]
        e[:-1, :] &= m[1:, :]
        e[:, 1:] &= m[:, :-1]
        e[:, :-1] &= m[:, 1:]
        e[0, :] = False
        e[-1, :] = False
        e[:, 0] = False
        e[:, -1] = False
        return e

    def image(self) -> Image.Image:
        return Image.fromarray(self.a, "RGBA")

    def save(self, path: str):
        self.image().save(path, optimize=False, compress_level=9)


def save_rgb(path: str, rgb: np.ndarray) -> None:
    Image.fromarray(rgb, "RGB").save(path, optimize=False, compress_level=9)


def periodic_noise(n: int, scale: float, seed: int, octaves: int = 3) -> np.ndarray:
    return px.noise(n, scale, seed, octaves)


def glow_disc(h: int, w: int, cx: float, cy: float, r: float, power: float = 2.0) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    return np.clip(1 - d, 0, 1) ** power
