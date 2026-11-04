"""View `pit`: a vast lava lake under a cavern roof, bone bridges to a far fortress, and the stage platform out on the lake
(ember red, orange and bone; the sky is the glare of the lake)."""
from __future__ import annotations

import math
import random

from . import uw_stage as U, uw_views as V
from .lib import OUT, circle, clip, ellipse, f, group, lighten, line, lin_grad, mix, path, poly, rad_grad, rect, write_svg
from .uw_stage import BONE, EMBER, GOLD, LAVA, MAG, VIO, pline

W, H = V.W, V.H
R = V.Room(640, 170, 330, 950, 110, 262)  # the platform is the "floor"; far edge y 266
HORIZON = 190  # the far shore line
PLATFORM = [(330, 266), (950, 266), (1110, 320), (1250, 440), (1330, 520), (-50, 520), (30, 440), (170, 320)]
CE = lambda x: 24 + 40 * ((x - 640) / 640.0) ** 2  # the cavern ceiling edge (y) at x, before the stalactite fringe
LIGHTS = [[150, 70], [330, 50], [500, 44], [780, 44], [950, 50], [1130, 70], [430, 66], [850, 66]]


def ridge(x0, x1, base, amp, rng, step=26, bottom=None):
    pts = [(x0, bottom if bottom is not None else base)]
    x = x0
    while x <= x1:
        pts.append((x, base - rng.uniform(0.15, 1.0) * amp))
        x += step * rng.uniform(0.6, 1.3)
    pts.append((x1, bottom if bottom is not None else base))
    return pts


