"""Hospital view `cafeteria`: the family lounge. A servery counter with a tea urn and cakes on the far wall, a big coral vending machine on the
left, a tea trolley, café tables and chairs by the walls, tall windows onto the garden on the right and a door back to the corridor,
a coral-and-cream chequered floor with a mint ring for the dance circle, swaying pendant lamps (a piece), tea-urn steam and sun beams.
The camera turns from the corridor into it and turns on towards the garden."""
from __future__ import annotations

import math
import random

from . import hp_props as P
from .hp_props import CORAL, CREAM, GOLD, TEAL, TEAL_D, TEAL_L, WOOD, WOOD_D, WOOD_L
from .hp_views import Room3, stroke_text, view_anchors
from .lib import OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, path, poly, rad_grad, rect, write_svg

W, H = 1280, 720
R = Room3(640, 140, 330, 950, 60, 266)
SE = R.s_edge()
WALL = "#fbe6c8"


def chair(cx, by, sc, col="#e9715b", seat="#ffd98a"):
    """A café chair seen head on, standing on y = by, scale sc (1 = far wall)."""
    s = sc
    o = ""
    for sx in (-1, 1):
        o += line((cx + sx * 12 * s, by - 26 * s), (cx + sx * 13 * s, by), OUT, 5 * s) + line((cx + sx * 12 * s, by - 26 * s), (cx + sx * 13 * s, by), "#8a5a30", 2.6 * s)
    o += rect(cx - 15 * s, by - 52 * s, 30 * s, 24 * s, col, OUT, 2.4 * s, rx=5 * s)  # the back
    o += line((cx - 8 * s, by - 46 * s), (cx + 8 * s, by - 46 * s), "#ffffff", 1.4 * s, 0.6)
    o += rect(cx - 17 * s, by - 30 * s, 34 * s, 8 * s, seat, OUT, 2.4 * s, rx=3 * s)
    return o


def table(cx, by, sc, top="#fff3e0", vase=True, seed=1):
    s = sc
    o = ellipse(cx, by + 2 * s, 30 * s, 7 * s, "#3a1f2e", None, op=0.16)
    o += rect(cx - 3 * s, by - 34 * s, 6 * s, 34 * s, "#8a5a30", OUT, 2 * s)
    o += ellipse(cx, by - 1 * s, 14 * s, 4 * s, "#8a5a30", OUT, 2 * s)
    o += ellipse(cx, by - 38 * s, 36 * s, 11 * s, top, OUT, 2.6 * s)
    o += ellipse(cx, by - 37 * s, 33 * s, 9 * s, None, "#f4a5b4", 1.4 * s, sop=0.9)
    o += ellipse(cx - 12 * s, by - 40 * s, 10 * s, 2.4 * s, "#ffffff", None, op=0.6)
    if vase:
        o += P.bouquet(cx, by - 39 * s, 0.34 * s * 1.6, seed)
    return o


