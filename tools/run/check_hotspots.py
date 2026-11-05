#!/usr/bin/env python3
"""Checks the run's hotspot data (content/run/hotspots/<world>.json) against the contract of section 2 of docs/VISUAL_RHYTHM_ADVENTURE_PLAN.md, and that every scene,
route, secret and the Bassment are reachable through hotspots alone. Pure Python, no Godot:

    python3 tools/run/check_hotspots.py            # all worlds; exit code 1 on any error
    python3 tools/run/check_hotspots.py warehouse  # one world's rules (reachability still walks the whole run)
    python3 tools/run/check_hotspots.py --path gospel   # a path's run (content/paths/gospel): the same rules, with the path's relaxations (several entries and exits, endings)

Rules (errors): every hotspot has the contract's fields; its world, scene and map agree with run.json; its anchor exists in the map (thing, waypoint, actor with a home, or a 3-float
pos); kind and looks are in the vocabularies; every route is a route of the scene (its `next`) or a Bassment passage; every cinematic names an entry of run.json `cinematics` whose
steps go to waypoints of the scene's map (look_at: a waypoint, thing or actor); every scene has 2 to 4 hotspots available at any time (over every combination of the flags its hotspots
read, with once-only hotspots present or already used: the minimum counts without the once-only ones, the maximum with them all), exactly one default exit and it is the scene's first
route, one exit hotspot per route anchored to that route's doorway; a failure outcome is never a dead end (a route, or a state change: flags, energy, music or a cinematic) and differs
from the success outcome. Reachability: from the start scene, following every route of every outcome (success and failure) and the default exits, every scene is reached, every route
of every scene is taken by some exit hotspot, every Bassment hotspot target is a passage, and every hotspot (secrets included) can become available: its flags are set by some outcome
of a reachable hotspot. A route "path:<id>" (a portal of the Warehouse) is accepted for a secret that pulses and is never the default, repeatable, whose failure has no route and costs energy; the path's run.json must exist (a warning
while it does not: the game leaves the portal out of play). In a path, an ending scene (`"ending": "<name>"`) has the one route "run:warehouse" and its default hotspot sets keep:path_<id>_<name>; reachability
needs every scene reachable from the start, every ending reached and its way back taken; there is no Bassment. Warnings: outcomes whose route differs from the scene's default route when the chart packs differ (the route lock of docs/CONTINUOUS_RUN.md decides the
chart at beat 60.5).
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATH_ID = ""  # set by --path
KNOWN_PATHS = {"gospel", "squadron", "ember"}  # the three portals of the Warehouse; any folder under content/paths is one too
KINDS = {"exit", "object", "character", "feature", "encounter", "secret"}
LOOKS = {"glow", "pulse", "beckon", "flicker", "open", "crack"}
ROLES = {"dancer", "on_stage", "dj", "queasy", "sick", "recovered"}
STYLES = {"walk", "stagger", "run", "climb", "carried"}
MUSIC = {"variation", "dip"}
FIELDS = ["id", "world", "scene", "map", "anchor", "kind", "radius_m", "min_px", "available", "look", "challenge", "on_success", "on_failure", "default", "repeatable"]
CHAPTER = {"night_one": "night_one", "mothership": "mothership", "underworld": "underworld", "hospital": "hospital", "mental_hospital": "mental_hospital"}


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def run_json_path():
    return ROOT / "content/paths" / PATH_ID / "run.json" if PATH_ID else ROOT / "content/run/run.json"


def music_json_path():
    return ROOT / "content/paths" / PATH_ID / "music.json" if PATH_ID else ROOT / "content/story/music.json"


def hotspots_dir():
    return ROOT / "content/paths" / PATH_ID / "hotspots" if PATH_ID else ROOT / "content/run/hotspots"


def path_exists(pid):
    return (ROOT / "content/paths" / pid / "run.json").exists() and (ROOT / "content/paths" / pid / "music.json").exists()


class Ctx:
    def chart_pack(self, n):
        """The chart pack of block 0 of a scene: its own `chart`, else the pack of the first section of its arrangement's slot (the base arrangement, not an alternate)."""
        if "chart" in n:
            return n["chart"]
        arr = load(ROOT / f"content/music/arrangements/{n['arrangement']}.json")
        phase_bars = int(self.run.get("timing", {}).get("phase_beats", 64)) // 4
        start = (int(n.get("slot", 0)) * phase_bars) % int(arr["bars"])
        bar = 0
        for sec in arr["sections"]:
            if bar >= start:
                return sec.get("pack", "")
            bar += int(sec["bars"])
        return ""

    def __init__(self):
        self.run = load(run_json_path())
        self.nodes = {n["id"]: n for n in self.run["nodes"]}
        self.worlds = {w["id"]: w for w in self.run["worlds"]}
        self.cin = self.run.get("cinematics", {})
        self.passages = set() if PATH_ID else set(load(ROOT / "content/trial/passages.json")["passages"])
        music = load(music_json_path())
        self.pack = {n["id"]: self.chart_pack(n) for n in music["nodes"]}
        self.maps = {}
        self.actors = {}
        for m in sorted({w["map"] for w in self.run["worlds"]} | set(CHAPTER)):
            CHAPTER.setdefault(m, m)
            d = load(ROOT / f"content/story/maps/{m}.json")
            self.maps[m] = {"things": {t["id"] for t in d["things"]}, "wps": {w["id"] for w in d["waypoints"]}, "homes": {h["actor"] for h in d["homes"]}}
            self.actors[m] = {a["id"] for a in load(ROOT / f"content/story/{CHAPTER[m]}.json")["actors"]}


