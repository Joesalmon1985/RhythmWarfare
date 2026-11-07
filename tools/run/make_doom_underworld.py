"""The Underworld's part of the Doom worlds overlay (docs/doom/scenes/underworld.md): the world `doom_underworld`, its scenes, its hotspots, its story. Called from tools/run/make_doom.py
(`write`), which merges it into content/run/doom/run.json, music.json and hotspots/doom_underworld.json.

Geography world (docs/engine/GEOGRAPHY_WORLDS.md, hook H1.6): ONE scene, the world's entry (id = world id, `"geography": true`), its `down` route the stay loop and its three
routes straight to the entry scenes of other geography worlds: ahead doom_mothership, left doom_warehouse (the Floor), right doom_dock. The guides' `on_success.route` names those worlds; each route move (`rail.routes[dir]`) ends at the
threshold (`rail.exits[dir]`), where the run walks before the boundary, shuts the frame and swaps the stage.
"""
from __future__ import annotations

import json
from pathlib import Path

WORLD_ID = "doom_underworld"
ROOT = Path(__file__).resolve().parent.parent.parent
WORLD = {"id": WORLD_ID, "title": "The Underworld (Doom worlds)", "map": "doom_underworld", "depth": 2, "geography": True, "story": "res://content/run/doom/story_doom_underworld.json",
         "blurb": "A black basalt plateau over a lava abyss. The ledge ahead climbs to the Mothership, the cave on the left leads to the Dance Floor, the stair on the right to the Dock: follow the guide you like."}
EXITS = {"up": "uw_gate", "left": "uw_cave_in", "right": "uw_shelf_end", "down": "uw_ref"}
DIR_OF = {"mothership": "up", "floor": "left", "dock": "right"}
GUIDE = {  # name: (guide thing, route node, sprite stem)
    "mothership": ("uw_guide_mothership", "doom_mothership", "mothership"),
    "floor": ("uw_guide_floor", "doom_warehouse", "floor"),
    "dock": ("uw_guide_dock", "doom_dock", "dock"),
}


def _rail(P):
    good = [
        P("uw_ledge_view", bars=4, hold=2, via=["uw_v_s1"]),
        P("uw_cave_view", bars=3, hold=2, via=["uw_v_s2"]),
        P("uw_stair_view", bars=4, hold=2, via=["uw_v_s1"]),
        P("uw_ref", bars=4, hold=8, choice=True, via=["uw_v_s1"]),
    ]
    bad = [P("uw_ref_back", "queasy", "walk", 2), P("uw_sw_corner", "queasy", "stagger", 3)]
    routes = {
        "up": P("uw_gate", "dancer", bars=5, hold=1, via=["uw_v_a1", "uw_v_a2", "uw_v_a3", "uw_v_a4"]),
        "left": P("uw_cave_in", "dancer", bars=4, hold=1, via=["uw_v_l1", "uw_v_l2", "uw_v_l3"]),
        "right": P("uw_shelf_end", "dancer", bars=5, hold=1, via=["uw_v_r1", "uw_v_r2", "uw_v_r3", "uw_v_r4"]),
        "stumble": P("uw_ref", "recovered", "stagger", bars=3, via=["uw_ref_back", "uw_sw_corner"]),
        "arrive": {**P("uw_ref", bars=3), "from": "uw_arrive"},
    }
    return {"good": good, "bad": bad, "arrive": "uw_arrive", "exits": dict(EXITS), "routes": routes}


# id, short name, title, exit_scene, next [(to, dir, label, loop)], music slot
SCENES = [
    ("doom_underworld", "underworld", "The Underworld", True,
     [("doom_underworld", "down", "Stay on the plateau", True), ("doom_mothership", "up", "Up the ledge to the Mothership", False),
      ("doom_warehouse", "left", "Into the cave to the Dance Floor", False), ("doom_dock", "right", "Up the stair to the Dock", False)], 0),
]


def _staging(thing, stem):
    def st(state, n, motion):
        return [{"thing": thing, "sprite": "guide_%s_%s_%d" % (stem, state, n), "motion": motion}]
    return {"archetype": "figure", "touch": {"w": 1.8, "h": 2.4},
            "states": {"current": st("available", 0, "still"), "other": st("idle", 0, "still"), "touched": st("selected", 0, "still"), "committed": st("committed", 0, "still"), "declined": st("idle", 0, "still")}}


