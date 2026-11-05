"""The Mission Count's city world (docs/THREE_PATHS_AND_FACES_PLAN.md 5.3): sepia and noir pixel art, no neon.

Three moods: the town at dusk (old limestone and stucco, brown and amber, soot and smoke), the Colonel's office (polished dark oak, green leather, brass, a burgundy carpet)
and the ruined city by night (blackened brick under a red-orange fire-lit sky, one big train lamp).
`DRAW = {id: fn}`; every fn() takes no arguments and returns a uint8 array (tools/story/art/tex_squadron.py checks the shapes). Deterministic: seeded generators only.
NO text anywhere: the only marks that look like writing are the painted digits of `thing_count_slate`.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from .pixeltex import BAYER8, bricks, grid, grime, hexc, noise, quantise, ramp, speckle
from .tex_underworld import _worley

# ---- palettes (dark to light) -------------------------------------------------------------------------------------------------------------------
LIME = ramp("#1a1410", "#362b20", "#584634", "#7e6748", "#a48b64", "#c8b184")
OCHRE = ramp("#2a1c0e", "#4c3416", "#765526", "#a07c3a", "#c4a258", "#dcc07a")
GREYST = ramp("#1c1914", "#38332a", "#585042", "#7a705c", "#9a8e76", "#b8ac90")
SOOTB = ramp("#040202", "#0e0706", "#1c0f0b", "#2e1913", "#47271b", "#643826")
BRICKW = ramp("#1a0a06", "#3a1a10", "#5e2c1a", "#84402a", "#a85a38", "#c47a50")
MORTAR = ramp("#0a0706", "#1c1410", "#30261c")
COBB = ramp("#140e08", "#2a1f14", "#43321f", "#614a30", "#816444", "#a08460")
PUDDLE = ramp("#1c140e", "#3e3022", "#6a5538", "#a58a58", "#d8b878")
OAK = ramp("#0a0603", "#1a0f07", "#2e1b0c", "#4a2d14", "#6a4420", "#8c5f2e")
LEATHER = ramp("#05100a", "#0c1e14", "#162f20", "#244a32", "#366a48", "#4e8a62")
BRASS = ramp("#2a1a06", "#6a4610", "#a87a1c", "#d8aa38", "#f8e080")
BURG = ramp("#14050a", "#2a0a10", "#461420", "#66222e", "#863a42", "#a85a56")
CREAM = ramp("#2a2218", "#5a4c36", "#8c7a58", "#b8a67c", "#d8caa0", "#efe4c0")
FIRE = ramp("#2a0804", "#6a1608", "#b8380c", "#f07a1a", "#ffc050", "#fff0b0")
SKYA = ramp("#2a1a10", "#4a301c", "#7a5028", "#b07a38", "#d8a050", "#f2c878")
NIGHTR = ramp("#0c0204", "#220609", "#46100d", "#771c0f", "#b4381a", "#e0642a", "#ffa04a")
SKYD = ramp("#2c2624", "#443630", "#5e463a", "#80583c", "#a8743c", "#d09a48", "#ecc070", "#f8dc98")
OLIVE = ramp("#0a0e07", "#161e0e", "#26331a", "#3c5026", "#566c36", "#788a4c")
STEEL = ramp("#0c0b0a", "#1c1a18", "#34302c", "#544e46", "#7c746a", "#aaa090")
CHROME = ramp("#201c18", "#58524a", "#a49c8c", "#e4dcc8", "#fffaf0")
SOOT = ramp("#030202", "#0a0605", "#160e0a", "#241810", "#34241a")
PAPER = ramp("#2c2216", "#5c4a30", "#8c7448", "#b8a068", "#d6c490", "#ece0b4")
CLOTH = ramp("#2a2018", "#4a3a2a", "#6e5a42", "#94805c", "#b8a47c", "#d8c8a0")
WHITE = ramp("#2c2a26", "#5e5a52", "#8e897c", "#bdb7a6", "#e0dac8", "#f6f0e0")
STONEN = ramp("#0a0807", "#1a1512", "#2c241e", "#44382e", "#5e4e40", "#7a6654")


def R(seed: int) -> np.random.RandomState:
    return np.random.RandomState(seed)


def q(shade, pal, d: float = 1.0) -> np.ndarray:
    return quantise(np.clip(shade, 0, 1), pal, d)


def rgbof(h: str) -> np.ndarray:
    return (hexc(h) * 255 + 0.5).astype(np.uint8)


def setc(rgb: np.ndarray, mask, hexs: str) -> np.ndarray:
    rgb[np.asarray(mask) > 0.5] = rgbof(hexs)
    return rgb


def bay(h: int, w: int) -> np.ndarray:
    """The 8x8 ordered-dither threshold 0..1 over an (h, w) field."""
    return BAYER8[np.arange(h)[:, None] % 8, np.arange(w)[None, :] % 8] + 0.5


def pseg(n: int, ax, ay, bx, by, w) -> np.ndarray:
    """A thick segment on a wrapping n x n tile."""
    x, y = grid(n)
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy + 1e-6
    best = np.full((n, n), 1e9, np.float32)
    for ox in (-n, 0, n):
        for oy in (-n, 0, n):
            t = np.clip(((x - ax - ox) * dx + (y - ay - oy) * dy) / L2, 0, 1)
            best = np.minimum(best, np.hypot(x - (ax + ox + t * dx), y - (ay + oy + t * dy)))
    return best <= w * 0.5


def pdist(n: int, c: float, axis: int) -> np.ndarray:
    """Wrapping distance of each row (axis 0) or column (axis 1) from c."""
    x, y = grid(n)
    v = y if axis == 0 else x
    d = np.abs(v - c)
    return np.minimum(d, n - d)


def edge_of(mask: np.ndarray) -> np.ndarray:
    """The one-pixel inner border of a mask (wrapping)."""
    m = mask.astype(bool)
    return m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))


def sel(mask, a, b):
    return np.where(np.asarray(mask)[..., None], a, b)


def dark(rgb, f=0.5):
    return (rgb.astype(np.float32) * f).astype(np.uint8)


def wnoise(w: int, h: int, scale: float, seed: int, octaves: int = 3) -> np.ndarray:
    """Noise of shape (h, w) cut from the tileable n x n field with n = w (w >= h): periodic along x."""
    return noise(w, scale, seed, octaves)[:h, :w]


# ======================================================================================================================================================
# surfaces
# ======================================================================================================================================================

def wall_stucco():
    n = 64
    r = R(6001)
    x, y = grid(n)
    sh = 0.5 + (noise(n, 6, 6002, 3) - 0.5) * 0.38 + (noise(n, 2.5, 6003, 2) - 0.5) * 0.14
    sh = sh - 0.18 * grime(n, 6004, 0.9)
    rgb = sel(noise(n, 18, 6005, 2) > 0.52, q(sh, GREYST), q(sh, OCHRE))
    # a painted facade: two faded shutters round a dark painted window
    sp = ramp("#1a1e18", "#2c3428", "#424c3a", "#5e6a50", "#76846a")
    for x0 in (3, 43):
        m = (x >= x0) & (x < x0 + 18) & (y >= 6) & (y < 54)
        slat = (y - 6) % 4
        shl = 0.5 + 0.18 * (slat == 0) - 0.22 * (slat == 3) + (noise(n, 3, 6007) - 0.5) * 0.3
        rgb = sel(m, q(shl, sp), rgb)
        rgb = sel(m & ((x == x0) | (x == x0 + 17) | (y == 6) | (y == 53)), q(np.full((n, n), 0.1), sp), rgb)
    win = (x >= 25) & (x < 39) & (y >= 9) & (y < 51)
    glass = q(0.2 + 0.2 * (1 - (y - 9) / 42) + (noise(n, 4, 6008) - 0.5) * 0.2, ramp("#0a0806", "#1c1610", "#34281c", "#54402a"))
    rgb = sel(win, glass, rgb)
    bar = win & (((y - 9) % 14 == 7) | (x == 31) | (x == 32))
    rgb = sel(bar, q(np.full((n, n), 0.5), STEEL), rgb)
    sill = (x >= 23) & (x < 41) & (y >= 51) & (y < 54)
    rgb = sel(sill, q(0.55 + (noise(n, 3, 6009) - 0.5) * 0.2, LIME), rgb)
    rgb = sel(win & ((x == 25) | (y == 9)), dark(rgb, 0.6), rgb)
    # stains running down
    g = grime(n, 6010, 0.85)
    rgb = sel(g > 0.55, dark(rgb, 0.62), rgb)
    # bare brick where the render has fallen
    pm = (noise(n, 14, 6011, 3) > 0.68) & ~win
    bsh, bm = bricks(n, rows=10, cols=4, mortar=1, seed=6012, wear=0.3)
    brick = sel(bm > 0.5, q(np.full((n, n), 0.4), MORTAR), q(bsh * 0.85, BRICKW))
    rgb = sel(pm, brick, rgb)
    rgb = sel(edge_of(pm), dark(rgb, 0.5), rgb)
    # cracks: random walks that wrap
    for k in range(4):
        cx, cy = r.uniform(0, n), r.uniform(0, n)
        ang = r.uniform(0.6, 2.5)
        for _ in range(r.randint(14, 30)):
            ang += r.uniform(-0.7, 0.7)
            cx += np.cos(ang) * 1.3
            cy += np.sin(ang) * 1.3 + 0.4
            rgb[int(cy) % n, int(cx) % n] = rgbof("#241a12")
    return rgb


def wall_panel():
    n = 64
    x, y = grid(n)
    grain = np.sin(x * 1.1 + noise(n, 9, 6101, 3) * 9.0) * 0.5 + 0.5
    sh = 0.38 + 0.2 * grain + (noise(n, 3, 6102) - 0.5) * 0.15
    sheen = 0.5 + 0.5 * np.cos(2 * np.pi * (x + y * 0.5 - 14) / n)
    sh += 0.18 * np.clip(sheen - 0.45, 0, 1) * 1.8
    # frieze y 0..4, picture rail 5..9, panels 12..51, dado rail 53..57, skirting 58..63
    sh = np.where(y < 5, sh - 0.12, sh)
    rail = (y >= 5) & (y < 10)
    sh = np.where(rail, sh + 0.12 - 0.22 * (y >= 9) + 0.12 * (y == 5), sh)
    sh = np.where(y >= 58, sh - 0.05 + 0.15 * (y == 58), sh)
    sh = np.where((y >= 53) & (y < 58), sh + 0.1 * (y == 53) - 0.2 * (y == 57), sh)
    sh = np.where(y >= 60, sh - 0.1, sh)
    for x0 in (3, 35):
        px0, px1, py0, py1 = x0, x0 + 26, 12, 51
        inside = (x >= px0) & (x < px1) & (y >= py0) & (y < py1)
        field = (x >= px0 + 4) & (x < px1 - 4) & (y >= py0 + 4) & (y < py1 - 4)
        sh = np.where(inside, sh + 0.06 + 0.2 * ((x < px0 + 2) | (y < py0 + 2)) - 0.22 * ((x >= px1 - 2) | (y >= py1 - 2)), sh)
        sh = np.where(field, sh - 0.17 + 0.2 * ((x < px0 + 5) | (y < py0 + 5)) - 0.1 * ((x >= px1 - 5) | (y >= py1 - 5)), sh)
    rgb = q(sh, OAK)
    # the gold trim: a brass line along the rail and a thin one in each panel moulding
    rgb = sel((y == 6) | (y == 8), q(np.full((n, n), 0.12), OAK), rgb)
    rgb = sel((y == 7) | ((y == 5) & (x % 2 == 0)), q(0.55 + 0.4 * sheen, BRASS), rgb)
    for x0 in (3, 35):
        mold = (x >= x0 + 3) & (x < x0 + 23) & (y >= 15) & (y < 48) & ((x == x0 + 3) | (x == x0 + 22) | (y == 15) | (y == 47))
        rgb = sel(mold, q(0.28 + 0.25 * sheen, BRASS), rgb)
    return rgb


def wall_ruin():
    n = 64
    x, y = grid(n)
    bsh, bm = bricks(n, rows=10, cols=4, mortar=1, seed=6201, wear=0.7)
    sh = bsh * 0.85 - 0.1 * grime(n, 6202, 1.0)
    rgb = sel(bm > 0.5, q(0.2 + (noise(n, 3, 6203) - 0.5) * 0.4, MORTAR), q(sh, SOOTB))
    # the burst hole: bricks gone, bare lath boards across it, shadow behind
    hole = (noise(n, 24, 6204, 3) > 0.60) & (pdist(n, 20, 0) < 20)
    lath_y = y % 5
    lath = hole & (lath_y < 3)
    gap = hole & ~lath
    rgb = sel(gap, q(0.05 + (noise(n, 3, 6205) - 0.5) * 0.12, SOOT), rgb)
    lsh = 0.4 + 0.25 * (lath_y == 0) - 0.2 * (lath_y == 2) + (noise(n, 2, 6206) - 0.5) * 0.35
    rgb = sel(lath, q(lsh, ramp("#080403", "#1a0e08", "#35200f", "#5a3818")), rgb)
    lip = (noise(n, 24, 6204, 3) > 0.54) & ~hole & (pdist(n, 20, 0) < 22) & (noise(n, 3, 6207) > 0.45)
    rgb = sel(lip, q(0.2 + 0.4 * noise(n, 2.5, 6208), ramp("#120f0c", "#2c2620", "#4a4034", "#6c5e4c")), rgb)
    rgb = sel(edge_of(hole), dark(rgb, 0.45), rgb)
    # rubble at the foot
    foot = pdist(n, 60, 0) < 5 + (noise(n, 6, 6209, 2) - 0.5) * 12
    f1, f2, ids = _worley(n, 9, 6210)
    tone = R(6211).rand(81)[ids]
    chunk = q(0.15 + 0.5 * tone + 0.2 * np.clip((f2 - f1) / 4, 0, 1) * (f1 < 7), ramp("#080404", "#1c0e0a", "#341d14", "#523022", "#6e4a38", "#8a7664"))
    chunk = sel((f2 - f1) < 1.1, q(np.full((n, n), 0.06), SOOT), chunk)
    rgb = sel(foot, chunk, rgb)
    rgb = setc(rgb, speckle(n, 0.006, 6212) * (grime(n, 6213, 0.6) > 0.2), "#c8561a")
    shadow = 0.7 + 0.3 * np.sin(np.pi * (y + 0.5) / n)
    return (rgb * (0.72 + 0.28 * shadow[..., None])).astype(np.uint8)


def floor_cobble():
    n = 64
    f1, f2, ids = _worley(n, 6, 6301)
    tone = R(6302).rand(36)[ids]
    edge = f2 - f1
    dome = np.clip(edge / 5.0, 0, 1)
    sh = 0.28 + 0.34 * tone + 0.3 * dome ** 0.7 + (noise(n, 4, 6303) - 0.5) * 0.2
    rut = np.maximum(np.exp(-(pdist(n, 16, 0) / 3.4) ** 2), np.exp(-(pdist(n, 46, 0) / 3.4) ** 2))
    sh = sh * (1 - 0.55 * rut) + 0.30 * 0.55 * rut
    rgb = q(sh, COBB)
    gap = (edge < 1.6) & (rut < 0.5)
    rgb = sel(gap, q(0.04 + 0.1 * noise(n, 3, 6304), COBB), rgb)
    # puddles lie in the ruts: flat, with a streak of amber sky in them
    x, y = grid(n)
    pm = ((noise(n, 12, 6305, 3) > 0.55) & (rut > 0.22)) | ((((x - 24) / 11) ** 2 + ((y - 16) / 3.2) ** 2) < 1) | ((((x - 50) / 9) ** 2 + ((y - 47) / 3) ** 2) < 1)
    psh = 0.34 + 0.25 * (np.sin((x + noise(n, 6, 6306) * 8) * 0.5) * 0.5 + 0.5) * (1 - (y % 4) / 4) + (noise(n, 5, 6307) - 0.5) * 0.15
    rgb = sel(pm, q(psh, PUDDLE), rgb)
    rgb = sel(edge_of(pm), dark(rgb, 0.7), rgb)
    # straw and paper
    r = R(6308)
    for k in range(15):
        px, py = r.uniform(0, n), r.uniform(0, n)
        a = r.uniform(0, np.pi)
        col = rgbof(["#b89a50", "#8a7038", "#d0b468"][k % 3])
        for t in range(r.randint(4, 9)):
            rgb[int(py + np.sin(a) * t) % n, int(px + np.cos(a) * t) % n] = col
    for k in range(5):
        px, py = int(r.uniform(0, n)), int(r.uniform(0, n))
        for dy in range(2):
            for dx in range(3 + k % 2):
                rgb[(py + dy) % n, (px + dx) % n] = rgbof("#d8cba8" if dy == 0 else "#a89a78")
        rgb[(py + 2) % n, (px + 1) % n] = rgbof("#241a10")
    return rgb


def floor_rubble():
    n = 64
    f1, f2, ids = _worley(n, 4, 6401)
    tone = R(6402).rand(16)[ids]
    edge = f2 - f1
    sh = 0.3 + 0.28 * tone + 0.2 * np.clip(edge / 6, 0, 1) + (noise(n, 3, 6403) - 0.5) * 0.25
    rgb = q(sh, ramp("#100d0b", "#24201c", "#3e3730", "#5a5046", "#7a6e60", "#9a8c7a"))
    rgb = sel(edge < 1.3, q(np.full((n, n), 0.04), SOOT), rgb)
    # small broken chunks piled in drifts
    g1, g2, gi = _worley(n, 12, 6404)
    gt = R(6405).rand(144)[gi]
    drift = noise(n, 16, 6406, 3) > 0.5
    ch = q(0.15 + 0.6 * gt + 0.15 * np.clip((g2 - g1) / 3, 0, 1), ramp("#0c0706", "#241410", "#46261a", "#6e3c28", "#8c5238", "#a8806a"))
    ch = sel((g2 - g1) < 1.0, q(np.full((n, n), 0.05), SOOT), ch)
    ch = sel(gt > 0.78, q(0.4 + 0.4 * gt, ramp("#4a4238", "#7a6e5c", "#a39a82", "#c8bea0")), ch)
    rgb = sel(drift, ch, rgb)
    # brick dust drifting over it
    dust = np.clip((noise(n, 8, 6407, 3) - 0.55) * 5, 0, 1) > bay(n, n) * 0.9
    rgb = sel(dust, (rgb.astype(np.float32) * 0.65 + np.array([150, 80, 50], np.float32) * 0.35).astype(np.uint8), rgb)
    # charred planks lying across it
    xx, yy = grid(n)
    for (ax, ay, bx, by) in ((6, 12, 40, 22), (30, 52, 62, 44), (14, 34, 26, 62)):
        m = pseg(n, ax, ay, bx, by, 4.5)
        grain = np.sin((xx * 0.8 + yy * 0.5) + noise(n, 5, 6409) * 6) * 0.5 + 0.5
        ps = 0.15 + 0.22 * grain + (noise(n, 2, 6410) - 0.5) * 0.3
        rgb = sel(m, q(ps, ramp("#050302", "#120a06", "#241408", "#3c2410")), rgb)
        rgb = sel(edge_of(m), q(np.full((n, n), 0.02), SOOT), rgb)
        rgb = setc(rgb, m & (noise(n, 3, 6411) > 0.8) & (grain > 0.5), "#b4481a")
    # glass glints
    r = R(6412)
    for k in range(9):
        px, py = int(r.uniform(0, n)), int(r.uniform(0, n))
        rgb[py % n, px % n] = rgbof("#e8f2f0")
        rgb[py % n, (px + 1) % n] = rgbof("#7c9096")
        rgb[(py + 1) % n, px % n] = rgbof("#566a70")
    return rgb


def floor_carpet():
    n = 64
    x, y = grid(n)
    xi, yi = x.astype(int), y.astype(int)
    ed = np.minimum(np.minimum(x, y), np.minimum(n - 1 - x, n - 1 - y))
    weave = ((x + y) % 2) * 0.05 + ((xi // 2 + yi // 2) % 2) * 0.03
    wear = np.clip((noise(n, 10, 6501, 3) - 0.5) * 2.2, 0, 1)
    sh = 0.36 + weave + (noise(n, 3, 6502) - 0.5) * 0.12 + 0.12 * wear
    u, v = x % 16, y % 16
    dia = np.abs(u - 8) + np.abs(v - 8)
    sh = np.where((dia == 6) | (dia == 7), sh + 0.13, sh)
    sh = np.where(dia < 2, sh + 0.09, sh)
    rgb = q(sh, BURG)
    # worn patches go brown and thin
    rgb = sel((wear > 0.55) & (bay(n, n) > 0.25), q(0.42 + weave * 2 + (noise(n, 2, 6503) - 0.5) * 0.2, ramp("#2a1a12", "#4a3020", "#6c4a32", "#8c6848")), rgb)
    # the pale border pattern: dark edge, cream line, a key pattern, cream line
    cream = q(0.6 + weave * 2 + (noise(n, 2, 6504) - 0.5) * 0.25, CREAM)
    drk = q(0.12 + weave, BURG)
    key = ((xi // 3) + (yi // 3)) % 2 == 0
    rgb = sel(ed <= 1, drk, rgb)
    rgb = sel((ed == 2) | (ed == 3), cream, rgb)
    rgb = sel(ed == 4, drk, rgb)
    rgb = sel((ed >= 5) & (ed <= 8), sel(key, cream, q(0.2 + weave, BURG)), rgb)
    rgb = sel(ed == 9, drk, rgb)
    rgb = sel(ed == 10, cream, rgb)
    rgb = sel(ed == 11, q(0.25 + weave, BURG), rgb)
    st = (((x - 40) / 7) ** 2 + ((y - 36) / 5) ** 2) < 1
    rgb = sel(st & (bay(n, n) > 0.5), dark(rgb, 0.6), rgb)
    return rgb


# ======================================================================================================================================================
# ceilings and sky
# ======================================================================================================================================================

def ceil_arcade():
    n = 64
    x, y = grid(n)
    band = 0.5 + 0.5 * np.cos(2 * np.pi * (y - 36) / n)
    sh = 0.42 + 0.3 * band + (noise(n, 14, 6601, 3) - 0.5) * 0.28
    rgb = q(sh, SKYA)
    # smoke wisps drifting across
    wsp = np.clip((noise(n, 10, 6602, 3) * 0.6 + np.roll(noise(n, 22, 6603, 2), 9, 1) * 0.5 - 0.45) * 4.5, 0, 1)
    smoke = q(0.3 + 0.35 * wsp * np.sin(np.pi * wsp) + (noise(n, 4, 6604) - 0.5) * 0.2, ramp("#1c1410", "#382a22", "#5a463a", "#7e6650"))
    rgb = sel((wsp > 0.75) | ((wsp > 0.35) & (bay(n, n) < wsp)), smoke, rgb)
    # wires and washing lines sagging across (wrapping)
    for (y0, sag, col) in ((14, 6, "#150f0b"), (34, 9, "#150f0b"), (54, 5, "#1e1610")):
        yy = y0 + sag * np.sin(np.pi * x / n) ** 2
        rgb = setc(rgb, np.abs(y - yy) < 0.8, col)
    # a few things hanging from the middle line: shirts, a sheet, a sock
    for (cx, w, h, col) in ((10, 6, 8, "#6e5a42"), (22, 8, 6, "#8e7a58"), (44, 7, 9, "#4a3a2a"), (56, 5, 5, "#94805c")):
        yl = int(round(34 + 9 * np.sin(np.pi * cx / n) ** 2)) + 1
        rgb[yl:yl + h, cx:cx + w] = rgbof(col)
        rgb[yl:yl + h, cx:cx + 1] = dark(rgb[yl:yl + h, cx:cx + 1], 0.7)
        rgb[yl + h - 1:yl + h, cx:cx + w] = dark(rgb[yl + h - 1:yl + h, cx:cx + w], 0.6)
    return rgb


def ceil_night_red():
    n = 64
    x, y = grid(n)
    d = noise(n, 22, 6701, 4) * 0.7 + noise(n, 9, 6702, 3) * 0.3
    cloud = np.clip((d - 0.42) * 3.2, 0, 1)
    lit = np.clip((cloud - np.roll(cloud, -3, 0)) * 2.2, 0, 1) * cloud
    glow = np.clip(0.5 + 0.5 * np.cos(2 * np.pi * (y - 40) / n), 0, 1)
    sh = 0.10 + 0.14 * glow * (1 - cloud) + cloud * (0.12 + 0.2 * glow) + lit * (0.55 + 0.25 * glow) + (noise(n, 3, 6703) - 0.5) * 0.08
    rgb = q(sh, NIGHTR)
    rgb = setc(rgb, (speckle(n, 0.012, 6704) > 0) & (cloud < 0.12), "#f0dca0")
    rgb = setc(rgb, (speckle(n, 0.02, 6705) > 0) & (cloud < 0.12), "#a08060")
    return rgb


def sky_dusk():
    h, w = 64, 256
    y = np.mgrid[0:h, 0:w][0].astype(np.float32) / (h - 1)
    x = np.mgrid[0:h, 0:w][1].astype(np.float32)
    dx = np.abs(x - 70)
    dx = np.minimum(dx, w - dx)
    sun = np.exp(-(dx / 46.0) ** 2)
    sh = 0.08 + 0.58 * y ** 1.7 + 0.3 * sun * y ** 1.2
    sh += (wnoise(w, h, 56, 6801, 3) - 0.5) * 0.12 * (0.4 + y)
    streak = np.clip((wnoise(w, h, 12, 6802, 3) * 0.5 + np.roll(wnoise(w, h, 60, 6803, 2), 20, 1) * 0.6 - 0.5) * 3.5, 0, 1)
    sh = sh - 0.2 * streak * np.clip(y * 1.4, 0, 1) * (y < 0.92)
    # smoke columns climbing from the roofs, leaning in the wind
    for (x0, hgt, wid, sw) in ((24, 44, 3.4, 5), (62, 38, 2.6, 4), (108, 52, 4.0, 7), (150, 34, 2.4, 4), (196, 48, 3.2, 6), (233, 36, 2.8, 5)):
        t = np.clip((1.0 - y) * (h - 1) / hgt, 0, 1.3)
        cx = x0 + sw * t + 2.2 * np.sin(t * 6 + x0)
        d = np.abs(x - cx)
        d = np.minimum(d, w - d)
        ww = wid * (0.5 + t * 1.3)
        dens = np.clip(1 - d / ww, 0, 1) * np.clip(1.15 - t, 0, 1) * (0.55 + 0.45 * wnoise(w, h, 7, 6804 + x0, 2))
        sh = sh - 0.34 * dens
    # a silhouette of roofs along the foot, with chimneys
    rr = R(6805)
    heights = np.zeros(w, np.int32)
    xx = 0
    while xx < w:
        bw = rr.randint(10, 24)
        bh = rr.randint(2, 6)
        heights[xx:xx + bw] = bh
        if rr.rand() < 0.4:
            heights[xx + 2:xx + 4] = bh + 3
        xx += bw
    roof = np.arange(h)[:, None] >= (h - heights[None, :])
    rgb = q(sh, SKYD)
    rgb[roof] = rgbof("#14100c")
    return rgb



# ======================================================================================================================================================
# billboards: the toolkit
# ======================================================================================================================================================

class S:
    """An RGBA prop canvas (128 x 128, or 128 x 256 for the wide ones). Shapes are boolean masks; paint() shades a mask from a ramp with ordered dithering, alpha stays hard."""

    def __init__(self, w: int = 128, h: int = 128):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), np.uint8)
        self.a = np.zeros((h, w), np.uint8)
        self.y, self.x = np.mgrid[0:h, 0:w].astype(np.float32)
        self.th = bay(h, w)

    # -- masks
    def rect(self, x0, y0, x1, y1):
        return (self.x >= x0) & (self.x < x1) & (self.y >= y0) & (self.y < y1)

    def ell(self, cx, cy, rx, ry):
        return ((self.x - cx) / rx) ** 2 + ((self.y - cy) / ry) ** 2 <= 1.0

    def poly(self, pts):
        im = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(im).polygon([(float(a), float(b)) for a, b in pts], fill=255)
        return np.array(im) > 0

    def line(self, ax, ay, bx, by, w=3.0):
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy + 1e-6
        t = np.clip(((self.x - ax) * dx + (self.y - ay) * dy) / L2, 0, 1)
        return (self.x - (ax + t * dx)) ** 2 + (self.y - (ay + t * dy)) ** 2 <= (w * 0.5) ** 2

    def path(self, pts, w=3.0, closed=False):
        m = np.zeros((self.h, self.w), bool)
        pts = list(pts) + ([pts[0]] if closed else [])
        for (a, b), (c, d) in zip(pts[:-1], pts[1:]):
            m |= self.line(a, b, c, d, w)
        return m

    def nz(self, scale, seed, octaves=3):
        return wnoise(max(self.w, self.h), self.h, scale, seed, octaves)[:, :self.w]

    # -- fields
    def hl(self, x0, x1, base=0.5, amp=0.35):
        """A left-lit cylinder's shade across x0..x1."""
        u = np.clip((self.x - x0) / max(x1 - x0, 1), 0, 1)
        return base + amp * (0.55 - u) + 0.08 * np.sin(u * np.pi)

    def vl(self, y0, y1, a=0.8, b=0.3):
        u = np.clip((self.y - y0) / max(y1 - y0, 1), 0, 1)
        return a + (b - a) * u

    # -- painting
    def paint(self, mask, shade, pal, edge=None, d=1.0):
        mask = np.asarray(mask, bool)
        sh = shade if isinstance(shade, np.ndarray) else np.full((self.h, self.w), float(shade), np.float32)
        col = quantise(np.clip(sh, 0, 1), pal, d)
        self.rgb[mask] = col[mask]
        self.a[mask] = 255
        if edge is not None:
            e = self.inner_edge(mask)
            self.rgb[e] = (self.rgb[e].astype(np.float32) * edge).astype(np.uint8)
        return mask

    def solid(self, mask, hexs):
        mask = np.asarray(mask, bool)
        self.rgb[mask] = rgbof(hexs)
        self.a[mask] = 255
        return mask

    def cut(self, mask):
        self.a[np.asarray(mask, bool)] = 0

    @staticmethod
    def inner_edge(m):
        p = np.pad(m, 1)
        return m & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])

    def outline(self, f=0.5):
        e = self.inner_edge(self.a > 0)
        self.rgb[e] = (self.rgb[e].astype(np.float32) * f).astype(np.uint8)

    def halo(self, cx, cy, r, pal, strength=1.0, power=1.6, ry=None):
        """A dithered glow with hard alpha, painted only where nothing is drawn yet."""
        ry = ry or r
        d = np.sqrt(((self.x - cx) / r) ** 2 + ((self.y - cy) / ry) ** 2)
        inten = np.clip(1 - d, 0, 1) ** power * strength
        on = (inten > self.th * 0.95) & (self.a == 0)
        col = quantise(np.clip(inten * 1.2, 0, 1), pal, 0.0)
        self.rgb[on] = col[on]
        self.a[on] = 255

    def rgba(self):
        return np.dstack([self.rgb, self.a])


