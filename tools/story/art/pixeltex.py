"""Procedural pixel-art textures for the 2.5D world (docs/STORY_25D_ART_DIRECTION.md 2.D): dense, dithered, worn surfaces in a chapter's palette.

The tiles baked from the chapter SVGs (tools/story/bake_tiles.gd) are flat; these are drawn in numpy straight at tile size (64 or 128 px), every one
tileable, then quantised to a small palette ramp with ordered dithering, so they read as hand-placed pixels: brick and grout, glazed tiles, rust and grime,
steel trusses, pipes, cables, blinds, panels, lino, checker, carpet, obsidian, lava. A chapter's `tex_<chapter>.py` composes them; `tiles.build` writes its
results after the Godot bake (a tile of the same id replaces the baked one). Deterministic: every random value comes from a seeded generator.
"""
from __future__ import annotations

import numpy as np

BAYER8 = (np.array([[0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38],
                    [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
                    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]], np.float32) + 0.5) / 64.0 - 0.5


def hexc(c: str) -> np.ndarray:
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def ramp(*cols) -> np.ndarray:
    """A palette ramp, dark to light, as an (n, 3) array."""
    return np.stack([hexc(c) if isinstance(c, str) else np.asarray(c, np.float32) for c in cols])


def grid(n: int):
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    return x, y


