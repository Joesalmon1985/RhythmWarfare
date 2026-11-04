"""View `courtyard`: a walled courtyard garden at dusk: warm brick walls with ivy, a peach to lilac sky with the first stars and the ward
building's lit windows behind, paving slabs, raised beds of vegetables and flowers, a bench, a water butt, a washing line of bunting and
costumes, and festoon string lights between two posts."""
from __future__ import annotations

import math
import random

from . import mh_stage as M, mh_views as V
from .lib import OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, poly, rad_grad, rect, write_svg
from .mh_stage import BUTTER, CORAL, INK, LEAF, LILAC, MINT, W, H, WOOD, WOOD_D, WOOD_L, paper_star

R = M.Room(640, 128, 340, 940, 120, 262)
BRICK, BRICK_D = "#d49080", "#b87a76"
STONES = ["#b9b2cc", "#aea7c2", "#c4bdd6", "#a6a0ba", "#bcb5d0"]
PETAL = ["#ffd966", "#ff8f8a", "#ff9ac0", "#b9a6f0", "#ffb070"]
CAB_Y = lambda x: 30 + 34 * (1 - ((x - 640) / 600.0) ** 2)  # the festoon cable's height at screen x


def P(xf, s, u=0):
    return (R.vx + (xf - R.vx) * s, R.vy + (R.fy1 - u - R.vy) * s)


def lerp_quad(q, a, b):
    """Bilinear point in the quad [p00, p10, p11, p01] at fractions (a along 0->1 edge, b along 0->3 edge)."""
    top = (q[0][0] + (q[1][0] - q[0][0]) * a, q[0][1] + (q[1][1] - q[0][1]) * a)
    bot = (q[3][0] + (q[2][0] - q[3][0]) * a, q[3][1] + (q[2][1] - q[3][1]) * a)
    return (top[0] + (bot[0] - top[0]) * b, top[1] + (bot[1] - top[1]) * b)


def plant_at(x, y, sc, kind, rng):
    d = ""
    if kind == "cabbage":
        for k, (r_, c) in enumerate(((9, "#6cc98a"), (6.6, "#8fe0a0"), (3.6, "#b8f0c0"))):
            d += circle(x, y - 6 * sc, r_ * sc, c, OUT if k == 0 else None, 1.4)
    elif kind == "sunflower":
        d += line((x, y), (x, y - 26 * sc), OUT, 4.4) + line((x, y), (x, y - 26 * sc), "#5dbb7a", 2.4)
        d += ellipse(x - 6 * sc, y - 10 * sc, 6 * sc, 3 * sc, "#5dbb7a", OUT, 1)
        for k in range(10):
            a = k * math.tau / 10
            d += ellipse(x + math.cos(a) * 8 * sc, y - 28 * sc + math.sin(a) * 8 * sc, 4 * sc, 2.6 * sc, "#ffd23f", OUT, 0.9)
        d += circle(x, y - 28 * sc, 5 * sc, "#8a5a3a", OUT, 1)
    elif kind == "lavender":
        for k in range(5):
            xx = x + (k - 2) * 3.4 * sc
            d += line((xx, y), (xx + (k - 2) * 1.4 * sc, y - 18 * sc), "#7fcf8f", 1.8)
            d += ellipse(xx + (k - 2) * 1.6 * sc, y - 20 * sc, 2.0 * sc, 5.5 * sc, "#a98aef", OUT, 0.8)
    elif kind == "tomato":
        d += line((x, y), (x, y - 30 * sc), "#a8743c", 2.2)
        for k in range(4):
            d += ellipse(x + (k % 2 * 2 - 1) * 5 * sc, y - (8 + k * 6) * sc, 5 * sc, 3.2 * sc, "#5dbb7a", OUT, 0.8)
        for k in range(3):
            d += circle(x + (k - 1) * 5 * sc, y - (10 + k * 5) * sc, 2.6 * sc, "#ff5a4a", OUT, 0.8)
    else:  # marigolds
        for k in range(4):
            xx = x + (k - 1.5) * 5 * sc
            d += circle(xx, y - (6 + (k % 2) * 4) * sc, 3.6 * sc, rng.choice(("#ffb02e", "#ff8a3a")), OUT, 0.9) + circle(xx, y - (6 + (k % 2) * 4) * sc, 1.4 * sc, "#c4601a", None)
        d += ellipse(x, y - 2 * sc, 11 * sc, 3.4 * sc, "#5dbb7a", None, op=0.9)
    return d