def outcome_keys_ok(o, where, errs):
    for k in o:
        if k not in ("route", "flags_set", "cinematic", "energy", "music", "pieces"):
            errs.append(f"{where}: unknown outcome field {k}")
    if "energy" in o and not (isinstance(o["energy"], int) and -20 <= o["energy"] <= 20):
        errs.append(f"{where}: energy must be an int in -20..20")
    if "music" in o and o["music"] not in MUSIC:
        errs.append(f"{where}: music {o['music']} not in {sorted(MUSIC)}")
    for f in o.get("flags_set", []):
        if not isinstance(f, str) or not f:
            errs.append(f"{where}: bad flag {f!r}")


def check_step(step, mapname, ctx, where, errs):
    mp = ctx.maps[mapname]
    if step.get("move") not in ("walk", "place"):
        errs.append(f"{where}: move must be walk or place")
    if step.get("to") not in mp["wps"]:
        errs.append(f"{where}: waypoint {step.get('to')} is not in map {mapname}")
    if step.get("role", "dancer") not in ROLES:
        errs.append(f"{where}: role {step.get('role')}")
    if step.get("style", "walk") not in STYLES:
        errs.append(f"{where}: style {step.get('style')}")
    if not (isinstance(step.get("bars"), int) and 2 <= step["bars"] <= 4):
        errs.append(f"{where}: bars is 2 to 4")
    la = step.get("look_at")
    if la and la not in mp["wps"] and la not in mp["things"] and la not in ctx.actors[mapname]:
        errs.append(f"{where}: look_at {la} is no waypoint, thing or actor of {mapname}")


def check_cin(c, mapname, ctx, where, errs):
    if c is None:
        return
    if isinstance(c, str):
        e = ctx.cin.get(c)
        if e is None:
            errs.append(f"{where}: cinematic {c} is not in run.json cinematics")
            return
        if not e["steps"]:
            errs.append(f"{where}: cinematic {c} has no steps")
        for i, s in enumerate(e["steps"]):
            check_step(s, mapname, ctx, f"{where} {c}[{i}]", errs)
    else:
        check_step(c, mapname, ctx, where + " (inline)", errs)


def check_portal(h, which, route, errs):
    """A portal (docs/THREE_PATHS_AND_FACES_PLAN.md 3.3): only on_success may lead into a path, the main run only, a secret that pulses, never the default, repeatable, failing without a route for a little energy."""
    hid = h["id"]
    pid = route[len("path:"):]
    if PATH_ID:
        errs.append(f"{hid}: a path does not lead into another path ({route})")
    if which != "on_success":
        errs.append(f"{hid}: only on_success may lead into a path")
    if not pid.isidentifier():
        errs.append(f"{hid}: {route} needs a path id")
    if h["kind"] != "secret" or h["look"].get("available") != "pulse":
        errs.append(f"{hid}: a portal is a secret with look.available pulse")
    if h["default"]:
        errs.append(f"{hid}: a portal is never the default")
    if not h["repeatable"]:
        errs.append(f"{hid}: a portal is repeatable")
    f = h["on_failure"]
    if f.get("route") or not (isinstance(f.get("energy"), int) and f["energy"] < 0):
        errs.append(f"{hid}: a portal that fails flickers out: no route, an energy cost")


