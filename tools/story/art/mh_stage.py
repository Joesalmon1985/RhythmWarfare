"""The Mental Hospital chapter's day room (view `main`): a ward day room of mint and lilac pastel walls, mismatched armchairs,
a wall TV, tall windows onto a garden and a checkered vinyl floor, seen from the DJ's eye line in the 1280 x 720 design space.

Tone: kind and whimsical. Cool mint/lilac fluorescent daylight, warmed by party lights added by the runtime (the lighting sprites
stay white). This module holds the shared palette, the one-point-perspective `Room`, a small prop library the other rooms reuse,
the `main` backdrop, speakers, riser, desk and the manifest assembly. Sprites, silhouettes and the interlude live in
mh_sprites.py, the authored pieces in mh_pieces.py and the three extra rooms in mh_views*.py.
"""
from __future__ import annotations

import math
import random

from .lib import (OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, pivot_in, poly, rad_grad, rect,
                  write_svg)

W, H = 1280, 720

# palette: cool mint and lilac with warm accents
MINT, MINT_D, MINT_L = "#bfeadf", "#9bd6c8", "#dff6ef"
LILAC, LILAC_D, LILAC_L = "#c9b8f0", "#a994de", "#e6dcfa"
CREAM, PEACH, CORAL, BUTTER, SKY, LEAF = "#fff4dc", "#ffcfae", "#ff8f8a", "#ffd966", "#bfe6ff", "#7fcf8f"
WOOD, WOOD_D, WOOD_L = "#d9a76a", "#a8743c", "#f0c88e"
INK = "#2a1b4e"
FLOOR_A, FLOOR_B, SEAM = "#d2ebdd", "#e6def7", "#a9c8bb"


class Room:
    """One-point perspective box: vanishing point (vx, vy), far wall rectangle fx0..fx1 x fy0..fy1 (symmetric about vx)."""

    def __init__(self, vx, vy, fx0, fx1, fy0, fy1):
        self.vx, self.vy, self.fx0, self.fx1, self.fy0, self.fy1 = vx, vy, fx0, fx1, fy0, fy1
        self.half = vx - fx0
        self.height = fy1 - fy0

    def scale(self, y):
        """Depth scale of floor row y: 1 at the far wall base, growing towards the camera."""
        return (y - self.vy) / (self.fy1 - self.vy)

    def floor_x(self, xfar, y):
        return self.vx + (xfar - self.vx) * self.scale(y)

    def floor_y(self, s):
        return self.vy + (self.fy1 - self.vy) * s

    def wall(self, side, s, u):
        """Point on the left (side -1) or right (+1) wall plane at depth scale s, u far-px above the floor."""
        return (self.vx + side * self.half * s, self.vy + (self.fy1 - u - self.vy) * s)

    def ceil(self, xfar, s):
        """Point on the ceiling plane: x on the far wall's top edge, depth scale s."""
        return (self.vx + (xfar - self.vx) * s, self.vy + (self.fy0 - self.vy) * s)

    def floor_pt(self, xfar, s):
        return (self.vx + (xfar - self.vx) * s, self.floor_y(s))

    def rows(self, front_y=438, ys=(286, 316, 350, 390, 438)):
        return [{"y": y, "scale": round(self.scale(y) / self.scale(front_y), 3)} for y in ys]

    def grid(self, nfar=9):
        step = (self.fx1 - self.fx0) / (nfar - 1)
        return {"vanishing_point": [self.vx, self.vy], "far_y": self.fy1, "far_x": [round(self.fx0 + step * i, 1) for i in range(nfar)],
                "note": "x on the far wall base line; a floor line through far_x at screen row y is at x = vp_x + (far_x - vp_x) * (y - vp_y) / (far_y - vp_y)"}

    def s_at_x(self, side, x):
        """Depth scale at which the wall plane reaches screen x."""
        return abs(x - self.vx) / self.half


R = Room(640, 132, 310, 970, 50, 262)


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


# ---- prop library (frontal, flat-cartoon, 3px indigo outline) --------------------------------------------------------------

def shade_r(x, y, w, h, op=0.14, rx=0):
    return rect(x, y, w, h, "#2a1b4e", None, rx=rx, op=op)


def paper_star(cx, cy, r, col, ol=1.6, rot=-90):
    pts_ = [(cx + math.cos(math.radians(rot + k * 36)) * (r if k % 2 == 0 else r * 0.45), cy + math.sin(math.radians(rot + k * 36)) * (r if k % 2 == 0 else r * 0.45)) for k in range(10)]
    return poly(pts_, col, OUT, ol)


def heart(cx, cy, r, col, ol=1.4):
    return path(f"M{f(cx)} {f(cy + r * 0.9)} C{f(cx - r * 1.5)} {f(cy - r * 0.2)} {f(cx - r * 0.7)} {f(cy - r * 1.2)} {f(cx)} {f(cy - r * 0.35)} "
                f"C{f(cx + r * 0.7)} {f(cy - r * 1.2)} {f(cx + r * 1.5)} {f(cy - r * 0.2)} {f(cx)} {f(cy + r * 0.9)} Z", col, OUT, ol)