def bed(xf0, xf1, s0, s1, side, h, kinds, seed):
    rng = random.Random(seed)
    top = [P(xf0, s0, h), P(xf1, s0, h), P(xf1, s1, h), P(xf0, s1, h)]
    front = [P(xf0, s1, h), P(xf1, s1, h), P(xf1, s1, 0), P(xf0, s1, 0)]
    inner = [P(xf1, s0, h), P(xf1, s1, h), P(xf1, s1, 0), P(xf1, s0, 0)] if side < 0 else [P(xf0, s0, h), P(xf0, s1, h), P(xf0, s1, 0), P(xf0, s0, 0)]
    d = ellipse((top[0][0] + top[2][0]) / 2, front[2][1] + 3, abs(front[1][0] - front[0][0]) * 0.8 + 20, 5, INK, None, op=0.2)
    d += poly(inner, WOOD_D, OUT, 2.4) + poly(front, WOOD, OUT, 2.4)
    d += poly(top, "#6a4a3a", OUT, 2.4)
    d += poly([lerp_quad(top, 0.06, 0.08), lerp_quad(top, 0.94, 0.08), lerp_quad(top, 0.94, 0.92), lerp_quad(top, 0.06, 0.92)], "#7a5646", None)
    for k in range(1, 3):  # board lines
        d += line(lerp_quad(front, 0, k / 3), lerp_quad(front, 1, k / 3), darken(WOOD, 0.25), 1.2, 0.6)
    for (a, b, kind) in kinds:
        x, y = lerp_quad(top, a, b)
        sc = (s0 + (s1 - s0) * b) * 0.72
        d += plant_at(x, y, sc, kind, rng)
    return d


def brick_wall_far(defs):
    d = rect(R.fx0, R.fy0, R.fx1 - R.fx0, R.fy1 - R.fy0, BRICK, None)
    defs_ = lin_grad("fwb", [(0, "#ffffff"), (1, "#2a1b4e")], 0, 0, 0, 1)
    rng = random.Random(4)
    for k in range(0, 16):
        y = R.fy0 + k * 9
        d += line((R.fx0, y), (R.fx1, y), BRICK_D, 1.2, 0.7)
        off = 14 if k % 2 else 0
        for x in range(int(R.fx0) + off, int(R.fx1), 28):
            d += line((x, y), (x, y + 9), BRICK_D, 1.1, 0.7)
    for k in range(70):  # tone variation
        d += rect(rng.uniform(R.fx0, R.fx1 - 14), R.fy0 + rng.randrange(0, 15) * 9 + 1, 13, 7, rng.choice(("#ffffff", "#2a1b4e")), None, op=0.06)
    d += rect(R.fx0, R.fy0 - 8, R.fx1 - R.fx0, 10, "#e6c0b0", OUT, 2.4, rx=2)  # coping stones
    d += rect(R.fx0, R.fy1 - 6, R.fx1 - R.fx0, 6, darken(BRICK, 0.2), None, op=0.5)
    return defs_, d


def side_wall_bricks(side):
    d = ""
    s_e = abs((0 if side < 0 else W) - R.vx) / R.half
    n_courses = 15
    for k in range(1, n_courses):
        u = k * (R.height / n_courses)
        d += line(R.wall(side, 1, u), R.wall(side, s_e, u), BRICK_D, 1.2, 0.7)
    for k in range(n_courses):
        u0, u1 = k * (R.height / n_courses), (k + 1) * (R.height / n_courses)
        off = 0.06 if k % 2 else 0.0
        s = 1.0 + off
        while s < s_e:
            d += line(R.wall(side, s, u0), R.wall(side, s, u1), BRICK_D, 1.0, 0.6)
            s += 0.12
    # coping along the wall top
    q = [R.wall(side, 1, R.height + 8), R.wall(side, s_e, R.height + 8), R.wall(side, s_e, R.height - 2), R.wall(side, 1, R.height - 2)]
    d += poly(q, "#e6c0b0", OUT, 2.4)
    return d


