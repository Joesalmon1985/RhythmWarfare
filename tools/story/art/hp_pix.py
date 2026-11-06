"""The Hospital's cut-outs as pixels (docs/art/VISUAL_AUDIT.md F2, F7, F15; docs/art/STYLE_GUIDE.md 6, 7 and 10).

Everything the 2D version drew as smooth SVG and the 2.5D world still shows is redrawn here at about 128 texels a metre of the size the map gives it, with palette ramps and
the 8x8 ordered dither (no partial alpha, a one-pixel darker edge, light from the upper left): the speaker (now a wheeled PA cabinet of the ward, not a target), the ceiling
spot, the paper lantern, the open door, the rear-row busts, the gifts and garlands that bloom on the beat, the big props redrawn on a finer grid, and the night sky.
Same sprite and piece ids, same design sizes and anchors as the SVGs they replace; PNGs go to the chapter's processed/ folder. Deterministic.
"""
from __future__ import annotations

import os

import numpy as np

from . import lib
from . import pixeltex as px
from . import tex_hospital as T
from .tex_night_one import Sprite, box, dmask, grid2, line2, noise2, oval, q, save_rgba

PPM = 128  # texels a metre

# ---- palettes (dark to light), the night ward's: cool plastic, black cloth, warm brass, pale paper -------------------------------------------------------------------
PLASTIC = px.ramp("#141a2c", "#202a44", "#313e60", "#46557c", "#62749c", "#8496bc")
CLOTH = px.ramp("#05070d", "#0b0f19", "#121826", "#1b2234", "#262f46")
CONE = px.ramp("#080a12", "#12182a", "#1e2740", "#2e3a5c", "#44547c", "#6a7ca8")
STEELB = px.ramp("#1a2030", "#2c3548", "#444e66", "#626e88", "#8892ac", "#b0bad2")
BRASS = px.ramp("#2a1a0c", "#4e3216", "#7a5424", "#a87a36", "#d4a854", "#f4d58a")
WOODN = px.ramp("#160e12", "#261820", "#3a2630", "#52363e", "#6e4a4c", "#8c6458")
PAPERW = px.ramp("#3a3448", "#5a526a", "#80788a", "#aaa0a4", "#d0c4bc", "#eee2d4")
CREAMN = px.ramp("#2a2230", "#4a3c48", "#725e62", "#9c8478", "#c8ae98", "#ecd4b4")
LAMPL = px.ramp("#5a3a16", "#9a6420", "#d29630", "#f4c660", "#fde8a4", "#fffaf0")
GREENP = px.ramp("#0a1a14", "#12301f", "#1e4a2c", "#2e6a3c", "#48904e", "#74b86c")
PAPERC = ["#e2705e", "#e8ae48", "#5fb3a6", "#7e9ad8", "#d98aa0", "#9cc088", "#a894d8"]  # the gifts: coral, gold, teal, blue, rose, sage, lilac, dimmed a notch for the night


def hexv(h: str) -> np.ndarray:
    return px.hexc(h)


def ramp_of(h: str, lo: float = 0.35, hi: float = 1.25, n: int = 6) -> np.ndarray:
    """A dark-to-light ramp of one colour."""
    b = px.hexc(h)
    return np.stack([np.clip(b * (lo + (hi - lo) * i / (n - 1)), 0, 1) for i in range(n)])


def lit(x, y, w, h, strength: float = 0.3):
    """Light from the upper left over a w x h sprite: +strength at the top left, -strength at the bottom right."""
    return strength * (1 - (x / max(w, 1) + y / max(h, 1)))


def _write(out_dir: str, name: str, a: np.ndarray) -> str:
    save_rgba(os.path.join(out_dir, name), a)
    return f"processed/{name}"


# ---- the sky (F7) ----------------------------------------------------------------------------------------------------------------------------------------------

