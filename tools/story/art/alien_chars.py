"""The six alien dancers of the `mothership` chapter, same rig contract as the Night One dancers (chars.py).

Same joints, part names (`torso head arm_l_up arm_l_fore arm_r_up arm_r_fore leg_l leg_r`, optional `pelvis`, `hair_back`,
`hair_front`), same four faces, rig space (origin between the feet, +y down). Different anatomy: big-headed grey, tall antenna
alien, jelly blob, mantis-like insect (wing-cases swing), cyclops, tentacle-crest. Friendly cartoon aliens, no gore.
"""
from __future__ import annotations

import math

from .chars import ARMS_REST_DEG, SHADE_GRAD, skeleton, torso_outline
from .lib import (OUT, bbox, capsule, circle, clip, darken, ellipse, f, group, lighten, line, mix, path, pivot_in, poly, rect,
                  union, write_svg)

BASE = "chars/"
ARCH = {
    "grey": dict(hip_y=100, sh_y=-170, sh_dx=22, neck_y=-178, cy=-213, rx=33, ry=37, up=37, fore=38, aw=11, sw=23, ww=15, hw=19, lw=13,
                 leg_dx=9, shoe_h=9, chin=0.34),
    "antenna": dict(hip_y=114, sh_y=-190, sh_dx=22, neck_y=-199, cy=-224, rx=22, ry=25, up=43, fore=46, aw=10, sw=22, ww=14, hw=17, lw=12,
                    leg_dx=9, shoe_h=10, chin=0.5),
    "blob": dict(hip_y=50, sh_y=-140, sh_dx=40, neck_y=-158, cy=-186, rx=27, ry=25, up=24, fore=27, aw=16, sw=46, ww=44, hw=40, lw=19,
                 leg_dx=17, shoe_h=8, chin=0.8),
    "insect": dict(hip_y=124, sh_y=-202, sh_dx=17, neck_y=-211, cy=-235, rx=19, ry=25, up=52, fore=54, aw=8, sw=18, ww=10, hw=13, lw=9,
                   leg_dx=8, shoe_h=8, chin=0.24),
    "cyclops": dict(hip_y=86, sh_y=-160, sh_dx=38, neck_y=-168, cy=-196, rx=30, ry=29, up=36, fore=36, aw=19, sw=40, ww=34, hw=33, lw=23,
                    leg_dx=16, shoe_h=12, chin=0.7),
    "tentacle": dict(hip_y=104, sh_y=-182, sh_dx=23, neck_y=-191, cy=-221, rx=24, ry=29, up=39, fore=41, aw=12, sw=24, ww=17, hw=21, lw=14,
                     leg_dx=11, shoe_h=9, chin=0.55),
}

# skin, body (suit / jelly), body2 (trim), accent (glow), iris
VARIANTS = {
    "grey": {
        "a": dict(skin="#b8c4d0", suit="#c9d3ea", trim="#19d2ff", accent="#ffc23f", iris="#19d2ff"),
        "b": dict(skin="#a9d8bd", suit="#e8d6ff", trim="#ff2f9d", accent="#19d2ff", iris="#ff2f9d"),
    },
    "antenna": {
        "a": dict(skin="#8fe07a", suit="#3b2a8a", trim="#4ff0a8", accent="#ff2f9d", iris="#ff2f9d"),
        "b": dict(skin="#ff8fc4", suit="#16708a", trim="#ffe36a", accent="#19d2ff", iris="#19d2ff"),
    },
    "blob": {
        "a": dict(skin="#6af0a0", suit="#9bffc8", trim="#e6fff2", accent="#ffe36a", iris="#0b0822"),
        "b": dict(skin="#d070ff", suit="#e6a8ff", trim="#fff0ff", accent="#19d2ff", iris="#0b0822"),
    },
    "insect": {
        "a": dict(skin="#a6d94a", suit="#5b8a1c", trim="#ff2f9d", accent="#ffe36a", iris="#0b0822"),
        "b": dict(skin="#ffb23f", suit="#b0561a", trim="#19d2ff", accent="#ff2f9d", iris="#0b0822"),
    },
    "cyclops": {
        "a": dict(skin="#ff9a4a", suit="#1fb7b0", trim="#ffe36a", accent="#ff2f9d", iris="#19d2ff"),
        "b": dict(skin="#a77aff", suit="#ffc23f", trim="#ff2f9d", accent="#19d2ff", iris="#4ff0a8"),
    },
    "tentacle": {
        "a": dict(skin="#c07aff", suit="#19b8c8", trim="#ffe36a", accent="#ff6fb8", iris="#ffe36a"),
        "b": dict(skin="#33d6c0", suit="#ff8a3a", trim="#fff0c4", accent="#9a70ff", iris="#ff2f9d"),
    },
}
EXPRESSIONS = ["neutral", "happy", "cheer", "sad"]
SKY = "#2a1b4e"