def ivy_clusters(seed):
    rng = random.Random(seed)
    d = ""
    for side in (-1, 1):
        for k in range(26):
            s = rng.uniform(1.05, 2.1)
            u = rng.choice((rng.uniform(R.height - 30, R.height), rng.uniform(20, 120)))
            x, y = R.wall(side, s, u)
            r_ = rng.uniform(4, 9) * s * 0.7
            d += circle(x, y, r_, rng.choice(("#4fae6a", "#5dbb7a", "#3f9a5a")), None, op=0.95)
        for k in range(8):  # hanging vines from the top
            s = rng.uniform(1.1, 2.0)
            x, y = R.wall(side, s, R.height)
            ln = rng.uniform(24, 70) * s * 0.7
            d += line((x, y), (x + rng.uniform(-3, 3), y + ln), "#3f9a5a", 2.2 * s * 0.6)
            for j in range(4):
                d += circle(x + rng.uniform(-3, 3), y + ln * (j + 1) / 4, 3.6 * s * 0.6, "#5dbb7a", None)
    return d


def build_backdrop():
    defs = ""
    d = ""
    # the sky: peach at the horizon, lilac, then deep dusk blue with the first stars and a crescent moon
    defs += lin_grad("sky", [(0, "#2d2a62"), (0.35, "#6a5aa8"), (0.72, "#e0a0b8"), (1, "#ffd0a8")], 0, 0, 0, 1)
    d += rect(0, 0, W, 150, "url(#sky)")
    rng = random.Random(8)
    for k in range(60):
        y = rng.uniform(2, 70)
        d += circle(rng.uniform(0, W), y, rng.uniform(0.6, 1.6), "#ffffff", None, op=rng.uniform(0.5, 1.0) * (1 - y / 120))
    d += circle(1030, 52, 17, "#fff6d0", None) + circle(1038, 47, 15, "#6a5aa8", None) + circle(1030, 52, 26, "#fff6d0", None, op=0.12)
    for (cx, cy, w_) in ((200, 78, 130), (920, 96, 160), (560, 52, 110)):  # long dusk clouds
        d += ellipse(cx, cy, w_, 7, "#f2c8d8", None, op=0.6) + ellipse(cx + 24, cy - 6, w_ * 0.6, 5, "#ffe0e8", None, op=0.55)
    # the ward building rising behind the far wall, with warm lit windows and a chimney
    d += rect(R.fx0 + 30, 58, R.fx1 - R.fx0 - 60, 70, "#6a5a8a", OUT, 2.4) + rect(R.fx0 + 20, 54, R.fx1 - R.fx0 - 40, 8, "#4a3a6a", OUT, 2)
    d += rect(840, 28, 16, 30, "#5a4a7a", OUT, 2) + ellipse(848, 22, 9, 4, "#c8b8e0", None, op=0.5)
    for k in range(9):
        for j in range(2):
            lit = (k * 3 + j * 5) % 4 != 0
            d += rect(R.fx0 + 48 + k * 58, 68 + j * 28, 26, 18, "#ffd98a" if lit else "#4a3f78", OUT, 1.6) + (line((R.fx0 + 61 + k * 58, 68 + j * 28), (R.fx0 + 61 + k * 58, 86 + j * 28), OUT, 1.2) if lit else "")
    # tree crowns behind the side walls
    for (cx, cy, r_, c) in ((60, 112, 62, "#2f5a58"), (210, 98, 56, "#37686a"), (1080, 100, 60, "#2f5a58"), (1230, 108, 64, "#37686a"), (420, 110, 0, "#000")):
        if r_:
            d += circle(cx, cy + 20, r_, c, None) + circle(cx + 24, cy + 28, r_ * 0.7, lighten(c, 0.08), None)
    # far wall, side walls
    fdefs, fw = brick_wall_far(defs)
    defs += fdefs
    d += fw
    for side in (-1, 1):
        x_edge = 0 if side < 0 else W
        s_e = abs(x_edge - R.vx) / R.half
        top_e, bot_e = R.wall(side, s_e, R.height), R.wall(side, s_e, 0)
        far_top, far_bot = R.wall(side, 1, R.height), R.wall(side, 1, 0)
        gid = "sw" + ("l" if side < 0 else "r")
        defs += lin_grad(gid, [(0, darken(BRICK, 0.28)), (1, darken(BRICK, 0.05))] if side < 0 else [(0, darken(BRICK, 0.05)), (1, darken(BRICK, 0.28))], 0, 0, 1, 0)
        d += poly([(x_edge, top_e[1]), far_top, far_bot, (x_edge, bot_e[1])], f"url(#{gid})")
        d += side_wall_bricks(side)
    d += ivy_clusters(5)
    # ground: paving slabs, grass edges and a worn path
    defs += lin_grad("gd", [(0, "#b9b2cc"), (1, "#d8d2e6")], 0, 0, 0, 1)
    ye = R.vy + (R.fy1 - R.vy) * (R.vx / R.half)
    d += poly([(0, ye), (W, ye), (W, H), (0, H)], "url(#gd)")
    fl = V.planks(R, STONES, 6, 0.1, seam="#7a7690", seam_op=0.55, seed=3)
    defs += clip("gc", f'<polygon points="0,{f(ye)} {f(R.fx0)},{f(R.fy1)} {f(R.fx1)},{f(R.fy1)} {W},{f(ye)} {W},{H} 0,{H}"/>')
    d += group(fl, 'clip-path="url(#gc)"')
    for side in (-1, 1):  # grass verges along the wall bases
        xa, xb = (R.fx0, R.fx0 + 14) if side < 0 else (R.fx1 - 14, R.fx1)
        d += poly([P(xa, 1.0), P(xb, 1.0), P(xb, 4.0), P(xa, 4.0)], "#7fcf8f", None, op=0.85)
    for k in range(26):  # tufts and daisies between the slabs
        rr = random.Random(k)
        xf, s = rr.uniform(R.fx0, R.fx1), rr.uniform(1.1, 3.0)
        x, y = P(xf, s)
        d += path(f"M{f(x - 3 * s * 0.6)} {f(y)} Q{f(x)} {f(y - 8 * s * 0.6)} {f(x + 3 * s * 0.6)} {f(y)}", None, "#5dbb7a", 1.8, sop=0.9)
    # a worn path of lighter slabs towards the gate
    for k in range(10):
        s0 = 1.0 + k * 0.22
        d += poly([P(600, s0), P(680, s0), P(680, s0 + 0.14), P(600, s0 + 0.14)], "#ece6f6", None, op=0.55)
    # the gate back into the building (doorway), with a lantern
    gx, gy, gw, gh = 380, 160, 64, 102
    d += path(f"M{gx - 8} {gy + gh} L{gx - 8} {gy + 20} Q{gx + gw / 2} {gy - 24} {gx + gw + 8} {gy + 20} L{gx + gw + 8} {gy + gh} Z", "#e6c0b0", OUT, 3)
    d += path(f"M{gx} {gy + gh} L{gx} {gy + 22} Q{gx + gw / 2} {gy - 12} {gx + gw} {gy + 22} L{gx + gw} {gy + gh} Z", "#8a5a6a", OUT, 2.6)
    for k in range(1, 5):
        d += line((gx + k * gw / 5, gy + 6 - abs(k - 2.5) * 2), (gx + k * gw / 5, gy + gh), darken("#8a5a6a", 0.2), 1.4, 0.7)
    for yy in (gy + 40, gy + 82):
        d += line((gx, yy), (gx + gw, yy), "#3a2a3a", 3.6) + circle(gx + 6, yy, 2.2, "#d8b24a", OUT, 1)
    d += circle(gx + gw - 10, gy + 62, 3.4, "#d8b24a", OUT, 1.4)
    d += line((gx + gw + 18, gy + 14), (gx + gw + 18, gy + 28), OUT, 2) + rect(gx + gw + 10, gy + 28, 16, 22, "#ffe6a0", OUT, 2.4, rx=3) + ellipse(gx + gw + 18, gy + 39, 14, 16, "#ffe6a0", None, op=0.28)
    # trellis with climbing roses on the far wall
    tx = 800
    for k in range(6):
        d += line((tx + k * 16, 150), (tx + k * 16, 258), "#c8a070", 3) + line((tx, 150 + k * 20), (tx + 80, 150 + k * 20), "#c8a070", 3)
    for k in range(18):
        rr = random.Random(100 + k)
        d += circle(tx + rr.uniform(0, 80), rr.uniform(150, 256), rr.uniform(3, 6), rr.choice(("#4fae6a", "#5dbb7a")), None) + (circle(tx + rr.uniform(0, 80), rr.uniform(150, 250), 3, rr.choice(("#ff8f8a", "#ff9ac0")), OUT, 1) if k % 3 == 0 else "")
    # raised beds against both walls, a bench and a water butt
    d += bed(340, 410, 1.08, 1.7, -1, 34, [(0.3, 0.2, "cabbage"), (0.7, 0.2, "cabbage"), (0.3, 0.55, "tomato"), (0.7, 0.55, "tomato"), (0.3, 0.85, "cabbage"), (0.7, 0.85, "marigold")], 1)
    d += bed(340, 410, 1.9, 2.5, -1, 34, [(0.3, 0.3, "sunflower"), (0.7, 0.3, "lavender"), (0.3, 0.75, "lavender"), (0.7, 0.75, "sunflower")], 2)
    d += bed(870, 940, 1.08, 1.7, 1, 34, [(0.3, 0.2, "lavender"), (0.7, 0.2, "marigold"), (0.3, 0.6, "sunflower"), (0.7, 0.6, "cabbage"), (0.5, 0.9, "lavender")], 3)
    # bench frontal against the right wall
    bx, by = 1136, 392
    d += ellipse(bx, by + 2, 74, 6, INK, None, op=0.22)
    for sx in (-1, 1):
        d += rect(bx + sx * 56 - 4, by - 26, 8, 26, WOOD_D, OUT, 2)
    d += rect(bx - 66, by - 40, 132, 7, WOOD_L, OUT, 2.4, rx=2) + rect(bx - 66, by - 62, 132, 7, WOOD_L, OUT, 2.4, rx=2) + rect(bx - 66, by - 52, 132, 7, WOOD_L, OUT, 2.4, rx=2)
    for sx in (-1, 1):
        d += rect(bx + sx * 60 - 3, by - 66, 6, 28, WOOD_D, OUT, 2)
    d += rect(bx - 30, by - 44, 34, 6, "#ff8f8a", OUT, 1.6, rx=2) + paper_star(bx + 20, by - 47, 4, BUTTER, 1)  # a cushion and a star
    # water butt and watering can on the left
    wx, wy = 104, 396
    d += ellipse(wx, wy + 2, 40, 6, INK, None, op=0.22) + path(f"M{wx - 28} {wy - 70} L{wx - 32} {wy} L{wx + 32} {wy} L{wx + 28} {wy - 70} Z", "#5a9ac0", OUT, 3)
    for yy in (wy - 54, wy - 24):
        d += path(f"M{wx - 30 + (yy - wy + 54) * 0.05} {yy} L{wx + 30} {yy}", None, "#2f6a90", 4)
    d += ellipse(wx, wy - 70, 28, 8, "#3a7aa0", OUT, 2.4) + rect(wx + 28, wy - 18, 10, 5, "#c8c8d8", OUT, 1.6) + circle(wx + 42, wy - 14, 2.4, "#6ad0ff", None, op=0.9)
    d += path(f"M{wx + 54} {wy} L{wx + 52} {wy - 18} L{wx + 78} {wy - 18} L{wx + 76} {wy} Z", "#ffb070", OUT, 2) + path(f"M{wx + 78} {wy - 14} L{wx + 98} {wy - 28}", None, OUT, 4) + path(f"M{wx + 78} {wy - 14} L{wx + 98} {wy - 28}", None, "#ffb070", 2)
    # cables: the festoon cable and its posts' brackets (the posts are in the front frame)
    cab = [(x, CAB_Y(x)) for x in range(0, W + 20, 20)]
    d += path("M" + " L".join(f"{x} {f(y)}" for x, y in cab), None, "#3a3a52", 2.4)
    for x in (150, 330, 510, 770, 950, 1130):  # ceiling-less lamp mounts: little hanging clamps
        d += rect(x - 6, CAB_Y(x) - 3, 12, 6, "#6a6a82", OUT, 1.4, rx=2)
    return defs, d