def sky_strip(w: int, h: int, seed: int, moons=((0, 0),), horizon: float = 0.76) -> np.ndarray:
    """A night sky strip, tileable sideways: indigo from the zenith to the fog at the horizon in ordered dither, stars of ONE texel in three brightnesses (thicker toward the
    zenith), the moons given as (x, y) in texels (one moon: radius a thirteenth of the height, a dithered halo), a low tree line at the horizon."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    hz = horizon * h
    t = np.clip(y / hz, 0, 1)
    zen, hor = px.hexc("#050a1e"), px.hexc("#1e3064")
    rgb = zen[None, None] * (1 - t[..., None] ** 1.4) + hor[None, None] * (t[..., None] ** 1.4)
    rng = np.random.RandomState(seed)
    n_stars = int(w * h / 90)
    for i in range(n_stars):
        sx = rng.randint(0, w)
        sy = int(abs(rng.rand() ** 1.6) * hz * 0.85)
        c = ("#e8eeff", "#9aaad8", "#6678b0")[0 if i % 7 == 0 else (1 if i % 3 == 0 else 2)]
        rgb[sy, sx] = px.hexc(c)
    for (mx, my) in moons:
        r = max(h / 19.0, 3.0)
        dx = np.minimum(np.abs(x - mx), w - np.abs(x - mx))
        d = np.hypot(dx, y - my)
        halo = np.clip(1 - d / (r * 3.2), 0, 1) ** 2 * 0.55
        rgb = rgb + px.hexc("#3a5aa0")[None, None] * halo[..., None]
        moon = d <= r
        rgb[moon] = px.hexc("#e8eeff")
        shade = moon & ((dx * np.sign(x - mx) + (y - my)) > r * 0.35)
        rgb[shade] = px.hexc("#b4c2e4")
        rgb[moon & (np.hypot(dx + r * 0.3, y - my + r * 0.25) < r * 0.28)] = px.hexc("#c4d0ee")
    # a tree line: three octaves of ridge so it is ragged, darker than the fog
    cols = np.arange(w)
    ridge = 0.0
    for o, (per, amp) in enumerate(((w / 6.0, 0.035), (w / 20.0, 0.022), (w / 60.0, 0.012))):
        ridge = ridge + amp * h * np.sin(2 * np.pi * cols / per * round(w / per) / (w / per) + rng.rand() * 6.28)
    top = hz - 0.045 * h + ridge
    trees = y > top[cols][None, :]
    rgb[trees] = px.hexc("#070c1c") * (0.8 + 0.4 * (px.speckle(max(w, h), 0.2, seed + 5)[:h, :w][trees]))[:, None]
    b = px.BAYER8[np.arange(h)[:, None] % 8, np.arange(w)[None, :] % 8][..., None]
    v = np.clip(rgb, 0, 1) * 23 + b
    return (np.clip(np.round(v), 0, 23) / 23 * 255 + 0.5).astype(np.uint8)


# ---- F15: the speaker is a wheeled PA cabinet ----------------------------------------------------------------------------------------------------------------------

def spr_pa_speaker() -> np.ndarray:
    """A wheeled PA speaker of the ward (1.5 m tall, 0.75 m wide, 96 x 192): a two-way cabinet in grey-blue plastic with black grille cloth, a tweeter horn over a 12-inch
    woofer, a steel carry handle, a little control panel, on a trolley frame with four castors."""
    w, h = 96, 192
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    # trolley: two uprights, a platform under the cabinet, castors
    sp.paint(box(w, h, 10, 152, 86, 160), STEELB, 0.45 + lit(x - 10, y - 152, 76, 8, 0.4))
    sp.paint(box(w, h, 14, 160, 19, 178) | box(w, h, 77, 160, 82, 178), STEELB, 0.4 + 0.3 * (x < 16) + 0.2 * (x > 77) * -1)
    sp.paint(box(w, h, 10, 174, 86, 178), STEELB, 0.4 + lit(x - 10, y - 174, 76, 4, 0.3))
    for cx in (17, 79):
        sp.paint(oval(w, h, cx, 184, 6, 6), CLOTH, np.full((h, w), 0.45) + 0.3 * (np.hypot(x - cx + 2, y - 182) < 3))
        sp.paint(box(w, h, cx - 1, 178, cx + 2, 182), STEELB, np.full((h, w), 0.5))
    # cabinet body (rounded corners by the oval caps)
    body = box(w, h, 10, 20, 86, 152)
    n1 = noise2(w, h, 6, 811)
    sp.paint(body, PLASTIC, 0.45 + lit(x - 10, y - 20, 76, 132, 0.28) + (n1 - 0.5) * 0.12 + (px.speckle(max(w, h), 0.12, 812)[:h, :w] - 0.5) * 0.12)
    sp.paint(box(w, h, 10, 20, 13, 152), PLASTIC, np.full((h, w), 0.78))   # lit left arris
    sp.paint(box(w, h, 83, 20, 86, 152), PLASTIC, np.full((h, w), 0.12))   # shadowed right arris
    sp.paint(box(w, h, 10, 20, 86, 23), PLASTIC, np.full((h, w), 0.8))
    # grille cloth panel with a weave
    grille = box(w, h, 18, 28, 78, 126)
    weave = (((x.astype(int) + y.astype(int)) % 3) == 0) * 0.07 + (n1 - 0.5) * 0.1
    sp.paint(grille, CLOTH, 0.32 + weave + lit(x - 18, y - 28, 60, 98, 0.1))
    sp.paint(box(w, h, 18, 28, 78, 29) | box(w, h, 18, 28, 19, 126), PLASTIC, np.full((h, w), 0.55))
    sp.paint(box(w, h, 18, 125, 78, 126) | box(w, h, 77, 28, 78, 126), PLASTIC, np.full((h, w), 0.05))
    # under the cloth: the tweeter horn (top) and the woofer ring (below), seen as lit bumps
    th = oval(w, h, 48, 44, 12, 12)
    sp.paint(th, STEELB, 0.3 + lit(x - 36, y - 32, 24, 24, 0.5) * 0.9)
    sp.paint(oval(w, h, 48, 44, 6.5, 6.5), CLOTH, 0.12 + 0.5 * (np.hypot(x - 46, y - 42) < 2.2))
    wf = oval(w, h, 48, 92, 26, 26)
    sp.paint(wf & ~oval(w, h, 48, 92, 22, 22), CONE, 0.35 + lit(x - 22, y - 66, 52, 52, 0.55))
    sp.paint(oval(w, h, 48, 92, 22, 22), CLOTH, 0.22 + 0.1 * np.sin(np.hypot(x - 48, y - 92) * 0.9) + 0.0)
    sp.paint(oval(w, h, 48, 92, 9, 9), CONE, 0.3 + lit(x - 39, y - 83, 18, 18, 0.9))
    # the carry handle and the pole socket on the top, the corner guards
    sp.paint(box(w, h, 30, 10, 66, 14) | box(w, h, 30, 10, 34, 22) | box(w, h, 62, 10, 66, 22), STEELB, 0.5 + 0.3 * (y < 12) - 0.1 * (x > 62))
    sp.paint(box(w, h, 44, 20, 52, 24), CLOTH, np.full((h, w), 0.2))
    for (cx, cy) in ((12, 22), (84, 22), (12, 150), (84, 150)):
        sp.paint(box(w, h, cx - 3, cy - 3, cx + 3, cy + 3), STEELB, np.full((h, w), 0.5) + 0.2 * (x < cx))
    # control strip: a knob, three lamps (one green), a socket
    sp.paint(box(w, h, 18, 132, 78, 146), CLOTH, 0.3 + lit(x - 18, y - 132, 60, 14, 0.2))
    sp.paint(oval(w, h, 28, 139, 5, 5), STEELB, 0.45 + 0.4 * (np.hypot(x - 26, y - 137) < 2))
    sp.paint(box(w, h, 27, 135, 29, 139), CLOTH, np.full((h, w), 0.9) * 0.0 + 0.1)
    sp.col(box(w, h, 44, 137, 47, 141), "#5aff96")
    sp.col(box(w, h, 52, 137, 55, 141), "#3a4a64")
    sp.col(box(w, h, 60, 137, 63, 141), "#3a4a64")
    sp.paint(oval(w, h, 72, 139, 3.5, 3.5), CLOTH, np.full((h, w), 0.1))
    sp.edge()
    return sp.rgba()


# ---- the fixture, the lantern, the open door ---------------------------------------------------------------------------------------------------------------------

def spr_fixture() -> np.ndarray:
    """A little brass ceiling spot on a yoke, lens down (0.5 m, 44 x 62 design px: 52 x 74 texels): the cosy room's 'moving head'."""
    w, h = 52, 74
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    sp.paint(box(w, h, 14, 0, 38, 7), BRASS, 0.4 + lit(x - 14, y, 24, 7, 0.5))
    sp.paint(box(w, h, 24, 7, 28, 14), BRASS, np.full((h, w), 0.35))
    yoke = box(w, h, 6, 14, 46, 18) | box(w, h, 6, 14, 10, 44) | box(w, h, 42, 14, 46, 44)
    sp.paint(yoke, BRASS, 0.5 + 0.3 * (x < 9) - 0.15 * (x > 43))
    can = box(w, h, 12, 20, 40, 62)
    sp.paint(can, BRASS, 0.42 + 0.45 * np.clip(1 - (x - 12) / 28.0, 0, 1) - 0.2 * (x > 33) + 0.1 * (((y - 20) % 8) < 1))
    sp.paint(box(w, h, 12, 56, 40, 61), BRASS, 0.55 + lit(x - 12, y - 56, 28, 5, 0.3))
    sp.paint(oval(w, h, 26, 66, 14, 5), CLOTH, np.full((h, w), 0.15))
    sp.paint(oval(w, h, 26, 66, 11, 3.6), LAMPL, 0.6 + 0.4 * (np.hypot(x - 22, (y - 66) * 2.6) < 5))
    sp.paint(oval(w, h, 8, 36, 3, 3) | oval(w, h, 44, 36, 3, 3), BRASS, np.full((h, w), 0.8))
    sp.edge()
    return sp.rgba()


