"""View `furnace`: the great forge. Riveted steel hall, pipes, anvils and molten channels, with a huge grinning demon face forged
into the far wall whose furnace mouth is the screen (steel blue and white-hot orange)."""
from __future__ import annotations

import math
import random

from . import uw_stage as U, uw_views as V
from .lib import OUT, circle, clip, ellipse, f, group, lighten, line, lin_grad, mix, path, poly, rad_grad, rect, write_svg
from .uw_stage import BONE, EMBER, GOLD, LAVA, MAG, VIO, pline

W, H = V.W, V.H
R = V.Room(640, 125, 330, 950, 40, 262)
STEEL0, STEEL1, STEEL2, STEEL3 = "#10161f", "#1d2736", "#2c3a50", "#465a76"
HOT, WHITE_HOT = "#ff7a1a", "#fff2c0"
LIGHTS = [[140, 40], [300, 34], [470, 36], [810, 36], [980, 34], [1140, 40], [420, 62], [860, 62]]
MOUTH = (470, 208, 340, 34)  # the led screen
ANVILS = ((412, 284), (868, 284))
CHANNELS = ((600, 680), (456, 492), (788, 824))  # molten channels: x range on the far wall base


def pipe(side, u, th, s0, s1, col, uid):
    """A pipe running along a side wall at height u, from depth s0 to s1, th far-px thick."""
    a0, a1 = R.wall(side, s0, u + th / 2), R.wall(side, s1, u + th / 2)
    b1, b0 = R.wall(side, s1, u - th / 2), R.wall(side, s0, u - th / 2)
    d = poly([a0, a1, b1, b0], OUT, OUT, 4.0)
    d += poly([a0, a1, b1, b0], f"url(#{uid})", None)
    m0, m1 = R.wall(side, s0, u + th * 0.2), R.wall(side, s1, u + th * 0.2)
    d += line(m0, m1, "#ffffff", 1.6, 0.22)
    # flanges
    k = max(2, int((s1 - s0) / 0.22))
    for i in range(k + 1):
        s = s0 + (s1 - s0) * i / k
        t0, t1 = R.wall(side, s, u + th * 0.66), R.wall(side, s, u - th * 0.66)
        d += line(t0, t1, OUT, 6.5 * s ** 0.7) + line(t0, t1, "#6a7a96", 3.6 * s ** 0.7)
    return d


def anvil(cx, yb, sc, hot=True):
    """A big anvil with a hot bar on it, a hammer leaning on the base."""
    s = sc
    d = ellipse(cx, yb + 2 * s, 54 * s, 8 * s, "#05010a", None, op=0.55)
    base = [(cx - 34 * s, yb), (cx - 26 * s, yb - 14 * s), (cx + 26 * s, yb - 14 * s), (cx + 34 * s, yb)]
    d += poly(base, "#2a3448", OUT, 2.6 * s ** 0.5)
    waist = [(cx - 16 * s, yb - 14 * s), (cx - 12 * s, yb - 32 * s), (cx + 12 * s, yb - 32 * s), (cx + 16 * s, yb - 14 * s)]
    d += poly(waist, "#3a4660", OUT, 2.6 * s ** 0.5)
    top = [(cx - 52 * s, yb - 46 * s), (cx - 30 * s, yb - 48 * s), (cx + 40 * s, yb - 48 * s), (cx + 38 * s, yb - 32 * s), (cx - 26 * s, yb - 32 * s), (cx - 38 * s, yb - 36 * s)]
    d += poly(top, "#5a6c8a", OUT, 2.8 * s ** 0.5)
    d += poly([(cx - 52 * s, yb - 46 * s), (cx - 70 * s, yb - 44 * s), (cx - 52 * s, yb - 40 * s)], "#5a6c8a", OUT, 2.4 * s ** 0.5)  # the horn
    d += line((cx - 28 * s, yb - 46 * s), (cx + 36 * s, yb - 46 * s), "#c8d8f0", 1.6 * s ** 0.5, 0.7)
    if hot:  # a glowing bar and its glow
        d += ellipse(cx, yb - 50 * s, 40 * s, 9 * s, HOT, None, op=0.18)
        d += rect(cx - 22 * s, yb - 55 * s, 44 * s, 8 * s, "#ff5a1a", OUT, 1.6 * s ** 0.5, rx=2) + rect(cx - 20 * s, yb - 54 * s, 40 * s, 3.4 * s, WHITE_HOT, None, op=0.85, rx=1.5)
    # hammer
    d += line((cx + 46 * s, yb - 2 * s), (cx + 60 * s, yb - 36 * s), OUT, 7 * s ** 0.7) + line((cx + 46 * s, yb - 2 * s), (cx + 60 * s, yb - 36 * s), "#8a5a3a", 4 * s ** 0.7)
    d += rect(cx + 51 * s, yb - 46 * s, 22 * s, 13 * s, "#6a7a96", OUT, 2.0 * s ** 0.5, rx=2)
    return d