def build_front():
    d = ""
    defs = lin_grad("ft", [(0, "#2f6a52"), (1, "#4fae6a")], 0, 0, 1, 1)
    # the two posts that carry the cables, with a cross-brace
    for x in (58, 1222):
        d += rect(x - 8, 20, 16, 450, WOOD, OUT, 3.2, rx=2) + rect(x - 5, 20, 4, 450, WOOD_L, None, op=0.7)
        d += rect(x - 14, 16, 28, 9, WOOD_D, OUT, 2.4, rx=2)
        d += circle(x, 40, 3.6, "#6a6a82", OUT, 1.6)
    # foreground foliage in the top corners: broad leaves, dark against the dusk, with soft highlights
    rng = random.Random(77)
    for cx0, sg in ((0, 1), (W, -1)):
        for k in range(14):
            x = cx0 + sg * rng.uniform(-10, 130)
            y = rng.uniform(-10, 100)
            r_ = rng.uniform(14, 34)
            a = math.degrees(math.atan2(y - 20, x - cx0 - sg * 40)) if k % 2 else rng.uniform(-60, 60)
            d += f'<g transform="rotate({f(a)} {f(x)} {f(y)})">' + ellipse(x, y, r_ * 1.5, r_ * 0.6, rng.choice(("#2f6a52", "#3a7a58", "#276248")), OUT, 2.0) + line((x - r_ * 1.3, y), (x + r_ * 1.3, y), "#5dbb7a", 1.4, 0.7) + "</g>"
    d += poly([(24, 150), (92, 150), (84, 176), (32, 176)], "#a8743c", OUT, 2.4)
    for k in range(7):
        d += circle(30 + k * 10, 148 + (k % 2) * 3, 6, PETAL_C[k % 5], OUT, 1.2)
    d += line((24, 150), (58, 112), "#6a5a7a", 1.4) + line((92, 150), (58, 112), "#6a5a7a", 1.4)
    return defs, d


