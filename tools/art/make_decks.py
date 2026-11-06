#!/usr/bin/env python3
"""The pad strip's skins, one per world family (lead ruling 29, package A3 of docs/art/VISUAL_AUDIT.md, style guide section 11).

    python tools/art/make_decks.py [--sheet <png>]

Every skin is the same construction (src/story/story_deck.gd draws it): a tileable surface behind the whole strip, a lip along its top,
a raised bank plate under each pad pair, a recessed well round each pad, a bezel round the middle display, and a small lamp (off | on)
that counts the beats of the bar. Only the material and the palette change, so a new family is one entry in FAMILIES plus, if its
material is new, one surface painter. Everything is drawn here at the picture's internal pixel size (360 lines; the game scales it by
screen height / 360 with nearest filtering, so the strip has the same pixel grain as the world above it), quantised to the family's ramp
with the 8x8 ordered dither of tools/story/art/pixeltex.py, lit from the upper left, edged one step darker. Deterministic (seeded); rerun
after any change, never edit the PNGs by hand.

Writes assets/run/deck/<family>/{panel,trim,plate,well,bezel,lamp}.png (+ platter.png, knob.png for the club) and
assets/run/deck/skins.json: the runtime colours of each skin (display, unlit pad, lamps, meters) and which art world uses which family.
--sheet writes a preview of every skin as a mock strip (for review, not shipped).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "story", "art"))
import pixeltex as px  # noqa: E402

OUT = os.path.join(ROOT, "assets", "run", "deck")
LIGHT = np.array([-0.62, -0.78], np.float32)  # towards the light: upper left

# The families. ramp: the surface's shades, dark to light (from the world's palette in docs/art/STYLE_GUIDE.md section 4, kept dark: the
# strip is a frame round the picture, the pads are what shines). rim: the shades of raised edges (plate, bezel). accent: the emitted
# colour (lamps, trim light). Runtime colours go to skins.json as they are.
FAMILIES = {
    "club": {  # the Warehouse: the DJ desk, black anodised metal with a magenta neon tube and spinning platters
        "worlds": ["night_one"],
        "material": "anodised", "trim": "neon",
        "ramp": ["#0a0618", "#13111f", "#1b1530", "#251c40", "#30244f"],
        "rim": ["#13111f", "#251c40", "#3a2a5c", "#5a3f86", "#7a5ab0"],
        "accent": ["#c23a8a", "#ff4fb0", "#ffd0ec"], "accent2": "#2fb6c8",
        "display": {"bg": "#050310", "edge": "#2fb6c8", "line": "#66d8ff"},
        "pad": {"off": "#140f26", "ring": "#3d3070"}, "lamp": "#ff4fb0",
        "vu": ["#3ae0a0", "#ffcc40", "#ff5068"], "label": "#e8e0ff",
        "spinners": True, "knobs": True,
    },
    "ship": {  # the Mothership: a console of hull plates and rivets with a teal light strip
        "worlds": ["mothership"],
        "material": "hull", "trim": "lightstrip",
        "ramp": ["#06081c", "#0b0c1e", "#141c30", "#1e2a40", "#2a3a52"],
        "rim": ["#0b0c1e", "#1e2a40", "#3b4d63", "#56708a", "#7b98b0"],
        "accent": ["#2a6a70", "#7be0d0", "#d8fff8"], "accent2": "#b88cff",
        "display": {"bg": "#030c14", "edge": "#7be0d0", "line": "#7be0d0"},
        "pad": {"off": "#0c1424", "ring": "#2e4a5e"}, "lamp": "#7be0d0",
        "vu": ["#7be0d0", "#b88cff", "#ff7ab0"], "label": "#d8f4ff",
    },
    "hell": {  # the Underworld: hammered copper sheets, rivets, an ember seam
        "worlds": ["underworld"],
        "material": "copper", "trim": "ember_band",
        "ramp": ["#200d11", "#2e1210", "#401a12", "#572618", "#6e3420"],
        "rim": ["#2a0a08", "#572222", "#8a4426", "#b06a38", "#d89058"],
        "accent": ["#8a2a10", "#ff6a1a", "#ffd090"], "accent2": "#c02030",
        "display": {"bg": "#120404", "edge": "#ff6a1a", "line": "#ff9a50"},
        "pad": {"off": "#1e0c0c", "ring": "#5a2a1e"}, "lamp": "#ff6a1a",
        "vu": ["#ffb050", "#ff6a1a", "#ff2a3a"], "label": "#ffe0c8",
    },
    "hospital": {  # the Hospital: a clinical panel of blue enamel, screws, a chrome edge, a monitor-green lamp
        "worlds": ["hospital"],
        "material": "enamel", "trim": "chrome",
        "ramp": ["#0c1636", "#132036", "#18293d", "#22344c", "#2c3f5a"],
        "rim": ["#0c1636", "#2c3f5a", "#4a5a78", "#6e809c", "#9fc4e8"],
        "accent": ["#2a6a48", "#5fd890", "#e0fff0"], "accent2": "#e0b060",
        "display": {"bg": "#03100c", "edge": "#5fd890", "line": "#5fd890"},
        "pad": {"off": "#101c30", "ring": "#34486a"}, "lamp": "#5fd890",
        "vu": ["#5fd890", "#e0b060", "#ff6a60"], "label": "#e8f0ff",
    },
    "ward": {  # the Ward: the same clinical panel in the asylum's green enamel, chipped to rust, an office-lamp amber pilot
        "worlds": ["mental_hospital"],
        "material": "enamel_chipped", "trim": "chrome",
        "ramp": ["#06110c", "#0b1519", "#14211e", "#1c2b25", "#26372f"],
        "rim": ["#0b1519", "#26372f", "#394d44", "#4a6758", "#7a9a88"],
        "accent": ["#6a4a20", "#e8c070", "#fff4d8"], "accent2": "#a05a30",
        "display": {"bg": "#060e0a", "edge": "#c8e8d0", "line": "#a8d8b8"},
        "pad": {"off": "#0e1814", "ring": "#34483e"}, "lamp": "#e8c070",
        "vu": ["#a8d8b8", "#e8c070", "#e07050"], "label": "#e8f4ea",
    },
    "gospel": {  # Galilee and Jerusalem: a board of cedar planks, nail heads, an oil-lamp glow
        "worlds": ["galilee_shore", "hillside", "bethany", "jerusalem"],
        "material": "planks", "trim": "moulding",
        "ramp": ["#1e140c", "#2a1c12", "#3a2a1c", "#4a3622", "#5a4228"],
        "rim": ["#2a1c12", "#5a3e26", "#7a5a38", "#9a7448", "#c8a878"],
        "accent": ["#8a5a20", "#ffb060", "#fff0c8"], "accent2": "#5a8ab8",
        "display": {"bg": "#14100c", "edge": "#c8a878", "line": "#ffc89a"},
        "pad": {"off": "#1e160e", "ring": "#5a4228"}, "lamp": "#ffb060",
        "vu": ["#a8b860", "#ffb060", "#ff7a40"], "label": "#fff0d8",
    },
    "squadron": {  # the 1940s airfield: an olive-drab instrument panel, screws, worn edges, brass, amber bulbs
        "worlds": ["airfield", "city", "harbour"],
        "material": "olive", "trim": "brass",
        "ramp": ["#14140c", "#1e1e12", "#2a2a18", "#343620", "#40422a"],
        "rim": ["#1a1810", "#3a3a24", "#5e6440", "#8a7a50", "#c8b070"],
        "accent": ["#7a5a20", "#ffd890", "#fff8e0"], "accent2": "#c86a2a",
        "display": {"bg": "#0c0a04", "edge": "#c8b070", "line": "#ffd890"},
        "pad": {"off": "#1a1a10", "ring": "#4a4a30"}, "lamp": "#ffd890",
        "vu": ["#c8d890", "#ffd890", "#ff8a40"], "label": "#fff4dc",
    },
    "ember": {  # the Ember road: dark timber with a carved knotwork band whose grooves glow with the Ember
        "worlds": ["orchard", "birch_hall", "deep_halls", "ash_land"],
        "material": "timber", "trim": "carved",
        "ramp": ["#120c08", "#1a1410", "#241a12", "#2e2216", "#3a2a1c"],
        "rim": ["#1a1410", "#3e2c1c", "#5a3e26", "#7a5a38", "#a07850"],
        "accent": ["#8a3a10", "#ff7a20", "#ffd8a0"], "accent2": "#ffb050",
        "display": {"bg": "#100a06", "edge": "#ff7a20", "line": "#ffb050"},
        "pad": {"off": "#18100a", "ring": "#4e3622"}, "lamp": "#ff7a20",
        "vu": ["#c8a060", "#ffb050", "#ff5a20"], "label": "#fff0e0",
    },
    "bassment": {  # the dungeon under the club: stone blocks, an iron band with studs, torch light
        "worlds": ["bassment"],
        "material": "stone", "trim": "iron",
        "ramp": ["#100c10", "#181418", "#221c20", "#2c2428", "#362e30"],
        "rim": ["#100c10", "#2a2628", "#45403e", "#625a54", "#8a8076"],
        "accent": ["#7a3a10", "#ffb050", "#fff0c0"], "accent2": "#a05acf",
        "display": {"bg": "#0a0808", "edge": "#ffb050", "line": "#ffb050"},
        "pad": {"off": "#161214", "ring": "#463e3e"}, "lamp": "#ffb050",
        "vu": ["#a0c080", "#ffb050", "#ff5040"], "label": "#f4e8dc",
    },
    "neutral": {  # any world without its own family (style guide 11: never another world's desk)
        "worlds": [],
        "material": "anodised", "trim": "plain",
        "ramp": ["#0c0a14", "#13111f", "#191626", "#201c2e", "#282336"],
        "rim": ["#13111f", "#282336", "#3a3448", "#56506a", "#8a849c"],
        "accent": ["#4a5a7a", "#9fc4e8", "#e8f4ff"], "accent2": "#eab278",
        "display": {"bg": "#06060c", "edge": "#9fc4e8", "line": "#9fc4e8"},
        "pad": {"off": "#14121e", "ring": "#3a3448"}, "lamp": "#9fc4e8",
        "vu": ["#9fc4e8", "#eab278", "#ff6a60"], "label": "#eef0ff",
    },
}

PANEL = 96
PLATE, PLATE_M = 48, 12
WELL, WELL_M = 40, 14
BEZEL, BEZEL_M = 40, 12
TRIM_W, TRIM_H = 32, 8
LAMP = 8


def pal(cols) -> np.ndarray:
    return px.ramp(*cols)


def bayer(h: int, w: int) -> np.ndarray:
    return px.BAYER8[np.arange(h)[:, None] % 8, np.arange(w)[None, :] % 8]


def quant(shade: np.ndarray, ramp: np.ndarray, dither: float = 0.9) -> np.ndarray:
    """A 0..1 field of any shape onto a ramp, ordered dither (pixeltex.quantise works on squares only)."""
    k = len(ramp) - 1
    v = np.clip(shade, 0, 1) * k + bayer(*shade.shape) * dither
    i = np.clip(np.round(v), 0, k).astype(int)
    return (ramp[i] * 255 + 0.5).astype(np.uint8)


def rgb(c: str) -> np.ndarray:
    return (px.hexc(c) * 255 + 0.5).astype(np.uint8)


def noise2(h: int, w: int, scale: float, seed: int) -> np.ndarray:
    n = max(h, w)
    return px.noise(n, scale, seed)[:h, :w]


# ---- surfaces: 0..1 shade fields, tileable at PANEL x PANEL, plus masks for details in other colours -----------------------------------------------

def surface(fam: dict, seed: int):
    n = PANEL
    x, y = px.grid(n)
    m = fam["material"]
    marks = {}  # name -> mask, drawn after quantising: "ink" (darkest), "hi" (rim light), "accent", "accent_dim"
    if m == "anodised":
        rows = np.random.RandomState(seed).rand(n).astype(np.float32)
        sh = 0.42 + 0.10 * (rows[y.astype(int)] - 0.5) + 0.10 * (px.noise(n, 24, seed + 1) - 0.5)
        groove = (y.astype(int) % 48) == 0
        sh = np.where(groove, 0.05, sh)
        sh = np.where((y.astype(int) % 48) == 1, sh + 0.25, sh)
    elif m == "hull":
        pw, ph = 48, 32
        lx, ly = x % pw, y % ph
        sh = 0.45 + 0.12 * (px.noise(n, 32, seed) - 0.5)
        tone = np.random.RandomState(seed + 2).rand(n // ph + 1, n // pw + 1).astype(np.float32)
        sh += 0.12 * (tone[(y // ph).astype(int), (x // pw).astype(int)] - 0.5)
        sh = np.where((lx == 1) | (ly == 1), sh + 0.25, sh)
        sh = np.where((lx == pw - 1) | (ly == ph - 1), sh - 0.2, sh)
        marks["ink"] = (lx == 0) | (ly == 0)
        riv = ((lx == 4) | (lx == pw - 5)) & ((ly == 4) | (ly == ph - 5))
        marks["hi"] = riv
        marks["ink2"] = ((lx == 5) | (lx == pw - 4)) & ((ly == 5) | (ly == ph - 4))
    elif m == "copper":
        ham = px.noise(n, 6, seed)
        sh = 0.5 + 0.35 * (ham - 0.5) + 0.1 * (px.noise(n, 24, seed + 1) - 0.5)
        lx, ly = x % 48, y % 48
        sh = np.where(ly == 1, sh + 0.2, sh)
        marks["ink"] = (ly == 0) | (lx == 0)
        marks["hi"] = ((lx % 12) == 6) & (ly == 3)
        crack = (np.abs(px.noise(n, 20, seed + 5) - 0.5) < 0.012) & (px.noise(n, 48, seed + 6) > 0.62)
        marks["accent_dim"] = crack
    elif m in ("enamel", "enamel_chipped"):
        sh = 0.5 + 0.06 * (px.noise(n, 16, seed) - 0.5) + 0.12 * (px.speckle(n, 0.03, seed + 1) - 0.03)
        ly = y.astype(int) % 48
        sh = np.where(ly == 24, 0.12, np.where(ly == 25, 0.85, sh))
        lx = x.astype(int) % 96
        marks["hi"] = ((lx == 6) | (lx == 54)) & (ly == 8)
        marks["ink2"] = ((lx == 7) | (lx == 55)) & (ly == 9)
        if m == "enamel_chipped":
            chip = px.noise(n, 5, seed + 3) > 0.74
            marks["accent2"] = chip & (px.noise(n, 30, seed + 4) > 0.55)
    elif m == "planks":
        phh = 12
        r = (y // phh).astype(int)
        tone = np.random.RandomState(seed).rand(n // phh + 1).astype(np.float32)
        warp = px.noise(n, 24, seed + 1) * 9
        grain = 0.5 + 0.5 * np.sin((y + warp) * 1.9 + r * 1.3)
        sh = 0.42 + 0.16 * (tone[r] - 0.5) + 0.16 * (grain - 0.5) + 0.06 * (px.noise(n, 6, seed + 2) - 0.5)
        ly = y.astype(int) % phh
        sh = np.where(ly == 1, sh + 0.18, sh)
        marks["ink"] = ly == 0
        off = (r % 2) * 48
        lx = (x.astype(int) + off) % 96
        marks["ink3"] = (lx == 0) & (ly > 0)
        marks["hi"] = ((lx == 3) | (lx == 92)) & (ly == 5)
        marks["ink2"] = ((lx == 3) | (lx == 92)) & (ly == 6)
    elif m == "olive":
        sh = 0.5 + 0.07 * (px.noise(n, 20, seed) - 0.5) + 0.05 * (px.noise(n, 4, seed + 1) - 0.5)
        lx, ly = x.astype(int) % 48, y.astype(int) % 48
        sh = np.where((lx == 1) | (ly == 1), sh + 0.22, sh)
        marks["ink"] = (lx == 0) | (ly == 0)
        wear = ((lx <= 3) | (ly <= 3)) & (px.noise(n, 3, seed + 2) > 0.66)
        marks["bare"] = wear
        scr = ((lx == 5) | (lx == 43)) & ((ly == 5) | (ly == 43))
        marks["hi"] = scr
        marks["ink2"] = ((lx == 6) | (lx == 44)) & ((ly == 6) | (ly == 44))
    elif m == "timber":
        warp = px.noise(n, 32, seed) * 12
        grain = 0.5 + 0.5 * np.sin((x + warp) * 1.4)
        pw = 24
        col = (x // pw).astype(int)
        tone = np.random.RandomState(seed + 1).rand(n // pw + 1).astype(np.float32)
        sh = 0.42 + 0.14 * (grain - 0.5) + 0.14 * (tone[col] - 0.5) + 0.06 * (px.noise(n, 5, seed + 2) - 0.5)
        lx = x.astype(int) % pw
        sh = np.where(lx == 1, sh + 0.16, sh)
        marks["ink"] = lx == 0
        knot = px.noise(n, 10, seed + 3) > 0.8
        sh = np.where(knot, sh - 0.2, sh)
    elif m == "stone":
        sh, mort = px.bricks(n, rows=6, cols=3, mortar=1, seed=seed, wear=0.4)
        sh = 0.25 + 0.6 * sh
        marks["ink"] = mort > 0.5
    else:
        sh = np.full((n, n), 0.5, np.float32)
    return np.clip(sh, 0, 1), marks


def paint(shade, marks, fam):
    ramp = pal(fam["ramp"])
    out = quant(shade, ramp)
    cols = {
        "ink": rgb(fam["ramp"][0]), "ink2": rgb(fam["ramp"][0]), "ink3": rgb(fam["ramp"][1]),
        "hi": rgb(fam["rim"][3]), "bare": rgb(fam["rim"][2]),
        "accent": rgb(fam["accent"][1]), "accent_dim": rgb(fam["accent"][0]), "accent2": rgb(fam["accent2"]),
    }
    for k in ("ink3", "ink", "ink2", "bare", "accent2", "accent_dim", "accent", "hi"):
        if k in marks:
            out[marks[k]] = cols[k]
    return out


# ---- shapes: signed distance to a rounded rectangle, and a bevelled frame from it ---------------------------------------------------------------

def sdf_round(w: int, h: int, inset: float, radius: float):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
    hx, hy = (w - 1) / 2.0 - inset - radius, (h - 1) / 2.0 - inset - radius
    qx, qy = np.abs(x - cx) - hx, np.abs(y - cy) - hy
    out = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - radius
    gx = np.sign(x - cx) * (qx > -0.5)
    gy = np.sign(y - cy) * (qy > -0.5)
    nrm = np.sqrt(gx * gx + gy * gy) + 1e-6
    return out, gx / nrm, gy / nrm


def frame(fam, w, h, radius, band, kind, seed):
    """A bevelled frame (RGBA). kind: 'raised' (a plate: rim lit at its outer upper left, centre the surface a step down),
    'well' (a recess: the inner wall shadowed at the upper left, lit at the lower right, centre near black),
    'bezel' (a raised ring with a transparent centre)."""
    d, nx, ny = sdf_round(w, h, 0.5, radius)
    lit = -(nx * LIGHT[0] + ny * LIGHT[1])  # 1 where the edge faces the light
    lit = -lit
    rim = pal(fam["rim"])
    tex = noise2(h, w, 6, seed) - 0.5
    out = np.zeros((h, w, 4), np.uint8)
    inside = d <= 0
    ring = inside & (d > -band)
    t = np.clip(-d / band, 0, 1)  # 0 at the outer edge, 1 at the inner edge of the ring
    if kind == "well":
        sh = 0.35 - 0.3 * lit * (t > 0.35) + 0.2 * lit * (t <= 0.35) + 0.08 * tex
        col = quant(sh, rim, 0.45)
        centre = rgb(fam["ramp"][0])
    else:
        slope = np.where(t < 0.5, lit, -lit * 0.7)  # the outer slope faces out, the inner slope faces the centre
        sh = 0.5 + 0.32 * slope + 0.1 * tex
        col = quant(sh, rim, 0.45)
        centre = None
    out[ring, :3] = col[ring]
    out[ring, 3] = 255
    edge = inside & (d > -1.0)
    out[edge, :3] = rgb(fam["ramp"][0])  # the one-pixel darker edge
    core = inside & ~ring
    if kind == "raised":
        s, marks = surface(fam, seed + 11)
        sp = paint(np.clip(s[:h, :w] * 0.85, 0, 1), {k: v[:h, :w] for k, v in marks.items() if k in ("ink", "ink3")}, fam)
        out[core, :3] = sp[core]
        out[core, 3] = 255
        inner = core & (d > -band - 1.0)  # a dark line where the plate's face meets the rim
        out[inner, :3] = rgb(fam["ramp"][0])
    elif kind == "well":
        out[core, :3] = centre
        out[core, 3] = 255
    return out


def screws(img, fam, pts):
    hi, lo, mid = rgb(fam["rim"][4]), rgb(fam["ramp"][0]), rgb(fam["rim"][2])
    for (x, y) in pts:
        img[y - 1:y + 2, x - 1:x + 2, :3] = mid
        img[y - 1:y + 2, x - 1:x + 2, 3] = 255
        img[y - 1, x - 1, :3] = hi
        img[y + 1, x + 1, :3] = lo
        img[y, x - 1:x + 2, :3] = lo if fam["material"] in ("olive", "enamel", "enamel_chipped", "hull") else img[y, x - 1:x + 2, :3]


def plate(fam, seed):
    img = frame(fam, PLATE, PLATE, 9.0, 5.0, "raised", seed)
    if fam["material"] not in ("anodised",):
        m = 3
        screws(img, fam, [(m + 1, m + 1), (PLATE - m - 2, m + 1), (m + 1, PLATE - m - 2), (PLATE - m - 2, PLATE - m - 2)])
    if fam["trim"] == "neon":  # the club's plates carry a thin violet tube on their rim
        d, _, _ = sdf_round(PLATE, PLATE, 0.5, 9.0)
        tube = (d <= -2.0) & (d > -3.0)
        img[tube, :3] = rgb(fam["rim"][3])
    return img


def well(fam, seed):
    return frame(fam, WELL, WELL, 12.0, 4.0, "well", seed)


def bezel(fam, seed):
    img = frame(fam, BEZEL, BEZEL, 6.0, 5.0, "bezel", seed)
    if fam["material"] in ("olive", "hull", "copper", "stone", "enamel", "enamel_chipped"):
        screws(img, fam, [(3, 3), (BEZEL - 4, 3), (3, BEZEL - 4), (BEZEL - 4, BEZEL - 4)])
    return img


def trim(fam, seed):
    w, h = TRIM_W, TRIM_H
    img = np.zeros((h, w, 4), np.uint8)
    img[..., 3] = 255
    rim = pal(fam["rim"])
    y, x = np.mgrid[0:h, 0:w]
    t = fam["trim"]
    base = np.clip(0.55 - 0.1 * y + 0.08 * (noise2(h, w, 4, seed) - 0.5), 0, 1)
    img[..., :3] = quant(base, rim)
    img[0, :, :3] = rgb(fam["ramp"][0])
    img[h - 1, :, :3] = rgb(fam["ramp"][0])
    img[1, :, :3] = rgb(fam["rim"][3])
    a, a1, a2 = rgb(fam["accent"][0]), rgb(fam["accent"][1]), rgb(fam["accent"][2])
    if t == "neon":  # a dark rail and a magenta tube: core, glow above and below
        img[2:7, :, :3] = rgb(fam["ramp"][0])
        img[3, :, :3] = a
        img[4, :, :3] = a2
        img[5, :, :3] = a1
        img[6, :, :3] = a
    elif t == "lightstrip":
        img[4:6, :, :3] = a
        seg = (x % 8) < 6
        img[4][seg[4], :3] = a1
        img[5][seg[5], :3] = a2 * 0 + a1
    elif t == "ember_band":
        stud = (x % 16 == 7) & (y >= 2) & (y <= 4)
        img[stud, :3] = rgb(fam["rim"][4])
        img[6, :, :3] = a
        img[6][(x[6] % 5) < 3, :3] = a1
    elif t == "chrome":
        img[2, :, :3] = rgb(fam["rim"][4])
        img[3, :, :3] = rgb(fam["rim"][3])
        img[4:7, :, :3] = quant(np.full((3, w), 0.35), rim)
        if fam["material"] == "enamel_chipped":
            chip = noise2(h, w, 2, seed + 4) > 0.72
            img[chip & (y >= 3) & (y <= 6), :3] = rgb(fam["accent2"])
    elif t == "moulding":
        img[2, :, :3] = rgb(fam["rim"][4])
        img[3, :, :3] = rgb(fam["rim"][3])
        img[5, :, :3] = rgb(fam["rim"][0])
        dots = (x % 8 == 3) & (y == 4)
        img[dots, :3] = rgb(fam["rim"][4])
    elif t == "brass":
        img[2:6, :, :3] = quant(np.clip(0.75 - 0.15 * y[2:6] + 0.1 * (noise2(4, w, 3, seed + 2) - 0.5), 0, 1), rim)
        scr = (x % 16 == 8)
        img[3][scr[3], :3] = rgb(fam["rim"][4])
        img[4][scr[4], :3] = rgb(fam["ramp"][0])
    elif t == "carved":  # a knotwork zigzag cut into the timber, the Ember glowing in the groove
        zig = np.abs(((x + 4) % 8) - 4)  # 0..4
        groove = (np.abs(y - 1 - zig) < 0.6) | (np.abs(y - 1 - (4 - zig)) < 0.6)
        img[groove & (y >= 1) & (y <= 6), :3] = a
        img[groove & (y >= 2) & (y <= 5) & ((x % 4) == 0), :3] = a1
    elif t == "iron":
        img[2:7, :, :3] = quant(np.full((5, w), 0.3) + 0.1 * (noise2(5, w, 3, seed) - 0.5), rim)
        stud = (x % 12 == 5)
        img[3][stud[3], :3] = rgb(fam["rim"][4])
        img[4][stud[4], :3] = rgb(fam["rim"][2])
        img[5][stud[5], :3] = rgb(fam["ramp"][0])
    return img


def lamp(fam):
    """Two frames side by side: off | on. A round lens in a ring of the rim's metal."""
    img = np.zeros((LAMP, LAMP * 2, 4), np.uint8)
    y, x = np.mgrid[0:LAMP, 0:LAMP].astype(np.float32)
    r = np.sqrt((x - 3.5) ** 2 + (y - 3.5) ** 2)
    for f in range(2):
        sub = img[:, f * LAMP:(f + 1) * LAMP]
        ring = r <= 3.9
        sub[ring, :3] = rgb(fam["rim"][2])
        sub[ring, 3] = 255
        sub[(r > 3.0) & ring & (x + y > 7), :3] = rgb(fam["ramp"][0])
        lens = r <= 2.6
        if f == 0:
            sub[lens, :3] = rgb(fam["accent"][0])
            sub[lens & (x < 3) & (y < 3), :3] = rgb(fam["rim"][3])
        else:
            sub[lens, :3] = rgb(fam["accent"][1])
            sub[(r <= 1.3), :3] = rgb(fam["accent"][2])
    return img


