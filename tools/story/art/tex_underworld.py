"""The Underworld's procedural pixel textures (docs/STORY_25D_ART_DIRECTION.md 2.D): red and black with ember orange.

`build()` returns the opaque tiles {id: (rgb uint8 (n, n, 3), metres)} that `tiles.procedural` writes after the Godot bake (an id equal to a baked tile
replaces it). The billboard props (`thing_*`, RGBA with a hard alpha for the scissor) are written here directly into the chapter's textures folder,
because `pixeltex.save` writes RGB; their metres are listed in `tiles.UNDERWORLD`. Everything is deterministic (seeded generators, no clock).

Surfaces: obsidian with glints (court floor, tiers' walls of the court), scorched brick (the arena), bone walls (the ossuary risers), iron plates with rivets
and rust (the furnace), a tread-plate floor, rusty pipes, the cage's bars, the arena's stone tiers, a carpet runner up the throne stair, a bone bridge, a basalt
platform and the lava: molten cracks glowing between dark crust plates.
Props: a brazier, a hanging chain, a skull, an anvil, tongs and hammers on a rack, the throne, a ticket booth, a rope barrier, the furnace mouth, a column.
"""
from __future__ import annotations

import os

import numpy as np

from . import lib
from .pixeltex import (bricks, grid, hexc, mix_rgb, noise, panels, pipes, quantise, ramp, rust, speckle, grime)

# ---- palettes (dark to light) ------------------------------------------------------------------------------------------------------------------
OBSIDIAN = ramp("#040306", "#0c0810", "#16101c", "#221828", "#302238", "#46304e")
GLINT = ramp("#5a3a6a", "#a070c0", "#e0b8ff")
LAVA = ramp("#120403", "#2a0805", "#4a0e06", "#7a1606", "#b42a08", "#e8520c", "#ff8a1c", "#ffc244", "#fff0a8")
SOOT_BRICK = ramp("#0a0505", "#1a0b09", "#2c120e", "#421a14", "#5a241a", "#743222")
MORTAR = ramp("#060303", "#140a08", "#2a1410")
BONE = ramp("#1a120c", "#3a2c20", "#5e4c38", "#8a7656", "#b4a078", "#d8c8a0", "#efe4c4")
IRON = ramp("#0c0b0e", "#18171c", "#26242a", "#36333a", "#4a464e", "#625c64")
RUST = ramp("#2a0e06", "#4e1c0a", "#7a3010", "#a44a1a")
STONE = ramp("#0e0808", "#1e1212", "#2e1c1a", "#422a24", "#58382e", "#704a3a")
CARPET = ramp("#1a0204", "#360508", "#5a0a0e", "#861418", "#b02020")
GOLD = ramp("#3a2008", "#7a4a10", "#c08a20", "#f0c850")
BASALT = ramp("#080506", "#140c0c", "#221414", "#321c1a", "#442622")
HEAT = ramp("#3a0a04", "#8a1a06", "#e0480a", "#ff9a20", "#ffe070")


def _rng(seed: int) -> np.random.RandomState:
    return np.random.RandomState(seed)


def _worley(n: int, cells: int, seed: int):
    """Tileable cellular noise: (f1, f2, cell id) in pixels, cells x cells jittered points wrapping around the tile."""
    rng = _rng(seed)
    pts = (np.stack(np.mgrid[0:cells, 0:cells], -1).reshape(-1, 2)[:, ::-1] + 0.15 + rng.rand(cells * cells, 2) * 0.7) * (n / cells)
    x, y = grid(n)
    f1 = np.full((n, n), 1e9, np.float32)
    f2 = np.full((n, n), 1e9, np.float32)
    ids = np.zeros((n, n), np.int32)
    for k, (px, py) in enumerate(pts):
        dx = np.abs(x - px)
        dx = np.minimum(dx, n - dx)
        dy = np.abs(y - py)
        dy = np.minimum(dy, n - dy)
        d = np.sqrt(dx * dx + dy * dy)
        closer = d < f1
        f2 = np.where(closer, f1, np.minimum(f2, d))
        ids = np.where(closer, k, ids)
        f1 = np.where(closer, d, f1)
    return f1, f2, ids


def _tone(ids: np.ndarray, count: int, seed: int) -> np.ndarray:
    return _rng(seed).rand(count).astype(np.float32)[ids]


# ---- surfaces ------------------------------------------------------------------------------------------------------------------------------------

def lava(n: int = 128):
    """Dark crust plates drifting on melt: the seams between plates glow white-hot to orange, the plates carry faint warm veins and cooling spots."""
    f1, f2, ids = _worley(n, 4, 101)
    seam = (f2 - f1) * (0.6 + 0.8 * noise(n, 24, 107, 2))  # the seams widen and narrow: rivers and hairlines
    melt = np.clip(1.0 - seam / 8.0, 0, 1) ** 1.3
    wide = np.clip(1.0 - seam / 16.0, 0, 1) ** 2.0
    crust = 0.05 + 0.08 * _tone(ids, 25, 102) + (noise(n, 10, 103, 3) - 0.5) * 0.16
    crust += 0.18 * np.clip(noise(n, 6, 104, 2) - 0.7, 0, 1) * 3.0  # hot spots breaking through the crust
    veins = np.clip(1.0 - np.abs(noise(n, 18, 105, 3) - 0.5) * 14.0, 0, 1) * 0.22
    sh = np.maximum(crust + veins + wide * 0.3, melt * (0.85 + 0.25 * noise(n, 8, 106, 2)))
    return quantise(np.clip(sh, 0, 1), LAVA), 4.0