PETAL_C = ["#ffd966", "#ff8f8a", "#ff9ac0", "#b9a6f0", "#ffb070"]


def build_pieces():
    out = []
    # 1. festoon string lights (additive bulbs with glows) along the cable
    w, h = W, 90
    defs = rad_grad("bg", [(0, "#ffffff", 0.9), (0.4, "#ffffff", 0.3), (1, "#ffffff", 0.0)])
    d = ""
    cols = ["#ffd98a", "#ffb0d0", "#a8f0e0", "#ffe6a0", "#c8b8ff"]
    for k in range(26):
        x = 40 + k * (W - 80) / 25
        y = CAB_Y(x) + 6
        c = cols[k % 5]
        d += line((x, CAB_Y(x)), (x, y), "#3a3a52", 1.0, 0.8)
        d += circle(x, y + 5, 14, c, None, op=0.22) + circle(x, y + 5, 8, c, None, op=0.45) + circle(x, y + 5, 4.2, "#ffffff", None) + circle(x, y + 5, 3, c, None, op=0.9)
    write_svg("views/courtyard_lights.svg", (0, 0, w, h), d, defs)
    out.append(M.piece("string_lights", "source/views/courtyard_lights.svg", (0, 0), (w, h), "flicker", "behind", "add", pivot=(w / 2, 30)))
    # 2. the washing line: bunting and a few costumes pegged out to dry (a stripy shirt, a towel cape, a tutu, a paper crown)
    x0, y0, w, h = 40, 84, 1200, 190
    d = ""
    cord = [(6 + t * (w - 12), 6 + 30 * 4 * t * (1 - t) + 10 * t) for t in [k / 60 for k in range(61)]]
    d += path("M" + " L".join(f"{f(x)} {f(y)}" for x, y in cord), None, "#6a5a7a", 2.0)

    def at(t):
        i = int(t * 60)
        return cord[i]

    from .mh_pieces import BUNT
    for k in range(34):  # bunting flags
        t = (k + 0.5) / 34
        if 0.22 < t < 0.78:
            continue
        x, y = at(t)
        d += poly([(x - 7, y), (x + 7, y), (x, y + 17)], BUNT[k % 6], OUT, 1.4)
    # costumes
    x, y = at(0.3)  # a striped pirate shirt
    d += poly([(x - 20, y + 2), (x + 20, y + 2), (x + 34, y + 18), (x + 24, y + 26), (x + 16, y + 20), (x + 16, y + 64), (x - 16, y + 64), (x - 16, y + 20), (x - 24, y + 26), (x - 34, y + 18)], "#fffaf0", OUT, 2.2)
    for k in range(6):
        d += rect(x - 16, y + 24 + k * 7, 32, 3.4, "#2c3f7a", None, op=0.95)
    x, y = at(0.43)  # a towel cape
    d += poly([(x - 16, y + 2), (x + 16, y + 2), (x + 20, y + 62), (x - 20, y + 62)], "#ff9a2e", OUT, 2.2)
    for k in range(4):
        d += rect(x - 17, y + 14 + k * 12, 34, 4.4, "#fff2c8", None, op=0.9)
    for k in range(9):
        d += line((x - 18 + k * 4.5, y + 62), (x - 18 + k * 4.5, y + 68), "#fff2c8", 1.6)
    x, y = at(0.57)  # a tutu
    d += poly([(x - 8, y + 2), (x + 8, y + 2), (x + 22, y + 24), (x + 18, y + 30), (x + 10, y + 26), (x + 0, y + 32), (x - 10, y + 26), (x - 18, y + 30), (x - 22, y + 24)], "#ffb0d0", OUT, 2.0)
    for k in range(5):
        d += line((x - 6 + k * 3, y + 6), (x - 16 + k * 8, y + 26), "#ff8ab8", 1.2, 0.7)
    x, y = at(0.7)  # a paper crown
    d += poly([(x - 16, y + 2), (x + 16, y + 2), (x + 16, y + 26), (x + 8, y + 16), (x, y + 30), (x - 8, y + 16), (x - 16, y + 26)], "#ffd23f", OUT, 2.0)
    d += circle(x - 8, y + 12, 2.4, "#e03a5a", OUT, 0.8) + circle(x + 8, y + 12, 2.4, "#3b86ff", OUT, 0.8)
    for t in (0.3, 0.43, 0.57, 0.7):
        px, py = at(t)
        for sx in (-1, 1):
            d += rect(px + sx * 11 - 2.5, py - 2, 5, 10, "#ffd966", OUT, 1.0, rx=1)
    write_svg("views/courtyard_washing.svg", (0, 0, w, h), d)
    out.append(M.piece("washing_line", "source/views/courtyard_washing.svg", (x0, y0), (w, h), "sway", "behind", pivot=(w / 2, 6)))
    # 3. fireflies and a soft dusk glow over the garden (additive)
    w, h = 1000, 260
    defs = rad_grad("ff", [(0, "#f6ffb0", 0.95), (0.35, "#e6ff90", 0.4), (1, "#e6ff90", 0.0)])
    defs += lin_grad("hz", [(0, "#ffb88a", 0.0), (0.7, "#ffb88a", 0.16), (1, "#ffb88a", 0.0)], 0, 0, 0, 1)
    d = rect(0, 10, w, 120, "url(#hz)")
    rng = random.Random(12)
    for k in range(34):
        x, y = rng.uniform(20, w - 20), rng.uniform(40, h - 20)
        r_ = rng.uniform(5, 11)
        d += circle(x, y, r_, "url(#ff)", None) + circle(x, y, r_ * 0.22, "#ffffcc", None)
    write_svg("views/courtyard_fireflies.svg", (0, 0, w, h), d, defs)
    out.append(M.piece("fireflies", "source/views/courtyard_fireflies.svg", (140, 100), (w, h), "pulse", "behind", "add", pivot=(w / 2, h / 2)))
    return out


