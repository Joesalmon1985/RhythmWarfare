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


# Every room is authored wider and taller than the 1280 x 720 frame: the moving camera pans (camera_look), sways, rolls and turns,
# and the far layers move less than the frame (parallax 0.82), so a backdrop that stopped at the frame edge would show a black gap.
XM, YM = 128, 32
X0, X1, Y0 = -XM, W + XM, -YM
BACK_BOX = (X0, Y0, X1, H)
FRONT_H = 470
FRONT_BOX = (X0, Y0, X1, FRONT_H)


def back_layer(file, lid="backdrop"):
    return layer(lid, file, (X0, Y0), (X1 - X0, H - Y0))


def front_layer(file):
    return layer("front_frame", file, (X0, Y0), (X1 - X0, FRONT_H - Y0), "front")


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


# a little hand-lettered stroke font for the ward's signs (glyph box 1 wide, 1.4 tall; y down)
GLYPHS = {
    "A": [[(0, 1.4), (.5, 0), (1, 1.4)], [(.22, .9), (.78, .9)]],
    "B": [[(0, 0), (0, 1.4), (.72, 1.4), (1, 1.12), (.72, .7), (0, .7)], [(0, 0), (.7, 0), (.95, .32), (.7, .7)]],
    "C": [[(1, .22), (.7, 0), (.3, 0), (0, .3), (0, 1.1), (.3, 1.4), (.7, 1.4), (1, 1.18)]],
    "D": [[(0, 0), (0, 1.4), (.55, 1.4), (1, 1.0), (1, .4), (.55, 0), (0, 0)]],
    "E": [[(1, 0), (0, 0), (0, 1.4), (1, 1.4)], [(0, .7), (.72, .7)]],
    "G": [[(1, .22), (.7, 0), (.3, 0), (0, .3), (0, 1.1), (.3, 1.4), (.7, 1.4), (1, 1.15), (1, .78), (.55, .78)]],
    "H": [[(0, 0), (0, 1.4)], [(1, 0), (1, 1.4)], [(0, .7), (1, .7)]],
    "I": [[(.5, 0), (.5, 1.4)]],
    "K": [[(0, 0), (0, 1.4)], [(1, 0), (0, .82)], [(.32, .6), (1, 1.4)]],
    "L": [[(0, 0), (0, 1.4), (.9, 1.4)]],
    "M": [[(0, 1.4), (0, 0), (.5, .78), (1, 0), (1, 1.4)]],
    "N": [[(0, 1.4), (0, 0), (1, 1.4), (1, 0)]],
    "O": [[(.32, 0), (.68, 0), (1, .32), (1, 1.08), (.68, 1.4), (.32, 1.4), (0, 1.08), (0, .32), (.32, 0)]],
    "P": [[(0, 1.4), (0, 0), (.75, 0), (1, .25), (1, .48), (.75, .72), (0, .72)]],
    "R": [[(0, 1.4), (0, 0), (.75, 0), (1, .25), (1, .48), (.75, .72), (0, .72)], [(.5, .72), (1, 1.4)]],
    "S": [[(1, .22), (.7, 0), (.3, 0), (0, .25), (.12, .6), (.88, .8), (1, 1.15), (.7, 1.4), (.3, 1.4), (0, 1.18)]],
    "T": [[(0, 0), (1, 0)], [(.5, 0), (.5, 1.4)]],
    "U": [[(0, 0), (0, 1.08), (.3, 1.4), (.7, 1.4), (1, 1.08), (1, 0)]],
    "W": [[(0, 0), (.22, 1.4), (.5, .55), (.78, 1.4), (1, 0)]],
    "Y": [[(0, 0), (.5, .72), (1, 0)], [(.5, .72), (.5, 1.4)]],
    "7": [[(0, 0), (1, 0), (.42, 1.4)]],
    "!": [[(.5, 0), (.5, .92)], [(.5, 1.3), (.5, 1.4)]],
}


