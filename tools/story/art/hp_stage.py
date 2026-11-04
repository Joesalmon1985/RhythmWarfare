"""The hospital chapter's private room: you wake in a hospital bed in a sunny room, flowers, balloons and cards, your family around you.

`build_stage()` writes the `main` room (backdrop in one-point perspective, wooden hi-fi speakers, a rug-and-step riser, the over-bed table
as the desk strip), the shared lighting sprites (white and neutral so the runtime tints them), the re-themed deck pieces, 7 authored
`stage.pieces`, and calls hp_views.build_views() for corridor / cafeteria / garden plus the `passage_frame`. `build_silhouettes()` and
`build_interlude()` (eyelids, white wash, heartbeat trace) are called by chapter_hospital.py. Same layer / anchor / sprite ids as every chapter.
"""
from __future__ import annotations

import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw

from . import hp_props as P, lib, sprites as png_sprites, stage as S
from .hp_props import (CORAL, CREAM, GOLD, LEAF, LEAF_D, PAPER, PEACH, ROSE, SAND, SUN, TEAL, TEAL_D, TEAL_L, WOOD, WOOD_D, WOOD_L, Room)
from .lib import (OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, pivot_in, poly, rad_grad, rect,
                  write_svg)

W, H = 1280, 720
ROOM = Room(640, 130, 270, 1010, 52, 262)
VPX, VPY, FX0, FX1, FY0, FY1 = ROOM.vx, ROOM.vy, ROOM.fx0, ROOM.fx1, ROOM.fy0, ROOM.fy1
FLOOR_ROWS = ROOM.rows()
SPK_W, SPK_H = S.SPK_W, S.SPK_H
SPK_POS, SPK_WOOFERS = S.SPK_POS, S.SPK_WOOFERS


def floor_x(xf, y):
    return ROOM.floor_x(xf, y)


# ---- backdrop ------------------------------------------------------------------------------------------------------------------

def build_bed():
    """The hospital bed against the far wall: a white-and-wood head board, a patchwork quilt, pillows, a teddy and a heart cushion."""
    d = ""
    defs = lin_grad("hb", [(0, "#e8b97c"), (1, "#b87a42")], 0, 0, 0, 1)
    defs += lin_grad("fb", [(0, "#f6e4c8"), (1, "#d9b88a")], 0, 0, 0, 1)
    defs += lin_grad("pil", [(0, "#ffffff"), (1, "#efe2d2")], 0, 0, 0, 1)
    d += ellipse(640, 300, 186, 13, "#3a1f2e", None, op=0.2)
    # head board
    d += path("M512 236 L512 168 Q512 146 540 146 L740 146 Q768 146 768 168 L768 236 Z", "url(#hb)", OUT, 3.2)
    d += path("M524 232 L524 172 Q524 158 542 158 L738 158 Q756 158 756 172 L756 232 Z", "#f8ecd8", OUT, 2)
    d += path("M534 226 L534 176 Q534 166 546 166 L734 166 Q746 166 746 176 L746 226 Z", TEAL_L, None, op=0.55)
    for k in range(4):
        d += line((576 + k * 42, 170), (576 + k * 42, 224), "#ffffff", 1.6, 0.5)
    d += rect(506, 232, 14, 38, WOOD_D, OUT, 2.4, rx=3) + rect(760, 232, 14, 38, WOOD_D, OUT, 2.4, rx=3)
    # mattress and quilt (top face in perspective)
    d += poly([(520, 214), (760, 214), (790, 272), (490, 272)], "#fff6ea", OUT, 3)
    qs = [("#ff8f7a", "#ffc65a", "#7fd1c4", "#f4a5b4", "#9ab8f0", "#ffe9a8"), ("#7fd1c4", "#f4a5b4", "#ffe9a8", "#ff8f7a", "#ffc65a", "#9ab8f0"),
          ("#ffc65a", "#9ab8f0", "#ff8f7a", "#7fd1c4", "#ffe9a8", "#f4a5b4")]
    rows = 5
    cols = 6
    for r in range(rows):
        t0, t1 = 0.14 + 0.86 * r / rows, 0.14 + 0.86 * (r + 1) / rows
        y0, y1 = 214 + 58 * t0, 214 + 58 * t1
        xl0, xr0 = 520 - 30 * t0, 760 + 30 * t0
        xl1, xr1 = 520 - 30 * t1, 760 + 30 * t1
        for c in range(cols):
            a0, a1 = c / cols, (c + 1) / cols
            col = qs[r % 3][(c + r) % 6]
            d += poly([(xl0 + (xr0 - xl0) * a0, y0), (xl0 + (xr0 - xl0) * a1, y0), (xl1 + (xr1 - xl1) * a1, y1), (xl1 + (xr1 - xl1) * a0, y1)], col, "#fff6ea", 1.4)
            if (r + c) % 3 == 0:
                cxm = xl0 + (xr0 - xl0) * (a0 + a1) / 2
                d += P.heart_shape(cxm, (y0 + y1) / 2 + 1, 3.0 + t0 * 2, "#ffffff", 0.0, None) if False else circle(cxm, (y0 + y1) / 2, 2.0 + t0, "#ffffff", None, op=0.7)
    d += poly([(520, 214), (760, 214), (790, 272), (490, 272)], "#ffffff", None, op=0.0)
    d += poly([(520, 214), (760, 214), (766, 226), (514, 226)], "#fffaf0", OUT, 2.2)  # the folded-back sheet
    for k in range(9):
        d += circle(526 + k * 29, 226, 2.4, "#ffffff", None, op=0.0)
    # pillows
    for cx in (582, 698):
        d += ellipse(cx, 220, 52, 17, "url(#pil)", OUT, 2.6) + path(f"M{cx - 38} 218 Q{cx} 212 {cx + 38} 218", None, "#d9c8b4", 1.6, sop=0.8)
        d += ellipse(cx - 20, 216, 14, 4, "#ffffff", None, op=0.7)
    # foot board
    d += poly([(486, 272), (794, 272), (798, 296), (482, 296)], "url(#fb)", OUT, 3)
    d += rect(480, 266, 320, 10, WOOD_L, OUT, 2.6, rx=4)
    d += rect(500, 278, 280, 14, TEAL_L, OUT, 1.8, rx=3, op=0.85)
    for k in range(7):
        d += circle(520 + k * 40, 285, 2.6, "#ffffff", None, op=0.8)
    d += rect(476, 270, 12, 40, WOOD_D, OUT, 2.4, rx=3) + rect(792, 270, 12, 40, WOOD_D, OUT, 2.4, rx=3)
    # teddy and cushion on the quilt
    d += P.teddy(560, 262, 1.25, "#c98f55")
    d += P.cushion_heart(738, 246, 15, "#ff8f9a")
    d += circle(738, 262, 0, "#fff")
    return d, defs


