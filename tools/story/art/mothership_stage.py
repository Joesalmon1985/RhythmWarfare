"""The `mothership` chapter's set: an alien ship's ring-shaped rave deck seen from the DJ's eye line.

Same camera and perspective as Night One (vanishing point (640, 130), far wall x 270..1010, y 52..262) so the runtime's floor rows,
crowd scaling and anchors behave identically; everything else is re-themed: a huge viewing window onto space and a ringed planet in
the far wall, a glowing hex floor, hanging tech pylons, resonator columns instead of speakers, an alien bar, an airlock, a hover-
platform riser, a bio-tech console. SVG for shapes, Pillow PNGs for soft light (shared with Night One via sprites.py).
Also writes the `stage.pieces` set pieces and the `interlude` sprites (a UFO that crashes the Night One club).
"""
from __future__ import annotations

import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw

from . import lib
from .lib import (OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, pivot_in, poly, rad_grad, rect,
                  write_svg)
from .stage import (FLOOR_ROWS, FX0, FX1, FY0, FY1, H, SPK_H, SPK_POS, SPK_W, SPK_WOOFERS, VPX, VPY, W, _recolor, floor_x, lwall_y,
                    rwall_y, truss)

CYAN, GREEN, MAG, VIO, AMB = "#19e6ff", "#4ff0a8", "#ff2f9d", "#8a5cff", "#ffc23f"
HULL0, HULL1, HULL2, HULL3 = "#050b24", "#0d1a4a", "#1c3478", "#3a5cb8"

LED = (460, 150, 360, 58)
WIN = (372, 62, 560, 144)  # the viewing window (x, y, w, h)
PLANET = (880, 130, 60)  # cx, cy, r in design px


def neon(p1, p2, color, w=2.0, glow=1.0) -> str:
    out = ""
    for mul, op in ((7.0, 0.05), (4.4, 0.09), (2.6, 0.16)):
        out += line(p1, p2, color, w * mul, op * glow)
    out += line(p1, p2, color, w) + line(p1, p2, lighten(color, 0.65), w * 0.38, 0.9)
    return out


def neon_path(d: str, color: str, w=2.0, glow=1.0) -> str:
    out = ""
    for mul, op in ((7.0, 0.05), (4.4, 0.09), (2.6, 0.16)):
        out += path(d, None, color, w * mul, sop=op * glow)
    return out + path(d, None, color, w) + path(d, None, lighten(color, 0.65), w * 0.38, sop=0.9)


def glyph(cx, cy, s, color, seed, op=1.0) -> str:
    """A little made-up alien glyph: a few strokes, dots and a ring."""
    r = random.Random(seed)
    out = ""
    kind = r.randrange(4)
    if kind == 0:
        out += circle(cx, cy, s * 0.5, None, color, 1.6, sop=op) + line((cx - s * 0.5, cy), (cx + s * 0.5, cy), color, 1.6, op)
        out += circle(cx, cy - s * 0.12, s * 0.12, color, None, op=op)
    elif kind == 1:
        out += path(f"M{f(cx - s * 0.5)} {f(cy + s * 0.5)} L{f(cx)} {f(cy - s * 0.5)} L{f(cx + s * 0.5)} {f(cy + s * 0.5)}", None, color, 1.6, sop=op)
        out += line((cx, cy - s * 0.1), (cx, cy + s * 0.5), color, 1.6, op)
    elif kind == 2:
        out += path(f"M{f(cx - s * 0.5)} {f(cy - s * 0.4)} H{f(cx + s * 0.3)} V{f(cy + s * 0.1)} H{f(cx - s * 0.2)} V{f(cy + s * 0.5)}", None, color, 1.6, sop=op)
        out += circle(cx + s * 0.4, cy + s * 0.4, s * 0.1, color, None, op=op)
    else:
        out += path(f"M{f(cx - s * 0.5)} {f(cy)} Q{f(cx)} {f(cy - s * 0.9)} {f(cx + s * 0.5)} {f(cy)}", None, color, 1.6, sop=op)
        out += line((cx - s * 0.3, cy + s * 0.2), (cx + s * 0.3, cy + s * 0.2), color, 1.6, op)
        out += circle(cx, cy + s * 0.45, s * 0.1, color, None, op=op)
    return out


def hexagon(cx, cy, r, rot=30):
    return [(cx + r * math.cos(math.radians(rot + 60 * k)), cy + r * math.sin(math.radians(rot + 60 * k))) for k in range(6)]


# ---- backdrop ------------------------------------------------------------------------------------------------------------------

def space_window() -> tuple[str, str]:
    """Stars, nebula, a ringed planet and a moon, clipped to the window; returns (defs, body)."""
    wx, wy, ww, wh = WIN
    rng = random.Random(41)
    defs = lin_grad("sp", [(0, "#04051a"), (0.6, "#0a0d36"), (1, "#14104a")], 0, 0, 0, 1)
    defs += clip("winclip", rect(wx, wy, ww, wh, rx=26))
    defs += rad_grad("neb1", [(0, MAG, 0.34), (1, MAG, 0.0)])
    defs += rad_grad("neb2", [(0, CYAN, 0.26), (1, CYAN, 0.0)])
    defs += rad_grad("neb3", [(0, VIO, 0.3), (1, VIO, 0.0)])
    pcx, pcy, pr = PLANET
    defs += rad_grad("planet", [(0, "#ffd9a8"), (0.35, "#ff7ab8"), (0.75, "#7a3fd0"), (1, "#1a0f4a")], 0.32, 0.3, 0.85)
    defs += rad_grad("atmo", [(0.8, CYAN, 0.0), (0.93, CYAN, 0.45), (1, CYAN, 0.0)])
    defs += clip("pclip", circle(pcx, pcy, pr))
    defs += rad_grad("moon", [(0, "#ffffff"), (0.6, "#bcd2ff"), (1, "#5b72b8")], 0.35, 0.3, 0.8)
    b = rect(wx, wy, ww, wh, "url(#sp)")
    inner = ellipse(wx + 140, wy + 60, 220, 90, "url(#neb1)") + ellipse(wx + 330, wy + 110, 260, 80, "url(#neb2)") + ellipse(wx + 460, wy + 30, 200, 80, "url(#neb3)")
    for _ in range(120):
        x, y = wx + rng.random() * ww, wy + rng.random() * wh
        r = rng.choice((0.7, 0.8, 1.0, 1.0, 1.3, 1.7))
        inner += circle(x, y, r, rng.choice(("#ffffff", "#cfe9ff", "#ffe7c8", "#ffd0ee")), None, op=rng.choice((0.5, 0.7, 0.9, 1.0)))
    for _ in range(8):  # bigger twinkles
        x, y = wx + rng.random() * ww, wy + rng.random() * wh * 0.8
        inner += line((x - 4, y), (x + 4, y), "#ffffff", 0.9, 0.8) + line((x, y - 4), (x, y + 4), "#ffffff", 0.9, 0.8)
    # moon
    inner += circle(wx + 86, wy + 46, 16, "url(#moon)") + circle(wx + 91, wy + 42, 15, "#2a3a80", None, op=0.35)
    # planet with rings (back half), body, bands, terminator, rings (front half), atmosphere
    ring = lambda a, b_: f"M{pcx - 1.7 * pr} {pcy + 6} A{1.7 * pr} {0.32 * pr} -14 0 {a} {pcx + 1.7 * pr} {pcy - 6}"
    inner += path(ring(1, 0), None, "#ffd9f0", 6, sop=0.5)
    pl = circle(pcx, pcy, pr, "url(#planet)")
    bands = ""
    for k in range(-4, 5):
        yy = pcy + k * pr * 0.2
        bands += path(f"M{pcx - pr} {f(yy)} Q{pcx} {f(yy + 8)} {pcx + pr} {f(yy - 3)}", None, ["#ffffff", "#c8a0ff", "#ffb0d8", "#7ad8ff"][k % 4], 5.5, sop=0.16)
    pl += group(bands, 'clip-path="url(#pclip)"')
    pl += group(circle(pcx + pr * 0.55, pcy + pr * 0.35, pr * 1.05, "#05061c", None, op=0.55), 'clip-path="url(#pclip)"')
    inner += pl + circle(pcx, pcy, pr * 1.06, "url(#atmo)")
    inner += path(f"M{pcx - 1.7 * pr} {pcy + 6} A{1.7 * pr} {0.32 * pr} -14 0 0 {pcx + 1.7 * pr} {pcy - 6}", None, "#ffe4f6", 4.4, sop=0.55)
    b += group(inner, 'clip-path="url(#winclip)"')
    return defs, b


