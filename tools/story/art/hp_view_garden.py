"""Hospital view `garden`: a sunlit courtyard garden at golden hour. A pale sandstone plaza with a mosaic ring (the dance circle), a tiered
fountain at the back in front of the ward's brick wing with its glass entrance and a WELCOME HOME banner, low garden walls with ivy and roses,
benches and lantern posts, hedges and flower beds, a pergola with leaves and fairy-light bunting overhead (front layer), drifting petals and
a fountain spray (pieces). The camera arrives here from the lounge and turns back to the private room."""
from __future__ import annotations

import math
import random

from . import hp_props as P
from .hp_props import CORAL, CREAM, GOLD, LEAF, LEAF_D, TEAL, TEAL_D, TEAL_L, WOOD, WOOD_D, WOOD_L
from .hp_views import Room3, stroke_text, view_anchors
from .lib import OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, poly, rad_grad, rect, write_svg

W, H = 1280, 720
R = Room3(640, 140, 330, 950, 40, 262)
SE = R.s_edge()
BRICK, BRICK_D = "#e9a78a", "#c97d62"


def tree(cx, by, th, cr, seed, light="#9ccf86", mid="#6fbf6a", dark="#4a9a5a", trunk="#8a5a30"):
    rng = random.Random(seed)
    o = ""
    o += poly([(cx - 12, by), (cx - 7, by - th), (cx + 7, by - th), (cx + 14, by)], trunk, OUT, 3)
    o += line((cx - 3, by - 6), (cx - 1, by - th + 10), "#ffffff", 2, 0.25)
    blobs = []
    for k in range(13):
        a = rng.uniform(0, math.tau)
        rr = rng.uniform(0, cr * 0.62)
        blobs.append((cx + math.cos(a) * rr * 1.2, by - th - cr * 0.55 + math.sin(a) * rr * 0.8, rng.uniform(cr * 0.36, cr * 0.58)))
    for (x, y, r) in blobs:
        o += circle(x, y, r, dark, OUT, 3)
    for (x, y, r) in blobs:
        o += circle(x - r * 0.08, y - r * 0.12, r * 0.86, mid, None)
    for (x, y, r) in blobs[::2]:
        o += circle(x - r * 0.25, y - r * 0.32, r * 0.5, light, None, op=0.9)
    return o


def hedge(x0, x1, by, h, seed, flowers=True):
    rng = random.Random(seed)
    o = ""
    n = max(2, int((x1 - x0) / 26))
    blobs = [(x0 + (k + 0.5) * (x1 - x0) / n, by - h * 0.5 + rng.uniform(-4, 4), h * rng.uniform(0.5, 0.62)) for k in range(n)]
    o += rect(x0, by - h * 0.5, x1 - x0, h * 0.5, "#3f8f52", OUT, 2.4)
    for (x, y, r) in blobs:
        o += circle(x, y, r, "#3f8f52", OUT, 2.6)
    for (x, y, r) in blobs:
        o += circle(x, y - 1, r * 0.86, "#58a85c", None)
    for (x, y, r) in blobs:
        o += circle(x - r * 0.25, y - r * 0.3, r * 0.45, "#86cf80", None, op=0.9)
    if flowers:
        cols = ["#ff8f7a", "#ffd23f", "#f4a5b4", "#ffffff", "#c9b6ec"]
        for k in range(n * 2):
            x = x0 + rng.uniform(4, x1 - x0 - 4)
            y = by - rng.uniform(h * 0.15, h * 0.85)
            o += circle(x, y, rng.uniform(2, 3.4), cols[k % 5], OUT, 0.9)
    return o


def bench(cx, by, sc, col="#c98f55"):
    s = sc
    o = ellipse(cx, by + 2 * s, 38 * s, 5 * s, "#3a1f2e", None, op=0.18)
    for sx in (-1, 1):
        o += rect(cx + sx * 30 * s - 3 * s, by - 28 * s, 6 * s, 28 * s, "#6a4020", OUT, 2 * s)
    for k in range(3):
        o += rect(cx - 40 * s, by - 58 * s + k * 9 * s, 80 * s, 6.4 * s, col, OUT, 2 * s, rx=2 * s)
    o += rect(cx - 42 * s, by - 32 * s, 84 * s, 8 * s, lighten(col, 0.18), OUT, 2.2 * s, rx=2 * s)
    o += rect(cx - 36 * s, by - 24 * s, 72 * s, 4 * s, "#3a1f2e", None, op=0.18)
    return o


