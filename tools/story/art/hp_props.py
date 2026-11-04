"""Shared drawing toolkit of the `hospital` chapter: the one-point-perspective `Room`, floors (planks, tiles, paving), plants, bunting,
balloons, windows and the warm daylight palette. Used by hp_stage.py (the private room) and hp_views*.py (corridor, cafeteria, garden).
All shapes are SVG strings in design px (the 1280 x 720 stage); see lib.py for the writers.
"""
from __future__ import annotations

import math
import random

from .lib import (OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, poly, rad_grad, rect)

W, H = 1280, 720

CREAM, PEACH, SAND = "#fff3e0", "#f7dcc0", "#ecc79c"
TEAL, TEAL_D, TEAL_L = "#4fb3a9", "#2f857f", "#9fdcd2"
CORAL, ROSE, GOLD, SUN = "#ff8f7a", "#f4a5b4", "#ffc65a", "#ffe9a8"
SAGE, LEAF, LEAF_D = "#b9d9a3", "#6fbf6a", "#3f8f52"
WOOD, WOOD_L, WOOD_D = "#c98f55", "#e2b47c", "#8a5a30"
SKY, SKY_L = "#a8dcf0", "#e6f6fb"
LILAC, MINT = "#c9b6ec", "#bfe8d4"
WARM_SHADOW = "#5a2f3a"
PAPER = ["#ff8f7a", "#ffc65a", "#7fd1c4", "#9ab8f0", "#f4a5b4", "#b9d9a3", "#c9b6ec"]


class Room:
    """One-point perspective box: vanishing point (vx, vy), far wall rectangle fx0..fx1 x fy0..fy1 (symmetric about vx)."""

    def __init__(self, vx, vy, fx0, fx1, fy0, fy1):
        self.vx, self.vy, self.fx0, self.fx1, self.fy0, self.fy1 = vx, vy, fx0, fx1, fy0, fy1
        self.half = vx - fx0

    def scale(self, y):
        return (y - self.vy) / (self.fy1 - self.vy)

    def floor_x(self, xfar, y):
        return self.vx + (xfar - self.vx) * self.scale(y)

    def floor_y(self, s):
        return self.vy + (self.fy1 - self.vy) * s

    def lwall(self, x, yf):
        """screen y of the point at far-wall height yf on the left wall plane, at screen x (x <= fx0)"""
        return self.vy + (yf - self.vy) * (self.vx - x) / (self.vx - self.fx0)

    def rwall(self, x, yf):
        return self.vy + (yf - self.vy) * (x - self.vx) / (self.fx1 - self.vx)

    def wall_poly(self, side, x0, x1, yf0, yf1):
        fn = self.lwall if side < 0 else self.rwall
        return [(x0, fn(x0, yf0)), (x1, fn(x1, yf0)), (x1, fn(x1, yf1)), (x0, fn(x0, yf1))]

    def ceil_pt(self, xfar, s):
        return (self.vx + (xfar - self.vx) * s, self.vy - (self.vy - self.fy0) * s)

    def rows(self, front_y=438, ys=(286, 316, 350, 390, 438)):
        return [{"y": y, "scale": round(self.scale(y) / self.scale(front_y), 3)} for y in ys]

    def grid(self, nfar=9):
        step = (self.fx1 - self.fx0) / (nfar - 1)
        return {"vanishing_point": [self.vx, self.vy], "far_y": self.fy1, "far_x": [round(self.fx0 + step * i, 1) for i in range(nfar)],
                "note": "x on the far wall base line; a floor line through far_x at screen row y is at x = vp_x + (far_x - vp_x) * (y - vp_y) / (far_y - vp_y)"}

    def floor_poly(self):
        yl = self.lwall(0, self.fy1)
        yr = self.rwall(W, self.fy1)
        return [(self.fx0, self.fy1), (self.fx1, self.fy1), (W, yr), (W, H), (0, H), (0, yl)]

    def floor_screen_poly(self, y_far=None, y_near=520):
        y_far = self.fy1 if y_far is None else y_far
        return [[self.fx0, y_far], [self.fx1, y_far], [round(self.floor_x(self.fx1, y_near)), y_near], [round(self.floor_x(self.fx0, y_near)), y_near]]

    def depth_lines(self, zstep=0.065):
        ys, z = [], 1.0
        while True:
            y = self.vy + (self.fy1 - self.vy) / z
            if y > H + 40:
                return ys
            ys.append(y)
            z -= zstep


