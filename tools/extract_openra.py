#!/usr/bin/env python3
"""Extract Red Alert art and OpenRA sequence definitions for the rhythm-RTS.

Reads the pinned OpenRA checkout (engine + ``mods/ra``), drives
``OpenRA.Utility.exe`` to render the owner's own Red Alert content with the
``temperat`` palette, converts every frame to RGBA and resolves the MiniYaml
sequence semantics of ``OpenRA.Mods.Common.Graphics.DefaultSpriteSequence``
(plus the Cnc ``ClassicSpriteSequence`` / ``TilesetSpecificSpriteSequence``
subclasses the RA mod uses) into ``assets/openra/sequences.json``.

It also builds ``data/maps/strip_53x20.json`` (a 53x20 temperate strip with
tree clumps) and renders ``docs/shots/map_preview.png``.

Only numpy and Pillow are required.  Nothing is ever written into the OpenRA
checkout: the utility is run inside a scratch work directory.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
from PIL import Image

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

DEFAULT_ENGINE = Path(
    r"C:\Users\joesa\Documents\Cursor\DuelMaster\DuelMasterBattle\WizardRTSHybrid\external\openra"
)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = PROJECT_ROOT / "assets" / "openra"
DEFAULT_MAP = PROJECT_ROOT / "data" / "maps" / "strip_53x20.json"
DEFAULT_PREVIEW = PROJECT_ROOT / "docs" / "shots" / "map_preview.png"
DEFAULT_WORK = Path(tempfile.gettempdir()) / "openra_extract_work"

MOD = "ra"
TILESET = "TEMPERAT"
PALETTE_FILE = "temperat.pal"
TRANSPARENT_INDEX = 0
SHADOW_INDEX = 4
SHADOW_ALPHA = 140
REMAP_INDICES = range(80, 96)  # the player-colour ramp (PlayerColorRemap); marked with alpha 253 for the faction shader
REMAP_ALPHA = 253
CELL = 24  # RA cell size in pixels

# image name -> (sequence yaml file, sequence names or None for "all but icons")
NEEDED: dict[str, tuple[str, list[str] | None]] = {
    # infantry
    "e1": ("infantry.yaml", None),
    "e2": ("infantry.yaml", None),
    "e3": ("infantry.yaml", None),
    "e4": ("infantry.yaml", None),
    # vehicles (+ the husk images that reuse the same shp)
    "1tnk": ("vehicles.yaml", None),
    "2tnk": ("vehicles.yaml", None),
    "3tnk": ("vehicles.yaml", None),
    "2tnk.destroyed": ("vehicles.yaml", None),
    "3tnk.destroyed": ("vehicles.yaml", None),
    "4tnk": ("vehicles.yaml", None),
    "4tnk.destroyed": ("vehicles.yaml", None),
    "jeep": ("vehicles.yaml", None),
    "apc": ("vehicles.yaml", None),
    "arty": ("vehicles.yaml", None),
    "v2rl": ("vehicles.yaml", None),
    "ftrk": ("vehicles.yaml", None),
    # aircraft
    "heli": ("aircraft.yaml", None),
    # structures
    "hpad": ("structures.yaml", None),
    "powr": ("structures.yaml", None),
    "fact": ("structures.yaml", None),
    "weap": ("structures.yaml", None),
    "barr": ("structures.yaml", None),
    "brik": ("structures.yaml", None),
    "sbag": ("structures.yaml", None),
    "gun": ("structures.yaml", None),
    "agun": ("structures.yaml", None),
    "sam": ("structures.yaml", None),
    "ftur": ("structures.yaml", None),
    "pbox": ("structures.yaml", None),
    "dome": ("structures.yaml", None),
    "fix": ("structures.yaml", None),
    # projectiles
    "120mm": ("misc.yaml", None),
    "50cal": ("misc.yaml", None),
    "dragon": ("misc.yaml", None),
    "missile": ("misc.yaml", None),
    "fb1": ("misc.yaml", None),
    "fb2": ("misc.yaml", None),
    "fb3": ("misc.yaml", None),
    "fb4": ("misc.yaml", None),
    "bomb": ("misc.yaml", None),
    "v2": ("misc.yaml", None),
    # impacts / explosions (water splashes and the nuke are left out)
    "explosion": (
        "misc.yaml",
        [
            "piff", "piffs", "small_explosion", "med_explosion",
            "flak_explosion_ground", "small_explosion_air", "med_explosion_air",
            "napalm", "building_napalm", "self_destruct", "artillery_explosion",
            "building", "large_explosion", "small_napalm", "offset_napalm",
            "large_napalm", "corpse",
        ],
    ),
    # smoke and fire
    "smoke_m": ("misc.yaml", None),
    "smokey": ("misc.yaml", None),
    "fire": ("misc.yaml", None),
    "burn-s": ("misc.yaml", None),
    "burn-m": ("misc.yaml", None),
    "burn-l": ("misc.yaml", None),
    "scorch_flames": ("misc.yaml", None),
    # smudges left by warheads
    "craters": ("misc.yaml", None),
    "scorches": ("misc.yaml", None),
    # repair decoration (WithBuildingRepairDecoration: Image allyrepair, Sequence repair)
    "allyrepair": ("misc.yaml", None),
    # trees (temperate) and their husks
    **{t: ("decorations.yaml", None) for t in
       ["t01", "t02", "t03", "t04", "t05", "t06", "t07", "t08",
        "tc01", "tc02", "tc03", "tc04", "tc05"]},
    **{t + ".husk": ("decorations.yaml", None) for t in
       ["t01", "t02", "t03", "t04", "t05", "t06", "t07", "t08",
        "tc01", "tc02", "tc03", "tc04", "tc05"]},
}
EXCLUDED_SEQUENCES = {"icon", "fake-icon"}

# Files that no sequence references but that the renderer needs anyway
# (terrain templates and the unused 4-wide bib for completeness).
EXTRA_FILES: list[str] = [
    "clear1.tem",   # the 16-variant clear ground tile (temperat.yaml Template 255/65535)
    "b1.tem", "b2.tem", "b3.tem",  # boulders (temperat.yaml Debris, Tiles: Rock)
    "p01.tem", "p02.tem",          # ground patches (temperat.yaml Debris)
    "bib1.tem",                    # 4-wide bib (not used by the actors here)
]

# Old composited / layered files that sequences.json makes obsolete.
OBSOLETE_PATTERNS: list[str] = [
    "1tnk-body-*", "1tnk-turret-*", "2tnk-body-*", "2tnk-turret-*",
    "3tnk-body-*", "3tnk-turret-*", "*-b-idle-*", "*-b-damaged-*",
    "*-b-make-*", "*-b-active-*", "*-b-damaged_active-*", "*-b-turret-*",
    "weap-top-*",
]

# Tree footprints from mods/ra/rules/decoration.yaml (Building: Footprint / Dimensions).
# 'x' = occupied cell, '_' = free cell under the sprite.
TREE_FOOTPRINTS: dict[str, tuple[int, int, str]] = {
    "t01": (2, 2, "__ x_"), "t02": (2, 2, "__ x_"), "t03": (2, 2, "__ x_"),
    "t04": (2, 2, "__ x_"), "t05": (2, 2, "__ x_"), "t06": (2, 2, "__ x_"),
    "t07": (2, 2, "__ x_"), "t08": (2, 1, "x_"),
    "tc01": (3, 2, "___ xx_"), "tc02": (3, 2, "_x_ xx_"), "tc03": (3, 2, "xx_ xx_"),
    "tc04": (4, 3, "____ xxx_ x___"), "tc05": (4, 3, "__x_ xxx_ _xx_"),
}
# t04 is desert-only (MapEditorData ExcludeTilesets: TEMPERAT); keep it off the map.
MAP_TREE_CHOICES = ["tc01", "tc02", "tc03", "tc04", "tc05",
                    "t01", "t02", "t03", "t05", "t06", "t07", "t08"]

# Base footprints on the left side: (x, y, w, h).  Mirrored for the right side.
BASE_FOOTPRINTS_LEFT: list[tuple[int, int, int, int]] = [
    (0, 4, 2, 2), (0, 6, 2, 2), (0, 8, 2, 2), (0, 10, 2, 2), (0, 12, 2, 2),  # pads
    (2, 1, 2, 2), (2, 16, 2, 2),  # power
    (3, 8, 3, 3),                 # main
    (7, 3, 3, 3),                 # factory
    (4, 6, 2, 1),                 # sam
    (7, 13, 2, 2),                # barracks
    *[(11, y, 1, 1) for y in range(0, 7)],    # walls
    *[(11, y, 1, 1) for y in range(13, 20)],
    (12, 5, 1, 1), (12, 14, 1, 1),            # turrets
]

FACING_NOTES = (
    "OpenRA facings are WAngle units: 1024 per full turn, 0 = north (screen up), increasing "
    "COUNTER-clockwise (WVec.Yaw = ArcTan(-Y, X) - 256, so west = 256, south = 512, east = 768; "
    "WAngle.FromFacing(f) = f * 4 for the classic 0..255 facing, FromDegrees(d) = d * 1024 / 360). "
    "For a sequence with Facings N (N a power of two <= 1024) the facing block is chosen by "
    "OpenRA.Mods.Common.Util.IndexFacing: step = 1024 // N; block = ((angle + step // 2) & 1023) // step. "
    "If the sequence has UseClassicFacings (RA 32-facing vehicle/turret art, ClassicSpriteSequence) "
    "the block comes from OpenRA.Mods.Cnc.Util.ClassicIndexFacing instead: with SpriteRanges = "
    "[20, 56, 88, 132, 156, 184, 212, 240, 268, 296, 324, 352, 384, 416, 452, 488, 532, 568, 604, 644, "
    "668, 696, 724, 752, 780, 808, 836, 864, 896, 928, 964, 1000] the block is the first i with "
    "angle < SpriteRanges[i], else 0 (so angles 1000..1023 and 0..19 use frame 0; frame 1 covers 20..55, "
    "frame 2 covers 56..87, ...). The actual facing drawn by classic block i is SpriteFacings[i] = "
    "[0, 40, 74, 112, 146, 172, 200, 228, 256, 284, 312, 340, 370, 402, 436, 472, 512, 552, 588, 626, 658, "
    "684, 712, 740, 768, 796, 824, 852, 882, 914, 948, 984]. A negative Facings in yaml means "
    "reverse_facings: block = (N - block) % N. With InterpolatedFacings M > N the closest block is drawn "
    "rotated by GetInterpolatedFacingRotation = (AngleDiffToStep(angle, N) // (1024 // M)) * (1024 // M) "
    "where AngleDiffToStep = ((angle + step/2) & 1023) % step - step/2 (none of the images here use it). "
    "Sprite index inside the sequence (DefaultSpriteSequence.GetSprite): index = block * length + "
    "(frame % length). That index addresses the 'frame_table' of each sequence, which this file has "
    "already resolved per DefaultSpriteSequence.CalculateFrameIndices: for block b and animation frame i, "
    "i_virtual = (i * facings + b) if transpose else (b * stride + i); sheet index = start + i_virtual, where the "
    "sheet is the file's frames, or the explicit Frames list when the yaml gives one (ResolveSprites expands "
    "Frames first, so source frame = Frames[start + i_virtual]; Length: * then means len(Frames) - start); "
    "stride defaults to length. "
    "Reverses appends the inner frames in reverse order (length becomes 2*length-2). If shadow_start >= 0 "
    "the shadow frame for a source frame f is f - start + shadow_start. For a plain sequence the "
    "frame_table ints are frame indices of 'file' (PNG '<file>-NNNN.png'); for a Combine sequence they "
    "index the 'combine' list, whose entries name the real file and frame."
)

FRAME_ADDRESSING_NOTES = (
    "Each sequence carries: file (shp/tem stem; PNG name is '<file>-<frame:04d>.png'), start, length, "
    "stride, facings, reverse_facings, tick (ms per frame), offset [x, y, z] in pixels added to the sprite "
    "position, z_offset (WDist units, 1024 per cell; higher draws on top), z_ramp, shadow_start, "
    "shadow_z_offset, flip_x, flip_y, transpose, reverses, classic_facings (UseClassicFacings), frames "
    "(explicit Frames list or null), scale, alpha, alpha_fade, blend_mode, ignore_world_tint, combine "
    "(virtual sheet for Combine sequences or null) and frame_table (list indexed [facing_block][frame])."
)

WALL_NOTES = (
    "brik/sbag idle, scratched-idle and damaged-idle have 16 frames with no facings: "
    "WithWallSpriteBody plays frame = adjacency bitmask where bit 1 = same wall type to the south "
    "(dy > 0), bit 2 = west (dx < 0), bit 4 = north (dy < 0), bit 8 = east (dx > 0)."
)

BIB_NOTES = (
    "WithBuildingBib draws the 'bib' sequence of the building image as a strip of tiles under the "
    "footprint: rows = 1 if HasMinibib else 2, width = Building.Dimensions.X, and bib frame i goes to cell "
    "(i % width, i // width + Dimensions.Y - rows) relative to the building's top-left cell. fact/weap use "
    "bib2 (3 wide), powr/barr/hpad use bib3 (2 wide), gun/agun/sam/ftur use their own 1-row mbXXX minibib. "
    "Building sprites are centred on the centre of the Dimensions rectangle plus LocalCenterOffset "
    "(BuildingInfo.CenterOffset)."
)


# --------------------------------------------------------------------------
# MiniYaml
# --------------------------------------------------------------------------

@dataclass
class Node:
    key: str
    value: str | None
    children: list["Node"] = field(default_factory=list)

    def child(self, key: str) -> "Node | None":
        for c in self.children:
            if c.key == key:
                return c
        return None


def _strip_comment(line: str) -> str:
    out: list[str] = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line) and line[i + 1] == "#":
            out.append("#")
            i += 2
            continue
        if ch == "#":
            break
        out.append(ch)
        i += 1
    return "".join(out)


def parse_miniyaml(text: str) -> list[Node]:
    """Parse OpenRA MiniYaml (tab indented 'Key: Value' trees)."""
    root = Node("", None)
    stack: list[tuple[int, Node]] = [(-1, root)]
    for raw in text.splitlines():
        line = _strip_comment(raw).rstrip()
        if not line.strip():
            continue
        depth = len(line) - len(line.lstrip("\t"))
        body = line.strip()
        if ":" in body:
            key, _, value = body.partition(":")
            key = key.strip()
            val: str | None = value.strip() or None
        else:
            key, val = body, None
        node = Node(key, val)
        while stack and stack[-1][0] >= depth:
            stack.pop()
        stack[-1][1].children.append(node)
        stack.append((depth, node))
    return root.children


# --------------------------------------------------------------------------
# Value parsers (FieldLoader equivalents)
# --------------------------------------------------------------------------

def parse_int(v: str) -> int:
    return int(v.strip())


def parse_bool(v: str) -> bool:
    return v.strip().lower() in ("true", "yes", "1")


def parse_float(v: str) -> float:
    return float(v.strip())


def parse_wdist(v: str) -> int:
    """WDist.TryParse: 'Nc' / 'NcM' / 'M'; sign propagates to the fractional part."""
    parts = re.split("[cC]", v.strip())
    if len(parts) == 2:
        cell, sub = int(parts[0]), int(parts[1])
    elif len(parts) == 1:
        cell, sub = 0, int(parts[0])
    else:
        raise ValueError(f"bad WDist {v!r}")
    if cell < 0:
        sub = -sub
    return 1024 * cell + sub


def parse_int_list(v: str) -> list[int]:
    return [int(x) for x in v.replace(" ", "").split(",") if x != ""]


def parse_float_list(v: str) -> list[float]:
    return [float(x) for x in v.replace(" ", "").split(",") if x != ""]


def parse_vec3(v: str) -> list[float]:
    parts = parse_float_list(v)
    if len(parts) == 2:
        parts.append(0.0)
    if len(parts) != 3:
        raise ValueError(f"bad Vector3 {v!r}")
    return parts


# --------------------------------------------------------------------------
# Sequence resolution (DefaultSpriteSequence semantics)
# --------------------------------------------------------------------------

@dataclass
class Reservation:
    """One SpriteReservation: a (sub)file plus the frames taken from it."""
    filename: str
    frames: list[int] | None  # explicit frame indices into the file, or None = all frames
    offset: list[float]
    flip_x: bool
    flip_y: bool
    scale: float


@dataclass
class ResolvedSequence:
    image: str
    name: str
    data: dict[str, Any]
    reservations: list[Reservation]
    is_combine: bool


def _field(data: Node, defaults: Node | None, key: str) -> Node | None:
    """DefaultSpriteSequence.LoadField: the sequence node first, then Defaults."""
    n = data.child(key)
    if n is None and defaults is not None:
        n = defaults.child(key)
    return n


def _field_value(data: Node, defaults: Node | None, key: str) -> str | None:
    n = _field(data, defaults, key)
    return None if n is None else n.value


def _tileset_filename(data: Node, defaults: Node | None, tileset: str) -> str | None:
    """TilesetSpecificSpriteSequence.ParseFilenames: TilesetFilenames[tileset] wins over Filename."""
    node = _field(data, defaults, "TilesetFilenames")
    if node is not None:
        t = node.child(tileset)
        if t is not None and t.value:
            return t.value
    return _field_value(data, defaults, "Filename")


def resolve_sequence(image: str, seq: Node, defaults: Node | None, tileset: str) -> ResolvedSequence:
    def val(key: str) -> str | None:
        return _field_value(seq, defaults, key)

    start = parse_int(val("Start") or "0")
    length_raw = val("Length")
    length: int | None = None if length_raw == "*" else parse_int(length_raw or "1")
    stride_raw = val("Stride")
    stride: int | None = parse_int(stride_raw) if stride_raw is not None else length
    facings = parse_int(val("Facings") or "1")
    interp_raw = val("InterpolatedFacings")
    interpolated = parse_int(interp_raw) if interp_raw is not None else None
    tick = parse_int(val("Tick") or "40")
    z_offset = parse_wdist(val("ZOffset") or "0")
    z_ramp = parse_int(val("ZRamp") or "0")
    shadow_start = parse_int(val("ShadowStart") or "-1")
    shadow_z_offset = parse_wdist(val("ShadowZOffset") or "-5")
    ignore_tint = parse_bool(val("IgnoreWorldTint") or "false")
    scale = parse_float(val("Scale") or "1")
    reverses = parse_bool(val("Reverses") or "false")
    transpose = parse_bool(val("Transpose") or "false")
    alpha_raw = val("Alpha")
    alpha = parse_float_list(alpha_raw) if alpha_raw else None
    alpha_fade = parse_bool(val("AlphaFade") or "false")
    frames_raw = val("Frames")
    frames = parse_int_list(frames_raw) if frames_raw else None
    flip_x = parse_bool(val("FlipX") or "false")
    flip_y = parse_bool(val("FlipY") or "false")
    offset = parse_vec3(val("Offset") or "0,0,0")
    blend = val("BlendMode") or "Alpha"
    classic = parse_bool(val("UseClassicFacings") or "false")

    reverse_facings = False
    if facings < 0:
        reverse_facings = True
        facings = -facings
    if facings == 0 or facings > 1024 or (facings & (facings - 1)) != 0:
        raise ValueError(f"{image}.{seq.key}: Facings must be a power of two in 1..1024")
    if length is not None and length <= 0:
        raise ValueError(f"{image}.{seq.key}: Length must be positive")
    if length is None and facings > 1:
        raise ValueError(f"{image}.{seq.key}: Facings cannot be used with Length: *")
    if classic and facings != 32:
        raise ValueError(f"{image}.{seq.key}: UseClassicFacings is only valid for 32 facings")

    reservations: list[Reservation] = []
    combine = seq.child("Combine")
    is_combine = combine is not None
    if combine is not None:
        for sub in combine.children:
            sub_frames_raw = sub.child("Frames")
            sub_frames = parse_int_list(sub_frames_raw.value) if sub_frames_raw and sub_frames_raw.value else None
            sub_len = sub.child("Length")
            if sub_frames is None and not (sub_len is not None and sub_len.value == "*"):
                s0 = parse_int(sub.child("Start").value) if sub.child("Start") else 0
                n = parse_int(sub_len.value) if sub_len and sub_len.value else 1
                sub_frames = [s0 + i for i in range(n)]
            sub_off = parse_vec3(sub.child("Offset").value) if sub.child("Offset") and sub.child("Offset").value else [0.0, 0.0, 0.0]
            sub_fx = parse_bool(sub.child("FlipX").value) if sub.child("FlipX") and sub.child("FlipX").value else False
            sub_fy = parse_bool(sub.child("FlipY").value) if sub.child("FlipY") and sub.child("FlipY").value else False
            # NOTE: DefaultSpriteSequence.ReserveSprites does not read Scale from Combine entries;
            # it is recorded here for information only.
            sub_scale = parse_float(sub.child("Scale").value) if sub.child("Scale") and sub.child("Scale").value else 1.0
            fname = _tileset_filename(sub, None, tileset)
            if not fname:
                raise ValueError(f"{image}.{seq.key}: Combine entry without Filename")
            reservations.append(Reservation(
                fname, sub_frames,
                [sub_off[i] + offset[i] for i in range(3)],
                sub_fx ^ flip_x, sub_fy ^ flip_y, sub_scale))
    else:
        fname = _tileset_filename(seq, defaults, tileset)
        if not fname:
            raise ValueError(f"{image}.{seq.key}: no Filename")
        reservations.append(Reservation(fname, None, offset, flip_x, flip_y, 1.0))

    data: dict[str, Any] = {
        "start": start, "length": length, "stride": stride, "facings": facings,
        "reverse_facings": reverse_facings, "interpolated_facings": interpolated,
        "tick": tick, "offset": offset, "z_offset": z_offset, "z_ramp": z_ramp,
        "shadow_start": shadow_start, "shadow_z_offset": shadow_z_offset,
        "flip_x": flip_x, "flip_y": flip_y, "transpose": transpose, "reverses": reverses,
        "classic_facings": classic, "frames": frames, "scale": scale, "alpha": alpha,
        "alpha_fade": alpha_fade, "blend_mode": blend, "ignore_world_tint": ignore_tint,
    }
    return ResolvedSequence(image, seq.key, data, reservations, is_combine)


def calculate_frame_indices(start: int, length: int, stride: int, facings: int,
                            frames: list[int] | None, transpose: bool,
                            reverse_facings: bool) -> list[int]:
    """DefaultSpriteSequence.CalculateFrameIndices (without the shadow block)."""
    used: list[int] = []
    for facing in range(facings):
        inner = (facings - facing) % facings if reverse_facings else facing
        for frame in range(length):
            i = frame * facings + inner if transpose else inner * stride + frame
            used.append(frames[i] if frames is not None else start + i)
    return used


def finalise_sequence(rs: ResolvedSequence, frame_counts: dict[str, int]) -> dict[str, Any]:
    """Resolve Length: * and build the frame_table against the (virtual) sprite sheet."""
    d = dict(rs.data)
    stems = [stem_of(r.filename) for r in rs.reservations]
    # virtual sheet: list of (stem, frame) in reservation order (ResolveSprites)
    sheet: list[tuple[str, int]] = []
    combine: list[dict[str, Any]] | None = [] if rs.is_combine else None
    for r in rs.reservations:
        stem = stem_of(r.filename)
        count = frame_counts.get(stem)
        if count is None:
            d["missing_file"] = r.filename
            d["file"] = stem if not rs.is_combine else None
            d["frame_table"] = None
            d["combine"] = None
            return d
        # ResolveSprites: an explicit Frames list *is* the sheet (resolved = Frames.Select(f => resolved[f]))
        seq_frames = d["frames"] if not rs.is_combine else None
        idx = r.frames if r.frames is not None else (seq_frames if seq_frames is not None else list(range(count)))
        for f in idx:
            if f >= count:
                raise ValueError(f"{rs.image}.{rs.name}: frame {f} out of range for {r.filename} ({count} frames)")
            sheet.append((stem, f))
            if combine is not None:
                combine.append({"file": stem, "frame": f, "offset": r.offset,
                                "flip_x": r.flip_x, "flip_y": r.flip_y, "scale": r.scale})

    start = d["start"]
    length = d["length"]
    if length is None:
        length = len(sheet) - start
    stride = d["stride"] if d["stride"] is not None else length
    # frames=None here: the sheet is already the Frames-expanded list (ResolveSprites passes `default`)
    index = calculate_frame_indices(start, length, stride, d["facings"], None,
                                    d["transpose"], d["reverse_facings"])
    if d["reverses"]:
        index = index + list(reversed(index[1:length - 1]))
        length = 2 * length - 2
    if not index:
        raise ValueError(f"{rs.image}.{rs.name} does not define any frames")
    if min(index) < 0 or max(index) >= len(sheet):
        raise ValueError(f"{rs.image}.{rs.name} uses frames {min(index)}..{max(index)} but only 0..{len(sheet) - 1} exist")
    facings = d["facings"]
    d["length"] = length
    d["stride"] = stride
    if rs.is_combine:
        d["file"] = None
        d["combine"] = combine
        table = [[index[b * length + i] for i in range(length)] for b in range(facings)]
    else:
        d["file"] = stems[0]
        d["combine"] = None
        table = [[sheet[index[b * length + i]][1] for i in range(length)] for b in range(facings)]
    d["frame_table"] = table
    if d["shadow_start"] >= 0:
        d["shadow_table"] = [[f - start + d["shadow_start"] for f in row] for row in table]
    else:
        d["shadow_table"] = None
    d["source_filename"] = rs.reservations[0].filename if not rs.is_combine else None
    return d


def stem_of(filename: str) -> str:
    """Utility output prefix: the file name without its extension (and any 'lores|' package prefix)."""
    name = filename.split("|")[-1]
    return Path(name).stem


# --------------------------------------------------------------------------
# Utility driver
# --------------------------------------------------------------------------

@dataclass
class ExtractResult:
    filename: str
    stem: str
    frames: int | None
    error: str | None


class Extractor:
    def __init__(self, engine: Path, work: Path) -> None:
        self.engine = engine
        self.work = work
        self.utility = engine / "bin" / "OpenRA.Utility.exe"
        if not self.utility.exists():
            raise SystemExit(f"utility not found: {self.utility}")
        work.mkdir(parents=True, exist_ok=True)
        self.env = dict(os.environ)
        self.env["ENGINE_DIR"] = str(engine)
        self.env["MOD_SEARCH_PATHS"] = str(engine / "mods")
        self.commands: list[str] = []

    def run(self, *args: str) -> subprocess.CompletedProcess[str]:
        cmd = [str(self.utility), MOD, *args]
        self.commands.append(" ".join(cmd[1:]))
        return subprocess.run(cmd, cwd=self.work, env=self.env, capture_output=True, text=True)

    def extract_palette(self) -> Path:
        out = self.work / PALETTE_FILE
        if not out.exists():
            r = self.run("--extract", PALETTE_FILE)
            if r.returncode != 0 or not out.exists():
                raise SystemExit(f"palette extraction failed:\n{r.stdout}\n{r.stderr}")
        return out

    def extract(self, filename: str, force: bool = False) -> ExtractResult:
        stem = stem_of(filename)
        raw = self.work / Path(filename.split("|")[-1]).name
        if force or not raw.exists():
            for old in self.work.glob(f"{stem}-[0-9][0-9][0-9][0-9].png"):
                old.unlink()
            r = self.run("--extract", filename)
            if r.returncode != 0 or not raw.exists():
                msg = (r.stdout + r.stderr).strip().splitlines()
                return ExtractResult(filename, stem, None, msg[-1] if msg else "extract failed")
        pngs = sorted(self.work.glob(f"{stem}-[0-9][0-9][0-9][0-9].png"))
        if force or not pngs:
            r = self.run("--png", raw.name, PALETTE_FILE)
            m = re.search(r"Saved .*-\[0\.\.(\d+)\]\.png", r.stdout)
            if r.returncode != 0 or not m:
                msg = (r.stdout + r.stderr).strip().splitlines()
                return ExtractResult(filename, stem, None, msg[-1] if msg else "png conversion failed")
            count = int(m.group(1)) + 1
            (self.work / f"{stem}.count").write_text(str(count))
        else:
            cfile = self.work / f"{stem}.count"
            count = int(cfile.read_text()) if cfile.exists() else len(pngs)
        return ExtractResult(filename, stem, count, None)


# --------------------------------------------------------------------------
# Palette / PNG conversion
# --------------------------------------------------------------------------

def load_palette(pal_path: Path) -> np.ndarray:
    """temperat.pal (256 x 6-bit RGB) -> (256, 4) uint8 RGBA, as ImmutablePalette does it."""
    raw = np.frombuffer(pal_path.read_bytes(), dtype=np.uint8)
    if raw.size != 768:
        raise SystemExit(f"unexpected palette size {raw.size}")
    six = raw.reshape(256, 3).astype(np.uint16)
    eight = ((six << 2) | (six >> 4)).astype(np.uint8)  # replicate high bits into low bits
    rgba = np.concatenate([eight, np.full((256, 1), 255, dtype=np.uint8)], axis=1)
    rgba[TRANSPARENT_INDEX] = (0, 0, 0, 0)
    rgba[SHADOW_INDEX] = (0, 0, 0, SHADOW_ALPHA)
    for i in REMAP_INDICES:
        rgba[i, 3] = REMAP_ALPHA  # src/ui/faction_remap.gdshader keys the player colour on this alpha
    return rgba


def convert_frame(src: Path, dst: Path, lut: np.ndarray) -> tuple[int, int]:
    im = Image.open(src)
    if im.mode != "P":
        raise SystemExit(f"{src}: expected an indexed PNG, got {im.mode}")
    idx = np.asarray(im, dtype=np.uint8)
    rgba = lut[idx]
    Image.fromarray(rgba, "RGBA").save(dst, optimize=True)
    return im.size


# --------------------------------------------------------------------------
# Map
# --------------------------------------------------------------------------

def mirror_footprints(width: int) -> list[tuple[int, int, int, int]]:
    out = list(BASE_FOOTPRINTS_LEFT)
    for x, y, w, h in BASE_FOOTPRINTS_LEFT:
        out.append((width - x - w, y, w, h))
    return out


def rects_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int], margin: int = 0) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax + aw + margin <= bx or bx + bw + margin <= ax or
                ay + ah + margin <= by or by + bh + margin <= ay)


def footprint_cells(name: str, x: int, y: int) -> list[list[int]]:
    w, h, pattern = TREE_FOOTPRINTS[name]
    rows = pattern.split()
    assert len(rows) == h and all(len(r) == w for r in rows), name
    return [[x + cx, y + cy] for cy, row in enumerate(rows) for cx, ch in enumerate(row) if ch == "x"]


def build_strip_map(width: int, height: int, clear_frames: int, available: set[str],
                    seed: int = 5320) -> dict[str, Any]:
    rng = random.Random(seed)
    tiles = [[{"t": "clear1", "f": rng.randrange(clear_frames)} for _ in range(width)] for _ in range(height)]
    bases = mirror_footprints(width)
    choices = [t for t in MAP_TREE_CHOICES if t in available]
    clumps = [c for c in choices if c.startswith("tc")]
    singles = [c for c in choices if not c.startswith("tc")]
    wanted = 7
    placed: list[tuple[str, int, int, int, int]] = []
    tries = 0
    while len(placed) < wanted and tries < 5000:
        tries += 1
        pool = clumps if (len(placed) % 2 == 0 and clumps) else (singles or clumps)
        name = rng.choice(pool)
        w, h, _ = TREE_FOOTPRINTS[name]
        x = rng.randint(14, 38 - w + 1)
        if rng.random() < 0.5:
            y = rng.randint(0, 6 - h + 1)        # top zone: rows 0..6
        else:
            y = rng.randint(13, height - h)      # bottom zone: rows 13..19
        rect = (x, y, w, h)
        if any(cy in range(7, 13) for cy in range(y, y + h)):
            continue
        if any(rects_overlap(rect, b) for b in bases):
            continue
        if any(rects_overlap(rect, p[1:], margin=1) for p in placed):
            continue
        placed.append((name, x, y, w, h))
    decorations = [{"image": n, "sequence": "idle", "x": x, "y": y, "w": w, "h": h}
                   for n, x, y, w, h in placed]
    blocked: list[list[int]] = []
    for n, x, y, _, _ in placed:
        blocked.extend(footprint_cells(n, x, y))
    return {
        "width": width, "height": height, "tileset": "temperat", "cell_px": CELL,
        "seed": seed, "tiles": tiles, "decorations": decorations, "blocked": blocked,
        "notes": ("Tiles are clear1.tem frames (16 variants, PickAny). A decoration's sprite is centred on the "
                  "centre of its w x h cell rectangle (OpenRA BuildingInfo.CenterOffset); 'blocked' are the 'x' "
                  "cells of the tree actor's Building footprint in mods/ra/rules/decoration.yaml."),
    }


def render_preview(map_data: dict[str, Any], assets: Path, sequences: dict[str, Any], out: Path) -> None:
    w, h = map_data["width"], map_data["height"]
    canvas = Image.new("RGBA", (w * CELL, h * CELL), (0, 0, 0, 255))
    tile_cache: dict[tuple[str, int], Image.Image] = {}
    for y, row in enumerate(map_data["tiles"]):
        for x, t in enumerate(row):
            key = (t["t"], t["f"])
            if key not in tile_cache:
                tile_cache[key] = Image.open(assets / f"{t['t']}-{t['f']:04d}.png").convert("RGBA")
            canvas.alpha_composite(tile_cache[key], (x * CELL, y * CELL))
    for d in map_data["decorations"]:
        seq = sequences["images"][d["image"]]["sequences"][d.get("sequence", "idle")]
        frame = seq["frame_table"][0][0]
        sprite = Image.open(assets / f"{seq['file']}-{frame:04d}.png").convert("RGBA")
        cx = (d["x"] + d["w"] / 2) * CELL + seq["offset"][0]
        cy = (d["y"] + d["h"] / 2) * CELL + seq["offset"][1]
        px = int(round(cx - sprite.width / 2))
        py = int(round(cy - sprite.height / 2))
        canvas.alpha_composite(sprite, (px, py))
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------

PROV_BEGIN = "<!-- extract_openra.py:begin -->"
PROV_END = "<!-- extract_openra.py:end -->"


def git_commit(engine: Path) -> str:
    head = engine / ".git" / "HEAD"
    try:
        ref = head.read_text().strip()
        if ref.startswith("ref:"):
            return (engine / ".git" / ref[4:].strip()).read_text().strip()
        return ref
    except OSError:
        return "unknown"


def content_packages(engine: Path) -> list[str]:
    text = (engine / "mods" / MOD / "mod.yaml").read_text(encoding="utf-8")
    return [ln.strip() for ln in text.splitlines() if ".mix" in ln and "content|" in ln]


def write_provenance(prov: Path, engine: Path, results: list[ExtractResult], out: Path,
                     png_count: int, total_bytes: int, commands: list[str]) -> None:
    commit = git_commit(engine)
    ok = [r for r in results if r.error is None]
    bad = [r for r in results if r.error is not None]
    lines = [PROV_BEGIN, "", "## Frames and sequences generated by `tools/extract_openra.py`", "",
             f"- OpenRA engine checkout: `{engine}` @ `{commit}` (GPL-3.0-or-later).",
             f"- Content: the owner's own Red Alert packages in `%APPDATA%\\OpenRA\\Content\\ra\\v2` "
             f"(the mod's content search order from `mods/ra/mod.yaml`: {', '.join(p.split('|')[-1].split(':')[0] for p in content_packages(engine))}). "
             "The utility does not report which package a file came from; shp/tem art is in conquer.mix / hires.mix / temperat.mix / expand.",
             f"- Palette: `{PALETTE_FILE}` converted like `ImmutablePalette` ((v << 2) | (v >> 4)); "
             f"index {TRANSPARENT_INDEX} fully transparent, index {SHADOW_INDEX} (RA `ShadowIndex`) black with alpha {SHADOW_ALPHA}, "
             f"indices {REMAP_INDICES.start}..{REMAP_INDICES.stop - 1} (the player-colour ramp) with alpha {REMAP_ALPHA} so the faction shader can recolour them.",
             "- Commands (run with `ENGINE_DIR` and `MOD_SEARCH_PATHS` pointing at the checkout, cwd = scratch dir):",
             "  `OpenRA.Utility.exe ra --extract <file>` then `OpenRA.Utility.exe ra --png <file> temperat.pal`; "
             "the indexed PNGs are then converted to RGBA by the script.",
             f"- Output: {png_count} RGBA PNG frames ({total_bytes / 1024:.0f} KiB) in `{out.relative_to(PROJECT_ROOT).as_posix()}`, "
             "named `<file stem>-<frame index>.png`, plus `sequences.json` resolved from `mods/ra/sequences/*.yaml`.",
             "", "### Files extracted", ""]
    for r in sorted(ok, key=lambda r: r.stem.lower()):
        lines.append(f"- `{r.filename}` -> `{r.stem}-0000..{r.frames - 1:04d}.png` ({r.frames} frames)")
    if bad:
        lines += ["", "### Files that could not be extracted", ""]
        for r in bad:
            lines.append(f"- `{r.filename}`: {r.error}")
    lines += ["", PROV_END, ""]
    block = "\n".join(lines)
    existing = prov.read_text(encoding="utf-8") if prov.exists() else ""
    if PROV_BEGIN in existing and PROV_END in existing:
        pre = existing[: existing.index(PROV_BEGIN)]
        post = existing[existing.index(PROV_END) + len(PROV_END):]
        new = pre + block + post.lstrip("\n")
    else:
        new = existing.rstrip("\n") + "\n\n" + block
    prov.write_text(new, encoding="utf-8")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def load_sequence_images(engine: Path) -> dict[str, tuple[Node, str]]:
    """image name -> (node, yaml file) for every image in mods/ra/sequences/*.yaml."""
    out: dict[str, tuple[Node, str]] = {}
    seq_dir = engine / "mods" / MOD / "sequences"
    for yaml in sorted(seq_dir.glob("*.yaml")):
        for node in parse_miniyaml(yaml.read_text(encoding="utf-8")):
            out[node.key] = (node, yaml.name)
    return out


def delete_obsolete(out: Path) -> list[str]:
    removed: list[str] = []
    for pattern in OBSOLETE_PATTERNS:
        for p in list(out.glob(pattern + ".png")) + list(out.glob(pattern + ".png.import")):
            p.unlink()
            removed.append(p.name)
    return removed


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engine", type=Path, default=DEFAULT_ENGINE, help="pinned OpenRA checkout")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory for PNG frames and sequences.json")
    ap.add_argument("--work", type=Path, default=DEFAULT_WORK, help="scratch directory the utility writes into")
    ap.add_argument("--map", type=Path, default=DEFAULT_MAP, help="strip map json to write")
    ap.add_argument("--preview", type=Path, default=DEFAULT_PREVIEW, help="map preview png to write")
    ap.add_argument("--force", action="store_true", help="re-run the utility even if the work dir has the file")
    ap.add_argument("--no-map", action="store_true", help="skip the map and preview")
    args = ap.parse_args(argv)

    engine: Path = args.engine
    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    images = load_sequence_images(engine)
    resolved: dict[str, dict[str, Any]] = {}
    pending: dict[str, list[tuple[str, ResolvedSequence]]] = {}
    files_needed: dict[str, str] = {}  # stem -> filename
    for image, (yaml_name, wanted) in NEEDED.items():
        if image not in images:
            print(f"WARNING: image {image} not found in sequences", file=sys.stderr)
            continue
        node, found_in = images[image]
        if found_in != yaml_name:
            print(f"NOTE: {image} is defined in {found_in}, not {yaml_name}", file=sys.stderr)
        defaults = node.child("Defaults")
        pending[image] = []
        for seq in node.children:
            if seq.key == "Defaults" or seq.key in EXCLUDED_SEQUENCES:
                continue
            if wanted is not None and seq.key not in wanted:
                continue
            rs = resolve_sequence(image, seq, defaults, TILESET)
            pending[image].append((seq.key, rs))
            for r in rs.reservations:
                stem = stem_of(r.filename)
                prev = files_needed.get(stem)
                if prev is not None and prev != r.filename:
                    raise SystemExit(f"stem clash: {prev} vs {r.filename}")
                files_needed[stem] = r.filename
        resolved[image] = {"yaml": found_in, "sequences": {}}
    for extra in EXTRA_FILES:
        files_needed.setdefault(stem_of(extra), extra)

    ex = Extractor(engine, args.work)
    pal = ex.extract_palette()
    lut = load_palette(pal)

    results: list[ExtractResult] = []
    frame_counts: dict[str, int] = {}
    for stem, filename in sorted(files_needed.items(), key=lambda kv: kv[0].lower()):
        r = ex.extract(filename, force=args.force)
        results.append(r)
        if r.error is not None:
            print(f"MISSING {filename}: {r.error}", file=sys.stderr)
            continue
        frame_counts[stem] = r.frames or 0
        print(f"{filename}: {r.frames} frames")

    removed = delete_obsolete(out)
    if removed:
        print(f"removed {len(removed)} obsolete files")

    file_info: dict[str, dict[str, Any]] = {}
    for r in results:
        if r.error is not None or r.frames is None:
            continue
        size: tuple[int, int] | None = None
        for i in range(r.frames):
            src = args.work / f"{r.stem}-{i:04d}.png"
            dst = out / f"{r.stem}-{i:04d}.png"
            if not src.exists():
                # 0x0 frames (the off frames of a muzzle flash, say) are skipped by the utility; write a transparent
                # pixel so every frame a sequence table names exists and the renderer never looks for a missing file
                if not dst.exists():
                    Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(dst, optimize=True)
                continue
            s = convert_frame(src, dst, lut)
            size = size or s
        file_info[r.stem] = {"source": r.filename, "frames": r.frames, "size": list(size) if size else None}

    for image, seqs in pending.items():
        for name, rs in seqs:
            resolved[image]["sequences"][name] = finalise_sequence(rs, frame_counts)

    sequences = {
        "openra_commit": git_commit(engine),
        "mod": MOD, "tileset": TILESET, "palette": PALETTE_FILE, "cell_px": CELL,
        "transparent_index": TRANSPARENT_INDEX, "shadow_index": SHADOW_INDEX, "shadow_alpha": SHADOW_ALPHA,
        "facing_notes": FACING_NOTES,
        "frame_addressing_notes": FRAME_ADDRESSING_NOTES,
        "wall_notes": WALL_NOTES,
        "bib_notes": BIB_NOTES,
        "files": file_info,
        "missing": [{"file": r.filename, "error": r.error} for r in results if r.error is not None],
        "images": resolved,
    }
    (out / "sequences.json").write_text(json.dumps(sequences, indent=1), encoding="utf-8")

    pngs = list(out.glob("*.png"))
    total = sum(p.stat().st_size for p in pngs)
    write_provenance(out / "PROVENANCE.md", engine, results, out, len(pngs), total, ex.commands)

    if not args.no_map:
        clear_frames = frame_counts.get("clear1", 16)
        available = {t for t in TREE_FOOTPRINTS if t in frame_counts and resolved.get(t, {}).get("sequences")}
        map_data = build_strip_map(53, 20, clear_frames, available)
        args.map.parent.mkdir(parents=True, exist_ok=True)
        args.map.write_text(json.dumps(map_data, separators=(",", ":")), encoding="utf-8")
        render_preview(map_data, out, sequences, args.preview)
        print(f"map: {args.map} ({len(map_data['decorations'])} tree clumps, {len(map_data['blocked'])} blocked cells)")

    n_seq = sum(len(v["sequences"]) for v in resolved.values())
    print(f"images: {len(resolved)}, sequences: {n_seq}, files: {len(file_info)}, missing: {len(sequences['missing'])}")
    print(f"png frames: {len(pngs)} ({total / 1024:.0f} KiB) in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