def stone_blocks(s: S, mask, x0, y0, bw, bh, seed, pal=LIME, light=0.5):
    """Courses of ashlar over a mask: staggered blocks, bevelled top left, soot at the foot."""
    xi, yi = s.x - x0, s.y - y0
    row = np.floor(yi / bh)
    off = (row % 2) * bw * 0.5
    col = np.floor((xi + off) / bw)
    r = R(seed)
    tone = r.rand(64, 64)[(row.astype(int)) % 64, (col.astype(int)) % 64]
    lx = (xi + off) - col * bw
    ly = yi - row * bh
    sh = light + 0.22 * (tone - 0.5) + 0.16 * ((lx < 2) | (ly < 2)) - 0.2 * ((lx >= bw - 2) | (ly >= bh - 2))
    sh += (s.nz(3, seed + 1) - 0.5) * 0.25
    joint = (lx < 1) | (ly < 1)
    sh = np.where(joint, 0.04, sh)
    return sh


# ======================================================================================================================================================
# billboards
# ======================================================================================================================================================

def thing_arch_broken():
    s = S()
    cx, cy = 64, 50
    outer = s.ell(cx, cy, 57, 46) & (s.y <= cy)
    inner = s.ell(cx, cy, 33, 30)
    ring = outer & ~inner
    pil = s.rect(7, cy, 31, 124) | s.rect(97, cy, 121, 124)
    # the view through the arch: a smoky street under a burning dusk
    view = (inner | s.rect(31, cy, 97, 124))
    yy = (s.y - 14) / 84.0
    sky = 0.18 + 0.85 * np.clip(yy, 0, 1) ** 1.3 + 0.12 * np.exp(-((s.x - 46) / 22) ** 2) * np.clip(yy, 0, 1)
    sky += (s.nz(14, 7001) - 0.5) * 0.14
    s.paint(view, sky, SKYD)
    # smoke column and distant roofs
    col = view & (np.abs(s.x - (74 + (88 - s.y) * 0.16)) < (3 + (90 - s.y) * 0.07)) & (s.y < 90) & (s.nz(5, 7002) > 0.3)
    s.paint(col, 0.1 + s.nz(4, 7003) * 0.3, ramp("#241a16", "#382a24", "#52403a"))
    hts = R(7004).randint(6, 20, 40)
    roofs = view & (s.y >= 90 - hts[np.clip(((s.x - 30) / 4).astype(int), 0, 39)]) & (s.y < 98)
    s.solid(roofs, "#1c1410")
    s.solid(roofs & (s.nz(2, 7005, 2) > 0.8) & (s.y > 86), "#d08a3a")
    street = view & (s.y >= 96)
    s.paint(street, 0.5 - 0.3 * (s.y - 96) / 28 + (s.nz(3, 7006) - 0.5) * 0.3, COBB)
    s.paint(view & (np.abs(s.x - 64) < 1.5) & (s.y >= 90) & (s.y < 112), 0.25, SOOT)  # a lamp post far off
    # the stone
    sh = np.full((s.h, s.w), 0.5, np.float32)
    th = np.arctan2(s.y - cy, s.x - cx)
    seg = (th + np.pi) / (np.pi / 12)
    fr = seg % 1.0
    ri = np.floor(seg).astype(int)
    tone = R(7010).rand(24)[ri % 24]
    rsh = 0.5 + 0.24 * (tone - 0.5) + 0.14 * (fr < 0.16) - 0.18 * (fr > 0.84) + (s.nz(3, 7011) - 0.5) * 0.25
    rsh = np.where((fr < 0.05) | (fr > 0.97), 0.05, rsh)
    # the arch gets lighter towards the lit upper left, darker to the right
    rsh = rsh + 0.12 * (1 - (s.x - 7) / 114.0) - 0.06
    psh = stone_blocks(s, pil, 7, cy, 24, 13, 7012, light=0.48) + 0.1 * (1 - (s.x - 7) / 114.0) - 0.04
    psh += 0.12 * np.exp(-((s.y - cy) / 6.0) ** 2) * 0
    s.paint(ring, rsh, LIME)
    # the collapse: the right half of the arch is gone, its edge ragged
    gap = s.poly([(70, 0), (128, 0), (128, 54), (119, 50), (116, 60), (108, 48), (102, 56), (99, 42), (93, 36), (91, 27), (84, 24), (82, 14), (76, 12), (73, 6)])
    ring_k = ring & ~gap
    pil_k = pil & ~gap
    s.a[:] = np.where(view, s.a, 0)
    s.paint(ring_k, rsh, LIME, edge=0.5)
    s.paint(pil_k, psh, LIME, edge=0.5)
    # impost blocks where the arch springs, a plinth at the foot
    s.paint(s.rect(4, cy - 2, 34, cy + 6), 0.62 + (s.nz(3, 7013) - 0.5) * 0.2 - 0.18 * (s.y > cy + 3), LIME, edge=0.5)
    s.paint(s.rect(4, 112, 34, 124) | s.rect(94, 112, 124, 124), 0.42 + (s.nz(3, 7014) - 0.5) * 0.3 + 0.12 * (s.y < 114), LIME, edge=0.5)
    s.a[gap & ~view] = 0
    # a fallen keystone and rubble on the ground
    s.paint(s.poly([(40, 124), (46, 112), (80, 108), (86, 124)]), 0.55 + (s.nz(3, 7015) - 0.5) * 0.2 - 0.25 * (s.x > 66), LIME, edge=0.45)
    s.paint(s.poly([(46, 112), (80, 108), (81, 112), (47, 116)]), 0.8, LIME)
    for (x0, y0, w, h) in ((80, 116, 12, 8), (92, 112, 8, 12), (36, 118, 9, 6), (100, 118, 14, 6), (20, 120, 8, 4)):
        s.paint(s.rect(x0, y0, x0 + w, y0 + h), 0.35 + R(x0).rand() * 0.25 + (s.nz(2, x0) - 0.5) * 0.2, LIME, edge=0.5)
    s.outline(0.55)
    return s.rgba()