def piece(pid, file, pos, size, anim, z="behind", blend="mix", pivot=None, px=0.5):
    d = {"id": pid, "file": file, "pos": [round(pos[0], 1), round(pos[1], 1)], "size": [size[0], size[1]], "px_scale": px}
    if pivot is not None:
        d["pivot"] = [round(pivot[0], 1), round(pivot[1], 1)]
    d.update({"anim": anim, "z": z, "blend": blend})
    return d


def layer(lid, file, pos, size, z=None):
    d = {"id": lid, "file": file, "pos": list(pos), "size": list(size), "px_scale": 0.5}
    if z:
        d["z"] = z
    return d


OV = 150  # design px every room layer reaches beyond each side of the 1280 frame (a camera look or the walker's sway never shows the void)


def overscan(rel_path, ov=OV):
    """Widen a room layer that was written with the viewBox (0, y0, 1280, h) by `ov` design px on both sides. The strips beyond the frame
    are filled with mirror images of the frame's edges (the room's own drawing goes on top, so anything drawn wider than the frame wins).
    The body is defined once and placed three times with <use>, so the file barely grows. Returns the layer's new (pos_x, width)."""
    import os
    import re
    from . import lib
    full = os.path.join(lib.SVG_DIR, rel_path)
    with open(full, encoding="utf-8") as fh:
        svg = fh.read()
    m = re.match(r'<svg xmlns="http://www.w3.org/2000/svg" width="(\d+)" height="(\d+)" viewBox="(-?\d+) (-?\d+) (\d+) (\d+)">(.*)</svg>\n$', svg, re.S)
    if not m:
        raise ValueError("unexpected svg header in " + rel_path)
    x0, y0, w, h = (int(m.group(k)) for k in (3, 4, 5, 6))
    inner = m.group(7)
    defs, body = "", inner
    if inner.startswith("<defs>"):
        end = inner.index("</defs>")
        defs, body = inner[6:end], inner[end + 7:]
    nw = w + 2 * ov
    defs += f'<clipPath id="ovL"><rect x="{x0 - ov}" y="{y0 - 10}" width="{ov}" height="{h + 20}"/></clipPath>'
    defs += f'<clipPath id="ovR"><rect x="{x0 + w}" y="{y0 - 10}" width="{ov}" height="{h + 20}"/></clipPath>'
    defs += f'<g id="ovroom">{body}</g>'
    out = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{nw * lib.SCALE}" height="{h * lib.SCALE}" '
           f'viewBox="{x0 - ov} {y0} {nw} {h}"><defs>{defs}</defs>'
           f'<g clip-path="url(#ovL)"><use xlink:href="#ovroom" transform="matrix(-1 0 0 1 {2 * x0} 0)"/></g>'
           f'<g clip-path="url(#ovR)"><use xlink:href="#ovroom" transform="matrix(-1 0 0 1 {2 * (x0 + w)} 0)"/></g>'
           f'<use xlink:href="#ovroom"/></svg>\n')
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    return x0 - ov, nw


def room_layer(lid, rel_svg, h=720, z=None):
    """The manifest entry of a full-width room layer already written to source/<rel_svg>, widened by overscan()."""
    x, w = overscan(rel_svg)
    return layer(lid, "source/" + rel_svg, (x, 0), (w, h), z)


# ---- light and glow ----------------------------------------------------------------------------------------------------------

def soft_glow(cx, cy, rx, ry, color, strength=0.5, steps=7):
    """A soft radial light made of stacked translucent ellipses (no blur filters in ThorVG)."""
    out = ""
    for k in range(steps):
        t = (k + 1) / steps
        out += ellipse(cx, cy, rx * (1.0 - t * 0.85), ry * (1.0 - t * 0.85), color, None, op=strength / steps * 1.6)
    return out


def glow_defs(gid, color, a0=0.55):
    return rad_grad(gid, [(0, color, a0), (0.5, color, a0 * 0.35), (1, color, 0.0)], 0.5, 0.5, 0.5)


def light_ray(poly_pts, gid):
    return poly(poly_pts, f"url(#{gid})")