def obsidian(n: int = 128):
    """Black volcanic glass slabs: conchoidal sheen in bands, hairline seams, violet and ember glints."""
    f1, f2, ids = _worley(n, 3, 111)
    seam = (f2 - f1) < 1.3
    t = _tone(ids, 9, 112)
    x, y = grid(n)
    sheen = 0.5 + 0.5 * np.sin((x * 0.9 + y * 0.6) / n * 2 * np.pi * (2 + (ids % 3)) + t * 6.0 + noise(n, 16, 113) * 4.0)
    sh = 0.22 + 0.18 * t + 0.28 * sheen ** 6 + (noise(n, 8, 114) - 0.5) * 0.1
    sh = np.where(seam, 0.02, sh)
    rgb = quantise(np.clip(sh, 0, 1), OBSIDIAN)
    gl = speckle(n, 0.006, 115) * (sheen > 0.6) * (~seam)
    rgb = mix_rgb(rgb, quantise(np.full((n, n), 0.9, np.float32), GLINT), gl)
    ember = speckle(n, 0.002, 116) * (~seam)
    rgb[ember > 0.5] = (hexc("#ff7a30") * 255).astype(np.uint8)
    return rgb, 2.5


def obsidian_wall(n: int = 128):
    """The court's walls: obsidian ashlar in tall courses, a carved pilaster every repeat, soot rising from the floor."""
    x, y = grid(n)
    sh, mort = bricks(n, rows=4, cols=2, mortar=1, seed=121, wear=0.2)
    sh = 0.18 + sh * 0.35
    pil = (x > n * 0.42) & (x < n * 0.58)
    sh = np.where(pil, 0.32 + 0.22 * (x < n * 0.45) - 0.18 * (x > n * 0.55) + (noise(n, 6, 122) - 0.5) * 0.08, sh)
    flute = pil & (np.abs((x - n * 0.5) % 4 - 2) < 0.6)
    sh = np.where(flute, sh - 0.12, sh)
    sheen = (0.5 + 0.5 * np.sin((x + y * 1.4) / n * 2 * np.pi * 3)) ** 8
    sh += sheen * 0.16 * (~pil)
    rgb = quantise(np.clip(sh, 0, 1), OBSIDIAN)
    rgb = np.where(((mort > 0.5) & ~pil)[..., None], quantise(np.full((n, n), 0.6, np.float32), MORTAR), rgb)
    gl = speckle(n, 0.004, 123) * (sheen > 0.5)
    rgb[gl > 0.5] = (hexc("#c090ff") * 255).astype(np.uint8)
    return rgb, 3.0


def scorched_brick(n: int = 128):
    """The arena's brick: oxblood courses blackened by fire, crumbling mortar, soot streaks and a few embers lodged in the joints."""
    sh, mort = bricks(n, rows=10, cols=4, mortar=1, seed=131, wear=0.5)
    soot = grime(n, 132, 0.9, drip=True)
    scorch = np.clip((noise(n, 20, 133, 3) - 0.45) * 2.5, 0, 1)
    sh = sh * (1.0 - 0.55 * soot) * (1.0 - 0.45 * scorch)
    rgb = quantise(np.clip(sh, 0, 1), SOOT_BRICK)
    mrgb = quantise(np.clip(0.4 + (noise(n, 4, 134) - 0.5) * 0.6, 0, 1), MORTAR)
    rgb = np.where((mort > 0.5)[..., None], mrgb, rgb)
    ember = (mort > 0.5) & (speckle(n, 0.05, 135) > 0.5) & (noise(n, 10, 136) > 0.6)
    rgb[ember] = (hexc("#ff6a1a") * 255).astype(np.uint8)
    return rgb, 2.5


def _skull(canvas_sh, canvas_m, cx, cy, s, n):
    """Stamp a skull face into a shade field (wrapping): cranium, eye sockets, nose, teeth row."""
    x, y = grid(n)
    dx = (x - cx + n / 2) % n - n / 2
    dy = (y - cy + n / 2) % n - n / 2
    head = (dx / s) ** 2 + ((dy + s * 0.15) / (s * 0.9)) ** 2 < 1.0
    jaw = (np.abs(dx) < s * 0.55) & (dy > s * 0.4) & (dy < s * 0.95)
    m = head | jaw
    light = np.clip(0.75 - (dx + dy) / (s * 3.0), 0.3, 1.0)
    canvas_sh[:] = np.where(m, light, canvas_sh)
    eye = ((np.abs(dx) - s * 0.36) ** 2 / (s * 0.24) ** 2 + (dy - s * 0.05) ** 2 / (s * 0.22) ** 2) < 1.0
    nose = (np.abs(dx) < s * 0.1 + (dy - s * 0.25) * 0.25) & (dy > s * 0.22) & (dy < s * 0.45)
    teeth = jaw & (dy > s * 0.58) & (dy < s * 0.85) & ((np.floor((dx + s) / (s * 0.18)) % 2) == 0)
    canvas_sh[:] = np.where(eye | nose, 0.02, canvas_sh)
    canvas_sh[:] = np.where(teeth, 0.25, canvas_sh)
    canvas_m[:] = np.maximum(canvas_m, m.astype(np.float32))


