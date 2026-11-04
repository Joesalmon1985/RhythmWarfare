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
    "toilet_floor": 1.5, "cubicle_door": 2.0, "wall_door": 3.0, "thing_sign_wc": 1.0,
    # billboard props drawn by tex_night_one.py (RGBA, written by its build()); its opaque tiles set their own metres
    "thing_decks": 1.0, "thing_pendant": 1.0, "thing_bulb": 1.0, "thing_sink": 1.0, "thing_dryer": 1.0, "thing_tube": 1.0,
    "thing_toilet": 1.0, "thing_firedoor": 1.0, "thing_exit_sign": 1.0, "thing_sofa": 1.0, "thing_lavalamp": 1.0, "thing_bulbs": 1.0,
    "thing_truss_tower": 1.0, "thing_bin": 1.0, "thing_rail": 1.0,
    "thing_wizard": 1.0, "thing_headphones": 1.0, "thing_crack": 1.0,
}


MOTHERSHIP = {
    "wall_hull": 2.0, "wall_planet": 10.0, "wall_led": 3.0, "wall_speaker": 2.0, "wall_door": 3.0, "wall_shelf": 2.0, "floor_hex": 2.5, "floor_dais": 2.0,
    "ceil_hull": 2.5, "trim": 2.0, "wall_gold": 3.0, "floor_lounge": 3.0, "wall_arch": 3.0, "wall_sofa": 3.0, "wall_tube": 2.0, "floor_grate": 3.0,
    "ceil_hazard": 2.0, "thing_core": 1.0, "wall_console": 3.0, "floor_bridge": 3.0, "wall_window": 12.0, "med_tile": 1.5, "med_floor": 1.5, "wall_hatch": 3.0,
    "sky_space": 1.0, "med_ceil": 2.0, "wall_airlock": 3.2, "floor_airlock": 2.0,
    # billboard props drawn by tools/story/art/tex_mothership.py (RGBA, written there)
    "thing_planet": 1.0, "thing_tube": 1.0, "thing_tube2": 1.0, "thing_probe_arm": 1.0, "thing_exam_table": 1.0, "thing_monitor": 1.0, "thing_cabinet": 1.0,
    "thing_screen": 1.0, "thing_bunk": 1.0, "thing_surglamp": 1.0, "thing_pipes": 1.0, "thing_cables": 1.0, "thing_console": 1.0, "thing_captain": 1.0,
    "thing_suit": 1.0, "thing_wheel": 1.0, "thing_warn": 1.0, "thing_plant": 1.0, "thing_bar": 1.0,
}

MENTAL_HOSPITAL = {
    "wall_mint": 2.0, "wall_dado": 2.0, "wall_led": 3.0, "wall_door": 3.0, "wall_speaker": 2.0, "wall_window": 3.0, "floor_check": 2.5, "ceil_tile": 2.5,
    "floor_dais": 2.0, "wall_cdoor": 3.0, "wall_cdoor2": 3.0, "floor_wood": 3.0, "ceil_pale": 2.5, "wall_end": 3.0, "wall_art": 3.0, "wall_awindow": 4.0,
    "floor_art": 3.0, "wall_brick": 2.5, "wall_archdoor": 3.0, "floor_paving": 3.0, "tx_tile": 1.5, "tx_floor": 1.5, "pad_tile": 1.5, "sky_moon": 1.0,
    "thing_lamp": 1.0, "thing_table": 1.0, "thing_bed": 1.0, "thing_easel": 1.0, "thing_chair": 1.0,
    # tex_mental_hospital.py: the procedural tiles it adds, and the RGBA props it writes itself
    "wall_office": 2.7, "wall_dwindow": 1.8, "wall_slit": 0.9,
    "thing_chair_b": 1.0, "thing_chair_c": 1.0, "thing_easel_b": 1.0, "thing_jars": 1.0, "thing_phone": 1.0, "thing_radiator": 1.0,
    "thing_fan": 1.0, "thing_clock": 1.0, "thing_cagelamp": 1.0, "thing_tube": 1.0, "thing_cabinet": 1.0, "thing_trolley": 1.0,
    "thing_sink": 1.0, "thing_wheelchair": 1.0,
}

