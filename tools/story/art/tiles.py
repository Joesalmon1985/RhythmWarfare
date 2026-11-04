"""Small texture tiles for the 2.5D world (StoryWorld): 64 or 128 px PNGs, drawn with Pillow from the chapter's own palette and motifs
(the neon trim, LED tiles, truss, bottle shelf, door transom of the Night One SVG art). No SVG rasteriser exists in the toolchain, so the tiles are
drawn directly in the same colours rather than cropped out of the SVGs; every pixel comes from a fixed script and a seeded random, so a rebuild is
byte-identical. Output: assets/story/<chapter>/textures/<id>.png and the manifest section `textures` {id: {file, size, metres}}.
"""
from __future__ import annotations

import os
import random

from PIL import Image, ImageDraw

from . import lib

MAGENTA, CYAN, VIOLET, AMBER = "#ff2f9d", "#19d2ff", "#7a4cff", "#ffc23f"
INK = "#07041a"
OUTLINE = lib.OUT


def _img(size, base):
    im = Image.new("RGB", (size, size), base)
    return im, ImageDraw.Draw(im)


def _noise(im: Image.Image, seed: int, amount: int = 6) -> None:
    rng = random.Random(seed)
    px = im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            if rng.random() < 0.18:
                r, g, b = px[x, y]
                d = rng.randint(-amount, amount)
                px[x, y] = (max(0, min(255, r + d)), max(0, min(255, g + d)), max(0, min(255, b + d)))


def wall_brick():
    im, d = _img(64, "#1b1150")
    for row in range(8):
        y = row * 8
        off = 0 if row % 2 == 0 else 8
        d.line([(0, y), (63, y)], fill=INK)
        for x in range(-off, 64, 16):
            d.line([(x, y), (x, y + 7)], fill=INK)
            d.rectangle([x + 1, y + 1, x + 14, y + 2], fill="#241766")
    d.line([(0, 63), (63, 63)], fill="#2a1d66")
    _noise(im, 1)
    return im


def wall_panel():
    im, d = _img(64, "#241a58")
    d.rectangle([0, 0, 63, 63], outline=OUTLINE)
    d.rectangle([4, 4, 59, 59], outline="#3a2a82")
    d.rectangle([8, 8, 55, 55], fill="#17103f")
    d.line([(8, 30), (55, 30)], fill=MAGENTA)
    d.line([(8, 31), (55, 31)], fill="#7a1a52")
    for cx, cy in ((6, 6), (57, 6), (6, 57), (57, 57)):
        d.rectangle([cx - 1, cy - 1, cx + 1, cy + 1], fill="#8c78d8")
    _noise(im, 2, 4)
    return im


def wall_led():
    im, d = _img(64, "#05031a")
    d.rectangle([0, 0, 63, 63], outline="#3a2a82")
    d.rectangle([2, 2, 61, 61], outline=OUTLINE)
    for y in range(6, 58, 4):
        d.line([(6, y), (57, y)], fill="#0d1a3a")
    for x in range(8, 56, 8):
        h = 6 + (x * 7) % 30
        d.rectangle([x, 56 - h, x + 4, 56], fill=CYAN)
        d.rectangle([x, 56 - h, x + 4, 56 - h + 1], fill="#c8f4ff")
    return im


def wall_speaker():
    im, d = _img(64, "#150d44")
    d.rectangle([0, 0, 63, 63], outline=OUTLINE)
    d.rectangle([3, 3, 60, 60], fill="#1b1150", outline="#3a2a82")
    d.ellipse([10, 10, 53, 53], fill="#0a0626", outline=OUTLINE)
    d.ellipse([18, 18, 45, 45], fill="#241a58", outline="#5f4aa8")
    d.ellipse([27, 27, 36, 36], fill=MAGENTA, outline="#ff9ad0")
    _noise(im, 3, 3)
    return im


def trim():
    im, d = _img(64, "#150d44")
    d.rectangle([0, 0, 63, 11], fill=INK)
    d.rectangle([0, 12, 63, 15], fill=MAGENTA)
    d.rectangle([0, 14, 63, 14], fill="#ffc8e8")
    d.rectangle([0, 16, 63, 19], fill="#7a1a52")
    d.rectangle([0, 48, 63, 51], fill="#0a4a66")
    d.rectangle([0, 50, 63, 50], fill=CYAN)
    _noise(im, 4, 3)
    return im


