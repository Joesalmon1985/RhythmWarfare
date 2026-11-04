"""Hospital view `corridor`: a long, bright ward corridor. Teal doors with paper hearts on the left, tall sunny windows on the right, a
nurses' desk by the far glass doors that lead out to the garden, polished tiles with painted guide lines, a get-well banner hanging across
(a piece) and hanging directional signs in the front layer. The camera walks out of it towards the glass doors at the far end."""
from __future__ import annotations

import random

from . import hp_props as P
from .hp_props import CORAL, CREAM, TEAL, TEAL_D, TEAL_L, WOOD, WOOD_D, WOOD_L
from .hp_views import Room3, stroke_text, view_anchors
from .lib import OUT, circle, clip, darken, ellipse, f, group, lighten, line, lin_grad, path, poly, rad_grad, rect, write_svg

W, H = 1280, 720
R = Room3(640, 150, 470, 810, 96, 256)
SE = R.s_edge()
WALL, WALL2 = "#fbebd0", "#f0d3aa"


def sd(lat, s0, s1, yf0, yf1, fill, sw=2.0, op=None):
    return poly(R.side(lat, yf0, yf1, s0, s1), fill, OUT if sw else None, sw, op=op)


def build_backdrop():
    d, defs = "", ""
    defs += lin_grad("bg", [(0, "#fff6e6"), (1, "#f4dcc0")], 0, 0, 0, 1)
    d += rect(0, 0, W, H, "url(#bg)")
    # ceiling with troffer light panels
    defs += lin_grad("ce", [(0, "#fffaf0"), (1, "#f4e2c8")], 0, 0, 0, 1)
    d += poly(R.horiz(96, -170, 170, 1.0, SE + 0.3), "url(#ce)")
    for lat in (-170, -120, -70, -20, 20, 70, 120, 170):
        d += line(R.p(lat, 96, 1.0), R.p(lat, 96, SE + 0.3), "#e2c9a4", 1.2, 0.7)
    for s in (1.3, 1.7, 2.2, 2.9, 3.6):
        d += line(R.p(-170, 96, s), R.p(170, 96, s), "#e2c9a4", 1.2, 0.7)
    for (l0, l1) in ((-100, -40), (40, 100)):
        for (s0, s1) in ((1.12, 1.38), (1.58, 1.95), (2.25, 2.8), (3.2, 3.8)):
            q = R.horiz(96, l0, l1, s0, s1)
            d += poly(q, "#fff4c8", "#d9b57a", 1.6) + poly(q, "#ffffff", None, op=0.55)
    # side walls
    defs += lin_grad("lw", [(0, "#e6c79c"), (1, WALL)], 0, 0, 1, 0)
    defs += lin_grad("rw", [(0, WALL), (1, "#e6c79c")], 0, 0, 1, 0)
    d += poly(R.side(-170, 96, 256, 1.0, SE + 0.3), WALL)
    d += poly(R.side(170, 96, 256, 1.0, SE + 0.3), WALL)
    d += poly(R.side(-170, 96, 256, 1.0, SE + 0.3), "url(#lw)", None, op=0.0)
    d += poly(R.side(-170, 200, 256, 1.0, SE + 0.3), "#7cc4b8") + poly(R.side(170, 200, 256, 1.0, SE + 0.3), "#7cc4b8")
    for sgn in (-1, 1):
        for k in range(9):  # wainscot panel lines
            s = 1.0 + 0.4 * k * (1 + k * 0.12)
            if s < SE:
                d += line(R.p(sgn * 170, 203, s), R.p(sgn * 170, 253, s), "#5aa89e", 1.4, 0.8)
        d += poly(R.side(sgn * 170, 198, 205, 1.0, SE + 0.3), "#fff6ea", OUT, 1.6)
        d += poly(R.side(sgn * 170, 205, 209, 1.0, SE + 0.3), WOOD_L, OUT, 1.6)  # the wooden hand rail
        d += poly(R.side(sgn * 170, 250, 256, 1.0, SE + 0.3), "#fff6ea", OUT, 1.6)
    # floor: polished tiles with painted guide lines and soft reflections of the ceiling lights
    fdefs, fbody = P.tile_floor(R, "fl", c1="#e2c39a", c2="#cda27a", cell=52, line_c="#a98058", gloss=0.12)
    defs += fdefs
    d += fbody
    for lat, col in ((-122, CORAL), (122, TEAL)):  # colour-coded way-finding lines
        d += poly([R.p(lat - 5, 256, 1.0), R.p(lat + 5, 256, 1.0), R.p(lat + 5, 256, SE + 0.4), R.p(lat - 5, 256, SE + 0.4)], col, None, op=0.9)
        d += poly([R.p(lat - 1.2, 256, 1.0), R.p(lat + 1.2, 256, 1.0), R.p(lat + 1.2, 256, SE + 0.4), R.p(lat - 1.2, 256, SE + 0.4)], "#ffffff", None, op=0.5)
    for (l0, l1) in ((-100, -40), (40, 100)):
        for (s0, s1) in ((1.12, 1.38), (1.58, 1.95), (2.25, 2.8), (3.2, 3.8)):
            d += poly(R.horiz(256, l0 * 0.8, l1 * 0.8, s0 * 1.0, s1 * 1.08), "#ffffff", None, op=0.1)
    # window light patches from the right windows
    defs += lin_grad("patch", [(0, "#fff2b8", 0.0), (0.5, "#fff2b8", 0.26), (1, "#fff2b8", 0.06)], 1, 0, 0, 0)
    for (s0, s1) in ((1.1, 1.5), (1.85, 2.5), (3.0, 3.7)):
        d += poly([R.p(170, 256, s0), R.p(170, 256, s1), R.p(10, 256, s1 + 0.4), R.p(30, 256, s0 + 0.35)], "url(#patch)")
    # far wall: glass double doors to the garden, a transom, a sign
    fw = R.quad(-170, 170, 96, 256, 1.0)
    d += poly(fw, WALL, None)
    d += poly(R.quad(-170, 170, 200, 256, 1.0), "#7cc4b8", None)
    d += poly(R.quad(-170, 170, 198, 205, 1.0), "#fff6ea", OUT, 1.4)
    gd = R.quad(-50, 50, 138, 256, 1.0)
    d += poly([(gd[0][0] - 7, gd[0][1] - 7), (gd[1][0] + 7, gd[1][1] - 7), (gd[2][0] + 7, gd[2][1]), (gd[3][0] - 7, gd[3][1])], "#fff6ea", OUT, 2.6)
    wdefs, wbody = P.window_scene(gd, "gdn", sky=("#9ed8f0", "#fdf1cf"), sun_xy=(640, 170), seed=9)
    defs += wdefs
    d += wbody
    d += rect(gd[0][0], gd[0][1], 100, 118, "#ffffff", None, op=0.16)
    d += line((640, gd[0][1]), (640, 256), "#fff6ea", 3.4) + line((gd[0][0], 196), (gd[1][0], 196), "#fff6ea", 2.4)
    for k, x in enumerate((624, 656)):
        d += circle(x, 200, 2.4, "#ffe27a", OUT, 1.2)
    d += poly(R.quad(-50, 50, 112, 136, 1.0), "#dff3ef", OUT, 2) if False else ""
    d += rect(706, 158, 92, 22, "#3f8f52", OUT, 2, rx=4)
    txt, tw = stroke_text("GARDEN", 716, 169, 9, "#ffffff", 1.6)
    d += txt
    d += P.plant(500, 256, 52, "fern", "#d9734a", 3) + P.plant(782, 256, 52, "palm", "#4fb3a9", 4)
    # the nurses' desk on the left of the far doors, a coat/bench and a trolley on the right
    d += R.box(-168, -62, 205, 1.0, 1.28, "#6fb9ad", "#e0a868", "#f2d0a0", 2.4)
    top = R.horiz(205, -168, -62, 1.0, 1.28)
    d += P.bouquet(R.p(-140, 205, 1.1)[0], R.p(-140, 205, 1.1)[1], 0.55, 11)
    mon = R.p(-96, 205, 1.12)
    d += rect(mon[0] - 13, mon[1] - 26, 26, 19, "#fff6ea", OUT, 2, rx=3) + rect(mon[0] - 10, mon[1] - 23, 20, 13, "#2f4a58", None) + line((mon[0] - 7, mon[1] - 14), (mon[0] + 6, mon[1] - 14), "#7dffc0", 1.4)
    d += rect(mon[0] - 3, mon[1] - 7, 6, 6, "#a8b4c0", OUT, 1.2)
    fr = R.quad(-168, -62, 205, 256, 1.28)
    d += P.heart_shape((fr[0][0] + fr[1][0]) / 2, (fr[0][1] + fr[3][1]) / 2 + 2, 7, "#ff8f9a", 1.8)
    d += poly(R.quad(-124, -72, 160, 176, 1.0), "#fff6ea", OUT, 2) if False else ""
    d += R.box(78, 140, 214, 1.0, 1.2, "#f6e8d2", "#d9c29a", "#ffe9c4", 2.2)
    d += P.lamp_shade(R.p(110, 214, 1.1)[0], R.p(110, 214, 1.1)[1], 30, "#ffe9a8")
    # left wall doors (teal, with a frosted window, a paper heart and a number plate) at depth intervals
    for k, (s0, s1) in enumerate(((1.12, 1.4), (1.7, 2.12), (2.5, 3.1))):
        d += poly(R.side(-170, 128, 256, s0 - 0.03, s1 + 0.03), "#fff6ea", OUT, 2.2)
        d += sd(-170, s0, s1, 134, 256, "#4fb3a9", 2.4)
        sm = (s0 + s1) / 2
        dw = (s1 - s0) * 0.5
        d += poly(R.side(-170, 146, 178, sm - dw * 0.7, sm + dw * 0.7), "#e8f6f4", OUT, 1.8)
        d += poly(R.side(-170, 146, 178, sm - dw * 0.7, sm + dw * 0.1), "#ffffff", None, op=0.5)
        d += circle(*R.p(-170, 205, s1 - (s1 - s0) * 0.14), 3.0 + s1 * 0.5, "#ffe27a", OUT, 1.4)
        hp = R.p(-170, 192, sm)
        d += P.heart_shape(hp[0], hp[1], 5 + sm * 1.8, "#ff8f9a", 1.6)
        d += poly(R.side(-170, 126, 134, sm - dw * 0.4, sm + dw * 0.4), "#fff6ea", OUT, 1.6)
        d += P.star_paper(*R.p(-170, 166, sm), 0.0 + 4 + sm * 1.2, P.PAPER[(k * 2) % 7], 6) if False else ""
        # notice board between doors
    for (s0, s1) in ((1.45, 1.66), (2.18, 2.45)):
        q = R.side(-170, 152, 190, s0, s1)
        d += poly(q, "#d9a066", OUT, 2.2) + poly(R.side(-170, 156, 186, s0 + 0.01, s1 - 0.01), "#f0d4a6", OUT, 1.2)
        for j, col in enumerate(("#ff8f7a", "#9ab8f0", "#ffe27a")):
            sm = s0 + (s1 - s0) * (0.22 + j * 0.28)
            d += poly(R.side(-170, 162 + (j % 2) * 6, 176 + (j % 2) * 6, sm - 0.025, sm + 0.025), col, OUT, 1.0)
    # right wall: tall bright windows
    for k, (s0, s1) in enumerate(((1.08, 1.5), (1.82, 2.5), (2.95, 3.75))):
        q = R.side(170, 124, 220, s0, s1)
        wdefs, wbody = P.window_scene(q, f"rw{k}", sun_xy=(R.p(170, 150, (s0 + s1) / 2)[0], R.p(170, 150, (s0 + s1) / 2)[1]), seed=10 + k)
        defs += wdefs
        d += poly(R.side(170, 118, 226, s0 - 0.03, s1 + 0.03), "#fff6ea", OUT, 2.6)
        d += wbody
        sm = (s0 + s1) / 2
        d += line(R.p(170, 124, sm), R.p(170, 220, sm), "#fff6ea", 4) + line(R.p(170, 172, s0), R.p(170, 172, s1), "#fff6ea", 3.4)
        d += poly(R.side(170, 222, 230, s0 - 0.06, s1 + 0.06), "#fff6ea", OUT, 2)
        d += poly(R.side(170, 124, 220, s0, s1), "#ffffff", None, op=0.0)
        if k < 2:
            px = R.p(150, 222, sm)
            d += P.plant(px[0], px[1], 26 + sm * 10, "bushy", "#d9734a", 20 + k)
    d += poly([R.p(-170, 256, 1.0), R.p(170, 256, 1.0), R.p(170, 256, 1.0), R.p(-170, 256, 1.0)], "#000", None, op=0.0)
    # the hanging ward information board (the runtime paints into the dark panel)
    led = (540, 100, 200, 26)
    d += rect(led[0] - 7, led[1] - 6, led[2] + 14, led[3] + 12, WOOD_L, OUT, 3, rx=6) + rect(led[0] - 3, led[1] - 3, led[2] + 6, led[3] + 6, "#fff6ea", OUT, 1.8, rx=4)
    d += rect(led[0], led[1], led[2], led[3], "#22303a", None)
    # warm shading at the far corners to seat the walls
    defs += rad_grad("fg", [(0, "#fff7d8", 0.32), (1, "#fff7d8", 0.0)], 0.5, 0.5, 0.5)
    d += ellipse(640, 200, 150, 120, "url(#fg)")
    gdefs, gbody = P.grade(R, "grade")
    defs += gdefs
    d += gbody
    return write_svg("views/corridor_backdrop.svg", (0, 0, W, H), d, defs)


