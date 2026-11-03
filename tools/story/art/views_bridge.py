"""The `bridge` view: the command bridge (banked consoles on both sides, a captain's chair on a dais, a huge viewscreen with a star field)."""
from __future__ import annotations

import math
import random

from .lib import OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, poly, rad_grad, rect, write_svg
from .mothership_stage import AMB, CYAN, GREEN, MAG, VIO, glyph, hex_bolt, neon, neon_path, polyhex
from .mothership_views import H, W, Room, floor_anchor, floor_rows, lamp, piece

B_ROOM = Room((640, 125), 0.55, -60, 374)
B_LED = (470, 46, 340, 40)
B_SCREEN = (322, 34, 636, 172)  # the viewscreen: x, y, w, h
B_LIGHTS = [[150, 30], [300, 30], [430, 30], [850, 30], [980, 30], [1130, 30], [220, 56], [1060, 56]]
B_WOOFERS = [[346, 236, 17], [934, 236, 17]]
RED = "#ff4a5a"


def qmap(q, s, t):
    """bilinear point inside the quad q = [tl, tr, br, bl]; s across, t down (0..1)"""
    top = (q[0][0] + (q[1][0] - q[0][0]) * s, q[0][1] + (q[1][1] - q[0][1]) * s)
    bot = (q[3][0] + (q[2][0] - q[3][0]) * s, q[3][1] + (q[2][1] - q[3][1]) * s)
    return (top[0] + (bot[0] - top[0]) * t, top[1] + (bot[1] - top[1]) * t)


def screen_on(q, seed, col=CYAN, bars=True) -> str:
    """A glowing display on a quad: dark glass, a bright frame, bar chart / trace lines and a glyph."""
    rng = random.Random(seed)
    inner = [qmap(q, .06, .1), qmap(q, .94, .1), qmap(q, .94, .9), qmap(q, .06, .9)]
    d = poly(q, "#050b24", OUT, 2) + poly(inner, col, None, op=0.22) + poly(inner, None, col, 1.2, sop=0.9)
    if bars:
        n = 7
        for i in range(n):
            h_ = rng.uniform(0.25, 0.8)
            s0 = 0.12 + i * 0.11
            d += poly([qmap(q, s0, 0.84), qmap(q, s0 + 0.07, 0.84), qmap(q, s0 + 0.07, 0.84 - h_ * 0.6), qmap(q, s0, 0.84 - h_ * 0.6)], [col, GREEN, AMB, MAG][i % 4], None, op=0.9)
    else:
        pts = [qmap(q, 0.1 + i * 0.1, 0.5 + 0.28 * math.sin(i * 1.3 + seed)) for i in range(9)]
        d += "".join(line(pts[i], pts[i + 1], col, 1.6, 0.95) for i in range(8))
    return d


