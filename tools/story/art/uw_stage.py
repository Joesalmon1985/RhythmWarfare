"""The Underworld chapter's room: hell's nightclub seen from the DJ's eye line (same 1280 x 720 design space and perspective
as Night One: vanishing point (640, 130), far wall x 270..1010, y 52..262).

A cavern arena of cracked obsidian and lava, a fanged hellmouth portal at the back, a skull throne stage, fire pits, bone and
chains, a demonic desk. Plain SVG (gradients, translucent layers) plus Pillow PNGs for soft light (swirls, embers, washes).
"""
from __future__ import annotations

import colorsys
import math
import os
import random
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from . import lib, sprites as png_sprites, stage as S, uw_chars as UC
from .lib import (OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, pivot_in, poly, rad_grad, rect,
                  write_svg)

W, H = S.W, S.H
VPX, VPY = S.VPX, S.VPY
FX0, FX1, FY0, FY1 = S.FX0, S.FX1, S.FY0, S.FY1
floor_x, lwall_y, rwall_y = S.floor_x, S.lwall_y, S.rwall_y

LAVA, EMBER, GOLD, MAG, VIO, GREEN = "#ff5a1a", "#ffb02e", "#ffd23f", "#ff2f9d", "#9a3cff", "#4fff9a"
BONE = "#efe2c0"
ROCK0, ROCK1, ROCK2, ROCK3 = "#0b0310", "#1a0a16", "#2d1220", "#46202c"
FLOOR_ROWS = S.FLOOR_ROWS


# ---- shared bits ---------------------------------------------------------------------------------------------------------

def neon(p1, p2, color, w=2.0, glow=1.0):
    return S.neon(p1, p2, color, w, glow)


def neon_path(d, color, w=2.0, glow=1.0):
    return S.neon_path(d, color, w, glow)


def jag(p0, p1, n, amp, rng, taper=True):
    pts = [p0]
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln
    for i in range(1, n):
        t = i / n
        a = amp * (1 if not taper else math.sin(t * math.pi) * 0.7 + 0.3) * rng.uniform(-1, 1)
        pts.append((p0[0] + dx * t + nx * a, p0[1] + dy * t + ny * a))
    pts.append(p1)
    return pts


def pline(points):
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in points)


def vein(points, color=LAVA, w=1.6, glow=1.0):
    return neon_path(pline(points), color, w, glow)


def skull(cx, cy, r, bone=BONE, eye="#ff7a1a", ol=2.2, jaw=True):
    out = ellipse(cx, cy, r, r * 0.92, bone, OUT, ol)
    if jaw:
        out += rect(cx - r * 0.55, cy + r * 0.55, r * 1.1, r * 0.62, bone, OUT, ol * 0.8, rx=r * 0.18)
        for k in (-1, 0, 1):
            out += line((cx + k * r * 0.28, cy + r * 0.62), (cx + k * r * 0.28, cy + r * 1.12), OUT, 1.0, 0.8)
    out += ellipse(cx - r * 0.38, cy - r * 0.05, r * 0.27, r * 0.3, "#1a0818", OUT, 1)
    out += ellipse(cx + r * 0.38, cy - r * 0.05, r * 0.27, r * 0.3, "#1a0818", OUT, 1)
    out += circle(cx - r * 0.38, cy - r * 0.03, r * 0.11, eye) + circle(cx + r * 0.38, cy - r * 0.03, r * 0.11, eye)
    out += poly([(cx, cy + r * 0.12), (cx - r * 0.11, cy + r * 0.38), (cx + r * 0.11, cy + r * 0.38)], "#1a0818", None)
    return out


