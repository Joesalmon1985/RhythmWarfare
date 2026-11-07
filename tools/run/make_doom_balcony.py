"""The Balcony's part of the Doom worlds overlay (docs/doom/scenes/balcony.md): the world `doom_balcony`, its scenes, its hotspots. Called from tools/run/make_doom.py (`write`), which merges it
into content/run/doom/run.json, music.json and hotspots/doom_balcony.json.

Geography world (docs/engine/GEOGRAPHY_WORLDS.md, hook H1.6): ONE scene, the world's entry (id = world id, `"geography": true`), its `down` route the stay loop and its three
routes straight to the entry scenes of other geography worlds: ahead doom_mothership, left doom_warehouse (the Floor), right doom_booth. The guides' `on_success.route` names those worlds; each route move (`rail.routes[dir]`) ends at the
threshold (`rail.exits[dir]`), where the run walks before the boundary, shuts the frame and swaps the stage.
"""
from __future__ import annotations

WORLD = {"id": "doom_balcony", "title": "The Balcony (Doom worlds)", "map": "doom_balcony", "depth": 2, "geography": True, "story": "res://content/run/doom/story_doom_balcony.json",
         "blurb": "A rainy industrial rooftop at night. The bridge to the mothership ahead, the brick stair down to the floor on the left, the lit booth door on the right: follow the guide you like."}
EXITS = {"up": "bc_bridge_end", "left": "bc_stair_foot", "right": "bc_cabin_in", "down": "bc_ref"}
DIR_OF = {"mothership": "up", "floor": "left", "booth": "right"}
GUIDE = {  # name: (guide thing, route node, sprite stem)
    "mothership": ("bc_guide_mothership", "doom_mothership", "mothership"),
    "floor": ("bc_guide_floor", "doom_warehouse", "floor"),
    "booth": ("bc_guide_booth", "doom_booth", "booth"),
}


def _rail(P):
    good = [
        P("bc_bridge_view", bars=4, hold=2, via=["bc_v_a1"]),
        P("bc_stair_view", bars=3, hold=2, via=["bc_v_a2"]),
        P("bc_cabin_view", bars=3, hold=2, via=["bc_v_a3"]),
        P("bc_ref", bars=4, hold=8, choice=True, via=["bc_v_a4"]),
    ]
    bad = [P("bc_ref_back", "queasy", "walk", 2), P("bc_sw_corner", "queasy", "stagger", 3)]
    routes = {
        "up": P("bc_bridge_end", "dancer", bars=5, hold=1, via=["bc_v_a1", "bc_v_n", "bc_v_ba", "bc_v_bb", "bc_v_bc"]),
        "left": P("bc_stair_foot", "dancer", bars=5, hold=1, via=["bc_v_a2", "bc_v_land", "bc_v_s_a", "bc_v_s_b", "bc_v_s_c", "bc_v_s_d"]),
        "right": P("bc_cabin_in", "dancer", bars=3, hold=1, via=["bc_v_e1", "bc_v_door"]),
        "stumble": P("bc_ref", "recovered", "stagger", bars=3, via=["bc_ref_back", "bc_sw_corner"]),
        "arrive": {**P("bc_ref", bars=3), "from": "bc_arrive"},
    }
    return {"good": good, "bad": bad, "arrive": "bc_arrive", "exits": dict(EXITS), "routes": routes}


# id, short name, title, exit_scene, next [(to, dir, label, loop)], music slot
SCENES = [
    ("doom_balcony", "balcony", "The Balcony", True,
     [("doom_balcony", "down", "Stay on the roof", True), ("doom_mothership", "up", "Over the bridge to the mothership", False),
      ("doom_warehouse", "left", "Down the brick stair to the floor", False), ("doom_booth", "right", "Through the lit door to the booth", False)], 2),
]


def _staging(thing, stem):
    def st(state, n, motion):
        return [{"thing": thing, "sprite": "guide_%s_%s_%d" % (stem, state, n), "motion": motion}]
    return {"archetype": "figure", "touch": {"w": 1.8, "h": 2.4},
            "states": {"current": st("available", 0, "still"), "other": st("idle", 0, "still"), "touched": st("selected", 0, "still"), "committed": st("committed", 0, "still"), "declined": st("idle", 0, "still")}}


def _hotspots(cinematics):
    hs = []
    for name, (thing, dest, stem) in GUIDE.items():
        cname = "doom_balcony.stagger_%s" % name
        cinematics[cname] = {"world": "doom_balcony", "steps": [{"move": "walk", "to": EXITS[DIR_OF[name]], "bars": 2, "role": "queasy", "style": "stagger"}]}
        hs.append({"id": "doom_balcony.exit_%s" % name, "world": "doom_balcony", "scene": "doom_balcony", "map": "doom_balcony", "anchor": {"thing": thing}, "kind": "exit",
                   "radius_m": 1.0, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
                   "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": dest},
                   "on_failure": {"route": dest, "cinematic": cname, "energy": -5}, "default": False, "repeatable": True, "staging": _staging(thing, stem),
                   "show": {"archetype": "figure", "light": "bc_lamp_%s" % name}})
    hs.append({"id": "doom_balcony.exit_stay", "world": "doom_balcony", "scene": "doom_balcony", "map": "doom_balcony", "anchor": {"pos": [0.5, 0.4, -3.4]}, "kind": "exit",
               "radius_m": 1.4, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
               "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": "doom_balcony"},
               "on_failure": {"route": "doom_balcony", "energy": -5}, "default": True, "repeatable": True,
               "staging": {"archetype": "none", "touch": {"w": 2.6, "h": 1.4}}, "show": {"archetype": "none"}})
    return {"world": "doom_balcony", "hotspots": hs}


def add(P, worlds, nodes, cinematics, music, hotspot_files):
    """Appends the balcony's world, nodes, cinematics, music entries and hotspot file to the overlay's lists (P: make_doom.P, the rail place builder)."""
    worlds.append(WORLD)
    for sid, short, title, exit_scene, nxt, slot in SCENES:
        r = _rail(P)
        r["glances"] = [{"by": -10, "bars": 2}, {"by": 12, "bars": 2}, {"by": -6, "pitch": 3, "bars": 2}]  # restrained: the pads and the guides stay in view
        r["strolls"] = [{"fwd": 0.6, "bars": 3}]
        nodes.append({"id": sid, "world": "doom_balcony", "scene": short, "title": title, "entry": sid == "doom_balcony", "exit_scene": exit_scene, "role": "dancer",
                      "blurb": WORLD["blurb"] if sid == "doom_balcony" else title,
                      "next": [{"to": t[0], "dir": t[1], "label": t[2], **({"loop": True} if t[3] else {})} for t in nxt],
                      "place": {"waypoint": "bc_ref", "rail": r}})
        music.append({"id": sid, "arrangement": "warehouse_1", "slot": slot, "alternates": ["warehouse_2", "warehouse_3"], "treatment": "none", "temporary": False})
    hotspot_files["doom_balcony"] = _hotspots(cinematics)
