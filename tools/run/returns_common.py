#!/usr/bin/env python3
"""The return objects of the three quest paths (work package N2.5 of the one-PC plan): one hotspot row per scene, `<quest>.return`, route `run:warehouse`.

    python tools/run/returns_common.py [--check]      # writes the rows into content/paths/<quest>/hotspots/*.json in place (idempotent); --check: exit 1 if a file is not up to date

The generators of the paths (tools/run/make_ember.py, tools/paths/make_squadron.py, tools/content/make_gospel.py) call `add_rows` on their hotspot lists, so a regenerated file
keeps its returns. The Gospel's generator has drifted from its committed files (hand-set staging, an acting line), so its returns are written in place by this script; do not
regenerate the Gospel's hotspots before that drift is settled.

THE OBJECT. One definition per quest (DEFS), the same object in every scene of the quest: the Warehouse's own steel fire door with the green running-man plate
(assets/run/choice/warehouse/door_*.png), standing in the scene like a door that does not belong to that world. Shut-but-ajar (door_1: a sliver of the club's violet light) while it is
not the pick, wide open on the lit corridor (door_3) when it is; it pulses on the beat (staging motion `pulse`: the bass thump). It is staged by the choice layer's `prop` steps with
the art's path under the shared folder (`warehouse/door_N`), so a world's own door set (galilee, airfield, ash ...) never replaces it. It is a hotspot of kind `object`, not an exit
(an exit is one per route and may be the default; the return is neither).

NEVER GATED. Success routes `run:warehouse` (the router lands it on the checkpoint, N2.2) and so does failure, with a small energy cost: the miss is not a refusal and does not change where
the object leads (docs/narrative/N2_2_ROUTER.md "No rhythm gate": a failure that leads the same way as the success stays as authored).

WHERE IT STANDS. The default rule: from the rail's top place of the scene (where the camera ends its walk and looks at the choices from beat 40), AHEAD metres in front of it and LEFT metres to the
left of its heading: the camera sees it left of centre at the opening (walking in from home it is further ahead) and in the choice window, not over the middle of the picture where the onward
exits are. A scene whose default spot is in a wall, out of sight, or crowded has its own spot in SPOTS (the table; tools/run/return_spots.gd checks every spot against the real camera and
searches a better one: `--check <json of {"<quest>/<scene>": [x, y, z]}>`).
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))

AHEAD = 8.0
LEFT = 5.0
CENTRE_Y = 1.5  # the anchor's height: the middle of a 3 m door
ENERGY_MISS = -5

# One definition per quest: the same object, so the player learns it once. Where a quest wants its own height or look later, it is changed here, in one place.
DEFS = {
    "gospel": {"id": "gospel.return", "height_m": 3.0},
    "squadron": {"id": "squadron.return", "height_m": 3.0},
    "ember": {"id": "ember.return", "height_m": 3.0},
}
ART_SHUT = "warehouse/door_1"
ART_OPEN = "warehouse/door_3"
ART_LAMP = "warehouse/lamp_go"

# Per-scene spots ("<quest>/<scene id>": [x, z]) where the default rule's spot fails (tools/run/return_spots.gd). Filled by the survey; see the file's header.
SPOTS: dict = {
    "ember/deeps": [-5.38, 14.48],
    "ember/deeps.falls": [-5.08, -49.03],
    "ember/hollow": [-6.42, 1.04],
    "ember/hollow.ford": [-3.05, -25.32],
    "ember/hollow.inn": [23.05, -25.03],
    "ember/marsh": [-7.13, 14.89],
    "ember/marsh.plain": [-6.29, -50.88],
    "ember/marsh.stair": [13.15, -43.48],
    "ember/mountain": [-3.51, -92.75],
    "ember/mountain.keeper": [19.1, -107.05],
    "ember/mountain.taken": [-23.36, -7.41],
    "ember/north": [-3.41, 8.59],
    "ember/north.pass": [-6.39, -20.49],
    "gospel/galilee": [-2.6, -5.3],
    "gospel/galilee.capernaum": [13.9, -2.9],
    "gospel/jerusalem": [-7.75, -3.07],
    "gospel/jerusalem.golgotha": [46.79, -4.41],
    "gospel/jerusalem.road": [86.04, -6.41],
    "gospel/jerusalem.trial": [29.03, -8.41],
    "gospel/jordan": [-4.35, -4.29],
    "gospel/jordan.wilderness": [29.65, -4.4],
    "gospel/road": [-5.64, -7.4],
    "gospel/road.entry": [29.4, -3.9],
    "gospel/road.loaves": [12.64, -7.9],
    "squadron/air.c05": [37.36, 0.38],
    "squadron/air.c06": [-7.36, 0.33],
    "squadron/base": [-8.87, 7.72],
    "squadron/base.c02": [12.28, 0.38],
    "squadron/base.c03": [0.42, -8.35],
    "squadron/city.c08": [13.11, 0.63],
    "squadron/city.c09": [11.34, 15.56],
    "squadron/city.c10": [31.1, 0.41],
    "squadron/escape": [-11.63, 7.59],
    "squadron/escape.c12": [13.29, 1.39],
    "squadron/escape.c13": [35.29, 1.12],
    "squadron/escape.c14": [0.68, -5.94],
}


def staging(q: str) -> dict:
    h = DEFS[q]["height_m"]
    beacon = {"prop": ART_LAMP, "at": [0.0, h + 0.4, 0.0], "size": 0.6}  # the Warehouse's green round lamp over the door: a lit beacon that a dark steel door needs in a snow storm or a night harbour
    shut = [{"prop": ART_SHUT, "size": h, "motion": "pulse"}, beacon]
    wide = [{"prop": ART_OPEN, "size": h, "motion": "pulse"}, beacon]
    return {"archetype": "door", "door": "none", "lamp": False, "height_m": h, "touch": {"w": 2.2, "h": 3.4},
            "states": {"current": wide, "other": shut, "committed": wide, "declined": shut}}


def staging_of(hotspot_id: str):
    """The staging block of a return row (tools/run/apply_staging.py keeps it: that script removes a `staging` that its table does not know)."""
    for q, d in DEFS.items():
        if hotspot_id == d["id"]:
            return staging(q)
    return None


def _maps() -> dict:
    out = {}
    for fn in glob.glob(os.path.join(ROOT, "content", "story", "maps", "*.json")):
        out[os.path.splitext(os.path.basename(fn))[0]] = json.load(open(fn, encoding="utf-8"))
    return out


def _fwd(yaw):
    r = math.radians(yaw)
    return (-math.sin(r), -math.cos(r))


def _right(yaw):
    r = math.radians(yaw)
    return (math.cos(r), -math.sin(r))


def default_spot(maps: dict, map_id: str, node: dict) -> list:
    rail = node["place"]["rail"]
    good = rail.get("good", [])
    wp = good[-1]["to"] if good else node["place"]["waypoint"]
    w = next(w for w in maps[map_id]["waypoints"] if w["id"] == wp)
    f, r = _fwd(w.get("yaw", 0.0)), _right(w.get("yaw", 0.0))
    return [round(w["at"][0] + f[0] * AHEAD - r[0] * LEFT, 2), round(w["at"][1] + f[1] * AHEAD - r[1] * LEFT, 2)]


def row(q: str, node: dict, world: dict, xz: list) -> dict:
    return {"id": DEFS[q]["id"], "world": node["world"], "scene": node["id"], "map": world["map"], "anchor": {"pos": [xz[0], CENTRE_Y, xz[1]]}, "kind": "object", "radius_m": 1.2, "min_px": 88,
            "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
            "look": {"available": "glow", "selected": "ring", "committed": "flash"}, "challenge": None,
            "on_success": {"route": "run:warehouse"}, "on_failure": {"route": "run:warehouse", "energy": ENERGY_MISS},
            "default": False, "repeatable": True, "staging": staging(q)}


def return_rows(q: str, run: dict) -> list:
    maps = _maps()
    worlds = {w["id"]: w for w in run["worlds"]}
    out = []
    for n in run["nodes"]:
        wd = worlds[n["world"]]
        xz = SPOTS.get(f"{q}/{n['id']}") or default_spot(maps, wd["map"], n)
        out.append(row(q, n, wd, xz))
    return out


def add_rows(q: str, hotspots: list, run: dict) -> list:
    """`hotspots`: the quest's rows in file order (dicts). Returns them with a fresh return row after the last row of each scene (an existing return row is dropped first)."""
    rid = DEFS[q]["id"]
    base = [h for h in hotspots if h["id"] != rid]
    rows = {r["scene"]: r for r in return_rows(q, run)}
    out = []
    last = {h["scene"]: i for i, h in enumerate(base)}
    for i, h in enumerate(base):
        out.append(h)
        if last[h["scene"]] == i and h["scene"] in rows:
            out.append(rows.pop(h["scene"]))
    for sid, r in rows.items():  # a scene with no row yet: at the end
        out.append(r)
    return out


def main(argv: list) -> int:
    check = "--check" in argv
    stale = []
    for q in DEFS:
        d = os.path.join(ROOT, "content", "paths", q)
        run = json.load(open(os.path.join(d, "run.json"), encoding="utf-8"))
        for fn in sorted(glob.glob(os.path.join(d, "hotspots", "*.json"))):
            doc = json.load(open(fn, encoding="utf-8"))
            new = {**doc, "hotspots": add_rows(q, doc["hotspots"], {"worlds": run["worlds"], "nodes": [n for n in run["nodes"] if n["world"] == doc["world"]]})}
            text = json.dumps(new, indent=1, ensure_ascii=False) + "\n"
            if open(fn, encoding="utf-8").read() != text:  # (universal newlines: a CRLF working copy compares as LF)
                stale.append(os.path.relpath(fn, ROOT))
                if not check:
                    with open(fn, "w", encoding="utf-8", newline="\n") as fh:
                        fh.write(text)
    if check and stale:
        print("not up to date: " + ", ".join(stale))
        return 1
    print("returns: " + (("wrote " + ", ".join(stale)) if stale and not check else "up to date"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