def build_backdrop() -> dict:
    rng = random.Random(23)
    d, defs = "", ""
    defs += lin_grad("bg", [(0, "#03061a"), (0.5, "#0a1240"), (1, "#050a26")], 0, 0, 0, 1)
    d += rect(0, 0, W, H, "url(#bg)")
    # ceiling: dark hull with converging seams and big arch ribs
    defs += lin_grad("ceil", [(0, "#02040f"), (1, "#14246a")], 0, 0, 0, 1)
    d += poly([(0, -6), (W, -6), (FX1, FY0), (FX0, FY0)], "url(#ceil)")
    for k in range(-8, 9):
        xf = VPX + k * 46.0
        if FX0 <= xf <= FX1:
            xt = VPX + (xf - VPX) * (-6 - VPY) / (FY0 - VPY)
            d += line((xf, FY0), (xt, -6), "#2a4aa8", 1.5, 0.5)
    for yy in (14, 28, 40):
        xl = VPX - (VPX - FX0) * (VPY - yy) / (VPY - FY0)
        xr = VPX + (FX1 - VPX) * (VPY - yy) / (VPY - FY0)
        d += line((xl, yy), (xr, yy), "#2a4aa8", 1.6, 0.6)
        d += line((xl, yy + 2), (xr, yy + 2), CYAN, 0.9, 0.18)
    # far wall hull
    defs += lin_grad("fw", [(0, "#1a2c70"), (0.5, "#0f1c52"), (1, "#080f36")], 0, 0, 0, 1)
    d += rect(FX0, FY0, FX1 - FX0, FY1 - FY0, "url(#fw)")
    for x in range(int(FX0) + 6, int(FX1), 22):  # vertical panel seams
        d += rect(x, FY0, 2.2, FY1 - FY0, "#030718", None, op=0.55) + rect(x + 2.2, FY0, 1.2, FY1 - FY0, CYAN, None, op=0.07)
    # window
    wdefs, wbody = space_window()
    defs += wdefs
    wx, wy, ww, wh = WIN
    d += rect(wx - 12, wy - 12, ww + 24, wh + 24, "#1a2c70", OUT, 3.6, rx=34)
    d += wbody
    d += rect(wx, wy, ww, wh, None, OUT, 3, rx=26)
    d += rect(wx - 6, wy - 6, ww + 12, wh + 12, None, CYAN, 1.2, rx=30, sop=0.7)
    for sx in (432, 872):  # frame struts
        d += rect(sx - 4, wy - 2, 8, wh + 4, "#14226a", OUT, 2.2) + line((sx - 1.2, wy), (sx - 1.2, wy + wh), "#7aa0ff", 1.2, 0.5)
    for k in range(14):  # frame rivets / lights
        x = wx + 18 + k * (ww - 36) / 13
        d += circle(x, wy - 6, 1.7, GREEN if k % 3 == 0 else "#8aa6ff", None, op=0.9)
    # console ledge under the window with emitters
    d += rect(354, 206, 590, 56, "#0a1442", OUT, 3) + rect(354, 206, 590, 8, "#2a4aa8", OUT, 2.2)
    d += rect(362, 224, 574, 30, "#030718", None, op=0.6, rx=3)
    for k in range(18):
        x = 372 + k * 31.5
        d += rect(x, 232, 20, 5, [CYAN, GREEN, MAG, AMB][k % 4], None, op=0.4 + 0.5 * ((k * 7) % 3 == 0), rx=2)
        d += glyph(x + 10, 246, 6, "#8aa6ff", k, 0.55)
    d += neon((354, 261), (944, 261), GREEN, 1.6, 1.0)
    # LED screen frame (empty panel for the runtime)
    lx, ly, lw_, lh = LED
    d += rect(lx - 12, ly - 12, lw_ + 24, lh + 24, "#162a78", OUT, 3.6, rx=10)
    d += rect(lx - 6, ly - 6, lw_ + 12, lh + 12, "#050b24", OUT, 2, rx=5)
    d += rect(lx, ly, lw_, lh, "#04061a", None)
    d += neon((lx - 12, ly - 12), (lx + lw_ + 12, ly - 12), CYAN, 1.2, 0.9) + neon((lx - 12, ly + lh + 12), (lx + lw_ + 12, ly + lh + 12), MAG, 1.2, 0.9)
    for cx_, cy_ in ((lx - 6, ly - 6), (lx + lw_ + 6, ly - 6), (lx - 6, ly + lh + 6), (lx + lw_ + 6, ly + lh + 6)):
        d += hex_bolt(cx_, cy_, 3.4)
    for x in (lx + 60, lx + lw_ - 60):  # hanging cables from the ceiling truss to the screen
        d += line((x, 56), (x, ly - 12), OUT, 4.5) + line((x, 56), (x, ly - 12), "#4a6ad0", 1.8)
    # airlock, closed: a round-topped hatch in a heavy frame with a hazard band and a ring light
    dx, dy, dw, dh = 284, 138, 70, 124
    d += rect(dx - 8, dy - 8, dw + 16, dh + 8, "#162a78", OUT, 3, rx=10)
    d += rect(dx, dy, dw, dh, "#030718")
    defs += lin_grad("hatch", [(0, "#3a5cb8"), (1, "#14226a")], 0, 0, 1, 0)
    d += rect(dx + 3, dy + 3, dw / 2 - 4, dh - 3, "url(#hatch)", OUT, 2, rx=3) + rect(dx + dw / 2 + 1, dy + 3, dw / 2 - 4, dh - 3, "url(#hatch)", OUT, 2, rx=3)
    d += circle(dx + dw / 2, dy + 50, 17, "#0a1442", OUT, 2.4) + circle(dx + dw / 2, dy + 50, 12, None, GREEN, 1.8, sop=0.9)
    for k in range(6):
        a = k * math.tau / 6
        d += line((dx + dw / 2 + math.cos(a) * 12, dy + 50 + math.sin(a) * 12), (dx + dw / 2 + math.cos(a) * 17, dy + 50 + math.sin(a) * 17), "#8aa6ff", 1.6)
    for k in range(5):  # hazard stripes at the foot
        d += poly([(dx + 4 + k * 13, dy + dh), (dx + 12 + k * 13, dy + dh), (dx + 18 + k * 13, dy + dh - 12), (dx + 10 + k * 13, dy + dh - 12)], AMB, None, op=0.9)
    d += line((dx + dw / 2, dy + 3), (dx + dw / 2, dy + dh), OUT, 2)
    d += neon((dx - 6, dy - 8), (dx + dw + 6, dy - 8), GREEN, 1.6, 1.0)
    d += rect(dx + 12, dy - 24, dw - 24, 12, "#050b24", OUT, 2, rx=6) + rect(dx + 17, dy - 21, dw - 34, 6, GREEN, None, op=0.95, rx=3)
    # above the airlock: a glyph sign
    d += rect(290, 70, 62, 52, "#050b24", OUT, 2.4, rx=4) + rect(290, 70, 62, 52, MAG, None, op=0.1, rx=4)
    d += glyph(321, 96, 30, MAG, 5) + glyph(305, 112, 8, CYAN, 7) + glyph(337, 112, 8, CYAN, 8)
    # alien bar in an alcove on the right: shelves of glowing vials, a curved counter, hover stools
    bx0, bx1 = 944, 1004
    d += rect(bx0, 140, bx1 - bx0, 122, "#030718", OUT, 2.4, rx=6)
    defs += lin_grad("shelf", [(0, MAG, 0.32), (1, VIO, 0.06)], 0, 0, 0, 1)
    d += rect(bx0 + 2, 142, bx1 - bx0 - 4, 100, "url(#shelf)", rx=5)
    cols = [GREEN, CYAN, MAG, AMB, VIO]
    for sy in (174, 208):
        d += rect(bx0 - 2, sy, bx1 - bx0 + 4, 4, "#3a5cb8", OUT, 1.6)
        x = bx0 + 6
        while x < bx1 - 10:
            c = rng.choice(cols)
            bh, bw = rng.choice((14, 18, 22)), rng.choice((7, 8, 9))
            d += path(f"M{x} {sy} V{sy - bh + 4} Q{x} {sy - bh} {x + bw / 2} {sy - bh} Q{x + bw} {sy - bh} {x + bw} {sy - bh + 4} V{sy} Z", c, OUT, 1.3, op=0.9)
            d += line((x + 2, sy - bh + 5), (x + 2, sy - 3), "#ffffff", 1.1, 0.5)
            x += bw + rng.choice((3, 4, 6))
    d += rect(bx0 - 6, 226, bx1 - bx0 + 12, 36, "#0f1c52", OUT, 3) + rect(bx0 - 6, 226, bx1 - bx0 + 12, 6, "#3a5cb8", OUT, 2.2)
    d += neon((bx0, 258), (bx1, 258), MAG, 1.5, 0.9)
    d += glyph(974, 152, 9, GREEN, 3)
    for sx in (962, 992):
        d += ellipse(sx, 272, 11, 3.6, "#162a78", OUT, 2) + ellipse(sx, 281, 7, 2.2, CYAN, None, op=0.35) + line((sx, 275), (sx, 279), "#5a7ad8", 2)
    # --- floor: a glowing hex plating in perspective (pointy hexes; rows equally spaced on the ground plane)
    floor_poly = [(0, lwall_y(FY1, 0)), (FX0, FY1), (FX1, FY1), (W, rwall_y(FY1, W)), (W, H), (0, H)]
    defs += lin_grad("fl", [(0, "#102058"), (0.3, "#0a1440"), (1, "#050a26")], 0, 0, 0, 1)
    d += poly(floor_poly, "url(#fl)")
    defs += clip("floorclip", poly(floor_poly))
    S, HC, R = 264.0, 1584.0, 0.52
    tiles = ""
    j = 0
    dd = 12.4
    # build rows from the far wall towards the camera; hex centres on the ground plane, depth dd, lateral X
    rows = []
    dcur = 12.2
    while dcur > 2.3:
        rows.append(dcur)
        dcur -= R * 1.5 * 0.0 + 0.0 + (R * 1.5) * (dcur / 12.2) ** 0.0 * 0.62
    cx_c, cy_c, rx_c, ry_c = 640, 372, 250, 46
    for ri, dc in enumerate(rows):
        w_x = math.sqrt(3) * R
        off = 0.5 * w_x if ri % 2 else 0.0
        X = -((640 / S) * dc + 2.0)
        X -= X % w_x
        while X < (640 / S) * dc + 2.0:
            Xc = X + off
            pts_ = [(VPX + (Xc + R * math.cos(math.radians(30 + 60 * k))) * S / (dc + R * 0.62 * math.sin(math.radians(30 + 60 * k))),
                     VPY + HC / (dc + R * 0.62 * math.sin(math.radians(30 + 60 * k)))) for k in range(6)]
            px = VPX + Xc * S / dc
            py = VPY + HC / dc
            X += w_x
            if px < -90 or px > W + 90 or py > H + 60:
                continue
            inside = ((px - cx_c) / rx_c) ** 2 + ((py - cy_c) / ry_c) ** 2
            near = min(1.0, (py - 262) / 300.0)
            h_ = (int(px * 7 + py * 13) * 2654435761) % 997 / 997.0
            if inside < 1.0:
                c, a = (CYAN, 0.34) if h_ < 0.45 else (VIO, 0.36) if h_ < 0.75 else (GREEN, 0.3)
            elif h_ < 0.07:
                c, a = MAG, 0.34
            elif h_ < 0.15:
                c, a = CYAN, 0.26
            elif h_ < 0.2:
                c, a = GREEN, 0.26
            else:
                c, a = "#1c3478", 0.32 + 0.1 * near
            sw = max(0.7, 3.4 / dc)
            tiles += poly(pts_, c, CYAN if inside >= 1.0 else lighten(CYAN, 0.3), sw, op=a,
                          sop=round(min(0.85, 0.28 + 0.4 * (1 - dc / 12.2) + (0.2 if inside < 1.0 else 0)), 2))
    d += group(tiles, 'clip-path="url(#floorclip)"')
    # the lit ring: glow plus ring outlines on the dance circle
    defs += rad_grad("ringglow", [(0, GREEN, 0.32), (0.7, CYAN, 0.12), (1, CYAN, 0.0)])
    d += ellipse(cx_c, cy_c, rx_c + 40, ry_c + 26, "url(#ringglow)")
    d += ellipse(cx_c, cy_c, rx_c, ry_c, None, CYAN, 4, sop=0.1) + ellipse(cx_c, cy_c, rx_c, ry_c, None, lighten(CYAN, 0.4), 1.6, sop=0.8)
    d += ellipse(cx_c, cy_c, rx_c * 0.62, ry_c * 0.62, None, GREEN, 1.2, sop=0.5)
    # floor edge lights under the walls
    d += neon((0, lwall_y(FY1, 0)), (FX0, FY1), GREEN, 2.0, 0.9) + neon((W, rwall_y(FY1, W)), (FX1, FY1), CYAN, 2.0, 0.9)
    # --- side walls: curved hull ribs and portholes
    defs += lin_grad("lw", [(0, "#03061a"), (1, "#16286c")], 0, 0, 1, 0)
    defs += lin_grad("rw", [(0, "#16286c"), (1, "#03061a")], 0, 0, 1, 0)
    lwall = [(0, lwall_y(FY0, 0)), (FX0, FY0), (FX0, FY1), (0, lwall_y(FY1, 0))]
    rwall = [(W, rwall_y(FY0, W)), (FX1, FY0), (FX1, FY1), (W, rwall_y(FY1, W))]
    d += poly(lwall, "url(#lw)") + poly(rwall, "url(#rw)")

    def wy_(side, yfar, x):
        return lwall_y(yfar, x) if side < 0 else rwall_y(yfar, x)

    for side in (-1, 1):
        ribs = []
        for k in range(0, 7):
            x = FX0 * k / 6.0
            ribs.append(x if side < 0 else W - x)
        for x in ribs:
            d += line((x, wy_(side, FY0, x)), (x, wy_(side, FY1, x)), "#02040f", 4, 0.8)
            d += line((x + side * -2, wy_(side, FY0, x)), (x + side * -2, wy_(side, FY1, x)), CYAN, 1.2, 0.3)
        for xa, xb in zip(ribs[:-1], ribs[1:]):  # a porthole slot in each panel
            if xa > xb:
                xa, xb = xb, xa
            span = xb - xa
            x1, x2 = xa + span * 0.2, xb - span * 0.2
            q = [(x1, wy_(side, 100, x1)), (x2, wy_(side, 100, x2)), (x2, wy_(side, 190, x2)), (x1, wy_(side, 190, x1))]
            d += poly(q, "#02040f", OUT, 2.4) + poly(q, "#16286c", None, op=0.0)
            d += poly([(x1 + 1.5, q[0][1] + 3), (x2 - 1.5, q[1][1] + 3), (x2 - 1.5, q[2][1] - 3), (x1 + 1.5, q[3][1] - 3)], "#0a1250", None)
            sx = (x1 + x2) / 2
            sy = (q[0][1] + q[3][1]) / 2
            for _ in range(4):
                d += circle(rng.uniform(x1 + 3, x2 - 3), rng.uniform(min(q[0][1], q[1][1]) + 6, max(q[2][1], q[3][1]) - 6), 0.8, "#ffffff", None, op=0.9)
            d += poly(q, None, CYAN, 1.2, sop=0.6)
            # a light strip under it
            ya = wy_(side, 206, x1)
            yb = wy_(side, 206, x2)
            d += line((x1, ya), (x2, yb), [GREEN, MAG, CYAN][int(span) % 3], 2.2, 0.85)
    d += neon((0, lwall_y(70, 0)), (FX0, 70), CYAN, 2.0, 0.8) + neon((W, rwall_y(70, W)), (FX1, 70), MAG, 2.0, 0.8)
    d += neon((0, lwall_y(236, 0)), (FX0, 236), MAG, 2.0, 0.9) + neon((W, rwall_y(236, W)), (FX1, 236), GREEN, 2.0, 0.9)
    d += neon((FX0 + 1, FY0 + 6), (FX0 + 1, FY1 - 4), GREEN, 2.0, 0.9) + neon((FX1 - 1, FY0 + 6), (FX1 - 1, FY1 - 4), MAG, 2.0, 0.9)
    # hanging tech pylons (ceiling), nearest ones large
    for px_, wd, ln in ((196, 40, 96), (1084, 40, 96), (394, 26, 64), (886, 26, 64)):
        d += pylon(px_, wd, ln)
    # ceiling rings (ribs) and light-mount plates at the 8 moving-head points
    d += truss(60, 1220, 6, 10, "#3a5cb8")
    for (mx, my) in LIGHT_POINTS:
        d += polyhex(mx, my - 4, 11)
    return write_svg("backdrop.svg", (0, 0, W, H), d, defs)


