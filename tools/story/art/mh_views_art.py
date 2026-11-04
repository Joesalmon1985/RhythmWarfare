"""View `art_room`: a bright studio of ash boards splashed with paint, exposed beams and a skylight, a long north-light window, shelves of
jars and a boombox, a clay kiln, easels, a painted-wall gallery and a clothes line of drying paintings (warm cream, peach and sky)."""
from __future__ import annotations

import math
import random

from . import mh_stage as M, mh_views as V
from .lib import OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, poly, rad_grad, rect, write_svg
from .mh_stage import BUTTER, CORAL, INK, LEAF, LILAC, MINT, W, H, WOOD, WOOD_D, WOOD_L, paper_star, plant

R = M.Room(640, 140, 300, 980, 62, 258)
ASH = ["#efe2cc", "#e8d8be", "#f3e8d4", "#e2d2b6"]
PAINTS = ["#ff8f8a", "#ffd966", "#7fb6ff", "#8fd9c8", "#b9a6f0", "#ff9ac0", "#ffb070"]


def wp(side, s0, s1, u0, u1, pts_):
    return [V.wall_lerp(R, side, s0, s1, u0, u1, a, b) for a, b in pts_]


def scribble_painting(side, s0, s1, u0, u1, kind, seed):
    """A child-bright painting pinned on a side wall (paper quad with a simple scene in wall-plane coordinates)."""
    rng = random.Random(seed)
    d = poly(V.wall_quad(R, side, s0, s1, u0, u1), "#fffdf5", OUT, 2.0)
    pad = [(0.08, 0.08), (0.92, 0.08), (0.92, 0.92), (0.08, 0.92)]
    bg = rng.choice(["#cfe9ff", "#ffe0e8", "#fff0b0", "#d8f4e4", "#e6dcfa"])
    d += poly(wp(side, s0, s1, u0, u1, pad), bg, None)
    if kind == "sun":
        pts_ = [(0.5 + math.cos(k * 0.5) * 0.17, 0.35 + math.sin(k * 0.5) * 0.17) for k in range(13)]
        d += poly(wp(side, s0, s1, u0, u1, pts_), "#ffd23f", OUT, 1.0)
        d += poly(wp(side, s0, s1, u0, u1, [(0.08, 0.72), (0.3, 0.55), (0.55, 0.7), (0.8, 0.52), (0.92, 0.66), (0.92, 0.92), (0.08, 0.92)]), "#7fcf8f", None)
    elif kind == "stripes":
        for k in range(5):
            d += poly(wp(side, s0, s1, u0, u1, [(0.1 + k * 0.16, 0.1), (0.2 + k * 0.16, 0.1), (0.2 + k * 0.16, 0.9), (0.1 + k * 0.16, 0.9)]), PAINTS[(k + seed) % 7], None, op=0.9)
    elif kind == "blobs":
        for k in range(5):
            pts_ = [(0.2 + k * 0.14 + math.cos(j * 0.8) * 0.08, 0.3 + (k % 2) * 0.3 + math.sin(j * 0.8) * 0.1) for j in range(8)]
            d += poly(wp(side, s0, s1, u0, u1, pts_), PAINTS[(k * 2 + seed) % 7], None, op=0.9)
    elif kind == "house":
        d += poly(wp(side, s0, s1, u0, u1, [(0.25, 0.9), (0.25, 0.5), (0.5, 0.25), (0.75, 0.5), (0.75, 0.9)]), "#ff8f8a", OUT, 1.0)
        d += poly(wp(side, s0, s1, u0, u1, [(0.44, 0.9), (0.44, 0.65), (0.56, 0.65), (0.56, 0.9)]), "#ffd966", None)
    else:  # smiley
        pts_ = [(0.5 + math.cos(k * 0.5) * 0.28, 0.5 + math.sin(k * 0.5) * 0.28) for k in range(13)]
        d += poly(wp(side, s0, s1, u0, u1, pts_), "#ffd966", OUT, 1.0)
        d += poly(wp(side, s0, s1, u0, u1, [(0.4, 0.4), (0.44, 0.4), (0.44, 0.5), (0.4, 0.5)]), INK, None) + poly(wp(side, s0, s1, u0, u1, [(0.56, 0.4), (0.6, 0.4), (0.6, 0.5), (0.56, 0.5)]), INK, None)
        d += poly(wp(side, s0, s1, u0, u1, [(0.38, 0.6), (0.5, 0.7), (0.62, 0.6), (0.5, 0.66)]), "#c4445a", None)
    for (a, b) in ((0.5, 0.04), ):  # a pin
        p = V.wall_lerp(R, side, s0, s1, u0, u1, a, 0.96)
        d += circle(p[0], p[1], 2.0, CORAL, OUT, 0.8)
    return d


