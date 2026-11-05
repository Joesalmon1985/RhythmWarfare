"""The Bassment's procedural pixel art (docs/RUN_DUNGEON_MUSIC_PLAN.md 2b): the wizard's cellars under the club, in a cellar palette.

`build()` writes assets/story/bassment/textures/*.png and returns the manifest `textures` section {id: {file, size, metres}}:
  surfaces (opaque tiles, 64 or 128 px, tileable): brick, damp brick, piped brick, barrel stacks, crystal, fungus stone, mirror glass, iron plates, record shelves, cave rock, the echo chamber's pale carved ashlar, the warren's gnawed earth,
    planked doors, the hatch, kitchen tile, cabled brick, carved hands, brass; floors (flags, planks, grate, moss, kitchen checker, crystal, mirror, dirt, straw, pavement, water),
    ceilings (arches, pipes, rock, crystal, beams) and a dawn sky strip;
  billboards (`thing_*`, 128 x 128 RGBA, hard alpha): torch, crystal cluster, mushrooms, barrel, lamp, furnace, doorway, ladder, rope, cables, skull, coat rack, valve wheel, bones,
    stove, stone hand, a soft glow, a hanging sign;
  figures (`fig_<creature>_<idle|attack|struck>`, 128 x 128 RGBA): the ten creatures of tools/trial/make_creatures.py (64 x 64) enlarged two to one, an attack frame (a lunge, red
    rim) and a struck frame (flash), and the wizard.
Everything is deterministic (seeded generators, no clock). Only this repository's own drawings are used; nothing is downloaded.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
from PIL import Image

from . import lib
from .pixeltex import (BAYER8, bricks, cables, checker, grid, grime, hexc, mix_rgb, noise, panels, pipes, planks, quantise, ramp, rust, speckle, tiles)
from .tex_underworld import Sprite

OUT = os.path.join(lib.ROOT, "assets", "story", "bassment", "textures")

# ---- cellar palettes (dark to light) ---------------------------------------------------------------------------------------------------------------
BRICK = ramp("#0a0706", "#1c110d", "#2e1c14", "#47291b", "#633a24", "#80502f")
DAMP = ramp("#05070a", "#0c121a", "#141e2a", "#1f3040", "#2e4658", "#456478")
MORT = ramp("#050403", "#120d0a", "#241a14")
STONE = ramp("#07080a", "#12141a", "#1e222a", "#2c323c", "#3e4650", "#56606a")
WOOD = ramp("#0c0704", "#1e1109", "#32200f", "#4e3217", "#6e4a22", "#94682e")
IRON = ramp("#08090c", "#13151b", "#20232b", "#30343e", "#454a56", "#5f6574")
CRYSTAL = ramp("#06061a", "#0e1236", "#1a2060", "#2e3a9a", "#4a6ad0", "#82a8f0", "#d0e4ff")
VIOLET = ramp("#0e0620", "#241048", "#3e1c78", "#6a30b0", "#a060e0", "#d0a0ff")
FUNGUS = ramp("#03080a", "#08140f", "#0e2a1a", "#144a2a", "#1e7a3c", "#3cb85a", "#9af0a0")
GLASS = ramp("#04060a", "#0a1018", "#142030", "#243850", "#3a5878", "#6a90b4", "#cfe6f4")
GOLD = ramp("#1c0e02", "#4a2c08", "#8a5a12", "#c8901e", "#f0c850", "#fff0a8")
TILE = ramp("#0e0f12", "#2a2c30", "#4a4d52", "#6e7278", "#9aa0a6", "#c8ccd0")
WATER = ramp("#02060a", "#06121c", "#0a2234", "#0e3a52", "#1a5c78", "#3a90a8", "#9adce8")
STRAW = ramp("#120c04", "#2a1c0a", "#4a3414", "#7a5a22", "#a8842e", "#d4b04c")
DIRT = ramp("#07050a", "#120d10", "#201820", "#32252a", "#483638", "#5e4a48")
PAVE = ramp("#1a1c22", "#2e313a", "#464a54", "#666a74", "#8a8e98", "#b0b4bc")
ECHO = ramp("#0c1018", "#1e2632", "#36414f", "#526073", "#76869c", "#a0afc4", "#ccd8e8")  # the echo chamber: cold pale stone
EARTH = ramp("#0a0503", "#1e0f06", "#36200c", "#563614", "#7a5020", "#a2702e")  # the warren: packed warm earth
FLAME = ramp("#3a0a04", "#8a1a06", "#e0480a", "#ff9a20", "#ffe070", "#fff8c8")


def _rgb(shade: np.ndarray, pal: np.ndarray, dither: float = 1.0) -> np.ndarray:
    return quantise(np.clip(shade, 0, 1), pal, dither)


def _col(rgb: np.ndarray, mask: np.ndarray, hexs: str) -> np.ndarray:
    out = rgb.copy()
    out[mask > 0.5] = (hexc(hexs) * 255).astype(np.uint8)
    return out


# ---- walls -------------------------------------------------------------------------------------------------------------------------------------------

def wall_brick(n=128):
    sh, m = bricks(n, rows=10, cols=4, mortar=1, seed=501, wear=0.45)
    sh = sh * (1.0 - 0.5 * grime(n, 502, 0.8))
    rgb = _rgb(sh, BRICK)
    return np.where((m > 0.5)[..., None], _rgb(0.35 + (noise(n, 4, 503) - 0.5) * 0.5, MORT), rgb), 2.5


def wall_brick_dark(n=128):
    sh, m = bricks(n, rows=8, cols=4, mortar=1, seed=511, wear=0.6)
    wet = np.clip((noise(n, 24, 512, 3) - 0.4) * 2.2, 0, 1)
    sh = sh * 0.8 + 0.12 * wet
    rgb = _rgb(sh, DAMP)
    rgb = np.where((m > 0.5)[..., None], _rgb(0.3 + (noise(n, 4, 513) - 0.5) * 0.4, MORT), rgb)
    return _col(rgb, speckle(n, 0.004, 514) * wet, "#7fc8d8"), 2.5


def wall_pipe(n=128):
    sh, m = bricks(n, rows=8, cols=4, mortar=1, seed=521, wear=0.4)
    rgb = _rgb(sh * 0.8, BRICK)
    rgb = np.where((m > 0.5)[..., None], _rgb(np.full((n, n), 0.3, np.float32), MORT), rgb)
    ps, pm = pipes(n, count=2, horizontal=True, seed=522)
    pr = _rgb(ps * 0.9 - 0.05 + rust(n, 523, 0.7) * 0.1, IRON)
    pr = _col(pr, (rust(n, 523, 0.8) > 0.5) & (pm > 0.5), "#7a3010")
    return np.where((pm > 0.5)[..., None], pr, rgb), 2.5


def wall_cable(n=128):
    sh, m = bricks(n, rows=10, cols=4, mortar=1, seed=531, wear=0.4)
    rgb = _rgb(sh * 0.75, DAMP)
    rgb = np.where((m > 0.5)[..., None], _rgb(np.full((n, n), 0.25, np.float32), MORT), rgb)
    for k, c in enumerate(("#101010", "#2a2a30", "#6a2a20", "#1a3a2a")):
        cm = cables(n, count=2, seed=540 + k)
        rgb = _col(rgb, cm, c)
    return rgb, 2.5


def wall_barrel(n=128):
    """Barrel ends and staves stacked in a rack: round oak heads with iron hoops on a dark shelf frame."""
    x, y = grid(n)
    sh = np.full((n, n), 0.15, np.float32)
    rgb = _rgb(sh, WOOD)
    s = n / 2.0
    for r in range(2):
        for c in range(2):
            cx, cy = (c + 0.5) * s + (r % 2) * s * 0.0, (r + 0.5) * s
            d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            head = d < s * 0.46
            ring = (d > s * 0.40) & (d < s * 0.46)
            plank = 0.45 + 0.2 * np.sin((x - cx) * 0.55 + noise(n, 10, 550 + r * 2 + c) * 5) + (noise(n, 6, 560 + c) - 0.5) * 0.2
            rgb = np.where(head[..., None], _rgb(plank - 0.2 * (d / s), WOOD), rgb)
            rgb = np.where(ring[..., None], _rgb(np.full((n, n), 0.45, np.float32), IRON), rgb)
            tap = d < s * 0.06
            rgb = _col(rgb, tap.astype(np.float32), "#1a0e06")
    return rgb, 2.0


def wall_crystal(n=128):
    """Faceted crystal columns: vertical prisms in blue and violet, bright edges, sparks."""
    x, y = grid(n)
    k = 5
    w = n / k
    i = (x // w).astype(int) % k
    lx = (x % w) / w
    rng = np.random.RandomState(571)
    tone = rng.rand(k)[i]
    facet = np.where(lx < 0.5, lx * 2, (1 - lx) * 2)
    tilt = np.sin((y / n + tone) * np.pi * 2) * 0.12
    sh = 0.25 + 0.4 * tone * facet + 0.25 * (facet > 0.82) + tilt + (noise(n, 10, 572) - 0.5) * 0.15
    pal = np.where((i % 2 == 0)[..., None], 0, 1)
    a = _rgb(sh, CRYSTAL)
    b = _rgb(sh, VIOLET)
    rgb = np.where((pal > 0), b, a)
    rgb = _col(rgb, speckle(n, 0.004, 573) * (facet > 0.4), "#e8f4ff")
    return rgb, 2.5


def wall_fungus(n=128):
    sh, m = bricks(n, rows=6, cols=3, mortar=1, seed=581, wear=0.7)
    base = _rgb(0.25 + sh * 0.35, STONE)
    glow = np.clip((noise(n, 18, 582, 4) - 0.5) * 3.0, 0, 1)
    rgb = np.where((glow > 0.05)[..., None], _rgb(0.15 + glow * 0.8, FUNGUS), base)
    return _col(rgb, speckle(n, 0.01, 583) * (glow > 0.2), "#c8ffb0"), 2.5


def wall_mirror(n=128):
    """Tall mirrors in dark frames: a cool gradient with a diagonal glint and a faint stranger's silhouette."""
    x, y = grid(n)
    k = 2
    w = n / k
    lx = x % w
    frame = (lx < 5) | (lx > w - 5) | (y < 6) | (y > n - 6)
    g = 0.35 + 0.25 * (y / n) + 0.35 * np.clip(1 - np.abs(((x + y * 0.6) % (n * 0.7)) - n * 0.3) / 6.0, 0, 1)
    fig = (np.abs(lx - w * 0.5) < 6 + 4 * np.clip(1 - y / (n * 0.35), 0, 1)) & (y > n * 0.2) & (y < n * 0.9)
    g = np.where(fig, g - 0.18, g)
    rgb = _rgb(g, GLASS)
    return np.where(frame[..., None], _rgb(0.35 + 0.2 * (lx < 2) + (noise(n, 4, 591) - 0.5) * 0.2, GOLD), rgb), 3.0