def window(x, y, w, h, uid="win", frame="#fbfbff", sash=2.6, scene="garden", ol=3.0, mullions=(1, 1)):
    """A window with a garden or sky view; returns (defs, svg)."""
    defs = lin_grad(uid, [(0, "#9fd8ff"), (0.6, "#d6f1ff"), (1, "#f4ffe8")], 0, 0, 0, 1)
    d = rect(x - 5, y - 5, w + 10, h + 10, frame, OUT, ol, rx=2)
    d += rect(x, y, w, h, f"url(#{uid})", None)
    if scene == "garden":
        m = min(w, h * 0.8)
        gy = y + h * 0.66
        defs += clip(uid + "c", f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}"/>')
        g = ellipse(x + w * 0.3, gy + 4, w * 0.6, h * 0.16, "#8fd98a", None) + ellipse(x + w * 0.85, gy + 8, w * 0.55, h * 0.18, "#76c97f", None)
        g += rect(x, gy + 2, w, y + h - gy - 2, "#8fd98a", None, op=0.95)
        nt = max(1, int(w / (m * 0.9)))
        for k in range(nt):  # trees spread along the window
            tx = x + w * (k + 0.5) / nt + (m * 0.2 if k % 2 else -m * 0.1)
            g += circle(tx, gy - h * 0.1, m * (0.22 if k % 2 == 0 else 0.17), "#5dbb7a" if k % 2 == 0 else "#6cc98a", None) + rect(tx - m * 0.015, gy - h * 0.02, m * 0.03, h * 0.12, "#8a5a3a", None)
        g += circle(x + w * 0.8, y + h * 0.2, m * 0.1, "#fff6b0", None, op=0.95)
        g += ellipse(x + w * 0.35, y + h * 0.22, m * 0.18, h * 0.05, "#ffffff", None, op=0.9) + ellipse(x + w * 0.45, y + h * 0.26, m * 0.12, h * 0.04, "#ffffff", None, op=0.9)
        d += group(g, f'clip-path="url(#{uid}c)"')
    d += rect(x, y, w, h * 0.5, "#ffffff", None, op=0.12)
    d += poly([(x, y + h), (x + w * 0.3, y), (x + w * 0.52, y), (x + w * 0.22, y + h)], "#ffffff", None, op=0.14)
    nx, ny = mullions
    for k in range(1, nx + 1):
        d += rect(x + w * k / (nx + 1) - sash / 2, y, sash, h, frame, OUT, 1.2)
    for k in range(1, ny + 1):
        d += rect(x, y + h * k / (ny + 1) - sash / 2, w, sash, frame, OUT, 1.2)
    d += rect(x - 8, y + h + 3, w + 16, 6, "#f0eefb", OUT, 2.2, rx=2)  # sill
    return defs, d


def door(x, y, w, h, col="#e9c58f", uid="dr", porthole=True, star=True, plate=True):
    """A friendly ward door: warm painted wood, round porthole, a paper star and a brass handle."""
    defs = lin_grad(uid, [(0, lighten(col, 0.18)), (1, darken(col, 0.1))], 0, 0, 1, 0)
    d = rect(x - 6, y - 5, w + 12, h + 5, "#fbfbff", OUT, 3, rx=2)
    d += rect(x, y, w, h, f"url(#{uid})", OUT, 2.4)
    d += rect(x + w * 0.1, y + h * 0.08, w * 0.8, h * 0.34, darken(col, 0.06), OUT, 1.4, rx=2, op=0.55)
    d += rect(x + w * 0.1, y + h * 0.5, w * 0.8, h * 0.4, darken(col, 0.06), OUT, 1.4, rx=2, op=0.55)
    if porthole:
        d += circle(x + w / 2, y + h * 0.27, w * 0.24, "#e8f7ff", OUT, 2.4) + circle(x + w / 2, y + h * 0.27, w * 0.17, "#bfe6ff", None)
        d += path(f"M{f(x + w * 0.38)} {f(y + h * 0.23)} Q{f(x + w * 0.46)} {f(y + h * 0.17)} {f(x + w * 0.5)} {f(y + h * 0.2)}", None, "#ffffff", 1.6, sop=0.8)
    if star:
        d += paper_star(x + w * 0.5, y + h * 0.64, w * 0.17, BUTTER)
    d += circle(x + w * 0.84, y + h * 0.56, 2.6, "#d8b24a", OUT, 1.2)
    if plate:
        d += rect(x + w * 0.76, y + h * 0.48, w * 0.14, h * 0.07, "#d8b24a", OUT, 1.0, rx=1)
    return defs, d


