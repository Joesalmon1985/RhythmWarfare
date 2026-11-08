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
    """The passage behind the club door: dark panels (stage D: darker, so the light is in the LED strips, not a flat blue wash), a bright LED strip at hand height and a
    dimmer one low, panel seams with a lit edge, scuffs (256 px, 128 texels per metre)."""
    arr = ramp(vnoise(T, T, 131, ((4, 0.5), (16, 0.5))) * 0.6 + 0.15, ("#0a1030", "#24327a", "#3448a4", "#4a64cc"), cell=2)
    for x in range(0, T, 64):
        arr[:, x:x + 2] = hexa("#060a24")
        arr[:, x + 2:x + 4] = arr[:, x + 2:x + 4] * 0.4 + hexa("#4a6ae0") * 0.6
    arr[82:84, :] = hexa("#6a8aff")
    arr[84:90, :] = hexa("#c8d8ff")
    arr[90:92, :] = hexa("#6a8aff")
    glow = np.clip(1 - np.abs(np.arange(T) - 87) / 26.0, 0, 1)[:, None] * np.ones((1, T)) * 0.5
    glow[82:92] = 0
    mix_dither(arr, glow, "#3a58d0", k=0.45, cell=2)
    arr[180:184, :] = arr[180:184, :] * 0.4 + hexa("#5a7aff") * 0.6
    return to_img(arr)


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
    """The passage floor (stage D): dark rubber tiles, wet, the LED strip's long blue reflections and a lit centre line."""
    arr = ramp(vnoise(T, T, 171, ((4, 0.5), (16, 0.5))) * 0.6 + 0.15, ("#0a0e26", "#121a3c", "#1a2652", "#22326a"), cell=2)
    for k in range(0, T, 64):
        arr[k:k + 2, :] *= 0.5
        arr[:, k:k + 2] *= 0.5
    arr[:, 124:132] = arr[:, 124:132] * 0.3 + hexa("#8aa8ff") * 0.7
    wet_gloss(arr, 172, ("#4a6ae0", "#6a8aff", "#c070ff"), n=10, length=(80, 200), width=(3, 8), ripples=4, sheen="#3a4a9a")
    return to_img(arr)


def _floor_blue_old():
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
    d.rounded_rectangle([4, 20, 215, 92], radius=10, fill=hexc("#8a8c94"))  # body (a grimy grey: the painting's van is not white in the rain)
    d.rectangle([4, 70, 215, 92], fill=hexc("#6a6c74"))
    d.polygon([(150, 24), (190, 24), (214, 54), (214, 62), (150, 62)], fill=hexc("#2a3040"))  # cab windows
    d.rectangle([20, 32, 120, 56], fill=hexc("#7a7c84"))
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



# --- stage D polish (docs/briefs/DOOM_POLISH_BRIEF.md): numpy helpers shared with the Balcony and the Booth (make_balcony_art.py, make_booth_art.py import them) ------------------------
# Ordered (4 x 4 Bayer) dither between the steps of a ramp, tileable value noise, 256 px tiles (2 m at 128 texels per metre), wet gloss baked into floors, a storm sky strip.

import numpy as np  # noqa: E402

BAYER4 = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) + 0.5) / 16.0
T = 256  # a polished tile: 256 px over the renderer's 2 m = 128 texels per metre


def hexa(s):
    return np.array(hexc(s), np.float32)


def hx(c):
    return "#%02x%02x%02x" % tuple(int(max(0, min(255, v))) for v in c[:3])


