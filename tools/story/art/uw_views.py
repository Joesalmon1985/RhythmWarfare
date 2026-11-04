"""Underworld extra views: three more rooms of hell for the Doom-style moving camera (see tools/story/ART_CONTRACT_VIEWS.md).

`court` (obsidian court of columns and braziers leading to a throne), `pit` (lava lake, bone bridges, a stage platform out on the
lake) and `furnace` (the great forge with a demonic face in the wall), plus the shared `passage_frame` sprite. Each room is a full
1280 x 720 design-space view drawn from the DJ's eye line with its own one-point perspective (`Room`), written as SVG at 2x
(px_scale 0.5) into assets/story/underworld/source/views/. The rooms live in uw_view_court.py, uw_view_pit.py and
uw_view_furnace.py; `build_views()` is called from uw_stage.build_stage() and returns (views, passage_frame sprite).
"""
from __future__ import annotations

import math
import random

from . import uw_stage as U
from .lib import OUT, circle, clip, ellipse, f, group, line, lin_grad, path, poly, rad_grad, rect, write_svg

W, H = 1280, 720


class Room:
    """One-point perspective box: vanishing point (vx, vy), far wall rectangle fx0..fx1 x fy0..fy1 (symmetric about vx)."""

    def __init__(self, vx, vy, fx0, fx1, fy0, fy1):
        self.vx, self.vy, self.fx0, self.fx1, self.fy0, self.fy1 = vx, vy, fx0, fx1, fy0, fy1
        self.half = vx - fx0

    def scale(self, y):
        """Depth scale of the floor row y: 1 at the far wall base, growing towards the camera."""
        return (y - self.vy) / (self.fy1 - self.vy)

    def floor_x(self, xfar, y):
        return self.vx + (xfar - self.vx) * self.scale(y)

    def floor_y(self, s):
        return self.vy + (self.fy1 - self.vy) * s

    def wall(self, side, s, u):
        """Point on the left (side -1) or right (+1) wall plane at depth scale s, u far-px above the floor."""
        return (self.vx + side * self.half * s, self.vy + (self.fy1 - u - self.vy) * s)

    def rows(self, front_y=438, ys=(286, 316, 350, 390, 438)):
        return [{"y": y, "scale": round(self.scale(y) / self.scale(front_y), 3)} for y in ys]

    def grid(self, nfar=9):
        step = (self.fx1 - self.fx0) / (nfar - 1)
        return {"vanishing_point": [self.vx, self.vy], "far_y": self.fy1, "far_x": [round(self.fx0 + step * i, 1) for i in range(nfar)],
                "note": "x on the far wall base line; a floor line through far_x at screen row y is at x = vp_x + (far_x - vp_x) * (y - vp_y) / (far_y - vp_y)"}

    def floor_lines(self, zstep=0.065):
        """Screen rows of the floor's cross lines (equal spacing in depth), from the far wall to below the screen."""
        ys, z = [], 1.0
        while True:
            y = self.vy + (self.fy1 - self.vy) / z
            if y > H + 40:
                return ys
            ys.append(y)
            z -= zstep


def fanged_skull(cx, cy, r, bone=U.BONE, eye="#ff7a1a"):
    return U.skull(cx, cy, r, bone, eye, max(1.2, r * 0.16), jaw=True)


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


def ceiling_brackets(pts, tone="#7a6a76"):
    out = ""
    for (x, y) in pts:
        out += line((x, -6), (x, y), OUT, 4.4) + line((x, -6), (x, y), tone, 2)
        out += rect(x - 9, y - 4, 18, 8, "#5a4a56", OUT, 2.2, rx=2) + circle(x, y, 3, U.EMBER, OUT, 1.2)
    return out