def floor_led():
    im = Image.new("RGB", (128, 128), INK)
    d = ImageDraw.Draw(im)
    cols = [[MAGENTA, "#3a2c9a"], [CYAN, VIOLET]]
    shade = {MAGENTA: "#a01c68", CYAN: "#0f8aa8", VIOLET: "#5030b0", "#3a2c9a": "#271c70"}
    for j in range(2):
        for i in range(2):
            c = cols[j][i]
            x0, y0 = i * 64, j * 64
            d.rectangle([x0, y0, x0 + 63, y0 + 63], fill=shade[c])
            d.rectangle([x0 + 3, y0 + 3, x0 + 60, y0 + 60], fill=c)
            d.rectangle([x0 + 3, y0 + 3, x0 + 60, y0 + 5], fill="#ffffff" if c in (CYAN, MAGENTA) else "#8c78d8")
            d.rectangle([x0, y0, x0 + 63, y0 + 63], outline=INK)
    _noise(im, 5, 4)
    return im


def floor_dark():
    im, d = _img(64, "#150e44")
    for k in range(0, 64, 16):
        d.line([(k, 0), (k, 63)], fill="#241766")
        d.line([(0, k), (63, k)], fill="#241766")
    d.rectangle([0, 0, 63, 63], outline="#0c0730")
    _noise(im, 6, 4)
    return im


def floor_stage():
    im, d = _img(64, "#2a1a4e")
    for k in range(0, 64, 16):
        d.line([(0, k), (63, k)], fill="#0a0626")
        d.rectangle([0, k + 1, 63, k + 2], fill="#3b2c80")
    d.line([(21, 0), (21, 15)], fill="#0a0626")
    d.line([(43, 16), (43, 31)], fill="#0a0626")
    d.line([(10, 32), (10, 47)], fill="#0a0626")
    d.line([(35, 48), (35, 63)], fill="#0a0626")
    d.line([(0, 63), (63, 63)], fill=AMBER)
    _noise(im, 7, 5)
    return im


def ceil_truss():
    im, d = _img(64, "#05031a")
    d.line([(0, 8), (63, 8)], fill="#5f4aa8")
    d.line([(0, 24), (63, 24)], fill="#3a2c6a")
    for x in range(0, 64, 16):
        d.line([(x, 8), (x + 8, 24)], fill="#3a2c6a")
        d.line([(x + 8, 24), (x + 16, 8)], fill="#3a2c6a")
    d.line([(0, 40), (63, 40)], fill="#0a0626")
    d.line([(0, 56), (63, 56)], fill="#0a0626")
    return im


