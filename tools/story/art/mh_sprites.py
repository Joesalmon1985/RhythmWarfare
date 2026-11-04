"""Mental Hospital chapter sprites: the shared stage.sprites ids (re-themed), the rear silhouettes and the `manifest.interlude`.

Deck pieces (pad bezel, platter, knobs, faders) are Night One's, drawn through a hue remap (indigo to deep teal, cyan to mint,
magenta to coral). Lighting sprites stay white/neutral so the runtime tints them. Everything is original, drawn by the script.
"""
from __future__ import annotations

import colorsys
import math
import os
import random
import re

import numpy as np
from PIL import Image, ImageDraw

from . import lib, sprites as png_sprites, stage as S
from .lib import (OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, pivot_in, poly, rad_grad, rect,
                  write_svg)
from .mh_stage import (BUTTER, CORAL, CREAM, INK, LILAC, LILAC_D, LILAC_L, MINT, MINT_D, WOOD, WOOD_D, WOOD_L, paper_star)

_HEX = re.compile(r"#[0-9a-fA-F]{6}")


def _remap_hex(m):
    c = m.group(0)
    r, g, b = lib.hex_to_rgb(c)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    hd = h * 360
    if s < 0.1:
        return c
    if 160 <= hd < 215:
        nh, ns = 156, s * 0.8
    elif 215 <= hd < 300:
        nh, ns = 188, s * 0.5
    elif 300 <= hd <= 350:
        nh, ns = 8, s * 0.9
    else:
        return c
    rr, gg, bb = colorsys.hls_to_rgb(nh / 360, l, ns)
    return lib.rgb_to_hex((rr * 255, gg * 255, bb * 255))


def remap(text):
    return _HEX.sub(_remap_hex, text)


def _save_rgba(name, arr):
    os.makedirs(lib.PNG_DIR, exist_ok=True)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(lib.PNG_DIR, name), compress_level=9)
    return f"processed/{name}"


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


# ---- props -----------------------------------------------------------------------------------------------------------------

