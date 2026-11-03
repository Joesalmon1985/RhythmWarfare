"""The `reactor` view: the reactor ring chamber (a glowing core in a containment housing, energy pylons, a catwalk grating floor)."""
from __future__ import annotations

import math
import random

from .lib import OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, poly, rad_grad, rect, write_svg
from .mothership_stage import AMB, CYAN, GREEN, MAG, VIO, glyph, hex_bolt, neon, neon_path, polyhex
from .mothership_views import H, W, Room, floor_anchor, floor_rows, front_edge_frame, lamp, piece, rig_plates

R_ROOM = Room((640, 140), 0.42, -95, 430)
R_LED = (492, 214, 296, 38)
R_CORE = (640, 126, 74)  # cx, cy, r of the containment opening on the far wall
R_LIGHTS = [[130, 34], [290, 34], [450, 34], [830, 34], [990, 34], [1150, 34], [540, 56], [740, 56]]
TEAL0, TEAL1, TEAL2, TEAL3 = "#031a26", "#08324a", "#10506e", "#2a86a8"
PYLONS = [(0.95, 0.78, 36, 172), (0.66, 0.55, 60, 190), (0.5, 0.44, 84, 200)]  # k0, k1, u0, u1 near-frame, mirrored on the right


def hazard(poly_pts_a, poly_pts_b, n, col1=AMB, col2="#0a1020", op=0.95) -> str:
    """Diagonal hazard stripes between two parallel edges (each a pair of points)."""
    (a0, a1), (b0, b1) = poly_pts_a, poly_pts_b
    out = ""
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        p0 = (a0[0] + (a1[0] - a0[0]) * t0, a0[1] + (a1[1] - a0[1]) * t0)
        p1 = (a0[0] + (a1[0] - a0[0]) * t1, a0[1] + (a1[1] - a0[1]) * t1)
        q1 = (b0[0] + (b1[0] - b0[0]) * (t1 + 0.5 / n), b0[1] + (b1[1] - b0[1]) * (t1 + 0.5 / n))
        q0 = (b0[0] + (b1[0] - b0[0]) * (t0 + 0.5 / n), b0[1] + (b1[1] - b0[1]) * (t0 + 0.5 / n))
        if i % 2 == 0:
            out += poly([p0, p1, q1, q0], col1, None, op=op)
    return out


