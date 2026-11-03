"""Extra views of the `mothership` chapter: three more rooms of the same ship, seen from the DJ's eye line (the camera tours the ship).

`gallery` (observation gallery with a vast curved window onto the planet, lounge seating, a long corridor), `reactor` (the reactor ring
chamber: a glowing core, energy pylons, a catwalk grating floor) and `bridge` (banked consoles, a captain's chair on a dais, a huge
viewscreen with a star field), plus `stage.sprites.passage_frame` (a hatch frame the camera steps through). Every room is a 1280 x 720
design-space backdrop in one-point perspective (see `Room`), authored at 2x like the rest, with a front layer (arches, rails, foreground
consoles) that draws over the crowd and 3 authored pieces. Hooked from `mothership_stage.build_stage()`; contract:
tools/story/ART_CONTRACT_VIEWS.md. The room code lives in `views_*` helpers below; the common toolkit is `Room`.
"""
from __future__ import annotations

import math
import random

from .lib import (OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, pivot_in, poly, rad_grad, rect,
                  write_svg)
from .mothership_stage import AMB, CYAN, GREEN, MAG, VIO, glyph, hex_bolt, neon, neon_path, polyhex

W, H = 1280, 720
ROW_YS = (286, 316, 350, 390, 438)  # crowd feet rows (same as the dance deck); only the scale changes with the room's horizon


class Room:
    """One-point perspective. Near-frame coordinates (u, v) live on the plane k = 1 (u across 0..1280, v down); a point at depth factor
    k (1 = near frame, kf = the far wall, smaller = further) lands at vp + (point - vp) * k. The floor is v = b0, the ceiling v = t0,
    the side walls u = 0 and u = 1280."""

    def __init__(self, vp, kf, t0, b0):
        self.vx, self.vy = vp
        self.kf, self.t0, self.b0 = kf, t0, b0

    def p(self, k, u, v):
        return (self.vx + (u - self.vx) * k, self.vy + (v - self.vy) * k)

    def wall(self, u, k0, k1, v0, v1):
        return [self.p(k0, u, v0), self.p(k1, u, v0), self.p(k1, u, v1), self.p(k0, u, v1)]

    def face(self, k, u0, u1, v0, v1):
        return [self.p(k, u0, v0), self.p(k, u1, v0), self.p(k, u1, v1), self.p(k, u0, v1)]

    def plane(self, v, k0, k1, u0, u1):
        return [self.p(k0, u0, v), self.p(k0, u1, v), self.p(k1, u1, v), self.p(k1, u0, v)]

    def ribs(self, n, spacing):
        """depth factors of n + 1 ribs at equal depth steps, the last one is the far wall"""
        return [1.0 / (1.0 + spacing * i) for i in range(n + 1)]

    def box(self, u0, u1, k0, k1, v0, v1, top, front, side, sw=2.2):
        """A solid box (k0 nearer than k1, v0 the top). Returns (svg, faces); draws the side that faces the room's axis, the top (if it is
        below the eye line) and the front."""
        o, faces = "", {}
        if u1 <= self.vx:
            faces["side"] = self.wall(u1, k0, k1, v0, v1)
        elif u0 >= self.vx:
            faces["side"] = self.wall(u0, k0, k1, v0, v1)
        if v0 > self.vy:
            faces["top"] = self.plane(v0, k0, k1, u0, u1)
        faces["front"] = self.face(k0, u0, u1, v0, v1)
        for name, col in (("side", side), ("top", top), ("front", front)):
            if name in faces:
                o += poly(faces[name], col, OUT, sw)
        return o, faces

    def floor_far(self, y):
        """floor-line helper: x of a floor line through x_far at the far wall base (y_far) at row y"""
        return None


def lamp(x, y, r, col, op=0.9) -> str:
    return circle(x, y, r * 2.6, col, None, op=0.1) + circle(x, y, r * 1.6, col, None, op=0.2) + circle(x, y, r, col, OUT, 1.2, op=op) + circle(x - r * .3, y - r * .3, r * .35, "#ffffff", None, op=0.9)


def quad_grad(gid, stops, x1=0, y1=0, x2=0, y2=1):
    return lin_grad(gid, stops, x1, y1, x2, y2)


def floor_anchor(vp, far_y, far_x0, far_x1, y0=266, y1=520):
    vx, vy = vp
    xs = [round(far_x0 + (far_x1 - far_x0) * i / 8) for i in range(9)]
    at = lambda xf, y: round(vx + (xf - vx) * (y - vy) / (far_y - vy))
    poly_ = [[xs[1], y0], [xs[7], y0], [at(xs[7], y1), y1], [at(xs[1], y1), y1]]
    grid = {"vanishing_point": [vx, vy], "far_y": far_y, "far_x": xs,
            "note": "x on the far wall base line; a floor line through far_x at screen row y is at x = vp_x + (far_x - vp_x) * (y - vp_y) / (far_y - vp_y)"}
    return poly_, grid


def floor_rows(vy):
    return [{"y": y, "scale": round((y - vy) / (438 - vy), 3)} for y in ROW_YS]


def rig_plates(points, style="plain") -> str:
    d = ""
    for (mx, my) in points:
        d += polyhex(mx, my - 4, 11)
    return d


