"""The Loading Dock's placeholder art (docs/doom/scenes/dock.md): textures, props, decals and the three guides, written to assets/story/doom_dock/textures/.

    python -I tools/doom/art/make_dock_art.py

PLACEHOLDER art, procedural (PIL, hashed noise), at the style guide's pixel density (128 texels per metre for walls and floors) and in the painting's palette
(`art/reference/doom_worlds/Rainy Rhythm Club Loading Dock-6.png`): red brick, rusted steel, wet asphalt and concrete with sodium and blue reflections, a dark night sky, lit windows in dark
towers, a glowing furnace mouth. It is below the owner's standard (art/reference/standard/guide_floor_sprite_standard.png); an art pass replaces the PNGs: the file names, sizes and frames per
state are the data contract. The guides are drawn by tools/doom/art/make_dock_guides.py (the Floor guide of the Lounge's set, the violet horned Mothership guide, the red horned Underworld guide).
"""
from __future__ import annotations

import os
import random
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_booth_art as mb  # noqa: E402  (hexc, shade, speckle, rust, canvas, outline, case: shared helpers)

ROOT = mb.ROOT
OUT = os.path.join(ROOT, "assets", "story", "doom_dock", "textures")
S = 128
hexc, shade, speckle, rust, canvas, outline = mb.hexc, mb.shade, mb.speckle, mb.rust, mb.canvas, mb.outline


def streaks(im, seed, n=26, col="#6a7aa8", alpha=0.35):
    """Rain running down a surface: thin vertical light streaks (in place)."""
    rnd = random.Random(seed)
    px = im.load()
    for _ in range(n):
        x = rnd.randrange(im.width)
        y0 = rnd.randrange(im.height)
        ln = rnd.randint(10, 40)
        c = hexc(col)
        for y in range(y0, y0 + ln):
            yy = y % im.height
            p = px[x, yy]
            px[x, yy] = tuple(int(p[k] * (1 - alpha) + c[k] * alpha) for k in range(3)) + tuple(p[3:])
    return im


def puddles(im, seed, cols=("#c8782c", "#3a50a0", "#a04a30"), n=7):
    """Wet gloss: soft horizontal reflection smears of the street lights."""
    rnd = random.Random(seed)
    d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y = rnd.randrange(S), rnd.randrange(S)
        w, h = rnd.randint(10, 34), rnd.randint(2, 5)
        c = hexc(rnd.choice(cols))
        base = im.getpixel((x % S, y % S))
        d.rectangle([x, y, x + w, y + h], fill=tuple(int(base[k] * 0.55 + c[k] * 0.45) for k in range(3)))
    return im


# --- textures (tile 128 x 128) -------------------------------------------------------------------------------------------------------------------------------

def wall_brick():
    im = Image.new("RGB", (S, S), hexc("#5a2420"))
    d = ImageDraw.Draw(im)
    rnd = random.Random(3)
    for row, y in enumerate(range(0, S, 8)):
        off = 0 if row % 2 == 0 else 16
        for x in range(-off, S, 32):
            tone = rnd.choice(["#6a2a24", "#58201c", "#722e26", "#4c1c1a", "#642622"])
            d.rectangle([x + 1, y + 1, x + 30, y + 6], fill=hexc(tone))
        d.line([(0, y), (S, y)], fill=hexc("#1e1210"))
    for row, y in enumerate(range(0, S, 8)):
        off = 0 if row % 2 == 0 else 16
        for x in range(-off, S, 32):
            d.line([(x, y), (x, y + 8)], fill=hexc("#1e1210"))
    return streaks(speckle(im, 0.3, 5), 6, 20, "#8a6a8a", 0.25)


def wall_tower():
    """A dark glass-and-concrete tower face: a grid of windows, some lit amber."""
    im = Image.new("RGB", (S, S), hexc("#141a2c"))
    d = ImageDraw.Draw(im)
    rnd = random.Random(7)
    for y in range(6, S, 24):
        for x in range(6, S, 32):
            lit = rnd.random() < 0.28
            d.rectangle([x, y, x + 20, y + 14], fill=hexc("#e0a448" if lit else "#0c1020"))
            d.rectangle([x, y + 14, x + 20, y + 15], fill=hexc("#2a3450"))
    for x in range(0, S, 32):
        d.line([(x, 0), (x, S)], fill=hexc("#0a0e1c"))
    return streaks(speckle(im, 0.2, 9), 10, 24, "#4a5a88", 0.3)


