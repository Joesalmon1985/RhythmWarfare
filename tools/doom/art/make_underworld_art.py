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
        d.rectangle([x, 0, x + 2, S], fill=shade(hexc(lit), shade_k))
        d.rectangle([x + w - 3, 0, x + w - 1, S], fill=hexc(dark))
        for _ in range(3):  # a facet seam across the prism
            y = rnd.randrange(S)
            d.line([(x, y), (x + w, y + rnd.randint(-4, 4))], fill=hexc(dark))
        x += w
    if glow:
        veins(im, seed + 1, glow, 0.8, vertical=True)
    return speckle(im, 0.22, seed + 2)


def wall_rock():
    return columns("#2a2230", "#4a3a52", "#100c14", 3, glow="#d65a14")


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
        d.line([(0, y), (S, y)], fill=hexc("#0e0a12"), width=2)
        d.line([(0, y + 2), (S, y + 2)], fill=hexc("#54445c"))
        for x in range(-off, S, 48):
            d.line([(x, y), (x, y + 32)], fill=hexc("#0e0a12"), width=2)
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


TEXTURES = {"uw_wall_rock": wall_rock, "uw_wall_cliff": wall_cliff, "uw_wall_step": wall_step, "uw_wall_cave": wall_cave, "uw_wall_tower": wall_tower, "uw_floor_slab": floor_slab,
            "uw_floor_stone": floor_stone, "uw_floor_cave": floor_cave, "uw_floor_tower": floor_tower, "uw_floor_lava": floor_lava, "uw_ceil": ceil_cloud, "uw_rail": rail_tile}
PROPS = {"uw_pillar": pillar, "uw_tusks": tusks, "uw_gong": gong, "uw_drum": drum, "uw_cloth": cloth, "uw_tent": tent, "uw_lantern": lantern, "uw_crate": crate, "uw_stub": stub}
DECALS = {"uw_bones": bones, "uw_lavafall": lavafall}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in {**TEXTURES, **PROPS, **DECALS}.items():
        fn().save(os.path.join(OUT, name + ".png"))
    print("wrote %d textures, %d props and %d decals to %s" % (len(TEXTURES), len(PROPS), len(DECALS), OUT))


if __name__ == "__main__":
    sys.exit(main())
