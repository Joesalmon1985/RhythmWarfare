"""The DJ Booth's part of the Doom worlds overlay (docs/doom/scenes/booth.md): the world `doom_booth`, its scenes, its hotspots. Called from tools/run/make_doom.py (`write`), which merges it
into content/run/doom/run.json, music.json and hotspots/doom_booth.json.

Geography world (docs/engine/GEOGRAPHY_WORLDS.md, hook H1.6): ONE scene, the world's entry (id = world id, `"geography": true`), its `down` route the stay loop and its three
routes straight to the entry scenes of other geography worlds: ahead doom_mothership, left doom_balcony, right doom_dock. The guides' `on_success.route` names those worlds; each route move (`rail.routes[dir]`) ends at the
threshold (`rail.exits[dir]`), where the run walks before the boundary, shuts the frame and swaps the stage.
"""
from __future__ import annotations

WORLD = {"id": "doom_booth", "title": "The DJ Booth (Doom worlds)", "map": "doom_booth", "depth": 2, "geography": True, "story": "res://content/run/doom/story_doom_booth.json",
         "blurb": "A windowed control room over the rain. The Mothership's hatch ahead, the balcony stair on the left, the dock door on the right: follow the guide you like."}
EXITS = {"up": "bt_hatch", "left": "bt_bal_top", "right": "bt_dock_in", "down": "bt_ref"}
DIR_OF = {"mothership": "up", "balcony": "left", "dock": "right"}
GUIDE = {  # name: (guide thing, route node, sprite stem)
    "mothership": ("bt_guide_mothership", "doom_mothership", "mothership"),
    "balcony": ("bt_guide_balcony", "doom_balcony", "balcony"),
    "dock": ("bt_guide_dock", "doom_dock", "dock"),
}


def _rail(P):
    # round 2: one reveal, then the choice viewpoint. The run moves the rail one place per passed block and holds the choice only when the camera stands on the choice place
    # by the window (beat 49): round 1's four-place loop was still walking when the window opened (a real run, the bot, RW_RUN_VIRTUAL). The other reveals stay in the map as views.
    good = [
        P("bt_hatch_view", bars=4, hold=2, via=["bt_v_a1"]),
        P("bt_ref", bars=4, hold=8, choice=True, via=["bt_v_a4"]),
    ]
    bad = [P("bt_ref_back", "queasy", "walk", 2), P("bt_sw_corner", "queasy", "stagger", 3)]
    routes = {
        "up": P("bt_hatch", "dancer", bars=4, hold=1, via=["bt_v_a1", "bt_v_a5"]),
        "left": P("bt_bal_top", "dancer", bars=5, hold=1, via=["bt_v_a2", "bt_v_land", "bt_v_door", "bt_v_porch", "bt_v_step_a", "bt_v_step_b"]),
        "right": P("bt_dock_in", "dancer", bars=3, hold=1, via=["bt_v_dock_a", "bt_v_dockdoor"]),
        "stumble": P("bt_ref", "recovered", "stagger", bars=3, via=["bt_ref_back", "bt_sw_corner"]),
        "arrive": {**P("bt_ref", bars=3), "from": "bt_arrive"},
    }
    return {"good": good, "bad": bad, "arrive": "bt_arrive", "exits": dict(EXITS), "routes": routes}


# id, short name, title, exit_scene, next [(to, dir, label, loop)], music slot
SCENES = [
    ("doom_booth", "booth", "The DJ Booth", True,
     [("doom_booth", "down", "Stay in the booth", True), ("doom_mothership", "up", "Through the hatch to the mothership", False),
      ("doom_balcony", "left", "Out to the balcony", False), ("doom_dock", "right", "Through the steel door to the dock", False)], 0),
]


def _staging(thing, stem):
    def st(state, n, motion):
        return [{"thing": thing, "sprite": "guide_%s_%s_%d" % (stem, state, n), "motion": motion}]
    return {"archetype": "figure", "touch": {"w": 1.8, "h": 2.4},
            "states": {"current": st("available", 0, "still"), "other": st("idle", 0, "still"), "touched": st("selected", 0, "still"), "committed": st("committed", 0, "still"), "declined": st("idle", 0, "still")}}


def _hotspots(cinematics):
    hs = []
    for name, (thing, dest, stem) in GUIDE.items():
        cname = "doom_booth.stagger_%s" % name
        cinematics[cname] = {"world": "doom_booth", "steps": [{"move": "walk", "to": EXITS[DIR_OF[name]], "bars": 2, "role": "queasy", "style": "stagger"}]}
        hs.append({"id": "doom_booth.exit_%s" % name, "world": "doom_booth", "scene": "doom_booth", "map": "doom_booth", "anchor": {"thing": thing}, "kind": "exit",
                   "radius_m": 1.0, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
                   "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": dest},
                   "on_failure": {"route": dest, "cinematic": cname, "energy": -5}, "default": False, "repeatable": True, "staging": _staging(thing, stem),
                   "show": {"archetype": "figure"}})
    hs.append({"id": "doom_booth.exit_stay", "world": "doom_booth", "scene": "doom_booth", "map": "doom_booth", "anchor": {"pos": [0.5, 0.4, -3.4]}, "kind": "exit",
               "radius_m": 1.4, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
               "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": "doom_booth"},
               "on_failure": {"route": "doom_booth", "energy": -5}, "default": True, "repeatable": True,
               "staging": {"archetype": "none", "touch": {"w": 2.6, "h": 1.4}}, "show": {"archetype": "none"}})
    return {"world": "doom_booth", "hotspots": hs}


def add(P, worlds, nodes, cinematics, music, hotspot_files):
    """Appends the booth's world, nodes, cinematics, music entries and hotspot file to the overlay's lists (P: make_doom.P, the rail place builder)."""
    worlds.append(WORLD)
    for sid, short, title, exit_scene, nxt, slot in SCENES:
        r = _rail(P)
        r["glances"] = [{"by": -10, "bars": 2}, {"by": 12, "bars": 2}, {"by": -6, "pitch": 3, "bars": 2}]  # restrained: the pads and the guides stay in view
        r["strolls"] = [{"fwd": 0.6, "bars": 3}]
        nodes.append({"id": sid, "world": "doom_booth", "scene": short, "title": title, "entry": sid == "doom_booth", "exit_scene": exit_scene, "role": "dancer",
                      "blurb": WORLD["blurb"] if sid == "doom_booth" else title,
                      "next": [{"to": t[0], "dir": t[1], "label": t[2], **({"loop": True} if t[3] else {})} for t in nxt],
                      "place": {"waypoint": "bt_ref", "rail": r}})
        music.append({"id": sid, "arrangement": "warehouse_1", "slot": slot, "alternates": ["warehouse_2", "warehouse_3"], "treatment": "none", "temporary": False})
    hotspot_files["doom_booth"] = _hotspots(cinematics)