LIGHT_POINTS = [[150, 30], [330, 30], [510, 30], [770, 30], [950, 30], [1130, 30], [450, 58], [830, 58]]


def polyhex(cx, cy, r) -> str:
    return poly(hexagon(cx, cy, r), "#162a78", OUT, 2.2) + poly(hexagon(cx, cy, r * 0.55), "#050b24", None) + circle(cx, cy, 2.2, GREEN, None, op=0.9)


def hex_bolt(cx, cy, r) -> str:
    return poly(hexagon(cx, cy, r), "#7a96e8", OUT, 1.2) + circle(cx, cy, r * 0.3, OUT)


def pylon(cx, w, ln) -> str:
    """A hanging tech pylon: tapered hex column with a glowing core, bands and a lamp tip."""
    d = ""
    defs_id = f"py{int(cx)}"
    top = -4
    d += line((cx, top), (cx, top + 14), OUT, 5) + line((cx, top), (cx, top + 14), "#4a6ad0", 2)
    body = poly([(cx - w / 2, top + 12), (cx + w / 2, top + 12), (cx + w * 0.34, top + ln), (cx - w * 0.34, top + ln)], "#162a78", OUT, 3)
    d += body
    d += poly([(cx - w * 0.06, top + 12), (cx + w / 2, top + 12), (cx + w * 0.34, top + ln), (cx + w * 0.04, top + ln)], "#050b24", None, op=0.45)
    d += poly([(cx - w / 2 + 2, top + 12), (cx - w / 2 + 6, top + 12), (cx - w * 0.34 + 4, top + ln), (cx - w * 0.34 + 1, top + ln)], "#9ab4ff", None, op=0.5)
    d += rect(cx - 2.2, top + 20, 4.4, ln - 34, GREEN, None, op=0.95, rx=2) + rect(cx - 4.5, top + 20, 9, ln - 34, GREEN, None, op=0.18, rx=4)
    for k in range(3):
        y = top + 18 + k * (ln - 30) / 3
        d += rect(cx - w / 2 - 2 + k * 0.6, y, w + 4 - k * 1.2, 5, "#3a5cb8", OUT, 1.6, rx=2)
    d += poly([(cx - w * 0.34, top + ln), (cx + w * 0.34, top + ln), (cx, top + ln + 10)], "#3a5cb8", OUT, 2.2)
    for r, op in ((11, 0.1), (7, 0.2)):
        d += circle(cx, top + ln + 10, r, GREEN, None, op=op)
    d += circle(cx, top + ln + 10, 3, "#ffffff", None, op=0.95)
    return d


# ---- columns, riser, desk -------------------------------------------------------------------------------------------------------------

def build_speaker(side: int) -> dict:
    """An alien resonator column: a fluted tech pillar with two sockets where the runtime draws the pulsing cones."""
    d = ""
    defs = lin_grad("col", [(0, "#2a4aa8"), (0.5, "#14226a"), (1, "#060c2c")], 0, 0, 1, 0)
    cx = SPK_W / 2
    d += poly([(10, 164), (14, 20), (cx - 18, 8), (cx + 18, 8), (SPK_W - 14, 20), (SPK_W - 10, 164)], "url(#col)", OUT, 4)
    d += poly([(cx + 4, 10), (cx + 18, 8), (SPK_W - 14, 20), (SPK_W - 10, 164), (cx + 10, 164)], "#02040f", None, op=0.3)
    d += rect(cx - 8, 0, 16, 10, "#3a5cb8", OUT, 2.2, rx=3)  # the cap and an emitter prong
    d += line((cx, 0), (cx, -0.0), OUT, 0)
    for (x, y, r) in SPK_WOOFERS:
        d += circle(x, y, r + 6, "#02040f", OUT, 3) + circle(x, y, r + 3, None, CYAN, 1.2, sop=0.7) + circle(x, y, r + 1, "#04071c")
    for yy in (82, 160):
        d += rect(8, yy - 4, SPK_W - 16, 8, "#3a5cb8", OUT, 2.2, rx=3) + rect(14, yy - 1.4, SPK_W - 28, 2.8, GREEN, None, op=0.95)
    d += rect(cx - 18, 14, 36, 7, "#050b24", OUT, 2, rx=3) + rect(cx - 14, 16, 12, 3, MAG, None, op=0.95) + rect(cx + 1, 16, 12, 3, CYAN, None, op=0.95)
    d += line((16, 40), (16, 140), CYAN if side < 0 else MAG, 2.0, 0.75)
    d += rect(12, 163, SPK_W - 24, 6, "#050b24", OUT, 2, rx=2)
    return write_svg("speaker_%s.svg" % ("l" if side < 0 else "r"), (0, 0, SPK_W, SPK_H), d, defs)


