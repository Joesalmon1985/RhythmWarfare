#!/usr/bin/env python3
"""The extra routes of the three quest paths (lead ruling 17; docs/parallel-development/NARRATIVE_GRAPH.md 2.4 and 2.5): the routes that give every path scene three distinct destinations
where its onward routes and its return (N2.5, tools/run/returns_common.py) give fewer.

    python tools/run/path_routes.py [--check]      # writes the routes into content/paths/<quest>/run.json and their rows into hotspots/*.json in place (idempotent); --check: exit 1 if stale

THE ROUTES (ROUTES below; the graph overlay content/narrative/graph.json `extra_routes` names the same objects):
  restart       an ending's way to the quest's first scene: a completed quest restarts there (D3). The ending's own way back (`run:warehouse`) stays its first route and its default;
                the restart sets the ending's keep flag too, so the quest counts as finished whichever way the player leaves.
  second_route  an entry scene's second way on (the entry scenes have one onward scene); the destinations were picked only so the graph is valid: the owner confirms them.
  back          the way back to the scene the player came from, for a scene that has one onward route (and for every ending, as its third way): a fixed scene (the scene's one predecessor; for the Ember's Deeps, entered from
                the North or its pass, the North, since the pass is already its other way on). Marked `loop` inside a world (a world keeps no cycle of its own).
Every route is a touchable object, not an exit (a path's route may be reached by a touch: tools/run/check_hotspots.py), never the default and never rhythm-gated (a miss leads the same
way, with a small energy cost, like the return). It shows as a door of the world's own door set (its `show` block, apply_staging.py) and stands where SPOTS says, else by the default
rule: from the rail's top place, AHEAD metres in front of it and RIGHT metres to its right (the return stands to the left). The route's doorway in rail.exits is the scene's own first
doorway (the walk out goes by it).

The generators of the paths (tools/run/make_ember.py, tools/paths/make_squadron.py, tools/content/make_gospel.py) are not re-run for this: like the returns, the routes are written in
place; a generator that is re-run must call `apply` (run.json) and `add_rows` (hotspots) as it calls returns_common.add_rows.
"""
from __future__ import annotations

import glob
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import returns_common  # noqa: E402

AHEAD = 7.0
RIGHT = 4.5
CENTRE_Y = 1.5
ENERGY_MISS = -4

# (quest, scene, kind, to, object id (the hotspot id: the scene's id first, tools/run/check_hotspots.py), dir, label)
ROUTES = [
    ("gospel", "jerusalem.tomb", "restart", "jordan", "jerusalem.tomb.restart", "restart", "Back to the Jordan, the life again"),
    ("gospel", "jerusalem.road", "restart", "jordan", "jerusalem.road.restart", "restart", "Back to the Jordan, the life again"),
    ("squadron", "escape.c13", "restart", "base", "escape.c13.restart", "restart", "Back to the base, the missions again"),
    ("ember", "mountain.spring", "restart", "hollow", "mountain.spring.restart", "restart", "Back to the Hollow, the road again"),
    ("ember", "mountain.keeper", "restart", "hollow", "mountain.keeper.restart", "restart", "Back to the Hollow, the road again"),
    ("gospel", "jordan", "second_route", "jordan.nazareth", "jordan.skip", "skip", "Straight on to Nazareth"),
    ("ember", "hollow", "second_route", "hollow.inn", "hollow.skip", "skip", "Straight to the inn"),
    ("gospel", "jerusalem.golgotha", "back", "jerusalem.trial", "jerusalem.golgotha.back", "back", "Back to the trial"),
    ("ember", "deeps", "back", "north", "deeps.back", "back", "Back to the North"),
    # an ending's third way (its way back to the run and its restart are two): back to the scene before it
    ("gospel", "jerusalem.tomb", "back", "jerusalem.golgotha", "jerusalem.tomb.back", "back", "Back to the hill"),
    ("gospel", "jerusalem.road", "back", "jerusalem.trial", "jerusalem.road.back", "back", "Back to the trial"),
    ("squadron", "escape.c13", "back", "escape.c12", "escape.c13.back", "back", "Back to the quay"),
    ("ember", "mountain.spring", "back", "mountain", "mountain.spring.back", "back", "Back down the mountain"),
    ("ember", "mountain.keeper", "back", "mountain", "mountain.keeper.back", "back", "Back down the mountain"),
]
# Per-scene spots ("<quest>/<scene id>": [x, z]) where the default rule's spot fails (judged with tools/run/return_spots.gd --routes).
SPOTS: dict = {}


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
    return [round(w["at"][0] + f[0] * AHEAD + r[0] * RIGHT, 2), round(w["at"][1] + f[1] * AHEAD + r[1] * RIGHT, 2)]


def routes_of(q: str) -> list:
    return [r for r in ROUTES if r[0] == q]


def route_entry(r) -> dict:
    q, sid, kind, to, oid, d, label = r
    e = {"to": to, "dir": d, "label": label, kind: True}
    if kind == "back":
        e["loop"] = True
    return e