def _hotspots(cinematics):
    hs = []
    for name, (thing, dest, stem) in GUIDE.items():
        cname = "doom_underworld.stagger_%s" % name
        cinematics[cname] = {"world": "doom_underworld", "steps": [{"move": "walk", "to": EXITS[DIR_OF[name]], "bars": 2, "role": "queasy", "style": "stagger"}]}
        hs.append({"id": "doom_underworld.exit_%s" % name, "world": "doom_underworld", "scene": "doom_underworld", "map": "doom_underworld", "anchor": {"thing": thing}, "kind": "exit",
                   "radius_m": 1.0, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
                   "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": dest},
                   "on_failure": {"route": dest, "cinematic": cname, "energy": -5}, "default": False, "repeatable": True, "staging": _staging(thing, stem),
                   "show": {"archetype": "figure"}})
    hs.append({"id": "doom_underworld.exit_stay", "world": "doom_underworld", "scene": "doom_underworld", "map": "doom_underworld", "anchor": {"pos": [0.0, 0.2, -3.4]}, "kind": "exit",
               "radius_m": 1.4, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
               "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": "doom_underworld"},
               "on_failure": {"route": "doom_underworld", "energy": -5}, "default": True, "repeatable": True,
               "staging": {"archetype": "none", "touch": {"w": 2.6, "h": 1.4}}, "show": {"archetype": "none"}})
    return {"world": "doom_underworld", "hotspots": hs}


def _story():
    """The world's StoryData: the Night One chapter's blocks and music with an empty cast (the painting's abyss has only its three guides) and the legacy camera moves taken out."""
    ch = json.load(open(ROOT / "content" / "story" / "night_one.json", encoding="utf-8"))
    ch["id"], ch["title"] = "doom_underworld", "Doom Underworld"
    ch["art"] = "night_one"
    for b in ch["blocks"]:
        b["events"] = [e for e in b.get("events", []) if not str(e.get("action", "")).startswith("player_") and str(e.get("action", "")) != "doors_open"]
    for dec in ch["decisions"]:
        for k in ("good", "bad"):
            dec[k] = [e for e in dec.get(k, []) if not (isinstance(e, dict) and str(e.get("action", "")).startswith("player_"))]
    for e in ch["endings"].values():
        e["journey"] = []
    ch["actors"], ch["silhouettes"] = [], []
    ch["groups"] = {k: [] for k in ch["groups"]}
    return ch


def add(P, worlds, nodes, cinematics, music, hotspot_files):
    """Appends the Underworld's world, nodes, cinematics, music entries and hotspot file to the overlay's lists (P: make_doom.P, the rail place builder) and writes its story file."""
    worlds.append(WORLD)
    for sid, short, title, exit_scene, nxt, slot in SCENES:
        r = _rail(P)
        r["glances"] = [{"by": -10, "bars": 2}, {"by": 12, "bars": 2}, {"by": -6, "pitch": 3, "bars": 2}]  # restrained: the pads and the guides stay in view
        r["strolls"] = [{"fwd": 0.6, "bars": 3}]
        nodes.append({"id": sid, "world": "doom_underworld", "scene": short, "title": title, "entry": sid == "doom_underworld", "exit_scene": exit_scene, "role": "dancer",
                      "blurb": WORLD["blurb"] if sid == "doom_underworld" else title,
                      "next": [{"to": t[0], "dir": t[1], "label": t[2], **({"loop": True} if t[3] else {})} for t in nxt],
                      "place": {"waypoint": "uw_ref", "rail": r}})
        music.append({"id": sid, "arrangement": "warehouse_1", "slot": slot, "alternates": ["warehouse_2", "warehouse_3"], "treatment": "none", "temporary": False})
    hotspot_files["doom_underworld"] = _hotspots(cinematics)
    out = ROOT / "content" / "run" / "doom"
    out.mkdir(parents=True, exist_ok=True)
    (out / "story_doom_underworld.json").write_text(json.dumps(_story(), indent=1) + "\n", encoding="utf-8", newline="\n")
