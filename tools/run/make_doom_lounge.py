#!/usr/bin/env python3
"""The Chill-out Lounge's part of the Doom worlds overlay (docs/doom/scenes/lounge.md): the world `doom_lounge`, its scenes, rail, hotspots, cinematics, music and story.

make_doom.write() calls `contribute()` and merges what it returns into content/run/doom/ (worlds, nodes, cinematics, music) and writes the hotspot files and the story file this module
returns. Nothing here touches the Warehouse's data. Run alone, it prints what it would add.

Geography world (docs/engine/GEOGRAPHY_WORLDS.md, hook H1.6): ONE scene, the world's entry (id = world id, `"geography": true`), its `down` route the stay loop and its three
routes straight to the entry scenes of other geography worlds: ahead doom_dock, left doom_bar, right doom_warehouse (the Floor). The guides' `on_success.route` names those worlds; each route move (`rail.routes[dir]`) ends at the
threshold (`rail.exits[dir]`), where the run walks before the boundary, shuts the frame and swaps the stage.

The camera: the stay loop is four places as via polylines with holds round the ring of walkway that circles the sunken pit (west, north, east reveals, then the choice viewpoint `lg_ref`, 8 bars
still); `rail.routes` carries up (ahead, to the Dock), left (the Bar), right (the Floor), stumble, arrive. Waypoints are `lg_*` in content/story/maps/doom_lounge.json (tools/doom/author_lounge.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

WORLD_ID = "doom_lounge"
WORLD = {"id": WORLD_ID, "title": "The Chill-out Lounge (Doom worlds)", "map": "doom_lounge", "depth": 2, "geography": True, "story": "res://content/run/doom/story_doom_lounge.json",
         "blurb": "A mustard octagon round a sunken conversation pit. Ahead the rain street to the Dock, on the left the bar, on the right the blue passage back to the dance floor: follow the guide you like."}
EXITS = {"up": "lg_ahead_door", "left": "lg_bar_door", "right": "lg_floor_door", "down": "lg_ref"}
GUIDE = {  # hotspot id suffix: (guide thing, route scene, sprite stem, direction)
    "dock": ("lg_guide_dock", "doom_dock", "dock", "up"),
    "bar": ("lg_guide_bar", "doom_bar", "bar", "left"),
    "floor": ("lg_guide_floor", "doom_warehouse", "floor", "right"),
}
# id, short name, title, entry, exit_scene, next [(to, dir, label, loop)], music slot
SCENES = [
    ("doom_lounge", "lounge", "The Chill-out Lounge", True, True,
     [("doom_lounge", "down", "Stay in the lounge", True), ("doom_dock", "up", "Ahead: the rain street to the Dock", False), ("doom_bar", "left", "Left: into the bar", False),
      ("doom_warehouse", "right", "Right: back to the dance floor", False)], 3),
]


def rail() -> dict:
    import make_doom as md
    P = md.P
    good = [
        P("lg_west", bars=4, hold=2, via=["lg_v_ssw", "lg_v_wsw"]),
        P("lg_north", bars=4, hold=2, via=["lg_v_wnw", "lg_v_nnw"]),
        P("lg_east", bars=4, hold=2, via=["lg_v_nne", "lg_v_ene"]),
        P("lg_ref", bars=4, hold=8, choice=True, via=["lg_v_ese", "lg_v_sse"]),
    ]
    bad = [P("lg_ref_back", "queasy", "walk", 2), P("lg_sw_corner", "queasy", "stagger", 3)]
    routes = {
        "up": P("lg_ahead_door", bars=5, hold=1, via=["lg_v_sse", "lg_v_ese", "lg_v_ene", "lg_v_nne", "lg_v_n"]),
        "left": P("lg_bar_door", bars=4, hold=1, via=["lg_v_ssw", "lg_v_wsw", "lg_v_wnw"]),
        "right": P("lg_floor_door", bars=4, hold=1, via=["lg_v_sse", "lg_v_ese", "lg_v_ene"]),
        "stumble": P("lg_ref", "recovered", "stagger", bars=3, via=["lg_ref_back", "lg_sw_corner"]),
        "arrive": {**P("lg_ref", bars=4, via=["lg_v_ene", "lg_v_ese", "lg_v_sse"]), "from": "lg_arrive"},
    }
    r = {"good": good, "bad": bad, "arrive": "lg_arrive", "exits": dict(EXITS), "routes": routes}
    r["glances"] = [{"by": -12, "bars": 2}, {"by": 14, "bars": 2}, {"by": -8, "pitch": 4, "bars": 2}]  # restrained: the pads and the guides stay in view
    r["strolls"] = [{"fwd": 0.8, "bars": 3}]
    return json.loads(json.dumps(r))


def staging(thing: str, stem: str) -> dict:
    """The choice layer's staging of a guide (src/run/choice_staging.gd, archetype figure): the billboard's sprite and motion per state, no ring and no lamp."""
    def st(state, n, motion):
        return [{"thing": thing, "sprite": "guide_%s_%s_%d" % (stem, state, n), "motion": motion}]
    return {"archetype": "figure", "touch": {"w": 1.8, "h": 2.4},
            "states": {"current": st("available", 0, "still"), "other": st("idle", 0, "still"), "touched": st("selected", 0, "still"), "committed": st("committed", 0, "still"), "declined": st("idle", 0, "still")}}


def hotspots(cin: dict) -> dict:
    hs = []
    for name, (thing, dest, stem, dr) in GUIDE.items():
        cname = "%s.stagger_%s" % (WORLD_ID, name)
        cin[cname] = {"world": WORLD_ID, "steps": [{"move": "walk", "to": EXITS[dr], "bars": 2, "role": "queasy", "style": "stagger"}]}
        hs.append({"id": "%s.exit_%s" % (WORLD_ID, name), "world": WORLD_ID, "scene": WORLD_ID, "map": "doom_lounge", "anchor": {"thing": thing}, "kind": "exit",
                   "radius_m": 1.0, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
                   "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": dest},
                   "on_failure": {"route": dest, "cinematic": cname, "energy": -5}, "default": False, "repeatable": True, "staging": staging(thing, stem)})
    hs.append({"id": "%s.exit_stay" % WORLD_ID, "world": WORLD_ID, "scene": WORLD_ID, "map": "doom_lounge", "anchor": {"pos": [0.0, 0.5, 4.2]}, "kind": "exit",
               "radius_m": 1.4, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
               "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": WORLD_ID},
               "on_failure": {"route": WORLD_ID, "energy": -5}, "default": True, "repeatable": True,
               "staging": {"archetype": "none", "touch": {"w": 2.6, "h": 1.4}}})  # (the foreground, the near sofa: no door and no lamp)
    return {"world": WORLD_ID, "hotspots": hs}


def story() -> dict:
    """The world's StoryData: the Night One chapter's blocks and music with an empty cast (the painting's lounge has only its three guides) and the legacy camera moves taken out."""
    root = HERE.parent.parent
    ch = json.load(open(root / "content" / "story" / "night_one.json", encoding="utf-8"))
    ch["id"], ch["title"] = WORLD_ID, "Doom Lounge"
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


def contribute() -> dict:
    """What make_doom.write() merges: worlds, nodes, cinematics, music rows, hotspot documents by file stem, and the story document."""
    cin: dict = {}
    nodes = []
    for sid, short, title, entry, exit_scene, nxt, slot in SCENES:
        nodes.append({"id": sid, "world": WORLD_ID, "scene": short, "title": title, "entry": entry, "exit_scene": exit_scene, "role": "dancer", "blurb": WORLD["blurb"] if entry else title,
                      "next": [{"to": t[0], "dir": t[1], "label": t[2], **({"loop": True} if t[3] else {})} for t in nxt], "place": {"waypoint": "lg_ref", "rail": rail()}})
    hot = hotspots(cin)
    music = [{"id": sid, "arrangement": "warehouse_1", "slot": slot, "alternates": ["warehouse_2", "warehouse_3"], "treatment": "none", "temporary": False} for sid, *_r, slot in SCENES]
    return {"worlds": [WORLD], "nodes": nodes, "cinematics": cin, "music": music, "hotspots": {WORLD_ID: hot}, "story": {"story_doom_lounge": story()}}


if __name__ == "__main__":
    c = contribute()
    print("lounge: %d scenes, %d hotspots, %d cinematics" % (len(c["nodes"]), len(c["hotspots"][WORLD_ID]["hotspots"]), len(c["cinematics"])))
