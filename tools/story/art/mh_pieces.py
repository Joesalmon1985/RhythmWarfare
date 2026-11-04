"""The authored set pieces of the day room (`stage.pieces` of `main`): notice board, mood lamp, bunting, craft table, wall clock,
paper chains, fairy lights and the window light. pos/size are design px; `pivot` (design px relative to pos) is the animation origin."""
from __future__ import annotations

import math
import random

from .lib import OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, poly, rad_grad, rect, write_svg
from .mh_stage import (BUTTER, CORAL, CREAM, INK, LEAF, LILAC, LILAC_D, MINT, MINT_D, PEACH, WOOD, WOOD_D, WOOD_L, W, H, R, clock, heart,
                       paper_star, piece)

BUNT = [CORAL, BUTTER, "#8fd9c8", "#b9a6f0", "#ff9ac0", "#7fb6ff"]


def swag(p0, p1, sag, n=24):
    """Points along a catenary-ish droop from p0 to p1."""
    pts_ = []
    for k in range(n + 1):
        t = k / n
        pts_.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t + sag * 4 * t * (1 - t)))
    return pts_


def string_path(pts_):
    return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts_)


def bunting_string(p0, p1, sag, n, hang=22, cols=BUNT, fw=15, ol=1.6, cord="#6a5a7a"):
    pts_ = swag(p0, p1, sag, 60)
    d = path(string_path(pts_), None, cord, 1.8)
    for k in range(n):
        t = (k + 0.5) / n
        i = int(t * 60)
        x, y = pts_[i]
        x2, y2 = pts_[min(i + 1, 60)]
        ang = math.atan2(y2 - y, x2 - x)
        c, s = math.cos(ang), math.sin(ang)
        a = (x - c * fw / 2, y - s * fw / 2)
        b = (x + c * fw / 2, y + s * fw / 2)
        d += poly([a, b, (x, y + hang)], cols[k % len(cols)], OUT, ol)
        d += line((x - fw * 0.2, y + 3), (x, y + hang - 5), "#ffffff", 1.2, 0.4)
    return d


# ---- 1. notice board -----------------------------------------------------------------------------------------------------

def notice_board():
    w, h = 92, 120
    d = rect(2, 2, w - 4, h - 4, "#c08850", OUT, 3.4, rx=3)
    d += rect(7, 7, w - 14, h - 14, "#e6b878", OUT, 1.6)
    rng = random.Random(3)
    for k in range(60):
        d += circle(rng.uniform(9, w - 9), rng.uniform(9, h - 9), rng.uniform(0.5, 1.2), "#b8864e", None, op=0.6)
    notes = [(12, 12, 30, 24, "#fff4dc", -4), (48, 14, 30, 30, "#ffd0e0", 3), (14, 44, 24, 30, "#cfeee6", 2), (42, 50, 34, 22, "#fff0a8", -3), (16, 82, 30, 28, "#e6dcfa", 4), (54, 80, 26, 30, "#cfe9ff", -2)]
    for x, y, nw, nh, col, r in notes:
        d += f'<g transform="rotate({r} {x + nw / 2} {y + nh / 2})">' + rect(x, y, nw, nh, col, OUT, 1.4)
        for k in range(3):  # scribbled lines of text
            d += line((x + 4, y + 7 + k * 6), (x + nw - 4 - (k % 2) * 6, y + 7 + k * 6), "#6a5a7a", 1.2, 0.6)
        d += circle(x + nw / 2, y + 2.5, 2.2, CORAL if col != "#ffd0e0" else "#5fc9bb", OUT, 0.8) + "</g>"
    d += paper_star(26, 62, 5, BUTTER, 1.2) + heart(66, 66, 4, CORAL, 1.1)
    d += rect(w / 2 - 22, h - 14, 44, 8, "#fbfbff", OUT, 1.6, rx=2)  # a little chalk shelf
    write_svg("pieces/notice_board.svg", (0, 0, w, h), d)
    return piece("notice_board", "source/pieces/notice_board.svg", (872, 76), (w, h), "none", "behind")


# ---- 2. mood lamp --------------------------------------------------------------------------------------------------------