def spr_lantern() -> np.ndarray:
    """The 'mirror ball' of the room: a paper-star lantern hanging on its ribbon (design 114 x 290 at 0.5 px: 58 x 148 texels), a glowing core inside folded paper points,
    a little ribbon bow under it."""
    w, h = 58, 148
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    cx, cy, R = 28.5, 88.0, 16.0
    sp.paint(box(w, h, 28, 0, 30, cy - R - 4) & ((y % 4) < 3), CREAMN, 0.5 + 0.3 * (x < 29))
    ang = np.arctan2(y - cy, x - cx)
    r = np.hypot(x - cx, y - cy)
    # folded paper points: a 12-point star, alternating tones, lit from the upper left
    k = 12
    spike = (R + 11) * (0.6 + 0.4 * np.abs(np.cos(ang * k / 2.0))) ** 1.5
    star = r <= spike
    tone = 0.45 + 0.35 * (np.floor((ang + np.pi) / (2 * np.pi) * k) % 2) + lit(x, y, w, h, 0.25) * 0.8
    sp.paint(star & (r > R - 4), CREAMN, tone)
    sp.paint(r <= R - 2, LAMPL, 0.55 + 0.4 * np.clip(1 - r / (R - 2), 0, 1) + 0.1 * (np.hypot(x - cx + 4, y - cy + 4) < 3))
    sp.paint(box(w, h, 25, cy + R + 9, 32, cy + R + 14), CREAMN, np.full((h, w), 0.55))
    sp.paint(box(w, h, 22, cy + R + 14, 28, cy + R + 22) | box(w, h, 29, cy + R + 14, 35, cy + R + 22), ramp_of("#d98aa0"), 0.6 + lit(x, y - 100, w, 30, 0.3))
    sp.edge()
    return sp.rgba()


