"""The Underworld's placeholder art (docs/doom/scenes/underworld.md): textures, props and decals, written to assets/story/doom_underworld/textures/. The three guides come from
make_underworld_guides.py.

    python -I tools/doom/art/make_underworld_art.py

PLACEHOLDER art, procedural (PIL, hashed noise), at the style guide's pixel density (128 texels per metre for walls and floors) and in the painting's palette (black and aubergine basalt
columns, orange lava veins and glow, a blue-lit cave, a red cloud sky, bone and brass props, a patched tent). It is below the owner's standard (art/reference/standard/guide_floor_sprite_standard.png);
an art pass replaces the PNGs: the file names and sizes are the data contract.
"""
from __future__ import annotations

import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_booth_art as mb  # noqa: E402  (helpers only: hexc, shade, speckle, canvas, outline)

ROOT = mb.ROOT
OUT = os.path.join(ROOT, "assets", "story", "doom_underworld", "textures")
S = 128
hexc, shade, speckle, canvas, outline = mb.hexc, mb.shade, mb.speckle, mb.canvas, mb.outline
BAYER4 = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def veins(im, seed, col="#ff7a1c", amt=0.5, vertical=False):
    """Thin glowing cracks: random walks of one pixel (the lava in the basalt)."""
    rnd = random.Random(seed)
    d = ImageDraw.Draw(im)
    for _ in range(int(S * amt / 8)):
        x, y = rnd.randrange(S), rnd.randrange(S)
        for _k in range(rnd.randint(6, 22)):
            d.point((x % S, y % S), fill=shade(hexc(col), 0.7 + rnd.random() * 0.6))
            if vertical:
                y += 1
                x += rnd.choice((-1, 0, 0, 1))
            else:
                x += rnd.choice((-1, 0, 1))
                y += rnd.choice((-1, 0, 1))
    return im


def columns(base, lit, dark, seed, widths=(14, 18, 22), glow=None):
    """Basalt columns seen from the side: vertical prisms, a lit edge on the left, a dark one on the right, uneven tops."""
    rnd = random.Random(seed)
    im = Image.new("RGB", (S, S), hexc(dark))
    d = ImageDraw.Draw(im)
    x = 0
    while x < S:
        w = rnd.choice(widths)
        w = min(w, S - x) if S - x < 28 else w
        shade_k = 0.75 + rnd.random() * 0.5
        d.rectangle([x, 0, x + w - 1, S], fill=shade(hexc(base), shade_k))
        d.rectangle([x, 0, x + 3, S], fill=shade(hexc(lit), shade_k * 1.35))  # the lit edge (dithered into the face below)
        for yy in range(S):
            for xx in range(x + 4, x + 4 + max(2, w // 4)):
                if BAYER4[yy % 4][xx % 4] < 5:
                    im.putpixel((xx % S, yy), shade(hexc(lit), shade_k))
        d.rectangle([x + w - 6, 0, x + w - 1, S], fill=shade(hexc(dark), 0.55))  # the deep seam between prisms (stage D: contrast that survives the distance)
        for _ in range(3):  # a facet seam across the prism
            y = rnd.randrange(S)
            d.line([(x, y), (x + w, y + rnd.randint(-4, 4))], fill=hexc(dark))
        x += w
    if glow:
        veins(im, seed + 1, glow, 0.8, vertical=True)
    return speckle(im, 0.22, seed + 2)


def wall_rock():
    return columns("#2a2230", "#4a3a52", "#100c14", 3, widths=(26, 34, 42), glow="#d65a14")


def wall_cliff():
    im = columns("#241c2a", "#3e3048", "#0c0810", 7, widths=(18, 24, 30), glow="#ff6a14")
    d = ImageDraw.Draw(im)
    for y in (0, 62):  # a glowing seam where a lava flow crossed the face
        d.rectangle([0, y, S, y + 1], fill=hexc("#ff8a2a"))
        d.rectangle([0, y + 2, S, y + 3], fill=hexc("#8a2a10"))
    return im


def wall_step():
    im = Image.new("RGB", (S, S), hexc("#2c2430"))
    d = ImageDraw.Draw(im)
    for row, y in enumerate(range(0, S, 32)):  # cut blocks
        off = 0 if row % 2 == 0 else 24
        d.line([(0, y), (S, y)], fill=hexc("#060408"), width=4)
        d.line([(0, y + 3), (S, y + 3)], fill=hexc("#6a5470"), width=2)
        for x in range(-off, S, 48):
            d.line([(x, y), (x, y + 32)], fill=hexc("#060408"), width=3)
    return veins(speckle(im, 0.3, 31), 32, "#e0661a", 0.25)


def wall_cave():
    im = columns("#1c2236", "#34426a", "#080a14", 11, glow="#3a64ff")
    return im


def wall_tower():
    im = Image.new("RGB", (S, S), hexc("#241e2a"))
    d = ImageDraw.Draw(im)
    for x in range(0, S, 32):  # tall slabs
        d.rectangle([x, 0, x + 1, S], fill=hexc("#0c0810"))
        d.rectangle([x + 2, 0, x + 3, S], fill=hexc("#4a3c54"))
    d.rectangle([0, 0, S, 7], fill=hexc("#5a1a1a"))  # red trim bands with a gold thread
    d.rectangle([0, 7, S, 8], fill=hexc("#c8982a"))
    d.rectangle([0, 96, S, 103], fill=hexc("#5a1a1a"))
    d.rectangle([0, 103, S, 104], fill=hexc("#c8982a"))
    for x in range(8, S, 32):  # glyphs
        d.rectangle([x, 40, x + 6, 48], outline=hexc("#6a5a40"))
        d.line([(x + 3, 40), (x + 3, 56)], fill=hexc("#6a5a40"))
    return speckle(im, 0.25, 41)


def floor_slab():
    """Big flat basalt flagstones, cracked, with the lava showing orange in the cracks (the foreground of the painting)."""
    rnd = random.Random(51)
    im = Image.new("RGB", (S, S), hexc("#16101a"))
    d = ImageDraw.Draw(im)
    pts = [(rnd.randrange(S), rnd.randrange(S)) for _ in range(9)]
    for y in range(S):  # nearest-seed cells (wrapped): a stone per cell, edges where two seeds are equally near
        for x in range(S):
            best, second, bi = 1e9, 1e9, 0
            for i, (px, py) in enumerate(pts):
                dx, dy = min(abs(x - px), S - abs(x - px)), min(abs(y - py), S - abs(y - py))
                dd = dx * dx + dy * dy
                if dd < best:
                    second, best, bi = best, dd, i
                elif dd < second:
                    second = dd
            edge = math.sqrt(second) - math.sqrt(best)
            if edge < 2.2:
                im.putpixel((x, y), hexc("#e0661a") if edge < 1.0 and (x + y) % 3 else hexc("#3a1810"))
            else:
                k = 0.8 + 0.15 * ((bi * 37) % 7) / 7.0
                im.putpixel((x, y), shade(hexc("#3a3040"), k))
    return speckle(im, 0.3, 52)


def floor_stone():
    im = Image.new("RGB", (S, S), hexc("#2e2634"))
    d = ImageDraw.Draw(im)
    for row, y in enumerate(range(0, S, 32)):
        off = 0 if row % 2 == 0 else 32
        d.line([(0, y), (S, y)], fill=hexc("#0e0a12"), width=2)
        for x in range(-off, S, 64):
            d.line([(x, y), (x, y + 32)], fill=hexc("#0e0a12"), width=2)
    return veins(speckle(im, 0.35, 61), 62, "#d6561a", 0.15)


def floor_cave():
    im = Image.new("RGB", (S, S), hexc("#1a2034"))
    d = ImageDraw.Draw(im)
    for y in range(0, S, 24):
        d.line([(0, y), (S, y + 4)], fill=hexc("#0a0e1c"), width=2)
    for x in range(0, S, 32):
        d.line([(x, 0), (x + 3, S)], fill=hexc("#0a0e1c"), width=2)
    return veins(speckle(im, 0.35, 71), 72, "#3a64ff", 0.2)


def floor_tower():
    im = Image.new("RGB", (S, S), hexc("#262030"))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, S - 1, S - 1], outline=hexc("#0e0a12"), width=3)
    d.rectangle([14, 14, S - 15, S - 15], outline=hexc("#5a1a1a"), width=3)
    d.rectangle([20, 20, S - 21, S - 21], outline=hexc("#c8982a"), width=1)
    return speckle(im, 0.3, 81)