def bone_wall(n: int = 128):
    """An ossuary wall: rows of skulls between courses of stacked long bones, dark gaps, soot."""
    x, y = grid(n)
    sh = np.full((n, n), 0.05, np.float32)
    m = np.zeros((n, n), np.float32)
    rows = 4
    rh = n / rows
    for r in range(rows):
        y0 = r * rh
        if r % 2 == 0:  # a course of long bones, each a shaft with knobbed ends
            for k in range(3):
                yy = y0 + 3 + k * (rh - 6) / 3 + 2
                ly = y - yy
                shaft = np.abs(ly) < 2.2
                off = (k * 13 + r * 7) % 24
                u = (x + off) % 24
                knob = ((u < 4) | (u > 20)) & (np.abs(ly) < 3.4)
                bone = (shaft | knob) & ~((u > 10) & (u < 11.5))  # a gap between bones
                shade = 0.62 + 0.25 * (ly < -0.8) - 0.25 * (ly > 1.2)
                sh = np.where(bone, shade, sh)
                m = np.maximum(m, bone.astype(np.float32))
        else:
            for c in range(4):
                _skull(sh, m, (c + 0.5 + (r % 4 == 3) * 0.5) * n / 4, y0 + rh * 0.5, rh * 0.36, n)
    sh += (noise(n, 6, 141) - 0.5) * 0.18 * m
    soot = grime(n, 142, 0.6, drip=True)
    sh *= 1.0 - 0.45 * soot
    return quantise(np.clip(sh, 0, 1), BONE), 2.0


def bone_bridge(n: int = 128):
    """The bone bridge's deck: rib bones laid across (rows along z) between knobbly spines of vertebrae, gaps dark with a faint glow from the lava below."""
    x, y = grid(n)
    count = 8
    s = n / count
    ly = y % s
    r = np.floor(y / s).astype(int)
    curve = np.sin(x / n * 2 * np.pi * 2 + r * 1.7) * 1.4
    half = s * (0.32 + 0.08 * np.sin(x / n * 2 * np.pi * 4 + r))  # ribs taper and swell along their length
    d = np.abs(ly - s / 2 - curve)
    rib = d < half
    sh = 0.78 - 0.5 * (d / half) ** 2 - 0.25 * ((ly - s / 2 - curve) > half * 0.4) + (noise(n, 8, 151) - 0.5) * 0.2
    sh -= 0.18 * _rng(152).rand(count)[r % count]
    sx = np.abs((x % (n / 2)) - n / 4)  # a spine every half tile: vertebrae as round knuckles across the ribs
    vert = (sx < 5.5) & (np.abs(((y + s / 2) % s) - s / 2) < s * 0.42)
    vsh = 0.85 - sx / 5.5 * 0.4 + (noise(n, 4, 155) - 0.5) * 0.15
    m = rib | vert
    sh = np.where(vert, vsh, sh)
    rgb = quantise(np.clip(sh, 0, 1), BONE)
    glow = quantise(np.clip(0.02 + 0.3 * noise(n, 12, 153) ** 2, 0, 1), HEAT)
    rgb = np.where((~m)[..., None], glow, rgb)
    cracks = (np.abs(noise(n, 10, 154, 3) - 0.5) < 0.012) & rib & ~vert
    rgb[cracks] = (hexc("#3a2c20") * 255).astype(np.uint8)
    soot = grime(n, 156, 0.5, drip=False) > 0.5
    rgb = mix_rgb(rgb, np.broadcast_to((hexc("#2a1c14") * 255).astype(np.uint8), rgb.shape), (soot & m).astype(np.float32) * 0.5)
    return rgb, 2.0


def iron_plates(n: int = 128):
    """The furnace walls: riveted iron plates, rust blooms, heat-blued bands, soot running down from the seams."""
    sh, seam = panels(n, count=2, seed=161, rivets=True)
    sh = 0.15 + sh * 0.55
    rs = rust(n, 162, 0.45)
    soot = grime(n, 163, 0.7)
    sh *= 1.0 - 0.35 * soot
    rgb = quantise(np.clip(sh, 0, 1), IRON)
    rrgb = quantise(np.clip(0.1 + noise(n, 4, 164) * 0.6, 0, 1), RUST)
    rgb = mix_rgb(rgb, rrgb, ((rs > 0.4) & (seam < 0.5)).astype(np.float32) * 0.8)
    rgb[seam > 0.5] = (hexc("#060506") * 255).astype(np.uint8)
    x, y = grid(n)
    streak = (rs > 0.2) & (speckle(n, 0.6, 165) > 0.5) & (((x * 7) % 11) < 2)
    rgb = mix_rgb(rgb, rrgb, streak.astype(np.float32) * 0.6)
    return rgb, 2.5


def tread_floor(n: int = 64):
    """The furnace floor: diamond tread plate, scuffed bright in the middle, rust and scale at the edges."""
    x, y = grid(n)
    u = (x + (np.floor(y / 8) % 2) * 4) % 8
    v = y % 8
    diamond = (np.abs(u - 4 + (v - 4) * 0.6) < 1.1) & (np.abs(v - 4) < 2.6)
    sh = 0.35 + (noise(n, 12, 171) - 0.5) * 0.3
    sh = np.where(diamond, sh + 0.25, sh)
    sh = np.where(np.roll(diamond, 1, axis=0) & ~diamond, sh - 0.2, sh)
    seam = (x % 32 < 1) | (y % 32 < 1)
    sh = np.where(seam, 0.05, sh)
    rgb = quantise(np.clip(sh, 0, 1), IRON)
    rs = rust(n, 172, 0.6)
    rgb = mix_rgb(rgb, quantise(np.clip(0.2 + noise(n, 4, 173) * 0.6, 0, 1), RUST), rs * 0.8)
    return rgb, 1.5


def rusty_pipes(n: int = 128):
    """The furnace ceiling: a bundle of rusted pipes with flanges over dark plate."""
    sh, m = pipes(n, count=5, horizontal=True, seed=181)
    back = quantise(np.full((n, n), 0.12, np.float32) + (noise(n, 8, 182) - 0.5) * 0.1, IRON)
    rgb = quantise(np.clip(sh * 0.9, 0, 1), IRON)
    rs = rust(n, 183, 0.8)
    rgb = mix_rgb(rgb, quantise(np.clip(sh * 0.8 + 0.1, 0, 1), RUST), rs)
    return np.where((m > 0.5)[..., None], rgb, back), 2.5