def noise(n: int, scale: float, seed: int, octaves: int = 3) -> np.ndarray:
    """Tileable value noise 0..1 (periodic in both directions)."""
    rng = np.random.RandomState(seed)
    out = np.zeros((n, n), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        cells = max(1, int(round(n / scale * (2 ** o))))
        g = rng.rand(cells, cells).astype(np.float32)
        x, y = grid(n)
        fx, fy = x / n * cells, y / n * cells
        x0, y0 = np.floor(fx).astype(int) % cells, np.floor(fy).astype(int) % cells
        x1, y1 = (x0 + 1) % cells, (y0 + 1) % cells
        tx, ty = fx - np.floor(fx), fy - np.floor(fy)
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        v = (g[y0, x0] * (1 - tx) + g[y0, x1] * tx) * (1 - ty) + (g[y1, x0] * (1 - tx) + g[y1, x1] * tx) * ty
        out += v * amp
        tot += amp
        amp *= 0.5
    return out / tot


def speckle(n: int, density: float, seed: int) -> np.ndarray:
    return (np.random.RandomState(seed).rand(n, n) < density).astype(np.float32)


def quantise(shade: np.ndarray, pal: np.ndarray, dither: float = 1.0) -> np.ndarray:
    """Map a 0..1 shade onto a palette ramp with 8x8 ordered dithering between neighbouring steps. Returns uint8 RGB."""
    n = shade.shape[0]
    k = len(pal) - 1
    b = BAYER8[np.arange(shade.shape[0])[:, None] % 8, np.arange(shade.shape[1])[None, :] % 8]
    v = np.clip(shade, 0, 1) * k + b * dither
    i = np.clip(np.round(v), 0, k).astype(int)
    return (pal[i] * 255 + 0.5).astype(np.uint8)


def mix_rgb(a: np.ndarray, b: np.ndarray, m: np.ndarray) -> np.ndarray:
    m = m[..., None].astype(np.float32)
    return (a.astype(np.float32) * (1 - m) + b.astype(np.float32) * m).astype(np.uint8)


def overlay(base: np.ndarray, mask: np.ndarray, rgb) -> np.ndarray:
    out = base.copy()
    out[mask > 0.5] = (np.asarray(hexc(rgb) if isinstance(rgb, str) else rgb) * 255).astype(np.uint8)
    return out


# ---- shades (0..1 fields) that the chapters quantise with their own palette -------------------------------------------------------------------------

def bricks(n: int, rows: int = 8, cols: int = 4, mortar: int = 1, seed: int = 1, wear: float = 0.35):
    """Brick courses: (shade, mortar mask). Each brick its own tone, chipped edges, grime towards the bottom."""
    x, y = grid(n)
    bh = n / rows
    bw = n / cols
    r = np.floor(y / bh)
    off = (r % 2) * bw * 0.5
    c = np.floor(((x + off) % n) / bw)
    rng = np.random.RandomState(seed)
    tone = rng.rand(rows, cols + 1).astype(np.float32)
    t = tone[r.astype(int) % rows, c.astype(int) % (cols + 1)]
    ly = y - r * bh
    lx = ((x + off) % n) - c * bw
    mort = (ly < mortar) | (lx < mortar)
    sh = 0.45 + 0.25 * t + 0.12 * (ly < mortar + 1.5) - 0.12 * (ly > bh - 2)
    sh += (noise(n, 8, seed + 3) - 0.5) * 0.3
    chips = (noise(n, 4, seed + 7) > 1 - wear * 0.4) & ~mort
    sh = np.where(chips, sh - 0.25, sh)
    return np.clip(sh, 0, 1), mort.astype(np.float32)


def tiles(n: int, count: int = 4, grout: int = 1, seed: int = 2, gloss: float = 0.3):
    """Glazed square tiles with grout lines and a highlight on each tile's upper left: (shade, grout mask)."""
    x, y = grid(n)
    s = n / count
    lx, ly = x % s, y % s
    g = (lx < grout) | (ly < grout)
    rng = np.random.RandomState(seed)
    tone = rng.rand(count, count).astype(np.float32)
    t = tone[(y // s).astype(int) % count, (x // s).astype(int) % count]
    sh = 0.5 + 0.12 * (t - 0.5) + gloss * np.clip(1 - (lx + ly) / (s * 0.6), 0, 1) * 0.5 - 0.1 * (lx > s - 2) - 0.1 * (ly > s - 2)
    sh += (noise(n, 16, seed) - 0.5) * 0.12
    return np.clip(sh, 0, 1), g.astype(np.float32)


def grime(n: int, seed: int = 3, amount: float = 0.5, drip: bool = True):
    """Dirt: blotches plus vertical streaks running down. 0 clean .. 1 filthy."""
    g = np.clip((noise(n, 24, seed, 4) - 0.55) * 3.0 * amount, 0, 1)
    if drip:
        rng = np.random.RandomState(seed + 11)
        cols = rng.rand(n) < 0.08
        x, y = grid(n)
        streak = cols[x.astype(int)] * np.clip(noise(n, 6, seed + 5) * 1.6 - 0.4, 0, 1)
        g = np.clip(g + streak * amount * 0.7, 0, 1)
    return g


def rust(n: int, seed: int = 4, amount: float = 0.5):
    """Rust patches with a crusty edge: 0 none .. 1 rust."""
    v = noise(n, 14, seed, 4)
    return np.clip((v - (1 - amount * 0.6)) * 6.0, 0, 1)


def panels(n: int, count: int = 2, seed: int = 5, rivets: bool = True):
    """Metal plates with seams and rivets: (shade, seam mask)."""
    x, y = grid(n)
    s = n / count
    lx, ly = x % s, y % s
    seam = (lx < 1) | (ly < 1)
    sh = 0.5 + 0.15 * (lx < 2) - 0.15 * (lx > s - 3) + 0.1 * (ly < 2) - 0.1 * (ly > s - 3)
    if rivets:
        for cx in (3, s - 4):
            for cy in (3, s - 4):
                d = (lx - cx) ** 2 + (ly - cy) ** 2
                sh = np.where(d < 2.2, 0.9, np.where(d < 4.5, 0.25, sh))
    sh += (noise(n, 10, seed) - 0.5) * 0.2
    return np.clip(sh, 0, 1), seam.astype(np.float32)


def truss(n: int, seed: int = 6):
    """A steel lattice girder across the tile: (shade, mask of steel)."""
    x, y = grid(n)
    t = n * 0.08
    top = (y > n * 0.12) & (y < n * 0.12 + t)
    bot = (y > n * 0.8) & (y < n * 0.8 + t)
    period = n / 2
    u = x % period
    diag = (np.abs(u - (y - n * 0.12) / (n * 0.68) * period) < t * 0.6) | (np.abs((period - u) - (y - n * 0.12) / (n * 0.68) * period) < t * 0.6)
    diag &= (y > n * 0.12) & (y < n * 0.8 + t)
    vert = (np.abs(u) < t * 0.5) & (y > n * 0.12) & (y < n * 0.8 + t)
    m = top | bot | diag | vert
    sh = 0.45 + 0.35 * ((y % (n * 0.8)) < t * 0.4) + (noise(n, 6, seed) - 0.5) * 0.3
    return np.clip(sh, 0, 1), m.astype(np.float32)


def pipes(n: int, count: int = 2, horizontal: bool = True, seed: int = 7):
    """Round pipes with flanges: (shade, mask)."""
    x, y = grid(n)
    a, b = (y, x) if horizontal else (x, y)
    s = n / count
    r = s * 0.28
    c = (a % s) - s * 0.5
    m = np.abs(c) < r
    u = c / r
    sh = 0.55 - 0.4 * u + 0.25 * (np.sqrt(np.clip(1 - u * u, 0, 1)) - 0.6)
    fl = (b % (n / 2)) < 3
    m2 = np.abs(c) < r * 1.25
    sh = np.where(fl & m2, sh + 0.1, sh)
    m = m | (fl & m2)
    return np.clip(sh, 0, 1), m.astype(np.float32)


def blinds(n: int, slats: int = 16, open_: float = 0.4):
    """Venetian blinds: light gaps between slats: (slat shade, gap mask)."""
    x, y = grid(n)
    s = n / slats
    ly = y % s
    gap = ly > s * (1 - open_)
    sh = 0.35 + 0.5 * (1 - ly / s)
    return np.clip(sh, 0, 1), gap.astype(np.float32)


def planks(n: int, count: int = 6, seed: int = 8):
    """Floor boards with grain and joints."""
    x, y = grid(n)
    s = n / count
    r = np.floor(y / s)
    rng = np.random.RandomState(seed)
    off = rng.rand(count) * n
    jx = (x + off[r.astype(int) % count]) % n
    joint = ((y % s) < 1) | (jx < 1)
    grain = np.sin((x * 0.15 + noise(n, 12, seed) * 6.0)) * 0.12
    t = rng.rand(count)[r.astype(int) % count]
    sh = 0.45 + 0.2 * t + grain - 0.25 * joint
    return np.clip(sh, 0, 1), joint.astype(np.float32)


def checker(n: int, count: int = 4):
    x, y = grid(n)
    s = n / count
    return (((x // s) + (y // s)) % 2).astype(np.float32)


def cables(n: int, count: int = 3, seed: int = 9):
    """Sagging cables across the tile: mask."""
    x, y = grid(n)
    rng = np.random.RandomState(seed)
    m = np.zeros((n, n), np.float32)
    for i in range(count):
        y0 = rng.rand() * n
        sag = 4 + rng.rand() * n * 0.12
        yy = y0 + sag * np.sin(np.pi * x / n) ** 2
        m = np.maximum(m, (np.abs(y - yy) < 1.2).astype(np.float32))
    return m


def lava(n: int, seed: int = 10):
    """Molten rock: bright cracks of melt between dark crusted plates (0 crust .. 1 white heat)."""
    v = noise(n, 20, seed, 4)
    w = noise(n, 9, seed + 1, 3)
    cracks = 1.0 - np.abs(v - 0.5) * 2.0
    heat = np.clip((cracks - 0.55) * 3.0, 0, 1) ** 1.3 + w * 0.25
    return np.clip(heat, 0, 1)


def save(path: str, rgb: np.ndarray) -> None:
    from PIL import Image
    Image.fromarray(rgb, "RGB").save(path, optimize=False, compress_level=9)
