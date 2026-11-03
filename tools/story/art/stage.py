"""The Night One room: fixed DJ point of view over the mixing desk. One-point perspective, vanishing point (640, 130).

Design space is 1280 x 720. Far wall x 270..1010, y 52..262; side walls and the floor recede to the camera; the crowd stands on the
floor rows listed in the manifest. Everything here is plain SVG (gradients, translucent layered shapes for glow) plus a few
Pillow PNGs (beams, haze, glows) in sprites.py.
"""
from __future__ import annotations

import math
import random

from .lib import (OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, pivot_in, poly, rad_grad, rect,
                  write_svg)

VPX, VPY = 640.0, 130.0
FX0, FX1, FY0, FY1 = 270.0, 1010.0, 52.0, 262.0  # far wall rectangle
W, H = 1280, 720

MAGENTA, CYAN, VIOLET, AMBER = "#ff2f9d", "#19d2ff", "#7a4cff", "#ffc23f"

FLOOR_ROWS = [  # crowd feet rows, back to front: scale = (y - horizon) / (front y - horizon)
    {"y": 286, "scale": round((286 - VPY) / (438 - VPY), 3)},
    {"y": 316, "scale": round((316 - VPY) / (438 - VPY), 3)},
    {"y": 350, "scale": round((350 - VPY) / (438 - VPY), 3)},
    {"y": 390, "scale": round((390 - VPY) / (438 - VPY), 3)},
    {"y": 438, "scale": 1.0},
]


def floor_x(x_far: float, y: float) -> float:
    """x of a floor line that is at x_far on the far wall base, at screen row y."""
    return VPX + (x_far - VPX) * (y - VPY) / (FY1 - VPY)


def lwall_y(y_far: float, x: float) -> float:
    return VPY + (y_far - VPY) * (VPX - x) / (VPX - FX0)


def rwall_y(y_far: float, x: float) -> float:
    return VPY + (y_far - VPY) * (x - VPX) / (FX1 - VPX)


def neon(p1, p2, color, w=2.0, glow=1.0) -> str:
    """A neon tube: wide faint halos (no blur filters in ThorVG) then a bright core."""
    out = ""
    for k, (mul, op) in enumerate(((7.0, 0.05), (4.4, 0.09), (2.6, 0.16))):
        out += line(p1, p2, color, w * mul, op * glow)
    out += line(p1, p2, color, w, 1.0)
    out += line(p1, p2, lighten(color, 0.65), w * 0.38, 0.9)
    return out


def neon_path(d: str, color: str, w=2.0, glow=1.0) -> str:
    out = ""
    for mul, op in ((7.0, 0.05), (4.4, 0.09), (2.6, 0.16)):
        out += path(d, None, color, w * mul, sop=op * glow)
    out += path(d, None, color, w)
    out += path(d, None, lighten(color, 0.65), w * 0.38, sop=0.9)
    return out


# ---- backdrop ---------------------------------------------------------------------------------------------------------------

def truss(x0, x1, y, h=14, color="#5f4aa8") -> str:
    out = line((x0, y), (x1, y), OUT, 7)
    out += line((x0, y + h), (x1, y + h), OUT, 7)
    n = int((x1 - x0) / (h * 1.1))
    step = (x1 - x0) / n
    for i in range(n):
        xa = x0 + i * step
        xb = xa + step
        if i % 2 == 0:
            out += line((xa, y), (xb, y + h), OUT, 4.5)
        else:
            out += line((xa, y + h), (xb, y), OUT, 4.5)
    out += line((x0, y), (x1, y), color, 3.2)
    out += line((x0, y + h), (x1, y + h), mix(color, "#150a33", 0.35), 3.2)
    for i in range(n):
        xa = x0 + i * step
        xb = xa + step
        if i % 2 == 0:
            out += line((xa, y), (xb, y + h), color, 2.0, 0.9)
        else:
            out += line((xa, y + h), (xb, y), color, 2.0, 0.9)
    out += line((x0, y - 1.6), (x1, y - 1.6), CYAN, 1.2, 0.55)  # rim light
    for xx in (x0, x1):
        out += rect(xx - 3, y - 3, 6, h + 6, "#3a2c72", OUT, 2)
    return out