def thing_awning():
    s = S()
    # the shopfront: sooty ochre render, pilasters, a roller shutter with rust
    wall = s.rect(4, 16, 124, 124)
    s.paint(wall, 0.42 + (s.nz(4, 7101) - 0.5) * 0.35 - 0.2 * grime_field(s, 7102), OCHRE, edge=0.5)
    for x0 in (4, 112):
        s.paint(s.rect(x0, 20, x0 + 12, 124), s.hl(x0, x0 + 12, 0.55, 0.3) + (s.nz(3, 7103) - 0.5) * 0.2, GREYST, edge=0.5)
    sh_rect = s.rect(18, 62, 110, 122)
    slat = (s.y - 62) % 4
    ssh = 0.5 + 0.2 * (slat == 0) - 0.22 * (slat == 3) + (s.nz(3, 7104) - 0.5) * 0.25 - 0.1 * (s.y - 62) / 60.0
    ssh -= 0.18 * (s.nz(6, 7105, 2) > 0.62)
    s.paint(sh_rect, ssh, ramp("#14120e", "#2a2620", "#443d34", "#665c4c", "#847860"), edge=0.5)
    rst = sh_rect & (s.nz(9, 7106, 3) > 0.6)
    s.paint(rst, 0.3 + 0.5 * s.nz(2, 7107), ramp("#2a1408", "#52280e", "#7a3e16", "#a05a24"))
    s.paint(s.rect(18, 118, 110, 124), 0.2, STEEL, edge=0.6)  # bottom bar
    s.paint(s.rect(54, 108, 62, 112), 0.8, STEEL, edge=0.5)  # a padlock hasp
    # the fascia board above, plain dark wood
    s.paint(s.rect(8, 6, 120, 22), 0.4 + 0.1 * np.sin(s.x * 0.4 + s.nz(6, 7108) * 6) + 0.2 * (s.y < 8) - 0.2 * (s.y > 19), OAK, edge=0.5)
    # the awning: a sloping canvas, wider at the foot, sagging in the middle, scalloped, sun-faded stripes
    top, foot = 22, 64
    sag = 5 * np.cos(np.pi * (s.x - 64) / 118) ** 2
    ybot = foot + sag
    hw = 44 + (np.clip(s.y, top, foot) - top) / (foot - top) * 16
    can = (s.y >= top) & (s.y <= ybot) & (np.abs(s.x - 64) <= hw)
    # scallops on the valance
    sc = (s.x - 4) % 14
    scal = ybot + 5 * np.sqrt(np.clip(1 - ((sc - 7) / 7.2) ** 2, 0, 1))
    can = ((s.y >= top) & (s.y <= scal) & (np.abs(s.x - 64) <= hw))
    u = (s.x - 64) / hw
    stripe = (np.floor((u + 1) * 5.5).astype(int) % 2) == 0
    fold = np.sin((s.x + 3) * 0.5) * 0.06
    base = np.where(stripe, 0.7, 0.24) + fold
    base -= 0.22 * np.clip((s.y - top) / (foot - top), 0, 1) ** 2 * 0.6  # the lower part darker, in the awning's shade
    base += 0.1 * np.clip(1 - (s.y - top) / 6, 0, 1)
    base += (s.nz(3, 7109) - 0.5) * 0.25
    s.paint(can, base, ramp("#1c120c", "#42301f", "#6a5238", "#947a56", "#bca680", "#dcc9a0"), edge=0.5)
    # a rip with a flap hanging
    rip = s.poly([(86, 40), (98, 38), (96, 56), (92, 66), (88, 56)])
    s.paint(rip, 0.05, SOOT)
    s.paint(s.poly([(98, 38), (104, 44), (101, 62), (96, 56)]), 0.35 + 0.2 * (s.x < 100), ramp("#1c120c", "#42301f", "#6a5238", "#947a56"), edge=0.5)
    # iron arms
    for (ax, bx) in ((10, 6), (118, 122)):
        s.paint(s.line(ax, 24, bx, 62, 2.4), 0.3, STEEL)
    s.outline(0.55)
    return s.rgba()


def grime_field(s: S, seed):
    return np.clip((s.nz(10, seed, 3) - 0.5) * 2.5, 0, 1) + 0.0 * s.y


def thing_broken_wall():
    s = S()
    prof = [(8, 124), (10, 96), (14, 84), (18, 62), (24, 50), (28, 34), (34, 18), (40, 26), (44, 44), (52, 38), (60, 30), (70, 24), (78, 32), (84, 48), (92, 44), (98, 60), (104, 76), (112, 70), (118, 92), (121, 124)]
    ytop = np.interp(np.arange(128), [p[0] for p in prof], [p[1] for p in prof]).astype(np.float32)
    ytop = np.round(ytop / 6.4) * 6.4 + 2
    ytop = np.repeat(ytop[::6][:22], 6)[:128]
    body = (s.y >= ytop[s.x.astype(int)]) & (s.y < 124) & (s.x >= 8) & (s.x < 122)
    hole = s.rect(51, 57, 79, 94) | s.ell(65, 57, 14, 11)
    # the glow behind: yellow low, red high, a black rafter across
    gl = np.clip(1 - (s.y - 46) / 48.0, 0, 1)
    glow = 0.3 + 0.7 * (1 - gl) ** 1.2
    glow += (s.nz(4, 7201) - 0.5) * 0.2
    s.paint(hole, glow, FIRE)
    s.paint(hole & (np.abs((s.y - 68) - (s.x - 51) * 0.12) < 2.0), 0.1, SOOT)
    s.paint(hole & (np.abs(s.x - 70) < 1.5) & (s.y > 74), 0.1, SOOT)
    bsh, bm = bricks(128, rows=20, cols=8, mortar=1, seed=7202, wear=0.5)
    near = hole | s.rect(46, 52, 84, 100)
    sh = bsh * 0.9 - 0.12 * grime_field(s, 7203) + (s.nz(8, 7204) - 0.5) * 0.1
    # fire-lit rims round the hole and the broken top edge
    wall_sh = sh
    mortar = bm > 0.5
    wcol = q(wall_sh, SOOTB)
    wcol = sel(mortar, q(np.full((128, 128), 0.25), MORTAR), wcol)
    s.rgb[body & ~hole] = wcol[body & ~hole]
    s.a[body & ~hole] = 255
    # rim light: pixels within 3 px of the hole, and on the upper edge of the silhouette, take the fire colour
    hm = hole.astype(np.float32)
    ring_h = np.zeros_like(hm, bool)
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if dx * dx + dy * dy <= 10:
                ring_h |= np.roll(np.roll(hole, dx, 1), dy, 0)
    ring_h &= body & ~hole
    s.rgb[ring_h] = q(0.3 + 0.5 * wall_sh, FIRE)[ring_h]
    e = S.inner_edge(body & ~hole)
    top_e = e & (np.roll(body, 1, 0) == False)
    s.rgb[e] = (s.rgb[e].astype(np.float32) * 0.5).astype(np.uint8)
    s.solid(top_e & (s.th > 0.35), "#c4561e")
    # a sill and lintel at the window, slumped lath hanging out of the hole
    s.paint(s.rect(48, 92, 82, 97), 0.5 + 0.2 * (s.y < 94), STONEN, edge=0.5)
    s.paint(s.line(60, 60, 72, 92, 2.0), 0.2, SOOT)
    # rubble at the foot
    r = R(7210)
    for k in range(16):
        x0 = r.randint(6, 116)
        w = r.randint(4, 10)
        h = r.randint(3, 7)
        s.paint(s.rect(x0, 124 - h, x0 + w, 124), 0.25 + r.rand() * 0.35, SOOTB, edge=0.5)
    s.outline(0.5)
    return s.rgba()


def thing_burnt_car():
    s = S()
    body = s.poly([(6, 104), (6, 86), (11, 76), (26, 70), (36, 68), (42, 50), (52, 40), (84, 38), (94, 46), (99, 64), (112, 68), (120, 76), (122, 88), (121, 104)])
    for (wx, wy) in ((34, 106), (94, 106)):
        body &= ~s.ell(wx, wy, 16, 15)
    sh = 0.24 + 0.2 * s.vl(36, 104, 1, 0) + (s.nz(4, 7301) - 0.5) * 0.25
    # soot black with a dull sheen along the top edges, flaking paint
    sh += 0.22 * ((s.y < 42) | ((s.y > 66) & (s.y < 70))) * 0.6
    sh -= 0.12 * (s.x > 80)
    s.paint(body, sh, SOOTB, edge=0.55)
    # chassis and the dark under the car
    s.paint(s.rect(14, 100, 116, 112), 0.08 + 0.06 * s.nz(3, 7302), SOOT)
    # burnt-out windows: no glass, ember glow inside
    for pts in ([(58, 46), (84, 46), (91, 54), (93, 63), (58, 63)], [(40, 63), (46, 52), (54, 46), (55, 46), (55, 63)]):
        w = s.poly(pts)
        g = 0.08 + 0.55 * np.clip((s.y - 46) / 20, 0, 1) ** 1.5 * (s.nz(3, 7303) > 0.35) + 0.1 * s.nz(2, 7304)
        s.paint(w, g, ramp("#0a0302", "#2a0a04", "#6a1a08", "#b4380c", "#f07a1a"), edge=0.4)
    s.paint(s.rect(55, 46, 59, 64), 0.2, SOOTB)  # the B pillar
    # door seams, a buckled bonnet, a gaping grille
    for x0 in (59, 99):
        s.paint(s.line(x0, 64, x0 - 1, 100, 1.2), 0.04, SOOT)
    s.paint(s.line(100, 66, 118, 72, 1.2), 0.06, SOOT)
    s.paint(s.line(6, 90, 120, 92, 1.0), 0.08, SOOT)
    s.paint(s.rect(112, 78, 122, 92), 0.09, SOOT, edge=0.5)  # radiator hole
    s.paint(s.rect(114, 82, 122, 88), 0.55 + 0.3 * s.nz(2, 7305), FIRE)  # glow in it
    # holes burnt in the sills showing embers
    for (x0, y0, w, h) in ((22, 92, 8, 5), (66, 94, 10, 5), (80, 90, 6, 4), (12, 82, 5, 4)):
        s.paint(s.rect(x0, y0, x0 + w, y0 + h), 0.3 + 0.55 * s.nz(2, x0 + 7306), FIRE, edge=0.35)
    # bare rims, no tyres: a ring, spokes, a hub
    for (wx, wy) in ((34, 108), (94, 108)):
        ring = s.ell(wx, wy, 10, 10) & ~s.ell(wx, wy, 7, 7)
        s.paint(ring, 0.32 + 0.35 * (s.x < wx), STEEL, edge=0.5)
        s.paint(s.ell(wx, wy, 7, 7), 0.07, SOOT)
        for a in (0, 1, 2, 3):
            ang = a * np.pi / 4 + 0.3
            s.paint(s.line(wx - 7 * np.cos(ang), wy - 7 * np.sin(ang), wx + 7 * np.cos(ang), wy + 7 * np.sin(ang), 1.4), 0.3, STEEL)
        s.paint(s.ell(wx, wy, 2.5, 2.5), 0.55, STEEL)
    # little embers drifting off it
    r = R(7307)
    for k in range(8):
        px, py = r.randint(30, 100), r.randint(22, 38)
        s.solid(s.rect(px, py, px + 1, py + 1), ["#f07a1a", "#ffc050", "#b8380c"][k % 3])
    s.outline(0.5)
    return s.rgba()


