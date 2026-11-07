"""The Mission Count's procedural pixel art (docs/THREE_PATHS_AND_FACES_PLAN.md 5.3): textures and billboard props for the three art worlds `airfield`, `city` and `harbour`.

What every id must look like is in tools/paths/squadron_tex_brief.json (written by tools/paths/make_squadron.py from the maps: {id: {kind, size, metres, desc, maps}}); the drawing
functions live in `tex_squadron_airfield.py`, `tex_squadron_city.py` and `tex_squadron_harbour.py`, each exporting a dict `DRAW = {id: fn}` where `fn()` returns a numpy uint8 array:

    kind "surface" / "ceil"   (n, n, 3) RGB, tileable both ways, n = 64 or 128 (the brief's `size` is the minimum)
    kind "sky"                (64, 256, 3) RGB, wraps horizontally
    kind "billboard"          (128, 128, 4) RGBA, or (128, 256, 4) for the wide props; alpha is hard (0 or 255) except for `blend: add` glows (flak burst, beams, birds may be soft)

An id is drawn once and written into every art folder whose maps use it (the same bytes), so a shared id looks the same in the hut of the airfield and the hut of the harbour.
`build(map_id)` writes assets/story/<map_id>/textures/<id>.png and returns the manifest `textures` section {id: {file, size, metres}}. Deterministic: seeded generators only.
"""
from __future__ import annotations

import importlib
import json
import os

import numpy as np
from PIL import Image

from . import lib

BRIEF = os.path.join(lib.ROOT, "tools", "paths", "squadron_tex_brief.json")
MODULES = ("tex_squadron_airfield", "tex_squadron_airfield2", "tex_squadron_city", "tex_squadron_harbour", "tex_squadron_surfaces")
OVERRIDES = ("tex_squadron_surfaces",)  # the redrawn 128 px surfaces and skies (package W7) replace the same ids of the older modules


def registry() -> dict:
    out: dict = {}
    for m in MODULES:
        try:
            mod = importlib.import_module("." + m, __package__)
        except ModuleNotFoundError as e:  # a module not written yet
            if m not in str(e):
                raise
            continue
        for k, fn in getattr(mod, "DRAW", {}).items():
            if k in out and m not in OVERRIDES:
                raise ValueError(f"texture {k} is drawn twice ({m})")
            out[k] = fn
    return out


def brief() -> dict:
    with open(BRIEF, encoding="utf-8") as fh:
        return json.load(fh)


def draw(tid: str, reg: dict, spec: dict) -> np.ndarray:
    arr = np.asarray(reg[tid]())
    kind = spec["kind"]
    if arr.dtype != np.uint8:
        raise ValueError(f"{tid}: must return uint8")
    h, w = arr.shape[:2]
    if kind in ("surface", "ceil"):
        if h != w or h not in (32, 64, 128) or arr.shape[2] not in (3, 4):
            raise ValueError(f"{tid}: a {kind} is n x n x 3 with n 64 or 128, got {arr.shape}")
    elif kind == "sky":
        if (h, w) != (64, 256) or arr.shape[2] != 3:
            raise ValueError(f"{tid}: a sky is 64 x 256 x 3, got {arr.shape}")
    elif kind == "billboard":
        if (h, w) not in ((128, 128), (128, 256)) or arr.shape[2] != 4:
            raise ValueError(f"{tid}: a billboard is 128 x 128 x 4 or 128 x 256 x 4, got {arr.shape}")
    return arr


def build(map_id: str, only=None) -> dict:
    reg = registry()
    b = brief()
    out_dir = os.path.join(lib.ROOT, "assets", "story", map_id, "textures")
    os.makedirs(out_dir, exist_ok=True)
    section: dict = {}
    for tid in sorted(b):
        spec = b[tid]
        if map_id not in spec["maps"] or (only and tid not in only):
            continue
        if tid not in reg:
            raise ValueError(f"{map_id}: texture {tid} is in the brief but no module draws it")
        arr = draw(tid, reg, spec)
        h, w = arr.shape[:2]
        mode = "RGBA" if arr.shape[2] == 4 else "RGB"
        Image.fromarray(arr, mode).save(os.path.join(out_dir, tid + ".png"), optimize=False, compress_level=9)
        section[tid] = {"file": f"textures/{tid}.png", "size": [w, h], "metres": float(spec["metres"])}
    if not only:  # a texture no map of this folder uses any more (or a stand-in for one) is removed with its import file
        for fn in os.listdir(out_dir):
            if fn.endswith(".png") and fn[:-4] not in section or fn.endswith(".png.import") and fn[:-11] not in section:
                os.remove(os.path.join(out_dir, fn))
    return section
