"""The Balcony's placeholder art (docs/doom/scenes/balcony.md): textures, props, decals and the three guides, written to assets/story/doom_balcony/textures/.

    python -I tools/doom/art/make_balcony_art.py        (the guides come from tools/doom/art/make_balcony_guides.py, called at the end)

PLACEHOLDER art, procedural (PIL, hashed noise), at 128 texels per metre for walls and floors, in the painting's palette (wet blue-grey concrete, red-brown brick, rusted iron rail,
magenta and cyan puddle reflections, an amber cabin, violet equalizer glow, a white lace dome). It is below the owner's standard (art/reference/standard/guide_floor_sprite_standard.png);
an art pass replaces the PNGs: names, sizes and frames per state are the data contract. Several props are the Booth's (`make_booth_art`), re-saved under this scene's names.
"""
from __future__ import annotations

import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_booth_art as mb  # noqa: E402

ROOT = mb.ROOT
OUT = os.path.join(ROOT, "assets", "story", "doom_balcony", "textures")
S = 128
hexc, shade, speckle, rust, canvas, outline = mb.hexc, mb.shade, mb.speckle, mb.rust, mb.canvas, mb.outline


def wall_brick():
    im = Image.new("RGB", (S, S), hexc("#4a2424"))
    d = ImageDraw.Draw(im)
    rnd = random.Random(101)
    for row, y in enumerate(range(0, S, 16)):  # brick courses, each brick its own shade
        off = 0 if row % 2 == 0 else 16
        for x in range(-off, S, 32):
            d.rectangle([x + 1, y + 1, x + 30, y + 14], fill=shade(hexc("#5a2c28"), 0.7 + rnd.random() * 0.6))
        d.line([(0, y), (S, y)], fill=hexc("#1c1010"))
        for x in range(-off, S, 32):
            d.line([(x, y), (x, y + 16)], fill=hexc("#1c1010"))
    for x in range(8, S, 24):  # wet streaks down the face
        d.line([(x, 0), (x + rnd.randint(-2, 2), S)], fill=hexc("#2a1818"), width=2)
    return speckle(im, 0.3, 102)


def wall_conc():
    im = Image.new("RGB", (S, S), hexc("#2c3140"))
    d = ImageDraw.Draw(im)
    rnd = random.Random(111)
    d.rectangle([0, 0, S, 2], fill=hexc("#4a5064"))  # a panel seam top and bottom
    d.rectangle([0, S - 3, S, S], fill=hexc("#181c28"))
    for k in range(14):  # vertical rain stains
        x = rnd.randint(0, S)
        d.line([(x, rnd.randint(0, 30)), (x + rnd.randint(-3, 3), rnd.randint(70, S))], fill=shade(hexc("#1c2030"), 0.8 + rnd.random() * 0.5), width=rnd.randint(1, 4))
    for y in (24, 72, 112):
        for x in range(10, S, 40):
            d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=hexc("#5a6078"))  # form-tie holes
    return rust(speckle(im, 0.28, 112), 113, 0.12, (96, 56, 36))


def wall_steel():
    im = Image.new("RGB", (S, S), hexc("#383c4a"))
    d = ImageDraw.Draw(im)
    for x in range(0, S, 32):  # corrugated sheet
        for k in range(32):
            t = abs(k - 16) / 16.0
            d.line([(x + k, 0), (x + k, S)], fill=shade(hexc("#4a5064"), 0.65 + 0.5 * (1 - t)))
    d.rectangle([0, 0, S, 3], fill=hexc("#5a6078"))
    return rust(speckle(im, 0.25, 121), 122, 0.4)


def wall_cabin():
    im = Image.new("RGB", (S, S), hexc("#4a3426"))
    d = ImageDraw.Draw(im)
    for y in range(0, S, 32):
        d.rectangle([0, y, S, y + 2], fill=hexc("#241810"))
    for x in range(0, S, 64):
        d.rectangle([x, 0, x + 1, S], fill=hexc("#241810"))
    return rust(speckle(im, 0.28, 131), 132, 0.2)