def check_hotspot(h, ctx, errs):
    hid = h.get("id", "?")
    for f in FIELDS:
        if f not in h:
            errs.append(f"{hid}: missing field {f}")
    if any(f not in h for f in FIELDS):
        return
    node = ctx.nodes.get(h["scene"])
    if node is None:
        errs.append(f"{hid}: scene {h['scene']} is not in run.json")
        return
    if h["world"] != node["world"] or h["map"] != ctx.worlds[node["world"]]["map"]:
        errs.append(f"{hid}: world/map disagree with the scene")
        return
    if not hid.startswith(h["scene"] + "."):
        errs.append(f"{hid}: id must start with the scene id")
    mp = ctx.maps[h["map"]]
    a = h["anchor"]
    if not isinstance(a, dict) or len(a) != 1:
        errs.append(f"{hid}: anchor is one of thing, waypoint, actor, pos")
    else:
        (k, v), = a.items()
        if k == "thing" and v not in mp["things"]:
            errs.append(f"{hid}: thing {v} is not in map {h['map']}")
        elif k == "waypoint" and v not in mp["wps"]:
            errs.append(f"{hid}: waypoint {v} is not in map {h['map']}")
        elif k == "actor" and (v not in ctx.actors[h["map"]] or v not in mp["homes"]):
            errs.append(f"{hid}: actor {v} has no home in map {h['map']}")
        elif k == "pos" and not (isinstance(v, list) and len(v) == 3 and all(isinstance(x, (int, float)) for x in v)):
            errs.append(f"{hid}: pos is [x, y, z]")
        elif k not in ("thing", "waypoint", "actor", "pos"):
            errs.append(f"{hid}: anchor kind {k}")
    if h["kind"] not in KINDS:
        errs.append(f"{hid}: kind {h['kind']}")
    if h["look"].get("available") not in LOOKS or h["look"].get("selected") != "ring" or h["look"].get("committed") != "flash":
        errs.append(f"{hid}: look {h['look']}")
    if h["min_px"] < 72 or not (0.3 <= h["radius_m"] <= 3.0):
        errs.append(f"{hid}: radius_m 0.3 to 3, min_px at least 72")
    av = h["available"]
    if set(av) != {"flags_all", "flags_none", "energy_min", "once"}:
        errs.append(f"{hid}: available fields {sorted(av)}")
    if set(av.get("flags_all", [])) & set(av.get("flags_none", [])):
        errs.append(f"{hid}: a flag both required and forbidden")
    for which in ("on_success", "on_failure"):
        o = h[which]
        outcome_keys_ok(o, f"{hid} {which}", errs)
        r = o.get("route")
        if r and r.startswith("path:"):
            check_portal(h, which, r, errs)
        elif r and r not in [n["to"] for n in node["next"]] and r not in ctx.passages:
            errs.append(f"{hid} {which}: route {r} is neither a route of {h['scene']} nor a Bassment passage")
        check_cin(o.get("cinematic"), h["map"], ctx, f"{hid} {which}", errs)
    if "cinematic" in h:
        check_cin(h["cinematic"], h["map"], ctx, f"{hid} hook", errs)
    s, f = h["on_success"], h["on_failure"]
    if not f or not (f.get("route") or f.get("flags_set") or f.get("energy") or f.get("music") or f.get("cinematic")):
        errs.append(f"{hid}: failure is a dead end (no route, no state change)")
    if f == s:
        errs.append(f"{hid}: failure equals success")
    if h["kind"] == "exit":
        if not s.get("route"):
            errs.append(f"{hid}: an exit leads somewhere")
    elif not (s.get("route") or s.get("flags_set") or s.get("energy") or s.get("music") or s.get("cinematic")):
        errs.append(f"{hid}: success changes nothing")
    if h["challenge"] is not None:
        c = h["challenge"]
        if c.get("family") not in ("drums", "bass") or c.get("tier") not in (1, 2, 3, 4):
            errs.append(f"{hid}: challenge {c}")


def counts(hs):
    """Min and max hotspots available at once, over every combination of the flags the scene's hotspots read and of the once-only ones used or not."""
    flags = sorted({f for h in hs for f in h["available"]["flags_all"] + h["available"]["flags_none"]})
    lo, hi = 99, 0
    for bits in itertools.product([False, True], repeat=len(flags)):
        on = {f for f, b in zip(flags, bits) if b}
        for energy in (0, 100):
            vis = [h for h in hs if set(h["available"]["flags_all"]) <= on and not (set(h["available"]["flags_none"]) & on) and h["available"]["energy_min"] <= energy]
            nonce = [h for h in vis if not h["available"]["once"]]
            lo = min(lo, len(nonce))
            hi = max(hi, len(vis))
    return lo, hi