def vnoise(w, h, seed, cells=((8, 0.5), (16, 0.3), (32, 0.2)), wrap_x=True, wrap_y=True):
    """Value noise in [0, 1], the sum of bilinear grids `cells` across (tileable when wrapped)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    for n, wt in cells:
        gx, gy = max(1, n), max(1, int(round(n * h / w)))
        g = rng.random((gy + 1, gx + 1)).astype(np.float32)
        if wrap_x:
            g[:, -1] = g[:, 0]
        if wrap_y:
            g[-1, :] = g[0, :]
        xs = np.linspace(0, gx, w, endpoint=False)
        ys = np.linspace(0, gy, h, endpoint=False)
        x0, y0 = xs.astype(int), ys.astype(int)
        fx, fy = (xs - x0)[None, :], (ys - y0)[:, None]
        a = g[y0][:, x0]
        b = g[y0][:, x0 + 1]
        c = g[y0 + 1][:, x0]
        d = g[y0 + 1][:, x0 + 1]
        out += wt * (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy)
    return np.clip(out / sum(wt for _, wt in cells), 0, 1)


def _bayer(h, w, ox=0, oy=0, cell=1):
    b = np.kron(BAYER4, np.ones((cell, cell), np.float32)) if cell > 1 else BAYER4
    n = 4 * cell
    th = np.tile(b, (h // n + 1, w // n + 1))[:h, :w]
    return np.roll(np.roll(th, oy, 0), ox, 1)


def ramp(v, cols, ox=0, oy=0, cell=1):
    """Map v (H x W in [0, 1]) onto the colour ramp `cols` with an ordered dither between neighbouring steps (no smooth blends: style guide section 1)."""
    pal = np.stack([hexa(c) for c in cols])
    v = np.atleast_2d(v)
    h, w = v.shape
    t = np.clip(v, 0, 1) * (len(cols) - 1)
    i = np.floor(t).astype(int)
    f = t - i
    i = np.clip(i + (f > _bayer(h, w, ox, oy, cell)), 0, len(cols) - 1)
    return pal[i]


def mix_dither(arr, mask_w, col, ox=0, oy=0, k=0.65, cell=1):
    """Glaze `col` into arr where the weight mask_w (0..1) beats the Bayer threshold (in place, returns arr). `cell` 2 dithers in 2 x 2 texel blocks: a floor seen at a
    grazing angle with nearest sampling and no mipmaps turns a 1-texel checker into grain, a 2-texel one survives (stage D polish: the Dock's gloss grain)."""
    h, w = mask_w.shape
    sel = mask_w > _bayer(h, w, ox, oy, cell)
    arr[sel] = arr[sel] * (1 - k) + hexa(col) * k
    return arr


def to_img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def wet_gloss(arr, seed, cols=("#e09040", "#4a68d0", "#c04a3a"), n=8, length=(60, 180), width=(3, 9), ripples=6, sheen="#8a96c0", cell=2):
    """Wet floor gloss baked in: vertical smears of light that fade from their bright end (the lamps' reflections), a solid bright core and a dithered fringe, small ripple
    rings, and a cool sheen in the low spots. In place on the H x W x 3 array; it wraps, so the tile stays tileable. The dither runs in `cell` x `cell` blocks and the rings are
    two texels wide, so the floor does not break into grain at mid distance (nearest sampling, no mipmaps)."""
    rng = np.random.default_rng(seed)
    h, w, _ = arr.shape
    yy, xx = np.indices((h, w))
    for _ in range(n):
        x0, y0 = rng.integers(w), rng.integers(h)
        ln, wd = rng.integers(*length), rng.integers(*width)
        col = cols[rng.integers(len(cols))]
        dx = (xx - x0 + w // 2) % w - w // 2
        dy = (yy - y0) % h
        k = np.where((np.abs(dx) <= wd) & (dy < ln), (1 - dy / ln) * (1 - np.abs(dx) / (wd + 1)) * 0.8, 0)
        core = k > 0.42
        arr[core] = arr[core] * 0.55 + hexa(col) * 0.45
        mix_dither(arr, np.where(core, 0, k * 1.6), col, k=0.4, cell=cell)
    for _ in range(ripples):
        cx, cy, r = rng.integers(w), rng.integers(h), rng.integers(5, 12)
        dx = (xx - cx + w // 2) % w - w // 2
        dy = ((yy - cy + h // 2) % h - h // 2) * 2.2
        d = np.sqrt(dx * dx + dy * dy)
        ring = np.abs(d - r) < 1.2
        arr[ring] = arr[ring] * 0.6 + hexa(sheen) * 0.4
    low = vnoise(w, h, seed + 7, ((4, 0.6), (8, 0.4)))
    mix_dither(arr, np.clip((low - 0.62) * 2.2, 0, 0.55), sheen, k=0.4, cell=cell)
    return arr

def brick_tile(seed, base=("#4a1e18", "#662a24", "#7c342a", "#904234"), mortar=("#24140f", "#3a2a22", "#4a3a30"), wet=1.0):
    """Red brick at 128 texels per metre (a brick 0.22 x 0.07 m = 28 x 9 px): each brick its own tone and grain, mortar of varying depth, soot, and rain streaks down the face."""
    rng = np.random.default_rng(seed)
    arr = ramp(vnoise(T, T, seed + 2, ((32, 1.0),)) * 0.6 + 0.2, mortar)
    grain = vnoise(T, T, seed, ((16, 0.3), (64, 0.7)))
    big = vnoise(T, T, seed + 1, ((2, 0.5), (4, 0.5)))
    for row in range(0, T - 8, 9):
        off = 0 if (row // 9) % 2 == 0 else 14
        for x in range(-off, T, 28):
            t = float(np.clip(rng.normal(0.55, 0.18) + (big[row, x % T] - 0.5) * 0.6, 0.05, 0.98))
            xs = np.arange(x + 1, x + 27) % T
            ys = np.arange(row + 1, row + 8)
            v = np.clip(t + (grain[np.ix_(ys, xs)] - 0.5) * 0.45, 0, 1)
            arr[np.ix_(ys, xs)] = ramp(v, base, x, row)
    soot = vnoise(T, T, seed + 3, ((3, 0.6), (6, 0.4)))
    mix_dither(arr, np.clip((soot - 0.55) * 1.6, 0, 0.6), "#1c1012", k=0.5)
    yy, xx = np.indices((T, T))
    for _ in range(int(16 * wet)):
        x0, y0, ln = rng.integers(T), rng.integers(T), rng.integers(20, 90)
        mix_dither(arr, np.where((xx == x0) & ((yy - y0) % T < ln), 0.7, 0), "#9a8aa8", k=0.5)
    return arr


def tower_tile(seed, lit=0.12, base=("#0e1224", "#242c46", "#38466a", "#52648e"), win_lit=("#e0a448", "#ffc068", "#c88a3a", "#9ac0e8"), floor_h=24, bay_w=20):
    """A dark tower face: concrete bands and dark glass in a grid with only a few windows lit (the paintings' dark towers); a lit window is a dithered glow with a curtain line."""
    rng = np.random.default_rng(seed)
    arr = ramp(vnoise(T, T, seed, ((8, 0.4), (32, 0.6))) * 0.55 + 0.15, base)
    for y in range(4, T - floor_h + 1, floor_h):
        arr[y + floor_h - 4:y + floor_h - 2, :] = arr[y + floor_h - 4:y + floor_h - 2, :] * 0.6 + hexa("#2e3a58") * 0.4
        for x in range(3, T - bay_w + 1, bay_w):
            win = arr[y:y + floor_h - 7, x:x + bay_w - 6]
            if rng.random() < lit:
                c = hexc(win_lit[rng.integers(len(win_lit))])
                v = np.full(win.shape[:2], 0.35 + rng.random() * 0.4) + vnoise(win.shape[1], win.shape[0], int(rng.integers(1 << 30)), ((2, 1.0),), False, False) * 0.3
                win[:] = ramp(v, (hx(shade(c, 0.5)), hx(c), hx(shade(c, 1.2))))
                win[:, int(rng.integers(2, bay_w - 8))] *= 0.55
            else:
                win[:] = win * 0.45 + hexa("#0a0e1c") * 0.55
                win[0, :] = win[0, :] * 0.6 + hexa("#3a4a6a") * 0.4
    yy, xx = np.indices((T, T))
    for _ in range(14):
        x0, y0, ln = rng.integers(T), rng.integers(T), rng.integers(30, 110)
        mix_dither(arr, np.where((xx == x0) & ((yy - y0) % T < ln), 0.6, 0), "#4a5a88", k=0.4)
    return arr


def conc_tile(seed, base=("#2c2c38", "#3a3a48", "#4a4a5a", "#5a5a6c"), joints=128, gloss=True, gloss_cols=("#e09040", "#4a68d0", "#c04a3a")):
    """Wet concrete slabs (joints every `joints` px, stains) with puddle gloss baked in."""
    arr = ramp(vnoise(T, T, seed, ((3, 0.4), (8, 0.4), (24, 0.2))) * 0.75 + 0.15, base, cell=2)
    for k in range(0, T, joints):
        arr[k:k + 2, :] *= 0.45
        arr[:, k:k + 2] *= 0.45
    stain = vnoise(T, T, seed + 5, ((3, 0.5), (6, 0.5)))
    mix_dither(arr, np.clip((stain - 0.6) * 1.8, 0, 0.6), "#141418", k=0.5, cell=2)
    if gloss:
        wet_gloss(arr, seed + 9, gloss_cols)
    return arr


def sky_strip(seed, W=1024, H=256, hz=0.76, clouds=("#0a0c22", "#141634", "#201f46", "#30295a", "#463a74", "#62508e"), glow=None, skyline=None, moon=None, beams=(), stars=0, lift=0.0):
    """A storm sky strip for the map's `sky` (StoryWorld wraps a 1024-wide strip once round the horizon, row hz x H at eye level): cloud banks in a dithered ramp, lifted by the
    city's glow toward the horizon; optionally a moon with a halo, searchlight beams, and a skyline standing on the horizon row (dark towers, sparse lit windows, red mast lamps)."""
    rng = np.random.default_rng(seed)
    hzr = int(H * hz)
    v = vnoise(W, H, seed, ((6, 0.35), (16, 0.35), (48, 0.2), (128, 0.1)), True, False)
    yy, xx = np.indices((H, W))
    v = np.clip((v - 0.25) * 1.3 + np.clip((yy / max(1, hzr)) ** 1.6, 0, 1) * 0.35 + lift, 0, 1)
    arr = ramp(v, clouds)
    if glow:
        mix_dither(arr, np.clip((yy - hzr * 0.55) / (hzr * 0.6), 0, 0.5) * vnoise(W, H, seed + 3, ((8, 1.0),), True, False), glow, k=0.45)
    for _ in range(stars):
        x, y = int(rng.integers(W)), int(rng.integers(0, hzr // 2))
        if v[y, x] < 0.3:
            arr[y, x] = hexa("#c8d0f0")
    if moon:
        mx, my, r = moon
        d = np.sqrt((xx - mx) ** 2 + (yy - my) ** 2)
        mix_dither(arr, np.clip(1 - (d - r) / (r * 3.5), 0, 0.6) * (d > r), "#6a88c0", k=0.5)
        disc = d <= r
        mv = vnoise(W, H, seed + 11, ((64, 0.5), (128, 0.5)), True, False)
        arr[disc] = ramp(np.clip(0.75 + (mv[disc] - 0.5) * 0.6 - (xx[disc] - mx) / (r * 6), 0, 1)[None, :], ("#7a90b8", "#b8c8e0", "#e0e8f4"))[0]
        cl = disc & (v > 0.62)
        arr[cl] = arr[cl] * 0.5 + hexa("#4a5a88") * 0.5
    for bx, ang, wd in beams:
        t = (hzr - yy) / max(1, hzr)
        cx = bx + t * hzr * np.tan(np.radians(ang))
        k = np.clip(1 - np.abs(xx - cx) / (wd * (0.3 + t)), 0, 1) * np.clip(1 - t, 0, 1) * (yy < hzr) * 0.6
        mix_dither(arr, k, "#9ab8f0", k=0.4)
    if skyline:
        wins = skyline.get("win", ("#e0a448", "#ffc068", "#a8c8ff", "#d070ff"))
        for col, hmin, hmax, lit in skyline.get("layers", (("#1a1e38", 18, 60, 0.05), ("#10142a", 30, 110, 0.08), ("#090b1a", 40, 150, 0.1))):
            x = int(rng.integers(0, 20))
            while x < W:
                bw, bh = int(rng.integers(14, 46)), int(rng.integers(hmin, hmax))
                top = max(12, hzr - bh)
                xs = np.arange(x, x + bw) % W
                arr[top:, xs] = ramp(vnoise(bw, H - top, int(rng.integers(1 << 30)), ((2, 0.5), (8, 0.5)), False, False) * 0.4 + 0.3, (col, hx(shade(hexc(col), 1.35))))
                for wy in range(top + 4, H, 6):
                    for wx in range(x + 2, x + bw - 2, 4):
                        if rng.random() < lit:
                            arr[wy:wy + 2, wx % W:(wx % W) + 2] = hexa(wins[rng.integers(len(wins))])
                if bh > hmax * 0.7 and rng.random() < 0.6:
                    m_ = (x + bw // 2) % W
                    arr[top - 8:top, m_] = hexa(col)
                    arr[top - 10:top - 8, m_:m_ + 2] = hexa("#ff2a20")
                x += bw + int(rng.integers(0, 10))
        arr[hzr:] = arr[hzr:] * 0.75 + hexa(skyline.get("street", "#1a1428")) * 0.25
    return arr


# --- the Dock's polished tiles and props -------------------------------------------------------------------------------------------------------------------------------

def p_wall_brick(seed=301):
    return to_img(brick_tile(seed))


def p_wall_tower(seed=311, lit=0.15):
    return to_img(tower_tile(seed, lit))


def p_wall_ware():
    """The brown warehouse across the street: stained render, big industrial windows (some lit), rain streaks, at 128 texels per metre."""
    rng = np.random.default_rng(321)
    arr = ramp(vnoise(T, T, 321, ((4, 0.4), (32, 0.6))) * 0.6 + 0.2, ("#221a14", "#2e241c", "#3e3226", "#4c3e30"))
    for y in range(0, T, 32):
        arr[y:y + 1, :] *= 0.6
    for x in (14, 142):
        for y in (40, 150):
            lit = rng.random() < 0.6
            v = vnoise(100, 60, int(rng.integers(1 << 30)), ((3, 1.0),), False, False) * 0.5 + (0.45 if lit else 0.0)
            arr[y:y + 60, x:x + 100] = ramp(v, ("#0e0c0e", "#1a1614", "#8a5a28", "#e0a048", "#ffd080") if lit else ("#0a0a0e", "#16161c", "#222230"))
            arr[y:y + 60:15, x:x + 100] *= 0.5
            arr[y:y + 60, x:x + 100:25] *= 0.5
    yy, xx = np.indices((T, T))
    for _ in range(18):
        x0, y0, ln = rng.integers(T), rng.integers(T), rng.integers(30, 120)
        mix_dither(arr, np.where((xx == x0) & ((yy - y0) % T < ln), 0.6, 0), "#6a6a80", k=0.4)
    return to_img(arr)


def p_floor_conc():
    """The apron: wet concrete slabs, the yellow edge stripe (worn), the lamps' long reflections and ripples."""
    arr = conc_tile(331, gloss_cols=("#f0a048", "#e09040", "#4a68d0", "#d05a3a"))
    wear = vnoise(T, T, 332, ((16, 0.5), (64, 0.5)))
    sel = np.zeros((T, T), bool)
    sel[200:224, :] = True
    sel &= wear > 0.3
    arr[sel] = ramp(wear[sel][None, :], ("#6a5418", "#a8821e", "#d0a830"))[0]
    return to_img(arr)


def p_floor_asphalt(base=("#222232", "#363650", "#4a4a68", "#5e5e84")):
    """The street: wet asphalt in broad low-frequency patches (no fine sparkle: it aliases into confetti at distance), sparse grit, a worn lane dash, the sodium and blue lamps'
    long smeared reflections, a few ripples."""
    rng = np.random.default_rng(343)
    arr = ramp(vnoise(T, T, 341, ((3, 0.4), (8, 0.4), (24, 0.2))) * 0.8 + 0.1, base, cell=2)
    g = np.kron(rng.random((T // 2, T // 2)) < 0.02, np.ones((2, 2), bool))
    arr[g] = arr[g] * 0.6 + hexa("#4a4a5c") * 0.4
    arr[20:80, 120:132] = arr[20:80, 120:132] * 0.4 + hexa("#6a6a72") * 0.6
    wet_gloss(arr, 342, ("#ffb858", "#f09a48", "#6080f0", "#d85a4a", "#ffc068"), n=13, length=(90, 220), width=(3, 10), ripples=6)
    return to_img(arr)


def p_floor_walk():
    return to_img(conc_tile(351, base=("#1e1c24", "#2c2a34", "#3a3842", "#48464e"), joints=64, gloss_cols=("#e09040", "#3a60ff", "#3a60ff")))


def p_sky():
    """The Dock's storm sky: violet-lit cloud banks over the city, and far tower tops on the horizon."""
    return to_img(sky_strip(361, clouds=("#1a1838", "#24224c", "#302c60", "#403878", "#564a92", "#7462b0"), glow="#8a6ac0", lift=0.04,
                            skyline={"layers": (("#2a2c4c", 8, 26, 0.05), ("#1e2240", 12, 38, 0.08)), "street": "#141020"}))


def p_bollard():
    """A steel bollard (1.1 m at 128 texels per metre): rounded cap, rust, the yellow band, the wet highlight on the lit side, dithered."""
    w, h = 36, 140
    xx = np.arange(w)[None, :].repeat(h, 0)
    v = np.clip(0.85 - np.abs(xx - 11) / 22.0, 0, 1) * 0.9 + vnoise(w, h, 371, ((4, 0.5), (16, 0.5)), False, False) * 0.2
    arr = ramp(v, ("#2a2628", "#4a4446", "#6a6466", "#8e888a", "#c0bcc0"))
    arr[48:66] = ramp(v[48:66], ("#5a4410", "#a07c18", "#d8a828", "#f0c848"))
    mix_dither(arr, np.clip((vnoise(w, h, 372, ((8, 0.5), (32, 0.5)), False, False) - 0.55) * 2, 0, 0.7), "#7a4220", k=0.55)
    im = to_img(arr).convert("RGBA")
    a = np.full((h, w), 255, np.uint8)
    for y in range(8):
        r = int(np.sqrt(max(0, 64 - (8 - y) ** 2)) * w / 16)
        a[y, :max(0, w // 2 - r)] = 0
        a[y, min(w, w // 2 + r):] = 0
    im.putalpha(Image.fromarray(a))
    return outline(im)


def p_furnace():
    """The domed boiler: riveted rust plates, a fire mouth glowing in dithered steps, smoke from its stack."""
    W_, H_ = 240, 240
    dome = Image.new("L", (W_, H_), 0)
    dd = ImageDraw.Draw(dome)
    dd.ellipse([20, 50, 230, 250], fill=255)
    dd.rectangle([20, 150, 230, 239], fill=255)
    dd.rectangle([168, 0, 194, 100], fill=255)
    xx = np.arange(W_)[None, :].repeat(H_, 0)
    v = np.clip(vnoise(W_, H_, 381, ((6, 0.4), (24, 0.6)), False, False) * 0.5 + (1 - np.abs(xx - 90) / 160) * 0.5, 0, 1)
    arr = ramp(v, ("#1c0e0a", "#3a1e14", "#5a3020", "#7a4428", "#9a5a30"))
    for y in range(60, 236, 22):
        arr[y:y + 1, :] *= 0.55
        arr[y + 3, ::14] = hexa("#c08050")
    yy, xx2 = np.indices((H_, W_))
    dm = np.sqrt(((xx2 - 125) / 52.0) ** 2 + ((yy - 182) / 46.0) ** 2)
    m = dm < 1
    arr[m] = ramp((np.clip(1 - dm[m], 0, 1) ** 0.7)[None, :], ("#a02a10", "#ff6a1a", "#ffb040", "#ffe490", "#fff8d8"))[0]
    rim = (dm >= 1) & (dm < 1.25)
    arr[rim] = arr[rim] * 0.4 + hexa("#ff7a20") * 0.6
    mix_dither(arr, np.where((dm >= 1.25) & (dm < 2.2), (2.2 - dm) / 0.95 * 0.55, 0), "#ff8a30", k=0.5)
    im = to_img(arr).convert("RGBA")
    im.putalpha(dome)
    smoke = vnoise(80, 100, 382, ((3, 0.5), (8, 0.5)), False, False)
    sm = to_img(ramp(smoke, ("#3a3448", "#5a5468", "#7a7488"))).convert("RGBA")
    a = ((smoke > 0.5) & (np.linspace(1, 0, 100)[:, None] > _bayer(100, 80))).astype(np.uint8) * 255
    sm.putalpha(Image.fromarray(a))
    out, _ = canvas(W_, H_ + 90)
    out.paste(sm, (140, 0), sm)
    out.paste(im, (0, 90), im)
    return outline(out)


def p_end_glow():
    """The far end of the club passage: the dance floor through an open door, blue, violet and magenta beams, the crowd's heads against them (emissive)."""
    W_, H_ = 256, 256
    arr = ramp(vnoise(W_, H_, 391, ((4, 0.5), (16, 0.5)), False, False) * 0.5 + 0.25, ("#0a0c2a", "#141a50", "#22308a", "#3a50c8"))
    yy, xx = np.indices((H_, W_))
    for bx, ang, col in ((60, 18, "#8a60ff"), (190, -22, "#ff4fb0"), (128, 5, "#5a9aff")):
        cx = bx + yy * np.tan(np.radians(ang))
        mix_dither(arr, np.clip(1 - np.abs(xx - cx) / (8 + yy * 0.12), 0, 1) * 0.8, col)
    rng = np.random.default_rng(392)
    for _ in range(26):
        x, y, r = int(rng.integers(0, W_)), int(rng.integers(170, 215)), int(rng.integers(7, 11))
        arr[np.sqrt((xx - x) ** 2 + (yy - y) ** 2) < r] = hexa("#0c0a1c")
        arr[(np.abs(xx - x) < r * 2) & (yy > y + r - 2)] = hexa("#0c0a1c")
    arr[:, :10] = arr[:, -10:] = hexa("#2a2e3c")
    arr[:12, :] = hexa("#2a2e3c")
    return to_img(arr)


def p_crate_drum():
    """The Underworld guide's seat: stacked crates with the hand drum on them (1.1 m)."""
    out, d = canvas(140, 150)
    im = crate().resize((128, 112), Image.NEAREST)
    out.paste(im, (6, 38), im)
    dr = drum().resize((84, 72), Image.NEAREST)
    out.paste(dr, (40, 0), dr)
    return out


def p_pallets_near():
    """The foreground pallets (a stack with a flight case against it), the painting's right edge: 1.2 m tall."""
    out, d = canvas(220, 156)
    ps = pallet_stack().resize((150, 156), Image.NEAREST)
    out.paste(ps, (0, 0), ps)
    c = mb.case().resize((110, 96), Image.NEAREST)
    out.paste(c, (108, 60), c)
    return out

TEXTURES = {"dk_wall_brick": wall_brick, "dk_wall_tower": wall_tower, "dk_wall_ware": wall_ware, "dk_wall_shutter": wall_shutter, "dk_wall_steel": wall_steel, "dk_wall_blue": wall_blue,
            "dk_floor_conc": floor_conc, "dk_floor_asphalt": floor_asphalt, "dk_floor_walk": floor_walk, "dk_floor_blue": floor_blue, "dk_ceil_sky": ceil_sky, "dk_ceil_truss": ceil_truss,
            "dk_trim": trim}
PROPS = {"dk_bollard": bollard, "dk_pallet": pallet, "dk_pallet_stack": pallet_stack, "dk_crate": crate, "dk_van": van, "dk_case": case_big, "dk_furnace": furnace,
         "dk_street_lamp": street_lamp, "dk_wall_lamp": wall_lamp, "dk_hang_lamp": hang_lamp, "dk_chain": chain, "dk_drum": drum}
DECALS = {"dk_door_leaf": door_leaf, "dk_clef": clef, "dk_pipe_vert": pipe_vert, "dk_pipes_yard": pipes_yard, "dk_fence": fence, "dk_windows_lit": windows_lit, "dk_neon_blue": neon_blue,
          "dk_shutter": shutter_big, "dk_towers": towers}


# stage D polish: 256 px tiles (128 texels per metre), three tower faces and two brick faces so no wall repeats its neighbour, the sky strip, the new props
TEXTURES.update({"dk_wall_brick": p_wall_brick, "dk_wall_brick_b": lambda: p_wall_brick(302), "dk_wall_tower": p_wall_tower, "dk_wall_tower_b": lambda: p_wall_tower(312, 0.13),
                 "dk_wall_tower_c": lambda: p_wall_tower(313, 0.17), "dk_wall_ware": p_wall_ware, "dk_floor_conc": p_floor_conc, "dk_floor_asphalt": p_floor_asphalt,
                 "dk_floor_walk": p_floor_walk, "dk_sky": p_sky})
PROPS.update({"dk_bollard": p_bollard, "dk_furnace": p_furnace, "dk_crate_drum": p_crate_drum, "dk_pallets_near": p_pallets_near})
DECALS.update({"dk_end_glow": p_end_glow})




# --- round 2 (docs/briefs/DOOM_POLISH_ROUND2_BRIEF.md, Dock): the near walls are brick and corrugated steel, the far buildings dark facades with FEW lit windows as decals placed
# one by one (no window grid in a tile, so nothing repeats every 2 m), a silhouette skyline in the sky strip, the brown building at the street's end with its lit doorway, and the club
# passage as a dark brick tunnel to a violet-lit door

def p_wall_bldg(seed, base=("#0c0e1a", "#151826", "#1e2234", "#2a3044")):
    """A dark city facade (2 m tile, no windows: they are decals): stained concrete in broad patches, one floor slab line, soot runs and rain streaks."""
    rng = np.random.default_rng(seed)
    arr = ramp(vnoise(T, T, seed, ((2, 0.4), (6, 0.35), (24, 0.25))) * 0.7 + 0.15, base, cell=2)
    arr[176:182, :] = arr[176:182, :] * 0.55 + hexa("#2a3048") * 0.45
    arr[182:184, :] *= 0.5
    yy, xx = np.indices((T, T))
    for _ in range(10):
        x0, y0, ln, wd = rng.integers(T), rng.integers(T), rng.integers(60, 200), rng.integers(2, 6)
        mix_dither(arr, np.where((np.abs((xx - x0 + T // 2) % T - T // 2) < wd) & ((yy - y0) % T < ln), 0.45, 0), "#07080e", k=0.5, cell=2)
    for _ in range(12):
        x0, y0, ln = rng.integers(T), rng.integers(T), rng.integers(30, 110)
        mix_dither(arr, np.where((xx == x0) & ((yy - y0) % T < ln), 0.6, 0), "#3a4466", k=0.4)
    return to_img(arr)


def p_wall_corr(seed=411):
    """Corrugated steel cladding (2 m tile): vertical ribs every 16 texels lit on one flank, rust blooms low down, rain streaks."""
    rng = np.random.default_rng(seed)
    xx = np.arange(T)[None, :].repeat(T, 0)
    rib = (np.sin(xx / 16.0 * 2 * np.pi) * 0.5 + 0.5) * 0.45
    v = np.clip(rib + vnoise(T, T, seed, ((4, 0.5), (16, 0.5))) * 0.4 + 0.05, 0, 1)
    arr = ramp(v, ("#14161e", "#22262f", "#323743", "#454b58", "#5c6370"), cell=2)
    yy = np.indices((T, T))[0]
    rust_w = np.clip((vnoise(T, T, seed + 1, ((3, 0.5), (12, 0.5))) - 0.5) * 2.0 + (yy / T - 0.6), 0, 0.7)
    mix_dither(arr, rust_w, "#6a3418", k=0.5, cell=2)
    for _ in range(14):
        x0, y0, ln = rng.integers(T), rng.integers(T), rng.integers(40, 140)
        mix_dither(arr, np.where((xx == x0) & ((yy - y0) % T < ln), 0.6, 0), "#7480a0", k=0.4)
    arr[0:3, :] *= 0.5
    return to_img(arr)


def p_wall_brown(seed=421):
    """The brown building at the street's end (the painting's): stained render in broad patches, a string course, rain streaks; its windows and lit door are decals."""
    return p_wall_bldg(seed, base=("#24180f", "#342418", "#463222", "#5a422e"))


def p_wall_tunnel(seed=431):
    """The club passage: dark sooty brick (the Dock's brick tile, darker and cooler), wet."""
    arr = brick_tile(seed, base=("#3e1e16", "#562c20", "#6c3a2a", "#844a36"), mortar=("#1a1010", "#281c18", "#382a22"), wet=0.3)
    return to_img(arr)


def p_ceil_tunnel(seed=432):
    """The passage's ceiling: dark sooty concrete with a cable run and damp stains (no grid: the old truss tile read as a lattice overhead)."""
    arr = ramp(vnoise(T, T, seed, ((3, 0.5), (12, 0.5))) * 0.6 + 0.15, ("#060508", "#0c0a10", "#141018", "#1c1620"), cell=2)
    arr[120:126, :] = hexa("#1a1a20")
    arr[121:123, :] = hexa("#3a3a44")
    return to_img(arr)


def p_window(lit, seed, w=96, h=128):
    """One window (decal; 0.75 x 1.0 m at size 1.0): a dark frame and sill, the glass lit (a warm or cold dithered glow, a curtain edge, a mullion) or dark (a cold sheen)."""
    rng = np.random.default_rng(seed)
    arr = ramp(vnoise(w, h, seed, ((2, 0.5), (6, 0.5)), False, False) * 0.4 + 0.2, ("#0a0a10", "#14141c", "#20202a"))
    g = (slice(8, h - 14), slice(8, w - 8))
    gh, gw = h - 22, w - 16
    if lit:
        c = hexc(lit)
        v = np.clip(vnoise(gw, gh, seed + 1, ((2, 0.6), (4, 0.4)), False, False) * 0.5 + np.linspace(0.45, 0.85, gh)[:, None], 0, 1)
        arr[g] = ramp(v, (hx(shade(c, 0.35)), hx(shade(c, 0.7)), hx(c), hx(shade(c, 1.25))))
        cx = int(rng.integers(gw // 3, 2 * gw // 3))
        arr[8:h - 14, 8 + cx:8 + cx + 3] *= 0.4
        arr[8:h - 14, 8:8 + int(rng.integers(6, 20))] *= 0.45
    else:
        v = np.clip(vnoise(gw, gh, seed + 2, ((2, 0.6), (6, 0.4)), False, False) * 0.5 + np.linspace(0.5, 0.1, gh)[:, None] * 0.5, 0, 1)
        arr[g] = ramp(v, ("#06070e", "#0e1220", "#1a2234", "#2a3650"))
        arr[8:h - 14, w // 2 - 1:w // 2 + 2] *= 0.5
    arr[h - 14:h - 8, 4:w - 4] = hexa("#3a3a44")
    im = to_img(arr).convert("RGBA")
    a = np.zeros((h, w), np.uint8)
    a[2:h - 6, 2:w - 2] = 255
    im.putalpha(Image.fromarray(a))
    return im


def p_far_door():
    """The lit doorway at the street's end (decal, 2.6 m tall): a recessed warm-lit opening, a steel frame, a caged lamp over it and its glow on the
    wet render; emissive."""
    W_, H_ = 208, 336
    yy, xx = np.indices((H_, W_))
    d = np.sqrt(((xx - W_ / 2) / 90.0) ** 2 + ((yy - 40) / 70.0) ** 2)
    glow = np.clip(1.2 - d, 0, 1) * 0.8
    arr = ramp(np.clip(glow, 0, 1), ("#1a120c", "#3a2410", "#6a4018", "#b07028"))
    ox0, ox1, oy0 = 44, W_ - 44, 96
    v = np.clip(np.linspace(1.0, 0.55, H_ - oy0)[:, None] + vnoise(ox1 - ox0, H_ - oy0, 441, ((2, 0.5), (5, 0.5)), False, False) * 0.25 - 0.1, 0, 1)
    arr[oy0:, ox0:ox1] = ramp(v, ("#5a3010", "#a86020", "#e09a40", "#ffd080", "#fff0c8"))
    arr[oy0 - 6:oy0, ox0 - 8:ox1 + 8] = hexa("#2a2a30")
    arr[oy0:, ox0 - 8:ox0] = hexa("#2a2a30")
    arr[oy0:, ox1:ox1 + 8] = hexa("#2a2a30")
    arr[H_ - 6:, :] = hexa("#5a5a60")
    arr[30:50, W_ // 2 - 10:W_ // 2 + 10] = ramp(np.full((20, 20), 0.9), ("#ffb050", "#fff0b0"))
    arr[28:30, W_ // 2 - 14:W_ // 2 + 14] = hexa("#202020")
    im = to_img(arr).convert("RGBA")
    a = np.full((H_, W_), 255, np.uint8)
    a[:oy0 - 6] = np.where(glow[:oy0 - 6] > _bayer(oy0 - 6, W_), 255, 0)
    a[28:50, W_ // 2 - 14:W_ // 2 + 14] = 255
    im.putalpha(Image.fromarray(a))
    return im


def p_violet_door():
    """The end of the club passage (decal, 2.6 m): a door open on violet light, a dark steel frame in the brick, the light's spill dithered round it; emissive."""
    W_, H_ = 320, 336
    yy, xx = np.indices((H_, W_))
    d = np.sqrt(((xx - W_ / 2) / 150.0) ** 2 + ((yy - 200) / 170.0) ** 2)
    arr = ramp(np.clip(1.1 - d, 0, 1) * 0.7, ("#120c16", "#24143a", "#3c1e66", "#5a2c98"))
    ox0, ox1, oy0 = 84, W_ - 84, 70
    v = np.clip(1.0 - np.abs(np.linspace(-1, 1, ox1 - ox0))[None, :] * 0.5 + vnoise(ox1 - ox0, H_ - oy0, 451, ((2, 0.5), (6, 0.5)), False, False) * 0.2
                - np.linspace(0, 0.35, H_ - oy0)[:, None], 0, 1)
    arr[oy0:, ox0:ox1] = ramp(v, ("#2a1048", "#5a26a0", "#9a50f0", "#d0a0ff", "#f4e4ff"))
    arr[oy0 - 8:oy0, ox0 - 10:ox1 + 10] = hexa("#1a1820")
    arr[oy0:, ox0 - 10:ox0] = hexa("#1a1820")
    arr[oy0:, ox1:ox1 + 10] = hexa("#1a1820")
    arr[oy0 - 30:oy0 - 18, W_ // 2 - 24:W_ // 2 + 24] = ramp(np.full((12, 48), 0.85), ("#a060ff", "#f0d8ff"))
    im = to_img(arr).convert("RGBA")
    a = np.where(np.clip(1.1 - d, 0, 1) * 1.3 > _bayer(H_, W_), 255, 0).astype(np.uint8)
    a[oy0 - 30:, ox0 - 10:ox1 + 10] = 255
    im.putalpha(Image.fromarray(a))
    return im


def p_sky2():
    """Round 2: the storm sky over a SILHOUETTE skyline (the painting's dark mid-rise and towers, a few lit windows), so the city is the sky behind the near walls, not a tile on them."""
    return to_img(sky_strip(362, clouds=("#0a0a1c", "#100f28", "#181636", "#221e48", "#30295e", "#423878"), glow="#5a4490", lift=0.0,
                            skyline={"layers": (("#1e1c3a", 26, 70, 0.025), ("#151530", 40, 110, 0.035), ("#0d0d22", 34, 90, 0.03)),
                                     "win": ("#e0a448", "#ffc068", "#c88a3a", "#9ac0e8"), "street": "#120e1c"}))


TEXTURES.update({"dk_wall_bldg_a": lambda: p_wall_bldg(401), "dk_wall_bldg_b": lambda: p_wall_bldg(402, ("#0e0e18", "#181a26", "#242636", "#30344a")),
                 "dk_wall_bldg_c": lambda: p_wall_bldg(403, ("#100c16", "#1a1624", "#262034", "#322a44")), "dk_wall_corr": p_wall_corr,
                 "dk_wall_corr_b": lambda: p_wall_corr(412), "dk_wall_brown_a": p_wall_brown, "dk_wall_brown_b": lambda: p_wall_brown(422),
                 "dk_floor_asphalt": lambda: p_floor_asphalt(("#282838", "#3e3e5a", "#545474", "#6a6a92")),  # round 2: a little lighter (the exposure rule)
                 "dk_wall_tunnel": p_wall_tunnel, "dk_ceil_tunnel": p_ceil_tunnel, "dk_sky": p_sky2})
TEXTURES.update({"dk_wall_brick": lambda: to_img(brick_tile(301, base=("#56241c", "#723228", "#8a4032", "#a2503e"), mortar=("#2a1a14", "#3c2c24", "#4e3c32"))),
                 "dk_wall_brick_b": lambda: to_img(brick_tile(302, base=("#56241c", "#723228", "#8a4032", "#a2503e"), mortar=("#2a1a14", "#3c2c24", "#4e3c32")))})  # round 2: a lighter red (the exposure rule)
DECALS.update({"dk_win_amber": lambda: p_window("#ffb050", 461), "dk_win_amber_b": lambda: p_window("#e09040", 462), "dk_win_cold": lambda: p_window("#9ab8e8", 463),
               "dk_win_dark": lambda: p_window(None, 464), "dk_win_dark_b": lambda: p_window(None, 465), "dk_far_door": p_far_door, "dk_violet_door": p_violet_door})


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in {**TEXTURES, **PROPS, **DECALS}.items():
        fn().save(os.path.join(OUT, name + ".png"))
    import make_dock_guides as dg
    n = dg.main()
    print("wrote %d textures, %d props, %d decals and %d guide frames to %s" % (len(TEXTURES), len(PROPS), len(DECALS), n, OUT))


if __name__ == "__main__":
    sys.exit(main())