def wall_ware():
    """The brown warehouse block across the street: stained brick-brown with two windows lit."""
    im = Image.new("RGB", (S, S), hexc("#463a2c"))
    d = ImageDraw.Draw(im)
    rnd = random.Random(11)
    for y in range(0, S, 16):
        d.line([(0, y), (S, y)], fill=hexc("#2a2018"))
    for x in range(8, S, 64):
        for y in (20, 76):
            lit = rnd.random() < 0.55
            d.rectangle([x, y, x + 20, y + 30], fill=hexc("#d89a44" if lit else "#1a1612"))
            d.line([(x + 10, y), (x + 10, y + 30)], fill=hexc("#2a2018"))
            d.line([(x, y + 15), (x + 20, y + 15)], fill=hexc("#2a2018"))
    return streaks(speckle(im, 0.35, 13), 14, 20, "#7a7a98", 0.25)


def wall_shutter():
    """The club's roller shutter: horizontal steel slats, rust at the edges and a few bright rain streaks."""
    im = Image.new("RGB", (S, S), hexc("#5a5650"))
    d = ImageDraw.Draw(im)
    for y in range(0, S, 8):
        d.rectangle([0, y, S, y + 5], fill=hexc("#6c6860"))
        d.rectangle([0, y + 6, S, y + 7], fill=hexc("#22201c"))
        d.line([(0, y), (S, y)], fill=hexc("#8a867c"))
    rust(im, 15, 0.5, (140, 78, 40))
    return streaks(speckle(im, 0.25, 16), 17, 16, "#9aa8c8", 0.3)


def wall_steel():
    im = Image.new("RGB", (S, S), hexc("#4a4c54"))
    d = ImageDraw.Draw(im)
    for y in (32, 96):
        d.rectangle([0, y, S, y + 2], fill=hexc("#1c1e24"))
    for y in (16, 48, 80, 112):
        for x in range(8, S, 16):
            d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=hexc("#8a8c98"))
    return rust(speckle(im, 0.25, 21), 22, 0.4)


def wall_blue():
    """The passage behind the club door: dark panels washed in blue light."""
    im = Image.new("RGB", (S, S), hexc("#1c2a58"))
    d = ImageDraw.Draw(im)
    for x in range(0, S, 32):
        d.rectangle([x, 0, x + 1, S], fill=hexc("#0c1230"))
        d.rectangle([x + 2, 0, x + 5, S], fill=hexc("#3a5ad0"))
    for y in (40, 90):
        d.rectangle([0, y, S, y + 3], fill=hexc("#5a7aff"))
    return speckle(im, 0.25, 25)


def floor_conc():
    """The wet concrete apron: dark slabs with the yellow edge stripe and reflections of the sodium lamp."""
    im = Image.new("RGB", (S, S), hexc("#383840"))
    d = ImageDraw.Draw(im)
    d.line([(0, 0), (S, 0)], fill=hexc("#1c1c22"), width=2)
    d.line([(0, 0), (0, S)], fill=hexc("#1c1c22"), width=2)
    d.polygon([(0, 104), (S, 90), (S, 100), (0, 114)], fill=hexc("#a8821e"))
    puddles(im, 31)
    return streaks(speckle(im, 0.35, 32), 33, 10, "#6a7aa8", 0.2)


def floor_asphalt():
    im = Image.new("RGB", (S, S), hexc("#1c1c28"))
    d = ImageDraw.Draw(im)
    rnd = random.Random(41)
    for _ in range(400):
        x, y = rnd.randrange(S), rnd.randrange(S)
        d.point((x, y), fill=shade(hexc("#3a3a48"), 0.6 + rnd.random() * 0.8))
    d.rectangle([60, 8, 66, 40], fill=hexc("#6a6a70"))  # a worn lane dash
    puddles(im, 42, n=9)
    return speckle(im, 0.3, 43)