def front_edge_frame(side_w=46, top_h=30, col="#2a4aa8", dark="#0a1442", accent=CYAN, accent2=MAG, name="front_frame", seed=1) -> str:
    """Foreground arch frame (a structural rib at the camera): two pillars, a lintel and corner brackets. Returns the SVG body."""
    d = ""
    defs_dummy = ""
    # pillars
    for side in (-1, 1):
        x0 = 0 if side < 0 else W - side_w
        d += rect(x0, -4, side_w, 480, dark, OUT, 3.2)
        xi = side_w if side < 0 else W - side_w
        d += rect(x0 + (3 if side < 0 else side_w - 11), -4, 8, 480, col, None, op=0.85)
        d += line((xi, 30), (xi, 440), accent if side < 0 else accent2, 2.2, 0.9)
        d += line((xi, 30), (xi, 440), "#ffffff", 0.8, 0.5)
        for yy in range(50, 440, 48):
            d += rect(x0 + 8, yy, side_w - 22, 6, "#02040f", None, op=0.7, rx=2) + rect(x0 + 10, yy + 1.5, side_w - 26, 2.4, [CYAN, GREEN, MAG, AMB][(yy // 48) % 4], None, op=0.9)
    # lintel and brackets
    d += rect(-4, -4, W + 8, top_h, dark, OUT, 3.2) + rect(-4, 2, W + 8, 7, col, None, op=0.85)
    d += line((side_w, top_h), (W - side_w, top_h), accent, 2.0, 0.9) + line((side_w, top_h), (W - side_w, top_h), "#ffffff", 0.8, 0.45)
    for side in (-1, 1):
        xo = side_w if side < 0 else W - side_w
        d += poly([(xo, top_h), (xo + side * 56, top_h), (xo, top_h + 56)], dark, OUT, 3)
        d += line((xo + side * 6, top_h + 4), (xo + side * 46, top_h + 4), accent2, 1.6, 0.9) + line((xo + side * 4, top_h + 6), (xo + side * 4, top_h + 44), accent2, 1.6, 0.9)
        d += hex_bolt(xo + side * 14, top_h + 14, 4)
    return d


# =====================================================================================================================
# gallery: the observation gallery
# =====================================================================================================================

G_ROOM = Room((640, 150), 0.3125, -110, 470)
G_LED = (480, 80, 320, 38)
G_WIN_V = (-40, 330)  # window extent on the right wall, near-frame v
G_LIGHTS = [[150, 28], [320, 28], [490, 28], [790, 28], [960, 28], [1130, 28], [430, 52], [850, 52]]
G_PLANET = (1130, 440, 345)  # cx, cy, r in screen px
G_SKY = (840, 0, 1280, 335)  # the window's bounding box (x0, y0, x1, y1)


def g_window_quad():
    R = G_ROOM
    return R.wall(1280, 1.0, R.kf, G_WIN_V[0], G_WIN_V[1])


def build_gallery_backdrop() -> dict:
    R = G_ROOM
    kf = R.kf
    rng = random.Random(311)
    ribs = R.ribs(4, 0.55)
    d, defs = "", ""
    HUL, HUL2 = "#1a1250", "#2c1c7a"
    d += rect(0, 0, W, H, "#050420")
    # ceiling: dark vault with light slots converging on the far end
    defs += lin_grad("ceil", [(0, "#03020f"), (1, "#241a68")], 0, 0, 0, 1)
    d += poly(R.plane(R.t0, 2.2, kf, -3000, 4300), "url(#ceil)")
    for u0, u1, col in ((560, 720, "#ffe9c8"), (230, 290, MAG), (990, 1050, CYAN)):
        d += poly(R.plane(R.t0 + 4, 1.0, kf, u0, u1), col, None, op=0.28 if u0 > 500 else 0.2)
        d += poly(R.plane(R.t0 + 4, 1.0, kf, u0 + (u1 - u0) * .35, u1 - (u1 - u0) * .35), "#ffffff", None, op=0.45)
    # left wall: lacquered hull with booth recesses
    defs += lin_grad("lw", [(0, "#0b0732"), (1, "#2b1d78")], 0, 0, 1, 0)
    d += poly(R.wall(0, 1.0, kf, R.t0, R.b0), "url(#lw)")
    for i in range(4):
        k0, k1 = ribs[i], ribs[i + 1]
        a, b = k0 - (k0 - k1) * 0.14, k1 + (k0 - k1) * 0.14
        q = R.wall(0, a, b, 10, 360)
        d += poly(q, "#07041c", OUT, 2.4)
        # warm back-light in each booth and slim light fins
        d += poly(R.wall(0, a - (a - b) * .04, b + (a - b) * .04, 14, 356), "#ff9a4a", None, op=0.10)
        for t in (0.2, 0.5, 0.8):
            kk = a + (b - a) * t
            d += line(R.p(kk, 0, 40), R.p(kk, 0, 330), AMB, 1.4 * kk + .5, 0.55) + line(R.p(kk, 0, 40), R.p(kk, 0, 330), "#fff1c8", 0.6, 0.6)
        d += poly(R.wall(0, a, b, 345, 358), AMB, None, op=0.6)
        # a round brass porthole high on the panel with a tiny planet
        kc = (a + b) / 2
        cx, cy = R.p(kc, 0, 120)
        d += ellipse(cx, cy, 20 * kc * 0.6, 26 * kc, "#06041a", AMB, 1.6, sop=0.9) + ellipse(cx, cy, 11 * kc * 0.6, 15 * kc, MAG, None, op=0.5)
        d += poly(R.wall(0, k0, k1, 372, 380), MAG, None, op=0.0)
    d += neon(R.p(1.0, 0, 372), R.p(kf, 0, 372), MAG, 2.0, 0.9)
    d += neon(R.p(1.0, 0, 40), R.p(kf, 0, 40), AMB, 1.6, 0.8)
    # right wall: the vast curved window onto the planet
    defs += lin_grad("rw", [(0, "#2b1d78"), (1, "#0b0732")], 0, 0, 1, 0)
    d += poly(R.wall(1280, 1.0, kf, R.t0, R.b0), "url(#rw)")
    wq = g_window_quad()
    defs += clip("wclip", poly(wq))
    sky = rect(*G_SKY[:2], G_SKY[2] - G_SKY[0], G_SKY[3] - G_SKY[1], "#05041e")
    defs += rad_grad("neb1", [(0, VIO, 0.45), (1, VIO, 0.0)]) + rad_grad("neb2", [(0, MAG, 0.3), (1, MAG, 0.0)])
    sky += ellipse(900, 80, 150, 70, "url(#neb1)") + ellipse(1010, 40, 190, 60, "url(#neb2)")
    for _ in range(130):
        x, y = rng.uniform(840, 1280), rng.uniform(0, 300)
        sky += circle(x, y, rng.choice((0.7, 0.9, 1.1, 1.4, 1.8)), rng.choice(("#ffffff", "#cfe9ff", "#ffe7c8", "#ffd0ee")), None, op=rng.choice((0.5, 0.7, 0.9)))
    pcx, pcy, pr = G_PLANET
    defs += rad_grad("planet", [(0, "#ffe0b0"), (0.3, "#ff8ac0"), (0.62, "#8a46d8"), (0.9, "#2a1470"), (1, "#120a40")], 0.28, 0.2, 0.95)
    defs += rad_grad("atmo", [(0.9, CYAN, 0.0), (0.955, "#8affff", 0.55), (1, CYAN, 0.0)])
    defs += clip("pclip", circle(pcx, pcy, pr))
    sky += circle(pcx, pcy, pr * 1.06, "url(#atmo)")
    pl = circle(pcx, pcy, pr, "url(#planet)")
    bands = ""
    for k in range(-5, 6):
        yy = pcy - pr * 0.8 + k * pr * 0.12 + 40
        bands += path(f"M{pcx - pr} {f(yy)} Q{pcx - pr * .2} {f(yy - 18)} {pcx + pr} {f(yy + 28)}", None, ["#ffffff", "#c8a0ff", "#ffb0d8", "#7ad8ff"][k % 4], 9, sop=0.14)
    for _ in range(9):  # storm swirls
        bands += ellipse(rng.uniform(pcx - pr * .8, pcx + pr * .6), rng.uniform(pcy - pr * .8, pcy - pr * .2), rng.uniform(20, 46), rng.uniform(5, 10), "#ffffff", None, op=0.12)
    defs += rad_grad("night", [(0, "#0a0626", 0.8), (0.86, "#0a0626", 0.74), (1, "#0a0626", 0.0)])
    bands += circle(pcx + pr * 0.17, pcy + pr * 0.06, pr * 1.02, "url(#night)")  # the night side: a lit crescent on the sun's side
    for _ in range(70):  # city lights on the night side
        x, y = rng.uniform(pcx - pr * .55, pcx + pr * .5), rng.uniform(pcy - pr * .75, pcy - pr * .25)
        if math.hypot(x - pcx - pr * 0.17, y - pcy - pr * 0.06) < pr * 0.86:
            bands += circle(x, y, rng.choice((0.9, 1.2, 1.6)), rng.choice(("#ffd890", "#ffb0e0", "#a8f0ff")), None, op=0.85)
    pl += group(bands, 'clip-path="url(#pclip)"')
    sky += pl + circle(pcx, pcy, pr, None, "#aef4ff", 2.0, sop=0.5)
    sky += circle(900, 118, 15, "#e8efff", None, op=0.95) + circle(905, 114, 14, "#4a5ab0", None, op=0.35)  # a small moon
    # the sun's glare at the planet's limb
    defs += rad_grad("glare", [(0, "#ffffff", 0.9), (0.25, "#ffe9c8", 0.35), (1, AMB, 0.0)])
    sky += circle(890, 214, 54, "url(#glare)")
    d += group(sky, 'clip-path="url(#wclip)"')
    d += poly(wq, None, OUT, 3.4)
    # window mullions on the ribs, curved header and sill
    for i, k in enumerate(ribs):
        pa, pb = R.p(k, 1280, G_WIN_V[0]), R.p(k, 1280, G_WIN_V[1])
        w_ = 20 * k + 3
        d += line(pa, pb, OUT, w_ + 5) + line(pa, pb, "#3a2a98", w_) + line(pa, pb, "#7a66e8", w_ * .3, 0.6)
    d += neon(R.p(1.0, 1280, G_WIN_V[0] + 6), R.p(kf, 1280, G_WIN_V[0] + 6), CYAN, 2.0, 0.9)
    d += poly(R.wall(1280, 1.0, kf, G_WIN_V[1], G_WIN_V[1] + 26), "#1a1250", OUT, 3)
    d += neon(R.p(1.0, 1280, G_WIN_V[1] + 10), R.p(kf, 1280, G_WIN_V[1] + 10), MAG, 2.0, 0.9)
    # far wall
    fx0, fx1, fy0, fy1 = 440, 840, 69, 250
    defs += lin_grad("fw", [(0, "#2a1c78"), (0.6, "#160e48"), (1, "#0a0630")], 0, 0, 0, 1)
    d += rect(fx0, fy0, fx1 - fx0, fy1 - fy0, "url(#fw)")
    for x in range(fx0 + 8, fx1, 20):
        d += rect(x, fy0, 2, fy1 - fy0, "#04021a", None, op=0.5) + rect(x + 2, fy0, 1, fy1 - fy0, MAG, None, op=0.07)
    # LED screen frame
    lx, ly, lw_, lh = G_LED
    d += rect(lx - 10, ly - 10, lw_ + 20, lh + 20, "#2a1c78", OUT, 3.2, rx=8) + rect(lx - 5, ly - 5, lw_ + 10, lh + 10, "#050420", OUT, 2, rx=4) + rect(lx, ly, lw_, lh, "#04061a")
    d += neon((lx - 10, ly - 10), (lx + lw_ + 10, ly - 10), AMB, 1.2, 0.9) + neon((lx - 10, ly + lh + 10), (lx + lw_ + 10, ly + lh + 10), MAG, 1.2, 0.9)
    for cx_, cy_ in ((lx - 5, ly - 5), (lx + lw_ + 5, ly - 5), (lx - 5, ly + lh + 5), (lx + lw_ + 5, ly + lh + 5)):
        d += hex_bolt(cx_, cy_, 3)
    # the arched door at the end of the corridor: the way ahead
    dx, dy, dw, dh = 588, 142, 104, 108
    defs += lin_grad("door", [(0, "#fff6d8"), (0.5, "#ffc98a"), (1, "#ff8a5a")], 0, 0, 0, 1)
    arch = f"M{dx} {dy + dh} V{dy + 44} A{dw / 2} 44 0 0 1 {dx + dw} {dy + 44} V{dy + dh} Z"
    d += path(f"M{dx - 9} {dy + dh} V{dy + 44} A{dw / 2 + 9} 52 0 0 1 {dx + dw + 9} {dy + 44} V{dy + dh} Z", "#2a1c78", OUT, 3.2)
    d += path(arch, "url(#door)", OUT, 2.4)
    for k in range(4):  # a lit corridor inside: nested frames
        s = 0.2 + k * 0.18
        d += rect(dx + dw / 2 * (1 - s), dy + dh * 0.45 + (dh * 0.55) * (1 - s), dw * s, dh * 0.55 * s, None, "#ffffff", 0.9, sop=0.35)
    d += path(f"M{dx + dw / 2} {dy + 8} V{dy + dh}", None, OUT, 2.2)
    d += neon_path(f"M{dx - 9} {dy + 44} A{dw / 2 + 9} 52 0 0 1 {dx + dw + 9} {dy + 44}", AMB, 1.6, 1.0)
    d += glyph(640, 128, 10, AMB, 4) + glyph(612, 128, 6, MAG, 6) + glyph(668, 128, 6, MAG, 8)
    # bar on the left of the door: counter, a wall of glowing vials
    bx0, bx1 = 452, 576
    defs += lin_grad("shelf", [(0, MAG, 0.38), (1, VIO, 0.06)], 0, 0, 0, 1)
    d += rect(bx0, 132, bx1 - bx0, 118, "#04021a", OUT, 2.2, rx=5) + rect(bx0 + 2, 134, bx1 - bx0 - 4, 96, "url(#shelf)", rx=4)
    cols = [GREEN, CYAN, MAG, AMB, VIO]
    for sy in (166, 200):
        d += rect(bx0 - 1, sy, bx1 - bx0 + 2, 4, "#6a58d8", OUT, 1.5)
        x = bx0 + 6
        while x < bx1 - 12:
            c = rng.choice(cols)
            bh, bw = rng.choice((14, 18, 22)), rng.choice((7, 8, 10))
            d += path(f"M{x} {sy} V{sy - bh + 4} Q{x} {sy - bh} {x + bw / 2} {sy - bh} Q{x + bw} {sy - bh} {x + bw} {sy - bh + 4} V{sy} Z", c, OUT, 1.2, op=0.9)
            d += line((x + 2, sy - bh + 5), (x + 2, sy - 3), "#ffffff", 1.0, 0.5)
            x += bw + rng.choice((3, 4, 6))
    d += rect(bx0 - 6, 218, bx1 - bx0 + 12, 32, "#1a1250", OUT, 3) + rect(bx0 - 6, 218, bx1 - bx0 + 12, 6, "#6a58d8", OUT, 2) + neon((bx0, 246), (bx1, 246), MAG, 1.4, 0.9)
    # planters on the right of the door: glowing alien plants in tall pots
    for px in (722, 760, 800):
        d += path(f"M{px - 11} 250 L{px - 8} 222 H{px + 8} L{px + 11} 250 Z", "#2a1c78", OUT, 2) + line((px - 9, 232), (px + 9, 232), AMB, 1.4, 0.9)
        for a in range(-2, 3):
            ex, ey = px + a * 9, 164 + abs(a) * 10 + (px % 7)
            d += path(f"M{px} 222 Q{px + a * 4} {(222 + ey) / 2} {ex} {ey}", None, OUT, 4.6) + path(f"M{px} 222 Q{px + a * 4} {(222 + ey) / 2} {ex} {ey}", None, [GREEN, CYAN, MAG][(a + px) % 3], 2.4)
            d += circle(ex, ey, 4.6, [AMB, MAG, GREEN][(a + 2) % 3], OUT, 1.2, op=0.95)
    # --- floor: polished plating, long light lanes and cross seams
    defs += lin_grad("fl", [(0, "#241a68"), (0.4, "#120c44"), (1, "#070420")], 0, 0, 0, 1)
    d += poly(R.plane(R.b0, 2.2, kf, -3000, 4300), "url(#fl)")
    defs += clip("floorclip", poly(R.plane(R.b0, 2.2, kf, -3000, 4300)))
    fl = ""
    ds = [1.0 / kf - i * 0.2 for i in range(0, 14)]
    for u in range(-1280, 2561, 160):
        a, b = R.p(2.2, u, R.b0), R.p(kf, u, R.b0)
        lane = u in (480, 800)
        fl += line(a, b, CYAN if lane else "#8a78f0", 2.4 if lane else 1.6, 0.6 if lane else 0.45)
    for dd in ds:
        k = 1.0 / dd
        if k > 2.2:
            continue
        fl += line(R.p(k, -1280, R.b0), R.p(k, 2560, R.b0), "#8a78f0", max(0.9, 2.4 * k), 0.45)
    # window light spilling on the floor from the right, and a soft pink on the left from the booths
    defs += lin_grad("spill", [(0, MAG, 0.0), (0.7, MAG, 0.16), (1, "#ffb0e0", 0.36)], 0, 0, 1, 0)
    fl += poly([(840, 250), (1280, 470), (1280, 720), (520, 720), (700, 250)], "url(#spill)")
    defs += lin_grad("spillL", [(0, AMB, 0.22), (1, AMB, 0.0)], 0, 0, 1, 0)
    fl += poly([(440, 250), (0, 470), (0, 720), (400, 720), (600, 250)], "url(#spillL)")
    # the amber arch reflected in the polished floor, and the window's mullions as dark bars in the pink spill
    defs += lin_grad("archrefl", [(0, "#ffd9a0", 0.45), (0.4, AMB, 0.16), (1, AMB, 0.0)], 0, 0, 0, 1)
    fl += poly([(596, 251), (684, 251), (740, 470), (540, 470)], "url(#archrefl)")
    for i, k in enumerate(ribs[1:], 1):
        pa, pb = R.p(k, 1280, R.b0), R.p(k * 0.93, 1280 - 300 * k, R.b0)
        fl += line(pa, (pa[0] - 260 * k, pa[1] + 2), "#1a0a40", 14 * k + 2, 0.25)
    d += group(fl, 'clip-path="url(#floorclip)"')
    # the dance circle: a lounge carpet ring
    cx_c, cy_c, rx_c, ry_c = 640, 372, 250, 46
    defs += rad_grad("ringglow", [(0, "#ffb0e0", 0.3), (0.7, MAG, 0.13), (1, MAG, 0.0)])
    d += ellipse(cx_c, cy_c, rx_c + 44, ry_c + 28, "url(#ringglow)")
    d += ellipse(cx_c, cy_c, rx_c, ry_c, "#1a1050", None, op=0.35) + ellipse(cx_c, cy_c, rx_c, ry_c, None, MAG, 4, sop=0.12) + ellipse(cx_c, cy_c, rx_c, ry_c, None, "#ffc0ea", 1.6, sop=0.85)
    d += ellipse(cx_c, cy_c, rx_c * .74, ry_c * .74, None, AMB, 1.2, sop=0.6) + ellipse(cx_c, cy_c, rx_c * .46, ry_c * .46, None, CYAN, 1.2, sop=0.5)
    for a in range(24):
        t = a * math.tau / 24
        d += circle(cx_c + rx_c * math.cos(t), cy_c + ry_c * math.sin(t), 2.0, "#ffffff", None, op=0.85)
    # floor edge lights at the wall bases
    d += neon(R.p(2.2, 0, R.b0), R.p(kf, 0, R.b0), AMB, 2.0, 0.9) + neon(R.p(2.2, 1280, R.b0), R.p(kf, 1280, R.b0), CYAN, 2.0, 0.9)
    # --- ribs: structural arches
    for i, k in enumerate(ribs[:-1]):
        a, b, c, e = R.p(k, 0, R.b0), R.p(k, 0, R.t0), R.p(k, 1280, R.t0), R.p(k, 1280, R.b0)
        dd_ = f"M{f(a[0])} {f(a[1])} L{f(b[0])} {f(b[1])} L{f(c[0])} {f(c[1])} L{f(e[0])} {f(e[1])}"
        w_ = 26 * k
        d += path(dd_, None, OUT, w_ + 6) + path(dd_, None, HUL2, w_) + path(dd_, None, "#6a58d8", w_ * 0.26, sop=0.6)
        if i > 0:
            d += neon_path(f"M{f(R.p(k, 0, 380)[0])} {f(R.p(k, 0, 380)[1])} L{f(R.p(k, 0, R.t0 + 20)[0])} {f(R.p(k, 0, R.t0 + 20)[1])} L{f(R.p(k, 1280, R.t0 + 20)[0])} {f(R.p(k, 1280, R.t0 + 20)[1])}", MAG if i % 2 else CYAN, 1.2, 0.8)
    # pendant orbs on cables
    for k in ribs[1:4]:
        for u in (430, 850):
            top, bot = R.p(k, u, R.t0), R.p(k, u, 40)
            d += line(top, bot, OUT, 2.4 * k + 1.2) + line(top, bot, "#a08af0", 1.0)
            d += circle(bot[0], bot[1] + 8 * k, 16 * k, "#fff1d0", OUT, 1.6) + circle(bot[0], bot[1] + 8 * k, 28 * k, AMB, None, op=0.18) + circle(bot[0] - 4 * k, bot[1] + 3 * k, 4 * k, "#ffffff", None, op=0.9)
    # --- lounge seating: sofas and low tables along the left wall, a long bench under the window
    cush, back = "#8a2ca0", "#5a1c78"
    sofa_spans = [(1, 2), (2, 3)]
    for i, (a, b) in enumerate([(0, 1), (1, 2), (2, 3)]):
        k0, k1 = ribs[a] - (ribs[a] - ribs[a + 1]) * 0.1, ribs[a + 1] + (ribs[a] - ribs[a + 1]) * 0.12
        o, fc = R.box(24, 52, k0, k1, 330, 470, mix(back, "#ffffff", .15), back, darken(back, .4))
        o2, fc2 = R.box(52, 176, k0, k1, 408, 470, lighten(cush, .25), cush, darken(cush, .35))
        d += o + o2
        for t in (1 / 3, 2 / 3):  # three seat cushions, tufted backrest buttons and two pillows per sofa
            kk = k0 + (k1 - k0) * t
            d += line(R.p(kk, 52, 408), R.p(kk, 176, 408), darken(cush, 0.45), max(1.0, 2.2 * kk), 0.8)
            d += line(R.p(kk, 52, 340), R.p(kk, 52, 404), darken(back, 0.4), max(1.0, 1.8 * kk), 0.7)
        for t in (0.17, 0.5, 0.83):
            kk = k0 + (k1 - k0) * t
            for vv in (356, 384):
                bp = R.p(kk, 52, vv)
                d += circle(bp[0], bp[1], max(0.8, 1.8 * kk), lighten(back, 0.35), None, op=0.8)
        for t, pc in ((0.2, AMB), (0.62, "#ff6fd0")):
            ka, kb = k0 + (k1 - k0) * t, k0 + (k1 - k0) * (t + 0.22)
            q = [R.p(ka, 54, 372), R.p(kb, 54, 376), R.p(kb, 58, 408), R.p(ka, 58, 408)]
            d += poly(q, pc, OUT, max(1.2, 2.0 * ka), op=0.95) + line(q[0], q[1], "#ffffff", max(0.8, 1.6 * ka), 0.5)
        d += line(fc2["front"][0], fc2["front"][1], "#ffd0f0", 1.4, 0.6)
        q = fc2["front"]
        d += line((q[3][0], q[3][1] + 3 * k0), (q[2][0], q[2][1] + 3 * k0), AMB, 2.0, 0.9)  # under-glow
        kt = (k0 + k1) / 2
        tx, ty = R.p(kt, 300, 440)  # a round table
        r_ = 36 * kt
        d += line((tx, ty), (tx, R.p(kt, 300, 470)[1]), OUT, 5 * kt + 1) + line((tx, ty), (tx, R.p(kt, 300, 470)[1]), "#6a58d8", 3 * kt)
        d += ellipse(tx, R.p(kt, 300, 470)[1], r_ * .8, r_ * .18, AMB, None, op=0.3)
        d += ellipse(tx, ty, r_, r_ * .28, "#2a1c78", OUT, 2) + ellipse(tx, ty - 1, r_ * .8, r_ * .2, "#ffd9f2", None, op=0.55) + circle(tx, ty - 7 * kt, 5 * kt, GREEN, None, op=0.9)
    for i in range(4):
        k0, k1 = ribs[i] - (ribs[i] - ribs[i + 1]) * 0.06, ribs[i + 1] + (ribs[i] - ribs[i + 1]) * 0.18
        o, fc = R.box(1110, 1280, k0, k1, 418, 470, lighten("#7a3ad8", .2), "#5a2cb8", "#2a1470")
        d += o + line(fc["front"][3], fc["front"][2], CYAN, 1.8 * k0 + 0.5, 0.9)
        for t in (0.5,):
            kk = k0 + (k1 - k0) * t
            d += line(R.p(kk, 1110, 418), R.p(kk, 1280, 418), "#2a1470", max(1.0, 2.2 * kk), 0.8)
        d += line(R.p(k0, 1112, 419), R.p(k1, 1112, 419), "#d8c0ff", max(0.8, 1.6 * k0), 0.6)  # piping catching the window light
    # light rig and mount plates
    d += poly([(60, 0), (1220, 0), (1220, 8), (60, 8)], "#2a1c78", OUT, 2)
    for xx in (140, 640, 1140):
        d += line((xx, 8), (xx, 18), OUT, 4) + line((xx, 8), (xx, 18), "#6a58d8", 1.6)
    d += neon((70, 12), (1210, 12), MAG, 1.2, 0.8)
    d += rig_plates(G_LIGHTS)
    return write_svg("views/gallery_backdrop.svg", (0, 0, W, H), d, defs)


def build_gallery_front() -> dict:
    d = front_edge_frame(48, 28, "#4a38c0", "#120c44", AMB, MAG)
    d += neon((48, 28), (48, 200), AMB, 1.2, 0.0)
    return write_svg("views/gallery_front.svg", (0, 0, W, 480), d)


def piece(pid, rel, box, anim, z, pivot_xy, blend=None, body="", defs="") -> dict:
    """Write a piece SVG whose viewBox is `box` (absolute design coordinates, so pos = box origin) and return its manifest entry."""
    info = write_svg(rel, box, body, defs)
    e = {"id": pid, "file": "source/" + rel, "pos": [info["x0"], info["y0"]], "size": [info["w"], info["h"]], "px_scale": 0.5,
         "pivot": pivot_in(info, pivot_xy), "anim": anim, "z": z}
    if blend:
        e["blend"] = blend
    return e


def gallery_pieces() -> list:
    out = []
    # the planet's shine: a bright limb glow and aurora ribbons inside the window (additive)
    pcx, pcy, pr = G_PLANET
    defs = rad_grad("g1", [(0, "#ffffff", 0.0), (0.82, "#ffffff", 0.0), (0.93, "#aef4ff", 0.34), (1, CYAN, 0.0)], 0.5, 0.5, 0.5)
    defs += rad_grad("g2", [(0, "#ffffff", 0.6), (0.3, "#ffd9a8", 0.28), (1, AMB, 0.0)])
    d = circle(pcx, pcy, pr * 1.08, "url(#g1)") + circle(890, 214, 70, "url(#g2)")
    for k, col in enumerate((GREEN, CYAN, MAG)):
        dd_ = f"M{960 + k * 8} {170 + k * 9} Q{1060} {96 + k * 12} {1220 - k * 10} {160 + k * 8}"
        d += path(dd_, None, col, 6 - k, sop=0.3) + path(dd_, None, "#ffffff", 1.2, sop=0.4)
    out.append(piece("gallery_planet_shine", "views/gallery_planet_shine.svg", (840, 0, 1280, 335), "pulse", "behind", (pcx, pcy), "add", d, defs))
    # a cruiser gliding past outside the window
    w, h = 96, 34
    defs = lin_grad("hu", [(0, "#e8eeff"), (0.5, "#8aa0f0"), (1, "#3a3a9a")], 0, 0, 0, 1)
    d = path("M4 18 L28 10 L70 8 L92 16 L70 26 L28 26 Z", "url(#hu)", OUT, 2.4) + path("M30 10 L40 3 L60 3 L66 8", "#c8d8ff", OUT, 2)
    for k in range(5):
        d += circle(36 + k * 9, 17, 1.8, [AMB, CYAN, MAG][k % 3], None, op=0.95)
    d += path("M4 18 L-8 14 L-8 22 Z", GREEN, None, op=0.8) + ellipse(-6, 18, 14, 4, GREEN, None, op=0.25) + line((34, 11), (62, 11), "#ffffff", 1.2, 0.6)
    d = group(d, f'transform="translate(912 108)"')
    out.append(piece("gallery_cruiser", "views/gallery_cruiser.svg", (892, 100, 1020, 150), "bob", "behind", (960, 125), None, d, defs))
    # the bar's holographic menu: a flickering floating board with glyph lines
    w, h = 124, 62
    defs = lin_grad("hm", [(0, CYAN, 0.1), (1, MAG, 0.3)], 0, 0, 0, 1)
    d = rect(4, 4, w - 8, h - 8, "url(#hm)", CYAN, 1.6, rx=6, sop=0.9)
    for k in range(4):
        d += glyph(18 + k * 6, 20, 5, [CYAN, GREEN, AMB, MAG][k], 50 + k, 0.9) + line((60, 16 + k * 10), (60 + 40 - k * 8, 16 + k * 10), "#ffffff", 1.6, 0.7)
    d += line((8, h - 8), (w - 8, h - 8), "#ffffff", 1.0, 0.7)
    d = group(d, 'transform="translate(454 92)"')
    out.append(piece("gallery_holo_menu", "views/gallery_holo_menu.svg", (454, 92, 454 + w, 92 + h), "flicker", "behind", (454 + w / 2, 92 + h / 2), "add", d, defs))
    return out


def gallery_view() -> dict:
    build_gallery_backdrop()
    build_gallery_front()
    plygon, grid = floor_anchor((640, 150), 250, 460, 820)
    anchors = {
        "floor_rows": floor_rows(150), "floor_polygon": plygon, "floor_grid": grid, "light_points": G_LIGHTS,
        "led_screen": list(G_LED), "circle_centre": [640, 372], "circle_radii": [250, 46], "horizon_y": 150, "vanish": [640, 150],
        "disco_ball": [640, 0], "wall_left_x": 440, "wall_right_x": 840,
        "doorway": [588, 142, 104, 108],  # the amber arch: guests arrive and gather here
        "window": [840, -40, 440, 370], "planet": list(G_PLANET), "bar": [446, 132, 130, 118],
    }
    return {"id": "gallery", "title": "Observation gallery",
            "layers": [{"id": "backdrop", "file": "source/views/gallery_backdrop.svg", "pos": [0, 0], "size": [W, H], "px_scale": 0.5},
                       {"id": "front_frame", "file": "source/views/gallery_front.svg", "pos": [0, 0], "size": [W, 480], "px_scale": 0.5, "z": "front"}],
            "anchors": anchors, "pieces": gallery_pieces(), "palette_hint": "violet"}


def _octa(cx, cy, hw, hh, c):
    return [(cx - hw + c, cy - hh), (cx + hw - c, cy - hh), (cx + hw, cy - hh + c), (cx + hw, cy + hh - c), (cx + hw - c, cy + hh), (cx - hw + c, cy + hh),
            (cx - hw, cy + hh - c), (cx - hw, cy - hh + c)]


def _ring(outer, inner, fill, stroke=OUT, sw=2.4, op=None) -> str:
    """the area between two polygons (even-odd), the inner one stays open"""
    dd = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in outer) + " Z M" + " L".join(f"{f(x)} {f(y)}" for x, y in inner) + " Z"
    return path(dd, fill, stroke, sw, op=op, extra='fill-rule="evenodd"')


def passage_frame() -> dict:
    """A bulkhead hatch frame to step through: authored 640 x 360 design px (a 1280 x 720 texture), centre pivot, scaled 2x by the runtime it
    covers the 1280 x 720 frame; the octagonal opening in the middle is transparent (so is nothing else: the plating reaches the corners)."""
    fw, fh = 640, 360
    cx, cy = 320, 180
    hole = _octa(cx, cy, 180, 100, 36)
    defs = lin_grad("pl", [(0, "#3a5cb8"), (0.5, "#1c3478"), (1, "#0a1442")], 0, 0, 1, 1)
    defs += lin_grad("pl2", [(0, "#14226a"), (1, "#050b24")], 0, 0, 0, 1)
    defs += lin_grad("bevel", [(0, "#7a96e8"), (1, "#1c3478")], 0, 0, 1, 1)
    # base plating with panel seams and rivets
    d = _ring([(0, 0), (fw, 0), (fw, fh), (0, fh)], hole, "url(#pl)", None, 0)
    for (x, y) in ((i * 64, j * 60) for i in range(11) for j in range(7)):
        if 0 < x < fw and 0 < y < fh and not (abs(x - cx) < 238 and abs(y - cy) < 148):
            d += circle(x, y, 2.2, "#8aa6ff", OUT, 0.8, op=0.85)
    for x in (32, 96, 544, 608):
        d += line((x, 0), (x, fh), OUT, 1.6, 0.45) + line((x + 1.6, 0), (x + 1.6, fh), CYAN, 0.8, 0.12)
    for y in (30, 330):
        d += line((0, y), (fw, y), OUT, 1.6, 0.45)
    # radial perspective seams from the opening to the corners
    for (hx, hy), (ex, ey) in zip((hole[0], hole[1], hole[4], hole[5]), ((0, 0), (fw, 0), (fw, fh), (0, fh))):
        d += line((hx, hy), (ex, ey), OUT, 2.4, 0.55) + line((hx, hy), (ex, ey), CYAN, 0.8, 0.18)
    # nested octagonal bevels
    r1 = _octa(cx, cy, 232, 142, 52)
    r2 = _octa(cx, cy, 210, 126, 46)
    r3 = _octa(cx, cy, 196, 114, 40)
    d += _ring(r1, r2, "url(#bevel)", OUT, 2.6)
    d += _ring(r2, r3, "url(#pl2)", OUT, 2.4)
    d += _ring(r3, hole, "#14226a", OUT, 2.4)
    d += poly(r1, None, "#bcd2ff", 1.2, sop=0.5)
    # hazard stripes along the straight edges of the innermost ring
    for k in range(18):
        x = cx - 120 + k * 14
        d += poly([(x, cy - 114), (x + 8, cy - 114), (x + 3, cy - 100), (x - 5, cy - 100)], AMB, None, op=0.95)
        d += poly([(x, cy + 114), (x + 8, cy + 114), (x + 3, cy + 100), (x - 5, cy + 100)], AMB, None, op=0.95)
    for k in range(7):
        y = cy - 60 + k * 18
        d += poly([(cx - 196, y), (cx - 196, y + 9), (cx - 182, y + 4), (cx - 182, y - 5)], AMB, None, op=0.95)
        d += poly([(cx + 196, y), (cx + 196, y + 9), (cx + 182, y + 4), (cx + 182, y - 5)], AMB, None, op=0.95)
    # retracted door leaves in guide slots left and right, a sign plate on top, a threshold plate below
    for sx in (-1, 1):
        x0 = cx + sx * 215
        d += rect(x0 - 12, cy - 70, 24, 140, "#050b24", OUT, 2.4, rx=6) + rect(x0 - 8, cy - 64, 16, 128, "#2a4aa8", OUT, 1.6, rx=4)
        for t in range(6):
            d += rect(x0 - 5, cy - 52 + t * 20, 10, 5, [CYAN, GREEN, MAG, AMB][t % 4], None, op=0.95, rx=1.5)
    d += rect(cx - 70, 20, 140, 34, "#050b24", OUT, 2.6, rx=8) + rect(cx - 64, 26, 128, 22, "#0a1442", None, rx=5)
    for k in range(7):
        d += glyph(cx - 54 + k * 18, 37, 9, [GREEN, CYAN, MAG][k % 3], 60 + k, 0.95)
    for k, xx in enumerate((cx - 100, cx - 90, cx + 90, cx + 100)):
        d += lamp(xx, 37, 3.4, [GREEN, AMB][k % 2])
    d += rect(cx - 90, 312, 180, 28, "#050b24", OUT, 2.6, rx=8)
    for k in range(9):
        d += poly([(cx - 78 + k * 18, 318), (cx - 66 + k * 18, 318), (cx - 60 + k * 18, 334), (cx - 72 + k * 18, 334)], CYAN if k % 2 else GREEN, None, op=0.8)
    for (bx, by) in ((20, 20), (620, 20), (20, 340), (620, 340)):
        d += hex_bolt(bx, by, 8)
    # glowing lining on the opening's edge
    dd = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in hole) + " Z"
    d += neon_path(dd, GREEN, 2.0, 1.0)
    info = write_svg("views/passage_frame.svg", (0, 0, fw, fh), d, defs)
    return {"file": "source/views/passage_frame.svg", "pivot": pivot_in(info, (cx, cy)), "px_scale": 0.5, "opening": [cx - 180, cy - 100, 360, 200],
            "note": "authored 640 x 360 design px (1280 x 720 texture); the runtime scales it 2x to cover the frame, the octagonal opening in the middle is transparent"}


def build_views() -> list:
    """The three extra views, in route order (main -> gallery -> reactor -> bridge -> main)."""
    from . import views_bridge, views_reactor
    return [gallery_view(), views_reactor.reactor_view(), views_bridge.bridge_view()]