def armchair(x, yb, w, col, trim=None, blanket=None, s=1.0):
    """A squashy frontal armchair standing on y=yb (x = centre); mismatched colours are the point."""
    h = w * 0.82
    trim = trim or darken(col, 0.18)
    d = ellipse(x, yb + 2, w * 0.58, 6 * s, INK, None, op=0.22)
    for sx in (-1, 1):  # stubby legs
        d += rect(x + sx * w * 0.38 - 3, yb - 8, 6, 8, WOOD_D, OUT, 1.6)
    d += rect(x - w * 0.34, yb - h, w * 0.68, h * 0.62, col, OUT, 3, rx=w * 0.16)  # back
    d += rect(x - w * 0.34, yb - h, w * 0.68, h * 0.62, "#ffffff", None, op=0.1, rx=w * 0.16)
    d += rect(x - w * 0.5, yb - h * 0.52, w * 0.2, h * 0.44, trim, OUT, 3, rx=w * 0.08) + rect(x + w * 0.3, yb - h * 0.52, w * 0.2, h * 0.44, trim, OUT, 3, rx=w * 0.08)
    d += rect(x - w * 0.31, yb - h * 0.36, w * 0.62, h * 0.3, lighten(col, 0.12), OUT, 3, rx=w * 0.07)  # seat cushion
    d += line((x - w * 0.2, yb - h * 0.3), (x + w * 0.2, yb - h * 0.3), "#ffffff", 1.6, 0.35)
    d += circle(x, yb - h * 0.72, 2.2, trim, OUT, 1.0)  # button
    if blanket:
        d += poly([(x - w * 0.32, yb - h * 0.34), (x + w * 0.1, yb - h * 0.36), (x + w * 0.16, yb - h * 0.04), (x - w * 0.3, yb - h * 0.05)], blanket, OUT, 2)
        for k in range(4):
            d += line((x - w * 0.3 + k * w * 0.11, yb - h * 0.2), (x - w * 0.3 + k * w * 0.11 + 5, yb - h * 0.05), lighten(blanket, 0.4), 1.4, 0.7)
    return d


def plant(x, yb, h, pot="#e07a5a", kind="fern"):
    d = ellipse(x, yb + 1, h * 0.16, 3, INK, None, op=0.2)
    pw = h * 0.17
    d += poly([(x - pw, yb - h * 0.28), (x + pw, yb - h * 0.28), (x + pw * 0.74, yb), (x - pw * 0.74, yb)], pot, OUT, 2.4)
    d += rect(x - pw * 1.08, yb - h * 0.31, pw * 2.16, h * 0.06, lighten(pot, 0.2), OUT, 2)
    top = yb - h * 0.3
    if kind == "fern":
        for k in range(9):
            a = math.radians(-160 + k * 40)
            tx, ty = x + math.cos(a) * h * 0.42, top - h * 0.3 + math.sin(a) * h * 0.4
            d += path(f"M{f(x)} {f(top)} Q{f((x + tx) / 2)} {f(top - h * 0.35)} {f(tx)} {f(ty)}", None, OUT, 5.6)
            d += path(f"M{f(x)} {f(top)} Q{f((x + tx) / 2)} {f(top - h * 0.35)} {f(tx)} {f(ty)}", None, LEAF if k % 2 else "#5dbb7a", 3.4)
    else:  # rubber-plant style big leaves
        for k, a in enumerate((-125, -95, -65, -150, -40)):
            tx, ty = x + math.cos(math.radians(a)) * h * 0.4, top + math.sin(math.radians(a)) * h * 0.6
            d += line((x, top), (tx, ty + 6), OUT, 4) + ellipse(tx, ty, h * 0.12, h * 0.2, LEAF if k % 2 else "#5dbb7a", OUT, 2.2)
    return d


def rug_ellipse(cx, cy, rx, ry, cols, uid=""):
    d = ""
    n = len(cols)
    for k, c in enumerate(cols):
        t = 1 - k / n
        d += ellipse(cx, cy, rx * t, ry * t, c, OUT if k == 0 else None, 3 if k == 0 else 0)
    return d


def bunting_flag(x, y, w, h, col):
    return poly([(x - w / 2, y), (x + w / 2, y), (x, y + h)], col, OUT, 1.6)


def clock(cx, cy, r, face="#fffdf4", rim="#7fcfc0"):
    d = circle(cx, cy, r + 3, rim, OUT, 2.4) + circle(cx, cy, r, face, OUT, 1.6)
    for k in range(12):
        a = math.radians(k * 30 - 90)
        d += line((cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78), (cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9), INK, 1.6 if k % 3 == 0 else 1.0)
    d += line((cx, cy), (cx + r * 0.1, cy - r * 0.5), INK, 2.2) + line((cx, cy), (cx + r * 0.52, cy + r * 0.12), INK, 1.8) + circle(cx, cy, 1.8, CORAL, INK, 1)
    return d


# ---- backdrop: room shell, floor ---------------------------------------------------------------------------------------------