def build_riser() -> dict:
    """A hovering platform: a low disc with a glowing rim and an energy cushion beneath."""
    w, h = 240, 34
    defs = lin_grad("rt", [(0, "#5a7ad8"), (1, "#2a4aa8")], 0, 0, 0, 1)
    defs += lin_grad("rf", [(0, "#14226a"), (1, "#050b24")], 0, 0, 0, 1)
    defs += rad_grad("cush", [(0, GREEN, 0.55), (0.6, CYAN, 0.2), (1, CYAN, 0.0)])
    d = ellipse(w / 2, 28, 104, 6.5, "url(#cush)")
    d += path(f"M4 14 L4 19 Q{w / 2} 30 {w - 4} 19 L{w - 4} 14 Z", "url(#rf)", OUT, 3)
    d += ellipse(w / 2, 13, w / 2 - 3, 10, "url(#rt)", OUT, 3)
    d += ellipse(w / 2, 13, w / 2 - 22, 6, "#0a1442", None) + ellipse(w / 2, 13, w / 2 - 22, 6, None, GREEN, 1.4, sop=0.9)
    d += ellipse(w / 2, 13, w / 2 - 52, 3.4, None, CYAN, 1.0, sop=0.7)
    d += path(f"M6 19 Q{w / 2} 30 {w - 6} 19", None, GREEN, 2.0, sop=0.95)
    d += path(f"M24 8 Q{w / 2} 2 {w - 24} 8", None, "#bcd2ff", 1.4, sop=0.5)
    return write_svg("riser.svg", (0, 0, w, h), d, defs)


def build_desk_top() -> dict:
    """The bio-tech console strip, authored 1280 x 260 and stretched into the pad-strip rectangle."""
    w, h = 1280, 260
    defs = lin_grad("dk", [(0, "#243a8a"), (0.06, "#14226a"), (1, "#060c2c")], 0, 0, 0, 1)
    defs += lin_grad("lip", [(0, "#7a96e8"), (0.5, "#3a5cb8"), (1, "#1c3478")], 0, 0, 0, 1)
    d = rect(0, 0, w, h, "url(#dk)") + rect(0, 0, w, 16, "url(#lip)") + line((0, 16), (w, 16), OUT, 3.5) + line((0, 2.5), (w, 2.5), "#d9ecff", 1.6, 0.7)
    for row in range(0, 9):  # a faint hex mesh across the whole console
        for col in range(0, 40):
            hx = col * 34 + (17 if row % 2 else 0)
            hy = 32 + row * 29
            d += poly(hexagon(hx, hy, 16, 30), None, CYAN, 1.0, sop=0.07)
    for x0, x1 in ((10, 424), (856, 1270)):  # pad wings
        d += rect(x0, 26, x1 - x0, h - 36, "#04081f", OUT, 2.6, rx=18, op=0.62)
        d += rect(x0 + 5, 31, x1 - x0 - 10, h - 46, None, GREEN, 1.2, rx=14, sop=0.4)
        for sx, sy in ((x0 + 14, 40), (x1 - 14, 40), (x0 + 14, h - 22), (x1 - 14, h - 22)):
            d += hex_bolt(sx, sy, 5)
        for k in range(5):
            d += rect(x0 + 30 + k * 12, h - 24, 7, 3, CYAN, None, op=0.5 if k % 2 else 0.9, rx=1)
    mx0, mx1 = 436, 844
    d += rect(mx0, 26, mx1 - mx0, h - 36, "#0a1442", OUT, 3, rx=16) + rect(mx0 + 5, 31, mx1 - mx0 - 10, h - 46, None, MAG, 1.4, rx=12, sop=0.45)
    for k in range(0, 17):
        x = mx0 + 24 + k * ((mx1 - mx0 - 48) / 16.0)
        d += line((x, 36), (x, 36 + (9 if k % 4 == 0 else 5)), "#8aa6ff", 1.4, 0.55) + line((x, h - 30), (x, h - 30 - (9 if k % 4 == 0 else 5)), "#8aa6ff", 1.4, 0.55)
    d += rect(mx0 + 60, h - 62, mx1 - mx0 - 120, 10, "#02040f", OUT, 2, rx=5) + rect(mx0 + 66, h - 59, mx1 - mx0 - 132, 3, GREEN, None, op=0.4)
    for x in (mx0 + 40, mx1 - 56):
        d += rect(x, 60, 16, 80, "#02040f", OUT, 2, rx=3)
        for k in range(8):
            d += rect(x + 3, 64 + k * 9.4, 10, 5, [CYAN, CYAN, CYAN, GREEN, GREEN, AMB, AMB, MAG][k], None, op=0.3)
    for gx in (mx0 + 100, 640, mx1 - 100):
        d += glyph(gx, 46, 9, "#8aa6ff", int(gx), 0.5)
    return write_svg("desk_top.svg", (0, 0, w, h), d, defs)


# ---- sprites --------------------------------------------------------------------------------------------------------------------------