def build_front():
    """Over the crowd: the hanging ward signs and a bulkhead at the top, and big plants at the two near edges."""
    d, defs = "", ""
    defs += lin_grad("bk", [(0, "#fff6ea"), (1, "#e8cfa6")], 0, 0, 0, 1)
    d += rect(-4, -6, W + 8, 26, "url(#bk)", OUT, 3)
    d += line((0, 18), (W, 18), "#c98f55", 3, 0.8)
    for x0, label, col in ((190, "WARD", "#4fb3a9"), (1010, "CAFE", "#ff8f7a")):
        for dx in (14, 120):
            d += line((x0 + dx, 18), (x0 + dx, 46), OUT, 4.4) + line((x0 + dx, 18), (x0 + dx, 46), "#c9b79a", 2)
        d += rect(x0, 44, 132, 40, col, OUT, 3.2, rx=7) + rect(x0 + 4, 48, 124, 32, None, "#ffffff", 1.6, rx=5, sop=0.8)
        txt, tw = stroke_text(label, x0 + 46, 64, 15, "#ffffff", 2.4, OUT)
        d += txt
        d += P.heart_shape(x0 + 22, 64, 8, "#ffffff", 1.8) if label == "WARD" else path(f"M{x0 + 14} 64 L{x0 + 34} 64 M{x0 + 26} 56 L{x0 + 34} 64 L{x0 + 26} 72", None, "#ffffff", 3.4)
    # near-edge plants (their pots sit below the desk strip)
    d += P.plant(52, 478, 210, "palm", "#d9734a", 31, 0.8)
    d += P.plant(1232, 478, 200, "fern", "#4fb3a9", 32, 0.8)
    d += rect(1190, 300, 70, 8, "#fff6ea", None, op=0.0)
    return write_svg("views/corridor_front.svg", (0, 0, W, 470), d, defs)


