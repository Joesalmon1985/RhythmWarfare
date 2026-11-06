"""The Bassment's procedural pixel art (docs/RUN_DUNGEON_MUSIC_PLAN.md 2b): the wizard's cellars under the club, in a cellar palette.

`build()` writes assets/story/bassment/textures/*.png and returns the manifest `textures` section {id: {file, size, metres}}:
  surfaces (opaque tiles, 128 px, tileable, 1.0 to 1.25 m each: 102 to 128 texels per metre, docs/art/STYLE_GUIDE.md section 7): brick, damp brick,
    piped brick, cabled brick, barrel racks, crystal columns, fungus stone, mirror panes, iron plates, record shelves, cave rock, the echo chamber's pale ashlar,
    the warren's gnawed earth, plank doors, the iron hatch, kitchen tile, carved hands, hammered brass; floors (flags, planks, grate, moss, kitchen checker,
    crystal, mirror tiles, dirt, straw, concrete, water in four frames), ceilings (brick vault, pipes, rock, crystal, beams) and a dawn sky strip;
  billboards (`thing_*`, 128 x 128 RGBA, hard alpha, a one-pixel edge two steps darker, lit from the upper left): torch, crystal cluster, mushrooms, barrel,
    lamp, furnace, lit doorway, ladder, rope, cables, skull, coat rack, valve wheel, bones, stove, stone hand, the hatch seen from below, a sign, and one soft
    glow (the only partial alpha: it is drawn additive);
  figures (`fig_<creature>_<idle|attack|struck>`, 128 x 128 RGBA): the ten creatures of tools/trial/make_creatures.py drawn at 128 (`make_creatures.frame`),
    and the wizard (the trial's wizard portrait cut out with hard alpha and reduced to 48 colours, as the Warehouse's thing_wizard).
Props and creatures share one painter (make_creatures.Painter), so a barrel, a skull and a Barrel Knight are drawn in the same pixels.
Everything is deterministic (seeded generators, no clock). Only this repository's own drawings are used; nothing is downloaded.
"""
from __future__ import annotations

import importlib
import json
import os
import sys

import numpy as np
from PIL import Image

from . import lib
from .pixeltex import BAYER8, grid, hexc, noise, quantise, ramp, speckle

OUT = os.path.join(lib.ROOT, "assets", "story", "bassment", "textures")
N = 128

# ---- cellar palettes (dark to light) ---------------------------------------------------------------------------------------------------------------
BRICK = ramp("#0e0908", "#1e140f", "#2e1f18", "#452d21", "#5e3e2c", "#785238", "#926a4c", "#aa8a6e")
DAMP = ramp("#070a0e", "#0e151d", "#16212d", "#213242", "#2e4658", "#43606f", "#5e7c88", "#86a0a8")
MORT = ramp("#0a0806", "#16100c", "#261c16", "#342820")
STONE = ramp("#090a0d", "#13161c", "#1e232b", "#2b313b", "#3c444f", "#525b66", "#6c7580", "#9098a0")
WOOD = ramp("#0e0805", "#1e1209", "#33210f", "#4c3117", "#664624", "#836034", "#9e7a4c", "#bc9a70")
IRON = ramp("#0a0b0f", "#15171d", "#22252d", "#32363f", "#474c57", "#60666f", "#7e848c", "#a4a8ac")
RUST = ramp("#2a0e06", "#4e1e0c", "#723214", "#94481e")
CRYSTAL = ramp("#0c0c1a", "#181c36", "#283052", "#3a4876", "#526494", "#7c8eb6", "#b4c2dc")
VIOLET = ramp("#120c1c", "#241834", "#3a2a54", "#544274", "#74629a", "#9c8cbc")
FUNGUS = ramp("#060c09", "#0e1a13", "#182e22", "#264632", "#386248", "#588a66", "#94c09a")
GLASS = ramp("#060810", "#0c1420", "#162434", "#243a50", "#38566e", "#5a7c94", "#a8c4d4")
GOLD = ramp("#1a1008", "#382612", "#58401e", "#7a5e2e", "#9c7e44", "#bea068", "#d4c094")
TILE = ramp("#121314", "#26282a", "#3e4042", "#5a5c5c", "#7a7a76", "#9c9a92", "#bcb8ac")
WATER = ramp("#03070b", "#071420", "#0b2232", "#10364a", "#1a5066", "#347c8c", "#8cc4c8")
STRAW = ramp("#120e08", "#261d12", "#3e321f", "#5c4c30", "#7a6842", "#9a885c")
DIRT = ramp("#09070b", "#140f12", "#211a20", "#30262a", "#433537", "#584846")
PAVE = ramp("#16181c", "#24272d", "#363a41", "#4c5058", "#666a72", "#848890")
ECHO = ramp("#0e121a", "#1e2632", "#323d4b", "#4a586a", "#66788c", "#8898ac", "#acb8c8")  # the echo chamber: cold pale stone
EARTH = ramp("#0c0805", "#1e130b", "#322214", "#4a3420", "#64492e", "#806242", "#a08466")  # the warren: packed warm earth
FLAME = ramp("#3a0a04", "#8a1a06", "#d8480c", "#f8962a", "#ffd468", "#fff4c0")
SLATE = ramp("#141220", "#221f30", "#322e42", "#443f56", "#58526a", "#6e6880")  # A4's Bassment door stone
SLEEVES = [ramp("#1a0a0c", "#3a1418", "#5c2228"), ramp("#0a0e1c", "#16203a", "#253456"), ramp("#1c1406", "#3c2c0e", "#5e4818"),
           ramp("#101210", "#22261f", "#383d32"), ramp("#0c160e", "#183020", "#264a30")]


def _mc():
    sys.path.insert(0, os.path.join(lib.ROOT, "tools", "trial"))
    return importlib.import_module("make_creatures")


def _rgb(shade: np.ndarray, pal: np.ndarray, dither: float = 0.8) -> np.ndarray:
    return quantise(np.clip(shade, 0, 1), pal, dither)


def _put(rgb: np.ndarray, mask: np.ndarray, shade, pal: np.ndarray, dither: float = 0.8) -> np.ndarray:
    sh = np.full(rgb.shape[:2], float(shade), np.float32) if np.isscalar(shade) else shade
    return np.where(np.asarray(mask, bool)[..., None], _rgb(sh, pal, dither), rgb)


def _col(rgb: np.ndarray, mask: np.ndarray, hexs: str) -> np.ndarray:
    out = rgb.copy()
    out[np.asarray(mask, bool)] = (hexc(hexs) * 255 + 0.5).astype(np.uint8)
    return out


def blocks(n, rows, cols, seed, mortar=1, stagger=0.5):
    """Staggered courses (bricks, flags, ashlar), tileable: (tone per block, mortar, upper-left lit row, lower-right shade row, block id)."""
    x, y = grid(n)
    bh, bw = n / rows, n / cols
    r = np.floor(y / bh)
    xx = (x + (r % 2) * bw * stagger) % n
    c = np.floor(xx / bw)
    lx, ly = xx - c * bw, y - r * bh
    tone = np.random.RandomState(seed).rand(rows, cols).astype(np.float32)
    t = tone[r.astype(int) % rows, c.astype(int) % cols]
    mort = (lx < mortar) | (ly < mortar)
    hi = ~mort & ((ly < mortar + 1) | (lx < mortar + 1))
    lo = ~mort & ((ly >= bh - 1) | (lx >= bw - 1))
    return t, mort, hi, lo, (r * cols + c).astype(int)


def emboss(f: np.ndarray, k: float) -> np.ndarray:
    """Relief from a height field, lit from the upper left (tileable: np.roll wraps)."""
    return (f - np.roll(np.roll(f, 1, 0), 1, 1)) * k


def cracks(n, count, seed, length=(10, 24)):
    """Hairline cracks: wandering one-pixel walks that wrap around the tile."""
    rng = np.random.RandomState(seed)
    m = np.zeros((n, n), bool)
    for _ in range(count):
        x, y = rng.rand() * n, rng.rand() * n
        ang = rng.rand() * np.pi * 2
        for _ in range(rng.randint(*length)):
            m[int(y) % n, int(x) % n] = True
            ang += rng.uniform(-0.7, 0.7)
            x, y = x + np.cos(ang), y + np.sin(ang)
    return m


def stone_shade(t, hi, lo, seed, wear=0.4, grain=0.22):
    n = t.shape[0]
    sh = 0.44 + 0.34 * (t - 0.5) + 0.16 * hi - 0.18 * lo
    sh += (noise(n, 6, seed) - 0.5) * grain + (noise(n, 2, seed + 1) - 0.5) * 0.12
    pits = noise(n, 3, seed + 2) > 1 - wear * 0.3
    sh = np.where(pits, sh - 0.22, sh)
    return sh