def check_scene(sid, hs, ctx, errs, warns):
    node = ctx.nodes[sid]
    if not hs:
        errs.append(f"{sid}: no hotspots")
        return
    lo, hi = counts(hs)
    if lo < 2 or hi > 4:
        errs.append(f"{sid}: {lo} to {hi} hotspots available (must stay 2 to 4)")
    exits = [h for h in hs if h["kind"] == "exit"]
    defaults = [h for h in exits if h["default"]]
    if len(defaults) != 1:
        errs.append(f"{sid}: {len(defaults)} default exits (exactly one)")
    elif defaults[0]["on_success"].get("route") != node["next"][0]["to"]:
        errs.append(f"{sid}: the default exit must lead to the scene's first route {node['next'][0]['to']}")
    if any(h["default"] for h in hs if h["kind"] != "exit"):
        errs.append(f"{sid}: only an exit can be the default")
    for h in exits:
        if h["available"] != {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False}:
            errs.append(f"{h['id']}: an exit is always available")
    if node.get("ending"):  # an ending's default exit marks the ending reached and leads back to the Warehouse
        flag = f"keep:path_{PATH_ID}_{node['ending']}"
        if [r["to"] for r in node["next"]] != ["run:warehouse"]:
            errs.append(f"{sid}: an ending has the one route run:warehouse")
        for h in defaults:
            if flag not in h["on_success"].get("flags_set", []):
                errs.append(f"{h['id']}: the default exit of an ending sets {flag}")
    ex = node["place"]["rail"]["exits"]
    for r in node["next"]:
        mine = [h for h in exits if h["on_success"].get("route") == r["to"]]
        if PATH_ID and not mine:  # a path's route may be reached by a touch (a feature, an object, a person) instead of an exit of its own
            if not any(h[w].get("route") == r["to"] for h in hs for w in ("on_success", "on_failure")):
                errs.append(f"{sid}: no hotspot leads to route {r['to']}")
            continue
        if len(mine) != 1:
            errs.append(f"{sid}: {len(mine)} exit hotspots for route {r['to']} (one)")
            continue
        h = mine[0]
        wp = ex[r["dir"]]
        a = h["anchor"]
        ok = a == {"waypoint": wp} or ("thing" in a)  # a thing placed at the doorway (the crack) may stand in for the waypoint
        if not ok:
            errs.append(f"{h['id']}: exit anchored to {a}, the doorway is waypoint {wp}")
    for h in hs:
        for which in ("on_success", "on_failure"):
            r = h[which].get("route")
            if r and r in ctx.nodes and r != node["next"][0]["to"] and ctx.pack.get(r) != ctx.pack.get(node["next"][0]["to"]) and h["kind"] != "exit":
                warns.append(f"{h['id']} {which}: route {r} ({ctx.pack.get(r)}) differs from the default route's chart pack ({ctx.pack.get(node['next'][0]['to'])})")
    return lo, hi