def build():
    defs, d = build_backdrop()
    write_svg("views/courtyard_backdrop.svg", (0, 0, W, H), d, defs)
    defs, d = build_front()
    write_svg("views/courtyard_front.svg", (0, 0, W, 470), d, defs)
    pieces = build_pieces()
    pts_ = [[x, round(CAB_Y(x) + 6)] for x in (150, 330, 510, 770, 950, 1130, 430, 850)]
    anchors = {
        "doorway": [380, 160, 64, 102],
        "floor_rows": R.rows(),
        "floor_polygon": [[R.fx0 + 10, 264], [R.fx1 - 10, 264], [round(R.floor_x(R.fx1, 520)), 520], [round(R.floor_x(R.fx0, 520)), 520]],
        "floor_grid": R.grid(9),
        "light_points": pts_,
        "circle_centre": [640, 372],
        "circle_radii": [250, 46],
        "vanish": [640, 190],
        "horizon_y": R.vy,
        "wall_left_x": R.fx0, "wall_right_x": R.fx1,
    }
    return {"id": "courtyard", "title": "Courtyard garden",
            "layers": [M.layer("backdrop", "source/views/courtyard_backdrop.svg", (0, 0), (W, H)),
                       M.layer("front_frame", "source/views/courtyard_front.svg", (0, 0), (W, 470), "front")],
            "anchors": anchors, "pieces": pieces, "palette_hint": "dusk"}
