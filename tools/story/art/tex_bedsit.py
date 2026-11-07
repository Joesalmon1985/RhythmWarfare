"""The bedsit's textures and sprites (content/story/maps/bedsit.json), drawn in numpy and PIL at 160 texels per metre (docs/art/STYLE_GUIDE.md section 7),
dithered onto warm ramps, lit from the upper left, a one-pixel darker edge on every shape (ruling 36: dense pixel painting, no flat fills).

    python3 tools/story/build_bedsit.py          # writes assets/story/bedsit/textures/*.png, manifest.json and content/story/maps/bedsit.json

`build()` returns {name: (kind, image, metres_or_none)}: kind "tile" (opaque RGB, repeats every `metres`), "decal" (RGBA, flat on a wall) or "thing" (RGBA billboard).
The room is 4 x 5 m, 2.5 m high; the camera stands in the middle. The plan the floor texture is drawn from has north up and east to the right.
"""
from __future__ import annotations

import math

import numpy as np

from . import pixeltex as px
from .bedsit_draw import PPM, Cv, fnoise, glow_disc, m2px, periodic_noise, ramp, speckle, stretched

H = np.float32

# ---- ramps (dark to light) -------------------------------------------------------------------------------------------------------------------------
WOOD = ramp("#24130e", "#42261a", "#65401f", "#8a5c30", "#ad7f46", "#cfa263")
OAK = ramp("#2b1a12", "#4b2f1f", "#704a2c", "#96683c", "#b98a52", "#d9ae74")
PAPER = ramp("#3b2a28", "#5f4540", "#876650", "#ad8864", "#cfae82", "#e6cfa0")
OLIVE = ramp("#1c2820", "#2f4237", "#48604b", "#648163", "#85a07c", "#a6bd96")
CREAM = ramp("#3d3631", "#6b6057", "#9a8d7b", "#c4b69c", "#e0d3b6", "#f0e6cc")
PLASTER = ramp("#4a423d", "#75695f", "#9d8f80", "#bcae98", "#d6c8ae", "#e8dcc2")
IRON = ramp("#14121a", "#26232f", "#3c3949", "#58556a", "#7a778c", "#a3a1b5")
MUSTARD = ramp("#4a2e0c", "#7a4d12", "#a6721c", "#cf9a2c", "#e8b94a", "#f6d77a")
RUST = ramp("#2e0f10", "#521a1a", "#7c2b26", "#a5442f", "#c76a40", "#e29360")
TEAL = ramp("#0b2326", "#14403f", "#206260", "#318681", "#52aaa0", "#86cdbd")
INDIGO = ramp("#0b0b24", "#17163f", "#2a2870", "#443f9e", "#6862c4", "#9890e2")
GREEN = ramp("#0b2410", "#143f1c", "#1f6129", "#328a38", "#56b04a", "#8cd470")
PINK = ramp("#3a0f2a", "#6b1c47", "#a22e68", "#d2528a", "#ee85ae", "#fbbdd2")
SKY = ramp("#06061c", "#0c0c38", "#181656", "#2a2278", "#4a3a9a", "#7456b8")
GOLD = ramp("#4a3008", "#7a5210", "#b07f1c", "#dcab34", "#f4cf5c", "#fff1a8")
STEEL = ramp("#16181f", "#2b303b", "#444b5a", "#646d7e", "#8c95a6", "#bcc4d2")
RED = ramp("#2b0808", "#561214", "#8a1c1e", "#c02a2a", "#e25040", "#f68a70")
WHITE = ramp("#3a3a48", "#6a6a7e", "#9a9aae", "#c4c4d4", "#e2e2ec", "#f6f6fa")
SKIN = ramp("#4a2a22", "#7a4634", "#a8684a", "#cd8a64", "#e8ac84", "#f6ccaa")


def hx(c):
    return px.hexc(c) * 255


# ================================================================================ tiles ===========================================================================