def brickwall(pal, seed, rows=8, cols=4, wear=0.45, grime_k=0.25, mort=MORT):
    t, m, hi, lo, _ = blocks(N, rows, cols, seed)
    sh = stone_shade(t, hi, lo, seed + 3, wear) - grime_k * np.clip((noise(N, 24, seed + 5, 4) - 0.5) * 2.5, 0, 1)
    rgb = _rgb(sh, pal)
    rgb = _put(rgb, cracks(N, 5, seed + 7) & ~m, 0.12, pal)
    return _put(rgb, m, 0.45 + (noise(N, 4, seed + 9) - 0.5) * 0.5, mort), m


# ---- walls -------------------------------------------------------------------------------------------------------------------------------------------

def wall_brick():
    """The cellars' warm brick: 0.25 x 0.125 m bricks, each its own tone, chipped, cracked, a white bloom of salt in the damp ones."""
    rgb, m = brickwall(BRICK, 501)
    salt = (noise(N, 14, 506, 3) > 0.72) & (speckle(N, 0.22, 507) > 0) & ~m
    return _put(rgb, salt, 0.92, BRICK), 1.0


def wall_brick_dark():
    """The damp blue-grey brick of the wet zones, with wet streaks running down and a few glints of water."""
    rgb, m = brickwall(DAMP, 511, wear=0.6)
    x, y = grid(N)
    cols = np.random.RandomState(512).rand(N) < 0.07
    wet = cols[x.astype(int)] & (noise(N, 10, 513) > 0.45) & ~m
    rgb = _put(rgb, wet, 0.75, DAMP)
    return _col(rgb, (speckle(N, 0.004, 514) > 0) & ~m, "#8cb8c4"), 1.0


def _pipe(rgb, cy, r, horizontal=True, seed=0):
    x, y = grid(N)
    a, b = (y, x) if horizontal else (x, y)
    u = np.clip((a - cy) / r, -1, 1)
    nz = np.sqrt(np.clip(1 - u * u, 0, 1))
    lit = (u * (-0.62 if horizontal else -0.45) + nz * 0.64) / 0.85
    m = np.abs(a - cy) < r
    fl = ((b % 64) < 4) & (np.abs(a - cy) < r * 1.3)
    sh = np.clip(lit, 0, 1) * 0.8 + 0.08 + 0.12 * fl
    rgb = _put(rgb, m | fl, sh, IRON)
    bolt = fl & (np.abs(np.abs(a - cy) - r * 1.1) < 1.2) & ((b % 64) > 0.5) & ((b % 64) < 3)
    rgb = _put(rgb, bolt, 0.95, IRON)
    rust = m & (noise(N, 8, seed) > 0.68)
    return _put(rgb, rust, 0.4 + 0.5 * np.clip(lit, 0, 1), RUST), m | fl


def wall_pipe():
    """Brick with two iron pipes run along it on flanges, rust where the paint went, rust streaks under them."""
    rgb, m = brickwall(BRICK, 521, grime_k=0.35)
    x, y = grid(N)
    for cy, r in ((34, 9), (94, 6)):
        streak = (np.random.RandomState(cy).rand(N) < 0.12)[x.astype(int)] & (y > cy + r) & (y < cy + r + 10 + 14 * noise(N, 5, cy))
        rgb = _put(rgb, streak, 0.3, RUST)
        rgb, _ = _pipe(rgb, cy, r, True, 523 + cy)
    return rgb, 1.0


def wall_cable():
    """Damp brick with sagging bundles of old cable (black, grey, red, green) pinned up by iron clips."""
    rgb, m = brickwall(DAMP, 531, grime_k=0.3)
    x, y = grid(N)
    rng = np.random.RandomState(540)
    cab = [ramp("#060608", "#16161c", "#2c2c34"), ramp("#121216", "#2a2a32", "#4a4a54"), ramp("#1e0806", "#4a1610", "#72281c"), ramp("#06120a", "#12301c", "#22502e")]
    for k in range(6):
        y0, sag, w = rng.rand() * N, 4 + rng.rand() * 14, 2.0 + rng.rand() * 1.5
        yy = y0 + sag * np.sin(np.pi * x / N) ** 2
        d = (y - yy + N / 2) % N - N / 2
        m2 = np.abs(d) < w
        rgb = _put(rgb, m2, 0.75 - 0.6 * (d + w) / (2 * w), cab[k % 4], 0.5)
    clip = ((x % 64) > 30) & ((x % 64) < 34)
    for y0 in (20, 84):
        rgb = _put(rgb, clip & (np.abs(y - y0) < 9), 0.55, IRON)
    return rgb, 1.0


def wall_barrel():
    """A rack of barrel heads, 0.55 m across: oak staves, an iron chime hoop, a bung, chalked numbers, on a dark shelf frame."""
    x, y = grid(N)
    rgb = _rgb(0.18 + (noise(N, 8, 549) - 0.5) * 0.2, WOOD)
    beam = (y % 64) > 58
    rgb = _put(rgb, beam, 0.35 + 0.25 * ((y % 64) < 60), WOOD)
    for k, (cx, cy) in enumerate(((32, 30), (96, 30), (32, 94), (96, 94))):
        dx, dy = x - cx, y - cy
        d = np.hypot(dx, dy)
        head = d < 27
        stave = np.floor((x - cx + 27) / 7)
        st = np.random.RandomState(550 + k).rand(9)[np.clip(stave.astype(int), 0, 8)]
        sh = 0.48 + 0.18 * (st - 0.5) - 0.22 * (d / 27) ** 2 - 0.14 * (dx + dy) / 54 + 0.1 * np.sin(y * 0.9 + st * 6) * 0.3
        sh = np.where(((x - cx + 27) % 7) < 1, sh - 0.25, sh)
        rgb = _put(rgb, head, sh, WOOD)
        ring = (d >= 23) & (d < 27)
        rgb = _put(rgb, ring, 0.55 - 0.3 * (dx + dy) / 54, IRON)
        rgb = _put(rgb, (d >= 27) & (d < 29), 0.08, WOOD)
        rgb = _put(rgb, np.hypot(dx - 8, dy + 6) < 3, 0.12, WOOD)
        if k in (0, 3):
            chalk = (np.abs(dy - 4) < 0.8) & (np.abs(dx + 8) < 5) | (np.abs(dx + 8) < 0.8) & (np.abs(dy - 2) < 5)
            rgb = _col(rgb, chalk & head, "#b8b0a0")
    return rgb, 1.25