def floor_lava():
    """The lava seen from far above: dark crust plates, bright orange flow lines. Drawn lit by the void haze, so it is bright."""
    rnd = random.Random(91)
    im = Image.new("RGB", (S, S), hexc("#c43a12"))
    d = ImageDraw.Draw(im)
    for _ in range(26):
        x, y = rnd.randrange(S), rnd.randrange(S)
        w, h = rnd.randint(8, 26), rnd.randint(6, 16)
        d.ellipse([x, y, x + w, y + h], fill=hexc(rnd.choice(["#5a1408", "#6a1a0a", "#7a2010"])))
    for _ in range(18):  # the flow lines
        x, y = rnd.randrange(S), rnd.randrange(S)
        for _k in range(rnd.randint(18, 40)):
            d.rectangle([x % S, y % S, x % S + 1, y % S + 1], fill=hexc(rnd.choice(["#ffb020", "#ff8a1c", "#ffd860"])))
            x += rnd.choice((-1, 0, 1, 1))
            y += rnd.choice((-1, 0, 1))
    return speckle(im, 0.25, 92)


def ceil_cloud():
    rnd = random.Random(101)
    im = Image.new("RGB", (S, S), hexc("#4a0c0a"))
    d = ImageDraw.Draw(im)
    for _ in range(40):
        x, y = rnd.randrange(S), rnd.randrange(S)
        w, h = rnd.randint(20, 60), rnd.randint(6, 18)
        c = rnd.choice(["#6a1410", "#2a0606", "#8a2412", "#3a0a08"])
        for ox in (-S, 0, S):
            d.ellipse([x + ox, y, x + ox + w, y + h], fill=hexc(c))
    return speckle(im, 0.2, 102)


def rail_tile():
    """The rim: a chain slung between iron posts every metre (the painting has none; the brief wants the abyss shut), alpha 0 elsewhere."""
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    iron, light, dark = hexc("#3a3038"), hexc("#7a6a70"), hexc("#14101a")
    d.rectangle([0, 4, 9, S], fill=(*iron, 255))  # post
    d.rectangle([0, 4, 2, S], fill=(*light, 255))
    d.ellipse([-2, 0, 11, 11], fill=(*light, 255))
    for k, y0 in enumerate((22, 54)):  # two sagging chains
        for x in range(10, S, 6):
            y = y0 + int(6 * math.sin((x - 10) / (S - 10) * math.pi))
            d.ellipse([x, y, x + 5, y + 4], outline=(*light, 255), width=1)
            d.line([(x + 1, y + 2), (x + 4, y + 2)], fill=(*dark, 255))
    d.rectangle([0, 106, S, S], fill=(*dark, 255))  # kick plate
    d.rectangle([0, 106, S, 108], fill=(*iron, 255))
    return im


# --- props (billboards) and decals ---------------------------------------------------------------------------------------------------------------------

def pillar():
    """A tower monolith: tall dark prism with a red banner edged in gold and a lit window slot."""
    im, d = canvas(64, 192)
    d.polygon([(6, 190), (6, 20), (14, 4), (50, 4), (58, 20), (58, 190)], fill=hexc("#241e2a"))
    d.rectangle([6, 20, 14, 190], fill=hexc("#463a50"))
    d.rectangle([50, 20, 58, 190], fill=hexc("#100c14"))
    d.polygon([(22, 40), (42, 40), (42, 120), (32, 108), (22, 120)], fill=hexc("#8a1818"))  # the banner
    d.polygon([(22, 40), (42, 40), (42, 44), (22, 44)], fill=hexc("#d8a830"))
    d.line([(32, 50), (32, 96)], fill=hexc("#d8a830"), width=2)
    d.rectangle([29, 140, 35, 156], fill=hexc("#ffb040"))  # a lit slot
    for y in range(30, 190, 28):
        d.line([(6, y), (58, y)], fill=hexc("#100c14"))
    return outline(speckle(im, 0.3, 111), "#0a060c")


