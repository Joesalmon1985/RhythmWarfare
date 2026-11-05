"""Build targets `airfield`, `city` and `harbour` (the Mission Count's three art worlds): textures and billboard props into assets/story/<map>/textures/ and the manifest.

The people sheets are added by build_assets.py (`add_people`), the textures come from tex_squadron.py (tools/paths/squadron_tex_brief.json says what each is). The manifest borrows Night One's light and
deck sprites (`borrow_sprites`: StoryAssets.sprite falls back to the shared art set), so these worlds need no SVG art of their own.
"""
from __future__ import annotations

import json
import os

from . import lib, tex_squadron


def build_map(name: str, only=()) -> int:
    root = os.path.join(lib.ROOT, "assets", "story", name)
    os.makedirs(root, exist_ok=True)
    path = os.path.join(root, "manifest.json")
    man: dict = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            man = json.load(fh)
    man.update({"version": 1, "level": name, "px_scale_note": "the Mission Count's worlds have no SVG rigs: textures and baked people only", "borrow_sprites": True})
    man["textures"] = tex_squadron.build(name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print(f"{name} art: {len(man['textures'])} textures, manifest {os.path.relpath(path, lib.ROOT)}")
    return 0