def mood_lamp():
    w, h = 90, 132
    defs = lin_grad("fl", [(0, "#ff9ad0"), (0.5, "#b98aff"), (1, "#7fb6ff")], 0, 0, 0, 1)
    defs += rad_grad("halo", [(0, "#ffd0f0", 0.65), (1, "#ffd0f0", 0.0)], 0.5, 0.45, 0.5)
    d = circle(w / 2, 42, 44, "url(#halo)", None)
    d += ellipse(w / 2, h - 3, 30, 4, INK, None, op=0.2)
    # round side table
    d += rect(w / 2 - 3, 88, 6, 38, WOOD_D, OUT, 2) + ellipse(w / 2, 126, 20, 4.5, WOOD_D, OUT, 2)
    d += ellipse(w / 2, 88, 32, 7, WOOD_L, OUT, 2.6)
    d += rect(w / 2 - 32, 88, 64, 5, WOOD, OUT, 2)
    # the lamp: base, glass, wax blobs, cap
    d += poly([(w / 2 - 14, 86), (w / 2 + 14, 86), (w / 2 + 10, 66), (w / 2 - 10, 66)], "#e6dcfa", OUT, 2.4)
    d += path(f"M{w / 2 - 10} 66 L{w / 2 - 15} 14 Q{w / 2} 2 {w / 2 + 15} 14 L{w / 2 + 10} 66 Z", "url(#fl)", OUT, 2.6)
    for (bx, by, r_, c) in ((w / 2 - 3, 52, 5.4, "#ffc0e8"), (w / 2 + 3, 36, 4.2, "#ffd9f6"), (w / 2 - 2, 24, 3.2, "#ffc0e8"), (w / 2 + 1, 62, 4, "#ffe0f6")):
        d += circle(bx, by, r_, c, None, op=0.85)
    d += path(f"M{w / 2 - 11} 20 L{w / 2 - 8} 58", None, "#ffffff", 2.2, sop=0.55)
    d += path(f"M{w / 2 - 15} 14 Q{w / 2} 2 {w / 2 + 15} 14 L{w / 2 + 12} 20 L{w / 2 - 12} 20 Z", "#e6dcfa", OUT, 2)
    d += circle(w / 2, 8, 3.2, CORAL, OUT, 1.2)
    write_svg("pieces/mood_lamp.svg", (0, 0, w, h), d, defs)
    return piece("mood_lamp", "source/pieces/mood_lamp.svg", (398, 190), (w, h), "pulse", "behind", pivot=(w / 2, 40))


# ---- 3. bunting ----------------------------------------------------------------------------------------------------------

def bunting():
    w, h = 1280, 120
    d = bunting_string((0, 6), (330, 62), 6, 12, 22) + bunting_string((1280, 6), (950, 62), 6, 12, 22)
    d += bunting_string((318, 44), (962, 44), 18, 30, 20, fw=15)
    write_svg("pieces/bunting.svg", (0, 0, w, h), d)
    return piece("bunting", "source/pieces/bunting.svg", (0, 0), (w, h), "sway", "behind", pivot=(640, 2))


# ---- 4. craft table --------------------------------------------------------------------------------------------------------

def craft_table():
    w, h = 180, 112
    d = ellipse(w / 2, h - 3, 78, 6, INK, None, op=0.22)
    d += rect(10, 52, 6, 56, WOOD_D, OUT, 2) + rect(w - 16, 52, 6, 56, WOOD_D, OUT, 2)  # legs
    d += line((16, 96), (w - 16, 96), WOOD_D, 3)
    d += poly([(2, 54), (w - 2, 54), (w - 10, 44), (10, 44)], WOOD_L, OUT, 2.6)  # tabletop in perspective
    d += rect(2, 54, w - 4, 7, WOOD, OUT, 2.4)
    d += rect(6, 57, w - 12, 18, "#fff4dc", None, op=0.0)
    # craft: paper stack, paint pots, brushes jar, glue, scissors, a half-made paper chain
    d += poly([(20, 50), (58, 50), (62, 44), (24, 44)], "#ffd0e0", OUT, 1.4) + poly([(22, 47), (60, 47), (64, 41), (26, 41)], "#cfeee6", OUT, 1.4)
    for k, c in enumerate(("#ff8f8a", "#ffd966", "#7fb6ff", "#8fd9c8")):
        x = 74 + k * 13
        d += rect(x, 36, 10, 10, "#fbfbff", OUT, 1.4, rx=2) + rect(x + 1.5, 36.5, 7, 3.4, c, None)
    d += rect(126, 28, 14, 18, "#e6dcfa", OUT, 1.6, rx=2)  # brush jar
    for k, c in enumerate(("#ff8f8a", "#5fc9bb", "#ffd966")):
        d += line((130 + k * 3, 29), (129 + k * 4.6, 12 - k), "#a8743c", 1.6) + line((129 + k * 4.6, 13 - k), (129 + k * 4.6, 8 - k), c, 3.2)
    d += rect(148, 36, 9, 12, "#ffffff", OUT, 1.4, rx=2) + rect(150, 33, 5, 4, "#ff9a2e", OUT, 1)  # glue
    # paper chain hanging off the edge
    for k in range(6):
        d += ellipse(32 + k * 7, 66 + (k % 2) * 2, 4.2, 2.8, BUNT[k % 6], OUT, 1.2)
    for k in range(4):
        d += ellipse(152 + k * 0, 64 + k * 8, 2.8, 4.2, BUNT[(k + 2) % 6], OUT, 1.2)
    for x in (22, w - 28):  # stools
        d += ellipse(x, 100, 11, 3, INK, None, op=0.15)
    d += paper_star(100, 25, 6, BUTTER, 1.4)
    write_svg("pieces/craft_table.svg", (0, 0, w, h), d)
    return piece("craft_table", "source/pieces/craft_table.svg", (790, 192), (w, h), "none", "behind")


# ---- 5. wall clock ---------------------------------------------------------------------------------------------------------

