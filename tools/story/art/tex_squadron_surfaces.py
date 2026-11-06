"""The Mission Count's surfaces and skies, redrawn for the art style guide (docs/art/STYLE_GUIDE.md sections 2, 4 and 7; package W7).

Every surface is a 128 px tile of 1.0 to 1.3 m (98 to 128 texels per metre: `check_assets` caps a tile at 128 px, so the density comes from the short repeat),
drawn with ordered dither through a small ramp that has a real dark and a real light (the Squadron keeps its period colours, khaki, olive drab, brick, sea grey, lamp yellow,
but the ramps run from a lifted shadow to a light, so the picture has range without any filter). One-off things the old 64 px tiles carried (the bulb rose, the ring, the tent's
brown stain, the dado) are stage billboards now (`thing_*` in the maps), not repeats.

`DRAW` here replaces the same ids of the older modules (tex_squadron.registry lets this module win). Skies are 256 x 64 strips that wrap at infinity (SKY_TEXELS_AROUND 1024: the strip
repeats four times round the horizon), horizon row 48; the small pixel clusters (a low sun, searchlights, flak, balloons, a skyline) are drawn at one or two texels.
Deterministic: seeded generators only.
"""
from __future__ import annotations

import numpy as np

from .pixeltex import BAYER8, grid, hexc, noise, quantise, ramp

N = 128


def _R(seed: int) -> np.random.RandomState:
    return np.random.RandomState(seed)


def _q(sh, pal, dither: float = 0.7) -> np.ndarray:
    return quantise(np.clip(sh, 0, 1).astype(np.float32), pal, dither)


def _col(rgb, mask, hexs: str):
    rgb[np.asarray(mask, bool)] = (hexc(hexs) * 255 + 0.5).astype(np.uint8)
    return rgb


def _fine(n: int, seed: int) -> np.ndarray:
    return (_R(seed).rand(n, n).astype(np.float32) - 0.5)


def _stretch(n: int, sx: float, sy: float, seed: int, oct_: int = 2) -> np.ndarray:
    """Tileable anisotropic grain: noise sampled with its axes scaled (long streaks along x when sx > sy)."""
    base = noise(n, 8, seed, oct_)
    x, y = grid(n)
    xi = (x * sx).astype(int) % n
    yi = (y * sy).astype(int) % n
    return base[yi, xi]


def _blocks(n: int, rows: int, avg_w: float, seed: int, mortar: int = 2, jitter: float = 0.4, stagger: bool = True):
    """Courses of blocks of varied width, tileable: dict(tone, mort, hi, lo, bid)."""
    rng = _R(seed)
    x, y = grid(n)
    rowh = n // rows
    tone = np.zeros((n, n), np.float32)
    mort = np.zeros((n, n), bool)
    hi = np.zeros((n, n), bool)
    lo = np.zeros((n, n), bool)
    bid = np.zeros((n, n), np.int32)
    lxm = np.zeros((n, n), np.int32)
    wm = np.ones((n, n), np.int32)
    lym = np.zeros((n, n), np.int32)
    k = max(2, int(round(n / avg_w)))
    nid = 0
    for r in range(rows):
        cuts = (np.arange(k) * n / k + rng.uniform(-jitter, jitter, k) * n / k + (n / k / 2 if (stagger and r % 2) else 0)).astype(int) % n
        cuts = np.unique(np.sort(cuts))
        b = (cuts - cuts[0]) % n
        xs = (np.arange(n) - cuts[0]) % n
        seg = np.searchsorted(b, xs, side="right") - 1
        start = b[seg]
        end = np.append(b[1:], n)[seg]
        lx = xs - start
        w = end - start
        t = rng.rand(len(b)).astype(np.float32)
        ys = np.arange(r * rowh, (r + 1) * rowh)
        ly = (ys - r * rowh)[:, None]
        sl = slice(r * rowh, (r + 1) * rowh)
        m = (lx[None, :] < mortar) | (ly < mortar)
        mort[sl] = m
        hi[sl] = ((lx[None, :] == mortar) | (ly == mortar)) & ~m
        lo[sl] = ((lx[None, :] == (w[None, :] - 1)) | (ly == rowh - 1)) & ~m
        tone[sl] = t[seg][None, :]
        bid[sl] = (nid + seg)[None, :]
        lxm[sl] = lx[None, :]
        wm[sl] = w[None, :]
        lym[sl] = ly
        nid += len(b)
    return {"tone": tone, "mort": mort, "hi": hi, "lo": lo, "bid": bid, "lx": lxm, "w": wm, "ly": lym, "rowh": rowh}


def _shade_blocks(bl, base: float, spread: float, seed: int, grain: float = 0.12) -> np.ndarray:
    n = bl["tone"].shape[0]
    sh = base + spread * (bl["tone"] - 0.5) + grain * (noise(n, 6, seed, 3) - 0.5) * 2
    sh = sh + 0.14 * bl["hi"] - 0.16 * bl["lo"]
    return np.where(bl["mort"], 0.04, sh)


def _speck(n: int, density: float, seed: int) -> np.ndarray:
    return _R(seed).rand(n, n) < density


def _blob(n: int, cx, cy, rx, ry) -> np.ndarray:
    x, y = grid(n)
    dx = (x - cx + n / 2) % n - n / 2
    dy = (y - cy + n / 2) % n - n / 2
    return (dx / rx) ** 2 + (dy / ry) ** 2 < 1


def _crack(n: int, seed: int, length: int = 40, x0=None, y0=None) -> np.ndarray:
    rng = _R(seed)
    m = np.zeros((n, n), bool)
    x = float(rng.randint(n) if x0 is None else x0)
    y = float(rng.randint(n) if y0 is None else y0)
    a = rng.uniform(0, 6.28)
    for _ in range(length):
        m[int(y) % n, int(x) % n] = True
        a += rng.uniform(-0.6, 0.6)
        x += np.cos(a)
        y += np.sin(a)
    return m