def cage_bars(n: int = 64):
    """Cage bars: round iron bars with a lit edge, rust flaking, crossbars riveted, black beyond."""
    x, y = grid(n)
    back = quantise(np.clip(0.08 + (noise(n, 10, 191) - 0.5) * 0.12, 0, 1), BASALT)
    s = n / 5
    lx = x % s - s / 2
    bar = np.abs(lx) < 2.2
    sh = 0.55 - lx / 2.2 * 0.35
    cross = ((np.abs(y - n * 0.14) < 2) | (np.abs(y - n * 0.84) < 2))
    sh = np.where(cross, 0.5 + 0.2 * (np.abs(y - n * 0.14) < 1), sh)
    m = bar | cross
    rgb = quantise(np.clip(sh, 0, 1), IRON)
    rs = rust(n, 192, 0.8)
    rgb = mix_rgb(rgb, quantise(np.clip(sh * 0.9, 0, 1), RUST), rs * 0.9)
    rivet = cross & bar & (np.abs(lx) < 1.2)
    rgb[rivet] = (hexc("#8a8090") * 255).astype(np.uint8)
    return np.where(m[..., None], rgb, back), 1.5


def stone_tiers(n: int = 128):
    """The arena's tiers: worn stone benches in bands (the bands run along z, so they read as tiers from the pit), cracked, with dark soot at each riser."""
    x, y = grid(n)
    count = 4
    s = n / count
    lx = x % s
    band = np.floor(x / s).astype(int)
    sh = 0.42 + 0.22 * (lx < 3) - 0.3 * (lx > s - 4) + 0.12 * _rng(201).rand(count)[band % count]
    blocks = (((y + band * 11) % 24) < 1)
    sh = np.where(blocks, 0.12, sh)
    sh += (noise(n, 8, 202) - 0.5) * 0.25
    worn = noise(n, 20, 203, 3) > 0.62
    sh = np.where(worn & (lx < s - 4), sh + 0.08, sh)
    cracks = np.abs(noise(n, 12, 204, 3) - 0.5) < 0.01
    sh = np.where(cracks, 0.08, sh)
    return quantise(np.clip(sh, 0, 1), STONE), 4.0