def thing_cafe_table():
    s = S()
    wood = ramp("#1a0e06", "#3a2412", "#5e3c1c", "#86602e", "#b08a46")

    def chair(flip):
        def X(x):
            return 127 - x if flip else x
        parts = []
        # legs (bentwood curves), a stretcher ring, the seat, the hooped back
        for pts in ([(14, 78), (11, 100), (8, 120)], [(34, 78), (36, 100), (38, 120)], [(18, 78), (17, 100), (15, 118)], [(30, 78), (31, 100), (32, 118)]):
            parts.append((s.path([(X(a), b) for a, b in pts], 3.0), 0.42))
        parts.append((s.path([(X(11), 104), (X(24), 108), (X(37), 104)], 2.5), 0.4))
        for m, shd in parts:
            s.paint(m, shd + 0.3 * (s.nz(2, 7401) - 0.5), wood)
        seat = s.ell(X(24), 76, 17, 5)
        s.paint(seat, 0.35 + 0.35 * np.clip(1 - (s.y - 71) / 8, 0, 1), wood, edge=0.6)
        s.paint(s.ell(X(24), 79, 17, 4) & ~seat, 0.28, wood)
        # the hooped back: two posts and a swept top loop
        loop = s.path([(X(10), 76), (X(8), 58), (X(10), 44), (X(18), 38), (X(26), 42), (X(28), 52), (X(30), 64), (X(32), 76)], 3.0)
        s.paint(loop, 0.46 + 0.3 * (s.nz(2, 7402) - 0.5), wood, edge=0.55)
        s.paint(s.path([(X(14), 50), (X(20), 48), (X(22), 56)], 2.0), 0.4, wood)
        s.paint(s.path([(X(10), 44), (X(18), 38), (X(26), 42)], 1.0), 0.8, wood)  # a highlight on the hoop

    chair(False)
    chair(True)
    # the table: marble top with a brass rim, a cast-iron pedestal and three feet
    s.paint(s.rect(61, 76, 67, 112), s.hl(61, 67, 0.4, 0.5), STEEL, edge=0.5)
    s.paint(s.ell(64, 114, 24, 6), 0.22 + 0.2 * (s.x < 60), STEEL, edge=0.5)
    s.paint(s.ell(64, 110, 7, 3), 0.55, STEEL, edge=0.5)
    s.paint(s.ell(64, 72, 33, 9), 0.3, BRASS)  # under the top
    top = s.ell(64, 68, 33, 8)
    s.paint(s.ell(64, 71, 33, 8) & ~top, 0.35, BRASS)
    s.paint(top, 0.62 + 0.12 * s.nz(3, 7403) + 0.12 * (s.x < 50), CREAM, edge=0.55)
    s.paint(top & ~s.ell(64, 68, 29, 6), 0.55, BRASS)
    # a bottle and two glasses (the glass is amber)
    s.paint(s.rect(59, 48, 68, 70), 0.2 + 0.4 * (s.x < 62), ramp("#040a06", "#0c1c10", "#1c3a22", "#3a6a42"), edge=0.5)
    s.paint(s.rect(62, 32, 65, 50), 0.2 + 0.4 * (s.x < 63), ramp("#040a06", "#0c1c10", "#1c3a22", "#3a6a42"), edge=0.5)
    s.paint(s.rect(62, 30, 65, 33), 0.5, ramp("#3a2410", "#8a6030", "#c09050"))
    s.paint(s.rect(59, 55, 68, 63), 0.7, CREAM)  # a blank label
    for (gx, gy, gw, gh) in ((75, 54, 8, 12), (46, 58, 7, 9)):
        gl = s.poly([(gx, gy), (gx + gw, gy), (gx + gw - 2, gy + gh), (gx + 2, gy + gh)])
        s.paint(gl, 0.3 + 0.5 * np.clip((s.y - gy) / gh, 0, 1) * 0.6 + 0.3 * (s.x < gx + 3), ramp("#1a0e04", "#4a2a0a", "#a06a1c", "#e0a640", "#ffe08a"), edge=0.55)
        s.paint(s.rect(gx + 2, gy + gh, gx + gw - 2, gy + gh + 2), 0.5, CHROME)
    s.outline(0.5)
    return s.rgba()


DIGITS = {
    "2": [[(0.08, 0.25), (0.3, 0.06), (0.7, 0.06), (0.92, 0.25), (0.88, 0.45), (0.1, 0.94), (0.96, 0.94)]],
    "4": [[(0.72, 0.96), (0.72, 0.06), (0.04, 0.68), (0.98, 0.68)]],
    "3": [[(0.08, 0.14), (0.4, 0.05), (0.8, 0.12), (0.88, 0.3), (0.5, 0.48), (0.9, 0.66), (0.84, 0.86), (0.4, 0.96), (0.06, 0.84)]],
    "7": [[(0.06, 0.06), (0.94, 0.06), (0.4, 0.96)]],
}


def thing_count_slate():
    s = S()
    # a ledge, the frame, the board
    s.paint(s.rect(6, 100, 122, 112), 0.5 + 0.3 * (s.y < 102) - 0.3 * (s.y > 109), OAK, edge=0.5)
    s.paint(s.rect(10, 112, 22, 124), 0.3, OAK, edge=0.5)
    s.paint(s.rect(106, 112, 118, 124), 0.3, OAK, edge=0.5)
    frame = s.rect(8, 8, 120, 100)
    fsh = 0.5 + 0.1 * np.sin(s.x * 0.5 + s.nz(5, 7501) * 5) + 0.2 * ((s.x < 11) | (s.y < 11)) - 0.2 * ((s.x >= 117) | (s.y >= 97))
    s.paint(frame, fsh, OAK, edge=0.5)
    board = s.rect(13, 13, 115, 95)
    bsh = 0.3 + 0.12 * s.nz(3, 7502) + (s.nz(2, 7503) - 0.5) * 0.1
    s.paint(board, bsh, ramp("#080b09", "#10150f", "#1a211a", "#2a332a", "#3c473c"))
    # old wiped chalk: smudges (not letters)
    sm = board & (s.nz(12, 7504, 3) > 0.52) & (s.th * 0.4 + 0.3 < s.nz(4, 7505))
    s.paint(sm, 0.5 + 0.2 * s.nz(3, 7506), ramp("#10150f", "#2a332a", "#4a554a", "#6a766a"))
    # the digits: thick chalk strokes with a ragged edge
    chalk = np.zeros((128, 128), bool)
    for k, ch in enumerate("24"):
        x0, y0, w, h = 22 + k * 46, 20, 36, 62
        for stroke in DIGITS[ch]:
            pts = [(x0 + a * w, y0 + b * h) for a, b in stroke]
            chalk |= s.path(pts, 6.5)
    rag = (s.nz(2, 7507, 2) > 0.16)
    chalk &= rag
    csh = 0.62 + 0.3 * s.nz(2, 7508) + 0.1 * (s.th - 0.5)
    s.paint(chalk, csh, WHITE)
    s.paint(chalk & (s.nz(1.5, 7509, 2) > 0.74), 0.9, WHITE)
    # a duster and a stub of chalk on the ledge
    s.paint(s.rect(80, 94, 106, 101), 0.12 + 0.3 * (s.y < 96), ramp("#0a0806", "#2a1c12", "#4a3424", "#6a4e38"), edge=0.5)
    s.paint(s.rect(80, 99, 106, 101), 0.45, OAK)
    s.paint(s.rect(84, 93, 100, 95) & (s.nz(1.2, 7510, 2) > 0.4), 0.8, WHITE)
    s.paint(s.rect(34, 97, 46, 100), 0.7 + 0.2 * (s.y < 98), WHITE, edge=0.7)
    s.outline(0.5)
    return s.rgba()


def thing_desk_colonel():
    s = S()
    # pedestals with three drawers each, a kneehole between, bun feet
    oak_n = (s.nz(2, 7601, 2) - 0.5) * 0.12
    for (x0, x1) in ((6, 44), (84, 122)):
        s.paint(s.rect(x0, 76, x1, 114), 0.4 + oak_n + 0.1 * (s.y < 78) - 0.1 * (s.y > 111), OAK, edge=0.5)
        for dy in (0, 12, 24):
            d = s.rect(x0 + 3, 78 + dy, x1 - 3, 88 + dy)
            s.paint(d, 0.46 + oak_n + 0.2 * ((s.y < 80 + dy) | (s.x < x0 + 5)) - 0.2 * ((s.y >= 86 + dy) | (s.x >= x1 - 5)), OAK, edge=0.45)
            cx = (x0 + x1) / 2
            s.paint(s.rect(cx - 5, 82 + dy, cx + 5, 85 + dy), 0.35 + 0.5 * (s.y < 83.5 + dy), BRASS, edge=0.5)
        s.paint(s.rect(x0 + 2, 114, x0 + 9, 124), 0.3 + 0.4 * (s.x < x0 + 4), OAK, edge=0.5)
        s.paint(s.rect(x1 - 9, 114, x1 - 2, 124), 0.3 + 0.4 * (s.x < x1 - 7), OAK, edge=0.5)
    s.paint(s.rect(44, 76, 84, 112), 0.03 + 0.05 * s.nz(3, 7602), SOOT)  # the kneehole
    s.paint(s.rect(46, 82, 82, 108), 0.2 + oak_n + 0.12 * (s.y < 85), OAK, edge=0.5)  # the modesty panel
    s.paint(s.rect(52, 88, 76, 102), 0.3 + oak_n - 0.1 * (s.y > 98) + 0.14 * (s.y < 90), OAK, edge=0.45)
    s.paint(s.rect(46, 76, 82, 82), 0.04, SOOT)
    # the apron and the top: green leather in a brass frame, seen a little from above
    s.paint(s.rect(2, 72, 126, 77), 0.55 + 0.25 * (s.y < 74) + oak_n, OAK, edge=0.5)
    s.paint(s.rect(2, 72, 126, 73), 0.75, BRASS)
    top = s.poly([(16, 60), (112, 60), (125, 72), (3, 72)])
    s.paint(top, 0.5 + 0.18 * (1 - (s.x - 3) / 122.0) + (s.nz(3, 7603) - 0.5) * 0.1 - 0.1 * (s.y > 69), LEATHER, edge=0.45)
    frame = top & ~s.poly([(20, 63), (108, 63), (119, 70), (9, 70)])
    s.paint(frame, 0.45 + 0.4 * (s.y < 62), BRASS)
    s.paint(top & s.poly([(20, 63), (108, 63), (119, 70), (9, 70)]) & (np.abs(s.y - 66.5) < 0.6), 0.25, BRASS)
    # the brass lamp: weighted base, stem, a hooded shade, warm light spilling
    s.halo(22, 46, 26, ramp("#2a1408", "#5a3410", "#a06a24", "#e0a850"), 0.5, 1.8)
    s.paint(s.ell(22, 62, 9, 3), 0.5, BRASS, edge=0.5)
    s.paint(s.rect(20, 40, 24, 62), s.hl(20, 24, 0.55, 0.4), BRASS)
    shade = s.ell(22, 31, 15, 11) & (s.y <= 34)
    s.paint(shade, 0.35 + 0.5 * np.clip(1 - np.hypot(s.x - 16, s.y - 25) / 18, 0, 1), BRASS, edge=0.5)
    s.paint(s.rect(7, 34, 37, 36), 0.4, BRASS, edge=0.5)
    s.paint(s.ell(22, 39, 5, 3), 0.95, ramp("#fff0b0", "#fff0b0"))  # the bulb, lit
    # a stack of ribbon-tied papers
    st = s.rect(84, 46, 108, 62)
    s.paint(st, 0.65 + 0.2 * ((s.y % 3) == 0) - 0.18 * ((s.y % 3) == 2) + (s.nz(2, 7604) - 0.5) * 0.2, PAPER, edge=0.5)
    s.paint(s.rect(93, 46, 99, 62), 0.45 + 0.2 * (s.x < 95), ramp("#2a0608", "#5a1016", "#8a1c24"), edge=0.5)
    s.paint(s.poly([(96, 46), (90, 41), (91, 47)]), 0.6, ramp("#2a0608", "#5a1016", "#8a1c24"), edge=0.5)
    s.paint(s.poly([(96, 46), (102, 41), (101, 47)]), 0.5, ramp("#2a0608", "#5a1016", "#8a1c24"), edge=0.5)
    s.paint(s.rect(86, 41, 104, 46), 0.7 + 0.2 * (s.y % 2 == 0), PAPER, edge=0.5)
    # a tiny model bomber on a brass stand: fuselage, high wing, twin fins, nacelles
    s.paint(s.ell(64, 59, 8, 2.5), 0.5, BRASS, edge=0.5)
    s.paint(s.rect(63, 49, 65, 59), 0.6, BRASS)
    s.paint(s.ell(64, 46, 17, 3), 0.55 + 0.3 * (s.y < 45), STEEL, edge=0.5)
    s.paint(s.poly([(44, 44), (84, 44), (88, 47), (40, 47)]), 0.6 + 0.2 * (s.y < 45), STEEL, edge=0.5)
    s.paint(s.poly([(48, 46), (44, 36), (50, 38), (53, 45)]), 0.5, STEEL, edge=0.5)
    s.paint(s.poly([(46, 48), (49, 48), (50, 52), (47, 52)]), 0.3, STEEL)
    for ex in (54, 74):
        s.paint(s.rect(ex, 43, ex + 4, 49), 0.35 + 0.3 * (s.x < ex + 2), STEEL, edge=0.5)
    s.paint(s.rect(80, 45, 83, 48), 0.3, OLIVE)
    s.outline(0.5)
    return s.rgba()


SAND = ramp("#1c160e", "#3e3220", "#6a583a", "#94805a", "#b8a47a")
LEATHERB = ramp("#0e0805", "#241209", "#3e2210", "#5c3a1c", "#7e5428", "#a07438")
RED = ramp("#1c0204", "#3e0608", "#700c0c", "#b01818", "#e83030", "#ff7a66")
SEA = ramp("#0e1618", "#1a2a2e", "#2a4044", "#3e5a5c", "#5a7a78")
VELVET = ramp("#060204", "#16060c", "#2a0a14", "#481424", "#6a2234")