UNDERWORLD = {
    "wall_arena": 2.5, "wall_speaker": 2.0, "wall_hellmouth": 3.0, "wall_bone": 1.5, "wall_shelf": 2.0, "floor_checker": 2.5, "floor_dais": 2.0,
    "ceil_spikes": 2.5, "trim": 2.0, "wall_court": 3.0, "wall_column": 2.0, "wall_throne": 4.0, "floor_obsidian": 2.5, "floor_carpet": 3.0,
    "ceil_court": 2.5, "floor_causeway": 2.5, "lava": 3.0, "wall_cave": 3.0, "wall_fortress": 4.0, "wall_plate": 2.5, "wall_face": 4.0,
    "floor_orange": 3.0, "floor_steel": 2.5, "ceil_pipes": 2.5, "wall_bars": 1.5, "sky_hell": 1.0, "thing_column": 1.0, "thing_anvil": 1.0,
    # props drawn by tex_underworld.py (RGBA, written next to the baked tiles)
    "thing_brazier": 1.0, "thing_chain": 1.0, "thing_skull": 1.0, "thing_tongs": 1.0, "thing_throne": 1.0, "thing_booth": 1.0, "thing_rope": 1.0,
    "thing_furnace": 1.0, "thing_crowd": 1.0,
}

HOSPITAL = {
    "wall_ward": 2.5, "wall_window": 4.0, "floor_wood": 2.5, "trim": 2.0, "wall_curtain": 1.5, "wall_door": 3.0, "floor_check": 2.5, "ceil_tile": 2.5,
    "wall_station": 3.0, "wall_counter": 2.0, "wall_vending": 4.8, "floor_cafe": 3.0, "wall_brick": 4.0, "wall_hedge": 3.0, "floor_stone": 3.0,
    "wall_quiet": 2.0, "floor_lino": 2.0, "wall_tv": 3.0, "sky_night": 1.0, "thing_chair": 1.0, "thing_bench": 1.0,
    # drawn by art/tex_hospital.py (the surfaces' metres come from its build(); the RGBA billboards are written there and listed here)
    "thing_monitor": 1.0, "thing_bed": 1.0, "thing_drip": 1.0, "thing_desk": 1.0, "thing_clock": 1.0, "thing_exit": 1.0, "thing_nightlight": 1.0,
    "thing_tree": 1.0, "thing_lamppost": 1.0, "thing_door_lit": 1.0, "thing_plant": 1.0, "thing_mic": 1.0,
}

SPECS = {"night_one": NIGHT_ONE, "mothership": MOTHERSHIP, "underworld": UNDERWORLD, "hospital": HOSPITAL, "mental_hospital": MENTAL_HOSPITAL}


def godot_binary() -> str:
    for cand in (os.environ.get("GODOT"), os.path.expanduser("~/godot/Godot_v4.5.1-stable_linux.x86_64"), shutil.which("godot")):
        if cand and os.path.exists(cand):
            return cand
    raise SystemExit("tiles: no Godot binary found (set GODOT=/path/to/godot)")


def _png_size(path: str):
    with open(path, "rb") as fh:
        head = fh.read(24)
    return struct.unpack(">II", head[16:24])


def procedural(chapter: str, out_dir: str) -> dict:
    """The chapter's procedural pixel textures (tools/story/art/tex_<chapter>.py, built on pixeltex.py), written after the Godot bake: a tile with a baked id
    replaces it, a new id is added. Returns {id: metres}."""
    import importlib
    try:
        mod = importlib.import_module(f"art.tex_{chapter}")
    except ModuleNotFoundError:
        return {}
    from . import pixeltex
    out = {}
    for tid, (rgb, metres) in sorted(mod.build().items()):
        pixeltex.save(os.path.join(out_dir, tid + ".png"), rgb)
        out[tid] = metres
    return out


def build(chapter: str, spec: dict | None = None) -> dict:
    """Bake the chapter's tiles with Godot and return the manifest `textures` section."""
    spec = spec or SPECS[chapter]
    r = subprocess.run([godot_binary(), "--headless", "--path", lib.ROOT, "-s", "tools/story/bake_tiles.gd", "--", chapter],
                       capture_output=True, text=True)
    if r.returncode != 0 or "ERROR" in r.stdout + r.stderr:
        raise SystemExit("tiles: bake_tiles.gd failed\n" + r.stdout + r.stderr)
    out_dir = os.path.join(lib.ROOT, "assets", "story", chapter, "textures")
    spec = dict(spec)
    spec.update(procedural(chapter, out_dir))
    section = {}
    for tid in sorted(spec):
        p = os.path.join(out_dir, tid + ".png")
        if not os.path.exists(p):
            raise SystemExit(f"tiles: bake_tiles.gd did not write {tid}.png")
        w, h = _png_size(p)
        section[tid] = {"file": f"textures/{tid}.png", "size": [w, h], "metres": spec[tid]}
    return section
