"""The Hospital's wall scenery as pixel props (the doors, boards and signs the old wall tiles carried, now stage sprites at 128 texels a metre).

The wall tiles are periodic (tex_hospital.py), so what makes a corridor a corridor is drawn here and placed in the map: scenery doors, notice boards, wall signs, a
hand-gel dispenser, trolleys, light bars, framed prints, a lit window. In content/story/maps/hospital.json the wall-mounted ones are wall decals (kind "decal", flat on
their wall, docs/art/WALL_DECALS.md) and the trolley and the linen cart are billboards. The doors share the language of the choice door set (assets/run/choice/hospital/, tools/run/
make_choice_art.py: steel frame #3a4a68..#d8ccb4, blue-grey leaf, wired glass in navy, a hatched kick plate) but are SCENERY: shut, dimmer, no lamp, no sign, no tape.
Same drawing helpers as hp_pix. Deterministic.
"""
from __future__ import annotations

import os

import numpy as np

from . import pixeltex as px
from .hp_pix import lit, ramp_of, save_rgba
from .tex_night_one import Sprite, box, grid2, line2, noise2, oval

FRAME = px.ramp("#18293d", "#3a4a68", "#7088a8", "#a8b8cc", "#d8ccb4")  # the choice set's frame ramp
LEAF = px.ramp("#10192a", "#34425c", "#566682", "#7a8aa6")  # its leaf, a step dimmer so scenery reads behind the choice doors
GLASS = px.ramp("#080e22", "#121d38", "#2a4060", "#5a7ea0")  # its wired glass, unlit
METAL = px.ramp("#2a3448", "#5a6a80", "#a0b0c0", "#d8e0e8")
CORK = px.ramp("#241a14", "#3a2a1e", "#56402c", "#745a3e", "#927450")
PAPER = px.ramp("#3a3a44", "#686470", "#9a9498", "#c8c0bc", "#e8e0d6")
WHITE = px.ramp("#2c3446", "#4a5670", "#7a88a4", "#aab6cc", "#d8dfec")
SIGNB = px.ramp("#0e1a34", "#183052", "#244a78", "#3a6aa0")
CLEAR = (0, 0, 0)


def _wear(w, h, seed, k=0.12):
    return (noise2(w, h, 7, seed) - 0.5) * k + (px.speckle(max(w, h), 0.08, seed + 1)[:h, :w] - 0.5) * k


