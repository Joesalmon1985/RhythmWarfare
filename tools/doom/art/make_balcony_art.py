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


# --- stage D polish (docs/briefs/DOOM_POLISH_BRIEF.md): 256 px tiles (128 texels per metre) on the Dock's numpy helpers (ordered dither, tileable noise, wet gloss in 2 x 2
# blocks), the moon sky with the city's skyline, the alley's lit side door and the cabin's stairwell glow. The PIL tiles above stay for the props and decals not redrawn.
import make_dock_art as dk  # noqa: E402
import numpy as np  # noqa: E402

T = dk.T


def p_sky():
    """The painting's sky: a full moon in torn storm cloud (upper left of the view north), a searchlight beam, the violet-lit city skyline with red mast lamps on the horizon."""
    return dk.to_img(dk.sky_strip(461, clouds=("#060a18", "#0c1428", "#142038", "#1e2c4a", "#2c3c60", "#465a80"), glow="#3a4a90", lift=0.0, moon=(968, 132, 18),
                                  beams=((930, 20, 7), (120, -14, 6)), stars=0,
                                  skyline={"layers": (("#141c34", 20, 70, 0.10), ("#0c1226", 30, 110, 0.12), ("#070a18", 40, 150, 0.08)),
                                           "win": ("#e0a448", "#ffc068", "#5ad0ff", "#d070ff", "#ff5ab0"), "street": "#0a0c1a"}))


def p_wall_brick():
    return dk.to_img(dk.brick_tile(471, base=("#3a1814", "#62281f", "#7e362b", "#9c4636")))


def p_wall_brick_b():
    return dk.to_img(dk.brick_tile(472, base=("#3a1814", "#62281f", "#7e362b", "#9c4636")))


def p_wall_conc():
    """Rain-darkened concrete (the far roofs and the deck's parapet): board marks, stains, long rain streaks."""
    rng = np.random.default_rng(481)
    arr = dk.ramp(dk.vnoise(T, T, 481, ((3, 0.4), (12, 0.4), (40, 0.2))) * 0.7 + 0.15, ("#10141e", "#20283a", "#30394c", "#445066"), cell=2)
    for y in range(0, T, 64):
        arr[y:y + 2, :] *= 0.55
    yy, xx = np.indices((T, T))
    for _ in range(24):
        x0, y0, ln = rng.integers(T), rng.integers(T), rng.integers(30, 140)
        dk.mix_dither(arr, np.where((np.abs(xx - x0) < 1) & ((yy - y0) % T < ln), 0.6, 0), "#5a6680", k=0.4)
    return dk.to_img(arr)


def p_wall_steel():
    """Riveted steel plate, rust bleeding from the seams, wet sheen."""
    arr = dk.ramp(dk.vnoise(T, T, 491, ((4, 0.5), (16, 0.5))) * 0.6 + 0.2, ("#141820", "#20262e", "#2e3640", "#3e4854"), cell=2)
    for k in range(0, T, 64):
        arr[k:k + 2, :] = dk.hexa("#0a0c10")
        arr[:, k:k + 2] = dk.hexa("#0a0c10")
        for r in range(8, T, 16):
            arr[k + 4:k + 6, r:r + 2] = dk.hexa("#6a7280")
            arr[r:r + 2, k + 4:k + 6] = dk.hexa("#6a7280")
    rust = dk.vnoise(T, T, 492, ((6, 0.5), (24, 0.5)))
    dk.mix_dither(arr, np.clip((rust - 0.55) * 2.0, 0, 0.6), "#6a3418", k=0.5, cell=2)
    return dk.to_img(arr)


def p_wall_cabin():
    """The control cabin inside: warm-lit panelled wall with rack lights and cable trays."""
    arr = dk.ramp(dk.vnoise(T, T, 501, ((4, 0.5), (16, 0.5))) * 0.6 + 0.2, ("#24160c", "#4a3018", "#6e4824", "#9a6a38"), cell=2)
    for x in range(0, T, 64):
        arr[:, x:x + 2] = dk.hexa("#140c08")
    arr[40:44, :] = dk.hexa("#8a6a40")
    rng = np.random.default_rng(502)
    for _ in range(40):
        x, y = int(rng.integers(4, T - 4)), int(rng.integers(60, 200))
        arr[y:y + 2, x:x + 2] = dk.hexa(["#5aff9a", "#ff5a4a", "#ffc048", "#5ad0ff"][int(rng.integers(4))])
    return dk.to_img(arr)


