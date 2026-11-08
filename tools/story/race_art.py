"""PLACEHOLDER art for the street race (tools/story/build_race.py, docs/bedsit/RACE.md), drawn procedurally with the bedsit's pixel kit (tools/story/art/bedsit_draw.py):
hard alpha, ramps with ordered dither, light from the upper left. None of it is finished art: it is the night street's stand-in until the art pass.

`textures(theme)` -> {name: (Cv, metres per repeat or None for a billboard / decal)} for assets/story/race_<theme>/textures/
`sheets(theme)`   -> {name: (Cv, [cols, rows])} for the race's dynamic things, assets/story/race_<theme>/sprites/
A theme is the palette block of build_race.THEMES (the street's colours, the neon, the rivals' paint).
"""
from __future__ import annotations

import math

import numpy as np

from art.bedsit_draw import Cv, ramp, lerp_ramp, fnoise
from art import pixeltex as px


def _hx(c):
    return (px.hexc(c) * 255).astype(np.uint8)


def _stipple(cv: Cv, field: np.ndarray, col: str, amount: float = 1.0):
    """Hard-alpha glow: pixels where the field beats the Bayer threshold take `col` (a dithered halo with no soft alpha)."""
    b = px.BAYER8[np.arange(cv.h)[:, None] % 8, np.arange(cv.w)[None, :] % 8] + 0.5
    m = field * amount > b
    cv.a[m, :3] = _hx(col)
    cv.a[m, 3] = 255


def _glow(cv: Cv, cx, cy, r, col, power=1.6, amount=1.0):
    d = np.sqrt((cv.xx - cx) ** 2 + (cv.yy - cy) ** 2) / max(r, 1)
    _stipple(cv, np.clip(1 - d, 0, 1) ** power, col, amount)


# ---------------------------------------------------------------------------------------------------------------- tiles (world textures)
def asphalt(t: dict, n=256) -> Cv:
    """Wet night asphalt, tileable: dark aggregate, puddles that hold the neon (pink, cyan, sodium) as dithered glints."""
    c = Cv(n, n)
    base = px.noise(n, 22, 3) * 0.55 + px.noise(n, 6, 4) * 0.45
    pal = ramp(t["road_dark"], t["road_mid"], t["road_lite"], "#5a5e78")
    c.a[..., :3] = px.quantise(0.25 + base * 0.45, pal, 1.0)
    c.a[..., 3] = 255
    grit = px.speckle(n, 0.05, 5) > 0
    c.a[grit, :3] = _hx("#6c6f88")
    wet = px.noise(n, 48, 7, 2)
    pud = wet > 0.6
    refl = px.noise(n, 10, 9, 2)
    for col, lo, hi in ((t["neon_a"], 0.0, 0.33), (t["neon_b"], 0.33, 0.66), (t["sodium"], 0.66, 1.0)):
        m = pud & (refl >= lo) & (refl < hi)
        glint = m & (px.speckle(n, 0.09, 11 + int(lo * 10)) > 0)
        c.a[m, :3] = (c.a[m, :3].astype(np.float32) * 0.55 + _hx("#101026").astype(np.float32) * 0.45).astype(np.uint8)
        c.a[glint, :3] = (_hx(col).astype(np.float32) * 0.75).astype(np.uint8)
    return c


def paving(t: dict, n=128) -> Cv:
    c = Cv(n, n)
    x, y = px.grid(n)
    seam = ((x % 32) < 1) | ((y % 32) < 1)
    shade = 0.45 + px.noise(n, 16, 21) * 0.35
    c.a[..., :3] = px.quantise(shade, ramp(*t.get("pave_ramp", ("#23263a", "#33374f", "#454a66", "#5a5f7e"))), 1.0)
    c.a[..., 3] = 255
    c.a[seam, :3] = _hx(t.get("pave_seam", "#15172a"))
    wet = (px.noise(n, 40, 23, 2) > 0.62) & (px.speckle(n, 0.3, 24) > 0)
    c.a[wet, :3] = _hx(t["neon_b"]) // 2
    return c


def kerb(t: dict, n=64) -> Cv:
    c = Cv(n, n)
    c.a[..., :3] = px.quantise(0.4 + px.noise(n, 8, 31) * 0.3, ramp(*t.get("kerb_ramp", ("#3b3e52", "#5d6078", "#8a8ea6", "#b8bccf"))), 1.0)
    c.a[..., 3] = 255
    c.a[:3, :, :3] = _hx("#d8dbe8")
    c.a[18:, :, :3] = _hx("#1a1c2c")
    return c


