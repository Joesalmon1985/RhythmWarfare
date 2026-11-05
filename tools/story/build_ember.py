#!/usr/bin/env python3
"""Builds the Ember Road's art: `python3 tools/story/build_ember.py [tiles|manifest|people] [map ...]`.

tiles     assets/story/<map>/textures/*.png  (tools/story/art/tex_ember_tiles.py and tex_ember_things.py)
manifest  assets/story/<map>/manifest.json   (the textures section; the people section is kept)
people    the people's sprite sheets (tools/story/art/people_sheets.py): needs content/story/<map>.json (tools/story/ember_maps.py) and the run data's acting and cast
          (tools/run/make_ember.py), which decide what each person is baked in.
No argument: tiles, manifest and people for all four maps. Run `godot --headless --path . --import` afterwards.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

from art import ember_spec, lib, people_sheets, tex_ember_things, tex_ember_tiles  # noqa: E402


def manifest_path(art: str) -> str:
    return os.path.join(ROOT, "assets", "story", art, "manifest.json")


def read_manifest(art: str) -> dict:
    p = manifest_path(art)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    return {"version": 1, "level": art, "px_scale_note": "the Ember Road's maps have no rigs; their world is textures and sprite sheets only"}


def write_manifest(art: str, man: dict) -> None:
    with open(manifest_path(art), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1, sort_keys=False)
        fh.write("\n")


def build_tiles(art: str) -> dict:
    section = {}
    section.update(tex_ember_tiles.build(art))
    section.update(tex_ember_things.build(art))
    man = read_manifest(art)
    man["textures"] = dict(sorted(section.items()))
    write_manifest(art, man)
    print(f"{art}: {len(section)} textures")
    return section


def build_people(art: str) -> None:
    lib.set_chapter(art) if hasattr(lib, "set_chapter") else None
    section = people_sheets.build(art)
    man = read_manifest(art)
    man["people"] = section
    write_manifest(art, man)


def main(argv: list) -> int:
    what = [a for a in argv if a in ("tiles", "manifest", "people")]
    arts = [a for a in argv if a in ember_spec.ARTS] or list(ember_spec.ARTS)
    for art in arts:
        if not what or "tiles" in what or "manifest" in what:
            build_tiles(art)
        if not what or "people" in what:
            build_people(art)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
