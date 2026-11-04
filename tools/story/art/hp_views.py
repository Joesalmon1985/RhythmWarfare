"""Hospital extra views for the moving camera: `corridor`, `cafeteria` and `garden` (see tools/story/ART_CONTRACT_VIEWS.md), plus the
shared `passage_frame` sprite (a door arch the camera steps through).

Every room is a full 1280 x 720 design-space backdrop in one-point perspective drawn from the DJ's eye line, authored at 2x
(px_scale 0.5) into assets/story/hospital/source/views/. The rooms live in hp_view_corridor.py, hp_view_cafeteria.py and
hp_view_garden.py; the route is main (the private room) -> corridor -> cafeteria -> garden -> main, so the corridor's far end is a glass
door to the garden, the cafeteria's window looks onto the garden and its door leads back to the corridor, and the garden's building has the
ward's windows. `build_views()` is called from hp_stage.build_stage() and returns (views, passage_frame sprite).
"""
from __future__ import annotations

import math

from . import hp_props as P
from .hp_props import Room
from .lib import OUT, circle, clip, ellipse, f, group, line, lin_grad, path, poly, rad_grad, rect, write_svg

W, H = 1280, 720


class Room3(Room):
    """Room with world coordinates: lat = lateral offset in far-wall px (negative = left), yf = height in far-wall px, s = depth scale
    (1 = far wall, larger = nearer; the near frame is at s = vx / half)."""

    def p(self, lat, yf, s):
        return (self.vx + lat * s, self.vy + (yf - self.vy) * s)

    def s_edge(self):
        return self.vx / self.half

    def quad(self, lat0, lat1, yf0, yf1, s):
        """a frontal rectangle (facing the camera) at depth s"""
        return [self.p(lat0, yf0, s), self.p(lat1, yf0, s), self.p(lat1, yf1, s), self.p(lat0, yf1, s)]

    def side(self, lat, yf0, yf1, s0, s1):
        """a plane parallel to the side walls at lateral offset lat, between depths s0 (far) and s1 (near)"""
        return [self.p(lat, yf0, s0), self.p(lat, yf0, s1), self.p(lat, yf1, s1), self.p(lat, yf1, s0)]

    def horiz(self, yf, lat0, lat1, s0, s1):
        """a horizontal plane (floor, a table top, the ceiling) at height yf"""
        return [self.p(lat0, yf, s0), self.p(lat1, yf, s0), self.p(lat1, yf, s1), self.p(lat0, yf, s1)]

    def floor_y_at(self, s):
        return self.vy + (self.fy1 - self.vy) * s

    def box(self, lat0, lat1, yf_top, s0, s1, front, side_c, top_c, sw=2.2):
        """a box standing on the floor between depths s0 (far) and s1 (near); draws the visible side, top (if below the eye line) and front"""
        o = ""
        if lat1 <= 0:  # left of the axis: we see its right face
            o += poly(self.side(lat1, yf_top, self.fy1, s0, s1), side_c, OUT, sw)
        elif lat0 >= 0:
            o += poly(self.side(lat0, yf_top, self.fy1, s0, s1), side_c, OUT, sw)
        if yf_top > self.vy:
            o += poly(self.horiz(yf_top, lat0, lat1, s0, s1), top_c, OUT, sw)
        o += poly(self.quad(lat0, lat1, yf_top, self.fy1, s1), front, OUT, sw)
        return o