def flame_tongue(s: S, fx, base_y, fh, fw, seed, layers=((1.0, 0.3), (0.66, 0.58), (0.34, 0.86))):
    rr = R(seed)
    ph = rr.uniform(0, 6.28)
    for (sc, shd) in layers:
        u = (base_y - s.y) / (fh * sc)
        wob = 4.0 * np.sin(u * 4.5 + ph) * u
        wid = fw * sc * np.clip(1 - u, 0, 1) ** 0.75 * (1 + 0.15 * np.sin(u * 9 + ph))
        m = (u >= 0) & (u <= 1) & (np.abs(s.x - fx - wob) < wid)
        s.paint(m, shd + 0.12 * (1 - np.clip(u, 0, 1)) + (s.th - 0.5) * 0.08, FIRE)


def thing_fire_barrel():
    s = S()
    x0, x1, ytop, ybot = 32, 96, 66, 124
    ry = 9
    cyl = s.rect(x0, ytop, x1, ybot - 4) | s.ell(64, ybot - 4, (x1 - x0) / 2, 4)
    body = cyl & ~s.ell(64, ytop, (x1 - x0) / 2, ry) | (s.rect(x0, ytop, x1, ytop + 1))
    body = (s.rect(x0, ytop, x1, ybot - 4) | (s.ell(64, ybot - 4, 32, 4) & (s.y >= ybot - 4)))
    sh = s.hl(x0, x1, 0.45, 0.45) + (s.nz(4, 7701) - 0.5) * 0.15
    sh += 0.35 * np.clip(1 - (s.y - ytop) / 26, 0, 1)  # lit by the fire from above
    s.paint(body, sh, ramp("#0a0807", "#1a1512", "#2e2620", "#4a3c30", "#6a5440", "#9a6a3c", "#d08440"), edge=0.5)
    # ribs and rust
    for yy in (78, 98, 116):
        s.paint(s.rect(x0, yy, x1, yy + 3) & body, np.clip(sh + 0.08, 0, 1) * 0.9 + 0.1 * (s.y < yy + 1) - 0.18 * (s.y > yy + 1), ramp("#0a0807", "#1a1512", "#2e2620", "#4a3c30", "#6a5440", "#9a6a3c", "#d08440"))
    rst = body & (s.nz(8, 7702, 3) > 0.58)
    s.paint(rst, 0.28 + 0.5 * s.nz(2, 7703) + 0.2 * s.hl(x0, x1, 0.5, 0.5), ramp("#2a1006", "#52240c", "#7a3a14", "#a85a24"))
    # punched holes with the fire showing
    for (hx, hy) in ((46, 88), (76, 104), (60, 76)):
        s.paint(s.ell(hx, hy, 3.2, 2.6), 0.55 + 0.4 * s.nz(2, hx), FIRE, edge=0.4)
    # the open mouth: dark rim, glowing coals
    mouth = s.ell(64, ytop, 32, ry)
    s.paint(mouth, 0.5 + 0.4 * (1 - np.clip(np.hypot((s.x - 64) / 32, (s.y - ytop) / ry), 0, 1)) + 0.1 * s.nz(2, 7704), FIRE, edge=0.5)
    s.paint(mouth & ~s.ell(64, ytop, 28, ry - 2.5), 0.3, STEEL)
    # flames: tongues rising from the mouth, hottest in the middle
    for k, (fx, fh, fw) in enumerate(((46, 38, 9), (82, 42, 9), (56, 56, 11), (72, 52, 10), (64, 60, 10), (52, 30, 7), (78, 30, 7))):
        flame_tongue(s, fx, ytop + 2, fh, fw, 7710 + k)
    # sparks and embers flying
    r = R(7720)
    for k in range(14):
        px, py = int(64 + r.normal(0, 16)), int(r.uniform(4, 52))
        s.solid(s.rect(px, py, px + 1 + (k % 5 == 0), py + 1), ["#ffc050", "#f07a1a", "#fff0b0", "#b8380c"][k % 4])
    s.halo(64, 56, 46, FIRE, 0.28, 1.3)
    s.outline(0.5)
    return s.rgba()


def thing_globe():
    s = S()
    cx, cy, rr = 64, 48, 34
    # the stand first: turned column, three splayed feet, a brass collar
    wood = ramp("#0c0704", "#1e1109", "#32200f", "#4e3217", "#6e4a22", "#94682e")
    s.paint(s.line(64, 88, 34, 122, 5), 0.4 + 0.3 * (s.x < 50), wood, edge=0.55)
    s.paint(s.line(64, 88, 94, 122, 5), 0.3, wood, edge=0.55)
    s.paint(s.line(64, 94, 64, 124, 6), 0.4, wood, edge=0.55)
    s.paint(s.rect(58, 84, 70, 112), s.hl(58, 70, 0.55, 0.45) + 0.08 * np.sin(s.y * 0.9), wood, edge=0.55)
    s.paint(s.ell(64, 98, 8, 3), 0.65, wood, edge=0.55)
    s.paint(s.ell(64, 112, 12, 4), 0.6, wood, edge=0.55)
    s.paint(s.rect(56, 84, 72, 89), s.hl(56, 72, 0.55, 0.4), BRASS, edge=0.5)
    # the brass meridian ring, then the sphere on its axis
    ring = s.ell(cx, cy, rr + 7, rr + 8) & ~s.ell(cx, cy, rr + 4, rr + 5)
    s.paint(ring, s.hl(cx - rr - 7, cx + rr + 7, 0.5, 0.6), BRASS, edge=0.5)
    sphere = s.ell(cx, cy, rr, rr)
    dx, dy = (s.x - cx) / rr, (s.y - cy) / rr
    z = np.sqrt(np.clip(1 - dx * dx - dy * dy, 0, 1))
    tilt = np.deg2rad(23)
    rx_, ry_ = dx * np.cos(tilt) + dy * np.sin(tilt), -dx * np.sin(tilt) + dy * np.cos(tilt)
    lon = np.arctan2(rx_, z) + 0.9
    lat = np.arcsin(np.clip(ry_, -1, 1))
    li = ((lon / (2 * np.pi) % 1.0) * 255).astype(int)
    la = np.clip(((lat / np.pi + 0.5)) * 127, 0, 127).astype(int)
    field = noise(256, 36, 7801, 4)[:128, :]
    land = field[la, li] > 0.5
    lam = np.clip(0.2 + 0.85 * (-dx * 0.5 - dy * 0.55 + z * 0.67), 0, 1)
    ocean = q(lam * 0.9 + 0.05, SEA)
    cont = q(0.2 + 0.7 * lam + (noise(256, 6, 7802)[:128, :][la, li] - 0.5) * 0.1, CREAM)
    img = sel(land, cont, ocean)
    # graticule: faint lines every 30 degrees, no labels
    glon = np.abs(((lon / (2 * np.pi)) * 12) % 1.0 - 0.5)
    glat = np.abs(((lat / np.pi + 0.5) * 6) % 1.0 - 0.5)
    grat = ((glon > 0.46) | (glat > 0.46)) & (z > 0.1)
    img = sel(grat, (img.astype(np.float32) * 0.72).astype(np.uint8), img)
    s.rgb[sphere] = img[sphere]
    s.a[sphere] = 255
    s.rgb[S.inner_edge(sphere)] = (s.rgb[S.inner_edge(sphere)].astype(np.float32) * 0.5).astype(np.uint8)
    for (gx, gy) in ((46, 30), (47, 30), (46, 31)):
        s.solid(s.rect(gx, gy, gx + 1, gy + 1), "#fffaf0")
    # axis caps and the lower bracket
    s.paint(s.ell(cx, cy - rr - 6, 5, 4), 0.7, BRASS, edge=0.5)
    s.paint(s.ell(cx, cy + rr + 7, 5, 4), 0.55, BRASS, edge=0.5)
    s.paint(s.rect(61, cy + rr + 8, 67, 86), s.hl(61, 67, 0.55, 0.4), BRASS, edge=0.5)
    s.outline(0.5)
    return s.rgba()