def spr_woofer(sp):
    """A radio speaker cone: paper cone in a cream surround with a little brass dust cap. Pivot centre."""
    r = 50
    defs = rad_grad("cone", [(0, "#fff0d6"), (0.5, "#e8c9a0"), (1, "#b8946a")], 0.42, 0.38, 0.75)
    d = circle(0, 0, r - 2, "#f7e7cf", OUT, 3.6)
    for k in range(16):  # surround stitching
        a = k * math.tau / 16
        d += circle(math.cos(a) * (r - 7), math.sin(a) * (r - 7), 1.6, "#a8743c", None)
    d += circle(0, 0, r - 12, "#3a2a2a", None)
    d += circle(0, 0, r - 14, "url(#cone)", OUT, 2.2)
    for k, rr in enumerate((34, 28, 22, 17)):
        d += circle(0, 0, rr, None, "#8a6a4a" if k % 2 == 0 else "#fff6e4", 1.3, sop=0.55)
    d += circle(0, 0, 12, "#d9b45a", OUT, 2.4) + circle(-3, -3, 4, "#fff2b0", None, op=0.8)
    d += path("M-32 -20 A38 38 0 0 1 -8 -36", None, "#ffffff", 3, sop=0.45)
    info = write_svg("props/woofer.svg", (-r - 8, -r - 8, r + 8, r + 8), d, defs)
    sp["woofer"] = {"file": "source/props/woofer.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "radius": r}


def spr_fixture(sp):
    """A clip-on spotlight painted lilac: clamp and yoke at the mount, a round-nosed lamp pointing straight down."""
    defs = lin_grad("body", [(0, "#c9b8f0"), (1, "#8a74c8")], 0, 0, 1, 0)
    d = rect(-11, 0, 22, 6, "#cfeee6", OUT, 2.4, rx=2)
    d += path("M-15 8 L-15 30 M15 8 L15 30", None, OUT, 8) + path("M-15 8 L-15 30 M15 8 L15 30", None, "#e6dcfa", 4.4)
    d += rect(-8, 6, 16, 8, "#9bd6c8", OUT, 2.2, rx=2)
    d += rect(-12, 16, 24, 34, "url(#body)", OUT, 3, rx=6)
    d += line((-8, 20), (-8, 46), "#ffffff", 1.6, 0.5)
    d += paper_star(0, 33, 5.2, BUTTER, 1.2)
    d += ellipse(0, 51, 11, 4.5, "#4a3a78", OUT, 2.4)
    d += ellipse(0, 51, 8, 3.2, "#fff6d0", None) + ellipse(0, 51, 3.2, 3.0, "#ffffff", None)
    d += circle(-15, 30, 3, "#cfeee6", OUT, 1.4) + circle(15, 30, 3, "#cfeee6", OUT, 1.4)
    info = write_svg("props/fixture.svg", (-22, -2, 22, 60), d, defs)
    sp["fixture"] = {"file": "source/props/fixture.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "lens": [0, 51]}


def spr_disco_ball(sp):
    """A glitter ball covered in pastel mirror tiles, hung from a twist of paper-chain loops."""
    cy, r = 66, 27
    defs = rad_grad("ball", [(0, "#ffffff"), (0.5, "#d9ecf4"), (1, "#8a9ac8")], 0.4, 0.36, 0.7)
    defs += clip("bc", f'<circle cx="0" cy="{cy}" r="{r}"/>')
    d = ""
    cols = ["#ffd0e0", "#bfeadf", "#e6dcfa", "#fff4c0", "#ffffff"]
    for k in range(7):  # paper-chain links on the cord
        y = 2 + k * 8.6
        d += ellipse(0, y + 4, 4.4 if k % 2 else 1.8, 5, cols[k % 4] if k % 2 else "#ffffff", OUT, 1.5)
    d += circle(0, cy, r + 8, "#ffffff", None, op=0.16) + circle(0, cy, r + 4, "#ffffff", None, op=0.2)
    d += circle(0, cy, r, "url(#ball)", OUT, 3.4)
    rng = random.Random(9)
    inner = ""
    for row in range(-4, 5):
        yy = cy + row * 6.4
        wd = math.sqrt(max(r * r - (row * 6.4) ** 2, 1))
        n = max(int(wd * 2 / 6.0), 1)
        for k in range(n):
            x0 = -wd + k * (2 * wd / n)
            inner += rect(x0 + 0.4, yy - 3, 2 * wd / n - 0.8, 5.8, rng.choice(cols), None, op=0.6)
    inner += circle(r * 0.5, cy + r * 0.45, r * 0.95, "#2a1b4e", None, op=0.22)
    d += group(inner, 'clip-path="url(#bc)"')
    for k in range(-3, 4):
        d += path(f"M{f(k * 7 * 0.5)} {cy - r} Q{f(k * 12)} {cy} {f(k * 7 * 0.5)} {cy + r}", None, "#6a6a98", 0.9, sop=0.5)
    d += circle(-9, cy - 10, 4.4, "#ffffff", None, op=0.9) + paper_star(14, cy - 16, 3.0, "#ffffff", 0)
    d += circle(0, cy, r, None, OUT, 3.4)
    info = write_svg("props/disco_ball.svg", (-r - 14, -2, r + 14, cy + r + 14), d, defs)
    sp["disco_ball"] = {"file": "source/props/disco_ball.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "radius": r, "ball_centre": [0, cy]}


def spr_glowstick(sp):
    """A foil-star wand from the craft table: white (the runtime tints it), pivot at the grip end."""
    d = line((0, 4), (0, 38), OUT, 10, cap="round") + line((0, 4), (0, 38), "#ffffff", 5.6, cap="round")
    d += line((0, 31), (0, 38), "#c9c4e8", 5.6, cap="butt")
    for yy in (14, 22):
        d += line((-4.4, yy), (4.4, yy), OUT, 1.2)
    d += paper_star(0, -6, 14, "#ffffff", 2.4)
    d += paper_star(0, -6, 7, "#fff6d0", 0)
    d += line((-3, -14), (-6, -9), "#ffffff", 1.4, 0.0)
    info = write_svg("props/glowstick.svg", (-18, -24, 18, 44), d)
    sp["glowstick"] = {"file": "source/props/glowstick.svg", "pivot": pivot_in(info, (0, 38)), "px_scale": 0.5, "length": 36}


def spr_door_open():
    """The ward door swung open onto the bright corridor (overlay for the `doorway` at 336, 146, 62 x 116): warm light, a staff
    member with a tea trolley arriving, leaves swung in and a pool of light on the floor. Origin = doorway - (40, 0)."""
    ox, oy = 296, 146
    dx, dy, dw, dh = 40, 0, 62, 116
    defs = lin_grad("spill", [(0, "#fff2c8", 0.7), (0.55, "#ffe0a0", 0.25), (1, "#ffe0a0", 0.0)], 0, 0, 0, 1)
    defs += lin_grad("room", [(0, "#fffbe8"), (1, "#ffe9b8")], 0, 0, 0, 1)
    d = poly([(dx - 4, dy + dh), (dx + dw + 4, dy + dh), (dx + dw + 54, dy + dh + 84), (dx - 54, dy + dh + 84)], "url(#spill)")
    d += rect(dx - 6, dy - 5, dw + 12, dh + 5, "#fbfbff", OUT, 3)
    d += rect(dx, dy, dw, dh, "url(#room)", None)
    d += rect(dx + 10, dy + 22, dw - 20, dh - 22, "#ffffff", None, op=0.5)
    # the corridor beyond: far doors and a floor stripe
    for k, xx in enumerate((dx + 14, dx + dw - 22)):
        d += rect(xx, dy + 54, 8, 40, "#d8c8f0", OUT, 1.2)
    d += rect(dx + 2, dy + dh - 14, dw - 4, 14, "#cdeee0", None, op=0.8)
    # a friendly figure in scrubs pushing a tea trolley
    cx = dx + dw / 2
    d += rect(cx - 12, dy + 64, 24, 30, "#5fc9bb", OUT, 1.6, rx=6) + circle(cx, dy + 56, 7.4, "#e6aa7a", OUT, 1.6)
    d += path(f"M{f(cx - 7)} {f(dy + 54)} Q{f(cx)} {f(dy + 46)} {f(cx + 7)} {f(dy + 54)}", None, "#2a1b3e", 3)
    d += circle(cx - 2.6, dy + 57, 1.0, "#2a1b4e") + circle(cx + 2.6, dy + 57, 1.0, "#2a1b4e") + path(f"M{f(cx - 3)} {f(dy + 60)} Q{f(cx)} {f(dy + 62.5)} {f(cx + 3)} {f(dy + 60)}", None, "#7a1f45", 1.2)
    d += rect(cx + 10, dy + 82, 20, 14, "#fff4dc", OUT, 1.6, rx=2) + circle(cx + 14, dy + 99, 2.6, "#7a6a8a", OUT, 1) + circle(cx + 26, dy + 99, 2.6, "#7a6a8a", OUT, 1)
    d += circle(cx + 20, dy + 80, 3, "#ff8f8a", OUT, 1)
    for sg, x0 in ((-1, dx), (1, dx + dw)):  # the door leaves swung in
        leaf = [(x0, dy + 2), (x0 - sg * 14, dy + 9), (x0 - sg * 14, dy + dh - 4), (x0, dy + dh)]
        d += poly(leaf, "#e9c58f", OUT, 2.2) + line((x0 - sg * 7, dy + 12), (x0 - sg * 7, dy + dh - 6), "#ffffff", 1.2, 0.4)
        d += circle(x0 - sg * 7, dy + 36, 3.6, "#e8f7ff", OUT, 1.2)
        d += line((x0, dy + 30), (x0 - sg * 14, dy + 32), "#a8743c", 3.0)
    d += rect(dx + 14, dy - 22, dw - 28, 11, "#f0eefb", OUT, 2, rx=3) + paper_star(dx + dw / 2, dy - 16.5, 4, BUTTER, 1.0)  # a small sign plaque
    info = write_svg("props/door_open.svg", (0, -8, 150, 214), d, defs)
    return {"file": "source/props/door_open.svg", "pivot": pivot_in(info, (0, -8)), "px_scale": 0.5, "pos": [ox, oy - 8]}


def deck_sprites(sp):
    """Night One's deck pieces drawn through the palette remap, with the ward's own desk top."""
    from . import mh_stage
    old_w = S.write_svg

    def w_(rel, box, body, defs=""):
        return lib.write_svg(rel, box, remap(body), remap(defs))
    S.write_svg = w_
    try:
        S.spr_deck(sp)
    finally:
        S.write_svg = old_w


# ---- PNG sprites -----------------------------------------------------------------------------------------------------------

def confetti_png():
    """Four 32 x 32 frames of pastel paper confetti: a rectangle, a circle punch-out, a star and a streamer curl."""
    cols = [(255, 143, 138), (127, 207, 143), (255, 217, 102), (169, 148, 222)]
    k = 4
    big = Image.new("RGBA", (128 * k, 32 * k), (0, 0, 0, 0))
    dr = ImageDraw.Draw(big)
    ink = (42, 27, 78, 255)
    cx0 = 16 * k
    ang = math.radians(25)
    pts = [(cx0 + sx * math.cos(ang) - sy * math.sin(ang), 16 * k + sx * math.sin(ang) + sy * math.cos(ang)) for sx, sy in ((-11 * k, -6 * k), (11 * k, -6 * k), (11 * k, 6 * k), (-11 * k, 6 * k))]
    dr.polygon(pts, fill=cols[0] + (255,), outline=ink)
    dr.ellipse([(48 - 9) * k, (16 - 9) * k, (48 + 9) * k, (16 + 9) * k], fill=cols[1] + (255,), outline=ink, width=k)
    dr.ellipse([(48 - 3) * k, (16 - 3) * k, (48 + 3) * k, (16 + 3) * k], fill=(0, 0, 0, 0))
    star = [(80 * k + math.cos(math.radians(-90 + i * 36)) * (12 if i % 2 == 0 else 5.2) * k, 16 * k + math.sin(math.radians(-90 + i * 36)) * (12 if i % 2 == 0 else 5.2) * k) for i in range(10)]
    dr.polygon(star, fill=cols[2] + (255,), outline=ink)
    for i in range(14):  # a streamer curl
        a = i * 0.45
        x = 112 * k + math.cos(a) * (3 + i * 0.7) * k
        y = 16 * k + math.sin(a) * (3 + i * 0.7) * k
        dr.ellipse([x - 2.6 * k, y - 2.6 * k, x + 2.6 * k, y + 2.6 * k], fill=cols[3] + (255,))
    small = big.resize((128, 32), Image.LANCZOS)
    os.makedirs(lib.PNG_DIR, exist_ok=True)
    small.save(os.path.join(lib.PNG_DIR, "confetti.png"), compress_level=9)
    return {"file": "processed/confetti.png", "pivot": [16, 16], "px_scale": 1.0, "frames": 4, "frame_size": [32, 32], "note": "paper confetti"}


def _white_png(name, a, rgb=(255, 255, 255)):
    h, w = a.shape
    return _save_rgba(name, np.dstack([np.full((h, w), float(rgb[0])), np.full((h, w), float(rgb[1])), np.full((h, w), float(rgb[2])),
                                       np.clip(a, 0, 1) * 255]))


def build_png_sprites():
    """The white lighting sprites, re-weighted for a pale pastel ward: the runtime draws beams, pools and glows additively over
    light walls, so every light sprite here carries far less alpha than Night One's (which lights a dark club) and keeps its brightness
    in a narrow core, so a beam reads as coloured light rather than a white smear across the room."""
    sp = png_sprites.build_png_sprites()  # glow, beam, spot_pool, haze_a/b, vignette, confetti (white lighting sprites)
    # beam: a slim soft cone, bright near the lamp and dying out well before the floor; the edges are only a whisper
    w, h = 256, 640
    yy, xx = np.mgrid[0:h, 0:w]
    half = 6 + yy * (112.0 / h)
    t = np.abs(xx - w / 2 + 0.5) / half
    edge = np.clip(1 - t ** 1.5, 0, 1)
    core = np.clip(1 - t * 1.6, 0, 1) ** 2.0
    fade = np.clip(1 - yy / h, 0, 1) ** 1.35
    a = (0.2 * edge + 0.5 * core) * fade
    a[:10] *= np.linspace(0.25, 1, 10)[:, None]
    sp["beam"] = {"file": _white_png("beam.png", a), "pivot": [w / 2, 0], "px_scale": 1.0, "length": h, "half_width_at_end": 118,
                  "note": "dimmer than Night One's: additive over pale walls"}
    # spot pool: a soft lit oval with a gentle rim; dim centre so the dancer standing in it keeps their colours
    w, h = 400, 140
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h / 2 + 0.5) / (h / 2))
    a = np.clip(1 - r ** 2, 0, 1) ** 1.5 * 0.3 + np.exp(-((r - 0.86) / 0.08) ** 2) * 0.22 * (r < 1.0)
    a = a * (0.45 + 0.55 * _smooth((yy + 0.5) / h * 1.4 - 0.2))
    sp["spot_pool"] = {"file": _white_png("spot_pool.png", a), "pivot": [w / 2, h / 2], "px_scale": 1.0}
    # (glow stays Night One's: the runtime also draws the dancers' contact shadows with it, and those need its full strength)
    # haze: thin lilac-grey drifts (normal blend): a mid-tone veil that adds depth to a bright room instead of whitening it
    for name, seed, sx, sy in (("haze_a", 21, 70.0, 16.0), ("haze_b", 77, 54.0, 12.0)):
        w, h = 640, 100
        n1 = png_sprites.periodic_noise(w, h, sx, sy, seed)
        n2 = png_sprites.periodic_noise(w, h, sx * 0.45, sy * 0.45, seed + 1)
        m = _smooth((0.65 * n1 + 0.35 * n2 - 0.4) / 0.42)
        env = np.sin(np.linspace(0, np.pi, h)) ** 1.6
        sp[name] = {"file": _white_png(name + ".png", m * env[:, None] * 0.42, (196, 186, 236)), "pivot": [w / 2, h / 2], "px_scale": 2.0,
                    "tileable_x": True}
    w, h = 640, 360
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h / 2 + 0.5) / (h / 2))
    a = _smooth((r - 0.62) / 0.6) * 0.55  # a gentle plum vignette: frames the bright room without dirtying it
    sp["vignette"] = {"file": _save_rgba("vignette.png", np.dstack([np.full((h, w), 40.0), np.full((h, w), 28.0), np.full((h, w), 70.0), a * 255])),
                      "pivot": [w / 2, h / 2], "px_scale": 2.0}
    sp["confetti"] = confetti_png()
    return sp