def floor_walk():
    im = Image.new("RGB", (S, S), hexc("#3e3a42"))
    d = ImageDraw.Draw(im)
    for k in (0, 64):
        d.line([(k, 0), (k, S)], fill=hexc("#1c1a20"), width=2)
        d.line([(0, k), (S, k)], fill=hexc("#1c1a20"), width=2)
    puddles(im, 51, cols=("#c8782c", "#3a50a0"), n=5)
    return speckle(im, 0.3, 52)


def floor_blue():
    im = Image.new("RGB", (S, S), hexc("#141c40"))
    d = ImageDraw.Draw(im)
    for k in range(0, S, 32):
        d.line([(k, 0), (k, S)], fill=hexc("#2a3a80"))
        d.line([(0, k), (S, k)], fill=hexc("#1c2658"))
    d.rectangle([0, 56, S, 62], fill=hexc("#3a5ad0"))
    return speckle(im, 0.25, 61)


def ceil_sky():
    """The night sky, a dark violet cloud wash (an ordinary ceiling tile: the renderer's real sky needs a hook, see docs/doom/scenes/dock.md)."""
    im = Image.new("RGB", (S, S), hexc("#14122a"))
    d = ImageDraw.Draw(im)
    rnd = random.Random(71)
    for _ in range(40):
        x, y = rnd.randrange(S), rnd.randrange(S)
        r = rnd.randint(8, 24)
        d.ellipse([x - r, y - r // 2, x + r, y + r // 2], fill=shade(hexc("#2a2250"), 0.7 + rnd.random() * 0.6))
    return speckle(im, 0.2, 72)


def ceil_truss():
    """The canopy's steel underside: dark girders in a grid with rust."""
    im = Image.new("RGB", (S, S), hexc("#2a2a30"))
    d = ImageDraw.Draw(im)
    for k in (0, 64):
        d.rectangle([k, 0, k + 7, S], fill=hexc("#44444c"))
        d.rectangle([0, k, S, k + 7], fill=hexc("#44444c"))
    for k in range(0, S, 16):
        d.line([(k, 0), (k + 16, 64)], fill=hexc("#1c1c20"))
    return rust(speckle(im, 0.3, 81), 82, 0.3)


def trim():
    """The kerb: concrete with yellow chipped paint."""
    im = Image.new("RGB", (S, S), hexc("#4a4650"))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, S, 14], fill=hexc("#8a7424"))
    d.rectangle([0, 15, S, 17], fill=hexc("#1c1a20"))
    return speckle(im, 0.4, 91)


# --- props (billboards) -----------------------------------------------------------------------------------------------------------------------------------

def bollard():
    im, d = canvas(40, 96)
    d.rounded_rectangle([6, 4, 33, 94], radius=8, fill=hexc("#7a7478"))
    d.rectangle([6, 36, 33, 52], fill=hexc("#d8a820"))
    d.rectangle([24, 8, 33, 92], fill=hexc("#4a464a"))
    d.rectangle([8, 8, 12, 90], fill=hexc("#aaa4a8"))
    return outline(rust(speckle(im, 0.35, 101), 102, 0.3))


def pallet():
    im, d = canvas(112, 40)
    d.rectangle([0, 0, 111, 10], fill=hexc("#8a5a34"))
    for x in (0, 40, 80):
        d.rectangle([x, 12, x + 24, 28], fill=hexc("#6a4224"))
    d.rectangle([0, 30, 111, 38], fill=hexc("#7a4e2c"))
    for x in range(8, 111, 20):
        d.line([(x, 0), (x, 10)], fill=hexc("#3a2214"))
    return outline(speckle(im, 0.4, 103))


def pallet_stack():
    im, d = canvas(96, 112)
    for k in range(5):
        y = 4 + k * 21
        d.rectangle([0, y, 95, y + 7], fill=hexc("#8a5a34"))
        for x in (2, 36, 70):
            d.rectangle([x, y + 8, x + 22, y + 18], fill=hexc("#6a4224"))
        d.rectangle([0, y + 19, 95, y + 20], fill=hexc("#7a4e2c"))
    return outline(speckle(im, 0.4, 104))


