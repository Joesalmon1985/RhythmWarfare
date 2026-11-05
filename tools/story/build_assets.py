#!/usr/bin/env python3
"""Regenerate all original Story Campaign (Night One) art: `python3 tools/story/build_assets.py`.

Writes SVG into assets/story/night_one/source/, Pillow PNGs into assets/story/night_one/processed/ and the manifest
assets/story/night_one/manifest.json that the runtime reads. Deterministic: same inputs, byte-identical outputs. It only
touches assets/story/night_one/; no Ableton sources and no other game assets. See docs/STORY_ART.md.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from art import lib  # noqa: E402

# chapter build targets, one art folder each under assets/story/ (`build_assets.py underworld [chars|stage]`); a bare run builds all


# Chapter art builds: None = built in this file (build_chapter), a module path = that module's build(argv). Night One is the default.
CHAPTERS = {"mothership": None, "underworld": "art.chapter_underworld", "hospital": "art.chapter_hospital",
            "mental_hospital": "art.chapter_mental_hospital",
            "airfield": "art.chapter_airfield", "city": "art.chapter_city", "harbour": "art.chapter_harbour"}  # (the last three: the Mission Count path's worlds)


def strip_dead(path: str) -> None:
    """Fields only the removed 2D rooms read (stage anchors, each room's layers, anchors and palette hint, the pieces note) are dropped from a manifest."""
    with open(path, encoding="utf-8") as fh:
        man = json.load(fh)
    st = man.get("stage", {})
    for k in ("anchors", "design_size", "pieces_note"):
        st.pop(k, None)
    for v in st.get("views", []):
        for k in ("layers", "anchors", "palette_hint", "title"):
            v.pop(k, None)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1, sort_keys=False)
        fh.write("\n")


def add_tiles(name: str) -> None:
    """The 2.5D world's texture tiles of a chapter (baked by Godot from its SVG art) go into its manifest's `textures` section."""
    from art import tiles
    if name not in tiles.SPECS:
        return
    path = os.path.join(lib.ROOT, "assets", "story", name, "manifest.json")
    with open(path, encoding="utf-8") as fh:
        man = json.load(fh)
    man["textures"] = tiles.build(name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print(f"{name} tiles: {len(man['textures'])}")


def add_people(name: str) -> None:
    """The chapter's actors baked to indexed sprite sheets (people.py, wardrobe.py), named in the manifest's `people` section."""
    from art import people_sheets
    path = os.path.join(lib.ROOT, "assets", "story", name, "manifest.json")
    section = people_sheets.build(name)
    with open(path, encoding="utf-8") as fh:
        man = json.load(fh)
    man["people"] = section
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1, sort_keys=False)
        fh.write("\n")


def build_any(name: str, only: list) -> int:
    if list(only) == ["people"]:  # `build_assets.py hospital people`: only the actors' sprite sheets
        add_people(name)
        return 0
    if list(only) == ["tiles"]:  # `build_assets.py mothership tiles`: only the world's texture tiles
        add_tiles(name)
        return 0
    if CHAPTERS[name] is None:
        rc = build_chapter(name, set(only))
    else:
        import importlib
        rc = importlib.import_module(CHAPTERS[name]).build(list(only))
    strip_dead(os.path.join(lib.ROOT, "assets", "story", name, "manifest.json"))
    if not only:
        add_tiles(name)
        add_people(name)
    return rc


def build_chapter(name: str, only: set) -> int:
    """Chapter art (assets/story/<name>/): `python3 tools/story/build_assets.py mothership [chars|stage|interlude]`."""
    lib.set_chapter(name)
    if name == "mothership":
        from art import alien_chars as ch, mothership_stage as st
    else:
        raise SystemExit(f"unknown chapter {name}")
    path = os.path.join(lib.ASSET_DIR, "manifest.json")
    if not only:
        for d in (lib.SVG_DIR, lib.PNG_DIR):
            for dirpath, _dirs, files in os.walk(d):
                for fn in files:
                    if not fn.endswith(".import"):
                        os.remove(os.path.join(dirpath, fn))
    os.makedirs(lib.SVG_DIR, exist_ok=True)
    os.makedirs(lib.PNG_DIR, exist_ok=True)
    manifest: dict = {"version": 1, "level": name, "px_scale_note": "texture px x px_scale = design px"}
    if not only or "chars" in only:
        manifest["archetypes"] = ch.build_all()
    if not only or "stage" in only:
        manifest["silhouettes"] = st.build_silhouettes()
        manifest["stage"] = st.build_stage()
    if not only or "interlude" in only:
        manifest["interlude"] = st.build_interlude()
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
    print(f"{name} art: {n_svg} SVG, {n_png} PNG, manifest {os.path.relpath(path, lib.ROOT)}")
    return 0


def main(argv) -> int:
    if len(argv) > 2 and argv[1] == "night_one" and argv[2:] == ["people"]:
        add_people("night_one")
        return 0
    if len(argv) > 1 and argv[1] in CHAPTERS:
        return build_any(argv[1], argv[2:])
    only = set(argv[1:])
    if not only:  # a full rebuild starts clean so removed assets do not linger (Godot's .import files are kept for now)
        for d in (lib.SVG_DIR, lib.PNG_DIR):
            for dirpath, _dirs, files in os.walk(d):
                for fn in files:
                    if not fn.endswith(".import"):
                        os.remove(os.path.join(dirpath, fn))
    os.makedirs(lib.SVG_DIR, exist_ok=True)
    os.makedirs(lib.PNG_DIR, exist_ok=True)
    manifest: dict = {"version": 1, "level": "night_one", "px_scale_note": "texture px x px_scale = design px"}
    if not only or "chars" in only:
        from art import chars
        manifest["archetypes"] = chars.build_all()
    if not only or "stage" in only:
        from art import stage
        manifest["silhouettes"] = stage.build_silhouettes()
        manifest["stage"] = stage.build_stage()
    if not only or "tiles" in only:
        from art import tiles
        manifest["textures"] = tiles.build("night_one")
    path = os.path.join(lib.ASSET_DIR, "manifest.json")
    if only and os.path.exists(path):  # partial build: keep the other sections
        with open(path, encoding="utf-8") as fh:
            old = json.load(fh)
        old.update(manifest)
        manifest = old
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=False)
        fh.write("\n")
    strip_dead(path)
    if not only:
        add_people("night_one")
    for d in (lib.SVG_DIR, lib.PNG_DIR):  # drop .import files whose asset is gone
        for dirpath, _dirs, files in os.walk(d):
            for fn in files:
                if fn.endswith(".import") and not os.path.exists(os.path.join(dirpath, fn[:-7])):
                    os.remove(os.path.join(dirpath, fn))
    n_svg = sum(1 for _, _, fs in os.walk(lib.SVG_DIR) for x in fs if x.endswith(".svg"))
    n_png = sum(1 for _, _, fs in os.walk(lib.PNG_DIR) for x in fs if x.endswith(".png"))
    print(f"Night One art: {n_svg} SVG, {n_png} PNG, manifest {os.path.relpath(path, lib.ROOT)}")
    if not only:  # a full rebuild also regenerates the chapter art (Night One first: it uses the default lib paths)
        for ch in CHAPTERS:
            build_any(ch, [])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
