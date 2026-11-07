"""The Copper Bar's own art (docs/doom/scenes/bar.md): wall, floor and ceiling tiles (128 px), wall decals and billboard props, drawn in code toward the painting
(`art/reference/doom_worlds/Copper Basement Bar, Three Hidden Routes-3.png`): copper and brick under warm lamps, wet blue cobbles, teal water, velvet and tapestry.

    python -I tools/doom/art/make_bar_art.py       writes assets/story/doom_bar/textures/*.png and docs/shots/doom/bar/art_sheet.png

PLACEHOLDER art: procedural pixel painting (palette ramps with ordered dither, hashed noise, hand-placed shapes), at the density of the project's tiles (128 texels per metre) but
not at the painting's finish. An art pass replaces the PNGs; the names, sizes and aspect ratios are the data contract (tools/doom/author_bar.py lists them).
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
OUT = os.path.join(ROOT, "assets", "story", "doom_bar", "textures")
SHEET = os.path.join(ROOT, "docs", "shots", "doom", "bar", "art_sheet.png")
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def hexc(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def ramp(v, cols, dither=0.9):
    """v in [0,1] (array) -> colours of the ramp, ordered-dithered between its steps."""
    h, w = v.shape
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.clip(v, 0, 1) * (len(cols) - 1) + (BAYER[yy % 4, xx % 4] - 0.5) * dither
    idx = np.clip(np.floor(d + 0.5), 0, len(cols) - 1).astype(int)
    pal = np.array([hexc(c) for c in cols], np.uint8)
    return pal[idx]


def noise(h, w, seed, cell=4, octaves=3):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = max(1, cell // (2 ** o))
        g = rng.random((h // c + 2, w // c + 2))
        big = np.kron(g, np.ones((c, c)))[:h, :w]
        out += big * amp
        tot += amp
        amp *= 0.5
    return out / tot


def save(name, arr, alpha=None):
    os.makedirs(OUT, exist_ok=True)
    if alpha is None:
        im = Image.fromarray(arr.astype(np.uint8), "RGB")
    else:
        a = np.dstack([arr.astype(np.uint8), (alpha * 255).astype(np.uint8)])
        im = Image.fromarray(a, "RGBA")
    im.save(os.path.join(OUT, name + ".png"))
    return im


# --- tiles --------------------------------------------------------------------------------------------------------------------------

BRICK = ["#1a0f0c", "#2e1a12", "#4a2a1a", "#6b3b22", "#8a4e2c", "#b06a38"]
COPPER = ["#2a1208", "#5a2a12", "#8f4a1c", "#c47a34", "#e6a455", "#ffd58a"]


def tile_brick(name="bar_brick", seed=1, w=128, h=128, rows=8, moss=True):
    rng = np.random.default_rng(seed)
    v = np.zeros((h, w))
    bh = h // rows
    for r in range(rows):
        off = (r % 2) * (w // 8)
        bw = w // 4
        for c in range(-1, 5):
            x0, y0 = c * bw + off, r * bh
            base = 0.40 + rng.random() * 0.30
            yy, xx = np.mgrid[0:bh, 0:bw]
            shade = base + 0.18 * (1 - yy / bh) * (xx < bw * 0.9) - 0.12 * (yy > bh * 0.85) + 0.06 * (rng.random((bh, bw)) - 0.5)
            shade[:2, :] -= 0.0
            shade[:, -2:] = 0.06
            shade[-2:, :] = 0.06  # mortar
            for yy_ in range(bh):
                for xx_ in range(bw):
                    X, Y = (x0 + xx_) % w, y0 + yy_
                    if Y < h:
                        v[Y, X] = shade[yy_, xx_]
    v += (noise(h, w, seed + 5, 6) - 0.5) * 0.18
    img = ramp(v, BRICK)
    if moss:
        n = noise(h, w, seed + 9, 12)
        m = (n > 0.72) & (np.mgrid[0:h, 0:w][0] > h * 0.6)
        img[m & (BAYER[np.mgrid[0:h, 0:w][0] % 4, np.mgrid[0:h, 0:w][1] % 4] < 0.55)] = hexc("#3a4a24")
    return img


def tile_cobble():
    h = w = 128
    rng = np.random.default_rng(3)
    v = np.zeros((h, w))
    cell = 32
    for r in range(h // 16):
        off = (r % 2) * 16
        for c in range(w // 32 + 1):
            x0, y0 = (c * 32 + off) % w, r * 16
            base = 0.38 + rng.random() * 0.34
            for yy in range(16):
                for xx in range(32):
                    edge = min(yy, 15 - yy, xx, 31 - xx)
                    s = base + (0.16 if edge >= 2 else -0.35) + 0.12 * (1 - yy / 16) + 0.05 * (rng.random() - 0.5)
                    v[(y0 + yy) % h, (x0 + xx) % w] = s
    wet = noise(h, w, 4, 16)
    v = v * 0.85 + wet * 0.2
    pal = ["#120a14", "#241426", "#3c2238", "#58334a", "#7a4a5a", "#a06a60"]
    img = ramp(v, pal, 0.8)
    glint = (wet > 0.66) & (v > 0.5)
    yy, xx = np.mgrid[0:h, 0:w]
    img[glint & (BAYER[yy % 4, xx % 4] < 0.5)] = hexc("#c9824a")
    img[(wet > 0.78) & (v > 0.55) & (BAYER[yy % 4, xx % 4] < 0.3)] = hexc("#ffc27a")
    return img


def tile_planks():
    h = w = 128
    rng = np.random.default_rng(5)
    v = np.zeros((h, w))
    for c in range(4):
        base = 0.4 + rng.random() * 0.3
        grain = noise(h, 32, 20 + c, 3)
        for x in range(32):
            col = base + 0.25 * np.sin((np.arange(h) / 9.0) + grain[:, x] * 6 + x * 0.05) * 0.4 + (grain[:, x] - 0.5) * 0.3
            v[:, c * 32 + x] = col
        v[:, c * 32] = 0.05
        v[:, c * 32 + 31] = 0.12
    for k in range(3):
        y = int(rng.integers(8, 120))
        c = int(rng.integers(0, 4))
        v[y:y + 2, c * 32 + 1:c * 32 + 31] = 0.06
    return ramp(v, ["#1c0f08", "#3a2012", "#5e3720", "#845030", "#a9703e", "#d09a5a"])


def tile_step():
    h = w = 128
    v = noise(h, w, 8, 5) * 0.6 + 0.2
    v[:6, :] += 0.25
    v[6:12, :] -= 0.1
    v[-3:, :] = 0.05
    for k in range(3):
        v[:, k * 40 + 20: k * 40 + 22] -= 0.25
    return ramp(v, ["#160c08", "#2e1a12", "#4e2e1e", "#744430", "#9c6444", "#c08a60"])


def tile_counter_front():
    h = w = 128
    v = np.full((h, w), 0.45)
    yy, xx = np.mgrid[0:h, 0:w]
    for c in range(2):
        x0 = c * 64 + 6
        pan = (xx >= x0) & (xx < x0 + 52) & (yy >= 12) & (yy < 116)
        edge = (np.minimum(np.minimum(xx - x0, x0 + 51 - xx), np.minimum(yy - 12, 115 - yy)))
        v[pan] = 0.34 + 0.05 * np.clip(edge[pan], 0, 6) / 6.0
        v[pan & (edge < 2)] = 0.7
    g = noise(h, w, 11, 3)
    v += (g - 0.5) * 0.18
    img = ramp(v, ["#150a06", "#2c1609", "#4b2610", "#6e3a18", "#9a5424", "#c47a34"])
    for c in range(2):
        for (sx, sy) in ((12, 18), (50, 18), (12, 108), (50, 108)):
            x = c * 64 + sx
            img[sy - 1:sy + 2, x - 1:x + 2] = hexc("#ffcc88")
            img[sy, x] = hexc("#fff0c0")
    return img


def tile_copper(seed=2):
    h = w = 128
    v = noise(h, w, seed, 4) * 0.5 + 0.25
    yy, xx = np.mgrid[0:h, 0:w]
    v += 0.22 * np.sin((xx + yy) / 14.0) * 0.5 + 0.08
    for gx in (0, 64):
        v[:, gx:gx + 2] -= 0.28
    for gy in (0, 64):
        v[gy:gy + 2, :] -= 0.28
    img = ramp(v, COPPER, 1.0)
    for gx in (8, 56, 72, 120):
        for gy in (8, 56, 72, 120):
            img[gy - 1:gy + 2, gx - 1:gx + 2] = hexc("#7a3c16")
            img[gy - 1, gx - 1] = hexc("#ffe0a0")
    return img


def tile_water():
    h = w = 128
    yy, xx = np.mgrid[0:h, 0:w]
    v = 0.35 + 0.18 * np.sin(xx / 9.0 + np.sin(yy / 7.0) * 2) + 0.14 * np.sin(yy / 5.0 + xx / 21.0) + (noise(h, w, 13, 4) - 0.5) * 0.3
    img = ramp(v, ["#04161c", "#08323a", "#0e5a60", "#18878a", "#52c7bd", "#a8f0d8"], 0.8)
    spark = (noise(h, w, 15, 2) > 0.86) & (BAYER[yy % 4, xx % 4] < 0.6)
    img[spark] = hexc("#ffc27a")  # the lamps' reflections
    return img


def tile_grate():
    h = w = 128
    img = np.zeros((h, w, 3), np.uint8)
    img[:] = hexc("#06141a")  # the water seen through
    yy, xx = np.mgrid[0:h, 0:w]
    bars = (xx % 16 < 5)
    cross = (yy % 64 < 7)
    m = bars | cross
    shade = 0.5 + 0.3 * (1 - (xx % 16) / 5.0) * bars + (noise(h, w, 17, 3) - 0.5) * 0.3
    metal = ramp(np.clip(shade, 0, 1), ["#1a0d08", "#3c1c0e", "#6a3416", "#a35a24", "#d48a3c"], 0.8)
    img[m] = metal[m]
    img[(xx % 16 == 0) & bars] = hexc("#ffcc88")
    img[(yy % 64 == 0) & cross] = hexc("#8a4a20")
    return img


def tile_quay():
    h = w = 128
    img = tile_brick("q", 21, rows=4, moss=False)
    v = noise(h, w, 22, 5)
    wet = np.mgrid[0:h, 0:w][0] > h * 0.55
    img = (img.astype(float) * np.where(wet, 0.75, 1.0)[..., None]).astype(np.uint8)
    img[(v > 0.7) & wet] = (img[(v > 0.7) & wet] * np.array([0.5, 0.9, 0.9])).astype(np.uint8)
    return img


def tile_ceiling():
    h = w = 128
    v = noise(h, w, 31, 6) * 0.35 + 0.15
    img = ramp(v, BRICK[:4], 0.6)
    yy, xx = np.mgrid[0:h, 0:w]
    for x0 in (0, 64):  # beams
        img[:, x0:x0 + 12] = ramp(np.full((h, 12), 0.2) + (noise(h, 12, 32 + x0, 3) - 0.5) * 0.2, BRICK[:3], 0.5)
        img[:, x0 + 12:x0 + 14] = hexc("#0c0604")
    pipe = (yy >= 44) & (yy < 76)  # the copper pipe across
    t = np.clip((yy - 44) / 32.0, 0, 1)
    cyl = 1 - np.abs(t - 0.38) * 2.0
    pimg = ramp(np.clip(cyl, 0, 1), COPPER, 0.6)
    img[pipe] = pimg[pipe]
    for x0 in (30, 100):  # collars
        img[40:80, x0:x0 + 8] = ramp(np.tile(np.clip(1 - np.abs((np.arange(40, 80) - 60) / 22.0), 0, 1)[:, None], (1, 8)), COPPER, 0.5)
        img[40:80, x0] = hexc("#2a1208")
    return img


def tile_booth_wall():
    h = w = 128
    img = np.zeros((h, w, 3), np.uint8)
    img[:] = hexc("#0d1015")
    rng = np.random.default_rng(41)
    for c in range(2):
        x0 = c * 64 + 4
        img[6:122, x0:x0 + 56] = hexc("#1c2028")
        img[6:122, x0:x0 + 2] = hexc("#3a4250")
        for r in range(6):
            y = 10 + r * 19
            img[y:y + 15, x0 + 4:x0 + 52] = hexc("#262c38")
            img[y:y + 1, x0 + 4:x0 + 52] = hexc("#4a5568")
            for k in range(7):
                col = hexc(["#ff3a2a", "#2af0d8", "#ffb040", "#3a3a48"][int(rng.integers(0, 4))])
                img[y + 4:y + 7, x0 + 7 + k * 6:x0 + 10 + k * 6] = col
            for k in range(2):
                img[y + 10:y + 12, x0 + 8 + k * 20:x0 + 24 + k * 20] = hexc("#10141a")
    return img


def tile_rail():
    """128 x 128 RGBA railing: two copper rails, posts, a lattice between (alpha)."""
    h = w = 128
    rgb = np.zeros((h, w, 3), np.uint8)
    a = np.zeros((h, w))
    yy, xx = np.mgrid[0:h, 0:w]
    for y0 in (8, 100):
        t = np.clip((yy - y0) / 14.0, 0, 1)
        shade = np.clip(1 - np.abs(t - 0.35) * 2.2, 0, 1)
        band = (yy >= y0) & (yy < y0 + 14)
        rgb[band] = ramp(shade, COPPER, 0.5)[band]
        a[band] = 1
    for x0 in (0, 64):
        post = (xx >= x0 + 28) & (xx < x0 + 36)
        sh = np.clip(1 - np.abs((xx - (x0 + 28)) / 8.0 - 0.35) * 2.2, 0, 1)
        rgb[post] = ramp(sh, COPPER, 0.5)[post]
        a[post] = 1
    diag = (((xx + yy) % 32) < 3) | (((xx - yy) % 32) < 3)
    diag &= (yy >= 22) & (yy < 100)
    rgb[diag] = hexc("#8f4a1c")
    a[diag] = 1
    return rgb, a


# --- sprites ------------------------------------------------------------------------------------------------------------------------

class Sheet:
    def __init__(self, w, h):
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.w, self.h = w, h

    def shaded(self, drawfn, cols, light=(-0.6, -0.7), dither=0.8):
        """Draw a mask with drawfn(ImageDraw), then fill it with the ramp by a blurred height field (a round-ish shading)."""
        from PIL import ImageFilter
        m = Image.new("L", (self.w, self.h), 0)
        drawfn(ImageDraw.Draw(m))
        a = np.array(m) > 127
        if not a.any():
            return
        blur = np.array(m.filter(ImageFilter.GaussianBlur(3.5))).astype(float) / 255.0
        gy, gx = np.gradient(blur)
        n = np.hypot(gx, gy) + 1e-6
        lit = (-gx / n) * light[0] + (-gy / n) * light[1]
        rim = np.clip((0.7 - blur) * 2.4, 0, 1)
        v = 0.55 + 0.45 * lit * rim
        arr = np.array(self.im)
        col = ramp(v, cols, dither)
        arr[a, :3] = col[a]
        arr[a, 3] = 255
        self.im = Image.fromarray(arr, "RGBA")
        self.d = ImageDraw.Draw(self.im)

    def outline(self, col="#0c0604"):
        from PIL import ImageFilter
        arr = np.array(self.im)
        a = arr[..., 3] > 127
        m = Image.fromarray((a * 255).astype(np.uint8))
        ring = (np.array(m.filter(ImageFilter.MaxFilter(3))) > 127) & ~a
        arr[ring, :3] = hexc(col)
        arr[ring, 3] = 255
        self.im = Image.fromarray(arr, "RGBA")
        self.d = ImageDraw.Draw(self.im)

    def save(self, name):
        os.makedirs(OUT, exist_ok=True)
        self.im.save(os.path.join(OUT, name + ".png"))
        return self.im


def glow(sh, cx, cy, r, col, strength=1.0):
    arr = np.array(sh.im).astype(float)
    yy, xx = np.mgrid[0:sh.h, 0:sh.w]
    g = np.clip(1 - np.hypot(xx - cx, yy - cy) / r, 0, 1) ** 2 * strength
    c = np.array(hexc(col), float)
    arr[..., :3] = arr[..., :3] * (1 - g[..., None] * 0.7) + c * g[..., None] * 0.7
    arr[..., 3] = np.maximum(arr[..., 3], g * 90)
    sh.im = Image.fromarray(arr.astype(np.uint8), "RGBA")
    sh.d = ImageDraw.Draw(sh.im)


def spr_pendant():
    s = Sheet(64, 96)
    s.d.line([(32, 0), (32, 26)], fill=hexc("#6a3416"), width=2)  # the chain
    s.shaded(lambda d: d.polygon([(14, 62), (50, 62), (42, 30), (22, 30)], fill=255), COPPER)
    s.shaded(lambda d: d.rectangle([26, 22, 38, 32], fill=255), COPPER)
    arr = np.array(s.im)
    arr[34:62:6, 14:50] = arr[34:62:6, 14:50] // 2  # the cage: dark bars across the lit shade
    for x in range(20, 46, 6):
        arr[32:62, x] = np.where(arr[32:62, x, 3:4] > 0, np.array([40, 18, 8, 255]), arr[32:62, x])
    s.im = Image.fromarray(arr, "RGBA")
    s.d = ImageDraw.Draw(s.im)
    s.d.ellipse([22, 48, 42, 68], fill=hexc("#ffd58a") + (255,))  # the bulb, lit
    s.d.ellipse([27, 53, 37, 63], fill=hexc("#fff4cc") + (255,))
    glow(s, 32, 56, 30, "#ffb050", 0.9)
    s.outline()
    return s.save("bar_pendant")


def spr_lantern():
    s = Sheet(48, 64)
    s.shaded(lambda d: d.rectangle([12, 14, 36, 50], fill=255), COPPER)
    s.shaded(lambda d: d.polygon([(10, 14), (38, 14), (32, 4), (16, 4)], fill=255), COPPER)
    s.d.rectangle([16, 20, 32, 44], fill=hexc("#ffcf80") + (255,))
    s.d.rectangle([20, 26, 28, 38], fill=hexc("#fff0c0") + (255,))
    s.d.line([(24, 20), (24, 44)], fill=hexc("#4a2210") + (255,), width=1)
    s.d.rectangle([14, 50, 34, 54], fill=hexc("#7a3c16") + (255,))
    glow(s, 24, 32, 28, "#ffa040", 0.8)
    s.outline()
    return s.save("bar_lantern")


def spr_crate(name="bar_crate", w=64, h=64, planks=3):
    s = Sheet(w, h)
    s.shaded(lambda d: d.rectangle([2, 2, w - 3, h - 3], fill=255), ["#2a160a", "#4a2810", "#6e3c1a", "#98582a", "#c47a34"], dither=0.9)
    for k in range(1, planks):
        y = k * h // planks
        s.d.line([(2, y), (w - 3, y)], fill=hexc("#1a0c06") + (255,), width=1)
    for (x, y) in ((6, 6), (w - 7, 6), (6, h - 7), (w - 7, h - 7)):  # copper corner rivets
        s.d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=hexc("#ffcc88") + (255,))
    s.d.rectangle([2, 2, w - 3, 5], fill=hexc("#8f4a1c") + (255,))
    s.d.rectangle([2, h - 6, w - 3, h - 3], fill=hexc("#6a3416") + (255,))
    s.outline()
    return s.save(name)


def spr_jug():
    s = Sheet(48, 64)
    s.shaded(lambda d: (d.ellipse([6, 22, 42, 60], fill=255), d.rectangle([17, 6, 31, 28], fill=255), d.ellipse([14, 2, 34, 12], fill=255)), COPPER)
    s.d.arc([30, 22, 46, 46], 270, 90, fill=hexc("#c47a34") + (255,), width=3)
    s.d.line([(10, 40), (38, 40)], fill=hexc("#5a2a12") + (255,))
    s.outline()
    return s.save("bar_jug")


def spr_stool():
    s = Sheet(64, 96)
    for x in (18, 46):  # legs
        s.d.line([(x, 52), (x - 4 if x < 32 else x + 4, 92)], fill=hexc("#3a1d0e") + (255,), width=4)
    s.shaded(lambda d: d.rounded_rectangle([6, 30, 58, 54], radius=8, fill=255), ["#2a0610", "#4e0c1c", "#781628", "#a02438", "#c84458"])
    s.d.arc([8, 44, 56, 60], 0, 180, fill=hexc("#d9a441") + (255,), width=2)  # the brass studs
    s.d.line([(32, 56), (32, 70)], fill=hexc("#6a3416") + (255,), width=3)
    s.d.ellipse([12, 69, 52, 77], outline=hexc("#c47a34") + (255,))
    s.outline()
    return s.save("bar_stool")


def spr_taps():
    s = Sheet(96, 64)
    s.shaded(lambda d: d.rectangle([6, 48, 90, 60], fill=255), COPPER)
    for k in range(4):
        x = 16 + k * 20
        s.shaded(lambda d, x=x: (d.rectangle([x - 4, 18, x + 4, 48], fill=255), d.rectangle([x - 2, 6, x + 2, 20], fill=255)), COPPER)
        s.d.rectangle([x - 6, 8, x + 6, 14], fill=hexc(["#d9a441", "#8c2230", "#2a8f9a", "#e8e0c8"][k]) + (255,))
    s.outline()
    return s.save("bar_taps")


def spr_bottles(name="bar_bottles", n=5, seed=3):
    rng = np.random.default_rng(seed)
    s = Sheet(24 * n + 8, 80)
    cols = [["#06201a", "#0c4a3a", "#1a7a5a", "#5ad0a0"], ["#2a1204", "#5a2a0a", "#9a5418", "#e0a040"], ["#0a1a2a", "#16406a", "#2a74b0", "#8ac8f0"], ["#2a0a10", "#5a1424", "#9a2a40", "#e06080"]]
    for k in range(n):
        x = 6 + k * 24 + 10
        hgt = int(rng.integers(34, 64))
        c = cols[int(rng.integers(0, 4))]
        s.shaded(lambda d, x=x, hgt=hgt: (d.rounded_rectangle([x - 9, 78 - hgt, x + 9, 78], radius=4, fill=255), d.rectangle([x - 3, 78 - hgt - 14, x + 3, 78 - hgt + 4], fill=255)), c)
        s.d.rectangle([x - 6, 78 - hgt // 2 - 4, x + 6, 78 - hgt // 2 + 8], fill=hexc("#e8dcc0") + (255,))  # label
        s.d.line([(x - 5, 78 - hgt + 8), (x - 5, 74)], fill=hexc("#ffffff") + (200,))
    s.outline()
    return s.save(name)


def spr_glass():
    s = Sheet(48, 48)
    s.d.polygon([(8, 10), (40, 10), (36, 44), (12, 44)], fill=(200, 230, 240, 120))
    s.d.polygon([(10, 24), (38, 24), (35, 43), (13, 43)], fill=hexc("#c47a34") + (230,))
    s.d.rectangle([14, 28, 22, 36], fill=(230, 250, 255, 200))  # ice
    s.d.line([(8, 10), (12, 44)], fill=(255, 255, 255, 220))
    s.d.line([(8, 10), (40, 10)], fill=(255, 255, 255, 220))
    s.outline("#1a0c06")
    return s.save("bar_glass")


def spr_pipe_col():
    s = Sheet(48, 192)
    s.shaded(lambda d: d.rectangle([12, 0, 36, 191], fill=255), COPPER, light=(-0.9, 0.0))
    for y in (24, 100, 170):
        s.shaded(lambda d, y=y: d.rectangle([8, y, 40, y + 12], fill=255), COPPER, light=(-0.9, 0.0))
        for x in (12, 36):
            s.d.rectangle([x - 1, y + 4, x + 1, y + 7], fill=hexc("#ffe0a0") + (255,))
    s.outline()
    return s.save("bar_pipe_col")


def spr_sofa():
    s = Sheet(176, 96)
    red = ["#1c0408", "#3e0a14", "#661424", "#8e2036", "#b83a50"]
    s.shaded(lambda d: d.rounded_rectangle([4, 14, 172, 60], radius=10, fill=255), red)  # the tufted back
    for r in range(2):
        for c in range(9):
            x, y = 14 + c * 18 + (r % 2) * 9, 24 + r * 16
            s.d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=hexc("#d9a441") + (255,))
            s.d.line([(x, y), (x + 9, y + 8)], fill=hexc("#2a0610") + (255,))
            s.d.line([(x, y), (x - 9, y + 8)], fill=hexc("#2a0610") + (255,))
    s.shaded(lambda d: d.rounded_rectangle([0, 54, 176, 84], radius=8, fill=255), red)
    s.shaded(lambda d: (d.rounded_rectangle([0, 34, 20, 90], radius=8, fill=255), d.rounded_rectangle([156, 34, 176, 90], radius=8, fill=255)), red)
    s.shaded(lambda d: d.rounded_rectangle([60, 44, 96, 72], radius=6, fill=255), ["#06201f", "#0c4a4a", "#188084", "#38b0b0", "#7ae0d8"])  # the teal cushion
    s.d.line([(64, 50), (92, 66)], fill=hexc("#d9a441") + (255,))
    s.d.line([(64, 66), (92, 50)], fill=hexc("#d9a441") + (255,))
    s.d.rectangle([14, 84, 22, 92], fill=hexc("#3a1d0e") + (255,))
    s.d.rectangle([154, 84, 162, 92], fill=hexc("#3a1d0e") + (255,))
    s.outline()
    return s.save("bar_sofa")


def spr_rug():
    s = Sheet(160, 64)
    s.d.polygon([(12, 6), (148, 6), (160, 58), (0, 58)], fill=hexc("#5a1020") + (255,))
    s.d.polygon([(22, 12), (138, 12), (148, 52), (12, 52)], outline=hexc("#d9a441") + (255,))
    for k in range(6):
        x = 32 + k * 20
        s.d.polygon([(x, 32), (x + 8, 22), (x + 16, 32), (x + 8, 42)], fill=hexc("#1a6a70") + (255,), outline=hexc("#d9a441") + (255,))
    s.outline()
    return s.save("bar_rug")


def decal_tapestry():
    s = Sheet(96, 176)
    s.d.rectangle([4, 0, 92, 8], fill=hexc("#6a3416") + (255,))  # the rail
    for x in (6, 88):
        s.d.ellipse([x - 3, 0, x + 5, 10], fill=hexc("#d9a441") + (255,))
    s.shaded(lambda d: d.rectangle([8, 8, 88, 158], fill=255), ["#1c0408", "#3a0814", "#5e1022", "#821a30", "#a82c44"], dither=1.0)
    s.d.rectangle([12, 12, 84, 154], outline=hexc("#d9a441") + (255,))
    # treble clef: a spine, the bowl, the loop
    g = hexc("#e8b850") + (255,)
    s.d.line([(50, 24), (50, 120)], fill=g, width=4)
    s.d.arc([30, 40, 70, 84], 200, 20, fill=g, width=4)
    s.d.arc([36, 62, 70, 104], 0, 220, fill=g, width=4)
    s.d.ellipse([34, 104, 54, 124], outline=g, width=4)
    s.d.ellipse([44, 20, 56, 32], outline=g, width=3)
    s.d.line([(30, 78), (64, 50)], fill=g, width=3)
    for k in range(10):  # woven pattern at the edges
        s.d.rectangle([14, 20 + k * 13, 18, 24 + k * 13], fill=hexc("#8f4a1c") + (255,))
        s.d.rectangle([78, 20 + k * 13, 82, 24 + k * 13], fill=hexc("#8f4a1c") + (255,))
    for x in range(10, 90, 5):  # the fringe
        s.d.line([(x, 158), (x, 172 - (x % 3))], fill=hexc("#d9a441") + (255,))
    s.outline("#0c0604")
    return s.save("bar_tapestry")


def decal_poster(name, base, accent, seed):
    s = Sheet(72, 104)
    rng = np.random.default_rng(seed)
    s.shaded(lambda d: d.rectangle([2, 2, 69, 101], fill=255), base)
    s.d.rectangle([6, 6, 65, 97], outline=hexc(accent) + (255,))
    s.d.ellipse([16, 14, 56, 54], fill=hexc(accent) + (255,))
    s.d.ellipse([22, 20, 50, 48], fill=hexc(base[1]) + (255,))
    for k in range(5):  # a sound wave across the middle and print lines
        y = 66 + k * 5
        w = int(rng.integers(20, 52))
        s.d.rectangle([10, y, 10 + w, y + 1], fill=hexc(accent) + ((255 if k < 2 else 160),))
    for x in range(10, 62, 4):
        hh = int(rng.integers(2, 10))
        s.d.rectangle([x, 34 - hh, x + 1, 34 + hh], fill=hexc("#fff0c0") + (255,))
    s.d.polygon([(0, 0), (8, 0), (0, 8)], fill=(0, 0, 0, 80))  # a curled corner
    s.outline("#0c0604")
    return s.save(name)


def decal_sign(name, glyph):
    """A copper plate over a way, with an arrow and a picture (no words): 'booth' headphones, 'floor' a note over waves, 'chill' a sofa."""
    s = Sheet(112, 56)
    s.shaded(lambda d: d.rounded_rectangle([2, 2, 109, 53], radius=6, fill=255), COPPER)
    for (x, y) in ((8, 8), (103, 8), (8, 47), (103, 47)):
        s.d.rectangle([x - 1, y - 1, x + 1, y + 1], fill=hexc("#ffe0a0") + (255,))
    dk = hexc("#2a1208") + (255,)
    if glyph == "booth":  # headphones
        s.d.arc([30, 10, 66, 46], 180, 360, fill=dk, width=4)
        s.d.rectangle([28, 26, 36, 40], fill=dk)
        s.d.rectangle([60, 26, 68, 40], fill=dk)
        s.d.polygon([(80, 40), (96, 28), (96, 40)], fill=dk)
        s.d.polygon([(80, 22), (90, 16), (90, 28)], fill=dk)
    elif glyph == "floor":  # a note over waves
        s.d.ellipse([30, 30, 44, 42], fill=dk)
        s.d.line([(43, 36), (43, 12)], fill=dk, width=3)
        s.d.line([(43, 12), (56, 18)], fill=dk, width=3)
        for k in range(3):
            s.d.arc([58, 14 + k * 8, 92, 30 + k * 8], 20, 160, fill=dk, width=2)
    else:  # a sofa
        s.d.rounded_rectangle([28, 16, 74, 28], radius=4, fill=dk)
        s.d.rounded_rectangle([22, 24, 80, 38], radius=4, fill=dk)
        s.d.rectangle([28, 38, 32, 44], fill=dk)
        s.d.rectangle([70, 38, 74, 44], fill=dk)
        s.d.polygon([(86, 20), (100, 28), (86, 36)], fill=dk)
    s.outline("#0c0604")
    return s.save(name)


def decal_shelf(name="bar_shelf", n=14, seed=7):
    rng = np.random.default_rng(seed)
    w, h = 24 * n + 8, 160
    s = Sheet(w, h)
    s.shaded(lambda d: d.rectangle([0, 0, w - 1, h - 1], fill=255), ["#0a0504", "#180c08", "#2a140c"], dither=0.5)  # the dark back wall of the shelves
    cols = [["#06201a", "#0c4a3a", "#1a7a5a", "#5ad0a0"], ["#2a1204", "#5a2a0a", "#9a5418", "#e0a040"], ["#0a1a2a", "#16406a", "#2a74b0", "#8ac8f0"], ["#2a0a10", "#5a1424", "#9a2a40", "#e06080"]]
    for row in range(2):
        yb = 70 + row * 78
        for k in range(n):
            x = 12 + k * 24
            hgt = int(rng.integers(30, 58))
            c = cols[int(rng.integers(0, 4))]
            s.shaded(lambda d, x=x, hgt=hgt, yb=yb: (d.rounded_rectangle([x - 8, yb - hgt, x + 8, yb], radius=3, fill=255), d.rectangle([x - 3, yb - hgt - 12, x + 3, yb - hgt + 3], fill=255)), c)
            s.d.rectangle([x - 5, yb - hgt // 2 - 3, x + 5, yb - hgt // 2 + 7], fill=hexc("#e8dcc0") + (255,))
        s.shaded(lambda d, yb=yb: d.rectangle([0, yb, w - 1, yb + 7], fill=255), COPPER)  # the shelf board
        glow(s, w // 2, yb - 20, w * 0.45, "#ffb050", 0.5)
    s.outline("#0c0604")
    return s.save(name)


def decal_ivy(name="bar_ivy", seed=9):
    rng = np.random.default_rng(seed)
    s = Sheet(112, 144)
    greens = [hexc(c) for c in ("#12300e", "#245a1c", "#3c8a2a", "#7ac04a", "#c0e878")]
    for k in range(5):  # trailing vines from the top
        x = 10 + k * 22 + int(rng.integers(-5, 5))
        for y in range(0, int(rng.integers(80, 140)), 3):
            x += int(rng.integers(-1, 2))
            s.d.rectangle([x, y, x + 1, y + 2], fill=greens[0] + (255,))
    for _ in range(110):
        x, y = int(rng.integers(6, 106)), int(rng.integers(2, 130 if rng.random() > 0.4 else 80))
        r = int(rng.integers(3, 6))
        c = greens[int(rng.integers(1, 5))]
        s.d.polygon([(x, y - r), (x + r, y), (x, y + r), (x - r, y)], fill=c + (255,), outline=greens[0] + (255,))
        s.d.line([(x, y - r), (x, y + r)], fill=greens[0] + (255,))
    return s.save(name)


def decal_pipe_h():
    s = Sheet(320, 40)
    s.shaded(lambda d: d.rectangle([0, 8, 319, 32], fill=255), COPPER, light=(0.0, -0.95))
    for x in (40, 120, 200, 280):
        s.shaded(lambda d, x=x: d.rectangle([x, 3, x + 12, 37], fill=255), COPPER, light=(0.0, -0.95))
        for y in (8, 30):
            s.d.rectangle([x + 5, y - 1, x + 7, y + 2], fill=hexc("#ffe0a0") + (255,))
    s.outline()
    return s.save("bar_pipe_h")


def decal_rack():
    s = Sheet(112, 144)
    s.shaded(lambda d: d.rectangle([0, 0, 111, 143], fill=255), ["#06080c", "#10141a", "#1c2028", "#2c3440"])
    rng = np.random.default_rng(14)
    for r in range(7):
        y = 6 + r * 19
        s.d.rectangle([6, y, 105, y + 15], fill=hexc("#232a36") + (255,), outline=hexc("#4a5568") + (255,))
        for k in range(10):
            c = ["#ff3a2a", "#2af0d8", "#ffb040", "#3a3a48"][int(rng.integers(0, 4))]
            s.d.rectangle([10 + k * 8, y + 4, 12 + k * 8, y + 7], fill=hexc(c) + (255,))
        s.d.rectangle([12, y + 10, 40, y + 11], fill=hexc("#0a0e14") + (255,))
    glow(s, 56, 60, 70, "#ff3a2a", 0.25)
    s.outline("#06080c")
    return s.save("bar_rack")


def decal_window():
    """The booth's window: dark glass with a teal glow, a copper frame and mullions."""
    s = Sheet(176, 96)
    s.shaded(lambda d: d.rectangle([0, 0, 175, 95], fill=255), ["#041418", "#08323a", "#0e5a60", "#18878a"], light=(0.2, -0.9), dither=1.0)
    for x in (58, 116):
        s.d.rectangle([x, 4, x + 3, 91], fill=hexc("#5a2a12") + (255,))
    s.d.rectangle([4, 46, 171, 49], fill=hexc("#5a2a12") + (255,))
    s.d.rectangle([0, 0, 175, 4], fill=hexc("#8f4a1c") + (255,))
    s.d.rectangle([0, 91, 175, 95], fill=hexc("#8f4a1c") + (255,))
    s.d.rectangle([0, 0, 4, 95], fill=hexc("#8f4a1c") + (255,))
    s.d.rectangle([171, 0, 175, 95], fill=hexc("#8f4a1c") + (255,))
    for k in range(5):  # lit equipment seen through
        s.d.rectangle([10 + k * 11, 60, 14 + k * 11, 64], fill=hexc(["#ff3a2a", "#2af0d8"][k % 2]) + (255,))
    s.outline("#0c0604")
    return s.save("bar_window")


