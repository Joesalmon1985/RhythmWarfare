"""View `corridor`: a long bright ward corridor of honey parquet and pale mint walls, painted doors with paper stars, a wooden hand rail,
a tea trolley, a laundry trolley with a stripy shirt hanging out of it, and glazed garden doors at the far end (morning mint and peach)."""
from __future__ import annotations

import math
import random

from . import mh_stage as M, mh_views as V
from .lib import OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, poly, rad_grad, rect, write_svg
from .mh_stage import BUTTER, CORAL, INK, LEAF, LILAC, MINT, W, H, WOOD, WOOD_D, WOOD_L, paper_star, plant

R = M.Room(640, 150, 470, 810, 96, 256)
DOOR_COLS = ["#ff9a8a", "#ffd966", "#c9b8f0", "#9fd8ff", "#8fd9c8", "#ffc9a0"]
HONEY = ["#d9ac70", "#d0a062", "#e0b87e", "#c99a5c", "#d6a96c"]


def wp(side, s0, s1, u0, u1, pts_):
    """Map (a, b) fractions inside the wall rectangle s0..s1 x u0..u1 to screen points."""
    return [V.wall_lerp(R, side, s0, s1, u0, u1, a, b) for a, b in pts_]


def wall_star(side, s0, s1, u0, u1, ca, cb, ra, rb, col, ol=1.4):
    pts_ = [(ca + math.cos(math.radians(-90 + k * 36)) * (ra if k % 2 == 0 else ra * 0.45), cb + math.sin(math.radians(-90 + k * 36)) * (rb if k % 2 == 0 else rb * 0.45)) for k in range(10)]
    return poly(wp(side, s0, s1, u0, u1, pts_), col, OUT, ol)


def wall_ellipse(side, s0, s1, u0, u1, ca, cb, ra, rb, col, ol=1.6, n=20):
    pts_ = [(ca + math.cos(k * math.tau / n) * ra, cb + math.sin(k * math.tau / n) * rb) for k in range(n)]
    return poly(wp(side, s0, s1, u0, u1, pts_), col, OUT if ol else None, ol or 0)


def wall_door(side, s0, s1, col):
    uh = 120
    d = poly(V.wall_quad(R, side, s0 - 0.03, s1 + 0.03, 0, uh + 8), "#fbfbff", OUT, 2.8)  # frame
    d += poly(V.wall_quad(R, side, s0, s1, 0, uh), col, OUT, 2.2)
    d += poly(wp(side, s0, s1, 0, uh, [(0.14, 0.08), (0.86, 0.08), (0.86, 0.46), (0.14, 0.46)]), darken(col, 0.08), None, op=0.5)
    d += poly(wp(side, s0, s1, 0, uh, [(0.14, 0.54), (0.86, 0.54), (0.86, 0.92), (0.14, 0.92)]), darken(col, 0.08), None, op=0.5)
    d += wall_ellipse(side, s0, s1, 0, uh, 0.5, 0.74, 0.2, 0.1, "#e8f7ff", 2.0)
    d += wall_ellipse(side, s0, s1, 0, uh, 0.5, 0.74, 0.14, 0.07, "#bfe6ff", 0)
    d += wall_star(side, s0, s1, 0, uh, 0.5, 0.34, 0.2, 0.1, BUTTER, 1.6)
    d += wall_star(side, s0, s1, 0, uh, 0.27, 0.21, 0.09, 0.05, CORAL, 1.2) + wall_star(side, s0, s1, 0, uh, 0.73, 0.22, 0.09, 0.05, "#8fd9c8", 1.2)
    hx = V.wall_lerp(R, side, s0, s1, 0, uh, 0.16 if side > 0 else 0.84, 0.42)
    d += circle(hx[0], hx[1], 3.0 * ((s0 + s1) / 2) ** 0.8, "#d8b24a", OUT, 1.4)
    pn = wp(side, s0, s1, 0, uh, [(0.3, 0.97), (0.7, 0.97), (0.7, 1.05), (0.3, 1.05)])
    return d