def lantern_post(cx, by, h):
    o = ellipse(cx, by + 2, 12, 3, "#3a1f2e", None, op=0.2)
    o += rect(cx - 2.6, by - h, 5.2, h, "#3a3a4a", OUT, 2) + rect(cx - 7, by - 8, 14, 8, "#4a4a5a", OUT, 2, rx=2)
    o += poly([(cx - 10, by - h), (cx + 10, by - h), (cx + 7, by - h - 24), (cx - 7, by - h - 24)], "#fff2b0", OUT, 2.4)
    o += poly([(cx - 12, by - h - 24), (cx + 12, by - h - 24), (cx, by - h - 34)], "#3a3a4a", OUT, 2.2) + circle(cx, by - h - 12, 14, "#ffe27a", None, op=0.28)
    return o


def build_backdrop():
    d, defs = "", ""
    # sky at golden hour
    defs += lin_grad("sky", [(0, "#8fd0f0"), (0.42, "#cfe9f2"), (0.62, "#ffe9c0"), (1, "#ffd19a")], 0, 0, 0, 1)
    d += rect(0, 0, W, 300, "url(#sky)")
    defs += P.glow_defs("sun", "#fff2b0", 0.95)
    d += circle(985, 118, 130, "url(#sun)") + circle(985, 118, 24, "#fff9d8", None)
    rng = random.Random(8)
    for (x, y, w_, h_) in ((140, 62, 150, 22), (310, 44, 110, 16), (520, 36, 160, 20), (760, 72, 130, 18), (1110, 40, 140, 20), (60, 110, 100, 14)):
        d += ellipse(x, y, w_, h_, "#ffffff", None, op=0.85) + ellipse(x + w_ * 0.25, y - h_ * 0.5, w_ * 0.5, h_ * 0.7, "#ffffff", None, op=0.85)
        d += ellipse(x, y + h_ * 0.5, w_ * 0.9, h_ * 0.4, "#ffd9b0", None, op=0.5)
    for (x, y) in ((420, 98), (452, 84), (700, 62), (730, 76)):  # a few birds
        d += path(f"M{x - 8} {y} Q{x - 4} {y - 5} {x} {y} Q{x + 4} {y - 5} {x + 8} {y}", None, "#5a3a4a", 1.8)
    # distant rolling trees
    for k in range(18):
        x = k * 74 - 20 + rng.uniform(-10, 10)
        d += circle(x, 190 + rng.uniform(-10, 8), rng.uniform(44, 64), ["#a8d48e", "#93c880", "#b7dc96"][k % 3], None, op=0.95)
    d += rect(0, 205, W, 60, "#8cc880")
    # the ward's brick wing with its glass entrance, windows, a roof edge and the welcome banner
    bx0, bx1, by0, by1 = 400, 880, 56, 236
    d += rect(bx0, by0, bx1 - bx0, by1 - by0, BRICK, OUT, 3.4)
    for r in range(0, 14):
        y = by0 + 6 + r * 13
        d += line((bx0, y), (bx1, y), BRICK_D, 1.0, 0.5)
        for c in range(0, 32):
            x = bx0 + (c * 15 + (r % 2) * 7.5)
            if x < bx1:
                d += line((x, y), (x, y + 13), BRICK_D, 1.0, 0.4)
    d += rect(bx0 - 8, by0 - 14, bx1 - bx0 + 16, 18, "#fff6ea", OUT, 3, rx=3)
    d += rect(bx0 + 40, by0 - 34, 26, 24, BRICK_D, OUT, 2.4) + rect(bx0 + 36, by0 - 40, 34, 8, "#fff6ea", OUT, 2)
    wcols = [(bx0 + 30 + k * 62) for k in range(7)]
    for r, wy in enumerate((82, 168)):
        for x in wcols:
            if r == 1 and 588 < x + 17 < 692:
                continue
            d += rect(x - 4, wy - 4, 42, 44, "#fff6ea", OUT, 2.4, rx=2)
            d += rect(x, wy, 34, 36, "#ffe9a8", OUT, 1.6) + rect(x, wy, 34, 14, "#cde9f2", None, op=0.65)
            d += line((x + 17, wy), (x + 17, wy + 36), "#fff6ea", 2) + line((x, wy + 18), (x + 34, wy + 18), "#fff6ea", 2)
            curt = ["#f4a5b4", "#9fdcd2", "#ffc65a", "#c9b6ec"][(x // 62 + r) % 4]
            d += poly([(x, wy), (x + 9, wy), (x + 4, wy + 36), (x, wy + 36)], curt, None, op=0.9) + poly([(x + 34, wy), (x + 25, wy), (x + 30, wy + 36), (x + 34, wy + 36)], curt, None, op=0.9)
            d += rect(x - 6, wy + 36, 46, 5, "#fff6ea", OUT, 1.4) + (P.flower(x + 8, wy + 33, 4, "#ff8f7a", "#ffd23f", 5, 0.8) + P.flower(x + 26, wy + 33, 4, "#f4a5b4", "#ffd23f", 5, 0.8) if x % 2 == 0 else "")
    # the entrance: canopy, glass doors and steps
    d += rect(582, 118, 116, 12, "#fff6ea", OUT, 2.6, rx=3) + poly([(572, 118), (708, 118), (700, 104), (580, 104)], "#4fb3a9", OUT, 2.6)
    d += rect(594, 150, 92, 86, "#fff6ea", OUT, 3, rx=3)
    d += rect(600, 156, 80, 80, "#cde9f2", OUT, 1.8) + rect(600, 156, 80, 80, "#ffe9a8", None, op=0.35) + line((640, 156), (640, 236), "#fff6ea", 3.4)
    d += poly([(606, 160), (622, 160), (606, 192)], "#ffffff", None, op=0.55)
    d += circle(632, 200, 2.6, "#ffe27a", OUT, 1.2) + circle(648, 200, 2.6, "#ffe27a", OUT, 1.2)
    # the sign board above the entrance (the runtime paints into the dark panel) and the banner on the roof edge
    led = (556, 128, 168, 20)
    d += rect(led[0] - 5, led[1] - 4, led[2] + 10, led[3] + 8, WOOD_L, OUT, 2.6, rx=4) + rect(led[0], led[1], led[2], led[3], "#22303a", None)
    txt, tw = stroke_text("WELCOME HOME", 0, 0, 13, "#ff6f8f", 2.8, "#5a2f3a", 0.38)
    d += f'<g transform="translate({f(640 - tw / 2)} {f(by0 + 10)})">' + txt + '</g>'
    for k in range(5):
        d += P.heart_shape(bx0 + 24 + k * 108, by0 + 10, 5, [CORAL, "#ffc65a", "#7fd1c4", "#f4a5b4", "#9ab8f0"][k], 1.2)
    # hedges at the back with a gap for the path, flower beds
    d += hedge(330, 584, 262, 46, 3) + hedge(696, 950, 262, 46, 4)
    d += hedge(0, 330, 262, 40, 5, True) + hedge(950, 1280, 262, 40, 6, True)
    # big trees behind the garden walls on both sides
    d += tree(120, 250, 130, 120, 2) + tree(1170, 250, 130, 120, 7, "#a8d48e", "#78c070", "#4a9a5a")
    # the plaza: sandstone paving, grass verges, flower beds, a mosaic ring
    fdefs, fbody = P.paving(R, "fl", stone="#e6c79c", stone2="#d6b085", grout="#a9835a", cell=46, seed=5)
    defs += fdefs
    d += fbody
    for sgn in (-1, 1):  # grass verges along the side walls
        q = R.horiz(262, sgn * 232, sgn * 330, 1.0, SE + 0.9)
        d += poly(q, "#8cc880") + poly(R.horiz(262, sgn * 226, sgn * 232, 1.0, SE + 0.9), "#d9b98a", OUT, 1.4)
        for k in range(26):
            s = 1.0 + k * 0.045
            xx = R.p(sgn * (240 + (k * 37) % 60), 262, s)
            d += line(xx, (xx[0] + 2, xx[1] - 5 * s), "#5aa84a", 1.4, 0.8) + line((xx[0] + 4, xx[1]), (xx[0] + 6, xx[1] - 6 * s), "#6fbf6a", 1.4, 0.8)
        for k in range(8):  # flowers in the verge
            xx = R.p(sgn * (250 + (k * 29) % 56), 262, 1.15 + k * 0.17)
            d += P.flower(xx[0], xx[1] - 3, 3.4 + k * 0.3, [CORAL, "#ffd23f", "#f4a5b4", "#ffffff"][k % 4], "#ffd23f", 5, 0.8)
    ring_c = (640, 372)
    d += ellipse(*ring_c, 268, 58, "#fff6ea", OUT, 2.6, op=0.0)
    for k in range(40):  # a mosaic ring of coloured stones
        a = k * math.tau / 40
        cx_, cy_ = ring_c[0] + math.cos(a) * 258, ring_c[1] + math.sin(a) * 54
        d += ellipse(cx_, cy_, 11, 4.4, [CORAL, "#ffc65a", "#7fd1c4", "#f4a5b4", "#9ab8f0"][k % 5], OUT, 1.2)
    d += ellipse(*ring_c, 240, 49, None, "#b58f62", 1.6, sop=0.6)
    # the garden walls (brick, low, with a stone coping, ivy and roses)
    for sgn in (-1, 1):
        d += poly(R.side(sgn * 310, 200, 262, 1.0, SE + 0.3), "#e9a78a", OUT, 2.4)
        d += poly(R.side(sgn * 310, 194, 201, 1.0, SE + 0.3), "#fff6ea", OUT, 2)
        for u in range(0, 12):
            s = 1.0 / (1.0 - u * 0.075) if u < 10 else None
            if s and s < SE:
                d += line(R.p(sgn * 310, 202, s), R.p(sgn * 310, 262, s), BRICK_D, 1.0, 0.5)
        for yf in (214, 226, 238, 250):
            d += line(R.p(sgn * 310, yf, 1.0), R.p(sgn * 310, yf, SE + 0.3), BRICK_D, 1.0, 0.5)
        rng2 = random.Random(40 + sgn)
        for k in range(16):  # ivy and roses on the wall
            s = rng2.uniform(1.05, SE - 0.1)
            x, y = R.p(sgn * 310, rng2.uniform(200, 250), s)
            d += circle(x, y, 7 * s, ["#4a9a5a", "#58a85c", "#3f8f52"][k % 3], OUT, 1.4)
            if k % 3 == 0:
                d += P.flower(x, y, 4 * s, [CORAL, "#ff6f8f", "#fff3e0"][k % 3], "#ffd23f", 6, 0.8)
    # benches and lantern posts along the plaza edge, a trellis
    for lat, s in ((-212, 1.42), (212, 1.42)):
        cx, by = R.p(lat, 262, s)
        d += bench(cx, by, s * 0.74, "#c98f55" if lat < 0 else "#d9a066")
    for lat, s in ((-262, 1.22), (262, 1.22)):
        cx, by = R.p(lat, 262, s)
        d += lantern_post(cx, by, 70 * s * 0.8)
    # the fountain: a tiered stone fountain in front of the path
    fx, fy = 640, 280
    d += ellipse(fx, fy + 4, 98, 24, "#3a1f2e", None, op=0.18)
    d += ellipse(fx, fy - 2, 92, 24, "#d9c9b0", OUT, 3) + ellipse(fx, fy - 6, 82, 19, "#8fd8e8", OUT, 2) + ellipse(fx, fy - 8, 70, 14, "#bff0f6", None, op=0.9)
    d += rect(fx - 9, fy - 50, 18, 44, "#d9c9b0", OUT, 3, rx=3)
    d += ellipse(fx, fy - 50, 44, 11, "#d9c9b0", OUT, 3) + ellipse(fx, fy - 53, 38, 8, "#8fd8e8", OUT, 1.8)
    d += rect(fx - 6, fy - 86, 12, 34, "#d9c9b0", OUT, 3, rx=3) + ellipse(fx, fy - 86, 22, 6, "#d9c9b0", OUT, 3) + ellipse(fx, fy - 88, 17, 4, "#8fd8e8", None)
    d += path(f"M{fx - 90} {fy - 4} q0 10 4 12", None, "#ffffff", 2, sop=0.5)
    # long golden-hour shadows across the plaza
    d += poly([(150, 266), (260, 266), (180, 430), (40, 430)], "#5a2f3a", None, op=0.09) + poly([(1010, 266), (1120, 266), (1250, 430), (1100, 430)], "#5a2f3a", None, op=0.09)
    # warm golden-hour cast over the whole garden
    defs += lin_grad("gh", [(0, "#ffb870", 0.0), (1, "#ffb870", 0.2)], 1, 0, 0, 0.6)
    d += rect(0, 0, W, 470, "url(#gh)")
    return write_svg("views/garden_backdrop.svg", (0, 0, W, H), d, defs)


def leaf_cluster(cx, cy, r, seed, hang=True):
    rng = random.Random(seed)
    o = ""
    for k in range(int(r / 6)):
        x, y = cx + rng.uniform(-r, r), cy + rng.uniform(-r * 0.5, r * 0.5)
        o += P.leaf(x, y, rng.uniform(40, 140) if hang else rng.uniform(180, 340), rng.uniform(14, 26), rng.uniform(5, 9), ["#4a9a5a", "#6fbf6a", "#86cf80", "#3f8f52"][k % 4], True, 1.6)
    return o


def build_front():
    """Over the crowd: a wooden pergola beam with rafters and hanging vines/leaves at the top, lit flower pots and sunflowers at the lower corners."""
    d, defs = "", ""
    defs += lin_grad("bm", [(0, "#e2b47c"), (1, "#a8703c")], 0, 0, 0, 1)
    d += rect(-4, 8, W + 8, 26, "url(#bm)", OUT, 3.4)
    for k in range(0, 30):
        d += line((k * 46, 10), (k * 46 + 10, 32), "#6a4020", 1.2, 0.35)
    d += rect(380, 48, 520, 10, "url(#bm)", OUT, 2.8, rx=2)
    for x in (380, 520, 640, 760, 900):
        d += rect(x - 4, 34, 8, 16, "#a8703c", OUT, 2)
    for x in (46, 1234):  # corner posts (only their top is in view)
        d += rect(x - 14, 8, 28, 200, "url(#bm)", OUT, 3.4) + line((x - 6, 30), (x - 6, 190), "#fff2d0", 2, 0.35)
    d += leaf_cluster(110, 60, 120, 3) + leaf_cluster(1180, 60, 120, 4) + leaf_cluster(330, 30, 70, 5) + leaf_cluster(960, 30, 70, 6)
    for x, seed in ((20, 7), (1260, 8)):
        d += leaf_cluster(x, 160, 40, seed)
    for k in range(7):  # trailing vines and tiny flowers
        x = 120 + k * 170 if k % 2 else 60 + k * 175
        d += path(f"M{x} 32 q{(-1) ** k * 10} 18 0 36 q{(-1) ** k * -10} 14 0 28", None, "#3f8f52", 2.6) + P.flower(x, 98, 4.2, [CORAL, "#f4a5b4", "#ffffff"][k % 3], "#ffd23f", 5, 1.0)
    # flowers at the foot of the frame: sunflowers and pots
    for x, hgt, seed in ((30, 150, 1), (88, 110, 2)):
        d += P.plant(x, 478, hgt, "bushy", "#d9734a", seed)
    for k, (x, hh) in enumerate(((20, 170), (66, 130))):
        d += line((x, 470), (x, 470 - hh), OUT, 5) + line((x, 470), (x, 470 - hh), "#3f8f52", 2.6)
        d += P.flower(x, 470 - hh, 15, "#ffd23f", "#8a5a30", 12, 1.6)
    for k, (x, hh) in enumerate(((1262, 160), (1214, 120))):
        d += line((x, 470), (x, 470 - hh), OUT, 5) + line((x, 470), (x, 470 - hh), "#3f8f52", 2.6)
        d += P.flower(x, 470 - hh, 15, "#ffd23f", "#8a5a30", 12, 1.6)
    d += P.plant(1196, 478, 90, "bushy", "#4fb3a9", 5)
    return write_svg("views/garden_front.svg", (0, 0, W, 470), d, defs)


def piece_spray():
    w, h = 220, 140
    d = ""
    defs = lin_grad("wt", [(0, "#ffffff", 0.9), (1, "#bff0f6", 0.5)], 0, 0, 0, 1)
    for sgn in (-1, 0, 1):
        pts = [(w / 2 + sgn * t * 52, 120 - (t * (2 - t)) * 78 * (1.0 if sgn == 0 else 0.72)) for t in [i / 10 for i in range(0, 11)]] if sgn != 0 else [(w / 2, 120 - i * 10) for i in range(0, 11)]
        dd = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
        d += path(dd, None, "#ffffff", 7, sop=0.16) + path(dd, None, "#ffffff", 3.4, sop=0.45) + path(dd, None, "#e6fbff", 1.4, sop=0.8)
    rng = random.Random(21)
    for k in range(26):
        d += circle(rng.uniform(40, w - 40), rng.uniform(20, 120), rng.uniform(1, 2.4), "#ffffff", None, op=rng.uniform(0.4, 0.9))
    write_svg("views/garden_spray.svg", (0, 0, w, h), d, defs)
    return P.piece("garden_spray", "source/views/garden_spray.svg", (530, 150), (w, h), "pulse", "behind", "add", pivot=(110, 130))


def piece_sunrays():
    w, h = 760, 380
    defs = lin_grad("ray", [(0, "#fff0b0", 0.34), (0.6, "#ffe49a", 0.12), (1, "#ffe49a", 0.0)], 1, 0, 0, 1)
    d = ""
    for k, (ya, yb, drop) in enumerate(((0, 40, 300), (60, 110, 320), (140, 190, 330))):
        d += poly([(w - 20, ya), (w - 20, yb), (w - 560 + k * 24, yb + drop), (w - 680 + k * 30, ya + drop - 12)], "url(#ray)")
    rng = random.Random(22)
    for k in range(24):
        d += circle(rng.uniform(80, w - 30), rng.uniform(30, h - 40), rng.uniform(1.2, 2.8), "#fffbe0", None, op=rng.uniform(0.4, 0.9))
    write_svg("views/garden_sunrays.svg", (0, 0, w, h), d, defs)
    return P.piece("garden_sunrays", "source/views/garden_sunrays.svg", (520, 70), (w, h), "pulse", "behind", "add", pivot=(w - 40, 10))


def piece_bunting():
    w, h = 1280, 120
    d = ""
    d += P.bunting((0, 70), (420, 62), 24, 14, P.PAPER, 17)
    d += P.bunting((420, 62), (860, 62), 14, 15, P.PAPER[3:] + P.PAPER[:3], 17)
    d += P.bunting((860, 62), (1280, 70), 24, 14, P.PAPER, 17)
    glow = P.glow_defs("fg", "#fff0b0", 0.7)
    for (x0, x1) in ((0, 640), (640, 1280)):
        pass
    write_svg("views/garden_bunting.svg", (0, 0, w, h), d)
    return P.piece("garden_bunting", "source/views/garden_bunting.svg", (0, 56), (w, h), "sway", "front", "mix", pivot=(640, 0))


def piece_petals():
    w, h = 520, 300
    d = ""
    rng = random.Random(23)
    cols = ["#f4a5b4", "#ffd0d8", "#ffffff", "#ffc65a", "#ff8f9a"]
    for k in range(34):
        x, y, a = rng.uniform(10, w - 10), rng.uniform(10, h - 10), rng.uniform(0, 180)
        d += f'<g transform="rotate({f(a)} {f(x)} {f(y)})">' + ellipse(x, y, rng.uniform(3, 5.4), rng.uniform(1.8, 3), cols[k % 5], OUT, 1.0) + "</g>"
    write_svg("views/garden_petals.svg", (0, 0, w, h), d)
    return P.piece("garden_petals", "source/views/garden_petals.svg", (380, 80), (w, h), "bob", "behind", "mix", pivot=(260, 150))


def build():
    build_backdrop()
    build_front()
    pieces = [piece_spray(), piece_sunrays(), piece_bunting(), piece_petals()]
    anchors = view_anchors(
        R, (640, 195),
        led_screen=[556, 128, 168, 20], doorway=[600, 156, 80, 80],
        light_points=[[150, 40], [330, 40], [510, 40], [770, 40], [950, 40], [1130, 40], [450, 62], [830, 62]],
        disco_ball=[640, -62])
    return {"id": "garden", "title": "Courtyard garden",
            "layers": [P.layer("backdrop", "source/views/garden_backdrop.svg", (0, 0), (W, H)),
                       P.layer("front_frame", "source/views/garden_front.svg", (0, 0), (W, 470), "front")],
            "anchors": anchors, "pieces": pieces, "palette_hint": "golden"}