def build_backdrop() -> dict:
    d, defs = "", ""
    defs += lin_grad("room_bg", [(0, "#fff6e6"), (1, "#f4dcc0")], 0, 0, 0, 1)
    d += rect(0, 0, W, H, "url(#room_bg)")
    # ceiling
    defs += lin_grad("ceil", [(0, "#fffaf0"), (1, "#f6e3c8")], 0, 0, 0, 1)
    d += poly([(0, -6), (W, -6), (FX1, FY0), (FX0, FY0)], "url(#ceil)")
    for xf in range(-700, 1800, 70):  # tile seams run to the vanishing point
        a = (xf, FY0)
        s = 1.9
        b = ROOM.ceil_pt(xf, s)
        if FX0 - 40 <= xf <= FX1 + 40:
            d += line(a, b, "#e2c9a4", 1.2, 0.8)
    for s in (1.18, 1.42, 1.75):
        pl, pr = ROOM.ceil_pt(FX0 - 160, s), ROOM.ceil_pt(FX1 + 160, s)
        d += line(pl, pr, "#e2c9a4", 1.2, 0.8)
    for xa, xb, s0, s1 in ((400, 540, 1.3, 1.62), (740, 880, 1.3, 1.62)):  # warm recessed light panels
        q = [ROOM.ceil_pt(xa, s0), ROOM.ceil_pt(xb, s0), ROOM.ceil_pt(xb, s1), ROOM.ceil_pt(xa, s1)]
        d += poly(q, "#fff2c4", "#d9b57a", 1.6) + poly(q, "#ffffff", None, op=0.4)
    d += poly([(0, -6), (W, -6), (W, -6), (0, -6)], "#fff", None, op=0.0)
    # far wall: wallpaper, wainscot, skirting
    defs += lin_grad("fw", [(0, "#f8e3c4"), (1, "#f1d1a8")], 0, 0, 0, 1)
    d += rect(FX0, FY0, FX1 - FX0, FY1 - FY0, "url(#fw)")
    for x in range(int(FX0) + 6, int(FX1), 22):  # soft wallpaper stripes
        d += rect(x, FY0, 9, 156, "#ffffff", None, op=0.22)
    for x in range(int(FX0) + 16, int(FX1), 44):  # tiny hearts on the wallpaper
        for y in (80, 118, 156):
            d += P.heart_shape(x + (11 if y == 118 else 0), y, 1.8, "#f4a5b4", 0, None) if False else circle(x + (11 if y == 118 else 0), y, 1.5, "#ffc9a4", None, op=0.8)
    d += rect(FX0, 204, FX1 - FX0, 58, "#7cc4b8")
    for x in range(int(FX0), int(FX1), 46):
        d += rect(x + 5, 212, 36, 40, "#8fd2c6", "#5aa89e", 1.4, rx=3)
    d += rect(FX0, 200, FX1 - FX0, 7, "#fff6ea", OUT, 1.8)
    d += rect(FX0, 255, FX1 - FX0, 7, "#fff6ea", OUT, 1.8)
    # side walls (perspective), wainscot and rail
    defs += lin_grad("lw", [(0, "#d6b088"), (1, "#f1d1a8")], 0, 0, 1, 0)
    defs += lin_grad("rw", [(0, "#f1d1a8"), (1, "#d6b088")], 0, 0, 1, 0)
    yl_top = ROOM.lwall(0, FY0)
    yr_top = ROOM.rwall(W, FY0)
    d += poly([(0, yl_top), (FX0, FY0), (FX0, FY1), (0, ROOM.lwall(0, FY1))], "url(#lw)")
    d += poly([(FX1, FY0), (W, yr_top), (W, ROOM.rwall(W, FY1)), (FX1, FY1)], "url(#rw)")
    d += poly(ROOM.wall_poly(-1, 0, FX0, 204, FY1), "#6fb9ad") + poly(ROOM.wall_poly(1, FX1, W, 204, FY1), "#6fb9ad")
    d += poly(ROOM.wall_poly(-1, 0, FX0, 199, 205), "#fff6ea", OUT, 1.6) + poly(ROOM.wall_poly(1, FX1, W, 199, 205), "#fff6ea", OUT, 1.6)
    d += poly(ROOM.wall_poly(-1, 0, FX0, 253, FY1), "#fff6ea", OUT, 1.6) + poly(ROOM.wall_poly(1, FX1, W, 253, FY1), "#fff6ea", OUT, 1.6)
    for xf in range(-4, 6):  # wainscot panel lines on the side walls
        xl = FX0 - xf * 56
        if 6 < xl < FX0:
            d += line((xl, ROOM.lwall(xl, 207)), (xl, ROOM.lwall(xl, 252)), "#5aa89e", 1.4, 0.8)
        xr = FX1 + xf * 56
        if FX1 < xr < W - 6:
            d += line((xr, ROOM.rwall(xr, 207)), (xr, ROOM.rwall(xr, 252)), "#5aa89e", 1.4, 0.8)
    # floor: honey planks with a woven oval rug in the dance circle
    fdefs, fbody = P.plank_floor(ROOM, "fl", base="#d29a58", plank=40, seed=3)
    defs += fdefs
    d += fbody
    d += line((FX0, FY1), (FX1, FY1), "#8a5a30", 1.6, 0.6)
    # window light patches lying on the floor (the sun comes in from the right)
    defs += lin_grad("patch", [(0, "#fff2b8", 0.0), (0.4, "#fff2b8", 0.42), (1, "#fff2b8", 0.1)], 1, 0, 0, 0)
    for k in range(3):
        y0 = 292 + k * 46
        d += poly([(1280, y0 - 30), (1280, y0 + 12), (760 - k * 24, y0 + 36 + k * 6), (700 - k * 26, y0 - 4 + k * 6)], "url(#patch)")
    d += P.oval_rug(640, 372, 296, 58, [("#e0a37a", 1.0), ("#ffe6c8", 0.93), ("#4fb3a9", 0.86), ("#ffe6c8", 0.74), ("#ff8f7a", 0.68), ("#ffd98a", 0.52), ("#7fd1c4", 0.44), ("#ffe6c8", 0.3)], "rug")
    # window on the right wall, left of it a notice board on the left wall
    wq = ROOM.wall_poly(1, 1138, 1264, 72, 216)
    wdefs, wbody = P.window_scene(wq, "win", sun_xy=(1200, 90))
    defs += wdefs
    d += poly([(wq[0][0] - 8, wq[0][1] - 8), (wq[1][0] + 8, wq[1][1] - 8), (wq[2][0] + 8, wq[2][1] + 8), (wq[3][0] - 8, wq[3][1] + 8)], "#fff6ea", OUT, 3)
    d += wbody
    xm = (wq[0][0] + wq[1][0]) / 2
    d += line((xm, (wq[0][1] + wq[1][1]) / 2), (xm, (wq[2][1] + wq[3][1]) / 2), "#fff6ea", 5) + line((wq[0][0], (wq[0][1] + wq[3][1]) / 2), (wq[1][0], (wq[1][1] + wq[2][1]) / 2), "#fff6ea", 5)
    d += poly([(wq[3][0] - 12, wq[3][1] + 8), (wq[2][0] + 12, wq[2][1] + 8), (wq[2][0] + 12, wq[2][1] + 18), (wq[3][0] - 12, wq[3][1] + 18)], "#fff6ea", OUT, 2.4)  # sill
    for sgn, xx in ((-1, wq[0][0] - 12), (1, wq[1][0] + 4)):  # curtains
        top0 = ROOM.rwall(xx, 66)
        d += poly([(xx, top0), (xx + sgn * 0 + 18, ROOM.rwall(xx + 18, 66)), (xx + 18, ROOM.rwall(xx + 18, 222)), (xx, ROOM.rwall(xx, 222))], "#ff8f7a", OUT, 2.4)
    d += poly([(wq[0][0] - 12, ROOM.rwall(wq[0][0] - 12, 66) - 2), (W, ROOM.rwall(W, 66) - 2), (W, ROOM.rwall(W, 66) + 4), (wq[0][0] - 12, ROOM.rwall(wq[0][0] - 12, 66) + 4)], "#c98f55", OUT, 2)
    # notice board with drawings on the left wall
    nb = ROOM.wall_poly(-1, 20, 124, 96, 190)
    d += poly(nb, "#d9a066", OUT, 3) + poly([(nb[0][0] + 6, nb[0][1] + 6), (nb[1][0] - 6, nb[1][1] + 4), (nb[2][0] - 6, nb[2][1] - 4), (nb[3][0] + 6, nb[3][1] - 6)], "#f0d4a6", OUT, 1.6)
    for k, (ux, uy, col) in enumerate(((36, 108, "#ff8f7a"), (70, 112, "#9ab8f0"), (98, 106, "#ffe27a"), (46, 148, "#b9d9a3"), (88, 150, "#f4a5b4"))):
        q = ROOM.wall_poly(-1, ux - 12, ux + 12, uy - 10 + (uy - 100) * 0, uy + 14)
        d += poly(q, col, OUT, 1.4)
        d += circle((q[0][0] + q[1][0]) / 2, (q[0][1] + q[2][1]) / 2, 3.2, "#ffffff", None, op=0.7)
    # door (closed): the doorway anchor, at the left end of the far wall
    dx, dy, dw, dh = 284, 138, 70, 124
    d += rect(dx - 6, dy - 6, dw + 12, dh + 6, "#fff6ea", OUT, 3, rx=3)
    d += rect(dx, dy, dw, dh, "#d9a066", OUT, 2.4)
    for yy in (dy + 14, dy + 66):
        d += rect(dx + 8, yy, dw - 16, 42 if yy < dy + 20 else 46, "#c98c52", "#a8703c", 1.6, rx=2)
    d += rect(dx + 14, dy + 20, dw - 28, 32, "#e8f4f4", OUT, 1.8, rx=2) + rect(dx + 14, dy + 20, dw - 28, 32, "#ffffff", None, op=0.0)
    d += line((dx + 18, dy + 24), (dx + 32, dy + 42), "#ffffff", 2, 0.8)
    d += circle(dx + dw - 10, dy + 70, 4, "#ffe27a", OUT, 1.8) + P.heart_shape(dx + dw / 2, dy + 78, 5, "#ff8f9a", 1.6)
    d += rect(dx + 18, dy - 22, dw - 36, 13, "#fff6ea", OUT, 2, rx=3) + P.heart_shape(dx + dw / 2, dy - 15.5, 3.6, "#ff6f8f", 1.2)
    # wall pictures and the information board's frame (the runtime paints into the dark panel)
    d += P.picture([(374, 104), (412, 104), (412, 148), (374, 148)], "#ffe9a8", "sun")
    d += P.picture([(884, 102), (936, 102), (936, 150), (884, 150)], "#cdeee6", "hills")
    d += P.picture([(944, 92), (984, 92), (984, 134), (944, 134)], "#f8d6e0", "flower")
    led = (400, 56, 480, 44)
    d += rect(led[0] - 10, led[1] - 8, led[2] + 20, led[3] + 16, "#c98f55", OUT, 3.4, rx=6)
    d += rect(led[0] - 4, led[1] - 3, led[2] + 8, led[3] + 6, "#fff6ea", OUT, 2, rx=4)
    d += rect(led[0], led[1], led[2], led[3], "#22303a", None)
    for xx in (led[0] - 10, led[0] + led[2] + 10):
        d += circle(xx, led[1] + led[3] + 12, 3, "#ffe27a", OUT, 1.6)
    d += line((led[0] + 40, led[1] - 8), (led[0] + 40, -6), OUT, 3) + line((led[0] + led[2] - 40, led[1] - 8), (led[0] + led[2] - 40, -6), OUT, 3)
    # the bed and the bedside cabinets
    bd, bdefs = build_bed()
    defs += bdefs
    for cx0, cx1 in ((430, 500), (780, 850)):
        d += rect(cx0, 206, cx1 - cx0, 56, "#d9a066", OUT, 3, rx=3) + rect(cx0 - 3, 200, cx1 - cx0 + 6, 9, WOOD_L, OUT, 2.4, rx=3)
        d += rect(cx0 + 6, 214, cx1 - cx0 - 12, 18, "#c98c52", "#a8703c", 1.4, rx=2) + rect(cx0 + 6, 235, cx1 - cx0 - 12, 20, "#c98c52", "#a8703c", 1.4, rx=2)
        d += circle((cx0 + cx1) / 2, 223, 2.6, "#ffe27a", OUT, 1.2) + circle((cx0 + cx1) / 2, 245, 2.6, "#ffe27a", OUT, 1.2)
    d += bd
    d += P.lamp_shade(486, 200, 40) + P.lamp_shade(843, 200, 40) if False else ""
    d += P.lamp_shade(487, 200, 38, "#ffe9a8")
    d += rect(804, 182, 8, 18, "#a8b4c0", OUT, 1.6)  # the monitor's stand (the screen itself is the `heart_monitor` piece)
    # bedside lamp glow, a soft warm pool on the wall
    defs += P.glow_defs("lampg", "#ffd27a", 0.5)
    d += ellipse(487, 172, 64, 56, "url(#lampg)")
    # radiator under the window and a chair by the bed
    d += poly([(FX0 + 8, 262), (FX0 + 8, 262)], "#fff", None, op=0.0)
    # window glow washing the right half
    defs += lin_grad("wg", [(0, "#fff2b8", 0.0), (1, "#fff2b8", 0.12)], 0, 0, 1, 0)
    d += rect(900, 0, 380, 420, "url(#wg)")
    gdefs, gbody = P.grade(ROOM, "grade")
    defs += gdefs
    d += gbody
    return write_svg("backdrop.svg", (0, 0, W, H), d, defs)


# ---- speakers (wooden hi-fi cabinets) ------------------------------------------------------------------------------------------------