def build_reactor_backdrop() -> dict:
    R = R_ROOM
    kf = R.kf
    rng = random.Random(521)
    sp = (1.0 / kf - 1.0) / 3
    ribs = R.ribs(3, sp)
    d, defs = "", ""
    d += rect(0, 0, W, H, "#02121c")
    # ceiling: dark plating with concentric iris rings above the core
    defs += lin_grad("ceil", [(0, "#010a12"), (1, "#0c3a52")], 0, 0, 0, 1)
    d += poly(R.plane(R.t0, 2.4, kf, -3000, 4300), "url(#ceil)")
    for rr, col, op in ((330, GREEN, 0.55), (250, CYAN, 0.45), (170, GREEN, 0.6)):
        pts = []
        for a in range(0, 61):
            t = a * math.tau / 60
            dd = 1.9 + math.sin(t) * rr / 330 * 0.55  # depth
            pts.append(R.p(1.0 / dd, 640 + math.cos(t) * rr * 1.5, R.t0))
        d += poly(pts, None, col, 2.0, sop=op)
    # walls: armoured plating
    defs += lin_grad("lw", [(0, "#021018"), (1, "#0c4260")], 0, 0, 1, 0)
    defs += lin_grad("rw", [(0, "#0c4260"), (1, "#021018")], 0, 0, 1, 0)
    d += poly(R.wall(0, 1.0, kf, R.t0, R.b0), "url(#lw)") + poly(R.wall(1280, 1.0, kf, R.t0, R.b0), "url(#rw)")
    for side, u in ((-1, 0), (1, 1280)):
        # big coolant pipes along the wall (three heights), with glowing collars at each rib
        for v0, v1, col in ((20, 70, "#10506e"), (110, 170, "#0e4462"), (262, 322, "#10506e")):
            q = R.wall(u, 1.0, kf, v0, v1)
            d += poly(q, col, OUT, 2.6) + poly(R.wall(u, 1.0, kf, v0 + 8, v0 + 14), "#8ad8f0", None, op=0.35)
            d += poly(R.wall(u, 1.0, kf, v1 - 10, v1), "#02101a", None, op=0.45)
            for k in ribs[:-1]:
                kk = k * 0.9
                d += poly(R.wall(u, kk + 0.02, kk - 0.02, v0 - 4, v1 + 4), "#1c6a8c", OUT, 2) + poly(R.wall(u, kk + 0.006, kk - 0.006, v0 - 2, v1 + 2), GREEN, None, op=0.85)
        # caution band at the wall base and a glowing conduit
        d += poly(R.wall(u, 1.0, kf, 362, 400), "#061622", OUT, 2.4)
        d += hazard(*(( R.p(1.0, u, 362), R.p(kf, u, 362)), (R.p(1.0, u, 388), R.p(kf, u, 388))), 22, AMB, "#0a1020", 0.9)
        d += neon(R.p(1.0, u, 214), R.p(kf, u, 214), GREEN if side < 0 else CYAN, 2.0, 0.9)
    # far wall: heavy bulkhead with the containment housing
    fx0, fx1, fy0, fy1 = 371, 909, 41, 262
    defs += lin_grad("fw", [(0, "#10506e"), (0.5, "#08324a"), (1, "#041a28")], 0, 0, 0, 1)
    d += rect(fx0, fy0, fx1 - fx0, fy1 - fy0, "url(#fw)")
    for x in range(fx0 + 10, fx1, 26):
        d += rect(x, fy0, 2.4, fy1 - fy0, "#02101a", None, op=0.5) + rect(x + 2.4, fy0, 1.2, fy1 - fy0, GREEN, None, op=0.07)
    for y in (84, 168):
        d += rect(fx0, y, fx1 - fx0, 6, "#0c3a52", OUT, 2) + line((fx0, y + 1.5), (fx1, y + 1.5), "#8ad8f0", 1.2, 0.4)
    # blast doors left and right with hazard frames
    for dx in (388, 836):
        d += rect(dx, 150, 62, 112, "#041a28", OUT, 2.6, rx=3)
        d += rect(dx + 5, 156, 24, 106, "#10506e", OUT, 2) + rect(dx + 33, 156, 24, 106, "#10506e", OUT, 2)
        d += hazard((( dx, 142), (dx + 62, 142)), ((dx + 12, 150), (dx + 74, 150)), 8, AMB, "#0a1020", 0.95)
        d += lamp(dx + 31, 196, 5, GREEN if dx < 600 else MAG)
    # the core housing: a massive ring with a glowing core
    cx, cy, cr = R_CORE
    defs += rad_grad("core", [(0, "#ffffff"), (0.25, "#d8ffe0"), (0.55, GREEN), (0.85, "#0a8a6a"), (1, "#04324a")], 0.5, 0.5, 0.5)
    defs += rad_grad("coreglow", [(0.6, GREEN, 0.0), (0.8, GREEN, 0.3), (1, GREEN, 0.0)])
    d += circle(cx, cy, cr + 34, "url(#coreglow)")
    d += circle(cx, cy, cr + 22, "#0c3a52", OUT, 3.4)
    for a in range(24):  # armour bolts and segment seams on the housing
        t = a * math.tau / 24
        d += line((cx + math.cos(t) * (cr + 8), cy + math.sin(t) * (cr + 8)), (cx + math.cos(t) * (cr + 22), cy + math.sin(t) * (cr + 22)), OUT, 2)
        d += circle(cx + math.cos(t + 0.13) * (cr + 15), cy + math.sin(t + 0.13) * (cr + 15), 1.6, "#8ad8f0", None, op=0.8)
    d += circle(cx, cy, cr + 6, "#041a28", OUT, 2.6)
    d += circle(cx, cy, cr, "url(#core)", OUT, 2.4)
    for k in range(7):  # energy swirls inside the core
        a0 = k * math.tau / 7
        d += path(f"M{f(cx)} {f(cy)} Q{f(cx + math.cos(a0) * cr * .55 - math.sin(a0) * 20)} {f(cy + math.sin(a0) * cr * .55 + math.cos(a0) * 20)} {f(cx + math.cos(a0 + .9) * cr * .9)} {f(cy + math.sin(a0 + .9) * cr * .9)}", None, "#ffffff", 1.6, sop=0.55)
    d += circle(cx, cy, cr, None, "#b8ffe8", 1.6, sop=0.9) + circle(cx - 18, cy - 20, 8, "#ffffff", None, op=0.9)
    # containment cage: three crossing struts and a gantry under the core
    for a in (0, 60, 120):
        t = math.radians(a)
        d += line((cx - math.cos(t) * (cr + 6), cy - math.sin(t) * (cr + 6)), (cx + math.cos(t) * (cr + 6), cy + math.sin(t) * (cr + 6)), OUT, 3.2) + line((cx - math.cos(t) * (cr + 6), cy - math.sin(t) * (cr + 6)), (cx + math.cos(t) * (cr + 6), cy + math.sin(t) * (cr + 6)), "#5aa8c8", 1.2, 0.6)
    # coolant tubes either side of the core
    for tx in (cx - 112, cx + 112):
        defs += lin_grad(f"tube{int(tx)}", [(0, "#0a8a6a"), (0.5, "#6affc8"), (1, "#0a8a6a")], 0, 0, 1, 0)
        d += rect(tx - 12, fy0, 24, 162, "#041a28", OUT, 2.6, rx=10) + rect(tx - 8, fy0 + 4, 16, 154, f"url(#tube{int(tx)})", None, rx=8, op=0.85)
        for _ in range(7):
            d += circle(tx + rng.uniform(-4, 4), rng.uniform(fy0 + 12, fy0 + 150), rng.uniform(1.2, 2.6), "#ffffff", None, op=0.7)
        for yy in (60, 110, 150):
            d += rect(tx - 15, yy, 30, 6, "#10506e", OUT, 1.8, rx=2)
    d += rect(fx0, 208, fx1 - fx0, 10, "#10506e", OUT, 2.6) + line((fx0, 210.5), (fx1, 210.5), "#8ad8f0", 1.2, 0.5)  # the gantry rail
    for x in range(fx0 + 8, fx1, 28):
        d += line((x, 208), (x, 192), OUT, 3) + line((x, 208), (x, 192), "#5aa8c8", 1.2)
    d += line((fx0, 192), (fx1, 192), OUT, 3.4) + line((fx0, 192), (fx1, 192), "#5aa8c8", 1.4)
    # LED screen frame
    lx, ly, lw_, lh = R_LED
    d += rect(lx - 10, ly - 8, lw_ + 20, lh + 16, "#10506e", OUT, 3.2, rx=6) + rect(lx - 4, ly - 3, lw_ + 8, lh + 6, "#041a28", OUT, 2) + rect(lx, ly, lw_, lh, "#03101c")
    d += neon((lx - 10, ly - 8), (lx + lw_ + 10, ly - 8), GREEN, 1.2, 0.9)
    for cx_, cy_ in ((lx - 4, ly - 3), (lx + lw_ + 4, ly - 3), (lx - 4, ly + lh + 3), (lx + lw_ + 4, ly + lh + 3)):
        d += hex_bolt(cx_, cy_, 3)
    # --- floor: catwalk grating over the glowing reactor pit
    defs += lin_grad("fl", [(0, "#0a4a5a"), (0.35, "#052a3a"), (1, "#021018")], 0, 0, 0, 1)
    d += poly(R.plane(R.b0, 2.4, kf, -3000, 4300), "url(#fl)")
    defs += clip("floorclip", poly(R.plane(R.b0, 2.4, kf, -3000, 4300)))
    defs += rad_grad("pit", [(0, "#d8ffd0", 0.85), (0.35, GREEN, 0.55), (0.7, "#0aa878", 0.28), (1, "#0aa878", 0.0)])
    fl = ellipse(640, 330, 640, 120, "url(#pit)")
    ds = [1.0 / kf - i * 0.16 for i in range(0, 17)]
    for j in range(len(ds) - 1):  # grating windows: glowing cells between dark bars
        da, db = ds[j], ds[j + 1]
        if db <= 0.5:
            break
        ka, kb = 1.0 / da, 1.0 / db
        for u in range(-480, 1760, 72):
            qq = R.plane(R.b0, kb - (kb - ka) * 0.0, ka, u + 9, u + 63)
            qq = [R.p(kb + (ka - kb) * 0.08, u + 9, R.b0), R.p(kb + (ka - kb) * 0.08, u + 63, R.b0), R.p(ka - (ka - kb) * 0.08, u + 63, R.b0), R.p(ka - (ka - kb) * 0.08, u + 9, R.b0)]
            # the pit glows through the grating: bright under the middle of the deck, dark teal toward the walls; a few amber
            # service lamps
            cxm = qq[0][0] * .5 + qq[1][0] * .5
            near = max(0.0, 1.0 - abs(cxm - 640) / 600.0) ** 1.6
            lamp_ = False
            col = AMB if lamp_ else mix("#0b4450", "#5affb4", near)
            fl += poly(qq, col, None, op=0.7 if lamp_ else round(0.22 + 0.5 * near * (1.0 - j / 26.0), 2))
    # bars of the grating (dark) and the main beams
    for u in range(-480, 1760, 72):
        pa, pb = R.p(2.4, u, R.b0), R.p(kf, u, R.b0)
        fl += line(pa, pb, "#02101a", 1.6, 0.35)
    for u in range(-480, 1760, 288):
        fl += line(R.p(2.4, u, R.b0), R.p(kf, u, R.b0), "#5aa8c8", 2.2, 0.55) + line(R.p(2.4, u, R.b0), R.p(kf, u, R.b0), "#02101a", 4, 0.35)
    for dd in ds[::3]:
        fl += line(R.p(1.0 / dd, -1280, R.b0), R.p(1.0 / dd, 2560, R.b0), "#5aa8c8", max(0.8, 2.2 / dd), 0.5)
    # a solid walkway of riveted plate from the camera to the core, with edge lights and chevrons pointing at the core
    defs += lin_grad("walk", [(0, "#1c5a6e"), (0.4, "#0d3242"), (1, "#061c28")], 0, 0, 0, 1)
    fl += poly(R.plane(R.b0, 2.4, kf, 548, 732), "url(#walk)", None, op=0.92)
    for dd in ds[1:14]:
        k = 1.0 / dd
        fl += line(R.p(k, 548, R.b0), R.p(k, 732, R.b0), "#02101a", max(1.0, 2.4 * k), 0.6)
        for u in (566, 714):
            p_ = R.p(k, u, R.b0)
            fl += circle(p_[0], p_[1], max(0.8, 2.2 * k), "#8ad8f0", None, op=0.6)
    for j in range(2, 13, 2):  # chevrons: depth d grows away from the camera, the tip points at the core
        d0 = ds[j]
        pq = lambda dd_, u: R.p(1.0 / dd_, u, R.b0)
        fl += poly([pq(d0, 592), pq(d0 + 0.2, 640), pq(d0, 688), pq(d0 + 0.08, 688), pq(d0 + 0.28, 640), pq(d0 + 0.08, 592)],
                   "#7affc0", None, op=round(0.55 - 0.03 * j, 2))
    for u, col in ((548, GREEN), (732, GREEN)):
        fl += line(R.p(2.4, u, R.b0), R.p(kf, u, R.b0), col, 5, 0.18) + line(R.p(2.4, u, R.b0), R.p(kf, u, R.b0), "#d8ffe8", 1.6, 0.85)
    # the core's reflection on the polished walkway
    defs += lin_grad("refl", [(0, "#e8fff0", 0.42), (0.35, GREEN, 0.16), (1, GREEN, 0.0)], 0, 0, 0, 1)
    fl += poly([R.p(kf, 600, R.b0), R.p(kf, 680, R.b0), R.p(1.5, 760, R.b0), R.p(1.5, 520, R.b0)], "url(#refl)")
    d += group(fl, 'clip-path="url(#floorclip)"')
    # the dance circle: an inlaid hazard ring with a bright inner ring
    cx_c, cy_c, rx_c, ry_c = 640, 372, 250, 46
    d += ellipse(cx_c, cy_c, rx_c + 8, ry_c + 5, "#02101a", None, op=0.55)
    for a in range(0, 40):
        t0, t1 = a * math.tau / 40, (a + 0.5) * math.tau / 40
        d += path(f"M{f(cx_c + rx_c * math.cos(t0))} {f(cy_c + ry_c * math.sin(t0))} A{rx_c} {ry_c} 0 0 1 {f(cx_c + rx_c * math.cos(t1))} {f(cy_c + ry_c * math.sin(t1))}", None, AMB, 5.5, sop=0.95, cap="butt")
    d += ellipse(cx_c, cy_c, rx_c, ry_c, None, "#ffffff", 1.0, sop=0.5) + ellipse(cx_c, cy_c, rx_c * .66, ry_c * .66, None, GREEN, 3, sop=0.9) + ellipse(cx_c, cy_c, rx_c * .66, ry_c * .66, None, "#ffffff", 1.0, sop=0.8)
    d += ellipse(cx_c, cy_c, rx_c * .3, ry_c * .3, None, CYAN, 1.6, sop=0.7)
    # --- ribs: armoured arch frames
    for i, k in enumerate(ribs[:-1]):
        a, b, c, e = R.p(k, 0, R.b0), R.p(k, 0, R.t0), R.p(k, 1280, R.t0), R.p(k, 1280, R.b0)
        dd_ = f"M{f(a[0])} {f(a[1])} L{f(b[0])} {f(b[1])} L{f(c[0])} {f(c[1])} L{f(e[0])} {f(e[1])}"
        w_ = 24 * k
        d += path(dd_, None, OUT, w_ + 6) + path(dd_, None, "#1c6a8c", w_) + path(dd_, None, "#8ad8f0", w_ * .22, sop=0.55)
    # energy pylons (boxes with a glowing core slit, rings and a coil on top)
    defs += lin_grad("pyf", [(0, "#1d6f90"), (0.18, "#12506e"), (0.7, "#0b3a54"), (1, "#05202f")], 0, 0, 1, 0)
    defs += lin_grad("pys", [(0, "#0c4260"), (1, "#03141e")], 0, 0, 1, 0)
    defs += lin_grad("pyt", [(0, "#0a6a54"), (0.3, "#5affb4"), (0.5, "#eafff4"), (0.7, "#5affb4"), (1, "#0a6a54")], 0, 0, 1, 0)
    defs += lin_grad("pyg", [(0, GREEN, 0.0), (0.5, GREEN, 0.26), (1, GREEN, 0.0)], 0, 0, 1, 0)
    for (k0, k1, u0, u1) in PYLONS[::-1]:
        for side in (-1, 1):
            a, b = (u0, u1) if side < 0 else (1280 - u1, 1280 - u0)
            o, fc = R.box(a, b, k0, k1, R.t0 + 20, R.b0, "#2a86a8", "#0e4462", "#06283a", 2.4)
            d += o
            if "side" in fc:  # the inner side: shaded plating and a green spill from the tube
                d += poly(fc["side"], "url(#pys)", OUT, 2.4) + poly(fc["side"], GREEN, None, op=0.1)
                us = b if side < 0 else a
                v0_, v1_ = R.t0 + 20, R.b0
                for t in (0.2, 0.42, 0.64, 0.84):  # the clamp bands wrap round the side
                    vv = v0_ + (v1_ - v0_) * t
                    d += poly(R.wall(us, k0, k1, vv, vv + 9), "#0c3a52", OUT, 1.4) + line(R.p(k0, us, vv + 2), R.p(k1, us, vv + 2), "#8ad8f0", 0.9, 0.45)
                for t in (0.3, 0.55, 0.78):  # recessed side panels with a vent grille
                    vv = v0_ + (v1_ - v0_) * t
                    km = k0 + (k1 - k0) * 0.25
                    kn = k0 + (k1 - k0) * 0.75
                    d += poly(R.wall(us, km, kn, vv - 30, vv - 6), "#04161f", None, op=0.75)
                    for g in range(4):
                        d += line(R.p(km + (kn - km) * 0.1, us, vv - 26 + g * 5.5), R.p(kn - (kn - km) * 0.1, us, vv - 26 + g * 5.5), GREEN, 1.0, 0.4)
                d += poly(R.wall(us, k0, k1, v1_ - 30, v1_ - 18), AMB, None, op=0.35)
            fq = fc["front"]
            d += poly(fq, "url(#pyf)", OUT, 2.4)
            x0_, x1_ = fq[0][0], fq[1][0]
            w_ = x1_ - x0_
            ytop, ybot = max(fq[0][1], -10), fq[3][1]
            # vertical panel seams and rivets
            for s_ in (0.16, 0.84):
                d += line((x0_ + w_ * s_, ytop), (x0_ + w_ * s_, ybot - 12 * k0), "#03141e", 1.4, 0.7)
            for t in (0.1, 0.5, 0.9):
                for s_ in (0.08, 0.92):
                    d += circle(x0_ + w_ * s_, ytop + (ybot - ytop) * t, max(1.0, 1.6 * k0), "#8ad8f0", None, op=0.7)
            # the glass coolant tube: a dark slot, a glowing core with bubbles and a highlight, and a soft halo
            tx0, tw = x0_ + w_ * 0.3, w_ * 0.4
            ty0, ty1 = ytop + 14, ybot - 44 * k0
            d += rect(tx0 - w_ * 0.18, ty0, tw + w_ * 0.36, ty1 - ty0, "url(#pyg)", None, rx=w_ * 0.2)
            d += rect(tx0 - 2, ty0 - 2, tw + 4, ty1 - ty0 + 4, "#02101a", OUT, 1.8, rx=tw * 0.5)
            d += rect(tx0 + 1, ty0 + 2, tw - 2, ty1 - ty0 - 4, "url(#pyt)", None, rx=tw * 0.45, op=0.95)
            for _ in range(int(8 * k0) + 3):
                d += circle(tx0 + tw * rng.uniform(0.25, 0.75), rng.uniform(ty0 + 10, ty1 - 10), tw * rng.uniform(0.06, 0.12), "#ffffff", None, op=0.65)
            d += line((tx0 + tw * 0.22, ty0 + 8), (tx0 + tw * 0.22, ty1 - 8), "#ffffff", max(1.0, tw * 0.08), 0.55)
            for t in (0.2, 0.42, 0.64, 0.84):  # clamp bands
                yy = ytop + (ybot - ytop) * t
                bh = 8 * k0 + 3
                d += rect(x0_ - 1, yy, w_ + 2, bh, "#10506e", OUT, 1.8) + line((x0_, yy + 2), (x1_, yy + 2), "#8ad8f0", 1.0, 0.6)
                d += rect(x0_ + w_ * 0.42, yy + bh * 0.3, w_ * 0.16, bh * 0.4, GREEN if t < 0.5 else AMB, None, op=0.9, rx=1)
            # base: a heavy plinth with hazard stripes and vent slits
            bh = 22 * k0 + 6
            d += rect(x0_ - w_ * 0.08, ybot - bh, w_ * 1.16, bh, "#06283a", OUT, 2)
            d += hazard(((x0_ - w_ * 0.08, ybot - bh), (x0_ + w_ * 1.08, ybot - bh)), ((x0_ - w_ * 0.08, ybot - bh * 0.55), (x0_ + w_ * 1.08, ybot - bh * 0.55)), 10, AMB, "#0a1020", 0.85)
            for s_ in range(4):
                d += rect(x0_ + w_ * (0.14 + s_ * 0.2), ybot - bh * 0.4, w_ * 0.12, bh * 0.18, "#02101a", None, op=0.9, rx=1)
    # light rig: a ring gantry with hazard stripes
    d += rect(60, 0, 1160, 10, "#10506e", OUT, 2) + hazard(((60, 0), (1220, 0)), ((72, 10), (1232, 10)), 54, AMB, "#0a1020", 0.85)
    for xx in (140, 640, 1140):
        d += line((xx, 10), (xx, 20), OUT, 4) + line((xx, 10), (xx, 20), "#5aa8c8", 1.6)
    d += rig_plates(R_LIGHTS)
    return write_svg("views/reactor_backdrop.svg", (0, 0, W, H), d, defs)


