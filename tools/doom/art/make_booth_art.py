"""The DJ Booth's placeholder art (docs/doom/scenes/booth.md): textures, props, decals and the three guides, written to assets/story/doom_booth/textures/.

    python -I tools/doom/art/make_booth_art.py

PLACEHOLDER art, procedural (PIL, hashed noise, ordered dither), at the style guide's pixel density (128 texels per metre for walls and floors) and in the painting's palette (olive acoustic
foam, rust and steel, amber task light, red LEDs, a violet chamber ahead, wet concrete on the dock). It is below the owner's standard (art/reference/standard/guide_floor_sprite_standard.png);
an art pass replaces the PNGs: the file names, sizes and frames per state are the data contract. The guides are drawn by tools/doom/art/make_guides.py with the colours of the painting's
three guides (the white-haired balcony guide in the long coat and red scarf, the horned violet guide of the mothership, the bald dock guide in the green raincoat with the yellow armband).
"""
from __future__ import annotations

import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "assets", "story", "doom_booth", "textures")
S = 128


def hexc(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3])


def speckle(im, amt, seed, keep_alpha=True):
    """Hashed per-pixel brightness noise (the weathering): in place."""
    rnd = random.Random(seed)
    px = im.load()
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            if len(p) == 4 and p[3] == 0:
                continue
            k = 1.0 + (rnd.random() - 0.5) * amt
            px[x, y] = (*shade(p, k), p[3]) if len(p) == 4 else shade(p, k)
    return im


def rust(im, seed, amt=0.35, col=(150, 80, 36)):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(im)
    for _ in range(int(im.width * im.height * amt / 40)):
        x, y = rnd.randrange(im.width), rnd.randrange(im.height)
        w, h = rnd.randint(1, 4), rnd.randint(1, 3)
        d.rectangle([x, y, x + w, y + h], fill=shade(col, 0.6 + rnd.random() * 0.7))
    return im


# --- textures (tile 128 x 128) -------------------------------------------------------------------------------------------------------------------------------

def wall_foam():
    im = Image.new("RGB", (S, S), hexc("#4a4a26"))
    d = ImageDraw.Draw(im)
    for x in range(0, S, 16):  # vertical ribbed foam panels, 16 texels wide, a dark seam, a lit ridge
        d.rectangle([x, 0, x + 1, S], fill=hexc("#1e1f0f"))
        for k in range(2, 16):
            t = abs(k - 8) / 8.0
            d.line([(x + k, 0), (x + k, S)], fill=shade(hexc("#6a6a34"), 0.7 + 0.5 * (1 - t) ** 1.5))
    for y in (0, 64):  # horizontal trim bands
        d.rectangle([0, y, S, y + 5], fill=hexc("#5a3a22"))
        d.rectangle([0, y + 5, S, y + 6], fill=hexc("#2a1a10"))
    return rust(speckle(im, 0.22, 11), 12, 0.25)


def wall_steel():
    im = Image.new("RGB", (S, S), hexc("#5a4048"))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, S - 1, 3], fill=hexc("#8a6050"))
    for y in (32, 96):
        d.rectangle([0, y, S, y + 2], fill=hexc("#2a1a22"))
    for y in (16, 48, 80, 112):  # rivet rows
        for x in range(8, S, 16):
            d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=hexc("#9a7a68"))
    return rust(speckle(im, 0.25, 21), 22, 0.45)


def wall_dock():
    im = Image.new("RGB", (S, S), hexc("#33261f"))
    d = ImageDraw.Draw(im)
    for row, y in enumerate(range(0, S, 16)):  # brick courses
        off = 0 if row % 2 == 0 else 16
        d.line([(0, y), (S, y)], fill=hexc("#1c140f"))
        for x in range(-off, S, 32):
            d.line([(x, y), (x, y + 16)], fill=hexc("#1c140f"))
    return rust(speckle(im, 0.35, 31), 32, 0.07, (110, 84, 40))


def wall_moth():
    im = Image.new("RGB", (S, S), hexc("#4a2e6a"))
    d = ImageDraw.Draw(im)
    for x in range(0, S, 32):  # violet ribs with a mint core
        for k in range(32):
            t = abs(k - 16) / 16.0
            d.line([(x + k, 0), (x + k, S)], fill=shade(hexc("#7a52a8"), 0.55 + 0.7 * (1 - t) ** 1.4))
        d.line([(x + 16, 0), (x + 16, S)], fill=hexc("#8fe0c0"))
    return speckle(im, 0.2, 41)


