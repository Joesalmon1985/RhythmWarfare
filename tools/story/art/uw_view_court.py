"""View `court`: the obsidian court of columns and braziers leading to the skull throne (violet, gold and magenta)."""
from __future__ import annotations

import math
import random

from . import uw_stage as U, uw_views as V
from .lib import OUT, circle, clip, ellipse, f, group, lighten, line, lin_grad, mix, path, poly, rad_grad, rect, write_svg
from .uw_stage import BONE, EMBER, GOLD, LAVA, MAG, VIO, pline

W, H = V.W, V.H
R = V.Room(640, 140, 390, 890, 66, 256)
COLS = (1.0, 1.45, 2.0)  # depth scales of the columns drawn in the backdrop; the nearest pair (2.7) is the front frame
COL_FRONT = 2.7
BRAZIERS = ((452, 280), (828, 280))  # pedestal bases (x, floor y)


def run_poly(ya, yb, a, b):
    """A floor strip between far-wall x a..b, from screen row ya to yb."""
    return [(R.floor_x(a, ya), ya), (R.floor_x(b, ya), ya), (R.floor_x(b, yb), yb), (R.floor_x(a, yb), yb)]


def wall_quad(side, sa, sb, ua, ub):
    return [R.wall(side, sa, ua), R.wall(side, sb, ua), R.wall(side, sb, ub), R.wall(side, sa, ub)]


def column(side, s, uid):
    """An obsidian column standing inboard of the wall at depth scale s: shaft, gold bands, plinth and a skull capital."""
    cx = R.vx + side * R.half * s * 0.86
    wd = 24 * s
    ybase = R.floor_y(s)
    ytop = R.vy + (R.fy0 - R.vy) * s
    hgt = ybase - ytop
    d = ellipse(cx, ybase + 2 * s, wd * 0.95, 4.5 * s, "#08020a", None, op=0.5)
    d += rect(cx - wd * 0.72, ybase - 14 * s, wd * 1.44, 14 * s, "#2d1a2c", OUT, 2.4 * s ** 0.5, rx=2)  # plinth
    d += rect(cx - wd / 2, ytop + 16 * s, wd, hgt - 28 * s, f"url(#{uid})", OUT, 2.8 * s ** 0.5)  # shaft
    for k in (-1, 1):  # flutes
        d += line((cx + k * wd * 0.18, ytop + 20 * s), (cx + k * wd * 0.18, ybase - 16 * s), "#05010a", 1.2 * s ** 0.5, 0.45)
    d += line((cx - side * wd * 0.36, ytop + 20 * s), (cx - side * wd * 0.36, ybase - 16 * s), "#ffffff", 1.4 * s ** 0.5, 0.16)
    for u in (36, 150):  # gold bands
        yb = R.vy + (R.fy1 - u - R.vy) * s
        d += rect(cx - wd * 0.56, yb - 3.4 * s, wd * 1.12, 6.8 * s, GOLD, OUT, 1.8 * s ** 0.5, rx=1.5)
        d += rect(cx - wd * 0.56, yb - 3.4 * s, wd * 1.12, 2.2 * s, "#ffffff", None, op=0.35)
    # glowing seam running up the lit side
    d += U.neon((cx + side * -wd * 0.45, ybase - 18 * s), (cx + side * -wd * 0.45, ytop + 30 * s), LAVA, 0.9 * s ** 0.5, 0.6)
    # capital: a flared block with a little skull, and a spike crown
    d += rect(cx - wd * 0.8, ytop + 2 * s, wd * 1.6, 15 * s, "#3a2038", OUT, 2.4 * s ** 0.5, rx=2)
    d += poly([(cx - wd * 0.8, ytop + 2 * s), (cx - wd * 0.55, ytop - 9 * s), (cx - wd * 0.25, ytop + 2 * s), (cx, ytop - 13 * s), (cx + wd * 0.25, ytop + 2 * s),
               (cx + wd * 0.55, ytop - 9 * s), (cx + wd * 0.8, ytop + 2 * s)], "#2d1a2c", OUT, 2.2 * s ** 0.5)
    d += U.skull(cx, ytop + 27 * s, 8.5 * s, BONE, "#ff7a1a", 1.6 * s ** 0.5, jaw=False)
    return d