def platter(fam, seed):
    n = 96
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.sqrt((x - 47.5) ** 2 + (y - 47.5) ** 2)
    a = np.arctan2(y - 47.5, x - 47.5)
    img = np.zeros((n, n, 4), np.uint8)
    disc = r <= 47
    groove = 0.3 + 0.12 * np.sin(r * 2.2) + 0.25 * np.clip(np.cos(a * 2 - 0.8), 0, 1) ** 6
    ramp = pal(["#05040a", "#0e0c16", "#1a1626", "#2c2640", "#4a4266"])
    img[disc, :3] = quant(groove, ramp)[disc]
    img[disc, 3] = 255
    img[(r > 46) & disc, :3] = rgb("#3a2a5c")
    lab = r <= 13
    img[lab, :3] = rgb(fam["accent"][0])
    img[(r <= 13) & (r > 11.5), :3] = rgb(fam["accent"][1])
    img[r <= 2, :3] = rgb("#d8d0e8")
    img[(r > 6) & (r < 9) & (np.abs(a) < 0.5), :3] = rgb(fam["accent2"])  # a mark, so the turning reads
    return img


def knob(fam):
    n = 12
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.sqrt((x - 5.5) ** 2 + (y - 5.5) ** 2)
    img = np.zeros((n, n, 4), np.uint8)
    body = r <= 5.6
    sh = 0.5 + 0.35 * np.clip(-((x - 5.5) * LIGHT[0] + (y - 5.5) * LIGHT[1]) / 6.0, -1, 1) * -1
    img[body, :3] = quant(sh, pal(fam["rim"]))[body]
    img[body, 3] = 255
    img[(r > 4.8) & body, :3] = rgb(fam["ramp"][0])
    img[(np.abs(x - 5.5) < 0.6) & (y < 5) & (y > 0), :3] = rgb(fam["accent"][1])
    return img


