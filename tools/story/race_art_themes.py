"""PLACEHOLDER art for the Magic, Dinos and Transport races (tools/story/build_race.py, docs/bedsit/RACE.md): the theme-specific pieces race_art.py dispatches to
(sky, building faces, neon signs, the rider's dash, the rivals and the traffic, the weather). Same pixel kit, same cell sizes and frame meanings as the Space art, so the race's
data and code stay theme-free. None of it is finished art."""
from __future__ import annotations

import math

import numpy as np

from art.bedsit_draw import Cv, ramp, lerp_ramp, fnoise
from art import pixeltex as px
import race_art as ra


def _hx(c):
    return ra._hx(c)


# ---------------------------------------------------------------------------------------------------------------- skies (1024 x 256, horizon at 0.76)
def _gradient_sky(t, c, h):
    yy = c.yy / h
    grad = np.clip(yy / 0.76, 0, 1)
    c.a[..., :3] = px.quantise(grad * 0.85, ramp(*t["sky"]), 1.0)
    c.a[..., 3] = 255
    return yy, grad


def sky_moon(t, w=1024, h=256):
    """A moonlit night: a big moon with a halo, stars, thin cloud, hills and a castle with lit windows on the horizon."""
    c = Cv(w, h)
    yy, grad = _gradient_sky(t, c, h)
    rng = np.random.RandomState(52)
    for _ in range(220):
        x, y = rng.randint(0, w), rng.randint(0, int(h * 0.62))
        c.a[y, x, :3] = _hx("#f0f4ff" if rng.rand() < 0.35 else "#7a86c0")
    mx, my, mr = 700, 62, 34
    ra._glow(c, mx, my, 110, t["neon_b"], 2.4, 0.5)
    c.paint(c.ell(mx - mr, my - mr, mx + mr, my + mr), ramp("#a8b4d8", "#d8e0f4", "#f4f8ff"), c.dome(mx - 8, my - 8, mr, mr, 0.5, 0.5), edge=False)
    for (dx, dy, r) in ((-10, -8, 7), (12, 6, 9), (-4, 16, 5), (14, -14, 4)):
        c.flat(c.ell(mx + dx - r, my + dy - r, mx + dx + r, my + dy + r), "#b4bedc")
    cl = fnoise(h, w, 80, 53) * (1 - np.abs(yy - 0.42) / 0.12).clip(0, 1)
    ra._stipple(c, np.clip(cl - 0.3, 0, 1) * 1.6, t["nebula"], 1.0)
    hz = int(h * 0.76)
    prof = (hz - 18 - (np.sin(np.arange(w) / 70.0) * 12 + np.sin(np.arange(w) / 23.0) * 4)).astype(int)
    for xx in range(w):  # rolling hills
        c.a[prof[xx]:h, xx, :3] = _hx("#080c1c")
        c.a[prof[xx]:h, xx, 3] = 255
    cx0 = 120  # the castle: curtain wall, towers with cone roofs, lit windows, a flag
    base = hz - 14
    c.flat(c.rect(cx0, base - 40, cx0 + 230, h), "#0a0f22")
    for tx, th in ((cx0 + 8, 100), (cx0 + 70, 70), (cx0 + 150, 120), (cx0 + 210, 80)):
        c.flat(c.rect(tx, base - th, tx + 22, h), "#0a0f22")
        c.flat(c.poly([(tx - 4, base - th), (tx + 11, base - th - 30), (tx + 26, base - th)]), "#10183a")
    c.a[base - 152:base - 120, cx0 + 160, :3] = _hx("#2a3050")
    c.flat(c.poly([(cx0 + 160, base - 152), (cx0 + 176, base - 146), (cx0 + 160, base - 140)]), t["neon_d"])
    for _ in range(26):
        wx, wy = cx0 + rng.randint(4, 224), base - rng.randint(8, 110)
        c.a[wy:wy + 5, wx:wx + 3, :3] = _hx(t["sodium"])
    ra._glow(c, cx0 + 115, base - 40, 70, t["city_glow"], 2.6, 0.25)
    for k in range(9):  # pines on the hills
        px0 = 420 + k * 70 + rng.randint(-12, 12)
        c.flat(c.poly([(px0, base + 6), (px0 + 9, base - 22 - rng.randint(0, 12)), (px0 + 18, base + 6)]), "#060a16")
    return c