def gear(cx, cy, r, teeth, fill, rim, hub=None, ol=3.0):
    pts = []
    for k in range(teeth * 2):
        a = k * math.pi / teeth
        rr = r if k % 2 == 0 else r * 0.84
        pts += [(cx + math.cos(a - math.pi / teeth * 0.5) * rr, cy + math.sin(a - math.pi / teeth * 0.5) * rr), (cx + math.cos(a + math.pi / teeth * 0.5) * rr, cy + math.sin(a + math.pi / teeth * 0.5) * rr)]
    d = poly(pts, fill, OUT, ol)
    d += circle(cx, cy, r * 0.64, None, rim, 2.0, sop=0.6) + circle(cx, cy, r * 0.28, hub or "#0c1018", OUT, ol * 0.8)
    for k in range(6):
        a = k * math.tau / 6
        d += line((cx + math.cos(a) * r * 0.3, cy + math.sin(a) * r * 0.3), (cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62), OUT, 4.0)
    return d


def demon_face(rng):
    """The great face hammered into the far wall: horns, smiling crescent eyes, vent nostrils, a furnace mouth."""
    cx = 640
    d = ""
    # head plate: a wide rounded hexagon of riveted steel, with a lava glow leaking out of the seams
    head = [(430, 54), (850, 54), (916, 118), (900, 214), (856, 262), (424, 262), (380, 214), (364, 118)]
    d += poly([(x * 1.0 + (6 if x > cx else -6), y) for x, y in head], "#ff5a1a", None, op=0.12)
    d += poly(head, "url(#face)", OUT, 4.4)
    d += poly([(444, 62), (836, 62), (896, 120), (884, 212), (848, 254), (432, 254), (396, 212), (384, 120)], None, "#7a8cb0", 1.4, sop=0.45)
    for k in range(6):  # forehead plates
        x = 440 + k * 72
        d += line((x, 56), (x + (k - 2.5) * 5, 110), "#05080e", 2.2, 0.7)
    for (a, b) in ((120, 52), (150, 60)):
        d += U.neon_path(f"M450 {a} L{cx - 20} {a + 6} L{cx} {a - 6} L{cx + 20} {a + 6} L830 {a}", HOT, 0.8, 0.7) if a == 120 else ""
    # horns sweeping up and out to the ceiling
    for sg in (-1, 1):
        pts = U.UC.bez((cx + sg * 232, 76), (cx + sg * 330, 52), (cx + sg * 292, 40 - 0), 22)
        d += U.UC.horn(pts, 34, 5, "#5a6c8a", rings=4, sw=3.2)
    # brows and smiling eyes
    for sg in (-1, 1):
        ex = cx + sg * 100
        d += poly([(ex - sg * 8, 104), (ex + sg * 84, 92), (ex + sg * 90, 106), (ex - sg * 6, 124)], "#3a4a68", OUT, 3.0)  # brow slab
        sock = [(ex - 62, 128), (ex + 62, 128), (ex + 74, 156), (ex - 74, 156)]
        d += poly([(ex - 70, 124), (ex + 70, 124), (ex + 74, 160), (ex - 74, 160)], "#06080d", OUT, 3.4)
        d += path(f"M{ex - 56} 152 Q{ex} 106 {ex + 56} 152 Q{ex} 130 {ex - 56} 152 Z", "#fff2c0", None)  # the glowing grin of an eye
        d += path(f"M{ex - 56} 152 Q{ex} 106 {ex + 56} 152", None, "#ff9a2a", 3.4, sop=0.9)
        d += circle(ex, 146, 5.5, "#ff5a1a", None, op=0.95)
        d += rect(ex - 66, 160, 132, 6, "#2a3448", OUT, 2.0, rx=2)
    # cheek plates and gear ears
    for sg in (-1, 1):
        d += gear(cx + sg * 268, 168, 34, 12, "#3a4a68", HOT)
        d += poly([(cx + sg * 232, 176), (cx + sg * 330, 168), (cx + sg * 318, 224), (cx + sg * 250, 244)], "#2c3a50", OUT, 3.0)
        d += bolt_row(cx + sg * 250, 232, cx + sg * 316, 4)
        d += U.neon((cx + sg * 240, 214), (cx + sg * 312, 206), HOT, 0.9, 0.7)
    # nose: a ridge with two vent nostrils
    d += poly([(cx - 22, 120), (cx + 22, 120), (cx + 30, 182), (cx + 12, 192), (cx - 12, 192), (cx - 30, 182)], "#3a4a68", OUT, 3.0)
    d += line((cx - 12, 124), (cx - 14, 180), "#9ab0d8", 1.6, 0.5)
    for sg in (-1, 1):
        d += ellipse(cx + sg * 14, 184, 9, 6, "#05080e", OUT, 2.0) + ellipse(cx + sg * 14, 185, 5, 3, HOT, None, op=0.9)
    return d