def sign_text(txt, x, y, h, color, sw, outline=OUT, gap=0.42, centre=True):
    """Hand-lettered block capitals with round-capped strokes, (x, y) = the centre (or left end) of the line. Returns svg."""
    u = h / 1.4
    widths = [(u * 0.62 if ch == " " else u * (0.4 if ch in "I!" else 0.82)) for ch in txt]
    total = sum(widths) + u * gap * (len(txt) - 1)
    cx = x - total / 2 if centre else x
    segs = []
    for ch, wd in zip(txt, widths):
        for stroke in GLYPHS.get(ch, []):
            segs.append([(cx + px * wd, y - h / 2 + py * u) for px, py in stroke])
        cx += wd + u * gap
    out = ""
    for pass_col, pass_w in ((outline, sw + 3.0), (color, sw)):
        if pass_col is None:
            continue
        for pts_ in segs:
            out += path("M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts_), None, pass_col, pass_w)
    return out


def clock(cx, cy, r, face="#fffdf4", rim="#7fcfc0"):
    d = circle(cx, cy, r + 3, rim, OUT, 2.4) + circle(cx, cy, r, face, OUT, 1.6)
    for k in range(12):
        a = math.radians(k * 30 - 90)
        d += line((cx + math.cos(a) * r * 0.78, cy + math.sin(a) * r * 0.78), (cx + math.cos(a) * r * 0.9, cy + math.sin(a) * r * 0.9), INK, 1.6 if k % 3 == 0 else 1.0)
    d += line((cx, cy), (cx + r * 0.1, cy - r * 0.5), INK, 2.2) + line((cx, cy), (cx + r * 0.52, cy + r * 0.12), INK, 1.8) + circle(cx, cy, 1.8, CORAL, INK, 1)
    return d


# ---- backdrop: room shell, floor ---------------------------------------------------------------------------------------------

def edge_s(R, side):
    """Depth scale at which a side wall reaches the authored canvas edge (X0 or X1, beyond the frame)."""
    return abs((X0 if side < 0 else X1) - R.vx) / R.half


def floor_edge_y(R):
    """Screen y where the floor meets the side walls at the canvas edge."""
    return R.vy + (R.fy1 - R.vy) * ((R.vx - X0) / R.half)


def floor_clip_poly(R):
    ye = floor_edge_y(R)
    return [(X0, ye), (R.fx0, R.fy1), (R.fx1, R.fy1), (X1, ye), (X1, H), (X0, H)]


def wall_band(R, side, u0, u1, s0=1.0, s1=None):
    s1 = edge_s(R, side) if s1 is None else s1
    return [R.wall(side, s0, u0), R.wall(side, s1, u0), R.wall(side, s1, u1), R.wall(side, s0, u1)]


def room_shell(R, wall=MINT, dado=LILAC, uidp="", ceil_tile=True, floor=(FLOOR_A, FLOOR_B), floor_seam=SEAM, extend=40, floor_fn=None,
               sky=None, ceil=("#b9c6da", "#e8f0f4"), dado_h=74, side_wall=None, ao=0.13, front_dark=0.2, skirting=None):
    """Ceiling, side walls with dado and skirting, far wall and the floor for room R, drawn over the whole authored canvas (BACK_BOX,
    wider than the frame). Shading: the side walls darken towards the camera, soft ambient occlusion in the corners, along the
    ceiling line and where the walls meet the floor, and the floor darkens towards the front edge so the crowd's feet sit on it.
    Returns (defs, svg)."""
    defs = ""
    d = ""
    vx, vy = R.vx, R.vy
    sw_ = side_wall or wall
    skirt = skirting or darken(dado, 0.22)
    defs += lin_grad(uidp + "ceil", [(0, ceil[0]), (1, ceil[1])], 0, 0, 0, 1)
    defs += lin_grad(uidp + "fw", [(0, lighten(wall, 0.16)), (0.7, wall), (1, darken(wall, 0.05))], 0, 0, 0, 1)
    defs += lin_grad(uidp + "lw", [(0, darken(sw_, 0.24)), (0.55, darken(sw_, 0.1)), (1, darken(sw_, 0.03))], 0, 0, 1, 0)
    defs += lin_grad(uidp + "rw", [(0, darken(sw_, 0.03)), (0.45, darken(sw_, 0.1)), (1, darken(sw_, 0.24))], 0, 0, 1, 0)
    defs += lin_grad(uidp + "fl", [(0, darken(floor[0], 0.12)), (1, floor[0])], 0, 0, 0, 1)
    defs += lin_grad(uidp + "fd", [(0, INK, 0.0), (1, INK, front_dark)], 0, 0, 0, 1)
    yt = Y0 - 6
    d += rect(X0, Y0, X1 - X0, H - Y0, mix(wall, "#ffffff", 0.1))
    # ceiling (one quad from the far wall's top edge to beyond the canvas top)
    xl = vx - (vx - R.fx0) * (vy - yt) / (vy - R.fy0)
    xr = vx + (R.fx1 - vx) * (vy - yt) / (vy - R.fy0)
    d += poly([(xl, yt), (xr, yt), (R.fx1, R.fy0), (R.fx0, R.fy0)], f"url(#{uidp}ceil)")
    if ceil_tile:
        for k in range(-8, 9):
            xf = vx + k * 55.0
            if R.fx0 <= xf <= R.fx1:
                xt = vx + (xf - vx) * (yt - vy) / (R.fy0 - vy)
                d += line((xf, R.fy0), (xt, yt), darken(ceil[1], 0.3), 1.3, 0.55)
        s = 1.0
        while s < 4:
            yy = vy + (R.fy0 - vy) * s
            if yy < yt:
                break
            d += line((vx - R.half * s, yy), (vx + R.half * s, yy), darken(ceil[1], 0.3), 1.3, 0.55)
            s *= 1.16
    # far wall
    d += rect(R.fx0, R.fy0, R.fx1 - R.fx0, R.fy1 - R.fy0, f"url(#{uidp}fw)")
    if dado_h:
        d += rect(R.fx0, R.fy1 - dado_h, R.fx1 - R.fx0, dado_h, dado, None)
        for x in range(int(R.fx0) + 14, int(R.fx1), 28):
            d += line((x, R.fy1 - dado_h + 4), (x, R.fy1), darken(dado, 0.12), 1.2, 0.55)
        d += rect(R.fx0, R.fy1 - dado_h, R.fx1 - R.fx0, 10, INK, None, op=0.06)
        d += rect(R.fx0, R.fy1 - dado_h - 5, R.fx1 - R.fx0, 6, lighten(dado, 0.45), OUT, 2)  # dado rail
    d += rect(R.fx0, R.fy1 - 9, R.fx1 - R.fx0, 9, skirt, OUT, 2)  # skirting
    d += poly([(R.fx0, R.fy0), (R.fx1, R.fy0), (R.fx1, R.fy0 + 10), (R.fx0, R.fy0 + 10)], INK, None, op=ao * 0.55)
    # side walls
    for side, gid in ((-1, "lw"), (1, "rw")):
        x_edge = X0 if side < 0 else X1
        s_e = edge_s(R, side)
        top_e = R.wall(side, s_e, R.height)
        bot_e = R.wall(side, s_e, 0)
        far_top, far_bot = R.wall(side, 1, R.height), R.wall(side, 1, 0)
        d += poly([(x_edge, top_e[1] - extend), far_top, far_bot, (x_edge, bot_e[1])], f"url(#{uidp}{gid})")
        if dado_h:
            d += poly(wall_band(R, side, 8, dado_h), darken(dado, 0.04), None)
            d += poly(wall_band(R, side, dado_h - 10, dado_h), INK, None, op=0.06)
            for k in range(1, 12):  # vertical seams of the dado boards
                s = 1 + (s_e - 1) * (k / 12.0) ** 1.3
                d += line(R.wall(side, s, 8), R.wall(side, s, dado_h), darken(dado, 0.14), 1.2, 0.5)
            d += poly(wall_band(R, side, dado_h, dado_h + 5), lighten(dado, 0.45), OUT, 2)
        d += poly(wall_band(R, side, 0, 8), skirt, OUT, 2)
        # ambient occlusion: the inside corner with the far wall, and the line under the ceiling
        for (s1, op) in ((1.12, ao * 0.35), (1.05, ao * 0.45), (1.018, ao * 0.6)):
            d += poly([R.wall(side, 1, 0), R.wall(side, s1, 0), R.wall(side, s1, R.height), R.wall(side, 1, R.height)], INK, None, op=op)
        d += poly(wall_band(R, side, R.height - 14, R.height), INK, None, op=ao * 0.5)
        fx = R.fx0 if side < 0 else R.fx1 - 8
        d += rect(fx, R.fy0, 8, R.height, INK, None, op=ao * 0.4)
    # floor, clipped to the floor polygon so it never paints over the walls
    fp = floor_clip_poly(R)
    defs += clip(uidp + "flc", f'<polygon points="{" ".join(f"{f(x)},{f(y)}" for x, y in fp)}"/>')
    fl = poly(fp, f"url(#{uidp}fl)")
    fl += floor_checker(R, floor, floor_seam) if floor_fn is None else floor_fn(R)
    # floor shading: occlusion along the wall bases and the far wall, and a darker front edge under the desk lip
    for side in (-1, 1):
        x_in = R.fx0 if side < 0 else R.fx1
        for (wd, op) in ((60, ao * 0.4), (26, ao * 0.6), (9, ao * 0.8)):
            xb = x_in - side * wd
            fl += poly([R.floor_pt(x_in, 1.0), R.floor_pt(xb, 1.0), R.floor_pt(xb, 8.0), R.floor_pt(x_in, 8.0)], INK, None, op=op)
    for (ds, op) in ((0.12, ao * 0.4), (0.05, ao * 0.6), (0.018, ao * 0.8)):
        fl += poly([R.floor_pt(R.fx0, 1.0), R.floor_pt(R.fx1, 1.0), R.floor_pt(R.fx1, 1.0 + ds), R.floor_pt(R.fx0, 1.0 + ds)], INK, None, op=op)
    fl += rect(X0, 330, X1 - X0, H - 330, f"url(#{uidp}fd)")
    d += group(fl, f'clip-path="url(#{uidp}flc)"')
    # the wall/floor seam line
    for side in (-1, 1):
        a, b = R.wall(side, 1, 0), R.wall(side, edge_s(R, side), 0)
        d += line(a, b, OUT, 2.6, 0.9)
    d += line((R.fx0, R.fy1), (R.fx1, R.fy1), OUT, 2.2, 0.8)
    return defs, d


def floor_checker(R, cols, seam, ncols=10, dz=0.06):
    """Checkered vinyl in perspective: `ncols` columns across the far wall, rows equally spaced in depth (z = 1/scale). Each light
    tile carries a faint polish highlight; drawn over the floor gradient and clipped by room_shell."""
    d = ""
    step = (R.fx1 - R.fx0) / ncols
    rows = []
    z = 1.0
    while z > 0.15:
        s = 1.0 / z
        rows.append((s, R.floor_y(s)))
        z -= dz
    cols_x = [R.fx0 + step * i for i in range(-4 * ncols, 5 * ncols + 1)]
    for ri in range(len(rows) - 1):
        s0, y0 = rows[ri]
        s1, y1 = rows[ri + 1]
        for ci in range(len(cols_x) - 1):
            xa, xb = cols_x[ci], cols_x[ci + 1]
            q = [(R.vx + (xa - R.vx) * s0, y0), (R.vx + (xb - R.vx) * s0, y0), (R.vx + (xb - R.vx) * s1, y1), (R.vx + (xa - R.vx) * s1, y1)]
            if max(p[0] for p in q) < X0 - 20 or min(p[0] for p in q) > X1 + 20:
                continue
            if (ri + ci) % 2 == 0:
                d += poly(q, cols[1], None)
            else:
                d += poly([q[0], (q[0][0] * 0.7 + q[1][0] * 0.3, q[0][1]), (q[3][0] * 0.85 + q[2][0] * 0.15, q[3][1] - (q[3][1] - q[0][1]) * 0.35)],
                          "#ffffff", None, op=0.12)
    for s0, y0 in rows:
        d += line((X0 - 20, y0), (X1 + 20, y0), seam, 1.3, 0.6)
    for xa in cols_x:
        d += line((R.vx + (xa - R.vx) * 1.0, R.floor_y(1.0)), (R.vx + (xa - R.vx) * 7.0, R.floor_y(7.0)), seam, 1.3, 0.6)
    return d


def floor_reflection(R, xa, xb, s1=2.2, col="#ffffff", op=0.22, uid="rf"):
    """A soft vertical streak on a polished floor: the reflection of a bright window or door at the far wall between xa and xb.
    Returns (defs, svg)."""
    defs = lin_grad(uid, [(0, col, op), (1, col, 0.0)], 0, 0, 0, 1)
    q = [R.floor_pt(xa, 1.0), R.floor_pt(xb, 1.0), R.floor_pt(xb, s1), R.floor_pt(xa, s1)]
    return defs, poly(q, f"url(#{uid})", None)


MAIN_WALL, MAIN_DADO = "#a9dccd", "#b6a4e6"
MAIN_FLOOR, MAIN_SEAM = ("#b2d6c5", "#c4b9e4"), "#8fb4a5"


def troffer(R, xa, xb, s0, s1, glow=True):
    """A fluorescent ceiling panel (light fitting set in the ceiling tiles) between far-wall x xa..xb at depth scales s0..s1."""
    q = [R.ceil(xa, s0), R.ceil(xb, s0), R.ceil(xb, s1), R.ceil(xa, s1)]
    d = poly(q, "#dfe6ee", OUT, 1.8)
    inset = [R.ceil(xa + (xb - xa) * 0.06, s0 + (s1 - s0) * 0.12), R.ceil(xb - (xb - xa) * 0.06, s0 + (s1 - s0) * 0.12),
             R.ceil(xb - (xb - xa) * 0.06, s1 - (s1 - s0) * 0.12), R.ceil(xa + (xb - xa) * 0.06, s1 - (s1 - s0) * 0.12)]
    d += poly(inset, "#f4fffb" if glow else "#e8eef4", None)
    for k in (1, 2):  # the diffuser's grid
        xm = xa + (xb - xa) * k / 3
        d += line(R.ceil(xm, s0 + (s1 - s0) * 0.12), R.ceil(xm, s1 - (s1 - s0) * 0.12), "#c8d8e0", 1.2, 0.8)
    if glow:
        d += poly([inset[0], inset[1], (inset[1][0], inset[1][1] + 2), (inset[0][0], inset[0][1] + 2)], "#ffffff", None, op=0.8)
    return d


def curtain(x0, y0, x1, y1, col, side=1, folds=4, tie=True):
    """A gathered curtain panel hanging from (x0, y0) to (x1, y1), tied back towards `side`."""
    w = x1 - x0
    d = ""
    if tie:
        ty = y0 + (y1 - y0) * 0.58
        tx = x0 + w * (0.25 if side < 0 else 0.75)
        pts = [(x0, y0), (x1, y0), (tx + w * 0.16, ty), (x1 if side > 0 else tx + w * 0.4, y1), (x0 if side < 0 else tx - w * 0.4, y1), (tx - w * 0.16, ty)]
        d += poly(pts, col, OUT, 2.2)
        for k in range(1, folds):
            xa = x0 + w * k / folds
            d += path(f"M{f(xa)} {f(y0 + 2)} Q{f((xa + tx) / 2)} {f((y0 + ty) / 2)} {f(tx + (k - folds / 2) * 2.5)} {f(ty)}", None, darken(col, 0.14), 1.6, sop=0.9)
        d += rect(tx - w * 0.2, ty - 3, w * 0.4, 6, lighten(col, 0.3), OUT, 1.4, rx=3)
    else:
        d += rect(x0, y0, w, y1 - y0, col, OUT, 2.2)
    for k in range(5):  # a little printed pattern of dots
        d += circle(x0 + w * (0.2 + 0.15 * k), y0 + 10 + (k % 2) * 14, 1.6, "#ffffff", None, op=0.7)
    d += rect(x0 - 4, y0 - 4, w + 8, 5, "#e6dcfa", OUT, 1.6, rx=2)  # the rail
    return d


def radiator(x, yb, w, h=30):
    d = rect(x, yb - h, w, h, "#f4f2fb", OUT, 2.2, rx=3)
    n = max(int(w / 9), 3)
    for k in range(1, n):
        xx = x + w * k / n
        d += line((xx, yb - h + 4), (xx, yb - 4), "#c9c4dc", 2.4)
    d += rect(x + 2, yb - h + 2, w - 4, 4, "#ffffff", None, op=0.6, rx=2)
    d += ellipse(x + w / 2, yb + 1, w * 0.55, 3, INK, None, op=0.12)
    return d


def wall_poly_frame(side, s0, s1, u0, u1, fill, ol=2.6):
    return poly([R.wall(side, s0, u1), R.wall(side, s1, u1), R.wall(side, s1, u0), R.wall(side, s0, u0)], fill, OUT, ol)


def build_backdrop():
    defs, d = room_shell(R, wall=MAIN_WALL, dado=MAIN_DADO, floor=MAIN_FLOOR, floor_seam=MAIN_SEAM, ceil=("#9fb0c8", "#dfe9f0"))
    # ---- ceiling: fluorescent troffer panels between the spotlights' tracks ----
    for (s0, s1) in ((1.07, 1.2), (1.4, 1.6), (1.95, 2.3)):
        for (xa, xb) in ((372, 452), (600, 680), (828, 908)):
            d += troffer(R, xa, xb, s0, s1)
    # light falling from the panels onto the top of the far wall
    defs += lin_grad("wash", [(0, "#f2fffa", 0.55), (1, "#f2fffa", 0.0)], 0, 0, 0, 1)
    d += rect(R.fx0, R.fy0, R.fx1 - R.fx0, 60, "url(#wash)")
    # ---- far wall: door, windows with curtains and radiators, the TV, a shelf ----
    ddefs, dd = door(336, 146, 62, 116)
    defs += ddefs
    d += dd
    d += rect(404, 196, 6, 9, "#f4f2fb", OUT, 1.2, rx=1)  # light switch
    for k, (wx, uid) in enumerate(((414, "w1"), (790, "w2"))):
        wd, wdd = window(wx, 84, 76, 114, uid, mullions=(1, 1))
        defs += wd
        d += wdd
        cc = "#ffb8c8" if k == 0 else "#ffd98a"
        d += curtain(wx - 14, 74, wx + 8, 204, cc, -1) + curtain(wx + 68, 74, wx + 90, 204, cc, 1)
        d += radiator(wx + 4, 250, 68, 34)
    # the TV: a dark panel in a pale frame on a bracket (the runtime paints into led_screen)
    tx, ty, tw, th = 500, 76, 280, 70
    d += rect(tx - 12, ty - 9, tw + 24, th + 22, INK, None, op=0.12, rx=8)  # its shadow on the wall
    d += rect(tx - 9, ty - 9, tw + 18, th + 18, "#f3f1fb", OUT, 3.4, rx=7)
    d += rect(tx - 4, ty - 4, tw + 8, th + 8, "#2a2c44", OUT, 2, rx=4)
    d += rect(tx, ty, tw, th, "#10111e", None)
    d += rect(tx - 10, ty + th + 9, tw + 20, 9, MAIN_DADO, OUT, 2.4, rx=3)  # shelf/bracket under the TV
    d += circle(tx + tw - 12, ty + th + 4, 2.4, "#7affc0", OUT, 0.8)
    # shelf with a plant, a teapot, a jigsaw box and a stack of board games
    d += rect(556, 172, 168, 12, INK, None, op=0.1) + rect(556, 168, 168, 7, WOOD, OUT, 2.4, rx=2) + line((568, 175), (568, 188), OUT, 3) + line((712, 175), (712, 188), OUT, 3)
    d += plant(584, 168, 40, "#ff9a7a")
    d += poly([(646, 168), (650, 150), (676, 150), (680, 168)], "#fff4dc", OUT, 2) + path("M680 154 Q692 156 686 166", None, OUT, 3) + path("M680 154 Q692 156 686 166", None, "#fff4dc", 1.4) + circle(663, 147, 3, CORAL, OUT, 1.2)
    d += rect(694, 154, 14, 14, "#bfe6ff", OUT, 2, rx=2)
    for k, c in enumerate(("#ff8f8a", "#7fb6ff", "#ffd966")):
        d += rect(606 + k * 2, 160 - k * 6, 30 - k * 4, 6, c, OUT, 1.4, rx=1)
    # ---- left wall: two tall windows with curtains and radiators ----
    for (s0, s1, uid) in ((1.2, 1.5, "lw1"), (1.62, 1.9, "lw2")):
        q = [R.wall(-1, s0, 150), R.wall(-1, s1, 150), R.wall(-1, s1, 52), R.wall(-1, s0, 52)]
        frame = [R.wall(-1, s0 - 0.02, 156), R.wall(-1, s1 + 0.02, 156), R.wall(-1, s1 + 0.02, 46), R.wall(-1, s0 - 0.02, 46)]
        defs += lin_grad(uid, [(0, "#a8dcff"), (0.6, "#e2f5ff"), (1, "#f6ffee")], 0, 0, 0, 1)
        d += poly(frame, "#fbfbff", OUT, 3)
        d += poly(q, f"url(#{uid})", None)
        gq = [R.wall(-1, s0, 82), R.wall(-1, s1, 82), R.wall(-1, s1, 52), R.wall(-1, s0, 52)]
        d += poly(gq, "#8fd98a", None, op=0.95)
        sm = (s0 + s1) / 2
        tr = R.wall(-1, sm, 92)
        d += circle(tr[0] + 2, tr[1], 16 * sm * 0.5, "#5dbb7a", None, op=0.9) + circle(tr[0] + 14 * sm * 0.5, tr[1] + 4, 11 * sm * 0.5, "#6cc98a", None, op=0.9)
        d += poly([R.wall(-1, s0, 140), R.wall(-1, s1, 140), R.wall(-1, s1, 126), R.wall(-1, s0, 126)], "#ffffff", None, op=0.3)
        d += line(R.wall(-1, sm, 150), R.wall(-1, sm, 52), "#fbfbff", 4) + line(R.wall(-1, s0, 101), R.wall(-1, s1, 101), "#fbfbff", 4)
        d += line(R.wall(-1, sm, 150), R.wall(-1, sm, 52), OUT, 1.0)
        sill = [R.wall(-1, s0 - 0.03, 52), R.wall(-1, s1 + 0.03, 52), R.wall(-1, s1 + 0.03, 46), R.wall(-1, s0 - 0.03, 46)]
        d += poly(sill, "#f0eefb", OUT, 2)
        # curtains gathered at both sides of the window (thin slivers on the wall plane)
        for (a0, a1) in ((s0 - 0.06, s0 + 0.02), (s1 - 0.02, s1 + 0.06)):
            cq = [R.wall(-1, a0, 160), R.wall(-1, a1, 160), R.wall(-1, a1 + 0.01, 40), R.wall(-1, a0, 40)]
            d += poly(cq, "#ffb8c8", OUT, 2.2)
            for j in (0.33, 0.66):
                d += line(R.wall(-1, a0 + (a1 - a0) * j, 158), R.wall(-1, a0 + (a1 - a0) * j, 42), darken("#ffb8c8", 0.16), 1.6)
        d += poly(wall_band(R, -1, 160, 166, s0 - 0.08, s1 + 0.08), "#e6dcfa", OUT, 1.6)
        d += poly([R.wall(-1, s0 + 0.01, 38), R.wall(-1, s1 - 0.01, 38), R.wall(-1, s1 - 0.01, 12), R.wall(-1, s0 + 0.01, 12)], "#f4f2fb", OUT, 2.0)  # radiator
        for j in range(1, 9):
            ss = s0 + 0.01 + (s1 - s0 - 0.02) * j / 9
            d += line(R.wall(-1, ss, 34), R.wall(-1, ss, 16), "#c9c4dc", 2.0)
    # light from the left windows across the floor (a soft warm parallelogram; the additive `window_light` piece adds to it)
    defs += lin_grad("lwl", [(0, "#fff8e0", 0.32), (1, "#fff8e0", 0.0)], 0, 0, 1, 0)
    for (s0, s1) in ((1.2, 1.5), (1.62, 1.9)):
        a, b = R.wall(-1, s0, 0), R.wall(-1, s1, 0)
        d += poly([a, b, (b[0] + 260 * s1 * 0.5, b[1] + 6), (a[0] + 240 * s0 * 0.5, a[1] + 4)], "url(#lwl)", None)
    # ---- right wall: framed patient art and a pinboard ----
    arts = [((1.18, 1.32), (150, 112), "#ffd0e0", "heart"), ((1.38, 1.55), (146, 100), "#cfe9ff", "sun"), ((1.62, 1.82), (150, 108), "#fff0b0", "house"),
            ((1.98, 2.2), (156, 96), "#d8f4e4", "flower")]
    for (s0, s1), (u1, u0), col, kind in arts:
        d += poly([R.wall(1, s0 + 0.01, u1 - 4), R.wall(1, s1 + 0.01, u1 - 4), R.wall(1, s1 + 0.01, u0 - 4), R.wall(1, s0 + 0.01, u0 - 4)], INK, None, op=0.12)
        d += wall_poly_frame(1, s0, s1, u0, u1, "#fbfbff")
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
        elif kind == "house":
            d += poly([(cx - 8 * sc, cy + 6 * sc), (cx - 8 * sc, cy - 3 * sc), (cx, cy - 10 * sc), (cx + 8 * sc, cy - 3 * sc), (cx + 8 * sc, cy + 6 * sc)], "#ff8f8a", OUT, 1.4)
        else:
            for k in range(6):
                a = k * math.tau / 6
                d += circle(cx + math.cos(a) * 6 * sc, cy + math.sin(a) * 6 * sc - 4 * sc, 4 * sc, "#ff9ac0", OUT, 1.0)
            d += circle(cx, cy - 4 * sc, 3.6 * sc, BUTTER, OUT, 1.0) + line((cx, cy + 2 * sc), (cx, cy + 14 * sc), "#5dbb7a", 2.4)
    # ---- floor: the windows and the door mirrored softly in the polished vinyl ----
    for (xa, xb, uid, op) in ((414, 490, "rf1", 0.3), (790, 866, "rf2", 0.3), (336, 398, "rf3", 0.16), (500, 780, "rf4", 0.08)):
        rd, rr = floor_reflection(R, xa, xb, 1.9, "#ffffff", op, uid)
        defs += rd
        d += rr
    return defs, d


# ---- furniture baked into the backdrop (the crowd stands in front of it) ---------------------------------------------------

def side_table(x, yb, top="#f0c88e", w=44):
    d = ellipse(x, yb + 2, w * 0.6, 4, INK, None, op=0.2)
    d += rect(x - 3, yb - 34, 6, 34, WOOD_D, OUT, 1.8)
    d += ellipse(x, yb - 36, w / 2, 6, top, OUT, 2.2) + rect(x - w / 2, yb - 36, w, 4, WOOD, OUT, 1.6)
    return d


def main_furniture():
    d = ""
    d += armchair(104, 372, 112, "#ffd966", "#e8b23a", blanket="#ff8f8a")
    d += plant(40, 350, 96, "#7fb6ff", "rubber")
    d += armchair(1176, 366, 108, "#5fc9bb", "#3a9a8c", blanket="#c9b8f0")
    d += plant(1244, 346, 90, "#ffb07a", "fern")
    # a side table with a jigsaw and a mug by the yellow chair
    d += side_table(-6, 352)
    d += rect(-24, 314, 30, 4, "#7fb6ff", OUT, 1.2) + rect(-2, 304, 9, 10, "#fff4dc", OUT, 1.4, rx=2)
    # a floor lamp beside the teal armchair, lit
    d += ellipse(1114, 351, 12, 3, INK, None, op=0.2) + line((1114, 350), (1114, 244), OUT, 6) + line((1114, 350), (1114, 244), "#a8a2c8", 3)
    d += ellipse(1114, 246, 34, 12, "#fff0b8", None, op=0.28)
    d += poly([(1094, 244), (1134, 244), (1126, 216), (1102, 216)], "#fff2c0", OUT, 2.4) + ellipse(1114, 246, 20, 3.4, "#ffe8a0", None, op=0.6)
    d += line((1100, 238), (1106, 220), "#ffffff", 1.6, 0.6)
    return d


def build_main_backdrop():
    defs, d = build_backdrop()
    d += build_rug()  # the rug under the dance circle matches circle_centre / circle_radii
    d += main_furniture()
    return defs, d


def build_rug():
    cx, cy, rx, ry = 640, 372, 262, 52
    cols = ["#eea6bc", "#fbeed4", "#9fd8c8", "#fbeed4", "#b9a6ec", "#fbeed4", "#ffcf8a", "#fbeed4", "#9fd8c8"]
    d = ellipse(cx, cy + 5, rx + 8, ry + 6, INK, None, op=0.18)
    d += rug_ellipse(cx, cy, rx, ry, cols)
    for k in range(48):  # fringe ticks
        a = k * math.tau / 48
        d += line((cx + math.cos(a) * rx, cy + math.sin(a) * ry), (cx + math.cos(a) * (rx + 7), cy + math.sin(a) * (ry + 2.4)), "#fbeed4", 2.0)
    for k in range(18):  # woven stars
        a = k * math.tau / 18 + 0.1
        d += paper_star(cx + math.cos(a) * rx * 0.72, cy + math.sin(a) * ry * 0.72, 4.2, "#ffffff", 0.0)
    d += ellipse(cx, cy - ry * 0.3, rx * 0.6, ry * 0.3, "#ffffff", None, op=0.1)  # a little sheen where the light lands
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
    write_svg("backdrop.svg", BACK_BOX, d, defs)
    layers.append(back_layer("source/backdrop.svg"))
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