def sky_volcano(t, w=1024, h=256):
    """A smoke-lit lava sky: a volcano with a glowing crater and a flow, a plume, pterosaurs in the haze, a jungle treeline and the glow of a lava river on the horizon."""
    c = Cv(w, h)
    yy, grad = _gradient_sky(t, c, h)
    rng = np.random.RandomState(62)
    pl = fnoise(h, w, 50, 63) * (1 - np.abs(yy - 0.3) / 0.3).clip(0, 1)
    ra._stipple(c, np.clip(pl - 0.25, 0, 1) * 1.5, "#2a0e0a", 1.0)
    hz = int(h * 0.76)
    vx, vy, vw = 330, 40, 330
    ra._glow(c, vx, vy + 8, 90, t["neon_b"], 2.0, 0.55)
    c.flat(c.poly([(vx - vw // 2, hz + 4), (vx - 26, vy + 6), (vx - 10, vy), (vx + 12, vy + 2), (vx + 28, vy + 8), (vx + vw // 2, hz + 4)]), "#120806")
    c.flat(c.poly([(vx - 10, vy), (vx + 12, vy + 2), (vx + 6, vy + 8), (vx - 8, vy + 7)]), t["neon_b"])
    c.flat(c.poly([(vx - 2, vy + 8), (vx + 6, vy + 8), (vx + 36, hz), (vx + 18, hz)]), t["neon_a"])
    for k in range(7):  # the plume
        px_, py_ = vx + 8 + k * 9 + rng.randint(-5, 5), vy - 6 - k * 9
        c.flat(c.ell(px_ - 14 - k, py_ - 8, px_ + 14 + k, py_ + 8), "#1c0c0a")
    for k in range(7):  # pterosaurs: a pair of swept wings
        sx, sy = 520 + k * 62 + rng.randint(-10, 10), 40 + rng.randint(0, 60)
        c.flat(c.lines([(sx - 12, sy + 3), (sx, sy), (sx + 12, sy + 3)], 2), "#0a0404")
        c.flat(c.lines([(sx, sy), (sx + 8, sy - 2)], 2), "#0a0404")
    xs = 0
    while xs < w:  # a jungle treeline
        bw = rng.randint(14, 36)
        bh = rng.randint(8, 34)
        c.flat(c.ell(xs, hz - bh, xs + bw, hz + 14), "#0a0806")
        if rng.rand() < 0.18:
            c.flat(c.lines([(xs + bw // 2, hz - bh), (xs + bw // 2, hz - bh - 14)], 2), "#0a0806")
        xs += bw - 4
    c.flat(c.rect(0, hz + 6, w, h), "#0a0604")
    glow = np.clip(1 - np.abs(yy - 0.78) / 0.1, 0, 1) ** 2
    ra._stipple(c, glow * 0.9, t["city_glow"], 1.0)
    return c


def sky_town(t, w=1024, h=256):
    """An overcast wet dusk over a railway town: low cloud, terraces with chimneys and lit windows, a cooling tower, a gasometer, signal masts with red and green lamps."""
    c = Cv(w, h)
    yy, grad = _gradient_sky(t, c, h)
    rng = np.random.RandomState(72)
    cl = fnoise(h, w, 70, 73) * (1 - np.abs(yy - 0.35) / 0.35).clip(0, 1)
    ra._stipple(c, np.clip(cl - 0.2, 0, 1) * 1.7, "#202a38", 1.0)
    hz = int(h * 0.76)
    x = 0
    while x < w:  # terraces
        bw = rng.randint(24, 70)
        bh = rng.randint(14, 54)
        top = hz - bh
        c.flat(c.rect(x, top, x + bw, h), "#0a0c12")
        c.flat(c.poly([(x, top), (x + bw // 2, top - 8), (x + bw, top)]), "#0c0e16")
        for chx in range(x + 6, x + bw - 4, 18):
            c.flat(c.rect(chx, top - 14, chx + 5, top), "#0a0c12")
        for wy in range(top + 5, h - 2, 8):
            for wx in range(x + 4, x + bw - 4, 7):
                if rng.rand() < 0.2:
                    c.a[wy:wy + 3, wx:wx + 3, :3] = _hx(t["sodium"])
        x += bw + rng.randint(0, 4)
    tx = 640  # a cooling tower, steaming
    c.flat(c.poly([(tx - 34, hz), (tx - 20, hz - 70), (tx - 24, hz - 100), (tx + 24, hz - 100), (tx + 20, hz - 70), (tx + 34, hz)]), "#10141c")
    ra._stipple(c, np.clip(1 - np.sqrt(((c.xx - tx) / 40.0) ** 2 + ((c.yy - (hz - 118)) / 26.0) ** 2), 0, 1), "#3a4658", 1.0)
    c.flat(c.ell(820, hz - 56, 900, hz + 6), "#0e1218")  # a gasometer
    c.flat(c.rect(820, hz - 28, 900, hz + 6), "#0e1218")
    for k in range(4):
        c.flat(c.rect(824, hz - 50 + k * 9, 896, hz - 49 + k * 9), "#1c222e")
    for sx in (200, 470, 980):  # signal masts
        c.flat(c.rect(sx, hz - 70, sx + 3, hz), "#0a0c12")
        c.flat(c.rect(sx - 5, hz - 76, sx + 8, hz - 62), "#06080c")
        c.flat(c.ell(sx - 2, hz - 74, sx + 5, hz - 68), t["neon_a"])
        c.flat(c.ell(sx - 2, hz - 66, sx + 5, hz - 60), t["neon_b"] if sx != 470 else "#2a2a30")
    glow = np.clip(1 - np.abs(yy - 0.78) / 0.1, 0, 1) ** 2 * (c.a[..., 0] < 30)
    ra._stipple(c, glow * 0.8, t["city_glow"], 1.0)
    return c


SKIES = {"moon": sky_moon, "volcano": sky_volcano, "town": sky_town}


# ---------------------------------------------------------------------------------------------------------------- building faces (256 x 256, tileable, 8 m square)
def facade_masonry(t, seed, wall, win_lit, n=256):
    """Dressed stone blocks with arched windows (some lit warm), courses of blocks: the Magic street's walls."""
    c = Cv(n, n)
    rng = np.random.RandomState(seed)
    base = 0.42 + px.noise(n, 18, seed) * 0.25
    c.a[..., :3] = px.quantise(base, ramp(*wall), 1.0)
    c.a[..., 3] = 255
    for y in range(0, n, 16):  # courses of blocks
        c.a[y:y + 1, :, :3] = _hx(wall[0])
        off = 0 if (y // 16) % 2 == 0 else 16
        for x in range(off, n, 32):
            c.a[y:y + 16, x:x + 1, :3] = _hx(wall[0])
    for r in range(2):
        for k in range(4):
            x0, y0 = k * 64 + 22, r * 128 + 26
            x1, y1 = x0 + 20, y0 + 56
            c.flat(c.rect(x0 - 3, y0 + 10, x1 + 3, y1 + 3), "#080a16")
            c.flat(c.ell(x0 - 3, y0 - 2, x1 + 3, y0 + 24), "#080a16")
            lit = rng.rand() < 0.3
            col = win_lit[int(rng.rand() * len(win_lit))]
            inner = c.rect(x0, y0 + 10, x1, y1) | c.ell(x0, y0 + 2, x1, y0 + 22)
            if lit:
                c.paint(inner, lerp_ramp("#20140a", col, 5), c.lit((x0, y0, x1, y1), 0.7, 0.4), edge=False)
                c.flat(c.rect(x0 + 9, y0 + 2, x0 + 11, y1), "#1a1008")
                c.flat(c.rect(x0, y0 + 26, x1, y0 + 28), "#1a1008")
            else:
                c.paint(inner, ramp("#06080e", "#0e1428", "#1c2a52", "#34508a"), c.lit((x0, y0, x1, y1), 0.35, 0.5), edge=False)
            c.a[y1 + 3:y1 + 6, x0 - 5:x1 + 5, :3] = _hx(wall[3])
    return c


def facade_rock(t, seed, wall, lava, n=256):
    """A basalt cliff, tileable: strata, columns, cracks that glow with lava, a cave mouth now and then (the Dinos ledge's walls)."""
    c = Cv(n, n)
    rng = np.random.RandomState(seed)
    base = 0.4 + px.noise(n, 14, seed) * 0.35 + np.sin(c.yy / 9.0 + px.noise(n, 30, seed + 2) * 5) * 0.08
    c.a[..., :3] = px.quantise(np.clip(base, 0, 1), ramp(*wall), 1.0)
    c.a[..., 3] = 255
    for k in range(0, n, 32):  # columns (a whole number of them, so the tile repeats)
        c.a[:, k:k + 1, :3] = _hx(wall[0])
        c.a[:, k + 1:k + 2, :3] = _hx(wall[3])
    for i in range(7):  # lava cracks
        x, y = rng.randint(8, n - 8), rng.randint(0, n - 120)
        pts = [(x, y)]
        for _k in range(5):
            x = int(np.clip(x + rng.randint(-10, 11), 1, n - 2))
            y = y + rng.randint(8, 20)
            pts.append((x, y))
        col = lava[int(rng.rand() * len(lava))]
        crack = c.lines(pts, 2)
        halo = c.lines(pts, 6) & ~crack & (px.speckle(n, 0.5, seed + i) > 0)
        c.a[halo, :3] = (_hx(col).astype(np.float32) * 0.45).astype(np.uint8)
        c.a[crack, :3] = _hx(col)
    if seed % 2:  # a cave mouth lit from inside
        c.flat(c.ell(100, 150, 160, 230), "#0a0604")
        c.flat(c.rect(100, 190, 160, 250), "#0a0604")
        ra._glow(c, 130, 215, 26, lava[0], 2.0, 0.6)
    return c


# ---------------------------------------------------------------------------------------------------------------- neon signs / lit emblems (96 x 72)
def neon_set(t, kind):
    c = Cv(96, 72)
    c.paint(c.rrect(2, 2, 94, 70, 6), ramp("#07070e", "#10101c", "#181828"), c.lit((2, 2, 94, 70)), edge=True, edge_col="#2a2a40")
    col = [t["neon_a"], t["neon_b"], t["neon_c"], t["sodium"], t["neon_d"]][kind % 5]

    def tube(mask):
        e = mask & ~Cv._erode(Cv._erode(mask))
        c.a[e, :3] = _hx(col)
        c.a[e, 3] = 255
    k = kind % 5
    s = t["neon_set"]
    if s == "magic":      # crescent, star, flask, wand, key
        if k == 0:
            tube(c.ell(24, 10, 72, 62) & ~c.ell(36, 8, 84, 60))
        elif k == 1:
            pts = [(48 + math.cos(-math.pi / 2 + i * 4 * math.pi / 5) * 26, 36 + math.sin(-math.pi / 2 + i * 4 * math.pi / 5) * 26) for i in range(6)]
            tube(c.lines(pts, 3))
        elif k == 2:
            tube(c.rect(42, 8, 54, 26))
            tube(c.poly([(42, 26), (54, 26), (72, 58), (24, 58)]))
        elif k == 3:
            tube(c.lines([(20, 58), (66, 16)], 3))
            tube(c.lines([(66, 8), (66, 24)], 2))
            tube(c.lines([(58, 16), (74, 16)], 2))
        else:
            tube(c.ell(20, 16, 44, 40))
            tube(c.lines([(44, 28), (78, 28)], 3))
            tube(c.lines([(70, 28), (70, 40)], 3))
            tube(c.lines([(60, 28), (60, 38)], 3))
    elif s == "dinos":   # footprint, egg, bone, fern, volcano
        if k == 0:
            tube(c.ell(30, 36, 66, 64))
            for fx in (22, 42, 60):
                tube(c.poly([(fx + 6, 8), (fx + 14, 8), (fx + 18, 34), (fx + 4, 34)]))
        elif k == 1:
            tube(c.ell(26, 8, 70, 64))
            tube(c.lines([(34, 36), (42, 28), (50, 38), (58, 30)], 2))
        elif k == 2:
            tube(c.lines([(26, 52), (70, 20)], 4))
            tube(c.ell(16, 48, 32, 62))
            tube(c.ell(22, 54, 38, 68))
            tube(c.ell(62, 10, 78, 24))
            tube(c.ell(58, 4, 74, 18))
        elif k == 3:
            tube(c.lines([(48, 64), (48, 10)], 3))
            for yy in (18, 30, 42):
                tube(c.lines([(48, yy + 10), (28, yy)], 2))
                tube(c.lines([(48, yy + 10), (68, yy)], 2))
        else:
            tube(c.poly([(14, 62), (40, 20), (56, 20), (82, 62)]))
            tube(c.lines([(40, 20), (34, 8)], 2))
            tube(c.lines([(56, 20), (62, 8)], 2))
    else:                # transport: arrow, signal, P roundel, bus, chevrons
        if k == 0:
            tube(c.poly([(14, 28), (54, 28), (54, 14), (84, 36), (54, 58), (54, 44), (14, 44)]))
        elif k == 1:
            tube(c.rrect(32, 6, 64, 66, 6))
            for yy in (22, 36, 50):
                tube(c.ell(40, yy - 6, 56, yy + 6))
        elif k == 2:
            tube(c.ell(18, 6, 78, 66))
            tube(c.lines([(38, 20), (38, 52)], 3))
            tube(c.lines([(38, 20), (56, 20), (56, 36), (38, 36)], 3))
        elif k == 3:
            tube(c.rrect(12, 16, 84, 52, 6))
            tube(c.lines([(12, 34), (84, 34)], 2))
            tube(c.ell(22, 48, 36, 62))
            tube(c.ell(60, 48, 74, 62))
        else:
            for ox in (0, 22, 44):
                tube(c.lines([(14 + ox, 12), (34 + ox, 36), (14 + ox, 60)], 3))
    ra._glow(c, 48, 36, 40, col, 2.6, 0.35)
    return c


# ---------------------------------------------------------------------------------------------------------------- the rider's view (cells 448 x 56, 5 rows: steady, left, right, braking, jolted)
def _jolt(row, f, cw, X, Y):
    if row == 4:
        rng = np.random.RandomState(9)
        for _ in range(80):
            x, y = int(rng.rand() * cw), int(Y(14) + rng.rand() * Y(30))
            f.a[y, x, :3] = _hx("#ffe080" if rng.rand() < 0.5 else "#ffffff")
            f.a[y, x, 3] = 255


def dash_broom(t):
    """The broom from the rider's seat: the polished handle across the bottom, two gloved hands in dark sleeves, a lantern on the hook (the brake light: red-gold when braking)."""
    cw, ch = 448, 56
    X = lambda x: int(round(x * cw / 400.0))
    Y = lambda y: int(round(y * ch / 104.0))
    sheet = Cv(cw, ch * 5)
    for row in range(5):
        f = Cv(cw, ch)
        tilt = {1: -6, 2: 6}.get(row, 0)
        f.paint(f.lines([(0, Y(80) - tilt), (X(200), Y(70)), (cw, Y(80) + tilt)], 11), ramp(*t["hood"]), f.lit((0, Y(60), cw, ch), 0.55, 0.5), edge=True)
        f.flat(f.lines([(0, Y(76) - tilt), (X(200), Y(66)), (cw, Y(76) + tilt)], 2), t["hood"][3])
        for hx in (X(110), X(290)):  # sleeve and glove
            hy = Y(74) + (tilt // 2) * (1 if hx > cw // 2 else -1)
            f.paint(f.poly([(hx - 26, 0), (hx + 26, 0), (hx + 20, hy - 12), (hx - 20, hy - 12)]), ramp("#0a0614", "#1c1030", "#34205a", "#5a3c92"), f.lit((hx - 26, 0, hx + 26, hy), 0.5, 0.5), edge=True)
            f.paint(f.ell(hx - 16, hy - 16, hx + 16, hy + 8), ramp("#241408", "#5a3a1a", "#9a6a34"), f.lit((hx - 16, hy - 16, hx + 16, hy + 8), 0.55, 0.5), edge=True)
            for fi in range(4):
                f.flat(f.rect(hx - 14 + fi * 7, hy - 4, hx - 9 + fi * 7, hy + 6), "#3a2410")
        lx, ly = X(200), Y(46)
        f.flat(f.lines([(lx, 0), (lx, ly - 6)], 2), "#1a1a22")
        on = row == 3
        f.paint(f.rrect(lx - 10, ly - 6, lx + 10, ly + 14, 4), ramp("#2a1a08", "#5a3a10", "#8a6420"), f.lit((lx - 10, ly - 6, lx + 10, ly + 14)), edge=True)
        f.flat(f.rect(lx - 6, ly - 2, lx + 6, ly + 10), "#ff4a2a" if on else "#6a2a10")
        if on:
            ra._glow(f, lx, ly + 4, 30, "#ff3a1a", 1.6, 0.8)
        _jolt(row, f, cw, X, Y)
        sheet.stamp(f, 0, row * ch)
    return sheet


def dash_hood(t, kind):
    """A bonnet seen from the driver's eye (jeep: roll bar and a spare wheel; rally: a chequered stripe and a number roundel), the Space dash's frames."""
    cw, ch = 448, 56
    X = lambda x: int(round(x * cw / 400.0))
    Y = lambda y: int(round(y * ch / 104.0))
    sheet = Cv(cw, ch * 5)
    for row in range(5):
        f = Cv(cw, ch)
        tilt = {1: -5, 2: 5}.get(row, 0)
        hood = [(0, 104), (0, 50 + tilt), (60, 26 + tilt // 2), (140, 14), (260, 14), (340, 26 - tilt // 2), (400, 50 - tilt), (400, 104)]
        f.paint(f.poly([(X(x), Y(y)) for x, y in hood]), ramp(*t["hood"]), f.lit((0, Y(14), cw, ch), 0.55, 0.55), edge=True)
        if kind == "jeep":
            for sx in (X(40), X(360)):  # roll bar uprights
                f.flat(f.lines([(sx, ch), (sx - 6, 0)], 5), "#1a1c12")
            f.paint(f.ell(X(165), Y(14), X(235), Y(52)), ramp("#08080a", "#16161a", "#26262c"), f.lit((X(165), Y(14), X(235), Y(52)), 0.5, 0.5), edge=True)
            f.flat(f.ell(X(182), Y(24), X(218), Y(42)), "#3a3a40")
            f.flat(f.lines([(X(330), Y(30)), (X(330), 0), (X(344), 0)], 3), "#1a1c12")
        else:
            for k in range(14):  # a chequered stripe down the bonnet
                for j in range(3):
                    if (k + j) % 2 == 0:
                        f.flat(f.rect(X(150) + k * 8, Y(16) + j * 6, X(150) + k * 8 + 8, Y(16) + j * 6 + 6), "#f0f0f8")
            f.flat(f.ell(X(60), Y(34), X(90), Y(62)), "#f0f0f8")
            f.flat(f.ell(X(66), Y(40), X(84), Y(56)), "#d02020")
        f.paint(f.rect(0, Y(78), cw, ch), ramp("#06060c", "#10101a", "#1c1c2a"), f.lit((0, Y(78), cw, ch)), edge=False)
        f.flat(f.rect(0, Y(76), cw, Y(76) + 2), t["neon_b"])
        if row == 3:
            f.flat(f.rect(X(186), Y(84), X(214), Y(98)), "#ff2a2a")
            ra._glow(f, X(200), Y(91), 22, "#ff2a2a", 1.6, 0.7)
        else:
            f.flat(f.rect(X(186), Y(84), X(214), Y(98)), "#3a0a0a")
        if row == 4:
            _jolt(row, f, cw, X, Y)
            f.flat(f.lines([(X(90), Y(30)), (X(120), Y(44)), (X(110), Y(60)), (X(140), Y(74))], 2), "#0a0a10")
        sheet.stamp(f, 0, row * ch)
    return sheet


# ---------------------------------------------------------------------------------------------------------------- rivals and traffic (160 x 104, frames: cruising, braking, contact)
def _tail_lamps(c, frame, dx, lamp_y, xs=(16, 118)):
    on = frame == 1
    for x0 in xs:
        c.flat(c.rect(x0 + dx, lamp_y - 6, x0 + 26 + dx, lamp_y + 4), "#ff3030" if on else "#7a1418")
        c.flat(c.rect(x0 + 2 + dx, lamp_y - 4, x0 + 10 + dx, lamp_y), "#ffd0c8" if on else "#b02028")
        if on:
            ra._glow(c, x0 + 13 + dx, lamp_y, 22, "#ff2a2a", 1.8, 0.7)


def _sparks(c, frame, w, h):
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


def vehicle(paint, frame, kind):
    """kind: witch (a rider on a broom), coach (a gilded carriage), cart (a hay cart), jeep, ute (a ranger pick-up), bus (a double-decker), hatch (a rally hatchback), cab (a black cab)."""
    w, h = 160, 104
    c = Cv(w, h)
    dx = 6 if frame == 2 else 0
    wheels = True
    if kind == "witch":
        wheels = False
        c.paint(c.lines([(10 + dx, 74), (80 + dx, 70), (150 + dx, 74)], 7), ramp("#1a0c04", "#5a3410", "#a06a2c", "#d8a050"), edge=True)
        for k in range(9):  # the bristles fanned behind
            c.flat(c.lines([(80 + dx, 72), (30 + k * 12 + dx, 98)], 2), "#a07a30" if k % 2 else "#7a5a20")
        c.paint(c.poly([(46 + dx, 70), (60 + dx, 34), (100 + dx, 34), (114 + dx, 70)]), ramp(*paint), c.lit((46, 34, 114, 70), 0.55, 0.45), edge=True)
        c.paint(c.ell(66 + dx, 14, 94 + dx, 40), ramp("#3a2410", "#8a5a30", "#d89a64"), c.lit((66, 14, 94, 40)), edge=True)
        c.paint(c.poly([(54 + dx, 22), (80 + dx, 4), (106 + dx, 22)]), ramp(*paint), c.lit((54, 4, 106, 22)), edge=True)
        c.flat(c.rect(54 + dx, 20, 106 + dx, 25), paint[3])
        _tail_lamps(c, frame, dx, 76, xs=(4, 130))
    elif kind in ("coach", "cart"):
        if kind == "coach":
            c.paint(c.rrect(24 + dx, 8, 136 + dx, 82, 16), ramp(*paint), c.lit((24, 8, 136, 82), 0.55, 0.45), edge=True)
            c.paint(c.ell(54 + dx, 22, 106 + dx, 56), ramp("#0a0c16", "#151a2c", "#2a3a60", "#4a6aa0"), c.lit((54, 22, 106, 56), 0.4, 0.5), edge=True)
            c.flat(c.rect(24 + dx, 60, 136 + dx, 64), "#e8c060")
            c.flat(c.ell(70 + dx, 0, 90 + dx, 14), "#e8c060")
            _tail_lamps(c, frame, dx, 70)
        else:
            c.paint(c.rect(14 + dx, 52, 146 + dx, 84), ramp("#201008", "#5a3a18", "#8a5a28"), c.lit((14, 52, 146, 84), 0.5, 0.4), edge=True)
            c.paint(c.ell(20 + dx, 6, 140 + dx, 66), ramp(*paint), c.lit((20, 6, 140, 66), 0.55, 0.5), edge=True)
            for k in range(14):
                c.flat(c.lines([(30 + k * 8 + dx, 20 + (k % 3) * 6), (36 + k * 8 + dx, 50)], 1), paint[3])
            _tail_lamps(c, frame, dx, 68)
    elif kind == "bus":
        c.paint(c.rrect(18 + dx, 2, 142 + dx, 88, 6), ramp(*paint), c.lit((18, 2, 142, 88), 0.55, 0.45), edge=True)
        for wy in (10, 42):
            c.paint(c.rect(28 + dx, wy, 132 + dx, wy + 22), ramp("#0a0c16", "#151a2c", "#2a3a60"), c.lit((28, wy, 132, wy + 22), 0.4, 0.5))
        c.flat(c.rect(18 + dx, 34, 142 + dx, 38), "#e8e0d0")
        c.flat(c.rect(60 + dx, 66, 100 + dx, 78), "#e8e0d0")
        _tail_lamps(c, frame, dx, 72)
    elif kind == "cab":
        body = [(10, 70), (24, 36), (52, 22), (108, 22), (136, 36), (150, 70), (150, 86), (10, 86)]
        c.paint(c.poly([(x + dx, y) for x, y in body]), ramp(*paint), c.lit((10, 22, 150, 86), 0.55, 0.5), edge=True)
        c.paint(c.poly([(48 + dx, 28), (112 + dx, 28), (122 + dx, 46), (38 + dx, 46)]), ramp("#0a0c16", "#151a2c", "#2a3a60", "#4a6aa0"), c.lit((38, 28, 122, 46), 0.4, 0.6), edge=True)
        c.paint(c.rrect(64 + dx, 10, 96 + dx, 22, 3), ramp("#5a4a10", "#c8a020", "#ffe070"), c.lit((64, 10, 96, 22)))
        _tail_lamps(c, frame, dx, 60)
    elif kind == "ute":
        c.paint(c.poly([(x + dx, y) for x, y in [(10, 70), (30, 36), (60, 28), (100, 28), (118, 40), (150, 56), (150, 86), (10, 86)]]), ramp(*paint), c.lit((10, 28, 150, 86), 0.55, 0.5), edge=True)
        c.paint(c.poly([(52 + dx, 32), (96 + dx, 32), (106 + dx, 46), (44 + dx, 46)]), ramp("#0a0c16", "#151a2c", "#2a3a60"), c.lit((44, 32, 106, 46), 0.4, 0.6), edge=True)
        for bx in range(112, 148, 8):  # the cage bars on the bed
            c.flat(c.lines([(bx + dx, 56), (bx + dx, 38)], 2), "#1c1e16")
        c.flat(c.lines([(110 + dx, 38), (148 + dx, 38)], 2), "#1c1e16")
        _tail_lamps(c, frame, dx, 66)
    elif kind == "jeep":
        c.paint(c.rrect(14 + dx, 30, 146 + dx, 84, 8), ramp(*paint), c.lit((14, 30, 146, 84), 0.55, 0.5), edge=True)
        c.flat(c.lines([(26 + dx, 30), (26 + dx, 6), (134 + dx, 6), (134 + dx, 30)], 4), "#12140c")
        c.paint(c.ell(56 + dx, 36, 104 + dx, 82), ramp("#08080a", "#16161a", "#26262c"), c.lit((56, 36, 104, 82), 0.5, 0.5), edge=True)
        c.flat(c.ell(70 + dx, 50, 90 + dx, 70), "#3a3a40")
        _tail_lamps(c, frame, dx, 50)
    else:  # hatch: a rally hatchback with a roof number plate and a white bumper plate
        body = [(14, 74), (26, 38), (54, 22), (106, 22), (134, 38), (146, 74), (146, 86), (14, 86)]
        c.paint(c.poly([(x + dx, y) for x, y in body]), ramp(*paint), c.lit((14, 22, 146, 86), 0.55, 0.5), edge=True)
        c.paint(c.poly([(50 + dx, 28), (110 + dx, 28), (122 + dx, 46), (38 + dx, 46)]), ramp("#0a0c16", "#151a2c", "#2a3a60", "#4a6aa0"), c.lit((38, 28, 122, 46), 0.4, 0.6), edge=True)
        c.flat(c.rect(62 + dx, 26, 98 + dx, 29), "#f0f0f8")
        c.flat(c.rect(60 + dx, 52, 100 + dx, 60), "#f0f0f8")
        c.flat(c.rect(70 + dx, 53, 90 + dx, 59), "#14141e")
        _tail_lamps(c, frame, dx, 62)
    if wheels:
        c.flat(c.rect(14 + dx, 86, 146 + dx, 92), "#0c0c14")
        for x0 in (20, 112):
            c.paint(c.rrect(x0 + dx, 84, x0 + 28 + dx, 102, 4), ramp("#08080c", "#14141e", "#22222e"), c.lit((x0, 84, x0 + 28, 102)))
    _sparks(c, frame, w, h)
    return c


# ---------------------------------------------------------------------------------------------------------------- weather (four frames, 200 x 120)
def weather(t, kind):
    """motes: fireflies drifting up and twinkling; embers: sparks falling slanted."""
    cw, ch = 200, 120
    sheet = Cv(cw * 4, ch)
    rng = np.random.RandomState(3)
    pts = [(rng.rand() * cw, rng.rand() * ch, 0.5 + rng.rand()) for _ in range(34)]
    for k in range(4):
        f = Cv(cw, ch)
        for (x, y, v) in pts:
            if kind == "motes":
                yy = (y - k * ch / 4 * v) % ch
                xx = (x + math.sin(k * 1.3 + x) * 5) % cw
                col = t["sodium"] if (k + int(x)) % 3 else t["neon_c"]
            else:
                yy = (y + k * ch / 4 * v) % ch
                xx = (x + yy * 0.25) % cw
                col = t["neon_b"] if int(x) % 2 else t["neon_a"]
            f.a[int(yy):int(yy) + 2, int(xx):int(xx) + 2, :3] = _hx(col)
            f.a[int(yy):int(yy) + 2, int(xx):int(xx) + 2, 3] = 255
        sheet.stamp(f, k * cw, 0)
    return sheet