def bolt_row(x0, y, x1, n, r=2.0):
    out = ""
    for i in range(n):
        out += circle(x0 + (x1 - x0) * (i + 0.5) / n, y, r, "#8a9ab8", OUT, 0.9)
    return out


def mouth(rng):
    """The furnace mouth: lips, a white-hot interior, iron teeth, the screen frame inside."""
    x, y, w, h = MOUTH
    d = path(f"M{x - 32} {y - 12} Q{640} {y - 36} {x + w + 32} {y - 12} L{x + w + 40} {y + h + 22} Q{640} {y + h + 36} {x - 40} {y + h + 22} Z", "#3a4a68", OUT, 4.0)
    d += path(f"M{x - 18} {y - 8} Q{640} {y - 26} {x + w + 18} {y - 8} L{x + w + 22} {y + h + 14} Q{640} {y + h + 26} {x - 22} {y + h + 14} Z", "url(#maw)", OUT, 3.0)
    d += rect(x - 4, y - 4, w + 8, h + 8, "#05080e", OUT, 2.6, rx=4) + rect(x, y, w, h, "#06020a", None)
    n = 11
    for k in range(n):  # iron teeth: upper and lower
        tx = x - 14 + (w + 28) * (k + 0.5) / n
        tw = (w + 28) / n * 0.46
        big = k % 2 == 0
        d += poly([(tx - tw, y - 8), (tx, y + (20 if big else 12)), (tx + tw, y - 8)], "#aab8d4", OUT, 2.2) + line((tx - tw * 0.3, y - 4), (tx, y + (14 if big else 8)), "#ffffff", 1.0, 0.5)
        d += poly([(tx - tw, y + h + 10), (tx, y + h - (18 if not big else 10)), (tx + tw, y + h + 10)], "#aab8d4", OUT, 2.2)
    d += U.neon((x - 18, y + h + 16), (x + w + 18, y + h + 16), HOT, 1.2, 0.9)
    return d