def build_sprites():
    sp = {}
    deck_sprites(sp)
    sp["door_open"] = spr_door_open()
    spr_woofer(sp)
    spr_fixture(sp)
    spr_disco_ball(sp)
    spr_glowstick(sp)
    sp.update(build_png_sprites())
    return sp


# ---- silhouettes -----------------------------------------------------------------------------------------------------------

def _sil_shape(kind, up):
    s = ""
    if kind == "a":  # a king: paper crown, fluffy hair and a wide dressing gown
        s += path("M-42 0 L-40 -26 Q-36 -44 -14 -48 Q-8 -50 -8 -57 L8 -57 Q8 -50 14 -48 Q36 -44 40 -26 L42 0 Z", "#fff")
        s += ellipse(0, -74, 17, 19, "#fff") + circle(-19, -76, 8, "#fff") + circle(19, -76, 8, "#fff")
        s += poly([(-16, -88), (-16, -104), (-8, -96), (0, -110), (8, -96), (16, -104), (16, -88)], "#fff")
    elif kind == "b":  # a chef: tall pleated toque
        s += path("M-36 0 L-34 -26 Q-32 -44 -13 -48 Q-8 -50 -8 -57 L8 -57 Q8 -50 13 -48 Q32 -44 34 -26 L36 0 Z", "#fff")
        s += ellipse(0, -73, 16, 18, "#fff")
        s += path("M-15 -84 L-16 -98 C-34 -102 -30 -128 -10 -124 C-6 -138 8 -138 10 -124 C30 -128 34 -102 16 -98 L15 -84 Z", "#fff")
    else:  # a pirate in a tricorn with a feather, and a parrot
        s += path("M-40 0 L-38 -24 Q-34 -46 -14 -49 Q-10 -50 -10 -57 L10 -57 Q10 -50 14 -49 Q34 -46 38 -24 L40 0 Z", "#fff")
        s += ellipse(0, -74, 17, 19, "#fff")
        s += path("M-32 -86 Q-30 -104 -12 -108 L-5 -118 Q0 -121 5 -118 L12 -108 Q30 -104 32 -86 Q0 -78 -32 -86 Z", "#fff")
        s += path("M22 -104 C40 -108 44 -86 38 -70 C32 -84 28 -92 22 -104 Z", "#fff")
        s += circle(-40, -50, 8, "#fff") + path("M-46 -44 L-54 -30 L-44 -36 Z", "#fff")
    if up:
        for sx in (-1, 1):
            s += line((sx * 26, -40), (sx * 46, -118), "#fff", 13)
            s += circle(sx * 47, -122, 8, "#fff")
    return s