def spr_door_open() -> np.ndarray:
    """The door thrown open (design 150 x 222 at size 2.0 m: 173 x 256 texels): a pale frame, the warm corridor beyond, a visitor back-lit with a balloon, the leaf swung in
    on the left, a heart over the door."""
    w, h = 173, 256
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    k = w / 150.0
    fx0, fx1, fy0, fy1 = 6 * k, 144 * k - 1, 36 * k, h - 4
    sp.paint(box(w, h, fx0 - 6, fy0 - 8, fx1 + 6, fy1 + 1), PAPERW, 0.35 + lit(x - fx0, y - fy0, fx1 - fx0, fy1 - fy0, 0.3))
    room = box(w, h, fx0, fy0, fx1, fy1)
    t = np.clip((y - fy0) / (fy1 - fy0), 0, 1)
    sp.paint(room, LAMPL, 0.62 + 0.3 * t + (noise2(w, h, 14, 821) - 0.5) * 0.12)
    sp.paint(room & (y > fy0 + (fy1 - fy0) * 0.55) & (x > fx0 + 14) & (x < fx1 - 14), PAPERW, 0.6)   # the far lit floor
    # the visitor
    vx = (fx0 + fx1) / 2 + 8
    body = (np.abs(x - vx) < 15 - 0.0 * y) & (y > fy1 - 70) & room
    body |= oval(w, h, vx, fy1 - 82, 9, 10) | box(w, h, vx - 3, fy1 - 74, vx + 3, fy1 - 66)
    sp.paint(body, px.ramp("#1a1226", "#2a1c36", "#3a2846"), 0.4 + lit(x - vx + 15, y - fy1 + 70, 30, 70, 0.3))
    sp.col(line2(w, h, vx + 13, fy1 - 50, vx + 22, fy1 - 92, 1.2), "#ece0d0")
    sp.paint(oval(w, h, vx + 23, fy1 - 104, 10, 12), ramp_of("#e2705e"), 0.5 + lit(x - vx - 13, y - fy1 + 92, 20, 24, 0.7))
    # the leaf swung in (a trapezoid on the left), a door handle
    leaf = np.zeros((h, w), bool)
    lx0, lx1 = fx0, fx0 + 22
    top0, top1 = fy0, fy0 + 12
    bot0, bot1 = fy1, fy1 - 8
    ty = top0 + (top1 - top0) * np.clip((x - lx0) / (lx1 - lx0), 0, 1)
    by = bot0 + (bot1 - bot0) * np.clip((x - lx0) / (lx1 - lx0), 0, 1)
    leaf = (x >= lx0) & (x < lx1) & (y >= ty) & (y < by)
    sp.paint(leaf, WOODN, 0.55 + 0.3 * (x < lx0 + 3) - 0.2 * (x > lx1 - 4) + (noise2(w, h, 5, 822) - 0.5) * 0.2)
    sp.col(box(w, h, lx1 - 7, fy0 + (fy1 - fy0) * 0.5, lx1 - 4, fy0 + (fy1 - fy0) * 0.5 + 4), "#e8c870")
    # a sign above the door with a heart
    sp.paint(box(w, h, fx0 + 22, fy0 - 40, fx1 - 22, fy0 - 14), PAPERW, 0.45 + lit(x - fx0 - 22, y - fy0 + 40, fx1 - fx0 - 44, 26, 0.3))
    hx, hy = (fx0 + fx1) / 2, fy0 - 27
    heart = (np.hypot(x - hx + 3, y - hy + 2) < 4.2) | (np.hypot(x - hx - 3, y - hy + 2) < 4.2) | ((np.abs(x - hx) + (y - hy)) < 7) & (y >= hy)
    sp.paint(heart & (y < hy + 8), ramp_of("#e2506e"), 0.55 + 0.3 * (np.hypot(x - hx + 2, y - hy + 1) < 2))
    sp.edge()
    return sp.rgba()


# ---- rear-row busts (the old purple and pink seated blobs) ---------------------------------------------------------------------------------------------------------

SIL_SCALE = 128.0 / 52.0  # design units per pixel of a rear silhouette: busts at the baked people's grain


def spr_silhouette(kind: str, up: bool) -> np.ndarray:
    """A rear-row figure from behind (head and shoulders, the old SVG shapes' sizes): a dark navy-plum dithered toward the fog, the hair's own shape, a one pixel rim of corridor
    amber on the left and moonlight blue on the right, arms up on the drop."""
    s = 1.0 / SIL_SCALE
    w = 52
    h = 59 if up else 47
    top = 140 if up else 112
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    X = (x + 0.5) / s - 64.0
    Y = (y + 0.5) / s - top
    sw = {"a": 38, "b": 30, "c": 44}[kind]
    hr = {"a": (16, 19), "b": (14, 17), "c": (18, 20)}[kind]
    torso = (Y > -50) & (Y < 4) & (np.abs(X) < sw - 6 * np.clip((Y + 50) / -1.0, 0, 1) - 8 * np.clip(-(Y + 26) / 24.0, 0, 1))
    neck = (np.abs(X) < 9) & (Y > -60) & (Y <= -46)
    head = ((X / hr[0]) ** 2 + ((Y + 74) / hr[1]) ** 2) <= 1.0
    if kind == "a":
        hair = ((X / (hr[0] + 1)) ** 2 + ((Y + 79) / (hr[1] - 2)) ** 2 <= 1.0) & (Y < -74)
        hair |= (((X) / 9) ** 2 + ((Y + 94) / 8) ** 2 <= 1.0)  # the bun
    elif kind == "b":
        hair = (((X - 1) / 8) ** 2 + ((Y + 94) / 8) ** 2 <= 1.0) | ((X > 6) & (X < 22) & (Y > -82) & (Y < -50 - (X - 6) * 0.5))
    else:
        hair = ((Y < -78) & (Y > -102) & (np.abs(X) < 20)) | ((Y > -82) & (Y < -74) & (X < -16) & (X > -38))
    arms = np.zeros_like(head)
    if up:
        for sd in (-1, 1):
            ax0, ay0, ax1, ay1 = sd * 26, -40, sd * 48, -116
            dx, dy = ax1 - ax0, ay1 - ay0
            t = np.clip(((X - ax0) * dx + (Y - ay0) * dy) / (dx * dx + dy * dy), 0, 1)
            arms |= np.hypot(X - (ax0 + t * dx), Y - (ay0 + t * dy)) < 6.5
            arms |= np.hypot(X - ax1 * 1.02, Y - ay1 - 4) < 7
    body = torso | neck | head | hair | arms
    SIL = px.ramp("#0c1024", "#131a34", "#1b2444", "#252f56")
    spk = px.speckle(64, 0.2, 421 + ord(kind))[:h, :w]
    sp.paint(body, SIL, 0.3 + 0.3 * np.clip(-(Y + 20) / 80.0, 0, 1) + (spk - 0.5) * 0.28)
    sp.paint(hair, SIL, np.full((h, w), 0.05))
    left = body & ~np.roll(body, 1, 1)
    right = body & ~np.roll(body, -1, 1)
    topr = body & ~np.roll(body, 1, 0)
    sp.col(left | (topr & (X < 0)), "#b8904a")
    sp.col(right | (topr & (X >= 0)), "#5a78c0")
    return sp.rgba()