def build_backdrop():
    d, defs = "", ""
    defs += lin_grad("bg", [(0, "#fff6e6"), (1, "#f4dcc0")], 0, 0, 0, 1)
    d += rect(0, 0, W, H, "url(#bg)")
    # ceiling: acoustic tiles, beams
    defs += lin_grad("ce", [(0, "#fffaf0"), (1, "#f4e2c8")], 0, 0, 0, 1)
    d += poly(R.horiz(60, -310, 310, 1.0, SE + 0.3), "url(#ce)")
    for lat in range(-310, 311, 62):
        d += line(R.p(lat, 60, 1.0), R.p(lat, 60, SE + 0.3), "#e2c9a4", 1.2, 0.7)
    for s in (1.25, 1.55, 1.9):
        d += line(R.p(-310, 60, s), R.p(310, 60, s), "#e2c9a4", 1.2, 0.7)
    for lat in (-200, 200):  # wooden beams
        d += poly([R.p(lat - 12, 60, 1.0), R.p(lat + 12, 60, 1.0), R.p(lat + 12, 60, SE + 0.3), R.p(lat - 12, 60, SE + 0.3)], "#d9a066", OUT, 2)
    # far wall: warm wallpaper, mint tiles behind the counter, the shelves and the door
    d += poly(R.quad(-310, 310, 60, 266, 1.0), WALL)
    for x in range(332, 950, 24):
        d += rect(x, 60, 10, 206, "#ffffff", None, op=0.2)
    d += poly(R.quad(-310, 310, 214, 266, 1.0), "#e7a07a")  # coral dado
    d += poly(R.quad(-310, 310, 211, 217, 1.0), "#fff6ea", OUT, 1.4)
    tl = R.quad(-165, 165, 116, 210, 1.0)
    d += poly(tl, "#bfeadf", OUT, 2)
    for k in range(0, 14):
        d += line((tl[0][0] + k * 330 / 13, tl[0][1]), (tl[0][0] + k * 330 / 13, tl[3][1]), "#9fdcd2", 1.2, 0.7)
    for k in range(0, 6):
        d += line((tl[0][0], tl[0][1] + k * 94 / 5), (tl[1][0], tl[0][1] + k * 94 / 5), "#9fdcd2", 1.2, 0.7)
    for yy, items in ((146, "cups"), (176, "jars")):  # shelves with cups and jars
        d += rect(488, yy, 304, 6, WOOD_L, OUT, 2, rx=2)
        for k in range(10):
            x = 504 + k * 29
            if items == "cups":
                d += poly([(x - 7, yy - 11), (x + 7, yy - 11), (x + 5, yy), (x - 5, yy)], [CORAL, "#fff6ea", TEAL_L, "#ffd98a"][k % 4], OUT, 1.4) + path(f"M{x + 7} {yy - 8} q5 1 0 6", None, OUT, 1.4)
            else:
                d += rect(x - 6, yy - 16, 12, 16, ["#ff8f7a", "#ffc65a", "#9fdcd2"][k % 3], OUT, 1.4, rx=3) + rect(x - 7, yy - 19, 14, 4, "#fff6ea", OUT, 1.2, rx=1.5)
    # the menu board (the runtime paints into the dark panel)
    led = (500, 76, 280, 32)
    for xx in (led[0] + 30, led[0] + led[2] - 30):
        d += line((xx, led[1] - 6), (xx, 60), OUT, 3) + line((xx, led[1] - 6), (xx, 60), "#c9b79a", 1.2)
    d += rect(led[0] - 8, led[1] - 7, led[2] + 16, led[3] + 14, "#4fb3a9", OUT, 3.2, rx=6) + rect(led[0] - 3, led[1] - 3, led[2] + 6, led[3] + 6, "#fff6ea", OUT, 1.8, rx=4)
    d += rect(led[0], led[1], led[2], led[3], "#22303a", None)
    # side walls
    d += poly(R.side(-310, 60, 266, 1.0, SE + 0.3), "#f0d1a6") + poly(R.side(310, 60, 266, 1.0, SE + 0.3), "#f4d9b2")
    d += poly(R.side(-310, 214, 266, 1.0, SE + 0.3), "#e7a07a") + poly(R.side(310, 214, 266, 1.0, SE + 0.3), "#e7a07a")
    for sgn in (-1, 1):
        d += poly(R.side(sgn * 310, 210, 216, 1.0, SE + 0.3), "#fff6ea", OUT, 1.6) + poly(R.side(sgn * 310, 258, 266, 1.0, SE + 0.3), "#fff6ea", OUT, 1.6)
    # floor: coral and cream chequered lino with a painted mint ring for the dance circle
    fdefs, fbody = P.tile_floor(R, "fl", c1="#e6c49a", c2="#d48a6c", cell=58, line_c="#b07a56", gloss=0.12)
    defs += fdefs
    d += fbody
    d += ellipse(640, 372, 262, 56, None, "#7fd1c4", 7, sop=0.9) + ellipse(640, 372, 262, 56, None, "#ffffff", 1.6, sop=0.8)
    d += ellipse(640, 372, 236, 48, None, "#ffc65a", 3, sop=0.9)
    # windows on the right wall (onto the garden) and pictures, pinboard and clock on the left wall
    for k, (s0, s1) in enumerate(((1.08, 1.55), (1.75, 2.1))):
        q = R.side(310, 96, 206, s0, s1)
        sx, sy = R.p(310, 130, (s0 + s1) / 2)
        wd, wb = P.window_scene(q, f"rw{k}", sun_xy=(sx, sy), seed=20 + k)
        defs += wd
        d += poly(R.side(310, 90, 212, s0 - 0.03, s1 + 0.03), "#fff6ea", OUT, 2.6)
        d += wb
        sm = (s0 + s1) / 2
        d += line(R.p(310, 96, sm), R.p(310, 206, sm), "#fff6ea", 4) + line(R.p(310, 151, s0), R.p(310, 151, s1), "#fff6ea", 3.4)
        d += poly(R.side(310, 208, 216, s0 - 0.06, s1 + 0.06), "#fff6ea", OUT, 2)
    for k, (s0, s1, kind, col) in enumerate(((1.12, 1.4, "sun", "#ffe9a8"), (1.55, 1.8, "hills", "#cdeee6"), (1.92, 2.06, "flower", "#f8d6e0"))):
        q = R.side(-310, 112, 170, s0, s1)
        d += P.picture(q, col, kind)
    q = R.side(-310, 126, 186, 1.5, 1.9) if False else None
    # the vending machine (far wall, left)
    vm = (344, 126, 96, 140)
    defs += lin_grad("vm", [(0, "#ff9a86"), (1, "#e9715b")], 0, 0, 1, 0)
    d += ellipse(vm[0] + 48, 268, 54, 7, "#3a1f2e", None, op=0.18)
    d += rect(vm[0], vm[1], vm[2], vm[3], "url(#vm)", OUT, 3.4, rx=6)
    d += rect(vm[0] + 7, vm[1] + 8, 62, 100, "#2b4a54", OUT, 2.4, rx=3)
    rng = random.Random(4)
    for r in range(4):
        d += line((vm[0] + 9, vm[1] + 33 + r * 24), (vm[0] + 67, vm[1] + 33 + r * 24), "#9fdcd2", 1.4, 0.8)
        for c in range(4):
            col = rng.choice(["#ffd23f", "#ff8f7a", "#9fdcd2", "#f4a5b4", "#ffffff", "#b9d9a3"])
            d += rect(vm[0] + 12 + c * 14, vm[1] + 15 + r * 24, 10, 17, col, OUT, 1.2, rx=2)
    d += rect(vm[0] + 7, vm[1] + 8, 62, 100, "#ffffff", None, op=0.1, rx=3)
    d += rect(vm[0] + 74, vm[1] + 14, 15, 34, "#fff6ea", OUT, 1.6, rx=2) + circle(vm[0] + 81, vm[1] + 24, 3, TEAL, OUT, 1.2) + rect(vm[0] + 77, vm[1] + 31, 8, 3, "#3a1f2e", None)
    d += rect(vm[0] + 10, vm[1] + 113, 60, 20, "#1a2a30", OUT, 2, rx=3) + P.heart_shape(vm[0] + 82, vm[1] + 120, 5, "#fff6ea", 1.2)
    # the servery counter: tea urn, teapots, a tiered cake stand, cups
    d += R.box(-160, 160, 210, 1.0, 1.3, "#7cc4b8", "#e0a868", "#f6dcae", 2.6)
    topy = R.p(0, 210, 1.15)[1]
    d += rect(R.p(-160, 210, 1.3)[0] + 8, R.p(0, 232, 1.3)[1], 304, 5, "#fff6ea", None, op=0.0)
    for k in range(7):  # glass front panels on the counter
        x0 = R.p(-150 + k * 43, 218, 1.3)[0]
        d += rect(x0, R.p(0, 226, 1.3)[1], 56, 40, "#bfeadf", "#5aa89e", 1.4, rx=2, op=0.55)
    ux = R.p(-110, 210, 1.15)[0]
    d += rect(ux - 14, topy - 48, 28, 46, "#c9d2dc", OUT, 2.4, rx=6) + rect(ux - 11, topy - 42, 8, 34, "#ffffff", None, op=0.5, rx=3) + rect(ux - 5, topy - 54, 10, 7, "#a8b4c0", OUT, 1.6, rx=2)
    d += circle(ux + 15, topy - 22, 3, "#ffd98a", OUT, 1.2) + rect(ux + 12, topy - 20, 8, 4, "#a8b4c0", OUT, 1.2)
    for k, cx in enumerate((R.p(-40, 210, 1.15)[0], R.p(0, 210, 1.15)[0], R.p(40, 210, 1.15)[0])):  # cake stands
        d += rect(cx - 2, topy - 20, 4, 20, "#e8cfa6", OUT, 1.4) + ellipse(cx, topy - 21, 20, 4, "#fff6ea", OUT, 2) + ellipse(cx, topy, 22, 4.4, "#fff6ea", OUT, 2)
        d += path(f"M{cx - 14} {topy - 23} Q{cx} {topy - 44} {cx + 14} {topy - 23} Z", "#e9e0d0", OUT, 1.6, op=0.55)
        for j in range(3):
            d += circle(cx - 9 + j * 9, topy - 25.5, 4.2, ["#ff8f9a", "#ffd98a", "#b9a0f0"][(j + k) % 3], OUT, 1.2)
    for k in range(3):
        px = R.p(70 + k * 26, 210, 1.15)
        d += poly([(px[0] - 6, topy - 12), (px[0] + 6, topy - 12), (px[0] + 4, topy), (px[0] - 4, topy)], [CORAL, TEAL_L, "#ffd98a"][k], OUT, 1.4)
    tp = R.p(125, 210, 1.15)
    d += ellipse(tp[0], topy - 10, 13, 10, "#ffc65a", OUT, 2) + rect(tp[0] - 4, topy - 24, 8, 6, "#e9a83a", OUT, 1.6, rx=2) + path(f"M{tp[0] + 12} {topy - 14} q10 2 3 10", None, OUT, 2.4)
    # the tea trolley (two shelves on wheels) on the right of the counter
    tx, tby = R.p(205, 266, 1.28)
    d += ellipse(tx, tby + 1, 36, 5, "#3a1f2e", None, op=0.16)
    for xx in (tx - 28, tx + 28):
        d += line((xx, tby - 56), (xx, tby - 6), OUT, 5) + line((xx, tby - 56), (xx, tby - 6), "#c9d2dc", 2.4)
        d += circle(xx, tby - 3, 5, "#3a2418", OUT, 1.6)
    for yy in (tby - 56, tby - 28):
        d += rect(tx - 34, yy, 68, 6, "#e0a868", OUT, 2, rx=2)
    d += rect(tx - 26, tby - 50 - 22, 22, 22, "#fff6ea", OUT, 2, rx=6) + path(f"M{tx - 4} {tby - 66} q9 2 2 10", None, OUT, 2.2) + rect(tx - 20, tby - 77, 10, 6, "#ffc65a", OUT, 1.6, rx=2)
    d += ellipse(tx + 12, tby - 56, 16, 5, "#fff6ea", OUT, 1.6) + circle(tx + 6, tby - 62, 4, "#ff8f9a", OUT, 1.2) + circle(tx + 17, tby - 62, 4, "#ffd98a", OUT, 1.2)
    for k in range(3):
        d += rect(tx - 24 + k * 16, tby - 38, 11, 10, [CORAL, TEAL_L, "#ffd98a"][k], OUT, 1.2, rx=2)
    # the door back to the corridor (far wall, right): the doorway anchor
    dx, dy, dw, dh = 860, 146, 62, 120
    d += rect(dx - 6, dy - 6, dw + 12, dh + 6, "#fff6ea", OUT, 3, rx=3) + rect(dx, dy, dw, dh, "#4fb3a9", OUT, 2.4)
    d += circle(dx + dw / 2, dy + 32, 15, "#e8f6f4", OUT, 2.4) + circle(dx + dw / 2, dy + 32, 15, "#ffffff", None, op=0.0)
    d += circle(dx + dw - 9, dy + 70, 3.6, "#ffe27a", OUT, 1.6) + P.heart_shape(dx + dw / 2, dy + 78, 6, "#ff8f9a", 1.6)
    d += P.plant(R.p(262, 266, 1.0)[0] + 4, 266, 50, "fern", "#d9734a", 6)
    # tables and chairs near the walls (far pair, then near pair), standing on their floor rows
    for lat, s in ((-240, 1.27), (240, 1.27), (-292, 1.95), (292, 1.95)):
        cx, by = R.p(lat, 266, s)
        sc = s * 0.62
        sgn = -1 if lat < 0 else 1
        d += chair(cx - sgn * 4, by - 4 * sc, sc, CORAL if lat < 0 else "#7fd1c4", "#ffd98a") if False else ""
        d += chair(cx + 38 * sc, by - 3 * sc, sc * 0.92, "#e9715b" if lat < 0 else "#4fb3a9", "#ffd98a")
        d += table(cx, by, sc, seed=abs(lat))
        d += chair(cx - 38 * sc, by - 3 * sc, sc * 0.92, "#4fb3a9" if lat < 0 else "#e9715b", "#ffd98a")
    # soft window light on the floor and a warm seat of shading
    defs += lin_grad("patch", [(0, "#fff2b8", 0.0), (0.5, "#fff2b8", 0.26), (1, "#fff2b8", 0.06)], 1, 0, 0, 0)
    for (s0, s1) in ((1.1, 1.55), (1.75, 2.1)):
        d += poly([R.p(310, 266, s0), R.p(310, 266, s1), R.p(60, 266, s1 + 0.55), R.p(90, 266, s0 + 0.5)], "url(#patch)")
    gdefs, gbody = P.grade(R, "grade")
    defs += gdefs
    d += gbody
    return write_svg("views/cafeteria_backdrop.svg", (0, 0, W, H), d, defs)