def hanging_frame(x, y, w, h, chains, tone="#3a1a24", top=-6):
    """The dark LED-screen frame hung on chains (the runtime paints into [x+4, y+4, w-8, h-8])."""
    d = ""
    for cx_ in chains:
        d += U.chain((cx_, top), (cx_, y - 10), 9)
    d += rect(x - 12, y - 12, w + 24, h + 24, tone, OUT, 3.6, rx=8)
    d += rect(x - 7, y - 7, w + 14, h + 14, "#12060c", OUT, 2, rx=5)
    d += rect(x, y, w, h, "#06020a", None)
    d += U.neon((x - 12, y - 12), (x + w + 12, y - 12), U.EMBER, 1.2, 0.9)
    d += U.neon((x - 12, y + h + 12), (x + w + 12, y + h + 12), U.MAG, 1.2, 0.9)
    for cx_, cy_ in ((x - 6, y - 6), (x + w + 6, y - 6), (x - 6, y + h + 6), (x + w + 6, y + h + 6)):
        d += U.skull(cx_, cy_, 6.6, U.BONE, "#ff7a1a", 1.6, jaw=False)
    return d


def speaker_stack(x, ybot, w, h, side, woofers=((0.5, 0.3, 0.2), (0.5, 0.7, 0.3)), cab=("#46202c", "#1a0a16")):
    """A frontal amp cabinet standing on y=ybot; returns (svg defs, svg body, [[cx, cy, r], ...])."""
    uid = f"cab{int(x)}"
    defs = lin_grad(uid, [(0, cab[0]), (1, cab[1])], 0, 0, 0, 1)
    y0 = ybot - h
    d = rect(x, y0, w, h, f"url(#{uid})", OUT, 3.4, rx=5)
    d += rect(x, y0, w, h, "#ffffff", None, op=0.04, rx=5)
    for yy in (y0 - 1, ybot - 9):
        d += rect(x - 1, yy, w + 2, 10, "#6a5a62", OUT, 2.4, rx=3)
    for xx in (x + 7, x + w - 7):
        for yy in (y0 + 8, ybot - 14):
            d += circle(xx, yy, 3.6, "#8a7a82", OUT, 1.6)
    ws = []
    for (fx, fy, fr) in woofers:
        cx, cy, r = x + w * fx, y0 + h * fy, w * fr
        d += circle(cx, cy, r + 4, "#08020a", OUT, 2.6) + circle(cx, cy, r + 1.5, "#05010a", None)
        ws.append([round(cx, 1), round(cy, 1), round(r, 1)])
    d += poly([(x + 6, y0 + 8), (x - 2, y0 - 16), (x + 18, y0 + 2)], U.BONE, OUT, 2.0)
    d += poly([(x + w - 6, y0 + 8), (x + w + 2, y0 - 16), (x + w - 18, y0 + 2)], U.BONE, OUT, 2.0)
    d += U.skull(x + w / 2, y0 + 12, w * 0.07 + 2.5, U.BONE, "#ff7a1a", 1.4, jaw=False)
    d += line((x + 4, y0 + h * 0.2), (x + 4, y0 + h * 0.8), U.EMBER if side < 0 else U.MAG, 1.8, 0.75)
    return defs, d, ws