def apply(q: str, run: dict) -> dict:
    """run.json of quest `q` with the routes (an existing route of the same direction is replaced); its rail exits name the scene's first doorway for them."""
    nodes = {n["id"]: n for n in run["nodes"]}
    for r in routes_of(q):
        n = nodes[r[1]]
        e = route_entry(r)
        n["next"] = [x for x in n["next"] if x.get("dir") != e["dir"]] + [e]
        ex = n["place"]["rail"]["exits"]
        if e["dir"] not in ex:
            ex[e["dir"]] = ex[n["next"][0]["dir"]]
    return run


def keep_flags(node: dict, hotspots: list) -> list:
    """The keep: flags an ending's default sets (the restart sets them too)."""
    for h in hotspots:
        if h["scene"] == node["id"] and h.get("default"):
            return [f for f in h["on_success"].get("flags_set", []) if f.startswith("keep:")]
    return []


def row(r, node: dict, world: dict, xz: list, flags: list) -> dict:
    q, sid, kind, to, oid, d, label = r
    s = {"route": to}
    f = {"route": to, "energy": ENERGY_MISS}
    if flags:
        s["flags_set"] = list(flags)
        f["flags_set"] = list(flags)
    return {"id": oid, "world": node["world"], "scene": sid, "map": world["map"], "anchor": {"pos": [xz[0], CENTRE_Y, xz[1]]}, "kind": "object", "radius_m": 1.2, "min_px": 88,
            "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
            "look": {"available": "glow", "selected": "ring", "committed": "flash"}, "challenge": None,
            "on_success": s, "on_failure": f, "default": False, "repeatable": True,
            "staging": json.loads(json.dumps(STAGING)), "show": {"archetype": "door"}}


STAGING = {"archetype": "door", "touch": {"w": 2.2, "h": 3.4}, "height_m": 3.0, "width_m": 1.5}  # (a door of the world's own set, drawn where the row stands: ChoiceStaging)


def staging_of(hotspot_id: str):
    """The staging block of a route row (tools/run/apply_staging.py keeps it), None for any other row."""
    return json.loads(json.dumps(STAGING)) if hotspot_id in ids() else None


def show_of(hotspot_id: str):
    """The `show` block of a route row: a door of the world's own set."""
    return {"archetype": "door"} if hotspot_id in ids() else None


def ids() -> set:
    return {r[4] for r in ROUTES}


def add_rows(q: str, hotspots: list, run: dict) -> list:
    """`hotspots`: the quest's rows (dicts) of the scenes in `run`. Returns them with a fresh row per route of those scenes after the scene's last row, before its return
    (an existing row of the same id in that scene is dropped first)."""
    maps = returns_common._maps()
    worlds = {w["id"]: w for w in run["worlds"]}
    nodes = {n["id"]: n for n in run["nodes"]}
    mine = [r for r in routes_of(q) if r[1] in nodes]
    drop = {(r[1], r[4]) for r in mine}
    base = [h for h in hotspots if (h["scene"], h["id"]) not in drop]
    rows = {}
    for r in mine:
        n = nodes[r[1]]
        wd = worlds[n["world"]]
        xz = SPOTS.get(f"{q}/{r[1]}") or default_spot(maps, wd["map"], n)
        rows.setdefault(r[1], []).append(row(r, n, wd, xz, keep_flags(n, base) if r[2] == "restart" else []))
    out = []
    rid = returns_common.DEFS[q]["id"]
    for h in base:
        if h["id"] == rid and h["scene"] in rows:
            out.extend(rows.pop(h["scene"]))
        out.append(h)
    for sid, rs in rows.items():
        out.extend(rs)
    return out


def main(argv: list) -> int:
    check = "--check" in argv
    stale = []
    for q in returns_common.DEFS:
        d = os.path.join(ROOT, "content", "paths", q)
        rp = os.path.join(d, "run.json")
        run = apply(q, json.load(open(rp, encoding="utf-8")))
        text = json.dumps(run, indent=1, ensure_ascii=False) + "\n"
        if open(rp, encoding="utf-8").read() != text:
            stale.append(os.path.relpath(rp, ROOT))
            if not check:
                with open(rp, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
        for fn in sorted(glob.glob(os.path.join(d, "hotspots", "*.json"))):
            doc = json.load(open(fn, encoding="utf-8"))
            new = {**doc, "hotspots": add_rows(q, doc["hotspots"], {"worlds": run["worlds"], "nodes": [n for n in run["nodes"] if n["world"] == doc["world"]]})}
            text = json.dumps(new, indent=1, ensure_ascii=False) + "\n"
            if open(fn, encoding="utf-8").read() != text:
                stale.append(os.path.relpath(fn, ROOT))
                if not check:
                    with open(fn, "w", encoding="utf-8", newline="\n") as fh:
                        fh.write(text)
    if check and stale:
        print("not up to date: " + ", ".join(stale))
        return 1
    print("path routes: " + (("wrote " + ", ".join(stale)) if stale and not check else "up to date"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
