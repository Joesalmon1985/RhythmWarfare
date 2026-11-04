"""Mental Hospital extra views: three more rooms for the moving camera (see tools/story/ART_CONTRACT_VIEWS.md).

`corridor` (a long bright ward corridor with painted doors, paper stars and a tea trolley), `art_room` (easels, paint pots, hanging
paintings and a kiln) and `courtyard` (a walled garden at dusk with raised beds, a washing line of bunting and string lights), plus the
shared `passage_frame` sprite. Each room is a full 1280 x 720 design-space view with its own one-point perspective (`mh_stage.Room`),
written as SVG at 2x (px_scale 0.5) into assets/story/mental_hospital/source/views/. `build_views()` is called from
mh_stage.build_stage() and returns (views, passage_frame sprite). The rooms live in mh_views_corridor.py, mh_views_art.py and
mh_views_courtyard.py.
"""
from __future__ import annotations

import math
import random

from .lib import OUT, circle, darken, ellipse, f, group, lighten, line, lin_grad, mix, path, poly, rad_grad, rect, write_svg
from .mh_stage import (BUTTER, CORAL, CREAM, INK, LEAF, LILAC, LILAC_D, MINT, MINT_D, WOOD, WOOD_D, WOOD_L, H, W, Room, layer, paper_star,
                       piece)


def wall_quad(R, side, s0, s1, u0, u1):
    return [R.wall(side, s0, u1), R.wall(side, s1, u1), R.wall(side, s1, u0), R.wall(side, s0, u0)]


def wall_lerp(R, side, s0, s1, u0, u1, a, b):
    """Point inside the wall quad at fractions a (along depth) and b (up from u0 to u1)."""
    return R.wall(side, s0 + (s1 - s0) * a, u0 + (u1 - u0) * b)


def planks(R, tones, ncols, dz=0.07, seam="#8a6a4a", seam_op=0.35, seed=1, stagger=True, lw=1.1, zmin=0.18):
    """Floor boards in perspective: ncols columns across the far wall, rows equally spaced in depth, each board lightly tinted."""
    rng = random.Random(seed)
    d = ""
    step = (R.fx1 - R.fx0) / ncols
    rows = []
    z = 1.0
    while z > zmin:
        rows.append(1.0 / z)
        z -= dz
    cols_x = [R.fx0 + step * i for i in range(-3 * ncols, 4 * ncols + 1)]
    for ri in range(len(rows) - 1):
        s0, s1 = rows[ri], rows[ri + 1]
        y0, y1 = R.floor_y(s0), R.floor_y(s1)
        for ci in range(len(cols_x) - 1):
            xa, xb = cols_x[ci], cols_x[ci + 1]
            q = [(R.vx + (xa - R.vx) * s0, y0), (R.vx + (xb - R.vx) * s0, y0), (R.vx + (xb - R.vx) * s1, y1), (R.vx + (xa - R.vx) * s1, y1)]
            if max(p[0] for p in q) < -20 or min(p[0] for p in q) > W + 20:
                continue
            c = rng.choice(tones)
            d += poly(q, c, None)
            d += line(q[2], q[3], seam, lw, seam_op)
        # board ends are staggered by drawing the long seams in alternate rows only
    for xa in cols_x:
        d += line((R.vx + (xa - R.vx) * 1.0, R.floor_y(1.0)), (R.vx + (xa - R.vx) * 5.5, R.floor_y(5.5)), seam, lw, seam_op)
    return d


def ceiling_quad(R, xa, xb, s0, s1):
    return [R.ceil(xa, s0), R.ceil(xb, s0), R.ceil(xb, s1), R.ceil(xa, s1)]