def reachability(allh, ctx, errs):
    by_scene = {}
    for h in allh:
        by_scene.setdefault(h["scene"], []).append(h)
    start = ctx.run["start_node"]
    seen_scenes, flags = {start}, set()
    taken_routes = set()
    reached_h = set()
    trial = False
    portals = set()
    endings = set()
    changed = True
    while changed:
        changed = False
        for sid in list(seen_scenes):
            for h in by_scene.get(sid, []):
                av = h["available"]
                if not set(av["flags_all"]) <= flags:
                    continue
                if h["id"] not in reached_h:
                    reached_h.add(h["id"])
                    changed = True
                for which in ("on_success", "on_failure"):
                    o = h[which]
                    for f in o.get("flags_set", []):
                        if f not in flags:
                            flags.add(f)
                            changed = True
                    r = o.get("route")
                    if r:
                        if r.startswith("path:"):
                            portals.add(r[len("path:"):])
                        elif r.startswith("run:"):
                            taken_routes.add((sid, r))
                            endings.add(sid)
                        elif r in ctx.nodes:
                            taken_routes.add((sid, r))
                            if r not in seen_scenes:
                                seen_scenes.add(r)
                                changed = True
                        elif r in ctx.passages:
                            if not trial:
                                trial = True
                                changed = True
                            if start not in seen_scenes:
                                seen_scenes.add(start)
                                changed = True
    for sid in ctx.nodes:
        if sid not in seen_scenes:
            errs.append(f"unreachable scene {sid}")
    for sid, n in ctx.nodes.items():
        for r in n["next"]:
            if (sid, r["to"]) not in taken_routes:
                errs.append(f"route {sid} -> {r['to']} is not taken by any reachable hotspot outcome")
    for h in allh:
        if h["id"] not in reached_h:
            errs.append(f"hotspot {h['id']} can never become available (its flags_all {h['available']['flags_all']} are never set)")
    if PATH_ID:
        want = {i for i, n in ctx.nodes.items() if n.get("ending")}
        for e in sorted(want - endings):
            errs.append(f"the ending {e} is never left by its way back to the Warehouse")
        if not want:
            errs.append("the path has no ending scene")
    elif not trial:
        errs.append("the Bassment (a trial passage route) is not reachable")
    return len(seen_scenes), len(taken_routes), len(flags), portals, endings


def main(argv):
    ctx = Ctx()
    errs, warns = [], []
    want = set(argv[1:])
    allh = []
    files = sorted(hotspots_dir().glob("*.json"))
    worlds_found = set()
    for p in files:
        d = load(p)
        w = d.get("world")
        worlds_found.add(w)
        if w != p.stem or w not in ctx.worlds:
            errs.append(f"{p.name}: world {w}")
            continue
        for h in d.get("hotspots", []):
            allh.append(h)
    ids = [h.get("id") for h in allh]
    for i in {x for x in ids if ids.count(x) > 1}:
        errs.append(f"duplicate hotspot id {i}")
    for w in ctx.worlds:
        if w not in worlds_found:
            errs.append(f"no hotspot file for world {w}")
    per_world = {}
    for h in allh:
        if want and h.get("world") not in want:
            continue
        check_hotspot(h, ctx, errs)
    rows = []
    for sid in ctx.nodes:
        hs = [h for h in allh if h.get("scene") == sid]
        if want and ctx.nodes[sid]["world"] not in want:
            continue
        r = check_scene(sid, hs, ctx, errs, warns)
        if r:
            rows.append((ctx.nodes[sid]["world"], sid, len(hs), r))
            per_world.setdefault(ctx.nodes[sid]["world"], []).append(len(hs))
    ns, nr, nf, portals, endings = reachability(allh, ctx, errs)
    for pid in sorted(portals):
        if not path_exists(pid):
            warns.append(f"portal into path '{pid}': content/paths/{pid}/run.json does not exist yet (the game leaves the portal out of play)")
    # unused cinematics are a sign of drift
    used = set()
    for h in allh:
        for which in ("on_success", "on_failure"):
            c = h.get(which, {}).get("cinematic")
            if isinstance(c, str):
                used.add(c)
    for c in ctx.cin:
        if c not in used:
            warns.append(f"cinematic {c} is not used by any outcome")
    for w, sid, n, (lo, hi) in rows:
        print(f"  {w:14} {sid:22} {n} hotspots (available at once: {lo} to {hi})")
    for w in ctx.worlds:
        if w in per_world:
            print(f"{w}: {sum(per_world[w])} hotspots in {len(per_world[w])} scenes")
    if PATH_ID:
        print(f"reachability: {ns}/{len(ctx.nodes)} scenes, {nr} routes taken, {nf} flags settable, endings {', '.join(ctx.nodes[e]['ending'] for e in sorted(endings)) or 'none'} left by run:warehouse")
    else:
        print(f"reachability: {ns}/{len(ctx.nodes)} scenes, {nr} routes taken, {nf} flags settable, Bassment via passage; portals into paths: {', '.join(sorted(portals)) or 'none'}")
    print(f"{len(allh)} hotspots, {len(ctx.cin)} cinematics")
    for w in warns:
        print("warning:", w)
    for e in errs:
        print("ERROR:", e)
    print("check_hotspots: %d errors, %d warnings" % (len(errs), len(warns)))
    return 1 if errs else 0


if __name__ == "__main__":
    argv = list(sys.argv)
    if "--path" in argv:
        i = argv.index("--path")
        PATH_ID = argv[i + 1]
        del argv[i:i + 2]
    sys.exit(main(argv))