def decal_door_floor():
    """The doorway to the Floor: a blue-lit lattice door, ivy on one side."""
    s = Sheet(112, 176)
    s.shaded(lambda d: d.rectangle([0, 0, 111, 175], fill=255), ["#050a2a", "#0c1a6a", "#1c3ab8", "#3a62f0", "#7aa0ff"], light=(0.0, -0.9), dither=1.0)
    for x in range(8, 104, 12):
        s.d.line([(x, 8), (x, 175)], fill=hexc("#0a1240") + (255,))
    for y in range(12, 175, 14):
        s.d.line([(4, y), (108, y)], fill=hexc("#0a1240") + (255,))
    s.d.rectangle([0, 0, 111, 6], fill=hexc("#5a2a12") + (255,))
    for x in (0, 105):
        s.d.rectangle([x, 0, x + 6, 175], fill=hexc("#8f4a1c") + (255,))
    glow(s, 56, 120, 80, "#5a8aff", 0.6)
    s.outline("#0c0604")
    return s.save("bar_door_floor")


def decal_curtain():
    s = Sheet(112, 176)
    s.d.rectangle([0, 0, 111, 10], fill=hexc("#6a3416") + (255,))
    for side, x0 in ((0, 0), (1, 62)):
        s.shaded(lambda d, x0=x0, side=side: d.polygon([(x0, 8), (x0 + 50, 8), (x0 + (44 if side == 0 else 50), 172), (x0 + (0 if side == 0 else 6), 172)], fill=255),
                 ["#06201f", "#0c4a4a", "#188084", "#2fa8a8", "#6ad8d0"], light=(-0.9, 0.0), dither=1.0)
        for k in range(5):
            x = x0 + 8 + k * 9
            s.d.line([(x, 12), (x + (2 if side else -2), 170)], fill=hexc("#06201f") + (200,))
        s.d.line([(x0 + 4, 60), (x0 + 46, 60)], fill=hexc("#d9a441") + (255,))
    s.d.rectangle([48, 10, 64, 172], fill=(255, 190, 110, 70))  # warm light through the gap
    s.outline("#0c0604")
    return s.save("bar_curtain")