def build_backdrop():
    rng = random.Random(555)
    defs = ""
    d = ""
    defs += lin_grad("bg", [(0, STEEL0), (1, "#161e2c")], 0, 0, 0, 1)
    d += rect(0, 0, W, H, "url(#bg)")
    defs += lin_grad("face", [(0, "#46587a"), (0.5, "#2c3a50"), (1, "#1c2638")], 0, 0, 0, 1)
    defs += lin_grad("maw", [(0, "#ff9a2a"), (0.5, "#ff4a1a"), (1, "#a01410")], 0, 0, 0, 1)
    defs += lin_grad("pipe", [(0, "#8a9ab8"), (0.35, "#4a5c7c"), (1, "#1c2638")], 0, 0, 0, 1)
    defs += lin_grad("pipe2", [(0, "#6a7a96"), (0.4, "#34425c"), (1, "#141c2a")], 0, 0, 0, 1)
    # ---- ceiling: girders and a crane rail
    defs += lin_grad("ceil", [(0, "#080b12"), (1, "#222e44")], 0, 0, 0, 1)
    d += poly([(0, -6), (W, -6), (R.fx1, R.fy0), (R.fx0, R.fy0)], "url(#ceil)")
    for s in (1.0, 1.18, 1.4, 1.7, 2.1, 2.7):
        y = R.vy + (R.fy0 - R.vy) * s
        if y > -10:
            d += line((R.vx - R.half * s, y), (R.vx + R.half * s, y), OUT, 9 * s ** 0.5) + line((R.vx - R.half * s, y), (R.vx + R.half * s, y), "#4a5c7c", 5 * s ** 0.5)
            d += line((R.vx - R.half * s, y - 2 * s), (R.vx + R.half * s, y - 2 * s), "#8a9ab8", 1.2, 0.5)
    for xf in (R.fx0 + 80, 640, R.fx1 - 80):
        xt = R.vx + (xf - R.vx) * (-6 - R.vy) / (R.fy0 - R.vy)
        d += line((xf, R.fy0), (xt, -6), OUT, 6) + line((xf, R.fy0), (xt, -6), "#34425c", 3)
    # ---- far wall: dark plates with the demon face
    defs += lin_grad("fw", [(0, "#1c2638"), (1, "#0e141e")], 0, 0, 0, 1)
    d += rect(R.fx0, R.fy0, R.fx1 - R.fx0, R.fy1 - R.fy0, "url(#fw)")
    for k in range(8):
        d += line((R.fx0 + k * 80, R.fy0), (R.fx0 + k * 80, R.fy1), "#05080e", 2.0, 0.6)
    for k in range(5):
        d += line((R.fx0, R.fy0 + k * 46), (R.fx1, R.fy0 + k * 46), "#05080e", 2.0, 0.6)
    defs += rad_grad("wallglow", [(0, "#ff7a2a", 0.45), (1, "#ff3a1a", 0.0)], 0.5, 0.78, 0.55)
    d += ellipse(640, 240, 360, 130, "url(#wallglow)")
    d += demon_face(rng)
    d += mouth(rng)
    # the screen frame is the mouth: runtime paints into MOUTH
    # ---- side walls: plates, hazard stripes, pipes, glowing vents
    defs += lin_grad("lw", [(0, "#060910"), (1, "#26344c")], 0, 0, 1, 0)
    defs += lin_grad("rw", [(0, "#26344c"), (1, "#060910")], 0, 0, 1, 0)
    ytop0 = R.vy + (R.fy0 - R.vy) * R.vx / R.half
    ybot0 = R.vy + (R.fy1 - R.vy) * R.vx / R.half
    lw = [(0, ytop0), (R.fx0, R.fy0), (R.fx0, R.fy1), (0, ybot0)]
    rw = [(W - x, y) for x, y in lw]
    d += poly(lw, "url(#lw)") + poly(rw, "url(#rw)")
    for side in (-1, 1):
        for s in (1.0, 1.25, 1.55, 1.9, 2.3, 2.56):  # panel seams
            a, b = R.wall(side, s, 0), R.wall(side, s, 222)
            d += line(a, b, "#05080e", 2.6 * s ** 0.6, 0.7) + line((a[0] + side * -2, a[1]), (b[0] + side * -2, b[1]), "#6a7a96", 1.0, 0.3)
        d += pipe(side, 190, 16, 1.0, 2.6, "#4a5c7c", "pipe")
        d += pipe(side, 150, 10, 1.0, 2.6, "#4a5c7c", "pipe2")
        d += pipe(side, 22, 14, 1.0, 2.6, "#4a5c7c", "pipe")
        # hazard stripe skirting
        for i in range(10):
            sa = 1.0 + 1.6 * i / 10
            sb = 1.0 + 1.6 * (i + 0.5) / 10
            d += poly([R.wall(side, sa, 0), R.wall(side, sb, 0), R.wall(side, sb, 9), R.wall(side, sa, 9)], HOT, None, op=0.85)
        # glowing vent slits in rows
        for s in (1.12, 1.42, 1.75, 2.1):
            for u in (86, 100, 114):
                a, b = R.wall(side, s, u), R.wall(side, s + 0.1, u)
                d += line(a, b, "#05080e", 5.0 * s ** 0.7) + line(a, b, HOT, 2.6 * s ** 0.7, 0.95)
    # boiler hatches under the woofers: a bolted plate each side with two round sockets
    woofers = []
    for side, x0 in ((-1, 58), (1, W - 58 - 124)):
        d += rect(x0, 112, 124, 188, "#26344c", OUT, 3.4, rx=6)
        d += rect(x0 + 4, 116, 116, 180, None, "#6a7a96", 1.4, rx=4, sop=0.5)
        d += bolt_row(x0 + 10, 124, x0 + 114, 5, 2.6) + bolt_row(x0 + 10, 288, x0 + 114, 5, 2.6)
        for (cy, r) in ((172, 24), (242, 34)):
            cx = x0 + 62
            d += circle(cx, cy, r + 8, "#3a4a68", OUT, 3.0) + circle(cx, cy, r + 4, "#08020a", OUT, 2.4) + circle(cx, cy, r + 1.5, "#05010a", None)
            woofers.append([cx, cy, r])
        d += U.neon((x0 + 6, 300), (x0 + 118, 300), HOT, 1.0, 0.8)
    # ---- floor: steel diamond plate, molten channels with grates
    defs += lin_grad("fl", [(0, "#243048"), (0.3, "#162030"), (1, "#080c14")], 0, 0, 0, 1)
    floor_poly = [(0, ybot0), (R.fx0, R.fy1), (R.fx1, R.fy1), (W, ybot0), (W, H), (0, H)]
    d += poly(floor_poly, "url(#fl)")
    defs += clip("fclip", poly(floor_poly))
    fl = ""
    ys = R.floor_lines()
    xfar = [R.fx0 + 62 * k for k in range(-8, 18)]
    for j in range(len(ys) - 1):
        for i in range(len(xfar) - 1):
            if (i + j) % 2:
                q = [(R.floor_x(xfar[i], ys[j]), ys[j]), (R.floor_x(xfar[i + 1], ys[j]), ys[j]), (R.floor_x(xfar[i + 1], ys[j + 1]), ys[j + 1]), (R.floor_x(xfar[i], ys[j + 1]), ys[j + 1])]
                fl += poly(q, "#5a6c8a", None, op=0.14)
    for i, y in enumerate(ys):
        fl += line((-80, y), (W + 80, y), "#8a9ab8", 1.0 + i * 0.14, 0.2)
    for x in xfar:
        fl += line((x, R.fy1), (R.floor_x(x, H + 40), H + 40), "#8a9ab8", 1.3, 0.18)
    for j in range(len(ys) - 1):  # diamond-plate studs
        ym = (ys[j] + ys[j + 1]) / 2
        sc = R.scale(ym)
        if ym < R.fy1:
            continue
        for i in range(len(xfar) - 1):
            if rng.random() < 0.5:
                xm = R.floor_x((xfar[i] + xfar[i + 1]) / 2, ym)
                fl += ellipse(xm, ym, 5 * sc, 1.8 * sc, "#8a9ab8", None, op=0.22)
    d += group(fl, 'clip-path="url(#fclip)"')
    defs += lin_grad("chan", [(0, "#ffd070"), (0.12, "#ff8a2a"), (0.55, "#e03a14"), (1, "#8a0e12")], 0, 0, 0, 1)
    for (a, b) in CHANNELS:
        q = [(R.floor_x(a, R.fy1), R.fy1), (R.floor_x(b, R.fy1), R.fy1), (R.floor_x(b, H + 40), H + 40), (R.floor_x(a, H + 40), H + 40)]
        gl = [(R.floor_x(a - 14, R.fy1), R.fy1), (R.floor_x(b + 14, R.fy1), R.fy1), (R.floor_x(b + 14, H + 40), H + 40), (R.floor_x(a - 14, H + 40), H + 40)]
        d += poly(gl, "#ff5a1a", None, op=0.12)
        d += poly(q, OUT, OUT, 5) + poly(q, "url(#chan)", None)
        for i in range(0, len(ys) - 1):  # grate bars crossing the channel
            y = ys[i]
            if y < R.fy1 + 3 or y > H:
                continue
            d += line((R.floor_x(a, y), y), (R.floor_x(b, y), y), "#1c2638", 2.4 * R.scale(y) ** 0.8, 0.85)
            d += line((R.floor_x(a, y), y - 1.4), (R.floor_x(b, y), y - 1.4), "#8a9ab8", 0.8, 0.55)
        d += line((R.floor_x(a, R.fy1), R.fy1), (R.floor_x(a, H + 40), H + 40), "#c8d8f0", 1.2, 0.5)
    # the basin under the ladle on the left
    d += ellipse(296, 292, 44, 10, "#0a1018", OUT, 3) + ellipse(296, 291, 36, 7, "#ff5a1a", None, op=0.9) + ellipse(296, 290, 22, 4, WHITE_HOT, None, op=0.9)
    d += ellipse(296, 288, 70, 18, HOT, None, op=0.10)
    # anvils on the floor, flanking the channel
    for (ax, ay) in ANVILS:
        d += anvil(ax, ay, R.scale(ay) * 0.95)
    # chains and a hook hoist hung from the girders on the right
    for xf, ln in ((1000, 90), (1060, 132)):
        d += U.chain((xf, -6), (xf, ln), 9, "#8a9ab8")
        d += path(f"M{xf} {ln} L{xf} {ln + 8} Q{xf} {ln + 22} {xf + 12} {ln + 16} Q{xf + 20} {ln + 10} {xf + 13} {ln + 4}", None, OUT, 7.4) + path(f"M{xf} {ln} L{xf} {ln + 8} Q{xf} {ln + 22} {xf + 12} {ln + 16} Q{xf + 20} {ln + 10} {xf + 13} {ln + 4}", None, "#b8c8e4", 4.2)
    # ---- ceiling brackets
    d += V.ceiling_brackets(LIGHTS, "#8a9ab8")
    return write_svg("views/furnace_backdrop.svg", (0, 0, W, H), d, defs), woofers


