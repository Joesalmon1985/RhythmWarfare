"""The Mothership's placeholder art (docs/doom/scenes/mothership.md): textures, props, decals, written to assets/story/doom_mothership/textures/; the three guides are
tools/doom/art/make_mothership_guides.py.

    python -I tools/doom/art/make_mothership_art.py

PLACEHOLDER art, procedural (PIL, hashed noise, the Booth's helpers), 128 texels per metre for walls and floors, in the painting's palette: pale lilac bone ribs with dark oval cut-outs,
violet shadow, mint-green glow from the pool far below, amber lamps in the wall, brass. It is below the owner's standard (art/reference/standard/guide_floor_sprite_standard.png); an art pass
replaces the PNGs: the file names, sizes and frames per state are the data contract.
"""
from __future__ import annotations

import math
import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_booth_art as mb  # noqa: E402  (hexc, shade, speckle, canvas, outline)

ROOT = mb.ROOT
OUT = os.path.join(ROOT, "assets", "story", "doom_mothership", "textures")
S = 128
hexc, shade, speckle, canvas, outline = mb.hexc, mb.shade, mb.speckle, mb.canvas, mb.outline


def wall_rib():
    """Pale lilac bone: a tile with two dark oval cut-outs and a lit ridge round each (the painting's organic ribs)."""
    im = Image.new("RGB", (S, S), hexc("#8a7aa8"))
    d = ImageDraw.Draw(im)
    for x in range(0, S, 4):  # fine vertical grain, the mosaic of the painting
        d.line([(x, 0), (x, S)], fill=shade(hexc("#8a7aa8"), 0.9 + 0.2 * ((x // 4) % 3) / 2))
    for cx, cy, rx, ry in ((32, 44, 20, 30), (96, 84, 20, 30)):
        d.ellipse([cx - rx - 4, cy - ry - 4, cx + rx + 4, cy + ry + 4], fill=hexc("#c8b8e0"))
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=hexc("#22143a"))
        d.ellipse([cx - rx + 4, cy - ry + 8, cx + rx - 4, cy + ry - 4], fill=hexc("#34205a"))
    d.rectangle([0, 0, S, 3], fill=hexc("#b8a8d4"))
    return speckle(im, 0.25, 111)


def wall_dark():
    im = Image.new("RGB", (S, S), hexc("#3a2a58"))
    d = ImageDraw.Draw(im)
    for y in range(0, S, 32):
        d.rectangle([0, y, S, y + 1], fill=hexc("#20143a"))
        for x in range((y // 32) % 2 * 16, S, 32):
            d.rectangle([x, y, x + 1, y + 32], fill=hexc("#20143a"))
    d.rectangle([0, 56, S, 62], fill=hexc("#5a4480"))
    return speckle(im, 0.3, 112)


def floor_walk():
    """Grey-lilac flagstones with big shallow ovals set in them and a dark slotted drain line (the painting's walkway)."""
    im = Image.new("RGB", (S, S), hexc("#7a6c90"))
    d = ImageDraw.Draw(im)
    for k in range(0, S, 4):
        d.line([(0, k), (S, k)], fill=shade(hexc("#7a6c90"), 0.92 + 0.1 * ((k // 4) % 2)))
    d.ellipse([6, 14, 70, 60], fill=hexc("#5a4c74"), outline=hexc("#a898c4"))
    d.ellipse([60, 74, 124, 118], fill=hexc("#5a4c74"), outline=hexc("#a898c4"))
    d.rectangle([0, S - 14, S, S - 8], fill=hexc("#1c1428"))
    for x in range(2, S, 10):
        d.rectangle([x, S - 13, x + 6, S - 9], fill=hexc("#0a0612"))
    return speckle(im, 0.25, 113)


def floor_void():
    """The pool far below: dark green with mint swirl rings."""
    im = Image.new("RGB", (S, S), hexc("#0c3a28"))
    d = ImageDraw.Draw(im)
    rnd = random.Random(114)
    for _ in range(14):
        x, y, r = rnd.randrange(S), rnd.randrange(S), rnd.randint(8, 30)
        for off in (-S, 0, S):
            d.ellipse([x - r + off, y - r // 2, x + r + off, y + r // 2], outline=shade(hexc("#58f0a8"), 0.5 + rnd.random() * 0.6))
    return speckle(im, 0.4, 115)


def floor_plate():
    im = Image.new("RGB", (S, S), hexc("#4a3c5e"))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, S - 1, S - 1], outline=hexc("#8a78a8"), width=2)
    d.ellipse([20, 20, 108, 108], outline=hexc("#c8a860"), width=2)
    d.ellipse([34, 34, 94, 94], outline=hexc("#8a78a8"))
    for a in range(0, 360, 45):
        d.line([(64, 64), (64 + 44 * math.cos(math.radians(a)), 64 + 44 * math.sin(math.radians(a)))], fill=hexc("#6a5a84"))
    return speckle(im, 0.3, 116)


def ceil_arch():
    im = Image.new("RGB", (S, S), hexc("#2a1c44"))
    d = ImageDraw.Draw(im)
    for k in (0, 64):
        d.rectangle([k, 0, k + 3, S], fill=hexc("#5a4684"))
        d.rectangle([0, k, S, k + 3], fill=hexc("#1c1030"))
    d.ellipse([12, 12, 52, 52], outline=hexc("#6a5694"))
    d.ellipse([76, 76, 116, 116], outline=hexc("#6a5694"))
    return speckle(im, 0.3, 117)


def trim():
    im = Image.new("RGB", (S, S), hexc("#7a6a98"))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, S, 8], fill=hexc("#b8a8d4"))
    d.rectangle([0, 56, S, 60], fill=hexc("#2a1c44"))
    return speckle(im, 0.3, 118)


def rail_tile():
    """The balustrade round the void: a pale lilac stone rail with a top coping and an oval opening (the painting's), alpha 0 in the opening so the abyss shows through; a post at the left edge."""
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    stone, light, dark = hexc("#6a5c84"), hexc("#9a8cb8"), hexc("#2c2244")
    d.rectangle([0, 0, S, 22], fill=(*stone, 255))  # the coping
    d.rectangle([0, 0, S, 5], fill=(*light, 255))
    d.rectangle([0, 18, S, 22], fill=(*dark, 255))
    d.rectangle([0, 22, S, S], fill=(*stone, 255))  # the panel with a big oval opening
    d.rectangle([0, 22, 8, S], fill=(*light, 255))
    d.rectangle([S - 4, 22, S, S], fill=(*dark, 255))
    d.ellipse([22, 36, 104, 108], fill=(0, 0, 0, 0))
    d.arc([22, 36, 104, 108], 0, 360, fill=(*dark, 255), width=3)
    d.rectangle([0, S - 14, S, S], fill=(*dark, 255))  # the foot
    d.rectangle([0, S - 14, S, S - 12], fill=(*stone, 255))
    return im


# --- props and decals ---------------------------------------------------------------------------------------------------------------------------------------

def crystal():
    im, d = canvas(96, 128)
    for x, w, h, c in ((10, 14, 70, "#80e0c0"), (28, 18, 110, "#b8f0d8"), (50, 14, 90, "#70d0b0"), (66, 12, 58, "#a0e8d0")):
        d.polygon([(x, 124), (x + w, 124), (x + w * 0.7, 124 - h), (x + w * 0.3, 124 - h - 10)], fill=hexc(c))
        d.line([(x + w * 0.4, 124), (x + w * 0.45, 124 - h)], fill=hexc("#f0fff8"), width=2)
    return outline(im)


def console():
    im, d = canvas(128, 72)
    d.polygon([(0, 70), (10, 22), (118, 22), (128, 70)], fill=hexc("#5a4478"))
    d.polygon([(10, 22), (118, 22), (122, 34), (6, 34)], fill=hexc("#7a62a0"))
    for k in range(10):
        d.rectangle([18 + k * 10, 38, 23 + k * 10, 44], fill=hexc("#8fe0c0") if k % 3 else hexc("#ffb0d0"))
    d.rectangle([40, 8, 88, 24], fill=hexc("#1a1230"))
    d.rectangle([44, 11, 84, 21], fill=hexc("#58f0a8"))
    return outline(speckle(im, 0.2, 119))


def orb():
    """The hanging cable sphere with glowing green cells (top left of the painting)."""
    im, d = canvas(192, 192)
    d.ellipse([8, 8, 184, 184], fill=hexc("#2a1c34"), outline=hexc("#0e0814"))
    rnd = random.Random(120)
    for k in range(22):
        a = rnd.random() * 6.28
        r = rnd.random() * 60
        x, y = 96 + r * math.cos(a), 96 + r * math.sin(a)
        rr = rnd.randint(8, 16)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=hexc("#58f0a8"), outline=hexc("#183a2a"), width=3)
    for k in range(0, 192, 12):
        d.arc([8 + k // 3, 8, 184 - k // 3, 184], 90, 270, fill=hexc("#4a3a54"), width=3)
    return outline(im)


def cables_hang():
    im, d = canvas(96, 192)
    rnd = random.Random(121)
    for k in range(5):
        x = 16 + k * 16 + rnd.randint(-4, 4)
        for y in range(0, 192, 8):
            x2 = x + int(math.sin(y * 0.05 + k) * 8)
            d.rectangle([x2, y, x2 + 8, y + 9], fill=hexc("#3a2a30"), outline=hexc("#140c10"))
    return im


def armillary():
    """The brass armillary sphere on a carved plinth (the pedestal in the painting's pool)."""
    im, d = canvas(96, 128)
    d.polygon([(8, 120), (88, 120), (80, 64), (16, 64)], fill=hexc("#3a3a30"), outline=hexc("#12120c"))
    d.rectangle([14, 64, 82, 72], fill=hexc("#58584a"))
    d.ellipse([20, 8, 76, 64], outline=hexc("#c89a30"), width=4)
    d.ellipse([34, 8, 62, 64], outline=hexc("#c89a30"), width=3)
    d.arc([20, 24, 76, 48], 0, 360, fill=hexc("#e8c860"), width=3)
    d.line([(48, 2), (48, 70)], fill=hexc("#8a6a20"), width=3)
    d.rectangle([40, 90, 56, 96], fill=hexc("#ffb040"))
    return outline(speckle(im, 0.2, 122))


def dj_rig():
    """The DJ's rig: a deck table with turntables and a mixer, amber lit."""
    im, d = canvas(160, 96)
    d.polygon([(4, 30), (156, 30), (160, 92), (0, 92)], fill=hexc("#4a3a56"))
    d.polygon([(4, 30), (156, 30), (158, 42), (2, 42)], fill=hexc("#6a5a78"))
    for x in (14, 100):
        d.ellipse([x, 34, x + 46, 56], fill=hexc("#101010"))
        d.ellipse([x + 15, 41, x + 31, 49], fill=hexc("#c22030"))
    d.rectangle([62, 34, 94, 60], fill=hexc("#201a2c"))
    for k in range(6):
        d.rectangle([66 + k * 5, 38, 67 + k * 5, 56], fill=hexc("#ffb040"))
    for x in range(8, 150, 14):
        d.rectangle([x, 70, x + 8, 84], fill=hexc("#2a2036"))
    return outline(speckle(im, 0.2, 123))


def speaker():
    im, d = canvas(80, 100)
    d.rectangle([2, 2, 77, 97], fill=hexc("#2a2434"))
    d.ellipse([14, 12, 66, 56], fill=hexc("#14101c"), outline=hexc("#6a5a7a"), width=3)
    d.ellipse([28, 26, 52, 42], fill=hexc("#4a3a5a"))
    d.ellipse([22, 62, 58, 88], fill=hexc("#14101c"), outline=hexc("#6a5a7a"), width=2)
    return outline(speckle(im, 0.2, 124))


def organ():
    """Golden organ pipes of different lengths (the left edge of the painting)."""
    im, d = canvas(112, 192)
    rnd = random.Random(125)
    for k in range(9):
        x = 4 + k * 11
        h = 60 + rnd.randint(0, 120)
        d.rectangle([x, 190 - h, x + 8, 190], fill=hexc("#d8a838"))
        d.rectangle([x, 190 - h, x + 2, 190], fill=hexc("#f8e090"))
        d.rectangle([x + 6, 190 - h, x + 8, 190], fill=hexc("#8a6a20"))
        d.ellipse([x + 1, 190 - h - 2, x + 7, 190 - h + 4], fill=hexc("#101010"))
    return outline(im)


def hatch_arch():
    """A round hatch with a bright rim and a warm mouth, behind the Booth guide."""
    im, d = canvas(128, 160)
    d.rounded_rectangle([4, 4, 123, 159], radius=56, fill=hexc("#b8a8d4"))
    d.rounded_rectangle([14, 14, 113, 159], radius=48, fill=hexc("#1c1030"))
    d.rounded_rectangle([22, 24, 105, 159], radius=42, fill=hexc("#ffc880"))
    d.rounded_rectangle([30, 34, 97, 159], radius=36, fill=hexc("#ffe0a8"))
    return outline(im)


def case():
    im, d = canvas(72, 64)
    d.rectangle([2, 8, 69, 60], fill=hexc("#34304a"))
    d.rectangle([2, 8, 69, 18], fill=hexc("#54506a"))
    for x, y in ((2, 8), (62, 8), (2, 52), (62, 52)):
        d.rectangle([x, y, x + 7, y + 7], fill=hexc("#a8a0c0"))
    d.rectangle([30, 34, 42, 40], fill=hexc("#a8a0c0"))
    return outline(speckle(im, 0.3, 126))


def lamp_post():
    im, d = canvas(48, 112)
    d.rectangle([21, 24, 26, 108], fill=hexc("#3a3040"))
    d.ellipse([10, 100, 38, 110], fill=hexc("#3a3040"))
    d.rounded_rectangle([12, 4, 36, 36], radius=6, fill=hexc("#ffc060"), outline=hexc("#3a3040"), width=3)
    d.ellipse([18, 12, 30, 28], fill=hexc("#fff0b8"))
    return outline(im)


def brazier():
    im, d = canvas(64, 80)
    d.polygon([(8, 78), (56, 78), (48, 40), (16, 40)], fill=hexc("#3a2a20"))
    d.ellipse([8, 32, 56, 48], fill=hexc("#1a1010"))
    d.polygon([(20, 40), (32, 4), (44, 40)], fill=hexc("#ff5a30"))
    d.polygon([(26, 40), (32, 16), (38, 40)], fill=hexc("#ffc060"))
    return outline(im)


def pillar():
    """A branching pale pillar rising from the abyss: a trunk with two ribs forking at the top, mint glow at its foot (alpha 0 around)."""
    W, H = 96, 256
    im, d = canvas(W, H)
    pale, light, dark = hexc("#b8a8d0"), hexc("#e0d4f4"), hexc("#5a4a78")
    d.polygon([(34, H), (62, H), (56, 90), (40, 90)], fill=pale)
    d.polygon([(40, 96), (56, 96), (80, 8), (64, 4)], fill=pale)
    d.polygon([(40, 96), (56, 96), (16, 8), (32, 4)], fill=pale)
    d.line([(38, H), (42, 90), (24, 8)], fill=light, width=2)
    d.line([(58, H), (54, 90), (72, 8)], fill=dark, width=2)
    d.ellipse([34, H - 22, 62, H], fill=hexc("#80f0b8"))
    return outline(speckle(im, 0.25, 127))


def oval_window():
    """An oval opening in the wall onto dark violet, rimmed in light, with a faint green glow from below."""
    im, d = canvas(96, 128)
    d.ellipse([2, 2, 93, 125], fill=hexc("#d8ccf0"))
    d.ellipse([8, 8, 87, 119], fill=hexc("#140a28"))
    d.ellipse([14, 40, 81, 113], fill=hexc("#1e3a38"))
    d.ellipse([26, 66, 69, 110], fill=hexc("#2a6a50"))
    return im


def wall_lamp():
    im, d = canvas(24, 48)
    d.rounded_rectangle([2, 2, 21, 45], radius=5, fill=hexc("#ffb040"), outline=hexc("#6a3a10"), width=2)
    d.rectangle([8, 8, 15, 39], fill=hexc("#fff0b8"))
    return im


def hatch_dock():
    """The dock hatch's far door: a steel shutter with amber light along its lintel."""
    im, d = canvas(128, 144)
    d.rounded_rectangle([0, 0, 127, 143], radius=10, fill=hexc("#3a3040"))
    d.rounded_rectangle([8, 8, 119, 143], radius=8, fill=hexc("#201a2c"))
    for y in range(16, 140, 10):
        d.rectangle([14, y, 113, y + 6], fill=hexc("#34304a"))
    d.rectangle([0, 0, 127, 6], fill=hexc("#ffb040"))
    return im


def hatch_uw():
    """The Underworld hatch: a dark arch with a red glow and a ring of runes."""
    im, d = canvas(128, 160)
    d.rounded_rectangle([0, 0, 127, 159], radius=60, fill=hexc("#5a2a3a"))
    d.rounded_rectangle([10, 10, 117, 159], radius=52, fill=hexc("#1a0608"))
    d.rounded_rectangle([22, 28, 105, 159], radius=44, fill=hexc("#6a1410"))
    d.rounded_rectangle([36, 52, 91, 159], radius=30, fill=hexc("#ff5a30"))
    for k in range(9):
        a = math.radians(200 + k * 17.5)
        d.ellipse([64 + 52 * math.cos(a) - 3, 66 + 56 * math.sin(a) - 3, 64 + 52 * math.cos(a) + 3, 66 + 56 * math.sin(a) + 3], fill=hexc("#ffc060"))
    return im


def shutter_panel():
    im, d = canvas(96, 64)
    d.rectangle([0, 0, 95, 63], fill=hexc("#2e2a3c"))
    for y in range(0, 64, 8):
        d.rectangle([0, y, 95, y + 6], fill=hexc("#3e3a50"))
    d.rectangle([0, 0, 95, 3], fill=hexc("#c8a030"))
    return speckle(im, 0.3, 128)


def runes():
    im, d = canvas(64, 96)
    d.rectangle([0, 0, 63, 95], fill=hexc("#1a1022"))
    rnd = random.Random(129)
    for row in range(6):
        for col in range(3):
            x, y = 8 + col * 18, 6 + row * 15
            for _ in range(3):
                d.line([(x + rnd.randint(0, 10), y + rnd.randint(0, 10)), (x + rnd.randint(0, 10), y + rnd.randint(0, 10))], fill=hexc("#ff7a50"), width=2)
    return im


TEXTURES = {"ms_wall_rib": wall_rib, "ms_wall_dark": wall_dark, "ms_floor_walk": floor_walk, "ms_floor_void": floor_void, "ms_floor_plate": floor_plate, "ms_ceil": ceil_arch,
            "ms_trim": trim, "ms_rail": rail_tile}
PROPS = {"ms_crystal": crystal, "ms_console": console, "ms_orb": orb, "ms_cables_hang": cables_hang, "ms_armillary": armillary, "ms_dj_rig": dj_rig, "ms_speaker": speaker,
         "ms_organ": organ, "ms_hatch_arch": hatch_arch, "ms_case": case, "ms_lamp_post": lamp_post, "ms_brazier": brazier, "ms_pillar": pillar}
DECALS = {"ms_oval_window": oval_window, "ms_wall_lamp": wall_lamp, "ms_hatch_dock": hatch_dock, "ms_hatch_uw": hatch_uw, "ms_shutter_panel": shutter_panel, "ms_runes": runes}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in {**TEXTURES, **PROPS, **DECALS}.items():
        fn().save(os.path.join(OUT, name + ".png"))
    print("wrote %d textures, %d props and %d decals to %s" % (len(TEXTURES), len(PROPS), len(DECALS), OUT))


if __name__ == "__main__":
    sys.exit(main())