def build_front():
    """Over the crowd: a ceiling bulkhead with the pendant lamps' caps, a foreground table with a teapot (left) and an armchair with a
    cushion beside a lamp (right)."""
    d, defs = "", ""
    defs += lin_grad("bk", [(0, "#fff6ea"), (1, "#e8cfa6")], 0, 0, 0, 1)
    d += rect(-4, -6, W + 8, 20, "url(#bk)", OUT, 3)
    d += line((0, 12), (W, 12), "#c98f55", 3, 0.8)
    # a foreground table (left edge)
    tx, ty = 48, 452
    d += ellipse(tx, ty + 10, 76, 10, "#3a1f2e", None, op=0.2)
    d += rect(tx - 6, ty - 90, 12, 96, "#8a5a30", OUT, 3) + ellipse(tx, ty + 4, 28, 7, "#8a5a30", OUT, 3)
    d += ellipse(tx, ty - 96, 74, 20, "#fff3e0", OUT, 3.4) + ellipse(tx, ty - 95, 68, 16, None, "#f4a5b4", 2, sop=0.9) + ellipse(tx - 22, ty - 100, 22, 4, "#ffffff", None, op=0.6)
    d += ellipse(tx - 10, ty - 108, 17, 12, "#ffc65a", OUT, 2.4) + rect(tx - 15, ty - 128, 10, 8, "#e9a83a", OUT, 1.8, rx=2) + path(f"M{tx + 6} {ty - 116} q13 3 4 14", None, OUT, 3)
    d += P.bouquet(tx + 36, ty - 98, 0.7, 12)
    # the armchair on the right
    ax, ay = 1226, 458
    d += ellipse(ax, ay + 6, 66, 9, "#3a1f2e", None, op=0.2)
    d += path(f"M{ax - 56} {ay - 120} Q{ax - 56} {ay - 150} {ax - 24} {ay - 150} L{ax + 24} {ay - 150} Q{ax + 56} {ay - 150} {ax + 56} {ay - 120} L{ax + 58} {ay - 30} L{ax - 58} {ay - 30} Z", "#4fb3a9", OUT, 3.4)
    d += rect(ax - 70, ay - 86, 28, 62, "#3f9d94", OUT, 3, rx=10) + rect(ax + 42, ay - 86, 28, 62, "#3f9d94", OUT, 3, rx=10)
    d += rect(ax - 50, ay - 62, 100, 34, "#5cc4b8", OUT, 3, rx=8)
    d += poly([(ax - 32, ay - 100), (ax + 6, ay - 106), (ax + 10, ay - 66), (ax - 28, ay - 62)], "#ffc65a", OUT, 2.6) + P.heart_shape(ax - 12, ay - 82, 7, "#ff8f9a", 1.8)
    for xx in (ax - 50, ax + 50):
        d += rect(xx - 4, ay - 30, 8, 26, "#8a5a30", OUT, 2)
    # a lamp
    d += P.lamp_shade(1160, 452, 120, "#ffe9a8")
    return write_svg("views/cafeteria_front.svg", (0, 0, W, 470), d, defs)