def build_reactor_front() -> dict:
    d = ""
    # foreground pipes at both edges, a hazard-striped lintel and chains
    for side in (-1, 1):
        x0 = 0 if side < 0 else W - 44
        d += rect(x0, -4, 44, 480, "#072a3c", OUT, 3.2)
        d += rect(x0 + (4 if side < 0 else 30), -4, 10, 480, "#2a86a8", None, op=0.8)
        d += rect(x0 + 14, -4, 16, 480, GREEN, None, op=0.0)
        for yy in range(30, 460, 70):
            d += rect(x0 - 2, yy, 48, 12, "#10506e", OUT, 2.2, rx=2) + line((x0, yy + 3), (x0 + 44, yy + 3), "#8ad8f0", 1.0, 0.6) + rect(x0 + 8, yy + 38, 28, 5, GREEN, None, op=0.9, rx=2)
        xi = 44 if side < 0 else W - 44
        d += line((xi, 30), (xi, 440), GREEN, 2.0, 0.9) + line((xi, 30), (xi, 440), "#ffffff", 0.8, 0.5)
    d += rect(-4, -4, W + 8, 26, "#072a3c", OUT, 3.2) + hazard(((-4, 0), (W + 4, 0)), ((8, 22), (W + 16, 22)), 60, AMB, "#0a1020", 0.9)
    d += line((44, 22), (W - 44, 22), GREEN, 1.8, 0.9)
    # catwalk handrail corners at the bottom
    for side in (-1, 1):
        xo = 44 if side < 0 else W - 44
        d += path(f"M{xo} 330 L{xo + side * 70} 372 L{xo + side * 70} 462", None, OUT, 8) + path(f"M{xo} 330 L{xo + side * 70} 372 L{xo + side * 70} 462", None, "#5aa8c8", 3.4)
        d += path(f"M{xo} 350 L{xo + side * 70} 392", None, OUT, 6) + path(f"M{xo} 350 L{xo + side * 70} 392", None, "#2a86a8", 2.4)
    return write_svg("views/reactor_front.svg", (0, 0, W, 480), d)