def p_floor_wet():
    """The roof deck: wet diamond plate in big plates with welded seams, puddles that hold the cabin's amber, the window's violet and the red and cyan of the city (gloss in 2 x 2
    blocks), ripple rings from the rain."""
    arr = dk.ramp(dk.vnoise(T, T, 511, ((3, 0.4), (8, 0.4), (24, 0.2))) * 0.7 + 0.15, ("#141822", "#262e3e", "#384256", "#4e5a72"), cell=2)
    yy, xx = np.indices((T, T))
    dia = ((xx // 2 + yy // 2) % 8 == 0) & ((xx // 2 - yy // 2) % 8 == 4)
    arr[dia] = arr[dia] * 0.6 + dk.hexa("#6a7488") * 0.4
    for k in range(0, T, 128):
        arr[k:k + 2, :] *= 0.45
        arr[:, k:k + 2] *= 0.45
    dk.wet_gloss(arr, 512, ("#ff5ab0", "#5ad0ff", "#ff3a3a", "#ffa850", "#a060ff"), n=12, length=(70, 200), width=(3, 10), ripples=9, sheen="#4a5a88")
    return dk.to_img(arr)


def p_floor_stair():
    """Iron stair treads: chequer plate, a worn front edge catching the wall lamp, wet."""
    arr = dk.ramp(dk.vnoise(T, T, 521, ((4, 0.5), (16, 0.5))) * 0.6 + 0.2, ("#1a1414", "#2a201c", "#3a2c24", "#4e3a2e"), cell=2)
    yy, xx = np.indices((T, T))
    arr[((xx // 2) % 6 == 0) & ((yy // 2) % 6 == 3)] = dk.hexa("#6a5040")
    for k in range(0, T, 64):
        arr[k:k + 4, :] = dk.hexa("#a06a3a")
        arr[k + 4:k + 6, :] = dk.hexa("#0c0808")
    dk.wet_gloss(arr, 522, ("#ff8a40", "#ff5ab0"), n=5, length=(40, 100), width=(3, 7), ripples=3, sheen="#5a4a6a")
    return dk.to_img(arr)


def p_floor_grate():
    """The bridge's steel grating: a bar grid with the dark drop showing through, wet highlights on the bars."""
    arr = np.tile(dk.hexa("#06080e"), (T, T, 1)).astype(np.float32)
    yy, xx = np.indices((T, T))
    bars = (xx % 16 < 4) | (yy % 32 < 4)
    v = dk.vnoise(T, T, 531, ((8, 0.5), (32, 0.5)))
    arr[bars] = dk.ramp(v[bars][None, :] * 0.6 + 0.3, ("#1e242e", "#323a48", "#4a5466", "#6a7690"))[0]
    dk.mix_dither(arr, np.where(bars, np.clip((v - 0.6) * 2.5, 0, 0.8), 0), "#9ab0e0", k=0.5, cell=2)
    return dk.to_img(arr)


def p_floor_cabin():
    arr = dk.ramp(dk.vnoise(T, T, 541, ((4, 0.5), (16, 0.5))) * 0.6 + 0.2, ("#1e1612", "#2c2018", "#3c2c20", "#4e3a2a"), cell=2)
    for k in range(0, T, 64):
        arr[k:k + 2, :] *= 0.5
    dk.wet_gloss(arr, 542, ("#ffa850", "#ffc070"), n=5, length=(60, 140), width=(4, 9), ripples=0, sheen="#5a4030")
    return dk.to_img(arr)


def p_floor_alley():
    return dk.to_img(dk.conc_tile(551, base=("#14141c", "#1e1e2a", "#2a2a38", "#363646"), gloss_cols=("#ff8a40", "#ff5ab0", "#5ad0ff")))


def _door_glow(seed, cols, beams, frame="#2a2420"):
    """A lit doorway seen from outside (emissive): a frame, the light inside in a dithered ramp, a few beams."""
    W_, H_ = 128, 256
    arr = dk.ramp(dk.vnoise(W_, H_, seed, ((4, 0.5), (16, 0.5)), False, False) * 0.5 + 0.3, cols)
    yy, xx = np.indices((H_, W_))
    for bx, ang, col in beams:
        cx = bx + yy * np.tan(np.radians(ang))
        dk.mix_dither(arr, np.clip(1 - np.abs(xx - cx) / (6 + yy * 0.08), 0, 1) * 0.7, col)
    arr[:, :10] = dk.hexa(frame)
    arr[:, -10:] = dk.hexa(frame)
    arr[:14, :] = dk.hexa(frame)
    return arr


def p_alley_door():
    """The alley's end: the club's side door open on the dance floor (blue and magenta light, the Floor's way)."""
    return dk.to_img(_door_glow(561, ("#0a0c2a", "#18205a", "#2a3a9a", "#4a6ae0", "#8aa8ff"), ((40, 14, "#ff5ab0"), (90, -12, "#a070ff"))))


def p_stair_glow():
    """The cabin's back door: a warm-lit stairwell going down (the Booth's way), the treads as dark bars."""
    arr = _door_glow(571, ("#2a140a", "#5a3014", "#a05a20", "#e09040", "#ffd080"), ())
    for i, y in enumerate(range(120, 246, 18)):
        arr[y:y + 5, 10 + i * 6:118] *= 0.3
    return dk.to_img(arr)


def p_tower(seed=581, lit=0.16):
    """A building across the drop (billboard, 256 x 512): a dark concrete mass in floor bands with dark glass and a few lit windows (amber, a violet and a cyan one), a
    lit penthouse band, roof plant and a mast with a red lamp; the silhouette is its alpha."""
    from PIL import Image as _I
    W_, H_ = 256, 512
    rng = np.random.default_rng(seed)
    arr = np.zeros((H_, W_, 3), np.float32)
    top = 60
    body = dk.ramp(dk.vnoise(W_, H_ - top, seed, ((4, 0.4), (16, 0.6)), False, False) * 0.55 + 0.15, ("#0a0e1a", "#182032", "#262f46", "#36425e"), cell=2)
    arr[top:] = body
    for y in range(top + 30, H_ - 10, 22):
        arr[y + 16:y + 18, 12:W_ - 12] = dk.hexa("#2c3650")
        for x in range(18, W_ - 30, 18):
            if rng.random() < lit:
                c = ("#e0a448", "#ffc068", "#c88a3a", "#a070ff", "#5ad0ff")[int(rng.integers(5))]
                v = np.full((14, 12), 0.4 + rng.random() * 0.4) + dk.vnoise(12, 14, int(rng.integers(1 << 30)), ((2, 1.0),), False, False) * 0.3
                arr[y:y + 14, x:x + 12] = dk.ramp(v, (dk.hx(dk.shade(dk.hexc(c), 0.5)), c, dk.hx(dk.shade(dk.hexc(c), 1.25))))
            else:
                arr[y:y + 14, x:x + 12] = arr[y:y + 14, x:x + 12] * 0.5 + dk.hexa("#080a14") * 0.5
    arr[top + 4:top + 20, 20:W_ - 20] = dk.ramp(np.full((16, W_ - 40), 0.6) + dk.vnoise(W_ - 40, 16, seed + 2, ((8, 1.0),), False, False) * 0.3, ("#5a3a20", "#c88a3a", "#ffc068"))
    alpha = np.zeros((H_, W_), bool)
    alpha[top:, 8:W_ - 8] = True
    arr[top - 24:top, 40:110] = dk.hexa("#141a28")
    alpha[top - 24:top, 40:110] = True
    arr[top - 14:top, 150:200] = dk.hexa("#1a2030")
    alpha[top - 14:top, 150:200] = True
    arr[8:top - 24, 74:78] = dk.hexa("#1a2030")
    alpha[8:top - 24, 74:78] = True
    arr[4:10, 72:80] = dk.hexa("#ff2a20")
    alpha[4:10, 72:80] = True
    for x in (8, W_ - 12):
        arr[top - 4:top, x:x + 4] = dk.hexa("#ff2a20")
        alpha[top - 4:top, x:x + 4] = True
    rgba = np.dstack([np.clip(arr, 0, 255).astype(np.uint8), np.where(alpha, 255, 0).astype(np.uint8)])
    return _I.fromarray(rgba, "RGBA")


PROPS.update({"bc_tower": p_tower, "bc_tower_b": lambda: p_tower(582, 0.22), "bc_tower_c": lambda: p_tower(583, 0.12)})
TEXTURES.update({"bc_wall_brick": p_wall_brick, "bc_wall_brick_b": p_wall_brick_b, "bc_wall_conc": p_wall_conc, "bc_wall_steel": p_wall_steel, "bc_wall_cabin": p_wall_cabin,
                 "bc_floor_wet": p_floor_wet, "bc_floor_stair": p_floor_stair, "bc_floor_grate": p_floor_grate, "bc_floor_cabin": p_floor_cabin, "bc_floor_alley": p_floor_alley,
                 "bc_sky": p_sky})
def p_tower_door():
    """The tower's door on the platform: violet light and a pale beam up (the Mothership's way)."""
    return dk.to_img(_door_glow(591, ("#1a0c30", "#3a1a6a", "#6a3ab0", "#a070ff", "#e0c8ff"), ((64, 0, "#f0e0ff"),), frame="#1a1c28"))


DECALS.update({"bc_alley_door": p_alley_door, "bc_stair_glow": p_stair_glow, "bc_tower_door": p_tower_door})




# --- round 2 (docs/briefs/DOOM_POLISH_ROUND2_BRIEF.md, Balcony): the drop and the city dominate the reference view. The drops' far walls stop under the eye and are the lit
# facades of the buildings below (dark concrete in three variants, single windows placed one by one as decals, the yard's blue-lit shutters at their feet); the sky keeps the moon
# where the reference view (pitched 4 degrees down) frames it, over a lower skyline drawn first (so no tower hides it)

def p_sky2():
    """The painting's sky: torn storm cloud, a searchlight beam, a dense low skyline of towers with lit windows and red mast lamps, and the full moon (drawn over the skyline, at
    the upper left of the view north: az -21 degrees, 16 degrees up)."""
    arr = dk.sky_strip(462, clouds=("#1e2c48", "#28385c", "#344870", "#445c88", "#5a74a2", "#7894c0"), glow="#6a7ac0", lift=0.08, moon=None,
                       beams=((900, 22, 7), (140, -14, 6)), stars=0,
                       skyline={"layers": (("#2c3a5c", 10, 36, 0.12), ("#222c4a", 14, 44, 0.14), ("#182038", 8, 30, 0.10)),
                                "win": ("#e0a448", "#ffc068", "#5ad0ff", "#d070ff", "#ff5ab0"), "street": "#0a0c1a"})
    H, W = arr.shape[:2]
    hz = int(H * 0.76)
    mx, my, r = 964, hz - 46, 13
    yy, xx = np.indices((H, W))
    d = np.sqrt((xx - mx) ** 2 + (yy - my) ** 2)
    dk.mix_dither(arr, np.clip(1 - (d - r) / (r * 3.2), 0, 0.7) * (d > r), "#7a98d0", k=0.5)
    disc = d <= r
    mv = dk.vnoise(W, H, 471, ((64, 0.5), (128, 0.5)), True, False)
    arr[disc] = dk.ramp(np.clip(0.8 + (mv[disc] - 0.5) * 0.5 - (xx[disc] - mx) / (r * 6), 0, 1)[None, :], ("#8aa0c8", "#c8d8ec", "#f0f4fc"))[0]
    for cy, cx0, cx1 in ((my - 6, mx - 30, mx + 4), (my + 9, mx - 6, mx + 34)):  # torn cloud across the disc
        band = (np.abs(yy - cy) < 2) & (xx > cx0) & (xx < cx1)
        arr[band] = arr[band] * 0.4 + dk.hexa("#2c3c60") * 0.6
    return dk.to_img(arr)


def p_facade(seed, base):
    return dk.p_wall_bldg(seed, base)


TEXTURES.update({"bc_sky": p_sky2, "bc_facade_a": lambda: p_facade(601, ("#2c3854", "#3a4866", "#4a587a", "#5c6c90")),
                 "bc_facade_b": lambda: p_facade(602, ("#2e3048", "#3c3e5a", "#4c4e6e", "#5e6286")), "bc_facade_c": lambda: p_facade(603, ("#342c44", "#423856", "#52466a", "#665a82"))})
DECALS.update({"bc_win_amber": lambda: dk.p_window("#ffb050", 611), "bc_win_violet": lambda: dk.p_window("#c070ff", 612), "bc_win_cyan": lambda: dk.p_window("#5ad0ff", 613),
               "bc_win_dark": lambda: dk.p_window(None, 614)})




def p_lace():
    """Round 2: the white lace dome over the Mothership's door (the painting's): an organic cream filigree (cell walls of a jittered Voronoi net) over a half-dome, lit warm from below,
    the holes open (alpha), small warm lamps along its foot. Replaces the flat placeholder (a dark half-disc with ruled arcs)."""
    W_, H_ = 256, 176
    rng = np.random.default_rng(621)
    pts = rng.random((70, 2)) * [W_, H_ * 1.1]
    yy, xx = np.indices((H_, W_))
    d = np.sqrt((xx[..., None] - pts[:, 0]) ** 2 + (yy[..., None] - pts[:, 1]) ** 2)
    d.sort(axis=2)
    edge = (d[..., 1] - d[..., 0]) < 3.2
    cx, base = W_ / 2, H_ - 10
    dome = (((xx - cx) / (W_ / 2 - 6)) ** 2 + ((yy - base) / (H_ - 18)) ** 2) <= 1.0
    rim = dome & ((((xx - cx) / (W_ / 2 - 6)) ** 2 + ((yy - base) / (H_ - 18)) ** 2) > 0.86)
    lace = (edge | rim) & dome & (yy <= base)
    v = np.clip(0.55 + (yy / H_) * 0.4 + dk.vnoise(W_, H_, 622, ((8, 0.5), (32, 0.5)), False, False) * 0.2, 0, 1)
    arr = dk.ramp(v, ("#8a8090", "#c8c0c8", "#ece4dc", "#fff4e0"))
    alpha = lace.copy()
    arr[base:base + 6, 10:W_ - 10] = dk.hexa("#d8d0d0")
    alpha[base:base + 6, 10:W_ - 10] = True
    for k in range(12):
        x = 16 + k * (W_ - 32) // 11
        arr[base - 3:base + 1, x:x + 4] = dk.hexa("#ffd890")
        alpha[base - 3:base + 1, x:x + 4] = True
    rgba = np.dstack([np.clip(arr, 0, 255).astype(np.uint8), np.where(alpha, 255, 0).astype(np.uint8)])
    from PIL import Image as _I
    return _I.fromarray(rgba, "RGBA")


DECALS.update({"bc_lace": p_lace})


def p_floor_grate2():
    """Round 2: the bridge's grating with the lit drop showing through (a hazy blue-violet, not black) and lighter wet bars (the exposure rule)."""
    arr = dk.ramp(dk.vnoise(T, T, 532, ((4, 0.5), (16, 0.5))) * 0.6 + 0.2, ("#141a2c", "#1c2438", "#262e48"), cell=2)
    yy, xx = np.indices((T, T))
    bars = (xx % 16 < 4) | (yy % 32 < 4)
    v = dk.vnoise(T, T, 531, ((8, 0.5), (32, 0.5)))
    arr[bars] = dk.ramp(v[bars][None, :] * 0.6 + 0.35, ("#2a323e", "#404a5a", "#5a6678", "#7a88a2"))[0]
    dk.mix_dither(arr, np.where(bars, np.clip((v - 0.55) * 2.5, 0, 0.8), 0), "#a8bce8", k=0.5, cell=2)
    return dk.to_img(arr)


TEXTURES.update({"bc_floor_grate": p_floor_grate2})


def p_alley_door2():
    """Round 2: the alley's end, the club's side door open on the dance floor: a brighter core (the light the alley is lit by), blue to white, magenta and violet beams."""
    return dk.to_img(_door_glow(561, ("#141a4a", "#2a3a9a", "#4a6ae0", "#8aa8ff", "#d8e4ff"), ((40, 14, "#ff7ac0"), (90, -12, "#b890ff"))))


DECALS.update({"bc_alley_door": p_alley_door2})


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in {**TEXTURES, **PROPS, **DECALS}.items():
        fn().save(os.path.join(OUT, name + ".png"))
    import make_balcony_guides as bg
    n = bg.main_cropped()
    print("wrote %d textures, %d props, %d decals and %d guide frames to %s" % (len(TEXTURES), len(PROPS), len(DECALS), n, OUT))


if __name__ == "__main__":
    sys.exit(main())