def thing_hq_door():
    s = S()
    # what is left of the wall: ochre render over brick, the top corner blown away
    top = [(4, 124), (4, 44), (10, 34), (18, 40), (26, 20), (36, 28), (46, 8), (66, 6), (80, 16), (96, 8), (106, 26), (118, 20), (124, 40), (124, 124)]
    wall = s.poly(top)
    bsh, bm = bricks(128, rows=20, cols=8, mortar=1, seed=7901, wear=0.4)
    stc = 0.45 + (s.nz(4, 7902) - 0.5) * 0.4 - 0.2 * grime_field(s, 7903)
    s.paint(wall, stc, OCHRE, edge=0.5)
    bare = wall & ((noise(128, 22, 7904, 3) > 0.62) | ((s.y < 50) & (s.x < 34) & (s.nz(10, 7905) > 0.35)) | ((s.y < 40) & (s.x > 88) & (s.nz(10, 7906) > 0.4)))
    bc = sel(bm > 0.5, q(np.full((128, 128), 0.35), MORTAR), q(bsh * 0.8, BRICKW))
    s.rgb[bare] = bc[bare]
    s.rgb[S.inner_edge(bare)] = (s.rgb[S.inner_edge(bare)] * 0.55).astype(np.uint8)
    # the doorway: stone surround, a lintel, a lit rectangle with the door ajar
    s.paint(s.rect(34, 28, 94, 124), stone_blocks(s, s.rect(34, 28, 94, 124), 34, 28, 20, 11, 7907, light=0.5), STONEN, edge=0.5)
    inner = s.rect(44, 40, 84, 124)
    lit = 0.55 + 0.35 * np.clip((s.y - 40) / 84.0, 0, 1) - 0.25 * np.clip((s.x - 44) / 40.0, 0, 1) * 0.5 + (s.nz(4, 7908) - 0.5) * 0.12
    s.paint(inner, lit, ramp("#3a1e08", "#74440f", "#b4781c", "#e0aa40", "#ffe08a"), edge=0.5)
    # a desk edge and a coat stand seen inside, as dark shapes
    s.paint(s.rect(50, 96, 70, 124), 0.15, SOOT)
    s.paint(s.rect(50, 96, 70, 99), 0.3, OAK)
    s.paint(s.rect(52, 52, 55, 96), 0.12, SOOT)
    s.paint(s.line(53, 54, 47, 64, 2), 0.12, SOOT)
    # the leaf, hinged on the right and swung in: narrow, battered planks with a strap hinge and a lamp above
    leaf = s.poly([(84, 40), (84, 124), (68, 118), (68, 46)])
    ls = 0.45 + 0.12 * np.sin((s.y - 40) * 0.0) + (s.nz(3, 7909) - 0.5) * 0.3 + 0.2 * ((s.x - 68) % 5 == 0)
    s.paint(leaf, ls - 0.2 * ((s.x - 68) % 5 == 4), OAK, edge=0.45)
    for yy in (52, 100):
        s.paint(s.rect(68, yy, 84, yy + 3), 0.3, STEEL)
    for (bx, by) in ((74, 70), (78, 84), (72, 90), (79, 62)):
        s.solid(s.rect(bx, by, bx + 2, by + 2), "#0a0604")
    # light spilling onto the ground
    s.paint(s.poly([(44, 122), (84, 122), (104, 124), (30, 124)]), 0.6 + 0.2 * s.th, ramp("#3a1e08", "#74440f", "#b4781c"))
    # a blank brass plate on the wall beside it
    s.paint(s.rect(99, 58, 113, 74), 0.35 + 0.5 * ((s.x < 102) | (s.y < 61)) - 0.1 * (s.y > 71), BRASS, edge=0.5)
    for (px, py) in ((100, 59), (111, 59), (100, 72), (111, 72)):
        s.solid(s.rect(px, py, px + 1, py + 1), "#2a1a06")
    # a caged lamp over the door
    s.paint(s.ell(64, 22, 7, 5), 0.9, FIRE)
    s.paint(s.path([(57, 22), (64, 15), (71, 22)], 1.4) | s.path([(57, 22), (64, 29), (71, 22)], 1.4), 0.3, STEEL)
    # sandbags piled both sides, front rows last
    def bags(x_start, x_end, rows, seed):
        rr = R(seed)
        for ro in range(rows):
            yy = 117 - ro * 8
            nb = int((x_end - x_start - ro * 8) // 11)
            xs = x_start + ro * 4 + (ro % 2) * 3
            for b in range(nb):
                bx = xs + b * 11 + 5.5
                tone = 0.4 + rr.rand() * 0.3
                m = s.ell(bx, yy, 6.4, 4.6)
                s.paint(m, tone + 0.25 * np.clip(1 - np.hypot((s.x - bx + 2) / 6, (s.y - yy + 2) / 4.4), 0, 1) - 0.15 * (s.y > yy + 2) + (s.nz(2, seed + b) - 0.5) * 0.1, SAND, edge=0.5)
                s.paint(s.rect(bx - 5, yy - 0.5, bx + 5, yy + 0.5) & m, tone * 0.5, SAND)
    bags(2, 46, 4, 7910)
    bags(80, 126, 3, 7911)
    s.outline(0.5)
    return s.rgba()


def thing_jacket_blood():
    s = S()
    wood = ramp("#0c0704", "#1e1109", "#32200f", "#4e3217", "#6e4a22", "#94682e")
    # the chair: back posts with finials, the seat and four legs
    for (x0, x1) in ((30, 37), (91, 98)):
        s.paint(s.rect(x0, 14, x1, 100), s.hl(x0, x1, 0.45, 0.4), wood, edge=0.5)
        s.paint(s.ell((x0 + x1) / 2, 13, 4.5, 4), 0.6, wood, edge=0.5)
    s.paint(s.rect(28, 98, 100, 106), 0.5 + 0.25 * (s.y < 100) - 0.2 * (s.y > 103), wood, edge=0.5)
    for (x0, x1) in ((30, 38), (90, 98)):
        s.paint(s.rect(x0, 106, x1, 124), s.hl(x0, x1, 0.42, 0.35), wood, edge=0.5)
    s.paint(s.rect(38, 112, 90, 115), 0.4, wood, edge=0.5)
    # the jacket: body slumped over the back, two sleeves, a sheepskin collar
    body = s.poly([(36, 30), (92, 30), (100, 40), (98, 70), (100, 99), (64, 104), (28, 99), (30, 70), (28, 40)])
    fold = 0.5 + 0.13 * np.sin(s.x * 0.28 + s.nz(6, 7921) * 3) + 0.14 * np.sin((s.x + s.y * 0.4) * 0.16)
    lsh = fold + 0.2 * np.clip(1 - (s.x - 28) / 60.0, 0, 1) - 0.1 + (s.nz(3, 7922) - 0.5) * 0.16
    s.paint(body, lsh, LEATHERB, edge=0.5)
    sleeve_l = s.poly([(30, 38), (14, 48), (8, 84), (14, 106), (28, 104), (32, 64)])
    sleeve_r = s.poly([(98, 38), (114, 50), (120, 82), (114, 104), (100, 102), (96, 66)])
    s.paint(sleeve_l, lsh * 0.85 + 0.06 * np.sin(s.y * 0.5), LEATHERB, edge=0.5)
    s.paint(sleeve_r, lsh * 0.7 + 0.06 * np.sin(s.y * 0.5), LEATHERB, edge=0.5)
    s.paint(s.rect(10, 96, 31, 106) & sleeve_l, 0.3, ramp("#0a0806", "#2a2018", "#4a3a2a"), edge=0.5)  # knitted cuffs
    s.paint(s.rect(100, 94, 118, 104) & sleeve_r, 0.3, ramp("#0a0806", "#2a2018", "#4a3a2a"), edge=0.5)
    # zip, pockets, belt strap, epaulettes
    s.paint(s.rect(63, 46, 65, 100), 0.5 + 0.4 * ((s.y % 3) < 1), STEEL)
    for (x0, x1) in ((38, 56), (73, 91)):
        s.paint(s.rect(x0, 60, x1, 73), lsh * 0.9 + 0.12 * (s.y < 62), LEATHERB, edge=0.45)
        s.solid(s.rect((x0 + x1) // 2, 67, (x0 + x1) // 2 + 2, 69), "#c8a040")
    s.paint(s.rect(30, 84, 98, 90), lsh * 0.85 - 0.05, LEATHERB, edge=0.45)
    s.solid(s.rect(60, 85, 68, 89), "#a88a30")
    s.paint(s.poly([(36, 30), (50, 30), (50, 38), (34, 40)]), 0.3, LEATHERB, edge=0.5)
    s.paint(s.poly([(78, 30), (92, 30), (94, 40), (78, 38)]), 0.3, LEATHERB, edge=0.5)
    # the sheepskin collar, open at the neck
    s.paint(s.poly([(36, 24), (92, 24), (100, 36), (82, 46), (64, 52), (46, 46), (28, 36)]), 0.7 + (s.nz(2, 7923) - 0.5) * 0.3, CREAM, edge=0.6)
    s.paint(s.poly([(48, 30), (80, 30), (74, 44), (64, 50), (54, 44)]), 0.18, ramp("#0a0806", "#2a1c12", "#4a3424"))
    # the dark stains: stylised patches with drips, dithered edges
    stn = np.zeros((128, 128), bool)
    for (bx, by, br) in ((48, 76, 11), (84, 56, 7), (70, 96, 6), (20, 80, 6)):
        stn |= s.ell(bx, by, br, br * 0.9) & (s.nz(3, bx * by) > 0.25)
        stn |= s.rect(bx - 1, by, bx + 1, by + br + 8)
    stn &= (body | sleeve_l) & ~s.rect(56, 24, 80, 52)
    s.paint(stn, 0.15 + 0.35 * s.nz(2, 7924) + 0.1 * s.th, ramp("#0a0203", "#220608", "#46100e", "#6a1a14"))
    # the scarf trails from the collar over the seat to the floor
    scarf = s.path([(86, 40), (96, 54), (102, 74), (94, 92), (102, 108), (98, 122)], 8.0)
    s.paint(scarf, 0.62 + 0.22 * np.sin((s.y + s.x * 0.5) * 0.6) + (s.nz(2, 7925) - 0.5) * 0.2 - 0.12 * (s.x > 98), CLOTH, edge=0.55)
    s.paint(scarf & ((s.y % 14) < 3), 0.2, CLOTH)
    s.paint(scarf & (s.y > 110) & (s.nz(3, 7926) > 0.4), 0.2, ramp("#0a0203", "#220608", "#46100e"))
    s.outline(0.5)
    return s.rgba()


def thing_lamp_alarm():
    s = S()
    cx, cy, rb = 64, 74, 24
    # mount, short pipe and socket at the top
    s.paint(s.rect(40, 8, 88, 16), s.hl(40, 88, 0.5, 0.5), STEEL, edge=0.5)
    s.paint(s.rect(58, 16, 70, 34), s.hl(58, 70, 0.5, 0.6), STEEL, edge=0.5)
    s.paint(s.rect(50, 32, 78, 44), s.hl(50, 78, 0.5, 0.6), STEEL, edge=0.5)
    # the bulb: deep red, white-pink at the heart
    bulb = s.ell(cx, cy, rb, rb)
    d = np.clip(np.hypot(s.x - cx, s.y - cy) / rb, 0, 1)
    s.paint(bulb, 0.95 - 0.55 * d ** 1.3 + (s.nz(3, 7931) - 0.5) * 0.08, RED, edge=0.6)
    s.paint(s.ell(cx - 5, cy - 6, 7, 5) & bulb, 0.97, RED)
    # the cage: a ring top and bottom, meridians and bands, dark iron
    cage = np.zeros((128, 128), bool)
    for k in (0.42, 0.78):
        cage |= (s.ell(cx, cy, rb + 3, rb + 3) & ~s.ell(cx, cy, rb + 3, rb + 3) )
    outer = s.ell(cx, cy, rb + 3, rb + 3)
    cage |= outer & ~s.ell(cx, cy, rb + 1, rb + 1)
    for e in (0.36, 0.7):
        cage |= s.ell(cx, cy, (rb + 3) * e, rb + 3) & ~s.ell(cx, cy, (rb + 3) * e - 2, rb + 1) & outer
    cage |= s.rect(cx - 1, cy - rb - 2, cx + 1, cy + rb + 3) & outer
    for dyb in (-13, 0, 13):
        rxb = np.sqrt((rb + 3) ** 2 - dyb ** 2)
        cage |= s.rect(cx - rxb, cy + dyb - 1, cx + rxb, cy + dyb + 1) & outer
    s.paint(cage, 0.22 + 0.3 * (s.x < cx), STEEL)
    # base cup at the bottom of the cage
    s.paint(s.rect(52, cy + rb + 1, 76, cy + rb + 6), s.hl(52, 76, 0.5, 0.5), STEEL, edge=0.5)
    s.halo(cx, cy, 60, RED, 1.0, 1.35)
    s.outline(0.5)
    return s.rgba()


def thing_map_wall():
    s = S()
    paper = s.rect(8, 10, 120, 114)
    # the torn corner: bottom right comes away and a flap curls back
    tear = s.poly([(120, 114), (120, 90), (112, 96), (108, 104), (100, 108), (96, 114)])
    paper &= ~tear
    base = 0.62 + (s.nz(4, 8001) - 0.5) * 0.25 - 0.25 * grime_field(s, 8002) + 0.1 * (1 - (s.x - 8) / 112)
    s.paint(paper, base, PAPER, edge=0.5)
    # sea (hatched by little waves) and the coasts
    d1 = np.hypot(s.x - 8, s.y - 66) + 26 * (s.nz(14, 8003, 3) - 0.5)
    d2 = np.hypot(s.x - 122, s.y - 114) + 24 * (s.nz(14, 8004, 3) - 0.5)
    d3 = np.hypot(s.x - 84, s.y - 24) + 14 * (s.nz(8, 8005, 3) - 0.5)
    land = paper & ((d1 < 40) | (d2 < 40) | (d3 < 13))
    sea = paper & ~land
    wave = sea & ((s.y % 6) == 3) & (((s.x + (s.y // 6) * 3) % 8) < 3)
    SEAP = ramp("#26241c", "#4a4a3a", "#767660", "#a2a284", "#c0c0a0")
    s.paint(sea, base * 0.85, SEAP)
    s.paint(land, base * 1.05, PAPER)
    s.paint(wave, 0.82, SEAP)
    s.paint(land & ((s.x + s.y) % 5 == 0) & (s.nz(3, 8006) > 0.5), 0.35, PAPER)  # hill hatching
    ink = ramp("#0a0604", "#1e140c", "#3a2a1c")
    coast = (land & ~S.inner_edge(land)) ^ land
    coast = S.inner_edge(land) | (S.inner_edge(land) & False)
    s.paint(coast & paper, 0.2 + 0.2 * s.nz(2, 8007), ink)
    # a faint grid, a scale bar
    grid_m = paper & ~land & ((s.x - 8) % 28 == 0) & ((s.y % 3) < 1)
    s.paint(grid_m | (paper & ~land & ((s.y - 10) % 26 == 0) & ((s.x % 3) < 1)), 0.45, PAPER)
    # scribbles where names would be: wavy strokes, no letters
    r = R(8008)
    for (x0, y0, ln) in ((14, 58, 20), (14, 76, 14), (96, 94, 14), (74, 18, 12), (100, 104, 8)):
        pts = [(x0 + i * 2, y0 + 1.6 * np.sin(i * 1.3 + x0) + r.uniform(-0.8, 0.8)) for i in range(ln // 2)]
        s.paint(s.path(pts, 1.4) & paper, 0.25, ink)
    # the dotted route with an arrow head and two pins
    rt = [(30, 74), (44, 62), (58, 58), (70, 50), (82, 40), (88, 28)]
    for (a, b), (c, d) in zip(rt[:-1], rt[1:]):
        L = int(np.hypot(c - a, d - b) // 4) + 1
        for i in range(L):
            px, py = a + (c - a) * i / L, b + (d - b) * i / L
            s.solid(s.rect(px, py, px + 2, py + 2), "#8a1c1c")
    s.paint(s.poly([(88, 24), (84, 32), (92, 32)]), 0.4, RED)
    for (px, py) in ((30, 74), (86, 28)):
        s.paint(s.ell(px, py, 3.2, 3.2), 0.65 + 0.3 * (s.x < px), RED, edge=0.5)
        s.solid(s.rect(px - 1, py - 1, px, py), "#ffd0c0")
    # the loose corner: the underside shows lighter and a crease runs across
    flap = s.poly([(96, 114), (108, 104), (120, 90), (112, 88), (98, 98), (90, 108)])
    s.paint(flap & ~paper, 0.7 + (s.nz(3, 8009) - 0.5) * 0.2 - 0.2 * ((s.x + s.y) > 210), ramp("#4a3a22", "#8c7448", "#c4b078", "#e8dcaa"), edge=0.5)
    # tacks at the corners
    for (px, py) in ((12, 14), (116, 14), (12, 110)):
        s.paint(s.ell(px, py, 3, 3), 0.6 + 0.35 * (s.x < px), STEEL, edge=0.45)
    s.outline(0.5)
    return s.rgba()


def thing_medal_case():
    s = S()
    # the case: moulded top and plinth, a dark wood frame, velvet inside, glass in front
    s.paint(s.rect(4, 6, 124, 14), 0.5 + 0.3 * (s.y < 8) - 0.25 * (s.y > 11), OAK, edge=0.5)
    s.paint(s.rect(8, 14, 120, 108), s.hl(8, 120, 0.5, 0.2) + 0.08 * np.sin(s.x * 0.8 + s.nz(6, 8101) * 4), OAK, edge=0.5)
    inside = s.rect(15, 21, 113, 101)
    glow = np.clip(1 - np.hypot((s.x - 64) / 52, (s.y - 62) / 44), 0, 1)
    s.paint(inside, 0.2 + 0.55 * glow + (s.nz(2, 8102) - 0.5) * 0.12 + 0.05 * (((s.x + s.y) % 3) == 0), VELVET, edge=0.45)
    s.paint(s.rect(4, 108, 124, 118), 0.5 + 0.3 * (s.y < 110) - 0.25 * (s.y > 115), OAK, edge=0.5)
    s.paint(s.rect(10, 118, 24, 124) | s.rect(104, 118, 118, 124), 0.3, OAK, edge=0.5)
    # a little brass stand for the medal
    s.paint(s.rect(50, 96, 78, 101), 0.5 + 0.4 * (s.y < 97), BRASS, edge=0.5)
    s.paint(s.rect(62, 82, 66, 97), s.hl(62, 66, 0.55, 0.4), BRASS)
    # the ribbon: two straps in a V from the top of the case, striped in colour bars
    for (ax, bx) in ((46, 62), (82, 66)):
        ln = np.hypot(bx - ax, 50 - 21)
        ux, uy = (bx - ax) / ln, (50 - 21) / ln
        px_, py_ = -uy, ux
        t = (s.x - ax) * ux + (s.y - 21) * uy
        p = (s.x - ax) * px_ + (s.y - 21) * py_
        strap = s.poly([(ax + 7 * px_, 21 + 7 * py_), (ax - 7 * px_, 21 - 7 * py_), (bx - 7 * px_, 50 - 7 * py_), (bx + 7 * px_, 50 + 7 * py_)])
        band = np.floor((p + 7) / 14 * 7).astype(int)
        cols = np.array([0, 1, 1, 2, 1, 1, 0])[np.clip(band, 0, 6)]
        shd = np.where(cols == 0, 0.5, np.where(cols == 1, 0.88, 0.45)) + 0.1 * (1 - np.clip(t / 40, 0, 1)) - 0.08
        strap_rgb = np.where((cols == 0)[..., None], q(shd, ramp("#1a0406", "#4a0c12", "#7a1c22", "#a2323a")),
                             np.where((cols == 1)[..., None], q(shd, CREAM), q(shd, ramp("#06100a", "#102a1a", "#1e4a2c", "#2e6a40"))))
        s.rgb[strap] = strap_rgb[strap]
        s.a[strap] = 255
        s.rgb[S.inner_edge(strap)] = (s.rgb[S.inner_edge(strap)] * 0.5).astype(np.uint8)
    # the medal: a ring, an eight-point star in gold, a boss in the middle with rings
    s.paint(s.ell(64, 50, 4.5, 4.5) & ~s.ell(64, 50, 2, 2), 0.6, BRASS, edge=0.5)
    pts = []
    for i in range(16):
        ang = -np.pi / 2 + i * np.pi / 8
        rad = 26 if i % 2 == 0 else 15
        pts.append((64 + rad * np.cos(ang), 76 + rad * np.sin(ang)))
    star = s.poly(pts)
    dstar = np.hypot(s.x - 64, s.y - 76)
    sh = 0.55 + 0.3 * np.clip(1 - np.hypot(s.x - 54, s.y - 66) / 30, 0, 1) - 0.3 * np.clip((s.x - 64) / 30, 0, 1) * 0.6 + 0.1 * np.sin(np.arctan2(s.y - 76, s.x - 64) * 8)
    s.paint(star, sh, BRASS, edge=0.5)
    s.paint(s.ell(64, 76, 12, 12), 0.35 + 0.4 * np.clip(1 - np.hypot(s.x - 60, s.y - 72) / 14, 0, 1), BRASS, edge=0.5)
    s.paint(s.ell(64, 76, 8, 8), 0.65 - 0.3 * np.clip(1 - np.hypot(s.x - 62, s.y - 74) / 8, 0, 1) * -1, BRASS, edge=0.55)
    s.paint(s.ell(64, 76, 3, 3), 0.9, BRASS)
    # glints: a bright flash on the medal and diagonal streaks on the glass
    for (gx, gy) in ((56, 62), (57, 62), (56, 63), (50, 70), (51, 70)):
        s.solid(s.rect(gx, gy, gx + 1, gy + 1), "#fffaf0")
    streak = inside & ((((s.x + s.y * 0.9) % 40) < 4) & (s.x + s.y * 0.9 < 130)) & (s.th > 0.35)
    s.rgb[streak] = np.clip(s.rgb[streak].astype(np.float32) * 1.0 + 38, 0, 255).astype(np.uint8)
    s.outline(0.5)
    return s.rgba()


def thing_medkit():
    s = S()
    enamel = WHITE
    # the lid stands open behind: its inside has elastic loops holding a bottle and scissors
    lid = s.rect(28, 14, 100, 72)
    s.paint(lid, 0.72 + (s.nz(3, 8201) - 0.5) * 0.14 + 0.1 * (s.x < 34) - 0.14 * (s.x > 94), enamel, edge=0.5)
    s.paint(lid & ((s.x < 31) | (s.y < 17)), 0.9, enamel)
    for yy in (32, 52):
        s.paint(s.rect(34, yy, 94, yy + 3), 0.25 + 0.15 * (s.y < yy + 1), ramp("#0a0806", "#2a2018", "#4a3a2a"))
    s.paint(s.rect(40, 36, 50, 56), 0.35 + 0.4 * (s.x < 43), ramp("#1a0e04", "#4a2a0a", "#8a5a1c", "#b88a3c"), edge=0.5)  # an iodine bottle
    s.paint(s.rect(42, 33, 48, 37), 0.7, ramp("#10100e", "#6a6a64", "#b8b8b0"))
    s.paint(s.path([(64, 30), (74, 58)], 2.4) | s.path([(72, 30), (64, 58)], 2.4), 0.55, CHROME)
    s.paint(s.ell(64, 59, 3, 2) | s.ell(75, 59, 3, 2), 0.3, ramp("#10100e", "#2a2018", "#4a3a2a"))
    s.paint(s.rect(80, 38, 92, 52), 0.8, CREAM, edge=0.5)  # a pad of gauze
    # the case: white enamel with a plain grey cross, chipped at the corners, steel latches
    case = s.rect(18, 74, 110, 118)
    csh = 0.7 + (s.nz(3, 8202) - 0.5) * 0.16 + 0.12 * (s.x < 24) - 0.2 * (s.y > 112) - 0.1 * (s.x > 104)
    s.paint(case, csh, enamel, edge=0.5)
    s.paint(s.rect(18, 74, 110, 80), 0.25, ramp("#0a0806", "#1e1a14", "#3a342a"))  # the open compartment's dark edge
    chips = case & (((s.x < 24) | (s.x > 104)) & (s.nz(2, 8203) > 0.55) | ((s.y > 112) & (s.nz(2, 8204) > 0.5)))
    s.paint(chips, 0.25 + 0.2 * s.nz(2, 8205), ramp("#1a0e08", "#4a2a14", "#7a4a24"))
    cross = s.rect(55, 84, 73, 114) | s.rect(44, 94, 84, 104)
    s.paint(cross, 0.38 + 0.12 * s.nz(2, 8206) + 0.12 * (s.x < 58), ramp("#1c1b1a", "#3a3836", "#5a5754", "#7a7672"), edge=0.6)
    for lx in (22, 106):
        s.paint(s.rect(lx - 2, 86, lx + 3, 96), 0.45 + 0.4 * (s.x < lx), STEEL, edge=0.5)
    # contents sticking up over the lip: rolls of bandage and a tin
    for (rx, ry, rh) in ((30, 64, 14), (48, 66, 12), (86, 66, 12)):
        s.paint(s.rect(rx, ry, rx + 14, ry + rh), s.hl(rx, rx + 14, 0.7, 0.4), enamel, edge=0.5)
        s.paint(s.ell(rx + 7, ry, 7, 2.6), 0.8, enamel, edge=0.55)
        s.paint(s.ell(rx + 7, ry, 2.5, 1.2), 0.2, enamel)
    s.paint(s.rect(66, 66, 82, 78), 0.35 + 0.4 * (s.x < 70), STEEL, edge=0.5)
    # a bandage unrolled over the front and down to the floor, curling
    wav = 3 * np.sin((s.y - 76) * 0.22)
    strip = (s.y >= 76) & (s.y < 120) & (np.abs(s.x - (92 + wav)) < 4.5)
    s.paint(strip, 0.78 + 0.18 * (s.x < 91 + wav) - 0.15 * (s.x > 94 + wav), enamel, edge=0.55)
    s.paint(s.ell(96, 121, 10, 3), 0.85, enamel, edge=0.55)
    s.paint(s.ell(14, 116, 8, 7), 0.78 + 0.1 * (s.x < 12), enamel, edge=0.55)
    s.paint(s.ell(14, 116, 3, 3), 0.25, enamel)
    s.outline(0.5)
    return s.rgba()


TRAINB = ramp("#030102", "#0c0607", "#180d0c", "#2a1714", "#40241c", "#5a3424")
SMOKE = ramp("#0e0807", "#241412", "#3e2018", "#6a3020", "#a04a24", "#d8742c")
LAMPY = ramp("#3a2a08", "#8a6a18", "#d8b040", "#fff0b0", "#ffffff")
CURT = ramp("#0c0506", "#20090c", "#3a1216", "#561c1c", "#743028")


def rot_rect(s: S, cx, cy, w, h, ang):
    c, sn = np.cos(ang), np.sin(ang)
    pts = [(cx + (dx * c - dy * sn), cy + (dx * sn + dy * c)) for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    return s.poly(pts)


def thing_night_train():
    s = S(256, 128)
    rr = R(8301)
    # the viaduct: a long dark arcade, brick arches you can see through
    deck_y = 102
    arc = s.rect(0, deck_y, 256, 128)
    for k in range(9):
        bx = 16 + 32 * k
        arc &= ~(s.rect(bx - 11, 114, bx + 11, 128) | s.ell(bx, 114, 11, 11) & (s.y < 128))
    sh = 0.28 + (s.nz(3, 8302) - 0.5) * 0.3 + 0.12 * ((s.y - deck_y) % 7 == 0)
    s.paint(arc, sh, TRAINB, edge=0.5)
    s.paint(s.rect(0, deck_y - 3, 256, deck_y + 3), 0.38 + (s.nz(2, 8303) - 0.5) * 0.2, TRAINB)  # the parapet
    # wagons: low box shapes along the line, a little different each
    x = 4
    k = 0
    while x < 122:
        w = 38 if k % 2 == 0 else 34
        top = 68 if k % 2 == 0 else 72
        wag = s.rect(x, top, x + w, deck_y - 4) | (s.ell(x + w / 2, top + 3, w / 2, 5) & (s.y < top + 3))
        s.paint(wag, 0.22 + 0.1 * ((s.x - x) % 6 == 0) + (s.nz(2, 8310 + k) - 0.5) * 0.1, TRAINB, edge=0.5)
        s.paint(s.rect(x - 3, deck_y - 8, x + w + 3, deck_y - 4), 0.14, TRAINB)  # underframe
        for wx in (x + 7, x + w - 7):
            s.paint(s.ell(wx, deck_y - 5, 4, 4), 0.1, TRAINB, edge=0.7)
        if k % 2 == 1:
            s.paint(s.rect(x + 12, top + 8, x + 16, top + 13), 0.7, ramp("#3a2a08", "#8a6a18", "#d8b040"))  # one lit window
        x += w + 3
        k += 1
    # the tender, with a heap of coal
    s.paint(s.rect(126, 72, 160, deck_y - 4), 0.2, TRAINB, edge=0.5)
    s.paint(s.ell(143, 72, 16, 5) & (s.y < 74), 0.24 + 0.2 * s.nz(2, 8320), TRAINB)
    # the engine: boiler, smokebox, chimney, domes, cab
    s.paint(s.rect(176, 70, 238, 94), s.vl(70, 94, 0.5, 0.15) + (s.nz(3, 8321) - 0.5) * 0.12, TRAINB, edge=0.5)
    s.paint(s.rect(238, 72, 248, 94), 0.3, TRAINB, edge=0.5)  # smokebox front
    s.paint(s.rect(224, 56, 234, 72) | s.poly([(221, 54), (237, 54), (234, 60), (224, 60)]), s.hl(221, 237, 0.4, 0.3), TRAINB, edge=0.5)
    for dx in (192, 207):
        s.paint(s.ell(dx, 70, 6, 5) & (s.y < 71), 0.4, TRAINB, edge=0.5)
    s.paint(s.rect(160, 62, 190, 98), 0.18 + (s.nz(2, 8322) - 0.5) * 0.1, TRAINB, edge=0.5)  # the cab
    s.paint(s.rect(156, 56, 194, 63), 0.3, TRAINB, edge=0.5)  # its roof
    s.paint(s.rect(170, 68, 182, 78), 0.9, FIRE, edge=0.3)  # a lit window
    s.paint(s.rect(166, 90, 186, 97), 0.5 + 0.4 * s.nz(2, 8323), FIRE)  # firebox glow under the footplate
    s.paint(s.rect(172, 94, 244, 98), 0.15, TRAINB)  # running plate
    for wx in (190, 205, 220):
        s.paint(s.ell(wx, 95, 10, 10) & (s.y < deck_y - 3), 0.16, TRAINB, edge=0.7)
        s.paint(s.ell(wx, 95, 3, 3), 0.55, TRAINB)
    s.paint(s.line(190, 95, 220, 95, 2.0), 0.4, TRAINB)  # the coupling rod
    s.paint(s.ell(243, 98, 5, 5) & (s.y < deck_y - 3), 0.14, TRAINB, edge=0.7)
    # smoke from the chimney drifting back, lit red underneath by the fires
    pu = [(228, 50, 6), (214, 44, 8), (196, 38, 10), (176, 34, 12), (154, 31, 14), (130, 30, 15), (104, 31, 15), (80, 34, 14)]
    for (px, py, pr) in pu:
        m = s.ell(px, py, pr * 1.2, pr)
        lit = np.clip((s.y - py) / pr, -1, 1) * 0.5 + 0.5
        s.paint(m, 0.12 + 0.55 * lit ** 1.6 + (s.nz(3, px) - 0.5) * 0.2, SMOKE)
    # the big lamp: a hard bright core and a halo
    s.paint(s.ell(246, 82, 4.5, 4.5), 0.98, LAMPY, edge=None)
    s.paint(s.ell(246, 82, 7, 7) & ~s.ell(246, 82, 4.5, 4.5), 0.6, LAMPY)
    s.halo(246, 82, 34, LAMPY, 0.85, 1.4)
    # a fire-lit rim along the tops of the wagons and the deck
    top_e = (s.a > 0) & (np.roll(s.a, 1, 0) == 0)
    rim = top_e & (s.th > 0.3) & (s.x < 238)
    s.rgb[rim] = rgbof("#7a2a12")
    s.outline(0.6)
    return s.rgba()


def thing_rubble():
    s = S()
    hill = 54 * np.clip(np.sin(np.pi * np.clip((s.x - 5) / 117.0, 0, 1)), 0, 1) ** 0.9 + (s.nz(8, 8401, 3) - 0.5) * 14
    mound = (s.y >= 124 - np.maximum(hill, 0) - 3) & (s.y < 124) & (s.x >= 5) & (s.x < 123)
    mound &= s.y >= 124 - hill * 1.0 - 3
    s.paint(mound, 0.3 + 0.35 * s.nz(3, 8402) + 0.1 * (1 - (s.x - 5) / 118), ramp("#0c0908", "#1e1814", "#352c24", "#4e4034", "#6a584a"), edge=0.5)
    rr = R(8403)
    # fallen bricks, tilted every way, back to front
    for k in range(70):
        px = rr.uniform(10, 118)
        py = rr.uniform(70, 122)
        if not mound[int(py), int(px)]:
            continue
        ang = rr.uniform(0, np.pi)
        m = rot_rect(s, px, py, 11, 5.5, ang) & mound
        tone = 0.3 + rr.rand() * 0.45
        s.paint(m, tone + 0.15 * (s.y < py) * 0 + (s.nz(2, k) - 0.5) * 0.12, BRICKW, edge=0.5)
    # lumps of pale plaster and a few charred sticks
    for k in range(18):
        px, py = rr.uniform(12, 116), rr.uniform(80, 120)
        if not mound[int(py), int(px)]:
            continue
        m = s.poly([(px + rr.uniform(-6, -2), py + rr.uniform(-4, 0)), (px + rr.uniform(2, 7), py + rr.uniform(-4, 0)), (px + rr.uniform(3, 8), py + rr.uniform(2, 5)), (px + rr.uniform(-6, -2), py + rr.uniform(2, 5))]) & mound
        s.paint(m, 0.45 + rr.rand() * 0.4, GREYST, edge=0.55)
    for k in range(8):
        px, py = rr.uniform(14, 112), rr.uniform(84, 118)
        a = rr.uniform(-0.6, 0.6)
        m = s.line(px, py, px + 14 * np.cos(a), py + 14 * np.sin(a), 2.2) & mound
        s.paint(m, 0.25 + 0.2 * rr.rand(), ramp("#050302", "#120a06", "#241408", "#3c2410"), edge=0.6)
    # dust on top
    s.paint(mound & (s.nz(2, 8404, 2) > 0.8) & (s.y < 100), 0.55, GREYST)
    # a bent lamp bracket standing out of the pile: stem, a curled arm, a broken holder and a dangling wire
    iron = ramp("#06050a", "#14121a", "#26242c", "#3e3a44", "#605a64")
    stem = s.path([(34, 108), (33, 80), (35, 54), (40, 36), (52, 26), (68, 26), (78, 34), (80, 44)], 4.4)
    s.paint(stem, s.hl(28, 84, 0.5, 0.5) + 0.2 * (s.nz(2, 8405) - 0.5), iron, edge=0.45)
    s.paint(s.path([(40, 70), (30, 66), (26, 74), (32, 80)], 2.6), 0.5, iron, edge=0.45)  # a scroll
    s.paint(s.poly([(74, 36), (86, 36), (84, 52), (76, 52)]), 0.25 + 0.3 * (s.x < 79), iron, edge=0.5)  # the empty socket
    s.paint(s.rect(75, 52, 85, 55), 0.5, BRASS, edge=0.5)
    s.paint(s.path([(80, 55), (84, 62), (78, 72), (86, 80)], 1.4), 0.3, ramp("#06050a", "#241810", "#46301c"))
    s.paint(s.rect(54, 22, 62, 27), 0.3, iron)
    s.outline(0.5)
    return s.rgba()


def thing_staff_car():
    s = S(256, 128)
    glass = ramp("#0a0806", "#1a1410", "#34281c", "#5c4a34", "#8a7456")
    # far wheel peeking out under the front, then the body
    s.paint(s.ell(232, 106, 7, 13), 0.1, SOOT, edge=0.7)
    flank = s.poly([(12, 74), (14, 100), (22, 106), (166, 114), (172, 66), (100, 68), (30, 70)])
    for (wx, wy, rx, ry) in ((50, 108, 17, 18), (146, 113, 18, 19)):
        flank &= ~s.ell(wx, wy - 2, rx + 3, ry + 2) | (s.y > wy + 2)
    ol = 0.5 + 0.28 * np.clip(1 - (s.y - 66) / 30.0, 0, 1) + (s.nz(4, 8501) - 0.5) * 0.12 - 0.1 * (s.x < 30)
    s.paint(flank, ol, OLIVE, edge=0.5)
    # a pressed swage line along the flank and the door seams, handles
    s.paint(s.path([(16, 80), (168, 76)], 1.2), 0.62, OLIVE)
    for (dx0, dx1) in ((24, 24),):
        pass
    for xx, y0, y1 in ((98, 68, 108), (150, 66, 112), (50, 70, 90)):
        s.paint(s.line(xx, y0, xx + 1, y1, 1.1), 0.06, OLIVE)
    for hx, hy in ((90, 82), (142, 80)):
        s.paint(s.rect(hx, hy, hx + 7, hy + 2), 0.85, CHROME)
    # running board and the sill
    s.paint(s.poly([(20, 104), (166, 112), (166, 116), (20, 108)]), 0.12 + 0.3 * (s.y < 108), OLIVE, edge=0.5)
    # the cabin: pillars, roof, windows with a dusty glint
    cab = s.poly([(46, 70), (60, 36), (72, 26), (122, 23), (148, 30), (160, 52), (170, 66)])
    s.paint(cab, ol * 0.95, OLIVE, edge=0.5)
    for pts in ([(60, 62), (66, 40), (76, 32), (94, 31), (94, 63)], [(104, 63), (104, 31), (128, 30), (148, 40), (156, 63)]):
        w = s.poly(pts)
        gl = 0.25 + 0.25 * np.clip(1 - (s.y - 30) / 34, 0, 1) + 0.15 * (((s.x + s.y * 1.6) % 30) < 5)
        s.paint(w, gl, glass, edge=0.45)
    # the bonnet: a wedge up to the windscreen, then the screen
    bonnet = s.poly([(156, 50), (192, 50), (246, 64), (172, 64)])
    s.paint(bonnet, 0.62 + 0.2 * (1 - (s.x - 150) / 96.0) + (s.nz(3, 8502) - 0.5) * 0.1, OLIVE, edge=0.5)
    s.paint(s.path([(158, 58), (200, 57), (232, 64)], 1.2), 0.3, OLIVE)  # the centre crease
    s.paint(s.poly([(72, 26), (122, 22), (152, 27), (178, 32), (152, 32), (122, 25)]), 0.78, OLIVE, edge=0.5)  # the roof, seen from a little above
    screen = s.poly([(150, 32), (186, 35), (192, 50), (158, 50)])
    s.paint(screen, 0.3 + 0.3 * np.clip(1 - (s.y - 30) / 20, 0, 1) + 0.15 * (((s.x + s.y * 1.6) % 24) < 4), glass, edge=0.45)
    s.paint(s.line(170, 33, 175, 50, 1.2), 0.1, OLIVE)  # screen centre bar
    # the front face: panel, grille in chrome slats, lamps on the wings, bumper
    front = s.poly([(172, 64), (246, 64), (246, 104), (172, 112)])
    s.paint(front, 0.5 + 0.2 * (1 - (s.x - 172) / 74.0) + (s.nz(3, 8503) - 0.5) * 0.12, OLIVE, edge=0.5)
    grille = s.poly([(190, 70), (224, 71), (224, 100), (190, 102)])
    s.paint(grille, 0.08, SOOT, edge=0.6)
    for k in range(7):
        gx = 193 + k * 4.6
        s.paint(s.rect(gx, 72, gx + 2, 100) & grille, 0.35 + 0.3 * (k % 2), CHROME)
    s.paint(grille & ((s.y - 71) % 8 < 1.2), 0.9, CHROME)
    s.paint(s.path([(188, 69), (225, 70), (225, 102), (188, 104)], 1.6, closed=True) & (s.x > 0), 0.8, CHROME)
    s.paint(s.ell(206, 66, 10, 3), 0.7, CHROME, edge=0.5)  # the radiator cap
    for (lx, ly, lr) in ((181, 76, 9), (237, 78, 7)):
        s.paint(s.ell(lx, ly, lr + 2, lr + 2), 0.3, CHROME, edge=0.5)
        s.paint(s.ell(lx, ly, lr, lr), 0.5 + 0.5 * np.clip(1 - np.hypot(s.x - lx + 3, s.y - ly + 3) / (lr * 1.4), 0, 1), ramp("#38342a", "#8a8472", "#d8d2bc", "#fffaf0"), edge=0.5)
        s.solid(s.rect(lx - 4, ly - 4, lx - 2, ly - 2), "#ffffff")
    bumper = s.poly([(166, 106), (248, 98), (248, 105), (168, 118)])
    s.paint(bumper, 0.5 + 0.4 * (s.y < 110) - 0.2 * (s.y > 114), CHROME, edge=0.5)
    for ox in (178, 238):
        s.paint(s.rect(ox, 104, ox + 5, 118), 0.55, CHROME, edge=0.5)
    # the near wheels: tyre, hub, a hubcap
    for (wx, wy, rx, ry) in ((50, 108, 16, 17), (146, 113, 17, 18)):
        s.paint(s.ell(wx, wy, rx, ry), 0.12 + 0.1 * (s.x < wx), SOOT, edge=0.7)
        s.paint(s.ell(wx, wy, rx * 0.55, ry * 0.55), 0.35 + 0.3 * np.clip(1 - np.hypot(s.x - wx + 3, s.y - wy + 3) / 12, 0, 1), STEEL, edge=0.5)
        s.paint(s.ell(wx, wy, 3, 3), 0.3, CHROME)
    # the dented near wing: a crumple, scratches and bare metal
    dent = s.poly([(138, 78), (168, 74), (170, 100), (150, 104), (140, 92)])
    s.paint(dent & (s.nz(3, 8504) > 0.35), 0.2 + 0.4 * (s.nz(2, 8505)), OLIVE)
    s.paint(s.path([(142, 82), (156, 88), (166, 84)], 1.2) | s.path([(146, 94), (160, 90)], 1.2), 0.06, OLIVE)
    s.paint(s.path([(150, 84), (153, 92)], 1.0), 0.9, STEEL)
    # dust: the lower half and the wheel arches are sand-coloured
    dust = (s.a > 0) & (s.y > 86) & (s.nz(5, 8506) > 0.4) & (s.th * 1.2 > 0.35 + (112 - s.y) / 30.0)
    s.rgb[dust] = (s.rgb[dust].astype(np.float32) * 0.45 + np.array([160, 140, 98], np.float32) * 0.55).astype(np.uint8)
    s.outline(0.5)
    return s.rgba()


def thing_street_lamp():
    s = S()
    iron = ramp("#06050a", "#14121a", "#26242c", "#3e3a44", "#605a64", "#86807c")
    # the post: a tall fluted column on a stepped base with collars
    s.paint(s.rect(60, 54, 68, 108), s.hl(60, 68, 0.5, 0.6) + 0.06 * np.sin(s.x * 3), iron, edge=0.45)
    s.paint(s.poly([(52, 124), (76, 124), (72, 102), (56, 102)]), s.hl(52, 76, 0.45, 0.5), iron, edge=0.45)
    s.paint(s.rect(48, 118, 80, 124), s.hl(48, 80, 0.5, 0.4), iron, edge=0.45)
    s.paint(s.ell(64, 101, 9, 3), 0.65, iron, edge=0.45)
    for cy in (58, 82):
        s.paint(s.rect(57, cy, 71, cy + 4), s.hl(57, 71, 0.55, 0.5), iron, edge=0.45)
    # scrolled arms under the lantern
    for sgn in (-1, 1):
        s.paint(s.path([(64 + sgn * 3, 74), (64 + sgn * 12, 66), (64 + sgn * 16, 56), (64 + sgn * 10, 52)], 2.6), 0.45 + 0.15 * (sgn < 0), iron, edge=0.45)
        s.paint(s.ell(64 + sgn * 9, 52, 3.5, 3.5) & ~s.ell(64 + sgn * 9, 52, 1.6, 1.6), 0.5, iron)
    # the lantern: a hipped cap, a finial, four glass panes in an iron frame, a lower cup
    s.paint(s.poly([(44, 24), (64, 8), (84, 24)]), s.hl(44, 84, 0.45, 0.5), iron, edge=0.45)
    s.paint(s.rect(42, 22, 86, 27), s.hl(42, 86, 0.5, 0.5), iron, edge=0.45)
    s.paint(s.ell(64, 6, 3, 3) | s.rect(63, 3, 65, 9), 0.7, iron, edge=0.45)
    gl = s.poly([(48, 27), (80, 27), (76, 52), (52, 52)])
    heat = np.clip(1 - np.hypot((s.x - 64) / 18, (s.y - 40) / 16), 0, 1)
    s.paint(gl, 0.25 + 0.65 * heat + (s.nz(3, 8601) - 0.5) * 0.1, ramp("#241408", "#4a2a0c", "#9a6a22", "#e0a850", "#fff0b0"), edge=0.5)
    s.paint(s.line(64, 27, 64, 52, 2), 0.35, iron)
    s.paint(s.line(56, 27, 58, 52, 1.4) | s.line(72, 27, 70, 52, 1.4), 0.4, iron)
    # cracks across the glass and a missing corner
    s.paint(s.path([(56, 33), (62, 38), (59, 44), (64, 49)], 1.0) | s.path([(62, 38), (71, 36), (75, 42)], 1.0), 0.12, SOOT)
    s.paint(s.poly([(70, 44), (77, 46), (76, 52), (68, 52)]), 0.06, SOOT)
    s.paint(s.poly([(52, 52), (76, 52), (70, 58), (58, 58)]), s.hl(52, 76, 0.5, 0.5), iron, edge=0.45)
    s.halo(64, 40, 44, ramp("#2a1408", "#5a3410", "#a06a24", "#e0a850"), 0.5, 1.7, ry=34)
    s.outline(0.5)
    return s.rgba()


def thing_washing_line():
    s = S()
    xs = np.arange(128)
    liney = 5 + 9 * np.sin(np.pi * xs / 127.0) ** 1.2   # the cord sags in the middle
    ly = liney[s.x.astype(int)]
    cord = np.abs(s.y - ly) < 1.1
    s.paint(cord, 0.2 + 0.3 * (s.y < ly), SOOT)
    hang = (s.y >= ly - 1)

    def piece(mask, base, ramp_=CLOTH, fold=0.35, ph=0.0, seed=0):
        sh = base + 0.16 * np.sin((s.x + ph) * fold) * (1 - 0.4 * np.clip((s.y - ly) / 60.0, 0, 1)) + (s.nz(3, seed) - 0.5) * 0.2
        sh = sh - 0.12 * np.clip((s.y - ly) / 80.0, 0, 1)
        s.paint(mask & hang, sh, ramp_, edge=0.55)

    wv = lambda a, f, p: a * np.sin(s.x * f + p)
    # a big sheet, cream
    piece(s.rect(4, 0, 36, 128) & (s.y < 76 + wv(3, 0.5, 1.0)) & ~s.poly([(24, 50), (30, 46), (33, 60), (27, 62)]), 0.72, CLOTH, 0.5, 0, 9001)
    # a shirt hung by its shoulders: body, two sleeves, a collar, in a darker stripe
    SHIRT = ramp("#140c06", "#32200f", "#583c1c", "#7c5a2c", "#a07e42")
    shirt = s.rect(46, 0, 68, 128) & (s.y < ly + 46 + wv(1.5, 0.9, 0.3))
    piece(shirt, 0.5, SHIRT, 0.6, 3, 9002)
    s.paint(shirt & hang & ((s.x - 46) % 6 < 2) & (s.y > ly + 4), 0.72, SHIRT)
    s.paint(s.poly([(46, liney[46] + 1), (38, liney[40] + 4), (36, liney[40] + 40), (43, liney[40] + 42), (47, liney[46] + 22)]), 0.42 + 0.2 * (s.x < 40), SHIRT, edge=0.55)
    s.paint(s.poly([(68, liney[68] + 1), (76, liney[74] + 4), (78, liney[74] + 38), (71, liney[74] + 40), (67, liney[68] + 22)]), 0.34 + 0.2 * (s.x < 73), SHIRT, edge=0.55)
    s.paint(s.poly([(52, liney[52] + 1), (57, liney[57] + 10), (62, liney[62] + 1)]), 0.1, SHIRT)
    for by in (22, 30, 38):
        s.solid(s.rect(56, liney[57] + by - 4, 58, liney[57] + by - 2), "#d8caa0")
    # trousers pegged by the waist: two legs with a gap
    tr = (s.rect(82, 0, 90, 128) | s.rect(92, 0, 100, 128)) & (s.y < ly + 54 + wv(1.0, 1.3, 0))
    piece(tr | s.rect(82, 0, 100, 128) & (s.y < ly + 12), 0.3, ramp("#0e0a08", "#241a14", "#3e2e22", "#5e4a36"), 0.8, 0, 9003)
    # a second sheet at the right edge and small things: a sock, a cloth
    piece(s.rect(108, 0, 128, 128) & (s.y < 98 + wv(3, 0.6, 2.0)), 0.62, CLOTH, 0.45, 5, 9004)
    piece(s.rect(102, 0, 106, 128) & (s.y < ly + 22), 0.5, CLOTH, 0.9, 0, 9005)
    # pegs where the cloth meets the cord
    for px in (8, 32, 48, 64, 85, 96, 109, 124):
        py = int(liney[min(px, 127)])
        s.paint(s.rect(px, py - 2, px + 2, py + 5), 0.5, OAK, edge=0.6)
    s.outline(0.5)
    return s.rgba()


def thing_window_dusk():
    s = S()
    win = s.rect(30, 20, 98, 112)
    # the view: amber dusk low, brown-grey above, one huge column of smoke, rooftops
    yy = np.clip((s.y - 20) / 88.0, 0, 1)
    sky = 0.1 + 0.8 * yy ** 1.5 + 0.12 * np.exp(-((s.x - 44) / 18) ** 2) * yy + (s.nz(12, 9101) - 0.5) * 0.1
    s.paint(win, sky, SKYD)
    cx = 72 + (96 - s.y) * 0.12 + 3 * np.sin(s.y * 0.12)
    col = win & (np.abs(s.x - cx) < 4 + (96 - s.y) * 0.1 * (s.nz(4, 9102) * 0.6 + 0.7)) & (s.y < 98)
    s.paint(col & (s.nz(2, 9103) > 0.18), 0.1 + 0.28 * s.nz(3, 9104) + 0.2 * (s.y > 80), ramp("#1c1210", "#32221c", "#503a2c", "#7a5238"))
    hts = R(9105).randint(4, 18, 40)
    roofs = win & (s.y >= 100 - hts[np.clip(((s.x - 30) / 2).astype(int), 0, 39)] * 0.7)
    s.solid(roofs, "#120d0a")
    s.solid(roofs & (s.nz(1.5, 9106, 2) > 0.8) & (s.y > 96), "#d08a3a")
    # frame, mullions, sill
    fr = ramp("#0a0603", "#1a0f07", "#2e1b0c", "#4a2d14", "#6a4420")
    s.paint(s.rect(26, 16, 102, 20) | s.rect(26, 112, 102, 117) | s.rect(26, 16, 31, 117) | s.rect(97, 16, 102, 117), 0.45 + 0.3 * ((s.x < 29) | (s.y < 18)), fr, edge=0.5)
    s.paint(s.rect(62, 20, 66, 112) | s.rect(31, 50, 97, 54) | s.rect(31, 80, 97, 84), 0.4 + 0.3 * ((s.x < 64) & (s.y < 52)), fr, edge=0.5)
    # glints on the panes
    for (gx, gy) in ((36, 26), (70, 26), (36, 58), (70, 58)):
        s.paint(s.line(gx, gy + 14, gx + 12, gy, 1.2), 0.6, SKYD) if False else None
        gm = s.line(gx, gy + 14, gx + 10, gy, 1.1) & win & (s.th > 0.2)
        s.rgb[gm] = np.clip(s.rgb[gm].astype(np.float32) + 46, 0, 255).astype(np.uint8)
    s.paint(s.rect(22, 112, 106, 120), 0.55 + 0.3 * (s.y < 114) - 0.2 * (s.y > 117), STONEN, edge=0.5)
    # the pelmet and the heavy velvet drapes tied back, a tassel hanging
    def drape(sign):
        xe = 4 if sign < 0 else 124
        edge_x = np.where(s.y < 78, 36 - (s.y - 14) * 0.13, 25 + (s.y - 78) * 0.25)
        if sign < 0:
            m = (s.x >= 4) & (s.x <= edge_x) & (s.y >= 14) & (s.y < 124)
        else:
            m = (s.x <= 124) & (s.x >= 127 - edge_x) & (s.y >= 14) & (s.y < 124)
        folds = np.sin((s.x - 4) * 0.62 + 0.4 * np.sin(s.y * 0.05)) * 0.5 + 0.5
        sh = 0.3 + 0.38 * folds + (0.1 if sign < 0 else -0.08) + (s.nz(3, 9110 + sign) - 0.5) * 0.1
        sh -= 0.2 * (np.abs(s.y - 78) < 3) * 0
        s.paint(m, sh, CURT, edge=0.5)
        tx = 22 if sign < 0 else 105
        s.paint(s.rect(tx - 7, 76, tx + 7, 81) & m, 0.4 + 0.5 * (s.y < 78), BRASS, edge=0.5)
        s.paint(s.rect(tx - 1, 81, tx + 1, 90) | s.ell(tx, 93, 3, 4), 0.55, BRASS, edge=0.5)
    drape(-1)
    drape(1)
    pel = s.rect(4, 4, 124, 20)
    pel_edge = 20 + 4 * np.sin((s.x - 4) * 0.52)
    s.paint(pel & (s.y <= pel_edge), 0.38 + 0.3 * (np.sin(s.x * 0.62) * 0.5 + 0.5) + 0.2 * (s.y < 7), CURT, edge=0.5)
    s.paint(s.rect(4, 4, 124, 7), 0.7, BRASS, edge=0.5)
    s.outline(0.5)
    return s.rgba()


DRAW = {k: v for k, v in list(globals().items()) if (k.startswith("thing_") or k.split("_")[0] in ("wall", "floor", "ceil", "sky")) and callable(v)}