def grade(room: Room, uid: str, floor=0.34, ceil=0.26, sides=0.3, shadow=WARM_SHADOW, ceil_y=None):
    """Light a room like a painter, drawn last over its backdrop: the near floor and the ceiling fall into a warm shadow and the side
    edges darken, so the middle distance where the family dances carries the brightest values, the dancers' bright clothes read against a
    mid-tone floor, and the runtime's additive party lights glow on the set instead of bleaching it. Returns (defs, body)."""
    ceil_y = room.fy0 if ceil_y is None else ceil_y
    defs = lin_grad(uid + "f", [(0, shadow, 0.0), (0.3, shadow, floor * 0.2), (0.7, shadow, floor * 0.7), (1, shadow, floor)], 0, 0, 0, 1)
    defs += lin_grad(uid + "c", [(0, shadow, ceil), (1, shadow, 0.0)], 0, 0, 0, 1)
    defs += lin_grad(uid + "l", [(0, shadow, sides), (1, shadow, 0.0)], 0, 0, 1, 0)
    defs += lin_grad(uid + "r", [(0, shadow, 0.0), (1, shadow, sides)], 0, 0, 1, 0)
    body = rect(-10, room.fy1, W + 20, 480 - room.fy1, f"url(#{uid}f)") + rect(-10, 480, W + 20, H - 470, shadow, None, op=floor)
    body += rect(-10, -10, W + 20, ceil_y + 10, f"url(#{uid}c)")
    body += rect(-10, -10, 230, H + 20, f"url(#{uid}l)") + rect(W - 220, -10, 230, H + 20, f"url(#{uid}r)")
    return defs, body


# ---- floors ----------------------------------------------------------------------------------------------------------------------

def plank_floor(room: Room, uid: str, base="#dcab6c", tones=("#d29a58", "#dca868", "#c98f4e", "#e0b070"), gap="#7a4a22", plank=34, seed=3, gloss=0.16):
    """A wooden floor in perspective: planks along the depth, staggered butt joints, a soft gloss. Returns (defs, body)."""
    rng = random.Random(seed)
    poly_pts = room.floor_poly()
    defs = clip(uid, poly(poly_pts, "#000"))
    defs += lin_grad(uid + "g", [(0, "#ffffff", gloss * 0.8), (0.45, "#ffffff", gloss * 0.2), (1, "#3a1f2e", 0.18)], 0, 0, 0, 1)
    body = poly(poly_pts, base)
    inner = ""
    xf = room.fx0 - plank * 40
    i = 0
    ys = room.depth_lines(0.05)
    while xf < room.fx1 + plank * 40:
        x2 = xf + plank
        quad = [(xf, room.fy1), (x2, room.fy1), (room.floor_x(x2, H + 10), H + 10), (room.floor_x(xf, H + 10), H + 10)]
        inner += poly(quad, tones[rng.randrange(len(tones))], None)
        off = rng.random()
        for k in range(len(ys) - 1):
            if (k + int(off * 3)) % 3 == 0:  # a butt joint in this plank
                y = ys[k]
                inner += line((room.floor_x(xf, y), y), (room.floor_x(x2, y), y), gap, 1.0 + 0.5 * room.scale(y), 0.7)
        inner += line((xf, room.fy1), (room.floor_x(xf, H + 10), H + 10), gap, 1.4, 0.62)
        xf = x2
        i += 1
    body += group(inner, f'clip-path="url(#{uid})"')
    body += group(poly(poly_pts, f"url(#{uid}g)"), "")
    return defs, body


def tile_floor(room: Room, uid: str, c1="#fff0d8", c2="#f2c9a0", cell=48, line_c="#d9a97a", gloss=0.2):
    """A checkerboard of floor tiles in perspective (equal squares in depth), clipped to the room's floor."""
    poly_pts = room.floor_poly()
    defs = clip(uid, poly(poly_pts, "#000"))
    defs += lin_grad(uid + "g", [(0, "#ffffff", gloss), (0.5, "#ffffff", gloss * 0.2), (1, "#3a1f2e", 0.16)], 0, 0, 0, 1)
    body = poly(poly_pts, c1)
    inner = ""
    ys = []
    z = 1.0
    while True:  # depth lines at equal steps in z
        y = room.vy + (room.fy1 - room.vy) / z
        if y > H + 40:
            break
        ys.append((y, z))
        z -= cell / 520.0
    nx = int((W * 2) / cell)
    for k in range(len(ys) - 1):
        y0, y1 = ys[k][0], ys[k + 1][0]
        for i in range(-nx, nx):
            if (i + k) % 2 == 0:
                continue
            xa, xb = room.fx0 + (i * cell), room.fx0 + ((i + 1) * cell)
            inner += poly([(room.floor_x(xa, y0), y0), (room.floor_x(xb, y0), y0), (room.floor_x(xb, y1), y1), (room.floor_x(xa, y1), y1)], c2, None)
    for k in range(len(ys)):
        y = ys[k][0]
        inner += line((-200, y), (W + 200, y), line_c, 1.0 + 0.5 * room.scale(y), 0.45)
    for i in range(-nx, nx):
        x = room.fx0 + i * cell
        inner += line((x, room.fy1), (room.floor_x(x, H + 10), H + 10), line_c, 1.2, 0.45)
    body += group(inner, f'clip-path="url(#{uid})"')
    body += poly(poly_pts, f"url(#{uid}g)")
    return defs, body