def build_front():
    rng = random.Random(33)
    defs = lin_grad("gird", [(0, "#46587a"), (1, "#1c2638")], 0, 0, 0, 1)
    d = rect(-6, -6, W + 12, 34, "url(#gird)", OUT, 4.0)
    d += line((0, 24), (W, 24), "#05080e", 3, 0.5) + line((0, 2), (W, 2), "#9ab0d8", 1.4, 0.5)
    for k in range(34):
        d += circle(20 + k * 38, 14, 2.8, "#8a9ab8", OUT, 1.2)
    for xf, ln in ((46, 330), (1234, 270)):
        d += U.chain((xf, 26), (xf, ln - 22), 12, "#8a9ab8")
        hook = f"M{xf} {ln - 22} L{xf} {ln - 10} Q{xf} {ln + 10} {xf + 15} {ln + 4} Q{xf + 26} {ln - 2} {xf + 17} {ln - 12}"
        d += path(hook, None, OUT, 10) + path(hook, None, "#b8c8e4", 5.6)
    for gx, gy, gr, side in ((-24, 434, 112, -1), (W + 24, 434, 112, 1)):  # cog silhouettes at the lower corners
        d += gear(gx, gy, gr, 14, "#101826", HOT, hub="#05080e", ol=3.6)
        d += circle(gx, gy, gr * 0.84, None, HOT, 2.0, sop=0.55)
    return write_svg("views/furnace_front.svg", (0, 0, W, 470), d, defs)