def room_shell(R, wall=MINT, dado=LILAC, uidp="", ceil_tile=True, floor=(FLOOR_A, FLOOR_B), floor_seam=SEAM, extend=40, floor_fn=None, sky=None):
    """Ceiling, side walls with dado and skirting, far wall and the checkered vinyl floor for room R. Returns (defs, svg)."""
    defs = ""
    d = ""
    vx, vy = R.vx, R.vy
    defs += lin_grad(uidp + "ceil", [(0, "#c9d6e4"), (1, "#f4f9fb")], 0, 0, 0, 1)
    defs += lin_grad(uidp + "fw", [(0, lighten(wall, 0.2)), (1, darken(wall, 0.04))], 0, 0, 0, 1)
    defs += lin_grad(uidp + "lw", [(0, darken(wall, 0.2)), (1, darken(wall, 0.02))], 0, 0, 1, 0)
    defs += lin_grad(uidp + "rw", [(0, darken(wall, 0.02)), (1, darken(wall, 0.2))], 0, 0, 1, 0)
    defs += lin_grad(uidp + "fl", [(0, darken(floor[0], 0.1)), (1, lighten(floor[0], 0.2))], 0, 0, 0, 1)
    yt = -extend
    d += rect(0, 0, W, H, mix(wall, "#ffffff", 0.2))
    # ceiling
    xl = vx - (vx - R.fx0) * (vy - yt) / (vy - R.fy0)
    xr = vx + (R.fx1 - vx) * (vy - yt) / (vy - R.fy0)
    d += poly([(xl, yt), (xr, yt), (R.fx1, R.fy0), (R.fx0, R.fy0)], f"url(#{uidp}ceil)")
    if ceil_tile:
        for k in range(-8, 9):
            xf = vx + k * 55.0
            if R.fx0 <= xf <= R.fx1:
                xt = vx + (xf - vx) * (yt - vy) / (R.fy0 - vy)
                d += line((xf, R.fy0), (xt, yt), "#8e9cb8", 1.4, 0.5)
        s = 1.0
        while s < 3:
            yy = vy + (R.fy0 - vy) * s
            if yy < yt:
                break
            d += line((vx - R.half * s, yy), (vx + R.half * s, yy), "#8e9cb8", 1.4, 0.5)
            s += 0.17
    # far wall
    d += rect(R.fx0, R.fy0, R.fx1 - R.fx0, R.fy1 - R.fy0, f"url(#{uidp}fw)")
    dh = 74  # dado height
    d += rect(R.fx0, R.fy1 - dh, R.fx1 - R.fx0, dh, dado, None)
    d += rect(R.fx0, R.fy1 - dh - 5, R.fx1 - R.fx0, 6, lighten(dado, 0.4), OUT, 2)  # dado rail
    for x in range(int(R.fx0) + 14, int(R.fx1), 28):
        d += line((x, R.fy1 - dh + 4), (x, R.fy1), darken(dado, 0.1), 1.2, 0.5)
    d += rect(R.fx0, R.fy1 - 9, R.fx1 - R.fx0, 9, darken(dado, 0.2), OUT, 2)  # skirting
    # side walls
    for side, gid in ((-1, "lw"), (1, "rw")):
        x_edge = 0 if side < 0 else W
        s_e = abs(x_edge - vx) / R.half
        top_e = R.wall(side, s_e, R.height)
        bot_e = R.wall(side, s_e, 0)
        far_top, far_bot = R.wall(side, 1, R.height), R.wall(side, 1, 0)
        d += poly([(x_edge, top_e[1] - extend), far_top, far_bot, (x_edge, bot_e[1])], f"url(#{uidp}{gid})")
        # dado band, rail and skirting as quads on the wall plane
        for (u0, u1, col, ol) in ((0, 8, darken(dado, 0.2), 2), (8, dh, dado, 0), (dh, dh + 5, lighten(dado, 0.4), 2)):
            q = [R.wall(side, 1, u0), R.wall(side, s_e, u0), R.wall(side, s_e, u1), R.wall(side, 1, u1)]
            d += poly(q, col, OUT if ol else None, ol or 0)
        for k in range(1, 8):  # vertical seams of the dado boards
            s = 1 + (s_e - 1) * k / 8.0
            d += line(R.wall(side, s, 8), R.wall(side, s, dh), darken(dado, 0.12), 1.2, 0.4)
    # floor
    d += poly([(0, R.vy + (R.fy1 - R.vy) * (vx / R.half)), (W, R.vy + (R.fy1 - R.vy) * (vx / R.half)), (W, H), (0, H)], f"url(#{uidp}fl)")
    if floor_fn is None:
        d += floor_checker(R, floor, floor_seam)
    else:  # a custom floor, clipped to the floor polygon so it never paints over the walls
        ye = R.vy + (R.fy1 - R.vy) * (vx / R.half)
        fp = f'<polygon points="0,{f(ye)} {f(R.fx0)},{f(R.fy1)} {f(R.fx1)},{f(R.fy1)} {W},{f(ye)} {W},{H} 0,{H}"/>'
        defs += clip(uidp + "flc", fp)
        d += group(floor_fn(R), f'clip-path="url(#{uidp}flc)"')
    # wall/floor shadow line
    for side in (-1, 1):
        x_edge = 0 if side < 0 else W
        s_e = abs(x_edge - vx) / R.half
        a, b = R.wall(side, 1, 0), R.wall(side, s_e, 0)
        d += line(a, b, OUT, 2.6, 0.9)
        d += poly([a, b, (b[0], b[1] + 14 * s_e), (a[0], a[1] + 6)], INK, None, op=0.1)
    return defs, d