# ---- the gifts and garlands that bloom on the beat (pieces, `mix`) --------------------------------------------------------------------------------------------------

def _catenary(w, h, x0, x1, y0, depth):
    """y of a rope sagging `depth` between x0 and x1 at the ends' height y0 (a parabola, like the SVG's quadratic)."""
    u = np.clip((np.arange(w) - x0) / max(x1 - x0, 1), 0, 1)
    return y0 + 4 * depth * u * (1 - u)


def _rope(sp, w, h, x0, x1, y0, depth, pal=CREAMN, wd=1.2):
    x, y = grid2(w, h)
    yy = _catenary(w, h, x0, x1, y0, depth)
    m = (np.abs(y - yy[None, :]) < wd * 0.5 + 0.35) & (x >= x0) & (x <= x1)
    sp.paint(m, pal, np.full((h, w), 0.45))
    return yy


def _heart(x, y, cx, cy, s):
    a = (np.hypot(x - cx + s * 0.5, y - cy + s * 0.35) < s * 0.62) | (np.hypot(x - cx - s * 0.5, y - cy + s * 0.35) < s * 0.62)
    b = (np.abs(x - cx) * 1.0 + (y - cy)) < s * 1.15
    return a | (b & (y >= cy))


def piece_balloons() -> np.ndarray:
    """Six balloons on strings to a weight (design 140 x 210, size 1.8 m: 154 x 230 texels)."""
    w, h = 154, 230
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    k = w / 140.0
    anchor = (70 * k, 196 * k)
    pos = [(40, 44, 22), (96, 52, 21), (68, 22, 20), (24, 96, 19), (112, 100, 20), (68, 78, 21)]
    for i, (cx, cy, r) in enumerate(pos):
        cx, cy, r = cx * k, cy * k, r * k
        sp.col(line2(w, h, cx, cy + r * 1.1, anchor[0], anchor[1], 1.1), "#d8ccc0")
    for i, (cx, cy, r) in enumerate(pos):
        cx, cy, r = cx * k, cy * k, r * k
        m = ((x - cx) / (r * 0.86)) ** 2 + ((y - cy) / r) ** 2 <= 1.0
        sp.paint(m, ramp_of(PAPERC[i % 6], 0.4, 1.3), 0.55 + 0.45 * np.clip(1 - np.hypot(x - cx + r * 0.3, y - cy + r * 0.35) / r, 0, 1) - 0.15 * (np.hypot(x - cx - r * 0.3, y - cy - r * 0.3) / r))
        sp.col(oval(w, h, cx - r * 0.35, cy - r * 0.42, r * 0.14, r * 0.2), "#f4ece4")
        sp.paint(box(w, h, cx - 2, cy + r - 1, cx + 3, cy + r + 4), ramp_of(PAPERC[i % 6], 0.4, 1.0), np.full((h, w), 0.4))
    sp.paint(box(w, h, 52 * k, 190 * k, 88 * k, 206 * k), ramp_of("#d98aa0"), 0.5 + lit(x - 52 * k, y - 190 * k, 36 * k, 16 * k, 0.4))
    sp.edge()
    return sp.rgba()


def _hung(sp, w, h, pts, draw_fn):
    for i, (px_, py_) in enumerate(pts):
        draw_fn(sp, i, px_, py_)


def piece_cards() -> np.ndarray:
    """A garland of get-well cards on a string (design 720 x 74, size 0.8 m: 995 x 102 texels)."""
    w, h = 995, 102
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    k = w / 720.0
    yy = _rope(sp, w, h, 0, w - 1, 5, 80)
    n = 13
    rng = np.random.RandomState(8)
    for i in range(n):
        cx = (i + 0.5) / n * w
        cy = float(yy[int(cx)]) + 24
        cw, ch = 24 * k * 0.9, 30 * k * 0.9
        ang = rng.uniform(-0.12, 0.12)
        u = (x - cx) * np.cos(ang) + (y - cy) * np.sin(ang)
        v = -(x - cx) * np.sin(ang) + (y - cy) * np.cos(ang)
        m = (np.abs(u) < cw / 2) & (np.abs(v) < ch / 2)
        sp.paint(m, ramp_of(PAPERC[i % 7], 0.45, 1.25), 0.6 + lit(u + cw / 2, v + ch / 2, cw, ch, 0.35))
        kind = i % 4
        if kind == 0:
            sp.col(_heart(u, v, 0, 1, 5.5) & m, "#e2506e")
        elif kind == 1:
            sp.col((np.abs(u) < 1.6) & (np.abs(v) < 8) & m | (np.abs(v) < 1.6) & (np.abs(u) < 8) & m, "#f4ece4")
        elif kind == 2:
            sp.col((np.hypot(u, v + 3) < 5) & m, "#f4d870")
            sp.col((np.abs(u) < 1) & (v > 2) & (v < 10) & m, "#4a8a4a")
        else:
            sp.col(((np.abs(v - 4 * np.sin(u * 0.5)) < 1.2) & (np.abs(u) < 8)) & m, "#f4ece4")
        sp.col(box(w, h, cx - 1, cy - ch / 2 - 3, cx + 1, cy - ch / 2) & (y > yy[int(cx)]), "#d8ccc0")
    sp.edge()
    return sp.rgba()