# a tiny stroke font for banners and signs (unit box 1 wide, 1.4 high)
_FONT = {
    "G": [[(1, .2), (.7, 0), (.3, 0), (0, .25), (0, 1.15), (.3, 1.4), (.7, 1.4), (1, 1.2), (1, .75), (.55, .75)]],
    "E": [[(1, 0), (0, 0), (0, 1.4), (1, 1.4)], [(0, .7), (.7, .7)]],
    "T": [[(0, 0), (1, 0)], [(.5, 0), (.5, 1.4)]],
    "W": [[(0, 0), (.25, 1.4), (.5, .6), (.75, 1.4), (1, 0)]],
    "L": [[(0, 0), (0, 1.4), (1, 1.4)]],
    "S": [[(1, .2), (.7, 0), (.3, 0), (0, .25), (.1, .6), (.9, .8), (1, 1.15), (.7, 1.4), (.3, 1.4), (0, 1.2)]],
    "O": [[(.3, 0), (.7, 0), (1, .3), (1, 1.1), (.7, 1.4), (.3, 1.4), (0, 1.1), (0, .3), (.3, 0)]],
    "N": [[(0, 1.4), (0, 0), (1, 1.4), (1, 0)]],
    "H": [[(0, 0), (0, 1.4)], [(1, 0), (1, 1.4)], [(0, .7), (1, .7)]],
    "A": [[(0, 1.4), (.5, 0), (1, 1.4)], [(.2, .95), (.8, .95)]],
    "R": [[(0, 1.4), (0, 0), (.75, 0), (1, .25), (1, .5), (.75, .72), (0, .72)], [(.55, .72), (1, 1.4)]],
    "D": [[(0, 0), (0, 1.4), (.6, 1.4), (1, 1.05), (1, .35), (.6, 0), (0, 0)]],
    "C": [[(1, .2), (.7, 0), (.3, 0), (0, .3), (0, 1.1), (.3, 1.4), (.7, 1.4), (1, 1.2)]],
    "F": [[(1, 0), (0, 0), (0, 1.4)], [(0, .7), (.7, .7)]],
    "U": [[(0, 0), (0, 1.1), (.3, 1.4), (.7, 1.4), (1, 1.1), (1, 0)]],
    "M": [[(0, 1.4), (0, 0), (.5, .8), (1, 0), (1, 1.4)]],
    "I": [[(.5, 0), (.5, 1.4)], [(.2, 0), (.8, 0)], [(.2, 1.4), (.8, 1.4)]],
    "P": [[(0, 1.4), (0, 0), (.8, 0), (1, .25), (1, .5), (.8, .72), (0, .72)]],
    "B": [[(0, 0), (0, 1.4), (.75, 1.4), (1, 1.15), (1, .95), (.75, .72), (0, .72)], [(0, 0), (.75, 0), (1, .22), (1, .5), (.75, .72)]],
    "K": [[(0, 0), (0, 1.4)], [(1, 0), (0, .8)], [(.3, .62), (1, 1.4)]],
    "Y": [[(0, 0), (.5, .75), (1, 0)], [(.5, .75), (.5, 1.4)]],
    "!": [[(.5, 0), (.5, .95)], [(.5, 1.3), (.5, 1.4)]],
}


def stroke_text(txt, x, y, h, color, sw, outline=None, gap=0.35, hspread=1.0):
    """Block letters drawn with round-capped strokes. (x, y) = the left end, vertical centre. Returns (svg, width)."""
    u = h / 1.4
    cx = x
    out = ""
    segs = []
    for ch in txt:
        if ch == " ":
            cx += u * 0.7
            continue
        for stroke in _FONT.get(ch, []):
            pts = [(cx + px * u * 0.78 * hspread, y - h / 2 + py * u) for px, py in stroke]
            segs.append(pts)
        cx += u * (0.78 * hspread + gap)
    for pts in segs:
        d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
        if outline:
            out += path(d, None, outline, sw + 3.4)
    for pts in segs:
        d = "M" + " L".join(f"{f(a)} {f(b)}" for a, b in pts)
        out += path(d, None, color, sw)
    return out, cx - x - u * gap


def view_anchors(room, vanish, **extra):
    a = {"floor_rows": room.rows(), "floor_polygon": [[room.fx0 - 10, room.fy1 + 2], [room.fx1 + 10, room.fy1 + 2],
                                                      [round(room.floor_x(room.fx1 + 10, 520)), 520], [round(room.floor_x(room.fx0 - 10, 520)), 520]],
         "floor_grid": room.grid(), "circle_centre": [640, 372], "circle_radii": [250, 46], "vanish": list(vanish), "horizon_y": room.vy,
         "wall_left_x": room.fx0, "wall_right_x": room.fx1}
    a.update(extra)
    return a