def floor_checker(R, cols, seam, ncols=10, dz=0.06):
    """Checkered vinyl in perspective: `ncols` columns across the far wall, rows equally spaced in depth (z = 1/scale)."""
    d = ""
    step = (R.fx1 - R.fx0) / ncols
    rows = []
    z = 1.0
    while z > 0.18:
        s = 1.0 / z
        rows.append((s, R.floor_y(s)))
        z -= dz
    cols_x = [R.fx0 + step * i for i in range(-2 * ncols, 3 * ncols + 1)]
    for ri in range(len(rows) - 1):
        s0, y0 = rows[ri]
        s1, y1 = rows[ri + 1]
        for ci in range(len(cols_x) - 1):
            if (ri + ci) % 2:
                continue
            xa, xb = cols_x[ci], cols_x[ci + 1]
            q = [(R.vx + (xa - R.vx) * s0, y0), (R.vx + (xb - R.vx) * s0, y0), (R.vx + (xb - R.vx) * s1, y1), (R.vx + (xa - R.vx) * s1, y1)]
            if max(p[0] for p in q) < -20 or min(p[0] for p in q) > W + 20:
                continue
            d += poly(q, cols[1], None, op=0.9)
    for s0, y0 in rows:
        d += line((-20, y0), (W + 20, y0), seam, 1.2, 0.4)
    for xa in cols_x:
        d += line((R.vx + (xa - R.vx) * 1.0, R.floor_y(1.0)), (R.vx + (xa - R.vx) * 5.5, R.floor_y(5.5)), seam, 1.2, 0.4)
    return d


def build_backdrop():
    defs, d = room_shell(R)
    # ---- far wall: door, windows, TV bracket, shelf ----
    ddefs, dd = door(336, 146, 62, 116)
    defs += ddefs
    d += dd
    for k, (wx, uid) in enumerate(((414, "w1"), (790, "w2"))):
        wd, wdd = window(wx, 84, 76, 114, uid, mullions=(1, 1))
        defs += wd
        d += wdd
    # the TV: a dark panel in a pale frame on a bracket (the runtime paints into led_screen)
    tx, ty, tw, th = 500, 76, 280, 70
    d += rect(tx - 9, ty - 9, tw + 18, th + 18, "#f3f1fb", OUT, 3.4, rx=7)
    d += rect(tx - 4, ty - 4, tw + 8, th + 8, "#2a2c44", OUT, 2, rx=4)
    d += rect(tx, ty, tw, th, "#10111e", None)
    d += rect(tx - 10, ty + th + 9, tw + 20, 9, LILAC_D, OUT, 2.4, rx=3)  # shelf/bracket under the TV
    d += circle(tx + tw - 12, ty + th + 4, 2.4, "#7affc0", OUT, 0.8)
    # shelf with a plant and a teapot on the far wall, below the TV
    d += rect(560, 168, 160, 7, WOOD, OUT, 2.4, rx=2) + line((572, 175), (572, 188), OUT, 3) + line((708, 175), (708, 188), OUT, 3)
    d += plant(584, 168, 40, "#ff9a7a")
    d += poly([(646, 168), (650, 150), (676, 150), (680, 168)], "#fff4dc", OUT, 2) + path("M680 154 Q692 156 686 166", None, OUT, 3) + path("M680 154 Q692 156 686 166", None, "#fff4dc", 1.4) + circle(663, 147, 3, CORAL, OUT, 1.2)
    d += rect(694, 154, 14, 14, "#bfe6ff", OUT, 2, rx=2)
    # radiator under the right window
    # ---- left wall (side -1): two big windows, a bookcase, a coat rack ----
    for (s0, s1, uid) in ((1.2, 1.5, "lw1"), (1.62, 1.9, "lw2")):
        q = [R.wall(-1, s0, 150), R.wall(-1, s1, 150), R.wall(-1, s1, 52), R.wall(-1, s0, 52)]
        frame = [R.wall(-1, s0 - 0.02, 156), R.wall(-1, s1 + 0.02, 156), R.wall(-1, s1 + 0.02, 46), R.wall(-1, s0 - 0.02, 46)]
        defs += lin_grad(uid, [(0, "#a8dcff"), (0.6, "#e2f5ff"), (1, "#f6ffee")], 0, 0, 0, 1)
        d += poly(frame, "#fbfbff", OUT, 3)
        d += poly(q, f"url(#{uid})", None)
        mid = [R.wall(-1, s0, 100), R.wall(-1, s1, 100)]
        gq = [R.wall(-1, s0, 82), R.wall(-1, s1, 82), R.wall(-1, s1, 52), R.wall(-1, s0, 52)]
        d += poly(gq, "#8fd98a", None, op=0.95)
        d += poly([R.wall(-1, s0, 130), R.wall(-1, s1, 130), R.wall(-1, s1, 118), R.wall(-1, s0, 118)], "#ffffff", None, op=0.18)
        sm = (s0 + s1) / 2
        d += line(R.wall(-1, sm, 150), R.wall(-1, sm, 52), "#fbfbff", 4) + line(R.wall(-1, s0, 101), R.wall(-1, s1, 101), "#fbfbff", 4)
        d += line(R.wall(-1, sm, 150), R.wall(-1, sm, 52), OUT, 1.0)
        tr = R.wall(-1, sm, 100)
        d += circle(tr[0] + 2, tr[1] + 8, 18 * sm * 0.5, "#5dbb7a", None, op=0.9)
        sill = [R.wall(-1, s0 - 0.03, 52), R.wall(-1, s1 + 0.03, 52), R.wall(-1, s1 + 0.03, 46), R.wall(-1, s0 - 0.03, 46)]
        d += poly(sill, "#f0eefb", OUT, 2)
    # blinds half drawn on the nearer window
    q = [R.wall(-1, 1.62, 150), R.wall(-1, 1.9, 150), R.wall(-1, 1.9, 128), R.wall(-1, 1.62, 128)]
    d += poly(q, "#f4f1dd", OUT, 1.6)
    for k in range(1, 5):
        d += line(R.wall(-1, 1.62, 150 - k * 5), R.wall(-1, 1.9, 150 - k * 5), darken("#f4f1dd", 0.2), 1.0, 0.8)
    # ---- right wall (side +1): framed patient art, a pinboard and a tea hatch ----
    arts = [((1.18, 1.32), (150, 112), "#ffd0e0", "heart"), ((1.38, 1.55), (146, 100), "#cfe9ff", "sun"), ((1.62, 1.82), (150, 108), "#fff0b0", "house")]
    for (s0, s1), (u1, u0), col, kind in arts:
        fr = [R.wall(1, s0, u1), R.wall(1, s1, u1), R.wall(1, s1, u0), R.wall(1, s0, u0)]
        d += poly(fr, "#fbfbff", OUT, 2.6)
        pad = 0.012
        inner = [R.wall(1, s0 + pad, u1 - 3), R.wall(1, s1 - pad, u1 - 3), R.wall(1, s1 - pad, u0 + 3), R.wall(1, s0 + pad, u0 + 3)]
        d += poly(inner, col, None)
        cx = (inner[0][0] + inner[1][0]) / 2
        cy = (inner[0][1] + inner[2][1]) / 2
        sc = (s0 + s1) / 2
        if kind == "heart":
            d += heart(cx, cy, 7 * sc, CORAL, 1.4)
        elif kind == "sun":
            d += circle(cx, cy, 7 * sc, BUTTER, OUT, 1.4)
            for k in range(8):
                a = k * math.pi / 4
                d += line((cx + math.cos(a) * 9 * sc, cy + math.sin(a) * 9 * sc), (cx + math.cos(a) * 13 * sc, cy + math.sin(a) * 13 * sc), "#ff9a2e", 1.8)
        else:
            d += poly([(cx - 8 * sc, cy + 6 * sc), (cx - 8 * sc, cy - 3 * sc), (cx, cy - 10 * sc), (cx + 8 * sc, cy - 3 * sc), (cx + 8 * sc, cy + 6 * sc)], "#ff8f8a", OUT, 1.4)
    hatch = [R.wall(1, 1.22, 96), R.wall(1, 1.5, 96), R.wall(1, 1.5, 48), R.wall(1, 1.22, 48)]
    # a pinboard on the right wall, nearer the camera
    pb = [R.wall(1, 1.62, 142), R.wall(1, 1.9, 142), R.wall(1, 1.9, 84), R.wall(1, 1.62, 84)]
    return defs, d, pb, hatch