def brazier(cx, yb, sc):
    """A tall bone-and-iron pedestal bowl; the flames above it are the `court_flames` piece."""
    d = ellipse(cx, yb + 2, 30 * sc, 7 * sc, "#05010a", None, op=0.55)
    d += poly([(cx - 22 * sc, yb), (cx - 12 * sc, yb - 14 * sc), (cx + 12 * sc, yb - 14 * sc), (cx + 22 * sc, yb)], "#46202c", OUT, 2.4)
    for k in range(3):  # a twisted rib stem
        xk = cx + (k - 1) * 6 * sc
        d += path(f"M{f(xk)} {f(yb - 14 * sc)} Q{f(xk + (3 - k) * 4 * sc)} {f(yb - 50 * sc)} {f(cx + (k - 1) * 9 * sc)} {f(yb - 86 * sc)}", None, OUT, 8 * sc)
        d += path(f"M{f(xk)} {f(yb - 14 * sc)} Q{f(xk + (3 - k) * 4 * sc)} {f(yb - 50 * sc)} {f(cx + (k - 1) * 9 * sc)} {f(yb - 86 * sc)}", None, BONE, 4.6 * sc)
    d += poly([(cx - 36 * sc, yb - 94 * sc), (cx + 36 * sc, yb - 94 * sc), (cx + 22 * sc, yb - 70 * sc), (cx - 22 * sc, yb - 70 * sc)], "#5a3030", OUT, 3)
    d += ellipse(cx, yb - 94 * sc, 36 * sc, 8 * sc, "#2a0c10", OUT, 3) + ellipse(cx, yb - 95 * sc, 30 * sc, 6 * sc, LAVA, None, op=0.85)
    d += ellipse(cx, yb - 96 * sc, 18 * sc, 3.4 * sc, "#fff2a0", None, op=0.85)
    for sx in (-1, 1):  # horns on the rim
        d += poly([(cx + sx * 34 * sc, yb - 92 * sc), (cx + sx * 46 * sc, yb - 118 * sc), (cx + sx * 26 * sc, yb - 96 * sc)], BONE, OUT, 2.0)
    d += U.skull(cx, yb - 78 * sc, 7.5 * sc, BONE, "#ff7a1a", 1.4, jaw=False)
    return d


def throne(cx, yb):
    d = ""
    # tall back with a spiked crown, ribs and a great skull
    back = (f"M{cx - 58} {yb} L{cx - 58} {yb - 80} L{cx - 74} {yb - 128} L{cx - 50} {yb - 112} L{cx - 36} {yb - 166} L{cx - 20} {yb - 120} L{cx} {yb - 190} "
            f"L{cx + 20} {yb - 120} L{cx + 36} {yb - 166} L{cx + 50} {yb - 112} L{cx + 74} {yb - 128} L{cx + 58} {yb - 80} L{cx + 58} {yb} Z")
    d += path(back, "url(#tback)", OUT, 4.2) + path(back, None, GOLD, 1.8, sop=0.7)
    for k in (-2, 0, 2):
        d += path(f"M{cx + k * 6} {yb - 112} Q{cx + k * 16} {yb - 70} {cx + k * 12} {yb - 34}", None, OUT, 6.6)
        d += path(f"M{cx + k * 6} {yb - 112} Q{cx + k * 16} {yb - 70} {cx + k * 12} {yb - 34}", None, BONE, 3.4)
    for sg in (-1, 1):
        d += U.UC.horn(U.UC.bez((cx + sg * 14, yb - 146), (cx + sg * 56, yb - 150), (cx + sg * 70, yb - 190)), 14, 2.4, BONE, rings=3)
    d += U.skull(cx, yb - 140, 19, BONE, "#ff5a1a", 2.4)
    d += circle(cx - 7.5, yb - 142, 8, "#ff7a1a", None, op=0.4) + circle(cx + 7.5, yb - 142, 8, "#ff7a1a", None, op=0.4)
    for sg in (-1, 1):  # arm rests ending in skulls
        d += rect(cx + sg * 66 - 11, yb - 58, 22, 8, "#6a5a62", OUT, 2.4, rx=3)
        d += rect(cx + sg * 66 - 5, yb - 50, 10, 46, "#3a2a32", OUT, 2.4)
        d += U.skull(cx + sg * 66, yb - 64, 8.5, BONE, "#ff7a1a", 1.8, jaw=False)
    d += rect(cx - 56, yb - 50, 112, 16, "#8a1a3a", OUT, 3, rx=5) + rect(cx - 56, yb - 50, 112, 5, "#ff6a8a", None, op=0.5, rx=2)
    d += rect(cx - 62, yb - 34, 124, 34, "url(#tback)", OUT, 3.4)
    for k in range(5):
        d += U.skull(cx - 44 + k * 22, yb - 17, 6, BONE, "#ff7a1a", 1.3, jaw=False)
    d += U.neon((cx - 58, yb - 33), (cx + 58, yb - 33), MAG, 1.2, 1.0)
    return d