def build_passage_frame():
    """A hospital door arch seen head on, authored 640 x 360 (px_scale 0.5 x 2 spans the 1280 x 720 frame): a cream papered wall with a
    teal dado, a wooden architrave with a heart keystone and a paper-chain swag, and a wide arched opening (300 px, apex y 36) that is
    transparent. Centre pivot."""
    w, h = 640, 360
    cx = w / 2
    ow, top, bot, shoulder = 150, 36, h + 4, 130
    hole = (f"M{cx - ow} {bot} L{cx - ow} {shoulder} C{cx - ow} {top + 20} {cx - 60} {top} {cx} {top} "
            f"C{cx + 60} {top} {cx + ow} {top + 20} {cx + ow} {shoulder} L{cx + ow} {bot} Z")
    slab = f"M0 0 H{w} V{h} H0 Z {hole}"
    defs = lin_grad("slab", [(0, "#fbe9cf"), (1, "#f0cfa4")], 0, 0, 0, 1)
    defs += clip("slabclip", f'<path d="{slab}" clip-rule="evenodd"/>')
    d = f'<path d="{slab}" fill="url(#slab)" fill-rule="evenodd"/>'
    inner = ""
    for x in range(8, w, 22):
        inner += rect(x, 0, 9, h, "#ffffff", None, op=0.28)
    for x in range(16, w, 44):
        for y in (30, 70, 110):
            inner += circle(x + (11 if y == 70 else 0), y, 1.8, "#ffc9a4", None, op=0.8)
    inner += rect(0, h - 96, w, 96, "#7cc4b8")
    for x in range(0, w, 50):
        inner += rect(x + 5, h - 88, 40, 70, "#8fd2c6", "#5aa89e", 1.4, rx=3)
    inner += rect(0, h - 104, w, 8, "#fff6ea", OUT, 2)
    for k in range(5):  # little pictures and a wall lamp on the wall
        pass
    d += group(inner, 'clip-path="url(#slabclip)"')
    for xx, tone in ((52, "#ffe9a8"), (w - 52, "#ffe9a8")):  # wall lamps either side
        d += rect(xx - 10, 100, 20, 8, "#c98f55", OUT, 2, rx=2) + path(f"M{xx - 12} 100 L{xx - 7} 78 L{xx + 7} 78 L{xx + 12} 100 Z", tone, OUT, 2)
        d += circle(xx, 90, 16, "#fff0b0", None, op=0.28)
    rim = (f"M{cx - ow - 11} {bot} L{cx - ow - 11} {shoulder} C{cx - ow - 11} {top + 8} {cx - 62} {top - 12} {cx} {top - 12} "
           f"C{cx + 62} {top - 12} {cx + ow + 11} {top + 8} {cx + ow + 11} {shoulder} L{cx + ow + 11} {bot}")
    d += path(rim, None, OUT, 15) + path(rim, None, "#e2b47c", 11) + path(rim, None, "#fff2d0", 3.2, sop=0.8)
    inner_rim = (f"M{cx - ow - 1} {bot} L{cx - ow - 1} {shoulder} C{cx - ow - 1} {top + 21} {cx - 60} {top + 1} {cx} {top + 1} "
                 f"C{cx + 60} {top + 1} {cx + ow + 1} {top + 21} {cx + ow + 1} {shoulder} L{cx + ow + 1} {bot}")
    d += path(inner_rim, None, OUT, 3) + path(inner_rim, None, "#7cc4b8", 1.6)
    d += rect(cx - 17, top - 30, 34, 26, "#fff6ea", OUT, 2.4, rx=5) + P.heart_shape(cx, top - 17, 7.4, "#ff6f8f", 1.8)  # keystone
    sw = f"M{cx - ow - 30} {shoulder - 40} Q{cx} {top - 50} {cx + ow + 30} {shoulder - 40}"
    d += P.bunting((cx - ow - 26, shoulder - 34), (cx + ow + 26, shoulder - 34), 62, 13, P.PAPER, 13)
    for sx in (60, w - 60):
        d += P.balloon(sx, 36, 14, P.CORAL if sx < cx else "#ffc65a", (sx, 124), True, 2)
    write_svg("views/passage_frame.svg", (0, 0, w, h), d, defs)
    return {"file": "source/views/passage_frame.svg", "pivot": [w, h], "px_scale": 0.5,
            "note": "hospital door arch, centre pivot, 640 x 360 design px: scale 2x to span the 1280 x 720 frame; the arched opening (300 wide, apex y 36) is transparent"}


def build_views():
    from . import hp_view_cafeteria, hp_view_corridor, hp_view_garden
    views = [hp_view_corridor.build(), hp_view_cafeteria.build(), hp_view_garden.build()]
    return views, build_passage_frame()