def crate():
    im, d = canvas(64, 56)
    d.rectangle([0, 0, 63, 55], fill=hexc("#8a6038"))
    for y in (0, 18, 36):
        d.rectangle([0, y, 63, y + 14], fill=hexc("#9a6c40"))
        d.line([(0, y + 15), (63, y + 15)], fill=hexc("#3a2414"), width=2)
    d.line([(0, 0), (63, 55)], fill=hexc("#4a2e18"), width=2)
    return outline(speckle(im, 0.4, 105))


def van():
    im, d = canvas(220, 110)
    d.rounded_rectangle([4, 20, 215, 92], radius=10, fill=hexc("#aeb0b6"))  # body
    d.rectangle([4, 70, 215, 92], fill=hexc("#8a8c92"))
    d.polygon([(150, 24), (190, 24), (214, 54), (214, 62), (150, 62)], fill=hexc("#2a3040"))  # cab windows
    d.rectangle([20, 32, 120, 56], fill=hexc("#9a9ca2"))
    d.rectangle([118, 24, 120, 90], fill=hexc("#5a5c62"))
    d.rectangle([4, 78, 18, 84], fill=hexc("#c82a24"))  # tail light
    d.rectangle([210, 74, 215, 80], fill=hexc("#ffd890"))  # headlight
    for cx in (50, 170):
        d.ellipse([cx - 17, 74, cx + 17, 108], fill=hexc("#16161a"))
        d.ellipse([cx - 8, 83, cx + 8, 99], fill=hexc("#6a6a72"))
    return outline(rust(speckle(im, 0.3, 106), 107, 0.2))


def case_big():
    return mb.case()


