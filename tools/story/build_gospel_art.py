#!/usr/bin/env python3
"""Builds the Gospel path's four art folders (assets/story/{galilee_shore,hillside,bethany,jerusalem}/): `python3 tools/story/build_gospel_art.py [maps...] [--people]`.

1. `tools/story/art/gospel_maps.py` writes the maps (content/story/maps/<map>.json) and the story-data files (content/story/<map>.json);
2. `gospel_tex.py` (floors, walls, ceilings, skies) and `gospel_things_a.py` / `gospel_things_b.py` (billboard props and set pieces) draw every tile and sprite into a staging
   folder; each map's folder gets only the ones its map uses, with a manifest (`textures`, `stage.sprites` glow and vignette copied from Night One, `stage.pieces` for the things
   a scene switches on and off);
3. with `--people` the people sheets are baked (tools/story/art/people_sheets.py: the wardrobe archetypes of `gospel()`, the acts and faces the path's data directs).

Run `godot --headless --path . --import` afterwards so the new PNGs get their `.import` files. Deterministic.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from art import gospel_maps, gospel_tex, gospel_things_a, gospel_things_b, lib  # noqa: E402

ROOT = Path(lib.ROOT)


def build(maps: list, people: bool) -> None:
    built = gospel_maps.build_all(True)
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp)
        info = {}
        info.update(gospel_tex.build(str(stage)))
        for mod in (gospel_things_a, gospel_things_b):
            for name, d in mod.build(str(stage)).items():
                info[name] = {"size": d["size"], "metres": 1.0, "blend": d.get("blend", "")}
        night = json.loads((ROOT / "assets/story/night_one/manifest.json").read_text(encoding="utf-8"))
        for mid in maps:
            m, sd = built[mid]
            out = ROOT / "assets" / "story" / mid
            tex_dir = out / "textures"
            if tex_dir.exists():
                for f in tex_dir.glob("*.png"):
                    f.unlink()
            tex_dir.mkdir(parents=True, exist_ok=True)
            (out / "processed").mkdir(parents=True, exist_ok=True)
            textures = {}
            for name in sorted(m["textures"]):
                src = stage / f"{name}.png"
                if not src.exists():
                    raise SystemExit(f"{mid}: texture {name} is not drawn by gospel_tex / gospel_things_*")
                shutil.copyfile(src, tex_dir / f"{name}.png")
                textures[name] = {"file": f"textures/{name}.png", "size": info[name]["size"], "metres": info[name]["metres"]}
            sprites = {}
            for sid in ("glow", "vignette"):
                e = night["stage"]["sprites"][sid]
                shutil.copyfile(ROOT / "assets/story/night_one" / e["file"], out / "processed" / Path(e["file"]).name)
                sprites[sid] = {"file": "processed/" + Path(e["file"]).name, "pivot": e["pivot"], "px_scale": e["px_scale"]}
            pieces = []
            for t in m["things"]:
                if "piece" in t:
                    pieces.append({"id": t["piece"], "file": f"textures/{t['sprite']}.png", "blend": t.get("blend", "mix") or "mix", "anim": "none"})
            man_path = out / "manifest.json"
            man = json.loads(man_path.read_text(encoding="utf-8")) if man_path.exists() else {}
            man.update({"version": 1, "level": mid, "px_scale_note": "the Gospel path's maps have no SVG rigs: the world is textures, billboards and baked people", "textures": textures,
                        "stage": {"sprites": sprites, "pieces": pieces, "views": []}, "archetypes": {}})
            man_path.write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
            print(f"{mid}: {len(textures)} textures, {len(pieces)} pieces, {len(sd['actors'])} people")
    if people:
        from art import people_sheets
        for mid in maps:
            section = people_sheets.build(mid)
            man_path = ROOT / "assets" / "story" / mid / "manifest.json"
            man = json.loads(man_path.read_text(encoding="utf-8"))
            man["people"] = section
            man_path.write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    build(args or list(gospel_maps.MAPS), "--people" in sys.argv)