def piece_monitor() -> np.ndarray:
    """A get-well heart monitor, a toy-bright one (design 64 x 58, size 0.6 m: 85 x 77 texels): cream casing, a trace on a dark screen, a heart."""
    w, h = 85, 77
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    k = w / 64.0
    sp.paint(box(w, h, 6 * k, 4 * k, 58 * k, 46 * k), PAPERW, 0.5 + lit(x - 6 * k, y - 4 * k, 52 * k, 42 * k, 0.4))
    sp.paint(box(w, h, 11 * k, 9 * k, 53 * k, 36 * k), px.ramp("#07140f", "#0a2018", "#0e2c22"), 0.4 + 0.2 * (y < 14 * k))
    tr = [(13, 27), (21, 27), (24, 19), (28, 35), (32, 23), (35, 27), (51, 27)]
    for (ax, ay), (bx, by) in zip(tr[:-1], tr[1:]):
        sp.col(line2(w, h, ax * k, ay * k, bx * k, by * k, 1.5), "#7dffc0")
    sp.col(_heart(x, y, 45 * k, 17 * k, 3.2 * k), "#ff8f9a")
    sp.col(box(w, h, 13 * k, 13 * k, 15 * k, 15 * k), "#f4d870")
    sp.col(box(w, h, 18 * k, 13 * k, 20 * k, 15 * k), "#7dffc0")
    sp.paint(box(w, h, 26 * k, 46 * k, 38 * k, 51 * k), STEELB, 0.6)
    sp.paint(box(w, h, 16 * k, 51 * k, 48 * k, 57 * k), STEELB, 0.55 + lit(x - 16 * k, y - 51 * k, 32 * k, 6 * k, 0.3))
    sp.edge()
    return sp.rgba()


def piece_vase() -> np.ndarray:
    """A vase of flowers (design 64 x 92, size 0.7 m: 64 x 90 texels): a glass vase, green stems, six blooms."""
    w, h = 64, 90
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    cx = 32.0
    sp.paint(box(w, h, 20, 60, 44, 88) & (np.abs(x - cx) < 12 + 5 * np.sin((y - 60) / 28 * np.pi)), px.ramp("#143a44", "#24606a", "#3a8a92", "#74c0c4"), 0.4 + lit(x - 20, y - 60, 24, 28, 0.5))
    sp.col(box(w, h, 22, 68, 24, 82), "#bfe8e8")
    for ang, ln in ((-0.5, 40), (-0.2, 46), (0.0, 50), (0.25, 44), (0.55, 38)):
        sp.col(line2(w, h, cx, 66, cx + np.sin(ang) * ln, 66 - np.cos(ang) * ln, 1.4), "#3e7a46")
    for i, (ang, ln, col) in enumerate(((-0.5, 40, "#e2705e"), (-0.2, 46, "#e8ae48"), (0.0, 50, "#d98aa0"), (0.25, 44, "#e8ae48"), (0.55, 38, "#e2705e"))):
        bx, by = cx + np.sin(ang) * ln, 66 - np.cos(ang) * ln
        for a in range(6):
            sp.paint(oval(w, h, bx + np.cos(a * 1.047) * 4.2, by + np.sin(a * 1.047) * 4.2, 3.4, 3.4), ramp_of(col, 0.5, 1.2), 0.5 + 0.4 * (a < 3))
        sp.col(oval(w, h, bx, by, 2.2, 2.2), "#f4d870")
    sp.edge()
    return sp.rgba()


def piece_paper_stars() -> np.ndarray:
    """Paper stars hanging on thread (design 700 x 150, size 1.2 m: 717 x 154 texels): eight folded stars."""
    w, h = 717, 154
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    k = w / 700.0
    stars = [(36, 66, 22, 0), (112, 108, 27, 1), (196, 52, 19, 2), (262, 92, 24, 3), (440, 84, 24, 4), (516, 46, 19, 5), (588, 112, 27, 6), (664, 70, 22, 0)]
    for (sx, sy, r, c) in stars:
        sx, sy, r = sx * k, sy * k, r * k
        sp.col(box(w, h, sx - 0.5, 0, sx + 1, sy - r * 0.5), "#d8ccc0")
        ang = np.arctan2(y - sy, x - sx)
        rr = np.hypot(x - sx, y - sy)
        spike = r * (0.5 + 0.5 * np.abs(np.cos(ang * 4.0))) ** 1.2
        m = rr <= np.maximum(spike, r * 0.42)
        half = (np.floor((ang + np.pi) / (2 * np.pi) * 16) % 2) == 0
        sp.paint(m, ramp_of(PAPERC[c % 7], 0.45, 1.3), 0.5 + 0.3 * half + lit(x - (sx - r), y - (sy - r), 2 * r, 2 * r, 0.3))
    sp.edge()
    return sp.rgba()


def piece_fairy_lights() -> np.ndarray:
    """Two strings of fairy lights (design 1280 x 96, size 0.5 m: 853 x 64 texels): bulbs of five colours, a warm lit core each."""
    w, h = 853, 64
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    k = w / 1280.0
    cols = ["#ffe27a", "#ff9f8a", "#9fe8d4", "#f4a5b4", "#ffd23f"]
    for (x0, x1) in ((0, 560), (720, 1280)):
        x0, x1 = x0 * k, x1 * k - 1
        yy = _rope(sp, w, h, x0, x1, 12, 38, STEELB, 1.2)
        n = 17
        for i in range(n):
            cx = x0 + (i + 0.5) / n * (x1 - x0)
            cy = float(yy[int(cx)]) + 6
            sp.paint(box(w, h, cx - 1.5, cy - 4, cx + 2, cy - 1), WOODN, np.full((h, w), 0.5))
            sp.paint(oval(w, h, cx, cy + 3, 3.2, 4.6), ramp_of(cols[i % 5], 0.5, 1.4), 0.6 + 0.4 * (np.hypot(x - cx + 1, y - cy - 2) < 1.8))
    sp.edge(0.8)
    return sp.rgba()