def paving(room: Room, uid: str, stone="#e8cfa6", stone2="#d9b98a", grout="#a98558", cell=44, seed=5, grass=None, path_w=None):
    """Stone paving slabs in perspective (staggered courses), clipped to the room floor."""
    rng = random.Random(seed)
    poly_pts = room.floor_poly()
    defs = clip(uid, poly(poly_pts, "#000"))
    defs += lin_grad(uid + "g", [(0, "#ffffff", 0.18), (0.5, "#ffffff", 0.04), (1, "#3a2410", 0.18)], 0, 0, 0, 1)
    body = poly(poly_pts, stone)
    inner = ""
    ys, z = [], 1.0
    while True:
        y = room.vy + (room.fy1 - room.vy) / z
        if y > H + 40:
            break
        ys.append(y)
        z -= cell / 560.0
    nx = int(W * 2 / (cell * 1.7))
    for k in range(len(ys) - 1):
        y0, y1 = ys[k], ys[k + 1]
        for i in range(-nx, nx):
            w = cell * 1.7
            xa = room.fx0 + i * w + (w / 2 if k % 2 else 0)
            xb = xa + w
            col = stone if rng.random() < 0.55 else (stone2 if rng.random() < 0.7 else lighten(stone, 0.18))
            inner += poly([(room.floor_x(xa, y0), y0), (room.floor_x(xb, y0), y0), (room.floor_x(xb, y1), y1), (room.floor_x(xa, y1), y1)], col, grout, 0.9 + 0.5 * room.scale(y0))
    body += group(inner, f'clip-path="url(#{uid})"')
    body += poly(poly_pts, f"url(#{uid}g)")
    return defs, body


def oval_rug(cx, cy, rx, ry, bands, uid, fringe=True, pattern=None):
    """A woven oval rug lying on the floor: concentric bands (colour, relative radius), fringe at both ends."""
    out = ""
    out += ellipse(cx + 3, cy + 6, rx + 8, ry + 6, "#3a1f2e", None, op=0.18)
    for col, k in bands:
        out += ellipse(cx, cy, rx * k, ry * k, col, OUT if k == 1.0 else None, 2.4 if k == 1.0 else 0)
    if fringe:
        for a in range(-9, 10):
            t = a / 9.0
            x = cx + rx * math.cos(math.pi * (0.5 + t * 0.12)) * 1.0
        for sgn in (-1, 1):
            for a in range(-6, 7):
                yy = cy + a * ry / 7.5
                xx = cx + sgn * rx * math.sqrt(max(0.0, 1 - ((yy - cy) / ry) ** 2))
                out += line((xx, yy), (xx + sgn * 9, yy + 1.2), "#fff3e0", 1.8, 0.95)
    return out


# ---- plants and nature --------------------------------------------------------------------------------------------------------------

def leaf(cx, cy, ang_deg, ln, w, color, vein=True, ol=1.8):
    a = math.radians(ang_deg)
    tip = (cx + math.cos(a) * ln, cy + math.sin(a) * ln)
    nx, ny = -math.sin(a), math.cos(a)
    m1 = (cx + math.cos(a) * ln * 0.5 + nx * w, cy + math.sin(a) * ln * 0.5 + ny * w)
    m2 = (cx + math.cos(a) * ln * 0.5 - nx * w, cy + math.sin(a) * ln * 0.5 - ny * w)
    d = f"M{f(cx)} {f(cy)} Q{f(m1[0])} {f(m1[1])} {f(tip[0])} {f(tip[1])} Q{f(m2[0])} {f(m2[1])} {f(cx)} {f(cy)} Z"
    o = path(d, color, OUT, ol)
    if vein:
        o += line((cx, cy), (cx + math.cos(a) * ln * 0.86, cy + math.sin(a) * ln * 0.86), lighten(color, 0.35), 1.0, 0.8)
    return o