def build_speaker(side: int):
    d = ""
    defs = lin_grad("cab", [(0, "#d9a066"), (0.5, "#c98c52"), (1, "#9a6434")], 0, 0, 1, 0)
    defs += lin_grad("cabs", [(0, "#ffffff", 0.0), (1, "#3a1f2e", 0.2)], 0, 0, 1, 0)
    d += rect(4, 6, SPK_W - 8, SPK_H - 12, "url(#cab)", OUT, 4, rx=8)
    d += rect(10, 12, SPK_W - 20, SPK_H - 24, "#f3e2c0", "#a8703c", 2, rx=5)  # the cloth grille
    for k in range(0, 40):  # woven grille texture
        d += line((12, 14 + k * 3.6), (SPK_W - 12, 14 + k * 3.6), "#d9c29a", 0.8, 0.6)
    d += rect(4, 6, SPK_W - 8, SPK_H - 12, "url(#cabs)", None, rx=8)
    for (x, y, r) in SPK_WOOFERS:
        d += circle(x, y, r + 5, "#8a5a30", OUT, 3) + circle(x, y, r + 2, "#3a2418", None)
    d += rect(36, 150, 40, 8, "#fff6ea", OUT, 1.8, rx=2) + P.heart_shape(56, 154, 2.6, "#ff6f8f", 0.8)
    d += rect(12, 164, 14, 6, WOOD_D, OUT, 2) + rect(86, 164, 14, 6, WOOD_D, OUT, 2)  # little feet
    d += line((8, 30), (8, 140), "#fff2b8", 2.0, 0.55)
    return write_svg("speaker_%s.svg" % ("l" if side < 0 else "r"), (0, 0, SPK_W, SPK_H), d, defs)


def build_riser():
    """A low wooden step with a striped rug on top: the 'storytime' platform at the back centre."""
    w, h = 240, 34
    d = ""
    defs = lin_grad("rt", [(0, "#f6d6a0"), (1, "#e0a868")], 0, 0, 0, 1)
    defs += lin_grad("rf", [(0, "#c98c52"), (1, "#8a5a30")], 0, 0, 0, 1)
    d += poly([(22, 3), (w - 22, 3), (w - 2, 16), (2, 16)], "url(#rt)", OUT, 3)
    for k in range(7):
        d += poly([(26 + k * 26 - k * 0.4, 5), (26 + k * 26 + 13, 5), (14 + k * 30 + 8, 14), (6 + k * 31, 14)], [CORAL, CREAM, TEAL_L][k % 3], None, op=0.9)
    d += poly([(2, 16), (w - 2, 16), (w - 2, h - 3), (2, h - 3)], "url(#rf)", OUT, 3)
    for k in range(1, 6):
        d += line((2 + k * (w - 4) / 6, 17), (2 + k * (w - 4) / 6, h - 5), "#6a4020", 2, 0.4)
    d += line((24, 6), (w - 24, 6), "#ffffff", 1.4, 0.5)
    return write_svg("riser.svg", (0, 0, w, h), d, defs)


# ---- desk strip and deck pieces (the over-bed table) -------------------------------------------------------------------------------------

def build_desk_top():
    w, h = 1280, 260
    d = ""
    defs = lin_grad("dk", [(0, "#e8b97c"), (0.06, "#c98f55"), (1, "#7a4a28")], 0, 0, 0, 1)
    defs += lin_grad("lip", [(0, "#ffe9c4"), (0.5, "#e2b47c"), (1, "#b87a42")], 0, 0, 0, 1)
    d += rect(0, 0, w, h, "url(#dk)")
    d += rect(0, 0, w, 16, "url(#lip)")
    d += line((0, 16), (w, 16), OUT, 3.5)
    d += line((0, 2.5), (w, 2.5), "#fff6ea", 1.6, 0.8)
    rng = random.Random(6)
    for y in range(24, h, 7):  # wood grain
        x0 = rng.uniform(0, 300)
        d += path(f"M{f(x0)} {y} Q{f(x0 + 400)} {f(y + rng.uniform(-3, 3))} {f(x0 + 900)} {y}", None, "#6a3a1a", 1.0, sop=0.12)
    for x0, x1 in ((10, 424), (856, 1270)):  # the pad wings: cream laminate inset with a teal edge
        d += rect(x0, 26, x1 - x0, h - 36, "#6a3a1a", OUT, 2.6, rx=14, op=0.42)
        d += rect(x0 + 5, 31, x1 - x0 - 10, h - 46, None, TEAL, 1.6, rx=11, sop=0.7)
        for sx, sy in ((x0 + 12, 38), (x1 - 12, 38), (x0 + 12, h - 22), (x1 - 12, h - 22)):
            d += circle(sx, sy, 4, "#ffd98a", OUT, 1.6) + line((sx - 2.2, sy - 2.2), (sx + 2.2, sy + 2.2), OUT, 1.1)
        for k in range(5):
            d += rect(x0 + 30 + k * 12, h - 24, 7, 3, "#4a2a14", None, op=0.8)
    mx0, mx1 = 436, 844
    d += rect(mx0, 26, mx1 - mx0, h - 36, "#2f857f", OUT, 3, rx=12)
    d += rect(mx0 + 5, 31, mx1 - mx0 - 10, h - 46, None, "#fff3e0", 1.4, rx=9, sop=0.8)
    for k in range(0, 17):
        x = mx0 + 24 + k * ((mx1 - mx0 - 48) / 16.0)
        d += line((x, 36), (x, 36 + (9 if k % 4 == 0 else 5)), "#d8f4ee", 1.4, 0.75)
        d += line((x, h - 30), (x, h - 30 - (9 if k % 4 == 0 else 5)), "#d8f4ee", 1.4, 0.75)
    d += rect(mx0 + 60, h - 62, mx1 - mx0 - 120, 10, "#1d4f4b", OUT, 2, rx=5)
    d += rect(mx0 + 66, h - 59, mx1 - mx0 - 132, 3, "#9fdcd2", None, op=0.5)
    for x in (mx0 + 40, mx1 - 56):
        d += rect(x, 60, 16, 80, "#1d4f4b", OUT, 2, rx=3)
        for k in range(8):
            d += rect(x + 3, 64 + k * 9.4, 10, 5, ["#9fdcd2", "#9fdcd2", "#9fdcd2", "#b9e98a", "#b9e98a", "#ffc65a", "#ffc65a", "#ff8f7a"][k], None, op=0.32)
    d += P.heart_shape(640, 70, 12, "#ff8f9a", 2.4)  # a little heart badge on the mixer
    return write_svg("desk_top.svg", (0, 0, w, h), d, defs)