def build_pieces():
    out = []
    rng = random.Random(81)
    # 1. eyes and mouth glow, pulsing
    w, h = 640, 230
    d = ""
    for sg in (-1, 1):
        ex = w / 2 + sg * 100
        d += ellipse(ex, 112, 78, 36, "#ff9a2a", None, op=0.1) + ellipse(ex, 118, 54, 22, "#ffe08a", None, op=0.14)
        d += path(f"M{ex - 56} 152 Q{ex} 106 {ex + 56} 152 Q{ex} 130 {ex - 56} 152 Z", "#fff6d0", None, op=0.55)
    mx, my, mw, mh = MOUTH
    d += ellipse(w / 2, my - 52 + mh / 2 + 52, mw / 2 + 36, 40, "#ff5a1a", None, op=0.22) + ellipse(w / 2, my - 52 + mh / 2 + 52, mw / 2 - 20, 20, "#ffb02e", None, op=0.3)
    d += rect(mx - 320 + 320 - 8, my - 52 + 52 + 2, mw + 16, mh - 4, "#ffd080", None, op=0.0)
    write_svg("views/furnace_eyes.svg", (0, 0, w, h), d)
    out.append(V.piece("furnace_eyes", "source/views/furnace_eyes.svg", (320, 52), (w, h), "pulse", "behind", "add", pivot=(w / 2, h * 0.5)))
    # 2. the ladle: crane chain, a tilted crucible and a stream of molten metal into the basin
    w, h = 190, 300
    d = ""
    d += U.chain((78, 0), (78, 74), 10, "#8a9ab8")
    d += path("M44 96 L64 78 L104 78 L128 100 Q122 140 84 146 Q48 142 44 96 Z", "#3a4a68", OUT, 3.6)
    d += path("M52 100 L66 86 L102 86 L118 102", None, "#9ab0d8", 1.6, sop=0.6)
    d += ellipse(84, 84, 22, 6, "#ff7a1a", OUT, 2.4) + ellipse(84, 84, 15, 3.6, WHITE_HOT, None, op=0.9)
    d += poly([(124, 98), (148, 104), (130, 116)], "#3a4a68", OUT, 3.0)
    d += bolt_row(56, 118, 112, 4, 2.2)
    d += rect(120, 108, 18, 190, "#ff7a1a", OUT, 2.0, rx=7) + rect(124, 110, 7, 186, WHITE_HOT, None, op=0.9, rx=3)
    d += rect(112, 108, 34, 190, "#ff5a1a", None, op=0.12, rx=9)
    for k in range(9):
        d += circle(rng.uniform(126, 152), rng.uniform(170, 290), rng.uniform(1.2, 2.4), "#ffe08a", None, op=0.9)
    write_svg("views/furnace_ladle.svg", (0, 0, w, h), d)
    out.append(V.piece("furnace_ladle", "source/views/furnace_ladle.svg", (190, -2), (w, h), "sway", "behind", "mix", pivot=(78, 4)))
    # 3. anvil sparks: both anvils, as one wide piece
    w, h = 700, 140
    d = ""
    for (ax, ay) in ANVILS:
        bx = ax - 238 + 0
        sc = R.scale(ay) * 0.95
        d += ellipse(bx, h - 18, 36 * sc, 8 * sc, "#ffb02e", None, op=0.2)
        for k in range(26):
            ang = math.radians(rng.uniform(-150, -30))
            ln = rng.uniform(16, 70) * sc
            p0 = (bx + rng.uniform(-14, 14) * sc, h - 24 - rng.uniform(0, 4))
            p1 = (p0[0] + math.cos(ang) * ln, p0[1] + math.sin(ang) * ln)
            d += line(p0, p1, "#ff9a2a", 1.4, 0.8) + circle(p1[0], p1[1], rng.uniform(1.0, 2.2), WHITE_HOT, None, op=0.95)
    write_svg("views/furnace_sparks.svg", (0, 0, w, h), d)
    out.append(V.piece("furnace_sparks", "source/views/furnace_sparks.svg", (238, ANVILS[0][1] - 55 * R.scale(ANVILS[0][1]) * 0.95 - (h - 24)), (w, h), "flicker", "behind", "add", pivot=(w / 2, h)))
    # 4. channel glow: the molten channels flaring, drawn as light only
    w, h = 1280, 460
    d = ""
    for (a, b) in CHANNELS:
        q = [(R.floor_x(a, R.fy1), 0), (R.floor_x(b, R.fy1), 0), (R.floor_x(b, 262 + h), h), (R.floor_x(a, 262 + h), h)]
        gl = [(R.floor_x(a - 22, R.fy1), 0), (R.floor_x(b + 22, R.fy1), 0), (R.floor_x(b + 22, 262 + h), h), (R.floor_x(a - 22, 262 + h), h)]
        d += poly(gl, "#ff6a1a", None, op=0.07) + poly(q, "#ff9a2a", None, op=0.12)
        d += line((R.floor_x((a + b) / 2, R.fy1), 0), (R.floor_x((a + b) / 2, 262 + h), h), WHITE_HOT, 2.0, 0.3)
    write_svg("views/furnace_channels.svg", (0, 0, w, h), d)
    out.append(V.piece("furnace_channels", "source/views/furnace_channels.svg", (0, 262), (w, h), "pulse", "behind", "add", pivot=(w / 2, 0)))
    return out