def spr_crates_stack():
    return spr_crate("bar_crate_tall", 64, 96, 4)


def sheet_of(names, path):
    ims = [Image.open(os.path.join(OUT, n + ".png")).convert("RGBA") for n in names]
    cols = 8
    cell = 160
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGBA", (cols * cell, rows * cell), (22, 14, 20, 255))
    for i, im in enumerate(ims):
        k = min(cell / im.width, cell / im.height, 2.0)
        r = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.NEAREST)
        sh.alpha_composite(r, ((i % cols) * cell + (cell - r.width) // 2, (i // cols) * cell + (cell - r.height) // 2))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sh.convert("RGB").save(path)


def main():
    tiles = {"bar_brick": tile_brick(), "bar_cobble": tile_cobble(), "bar_planks": tile_planks(), "bar_step": tile_step(), "bar_counter_front": tile_counter_front(),
             "bar_copper": tile_copper(), "bar_water": tile_water(), "bar_grate": tile_grate(), "bar_quay": tile_quay(), "bar_ceiling": tile_ceiling(), "bar_booth_wall": tile_booth_wall(),
             "bar_brick_lit": tile_brick("b2", 7, rows=8, moss=False)}
    for n, a in tiles.items():
        save(n, a)
    rgb, a = tile_rail()
    save("bar_railing", rgb, a)
    sprites = [spr_pendant, spr_lantern, lambda: spr_crate(), spr_crates_stack, spr_jug, spr_stool, spr_taps, spr_bottles, lambda: spr_bottles("bar_bottles_b", 4, 8), spr_glass, spr_pipe_col, spr_sofa, spr_rug,
               decal_tapestry, lambda: decal_poster("bar_poster_a", ["#0c1a3a", "#16306a", "#2a52a0", "#5a8ae0"], "#ffb050", 1), lambda: decal_poster("bar_poster_b", ["#2a0a10", "#5a1424", "#9a2a40", "#e06080"], "#7ae0d8", 2),
               lambda: decal_sign("bar_sign_booth", "booth"), lambda: decal_sign("bar_sign_floor", "floor"), lambda: decal_sign("bar_sign_chill", "chill"), decal_shelf, decal_ivy, decal_pipe_h, decal_rack, decal_window,
               decal_door_floor, decal_curtain]
    for f in sprites:
        f()
    names = sorted(os.path.splitext(f)[0] for f in os.listdir(OUT) if f.endswith(".png") and not f.startswith("guide_"))
    sheet_of(names, SHEET)
    print("wrote %d images to %s" % (len(names), OUT))


if __name__ == "__main__":
    sys.exit(main())