# ---- furniture baked into the backdrop (the crowd stands in front of it) ---------------------------------------------------

def main_furniture():
    d = ""
    d += armchair(104, 372, 112, "#ffd966", "#e8b23a", blanket="#ff8f8a")
    d += plant(40, 350, 96, "#7fb6ff", "rubber")
    d += armchair(1176, 366, 108, "#5fc9bb", "#3a9a8c", blanket=None)
    d += plant(1244, 346, 90, "#ffb07a", "fern")
    # a floor lamp beside the teal armchair
    d += ellipse(1114, 351, 12, 3, INK, None, op=0.2) + line((1114, 350), (1114, 244), OUT, 6) + line((1114, 350), (1114, 244), "#a8a2c8", 3)
    d += poly([(1094, 244), (1134, 244), (1126, 216), (1102, 216)], "#fff2c0", OUT, 2.4) + ellipse(1114, 246, 20, 3.4, "#ffe8a0", None, op=0.6)
    return d


def build_main_backdrop():
    defs, d, pb, hatch = build_backdrop()
    d += build_rug()  # the rug under the dance circle matches circle_centre / circle_radii
    d += main_furniture()
    return defs, d


def build_rug():
    cx, cy, rx, ry = 640, 372, 262, 52
    cols = ["#f3b8c8", "#fff4dc", "#b8e4d8", "#fff4dc", "#c9b8f0", "#fff4dc", "#ffd9a0", "#fff4dc", "#b8e4d8"]
    d = ellipse(cx, cy + 4, rx + 6, ry + 4, INK, None, op=0.16)
    d += rug_ellipse(cx, cy, rx, ry, cols)
    for k in range(40):  # fringe ticks
        a = k * math.tau / 40
        d += line((cx + math.cos(a) * rx, cy + math.sin(a) * ry), (cx + math.cos(a) * (rx + 7), cy + math.sin(a) * (ry + 2.4)), "#fff4dc", 2.0)
    for k in range(18):  # woven stars
        a = k * math.tau / 18 + 0.1
        d += paper_star(cx + math.cos(a) * rx * 0.72, cy + math.sin(a) * ry * 0.72, 4.2, "#ffffff", 0.0)
    return d


# ---- speakers (hi-fi cabinets), riser, desk --------------------------------------------------------------------------------