def wall_iron(n=128):
    sh, seam = panels(n, count=2, seed=601, rivets=True)
    r = rust(n, 602, 0.8)
    rgb = _rgb(sh * 0.9 - 0.2 * grime(n, 603, 0.5), IRON)
    return _col(rgb, (r > 0.5) * (seam < 0.5), "#6a2a10"), 2.0


def wall_shelf(n=128):
    """Stone shelves packed with old records: dark spines in rows, brass labels."""
    x, y = grid(n)
    rows = 4
    s = n / rows
    ly = y % s
    shelf = ly > s - 6
    rng = np.random.RandomState(611)
    cols = n // 5
    tone = rng.rand(rows, cols + 1)
    ri = (y // s).astype(int) % rows
    ci = (x // 5).astype(int) % (cols + 1)
    t = tone[ri, ci]
    spine = 0.15 + 0.35 * t + 0.15 * ((x % 5) < 1)
    rgb = _rgb(spine, np.vstack([WOOD[:3], DAMP[2:5], VIOLET[1:4]]))
    lab = (ly > s * 0.35) & (ly < s * 0.5) & ((x % 5) > 1) & (t > 0.55)
    rgb = _col(rgb, lab.astype(np.float32), "#c8a04a")
    return np.where(shelf[..., None], _rgb(0.35 + (noise(n, 4, 612) - 0.5) * 0.3, STONE), rgb), 2.0


def wall_rock(n=128):
    from .tex_underworld import cave_rock  # noqa: F401  (not used: this one is cooler)
    v = noise(n, 22, 621, 4)
    ridges = 1 - np.abs(noise(n, 12, 622, 3) - 0.5) * 2
    sh = 0.2 + 0.4 * v + 0.2 * ridges ** 3
    sh *= 1.0 - 0.3 * grime(n, 623, 0.7)
    return _rgb(sh, STONE), 3.0


def wall_echo(n=128):
    """The echo chamber's bare stone: long pale ashlar courses, cold and clean, with the rings of a sound carved faintly across them (they tile: a toroidal distance)."""
    sh, m = bricks(n, rows=4, cols=2, mortar=1, seed=681, wear=0.2)
    x, y = grid(n)
    dx = np.minimum(np.abs(x - n / 2), n - np.abs(x - n / 2))
    dy = np.minimum(np.abs(y - n / 2), n - np.abs(y - n / 2))
    d = np.sqrt(dx * dx + dy * dy)
    groove = (np.sin(d * 0.42) > 0.9) & (d < n * 0.5)
    sh = sh * 0.75 + 0.18 + (noise(n, 10, 682, 3) - 0.5) * 0.12 - 0.12 * groove - 0.1 * grime(n, 683, 0.35, drip=False)
    rgb = _rgb(sh, ECHO)
    return np.where((m > 0.5)[..., None], _rgb(np.full((n, n), 0.18, np.float32), ECHO), rgb), 3.0


def wall_burrow(n=128):
    """The warren's walls: packed earth in warm layers, gnawed into, with the round black mouths of rat holes (a lit lip under each) and gnaw scratches."""
    x, y = grid(n)
    strata = 0.5 + 0.5 * np.sin(y * 0.28 + noise(n, 16, 691, 3) * 5.0)
    sh = 0.32 + 0.22 * noise(n, 12, 692, 4) + 0.14 * strata
    rng = np.random.RandomState(693)
    hole = np.zeros((n, n), bool)
    lip = np.zeros((n, n), bool)
    for _ in range(5):
        cx, cy, rx = rng.rand() * n, rng.rand() * n, 5 + rng.rand() * 6
        ddx = np.minimum(np.abs(x - cx), n - np.abs(x - cx))
        ddy = np.minimum(np.abs(y - cy), n - np.abs(y - cy))
        e = (ddx / rx) ** 2 + (ddy / (rx * 0.7)) ** 2
        hole |= e < 1.0
        lip |= (e >= 1.0) & (e < 1.7) & (((y - cy) % n) < n / 2) & (((y - cy) % n) > 0)
    scratch = np.zeros((n, n), bool)
    for _ in range(14):
        sx, sy, ln = rng.rand() * n, rng.rand() * n, 4 + int(rng.rand() * 5)
        for k in range(ln):
            scratch[int(sy + k) % n, int(sx + k * 0.6) % n] = True
            scratch[int(sy + k) % n, int(sx + 2 + k * 0.6) % n] = True
    sh = sh + 0.3 * lip - 0.12 * scratch
    rgb = _rgb(sh, EARTH)
    rgb = _col(rgb, scratch.astype(np.float32) * (rng.rand(n, n) < 0.6), "#b07a3c")
    rgb = _col(rgb, speckle(n, 0.006, 694), "#c89a58")
    return np.where(hole[..., None], _rgb(np.full((n, n), 0.04, np.float32), EARTH), rgb), 3.0


def wall_door(n=128):
    """A plank door with iron straps and a ring, for the exits."""
    x, y = grid(n)
    pl = (x // (n / 5)).astype(int)
    rng = np.random.RandomState(631)
    t = rng.rand(5)[pl % 5]
    grain = np.sin(y * 0.2 + noise(n, 10, 632) * 6) * 0.1
    sh = 0.35 + 0.25 * t + grain - 0.25 * ((x % (n / 5)) < 1.5)
    rgb = _rgb(sh, WOOD)
    strap = ((y > n * 0.18) & (y < n * 0.26)) | ((y > n * 0.72) & (y < n * 0.8))
    rgb = np.where(strap[..., None], _rgb(0.4 + (noise(n, 3, 633) - 0.5) * 0.3, IRON), rgb)
    ring = ((x - n * 0.72) ** 2 + (y - n * 0.52) ** 2 < 49) & ((x - n * 0.72) ** 2 + (y - n * 0.52) ** 2 > 20)
    return _col(rgb, ring.astype(np.float32), "#b08a3a"), 3.0


def wall_hatch(n=128):
    x, y = grid(n)
    sh, seam = panels(n, count=1, seed=641, rivets=True)
    d = np.sqrt((x - n / 2) ** 2 + (y - n / 2) ** 2)
    rgb = _rgb(sh * 0.8 - 0.1 * grime(n, 642, 0.6), IRON)
    ring = (d > n * 0.36) & (d < n * 0.4)
    wheel = (np.abs(x - n / 2) < 4) | (np.abs(y - n / 2) < 4)
    rgb = np.where(ring[..., None], _rgb(np.full((n, n), 0.7, np.float32), IRON), rgb)
    rgb = _col(rgb, wheel & (d < n * 0.3), "#6a4a20")
    return _col(rgb, (d < 6), "#a08040"), 3.0


def wall_tile(n=64):
    sh, g = tiles(n, count=4, grout=1, seed=651, gloss=0.4)
    rgb = _rgb(sh * (1 - 0.35 * grime(n, 652, 0.9)), TILE)
    return np.where((g > 0.5)[..., None], _rgb(np.full((n, n), 0.15, np.float32), TILE), rgb), 1.5


def wall_hands(n=128):
    """Stone carved with rows of open hands, palms out."""
    x, y = grid(n)
    base = _rgb(0.25 + (noise(n, 14, 661, 3) - 0.5) * 0.3, STONE)
    sp = Sprite(n)
    for r in range(2):
        for c in range(2):
            cx, cy = (c + 0.5) * n / 2, (r + 0.55) * n / 2
            sp.paint(sp.ellipse(cx, cy + 6, 11, 13), 0.55, STONE)
            for k, ang in enumerate((-0.7, -0.3, 0.0, 0.3, 0.7)):
                fx, fy = cx + np.sin(ang) * 16, cy - 6 - np.cos(ang) * 16
                sp.paint(sp.line(cx + np.sin(ang) * 6, cy, fx, fy, 4.5 if k else 5.5), 0.5 + 0.1 * k / 4, STONE)
    carved = sp.a > 0
    rgb = np.where(carved[..., None], sp.rgb, base)
    edge = carved & ~np.roll(carved, 1, 0)
    return _col(rgb, edge, "#0a0c10"), 3.0


def wall_brass(n=128):
    x, y = grid(n)
    d = np.sqrt((x - n / 2) ** 2 + (y - n / 2) ** 2)
    rings = 0.5 + 0.5 * np.sin(d * 0.9)
    sh = 0.35 + 0.3 * rings + (noise(n, 8, 671) - 0.5) * 0.15 - 0.15 * (d > n * 0.46)
    rgb = _rgb(sh, GOLD)
    return _col(rgb, speckle(n, 0.01, 672), "#fff0b0"), 3.0


# ---- floors and ceilings --------------------------------------------------------------------------------------------------------------------------

def floor_flag(n=128):
    sh, g = tiles(n, count=3, grout=1, seed=701, gloss=0.1)
    sh = sh * 0.8 - 0.15 * grime(n, 702, 0.8, drip=False)
    rgb = _rgb(sh, STONE)
    return np.where((g > 0.5)[..., None], _rgb(np.full((n, n), 0.1, np.float32), STONE), rgb), 2.5


def floor_wood(n=128):
    sh, j = planks(n, count=6, seed=711)
    return _rgb(sh * 0.9 - 0.15 * grime(n, 712, 0.6, drip=False), WOOD), 2.5


def floor_grate(n=64):
    x, y = grid(n)
    bars = ((x % 8) < 3) | ((y % 16) < 2)
    rgb = _rgb(0.4 + (noise(n, 6, 721) - 0.5) * 0.3, IRON)
    void = np.where(bars[..., None], rgb, _rgb(np.full((n, n), 0.0, np.float32), WATER))
    return void, 2.0


def floor_moss(n=128):
    v = noise(n, 14, 731, 4)
    base = _rgb(0.2 + 0.3 * v, DIRT)
    moss = np.clip((noise(n, 10, 732, 3) - 0.45) * 3, 0, 1)
    rgb = np.where((moss > 0.1)[..., None], _rgb(0.15 + moss * 0.7, FUNGUS), base)
    return _col(rgb, speckle(n, 0.006, 733) * (moss > 0.3), "#d0ffc0"), 3.0


def floor_kitchen(n=64):
    c = checker(n, 4)
    sh = 0.25 + 0.4 * c + (noise(n, 8, 741) - 0.5) * 0.12 - 0.2 * grime(n, 742, 0.9, drip=False)
    return _rgb(sh, TILE), 2.0


def floor_crystal(n=128):
    from .tex_underworld import _worley
    f1, f2, ids = _worley(n, 4, 751)
    sh = 0.25 + 0.35 * np.random.RandomState(752).rand(16)[ids % 16] + 0.3 * np.clip(1 - (f2 - f1) / 2.5, 0, 1)
    rgb = np.where(((ids % 3) == 0)[..., None], _rgb(sh, VIOLET), _rgb(sh, CRYSTAL))
    return rgb, 3.0


def floor_mirror(n=64):
    c = checker(n, 2)
    x, y = grid(n)
    sh = 0.15 + 0.2 * c + 0.4 * np.clip(1 - np.abs(((x + y) % (n * 0.8)) - n * 0.3) / 5.0, 0, 1)
    return _rgb(sh, GLASS), 2.0


def floor_dirt(n=128):
    return _rgb(0.25 + 0.4 * noise(n, 16, 761, 4) - 0.2 * grime(n, 762, 0.7, drip=False), DIRT), 3.0


def floor_straw(n=128):
    x, y = grid(n)
    rng = np.random.RandomState(771)
    sh = 0.35 + 0.3 * noise(n, 6, 772, 3) + 0.2 * (np.sin(x * 0.7 + y * 0.45 + rng.rand() * 6) > 0.7)
    return _rgb(sh, STRAW), 2.5


def floor_pavement(n=128):
    sh, g = tiles(n, count=2, grout=1, seed=781, gloss=0.0)
    sh = sh * 0.9 + (noise(n, 6, 782) - 0.5) * 0.2
    return np.where((g > 0.5)[..., None], _rgb(np.full((n, n), 0.1, np.float32), PAVE), _rgb(sh, PAVE)), 3.0


def water(n=64, phase=0):
    """Black water with moving caustic light: four frames (swap) and the base tile."""
    x, y = grid(n)
    a = np.sin((x + phase * n / 8) / n * 2 * np.pi * 2 + noise(n, 12, 791) * 5) * np.sin((y - phase * n / 8) / n * 2 * np.pi * 2 + noise(n, 12, 792) * 5)
    caustic = np.clip(1 - np.abs(a) * 3.0, 0, 1) ** 2
    sh = 0.18 + 0.25 * noise(n, 14, 793, 3) + 0.55 * caustic
    return _rgb(sh, WATER), 3.0


def ceil_arch(n=128):
    sh, m = bricks(n, rows=6, cols=3, mortar=1, seed=801, wear=0.5)
    return np.where((m > 0.5)[..., None], _rgb(np.full((n, n), 0.2, np.float32), MORT), _rgb(sh * 0.55, BRICK)), 2.5


def ceil_pipes(n=128):
    ps, pm = pipes(n, count=2, horizontal=False, seed=811)
    base = _rgb(0.12 + (noise(n, 10, 812) - 0.5) * 0.15, BRICK)
    return np.where((pm > 0.5)[..., None], _rgb(ps * 0.8, IRON), base), 2.5


def ceil_rock(n=64):
    return _rgb(0.1 + 0.3 * noise(n, 14, 821, 4), STONE), 3.0


def ceil_crystal(n=64):
    return _rgb(0.12 + 0.4 * noise(n, 8, 831, 3) + 0.4 * speckle(n, 0.02, 832), CRYSTAL), 3.0


def ceil_beams(n=64):
    sh, j = planks(n, count=3, seed=841)
    return _rgb(sh * 0.6, WOOD), 2.0


def sky_dawn():
    """The car park's morning: a strip that wraps once around the world, deep blue at the top to a rose-gold horizon."""
    w, h = 256, 64
    y = np.mgrid[0:h, 0:w][0].astype(np.float32) / h
    x = np.mgrid[0:h, 0:w][1].astype(np.float32) / w
    top = np.array([0.12, 0.16, 0.38])
    mid = np.array([0.82, 0.5, 0.5])
    low = np.array([1.0, 0.82, 0.5])
    t = np.clip(y, 0, 1)[..., None]
    col = np.where(t < 0.6, top + (mid - top) * (t / 0.6), mid + (low - mid) * ((t - 0.6) / 0.4))
    col += (noise(256, 40, 851, 2)[:h, :w, None] - 0.5) * 0.06
    sun = np.exp(-(((x - 0.5) * 6) ** 2 + ((y - 0.92) * 5) ** 2) * 2)[..., None]
    col = np.clip(col + sun * np.array([0.5, 0.4, 0.2]), 0, 1)
    b = BAYER8[np.arange(h)[:, None] % 8, np.arange(w)[None, :] % 8][..., None]
    return (np.clip(np.round(col * 12 + b * 0.9) / 12, 0, 1) * 255).astype(np.uint8)


# ---- props (RGBA billboards) --------------------------------------------------------------------------------------------------------------------------

def _flame(sp: Sprite, cx, base_y, w, h, seed):
    rng = np.random.RandomState(seed)
    nz = noise(sp.n, 6, seed, 2)
    for k in range(3):
        fx = cx + (k - 1) * w * 0.2 + rng.uniform(-1, 1)
        fh = h * (0.6 + 0.4 * rng.rand()) * (1.0 - abs(k - 1) * 0.25)
        u = (base_y - sp.y) / fh
        wid = w * 0.24 * np.clip(1 - u, 0, 1) ** 0.8 * (0.8 + 0.4 * nz)
        m = (u >= 0) & (u <= 1) & (np.abs(sp.x - fx) < wid)
        sp.paint(m, np.clip(1.0 - u * 1.1, 0.1, 1) * 0.9, FLAME)


def th_torch():
    sp = Sprite()
    sp.paint(sp.line(64, 124, 64, 70, 8), 0.4, WOOD)
    sp.paint(sp.rect(50, 64, 78, 76), 0.55, IRON)
    sp.paint(sp.rect(52, 74, 76, 80), 0.3, IRON)
    _flame(sp, 64, 66, 52, 60, 901)
    return sp.rgba()


def th_crystal():
    sp = Sprite()
    for cx, base, h, w, tone in ((64, 124, 108, 18, 0.7), (38, 124, 70, 14, 0.5), (92, 124, 82, 15, 0.6), (22, 124, 40, 10, 0.4), (108, 124, 46, 10, 0.5)):
        pts = [(cx - w, base), (cx - w * 0.7, base - h * 0.8), (cx, base - h), (cx + w * 0.7, base - h * 0.8), (cx + w, base)]
        m = sp.tri(pts[:3] + [pts[3], pts[4]]) if False else (sp.tri([pts[0], pts[2], pts[4]]) | sp.tri([pts[0], pts[1], pts[2]]) | sp.tri([pts[2], pts[3], pts[4]]))
        u = np.clip((sp.x - (cx - w)) / (2 * w), 0, 1)
        sp.paint(m, tone + 0.35 * (1 - u) - 0.2 * (u > 0.7), CRYSTAL if cx != 38 else VIOLET)
    return sp.rgba()


def th_mushroom():
    sp = Sprite()
    for cx, base, h, r in ((44, 124, 60, 24), (86, 124, 40, 16), (66, 124, 28, 12), (24, 124, 24, 10)):
        sp.paint(sp.rect(cx - 4, base - h, cx + 4, base), 0.5 + (sp.x - cx) * 0.03, FUNGUS)
        cap = sp.ellipse(cx, base - h, r, r * 0.6) & (sp.y <= base - h + 2)
        sp.paint(cap, 0.35 + 0.5 * np.clip(1 - (sp.y - (base - h - r * 0.6)) / (r * 0.6), 0, 1), FUNGUS)
        sp.solid(sp.ellipse(cx - r * 0.3, base - h - r * 0.25, 2.5, 2.5), "#e8ffd0")
        sp.solid(sp.ellipse(cx + r * 0.35, base - h - r * 0.15, 2, 2), "#e8ffd0")
    return sp.rgba()


def th_barrel():
    sp = Sprite()
    body = sp.ellipse(64, 76, 40, 50) & (sp.y > 30) & (sp.y < 122)
    u = np.clip((sp.x - 24) / 80, 0, 1)
    sp.paint(body, 0.55 - 0.4 * u + 0.15 * np.sin(sp.x * 0.9), WOOD)
    for hy in (42, 62, 92, 112):
        hoop = body & (np.abs(sp.y - hy) < 3)
        sp.paint(hoop, 0.35 + 0.3 * (1 - u), IRON)
    sp.solid(sp.ellipse(64, 76, 4, 4) & (sp.y > 70), "#120a04")
    return sp.rgba()


def th_lamp():
    sp = Sprite()
    sp.paint(sp.rect(60, 20, 68, 36), 0.4, IRON)
    sp.paint(sp.ellipse(64, 70, 26, 30), 0.5, GOLD)
    glass = sp.ellipse(64, 70, 18, 22)
    sp.paint(glass, 0.8 - 0.3 * np.clip((sp.y - 50) / 40, 0, 1), FLAME)
    sp.paint(sp.rect(44, 96, 84, 108), 0.5, GOLD)
    sp.paint(sp.rect(50, 108, 78, 114), 0.35, GOLD)
    return sp.rgba()


def th_furnace():
    sp = Sprite()
    sp.paint(sp.rect(14, 24, 114, 124), 0.2 + 0.12 * noise(128, 6, 902), IRON)
    sp.paint(sp.rect(14, 24, 114, 32), 0.55, IRON)
    mouth = sp.ellipse(64, 84, 34, 30) & (sp.y > 56)
    sp.paint(mouth, 0.2 + 0.7 * np.clip(1 - np.abs(sp.y - 100) / 40, 0, 1) * (0.6 + 0.4 * noise(128, 5, 903)), FLAME)
    for rx in range(22, 110, 14):
        sp.solid(sp.ellipse(rx, 29, 2, 2), "#8a8494")
    return sp.rgba()


def th_door():
    """A lit arched doorway: a stone surround and a warm bright opening."""
    sp = Sprite()
    sp.paint(sp.rect(18, 38, 110, 128) | sp.ellipse(64, 40, 46, 30), 0.35 + 0.15 * noise(128, 6, 904), STONE)
    op = sp.rect(32, 44, 96, 128) | sp.ellipse(64, 46, 32, 24)
    u = np.clip((sp.y - 22) / 100, 0, 1)
    sp.paint(op, 0.95 - 0.5 * u, FLAME)
    return sp.rgba()


def th_ladder():
    sp = Sprite()
    for x0 in (40, 84):
        sp.paint(sp.rect(x0, 0, x0 + 6, 128), 0.55 + (sp.x - x0) * 0.03, WOOD)
    for y0 in range(8, 128, 18):
        sp.paint(sp.rect(40, y0, 90, y0 + 5), 0.5, IRON)
    return sp.rgba()


def th_rope():
    sp = Sprite()
    sp.paint(sp.line(64, 0, 64, 128, 7), 0.5 + 0.3 * np.sin(sp.y * 0.8), STRAW)
    sp.paint(sp.ellipse(64, 118, 11, 11), 0.5, STRAW)
    return sp.rgba()


def th_cables():
    sp = Sprite()
    for i, (x0, c) in enumerate(((30, "#14141a"), (52, "#3a1a16"), (76, "#14241c"), (98, "#26262e"))):
        pts = [(x0 + np.sin(y * 0.05 + i) * 6, y) for y in range(0, 128, 4)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            sp.solid(sp.line(ax, ay, bx, by, 6), c)
    sp.solid(sp.rect(20, 56, 108, 80), "#2a2a34")
    sp.solid(sp.ellipse(36, 68, 3, 3), "#40ff60")
    sp.solid(sp.ellipse(92, 68, 3, 3), "#ff5040")
    return sp.rgba()


def th_skull():
    sp = Sprite()
    sp.paint(sp.ellipse(64, 70, 30, 34), 0.7 - 0.3 * np.clip((sp.x - 34) / 60, 0, 1), STRAW)
    sp.paint(sp.rect(48, 88, 80, 108), 0.55, STRAW)
    sp.solid(sp.ellipse(52, 68, 8, 9), "#0a0608")
    sp.solid(sp.ellipse(76, 68, 8, 9), "#0a0608")
    sp.solid(sp.tri([(64, 78), (60, 90), (68, 90)]), "#0a0608")
    for tx in range(52, 78, 6):
        sp.solid(sp.rect(tx, 96, tx + 2, 106), "#201408")
    return sp.rgba()


def th_coatrack():
    sp = Sprite()
    sp.paint(sp.rect(60, 12, 68, 122), 0.5, WOOD)
    sp.paint(sp.ellipse(64, 122, 30, 6), 0.4, WOOD)
    for (cx, cy, c, h) in ((40, 40, "#4a1a2a", 50), (88, 46, "#1a2a4a", 44), (52, 78, "#2a3a22", 40)):
        sp.solid(sp.tri([(cx - 16, cy + h), (cx + 16, cy + h), (cx, cy)]) | sp.rect(cx - 12, cy + 4, cx + 12, cy + h), c)
    sp.solid(sp.line(30, 30, 98, 30, 3), "#8a6a3a")
    return sp.rgba()


def th_valve():
    sp = Sprite()
    sp.paint(sp.rect(60, 70, 68, 128), 0.4, IRON)
    ring = sp.ellipse(64, 56, 38, 38) & ~sp.ellipse(64, 56, 30, 30)
    sp.paint(ring, 0.6 - 0.3 * np.clip((sp.x - 26) / 76, 0, 1), IRON)
    sp.paint(sp.rect(26, 52, 102, 60) | sp.rect(60, 18, 68, 94), 0.5, IRON)
    sp.solid(sp.ellipse(64, 56, 6, 6), "#8a3a20")
    return sp.rgba()


def th_bones():
    sp = Sprite()
    for (ax, ay, bx, by) in ((20, 112, 100, 96), (30, 98, 108, 118), (50, 120, 90, 80)):
        sp.paint(sp.line(ax, ay, bx, by, 6), 0.7, STRAW)
        sp.paint(sp.ellipse(ax, ay, 6, 6) | sp.ellipse(bx, by, 6, 6), 0.8, STRAW)
    sp.paint(sp.ellipse(88, 100, 16, 14), 0.75, STRAW)
    sp.solid(sp.ellipse(84, 98, 3, 4) | sp.ellipse(94, 98, 3, 4), "#0a0608")
    return sp.rgba()


def th_stove():
    sp = Sprite()
    sp.paint(sp.rect(10, 44, 118, 124), 0.25 + 0.1 * noise(128, 6, 905), TILE)
    sp.paint(sp.rect(10, 40, 118, 50), 0.7, IRON)
    for cx in (34, 64, 94):
        sp.paint(sp.ellipse(cx, 44, 14, 5), 0.2, IRON)
        sp.solid(sp.ellipse(cx, 44, 8, 2.5), "#ff7a1a")
    sp.paint(sp.rect(24, 70, 104, 116), 0.2, IRON)
    sp.solid(sp.rect(30, 76, 98, 110), "#1a0c08")
    sp.paint(sp.ellipse(64, 24, 30, 16) & (sp.y > 14), 0.55, IRON)
    sp.paint(sp.rect(36, 24, 92, 38), 0.45, IRON)
    return sp.rgba()


def th_hand():
    sp = Sprite()
    sp.paint(sp.rect(52, 84, 78, 128), 0.45, STONE)
    sp.paint(sp.ellipse(64, 72, 30, 28), 0.55 - 0.2 * np.clip((sp.x - 34) / 60, 0, 1), STONE)
    for k, ang in enumerate((-0.75, -0.35, 0.0, 0.35, 0.75)):
        ln = 44 if k in (1, 2, 3) else 34
        sp.paint(sp.line(64 + np.sin(ang) * 14, 70, 64 + np.sin(ang) * ln, 70 - np.cos(ang) * ln, 10), 0.55 + 0.05 * k, STONE)
    return sp.rgba()


def th_glow():
    sp = Sprite()
    d = np.sqrt((sp.x - 64) ** 2 + (sp.y - 64) ** 2) / 64.0
    a = np.clip(1 - d, 0, 1) ** 2
    sp.rgb[...] = (255, 240, 210)
    sp.a = (a * 255).astype(np.uint8)
    return sp.rgba()


def th_sign():
    sp = Sprite()
    sp.paint(sp.line(64, 0, 64, 40, 4), 0.4, IRON)
    sp.paint(sp.rect(18, 40, 110, 96), 0.4 + 0.1 * noise(128, 5, 906), WOOD)
    sp.paint(sp.rect(18, 40, 110, 44) | sp.rect(18, 92, 110, 96), 0.7, GOLD)
    for tx in range(30, 100, 14):
        sp.solid(sp.rect(tx, 58, tx + 8, 76), "#c8a04a")
    return sp.rgba()


PROPS = {"thing_torch": th_torch, "thing_crystal": th_crystal, "thing_mushroom": th_mushroom, "thing_barrel": th_barrel, "thing_lamp": th_lamp, "thing_furnace": th_furnace,
         "thing_door": th_door, "thing_ladder": th_ladder, "thing_rope": th_rope, "thing_cables": th_cables, "thing_skull": th_skull, "thing_coatrack": th_coatrack,
         "thing_valve": th_valve, "thing_bones": th_bones, "thing_stove": th_stove, "thing_hand": th_hand, "thing_glow": th_glow, "thing_sign": th_sign}

TILES = {"wall_brick": wall_brick, "wall_brick_dark": wall_brick_dark, "wall_pipe": wall_pipe, "wall_cable": wall_cable, "wall_barrel": wall_barrel, "wall_crystal": wall_crystal,
         "wall_fungus": wall_fungus, "wall_mirror": wall_mirror, "wall_iron": wall_iron, "wall_shelf": wall_shelf, "wall_rock": wall_rock, "wall_door": wall_door,
         "wall_hatch": wall_hatch, "wall_tile": wall_tile, "wall_hands": wall_hands, "wall_brass": wall_brass, "wall_echo": wall_echo, "wall_burrow": wall_burrow,
         "floor_flag": floor_flag, "floor_wood": floor_wood, "floor_grate": floor_grate, "floor_moss": floor_moss, "floor_kitchen": floor_kitchen, "floor_crystal": floor_crystal,
         "floor_mirror": floor_mirror, "floor_dirt": floor_dirt, "floor_straw": floor_straw, "floor_pavement": floor_pavement, "water": water,
         "ceil_arch": ceil_arch, "ceil_pipes": ceil_pipes, "ceil_rock": ceil_rock, "ceil_crystal": ceil_crystal, "ceil_beams": ceil_beams}


# ---- figures ------------------------------------------------------------------------------------------------------------------------------------------

CREATURES = ["lampmoth", "cable_eel", "barrel_knight", "mildew_mother", "mirror_twin", "bouncer", "rat_king", "furnace_imp", "gargoyle", "echo"]


def _creature_frames() -> dict:
    """{id: (idle, attack, struck)} as 128 x 128 RGBA arrays from the 64 x 64 portraits tools/trial/make_creatures.py draws."""
    sys.path.insert(0, os.path.join(lib.ROOT, "tools", "trial"))
    import importlib
    mc = importlib.import_module("make_creatures")
    out = {}
    for name in CREATURES:
        fr = []
        for hit in (False, True):
            im, d = mc.canvas()
            mc.CREATURES[name](d, hit)
            fr.append(mc.finish(im, hit))
        idle, struck = fr
        big = idle.resize((128, 128), Image.NEAREST)
        a = np.asarray(big).copy()
        # attack: leaning into the camera (a shear to the left and a stretch), a red rim, eyes unchanged
        h, w = a.shape[:2]
        att = np.zeros_like(a)
        for yy in range(h):
            shift = int((h - yy) * 0.12)
            row = a[yy]
            att[yy] = np.roll(row, -shift, 0)
        alpha = att[..., 3] > 0
        grown = alpha.copy()
        for dy, dx in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            grown |= np.roll(np.roll(alpha, dy, 0), dx, 1)
        rim = grown & ~alpha
        att[rim] = (200, 40, 30, 255)
        rgb = att[..., :3].astype(np.float32)
        rgb[alpha] = rgb[alpha] * 0.85 + np.array([60, 0, 0]) * 0.5
        att[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
        out[name] = (np.asarray(big), att, np.asarray(struck.resize((128, 128), Image.NEAREST)))
    return out


def _wizard_frames() -> tuple:
    im = Image.open(os.path.join(lib.ROOT, "assets", "trial", "art", "wizard.png")).convert("RGBA").resize((128, 128), Image.NEAREST)
    a = np.asarray(im).copy()
    att = a.copy()
    glow = att[..., 3] > 0
    att[..., :3] = np.where(glow[..., None], np.clip(att[..., :3].astype(np.float32) * 1.25 + 20, 0, 255), att[..., :3]).astype(np.uint8)
    return a, att


def build() -> dict:
    os.makedirs(OUT, exist_ok=True)
    for fn in os.listdir(OUT):
        if fn.endswith(".png"):
            os.remove(os.path.join(OUT, fn))
    section = {}

    def reg(tid, path_arr, mode, metres):
        im = Image.fromarray(path_arr, mode)
        im.save(os.path.join(OUT, tid + ".png"), optimize=False, compress_level=9)
        section[tid] = {"file": f"textures/{tid}.png", "size": [im.width, im.height], "metres": metres}

    for tid in sorted(TILES):
        if tid == "water":
            continue
        rgb, metres = TILES[tid]()
        reg(tid, rgb, "RGB", metres)
    for k in range(4):  # the water: a base tile and four frames the map swaps through
        rgb, metres = water(64, k)
        reg("water" if k == 0 else f"water_{k}", rgb, "RGB", metres)
    reg("sky_dawn", sky_dawn(), "RGB", 1.0)
    for tid in sorted(PROPS):
        reg(tid, PROPS[tid](), "RGBA", 1.0)
    for name, (idle, att, struck) in sorted(_creature_frames().items()):
        reg(f"fig_{name}_idle", idle, "RGBA", 1.0)
        reg(f"fig_{name}_attack", att, "RGBA", 1.0)
        reg(f"fig_{name}_struck", struck, "RGBA", 1.0)
    w_idle, w_att = _wizard_frames()
    reg("fig_wizard_idle", w_idle, "RGBA", 1.0)
    reg("fig_wizard_attack", w_att, "RGBA", 1.0)
    return dict(sorted(section.items()))


def main() -> int:
    section = build()
    man_path = os.path.join(lib.ROOT, "assets", "story", "bassment", "manifest.json")
    man = {"version": 1, "level": "bassment", "px_scale_note": "the Bassment has no rigs; its world is textures only", "textures": section}
    with open(man_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print(f"bassment: {len(section)} textures, manifest {os.path.relpath(man_path, lib.ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