def piece_banner() -> np.ndarray:
    """The corridor's welcome banner (design 600 x 96, size 0.5 m: 400 x 64 texels): a sagging cream banner with a coral and a teal stripe, two hearts, six paper pennants."""
    w, h = 400, 64
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    k = w / 600.0
    yc = 4 + 14 * k * (1 - ((np.arange(w) - w / 2) / (w / 2)) ** 2)
    top, bot = yc + 4, yc + 44 * k
    cloth = (y >= top[None, :]) & (y <= bot[None, :]) & (x >= 14 * k) & (x <= w - 14 * k)
    sp.paint(cloth, CREAMN, 0.55 + lit(x, y - top[None, :], w, 40, 0.3) + (noise2(w, h, 8, 831) - 0.5) * 0.1)
    sp.col(cloth & (y >= top[None, :] + 4 * k) & (y < top[None, :] + 8 * k), "#e2705e")
    sp.col(cloth & (y <= bot[None, :] - 4 * k) & (y > bot[None, :] - 8 * k), "#5fb3a6")
    for hx in (26, 574):
        hy = float(yc[int(hx * k)]) + 4 + 22 * k
        sp.col(_heart(x, y, hx * k, hy, 4.5 * k) & cloth, "#e2506e")
    # a row of dots in place of lettering (no text in the picture): a light stitched line down the middle
    mid = (top + bot) / 2
    sp.col(cloth & (np.abs(y - mid[None, :]) < 1) & ((x.astype(int) % 6) < 3) & (x > 60 * k) & (x < w - 60 * k), "#7a5a52")
    for i, px_ in enumerate((60, 150, 240, 360, 450, 540)):
        cx = px_ * k
        by = float(bot[int(cx)]) + 1
        tri = (np.abs(x - cx) < 6 * k * np.clip(1 - (y - by) / (18 * k), 0, 1)) & (y >= by) & (y < by + 18 * k)
        sp.paint(tri, ramp_of(PAPERC[i % 7], 0.45, 1.25), 0.6 + lit(x - cx + 6 * k, y - by, 12 * k, 18 * k, 0.3))
    sp.edge()
    return sp.rgba()


def piece_lamps() -> np.ndarray:
    """Four pendant lamps on cords (design 720 x 130, size 0.8 m: 399 x 102 texels): coloured shades, a lit rim and bulb."""
    w, h = 399, 102
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    k = w / 720.0
    for (px_, col, py_) in ((80, "#e2705e", 74), (250, "#5fb3a6", 90), (470, "#e8ae48", 86), (640, "#d98aa0", 76)):
        cx, cy = px_ * k, py_ * k * 0.9
        sp.paint(box(w, h, cx - 0.5, 0, cx + 1, cy - 8), CREAMN, np.full((h, w), 0.5))
        dome = ((np.abs(x - cx) < 15 * k) & (y > cy - 14) & (y < cy + 8)) & (((x - cx) / (15 * k)) ** 2 + ((y - cy + 14 - 0) / 22.0) ** 2 <= 1.0) | ((np.abs(x - cx) < 15 * k) & (y >= cy - 4) & (y < cy + 8))
        sp.paint(dome, ramp_of(col, 0.4, 1.3), 0.55 + lit(x - cx + 15 * k, y - cy + 14, 30 * k, 22, 0.5))
        sp.paint(box(w, h, cx - 15 * k, cy + 6, cx + 15 * k, cy + 9), LAMPL, np.full((h, w), 0.8))
        sp.paint(oval(w, h, cx, cy + 11, 5, 2.4), LAMPL, np.full((h, w), 0.95))
    sp.edge()
    return sp.rgba()


def piece_bunting() -> np.ndarray:
    """Garden bunting along three swags (design 1280 x 120, size 0.55 m: 586 x 70 texels): paper pennants on a string."""
    w, h = 586, 70
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    k = w / 1280.0
    swags = ((0, 420, 41, 14), (420, 860, 36, 8), (860, 1280, 41, 14))
    n = 0
    for (a, b, y0, depth) in swags:
        a, b = a * k, b * k - 1
        yy = _rope(sp, w, h, a, b, y0 * k * 1.2, depth * 1.6, CREAMN, 1.2)
        m = 14
        for i in range(m):
            cx = a + (i + 0.5) / m * (b - a)
            cy = float(yy[int(cx)])
            tri = (np.abs(x - cx) < 6.5 * np.clip(1 - (y - cy) / 18.0, 0, 1)) & (y >= cy) & (y < cy + 18)
            sp.paint(tri, ramp_of(PAPERC[(i + n) % 7], 0.45, 1.25), 0.6 + lit(x - cx + 6, y - cy, 13, 18, 0.3))
        n += 3
    sp.edge()
    return sp.rgba()


def piece_petals() -> np.ndarray:
    """Petals drifting in the lamp light (design 520 x 300, size 2.0 m: 443 x 256 texels): 34 petals of five colours, a pixel or three each."""
    w, h = 443, 256
    sp = Sprite(w, h)
    x, y = grid2(w, h)
    rng = np.random.RandomState(23)
    cols = ["#d98aa0", "#f0c4cc", "#ece4e0", "#e8ae48", "#e2706e"]
    for i in range(34):
        cx, cy, a = rng.uniform(6, w - 6), rng.uniform(6, h - 6), rng.uniform(0, np.pi)
        rx, ry = rng.uniform(2.2, 3.6), rng.uniform(1.3, 2.0)
        u = (x - cx) * np.cos(a) + (y - cy) * np.sin(a)
        v = -(x - cx) * np.sin(a) + (y - cy) * np.cos(a)
        m = (u / rx) ** 2 + (v / ry) ** 2 <= 1.0
        sp.paint(m, ramp_of(cols[i % 5], 0.55, 1.2, 4), 0.35 + 0.5 * (u < 0))
    return sp.rgba()