def piece_banner():
    w, h = 600, 96
    d = ""
    defs = lin_grad("bn", [(0, "#fff6ea"), (1, "#f9e1c0")], 0, 0, 0, 1)
    d += path("M0 6 Q300 30 600 6", None, OUT, 4) + path("M0 6 Q300 30 600 6", None, "#fff3e0", 1.6)
    d += path("M22 12 Q300 38 578 12 L578 66 Q300 90 22 66 Z", "url(#bn)", OUT, 3.4)
    d += path("M30 17 Q300 43 570 17", None, "#ff8f7a", 2.6, sop=0.9) + path("M30 61 Q300 85 570 61", None, "#7fd1c4", 2.6, sop=0.9)
    txt, tw = stroke_text("GET WELL SOON", 60, 41, 22, "#e9715b", 4.2, "#5a2f3a", 0.38)
    off = (600 - tw) / 2 - 60 + 4
    d += f'<g transform="translate({f(off)} 6)">{txt}</g>'
    for x, y in ((40, 44), (562, 44)):
        d += P.heart_shape(x, y, 9, "#ff6f8f", 2)
    for x in (60, 150, 240, 360, 450, 540):
        yy = 66 + 12 * (1 - abs(x - 300) / 300.0) * 0 + 12 * (abs(x - 300) / 300.0 ** 1) * 0
        d += poly([(x - 6, 72), (x + 6, 72), (x, 90)], P.PAPER[(x // 30) % 7], OUT, 1.6)
    write_svg("views/corridor_banner.svg", (0, 0, w, h), d, defs)
    return P.piece("corridor_banner", "source/views/corridor_banner.svg", (340, 28), (w, h), "sway", "behind", "mix", pivot=(300, 6))


def piece_lights():
    """The ceiling troffers' warm glow and their reflections down the tiled floor."""
    w, h = 1280, 470
    d = ""
    defs = P.glow_defs("tg", "#fff2b0", 0.17)
    for (l0, l1) in ((-100, -40), (40, 100)):
        for (s0, s1) in ((1.12, 1.38), (1.58, 1.95), (2.25, 2.8), (3.2, 3.8)):
            q = R.horiz(96, l0, l1, s0, s1)
            cx = sum(p[0] for p in q) / 4
            cy = sum(p[1] for p in q) / 4
            rx = (abs(q[2][0] - q[3][0]) + 40) * 0.9
            d += ellipse(cx, cy, rx, 34 + 10 * s0, "url(#tg)")
    for (l0, l1) in ((-100, -40), (40, 100)):
        for (s0, s1) in ((1.12, 1.38), (1.58, 1.95), (2.25, 2.8)):
            q = R.horiz(256, l0 * 0.8, l1 * 0.8, s0, s1 * 1.08)
            d += poly(q, "#fff4c8", None, op=0.05)
    write_svg("views/corridor_lights.svg", (0, 0, w, h), d, defs)
    return P.piece("corridor_lights", "source/views/corridor_lights.svg", (0, 0), (w, h), "pulse", "behind", "add", pivot=(640, 150))


def piece_doorglow():
    """Garden daylight pouring in through the far glass doors."""
    w, h = 520, 330
    defs = lin_grad("ray", [(0, "#fff6c0", 0.15), (0.6, "#ffeaa0", 0.05), (1, "#ffeaa0", 0.0)], 0, 0, 0, 1)
    d = poly([(190, 0), (330, 0), (470, 330), (50, 330)], "url(#ray)")
    d += poly([(230, 0), (290, 0), (360, 330), (160, 330)], "url(#ray)")
    defs += P.glow_defs("dg", "#fff6c0", 0.22)
    d += ellipse(260, 20, 120, 60, "url(#dg)")
    rng = random.Random(31)
    for k in range(22):
        d += circle(rng.uniform(120, 400), rng.uniform(30, 300), rng.uniform(1.2, 2.6), "#fffbe0", None, op=rng.uniform(0.4, 0.9))
    write_svg("views/corridor_doorglow.svg", (0, 0, w, h), d, defs)
    return P.piece("corridor_doorglow", "source/views/corridor_doorglow.svg", (380, 138), (w, h), "pulse", "behind", "add", pivot=(260, 10))


def build():
    build_backdrop()
    build_front()
    pieces = [piece_banner(), piece_lights(), piece_doorglow()]
    anchors = view_anchors(
        R, (640, 205),
        led_screen=[540, 100, 200, 26], doorway=[590, 138, 100, 118],
        light_points=[[230, 16], [320, 36], [430, 6], [540, 0], [740, 0], [850, 6], [960, 36], [1050, 16]],
        disco_ball=None)
    anchors.pop("disco_ball")
    return {"id": "corridor", "title": "Ward corridor",
            "layers": [P.room_layer("backdrop", "views/corridor_backdrop.svg"),
                       P.room_layer("front_frame", "views/corridor_front.svg", 470, "front")],
            "anchors": anchors, "pieces": pieces, "palette_hint": "ward"}