# ---- palettes (dark to light): lifted shadows, a real light --------------------------------------------------------------------------------------
HUT = ramp("#2c2216", "#4a3b26", "#6c5a38", "#90794a", "#b39a64", "#d3bd84", "#ecdca6")
BOARD = ramp("#241a10", "#3e2e1b", "#5e4829", "#7e6439", "#a0824c", "#c1a26a", "#dcc38c")
BEAM = ramp("#120c08", "#22160d", "#38271a", "#52392a", "#6c4d36")
CANV = ramp("#3c3426", "#5c503a", "#7e6f50", "#a08e68", "#c0ad84", "#dccba0", "#eee0b8")
PLAS = ramp("#463c24", "#665932", "#8a7a46", "#ad9a5c", "#cbb878", "#e2d090")
BRICKC = ramp("#2a1610", "#4e2a1e", "#74402c", "#98583c", "#b9774e")
CORR = ramp("#14170f", "#272a1b", "#3c4128", "#555a38", "#727648", "#92966a")
ORNG = ramp("#4a2410", "#74401c", "#9c5a2a", "#c07838", "#dc9a52", "#f0be7c")
BAGS = ramp("#3a2e1c", "#5c4a2c", "#80693e", "#a58a54", "#c8aa6c", "#e4c98c")
DUST = ramp("#4e2a14", "#7a4522", "#a2602e", "#c27c40", "#dc9a58", "#eebc80")
CONC = ramp("#2e2e2a", "#46453f", "#625f55", "#807b6d", "#a09a86", "#bfb89e")
LINO_C = ramp("#4a4228", "#6c6240", "#948860", "#b8aa7c", "#d8c99a", "#ece0b4")
LINO_G = ramp("#122418", "#1e3a26", "#2c5236", "#3e6c48", "#588a5c")
TREAD = ramp("#12140f", "#22261f", "#363c33", "#515a4e", "#6f7a6c", "#929c8a")
BOMB = ramp("#09110c", "#14231a", "#223a2a", "#355540", "#4e7556", "#74a074")
RIVET = ramp("#0e1812", "#1c3022", "#2e4c36", "#486c4c", "#6c9a6c")
OCHRE = ramp("#3a2c20", "#5e4834", "#846a4a", "#a98c64", "#c9ac80", "#e4cc9e")
SOOT = ramp("#0e0908", "#1e1412", "#34231e", "#523529", "#74503c", "#98705a")
OAK = ramp("#1a0f08", "#31200f", "#4c3216", "#6c4a22", "#8e6630", "#b48a48")
WINE = ramp("#240c10", "#42161c", "#63242b", "#85363c", "#a7504e", "#c8786a")
SETT = ramp("#2a2019", "#473a2c", "#675642", "#8a7658", "#ac9774", "#cbb894")
RUBB = ramp("#241c18", "#403329", "#5f4f40", "#80694f", "#a28866", "#c2a883")
WETSTONE = ramp("#0c1624", "#16273c", "#243d58", "#365876", "#4f7694", "#76a0b6")
WEED = ramp("#102418", "#1c3e26", "#2c5c36", "#42804a", "#68a860")
SHED = ramp("#0c1a30", "#16294a", "#243f68", "#38598a", "#5479a8", "#7c9fc4")
CELLG = ramp("#12161a", "#212a30", "#364249", "#4f5e66", "#6f808a", "#98a8b0")
SANDC = ramp("#4a3418", "#6c4e28", "#947038", "#bc9a4e", "#dcc072", "#f6e8ae")
MARR = ramp("#3e5622", "#5e7a2c", "#84a43c", "#b0cc62")
QUAYC = ramp("#0e1620", "#1a2634", "#2c3d50", "#445a72", "#62809a", "#88a8bc")


# ---- generic painters ---------------------------------------------------------------------------------------------------------------------------

def _planks(n, count, vertical, pal, seed, gap_col, tone_spread=0.22, joints=True, nails=True, peel=0.0, base=0.55, grain=0.16):
    x, y = grid(n)
    a, b = (x, y) if vertical else (y, x)  # a runs across the planks, b along them
    pw = n / count
    pid = np.floor(a / pw).astype(int)
    la = a - pid * pw
    rng = _R(seed)
    tone = rng.rand(count).astype(np.float32)[pid % count]
    off = rng.rand(count).astype(np.float32)[pid % count] * n
    along = (b + off) % n
    jn = rng.randint(2, 3, size=count) if joints else np.zeros(count, int)
    # end joints: one per plank at a random place
    jpos = rng.rand(count) * n
    jd = ((b - jpos[pid % count]) % n)
    gap = (la < 1.0) | (joints & (jd < 1.0))
    streak = _stretch(n, 1.0, 0.18, seed + 5) if vertical else _stretch(n, 0.18, 1.0, seed + 5)
    sh = base + tone_spread * (tone - 0.5) + grain * (streak - 0.5) * 2 + 0.05 * _fine(n, seed + 9)
    sh = sh + 0.12 * ((la >= 1.0) & (la < 2.0)) - 0.1 * (la > pw - 2)
    sh = sh + 0.1 * ((jd >= 1) & (jd < 2)) * joints
    rgb = _q(sh, pal, 0.65)
    if peel > 0:
        pm = noise(n, 22, seed + 21, 3) > 1 - peel
        rgb = np.where(pm[..., None], _q(sh * 0.62 + 0.0, pal, 0.5), rgb)
    if nails:
        nx = (la > pw / 2 - 1) & (la < pw / 2 + 1) & ((b % (n / 4) > 6) & (b % (n / 4) < 8))
        rgb = _col(rgb, nx, "#1c1810")
    rgb = _col(rgb, gap, gap_col)
    return rgb


def _corrugated(n, period, pal, seed, rust_pal=None, rust_amt=0.45, vertical=True, bolts=True, nets=False):
    x, y = grid(n)
    a, b = (x, y) if vertical else (y, x)
    ph = (a % period) / period
    prof = 0.5 + 0.5 * np.cos(ph * 6.2832 - 0.9)  # light from the upper left: the ridge faces it
    sh = 0.22 + 0.62 * prof + 0.16 * (noise(n, 14, seed, 3) - 0.5) * 2 + 0.05 * _fine(n, seed + 1)
    sh = sh - 0.2 * np.clip((noise(n, 40, seed + 2, 2) - 0.55) * 3, 0, 1)  # soot / wet streaks
    streak = _stretch(n, 0.06, 1.0, seed + 3) if vertical else _stretch(n, 1.0, 0.06, seed + 3)
    sh = sh - 0.18 * np.clip((streak - 0.55) * 4, 0, 1)
    rgb = _q(sh, pal, 0.6)
    if rust_pal is not None:
        rm = noise(n, 18, seed + 4, 4)
        rm = np.clip((rm - (1 - rust_amt)) * 5, 0, 1)
        rsh = 0.25 + 0.55 * prof + 0.15 * _fine(n, seed + 6)
        rgb = np.where((rm > 0.5)[..., None], _q(rsh * 0.9, rust_pal, 0.8), rgb)
    if bolts:
        bm = ((b % (n / 2)) > 3) & ((b % (n / 2)) < 6) & ((a % (period * 2)) > period * 0.5 - 1.2) & ((a % (period * 2)) < period * 0.5 + 1.2)
        rgb = _col(rgb, bm, "#1c1a14")
    if nets:
        lat = (((x + y) % 16) < 1.5) | (((x - y) % 16) < 1.5)
        lat &= noise(n, 30, seed + 8, 2) > 0.42
        rgb = _col(rgb, lat, "#0a1022")
    return rgb


def _plaster(n, pal, seed, base=0.58, stain=0.22, cracks=2, peel_col=None, peel=0.0, ghosts=0):
    sh = base + stain * (noise(n, 28, seed, 4) - 0.5) * 2 + 0.07 * _fine(n, seed + 1)
    sh = sh - 0.16 * np.clip((_stretch(n, 0.1, 1.0, seed + 2) - 0.58) * 4, 0, 1)
    rgb = _q(sh, pal, 0.75)
    if ghosts:
        rng = _R(seed + 3)
        for _ in range(ghosts):
            cx, cy = rng.randint(n), rng.randint(n)
            w, h = rng.randint(22, 44), rng.randint(26, 50)
            x, y = grid(n)
            dx = (x - cx + n / 2) % n - n / 2
            dy = (y - cy + n / 2) % n - n / 2
            gm = (np.abs(dx) < w / 2) & (np.abs(dy) < h / 2)
            edge = gm & ((np.abs(dx) > w / 2 - 2) | (np.abs(dy) > h / 2 - 2))
            rgb = np.where(gm[..., None], _q(sh + 0.1, pal, 0.5), rgb)
            rgb = np.where(edge[..., None], _q(sh - 0.2, pal, 0.5), rgb)
    for c in range(cracks):
        rgb = _col(rgb, _crack(n, seed + 10 + c, 34), hex_of(pal[0]))
    if peel_col is not None and peel > 0:
        pm = noise(n, 20, seed + 30, 3) > 1 - peel
        rgb = np.where(pm[..., None], _q(0.25 + 0.5 * noise(n, 5, seed + 31, 3), peel_col, 0.8), rgb)
    return rgb


def hex_of(c) -> str:
    c = np.asarray(c)
    return "#%02x%02x%02x" % tuple(int(v * 255 + 0.5) for v in c)