def reactor_pieces() -> list:
    out = []
    cx, cy, cr = R_CORE
    defs = rad_grad("cg", [(0, "#ffffff", 0.35), (0.3, "#b0ffd8", 0.26), (0.65, GREEN, 0.12), (1, GREEN, 0.0)])
    d = circle(cx, cy, 170, "url(#cg)")
    for k in range(10):  # light spokes
        t = k * math.tau / 10 + 0.2
        d += poly([(cx + math.cos(t) * 40, cy + math.sin(t) * 40), (cx + math.cos(t - .07) * 160, cy + math.sin(t - .07) * 160), (cx + math.cos(t + .07) * 160, cy + math.sin(t + .07) * 160)], "#d8ffe8", None, op=0.08)
    out.append(piece("reactor_core_glow", "views/reactor_core_glow.svg", (cx - 170, cy - 130, cx + 170, cy + 130), "pulse", "behind", (cx, cy), "add", d, defs))
    d = ""
    for rr, col, w, arc in ((112, GREEN, 3.4, (0.0, 1.9)), (112, CYAN, 3.4, (3.14, 5.0)), (96, "#ffffff", 1.6, (1.0, 3.2)), (128, GREEN, 2.0, (2.4, 4.4))):
        a0, a1 = arc
        p0 = (cx + rr * math.cos(a0), cy + rr * math.sin(a0))
        p1 = (cx + rr * math.cos(a1), cy + rr * math.sin(a1))
        large = 1 if (a1 - a0) > math.pi else 0
        dd_ = f"M{f(p0[0])} {f(p0[1])} A{rr} {rr} 0 {large} 1 {f(p1[0])} {f(p1[1])}"
        d += path(dd_, None, col, w * 3, sop=0.15) + path(dd_, None, col, w, sop=0.9)
    for k in range(16):
        t = k * math.tau / 16
        d += line((cx + math.cos(t) * 102, cy + math.sin(t) * 102), (cx + math.cos(t) * 108, cy + math.sin(t) * 108), "#ffffff", 1.4, 0.8)
    out.append(piece("reactor_core_ring", "views/reactor_core_ring.svg", (cx - 140, cy - 140, cx + 140, cy + 140), "rotate", "behind", (cx, cy), "add", d))
    # arcing lightning between the pylon tops and the housing
    rng = random.Random(77)
    d = ""
    for (xa, ya, xb, yb) in ((330, 54, 566, 100), (950, 54, 714, 100), (330, 70, 950, 70)):
        pts = [(xa, ya)]
        n = 9
        for i in range(1, n):
            t = i / n
            pts.append((xa + (xb - xa) * t, ya + (yb - ya) * t + rng.uniform(-10, 10) - (14 * math.sin(t * math.pi) if ya == yb else 0)))
        pts.append((xb, yb))
        dd_ = "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts)
        d += path(dd_, None, GREEN, 7, sop=0.12) + path(dd_, None, "#d8ffe8", 1.8, sop=0.9)
    out.append(piece("reactor_pylon_arcs", "views/reactor_pylon_arcs.svg", (310, 30, 970, 120), "flicker", "behind", (640, 75), "add", d))
    # coolant vents venting glowing steam beside the near pylon plinths (additive, flickers)
    rng = random.Random(915)
    defs = rad_grad("st", [(0, "#e8fff4", 0.34), (0.6, GREEN, 0.12), (1, GREEN, 0.0)])
    d = ""
    for (vx, vy) in ((236, 392), (1044, 392), (330, 300), (950, 300)):
        sc = 1.0 if vy > 350 else 0.62
        for i in range(7):
            t = i / 6
            d += ellipse(vx + rng.uniform(-8, 8) * sc + (t * 18 * sc if vx < 640 else -t * 18 * sc), vy - t * 170 * sc,
                         (22 + 46 * t) * sc, (16 + 26 * t) * sc, "url(#st)")
        d += ellipse(vx, vy + 2, 24 * sc, 5 * sc, "#bfffe0", None, op=0.5)
    out.append(piece("reactor_steam", "views/reactor_steam.svg", (150, 150, 1130, 410), "flicker", "behind", (640, 300), "add", d, defs))
    return out


def reactor_view() -> dict:
    build_reactor_backdrop()
    build_reactor_front()
    poly_, grid = floor_anchor((640, 140), 262, 400, 880)
    anchors = {
        "floor_rows": floor_rows(140), "floor_polygon": poly_, "floor_grid": grid, "light_points": R_LIGHTS,
        "led_screen": list(R_LED), "circle_centre": [640, 372], "circle_radii": [250, 46], "horizon_y": 140, "vanish": [640, 140],
        "disco_ball": [640, 0], "wall_left_x": 371, "wall_right_x": 909, "core": list(R_CORE),
        "doorway": [388, 150, 62, 112],  # the left blast door: late arrivals walk in from here
    }
    return {"id": "reactor", "title": "Reactor ring chamber",
            "layers": [{"id": "backdrop", "file": "source/views/reactor_backdrop.svg", "pos": [0, 0], "size": [W, H], "px_scale": 0.5},
                       {"id": "front_frame", "file": "source/views/reactor_front.svg", "pos": [0, 0], "size": [W, 480], "px_scale": 0.5, "z": "front"}],
            "anchors": anchors, "pieces": reactor_pieces(), "palette_hint": "green"}