def tusks():
    """A pair of curved ivory tusks standing like a gate, with a few carved rings."""
    im, d = canvas(128, 160)
    for side in (-1, 1):
        cx = 64 + side * 30
        pts = []
        for k in range(0, 21):
            t = k / 20.0
            x = cx - side * (28 * math.sin(t * 1.2)) + side * 6
            y = 156 - 150 * t
            pts.append((x, y))
        for k, (x, y) in enumerate(pts):
            r = 11 * (1 - k / 24.0)
            d.ellipse([x - r, y - r, x + r, y + r], fill=hexc("#e8dcb8"))
            d.ellipse([x - r * 0.4 - side * r * 0.3, y - r * 0.6, x + r * 0.2 - side * r * 0.3, y + r * 0.1], fill=hexc("#fff8e0"))
    return outline(speckle(im, 0.2, 121), "#2a2018")


def bones():
    """A cord hung with bone chimes (the painting's left wall): decal."""
    im, d = canvas(128, 160)
    d.arc([-20, -60, 148, 40], 20, 160, fill=hexc("#8a1818"), width=3)
    rnd = random.Random(131)
    for k in range(7):
        x = 14 + k * 16
        top = 8 + int(14 * math.sin((x / 128.0) * math.pi))
        ln = rnd.randint(50, 100)
        d.line([(x, top), (x, top + 12)], fill=hexc("#8a1818"), width=2)
        d.rounded_rectangle([x - 4, top + 12, x + 4, top + 12 + ln], radius=3, fill=hexc("#e8dcc0"))
        d.ellipse([x - 7, top + 8, x + 1, top + 20], fill=hexc("#e8dcc0"))
        d.ellipse([x - 1, top + 8, x + 7, top + 20], fill=hexc("#e8dcc0"))
        d.ellipse([x - 7, top + 8 + ln, x + 1, top + 20 + ln], fill=hexc("#e8dcc0"))
        d.ellipse([x - 1, top + 8 + ln, x + 7, top + 20 + ln], fill=hexc("#e8dcc0"))
        d.rectangle([x - 5, top + 30, x + 5, top + 34], fill=hexc("#c82828"))
    return outline(im, "#2a1a10")


def gong():
    im, d = canvas(112, 160)
    d.rectangle([4, 8, 12, 156], fill=hexc("#7a4a22"))
    d.rectangle([100, 8, 108, 156], fill=hexc("#7a4a22"))
    d.rectangle([4, 8, 108, 16], fill=hexc("#8a5a2a"))
    d.line([(56, 16), (56, 30)], fill=hexc("#2a1a10"), width=2)
    d.ellipse([16, 28, 100, 112], fill=hexc("#b8862a"))
    d.ellipse([22, 34, 94, 106], outline=hexc("#e8c050"), width=3)
    d.ellipse([40, 52, 76, 88], fill=hexc("#8a6018"))
    d.ellipse([46, 58, 66, 74], fill=hexc("#e8c860"))
    d.rectangle([0, 150, 111, 159], fill=hexc("#5a3a1c"))
    return outline(speckle(im, 0.25, 141), "#1c1008")


def drum():
    im, d = canvas(72, 88)
    d.polygon([(10, 22), (62, 22), (56, 82), (16, 82)], fill=hexc("#9a5a26"))
    d.polygon([(10, 22), (22, 22), (26, 82), (16, 82)], fill=hexc("#c07a38"))
    d.ellipse([8, 14, 64, 32], fill=hexc("#e0c898"))
    d.ellipse([12, 17, 60, 29], outline=hexc("#6a4020"), width=2)
    for k in range(6):
        x = 14 + k * 8
        d.line([(x, 30), (x + 2, 70)], fill=hexc("#4a2a14"), width=2)
    d.rectangle([14, 78, 58, 84], fill=hexc("#6a3a18"))
    return outline(speckle(im, 0.25, 151), "#1c1008")


def cloth():
    """A crimson cloth with gold fringe slung over a rock."""
    im, d = canvas(112, 96)
    d.polygon([(4, 20), (100, 8), (108, 60), (90, 70), (60, 64), (30, 72), (8, 66)], fill=hexc("#8a1420"))
    d.polygon([(4, 20), (100, 8), (102, 20), (8, 32)], fill=hexc("#b82430"))
    for x in range(10, 104, 4):
        d.line([(x, 66 + (x % 8)), (x, 86 + (x % 12))], fill=hexc("#d8a830"), width=1)
    d.line([(8, 66), (100, 62)], fill=hexc("#d8a830"), width=2)
    d.line([(14, 40), (96, 28)], fill=hexc("#d8a830"), width=1)
    return outline(speckle(im, 0.25, 161), "#200808")


def tent():
    """A patched grey awning on two poles, a lantern bracket on the right pole."""
    im, d = canvas(192, 144)
    d.rectangle([6, 20, 14, 140], fill=hexc("#6a4222"))
    d.rectangle([176, 20, 184, 140], fill=hexc("#6a4222"))
    d.polygon([(0, 24), (192, 14), (192, 44), (150, 56), (110, 46), (70, 58), (30, 48), (0, 54)], fill=hexc("#8a8478"))
    d.polygon([(0, 24), (192, 14), (192, 24), (0, 34)], fill=hexc("#a8a290"))
    d.rectangle([46, 28, 76, 44], fill=hexc("#6a6458"))  # patches
    d.rectangle([116, 22, 140, 36], fill=hexc("#78705e"))
    for x in range(8, 188, 12):
        d.line([(x, 50 + (x % 7)), (x, 58 + (x % 5))], fill=hexc("#6a6458"), width=2)
    d.rectangle([20, 130, 172, 142], fill=hexc("#241c20"))
    return outline(speckle(im, 0.3, 171), "#14100c")


def lantern():
    im, d = canvas(40, 72)
    d.line([(20, 0), (20, 14)], fill=hexc("#20202a"), width=2)
    d.rectangle([8, 14, 32, 22], fill=hexc("#34343e"))
    d.rectangle([10, 22, 30, 56], fill=hexc("#ffc060"))
    d.rectangle([12, 28, 28, 50], fill=hexc("#fff0b0"))
    for x in (10, 20, 30):
        d.line([(x, 22), (x, 56)], fill=hexc("#20202a"), width=2)
    d.rectangle([8, 56, 32, 62], fill=hexc("#34343e"))
    return outline(im, "#0c0c10")


