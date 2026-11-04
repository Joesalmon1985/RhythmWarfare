"""Texture tiles for the 2.5D world (StoryWorld): 64 or 128 px PNGs cropped out of the chapter's own SVG art.

The rasterising is done by Godot (`tools/story/bake_tiles.gd`, run headless: Image.load_svg_from_string, crop, resample), because the Python toolchain
has no SVG rasteriser; the recipes (which region of which SVG becomes which tile) live in that script. This module only holds the metres-per-repeat of each tile,
runs the bake and returns the manifest `textures` section {id: {file, size, metres}}. Same SVGs in, same bytes out (checked by check_assets.py --determinism).
Needs a Godot 4 binary: $GODOT, else ~/godot/Godot_v4.5.1-stable_linux.x86_64, else `godot` on the PATH.
"""
from __future__ import annotations

import os
import shutil
import struct
import subprocess

from . import lib

# id -> metres of the world one repeat of the tile covers
NIGHT_ONE = {
    "wall_brick": 2.0, "wall_panel": 2.0, "wall_led": 3.0, "wall_speaker": 2.0, "trim": 2.0, "floor_led": 2.0, "floor_dark": 2.0,
    "floor_stage": 2.0, "ceil_truss": 2.0, "floor_carpet": 2.0, "wall_bar": 2.0, "bar_front": 1.0, "toilet_tile": 1.5,
    "toilet_floor": 1.5, "cubicle_door": 2.0, "wall_door": 3.0,
}


MOTHERSHIP = {
    "wall_hull": 2.0, "wall_planet": 10.0, "wall_led": 3.0, "wall_speaker": 2.0, "wall_door": 3.0, "wall_shelf": 2.0, "floor_hex": 2.5, "floor_dais": 2.0,
    "ceil_hull": 2.5, "trim": 2.0, "wall_gold": 3.0, "floor_lounge": 3.0, "wall_arch": 3.0, "wall_sofa": 3.0, "wall_tube": 2.0, "floor_grate": 3.0,
    "ceil_hazard": 2.0, "thing_core": 1.0, "wall_console": 3.0, "floor_bridge": 3.0, "wall_window": 12.0, "med_tile": 1.5, "med_floor": 1.5, "wall_hatch": 3.0,
    "sky_space": 1.0,
}

SPECS = {"night_one": NIGHT_ONE, "mothership": MOTHERSHIP}


def godot_binary() -> str:
    for cand in (os.environ.get("GODOT"), os.path.expanduser("~/godot/Godot_v4.5.1-stable_linux.x86_64"), shutil.which("godot")):
        if cand and os.path.exists(cand):
            return cand
    raise SystemExit("tiles: no Godot binary found (set GODOT=/path/to/godot)")


def _png_size(path: str):
    with open(path, "rb") as fh:
        head = fh.read(24)
    return struct.unpack(">II", head[16:24])


def build(chapter: str, spec: dict | None = None) -> dict:
    """Bake the chapter's tiles with Godot and return the manifest `textures` section."""
    spec = spec or SPECS[chapter]
    r = subprocess.run([godot_binary(), "--headless", "--path", lib.ROOT, "-s", "tools/story/bake_tiles.gd", "--", chapter],
                       capture_output=True, text=True)
    if r.returncode != 0 or "ERROR" in r.stdout + r.stderr:
        raise SystemExit("tiles: bake_tiles.gd failed\n" + r.stdout + r.stderr)
    out_dir = os.path.join(lib.ROOT, "assets", "story", chapter, "textures")
    section = {}
    for tid in sorted(spec):
        p = os.path.join(out_dir, tid + ".png")
        if not os.path.exists(p):
            raise SystemExit(f"tiles: bake_tiles.gd did not write {tid}.png")
        w, h = _png_size(p)
        section[tid] = {"file": f"textures/{tid}.png", "size": [w, h], "metres": spec[tid]}
    return section