def floor_carpet():
    im, d = _img(64, "#2a1766")
    for y in range(0, 64, 8):
        for x in range((y // 8 % 2) * 8, 64, 16):
            d.rectangle([x, y, x + 3, y + 3], fill="#3b2490")
    d.rectangle([0, 0, 63, 63], outline="#170c44")
    _noise(im, 8, 5)
    return im


def wall_bar():
    im, d = _img(64, "#17103f")
    cols = [MAGENTA, CYAN, AMBER, VIOLET, "#4ff0a8", "#ff7a59"]
    for shelf in (20, 44):
        d.rectangle([0, shelf, 63, shelf + 3], fill="#3a2a82")
        d.line([(0, shelf + 4), (63, shelf + 4)], fill=INK)
        for k, x in enumerate(range(4, 60, 9)):
            c = cols[(k + shelf) % len(cols)]
            h = 8 + (k * 5 + shelf) % 6
            d.rectangle([x, shelf - h, x + 4, shelf - 1], fill=c)
            d.rectangle([x + 1, shelf - h - 3, x + 3, shelf - h], fill=c)
            d.line([(x + 1, shelf - h + 1), (x + 1, shelf - 3)], fill="#ffffff")
    d.rectangle([0, 0, 63, 63], outline=OUTLINE)
    return im


def bar_front():
    im, d = _img(64, "#2a1a4e")
    for x in range(0, 64, 8):
        d.rectangle([x + 1, 6, x + 6, 58], fill="#3b2c80", outline=INK)
    d.rectangle([0, 0, 63, 5], fill="#5f4aa8")
    d.line([(0, 6), (63, 6)], fill=INK)
    d.line([(0, 60), (63, 60)], fill=CYAN)
    _noise(im, 9, 4)
    return im


def toilet_tile():
    im, d = _img(64, "#cfe6f0")
    for k in range(0, 64, 16):
        d.line([(k, 0), (k, 63)], fill="#7fa6b8")
        d.line([(0, k), (63, k)], fill="#7fa6b8")
        d.line([(k + 1, 0), (k + 1, 63)], fill="#ffffff")
    d.rectangle([0, 0, 63, 63], outline="#7fa6b8")
    _noise(im, 10, 5)
    return im


def toilet_floor():
    im, d = _img(64, "#5a7a8c")
    for j in range(4):
        for i in range(4):
            if (i + j) % 2:
                d.rectangle([i * 16, j * 16, i * 16 + 15, j * 16 + 15], fill="#46647a")
    d.rectangle([0, 0, 63, 63], outline="#344e60")
    _noise(im, 11, 5)
    return im


def cubicle_door():
    im, d = _img(64, "#2c8a8a")
    d.rectangle([0, 0, 63, 63], outline="#0f4a4a")
    d.rectangle([5, 5, 58, 58], outline="#46b0a8")
    for y in range(10, 54, 6):
        d.line([(9, y), (54, y)], fill="#1f6e6e")
    d.rectangle([27, 28, 36, 33], fill="#e8e8e8", outline="#555566")
    d.rectangle([30, 29, 33, 32], fill="#cc3333")
    _noise(im, 12, 4)
    return im


def wall_door():
    im, d = _img(64, "#3a2a82")
    d.rectangle([0, 0, 63, 63], outline=OUTLINE)
    d.rectangle([8, 14, 55, 63], fill="#0a0626", outline=OUTLINE)
    d.rectangle([14, 5, 49, 9], fill="#0a0626", outline=OUTLINE)
    d.rectangle([17, 6, 46, 8], fill=AMBER)
    d.line([(31, 14), (31, 63)], fill=OUTLINE)
    d.rectangle([27, 38, 28, 42], fill="#8c78d8")
    d.rectangle([34, 38, 35, 42], fill="#8c78d8")
    return im


# id -> (builder, metres per texture repeat)
NIGHT_ONE = {
    "wall_brick": (wall_brick, 2.0), "wall_panel": (wall_panel, 2.0), "wall_led": (wall_led, 3.0), "wall_speaker": (wall_speaker, 2.0),
    "trim": (trim, 2.0), "floor_led": (floor_led, 2.0), "floor_dark": (floor_dark, 2.0), "floor_stage": (floor_stage, 2.0),
    "ceil_truss": (ceil_truss, 2.0), "floor_carpet": (floor_carpet, 2.0), "wall_bar": (wall_bar, 2.0), "bar_front": (bar_front, 1.0),
    "toilet_tile": (toilet_tile, 1.5), "toilet_floor": (toilet_floor, 1.5), "cubicle_door": (cubicle_door, 2.0), "wall_door": (wall_door, 3.0),
}


def build(chapter: str, spec: dict | None = None) -> dict:
    """Write the chapter's tiles; return the manifest `textures` section."""
    spec = spec or NIGHT_ONE
    out_dir = os.path.join(lib.ROOT, "assets", "story", chapter, "textures")
    os.makedirs(out_dir, exist_ok=True)
    for fn in os.listdir(out_dir):
        if fn.endswith(".png"):
            os.remove(os.path.join(out_dir, fn))
    section = {}
    for tid in sorted(spec):
        fn, metres = spec[tid]
        im = fn()
        im.save(os.path.join(out_dir, tid + ".png"), optimize=False, compress_level=9)
        section[tid] = {"file": f"textures/{tid}.png", "size": [im.size[0], im.size[1]], "metres": metres}
    return section