def build_silhouettes():
    out = {}
    # soft mid-tone lilac and slate figures (not black cut-outs: in a bright ward the far crowd is simply in softer light), with a
    # mint rim from the left, a peach rim from the right and a faint lighter top where the ceiling light lands
    fills = {"a": "#b4a4da", "b": "#a4aed8", "c": "#bca6d2"}  # the runtime multiplies these by a lilac tint (0.55..0.78)
    for kind in ("a", "b", "c"):
        entry = {}
        for state in ("idle", "up"):
            up = state == "up"
            shape = _sil_shape(kind, up)
            body = ""
            for dx, dy, col in ((-2.6, -1.4, "#b8fff0"), (2.6, -1.4, "#ffd2b8")):  # mint from the left, warm from the right
                body += S._recolor(shape, col, dx, dy)
            body += S._recolor(shape, fills[kind], 0, 0)
            body += S._recolor(shape, lighten(fills[kind], 0.18), 0, 0).replace("<g ", '<g opacity="0.55" clip-path="url(#topband)" ', 1)
            body += S._recolor(shape, darken(fills[kind], 0.16), 0, 0).replace("<g ", '<g opacity="0.6" clip-path="url(#lowband)" ', 1)
            sdefs = clip("topband", '<rect x="-90" y="-150" width="180" height="70"/>') + clip("lowband", '<rect x="-90" y="-26" width="180" height="40"/>')
            info = write_svg(f"silhouettes/sil_{kind}_{state}.svg", (-84, -146 if up else -140, 84, 4), body, sdefs)
            entry[state] = {"file": f"source/silhouettes/sil_{kind}_{state}.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
        entry["height"] = 110
        out[f"sil_{kind}"] = entry
    return out


# ---- interlude -------------------------------------------------------------------------------------------------------------

def spr_cell_door(sp):
    """A plain, friendly ward door in a pale frame (no bars, no lock plate): a painted wooden leaf with a round porthole window,
    paper stars and a brass handle. Four sprites share one 320 x 440 design-px footprint, all pivoted at the bottom centre
    (the door's foot on the floor): `cell_door` the closed door (frame + leaf), `cell_door_frame` the frame with a transparent
    opening, `cell_door_leaf` the leaf alone with its pivot at the HINGE (bottom-left), `cell_door_open` the leaf swung inward."""
    w, h = 320, 440
    fx, fy, fw, fh = 40, 36, 240, 404  # frame outer
    ox, oy, ow, oh = 66, 62, 188, 378  # opening
    col = "#f0cf98"
    defs = lin_grad("dleaf", [(0, lighten(col, 0.2)), (1, darken(col, 0.08))], 0, 0, 1, 0)
    defs += lin_grad("dframe", [(0, "#ffffff"), (1, "#e4e0f6")], 0, 0, 0, 1)

    def frame_svg():
        o = rect(fx, fy, fw, fh, "url(#dframe)", OUT, 4, rx=4)
        o += rect(ox - 4, oy - 4, ow + 8, oh + 4, "#d8d2ee", OUT, 3)
        o += rect(ox, oy, ow, oh, "#ffffff", None, op=0.0)
        o += line((fx + 10, fy + 8), (fx + fw - 10, fy + 8), "#ffffff", 3, 0.7)
        return o

    def leaf_svg(x, y, wd, ht):
        o = rect(x, y, wd, ht, "url(#dleaf)", OUT, 3.4)
        o += rect(x + wd * 0.1, y + ht * 0.07, wd * 0.8, ht * 0.4, darken(col, 0.06), OUT, 2, rx=4, op=0.6)
        o += rect(x + wd * 0.1, y + ht * 0.53, wd * 0.8, ht * 0.38, darken(col, 0.06), OUT, 2, rx=4, op=0.6)
        o += circle(x + wd / 2, y + ht * 0.25, wd * 0.2, "#e8f7ff", OUT, 3.4) + circle(x + wd / 2, y + ht * 0.25, wd * 0.14, "#bfe6ff", None)
        o += path(f"M{f(x + wd * 0.38)} {f(y + ht * 0.2)} Q{f(x + wd * 0.44)} {f(y + ht * 0.13)} {f(x + wd * 0.5)} {f(y + ht * 0.16)}", None, "#ffffff", 2.4, sop=0.85)
        o += paper_star(x + wd * 0.5, y + ht * 0.66, wd * 0.14, BUTTER, 2) + paper_star(x + wd * 0.26, y + ht * 0.8, wd * 0.07, CORAL, 1.4) + paper_star(x + wd * 0.74, y + ht * 0.78, wd * 0.07, "#8fd9c8", 1.4)
        o += circle(x + wd * 0.86, y + ht * 0.55, 6, "#d8b24a", OUT, 1.8) + rect(x + wd * 0.78, y + ht * 0.47, wd * 0.12, ht * 0.06, "#d8b24a", OUT, 1.4, rx=2)
        o += line((x + 4, y + ht * 0.04), (x + 4, y + ht * 0.96), "#ffffff", 2.4, 0.4)
        return o

    info = write_svg("interlude/cell_door.svg", (0, 0, w, h), frame_svg() + leaf_svg(ox, oy, ow, oh), defs)
    sp["cell_door"] = {"file": "source/interlude/cell_door.svg", "pivot": pivot_in(info, (w / 2, h)), "px_scale": 0.5, "blend": "mix",
                       "note": "closed ward door, frame + leaf; 320 x 440 design px at px_scale 0.5 (drawn at 1x it stands 440 px tall, its foot at anchors.door_centre), pivot bottom centre"}
    # frame alone: a transparent opening (evenodd) so the new room shows through
    hole = f"M{fx} {fy} H{fx + fw} V{fy + fh} H{fx} Z M{ox} {oy} H{ox + ow} V{oy + oh} H{ox} Z"
    fr = f'<path d="{hole}" fill="url(#dframe)" fill-rule="evenodd"/>' + path(f"M{fx} {fy} H{fx + fw} V{fy + fh} H{fx} Z", None, OUT, 4) + rect(ox, oy, ow, oh, None, OUT, 3)
    fr += rect(ox - 4, oy - 4, ow + 8, 4, "#d8d2ee", OUT, 2) + line((fx + 10, fy + 8), (fx + fw - 10, fy + 8), "#ffffff", 3, 0.7)
    info = write_svg("interlude/cell_door_frame.svg", (0, 0, w, h), fr, defs)
    sp["cell_door_frame"] = {"file": "source/interlude/cell_door_frame.svg", "pivot": pivot_in(info, (w / 2, h)), "px_scale": 0.5, "blend": "mix",
                             "note": "the frame only, transparent opening, same footprint as cell_door"}
    # leaf alone, hinge at the bottom-left of its own texture
    info = write_svg("interlude/cell_door_leaf.svg", (0, 0, ow + 8, oh + 8), leaf_svg(4, 4, ow, oh), defs)
    sp["cell_door_leaf"] = {"file": "source/interlude/cell_door_leaf.svg", "pivot": pivot_in(info, (4, 4 + oh)), "px_scale": 0.5, "blend": "mix",
                            "note": "the door leaf alone, 188 x 378 design px; pivot at the hinge foot (bottom-left) so it can be scaled in x to swing"}
    # the leaf swung inward: foreshortened to 38% width with a perspective skew, hinge on the left
    sw_ = ow * 0.36
    sk = 22
    pts_ = [(0, sk), (sw_, 0), (sw_, oh), (0, oh - sk)]
    op_ = poly(pts_, "url(#dleaf)", OUT, 3.4)
    op_ += poly([(sw_ * 0.18, sk * 0.82 + 10), (sw_ * 0.82, 8), (sw_ * 0.82, oh * 0.46), (sw_ * 0.18, oh * 0.46 - sk * 0.2)], darken(col, 0.06), OUT, 1.6, op=0.6)
    op_ += circle(sw_ * 0.56, oh * 0.25, sw_ * 0.17, "#e8f7ff", OUT, 2.6) + circle(sw_ * 0.86, oh * 0.55, 4, "#d8b24a", OUT, 1.6)
    info = write_svg("interlude/cell_door_open.svg", (-4, -4, sw_ + 6, oh + 6), op_, defs)
    sp["cell_door_open"] = {"file": "source/interlude/cell_door_open.svg", "pivot": pivot_in(info, (0, oh)), "px_scale": 0.5, "blend": "mix",
                            "note": "the leaf swung open (foreshortened), hinge-foot pivot at the left; place at the frame's left jamb foot"}


def spr_flicker_tube(sp):
    """A fluorescent ceiling tube in its housing with a soft halo: 360 x 40 design px, centre pivot. White/mint so it can be tinted
    and drawn additively; fade its alpha to flicker."""
    w, h = 360, 44
    defs = lin_grad("tube", [(0, "#ffffff"), (0.5, "#f0fffa"), (1, "#c9eee4")], 0, 0, 0, 1)
    defs += lin_grad("halo", [(0, "#dffff4", 0.0), (0.5, "#dffff4", 0.55), (1, "#dffff4", 0.0)], 0, 0, 0, 1)
    d = rect(2, 2, w - 4, h - 4, "url(#halo)", None, rx=18, op=0.55)
    d += rect(14, 10, w - 28, 24, "#dfe6ee", OUT, 3, rx=4)  # housing
    d += rect(26, 14, w - 52, 16, "url(#tube)", OUT, 2, rx=8)
    d += rect(34, 17, w - 68, 4, "#ffffff", None, rx=2, op=0.95)
    for xx in (22, w - 22):
        d += rect(xx - 6, 12, 12, 20, "#8a96aa", OUT, 2, rx=2)
    d += line((40, 26), (w - 40, 26), "#bfeadf", 1.6, 0.6)
    info = write_svg("interlude/flicker_tube.svg", (0, 0, w, h), d, defs)
    sp["flicker_tube"] = {"file": "source/interlude/flicker_tube.svg", "pivot": pivot_in(info, (w / 2, h / 2)), "px_scale": 0.5, "blend": "add",
                          "note": "a fluorescent tube in its housing; flicker its alpha"}


def build_interlude():
    sp = {}
    # fluoro wash: 320 x 180 shown at 1280 x 720, a cold mint-white with faint banding like tube light on a ceiling
    w, h = 320, 180
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h / 2 + 0.5) / (h / 2))
    band = 0.04 * np.sin(yy * 0.9) * (1 - _smooth(r - 0.2))
    a = np.clip(0.62 + 0.3 * _smooth(1.0 - r) + band, 0, 1)
    col = np.dstack([np.full((h, w), 226.0) + 20 * (1 - r).clip(0, 1), np.full((h, w), 255.0), np.full((h, w), 244.0), a * 255])
    sp["fluoro_wash"] = {"file": _save_rgba("fluoro_wash.png", col), "pivot": [w / 2, h / 2], "px_scale": 4.0, "blend": "mix",
                         "note": "cold mint-white wash, full screen at px_scale 4; fade its alpha"}
    # tunnel vignette: 640 x 360 shown at 1280 x 720, clear in the middle and closing to deep teal-navy at the edges
    w, h = 640, 360
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h / 2 + 0.5) / (h / 2))
    a = _smooth((r - 0.28) / 0.62) * 0.97
    arr = np.dstack([np.full((h, w), 10.0), np.full((h, w), 20.0), np.full((h, w), 34.0), a * 255])
    sp["tunnel_vignette"] = {"file": _save_rgba("tunnel_vignette.png", arr), "pivot": [w / 2, h / 2], "px_scale": 2.0, "blend": "mix",
                             "note": "a soft dark tunnel; scale it down from 2x to 1x about its centre to close in"}
    spr_cell_door(sp)
    spr_flicker_tube(sp)
    anchors = {"door_centre": [640, 440], "door_opening": [546, 62, 188, 378], "tube_row": [[250, 40], [640, 40], [1030, 40]]}
    return {"sprites": sp, "anchors": anchors,
            "note": "cell_door is a friendly ward door (pastel frame, porthole, paper stars): swing it open (cell_door_leaf scaled in x, or cell_door_open) to reveal the day room"}
