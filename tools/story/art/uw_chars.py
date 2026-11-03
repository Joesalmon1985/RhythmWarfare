"""The six demon dancers of the Underworld chapter: same rig/face contract as Night One (chars.py), different anatomy.

Archetypes: imp, brute, fiend, skeleton, flame, horned_queen; variants a and b (palette + one clothing/detail change).
Parts are drawn at the rest pose in rig space (origin between the feet, +y down). Swinging extras (imp tail, fiend wings,
flame hair, queen cape) are parts with `swing: true` exactly like Night One's ponytail.
"""
from __future__ import annotations

import math

from . import chars as C
from .lib import (OUT, capsule, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, pivot_in, poly,
                  rad_grad, rect, write_svg)

RIM_L, RIM_R = "#ffa02e", "#ff2f9d"
INK = "#2a0a1e"

ARCH = {
    "imp": dict(hip_y=68, sh_y=-124, sh_dx=17, neck_y=-130, cy=-158, rx=31, ry=29, up=25, fore=26, aw=11, sw=19, ww=16, hw=18,
                lw=13, leg_dx=9, shoe_h=9),
    "brute": dict(hip_y=96, sh_y=-176, sh_dx=45, neck_y=-184, cy=-212, rx=31, ry=28, up=44, fore=42, aw=24, sw=47, ww=37, hw=35,
                  lw=26, leg_dx=18, shoe_h=15),
    "fiend": dict(hip_y=118, sh_y=-196, sh_dx=26, neck_y=-205, cy=-231, rx=22, ry=27, up=45, fore=47, aw=12, sw=26, ww=17, hw=20,
                  lw=14, leg_dx=10, shoe_h=11),
    "skeleton": dict(hip_y=104, sh_y=-182, sh_dx=24, neck_y=-190, cy=-216, rx=24, ry=27, up=40, fore=42, aw=9, sw=22, ww=16,
                     hw=17, lw=10, leg_dx=11, shoe_h=9),
    "flame": dict(hip_y=100, sh_y=-180, sh_dx=26, neck_y=-188, cy=-212, rx=23, ry=26, up=40, fore=42, aw=14, sw=27, ww=20, hw=22,
                  lw=17, leg_dx=11, shoe_h=8),
    "horned_queen": dict(hip_y=108, sh_y=-186, sh_dx=25, neck_y=-196, cy=-222, rx=22, ry=26, up=41, fore=44, aw=12, sw=26, ww=17,
                         hw=22, lw=14, leg_dx=11, shoe_h=14),
}

VARIANTS = {
    "imp": {
        "a": dict(skin="#ff5a4a", skin2="#ffb28a", horn="#ffe9a8", cloth="#7a3cff", cloth2="#d9c4ff", accent="#ffc23f", iris="#ffe14a", detail="vest"),
        "b": dict(skin="#9a5cff", skin2="#e0c4ff", horn="#ff9ad0", cloth="#19c8e8", cloth2="#ffffff", accent="#ff2f9d", iris="#7dff6a", detail="stripes"),
    },
    "brute": {
        "a": dict(skin="#c42a3c", skin2="#e8566a", horn="#efe2c0", cloth="#3a2a30", cloth2="#6a5058", accent="#ffb02e", iris="#ffd23f", detail="harness",
                  pd="#6e5a72", pd_trim="#ffb02e", pd_spike="#efe2c0"),
        "b": dict(skin="#4f74c4", skin2="#86a6ea", horn="#ffd23f", cloth="#2a2440", cloth2="#5a4a80", accent="#ff6a2e", iris="#ff5a4a", detail="plate",
                  pd="#ff7a2e", pd_trim="#ffd23f", pd_spike="#fff0c8"),
    },
    "fiend": {
        "a": dict(skin="#8d3fd0", skin2="#b97af0", horn="#f2dcff", cloth="#1d1240", cloth2="#f4e6ff", accent="#ff2f9d", iris="#ffe14a", hair="#150a2a",
                  wing="#6a1f7a", sleeve="#5b2fa0", detail="bowtie"),
        "b": dict(skin="#cdb4ff", skin2="#efe4ff", horn="#ff6a2e", cloth="#c4163c", cloth2="#fff0d8", accent="#ffc23f", iris="#ff4a4a", hair="#ff2f9d",
                  wing="#3a1a70", sleeve="#c4163c", detail="tie"),
    },
    "skeleton": {
        "a": dict(skin="#f4ecd0", skin2="#d8caa0", cloth="#ff2f9d", cloth2="#ffe14a", accent="#ffc23f", iris="#ff7a2e", detail="hat"),
        "b": dict(skin="#d6f0e8", skin2="#a8d4c8", cloth="#2fe08a", cloth2="#ffffff", accent="#ff6a2e", iris="#4fff9a", detail="bow"),
    },
    "flame": {
        "a": dict(skin="#ff7a1a", skin2="#ffe45a", cloth="#2a1030", cloth2="#ff4a1a", accent="#ffb02e", fl1="#ff3a1a", fl2="#ff9a1a", fl3="#fff29a", iris="#7a1010", detail="shorts"),
        "b": dict(skin="#5a6cff", skin2="#9ff0ff", cloth="#1a0a2a", cloth2="#7a3cff", accent="#3ac8ff", fl1="#7a3cff", fl2="#3a8cff", fl3="#e6fbff", iris="#1a1060", detail="scarf"),
    },
    "horned_queen": {
        "a": dict(skin="#ff3fa0", skin2="#ff8cc8", horn="#ffd23f", cloth="#1b1040", cloth2="#ffc23f", accent="#ff2f4a", cape="#ff2f4a", lining="#ff2f9d",
                  hair="#1a0a2e", iris="#ffe14a", detail="bare"),
        "b": dict(skin="#e9d4ff", skin2="#fff0ff", horn="#d8e0ff", cloth="#c4163c", cloth2="#ffe9a8", accent="#ffb02e", cape="#3a1a70", lining="#ffb02e",
                  hair="#f4f0ff", iris="#ff4a4a", detail="gloves"),
    },
}
EXPRESSIONS = C.EXPRESSIONS


def bb(points, pad=8.0):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def bez(p0, p1, p2, n=16):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in [i / (n - 1) for i in range(n)]]