def build():
    _, woofers = build_backdrop()
    build_front()
    pieces = build_pieces()
    anchors = {
        "led_screen": list(MOUTH),
        "floor_rows": R.rows(),
        "floor_polygon": [[R.fx0, 264], [R.fx1, 264], [round(R.floor_x(R.fx1, 520)), 520], [round(R.floor_x(R.fx0, 520)), 520]],
        "floor_grid": R.grid(9),
        "light_points": LIGHTS,
        "woofers": woofers,
        "disco_ball": [640, 0],
        "riser": [640, 262, 340],
        "circle_centre": [640, 372],
        "circle_radii": [250, 46],
        "vanish": [640, 232],
        "horizon_y": R.vy,
        "wall_left_x": R.fx0, "wall_right_x": R.fx1,
        "face": [640, 150, 540], "anvils": [list(a) for a in ANVILS], "channels": [[R.floor_x(a, 262), R.floor_x(b, 262)] for a, b in CHANNELS],
    }
    return {"id": "furnace", "title": "The great forge",
            "layers": [V.layer("backdrop", "source/views/furnace_backdrop.svg", (0, 0), (W, H)),
                       V.layer("front_frame", "source/views/furnace_front.svg", (0, 0), (W, 470), "front")],
            "anchors": anchors, "pieces": pieces, "palette_hint": "steel"}