def build_backdrop():
    rng = random.Random(201)
    defs = ""
    d = ""
    defs += lin_grad("bg", [(0, "#0b0314"), (0.6, "#1c0a24"), (1, "#0d0412")], 0, 0, 0, 1)
    d += rect(0, 0, W, H, "url(#bg)")
    defs += lin_grad("tback", [(0, "#74406c"), (1, "#26102c")], 0, 0, 0, 1)
    defs += lin_grad("shaft0", [(0, "#14081e"), (0.45, "#4a2a52"), (1, "#190a22")], 0, 0, 1, 0)
    # ---- vaulted ceiling with ribs
    defs += lin_grad("ceil", [(0, "#06020c"), (1, "#2a1034")], 0, 0, 0, 1)
    d += poly([(0, -6), (W, -6), (R.fx1, R.fy0), (R.fx0, R.fy0)], "url(#ceil)")
    for s in (1.0, 1.22, 1.45, 1.72, 2.0, 2.3, 2.6):
        y = R.vy + (R.fy0 - R.vy) * s
        if y > -8:
            d += line((R.vx - R.half * s, y), (R.vx + R.half * s, y), "#05010a", 5.0 * s ** 0.6, 0.8)
            d += line((R.vx - R.half * s, y + 2.2 * s), (R.vx + R.half * s, y + 2.2 * s), GOLD, 1.2 * s ** 0.6, 0.45)
    for k in range(-4, 5):
        xf = R.vx + k * 62.5
        xt = R.vx + (xf - R.vx) * (-6 - R.vy) / (R.fy0 - R.vy)
        d += line((xf, R.fy0), (xt, -6), "#3a1a44", 2.0, 0.7)
    # ---- far wall: polished obsidian with lava seams, a tall pointed niche behind the throne
    defs += lin_grad("fw", [(0, "#241030"), (0.6, "#1a0a22"), (1, "#3a1230")], 0, 0, 0, 1)
    d += rect(R.fx0, R.fy0, R.fx1 - R.fx0, R.fy1 - R.fy0, "url(#fw)")
    for k in range(9):
        x = R.fx0 + 8 + k * 61
        d += line((x, R.fy0), (x, R.fy1), "#08020c", 1.6, 0.5)
    for k in range(12):
        x = rng.uniform(R.fx0 + 10, R.fx1 - 10)
        d += U.vein(U.jag((x, R.fy1 - 2), (x + rng.uniform(-30, 30), R.fy1 - rng.uniform(20, 80)), 5, 6, rng), LAVA, 1.3, 0.8)
    cx = 640
    niche = f"M{cx - 108} {R.fy1} L{cx - 108} 128 Q{cx - 100} 84 {cx} 62 Q{cx + 100} 84 {cx + 108} 128 L{cx + 108} {R.fy1} Z"
    defs += rad_grad("nglow", [(0, "#d83a5a", 0.9), (0.5, "#7a1040", 0.92), (1, "#2a0a22", 1.0)], 0.5, 0.78, 0.8)
    d += path(niche, None, OUT, 11) + path(niche, None, GOLD, 6.5) + path(niche, "url(#nglow)", OUT, 2)
    for k in range(-5, 6):  # god rays fanning up the niche
        d += poly([(cx + k * 3, R.fy1 - 4), (cx + k * 18 - 4, 70 + abs(k) * 6), (cx + k * 18 + 4, 70 + abs(k) * 6)], "#ffb070", None, op=0.1)
    d += circle(cx, 150, 64, "#ff7a8a", None, op=0.12)
    # ---- the judgement tablet (led_screen) hanging above the throne
    d += V.hanging_frame(540, 76, 200, 30, (556, 724), "#3a1a30", top=62)
    # ---- side walls
    defs += lin_grad("lw", [(0, "#07020e"), (1, "#3c1a40")], 0, 0, 1, 0)
    defs += lin_grad("rw", [(0, "#3c1a40"), (1, "#07020e")], 0, 0, 1, 0)
    lw = [(0, R.vy + (R.fy0 - R.vy) * R.vx / R.half), (R.fx0, R.fy0), (R.fx0, R.fy1), (0, R.vy + (R.fy1 - R.vy) * R.vx / R.half)]
    rw = [(W - x, y) for x, y in lw]
    d += poly(lw, "url(#lw)") + poly(rw, "url(#rw)")
    stops = (1.0,) + COLS[1:] + (COL_FRONT,)
    for side in (-1, 1):
        # lower wainscot and a gold dado line, window recesses in every bay
        for sa, sb in zip((1.0,) + COLS[1:], COLS[1:] + (COL_FRONT,)):
            q = wall_quad(side, sa + 0.07 * (sb - sa), sb - 0.07 * (sb - sa), 0, 36)
            d += poly(q, "#120618", OUT, 1.8)
            d += poly(wall_quad(side, sa + 0.07 * (sb - sa), sb - 0.07 * (sb - sa), 34, 38), GOLD, None, op=0.5)
            u0, u1, u2, u3 = 58, 128, 156, 176
            sm = (sa + sb) / 2
            pa, pb = sa + 0.2 * (sb - sa), sb - 0.2 * (sb - sa)
            win = [R.wall(side, pa, u0), R.wall(side, pb, u0), R.wall(side, pb, u1), R.wall(side, (pa + pb) / 2 + 0.0, u3), R.wall(side, pa, u1)]
            glass = [(MAG, "#ffb02e", "#9a3cff")][0]
            d += poly([(x + (0 if k else 0), y) for k, (x, y) in enumerate(win)], "#0a0210", OUT, 3.2)
            inner_w = [R.wall(side, pa + 0.02 * (pb - pa), u0 + 5), R.wall(side, pb - 0.02 * (pb - pa), u0 + 5), R.wall(side, pb - 0.02 * (pb - pa), u1 - 2),
                       R.wall(side, (pa + pb) / 2, u3 - 9), R.wall(side, pa + 0.02 * (pb - pa), u1 - 2)]
            d += poly(inner_w, mix(MAG, "#150a33", 0.35), None)
            # glass facets: alternate magenta/amber/violet panes with a lead cross
            cols = [MAG, "#ffb02e", VIO, "#ff6a3a"]
            for j in range(3):
                ta, tb = pa + (pb - pa) * (j / 3.0 + 0.03), pa + (pb - pa) * ((j + 1) / 3.0 - 0.03)
                for i, (ua, ub) in enumerate(((u0 + 8, 90), (92, u1 - 4))):
                    pane = [R.wall(side, ta, ua), R.wall(side, tb, ua), R.wall(side, tb, ub), R.wall(side, ta, ub)]
                    d += poly(pane, cols[(i + j + (1 if side > 0 else 0)) % 4], None, op=0.72)
            d += line(R.wall(side, pa, 91), R.wall(side, pb, 91), "#08020c", 2.0 * ((pa + pb) / 2) ** 0.5, 0.9)
            for t in (1 / 3.0, 2 / 3.0):
                d += line(R.wall(side, pa + (pb - pa) * t, u0 + 5), R.wall(side, pa + (pb - pa) * t, u1), "#08020c", 2.0 * ((pa + pb) / 2) ** 0.5, 0.9)
            d += poly(inner_w, None, GOLD, 1.0 * ((pa + pb) / 2) ** 0.5, sop=0.6)
            # light spill on the floor below each window
            d += poly([R.wall(side, pa, 0), R.wall(side, pb, 0), (R.vx + side * R.half * pb * 0.8, R.floor_y(pb) + 18 * pb), (R.vx + side * R.half * pa * 0.8, R.floor_y(pa) + 18 * pa)], MAG, None, op=0.0)
    # ---- floor: glossy obsidian slabs, a red runner to the throne
    defs += lin_grad("fl", [(0, "#34163a"), (0.35, "#1c0a22"), (1, "#0b0310")], 0, 0, 0, 1)
    floor_poly = [(0, R.vy + (R.fy1 - R.vy) * R.vx / R.half), (R.fx0, R.fy1), (R.fx1, R.fy1), (W, R.vy + (R.fy1 - R.vy) * R.vx / R.half), (W, H), (0, H)]
    d += poly(floor_poly, "url(#fl)")
    defs += clip("fclip", poly(floor_poly))
    ys = R.floor_lines()
    xfar = [R.fx0 + 62.5 * k for k in range(-8, 17)]
    slabs = ""
    for j in range(len(ys) - 1):
        ya, yb = ys[j], ys[j + 1]
        for i in range(len(xfar) - 1):
            if (i + j) % 2:
                q = [(R.floor_x(xfar[i], ya), ya), (R.floor_x(xfar[i + 1], ya), ya), (R.floor_x(xfar[i + 1], yb), yb), (R.floor_x(xfar[i], yb), yb)]
                slabs += poly(q, "#4a2a58", None, op=0.22)
    for i, y in enumerate(ys):
        slabs += line((-80, y), (W + 80, y), "#a06ac0", 1.0 + i * 0.14, 0.22)
    for x in xfar:
        slabs += line((x, R.fy1), (R.floor_x(x, H + 40), H + 40), "#a06ac0", 1.3, 0.2)
    for k in range(28):  # hairline cracks with a lava glint
        xf_ = rng.uniform(R.fx0 - 400, R.fx1 + 400)
        ya = rng.uniform(R.fy1 + 6, H - 70)
        sc = R.scale(ya)
        xa = R.floor_x(xf_, ya)
        pts = U.jag((xa, ya), (xa + rng.uniform(-24, 24) * sc, ya + rng.uniform(10, 36) * sc), 4, 6 * sc, rng)
        slabs += path(pline(pts), None, "#08020c", 1.8 * sc, sop=0.7)
        if k % 4 == 0:
            slabs += path(pline(pts), None, LAVA, 0.9 * sc, sop=0.6)
    # polished obsidian: mirror streaks of the columns, the stained-glass windows and the braziers
    refl = ""
    defs += lin_grad("rfl_col", [(0, "#c08ae0", 0.22), (1, "#c08ae0", 0.0)], 0, 0, 0, 1)
    defs += lin_grad("rfl_fire", [(0, "#ffb05a", 0.5), (0.5, "#ff6a2a", 0.18), (1, "#ff6a2a", 0.0)], 0, 0, 0, 1)
    defs += lin_grad("rfl_glass", [(0, "#ff5ac0", 0.2), (1, "#ff5ac0", 0.0)], 0, 0, 0, 1)
    for s in COLS + (COL_FRONT,):
        for side in (-1, 1):
            cx_ = R.vx + side * R.half * s * 0.86
            yb_ = R.floor_y(s)
            refl += rect(cx_ - 10 * s, yb_ + 2, 20 * s, 70 * s, "url(#rfl_col)")
    for (bx, by) in BRAZIERS + ((516, 262), (764, 262)):
        sc = R.scale(by)
        refl += rect(bx - 20 * sc, by + 2, 40 * sc, 120 * sc, "url(#rfl_fire)")
        refl += ellipse(bx, by + 4 * sc, 34 * sc, 6 * sc, "#ffb05a", None, op=0.18)
    for side in (-1, 1):  # coloured light falling from each window bay onto the floor near the wall
        for sa, sb in zip((1.0,) + COLS[1:], COLS[1:] + (COL_FRONT,)):
            pa, pb = sa + 0.2 * (sb - sa), sb - 0.2 * (sb - sa)
            q = [R.wall(side, pa, 0), R.wall(side, pb, 0), (R.vx + side * R.half * pb * 0.66, R.floor_y(pb) + 30 * pb), (R.vx + side * R.half * pa * 0.66, R.floor_y(pa) + 30 * pa)]
            refl += poly(q, MAG, None, op=0.07) + poly(q[:2] + [((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2), ((q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2)], "#ffb02e", None, op=0.05)
    refl += poly(run_poly(R.fy1, H + 40, 560, 720), "url(#rfl_glass)")
    # gold inlay: a border band running along each wall, and cross-bands at the column bases
    for xf_ in (R.fx0 + 24, R.fx1 - 24):
        refl += line((R.floor_x(xf_, R.fy1), R.fy1), (R.floor_x(xf_, H + 40), H + 40), GOLD, 2.0, 0.55)
        refl += line((R.floor_x(xf_ + (8 if xf_ < 640 else -8), R.fy1), R.fy1), (R.floor_x(xf_ + (8 if xf_ < 640 else -8), H + 40), H + 40), GOLD, 1.0, 0.35)
    for s in COLS[1:] + (COL_FRONT,):
        y_ = R.floor_y(s)
        refl += line((R.floor_x(R.fx0 - 200, y_), y_), (R.floor_x(R.fx0 + 24, y_), y_), GOLD, 1.4 * s ** 0.5, 0.45)
        refl += line((R.floor_x(R.fx1 - 24, y_), y_), (R.floor_x(R.fx1 + 200, y_), y_), GOLD, 1.4 * s ** 0.5, 0.45)
    d += group(slabs + refl, 'clip-path="url(#fclip)"')
    # runner
    rx0, rx1 = 592, 688
    run = lambda ya, yb, a=rx0, b=rx1: [(R.floor_x(a, ya), ya), (R.floor_x(b, ya), ya), (R.floor_x(b, yb), yb), (R.floor_x(a, yb), yb)]
    defs += lin_grad("runner", [(0, "#ff4a3a", 0.9), (0.5, "#a0143a", 0.9), (1, "#4a0a2a", 0.95)], 0, 0, 0, 1)
    d += poly(run(R.fy1, H + 40, 585, 695), "#ff3a1a", None, op=0.10)
    d += poly(run(R.fy1, H + 40), "url(#runner)")
    for xf_ in (rx0, rx1):
        d += line((R.floor_x(xf_, R.fy1), R.fy1), (R.floor_x(xf_, H + 40), H + 40), GOLD, 2.4, 0.9)
        d += line((R.floor_x(xf_, R.fy1), R.fy1), (R.floor_x(xf_, H + 40), H + 40), "#ffffff", 0.8, 0.5)
    for i in range(0, len(ys) - 1, 1):  # gold diamonds down the middle
        ya, yb = ys[i], ys[i + 1]
        ym = (ya + yb) / 2
        sc = R.scale(ym)
        if ym > H:
            break
        d += poly([(640, ym - 9 * sc), (640 + 11 * sc, ym), (640, ym + 9 * sc), (640 - 11 * sc, ym)], None, GOLD, 1.5 * sc ** 0.7, sop=0.85)
    # ---- the dais: three steps with gold edges
    for i, (yf, a, b) in enumerate(((282, 440, 840), (272, 466, 814), (264, 492, 788))):
        hgt = 9
        xl, xr = R.floor_x(a, yf), R.floor_x(b, yf)
        d += poly([(xl, yf - hgt), (xr, yf - hgt), (xr, yf), (xl, yf)], "#2a1236", OUT, 2.4)
        d += poly([(xl + 5, yf - hgt - 8), (xr - 5, yf - hgt - 8), (xr, yf - hgt), (xl, yf - hgt)], "#4a2658", OUT, 2.2)
        d += line((xl + 2, yf - hgt), (xr - 2, yf - hgt), GOLD, 1.6, 0.9)
        d += U.neon((xl + 4, yf - 2.5), (xr - 4, yf - 2.5), LAVA, 0.9, 0.7)
        d += poly([(xl + 5, yf - hgt - 8), (xr - 5, yf - hgt - 8), (xr - 5, yf - hgt - 2), (xl + 5, yf - hgt - 2)], "#ff3a5a", None, op=0.07)
    # ---- throne, flanking guard braziers on the dais
    d += throne(640, 252)
    for sx in (-1, 1):  # small guard braziers either side of the throne
        d += brazier(640 + sx * 124, 262, 0.62)
    # ---- the big braziers on the floor, then the columns
    for (bx, by) in BRAZIERS:
        d += brazier(bx, by, R.scale(by) * 0.95)
    for side in (-1, 1):
        for s in sorted(COLS, reverse=False):
            pass
    for s in COLS:
        for side in (-1, 1):
            d += column(side, s, "shaft0")
    # ---- ceiling brackets for the lights
    d += V.ceiling_brackets(LIGHTS[:6] + [(x, y) for x, y in LIGHTS[6:]], "#8a7a8e")
    defs += ""
    return write_svg("views/court_backdrop.svg", (0, 0, W, H), d, defs)


LIGHTS = [[130, 36], [300, 30], [470, 36], [810, 36], [980, 30], [1150, 36], [540, 58], [740, 58]]


def build_front():
    """The nearest column pair, hugging the screen edges, and hanging drapes at the top corners (drawn over the crowd)."""
    defs = lin_grad("shaft0", [(0, "#14081e"), (0.45, "#4a2a52"), (1, "#190a22")], 0, 0, 1, 0)
    d = ""
    for side in (-1, 1):
        s = COL_FRONT
        cx = R.vx + side * R.half * s * 0.86
        d += column(side, s, "shaft0")
        # banner cloth in front of the wall at the corner
        x0 = 0 if side < 0 else W - 70
        d += poly([(x0, -4), (x0 + 70, -4), (x0 + 70, 250), (x0 + 35, 290), (x0, 250)], "#7a0f2e", OUT, 3.4)
        d += poly([(x0 + 8, -4), (x0 + 62, -4), (x0 + 62, 240), (x0 + 35, 272), (x0 + 8, 240)], None, GOLD, 1.6, sop=0.8)
        d += U.skull(x0 + 35, 96, 15, BONE, "#ff7a1a", 2.0, jaw=True)
        d += poly([(x0 + 35, 140), (x0 + 44, 168), (x0 + 35, 196), (x0 + 26, 168)], None, GOLD, 1.8, sop=0.9)
    return write_svg("views/court_front.svg", (0, 0, W, 470), d, defs)


def _flames(cx, base_y, h, rng, w=16):
    return U._flame_cluster(cx, base_y, h, rng, n=5, spread=h * 0.14, w=w)


def build_pieces():
    out = []
    rng = random.Random(55)
    # 1. throne aura: a warm radiance and rays behind the throne
    w, h = 440, 300
    defs = rad_grad("aura", [(0, "#ff8a6a", 0.5), (0.4, "#ff3a5a", 0.25), (1, "#ff2a4a", 0.0)], 0.5, 0.62, 0.5)
    d = ellipse(w / 2, h * 0.66, w / 2, h * 0.5, "url(#aura)")
    for k in range(-5, 6):
        d += poly([(w / 2 + k * 4, h * 0.75), (w / 2 + k * 36 - 7, 14 + abs(k) * 10), (w / 2 + k * 36 + 7, 14 + abs(k) * 10)], "#ffb08a", None, op=0.06)
    d += ellipse(w / 2, h * 0.88, 150, 14, "#ff5a6a", None, op=0.25)
    write_svg("views/court_aura.svg", (0, 0, w, h), d, defs)
    out.append(V.piece("court_throne_aura", "source/views/court_aura.svg", (640 - w / 2, 252 - h * 0.88), (w, h), "pulse", "behind", "add", pivot=(w / 2, h * 0.66)))
    # 2. brazier flames: tall tongues above the two floor braziers and the two dais ones, as one wide piece
    x0, x1 = 400, 880
    ytop, ybot = 70, 272
    w, h = x1 - x0, ybot - ytop
    d = ""
    for (bx, by, sc) in ((452, 280, R.scale(280) * 0.95), (828, 280, R.scale(280) * 0.95), (516, 262, 0.62), (764, 262, 0.62)):
        base = by - 96 * sc
        d += U._flame_cluster(bx - x0, base - ytop, 92 * sc + 24, rng, n=5, spread=20 * sc + 6, w=15 * sc + 4)
        for k in range(4):
            d += circle(bx - x0 + rng.uniform(-18, 18), base - ytop - rng.uniform(40, 110) * sc, rng.uniform(1.1, 2.2), "#ffe08a", None, op=0.9)
    write_svg("views/court_flames.svg", (0, 0, w, h), d)
    out.append(V.piece("court_flames", "source/views/court_flames.svg", (x0, ytop), (w, h), "flicker", "behind", "add", pivot=(w / 2, h)))
    # 3. banners: two long crimson banners hanging from the vault, swaying together from the top
    w, h = 580, 190
    d = ""
    for bx in (150, 430):
        d += U.chain((bx - 24, 0), (bx - 24, 24), 8) + U.chain((bx + 24, 0), (bx + 24, 24), 8)
        d += rect(bx - 38, 20, 76, 7, "#6a5a62", OUT, 2.2, rx=3)
        body = f"M{bx - 32} 27 L{bx + 32} 27 L{bx + 32} 150 L{bx} 184 L{bx - 32} 150 Z"
        d += path(body, "#8a1032", OUT, 3.4) + path(f"M{bx - 24} 33 L{bx + 24} 33 L{bx + 24} 146 L{bx} 172 L{bx - 24} 146 Z", None, GOLD, 1.6, sop=0.85)
        d += U.skull(bx, 74, 14, BONE, "#ff7a1a", 1.8, jaw=True)
        d += poly([(bx, 108), (bx + 9, 126), (bx, 144), (bx - 9, 126)], None, GOLD, 1.6, sop=0.9)
        d += line((bx - 32, 27), (bx - 32, 150), "#ffffff", 1.4, 0.15)
    write_svg("views/court_banners.svg", (0, 0, w, h), d)
    out.append(V.piece("court_banners", "source/views/court_banners.svg", (350, -2), (w, h), "sway", "behind", "mix", pivot=(w / 2, 6)))
    # 4. the court seal: a glowing ring of runes on the floor, matching circle_centre / circle_radii
    w, h = 540, 112
    cx, cy, rx, ry = w / 2, h / 2, 250, 46
    d = ellipse(cx, cy, rx + 14, ry + 8, "#ff3a5a", None, op=0.07)
    for rr, wd, op in ((1.0, 2.2, 0.95), (0.9, 1.4, 0.7), (0.62, 1.2, 0.5)):
        d += ellipse(cx, cy, rx * rr, ry * rr, None, GOLD if rr == 1.0 else MAG, wd, sop=op)
    for k in range(36):  # runes between the two outer rings
        a = k * math.tau / 36
        p0 = (cx + math.cos(a) * rx * 0.91, cy + math.sin(a) * ry * 0.91)
        p1 = (cx + math.cos(a) * rx * 0.99, cy + math.sin(a) * ry * 0.99)
        d += line(p0, p1, "#ffd2a0", 1.6 if k % 3 else 2.6, 0.85)
    star = [(cx + math.cos(math.radians(-90 + k * 144)) * rx * 0.62, cy + math.sin(math.radians(-90 + k * 144)) * ry * 0.62) for k in range(5)]
    d += path("M" + " L".join(f"{f(x)} {f(y)}" for x, y in star) + " Z", None, "#ff7a9a", 1.4, sop=0.8)
    write_svg("views/court_seal.svg", (0, 0, w, h), d)
    out.append(V.piece("court_seal", "source/views/court_seal.svg", (640 - w / 2, 372 - h / 2), (w, h), "pulse", "behind", "add", pivot=(w / 2, h / 2)))
    return out


def build():
    build_backdrop()
    build_front()
    pieces = build_pieces()
    ws = R.rows()
    anchors = {
        "led_screen": [540, 76, 200, 30],
        "floor_rows": ws,
        "floor_polygon": [[R.fx0, 258], [R.fx1, 258], [round(R.floor_x(R.fx1, 520)), 520], [round(R.floor_x(R.fx0, 520)), 520]],
        "floor_grid": R.grid(9),
        "light_points": LIGHTS,
        "disco_ball": [640, 0],
        "riser": [640, 262, 330],
        "circle_centre": [640, 372],
        "circle_radii": [250, 46],
        "vanish": [640, 200],
        "horizon_y": R.vy,
        "wall_left_x": R.fx0, "wall_right_x": R.fx1,
        "throne": [640, 252], "braziers": [list(b) for b in BRAZIERS],
    }
    return {"id": "court", "title": "Obsidian court",
            "layers": [V.layer("backdrop", "source/views/court_backdrop.svg", (0, 0), (W, H)),
                       V.layer("front_frame", "source/views/court_front.svg", (0, 0), (W, 470), "front")],
            "anchors": anchors, "pieces": pieces, "palette_hint": "violet"}