def build_passage_frame():
    """A hell-gate arch seen head on, authored 640 x 360 (px_scale 0.5 x 2 spans the 1280 x 720 frame): a rocky slab with a
    fanged arched opening (transparent) in the middle for the camera to fly through. Centre pivot."""
    rng = random.Random(404)
    w, h = 640, 360
    cx = w / 2
    ow, top, bot, shoulder = 150, 36, h + 4, 130  # opening half-width, arch apex, bottom, where the arch starts to curve
    hole = (f"M{cx - ow} {bot} L{cx - ow} {shoulder} C{cx - ow} {top + 20} {cx - 60} {top} {cx} {top} "
            f"C{cx + 60} {top} {cx + ow} {top + 20} {cx + ow} {shoulder} L{cx + ow} {bot} Z")
    slab = f"M0 0 H{w} V{h} H0 Z {hole}"
    defs = lin_grad("slab", [(0, "#4a2440"), (0.5, "#301630"), (1, "#4a2238")], 0, 0, 1, 1)
    defs += clip("slabclip", f'<path d="{slab}" clip-rule="evenodd"/>')
    d = f'<path d="{slab}" fill="url(#slab)" fill-rule="evenodd"/>'
    inner = ""
    for k in range(7):  # carved blocks and cracks, clipped to the slab so nothing crosses the opening
        y = 22 + k * 52
        inner += line((0, y), (w, y), "#0a0410", 2.6, 0.7)
        for j in range(9):
            x = j * 86 + (k % 2) * 43 + rng.uniform(-4, 4)
            inner += line((x, y), (x, y + 52), "#08020a", 2.0, 0.4)
    for k in range(18):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        inner += path(U.pline(U.jag((x, y), (x + rng.uniform(-30, 30), y + rng.uniform(20, 60)), 4, 7, rng)), None, "#08020a", 1.6, sop=0.6)
    for k in range(12):
        xs = rng.choice((rng.uniform(8, 100), rng.uniform(w - 100, w - 8)))
        y = rng.uniform(10, h - 40)
        inner += U.vein(U.jag((xs, y), (xs + rng.uniform(-12, 12), y + rng.uniform(30, 70)), 5, 6, rng), U.LAVA if k % 2 else U.EMBER, 1.3, 0.8)
    d += group(inner, 'clip-path="url(#slabclip)"')
    rim = (f"M{cx - ow - 9} {bot} L{cx - ow - 9} {shoulder} C{cx - ow - 9} {top + 8} {cx - 62} {top - 10} {cx} {top - 10} "
           f"C{cx + 62} {top - 10} {cx + ow + 9} {top + 8} {cx + ow + 9} {shoulder} L{cx + ow + 9} {bot}")
    d += path(rim, None, U.LAVA, 16, sop=0.14) + path(rim, None, U.LAVA, 10, sop=0.28)
    d += path(rim, None, OUT, 10) + path(rim, None, U.BONE, 6.4) + path(rim, None, "#ffffff", 1.6, sop=0.5)
    teeth = []  # (base point, unit direction into the opening, length)
    for k in range(7):
        y = bot - 30 - k * (bot - shoulder - 30) / 6.0
        teeth.append(((cx - ow, y), (1.0, 0.0), 21 + 6 * math.sin(k * 1.9)))
        teeth.append(((cx + ow, y + 12), (-1.0, 0.0), 21 + 6 * math.cos(k * 1.7)))
    for k in range(9):
        a = math.radians(180 + (k + 0.5) * 20)
        bx, by = cx + math.cos(a) * ow, shoulder + math.sin(a) * (shoulder - top) * 0.98
        teeth.append(((bx, by), (-math.cos(a), -math.sin(a)), 24 + 8 * (k % 2)))
    for (bx, by), (nx, ny), ln in teeth:
        tx, ty = -ny, nx
        a_, b_ = (bx - tx * 9, by - ty * 9), (bx + tx * 9, by + ty * 9)
        tip = (bx + nx * ln, by + ny * ln)
        mid = ((a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2)
        d += poly([a_, tip, b_], U.BONE, OUT, 2.4) + line(mid, tip, "#ffffff", 1.2, 0.5) + poly([b_, tip, mid], "#150a33", None, op=0.18)
    for sg in (-1, 1):  # great curling horns from the keystone
        d += U.UC.horn(U.UC.bez((cx + sg * 24, top - 4), (cx + sg * 110, top - 26), (cx + sg * 150, top + 40)), 20, 3, U.BONE, rings=4)
    d += fanged_skull(cx, top - 8, 22) + circle(cx - 8, top - 12, 8, "#ff7a1a", None, op=0.35) + circle(cx + 8, top - 12, 8, "#ff7a1a", None, op=0.35)
    for sx in (56, w - 56):
        for sy in (62, h - 52):
            d += fanged_skull(sx, sy, 17)
    d += U.neon((8, 8), (w - 8, 8), U.EMBER, 1.0, 0.8) + U.neon((8, h - 6), (w - 8, h - 6), U.MAG, 1.0, 0.8)
    write_svg("views/passage_frame.svg", (0, 0, w, h), d, defs)
    return {"file": "source/views/passage_frame.svg", "pivot": [w, h], "px_scale": 0.5,
            "note": "hell-gate arch, centre pivot, 640 x 360 design px: scale 2x to span the 1280 x 720 frame; the arched opening (300 wide, apex y 36) is transparent"}


def build_views():
    from . import uw_view_court, uw_view_furnace, uw_view_pit
    views = [uw_view_court.build(), uw_view_pit.build(), uw_view_furnace.build()]
    return [v for v in views if v], build_passage_frame()