def deck_quad(a, b, wa, wb):
    """A bridge deck as a quad between centre points a and b with half-widths wa, wb (perpendicular offsets on screen)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    return [(a[0] + nx * wa, a[1] + ny * wa), (b[0] + nx * wb, b[1] + ny * wb), (b[0] - nx * wb, b[1] - ny * wb), (a[0] - nx * wa, a[1] - ny * wa)]


def bone_bridge(a, b, wa, wb, n_post=6, tilt=0.0):
    """A bridge of bone: arched rib supports in the lava, plank deck, vertebra posts with skull lanterns and a rail."""
    d = ""
    q = deck_quad(a, b, wa, wb)
    ln = math.hypot(b[0] - a[0], b[1] - a[1])
    # supports: rib arches dipping below the deck at intervals
    for k in range(5):
        t = (k + 0.5) / 5
        c = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        w_ = wa + (wb - wa) * t
        drop = 22 * (0.4 + 0.6 * (1 - t))
        d += path(f"M{f(c[0] - w_ * 0.8)} {f(c[1] + 1)} Q{f(c[0])} {f(c[1] + drop * 1.7)} {f(c[0] + w_ * 0.8)} {f(c[1] + 1)}", None, OUT, 4.6 * (0.5 + 0.5 * (1 - t)) + 2)
        d += path(f"M{f(c[0] - w_ * 0.8)} {f(c[1] + 1)} Q{f(c[0])} {f(c[1] + drop * 1.7)} {f(c[0] + w_ * 0.8)} {f(c[1] + 1)}", None, "#cdbf9c", 2.6 * (0.5 + 0.5 * (1 - t)) + 1)
    d += poly(q, "#8a7a6a", OUT, 2.4)
    d += poly([(q[0][0], q[0][1] + 0.5), (q[1][0], q[1][1] + 0.5), (q[2][0], q[2][1] + 0.5), (q[3][0], q[3][1] + 0.5)], "#d8c8a0", None, op=0.55)
    for k in range(1, 12):  # planks
        t = k / 12
        pa = (q[0][0] + (q[1][0] - q[0][0]) * t, q[0][1] + (q[1][1] - q[0][1]) * t)
        pb = (q[3][0] + (q[2][0] - q[3][0]) * t, q[3][1] + (q[2][1] - q[3][1]) * t)
        d += line(pa, pb, "#3a2a2a", 1.2, 0.7)
    d += line(q[0], q[1], "#fff2c8", 1.0, 0.7) + line(q[3], q[2], "#fff2c8", 1.0, 0.5)
    # posts with little skull caps along both rails
    for k in range(n_post):
        t = k / (n_post - 1)
        for sgn, (i0, i1) in ((1, (0, 3)), (-1, (1, 2))):
            pt = (q[i0][0] + (q[i1][0] - q[i0][0]) * t, q[i0][1] + (q[i1][1] - q[i0][1]) * t) if False else None
        c = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        w_ = wa + (wb - wa) * t
        sc = 0.55 + 0.45 * (1 - t)
        for sgn in (-1, 1):
            px_, py_ = c[0] + sgn * w_, c[1]
            d += rect(px_ - 2.2 * sc, py_ - 17 * sc, 4.4 * sc, 17 * sc, BONE, OUT, 1.4)
            d += circle(px_, py_ - 19 * sc, 4.6 * sc, BONE, OUT, 1.3) + circle(px_, py_ - 19.5 * sc, 2.2 * sc, "#ff7a1a", None, op=0.9)
    return d


def build_backdrop():
    rng = random.Random(311)
    defs = ""
    d = ""
    defs += lin_grad("sky", [(0, "#07020c"), (0.42, "#2a0a18"), (0.9, "#ff7a2a")], 0, 0, 0, 1)
    d += rect(0, 0, W, HORIZON + 2, "url(#sky)")
    defs += rad_grad("hz", [(0, "#ffd070", 0.95), (0.35, "#ff7a2a", 0.55), (1, "#ff3a1a", 0.0)], 0.5, 0.5, 0.5)
    d += ellipse(640, HORIZON - 6, 640, 150, "url(#hz)")
    # ---- far shore: layered ridges, a smoking volcano and the fortress that the central causeway leads to
    d += poly(ridge(-10, W + 10, HORIZON - 14, 40, rng, 34, HORIZON + 2), "#4a1424", None, op=0.9)
    d += path(pline([(x, y) for x, y in ridge(-10, W + 10, HORIZON - 6, 34, rng, 30)]), None, "#ff9a3a", 1.2, sop=0.35)
    vx = 238
    cone = [(vx - 150, HORIZON + 2), (vx - 40, 96), (vx - 22, 84), (vx + 22, 84), (vx + 40, 96), (vx + 150, HORIZON + 2)]
    d += poly(cone, "#2d1020", OUT, 2.6)
    d += poly([(vx - 22, 84), (vx + 22, 84), (vx + 14, 92), (vx - 14, 92)], "#ff9a3a", None, op=0.95)
    d += path(f"M{vx - 6} 90 L{vx - 18} 118 L{vx - 8} 134 L{vx - 26} 160 L{vx - 18} {HORIZON}", None, "#ff6a1a", 2.8, sop=0.9)
    d += path(f"M{vx + 6} 90 L{vx + 14} 112 L{vx + 6} 140 L{vx + 20} 165", None, "#ffb02e", 2.2, sop=0.8)
    for k, (px_, py_, rr) in enumerate(((vx - 4, 62, 26), (vx + 10, 40, 34), (vx - 6, 16, 44))):  # smoke plume, lit from below
        d += circle(px_, py_, rr, "#3a1020", None, op=0.62) + circle(px_ - 4, py_ + 6, rr * 0.7, "#ff5a2a", None, op=0.12)
    # fortress on the far shore, dead centre: a gate tower with spires
    d += ellipse(640, 170, 150, 56, "#ff3a1a", None, op=0.12) + ellipse(640, 176, 100, 36, "#ff7a2a", None, op=0.14)
    fy = HORIZON + 2
    towers = ((560, 40, 96), (586, 30, 128), (640, 56, 154), (694, 30, 128), (720, 40, 96))
    for (tx, tw, th) in towers:
        d += rect(tx - tw / 2, fy - th, tw, th, "#2a0e1c", OUT, 2.4)
        d += poly([(tx - tw / 2 - 3, fy - th + 1), (tx, fy - th - tw * 1.25), (tx + tw / 2 + 3, fy - th + 1)], "#3a1426", OUT, 2.4)
        d += line((tx, fy - th - tw * 1.25), (tx, fy - th - tw * 1.25 - 10), BONE, 1.6)
        d += poly([(tx, fy - th - tw * 1.25 - 10), (tx + 8, fy - th - tw * 1.25 - 7), (tx, fy - th - tw * 1.25 - 4)], MAG, None)
        for wy in range(int(fy - th + 12), int(fy - 20), 20):
            d += rect(tx - 3, wy, 6, 10, "#ffc060", OUT, 1.0, rx=2)
    d += path(f"M606 {fy} L606 {fy - 34} Q606 {fy - 54} 640 {fy - 56} Q674 {fy - 54} 674 {fy - 34} L674 {fy} Z", "#0a0108", OUT, 2.6)
    d += path(f"M614 {fy} L614 {fy - 32} Q614 {fy - 46} 640 {fy - 48} Q666 {fy - 46} 666 {fy - 32} L666 {fy} Z", "#ff3a1a", None, op=0.9)
    d += U.skull(640, fy - 64, 9, BONE, "#ff7a1a", 1.6, jaw=False)
    d += ellipse(640, fy + 2, 120, 5, "#ff9a3a", None, op=0.55)
    # ---- the lake
    defs += lin_grad("lake", [(0, "#ffd070"), (0.07, "#ff8a2a"), (0.3, "#e03a14"), (0.65, "#8a1018"), (1, "#3a0610")], 0, 0, 0, 1)
    d += rect(0, HORIZON, W, H - HORIZON, "url(#lake)")
    defs += clip("lakeclip", rect(0, HORIZON, W, H - HORIZON))
    lk = ""
    y = HORIZON + 4
    k = 0
    while y < H + 10:  # ripple streaks, wider and brighter nearer the camera
        sc = (y - HORIZON) / 120.0 + 0.4
        for j in range(int(5 + sc * 4)):
            x = rng.uniform(-40, W + 40)
            ln = rng.uniform(40, 130) * sc
            c = rng.choice(("#ffe08a", "#ffb02e", "#ff7a1a", "#ffd23f"))
            lk += path(f"M{f(x)} {f(y)} q{f(ln * 0.25)} {f(-3 * sc)} {f(ln * 0.5)} 0 t{f(ln * 0.5)} 0", None, c, 1.4 * sc ** 0.8, sop=min(0.8, 0.28 + 0.1 * sc))
        y += 7 * sc ** 1.2 + 2
        k += 1
    for k in range(34):  # dark crust plates floating in the lava, glowing at the cracks
        cx_ = rng.uniform(-20, W + 20)
        cy_ = rng.uniform(HORIZON + 14, H - 40)
        sc = (cy_ - HORIZON) / 150.0 + 0.3
        rx, ry = rng.uniform(16, 44) * sc, rng.uniform(4, 9) * sc
        pts = [(cx_ + math.cos(a) * rx * rng.uniform(0.75, 1.1), cy_ + math.sin(a) * ry * rng.uniform(0.8, 1.1)) for a in [i * math.tau / 9 for i in range(9)]]
        lk += poly(pts, "#2a0a12", "#ff6a1a", 1.2 * sc ** 0.6, sop=0.8)
        lk += path(pline([(cx_ - rx * 0.5, cy_), (cx_ + rx * 0.1, cy_ - ry * 0.3), (cx_ + rx * 0.5, cy_ + ry * 0.2)]), None, "#ffb02e", 0.9 * sc ** 0.5, sop=0.8)
    for k in range(18):  # bubbles
        cx_, cy_ = rng.uniform(0, W), rng.uniform(HORIZON + 30, H - 30)
        sc = (cy_ - HORIZON) / 150.0 + 0.3
        lk += ellipse(cx_, cy_, 7 * sc, 3.6 * sc, "#ffe08a", None, op=0.3) + ellipse(cx_, cy_ - 0.6 * sc, 5 * sc, 2.4 * sc, "#ff8a2a", "#fff2c0", 0.8, sop=0.8)
    d += group(lk, 'clip-path="url(#lakeclip)"')
    # ---- the causeway (centre) and the two diagonal bridges, drawn before the platform so the platform overlaps their ends
    d += bone_bridge((640, 267), (640, fy + 2), 54, 13, n_post=6)
    d += bone_bridge((196, 316), (110, 240), 32, 13, n_post=6)
    d += bone_bridge((1084, 316), (1170, 240), 32, 13, n_post=6)
    # ---- the platform: basalt slabs with hot seams, a raised stone curb round the rim and a glowing seal
    defs += lin_grad("plat", [(0, "#3a1828"), (0.4, "#240e1c"), (1, "#120610")], 0, 0, 0, 1)
    defs += lin_grad("edgeglow", [(0, "#ff7a2a", 0.0), (1, "#ff7a2a", 0.55)], 0, 0, 1, 0)
    # the lake boils and glows right against the rim (drawn before the slab so the slab cuts it)
    for (a, b) in ((PLATFORM[7], PLATFORM[0]), (PLATFORM[6], PLATFORM[7]), (PLATFORM[5], PLATFORM[6]),
                   (PLATFORM[1], PLATFORM[2]), (PLATFORM[2], PLATFORM[3]), (PLATFORM[3], PLATFORM[4])):
        sc = R.scale((a[1] + b[1]) / 2)
        d += line(a, b, "#ff8a2a", 30 * sc ** 0.8, 0.22) + line(a, b, "#ffd070", 12 * sc ** 0.8, 0.35)
    for k in range(26):  # splashes and bubbles hugging the rim
        side = -1 if k % 2 == 0 else 1
        t = rng.uniform(0.05, 0.95)
        a, b = (PLATFORM[7], PLATFORM[5]) if side < 0 else (PLATFORM[2], PLATFORM[4])
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        sc = R.scale(y) * 0.5
        x += side * rng.uniform(8, 30) * sc
        d += ellipse(x, y, 7 * sc, 3 * sc, "#fff0b0", "#ff9a2a", 1.0, op=0.7)
    d += poly([(x, y + 7) for x, y in PLATFORM[:5]], "#08020a", None, op=0.55)
    d += poly(PLATFORM, "url(#plat)")
    defs += clip("platclip", poly(PLATFORM))
    gp = ""
    ys = [yy for yy in R.floor_lines(0.085) if yy > 262]
    for j in range(len(ys) - 1):  # running-bond slabs: rows offset by half a slab, each slab its own shade of basalt
        ya, yb = ys[j], ys[j + 1]
        off = 0.5 if j % 2 else 0.0
        for i in range(-12, 13):
            xa, xb = 640 + (i + off - 0.5) * 70, 640 + (i + off + 0.5) * 70
            q = [(R.floor_x(xa, ya), ya), (R.floor_x(xb, ya), ya), (R.floor_x(xb, yb), yb), (R.floor_x(xa, yb), yb)]
            tone = rng.choice(("#3a1828", "#46202e", "#2c1220", "#502634", "#341424"))
            gp += poly(q, tone, "#0a0208", 1.6 * R.scale(ya) ** 0.5, op=0.95)
            gp += line((q[0][0] + 2, q[0][1] + 1.2), (q[1][0] - 2, q[1][1] + 1.2), "#9a5a6a", 1.1 * R.scale(ya) ** 0.5, 0.5)  # lit top edge of the slab
            gp += line((q[3][0] + 2, q[3][1] - 1.5), (q[2][0] - 2, q[2][1] - 1.5), "#08020a", 1.4 * R.scale(ya) ** 0.5, 0.45)
            hot = rng.random()
            if hot < 0.16:  # an ember-lit inlay in a few slabs
                cxm, cym = (q[0][0] + q[2][0]) / 2, (ya + yb) / 2
                sc = R.scale(cym)
                gp += ellipse(cxm, cym, 14 * sc, 3.2 * sc, LAVA, None, op=0.22) + ellipse(cxm, cym, 7 * sc, 1.6 * sc, "#ffd070", None, op=0.4)
        gp += U.neon((-80, yb), (W + 80, yb), "#ff5a1a", 0.7 * R.scale(yb) ** 0.5, 0.35) if j % 3 == 1 else line((-80, yb), (W + 80, yb), "#08020a", 1.6 * R.scale(yb) ** 0.5, 0.8)
    for k in range(24):  # cracks with a lava glint
        xf_ = rng.uniform(-200, 1480)
        ya = rng.uniform(270, H - 60)
        sc = R.scale(ya) * 1.0
        xa = R.floor_x(xf_, ya)
        pts = U.jag((xa, ya), (xa + rng.uniform(-30, 30) * sc, ya + rng.uniform(14, 46) * sc), 4, 7 * sc, rng)
        gp += path(pline(pts), None, "#08020a", 2.0 * sc, sop=0.7)
        if k % 3 == 0:
            gp += path(pline(pts), None, LAVA, 1.0 * sc, sop=0.7)
    # heat from the lake creeping onto the slabs along both side edges
    for side in (-1, 1):
        pts = [PLATFORM[7], PLATFORM[6], PLATFORM[5]] if side < 0 else [PLATFORM[2], PLATFORM[3], PLATFORM[4]]
        inner = [(x - side * 70 * R.scale(y) ** 0.9, y) for x, y in pts]
        gid = "heat%d" % (side + 1)
        defs += lin_grad(gid, [(0, "#ff6a1a", 0.32 if side < 0 else 0.0), (1, "#ff6a1a", 0.0 if side < 0 else 0.32)], 0, 0, 1, 0)
        gp += poly(pts + inner[::-1], f"url(#{gid})")
    ccx, ccy, crx, cry = 640, 372, 250, 46
    gp += ellipse(ccx, ccy, crx * 1.04, cry * 1.12, "#120610", None, op=0.55)  # the seal is a dark inlaid disc
    for rr, op, c, wd in ((1.0, 0.85, EMBER, 2.2), (0.94, 0.5, LAVA, 1.2), (0.62, 0.5, LAVA, 1.2)):
        gp += ellipse(ccx, ccy, crx * rr, cry * rr, None, c, wd, sop=op)
    for k in range(30):
        a = k * math.tau / 30
        gp += line((ccx + math.cos(a) * crx * 0.95, ccy + math.sin(a) * cry * 0.95), (ccx + math.cos(a) * crx * 0.99, ccy + math.sin(a) * cry * 0.99), "#ffd2a0", 1.4 if k % 3 else 2.4, 0.8)
    star = [(ccx + math.cos(math.radians(-90 + k * 144)) * crx * 0.92, ccy + math.sin(math.radians(-90 + k * 144)) * cry * 0.92) for k in range(5)]
    gp += path("M" + " L".join(f"{f(x)} {f(y)}" for x, y in star) + " Z", None, LAVA, 1.4, sop=0.6)
    d += group(gp, 'clip-path="url(#platclip)"')
    # the curb: a low stone parapet round the rim (we see its inner face), gaps where the causeway and bridges land
    def curb(a, b, gaps=(), n=10):
        out = ""
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            tm = (t0 + t1) / 2
            if any(g0 <= tm <= g1 for g0, g1 in gaps):
                continue
            p0 = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
            p1 = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            h0, h1 = 13 * R.scale(p0[1]), 13 * R.scale(p1[1])
            face = [p0, p1, (p1[0], p1[1] - h1), (p0[0], p0[1] - h0)]
            out += poly(face, "#5a2a36" if i % 2 else "#68323e", OUT, 1.8 * R.scale(p0[1]) ** 0.5)
            out += poly([p0, p1, (p1[0], p1[1] - h1 * 0.35), (p0[0], p0[1] - h0 * 0.35)], "#1a0610", None, op=0.45)  # shadow at its foot
            out += line((p0[0], p0[1] - h0), (p1[0], p1[1] - h1), "#ff8a3a", 4.4 * R.scale(p0[1]) ** 0.5, 0.35)  # lava glow over the top
            out += line((p0[0], p0[1] - h0), (p1[0], p1[1] - h1), "#ffd090", 1.8 * R.scale(p0[1]) ** 0.5, 0.95)  # lava-lit coping
            out += line((p0[0], p0[1] - h0 * 0.45), (p1[0], p1[1] - h1 * 0.45), "#08020a", 1.0 * R.scale(p0[1]) ** 0.5, 0.35)
        return out
    rimsegs = [(PLATFORM[5], PLATFORM[6], ()), (PLATFORM[6], PLATFORM[7], ((0.6, 1.0),)), (PLATFORM[7], PLATFORM[0], ((0.0, 0.18),)),
               (PLATFORM[0], PLATFORM[1], ((0.4, 0.6),)), (PLATFORM[1], PLATFORM[2], ((0.82, 1.0),)), (PLATFORM[2], PLATFORM[3], ((0.0, 0.4),)), (PLATFORM[3], PLATFORM[4], ())]
    for a, b, gaps in rimsegs:
        ln = math.hypot(b[0] - a[0], b[1] - a[1])
        d += curb(a, b, gaps, max(4, int(ln / 40)))
    for t, (a, b) in ((0.5, (PLATFORM[6], PLATFORM[7])), (0.55, (PLATFORM[5], PLATFORM[6])), (0.5, (PLATFORM[2], PLATFORM[3])), (0.55, (PLATFORM[3], PLATFORM[4]))):
        x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t  # bone posts with skull lanterns along the side curbs
        sc = R.scale(y) * 0.55
        d += rect(x - 4 * sc, y - 34 * sc, 8 * sc, 34 * sc, BONE, OUT, 1.8)
        d += circle(x, y - 36 * sc, 14 * sc, "#ff7a1a", None, op=0.18) + U.skull(x, y - 38 * sc, 7.5 * sc, BONE, "#ff7a1a", 1.6, jaw=False)
    for (px_, py_) in ((330, 266), (950, 266), (170, 320), (1110, 320)):  # corner skull posts
        d += rect(px_ - 5, py_ - 16, 10, 20, BONE, OUT, 2.0) + U.skull(px_, py_ - 22, 9, BONE, "#ff7a1a", 1.7, jaw=False)
    # ---- amp stacks at the platform's rear corners, with woofer sockets
    woofers = []
    for side, x0 in ((-1, 292), (1, 880)):
        defs_s, body, ws = V.speaker_stack(x0, 276, 108, 150, side, ((0.5, 0.3, 0.2), (0.5, 0.7, 0.3)), ("#5a2a34", "#1a0a16"))
        defs += defs_s
        d += body
        woofers += ws
    # ---- the screen hung over the lake
    d += V.hanging_frame(440, 54, 400, 34, (452, 640, 828), "#3a1a24", top=0)
    # ---- cavern frame: the left and right cliffs, the ceiling mass, lava falls and stalactites
    defs += lin_grad("rock", [(0, "#07020c"), (1, "#2d1220")], 0, 0, 0, 1)
    for side in (-1, 1):
        edge = [(-10, -10)]
        for t in range(0, 11):
            y = t * 36
            inw = 150 - t * 5 + 22 * math.sin(t * 1.3 + (1.3 if side > 0 else 0)) + rng.uniform(-8, 8)
            edge.append((inw, y))
        edge += [(120, 360), (70, 420), (60, 480), (-10, 480)]
        pts = [(x if side < 0 else W - x, y) for x, y in edge]
        d += poly(pts, "url(#rock)", OUT, 3.4)
        d += path(pline([(x if side < 0 else W - x, y) for x, y in edge[1:-4]]), None, "#ff7a2a", 1.6, sop=0.5)
        for kk in range(9):  # lava veins down the cliff face
            x = rng.uniform(10, 150)
            x = x if side < 0 else W - x
            y0 = rng.uniform(20, 150)
            d += U.vein(U.jag((x, y0), (x + rng.uniform(-14, 14), y0 + rng.uniform(50, 130)), 6, 7, rng), LAVA if kk % 2 else EMBER, 1.3, 0.8)
        # the bridge ends at a bone-framed gate in the cliff
        gx = 94 if side < 0 else W - 94
        d += path(f"M{gx - 26} 250 L{gx - 26} 214 Q{gx - 26} 190 {gx} 188 Q{gx + 26} 190 {gx + 26} 214 L{gx + 26} 250 Z", BONE, OUT, 2.6)
        d += path(f"M{gx - 17} 250 L{gx - 17} 216 Q{gx - 17} 200 {gx} 199 Q{gx + 17} 200 {gx + 17} 216 L{gx + 17} 250 Z", "#ff5a1a", OUT, 2.0)
        d += path(f"M{gx - 9} 250 L{gx - 9} 220 Q{gx} 210 {gx + 9} 220 L{gx + 9} 250 Z", "#ffe08a", None, op=0.9)
        d += U.skull(gx, 184, 8, BONE, "#ff7a1a", 1.6, jaw=False)
        # a lava fall off the cliff into the lake
        fx = 48 if side < 0 else W - 48
        d += rect(fx - 8, 160, 16, 120, "#ffb02e", OUT, 2.0, rx=3) + rect(fx - 3, 160, 6, 120, "#fff2a0", None, op=0.8)
        d += ellipse(fx, 282, 34, 7, LAVA, None, op=0.3) + ellipse(fx, 282, 18, 4, "#ffe08a", None, op=0.8)
    ceil = [(0, -10), (W, -10)]
    xs_ = list(range(W, -1, -40))
    for x in xs_:
        ceil.append((x, CE(x) + rng.uniform(-8, 10)))
    d += poly(ceil, "url(#rock)", OUT, 3.0)
    d += U.stalactites(-6, 220, 1060, rng, 14, 54, 16, 40, "#2a0f1c")
    d += path(pline([(x, y) for x, y in ceil[2:]]), None, "#ff7a2a", 1.4, sop=0.45)
    d += V.ceiling_brackets(LIGHTS, "#8a7a82")
    return write_svg("views/pit_backdrop.svg", (0, 0, W, H), d, defs), woofers


def build_front():
    rng = random.Random(17)
    d = ""
    defs = lin_grad("fr", [(0, "#05010a"), (1, "#24101c")], 0, 0, 0, 1)
    # big stalactite tips at the top corners and basalt spikes at the lower corners, rim-lit by the lake
    for side in (-1, 1):
        for k, (x, ln, wd) in enumerate(((20, 88, 46), (78, 128, 52), (150, 60, 36))):
            xx = x if side < 0 else W - x - wd
            d += poly([(xx, -6), (xx + wd / 2 + rng.uniform(-4, 4), ln), (xx + wd, -6)], "url(#fr)", OUT, 3.0)
            d += line((xx + wd * 0.3, 4), (xx + wd / 2, ln - 10), "#ff7a2a", 1.4, 0.45)
        base = 470
        for k, (x, hh, wd) in enumerate(((0, 120, 64), (50, 78, 50), (96, 40, 36))):
            xx = x if side < 0 else W - x - wd
            d += poly([(xx, base), (xx + wd * 0.45 + rng.uniform(-5, 5), base - hh), (xx + wd, base)], "url(#fr)", OUT, 3.0)
            d += line((xx + wd * (0.35 if side < 0 else 0.65), base - hh + 8), (xx + wd * (0.1 if side < 0 else 0.9), base - 8), "#ff7a2a", 1.4, 0.4)
    return write_svg("views/pit_front.svg", (0, 0, W, 470), d, defs)


def build_pieces():
    out = []
    rng = random.Random(91)
    # 1. lava glare: hot spots and bright wave streaks over the lake, pulsing
    w, h = 1280, 84
    d = ""
    for k in range(16):
        cx_ = rng.uniform(40, 1240)
        cy_ = rng.uniform(8, 76)
        sc = (cy_ + 20) / 100.0 + 0.3
        d += ellipse(cx_, cy_, rng.uniform(40, 90) * sc, 9 * sc, "#ff8a2a", None, op=0.14) + ellipse(cx_, cy_, 26 * sc, 4 * sc, "#ffd070", None, op=0.35)
    for k in range(26):
        x = rng.uniform(-20, 1280)
        y = rng.uniform(6, 80)
        sc = (y + 20) / 100.0 + 0.3
        ln = rng.uniform(40, 120) * sc
        d += path(f"M{f(x)} {f(y)} q{f(ln * 0.25)} {f(-3 * sc)} {f(ln * 0.5)} 0 t{f(ln * 0.5)} 0", None, "#fff0b0", 1.6 * sc ** 0.7, sop=0.55)
    write_svg("views/pit_glare.svg", (0, 0, w, h), d)
    out.append(V.piece("pit_lava_glare", "source/views/pit_glare.svg", (0, 190), (w, h), "pulse", "behind", "add", pivot=(w / 2, h / 2)))
    # 2. flame columns rising from the lake at the left and right
    for side in (-1, 1):
        w, h = 200, 300
        d = ""
        for (bx, hh, n) in ((100, 250, 5), (50 if side < 0 else 150, 150, 4), (152 if side < 0 else 48, 120, 4)):
            d += U._flame_cluster(bx, h - 10, hh, rng, n=n, spread=24, w=20)
        for k in range(10):
            d += circle(rng.uniform(30, 170), rng.uniform(10, 200), rng.uniform(1.2, 2.6), "#ffe08a", None, op=0.9)
        name = "pit_plumes_%s" % ("l" if side < 0 else "r")
        write_svg(f"views/{name}.svg", (0, 0, w, h), d)
        cx = 44 if side < 0 else 1236
        out.append(V.piece(name, f"source/views/{name}.svg", (cx - w / 2, 306 - h + 10), (w, h), "flicker", "behind", "add", pivot=(w / 2, h - 10)))
    # 3. the far fortress: windows and gate burning, a halo above
    w, h = 400, 200
    defs = rad_grad("fg", [(0, "#ff7a3a", 0.8), (0.5, "#ff3a1a", 0.3), (1, "#ff3a1a", 0.0)], 0.5, 0.6, 0.5)
    d = ellipse(w / 2, 130, 200, 90, "url(#fg)")
    for k in range(7):
        x = w / 2 + (k - 3) * 22
        d += poly([(x - 4, 190), (x, 70 + abs(k - 3) * 10), (x + 4, 190)], "#ffb070", None, op=0.12)
    d += ellipse(w / 2, 186, 38, 12, "#ffe08a", None, op=0.5)
    write_svg("views/pit_fortress.svg", (0, 0, w, h), defs and d, defs)
    out.append(V.piece("pit_fortress_glow", "source/views/pit_fortress.svg", (640 - w / 2, 64), (w, h), "pulse", "behind", "add", pivot=(w / 2, h * 0.7)))
    return out


def build():
    _, woofers = build_backdrop()
    build_front()
    pieces = build_pieces()
    anchors = {
        "led_screen": [440, 54, 400, 34],
        "doorway": [72, 196, 44, 62],  # the bone gate in the left cliff: arrivals cross the left bridge onto the platform
        "floor_rows": R.rows(),
        "floor_polygon": [[400, 266], [880, 266], [round(R.floor_x(880, 520)), 520], [round(R.floor_x(400, 520)), 520]],  # the lit dance zone
        "floor_grid": R.grid(9),
        "light_points": LIGHTS,
        "woofers": woofers,
        "disco_ball": [640, 0],
        "riser": [640, 266, 620],
        "circle_centre": [640, 372],
        "circle_radii": [250, 46],
        "vanish": [640, HORIZON + 2],
        "horizon_y": HORIZON,
        "wall_left_x": 170, "wall_right_x": 1110,
        "causeway": [640, 267, 640, HORIZON + 2], "bridges": [[196, 316, 110, 240], [1084, 316, 1170, 240]],
    }
    return {"id": "pit", "title": "The lava pit",
            "layers": [V.layer("backdrop", "source/views/pit_backdrop.svg", (0, 0), (W, H)),
                       V.layer("front_frame", "source/views/pit_front.svg", (0, 0), (W, 470), "front")],
            "anchors": anchors, "pieces": pieces, "palette_hint": "hot"}