def wall_clock():
    w = h = 40
    d = clock(20, 20, 15, rim="#7fcfc0")
    write_svg("pieces/wall_clock.svg", (0, 0, w, h), d)
    return piece("wall_clock", "source/pieces/wall_clock.svg", (347, 100), (w, h), "none", "behind")


# ---- 6. paper chains ---------------------------------------------------------------------------------------------------------

def chain_loop(x, y, c, vertical=True):
    return ellipse(x, y, 4.6, 6.4, c, OUT, 1.4) if vertical else ellipse(x, y, 6.4, 4.6, c, OUT, 1.4)


def paper_chains():
    w, h = 1280, 190
    d = ""
    for (p0, p1, sag) in (((0, 14), (300, 70), 20), ((1280, 14), (980, 70), 20), ((330, 100), (950, 100), 30)):
        pts_ = swag(p0, p1, sag, 60)
        n = int(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) / 8.2)
        for k in range(n):
            t = (k + 0.5) / n
            i = int(t * 60)
            x, y = pts_[i]
            x2, y2 = pts_[min(i + 1, 60)]
            ang = math.degrees(math.atan2(y2 - y, x2 - x))
            d += f'<g transform="rotate({f(ang)} {f(x)} {f(y)})">' + ellipse(x, y, 6.6, 4.4, BUNT[k % 6], OUT, 1.4, op=1.0) + ellipse(x, y, 3.0, 1.8, "#ffffff", None, op=0.4) + "</g>"
    # two droppers hanging from the swags
    for xx, yy in ((160, 44), (1120, 44), (640, 124)):
        for k in range(7):
            d += chain_loop(xx, yy + 8 + k * 10, BUNT[(k + 1) % 6], True)
        d += paper_star(xx, yy + 8 + 7 * 10 + 6, 8, BUTTER, 1.6)
    write_svg("pieces/paper_chains.svg", (0, 0, w, h), d)
    return piece("paper_chains", "source/pieces/paper_chains.svg", (0, 40), (w, h), "sway", "behind", pivot=(640, 0))


# ---- 7. fairy lights (additive) ---------------------------------------------------------------------------------------------

def fairy_lights():
    w, h = 680, 70
    cols = ["#ffb0d0", "#fff0a0", "#a8f0e0", "#c8b8ff", "#ffc890"]
    defs = rad_grad("gl", [(0, "#ffffff", 0.9), (0.4, "#ffffff", 0.35), (1, "#ffffff", 0.0)])
    d = ""
    for (p0, p1, sag) in (((10, 6), (340, 20), 16), ((340, 20), (670, 6), 16)):
        pts_ = swag(p0, p1, sag, 40)
        d += path(string_path(pts_), None, "#b8a8d8", 1.2, sop=0.6)
        for k in range(1, 13):
            x, y = pts_[int(k / 13 * 40)]
            c = cols[(k + (3 if p0[0] > 100 else 0)) % 5]
            d += circle(x, y + 5, 11, c, None, op=0.25) + circle(x, y + 5, 6, c, None, op=0.5) + circle(x, y + 5, 2.8, "#ffffff", None)
    write_svg("pieces/fairy_lights.svg", (0, 0, w, h), d, defs)
    return piece("fairy_lights", "source/pieces/fairy_lights.svg", (300, 40), (w, h), "flicker", "behind", "add", pivot=(w / 2, h / 2))


# ---- 8. window light (additive) -----------------------------------------------------------------------------------------------

def window_light():
    """Soft sunbeams from the two left windows slanting across the floor and the air, in warm white (drawn additively)."""
    w, h = 760, 330
    defs = lin_grad("sb", [(0, "#fff0c8", 0.2), (1, "#fff0c8", 0.0)], 0, 0, 1, 0)
    defs += lin_grad("fb", [(0, "#fff6d8", 0.0), (0.25, "#fff0c8", 0.16), (1, "#fff6d8", 0.0)], 0, 0, 1, 0)
    d = ""
    for k, (y0, ln) in enumerate(((24, 560), (70, 600))):  # shafts through the air from the window area
        d += poly([(0, y0), (ln, y0 + 150), (ln, y0 + 250), (0, y0 + 70)], "url(#sb)", None, op=1.0 if k == 0 else 0.7)
    for k, (x0, y0, wd) in enumerate(((20, 236, 140), (190, 262, 170))):  # patches on the floor in perspective
        d += poly([(x0, y0), (x0 + wd, y0), (x0 + wd + 60, y0 + 62), (x0 + 40, y0 + 62)], "url(#fb)", None, op=1.0)
        d += poly([(x0 + 12, y0 + 8), (x0 + wd - 12, y0 + 8), (x0 + wd + 36, y0 + 52), (x0 + 50, y0 + 52)], "#fff0c8", None, op=0.07)
    write_svg("pieces/window_light.svg", (0, 0, w, h), d, defs)
    return piece("window_light", "source/pieces/window_light.svg", (150, 60), (w, h), "pulse", "behind", "add", pivot=(w / 2, h / 2))


def build_pieces():
    return [notice_board(), mood_lamp(), bunting(), craft_table(), wall_clock(), paper_chains(), fairy_lights(), window_light()]