def spr_deck(sprites):
    SZ, hole = 240, 200
    o = (SZ - hole) / 2
    defs = lin_grad("bz", [(0, "#f0c690"), (0.5, "#c98f55"), (1, "#8a5a30")], 0, 0, 1, 1)
    defs += lin_grad("bzn", [(0, TEAL_L), (0.5, "#ffffff"), (1, CORAL)], 0, 0, 1, 1)
    outer = f"M{26} 0 H{SZ - 26} Q{SZ} 0 {SZ} 26 V{SZ - 26} Q{SZ} {SZ} {SZ - 26} {SZ} H26 Q0 {SZ} 0 {SZ - 26} V26 Q0 0 26 0 Z"
    inner = (f"M{o + 20} {o} H{SZ - o - 20} Q{SZ - o} {o} {SZ - o} {o + 20} V{SZ - o - 20} Q{SZ - o} {SZ - o} {SZ - o - 20} {SZ - o} "
             f"H{o + 20} Q{o} {SZ - o} {o} {SZ - o - 20} V{o + 20} Q{o} {o} {o + 20} {o} Z")
    d = f'<path d="{outer} {inner}" fill="url(#bz)" fill-rule="evenodd"/>'
    d += path(outer, None, OUT, 4) + path(inner, None, OUT, 3) + path(inner, None, "url(#bzn)", 2.6, sop=0.95)
    d += path(outer, None, "#fff6ea", 1.4, sop=0.45)
    for sx, sy in ((11, 11), (SZ - 11, 11), (11, SZ - 11), (SZ - 11, SZ - 11)):
        d += circle(sx, sy, 5.4, "#ffd98a", OUT, 2) + line((sx - 2.6, sy - 2.6), (sx + 2.6, sy + 2.6), OUT, 1.4)
    info = write_svg("props/pad_bezel.svg", (0, 0, SZ, SZ), d, defs)
    sprites["pad_bezel"] = {"file": "source/props/pad_bezel.svg", "pivot": pivot_in(info, (SZ / 2, SZ / 2)), "px_scale": 0.5, "inner_ratio": hole / SZ}

    R = 120
    d = ""
    defs = rad_grad("vin", [(0, "#4a2a30"), (0.55, "#2a1620"), (1, "#1a0c14")], 0.5, 0.5, 0.5)
    defs += lin_grad("lab", [(0, "#ff9a8a"), (1, "#ffc65a")], 0, 0, 1, 1)
    d += circle(0, 0, R, "#e2b47c", OUT, 4) + circle(0, 0, R - 6, None, "#fff3e0", 1.4, sop=0.7)
    for k in range(60):
        a = k * math.tau / 60
        d += circle(math.cos(a) * (R - 11), math.sin(a) * (R - 11), 1.7, "#fff6ea" if k % 5 else TEAL, None, op=0.95)
    d += circle(0, 0, R - 20, "url(#vin)", OUT, 3)
    for rr in range(46, R - 22, 5):
        d += circle(0, 0, rr, None, "#8a5a60" if rr % 10 else "#5a3a40", 0.8, sop=0.3)
    d += path(f"M{-R + 34} -34 A{R - 28} {R - 28} 0 0 1 -34 {-R + 34}", None, "#ffffff", 5, sop=0.2)
    d += path(f"M{R - 34} 34 A{R - 28} {R - 28} 0 0 1 34 {R - 34}", None, "#ffffff", 5, sop=0.12)
    d += circle(0, 0, 38, "url(#lab)", OUT, 3)
    d += P.heart_shape(0, -6, 12, "#fff6ea", 2.0)
    d += rect(-22, 14, 44, 4, "#fff6ea", None, op=0.9) + rect(-14, 21, 28, 3.4, "#fff6ea", None, op=0.7)
    d += circle(0, 0, 4.5, "#fff6ea", OUT, 1.6)
    d += circle(0, -(R - 30), 4.2, CORAL, OUT, 1.4)
    info = write_svg("props/platter.svg", (-R - 3, -R - 3, R + 3, R + 3), d, defs)
    sprites["platter"] = {"file": "source/props/platter.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "diameter": 2 * R}

    defs = rad_grad("kb", [(0, "#fff6ea"), (0.6, "#e2c49a"), (1, "#b88a58")], 0.4, 0.35, 0.7)
    d = circle(0, 0, 24, "#6a3a1a", OUT, 3)
    for k in range(12):
        a = k * math.tau / 12 - math.pi / 2
        d += line((math.cos(a) * 20, math.sin(a) * 20), (math.cos(a) * 23, math.sin(a) * 23), "#ffd98a", 1.6, 0.9)
    d += circle(0, 0, 17, "url(#kb)", OUT, 2.4) + circle(-4, -5, 6, "#ffffff", None, op=0.3)
    d += line((0, -4), (0, -15), TEAL_D, 3.4) + line((0, -4), (0, -15), "#bff2e8", 1.3)
    info = write_svg("props/knob.svg", (-26, -26, 26, 26), d, defs)
    sprites["knob"] = {"file": "source/props/knob.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}

    d = rect(-5, -60, 10, 120, "#3a2418", OUT, 2.4, rx=5) + rect(-1.6, -55, 3.2, 110, "#ffd98a", None, op=0.5)
    for k in range(11):
        y = -55 + k * 11
        d += line((-12, y), (-8, y), "#fff3e0", 1.4, 0.8) + line((8, y), (12, y), "#fff3e0", 1.4, 0.8)
    info = write_svg("props/fader_slot.svg", (-16, -66, 16, 66), d)
    sprites["fader_slot"] = {"file": "source/props/fader_slot.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "travel": 110}
    defs = lin_grad("fc", [(0, "#fff6ea"), (0.5, "#e8cfa6"), (1, "#b88a58")], 0, 0, 0, 1)
    d = rect(-12, -17, 24, 34, "url(#fc)", OUT, 2.8, rx=5) + line((-12, 0), (12, 0), "#6a3a1a", 3) + line((-10, 0), (10, 0), TEAL, 1.6) + line((-9, -11), (9, -11), "#ffffff", 1.2, 0.6)
    info = write_svg("props/fader_cap.svg", (-16, -21, 16, 21), d, defs)
    sprites["fader_cap"] = {"file": "source/props/fader_cap.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
    d = rect(-26, -15, 52, 30, "url(#fc)", OUT, 2.8, rx=6)
    for k in range(-5, 6):
        d += line((k * 4.2, -11), (k * 4.2, 11), "#6a3a1a", 1.4, 0.4)
    d += line((0, -15), (0, 15), CORAL, 2.4)
    info = write_svg("props/crossfader.svg", (-30, -19, 30, 19), d, defs)
    sprites["crossfader"] = {"file": "source/props/crossfader.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
    d = rect(-20, -5, 40, 10, "#ffffff", None, rx=3)
    info = write_svg("props/vu_segment.svg", (-22, -7, 22, 7), d)
    sprites["vu_segment"] = {"file": "source/props/vu_segment.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
    d = circle(0, 0, 5.5, "#ffd98a", OUT, 1.8) + line((-2.6, -2.6), (2.6, 2.6), OUT, 1.4)
    info = write_svg("props/deck_screw.svg", (-8, -8, 8, 8), d)
    sprites["deck_screw"] = {"file": "source/props/deck_screw.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
    defs = lin_grad("lg", [(0, CORAL), (0.5, "#ffd98a"), (1, CORAL)], 0, 0, 1, 0)
    d = rect(0, 5, 1280, 11, "url(#lg)", None, op=0.14) + rect(0, 8, 1280, 6, "url(#lg)", None, op=0.28)
    d += rect(0, 9.5, 1280, 3, "url(#lg)", None, op=1.0) + rect(0, 10.4, 1280, 1.2, "#ffffff", None, op=0.8)
    info = write_svg("props/desk_lip_glow.svg", (0, 0, 1280, 16), d, defs)
    sprites["desk_lip_glow"] = {"file": "source/props/desk_lip_glow.svg", "pivot": pivot_in(info, (640, 8)), "px_scale": 0.5}


# ---- shared stage sprites --------------------------------------------------------------------------------------------------------------------

def spr_woofer(sprites):
    """The speaker cone: a cream paper cone in a wooden ring, pulsed by the runtime."""
    r = 50
    d = ""
    defs = rad_grad("cone", [(0, "#fff6ea"), (0.45, "#e9d4b0"), (1, "#b89268")], 0.42, 0.38, 0.75)
    defs += lin_grad("rim", [(0, "#e2b47c"), (1, "#8a5a30")], 0, 0, 1, 1)
    d += circle(0, 0, r - 3, "url(#rim)", OUT, 3.5) + circle(0, 0, r - 8, "#3a2418", None)
    d += circle(0, 0, r - 12, "url(#cone)", OUT, 2.2)
    for k, rr in enumerate((34, 28, 22, 17)):
        d += circle(0, 0, rr, None, "#b89268" if k % 2 == 0 else "#fff6ea", 1.4, sop=0.7)
    d += circle(0, 0, 12, "#ffd98a", OUT, 2.4) + P.heart_shape(0, 0, 5, "#ff8f9a", 1.2)
    d += path("M-32 -20 A38 38 0 0 1 -8 -36", None, "#ffffff", 3, sop=0.55)
    for k in range(8):
        a = k * math.tau / 8 + 0.4
        d += circle(math.cos(a) * (r - 6), math.sin(a) * (r - 6), 2, "#ffd98a", OUT, 1)
    info = write_svg("props/woofer.svg", (-r - 8, -r - 8, r + 8, r + 8), d, defs)
    sprites["woofer"] = {"file": "source/props/woofer.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "radius": r}


def spr_fixture(sprites):
    """A little brass ceiling spotlight on a yoke, lens pointing down (the 'moving head' of a cosy room)."""
    d = ""
    defs = lin_grad("body", [(0, "#f6d68a"), (1, "#b87a32")], 0, 0, 1, 0)
    d += rect(-11, 0, 22, 6, "#c9a05a", OUT, 2.4, rx=2)
    d += path("M-15 8 L-15 30 M15 8 L15 30", None, OUT, 8) + path("M-15 8 L-15 30 M15 8 L15 30", None, "#e6c27a", 4.4)
    d += rect(-8, 6, 16, 8, "#9a6a2e", OUT, 2.2, rx=2)
    d += rect(-12, 16, 24, 34, "url(#body)", OUT, 3, rx=5)
    d += line((-8, 20), (-8, 46), "#fff6d0", 1.6, 0.7)
    for yy in (24, 30, 36):
        d += line((-10, yy), (10, yy), "#6a4a1a", 1.2, 0.5)
    d += ellipse(0, 51, 11, 4.5, "#6a4a1a", OUT, 2.4) + ellipse(0, 51, 8, 3.2, "#fff6d0", None) + ellipse(0, 51, 3.2, 3.0, "#ffffff", None)
    d += circle(-15, 30, 3, "#e6c27a", OUT, 1.4) + circle(15, 30, 3, "#e6c27a", OUT, 1.4)
    info = write_svg("props/fixture.svg", (-22, -2, 22, 60), d, defs)
    sprites["fixture"] = {"file": "source/props/fixture.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "lens": [0, 51]}


def spr_disco_ball(sprites):
    """The mirror ball is a hanging paper-star lantern: a glowing core wrapped in folded paper points, on a ribbon."""
    d = ""
    cy, r = 66, 27
    defs = rad_grad("core", [(0, "#fffbe6"), (0.5, "#ffe08a"), (1, "#ffb85a")], 0.45, 0.4, 0.62)
    d += line((0, 0), (0, cy - r + 4), OUT, 3.4) + line((0, 0), (0, cy - r + 4), "#fff3e0", 1.4)
    d += circle(0, cy, r + 17, "#ffd98a", None, op=0.12) + circle(0, cy, r + 11, "#ffe9a8", None, op=0.18)
    n = 14
    for ring, (rl, col_a, col_b) in enumerate(((r + 22, "#ffe9c4", "#fff6ea"), (r + 14, "#ffc8a0", "#ffdcc0"))):
        for k in range(n):
            a = k * math.tau / n + (0.0 if ring == 0 else math.tau / n / 2) - math.pi / 2
            ca, sa = math.cos(a), math.sin(a)
            w = 0.2
            b0 = (math.cos(a - w) * (r * 0.8), cy + math.sin(a - w) * (r * 0.8))
            b1 = (math.cos(a + w) * (r * 0.8), cy + math.sin(a + w) * (r * 0.8))
            tip = (ca * rl, cy + sa * rl)
            d += poly([b0, tip, b1], col_a if k % 2 == 0 else col_b, OUT, 2.0)
            d += line(((b0[0] + b1[0]) / 2, (b0[1] + b1[1]) / 2), tip, "#ffffff", 1.0, 0.5)
    d += circle(0, cy, r, "url(#core)", OUT, 3)
    for k in range(6):
        a = k * math.tau / 6
        d += line((math.cos(a) * 4, cy + math.sin(a) * 4), (math.cos(a) * (r - 2), cy + math.sin(a) * (r - 2)), "#ffb85a", 1.4, 0.55)
    d += circle(-8, cy - 9, 5.4, "#ffffff", None, op=0.85)
    d += poly([(0, cy + r + 20), (-6, cy + r + 36), (6, cy + r + 36)], "#ff8f9a", OUT, 1.6) + circle(0, cy + r + 20, 3.4, "#ffd98a", OUT, 1.4)
    info = write_svg("props/disco_ball.svg", (-r - 30, -2, r + 30, cy + r + 42), d, defs)
    sprites["disco_ball"] = {"file": "source/props/disco_ball.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "radius": r, "ball_centre": [0, cy]}


def spr_glowstick(sprites):
    """A heart balloon on a stick (white, the runtime tints it); pivot at the grip."""
    d = line((0, 4), (0, 38), OUT, 9, cap="round") + line((0, 4), (0, 38), "#ffffff", 4.6, cap="round")
    d += line((0, 30), (0, 38), "#d8cbb0", 4.6, cap="butt")
    d += P.heart_shape(0, -12, 13, "#ffffff", 2.4) + path("M-8 -18 q3 -4 8 -2", None, "#bfbfd0", 1.8, sop=0.9)
    d += path("M-2 12 q-5 4 0 8 q5 4 0 8", None, OUT, 2.8) if False else ""
    info = write_svg("props/glowstick.svg", (-18, -30, 18, 44), d)
    sprites["glowstick"] = {"file": "source/props/glowstick.svg", "pivot": pivot_in(info, (0, 38)), "px_scale": 0.5, "length": 36}


def spr_door_open():
    """The door thrown open (overlay for the `doorway` at 284, 138, 70 x 124): the bright corridor beyond, a visitor with a balloon arriving."""
    ox, oy = 244, 138
    dx, dy, dw, dh = 284 - ox, 138 - oy, 70, 124
    defs = lin_grad("spill", [(0, "#fff0c0", 0.7), (0.55, "#ffe0a0", 0.25), (1, "#ffd890", 0.0)], 0, 0, 0, 1)
    defs += lin_grad("room", [(0, "#fffbe8"), (1, "#ffe9b8")], 0, 0, 0, 1)
    d = poly([(dx - 4, dy + dh), (dx + dw + 4, dy + dh), (dx + dw + 56, dy + dh + 88), (dx - 56, dy + dh + 88)], "url(#spill)")
    d += rect(dx - 6, dy - 6, dw + 12, dh + 6, "#fff6ea", OUT, 3, rx=3)
    d += rect(dx, dy, dw, dh, "url(#room)", None)
    d += rect(dx + 10, dy + 60, dw - 20, dh - 60, "#cdeee6", None, op=0.5)
    d += rect(dx + 14, dy + 18, dw - 28, 18, "#ffffff", None, op=0.7)
    cx = dx + dw / 2  # a visitor in the doorway, back-lit: head, shoulders, a balloon
    d += path(f"M{cx - 13} {dy + dh} Q{cx - 13} {dy + 76} {cx} {dy + 74} Q{cx + 13} {dy + 76} {cx + 13} {dy + dh} Z", "#7a4a4a", OUT, 1.6)
    d += circle(cx, dy + 64, 8, "#7a4a4a", OUT, 1.6)
    d += line((cx + 11, dy + 90), (cx + 21, dy + 50), OUT, 2.6) + line((cx + 11, dy + 90), (cx + 21, dy + 50), "#fff3e0", 1.0)
    d += P.balloon(cx + 21, dy + 38, 9, CORAL, None, True, 1.8)
    d += poly([(dx, dy), (dx + 13, dy + 7), (dx + 13, dy + dh - 3), (dx, dy + dh)], "#d9a066", OUT, 2.4)  # the leaf swung in
    d += line((dx + 6, dy + 14), (dx + 6, dy + dh - 8), "#a8703c", 1.4, 0.7) + circle(dx + 9, dy + 70, 2.2, "#ffe27a", OUT, 1)
    d += rect(dx + 18, dy - 22, dw - 36, 13, "#fff6ea", OUT, 2, rx=3) + P.heart_shape(dx + dw / 2, dy - 15.5, 3.6, "#ff6f8f", 1.2)
    info = write_svg("props/door_open.svg", (0, -8, 150, 214), d, defs)
    return {"file": "source/props/door_open.svg", "pivot": pivot_in(info, (0, -8)), "px_scale": 0.5, "pos": [ox, oy - 8]}


# ---- Pillow textures (warm vignette, dust-mote haze, paper confetti) -------------------------------------------------------------------

def _save_rgba(name, arr):
    os.makedirs(lib.PNG_DIR, exist_ok=True)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(lib.PNG_DIR, name), compress_level=9)
    return f"processed/{name}"


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def _white_rgba(a, tint=(255, 255, 255)):
    h, w = a.shape
    arr = np.zeros((h, w, 4))
    arr[..., 0], arr[..., 1], arr[..., 2] = tint
    arr[..., 3] = np.clip(a, 0, 1) * 255
    return arr


def build_light_sprites(sp):
    """The chapter's own daylight versions of the runtime's lighting sprites. The room is bright and the runtime draws beams, pools and
    blooms additively, so these carry far less light than Night One's club sprites: a beam is a soft shaft of sunlight with drifting dust
    (not a laser cone), a spot pool a gentle warm puddle, and the haze sunlit dust instead of club smoke. Still white / neutral: the
    runtime tints them with the chapter's palettes."""
    rng = np.random.default_rng(41)
    # beam: 256 x 640, soft-edged shaft widening down, brightest just below the lamp, gone before the floor
    w, h = 256, 640
    yy, xx = np.mgrid[0:h, 0:w]
    half = 9 + yy * (112.0 / h)
    t = np.abs(xx - w / 2 + 0.5) / half
    edge = np.clip(1 - t, 0, 1) ** 1.5
    core = np.exp(-(t / 0.32) ** 2)
    fade = np.clip(1 - yy / h, 0, 1) ** 1.35
    a = (0.62 * edge + 0.38 * core) * fade * 0.4
    a[:10] *= np.linspace(0.2, 1, 10)[:, None]
    motes = np.zeros((h, w))
    for _ in range(70):  # dust specks caught in the light
        my, mx = rng.uniform(30, h * 0.8), rng.uniform(-0.8, 0.8)
        cx = w / 2 + mx * (9 + my * 112.0 / h)
        r = rng.uniform(1.0, 2.2)
        motes += np.exp(-((xx - cx) ** 2 + (yy - my) ** 2) / (r * r)) * rng.uniform(0.25, 0.6)
    a = a + motes * edge * fade * 0.55
    sp["beam"] = {"file": _save_rgba("beam.png", _white_rgba(a)), "pivot": [w / 2, 0], "px_scale": 1.0, "length": h, "half_width_at_end": 121}
    # spot pool: a soft warm puddle of light, a faint rim, a dim centre (the dancer standing in it must stay readable)
    w, h = 400, 140
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h / 2 + 0.5) / (h / 2))
    a = np.clip(1 - r ** 2, 0, 1) ** 1.6 * 0.42 + np.exp(-((r - 0.84) / 0.08) ** 2) * 0.16 * (r < 1.0)
    sp["spot_pool"] = {"file": _save_rgba("spot_pool.png", _white_rgba(a)), "pivot": [w / 2, h / 2], "px_scale": 1.0}
    # haze: sunlit dust, two tileable 640 x 100 bands shown at 2x; thin and warm so the room never turns milky
    for name, seed, sx, sy in (("haze_a", 21, 70.0, 16.0), ("haze_b", 77, 54.0, 12.0)):
        w, h = 640, 100
        n1 = png_sprites.periodic_noise(w, h, sx, sy, seed)
        n2 = png_sprites.periodic_noise(w, h, sx * 0.45, sy * 0.45, seed + 1)
        m = _smooth((0.65 * n1 + 0.35 * n2 - 0.42) / 0.4)
        env = np.sin(np.linspace(0, np.pi, h)) ** 1.8
        a = m * env[:, None] * 0.32
        yy, xx = np.mgrid[0:h, 0:w]
        r2 = np.random.default_rng(seed)
        for _ in range(60):
            cx, cy, rr = r2.uniform(0, w), r2.uniform(15, h - 15), r2.uniform(0.8, 1.6)
            for ox in (-w, 0, w):  # wrap so the band still tiles
                a += np.exp(-((xx - cx - ox) ** 2 + (yy - cy) ** 2) / (rr * rr)) * 0.5 * env[:, None]
        sp[name] = {"file": _save_rgba(name + ".png", _white_rgba(a, (255, 236, 200))), "pivot": [w / 2, h / 2], "px_scale": 2.0, "tileable_x": True}


def build_png_sprites():
    sp = png_sprites.build_png_sprites()  # glow, beam, spot_pool, haze_a/b, vignette, confetti (all white / neutral)
    build_light_sprites(sp)
    w, h = 640, 360
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h / 2 + 0.5) / (h / 2))
    a = _smooth((r - 0.62) / 0.6) * 0.5
    arr = np.zeros((h, w, 4))
    arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3] = 62, 30, 34, a * 255
    sp["vignette"] = {"file": _save_rgba("vignette.png", arr), "pivot": [w / 2, h / 2], "px_scale": 2.0}
    # confetti: four 32 x 32 frames of paper confetti, a petal, a tiny heart and a star (supersampled 4x), warm palette
    big = Image.new("RGBA", (128 * 4, 32 * 4), (0, 0, 0, 0))
    dr = ImageDraw.Draw(big)
    cols = [(255, 143, 122), (255, 198, 90), (127, 209, 196), (244, 165, 180)]
    for i, c in enumerate(cols):
        cx, cy = (16 + i * 32) * 4, 16 * 4
        if i == 0:  # paper rectangle
            ang = math.radians(25)
            pts = [(cx + sx * math.cos(ang) - sy * math.sin(ang), cy + sx * math.sin(ang) + sy * math.cos(ang)) for sx, sy in ((-44, -22), (44, -22), (44, 22), (-44, 22))]
            dr.polygon(pts, fill=c + (255,), outline=(90, 47, 58, 255))
        elif i == 1:  # petal
            dr.ellipse((cx - 22, cy - 46, cx + 22, cy + 46), fill=c + (255,), outline=(90, 47, 58, 255))
        elif i == 2:  # tiny heart
            dr.polygon([(cx, cy + 40), (cx - 46, cy - 6), (cx - 30, cy - 36), (cx, cy - 16), (cx + 30, cy - 36), (cx + 46, cy - 6)], fill=c + (255,), outline=(90, 47, 58, 255))
        else:  # star
            pts = []
            for k in range(10):
                an = -math.pi / 2 + k * math.pi / 5
                rr = 48 if k % 2 == 0 else 20
                pts.append((cx + math.cos(an) * rr, cy + math.sin(an) * rr))
            dr.polygon(pts, fill=c + (255,), outline=(90, 47, 58, 255))
    small = big.resize((128, 32), Image.LANCZOS)
    small.save(os.path.join(lib.PNG_DIR, "confetti.png"), compress_level=9)
    sp["confetti"] = {"file": "processed/confetti.png", "pivot": [16, 16], "px_scale": 1.0, "frames": 4, "frame_size": [32, 32], "note": "paper, petal, heart, star"}
    return sp


# ---- silhouettes -------------------------------------------------------------------------------------------------------------------------------

def _sil_shape(kind, up):
    s = ""
    if kind == "a":  # a mum with a bun and a bouquet
        s += path("M-34 0 L-32 -24 Q-30 -42 -14 -46 Q-9 -48 -9 -54 L9 -54 Q9 -48 14 -46 Q30 -42 32 -24 L34 0 Z", "#fff")
        s += ellipse(0, -72, 17, 19, "#fff") + circle(0, -94, 9, "#fff")
        s += path("M-17 -70 Q-22 -50 -16 -38 L-26 -34 Q-28 -54 -17 -70 Z", "#fff")
        if up:
            for sx in (-1, 1):
                s += line((sx * 24, -40), (sx * 12, -108), "#fff", 11) + circle(sx * 11, -112, 7, "#fff")
            for k in range(5):  # the bouquet held high
                s += circle(-16 + k * 8, -126 - (k % 2) * 7, 8.5, "#fff")
            s += line((0, -112), (0, -122), "#fff", 6)
        else:
            s += line((26, -26), (30, -48), "#fff", 6) + circle(30, -54, 9, "#fff") + circle(22, -58, 6, "#fff") + circle(38, -58, 6, "#fff")
    elif kind == "b":  # a tall dad: broad shoulders, short hair, round glasses
        s += path("M-44 0 L-42 -26 Q-40 -44 -16 -48 Q-10 -50 -9 -57 L9 -57 Q10 -50 16 -48 Q40 -44 42 -26 L44 0 Z", "#fff")
        s += ellipse(0, -75, 18, 20, "#fff") + path("M-18 -80 Q-18 -100 0 -98 Q18 -100 18 -80 Q8 -88 -18 -80 Z", "#fff")
        if up:
            for sx in (-1, 1):
                s += line((sx * 36, -40), (sx * 52, -118), "#fff", 13) + circle(sx * 53, -122, 8, "#fff")
    else:  # a kid with a balloon
        s += path("M-24 0 L-22 -18 Q-20 -30 -9 -33 Q-6 -34 -6 -40 L6 -40 Q6 -34 9 -33 Q20 -30 22 -18 L24 0 Z", "#fff")
        s += ellipse(0, -58, 18, 19, "#fff") + circle(-17, -66, 7, "#fff") + circle(17, -66, 7, "#fff")
        s += ellipse(26, -112, 17, 21, "#fff") + line((20, -92), (12, -34), "#fff", 2.4)
        if up:
            for sx in (-1, 1):
                s += line((sx * 18, -28), (sx * 32, -86), "#fff", 10) + circle(sx * 33, -90, 6.5, "#fff")
    return s


def build_silhouettes():
    out = {}
    fills = {"a": "#7a4a58", "b": "#6e4452", "c": "#80505a"}
    for kind in ("a", "b", "c"):
        entry = {}
        for state in ("idle", "up"):
            up = state == "up"
            shape = _sil_shape(kind, up)
            body = ""
            for dx, dy, col in ((-2.2, -1.2, "#ffd98a"), (2.2, -1.2, "#ff9f8a")):
                body += S._recolor(shape, col, dx, dy)
            body += S._recolor(shape, fills[kind], 0, 0)
            info = write_svg(f"silhouettes/sil_{kind}_{state}.svg", (-84, -150 if up else -140, 84, 4), body)
            entry[state] = {"file": f"source/silhouettes/sil_{kind}_{state}.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
        entry["height"] = 100
        out[f"sil_{kind}"] = entry
    return out


# ---- the 7 pieces of the main room ----------------------------------------------------------------------------------------------------------------

def piece_sunbeams():
    w, h = 720, 330
    defs = lin_grad("ray", [(0, "#fff0b0", 0.22), (0.6, "#ffe49a", 0.11), (1, "#ffe49a", 0.0)], 1, 0, 0, 1)
    d = ""
    for k, (ya, yb, drop) in enumerate(((10, 52, 250), (70, 118, 270), (140, 186, 290), (206, 250, 300))):
        d += poly([(w + 4, ya), (w + 4, yb), (w - 540 + k * 20, yb + drop), (w - 640 + k * 30, ya + drop - 14)], "url(#ray)")
    rng = random.Random(14)
    for k in range(26):  # dust motes dancing in the light
        d += circle(rng.uniform(80, w - 30), rng.uniform(30, h - 40), rng.uniform(1.2, 2.8), "#fffbe0", None, op=rng.uniform(0.4, 0.9))
    write_svg("pieces/window_sunbeams.svg", (0, 0, w, h), d, defs)
    return P.piece("window_sunbeams", "source/pieces/window_sunbeams.svg", (560, 96), (w, h), "pulse", "behind", "add", pivot=(w - 20, 10))


def piece_fairy_lights():
    w, h = 1280, 96
    d = ""
    cols = ["#ffe27a", "#ff9f8a", "#9fe8d4", "#f4a5b4", "#ffd23f"]
    defs = P.glow_defs("fg", "#fff0b0", 0.8)
    for (x0, x1) in ((0, 560), (720, 1280)):
        mx, my = (x0 + x1) / 2, 20 + 80
        d += path(f"M{x0} 20 Q{mx} {my} {x1} 20", None, OUT, 3.4) + path(f"M{x0} 20 Q{mx} {my} {x1} 20", None, "#6a4a30", 1.4)
        n = 17
        for i in range(n):
            t = (i + 0.5) / n
            x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * mx + t * t * x1
            y = (1 - t) ** 2 * 20 + 2 * (1 - t) * t * my + t * t * 20
            c = cols[i % len(cols)]
            d += circle(x, y + 7, 13, c, None, op=0.22) + circle(x, y + 7, 8, "url(#fg)", None)
            d += poly([(x - 2.4, y), (x + 2.4, y), (x + 3, y + 4), (x - 3, y + 4)], "#6a4a30", OUT, 1)
            d += ellipse(x, y + 8.5, 3.6, 4.8, c, OUT, 1.4) + ellipse(x - 1, y + 6.5, 1, 1.6, "#ffffff", None, op=0.8)
    write_svg("pieces/fairy_lights.svg", (0, 0, w, h), d, defs)
    return P.piece("fairy_lights", "source/pieces/fairy_lights.svg", (0, 0), (w, h), "flicker", "front", "mix")


def piece_balloons():
    w, h = 140, 210
    d = ""
    cols = [CORAL, "#ffc65a", "#7fd1c4", "#9ab8f0", "#f4a5b4", "#ff6f8f"]
    anchor = (70, 196)
    pos = [(40, 44, 22), (96, 52, 21), (68, 22, 20), (24, 96, 19), (112, 100, 20), (68, 78, 21)]
    for k, (cx, cy, r) in enumerate(pos):
        d += P.balloon(cx, cy, r, cols[k % 6], anchor, True, 2.4)
    d += rect(52, 190, 36, 16, "#ff8f9a", OUT, 2.4, rx=2) + line((52, 197), (88, 197), "#fff3e0", 2) + line((70, 190), (70, 206), "#fff3e0", 2)
    write_svg("pieces/balloon_bunch.svg", (0, 0, w, h), d)
    return P.piece("balloon_bunch", "source/pieces/balloon_bunch.svg", (14, 90), (w, h), "bob", "behind", "mix", pivot=(70, 200))


def piece_cards():
    w, h = 720, 74
    d = ""
    p0, p1 = (0, 6), (720, 6)
    mx, my = 360, 6 + 56
    d += path(f"M0 6 Q{mx} {my} {w} 6", None, OUT, 3) + path(f"M0 6 Q{mx} {my} {w} 6", None, "#fff3e0", 1.2)
    n = 13
    rng = random.Random(8)
    for i in range(n):
        t = (i + 0.5) / n
        x = (1 - t) ** 2 * 0 + 2 * (1 - t) * t * mx + t * t * w
        y = (1 - t) ** 2 * 6 + 2 * (1 - t) * t * my + t * t * 6
        d += P.card(x, y + 20, 24, 30, P.PAPER[i % len(P.PAPER)], i % 4, rng.uniform(-7, 7))
    write_svg("pieces/cards_garland.svg", (0, 0, w, h), d)
    return P.piece("cards_garland", "source/pieces/cards_garland.svg", (290, 100), (w, h), "sway", "behind", "mix", pivot=(360, 0))


def piece_monitor():
    w, h = 64, 58
    d = ""
    defs = lin_grad("ms", [(0, "#16323a"), (1, "#0e2228")], 0, 0, 0, 1)
    d += rect(6, 4, 52, 42, "#fff6ea", OUT, 3, rx=6) + rect(11, 9, 42, 32, "url(#ms)", OUT, 1.6, rx=3)
    tr = "M13 27 L21 27 L24 19 L28 35 L32 23 L35 27 L51 27"
    d += path(tr, None, "#7dffc0", 6.5, sop=0.2) + path(tr, None, "#7dffc0", 2.6) + path(tr, None, "#eafff4", 1.0)
    d += P.heart_shape(45, 16, 3.6, "#ff8f9a", 0.8, "#ffd0d6")
    d += circle(14, 14, 1.6, "#ffe27a", None) + circle(20, 14, 1.6, "#7dffc0", None)
    d += rect(26, 46, 12, 5, "#a8b4c0", OUT, 1.6) + rect(16, 51, 32, 5, "#a8b4c0", OUT, 1.8, rx=2)
    write_svg("pieces/heart_monitor.svg", (0, 0, w, h), d, defs)
    return P.piece("heart_monitor", "source/pieces/heart_monitor.svg", (772, 144), (w, h), "pulse", "behind", "mix", pivot=(32, 27))


def piece_vase():
    w, h = 64, 92
    d = P.bouquet(32, 84, 0.9, 5)
    write_svg("pieces/flower_vase.svg", (0, 0, w, h), d)
    return P.piece("flower_vase", "source/pieces/flower_vase.svg", (418, 114), (w, h), "sway", "behind", "mix", pivot=(32, 86))


def piece_paper_stars():
    w, h = 700, 150
    d = ""
    stars = [(36, 66, 22, 0), (112, 108, 27, 1), (196, 52, 19, 2), (262, 92, 24, 3), (440, 84, 24, 4), (516, 46, 19, 5), (588, 112, 27, 6), (664, 70, 22, 0)]
    for x, y, r, k in stars:
        d += P.hang_string(x, 0, y - r * 0.6)
        d += P.star_paper(x, y, r, P.PAPER[k % len(P.PAPER)], 8)
    write_svg("pieces/paper_stars.svg", (0, 0, w, h), d)
    return P.piece("paper_stars", "source/pieces/paper_stars.svg", (300, 0), (w, h), "bob", "behind", "mix", pivot=(350, 0))


# ---- interlude: waking up -------------------------------------------------------------------------------------------------------------------------

def _feather(a, n):
    from PIL import ImageFilter
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(n))
    return np.asarray(im).astype(np.float64) / 255.0


def eyelid_png(name, top):
    """A closed eyelid half: a warm, soft shape that fills a screen half; the edge curves like a lid and carries lashes.
    Texture 640 x 260 shown at 2x (1280 x 520). Top lid: pivot at the bottom centre (the closing edge); bottom lid: pivot at the top centre.
    Deep plum at the outer edge warming to a rosy red near the edge (daylight shining through skin), a soft crease, a dark lash line;
    the upper lid carries long tapered lashes that curl out from the middle, the lower one short sparse ones."""
    w, h = 640, 260
    yy, xx = np.mgrid[0:h, 0:w]
    u = (xx - w / 2 + 0.5) / (w / 2)
    edge = 28 * (1 - u ** 2)  # how far the lid edge bulges towards the seam at the centre
    ysrc = yy if top else (h - 1 - yy)
    limit = (h - 40) + edge  # the lid body ends at this row (from its outer edge); beyond it is transparent
    body = _feather(np.clip((limit - ysrc) / 2.0, 0, 1), 1.0)
    t = np.clip(ysrc / limit, 0, 1)
    d = limit - ysrc  # rows above the edge
    r = 58 + 128 * t ** 1.8
    g = 20 + 50 * t ** 1.8
    b = 30 + 42 * t ** 1.8
    crease = np.exp(-((d - (34 if top else 22)) / 7.0) ** 2) * (1 - 0.6 * np.abs(u))  # the lid's fold: a soft shadow line
    lit = np.exp(-((d - 14) / 8.0) ** 2) * (1 - 0.5 * np.abs(u))  # the rim catching the light just above the edge
    rim = np.exp(-(np.maximum(d, 0) / 2.2) ** 2)  # the dark lash line on the edge itself
    r = r * (1 - 0.32 * crease) + 40 * lit
    g = g * (1 - 0.32 * crease) + 22 * lit
    b = b * (1 - 0.32 * crease) + 18 * lit
    r, g, b = (r * (1 - rim) + 52 * rim, g * (1 - rim) + 20 * rim, b * (1 - rim) + 30 * rim)
    arr = np.dstack([r, g, b, body * 255])
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    # lashes along the edge, tapered and curling away from the middle, supersampled on a 4x canvas
    S = 4
    big = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    bd = ImageDraw.Draw(big)
    rng = random.Random(77 if top else 78)
    n = 70 if top else 34
    for k in range(n):
        ux = math.sin((k + 0.5) / n * math.pi - math.pi / 2) * 0.97  # denser in the middle, sparser at the corners
        ux += rng.uniform(-0.006, 0.006)
        px = (ux * (w / 2) + w / 2) * S
        yedge = ((h - 40) + 28 * (1 - ux ** 2)) * S
        ln = (rng.uniform(15, 25) if top else rng.uniform(6, 10)) * (1 - abs(ux) * 0.5) * S
        side = 1 if ux >= 0 else -1
        curl = side * (0.25 + 0.9 * abs(ux)) * ln * 0.55
        y0 = yedge - 2 * S if top else (h * S - yedge + 2 * S)
        sgn = 1 if top else -1
        root_w = (1.9 if top else 1.3) * S
        m = 14
        left, right = [], []
        for j in range(m + 1):
            q = j / m
            x = px + curl * q * q
            y = y0 + sgn * ln * (q - 0.15 * q * q)
            dx, dy = 2 * curl * q, sgn * ln * (1 - 0.3 * q)
            nl = math.hypot(dx, dy) or 1.0
            wq = root_w * (1 - q) ** 0.8 + 0.25 * S
            left.append((x - dy / nl * wq, y + dx / nl * wq))
            right.append((x + dy / nl * wq, y - dx / nl * wq))
        bd.polygon(left + right[::-1], fill=(46, 18, 28, 255))
    big = big.resize((w, h), Image.LANCZOS)
    img = Image.alpha_composite(img, big)
    os.makedirs(lib.PNG_DIR, exist_ok=True)
    img.save(os.path.join(lib.PNG_DIR, name), compress_level=9)
    return f"processed/{name}", (w, h)


def _face(dr, cx, cy, r, skin, hair, kind, k=1.0):
    """One friendly face leaning in over the bed (Pillow, 2x canvas), in the chapter's outlined cartoon style: hair by `kind`, closed happy
    eyes, brows, a button nose, an open smile and rosy cheeks."""
    ink = (74, 34, 46, 255)
    ow = max(4, int(r * 0.045))

    def ell(x0, y0, x1, y1, fill):
        dr.ellipse((x0, y0, x1, y1), fill=fill, outline=ink, width=ow)

    if kind == "mum":  # long hair: a crown behind the head and two lengths falling past the shoulders
        for sx in (-1, 1):
            ell(cx + sx * r * 0.98 - r * 0.42, cy - r * 0.2, cx + sx * r * 0.98 + r * 0.42, cy + r * 1.75, hair)
        ell(cx - r * 1.2, cy - r * 1.22, cx + r * 1.2, cy + r * 0.85, hair)
    if kind == "granny":  # white curls round the head
        for a in range(0, 360, 30):
            ax, ay = cx + math.cos(math.radians(a)) * r * 0.98, cy - r * 0.15 + math.sin(math.radians(a)) * r * 0.92
            ell(ax - r * 0.36, ay - r * 0.36, ax + r * 0.36, ay + r * 0.36, hair)
    if kind == "kid":  # pigtails with ribbons
        for sx in (-1, 1):
            px = cx + sx * r * 1.08
            ell(px - r * 0.44, cy - r * 0.55, px + r * 0.44, cy + r * 0.35, hair)
            ell(px - sx * r * 0.32 - r * 0.14, cy - r * 0.52, px - sx * r * 0.32 + r * 0.14, cy - r * 0.24, (255, 210, 63, 255))
    if kind in ("dad", "kid"):  # ears
        for sx in (-1, 1):
            ell(cx + sx * r * 0.98 - r * 0.18, cy - r * 0.12, cx + sx * r * 0.98 + r * 0.18, cy + r * 0.3, skin)
    ell(cx - r, cy - r * 1.05, cx + r, cy + r, skin)
    if kind == "mum":  # side-swept fringe
        dr.chord((cx - r * 1.04, cy - r * 1.12, cx + r * 1.04, cy + r * 0.5), 180, 352, fill=hair, outline=ink, width=ow)
        dr.ellipse((cx - r * 0.9, cy - r * 0.52, cx - r * 0.05, cy - r * 0.02), fill=skin)
        ell(cx + r * 0.42, cy - r * 0.86, cx + r * 0.72, cy - r * 0.56, (255, 143, 154, 255))  # a flower clip
    elif kind == "dad":
        dr.chord((cx - r * 1.0, cy - r * 1.12, cx + r * 1.0, cy + r * 0.2), 182, 358, fill=hair, outline=ink, width=ow)
        dr.chord((cx - r * 0.97, cy - r * 0.25, cx + r * 0.97, cy + r * 1.03), 8, 172, fill=hair, outline=ink, width=ow)  # the beard
        dr.ellipse((cx - r * 0.5, cy + r * 0.12, cx + r * 0.5, cy + r * 0.6), fill=skin)
    elif kind == "kid":
        dr.chord((cx - r * 1.0, cy - r * 1.12, cx + r * 1.0, cy + r * 0.4), 180, 360, fill=hair, outline=ink, width=ow)
        dr.ellipse((cx - r * 0.72, cy - r * 0.6, cx + r * 0.72, cy - r * 0.08), fill=skin)
    ew = r * 0.21
    lw = max(4, int(r * 0.075))
    for sx in (-1, 1):  # closed, smiling eyes, raised brows, rosy cheeks
        ex, ey = cx + sx * r * 0.38, cy - r * 0.08
        dr.arc((ex - ew, ey - ew * 0.8, ex + ew, ey + ew * 0.9), 200, 340, fill=ink, width=lw)
        dr.arc((ex - ew * 1.1, ey - ew * 2.3, ex + ew * 1.1, ey - ew * 0.9), 210, 330, fill=ink if kind != "granny" else (190, 180, 170, 255), width=max(3, lw - 2))
        dr.ellipse((ex - ew * 1.0, ey + ew * 1.1, ex + ew * 1.0, ey + ew * 1.75), fill=(255, 120, 125, 120))
    if kind == "granny":
        for sx in (-1, 1):  # round glasses
            dr.ellipse((cx + sx * r * 0.38 - r * 0.3, cy - r * 0.36, cx + sx * r * 0.38 + r * 0.3, cy + r * 0.2), outline=(214, 168, 74, 255), width=max(3, int(r * 0.07)))
        dr.line((cx - r * 0.1, cy - r * 0.12, cx + r * 0.1, cy - r * 0.12), fill=(214, 168, 74, 255), width=max(3, int(r * 0.06)))
    dr.arc((cx - r * 0.12, cy + r * 0.02, cx + r * 0.12, cy + r * 0.2), 20, 160, fill=ink, width=max(3, lw - 2))  # nose
    dr.chord((cx - r * 0.34, cy + r * 0.22, cx + r * 0.34, cy + r * 0.68), 0, 180, fill=(120, 40, 56, 255), outline=ink, width=max(3, lw - 3))
    dr.chord((cx - r * 0.2, cy + r * 0.44, cx + r * 0.2, cy + r * 0.66), 0, 180, fill=(255, 128, 140, 255))


def waking_view_png():
    """What you see when your eyes first open: your family leaning in over the bed against the sunny window, warm and out of focus.
    Two 640 x 360 PNGs shown at 2x: `waking_view` (nearly in focus) and `waking_blur` (the first blurry moment); the cutscene
    cross-fades them to pull focus. Drawn on a 2x canvas and filtered down."""
    from PIL import ImageFilter
    W2, H2 = 1280, 720
    yy, xx = np.mgrid[0:H2, 0:W2]
    t = yy / H2
    bg = np.dstack([255 - 10 * t, 236 - 40 * t, 206 - 60 * t, np.full((H2, W2), 255.0)])
    win = np.exp(-(((xx - 1010) / 260.0) ** 2 + ((yy - 250) / 230.0) ** 2))  # the sunny window glowing on the right
    for c, v in enumerate((255, 250, 226)):
        bg[..., c] = bg[..., c] * (1 - win * 0.85) + v * win * 0.85
    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), "RGBA")
    dr = ImageDraw.Draw(img, "RGBA")
    for x in (900, 1120):  # window bars, soft
        dr.rectangle((x - 7, 40, x + 7, 470), fill=(255, 238, 205, 150))
    dr.rectangle((760, 250, 1280, 262), fill=(255, 238, 205, 150))
    rng = random.Random(9)
    cols = [(255, 214, 120), (255, 150, 140), (150, 230, 210), (255, 190, 200), (255, 236, 150)]
    for k in range(26):  # fairy-light bokeh across the top
        x = 40 + k * 48 + rng.uniform(-12, 12)
        y = 70 + 46 * math.sin(k * 0.45) + rng.uniform(-8, 8)
        r = rng.uniform(14, 24)
        c = cols[k % len(cols)]
        dr.ellipse((x - r, y - r, x + r, y + r), fill=c + (150,))
    # a red balloon floating over the kid, a teal one by granny
    dr.ellipse((300, 120, 420, 270), fill=(233, 69, 63, 255))
    dr.ellipse((322, 140, 350, 190), fill=(255, 190, 180, 200))
    dr.line((360, 270, 430, 520), fill=(255, 243, 224, 255), width=4)
    dr.ellipse((690, 70, 790, 195), fill=(79, 179, 169, 255))
    dr.line((740, 195, 760, 330), fill=(255, 243, 224, 255), width=4)
    # the family: granny further back on the right, dad on the right, mum on the left, the kid peeking up from the bottom
    _face(dr, 860, 300, 120, (251, 217, 192, 255), (246, 242, 236, 255), "granny")
    dr.ellipse((700, 400, 1030, 760), fill=(183, 155, 224, 255))  # granny's lilac cardigan
    dr.ellipse((960, 470, 1440, 900), fill=(200, 71, 63, 255))  # dad's red plaid shoulders
    for k in range(6):
        dr.line((1000 + k * 70, 470, 980 + k * 70, 900), fill=(47, 58, 99, 120), width=10)
    _face(dr, 1150, 390, 175, (230, 170, 122, 255), (90, 54, 34, 255), "dad")
    dr.ellipse((-160, 470, 420, 920), fill=(79, 179, 169, 255))  # mum's teal cardigan
    _face(dr, 170, 360, 185, (244, 195, 160, 255), (107, 58, 36, 255), "mum")
    dr.ellipse((380, 620, 760, 880), fill=(77, 120, 184, 255))  # the kid's dungarees
    _face(dr, 570, 610, 130, (182, 122, 82, 255), (42, 26, 30, 255), "kid")
    sharp = img.filter(ImageFilter.GaussianBlur(3)).resize((640, 360), Image.LANCZOS)
    blur = img.filter(ImageFilter.GaussianBlur(26)).resize((640, 360), Image.LANCZOS)
    sharp.save(os.path.join(lib.PNG_DIR, "waking_view.png"), compress_level=9)
    blur.save(os.path.join(lib.PNG_DIR, "waking_blur.png"), compress_level=9)
    return "processed/waking_view.png", "processed/waking_blur.png"


def build_interlude():
    sp = {}
    f_view, f_blur = waking_view_png()
    sp["waking_view"] = {"file": f_view, "pivot": [320, 180], "px_scale": 2.0,
                         "note": "what the opening eyes see: the family leaning in over the bed, warm and almost in focus (full screen, centre pivot)"}
    sp["waking_blur"] = {"file": f_blur, "pivot": [320, 180], "px_scale": 2.0, "note": "the same, completely out of focus (the first moment)"}
    f_top, (w, h) = eyelid_png("eyelid_top.png", True)
    sp["eyelid_top"] = {"file": f_top, "pivot": [w / 2, h], "px_scale": 2.0,
                        "note": "the upper lid, 1280 x 520 design px; pivot = bottom centre = the closing edge (put it at the eye line y 360 when shut, slide it up to open)"}
    f_bot, _ = eyelid_png("eyelid_bottom.png", False)
    sp["eyelid_bottom"] = {"file": f_bot, "pivot": [w / 2, 0], "px_scale": 2.0,
                           "note": "the lower lid, 1280 x 520 design px; pivot = top centre (the edge that meets the upper lid at y 360); slide it down to open"}
    # white wash: 320 x 180 shown at 1280 x 720, warm white, brightest at the middle
    ww, wh = 320, 180
    yy, xx = np.mgrid[0:wh, 0:ww]
    r = np.hypot((xx - ww / 2 + 0.5) / (ww / 2), (yy - wh / 2 + 0.5) / (wh / 2))
    a = 0.82 + 0.18 * _smooth(1 - r)
    col = np.dstack([np.full((wh, ww), 255.0), 247 - 12 * _smooth(r / 1.3), 232 - 40 * _smooth(r / 1.3)])
    sp["white_wash"] = {"file": _save_rgba("white_wash.png", np.dstack([col, a * 255])), "pivot": [ww / 2, wh / 2], "px_scale": 4.0}
    # heartbeat trace: 1024 x 128, a glowing ECG line (blend add), pivot at the left centre of the baseline
    lw, lh = 1024, 128
    big = Image.new("RGBA", (lw * 2, lh * 2), (0, 0, 0, 0))
    pts = [(0, 64)]
    xs = 0
    while xs < lw:
        base = xs
        pts += [(base + 70, 64), (base + 86, 52), (base + 100, 64), (base + 124, 64), (base + 134, 72), (base + 148, 10), (base + 164, 112), (base + 176, 64),
                (base + 206, 64), (base + 232, 46), (base + 258, 64), (base + 330, 64)]
        xs += 330
    pts = [(min(x, lw), y) for x, y in pts if x <= lw + 330]
    pts2 = [(x * 2, y * 2) for x, y in pts]
    for width, alpha in ((22, 40), (12, 90), (6, 255)):
        glow = Image.new("RGBA", big.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.line(pts2, fill=(190, 255, 225, alpha), width=width, joint="curve")
        big = Image.alpha_composite(big, glow)
    core = Image.new("RGBA", big.size, (0, 0, 0, 0))
    ImageDraw.Draw(core).line(pts2, fill=(255, 255, 250, 255), width=3, joint="curve")
    big = Image.alpha_composite(big, core)
    img = big.resize((lw, lh), Image.LANCZOS)
    img.save(os.path.join(lib.PNG_DIR, "monitor_line.png"), compress_level=9)
    sp["monitor_line"] = {"file": "processed/monitor_line.png", "pivot": [0, 64], "px_scale": 1.0, "blend": "add",
                          "note": "a 1024 px heartbeat trace repeating every 330 px; scroll or reveal it left to right; tint it green-white"}
    anchors = {"eyelid_seam": [640, 360], "monitor_line": [128, 360], "monitor_line_width": 1024}
    return {"sprites": sp, "anchors": anchors}


# ---- the stage manifest -----------------------------------------------------------------------------------------------------------------------------

def build_stage():
    build_desk_top()
    sp: dict = {}
    spr_deck(sp)
    sp["door_open"] = spr_door_open()
    spr_woofer(sp)
    spr_fixture(sp)
    spr_disco_ball(sp)
    spr_glowstick(sp)
    sp.update(build_png_sprites())
    layers = []
    build_backdrop()
    layers.append(P.room_layer("backdrop", "backdrop.svg"))
    build_riser()
    layers.append({"id": "riser", "file": "source/riser.svg", "pos": [520, 252], "size": [240, 34], "px_scale": 0.5})
    for side in (-1, 1):
        build_speaker(side)
        sid = "speaker_l" if side < 0 else "speaker_r"
        px, py = SPK_POS[sid]
        layers.append({"id": sid, "file": f"source/{sid}.svg", "pos": [px - 6, py - 16], "size": [SPK_W + 12, SPK_H + 16], "px_scale": 0.5})
    layers.append({"id": "desk_top", "file": "source/desk_top.svg", "pos": [0, 460], "size": [1280, 260], "px_scale": 0.5,
                   "note": "authored 1280 x 260; stretch to the pad-strip rectangle"})
    woofers = []
    for sid in ("speaker_l", "speaker_r"):
        px, py = SPK_POS[sid]
        for (wx, wy, wr) in SPK_WOOFERS:
            woofers.append([px + wx, py + wy, wr])
    pieces = [piece_sunbeams(), piece_fairy_lights(), piece_balloons(), piece_cards(), piece_monitor(), piece_vase(), piece_paper_stars()]
    anchors = {
        "led_screen": [400, 56, 480, 44],
        "doorway": [284, 138, 70, 124],
        "floor_rows": FLOOR_ROWS,
        "floor_polygon": [[400, 266], [880, 266], [round(floor_x(880, 520)), 520], [round(floor_x(400, 520)), 520]],
        "floor_grid": ROOM.grid(),
        "light_points": [[150, 30], [330, 30], [510, 30], [770, 30], [950, 30], [1130, 30], [450, 58], [830, 58]],
        "woofers": woofers,
        "disco_ball": [640, 0],
        "riser": [640, 286, 240],
        "circle_centre": [640, 372],
        "circle_radii": [250, 46],
        "wall_left_x": FX0, "wall_right_x": FX1, "horizon_y": VPY,
        "bed": [640, 296, 310], "window": [1138, 72, 126, 144], "vanish": [640, 130],
    }
    stage = {"design_size": [W, H], "layers": layers, "anchors": anchors, "sprites": sp, "pieces": pieces,
             "pieces_note": "pos/size = top-left rectangle in design px; pivot (rotate/sway/flicker/bob/pulse) is in design px relative to pos; blend add = draw additively"}
    from . import hp_views  # corridor, cafeteria, garden + passage_frame
    views, passage = hp_views.build_views()
    sp["passage_frame"] = passage
    stage["views"] = views
    return stage