def rot(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


def add(p, v, k=1.0):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(dx, dy) or 1.0
    return (dx / ln, dy / ln)


def tapered(points, w0, w1, fill, outline=True, ol=2.6):
    """A tapered ribbon along a centre line (list of points): used for tentacles."""
    n = len(points)
    left, right = [], []
    for i, p in enumerate(points):
        a = points[max(i - 1, 0)]
        b = points[min(i + 1, n - 1)]
        u = unit(a, b)
        nx, ny = -u[1], u[0]
        w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append((p[0] + nx * w, p[1] + ny * w))
        right.append((p[0] - nx * w, p[1] - ny * w))
    return poly(left + right[::-1], fill, OUT if outline else None, ol)


def wave(p0, length, sway, phase, n=9, drift=0.0):
    out = []
    for i in range(n):
        t = i / (n - 1)
        out.append((p0[0] + drift * t + math.sin(t * 5.0 + phase) * sway * (0.25 + t), p0[1] + length * t))
    return out


# ---- heads -------------------------------------------------------------------------------------------------------------

def head_path(P, grow=0.0, topk=1.32):
    rx, ry, cy, ch = P["rx"] + grow, P["ry"] + grow, P["cy"], P["chin"]
    return (f"M{f(-rx)} {f(cy)} C{f(-rx)} {f(cy - ry * topk)} {f(rx)} {f(cy - ry * topk)} {f(rx)} {f(cy)} "
            f"C{f(rx)} {f(cy + ry * 0.7)} {f(rx * ch)} {f(cy + ry)} 0 {f(cy + ry)} "
            f"C{f(-rx * ch)} {f(cy + ry)} {f(-rx)} {f(cy + ry * 0.7)} {f(-rx)} {f(cy)} Z")


def head_part(arch, P, V):
    rx, ry, cy, ny = P["rx"], P["ry"], P["cy"], P["neck_y"]
    skin = V["skin"]
    d = head_path(P, 0, 1.38 if arch in ("tentacle", "grey") else 1.32)
    defs = clip("hc", f'<path d="{d}"/>') + SHADE_GRAD
    body = ""
    if arch != "blob":  # neck
        nw = 5.5 if arch in ("insect", "grey", "antenna") else 8
        body += rect(-nw, cy + ry * 0.55, nw * 2, ny - (cy + ry * 0.55) + 14, darken(skin, 0.14), OUT, 2.6, rx=3)
        body += rect(-nw, cy + ry * 0.78, nw * 2, 9, "#150a33", None, op=0.18)
    if arch == "cyclops":  # round ear nubs and two little horn buds
        for s in (-1, 1):
            body += ellipse(s * (rx - 1), cy + 4, 6, 7, skin, OUT, 2.4)
            body += circle(s * 14, cy - ry * 0.86, 5, V["trim"], OUT, 2.2)
    elif arch == "tentacle":  # fin ears
        for s in (-1, 1):
            body += path(f"M{f(s * (rx - 2))} {f(cy - 4)} Q{f(s * (rx + 15))} {f(cy - 14)} {f(s * (rx + 11))} {f(cy + 10)} Q{f(s * (rx + 4))} {f(cy + 6)} {f(s * (rx - 2))} {f(cy + 8)} Z", mix(skin, V["accent"], 0.4), OUT, 2.2)
    elif arch == "grey":  # small slit ears
        for s in (-1, 1):
            body += ellipse(s * (rx - 2), cy + 8, 3.2, 5, darken(skin, 0.1), OUT, 2)
    body += f'<path d="{d}" fill="{skin}"/>'
    inner = f'<rect x="{f(-rx - 4)}" y="{f(cy - ry * 1.4)}" width="{f(rx * 2 + 8)}" height="{f(ry * 2.6)}" fill="url(#shd)"/>'
    inner += f'<rect x="{f(-rx - 2)}" y="{f(cy - ry * 1.4)}" width="4.5" height="{f(ry * 2.6)}" fill="#19d2ff" fill-opacity="0.5"/>'
    inner += f'<rect x="{f(rx - 2.5)}" y="{f(cy - ry * 1.4)}" width="4.5" height="{f(ry * 2.6)}" fill="#ff2f9d" fill-opacity="0.4"/>'
    inner += ellipse(-rx * 0.36, cy - ry * 0.5, rx * 0.26, ry * 0.13, lighten(skin, 0.4), None, op=0.5)
    if arch == "grey":  # cranial ridge shading and a forehead seam
        inner += path(f"M{f(-rx * 0.5)} {f(cy - ry * 0.95)} Q0 {f(cy - ry * 1.15)} {f(rx * 0.5)} {f(cy - ry * 0.95)}", None, darken(skin, 0.25), 1.6, sop=0.6)
    if arch == "insect":  # head plate seam and cheek plates
        inner += path(f"M0 {f(cy - ry)} L0 {f(cy - ry * 0.35)}", None, darken(skin, 0.35), 1.8, sop=0.7)
        inner += path(f"M{f(-rx * 0.8)} {f(cy + ry * 0.15)} Q{f(-rx * 0.4)} {f(cy + ry * 0.6)} 0 {f(cy + ry)}", None, darken(skin, 0.35), 1.6, sop=0.6)
        inner += path(f"M{f(rx * 0.8)} {f(cy + ry * 0.15)} Q{f(rx * 0.4)} {f(cy + ry * 0.6)} 0 {f(cy + ry)}", None, darken(skin, 0.35), 1.6, sop=0.6)
    if arch == "tentacle":  # glowing freckle dots on the crest
        for k, (x, y) in enumerate(((-9, -0.88), (-3, -1.02), (4, -0.94), (10, -0.8), (0, -0.7))):
            inner += circle(x, cy + ry * y, 1.7, V["trim"], None, op=0.9)
    if arch == "cyclops":
        inner += ellipse(rx * 0.55, cy + ry * 0.5, 4, 2.6, darken(skin, 0.2), None, op=0.5)
    body += group(inner, 'clip-path="url(#hc)"')
    body += path(d, None, OUT, 3)
    if arch == "blob":  # glossy jelly highlight on top of the outline
        body += path(f"M{f(-rx * 0.62)} {f(cy - ry * 0.4)} Q{f(-rx * 0.5)} {f(cy - ry * 0.9)} {f(-rx * 0.05)} {f(cy - ry * 0.95)}", None, "#ffffff", 3.4, sop=0.6)
    return defs, body, (-rx - 22, cy - ry - 10, rx + 22, ny + 18)


# ---- faces ---------------------------------------------------------------------------------------------------------------

def _local_path(cx, cy, tilt, pts):
    """Quadratic almond given local points rotated by tilt degrees around its centre."""
    P_ = [rot(p, tilt) for p in pts]
    P_ = [(cx + p[0], cy + p[1]) for p in P_]
    return P_


def almond(cx, cy, w, h, tilt, fill, glint=True):
    a, c1, b, c2 = _local_path(cx, cy, tilt, [(-w, 0), (0, -h * 1.35), (w, 0), (0, h * 1.15)])
    d = f"M{f(a[0])} {f(a[1])} Q{f(c1[0])} {f(c1[1])} {f(b[0])} {f(b[1])} Q{f(c2[0])} {f(c2[1])} {f(a[0])} {f(a[1])} Z"
    out = path(d, fill, OUT, 1.8)
    if glint:
        g = _local_path(cx, cy, tilt, [(-w * 0.35, -h * 0.35), (w * 0.38, h * 0.1)])
        out += ellipse(g[0][0], g[0][1], w * 0.2, h * 0.28, "#ffffff", None, op=0.95)
        out += circle(g[1][0], g[1][1], h * 0.12, "#bff6ff", None, op=0.85)
    return out


def eyeball(cx, cy, rx, ry, iris, pupil=2.6, look=0.0):
    out = ellipse(cx, cy, rx, ry, "#ffffff", OUT, 1.8)
    out += circle(cx + look * 1.5, cy + 0.6, min(rx, ry) * 0.78, iris, OUT, 1.0)
    out += circle(cx + look * 1.5, cy + 0.6, pupil, "#1a0f3a")
    out += circle(cx + look * 1.5 + 1.9, cy - 1.5, 1.5, "#ffffff")
    return out


def lid_top(cx, cy, rx, ry, drop, skin, tilt=0.0, side=1):
    """A skin lid covering the top of an eye: drop is the height covered, tilt slants it (sad)."""
    y0 = cy - ry - 2
    yl = cy - ry + drop + tilt * side * -1
    yr = cy - ry + drop + tilt * side
    return path(f"M{f(cx - rx - 1)} {f(y0)} L{f(cx + rx + 1)} {f(y0)} L{f(cx + rx + 1)} {f(yr)} Q{f(cx)} {f(cy - ry + drop + 1.5)} {f(cx - rx - 1)} {f(yl)} Z", skin, OUT, 1.5)


def smile_arc(cx, cy, w, h, color, sw=2.2):
    return path(f"M{f(cx - w)} {f(cy)} Q{f(cx)} {f(cy - h)} {f(cx + w)} {f(cy)}", None, color, sw)


def mouth(expr, y, w, skin, tongue="#ff6f9c", fangs=False):
    dark = "#4a1636"
    if expr == "neutral":
        return path(f"M{f(-w * 0.7)} {f(y)} Q0 {f(y + w * 0.5)} {f(w * 0.7)} {f(y)}", None, dark, 2.2)
    if expr == "happy":
        return (path(f"M{f(-w)} {f(y - 1)} Q0 {f(y + w * 1.2)} {f(w)} {f(y - 1)} Q0 {f(y + w * 0.3)} {f(-w)} {f(y - 1)} Z", "#7a1f45", OUT, 1.6) +
                path(f"M{f(-w * 0.8)} {f(y - 0.4)} Q0 {f(y + w * 0.4)} {f(w * 0.8)} {f(y - 0.4)} L{f(w * 0.7)} {f(y + 1.2)} Q0 {f(y + w * 0.7)} {f(-w * 0.7)} {f(y + 1.2)} Z", "#ffffff", None))
    if expr == "cheer":
        my = y - 3
        s = path(f"M{f(-w * 1.2)} {f(my)} L{f(w * 1.2)} {f(my)} Q{f(w * 1.1)} {f(my + w * 1.9)} 0 {f(my + w * 1.9)} Q{f(-w * 1.1)} {f(my + w * 1.9)} {f(-w * 1.2)} {f(my)} Z", "#6e1540", OUT, 2)
        s += path(f"M{f(-w * 1.05)} {f(my + 0.8)} L{f(w * 1.05)} {f(my + 0.8)} L{f(w * 0.95)} {f(my + 4.4)} L{f(-w * 0.95)} {f(my + 4.4)} Z", "#ffffff", None)
        s += ellipse(0, my + w * 1.5, w * 0.6, w * 0.42, tongue, None)
        return s
    return path(f"M{f(-w * 0.7)} {f(y + 3.4)} Q0 {f(y - 2.6)} {f(w * 0.7)} {f(y + 3.4)}", None, dark, 2.4)


def sweat(P):
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    return path(f"M{f(rx * 0.72)} {f(cy - ry * 0.35)} Q{f(rx * 0.95)} {f(cy - ry * 0.05)} {f(rx * 0.72)} {f(cy + ry * 0.1)} Q{f(rx * 0.5)} {f(cy - ry * 0.05)} {f(rx * 0.72)} {f(cy - ry * 0.35)} Z", "#8fe6ff", OUT, 1.4)


def blush(x, y, w=4.5, col="#ff4f9a", op=0.4):
    return ellipse(x, y, w, w * 0.58, col, None, op=op)


def face_overlay(arch, P, V, expr):
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    skin = V["skin"]
    b = ""
    brow = "#1b1330"
    if arch == "grey":
        ex, ey = rx * 0.42, cy + 5
        w, h = 10.6, 6.8  # the classic huge black almond eyes, slanting outward
        tilt = {"neutral": 14, "happy": 6, "cheer": 0, "sad": 28}[expr]
        for s in (-1, 1):
            if expr == "cheer":
                b += path(f"M{f(s * ex - 9)} {f(ey + 2.6)} Q{f(s * ex)} {f(ey - 11)} {f(s * ex + 9)} {f(ey + 2.6)}", None, "#150a33", 4.2)
                b += path(f"M{f(s * ex - 6)} {f(ey - 1.5)} Q{f(s * ex)} {f(ey - 7.5)} {f(s * ex + 6)} {f(ey - 1.5)}", None, V["trim"], 1.4, sop=0.8)
            else:
                b += almond(s * ex, ey + (1.5 if expr == "sad" else 0), w, h, s * tilt, "#0b0822")
                b += ellipse(s * ex + s * 1.5, ey + 1.2, w * 0.55, h * 0.42, V["iris"], None, op=0.22)  # a faint coloured sheen
            if expr == "happy":  # cheeks push the lower lids up into a smile
                b += path(f"M{f(s * ex - w - 1)} {f(ey + h + 3)} Q{f(s * ex)} {f(ey + 0.5)} {f(s * ex + w + 1)} {f(ey + h + 3)} Z", skin, None)
                b += path(f"M{f(s * ex - w + 1)} {f(ey + h * 0.6)} Q{f(s * ex)} {f(ey + 0.8)} {f(s * ex + w - 1)} {f(ey + h * 0.6)}", None, OUT, 1.6)
        if expr in ("happy", "cheer"):
            b += blush(-ex - 3, ey + 11, 4.6, V["trim"], 0.45) + blush(ex + 3, ey + 11, 4.6, V["trim"], 0.45)
        if expr == "sad":
            b += line((-ex - 6, ey - 8), (-ex + 5, ey - 11), brow, 1.8, 0.8) + line((ex - 5, ey - 11), (ex + 6, ey - 8), brow, 1.8, 0.8)
            b += sweat(P)
        b += circle(-2, cy + ry * 0.36, 0.9, darken(skin, 0.4)) + circle(2, cy + ry * 0.36, 0.9, darken(skin, 0.4))  # nose slits
        b += mouth(expr, cy + ry * 0.66, 5.0 if expr != "cheer" else 5.6, skin)
    elif arch == "antenna":
        ex, ey, er = rx * 0.43, cy + 2, 5.4
        ery = er * 1.25
        b += _round_eyes(expr, ex, ey, er, ery, V, skin, brow, P)
        b += mouth(expr, cy + ry * 0.58, 6.4, skin)
        if expr in ("happy", "cheer"):
            b += blush(-ex - 4, ey + 9) + blush(ex + 4, ey + 9)
    elif arch == "tentacle":
        ex, ey, er = rx * 0.42, cy + 3, 5.2
        ery = er * 1.3
        b += _round_eyes(expr, ex, ey, er, ery, V, skin, brow, P, lashes=True)
        b += mouth(expr, cy + ry * 0.56, 5.6, skin)
        if expr in ("happy", "cheer"):
            b += blush(-ex - 3, ey + 9, 4.6, V["accent"], 0.5) + blush(ex + 3, ey + 9, 4.6, V["accent"], 0.5)
    elif arch == "blob":
        ex, ey = rx * 0.38, cy + 2
        for s in (-1, 1):
            if expr == "cheer":
                b += path(f"M{f(s * ex - 5.5)} {f(ey + 1.6)} Q{f(s * ex)} {f(ey - 7)} {f(s * ex + 5.5)} {f(ey + 1.6)}", None, "#0b0822", 3)
            elif expr == "happy":
                b += circle(s * ex, ey, 5.6, "#0b0822") + circle(s * ex + 1.7, ey - 1.8, 1.9, "#ffffff") + circle(s * ex - 1.6, ey + 1.8, 0.9, "#ffffff")
                b += path(f"M{f(s * ex - 6)} {f(ey + 5.4)} Q{f(s * ex)} {f(ey + 2.2)} {f(s * ex + 6)} {f(ey + 5.4)}", V["skin"], None)
            else:
                yy = ey + (1.5 if expr == "sad" else 0)
                b += circle(s * ex, yy, 5.8, "#0b0822") + circle(s * ex + 1.8, yy - 2, 2.1, "#ffffff") + circle(s * ex - 1.6, yy + 2, 1.0, "#ffffff")
        if expr == "sad":
            b += line((-ex - 6, ey - 8.5), (-ex + 5, ey - 11.5), "#0b0822", 2.2) + line((ex - 5, ey - 11.5), (ex + 6, ey - 8.5), "#0b0822", 2.2)
            b += sweat(P)
        b += mouth(expr, cy + ry * 0.52, 8.6 if expr != "cheer" else 8.0, skin)
        b += blush(-ex - 5, ey + 8.5, 4.6, "#ff4f9a", 0.4) + blush(ex + 5, ey + 8.5, 4.6, "#ff4f9a", 0.4)
    elif arch == "insect":
        ex, ey = 9.5, cy - 1
        tilt = {"neutral": 22, "happy": 16, "cheer": 10, "sad": 38}[expr]
        for s in (-1, 1):
            ang = s * tilt  # big compound eyes slanting outward-down
            c = (s * ex, ey)
            q = [(c[0] + p[0], c[1] + p[1]) for p in [rot(p, ang) for p in ((0, -11), (8.5, -5), (7.6, 6), (0, 11.5), (-7.6, 6), (-8.5, -5))]]
            d = f"M{f(q[0][0])} {f(q[0][1])} Q{f(q[1][0])} {f(q[1][1])} {f(q[2][0])} {f(q[2][1])} Q{f(q[3][0])} {f(q[3][1])} {f(q[4][0])} {f(q[4][1])} Q{f(q[5][0])} {f(q[5][1])} {f(q[0][0])} {f(q[0][1])} Z"
            if expr == "cheer":  # squeezed shut with joy: thick happy arcs, a bright facet line
                b += path(f"M{f(s * ex - 7.5)} {f(ey + 3)} Q{f(s * ex)} {f(ey - 9)} {f(s * ex + 7.5)} {f(ey + 3)}", None, "#1b1342", 4.4)
                b += path(f"M{f(s * ex - 5)} {f(ey - 1.5)} Q{f(s * ex)} {f(ey - 6.5)} {f(s * ex + 5)} {f(ey - 1.5)}", None, V["trim"], 1.5, sop=0.9)
                continue
            b += path(d, "#1b1342", OUT, 2)
            g1, g2, g3 = [(c[0] + p[0], c[1] + p[1]) for p in (rot((-2.2, -4.5), ang), rot((2.4, 1.5), ang), rot((-1.4, 5.0), ang))]
            b += ellipse(g1[0], g1[1], 2.2, 3.4, "#ffffff", None, op=0.9) + circle(g2[0], g2[1], 1.2, V["trim"], None, op=0.95) + circle(g3[0], g3[1], 0.9, "#ffffff", None, op=0.7)
            for k in (-3, 0, 3):  # compound facets
                fa = rot((k, -2), ang)
                b += circle(c[0] + fa[0], c[1] + fa[1] + 4, 0.8, V["trim"], None, op=0.5)
            if expr == "happy":  # cheek plates push up under the eyes
                b += path(f"M{f(s * ex - 10)} {f(ey + 12)} Q{f(s * ex)} {f(ey + 2)} {f(s * ex + 10)} {f(ey + 12)} Z", V["skin"], None)
                b += path(f"M{f(s * ex - 7.5)} {f(ey + 7.5)} Q{f(s * ex)} {f(ey + 2.4)} {f(s * ex + 7.5)} {f(ey + 7.5)}", None, OUT, 1.6)
            if expr == "sad":  # heavy lids drooping toward the outside
                xi, xo = s * ex - s * 9.5, s * ex + s * 9.5
                b += path(f"M{f(xi)} {f(ey - 14)} L{f(xo)} {f(ey - 14)} L{f(xo)} {f(ey + 1.5)} Q{f(s * ex)} {f(ey - 1.5)} {f(xi)} {f(ey - 5)} Z", V["skin"], None)
                b += path(f"M{f(xo)} {f(ey + 1.5)} Q{f(s * ex)} {f(ey - 1.5)} {f(xi)} {f(ey - 5)}", None, OUT, 1.6)
        if expr == "sad":
            b += line((-ex - 7, ey - 13), (-ex + 6, ey - 17), "#2a1b4e", 2.2) + line((ex - 6, ey - 17), (ex + 7, ey - 13), "#2a1b4e", 2.2)
            b += sweat(P)
        if expr in ("happy", "cheer"):
            b += blush(-ex - 7, ey + 9, 3.6, V["trim"], 0.5) + blush(ex + 7, ey + 9, 3.6, V["trim"], 0.5)
        # mandibles and mouth
        my = cy + ry * 0.7
        mc = {"neutral": 0.0, "happy": 2.6, "cheer": 5.0, "sad": -1.5}[expr]
        for s in (-1, 1):
            dd = f"M{f(s * 3.4)} {f(my - 1)} Q{f(s * (7 + mc * 0.4))} {f(my + 1 + mc * 0.5)} {f(s * (7.6 + mc * 0.5))} {f(my + 6 + mc)}"
            b += path(dd, None, OUT, 3.8) + path(dd, None, V["trim"], 1.5)
        if expr == "happy":
            b += path(f"M-4 {f(my + 0.5)} Q0 {f(my + 6)} 4 {f(my + 0.5)} Z", "#7a1f45", OUT, 1.3)
        elif expr == "cheer":
            b += path(f"M-5 {f(my)} L5 {f(my)} Q4.6 {f(my + 8)} 0 {f(my + 8)} Q-4.6 {f(my + 8)} -5 {f(my)} Z", "#6e1540", OUT, 1.5)
            b += ellipse(0, my + 5.5, 2.6, 1.6, "#ff6f9c", None)
        elif expr == "sad":
            b += path(f"M-3.4 {f(my + 4)} Q0 {f(my + 1)} 3.4 {f(my + 4)}", None, "#4a1636", 1.8)
    else:  # cyclops: one big eye
        ey = cy + 1
        er_x, er_y = 14.5, 12.5
        if expr == "cheer":
            b += path(f"M-14 {f(ey + 3)} Q0 {f(ey - 17)} 14 {f(ey + 3)}", None, "#150a33", 3.6)
            b += blush(-20, ey + 4, 4, "#ffffff", 0.0)
        else:
            lk = -0.6 if expr == "sad" else 0
            b += eyeball(0, ey + (1 if expr == "sad" else 0), er_x, er_y, V["iris"], 4.6, lk)
            b += circle(0, ey, er_x - 0.5, None, "#ffffff", 0.0)
            if expr == "happy":  # lower lid pushed up
                b += path(f"M{f(-er_x - 1)} {f(ey + 12)} Q0 {f(ey + 2)} {f(er_x + 1)} {f(ey + 12)} L{f(er_x + 1)} {f(ey + 15)} L{f(-er_x - 1)} {f(ey + 15)} Z", skin, OUT, 1.5)
            if expr == "sad":
                b += lid_top(0, ey + 1, er_x, er_y, 9, skin, 0, 1)
                b += path(f"M{f(-er_x)} {f(ey - 8)} L{f(er_x)} {f(ey - 8)}", None, None, 0)
        by_ = ey - er_y - 4
        if expr == "sad":
            b += path(f"M-12 {f(by_ + 4)} Q-2 {f(by_ - 3)} 12 {f(by_ - 3.5)}", None, brow, 2.8, sop=1)
        elif expr == "cheer":
            b += path(f"M-13 {f(by_ - 3)} Q0 {f(by_ - 10)} 13 {f(by_ - 3)}", None, brow, 2.8)
        else:
            b += path(f"M-12 {f(by_ + 1.6)} Q0 {f(by_ - 3.6 - (2 if expr == 'happy' else 0))} 12 {f(by_ + 1.6)}", None, brow, 2.8)
        if expr == "sad":
            b += sweat(P)
        b += mouth(expr, cy + ry * 0.64, 7.5 if expr != "cheer" else 7.5, skin)
        if expr in ("happy", "cheer"):
            b += blush(-20, ey + 10, 5, "#ff4f9a", 0.4) + blush(20, ey + 10, 5, "#ff4f9a", 0.4)
        if expr != "cheer":  # a tooth peeking in the neutral and sad mouth is cute but keep it on happy only
            pass
    return b, (-rx - 12, cy - ry - 10, rx + 12, cy + ry + 8)


def _round_eyes(expr, ex, ey, er, ery, V, skin, brow, P, lashes=False):
    b = ""
    iris = V["iris"]
    for s in (-1, 1):
        if expr == "cheer":
            b += path(f"M{f(s * ex - 5.5)} {f(ey + 1.6)} Q{f(s * ex)} {f(ey - 7)} {f(s * ex + 5.5)} {f(ey + 1.6)}", None, "#2a1b4e", 3)
            if lashes:
                b += line((s * ex + s * 5, ey - 1), (s * ex + s * 8, ey - 4), OUT, 1.5)
            continue
        yy = ey + (1 if expr == "sad" else 0)
        b += eyeball(s * ex, yy, er, ery * (0.9 if expr == "happy" else 1), iris, 2.6, -0.5 if expr == "sad" else 0)
        if lashes:
            for k in range(3):
                b += line((s * (ex + er - 0.5), yy - 1.5), (s * (ex + er + 1.6 + k * 0.5), yy - 3.8 - k * 1.7), OUT, 1.5)
        if expr == "happy":
            b += path(f"M{f(s * ex - 5.5)} {f(yy + ery - 0.5)} Q{f(s * ex)} {f(yy + ery - 5)} {f(s * ex + 5.5)} {f(yy + ery - 0.5)} L{f(s * ex + 5.5)} {f(yy + ery + 2)} L{f(s * ex - 5.5)} {f(yy + ery + 2)} Z", skin, None)
            b += path(f"M{f(s * ex - 5.5)} {f(yy + ery - 0.5)} Q{f(s * ex)} {f(yy + ery - 5)} {f(s * ex + 5.5)} {f(yy + ery - 0.5)}", None, OUT, 1.5)
        if expr == "sad":
            b += lid_top(s * ex, yy, er, ery, ery * 0.95, skin, 2.0, s)
    by_ = ey - ery - 4.5
    if expr == "sad":
        b += line((-ex - 5.5, by_ + 3.2), (-ex + 4.5, by_ - 2.6), brow, 2.4) + line((ex - 4.5, by_ - 2.6), (ex + 5.5, by_ + 3.2), brow, 2.4)
        b += sweat(P)
    elif expr == "neutral":
        b += line((-ex - 5, by_ + 0.5), (-ex + 5, by_ - 0.6), brow, 2.4) + line((ex - 5, by_ - 0.6), (ex + 5, by_ + 0.5), brow, 2.4)
    else:
        by_ -= 2
        b += path(f"M{f(-ex - 5)} {f(by_ + 1.8)} Q{f(-ex)} {f(by_ - 1.6)} {f(-ex + 5)} {f(by_ + 0.8)}", None, brow, 2.4)
        b += path(f"M{f(ex - 5)} {f(by_ + 0.8)} Q{f(ex)} {f(by_ - 1.6)} {f(ex + 5)} {f(by_ + 1.8)}", None, brow, 2.4)
    return b


# ---- hair-like swinging parts ------------------------------------------------------------------------------------------------

def antennae(P, V):
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    base = cy - ry * 0.98
    b = ""
    tips = []
    for s in (-1, 1):
        p0 = (s * 6, base + 4)
        p1 = (s * 17, base - 22)
        p2 = (s * 24, base - 36)
        d = f"M{f(p0[0])} {f(p0[1])} Q{f(p1[0])} {f(p1[1] + 4)} {f(p2[0])} {f(p2[1])}"
        b += path(d, None, OUT, 6.4) + path(d, None, V["skin"], 3.2) + path(d, None, V["trim"], 1.0, sop=0.9)
        tips.append(p2)
    for p2 in tips:
        for r, op in ((16, 0.1), (12, 0.18), (9, 0.3)):
            b += circle(p2[0], p2[1], r, V["accent"], None, op=op)
        b += circle(p2[0], p2[1], 6.6, V["accent"], OUT, 2.4) + circle(p2[0] - 1.6, p2[1] - 1.8, 2.4, "#ffffff", None, op=0.95)
    box = bbox([(-26, base - 38), (26, base - 38), (0, base + 6)], 22)
    return b, box, (0, base + 4)


def tentacle_hair(P, V):
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    skin = V["skin"]
    tc = mix(skin, V["accent"], 0.3)
    b = ""
    items = [(-20, 56, 6.0, 0.0, -14), (-10, 74, 6.4, 1.3, -7), (0, 84, 6.6, 2.4, 0), (10, 74, 6.4, 3.6, 7), (20, 56, 6.0, 4.7, 14)]
    order = [0, 4, 1, 3, 2]
    tips = []
    for i in order:
        x0, ln, w, ph, drift = items[i]
        base_y = cy - ry * 0.5 + abs(x0) * 0.15
        pts_ = wave((x0, base_y), ln + ry * 0.9, 4.0, ph, drift=drift * 1.2)
        b += tapered(pts_, w * 1.7, 2.4, tc)
        # sucker dots along the inside
        for k in (2, 4, 6):
            p = pts_[k]
            b += circle(p[0], p[1], 1.5, lighten(tc, 0.45), None, op=0.85)
        tips.append(pts_[-1])
    for p in tips:
        b += circle(p[0], p[1], 5, V["trim"], None, op=0.28) + circle(p[0], p[1], 2.5, V["trim"], OUT, 1.4)
    box = (-52, cy - ry * 0.7, 52, cy + 150)
    return b, box, (0, cy - ry * 0.6)


def tentacle_front(P, V):
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    tc = mix(V["skin"], V["accent"], 0.3)
    b = ""
    for s in (-1, 1):
        pts_ = wave((s * (rx - 2), cy - ry * 0.35), 62, 3.2, 1.0 + s, drift=s * 6)
        b += tapered(pts_, 9.5, 2.2, tc)
        for k in (2, 4, 5):
            b += circle(pts_[k][0], pts_[k][1], 1.4, lighten(tc, 0.5), None, op=0.85)
        b += circle(pts_[-1][0], pts_[-1][1], 2.4, V["trim"], OUT, 1.4)
    return b, (-rx - 30, cy - ry * 0.5, rx + 30, cy + 90)


def feelers(P, V):
    """The insect's two thin feelers: they leave the brow, arch outward and end in small glowing knobs (a swinging part)."""
    rx, ry, cy = P["rx"], P["ry"], P["cy"]
    base = cy - ry * 0.82
    b = ""
    for s in (-1, 1):
        p0 = (s * 5, base + 2)
        c1 = (s * 4, base - 30)
        p2 = (s * 30, base - 40)
        d = f"M{f(p0[0])} {f(p0[1])} Q{f(c1[0])} {f(c1[1])} {f(p2[0])} {f(p2[1])}"
        b += path(d, None, OUT, 5.2) + path(d, None, V["suit"], 2.4)
        b += circle(p2[0], p2[1], 7, V["trim"], None, op=0.18) + circle(p2[0], p2[1], 3.6, V["trim"], OUT, 1.8) + circle(p2[0] - 1, p2[1] - 1, 1.2, "#ffffff")
    box = bbox([(-40, base - 50), (40, base - 50), (0, base + 6)], 10)
    return b, box, (0, base + 2)


def wing_cases(P, V):
    sh = P["sh_y"]
    hip = -P["hip_y"]
    b = ""
    col = mix(V["suit"], V["skin"], 0.25)
    for s in (-1, 1):
        d = (f"M{f(s * 4)} {f(sh - 2)} Q{f(s * 34)} {f(sh + 22)} {f(s * 30)} {f(hip - 6)} Q{f(s * 24)} {f(hip + 28)} {f(s * 12)} {f(hip + 26)} "
             f"Q{f(s * 6)} {f(hip)} {f(s * 3)} {f(sh + 18)} Z")
        b += path(d, col, OUT, 3)
        b += path(d, V["trim"], None, op=0.16)
        for k in range(1, 5):
            t = k / 5
            b += path(f"M{f(s * 5)} {f(sh + 4 + t * 20)} Q{f(s * (14 + 14 * t))} {f(sh + 40 + t * 60)} {f(s * (26 - 10 * t))} {f(hip + 10 + t * 8)}", None, darken(col, 0.4), 1.2, sop=0.55)
        b += path(f"M{f(s * 8)} {f(sh + 10)} Q{f(s * 24)} {f(sh + 40)} {f(s * 23)} {f(hip - 14)}", None, "#ffffff", 1.8, sop=0.4)
    return b, (-44, sh - 8, 44, hip + 36), (0, sh - 2)


# ---- body -----------------------------------------------------------------------------------------------------------------------

def blob_outline(P):
    cx0, cy0 = 0, -P["hip_y"] - 54
    return (f"M0 {f(cy0 - 66)} C{f(34)} {f(cy0 - 66)} {f(50)} {f(cy0 - 34)} {f(48)} {f(cy0 + 8)} C{f(47)} {f(cy0 + 40)} {f(30)} {f(cy0 + 58)} 0 {f(cy0 + 58)} "
            f"C{f(-30)} {f(cy0 + 58)} {f(-47)} {f(cy0 + 40)} {f(-48)} {f(cy0 + 8)} C{f(-50)} {f(cy0 - 34)} {f(-34)} {f(cy0 - 66)} 0 {f(cy0 - 66)} Z")


def torso_part(arch, P, V):
    sw, ww, hw = P["sw"], P["ww"], P["hw"]
    ts = P["sh_y"] - 8
    wy = -P["hip_y"] - 34
    by = -P["hip_y"] + 14
    skin, suit, trim, acc = V["skin"], V["suit"], V["trim"], V["accent"]
    if arch == "blob":
        d = blob_outline(P)
        cy0 = -P["hip_y"] - 54
        defs = clip("tc", f'<path d="{d}"/>') + SHADE_GRAD
        body = f'<path d="{d}" fill="{skin}" fill-opacity="0.9"/>'
        inner = ellipse(0, cy0 + 8, 40, 50, suit, None, op=0.55)
        inner += ellipse(0, cy0 + 12, 24, 32, lighten(suit, 0.3), None, op=0.5)
        # glowing nucleus
        for r, op in ((18, 0.2), (13, 0.35), (9, 0.6)):
            inner += circle(0, cy0 + 14, r, V["accent"], None, op=op)
        inner += circle(0, cy0 + 14, 5.5, "#ffffff", None, op=0.95)
        rng = [(-26, -28, 5), (22, -36, 3.6), (-30, 24, 3.6), (26, 16, 5.4), (-10, 40, 3), (14, 44, 4.2), (-16, -48, 3)]
        for x, y, r in rng:
            inner += circle(x, cy0 + y, r, "#ffffff", None, op=0.28) + circle(x, cy0 + y, r, None, "#ffffff", 1.1, sop=0.6)
        if V["accent"] == "#ffe36a":  # variant a: spots
            for x, y in ((-12, 36), (4, -36), (20, 28)):
                inner += circle(x, cy0 + y, 4.4, darken(skin, 0.2), None, op=0.55)
        else:  # variant b: curved stripes
            for k in (-1, 0, 1):
                inner += path(f"M{f(-44)} {f(cy0 + k * 22 + 10)} Q0 {f(cy0 + k * 22 - 6)} {f(44)} {f(cy0 + k * 22 + 10)}", None, darken(skin, 0.3), 3, sop=0.45)
        body += group(inner, 'clip-path="url(#tc)"')
        body += group(f'<rect x="-56" y="{f(cy0 - 70)}" width="112" height="140" fill="url(#shd)"/>'
                      f'<rect x="-52" y="{f(cy0 - 70)}" width="6" height="140" fill="#19d2ff" fill-opacity="0.45"/>'
                      f'<rect x="46" y="{f(cy0 - 70)}" width="6" height="140" fill="#ff2f9d" fill-opacity="0.35"/>', 'clip-path="url(#tc)"')
        body += path(d, None, OUT, 3)
        body += path(f"M-34 {f(cy0 - 40)} Q-40 {f(cy0 - 14)} -36 {f(cy0 + 6)}", None, "#ffffff", 3.6, sop=0.55)
        return defs, body, (-58, cy0 - 72, 58, cy0 + 64)
    d = torso_outline(P)
    defs = clip("tc", f'<path d="{d}"/>') + SHADE_GRAD
    base = suit
    inner = ""
    if arch == "grey":  # silver jumpsuit, collar, zip, chest emblem, belt
        inner += rect(-sw - 4, ts - 6, sw * 2 + 8, by - ts + 12, f"{lighten(suit, 0.25)}", None, op=0.35)
        inner += poly([(-9, ts - 4), (9, ts - 4), (0, ts + 14)], skin, OUT, 1.8)
        inner += path(f"M-12 {f(ts - 4)} L0 {f(ts + 18)} L12 {f(ts - 4)}", None, trim, 3)
        inner += line((0, ts + 18), (0, by - 12), darken(suit, 0.35), 1.6, 0.8)
        if V["trim"] == "#19d2ff":
            inner += circle(-9, ts + 30, 5.5, "#0b0822", OUT, 1.6) + poly([(-9, ts + 25), (-7.5, ts + 29), (-3.8, ts + 29.4), (-6.6, ts + 31.8), (-5.6, ts + 36), (-9, ts + 33.5), (-12.4, ts + 36), (-11.4, ts + 31.8), (-14.2, ts + 29.4), (-10.5, ts + 29)], acc, None)
        else:
            inner += poly([(-9, ts + 24), (-2, ts + 36), (-16, ts + 36)], "#0b0822", OUT, 1.6) + circle(-9, ts + 32, 2, acc)
            inner += line((-sw + 3, ts + 18), (-ww + 2, wy), trim, 3.2, 0.9) + line((sw - 3, ts + 18), (ww - 2, wy), trim, 3.2, 0.9)
        inner += rect(-hw - 2, by - 14, hw * 2 + 4, 7, trim, OUT, 1.8) + rect(-4, by - 14, 8, 7, acc, OUT, 1.4)
    elif arch == "antenna":  # dark tunic with glowing circuit lines
        inner += poly([(-9, ts - 4), (9, ts - 4), (0, ts + 12)], skin, OUT, 1.8)
        for x in (-12, 12):
            inner += path(f"M{f(x)} {f(ts + 6)} L{f(x)} {f(ts + 30)} L{f(x * 0.5)} {f(ts + 40)} L{f(x * 0.5)} {f(by - 14)}", None, trim, 2.2)
            inner += circle(x, ts + 30, 2.4, acc, OUT, 1)
        inner += path(f"M-{ww} {f(wy + 4)} H{ww}", None, trim, 2.2) + circle(0, ts + 20, 4.4, trim, OUT, 1.5) + circle(0, ts + 20, 1.8, "#ffffff")
        if V["accent"] == "#19d2ff":
            inner += path(f"M-{f(sw)} {f(ts + 12)} L{f(sw)} {f(ts + 12)}", None, trim, 3)
            inner += poly([(-sw - 2, ts - 4), (-sw + 12, ts - 4), (-sw - 2, ts + 22)], trim, None, op=0.75) + poly([(sw + 2, ts - 4), (sw - 12, ts - 4), (sw + 2, ts + 22)], trim, None, op=0.75)
        inner += rect(-hw - 2, by - 14, hw * 2 + 4, 7, darken(suit, 0.4), OUT, 1.8) + rect(-4, by - 14, 8, 7, acc, OUT, 1.4)
    elif arch == "insect":  # segmented thorax plates
        base = skin
        for k in range(5):
            y = ts + 6 + k * 15
            inner += path(f"M{f(-sw - 2)} {f(y)} Q0 {f(y + 9)} {f(sw + 2)} {f(y)} L{f(sw + 2)} {f(y + 13)} Q0 {f(y + 20)} {f(-sw - 2)} {f(y + 13)} Z", suit if k % 2 == 0 else mix(suit, skin, 0.4), OUT, 1.8)
        inner += line((0, ts), (0, by), trim, 2.2, 0.9)
        inner += circle(0, ts + 12, 3.2, acc, OUT, 1.4)
        if V["trim"] == "#19d2ff":
            inner += circle(-6, ts + 34, 1.8, trim) + circle(6, ts + 34, 1.8, trim) + circle(-5, ts + 50, 1.6, trim) + circle(5, ts + 50, 1.6, trim)
    elif arch == "cyclops":  # t-shirt and bib overalls
        base = trim if V["trim"] != "#ffe36a" else "#fff0a8"
        base = lighten(suit, 0.55)
        inner += rect(-hw - 6, wy - 16, hw * 2 + 12, by - wy + 22, suit, OUT, 2.4, rx=3)
        inner += rect(-14, wy - 6, 28, 22, darken(suit, 0.15), OUT, 1.8, rx=3)
        for s in (-1, 1):
            inner += poly([(s * 8, ts - 4), (s * 20, ts - 4), (s * 18, wy - 14), (s * 8, wy - 14)], suit, OUT, 2.2)
            inner += circle(s * 14, wy - 12, 3.2, trim, OUT, 1.4)
        inner += circle(0, wy + 4, 3.6, acc, OUT, 1.4)
        if V["trim"] == "#ffe36a":
            inner += rect(-sw, ts + 12, sw * 2, 8, V["accent"], None, op=0.9)
    else:  # tentacle: tunic with a star emblem
        inner += rect(-sw - 4, ts - 4, sw * 2 + 8, 56, suit, None)
        inner += path(f"M{f(-sw - 4)} {f(ts + 52)} " + "".join(f"Q{f(-sw + 6 + k * 12)} {f(ts + 60)} {f(-sw + 12 + k * 12)} {f(ts + 52)} " for k in range(5)) + f"L{f(sw + 4)} {f(ts + 40)} L{f(-sw - 4)} {f(ts + 40)} Z", suit, None)
        inner += path(f"M-10 {f(ts - 4)} Q0 {f(ts + 12)} 10 {f(ts - 4)}", skin, OUT, 1.8)
        inner += poly([(0, ts + 20), (3, ts + 28), (11, ts + 28), (5, ts + 33), (7, ts + 41), (0, ts + 36), (-7, ts + 41), (-5, ts + 33), (-11, ts + 28), (-3, ts + 28)], trim, OUT, 1.4)
        inner += line((-sw + 2, ts + 50), (sw - 2, ts + 50), trim, 2.4, 0.8)
        if V["accent"] == "#9a70ff":
            inner += circle(-sw + 5, ts + 22, 3, acc, OUT, 1.2) + circle(sw - 5, ts + 22, 3, acc, OUT, 1.2)
        inner += rect(-hw - 2, by - 14, hw * 2 + 4, 7, darken(suit, 0.35), OUT, 1.8)
    body = f'<path d="{d}" fill="{base if arch not in ("cyclops",) else lighten(suit, 0.5)}"/>'
    if arch == "tentacle":
        body = f'<path d="{d}" fill="{skin}"/>'
    if arch == "cyclops":
        body = f'<path d="{d}" fill="{mix(skin, "#ffffff", 0.25)}"/>'
    body += group(inner, 'clip-path="url(#tc)"')
    shade = f'<rect x="{f(-sw - 8)}" y="{f(ts - 6)}" width="{f(sw * 2 + 16)}" height="{f(by - ts + 12)}" fill="url(#shd)"/>'
    rim_l = f'<rect x="{f(-sw - 3)}" y="{f(ts - 6)}" width="5" height="{f(by - ts + 12)}" fill="#19d2ff" fill-opacity="0.45"/>'
    rim_r = f'<rect x="{f(sw - 2)}" y="{f(ts - 6)}" width="5" height="{f(by - ts + 12)}" fill="#ff2f9d" fill-opacity="0.35"/>'
    body += group(shade + rim_l + rim_r, 'clip-path="url(#tc)"')
    body += path(d, None, OUT, 3)
    return defs, body, (-sw - 8, ts - 10, sw + 8, by + 6)


def pelvis_part(arch, P, V):
    hy = -P["hip_y"]
    hw = P["hw"] + 1
    if arch == "blob":
        return None
    if arch == "insect":  # a rounded abdomen bulge with plates
        d = f"M{f(-hw)} {f(hy - 12)} L{f(hw)} {f(hy - 12)} Q{f(hw + 9)} {f(hy + 8)} {f(hw - 2)} {f(hy + 22)} Q0 {f(hy + 32)} {f(-hw + 2)} {f(hy + 22)} Q{f(-hw - 9)} {f(hy + 8)} {f(-hw)} {f(hy - 12)} Z"
        b = path(d, V["suit"], OUT, 3)
        for k in range(3):
            b += path(f"M{f(-hw + 1)} {f(hy - 2 + k * 9)} Q0 {f(hy + 4 + k * 9)} {f(hw - 1)} {f(hy - 2 + k * 9)}", None, darken(V["suit"], 0.4), 1.6, sop=0.8)
        b += circle(0, hy + 10, 2, V["trim"])
        return b, (-hw - 14, hy - 18, hw + 14, hy + 38)
    cloth = {"grey": V["suit"], "antenna": darken(V["suit"], 0.2), "cyclops": V["suit"], "tentacle": darken(V["suit"], 0.15)}[arch]
    d = f"M{f(-hw)} {f(hy - 12)} L{f(hw)} {f(hy - 12)} L{f(hw + 1)} {f(hy + 12)} Q0 {f(hy + 22)} {f(-hw - 1)} {f(hy + 12)} Z"
    b = path(d, cloth, OUT, 3)
    b += line((-hw + 2, hy - 8), (hw - 2, hy - 8), darken(cloth, 0.35), 3, 0.8)
    return b, (-hw - 8, hy - 18, hw + 8, hy + 30)


# ---- limbs ------------------------------------------------------------------------------------------------------------------------

def arm_spec(arch, V):
    skin, suit, trim = V["skin"], V["suit"], V["trim"]
    return {
        "grey": dict(up=suit, fore=suit, hand="fingers3", cuff=trim),
        "antenna": dict(up=None, fore=None, hand="fingers3", cuff=trim),
        "blob": dict(up=None, fore=None, hand="mitt", cuff=None),
        "insect": dict(up=None, fore=None, hand="claw", cuff=None),
        "cyclops": dict(up=lighten(suit, 0.0), fore=None, hand="fat", cuff=trim),
        "tentacle": dict(up=None, fore=None, hand="fingers3", cuff=trim),
    }[arch]


def hand_svg(kind, wr, u, aw, skin, side, accent):
    n = (-u[1], u[0])
    outs, fills = "", ""
    if kind == "fingers3":
        pc = add(wr, u, aw * 0.2)
        r = aw * 0.55
        for ang in (-34, 0, 34):
            dv = rot(u, ang)
            e = add(pc, dv, aw * 1.2)
            outs += line(pc, e, OUT, aw * 0.34 + 4.4)
            fills += line(pc, e, skin, aw * 0.34) + circle(e[0], e[1], aw * 0.2, accent, None, op=0.0)
        outs += circle(pc[0], pc[1], r + 2.4, OUT)
        fills += circle(pc[0], pc[1], r, skin)
        tips = [add(pc, rot(u, a), aw * 1.4) for a in (-34, 0, 34)]
        return outs + fills, pc, tips
    if kind == "mitt":
        pc = add(wr, u, aw * 0.45)
        th = add(pc, (n[0] * side, n[1] * side), aw * 0.7)
        outs = circle(pc[0], pc[1], aw * 0.82 + 2.6, OUT) + circle(th[0], th[1], aw * 0.34 + 2.6, OUT)
        fills = circle(th[0], th[1], aw * 0.34, skin) + circle(pc[0], pc[1], aw * 0.82, skin)
        fills += circle(pc[0] - n[0] * side * aw * 0.25, pc[1] - n[1] * side * aw * 0.25, aw * 0.28, "#ffffff", None, op=0.4)
        return outs + fills, pc, [add(pc, u, aw * 1.0)]
    if kind == "claw":
        pc = add(wr, u, aw * 0.25)
        for sgn in (-1, 1):
            d_ = rot(u, sgn * 18)
            tip = add(pc, rot(u, sgn * 5), aw * 2.4)
            p1 = add(pc, (n[0] * sgn, n[1] * sgn), aw * 0.55)
            p2 = add(pc, (n[0] * sgn, n[1] * sgn), -aw * 0.1)
            mid = add(add(pc, rot(u, sgn * 24), aw * 1.5), (n[0] * sgn, n[1] * sgn), aw * 0.35)
            dd = f"M{f(p1[0])} {f(p1[1])} Q{f(mid[0])} {f(mid[1])} {f(tip[0])} {f(tip[1])} Q{f(p2[0] + u[0] * aw)} {f(p2[1] + u[1] * aw)} {f(p2[0])} {f(p2[1])} Z"
            outs += path(dd, skin, OUT, 2.4)
        outs += circle(pc[0], pc[1], aw * 0.62, skin, OUT, 2.4)
        return outs, pc, [add(pc, u, aw * 2.4)]
    pc = add(wr, u, aw * 0.3)  # fat: three short thick fingers
    for ang in (-38, 0, 38):
        dv = rot(u, ang)
        e = add(pc, dv, aw * 0.8)
        outs += line(pc, e, OUT, aw * 0.5 + 4.4)
        fills += line(pc, e, skin, aw * 0.5)
    outs += circle(pc[0], pc[1], aw * 0.62 + 2.4, OUT)
    fills += circle(pc[0], pc[1], aw * 0.62, skin)
    return outs + fills, pc, [add(pc, u, aw * 1.3)]


def arm_parts(arch, P, V, J, side):
    from .chars import wrist
    name = "l" if side < 0 else "r"
    s, e, w = J["shoulder_" + name], J["elbow_" + name], wrist(P, J, side)
    aw = P["aw"]
    skin = V["skin"]
    spec = arm_spec(arch, V)
    out = {}
    c = spec["up"] or skin
    dx, dy = e[0] - s[0], e[1] - s[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    body = line(s, e, OUT, aw + 6, cap="butt") + circle(s[0], s[1], aw / 2 + 3, OUT) + line(s, e, c, aw, cap="round")
    for off, col, w_, op in ((aw * 0.24 * side, darken(c, 0.25), aw * 0.4, 0.7), (-aw * 0.26 * side, lighten(c, 0.3), aw * 0.14, 0.65)):
        body += line((s[0] + nx * off, s[1] + ny * off), (e[0] + nx * off, e[1] + ny * off), col, w_, op)
    if arch == "blob":
        body += line((s[0] - nx * aw * 0.2 * side, s[1] - ny * aw * 0.2 * side), (e[0] - nx * aw * 0.2 * side, e[1] - ny * aw * 0.2 * side), "#ffffff", 2.4, 0.35)
    if arch == "cyclops":  # puffy shoulder strap tip
        body += circle(s[0], s[1], aw / 2 + 0.5, V["suit"])
    if arch == "grey":  # a rounded shoulder pad with a glowing trim stripe
        pr_ = aw * 0.92
        body += circle(s[0], s[1] + 1, pr_, lighten(V["suit"], 0.25), OUT, 2.6)
        body += path(f"M{f(s[0] - pr_ * 0.75)} {f(s[1] + pr_ * 0.45)} Q{f(s[0])} {f(s[1] + pr_ * 1.05)} {f(s[0] + pr_ * 0.75)} {f(s[1] + pr_ * 0.45)}", None, V["trim"], 2.2)
        body += circle(s[0] - pr_ * 0.3, s[1] - pr_ * 0.3, pr_ * 0.28, "#ffffff", None, op=0.6)
    out["up"] = (body, bbox([s, e], aw / 2 + 8))
    fc = spec["fore"] or skin
    body = circle(e[0], e[1], aw / 2 + 3, OUT)
    body += line(e, w, OUT, aw + 6, cap="butt") + circle(w[0], w[1], aw / 2 + 3, OUT)
    body += line(e, w, fc, aw, cap="round")
    dx, dy = w[0] - e[0], w[1] - e[1]
    ln = math.hypot(dx, dy)
    nx, ny = -dy / ln, dx / ln
    u = (dx / ln, dy / ln)
    for off, col, w_, op in ((aw * 0.24 * side, darken(fc, 0.25), aw * 0.4, 0.7), (-aw * 0.26 * side, lighten(fc, 0.3), aw * 0.14, 0.65)):
        body += line((e[0] + nx * off, e[1] + ny * off), (w[0] + nx * off, w[1] + ny * off), col, w_, op)
    if arch == "blob":
        body += line((e[0], e[1]), (w[0], w[1]), "#ffffff", 2.2, 0.3)
    if arch == "insect":  # blade serrations along the inside of the forearm and a knobbly elbow
        for k in range(1, 5):
            m = (e[0] + dx * k / 5.2, e[1] + dy * k / 5.2)
            a_ = (m[0] - nx * side * (aw / 2 + 0.5), m[1] - ny * side * (aw / 2 + 0.5))
            b_ = (m[0] - nx * side * (aw / 2 + 5.5) + u[0] * 4, m[1] - ny * side * (aw / 2 + 5.5) + u[1] * 4)
            c_ = (m[0] + u[0] * 5.5 - nx * side * (aw / 2 + 0.5), m[1] + u[1] * 5.5 - ny * side * (aw / 2 + 0.5))
            body += poly([a_, b_, c_], V["trim"], OUT, 1.6)
        body += circle(e[0], e[1], aw / 2 + 1.5, V["suit"], OUT, 2)
    if spec["cuff"]:
        cuff = add(w, u, -3)
        body += line(add(cuff, (nx, ny), -(aw / 2 + 2)), add(cuff, (nx, ny), aw / 2 + 2), spec["cuff"], 5, cap="butt")
        body += line(add(cuff, (nx, ny), -(aw / 2 + 2.5)), add(cuff, (nx, ny), -(aw / 2 + 2.5)), OUT, 0)
    hs, hc, tips = hand_svg(spec["hand"], w, u, aw, skin, side, V["accent"])
    body += hs
    out["fore"] = (body, bbox([e, w, hc] + tips, aw / 2 + 12), hc)
    return out


def leg_part(arch, P, V, J, side):
    name = "l" if side < 0 else "r"
    h = J["hip_" + name]
    sh = P["shoe_h"]
    ax, ay = h[0] + side * 2.0, -sh - 2
    lw = P["lw"]
    skin, suit, trim, acc = V["skin"], V["suit"], V["trim"], V["accent"]
    body = ""
    pts_ = [h, (ax, ay)]
    fx = ax + side * 4
    if arch == "grey":
        body += capsule(h, (ax, ay), lw, suit, darken(suit, 0.3), lighten(suit, 0.3))
        body += line((h[0] + side * lw * 0.3, h[1] + 8), (ax + side * lw * 0.3, ay), trim, 2.2, 0.9)
        body += _boot(ax, fx, side, 12, "#3a3f78", trim, 11)
        pts_ += [(fx + side * 16, 0), (ax - 14, 0)]
    elif arch == "antenna":
        body += capsule(h, (ax, ay), lw, skin, darken(skin, 0.25), lighten(skin, 0.35))
        body += line((ax - lw / 2 - 1, ay - 24), (ax + lw / 2 + 1, ay - 24), trim, 2.6, cap="butt")
        body += _boot(ax, fx, side, 12, darken(V["suit"], 0.1), trim, 13)
        pts_ += [(fx + side * 16, 0), (ax - 14, 0)]
    elif arch == "blob":  # short stubby jelly legs ending in round feet
        body += capsule(h, (ax, ay - 2), lw, V["skin"], darken(V["skin"], 0.25), lighten(V["skin"], 0.4))
        body += ellipse(fx, -6, 15, 8, V["skin"], OUT, 3) + ellipse(fx - 2, -8, 8, 2.8, "#ffffff", None, op=0.5)
        pts_ += [(fx + side * 16, 0), (ax - 16, 0)]
    elif arch == "insect":  # thin, long leg with a knee spur and a pointed foot
        km = (h[0] + (ax - h[0]) * 0.52 + side * 5, h[1] + (ay - h[1]) * 0.52)
        body += line(h, km, OUT, lw + 5, cap="round") + line(km, (ax, ay), OUT, lw + 5, cap="round")
        body += line(h, km, V["suit"], lw, cap="round") + line(km, (ax, ay), V["skin"], lw - 1.5, cap="round")
        body += poly([(km[0] + side * 3, km[1] - 6), (km[0] + side * 12, km[1] + 2), (km[0] + side * 3, km[1] + 6)], trim, OUT, 1.6)
        body += path(f"M{f(ax - 6)} -2 Q{f(ax - 6)} -10 {f(ax)} -10 Q{f(fx + side * 10)} -9 {f(fx + side * 16)} -1 L{f(ax - 6)} 0 Z", V["suit"], OUT, 3)
        body += line((ax - 5, -2), (fx + side * 14, -2), trim, 2.4, cap="butt")
        pts_ += [(fx + side * 18, 0), (ax - 8, 0), km]
    elif arch == "cyclops":
        body += capsule(h, (ax, ay), lw, suit, darken(suit, 0.3), lighten(suit, 0.3))
        body += line((ax - lw / 2 - 1.5, ay - 14), (ax + lw / 2 + 1.5, ay - 14), trim, 3, cap="butt")
        body += path(f"M{f(ax - 15)} -3 Q{f(ax - 18)} -18 {f(ax)} -18 Q{f(fx + side * 20)} -18 {f(fx + side * 22)} -5 Q{f(fx + side * 22)} 1 {f(fx + side * 12)} 1 L{f(ax - 12)} 1 Q{f(ax - 17)} 0 {f(ax - 15)} -3 Z", skin, OUT, 3)
        body += line((ax - 14, -3), (fx + side * 21, -3), darken(skin, 0.3), 3.4, cap="butt")
        body += line((ax - 5, -13), (ax + 6, -13), "#ffffff", 2, 0.45)
        pts_ += [(fx + side * 24, 0), (ax - 18, 0)]
    else:  # tentacle: slim legs, flipper feet
        body += capsule(h, (ax, ay), lw, V["skin"], darken(V["skin"], 0.25), lighten(V["skin"], 0.35))
        body += line((ax - lw / 2 - 1, ay - 18), (ax + lw / 2 + 1, ay - 18), trim, 2.6, cap="butt")
        body += path(f"M{f(ax - 7)} -4 Q{f(ax - 7)} -12 {f(ax)} -12 Q{f(ax + 7)} -12 {f(ax + 7)} -4 Q{f(fx + side * 22)} -6 {f(fx + side * 24)} 1 L{f(ax - 12)} 1 Z", mix(V["skin"], V["accent"], 0.5), OUT, 3)
        for k in range(3):
            body += line((ax + side * (6 + k * 5), -3), (ax + side * (12 + k * 5), -0.5), OUT, 1.2, 0.7)
        pts_ += [(fx + side * 26, 0), (ax - 14, 0)]
    return body, bbox(pts_, lw / 2 + 12)


def _boot(ax, fx, side, rx_, col, trim, top):
    b = path(f"M{f(ax - rx_ + 2)} -4 Q{f(ax - rx_)} {f(-top)} {f(ax)} {f(-top)} Q{f(fx + side * rx_)} {f(-top)} {f(fx + side * (rx_ + 3))} -4 Q{f(fx + side * (rx_ + 3))} 1 {f(fx + side * (rx_ - 2))} 1 L{f(ax - rx_ + 4)} 1 Q{f(ax - rx_ - 1)} 0 {f(ax - rx_ + 2)} -4 Z", col, OUT, 3)
    b += line((ax - rx_ + 3, -1.5), (fx + side * (rx_ + 2), -1.5), trim, 3, cap="butt")
    b += line((ax - 4, -top + 2), (ax + 5, -top + 2), "#ffffff", 1.6, 0.5)
    return b


# ---- assembly --------------------------------------------------------------------------------------------------------------------------

def build_variant(arch, variant):
    P = ARCH[arch]
    V = VARIANTS[arch][variant]
    J = skeleton(P)
    base = f"{BASE}{arch}_{variant}/"
    parts = []

    def emit(name, joint, z, body, box, defs="", swing=False, pivot_xy=None):
        info = write_svg(base + name + ".svg", box, body, defs)
        pv = pivot_in(info, J[joint])
        e = {"name": name, "joint": joint, "z": z, "file": f"source/{base}{name}.svg", "pivot": pv, "px_scale": 0.5}
        if swing:
            e["swing"] = True
            e["swing_pivot"] = pivot_in(info, pivot_xy) if pivot_xy else pv
        parts.append(e)

    if arch == "tentacle":
        body, box, pv = tentacle_hair(P, V)
        emit("hair_back", "head", -20, body, box, swing=True, pivot_xy=pv)
    if arch == "insect":
        body, box, pv = wing_cases(P, V)
        emit("hair_back", "torso", -20, body, box, swing=True, pivot_xy=pv)
    for side in (-1, 1):
        n = "l" if side < 0 else "r"
        body, box = leg_part(arch, P, V, J, side)
        emit(f"leg_{n}", f"hip_{n}", -10, body, box)
    pel = pelvis_part(arch, P, V)
    if pel:
        emit("pelvis", "hips", -5, pel[0], pel[1])
    defs, body, box = torso_part(arch, P, V)
    emit("torso", "torso", 0, body, box, defs)
    arms = {}
    for side in (-1, 1):
        n = "l" if side < 0 else "r"
        a = arm_parts(arch, P, V, J, side)
        arms[n] = a
        emit(f"arm_{n}_up", f"shoulder_{n}", 5, a["up"][0], a["up"][1])
        emit(f"arm_{n}_fore", f"elbow_{n}", 4, a["fore"][0], a["fore"][1])
    defs, body, box = head_part(arch, P, V)
    emit("head", "head", 10, body, box, defs)
    faces = {}
    for ex in EXPRESSIONS:
        body, box = face_overlay(arch, P, V, ex)
        info = write_svg(f"{base}face_{ex}.svg", box, body)
        faces[ex] = {"file": f"source/{base}face_{ex}.svg", "pivot": pivot_in(info, J["head"]), "px_scale": 0.5}
    if arch == "antenna":
        body, box, pv = antennae(P, V)
        emit("hair_front", "head", 20, body, box, swing=True, pivot_xy=pv)
    if arch == "tentacle":
        body, box = tentacle_front(P, V)
        emit("hair_front", "head", 20, body, box, swing=True, pivot_xy=(0, P["cy"] - P["ry"] * 0.3))
    if arch == "insect":
        body, box, pv = feelers(P, V)
        emit("hair_front", "head", 20, body, box, swing=True, pivot_xy=pv)

    def hand_px(side):
        n = "l" if side < 0 else "r"
        hand = arms[n]["fore"][2]
        fb = arms[n]["fore"][1]
        return [round((hand[0] - math.floor(fb[0])) * 2, 1), round((hand[1] - math.floor(fb[1])) * 2, 1)]

    return {"parts": parts, "faces": faces, "face_z": 12,
            "glow_hand": {"joint": "elbow_r", "at": hand_px(1), "joint_l": "elbow_l", "at_l": hand_px(-1)}}


def build_all():
    archetypes = {}
    tops = {"grey": 0, "antenna": 56, "blob": 0, "insect": 8, "cyclops": 12, "tentacle": 0}
    for arch, P in ARCH.items():
        J = skeleton(P)
        entry = {"height": int(-(P["cy"] - P["ry"] * 1.3) + tops[arch]),
                 "joints": {k: [round(v[0], 1), round(v[1], 1)] for k, v in J.items()}, "variants": {}}
        for variant in VARIANTS[arch]:
            v = build_variant(arch, variant)
            entry["variants"][variant] = {k: v[k] for k in ("parts", "faces", "face_z", "glow_hand")}
        archetypes[arch] = entry
    return archetypes