def piece_lamps():
    """Four pendant lamps on cords, swaying (their halos are baked in as soft translucent circles)."""
    w, h = 720, 130
    d = ""
    defs = P.glow_defs("lg", "#ffe9a8", 0.55)
    xs = [(80, CORAL, 74), (250, "#7fd1c4", 90), (470, "#ffc65a", 86), (640, "#f4a5b4", 76)]
    for x, col, y in xs:
        d += line((x, 0), (x, y - 20), OUT, 3.4) + line((x, y - 20), (x, 0), "#fff3e0", 1.2)
        d += ellipse(x, y + 12, 48, 34, "url(#lg)")
        d += path(f"M{x - 28} {y + 10} Q{x - 24} {y - 22} {x} {y - 24} Q{x + 24} {y - 22} {x + 28} {y + 10} Z", col, OUT, 2.8)
        d += path(f"M{x - 16} {y - 10} Q{x - 14} {y - 18} {x - 6} {y - 20}", None, "#ffffff", 2.4, sop=0.7)
        d += ellipse(x, y + 10, 28, 5, lighten(col, 0.5), OUT, 2.2) + ellipse(x, y + 12, 15, 2.8, "#fff6c0", None)
        d += circle(x, y - 24, 4, "#ffe27a", OUT, 1.4)
    write_svg("views/cafeteria_lamps.svg", (0, 0, w, h), d, defs)
    return P.piece("cafeteria_lamps", "source/views/cafeteria_lamps.svg", (280, 40), (w, h), "sway", "behind", "mix", pivot=(360, 0))