def wall_paper(variant: int) -> np.ndarray:
    """Wallpaper, a painted dado, skirting and cornice: one repeat is 2.5 m (floor to ceiling), 160 px a metre, periodic along the wall."""
    n = 400
    cv = Cv(n, n)
    yy, xx = cv.yy, cv.xx
    sh = np.full((n, n), 0.5, np.float32)
    cols = np.zeros((n, n, 3), np.uint8)
    noise = px.noise(n, 10, 40 + variant, 3)
    fine = px.noise(n, 3, 90 + variant, 2)
    # paper (rows 16..244): cream-ochre stripes with terracotta sprigs
    stripe = ((xx % 20) < 5).astype(np.float32)
    s_paper = 0.62 + 0.05 * (1 - stripe) - 0.10 * stripe + (noise - 0.5) * 0.18 + (fine - 0.5) * 0.10
    # sprig motif every 40 px, offset on alternate rows of 40
    row = (yy // 40).astype(int)
    ox = np.where(row % 2 == 0, 20, 0)
    fx = (xx + ox) % 40 - 20
    fy = yy % 40 - 20
    flower = (np.abs(fx) + np.abs(fy) < 6.5) & ((yy > 16) & (yy < 244))
    centre = (np.abs(fx) + np.abs(fy) < 2.5) & flower
    leaf = ((np.abs(fx) < 1.4) & (fy > 6) & (fy < 15)) | ((np.abs(fx - fy * 0.8 + 6) < 1.3) & (fy > 7) & (fy < 14))
    paper = px.quantise(s_paper, PAPER, 1.0)
    paper[flower & ~centre] = (hx("#b2573a")).astype(np.uint8)
    paper[centre] = (hx("#e8c070")).astype(np.uint8)
    paper[leaf & ~flower] = (hx("#7d8a58")).astype(np.uint8)
    # a faded tide-line of damp at the top, grime lower
    damp = np.clip((noise - 0.62) * 4.0, 0, 1) * np.clip((yy - 150) / 90, 0, 1) * 0.4
    paper = (paper.astype(np.float32) * (1 - damp[..., None] * 0.45)).astype(np.uint8)
    cols[:] = paper
    # cornice (0..16)
    cs = 0.78 - 0.22 * (yy / 16) + (fine - 0.5) * 0.1
    cs = np.where((yy > 3) & (yy < 6), cs + 0.12, cs)
    cs = np.where((yy >= 12) & (yy < 14), cs - 0.2, cs)
    cornice = px.quantise(cs, PLASTER, 1.0)
    cols[:16] = cornice[:16]
    # dado rail (244..254)
    dr = 0.7 - 0.5 * ((yy - 244) / 10) + (stretched(n, n, 40, 2, 5 + variant) - 0.5) * 0.3
    rail = px.quantise(dr, OAK, 1.0)
    cols[244:254] = rail[244:254]
    # painted woodchip below (254..382): dusty olive, speckled
    woodchip = (px.noise(n, 3.5, 12 + variant, 2) - 0.5) * 0.45
    ls = 0.46 + woodchip + (noise - 0.5) * 0.14 + np.clip((yy - 254) / 128, 0, 1) * -0.06
    chip = ((fine > 0.78)).astype(np.float32) * 0.1
    low = px.quantise(ls + chip, OLIVE, 1.0)
    # scuffs at hand height and by the skirting
    rng = np.random.RandomState(100 + variant)
    for _ in range(9):
        x = rng.randint(0, n)
        y = rng.randint(262, 372)
        ln = rng.randint(6, 20)
        for i in range(ln):
            xi = (x + i) % n
            yi = min(y + (i // 5), 381)
            low[yi, xi] = (hx("#a6bd96") * 0.88).astype(np.uint8)
    cols[254:382] = low[254:382]
    # skirting (382..400)
    ks = 0.8 - 0.35 * np.clip((yy - 382) / 18, 0, 1) + (fine - 0.5) * 0.12
    ks = np.where((yy >= 382) & (yy < 385), ks + 0.15, ks)
    skirt = px.quantise(ks, CREAM, 1.0)
    # chipped paint shows the wood
    chips = (px.noise(n, 5, 77 + variant, 2) > 0.8) & (yy >= 386)
    skirt[chips] = (hx("#65401f")).astype(np.uint8)
    cols[382:] = skirt[382:]
    # grime near the floor and a darker shadow under the cornice
    g = np.clip((yy - 330) / 70, 0, 1)[..., None] * 0.22
    cols = (cols.astype(np.float32) * (1 - g)).astype(np.uint8)
    return cols


def ceiling_plaster() -> np.ndarray:
    n = 400
    a = px.noise(n, 14, 61, 3)
    b = px.noise(n, 4, 62, 2)
    sh = 0.62 + (a - 0.5) * 0.34 + (b - 0.5) * 0.16
    stain = np.clip((px.noise(n, 60, 63, 2) - 0.6) * 3, 0, 1) * 0.2
    return px.quantise(sh - stain, PLASTER, 1.0)


# ---- the floor: a 5 x 5 m painted plan, north up, east right; the plan's (0, 0) is the tile's top left so the room's origin lands on the tile corner ------------------------------

def _P(x, z):
    return 400 + x * PPM, 400 + z * PPM


def floor_room() -> np.ndarray:
    n = 800
    cv = Cv(n, n)
    yy, xx = cv.yy, cv.xx
    # boards run east-west, 0.1 m wide, 1.3 m long, staggered
    bh = 16
    r = (yy // bh).astype(int)
    rng = np.random.RandomState(7)
    off = rng.rand(60) * 208
    tone = rng.rand(60) * 0.28
    L = 208
    bx = ((xx + off[r % 60]) // L).astype(int)
    tone2 = np.random.RandomState(9).rand(24, 8)[(r % 24), (bx % 8)] * 0.22
    joint = ((yy % bh) < 1) | (((xx + off[r % 60]) % L) < 1)
    grain = np.sin(xx * 0.09 + stretched(n, n, 60, 3, 3) * 9.0) * 0.07
    sh = 0.46 + tone[r % 60] * 0.5 + tone2 + grain + (fnoise(n, n, 40, 4) - 0.5) * 0.14 - 0.3 * joint
    # nail heads
    sh = np.where(speckle(n, n, 0.0007, 5), 0.85, sh)
    rgb = px.quantise(np.clip(sh, 0, 1), OAK, 1.0).astype(np.float32)
    # varnish worn pale along the walking line (door to window) and dark near the walls
    walk = np.exp(-((xx - 400) / 90.0) ** 2) * 0.1
    rgb = rgb * (1 + walk[..., None])
    wall_dark = np.clip(1 - np.minimum(np.minimum(xx - 40, 760 - xx), np.minimum(yy, 800 - yy)) / 60, 0, 1) * 0.35
    rgb = rgb * (1 - wall_dark[..., None])
    cv.a[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    cv.a[..., 3] = 255

    def shadow(x0, z0, x1, z1, k=0.5, soft=7):
        a0, b0 = _P(x0, z0)
        a1, b1 = _P(x1, z1)
        d = np.maximum(np.maximum(a0 - xx, xx - a1), np.maximum(b0 - yy, yy - b1))
        t = np.clip(1 - d / soft, 0, 1)
        dith = px.BAYER8[(np.arange(n)[:, None] % 8), (np.arange(n)[None, :] % 8)] + 0.5
        m = (t > dith * 0.98) | ((d <= 0))
        cv.a[m, :3] = (cv.a[m, :3].astype(np.float32) * k).astype(np.uint8)

    # furniture footprints (the bed, the desk, the wardrobe, the clothes rail, the plant)
    shadow(-2.0, -2.5, -0.98, -0.42, 0.42)
    shadow(1.38, -0.8, 2.0, 0.8, 0.45)
    shadow(-0.65, 2.0, 0.65, 2.5, 0.45)
    shadow(0.7, 2.15, 1.55, 2.5, 0.5)
    shadow(1.45, 0.95, 1.9, 1.4, 0.55, 5)
    shadow(-0.95, -2.5, 0.95, -2.2, 0.55, 5)  # the radiator under the window

    # ---- light spilling on the boards from the four thresholds (painted, additive; the map's lights add the rest) ----
    def pool(cx, cz, rx, rz, col, strength, mask_fn=None):
        a, b = _P(cx, cz)
        d = np.sqrt(((xx - a) / (rx * PPM)) ** 2 + ((yy - b) / (rz * PPM)) ** 2)
        t = np.clip(1 - d, 0, 1) ** 1.6 * strength
        dith = px.BAYER8[(np.arange(n)[:, None] % 8), (np.arange(n)[None, :] % 8)] * 0.18
        t = np.clip(t + dith * (t > 0.02), 0, 1)
        q = np.round(t * 5) / 5.0
        c = hx(col)
        cv.a[..., :3] = np.clip(cv.a[..., :3].astype(np.float32) * (1 - q[..., None] * 0.5) + c * q[..., None] * 0.7, 0, 255).astype(np.uint8)

    pool(0.0, -1.55, 0.9, 0.8, "#6a58d8", 0.8)            # north: the window's night glow
    pool(0.25, 1.75, 0.8, 0.75, "#e87ad0", 0.9)           # south: iridescent light under the wardrobe door
    pool(0.0, 1.55, 0.5, 0.6, "#5fe0d0", 0.5)
    pool(1.45, 0.0, 0.7, 0.9, "#7adf58", 0.75)            # east: green light from the jungle
    pool(-1.5, 0.35, 0.6, 0.7, "#ffb347", 0.8)            # west: sodium light under the door
    pool(1.45, -1.9, 0.9, 0.7, "#ffc070", 0.55)          # the standing lamp

    # ---- the rug, 2 x 2.8 m, kilim-ish: burgundy field, cream and indigo diamonds, fringe at the short ends ----
    x0, z0 = _P(-1.0, -1.4)
    x1, z1 = _P(1.0, 1.4)
    inside = (xx >= x0) & (xx < x1) & (yy >= z0) & (yy < z1)
    fx, fy = (xx - x0), (yy - z0)
    bw = 22  # border
    in_field = inside & (fx >= bw) & (fx < (x1 - x0) - bw) & (yy >= z0 + bw) & (yy < z1 - bw)
    P = 40
    dm = np.abs((fx % P) - P / 2) + np.abs((fy % P) - P / 2)
    cxm, cym = (x0 + x1) / 2, (z0 + z1) / 2
    dc = np.abs(xx - cxm) * 0.72 + np.abs(yy - cym) * 0.5
    rs = 0.34 + (stretched(n, n, 2, 2, 11) - 0.5) * 0.22  # woven stipple
    rug = px.quantise(rs, RUST, 1.0)
    rug[in_field & (dm < 5)] = hx("#e8d4a8").astype(np.uint8)
    rug[in_field & (dm >= 5) & (dm < 9)] = hx("#2a2870").astype(np.uint8)
    med = in_field & (dc < 64)
    rug[med] = hx("#26224f").astype(np.uint8)
    rug[med & (dc < 52) & (dc >= 44)] = hx("#e8c070").astype(np.uint8)
    rug[med & (dc < 36) & (dc >= 28)] = hx("#c76a40").astype(np.uint8)
    rug[med & (dc < 18)] = hx("#e8d4a8").astype(np.uint8)
    rug[med & (dc < 8)] = hx("#a22e68").astype(np.uint8)
    # border: stripes
    brd = inside & ~in_field
    bd = np.minimum(np.minimum(fx, (x1 - x0) - 1 - fx), np.minimum(fy, (z1 - z0) - 1 - fy))
    rug[brd] = hx("#521a1a").astype(np.uint8)
    rug[brd & (bd >= 3) & (bd < 6)] = hx("#e8c070").astype(np.uint8)
    rug[brd & (bd >= 6) & (bd < 15)] = np.where(((fx + fy)[brd & (bd >= 6) & (bd < 15)] % 12 < 6)[:, None], hx("#2a2870"), hx("#7c2b26")).astype(np.uint8)
    rug[brd & (bd >= 15) & (bd < 18)] = hx("#e8c070").astype(np.uint8)
    # worn patches and a scuffed edge, soft shading from the pile
    wear = fnoise(n, n, 30, 14) > 0.7
    rug[inside & wear] = (rug[inside & wear].astype(np.float32) * 0.82 + 30).clip(0, 255).astype(np.uint8)
    # lit from upper left: the rug's own edge catches light
    edge_in = inside & ((fx < 2) | (fy < 2))
    edge_out = inside & ((fx > (x1 - x0) - 3) | (fy > (z1 - z0) - 3))
    rug[edge_in] = np.clip(rug[edge_in].astype(np.float32) * 1.25, 0, 255).astype(np.uint8)
    rug[edge_out] = (rug[edge_out].astype(np.float32) * 0.6).astype(np.uint8)
    # the rug throws a soft shadow on the boards (right and down)
    sh_m = ((xx >= x0 + 3) & (xx < x1 + 4) & (yy >= z0 + 3) & (yy < z1 + 4)) & ~inside
    cv.a[sh_m, :3] = (cv.a[sh_m, :3].astype(np.float32) * 0.62).astype(np.uint8)
    cv.a[inside, :3] = rug[inside]
    # fringe at the short ends (north and south edges)
    rng2 = np.random.RandomState(21)
    for side in (0, 1):
        for i in range(int(x0) + 3, int(x1) - 2, 3):
            ln = 8 + rng2.randint(0, 5)
            y_a = int(z0) - ln if side == 0 else int(z1)
            sl = slice(max(y_a, 0), min(y_a + ln, n))
            cv.a[sl, i, :3] = hx("#d9c9a0").astype(np.uint8)
            cv.a[sl, i + 1, :3] = hx("#a89a78").astype(np.uint8)

    # ---- things on the floor (plan views) ----
    def blob(cx, cz, rx, rz, pal, seed, ang=0.0):
        a, b = _P(cx, cz)
        c, s = math.cos(ang), math.sin(ang)
        dx, dy = xx - a, yy - b
        u = (dx * c + dy * s) / (rx * PPM)
        v = (-dx * s + dy * c) / (rz * PPM)
        m = u * u + v * v < 1.0
        shd = 0.5 + (fnoise(n, n, 6, seed) - 0.5) * 0.5 - 0.3 * (u + v) * 0.5
        cv.paint(m, pal, shd)

    blob(-0.95, 0.28, 0.17, 0.11, TEAL, 31, 0.5)         # a rolled sock
    blob(-0.78, 0.4, 0.15, 0.09, MUSTARD, 32, -0.4)
    blob(1.45, 1.2, 0.34, 0.21, INDIGO, 33, 0.3)         # the laundry heap by the clothes rail
    blob(1.34, 1.14, 0.18, 0.13, PINK, 34, -0.6)
    blob(1.6, 1.3, 0.14, 0.1, RUST, 35, 0.9)
    # a vinyl record half out of its sleeve, by the rug's corner
    sx, sz = _P(0.72, 0.62)
    sleeve = cv.rect(int(sx - 25), int(sz - 25), int(sx + 25), int(sz + 25))
    cv.paint(sleeve, MUSTARD, cv.lit((sx - 25, sz - 25, sx + 25, sz + 25), 0.55, 0.3, 0.1, 41))
    cv.paint(cv.ell(int(sx - 10), int(sz - 12), int(sx + 10), int(sz + 8)), RED, cv.dome(sx, sz - 2, 10, 10, 0.5, 0.5))
    dx0, dz0 = sx + 21, sz - 3
    disc = cv.ell(int(dx0 - 22), int(dz0 - 22), int(dx0 + 22), int(dz0 + 22)) & ~sleeve
    cv.paint(disc, IRON, cv.lit((dx0 - 22, dz0 - 22, dx0 + 22, dz0 + 22), 0.3, 0.3, 0.06, 42))
    cv.paint(cv.ell(int(dx0 - 6), int(dz0 - 6), int(dx0 + 6), int(dz0 + 6)) & ~sleeve, PINK, edge=False)
    # slippers
    for k, (cx, cz) in enumerate([(-1.45, 0.62), (-1.28, 0.74)]):
        blob(cx, cz, 0.12, 0.06, RED if k == 0 else RUST, 50 + k, 0.2 + k * 0.1)
    # a mug on its side, a paperback face down
    a, b = _P(-0.38, 0.96)
    book = cv.rect(int(a - 18), int(b - 12), int(a + 18), int(b + 12))
    cv.paint(book, GREEN, cv.lit((a - 18, b - 12, a + 18, b + 12), 0.5, 0.3, 0.1, 55))
    cv.flat(cv.rect(int(a - 16), int(b - 10), int(a - 13), int(b + 10)), "#e8d4a8")
    mc = _P(0.12, 1.2)
    cv.paint(cv.ell(int(mc[0] - 9), int(mc[1] - 9), int(mc[0] + 9), int(mc[1] + 9)), CREAM, cv.dome(mc[0], mc[1], 9, 9, 0.5, 0.5))
    cv.paint(cv.ell(int(mc[0] - 6), int(mc[1] - 6), int(mc[0] + 6), int(mc[1] + 6)), RUST, edge=False)
    # the headphone lead from the desk, a wavy dark line along the boards
    pts = [(_P(1.85, 0.35)[0] - i * 7, _P(1.85, 0.35)[1] + 22 * math.sin(i * 0.5) + i * 1.3) for i in range(0, 30)]
    cv.flat(cv.lines(pts, 2), "#14121a")
    # a puddle of mid-night spilt light under the door (the door is on the west wall)
    return cv.a[..., :3].copy()


def tile_floor() -> np.ndarray:
    plan = floor_room()
    return np.roll(np.roll(plan, 400, axis=1), 400, axis=0)  # plan (0,0) is x=-2.5, z=-2.5; the tile's (0,0) is world (0,0)


# ================================================================================ decals ==========================================================================

def _edge_pal(cv):
    return None


def curtains(cv: Cv, x0, x1, y0, y1, pal=MUSTARD, seed=1, pattern=True, gather=0.0):
    """A curtain panel with vertical folds and a printed pattern, lit from the left."""
    w = x1 - x0
    m = cv.rect(x0, y0, x1, y1)
    folds = np.sin((cv.xx - x0) / w * math.pi * 4.0 + seed) * 0.5 + 0.5
    sh = 0.3 + 0.4 * folds + (fnoise(cv.h, cv.w, 8, seed) - 0.5) * 0.12 + cv.lit((x0, y0, x1, y1), 0.0, 0.18)
    sh = sh * (1 - 0.18 * np.clip((cv.yy - y0) / max(y1 - y0, 1), 0, 1))
    cv.paint(m, pal, sh)
    if pattern:  # a retro circle print
        for cy in range(y0 + 10, y1 - 4, 22):
            for cx in range(x0 + 6 + (cy // 22 % 2) * 11, x1 - 3, 22):
                d = cv.ell(cx - 4, cy - 4, cx + 5, cy + 5) & m
                cv.tint(d, "#3a1c10", 0.55)
    cv.flat(cv.rect(x0, y0, x1, y0 + 3), "#2b1a12")  # rail pocket


def window_frame(w=304, h=232) -> tuple:
    """The window: frame, curtains and sill with a hole where the glass is. Returns (frame canvas, glass box (x0,y0,x1,y1))."""
    cv = Cv(w, h)
    gx0, gy0, gx1, gy1 = 62, 20, 242, 186
    # outer architrave and frame in chipped cream paint
    frame = cv.rect(gx0 - 12, gy0 - 12, gx1 + 12, gy1 + 12)
    cv.paint(frame, CREAM, cv.lit((gx0 - 12, gy0 - 12, gx1 + 12, gy1 + 12), 0.62, 0.3, 0.12, 3))
    # chips showing wood
    chips = (fnoise(h, w, 4, 8) > 0.84) & frame
    cv.flat(chips, "#65401f")
    # the glass hole
    glass = cv.rect(gx0, gy0, gx1, gy1)
    cv.erase(glass)
    # glazing bars: a vertical mullion and a transom, in front of the glass
    mx = (gx0 + gx1) // 2
    ty = gy0 + 70
    bars = cv.rect(mx - 3, gy0, mx + 3, gy1) | cv.rect(gx0, ty - 3, gx1, ty + 3)
    cv.paint(bars, CREAM, cv.lit((gx0, gy0, gx1, gy1), 0.6, 0.3, 0.1, 5))
    # an inner dark rebate line round the glass
    inner = cv.rect(gx0 - 3, gy0 - 3, gx1 + 3, gy1 + 3) & ~glass
    cv.paint(inner, WOOD, cv.lit((gx0, gy0, gx1, gy1), 0.4, 0.3), edge=False)
    # sill: a board across the bottom, projecting, lit on top
    sill_top = cv.rect(gx0 - 22, gy1 + 8, gx1 + 22, gy1 + 18)
    cv.paint(sill_top, CREAM, 0.88 - cv.lit((0, gy1 + 8, 0, gy1 + 18), 0.0, 0.0) + 0.0 * cv.xx)
    sill_front = cv.rect(gx0 - 22, gy1 + 18, gx1 + 22, gy1 + 26)
    cv.paint(sill_front, CREAM, np.full((h, w), 0.52, np.float32) + (fnoise(h, w, 6, 9) - 0.5) * 0.2)
    # curtains, pulled back either side with ties
    curtains(cv, 4, 54, 6, 214, MUSTARD, 1)
    curtains(cv, 250, 300, 6, 214, MUSTARD, 3)
    for tx0 in (4, 250):
        tie = cv.rect(tx0 - 1, 120, tx0 + 51, 126)
        cv.paint(tie, RUST, cv.lit((tx0, 120, tx0 + 50, 126), 0.5, 0.3))
    return cv, (gx0, gy0, gx1, gy1)


def window_glass(box) -> Cv:
    """The night through the window (emissive): indigo sky, a ringed planet, stars, a rooftop skyline and a nebula glow behind it."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    cv = Cv(w, h)
    yy, xx = cv.yy, cv.xx
    t = yy / h
    sh = 0.14 + 0.55 * t ** 1.4 + (fnoise(h, w, 24, 3) - 0.5) * 0.12
    sky = px.quantise(sh, SKY, 1.0)
    # nebula glow beyond the rooftops: magenta, cyan and gold
    for cx, cy, r, col, k in [(w * 0.62, h * 0.78, 90, "#ff5ac8", 0.8), (w * 0.35, h * 0.82, 70, "#4ce6ff", 0.7), (w * 0.5, h * 0.9, 120, "#ffd070", 0.5)]:
        g = glow_disc(h, w, cx, cy, r, 1.8) * k
        g = np.clip(g + (px.BAYER8[(np.arange(h)[:, None] % 8), (np.arange(w)[None, :] % 8)]) * 0.12 * (g > 0.03), 0, 1)
        g = np.round(g * 4) / 4
        sky = np.clip(sky.astype(np.float32) * (1 - g[..., None] * 0.7) + hx(col) * g[..., None] * 0.9, 0, 255).astype(np.uint8)
    cv.a[..., :3] = sky
    cv.a[..., 3] = 255
    rng = np.random.RandomState(12)
    for _ in range(46):  # stars
        x, y = rng.randint(2, w - 2), rng.randint(2, int(h * 0.62))
        col = ["#ffffff", "#bcd8ff", "#ffe8b0"][rng.randint(0, 3)]
        cv.dots([(x, y)], col)
        if rng.rand() < 0.25:
            cv.dots([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)], "#8aa0e0")
    # ringed planet, upper right
    pc = (w * 0.74, h * 0.24)
    ring = cv.ell(int(pc[0] - 30), int(pc[1] - 7), int(pc[0] + 30), int(pc[1] + 8))
    planet = cv.ell(int(pc[0] - 14), int(pc[1] - 14), int(pc[0] + 14), int(pc[1] + 14))
    back = ring & (cv.yy < pc[1])
    cv.paint(back, GOLD, cv.lit((pc[0] - 30, pc[1] - 7, pc[0] + 30, pc[1] + 8), 0.55, 0.3), edge=False)
    cv.paint(planet, PINK, cv.dome(pc[0], pc[1], 14, 14, 0.5, 0.6))
    front = ring & (cv.yy >= pc[1]) & ~cv.ell(int(pc[0] - 26), int(pc[1] - 2), int(pc[0] + 26), int(pc[1] + 4))
    cv.paint(front, GOLD, cv.lit((pc[0] - 30, pc[1], pc[0] + 30, pc[1] + 8), 0.65, 0.3), edge=False)
    # a crescent moon, left
    mc = (w * 0.2, h * 0.2)
    moon = cv.ell(int(mc[0] - 9), int(mc[1] - 9), int(mc[0] + 9), int(mc[1] + 9)) & ~cv.ell(int(mc[0] - 4), int(mc[1] - 11), int(mc[0] + 12), int(mc[1] + 7))
    cv.paint(moon, WHITE, cv.dome(mc[0] - 4, mc[1], 10, 10, 0.7, 0.4), edge=False)
    # a thin streak of a shooting star
    cv.flat(cv.line((int(w * 0.42), int(h * 0.12)), (int(w * 0.52), int(h * 0.22)), 1), "#ffffff")
    # rooftops: dark silhouettes with lit windows and chimney pots, in two layers
    for layer, (base, col, seed) in enumerate([(0.78, "#1b1a40", 5), (0.86, "#100f2a", 8)]):
        rr = np.random.RandomState(seed)
        x = -4
        while x < w:
            bw = rr.randint(14, 30)
            bh = int(h * (1 - base) * (0.5 + rr.rand() * 0.9))
            top = int(h * base) + 4 - bh + (0 if layer == 0 else 8)
            body = cv.rect(x, top, x + bw, h)
            cv.flat(body, col)
            if rr.rand() < 0.5:
                cv.flat(cv.poly([(x - 1, top), (x + bw // 2, top - rr.randint(4, 9)), (x + bw + 1, top)]), col)
            if rr.rand() < 0.4:
                cv.flat(cv.rect(x + 3, top - 5, x + 6, top), col)
            for wy in range(top + 5, h - 3, 8):
                for wx in range(x + 3, x + bw - 3, 7):
                    if rr.rand() < 0.28:
                        cv.dots([(wx, wy), (wx + 1, wy), (wx, wy + 1), (wx + 1, wy + 1)], ["#ffd070", "#ffb347", "#9fe8ff"][rr.randint(0, 3)])
            x += bw
    return cv


def radiator(w=160, h=88) -> Cv:
    cv = Cv(w, h)
    # a panel radiator with fins, pipe and valve
    body = cv.rect(8, 12, w - 8, h - 10)
    cv.paint(body, CREAM, cv.lit((8, 12, w - 8, h - 10), 0.66, 0.3, 0.06, 4))
    for x in range(14, w - 10, 9):
        cv.shade_mul(cv.rect(x, 14, x + 3, h - 12), 0.72)
        cv.shade_mul(cv.rect(x - 1, 14, x, h - 12), 1.08)
    cv.paint(cv.rect(4, 6, w - 4, 14), CREAM, cv.lit((4, 6, w - 4, 14), 0.78, 0.2))
    cv.paint(cv.rect(w - 20, h - 12, w - 12, h), IRON, cv.round_x(w - 20, w - 12, 0.55, 0.4))
    cv.paint(cv.rect(14, h - 12, 22, h), IRON, cv.round_x(14, 22, 0.55, 0.4))
    cv.paint(cv.ell(w - 22, h - 24, w - 8, h - 10), GOLD, cv.dome(w - 15, h - 17, 7, 7, 0.5, 0.5))
    # a sock drying on top
    cv.paint(cv.poly([(30, 8), (52, 8), (54, 0), (34, -4)]) & cv.rect(0, 0, w, 12), TEAL, cv.lit((30, 0, 54, 12), 0.5, 0.3), edge=True)
    return cv


def _box(cv, x0, y0, x1, y1, pal, base=0.58, spread=0.32, noise=0.1, seed=1, edge=True):
    m = cv.rect(x0, y0, x1, y1)
    cv.paint(m, pal, cv.lit((x0, y0, x1, y1), base, spread, noise, seed), edge=edge)
    return m


def wardrobe_frame() -> tuple:
    """A 70s wardrobe against the south wall: left door shut, right door ajar with a slot of dark. Returns (frame canvas, slot box)."""
    w, h = 208, 336
    cv = Cv(w, h)
    # plinth, carcass
    _box(cv, 0, 24, w, h - 14, WOOD, 0.6, 0.35, 0.16, 6)
    stretch = stretched(h, w, 3, 40, 8)  # veneer grain running vertically
    cv.shade_mul(cv.rect(0, 24, w, h - 14) & (stretch > 0.55), 1.12)
    cv.shade_mul(cv.rect(0, 24, w, h - 14) & (stretch < 0.3), 0.88)
    # cornice and plinth
    _box(cv, -0 + 2, 6, w - 2, 24, WOOD, 0.74, 0.3, 0.08, 7)
    _box(cv, 6, h - 14, w - 6, h, WOOD, 0.35, 0.2, 0.06, 9)
    # left door (shut), with a raised panel
    _box(cv, 8, 34, 100, h - 22, OAK, 0.58, 0.3, 0.12, 10)
    _box(cv, 20, 52, 88, 142, OAK, 0.52, 0.35, 0.1, 11)
    _box(cv, 20, 156, 88, h - 40, OAK, 0.52, 0.35, 0.1, 12)
    cv.paint(cv.ell(88, 176, 96, 192), GOLD, cv.dome(91, 183, 5, 7, 0.5, 0.6))
    # right door ajar: the gap is a dark slot with light pouring out (transparent here, the light decal shows through)
    slot = (106, 34, 124, h - 22)
    cv.erase(cv.rect(*slot))
    # the open door, foreshortened to a thin edge on the right of the slot
    _box(cv, 124, 34, 134, h - 22, OAK, 0.46, 0.25, 0.1, 13)
    _box(cv, 134, 34, 200, h - 22, OAK, 0.58, 0.3, 0.12, 14)
    _box(cv, 144, 52, 190, 142, OAK, 0.52, 0.35, 0.1, 15)
    _box(cv, 144, 156, 190, h - 40, OAK, 0.52, 0.35, 0.1, 16)
    cv.paint(cv.ell(138, 176, 146, 192), GOLD, cv.dome(141, 183, 5, 7, 0.5, 0.6))
    # a dark inner shadow down both edges of the slot (the carcass depth)
    cv.shade_mul(cv.rect(102, 34, 106, h - 22), 0.5)
    cv.flat(cv.rect(104, 30, 106, h - 18), "#24130e")
    # things on top: a suitcase and a stack of hat boxes
    return cv, slot


def wardrobe_light(slot) -> Cv:
    """The light pouring out of the wardrobe (emissive): an iridescent gradient with a few hanging coats in silhouette and sparkles."""
    x0, y0, x1, y1 = slot
    w, h = x1 - x0, y1 - y0
    cv = Cv(w, h)
    t = (cv.yy / h)[..., None]
    a, b, c = hx("#ff7ad0"), hx("#7af0ff"), hx("#ffe58a")
    f = (np.sin(cv.yy * 0.07 + cv.xx * 0.18) * 0.5 + 0.5)[..., None]
    col = (a * (1 - f) + b * f) * (1 - t * 0.3) + c * np.clip(1 - np.abs(t - 0.45) * 3, 0, 1) * 0.35
    shade = np.clip(0.55 + 0.45 * (1 - np.abs(cv.xx - w / 2) / (w / 2)), 0, 1)[..., None]
    out = np.clip(col * (0.7 + 0.3 * shade), 0, 255)
    d = px.BAYER8[(np.arange(h)[:, None] % 8), (np.arange(w)[None, :] % 8)][..., None] * 22
    cv.a[..., :3] = np.clip(np.round((out + d) / 24) * 24, 0, 255).astype(np.uint8)
    cv.a[..., 3] = 255
    rng = np.random.RandomState(14)
    for _ in range(12):
        x, y = rng.randint(1, w - 2), rng.randint(6, h - 4)
        cv.dots([(x, y), (x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)], "#ffffff")
    # a coat hanger and a hint of sequin sleeves
    cv.flat(cv.line((w // 2 - 8, 6), (w // 2 + 8, 14), 1), "#6a2a7a")
    cv.flat(cv.rect(w // 2 - 2, 20, w // 2 + 4, 120), "#b84ac0")
    return cv


def shelf() -> Cv:
    w, h = 160, 44
    cv = Cv(w, h)
    _box(cv, 0, h - 8, w, h, WOOD, 0.7, 0.3, 0.1, 21)
    cv.paint(cv.rect(2, h - 14, w - 2, h - 8), WOOD, cv.lit((2, h - 14, w - 2, h - 8), 0.82, 0.2, 0.05), edge=False)
    # books leaning on the right
    bx = 100
    for i, (bw, bh, pal) in enumerate([(10, 34, TEAL), (8, 30, RUST), (12, 36, INDIGO), (9, 28, MUSTARD), (11, 32, GREEN), (8, 26, PINK)]):
        _box(cv, bx, h - 8 - bh, bx + bw, h - 8, pal, 0.55, 0.35, 0.1, 22 + i)
        cv.flat(cv.rect(bx + 1, h - 8 - bh + 4, bx + bw - 1, h - 8 - bh + 6), "#e8d4a8")
        bx += bw
    # a small potted cactus and a snow globe on the left
    cv.paint(cv.rect(8, h - 8 - 14, 22, h - 8), RUST, cv.round_x(8, 22, 0.55, 0.4))
    cv.paint(cv.rect(12, h - 8 - 32, 18, h - 8 - 14), GREEN, cv.round_x(12, 18, 0.55, 0.5))
    cv.paint(cv.rect(6, h - 8 - 26, 12, h - 8 - 20), GREEN, cv.round_x(6, 12, 0.55, 0.5))
    return cv


def fairy_lights(w=608, h=72) -> Cv:
    """A string of fairy lights swagged along the wall (emissive): wire, bulbs in six colours, a soft sparkle."""
    cv = Cv(w, h)
    cols = ["#ff6ad0", "#6af0ff", "#ffe070", "#8aff7a", "#ff9a5a", "#b48aff"]
    pts = []
    swags = 9
    for i in range(swags * 20 + 1):
        x = i * (w - 1) / (swags * 20)
        k = (x / (w - 1) * swags) % 1.0
        y = 10 + 26 * math.sin(k * math.pi)
        pts.append((x, y))
    cv.flat(cv.lines(pts, 2), "#2b2230")
    for i in range(swags * 3 + 1):
        j = int(i * (len(pts) - 1) / (swags * 3))
        x, y = pts[j]
        c = cols[i % len(cols)]
        cv.flat(cv.rect(int(x) - 1, int(y) + 1, int(x) + 2, int(y) + 5), "#2b2230")
        b = cv.ell(int(x) - 4, int(y) + 4, int(x) + 5, int(y) + 16)
        cv.flat(b, c, edge=True)
        cv.flat(cv.ell(int(x) - 2, int(y) + 6, int(x) + 1, int(y) + 9), "#ffffff")
        # glow ring, dithered
        for r in (6, 8):
            ring = cv.ell(int(x) - r, int(y) + 10 - r, int(x) + r + 1, int(y) + 10 + r + 1) & ~cv.ell(int(x) - r + 2, int(y) + 10 - r + 2, int(x) + r - 1, int(y) + 10 + r - 1)
            dm = ((cv.xx + cv.yy) % 2 == 0)
            m = ring & dm & (cv.a[..., 3] == 0)
            cv.flat(m, c)
    return cv


def clothes_rail(w=176, h=288) -> Cv:
    """A clothes rail against the wall: A-frame legs, a top bar, a crowd of hangers: jackets, a sequinned top, a hoodie, shirts; trainers underneath."""
    cv = Cv(w, h)
    bar_y = 40
    cv.paint(cv.rect(6, bar_y, w - 6, bar_y + 4), STEEL, cv.lit((6, bar_y, w - 6, bar_y + 4), 0.72, 0.4))
    for lx in (10, w - 14):
        cv.paint(cv.rect(lx, bar_y, lx + 5, h - 6), STEEL, cv.round_x(lx, lx + 5, 0.55, 0.5))
        cv.paint(cv.rect(lx - 8, h - 10, lx + 14, h - 4), STEEL, cv.lit((lx - 8, h - 10, lx + 14, h - 4), 0.5, 0.3))
    garments = [
        (18, 46, 22, 150, INDIGO), (36, 46, 24, 130, RUST), (56, 46, 22, 166, GREEN), (74, 46, 26, 120, PINK), (96, 46, 22, 158, MUSTARD),
        (116, 46, 24, 140, TEAL), (136, 46, 20, 170, RED),
    ]
    for i, (gx, gy, gw, gh, pal) in enumerate(garments):
        cv.paint(cv.rect(gx + gw // 2 - 1, bar_y - 8, gx + gw // 2 + 1, bar_y + 2), STEEL, edge=False)  # hook
        top = gy
        body = cv.poly([(gx + 3, top), (gx + gw - 3, top), (gx + gw + 3, top + 18), (gx + gw, top + gh), (gx, top + gh), (gx - 3, top + 18)])
        s = cv.lit((gx - 3, top, gx + gw + 3, top + gh), 0.5, 0.4, 0.2, 60 + i) + np.sin(cv.xx * 0.9 + i) * 0.04
        cv.paint(body, pal, s)
        cv.shade_mul(cv.rect(gx + gw // 2, top + 24, gx + gw // 2 + 1, top + gh), 0.7)  # a placket or zip
        if i % 3 == 1:  # a sequinned one
            spk = speckle(h, w, 0.05, 90 + i) & body
            cv.flat(spk, "#fff1a8")
    cv.dots([(150, 150)], "#ffffff")
    # a pair of trainers and a bag under the rail
    for tx in (44, 70):
        cv.paint(cv.rrect(tx, h - 22, tx + 24, h - 8, 5), WHITE, cv.lit((tx, h - 22, tx + 24, h - 8), 0.7, 0.3, 0.1, tx))
        cv.paint(cv.rect(tx + 2, h - 10, tx + 22, h - 6), IRON, edge=False)
    cv.paint(cv.rrect(110, h - 34, 148, h - 8, 5), RUST, cv.lit((110, h - 34, 148, h - 8), 0.55, 0.4, 0.1, 9))
    return cv


def desk_frame(w=240, h=230) -> Cv:
    """A desk against the east wall, seen from the room, with a pair of decks and a mixer on it (the top face is drawn in a squashed perspective), monitor speakers either side.
    The front edge of the top is 0.74 m above the floor (118 px above the bottom)."""
    cv = Cv(w, h)
    top_y0, top_y1 = 70, 112  # the top face (squashed): back edge at 70, front edge at 112 (0.74 m up)
    base = h
    # legs and a pedestal of drawers on the left, a trestle leg on the right
    cv.paint(cv.rect(10, 124, 82, base - 4), WOOD, cv.lit((10, 124, 82, base - 4), 0.56, 0.35, 0.12, 31))
    for k, dy in enumerate((128, 160, 192)):
        cv.paint(cv.rect(14, dy, 78, dy + 28), OAK, cv.lit((14, dy, 78, dy + 28), 0.56, 0.3, 0.1, 32 + dy))
        cv.paint(cv.rect(40, dy + 11, 52, dy + 14), GOLD, cv.lit((40, dy + 11, 52, dy + 14), 0.7, 0.3), edge=False)
    cv.paint(cv.rect(196, 124, 206, base - 4), WOOD, cv.round_x(196, 206, 0.5, 0.4))
    cv.paint(cv.rect(180, 190, 222, 196), WOOD, cv.lit((180, 190, 222, 196), 0.5, 0.3))  # a low shelf on the right with a box on it
    cv.paint(cv.rect(188, 170, 214, 190), CREAM, cv.lit((188, 170, 214, 190), 0.5, 0.3, 0.1, 29))
    cv.paint(cv.rect(14, base - 4, 80, base), IRON, edge=False)
    # the desk front (apron) and the top
    cv.paint(cv.rect(4, 112, w - 4, 124), WOOD, cv.lit((4, 112, w - 4, 124), 0.5, 0.35, 0.1, 33))
    top = cv.poly([(14, top_y0), (w - 14, top_y0), (w - 2, top_y1), (2, top_y1)])
    cv.paint(top, OAK, cv.lit((2, top_y0, w - 2, top_y1), 0.78, 0.2, 0.1, 34))
    # monitor speakers, standing at the back of the top
    for sx in (12, 186):
        cv.paint(cv.rect(sx, 38, sx + 42, 84), IRON, cv.lit((sx, 38, sx + 42, 84), 0.5, 0.4, 0.06, 35 + sx))
        cv.paint(cv.ell(sx + 11, 42, sx + 31, 54), STEEL, cv.dome(sx + 19, 48, 10, 6, 0.5, 0.5))
        cv.paint(cv.ell(sx + 7, 56, sx + 35, 82), STEEL, cv.dome(sx + 18, 69, 14, 13, 0.45, 0.6))
        cv.paint(cv.ell(sx + 14, 63, sx + 28, 75), IRON, cv.dome(sx + 19, 69, 7, 6, 0.3, 0.5))
        cv.dots([(sx + 38, 42)], "#ff4040")
    # two turntables (platters seen at a low angle) and a mixer between them
    for px0 in (58, 138):
        deck = cv.poly([(px0 + 4, 74), (px0 + 40, 74), (px0 + 44, 108), (px0, 108)])
        cv.paint(deck, STEEL, cv.lit((px0, 74, px0 + 44, 108), 0.55, 0.4, 0.06, 36 + px0))
        plat = cv.ell(px0 + 3, 79, px0 + 41, 103)
        cv.paint(plat, IRON, cv.dome(px0 + 20, 91, 19, 12, 0.32, 0.4))
        cv.paint(cv.ell(px0 + 14, 86, px0 + 28, 96), RED, cv.dome(px0 + 20, 91, 7, 5, 0.5, 0.5), edge=False)
        cv.flat(cv.ell(px0 + 19, 90, px0 + 22, 93), "#f6f6fa")
        ring = cv.ell(px0 + 6, 82, px0 + 38, 100) & ~cv.ell(px0 + 9, 84, px0 + 35, 98)
        cv.flat(ring & (((cv.xx + cv.yy) % 3) == 0), "#58556a")
        cv.flat(cv.line((px0 + 40, 76), (px0 + 26, 96), 2), "#cfd6e2")  # the tonearm
        cv.flat(cv.rect(px0 + 24, 95, px0 + 29, 99), "#cfd6e2")
        cv.flat(cv.rect(px0 + 37, 80, px0 + 40, 104), "#14121a")  # pitch fader
        cv.flat(cv.rect(px0 + 36, 90, px0 + 41, 93), "#e29360")
    mix = cv.poly([(106, 76), (132, 76), (134, 110), (104, 110)])
    cv.paint(mix, IRON, cv.lit((104, 76, 134, 110), 0.45, 0.4, 0.05, 40))
    for ky, kcol in zip((80, 89, 98), ("#ff6ad0", "#6af0ff", "#ffe070")):
        for kx in (110, 116, 122, 128):
            cv.flat(cv.ell(kx - 2, ky - 2, kx + 2, ky + 2), kcol if kx % 12 == 2 else "#a3a1b5")
    cv.flat(cv.rect(112, 104, 128, 107), "#e8e8f0")
    cv.flat(cv.rect(118, 103, 122, 108), "#14121a")
    cv.paint(cv.rect(96, 62, 106, 78), CREAM, cv.round_x(96, 106, 0.6, 0.5))  # a mug
    cv.flat(cv.line((105, 112), (100, 130), 1), "#14121a")
    return cv


def jungle_poster() -> tuple:
    """A poster of a jungle that is becoming a real opening. Returns (base canvas with a hole, hole box, glow canvas). The leaves spill over the poster's torn border onto the wall."""
    w, h = 244, 200
    cv = Cv(w, h)
    px0, py0, px1, py1 = 29, 18, 215, 181  # the paper
    paper = cv.rect(px0, py0, px1, py1)
    cv.paint(paper, CREAM, cv.lit((px0, py0, px1, py1), 0.7, 0.3, 0.12, 71))
    # a darker green jungle printed on it (a shaded picture) with a white border
    img = cv.rect(px0 + 8, py0 + 8, px1 - 8, py1 - 8)
    t = (cv.yy - py0) / (py1 - py0)
    shd = 0.3 + 0.25 * (fnoise(h, w, 18, 72)) + 0.2 * (1 - t) * 0.0
    cv.paint(img, GREEN, shd, edge=False)
    rng = np.random.RandomState(73)
    # layered fronds: big palm leaves radiating from below
    for layer, (pal, n_, sz, base) in enumerate([(GREEN, 16, 45, 0.28), (GREEN, 12, 35, 0.5), (TEAL, 10, 27, 0.62)]):
        for i in range(n_):
            cx = rng.randint(px0 + 10, px1 - 10)
            cy = rng.randint(py0 + 30, py1 - 8)
            ang = rng.uniform(-2.4, -0.7)
            ln = sz * rng.uniform(0.7, 1.2)
            ex, ey = cx + math.cos(ang) * ln, cy + math.sin(ang) * ln
            mx, my = (cx + ex) / 2, (cy + ey) / 2
            nx, ny = -math.sin(ang), math.cos(ang)
            wd = ln * 0.22
            leaf = cv.poly([(cx, cy), (mx + nx * wd, my + ny * wd), (ex, ey), (mx - nx * wd, my - ny * wd)]) & img
            cv.paint(leaf, pal, cv.lit((cx - ln, cy - ln, cx + ln, cy + ln), base, 0.4, 0.15, 80 + i + layer * 7))
            cv.shade_mul(cv.line((int(cx), int(cy)), (int(ex), int(ey)), 1) & img, 1.25)
    # the opening: the centre of the picture is not a picture any more (hole; the glow decal sits behind)
    ox0, oy0, ox1, oy1 = 79, 56, 165, 150
    hole = cv.ell(ox0, oy0, ox1, oy1)
    cv.erase(hole)
    # a torn lip round the hole: paper edge curled, lit
    lip = cv.ell(ox0 - 5, oy0 - 5, ox1 + 5, oy1 + 5) & ~hole
    cv.paint(lip, CREAM, cv.lit((ox0, oy0, ox1, oy1), 0.8, 0.4, 0.15, 74), edge=True)
    # curled paper corners, bottom left and top right
    cv.paint(cv.poly([(px0 - 2, py1 - 24), (px0 + 22, py1 + 2), (px0 - 2, py1 + 2)]), CREAM, cv.lit((px0, py1 - 24, px0 + 22, py1 + 2), 0.9, 0.3))
    cv.paint(cv.poly([(px1 - 26, py0 - 2), (px1 + 2, py0 - 2), (px1 + 2, py0 + 24)]), CREAM, cv.lit((px1 - 26, py0, px1 + 2, py0 + 24), 0.85, 0.3))
    # leaves breaking out over the paper's border and onto the wall: left, right and top, drawn over the paper edge and beyond it
    for side, spots in {"l": [(px0 + 4, 48, 3.6), (px0 + 4, 96, 3.0), (px0 + 8, 140, 3.9)], "r": [(px1 - 4, 72, -0.45), (px1 - 6, 120, 0.3), (px1 - 4, 158, 0.6)], "t": [(96, py0 + 4, -1.9), (152, py0 + 6, -1.2)]}.items():
        for k, (cx, cy, ang) in enumerate(spots):
            ln = 38 + 6 * k
            ex, ey = cx + math.cos(ang) * ln, cy + math.sin(ang) * ln
            mx, my = (cx + ex) / 2, (cy + ey) / 2
            nx, ny = -math.sin(ang), math.cos(ang)
            wd = ln * 0.2
            leaf = cv.poly([(cx, cy), (mx + nx * wd, my + ny * wd), (ex, ey), (mx - nx * wd, my - ny * wd)])
            cv.paint(leaf, GREEN, cv.lit((cx - ln, cy - ln, cx + ln, cy + ln), 0.62, 0.4, 0.15, 95 + k))
            cv.flat(cv.line((int(cx), int(cy)), (int(ex), int(ey)), 1), "#8cd470")
    # a drawing pin at each top corner
    for (ax, ay) in ((px0 + 6, py0 + 6), (px1 - 8, py0 + 6)):
        cv.paint(cv.ell(ax - 3, ay - 3, ax + 4, ay + 4), RED, cv.dome(ax, ay, 3, 3, 0.5, 0.6))
    # the glow behind the hole (emissive): sunlight through a canopy, mist, a far green distance
    gw, gh = ox1 - ox0, oy1 - oy0
    gl = Cv(gw, gh)
    t2 = gl.yy / gh
    sh = 0.78 - 0.45 * np.abs(gl.xx / gw - 0.5) * 2 * 0.7 + 0.1 * (1 - t2) + (fnoise(gh, gw, 12, 75) - 0.5) * 0.25
    g = px.quantise(np.clip(sh, 0, 1), ramp("#0f3a1a", "#1f6129", "#4a9a3a", "#8cd470", "#c8f090", "#f6ffd0"), 1.0)
    gl.a[..., :3] = g
    gl.a[..., 3] = 255
    for _ in range(9):  # light shafts
        x = rng.randint(4, gw - 4)
        gl.flat(gl.poly([(x, 0), (x + 4, 0), (x + 16, gh), (x + 8, gh)]) & (((gl.xx + gl.yy) % 2) == 0), "#f6ffd0")
    # silhouette of a huge fern and a far tall tree, and a dark shape: something big breathing among the leaves
    gl.flat(gl.ell(int(gw * 0.1), int(gh * 0.62), int(gw * 0.55), int(gh * 0.98)), "#14502a")
    gl.flat(gl.rect(int(gw * 0.72), int(gh * 0.2), int(gw * 0.78), gh), "#14502a")
    gl.flat(gl.ell(int(gw * 0.6), int(gh * 0.12), int(gw * 0.95), int(gh * 0.34)), "#14502a")
    gl.flat(gl.ell(int(gw * 0.64), int(gh * 0.34), int(gw * 0.74), int(gh * 0.42)), "#f6ffd0")  # an eye
    gl.flat(gl.ell(int(gw * 0.67), int(gh * 0.36), int(gw * 0.70), int(gh * 0.40)), "#14502a")
    mist = (fnoise(gh, gw, 16, 77) > 0.62) & (((gl.xx + gl.yy) % 2) == 0)
    gl.flat(mist, "#d8f0b0")
    return cv, (ox0, oy0, ox1, oy1), gl


def door_frame() -> tuple:
    """The west door: architrave, a four-panel door in cream paint, brass knob and a letterbox slot; the gap under it is transparent (the street light decal shows through). Returns (canvas, gap box)."""
    w, h = 176, 336
    cv = Cv(w, h)
    # architrave
    _box(cv, 0, 0, w, h, CREAM, 0.62, 0.3, 0.12, 111)
    leaf = (12, 12, w - 12, h - 8)
    cv.erase(cv.rect(*leaf))
    # the leaf, slightly proud of the frame
    _box(cv, 14, 14, w - 14, h - 14, CREAM, 0.7, 0.3, 0.1, 112)
    for (a, b, c, d) in [(30, 30, w - 30, 140), (30, 152, w - 30, 306)]:
        cv.paint(cv.rect(a, b, c, d), CREAM, cv.lit((a, b, c, d), 0.58, 0.4, 0.08, 113 + b))
        cv.shade_mul(cv.rect(a + 3, b + 3, c - 3, d - 3), 1.1)
    cv.paint(cv.ell(w - 44, 150, w - 32, 164), GOLD, cv.dome(w - 38, 156, 6, 7, 0.55, 0.6))  # knob
    cv.paint(cv.rect(w - 48, 168, w - 28, 174), GOLD, cv.lit((w - 48, 168, w - 28, 174), 0.6, 0.3))  # key plate
    cv.paint(cv.rect(w - 112, 60, w - 52, 70), GOLD, cv.lit((w - 112, 60, w - 52, 70), 0.6, 0.3))  # letterbox
    # chipped paint
    chips = (fnoise(h, w, 4, 115) > 0.85) & cv.rect(14, 14, w - 14, h - 14)
    cv.flat(chips, "#9a8d7b")
    # the gap under the door (transparent)
    gap = (16, h - 14, w - 16, h - 4)
    cv.erase(cv.rect(*gap))
    return cv, gap


def street_light(box) -> Cv:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    cv = Cv(w, h)
    f = (np.sin(cv.xx * 0.12) * 0.5 + 0.5)[..., None]
    col = hx("#ffb347") * (1 - f) + hx("#fff0b0") * f
    cv.a[..., :3] = col.astype(np.uint8)
    cv.a[..., 3] = 255
    cv.flat(cv.rect(w // 2 - 20, 0, w // 2 + 4, h), "#ff7a2a")  # a bus passing: a red-orange smear
    return cv


def timetable() -> Cv:
    """A bus timetable pinned on the door: a red header with a double-decker, a grid of tiny times; no readable text."""
    w, h = 56, 78
    cv = Cv(w, h)
    cv.paint(cv.rect(0, 0, w, h), CREAM, cv.lit((0, 0, w, h), 0.78, 0.25, 0.08, 120))
    cv.paint(cv.rect(2, 2, w - 2, 20), RED, cv.lit((2, 2, w - 2, 20), 0.55, 0.3), edge=False)
    # a little double-decker in the header
    bus = cv.rect(8, 6, 40, 17)
    cv.flat(bus, "#fff1a8")
    cv.flat(cv.rect(8, 11, 40, 12), "#c02a2a")
    for wx in range(10, 38, 5):
        cv.flat(cv.rect(wx, 7, wx + 3, 10), "#27a0c8")
        cv.flat(cv.rect(wx, 13, wx + 3, 15), "#27a0c8")
    cv.flat(cv.ell(11, 15, 16, 20), "#14121a")
    cv.flat(cv.ell(31, 15, 36, 20), "#14121a")
    cv.flat(cv.rect(44, 6, 52, 17), "#fff1a8")
    rng = np.random.RandomState(121)
    for ry in range(24, h - 4, 5):  # rows of times: dark dashes
        for rx in (6, 20, 34, 46):
            ln = rng.randint(4, 9)
            cv.flat(cv.rect(rx, ry, rx + min(ln, 10), ry + 2), "#3d3631")
        if (ry // 5) % 2 == 0:
            cv.tint(cv.rect(3, ry - 1, w - 3, ry + 3), "#27a0c8", 0.18)
    cv.paint(cv.ell(w // 2 - 3, 1, w // 2 + 3, 7), RED, cv.dome(w // 2, 4, 3, 3, 0.5, 0.6))
    return cv


def mirror(w=88, h=232) -> Cv:
    cv = Cv(w, h)
    _box(cv, 0, 0, w, h, OAK, 0.6, 0.3, 0.1, 131)
    glass = cv.rect(8, 8, w - 8, h - 8)
    t = cv.yy / h
    # a blurred reflection of the room: warm lamp glow at the top, the rug below, a dark wardrobe edge
    sh = 0.55 - 0.2 * t + 0.25 * glow_disc(h, w, w * 0.3, h * 0.22, 52, 1.6) + (fnoise(h, w, 20, 132) - 0.5) * 0.14
    cv.paint(glass, ramp("#1c1626", "#2e2540", "#4a3d5e", "#6e5f7c", "#9a8aa0", "#c8b8c4"), sh, edge=False)
    cv.flat(glass & (cv.yy > h * 0.7) & (cv.yy < h * 0.92) & (((cv.xx + cv.yy) % 2) == 0), "#7c2b26")
    cv.flat(cv.rect(10, 10, 22, h - 10) & (((cv.xx + cv.yy) % 2) == 0) & glass, "#3c3949")
    # a diagonal glint and a smudge
    gl = cv.poly([(16, 10), (30, 10), (14, 84), (8, 84)]) & glass
    cv.flat(gl & (((cv.xx + cv.yy) % 2) == 0), "#f0eaf0")
    cv.flat(cv.poly([(34, 12), (38, 12), (30, 50), (26, 50)]) & glass, "#d8cce0")
    # inner edge shade
    cv.shade_mul(cv.rect(8, 8, w - 8, 12), 0.7)
    cv.shade_mul(cv.rect(8, 8, 12, h - 8), 0.8)
    return cv


def hooks(w=88, h=96) -> Cv:
    """A coat-hook board with a denim jacket and a canvas bag; the bag has a cassette-sized badge."""
    cv = Cv(w, h)
    _box(cv, 0, 4, w, 18, OAK, 0.6, 0.3, 0.1, 141)
    for hx_ in (14, 44, 74):
        cv.paint(cv.ell(hx_ - 3, 14, hx_ + 4, 22), IRON, cv.dome(hx_, 18, 3, 3, 0.5, 0.5))
    jacket = cv.poly([(8, 20), (26, 20), (30, 28), (30, 82), (6, 82), (4, 28)])
    cv.paint(jacket, INDIGO, cv.lit((4, 20, 30, 82), 0.5, 0.4, 0.2, 142))
    cv.flat(cv.rect(16, 28, 17, 82), "#17163f")
    cv.flat(cv.rect(8, 40, 14, 45), "#2a2870")
    bag = cv.rrect(38, 30, 70, 78, 5)
    cv.paint(bag, CREAM, cv.lit((38, 30, 70, 78), 0.6, 0.35, 0.12, 143))
    cv.flat(cv.line((44, 24), (54, 34), 2) | cv.line((64, 24), (54, 34), 2), "#c76a40")
    cv.paint(cv.ell(48, 50, 62, 64), PINK, cv.dome(55, 57, 7, 7, 0.5, 0.6), edge=False)
    return cv


def poster(kind: int, w=80, h=112) -> Cv:
    """Gig posters and prints, no text: geometric bands, a sunburst, a face in halftone, a night skyline."""
    cv = Cv(w, h)
    paper = cv.rect(0, 0, w, h)
    cv.paint(paper, CREAM, cv.lit((0, 0, w, h), 0.7, 0.3, 0.08, 150 + kind))
    ix0, iy0, ix1, iy1 = 5, 5, w - 5, h - 18
    img = cv.rect(ix0, iy0, ix1, iy1)
    if kind == 0:  # sunburst over a city, magenta and gold
        cv.paint(img, PINK, cv.lit((ix0, iy0, ix1, iy1), 0.5, 0.4), edge=False)
        cx, cy = w // 2, int(iy1 - 22)
        for i in range(14):
            a0 = math.pi + i * math.pi / 14
            a1 = a0 + math.pi / 28
            ray = cv.poly([(cx, cy), (cx + math.cos(a0) * 80, cy + math.sin(a0) * 80), (cx + math.cos(a1) * 80, cy + math.sin(a1) * 80)]) & img
            cv.paint(ray, GOLD, np.full((h, w), 0.55 if i % 2 else 0.7, np.float32), edge=False)
        cv.paint(cv.ell(cx - 15, cy - 15, cx + 15, cy + 15) & img, GOLD, cv.dome(cx, cy, 15, 15, 0.7, 0.4), edge=False)
        cv.flat(cv.rect(ix0, cy + 4, ix1, iy1) , "#17163f")
        for bx in range(ix0 + 2, ix1 - 6, 9):
            cv.flat(cv.rect(bx, cy + 4 + (bx * 7) % 12, bx + 7, iy1), "#0b0b24")
    elif kind == 1:  # halftone face, teal and ink
        cv.paint(img, TEAL, cv.lit((ix0, iy0, ix1, iy1), 0.5, 0.3), edge=False)
        face = cv.ell(18, 18, 62, 78) & img
        cv.paint(face, SKIN, cv.dome(36, 40, 24, 32, 0.55, 0.5), edge=False)
        dots = ((cv.xx % 3 == 0) & (cv.yy % 3 == 0)) & face & (cv.xx > 38)
        cv.flat(dots, "#4a2a22")
        cv.flat(cv.rect(26, 38, 34, 41), "#14121a")
        cv.flat(cv.rect(44, 38, 52, 41), "#14121a")
        cv.flat(cv.rect(32, 58, 48, 61), "#a22e68")
        cv.paint(cv.poly([(8, 8), (72, 8), (72, 26), (50, 18), (30, 20), (8, 28)]) & img, IRON, cv.lit((8, 8, 72, 28), 0.3, 0.2), edge=False)
    elif kind == 2:  # a planet and rings, indigo
        cv.paint(img, INDIGO, cv.lit((ix0, iy0, ix1, iy1), 0.35, 0.3), edge=False)
        cv.flat(speckle(h, w, 0.03, 160) & img, "#ffffff")
        cv.paint(cv.ell(18, 26, 62, 70) & img, RUST, cv.dome(34, 42, 22, 22, 0.55, 0.6), edge=False)
        cv.flat(cv.ell(6, 42, 74, 56) & ~cv.ell(14, 44, 66, 54) & (cv.yy > 48) & img, "#e8c070")
        cv.flat(cv.ell(6, 42, 74, 56) & ~cv.ell(14, 44, 66, 54) & (cv.yy <= 48) & img & (cv.xx < 18), "#e8c070")
    elif kind == 3:  # concentric record, mustard and black
        cv.paint(img, MUSTARD, cv.lit((ix0, iy0, ix1, iy1), 0.55, 0.3), edge=False)
        cx, cy = w // 2, 44
        for r, c in [(32, "#14121a"), (28, "#26232f"), (22, "#14121a"), (16, "#26232f"), (11, "#c02a2a"), (3, "#14121a")]:
            cv.flat(cv.ell(cx - r, cy - r, cx + r, cy + r) & img, c)
        cv.flat(cv.line((18, 24), (34, 14), 1) & img, "#ffffff")
    else:  # a green mountain range under a pink sky
        cv.paint(img, ramp("#a22e68", "#d2528a", "#ee85ae", "#fbbdd2", "#ffd8c0"), (cv.yy - iy0) / (iy1 - iy0), edge=False)
        cv.paint(cv.poly([(ix0, iy1), (ix0, 60), (22, 38), (36, 56), (52, 30), (ix1, 62), (ix1, iy1)]) & img, GREEN, cv.lit((ix0, 30, ix1, iy1), 0.45, 0.5, 0.1, 165), edge=False)
        cv.flat(cv.poly([(52, 30), (47, 40), (52, 38), (57, 41)]) & img, "#f0e6cc")
        cv.paint(cv.ell(54, 12, 70, 28) & img, GOLD, cv.dome(62, 20, 8, 8, 0.8, 0.3), edge=False)
    # a printed strip along the bottom (lines standing in for text)
    cv.flat(cv.rect(8, h - 14, w - 8, h - 11), "#3d3631")
    cv.flat(cv.rect(8, h - 8, w - 26, h - 6), "#6b6057")
    # blu-tack
    for (ax, ay) in ((2, 2), (w - 4, 2), (2, h - 4), (w - 4, h - 4)):
        cv.flat(cv.rect(ax, ay, ax + 3, ay + 3), "#6a6aa0")
    return cv


def bed_side(w=336, h=168) -> Cv:
    """A single bed against the west wall, side on (north is to the right): headboard, mattress with a quilted duvet in a geometric print, two pillows, a toy; the top face squashed."""
    cv = Cv(w, h)
    mt_y0, mt_y1 = 70, 104  # the mattress's top face
    # legs, divan base
    for lx in (14, 70, 266):
        cv.paint(cv.rect(lx, 128, lx + 8, h - 4), WOOD, cv.round_x(lx, lx + 8, 0.45, 0.4))
    cv.paint(cv.rect(8, 112, w - 24, 134), WOOD, cv.lit((8, 112, w - 24, 134), 0.5, 0.35, 0.1, 171))
    # the headboard (right): tall, slatted pine, and the footboard (left): low
    head = cv.rrect(w - 40, 14, w - 6, h - 6, 4)
    cv.paint(head, WOOD, cv.lit((w - 40, 14, w - 6, h - 6), 0.56, 0.4, 0.12, 172))
    for sy in range(30, h - 16, 14):
        cv.shade_mul(cv.rect(w - 38, sy, w - 8, sy + 2), 0.65)
        cv.flat(cv.rect(w - 38, sy - 1, w - 8, sy), "#b98a52")
    foot = cv.rrect(4, 78, 20, h - 6, 3)
    cv.paint(foot, WOOD, cv.lit((4, 78, 20, h - 6), 0.56, 0.4, 0.1, 173))
    # the mattress side and the duvet hanging over it
    cv.paint(cv.rect(20, 96, w - 40, 124), CREAM, cv.lit((20, 96, w - 40, 124), 0.62, 0.3, 0.1, 174))
    # the duvet: teal and mustard geometric print, rumpled
    duv = cv.poly([(22, 72), (w - 110, 66), (w - 110, 120), (24, 122)])
    base_sh = cv.lit((20, 66, w - 110, 124), 0.5, 0.4, 0.2, 175) + np.sin(cv.xx * 0.11 + cv.yy * 0.05) * 0.07
    cv.paint(duv, TEAL, base_sh)
    zig = (((cv.xx // 2 + (cv.yy // 14) * 7) % 28) < 3) & duv
    cv.flat(zig, "#e8b94a")
    tri = (((cv.xx + cv.yy * 2) % 36) < 2) & duv
    cv.flat(tri, "#f0e6cc")
    cv.shade_mul(cv.poly([(24, 112), (w - 110, 108), (w - 110, 121), (24, 123)]), 0.78)
    # the top face of the mattress, under the pillows (squashed): a lighter band
    cv.paint(cv.poly([(26, mt_y0), (w - 100, mt_y0 - 4), (w - 44, mt_y0 + 8), (30, mt_y0 + 12)]), CREAM, cv.lit((26, mt_y0, w - 44, mt_y0 + 12), 0.84, 0.2, 0.08, 176), edge=False)
    # two pillows by the headboard
    for (a, b, c, d, pal, sd) in [(w - 120, 52, w - 62, 92, WHITE, 177), (w - 96, 60, w - 44, 98, PINK, 178)]:
        pl = cv.rrect(a, b, c, d, 12)
        cv.paint(pl, pal, cv.lit((a, b, c, d), 0.66, 0.4, 0.15, sd))
        cv.shade_mul(cv.line((a + 8, b + 14), (c - 8, b + 18), 1) & pl, 0.8)
    # a soft toy dinosaur on the duvet
    cv.paint(cv.ell(120, 56, 156, 84), GREEN, cv.dome(136, 66, 18, 14, 0.55, 0.6))
    cv.paint(cv.ell(150, 46, 170, 64), GREEN, cv.dome(158, 54, 10, 9, 0.55, 0.6))
    cv.paint(cv.poly([(122, 70), (100, 80), (122, 82)]), GREEN, cv.lit((100, 70, 122, 82), 0.5, 0.3))
    cv.flat(cv.rect(163, 51, 165, 53), "#14121a")
    for sx in (128, 138, 146):
        cv.flat(cv.poly([(sx, 56), (sx + 3, 50), (sx + 6, 56)]), "#e8b94a")
    # a hot-water bottle and a paperback on the footboard side, a sock dangling
    cv.paint(cv.rrect(30, 62, 70, 82, 8), RED, cv.lit((30, 62, 70, 82), 0.5, 0.4, 0.1, 179))
    # boxes under the bed
    cv.paint(cv.rect(86, 136, 178, h - 6), CREAM, cv.lit((86, 136, 178, h - 6), 0.45, 0.3, 0.12, 180))
    cv.flat(cv.rect(90, 140, 174, 143), "#6b6057")
    cv.paint(cv.rect(188, 138, 252, h - 6), RUST, cv.lit((188, 138, 252, h - 6), 0.4, 0.3, 0.12, 181))
    return cv


# ================================================================================ things (billboards) =============================================================

def model_rocket(w=36, h=84) -> Cv:
    cv = Cv(w, h)
    cx = w // 2
    body = cv.rect(cx - 6, 24, cx + 7, 66)
    cv.paint(body, WHITE, cv.round_x(cx - 6, cx + 7, 0.62, 0.5))
    cv.paint(cv.poly([(cx - 6, 24), (cx + 7, 24), (cx + 3, 6), (cx, 1), (cx - 3, 6)]), RED, cv.round_x(cx - 6, cx + 7, 0.55, 0.5))
    cv.flat(cv.rect(cx - 6, 38, cx + 7, 42), "#c02a2a")
    cv.paint(cv.ell(cx - 3, 28, cx + 4, 35), TEAL, cv.dome(cx, 31, 3, 3, 0.5, 0.6))
    cv.paint(cv.poly([(cx - 6, 56), (cx - 15, 74), (cx - 6, 68)]), RED, cv.lit((cx - 15, 56, cx - 6, 74), 0.55, 0.4))
    cv.paint(cv.poly([(cx + 7, 56), (cx + 16, 74), (cx + 7, 68)]), RED, cv.lit((cx + 7, 56, cx + 16, 74), 0.35, 0.3))
    cv.paint(cv.poly([(cx - 5, 66), (cx + 6, 66), (cx + 4, 72), (cx - 3, 72)]), IRON, cv.lit((cx - 5, 66, cx + 6, 72), 0.4, 0.3))
    cv.paint(cv.poly([(cx - 3, 72), (cx + 4, 72), (cx, 82)]), GOLD, cv.lit((cx - 3, 72, cx + 4, 82), 0.7, 0.3), edge=False)
    return cv


def star_mobile(w=84, h=124) -> Cv:
    cv = Cv(w, h)
    cx = w // 2
    cv.flat(cv.rect(cx - 1, 0, cx + 1, 14), "#6b6057")
    cv.flat(cv.line((8, 14), (w - 8, 14), 2), "#cfd6e2")
    rng = [(10, 22, 14, GOLD), (cx, 44, 18, STEEL), (w - 12, 30, 12, GOLD), (28, 74, 12, STEEL), (w - 26, 86, 15, GOLD)]
    for (sx, sy, r, pal) in rng:
        cv.flat(cv.line((sx, 14 if sy < 60 else 15), (sx, sy - r), 1), "#9a9aae")
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr))
        cv.paint(cv.poly(pts), pal, cv.dome(sx - r * 0.2, sy - r * 0.2, r, r, 0.65, 0.5))
    cv.flat(cv.line((cx, 14), (cx - 16, 40), 1) | cv.line((cx, 14), (cx + 6, 26), 1), "#9a9aae")
    return cv


def unicorn(w=64, h=84) -> Cv:
    """A china unicorn figurine: white body, iridescent mane and horn."""
    cv = Cv(w, h)
    body = cv.ell(14, 40, 52, 66)
    cv.paint(body, WHITE, cv.dome(28, 50, 24, 14, 0.62, 0.5))
    for lx in (18, 24, 38, 44):
        cv.paint(cv.rect(lx, 58, lx + 5, 80), WHITE, cv.round_x(lx, lx + 5, 0.55, 0.5))
        cv.flat(cv.rect(lx, 76, lx + 5, 80), "#c4b69c")
    neck = cv.poly([(38, 46), (52, 44), (56, 22), (46, 18)])
    cv.paint(neck, WHITE, cv.lit((38, 18, 56, 46), 0.65, 0.4))
    head = cv.ell(46, 14, 62, 28)
    cv.paint(head, WHITE, cv.dome(52, 20, 8, 7, 0.65, 0.4))
    cv.flat(cv.rect(56, 17, 58, 19), "#14121a")
    cv.flat(cv.rect(59, 22, 61, 24), "#f2a0c8")
    cv.paint(cv.poly([(50, 14), (55, 14), (53, 0)]), GOLD, cv.lit((50, 0, 55, 14), 0.8, 0.3), edge=True)
    cv.flat(cv.line((51, 11), (54, 5), 1), "#fff1a8")
    for i, c in enumerate(["#ff6ad0", "#b48aff", "#6af0ff", "#8aff7a"]):  # mane
        cv.flat(cv.line((48, 14 + i * 4), (38 - i * 2, 30 + i * 4), 3), c)
    for i, c in enumerate(["#ff6ad0", "#b48aff", "#6af0ff"]):  # tail
        cv.flat(cv.line((14, 46 + i * 3), (4 + i, 62 + i * 4), 3), c)
    cv.dots([(10, 8), (60, 40), (6, 30), (22, 30), (34, 34)], "#ffffff")
    return cv


def toy_dino(w=56, h=56) -> Cv:
    """A green plastic T. rex, glossy, on the desk."""
    cv = Cv(w, h)
    body = cv.ell(14, 22, 42, 46)
    cv.paint(body, GREEN, cv.dome(26, 32, 14, 12, 0.55, 0.6))
    cv.paint(cv.poly([(16, 30), (2, 44), (16, 44)]), GREEN, cv.lit((2, 30, 16, 44), 0.5, 0.4))
    head = cv.rrect(32, 8, 52, 24, 4)
    cv.paint(head, GREEN, cv.dome(40, 14, 10, 8, 0.6, 0.5))
    cv.flat(cv.rect(46, 20, 52, 22), "#14121a")  # mouth line
    cv.flat(cv.rect(44, 11, 46, 13), "#ffffff")
    cv.flat(cv.rect(44, 12, 45, 13), "#14121a")
    cv.paint(cv.rect(36, 24, 40, 32), GREEN, cv.lit((36, 24, 40, 32), 0.5, 0.3), edge=False)
    cv.paint(cv.rect(20, 42, 26, 54), GREEN, cv.round_x(20, 26, 0.5, 0.4))
    cv.paint(cv.rect(30, 42, 36, 54), GREEN, cv.round_x(30, 36, 0.45, 0.4))
    cv.flat(cv.rect(20, 52, 26, 54), "#e8e8c0")
    cv.flat(cv.rect(30, 52, 36, 54), "#e8e8c0")
    cv.flat(cv.rect(34, 14, 36, 18), "#d8f0b0")  # gloss
    cv.flat(cv.line((18, 28), (24, 26), 1), "#d8f0b0")
    return cv


def headphones(w=48, h=52) -> Cv:
    cv = Cv(w, h)
    band = cv.ell(6, 4, 42, 48) & ~cv.ell(11, 9, 37, 52)
    cv.paint(band, IRON, cv.lit((6, 4, 42, 48), 0.5, 0.5, 0.05, 190))
    for cx in (6, 36):
        cv.paint(cv.rrect(cx - 3, 26, cx + 10, 48, 5), RED, cv.lit((cx - 3, 26, cx + 10, 48), 0.55, 0.45, 0.06, 191 + cx))
        cv.paint(cv.rect(cx, 30, cx + 5, 44), IRON, cv.lit((cx, 30, cx + 5, 44), 0.35, 0.3), edge=False)
    cv.flat(cv.line((8, 50), (14, 51), 1), "#14121a")
    return cv


def fern(w=128, h=140) -> Cv:
    """A big potted fern in a glazed pot, fronds arching out over the rim."""
    cv = Cv(w, h)
    cx = w // 2
    rng = np.random.RandomState(200)
    for i in range(15):
        ang = -math.pi / 2 + (i - 7) * 0.2 + rng.uniform(-0.08, 0.08)
        ln = rng.uniform(55, 100)
        pts = []
        px_, py_ = cx, h - 44
        for k in range(14):
            t = k / 13
            a = ang + t * (0.6 if ang > -math.pi / 2 else -0.6) * 0.7
            px_ += math.cos(a) * ln / 13
            py_ += math.sin(a) * ln / 13
            pts.append((px_, py_))
        cv.flat(cv.lines([(cx, h - 44)] + pts, 1), "#1f6129")
        for k, (x, y) in enumerate(pts[2:], 2):
            sz = 11 * (1 - k / 16) + 2
            a = ang + (k / 13) * (0.6 if ang > -math.pi / 2 else -0.6) * 0.7
            for side in (-1, 1):
                nx, ny = -math.sin(a) * side, math.cos(a) * side
                leaf = cv.poly([(x, y), (x + nx * sz + math.cos(a) * sz * 0.6, y + ny * sz + math.sin(a) * sz * 0.6), (x + math.cos(a) * 3, y + math.sin(a) * 3)])
                cv.paint(leaf, GREEN, cv.lit((x - sz, y - sz, x + sz, y + sz), 0.5 + 0.1 * (k % 2), 0.5, 0.1, 210 + i + k), edge=False)
    # the pot
    pot = cv.poly([(cx - 30, h - 46), (cx + 30, h - 46), (cx + 24, h - 4), (cx - 24, h - 4)])
    cv.paint(pot, TEAL, cv.round_x(cx - 30, cx + 30, 0.5, 0.55))
    cv.paint(cv.rect(cx - 33, h - 52, cx + 33, h - 44), TEAL, cv.lit((cx - 33, h - 52, cx + 33, h - 44), 0.7, 0.3))
    cv.flat(cv.rect(cx - 24, h - 30, cx + 24, h - 28), "#86cdbd")
    cv.flat(cv.rect(cx - 25, h - 20, cx + 25, h - 18), "#86cdbd")
    return cv


def toy_car(w=52, h=28) -> Cv:
    cv = Cv(w, h)
    cv.paint(cv.rrect(2, 12, w - 2, 22, 3), RED, cv.lit((2, 12, w - 2, 22), 0.58, 0.45, 0.06, 220))
    cv.paint(cv.poly([(14, 12), (20, 3), (36, 3), (42, 12)]), RED, cv.lit((14, 3, 42, 12), 0.58, 0.45, 0.06, 221))
    cv.flat(cv.poly([(18, 11), (22, 5), (28, 5), (28, 11)]), "#86cdbd")
    cv.flat(cv.poly([(30, 11), (30, 5), (35, 5), (39, 11)]), "#86cdbd")
    cv.flat(cv.rect(w - 6, 15, w - 2, 18), "#ffe58a")
    cv.flat(cv.rect(2, 15, 5, 18), "#ff4040")
    for wx in (13, 38):
        cv.paint(cv.ell(wx - 6, 16, wx + 6, h - 1), IRON, cv.dome(wx, 22, 6, 6, 0.35, 0.5))
        cv.flat(cv.ell(wx - 2, 20, wx + 2, 24), "#cfd6e2")
    cv.flat(cv.line((8, 14), (22, 14), 1), "#ff9a7a")
    return cv


def indicator_light(w=28, h=28) -> Cv:
    """A little amber indicator lamp on a dark housing (emissive): a car-style turn signal that blinks."""
    cv = Cv(w, h)
    cv.paint(cv.rrect(2, 4, w - 2, h - 4, 4), IRON, cv.lit((2, 4, w - 2, h - 4), 0.4, 0.4, 0.05, 230))
    cv.paint(cv.rrect(5, 7, w - 5, h - 7, 3), ramp("#7a3a08", "#c76a14", "#ffa030", "#ffcf70", "#fff0b8"), cv.dome(w / 2 - 2, h / 2 - 2, 8, 6, 0.75, 0.4), edge=False)
    cv.flat(cv.rect(w // 2 - 4, h // 2 - 2, w // 2 - 2, h // 2 + 1), "#ffffff")
    return cv


def standing_lamp(w=76, h=260) -> Cv:
    """A standing lamp with a warm pleated shade (emissive)."""
    cv = Cv(w, h)
    cx = w // 2
    cv.paint(cv.rect(cx - 2, 70, cx + 3, h - 12), STEEL, cv.round_x(cx - 2, cx + 3, 0.5, 0.5))
    cv.paint(cv.ell(cx - 20, h - 14, cx + 20, h - 2), IRON, cv.dome(cx, h - 8, 20, 6, 0.4, 0.4))
    shade = cv.poly([(cx - 20, 8), (cx + 20, 8), (cx + 32, 66), (cx - 32, 66)])
    pleat = np.sin((cv.xx - cx) * 0.9) * 0.1
    cv.paint(shade, ramp("#9a4a14", "#c8742a", "#e8a04a", "#f6c872", "#ffe0a0", "#fff4d0"), 0.72 + pleat - 0.28 * (np.abs(cv.xx - cx) / 32) + 0.1 * (1 - cv.yy / 66))
    cv.flat(cv.rect(cx - 20, 8, cx + 21, 10), "#fff4d0")
    cv.flat(cv.rect(cx - 32, 64, cx + 33, 66), "#e8a04a")
    return cv


def glow_soft(w=96, h=160, col="#ff7ad0") -> Cv:
    """A soft additive glow (the one soft-edged thing allowed): a vertical bloom for the wardrobe light and the like."""
    cv = Cv(w, h)
    d = glow_disc(h, w, w / 2, h / 2, max(w, h) / 2, 1.8) * np.clip(1 - np.abs(cv.xx - w / 2) / (w / 2) * 0.5, 0, 1)
    c = hx(col)
    cv.a[..., :3] = c.astype(np.uint8)
    cv.a[..., 3] = (np.clip(d, 0, 1) * 200).astype(np.uint8)
    return cv


# ================================================================================ the build =======================================================================

def build() -> dict:
    """{name: (kind, image (RGB array for tiles / Cv for the rest), metres | None, extra)}. `extra` is a dict of notes for the map builder (the glass box etc.)."""
    out: dict = {}
    for i, c in enumerate("nesw"):
        out["wall_paper_" + c] = ("tile", wall_paper(i), 2.5, {})
    out["ceil_plaster"] = ("tile", ceiling_plaster(), 2.5, {})
    out["floor_room"] = ("tile", tile_floor(), 5.0, {})
    wf, gbox = window_frame()
    out["win_frame"] = ("decal", wf, None, {"glass": gbox})
    out["win_glass"] = ("decal", window_glass(gbox), None, {})
    out["radiator"] = ("decal", radiator(), None, {})
    wd, slot = wardrobe_frame()
    out["wardrobe"] = ("decal", wd, None, {"slot": slot})
    out["wardrobe_light"] = ("decal", wardrobe_light(slot), None, {})
    out["shelf"] = ("decal", shelf(), None, {})
    out["fairy_lights"] = ("decal", fairy_lights(), None, {})
    out["clothes_rail"] = ("decal", clothes_rail(), None, {})
    out["desk"] = ("decal", desk_frame(), None, {})
    jp, jhole, jglow = jungle_poster()
    out["jungle_poster"] = ("decal", jp, None, {"hole": jhole})
    out["jungle_glow"] = ("decal", jglow, None, {})
    df, gap = door_frame()
    out["door"] = ("decal", df, None, {"gap": gap})
    out["door_light"] = ("decal", street_light(gap), None, {})
    out["timetable"] = ("decal", timetable(), None, {})
    out["mirror"] = ("decal", mirror(), None, {})
    out["hooks"] = ("decal", hooks(), None, {})
    for k in range(5):
        out["poster_%d" % k] = ("decal", poster(k), None, {})
    out["bed_side"] = ("decal", bed_side(), None, {})
    out["thing_rocket"] = ("thing", model_rocket(), None, {})
    out["thing_mobile"] = ("thing", star_mobile(), None, {})
    out["thing_unicorn"] = ("thing", unicorn(), None, {})
    out["thing_dino"] = ("thing", toy_dino(), None, {})
    out["thing_headphones"] = ("thing", headphones(), None, {})
    out["thing_fern"] = ("thing", fern(), None, {})
    out["thing_car"] = ("thing", toy_car(), None, {})
    out["thing_indicator"] = ("thing", indicator_light(), None, {})
    out["thing_lamp"] = ("thing", standing_lamp(), None, {})
    out["thing_glow_pink"] = ("thing", glow_soft(112, 200, "#ff7ad0"), None, {})
    out["thing_glow_cyan"] = ("thing", glow_soft(80, 160, "#7af0ff"), None, {})
    out["thing_glow_green"] = ("thing", glow_soft(150, 170, "#9aff70"), None, {})
    return out