def crate():
    im, d = canvas(72, 64)
    d.rectangle([2, 6, 69, 60], fill=hexc("#7a5028"))
    d.rectangle([2, 6, 69, 14], fill=hexc("#a07038"))
    for x in (2, 32, 62):
        d.rectangle([x, 6, x + 7, 60], fill=hexc("#4a3018"))
    d.line([(2, 32), (69, 32)], fill=hexc("#3a2410"), width=2)
    d.rectangle([28, 28, 44, 38], fill=hexc("#b8a070"))
    return outline(speckle(im, 0.3, 181), "#1c1008")


def stub():
    """A short hexagonal basalt column stump (the foreground rocks of the painting)."""
    im, d = canvas(64, 96)
    d.polygon([(4, 94), (4, 26), (18, 8), (46, 8), (60, 26), (60, 94)], fill=hexc("#2a2230"))
    d.polygon([(18, 8), (46, 8), (60, 26), (4, 26)], fill=hexc("#4a3c54"))
    d.rectangle([4, 26, 16, 94], fill=hexc("#3a2e44"))
    d.rectangle([50, 26, 60, 94], fill=hexc("#120e16"))
    d.line([(12, 94), (14, 60), (12, 40)], fill=hexc("#ff7a1c"), width=1)
    return outline(speckle(im, 0.3, 191), "#0a060c")


def lavafall():
    """A lava fall down a dark cliff face: decal, emissive."""
    im, d = canvas(64, 256)
    rnd = random.Random(201)
    x = 32
    for y in range(0, 256, 2):
        x += rnd.choice((-1, 0, 0, 1))
        x = max(18, min(46, x))
        w = 7 + int(3 * math.sin(y / 11.0))
        d.rectangle([x - w, y, x + w, y + 2], fill=hexc(rnd.choice(["#ff9a20", "#ffb830", "#ff7a14"])))
        d.rectangle([x - w - 2, y, x - w, y + 2], fill=hexc("#c0360c"))
        d.rectangle([x + w, y, x + w + 2, y + 2], fill=hexc("#c0360c"))
    d.ellipse([6, 238, 58, 256], fill=hexc("#ffd860"))
    return im


# --- stage D round 1 (docs/briefs/DOOM_POLISH_BRIEF.md): the abyss, the far cliffs, the sky, the rim, the tunnel and the passage -------------------------------------------------