def build_passage_frame():
    """A ward door frame seen head on, authored 640 x 360 (px_scale 0.5 x 2 spans the 1280 x 720 frame): a pastel wall slab with a
    pale timber arch-topped opening (transparent) in the middle for the camera to step through. Centre pivot."""
    rng = random.Random(404)
    w, h = 640, 360
    cx = w / 2
    ow, top, bot, shoulder = 150, 36, h + 4, 120
    hole = (f"M{cx - ow} {bot} L{cx - ow} {shoulder} C{cx - ow} {top + 12} {cx - 70} {top} {cx} {top} "
            f"C{cx + 70} {top} {cx + ow} {top + 12} {cx + ow} {shoulder} L{cx + ow} {bot} Z")
    slab = f"M0 0 H{w} V{h} H0 Z {hole}"
    defs = lin_grad("slab", [(0, "#cdeee3"), (0.55, "#bfeadf"), (1, "#a9d9cc")], 0, 0, 0, 1)
    d = f'<path d="{slab}" fill="url(#slab)" fill-rule="evenodd"/>'
    side_x = ((0, cx - ow - 11), (cx + ow + 11, w))  # decoration only on the two wall panels, never across the opening
    inner = ""
    for (xa, xb) in side_x:
        inner += rect(xa, h - 74, xb - xa, 74, LILAC, None) + rect(xa, h - 79, xb - xa, 6, lighten(LILAC, 0.4), OUT, 2)
        for x in range(int(xa) + 14, int(xb), 28):
            inner += line((x, h - 70), (x, h), darken(LILAC, 0.1), 1.2, 0.5)
        for k in range(10):  # the odd scuff, softly
            inner += ellipse(rng.uniform(xa + 12, xb - 12), rng.uniform(40, h - 90), rng.uniform(5, 12), rng.uniform(3, 7), "#ffffff", None, op=0.12)
    # a garland of paper stars across the top (clear of the arch) and stars at the jambs
    for k in range(9):
        x = 40 + k * 70
        if abs(x - cx) < ow + 40:
            continue
        inner += paper_star(x, 18 + 6 * math.sin(k), 8, [BUTTER, CORAL, "#8fd9c8", "#b9a6f0"][k % 4], 1.6)
    for xs in (66, w - 66):
        for k in range(4):
            inner += paper_star(xs + rng.uniform(-14, 14), 120 + k * 52, 7, [BUTTER, CORAL, "#8fd9c8", "#b9a6f0"][(k + 1) % 4], 1.4)
    d += inner
    rim = (f"M{cx - ow - 11} {bot} L{cx - ow - 11} {shoulder} C{cx - ow - 11} {top + 4} {cx - 72} {top - 12} {cx} {top - 12} "
           f"C{cx + 72} {top - 12} {cx + ow + 11} {top + 4} {cx + ow + 11} {shoulder} L{cx + ow + 11} {bot}")
    d += path(rim, None, OUT, 14) + path(rim, None, "#fbfbff", 10) + path(rim, None, "#ffffff", 1.6, sop=0.5)
    inner_rim = (f"M{cx - ow} {bot} L{cx - ow} {shoulder} C{cx - ow} {top + 12} {cx - 70} {top} {cx} {top} C{cx + 70} {top} {cx + ow} {top + 12} {cx + ow} {shoulder} L{cx + ow} {bot}")
    d += path(inner_rim, None, OUT, 3)
    d += rect(cx - 28, top - 26, 56, 18, "#fbfbff", OUT, 2.4, rx=4) + paper_star(cx, top - 17, 6, BUTTER, 1.4)  # keystone sign plate
    write_svg("views/passage_frame.svg", (0, 0, w, h), d, defs)
    return {"file": "source/views/passage_frame.svg", "pivot": [w, h], "px_scale": 0.5,
            "note": "ward door frame, centre pivot, 640 x 360 design px: scale 2x to span the 1280 x 720 frame; the arched opening (300 wide, apex y 36) is transparent"}


def build_views():
    from . import mh_views_art, mh_views_corridor, mh_views_courtyard
    views = [mh_views_corridor.build(), mh_views_art.build(), mh_views_courtyard.build()]
    return [v for v in views if v], build_passage_frame()