def build_backdrop() -> dict:
    rng = random.Random(11)
    d = ""
    defs = ""
    # base fill
    defs += lin_grad("bg", [(0, "#07041a"), (0.4, "#120a30"), (1, "#0b0624")], 0, 0, 0, 1)
    d += rect(0, 0, W, H, "url(#bg)")
    # ceiling and ceiling lines
    defs += lin_grad("ceil", [(0, "#05031a"), (1, "#1a1048")], 0, 0, 0, 1)
    d += poly([(0, -6), (W, -6), (FX1, FY0), (FX0, FY0)], "url(#ceil)")
    for k in range(-6, 7):
        xf = VPX + k * 63.0
        xa = VPX + (xf - VPX) * (FY0 - VPY) / (FY0 - VPY) if False else xf
        # ceiling seams: from the far wall top edge towards the camera along the vanishing point
        if FX0 <= xf <= FX1:
            yt = -6
            xt = VPX + (xf - VPX) * (yt - VPY) / (FY0 - VPY)
            d += line((xf, FY0), (xt, yt), "#2a1d66", 1.6, 0.55)
    for yy in (24, 38):  # ceiling cross seams
        xl = VPX - (VPX - FX0) * (VPY - yy) / (VPY - FY0)
        xr = VPX + (FX1 - VPX) * (VPY - yy) / (VPY - FY0)
        d += line((xl, yy), (xr, yy), "#2a1d66", 1.6, 0.55)
    # far wall
    defs += lin_grad("fw", [(0, "#241766"), (0.55, "#150d44"), (1, "#0c0730")], 0, 0, 0, 1)
    d += rect(FX0, FY0, FX1 - FX0, FY1 - FY0, "url(#fw)")
    for x in range(int(FX0) + 8, int(FX1), 16):  # acoustic slats
        d += rect(x, FY0, 8, FY1 - FY0, "#07041a", None, op=0.22)
        d += rect(x + 8, FY0, 1.4, FY1 - FY0, VIOLET, None, op=0.12)
    # side walls
    defs += lin_grad("lw", [(0, "#07041a"), (1, "#1b1150")], 0, 0, 1, 0)
    defs += lin_grad("rw", [(0, "#1b1150"), (1, "#07041a")], 0, 0, 1, 0)
    lwall = [(0, lwall_y(FY0, 0)), (FX0, FY0), (FX0, FY1), (0, lwall_y(FY1, 0))]
    rwall = [(W, rwall_y(FY0, W)), (FX1, FY0), (FX1, FY1), (W, rwall_y(FY1, W))]
    d += poly(lwall, "url(#lw)") + poly(rwall, "url(#rw)")
    # wall panel seams (vertical) and perspective neon runs
    for k in range(1, 6):
        x = FX0 * k / 6.0
        d += line((x, lwall_y(FY0, x)), (x, lwall_y(FY1, x)), "#07041a", 3, 0.5)
        d += line((x + 2, lwall_y(FY0, x)), (x + 2, lwall_y(FY1, x)), VIOLET, 1.2, 0.18)
        xr = W - x
        d += line((xr, rwall_y(FY0, xr)), (xr, rwall_y(FY1, xr)), "#07041a", 3, 0.5)
        d += line((xr - 2, rwall_y(FY0, xr)), (xr - 2, rwall_y(FY1, xr)), VIOLET, 1.2, 0.18)
    d += neon((0, lwall_y(78, 0)), (FX0, 78), MAGENTA, 2.4, 0.9)
    d += neon((W, rwall_y(78, W)), (FX1, 78), CYAN, 2.4, 0.9)
    d += neon((0, lwall_y(236, 0)), (FX0, 236), CYAN, 2.0, 0.9)
    d += neon((W, rwall_y(236, W)), (FX1, 236), MAGENTA, 2.0, 0.9)
    # posters on the side walls: neon pictograms in dark frames, skewed with the wall
    def wall_quad(side, xa, xb, ya, yb):
        if side < 0:
            return [(xa, lwall_y(ya, xa)), (xb, lwall_y(ya, xb)), (xb, lwall_y(yb, xb)), (xa, lwall_y(yb, xa))]
        return [(xa, rwall_y(ya, xa)), (xb, rwall_y(ya, xb)), (xb, rwall_y(yb, xb)), (xa, rwall_y(yb, xa))]
    for side in (-1, 1):
        for xa, xb, ya, yb, col in ((26, 100, 110, 188, MAGENTA), (118, 214, 118, 196, CYAN)):
            xa2, xb2 = (xa, xb) if side < 0 else (W - xb, W - xa)
            q = wall_quad(side, xa2, xb2, ya, yb)
            d += poly(q, "#0a0626", OUT, 2.4) + poly(q, col, None, op=0.1)
            cxp = (xa2 + xb2) / 2
            cyp = (q[0][1] + q[3][1] + q[1][1] + q[2][1]) / 4
            sc = (xb2 - xa2) / 74.0
            if col == MAGENTA:  # equaliser bars
                for k, bh in enumerate((16, 30, 22, 38, 26)):
                    bxp = cxp + (k - 2) * 9 * sc
                    d += line((bxp, cyp + 20 * sc), (bxp, cyp + 20 * sc - bh * sc), lighten(col, 0.3), 3.4 * sc, 0.95)
            else:  # a record and a sound wave
                d += circle(cxp, cyp - 6 * sc, 17 * sc, None, lighten(col, 0.3), 1.8, sop=0.9) + circle(cxp, cyp - 6 * sc, 6 * sc, lighten(col, 0.3), None, op=0.8)
                d += neon_path(f"M{f(cxp - 24 * sc)} {f(cyp + 20 * sc)} Q{f(cxp - 12 * sc)} {f(cyp + 8 * sc)} {f(cxp)} {f(cyp + 20 * sc)} T{f(cxp + 24 * sc)} {f(cyp + 20 * sc)}", col, 1.2, 0.7)
    # far wall: lower wainscot, neon strips
    d += rect(FX0, 222, FX1 - FX0, FY1 - 222, "#07041a", None, op=0.45)
    d += neon((FX0, 78), (FX1, 78), MAGENTA, 2.2, 1.0)
    d += neon((FX0, 222), (FX1, 222), CYAN, 1.8, 1.0)
    d += neon((FX0, FY1 - 1), (FX1, FY1 - 1), VIOLET, 2.0, 1.0)
    # corner light tubes
    d += neon((FX0 + 1, FY0 + 6), (FX0 + 1, FY1 - 4), MAGENTA, 2.0, 0.9)
    d += neon((FX1 - 1, FY0 + 6), (FX1 - 1, FY1 - 4), CYAN, 2.0, 0.9)
    # LED screen frame (the runtime paints the panel)
    lx, ly, lw_, lh = 450, 104, 380, 104
    d += rect(lx - 12, ly - 12, lw_ + 24, lh + 24, "#241a58", OUT, 3.5, rx=8)
    d += rect(lx - 7, ly - 7, lw_ + 14, lh + 14, "#0a0626", OUT, 2, rx=5)
    d += rect(lx, ly, lw_, lh, "#05031a", None)
    d += neon((lx - 12, ly - 12), (lx + lw_ + 12, ly - 12), CYAN, 1.2, 0.9)
    d += neon((lx - 12, ly + lh + 12), (lx + lw_ + 12, ly + lh + 12), MAGENTA, 1.2, 0.9)
    for cx_, cy_ in ((lx - 6, ly - 6), (lx + lw_ + 6, ly - 6), (lx - 6, ly + lh + 6), (lx + lw_ + 6, ly + lh + 6)):
        d += circle(cx_, cy_, 2.4, "#8c78d8", OUT, 1.2)
    # entrance doors, closed (a double door with a neon frame and a transom light)
    dx, dy, dw, dh = 284, 138, 70, 124
    d += rect(dx - 7, dy - 7, dw + 14, dh + 7, "#3a2a82", OUT, 3, rx=4)
    d += rect(dx, dy, dw, dh, "#0a0626", None)
    defs += lin_grad("dl", [(0, "#3b2c80"), (1, "#1c1250")], 0, 0, 0, 1)
    d += rect(dx + 2, dy + 2, dw / 2 - 3, dh - 2, "url(#dl)", OUT, 2) + rect(dx + dw / 2 + 1, dy + 2, dw / 2 - 3, dh - 2, "url(#dl)", OUT, 2)
    for xx in (dx + 8, dx + dw / 2 + 7):
        d += rect(xx, dy + 12, dw / 2 - 20, 26, "#07041a", None, op=0.55)
    d += circle(dx + dw / 2 - 5, dy + dh * 0.58, 2.2, AMBER, OUT, 1) + circle(dx + dw / 2 + 5, dy + dh * 0.58, 2.2, AMBER, OUT, 1)
    d += neon((dx - 7, dy - 7), (dx + dw + 7, dy - 7), MAGENTA, 1.6, 1.0) + neon((dx - 7, dy - 7), (dx - 7, dy + dh), MAGENTA, 1.6, 0.8)
    d += neon((dx + dw + 7, dy - 7), (dx + dw + 7, dy + dh), MAGENTA, 1.6, 0.8)
    d += rect(dx + 14, dy - 22, dw - 28, 11, "#0a0626", OUT, 2, rx=2) + rect(dx + 18, dy - 19, dw - 36, 5, AMBER, None, op=0.9)  # transom light
    # bar on the far wall's right: back shelves with bottles, counter with under-glow, stools
    bx0, bx1 = 858, 1000
    d += rect(bx0, 114, bx1 - bx0, 100, "#07041a", OUT, 2.4, rx=2)
    defs += lin_grad("shelfglow", [(0, MAGENTA, 0.34), (1, VIOLET, 0.08)], 0, 0, 0, 1)
    d += rect(bx0 + 2, 116, bx1 - bx0 - 4, 96, "url(#shelfglow)")
    cols = [MAGENTA, CYAN, AMBER, VIOLET, "#4ff0a8", "#ff7a59"]
    for row, sy in enumerate((148, 190)):
        d += rect(bx0 - 3, sy, bx1 - bx0 + 6, 5, "#3a2a82", OUT, 1.8)
        x = bx0 + 6
        while x < bx1 - 10:
            c = cols[rng.randrange(len(cols))]
            bh = rng.choice((16, 20, 24, 18))
            bw = rng.choice((6, 7, 8))
            d += rect(x, sy - bh, bw, bh, c, OUT, 1.4, rx=2, op=0.92)
            d += rect(x + bw * 0.25, sy - bh - 5, bw * 0.5, 5, c, OUT, 1.2, op=0.9)
            d += line((x + 1.8, sy - bh + 3), (x + 1.8, sy - 4), "#ffffff", 1.2, 0.45)
            x += bw + rng.choice((3, 5, 7))
    d += rect(bx0 - 6, 204, bx1 - bx0 + 12, 58, "#17103f", OUT, 3)
    d += rect(bx0 - 6, 204, bx1 - bx0 + 12, 7, "#3a2a82", OUT, 2.4)
    d += rect(bx0 + 6, 220, bx1 - bx0 - 12, 34, "#07041a", None, op=0.55)
    d += neon((bx0, 258), (bx1, 258), MAGENTA, 1.6, 0.9)
    for sx in (878, 930, 982):
        d += ellipse(sx, 270, 13, 4.2, "#241a58", OUT, 2) + rect(sx - 2, 270, 4, 16, "#3a2a82", OUT, 1.4)
        d += ellipse(sx, 267, 11, 3.4, mix(MAGENTA, "#150a33", 0.35), OUT, 1.4)
    # floor
    defs += lin_grad("fl", [(0, "#241766"), (0.3, "#150e44"), (1, "#080520")], 0, 0, 0, 1)
    floor_poly = [(0, lwall_y(FY1, 0)), (FX0, FY1), (FX1, FY1), (W, rwall_y(FY1, W)), (W, H), (0, H)]
    d += poly(floor_poly, "url(#fl)")
    defs += clip("floorclip", poly(floor_poly))
    grid = ""
    ys = []
    z = 1.0
    while True:
        y = VPY + (FY1 - VPY) / z
        if y > H + 40:
            break
        ys.append(y)
        z -= 0.065
    for i, y in enumerate(ys):
        grid += line((-80, y), (W + 80, y), "#6a4cff", 1.0 + i * 0.16, 0.22 + min(i, 8) * 0.012)
    for k in range(-16, 17):
        xf = VPX + k * 61.7
        grid += line((xf, FY1), (floor_x(xf, H + 40), H + 40), "#6a4cff", 1.4, 0.22)
    d += group(grid, 'clip-path="url(#floorclip)"')
    # the lit dance floor: coloured LED tiles inside a perspective trapezoid
    cols_far = [400 + 60 * i for i in range(9)]  # x on the far wall base
    y_lines = [y for y in ys if 264 <= y <= 530]
    palette = [(MAGENTA, 0.30), (CYAN, 0.26), (VIOLET, 0.34), ("#3a2c9a", 0.5), (MAGENTA, 0.16), (CYAN, 0.14), (AMBER, 0.16), ("#4a34c0", 0.4)]
    tiles = ""
    for j in range(len(y_lines) - 1):
        ya, yb = y_lines[j], y_lines[j + 1]
        for i in range(len(cols_far) - 1):
            c, a = palette[rng.randrange(len(palette))]
            q = [(floor_x(cols_far[i], ya), ya), (floor_x(cols_far[i + 1], ya), ya), (floor_x(cols_far[i + 1], yb), yb), (floor_x(cols_far[i], yb), yb)]
            tiles += poly(q, c, None, op=a)
            tiles += poly(q, None, lighten(c, 0.5), 1.1, sop=0.5)
    d += tiles
    d += neon((floor_x(400, 264), 264), (floor_x(880, 264), 264), CYAN, 1.4, 0.8)
    # soft floor sheen under the wall neon and the LED screen
    defs += lin_grad("sheen", [(0, MAGENTA, 0.22), (1, MAGENTA, 0.0)], 0, 0, 0, 1)
    d += poly([(FX0, FY1), (FX1, FY1), (FX1 + 40, FY1 + 36), (FX0 - 40, FY1 + 36)], "url(#sheen)")
    # ceiling trusses (static housings; the moving heads are separate sprites hung from the light points)
    d += truss(60, 1220, 24, 14)
    d += truss(330, 950, 54, 10)
    for xx in (60, 330, 640, 950, 1220):
        d += line((xx, -6), (xx, 24), OUT, 4) + line((xx, -6), (xx, 24), "#5f4aa8", 1.8)
    d += neon((60, 38), (1220, 38), VIOLET, 1.2, 0.6)
    return write_svg("backdrop.svg", (0, 0, W, H), d, defs)