def wall_board(side, s0, s1, u0, u1, col="#e6b878"):
    d = poly(V.wall_quad(R, side, s0, s1, u0, u1), "#fbfbff", OUT, 2.4)
    d += poly(wp(side, s0, s1, u0, u1, [(0.06, 0.06), (0.94, 0.06), (0.94, 0.94), (0.06, 0.94)]), col, None)
    rng = random.Random(int(s0 * 100))
    for k, c in enumerate(("#fff4dc", "#ffd0e0", "#cfeee6", "#fff0a8", "#e6dcfa")):
        a, b = 0.12 + (k % 3) * 0.28, 0.14 + (k // 3) * 0.42
        d += poly(wp(side, s0, s1, u0, u1, [(a, b), (a + 0.22, b), (a + 0.22, b + 0.3), (a, b + 0.3)]), c, OUT, 1.0)
    return d


def tea_trolley(x, yb, sc=1.0):
    d = ellipse(x, yb + 2, 48 * sc, 5 * sc, INK, None, op=0.22)
    for sx in (-1, 1):
        d += rect(x + sx * 38 * sc - 2, yb - 62 * sc, 4, 56 * sc, "#b8bcd0", OUT, 1.6)
        d += circle(x + sx * 38 * sc, yb - 4 * sc, 5 * sc, "#6a6a82", OUT, 1.6)
    for yy, h in ((yb - 62 * sc, 5 * sc), (yb - 30 * sc, 5 * sc)):
        d += rect(x - 46 * sc, yy, 92 * sc, h, "#eef0fa", OUT, 2, rx=2)
    d += line((x + 44 * sc, yb - 62 * sc), (x + 56 * sc, yb - 82 * sc), OUT, 4) + line((x + 44 * sc, yb - 62 * sc), (x + 56 * sc, yb - 82 * sc), "#b8bcd0", 2)
    d += line((x + 54 * sc, yb - 82 * sc), (x + 66 * sc, yb - 82 * sc), OUT, 5) + line((x + 54 * sc, yb - 82 * sc), (x + 66 * sc, yb - 82 * sc), "#b8bcd0", 2.4)
    # upper tray: teapot, cups, a cake under a dome
    d += poly([(x - 36 * sc, yb - 62 * sc), (x - 14 * sc, yb - 62 * sc), (x - 16 * sc, yb - 80 * sc), (x - 34 * sc, yb - 80 * sc)], "#ff9ac0", OUT, 1.8)
    d += path(f"M{f(x - 14 * sc)} {f(yb - 76 * sc)} Q{f(x - 6 * sc)} {f(yb - 74 * sc)} {f(x - 15 * sc)} {f(yb - 66 * sc)}", None, OUT, 3) + circle(x - 25 * sc, yb - 83 * sc, 2.4, "#fff4dc", OUT, 1.2)
    for k in range(3):
        d += poly([(x + (2 + k * 12) * sc, yb - 62 * sc), (x + (12 + k * 12) * sc, yb - 62 * sc), (x + (11 + k * 12) * sc, yb - 72 * sc), (x + (3 + k * 12) * sc, yb - 72 * sc)], ["#ffffff", "#ffd966", "#9fd8ff"][k], OUT, 1.4)
    # lower tray: biscuit tin and a stack of paper napkins
    d += rect(x - 30 * sc, yb - 46 * sc, 26 * sc, 16 * sc, "#ffd966", OUT, 1.8, rx=3) + paper_star(x - 17 * sc, yb - 38 * sc, 4.5 * sc, "#ff8f8a", 1.0)
    d += rect(x + 4 * sc, yb - 40 * sc, 24 * sc, 10 * sc, "#ffffff", OUT, 1.6) + rect(x + 8 * sc, yb - 44 * sc, 16 * sc, 4 * sc, "#cfeee6", OUT, 1.2)
    return d


def laundry_trolley(x, yb):
    d = ellipse(x, yb + 2, 40, 5, INK, None, op=0.22)
    for sx in (-1, 1):
        d += circle(x + sx * 30, yb - 4, 4.4, "#6a6a82", OUT, 1.6) + line((x + sx * 30, yb - 8), (x + sx * 30, yb - 30), "#b8bcd0", 3)
    d += poly([(x - 36, yb - 74), (x + 36, yb - 74), (x + 30, yb - 24), (x - 30, yb - 24)], "#9fd8ff", OUT, 2.6)
    for k in range(5):
        d += line((x - 33 + k * 8, yb - 70), (x - 28 + k * 7, yb - 28), "#ffffff", 1.8, 0.5)
    d += rect(x - 38, yb - 78, 76, 7, "#7fb6e8", OUT, 2, rx=3)
    # a stripy shirt, a towel and a paper crown hanging out of the bag
    for k in range(5):
        d += rect(x - 28 + k * 5, yb - 98, 5, 20, "#fffaf0" if k % 2 == 0 else "#2c3f7a", None)
    d += path(f"M{f(x - 30)} {f(yb - 78)} L{f(x - 30)} {f(yb - 98)} Q{f(x - 4)} {f(yb - 108)} {f(x - 2)} {f(yb - 96)} L{f(x - 2)} {f(yb - 78)}", None, OUT, 2.4)
    d += poly([(x + 6, yb - 78), (x + 30, yb - 78), (x + 26, yb - 100), (x + 12, yb - 96)], "#ff9a2e", OUT, 2.0)
    for k in range(3):
        d += line((x + 8 + k * 7, yb - 80), (x + 11 + k * 6, yb - 97), "#fff2c8", 2.2, 0.9)
    d += poly([(x - 8, yb - 78), (x - 6, yb - 90), (x - 2, yb - 83), (x + 2, yb - 92), (x + 5, yb - 78)], "#ffd23f", OUT, 1.4)
    return d


def build_backdrop():
    wall = "#b9e2d6"
    defs, d = M.room_shell(R, wall=wall, dado="#8ccbbb", uidp="c", ceil_tile=True, ceil=("#a8bccb", "#e2edf0"),
                           floor_fn=lambda Rm: V.planks(Rm, HONEY, 9, 0.075, seam="#a07a4a", seed=7))
    # ceiling troffer panels (receding) and a pale cove
    for (xa, xb) in ((560, 720), (490, 530), (750, 790)):
        s = 1.04
        while s < 3.6:
            q = V.ceiling_quad(R, xa, xb, s, s + 0.2)
            d += poly(q, "#f4fffb", OUT, 1.8)
            d += poly([R.ceil(xa + (xb - xa) * 0.1, s + 0.03), R.ceil(xb - (xb - xa) * 0.1, s + 0.03), R.ceil(xb - (xb - xa) * 0.1, s + 0.17), R.ceil(xa + (xb - xa) * 0.1, s + 0.17)], "#ffffff", None, op=0.7)
            s += 0.36 if xb - xa > 100 else 0.5
    # far wall: glazed double doors onto the garden, a banner of hearts and stars, a notice board each side
    fx, fy, fw, fh = 560, 124, 160, 132
    d += rect(fx - 8, fy - 8, fw + 16, fh + 8, "#fbfbff", OUT, 3, rx=3)
    defs += lin_grad("cgl", [(0, "#fffbe8"), (0.6, "#e8f9ff"), (1, "#c8f0d0")], 0, 0, 0, 1)
    for k in range(2):
        x0 = fx + k * (fw / 2)
        d += rect(x0 + 2, fy, fw / 2 - 4, fh, "url(#cgl)", OUT, 2.2)
        d += rect(x0 + 8, fy + 8, fw / 2 - 16, fh * 0.52, "#ffffff", None, op=0.45)
        d += circle(x0 + fw / 4, fy + fh * 0.42, 14, "#bfe6ff", None, op=0.0)
    d += line((fx + fw / 2, fy), (fx + fw / 2, fy + fh), OUT, 3)
    d += rect(fx + 4, fy + fh - 30, fw - 8, 30, "#8fd98a", None, op=0.9)  # garden seen through the glass
    d += ellipse(fx + 34, fy + fh - 30, 20, 11, "#5dbb7a", None) + ellipse(fx + 124, fy + fh - 30, 17, 9, "#6cc98a", None)
    for xx in (fx + fw / 4, fx + fw * 3 / 4):
        d += rect(xx - 4, fy + fh * 0.55, 8, 7, "#d8b24a", OUT, 1.2, rx=2)
    for k in range(7):  # banner
        x = 548 + k * 24
        d += poly([(x - 8, 108), (x + 8, 108), (x, 124)], [CORAL, BUTTER, "#8fd9c8", "#b9a6f0"][k % 4], OUT, 1.4)
    d += line((540, 108), (732, 108), "#6a5a7a", 1.6)
    d += rect(488, 150, 50, 66, "#fbfbff", OUT, 2.4, rx=2) + rect(492, 154, 42, 58, "#e6b878", None)
    for k, c in enumerate(("#fff4dc", "#ffd0e0", "#cfeee6", "#fff0a8")):
        d += rect(496 + (k % 2) * 20, 158 + (k // 2) * 26, 16, 22, c, OUT, 1)
    d += plant(764, 256, 62, "#ff9a7a")
    # way-finding: a GARDEN plaque on the glazed doors and an ART ROOM sign hanging from the ceiling, pointing right
    d += rect(604, 130, 72, 15, "#fff4dc", OUT, 2.0, rx=3) + M.sign_text("GARDEN", 640, 137.5, 8.5, "#3f9a5e", 1.8, outline=None)
    for xx in (586, 694):
        d += line((xx, 50), (xx, 70), "#8a8aa0", 1.6)
    d += rect(566, 68, 148, 24, "#fbfbff", OUT, 2.6, rx=4) + rect(570, 72, 140, 16, "#e6dcfa", None, rx=3)
    d += M.sign_text("ART ROOM", 628, 80, 11, "#7a5ad0", 2.2, outline=None)
    d += poly([(684, 74), (700, 80), (684, 86), (687, 80)], CORAL, OUT, 1.2)
    # side walls: painted doors with paper stars, rail, boards, fire extinguisher
    lefts = [(1.1, 1.38, 0), (1.56, 1.96, 1), (2.2, 2.78, 2), (3.0, 3.8, 3)]
    rights = [(1.22, 1.5, 3), (1.7, 2.12, 4), (2.36, 2.96, 5), (3.2, 4.0, 0)]
    for side, spec in ((-1, lefts), (1, rights)):
        for (s0, s1, ci) in spec:
            d += wall_door(side, s0, s1, DOOR_COLS[ci])
    # boards and pictures between doors (upper wall)
    d += wall_board(-1, 1.42, 1.54, 70, 118) + wall_board(1, 1.54, 1.68, 70, 118) + wall_board(-1, 2.0, 2.16, 74, 124) + wall_board(1, 2.16, 2.34, 74, 124)
    # wooden hand rail along both walls
    for side in (-1, 1):
        d += poly(V.wall_quad(R, side, 1.0, 4.6, 58, 64), WOOD_L, OUT, 2.2)
        d += poly(V.wall_quad(R, side, 1.0, 4.6, 58, 60), WOOD, None, op=0.7)
    # fire extinguisher (red, friendly) and a sanitiser dispenser at the left, nearer the camera
    p0 = R.wall(-1, 2.0, 0)
    d += ellipse(p0[0] + 8, p0[1] + 3, 14, 3, INK, None, op=0.2) + rect(p0[0] + 2, p0[1] - 52, 14, 52, "#ff5a5a", OUT, 2.4, rx=6) + rect(p0[0] + 5, p0[1] - 60, 8, 10, "#3a3a4a", OUT, 1.6, rx=2)
    d += circle(p0[0] + 9, p0[1] - 30, 4, "#fff4dc", OUT, 1.2)
    # the garden-door light spill on the floor
    defs += lin_grad("spillc", [(0, "#fff6d0", 0.6), (1, "#fff6d0", 0.0)], 0, 0, 0, 1)
    d += poly([(570, 256), (710, 256), (790, 330), (490, 330)], "url(#spillc)", None, op=0.6)
    # runner guide line along the corridor floor
    for k in range(14):
        s0 = 1.0 + k * 0.28
        q = [R.floor_pt(628, s0), R.floor_pt(652, s0), R.floor_pt(652, s0 + 0.16), R.floor_pt(628, s0 + 0.16)]
        d += poly(q, "#ff9a8a", None, op=0.75)
    d += tea_trolley(872, 346, 1.0)
    d += laundry_trolley(418, 342)
    d += plant(1190, 394, 130, "#7fb6ff", "rubber")
    d += plant(92, 392, 120, "#ffb07a", "fern")
    return defs, d


def build_front():
    d = ""
    defs = lin_grad("bk", [(0, "#c9b8f0"), (1, "#a994de")], 0, 0, 0, 1)
    defs += lin_grad("pl", [(0, "#a994de"), (1, "#d6cbf5")], 0, 0, 1, 0)
    # lowered bulkhead with hanging paper sign shapes, and the door-frame pillars either side
    d += rect(M.X0, M.Y0, M.X1 - M.X0, 40 - M.Y0, "url(#bk)", OUT, 3.4)
    d += rect(M.X0, 30, M.X1 - M.X0, 7, "#e6dcfa", OUT, 2.4)
    for k in range(9):
        x = 90 + k * 137
        d += line((x, 36), (x, 54), "#6a5a7a", 1.4) + paper_star(x, 62, 9, [BUTTER, CORAL, "#8fd9c8", "#b9a6f0"][k % 4], 1.8)
    d += rect(M.X0, 36, 46 - M.X0, 440, "url(#pl)", OUT, 3.4) + rect(W - 46, 36, M.X1 - W + 46, 440, "url(#pl)", OUT, 3.4)
    for x0 in (-6, W - 46):
        d += rect(x0 + 8, 80, 32, 360, "#ffffff", None, op=0.08) + rect(x0, 36, 52, 12, "#e6dcfa", OUT, 2.4)
    d += rect(0, 360, 46, 8, WOOD_L, OUT, 2) + rect(W - 46, 360, 46, 8, WOOD_L, OUT, 2)  # the rail continues
    return defs, d


def build_pieces():
    out = []
    # 1. ceiling tubes glow (additive): the same troffer quads, a halo each, so they can flicker
    d = ""
    defs = rad_grad("hh", [(0, "#e8fff6", 0.8), (1, "#e8fff6", 0.0)])
    for (xa, xb) in ((560, 720), (490, 530), (750, 790)):
        s = 1.04
        while s < 3.0:
            q = V.ceiling_quad(R, xa, xb, s, s + 0.2)
            cx = sum(p[0] for p in q) / 4
            cy = sum(p[1] for p in q) / 4
            wd = (q[1][0] - q[0][0]) * 2.2 + 30
            d += ellipse(cx, cy + 6, wd / 2, 22, "url(#hh)", None)
            d += poly(q, "#ffffff", None, op=0.85)
            s += 0.36 if xb - xa > 100 else 0.5
    write_svg("views/corridor_tubes.svg", (0, 0, W, 130), d, defs)
    out.append(M.piece("corridor_tubes", "source/views/corridor_tubes.svg", (0, 0), (W, 130), "flicker", "behind", "add", pivot=(640, 40)))
    # 2. the glow of the garden doors at the far end
    w, h = 340, 190
    defs = rad_grad("eg", [(0, "#fffbe0", 0.5), (0.45, "#ffe9b0", 0.18), (1, "#ffe9b0", 0.0)])
    d = ellipse(w / 2, h * 0.62, w / 2, h * 0.5, "url(#eg)", None)
    for k in range(-4, 5):
        d += poly([(w / 2 + k * 6, h * 0.8), (w / 2 + k * 34 - 6, 14 + abs(k) * 8), (w / 2 + k * 34 + 6, 14 + abs(k) * 8)], "#fff6d0", None, op=0.07)
    write_svg("views/corridor_end_glow.svg", (0, 0, w, h), d, defs)
    out.append(M.piece("corridor_end_glow", "source/views/corridor_end_glow.svg", (470, 120), (w, h), "pulse", "behind", "add", pivot=(w / 2, h * 0.62)))
    # 3. a garland of paper stars strung across the corridor
    x0, y0, w, h = 360, 40, 560, 120
    d = ""
    pts_ = [(0, 6 + 34 * (1 - ((k / 40 * 2 - 1) ** 2)) * 0 + 0) for k in range(1)]
    cord = []
    for k in range(41):
        t = k / 40
        cord.append((6 + t * (w - 12), 8 + 30 * 4 * t * (1 - t)))
    d += path("M" + " L".join(f"{f(x)} {f(y)}" for x, y in cord), None, "#6a5a7a", 1.8)
    cols = [BUTTER, CORAL, "#8fd9c8", "#b9a6f0", "#ff9ac0"]
    for k in range(1, 12):
        x, y = cord[int(k / 12 * 40)]
        ln = 10 + (k % 3) * 8
        d += line((x, y), (x, y + ln), "#6a5a7a", 1.2) + paper_star(x, y + ln + 8, 8 + (k % 2) * 2, cols[k % 5], 1.6)
    write_svg("views/corridor_garland.svg", (0, 0, w, h), d)
    out.append(M.piece("star_garland", "source/views/corridor_garland.svg", (x0, y0), (w, h), "sway", "behind", pivot=(w / 2, 4)))
    return out


def build():
    defs, d = build_backdrop()
    write_svg("views/corridor_backdrop.svg", M.BACK_BOX, d, defs)
    defs, d = build_front()
    write_svg("views/corridor_front.svg", M.FRONT_BOX, d, defs)
    pieces = build_pieces()
    pts_ = []
    for (s, xs) in ((1.3, (450, 830)), (1.7, (370, 910)), (2.1, (290, 990)), (2.5, (220, 1060))):
        for x in xs:
            y = R.vy + (R.fy0 - R.vy) * s
            pts_.append([x, round(y + 4)])
    anchors = {
        "floor_rows": R.rows(),
        "floor_polygon": [[R.fx0 + 10, 258], [R.fx1 - 10, 258], [round(R.floor_x(R.fx1, 520)), 520], [round(R.floor_x(R.fx0, 520)), 520]],
        "floor_grid": R.grid(9),
        "light_points": pts_,
        "circle_centre": [640, 376],
        "circle_radii": [230, 42],
        "vanish": [640, 190],
        "doorway": [600, 150, 80, 106],
        "disco_ball": [640, 2],
        "horizon_y": R.vy,
        "wall_left_x": R.fx0, "wall_right_x": R.fx1,
    }
    return {"id": "corridor", "title": "Ward corridor",
            "layers": [M.back_layer("source/views/corridor_backdrop.svg"),
                       M.front_layer("source/views/corridor_front.svg")],
            "anchors": anchors, "pieces": pieces, "palette_hint": "cool"}
