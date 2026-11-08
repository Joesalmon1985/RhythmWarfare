"""The Copper Bar's part of the Doom overlay (docs/doom/scenes/bar.md): the world `doom_bar` (map `doom_bar`, tools/doom/author_bar.py), its one scene `doom_bar`. Imported by tools/run/make_doom.py, which writes it into content/run/doom/ with the Warehouse's.

Geography world (docs/engine/GEOGRAPHY_WORLDS.md, hook H1.6): ONE scene, the world's entry (id = world id, `"geography": true`), its `down` route the stay loop and its three
routes straight to the entry scenes of other geography worlds: ahead doom_booth, left doom_warehouse (the Floor), right doom_lounge (the Chill-out). The guides' `on_success.route` names those worlds; each route move (`rail.routes[dir]`) ends at the
threshold (`rail.exits[dir]`), where the run walks before the boundary, shuts the frame and swaps the stage.
"""
from __future__ import annotations

import json

WORLD = {"id": "doom_bar", "title": "The Copper Bar (Doom worlds)", "map": "doom_bar", "depth": 2, "geography": True, "story": "res://content/run/doom/story_doom_bar.json",
         "blurb": "A brick passage under copper pipes, a drain channel crossed by grates. The booth up the stairs, the Floor to the left, the Chill-out across the water: follow the guide you like."}
SCENE = "doom_bar"


def P(to, role="dancer", style="walk", bars=3, hold=0, via=None, choice=False):
    """One rail place (see make_doom.P): the move to waypoint `to` through the `via` waypoints, then `hold` bars still; `choice` marks a choice viewpoint."""
    d = {"to": to, "role": role, "style": style, "bars": bars}
    if via:
        d["via"] = list(via)
    if hold:
        d["hold_bars"] = hold
    if choice:
        d["choice"] = True
    return d


EXITS = {"up": "wb_booth_door", "left": "wb_floor_door", "right": "wb_chill_door", "down": "wb_ref"}
# The stay rail (round 2, 9 November): the rail climbs one place per block decision (beats 12.5, 28.5, 44.5, not while a leg holds) and the window opens at beat 49. Round 1's
# four places put the FIRST phase's window on the third reveal (the camera walking to the way), so a first visit never chose from the reference viewpoint. Now: out to the first
# grate crossing and back to wb_ref by beat 40.5 (still through the window); in a second phase, out to the way to the Floor and back. The counter reveal is off the rail
# (its waypoint stays, for the shots).
GOOD = [
    P("wb_bridge", bars=2, hold=1.5, via=["wb_v_pass_e"]),
    P("wb_ref", bars=3, hold=8, choice=True, via=["wb_v_pass_e"]),
    P("wb_way", bars=2, hold=1.5, via=["wb_v_jamb"]),
    P("wb_ref", bars=3, hold=8, choice=True, via=["wb_v_jamb"]),
]
BAD = [P("wb_ref_back", "queasy", "walk", 2), P("wb_sw_corner", "queasy", "stagger", 3)]  # a stumble back along the passage's end
ROUTE_MOVES = {
    "up": P("wb_booth_door", "on_stage", bars=4, hold=1, via=["wb_stairs_foot"]),
    "left": P("wb_floor_door", bars=3, hold=1, via=["wb_v_jamb"]),
    "right": P("wb_chill_door", bars=3, hold=1, via=["wb_v_pass_e"]),
    "stumble": P("wb_ref", "recovered", "stagger", bars=3, via=["wb_ref_back", "wb_sw_corner"]),
    "arrive": {**P("wb_ref", bars=3, via=["wb_v_jamb"]), "from": "wb_arrive"},
}


def rail():
    return {"good": json.loads(json.dumps(GOOD)), "bad": json.loads(json.dumps(BAD)), "arrive": "wb_arrive", "exits": dict(EXITS), "routes": json.loads(json.dumps(ROUTE_MOVES)),
            "glances": [{"by": -12, "bars": 2}, {"by": 14, "bars": 2}, {"by": -8, "pitch": 4, "bars": 2}], "strolls": [{"fwd": 0.8, "bars": 3}]}