def _ground(n, pal, seed, grain=0.14, pebbles=0.0, tufts=0.0, ruts=False, pebble_pal=None, tuft_pal=None, base=0.55, scale=30, shade=0.0):
    sh = base + 0.3 * (noise(n, scale, seed, 4) - 0.5) * 2 + grain * _fine(n, seed + 1)
    if ruts:
        x, y = grid(n)
        sh = sh - 0.24 * np.exp(-((((y - 38) % n) ** 2) / 90.0)) - 0.24 * np.exp(-((((y - 90) % n) ** 2) / 90.0)) * (0.5 + noise(n, 24, seed + 2, 2))
    if shade > 0:
        sh = sh - shade * (noise(n, 44, seed + 9, 3) > 0.64)
    rgb = _q(sh, pal, 0.8)
    rng = _R(seed + 4)
    if pebbles > 0 and pebble_pal is not None:
        for _ in range(int(pebbles * n)):
            cx, cy = rng.randint(n), rng.randint(n)
            r = rng.choice([1.5, 2.2, 3.0])
            bm = _blob(n, cx, cy, r * 1.3, r)
            lit = _blob(n, cx - 0.8, cy - 0.7, r * 0.8, r * 0.6)
            rgb = np.where(bm[..., None], _q(np.full((n, n), 0.35 + rng.rand() * 0.25), pebble_pal, 0.4), rgb)
            rgb = np.where(lit[..., None], _q(np.full((n, n), 0.82), pebble_pal, 0.4), rgb)
    if tufts > 0 and tuft_pal is not None:
        for _ in range(int(tufts * n)):
            cx, cy = rng.randint(n), rng.randint(n)
            for k in range(rng.randint(4, 8)):
                dx = int(rng.randint(-3, 4))
                hgt = int(rng.randint(3, 7))
                for t in range(hgt):
                    rgb[(cy - t) % n, (cx + dx * t // 3) % n] = (tuft_pal[min(len(tuft_pal) - 1, 1 + t // 2 + (k % 2))] * 255 + 0.5).astype(np.uint8)
    return rgb


# ---- airfield surfaces ---------------------------------------------------------------------------------------------------------------------------

def wall_hut():
    return _planks(N, 8, True, HUT, 301, "#1e160c", peel=0.14)


def floor_boards():
    return _planks(N, 8, False, BOARD, 302, "#140e08", tone_spread=0.28, peel=0.0, base=0.5)


def ceil_beams():
    rgb = _planks(N, 8, False, BOARD, 303, "#140e08", tone_spread=0.2, base=0.42, nails=False)
    x, y = grid(N)
    bm = (x % N >= 0) & (np.abs(((y - 64 + N / 2) % N) - N / 2) < 14)
    sh = 0.42 + 0.35 * np.clip(1 - np.abs(((y - 64 + N / 2) % N) - N / 2) / 14, 0, 1) * 0 + 0.06 * (noise(N, 10, 304) - 0.5)
    top = (np.abs(((y - 64 + N / 2) % N) - N / 2) < 14)
    ly = ((y - 50) % N)
    sh = 0.5 - 0.3 * (ly / 28.0) + 0.12 * _fine(N, 305) + 0.1 * (noise(N, 8, 306) - 0.5)
    rgb = np.where(top[..., None], _q(sh, BEAM, 0.7), rgb)
    rgb = _col(rgb, top & ((y - 50) % N == 0), "#2c1c10")
    return rgb


def wall_tent():
    n = N
    x, y = grid(n)
    fold = 0.5 + 0.5 * np.sin((x / n) * 6.2832 * 4 + 0.35 * np.sin(y / n * 6.2832) + 2.0 * noise(n, 40, 317, 2))
    sh = 0.45 + 0.28 * fold + 0.1 * (noise(n, 18, 311, 3) - 0.5) * 2 + 0.06 * _fine(n, 312)
    sh = sh - 0.2 * np.clip((noise(n, 36, 313, 3) - 0.6) * 4, 0, 1)
    rgb = _q(sh, CANV, 0.8)
    seam = (x % 64) < 1.5
    rgb = np.where(seam[..., None], _q(sh * 0.55, CANV, 0.5), rgb)
    stitch = ((x % 64) >= 3) & ((x % 64) < 4) & ((y % 6) < 3)
    rgb = _col(rgb, stitch, "#3a2f20")
    patch = (np.abs(((x - 30) % n)) < 22) & (np.abs(((y - 84) % n)) < 18) & (noise(n, 30, 314) > 0.0)
    pe = patch & ((np.abs(((x - 30) % n) - 0) > 20) | (np.abs(((y - 84) % n)) > 16))
    rgb = np.where(patch[..., None], _q(sh * 1.04 + 0.04, CANV, 0.7), rgb)
    rgb = _col(rgb, pe, "#4a3e2c")
    return rgb


def ceil_canvas():
    n = N
    x, y = grid(n)
    fold = 0.5 + 0.5 * np.sin((y / n) * 6.2832 * 3 + 0.3 * np.sin(x / n * 6.2832) + 2.0 * noise(n, 40, 318, 2))
    sh = 0.5 + 0.22 * fold + 0.1 * (noise(n, 18, 315, 3) - 0.5) * 2 + 0.05 * _fine(n, 316)
    rgb = _q(sh, CANV, 0.8)
    seam = (y % 64) < 1.5
    rgb = np.where(seam[..., None], _q(sh * 0.55, CANV, 0.5), rgb)
    rgb = _col(rgb, ((y % 64) >= 3) & ((y % 64) < 4) & ((x % 6) < 3), "#3a2f20")
    return rgb


def wall_office():
    return _plaster(N, PLAS, 321, base=0.56, stain=0.26, cracks=2, peel_col=ramp("#4a3a20", "#6a5630", "#8a7440"), peel=0.1, ghosts=2)


def ceil_plaster():
    return _plaster(N, PLAS, 322, base=0.62, stain=0.22, cracks=1, ghosts=0)


def wall_hangar():
    return _corrugated(N, 8, CORR, 331, rust_pal=ORNG, rust_amt=0.2)


def ceil_hangar():
    rgb = _corrugated(N, 8, CORR, 332, rust_pal=ORNG, rust_amt=0.14, vertical=False, bolts=False)
    x, y = grid(N)
    tr = ((y > 56) & (y < 64)) | ((x % 64 > 30) & (x % 64 < 34))
    sh = 0.3 + 0.1 * _fine(N, 333)
    rgb = np.where(tr[..., None], _q(sh, STEEL_TRUSS, 0.6), rgb)
    return rgb


STEEL_TRUSS = ramp("#0e1114", "#1c2126", "#2e353b", "#454e56", "#62707a")


BAGS2 = ramp("#2e2b1e", "#49442c", "#686040", "#887d56", "#a89c70", "#c6b98c")
BAGS3 = ramp("#3e2c1c", "#5e432a", "#82603a", "#a57f50", "#c69e6a", "#e0be8c")


def wall_berm():
    """Sandbags: plump pillows in three canvas colours (sand, olive, earth), lit on top, shaded below, a dark gap between courses, ends pinched."""
    n = N
    rows = 8
    bl = _blocks(n, rows, 46, 341, mortar=3, jitter=0.3)
    cx_ = np.minimum(bl["lx"], bl["w"] - 1 - bl["lx"])
    cy_ = np.minimum(bl["ly"], bl["rowh"] - 1 - bl["ly"])
    corner = (cx_ + cy_) < 6  # the bags are rounded: the corners fall into the gap
    bl["mort"] = bl["mort"] | (corner & (bl["ly"] >= 3))
    x, y = grid(n)
    rowh = n // rows
    ly = (y % rowh) / rowh
    r = _R(344)
    lean = r.rand(4000).astype(np.float32)[bl["bid"] % 4000]
    sh = 0.5 + 0.12 * (noise(n, 8, 342, 3) - 0.5) * 2 + 0.05 * _fine(n, 343)
    sh = sh + 0.7 * (0.55 - np.clip(ly + 0.18 * (lean - 0.5), 0, 1)) + 0.12 * bl["hi"] - 0.22 * bl["lo"] + 0.14 * (bl["tone"] - 0.5)
    sh = np.where(bl["mort"], 0.0, sh)
    kind = bl["bid"] % 3
    off = np.where(kind == 0, 0.0, np.where(kind == 1, -0.1, 0.06))
    rgb = _q(sh + off, BAGS, 0.75)
    weave = ((x + y) % 3 == 0) & ~bl["mort"] & (bl["bid"] % 2 == 0)
    rgb = np.where(weave[..., None], (rgb * 0.9).astype(np.uint8), rgb)
    seam = (np.abs(ly - 0.5) < 0.04) & ~bl["mort"] & (bl["bid"] % 3 != 1)
    rgb = np.where(seam[..., None], (rgb * 0.75).astype(np.uint8), rgb)
    return rgb


def floor_dust():
    return _ground(N, DUST, 351, pebbles=0.35, pebble_pal=BAGS, tufts=0.07, tuft_pal=hexs_to_arr(["#1c2a0c", "#4e6a22", "#7a9a34", "#a8c456"]), ruts=True, scale=26, shade=0.3)


def hexs_to_arr(hs):
    return np.stack([hexc(h) for h in hs])


def floor_concrete():
    n = N
    sh = 0.55 + 0.26 * (noise(n, 24, 361, 4) - 0.5) * 2 + 0.1 * _fine(n, 362)
    rgb = _q(sh, CONC, 0.8)
    x, y = grid(n)
    rgb = _col(rgb, (x < 1) | (y < 1), "#161614")  # expansion joints at the tile edge: slabs of a metre
    rgb = _col(rgb, ((x == 1) | (y == 1)), "#7a766a")
    oil = _blob(n, 44, 70, 18, 11) & (noise(n, 10, 363) > 0.36)
    rgb = np.where(oil[..., None], _q(0.12 + 0.12 * noise(n, 5, 364), CONC, 0.5), rgb)
    for c in range(3):
        rgb = _col(rgb, _crack(n, 365 + c, 36), "#1c1c18")
    rng = _R(368)
    for _ in range(26):  # scattered straw
        cx, cy = rng.randint(n), rng.randint(n)
        L = rng.randint(3, 6)
        for t in range(L):
            rgb[(cy + t // 3) % n, (cx + t) % n] = (hexc("#c8aa44" if t % 2 else "#9c8228") * 255).astype(np.uint8)
    return rgb


def floor_lino():
    n = N
    x, y = grid(n)
    s = n // 4
    cell = ((x // s).astype(int) + (y // s).astype(int)) % 2
    lx, ly = x % s, y % s
    sh = 0.55 + 0.14 * (noise(n, 14, 371, 3) - 0.5) * 2 + 0.07 * _fine(n, 372)
    sh = sh + 0.1 * ((lx < 3) | (ly < 3)) - 0.12 * ((lx > s - 3) | (ly > s - 3))
    rgb = np.where((cell == 0)[..., None], _q(sh, LINO_C, 0.7), _q(sh * 0.9, LINO_G, 0.7))
    rgb = _col(rgb, (lx < 1) | (ly < 1), "#141008")
    for c in range(3):
        rgb = _col(rgb, _crack(n, 373 + c, 30), "#0e0c08")
    grime = noise(n, 20, 376, 3) > 0.62
    rgb = np.where(grime[..., None], (rgb * 0.7).astype(np.uint8), rgb)
    return rgb


def floor_metal():
    n = N
    x, y = grid(n)
    d = 16
    u = (x % d) / d
    v = (y % d) / d
    k1 = np.abs(((u + v) % 1.0) - 0.5) < 0.12
    k2 = np.abs(((u - v) % 1.0) - 0.5) < 0.12
    odd = (((x // d) + (y // d)) % 2).astype(bool)
    lozenge = np.where(odd, k1, k2)
    sh = 0.42 + 0.22 * lozenge + 0.12 * (noise(n, 18, 381, 3) - 0.5) * 2 + 0.06 * _fine(n, 382)
    sh = sh - 0.22 * np.clip((noise(n, 30, 383, 3) - 0.6) * 4, 0, 1)
    rgb = _q(sh, TREAD, 0.7)
    rgb = _col(rgb, (y % 64) < 1, "#080b0e")
    rgb = _col(rgb, (y % 64) == 1, "#62727e")
    rv = (((x % 64) > 5) & ((x % 64) < 8) | ((x % 64) > 56) & ((x % 64) < 59)) & ((y % 16) > 6) & ((y % 16) < 9)
    return _col(rgb, rv, "#86a0a8")


def wall_bomber():
    n = N
    x, y = grid(n)
    sh = 0.5 + 0.12 * (noise(n, 24, 391, 3) - 0.5) * 2 + 0.06 * _fine(n, 392)
    lx, ly = x % 64, y % 64
    sh = sh + 0.16 * ((lx == 1) | (ly == 1)) - 0.22 * ((lx == 63) | (ly == 63)) - 0.5 * ((lx == 0) | (ly == 0))
    sh = sh - 0.2 * np.clip((_stretch(n, 0.08, 1.0, 393) - 0.56) * 4, 0, 1)
    rgb = _q(sh, BOMB, 0.65)
    riv = (((lx % 16) > 6) & ((lx % 16) < 9) & ((ly > 4) & (ly < 7) | (ly > 56) & (ly < 59))) | (((ly % 16) > 6) & ((ly % 16) < 9) & ((lx > 4) & (lx < 7) | (lx > 56) & (lx < 59)))
    rgb = _col(rgb, riv, "#7fae80")
    rgb = _col(rgb, np.roll(riv, (1, 1), (0, 1)) & ~riv, "#0a1610")
    rib = (x > 90) & (x < 110)  # a lighter ribbed strip
    rsh = 0.55 + 0.25 * np.sin((y / 8.0) * 3.14159) ** 2 + 0.05 * _fine(n, 394)
    rgb = np.where(rib[..., None], _q(rsh, RIVET, 0.6), rgb)
    scuff = _speck(n, 0.004, 395) & (noise(n, 18, 396) > 0.4)
    return _col(rgb, scuff, "#a4b88a")


def ceil_fuselage():
    n = N
    x, y = grid(n)
    rib = ((x % 64) > 24) & ((x % 64) < 40)
    rsh = 0.5 + 0.35 * np.abs(np.sin(((x % 64) - 24) / 16.0 * 3.14159)) ** 0.7 + 0.06 * _fine(n, 401)
    sh = 0.38 + 0.1 * (noise(n, 22, 402, 3) - 0.5) * 2 + 0.06 * _fine(n, 403)
    rgb = _q(sh, BOMB, 0.65)
    rgb = np.where(rib[..., None], _q(rsh, RIVET, 0.6), rgb)
    loom = ((y > 58) & (y < 66)) | ((y > 62 + 64 - 128) & (y < 70 - 64)) if False else (np.abs(((y - 94) % n) - 0) < 5)
    lsh = 0.3 + 0.4 * np.sin((x / 6.0)) ** 2
    rgb = np.where(loom[..., None], _q(lsh, ramp("#06090a", "#10181a", "#1c2a2c", "#324a4c"), 0.6), rgb)
    rgb = _col(rgb, ((x % 64) == 24) | ((x % 64) == 39), "#06100a")
    return rgb


# ---- city surfaces -------------------------------------------------------------------------------------------------------------------------------

def wall_stucco():
    n = N
    sh = 0.55 + 0.26 * (noise(n, 26, 411, 4) - 0.5) * 2 + 0.08 * _fine(n, 412)
    sh = sh - 0.18 * np.clip((_stretch(n, 0.09, 1.0, 413) - 0.58) * 4, 0, 1)
    rgb = _q(sh, OCHRE, 0.75)
    # bare brick showing through two broken patches
    bl = _blocks(n, 16, 28, 414, mortar=1, jitter=0.3)
    bsh = _shade_blocks(bl, 0.5, 0.45, 415, 0.1)
    brick = _q(bsh, BRICKC, 0.7)
    for cx, cy, rx, ry in ((44, 92, 24, 22),):
        xx, yy = grid(n)
        jt = noise(n, 14, 416, 3) - 0.5
        pm = (np.abs(xx - cx) < rx + 14 * jt) & (np.abs(yy - cy) < ry + 14 * jt)
        rgb = np.where(pm[..., None], brick, rgb)
        edge = pm & ~np.roll(pm, 1, 0) | pm & ~np.roll(pm, 1, 1)
        rgb = _col(rgb, edge, "#e4cc9e")
    for c in range(3):
        rgb = _col(rgb, _crack(n, 420 + c, 38), "#2a1e16")
    return rgb


def wall_ruin():
    n = N
    bl = _blocks(n, 16, 28, 431, mortar=1, jitter=0.3)
    sh = _shade_blocks(bl, 0.46, 0.5, 432, 0.14)
    soot = np.clip((noise(n, 40, 433, 3) - 0.35) * 2.6, 0, 1)
    sh = sh * (1 - 0.55 * soot)
    rgb = _q(sh, SOOT, 0.75)
    # a burnt-out hole showing lath and dark, and a few lit brick edges
    hole = np.zeros((n, n), bool)
    rgb = np.where(hole[..., None], _q(0.1 + 0.2 * noise(n, 4, 435), SOOT, 0.5), rgb)
    x, y = grid(n)
    lath = hole & ((y % 6) < 2)
    rgb = _col(rgb, lath, "#6c5236")
    ember = _speck(n, 0.0025, 436) & ~bl["mort"]
    return _col(rgb, ember, "#ffa050")


def wall_panel():
    n = N
    x, y = grid(n)
    pw = n // 2
    lx, ly = x % pw, y
    frame = (lx < 6) | (lx > pw - 7) | (ly < 8) | (ly > n - 9)
    inner = ~frame
    sh = 0.5 + 0.18 * _stretch(n, 0.1, 1.0, 441) + 0.06 * _fine(n, 442)
    sh = np.where(inner, sh - 0.12 + 0.2 * np.clip(1 - ((lx - 8) + (ly - 10)) / 30.0, 0, 1) * (((lx > 6) & (lx < 14)) | ((ly > 8) & (ly < 16))) , sh + 0.08)
    sh = sh - 0.24 * (((lx > pw - 14) & (lx < pw - 6)) | ((ly > n - 17) & (ly < n - 9))) * inner
    rgb = _q(sh, OAK, 0.7)
    rgb = _col(rgb, (lx == pw - 1) | (lx == 0), "#0e0804")
    gold = (ly > n - 8) & (ly < n - 6)
    rgb = _col(rgb, gold, "#b48a48")
    return rgb


def floor_carpet():
    n = N
    x, y = grid(n)
    wv = ((x + y) % 4 < 2).astype(np.float32)
    sh = 0.45 + 0.08 * wv + 0.1 * (noise(n, 16, 451, 3) - 0.5) * 2 + 0.1 * _fine(n, 452)
    rgb = _q(sh, WINE, 0.7)
    # a pale border pattern of diamonds across the tile
    d = (np.abs(((x % 32) - 16)) + np.abs(((y % 32) - 16)))
    dm = (d < 11) & (d > 7)
    rgb = _col(rgb, dm & (((x // 32) + (y // 32)) % 2 == 0), "#c8a888")
    rgb = _col(rgb, (d < 4) & (((x // 32) + (y // 32)) % 2 == 1), "#d8b890")
    wear = noise(n, 26, 453, 3) > 0.66
    return np.where(wear[..., None], (rgb * 0.72).astype(np.uint8), rgb)


def floor_cobble():
    n = N
    bl = _blocks(n, 8, 22, 461, mortar=2, jitter=0.45, stagger=True)
    sh = _shade_blocks(bl, 0.54, 0.34, 462, 0.14)
    x, y = grid(n)
    sh = sh - 0.16 * np.exp(-((((y - 20) % n) ** 2) / 60.0)) * 0 
    rgb = _q(sh, SETT, 0.75)
    pud = noise(n, 30, 463, 3) > 0.78
    rgb = np.where((pud & ~bl["mort"])[..., None], (_q(0.3 + 0.2 * noise(n, 6, 464), SETT, 0.6) * 0.62).astype(np.uint8), rgb)
    rng = _R(465)
    for _ in range(18):
        cx, cy = rng.randint(n), rng.randint(n)
        for t in range(rng.randint(3, 7)):
            rgb[cy, (cx + t) % n] = (hexc("#c8aa5a") * 255).astype(np.uint8)
    return rgb


def floor_rubble():
    n = N
    sh = 0.5 + 0.3 * (noise(n, 14, 471, 4) - 0.5) * 2 + 0.12 * _fine(n, 472)
    rgb = _q(sh, RUBB, 0.8)
    rng = _R(473)
    for i in range(34):
        cx, cy = rng.randint(n), rng.randint(n)
        rx, ry = rng.uniform(2, 6), rng.uniform(1.5, 4)
        bm = _blob(n, cx, cy, rx, ry)
        pal = BRICKC if i % 3 == 0 else (SOOT if i % 3 == 1 else RUBB)
        rgb = np.where(bm[..., None], _q(np.full((n, n), 0.4 + rng.rand() * 0.35), pal, 0.4), rgb)
        lit = _blob(n, cx - 1, cy - 1, rx * 0.6, ry * 0.5)
        rgb = np.where(lit[..., None], _q(np.full((n, n), 0.88), pal, 0.4), rgb)
    ch = noise(n, 30, 474, 3) > 0.8
    rgb = np.where(ch[..., None], _q(0.25 + 0.2 * noise(n, 4, 475), SOOT, 0.5), rgb)
    return _col(rgb, _speck(n, 0.004, 476), "#cfe8f0")  # glass glints


# ---- harbour surfaces ----------------------------------------------------------------------------------------------------------------------------

def wall_quay():
    n = N
    bl = _blocks(n, 8, 36, 481, mortar=2, jitter=0.2, stagger=True)
    sh = _shade_blocks(bl, 0.5, 0.36, 482, 0.14)
    sh = sh - 0.22 * np.clip((_stretch(n, 0.1, 1.0, 483) - 0.55) * 4, 0, 1)
    rgb = _q(sh, WETSTONE, 0.75)
    x, y = grid(n)
    weed = (noise(n, 16, 484, 3) > 0.62) & (((y + 20) % n) > 70)
    rgb = np.where((weed & ~bl["mort"])[..., None], _q(0.3 + 0.5 * noise(n, 5, 485), WEED, 0.7), rgb)
    ring = ((np.abs(((x - 62) % n) - 0) < 5) & (np.abs(((y - 40) % n)) < 5)) & (((x - 62) ** 2 + (y - 40) ** 2) > 6) & (((x - 62) ** 2 + (y - 40) ** 2) < 26)
    return _col(rgb, ring, "#2a2018")


def wall_shed():
    return _corrugated(N, 8, SHED, 491, rust_pal=ramp("#2a1208", "#4e2410", "#7a3a16", "#a45a24"), rust_amt=0.22, nets=True)


def wall_cell():
    n = N
    bl = _blocks(n, 8, 40, 501, mortar=2, jitter=0.2)
    sh = _shade_blocks(bl, 0.5, 0.36, 502, 0.16)
    sh = sh - 0.22 * np.clip((_stretch(n, 0.1, 1.0, 503) - 0.55) * 4, 0, 1)
    rgb = _q(sh, CELLG, 0.75)
    rng = _R(504)
    for g in range(3):  # scratched tally marks: groups of four strokes and one across
        cx, cy = rng.randint(10, 110), rng.randint(10, 110)
        for k in range(4):
            for t in range(9):
                rgb[(cy + t) % n, (cx + k * 3) % n] = (hexc("#a6b4b8") * 255).astype(np.uint8)
        for t in range(14):
            rgb[(cy + 7 - t // 2) % n, (cx - 1 + t) % n] = (hexc("#a6b4b8") * 255).astype(np.uint8)
    drip = (_stretch(n, 0.06, 1.0, 505) > 0.64)
    return np.where(drip[..., None], (rgb * 0.7).astype(np.uint8), rgb)


def wall_dunes():
    n = N
    x, y = grid(n)
    ripple = 0.5 + 0.5 * np.sin((y / n) * 6.2832 * 5 + 3.0 * noise(n, 40, 511, 3))
    sh = 0.55 + 0.2 * ripple + 0.2 * (noise(n, 30, 512, 4) - 0.5) * 2 + 0.06 * _fine(n, 513)
    sh = sh - 0.4 * (noise(n, 60, 516, 2) > 0.7) + 0.1 * (noise(n, 20, 517, 3) > 0.72)
    rgb = _q(sh, SANDC, 0.8)
    rng = _R(514)
    for _ in range(9):  # tufts of marram grass
        cx, cy = rng.randint(n), rng.randint(20, n)
        for k in range(7):
            dx = rng.uniform(-0.9, 0.9)
            for t in range(rng.randint(6, 12)):
                rgb[(cy - t) % n, int(cx + dx * t) % n] = (MARR[min(3, 1 + t // 4 + (k % 2))] * 255 + 0.5).astype(np.uint8)
    return rgb


def floor_sand():
    n = N
    x, y = grid(n)
    ripple = 0.5 + 0.5 * np.sin(((x + 14 * noise(n, 30, 521, 3)) / n) * 6.2832 * 4)
    sh = 0.55 + 0.2 * ripple + 0.2 * (noise(n, 22, 522, 4) - 0.5) * 2 + 0.07 * _fine(n, 523)
    sh = sh - 0.42 * (noise(n, 60, 526, 2) > 0.7) + 0.1 * (noise(n, 20, 527, 3) > 0.72)  # the shade of a pine and the sun's glare
    rgb = _q(sh, SANDC, 0.8)
    rng = _R(524)
    for _ in range(26):  # tiny shells
        cx, cy = rng.randint(n), rng.randint(n)
        rgb[cy, cx] = (hexc("#fff8e8") * 255).astype(np.uint8)
        rgb[(cy + 1) % n, (cx + 1) % n] = (hexc("#8a6a3c") * 255).astype(np.uint8)
    wr = (np.abs(((y - 96) % n)) < 3) & (noise(n, 12, 525) > 0.35)
    return _col(rgb, wr, "#9a7a44")  # a line of dry seaweed


def floor_quay():
    n = N
    pl = _planks(n, 8, False, QUAYC, 531, "#080c12", tone_spread=0.3, peel=0.0, base=0.45, nails=False)
    bl = _blocks(n, 4, 40, 532, mortar=2, jitter=0.25)
    sh = _shade_blocks(bl, 0.48, 0.34, 533, 0.14)
    sett = _q(sh, QUAYC, 0.75)
    x, y = grid(n)
    rgb = np.where((y < 64)[..., None], pl, sett)
    pud = noise(n, 30, 534, 3) > 0.8
    rgb = np.where(pud[..., None], _q(0.3 + 0.25 * noise(n, 6, 535), QUAYC, 0.4), rgb)
    return _col(rgb, (y % 64) < 1, "#060a10")


def floor_cell():
    n = N
    bl = _blocks(n, 4, 40, 541, mortar=2, jitter=0.25)
    sh = _shade_blocks(bl, 0.48, 0.34, 542, 0.14)
    rgb = _q(sh, CELLG, 0.75)
    rng = _R(543)
    for _ in range(40):
        cx, cy = rng.randint(n), rng.randint(n)
        for t in range(rng.randint(3, 7)):
            rgb[(cy + t // 3) % n, (cx + t) % n] = (hexc("#a08a50" if t % 2 else "#78663a") * 255).astype(np.uint8)
    damp = noise(n, 34, 544, 3) > 0.66
    return np.where(damp[..., None], (rgb * 0.68).astype(np.uint8), rgb)


def ceil_cell():
    n = N
    bl = _blocks(n, 8, 30, 551, mortar=2, jitter=0.3)
    sh = _shade_blocks(bl, 0.4, 0.3, 552, 0.14)
    rgb = _q(sh, CELLG, 0.75)
    x, y = grid(n)
    return _col(rgb, (y % 64) < 2, "#0a0e12")


# ---- skies: 256 x 64, the horizon at row 48 (SKY_HORIZON 0.76); wrap horizontally -------------------------------------------------------------------

W, H = 256, 64
HZ = 48


def _band_noise(seed: int, sx: float, sy: float, oct_: int = 3) -> np.ndarray:
    """A (H, W) field, tileable along x, stretched along x (clouds as long bands)."""
    base = noise(256, 30, seed, oct_)
    xi = (np.arange(W)[None, :] * sx).astype(int) % 256
    yi = (np.arange(H)[:, None] * sy).astype(int) % 256
    return base[yi, xi]


def _dither_pal(sh, pal):
    b = BAYER8[np.arange(H)[:, None] % 8, np.arange(W)[None, :] % 8]
    k = len(pal) - 1
    i = np.clip(np.round(np.clip(sh, 0, 1) * k + b * 0.45), 0, k).astype(int)
    return (pal[i] * 255 + 0.5).astype(np.uint8)


def _ridge(seed: int, base: float, amp: float, scale: float) -> np.ndarray:
    """A tileable 1D profile of H rows' worth: the row (float) of a far silhouette per column."""
    r = _R(seed)
    cells = max(2, int(W / scale))
    g = r.rand(cells)
    xs = np.arange(W) / W * cells
    i0 = np.floor(xs).astype(int) % cells
    i1 = (i0 + 1) % cells
    t = xs - np.floor(xs)
    t = t * t * (3 - 2 * t)
    v = g[i0] * (1 - t) + g[i1] * t
    return base - amp * v


def _put(rgb, x, y, hexs):
    if 0 <= y < H:
        rgb[int(y), int(x) % W] = (hexc(hexs) * 255 + 0.5).astype(np.uint8)


def _cluster(rgb, cx, cy, pts, cols):
    for (dx, dy, k) in pts:
        _put(rgb, cx + dx, cy + dy, cols[k])


def sky_day():
    """The airfield's bleached day: a deeper blue overhead, cloud bands with a shaded belly, a low white sun with a dithered bloom, a far line of hills and hangar roofs, two barrage balloons."""
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    pal = ramp("#3d6aa0", "#5b86b8", "#7ba3cc", "#a0c0da", "#c4d8e6", "#e3ecee", "#f6f0dc")
    base = 0.12 + 0.62 * np.clip(yy / HZ, 0, 1) ** 1.3
    cl = _band_noise(601, 1.0, 5.0, 3)
    cl2 = _band_noise(602, 1.0, 9.0, 3)
    band1 = np.clip((cl - 0.5) * 6, 0, 1) * np.clip(1 - np.abs(yy - 24) / 11.0, 0, 1)
    band2 = np.clip((cl2 - 0.54) * 6, 0, 1) * np.clip(1 - np.abs(yy - 11) / 7.0, 0, 1)
    belly = np.clip((cl - 0.5) * 6, 0, 1) * np.clip((yy - 24) / 10.0, 0, 1) * (1 - np.clip((yy - 34) / 6, 0, 1))
    sh = base + 0.4 * band1 + 0.3 * band2 - 0.16 * belly
    d = np.sqrt((((xx - 70 + W / 2) % W - W / 2) / 40.0) ** 2 + ((yy - 40) / 14.0) ** 2)
    sh = sh + 0.28 * np.clip(1 - d, 0, 1) ** 1.6
    sh = sh + 0.015 * (_R(603).rand(H, W) - 0.5)
    rgb = _dither_pal(sh, pal)
    # the sun: a pale disc
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if dx * dx + dy * dy <= 9:
                _put(rgb, 70 + dx, 38 + dy, "#fffbe8" if dx * dx + dy * dy <= 5 else "#fbeab8")
    # far hills and hangars (one silhouette, haze blue-khaki), then the ground haze under the horizon
    ridge = _ridge(604, HZ - 1, 7, 28)
    for xcol in range(W):
        top = int(ridge[xcol])
        for y in range(top, HZ + 1):
            _put(rgb, xcol, y, "#6a7f88" if y - top < 2 else "#5a6e74")
    hz = _R(605)
    for hx in (22, 96, 150, 214):  # hangar roofs: a flat box with a low pitch
        w = int(hz.randint(14, 22))
        for xcol in range(hx, hx + w):
            top = HZ - 6 - (1 if (xcol - hx) in (0, w - 1) else 0)
            for y in range(top, HZ + 1):
                _put(rgb, xcol, y, "#7e8c8a" if y == top else "#4e5f60")
        for xcol in range(hx + 2, hx + w - 2, 3):
            _put(rgb, xcol, HZ - 3, "#2a3638")
    for y in range(HZ + 1, H):
        t = (y - HZ) / (H - HZ)
        for xcol in range(W):
            _put(rgb, xcol, y, "#b6b090" if ((xcol + y) % 2) == 0 or t > 0.5 else "#a39c7e")
    # barrage balloons: a plump grey ellipse with fins and a thin cable
    for bx, by in ((38, 20), (184, 27)):
        for dy in range(-2, 3):
            for dx in range(-5, 6):
                if (dx / 5.0) ** 2 + (dy / 2.4) ** 2 <= 1:
                    _put(rgb, bx + dx, by + dy, "#d0d4d0" if dy < 0 else ("#9ea6a8" if dy == 0 else "#6e7a7e"))
        for k in range(3):
            _put(rgb, bx + 5 + k, by + 2 + k, "#4a5658")
            _put(rgb, bx + 5 + k, by - 2 - k, "#4a5658")
        for t in range(3, HZ - by):
            _put(rgb, bx - (t // 6), by + t, "#6c7678")
    return rgb


def sky_harbour():
    """The harbour at night: deep navy to a lighter horizon, a pale low moon with a small halo, stars at one texel, thin high cloud, three searchlight beams crossing, flak bursts as small clusters, the sea line."""
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    pal = ramp("#08122a", "#0e1c3e", "#16295a", "#223a78", "#34509a", "#4e6db4", "#7a92cc", "#aebfe0")
    base = 0.06 + 0.5 * np.clip(yy / HZ, 0, 1) ** 1.5
    cl = _band_noise(611, 1.0, 6.0, 3)
    cloud = np.clip((cl - 0.52) * 5, 0, 1) * np.clip(1 - np.abs(yy - 30) / 12.0, 0, 1)
    sh = base + 0.2 * cloud
    d = np.sqrt((((xx - 190 + W / 2) % W - W / 2) / 34.0) ** 2 + ((yy - 33) / 16.0) ** 2)
    sh = sh + 0.3 * np.clip(1 - d, 0, 1) ** 1.8
    sh = sh + 0.015 * (_R(612).rand(H, W) - 0.5)
    rgb = _dither_pal(sh, pal)
    rs = _R(613)
    for _ in range(46):  # stars, one texel
        _put(rgb, rs.randint(W), rs.randint(0, 34), "#e8f0ff" if rs.rand() < 0.4 else "#9db4e0")
    for dy in range(-3, 4):  # the moon
        for dx in range(-3, 4):
            if dx * dx + dy * dy <= 9:
                _put(rgb, 190 + dx, 33 + dy, "#f4f6ee" if dx * dx + dy * dy <= 4 else "#d6dcdc")
    _put(rgb, 192, 32, "#aab4bc")
    _put(rgb, 189, 34, "#aab4bc")
    # the sea line: dark water below the horizon, with a few glints
    for y in range(HZ, H):
        for xcol in range(W):
            _put(rgb, xcol, y, "#16284a" if (xcol + y) % 3 else "#223a66")
    for xcol in range(W):
        _put(rgb, xcol, HZ - 1, "#0e1c38")
    for xcol in range(0, W, 7):
        _put(rgb, xcol + (xcol // 7) % 3, HZ + 2 + (xcol // 7) % 5, "#7ea0d0")
    # searchlight beams: thin straight lines from the horizon, leaning, each two texels at the root and one at the tip
    for bx, lean in ((30, 0.5), (96, -0.35), (138, 0.18), (232, -0.55)):
        for t in range(0, HZ - 2):
            xcol = bx + lean * t
            _put(rgb, xcol, HZ - 2 - t, "#dce8ff")
            if t < 26:
                _put(rgb, xcol + 1, HZ - 2 - t, "#a8bcec")
    # flak bursts: a dark puff with a lit core and two sparks
    for fx, fy in ((54, 16), (116, 26), (222, 20)):
        _cluster(rgb, fx, fy, [(-1, 0, 0), (0, -1, 0), (1, 0, 0), (0, 1, 0), (-2, 1, 0), (2, -1, 0), (0, 0, 1), (-1, -1, 2), (3, 1, 2), (-3, -1, 2)], ["#0a1226", "#ffd480", "#ff9a40"])
    return rgb


def sky_harbour_day():
    """The coast's cobalt morning: saturated blue overhead to a pale gold horizon, cumulus bands, a low sun, gulls as 2-pixel marks, a far headland, and the sea line (the one saturated sky of the path)."""
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    pal = ramp("#2c62b4", "#3f7acc", "#5e98dc", "#84b6ea", "#aed0f2", "#d4e6f6", "#f4f0dc")
    base = 0.2 + 0.62 * np.clip(yy / HZ, 0, 1) ** 1.0
    cl = _band_noise(621, 1.0, 5.0, 4)
    band = np.clip((cl - 0.52) * 6, 0, 1) * np.clip(1 - np.abs(yy - 22) / 13.0, 0, 1)
    belly = np.clip((cl - 0.52) * 6, 0, 1) * np.clip((yy - 24) / 8.0, 0, 1) * (1 - np.clip((yy - 33) / 6, 0, 1))
    sh = base + 0.3 * band - 0.1 * belly
    d = np.sqrt((((xx - 150 + W / 2) % W - W / 2) / 44.0) ** 2 + ((yy - 40) / 14.0) ** 2)
    sh = sh + 0.22 * np.clip(1 - d, 0, 1) ** 1.5
    sh = sh + 0.015 * (_R(622).rand(H, W) - 0.5)
    rgb = _dither_pal(sh, pal)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if dx * dx + dy * dy <= 9:
                _put(rgb, 150 + dx, 36 + dy, "#fffbea" if dx * dx + dy * dy <= 5 else "#fcecb4")
    ridge = _ridge(623, HZ - 1, 5, 40)
    for xcol in range(W):
        top = int(ridge[xcol])
        for y in range(top, HZ + 1):
            _put(rgb, xcol, y, "#6c8aa2" if y - top < 2 else "#587890")
    for y in range(HZ + 1, H):  # the sea
        for xcol in range(W):
            _put(rgb, xcol, y, "#2f8fb8" if (xcol + y) % 3 else "#3ea6c8")
    for xcol in range(0, W, 5):
        _put(rgb, xcol + (xcol // 5) % 4, HZ + 1 + (xcol // 5) % 7, "#f4f8f0")
    rs = _R(624)
    for _ in range(9):  # gulls: a 3-texel 'v'
        gx, gy = rs.randint(W), rs.randint(8, 30)
        for (dx, dy) in ((-2, 0), (-1, 1), (0, 0), (1, 1), (2, 0)):
            _put(rgb, gx + dx, gy + dy, "#f8f8f4")
    return rgb


def sky_dusk():
    """The old city's dusk: a brown-grey sky going amber at the horizon, smoke columns leaning in the wind, a ragged skyline of roofs, chimneys and one dome, lit windows as single texels."""
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    pal = ramp("#241a1c", "#3a2a2a", "#58403a", "#7c5a44", "#a47a52", "#cc9a60", "#eab878")
    base = 0.08 + 0.62 * np.clip(yy / HZ, 0, 1) ** 1.4
    cl = _band_noise(631, 1.0, 5.0, 3)
    cloud = np.clip((cl - 0.52) * 5, 0, 1) * np.clip(1 - np.abs(yy - 26) / 12.0, 0, 1)
    sh = base + 0.18 * cloud
    d = np.sqrt((((xx - 120 + W / 2) % W - W / 2) / 70.0) ** 2 + ((yy - 46) / 14.0) ** 2)
    sh = sh + 0.24 * np.clip(1 - d, 0, 1) ** 1.3
    sh = sh + 0.015 * (_R(632).rand(H, W) - 0.5)
    rgb = _dither_pal(sh, pal)
    # smoke columns
    for sx0, lean in ((30, 0.3), (140, 0.25), (208, 0.35)):
        for t in range(0, 44):
            xc = sx0 + lean * t + int(2 * np.sin(t / 5.0))
            wd = 1 + t // 10
            for k in range(wd):
                _put(rgb, xc + k, HZ - 6 - t, "#2c2224" if k < wd - 1 else "#46322e")
    # the skyline
    r = _R(633)
    xcol = 0
    while xcol < W:
        w = int(r.randint(6, 16))
        top = int(HZ - r.randint(4, 14))
        for x2 in range(xcol, min(W, xcol + w)):
            for y in range(top, HZ + 2):
                _put(rgb, x2, y, "#1a1214" if y > top else "#2a1e1e")
        if r.rand() < 0.4:
            _put(rgb, xcol + 2, top - 1, "#1a1214")
            _put(rgb, xcol + 2, top - 2, "#1a1214")
        for wy in range(top + 2, HZ, 4):
            if r.rand() < 0.35:
                _put(rgb, xcol + 1 + int(r.randint(0, max(1, w - 2))), wy, "#ffc060")
        xcol += w
    for y in range(HZ + 2, H):
        for xc in range(W):
            _put(rgb, xc, y, "#1a1214")
    return rgb


def sky_fire():
    """The ruined city at night: a black-red sky, smoke banks lit from below by fires, a few stars, flak sparks and the ragged line of burning roofs."""
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    pal = ramp("#120a14", "#241014", "#3e1a18", "#62281c", "#8e3c20", "#c05a28", "#e88a40")
    base = 0.04 + 0.5 * np.clip(yy / HZ, 0, 1) ** 1.6
    cl = _band_noise(641, 1.0, 5.0, 4)
    smoke = np.clip((cl - 0.46) * 4, 0, 1) * np.clip(1 - np.abs(yy - 28) / 18.0, 0, 1)
    sh = base * (1 - 0.3 * smoke) + 0.1 * smoke * np.clip((yy - 20) / 24.0, 0, 1)
    glow = np.sqrt((((xx - 70 + W / 2) % W - W / 2) / 40.0) ** 2 + ((yy - 46) / 18.0) ** 2) * 0 + 0
    for gx in (40, 150, 226):
        d = np.sqrt((((xx - gx + W / 2) % W - W / 2) / 34.0) ** 2 + ((yy - 47) / 16.0) ** 2)
        sh = sh + 0.3 * np.clip(1 - d, 0, 1) ** 1.4
    sh = sh + 0.015 * (_R(642).rand(H, W) - 0.5)
    rgb = _dither_pal(sh, pal)
    rs = _R(643)
    for _ in range(22):
        _put(rgb, rs.randint(W), rs.randint(0, 22), "#d8c8c0" if rs.rand() < 0.4 else "#8a6a66")
    r = _R(644)
    xcol = 0
    while xcol < W:
        w = int(r.randint(5, 14))
        top = int(HZ - r.randint(2, 11))
        for x2 in range(xcol, min(W, xcol + w)):
            for y in range(top, HZ + 2):
                _put(rgb, x2, y, "#0c0608" if y > top else "#1c0e0e")
            if r.rand() < 0.3:
                _put(rgb, x2, top - 1, "#ff8a30")
        xcol += w
    for y in range(HZ + 2, H):
        for xc in range(W):
            _put(rgb, xc, y, "#0c0608")
    for fx, fy in ((84, 14), (176, 22)):
        _cluster(rgb, fx, fy, [(-1, 0, 0), (0, -1, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), (-2, 1, 2), (2, -1, 2), (3, 0, 2)], ["#0c0608", "#ffd890", "#ff8a30"])
    return rgb


# ---- a billboard the old canvas tiles carried as a repeat: the tent's guy-rope eyelet, an iron ring on a stitched canvas patch (hard alpha, a one-pixel darker edge, lit from the upper left) ----

IRON_R = ramp("#0e1012", "#1e2226", "#343a40", "#505860", "#78828a", "#a4aeb4")


def thing_tent_eyelet():
    n = 128
    x, y = grid(n)
    cx, cy = 64.0, 66.0
    patch = (np.abs(x - cx) < 30) & (np.abs(y - cy) < 30)
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    ring = (d > 11) & (d < 18)
    hole = d <= 11
    lit = np.clip(0.55 - ((x - cx) + (y - cy)) / 120.0, 0, 1)
    rgb = _q(0.3 + 0.5 * lit + 0.1 * _fine(n, 701), CANV, 0.7)
    stitch = (patch & ((np.abs(x - cx) > 25) & (np.abs(x - cx) < 27) | (np.abs(y - cy) > 25) & (np.abs(y - cy) < 27)) & (((x + y) % 5) < 3))
    rgb = _col(rgb, stitch, "#3a2f20")
    rgb = np.where(hole[..., None] & patch[..., None], _q(0.12 + 0.1 * lit, CANV, 0.5), rgb)
    rgb = np.where(ring[..., None], _q(0.2 + 0.7 * lit, IRON_R, 0.6), rgb)
    shadow = ((d > 18) & (d < 21)) & ((x - cx) + (y - cy) > 4)
    rgb = np.where(shadow[..., None], (rgb * 0.7).astype(np.uint8), rgb)
    m = patch
    edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    rgb = np.where(edge[..., None], (rgb * 0.5).astype(np.uint8), rgb)
    out = np.zeros((n, n, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.where(m, 255, 0)
    return out


DRAW = {k: v for k, v in sorted(globals().items()) if callable(v) and k.startswith(("ceil_", "floor_", "wall_", "sky_", "thing_")) and v.__module__ == __name__}