def pot(cx, by, w, h, color="#d9734a", rim=True):
    o = poly([(cx - w * 0.5, by - h), (cx + w * 0.5, by - h), (cx + w * 0.38, by), (cx - w * 0.38, by)], color, OUT, 2.2)
    if rim:
        o += rect(cx - w * 0.56, by - h - 5, w * 1.12, 8, lighten(color, 0.12), OUT, 2, rx=2)
    o += line((cx - w * 0.3, by - h + 5), (cx - w * 0.22, by - 3), "#ffffff", 1.6, 0.35)
    return o


def plant(cx, by, h, kind="fern", pot_color="#d9734a", seed=1, spread=1.0):
    rng = random.Random(seed)
    o = ""
    w = h * 0.34
    top = by - h * 0.34
    if kind == "fern":
        for k in range(11):
            a = -90 + (k - 5) * 17 + rng.uniform(-4, 4)
            o += leaf(cx, top, a, h * rng.uniform(0.55, 0.78) * spread, h * 0.1, [LEAF, LEAF_D, "#8fd08a"][k % 3])
    elif kind == "palm":
        for k in range(9):
            a = -90 + (k - 4) * 22 + rng.uniform(-4, 4)
            o += leaf(cx, top, a, h * rng.uniform(0.55, 0.72) * spread, h * 0.07, [LEAF, "#4fa860", "#7ccf78"][k % 3])
    else:  # bushy
        for k in range(9):
            o += circle(cx + rng.uniform(-w * 0.9, w * 0.9) * spread, top - rng.uniform(0, h * 0.4), rng.uniform(h * 0.1, h * 0.17), [LEAF, "#58a85c", "#86cf80"][k % 3], OUT, 2)
    o += pot(cx, by, w, h * 0.34, pot_color)
    return o


def flower(cx, cy, r, petal, center="#ffd23f", n=6, ol=1.4):
    o = ""
    for k in range(n):
        a = k * math.tau / n
        o += circle(cx + math.cos(a) * r * 0.7, cy + math.sin(a) * r * 0.7, r * 0.55, petal, OUT, ol)
    o += circle(cx, cy, r * 0.5, center, OUT, ol)
    return o


def tulip(cx, cy, s, color, ol=1.6):
    o = path(f"M{f(cx - s)} {f(cy)} Q{f(cx - s * 1.1)} {f(cy - s * 1.6)} {f(cx - s * 0.5)} {f(cy - s * 2.0)} L{f(cx)} {f(cy - s * 1.2)} L{f(cx + s * 0.5)} {f(cy - s * 2.0)} "
             f"Q{f(cx + s * 1.1)} {f(cy - s * 1.6)} {f(cx + s)} {f(cy)} Q{f(cx)} {f(cy + s * 0.5)} {f(cx - s)} {f(cy)} Z", color, OUT, ol)
    o += path(f"M{f(cx - s * 0.5)} {f(cy - s * 1.5)} Q{f(cx - s * 0.3)} {f(cy - s * 0.4)} {f(cx - s * 0.2)} {f(cy)}", None, lighten(color, 0.5), 1.0, 0.8)
    return o