def furnace():
    """The domed boiler with the glowing mouth, a smoke stack and pipes."""
    im, d = canvas(200, 190)
    d.rectangle([150, 0, 172, 80], fill=hexc("#3a2a24"))  # stack
    d.ellipse([20, 40, 190, 190], fill=hexc("#5a3626"))  # dome
    d.rectangle([20, 118, 190, 190], fill=hexc("#4a2c20"))
    for k in range(40, 190, 22):
        d.arc([20, 40, 190, 190], 200, 340, fill=hexc("#2a1810"), width=2)
        d.line([(k, 60 + abs(k - 105) // 3), (k, 188)], fill=hexc("#3a2218"))
    d.ellipse([70, 100, 150, 180], fill=hexc("#ff7a1c"))  # the mouth
    d.ellipse([84, 114, 136, 170], fill=hexc("#ffd060"))
    d.ellipse([96, 130, 124, 162], fill=hexc("#fff4c0"))
    d.rectangle([0, 80, 24, 190], fill=hexc("#4a3a30"))
    d.rectangle([176, 100, 199, 190], fill=hexc("#4a3a30"))
    return outline(rust(speckle(im, 0.3, 108), 109, 0.3))


def street_lamp():
    im, d = canvas(48, 224)
    d.rectangle([20, 22, 26, 223], fill=hexc("#2a2a30"))
    d.rectangle([20, 22, 26, 223], fill=hexc("#34343c"))
    d.polygon([(20, 22), (6, 8), (4, 12), (20, 28)], fill=hexc("#34343c"))
    d.rectangle([0, 6, 12, 14], fill=hexc("#ffc060"))
    d.rectangle([2, 8, 10, 12], fill=hexc("#fff0c0"))
    return outline(im)


def wall_lamp():
    im, d = canvas(48, 44)
    d.rectangle([0, 4, 6, 12], fill=hexc("#2a2a30"))
    d.arc([2, 4, 30, 30], 270, 360, fill=hexc("#2a2a30"), width=3)
    d.polygon([(20, 24), (44, 24), (38, 14), (26, 14)], fill=hexc("#1c1c22"))
    d.rectangle([22, 24, 42, 29], fill=hexc("#ffc060"))
    return outline(im)


def hang_lamp():
    im, d = canvas(32, 56)
    d.rectangle([14, 0, 17, 14], fill=hexc("#2a2a30"))
    d.rounded_rectangle([6, 14, 25, 50], radius=5, fill=hexc("#ffb040"))
    d.rounded_rectangle([10, 20, 21, 44], radius=3, fill=hexc("#fff0b0"))
    for y in (22, 32, 42):
        d.line([(6, y), (25, y)], fill=hexc("#2a2a30"))
    d.rectangle([4, 10, 27, 15], fill=hexc("#2a2a30"))
    return outline(im)


def chain():
    im, d = canvas(24, 120)
    for y in range(0, 120, 14):
        d.ellipse([6, y, 18, y + 14], outline=hexc("#6a6a72"), width=3)
    return outline(im)


def drum():
    im, d = canvas(64, 56)
    d.ellipse([2, 6, 61, 52], fill=hexc("#8a5a34"))
    d.ellipse([8, 10, 56, 28], fill=hexc("#e0d0a8"))
    d.ellipse([2, 6, 61, 52], outline=hexc("#3a2214"), width=2)
    return outline(im)


# --- decals (hung on a solid wall) -----------------------------------------------------------------------------------------------------------------------

def door_leaf():
    """The steel door ajar against the brick: a grey leaf with a push bar and a wet sheen."""
    im, d = canvas(96, 192)
    d.rectangle([0, 0, 95, 191], fill=hexc("#6a6e78"))
    d.rectangle([0, 0, 95, 6], fill=hexc("#9aa0ac"))
    d.rectangle([4, 4, 91, 187], outline=hexc("#40444e"), width=3)
    d.rectangle([8, 108, 82, 118], fill=hexc("#aab0ba"))
    d.rectangle([72, 100, 90, 126], fill=hexc("#2a2c32"))
    return streaks(rust(speckle(im, 0.25, 111), 112, 0.2), 113, 12, "#c8d0e0", 0.3)


def clef():
    """The treble clef sprayed on the brick, magenta with a white tag beside it."""
    im, d = canvas(96, 192)
    c = hexc("#a03a88")
    d.arc([22, 70, 74, 130], 0, 360, fill=c, width=7)
    d.line([(52, 20), (46, 150)], fill=c, width=7)
    d.arc([30, 10, 62, 60], 200, 380, fill=c, width=6)
    d.ellipse([28, 140, 50, 170], fill=c)
    d.rectangle([60, 150, 92, 186], fill=hexc("#d8d0d4"))
    return speckle(im, 0.4, 114)


def pipe_vert():
    im, d = canvas(24, 256)
    d.rectangle([4, 0, 17, 255], fill=hexc("#2a2a30"))
    d.rectangle([5, 0, 8, 255], fill=hexc("#4a4a54"))
    for y in range(20, 256, 70):
        d.rectangle([0, y, 21, y + 6], fill=hexc("#1c1c22"))
    return im


def pipes_yard():
    im, d = canvas(192, 128)
    for y, c in ((20, "#4a3a30"), (52, "#3a2e28"), (84, "#4a3a30")):
        d.rectangle([0, y, 191, y + 14], fill=hexc(c))
        d.rectangle([0, y, 191, y + 3], fill=hexc("#7a6050"))
    for x in (40, 110, 170):
        d.rectangle([x, 0, x + 12, 127], fill=hexc("#352a24"))
    return rust(speckle(im, 0.3, 115), 116, 0.4)


def fence():
    """Chain link, seen against a dark building: a wire diamond mesh (alpha elsewhere), posts every 3 m."""
    im = Image.new("RGBA", (192, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(-96, 192 * 2, 8):
        d.line([(k, 0), (k + 96, 96)], fill=(*hexc("#7a8294"), 150))
        d.line([(k + 96, 0), (k, 96)], fill=(*hexc("#7a8294"), 150))
    for x in (0, 94, 188):
        d.rectangle([x, 0, x + 3, 95], fill=(*hexc("#3a3e48"), 255))
    d.rectangle([0, 0, 191, 3], fill=(*hexc("#3a3e48"), 255))
    return im


def windows_lit():
    im, d = canvas(128, 96)
    rnd = random.Random(121)
    for y in (6, 52):
        for x in range(6, 120, 30):
            d.rectangle([x, y, x + 18, y + 30], fill=hexc("#ffb050" if rnd.random() < 0.7 else "#d88a40"))
            d.line([(x + 9, y), (x + 9, y + 30)], fill=hexc("#3a2a1c"))
            d.line([(x, y + 15), (x + 18, y + 15)], fill=hexc("#3a2a1c"))
    return im


def neon_blue():
    im, d = canvas(64, 24)
    for x in (8, 24, 40):
        d.rectangle([x, 2, x + 6, 22], fill=hexc("#6a9aff"))
        d.rectangle([x + 2, 4, x + 4, 20], fill=hexc("#d8e8ff"))
    return im


def shutter_big():
    im, d = canvas(192, 128)
    d.rectangle([0, 0, 191, 127], fill=hexc("#4a4640"))
    for y in range(0, 128, 8):
        d.rectangle([0, y, 191, y + 5], fill=hexc("#605c54"))
        d.rectangle([0, y + 7, 191, y + 7], fill=hexc("#1c1a16"))
    d.rectangle([0, 0, 191, 12], fill=hexc("#34302c"))
    return rust(speckle(im, 0.3, 123), 124, 0.5, (140, 78, 40))


def towers():
    """The night city at the street's end: layered dark towers with lit windows and a red aircraft lamp; emissive."""
    W, H = 384, 192
    im, d = canvas(W, H)
    rnd = random.Random(125)
    d.rectangle([0, 0, W, H], fill=hexc("#181436"))
    for layer, (base, hmax, win) in enumerate((("#1c2240", 130, "#8a7a50"), ("#141a34", 100, "#c89a50"), ("#0e1226", 70, "#ffb050"))):
        x = 0
        while x < W:
            bw = rnd.randint(30, 60)
            bh = rnd.randint(50, 50 + hmax)
            d.rectangle([x, H - bh, x + bw, H], fill=hexc(base))
            for wy in range(H - bh + 6, H - 6, 9):
                for wx in range(x + 4, x + bw - 4, 8):
                    if rnd.random() < 0.3:
                        d.rectangle([wx, wy, wx + 3, wy + 4], fill=hexc(win))
            x += bw + rnd.randint(0, 8)
    d.rectangle([300, 14, 302, 18], fill=hexc("#ff2020"))
    for _ in range(240):  # rain
        x, y = rnd.randrange(W), rnd.randrange(H)
        d.line([(x, y), (x - 2, y + 9)], fill=hexc("#6a7aa8"))
    return im


TEXTURES = {"dk_wall_brick": wall_brick, "dk_wall_tower": wall_tower, "dk_wall_ware": wall_ware, "dk_wall_shutter": wall_shutter, "dk_wall_steel": wall_steel, "dk_wall_blue": wall_blue,
            "dk_floor_conc": floor_conc, "dk_floor_asphalt": floor_asphalt, "dk_floor_walk": floor_walk, "dk_floor_blue": floor_blue, "dk_ceil_sky": ceil_sky, "dk_ceil_truss": ceil_truss,
            "dk_trim": trim}
PROPS = {"dk_bollard": bollard, "dk_pallet": pallet, "dk_pallet_stack": pallet_stack, "dk_crate": crate, "dk_van": van, "dk_case": case_big, "dk_furnace": furnace,
         "dk_street_lamp": street_lamp, "dk_wall_lamp": wall_lamp, "dk_hang_lamp": hang_lamp, "dk_chain": chain, "dk_drum": drum}
DECALS = {"dk_door_leaf": door_leaf, "dk_clef": clef, "dk_pipe_vert": pipe_vert, "dk_pipes_yard": pipes_yard, "dk_fence": fence, "dk_windows_lit": windows_lit, "dk_neon_blue": neon_blue,
          "dk_shutter": shutter_big, "dk_towers": towers}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in {**TEXTURES, **PROPS, **DECALS}.items():
        fn().save(os.path.join(OUT, name + ".png"))
    import make_dock_guides as dg
    n = dg.main()
    print("wrote %d textures, %d props, %d decals and %d guide frames to %s" % (len(TEXTURES), len(PROPS), len(DECALS), n, OUT))


if __name__ == "__main__":
    sys.exit(main())