def roof(t: dict, n=64) -> Cv:
    c = Cv(n, n)
    c.a[..., :3] = px.quantise(0.3 + px.noise(n, 10, 41) * 0.3, ramp(*t.get("roof_ramp", ("#0d0e1a", "#171a2a", "#22263a"))), 1.0)
    c.a[..., 3] = 255
    return c


def facade(t: dict, seed: int, wall: tuple, win_lit: list, n=256, cols=4, rows=2) -> Cv:
    """A building face, tileable both ways: a grid of `cols` x `rows` windows on an 8 m square (two storeys of 4 m), ledges, drips, an air-conditioner here and there; some
    windows lit warm or with a screen's blue, most dark with the street's neon caught in the glass."""
    c = Cv(n, n)
    rng = np.random.RandomState(seed)
    shade = 0.42 + px.noise(n, 18, seed) * 0.28 - (px.noise(n, 6, seed + 1) > 0.7) * 0.08
    c.a[..., :3] = px.quantise(shade, ramp(*wall), 1.0)
    c.a[..., 3] = 255
    cw, ch = n // cols, n // rows
    for r in range(rows):
        c.a[r * ch:r * ch + 4, :, :3] = _hx(wall[3])           # the ledge under each storey (lit edge)
        c.a[r * ch + 4:r * ch + 7, :, :3] = _hx(wall[0])
        for k in range(cols):
            x0, y0 = k * cw + cw // 5, r * ch + ch // 4
            x1, y1 = (k + 1) * cw - cw // 5, (r + 1) * ch - ch // 6
            c.flat(c.rect(x0 - 2, y0 - 2, x1 + 2, y1 + 2), "#0b0c16")
            roll = rng.rand()
            if roll < 0.28:
                col = win_lit[int(rng.rand() * len(win_lit))]
                pal = lerp_ramp("#20140a", col, 5)
                c.paint(c.rect(x0, y0, x1, y1), pal, c.lit((x0, y0, x1, y1), 0.72, 0.4), edge=False)
                if rng.rand() < 0.5:  # blinds
                    for yy in range(y0 + 3, y1, 5):
                        c.a[yy, x0:x1, :3] = (c.a[yy, x0:x1, :3].astype(np.float32) * 0.6).astype(np.uint8)
                if rng.rand() < 0.4:  # a figure's silhouette at the window
                    fx = int(x0 + (x1 - x0) * (0.3 + rng.rand() * 0.4))
                    c.flat(c.ell(fx - 5, y0 + 6, fx + 5, y0 + 16), "#1a1008")
                    c.flat(c.rect(fx - 7, y0 + 15, fx + 7, y1), "#1a1008")
            else:
                c.paint(c.rect(x0, y0, x1, y1), ramp("#06070e", "#0d1022", "#18203e", "#2a3866"), c.lit((x0, y0, x1, y1), 0.35, 0.5), edge=False)
                gl = c.rect(x0 + 3, y0 + 3, x0 + 7, y1 - 3)       # a streak of the neon caught in the glass
                c.a[gl & (px.speckle(n, 0.5, seed + k + r * 9) > 0), :3] = _hx(t["neon_a"] if (k + r) % 2 else t["neon_b"]) // 2
            c.a[y1 + 2:y1 + 5, x0 - 3:x1 + 3, :3] = _hx(wall[2])  # the sill
            if rng.rand() < 0.22:  # an air-conditioner box under the sill, dripping
                ax = x0 + int((x1 - x0) * 0.2)
                c.paint(c.rect(ax, y1 + 6, ax + 18, y1 + 16), ramp("#3a3e4e", "#6a6e80", "#9ca0b4"), c.lit((ax, y1 + 6, ax + 18, y1 + 16)))
                for d in range(3):
                    c.a[y1 + 17:min(y1 + 17 + 6 + d * 4, n), ax + 4 + d * 5, :3] = _hx("#2a2e48")
    drip = (px.noise(n, 3, seed + 5, 1) > 0.78) & (c.yy % ch > ch * 0.75)
    c.a[drip, :3] = (c.a[drip, :3].astype(np.float32) * 0.7).astype(np.uint8)
    return c