def bouquet(cx, by, s=1.0, seed=2, vase="#9fdcd2"):
    """Flowers in a glass-blue vase, sitting on y = by."""
    rng = random.Random(seed)
    o = ""
    pal = ["#ff8f7a", "#ffd23f", "#f4a5b4", "#fff3e0", "#c9b6ec", "#ff6f8f"]
    for k in range(7):
        a = -90 + (k - 3) * 15 + rng.uniform(-4, 4)
        ln = rng.uniform(46, 62) * s
        bx, by_ = cx, by - 22 * s
        tx, ty = bx + math.cos(math.radians(a)) * ln, by_ + math.sin(math.radians(a)) * ln
        o += line((bx, by_), (tx, ty), LEAF_D, 2.6) + line((bx, by_), (tx, ty), LEAF, 1.2)
        if k % 2 == 0:
            o += leaf(bx + (tx - bx) * 0.45, by_ + (ty - by_) * 0.45, a + 50, 16 * s, 4 * s, LEAF, False, 1.2)
        o += flower(tx, ty, rng.uniform(7, 10) * s, pal[k % len(pal)], n=5 + k % 3)
    o += path(f"M{f(cx - 11 * s)} {f(by - 36 * s)} L{f(cx + 11 * s)} {f(by - 36 * s)} Q{f(cx + 17 * s)} {f(by - 10 * s)} {f(cx + 12 * s)} {f(by)} L{f(cx - 12 * s)} {f(by)} Q{f(cx - 17 * s)} {f(by - 10 * s)} {f(cx - 11 * s)} {f(by - 36 * s)} Z", vase, OUT, 2.2, op=0.9)
    o += path(f"M{f(cx - 8 * s)} {f(by - 28 * s)} Q{f(cx - 11 * s)} {f(by - 12 * s)} {f(cx - 8 * s)} {f(by - 4)}", None, "#ffffff", 1.8, 0.7)
    o += line((cx - 11 * s, by - 20 * s), (cx + 12 * s, by - 20 * s), lighten(vase, 0.5), 1.2, 0.6)
    return o


# ---- party things -----------------------------------------------------------------------------------------------------------------------

def balloon(cx, cy, r, color, string_to=None, shine=True, ol=2.4):
    o = ""
    if string_to:
        mx, my = (cx + string_to[0]) / 2 + 6, (cy + r + string_to[1]) / 2
        o += path(f"M{f(cx)} {f(cy + r * 1.2)} Q{f(mx)} {f(my)} {f(string_to[0])} {f(string_to[1])}", None, "#fff3e0", 1.5, sop=0.95)
    o += path(f"M{f(cx)} {f(cy + r * 1.18)} L{f(cx - 3.4)} {f(cy + r * 1.18 + 5)} L{f(cx + 3.4)} {f(cy + r * 1.18 + 5)} Z", darken(color, 0.15), OUT, 1.4)
    o += path(f"M{f(cx)} {f(cy - r * 1.05)} C{f(cx + r * 1.22)} {f(cy - r * 1.05)} {f(cx + r * 1.2)} {f(cy + r * 1.2)} {f(cx)} {f(cy + r * 1.2)} "
              f"C{f(cx - r * 1.2)} {f(cy + r * 1.2)} {f(cx - r * 1.22)} {f(cy - r * 1.05)} {f(cx)} {f(cy - r * 1.05)} Z", color, OUT, ol)
    if shine:
        o += ellipse(cx - r * 0.42, cy - r * 0.4, r * 0.18, r * 0.34, "#ffffff", None, op=0.55)
    return o