def door(variant: str = "a") -> np.ndarray:
    """A scenery ward door (2.1 m, 1.05 m wide: 134 x 269 texels): steel frame, shut leaf, a narrow wired-glass light (variant a) or a plain flush leaf (b), a push plate,
    a lever handle, a hatched kick plate. Dimmer than a choice door, no lamp, no sign."""
    w, h = 134, 269
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    sp.paint(box(w, h, 0, 8, w, h), FRAME, 0.4 + lit(x, y, w, h, 0.35) * 0.8 + _wear(w, h, 11))
    sp.paint(box(w, h, 0, 8, w, 14), FRAME, 0.62)
    lx0, lx1, ly0 = 12, w - 12, 22
    leaf = box(w, h, lx0, ly0, lx1, h)
    sp.paint(leaf, LEAF, 0.45 + lit(x - lx0, y - ly0, lx1 - lx0, h - ly0, 0.3) * 0.8 + _wear(w, h, 21, 0.14))
    sp.paint(box(w, h, lx0, ly0, lx0 + 3, h), LEAF, np.full((h, w), 0.8))   # lit left arris
    sp.paint(box(w, h, lx1 - 3, ly0, lx1, h), LEAF, np.full((h, w), 0.08))  # shadowed right arris
    if variant == "a":
        gx0, gx1, gy0, gy1 = 44, 88, 52, 156
        gl = box(w, h, gx0, gy0, gx1, gy1)
        sp.paint(gl, GLASS, 0.3 + 0.35 * (y - gy0) / (gy1 - gy0) * -1 + 0.45 + (noise2(w, h, 6, 31) - 0.5) * 0.1)
        dia = (((x + y) % 12 < 1.2) | ((x - y) % 12 < 1.2)) & gl                       # the wire mesh
        sp.paint(dia, GLASS, np.full((h, w), 0.9))
        sp.paint(box(w, h, gx0 - 4, gy0 - 4, gx1 + 4, gy0) | box(w, h, gx0 - 4, gy1, gx1 + 4, gy1 + 4) | box(w, h, gx0 - 4, gy0, gx0, gy1) | box(w, h, gx1, gy0, gx1 + 4, gy1), METAL, 0.45 + 0.2 * (x < gx0 + 2))
    else:
        sp.paint(box(w, h, 34, 46, w - 34, 150), LEAF, 0.55 + lit(x - 34, y - 46, w - 68, 104, 0.2) + _wear(w, h, 41, 0.1))
        sp.paint(box(w, h, 34, 46, w - 34, 48) | box(w, h, 34, 46, 36, 150), LEAF, np.full((h, w), 0.85))
        sp.paint(box(w, h, w - 36, 46, w - 34, 150) | box(w, h, 34, 148, w - 34, 150), LEAF, np.full((h, w), 0.05))
    sp.paint(box(w, h, 24, 168, 40, 196), METAL, 0.5 + 0.3 * (x < 28))                # push plate
    sp.paint(box(w, h, 98, 150, 104, 160) | box(w, h, 98, 156, 118, 161), METAL, 0.55 + 0.3 * (y < 156))  # lever handle
    for yy in (62, 146, 220):                                                         # hinges
        sp.paint(box(w, h, 12, yy, 17, yy + 14), METAL, 0.5 + 0.3 * (x < 14))
    kick = box(w, h, lx0, h - 52, lx1, h)
    sp.paint(kick, METAL, 0.28 + 0.1 * (((x + y) % 10) < 4) + lit(x - lx0, y - h + 52, lx1 - lx0, 52, 0.15))
    sp.paint(box(w, h, lx0, h - 52, lx1, h - 50), METAL, np.full((h, w), 0.6))
    sp.edge()
    return sp.rgba()