def piece_steam():
    w, h = 200, 150
    d = ""
    rng = random.Random(15)
    for k in range(3):
        x0 = 60 + k * 36
        pts = [(x0 + math.sin(i * 0.9 + k) * (6 + i * 1.4), 140 - i * 22) for i in range(7)]
        dd = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
        d += path(dd, None, "#ffffff", 13, sop=0.12) + path(dd, None, "#ffffff", 7, sop=0.2) + path(dd, None, "#ffffff", 3, sop=0.35)
    for k in range(12):
        d += circle(rng.uniform(40, 160), rng.uniform(10, 130), rng.uniform(2, 5), "#ffffff", None, op=rng.uniform(0.1, 0.25))
    write_svg("views/cafeteria_steam.svg", (0, 0, w, h), d)
    ux = R.p(-110, 210, 1.15)[0]
    return P.piece("cafeteria_steam", "source/views/cafeteria_steam.svg", (ux - 100 + 6, 56), (w, h), "flicker", "behind", "add", pivot=(100, 148))


def piece_vending():
    w, h = 120, 160
    defs = P.glow_defs("vg", "#9fe8ff", 0.7)
    d = ellipse(40, 66, 56, 70, "url(#vg)")
    for r in range(4):  # shelf lights chasing
        d += rect(8, 36 + r * 24 - 4, 62, 3, "#d8fbff", None, op=0.9)
    d += circle(97, 25, 4, "#7dffc0", None, op=0.9) + circle(97, 25, 8, "#7dffc0", None, op=0.25)
    write_svg("views/cafeteria_vending.svg", (0, 0, w, h), d, defs)
    return P.piece("cafeteria_vending", "source/views/cafeteria_vending.svg", (352, 134), (w, h), "flicker", "behind", "add", pivot=(60, 80))