def bunting(p0, p1, sag, n, colors=PAPER, size=15, line_c="#fff3e0", ol=1.6):
    """Triangular flags hung along a sagging cord (quadratic curve p0 -> p1, sag px below the chord's middle)."""
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + sag * 2
    o = path(f"M{f(p0[0])} {f(p0[1])} Q{f(mx)} {f(my)} {f(p1[0])} {f(p1[1])}", None, OUT, 3.2) + path(f"M{f(p0[0])} {f(p0[1])} Q{f(mx)} {f(my)} {f(p1[0])} {f(p1[1])}", None, line_c, 1.4)
    for i in range(n):
        t = (i + 0.5) / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * mx + t * t * p1[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * my + t * t * p1[1]
        o += poly([(x - size * 0.55, y), (x + size * 0.55, y), (x, y + size * 1.1)], colors[i % len(colors)], OUT, ol)
        o += line((x - size * 0.3, y + 2), (x - size * 0.05, y + size * 0.6), "#ffffff", 1.2, 0.5)
    return o


def star_paper(cx, cy, r, color, n=8, ol=1.8):
    """A folded paper star (two-tone points)."""
    o = ""
    for k in range(n):
        a = -math.pi / 2 + k * math.tau / n
        a2 = a + math.tau / n / 2
        tip = (cx + math.cos(a) * r, cy + math.sin(a) * r)
        b0 = (cx + math.cos(a - math.tau / n / 2) * r * 0.42, cy + math.sin(a - math.tau / n / 2) * r * 0.42)
        b1 = (cx + math.cos(a2) * r * 0.42, cy + math.sin(a2) * r * 0.42)
        o += poly([b0, tip, b1], color if k % 2 == 0 else lighten(color, 0.3), OUT, ol)
    o += circle(cx, cy, r * 0.22, lighten(color, 0.55), OUT, 1.2)
    return o


def hang_string(x, y0, y1, color="#fff3e0"):
    return line((x, y0), (x, y1), OUT, 2.6) + line((x, y0), (x, y1), color, 1.0)


def heart_shape(cx, cy, s, fill, sw=1.8, stroke=OUT):
    return path(f"M{f(cx)} {f(cy + s * 0.9)} C{f(cx - s * 1.5)} {f(cy - s * 0.2)} {f(cx - s * 0.8)} {f(cy - s * 1.2)} {f(cx)} {f(cy - s * 0.4)} "
                f"C{f(cx + s * 0.8)} {f(cy - s * 1.2)} {f(cx + s * 1.5)} {f(cy - s * 0.2)} {f(cx)} {f(cy + s * 0.9)} Z", fill, stroke, sw)


def card(cx, cy, w, h, color, kind, ang=0.0):
    """A little greetings card hanging by a peg: a folded rectangle with a heart / flower / star on it."""
    rot = f' transform="rotate({f(ang)} {f(cx)} {f(cy - h / 2)})"'
    o = rect(cx - w / 2, cy - h / 2, w, h, color, OUT, 1.8, rx=1.5)
    o += rect(cx - w / 2 + 2.4, cy - h / 2 + 2.4, w - 4.8, h - 4.8, lighten(color, 0.55), None, rx=1)
    if kind == 0:
        o += heart_shape(cx, cy + 1, 4.4, "#ff6f8f", 1.0)
    elif kind == 1:
        o += flower(cx, cy + 1, 4.6, "#ffd23f", "#ff8f7a", 5, 0.9)
    elif kind == 2:
        o += star_paper(cx, cy + 1, 6.4, "#ffc65a", 5, 1.0)
    else:
        o += circle(cx, cy + 1, 4.2, "#7fd1c4", OUT, 1.0) + line((cx - 6, cy + 8), (cx + 6, cy + 8), color, 1.4)
    o += rect(cx - 2, cy - h / 2 - 5, 4, 9, "#ffe27a", OUT, 1.0)
    return f"<g{rot}>{o}</g>"


# ---- wall things ---------------------------------------------------------------------------------------------------------------------------

def window_scene(pts, uid, sky=("#9ed8f0", "#f9eecb"), sun_xy=None, trees=True, seed=4):
    """A window (4 corner points of a quad: tl, tr, br, bl) showing a bright morning garden; returns (defs, body)."""
    rng = random.Random(seed)
    tl, tr, br, bl = pts
    defs = clip(uid, poly(pts, "#000"))
    defs += lin_grad(uid + "s", [(0, sky[0]), (0.75, sky[1]), (1, "#fff6d8")], 0, 0, 0, 1)
    body = poly(pts, f"url(#{uid}s)")
    inner = ""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    x0, y0 = min(xs), min(ys)
    if trees:
        for k in range(7):
            cx = x0 + w * (k + 0.5) / 7 + rng.uniform(-6, 6)
            cy = y0 + h * 0.82 - rng.uniform(0, h * 0.14)
            inner += circle(cx, cy, h * rng.uniform(0.15, 0.24), ["#9ccf86", "#86c27a", "#b3dc90"][k % 3], None, op=0.95)
        inner += poly([(x0 - 20, y0 + h * 0.9), (x0 + w + 20, y0 + h * 0.9), (x0 + w + 20, y0 + h + 20), (x0 - 20, y0 + h + 20)], "#8ccc80", None)
    if sun_xy:
        inner += circle(sun_xy[0], sun_xy[1], h * 0.12, "#fff6c8", None, op=0.95) + circle(sun_xy[0], sun_xy[1], h * 0.22, "#fff2b0", None, op=0.35)
    body += group(inner, f'clip-path="url(#{uid})"')
    return defs, body


def picture(pts, color, kind, frame="#fff3e0"):
    """A framed picture on a (possibly skewed) wall quad: tl, tr, br, bl."""
    o = poly(pts, frame, OUT, 2.4)
    (ax, ay), (bx, by), (cx, cy), (dx, dy) = pts

    def lerp(p, q, t):
        return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)

    def inset(t):
        tl, tr, br, bl = lerp(pts[0], pts[2], t), lerp(pts[1], pts[3], t), lerp(pts[2], pts[0], t), lerp(pts[3], pts[1], t)
        return [tl, tr, br, bl]
    inn = inset(0.14)
    o += poly(inn, color, OUT, 1.2)
    mid = lerp(lerp(inn[0], inn[2], 0.5), lerp(inn[1], inn[3], 0.5), 0.5)
    sc = abs(inn[1][0] - inn[0][0]) * 0.3
    if kind == "sun":
        o += circle(mid[0], mid[1] - sc * 0.2, sc * 0.9, "#ffd23f", None) + circle(mid[0], mid[1] - sc * 0.2, sc * 0.5, "#ffe9a8", None)
    elif kind == "hills":
        o += path(f"M{f(inn[3][0])} {f(inn[3][1])} Q{f(mid[0])} {f(mid[1] - sc)} {f(inn[2][0])} {f(inn[2][1])} Z", "#7fd1a0", None)
    elif kind == "flower":
        o += flower(mid[0], mid[1], sc * 0.8, "#ff8f7a", "#ffd23f", 6, 1.0)
    elif kind == "boat":
        o += poly([(mid[0] - sc, mid[1] + sc * 0.3), (mid[0] + sc, mid[1] + sc * 0.3), (mid[0] + sc * 0.6, mid[1] + sc * 0.8), (mid[0] - sc * 0.6, mid[1] + sc * 0.8)], "#ff8f7a", OUT, 1.0)
        o += poly([(mid[0], mid[1] - sc), (mid[0] + sc * 0.8, mid[1] + sc * 0.2), (mid[0], mid[1] + sc * 0.2)], "#ffffff", OUT, 1.0)
    return o