def easel(x, yb, w, h, kind, sc=1.0):
    """A wooden A-frame easel with a canvas on it (frontal), standing on yb."""
    d = ellipse(x, yb + 2, w * 0.7, 4 * sc, INK, None, op=0.2)
    for sx in (-1, 1):
        d += line((x + sx * w * 0.42, yb), (x + sx * w * 0.14, yb - h * 1.05), OUT, 6 * sc) + line((x + sx * w * 0.42, yb), (x + sx * w * 0.14, yb - h * 1.05), WOOD_L, 3.2 * sc)
    d += line((x, yb - h * 0.2), (x, yb - h * 1.12), OUT, 6 * sc) + line((x, yb - h * 0.2), (x, yb - h * 1.12), WOOD, 3.2 * sc)
    d += rect(x - w * 0.55, yb - h * 0.34, w * 1.1, 5 * sc, WOOD, OUT, 2)  # tray
    cx0, cy0, cw, ch = x - w * 0.5, yb - h * 1.0, w, h * 0.66
    d += rect(cx0, cy0, cw, ch, "#fffdf5", OUT, 2.6)
    if kind == "sun":
        d += rect(cx0 + 3, cy0 + 3, cw - 6, ch * 0.62, "#bfe6ff", None) + rect(cx0 + 3, cy0 + 3 + ch * 0.62, cw - 6, ch * 0.38 - 6, "#8fd98a", None)
        d += circle(cx0 + cw * 0.7, cy0 + ch * 0.28, cw * 0.14, "#ffd23f", OUT, 1.4)
        d += poly([(cx0 + cw * 0.15, cy0 + ch * 0.62), (cx0 + cw * 0.38, cy0 + ch * 0.34), (cx0 + cw * 0.6, cy0 + ch * 0.62)], "#b9a6f0", OUT, 1.4)
    elif kind == "abstract":
        for k in range(6):
            d += circle(cx0 + cw * (0.2 + (k % 3) * 0.3), cy0 + ch * (0.3 + (k // 3) * 0.4), cw * 0.13, PAINTS[k], None, op=0.95)
        d += path(f"M{f(cx0 + 4)} {f(cy0 + ch * 0.8)} Q{f(cx0 + cw * 0.5)} {f(cy0 + ch * 0.4)} {f(cx0 + cw - 4)} {f(cy0 + ch * 0.8)}", None, "#ff6f8a", 2.6)
    else:  # a portrait of a very proud banana
        d += rect(cx0 + 3, cy0 + 3, cw - 6, ch - 6, "#ffe0e8", None)
        d += path(f"M{f(cx0 + cw * 0.3)} {f(cy0 + ch * 0.8)} Q{f(cx0 + cw * 0.2)} {f(cy0 + ch * 0.3)} {f(cx0 + cw * 0.7)} {f(cy0 + ch * 0.2)} Q{f(cx0 + cw * 0.5)} {f(cy0 + ch * 0.6)} {f(cx0 + cw * 0.7)} {f(cy0 + ch * 0.85)} Z", "#ffd23f", OUT, 1.4)
        d += circle(cx0 + cw * 0.46, cy0 + ch * 0.5, 1.6, INK) + circle(cx0 + cw * 0.56, cy0 + ch * 0.48, 1.6, INK)
    return d


def kiln(x, yb, w=80):
    h = 96
    d = ellipse(x + w / 2, yb + 2, w * 0.6, 4, INK, None, op=0.22)
    d += rect(x + 6, yb - 12, 8, 12, "#6a5a6a", OUT, 1.6) + rect(x + w - 14, yb - 12, 8, 12, "#6a5a6a", OUT, 1.6)
    d += rect(x, yb - h + 22, w, h - 34, "#c8765a", OUT, 3, rx=4)  # brick-coloured cylinder body
    for k in range(5):
        d += line((x + 2, yb - h + 34 + k * 10), (x + w - 2, yb - h + 34 + k * 10), darken("#c8765a", 0.2), 1.2, 0.6)
    d += path(f"M{x - 4} {yb - h + 24} Q{x + w / 2} {yb - h - 16} {x + w + 4} {yb - h + 24} Z", "#a85a44", OUT, 3)  # the domed lid
    d += rect(x + w / 2 - 6, yb - h - 14, 12, 14, "#8a8a9c", OUT, 2, rx=2)  # chimney
    d += rect(x + 10, yb - 58, 30, 38, "#2a1b2e", OUT, 2.4, rx=3) + rect(x + 14, yb - 54, 22, 30, "#ff9a4a", None, op=0.85, rx=2)  # door with a warm glow
    d += circle(x + w - 22, yb - 50, 5, "#ffd9a0", OUT, 1.8) + circle(x + w - 22, yb - 32, 4, "#9fd8ff", OUT, 1.6) + circle(x + w - 22, yb - 20, 3, CORAL, OUT, 1.4)
    d += rect(x + 4, yb - h + 28, 4, h - 44, "#ffffff", None, op=0.18)
    return d


def build_backdrop():
    defs, d = M.room_shell(R, wall="#fff1de", dado="#ffc9a0", uidp="a", ceil_tile=False,
                           floor_fn=lambda Rm: V.planks(Rm, ASH, 12, 0.08, seam="#b39a78", seed=11))
    # ceiling: wooden beams and a skylight
    sk = V.ceiling_quad(R, 480, 800, 1.12, 1.9)
    defs += lin_grad("sky", [(0, "#a8dcff"), (1, "#eaf8ff")], 0, 0, 0, 1)
    d += poly(sk, "url(#sky)", OUT, 3.4)
    for k in range(1, 4):
        d += line(R.ceil(480 + k * 80, 1.12), R.ceil(480 + k * 80, 1.9), "#fbfbff", 2.4)
    d += line(R.ceil(480, 1.5), R.ceil(800, 1.5), "#fbfbff", 2.4)
    for s0 in (1.0, 1.45, 2.0, 2.6):
        q = V.ceiling_quad(R, 300, 980, s0, s0 + 0.07)
        d += poly(q, WOOD, OUT, 2.4)
        d += poly([q[0], q[1], (q[1][0], q[1][1] + 3), (q[0][0], q[0][1] + 3)], WOOD_D, None, op=0.5)
    # far wall: long north window over a work counter, shelves with jars and a boombox, the kiln
    wd, wdd = M.window(420, 74, 440, 124, "aw", mullions=(3, 1))
    defs += wd
    d += wdd
    d += rect(412, 204, 456, 8, WOOD_L, OUT, 2.4, rx=2) + rect(414, 212, 452, 46, "#ffd9b0", OUT, 2.6)
    for k in range(5):
        d += rect(422 + k * 90, 218, 76, 36, "#ffffff", None, op=0.18, rx=2) + circle(460 + k * 90, 236, 2.6, "#d8b24a", OUT, 1.2)
    # jars of brushes and paint pots on the counter
    for k, x in enumerate((440, 480, 520, 700, 740, 800, 836)):
        c = PAINTS[k % 7]
        d += rect(x - 7, 190, 14, 14, "#fbfbff", OUT, 1.6, rx=2) + rect(x - 5.4, 190.6, 10.8, 5, c, None)
    for x in (600, 628):
        d += rect(x - 9, 182, 18, 22, "#e6dcfa", OUT, 1.8, rx=3)
        for j, c in enumerate(("#ff8f8a", "#5fc9bb", "#ffd966")):
            d += line((x - 4 + j * 4, 183), (x - 6 + j * 5, 168 - j), "#a8743c", 1.4) + line((x - 6 + j * 5, 169 - j), (x - 6 + j * 5, 164 - j), c, 3)
    d += ellipse(668, 200, 18, 6, "#c8765a", OUT, 1.8) + path("M650 200 Q668 180 686 200", "#c8765a", OUT, 1.8)  # a clay pot
    # left shelves with a boombox
    for k, yy in enumerate((110, 168, 224)):
        d += rect(312, yy, 100, 6, WOOD_L, OUT, 2.2, rx=1) + line((322, yy + 6), (322, yy + 14), OUT, 3) + line((402, yy + 6), (402, yy + 14), OUT, 3)
    d += rect(322, 160, 82, 8, "#9a9aaa", OUT, 0.0, op=0.0)
    d += rect(318, 140, 90, 28, "#8a86c8", OUT, 2.6, rx=5) + circle(343, 154, 12.5, "#2a2438", OUT, 2) + circle(383, 154, 12.5, "#2a2438", OUT, 2)
    d += rect(356, 146, 14, 8, "#ffd966", OUT, 1.2, rx=1) + line((372, 140), (386, 124), OUT, 3) + circle(386, 123, 2, CORAL, OUT, 1)
    d += rect(322, 96, 10, 14, "#ff8f8a", OUT, 1.4, rx=2) + rect(336, 92, 12, 18, "#8fd9c8", OUT, 1.4, rx=2) + rect(352, 98, 12, 12, "#ffd966", OUT, 1.4, rx=2) + rect(372, 94, 18, 16, "#b9a6f0", OUT, 1.4, rx=2)
    for k in range(6):
        d += rect(322 + k * 14, 206, 10, 18, PAINTS[k], OUT, 1.2, rx=2)
    d += plant(396, 224, 30, "#ff9a7a")
    d += kiln(886, 258, 80)
    # left wall: a gallery of paintings (nearest are cut by the frame)
    left = [(1.08, 1.3, 90, 140, "sun"), (1.36, 1.6, 82, 132, "stripes"), (1.68, 2.02, 90, 150, "smiley"), (2.1, 2.5, 80, 140, "blobs"), (2.6, 3.1, 96, 160, "house")]
    for k, (s0, s1, u0, u1, kind) in enumerate(left):
        d += scribble_painting(-1, s0, s1, u0, u1, kind, k + 3)
    # right wall: cubby shelves with paint tubs and paper rolls
    for (s0, s1) in ((1.1, 1.5), (1.6, 2.1)):
        d += poly(V.wall_quad(R, 1, s0, s1, 40, 150), "#f0d9b8", OUT, 2.4)
        for j in range(3):
            for i in range(3):
                a0, a1 = i / 3 + 0.04, (i + 1) / 3 - 0.04
                b0, b1 = j / 3 + 0.04, (j + 1) / 3 - 0.04
                d += poly(wp(1, s0, s1, 40, 150, [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]), "#c9a678", OUT, 1.0)
                c = PAINTS[(i * 3 + j) % 7]
                d += poly(wp(1, s0, s1, 40, 150, [(a0 + 0.06, b0 + 0.04), (a1 - 0.06, b0 + 0.04), (a1 - 0.06, b0 + 0.2), (a0 + 0.06, b0 + 0.2)]), c, OUT, 0.8)
    d += poly(V.wall_quad(R, 1, 2.2, 2.9, 20, 118), "#ffffff", None, op=0.0)
    # paint-splashed drop cloth and loose splats on the floor
    cloth = [R.floor_pt(430, 1.55), R.floor_pt(850, 1.55), R.floor_pt(850, 2.55), R.floor_pt(430, 2.55)]
    d += poly(cloth, "#f5ead4", OUT, 2.0, op=0.9)
    rng = random.Random(31)
    for k in range(34):
        a = rng.uniform(0, 1)
        b = rng.uniform(0, 1)
        s = 1.55 + b * 1.0
        x = R.vx + (430 + (850 - 430) * a - R.vx) * s
        y = R.floor_y(s)
        r_ = rng.uniform(3, 10) * s * 0.7
        d += ellipse(x, y, r_ * 1.5, r_ * 0.55, PAINTS[rng.randrange(7)], None, op=0.9)
    for k in range(40):
        s = rng.uniform(1.15, 3.6)
        xf = rng.choice((rng.uniform(300, 430), rng.uniform(850, 980)))
        x = R.vx + (xf - R.vx) * s
        y = R.floor_y(s)
        r_ = rng.uniform(2, 7) * s * 0.6
        d += ellipse(x, y, r_ * 1.4, r_ * 0.5, PAINTS[rng.randrange(7)], None, op=0.85)
    d += easel(150, 384, 70, 82, "abstract") + easel(1136, 378, 66, 78, "banana")
    return defs, d


def build_front():
    defs = lin_grad("beam", [(0, WOOD_L), (1, WOOD)], 0, 0, 0, 1)
    d = rect(-4, -4, W + 8, 22, "url(#beam)", OUT, 3.2)
    d += rect(-4, 14, W + 8, 5, WOOD_D, OUT, 2)
    # a hanging string of paint-pot pendants at either end, and tall shelving posts at the sides
    for x in (60, 1220):
        d += line((x, 18), (x, 70), "#6a5a7a", 1.8)
        d += poly([(x - 22, 112), (x + 22, 112), (x + 14, 72), (x - 14, 72)], "#ffd966", OUT, 2.6) + ellipse(x, 114, 18, 4, "#fff6c0", None, op=0.9)
    # left: a nearby easel edge with a canvas cut by the frame
    d += rect(-10, 130, 64, 86, "#fffdf5", OUT, 3) + rect(-6, 134, 56, 78, "#ffe0e8", None)
    d += circle(18, 168, 16, "#ffd23f", OUT, 1.6) + path("M-6 206 Q20 170 50 206", None, "#7fcf8f", 7)
    d += line((20, 216), (6, 470), OUT, 9) + line((20, 216), (6, 470), WOOD_L, 5) + line((40, 216), (62, 470), OUT, 9) + line((40, 216), (62, 470), WOOD_L, 5)
    # right: a trolley of paint pots and brushes
    d += rect(W - 74, 330, 84, 7, WOOD_L, OUT, 2.4, rx=2) + rect(W - 74, 396, 84, 7, WOOD_L, OUT, 2.4, rx=2)
    for k, c in enumerate(PAINTS[:5]):
        d += rect(W - 66 + k * 15, 308, 12, 22, "#fbfbff", OUT, 1.6, rx=2) + rect(W - 64.6 + k * 15, 309, 9, 8, c, None)
    d += rect(W - 48, 366, 30, 30, "#e6dcfa", OUT, 2, rx=4)
    for k, c in enumerate(("#ff8f8a", "#5fc9bb", "#ffd966", "#b9a6f0")):
        d += line((W - 42 + k * 6, 367), (W - 46 + k * 7, 346), "#a8743c", 1.8) + line((W - 46 + k * 7, 347), (W - 46 + k * 7, 340), c, 3.4)
    d += line((W - 62, 337), (W - 62, 470), OUT, 6) + line((W - 62, 337), (W - 62, 470), "#b8bcd0", 3) + line((W + 2, 337), (W + 2, 470), OUT, 6)
    return defs, d


def build_pieces():
    out = []
    # 1. kiln glow (additive)
    w, h = 150, 150
    defs = rad_grad("kg", [(0, "#ffd09a", 0.95), (0.4, "#ff9a4a", 0.35), (1, "#ff9a4a", 0.0)])
    d = circle(w / 2, h * 0.58, 70, "url(#kg)", None)
    d += rect(w / 2 - 12, h * 0.46, 24, 22, "#ffe6b0", None, op=0.8, rx=3)
    write_svg("views/kiln_glow.svg", (0, 0, w, h), d, defs)
    out.append(M.piece("kiln_glow", "source/views/kiln_glow.svg", (886 + 25 - w / 2, 219 - h * 0.58), (w, h), "flicker", "behind", "add", pivot=(w / 2, h * 0.58)))
    # 2. a clothes line of drying paintings across the room
    x0, y0, w, h = 40, 44, 1200, 140
    d = ""
    cord = [(6 + t * (w - 12), 10 + 26 * 4 * t * (1 - t)) for t in [k / 50 for k in range(51)]]
    d += path("M" + " L".join(f"{f(x)} {f(y)}" for x, y in cord), None, "#6a5a7a", 2.0)
    rng = random.Random(2)
    kinds = ["sun", "stripes", "smiley", "blobs", "house", "sun", "smiley"]
    for k in range(10):
        t = (k + 0.7) / 10.4
        x, y = cord[int(t * 50)]
        pw, ph = rng.choice((34, 40, 46)), rng.choice((44, 52, 60))
        d += rect(x - pw / 2, y + 2, pw, ph, "#fffdf5", OUT, 2.0)
        bg = rng.choice(["#cfe9ff", "#ffe0e8", "#fff0b0", "#d8f4e4", "#e6dcfa"])
        d += rect(x - pw / 2 + 3, y + 5, pw - 6, ph - 6, bg, None)
        kd = kinds[k % 7]
        cx, cy = x, y + 2 + ph / 2
        if kd == "sun":
            d += circle(cx + 4, cy - 6, 8, "#ffd23f", OUT, 1.2) + rect(x - pw / 2 + 3, cy + 8, pw - 6, ph / 2 - 11, "#7fcf8f", None)
        elif kd == "stripes":
            for j in range(4):
                d += rect(x - pw / 2 + 5 + j * 7, y + 7, 5, ph - 10, PAINTS[(j + k) % 7], None, op=0.9)
        elif kd == "smiley":
            d += circle(cx, cy, 11, "#ffd966", OUT, 1.2) + circle(cx - 4, cy - 3, 1.4, INK) + circle(cx + 4, cy - 3, 1.4, INK) + path(f"M{f(cx - 5)} {f(cy + 3)} Q{f(cx)} {f(cy + 8)} {f(cx + 5)} {f(cy + 3)}", None, "#c4445a", 1.6)
        elif kd == "blobs":
            for j in range(4):
                d += circle(cx - 9 + j * 6, cy - 6 + (j % 2) * 12, 6, PAINTS[(j * 2 + k) % 7], None, op=0.9)
        else:
            d += poly([(cx - 10, cy + 12), (cx - 10, cy - 2), (cx, cy - 12), (cx + 10, cy - 2), (cx + 10, cy + 12)], "#ff8f8a", OUT, 1.2)
        for sx in (-1, 1):  # pegs
            d += rect(x + sx * (pw / 2 - 6) - 2, y - 3, 4, 9, "#ffd966", OUT, 1.0, rx=1)
    write_svg("views/art_clothesline.svg", (0, 0, w, h), d)
    out.append(M.piece("hanging_paintings", "source/views/art_clothesline.svg", (x0, y0), (w, h), "sway", "behind", pivot=(w / 2, 8)))
    # 3. the skylight beam falling to the floor (additive)
    w, h = 520, 360
    defs = lin_grad("bm", [(0, "#fff6d8", 0.0), (0.12, "#fff6d8", 0.16), (1, "#fff6d8", 0.0)], 0, 0, 0, 1)
    d = poly([(130, 0), (390, 0), (500, h), (20, h)], "url(#bm)", None)
    d += poly([(190, 0), (330, 0), (400, h), (120, h)], "url(#bm)", None, op=0.7)
    write_svg("views/art_skybeam.svg", (0, 0, w, h), d, defs)
    out.append(M.piece("skylight_beam", "source/views/art_skybeam.svg", (380, 70), (w, h), "pulse", "behind", "add", pivot=(w / 2, 40)))
    return out


def build():
    defs, d = build_backdrop()
    write_svg("views/art_backdrop.svg", (0, 0, W, H), d, defs)
    defs, d = build_front()
    write_svg("views/art_front.svg", (0, 0, W, 470), d, defs)
    pieces = build_pieces()
    pts_ = []
    for (s, xs) in ((1.25, (430, 850)), (1.7, (330, 950)), (2.2, (240, 1040)), (2.7, (150, 1130))):
        y = R.vy + (R.fy0 - R.vy) * s
        for x in xs:
            pts_.append([x, round(y + 4)])
    anchors = {
        "floor_rows": R.rows(),
        "floor_polygon": [[R.fx0 + 10, 260], [R.fx1 - 10, 260], [round(R.floor_x(R.fx1, 520)), 520], [round(R.floor_x(R.fx0, 520)), 520]],
        "floor_grid": R.grid(9),
        "light_points": pts_,
        "woofers": [[343, 154, 12.5], [383, 154, 12.5]],
        "circle_centre": [640, 372],
        "circle_radii": [250, 46],
        "vanish": [640, 200],
        "horizon_y": R.vy,
        "wall_left_x": R.fx0, "wall_right_x": R.fx1,
        "kiln": [926, 258],
    }
    return {"id": "art_room", "title": "Art room",
            "layers": [M.layer("backdrop", "source/views/art_backdrop.svg", (0, 0), (W, H)),
                       M.layer("front_frame", "source/views/art_front.svg", (0, 0), (W, 470), "front")],
            "anchors": anchors, "pieces": pieces, "palette_hint": "warm"}