def piece_sun():
    w, h = 620, 300
    defs = lin_grad("ray", [(0, "#fff0b0", 0.3), (0.6, "#ffe49a", 0.12), (1, "#ffe49a", 0.0)], 1, 0, 0, 1)
    d = ""
    for k, (ya, yb, drop) in enumerate(((20, 66, 180), (90, 136, 200))):
        d += poly([(w + 4, ya), (w + 4, yb), (w - 460 + k * 30, yb + drop), (w - 560 + k * 40, ya + drop - 10)], "url(#ray)")
    rng = random.Random(16)
    for k in range(20):
        d += circle(rng.uniform(60, w - 30), rng.uniform(30, h - 40), rng.uniform(1.2, 2.6), "#fffbe0", None, op=rng.uniform(0.4, 0.9))
    write_svg("views/cafeteria_sun.svg", (0, 0, w, h), d, defs)
    return P.piece("cafeteria_sun", "source/views/cafeteria_sun.svg", (660, 100), (w, h), "pulse", "behind", "add", pivot=(600, 20))


def build():
    build_backdrop()
    build_front()
    pieces = [piece_lamps(), piece_steam(), piece_vending(), piece_sun()]
    anchors = view_anchors(
        R, (640, 190),
        led_screen=[500, 76, 280, 32], doorway=[860, 146, 62, 120],
        light_points=[[240, 28], [420, 24], [1040, 28], [860, 24], [330, 54], [950, 54], [540, 50], [740, 50]],
        disco_ball=[640, 0])
    return {"id": "cafeteria", "title": "Family lounge",
            "layers": [P.room_layer("backdrop", "views/cafeteria_backdrop.svg"),
                       P.room_layer("front_frame", "views/cafeteria_front.svg", 470, "front")],
            "anchors": anchors, "pieces": pieces, "palette_hint": "tea"}