def floor_plate():
    im = Image.new("RGB", (S, S), hexc("#3a2a26"))
    d = ImageDraw.Draw(im)
    for gy in range(0, S, 16):  # diamond plate: short raised bars at alternating diagonals
        for gx in range(0, S, 16):
            if ((gx + gy) // 16) % 2:
                d.line([(gx + 3, gy + 12), (gx + 12, gy + 3)], fill=hexc("#8a5a38"), width=2)
            else:
                d.line([(gx + 3, gy + 3), (gx + 12, gy + 12)], fill=hexc("#8a5a38"), width=2)
    return rust(speckle(im, 0.3, 51), 52, 0.2)


def floor_grate():
    im = Image.new("RGB", (S, S), hexc("#14100e"))
    d = ImageDraw.Draw(im)
    for k in range(0, S, 8):
        d.line([(k, 0), (k, S)], fill=hexc("#5a3a22"))
        d.line([(0, k), (S, k)], fill=hexc("#3a2616"))
    return speckle(im, 0.3, 61)


def floor_conc():
    im = Image.new("RGB", (S, S), hexc("#3e362e"))
    d = ImageDraw.Draw(im)
    d.polygon([(0, 70), (S, 20), (S, 40), (0, 90)], fill=hexc("#a8821e"))  # the yellow floor stripe (wet)
    for y in range(0, S, 8):
        d.line([(0, y + (y // 8) % 3), (S, y + (y // 8) % 3)], fill=hexc("#4e443a"))
    return speckle(im, 0.4, 71)


def floor_moth():
    im = Image.new("RGB", (S, S), hexc("#4a4060"))
    d = ImageDraw.Draw(im)
    for k in range(0, S, 32):
        d.line([(k, 0), (k, S)], fill=hexc("#8fe0c0"))
        d.line([(0, k), (S, k)], fill=hexc("#2c2440"))
    return speckle(im, 0.25, 81)


def ceil_tile():
    im = Image.new("RGB", (S, S), hexc("#2a1c16"))
    d = ImageDraw.Draw(im)
    for k in (0, 64):
        d.rectangle([k, 0, k + 1, S], fill=hexc("#1c1210"))
        d.rectangle([0, k, S, k + 1], fill=hexc("#1c1210"))
    for y in range(8, S, 16):
        for x in range(8, S, 16):
            d.point((x, y), fill=hexc("#1c1210"))
    return rust(speckle(im, 0.25, 91), 92, 0.12, (90, 56, 32))


def trim():
    im = Image.new("RGB", (S, S), hexc("#6a4a38"))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, S, 8], fill=hexc("#9a6a44"))
    d.rectangle([0, 56, S, 60], fill=hexc("#2a1a12"))
    return rust(speckle(im, 0.3, 101), 102, 0.3)


def rail_tile():
    """The desk edge: a handrail on posts every metre with two bars and a kick plate; the rest alpha 0."""
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    steel, light, dark = hexc("#6a4a34"), hexc("#9a7050"), hexc("#2a1a10")
    d.rectangle([0, 6, S, 13], fill=(*steel, 255))
    d.rectangle([0, 6, S, 7], fill=(*light, 255))
    d.rectangle([0, 12, S, 13], fill=(*dark, 255))
    for y in (46, 80):
        d.rectangle([0, y, S, y + 3], fill=(*steel, 255))
    d.rectangle([0, 6, 7, S], fill=(*steel, 255))  # post
    d.rectangle([0, 6, 1, S], fill=(*light, 255))
    d.rectangle([0, 108, S, S], fill=(*dark, 255))  # kick plate
    d.rectangle([0, 108, S, 110], fill=(*steel, 255))
    return im


def window_tile():
    """The window onto the balcony: a fine wire mesh (the painting's chain-link) in a steel frame; alpha 0 elsewhere (the rain and the balcony show through)."""
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    wire, light = hexc("#1c1612"), hexc("#4a3e36")
    for k in range(-S, S * 2, 8):
        d.line([(k, 0), (k + S, S)], fill=(*wire, 255))
        d.line([(k + S, 0), (k, S)], fill=(*wire, 255))
    for k in range(-S, S * 2, 32):  # a light thread now and then
        d.line([(k, 0), (k + S, S)], fill=(*light, 255))
    steel = hexc("#4a3428")
    d.rectangle([0, 0, S, 5], fill=(*steel, 255))
    d.rectangle([0, S - 6, S, S], fill=(*steel, 255))
    d.rectangle([0, 0, 5, S], fill=(*steel, 255))
    return im


# --- props (billboards) and decals ---------------------------------------------------------------------------------------------------------------------

def canvas(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def outline(im, col="#0e0806"):
    a = im.split()[3].point(lambda v: 255 if v > 127 else 0)
    from PIL import ImageFilter
    grown = a.filter(ImageFilter.MaxFilter(3))
    ring = Image.new("RGBA", im.size, (*hexc(col), 255))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(ring, mask=grown)
    out.alpha_composite(im)
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            if px[x, y][3] not in (0, 255):
                px[x, y] = (*px[x, y][:3], 255 if px[x, y][3] > 127 else 0)
    return out


def turntable():
    im, d = canvas(96, 64)
    d.polygon([(4, 24), (92, 24), (96, 56), (0, 56)], fill=hexc("#6a4a38"))  # the plinth, top face lighter
    d.polygon([(4, 24), (92, 24), (94, 34), (2, 34)], fill=hexc("#8a6248"))
    d.ellipse([10, 20, 70, 44], fill=hexc("#101010"))  # the record
    d.ellipse([30, 28, 50, 36], fill=hexc("#c22030"))
    d.ellipse([38, 31, 42, 33], fill=hexc("#f0e0c0"))
    d.line([(84, 26), (60, 32)], fill=hexc("#d8c8b0"), width=2)  # the tonearm
    d.ellipse([78, 24, 90, 32], fill=hexc("#c0b098"))
    d.ellipse([72, 40, 78, 46], fill=hexc("#d8c8b0"))  # the pitch knob
    for x in range(10, 90, 12):
        d.rectangle([x, 50, x + 3, 53], fill=hexc("#2a1a12"))
    return outline(speckle(im, 0.2, 5))


def mixer():
    im, d = canvas(128, 72)
    d.polygon([(6, 20), (122, 20), (128, 64), (0, 64)], fill=hexc("#4a3a36"))
    d.polygon([(6, 20), (122, 20), (124, 30), (4, 30)], fill=hexc("#6a5650"))
    rnd = random.Random(8)
    for i in range(12):  # channel faders with caps and LED meters
        x = 10 + i * 9
        d.rectangle([x, 34, x + 1, 56], fill=hexc("#120c0a"))
        y = 36 + rnd.randint(0, 16)
        d.rectangle([x - 2, y, x + 3, y + 4], fill=hexc("#c8b8a0"))
        for k in range(4):
            on = k < rnd.randint(1, 4)
            d.rectangle([x - 1, 22 + k * 2, x + 2, 23 + k * 2], fill=hexc("#ff3030") if on else hexc("#401010"))
    for x in (12, 40, 68, 96):  # knobs
        d.ellipse([x, 26, x + 5, 31], fill=hexc("#d8d0c0"))
    d.rectangle([100, 34, 120, 52], fill=hexc("#201816"))  # a small display, amber
    d.rectangle([102, 36, 118, 40], fill=hexc("#ffb040"))
    return outline(speckle(im, 0.2, 9))


def lamp():
    im, d = canvas(72, 112)
    d.ellipse([6, 100, 40, 110], fill=hexc("#303030"))
    d.line([(24, 104), (30, 60)], fill=hexc("#5a5a5a"), width=3)
    d.line([(30, 60), (52, 30)], fill=hexc("#5a5a5a"), width=3)
    d.polygon([(40, 18), (68, 12), (66, 40), (46, 38)], fill=hexc("#3a3a3a"))  # the shade
    d.polygon([(46, 38), (66, 40), (62, 46), (50, 44)], fill=hexc("#ffd890"))  # the lit mouth
    d.ellipse([28, 56, 34, 62], fill=hexc("#a08060"))
    return outline(im)


def stool():
    im, d = canvas(56, 72)
    d.ellipse([4, 4, 52, 24], fill=hexc("#7a2a2a"))
    d.rectangle([4, 14, 52, 26], fill=hexc("#5a1c1c"))
    d.ellipse([4, 20, 52, 32], fill=hexc("#6a2424"))
    d.rectangle([26, 32, 29, 62], fill=hexc("#8a8a8a"))
    d.ellipse([10, 58, 46, 70], outline=hexc("#8a8a8a"), width=2)
    return outline(speckle(im, 0.4, 13))


def rack(tall=True):
    h = 112 if tall else 72
    im, d = canvas(72, h)
    d.rectangle([2, 2, 69, h - 3], fill=hexc("#2e2420"))
    rnd = random.Random(15)
    y = 6
    while y < h - 18:  # rack units, each with a row of red LEDs
        u = rnd.choice([12, 16])
        d.rectangle([6, y, 65, y + u - 2], fill=hexc("#4a3c38"))
        d.rectangle([6, y, 65, y + 1], fill=hexc("#6a5a54"))
        for k in range(rnd.randint(3, 9)):
            on = rnd.random() < 0.7
            d.rectangle([10 + k * 6, y + 4, 12 + k * 6, y + 6], fill=hexc("#ff3028") if on else hexc("#501410"))
        y += u
    return outline(speckle(im, 0.2, 16))


def cables():
    """A tangled heap of red and black cable on the floor (filled, lumpy: not a ring)."""
    im, d = canvas(72, 56)
    rnd = random.Random(14)
    d.ellipse([4, 22, 68, 54], fill=hexc("#181212"))
    for k in range(26):
        col = "#b02028" if k % 3 == 0 else "#241a1a"
        x, y = rnd.randint(8, 52), rnd.randint(14, 40)
        d.ellipse([x, y, x + rnd.randint(10, 18), y + rnd.randint(8, 14)], fill=hexc(col), outline=hexc("#0c0808"))
    d.line([(6, 50), (30, 40), (66, 52)], fill=hexc("#b02028"), width=3)
    return outline(im)


def cage_lamp():
    """The painting's caged ceiling lamp: an amber bulb in a steel cage; emissive in effect (a bright sprite)."""
    im, d = canvas(40, 48)
    d.rectangle([14, 0, 26, 6], fill=hexc("#3a3028"))
    d.rounded_rectangle([6, 6, 34, 40], radius=8, fill=hexc("#ffc060"))
    d.ellipse([12, 14, 28, 34], fill=hexc("#fff0b8"))
    for x in (10, 18, 26, 32):
        d.line([(x, 6), (x, 40)], fill=hexc("#4a3a2c"), width=2)
    for y in (16, 28):
        d.line([(6, y), (34, y)], fill=hexc("#4a3a2c"), width=2)
    d.rectangle([4, 38, 36, 44], fill=hexc("#3a3028"))
    return outline(im)


def case():
    im, d = canvas(72, 64)
    d.rectangle([2, 8, 69, 60], fill=hexc("#3a3a40"))
    d.rectangle([2, 8, 69, 18], fill=hexc("#54545c"))
    for x, y in ((2, 8), (62, 8), (2, 52), (62, 52)):
        d.rectangle([x, y, x + 7, y + 7], fill=hexc("#a8a8b0"))
    d.rectangle([30, 34, 42, 40], fill=hexc("#a8a8b0"))
    d.line([(2, 34), (69, 34)], fill=hexc("#18181c"), width=1)
    return outline(speckle(im, 0.3, 17))


def records():
    im, d = canvas(72, 64)
    rnd = random.Random(19)
    for k in range(14):
        col = rnd.choice(["#c8302c", "#d8a030", "#2c5a8a", "#e0d8c0", "#8a2a5a", "#3a6a3a"])
        d.rectangle([4 + k * 4, 10 + rnd.randint(0, 6), 7 + k * 4, 60], fill=hexc(col))
    d.rectangle([2, 56, 68, 62], fill=hexc("#4a3226"))
    return outline(im)


def crystal():
    im, d = canvas(96, 128)
    for x, w, h, c in ((10, 14, 70, "#b8a0e8"), (28, 18, 110, "#d0b8ff"), (50, 14, 90, "#a890d8"), (66, 12, 58, "#c0a8f0")):
        d.polygon([(x, 124), (x + w, 124), (x + w * 0.7, 124 - h), (x + w * 0.3, 124 - h - 10)], fill=hexc(c))
        d.line([(x + w * 0.4, 124), (x + w * 0.45, 124 - h)], fill=hexc("#f0e8ff"), width=2)
    return outline(im)


def moth_console():
    im, d = canvas(128, 56)
    d.polygon([(0, 56), (10, 18), (118, 18), (128, 56)], fill=hexc("#5a4478"))
    for k in range(10):
        d.rectangle([20 + k * 10, 24, 25 + k * 10, 28], fill=hexc("#8fe0c0") if k % 3 else hexc("#ffb0d0"))
    return outline(im)


def screen_decal():
    """A wall monitor: the painting's amber window grid; emissive."""
    im, d = canvas(64, 48)
    d.rectangle([0, 0, 63, 47], fill=hexc("#1a1210"))
    d.rectangle([3, 3, 60, 44], fill=hexc("#2a1c10"))
    rnd = random.Random(23)
    for gy in range(6, 42, 6):
        for gx in range(6, 58, 6):
            if rnd.random() < 0.6:
                d.rectangle([gx, gy, gx + 3, gy + 3], fill=hexc(rnd.choice(["#ffb040", "#ffd070", "#ff8030"])))
    return im


def screen_wave():
    im, d = canvas(64, 48)
    d.rectangle([0, 0, 63, 47], fill=hexc("#1a1210"))
    d.rectangle([3, 3, 60, 44], fill=hexc("#0c1a1a"))
    pts = [(4 + i, 24 + int(math.sin(i * 0.5) * (10 - abs(i - 28) * 0.3))) for i in range(0, 56)]
    d.line(pts, fill=hexc("#60ffd0"), width=2)
    d.line([(4, 24), (59, 24)], fill=hexc("#1c4a40"))
    return im


def led_strip():
    im, d = canvas(64, 12)
    d.rectangle([0, 3, 63, 8], fill=hexc("#201010"))
    for k in range(0, 64, 5):
        d.rectangle([k + 1, 4, k + 3, 7], fill=hexc("#ff3028"))
    return im


def vent_door():
    """A steel door with a louvred vent and a lever handle (the painting's open door's leaf)."""
    im, d = canvas(96, 192)
    d.rectangle([0, 0, 95, 191], fill=hexc("#7a5a44"))
    d.rectangle([4, 4, 91, 187], fill=hexc("#8a6a50"))
    for k in range(10):
        d.rectangle([28, 20 + k * 6, 68, 22 + k * 6], fill=hexc("#1c1210"))
        d.rectangle([28, 22 + k * 6, 68, 23 + k * 6], fill=hexc("#b08a68"))
    d.rectangle([12, 104, 40, 110], fill=hexc("#c0c0c8"))  # lever handle
    d.rectangle([10, 100, 16, 116], fill=hexc("#a0a0a8"))
    return speckle(rust(im, 29, 0.5), 0.3, 30)


def cable_shelf():
    im, d = canvas(96, 112)
    d.rectangle([0, 8, 95, 14], fill=hexc("#4a3a30"))
    d.rectangle([0, 64, 95, 70], fill=hexc("#4a3a30"))
    for sy in (8, 64):  # coils hung on hooks above each shelf
        for k, col in enumerate(["#b02028", "#161616", "#b02028", "#161616"]):
            x = 8 + k * 22
            d.ellipse([x, sy - 52 + 6, x + 20, sy + 4], outline=hexc(col), width=4)
    d.rectangle([60, 30, 92, 62], fill=hexc("#5a4030"))  # a box on the lower shelf
    return outline(im)


def pipe_run():
    im, d = canvas(32, 192)
    for x, col in ((4, "#9a2a28"), (14, "#2a2020"), (24, "#9a2a28")):
        d.rectangle([x, 0, x + 6, 191], fill=hexc(col))
        d.rectangle([x, 0, x + 1, 191], fill=hexc(col) and shade(hexc(col), 1.6))
    for y in range(12, 192, 48):
        d.rectangle([0, y, 31, y + 5], fill=hexc("#6a5a50"))
    return im


def shutter():
    im, d = canvas(192, 128)
    d.rectangle([0, 0, 191, 127], fill=hexc("#2e2822"))
    for y in range(0, 128, 8):
        d.rectangle([0, y, 191, y + 6], fill=hexc("#3e362e"))
        d.rectangle([0, y + 7, 191, y + 7], fill=hexc("#1c1612"))
    return speckle(im, 0.3, 33)


def skyline():
    """The night city beyond the balcony: layered silhouettes with lit windows and a red aircraft lamp; emissive."""
    W, H = 384, 192
    im, d = canvas(W, H)
    rnd = random.Random(35)
    d.rectangle([0, 0, W, H], fill=hexc("#10162a"))
    for layer, (base, col, win) in enumerate((("#1a2240", 90, "#8a7a50"), ("#141a30", 60, "#c89a50"), ("#0e1224", 30, "#ffb050"))):
        x = 0
        while x < W:
            bw = rnd.randint(16, 40)
            bh = rnd.randint(40, 40 + col + 40)
            d.rectangle([x, H - bh, x + bw, H], fill=hexc(base))
            for wy in range(H - bh + 6, H - 6, 8):
                for wx in range(x + 4, x + bw - 4, 7):
                    if rnd.random() < 0.28:
                        d.rectangle([wx, wy, wx + 2, wy + 3], fill=hexc(win))
            x += bw + rnd.randint(0, 6)
    d.rectangle([300, 20, 302, 24], fill=hexc("#ff2020"))
    for _ in range(140):  # rain
        x, y = rnd.randrange(W), rnd.randrange(H)
        d.line([(x, y), (x - 2, y + 8)], fill=hexc("#6a7aa8"))
    return im


TEXTURES = {"bt_wall_foam": wall_foam, "bt_wall_steel": wall_steel, "bt_wall_dock": wall_dock, "bt_wall_moth": wall_moth, "bt_floor_plate": floor_plate, "bt_floor_grate": floor_grate,
            "bt_floor_conc": floor_conc, "bt_floor_moth": floor_moth, "bt_ceil": ceil_tile, "bt_trim": trim, "bt_rail": rail_tile, "bt_window": window_tile}
PROPS = {"bt_turntable": turntable, "bt_mixer": mixer, "bt_lamp": lamp, "bt_stool": stool, "bt_rack": rack, "bt_cables": cables, "bt_case": case, "bt_records": records,
         "bt_crystal": crystal, "bt_cage_lamp": cage_lamp, "bt_moth_console": moth_console, "bt_rack_short": lambda: rack(False)}
DECALS = {"bt_screen": screen_decal, "bt_screen_wave": screen_wave, "bt_led": led_strip, "bt_vent_door": vent_door, "bt_cable_shelf": cable_shelf, "bt_pipes": pipe_run,
          "bt_shutter": shutter, "bt_skyline": skyline}


def guides():
    import make_guides as mg
    base = {k: dict(v) for k, v in mg.GUIDES.items()}
    variants = {
        "balcony": ("stage", {}),  # white hair, long coat, red scarf: exactly the painting's balcony guide
        "mothership": ("stage", dict(skin="#d8c8e0", hair="#e8e0f8", top="#6a3a8e", vest="#4a2a6a", trousers="#2a1a3a", shoes="#1a1228", accent="#d8b0f0")),
        "dock": ("bar", dict(skin="#6a4630", hair="#6a4630", top="#3c4a22", vest="#46562a", trousers="#1c2218", shoes="#161410", curly=False, moustache=False, accent="#e0b020")),
    }
    n = 0
    for who, (arch, patch) in variants.items():
        mg.GUIDES[arch] = {**base[arch], **patch}
        for state, frames in mg.FRAMES.items():
            for i in range(frames):
                im = mg.draw_guide(arch, state, i)
                if who == "dock":  # the yellow armband and the coat's collar
                    d = ImageDraw.Draw(im)
                    d.rectangle([34, 96, 48, 104], fill=hexc("#e0b020"))
                im.save(os.path.join(OUT, "guide_%s_%s_%d.png" % (who, state, i)))
                n += 1
        mg.GUIDES[arch] = dict(base[arch])
    return n


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in {**TEXTURES, **PROPS, **DECALS}.items():
        fn().save(os.path.join(OUT, name + ".png"))
    n = guides()
    print("wrote %d textures, %d props, %d decals and %d guide frames to %s" % (len(TEXTURES), len(PROPS), len(DECALS), n, OUT))
    import make_booth_polish as bp  # stage D polish: the cropped desk and guides, 256 px foam/grate/concrete, the sky, the open shutter (they overwrite the placeholders above)
    k, g = bp.main()
    print("polish: %d images and %d guide frames (cropped from the painting)" % (k, g))


if __name__ == "__main__":
    sys.exit(main())