def wall_abyss():
    """The abyss's cliffs (the faces under the plateau, the ledge, the shelf and the tower, 5 m down to the lava): tall basalt prisms, a lit edge, a dark seam, dithered highlights, no
    horizontal seam (the old one tiled into a grid); a few glowing cracks climbing from below. The lava lamps light their feet orange, their tops stay dark (ABYSS_AMBIENT)."""
    rnd = random.Random(301)
    im = Image.new("RGB", (S, S), hexc("#0c080e"))
    d = ImageDraw.Draw(im)
    x = 0
    while x < S:
        w = rnd.choice((22, 28, 36))
        w = S - x if S - x < 24 else w
        k = 0.8 + rnd.random() * 0.45
        d.rectangle([x, 0, x + w - 1, S], fill=shade(hexc("#2a2030"), k))
        d.rectangle([x, 0, x + 1, S], fill=shade(hexc("#54445e"), k))
        for yy in range(S):  # a dithered lit band down the prism's left third
            for xx in range(x + 2, x + max(3, w // 3)):
                if BAYER4[yy % 4][xx % 4] < 6:
                    im.putpixel((xx % S, yy), shade(hexc("#3c3046"), k))
        d.rectangle([x + w - 2, 0, x + w - 1, S], fill=hexc("#08060a"))
        y = rnd.randrange(S)  # a facet break, short and slanted (not a full seam)
        d.line([(x + 2, y), (x + w - 3, y + rnd.randint(-3, 3))], fill=hexc("#140e18"))
        x += w
    veins(im, 302, "#ff7a1c", 0.35, vertical=True)
    return speckle(im, 0.18, 303)


def wall_far():
    """The far cliffs round the abyss (12 m above the lava, the sky over them): terraced basalt, darker and redder with the distance, ledges every so often with a glowing lip."""
    rnd = random.Random(311)
    im = Image.new("RGB", (S, S), hexc("#1a0e14"))
    d = ImageDraw.Draw(im)
    x = 0
    while x < S:
        w = rnd.choice((18, 24, 30))
        w = S - x if S - x < 20 else w
        k = 0.75 + rnd.random() * 0.5
        top = rnd.randrange(0, 40)
        d.rectangle([x, top, x + w - 1, S], fill=shade(hexc("#30202c"), k))
        d.rectangle([x, top, x + 1, S], fill=shade(hexc("#4e3646"), k))
        d.rectangle([x, top, x + w - 1, top + 1], fill=hexc("#ffa040") if rnd.random() < 0.7 else hexc("#5a3a48"))
        for yy in range(top + 2, min(S, top + 10)):  # the lava's light caught under each ledge lip, dithered out
            for xx in range(x + 2, x + w - 2):
                if BAYER4[yy % 4][xx % 4] < 10 - (yy - top):
                    im.putpixel((xx % S, yy), shade(hexc("#a04a2a"), 0.8 + 0.4 * rnd.random()))
        x += w
    veins(im, 312, "#ff8a24", 0.6, vertical=True)
    return speckle(im, 0.2, 313)


def wall_cliff_v2():
    """The cliff faces beside the paths (the plateau's sides, the shelf): basalt prisms as the abyss's, a little lighter, no grid seams."""
    im = columns("#2c2234", "#4a3a56", "#0e0a12", 7, widths=(28, 36, 44), glow=None)
    return veins(im, 8, "#ff6a14", 0.3, vertical=True)


def floor_lava_v2():
    """The lava seen from above: bright orange-yellow flow, dark crust rafts with glowing rims, braided flow lines (the painting's river)."""
    rnd = random.Random(91)
    im = Image.new("RGB", (S, S), hexc("#f06a1c"))
    d = ImageDraw.Draw(im)
    for _ in range(16):  # crust rafts with a glowing rim
        x, y = rnd.randrange(S), rnd.randrange(S)
        w, h = rnd.randint(10, 30), rnd.randint(6, 14)
        for ox in (-S, 0):
            for oy in (-S, 0):
                d.ellipse([x + ox, y + oy, x + ox + w, y + oy + h], fill=hexc("#ff9a30"))
                d.ellipse([x + ox + 2, y + oy + 2, x + ox + w - 2, y + oy + h - 2], fill=hexc(rnd.choice(["#4a1008", "#5a160a", "#3a0c06"])))
    for _ in range(40):  # braided bright flow lines
        x, y = rnd.randrange(S), rnd.randrange(S)
        for _k in range(rnd.randint(20, 50)):
            d.point((x % S, y % S), fill=hexc(rnd.choice(["#ffd040", "#ffb020", "#fff080"])))
            d.point(((x + 1) % S, y % S), fill=hexc("#ff9a20"))
            x += 1
            y += rnd.choice((-1, 0, 0, 1))
    px = im.load()
    for y in range(S):  # dithered glow pockets (no flat fill)
        for x in range(S):
            if BAYER4[y % 4][x % 4] < 2 and px[x, y][0] > 200:
                px[x, y] = shade(px[x, y], 1.15)
    return im


def sky_red():
    """The red cloud sky (512 x 128, the map's `sky`, horizon at row 97): banded crimson clouds, dithered, darker toward the zenith; near the horizon a far range of terraced cliffs in
    silhouette with lava falls and glowing ledges (the painting's far right)."""
    W, Hh, hz = 512, 128, 97
    rnd = random.Random(401)
    im = Image.new("RGB", (W, Hh), hexc("#2a0606"))
    px = im.load()
    for y in range(Hh):
        t = y / float(hz)
        base = (int(30 + 170 * t ** 1.4), int(6 + 70 * t ** 2.0), int(8 + 18 * t))  # near black at the zenith, the lava's glow on the cloud bottoms at the horizon (contrast, not a flat red)
        for x in range(W):
            n = math.sin(x * 0.045 + y * 0.31) + math.sin(x * 0.013 - y * 0.17 + 1.3) * 1.4 + math.sin(x * 0.11 + y * 0.07) * 0.5
            k = 0.78 + 0.16 * n + (BAYER4[y % 4][x % 4] - 7.5) / 60.0
            px[x, y] = shade(base, k)
    d = ImageDraw.Draw(im)
    x = 0
    while x < W:  # the far terraces
        w = rnd.randint(14, 40)
        top = rnd.randint(62, 90)
        d.rectangle([x, top, x + w, Hh], fill=hexc(rnd.choice(["#120806", "#160908", "#100605"])))  # (round 2: near black before the sky's lift, so the terraces read as rock, not flat purple)
        for yy in range(top + 1, Hh):  # the terrace's face: a lit left edge and a ledge every 9 rows with the lake's glow under it, dithered
            for xx in range(x, min(W, x + w)):
                k = (yy - top) % 9
                if (xx - x < 2) or (k == 0 and BAYER4[yy % 4][xx % 4] < 12) or (k in (1, 2) and BAYER4[yy % 4][xx % 4] < 5):
                    px[xx, yy] = hexc("#4a1a0e") if k else hexc("#702a12")
        d.rectangle([x, top, x + w, top], fill=hexc("#7a2a1a"))
        if rnd.random() < 0.3:  # a lava fall
            fx = x + rnd.randint(2, max(3, w - 4))
            for yy in range(top, Hh):
                d.point((fx, yy), fill=hexc(rnd.choice(["#ff8a20", "#ffb030"])))
                d.point((fx + 1, yy), fill=hexc("#c03a10"))
        x += w
    return im


def rail_stumps():
    """The rim of the abyss: a row of short basalt column stumps (the painting's rim stones), alpha 0 between them so the lava shows through; 128 px for 0.9 m along and up."""
    T = 128
    im = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(501)
    for x0, w, top in ((10, 18, 92), (78, 16, 100)):  # low stones (0.2 to 0.25 m of the 0.9 m strip): the lava shows over them
        body, lit, dark = hexc("#2a2230"), hexc("#54445e"), hexc("#0c080e")
        d.rectangle([x0, top + 8, x0 + w, T - 1], fill=(*body, 255))
        d.polygon([(x0, top + 8), (x0 + 6, top), (x0 + w - 6, top), (x0 + w, top + 8)], fill=(*hexc("#4a3c54"), 255))
        d.rectangle([x0, top + 8, x0 + 4, T - 1], fill=(*lit, 255))
        d.rectangle([x0 + w - 4, top + 8, x0 + w, T - 1], fill=(*dark, 255))
        for _ in range(3):
            y = rnd.randint(top + 12, T - 4)
            d.line([(x0 + 2, y), (x0 + w - 2, y + rnd.randint(-2, 2))], fill=(*dark, 255))
        cx = x0 + w // 2  # a glowing crack at the foot
        d.line([(cx, T - 1), (cx + rnd.randint(-3, 3), T - 14)], fill=(*hexc("#ff7a1c"), 255))
    return im


def tunnel():
    """The cave's far end: the blue tunnel running on (an emissive decal, 192 x 192): round-topped rock arches shrinking toward a lit bend, columns between them, a cobbled floor
    narrowing to the vanishing point, bone chimes hanging in the first arch."""
    im, d = canvas(192, 192)
    d.rectangle([0, 0, 191, 191], fill=hexc("#080a18"))
    cx, horizon = 96, 110
    for y in range(horizon, 192):  # the floor: cobbles in perspective, lighter toward the bend
        t = (y - horizon) / 82.0
        hw = int(10 + 86 * t)
        d.line([(cx - hw, y), (cx + hw, y)], fill=shade(hexc("#26305a"), 1.25 - 0.6 * t))
        if y % max(2, int(8 * t)) == 0:
            d.line([(cx - hw, y), (cx + hw, y)], fill=hexc("#10142c"))
    for k in range(6, -1, -1):  # arches, far first
        t = k / 6.0
        hw, top, bot = int(10 + 86 * (1 - t)), int(horizon - 20 - 90 * (1 - t)), int(horizon + 82 * (1 - t))
        col = shade(hexc("#3a4c9a"), 0.45 + 0.7 * t)
        wid = max(2, int(10 * (1 - t)))
        d.arc([cx - hw, top, cx + hw, top + 2 * hw], 180, 360, fill=col, width=wid)
        d.rectangle([cx - hw, top + hw, cx - hw + wid, bot], fill=col)
        d.rectangle([cx + hw - wid, top + hw, cx + hw, bot], fill=shade(col, 0.7))
    d.ellipse([84, 88, 108, 112], fill=hexc("#6a88f0"))
    d.ellipse([90, 94, 102, 106], fill=hexc("#d0e0ff"))
    for x in (30, 46, 146, 162):
        d.line([(x, 10), (x, 30 + (x % 13))], fill=hexc("#8a1818"))
        d.rounded_rectangle([x - 2, 30 + (x % 13), x + 2, 50 + (x % 13)], radius=2, fill=hexc("#e8dcc0"))
    return speckle(im, 0.2, 601)


def passage():
    """A lit path climbing the far east cliff (emissive decal, 128 x 256): a zigzag stair cut in the rock, a lantern at each turn, the Dock route's way on."""
    im, d = canvas(128, 256)
    pts = [(20, 250), (100, 210), (30, 160), (96, 110), (40, 60), (80, 20)]
    for a, b in zip(pts, pts[1:]):
        d.line([a, b], fill=hexc("#6a4a3a"), width=9)
        d.line([a, b], fill=hexc("#a07a5a"), width=3)
    for p in pts[1:]:
        d.rectangle([p[0] - 3, p[1] - 10, p[0] + 3, p[1] - 2], fill=hexc("#ffd070"))
        d.ellipse([p[0] - 8, p[1] - 14, p[0] + 8, p[1] + 2], outline=hexc("#ff9a40"))
    return im


# --- stage D round 2 (docs/briefs/DOOM_POLISH_ROUND2_BRIEF.md): near-black basalt, no texture lift, 2-3 variants per surface, a dark tunnel mouth ---------------------------------------

def basalt(seed, body="#54463e", lit="#a8887a", dark="#0c0808", widths=(22, 30, 38, 48, 60), crack="#ff6a14", cracks=0.25, T=256):
    """Near-black basalt prisms (the painting's rock, 256 px for 2 m): IRREGULAR column widths across the whole tile, each column broken into blocks of uneven height (a lit bevel on
    each block's top, a dark seam under it, the breaks staggered between columns so no row reads), a dithered cool lit face on the left third, a deep seam on the right, a few thin lava
    cracks climbing. The light on it comes from the lava lamps and the lanterns, not from the tile."""
    rnd = random.Random(seed)
    im = Image.new("RGB", (T, T), hexc(dark))
    px = im.load()
    d = ImageDraw.Draw(im)
    x = 0
    while x < T:
        w = rnd.choice(widths)
        if T - x < min(widths) + 10:
            w = T - x
        k0 = 0.7 + rnd.random() * 0.6
        y = -rnd.randrange(0, 90)
        while y < T:  # the blocks of this column
            h = rnd.randint(40, 150)
            k = k0 * (0.85 + rnd.random() * 0.3)
            y0, y1 = max(0, y), min(T, y + h)
            if y1 > y0:
                d.rectangle([x, y0, x + w - 1, y1 - 1], fill=shade(hexc(body), k))
                face = max(3, w // 3)
                for yy in range(y0, y1):  # the lit left face, dithered out to the right
                    for xx in range(x, x + face):
                        lim = 12 - int(12 * (xx - x) / face)
                        if BAYER4[yy % 4][xx % 4] < lim:
                            px[xx % T, yy] = shade(hexc(lit), k)
                for yy in range(y0, y1):  # the shadowed right face (round 2: deep, so the prisms keep their contrast at distance)
                    for xx in range(x + w - face, x + w - 3):
                        if BAYER4[yy % 4][xx % 4] < 10:
                            px[xx % T, yy] = shade(hexc(body), k * 0.22)
                if y >= 0:
                    d.rectangle([x, y0, x + w - 1, y0 + 1], fill=shade(hexc(lit), k * 1.25))  # the block's top bevel
                    d.rectangle([x, y0 + 2, x + w - 1, y0 + 2], fill=hexc(dark))
            y += h
        d.rectangle([x + w - 4, 0, x + w - 1, T], fill=hexc(dark))  # the seam between prisms
        x += w
    if cracks:
        for _ in range(int(T * cracks / 8)):
            cx, cy = rnd.randrange(T), rnd.randrange(T)
            for _k in range(rnd.randint(8, 26)):
                px[cx % T, cy % T] = shade(hexc(crack), 0.6 + rnd.random() * 0.6)
                cy += 1
                cx += rnd.choice((-1, 0, 0, 1))
    return speckle(im, 0.16, seed + 7)


def wall_rock_r2(v=0):
    return basalt(3 + 17 * v, widths=((26, 34, 44, 58), (20, 30, 40, 52), (30, 42, 50, 64))[v])


def wall_cliff_r2(v=0):
    return basalt(7 + 13 * v, body="#564640", lit="#967a6c", widths=(28, 36, 46, 56), cracks=0.3)


def wall_abyss_r2(v=0):
    """The cliffs into the lava (the void's mesh: the lava lamps light their feet orange): the same near-black prisms with more glowing cracks."""
    return basalt(301 + 11 * v, body="#504238", lit="#8e7262", widths=((22, 28, 36, 44), (26, 34, 40, 52), (20, 30, 42, 56))[v], crack="#ff7a1c", cracks=0.4)


def wall_step_r2():
    """The risers of the cut stairs: dark basalt slabs, a lit nosing at the top, no brick bond."""
    T = 256
    rnd = random.Random(33)
    im = Image.new("RGB", (T, T), hexc("#0a080c"))
    d = ImageDraw.Draw(im)
    for y in range(0, T, 64):
        x = -rnd.randrange(0, 60)
        while x < T:
            w = rnd.randint(50, 110)
            k = 0.8 + rnd.random() * 0.4
            d.rectangle([x + 2, y + 3, x + w - 2, y + 62], fill=shade(hexc("#4a3e3c"), k))
            d.rectangle([x + 2, y + 3, x + w - 2, y + 5], fill=shade(hexc("#6a5a58"), k))
            x += w
    return veins(speckle(im, 0.22, 34), 35, "#e0661a", 0.15)


def wall_far_r2():
    """The far cliffs over the lava (round 2): the basalt prisms of the near rock, terraced: a ledge every so often with a glowing lip and the lake's light dithered up under it,
    lava trickles in the seams (the painting's far terraces). Seen from 20 to 50 m: big shapes, strong lights."""
    T = 256
    im = basalt(311, body="#4e3c36", lit="#8a6a5c", widths=(30, 40, 52, 64), crack="#ff8a24", cracks=0.5)
    px = im.load()
    d = ImageDraw.Draw(im)
    rnd = random.Random(312)
    for y in (40, 118, 196):  # the terraces: a lit lip and the glow under it
        x = 0
        while x < T:
            w = rnd.randint(30, 80)
            yy = y + rnd.randint(-8, 8)
            d.rectangle([x, yy, x + w, yy + 2], fill=hexc("#ffa040"))
            for k in range(3, 16):
                for xx in range(x, min(T, x + w)):
                    if BAYER4[(yy + k) % 4][xx % 4] < 14 - k:
                        c = px[xx % T, (yy + k) % T]
                        px[xx % T, (yy + k) % T] = (min(255, c[0] + 60), min(255, c[1] + 22), c[2])
            x += w + rnd.randint(0, 20)
    return im


def floor_slab_r2():
    """The foreground: big flat basalt flagstones (near black, a cool top light dithered on each) with lava glowing in the cracks between them (the painting's foreground)."""
    rnd = random.Random(51)
    T = 128
    im = Image.new("RGB", (T, T), hexc("#120e14"))
    pts = [(rnd.randrange(T), rnd.randrange(T)) for _ in range(9)]
    px = im.load()
    for y in range(T):
        for x in range(T):
            best, second, bi = 1e9, 1e9, 0
            for i, (qx, qy) in enumerate(pts):
                dx, dy = min(abs(x - qx), T - abs(x - qx)), min(abs(y - qy), T - abs(y - qy))
                dd = dx * dx + dy * dy
                if dd < best:
                    second, best, bi = best, dd, i
                elif dd < second:
                    second = dd
            edge = math.sqrt(second) - math.sqrt(best)
            if edge < 2.2:
                px[x, y] = hexc("#ff7a1c") if edge < 1.0 and (x + y) % 3 else hexc("#4a1a0c")
            else:
                k = 0.8 + 0.25 * ((bi * 37) % 7) / 7.0
                c = hexc("#4a4042") if BAYER4[y % 4][x % 4] < 3 + (bi % 4) else hexc("#363032")
                px[x, y] = shade(c, k)
    return speckle(im, 0.25, 52)


def floor_stone_r2():
    """The paths' cut stone (round 2): warm grey slabs (the painting's paths), dark joints, a lit edge, a few lava veins; no lilac."""
    rnd = random.Random(63)
    im = Image.new("RGB", (S, S), hexc("#0e0a0a"))
    d = ImageDraw.Draw(im)
    for row, y in enumerate(range(0, S, 32)):
        x = -(0 if row % 2 == 0 else 32) - rnd.randrange(0, 12)
        while x < S:
            w = rnd.choice((52, 64, 76))
            k = 0.82 + rnd.random() * 0.36
            d.rectangle([x + 1, y + 1, x + w - 2, y + 30], fill=shade(hexc("#5a4c46"), k))
            d.rectangle([x + 1, y + 1, x + w - 2, y + 2], fill=shade(hexc("#8a7466"), k))
            x += w
    return veins(speckle(im, 0.3, 64), 65, "#e0661a", 0.12)


def wall_cave_r2():
    """The cave: the same basalt, the cool blue of its light caught on the lit faces (the painting's blue tunnel), darker than round 1's."""
    return basalt(11, body="#363e56", lit="#66749e", dark="#06070c", crack="#3a64ff", cracks=0.15)


def tunnel_r2():
    """The cave's far end (emissive decal, 192 x 192): a DARK tunnel mouth running on, one warm lantern hung inside, the path lit by a lava crack; the rock arches in near black (no blue
    stripes, no bright rings)."""
    im, d = canvas(176, 192)  # (2.5 m wide at 2.75 m: the whole end wall of the narrow passage)
    d.rectangle([0, 0, 175, 191], fill=hexc("#07060a"))
    cx, horizon = 88, 112
    px = im.load()
    for y in range(horizon, 192):  # the floor: dark slabs, brighter toward us
        t = (y - horizon) / 80.0
        hw = int(12 + 75 * t)
        for x in range(cx - hw, cx + hw + 1):
            px[x, y] = shade(hexc("#1c1416"), 0.6 + 0.6 * t) + (255,)
        if y % max(2, int(9 * t + 1)) == 0:
            d.line([(cx - hw, y), (cx + hw, y)], fill=hexc("#0a0608"))
    rnd = random.Random(611)
    x, y = cx + 4, 190
    while y > horizon + 2:  # one lava crack along the path, narrowing into the dark
        d.point((x, y), fill=hexc(rnd.choice(["#ff8a24", "#ffb030", "#d0501a"])))
        d.point((x + 1, y), fill=hexc("#8a2a10"))
        y -= 1
        if y % 3 == 0:
            x += rnd.choice((-1, 0, 0, 1))
        x = max(cx - 30, min(cx + 30, x))
    for k in range(6, -1, -1):  # rough rock arches in near black, faintly lit by the lantern
        t = k / 6.0
        hw, top = int(12 + 75 * (1 - t)), int(horizon - 22 - 88 * (1 - t))
        bot = int(horizon + 80 * (1 - t))
        col = shade(hexc("#2a222c"), 0.5 + 0.5 * (1 - abs(t - 0.35)))
        wid = max(2, int(9 * (1 - t)))
        d.arc([cx - hw, top, cx + hw, top + 2 * hw], 180, 360, fill=col, width=wid)
        d.rectangle([cx - hw, top + hw, cx - hw + wid, bot], fill=col)
        d.rectangle([cx + hw - wid, top + hw, cx + hw, bot], fill=shade(col, 0.6))
    lx, ly = cx - 18, 70  # the one lantern: a warm dithered pool round it
    for r in range(26, 0, -2):
        for yy in range(ly - r, ly + r):
            for xx in range(lx - r, lx + r):
                if 0 <= xx < 176 and 0 <= yy < 192 and (xx - lx) ** 2 + (yy - ly) ** 2 < r * r and BAYER4[yy % 4][xx % 4] < (26 - r) // 2:
                    c = px[xx, yy]
                    px[xx, yy] = (min(255, c[0] + 26), min(255, c[1] + 14), c[2], 255)
    d.line([(lx, 48), (lx, 60)], fill=hexc("#20202a"), width=1)
    d.rectangle([lx - 5, 60, lx + 5, 62], fill=hexc("#34343e"))
    d.rectangle([lx - 4, 62, lx + 4, 76], fill=hexc("#ffc060"))
    d.rectangle([lx - 2, 64, lx + 2, 74], fill=hexc("#fff0b0"))
    d.rectangle([lx - 5, 76, lx + 5, 78], fill=hexc("#34343e"))
    return speckle(im, 0.15, 612)


def floor_lava_r2():
    """The lava lake seen from above (round 2): a deep orange melt under dark crust rafts, braided bright flow lines between them (the painting's river), no flat yellow: the
    brightest pixels are the thin lines, the mass is orange-red."""
    rnd = random.Random(93)
    T = 128
    im = Image.new("RGB", (T, T), hexc("#c8461a"))
    px = im.load()
    for y in range(T):  # the melt: dithered between two oranges
        for x in range(T):
            n = math.sin(x * 0.19 + y * 0.07) + math.sin(y * 0.23 - x * 0.05)
            px[x, y] = hexc("#fa8c2c") if BAYER4[y % 4][x % 4] < 6 + 3 * n else hexc("#dc601e")
    d = ImageDraw.Draw(im)
    for _ in range(22):  # crust rafts with a glowing rim
        x, y = rnd.randrange(T), rnd.randrange(T)
        w, h = rnd.randint(10, 28), rnd.randint(5, 12)
        for ox in (-T, 0):
            for oy in (-T, 0):
                d.ellipse([x + ox, y + oy, x + ox + w, y + oy + h], fill=hexc("#ff8a2a"))
                d.ellipse([x + ox + 2, y + oy + 2, x + ox + w - 2, y + oy + h - 2], fill=hexc(rnd.choice(["#3a0e08", "#4a140a", "#2e0a06"])))
    for _ in range(26):  # braided flow lines, thin
        x, y = rnd.randrange(T), rnd.randrange(T)
        for _k in range(rnd.randint(20, 46)):
            px[x % T, y % T] = hexc(rnd.choice(["#ffd040", "#ffb020", "#ffe070"]))
            x += 1
            y += rnd.choice((-1, 0, 0, 1))
    return im


TEXTURES = {"uw_wall_rock": wall_rock_r2, "uw_wall_rock_b": lambda: wall_rock_r2(1), "uw_wall_rock_c": lambda: wall_rock_r2(2), "uw_wall_cliff": wall_cliff_r2,
            "uw_wall_cliff_b": lambda: wall_cliff_r2(1), "uw_wall_step": wall_step_r2, "uw_wall_cave": wall_cave_r2, "uw_wall_tower": wall_tower, "uw_floor_slab": floor_slab_r2,
            "uw_floor_stone": floor_stone_r2, "uw_floor_cave": floor_cave, "uw_floor_tower": floor_tower, "uw_floor_lava": floor_lava_r2, "uw_ceil": ceil_cloud, "uw_rail": rail_stumps,
            "uw_wall_abyss": wall_abyss_r2, "uw_wall_abyss_b": lambda: wall_abyss_r2(1), "uw_wall_abyss_c": lambda: wall_abyss_r2(2), "uw_wall_far": wall_far_r2, "uw_sky": sky_red}
PROPS = {"uw_pillar": pillar, "uw_tusks": tusks, "uw_gong": gong, "uw_drum": drum, "uw_cloth": cloth, "uw_tent": tent, "uw_lantern": lantern, "uw_crate": crate, "uw_stub": stub}
DECALS = {"uw_bones": bones, "uw_lavafall": lavafall, "uw_tunnel": tunnel_r2, "uw_passage": passage}


# round 1 lifted the basalt tiles (LIFT 1.6 to 1.7) to meet the exposure rule; round 2 takes that out (the brief: the basalt goes near black, the lava and the lamps carry the light). Only the
# sky keeps a lift (the painting's red sky reads brighter than the tile's dithered pixels).
WARM = (1.12, 1.0, 0.9)
LIFT = {"uw_sky": 2.8, "uw_wall_tower": 1.5, "uw_floor_tower": 1.5, "uw_pillar": 1.4}  # (the sky and the tower: the far side, lit by the lake)


def lifted(name, im):
    k = LIFT.get(name)
    if k is None:
        return im
    if name == "uw_sky":  # (round 2: the lift grows toward the horizon: the zenith stays near black, the cloud bottoms glow)
        out = im.convert("RGB")
        px = out.load()
        for y in range(out.height):
            f = 1.0 + (k - 1.0) * min(1.0, y / (out.height * 0.76)) ** 1.5
            for x in range(out.width):
                px[x, y] = tuple(min(255, int(v * f)) for v in px[x, y])
        return out
    if name in ("uw_pillar",):
        return im.point(lambda v: min(255, int(v * k))) if im.mode != "RGBA" else Image.merge("RGBA", [*[c.point(lambda v: min(255, int(v * k))) for c in im.split()[:3]], im.split()[3]])
    r, g, b = im.convert("RGB").split()
    return Image.merge("RGB", [ch.point(lambda v, f=k * w: min(255, int(v * f))) for ch, w in zip((r, g, b), WARM)])


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in {**TEXTURES, **PROPS, **DECALS}.items():
        lifted(name, fn()).save(os.path.join(OUT, name + ".png"))
    print("wrote %d textures, %d props and %d decals to %s" % (len(TEXTURES), len(PROPS), len(DECALS), OUT))


if __name__ == "__main__":
    sys.exit(main())