# ---- speaker stacks, riser, desk ---------------------------------------------------------------------------------------------

SPK_W, SPK_H = 112, 170
SPK_POS = {"speaker_l": (146, 108), "speaker_r": (1022, 108)}
SPK_WOOFERS = [(56, 50, 23), (56, 120, 34)]  # (x, y, r) inside the cabinet; the runtime draws the woofer sprites on top


def build_speaker(side: int) -> dict:
    d = ""
    defs = lin_grad("cab", [(0, "#2a1f66"), (1, "#120b34")], 0, 0, 0, 1)
    defs += lin_grad("cabside", [(0, "#ffffff", 0.0), (1, "#ffffff", 0.14)], 0, 0, 1, 0)
    d += rect(4, 6, SPK_W - 8, SPK_H - 12, "url(#cab)", OUT, 4, rx=8)
    d += rect(4, 6, SPK_W - 8, SPK_H - 12, "url(#cabside)", None, rx=8)
    for yy in (6, SPK_H - 6):
        d += rect(4, yy - 5 if yy < 20 else yy - 6, SPK_W - 8, 11, "#3b2d80", OUT, 3, rx=4)
    for xx in (8, SPK_W - 8):  # corner guards
        for yy in (12, SPK_H - 12):
            d += circle(xx, yy, 5, "#5a49b0", OUT, 2) + line((xx - 2, yy - 2), (xx + 2, yy + 2), OUT, 1.2)
    for (x, y, r) in SPK_WOOFERS:
        d += circle(x, y, r + 5, "#0a0626", OUT, 3)
        d += circle(x, y, r + 2, "#05031a", None)
    d += rect(28, 14, 56, 7, "#0a0626", OUT, 2, rx=2) + rect(31, 16, 22, 3, MAGENTA, None, op=0.95)  # a logo plate, abstract
    d += rect(28, 158, 56, 7, "#0a0626", OUT, 2, rx=2) + rect(58, 160, 22, 3, CYAN, None, op=0.95)
    d += rect(20, 164, 14, 5, "#07041a", OUT, 2) + rect(78, 164, 14, 5, "#07041a", OUT, 2)  # feet
    d += line((6, 50), (6, 130), CYAN if side < 0 else MAGENTA, 2.0, 0.7)  # rim light on the stack
    return write_svg("speaker_%s.svg" % ("l" if side < 0 else "r"), (0, 0, SPK_W, SPK_H), d, defs)