def taper(center, w0, w1):
    """Polygon around a centre line with linearly tapering width."""
    n = len(center)
    left, right = [], []
    for i, (x, y) in enumerate(center):
        a = center[max(i - 1, 0)]
        b = center[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return left + right[::-1], left, right


def horn(center, w0, w1, color, rings=4, sw=3.0):
    poly_pts, left, right = taper(center, w0, w1)
    out = poly(poly_pts, color, OUT, sw)
    n = len(center)
    hl = [(left[i][0] * 0.7 + center[i][0] * 0.3, left[i][1] * 0.7 + center[i][1] * 0.3) for i in range(n)]
    out += path("M" + " L".join(f"{f(x)} {f(y)}" for x, y in hl[1:n - 2]), None, lighten(color, 0.55), 1.8, sop=0.8)
    for k in range(1, rings + 1):
        i = int(k * (n - 2) / (rings + 1)) + 1
        out += line(left[i], right[i], darken(color, 0.38), 1.5, 0.8)
    return out


def flame_path(bx, by, tx, ty, w, bend=0.0):
    mx, my = bx + (tx - bx) * 0.5, by + (ty - by) * 0.55
    return (f"M{f(bx - w)} {f(by)} Q{f(bx - w * 0.5 + bend * 0.3)} {f(my)} {f(tx)} {f(ty)} "
            f"Q{f(bx + w * 0.9 + bend)} {f(by + (ty - by) * 0.4)} {f(bx + w)} {f(by)} Q{f(bx)} {f(by + w * 0.7)} {f(bx - w)} {f(by)} Z")


def flame_layer(bx, by, tx, ty, w, bend, cols, sw=2.6):
    """A flame tongue with nested hotter cores (cols = outer, mid, core)."""
    out = path(flame_path(bx, by, tx, ty, w, bend), cols[0], OUT, sw)
    out += path(flame_path(bx, by - 1, bx + (tx - bx) * 0.9, by + (ty - by) * 0.78, w * 0.66, bend * 0.7), cols[1], None)
    out += path(flame_path(bx, by - 2, bx + (tx - bx) * 0.75, by + (ty - by) * 0.52, w * 0.34, bend * 0.5), cols[2], None)
    return out


# ---- torso -------------------------------------------------------------------------------------------------------------

def torso_wrap(P, base, inner, outer="", flare=0.0, defs_extra=""):
    sw = P["sw"]
    ts = P["sh_y"] - 8
    by = -P["hip_y"] + 14
    d = C.torso_outline(P, flare)
    defs = clip("tc", f'<path d="{d}"/>') + C.SHADE_GRAD + defs_extra
    body = f'<path d="{d}" fill="{base}"/>' + group(inner, 'clip-path="url(#tc)"')
    shade = f'<rect x="{f(-sw - 8)}" y="{f(ts - 6)}" width="{f(sw * 2 + 16)}" height="{f(by - ts + 12)}" fill="url(#shd)"/>'
    rim_l = f'<rect x="{f(-sw - 3)}" y="{f(ts - 6)}" width="5" height="{f(by - ts + 12)}" fill="{RIM_L}" fill-opacity="0.5"/>'
    rim_r = f'<rect x="{f(sw - 2)}" y="{f(ts - 6)}" width="5" height="{f(by - ts + 12)}" fill="{RIM_R}" fill-opacity="0.38"/>'
    body += group(shade + rim_l + rim_r, 'clip-path="url(#tc)"')
    body += path(d, None, OUT, 3)
    body += outer
    return defs, body, (-sw - 30, ts - 24, sw + 30, by + 24)


def torso_part(arch, P, V):
    sw, ww, hw = P["sw"], P["ww"], P["hw"]
    ts = P["sh_y"] - 8
    wy = -P["hip_y"] - 34
    by = -P["hip_y"] + 14
    skin, skin2, acc = V["skin"], V["skin2"], V["accent"]
    inner, outer, base, flare, dx = "", "", skin, 0.0, ""
    if arch == "imp":
        flare = 3
        inner += ellipse(0, by - 24, ww + 2, 24, skin2, None, op=0.95)
        inner += path(f"M-6 {f(by - 36)} Q0 {f(by - 32)} 6 {f(by - 36)}", None, darken(skin2, 0.3), 1.6)
        if V["detail"] == "vest":
            vest = V["cloth"]
            inner += poly([(-sw - 3, ts - 4), (-8, ts - 4), (-5, by - 30), (-hw - 6, by - 30)], vest, OUT, 2.2)
            inner += poly([(sw + 3, ts - 4), (8, ts - 4), (5, by - 30), (hw + 6, by - 30)], vest, OUT, 2.2)
            for k in range(3):
                inner += circle(-3.5, ts + 14 + k * 11, 2.0, acc, OUT, 1) + circle(3.5, ts + 14 + k * 11, 2.0, acc, OUT, 1)
        else:
            base = V["cloth"]
            for k in range(7):
                inner += rect(-sw - 4, ts + 6 + k * 11, sw * 2 + 8, 5, V["cloth2"], None, op=0.9)
            inner += ellipse(0, ts + 1, 11, 6, skin, OUT, 2)
    elif arch == "brute":
        inner += path(f"M{f(-ww)} {f(ts + 22)} Q{f(-ww * 0.4)} {f(ts + 40)} 0 {f(ts + 30)} Q{f(ww * 0.4)} {f(ts + 40)} {f(ww)} {f(ts + 22)}", None, darken(skin, 0.38), 2.4)
        for k in range(3):
            inner += line((0, ts + 36 + k * 11), (0, ts + 40 + k * 11), darken(skin, 0.35), 2)
            inner += path(f"M-12 {f(ts + 42 + k * 11)} Q-4 {f(ts + 46 + k * 11)} 0 {f(ts + 42 + k * 11)} Q4 {f(ts + 46 + k * 11)} 12 {f(ts + 42 + k * 11)}", None, darken(skin, 0.3), 1.8, sop=0.7)
        inner += ellipse(0, by - 16, ww, 24, skin2, None, op=0.22)
        if V["detail"] == "harness":
            st = V["cloth"]
            inner += poly([(-sw + 6, ts - 4), (-sw + 20, ts - 4), (sw - 4, by - 28), (sw - 18, by - 28)], st, OUT, 2.2)
            inner += poly([(sw - 6, ts - 4), (sw - 20, ts - 4), (-sw + 4, by - 28), (-sw + 18, by - 28)], st, OUT, 2.2)
            for k in range(4):
                for sgn in (-1, 1):
                    inner += circle(sgn * (sw - 14 - k * 9.5), ts + 8 + k * 14.5, 2.1, acc, OUT, 1)
            inner += circle(0, ts + 36, 8.5, V["horn"], OUT, 2) + ellipse(-3, ts + 35, 2.2, 2.8, INK) + ellipse(3, ts + 35, 2.2, 2.8, INK)
        else:
            plate = path(f"M{f(-sw - 3)} {f(ts - 2)} L{f(sw + 3)} {f(ts - 2)} L{f(ww + 4)} {f(ts + 48)} L{f(-ww - 4)} {f(ts + 48)} Z", acc, OUT, 2.6)
            inner += plate
            inner += path(f"M{f(-sw + 6)} {f(ts + 8)} L{f(sw - 6)} {f(ts + 8)}", None, lighten(acc, 0.5), 2, sop=0.8)
            inner += line((0, ts + 8), (0, ts + 46), darken(acc, 0.35), 2.2)
            for sgn in (-1, 1):
                inner += circle(sgn * (sw - 9), ts + 6, 2.2, lighten(acc, 0.6), OUT, 1) + circle(sgn * (ww - 2), ts + 40, 2.2, lighten(acc, 0.6), OUT, 1)
        outer += ""
    elif arch == "fiend":
        base = V["cloth2"]
        vest = V["cloth"]
        inner += poly([(-sw - 3, ts - 4), (-6, ts - 4), (0, by - 4), (-hw - 6, by + 2)], vest, OUT, 2.4)
        inner += poly([(sw + 3, ts - 4), (6, ts - 4), (0, by - 4), (hw + 6, by + 2)], vest, OUT, 2.4)
        inner += poly([(-6, ts - 4), (-17, ts + 2), (-8, ts + 24), (-1, ts + 14)], lighten(vest, 0.18), OUT, 2)
        inner += poly([(6, ts - 4), (17, ts + 2), (8, ts + 24), (1, ts + 14)], lighten(vest, 0.18), OUT, 2)
        for k in range(3):
            inner += circle(-5.5 if k % 2 == 0 else 5.5, ts + 34 + k * 11, 1.8, V["accent"], OUT, 1)
        for k in range(-3, 4):  # pinstripes
            inner += line((k * 6.5 - 20, ts + 20), (k * 6.5 - 21, by), lighten(vest, 0.18), 1.2, 0.5)
        if V["detail"] == "bowtie":
            inner += poly([(0, ts + 4), (-11, ts - 3), (-11, ts + 11)], V["accent"], OUT, 1.8) + poly([(0, ts + 4), (11, ts - 3), (11, ts + 11)], V["accent"], OUT, 1.8) + circle(0, ts + 4, 3, darken(V["accent"], 0.3), OUT, 1.4)
        else:
            inner += poly([(-3, ts + 1), (3, ts + 1), (6, ts + 34), (0, ts + 42), (-6, ts + 34)], V["accent"], OUT, 1.8)
        inner += poly([(sw - 12, ts + 30), (sw - 4, ts + 30), (sw - 4, ts + 36), (sw - 12, ts + 36)], V["accent"], None, op=0.95)
    elif arch == "skeleton":
        base = "#2b1030"
        bone = skin
        for sgn in (-1, 1):  # collarbones
            inner += line((0, ts + 4), (sgn * (sw - 2), ts + 2), OUT, 7) + line((0, ts + 4), (sgn * (sw - 2), ts + 2), bone, 4)
        inner += line((0, ts + 2), (0, by - 4), OUT, 8) + line((0, ts + 2), (0, by - 4), skin2, 5)
        for k in range(8):
            inner += circle(0, ts + 12 + k * 8.4, 3.6, bone, OUT, 1.6)
        for k in range(5):
            y0 = ts + 12 + k * 11
            wr = ww + 6 - abs(k - 1) * 0.5 - k * 0.8
            for sgn in (-1, 1):
                dd = f"M{f(sgn * 3)} {f(y0)} Q{f(sgn * wr)} {f(y0 - 5)} {f(sgn * (wr + 1))} {f(y0 + 12)}"
                inner += path(dd, None, OUT, 8.4) + path(dd, None, bone, 5.0)
        inner += f'<rect x="{f(-sw)}" y="{f(ts)}" width="{f(sw * 2)}" height="{f(by - ts)}" fill="#ff7a2e" fill-opacity="0.07"/>'
        if V["detail"] == "bow":
            outer += poly([(0, ts + 5), (-12, ts - 2), (-12, ts + 12)], V["accent"], OUT, 1.8) + poly([(0, ts + 5), (12, ts - 2), (12, ts + 12)], V["accent"], OUT, 1.8) + circle(0, ts + 5, 3.2, darken(V["accent"], 0.3), OUT, 1.4)
    elif arch == "flame":
        gid = "fb"
        dx = lin_grad(gid, [(0, skin2), (0.45, skin), (1, darken(skin, 0.2))], 0, 0, 0, 1)
        base = f"url(#{gid})"
        inner += ellipse(0, ts + 34, ww - 2, 26, skin2, None, op=0.75)
        inner += ellipse(0, ts + 38, ww - 8, 16, "#ffffff", None, op=0.35)
        for k in range(3):
            inner += path(f"M-9 {f(ts + 56 + k * 9)} Q0 {f(ts + 60 + k * 9)} 9 {f(ts + 56 + k * 9)}", None, darken(skin, 0.35), 1.8, sop=0.6)
        if V["detail"] == "scarf":
            outer += path(f"M{f(-15)} {f(ts + 2)} Q0 {f(ts + 14)} 15 {f(ts + 2)} L13 {f(ts + 12)} Q0 {f(ts + 24)} -13 {f(ts + 12)} Z", V["cloth2"], OUT, 2.4)
            outer += path(f"M10 {f(ts + 12)} L16 {f(ts + 44)} L7 {f(ts + 40)} L3 {f(ts + 16)} Z", V["cloth2"], OUT, 2.2)
        else:
            outer += circle(0, ts + 12, 5, V["fl3"], OUT, 1.8) + circle(0, ts + 12, 2.2, V["fl1"])
    elif arch == "horned_queen":
        dress = V["cloth"]
        base = dress
        inner += poly([(-14, ts - 4), (14, ts - 4), (0, ts + 30)], skin, OUT, 2)  # plunging neckline
        inner += path(f"M-14 {f(ts - 3)} L0 {f(ts + 30)} L14 {f(ts - 3)}", None, V["cloth2"], 2.4)
        for k in range(5):
            y = ts + 32 + k * 8
            inner += line((-10, y), (10, y + 8), V["cloth2"], 1.4, 0.85) + line((10, y), (-10, y + 8), V["cloth2"], 1.4, 0.85)
        inner += line((-ww + 2, ts + 26), (-ww + 2, by - 18), V["cloth2"], 2, 0.7) + line((ww - 2, ts + 26), (ww - 2, by - 18), V["cloth2"], 2, 0.7)
        inner += rect(-hw - 4, by - 18, hw * 2 + 8, 8, V["cloth2"], OUT, 2, rx=2)
        inner += poly([(0, by - 20), (5, by - 14), (0, by - 8), (-5, by - 14)], V["accent"], OUT, 1.6)
        inner += circle(-sw + 5, ts + 6, 7, V["cloth2"], OUT, 2) + circle(sw - 5, ts + 6, 7, V["cloth2"], OUT, 2)  # shoulder studs
        outer += path(f"M-9 {f(ts + 1)} Q0 {f(ts + 10)} 9 {f(ts + 1)}", None, V["cloth2"], 3.4)  # choker
    return torso_wrap(P, base, inner, outer, flare, dx)


def pelvis_part(arch, P, V):
    hy = -P["hip_y"]
    hw = P["hw"] + 1
    skin, acc = V["skin"], V["accent"]
    if arch == "horned_queen":
        return None
    if arch == "skeleton":
        bone = skin
        d = (f"M{f(-hw - 2)} {f(hy - 10)} Q{f(-hw - 6)} {f(hy + 4)} {f(-hw + 3)} {f(hy + 14)} Q{f(-4)} {f(hy + 9)} 0 {f(hy + 17)} "
             f"Q{f(4)} {f(hy + 9)} {f(hw - 3)} {f(hy + 14)} Q{f(hw + 6)} {f(hy + 4)} {f(hw + 2)} {f(hy - 10)} Z")
        body = path(d, bone, OUT, 3)
        body += ellipse(-9, hy + 3, 3.4, 4.4, "#2b1030", OUT, 1.4) + ellipse(9, hy + 3, 3.4, 4.4, "#2b1030", OUT, 1.4)
        body += line((-hw + 2, hy - 7), (hw - 2, hy - 7), darken(bone, 0.25), 2, 0.7)
        return body, (-hw - 12, hy - 16, hw + 12, hy + 26)
    cloth = V["cloth"]
    if arch == "flame":
        cloth = V["cloth"]
    if arch == "brute":
        cloth = V["cloth"]
    if arch == "fiend":
        cloth = V["cloth"]
    if arch == "imp":
        cloth = V["cloth"]
    d = f"M{f(-hw)} {f(hy - 12)} L{f(hw)} {f(hy - 12)} L{f(hw + 1)} {f(hy + 12)} Q0 {f(hy + 22)} {f(-hw - 1)} {f(hy + 12)} Z"
    body = path(d, cloth, OUT, 3)
    body += line((-hw + 2, hy - 8), (hw - 2, hy - 8), darken(cloth, 0.35), 3, 0.8)
    if arch == "brute":
        body = path(f"M{f(-hw - 3)} {f(hy - 12)} L{f(hw + 3)} {f(hy - 12)} L{f(hw + 4)} {f(hy + 10)} Q0 {f(hy + 20)} {f(-hw - 4)} {f(hy + 10)} Z", cloth, OUT, 3)
        body += rect(-hw - 4, hy - 14, hw * 2 + 8, 9, acc, OUT, 2.2, rx=2)
        body += circle(0, hy - 9.5, 4.4, V["horn"], OUT, 1.6)
        body += poly([(-8, hy + 2), (8, hy + 2), (0, hy + 24)], darken(cloth, 0.1), OUT, 2.2) + circle(0, hy + 9, 2.2, acc)
    elif arch == "flame":
        body += line((-hw + 2, hy + 10), (hw - 2, hy + 10), V["cloth2"], 2.6, 0.95)
    elif arch == "imp":
        body += line((-hw + 2, hy + 6), (hw - 2, hy + 6), acc, 2.4, 0.9)
    elif arch == "fiend":
        body += line((0, hy - 8), (0, hy + 12), darken(cloth, 0.4), 2, 0.6)
        body += line((-hw + 2, hy - 8), (hw - 2, hy - 8), V["accent"], 3, 0.9)
    return body, (-hw - 12, hy - 18, hw + 12, hy + 30)


def skirt_part(P, V):
    hy = -P["hip_y"]
    top = hy - 16
    bot = hy + 40
    w0, w1 = P["hw"] - 1, P["hw"] + 17
    n = 7
    pts = []
    for k in range(n + 1):  # scalloped flame hem
        x = -w1 + k * (2 * w1 / n)
        pts.append((x, bot + (7 if k % 2 == 0 else -2)))
    d = f"M{f(-w0)} {f(top)} L{f(w0)} {f(top)} L{f(w1 + 2)} {f(bot)} " + " ".join(f"L{f(x)} {f(y)}" for x, y in reversed(pts)) + f" L{f(-w1 - 2)} {f(bot)} Z"
    c = V["cloth"]
    defs = clip("sc", f'<path d="{d}"/>')
    body = f'<path d="{d}" fill="{c}"/>'
    inner = ""
    for k in range(-4, 5):
        inner += line((k * 4.5, top), (k * 7.2, bot + 6), darken(c, 0.35), 1.6, 0.55)
    inner += rect(-w1 - 4, bot - 8, w1 * 2 + 8, 6, V["cloth2"], None, op=0.95)
    inner += rect(w0 * 0.3, top, w1, bot - top + 12, "#150a33", None, op=0.2)
    inner += poly([(-w1 * 0.1, top), (w1 * 0.5, top), (w1 * 0.8, bot + 6), (w1 * 0.2, bot + 6)], V["accent"], None, op=0.0)
    body += group(inner, 'clip-path="url(#sc)"')
    body += path(d, None, OUT, 3)
    return defs, body, (-w1 - 10, top - 8, w1 + 10, bot + 18)


# ---- limbs -------------------------------------------------------------------------------------------------------------

def sleeve(arch, V, part):
    if arch == "fiend":
        return V["sleeve"]
    if arch == "horned_queen" and part == "fore" and V["detail"] == "gloves":
        return V["cloth"]
    return None


def claws(hc, ux, uy, nx, ny, hr, color):
    out = ""
    for k in (-1, 0, 1):
        bx, by = hc[0] + ux * hr * 0.55 + nx * k * hr * 0.55, hc[1] + uy * hr * 0.55 + ny * k * hr * 0.55
        tip = (bx + ux * (hr * 0.95) + nx * k * 1.2, by + uy * (hr * 0.95) + ny * k * 1.2)
        out += poly([(bx - nx * 1.7, by - ny * 1.7), tip, (bx + nx * 1.7, by + ny * 1.7)], color, OUT, 1.3)
    return out


def arm_parts(arch, P, V, J, side):
    name = "l" if side < 0 else "r"
    s = J["shoulder_" + name]
    e = J["elbow_" + name]
    w = C.wrist(P, J, side)
    aw = P["aw"]
    skin = V["skin"]
    out = {}
    sl = sleeve(arch, V, "up")
    c = sl or skin
    dx, dy = e[0] - s[0], e[1] - s[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    body = line(s, e, OUT, aw + 6, cap="butt") + circle(s[0], s[1], aw / 2 + 3, OUT)
    body += line(s, e, c, aw, cap="round")
    o = aw * 0.24 * side
    body += line((s[0] + nx * o, s[1] + ny * o), (e[0] + nx * o, e[1] + ny * o), darken(c, 0.25), aw * 0.4, 0.7)
    o2 = -aw * 0.26 * side
    body += line((s[0] + nx * o2, s[1] + ny * o2), (e[0] + nx * o2, e[1] + ny * o2), lighten(c, 0.3), aw * 0.14, 0.65)
    box_up = bb([s, e], aw / 2 + 24)
    if arch == "skeleton":
        body = line(s, e, OUT, aw + 5, cap="butt") + circle(s[0], s[1], aw * 0.75 + 2.6, OUT)
        body += line(s, e, skin, aw, cap="round") + circle(s[0], s[1], aw * 0.75, skin)
        body += line((s[0] + nx * o2, s[1] + ny * o2), (e[0] + nx * o2, e[1] + ny * o2), lighten(skin, 0.4), 1.8, 0.8)
        body += line((s[0] + nx * o, s[1] + ny * o), (e[0] + nx * o, e[1] + ny * o), V["skin2"], 2.4, 0.8)
    elif arch == "brute":  # a bulging deltoid; the armoured pauldron itself is a separate part fixed to the torso
        r = aw * 0.62 + 3
        body += circle(s[0], s[1], r + 3, OUT) + circle(s[0], s[1], r, skin)
        body += circle(s[0] - side * r * 0.3, s[1] - r * 0.25, r * 0.45, lighten(skin, 0.3), None, op=0.55)
        body += line(s, e, skin, aw, cap="round")
        body += line((s[0] + nx * o, s[1] + ny * o), (e[0] + nx * o, e[1] + ny * o), darken(skin, 0.25), aw * 0.4, 0.7)
        box_up = bb([s, e], aw / 2 + 12)
    elif arch == "imp" and V["detail"] == "stripes":
        pass
    elif arch == "fiend":
        m = (s[0] + dx * 0.5, s[1] + dy * 0.5)
        body += circle(s[0], s[1], aw / 2 + 1.5, lighten(V["sleeve"], 0.12), OUT, 2.0)  # padded jacket shoulder
        body += line((s[0] - nx * side * aw * 0.32, s[1] - ny * side * aw * 0.32), (m[0] - nx * side * aw * 0.32, m[1] - ny * side * aw * 0.32), V["accent"], 1.4, 0.6)  # pinstripe
    elif arch == "flame":  # a hot core down the limb and a little flame licking off the shoulder
        body += line(s, e, V["skin2"], aw * 0.34, 0.6) + line(s, e, "#ffffff", aw * 0.12, 0.35)
        body += flame_layer(s[0] + side * 3, s[1] - 2, s[0] + side * 12, s[1] - 24, 6, side * 5, (V["fl1"], V["fl2"], V["fl3"]), 2.0)
        box_up = bb([s, e, (s[0] + side * 14, s[1] - 28)], aw / 2 + 8)
    elif arch == "horned_queen":
        m = (s[0] + dx * 0.78, s[1] + dy * 0.78)
        body += line((m[0] - nx * (aw / 2 + 1), m[1] - ny * (aw / 2 + 1)), (m[0] + nx * (aw / 2 + 1), m[1] + ny * (aw / 2 + 1)), V["cloth2"], 3.2, cap="butt")
    out["up"] = (body, box_up)
    # forearm + hand
    fc = sleeve(arch, V, "fore") or skin
    body = circle(e[0], e[1], aw / 2 + 3, OUT)
    body += line(e, w, OUT, aw + 6, cap="butt") + circle(w[0], w[1], aw / 2 + 3, OUT)
    body += line(e, w, fc, aw, cap="round")
    dx, dy = w[0] - e[0], w[1] - e[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    ux, uy = dx / ln, dy / ln
    body += line((e[0] + nx * aw * 0.24 * side, e[1] + ny * aw * 0.24 * side), (w[0] + nx * aw * 0.24 * side, w[1] + ny * aw * 0.24 * side), darken(fc, 0.25), aw * 0.4, 0.7)
    body += line((e[0] - nx * aw * 0.26 * side, e[1] - ny * aw * 0.26 * side), (w[0] - nx * aw * 0.26 * side, w[1] - ny * aw * 0.26 * side), lighten(fc, 0.3), aw * 0.14, 0.65)
    hand_c = (w[0] + ux * aw * 0.28, w[1] + uy * aw * 0.28)
    hr = aw * 0.62
    claw_c = lighten(skin, 0.7) if arch not in ("skeleton",) else skin
    if arch == "skeleton":
        body += circle(e[0], e[1], aw * 0.75 + 2.6, OUT) + circle(e[0], e[1], aw * 0.75, skin)
        body += line(e, w, skin, aw, cap="round")
        for k in (-1, 0, 1):  # finger bones
            tip = (hand_c[0] + ux * hr * 1.9 + nx * k * hr * 0.8, hand_c[1] + uy * hr * 1.9 + ny * k * hr * 0.8)
            body += line(hand_c, tip, OUT, 4.8) + line(hand_c, tip, skin, 2.2)
        body += circle(hand_c[0], hand_c[1], hr + 2.4, OUT) + circle(hand_c[0], hand_c[1], hr, skin)
    else:
        if arch == "brute":
            m = (w[0] - ux * 10, w[1] - uy * 10)
            body += line((m[0] - nx * (aw / 2 + 2), m[1] - ny * (aw / 2 + 2)), (m[0] + nx * (aw / 2 + 2), m[1] + ny * (aw / 2 + 2)), V["cloth"], 8, cap="butt")
            body += circle(m[0], m[1], 2.0, V["accent"])
            hr = aw * 0.58
        if arch == "flame":  # glowing core, and flames curling off the back of the forearm
            body += line(e, w, V["skin2"], aw * 0.34, 0.6) + line(e, w, "#ffffff", aw * 0.12, 0.35)
            for t_, ln_ in ((0.28, 24), (0.6, 17)):
                bx_, by_ = e[0] + dx * t_ + nx * side * aw * 0.45, e[1] + dy * t_ + ny * side * aw * 0.45
                body += flame_layer(bx_, by_, bx_ + nx * side * ln_ - ux * ln_ * 0.5, by_ + ny * side * ln_ - uy * ln_ * 0.5, 6.5, 0,
                                    (V["fl1"], V["fl2"], V["fl3"]), 1.6)
        if arch == "fiend":
            cuff = (w[0] - ux * 3, w[1] - uy * 3)
            body += line((cuff[0] - nx * (aw / 2 + 2), cuff[1] - ny * (aw / 2 + 2)), (cuff[0] + nx * (aw / 2 + 2), cuff[1] + ny * (aw / 2 + 2)), OUT, 7.5, cap="butt")
            body += line((cuff[0] - nx * (aw / 2 + 1), cuff[1] - ny * (aw / 2 + 1)), (cuff[0] + nx * (aw / 2 + 1), cuff[1] + ny * (aw / 2 + 1)), V["cloth2"], 4.5, cap="butt")
            body += circle(cuff[0] + nx * 3, cuff[1] + ny * 3, 1.6, V["accent"])
        if arch == "horned_queen":
            if V["detail"] == "gloves":
                hand_col = V["cloth"]
            else:
                hand_col = skin
                for k in (-1, 1):
                    body += line((w[0] - ux * 4 - nx * (aw / 2 + 1), w[1] - uy * 4 - ny * (aw / 2 + 1)), (w[0] - ux * 4 + nx * (aw / 2 + 1), w[1] - uy * 4 + ny * (aw / 2 + 1)), V["cloth2"], 4, cap="butt")
                    break
        else:
            hand_col = skin
        body += claws(hand_c, ux, uy, nx, ny, hr, V.get("claw", darken(skin, 0.55) if arch != "queen" else INK) if arch != "horned_queen" else V["cloth2"])
        body += circle(hand_c[0], hand_c[1], hr + 2.6, OUT)
        body += circle(hand_c[0], hand_c[1], hr, hand_col if arch == "horned_queen" else (skin if arch != "fiend" else skin))
        body += circle(hand_c[0] - nx * side * hr * 0.25, hand_c[1] - ny * side * hr * 0.25, hr * 0.4, lighten(skin, 0.3), None, op=0.6)
    out["fore"] = (body, bb([e, w, hand_c], aw / 2 + 24), (hand_c[0], hand_c[1]))
    return out


def pauldron_part(P, V, J, side):
    """The brute's armoured pauldron: a riveted dome with two lames, a gold trim and three curved horn spikes. It is a part on
    the `torso` joint drawn over the upper arm (z 6), so a raised arm slides out from under it instead of rotating the armour."""
    s = J["shoulder_" + ("l" if side < 0 else "r")]
    metal, trim, spike = V["pd"], V["pd_trim"], V["pd_spike"]
    mx = lambda u: s[0] + side * u  # noqa: E731  outward = +u, down = +v (local to the shoulder joint)
    my = lambda v: s[1] + v  # noqa: E731

    def P_(pts):
        return [(mx(u), my(v)) for u, v in pts]

    def D(cmds):
        out = ""
        for c in cmds:
            if isinstance(c, str):
                out += c + " "
            else:
                out += f"{f(mx(c[0]))} {f(my(c[1]))} "
        return out.strip()

    d = ""
    # the lames: two curved plates fanning down the outside of the arm, under the dome
    for k, (dv, du, col) in enumerate(((22, 10, darken(metal, 0.18)), (12, 5, darken(metal, 0.08)))):
        lame = D(["M", (-4 + du, 0 + dv * 0.4), "Q", (16 + du, -4 + dv), (36 + du * 0.4, 4 + dv * 0.8), "L", (34 + du * 0.3, 14 + dv * 0.8),
                  "Q", (16 + du, 8 + dv), (-2 + du, 10 + dv * 0.4), "Z"])
        d += path(lame, col, OUT, 2.6)
        d += path(D(["M", (0 + du, 9 + dv * 0.4), "Q", (16 + du, 7 + dv), (33 + du * 0.3, 13 + dv * 0.8)]), None, trim, 2.0, sop=0.9)
        d += circle(mx(30 + du * 0.35), my(6 + dv * 0.8), 2.0, lighten(trim, 0.4), OUT, 1.0)
    # the spikes, behind the dome's top edge
    for (b, c, t, w0) in (((-2, -16), (-8, -38), (-4, -56), 12), ((14, -20), (18, -46), (30, -60), 13), ((28, -8), (46, -22), (60, -22), 11)):
        d += horn([(mx(u), my(v)) for u, v in bez(b, c, t, 10)], w0, 1.6, spike, rings=2, sw=2.4)
    dome = D(["M", (-20, -6), "Q", (-14, -26), (6, -27), "Q", (30, -26), (36, -2), "Q", (38, 12), (30, 16),
              "Q", (12, 8), (-4, 8), "Q", (-16, 6), (-20, -6), "Z"])
    gid = f"pd{'l' if side < 0 else 'r'}"
    defs = lin_grad(gid, [(0, lighten(metal, 0.35)), (0.45, metal), (1, darken(metal, 0.35))], 0, 0, 0, 1)
    d += path(dome, f"url(#{gid})", OUT, 3.2)
    d += path(D(["M", (-14, -14), "Q", (-6, -23), (8, -23)]), None, "#ffffff", 2.6, sop=0.55)  # specular sweep
    d += path(D(["M", (30, -14), "Q", (35, -4), (33, 8)]), None, RIM_L if side < 0 else RIM_R, 3.0, sop=0.7)  # rim light from the room
    d += path(D(["M", (-17, 2), "Q", (-6, 9), (6, 9), "Q", (20, 10), (31, 15)]), None, trim, 3.2)  # gold lower trim
    for u, v in ((-12, 3), (2, 6), (16, 8), (28, 12)):
        d += circle(mx(u), my(v), 2.2, lighten(trim, 0.45), OUT, 1.0)
    if V["detail"] == "harness":  # a little skull boss on the dome
        d += U_skull(mx(10), my(-11), 6.0)
    else:  # an embossed flame sigil
        d += path(flame_path(mx(10), my(-4), mx(10 + side * 1.5), my(-20), 5.5, side * 2), trim, OUT, 1.6)
    pts = P_([(-24, -66), (66, -66), (66, 30), (-24, 30)])
    return defs, d, bb(pts, 6)


def U_skull(cx, cy, r):
    """A small bone skull emblem (eyes dark)."""
    out = ellipse(cx, cy, r, r * 0.92, "#efe2c0", OUT, 1.4)
    out += rect(cx - r * 0.5, cy + r * 0.5, r, r * 0.55, "#efe2c0", OUT, 1.1, rx=r * 0.15)
    out += ellipse(cx - r * 0.36, cy - r * 0.02, r * 0.26, r * 0.3, "#2a0a1e") + ellipse(cx + r * 0.36, cy - r * 0.02, r * 0.26, r * 0.3, "#2a0a1e")
    return out


def leg_part(arch, P, V, J, side):
    name = "l" if side < 0 else "r"
    h = J["hip_" + name]
    sh = P["shoe_h"]
    ax = h[0] + side * 2.0
    ay = -sh - 2
    lw = P["lw"]
    skin, acc = V["skin"], V["accent"]
    body = ""
    pts_ = [h, (ax, ay), (ax - 20, 4), (ax + 20, 4)]
    fx = ax + side * 4
    if arch == "imp":
        body += capsule(h, (ax, ay), lw, skin, darken(skin, 0.25), lighten(skin, 0.3))
        for k in (-1, 0, 1):  # clawed toes
            body += circle(fx + k * 6.0 + side * 1, -4.5, 4.2, skin, OUT, 2.2)
            body += poly([(fx + k * 6.0 - 1.6 + side, -1.5), (fx + k * 6.0 + 1.6 + side, -1.5), (fx + k * 6.0 + 0.5 + side + k * 0.6, 1.6)], V["horn"], OUT, 1)
        body += ellipse(ax, -7, 9.5, 6, skin, OUT, 2.4) + ellipse(ax - 1, -9, 4.5, 2.2, lighten(skin, 0.35), None, op=0.6)
    elif arch == "brute":
        body += capsule(h, (ax, ay - 8), lw + 2, skin, darken(skin, 0.28), lighten(skin, 0.25))
        boot = V["cloth"]
        body += capsule((ax, ay - 20), (ax, ay), lw + 8, boot, darken(boot, 0.2), lighten(boot, 0.3))
        body += line((ax - lw / 2 - 4, ay - 20), (ax + lw / 2 + 4, ay - 20), V["accent"], 3.2, cap="butt")
        body += path(f"M{f(ax - 15)} {f(-5)} Q{f(ax - 16)} {f(-17)} {f(ax)} {f(-17)} Q{f(fx + side * 17)} {f(-17)} {f(fx + side * 20)} {f(-5)} L{f(fx + side * 20)} 1 L{f(ax - 15)} 1 Z", boot, OUT, 3)
        body += path(f"M{f(fx + side * 12)} {f(-17)} Q{f(fx + side * 24)} {f(-16)} {f(fx + side * 21)} {f(-3)}", None, V["horn"], 4)  # hoof tip
        body += line((ax - 14, -3), (fx + side * 19, -3), darken(boot, 0.35), 3, cap="butt")
        pts_ += [(fx + side * 24, 0)]
    elif arch == "fiend":
        cloth = V["cloth"]
        body += capsule(h, (ax, ay + 2), lw, cloth, darken(cloth, 0.3), lighten(cloth, 0.22))
        body += line((h[0] + side * lw * 0.28, h[1] + 4), (ax + side * lw * 0.28, ay), V["accent"], 1.8, 0.75)
        body += path(f"M{f(ax - 11)} {f(-3)} Q{f(ax - 12)} {f(-14)} {f(ax)} {f(-14)} Q{f(fx + side * 12)} {f(-13)} {f(fx + side * 24)} {f(-9)} Q{f(fx + side * 28)} {f(-7)} {f(fx + side * 24)} {f(-3)} Q{f(fx + side * 24)} 1 {f(fx + side * 14)} 1 L{f(ax - 10)} 1 Q{f(ax - 12)} 0 {f(ax - 11)} {f(-3)} Z", "#241230", OUT, 3)
        body += line((ax - 8, -11), (fx + side * 14, -12), lighten("#241230", 0.5), 1.8, 0.8)
        body += circle(ax + side * 3, -9, 2.2, acc, OUT, 1)
        pts_ += [(fx + side * 30, 0)]
    elif arch == "skeleton":
        bone = skin
        body += line(h, (ax, ay), OUT, lw + 5, cap="butt") + line(h, (ax, ay), bone, lw, cap="round")
        body += line((h[0] + lw * 0.22 * side, h[1] + 3), (ax + lw * 0.22 * side, ay), V["skin2"], 2.4, 0.8)
        body += circle(h[0], h[1] + 2, lw * 0.78 + 2.6, OUT) + circle(h[0], h[1] + 2, lw * 0.78, bone)
        km = (h[0] + (ax - h[0]) * 0.52, h[1] + (ay - h[1]) * 0.52)
        body += circle(km[0], km[1], lw * 0.74 + 2.6, OUT) + circle(km[0], km[1], lw * 0.74, bone) + line((km[0] - 3, km[1] - 2), (km[0] + 2, km[1] - 3), "#ffffff", 1.4, 0.8)
        body += path(f"M{f(ax - 12)} {f(-3)} Q{f(ax - 12)} {f(-11)} {f(ax)} {f(-11)} Q{f(fx + side * 14)} {f(-11)} {f(fx + side * 16)} {f(-4)} Q{f(fx + side * 16)} 1 {f(fx + side * 8)} 1 L{f(ax - 10)} 1 Q{f(ax - 13)} 0 {f(ax - 12)} {f(-3)} Z", bone, OUT, 3)
        for k in range(3):
            body += line((fx + side * (4 + k * 4.2), -9), (fx + side * (4 + k * 4.2), -1), darken(bone, 0.3), 1.4, 0.8)
        pts_ += [(fx + side * 18, 0)]
    elif arch == "flame":
        gid = "lg"
        defs_note = ""
        body += capsule(h, (ax, ay), lw, skin, darken(skin, 0.22), lighten(V["skin2"], 0.1))
        body += line((h[0], h[1] + 6), (ax, ay - 6), V["skin2"], lw * 0.3, 0.55)
        body += line((ax, ay - 4), (ax, ay + 4), V["skin2"], lw * 0.5, 0.8)
        # feet are small flames
        body += flame_layer(ax, -2, ax + side * 2, -22, 9.5, side * 3, (V["fl1"], V["fl2"], V["fl3"]), 2.4)
        body += ellipse(ax, -2, 10.5, 4.5, V["fl2"], OUT, 2.2)
        pts_ += [(ax, -24)]
    elif arch == "horned_queen":
        body += capsule(h, (ax, ay - 22), lw, skin, darken(skin, 0.25), lighten(skin, 0.3))
        boot = V["cloth"]
        body += capsule((ax, ay - 34), (ax, ay), lw + 3, boot, darken(boot, 0.2), lighten(boot, 0.3))
        body += line((ax - lw / 2 - 2, ay - 34), (ax + lw / 2 + 2, ay - 34), V["cloth2"], 2.6, cap="butt")
        body += path(f"M{f(ax - 9)} {f(-8)} Q{f(ax - 9)} {f(-12)} {f(ax)} {f(-12)} Q{f(fx + side * 8)} {f(-12)} {f(fx + side * 16)} {f(-5)} Q{f(fx + side * 19)} 1 {f(fx + side * 11)} 1 L{f(ax - 8)} 1 Z", boot, OUT, 3)
        body += poly([(ax - side * 4, -9), (ax - side * 9, 3), (ax - side * 2, 3)], V["cloth2"], OUT, 1.6)  # heel
        pts_ += [(fx + side * 20, 0)]
    return body, bb(pts_, lw / 2 + 24)


# ---- heads ---------------------------------------------------------------------------------------------------------------

def head_part(arch, P, V):
    rx, ry, cy, ny = P["rx"], P["ry"], P["cy"], P["neck_y"]
    skin = V["skin"]
    d = C.head_path(P)
    defs = clip("hc", f'<path d="{d}"/>') + C.SHADE_GRAD
    body = ""
    if arch == "skeleton":
        neck = skin
        body += rect(-5.5, cy + ry * 0.55, 11, ny - (cy + ry * 0.55) + 14, neck, OUT, 2.4, rx=3)
        for k in range(3):
            body += line((-5.5, cy + ry + 3 + k * 5), (5.5, cy + ry + 3 + k * 5), OUT, 1.5, 0.8)
        skull = (f"M{f(-rx)} {f(cy)} C{f(-rx)} {f(cy - ry * 1.34)} {f(rx)} {f(cy - ry * 1.34)} {f(rx)} {f(cy)} "
                 f"C{f(rx)} {f(cy + ry * 0.4)} {f(rx * 0.78)} {f(cy + ry * 0.62)} {f(rx * 0.7)} {f(cy + ry * 0.74)} L{f(rx * 0.66)} {f(cy + ry * 0.98)} "
                 f"Q0 {f(cy + ry * 1.12)} {f(-rx * 0.66)} {f(cy + ry * 0.98)} L{f(-rx * 0.7)} {f(cy + ry * 0.74)} C{f(-rx * 0.78)} {f(cy + ry * 0.62)} {f(-rx)} {f(cy + ry * 0.4)} {f(-rx)} {f(cy)} Z")
        defs = clip("hc", f'<path d="{skull}"/>') + C.SHADE_GRAD
        body += f'<path d="{skull}" fill="{skin}"/>'
        inner = f'<rect x="{f(-rx - 4)}" y="{f(cy - ry * 1.3)}" width="{f(rx * 2 + 8)}" height="{f(ry * 2.6)}" fill="url(#shd)"/>'
        inner += f'<rect x="{f(-rx - 2)}" y="{f(cy - ry * 1.3)}" width="4.5" height="{f(ry * 2.6)}" fill="{RIM_L}" fill-opacity="0.5"/>'
        inner += f'<rect x="{f(rx - 2.5)}" y="{f(cy - ry * 1.3)}" width="4.5" height="{f(ry * 2.6)}" fill="{RIM_R}" fill-opacity="0.4"/>'
        inner += ellipse(-rx * 0.35, cy - ry * 0.55, rx * 0.3, ry * 0.15, "#ffffff", None, op=0.5)
        inner += path(f"M{f(-rx * 0.15)} {f(cy - ry * 1.2)} L{f(-rx * 0.05)} {f(cy - ry * 0.9)} L{f(-rx * 0.2)} {f(cy - ry * 0.78)}", None, darken(skin, 0.3), 1.4, sop=0.8)  # skull crack
        body += group(inner, 'clip-path="url(#hc)"')
        body += path(skull, None, OUT, 3)
        return defs, body, (-rx - 14, cy - ry - 8, rx + 14, ny + 18)
    nt, nb = cy + ry * 0.55, ny + 14  # a tapered neck with a soft shadow under the jaw
    nw = {"brute": 11.0, "imp": 6.5}.get(arch, 7.0)
    neck = f"M{f(-nw)} {f(nt)} L{f(nw)} {f(nt)} L{f(nw + 3)} {f(nb)} L{f(-nw - 3)} {f(nb)} Z"
    body += path(neck, darken(skin, 0.1), OUT, 2.6)
    body += ellipse(0, cy + ry * 0.92, nw + 2, 5, darken(skin, 0.45), None, op=0.45)
    body += line((-nw * 0.45, nt + 6), (-nw * 0.6, nb - 4), lighten(skin, 0.25), 1.6, 0.5)
    if arch in ("imp", "brute", "fiend", "horned_queen"):  # pointed ears
        big = {"imp": 20, "brute": 12, "fiend": 17, "horned_queen": 15}[arch]
        for side in (-1, 1):
            ex = side * (rx - 2)
            tip = (side * (rx + big), cy - ry * 0.32 - (4 if arch == "imp" else 0))
            body += poly([(ex, cy - 8), tip, (ex, cy + 9)], skin, OUT, 2.6)
            body += poly([(ex + side * 1.5, cy - 4), (side * (rx + big * 0.62), cy - ry * 0.18 - (3 if arch == "imp" else 0)), (ex + side * 1.5, cy + 5)], V["skin2"], None, op=0.9)
    body += f'<path d="{d}" fill="{skin}"/>'
    inner = f'<rect x="{f(-rx - 4)}" y="{f(cy - ry * 1.3)}" width="{f(rx * 2 + 8)}" height="{f(ry * 2.5)}" fill="url(#shd)"/>'
    inner += f'<rect x="{f(-rx - 2)}" y="{f(cy - ry * 1.3)}" width="4.5" height="{f(ry * 2.5)}" fill="{RIM_L}" fill-opacity="0.55"/>'
    inner += f'<rect x="{f(rx - 2.5)}" y="{f(cy - ry * 1.3)}" width="4.5" height="{f(ry * 2.5)}" fill="{RIM_R}" fill-opacity="0.42"/>'
    inner += ellipse(-rx * 0.32, cy - ry * 0.45, rx * 0.28, ry * 0.14, lighten(skin, 0.4), None, op=0.5)
    if arch == "flame":
        inner += ellipse(0, cy + ry * 0.2, rx * 0.8, ry * 0.7, V["skin2"], None, op=0.55)
    if arch == "brute":  # heavy brow ridge shadow
        inner += path(f"M{f(-rx)} {f(cy - ry * 0.28)} Q0 {f(cy - ry * 0.5)} {f(rx)} {f(cy - ry * 0.28)} L{f(rx)} {f(cy - ry * 0.7)} L{f(-rx)} {f(cy - ry * 0.7)} Z", darken(skin, 0.32), None, op=0.55)
    body += group(inner, 'clip-path="url(#hc)"')
    body += path(d, None, OUT, 3)
    return defs, body, (-rx - 34, cy - ry - 8, rx + 34, ny + 18)


def _demon_eye(cx, cy, rx, ry, iris, side, lid=None, skin=None, look=0.0, slit=True):
    out = ellipse(cx, cy, rx, ry, "#fffbe8", OUT, 1.8)
    out += ellipse(cx + look, cy + 0.6, rx * 0.62, ry * 0.8, iris, None)
    if slit:
        out += ellipse(cx + look, cy + 0.6, rx * 0.2, ry * 0.7, "#1a0818", None)
    else:
        out += circle(cx + look, cy + 0.6, rx * 0.34, "#1a0818")
    out += circle(cx + look - rx * 0.28, cy - ry * 0.3, rx * 0.2, "#ffffff")
    if lid is not None:
        out += path(f"M{f(cx - rx - 0.8)} {f(cy - ry - 1.5)} L{f(cx + rx + 0.8)} {f(cy - ry - 1.5)} L{f(cx + rx + 0.8)} {f(cy - ry + lid)} Q{f(cx)} {f(cy - ry + lid + 2.2)} {f(cx - rx - 0.8)} {f(cy - ry + lid)} Z", skin, OUT, 1.6)
    return out


def face_overlay(arch, P, V, expr):
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    skin, iris = V["skin"], V["iris"]
    ex = rx * 0.42
    ey = cy + {"imp": 3.0, "brute": 3.0, "skeleton": 1.0}.get(arch, 2.0)
    erx = {"imp": 6.6, "brute": 6.0, "skeleton": 6.4}.get(arch, 5.6)
    ery = erx * 1.2
    brow = {"skeleton": OUT}.get(arch, INK)
    mouth_y = cy + ry * 0.58
    fang = arch in ("imp", "brute", "fiend", "horned_queen")
    blush = {"imp": "#ff2f9d", "flame": "#ff3a1a"}.get(arch, "#ff4f9a")
    body = ""
    if arch == "skeleton":
        def sock(sx, kind):
            cx_ = sx * ex
            o = ellipse(cx_, ey, 7.6, 8.6, "#1a0818", OUT, 1.8)
            if kind == "neutral":
                o += circle(cx_, ey + 0.5, 3.6, iris) + circle(cx_, ey + 0.5, 1.6, "#ffffff")
            elif kind == "happy":
                o += path(f"M{f(cx_ - 4.6)} {f(ey + 2.4)} Q{f(cx_)} {f(ey - 5)} {f(cx_ + 4.6)} {f(ey + 2.4)}", None, iris, 2.8)
            elif kind == "cheer":
                o += path(f"M{f(cx_ - 5)} {f(ey + 2.6)} Q{f(cx_)} {f(ey - 6.5)} {f(cx_ + 5)} {f(ey + 2.6)}", None, "#ffffff", 3.0)
            else:
                o += circle(cx_ + 0.4, ey + 2.6, 2.6, iris) + path(f"M{f(cx_ - 6)} {f(ey - 5.5)} L{f(cx_ + 6)} {f(ey - 5.5)} L{f(cx_ + 6)} {f(ey - 2)} Q{f(cx_)} {f(ey - 1)} {f(cx_ - 6)} {f(ey - 2)} Z", skin, OUT, 1.4)
            return o
        body += sock(-1, expr) + sock(1, expr)
        by_ = ey - 11
        if expr == "happy":
            body += path(f"M{f(-ex - 5)} {f(by_ + 1)} Q{f(-ex)} {f(by_ - 2)} {f(-ex + 5)} {f(by_ + 1)}", None, brow, 2.0) + path(f"M{f(ex - 5)} {f(by_ + 1)} Q{f(ex)} {f(by_ - 2)} {f(ex + 5)} {f(by_ + 1)}", None, brow, 2.0)
        elif expr == "sad":
            body += line((-ex - 5, by_ + 3), (-ex + 4, by_ - 2), brow, 2.2) + line((ex - 4, by_ - 2), (ex + 5, by_ + 3), brow, 2.2)
        body += path(f"M-1.4 {f(cy + ry * 0.28)} L0 {f(cy + ry * 0.12)} L1.4 {f(cy + ry * 0.28)} Z", "#1a0818", None)  # nose hole
        my = cy + ry * 0.6
        if expr == "cheer":
            body += path(f"M{f(-rx * 0.62)} {f(my - 3)} L{f(rx * 0.62)} {f(my - 3)} L{f(rx * 0.5)} {f(my + 15)} Q0 {f(my + 19)} {f(-rx * 0.5)} {f(my + 15)} Z", "#1a0818", OUT, 2)
            body += rect(-rx * 0.58, my - 2.4, rx * 1.16, 5.5, "#fffbe8", None, rx=1.4)
            for k in range(-3, 4):
                body += line((k * rx * 0.17, my - 2.4), (k * rx * 0.17, my + 3), "#1a0818", 1.0)
            body += rect(-rx * 0.42, my + 9.5, rx * 0.84, 5, "#fffbe8", None, rx=1.4) + ellipse(0, my + 14.5, 5, 2.4, "#ff6f9c", None)
        else:
            if expr == "happy":
                dd = f"M{f(-rx * 0.62)} {f(my - 1)} Q0 {f(my + 9)} {f(rx * 0.62)} {f(my - 1)}"
            elif expr == "sad":
                dd = f"M{f(-rx * 0.5)} {f(my + 5)} Q0 {f(my - 3)} {f(rx * 0.5)} {f(my + 5)}"
            else:
                dd = f"M{f(-rx * 0.52)} {f(my + 1)} Q0 {f(my + 3.5)} {f(rx * 0.52)} {f(my + 1)}"
            body += path(dd, None, OUT, 5.4) + path(dd, None, "#fffbe8", 3.2)
            for k in range(-3, 4):
                px_ = k * rx * 0.16
                body += line((px_, my + 7 - abs(k) * 0.4 if expr == "happy" and False else my - 1), (px_, my + 3), OUT, 0.0)
        return body, (-rx - 8, cy - ry - 6, rx + 8, cy + ry * 1.3)
    # --- generic demon / flame face ---
    slit = arch != "flame"
    if expr == "neutral":
        body += _demon_eye(-ex, ey, erx, ery, iris, -1, slit=slit) + _demon_eye(ex, ey, erx, ery, iris, 1, slit=slit)
        by_ = ey - ery - 4.0
        body += line((-ex - 6, by_ - 1.6), (-ex + 5.5, by_ + 1.8), brow, 3.0) + line((ex - 5.5, by_ + 1.8), (ex + 6, by_ - 1.6), brow, 3.0)  # scheming brows
        body += path(f"M-6 {f(mouth_y)} Q0 {f(mouth_y + 4)} 6 {f(mouth_y)}", None, "#4a0f2a", 2.4)
        if fang:
            body += poly([(-4.6, mouth_y + 1.2), (-2.4, mouth_y + 2.6), (-3.6, mouth_y + 6)], "#ffffff", OUT, 1.0) + poly([(4.6, mouth_y + 1.2), (2.4, mouth_y + 2.6), (3.6, mouth_y + 6)], "#ffffff", OUT, 1.0)
    elif expr == "happy":
        body += _demon_eye(-ex, ey, erx, ery * 0.88, iris, -1, slit=slit) + _demon_eye(ex, ey, erx, ery * 0.88, iris, 1, slit=slit)
        by_ = ey - ery - 5.4
        body += path(f"M{f(-ex - 6)} {f(by_ + 0.4)} Q{f(-ex)} {f(by_ - 3)} {f(-ex + 5.5)} {f(by_ + 2.6)}", None, brow, 3.0) + path(f"M{f(ex - 5.5)} {f(by_ + 2.6)} Q{f(ex)} {f(by_ - 3)} {f(ex + 6)} {f(by_ + 0.4)}", None, brow, 3.0)
        body += path(f"M-8 {f(mouth_y - 1)} Q0 {f(mouth_y + 10)} 8 {f(mouth_y - 1)} Q0 {f(mouth_y + 2.6)} -8 {f(mouth_y - 1)} Z", "#5a0f33", OUT, 1.6)
        body += path(f"M-6.4 {f(mouth_y - 0.2)} Q0 {f(mouth_y + 2.8)} 6.4 {f(mouth_y - 0.2)} L5.6 {f(mouth_y + 1.4)} Q0 {f(mouth_y + 3.8)} -5.6 {f(mouth_y + 1.4)} Z", "#ffffff", None)
        if fang:
            body += poly([(-6.4, mouth_y - 0.2), (-3.6, mouth_y + 1.2), (-5.4, mouth_y + 6.6)], "#ffffff", OUT, 1.0) + poly([(6.4, mouth_y - 0.2), (3.6, mouth_y + 1.2), (5.4, mouth_y + 6.6)], "#ffffff", OUT, 1.0)
        body += ellipse(-ex - 3, ey + 8, 4.5, 2.6, blush, None, op=0.4) + ellipse(ex + 3, ey + 8, 4.5, 2.6, blush, None, op=0.4)
    elif expr == "cheer":
        for sx in (-1, 1):
            body += path(f"M{f(sx * ex - 5.5)} {f(ey + 1.6)} Q{f(sx * ex)} {f(ey - 7.5)} {f(sx * ex + 5.5)} {f(ey + 1.6)}", None, "#2a0a1e", 3.0)
        by_ = ey - ery - 8.6
        body += path(f"M{f(-ex - 6)} {f(by_ + 2.4)} Q{f(-ex)} {f(by_ - 3)} {f(-ex + 6)} {f(by_ + 1.2)}", None, brow, 3.0) + path(f"M{f(ex - 6)} {f(by_ + 1.2)} Q{f(ex)} {f(by_ - 3)} {f(ex + 6)} {f(by_ + 2.4)}", None, brow, 3.0)
        my = mouth_y - 3.4
        body += path(f"M-10 {f(my)} L10 {f(my)} Q9 {f(my + 15)} 0 {f(my + 15)} Q-9 {f(my + 15)} -10 {f(my)} Z", "#5a0f33", OUT, 2)
        body += path(f"M-9 {f(my + 0.8)} L9 {f(my + 0.8)} L8.4 {f(my + 4.4)} L-8.4 {f(my + 4.4)} Z", "#ffffff", None)
        if fang:
            body += poly([(-9, my + 0.8), (-5.5, my + 1), (-7.6, my + 8)], "#ffffff", OUT, 1.0) + poly([(9, my + 0.8), (5.5, my + 1), (7.6, my + 8)], "#ffffff", OUT, 1.0)
        body += ellipse(0, my + 12, 5.2, 3.4, "#ff6f9c", None)
        body += ellipse(-ex - 3.5, ey + 8.5, 5, 3, blush, None, op=0.5) + ellipse(ex + 3.5, ey + 8.5, 5, 3, blush, None, op=0.5)
    else:
        body += _demon_eye(-ex, ey + 1, erx, ery * 0.9, iris, -1, lid=ery * 0.9, skin=skin, look=-0.8, slit=slit)
        body += _demon_eye(ex, ey + 1, erx, ery * 0.9, iris, 1, lid=ery * 0.9, skin=skin, look=-0.8, slit=slit)
        by_ = ey - ery - 3.0
        body += line((-ex - 6, by_ + 3.4), (-ex + 5, by_ - 2.8), brow, 2.8) + line((ex - 5, by_ - 2.8), (ex + 6, by_ + 3.4), brow, 2.8)
        body += path(f"M-6 {f(mouth_y + 3.8)} Q0 {f(mouth_y - 2.6)} 6 {f(mouth_y + 3.8)}", None, "#4a0f2a", 2.5)
        body += path(f"M{f(rx * 0.72)} {f(cy - ry * 0.35)} Q{f(rx * 0.95)} {f(cy - ry * 0.05)} {f(rx * 0.72)} {f(cy + ry * 0.1)} Q{f(rx * 0.5)} {f(cy - ry * 0.05)} {f(rx * 0.72)} {f(cy - ry * 0.35)} Z", "#8fe6ff", OUT, 1.4)
    nose_y = cy + ry * 0.3
    if arch == "brute":  # tusks + nose ring on every expression
        body += poly([(-9, mouth_y + 1), (-5, mouth_y - 1), (-7.2, mouth_y - 11)], V["horn"], OUT, 1.6) + poly([(9, mouth_y + 1), (5, mouth_y - 1), (7.2, mouth_y - 11)], V["horn"], OUT, 1.6)
        body += circle(0, nose_y + 4.6, 3.6, None, V["accent"], 1.8)
        body += ellipse(-2.6, nose_y + 1.4, 1.1, 0.8, darken(skin, 0.55), None) + ellipse(2.6, nose_y + 1.4, 1.1, 0.8, darken(skin, 0.55), None)
    elif arch == "imp":
        body += ellipse(-1.6, nose_y + 1, 1.0, 0.8, darken(skin, 0.5), None) + ellipse(1.6, nose_y + 1, 1.0, 0.8, darken(skin, 0.5), None)
    elif arch == "flame":
        body += path(f"M-1.8 {f(nose_y)} Q0.4 {f(nose_y + 3.4)} 2.8 {f(nose_y + 1.8)}", None, darken(skin, 0.4), 1.5, sop=0.8)
    else:
        body += path(f"M-1.8 {f(nose_y)} Q0.4 {f(nose_y + 3.6)} 2.8 {f(nose_y + 1.8)}", None, darken(skin, 0.42), 1.5, sop=0.85)
    if arch == "horned_queen":  # long lashes + beauty mark
        for sx in (-1, 1):
            for k in range(3):
                body += line((sx * ex + sx * (erx - 0.5), ey - 1.5), (sx * ex + sx * (erx + 1.8 + k * 0.6), ey - 4 - k * 1.8), INK, 1.6)
        body += circle(ex + 6, ey + 10, 0.9, darken(skin, 0.5), None, op=0.8)
    if arch == "fiend":  # a little goatee
        body += poly([(-2.4, cy + ry * 0.95), (2.4, cy + ry * 0.95), (0, cy + ry * 1.4)], V["hair"], None)
    return body, (-rx - 8, cy - ry - 6, rx + 8, cy + ry + 8)


# ---- extras: horns, hair, tail, wings, cape ---------------------------------------------------------------------------------

def ram_horn(sgn, rx, cy, ry, color, r0=22, w0=21):
    cx_, cy_ = sgn * (rx * 0.95 + r0 * 0.82), cy - ry * 0.28
    pts = []
    n = 30
    for i in range(n):
        t = i / (n - 1)
        a = math.radians(-150 + t * 270) if sgn > 0 else math.radians(-30 - t * 270)
        r = r0 * (1 - 0.5 * t)
        pts.append((cx_ + math.cos(a) * r, cy_ + math.sin(a) * r))
    return horn(pts, w0, 3.0, color, rings=6)


def hair_parts(arch, P, V):
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    out = {"back": None, "front": None, "extra": []}
    if arch == "imp":
        body = ""
        for sgn in (-1, 1):
            body += horn(bez((sgn * 11, cy - ry * 0.85), (sgn * 22, cy - ry * 1.15), (sgn * 20, cy - ry - 24)), 12, 2.5, V["horn"], rings=3)
        out["back"] = (body, (-rx - 10, cy - ry - 40, rx + 10, cy), None, False)
        fr = ""
        for k, (dx_, ln_) in enumerate(((-6, 14), (0, 20), (6, 14))):  # a cheeky curl of hair
            fr += path(flame_path(dx_, cy - ry * 0.96, dx_ * 1.4 + 2, cy - ry * 0.96 - ln_, 4.2, 3), "#2a0a1e", OUT, 2)
        out["front"] = (fr, (-rx, cy - ry - 34, rx, cy - ry * 0.5))
        # tail: root on the pelvis at the back, S-curve out to the right ending in a spade
        hy = -P["hip_y"]
        root = (3, hy + 4)
        pts = bez(root, (58, hy + 44), (50, hy - 20), 14) + bez((50, hy - 20), (44, hy - 56), (74, hy - 50), 12)[1:]
        poly_pts, l_, r_ = taper(pts, 11, 4.5)
        tb = poly(poly_pts, V["skin"], OUT, 3)
        tip = pts[-1]
        tb += poly([(tip[0] - 2, tip[1] - 8), (tip[0] + 16, tip[1] - 2), (tip[0] + 4, tip[1] + 14), (tip[0] - 8, tip[1] + 4)], V["skin"], OUT, 3)
        tb += path("M" + " L".join(f"{f((l_[i][0] * 0.65 + pts[i][0] * 0.35))} {f(l_[i][1] * 0.65 + pts[i][1] * 0.35)}" for i in range(2, len(pts) - 4)), None, lighten(V["skin"], 0.35), 1.8, sop=0.7)
        out["extra"].append(dict(name="tail", joint="hips", z=-15, body=tb, box=bb(pts + [(tip[0] + 18, tip[1] + 14)], 14), swing=True, pivot_xy=root))
    elif arch == "brute":
        back = ram_horn(-1, rx, cy, ry, V["horn"]) + ram_horn(1, rx, cy, ry, V["horn"])
        out["back"] = (back, (-rx - 80, cy - ry - 50, rx + 80, cy + ry), None, False)
        fr = path(f"M{f(-rx * 0.5)} {f(cy - ry * 0.92)} L{f(-rx * 0.28)} {f(cy - ry * 1.18)} L0 {f(cy - ry * 0.98)} L{f(rx * 0.28)} {f(cy - ry * 1.18)} L{f(rx * 0.5)} {f(cy - ry * 0.92)} Q0 {f(cy - ry * 1.12)} {f(-rx * 0.5)} {f(cy - ry * 0.92)} Z", "#2a0a1e", OUT, 2.4)
        out["front"] = (fr, (-rx, cy - ry * 1.4, rx, cy - ry * 0.7))
    elif arch == "fiend":
        back = ""
        for sgn in (-1, 1):
            back += horn(bez((sgn * 9, cy - ry * 0.9), (sgn * 17, cy - ry * 1.3), (sgn * 15, cy - ry - 26)), 11, 2.2, V["horn"], rings=3)
        out["back"] = (back, (-rx - 10, cy - ry - 40, rx + 10, cy), None, False)
        hair = V["hair"]
        cap = (f"M{f(-rx - 2.5)} {f(cy + 4)} C{f(-rx - 4)} {f(cy - ry * 1.5)} {f(rx + 4)} {f(cy - ry * 1.5)} {f(rx + 2.5)} {f(cy + 4)} "
               f"L{f(rx - 1)} {f(cy - 8)} C{f(rx * 0.6)} {f(cy - ry * 0.45)} {f(rx * 0.2)} {f(cy - ry * 0.75)} 0 {f(cy - ry * 0.46)} "
               f"C{f(-rx * 0.2)} {f(cy - ry * 0.75)} {f(-rx * 0.6)} {f(cy - ry * 0.45)} {f(-rx + 1)} {f(cy - 8)} Z")
        fr = path(cap, hair, OUT, 3)
        fr += path(f"M{f(-rx * 0.6)} {f(cy - ry * 1.0)} Q{f(0)} {f(cy - ry * 1.28)} {f(rx * 0.7)} {f(cy - ry * 0.95)}", None, lighten(hair, 0.5), 3, 0.75)
        fr += path(f"M{f(-rx * 0.1)} {f(cy - ry * 1.12)} Q{f(rx * 0.5)} {f(cy - ry * 1.5)} {f(rx * 0.95)} {f(cy - ry * 1.28)} Q{f(rx * 0.5)} {f(cy - ry * 1.2)} {f(rx * 0.1)} {f(cy - ry * 1.0)} Z", hair, OUT, 2.4)  # swept quiff
        out["front"] = (fr, (-rx - 12, cy - ry - 22, rx + 14, cy + 8))
        # bat wings behind the shoulders, swing about the root between the shoulder blades
        ts = P["sh_y"] - 4
        root = (0, ts + 14)
        wing = ""
        for sgn in (-1, 1):
            wr_ = (sgn * 44, ts - 62)
            T = [(sgn * 100, ts - 48), (sgn * 106, ts - 2), (sgn * 84, ts + 34)]
            Bp = (sgn * 12, ts + 50)
            dd = f"M{f(root[0])} {f(root[1])} L{f(wr_[0])} {f(wr_[1])} L{f(T[0][0])} {f(T[0][1])} "
            prev = T[0]
            for tp in T[1:] + [Bp]:
                cxm, cym = (prev[0] + tp[0]) / 2 - sgn * 16, (prev[1] + tp[1]) / 2 - 4
                dd += f"Q{f(cxm)} {f(cym)} {f(tp[0])} {f(tp[1])} "
                prev = tp
            dd += "Z"
            wing += path(dd, V["wing"], OUT, 3)
            wing += path(f"M{f(root[0])} {f(root[1])} L{f(wr_[0])} {f(wr_[1])} L{f(T[0][0])} {f(T[0][1])} L{f(sgn * 70)} {f(ts - 2)} Z", lighten(V["wing"], 0.16), None, op=0.5)
            for t_ in T + [Bp]:
                wing += line(wr_, t_, lighten(V["wing"], 0.45), 2.6, 0.95)
            wing += line(root, wr_, OUT, 8) + line(root, wr_, lighten(V["wing"], 0.55), 4.6) + line(wr_, T[0], OUT, 7) + line(wr_, T[0], lighten(V["wing"], 0.55), 3.6)
            wing += poly([(wr_[0] - sgn * 3, wr_[1] - 3), (wr_[0] + sgn * 1, wr_[1] - 14), (wr_[0] + sgn * 6, wr_[1] + 1)], lighten(V["wing"], 0.6), OUT, 1.6)
        out["extra"].append(dict(name="wings", joint="torso", z=-25, body=wing, box=(-118, ts - 108, 118, ts + 64), swing=True, pivot_xy=root))
    elif arch == "skeleton":
        hat = V["cloth"]
        top = cy - ry
        base_y = cy - ry * 0.7
        tipx, tipy = 6, top - 54
        d = f"M{f(-17)} {f(base_y + 6)} L{f(tipx)} {f(tipy)} L{f(19)} {f(base_y + 2)} Q{f(0)} {f(base_y + 11)} {f(-17)} {f(base_y + 6)} Z"
        defs = clip("hatc", f'<path d="{d}"/>')
        b = path(d, hat, None)
        inn = ""
        for k in range(4):
            y_ = base_y - k * 15 - 2
            inn += poly([(-30, y_), (40, y_ - 14), (40, y_ - 8), (-30, y_ + 6)], V["cloth2"], None, op=0.95)
        for (x_, y_, c_) in ((-6, base_y - 6, V["accent"]), (6, base_y - 24, "#ffffff"), (0, base_y - 38, V["accent"])):
            inn += circle(x_, y_, 2.2, c_, None)
        b += group(inn, 'clip-path="url(#hatc)"')
        b += path(d, None, OUT, 3)
        b += circle(tipx, tipy - 1, 7, V["cloth2"], OUT, 2.4)
        for k in range(8):
            a_ = k * math.tau / 8
            b += line((tipx, tipy - 1), (tipx + math.cos(a_) * 10, tipy - 1 + math.sin(a_) * 10), V["cloth2"], 2.4)
        b += circle(tipx, tipy - 1, 4.2, lighten(V["cloth2"], 0.5), None)
        out["front"] = (b, (-26, tipy - 20, 30, base_y + 18), defs)
    elif arch == "flame":
        cols = (V["fl1"], V["fl2"], V["fl3"])
        base_y = cy - ry * 0.5
        back = ""
        for bx, tx, ty, w, bend in ((-20, -42, -78, 11, -6), (-10, -22, -108, 12, -4), (0, 2, -128, 13, 2), (10, 26, -104, 12, 5), (20, 44, -74, 11, 6)):
            back += flame_layer(bx * 0.8, base_y, tx, cy + ty, w, bend, (darken(cols[0], 0.12), cols[0], cols[1]), 2.8)
        out["back"] = (back, (-74, cy - 150, 74, base_y + 8), (0, base_y), True)
        fr = ""
        for bx, tx, ty, w, bend in ((-14, -24, -60, 8, -4), (0, 0, -78, 9, 2), (14, 26, -58, 8, 4)):
            fr += flame_layer(bx * 0.7, cy - ry * 0.76, tx, cy + ty, w, bend, cols, 2.4)
        out["front"] = (fr, (-50, cy - 110, 50, cy - ry * 0.5), None, True)
    elif arch == "horned_queen":
        back = ""
        for sgn in (-1, 1):
            back += horn(bez((sgn * 10, cy - ry * 0.85), (sgn * rx * 1.9, cy - ry * 1.5), (sgn * (rx + 20), cy - ry - 62)), 15, 2.4, V["horn"], rings=5)
        out["back"] = (back, (-rx - 48, cy - ry - 80, rx + 48, cy), None, False)
        hair = V["hair"]
        bk = path(f"M{f(-rx - 8)} {f(cy - 4)} C{f(-rx - 12)} {f(cy - ry * 1.6)} {f(rx + 12)} {f(cy - ry * 1.6)} {f(rx + 8)} {f(cy - 4)} L{f(rx + 11)} {f(cy + ry + 28)} Q{f(rx * 0.4)} {f(cy + ry + 40)} 0 {f(cy + ry + 20)} Q{f(-rx * 0.4)} {f(cy + ry + 40)} {f(-rx - 11)} {f(cy + ry + 28)} Z", hair, OUT, 3)
        bk += path(f"M{f(rx + 4)} {f(cy + 6)} Q{f(rx + 9)} {f(cy + ry + 8)} {f(rx + 6)} {f(cy + ry + 26)}", None, lighten(hair, 0.4), 2.4, sop=0.7)
        out["back"] = (back + bk, (-rx - 48, cy - ry - 80, rx + 48, cy + ry + 48), None, False)
        fr = (f"M{f(-rx - 3)} {f(cy + ry * 0.4)} C{f(-rx - 5)} {f(cy - ry * 1.5)} {f(rx + 5)} {f(cy - ry * 1.5)} {f(rx + 3)} {f(cy + ry * 0.4)} "
              f"L{f(rx - 3)} {f(cy + 2)} C{f(rx * 0.5)} {f(cy - ry * 0.3)} {f(-rx * 0.1)} {f(cy - ry * 0.7)} {f(-rx * 0.5)} {f(cy - ry * 0.5)} "
              f"C{f(-rx * 0.8)} {f(cy - ry * 0.3)} {f(-rx + 2)} {f(cy)} {f(-rx + 3)} {f(cy + ry * 0.4)} Z")
        body = path(fr, hair, OUT, 3)
        body += path(f"M{f(-rx * 0.6)} {f(cy - ry * 1.0)} Q{f(0)} {f(cy - ry * 1.26)} {f(rx * 0.6)} {f(cy - ry * 0.98)}", None, lighten(hair, 0.45), 3, 0.7)
        body += circle(rx * 0.55, cy - ry * 0.95, 4.2, V["accent"], OUT, 1.6)  # a flame-red flower
        out["front"] = (body, (-rx - 12, cy - ry - 12, rx + 14, cy + ry * 0.6))
        # the cape: a high collar fan and a flowing cloak behind, swinging at the shoulders
        ts = P["sh_y"] - 8
        root = (0, ts + 4)
        cape = ""
        hem = P["hip_y"] - 4
        ck = [(-P["sw"] - 4, ts + 4), (-P["sw"] - 26, -hem + 8), (-P["sw"] - 12, -hem + 42)]
        cape_pts = [(-P["sw"] - 2, ts + 2), (-P["sw"] - 28, -hem * 0.5 - 20)]
        d = (f"M{f(-P['sw'] - 3)} {f(ts + 2)} L{f(P['sw'] + 3)} {f(ts + 2)} Q{f(P['sw'] + 34)} {f(-hem * 0.55)} {f(P['sw'] + 30)} {f(-hem + 48)} ")
        for k in range(6):
            xa = P["sw"] + 30 - k * (2 * (P["sw"] + 30) / 6)
            d += f"Q{f(xa - (P['sw'] + 30) / 6)} {f(-hem + 62)} {f(xa - (P['sw'] + 30) / 3)} {f(-hem + 48)} "
        d += "Z"
        cape += path(d, V["cape"], OUT, 3)
        cape += path(d.split("Q")[0] + "Z", None, None)
        lin = (f"M{f(-P['sw'] + 10)} {f(ts + 4)} L{f(P['sw'] - 10)} {f(ts + 4)} Q{f(P['sw'] + 10)} {f(-hem * 0.5)} {f(P['sw'] + 14)} {f(-hem + 44)} L{f(-P['sw'] - 14)} {f(-hem + 44)} Q{f(-P['sw'] - 10)} {f(-hem * 0.5)} {f(-P['sw'] + 10)} {f(ts + 4)} Z")
        cape += path(lin, V["lining"], None, op=0.9)
        for k in range(-3, 4):
            cape += line((k * 8, ts + 14), (k * 12, -hem + 44), darken(V["lining"], 0.3), 1.4, 0.4)
        collar = path(f"M{f(-14)} {f(ts + 2)} L{f(-34)} {f(ts - 52)} Q{f(-18)} {f(ts - 40)} {f(-8)} {f(ts - 58)} Q0 {f(ts - 42)} 8 {f(ts - 58)} Q{f(18)} {f(ts - 40)} 34 {f(ts - 52)} L14 {f(ts + 2)} Z", V["cape"], OUT, 3)
        collar += path(f"M-12 {f(ts)} L-28 {f(ts - 46)} M0 {f(ts)} L0 {f(ts - 48)} M12 {f(ts)} L28 {f(ts - 46)}", None, V["lining"], 2.4, sop=0.9)
        out["extra"].append(dict(name="cape", joint="torso", z=-22, body=cape, box=(-P["sw"] - 52, ts - 20, P["sw"] + 52, -hem + 74), swing=True, pivot_xy=root))
        out["extra"].append(dict(name="collar", joint="torso", z=-21, body=collar, box=(-46, ts - 70, 46, ts + 10), swing=False))
    return out


# ---- assembly ------------------------------------------------------------------------------------------------------------

def build_variant(arch, variant):
    P = ARCH[arch]
    V = VARIANTS[arch][variant]
    J = C.skeleton(P)
    base = f"chars/{arch}_{variant}/"
    parts = []

    def emit(name, joint, z, body, box, defs="", swing=False, pivot_xy=None):
        info = write_svg(base + name + ".svg", box, body, defs)
        pv = pivot_in(info, J[joint])
        e = {"name": name, "joint": joint, "z": z, "file": f"source/{base}{name}.svg", "pivot": pv, "px_scale": 0.5}
        if swing:
            e["swing"] = True
            e["swing_pivot"] = pivot_in(info, pivot_xy) if pivot_xy else pv
        parts.append(e)

    hair = hair_parts(arch, P, V)
    if hair["back"]:
        body, box, pv, sw_ = hair["back"]
        emit("hair_back", "head", -20, body, box, swing=sw_, pivot_xy=pv if (sw_ and pv) else None)
    for ex in hair["extra"]:
        emit(ex["name"], ex["joint"], ex["z"], ex["body"], ex["box"], swing=ex["swing"], pivot_xy=ex.get("pivot_xy"))
    for side in (-1, 1):
        n = "l" if side < 0 else "r"
        body, box = leg_part(arch, P, V, J, side)
        emit(f"leg_{n}", f"hip_{n}", -10, body, box)
    pel = pelvis_part(arch, P, V)
    if pel:
        emit("pelvis", "hips", -5, pel[0], pel[1])
    defs, body, box = torso_part(arch, P, V)
    emit("torso", "torso", 0, body, box, defs)
    if arch == "horned_queen":
        defs, body, box = skirt_part(P, V)
        emit("skirt", "hips", 2, body, box, defs)
    arms = {}
    for side in (-1, 1):
        n = "l" if side < 0 else "r"
        a = arm_parts(arch, P, V, J, side)
        arms[n] = a
        emit(f"arm_{n}_up", f"shoulder_{n}", 5, a["up"][0], a["up"][1])
        emit(f"arm_{n}_fore", f"elbow_{n}", 4, a["fore"][0], a["fore"][1])
    if arch == "brute":
        for side in (-1, 1):
            n = "l" if side < 0 else "r"
            defs, body, box = pauldron_part(P, V, J, side)
            emit(f"pauldron_{n}", "torso", 6, body, box, defs)
    defs, body, box = head_part(arch, P, V)
    emit("head", "head", 10, body, box, defs)
    faces = {}
    for ex in EXPRESSIONS:
        body, box = face_overlay(arch, P, V, ex)
        info = write_svg(f"{base}face_{ex}.svg", box, body)
        faces[ex] = {"file": f"source/{base}face_{ex}.svg", "pivot": pivot_in(info, J["head"]), "px_scale": 0.5}
    if hair["front"]:
        body, box = hair["front"][0], hair["front"][1]
        fdefs = hair["front"][2] if len(hair["front"]) > 2 and isinstance(hair["front"][2], str) else ""
        fsw = len(hair["front"]) > 3 and hair["front"][3]
        emit("hair_front", "head", 20, body, box, fdefs, swing=bool(fsw), pivot_xy=(0, P["cy"] - P["ry"] * 0.5) if fsw else None)
    fb = arms["r"]["fore"][1]
    hand = arms["r"]["fore"][2]
    hand_px = [round((hand[0] - math.floor(fb[0])) * 2, 1), round((hand[1] - math.floor(fb[1])) * 2, 1)]
    fbl = arms["l"]["fore"][1]
    handl = arms["l"]["fore"][2]
    hand_px_l = [round((handl[0] - math.floor(fbl[0])) * 2, 1), round((handl[1] - math.floor(fbl[1])) * 2, 1)]
    return {"parts": parts, "faces": faces, "face_z": 12,
            "glow_hand": {"joint": "elbow_r", "at": hand_px, "joint_l": "elbow_l", "at_l": hand_px_l}}


TOP_EXTRA = {"imp": 30, "brute": 40, "fiend": 28, "skeleton": 56, "flame": 120, "horned_queen": 64}


def build_all():
    out = {}
    for arch in ARCH:
        P = ARCH[arch]
        J = C.skeleton(P)
        entry = {"height": int(-(P["cy"] - P["ry"] - TOP_EXTRA[arch])),
                 "joints": {k: [round(v[0], 1), round(v[1], 1)] for k, v in J.items()}, "variants": {}}
        for variant in VARIANTS[arch]:
            v = build_variant(arch, variant)
            entry["variants"][variant] = v
        out[arch] = entry
    return out