SPK_W, SPK_H = 112, 170
SPK_POS = {"speaker_l": (146, 108), "speaker_r": (1022, 108)}
SPK_WOOFERS = [(56, 50, 23), (56, 120, 34)]


def build_speaker(side):
    d = ""
    defs = lin_grad("cab", [(0, WOOD_L), (1, WOOD)], 0, 0, 1, 0)
    defs += lin_grad("grille", [(0, "#f3c8d9"), (1, "#e0a8c4")], 0, 0, 0, 1)
    d += rect(4, 6, SPK_W - 8, SPK_H - 12, "url(#cab)", OUT, 4, rx=8)
    d += rect(10, 12, SPK_W - 20, SPK_H - 24, "url(#grille)", OUT, 2.4, rx=5)
    for k in range(0, 12):  # woven grille cloth
        d += line((12, 18 + k * 12), (SPK_W - 12, 18 + k * 12), "#ffffff", 1.0, 0.25)
    for k in range(0, 9):
        d += line((16 + k * 10.5, 14), (16 + k * 10.5, SPK_H - 14), "#ffffff", 1.0, 0.18)
    for (x, y, r) in SPK_WOOFERS:
        d += circle(x, y, r + 5, "#8a5a34", OUT, 3) + circle(x, y, r + 2, "#2a2233", None)
    d += rect(SPK_W / 2 - 14, 150, 28, 8, "#fff4dc", OUT, 1.8, rx=2) + circle(SPK_W / 2 - 6, 154, 1.6, CORAL) + circle(SPK_W / 2 + 6, 154, 1.6, "#5fc9bb")
    d += rect(14, SPK_H - 10, 14, 6, WOOD_D, OUT, 2) + rect(SPK_W - 28, SPK_H - 10, 14, 6, WOOD_D, OUT, 2)
    d += line((7, 40), (7, 130), "#ffffff", 2.0, 0.5)
    return write_svg("speaker_%s.svg" % ("l" if side < 0 else "r"), (-6, -16, SPK_W + 6, SPK_H), d, defs)


def build_riser():
    """A low wooden talent-show platform with a pastel rug runner and paper bunting along its lip."""
    w, h = 240, 34
    defs = lin_grad("rt", [(0, WOOD_L), (1, WOOD)], 0, 0, 0, 1)
    defs += lin_grad("rf", [(0, WOOD), (1, WOOD_D)], 0, 0, 0, 1)
    d = poly([(22, 3), (w - 22, 3), (w - 2, 16), (2, 16)], "url(#rt)", OUT, 3)
    d += poly([(2, 16), (w - 2, 16), (w - 2, h - 3), (2, h - 3)], "url(#rf)", OUT, 3)
    d += poly([(40, 6), (w - 40, 6), (w - 22, 14), (22, 14)], "#f3b8c8", None, op=0.9)
    for k in range(1, 6):
        d += line((2 + k * (w - 4) / 6, 17), (2 + k * (w - 4) / 6, h - 5), darken(WOOD_D, 0.2), 1.6, 0.4)
    cols = [CORAL, BUTTER, "#8fd9c8", "#b9a6f0"]
    for k in range(8):
        x = 14 + k * (w - 28) / 7
        d += poly([(x - 7, 17), (x + 7, 17), (x, 28)], cols[k % 4], OUT, 1.4)
    d += line((24, 6), (w - 24, 6), "#ffffff", 1.4, 0.5)
    return write_svg("riser.svg", (0, 0, w, h), d, defs)