# ---- the big props on a finer grid (same drawings, same ids: k times the pixels so 100 to 140 texels a metre at the map's size) ------------------------------------------

GRAIN = {"thing_door_lit": 0.07, "thing_desk": 0.06, "thing_bed": 0.05, "wall_vending": 0.04, "wall_tv": 0.03}  # fine wear on the flat-painted props


def big_prop(tid: str) -> np.ndarray:
    """A th_* drawing on its k-times finer grid, then the sprite finish of the style guide (section 6): a one pixel edge a step darker than its colour, and a fine grain
    on the flat paint (ordered dither, 24 levels) so a door or a desk at arm's length is not one flat block."""
    fn, k = T.BIG[tid]
    a = fn(k).copy()
    opaque = a[..., 3] > 0
    g = GRAIN.get(tid, 0.0)
    if g > 0:
        n = a.shape[0]
        f = (px.noise(n, 3.0, 901 + len(tid), 2) - 0.5) * 2 * g + (px.speckle(n, 0.04, 902) - px.speckle(n, 0.04, 903)) * g * 1.2
        rgb = np.clip(a[..., :3].astype(np.float32) / 255.0 * (1.0 + f)[..., None], 0, 1)
        d = T.dith(rgb, 24)
        a[..., :3] = np.where(opaque[..., None], d, a[..., :3])
    rim = opaque & ~(np.roll(opaque, 1, 0) & np.roll(opaque, -1, 0) & np.roll(opaque, 1, 1) & np.roll(opaque, -1, 1))
    rim[0, :] |= opaque[0, :]
    rim[-1, :] |= opaque[-1, :]
    rim[:, 0] |= opaque[:, 0]
    rim[:, -1] |= opaque[:, -1]
    a[..., :3] = np.where(rim[..., None], (a[..., :3].astype(np.float32) * 0.74).astype(np.uint8), a[..., :3])
    return a


# ---- writing everything ------------------------------------------------------------------------------------------------------------------------------------------

def write_sprites(out_dir: str) -> dict:
    """The stage sprites (woofer, fixture, disco_ball, door_open, the big props) as processed PNGs; returns manifest entries."""
    os.makedirs(out_dir, exist_ok=True)
    sp = {}
    a = spr_pa_speaker()
    sp["woofer"] = {"file": _write(out_dir, "woofer.png", a), "pivot": [a.shape[1] / 2.0, a.shape[0] / 2.0], "px_scale": round(150.0 / a.shape[0], 6), "radius": 50}
    a = spr_fixture()
    k = 62.0 / a.shape[0]
    sp["fixture"] = {"file": _write(out_dir, "fixture.png", a), "pivot": [a.shape[1] / 2.0, round(2.0 / k, 3)], "px_scale": round(k, 6), "lens": [0, 51]}
    a = spr_lantern()
    k = 290.0 / a.shape[0]
    sp["disco_ball"] = {"file": _write(out_dir, "disco_ball.png", a), "pivot": [a.shape[1] / 2.0, round(2.0 / k, 3)], "px_scale": round(k, 6), "radius": 27, "ball_centre": [0, 66]}
    a = spr_door_open()
    sp["door_open"] = {"file": _write(out_dir, "door_open.png", a), "pivot": [0, 0], "px_scale": round(150.0 / a.shape[1], 6), "pos": [244, 130]}
    for tid in sorted(T.BIG):
        a = big_prop(tid)
        sp[tid] = {"file": _write(out_dir, tid + ".png", a), "pivot": [a.shape[1] / 2.0, float(a.shape[0])], "px_scale": 1.0}
    return sp


def write_silhouettes(out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    sils = {}
    for kind in ("a", "b", "c"):
        e = {}
        for state in ("idle", "up"):
            a = spr_silhouette(kind, state == "up")
            fn = f"sil_{kind}_{state}.png"
            save_rgba(os.path.join(out_dir, fn), a)
            top = 140 if state == "up" else 112
            e[state] = {"file": f"processed/{fn}", "pivot": [26.0, round(top / SIL_SCALE, 3)], "px_scale": round(SIL_SCALE, 6)}
        e["height"] = 100
        sils[f"sil_{kind}"] = e
    return sils


PIECES = {  # id -> drawing; the file is processed/piece_<id>.png
    "balloon_bunch": piece_balloons, "cards_garland": piece_cards, "heart_monitor": piece_monitor, "flower_vase": piece_vase, "paper_stars": piece_paper_stars,
    "fairy_lights": piece_fairy_lights, "corridor_banner": piece_banner, "cafeteria_lamps": piece_lamps, "garden_bunting": piece_bunting, "garden_petals": piece_petals,
}


def write_pieces(out_dir: str) -> dict:
    """Pixel versions of the `mix` pieces; returns {id: texture width} so the caller can set each piece's file and px_scale."""
    os.makedirs(out_dir, exist_ok=True)
    out = {}
    for pid, fn in sorted(PIECES.items()):
        a = fn()
        save_rgba(os.path.join(out_dir, f"piece_{pid}.png"), a)
        out[pid] = a.shape[1]
    return out


def write_sky(out_dir: str) -> None:
    """The map's sky: 1024 x 128 texels once round the horizon (map sky.repeats 1), one moon to the east-north-east where the garden looks, pixel stars."""
    os.makedirs(out_dir, exist_ok=True)
    from PIL import Image
    a = sky_strip(1024, 128, 211, ((236, 57),))
    Image.fromarray(a, "RGB").save(os.path.join(out_dir, "sky_night_wide.png"), optimize=False, compress_level=9)