def floor_wet():
    """The deck: diamond plate under rain, with magenta, cyan and red puddle reflections."""
    im = Image.new("RGB", (S, S), hexc("#222836"))
    d = ImageDraw.Draw(im)
    for gy in range(0, S, 16):
        for gx in range(0, S, 16):
            a = ((gx + gy) // 16) % 2
            d.line([(gx + 3, gy + (12 if a else 3)), (gx + 12, gy + (3 if a else 12))], fill=hexc("#4a5268"), width=2)
    rnd = random.Random(141)
    for col, n in (("#a02a6a", 3), ("#2a8ab8", 3), ("#b02a2a", 2)):  # reflections: the puddle is a flat ellipse, brighter than the plate
        for _ in range(n):
            x, y = rnd.randint(8, S - 40), rnd.randint(8, S - 24)
            w, h = rnd.randint(20, 40), rnd.randint(8, 16)
            d.ellipse([x, y, x + w, y + h], fill=shade(hexc(col), 0.55))
            d.ellipse([x + 3, y + 2, x + w - 6, y + h - 3], fill=shade(hexc(col), 0.85))
            d.ellipse([x + w // 2 - 6, y + h // 2 - 2, x + w // 2 + 6, y + h // 2 + 2], outline=hexc("#c8d0e8"))  # a raindrop ring
    return speckle(im, 0.22, 142)


def floor_stair():
    im = Image.new("RGB", (S, S), hexc("#2a2430"))
    d = ImageDraw.Draw(im)
    for gy in range(0, S, 16):
        for gx in range(0, S, 16):
            a = ((gx + gy) // 16) % 2
            d.line([(gx + 3, gy + (12 if a else 3)), (gx + 12, gy + (3 if a else 12))], fill=hexc("#8a5a40"), width=2)
    d.rectangle([0, 0, S, 6], fill=hexc("#a06a48"))  # the tread's lit nosing
    return rust(speckle(im, 0.3, 151), 152, 0.25)


def floor_conc():
    im = Image.new("RGB", (S, S), hexc("#262a36"))
    d = ImageDraw.Draw(im)
    d.polygon([(0, 70), (S, 20), (S, 34), (0, 84)], fill=hexc("#7a6218"))  # a yard marking
    for y in range(0, S, 8):
        d.line([(0, y + (y // 8) % 3), (S, y + (y // 8) % 3)], fill=hexc("#303644"))
    return speckle(im, 0.4, 161)


def floor_grate():
    im = Image.new("RGB", (S, S), hexc("#10121a"))
    d = ImageDraw.Draw(im)
    for k in range(0, S, 8):
        d.line([(k, 0), (k, S)], fill=hexc("#6a4a38"))
        d.line([(0, k), (S, k)], fill=hexc("#3a2c26"))
    return speckle(im, 0.3, 171)


def floor_cabin():
    im = Image.new("RGB", (S, S), hexc("#2e2018"))
    d = ImageDraw.Draw(im)
    for x in range(0, S, 32):
        d.rectangle([x, 0, x + 1, S], fill=hexc("#160e0a"))
    return speckle(im, 0.3, 181)


def ceil_storm():
    """The night sky as a ceiling: dark blue cloud with lighter drifts (tiles)."""
    im = Image.new("RGB", (S, S), hexc("#0c1220"))
    d = ImageDraw.Draw(im)
    rnd = random.Random(191)
    for _ in range(26):
        x, y = rnd.randint(-20, S), rnd.randint(0, S)
        w, h = rnd.randint(30, 80), rnd.randint(8, 22)
        for dx in (-S, 0, S):
            d.ellipse([x + dx, y, x + dx + w, y + h], fill=shade(hexc("#18223a"), 0.8 + rnd.random() * 0.6))
    return speckle(im, 0.2, 192)


def rail_tile():
    """The roof railing: a rusty iron handrail, a mid bar, balusters every 16 texels and a thick post at the tile's edge; alpha 0 elsewhere (the drop and the city show through)."""
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    iron, light, dark = hexc("#6a3e2c"), hexc("#b07a58"), hexc("#241410")
    d.rectangle([0, 4, S, 12], fill=(*iron, 255))
    d.rectangle([0, 4, S, 5], fill=(*light, 255))  # wet highlight on the handrail
    d.rectangle([0, 11, S, 12], fill=(*dark, 255))
    d.rectangle([0, 60, S, 64], fill=(*iron, 255))
    d.rectangle([0, 60, S, 61], fill=(*light, 255))
    for x in range(20, S, 16):
        d.rectangle([x, 12, x + 2, S], fill=(*iron, 255))
    d.rectangle([0, 4, 9, S], fill=(*iron, 255))  # the post
    d.rectangle([0, 4, 2, S], fill=(*light, 255))
    d.rectangle([0, 112, S, S], fill=(*dark, 255))
    return im


def tower():
    """A far building rising out of the dark drop: a dark mass with lit windows, a lit sign and red aircraft lamps (a billboard)."""
    W, H = 128, 256
    im, d = canvas(W, H)
    rnd = random.Random(201)
    d.rectangle([8, 24, 120, 255], fill=hexc("#1c2230"))
    d.rectangle([8, 24, 120, 30], fill=hexc("#2e3650"))
    d.rectangle([36, 4, 92, 24], fill=hexc("#181e2c"))
    for wy in range(40, 250, 12):
        for wx in range(14, 114, 10):
            if rnd.random() < 0.34:
                d.rectangle([wx, wy, wx + 5, wy + 6], fill=hexc(rnd.choice(["#ffb050", "#ff9a40", "#ffd080", "#8a6aa8"])))
    for k in range(7):  # an equalizer sign
        d.rectangle([22 + k * 6, 150 - rnd.randint(8, 40), 25 + k * 6, 150], fill=hexc("#d03a9a"))
    for x, y in ((44, 2), (84, 2), (12, 22), (112, 22)):
        d.rectangle([x, y, x + 3, y + 3], fill=hexc("#ff2a20"))
    return outline(speckle(im, 0.2, 202), "#080a12")


def dish():
    im, d = canvas(96, 128)
    d.rectangle([44, 70, 52, 127], fill=hexc("#2a2e3a"))  # pole
    d.ellipse([14, 6, 78, 76], fill=hexc("#3e4658"), outline=hexc("#6a7288"), width=3)  # the dish
    d.ellipse([28, 20, 66, 62], fill=hexc("#2a3040"))
    d.line([(46, 40), (84, 14)], fill=hexc("#8a90a8"), width=3)  # the feed arm
    d.rectangle([80, 10, 88, 18], fill=hexc("#a0a6b8"))
    d.rectangle([36, 118, 62, 127], fill=hexc("#2a2e3a"))
    return outline(speckle(im, 0.25, 211), "#080a12")


def forklift():
    im, d = canvas(112, 96)
    d.rectangle([30, 36, 90, 80], fill=hexc("#b08a18"))  # body
    d.rectangle([34, 20, 80, 40], fill=hexc("#7a5a10"))  # cab
    d.rectangle([40, 24, 74, 36], fill=hexc("#2a3a58"))
    d.rectangle([14, 8, 22, 84], fill=hexc("#3a3e4a"))  # the mast
    d.rectangle([4, 74, 28, 80], fill=hexc("#3a3e4a"))  # the forks
    for cx in (44, 80):
        d.ellipse([cx - 11, 70, cx + 11, 92], fill=hexc("#14161c"))
    return outline(speckle(im, 0.3, 221), "#080a12")


def eq_graffiti(col_a, col_b, seed, w=96, h=128):
    """A spray-painted equalizer (the painting's pink bars on the brick): bars of two colours with a wave over them."""
    im, d = canvas(w, h)
    rnd = random.Random(seed)
    x = 4
    while x < w - 8:
        bh = rnd.randint(18, h - 20)
        d.rectangle([x, h - bh, x + 8, h - 6], fill=hexc(col_a))
        d.rectangle([x + 2, h - bh, x + 3, h - 6], fill=hexc(col_b))
        x += 12
    pts = [(i, int(h * 0.4 + math.sin(i * 0.12 + seed) * 14)) for i in range(0, w, 3)]
    d.line(pts, fill=hexc(col_b), width=3)
    return im


def window_glow():
    """The cabin's big window seen from the deck: a dark steel frame in four panes with violet and magenta equalizer light inside; emissive."""
    W, H = 160, 128
    im, d = canvas(W, H)
    d.rectangle([0, 0, W - 1, H - 1], fill=hexc("#10121a"))
    rnd = random.Random(231)
    for pane in range(4):
        x0 = 6 + pane * 38
        d.rectangle([x0, 6, x0 + 32, H - 8], fill=hexc("#1a1230"))
        for k in range(5):
            bh = rnd.randint(10, 60)
            d.rectangle([x0 + 2 + k * 6, H - 10 - bh, x0 + 6 + k * 6, H - 10], fill=hexc(rnd.choice(["#a050ff", "#d03aa0", "#6a3ae0"])))
    d.line([(6, 52), (W - 6, 52)], fill=hexc("#383c4a"), width=3)  # the mullion
    return im


def lace_dome():
    """The white lace lattice dome of the tower the bridge ends at (a decal on the platform's far wall)."""
    W, H = 192, 128
    im, d = canvas(W, H)
    d.rectangle([0, 0, W - 1, H - 1], fill=hexc("#1c2030"))
    d.pieslice([10, 10, W - 10, 2 * H - 20], 180, 360, fill=hexc("#0c1020"))
    for r in range(30, 90, 16):
        d.arc([W // 2 - r * 1.4, H - 10 - r, W // 2 + r * 1.4, H - 10 + r], 180, 360, fill=hexc("#e8e4f4"), width=3)
    for k in range(-4, 5):
        d.line([(W // 2 + k * 6, H - 10), (W // 2 + k * 20, 14)], fill=hexc("#d8d4ec"), width=2)
    for k in range(0, 10):  # fairy lights along the foot
        d.ellipse([14 + k * 18, H - 18, 18 + k * 18, H - 14], fill=hexc("#ffd890"))
    return im


def shutters_blue():
    """Two roller shutters lit from above by a cold blue lamp (the painting's yard at the foot of the drop); emissive."""
    W, H = 192, 128
    im, d = canvas(W, H)
    d.rectangle([0, 0, W - 1, H - 1], fill=hexc("#10162a"))
    for x0 in (10, 100):
        d.rectangle([x0, 20, x0 + 80, H - 1], fill=hexc("#2a3450"))
        for y in range(24, H, 8):
            d.rectangle([x0 + 2, y, x0 + 78, y + 5], fill=shade(hexc("#3a4a70"), 1.0 - (y - 24) / 220))
        d.polygon([(x0 + 20, 14), (x0 + 60, 14), (x0 + 80, 40), (x0, 40)], fill=hexc("#2a5a9a"))  # the cold lamp's cone
        d.rectangle([x0 + 28, 8, x0 + 52, 16], fill=hexc("#9ad0ff"))
    return im


def windows_lit():
    W, H = 128, 192
    im, d = canvas(W, H)
    rnd = random.Random(241)
    d.rectangle([0, 0, W - 1, H - 1], fill=hexc("#161c2c"))
    for wy in range(8, H - 8, 14):
        for wx in range(6, W - 10, 12):
            if rnd.random() < 0.4:
                d.rectangle([wx, wy, wx + 7, wy + 8], fill=hexc(rnd.choice(["#ffb050", "#ffd080", "#c07aff", "#ff8a40"])))
    return im


TEXTURES = {"bc_wall_brick": wall_brick, "bc_wall_conc": wall_conc, "bc_wall_steel": wall_steel, "bc_wall_cabin": wall_cabin, "bc_floor_wet": floor_wet, "bc_floor_stair": floor_stair,
            "bc_floor_conc": floor_conc, "bc_floor_grate": floor_grate, "bc_floor_cabin": floor_cabin, "bc_ceil": ceil_storm, "bc_trim": mb.trim, "bc_rail": rail_tile}
PROPS = {"bc_case": mb.case, "bc_cables": mb.cables, "bc_cage_lamp": mb.cage_lamp, "bc_rack": mb.rack, "bc_tower": tower, "bc_dish": dish, "bc_forklift": forklift}
DECALS = {"bc_eq_pink": lambda: eq_graffiti("#d03a9a", "#ff9ad8", 3), "bc_eq_violet": lambda: eq_graffiti("#7a4ae0", "#c0a0ff", 5, 96, 96), "bc_window_glow": window_glow,
          "bc_skyline": mb.skyline, "bc_lace": lace_dome, "bc_pipes": mb.pipe_run, "bc_shutters": shutters_blue, "bc_led": mb.led_strip, "bc_windows": windows_lit}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in {**TEXTURES, **PROPS, **DECALS}.items():
        fn().save(os.path.join(OUT, name + ".png"))
    import make_balcony_guides as bg
    n = bg.main()
    print("wrote %d textures, %d props, %d decals and %d guide frames to %s" % (len(TEXTURES), len(PROPS), len(DECALS), n, OUT))


if __name__ == "__main__":
    sys.exit(main())