def chain(p0, p1, link=9.0, color="#7a6a76", w=2.4):
    """A hanging chain: alternating front and side-on links."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = math.hypot(dx, dy)
    n = max(2, int(ln / (link * 0.78)))
    ang = math.degrees(math.atan2(dy, dx)) - 90
    out = ""
    for i in range(n):
        t = (i + 0.5) / n
        x, y = p0[0] + dx * t, p0[1] + dy * t
        if i % 2 == 0:
            out += f'<g transform="translate({f(x)} {f(y)}) rotate({f(ang)})">{ellipse(0, 0, link * 0.34, link * 0.62, None, OUT, w + 2.4)}{ellipse(0, 0, link * 0.34, link * 0.62, None, color, w)}{line((-link * 0.18, -link * 0.3), (-link * 0.18, link * 0.1), "#ffd0a0", 1.0, 0.7)}</g>'
        else:
            out += f'<g transform="translate({f(x)} {f(y)}) rotate({f(ang)})">{rect(-link * 0.12, -link * 0.5, link * 0.24, link * 1.0, color, OUT, 1.6, rx=link * 0.12)}</g>'
    return out


def stalactites(y_base, x0, x1, rng, lmin, lmax, wmin, wmax, fill, glow=True, ol=2.4):
    out = ""
    x = x0
    while x < x1:
        w = rng.uniform(wmin, wmax)
        ln = rng.uniform(lmin, lmax)
        tip = (x + w / 2 + rng.uniform(-3, 3), y_base + ln)
        out += poly([(x, y_base - 2), tip, (x + w, y_base - 2)], fill, OUT, ol)
        if glow:
            out += line((x + w * 0.25, y_base + 2), (tip[0] - 0.5, tip[1] - ln * 0.12), "#ff7a2e", 1.3, 0.55)
        out += line((x + w * 0.78, y_base + 2), (tip[0] + 0.4, tip[1] - ln * 0.3), "#ffffff", 1.0, 0.1)
        x += w * rng.uniform(0.7, 1.0)
    return out


# ---- backdrop --------------------------------------------------------------------------------------------------------------

def build_backdrop():
    rng = random.Random(66)
    d = ""
    defs = ""
    defs += lin_grad("bg", [(0, "#0a0310"), (0.5, "#1a0814"), (1, "#0d0410")], 0, 0, 0, 1)
    d += rect(0, 0, W, H, "url(#bg)")
    # ---- ceiling: rock with a glowing seam, and the stalactite fringe
    defs += lin_grad("ceil", [(0, "#07020c"), (1, "#2a0f1c")], 0, 0, 0, 1)
    d += poly([(0, -6), (W, -6), (FX1, FY0), (FX0, FY0)], "url(#ceil)")
    for k in range(-5, 6):
        xf = VPX + k * 70.0
        if FX0 <= xf <= FX1:
            xt = VPX + (xf - VPX) * (-6 - VPY) / (FY0 - VPY)
            d += line((xf, FY0), (xt, -6), "#3a1426", 1.8, 0.7)
    # ---- far wall: cracked rock with a lava glow from below
    defs += lin_grad("fw", [(0, "#2a0f1c"), (0.55, "#1a0a16"), (1, "#3a1218")], 0, 0, 0, 1)
    d += rect(FX0, FY0, FX1 - FX0, FY1 - FY0, "url(#fw)")
    for y in range(66, 262, 24):  # sedimentary bands
        pts = [(FX0 + i * 20, y + math.sin(i * 0.7 + y) * 3) for i in range(int((FX1 - FX0) / 20) + 1)]
        d += path(pline(pts), None, "#08020a", 3.0, sop=0.32)
        d += path(pline([(x, yy + 3) for x, yy in pts]), None, "#5a2a38", 1.2, sop=0.22)
    for k in range(34):  # rock block seams
        x = rng.uniform(FX0 + 6, FX1 - 6)
        y = rng.uniform(FY0 + 6, FY1 - 40)
        d += path(pline(jag((x, y), (x + rng.uniform(-18, 18), y + rng.uniform(14, 38)), 3, 6, rng)), None, "#08020a", 1.6, sop=0.5)
    defs += lin_grad("fwglow", [(0, "#ff4a1c", 0.0), (0.55, "#ff4a1c", 0.12), (1, "#ff6a1c", 0.55)], 0, 0, 0, 1)
    d += rect(FX0, 100, FX1 - FX0, FY1 - 100, "url(#fwglow)")
    for k in range(7):  # lava veins on the far wall
        x = rng.uniform(FX0 + 10, FX1 - 10)
        y1 = FY1 - 2
        pts = jag((x, y1), (x + rng.uniform(-40, 40), y1 - rng.uniform(40, 110)), 6, 9, rng)
        d += vein(pts, LAVA, 1.5, 0.9)
    # ---- side walls
    defs += lin_grad("lw", [(0, "#07020c"), (1, "#3a1626")], 0, 0, 1, 0)
    defs += lin_grad("rw", [(0, "#3a1626"), (1, "#07020c")], 0, 0, 1, 0)
    lwall = [(0, lwall_y(FY0, 0)), (FX0, FY0), (FX0, FY1), (0, lwall_y(FY1, 0))]
    rwall = [(W, rwall_y(FY0, W)), (FX1, FY0), (FX1, FY1), (W, rwall_y(FY1, W))]
    d += poly(lwall, "url(#lw)") + poly(rwall, "url(#rw)")
    defs += clip("lwc", poly(lwall)) + clip("rwc", poly(rwall))
    for side, cid in ((-1, "lwc"), (1, "rwc")):
        inner = ""
        for k in range(1, 9):  # rock strata sloping with the perspective
            yy = FY0 + (FY1 - FY0) * k / 9.0
            x_edge = 0 if side < 0 else W
            x_in = FX0 if side < 0 else FX1
            y_edge = lwall_y(yy, 0) if side < 0 else rwall_y(yy, W)
            inner += line((x_edge, y_edge), (x_in, yy), "#08020a", 2.6, 0.35)
        for k in range(12):  # broken rock seams
            x = rng.uniform(0, FX0) if side < 0 else rng.uniform(FX1, W)
            y = (lwall_y(FY0, x) if side < 0 else rwall_y(FY0, x)) + rng.uniform(10, 150)
            inner += path(pline(jag((x, y), (x + rng.uniform(-10, 10), y + rng.uniform(20, 60)), 4, 6, rng)), None, "#08020a", 1.8, sop=0.55)
        for k in range(5):  # lava veins running down the rock
            x = rng.uniform(20, FX0 - 10) if side < 0 else rng.uniform(FX1 + 10, W - 20)
            y0 = (lwall_y(FY0, x) if side < 0 else rwall_y(FY0, x)) + rng.uniform(20, 80)
            y1 = (lwall_y(FY1, x) if side < 0 else rwall_y(FY1, x)) - 2
            inner += vein(jag((x, y0), (x + rng.uniform(-14, 14), y1), 7, 8, rng), LAVA if k % 2 else EMBER, 1.3, 0.8)
        d += group(inner, f'clip-path="url(#{cid})"')
    # lava falls pouring down the near edges of the side walls into glowing pools
    for xf in (46, W - 46):
        side = -1 if xf < 640 else 1
        ytop = (lwall_y(FY0, xf) if side < 0 else rwall_y(FY0, xf)) - 2
        ybot = (lwall_y(FY1, xf) if side < 0 else rwall_y(FY1, xf)) + 4
        defs += lin_grad(f"fall{side}", [(0, "#ffe08a"), (0.5, "#ff7a1a"), (1, "#e02a10")], 0, 0, 0, 1)
        for wd, op in ((46, 0.1), (34, 0.16), (24, 0.25)):
            d += rect(xf - wd / 2, ytop, wd, ybot - ytop, LAVA, None, op=op)
        d += rect(xf - 8, ytop, 16, ybot - ytop, f"url(#fall{side})", OUT, 2.2, rx=3)
        for k in range(6):
            yy = ytop + 12 + k * (ybot - ytop - 20) / 6
            d += line((xf - 5, yy), (xf + 3, yy + 9), "#fff2a0", 1.8, 0.8)
        d += ellipse(xf, ybot + 6, 38, 8, LAVA, None, op=0.22) + ellipse(xf, ybot + 6, 26, 5.5, "#ff8a2a", None, op=0.55) + ellipse(xf, ybot + 6, 14, 3.2, "#ffe08a", None, op=0.8)
    # ---- bone columns (stacked vertebrae) at the corners of the far wall
    for xc in (FX0 - 2, FX1 + 2):
        yb = FY1 + 6
        k = 0
        y = FY0 - 6
        while y < yb:
            hgt = 15
            wv = 21 - (k % 2) * 3
            d += rect(xc - wv / 2, y, wv, hgt, BONE, OUT, 2.4, rx=5)
            d += line((xc - wv / 2 + 3, y + 3), (xc - wv / 2 + 3, y + hgt - 3), "#ffffff", 1.4, 0.55)
            d += rect(xc + wv / 2 - 6, y + 1, 5, hgt - 2, "#150a33", None, op=0.22)
            y += hgt + 1
            k += 1
        d += circle(xc, FY0 - 6, 11, BONE, OUT, 2.4) + circle(xc - 3, FY0 - 9, 3, "#ffffff", None, op=0.6)
    # ---- the hellmouth: a fanged gate rising from the floor at the back centre
    pcx, pcy, pr = 640, 178, 76
    defs += clip("mouthclip", rect(FX0, FY0, FX1 - FX0, FY1 - FY0))
    defs += rad_grad("mouthglow", [(0, "#ff5a1a", 0.45), (0.6, "#ff2a1a", 0.18), (1, "#ff2a1a", 0.0)], 0.5, 0.5, 0.5)
    defs += rad_grad("mouthin", [(0, "#0a0108"), (0.7, "#2a0610"), (1, "#7a1010")], 0.5, 0.5, 0.5)
    m = ""
    m += circle(pcx, pcy, 168, "url(#mouthglow)")
    for k in range(30):  # jagged cavern rock around the maw
        a = k * math.tau / 30
        r1 = pr + 30
        r2 = r1 + rng.uniform(10, 26)
        m += poly([(pcx + math.cos(a - 0.11) * r1, pcy + math.sin(a - 0.11) * r1), (pcx + math.cos(a) * r2, pcy + math.sin(a) * r2), (pcx + math.cos(a + 0.11) * r1, pcy + math.sin(a + 0.11) * r1)], "#2d1220", OUT, 2)
    m += circle(pcx, pcy, pr + 34, "#1a0810", OUT, 3.4)
    m += circle(pcx, pcy, pr + 30, None, LAVA, 5, sop=0.16)
    m += circle(pcx, pcy, pr + 16, "#6a1220", OUT, 3.4)  # gums
    m += circle(pcx, pcy, pr + 12, None, "#ff6a4a", 1.6, sop=0.55)
    m += circle(pcx, pcy, pr + 2, "#0a0108", OUT, 3)
    m += circle(pcx, pcy, pr - 3, "url(#mouthin)", None)
    for row, (a0, a1, cnt) in enumerate(((-168, -12, 9), (12, 168, 9))):  # fangs: a top and a bottom row with the corners of the mouth open
        for k in range(cnt):
            a = math.radians(a0 + (a1 - a0) * (k + 0.5) / cnt)
            big = (k % 2 == 0) != (row == 1)
            mid = 1.0 - abs(k - (cnt - 1) / 2) / ((cnt - 1) / 2) * 0.35
            r0 = pr + 10
            r1 = pr - (30 if big else 17) * mid
            hw = (0.12 if big else 0.09)
            p0 = (pcx + math.cos(a - hw) * r0, pcy + math.sin(a - hw) * r0)
            p1 = (pcx + math.cos(a + hw) * r0, pcy + math.sin(a + hw) * r0)
            tip = (pcx + math.cos(a) * r1, pcy + math.sin(a) * r1)
            m += poly([p0, tip, p1], BONE, OUT, 2.4)
            mid_pt = (pcx + math.cos(a) * (r0 * 0.7 + r1 * 0.3), pcy + math.sin(a) * (r0 * 0.7 + r1 * 0.3))
            m += line(mid_pt, tip, "#ffffff", 1.2, 0.5)
            m += poly([p1, tip, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)], "#150a33", None, op=0.16)
    d += group(m, 'clip-path="url(#mouthclip)"')
    # ---- the marquee (LED screen) hung by chains over the hellmouth
    lx, ly, lw_, lh = 400, 56, 480, 44
    for cx_ in (lx + 14, lx + lw_ - 14, lx + 150, lx + lw_ - 150):
        d += chain((cx_, -6), (cx_, ly - 10), 9)
    d += rect(lx - 12, ly - 12, lw_ + 24, lh + 24, "#3a1a24", OUT, 3.6, rx=8)
    d += rect(lx - 7, ly - 7, lw_ + 14, lh + 14, "#12060c", OUT, 2, rx=5)
    d += rect(lx, ly, lw_, lh, "#06020a", None)
    d += neon((lx - 12, ly - 12), (lx + lw_ + 12, ly - 12), EMBER, 1.2, 0.9)
    d += neon((lx - 12, ly + lh + 12), (lx + lw_ + 12, ly + lh + 12), MAG, 1.2, 0.9)
    for cx_, cy_ in ((lx - 6, ly - 6), (lx + lw_ + 6, ly - 6), (lx - 6, ly + lh + 6), (lx + lw_ + 6, ly + lh + 6)):
        d += skull(cx_, cy_, 6.6, BONE, "#ff7a1a", 1.6, jaw=False)
    d += poly([(lx + lw_ / 2 - 16, ly - 12), (lx + lw_ / 2, ly - 32), (lx + lw_ / 2 + 16, ly - 12)], "#2d1220", OUT, 2.4)
    d += skull(lx + lw_ / 2, ly - 20, 9, BONE, "#ff7a1a", 1.8, jaw=False)
    # ---- the gate (doorway): iron-bound doors in a horned stone arch, closed, with a glowing seam
    dx, dy, dw, dh = 284, 138, 70, 124
    d += path(f"M{dx - 10} {dy + dh} L{dx - 10} {dy + 14} Q{dx - 10} {dy - 12} {dx + dw / 2} {dy - 14} Q{dx + dw + 10} {dy - 12} {dx + dw + 10} {dy + 14} L{dx + dw + 10} {dy + dh} Z", "#46202c", OUT, 3.4)
    d += path(f"M{dx - 3} {dy + dh} L{dx - 3} {dy + 10} Q{dx - 3} {dy - 6} {dx + dw / 2} {dy - 7} Q{dx + dw + 3} {dy - 6} {dx + dw + 3} {dy + 10} L{dx + dw + 3} {dy + dh} Z", "#0a0108", None)
    defs += lin_grad("gl", [(0, "#4a2630"), (1, "#1c0c14")], 0, 0, 0, 1)
    for xs in (dx, dx + dw / 2 + 1.5):
        d += rect(xs, dy + 2, dw / 2 - 1.5, dh - 2, "url(#gl)", OUT, 2.2)
        d += line((xs + 8, dy + 12), (xs + 8, dy + dh - 4), "#08020a", 1.6, 0.6)
        d += rect(xs, dy + 28, dw / 2 - 1.5, 7, "#2a1820", OUT, 1.6) + rect(xs, dy + 84, dw / 2 - 1.5, 7, "#2a1820", OUT, 1.6)
        for rx_ in (xs + 5, xs + dw / 2 - 7):
            d += circle(rx_, dy + 31.5, 1.5, "#9a8a96", OUT, 0.8) + circle(rx_, dy + 87.5, 1.5, "#9a8a96", OUT, 0.8)
    d += rect(dx + dw / 2 - 1.3, dy + 2, 2.6, dh - 2, "#ff3a1a", None, op=0.95) + rect(dx + dw / 2 - 4.5, dy + 2, 9, dh - 2, "#ff3a1a", None, op=0.18)
    d += skull(dx + dw / 2, dy + dh * 0.5, 7.0, BONE, "#ff7a1a", 1.6, jaw=False)
    d += poly([(dx - 12, dy + 12), (dx - 26, dy - 18), (dx - 4, dy)], BONE, OUT, 2.2) + poly([(dx + dw + 12, dy + 12), (dx + dw + 26, dy - 18), (dx + dw + 4, dy)], BONE, OUT, 2.2)
    d += skull(dx + dw / 2, dy - 16, 8.0, BONE, "#ff7a1a", 1.8, jaw=False)
    d += neon((dx - 3, dy + dh - 3), (dx + dw + 3, dy + dh - 3), LAVA, 1.4, 0.9)
    # ---- the bar on the far wall's right: bone shelves, glowing potions, a skull on the counter
    bx0, bx1 = 858, 1000
    d += rect(bx0, 114, bx1 - bx0, 100, "#08020a", OUT, 2.4, rx=2)
    defs += lin_grad("shelfglow", [(0, "#ff5a1a", 0.34), (1, "#9a3cff", 0.1)], 0, 0, 0, 1)
    d += rect(bx0 + 2, 116, bx1 - bx0 - 4, 96, "url(#shelfglow)")
    cols = [LAVA, GREEN, GOLD, VIO, MAG, "#ff7a59"]
    for row, sy in enumerate((148, 190)):
        d += rect(bx0 - 3, sy, bx1 - bx0 + 6, 5, "#d8c8a0", OUT, 1.8)
        x = bx0 + 6
        while x < bx1 - 10:
            c = cols[rng.randrange(len(cols))]
            bh = rng.choice((16, 20, 24, 18))
            bw = rng.choice((6, 7, 8))
            if rng.random() < 0.18:
                d += skull(x + 5, sy - 8, 6, BONE, c, 1.2, jaw=False)
                x += 14
                continue
            d += rect(x, sy - bh, bw, bh, c, OUT, 1.4, rx=2, op=0.92)
            d += rect(x + bw * 0.25, sy - bh - 5, bw * 0.5, 5, c, OUT, 1.2, op=0.9)
            d += line((x + 1.8, sy - bh + 3), (x + 1.8, sy - 4), "#ffffff", 1.2, 0.45)
            x += bw + rng.choice((3, 5, 7))
    d += rect(bx0 - 6, 204, bx1 - bx0 + 12, 58, "#2d1220", OUT, 3)
    d += rect(bx0 - 6, 204, bx1 - bx0 + 12, 7, "#d8c8a0", OUT, 2.4)
    d += rect(bx0 + 6, 220, bx1 - bx0 - 12, 34, "#08020a", None, op=0.55)
    for k in range(6):  # rib bones across the counter front
        xk = bx0 + 12 + k * 22
        d += path(f"M{xk} 218 Q{xk + 7} 236 {xk} 254", None, OUT, 5.4) + path(f"M{xk} 218 Q{xk + 7} 236 {xk} 254", None, BONE, 3)
    d += neon((bx0, 258), (bx1, 258), LAVA, 1.6, 0.9)
    d += skull(bx0 + 20, 196, 0, BONE, "#ff7a1a", 1.2, jaw=False) if False else ""
    for sx in (878, 930, 982):
        d += ellipse(sx, 270, 13, 4.2, "#46202c", OUT, 2) + rect(sx - 2, 270, 4, 16, "#d8c8a0", OUT, 1.4)
        d += ellipse(sx, 267, 11, 3.4, mix(LAVA, "#150a33", 0.35), OUT, 1.4)
    # ---- the floor: cracked obsidian with a lit dance floor of glowing tiles
    defs += lin_grad("fl", [(0, "#321320"), (0.3, "#1a0a16"), (1, "#0a0208")], 0, 0, 0, 1)
    floor_poly = [(0, lwall_y(FY1, 0)), (FX0, FY1), (FX1, FY1), (W, rwall_y(FY1, W)), (W, H), (0, H)]
    d += poly(floor_poly, "url(#fl)")
    defs += clip("floorclip", poly(floor_poly))
    grid = ""
    ys = []
    z = 1.0
    while True:
        y = VPY + (FY1 - VPY) / z
        if y > H + 40:
            break
        ys.append(y)
        z -= 0.065
    for i, y in enumerate(ys):
        grid += line((-80, y), (W + 80, y), "#8a3a4a", 1.0 + i * 0.16, 0.18 + min(i, 8) * 0.01)
    for k in range(-16, 17):
        xf = VPX + k * 61.7
        grid += line((xf, FY1), (floor_x(xf, H + 40), H + 40), "#8a3a4a", 1.4, 0.18)
    for k in range(34):  # obsidian cracks outside the dance floor
        xf = rng.uniform(-300, 1580)
        ya = rng.uniform(FY1 + 4, H - 60)
        sc = (ya - VPY) / (FY1 - VPY)
        xa = floor_x(xf, ya)
        pts = jag((xa, ya), (xa + rng.uniform(-30, 30) * sc, ya + rng.uniform(16, 50) * sc), 4, 8 * sc, rng)
        grid += path(pline(pts), None, "#08020a", 2.2 * sc, sop=0.7)
        if k % 3 == 0:
            grid += path(pline(pts), None, LAVA, 1.1 * sc, sop=0.6)
    d += group(grid, 'clip-path="url(#floorclip)"')
    cols_far = [400 + 60 * i for i in range(9)]
    y_lines = [y for y in ys if 264 <= y <= 530]
    palette = [(LAVA, 0.30), (MAG, 0.2), (VIO, 0.2), ("#46202c", 0.6), ("#2a0c1a", 0.7), (LAVA, 0.14), (EMBER, 0.16), (MAG, 0.1)]
    tiles = ""
    for j in range(len(y_lines) - 1):
        ya, yb = y_lines[j], y_lines[j + 1]
        for i in range(len(cols_far) - 1):
            c, a = palette[rng.randrange(len(palette))]
            q = [(floor_x(cols_far[i], ya), ya), (floor_x(cols_far[i + 1], ya), ya), (floor_x(cols_far[i + 1], yb), yb), (floor_x(cols_far[i], yb), yb)]
            tiles += poly(q, "#120610", None, op=0.55)
            tiles += poly(q, c, None, op=a)
            tiles += poly(q, None, lighten(c, 0.35), 1.1, sop=0.5)
    d += tiles
    d += neon((floor_x(400, 264), 264), (floor_x(880, 264), 264), LAVA, 1.4, 0.8)
    # the summoning circle on the floor under the crowd (matches circle_centre / circle_radii)
    ccx, ccy, crx, cry = 640, 372, 250, 46
    for rr, op in ((1.0, 0.7), (0.88, 0.4)):
        d += ellipse(ccx, ccy, crx * rr, cry * rr, None, EMBER if rr == 1.0 else LAVA, 1.8 if rr == 1.0 else 1.2, sop=op)
    star = [(ccx + math.cos(math.radians(-90 + k * 144)) * crx * 0.94, ccy + math.sin(math.radians(-90 + k * 144)) * cry * 0.94) for k in range(5)]
    d += path("M" + " L".join(f"{f(x)} {f(y)}" for x, y in star) + " Z", None, LAVA, 1.4, sop=0.55)
    for k in range(24):
        a = k * math.tau / 24
        d += line((ccx + math.cos(a) * crx * 1.0, ccy + math.sin(a) * cry * 1.0), (ccx + math.cos(a) * crx * 1.06, ccy + math.sin(a) * cry * 1.06), EMBER, 1.6, 0.6)
    defs += lin_grad("sheen", [(0, "#ff4a1c", 0.28), (1, "#ff4a1c", 0.0)], 0, 0, 0, 1)
    d += poly([(FX0, FY1), (FX1, FY1), (FX1 + 40, FY1 + 36), (FX0 - 40, FY1 + 36)], "url(#sheen)")
    # ---- lava gutters along the foot of both side walls, fed by the lava falls; their light rakes across the floor
    defs += lin_grad("gut", [(0, "#ffe08a"), (0.15, "#ff8a2a"), (0.6, "#e0361a"), (1, "#8a1010")], 0, 0, 0, 1)
    defs += lin_grad("gutglowL", [(0, "#ff6a1a", 0.34), (1, "#ff6a1a", 0.0)], 0, 0, 1, 0)
    defs += lin_grad("gutglowR", [(0, "#ff6a1a", 0.0), (1, "#ff6a1a", 0.34)], 0, 0, 1, 0)
    for side in (-1, 1):
        xa, xb = (FX0, FX0 + 22) if side < 0 else (FX1 - 22, FX1)
        xg = FX0 + 90 if side < 0 else FX1 - 90
        strip = lambda a, b, y0=FY1, y1=H + 40: [(floor_x(a, y0), y0), (floor_x(b, y0), y0), (floor_x(b, y1), y1), (floor_x(a, y1), y1)]  # noqa: E731
        d += poly(strip(xb, xg) if side < 0 else strip(xg, xa), "url(#gutglow%s)" % ("L" if side < 0 else "R"))
        d += poly(strip(xa, xb), OUT, OUT, 4) + poly(strip(xa, xb), "url(#gut)")
        for i, y in enumerate(ys):
            if FY1 + 4 < y < H:
                sc = (y - VPY) / (FY1 - VPY)
                d += line((floor_x(xa, y), y), (floor_x(xb, y), y), "#2a0a0a", 2.2 * sc ** 0.8, 0.35)  # crust ripples
        lip = xb if side < 0 else xa
        d += line((floor_x(lip, FY1), FY1), (floor_x(lip, H + 40), H + 40), "#5a2a32", 3.0, 0.9)
        d += line((floor_x(lip, FY1), FY1), (floor_x(lip, H + 40), H + 40), "#ffb070", 1.2, 0.7)
    # ---- fire pit bowls (the flames are a stage piece)
    for px_ in (118, 1162):
        py_ = 334
        d += ellipse(px_, py_ + 8, 60, 14, "#08020a", None, op=0.5)
        d += ellipse(px_, py_ + 4, 50, 15, "#2d1220", OUT, 3)
        d += ellipse(px_, py_, 50, 15, "#46202c", OUT, 3)
        for k in range(14):  # stones
            a = k * math.tau / 14
            d += ellipse(px_ + math.cos(a) * 46, py_ + math.sin(a) * 12.4, 6.4, 4.6, mix("#46202c", "#8a5a5a", (k % 3) * 0.12), OUT, 1.5)
        d += ellipse(px_, py_ - 1, 38, 10, "#1a0408", OUT, 2)
        d += ellipse(px_, py_ - 1, 34, 8.5, LAVA, None, op=0.55) + ellipse(px_, py_ - 1, 24, 6, "#ffb02e", None, op=0.7) + ellipse(px_, py_ - 1, 12, 3.4, "#fff2a0", None, op=0.85)
        d += ellipse(px_, py_ + 6, 78, 20, LAVA, None, op=0.08)
    # ---- ceiling: rock fringe, iron brackets for the light points
    d += stalactites(-6, -10, W + 10, rng, 16, 58, 18, 46, "#2a0f1c")
    d += stalactites(FY0, FX0, FX1, rng, 6, 22, 10, 22, "#1f0b16", ol=2.0)
    d += neon((60, 5), (1220, 5), LAVA, 1.0, 0.45)
    for (x, y) in ((150, 30), (330, 30), (510, 30), (770, 30), (950, 30), (1130, 30), (450, 58), (830, 58)):
        d += line((x, -6), (x, y), OUT, 4.4) + line((x, -6), (x, y), "#7a6a76", 2)
        d += rect(x - 9, y - 4, 18, 8, "#5a4a56", OUT, 2.2, rx=2) + circle(x, y, 3, EMBER, OUT, 1.2)
    return write_svg("backdrop.svg", (0, 0, W, H), d, defs)


# ---- speaker stacks, riser, desk -------------------------------------------------------------------------------------------

SPK_W, SPK_H = S.SPK_W, S.SPK_H


def build_speaker(side):
    d = ""
    defs = lin_grad("cab", [(0, "#46202c"), (1, "#1a0a16")], 0, 0, 0, 1)
    defs += lin_grad("cabside", [(0, "#ffffff", 0.0), (1, "#ffffff", 0.12)], 0, 0, 1, 0)
    d += rect(4, 6, SPK_W - 8, SPK_H - 12, "url(#cab)", OUT, 4, rx=6)
    d += rect(4, 6, SPK_W - 8, SPK_H - 12, "url(#cabside)", None, rx=6)
    for yy in (6, SPK_H - 6):
        d += rect(4, yy - 5 if yy < 20 else yy - 6, SPK_W - 8, 11, "#6a5a62", OUT, 3, rx=3)
    for xx in (8, SPK_W - 8):
        for yy in (12, SPK_H - 12):
            d += circle(xx, yy, 5, "#8a7a82", OUT, 2) + line((xx - 2, yy - 2), (xx + 2, yy + 2), OUT, 1.2)
    for (x, y, r) in S.SPK_WOOFERS:
        d += circle(x, y, r + 5, "#08020a", OUT, 3)
        d += circle(x, y, r + 2, "#05010a", None)
    d += poly([(8, 12), (-2, -12), (20, 6)], BONE, OUT, 2.2) + poly([(SPK_W - 8, 12), (SPK_W + 2, -12), (SPK_W - 20, 6)], BONE, OUT, 2.2)  # horns on top
    d += skull(SPK_W / 2, 18, 8.5, BONE, "#ff7a1a", 1.8, jaw=False)
    d += rect(34, 158, 44, 6, "#08020a", OUT, 2, rx=2) + rect(37, 160, 18, 2.4, LAVA, None, op=0.95)
    d += rect(20, 164, 14, 5, "#07020c", OUT, 2) + rect(78, 164, 14, 5, "#07020c", OUT, 2)
    d += line((6, 50), (6, 130), EMBER if side < 0 else MAG, 2.0, 0.75)
    for k in range(5):
        yy = 148 + (k % 2) * 3
        d += path(f"M{10 + k * 22} {yy - 3} L{16 + k * 22} {yy + 4} L{22 + k * 22} {yy - 3}", None, "#08020a", 1.4, sop=0.6)
    return write_svg("speaker_%s.svg" % ("l" if side < 0 else "r"), (-6, -16, SPK_W + 6, SPK_H), d, defs)


def build_riser():
    w, h = 240, 34
    d = ""
    defs = lin_grad("rt", [(0, "#6a5a62"), (1, "#3a2a32")], 0, 0, 0, 1)
    defs += lin_grad("rf", [(0, "#2d1220"), (1, "#0b0308")], 0, 0, 0, 1)
    d += poly([(22, 3), (w - 22, 3), (w - 2, 16), (2, 16)], "url(#rt)", OUT, 3)
    d += poly([(2, 16), (w - 2, 16), (w - 2, h - 3), (2, h - 3)], "url(#rf)", OUT, 3)
    for k in range(7):  # rib bones standing in the riser front
        xk = 14 + k * 35
        d += path(f"M{xk} 18 Q{xk + 7} 26 {xk} {h - 5}", None, OUT, 6) + path(f"M{xk} 18 Q{xk + 7} 26 {xk} {h - 5}", None, BONE, 3.4)
    d += neon((6, 17), (w - 6, 17), LAVA, 1.5, 1.0)
    d += neon((6, h - 6), (w - 6, h - 6), MAG, 1.2, 0.8)
    d += line((24, 6), (w - 24, 6), "#bcaab2", 1.4, 0.5)
    return write_svg("riser.svg", (0, 0, w, h), d, defs)


_HEX = re.compile(r"#[0-9a-fA-F]{6}")


def _remap_hex(m):
    c = m.group(0)
    r, g, b = lib.hex_to_rgb(c)
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    hd = h * 360
    if s < 0.12:
        return c
    if 160 <= hd < 215:
        nh, ns = 40, s
    elif 215 <= hd < 300:
        nh, ns = 352, s * 0.8
    elif 300 <= hd <= 350:
        nh, ns = 14, s
    else:
        return c
    rr, gg, bb = colorsys.hls_to_rgb(nh / 360, l, ns)
    return lib.rgb_to_hex((rr * 255, gg * 255, bb * 255))


def remap(text):
    """Re-theme Night One's cool neon palette to hell's: indigo to wine, cyan to gold, magenta to lava."""
    return _HEX.sub(_remap_hex, text)


def _desk_extras():
    d = ""
    w = 1280
    for xs, sgn in ((0, 1), (1280, -1)):  # curved horns on the lip ends
        d += poly([(xs + sgn * 4, 14), (xs + sgn * 50, 18), (xs + sgn * 100, 14), (xs + sgn * 46, 6)], "#d8c8a0", OUT, 2)
    for k in range(16):  # skull rivets along the lip
        x = 110 + k * 72
        d += circle(x, 8.5, 2.6, BONE, OUT, 1.2)
    rng = random.Random(8)
    for xc in (430, 850):  # lava cracks between the pad wings and the mixer
        pts = jag((xc, 28), (xc + rng.uniform(-3, 3), 246), 12, 6, rng, taper=False)
        d += neon_path(pline(pts), LAVA, 1.2, 0.8)
    return d


def _wsvg_factory(extras=True):
    def _w(rel, box, body, defs=""):
        body = remap(body)
        if extras and rel == "desk_top.svg":
            body += _desk_extras()
        return lib.write_svg(rel, box, body, remap(defs))
    return _w


def spr_woofer(sprites):
    r = 50
    d = ""
    defs = rad_grad("cone", [(0, "#8a2a2a"), (0.45, "#4a1620"), (1, "#1a0610")], 0.42, 0.38, 0.75)
    defs += lin_grad("rim", [(0, "#9a8a92"), (1, "#3a2a32")], 0, 0, 1, 1)
    for k in range(14):  # a ring of iron teeth
        a = k * math.tau / 14
        d += poly([(math.cos(a - 0.12) * (r - 2), math.sin(a - 0.12) * (r - 2)), (math.cos(a) * (r + 5), math.sin(a) * (r + 5)), (math.cos(a + 0.12) * (r - 2), math.sin(a + 0.12) * (r - 2))], "#9a8a92", OUT, 2)
    d += circle(0, 0, r - 3, "url(#rim)", OUT, 3.5)
    d += circle(0, 0, r - 8, "#08020a", None)
    d += circle(0, 0, r - 12, "url(#cone)", OUT, 2.2)
    for k, rr in enumerate((34, 28, 22, 17)):
        d += circle(0, 0, rr, None, "#05010a" if k % 2 == 0 else "#ff5a1a", 1.4, sop=0.6)
    d += circle(0, 0, 12, "#2d0a0a", OUT, 2.4)
    d += ellipse(0, 0, 7, 9, "#ff7a1a", OUT, 1.4) + ellipse(0, 0, 2.2, 7, "#1a0010", None)
    d += path("M-32 -20 A38 38 0 0 1 -8 -36", None, "#ffffff", 3, sop=0.35)
    info = write_svg("props/woofer.svg", (-r - 8, -r - 8, r + 8, r + 8), d, defs)
    sprites["woofer"] = {"file": "source/props/woofer.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "radius": r}


def spr_fixture(sprites):
    d = ""
    defs = lin_grad("body", [(0, "#6a4a5a"), (1, "#2a1220")], 0, 0, 1, 0)
    d += rect(-11, 0, 22, 6, "#8a7a82", OUT, 2.4, rx=2)
    d += path("M-15 8 L-15 30 M15 8 L15 30", None, OUT, 8) + path("M-15 8 L-15 30 M15 8 L15 30", None, "#6a5a62", 4.4)
    d += rect(-8, 6, 16, 8, "#46202c", OUT, 2.2, rx=2)
    d += poly([(-11, 20), (-17, 6), (-5, 17)], BONE, OUT, 1.8) + poly([(11, 20), (17, 6), (5, 17)], BONE, OUT, 1.8)  # little horns
    d += rect(-12, 16, 24, 34, "url(#body)", OUT, 3, rx=5)
    d += line((-8, 20), (-8, 46), "#ffd0b0", 1.4, 0.45)
    for yy in (24, 30, 36):
        d += line((-10, yy), (10, yy), "#08020a", 1.2, 0.5)
    d += ellipse(0, 51, 11, 4.5, "#0a0108", OUT, 2.4)  # the eye-lamp
    d += ellipse(0, 51, 8, 3.2, "#fff2c0", None) + ellipse(0, 51, 3.2, 3.0, "#ffffff", None) + ellipse(0, 51, 1.2, 3.0, "#ff3a1a", None)
    d += circle(-15, 30, 3, "#8a7a82", OUT, 1.4) + circle(15, 30, 3, "#8a7a82", OUT, 1.4)
    info = write_svg("props/fixture.svg", (-22, -2, 22, 60), d, defs)
    sprites["fixture"] = {"file": "source/props/fixture.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "lens": [0, 51]}


def spr_disco_ball(sprites):
    """The infernal brazier-ball: a lava orb in an iron cage, hanging from a chain."""
    d = ""
    defs = rad_grad("ball", [(0, "#fff2a0"), (0.35, "#ff9a2a"), (0.75, "#c42a10"), (1, "#4a0a10")], 0.42, 0.38, 0.62)
    cy, r = 66, 27
    d += chain((0, 0), (0, cy - r + 2), 8)
    d += circle(0, cy, r + 9, "#ff5a1a", None, op=0.14) + circle(0, cy, r + 5, "#ff7a1a", None, op=0.2)
    d += circle(0, cy, r, "url(#ball)", OUT, 3.4)
    rng = random.Random(9)
    defs += clip("bc", f'<circle cx="0" cy="{cy}" r="{r}"/>')
    inner = ""
    for k in range(5):  # molten cracks
        a = rng.uniform(0, math.tau)
        pts = jag((math.cos(a) * 4, cy + math.sin(a) * 4), (math.cos(a + 0.3) * r, cy + math.sin(a + 0.3) * r), 4, 4, rng)
        inner += path(pline(pts), None, "#3a0808", 2.0, sop=0.8)
    inner += circle(r * 0.5, cy + r * 0.45, r * 0.9, "#150a33", None, op=0.22)
    d += group(inner, 'clip-path="url(#bc)"')
    for k in range(-2, 3):  # cage ribs
        d += path(f"M{f(k * 7 * 0.5)} {cy - r} Q{f(k * 14)} {cy} {f(k * 7 * 0.5)} {cy + r}", None, "#3a2a32", 2.2)
    d += path(f"M{-r} {cy} Q0 {cy + 8} {r} {cy}", None, "#3a2a32", 2.2) + path(f"M{-r} {cy} Q0 {cy - 8} {r} {cy}", None, "#3a2a32", 2.2)
    for k in range(8):  # spikes
        a = k * math.tau / 8 + 0.3
        d += poly([(math.cos(a - 0.12) * r, cy + math.sin(a - 0.12) * r), (math.cos(a) * (r + 9), cy + math.sin(a) * (r + 9)), (math.cos(a + 0.12) * r, cy + math.sin(a + 0.12) * r)], "#9a8a92", OUT, 1.8)
    d += circle(-9, cy - 10, 4.4, "#ffffff", None, op=0.8)
    d += circle(0, cy, r, None, OUT, 3.4)
    info = write_svg("props/disco_ball.svg", (-r - 14, -2, r + 14, cy + r + 14), d, defs)
    sprites["disco_ball"] = {"file": "source/props/disco_ball.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5, "radius": r, "ball_centre": [0, cy]}


def spr_glowstick(sprites):
    """A small flame torch: white so the runtime tints it; pivot at the grip end."""
    d = ""
    d += line((0, 4), (0, 38), OUT, 10, cap="round")
    d += line((0, 4), (0, 38), "#ffffff", 5.6, cap="round")
    d += line((0, 31), (0, 38), "#9d90d8", 5.6, cap="butt")
    d += line((-4.4, 14), (4.4, 14), OUT, 1.4) + line((-4.4, 22), (4.4, 22), OUT, 1.4)
    d += path(UC.flame_path(0, 4, 1, -24, 6.5, 2), "#ffffff", OUT, 2.2)
    d += path(UC.flame_path(0, 2, 0.6, -14, 3.2, 1.2), "#ffffff", None, op=0.0)
    info = write_svg("props/glowstick.svg", (-12, -30, 12, 44), d)
    sprites["glowstick"] = {"file": "source/props/glowstick.svg", "pivot": pivot_in(info, (0, 38)), "px_scale": 0.5, "length": 36}


# ---- silhouettes -----------------------------------------------------------------------------------------------------------

def _sil_shape(kind, up):
    s = ""

    def horn_shape(pts, w0, w1):
        poly_pts, _l, _r = UC.taper(pts, w0, w1)
        return poly(poly_pts, "#fff")

    if kind == "a":  # a brute: broad shoulders with spiked pauldrons and big curling ram horns
        s += path("M-46 0 L-44 -24 Q-42 -42 -18 -47 Q-10 -49 -9 -55 L9 -55 Q10 -49 18 -47 Q42 -42 44 -24 L46 0 Z", "#fff")
        s += ellipse(0, -72, 18, 19, "#fff")
        for sg in (-1, 1):
            spiral = [(sg * 8, -86)]
            for k in range(26):
                a = math.radians(-120 + k * 13)
                r = 19 - k * 0.5
                spiral.append((sg * (30 + r * math.cos(a)), -78 + r * math.sin(a)))
            s += horn_shape(spiral, 13, 4)
            for k in range(3):  # pauldron spikes
                a = math.radians(-150 + k * 40)
                bx, by = sg * (34 + math.cos(a) * 12), -44 + math.sin(a) * 10
                tx, ty = sg * (34 + math.cos(a) * 30), -44 + math.sin(a) * 26
                s += poly([(bx - 5, by + 2), (tx, ty), (bx + 5, by + 2)], "#fff")
            s += ellipse(sg * 34, -42, 16, 11, "#fff")
    elif kind == "b":  # a fiend: long swept horns and wide bat wings behind the shoulders
        for sg in (-1, 1):
            s += path(f"M{sg * 18} -40 L{sg * 50} -96 Q{sg * 60} -98 {sg * 70} -84 L{sg * 78} -54 Q{sg * 66} -56 {sg * 62} -40 "
                      f"Q{sg * 58} -26 {sg * 50} -18 Q{sg * 44} -30 {sg * 34} -26 Z", "#fff")
            s += line((sg * 50, -96), (sg * 53, -108), "#fff", 5)
        s += path("M-30 0 L-28 -26 Q-26 -44 -11 -48 Q-7 -50 -7 -57 L7 -57 Q7 -50 11 -48 Q26 -44 28 -26 L30 0 Z", "#fff")
        s += ellipse(0, -72, 14, 17, "#fff")
        for sg in (-1, 1):
            s += horn_shape(UC.bez((sg * 7, -84), (sg * 20, -100), (sg * 30, -122), 12), 8, 1.5)
        s += path("M-10 -86 Q0 -96 12 -88 Q18 -92 16 -80 Z", "#fff")  # slick quiff
    else:  # an imp: huge pointed ears, little horns and a spade-tipped tail
        s += path("M-32 0 L-30 -22 Q-28 -40 -12 -44 Q-8 -46 -8 -52 L8 -52 Q8 -46 12 -44 Q28 -40 30 -22 L32 0 Z", "#fff")
        s += ellipse(0, -72, 21, 19, "#fff")
        for sg in (-1, 1):
            s += poly([(sg * 17, -80), (sg * 48, -90), (sg * 19, -64)], "#fff")
            s += horn_shape(UC.bez((sg * 8, -86), (sg * 16, -98), (sg * 13, -110), 10), 8, 1.5)
        s += path("M28 -6 Q60 -4 56 -34 Q54 -44 60 -50", None, "#fff", 6)
        s += poly([(60, -62), (71, -47), (61, -42), (51, -48)], "#fff")
    if up:
        for sx in (-1, 1):
            s += line((sx * 26, -40), (sx * 46, -118), "#fff", 13)
            s += circle(sx * 47, -122, 8, "#fff")
            for k in (-1, 1):  # devil-horns hands
                s += line((sx * 47 + k * 4, -126), (sx * 47 + k * 7, -138), "#fff", 4)
    return s


def build_silhouettes():
    out = {}
    fills = {"a": "#12040c", "b": "#0e030a", "c": "#150610"}
    for kind in ("a", "b", "c"):
        entry = {}
        for state in ("idle", "up"):
            up = state == "up"
            shape = _sil_shape(kind, up)
            body = ""
            for dx, dy, col in ((-2.2, -1.2, EMBER), (2.2, -1.2, MAG)):
                body += S._recolor(shape, col, dx, dy)
            body += S._recolor(shape, fills[kind], 0, 0)
            info = write_svg(f"silhouettes/sil_{kind}_{state}.svg", (-84, -146 if up else -128, 84, 4), body)
            entry[state] = {"file": f"source/silhouettes/sil_{kind}_{state}.svg", "pivot": pivot_in(info, (0, 0)), "px_scale": 0.5}
        entry["height"] = 100
        out[f"sil_{kind}"] = entry
    return out


# ---- Pillow textures ---------------------------------------------------------------------------------------------------------

def _save_rgba(name, arr):
    os.makedirs(lib.PNG_DIR, exist_ok=True)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(lib.PNG_DIR, name), compress_level=9)
    return f"processed/{name}"


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def _ramp(v, stops):
    """Piecewise-linear colour ramp: v in 0..1 -> rgb array; stops = [(t, (r, g, b))]."""
    out = np.zeros(v.shape + (3,), dtype=np.float64)
    ts = [s[0] for s in stops]
    for c in range(3):
        out[..., c] = np.interp(v, ts, [s[1][c] for s in stops])
    return out


def swirl_png(name, n, arms, twist, hole, ring_in, alpha_dark, seed, bright=1.0):
    """A hellmouth swirl: logarithmic spiral arms from lava white-hot at the rim of the hole to deep red-black at the edge."""
    yy, xx = np.mgrid[0:n, 0:n]
    dxn = (xx - n / 2 + 0.5) / (n / 2)
    dyn = (yy - n / 2 + 0.5) / (n / 2)
    r = np.hypot(dxn, dyn)
    th = np.arctan2(dyn, dxn)
    noise = png_sprites.periodic_noise(n, n, n / 16.0, n / 16.0, seed)
    ph = arms * th + twist * np.log(np.maximum(r, 0.04)) * 3.0 + (noise - 0.5) * 1.6
    arm = 0.5 + 0.5 * np.sin(ph)
    arm = _smooth((arm - 0.25) / 0.6)
    fall = _smooth((1.0 - r) / 0.38)  # fade towards the edge
    heat = np.clip(arm * (0.22 + 0.6 * _smooth((r - hole) / (0.6 - hole))) + (1 - _smooth((r - hole) / 0.3)) * 0.28, 0, 1)
    col = _ramp(heat * bright, [(0.0, (10, 0, 6)), (0.35, (90, 6, 16)), (0.65, (200, 30, 14)), (0.88, (255, 110, 30)), (1.0, (255, 200, 90))])
    a = fall * (0.55 + 0.45 * arm) * alpha_dark
    a = np.maximum(a, fall * 0.75 * alpha_dark)
    core = _smooth((r - hole * 0.6) / (hole * 0.5))  # the black hole in the middle
    col = col * (0.15 + 0.85 * core)[..., None]
    a = np.where(r < hole, alpha_dark * fall, a)
    ringglow = np.exp(-((r - ring_in) / 0.05) ** 2)
    col = col + ringglow[..., None] * np.array([255, 150, 60]) * 0.6
    a = np.clip(a + ringglow * 0.9 * fall, 0, 1)
    out = np.zeros((n, n, 4))
    out[..., :3] = np.clip(col, 0, 255)
    out[..., 3] = a * 255
    return _save_rgba(name, out)


def _soft_dot(size, cx, cy, rad, color, falloff=2.0):
    yy, xx = np.mgrid[0:size, 0:size]
    r = np.hypot(xx - cx, yy - cy) / rad
    a = np.clip(1 - r, 0, 1) ** falloff
    return a


def embers_png(name, colors, frames=4, cell=32):
    out = np.zeros((cell, cell * frames, 4))
    for i in range(frames):
        sub = np.zeros((cell, cell, 4))
        halo = _soft_dot(cell, cell / 2, cell / 2, cell * 0.48, None, 1.8)
        core = _soft_dot(cell, cell / 2, cell / 2, cell * (0.14 + 0.03 * (i % 2)), None, 1.2)
        c = np.array(colors[i % len(colors)], dtype=float)
        sub[..., :3] = c
        sub[..., 3] = np.clip(halo * 0.55 + core, 0, 1) * 255
        sub[..., :3] = sub[..., :3] * (1 - core[..., None]) + np.array([255, 245, 200]) * core[..., None]
        out[:, i * cell:(i + 1) * cell] = sub
    return _save_rgba(name, out)


def ember_rain_png(name, w, h, count, seed):
    rng = random.Random(seed)
    big = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    dr = ImageDraw.Draw(big)
    for _ in range(count):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        ln = rng.uniform(6, 26)
        wd = rng.uniform(1.2, 3.0)
        c = rng.choice([(255, 90, 30), (255, 150, 40), (255, 205, 80), (255, 60, 40)])
        dr.line([(x * 2, y * 2), ((x - ln * 0.18) * 2, (y - ln) * 2)], fill=c + (130,), width=int(wd * 2))
        dr.ellipse([(x - wd) * 2, (y - wd) * 2, (x + wd) * 2, (y + wd) * 2], fill=(255, 240, 190, 255))
    glow = big.filter(ImageFilter.GaussianBlur(5))
    img = Image.alpha_composite(glow, big).resize((w, h), Image.LANCZOS)
    os.makedirs(lib.PNG_DIR, exist_ok=True)
    img.save(os.path.join(lib.PNG_DIR, name), compress_level=9)
    return f"processed/{name}"


def crack_png(name, w, h, seed, branches=5, width0=2.6, width1=30.0, jitter=34.0, pad=56):
    """A glowing fissure fanning down from the top centre, in perspective (thin far away, wide near), with side branches.
    Drawn at 2x with round joints: a blurred red glow, a charred dark lip, molten orange and a white-hot core; then
    downsampled. Everything stays `pad` texture px inside the edges and the alpha fades out towards them, so the glow is
    never cut by the texture border however the sprite is stretched."""
    rng = random.Random(seed)
    k = 2
    layers = [Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0)) for _ in range(4)]
    draws = [ImageDraw.Draw(im) for im in layers]
    x_lo, x_hi, y_hi = pad, w - pad, h - pad

    def clampp(p):
        return (min(max(p[0], x_lo), x_hi), min(p[1], y_hi))

    def seg(p, q, wd):
        p, q = clampp(p), clampp(q)
        for dr, mul, add, col in ((draws[0], 4.4, 4, (255, 60, 20, 200)), (draws[1], 2.6, 3, (70, 12, 8, 190)),
                                  (draws[2], 2.0, 1.8, (255, 120, 30, 255)), (draws[3], 0.5, 0.6, (255, 236, 150, 255))):
            wd_ = (wd * mul + add) * k
            dr.line([(p[0] * k, p[1] * k), (q[0] * k, q[1] * k)], fill=col, width=int(wd_))
            r_ = wd_ / 2
            for (x, y) in (p, q):
                dr.ellipse([x * k - r_, y * k - r_, x * k + r_, y * k + r_], fill=col)

    def zig(x0, y0, x1, y1, n, amp, wd0, wd1, branch_p, depth=0):
        pts = [(x0, y0)]
        side = rng.choice((-1, 1))
        for i in range(1, n):
            t = i / n
            side = -side if rng.random() < 0.8 else side
            pts.append((x0 + (x1 - x0) * t + side * amp * (0.3 + 0.7 * t) * rng.uniform(0.5, 1.0), y0 + (y1 - y0) * t + rng.uniform(-8, 8)))
        pts.append((x1, y1))
        for i, (p, q) in enumerate(zip(pts, pts[1:])):
            t = i / n
            seg(p, q, wd0 + (wd1 - wd0) * t ** 1.2)
            if depth == 0 and rng.random() < branch_p and i > 1:
                sgn = rng.choice((-1, 1))
                zig(q[0], q[1], q[0] + sgn * rng.uniform(160, 420) * (0.4 + t), q[1] + rng.uniform(40, 160) * (0.5 + 0.6 * t), 7, 40,
                    wd1 * 0.35 * (0.4 + t), wd1 * 0.5 * (0.4 + t), 0.0, 1)

    zig(w / 2, 2, w / 2 + rng.uniform(-60, 60), y_hi, 12, jitter * 2.4, width0, width1, 0.34)
    for _ in range(branches - 1):
        t = rng.uniform(0.08, 0.35)
        zig(w / 2 + rng.uniform(-14, 14), h * t, w / 2 + rng.choice((-1, 1)) * rng.uniform(300, 700), h * rng.uniform(0.55, 0.95), 9, 44, 1.5,
            width1 * 0.4, 0.0, 1)
    glow = layers[0].filter(ImageFilter.GaussianBlur(9 * k))
    glow = Image.alpha_composite(glow, layers[0].filter(ImageFilter.GaussianBlur(4 * k)))
    lip = layers[1].filter(ImageFilter.GaussianBlur(0.8 * k))
    mid = layers[2].filter(ImageFilter.GaussianBlur(1.5 * k))
    img = Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(glow, lip), mid), layers[3]).resize((w, h), Image.LANCZOS)
    arr = np.asarray(img).astype(np.float64)
    yy, xx = np.mgrid[0:h, 0:w]
    edge = _smooth(np.minimum(np.minimum(xx, w - 1 - xx), h - 1 - yy) / (pad * 0.6))  # the top edge is the origin, keep it
    arr[..., 3] *= edge
    return _save_rgba(name, arr)


def build_png_sprites():
    sp = png_sprites.build_png_sprites()  # glow, beam, spot_pool, haze_a/b, vignette, confetti (white lighting sprites)
    w, h = 640, 360
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h / 2 + 0.5) / (h / 2))
    a = _smooth((r - 0.6) / 0.62) * 0.74
    sp["vignette"] = {"file": _save_rgba("vignette.png", np.dstack([np.full((h, w), 24.0), np.full((h, w), 2.0), np.full((h, w), 10.0), a * 255])), "pivot": [w / 2, h / 2], "px_scale": 2.0}
    sp["confetti"] = {"file": embers_png("confetti.png", [(255, 120, 40), (255, 190, 70), (255, 70, 50), (190, 170, 170)]), "pivot": [16, 16], "px_scale": 1.0,
                      "frames": 4, "frame_size": [32, 32], "note": "ash-embers"}
    # the floor spot pool, gentler than Night One's: it is drawn over the crowd, so a dimmer centre and a fainter far half keep
    # the dancer standing in it lit instead of washed out, while the rim still reads as a pool of light on the floor
    w, h = 400, 140
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h / 2 + 0.5) / (h / 2))
    a = np.clip(1 - r ** 2, 0, 1) ** 1.4 * 0.42 + np.exp(-((r - 0.86) / 0.08) ** 2) * 0.3 * (r < 1.0)
    a = a * (0.45 + 0.55 * _smooth((yy + 0.5) / h * 1.4 - 0.2))
    sp["spot_pool"] = {"file": _save_rgba("spot_pool.png", np.dstack([np.full((h, w), 255.0)] * 3 + [np.clip(a, 0, 1) * 255])),
                       "pivot": [w / 2, h / 2], "px_scale": 1.0}
    return sp


# ---- set pieces -------------------------------------------------------------------------------------------------------------

def _flame_cluster(cx, base_y, h, rng, n=5, spread=34, w=15, soft=True):
    d = ""
    if soft:
        d += ellipse(cx, base_y - h * 0.3, spread + 26, h * 0.5, "#ff5a1a", None, op=0.1) + ellipse(cx, base_y - h * 0.25, spread + 8, h * 0.38, "#ff8a2a", None, op=0.12)
    tongues = []
    for i in range(n):
        t = i / (n - 1) - 0.5
        tongues.append((cx + t * spread * 1.3, cx + t * spread * 2.0 + rng.uniform(-6, 6), base_y - h * (0.62 + 0.38 * (1 - abs(t) * 1.6)) * rng.uniform(0.86, 1.0), w * (1.0 - abs(t) * 0.5), t * 10))
    tongues.sort(key=lambda t: -abs(t[0] - cx))
    for bx, tx, ty, ww, bend in tongues:
        d += UC.flame_layer(bx, base_y, tx, ty, ww, bend, ("#ff3a1a", "#ff9a1a", "#fff29a"), 0)
    return d


def build_fire_pit(side):
    rng = random.Random(30 + side)
    w, h = 140, 190
    d = _flame_cluster(w / 2, h - 12, 176, rng, n=5, spread=26, w=18)
    for k in range(7):  # sparks
        d += circle(rng.uniform(w * 0.2, w * 0.8), rng.uniform(10, h * 0.6), rng.uniform(1.2, 2.4), "#ffe08a", None, op=0.9)
    name = "pieces/fire_pits_%s.svg" % ("left" if side < 0 else "right")
    write_svg(name, (0, 0, w, h), d)
    cx = 118 if side < 0 else 1162
    return {"id": "fire_pits_%s" % ("left" if side < 0 else "right"), "file": "source/" + name, "pos": [cx - w / 2, 334 - h + 8], "size": [w, h],
            "px_scale": 0.5, "pivot": [w / 2, h - 12], "anim": "flicker", "z": "behind", "blend": "add"}


def build_lava_flow():
    rng = random.Random(77)
    w, h = 1280, 280
    d = ""
    segs = []
    for k in range(11):
        xf = 400 + k * 48 + rng.uniform(-10, 10)
        yb = rng.uniform(150, h - 20)
        pts = [(floor_x(xf, 264), 264 - 262)]
        n = 7
        for i in range(1, n + 1):
            y = 264 + (yb + 262 - 264) * i / n
            sc = (y - VPY) / (FY1 - VPY)
            x = floor_x(xf, y) + rng.uniform(-14, 14) * sc
            pts.append((x, y - 262))
        segs.append(pts)
        if k % 2 == 0:  # a side branch
            j = rng.randrange(2, 5)
            bx, by = pts[j]
            sc = (by + 262 - VPY) / (FY1 - VPY)
            pts2 = [(bx, by)]
            for i in range(1, 4):
                pts2.append((bx + rng.choice((-1, 1)) * i * 30 * sc + rng.uniform(-6, 6), by + i * 16 * sc))
            segs.append(pts2)
    for halo, op in ((4.4, 0.06), (2.6, 0.1)):
        for pts in segs:
            for a, b in zip(pts, pts[1:]):
                sc = max(0.3, (a[1] + 262 - VPY) / (FY1 - VPY))
                d += line(a, b, LAVA, 2.2 * sc * halo, op)
    for pts in segs:
        for a, b in zip(pts, pts[1:]):
            sc = max(0.3, (a[1] + 262 - VPY) / (FY1 - VPY))
            d += line(a, b, "#ff6a1a", 2.2 * sc, 0.85) + line(a, b, "#ffd070", 0.9 * sc, 0.8)
    write_svg("pieces/lava_flow.svg", (0, 0, w, h), d)
    return {"id": "lava_flow", "file": "source/pieces/lava_flow.svg", "pos": [0, 262], "size": [w, h], "px_scale": 0.5, "anim": "pulse", "z": "behind", "blend": "add"}


def build_portal_piece():
    n = 400
    file = swirl_png("hellmouth_swirl.png", n, 5, 1.0, 0.16, 0.2, 1.0, 12)
    return {"id": "hellmouth_portal", "file": file, "pos": [640 - 76, 178 - 76], "size": [152, 152], "px_scale": 152.0 / n, "pivot": [76, 76],
            "anim": "rotate", "z": "behind", "blend": "mix"}


def build_chains():
    w, h = 150, 300
    d = ""
    rng = random.Random(4)
    specs = [(34, 250), (76, 198), (116, 276)]
    for i, (x, ln) in enumerate(specs):
        d += chain((x, 0), (x, ln - 18), 10)
        d += path(f"M{x} {ln - 18} L{x} {ln - 8} Q{x} {ln + 8} {x + 11} {ln + 4} Q{x + 18} {ln} {x + 12} {ln - 7}", None, OUT, 7.4, cap="round")
        d += path(f"M{x} {ln - 18} L{x} {ln - 8} Q{x} {ln + 8} {x + 11} {ln + 4} Q{x + 18} {ln} {x + 12} {ln - 7}", None, "#9a8a92", 4.2, cap="round")
        d += line((x, 2), (x, 8), OUT, 11) + rect(x - 8, -2, 16, 7, "#6a5a62", OUT, 2, rx=2)
    # a skull lantern hanging from the middle chain
    d += skull(76, 214, 13, BONE, "#ff7a1a", 2.0, jaw=True)
    d += circle(76, 214, 22, "#ff7a1a", None, op=0.14) + circle(76, 214, 15, "#ff9a2a", None, op=0.14)
    write_svg("pieces/chains_swing.svg", (0, -4, w, h), d)
    return {"id": "chains_swing", "file": "source/pieces/chains_swing.svg", "pos": [1090, -4], "size": [w, h + 4], "px_scale": 0.5, "pivot": [76, 4],
            "anim": "sway", "z": "behind", "blend": "mix"}


def build_throne():
    w, h = 170, 160
    d = ""
    defs = lin_grad("tb", [(0, "#4a2630"), (1, "#14060c")], 0, 0, 0, 1)
    defs += rad_grad("tg", [(0, "#ff7a1a", 0.5), (1, "#ff3a1a", 0.0)], 0.5, 0.5, 0.5)
    cx = w / 2
    d += circle(cx, 70, 78, "url(#tg)")
    # tall back with a pointed crown
    back = (f"M{cx - 52} {h} L{cx - 52} 62 L{cx - 38} 40 L{cx - 30} 52 L{cx - 18} 26 L{cx - 8} 42 L{cx} 12 L{cx + 8} 42 L{cx + 18} 26 L{cx + 30} 52 L{cx + 38} 40 L{cx + 52} 62 L{cx + 52} {h} Z")
    d += path(back, "url(#tb)", OUT, 4)
    d += path(back, None, BONE, 2.2, sop=0.8)
    for k in range(-3, 4):  # ribs fanning out from the skull
        d += path(f"M{cx + k * 5} 70 Q{cx + k * 15} 98 {cx + k * 12} {h - 26}", None, OUT, 6.4) + path(f"M{cx + k * 5} 70 Q{cx + k * 15} 98 {cx + k * 12} {h - 26}", None, BONE, 3.6)
    # big horns and skull on top
    for sg in (-1, 1):
        d += UC.horn(UC.bez((cx + sg * 14, 18), (cx + sg * 44, 6), (cx + sg * 50, -6 + 4)), 13, 2.4, BONE, rings=3)
    d += skull(cx, 24, 17, BONE, "#ff7a1a", 2.4)
    d += circle(cx - 6.4, 22, 7, "#ff7a1a", None, op=0.35) + circle(cx + 6.4, 22, 7, "#ff7a1a", None, op=0.35)
    # arm rests ending in skulls, and the seat
    for sg in (-1, 1):
        d += rect(cx + sg * 56 - 12 if sg > 0 else cx + sg * 56 - 12, 98, 24, 8, "#6a5a62", OUT, 2.4, rx=3)
        d += rect(cx + sg * 56 - 5, 106, 10, h - 106, "#3a2a32", OUT, 2.4)
        d += skull(cx + sg * 56, 92, 8.5, BONE, "#ff7a1a", 1.8, jaw=False)
    d += rect(cx - 62, 112, 124, 18, "#6a2a30", OUT, 3, rx=5) + rect(cx - 62, 112, 124, 5, "#ff7a2a", None, op=0.5, rx=2)
    d += rect(cx - 66, 130, 132, h - 130, "url(#tb)", OUT, 3.4)
    for k in range(5):
        d += skull(cx - 48 + k * 24, h - 14, 6.4, BONE, "#ff7a1a", 1.4, jaw=False)
    d += neon((cx - 62, 132), (cx + 62, 132), LAVA, 1.4, 1.0)
    d += rect(cx - 30, 114, 60, 8, "#ffd23f", None, op=0.0)
    write_svg("pieces/skull_throne.svg", (0, -10, w, h), d, defs)
    return {"id": "skull_throne", "file": "source/pieces/skull_throne.svg", "pos": [640 - w * 0.4, 270 - (h + 10) * 0.8], "size": [w * 0.8, (h + 10) * 0.8], "px_scale": 0.5,
            "anim": "none", "z": "behind", "blend": "mix"}


def build_bone_arches():
    w, h = 1280, 470
    d = ""
    for sg in (-1, 1):
        def X(x):
            return x if sg < 0 else w - x
        for (p0, p1, p2, w0, w1) in (((-14, 480), (-30, 120), (196, -20), 52, 16), ((-14, 480), (-4, 250), (92, -20), 34, 11)):
            pts = UC.bez((X(p0[0]), p0[1]), (X(p1[0]), p1[1]), (X(p2[0]), p2[1]), 36)
            poly_pts, left, right = UC.taper(pts, w0, w1)
            d += poly(poly_pts, BONE, OUT, 3.4)
            d += path(pline([(left[i][0] * 0.7 + pts[i][0] * 0.3, left[i][1] * 0.7 + pts[i][1] * 0.3) for i in range(2, 34)]), None, "#ffffff", 2.2, sop=0.5)
            d += path(pline([(right[i][0] * 0.78 + pts[i][0] * 0.22, right[i][1] * 0.78 + pts[i][1] * 0.22) for i in range(2, 34)]), None, "#8a7a6a", 3.0, sop=0.45)
            for i in range(4, 34, 4):
                d += line(left[i], right[i], "#8a7a6a", 1.4, 0.7)
            d += circle(pts[-1][0], pts[-1][1], w1 * 0.9, BONE, OUT, 3)
    d += skull(54, 436, 20, BONE, "#ff7a1a", 2.4) + skull(w - 54, 436, 20, BONE, "#ff7a1a", 2.4)
    write_svg("pieces/bone_arches.svg", (0, 0, w, h), d)
    return {"id": "bone_arches", "file": "source/pieces/bone_arches.svg", "pos": [0, 0], "size": [w, h], "px_scale": 0.5, "anim": "none", "z": "front", "blend": "mix"}


def build_ember_rain():
    file = ember_rain_png("ember_rain.png", 640, 360, 70, 5)
    return {"id": "ember_rain", "file": file, "pos": [0, 0], "size": [1280, 720], "px_scale": 2.0, "anim": "flicker", "z": "front", "blend": "add"}


# ---- interlude sprites ---------------------------------------------------------------------------------------------------------

def _flame_field(w, h, seed, width=0.34, sway=0.07):
    """One soft flame tongue as (rgb, alpha, heat) arrays: noise-licked edges, a white-hot core, a red halo. Base at the bottom."""
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    t = 1.0 - (yy + 0.5) / h  # 0 at the base, 1 at the tip
    n1 = png_sprites.periodic_noise(w, h, w / 9.0, h / 10.0, seed)
    n2 = png_sprites.periodic_noise(w, h, w / 5.0, h / 6.0, seed + 7)
    cx = w / 2 + np.sin(t * 6.0 + 0.7 + seed) * w * sway * t + (n1 - 0.5) * w * 0.12 * t
    wp = w * width * np.power(np.clip(1 - t, 0, 1), 0.6) * (0.8 + 0.2 * np.sin(t * 11.0 + seed)) * _smooth(t / 0.05 + 0.35) + 1.0
    dd = np.abs(xx - cx) / wp + (n2 - 0.5) * 0.9 * t
    heat = np.clip(1.0 - dd, 0, 1) * (1.0 - 0.55 * t) + 0.25 * np.exp(-(dd / 0.35) ** 2) * (1 - t)
    tongues = _smooth((heat - n1 * 0.55 * t ** 1.3) / 0.18)
    core = np.exp(-(dd / 0.32) ** 2) * np.clip(1 - t * 1.3, 0, 1)
    v = np.clip(heat * 1.15 + core * 0.5, 0, 1)
    col = _ramp(v, [(0.0, (150, 10, 8)), (0.3, (235, 50, 14)), (0.55, (255, 120, 30)), (0.8, (255, 205, 90)), (1.0, (255, 250, 220))])
    a = np.maximum(np.clip(tongues * 1.4, 0, 1), np.exp(-((dd - 0.4) / 0.9) ** 2) * (1 - t) * 0.35) * _smooth(t / 0.09)
    return col, a, v


def flame_png(name, w, h, seed):
    """A flame jet: a tall central tongue with two shorter side tongues, composited hottest-wins."""
    col, a, v = _flame_field(w, h, seed)
    for k, (dx, hs) in enumerate(((-0.2, 0.62), (0.2, 0.55))):
        sh = int(h * hs)
        c2, a2, v2 = _flame_field(w, sh, seed + 3 + k, width=0.28, sway=0.1)
        shift = int(w * dx)
        c2, a2, v2 = np.roll(c2, shift, axis=1), np.roll(a2, shift, axis=1), np.roll(v2, shift, axis=1)
        if shift > 0:
            a2[:, :shift] = 0
        else:
            a2[:, shift:] = 0
        sl = slice(h - sh, h)
        hot = (v2 * a2) > (v[sl] * a[sl])
        col[sl] = np.where(hot[..., None], c2, col[sl])
        v[sl] = np.where(hot, v2, v[sl])
        a[sl] = np.maximum(a[sl], a2)
    out = np.zeros((h, w, 4))
    out[..., :3] = col
    out[..., 3] = a * 255
    return _save_rgba(name, out)


def build_flame_jet():
    """Interlude flame jet (PNG, a soft licking flame): pivot at the base centre; the cutscene scales it up out of the crack."""
    w, h = 160, 360
    return {"file": flame_png("flame_jet.png", w, h, 14), "pivot": [w / 2, h - 2], "px_scale": 0.5, "blend": "add",
            "note": "pivot at the base centre; animate by flip/scale"}


def build_interlude():
    sp = {}
    # crack: 1520 x 440 texture shown at 760 x 220 design px, pivot at the top centre (the origin, far end of the fissure)
    cw, ch = 1520, 440
    sp["crack_glow"] = {"file": crack_png("crack_glow.png", cw, ch, 21), "pivot": [cw / 2, 0], "px_scale": 0.5, "blend": "add"}
    seg_w, seg_h = 192, 128
    seg_png = crack_png("crack_segment.png", seg_w, seg_h, 5, branches=2, width0=9.0, width1=12.0, jitter=14, pad=18)
    sp["crack_segment"] = {"file": seg_png, "pivot": [seg_w / 2, 0], "px_scale": 0.5, "blend": "add",
                           "note": "a straight fissure slice: stretch it vertically or chain it end to end"}
    sp["flame_jet"] = build_flame_jet()
    n = 512
    sp["portal_vortex"] = {"file": swirl_png("portal_vortex.png", n, 6, 1.3, 0.3, 0.34, 1.0, 31, 0.9), "pivot": [n / 2, n / 2], "px_scale": 1.0}
    sp["embers"] = {"file": embers_png("embers.png", [(255, 110, 30), (255, 190, 60), (255, 70, 40), (255, 160, 50)]), "pivot": [16, 16], "px_scale": 1.0,
                    "frames": 4, "frame_size": [32, 32], "blend": "add"}
    # dark wash: 320 x 180 shown at 1280 x 720; deep red-black, darker at the edges
    w, h = 320, 180
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot((xx - w / 2 + 0.5) / (w / 2), (yy - h / 2 + 0.5) / (h / 2))
    a = 0.5 + 0.45 * _smooth(r / 1.25)
    bottom = np.clip((yy / h - 0.55) / 0.45, 0, 1)
    col = np.dstack([40 + 90 * bottom, 2 + 10 * bottom, 8 + 4 * bottom])
    arr = np.dstack([col, a * 255])
    sp["dark_wash"] = {"file": _save_rgba("dark_wash.png", arr), "pivot": [w / 2, h / 2], "px_scale": 4.0}
    anchors = {"ufo_hover": [640, 70], "beam_floor": [640, 372], "crack_origin": [640, 268], "crack_end": [640, 470], "portal_centre": [640, 196],
               "flame_jets": [[330, 372], [950, 372]]}
    return {"sprites": sp, "anchors": anchors}


# ---- the stage manifest -----------------------------------------------------------------------------------------------------

def build_stage():
    old_w = S.write_svg
    S.write_svg = _wsvg_factory()
    try:
        S.build_desk_top()
        sp: dict = {}
        S.spr_deck(sp)
        door = S.spr_door_open(sp)
    finally:
        S.write_svg = old_w
    sp["door_open"] = door
    spr_woofer(sp)
    spr_fixture(sp)
    spr_disco_ball(sp)
    spr_glowstick(sp)
    sp.update(build_png_sprites())
    layers = []
    build_backdrop()
    layers.append({"id": "backdrop", "file": "source/backdrop.svg", "pos": [0, 0], "size": [W, H], "px_scale": 0.5})
    build_riser()
    layers.append({"id": "riser", "file": "source/riser.svg", "pos": [520, 252], "size": [240, 34], "px_scale": 0.5})
    for side in (-1, 1):
        build_speaker(side)
        sid = "speaker_l" if side < 0 else "speaker_r"
        px, py = S.SPK_POS[sid]
        layers.append({"id": sid, "file": f"source/{sid}.svg", "pos": [px - 6, py - 16], "size": [SPK_W + 12, SPK_H + 16], "px_scale": 0.5})
    layers.append({"id": "desk_top", "file": "source/desk_top.svg", "pos": [0, 460], "size": [1280, 260], "px_scale": 0.5,
                   "note": "authored 1280 x 260; stretch to the pad-strip rectangle"})
    woofers = []
    for sid in ("speaker_l", "speaker_r"):
        px, py = S.SPK_POS[sid]
        for (wx, wy, wr) in S.SPK_WOOFERS:
            woofers.append([px + wx, py + wy, wr])
    pieces = [build_lava_flow(), build_fire_pit(-1), build_fire_pit(1), build_portal_piece(), build_chains(), build_throne(), build_bone_arches(), build_ember_rain()]
    anchors = {
        "led_screen": [400, 56, 480, 44],
        "doorway": [284, 138, 70, 124],
        "floor_rows": FLOOR_ROWS,
        "floor_polygon": [[400, 266], [880, 266], [round(floor_x(880, 520)), 520], [round(floor_x(400, 520)), 520]],
        "floor_grid": {"vanishing_point": [VPX, VPY], "far_y": FY1, "far_x": [400 + 60 * i for i in range(9)],
                       "note": "x on the far wall base line; a floor line through far_x at screen row y is at x = vp_x + (far_x - vp_x) * (y - vp_y) / (far_y - vp_y)"},
        "light_points": [[150, 30], [330, 30], [510, 30], [770, 30], [950, 30], [1130, 30], [450, 58], [830, 58]],
        "woofers": woofers,
        "disco_ball": [640, 0],
        "riser": [640, 286, 240],
        "circle_centre": [640, 372],
        "circle_radii": [250, 46],
        "wall_left_x": FX0, "wall_right_x": FX1, "horizon_y": VPY,
        "hellmouth": [640, 178, 76], "fire_pits": [[118, 334], [1162, 334]],
    }
    stage = {"design_size": [W, H], "layers": layers, "anchors": anchors, "sprites": sp, "pieces": pieces,
             "pieces_note": "pos/size = top-left rectangle in design px; pivot (rotate/sway/flicker) is in design px relative to pos; blend add = draw additively"}
    from . import uw_views  # extra rooms for the moving camera: stage.views and stage.sprites.passage_frame (new files only)
    views, passage = uw_views.build_views()
    sp["passage_frame"] = passage
    stage["views"] = views
    return stage