def build_bridge_backdrop() -> dict:
    R = B_ROOM
    kf = R.kf
    rng = random.Random(733)
    sp = (1.0 / kf - 1.0) / 3
    ribs = R.ribs(3, sp)
    d, defs = "", ""
    NAV0, NAV1, NAV2 = "#06102e", "#102a62", "#2a52a8"
    d += rect(0, 0, W, H, "#040a22")
    # ceiling: dark vault with a central light panel
    defs += lin_grad("ceil", [(0, "#02060f"), (1, "#14306e")], 0, 0, 0, 1)
    d += poly(R.plane(R.t0, 2.4, kf, -3000, 4300), "url(#ceil)")
    d += poly(R.plane(R.t0 + 3, 1.0, kf, 470, 810), "#dff4ff", None, op=0.35) + poly(R.plane(R.t0 + 3, 1.0, kf, 540, 740), "#ffffff", None, op=0.45)
    for u in (180, 1100):
        d += poly(R.plane(R.t0 + 3, 1.0, kf, u - 20, u + 20), CYAN, None, op=0.3)
    # side walls: banks of tactical displays between the ribs
    defs += lin_grad("lw", [(0, "#050c26"), (1, "#1a3a80")], 0, 0, 1, 0)
    defs += lin_grad("rw", [(0, "#1a3a80"), (1, "#050c26")], 0, 0, 1, 0)
    d += poly(R.wall(0, 1.0, kf, R.t0, R.b0), "url(#lw)") + poly(R.wall(1280, 1.0, kf, R.t0, R.b0), "url(#rw)")
    for side, u in ((-1, 0), (1, 1280)):
        for i in range(3):
            k0, k1 = ribs[i], ribs[i + 1]
            a, b = k0 - (k0 - k1) * 0.12, k1 + (k0 - k1) * 0.12
            # a tall display wall, two stacked screens
            q1 = R.wall(u, a, b, -10, 110)
            q2 = R.wall(u, a, b, 126, 238)
            d += poly(R.wall(u, a - 0.01, b + 0.01, -16, 244), "#0a1c48", OUT, 2.6)
            d += screen_on(q1, 10 + i + (3 if side > 0 else 0), CYAN if side < 0 else MAG, bars=False)
            d += screen_on(q2, 20 + i + (3 if side > 0 else 0), GREEN if side < 0 else AMB, bars=True)
        d += neon(R.p(1.0, u, 250), R.p(kf, u, 250), CYAN if side < 0 else MAG, 2.0, 0.9)
    # far wall
    fx0, fx1, fy0, fy1 = 288, 992, 23, 262
    defs += lin_grad("fw", [(0, "#2a52a8"), (0.5, "#12306e"), (1, "#081a44")], 0, 0, 0, 1)
    d += rect(fx0, fy0, fx1 - fx0, fy1 - fy0, "url(#fw)")
    for x in range(fx0 + 8, fx1, 24):
        d += rect(x, fy0, 2.2, fy1 - fy0, "#030818", None, op=0.5) + rect(x + 2.2, fy0, 1.2, fy1 - fy0, CYAN, None, op=0.07)
    # the viewscreen: a stretch of space with a planet limb, a sun glare and a distant fleet
    sx, sy, sw, sh = B_SCREEN
    d += rect(sx - 14, sy - 12, sw + 28, sh + 24, "#12306e", OUT, 3.6, rx=30)
    defs += clip("vsclip", rect(sx, sy, sw, sh, rx=20))
    defs += lin_grad("vs", [(0, "#02030f"), (0.7, "#070a2e"), (1, "#101450")], 0, 0, 0, 1)
    defs += rad_grad("vn1", [(0, CYAN, 0.32), (1, CYAN, 0.0)]) + rad_grad("vn2", [(0, MAG, 0.32), (1, MAG, 0.0)]) + rad_grad("vn3", [(0, VIO, 0.35), (1, VIO, 0.0)])
    defs += rad_grad("vp", [(0, "#ffe6c8"), (0.4, "#ff9ab0"), (0.75, "#6a3ac8"), (1, "#14104a")], 0.3, 0.25, 0.9)
    defs += rad_grad("vatmo", [(0.9, CYAN, 0.0), (0.955, "#aaffff", 0.6), (1, CYAN, 0.0)])
    defs += rad_grad("vsun", [(0, "#ffffff", 1.0), (0.2, "#fff0c8", 0.5), (1, AMB, 0.0)])
    v = rect(sx, sy, sw, sh, "url(#vs)")
    v += ellipse(sx + 150, sy + 60, 190, 60, "url(#vn1)") + ellipse(sx + 360, sy + 40, 220, 55, "url(#vn2)") + ellipse(sx + 520, sy + 120, 200, 60, "url(#vn3)")
    for _ in range(170):
        x, y = sx + rng.random() * sw, sy + rng.random() * sh
        v += circle(x, y, rng.choice((0.6, 0.8, 1.0, 1.2, 1.6)), rng.choice(("#ffffff", "#cfe9ff", "#ffe7c8")), None, op=rng.choice((0.5, 0.7, 0.95)))
    for _ in range(9):
        x, y = sx + rng.random() * sw, sy + rng.random() * sh * 0.8
        v += line((x - 5, y), (x + 5, y), "#ffffff", 0.9, 0.8) + line((x, y - 5), (x, y + 5), "#ffffff", 0.9, 0.8)
    pcx, pcy, pr = 800, 360, 190
    defs += clip("vpc", circle(pcx, pcy, pr))
    v += circle(pcx, pcy, pr * 1.04, "url(#vatmo)") + circle(pcx, pcy, pr, "url(#vp)")
    bands = ""
    for k in range(-5, 5):
        yy = pcy - pr + 30 + k * 15 + 40
        bands += path(f"M{pcx - pr} {yy} Q{pcx} {yy - 16} {pcx + pr} {yy + 10}", None, ["#ffffff", "#c8a0ff", "#ffb0d8"][k % 3], 7, sop=0.14)
    v += group(bands, 'clip-path="url(#vpc)"') + circle(pcx, pcy, pr, None, "#aef4ff", 1.6, sop=0.5)
    v += circle(430, 128, 70, "url(#vsun)")
    for (fx_, fy_, s) in ((500, 150, 1.0), (545, 134, 0.7), (580, 160, 0.55)):  # a small fleet of ships
        v += path(f"M{fx_} {fy_} l{18 * s} {-4 * s} l{12 * s} {2 * s} l{-12 * s} {4 * s} Z", "#c8d8ff", OUT, 1.0) + circle(fx_ - 1, fy_, 1.6 * s, GREEN, None, op=0.95)
    d += group(v, 'clip-path="url(#vsclip)"')
    d += rect(sx, sy, sw, sh, None, OUT, 3, rx=20) + rect(sx - 6, sy - 6, sw + 12, sh + 12, None, CYAN, 1.2, rx=26, sop=0.7)
    for x in (sx + 160, sx + 318, sx + 476):  # frame struts
        d += rect(x - 3, sy, 6, sh, "#12306e", OUT, 2) + line((x - 1, sy), (x - 1, sy + sh), "#7aa0ff", 1.0, 0.5)
    # LED screen hanging in front of the viewscreen
    lx, ly, lw_, lh = B_LED
    for x in (lx + 40, lx + lw_ - 40):
        d += line((x, 16), (x, ly - 10), OUT, 4.4) + line((x, 16), (x, ly - 10), "#6a8ae8", 1.6)
    d += rect(lx - 10, ly - 10, lw_ + 20, lh + 20, "#162a78", OUT, 3.2, rx=8) + rect(lx - 5, ly - 5, lw_ + 10, lh + 10, "#050b24", OUT, 2, rx=4) + rect(lx, ly, lw_, lh, "#04061a")
    d += neon((lx - 10, ly - 10), (lx + lw_ + 10, ly - 10), CYAN, 1.2, 0.9) + neon((lx - 10, ly + lh + 10), (lx + lw_ + 10, ly + lh + 10), RED, 1.2, 0.9)
    for cx_, cy_ in ((lx - 5, ly - 5), (lx + lw_ + 5, ly - 5), (lx - 5, ly + lh + 5), (lx + lw_ + 5, ly + lh + 5)):
        d += hex_bolt(cx_, cy_, 3)
    # the far console bank under the viewscreen, broken by the dais; speaker pods at the ends
    for x0, x1 in ((296, 566), (714, 984)):
        d += rect(x0, 214, x1 - x0, 48, "#0a1c48", OUT, 2.8) + rect(x0, 214, x1 - x0, 7, "#3a64c8", OUT, 2) + rect(x0 + 4, 224, x1 - x0 - 8, 30, "#030818", None, op=0.6, rx=3)
        for k in range(int((x1 - x0) / 17)):
            x = x0 + 10 + k * 17
            d += rect(x, 232, 11, 5, [CYAN, GREEN, RED, AMB][k % 4], None, op=0.4 + 0.5 * (((k * 5) % 3) == 0), rx=2) + glyph(x + 5, 246, 5, "#8aa6ff", k, 0.5)
        d += neon((x0, 261), (x1, 261), CYAN, 1.3, 0.9)
    for (wx, wy, wr) in B_WOOFERS:
        d += circle(wx, wy, wr + 5, "#030818", OUT, 2.6) + circle(wx, wy, wr + 3, None, CYAN, 1.0, sop=0.7) + circle(wx, wy, wr, "#04071c")
    # --- floor: dark steel plates, a central runway with chevrons, then a star-chart ring
    defs += lin_grad("fl", [(0, "#1a3a80"), (0.3, "#0c1c4c"), (1, "#050a22")], 0, 0, 0, 1)
    d += poly(R.plane(R.b0, 2.4, kf, -3000, 4300), "url(#fl)")
    defs += clip("floorclip", poly(R.plane(R.b0, 2.4, kf, -3000, 4300)))
    fl = ""
    ds = [1.0 / kf - i * 0.22 for i in range(0, 14)]
    for u in range(-1280, 2561, 160):  # alternate plate shades
        if (u // 160) % 2 == 0:
            fl += poly(R.plane(R.b0, 2.4, kf, u, u + 160), "#4a78e8", None, op=0.2)
    for u in range(-1280, 2561, 160):
        fl += line(R.p(2.4, u, R.b0), R.p(kf, u, R.b0), "#8aa6ff", 1.6, 0.6)
    for dd in ds:
        fl += line(R.p(1.0 / dd, -1280, R.b0), R.p(1.0 / dd, 2560, R.b0), "#8aa6ff", max(0.9, 2.6 / dd), 0.55)
    # the runway: a lit strip toward the viewscreen with chevrons
    fl += poly(R.plane(R.b0, 2.4, kf, 520, 760), "#06102e", None, op=0.5)
    for u in (520, 760):
        fl += line(R.p(2.4, u, R.b0), R.p(kf, u, R.b0), RED, 3.0, 0.9) + line(R.p(2.4, u, R.b0), R.p(kf, u, R.b0), "#ffd0d0", 1.0, 0.7)
    for dd in ds[2:-1:2]:
        k1_, k0_ = 1.0 / dd, 1.0 / (dd - 0.12)
        fl += poly([R.p(k1_, 560, R.b0), R.p(k1_, 640, R.b0), R.p(k0_, 640, R.b0), R.p(k0_, 560, R.b0)], RED, None, op=0.0)
        fl += poly([R.p(k1_, 560, R.b0), R.p(k1_ * 0.97 + k0_ * .03, 640, R.b0), R.p(k0_, 560, R.b0), R.p(k0_, 520 + 40, R.b0)], CYAN, None, op=0.0)
    d += group(fl, 'clip-path="url(#floorclip)"')
    # the star-chart ring under the dancers
    cx_c, cy_c, rx_c, ry_c = 640, 372, 250, 46
    defs += rad_grad("ringglow", [(0, CYAN, 0.28), (0.7, "#4a7aff", 0.12), (1, CYAN, 0.0)])
    d += ellipse(cx_c, cy_c, rx_c + 44, ry_c + 28, "url(#ringglow)")
    d += ellipse(cx_c, cy_c, rx_c, ry_c, "#06102e", None, op=0.4) + ellipse(cx_c, cy_c, rx_c, ry_c, None, CYAN, 4, sop=0.12) + ellipse(cx_c, cy_c, rx_c, ry_c, None, "#b8ecff", 1.6, sop=0.9)
    d += ellipse(cx_c, cy_c, rx_c * .78, ry_c * .78, None, CYAN, 1.0, sop=0.6) + ellipse(cx_c, cy_c, rx_c * .5, ry_c * .5, None, RED, 1.4, sop=0.8)
    for a in range(48):  # compass ticks
        t = a * math.tau / 48
        r0, r1 = (0.92, 1.0) if a % 4 == 0 else (0.96, 1.0)
        d += line((cx_c + rx_c * r0 * math.cos(t), cy_c + ry_c * r0 * math.sin(t)), (cx_c + rx_c * r1 * math.cos(t), cy_c + ry_c * r1 * math.sin(t)), "#ffffff", 1.4 if a % 4 == 0 else 0.8, 0.85)
    for a in (0, 90, 180, 270):  # a compass rose: four long points
        t = math.radians(a)
        d += poly([(cx_c + rx_c * .4 * math.cos(t), cy_c + ry_c * .4 * math.sin(t)), (cx_c + rx_c * .12 * math.cos(t + 1.0), cy_c + ry_c * .12 * math.sin(t + 1.0)), (cx_c + rx_c * .12 * math.cos(t - 1.0), cy_c + ry_c * .12 * math.sin(t - 1.0))], RED if a == 270 else CYAN, None, op=0.7)
    d += neon(R.p(2.4, 0, R.b0), R.p(kf, 0, R.b0), CYAN, 2.0, 0.9) + neon(R.p(2.4, 1280, R.b0), R.p(kf, 1280, R.b0), MAG, 2.0, 0.9)
    # --- ribs
    for i, k in enumerate(ribs[:-1]):
        a, b, c, e = R.p(k, 0, R.b0), R.p(k, 0, R.t0), R.p(k, 1280, R.t0), R.p(k, 1280, R.b0)
        dd_ = f"M{f(a[0])} {f(a[1])} L{f(b[0])} {f(b[1])} L{f(c[0])} {f(c[1])} L{f(e[0])} {f(e[1])}"
        w_ = 22 * k
        d += path(dd_, None, OUT, w_ + 6) + path(dd_, None, "#2a52a8", w_) + path(dd_, None, "#9ab8ff", w_ * .22, sop=0.55)
    # --- banked consoles on both sides: a low tier and a high tier per bay, screens on the tops and fronts
    for side in (-1, 1):
        for i in range(3):
            k0, k1 = ribs[i] - (ribs[i] - ribs[i + 1]) * 0.1, ribs[i + 1] + (ribs[i] - ribs[i + 1]) * 0.1
            for (ua, ub, top, col, sd) in ((0, 118, 262, NAV2, 7), (118, 250, 318, "#1c3c88", 11)):
                a, b = (ua, ub) if side < 0 else (1280 - ub, 1280 - ua)
                o, fc = R.box(a, b, k0, k1, top, R.b0, lighten(col, .22), col, darken(col, .4), 2.4)
                d += o
                tq = fc.get("top")
                if tq is not None:
                    # plane() order is near-left, near-right, far-right, far-left; the display is a slanted panel inset in the top face
                    d += screen_on([qmap(tq, .12, .86), qmap(tq, .88, .86), qmap(tq, .88, .2), qmap(tq, .12, .2)],
                                   sd + i + side, CYAN if side < 0 else MAG, bars=(i + (0 if top > 300 else 1)) % 2 == 0)
                fq = fc["front"]
                for t in range(5):  # a row of lit keys on the front face
                    d += poly([qmap(fq, .1 + t * .17, .3), qmap(fq, .2 + t * .17, .3), qmap(fq, .2 + t * .17, .45), qmap(fq, .1 + t * .17, .45)], [CYAN, GREEN, AMB, RED, MAG][(t + i) % 5], None, op=0.9)
                d += line(fq[3], fq[2], CYAN if side < 0 else MAG, 1.6, 0.9)
            # an operator's seat in front of the low tier
            kc = (k0 + k1) / 2
            ux = 330 if side < 0 else 950
            sx_, sy_ = R.p(kc, ux, R.b0)
            r_ = 30 * kc
            d += ellipse(sx_, sy_ + 2, r_ * 1.1, r_ * .3, "#02040f", None, op=0.5)
            d += path(f"M{f(sx_ - r_)} {f(sy_ - r_ * .9)} Q{f(sx_)} {f(sy_ - r_ * 2.2)} {f(sx_ + r_)} {f(sy_ - r_ * .9)} L{f(sx_ + r_ * .8)} {f(sy_)} L{f(sx_ - r_ * .8)} {f(sy_)} Z", "#1c3c88", OUT, 2)
            d += line((sx_ - r_ * .6, sy_ - r_ * 1.1), (sx_ + r_ * .6, sy_ - r_ * 1.1), CYAN, 1.8 * kc + .4, 0.9)
    # --- the captain's dais and chair
    o1, f1 = R.box(480, 800, 0.655, 0.55, 340, R.b0, "#4a78d8", "#1c3c88", "#0c1c4c", 2.6)
    o2, f2 = R.box(552, 728, 0.62, 0.55, 316, R.b0, "#6a98f0", "#2a52a8", "#14306e", 2.6)
    d += o1 + o2
    d += line(f1["front"][3], f1["front"][2], RED, 2.2, 0.95) + line(f2["front"][3], f2["front"][2], CYAN, 1.8, 0.95)
    for t in range(1, 7):
        d += circle(qmap(f1["front"], t / 7.0, 0.5)[0], qmap(f1["front"], t / 7.0, 0.5)[1], 1.8, "#ffffff", None, op=0.8)
    cx, cb = 640, 236  # chair base centre (on the upper step)
    ch = ""
    defs += lin_grad("chair", [(0, "#d84a6a"), (0.5, "#7a1c48"), (1, "#3a0c30")], 0, 0, 0, 1)
    ch += ellipse(cx, cb + 2, 38, 7, "#02040f", None, op=0.55)
    ch += rect(cx - 5, cb - 16, 10, 16, "#2a52a8", OUT, 2, rx=2) + ellipse(cx, cb - 1, 24, 5, "#3a64c8", OUT, 2.2)  # pedestal
    ch += path(f"M{cx - 30} {cb - 22} L{cx - 33} {cb - 78} Q{cx - 33} {cb - 98} {cx - 14} {cb - 98} H{cx + 14} Q{cx + 33} {cb - 98} {cx + 33} {cb - 78} L{cx + 30} {cb - 22} Z", "url(#chair)", OUT, 3)  # tall back
    ch += path(f"M{cx - 22} {cb - 40} L{cx - 24} {cb - 84} Q{cx - 24} {cb - 90} {cx - 14} {cb - 90} H{cx + 14} Q{cx + 24} {cb - 90} {cx + 24} {cb - 84} L{cx + 22} {cb - 40} Z", "#ff7a98", None, op=0.35)
    ch += path(f"M{cx - 38} {cb - 80} Q{cx - 46} {cb - 100} {cx - 26} {cb - 108} L{cx - 20} {cb - 94}", "#2a52a8", OUT, 2.4) + path(f"M{cx + 38} {cb - 80} Q{cx + 46} {cb - 100} {cx + 26} {cb - 108} L{cx + 20} {cb - 94}", "#2a52a8", OUT, 2.4)  # wings
    ch += rect(cx - 33, cb - 34, 66, 16, "#b8365a", OUT, 2.4, rx=7)  # seat
    for sgn in (-1, 1):
        ch += rect(cx + sgn * 36 - 7, cb - 44, 14, 28, "#2a52a8", OUT, 2.2, rx=4) + rect(cx + sgn * 36 - 4, cb - 42, 8, 8, CYAN, None, op=0.9, rx=2) + rect(cx + sgn * 36 - 4, cb - 31, 8, 3, GREEN, None, op=0.9)
    ch += line((cx, cb - 90), (cx, cb - 60), AMB, 1.6, 0.8) + circle(cx, cb - 74, 5, None, AMB, 1.5, sop=0.9)
    ch += neon((cx - 33, cb - 96), (cx - 31, cb - 28), RED, 1.2, 0.9) + neon((cx + 33, cb - 96), (cx + 31, cb - 28), RED, 1.2, 0.9)
    d += group(ch, f'transform="translate({cx} {cb}) scale(1.32) translate({-cx} {-cb})"')
    # alert beacons on the far wall corners (the glow is a piece) and overhead rail with the light plates
    for bx in (306, 974):
        d += rect(bx - 10, 46, 20, 24, "#12306e", OUT, 2.2, rx=4) + circle(bx, 54, 8, RED, OUT, 1.6) + circle(bx - 2, 52, 2.6, "#ffffff", None, op=0.9)
    d += rect(60, 0, 1160, 9, "#2a52a8", OUT, 2) + line((60, 3), (1220, 3), "#9ab8ff", 1.2, 0.6)
    for xx in (140, 640, 1140):
        d += line((xx, 9), (xx, 18), OUT, 4) + line((xx, 9), (xx, 18), "#6a8ae8", 1.6)
    for (mx, my) in B_LIGHTS:
        d += polyhex(mx, my - 4, 11)
    return write_svg("views/bridge_backdrop.svg", (0, 0, W, H), d, defs)


def build_bridge_front() -> dict:
    d = ""
    # foreground console wedges at the screen corners, a pillar and a lintel
    for side in (-1, 1):
        x0 = 0 if side < 0 else W
        e = 120 * side
        dark, mid, hi = "#0c1c4c", "#1c3c88", "#4a78d8"
        d += poly([(x0, 330), (x0 + e, 392), (x0 + e, 470), (x0, 470)], mid, OUT, 3.2)
        d += poly([(x0, 330), (x0 + e, 392), (x0 + e * .86, 380), (x0, 318)], hi, OUT, 2.6)
        d += poly([(x0 + side * 4, 322), (x0 + e * .82, 376), (x0 + e * .82, 384), (x0 + side * 4, 330)], "#050b24", None, op=0.0)
        scr = [(x0 + side * 12, 336), (x0 + e * .78, 386), (x0 + e * .78, 424), (x0 + side * 12, 408)]
        d += screen_on(scr, 90 + side, CYAN if side < 0 else MAG, bars=side < 0)
        for t in range(4):
            d += rect(x0 + side * (14 + t * 24) - (0 if side > 0 else 8), 442, 8, 6, [CYAN, GREEN, AMB, RED][t], None, op=0.9, rx=2)
        px = 0 if side < 0 else W - 36
        d += rect(px, -4, 36, 336, dark, OUT, 3.2) + rect(px + (4 if side < 0 else 24), -4, 8, 336, "#2a52a8", None, op=0.85)
        xi = 36 if side < 0 else W - 36
        d += line((xi, 28), (xi, 326), CYAN if side < 0 else MAG, 2.0, 0.9) + line((xi, 28), (xi, 326), "#ffffff", 0.8, 0.5)
        for yy in range(50, 320, 50):
            d += rect(px + 6, yy, 24, 5, "#02040f", None, op=0.7, rx=2) + rect(px + 8, yy + 1.2, 20, 2.6, [CYAN, GREEN, RED, AMB][(yy // 50) % 4], None, op=0.9)
    d += rect(-4, -4, W + 8, 24, "#0c1c4c", OUT, 3.2) + rect(-4, 2, W + 8, 6, "#2a52a8", None, op=0.85) + line((36, 20), (W - 36, 20), CYAN, 1.8, 0.9)
    return write_svg("views/bridge_front.svg", (0, 0, W, 480), d)


def bridge_pieces() -> list:
    out = []
    sx, sy, sw, sh = B_SCREEN
    rng = random.Random(91)
    # the viewscreen's hyperspace streaks (additive)
    cx, cy = sx + sw / 2, sy + sh * 0.5
    d = ""
    for _ in range(80):
        a = rng.random() * math.tau
        r0 = rng.uniform(30, 250)
        ln = r0 * rng.uniform(0.2, 0.6)
        p0 = (cx + math.cos(a) * r0 * 1.7, cy + math.sin(a) * r0 * 0.5)
        p1 = (cx + math.cos(a) * (r0 + ln) * 1.7, cy + math.sin(a) * (r0 + ln) * 0.5)
        if not (sx + 8 < p0[0] < sx + sw - 8 and sy + 8 < p0[1] < sy + sh - 8 and sx + 8 < p1[0] < sx + sw - 8 and sy + 8 < p1[1] < sy + sh - 8):
            continue
        if B_LED[0] - 12 < p0[0] < B_LED[0] + B_LED[2] + 12 and B_LED[1] - 12 < p0[1] < B_LED[1] + B_LED[3] + 12:
            continue
        col = rng.choice(("#ffffff", "#c8f4ff", "#ffd0f0"))
        d += line(p0, p1, col, 3.0, rng.uniform(0.1, 0.2)) + line(p0, p1, col, 1.1, rng.uniform(0.7, 1.0))
    out.append(piece("bridge_warp_streaks", "views/bridge_warp_streaks.svg", (sx, sy, sx + sw, sy + sh), "pulse", "behind", (cx, cy), "add", d))
    # a holographic tactical globe floating over the left console bank
    gx, gy, gr = 420, 186, 24
    d = circle(gx, gy, gr + 14, "#8affff", None, op=0.08) + circle(gx, gy, gr, "#8affff", None, op=0.12) + circle(gx, gy, gr, None, CYAN, 1.8, sop=0.95)
    for k in range(-2, 3):
        yy = gy + k * gr * 0.4
        rr = math.sqrt(max(0.0, gr * gr - (k * gr * 0.4) ** 2))
        d += ellipse(gx, yy, rr, rr * 0.22, None, CYAN, 1.0, sop=0.75)
    d += ellipse(gx, gy, gr * 0.4, gr, None, "#ffffff", 1.0, sop=0.7) + ellipse(gx, gy, gr * 1.5, gr * 0.3, None, GREEN, 1.6, sop=0.9)
    for (a, b_) in ((-6, -8), (8, 4), (3, -14)):
        d += circle(gx + a, gy + b_, 2.2, RED, None, op=0.95)
    d += poly([(gx - 22, gy + 44), (gx + 22, gy + 44), (gx + 9, gy + gr + 4), (gx - 9, gy + gr + 4)], CYAN, None, op=0.16) + ellipse(gx, gy + 44, 22, 4, CYAN, None, op=0.4)
    out.append(piece("bridge_holo_globe", "views/bridge_holo_globe.svg", (gx - 44, gy - 40, gx + 44, gy + 54), "bob", "behind", (gx, gy + 10), "add", d))
    # alert beacons: red glow with a sweeping cone
    d = ""
    defs = rad_grad("ab", [(0, "#ff9a9a", 0.9), (0.3, RED, 0.4), (1, RED, 0.0)])
    for bx in (306, 974):
        d += circle(bx, 54, 36, "url(#ab)")
        s = 1 if bx < 640 else -1
        d += poly([(bx, 54), (bx + s * 90, 20), (bx + s * 90, 100)], RED, None, op=0.14)
    out.append(piece("bridge_alert_beacons", "views/bridge_alert_beacons.svg", (240, 0, 1040, 130), "flicker", "behind", (640, 54), "add", d, defs))
    return out


def bridge_view() -> dict:
    build_bridge_backdrop()
    build_bridge_front()
    poly_, grid = floor_anchor((640, 125), 262, 330, 950)
    anchors = {
        "floor_rows": floor_rows(125), "floor_polygon": poly_, "floor_grid": grid, "light_points": B_LIGHTS,
        "led_screen": list(B_LED), "woofers": B_WOOFERS, "circle_centre": [640, 372], "circle_radii": [250, 46], "horizon_y": 125,
        "vanish": [640, 125], "disco_ball": [640, 0], "riser": [640, 262, 240], "wall_left_x": 288, "wall_right_x": 992,
        "window": list(B_SCREEN), "chair": [640, 236],
    }
    return {"id": "bridge", "title": "Command bridge",
            "layers": [{"id": "backdrop", "file": "source/views/bridge_backdrop.svg", "pos": [0, 0], "size": [W, H], "px_scale": 0.5},
                       {"id": "front_frame", "file": "source/views/bridge_front.svg", "pos": [0, 0], "size": [W, 480], "px_scale": 0.5, "z": "front"}],
            "anchors": anchors, "pieces": bridge_pieces(), "palette_hint": "cool"}