def sky(t: dict, w=1024, h=256) -> Cv:
    """The sky strip (horizon at 0.76 of its height): a violet night, stars, a nebula, the Mothership hanging over the city, towers with lit windows on the horizon and the
    city's glow under them."""
    if t.get("sky_kind"):  # a theme's own sky (race_art_themes.py)
        import race_art_themes as rt
        return rt.SKIES[t["sky_kind"]](t, w, h)
    c = Cv(w, h)
    yy = c.yy / h
    grad = np.clip(yy / 0.76, 0, 1)
    c.a[..., :3] = px.quantise(grad * 0.85, ramp(*t["sky"]), 1.0)
    c.a[..., 3] = 255
    neb = fnoise(h, w, 60, 51) * (1 - grad) * 1.2
    _stipple(c, np.clip(neb - 0.35, 0, 1) * 1.3, t["nebula"], 1.0)
    rng = np.random.RandomState(52)
    for _ in range(140):
        x, y = rng.randint(0, w), rng.randint(0, int(h * 0.6))
        c.a[y, x, :3] = _hx("#d8dcff" if rng.rand() < 0.3 else "#6a6a9a")
    # the Mothership: a long saucer with a ring of lights
    mx, my, mw = 300, 64, 220
    c.paint(c.ell(mx - mw // 2, my - 18, mx + mw // 2, my + 18), ramp("#120c22", "#231a3e", "#3a2c60", "#5a4890"), c.dome(mx, my - 6, mw // 2, 18, 0.45, 0.6), edge=True)
    c.paint(c.ell(mx - 50, my - 36, mx + 50, my - 2), ramp("#1a1230", "#2e2452", "#4a3c80", "#7a6cc0"), c.dome(mx - 10, my - 26, 50, 18), edge=True)
    for k in range(18):
        lx = mx - mw // 2 + 12 + k * (mw - 24) // 17
        c.flat(c.rect(lx, my + 6, lx + 3, my + 9), t["neon_b"] if k % 3 else t["neon_a"])
    _glow(c, mx, my + 22, 60, t["neon_b"], 2.2, 0.55)
    # the skyline under the horizon line
    hz = int(h * 0.76)
    x = 0
    while x < w:
        bw = rng.randint(18, 60)
        bh = rng.randint(20, 120)
        top = hz - bh
        c.flat(c.rect(x, top, x + bw, h), "#0a0a16")
        for wy in range(top + 4, h - 2, 6):
            for wx in range(x + 3, x + bw - 3, 5):
                if rng.rand() < 0.18:
                    c.a[wy:wy + 2, wx:wx + 2, :3] = _hx(t["sodium"] if rng.rand() < 0.6 else t["neon_b"])
        if rng.rand() < 0.25:  # an antenna with a red lamp
            c.a[top - 10:top, x + bw // 2, :3] = _hx("#2a2a3a")
            c.a[top - 11, x + bw // 2, :3] = _hx("#ff3a3a")
        x += bw + rng.randint(0, 6)
    glow = np.clip(1 - np.abs(yy - 0.76) / 0.12, 0, 1) ** 2 * (c.a[..., 0] < 30)
    _stipple(c, glow * 0.8, t["city_glow"], 1.0)
    return c


# ---------------------------------------------------------------------------------------------------------------- billboards and decals
def lamp(t: dict) -> Cv:
    c = Cv(48, 208)
    c.paint(c.rect(21, 30, 27, 208), ramp("#1a1c28", "#30344a", "#4c5270", "#6a7092"), c.round_x(21, 27))
    c.paint(c.rect(17, 196, 31, 208), ramp("#1a1c28", "#30344a", "#4c5270"), c.lit((17, 196, 31, 208)))
    c.paint(c.lines([(24, 32), (24, 18), (30, 10), (40, 8)], 4), ramp("#1a1c28", "#30344a", "#4c5270"))
    c.paint(c.rrect(30, 6, 48, 14, 3), ramp("#2a2c3a", "#4a4e66", "#6a7092"))
    c.flat(c.rect(32, 13, 46, 16), t["sodium_hot"])
    _glow(c, 39, 18, 12, t["sodium"], 1.4, 0.8)
    return c


def stud(t: dict) -> Cv:
    c = Cv(8, 6)
    c.flat(c.rect(0, 2, 8, 6), "#2a2c3c")
    c.flat(c.rect(2, 0, 6, 3), t["stud"])
    c.a[0, 3:5, :3] = _hx("#ffffff")
    return c


def gantry(t: dict) -> Cv:
    """The finish gantry: two lit pylons and a chequered banner across the road; the middle is open (hard alpha)."""
    w, h = 400, 200
    c = Cv(w, h)
    for x0 in (8, w - 32):
        c.paint(c.rect(x0, 30, x0 + 24, h), ramp("#14141e", "#2a2c40", "#46496a", "#6e7296"), c.round_x(x0, x0 + 24))
        for y in range(44, h - 10, 18):
            c.flat(c.rect(x0 + 8, y, x0 + 16, y + 6), t["neon_a"] if (y // 18) % 2 else t["neon_b"])
    c.paint(c.rect(0, 10, w, 52), ramp("#0a0a12", "#1c1c2c"), c.lit((0, 10, w, 52)), edge=True)
    sq = 14
    for i in range(w // sq):
        for j in range(3):
            if (i + j) % 2 == 0:
                c.flat(c.rect(i * sq, 12 + j * sq, i * sq + sq, 12 + (j + 1) * sq), "#e8e8f4")
    c.flat(c.rect(0, 8, w, 11), t["neon_b"])
    c.flat(c.rect(0, 52, w, 55), t["neon_a"])
    return c


def banner(t: dict) -> Cv:
    """An approach banner hung over the road before the finish: a chequer strip with a lit hem."""
    w, h = 256, 40
    c = Cv(w, h)
    c.flat(c.rect(0, 0, w, h), "#101018")
    sq = 10
    for i in range(w // sq):
        for j in range(3):
            if (i + j) % 2 == 0:
                c.flat(c.rect(i * sq, 5 + j * sq, i * sq + sq, 5 + (j + 1) * sq), "#d8d8e8")
    c.flat(c.rect(0, 0, w, 3), t["neon_a"])
    c.flat(c.rect(0, h - 3, w, h), t["neon_a"])
    return c


def neon(t: dict, kind: int) -> Cv:
    """A neon sign (an emissive decal): tubes on a dark backing board. No words: a noodle bowl, an alien head, a ringed planet, a cocktail glass, a rocket."""
    if t.get("neon_set"):
        import race_art_themes as rt
        return rt.neon_set(t, kind)
    c = Cv(96, 72)
    c.paint(c.rrect(2, 2, 94, 70, 6), ramp("#07070e", "#10101c", "#181828"), c.lit((2, 2, 94, 70)), edge=True, edge_col="#2a2a40")
    col = [t["neon_a"], t["neon_b"], t["neon_c"], t["sodium"], t["neon_d"]][kind % 5]
    def tube(mask):
        e = mask & ~Cv._erode(Cv._erode(mask))
        c.a[e, :3] = _hx(col)
        c.a[e, 3] = 255
    if kind % 5 == 0:   # a bowl with chopsticks
        tube(c.ell(18, 28, 78, 62) & (c.yy > 40))
        tube(c.lines([(22, 41), (74, 41)], 3))
        tube(c.lines([(52, 36), (70, 10)], 3))
        tube(c.lines([(58, 36), (80, 14)], 3))
    elif kind % 5 == 1:  # an alien head
        tube(c.ell(26, 8, 70, 64))
        tube(c.ell(32, 26, 46, 40))
        tube(c.ell(50, 26, 64, 40))
    elif kind % 5 == 2:  # a ringed planet
        tube(c.ell(32, 18, 64, 50))
        tube(c.ell(10, 28, 86, 42))
    elif kind % 5 == 3:  # a cocktail glass
        tube(c.poly([(22, 12), (74, 12), (48, 40)]))
        tube(c.lines([(48, 40), (48, 60)], 3))
        tube(c.lines([(34, 62), (62, 62)], 3))
    else:               # a rocket
        tube(c.poly([(48, 6), (60, 26), (60, 52), (36, 52), (36, 26)]))
        tube(c.poly([(36, 40), (26, 58), (36, 54)]))
        tube(c.poly([(60, 40), (70, 58), (60, 54)]))
    _glow(c, 48, 36, 40, col, 2.6, 0.35)
    c.a[c.a[..., 3] == 0, 3] = 0
    return c


def shopfront(t: dict, seed: int) -> Cv:
    """A lit shop window at street level (an emissive decal): warm light, shelves of goods, a sill."""
    c = Cv(160, 72)
    rng = np.random.RandomState(seed)
    c.paint(c.rect(0, 0, 160, 72), ramp("#0a0a12", "#16161f", "#22222e"), c.lit((0, 0, 160, 72)))
    warm = t["shop"][seed % len(t["shop"])]
    c.paint(c.rect(8, 10, 152, 64), lerp_ramp("#2a1408", warm, 6), c.lit((8, 10, 152, 64), 0.7, 0.4), edge=False)
    for sy in (26, 42):
        c.flat(c.rect(10, sy, 150, sy + 2), "#3a2010")
        x = 12
        while x < 146:
            gw = rng.randint(4, 10)
            c.flat(c.rect(x, sy - rng.randint(5, 12), x + gw, sy), ["#ff6a8a", "#6af0ff", "#ffe08a", "#9aff7a", "#c08aff"][rng.randint(0, 5)])
            x += gw + rng.randint(1, 4)
    c.flat(c.rect(0, 64, 160, 72), "#2a2c3e")
    c.flat(c.rect(0, 2, 160, 8), t["neon_a"] if seed % 2 else t["neon_b"])
    return c


# ---------------------------------------------------------------------------------------------------------------- the race's dynamic things
def car(paint: tuple, frame: int, kind="racer") -> Cv:
    """A car seen from behind (the rivals, the traffic): racer = a low wide hover racer; taxi; van = a tall box. frame 0 cruising (tail lights dim), 1 braking (bright, a glow),
    2 contact (sparks off the corner, the body knocked askew)."""
    w, h = 160, 104
    c = Cv(w, h)
    dx = 6 if frame == 2 else 0
    if kind == "van":
        c.paint(c.rrect(18 + dx, 6, 142 + dx, 86, 6), ramp(*paint), c.lit((18, 6, 142, 86), 0.55, 0.45), edge=True)
        c.paint(c.rect(30 + dx, 14, 130 + dx, 50), ramp("#0a0c16", "#151a2c", "#22304c"), c.lit((30, 14, 130, 50), 0.4, 0.5))
        c.flat(c.rect(78 + dx, 14, 82 + dx, 84), "#1c1e2a")
        lamp_y = 62
    else:
        body = [(10, 70), (22, 40), (50, 26), (110, 26), (138, 40), (150, 70), (150, 86), (10, 86)]
        c.paint(c.poly([(x + dx, y) for x, y in body]), ramp(*paint), c.lit((10, 26, 150, 86), 0.55, 0.5), edge=True)
        c.paint(c.poly([(46 + dx, 30), (114 + dx, 30), (126 + dx, 46), (34 + dx, 46)]), ramp("#0a0c16", "#151a2c", "#2a3a60", "#4a6aa0"), c.lit((34, 30, 126, 46), 0.4, 0.6), edge=True)
        if kind == "taxi":
            c.paint(c.rrect(64 + dx, 16, 96 + dx, 27, 3), ramp("#5a4a10", "#c8a020", "#ffe070"), c.lit((64, 16, 96, 27)))
        c.flat(c.rect(40 + dx, 56, 120 + dx, 62), "#14141e")  # the boot line
        lamp_y = 60
    on = frame == 1
    for x0 in (16, 118):
        c.flat(c.rect(x0 + dx, lamp_y - 6, x0 + 26 + dx, lamp_y + 4), "#ff3030" if on else "#7a1418")
        c.flat(c.rect(x0 + 2 + dx, lamp_y - 4, x0 + 10 + dx, lamp_y), "#ffd0c8" if on else "#b02028")
        if on:
            _glow(c, x0 + 13 + dx, lamp_y, 22, "#ff2a2a", 1.8, 0.7)
    c.flat(c.rect(14 + dx, 86, 146 + dx, 92), "#0c0c14")
    for x0 in (20, 112):
        c.paint(c.rrect(x0 + dx, 84, x0 + 28 + dx, 102, 4), ramp("#08080c", "#14141e", "#22222e"), c.lit((x0, 84, x0 + 28, 102)))
    _stipple(c, np.clip(1 - np.abs(c.yy - 98) / 6, 0, 1) * ((c.xx > 24 + dx) & (c.xx < 136 + dx)), paint[3], 0.7)  # the hover glow under it
    if frame == 2:
        rng = np.random.RandomState(7)
        for _ in range(40):
            a = rng.rand() * math.pi - math.pi
            r = rng.rand() * 26
            x, y = int(12 + math.cos(a) * r), int(60 + math.sin(a) * r)
            if 0 <= x < w and 0 <= y < h:
                c.a[y, x, :3] = _hx("#ffe080" if rng.rand() < 0.6 else "#ffffff")
                c.a[y, x, 3] = 255
        c.a[40:48, 8:18, :3] = _hx("#3a3a48")
    return c


def barrier(t: dict, frame: int) -> Cv:
    """Roadworks closing a lane: a striped barrier on trestles, two lamps flashing (frame 1 lit)."""
    w, h = 192, 80
    c = Cv(w, h)
    c.paint(c.rect(4, 22, w - 4, 46), ramp(*t.get("barrier_ramp", ("#401808", "#a03c10", "#ff7a20"))), c.lit((4, 22, w - 4, 46)), edge=True)
    for k in range(0, w, 24):
        c.flat(c.poly([(k, 22), (k + 12, 22), (k + 2, 46), (k - 10, 46)]) & c.rect(4, 22, w - 4, 46), t.get("barrier_stripe", "#f0f0f0"))
    for x0 in (16, w - 30):
        c.paint(c.rect(x0, 46, x0 + 10, 80), ramp("#1a1a24", "#3a3a4a", "#5a5a70"), c.round_x(x0, x0 + 10))
    for x0 in (22, w - 34):
        c.flat(c.ell(x0, 6, x0 + 14, 20), "#ffcc30" if frame else "#5a4010")
        if frame:
            _glow(c, x0 + 7, 13, 18, "#ffb020", 1.6, 0.8)
    return c


def cones(t: dict, frame: int) -> Cv:
    """A line of cones narrowing the street, their bands lit by the car's lamps (frame 1)."""
    w, h = 192, 64
    c = Cv(w, h)
    for k in range(5):
        x = 10 + k * 38
        c.paint(c.poly([(x + 10, 6), (x + 18, 6), (x + 26, 56), (x + 2, 56)]), ramp(*t.get("cone_ramp", ("#5a1a08", "#c04010", "#ff7a30"))), c.lit((x, 6, x + 28, 56)), edge=True)
        c.flat(c.rect(x + 7, 24, x + 21, 30), "#ffffff" if frame else "#b0b0b8")
        c.flat(c.rect(x - 2, 56, x + 30, 62), "#1a1a20")
    return c


def dash(t: dict) -> Cv:
    """The car's bonnet and dash from the driver's low eye, one row per state: steady, leaning left, leaning right, braking (the brake lamp on the dash), jolted (a crack of
    sparks at the bonnet's edge). The lean is the car body's, drawn in the frame; the camera never rolls. Cells are 448 x 56 (drawn about 3.4 x 0.42 m)."""
    if t.get("vehicle") in ("broom", "jeep", "rally"):
        import race_art_themes as rt
        return rt.dash_broom(t) if t["vehicle"] == "broom" else rt.dash_hood(t, t["vehicle"])
    cw, ch = 448, 56
    X = lambda x: int(round(x * cw / 400.0))
    Y = lambda y: int(round(y * ch / 104.0))
    sheet = Cv(cw, ch * 5)
    for row in range(5):
        f = Cv(cw, ch)
        tilt = {1: -5, 2: 5}.get(row, 0)
        hood = [(0, 104), (0, 50 + tilt), (60, 26 + tilt // 2), (140, 14), (260, 14), (340, 26 - tilt // 2), (400, 50 - tilt), (400, 104)]
        f.paint(f.poly([(X(x), Y(y)) for x, y in hood]), ramp(*t["hood"]), f.lit((0, Y(14), cw, ch), 0.55, 0.55), edge=True)
        f.paint(f.poly([(X(150), Y(18)), (X(250), Y(18)), (X(262), Y(40)), (X(138), Y(40))]), ramp("#0a0a12", "#1a1a26", "#2a2c40"), f.lit((X(138), Y(18), X(262), Y(40))), edge=True)
        for side in (-1, 1):  # the hood's crease catching the street light
            x0 = X(200 + side * 70)
            f.a[Y(24):ch, x0:x0 + 2, :3] = _hx(t["hood"][3])
        f.paint(f.rect(0, Y(78), cw, ch), ramp("#06060c", "#10101a", "#1c1c2a"), f.lit((0, Y(78), cw, ch)), edge=False)  # the dash's lip
        f.flat(f.rect(0, Y(76), cw, Y(76) + 2), t["neon_b"])
        if row == 3:
            f.flat(f.rect(X(186), Y(84), X(214), Y(98)), "#ff2a2a")
            _glow(f, X(200), Y(91), 22, "#ff2a2a", 1.6, 0.7)
        else:
            f.flat(f.rect(X(186), Y(84), X(214), Y(98)), "#3a0a0a")
        if row == 4:
            rng = np.random.RandomState(9)
            for _ in range(80):
                x, y = int(rng.rand() * cw), int(Y(14) + rng.rand() * Y(30))
                f.a[y, x, :3] = _hx("#ffe080" if rng.rand() < 0.5 else "#ffffff")
                f.a[y, x, 3] = 255
            f.flat(f.lines([(X(90), Y(30)), (X(120), Y(44)), (X(110), Y(60)), (X(140), Y(74))], 2), "#0a0a10")
        sheet.stamp(f, 0, row * ch)
    return sheet


def gauge(t: dict) -> Cv:
    """The countdown gauge on the dash: eight segments round a dial, all lit at the start of a decision, one going out per eighth of the time; green, then amber, then red;
    frame 0 = the deadline (the ring flashes red), frames 1..8 = that many segments left."""
    cw = 72
    sheet = Cv(cw * 9, cw)
    for k in range(9):
        f = Cv(cw, cw)
        f.paint(f.ell(2, 2, cw - 2, cw - 2), ramp("#05050a", "#10101a", "#1e1e2e", "#2e2e44"), f.dome(30, 30, 34, 34), edge=True, edge_col="#5a5e7a")
        col = "#ff2a2a" if k <= 2 else ("#ffb020" if k <= 5 else "#40ff8a")
        for i in range(8):
            a0 = -math.pi / 2 + i * (2 * math.pi / 8) + 0.12
            a1 = a0 + 2 * math.pi / 8 - 0.24
            pts = [(36 + math.cos(a) * r, 36 + math.sin(a) * r) for r, a in [(30, a0), (30, (a0 + a1) / 2), (30, a1), (19, a1), (19, a0)]]
            lit = i < k
            f.flat(f.poly(pts), col if lit else "#24242e")
        if k == 0:
            f.flat(f.ell(14, 14, 58, 58) & ~f.ell(22, 22, 50, 50), "#ff2a2a")
        f.flat(f.ell(28, 28, 44, 44), "#d8dcef" if k else "#ff2a2a")
        sheet.stamp(f, k * cw, 0)
    return sheet


def speedo(t: dict) -> Cv:
    """The speed bar on the dash: eight frames, one more lit bar per step of speed."""
    cw, ch = 96, 32
    sheet = Cv(cw * 8, ch)
    for k in range(8):
        f = Cv(cw, ch)
        f.paint(f.rrect(0, 0, cw, ch, 4), ramp("#05050a", "#10101a", "#1e1e2e"), f.lit((0, 0, cw, ch)), edge=True, edge_col="#4a4e6a")
        for i in range(8):
            x0 = 6 + i * 11
            hgt = 6 + i * 2
            f.flat(f.rect(x0, ch - 5 - hgt, x0 + 8, ch - 5), (t["neon_b"] if i < 5 else t["neon_a"]) if i <= k else "#202030")
        sheet.stamp(f, k * cw, 0)
    return sheet


def lane_glow(t: dict) -> Cv:
    """The opening the player has chosen, lit on the road (a floor that glows under it: ruling 35b): frame 0 = a faint pulse, frame 1 = lit."""
    cw, ch = 160, 28
    sheet = Cv(cw * 2, ch)
    for k in range(2):
        f = Cv(cw, ch)
        d = np.sqrt(((f.xx - cw / 2) / (cw / 2)) ** 2 + ((f.yy - ch / 2) / (ch / 2)) ** 2)
        _stipple(f, np.clip(1 - d, 0, 1) ** (1.2 if k else 2.2), t["choice"], 1.0 if k else 0.6)
        if k:
            f.flat(f.rect(int(cw * 0.15), ch // 2 - 1, int(cw * 0.85), ch // 2 + 1), "#ffffff")
        sheet.stamp(f, k * cw, 0)
    return sheet


def start_lights(t: dict) -> Cv:
    """The start gantry's lamps: one, two, three reds, then all green."""
    cw, ch = 160, 56
    sheet = Cv(cw * 4, ch)
    for k in range(4):
        f = Cv(cw, ch)
        f.paint(f.rrect(0, 0, cw, ch, 6), ramp("#05050a", "#10101a", "#22222e"), f.lit((0, 0, cw, ch)), edge=True, edge_col="#4a4e6a")
        for i in range(3):
            cx = 30 + i * 50
            on_red = k < 3 and i <= k
            col = "#40ff8a" if k == 3 else ("#ff2a2a" if on_red else "#2a0a0a")
            f.flat(f.ell(cx - 16, 12, cx + 16, 44), col)
            if k == 3 or on_red:
                _glow(f, cx, 28, 26, col, 1.6, 0.6)
        sheet.stamp(f, k * cw, 0)
    return sheet


def rain(t: dict) -> Cv:
    """Rain on the view (four frames of falling streaks, hard alpha, sparse)."""
    if t.get("weather", "rain") != "rain":
        import race_art_themes as rt
        return rt.weather(t, t["weather"])
    cw, ch = 200, 120
    sheet = Cv(cw * 4, ch)
    rng = np.random.RandomState(3)
    drops = [(rng.rand() * cw, rng.rand() * ch, 5 + rng.rand() * 9) for _ in range(30)]
    for k in range(4):
        f = Cv(cw, ch)
        for (x, y, ln) in drops:
            yy = (y + k * ch / 4) % ch
            x0 = int(x + yy * 0.08) % cw
            for d in range(int(ln)):
                py = int(yy + d)
                if py < ch:
                    f.a[py, x0, :3] = _hx("#5a6ea8" if d < ln - 2 else "#a8b8e0")
                    f.a[py, x0, 3] = 255
        sheet.stamp(f, k * cw, 0)
    return sheet


def textures(t: dict) -> dict:
    out = {
        "rc_asphalt": (asphalt(t), 4.0),
        "rc_pave": (paving(t), 2.0),
        "rc_kerb": (kerb(t), 0.5),
        "rc_roof": (roof(t), 4.0),
        "rc_sky": (sky(t), None),
        "rc_lamp": (lamp(t), None),
        "rc_stud": (stud(t), None),
        "rc_gantry": (gantry(t), None),
        "rc_banner": (banner(t), None),
    }
    for i, (wall, lit) in enumerate(t["facades"]):
        fk = t.get("facade_kind", "windows")
        if fk == "stone":
            import race_art_themes as rt
            out["rc_facade_%d" % i] = (rt.facade_masonry(t, 61 + i * 7, wall, lit), 8.0)
        elif fk == "rock":
            import race_art_themes as rt
            out["rc_facade_%d" % i] = (rt.facade_rock(t, 61 + i * 7, wall, lit), 8.0)
        else:
            out["rc_facade_%d" % i] = (facade(t, 61 + i * 7, wall, lit), 8.0)
    for k in range(5):
        out["rc_neon_%d" % k] = (neon(t, k), None)
    for k in range(3):
        out["rc_shop_%d" % k] = (shopfront(t, k), None)
    return out


def sheets(t: dict) -> dict:
    out = {}
    def vcar(paint, f, kind):
        if t.get("vehicles", {}).get(kind):
            import race_art_themes as rt
            return rt.vehicle(paint, f, t["vehicles"][kind])
        return car(paint, f, kind)
    for i, paint in enumerate(t["rivals"]):
        s = Cv(160 * 3, 104)
        for f in range(3):
            s.stamp(vcar(paint, f, "racer"), f * 160, 0)
        out["car_rival_%d" % i] = (s, [3, 1])
    for name, paint, kind in (("car_taxi", t["taxi"], "taxi"), ("car_van", t["van"], "van")):
        s = Cv(160 * 3, 104)
        for f in range(3):
            s.stamp(vcar(paint, f, kind), f * 160, 0)
        out[name] = (s, [3, 1])
    s = Cv(192 * 2, 80)
    for f in range(2):
        s.stamp(barrier(t, f), f * 192, 0)
    out["barrier"] = (s, [2, 1])
    s = Cv(192 * 2, 64)
    for f in range(2):
        s.stamp(cones(t, f), f * 192, 0)
    out["cones"] = (s, [2, 1])
    out["dash"] = (dash(t), [1, 5])
    out["gauge"] = (gauge(t), [9, 1])
    out["speedo"] = (speedo(t), [8, 1])
    out["lane_glow"] = (lane_glow(t), [2, 1])
    out["start_lights"] = (start_lights(t), [4, 1])
    out["rain"] = (rain(t), [4, 1])
    return out