def build_riser() -> dict:
    w, h = 240, 34
    d = ""
    defs = lin_grad("rt", [(0, "#4a3a9a"), (1, "#2a1f66")], 0, 0, 0, 1)
    defs += lin_grad("rf", [(0, "#1c1352"), (1, "#0b0726")], 0, 0, 0, 1)
    d += poly([(22, 3), (w - 22, 3), (w - 2, 16), (2, 16)], "url(#rt)", OUT, 3)
    d += poly([(2, 16), (w - 2, 16), (w - 2, h - 3), (2, h - 3)], "url(#rf)", OUT, 3)
    for k in range(1, 6):
        d += line((2 + k * (w - 4) / 6, 17), (2 + k * (w - 4) / 6, h - 5), "#07041a", 2, 0.5)
    d += neon((6, 17), (w - 6, 17), MAGENTA, 1.5, 1.0)
    d += neon((6, h - 6), (w - 6, h - 6), CYAN, 1.2, 0.8)
    d += line((24, 6), (w - 24, 6), "#8c78d8", 1.4, 0.5)
    return write_svg("riser.svg", (0, 0, w, h), d, defs)


def build_desk_top() -> dict:
    w, h = 1280, 260
    d = ""
    defs = lin_grad("dk", [(0, "#2b2068"), (0.06, "#1a1250"), (1, "#0a0624")], 0, 0, 0, 1)
    defs += lin_grad("lip", [(0, "#8d7be0"), (0.5, "#4a3a9a"), (1, "#241a58")], 0, 0, 0, 1)
    d += rect(0, 0, w, h, "url(#dk)")
    d += rect(0, 0, w, 16, "url(#lip)")
    d += line((0, 16), (w, 16), OUT, 3.5)
    d += line((0, 2.5), (w, 2.5), "#d9ccff", 1.6, 0.7)
    # brushed panel lines
    for y in range(26, h, 9):
        d += line((0, y), (w, y), "#6a4cff", 1.0, 0.05)
    # side wings (pad areas) and the centre mixer inset
    for x0, x1 in ((10, 424), (856, 1270)):
        d += rect(x0, 26, x1 - x0, h - 36, "#0b0728", OUT, 2.6, rx=14, op=0.55)
        d += rect(x0 + 5, 31, x1 - x0 - 10, h - 46, None, "#6a4cff", 1.2, rx=11, sop=0.35)
        for sx, sy in ((x0 + 12, 38), (x1 - 12, 38), (x0 + 12, h - 22), (x1 - 12, h - 22)):
            d += circle(sx, sy, 4, "#6a5cc0", OUT, 1.6) + line((sx - 2.2, sy - 2.2), (sx + 2.2, sy + 2.2), OUT, 1.1)
        for k in range(5):  # vent slots
            d += rect(x0 + 30 + k * 12, h - 24, 7, 3, "#05031a", None, op=0.9)
    mx0, mx1 = 436, 844
    d += rect(mx0, 26, mx1 - mx0, h - 36, "#100a30", OUT, 3, rx=12)
    d += rect(mx0 + 5, 31, mx1 - mx0 - 10, h - 46, None, MAGENTA, 1.4, rx=9, sop=0.45)
    for k in range(0, 17):  # ruler ticks along the top and bottom of the mixer
        x = mx0 + 24 + k * ((mx1 - mx0 - 48) / 16.0)
        d += line((x, 36), (x, 36 + (9 if k % 4 == 0 else 5)), "#8c78d8", 1.4, 0.55)
        d += line((x, h - 30), (x, h - 30 - (9 if k % 4 == 0 else 5)), "#8c78d8", 1.4, 0.55)
    d += rect(mx0 + 60, h - 62, mx1 - mx0 - 120, 10, "#05031a", OUT, 2, rx=5)  # crossfader groove
    d += rect(mx0 + 66, h - 59, mx1 - mx0 - 132, 3, "#6a4cff", None, op=0.35)
    for x in (mx0 + 40, mx1 - 56):  # EQ channel strips
        d += rect(x, 60, 16, 80, "#05031a", OUT, 2, rx=3)
        for k in range(8):
            d += rect(x + 3, 64 + k * 9.4, 10, 5, [CYAN, CYAN, CYAN, "#4ff0a8", "#4ff0a8", AMBER, AMBER, MAGENTA][k], None, op=0.28)
    return write_svg("desk_top.svg", (0, 0, w, h), d, defs)