def build_desk_top():
    """The pad strip: deep teal formica with a mint lip, doodle stickers and masking-tape labels (1280 x 260, stretchable)."""
    w, h = 1280, 260
    defs = lin_grad("dk", [(0, "#2e5360"), (0.06, "#25444f"), (1, "#16303a")], 0, 0, 0, 1)
    defs += lin_grad("lip", [(0, "#d8f6ee"), (0.5, "#9bd6c8"), (1, "#5fa89c")], 0, 0, 0, 1)
    d = rect(0, 0, w, h, "url(#dk)")
    d += rect(0, 0, w, 16, "url(#lip)")
    d += line((0, 16), (w, 16), OUT, 3.5) + line((0, 2.5), (w, 2.5), "#ffffff", 1.6, 0.7)
    rng = random.Random(5)
    for k in range(90):  # formica flecks
        d += circle(rng.uniform(0, w), rng.uniform(22, h), rng.uniform(0.6, 1.5), "#ffffff", None, op=0.1)
    for x0, x1 in ((10, 424), (856, 1270)):
        d += rect(x0, 26, x1 - x0, h - 36, "#0f2229", OUT, 2.6, rx=14, op=0.5)
        d += rect(x0 + 5, 31, x1 - x0 - 10, h - 46, None, "#8fe0d0", 1.2, rx=11, sop=0.35)
        for sx, sy in ((x0 + 12, 38), (x1 - 12, 38), (x0 + 12, h - 22), (x1 - 12, h - 22)):
            d += circle(sx, sy, 4, "#cfeee6", OUT, 1.6) + line((sx - 2.2, sy - 2.2), (sx + 2.2, sy + 2.2), OUT, 1.1)
    mx0, mx1 = 436, 844
    d += rect(mx0, 26, mx1 - mx0, h - 36, "#1b3540", OUT, 3, rx=12)
    d += rect(mx0 + 5, 31, mx1 - mx0 - 10, h - 46, None, "#ff9a9a", 1.4, rx=9, sop=0.45)
    for k in range(0, 17):
        x = mx0 + 24 + k * ((mx1 - mx0 - 48) / 16.0)
        d += line((x, 36), (x, 36 + (9 if k % 4 == 0 else 5)), "#cfeee6", 1.4, 0.55)
        d += line((x, h - 30), (x, h - 30 - (9 if k % 4 == 0 else 5)), "#cfeee6", 1.4, 0.55)
    d += rect(mx0 + 60, h - 62, mx1 - mx0 - 120, 10, "#0b1a20", OUT, 2, rx=5)
    d += rect(mx0 + 66, h - 59, mx1 - mx0 - 132, 3, "#8fe0d0", None, op=0.35)
    for x in (mx0 + 40, mx1 - 56):
        d += rect(x, 60, 16, 80, "#0b1a20", OUT, 2, rx=3)
        for k in range(8):
            d += rect(x + 3, 64 + k * 9.4, 10, 5, ["#7affc0", "#7affc0", "#7affc0", "#b8ff8a", "#b8ff8a", BUTTER, BUTTER, CORAL][k], None, op=0.3)
    # doodles: stickers and masking tape on the lip and the wings
    for x, col, kind in ((60, BUTTER, "star"), (220, CORAL, "heart"), (380, "#b9a6f0", "star"), (900, "#8fd9c8", "heart"), (1100, BUTTER, "star"), (1230, CORAL, "heart")):
        d += (paper_star(x, 8.5, 6.4, col, 1.4) if kind == "star" else heart(x, 7.5, 4.6, col, 1.3))
    for x, y, r in ((22, 232, -6), (1230, 236, 5), (448, 236, -3), (810, 234, 4)):
        d += f'<g transform="rotate({r} {x} {y})">' + rect(x - 14, y - 5, 28, 10, "#fff0a8", OUT, 1.2, op=0.92) + "</g>"
    return write_svg("desk_top.svg", (0, 0, w, h), d, defs)


# ---- assembly ----------------------------------------------------------------------------------------------------------------

def build_stage():
    from . import mh_pieces, mh_sprites, mh_views
    sp = mh_sprites.build_sprites()
    layers = []
    defs, d = build_main_backdrop()[:2]
    d += ""
    write_svg("backdrop.svg", (0, 0, W, H), d, defs)
    layers.append({"id": "backdrop", "file": "source/backdrop.svg", "pos": [0, 0], "size": [W, H], "px_scale": 0.5})
    build_riser()
    layers.append({"id": "riser", "file": "source/riser.svg", "pos": [520, 252], "size": [240, 34], "px_scale": 0.5})
    for side in (-1, 1):
        build_speaker(side)
        sid = "speaker_l" if side < 0 else "speaker_r"
        px, py = SPK_POS[sid]
        layers.append({"id": sid, "file": f"source/{sid}.svg", "pos": [px - 6, py - 16], "size": [SPK_W + 12, SPK_H + 16], "px_scale": 0.5})
    build_desk_top()
    layers.append({"id": "desk_top", "file": "source/desk_top.svg", "pos": [0, 460], "size": [1280, 260], "px_scale": 0.5,
                   "note": "authored 1280 x 260; stretch to the pad-strip rectangle"})
    woofers = []
    for sid in ("speaker_l", "speaker_r"):
        px, py = SPK_POS[sid]
        for (wx, wy, wr) in SPK_WOOFERS:
            woofers.append([px + wx, py + wy, wr])
    pieces = mh_pieces.build_pieces()
    anchors = {
        "led_screen": [500, 76, 280, 70],
        "doorway": [336, 146, 62, 116],
        "floor_rows": R.rows(),
        "floor_polygon": [[R.fx0 + 10, 266], [R.fx1 - 10, 266], [round(R.floor_x(R.fx1, 520)), 520], [round(R.floor_x(R.fx0, 520)), 520]],
        "floor_grid": R.grid(9),
        "light_points": [[150, 30], [330, 30], [510, 30], [770, 30], [950, 30], [1130, 30], [450, 58], [830, 58]],
        "woofers": woofers,
        "disco_ball": [640, 0],
        "riser": [640, 286, 240],
        "circle_centre": [640, 372],
        "circle_radii": [250, 46],
        "wall_left_x": R.fx0, "wall_right_x": R.fx1, "horizon_y": R.vy,
    }
    stage = {"design_size": [W, H], "layers": layers, "anchors": anchors, "sprites": sp, "pieces": pieces,
             "pieces_note": "pos/size = top-left rectangle in design px; pivot (rotate/sway/flicker) is in design px relative to pos; blend add = draw additively"}
    views, passage = mh_views.build_views()
    sp["passage_frame"] = passage
    stage["views"] = views
    return stage


def build_silhouettes():
    from . import mh_sprites
    return mh_sprites.build_silhouettes()


def build_interlude():
    from . import mh_sprites
    return mh_sprites.build_interlude()


def build_all():
    from . import mh_chars
    return mh_chars.build_all()