def spr_woofer(sprites: dict) -> None:
    r = 50
    defs = rad_grad("cone", [(0, "#3a5cb8"), (0.45, "#1c3478"), (1, "#0a1442")], 0.42, 0.38, 0.75)
    defs += lin_grad("rim", [(0, "#7a96e8"), (1, "#1c3478")], 0, 0, 1, 1)
    d = circle(0, 0, r, "url(#rim)", OUT, 3.5) + circle(0, 0, r - 5, "#04081f") + circle(0, 0, r - 9, "url(#cone)", OUT, 2.2)
    for k, rr in enumerate((36, 30, 24, 18)):
        d += circle(0, 0, rr, None, CYAN if k % 2 == 0 else "#02040f", 1.5, sop=0.6)
    for k in range(8):  # radial energy ribs
        a = k * math.tau / 8
        d += line((math.cos(a) * 14, math.sin(a) * 14), (math.cos(a) * 34, math.sin(a) * 34), GREEN, 1.2, 0.35)
    d += circle(0, 0, 12, "#0a1442", OUT, 2.4) + circle(0, 0, 8, GREEN, None, op=0.55) + circle(-2.5, -2.5, 3.6, "#ffffff", None, op=0.9)
    d += path("M-32 -20 A38 38 0 0 1 -8 -36", None, "#ffffff", 3, sop=0.4)
    info = write_svg("props/woofer.svg", (-r - 3, -r - 3, r + 3, r + 3), d, defs)
    sprites["woofer"] = {"file": "source/props/woofer.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "radius": r}


def spr_fixture(sprites: dict) -> None:
    """An alien light-probe: a mount plate, a short stem, a ringed orb with a lens pointing straight down."""
    defs = rad_grad("orb", [(0, "#8aa6ff"), (0.6, "#2a4aa8"), (1, "#0a1442")], 0.38, 0.32, 0.8)
    d = rect(-11, 0, 22, 6, "#3a5cb8", OUT, 2.4, rx=2) + rect(-3.5, 5, 7, 9, "#162a78", OUT, 2)
    d += circle(0, 28, 16, "url(#orb)", OUT, 3)
    d += ellipse(0, 28, 21, 5, None, OUT, 4.4, sop=1) + ellipse(0, 28, 21, 5, None, CYAN, 2.2, sop=0.95)
    d += path("M-9 22 Q-6 16 1 15", None, "#ffffff", 2, sop=0.55)
    d += circle(0, 41, 6.5, "#04081f", OUT, 2.2) + circle(0, 41.5, 4.6, "#e6fbff") + circle(0, 42, 2.4, "#ffffff")
    info = write_svg("props/fixture.svg", (-24, -2, 24, 52), d, defs)
    sprites["fixture"] = {"file": "source/props/fixture.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "lens": [0, 44]}


def spr_disco_ball(sprites: dict) -> None:
    """The energy orb: a glowing sphere on a cable with two orbiting rings."""
    cy, r = 66, 28
    defs = rad_grad("ball", [(0, "#ffffff"), (0.35, "#bff6ff"), (0.75, "#4aa8ff"), (1, "#2a2a9a")], 0.4, 0.36, 0.78)
    defs += rad_grad("halo", [(0.45, GREEN, 0.0), (0.7, GREEN, 0.22), (1, GREEN, 0.0)])
    d = line((0, 0), (0, cy - r + 2), OUT, 4.2) + line((0, 0), (0, cy - r + 2), "#8aa6ff", 1.6) + rect(-5, 0, 10, 6, "#3a5cb8", OUT, 2, rx=2)
    d += circle(0, cy, r + 14, "url(#halo)")
    d += ellipse(0, cy, r + 9, 8, None, OUT, 4.6, sop=0.9) + circle(0, cy, r, "url(#ball)", OUT, 3.4)
    rng = random.Random(9)
    inner = "".join(circle(math.cos(a) * rr, cy + math.sin(a) * rr, rng.choice((1.0, 1.4, 1.8)), rng.choice(("#ffffff", GREEN, MAG)), None, op=0.8)
                    for a, rr in ((rng.random() * math.tau, rng.random() * (r - 6)) for _ in range(16)))
    defs += clip("bc", f'<circle cx="0" cy="{cy}" r="{r}"/>')
    d += group(inner, 'clip-path="url(#bc)"')
    d += circle(-9, cy - 10, 4.4, "#ffffff", None, op=0.85)
    d += ellipse(0, cy, r + 9, 8, None, CYAN, 2.2, sop=0.95)
    d += path(f"M{-r - 9} {cy} A{r + 9} 8 0 0 0 {r + 9} {cy}", None, MAG, 2.2, sop=0.0)
    d += ellipse(0, cy, r * 0.9, r + 7, None, MAG, 1.4, sop=0.55)
    info = write_svg("props/disco_ball.svg", (-r - 14, -2, r + 14, cy + r + 14), d, defs)
    sprites["disco_ball"] = {"file": "source/props/disco_ball.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "radius": r, "ball_centre": [0, cy]}


def spr_glowstick(sprites: dict) -> None:
    """A glow wand: a white (tintable) orb on a short stem; the grip end is the pivot."""
    d = line((0, 14), (0, 38), OUT, 8.4) + line((0, 14), (0, 38), "#ffffff", 4.2) + line((0, 30), (0, 38), "#7a96e8", 4.2, cap="butt")
    d += circle(0, 8, 9.5, "#ffffff", OUT, 2.8) + circle(-2.6, 5.4, 3, "#ffffff", None, op=0.9) + circle(0, 8, 9.5, None, "#ffffff", 0.0)
    d += line((-6.5, 14.5), (6.5, 14.5), "#9ab0f0", 2.4, 0.95, cap="butt")
    info = write_svg("props/glowstick.svg", (-14, -4, 14, 44), d)
    sprites["glowstick"] = {"file": "source/props/glowstick.svg", "pivot": pivot_in(info, (0, 38)), "px_scale": 0.5, "length": 36}


def spr_door_open(sprites: dict) -> dict:
    ox, oy = 244, 138
    dx, dy, dw, dh = 284 - ox, 138 - oy, 70, 124
    defs = lin_grad("spill", [(0, "#bffff0", 0.7), (0.6, GREEN, 0.25), (1, CYAN, 0.0)], 0, 0, 0, 1)
    defs += lin_grad("room", [(0, "#f0fffa"), (1, "#7affd0")], 0, 0, 0, 1)
    d = poly([(dx - 4, dy + dh), (dx + dw + 4, dy + dh), (dx + dw + 54, dy + dh + 86), (dx - 54, dy + dh + 86)], "url(#spill)")
    d += rect(dx - 8, dy - 8, dw + 16, dh + 8, "#162a78", OUT, 3, rx=10) + rect(dx, dy, dw, dh, "url(#room)")
    d += rect(dx + 14, dy + 20, dw - 28, dh - 20, "#ffffff", None, op=0.5)
    d += rect(dx, dy + 3, 14, dh - 3, "#14226a", OUT, 2.4, rx=3) + rect(dx + dw - 14, dy + 3, 14, dh - 3, "#14226a", OUT, 2.4, rx=3)  # hatch halves slid apart
    cxm = dx + dw / 2  # a small grey alien silhouette arriving
    d += ellipse(cxm, dy + 62, 8.5, 10, "#3a2a6a", OUT, 1.6) + path(f"M{cxm - 10} {dy + dh} Q{cxm - 10} {dy + 78} {cxm} {dy + 76} Q{cxm + 10} {dy + 78} {cxm + 10} {dy + dh} Z", "#3a2a6a", OUT, 1.6)
    d += line((cxm - 7, dy + 76), (cxm - 16, dy + 60), "#3a2a6a", 4) + line((cxm + 7, dy + 76), (cxm + 16, dy + 60), "#3a2a6a", 4)
    d += neon((dx - 8, dy - 8), (dx + dw + 8, dy - 8), GREEN, 1.6, 1.0)
    d += rect(dx + 12, dy - 24, dw - 24, 12, "#050b24", OUT, 2, rx=6) + rect(dx + 17, dy - 21, dw - 34, 6, GREEN, None, op=0.95, rx=3)
    info = write_svg("props/door_open.svg", (0, -8, 150, 214), d, defs)
    return {"file": "source/props/door_open.svg", "pivot": pivot_in(info, (0, -8)), "px_scale": 0.5, "pos": [ox, oy - 8]}


def spr_deck(sprites: dict) -> None:
    S, hole = 240, 200
    o = (S - hole) / 2
    defs = lin_grad("bz", [(0, "#3a5cb8"), (0.5, "#1c3478"), (1, "#0a1442")], 0, 0, 1, 1) + lin_grad("bzn", [(0, CYAN), (0.5, GREEN), (1, MAG)], 0, 0, 1, 1)
    c = 30

    def chamfer(x0, y0, x1, y1, k):
        return f"M{x0 + k} {y0} H{x1 - k} L{x1} {y0 + k} V{y1 - k} L{x1 - k} {y1} H{x0 + k} L{x0} {y1 - k} V{y0 + k} Z"

    outer, inner = chamfer(0, 0, S, S, c), chamfer(o, o, S - o, S - o, 22)
    d = f'<path d="{outer} {inner}" fill="url(#bz)" fill-rule="evenodd"/>' + path(outer, None, OUT, 4) + path(inner, None, OUT, 3)
    d += path(inner, None, "url(#bzn)", 2.4, sop=0.95) + path(outer, None, "#d9ecff", 1.4, sop=0.25)
    for sx, sy in ((14, 14), (S - 14, 14), (14, S - 14), (S - 14, S - 14)):
        d += hex_bolt(sx, sy, 6)
    for k in range(5):  # status ticks along the top bar
        d += rect(S / 2 - 30 + k * 12, 4, 7, 3, GREEN if k < 3 else CYAN, None, op=0.9)
    info = write_svg("props/pad_bezel.svg", (0, 0, S, S), d, defs)
    sprites["pad_bezel"] = {"file": "source/props/pad_bezel.svg", "pivot": pivot_in(info, (S / 2, S / 2)), "px_scale": 0.5, "inner_ratio": hole / S}
    # platter: a hologram record disc, glyph ring and a bright marker that shows the spin
    R = 120
    defs = rad_grad("vin", [(0, "#14226a"), (0.55, "#060c2c"), (1, "#02040f")]) + lin_grad("lab", [(0, GREEN), (1, CYAN)], 0, 0, 1, 1)
    d = circle(0, 0, R, "#14226a", OUT, 4) + circle(0, 0, R - 6, None, CYAN, 1.4, sop=0.6)
    for k in range(48):
        a = k * math.tau / 48
        d += line((math.cos(a) * (R - 15), math.sin(a) * (R - 15)), (math.cos(a) * (R - 8), math.sin(a) * (R - 8)), GREEN if k % 4 else MAG, 2.0, 0.85)
    d += circle(0, 0, R - 20, "url(#vin)", OUT, 3)
    for rr in range(46, R - 22, 6):
        d += circle(0, 0, rr, None, CYAN if rr % 12 else "#3a5cb8", 0.8, sop=0.3)
    for k in range(10):
        a = k * math.tau / 10
        d += glyph(math.cos(a) * 78, math.sin(a) * 78, 11, "#8aa6ff", k, 0.7)
    d += path(f"M{-R + 34} -34 A{R - 28} {R - 28} 0 0 1 -34 {-R + 34}", None, "#ffffff", 5, sop=0.14)
    d += circle(0, 0, 38, "url(#lab)", OUT, 3) + poly(hexagon(0, 0, 24, 0), "#04081f", OUT, 2) + path("M0 -14 L8 8 L-8 8 Z", "#ffffff", None, op=0.9)
    d += circle(0, 0, 4, "#ffffff", OUT, 1.4) + circle(0, -(R - 30), 4.6, AMB, OUT, 1.4)
    info = write_svg("props/platter.svg", (-R - 3, -R - 3, R + 3, R + 3), d, defs)
    sprites["platter"] = {"file": "source/props/platter.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "diameter": 2 * R}
    # knob: a glowing orb-knob
    defs = rad_grad("kb", [(0, "#7a96e8"), (0.6, "#2a4aa8"), (1, "#0a1442")], 0.4, 0.35, 0.7)
    d = circle(0, 0, 24, "#02040f", OUT, 3)
    for k in range(12):
        a = k * math.tau / 12 - math.pi / 2
        d += line((math.cos(a) * 20, math.sin(a) * 20), (math.cos(a) * 23, math.sin(a) * 23), GREEN, 1.6, 0.8)
    d += circle(0, 0, 17, "url(#kb)", OUT, 2.4) + circle(-4, -5, 6, "#ffffff", None, op=0.18) + line((0, -4), (0, -15), GREEN, 3.4) + line((0, -4), (0, -15), "#e6fff6", 1.3)
    info = write_svg("props/knob.svg", (-26, -26, 26, 26), d, defs)
    sprites["knob"] = {"file": "source/props/knob.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
    d = rect(-5, -60, 10, 120, "#02040f", OUT, 2.4, rx=5) + rect(-1.6, -55, 3.2, 110, GREEN, None, op=0.45)
    for k in range(11):
        y = -55 + k * 11
        d += line((-12, y), (-8, y), "#8aa6ff", 1.4, 0.7) + line((8, y), (12, y), "#8aa6ff", 1.4, 0.7)
    info = write_svg("props/fader_slot.svg", (-16, -66, 16, 66), d)
    sprites["fader_slot"] = {"file": "source/props/fader_slot.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "travel": 110}
    defs = lin_grad("fc", [(0, "#a8c0ff"), (0.5, "#3a5cb8"), (1, "#14226a")], 0, 0, 0, 1)
    d = rect(-12, -17, 24, 34, "url(#fc)", OUT, 2.8, rx=7) + line((-12, 0), (12, 0), "#02040f", 3) + line((-10, 0), (10, 0), GREEN, 1.6) + line((-9, -11), (9, -11), "#ffffff", 1.2, 0.4)
    info = write_svg("props/fader_cap.svg", (-16, -21, 16, 21), d, defs)
    sprites["fader_cap"] = {"file": "source/props/fader_cap.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
    d = rect(-26, -15, 52, 30, "url(#fc)", OUT, 2.8, rx=9)
    for k in range(-5, 6):
        d += line((k * 4.2, -11), (k * 4.2, 11), "#0a1442", 1.4, 0.55)
    d += line((0, -15), (0, 15), MAG, 2.4)
    info = write_svg("props/crossfader.svg", (-30, -19, 30, 19), d, defs)
    sprites["crossfader"] = {"file": "source/props/crossfader.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
    info = write_svg("props/vu_segment.svg", (-22, -7, 22, 7), rect(-20, -5, 40, 10, "#ffffff", None, rx=4))
    sprites["vu_segment"] = {"file": "source/props/vu_segment.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
    info = write_svg("props/deck_screw.svg", (-8, -8, 8, 8), hex_bolt(0, 0, 6.2))
    sprites["deck_screw"] = {"file": "source/props/deck_screw.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
    defs = lin_grad("lg", [(0, GREEN), (0.5, CYAN), (1, MAG)], 0, 0, 1, 0)
    d = rect(0, 5, 1280, 11, "url(#lg)", None, op=0.14) + rect(0, 8, 1280, 6, "url(#lg)", None, op=0.28) + rect(0, 9.5, 1280, 3, "url(#lg)", None, op=1.0) + rect(0, 10.4, 1280, 1.2, "#ffffff", None, op=0.7)
    info = write_svg("props/desk_lip_glow.svg", (0, 0, 1280, 16), d, defs)
    sprites["desk_lip_glow"] = {"file": "source/props/desk_lip_glow.svg", "pivot": pivot_in(info, (640, 8)), "px_scale": 0.5}


def sparks_png() -> dict:
    """Confetti re-themed as star sparks: four 32 px frames of different stars/diamonds (supersampled)."""
    cols = [(255, 255, 255), (79, 240, 168), (25, 230, 255), (255, 194, 63)]
    big = Image.new("RGBA", (128 * 4, 32 * 4), (0, 0, 0, 0))
    dr = ImageDraw.Draw(big)
    for i, c in enumerate(cols):
        cx, cy = (16 + i * 32) * 4, 64
        n, ro, ri = (4, 14, 3.4) if i % 2 == 0 else (5, 12, 5.2)
        pts_ = []
        for k in range(n * 2):
            rr = (ro if k % 2 == 0 else ri) * 4
            a = math.pi * k / n - math.pi / 2 + (0.3 if i == 3 else 0)
            pts_.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        dr.polygon(pts_, fill=c + (255,), outline=(27, 16, 64, 255))
    small = big.resize((128, 32), Image.LANCZOS)
    os.makedirs(lib.PNG_DIR, exist_ok=True)
    small.save(os.path.join(lib.PNG_DIR, "confetti.png"), compress_level=9)
    return {"file": "processed/confetti.png", "pivot": [16, 16], "px_scale": 1.0, "frames": 4, "frame_size": [32, 32]}


# ---- silhouettes ----------------------------------------------------------------------------------------------------------------------

def _sil_shape(kind: str, up: bool) -> str:
    s = ""
    if kind == "a":  # big bulbous head, narrow shoulders
        s += path("M-28 0 L-26 -26 Q-24 -42 -9 -46 Q-5 -48 -5 -54 L5 -54 Q5 -48 9 -46 Q24 -42 26 -26 L28 0 Z", "#fff")
        s += path("M-24 -86 Q-26 -62 -6 -54 L6 -54 Q26 -62 24 -86 Q22 -108 0 -108 Q-22 -108 -24 -86 Z", "#fff")
    elif kind == "b":  # two antennae with orb tips
        s += path("M-32 0 L-30 -26 Q-28 -44 -12 -48 Q-7 -50 -7 -57 L7 -57 Q7 -50 12 -48 Q28 -44 30 -26 L32 0 Z", "#fff")
        s += ellipse(0, -74, 15, 18, "#fff")
        for sx in (-1, 1):
            s += line((sx * 7, -88), (sx * 20, -112), "#fff", 3.4) + circle(sx * 21, -115, 5.5, "#fff")
    else:  # tentacle crest and a wide body
        s += path("M-40 0 L-38 -24 Q-34 -44 -13 -48 Q-9 -50 -9 -57 L9 -57 Q9 -50 13 -48 Q34 -44 38 -24 L40 0 Z", "#fff")
        s += ellipse(0, -76, 17, 21, "#fff") + path("M-18 -86 Q-18 -108 0 -108 Q18 -108 18 -86 Z", "#fff")
        for sx in (-1, 1):
            s += path(f"M{sx * 14} -90 Q{sx * 30} -80 {sx * 24} -56 Q{sx * 22} -70 {sx * 12} -76 Z", "#fff")
    if up:
        for sx in (-1, 1):
            s += line((sx * 24, -38), (sx * 46, -112), "#fff", 10) + circle(sx * 47, -116, 6.5, "#fff")
            for a in (-25, 0, 25):
                s += line((sx * 47, -116), (sx * 47 + math.sin(math.radians(a)) * 9, -116 - math.cos(math.radians(a)) * 9), "#fff", 2.6)
    return s


def build_silhouettes() -> dict:
    out = {}
    fills = {"a": "#080d2c", "b": "#060a26", "c": "#0a1032"}
    for kind in ("a", "b", "c"):
        entry = {}
        for state in ("idle", "up"):
            up = state == "up"
            shape = _sil_shape(kind, up)
            body = "".join(_recolor(shape, col, dx, -1.2) for dx, col in ((-2.2, CYAN), (2.2, MAG)))
            body += _recolor(shape, fills[kind], 0, 0)
            info = write_svg(f"silhouettes/sil_{kind}_{state}.svg", (-64, -140 if up else -122, 64, 4), body)
            entry[state] = {"file": f"source/silhouettes/sil_{kind}_{state}.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
        entry["height"] = 108
        out[f"sil_{kind}"] = entry
    return out


# ---- pieces --------------------------------------------------------------------------------------------------------------------------

def piece_planet_glow() -> dict:
    wx, wy, ww, wh = WIN
    pcx, pcy = PLANET[0] - wx, PLANET[1] - wy
    defs = rad_grad("pg1", [(0, "#ffffff", 0.22), (0.4, "#ff8ad0", 0.2), (1, MAG, 0.0)]) + rad_grad("pg2", [(0, CYAN, 0.22), (1, CYAN, 0.0)])
    d = ellipse(pcx, pcy, 150, 80, "url(#pg2)") + circle(pcx, pcy, 92, "url(#pg1)")
    for k, col in enumerate((GREEN, CYAN, MAG)):  # aurora arcs over the planet's limb
        dd_ = f"M{pcx - 64 + k * 6} {pcy - 10 + k * 5} Q{pcx - 10} {pcy - 84 + k * 10} {pcx + 56 - k * 5} {pcy - 24 + k * 6}"
        d += path(dd_, None, col, 4 - k * 0.8, sop=0.4) + path(dd_, None, "#ffffff", 1.0, sop=0.4)
    info = write_svg("pieces/planet_window_glow.svg", (0, 0, ww, wh), d, defs)
    return {"id": "planet_window_glow", "file": "source/pieces/planet_window_glow.svg", "pos": [wx, wy], "size": [ww, wh], "px_scale": 0.5,
            "pivot": pivot_in(info, (pcx, pcy)), "anim": "pulse", "z": "behind"}


def piece_dome() -> dict:
    w, h = 460, 250
    cx, by = w / 2, 214
    rx, ry, hh = 222, 36, 196
    defs = lin_grad("dm", [(0, CYAN, 0.04), (0.7, CYAN, 0.12), (1, GREEN, 0.34)], 0, 0, 0, 1)
    dome = f"M{cx - rx} {by} C{cx - rx} {by - hh * 1.3} {cx + rx} {by - hh * 1.3} {cx + rx} {by} A{rx} {ry} 0 0 1 {cx - rx} {by} Z"
    d = path(dome, "url(#dm)", None)
    for k in range(1, 5):  # latitude rings
        t = k / 5
        yy = by - hh * 0.97 * t
        rxx = rx * math.sqrt(max(0.0, 1 - t ** 2)) * 0.98
        d += ellipse(cx, yy, rxx, ry * 0.8 * math.sqrt(max(0.0, 1 - t ** 2)) + 3, None, CYAN, 1.3, sop=0.45)
    for k in range(-3, 4):  # meridians
        d += path(f"M{cx + k * rx * 0.3} {by + ry * 0.55 * (1 - abs(k) / 4)} Q{cx + k * rx * 0.62} {by - hh * 0.95} {cx + k * 6} {by - hh * 0.97}", None, CYAN, 1.2, sop=0.35)
    d += ellipse(cx, by, rx, ry, None, GREEN, 3.4, sop=0.9) + ellipse(cx, by, rx, ry, None, "#ffffff", 1.2, sop=0.8) + ellipse(cx, by, rx, ry, None, GREEN, 9, sop=0.15)
    d += path(f"M{cx - rx * 0.8} {by - 60} Q{cx - rx * 0.5} {by - hh * 0.9} {cx - 20} {by - hh * 0.96}", None, "#ffffff", 3, sop=0.35)
    info = write_svg("pieces/hologram_dome.svg", (0, 0, w, h), d, defs)
    return {"id": "hologram_dome", "file": "source/pieces/hologram_dome.svg", "pos": [640 - w / 2, 372 + 8 - by], "size": [w, h], "px_scale": 0.5,
            "pivot": pivot_in(info, (cx, by)), "anim": "pulse", "z": "front"}


def piece_ring_lights() -> dict:
    w, h = 560, 120
    cx, cy = w / 2, h / 2
    d = ""
    for k, (rx, ry, col) in enumerate(((250, 46, CYAN), (196, 36, GREEN), (140, 25.5, MAG), (84, 15.4, CYAN), (36, 6.6, GREEN))):
        d += ellipse(cx, cy, rx, ry, None, col, 9, sop=0.1) + ellipse(cx, cy, rx, ry, None, col, 4, sop=0.22) + ellipse(cx, cy, rx, ry, None, lighten(col, 0.4), 1.8, sop=0.95)
        for j in range(12 + k * 2):  # ring lamps
            a = j * math.tau / (12 + k * 2)
            d += circle(cx + rx * math.cos(a), cy + ry * math.sin(a), 2.2, "#ffffff", None, op=0.9)
    info = write_svg("pieces/ring_lights.svg", (0, 0, w, h), d)
    return {"id": "ring_lights", "file": "source/pieces/ring_lights.svg", "pos": [640 - cx, 372 - cy], "size": [w, h], "px_scale": 0.5,
            "pivot": pivot_in(info, (cx, cy)), "anim": "pulse", "z": "behind"}


def piece_pylon_beams() -> dict:
    w, h = 920, 330
    xs = [(25, 11, 310), (210, 8, 270), (710, 8, 270), (895, 11, 310)]  # (x, half width, bottom y)
    defs = ""
    d = ""
    for i, (x, hw, by) in enumerate(xs):
        defs += lin_grad(f"pb{i}", [(0, GREEN, 0.0), (0.12, GREEN, 0.55), (0.9, GREEN, 0.5), (1, CYAN, 0.0)], 0, 0, 0, 1)
        for mul, op in ((3.0, 0.12), (2.0, 0.22), (1.0, 0.7)):
            d += rect(x - hw * mul, 6, hw * 2 * mul, by - 6, f"url(#pb{i})", None, op=op, rx=hw * mul)
        d += rect(x - 1.6, 10, 3.2, by - 20, "#d8fff0", None, op=0.6, rx=1.6)
        for k in range(6):
            yy = 30 + k * (by - 50) / 6
            d += ellipse(x, yy, hw * 1.7, 3, None, "#ffffff", 1.4, sop=0.55)
        d += ellipse(x, by, hw * 2.6, 6, GREEN, None, op=0.35) + ellipse(x, by, hw * 1.4, 3, "#ffffff", None, op=0.75)
    info = write_svg("pieces/pylon_beams.svg", (0, 0, w, h), d, defs)
    return {"id": "pylon_beams", "file": "source/pieces/pylon_beams.svg", "pos": [185, 20], "size": [w, h], "px_scale": 0.5,
            "pivot": pivot_in(info, (w / 2, 0)), "anim": "pulse", "z": "behind"}


def piece_warp() -> dict:
    wx, wy, ww, wh = WIN
    lx, ly, lw_, lh = LED
    rng = random.Random(77)
    cx, cy = (wx + ww / 2) - wx, (wy + wh / 2) - wy
    d = ""
    for _ in range(90):
        a = rng.random() * math.tau
        r0 = rng.uniform(24, 260)
        ln = r0 * rng.uniform(0.25, 0.7)
        p0 = (cx + math.cos(a) * r0 * 1.8, cy + math.sin(a) * r0 * 0.55)
        p1 = (cx + math.cos(a) * (r0 + ln) * 1.8, cy + math.sin(a) * (r0 + ln) * 0.55)
        if not (4 < p0[0] < ww - 4 and 4 < p0[1] < wh - 4 and 4 < p1[0] < ww - 4 and 4 < p1[1] < wh - 4):
            continue
        pm = ((p0[0] + p1[0]) / 2 + wx, (p0[1] + p1[1]) / 2 + wy)
        if any(lx - 14 < q[0] + wx < lx + lw_ + 14 and ly - 14 < q[1] + wy < ly + lh + 14 for q in (p0, p1, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2))):
            continue
        col = rng.choice(("#ffffff", "#c8f4ff", "#c8ffe6"))
        d += line(p0, p1, col, 3.2, rng.uniform(0.1, 0.2)) + line(p0, p1, col, 1.2, rng.uniform(0.7, 1.0))
    info = write_svg("pieces/warp_streaks.svg", (0, 0, ww, wh), d)
    return {"id": "warp_streaks", "file": "source/pieces/warp_streaks.svg", "pos": [wx, wy], "size": [ww, wh], "px_scale": 0.5,
            "pivot": pivot_in(info, (cx, cy)), "anim": "none", "z": "behind"}


def saucer(prefix: str, w=120, h=52) -> tuple[str, str]:
    cx, cy = w / 2, h * 0.58
    defs = lin_grad(prefix + "h", [(0, "#d9e4ff"), (0.5, "#7a96e8"), (1, "#2a3a90")], 0, 0, 0, 1)
    defs += rad_grad(prefix + "d", [(0, "#e6ffff"), (1, "#4aa8ff")], 0.4, 0.3, 0.8)
    d = ellipse(cx, cy + 4, w * 0.46, 7, GREEN, None, op=0.22)
    d += path(f"M{cx - w * 0.2} {cy - 4} Q{cx - w * 0.15} {cy - h * 0.55} {cx} {cy - h * 0.58} Q{cx + w * 0.15} {cy - h * 0.55} {cx + w * 0.2} {cy - 4} Z", f"url(#{prefix}d)", OUT, 2.4)
    d += path(f"M2 {cy} Q4 {cy - 9} {cx} {cy - 10} Q{w - 4} {cy - 9} {w - 2} {cy} Q{w - 6} {cy + 12} {cx} {cy + 13} Q6 {cy + 12} 2 {cy} Z", f"url(#{prefix}h)", OUT, 2.6)
    for k in range(7):
        t = (k + 0.5) / 7
        d += circle(cx + (t - 0.5) * (w - 26), cy + 3 + 5 * (1 - (2 * t - 1) ** 2) * 0.9, 2.1, [GREEN, AMB, MAG, CYAN][k % 4], OUT, 0.8)
    d += path(f"M{cx - w * 0.3} {cy - 4} Q{cx} {cy - 12} {cx + w * 0.1} {cy - 8}", None, "#ffffff", 1.6, sop=0.6)
    return defs, d


def piece_saucer() -> dict:
    w, h = 120, 52
    defs, d = saucer("sf", w, h)
    info = write_svg("pieces/saucer_flyby.svg", (0, 0, w, h), d, defs)
    return {"id": "saucer_flyby", "file": "source/pieces/saucer_flyby.svg", "pos": [392, 76], "size": [w, h], "px_scale": 0.5,
            "pivot": pivot_in(info, (w / 2, h * 0.58)), "anim": "bob", "z": "behind"}


def piece_banner() -> dict:
    w, h = 76, 200
    defs = lin_grad("bn", [(0, "#3a1a8a"), (1, "#14226a")], 0, 0, 0, 1)
    d = rect(2, 0, w - 4, 9, "#3a5cb8", OUT, 2.4, rx=3)
    d += path(f"M8 9 L{w - 8} 9 L{w - 8} {h - 38} L{w / 2} {h - 14} L8 {h - 38} Z", "url(#bn)", OUT, 3)
    d += path(f"M14 16 L{w - 14} 16 L{w - 14} {h - 44} L{w / 2} {h - 24} L14 {h - 44} Z", None, MAG, 1.6, sop=0.85)
    d += circle(w / 2, 64, 17, None, GREEN, 2.4, sop=0.95) + circle(w / 2, 64, 6, GREEN, None, op=0.95) + path(f"M{w / 2 - 20} 64 H{w / 2 + 20}", None, GREEN, 1.4, sop=0.8)
    for k, yy in enumerate((102, 124, 146)):
        d += glyph(w / 2, yy, 13, [CYAN, MAG, AMB][k], 30 + k)
    d += circle(w / 2, h - 15, 3, AMB, OUT, 1)
    info = write_svg("pieces/alien_banner.svg", (0, 0, w, h), d, defs)
    return {"id": "alien_banner", "file": "source/pieces/alien_banner.svg", "pos": [1166, 0], "size": [w, h], "px_scale": 0.5,
            "pivot": pivot_in(info, (w / 2, 0)), "anim": "sway", "z": "behind"}


def piece_bar_glow() -> dict:
    w, h = 80, 140
    defs = lin_grad("bgl", [(0, MAG, 0.0), (0.5, MAG, 0.4), (1, VIO, 0.0)], 0, 0, 0, 1)
    d = rect(0, 0, w, h, "url(#bgl)", None, op=0.9, rx=14) + neon((10, 124), (w - 10, 124), MAG, 1.6, 1.0)
    d += glyph(w / 2, 16, 14, "#ffffff", 3, 0.9) + circle(w / 2, 16, 12, None, "#ffffff", 1.4, sop=0.9)
    info = write_svg("pieces/bar_glow.svg", (0, 0, w, h), d, defs)
    return {"id": "bar_glow", "file": "source/pieces/bar_glow.svg", "pos": [934, 130], "size": [w, h], "px_scale": 0.5,
            "pivot": pivot_in(info, (w / 2, h / 2)), "anim": "flicker", "z": "behind"}


# ---- manifest -------------------------------------------------------------------------------------------------------------------------

def build_stage() -> dict:
    from . import sprites as png

    layers = []
    build_backdrop()
    layers.append({"id": "backdrop", "file": "source/backdrop.svg", "pos": [0, 0], "size": [W, H], "px_scale": 0.5})
    build_riser()
    layers.append({"id": "riser", "file": "source/riser.svg", "pos": [520, 252], "size": [240, 34], "px_scale": 0.5})
    for side in (-1, 1):
        build_speaker(side)
        sid = "speaker_l" if side < 0 else "speaker_r"
        layers.append({"id": sid, "file": f"source/{sid}.svg", "pos": list(SPK_POS[sid]), "size": [SPK_W, SPK_H], "px_scale": 0.5})
    build_desk_top()
    layers.append({"id": "desk_top", "file": "source/desk_top.svg", "pos": [0, 460], "size": [1280, 260], "px_scale": 0.5,
                   "note": "authored 1280 x 260; stretch to the pad-strip rectangle"})
    sprites: dict = {}
    spr_woofer(sprites)
    spr_fixture(sprites)
    spr_disco_ball(sprites)
    spr_glowstick(sprites)
    sprites["door_open"] = spr_door_open(sprites)
    spr_deck(sprites)
    sprites.update(png.build_png_sprites())
    sprites["confetti"] = sparks_png()
    woofers = []
    for sid in ("speaker_l", "speaker_r"):
        px, py = SPK_POS[sid]
        for (wx, wy, wr) in SPK_WOOFERS:
            woofers.append([px + wx, py + wy, wr])
    anchors = {
        "led_screen": list(LED), "doorway": [284, 138, 70, 124], "floor_rows": FLOOR_ROWS,
        "floor_polygon": [[400, 266], [880, 266], [round(floor_x(880, 520)), 520], [round(floor_x(400, 520)), 520]],
        "floor_grid": {"vanishing_point": [VPX, VPY], "far_y": FY1, "far_x": [400 + 60 * i for i in range(9)],
                       "note": "x on the far wall base line; a floor line through far_x at screen row y is at x = vp_x + (far_x - vp_x) * (y - vp_y) / (far_y - vp_y)"},
        "light_points": LIGHT_POINTS, "woofers": woofers, "disco_ball": [640, 0], "riser": [640, 286, 240],
        "circle_centre": [640, 372], "circle_radii": [250, 46],
        "wall_left_x": FX0, "wall_right_x": FX1, "horizon_y": VPY,
        "window": list(WIN), "planet": list(PLANET), "bar": [944, 140, 60, 122],
    }
    pieces = [piece_planet_glow(), piece_warp(), piece_saucer(), piece_ring_lights(), piece_pylon_beams(), piece_banner(), piece_bar_glow(), piece_dome()]
    from . import mothership_views as views  # the three extra rooms (gallery, reactor, bridge) and the passage frame
    sprites["passage_frame"] = views.passage_frame()
    return {"design_size": [W, H], "layers": layers, "anchors": anchors, "sprites": sprites, "pieces": pieces, "views": views.build_views(),
            "pieces_note": "pos = top-left in design space, size in design px, pivot = anim origin in texture px; z behind = under the crowd, front = over it; "
                           "glowing pieces use light colours on transparent and are meant to be drawn additively"}


# ---- interlude: a UFO over the Night One club -------------------------------------------------------------------------------------------

def spr_ufo() -> dict:
    """A huge saucer seen from below, 900 x 260 design px: hull rim, a ring of lights, a glowing underside."""
    w, h = 900, 260
    cx = w / 2
    defs = lin_grad("uh", [(0, "#c4d4ff"), (0.45, "#6a86d8"), (1, "#1c2a78")], 0, 0, 0, 1)
    defs += lin_grad("ub", [(0, "#8aa6ff"), (1, "#14226a")], 0, 0, 0, 1)
    defs += rad_grad("ug", [(0, "#ffffff"), (0.25, "#bfffe8"), (0.6, GREEN), (1, "#0a6a8a")], 0.5, 0.5, 0.5)
    defs += rad_grad("uhalo", [(0, GREEN, 0.5), (1, GREEN, 0.0)])
    defs += clip("ucl", ellipse(cx, 150, 400, 78))
    d = ""
    # upper dome peeking over the rim
    d += path(f"M{cx - 150} 74 Q{cx - 120} 6 {cx} 4 Q{cx + 120} 6 {cx + 150} 74 Z", "url(#ub)", OUT, 4)
    d += path(f"M{cx - 100} 70 Q{cx - 76} 20 {cx - 20} 14", None, "#e6f2ff", 4, sop=0.55)
    for k in range(-2, 3):
        d += line((cx + k * 50, 10 + abs(k) * 8), (cx + k * 62, 72), OUT, 2.4, 0.6)
    # saucer body: a lens-shaped silhouette; the near rim is thick, the underside is lighter
    body = f"M6 140 Q40 66 {cx} 58 Q{w - 40} 66 {w - 6} 140 Q{w - 70} 244 {cx} 252 Q70 244 6 140 Z"
    d += path(body, "url(#uh)", OUT, 5)
    d += path(f"M20 142 Q{cx} 40 {w - 20} 142 Q{cx} 226 20 142 Z", "url(#ub)", OUT, 3)
    d += ellipse(cx, 150, 400, 80, "#0a1442", None, op=0.0)
    # outer rim lights in perspective (ellipse ring)
    for k in range(34):
        a = k * math.tau / 34
        x, y = cx + 384 * math.cos(a), 148 + 70 * math.sin(a)
        d += circle(x, y, 7.5, [GREEN, AMB, MAG, CYAN][k % 4], None, op=0.2) + circle(x, y, 4.2, [GREEN, AMB, MAG, CYAN][k % 4], OUT, 1.4) + circle(x - 1, y - 1, 1.4, "#ffffff", None, op=0.9)
    d += ellipse(cx, 150, 330, 60, None, OUT, 3.4, sop=0.8) + ellipse(cx, 150, 330, 60, None, CYAN, 1.4, sop=0.6)
    # panel seams on the underside
    for k in range(-7, 8):
        a = k * 0.2
        d += line((cx + math.sin(a) * 120, 150 + math.cos(a) * 12), (cx + math.sin(a) * 330, 150 + math.cos(a) * 60), OUT, 1.6, 0.5)
    for rr in (210, 130):
        d += ellipse(cx, 150, rr, rr * 0.18, None, OUT, 1.8, sop=0.55)
    # central emitter
    d += ellipse(cx, 150, 150, 36, "url(#uhalo)") + ellipse(cx, 150, 100, 24, "#0a1442", OUT, 3.4) + ellipse(cx, 150, 90, 20, "url(#ug)", None)
    for rr in (70, 48, 26):
        d += ellipse(cx, 150, rr, rr * 0.22, None, "#ffffff", 1.4, sop=0.7)
    d += ellipse(cx, 150, 100, 24, None, GREEN, 1.6, sop=0.9)
    d += path(f"M30 118 Q60 84 {cx - 200} 70", None, "#ffffff", 3, sop=0.45)
    info = write_svg("interlude/ufo.svg", (0, 0, w, h), d, defs)
    return {"file": "source/interlude/ufo.svg", "pivot": pivot_in(info, (cx, 150)), "px_scale": 0.5, "size": [w, h]}


def spr_sparkle() -> dict:
    d = ""
    for k, (r, op) in enumerate(((14, 0.18), (9, 0.3))):
        d += circle(0, 0, r, "#ffffff", None, op=op)
    d += path("M0 -16 Q1.5 -1.5 16 0 Q1.5 1.5 0 16 Q-1.5 1.5 -16 0 Q-1.5 -1.5 0 -16 Z", "#ffffff", None)
    d += path("M0 -8 Q0.8 -0.8 8 0 Q0.8 0.8 0 8 Q-0.8 0.8 -8 0 Q-0.8 -0.8 0 -8 Z", "#ffffff", None, extra='transform="rotate(45)"')
    d += circle(0, 0, 2.6, "#ffffff")
    info = write_svg("interlude/sparkle.svg", (-18, -18, 18, 18), d)
    return {"file": "source/interlude/sparkle.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}


def _save(name: str, rgba) -> str:
    os.makedirs(lib.PNG_DIR, exist_ok=True)
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(lib.PNG_DIR, name), compress_level=9)
    return f"processed/{name}"


def build_interlude() -> dict:
    sprites = {"ufo": spr_ufo(), "sparkle": spr_sparkle()}
    # tractor beam: a soft column, narrow at the top and flaring wide at the floor, brighter core and edges; white to be tinted
    w, h = 240, 170  # shown at 2x: 480 x 340 design px
    yy, xx = np.mgrid[0:h, 0:w]
    t = yy / h
    half = (30 + 88 * t ** 1.15) * 1.0
    u = np.abs(xx - w / 2 + 0.5) / half
    body = np.clip(1 - u ** 2.2, 0, 1)
    core = np.clip(1 - u, 0, 1) ** 1.6
    edge = np.exp(-((u - 0.92) / 0.08) ** 2) * (u < 1.05)
    a = (0.45 * body + 0.4 * core + 0.18 * edge) * (0.55 + 0.45 * np.sin(t * math.pi * 0.5 + 0.2))
    a *= np.clip(t * 12, 0, 1) * np.clip((1 - t) * 10 + 0.55, 0, 1)
    arr = np.zeros((h, w, 4))
    arr[..., :3] = (225, 255, 240)
    arr[..., 3] = np.clip(a, 0, 1) * 255
    sprites["tractor_beam"] = {"file": _save("tractor_beam.png", arr), "pivot": [w / 2, 0], "px_scale": 2.0, "size": [w * 2, h * 2]}
    # underglow: a round soft glow, slightly flattened, with a faint ring
    w, h = 256, 128
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h / 2 + 0.5) / (h / 2))
    a = np.clip(1 - r, 0, 1) ** 1.8 * 0.9 + np.exp(-((r - 0.6) / 0.08) ** 2) * 0.18 * (r < 1)
    arr = np.zeros((h, w, 4))
    arr[..., :3] = (200, 255, 235)
    arr[..., 3] = np.clip(a, 0, 1) * 255
    sprites["ufo_glow"] = {"file": _save("ufo_glow.png", arr), "pivot": [w / 2, h / 2], "px_scale": 4.0, "size": [w * 4, h * 4]}
    # light flood: a full-screen green-white wash, brightest at the centre (160 x 90 shown at 1280 x 720)
    w, h = 160, 90
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h / 2 + 0.5) / (h / 2))
    a = 0.55 + 0.45 * np.clip(1 - r / 1.2, 0, 1) ** 1.2
    arr = np.zeros((h, w, 4))
    arr[..., 0], arr[..., 1], arr[..., 2] = 210, 255, 232
    arr[..., 3] = a * 255
    sprites["light_flood"] = {"file": _save("light_flood.png", arr), "pivot": [w / 2, h / 2], "px_scale": 8.0, "size": [1280, 720]}
    return {"sprites": sprites, "anchors": {"ufo_hover": [640, 92], "beam_floor": [640, 372]},
            "note": "ufo_hover = centre of the saucer's underside ellipse; the tractor_beam pivot (top centre) sits under it and reaches beam_floor"}