def wall_crystal():
    """Crystal columns: four prisms per tile, each broken into segments with slanted tops, a lit and a shaded facet, a bright ridge, sparks."""
    x, y = grid(N)
    w = 32
    i = (x // w).astype(int)
    lx = (x % w) / w
    rng = np.random.RandomState(571)
    cuts = rng.rand(4, 3) * N
    seg = np.zeros((N, N), np.int32)
    for c in range(3):
        seg += (((y + (lx - 0.5) * 10) % N) > cuts[i, c]).astype(np.int32)
    tone = rng.rand(4, 4)[i, seg % 4]
    facet = np.where(lx < 0.45, 0.62 - 0.2 * lx, 0.28 + 0.1 * (1 - lx))
    sh = facet + 0.18 * (tone - 0.5) + (noise(N, 10, 572) - 0.5) * 0.12
    sh = np.where(np.abs(lx - 0.45) < 0.04, 0.95, sh)
    sh = np.where((lx < 0.04) | (lx > 0.96), 0.08, sh)
    rgb = np.where((i % 2 == 0)[..., None], _rgb(sh, CRYSTAL), _rgb(sh, VIOLET))
    for c in range(3):
        line = np.abs(((y + (lx - 0.5) * 10) % N) - cuts[i, c]) < 0.8
        rgb = np.where(line[..., None], _rgb(np.full((N, N), 0.15, np.float32), CRYSTAL), rgb)
    return _col(rgb, (speckle(N, 0.003, 573) > 0) & (lx < 0.45), "#dce8f4"), 1.25


def wall_fungus():
    """Rough stone blocks overgrown with glowing fungus: soft green mats and shelf caps with pale gills."""
    t, m, hi, lo, _ = blocks(N, 4, 2, 581)
    rgb = _rgb(stone_shade(t, hi, lo, 582, 0.6) * 0.85, STONE)
    rgb = _put(rgb, m, 0.12, STONE)
    mat = noise(N, 18, 583, 4)
    patch = mat > 0.58
    rgb = _put(rgb, patch, 0.2 + (mat - 0.58) * 2.2 + (noise(N, 3, 584) - 0.5) * 0.25, FUNGUS)
    x, y = grid(N)
    rng = np.random.RandomState(585)
    for _ in range(7):
        cx, cy, r = rng.rand() * N, rng.rand() * N, 4 + rng.rand() * 5
        dx = (x - cx + N / 2) % N - N / 2
        dy = (y - cy + N / 2) % N - N / 2
        cap = ((dx / r) ** 2 + (dy / (r * 0.55)) ** 2 < 1) & (dy < 1)
        rgb = _put(rgb, cap, 0.7 - 0.4 * (dx + r) / (2 * r) - 0.2 * (dy > -1), FUNGUS)
    return _col(rgb, (speckle(N, 0.006, 586) > 0) & patch, "#b8e8b0"), 1.0


def wall_mirror():
    """Mirror panes in gilt frames: a cold gradient, a diagonal glint, and in some panes a stranger dancing who is not in the room."""
    x, y = grid(N)
    lx, ly = x % 64, y % 64
    pid = (x // 64).astype(int) + 2 * (y // 64).astype(int)
    tone = np.random.RandomState(591).rand(4)[pid]
    g = 0.3 + 0.25 * (ly / 64) + 0.12 * tone
    glint = np.abs(((lx + ly * 0.7 + tone * 30) % 64) - 30) < 2.5
    g = np.where(glint, g + 0.4, g)
    fig = (np.abs(lx - 32) < 4 + 3 * np.clip(1 - ly / 40, 0, 1)) & (ly > 16) & (ly < 58) | (np.hypot(lx - 32, ly - 12) < 4.5)
    g = np.where(fig & (pid % 3 == 0), g - 0.22, g)
    rgb = _rgb(g, GLASS)
    frame = (lx < 5) | (lx > 59) | (ly < 5) | (ly > 59)
    fsh = 0.5 + 0.3 * ((lx < 2) | (ly < 2)) - 0.3 * ((lx > 62) | (ly > 62)) + (noise(N, 3, 592) - 0.5) * 0.3
    rgb = _put(rgb, frame, fsh, GOLD)
    return rgb, 1.25


def wall_iron():
    """Riveted iron plates, 0.5 m square, with seams, rivet heads lit on the upper left and rust run down from them."""
    x, y = grid(N)
    lx, ly = x % 64, y % 64
    seam = (lx < 1) | (ly < 1)
    sh = 0.45 + 0.12 * (lx < 3) + 0.08 * (ly < 3) - 0.15 * (lx > 61) - 0.12 * (ly > 61) + (noise(N, 10, 601) - 0.5) * 0.2
    sh += 0.08 * (np.random.RandomState(602).rand(4)[(x // 64).astype(int) + 2 * (y // 64).astype(int)] - 0.5)
    rgb = _rgb(sh, IRON)
    riv = ((lx % 16) - 8) ** 2 + ((ly < 8) * (ly - 4) ** 2 + (ly >= 8) * 99) < 3.5
    riv |= (((ly % 16) - 8) ** 2 + ((lx < 8) * (lx - 4) ** 2 + (lx >= 8) * 99)) < 3.5
    rgb = _put(rgb, riv, 0.85, IRON)
    streak = (np.random.RandomState(603).rand(N) < 0.18)[x.astype(int)] & (noise(N, 6, 604) > 0.5) & ~seam
    rgb = _put(rgb, streak, 0.35, RUST)
    rgb = _put(rgb, (noise(N, 12, 605, 4) > 0.7) & ~seam, 0.6 + (noise(N, 3, 606) - 0.5) * 0.4, RUST)
    return _put(rgb, seam, 0.05, IRON), 1.0


def wall_shelf():
    """Stone shelves packed with old records: sleeves in faded colours, a few leaning, brass catalogue labels, the shelf boards worn."""
    x, y = grid(N)
    s = 32
    ly = y % s
    row = (y // s).astype(int)
    rgb = _rgb(0.15 + (noise(N, 6, 610) - 0.5) * 0.1, STONE)
    rng = np.random.RandomState(611)
    for r in range(4):
        xx = 0
        while xx < N:
            w = int(rng.choice([2, 2, 3, 3, 4]))
            if rng.rand() < 0.06:
                xx += 3
                continue
            pal = SLEEVES[rng.randint(len(SLEEVES))]
            top = 6 + rng.randint(0, 4)
            m = (row == r) & (x >= xx) & (x < xx + w) & (ly >= top) & (ly < s - 4)
            sh = 0.55 + 0.4 * (x == xx) - 0.3 * (x == xx + w - 1) + rng.uniform(-0.15, 0.15)
            rgb = _put(rgb, m, sh, pal, 0.0)
            if rng.rand() < 0.18:
                rgb = _col(rgb, m & (ly > top + 6) & (ly < top + 9), "#b08a3c")
            xx += w
    board = ly >= s - 4
    rgb = _put(rgb, board, 0.55 + 0.25 * (ly == s - 4) - 0.3 * (ly == s - 1) + (noise(N, 4, 612) - 0.5) * 0.2, WOOD)
    return rgb, 1.25


def wall_rock():
    """Cave rock: layered, cracked, lit in relief from the upper left; cooler than the Underworld's."""
    h = noise(N, 22, 621, 4) * 0.7 + (1 - np.abs(noise(N, 12, 622, 3) - 0.5) * 2) ** 3 * 0.3
    x, y = grid(N)
    strata = np.sin(y / N * 2 * np.pi * 5 + noise(N, 32, 623, 2) * 6) * 0.06
    sh = 0.32 + 0.35 * h + strata + emboss(noise(N, 8, 624, 3), 2.0)
    rgb = _rgb(sh, STONE)
    return _put(rgb, cracks(N, 9, 625), 0.08, STONE), 1.25


def wall_echo():
    """The echo chamber's bare stone: long pale ashlar courses, cold and clean, with the rings of a sound carved faintly across them (they tile: a toroidal distance)."""
    t, m, hi, lo, _ = blocks(N, 4, 2, 681)
    x, y = grid(N)
    dx = np.minimum(np.abs(x - N / 2), N - np.abs(x - N / 2))
    dy = np.minimum(np.abs(y - N / 2), N - np.abs(y - N / 2))
    d = np.sqrt(dx * dx + dy * dy)
    groove = (np.sin(d * 0.42) > 0.9) & (d < N * 0.5)
    sh = stone_shade(t, hi, lo, 682, 0.25, 0.14) * 0.9 + 0.12 - 0.14 * groove
    rgb = _rgb(sh, ECHO)
    return _put(rgb, m, 0.16, ECHO), 1.25


def wall_burrow():
    """The warren's walls: packed earth in warm layers, gnawed into, with the round black mouths of rat holes (a lit lip under each), roots and gnaw scratches."""
    x, y = grid(N)
    strata = 0.5 + 0.5 * np.sin(y / N * 2 * np.pi * 6 + noise(N, 16, 691, 3) * 5.0)
    hf = noise(N, 8, 692, 4)
    sh = 0.3 + 0.2 * hf + 0.12 * strata + emboss(hf, 4.0)
    rng = np.random.RandomState(693)
    hole = np.zeros((N, N), bool)
    lip = np.zeros((N, N), bool)
    for _ in range(4):
        cx, cy, rx = rng.rand() * N, rng.rand() * N, 6 + rng.rand() * 5
        ddx = (x - cx + N / 2) % N - N / 2
        ddy = (y - cy + N / 2) % N - N / 2
        e = (ddx / rx) ** 2 + (ddy / (rx * 0.7)) ** 2
        hole |= e < 1.0
        lip |= (e >= 1.0) & (e < 1.8) & (ddy > 0)
    scratch = np.zeros((N, N), bool)
    for _ in range(16):
        sx, sy, ln = rng.rand() * N, rng.rand() * N, 4 + rng.randint(0, 5)
        for k in range(ln):
            for o in (0, 2, 4):
                scratch[int(sy + k) % N, int(sx + o + k * 0.5) % N] = True
    sh = sh + 0.28 * lip - 0.16 * scratch
    rgb = _rgb(sh, EARTH)
    rgb = _put(rgb, cracks(N, 6, 695, (14, 30)), 0.1, EARTH)  # roots
    rgb = _col(rgb, (speckle(N, 0.005, 694) > 0) & ~hole, "#a88454")
    return _put(rgb, hole, 0.06, EARTH), 1.25


def wall_door():
    """Plank doors for the exits: four oak planks, grain and knots, two iron straps with nail heads."""
    x, y = grid(N)
    pl = (x // 32).astype(int)
    t = np.random.RandomState(631).rand(4)[pl % 4]
    lx = x % 32
    grain = np.sin(y * 0.18 + noise(N, 10, 632) * 7 + pl * 2) * 0.08
    sh = 0.38 + 0.2 * t + grain + 0.14 * (lx < 2) - 0.2 * (lx > 29) + (noise(N, 3, 634) - 0.5) * 0.12
    knot = (np.hypot((x - 20) % N - 0, (y - 44) % N - 0) < 3) | (np.hypot(x - 82, y - 100) < 2.5)
    sh = np.where(knot, 0.15, sh)
    rgb = _rgb(sh, WOOD)
    rgb = _put(rgb, lx < 1, 0.05, WOOD)
    for y0 in (20, 84):
        strap = (y >= y0) & (y < y0 + 8)
        rgb = _put(rgb, strap, 0.45 + 0.25 * (y == y0) - 0.25 * (y == y0 + 7) + (noise(N, 3, 633) - 0.5) * 0.25, IRON)
        nail = strap & (np.abs(y - y0 - 4) < 1.5) & (np.abs(lx - 16) < 1.5)
        rgb = _put(rgb, nail, 0.9, IRON)
        rgb = _put(rgb, (np.abs(y - y0 - 8.5) < 1) & (np.random.RandomState(y0).rand(N) < 0.5)[x.astype(int)], 0.25, RUST)
    return rgb, 1.25


def wall_hatch():
    """An iron hatch door: one riveted plate per tile with a wheel lock, spokes and hub, its rim worn bright."""
    x, y = grid(N)
    d = np.hypot(x - 64, y - 64)
    sh = 0.42 + 0.1 * (x < 4) + 0.06 * (y < 4) - 0.12 * (x > 123) - 0.1 * (y > 123) + (noise(N, 10, 641) - 0.5) * 0.18
    rgb = _rgb(sh, IRON)
    edge = ((x % 128) < 1) | ((y % 128) < 1)
    riv = (((x % 16) - 8) ** 2 + (np.minimum(y, 127 - y) - 5) ** 2 < 4) | (((y % 16) - 8) ** 2 + (np.minimum(x, 127 - x) - 5) ** 2 < 4)
    rgb = _put(rgb, riv, 0.85, IRON)
    ring = (d > 38) & (d < 46)
    rgb = _put(rgb, ring, 0.6 - 0.35 * ((x - 64) + (y - 64)) / 92 + 0.2 * (d < 40), IRON)
    sp = ((np.abs(x - 64) < 3) | (np.abs(y - 64) < 3)) & (d < 40)
    rgb = _put(rgb, sp, 0.55 + 0.2 * ((x - 64) < -1) + 0.2 * ((y - 64) < -1) - 0.2 * ((x - 64) > 1), IRON)
    rgb = _put(rgb, d < 8, 0.4 + 0.5 * np.clip(1 - np.hypot(x - 61, y - 61) / 6, 0, 1), RUST)
    rgb = _put(rgb, (noise(N, 10, 642, 4) > 0.72) & ~ring & ~sp, 0.35, RUST)
    return _put(rgb, edge, 0.05, IRON), 1.25


def wall_tile():
    """Kitchen wall tile: 0.15 m glazed squares, a gloss on each one's upper left, crazed and chipped, grease and soot."""
    x, y = grid(N)
    lx, ly = x % 16, y % 16
    g = (lx < 1) | (ly < 1)
    tone = np.random.RandomState(651).rand(8, 8)[(y // 16).astype(int), (x // 16).astype(int)]
    sh = 0.62 + 0.1 * (tone - 0.5) + 0.2 * ((lx + ly) < 6) * (lx > 1) * (ly > 1) - 0.1 * ((lx > 14) | (ly > 14))
    dirt = np.clip((noise(N, 24, 652, 4) - 0.45) * 2.0, 0, 1)
    sh = sh - 0.3 * dirt + (noise(N, 4, 653) - 0.5) * 0.08
    rgb = _rgb(sh, TILE)
    rgb = _put(rgb, cracks(N, 6, 654, (6, 14)) & ~g, 0.25, TILE)
    return _put(rgb, g, 0.15 - 0.1 * dirt, TILE), 1.2


def wall_hands():
    """Stone carved with open hands, palms out, 0.4 m tall, in relief: lit edges up and left, their shadows down and right."""
    mc = _mc()
    p = mc.Painter(N)
    base = _rgb(0.28 + (noise(N, 14, 661, 3) - 0.5) * 0.22 + emboss(noise(N, 9, 662), 1.0), STONE)
    pal = np.asarray((STONE * 255 + 0.5), np.uint8)
    for (cx, cy) in ((32, 36), (96, 36), (32, 100), (96, 100)):
        p.part(p.ell(cx, cy + 8, 11, 12) | p.rect(cx - 7, cy + 14, cx + 7, cy + 28), pal, p.sphere(cx - 2, cy + 6, 12, 14))
        for k, ang in enumerate((-0.42, -0.14, 0.14, 0.42)):
            ln = (17, 20, 19, 15)[k]
            p.part(p.seg(cx + np.sin(ang) * 7, cy + 2, cx + np.sin(ang) * ln, cy + 2 - np.cos(ang) * ln, 5), pal, 0.62 - 0.05 * k)
        p.part(p.seg(cx - 9, cy + 10, cx - 18, cy + 2, 5), pal, 0.65)
    rgba = p.finish()
    a = rgba[..., 3] > 0
    shadow = np.roll(np.roll(a, 2, 0), 2, 1) & ~a
    rgb = np.where(a[..., None], rgba[..., :3], base)
    return _put(rgb, shadow, 0.05, STONE), 1.25


def wall_brass():
    """The Resonance Door's hammered brass: plates with dimpled hammer marks, rivet rows, rings engraved round each plate's centre, verdigris in the seams."""
    x, y = grid(N)
    lx, ly = x % 64, y % 64
    d = np.hypot(lx - 32, ly - 32)
    hammer = noise(N, 6, 671, 2)
    rings = np.sin(d * 0.75)
    sh = 0.46 + emboss(hammer, 0.9) + 0.26 * (rings > 0.6) - 0.22 * ((rings < -0.75) & (rings > -0.98)) - 0.12 * (d / 46)
    sh += 0.12 * ((lx < 3) | (ly < 3)) - 0.15 * ((lx > 60) | (ly > 60))
    rgb = _rgb(sh, GOLD)
    riv = ((((lx % 8) - 4) ** 2 + (np.minimum(ly, 63 - ly) - 3) ** 2) < 2.2) | ((((ly % 8) - 4) ** 2 + (np.minimum(lx, 63 - lx) - 3) ** 2) < 2.2)
    rgb = _put(rgb, riv, 0.95, GOLD)
    seam = (lx < 1) | (ly < 1)
    rgb = _put(rgb, seam, 0.05, GOLD)
    verd = (seam | (np.roll(seam, -1, 0) | np.roll(seam, -1, 1))) & (noise(N, 6, 672) > 0.55)
    return _col(rgb, verd, "#4e8a78"), 1.25


# ---- floors and ceilings --------------------------------------------------------------------------------------------------------------------------

def floor_flag():
    """Flagstones 0.62 x 0.31 m laid in courses, worn smooth in the middle, cracked, dark joints."""
    t, m, hi, lo, _ = blocks(N, 4, 2, 701)
    sh = stone_shade(t, hi, lo, 702, 0.35) - 0.18 * np.clip((noise(N, 24, 703, 4) - 0.5) * 2.5, 0, 1)
    rgb = _rgb(sh, STONE)
    rgb = _put(rgb, cracks(N, 6, 704) & ~m, 0.1, STONE)
    return _put(rgb, m, 0.08, STONE), 1.25


def floor_wood():
    """Floor boards 0.125 m wide with butt joints, grain, knots and nail heads."""
    x, y = grid(N)
    r = (y // 16).astype(int)
    rng = np.random.RandomState(711)
    off = rng.rand(8) * N
    jx = (x + off[r % 8]) % N
    seg = (jx // 64).astype(int)
    t = rng.rand(8, 2)[r % 8, seg % 2]
    ly = y % 16
    grain = np.sin(x * 0.12 + noise(N, 12, 712) * 8 + r * 1.7) * 0.07
    sh = 0.42 + 0.22 * (t - 0.5) + grain + 0.12 * (ly < 1.5) - 0.14 * (ly > 14) - 0.15 * np.clip((noise(N, 24, 713, 4) - 0.5) * 2.5, 0, 1)
    rgb = _rgb(sh, WOOD)
    joint = (ly < 1) | ((jx % 64) < 1)
    rgb = _put(rgb, joint, 0.05, WOOD)
    nail = (np.abs(ly - 8) < 1.2) & ((np.abs((jx % 64) - 3) < 1.2) | (np.abs((jx % 64) - 61) < 1.2))
    return _put(rgb, nail, 0.6, IRON), 1.0


def floor_grate():
    """An iron floor grate over black water: 3 px bars every 8 px, cross bars every 32, a glint of water below."""
    x, y = grid(N)
    bars = (x % 8) < 3
    cross = (y % 32) < 4
    m = bars | cross
    sh = 0.42 + 0.25 * (((x % 8) < 1) & ~cross) + 0.2 * (((y % 32) < 1)) - 0.2 * (((x % 8) == 2) & ~cross) + (noise(N, 6, 721) - 0.5) * 0.25
    rgb = _rgb(sh, IRON)
    under = _rgb(0.08 + 0.35 * (noise(N, 10, 722) > 0.75) * (noise(N, 3, 723) > 0.5), WATER)
    rgb = np.where(m[..., None], rgb, under)
    return _put(rgb, m & (noise(N, 10, 724, 4) > 0.7), 0.5, RUST), 1.0


def floor_moss():
    """Dark earth carpeted in moss, the brightest tufts glowing, a scatter of tiny caps."""
    v = noise(N, 14, 731, 4)
    base = _rgb(0.25 + 0.3 * v + emboss(noise(N, 4, 734), 2.0), DIRT)
    moss = np.clip((noise(N, 10, 732, 3) - 0.42) * 3, 0, 1)
    tuft = noise(N, 2, 735)
    rgb = np.where((moss > 0.1)[..., None], _rgb(0.12 + moss * 0.55 + (tuft - 0.5) * 0.3, FUNGUS), base)
    return _col(rgb, (speckle(N, 0.004, 733) > 0) & (moss > 0.3), "#b8e8b0"), 1.25


def floor_kitchen():
    """The kitchens' checker of 0.15 m tiles, cream and charcoal, greasy, with chipped corners."""
    x, y = grid(N)
    c = (((x // 16) + (y // 16)) % 2).astype(np.float32)
    lx, ly = x % 16, y % 16
    dirt = np.clip((noise(N, 24, 742, 4) - 0.45) * 2.0, 0, 1)
    sh = 0.2 + 0.45 * c + 0.08 * ((lx < 2) | (ly < 2)) + (noise(N, 4, 741) - 0.5) * 0.1 - 0.25 * dirt
    rgb = _rgb(sh, TILE)
    return _put(rgb, (lx < 1) | (ly < 1), 0.12, TILE), 1.2


def floor_crystal():
    from .tex_underworld import _worley
    f1, f2, ids = _worley(N, 6, 751)
    tone = np.random.RandomState(752).rand(36)[ids % 36]
    sh = 0.3 + 0.3 * tone + 0.25 * np.clip(1 - f1 / 12, 0, 1) * 0.5 - 0.4 * ((f2 - f1) < 1.2)
    rgb = np.where(((ids % 3) == 0)[..., None], _rgb(sh, VIOLET), _rgb(sh, CRYSTAL))
    return _col(rgb, (speckle(N, 0.003, 753) > 0) & ((f2 - f1) > 3), "#c8d8f0"), 1.25


def floor_mirror():
    """Mirror tiles 0.25 m square in dark gilt joints, each with a diagonal glint."""
    x, y = grid(N)
    lx, ly = x % 32, y % 32
    tone = np.random.RandomState(761).rand(16)[(x // 32).astype(int) + 4 * (y // 32).astype(int)]
    sh = 0.22 + 0.15 * tone + 0.45 * (np.abs(((lx + ly) % 32) - 14 - tone * 6) < 1.5)
    rgb = _rgb(sh, GLASS)
    return _put(rgb, (lx < 1) | (ly < 1), 0.3, GOLD), 1.0


def floor_dirt():
    """Packed dirt with pebbles (each lit on its upper left) and scuffs."""
    x, y = grid(N)
    h = noise(N, 16, 761, 4)
    sh = 0.28 + 0.3 * h + emboss(noise(N, 4, 763), 2.5) - 0.15 * np.clip((noise(N, 24, 762, 4) - 0.5) * 2.5, 0, 1)
    rgb = _rgb(sh, DIRT)
    rng = np.random.RandomState(764)
    for _ in range(18):
        cx, cy, r = rng.rand() * N, rng.rand() * N, 1.2 + rng.rand() * 1.8
        dx = (x - cx + N / 2) % N - N / 2
        dy = (y - cy + N / 2) % N - N / 2
        rgb = _put(rgb, np.hypot(dx, dy) < r, 0.75 - 0.4 * (dx + dy) / (2 * r), STONE)
    return rgb, 1.25


def floor_straw():
    """Straw strewn over a dark floor: single stalks in many directions, lit and shaded."""
    x, y = grid(N)
    rgb = _rgb(0.25 + 0.25 * noise(N, 8, 771) + (noise(N, 2, 773) - 0.5) * 0.3, STRAW)
    rng = np.random.RandomState(772)
    for _ in range(700):
        cx, cy = rng.rand() * N, rng.rand() * N
        a = rng.uniform(-0.6, 0.6) + (0 if rng.rand() < 0.7 else np.pi / 2)
        ln = 6 + rng.rand() * 10
        for k in range(int(ln)):
            px, py = int(cx + np.cos(a) * k) % N, int(cy + np.sin(a) * k) % N
            rgb[py, px] = (STRAW[min(5, 1 + int(rng.rand() * 5))] * 255 + 0.5).astype(np.uint8)
    return rgb, 1.0


def floor_pavement():
    """Concrete slabs 0.62 m square: cracked, stained with oil, the aggregate speckled."""
    x, y = grid(N)
    lx, ly = x % 64, y % 64
    tone = np.random.RandomState(781).rand(4)[(x // 64).astype(int) + 2 * (y // 64).astype(int)]
    sh = 0.48 + 0.12 * (tone - 0.5) + (noise(N, 6, 782) - 0.5) * 0.2 + 0.25 * (speckle(N, 0.05, 783) - 0.025) - 0.25 * (noise(N, 20, 784, 3) > 0.7)
    rgb = _rgb(sh, PAVE)
    rgb = _put(rgb, cracks(N, 5, 785, (12, 30)), 0.15, PAVE)
    return _put(rgb, (lx < 1) | (ly < 1), 0.1, PAVE), 1.25


def water(phase=0):
    """Black water with moving caustic light: the base tile and three more frames (the map swaps through them)."""
    x, y = grid(N)
    a = np.sin((x / N + phase / 8) * 2 * np.pi * 3 + noise(N, 16, 791) * 5) * np.sin((y / N - phase / 8) * 2 * np.pi * 3 + noise(N, 16, 792) * 5)
    caustic = np.clip(1 - np.abs(a) * 3.0, 0, 1) ** 2
    sh = 0.14 + 0.22 * noise(N, 18, 793, 3) + 0.5 * caustic
    return _rgb(sh, WATER), 1.25


def ceil_arch():
    """The brick vault overhead, sooted from the torches."""
    rgb, m = brickwall(BRICK, 801, grime_k=0.45)
    soot = noise(N, 20, 802, 3) > 0.55
    return _put(rgb, soot & ~m, 0.15 + (noise(N, 3, 803) - 0.5) * 0.2, BRICK), 1.0


def ceil_pipes():
    """Pipes run under a dark brick ceiling on iron brackets."""
    rgb, m = brickwall(BRICK, 811, grime_k=0.5)
    rgb = np.where(m[..., None], rgb, (rgb.astype(np.float32) * 0.7).astype(np.uint8))
    for cx, r in ((34, 10), (96, 6)):
        rgb, _ = _pipe(rgb, cx, r, False, 812 + cx)
    return rgb, 1.0


def ceil_rock():
    h = noise(N, 18, 821, 4)
    sh = 0.18 + 0.3 * h + emboss(noise(N, 5, 822, 3), 2.5)
    rgb = _rgb(sh, STONE)
    return _put(rgb, cracks(N, 6, 823), 0.04, STONE), 1.25


def ceil_crystal():
    h = noise(N, 14, 831, 4)
    rgb = _rgb(0.15 + 0.25 * h + emboss(noise(N, 5, 834, 3), 2.0), STONE)
    clus = (noise(N, 6, 832, 3) > 0.7) & (noise(N, 20, 836, 2) > 0.45)
    rgb = _put(rgb, clus, 0.3 + 0.5 * noise(N, 2, 833), CRYSTAL)
    return _col(rgb, (speckle(N, 0.006, 835) > 0) & clus, "#dce8f4"), 1.25


def ceil_beams():
    """Heavy beams across the ceiling with boards laid over them, cobwebs in the corners."""
    x, y = grid(N)
    ly = y % 64
    beam = ly < 22
    board = (x % 16)
    sh_b = 0.22 + 0.1 * (board < 1.5) - 0.1 * (board > 14) + (noise(N, 6, 841) - 0.5) * 0.15
    rgb = _rgb(sh_b, WOOD)
    rgb = _put(rgb, (x % 16) < 1, 0.04, WOOD)
    grain = np.sin(x * 0.2 + noise(N, 10, 842) * 6) * 0.07
    rgb = _put(rgb, beam, 0.5 + grain + 0.2 * (ly < 2) - 0.3 * (ly > 19) + (noise(N, 3, 843) - 0.5) * 0.1, WOOD)
    web = (ly > 22) & (ly < 34) & ((((x % 64) - (ly - 22) * 2) % 9) < 0.8) & ((x % 64) < 18)
    return _col(rgb, web, "#6e6a62"), 1.25


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


# ---- props (RGBA billboards, the creatures' painter) ------------------------------------------------------------------------------------------------

def _P():
    mc = _mc()
    return mc, mc.Painter(N)


def _pal(r):
    return np.asarray(r * 255 + 0.5, np.uint8)


def _flame(p, cx, base_y, w, h, seed):
    """Tongues of fire: a red outer, orange, yellow and a pale core, stepped."""
    rng = np.random.RandomState(seed)
    nz = p.noise(4, seed)
    for k, (scale, lv) in enumerate(((1.0, 0.25), (0.75, 0.5), (0.5, 0.75), (0.28, 1.0))):
        fh = h * scale
        u = (base_y - p.y) / fh
        wid = w * 0.5 * scale ** 0.5 * np.clip(1 - u, 0, 1) ** 0.7 * (0.8 + 0.4 * nz) * np.clip(u * 4 + 0.4, 0, 1)
        m = (u >= -0.05) & (u <= 1) & (np.abs(p.x - cx - np.sin(u * 5 + seed) * 2 * (1 - scale)) < wid)
        p.part(m, _pal(FLAME), lv, bevel=0, dither=0.4)


def th_torch():
    mc, p = _P()
    p.part(p.poly([(60, 124), (68, 124), (70, 74), (58, 74)]), _pal(WOOD), p.lin(58, 0, 70, 0, 0.75, 0.3))
    p.part(p.rect(54, 66, 74, 78), _pal(IRON), p.lin(54, 66, 74, 78, 0.8, 0.3))
    p.part(p.rect(54, 70, 74, 72), _pal(IRON), 0.15, bevel=0)
    p.part(p.ell(64, 64, 9, 4), _pal(BRICK), 0.3)
    _flame(p, 64, 66, 30, 56, 901)
    return p.finish()


def th_crystal():
    mc, p = _P()
    for cx, base, h, w, pal in ((38, 124, 70, 13, VIOLET), (92, 124, 82, 15, CRYSTAL), (22, 124, 40, 9, CRYSTAL), (108, 124, 46, 9, VIOLET), (64, 124, 108, 18, CRYSTAL)):
        pts = [(cx - w, base), (cx - w, base - h * 0.78), (cx, base - h), (cx + w, base - h * 0.78), (cx + w, base)]
        m = p.poly(pts)
        u = (p.x - (cx - w)) / (2 * w)
        sh = np.where(u < 0.45, 0.72 - 0.2 * u, 0.32) + 0.25 * (np.abs(u - 0.45) < 0.06) - 0.1 * (p.y - (base - h)) / h
        p.part(m, _pal(pal), sh)
    p.glow(p.rect(60, 30, 62, 32) | p.rect(88, 60, 90, 62), "#dce8f4")
    return p.finish()


def th_mushroom():
    mc, p = _P()
    for cx, base, h, r in ((44, 124, 60, 24), (86, 124, 40, 16), (66, 124, 28, 12), (24, 124, 24, 10)):
        p.part(p.poly([(cx - 4, base), (cx - 3, base - h), (cx + 3, base - h), (cx + 4, base)]), _pal(STRAW), p.lin(cx - 4, 0, cx + 4, 0, 0.8, 0.35))
        p.part(p.ell(cx, base - h + r * 0.25, r * 0.85, r * 0.2), _pal(STRAW), 0.3, bevel=0)
        cap = p.ell(cx, base - h, r, r * 0.62) & (p.y <= base - h + 2)
        p.part(cap, _pal(FUNGUS), p.sphere(cx - r * 0.3, base - h - r * 0.4, r, r * 0.6) + 0.05)
        for k in range(3):
            p.glow(p.ell(cx + (k - 1) * r * 0.45, base - h - r * 0.3 + (k % 2) * 3, 1.6, 1.4), "#c8f0c0")
    return p.finish()


def th_barrel():
    mc, p = _P()
    body = p.ell(64, 76, 38, 50) & (p.y > 30) & (p.y < 122)
    stave = np.floor((p.x - 26) / 8)
    st = np.random.RandomState(903).rand(12)[np.clip(stave.astype(int), 0, 11)]
    p.part(body, _pal(WOOD), p.sphere(58, 70, 40, 60, 0.15) + 0.1 * (st - 0.5))
    p.part(body & (((p.x - 26) % 8) < 1), _pal(WOOD), 0.1, bevel=0)
    for hy in (40, 60, 92, 112):
        p.part(body & (np.abs(p.y - hy) < 2.5), _pal(IRON), p.sphere(58, hy, 40, 8, 0.2))
    p.part(p.ell(64, 32, 30, 5), _pal(WOOD), 0.75)
    p.part(p.ell(70, 76, 3.5, 3.5), _pal(WOOD), 0.05, bevel=0)
    return p.finish()


def th_lamp():
    mc, p = _P()
    p.part(p.rect(62, 14, 66, 34), _pal(IRON), 0.5)
    p.part(p.ell(64, 36, 10, 5), _pal(GOLD), p.sphere(62, 34, 10, 5))
    cage = p.ell(64, 68, 24, 30) & ~p.ell(64, 68, 20, 26)
    bars = p.ell(64, 68, 24, 30) & (np.abs(p.x - 64) % 10 < 2)
    glass = p.ell(64, 68, 20, 26)
    p.part(glass, _pal(FLAME), 0.95 - 0.6 * np.clip(np.hypot(p.x - 62, p.y - 66) / 26, 0, 1), bevel=0, dither=0.5)
    p.part(cage | bars, _pal(GOLD), p.sphere(58, 62, 24, 30))
    p.part(p.rect(42, 96, 86, 104), _pal(GOLD), p.lin(42, 0, 86, 0, 0.8, 0.35))
    p.part(p.rect(50, 104, 78, 110), _pal(GOLD), 0.3)
    return p.finish()


def th_furnace():
    mc, p = _P()
    body = p.rect(12, 26, 116, 124)
    bricks = (((p.y - 26) % 10) < 1) | ((((p.x + 12 * ((np.floor((p.y - 26) / 10)) % 2)) % 24)) < 1)
    p.part(body, _pal(SLATE), p.lin(12, 26, 116, 124, 0.7, 0.25) + (p.noise(5, 902) - 0.5) * 0.2)
    p.part(body & bricks, _pal(SLATE), 0.05, bevel=0)
    p.part(p.rect(8, 20, 120, 30), _pal(IRON), p.lin(8, 20, 8, 30, 0.85, 0.3))
    mouth = p.ell(64, 88, 32, 28) & (p.y > 62)
    p.part(p.ell(64, 88, 36, 32) & (p.y > 58), _pal(IRON), 0.45)
    heat = np.clip(1 - np.abs(p.y - 104) / 36, 0, 1) * (0.6 + 0.4 * p.noise(5, 903))
    p.part(mouth, _pal(FLAME), 0.1 + 0.85 * heat, bevel=0, dither=0.5)
    for rx in range(18, 112, 12):
        p.part(p.ell(rx, 25, 1.8, 1.8), _pal(IRON), 0.9, bevel=0)
    return p.finish()


def th_door():
    """A lit doorway in the Bassment's door stone (A4's slate brick): an arched surround, the light beyond stepping from warm to deep, a spill on the step."""
    mc, p = _P()
    outer = p.rect(14, 40, 114, 128) | p.ell(64, 42, 50, 34)
    op = p.rect(32, 48, 96, 128) | p.ell(64, 48, 32, 24)
    t = (p.x + 14 * (np.floor(p.y / 10) % 2)) % 28
    bricks = ((p.y % 10) < 1) | (t < 1)
    p.part(outer & ~op, _pal(SLATE), p.lin(14, 20, 114, 128, 0.8, 0.3) + (p.noise(3, 904) - 0.5) * 0.25)
    p.part(outer & ~op & bricks, _pal(SLATE), 0.05, bevel=0)
    depth = np.clip((p.y - 24) / 104, 0, 1)
    p.part(op, _pal(FLAME), 0.85 - 0.75 * depth ** 0.8 - 0.15 * np.abs(p.x - 64) / 32, bevel=0, dither=0.7)
    p.part(p.rect(28, 122, 100, 128), _pal(SLATE), 0.6)
    return p.finish()


def th_hatch():
    """The way back up, seen from below: a square trapdoor opening in a timber frame, its lid hanging open on its hinges, daylight-warm light pouring down,
    the top rungs of the ladder in it."""
    mc, p = _P()
    frame = p.rect(18, 30, 110, 112)
    op = p.rect(30, 42, 98, 100)
    p.part(frame & ~op, _pal(WOOD), p.lin(18, 30, 110, 112, 0.8, 0.25) + 0.08 * np.sin(p.x * 0.4))
    lightf = 1.0 - 0.45 * np.clip(np.hypot(p.x - 60, p.y - 62) / 48, 0, 1)
    p.part(op, _pal(FLAME), 0.55 + 0.42 * lightf, bevel=0, dither=0.6)
    for y0 in (52, 70, 88):  # the top rungs, dark against the light
        p.part(p.rect(42, y0, 86, y0 + 4), _pal(WOOD), 0.25)
    for x0 in (40, 84):
        p.part(p.rect(x0, 42, x0 + 4, 100), _pal(WOOD), 0.3)
    lid = p.poly([(30, 30), (98, 30), (90, 4), (38, 4)])  # the open lid, hinged at the frame's far edge, seen edge-on
    p.part(lid, _pal(WOOD), p.lin(38, 4, 98, 30, 0.6, 0.2))
    p.part(lid & ((np.abs(p.y - 12) < 2) | (np.abs(p.y - 24) < 2)), _pal(IRON), 0.6, bevel=0)
    for hx in (44, 84):
        p.part(p.rect(hx - 3, 28, hx + 3, 34), _pal(IRON), 0.7)
    for bx in (18, 106):
        p.part(p.rect(bx, 30, bx + 4, 112), _pal(IRON), 0.45)
    return p.finish()


def th_ladder():
    mc, p = _P()
    for x0 in (38, 84):
        p.part(p.rect(x0, 0, x0 + 7, 128), _pal(WOOD), p.lin(x0, 0, x0 + 7, 0, 0.85, 0.3) + 0.05 * np.sin(p.y * 0.3 + x0))
    for y0 in range(10, 128, 22):
        p.part(p.rect(42, y0, 88, y0 + 6), _pal(WOOD), p.lin(0, y0, 0, y0 + 6, 0.8, 0.3))
        for x0 in (40, 86):
            p.part(p.rect(x0 - 1, y0 + 1, x0 + 2, y0 + 5), _pal(IRON), 0.7, bevel=0)
    return p.finish()


def th_rope():
    mc, p = _P()
    m = p.rect(60, 0, 68, 112)
    p.part(m, _pal(STRAW), 0.5 + 0.3 * (((p.y + p.x * 0.8) % 6) < 3) - 0.25 * (p.x > 66) + 0.15 * (p.x < 62))
    knot = p.ell(64, 116, 10, 10)
    p.part(knot, _pal(STRAW), p.sphere(61, 113, 10, 10) + 0.12 * (((p.x - p.y) % 5) < 2))
    return p.finish()


def th_cables():
    mc, p = _P()
    pals = [ramp("#060608", "#16161c", "#2c2c34", "#44444e"), ramp("#1e0806", "#4a1610", "#72281c", "#943a26"), ramp("#06120a", "#12301c", "#22502e", "#347040"),
            ramp("#121216", "#2a2a32", "#4a4a54", "#6a6a74")]
    for i, (x0, pal) in enumerate(((30, pals[0]), (52, pals[1]), (76, pals[2]), (98, pals[3]))):
        pts = [(x0 + np.sin(y * 0.05 + i) * 6, y) for y in range(0, 132, 8)]
        m, sh = p.tube(pts, 3.2, 3.2)
        p.part(m, _pal(pal), sh)
    box = p.rect(20, 54, 108, 82)
    p.part(box, _pal(IRON), p.lin(20, 54, 108, 82, 0.7, 0.3))
    p.part(p.rect(26, 60, 102, 76), _pal(IRON), 0.2)
    p.glow(p.ell(36, 68, 2.5, 2.5), "#50e070")
    p.glow(p.ell(92, 68, 2.5, 2.5), "#e05040")
    return p.finish()


def th_skull():
    mc, p = _P()
    bone = _pal(ramp("#2e2620", "#5a4e40", "#8a7e66", "#b8ac90", "#d0c4a8"))
    p.part(p.ell(64, 64, 30, 32), bone, p.sphere(58, 56, 30, 32))
    p.part(p.rect(46, 84, 82, 108) & p.ell(64, 92, 20, 18), bone, p.lin(46, 84, 82, 108, 0.7, 0.3))
    for sx in (-1, 1):
        p.part(p.ell(64 + sx * 12, 66, 8, 9), _pal(BRICK), 0.05, bevel=0)
    p.part(p.poly([(64, 76), (60, 87), (68, 87)]), _pal(BRICK), 0.05, bevel=0)
    for tx in range(50, 80, 6):
        p.part(p.rect(tx, 96, tx + 1.5, 106), bone, 0.05, bevel=0)
    p.part(p.seg(70, 36, 78, 52, 1.4), bone, 0.15, bevel=0)
    return p.finish()


def th_coatrack():
    mc, p = _P()
    p.part(p.rect(60, 12, 68, 120), _pal(WOOD), p.lin(60, 0, 68, 0, 0.8, 0.3))
    p.part(p.ell(64, 122, 30, 6), _pal(WOOD), p.sphere(58, 120, 30, 6))
    p.part(p.seg(26, 28, 102, 28, 4), _pal(WOOD), 0.6)
    p.part(p.ell(64, 12, 6, 5), _pal(WOOD), p.sphere(62, 10, 6, 5))
    coats = ((40, 32, ramp("#14060a", "#2e0e16", "#4a1a24", "#682a32"), 54), (88, 32, ramp("#060a16", "#10182e", "#1c2a48", "#2c3e62"), 48),
             (52, 72, ramp("#0a1008", "#182214", "#283822", "#3a5030"), 44))
    for (cx, cy, pal, h) in coats:
        m = p.poly([(cx - 5, cy), (cx + 5, cy), (cx + 15, cy + h), (cx - 15, cy + h)]) | p.ell(cx, cy + 4, 9, 6)
        fold = (np.abs(((p.x - cx) * 0.6) % 6 - 3) < 0.8)
        p.part(m, _pal(pal), p.lin(cx - 12, cy, cx + 12, cy + h, 0.85, 0.25) - 0.25 * fold)
        p.part(p.rect(cx - 1, cy - 4, cx + 1, cy + 1), _pal(GOLD), 0.7, bevel=0)
    return p.finish()


def th_valve():
    mc, p = _P()
    p.part(p.rect(58, 72, 70, 128), _pal(IRON), p.lin(58, 0, 70, 0, 0.8, 0.3))
    p.part(p.rect(52, 116, 76, 124), _pal(IRON), 0.5)
    ring = p.ell(64, 56, 38, 38) & ~p.ell(64, 56, 31, 31)
    p.part(ring, _pal(RUST), p.sphere(54, 46, 40, 40, 0.15))
    spokes = (p.seg(64, 56, 64, 20, 6) | p.seg(64, 56, 64, 92, 6) | p.seg(64, 56, 28, 56, 6) | p.seg(64, 56, 100, 56, 6)) & p.ell(64, 56, 34, 34)
    p.part(spokes, _pal(RUST), 0.55)
    p.part(p.ell(64, 56, 8, 8), _pal(IRON), p.sphere(61, 53, 8, 8))
    return p.finish()


def th_bones():
    mc, p = _P()
    bone = _pal(ramp("#2e2620", "#5a4e40", "#8a7e66", "#b8ac90", "#d0c4a8"))
    for (ax, ay, bx, by) in ((20, 112, 100, 96), (30, 98, 108, 118), (50, 122, 86, 84)):
        m, sh = p.tube([(ax, ay), (bx, by)], 3.5, 3.5)
        p.part(m, bone, sh)
        for (ex, ey) in ((ax, ay), (bx, by)):
            p.part(p.ell(ex - 2, ey, 4.5, 4) | p.ell(ex + 2, ey + 1, 4.5, 4), bone, p.sphere(ex - 1, ey - 1, 6, 5))
    p.part(p.ell(88, 100, 16, 14), bone, p.sphere(84, 96, 16, 14))
    p.part(p.ell(83, 99, 3, 4) | p.ell(94, 99, 3, 4), _pal(BRICK), 0.05, bevel=0)
    return p.finish()


def th_stove():
    mc, p = _P()
    p.part(p.rect(10, 44, 118, 124), _pal(IRON), p.lin(10, 44, 118, 124, 0.6, 0.2) + (p.noise(5, 905) - 0.5) * 0.15)
    p.part(p.rect(8, 38, 120, 48), _pal(IRON), p.lin(0, 38, 0, 48, 0.9, 0.35))
    for cx in (34, 64, 94):
        p.part(p.ell(cx, 42, 12, 4), _pal(IRON), 0.2, bevel=0)
        p.glow(p.ell(cx, 42, 7, 2.2), "#f8962a")
    door = p.rect(26, 68, 102, 114)
    p.part(door, _pal(IRON), p.lin(26, 68, 102, 114, 0.7, 0.25))
    p.part(p.rect(32, 76, 96, 106), _pal(FLAME), 0.1 + 0.4 * np.clip((p.y - 76) / 30, 0, 1), bevel=0)
    for gx in range(36, 96, 8):
        p.part(p.rect(gx, 76, gx + 3, 106), _pal(IRON), 0.35, bevel=0)
    p.part(p.rect(52, 18, 76, 38), _pal(IRON), p.lin(52, 0, 76, 0, 0.8, 0.3))
    return p.finish()


def th_hand():
    mc, p = _P()
    st = _pal(STONE)
    p.part(p.rect(52, 86, 78, 128), st, p.lin(52, 0, 78, 0, 0.75, 0.3))
    p.part(p.ell(64, 74, 26, 24), st, p.sphere(58, 68, 26, 24))
    for k, ang in enumerate((-0.42, -0.14, 0.14, 0.42)):
        ln = (40, 46, 44, 36)[k]
        m, sh = p.tube([(64 + np.sin(ang) * 14, 64), (64 + np.sin(ang) * ln, 74 - np.cos(ang) * ln)], 5.5, 4.5)
        p.part(m, st, sh)
    m, sh = p.tube([(44, 80), (30, 64), (24, 52)], 6, 5)
    p.part(m, st, sh)
    return p.finish()


def th_glow():
    """A soft round glow (drawn additive: the one billboard with partial alpha, style guide section 6)."""
    y, x = np.mgrid[0:N, 0:N].astype(np.float32)
    d = np.sqrt((x + 0.5 - 64) ** 2 + (y + 0.5 - 64) ** 2) / 64.0
    out = np.zeros((N, N, 4), np.uint8)
    out[..., :3] = (255, 240, 210)
    out[..., 3] = (np.clip(1 - d, 0, 1) ** 2 * 255).astype(np.uint8)
    return out


def th_sign():
    mc, p = _P()
    p.part(p.seg(46, 0, 46, 42, 2.5) | p.seg(82, 0, 82, 42, 2.5), _pal(IRON), 0.5, bevel=0)
    board = p.rect(18, 40, 110, 96)
    p.part(board, _pal(WOOD), p.lin(18, 40, 110, 96, 0.75, 0.3) + 0.06 * np.sin(p.y * 0.8 + p.noise(6, 906) * 5))
    p.part(p.rect(18, 40, 110, 44) | p.rect(18, 92, 110, 96), _pal(GOLD), p.lin(18, 0, 110, 0, 0.85, 0.4))
    for tx in range(30, 100, 14):  # gilt letters, worn
        p.part(p.rect(tx, 56, tx + 8, 58) | p.rect(tx, 56, tx + 2, 78) | p.rect(tx, 66, tx + 6, 68) | (p.rect(tx + 6, 56, tx + 8, 78) & (tx % 28 == 2)), _pal(GOLD), 0.75, bevel=0)
    return p.finish()


PROPS = {"thing_torch": th_torch, "thing_crystal": th_crystal, "thing_mushroom": th_mushroom, "thing_barrel": th_barrel, "thing_lamp": th_lamp, "thing_furnace": th_furnace,
         "thing_door": th_door, "thing_ladder": th_ladder, "thing_rope": th_rope, "thing_cables": th_cables, "thing_skull": th_skull, "thing_coatrack": th_coatrack,
         "thing_valve": th_valve, "thing_bones": th_bones, "thing_stove": th_stove, "thing_hand": th_hand, "thing_glow": th_glow, "thing_sign": th_sign, "thing_hatch": th_hatch}

TILES = {"wall_brick": wall_brick, "wall_brick_dark": wall_brick_dark, "wall_pipe": wall_pipe, "wall_cable": wall_cable, "wall_barrel": wall_barrel, "wall_crystal": wall_crystal,
         "wall_fungus": wall_fungus, "wall_mirror": wall_mirror, "wall_iron": wall_iron, "wall_shelf": wall_shelf, "wall_rock": wall_rock, "wall_door": wall_door,
         "wall_hatch": wall_hatch, "wall_tile": wall_tile, "wall_hands": wall_hands, "wall_brass": wall_brass, "wall_echo": wall_echo, "wall_burrow": wall_burrow,
         "floor_flag": floor_flag, "floor_wood": floor_wood, "floor_grate": floor_grate, "floor_moss": floor_moss, "floor_kitchen": floor_kitchen, "floor_crystal": floor_crystal,
         "floor_mirror": floor_mirror, "floor_dirt": floor_dirt, "floor_straw": floor_straw, "floor_pavement": floor_pavement,
         "ceil_arch": ceil_arch, "ceil_pipes": ceil_pipes, "ceil_rock": ceil_rock, "ceil_crystal": ceil_crystal, "ceil_beams": ceil_beams}


# ---- figures ------------------------------------------------------------------------------------------------------------------------------------------

CREATURES = ["lampmoth", "cable_eel", "barrel_knight", "mildew_mother", "mirror_twin", "bouncer", "rat_king", "furnace_imp", "gargoyle", "echo"]


def _wizard_frames() -> tuple:
    """The trial's wizard portrait (the owner's sprite) as a billboard: hard alpha, 48 colours, edged one step darker, no halo; the attack frame his staff's orb flared."""
    im = Image.open(os.path.join(lib.ROOT, "assets", "trial", "art", "wizard.png")).convert("RGBA").resize((N, N), Image.NEAREST)
    rgba = np.array(im, np.uint8)
    a = rgba[..., 3] > 127
    pal = np.array(Image.fromarray(rgba[..., :3], "RGB").quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert("RGB"), np.uint8)
    rim = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
    pal[rim] = (pal[rim].astype(np.float32) * 0.72).astype(np.uint8)
    idle = np.dstack([np.where(a[..., None], pal, 0), np.where(a, 255, 0)]).astype(np.uint8)
    att = idle.copy()
    hot = a & (pal.astype(np.int32).sum(-1) > 330)  # the brightest pixels (the orb and its sparks) burn hotter
    att[hot, :3] = (255, 236, 180)
    return idle, att


def build() -> dict:
    os.makedirs(OUT, exist_ok=True)
    for fn in os.listdir(OUT):
        if fn.endswith(".png"):
            os.remove(os.path.join(OUT, fn))
    section = {}

    def reg(tid, arr, mode, metres):
        im = Image.fromarray(arr, mode)
        im.save(os.path.join(OUT, tid + ".png"), optimize=False, compress_level=9)
        section[tid] = {"file": f"textures/{tid}.png", "size": [im.width, im.height], "metres": metres}

    for tid in sorted(TILES):
        rgb, metres = TILES[tid]()
        reg(tid, rgb, "RGB", metres)
    for k in range(4):  # the water: a base tile and three frames the map swaps through
        rgb, metres = water(k)
        reg("water" if k == 0 else f"water_{k}", rgb, "RGB", metres)
    reg("sky_dawn", sky_dawn(), "RGB", 1.0)
    for tid in sorted(PROPS):
        reg(tid, PROPS[tid](), "RGBA", 1.0)
    mc = _mc()
    for name in sorted(CREATURES):
        for pose in mc.POSES:
            reg(f"fig_{name}_{pose}", mc.frame(name, pose, N), "RGBA", 1.0)
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
