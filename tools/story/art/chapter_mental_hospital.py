"""Build target `mental_hospital`: art into assets/story/mental_hospital/ (see docs/STORY_ART.md and ART_CONTRACT_CHAPTERS2.md).

Reuses Night One's drawing helpers (lib.py) and rig conventions; only the output folders are redirected. Night One's own
output is never touched by this module.
"""
from __future__ import annotations

import json
import os

from . import lib

CHAPTER = "mental_hospital"


def _redirect():
    lib.ASSET_DIR = os.path.join(lib.ROOT, "assets", "story", CHAPTER)
    lib.SVG_DIR = os.path.join(lib.ASSET_DIR, "source")
    lib.PNG_DIR = os.path.join(lib.ASSET_DIR, "processed")


def build(only=()) -> int:
    saved = (lib.ASSET_DIR, lib.SVG_DIR, lib.PNG_DIR)
    _redirect()
    try:
        only = set(only)
        if not only:
            for d in (lib.SVG_DIR, lib.PNG_DIR):
                for dirpath, _dirs, files in os.walk(d):
                    for fn in files:
                        if not fn.endswith(".import"):
                            os.remove(os.path.join(dirpath, fn))
        os.makedirs(lib.SVG_DIR, exist_ok=True)
        os.makedirs(lib.PNG_DIR, exist_ok=True)
        manifest = {"version": 1, "level": CHAPTER, "px_scale_note": "texture px x px_scale = design px"}
        if not only or "chars" in only:
            from . import mh_chars
            manifest["archetypes"] = mh_chars.build_all()
        if not only or "stage" in only:
            from . import mh_stage
            manifest["silhouettes"] = mh_stage.build_silhouettes()
            manifest["stage"] = mh_stage.build_stage()
            manifest["interlude"] = mh_stage.build_interlude()
        path = os.path.join(lib.ASSET_DIR, "manifest.json")
        if only and os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                old = json.load(fh)
            old.update(manifest)
            manifest = old
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(manifest, fh, indent=1, sort_keys=False)
            fh.write("\n")
        for d in (lib.SVG_DIR, lib.PNG_DIR):
            for dirpath, _dirs, files in os.walk(d):
                for fn in files:
                    if fn.endswith(".import") and not os.path.exists(os.path.join(dirpath, fn[:-7])):
                        os.remove(os.path.join(dirpath, fn))
        n_svg = sum(1 for _, _, fs in os.walk(lib.SVG_DIR) for x in fs if x.endswith(".svg"))
        n_png = sum(1 for _, _, fs in os.walk(lib.PNG_DIR) for x in fs if x.endswith(".png"))
        print(f"Mental hospital art: {n_svg} SVG, {n_png} PNG, manifest {os.path.relpath(path, lib.ROOT)}")
        return 0
    finally:
        lib.ASSET_DIR, lib.SVG_DIR, lib.PNG_DIR = saved