# ---- sprites ---------------------------------------------------------------------------------------------------------------

def spr_woofer(sprites: dict) -> None:
    r = 50
    d = ""
    defs = rad_grad("cone", [(0, "#4a3a9a"), (0.45, "#2a1f66"), (1, "#120b34")], 0.42, 0.38, 0.75)
    defs += lin_grad("rim", [(0, "#8d7be0"), (1, "#241a58")], 0, 0, 1, 1)
    d += circle(0, 0, r, "url(#rim)", OUT, 3.5)
    d += circle(0, 0, r - 5, "#0a0626", None)
    d += circle(0, 0, r - 9, "url(#cone)", OUT, 2.2)
    for k, rr in enumerate((36, 30, 24, 18)):
        d += circle(0, 0, rr, None, "#05031a" if k % 2 == 0 else "#6a4cff", 1.4, sop=0.6)
    d += circle(0, 0, 12, "#241a58", OUT, 2.4)
    d += circle(-3, -3, 4, "#d9ccff", None, op=0.55)
    d += path("M-32 -20 A38 38 0 0 1 -8 -36", None, "#ffffff", 3, sop=0.4)
    info = write_svg("props/woofer.svg", (-r - 3, -r - 3, r + 3, r + 3), d, defs)
    sprites["woofer"] = {"file": "source/props/woofer.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "radius": r}


def spr_fixture(sprites: dict) -> None:
    d = ""
    defs = lin_grad("body", [(0, "#4a3a9a"), (1, "#1a1250")], 0, 0, 1, 0)
    d += rect(-11, 0, 22, 6, "#5a49b0", OUT, 2.4, rx=2)
    d += path("M-15 8 L-15 30 M15 8 L15 30", None, OUT, 8) + path("M-15 8 L-15 30 M15 8 L15 30", None, "#3b2d80", 4.4)
    d += rect(-8, 6, 16, 8, "#2a1f66", OUT, 2.2, rx=2)
    d += rect(-12, 16, 24, 34, "url(#body)", OUT, 3, rx=5)
    d += line((-8, 20), (-8, 46), "#d9ccff", 1.4, 0.45)
    for yy in (24, 30, 36):
        d += line((-10, yy), (10, yy), "#07041a", 1.2, 0.5)
    d += ellipse(0, 51, 11, 4.5, "#0a0626", OUT, 2.4)
    d += ellipse(0, 51, 8, 3, "#e6fbff", None) + ellipse(0, 51, 4.5, 1.8, "#ffffff", None)
    d += circle(-15, 30, 3, "#6a5cc0", OUT, 1.4) + circle(15, 30, 3, "#6a5cc0", OUT, 1.4)
    info = write_svg("props/fixture.svg", (-20, -2, 20, 60), d, defs)
    sprites["fixture"] = {"file": "source/props/fixture.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "lens": [0, 51]}


def spr_disco_ball(sprites: dict) -> None:
    d = ""
    defs = rad_grad("ball", [(0, "#e8e0ff"), (0.45, "#8f82e0"), (1, "#2a2070")], 0.38, 0.34, 0.78)
    cy, r = 66, 28
    d += line((0, 0), (0, cy - r + 2), OUT, 4.2) + line((0, 0), (0, cy - r + 2), "#8c78d8", 1.6)
    d += rect(-5, 0, 10, 6, "#5a49b0", OUT, 2, rx=2)
    d += circle(0, cy, r, "url(#ball)", OUT, 3.4)
    defs += clip("bc", f'<circle cx="0" cy="{cy}" r="{r}"/>')
    inner = ""
    for k in range(-3, 4):  # facet lattice
        yy = cy + k * 7.5
        inner += path(f"M{-r} {f(yy)} Q0 {f(yy + k * 2.6)} {r} {f(yy)}", None, "#150a33", 1.0, sop=0.55)
    for k in range(-4, 5):
        xx = k * 7.0
        inner += path(f"M{f(xx * 0.45)} {cy - r} Q{f(xx * 1.5)} {cy} {f(xx * 0.45)} {cy + r}", None, "#150a33", 1.0, sop=0.55)
    rng = random.Random(5)
    for _ in range(26):
        a = rng.random() * math.tau
        rr = rng.random() * (r - 5)
        x, yv = math.cos(a) * rr, cy + math.sin(a) * rr
        inner += rect(x - 2.4, yv - 2.4, 4.8, 4.8, rng.choice([MAGENTA, CYAN, "#ffffff", AMBER, "#ffffff"]), None, op=0.9)
    inner += circle(r * 0.5, cy + r * 0.45, r * 0.9, "#150a33", None, op=0.28)
    d += group(inner, 'clip-path="url(#bc)"')
    d += circle(-9, cy - 10, 4.4, "#ffffff", None, op=0.85)
    d += circle(0, cy, r, None, OUT, 3.4)
    info = write_svg("props/disco_ball.svg", (-r - 4, -2, r + 4, cy + r + 4), d, defs)
    sprites["disco_ball"] = {"file": "source/props/disco_ball.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "radius": r,
                             "ball_centre": [0, cy]}


def spr_glowstick(sprites: dict) -> None:
    d = ""
    d += rect(-4.5, 0, 9, 42, "#ffffff", OUT, 2.6, rx=4.5, op=0.0)
    d += line((0, 4), (0, 38), OUT, 10, cap="round")
    d += line((0, 4), (0, 38), "#ffffff", 5.6, cap="round")
    d += line((-1.2, 6), (-1.2, 30), "#ffffff", 1.4, 0.9)
    d += line((0, 31), (0, 38), "#9d90d8", 5.6, cap="butt")  # the grip end
    d += line((0, 30.5), (0, 30.5), OUT, 0)
    info = write_svg("props/glowstick.svg", (-8, -2, 8, 44), d)
    sprites["glowstick"] = {"file": "source/props/glowstick.svg", "pivot": pivot_in(info, (0, 38)), "px_scale": 0.5, "length": 36}


def spr_door_open(sprites: dict) -> dict:
    ox, oy = 244, 138  # sprite origin on the stage
    dx, dy, dw, dh = 284 - ox, 138 - oy, 70, 124
    d = ""
    defs = lin_grad("spill", [(0, "#ffd88a", 0.7), (0.6, "#ff9a4a", 0.25), (1, "#ff7a59", 0.0)], 0, 0, 0, 1)
    defs += lin_grad("room", [(0, "#fff2c8"), (1, "#ffb25a")], 0, 0, 0, 1)
    d += poly([(dx - 4, dy + dh), (dx + dw + 4, dy + dh), (dx + dw + 54, dy + dh + 86), (dx - 54, dy + dh + 86)], "url(#spill)")
    d += rect(dx - 7, dy - 7, dw + 14, dh + 7, "#3a2a82", OUT, 3, rx=4)
    d += rect(dx, dy, dw, dh, "url(#room)", None)
    d += rect(dx + 14, dy + 20, dw - 28, dh - 20, "#ffffff", None, op=0.5)
    # the open door leaves, swung inwards: dark slanted panels at both sides
    d += poly([(dx, dy), (dx + 13, dy + 7), (dx + 13, dy + dh - 3), (dx, dy + dh)], "#1c1250", OUT, 2.4)
    d += poly([(dx + dw, dy), (dx + dw - 13, dy + 7), (dx + dw - 13, dy + dh - 3), (dx + dw, dy + dh)], "#1c1250", OUT, 2.4)
    # a dancer's silhouette arriving in the doorway
    d += circle(dx + dw / 2, dy + 62, 7, "#2a1a54", OUT, 1.6) + path(f"M{dx + dw / 2 - 12} {dy + dh} Q{dx + dw / 2 - 12} {dy + 76} {dx + dw / 2} {dy + 74} Q{dx + dw / 2 + 12} {dy + 76} {dx + dw / 2 + 12} {dy + dh} Z", "#2a1a54", OUT, 1.6)
    d += neon((dx - 7, dy - 7), (dx + dw + 7, dy - 7), AMBER, 1.6, 1.0)
    d += rect(dx + 14, dy - 22, dw - 28, 11, "#0a0626", OUT, 2, rx=2) + rect(dx + 18, dy - 19, dw - 36, 5, AMBER, None, op=0.95)
    info = write_svg("props/door_open.svg", (0, -8, 150, 214), d, defs)
    return {"file": "source/props/door_open.svg", "pivot": pivot_in(info, (0, -8)), "px_scale": 0.5, "pos": [ox, oy - 8]}


def spr_deck(sprites: dict) -> None:
    # pad bezel: a 240 px square frame; the opening is 200 px (inner_ratio 0.8333) so the runtime scales it to the pad
    S, hole = 240, 200
    o = (S - hole) / 2
    defs = lin_grad("bz", [(0, "#4a3a9a"), (0.5, "#241a58"), (1, "#120b34")], 0, 0, 1, 1)
    defs += lin_grad("bzn", [(0, CYAN), (0.5, "#8c78d8"), (1, MAGENTA)], 0, 0, 1, 1)
    outer = f"M{26} 0 H{S - 26} Q{S} 0 {S} 26 V{S - 26} Q{S} {S} {S - 26} {S} H26 Q0 {S} 0 {S - 26} V26 Q0 0 26 0 Z"
    inner = (f"M{o + 20} {o} H{S - o - 20} Q{S - o} {o} {S - o} {o + 20} V{S - o - 20} Q{S - o} {S - o} {S - o - 20} {S - o} "
             f"H{o + 20} Q{o} {S - o} {o} {S - o - 20} V{o + 20} Q{o} {o} {o + 20} {o} Z")
    d = f'<path d="{outer} {inner}" fill="url(#bz)" fill-rule="evenodd"/>'
    d += path(outer, None, OUT, 4)
    d += path(inner, None, OUT, 3)
    d += path(inner, None, "url(#bzn)", 2.4, sop=0.95)
    d += path(outer, None, "#d9ccff", 1.4, sop=0.25)
    for sx, sy in ((11, 11), (S - 11, 11), (11, S - 11), (S - 11, S - 11)):
        d += circle(sx, sy, 5.4, "#6a5cc0", OUT, 2) + line((sx - 2.6, sy - 2.6), (sx + 2.6, sy + 2.6), OUT, 1.4)
    info = write_svg("props/pad_bezel.svg", (0, 0, S, S), d, defs)
    sprites["pad_bezel"] = {"file": "source/props/pad_bezel.svg", "pivot": pivot_in(info, (S / 2, S / 2)), "px_scale": 0.5, "inner_ratio": hole / S}

    # platter: turntable platter with a record, rotated on the beat (the label and the edge notch show the rotation)
    R = 120
    d = ""
    defs = rad_grad("vin", [(0, "#241a58"), (0.55, "#0b0726"), (1, "#05031a")], 0.5, 0.5, 0.5)
    defs += lin_grad("lab", [(0, MAGENTA), (1, VIOLET)], 0, 0, 1, 1)
    d += circle(0, 0, R, "#1c1352", OUT, 4)
    d += circle(0, 0, R - 6, None, "#6a4cff", 1.4, sop=0.5)
    for k in range(60):  # strobe dots
        a = k * math.tau / 60
        d += circle(math.cos(a) * (R - 11), math.sin(a) * (R - 11), 1.7, "#d9ccff" if k % 5 else CYAN, None, op=0.9 if k % 5 else 1.0)
    d += circle(0, 0, R - 20, "url(#vin)", OUT, 3)
    for rr in range(46, R - 22, 5):
        d += circle(0, 0, rr, None, "#6a4cff" if rr % 10 else "#4a3a9a", 0.8, sop=0.28)
    d += path(f"M{-R + 34} -34 A{R - 28} {R - 28} 0 0 1 -34 {-R + 34}", None, "#ffffff", 5, sop=0.16)
    d += path(f"M{R - 34} 34 A{R - 28} {R - 28} 0 0 1 34 {R - 34}", None, "#ffffff", 5, sop=0.1)
    d += circle(0, 0, 38, "url(#lab)", OUT, 3)
    d += poly([(0, -26), (22, 14), (-22, 14)], "#ffffff", None, op=0.0)
    d += path("M0 -30 L9 -6 L0 -10 L-9 -6 Z", "#ffe9a8", OUT, 1.4)
    d += rect(-24, 8, 48, 5, "#ffe9a8", None, op=0.9) + rect(-16, 17, 32, 4, "#ffe9a8", None, op=0.7)
    d += circle(0, 0, 4.5, "#d9ccff", OUT, 1.6)
    d += circle(0, -(R - 30), 4.2, AMBER, OUT, 1.4)  # the notch that shows the spin
    info = write_svg("props/platter.svg", (-R - 3, -R - 3, R + 3, R + 3), d, defs)
    sprites["platter"] = {"file": "source/props/platter.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "diameter": 2 * R}

    # knob
    d = ""
    defs = rad_grad("kb", [(0, "#8d7be0"), (0.6, "#3b2d80"), (1, "#1a1250")], 0.4, 0.35, 0.7)
    d += circle(0, 0, 24, "#0a0626", OUT, 3)
    for k in range(12):
        a = k * math.tau / 12 - math.pi / 2
        d += line((math.cos(a) * 20, math.sin(a) * 20), (math.cos(a) * 23, math.sin(a) * 23), "#8c78d8", 1.6, 0.8)
    d += circle(0, 0, 17, "url(#kb)", OUT, 2.4)
    d += circle(-4, -5, 6, "#ffffff", None, op=0.18)
    d += line((0, -4), (0, -15), CYAN, 3.4) + line((0, -4), (0, -15), "#e6fbff", 1.3)
    info = write_svg("props/knob.svg", (-26, -26, 26, 26), d, defs)
    sprites["knob"] = {"file": "source/props/knob.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}

    # fader slot and caps
    d = ""
    d += rect(-5, -60, 10, 120, "#05031a", OUT, 2.4, rx=5)
    d += rect(-1.6, -55, 3.2, 110, "#6a4cff", None, op=0.45)
    for k in range(11):
        y = -55 + k * 11
        d += line((-12, y), (-8, y), "#8c78d8", 1.4, 0.7) + line((8, y), (12, y), "#8c78d8", 1.4, 0.7)
    info = write_svg("props/fader_slot.svg", (-16, -66, 16, 66), d)
    sprites["fader_slot"] = {"file": "source/props/fader_slot.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "travel": 110}
    defs = lin_grad("fc", [(0, "#b9aef0"), (0.5, "#5a49b0"), (1, "#2a1f66")], 0, 0, 0, 1)
    d = rect(-12, -17, 24, 34, "url(#fc)", OUT, 2.8, rx=5)
    d += line((-12, 0), (12, 0), "#05031a", 3) + line((-10, 0), (10, 0), CYAN, 1.6)
    d += line((-9, -11), (9, -11), "#ffffff", 1.2, 0.4)
    info = write_svg("props/fader_cap.svg", (-16, -21, 16, 21), d, defs)
    sprites["fader_cap"] = {"file": "source/props/fader_cap.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
    d = rect(-26, -15, 52, 30, "url(#fc)", OUT, 2.8, rx=6)
    for k in range(-5, 6):
        d += line((k * 4.2, -11), (k * 4.2, 11), "#150a33", 1.4, 0.55)
    d += line((0, -15), (0, 15), MAGENTA, 2.4)
    info = write_svg("props/crossfader.svg", (-30, -19, 30, 19), d, defs)
    sprites["crossfader"] = {"file": "source/props/crossfader.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}

    d = rect(-20, -5, 40, 10, "#ffffff", None, rx=3)
    info = write_svg("props/vu_segment.svg", (-22, -7, 22, 7), d)
    sprites["vu_segment"] = {"file": "source/props/vu_segment.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
    d = circle(0, 0, 5.5, "#8c78d8", OUT, 1.8) + line((-2.6, -2.6), (2.6, 2.6), OUT, 1.4)
    info = write_svg("props/deck_screw.svg", (-8, -8, 8, 8), d)
    sprites["deck_screw"] = {"file": "source/props/deck_screw.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}

    # the illuminated edge trim of the desk lip: 1280 x 16, magenta to cyan to magenta
    defs = lin_grad("lg", [(0, MAGENTA), (0.5, CYAN), (1, MAGENTA)], 0, 0, 1, 0)
    d = rect(0, 5, 1280, 11, "url(#lg)", None, op=0.14)
    d += rect(0, 8, 1280, 6, "url(#lg)", None, op=0.28)
    d += rect(0, 9.5, 1280, 3, "url(#lg)", None, op=1.0)
    d += rect(0, 10.4, 1280, 1.2, "#ffffff", None, op=0.7)
    info = write_svg("props/desk_lip_glow.svg", (0, 0, 1280, 16), d, defs)
    sprites["desk_lip_glow"] = {"file": "source/props/desk_lip_glow.svg", "pivot": pivot_in(info, (640, 8)), "px_scale": 0.5}


# ---- silhouettes -----------------------------------------------------------------------------------------------------------

def _sil_shape(kind: str, up: bool) -> str:
    """The silhouette's filled shapes (one colour, so overlaps merge). Origin bottom centre, +y down."""
    s = ""
    if kind == "a":  # round head, short hair, broad shoulders
        s += path("M-38 0 L-36 -26 Q-34 -44 -14 -48 Q-8 -50 -8 -57 L8 -57 Q8 -50 14 -48 Q34 -44 36 -26 L38 0 Z", "#fff")
        s += ellipse(0, -74, 16, 19, "#fff") + path("M-17 -78 Q-16 -97 0 -97 Q16 -97 17 -78 Q8 -88 0 -88 Q-8 -88 -17 -78 Z", "#fff")
    elif kind == "b":  # hair bun and a ponytail, narrow shoulders
        s += path("M-30 0 L-28 -26 Q-26 -44 -11 -48 Q-7 -50 -7 -57 L7 -57 Q7 -50 11 -48 Q26 -44 28 -26 L30 0 Z", "#fff")
        s += ellipse(0, -72, 14, 17, "#fff") + circle(1, -94, 8, "#fff") + path("M10 -82 Q30 -80 27 -48 Q22 -62 12 -68 Z", "#fff")
    else:  # cap and hoodie, wide
        s += path("M-44 0 L-42 -24 Q-38 -46 -14 -49 Q-10 -50 -10 -57 L10 -57 Q10 -50 14 -49 Q38 -46 42 -24 L44 0 Z", "#fff")
        s += ellipse(0, -74, 18, 20, "#fff") + path("M-20 -80 Q-20 -102 0 -102 Q20 -102 20 -80 Z", "#fff") + path("M-19 -82 L-38 -77 L-19 -72 Z", "#fff")
        s += path("M-30 -50 Q-34 -62 -22 -64 L-16 -52 Z", "#fff") + path("M30 -50 Q34 -62 22 -64 L16 -52 Z", "#fff")
    if up:
        for sx in (-1, 1):
            s += line((sx * 26, -40), (sx * 50, -118), "#fff", 13)
            s += circle(sx * 51, -122, 8, "#fff")
    return s


def build_silhouettes() -> dict:
    out = {}
    fills = {"a": "#0d0828", "b": "#0b0622", "c": "#100a2e"}
    for kind in ("a", "b", "c"):
        entry = {}
        for state in ("idle", "up"):
            up = state == "up"
            shape = _sil_shape(kind, up)
            body = ""
            for dx, dy, col in ((-2.2, -1.2, CYAN), (2.2, -1.2, MAGENTA)):  # rim lights from both sides
                body += _recolor(shape, col, dx, dy)
            body += _recolor(shape, fills[kind], 0, 0)
            # a soft top light on the head so it is not a flat blob
            top = -128 if up else -98
            info = write_svg(f"silhouettes/sil_{kind}_{state}.svg", (-64, -140 if up else -112, 64, 4), body)
            entry[state] = {"file": f"source/silhouettes/sil_{kind}_{state}.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
        entry["height"] = 100
        out[f"sil_{kind}"] = entry
    return out


def _recolor(shape: str, color: str, dx: float, dy: float) -> str:
    """Re-emit the generic shape string with fill colour and an offset (None fills become the colour)."""
    s = shape
    s = s.replace('fill="#fff"', f'fill="{color}"')
    s = s.replace('stroke="#fff"', f'stroke="{color}"')
    return f'<g transform="translate({f(dx)} {f(dy)})">{s}</g>'


# ---- manifest --------------------------------------------------------------------------------------------------------------

def build_stage() -> dict:
    from . import sprites as png

    layers = []
    info = build_backdrop()
    layers.append({"id": "backdrop", "file": "source/backdrop.svg", "pos": [0, 0], "size": [W, H], "px_scale": 0.5})
    info = build_riser()
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
    woofers = []
    for sid in ("speaker_l", "speaker_r"):
        px, py = SPK_POS[sid]
        for (wx, wy, wr) in SPK_WOOFERS:
            woofers.append([px + wx, py + wy, wr])
    anchors = {
        "led_screen": [450, 104, 380, 104],
        "doorway": [284, 138, 70, 124],
        "floor_rows": FLOOR_ROWS,
        "floor_polygon": [[400, 266], [880, 266], [round(floor_x(880, 520)), 520], [round(floor_x(400, 520)), 520]],
        "floor_grid": {"vanishing_point": [VPX, VPY], "far_y": FY1, "far_x": [400 + 60 * i for i in range(9)],
                       "note": "x on the far wall base line; a floor line through far_x at screen row y is at x = vp_x + (far_x - vp_x) * (y - vp_y) / (far_y - vp_y)"},
        "light_points": [[150, 30], [330, 30], [510, 30], [770, 30], [950, 30], [1130, 30], [450, 58], [830, 58]],
        "woofers": woofers,
        "disco_ball": [640, 0],
        "riser": [640, 286, 240],
        "circle_centre": [640, 372],
        "circle_radii": [250, 46],
        "wall_left_x": FX0, "wall_right_x": FX1, "horizon_y": VPY,
        "led_tiles": led_tiles(),
    }
    return {"design_size": [W, H], "layers": layers, "anchors": anchors, "sprites": sprites}


def led_tiles() -> dict:
    """The lit dance floor's tile grid as drawn in build_backdrop: the runtime lights single tiles in chases and ripples on the beat.
    A tile (i, j) is the quad between far_x[i]..far_x[i+1] and rows[j]..rows[j+1], each x projected with floor_grid's rule."""
    rows = []
    z = 1.0
    while True:
        y = VPY + (FY1 - VPY) / z
        if y > H + 40:
            break
        if 264 <= y <= 530:
            rows.append(round(y, 2))
        z -= 0.065
    return {"far_x": [400 + 60 * i for i in range(9)], "rows": rows, "vanishing_point": [VPX, VPY], "far_y": FY1}
