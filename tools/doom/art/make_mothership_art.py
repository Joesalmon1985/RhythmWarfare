"""The Mothership's placeholder art (docs/doom/scenes/mothership.md): textures, props, decals, written to assets/story/doom_mothership/textures/; the three guides are
tools/doom/art/make_mothership_guides.py.

    python -I tools/doom/art/make_mothership_art.py

PLACEHOLDER art, procedural (PIL, hashed noise, the Booth's helpers), 128 px tiles, in the painting's palette: a lattice of pale lilac bone ribs round dark openings (three variants),
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
    """The Underworld hatch (stage D round 2): a bone arch (the painting's stair alcove is framed in ribs) round a passage glowing from within, the furnace's light rising from a
    yellow core through orange to a red rim (an ordered dither, no flat fill), steps climbing into it in silhouette and a ring of amber rune lamps over the arch."""
    W, Hh = 128, 160
    im, d = canvas(W, Hh)
    d.rounded_rectangle([0, 0, W - 1, Hh - 1], radius=60, fill=hexc("#c8b4c8"))
    d.rounded_rectangle([4, 4, W - 5, Hh - 1], radius=56, fill=hexc("#8a7498"))
    d.rounded_rectangle([12, 14, W - 13, Hh - 1], radius=50, fill=hexc("#3a1a28"))
    px = im.load()
    inner = Image.new("L", (W, Hh), 0)
    ImageDraw.Draw(inner).rounded_rectangle([18, 22, W - 19, Hh - 1], radius=44, fill=255)
    m = inner.load()
    cols = [hexc("#7a1810"), hexc("#c8361a"), hexc("#f06a24"), hexc("#ffa840"), hexc("#ffe08a")]
    for y in range(Hh):
        for x in range(W):
            if m[x, y] < 128:
                continue
            r = math.hypot((x - W / 2) / 40.0, (y - Hh * 0.62) / 70.0)  # the core low in the passage
            v = max(0.0, 1.0 - r) * 4.0 + (BAYER4[y % 4][x % 4] - 7.5) / 16.0
            px[x, y] = (*cols[max(0, min(4, int(v)))], 255)
    for k in range(6):  # the steps going up into the light: dark treads
        y = Hh - 4 - k * 11
        w = 40 - k * 4
        d.rectangle([W // 2 - w, y, W // 2 + w, y + 2], fill=hexc("#3a0e0a"))
    # the bone frame's lit left flank and dithered tesserae
    for y in range(Hh):
        for x in range(0, 12):
            if px[x, y][3] and BAYER4[y % 4][x % 4] < 6:
                px[x, y] = (*hexc("#f2e6d8"), 255)
    for k in range(9):
        a = math.radians(200 + k * 17.5)
        cx, cy = 64 + 54 * math.cos(a), 66 + 58 * math.sin(a)
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=hexc("#ffc060"), outline=hexc("#5a2a10"))
        d.point((int(cx), int(cy)), fill=hexc("#fff4c8"))
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


# --- stage D round 1 (docs/briefs/DOOM_POLISH_BRIEF.md): organic ribs for the polka dots, the void's cliffs and haze band, the vault sky -------------------------------------------

BAYER4 = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def rib_lattice(seed, n=3, stretch=1.7, rib=24.0, T=256):
    """The painting's bone lattice: a wrapped Voronoi of tall cells (stretched vertically: the ribs run up the wall) whose borders are thick pale bone ribs, shaded round (a lit
    left flank, a dark right flank, dithered between), and whose cells are the dark violet openings (deeper toward their middle, a faint green from the pool far below in the lower
    ones). Every seed gives a different tile: three variants keep a wall from repeating."""
    # stage D round 2: a 256 px tile (2 m of wall at 128 texels per metre) holding 4 cells, so an opening is a metre or more as the painting's are (the 128 px tile of 7 cells read
    # as a crackle pattern); warm bone (the amber lamps catch it) against deep violet openings
    S = T
    rnd = random.Random(seed)
    pts = [(rnd.uniform(0, S), rnd.uniform(0, S)) for _ in range(n)]
    im = Image.new("RGB", (S, S))
    px = im.load()
    bone_l, bone, bone_d, bone_dd = hexc("#f2e6d8"), hexc("#c8b4c8"), hexc("#8a7498"), hexc("#3e2e58")
    hole, hole_d, glow = hexc("#24163e"), hexc("#100820"), hexc("#1e4a40")
    for y in range(S):
        for x in range(S):
            best, second, bi, si, bx = 1e9, 1e9, 0, 0, 0.0
            vec = {}
            for i, (qx, qy) in enumerate(pts):
                dx = (x - qx + S / 2) % S - S / 2
                dy = ((y - qy + S / 2) % S - S / 2) / stretch
                vec[i] = (dx, dy)
                dd = dx * dx + dy * dy
                if dd < best:
                    second, si, best, bi, bx = best, bi, dd, i, dx
                elif dd < second:
                    second, si = dd, i
            sep = math.hypot(vec[bi][0] - vec[si][0], vec[bi][1] - vec[si][1]) or 1.0
            edge = (second - best) / (2.0 * sep)  # the distance to the cells' border (the bisector), in the stretched metric
            b = BAYER4[y % 4][x % 4] / 16.0
            if edge < rib:  # the rib: round shading across it, the lit side toward the cell's left
                t = edge / rib  # 0 at the rib's crest .. 1 at its foot
                side = -1 if bx > 0 else 1  # which flank of the rib this pixel is on
                v = 1.0 - t * 0.9 + (0.25 if side < 0 else -0.25) * t
                if v + (b - 0.5) * 0.3 > 0.85:
                    c = bone_l
                elif v + (b - 0.5) * 0.3 > 0.55:
                    c = bone
                elif v + (b - 0.5) * 0.3 > 0.28:
                    c = bone_d
                else:
                    c = bone_dd
                if ((x // 2) * 7 + (y // 2) * 13 + seed) % 11 == 0:  # the mosaic: a tessera a shade off (the painting's ribs are tiled)
                    c = shade(c, 0.86)
            else:  # the opening
                depth = min(1.0, (edge - rib) / 30.0)
                c = hole if depth + (b - 0.5) * 0.4 < 0.55 else hole_d
                if pts[bi][1] > S * 0.55 and depth > 0.4 and b < 0.25:
                    c = glow
            px[x, y] = c
    return speckle(im, 0.12, seed + 1)


def wall_rib():
    """Pale bone ribs (the painting's organic walls), variant a."""
    return rib_lattice(211)


def wall_rib_b():
    return rib_lattice(223, n=3, stretch=2.1, rib=20.0)


def wall_rib_c():
    return rib_lattice(239, n=4, stretch=1.5, rib=22.0)


def rim_lamp():
    """The amber floor lamps along the ring's rim (the painting's warm practicals at the railing's foot): a small glowing block in a dark housing, dithered core."""
    im, d = canvas(32, 20)
    d.rounded_rectangle([0, 2, 31, 19], radius=3, fill=hexc("#2a1e34"), outline=hexc("#0e0a16"))
    d.rectangle([4, 6, 27, 15], fill=hexc("#ffa830"))
    for y in range(7, 15):
        for x in range(5, 27):
            if BAYER4[y % 4][x % 4] < 7:
                d.point((x, y), fill=hexc("#fff0b0"))
    return im


def void_cliff():
    """The void's cliffs (the faces under the ring's rim and the platform, 9 m down to the pool): pale arch legs (vertical bone ribs) against deep violet, a mint wash at their feet
    (the pool lamps add the glow, the haze band decals the depth)."""
    rnd = random.Random(251)
    im = Image.new("RGB", (S, S), hexc("#1a1030"))
    d = ImageDraw.Draw(im)
    x = 4
    while x < S:
        w = rnd.choice((14, 18, 22))
        d.rectangle([x, 0, x + w, S], fill=hexc("#9a8ab8"))
        d.rectangle([x, 0, x + 3, S], fill=hexc("#d8ccf0"))
        d.rectangle([x + w - 3, 0, x + w, S], fill=hexc("#4a3a68"))
        for yy in range(S):
            for xx in range(x + 4, x + w // 2):
                if BAYER4[yy % 4][xx % 4] < 5:
                    im.putpixel((xx, yy), hexc("#b8a8d4"))
        x += w + rnd.choice((24, 30, 36))
    for yy in range(S):  # faint green slots of light between the legs
        for xx in range(S):
            if im.getpixel((xx, yy)) == hexc("#1a1030") and (xx * 3 + yy) % 41 == 0:
                im.putpixel((xx, yy), hexc("#3a8a6a"))
    return speckle(im, 0.15, 252)


def void_haze():
    """The void's depth haze (the hook's work-around: StoryWorld's void haze is off when the void is split into wedges, void_top equals the floor): a band hung on each wedge's
    cliffs, 96 x 256, clear at the top and denser toward the bottom in an ordered dither of the pool's mint mist and the room's violet (an opaque cut-out: no blending in the decal pass)."""
    W, Hh = 96, 256
    im = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
    px = im.load()
    rnd = random.Random(261)
    for y in range(Hh):
        t = y / float(Hh - 1)
        dens = max(0.0, (t - 0.12) / 0.88) ** 0.8  # 0 at the top eighth .. 1 at the bottom
        for x in range(W):
            b = (BAYER4[y % 4][x % 4] + 0.5) / 16.0
            wob = 0.08 * math.sin(x * 0.21 + y * 0.05) + 0.05 * math.sin(x * 0.07 - y * 0.11)
            if dens + wob > b:
                k = 0.7 + 0.5 * t + rnd.random() * 0.08
                c = shade(hexc("#3a8a72"), k) if (x // 2 + y // 3) % 3 else shade(hexc("#4a3a7a"), k)
                px[x, y] = (*c, 255)
    return im


def sky_vault():
    """The atrium's vault as the map's sky (512 x 128, horizon row 97): the void's violet haze rising into a dark vault crossed by pale bone arches, dithered."""
    W, Hh, hz = 512, 128, 97
    im = Image.new("RGB", (W, Hh))
    px = im.load()
    for y in range(Hh):
        t = min(1.0, y / float(hz))
        base = (int(16 + 44 * t), int(10 + 22 * t), int(34 + 56 * t))
        for x in range(W):
            n = math.sin(x * 0.03 + y * 0.2) * 0.5 + math.sin(x * 0.011 - y * 0.07) * 0.7
            px[x, y] = shade(base, 0.85 + 0.12 * n + (BAYER4[y % 4][x % 4] - 7.5) / 70.0)
    d = ImageDraw.Draw(im)
    for k in range(8):  # the arches of the vault: pale ribs sweeping up from the horizon
        cx = k * 64 + 32
        for w, col in ((7, "#5a4a7a"), (4, "#8a7aa8"), (1, "#c8b8e0")):
            d.arc([cx - 60, 10, cx + 60, 200], 190, 350, fill=hexc(col), width=w)
    return im


# --- stage D round 2 (docs/briefs/DOOM_POLISH_ROUND2_BRIEF.md): the ribs as a few sweeping arches, not a fine white mesh ------------------------------------------------------------

def wall_rib_r2(v=0):
    """The outer wall between the arches (256 px, 2 m): soft bone on dusky violet at LOW contrast (the painting's bone is cream lit by amber, not white on violet): one broad rib
    swaying up the tile, a narrower one beside it, the shadowed hollows between them a deep violet with a dithered edge. Three variants (the rib's sway and place)."""
    T = 256
    rnd = random.Random(401 + 37 * v)
    im = Image.new("RGB", (T, T), hexc("#443858"))
    px = im.load()
    ribs = [(rnd.uniform(40, 216), rnd.uniform(20, 28), rnd.choice((1, 2)), rnd.uniform(0, 6.28)), (rnd.uniform(0, 256), 9, rnd.choice((1, 2, 3)), rnd.uniform(0, 6.28))]  # (one soft rib and a thin one: the arches carry the bone)
    for y in range(T):
        for x in range(T):
            b = (BAYER4[y % 4][x % 4] - 7.5) / 16.0
            c = None
            for cx, w, f, ph in ribs:
                xc = cx + 10 * math.sin(y / T * 2 * math.pi * f + ph)  # (whole periods: the tile wraps)
                dx = ((x - xc + T / 2) % T) - T / 2
                if abs(dx) < w:
                    t = dx / w  # -1 left flank .. 1 right flank
                    v2 = 0.75 - 0.45 * t - 0.25 * t * t + b * 0.25
                    c = hexc("#b8a8ac") if v2 > 0.8 else hexc("#988496") if v2 > 0.5 else hexc("#74627e") if v2 > 0.25 else hexc("#544462")
                    break
            if c is None:  # the hollow: deeper toward its middle
                c = hexc("#4a3c62") if b > -0.2 else hexc("#3a2e52")
            px[x, y] = c
    return speckle(im, 0.1, 402 + v)


def wall_bone():
    """The hatch alcoves' walls (round 2): the painting frames each hatch in close bone ribs, lit warm by the hatch lamps: the round 1 lattice, softened and warmed."""
    im = rib_lattice(239, n=4, stretch=1.5, rib=26.0)
    r, g, b = im.split()
    warm = Image.merge("RGB", [r.point(lambda v: min(255, int(v * 1.05 + 14))), g.point(lambda v: min(255, int(v * 0.95 + 8))), b.point(lambda v: int(v * 0.85))])
    return Image.blend(warm, Image.new("RGB", warm.size, hexc("#7a6a86")), 0.45)  # (half its contrast: soft bone, not a shouting lattice)


def arch(v=0):
    """A sweeping bone arch (decal, 192 x 320, hung on the outer wall every ring piece: 5.3 m tall, 3.2 m wide): two thick ribs rising from the floor and leaning in to meet in a pointed
    arch near the top, rounded (a lit left flank warm from the amber lamps, a violet right flank), tesserae dithered on them; transparent between and around (the wall shows)."""
    W, Hh = 192, 320
    im, d = canvas(W, Hh)
    px = im.load()
    rnd = random.Random(431 + v)
    lean = (0.0, 10.0)[v]
    for y in range(Hh):
        t = y / float(Hh - 1)  # 0 top .. 1 floor
        half = (W / 2 - 18) * min(1.0, (t / 0.42) ** 0.55)  # the ribs' centre lines: together at the top, apart below
        wid = 13 + 13 * t  # thicker toward the floor
        for side in (-1, 1):
            cx = W / 2 + side * half + lean * math.sin(t * 3.0) * side
            for x in range(int(cx - wid), int(cx + wid) + 1):
                if not (0 <= x < W):
                    continue
                u = (x - cx) / wid  # -1 .. 1 across the rib
                if abs(u) > 1:
                    continue
                b = (BAYER4[y % 4][x % 4] - 7.5) / 16.0
                lit = 0.78 - 0.5 * u * (1 if side < 0 else 0.6) - 0.3 * u * u + b * 0.25
                c = hexc("#e6d4c0") if lit > 0.82 else hexc("#bca898") if lit > 0.52 else hexc("#8a7488") if lit > 0.26 else hexc("#4e3e60")
                if (x * 7 + y * 13 + v) % 17 == 0:
                    c = shade(c, 0.88)
                px[x, y] = (*c, 255)
    # a thin inner rib following the arch (the painting's double ribs), and a keystone lamp at the crown
    for y in range(40, Hh):
        t = y / float(Hh - 1)
        half = (W / 2 - 18) * min(1.0, (t / 0.42) ** 0.55) - 28
        if half < 4:
            continue
        for side in (-1, 1):
            x = int(W / 2 + side * half)
            if 0 <= x < W - 2:
                for k in range(3):
                    px[x + k, y] = (*hexc("#9a8698"), 255)
    d.ellipse([W / 2 - 7, 30, W / 2 + 7, 44], fill=hexc("#ffb040"), outline=hexc("#5a3010"))
    d.point((int(W / 2), 36), fill=hexc("#fff0c0"))
    return im


def rail_r2():
    """The balustrade (round 2): a warm bone coping and a frame round a LARGE oval opening (the painting's: most of the panel is open, the pool's glow shows through), alpha 0 in it."""
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    stone, light, dark = hexc("#9a8a98"), hexc("#d4c4bc"), hexc("#3a2e48")
    d.rectangle([0, 0, S, 18], fill=(*stone, 255))
    d.rectangle([0, 0, S, 4], fill=(*light, 255))
    d.rectangle([0, 15, S, 18], fill=(*dark, 255))
    d.rectangle([0, 18, S, S], fill=(*stone, 255))
    d.rectangle([0, 18, 5, S], fill=(*light, 255))
    d.ellipse([10, 24, 118, 120], fill=(0, 0, 0, 0))
    d.arc([10, 24, 118, 120], 0, 360, fill=(*dark, 255), width=3)
    d.arc([13, 27, 115, 117], 200, 300, fill=(*light, 255), width=2)
    return im


def hatch_dock_r2():
    """The dock hatch's far doorway (round 2, emissive decal 128 x 144 at the end of the lit passage dk_c): a bone oval arch round a corridor running on, violet walls, amber floor
    lamps in two rows receding to a warm bright door, the wet floor catching them (the painting's right-hand passage). No shutter."""
    W, Hh = 128, 144
    im, d = canvas(W, Hh)
    d.rounded_rectangle([0, 0, W - 1, Hh - 1], radius=56, fill=hexc("#c8b4b0"))
    d.rounded_rectangle([5, 5, W - 6, Hh - 1], radius=52, fill=hexc("#8a7488"))
    d.rounded_rectangle([12, 14, W - 13, Hh - 1], radius=46, fill=hexc("#1c1430"))
    px = im.load()
    cx, hz = W // 2, 70
    for y in range(hz, Hh):  # the wet floor: violet, the lamps' amber streaks on it
        t = (y - hz) / float(Hh - hz)
        hw = int(6 + 46 * t)
        for x in range(cx - hw, cx + hw + 1):
            if 12 < x < W - 13 and px[x, y][3]:
                b = BAYER4[y % 4][x % 4]
                px[x, y] = (*(hexc("#3a2c50") if b < 8 else hexc("#2a2040")), 255)
    for y in range(24, hz):  # the walls and the vault receding: darker toward the far door
        t = (hz - y) / float(hz - 24)
        hw = int(6 + 40 * t)
        for x in (cx - hw, cx + hw):
            if 12 < x < W - 13:
                px[x, y] = (*hexc("#5a4870"), 255)
    d.rectangle([cx - 6, hz - 16, cx + 6, hz], fill=hexc("#ffcf80"))  # the far door, bright
    d.rectangle([cx - 3, hz - 13, cx + 3, hz - 1], fill=hexc("#fff0c8"))
    for k in range(6):  # two rows of floor lamps, receding, each with a streak on the wet floor
        t = (k + 1) / 7.0
        y = int(hz + (Hh - hz) * t * t)
        for side in (-1, 1):
            x = cx + side * int(6 + 44 * t * t)
            r = 1 + int(3 * t)
            d.rectangle([x - r, y - r, x + r, y + r // 2], fill=hexc("#ffb040"))
            for yy in range(y + 2, min(Hh, y + 2 + 3 * r)):
                if BAYER4[yy % 4][x % 4] < 9:
                    px[x, yy] = (*hexc("#c88040"), 255)
    for y in range(Hh):  # the bone frame's lit left flank, dithered
        for x in range(0, 10):
            if px[x, y][3] and BAYER4[y % 4][x % 4] < 6:
                px[x, y] = (*hexc("#f2e6d8"), 255)
    return im


def floor_void_r2():
    """The pool (round 2, unhazed now: the shore): a luminous mint-green water, brighter swirl rings, dithered (the painting's main light)."""
    rnd = random.Random(114)
    im = Image.new("RGB", (S, S), hexc("#1e7a52"))
    px = im.load()
    for y in range(S):
        for x in range(S):
            n = math.sin(x * 0.2 + y * 0.09) + math.sin(y * 0.17 - x * 0.06)
            px[x, y] = hexc("#2a9a68") if BAYER4[y % 4][x % 4] < 7 + 3 * n else hexc("#166048")
    d = ImageDraw.Draw(im)
    for _ in range(16):
        x, y, r = rnd.randrange(S), rnd.randrange(S), rnd.randint(8, 30)
        for off in (-S, 0, S):
            d.ellipse([x - r + off, y - r // 2, x + r + off, y + r // 2], outline=shade(hexc("#9affc8"), 0.6 + rnd.random() * 0.5))
    return im


def void_cliff_r2():
    """The void's cliffs (round 2): the pale arch legs of round 1 on deep violet, the pool's mint light washing up them from below (a dithered band in the tile's lower half)."""
    im = void_cliff()
    px = im.load()
    for y in range(S // 2, S):
        k = (y - S // 2) / float(S // 2)
        for x in range(S):
            if BAYER4[y % 4][x % 4] < int(10 * k):
                c = px[x, y]
                px[x, y] = (c[0] // 2 + 20, min(255, c[1] // 2 + 90), c[2] // 2 + 50)
    return im


TEXTURES = {"ms_wall_bone": wall_bone, "ms_wall_rib": wall_rib_r2, "ms_wall_rib_b": lambda: wall_rib_r2(1), "ms_wall_rib_c": lambda: wall_rib_r2(2), "ms_wall_dark": wall_dark, "ms_floor_walk": floor_walk, "ms_floor_void": floor_void_r2,
            "ms_floor_plate": floor_plate, "ms_ceil": ceil_arch, "ms_trim": trim, "ms_rail": rail_r2, "ms_void_cliff": void_cliff_r2, "ms_sky": sky_vault}
PROPS = {"ms_crystal": crystal, "ms_console": console, "ms_orb": orb, "ms_cables_hang": cables_hang, "ms_armillary": armillary, "ms_dj_rig": dj_rig, "ms_speaker": speaker,
         "ms_organ": organ, "ms_hatch_arch": hatch_arch, "ms_case": case, "ms_lamp_post": lamp_post, "ms_brazier": brazier, "ms_pillar": pillar,
         "ms_rim_lamp": rim_lamp}
DECALS = {"ms_void_haze": void_haze, "ms_oval_window": oval_window, "ms_wall_lamp": wall_lamp, "ms_hatch_dock": hatch_dock_r2, "ms_arch_a": arch, "ms_arch_b": lambda: arch(1), "ms_hatch_uw": hatch_uw, "ms_shutter_panel": shutter_panel, "ms_runes": runes}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in {**TEXTURES, **PROPS, **DECALS}.items():
        fn().save(os.path.join(OUT, name + ".png"))
    print("wrote %d textures, %d props and %d decals to %s" % (len(TEXTURES), len(PROPS), len(DECALS), OUT))


if __name__ == "__main__":
    sys.exit(main())