def carpet_runner(n: int = 128):
    """The throne stair's runner: a crimson carpet with gold borders centred on the stair's middle line (the tile's top edge, z = 4 m with 4 m per repeat),
    over obsidian steps either side. Worn paler along its centre."""
    x, y = grid(n)
    d = np.minimum(y, n - y)  # distance from the runner's centre line (row 0 wraps)
    half = n * 0.2  # 0.8 m either side
    run = d < half
    border = run & (d > half - 4)
    pattern = ((x // 8 + y // 8) % 2 == 0) & (d < half - 8) & (np.abs((x % 8) - 4) + np.abs((y % 8) - 4) < 3)
    wear = np.clip(1.0 - d / (half * 0.6), 0, 1) * 0.25 * noise(n, 10, 211)
    sh = 0.55 + wear + (noise(n, 6, 212) - 0.5) * 0.15 - 0.15 * pattern
    rgb_c = quantise(np.clip(sh, 0, 1), CARPET)
    rgb_b = quantise(np.clip(0.55 + 0.35 * ((x % 6) < 3) - 0.3 * (d > half - 1.5), 0, 1), GOLD)
    ob, _ = obsidian(n)
    out = np.where(run[..., None], rgb_c, ob)
    out = np.where(border[..., None], rgb_b, out)
    nose = (x % 32) < 2  # the step's nosing every 1 m along x
    out = np.where((nose & ~run)[..., None], (hexc("#4a3458") * 255).astype(np.uint8), out)
    return out, 4.0


def checker_floor(n: int = 128):
    """The arena floor: black and oxblood flagstones in a checker, cracked, with ember light in the cracks and scuffs from a thousand hooves."""
    x, y = grid(n)
    s = n / 4
    chk = (((x // s) + (y // s)) % 2).astype(np.float32)
    lx, ly = x % s, y % s
    edge = (lx < 1) | (ly < 1)
    sh = 0.18 + 0.32 * chk + 0.1 * (lx + ly < 6) - 0.08 * ((lx > s - 2) | (ly > s - 2)) + (noise(n, 8, 221) - 0.5) * 0.2
    scuff = noise(n, 4, 222, 2) > 0.7
    sh = np.where(scuff, sh + 0.08, sh)
    pal = ramp("#060304", "#14080a", "#260c0e", "#3e1412", "#581c16", "#6e281c")
    rgb = quantise(np.clip(sh, 0, 1), pal)
    rgb[edge] = (hexc("#040203") * 255).astype(np.uint8)
    crack = (np.abs(noise(n, 14, 223, 3) - 0.5) < 0.008) & ~edge & (noise(n, 32, 224, 2) > 0.5)
    rgb[crack] = (hexc("#ff5a14") * 255).astype(np.uint8)
    halo = (np.abs(noise(n, 14, 223, 3) - 0.5) < 0.02) & ~crack & ~edge & (noise(n, 32, 224, 2) > 0.5)
    rgb = mix_rgb(rgb, np.broadcast_to((hexc("#8a2008") * 255).astype(np.uint8), rgb.shape), halo.astype(np.float32) * 0.6)
    return rgb, 3.0


def basalt(n: int = 128):
    """The pit platform: the tops of basalt columns, each its own tone, hairline joints lit orange from the lava beneath."""
    f1, f2, ids = _worley(n, 4, 231)
    seam = (f2 - f1) < 1.6
    t = _tone(ids, 16, 232)
    sh = 0.3 + 0.35 * t - 0.25 * np.clip(f1 / (n / 4), 0, 1) * 0.5 + (noise(n, 6, 233) - 0.5) * 0.2
    rgb = quantise(np.clip(sh, 0, 1), BASALT)
    glow = quantise(np.clip(0.1 + 0.5 * noise(n, 16, 234), 0, 1), HEAT)
    hot = seam & (noise(n, 24, 235, 2) > 0.5)
    rgb[seam] = (hexc("#050303") * 255).astype(np.uint8)
    return np.where(hot[..., None], glow, rgb), 3.0


def cave_rock(n: int = 128):
    """Volcanic rock for the cave walls and the bridge's sides: lumpy, layered, with glowing fissures."""
    x, y = grid(n)
    f1, f2, ids = _worley(n, 4, 241)
    t = _tone(ids, 16, 242)
    sh = 0.2 + 0.3 * t + 0.3 * np.clip(1 - f1 / (n / 5), 0, 1) - 0.2 * (y % 21 < 2) + (noise(n, 6, 243) - 0.5) * 0.25
    rgb = quantise(np.clip(sh, 0, 1), STONE)
    fis = (f2 - f1) < 1.2
    hot = fis & (noise(n, 20, 244, 2) > 0.55)
    rgb[fis] = (hexc("#080404") * 255).astype(np.uint8)
    rgb[hot] = (hexc("#e8460c") * 255).astype(np.uint8)
    return rgb, 3.0


def court_ceiling(n: int = 64):
    """The court's vault: obsidian ribs crossing in a grid with dark coffers between."""
    x, y = grid(n)
    rib = (np.abs(x % 32 - 16) > 13) | (np.abs(y % 32 - 16) > 13)
    sh = np.where(rib, 0.45 + 0.2 * ((x % 32) < 2) + (noise(n, 4, 251) - 0.5) * 0.2, 0.1 + (noise(n, 8, 252) - 0.5) * 0.1)
    return quantise(np.clip(sh, 0, 1), OBSIDIAN), 2.5


def rock_ceiling(n: int = 64):
    """The arena's roof: rough rock with the hanging tips of stalactites, warm underlight on the lumps."""
    f1, f2, ids = _worley(n, 3, 261)
    t = _tone(ids, 9, 262)
    tip = np.clip(1.0 - f1 / 6.0, 0, 1)
    sh = 0.12 + 0.2 * t + 0.5 * tip ** 2 - 0.1 * ((f2 - f1) < 1.5)
    return quantise(np.clip(sh + (noise(n, 4, 263) - 0.5) * 0.1, 0, 1), STONE), 2.5


def iron_dais(n: int = 64):
    """The gate dais and the pit stage: heavy riveted iron, hammered, rimmed with a hot glowing seam."""
    sh, seam = panels(n, count=2, seed=271, rivets=True)
    sh = 0.3 + sh * 0.55 + (noise(n, 3, 272) - 0.5) * 0.12
    rgb = quantise(np.clip(sh, 0, 1), IRON)
    rgb[seam > 0.5] = (hexc("#c8380a") * 255).astype(np.uint8)
    return rgb, 2.0


# ---- props (RGBA billboards) -----------------------------------------------------------------------------------------------------------------------

class Sprite:
    """A 128 x 128 RGBA canvas for a prop: shapes are masks, shaded by a ramp with dithering; alpha is hard (the billboard uses an alpha scissor)."""

    def __init__(self, n: int = 128):
        self.n = n
        self.rgb = np.zeros((n, n, 3), np.uint8)
        self.a = np.zeros((n, n), np.uint8)
        self.x, self.y = np.mgrid[0:n, 0:n][::-1].astype(np.float32)

    def paint(self, mask: np.ndarray, shade, pal: np.ndarray) -> None:
        sh = shade if isinstance(shade, np.ndarray) else np.full((self.n, self.n), float(shade), np.float32)
        col = quantise(np.clip(sh, 0, 1), pal)
        self.rgb[mask] = col[mask]
        self.a[mask] = 255

    def solid(self, mask: np.ndarray, colour: str) -> None:
        self.rgb[mask] = (hexc(colour) * 255).astype(np.uint8)
        self.a[mask] = 255

    def rect(self, x0, y0, x1, y1) -> np.ndarray:
        return (self.x >= x0) & (self.x < x1) & (self.y >= y0) & (self.y < y1)

    def ellipse(self, cx, cy, rx, ry) -> np.ndarray:
        return ((self.x - cx) / rx) ** 2 + ((self.y - cy) / ry) ** 2 <= 1.0

    def tri(self, pts) -> np.ndarray:
        """Inside a convex polygon given clockwise or anticlockwise."""
        m = np.ones((self.n, self.n), bool)
        k = len(pts)
        sgn = None
        for i in range(k):
            (ax, ay), (bx, by) = pts[i], pts[(i + 1) % k]
            c = (bx - ax) * (self.y + 0.5 - ay) - (by - ay) * (self.x + 0.5 - ax)
            s = c >= 0
            if sgn is None:
                area = sum(pts[j][0] * pts[(j + 1) % k][1] - pts[(j + 1) % k][0] * pts[j][1] for j in range(k))
                sgn = area > 0
            m &= s if sgn else (c <= 0)
        return m

    def line(self, ax, ay, bx, by, w) -> np.ndarray:
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = np.clip(((self.x - ax) * dx + (self.y - ay) * dy) / L2, 0, 1)
        px, py = ax + t * dx, ay + t * dy
        return (self.x - px) ** 2 + (self.y - py) ** 2 <= (w * 0.5) ** 2

    def rgba(self) -> np.ndarray:
        return np.dstack([self.rgb, self.a])


def _hshade(sp: Sprite, x0, x1, base=0.5, amp=0.35):
    """A cylinder's left-lit shade across x0..x1."""
    u = np.clip((sp.x - x0) / max(x1 - x0, 1), 0, 1)
    return base + amp * (0.6 - u) + 0.1 * np.sin(u * np.pi)


def _flames(sp: Sprite, cx, base_y, w, h, seed):
    """Tongues of fire rising from base_y: white core, yellow, orange, red tips (static; the brazier's glow does the flicker)."""
    rng = _rng(seed)
    nz = noise(sp.n, 6, seed, 2)
    for k in range(5):
        fx = cx + (k - 2) * w * 0.18 + rng.uniform(-2, 2)
        fh = h * (0.55 + 0.45 * rng.rand()) * (1.0 - abs(k - 2) * 0.18)
        fw = w * 0.22
        u = (base_y - sp.y) / fh
        wid = fw * np.clip(1 - u, 0, 1) ** 0.8 * (0.8 + 0.4 * nz)
        m = (u >= 0) & (u <= 1) & (np.abs(sp.x - fx - u * u * 3 * np.sin(k + 1)) < wid)
        heat = np.clip(1.0 - u * 1.1 - np.abs(sp.x - fx) / (fw * 1.5) * 0.4, 0, 1)
        sp.paint(m, 0.25 + 0.75 * heat, HEAT)


def th_brazier():
    """An iron fire bowl on three legs, coals glowing, flames licking up."""
    sp = Sprite()
    for (ax, bx) in ((44, 30), (84, 98), (64, 64)):
        sp.paint(sp.line(ax, 74, bx, 124, 5), 0.35 if ax != 84 else 0.2, IRON)
    sp.paint(sp.rect(36, 104, 92, 108), 0.3, IRON)
    bowl = sp.ellipse(64, 66, 34, 18) & (sp.y > 60)
    sp.paint(bowl, _hshade(sp, 30, 98, 0.45), IRON)
    sp.paint(sp.rect(26, 58, 102, 64), _hshade(sp, 26, 102, 0.55), IRON)
    rs = rust(128, 301, 0.7) > 0.5
    sp.paint(bowl & rs, 0.5, RUST)
    for rx in (34, 50, 64, 78, 94):  # rivets on the rim
        sp.solid(sp.ellipse(rx, 61, 1.6, 1.6), "#8a8090")
    coals = sp.ellipse(64, 57, 30, 6)
    sp.paint(coals, 0.3 + 0.6 * noise(128, 4, 302), HEAT)
    _flames(sp, 64, 58, 60, 54, 303)
    return sp.rgba()


def th_chain():
    """A hanging chain: oval iron links alternating face-on and edge-on, a hook at the bottom."""
    sp = Sprite()
    for k in range(11):
        cy = 4 + k * 11
        if k % 2 == 0:
            ring = sp.ellipse(64, cy, 5, 7) & ~sp.ellipse(64, cy, 2.4, 4.2)
            sp.paint(ring, _hshade(sp, 59, 69, 0.55), IRON)
        else:
            sp.paint(sp.rect(62, cy - 7, 66, cy + 7), _hshade(sp, 62, 66, 0.45), IRON)
    rs = (rust(128, 311, 0.6) > 0.5) & (sp.a > 0)
    sp.paint(rs, 0.5, RUST)
    hook = (sp.ellipse(64, 118, 8, 8) & ~sp.ellipse(64, 118, 5, 5) & (sp.y > 116)) | sp.rect(70, 108, 73, 118)
    sp.paint(hook, 0.6, IRON)
    return sp.rgba()


def th_skull():
    """A horned demon skull mounted on a column: bone, dark sockets with an ember in each."""
    sp = Sprite()
    head = sp.ellipse(64, 56, 34, 32)
    jaw = sp.rect(42, 70, 86, 100) & sp.ellipse(64, 78, 24, 26)
    sp.paint(head | jaw, np.clip(0.7 - (sp.x - 64 + sp.y - 56) / 140.0, 0, 1), BONE)
    for sx in (-1, 1):
        horn = sp.line(64 + sx * 26, 40, 64 + sx * 48, 14, 10) | sp.line(64 + sx * 48, 14, 64 + sx * 46, 2, 5)
        sp.paint(horn, 0.35 + 0.2 * (sp.y < 24), BONE)
        eye = sp.ellipse(64 + sx * 14, 58, 9, 8)
        sp.solid(eye, "#0a0404")
        sp.solid(sp.ellipse(64 + sx * 14, 59, 2.5, 2.5), "#ff6a14")
    sp.solid(sp.tri([(60, 70), (68, 70), (64, 78)]), "#0a0404")
    for k in range(6):
        sp.solid(sp.rect(46 + k * 6, 86, 48 + k * 6, 94), "#2a1c12")
    sp.solid(sp.rect(44, 84, 84, 85), "#2a1c12")
    sp.paint(sp.rect(40, 104, 88, 124), _hshade(sp, 40, 88, 0.45), IRON)  # the bracket
    return sp.rgba()


def th_anvil():
    """A smith's anvil on a stump: horn, face polished bright, a glowing billet on it."""
    sp = Sprite()
    sp.paint(sp.rect(38, 92, 90, 126), 0.3 + 0.3 * noise(128, 6, 321), STONE)  # the stump
    body = sp.rect(18, 50, 110, 66) | sp.tri([(18, 50), (2, 54), (18, 62)]) | sp.rect(48, 66, 80, 92) | sp.rect(36, 84, 92, 94)
    sp.paint(body, _hshade(sp, 2, 110, 0.4), IRON)
    sp.paint(sp.rect(20, 48, 110, 52), 0.95, IRON)
    sp.paint(sp.rect(44, 40, 84, 48), 0.55 + 0.4 * noise(128, 3, 322), HEAT)  # a hot billet
    sp.paint(sp.line(88, 47, 116, 18, 4), 0.4, IRON)  # a hammer leaning on it
    sp.paint(sp.rect(108, 12, 124, 22), 0.5, IRON)
    return sp.rgba()


def th_tongs():
    """A rack of smith's tools: tongs, hammers and a poker hanging from an iron rail, glowing tips on two."""
    sp = Sprite()
    sp.paint(sp.rect(4, 10, 124, 16), _hshade(sp, 4, 124, 0.5), IRON)
    sp.paint(sp.rect(8, 16, 12, 124) | sp.rect(116, 16, 120, 124), 0.3, IRON)
    # tongs
    sp.paint(sp.line(30, 18, 24, 100, 4) | sp.line(34, 18, 40, 100, 4), 0.45, IRON)
    sp.paint(sp.line(24, 100, 30, 116, 4) | sp.line(40, 100, 34, 116, 4), 0.7, HEAT)
    # hammers
    for hx, ln in ((58, 70), (76, 80)):
        sp.paint(sp.rect(hx - 2, 18, hx + 2, 18 + ln), 0.5, STONE)
        sp.paint(sp.rect(hx - 9, 18 + ln, hx + 9, 30 + ln), _hshade(sp, hx - 9, hx + 9, 0.5), IRON)
    # poker
    sp.paint(sp.rect(96, 18, 99, 112), 0.4, IRON)
    sp.paint(sp.rect(95, 104, 100, 116), 0.85, HEAT)
    return sp.rgba()


def th_throne():
    """The throne: a tall black-iron back with horns and a skull crest, a crimson seat, armrests of bone."""
    sp = Sprite()
    back = sp.tri([(30, 20), (98, 20), (92, 92), (36, 92)])
    sp.paint(back, _hshade(sp, 30, 98, 0.35) + 0.1 * noise(128, 5, 331), IRON)
    sp.paint(sp.tri([(38, 28), (90, 28), (86, 84), (42, 84)]), 0.5 + 0.2 * noise(128, 8, 332), CARPET)
    for sx in (-1, 1):
        sp.paint(sp.line(64 + sx * 34, 22, 64 + sx * 52, 0, 7), 0.5, BONE)
        sp.paint(sp.line(64 + sx * 30, 24, 64 + sx * 40, 4, 5), 0.35, BONE)
    sp.paint(sp.ellipse(64, 20, 12, 11), 0.75, BONE)
    sp.solid(sp.ellipse(60, 20, 3, 3) | sp.ellipse(68, 20, 3, 3), "#ff3a10")
    sp.paint(sp.rect(24, 84, 104, 98), _hshade(sp, 24, 104, 0.5), CARPET)
    sp.paint(sp.rect(18, 70, 34, 80) | sp.rect(94, 70, 110, 80), 0.7, BONE)
    sp.paint(sp.rect(22, 80, 30, 124) | sp.rect(98, 80, 106, 124), 0.3, IRON)
    sp.paint(sp.rect(30, 98, 98, 124), _hshade(sp, 30, 98, 0.25), IRON)
    sp.paint(sp.rect(40, 100, 88, 104), 0.9, GOLD)
    return sp.rgba()


def th_booth():
    """The gate's ticket booth: a little iron kiosk with a lit hatch, a sign of horns and ADMIT ONE stubs pinned on."""
    sp = Sprite()
    sp.paint(sp.rect(20, 34, 108, 126), _hshade(sp, 20, 108, 0.35) + 0.08 * noise(128, 6, 341), IRON)
    sp.paint(sp.tri([(12, 36), (116, 36), (100, 16), (28, 16)]), 0.45, RUST)
    sp.paint(sp.rect(32, 46, 96, 82), 0.75 + 0.2 * noise(128, 8, 342), HEAT)  # the lit hatch
    sp.solid(sp.rect(32, 64, 96, 66), "#1a0806")
    sp.paint(sp.rect(26, 82, 102, 88), 0.6, IRON)  # the counter
    for k in range(4):  # ticket stubs
        sp.paint(sp.rect(28 + k * 18, 94, 40 + k * 18, 104), 0.7, GOLD)
        sp.solid(sp.rect(33 + k * 18, 94, 35 + k * 18, 104), "#3a2008")
    sp.solid(sp.rect(56, 4, 72, 16), "#2a0806")
    sp.paint(sp.line(56, 10, 46, 0, 4) | sp.line(72, 10, 82, 0, 4), 0.6, BONE)
    sp.solid(sp.ellipse(64, 10, 3, 3), "#ff5a14")
    return sp.rgba()


def th_rope():
    """A queue barrier: two brass-capped iron posts and a sagging crimson rope."""
    sp = Sprite()
    for px in (10, 118):
        sp.paint(sp.rect(px - 3, 64, px + 3, 120), _hshade(sp, px - 3, px + 3, 0.45), IRON)
        sp.paint(sp.ellipse(px, 122, 10, 4), 0.35, IRON)
        sp.paint(sp.ellipse(px, 62, 5, 5), 0.8, GOLD)
    x = sp.x
    sag = 70 + 16 * np.sin(np.clip((x - 10) / 108, 0, 1) * np.pi)
    rope = (np.abs(sp.y - sag) < 3) & (x > 10) & (x < 118)
    sp.paint(rope, 0.65 - (sp.y - sag) * 0.1, CARPET)
    return sp.rgba()


def th_furnace():
    """The furnace mouth: an iron arch in riveted plate, a grate, the fire roaring behind it."""
    sp = Sprite()
    body = sp.rect(4, 14, 124, 128)
    sp.paint(body, _hshade(sp, 4, 124, 0.35) + 0.08 * noise(128, 6, 351), IRON)
    sp.paint(sp.ellipse(64, 14, 60, 14) & (sp.y < 14), 0.3, IRON)
    mouth = (sp.ellipse(64, 64, 40, 34) & (sp.y < 64)) | sp.rect(24, 64, 104, 110)
    fire = 0.45 + 0.55 * np.clip(1 - np.abs(sp.x - 64) / 50, 0, 1) * np.clip((sp.y - 40) / 70, 0, 1) + 0.2 * (noise(128, 6, 352) - 0.5)
    sp.paint(mouth, fire, HEAT)
    _flames(sp, 64, 100, 70, 60, 353)
    bars = mouth & (((sp.x - 24) % 14) < 3)
    sp.paint(bars, 0.25, IRON)
    sp.paint(sp.rect(16, 108, 112, 116), 0.5, IRON)
    for k in range(9):
        sp.solid(sp.ellipse(12 + k * 13, 22, 1.8, 1.8), "#8a8090")
    rs = (rust(128, 354, 0.6) > 0.5) & body & ~mouth
    sp.paint(rs, 0.45, RUST)
    return sp.rgba()


def th_column():
    """An obsidian column: fluted shaft with a violet sheen, a bronze collar, chipped capital and base."""
    sp = Sprite()
    shaft = sp.rect(42, 12, 86, 116)
    sh = _hshade(sp, 42, 86, 0.3, 0.4)
    flutes = ((sp.x - 42) % 7) < 1.5
    sh = np.where(flutes, sh - 0.15, sh)
    sp.paint(shaft, sh + 0.08 * noise(128, 4, 361), OBSIDIAN)
    sp.paint(sp.rect(32, 0, 96, 12), _hshade(sp, 32, 96, 0.45), OBSIDIAN)
    sp.paint(sp.rect(32, 116, 96, 128), _hshade(sp, 32, 96, 0.45), OBSIDIAN)
    sp.paint(sp.rect(41, 56, 87, 59), _hshade(sp, 41, 87, 0.35, 0.3), GOLD)
    gl = (speckle(128, 0.01, 362) > 0.5) & shaft & (sp.x < 56)
    sp.solid(gl, "#c090ff")
    return sp.rgba()


def th_crowd():
    """Far demon silhouettes for the arena's tiers: a row of horned heads and raised arms, near-black with an ember rim."""
    sp = Sprite()
    rng = _rng(371)
    for k in range(7):
        cx = 10 + k * 18 + rng.uniform(-3, 3)
        top = 58 + rng.uniform(-8, 8)
        body = sp.ellipse(cx, top + 40, 11, 34) | sp.ellipse(cx, top + 6, 6, 7)
        horns = sp.line(cx - 4, top + 2, cx - 8, top - 8, 2.5) | sp.line(cx + 4, top + 2, cx + 8, top - 8, 2.5)
        arm = sp.line(cx + 8, top + 22, cx + 14 * (1 if k % 2 else -1), top - 14, 4) if k % 3 != 1 else np.zeros_like(body)
        m = body | horns | arm
        m &= sp.y < 127
        sp.paint(m, np.clip(0.25 + 0.2 * (sp.x < cx - 7), 0, 1), BASALT)
        rim = m & ~np.roll(m, 3, axis=1)
        sp.solid(rim & (sp.y < top + 60), "#d0501a")
        top_rim = m & ~np.roll(m, 2, axis=0)
        sp.solid(top_rim, "#ff8a30")
        sp.solid(sp.ellipse(cx - 2.5, top + 5, 1.2, 1.2) | sp.ellipse(cx + 2.5, top + 5, 1.2, 1.2), "#ffd060")  # eyes
    return sp.rgba()


PROPS = {
    "thing_brazier": th_brazier, "thing_chain": th_chain, "thing_skull": th_skull, "thing_anvil": th_anvil, "thing_tongs": th_tongs,
    "thing_throne": th_throne, "thing_booth": th_booth, "thing_rope": th_rope, "thing_furnace": th_furnace, "thing_column": th_column,
    "thing_crowd": th_crowd,
}


def write_props(out_dir: str) -> list:
    from PIL import Image
    os.makedirs(out_dir, exist_ok=True)
    for tid, fn in sorted(PROPS.items()):
        Image.fromarray(fn(), "RGBA").save(os.path.join(out_dir, tid + ".png"), optimize=False, compress_level=9)
    return sorted(PROPS)


def build() -> dict:
    write_props(os.path.join(lib.ROOT, "assets", "story", "underworld", "textures"))
    tiles = {
        "lava": lava(),
        "floor_obsidian": obsidian(),
        "wall_column": obsidian_wall(),
        "wall_arena": scorched_brick(),
        "wall_bone": bone_wall(),
        "floor_causeway": bone_bridge(),
        "wall_plate": iron_plates(),
        "floor_steel": tread_floor(),
        "ceil_pipes": rusty_pipes(),
        "wall_bars": cage_bars(),
        "floor_tier": stone_tiers(),
        "floor_carpet": carpet_runner(),
        "floor_checker": checker_floor(),
        "floor_basalt": basalt(),
        "wall_cave": cave_rock(),
        "ceil_court": court_ceiling(),
        "ceil_spikes": rock_ceiling(),
        "floor_dais": iron_dais(),
    }
    return tiles