def noticeboard() -> np.ndarray:
    """A cork notice board (0.8 m high, 1.1 m wide: 141 x 102 texels): a pale wood frame, pinned sheets, a leaflet, a rota card, pins."""
    w, h = 141, 102
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    sp.paint(box(w, h, 0, 0, w, h), FRAME, 0.35 + lit(x, y, w, h, 0.4) + _wear(w, h, 51))
    cork = box(w, h, 6, 6, w - 6, h - 6)
    sp.paint(cork, CORK, 0.45 + (noise2(w, h, 3, 52) - 0.5) * 0.35 + (px.speckle(max(w, h), 0.2, 53)[:h, :w] - 0.5) * 0.3 + lit(x - 6, y - 6, w - 12, h - 12, 0.15))
    sheets = [(12, 12, 38, 46, 0), (50, 10, 80, 38, 1), (88, 14, 128, 52, 0), (16, 56, 44, 88, 2), (56, 50, 98, 90, 0), (106, 60, 130, 90, 1)]
    for i, (x0, y0, x1, y1, kind) in enumerate(sheets):
        sp.paint(box(w, h, x0 + 2, y0 + 2, x1 + 2, y1 + 2), CORK, np.full((h, w), 0.12))  # the sheet's shadow
        pal = PAPER if kind != 2 else px.ramp("#2a4a30", "#487a50", "#6ea878", "#a0d0a0")
        if kind == 1:
            pal = px.ramp("#4a3a20", "#7a6030", "#b08a40", "#e0b860")
        sp.paint(box(w, h, x0, y0, x1, y1), pal, 0.6 + lit(x - x0, y - y0, x1 - x0, y1 - y0, 0.3) + _wear(w, h, 60 + i, 0.06))
        for r in range(int((y1 - y0 - 8) // 5)):                                     # lines of text as strokes
            ln = x1 - x0 - 8 - (r * 7 % 11)
            sp.paint(box(w, h, x0 + 4, y0 + 5 + r * 5, x0 + 4 + ln, y0 + 6 + r * 5), px.ramp("#20242e", "#3a4050"), np.full((h, w), 0.4))
        sp.col(box(w, h, (x0 + x1) // 2 - 1, y0 + 1, (x0 + x1) // 2 + 2, y0 + 4), ["#d04a3a", "#3a7ad0", "#e0b030"][i % 3])  # a pin
    sp.edge()
    return sp.rgba()


def whiteboard() -> np.ndarray:
    """The station's rota board (0.6 m high, 0.9 m wide: 115 x 77 texels): a white board in a steel frame with a grid of coloured shifts."""
    w, h = 115, 77
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    sp.paint(box(w, h, 0, 0, w, h), METAL, 0.45 + lit(x, y, w, h, 0.3))
    sp.paint(box(w, h, 4, 4, w - 4, h - 12), WHITE, 0.72 + lit(x - 4, y - 4, w - 8, h - 16, 0.12) + _wear(w, h, 71, 0.05))
    for c in range(1, 6):
        sp.paint(box(w, h, 4 + c * 17, 4, 5 + c * 17, h - 12), WHITE, np.full((h, w), 0.2))
    for r in range(1, 4):
        sp.paint(box(w, h, 4, 4 + r * 14, w - 4, 5 + r * 14), WHITE, np.full((h, w), 0.2))
    rng = np.random.RandomState(72)
    cols = ["#e2705e", "#5fb3a6", "#7e9ad8", "#e8ae48"]
    for r in range(4):
        for c in range(6):
            if rng.rand() < 0.62:
                sp.paint(box(w, h, 7 + c * 17, 7 + r * 14, 18 + c * 17, 15 + r * 14), ramp_of(cols[rng.randint(4)], 0.5, 1.15, 5), 0.5 + 0.3 * (x < 10 + c * 17))
    sp.paint(box(w, h, 10, h - 9, w - 10, h - 6), METAL, 0.3)    # the pen tray
    sp.edge()
    return sp.rgba()


def wall_sign() -> np.ndarray:
    """A wall sign over a door (0.3 m high, 0.5 m wide: 64 x 38 texels): a navy plate with an arrow and three bars of text, a pale rim."""
    w, h = 64, 38
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    sp.paint(box(w, h, 0, 0, w, h), FRAME, 0.55 + lit(x, y, w, h, 0.3))
    sp.paint(box(w, h, 3, 3, w - 3, h - 3), SIGNB, 0.55 + lit(x - 3, y - 3, w - 6, h - 6, 0.25))
    sp.col(line2(w, h, 10, 19, 26, 19, 3) | (np.abs(x - 24) + np.abs(y - 19) < 6) & (x > 18) & (x < 30), "#e8e0d0")
    for i, ln in enumerate((26, 20, 24)):
        sp.col(box(w, h, 34, 9 + i * 8, 34 + ln, 12 + i * 8), "#d8e0ec")
    sp.edge()
    return sp.rgba()


def gel_dispenser() -> np.ndarray:
    """A hand-gel dispenser (0.4 m high: 26 x 51 texels): a white body, a blue pump lever, a drip tray, a wall bracket."""
    w, h = 26, 51
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    sp.paint(box(w, h, 6, 0, 20, 4), METAL, 0.5)
    sp.paint(box(w, h, 4, 4, 22, 40), WHITE, 0.65 + lit(x - 4, y - 4, 18, 36, 0.4))
    sp.paint(box(w, h, 4, 4, 6, 40), WHITE, np.full((h, w), 0.95))
    sp.paint(box(w, h, 20, 4, 22, 40), WHITE, np.full((h, w), 0.12))
    sp.paint(box(w, h, 8, 12, 18, 26), px.ramp("#10285a", "#2250a0", "#4a82d8", "#8ab4f0"), 0.5 + lit(x - 8, y - 12, 10, 14, 0.5))
    sp.paint(box(w, h, 10, 28, 18, 32) | box(w, h, 16, 30, 24, 34), px.ramp("#10285a", "#2250a0", "#4a82d8"), 0.6)
    sp.paint(box(w, h, 5, 40, 21, 44), WHITE, 0.4)
    sp.paint(box(w, h, 8, 44, 18, 47), METAL, 0.3)
    sp.edge()
    return sp.rgba()


def trolley() -> np.ndarray:
    """A medicine trolley (1.0 m high, 0.9 m wide: 115 x 128 texels): two steel shelves on a post frame with castors, blue crates, a dish, a bottle, a chart on the top."""
    w, h = 115, 128
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    for px_ in (8, 104):
        sp.paint(box(w, h, px_, 16, px_ + 3, 116), METAL, 0.45 + 0.35 * (x < px_ + 1))
    for (y0, y1) in ((22, 28), (74, 80), (104, 110)):
        sp.paint(box(w, h, 4, y0, 111, y1), METAL, 0.5 + lit(x - 4, y - y0, 107, y1 - y0, 0.3) + (y == y0) * 0.2)
    sp.paint(box(w, h, 12, 36, 52, 74), px.ramp("#0c2048", "#1c4488", "#3a6ec0", "#78a8e8"), 0.5 + lit(x - 12, y - 36, 40, 38, 0.4))   # a crate
    sp.paint(box(w, h, 12, 44, 52, 48), px.ramp("#0c2048", "#1c4488", "#3a6ec0"), np.full((h, w), 0.2))
    sp.paint(box(w, h, 58, 50, 78, 74), WHITE, 0.6 + lit(x - 58, y - 50, 20, 24, 0.35))                                                   # a box
    sp.paint(box(w, h, 84, 40, 96, 74), px.ramp("#103a2a", "#206848", "#3a9a6a", "#8ad0a0"), 0.5 + lit(x - 84, y - 40, 12, 34, 0.5))      # a bottle
    sp.paint(box(w, h, 87, 34, 93, 40), WHITE, 0.7)
    sp.paint(box(w, h, 16, 4, 56, 22), PAPER, 0.6 + lit(x - 16, y - 4, 40, 18, 0.3))                                                     # a chart on the top shelf
    sp.paint(oval(w, h, 82, 18, 14, 4), METAL, 0.55)                                                                                      # a kidney dish
    sp.paint(box(w, h, 12, 84, 100, 104), px.ramp("#241a2c", "#3a2c48", "#5a4870"), 0.45 + lit(x - 12, y - 84, 88, 20, 0.2))              # a linen shelf
    sp.paint(box(w, h, 12, 84, 100, 88), WHITE, 0.55)
    sp.paint(box(w, h, 108, 4, 112, 22), METAL, 0.5)                                                                                      # the push handle
    for cx in (12, 102):
        sp.paint(oval(w, h, cx, 120, 6, 6), px.ramp("#0a0c14", "#1a1e2c", "#2c3244"), 0.4 + 0.4 * (np.hypot(x - cx + 2, y - 118) < 2.5))
        sp.paint(box(w, h, cx - 1, 112, cx + 2, 117), METAL, 0.5)
    sp.edge()
    return sp.rgba()


def linen_cart() -> np.ndarray:
    """A linen cart (0.9 m high, 0.8 m wide: 102 x 115 texels): a steel frame with a heap of folded sheets and one bag, on castors."""
    w, h = 102, 115
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    for px_ in (6, 92):
        sp.paint(box(w, h, px_, 30, px_ + 3, 104), METAL, 0.45 + 0.35 * (x < px_ + 1))
    sp.paint(box(w, h, 4, 96, 98, 103), METAL, 0.5 + lit(x - 4, y - 96, 94, 7, 0.3))
    for i, (y0, col) in enumerate(((78, "#aab6cc"), (62, "#9aa6c0"), (46, "#b8c4d8"))):
        sp.paint(box(w, h, 10 + i * 2, y0, 90 - i * 3, y0 + 16), px.ramp("#2a3450", "#5a6a8a", "#8a9ab8", "#c0cce0"), 0.5 + lit(x - 10, y - y0, 80, 16, 0.4) + 0.1 * (((y - y0) % 8) < 1) * -1)
    sp.paint(oval(w, h, 66, 38, 24, 16), px.ramp("#3a3a48", "#686878", "#9898a8", "#c8c8d4"), 0.5 + lit(x - 42, y - 22, 48, 32, 0.5))   # the sack
    sp.paint(box(w, h, 62, 20, 70, 26), METAL, 0.5)
    for cx in (10, 92):
        sp.paint(oval(w, h, cx, 108, 5, 5), px.ramp("#0a0c14", "#1a1e2c", "#2c3244"), 0.4 + 0.4 * (np.hypot(x - cx + 2, y - 106) < 2))
    sp.edge()
    return sp.rgba()


def light_bar() -> np.ndarray:
    """A wall light bar (0.65 m wide, 0.1 m high: 83 x 13 texels): a pale cold tube in a steel housing, dim at night (an emissive sprite)."""
    w, h = 83, 13
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    sp.paint(box(w, h, 0, 0, w, h), METAL, 0.35 + lit(x, y, w, h, 0.3))
    sp.paint(box(w, h, 3, 3, w - 3, h - 3), px.ramp("#5a7ab0", "#8aaad8", "#b8d0f0", "#e0ecfc"), 0.55 + 0.4 * (y < 6))
    sp.edge(0.8)
    return sp.rgba()


def picture() -> np.ndarray:
    """A framed print of the sea at night (0.8 m high, 1.1 m wide: 141 x 102 texels): a cream frame, indigo sky, a pixel moon, dark water with a lit path."""
    w, h = 141, 102
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    sp.paint(box(w, h, 0, 0, w, h), FRAME, 0.5 + lit(x, y, w, h, 0.4) + _wear(w, h, 81, 0.05))
    inner = box(w, h, 9, 9, w - 9, h - 9)
    t = np.clip((y - 9) / (h - 18.0), 0, 1)
    sea = t > 0.58
    sp.paint(inner & ~sea, px.ramp("#0a1230", "#14224c", "#223a74", "#3a5a9c"), 0.2 + 0.7 * t / 0.58 + (noise2(w, h, 12, 82) - 0.5) * 0.1)
    sp.paint(inner & sea, px.ramp("#050a1c", "#0c1630", "#142446", "#223a6a"), 0.3 + 0.2 * np.sin(y * 1.4 + x * 0.2) + 0.2 * (np.abs(x - 96) < 5 + (y - 60) * 0.25))
    sp.col(oval(w, h, 96, 34, 8, 8) & inner, "#e8eeff")
    sp.col(oval(w, h, 99, 36, 5, 5) & inner & (x > 96), "#b4c2e4")
    sp.col(box(w, h, 9, 9 + (h - 18) * 0.58, w - 9, 11 + (h - 18) * 0.58) & inner, "#2a4a80")
    sp.col(box(w, h, 9, 9, w - 9, 11) | box(w, h, 9, 9, 11, h - 9), "#0a1020")  # the mount's inner shadow
    sp.edge()
    return sp.rgba()


def window_lit() -> np.ndarray:
    """A large lit window (1.5 m high, 1.6 m wide: 205 x 192 texels): a white frame with a cross of mullions, warm amber light behind half-drawn curtains, a lamp and a
    plant on the sill. The room's warm window, the light of the cafeteria's far wall (an emissive sprite)."""
    w, h = 205, 192
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    sp.paint(box(w, h, 0, 0, w, h), FRAME, 0.55 + lit(x, y, w, h, 0.4))
    gl = box(w, h, 10, 10, w - 10, h - 18)
    t = np.clip((y - 10) / (h - 28.0), 0, 1)
    warm = px.ramp("#3a2214", "#6a4220", "#a4682e", "#d49a4c", "#f4cc82", "#fff0c0")
    sp.paint(gl, warm, 0.45 + 0.4 * (1 - np.hypot((x - 102) / 110.0, (y - 110) / 100.0)) + (noise2(w, h, 18, 91) - 0.5) * 0.12)
    cur = gl & ((x < 46) | (x > w - 46))                                   # curtains, folded
    sp.paint(cur, px.ramp("#2a1a3a", "#4a3260", "#6e4a8a", "#9470b0"), 0.5 + 0.3 * np.sin(x * 0.45) + lit(x, y, w, h, 0.2))
    sp.paint(box(w, h, 12, 10, w - 12, 20), px.ramp("#3a3a4a", "#6a6a80", "#a0a0b8"), 0.5)   # pelmet
    sp.paint(box(w, h, 98, 10, 108, h - 18) | box(w, h, 10, 84, w - 10, 94), FRAME, 0.55 + 0.3 * (x < 100))   # mullions
    sp.paint(oval(w, h, 130, 146, 14, 18) & gl, px.ramp("#3a2a1c", "#7a5a38", "#c09a60", "#f0d090"), 0.5 + lit(x - 116, y - 128, 28, 36, 0.6))   # a lamp
    sp.paint(box(w, h, 126, 160, 134, h - 18) & gl, METAL, 0.4)
    sp.paint(box(w, h, 0, h - 18, w, h), FRAME, 0.7 + lit(x, y - h + 18, w, 18, 0.3))                  # the sill
    sp.paint(box(w, h, 0, h - 4, w, h), FRAME, np.full((h, w), 0.15))
    sp.edge()
    return sp.rgba()


def phone() -> np.ndarray:
    """A wall telephone at the station (0.22 m high: 28 x 36 texels): a cream handset on its cradle, a coiled lead, a keypad."""
    w, h = 28, 36
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    sp.paint(box(w, h, 4, 2, 24, 34), PAPER, 0.62 + lit(x - 4, y - 2, 20, 32, 0.4))
    sp.paint(box(w, h, 8, 6, 20, 12), px.ramp("#20242e", "#3a4050"), 0.4)
    for r in range(3):
        for c in range(3):
            sp.paint(box(w, h, 9 + c * 4, 15 + r * 4, 11 + c * 4, 17 + r * 4), px.ramp("#20242e", "#5a6070"), 0.6)
    sp.paint(box(w, h, 2, 6, 6, 24) | box(w, h, 22, 6, 26, 24), PAPER, 0.45)
    sp.edge()
    return sp.rgba()


PROPS = {
    "prop_ward_door_a": lambda: door("a"), "prop_ward_door_b": lambda: door("b"), "prop_noticeboard": noticeboard, "prop_whiteboard": whiteboard, "prop_wall_sign": wall_sign,
    "prop_gel": gel_dispenser, "prop_trolley": trolley, "prop_linen_cart": linen_cart, "prop_light_bar": light_bar, "prop_picture": picture, "prop_window_lit": window_lit,
    "prop_phone": phone,
}


def write_props(out_dir: str) -> dict:
    """The wall props as processed PNGs; returns manifest sprite entries (pivot at the bottom centre, px_scale 1)."""
    os.makedirs(out_dir, exist_ok=True)
    out = {}
    for sid, fn in sorted(PROPS.items()):
        a = fn()
        save_rgba(os.path.join(out_dir, sid + ".png"), a)
        out[sid] = {"file": f"processed/{sid}.png", "pivot": [a.shape[1] / 2.0, float(a.shape[0])], "px_scale": 1.0}
    return out