def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "RGBA" if img.shape[2] == 4 else "RGB"
    Image.fromarray(img, mode).save(path, optimize=False, compress_level=9)


def build():
    skins = {"worlds": {}, "skins": {}, "sizes": {"panel": PANEL, "plate": [PLATE, PLATE_M], "well": [WELL, WELL_M], "bezel": [BEZEL, BEZEL_M],
                                                    "trim": [TRIM_W, TRIM_H], "lamp": LAMP}}
    for i, (name, fam) in enumerate(FAMILIES.items()):
        seed = 1000 + 37 * i
        d = os.path.join(OUT, name)
        s, marks = surface(fam, seed)
        save(paint(s, marks, fam), os.path.join(d, "panel.png"))
        save(trim(fam, seed), os.path.join(d, "trim.png"))
        save(plate(fam, seed), os.path.join(d, "plate.png"))
        save(well(fam, seed), os.path.join(d, "well.png"))
        save(bezel(fam, seed), os.path.join(d, "bezel.png"))
        save(lamp(fam), os.path.join(d, "lamp.png"))
        if fam.get("spinners"):
            save(platter(fam, seed), os.path.join(d, "platter.png"))
        if fam.get("knobs"):
            save(knob(fam), os.path.join(d, "knob.png"))
        for w in fam["worlds"]:
            skins["worlds"][w] = name
        skins["skins"][name] = {
            "display_bg": fam["display"]["bg"], "display_edge": fam["display"]["edge"], "display_line": fam["display"]["line"],
            "pad_off": fam["pad"]["off"], "pad_ring": fam["pad"]["ring"], "lamp": fam["lamp"], "vu": fam["vu"], "label": fam["label"],
            "ink": fam["ramp"][0], "rim_light": fam["rim"][3],
            "spinners": bool(fam.get("spinners", False)), "knobs": bool(fam.get("knobs", False)),
        }
    with open(os.path.join(OUT, "skins.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(skins, f, indent=1, sort_keys=True)
        f.write("\n")
    print("decks:", ", ".join(FAMILIES))


# ---- the preview sheet: each skin composed as a strip the way story_deck.gd lays it out (pads as flat squares) -----------------------------------

def nine(img, w, h, m):
    """Nine-patch an RGBA image to w x h (corners kept, edges and centre stretched by nearest)."""
    H, W = img.shape[:2]
    out = np.zeros((h, w, 4), np.uint8)
    xs = np.concatenate([np.arange(m), m + (np.arange(w - 2 * m) * (W - 2 * m) // max(w - 2 * m, 1)), W - m + np.arange(m)])
    ys = np.concatenate([np.arange(m), m + (np.arange(h - 2 * m) * (H - 2 * m) // max(h - 2 * m, 1)), H - m + np.arange(m)])
    out[:] = img[ys][:, xs]
    return out


def blit(dst, src, x, y):
    h, w = src.shape[:2]
    a = src[..., 3:4].astype(np.float32) / 255.0
    region = dst[y:y + h, x:x + w, :3].astype(np.float32)
    dst[y:y + h, x:x + w, :3] = (region * (1 - a) + src[..., :3] * a).astype(np.uint8)


def preview(path):
    W, H = 640, 130
    rows = []
    for name, fam in FAMILIES.items():
        d = os.path.join(OUT, name)
        ld = lambda f: np.array(Image.open(os.path.join(d, f)).convert("RGBA"))
        strip = np.zeros((H, W, 3), np.uint8)
        pan = ld("panel.png")
        for yy in range(0, H, PANEL):
            for xx in range(0, W, PANEL):
                blit(strip, pan[: min(PANEL, H - yy), : min(PANEL, W - xx)], xx, yy)
        tr = ld("trim.png")
        for xx in range(0, W, TRIM_W):
            blit(strip, tr[:, : min(TRIM_W, W - xx)], xx, 0)
        s, gap = 96, 12
        y0 = int((H - s) * 0.55)
        pads = [(24, y0), (24 + s + gap, y0), (W - 24 - 2 * s - gap, y0), (W - 24 - s, y0)]
        for a, b in ((0, 1), (2, 3)):
            x0 = pads[a][0] - 10
            blit(strip, nine(ld("plate.png"), pads[b][0] + s + 10 - x0, s + 20, PLATE_M), x0, y0 - 10)
        for (xx, yy) in pads:
            blit(strip, nine(ld("well.png"), s + 10, s + 10, WELL_M), xx - 5, yy - 5)
            strip[yy + 2:yy + s - 2, xx + 2:xx + s - 2] = rgb(fam["pad"]["off"])
        lx0, lx1 = pads[1][0] + s + 30, pads[2][0] - 30
        blit(strip, nine(ld("bezel.png"), lx1 - lx0, 60, BEZEL_M), lx0, 30)
        strip[30 + 5:30 + 55, lx0 + 5:lx1 - 5] = rgb(fam["display"]["bg"])
        lp = ld("lamp.png")
        for k in range(4):
            blit(strip, lp[:, (LAMP if k == 1 else 0):(LAMP * 2 if k == 1 else LAMP)], (lx0 + lx1) // 2 - 22 + k * 12, 16)
        rows.append(strip)
    sheet = np.concatenate(rows, 0)
    Image.fromarray(sheet).resize((W * 2, sheet.shape[0] * 2), Image.NEAREST).save(path)
    print("sheet", path)


if __name__ == "__main__":
    build()
    if "--sheet" in sys.argv:
        preview(sys.argv[sys.argv.index("--sheet") + 1])
