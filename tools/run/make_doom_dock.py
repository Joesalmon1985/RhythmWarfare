"""The Loading Dock's part of the Doom worlds overlay (docs/doom/scenes/dock.md): the world `doom_dock`, its scenes, its hotspots. Called from tools/run/make_doom.py (`write`), which merges it
into content/run/doom/run.json, music.json and hotspots/doom_dock.json.

Routing (docs/briefs/DOOM_WAVE2_BRIEF.md): from the Dock ahead = Mothership, left = Floor (the club door), right = Underworld (the furnace). Those scenes are not built on this branch, so under the flag the three
are STAND-INS of this world (doom_dock.mothership, .floor, .underworld: the same map and the dock's own rail), each leading on to `doom_dock.return`, the world's exit scene, whose two routes loop back to
the dock. The data the real cut needs is already here: the threshold waypoint is the `to` of each route move (`dk_moth`, `dk_floor_door`, `dk_under`), the doorway is `rail.exits[dir]`, the route labels
are the destination names. When the engine's geography hook (H1.6) lands, the stand-ins are deleted by a change here (SCENES) and the guides' `on_success.route` names the real worlds.
"""
from __future__ import annotations

WORLD = {"id": "doom_dock", "title": "The Loading Dock (Doom worlds)", "map": "doom_dock", "depth": 2, "story": "res://content/run/doom/story_doom_dock.json",
         "blurb": "The club's loading dock in the rain. The street to the Mothership ahead, the club door and the dance floor on the left, the furnace and the Underworld on the right: follow the guide you like."}
EXITS = {"up": "dk_moth", "left": "dk_floor_door", "right": "dk_under", "down": "dk_ref"}
DIR_OF = {"mothership": "up", "floor": "left", "underworld": "right"}
GUIDE = {  # name: (guide thing, route node, sprite stem)
    "mothership": ("dk_guide_mothership", "doom_dock.mothership", "mothership"),
    "floor": ("dk_guide_floor", "doom_dock.floor", "floor"),
    "underworld": ("dk_guide_underworld", "doom_dock.underworld", "underworld"),
}


def _rail(P):
    good = [
        P("dk_street_view", bars=4, hold=2, via=["dk_v_s1"]),
        P("dk_door_view", bars=4, hold=2, via=["dk_v_a1"]),
        P("dk_yard_view", bars=4, hold=2, via=["dk_v_u1"]),
        P("dk_ref", bars=4, hold=8, choice=True, via=["dk_v_r1"]),
    ]
    bad = [P("dk_ref_back", "queasy", "walk", 2), P("dk_sw_corner", "queasy", "stagger", 3)]
    routes = {
        "up": P("dk_moth", "dancer", bars=6, hold=1, via=["dk_v_s1", "dk_v_s2", "dk_v_s3"]),
        "left": P("dk_floor_door", "dancer", bars=5, hold=1, via=["dk_v_a1", "dk_v_w1", "dk_v_w2", "dk_v_d"]),
        "right": P("dk_under", "dancer", bars=5, hold=1, via=["dk_v_u1", "dk_v_u2", "dk_v_u3"]),
        "stumble": P("dk_ref", "recovered", "stagger", bars=3, via=["dk_ref_back", "dk_sw_corner"]),
        "arrive": {**P("dk_ref", bars=3), "from": "dk_arrive"},
    }
    return {"good": good, "bad": bad, "arrive": "dk_arrive", "exits": dict(EXITS), "routes": routes}


# id, short name, title, exit_scene, next [(to, dir, label, loop)], music slot
SCENES = [
    ("doom_dock", "dock", "The Loading Dock", False,
     [("doom_dock", "down", "Stay on the dock", True), ("doom_dock.mothership", "up", "Up the street to the Mothership", False),
      ("doom_dock.floor", "left", "Through the club door to the Floor", False), ("doom_dock.underworld", "right", "Across the yard to the Underworld", False)], 0),
    ("doom_dock.mothership", "dock_mothership", "The Mothership (stand-in)", False, [("doom_dock.return", "up", "On", False)], 2),
    ("doom_dock.floor", "dock_floor", "The Floor (stand-in)", False, [("doom_dock.return", "up", "On", False)], 1),
    ("doom_dock.underworld", "dock_underworld", "The Underworld (stand-in)", False, [("doom_dock.return", "up", "On", False)], 3),
    ("doom_dock.return", "dock_return", "Back to the Dock", True, [("doom_dock", "up", "Round again", True), ("doom_dock", "left", "Round again", True)], 5),
]


def _staging(thing, stem):
    def st(state, n, motion):
        return [{"thing": thing, "sprite": "guide_%s_%s_%d" % (stem, state, n), "motion": motion}]
    return {"archetype": "figure", "touch": {"w": 1.8, "h": 2.4},
            "states": {"current": st("available", 0, "still"), "other": st("idle", 0, "still"), "touched": st("selected", 0, "still"), "committed": st("committed", 0, "still"), "declined": st("idle", 0, "still")}}


def _hotspots(cinematics):
    hs = []
    for name, (thing, dest, stem) in GUIDE.items():
        cname = "doom_dock.stagger_%s" % name
        cinematics[cname] = {"world": "doom_dock", "steps": [{"move": "walk", "to": EXITS[DIR_OF[name]], "bars": 2, "role": "queasy", "style": "stagger"}]}
        hs.append({"id": "doom_dock.exit_%s" % name, "world": "doom_dock", "scene": "doom_dock", "map": "doom_dock", "anchor": {"thing": thing}, "kind": "exit",
                   "radius_m": 1.0, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
                   "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": dest},
                   "on_failure": {"route": dest, "cinematic": cname, "energy": -5}, "default": False, "repeatable": True, "staging": _staging(thing, stem),
                   "show": {"archetype": "figure"}})
    hs.append({"id": "doom_dock.exit_stay", "world": "doom_dock", "scene": "doom_dock", "map": "doom_dock", "anchor": {"pos": [1.0, 0.4, -3.2]}, "kind": "exit",
               "radius_m": 1.4, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
               "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": "doom_dock"},
               "on_failure": {"route": "doom_dock", "energy": -5}, "default": True, "repeatable": True,
               "staging": {"archetype": "none", "touch": {"w": 2.6, "h": 1.4}}, "show": {"archetype": "none"}})
    return {"world": "doom_dock", "hotspots": hs}


def add(P, worlds, nodes, cinematics, music, hotspot_files):
    """Appends the dock's world, nodes, cinematics, music entries and hotspot file to the overlay's lists (P: make_doom.P, the rail place builder)."""
    worlds.append(WORLD)
    for sid, short, title, exit_scene, nxt, slot in SCENES:
        r = _rail(P)
        r["glances"] = [{"by": -10, "bars": 2}, {"by": 12, "bars": 2}, {"by": -6, "pitch": 3, "bars": 2}]  # restrained: the pads and the guides stay in view
        r["strolls"] = [{"fwd": 0.6, "bars": 3}]
        nodes.append({"id": sid, "world": "doom_dock", "scene": short, "title": title, "entry": sid == "doom_dock", "exit_scene": exit_scene, "role": "dancer",
                      "blurb": WORLD["blurb"] if sid == "doom_dock" else title,
                      "next": [{"to": t[0], "dir": t[1], "label": t[2], **({"loop": True} if t[3] else {})} for t in nxt],
                      "place": {"waypoint": "dk_ref", "rail": r}})
        music.append({"id": sid, "arrangement": "warehouse_1", "slot": slot, "alternates": ["warehouse_2", "warehouse_3"], "treatment": "none", "temporary": False})
    hotspot_files["doom_dock"] = _hotspots(cinematics)
