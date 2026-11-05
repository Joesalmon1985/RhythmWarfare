#!/usr/bin/env python3
"""Writes everything of the Mission Count (`squadron`, docs/THREE_PATHS_AND_FACES_PLAN.md section 5) that is data:

    content/story/maps/{airfield,city,harbour}.json      the three maps (tools/paths/squadron_{airfield,city,harbour}.py)
    content/story/{airfield,city,harbour}.json           the chapter data the stage and the people-sheet baker read (actors, groups, palettes)
    content/paths/squadron/run.json                      140 BPM, 14 scenes, routes, rails, cast, cinematics
    content/paths/squadron/music.json                    the owner's 14 loops (packs squadron_c01 .. c14, made by tools/content/import_squadron.py)
    content/paths/squadron/hotspots/<world>.json         the hotspots with their acting
    tools/paths/squadron_tex_brief.json                  what every texture of the three art folders must show (tools/story/art/tex_squadron.py builds them)

    python3 tools/paths/make_squadron.py [--standins]    (--standins writes flat stand-in PNGs for textures that do not exist yet)

Idempotent. Yaw: 0 faces -z, 90 faces -x, 180 faces +z, -90 faces +x.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import squadron_airfield  # noqa: E402
import squadron_city  # noqa: E402
import squadron_harbour  # noqa: E402
import squadron_lib  # noqa: E402
import squadron_story as st  # noqa: E402

PATHDIR = ROOT / "content" / "paths" / "squadron"

TITLES = {"airfield": "The Airfield", "city": "The Old City", "harbour": "The Harbour"}
BASE_PALETTES = {"low": ["#a88a58", "#7a6a50"], "cool": ["#6f8fd0", "#a0c0ff"], "warm": ["#ffb060", "#ffd890"], "rave": ["#ffd890", "#ffb060", "#a0c0ff", "#fff0c0"]}
EXTRA_PALETTES = {
    "airfield": {"khaki": ["#ffd890", "#ffb060"], "glare": ["#fff0c0", "#ffe090"], "instrument": ["#60ff90", "#ffa040"]},
    "city": {"red": ["#ff4030", "#ff8060"], "sepia": ["#ffc070", "#d08040"], "fire": ["#ff7030", "#ffb060"]},
    "harbour": {"khaki": ["#ffd890", "#ffb060"], "searchlight": ["#a0c8ff", "#ffffff"], "bright": ["#fff0a0", "#ffffff"], "cold": ["#8aa0d0", "#6070a0"]},
}
ENERGY = {"pass_delta": {"sharp": 4, "steady": 3, "loose": 2}, "fail_delta": -5, "min": 0, "max": 100,
          "bands": [{"id": "quiet", "label": "Unimpressed", "max": 29}, {"id": "dancing", "label": "Dancing", "max": 64}, {"id": "hype", "label": "Hype", "max": 84}, {"id": "euphoric", "label": "Euphoric", "max": 100}]}


def dump(path: Path, doc, compact=False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=None if compact else 1, ensure_ascii=False)
        fh.write("\n")


def build_maps() -> dict:
    out = {}
    for name, mod, start in (("airfield", squadron_airfield, "c01_home"), ("city", squadron_city, "c07_home"), ("harbour", squadron_harbour, "c11_home")):
        mb = mod.build()
        out[name] = mb
        dump(ROOT / "content" / "story" / "maps" / f"{name}.json", mb.map_json(start))
        actors = [dict(a) for a in mb.actors]
        ids = [a["id"] for a in actors]
        chapter = {"id": name, "title": TITLES[name], "chapter": 0, "art": name, "run_only": True, "duration_bars": 64, "sequence_bars": 2, "initial_energy": 60,
                   "description": "A map of the Mission Count path (content/paths/squadron): the stage the run builds, not a chapter of the old campaign.",
                   "palettes": {**BASE_PALETTES, **EXTRA_PALETTES[name]}, "energy": ENERGY, "acts": [], "blocks": [], "decisions": [], "endings": {}, "ending_order": [],
                   "groups": {"all": ids, "core": ids}, "actors": actors, "silhouettes": []}
        dump(ROOT / "content" / "story" / f"{name}.json", chapter)
    return out


def rail_of(code: str, dirs: list) -> dict:
    p = code.lower()
    return {"waypoint": f"{p}_home", "rail": {
        "good": [{"to": f"{p}_g1", "role": "dancer", "style": "walk", "bars": 3}, {"to": f"{p}_g2", "role": "dancer", "style": "walk", "bars": 3}],
        "bad": [{"to": f"{p}_b1", "role": "queasy", "style": "walk", "bars": 2}, {"to": f"{p}_b2", "role": "queasy", "style": "walk", "bars": 2}],
        "arrive": f"{p}_arrive",
        "glances": [{"by": -12, "pitch": 8, "bars": 2}, {"by": -28, "bars": 2}, {"pitch": 14, "bars": 3}, {"by": 24, "bars": 2}],
        "strolls": [{"fwd": 1.2, "bars": 3}, {"turn": 35, "fwd": 0.8, "bars": 3}, {"right": 1.0, "bars": 2}],
        "exits": {d: f"{p}_x_{d}" for d in dirs}}}


def build_run() -> dict:
    nodes = []
    for code, s in st.S.items():
        routes = []
        for r in s["routes"]:
            e = {"to": st.nid(r[0]), "dir": r[1], "label": ("Back to the Warehouse" if r[0] == "run:warehouse" else f"On to {st.S[r[0]]['title']}")}
            if len(r) > 2 and r[2]:
                e["loop"] = True
            routes.append(e)
        n = {"id": s["id"], "world": s["world"], "scene": code.lower(), "title": s["title"], "entry": s["entry"], "exit_scene": s["exit"], "role": "dancer",
             "blurb": f"{code}: {s['title']}.", "next": routes, "cast": st.CAST[code], "place": rail_of(code, [r[1] for r in s["routes"]])}
        if s.get("ending"):
            n["ending"] = s["ending"]
        nodes.append(n)
    cin = {k: v for k, v in st.CINEMATICS.items()}
    return {"schema": 1,
            "path": {"id": "squadron", "title": "The Mission Count", "entry_from": "warehouse.booth.radio", "returns_to": "warehouse",
                     "opens": "A flickering military radio in the booth, with the shadow of a bomber on the wall behind it."},
            "timing": {"bpm": 140, "phase_beats": 64, "block_beats": 16, "cue_span_beats": 12.0, "decision_beat": 12.5, "fade_beats": 2.0},
            "stages": [{"id": "drums_alone", "label": "Drums", "cue": "drums", "gains": {"drums": 1.0, "bass": 0.0, "other": 0.0}},
                       {"id": "bass_enters", "label": "Bass enters", "cue": "bass", "gains": {"drums": 0.7, "bass": 1.0, "other": 0.0}},
                       {"id": "synth_joins", "label": "Drums return, synth joins", "cue": "drums", "gains": {"drums": 1.0, "bass": 0.9, "other": 0.5}},
                       {"id": "bass_strongest", "label": "Bass strongest", "cue": "bass", "gains": {"drums": 0.55, "bass": 1.0, "other": 0.7}}],
            "start_node": st.S["C01"]["id"], "worlds": st.WORLDS, "nodes": nodes, "cinematics": cin}


def build_hotspots() -> dict:
    by_world: dict = {w["id"]: [] for w in st.WORLDS}
    for code, lst in st.HOTSPOTS.items():
        s = st.S[code]
        for h in lst:
            h = dict(h)
            h["world"] = s["world"]
            h["map"] = st.MAP_OF_WORLD[s["world"]]
            h.setdefault("min_px", 72)
            h["available"] = {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False}
            h["look"] = {"available": h["look"]["available"], "selected": "ring", "committed": "flash"}
            h["challenge"] = None
            h["default"] = bool(h.get("default", False))
            h["repeatable"] = bool(h.get("repeatable", False))
            order = ["id", "world", "scene", "map", "anchor", "kind", "radius_m", "min_px", "available", "look", "challenge", "on_success", "on_failure", "default", "repeatable"]
            h = {**{k: h[k] for k in order}, **{k: v for k, v in h.items() if k not in order}}
            by_world[s["world"]].append(h)
    return {w: {"world": w, "hotspots": hs} for w, hs in by_world.items()}


def build_music() -> dict:
    nodes = [{"id": s["id"], "audio": st.PACK[code], "chart": st.PACK[code], "treatment": "none"} for code, s in st.S.items()]
    return {"schema": 1, "note": "The owner's 14 Squadron loops (140 BPM, 4-bar phrases), imported by tools/content/import_squadron.py into songs/packs/squadron_c01 .. c14. Not temporary.", "nodes": nodes}


def standins(mbs: dict) -> None:
    """Flat stand-in PNGs for every texture that has no file yet (so the maps load and can be shot before the art is built)."""
    from PIL import Image
    import hashlib
    for tid, e in squadron_lib.TEX.items():
        for m in e["maps"]:
            p = ROOT / "assets" / "story" / m / "textures" / f"{tid}.png"
            if p.exists():
                continue
            p.parent.mkdir(parents=True, exist_ok=True)
            h = int(hashlib.md5(tid.encode()).hexdigest()[:6], 16)
            col = (80 + (h & 0x7F), 70 + ((h >> 7) & 0x7F), 60 + ((h >> 14) & 0x7F))
            if e["kind"] == "billboard":
                im = Image.new("RGBA", (e["size"] if e["size"] >= 128 else 128, 128 if e["size"] != 256 else 128), (0, 0, 0, 0))
                w, hgt = im.size
                for y in range(hgt // 6, hgt - 4):
                    for x in range(w // 4, w - w // 4):
                        im.putpixel((x, y), col + (255,))
            elif e["kind"] == "sky":
                im = Image.new("RGB", (256, 64), col)
            else:
                im = Image.new("RGB", (e["size"], e["size"]), col)
            im.save(p)


def keep_mix(run: dict, music: dict) -> None:
    """The audio polish's data survives a rewrite: run.json `mix` (the path's level and bass bus) and each scene's music.json `bass_bus` (docs/HANDOVER.md "Audio polish")."""
    if (PATHDIR / "run.json").exists():
        old = json.loads((PATHDIR / "run.json").read_text(encoding="utf-8"))
        if "mix" in old:
            run["mix"] = old["mix"]
    if (PATHDIR / "music.json").exists():
        bb = {n["id"]: n["bass_bus"] for n in json.loads((PATHDIR / "music.json").read_text(encoding="utf-8"))["nodes"] if "bass_bus" in n}
        for n in music["nodes"]:
            if n["id"] in bb:
                n["bass_bus"] = bb[n["id"]]


def main(argv) -> int:
    mbs = build_maps()
    run, music = build_run(), build_music()
    keep_mix(run, music)
    dump(PATHDIR / "run.json", run)
    dump(PATHDIR / "music.json", music)
    for w, doc in build_hotspots().items():
        dump(PATHDIR / "hotspots" / f"{w}.json", doc)
    brief = {}
    for tid in sorted(squadron_lib.TEX):
        if squadron_lib.TEX[tid]["maps"]:
            brief[tid] = squadron_lib.TEX[tid]
    order = ["airfield", "city", "harbour"]
    for tid in brief:
        brief[tid]["maps"].sort(key=order.index)
    dump(HERE / "squadron_tex_brief.json", brief)
    if "--standins" in argv:
        standins(mbs)
    n_things = sum(len(m.things) for m in mbs.values())
    print(f"squadron: {len(mbs)} maps, {sum(len(m.actors) for m in mbs.values())} actors, {n_things} things, {len(brief)} textures, 14 scenes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