def lamp_shade(cx, by, h, color="#ffe9a8", base="#c98f55"):
    """A bedside table lamp standing on y = by."""
    o = path(f"M{f(cx - 4)} {f(by)} L{f(cx + 4)} {f(by)} L{f(cx + 2)} {f(by - h * 0.5)} L{f(cx - 2)} {f(by - h * 0.5)} Z", base, OUT, 2)
    o += ellipse(cx, by - 1, 11, 4, base, OUT, 2)
    o += poly([(cx - 12, by - h * 0.46), (cx + 12, by - h * 0.46), (cx + 20, by - h), (cx - 20, by - h)], color, OUT, 2.2)
    o += line((cx - 14, by - h * 0.55), (cx - 17, by - h * 0.9), "#ffffff", 2, 0.6)
    return o


def cushion_heart(cx, cy, s, color):
    return heart_shape(cx, cy, s, color, 2.2) + path(f"M{f(cx - s * 0.7)} {f(cy - s * 0.6)} q{f(s * 0.3)} {f(-s * 0.3)} {f(s * 0.6)} {f(-s * 0.1)}", None, "#ffffff", 1.6, sop=0.6)


def teddy(cx, by, s=1.0, color="#c98f55"):
    """A small teddy bear sitting on y = by."""
    o = ""
    for sx in (-1, 1):
        o += circle(cx + sx * 9 * s, by - 28 * s, 4.6 * s, color, OUT, 1.8)  # ears
        o += ellipse(cx + sx * 12 * s, by - 5 * s, 5.4 * s, 4 * s, color, OUT, 1.8)  # feet
        o += ellipse(cx + sx * 14 * s, by - 16 * s, 4.2 * s, 6 * s, color, OUT, 1.8)  # arms
    o += ellipse(cx, by - 11 * s, 11.5 * s, 11 * s, color, OUT, 2)
    o += ellipse(cx, by - 9 * s, 6.6 * s, 6.6 * s, lighten(color, 0.4), None)
    o += circle(cx, by - 25 * s, 9.6 * s, color, OUT, 2)
    o += ellipse(cx, by - 22 * s, 4.6 * s, 3.6 * s, lighten(color, 0.45), None)
    o += circle(cx, by - 23 * s, 1.5 * s, OUT) + circle(cx - 4 * s, by - 27 * s, 1.3 * s, OUT) + circle(cx + 4 * s, by - 27 * s, 1.3 * s, OUT)
    o += poly([(cx - 5 * s, by - 18 * s), (cx, by - 15 * s), (cx + 5 * s, by - 18 * s), (cx + 3 * s, by - 14 * s), (cx - 3 * s, by - 14 * s)], "#ff6f8f", OUT, 1.2)
    return o


def person_dots(*a, **k):
    return ""