# id, short name, title, entry, exit_scene, next [(to, dir, label, loop)], music slot
SCENES = [
    ("doom_bar", "bar", "The Copper Bar", True, True,
     [("doom_bar", "down", "Stay in the bar", True), ("doom_booth", "up", "Up the stairs to the booth", False), ("doom_warehouse", "left", "Back to the floor", False),
      ("doom_lounge", "right", "Over the water to the chill-out", False)], 1),
]
GUIDE = {  # hotspot id suffix: (guide thing, route, sprite stem, direction, lamp thing)
    "booth": ("wb_guide_booth", "doom_booth", "booth", "up", "wb_lamp_booth"),
    "floor": ("wb_guide_floor", "doom_warehouse", "floor", "left", "wb_lamp_floor"),
    "chill": ("wb_guide_chill", "doom_lounge", "chill", "right", "wb_lamp_chill"),
}


def staging(thing, stem):
    def st(state, n, motion):
        return [{"thing": thing, "sprite": "guide_%s_%s_%d" % (stem, state, n), "motion": motion}]
    return {"archetype": "figure", "touch": {"w": 1.8, "h": 2.4},
            "states": {"current": st("available", 0, "still"), "other": st("idle", 0, "still"), "touched": st("selected", 0, "still"), "committed": st("committed", 0, "still"), "declined": st("idle", 0, "still")}}


def hotspots(cinematics: dict) -> dict:
    hs = []
    for name, (thing, dest, stem, dr, lamp) in GUIDE.items():
        cname = "doom_bar.stagger_%s" % name
        cinematics[cname] = {"world": "doom_bar", "steps": [{"move": "walk", "to": EXITS[dr], "bars": 2, "role": "queasy", "style": "stagger"}]}
        hs.append({"id": "doom_bar.exit_%s" % name, "world": "doom_bar", "scene": SCENE, "map": "doom_bar", "anchor": {"thing": thing}, "kind": "exit",
                   "radius_m": 1.0, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
                   "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": dest},
                   "on_failure": {"route": dest, "cinematic": cname, "energy": -5}, "default": False, "repeatable": True, "staging": staging(thing, stem),
                   # A7 (ruling 35b): a figure beckons when available, leans in when touched and gestures when committed; the lamp over it brightens with the state
                   "show": {"archetype": "figure", "light": lamp}})
    hs.append({"id": "doom_bar.exit_stay", "world": "doom_bar", "scene": SCENE, "map": "doom_bar", "anchor": {"pos": [0.1, 0.4, -2.1]}, "kind": "exit",
               "radius_m": 1.4, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
               "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": SCENE},
               "on_failure": {"route": SCENE, "energy": -5}, "default": True, "repeatable": True,
               "staging": {"archetype": "none", "touch": {"w": 2.6, "h": 1.4}}, "show": {"archetype": "none"}})
    return {"world": "doom_bar", "hotspots": hs}


def nodes() -> list:
    out = []
    for sid, short, title, entry, exit_scene, nxt, slot in SCENES:
        out.append({"id": sid, "world": "doom_bar", "scene": short, "title": title, "entry": entry, "exit_scene": exit_scene, "role": "dancer",
                    "blurb": WORLD["blurb"] if entry else title,
                    "next": [{"to": t[0], "dir": t[1], "label": t[2], **({"loop": True} if t[3] else {})} for t in nxt],
                    "place": {"waypoint": "wb_ref", "rail": rail()}})
    return out


def music() -> list:
    return [{"id": sid, "arrangement": "warehouse_1", "slot": slot, "alternates": ["warehouse_2", "warehouse_3"], "treatment": "none", "temporary": True} for sid, *_r, slot in SCENES]
