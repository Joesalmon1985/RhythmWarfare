"""The Mothership's part of the Doom worlds overlay (docs/doom/scenes/mothership.md): the world `doom_mothership`, its scenes, its hotspots. Called from tools/run/make_doom.py (`write`), which merges it
into content/run/doom/run.json, music.json and hotspots/doom_mothership.json.

Geography world (docs/engine/GEOGRAPHY_WORLDS.md, hook H1.6): ONE scene, the world's entry (id = world id, `"geography": true`), its `down` route the stay loop and its three
routes straight to the entry scenes of other geography worlds: ahead doom_underworld, left doom_booth, right doom_dock. The guides' `on_success.route` names those worlds; each route move (`rail.routes[dir]`) ends at the
threshold (`rail.exits[dir]`), where the run walks before the boundary, shuts the frame and swaps the stage.
"""
from __future__ import annotations

WORLD = {"id": "doom_mothership", "title": "The Mothership (Doom worlds)", "map": "doom_mothership", "depth": 2, "geography": True, "story": "res://content/run/doom/story_doom_mothership.json",
         "blurb": "A violet atrium, a ring walk over a glowing void. The stair to the Underworld ahead, the platform hatch of the Booth on the left, the dock hatch on the right: follow the guide you like."}
EXITS = {"up": "ms_uw_hatch", "left": "ms_booth_hatch", "right": "ms_dock_in", "down": "ms_ref"}
PITCH = -14.0  # degrees (negative looks down): the choice hold at ms_ref (docs/engine/GEOGRAPHY_WORLDS.md)
DIR_OF = {"underworld": "up", "booth": "left", "dock": "right"}
GUIDE = {  # name: (guide thing, route node, sprite stem)
    "underworld": ("ms_guide_underworld", "doom_underworld", "underworld"),
    "booth": ("ms_guide_booth", "doom_booth", "booth"),
    "dock": ("ms_guide_dock", "doom_dock", "dock"),
}
STAY_AT = (-1.3, 0.4, -6.6)  # on the ring just ahead of the reference viewpoint (map x, height, z)


def _rail(P):
    ring = ["ms_v_a1", "ms_v_a2", "ms_v_a3", "ms_v_a4"]
    good = [
        P("ms_hub_view", bars=3, hold=2, via=["ms_v_a1"]),
        P("ms_stair_view", bars=3, hold=2, via=["ms_v_a3"]),
        P("ms_bridge_view", bars=4, hold=2, via=["ms_v_a3", "ms_v_a2", "ms_v_a1"]),
        {**P("ms_ref", bars=3, hold=8, choice=True, via=["ms_v_a1"]), "pitch": PITCH},  # round 2: a steady look down over the balustrade: the pool's glow in the lower part of the choice view
    ]
    bad = [P("ms_ref_back", "queasy", "walk", 2), P("ms_sw_corner", "queasy", "stagger", 3)]
    routes = {
        "up": P("ms_uw_hatch", "dancer", bars=7, hold=1, via=ring + ["ms_v_uw"]),
        "left": P("ms_booth_hatch", "dancer", bars=4, hold=1, via=["ms_v_a1", "ms_v_br"]),
        "right": P("ms_dock_in", "dancer", bars=4, hold=1, via=["ms_v_a1", "ms_v_a2", "ms_v_dk"]),
        "stumble": P("ms_ref", "recovered", "stagger", bars=3, via=["ms_ref_back", "ms_sw_corner"]),
        "arrive": {**P("ms_ref", bars=3), "from": "ms_arrive"},
    }
    return {"good": good, "bad": bad, "arrive": "ms_arrive", "exits": dict(EXITS), "routes": routes}


# id, short name, title, exit_scene, next [(to, dir, label, loop)], music slot
SCENES = [
    ("doom_mothership", "mothership", "The Mothership", True,
     [("doom_mothership", "down", "Stay on the ring", True), ("doom_underworld", "up", "Up the stair to the Underworld", False),
      ("doom_booth", "left", "Across the bridge to the Booth", False), ("doom_dock", "right", "Through the hatch to the Dock", False)], 0),
]


def _staging(thing, stem):
    def st(state, n, motion):
        return [{"thing": thing, "sprite": "guide_%s_%s_%d" % (stem, state, n), "motion": motion}]
    return {"archetype": "figure", "touch": {"w": 1.8, "h": 2.4},
            "states": {"current": st("available", 0, "still"), "other": st("idle", 0, "still"), "touched": st("selected", 0, "still"), "committed": st("committed", 0, "still"), "declined": st("idle", 0, "still")}}


def _hotspots(cinematics):
    hs = []
    for name, (thing, dest, stem) in GUIDE.items():
        cname = "doom_mothership.stagger_%s" % name
        cinematics[cname] = {"world": "doom_mothership", "steps": [{"move": "walk", "to": EXITS[DIR_OF[name]], "bars": 2, "role": "queasy", "style": "stagger"}]}
        hs.append({"id": "doom_mothership.exit_%s" % name, "world": "doom_mothership", "scene": "doom_mothership", "map": "doom_mothership", "anchor": {"thing": thing}, "kind": "exit",
                   "radius_m": 1.0, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
                   "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": dest},
                   "on_failure": {"route": dest, "cinematic": cname, "energy": -5}, "default": False, "repeatable": True, "staging": _staging(thing, stem),
                   "show": {"archetype": "figure"}})
    hs.append({"id": "doom_mothership.exit_stay", "world": "doom_mothership", "scene": "doom_mothership", "map": "doom_mothership", "anchor": {"pos": list(STAY_AT)}, "kind": "exit",
               "radius_m": 1.4, "min_px": 88, "available": {"flags_all": [], "flags_none": [], "energy_min": 0, "once": False},
               "look": {"available": "open", "selected": "ring", "committed": "flash"}, "challenge": None, "on_success": {"route": "doom_mothership"},
               "on_failure": {"route": "doom_mothership", "energy": -5}, "default": True, "repeatable": True,
               "staging": {"archetype": "none", "touch": {"w": 2.6, "h": 1.4}}, "show": {"archetype": "none"}})
    return {"world": "doom_mothership", "hotspots": hs}


def add(P, worlds, nodes, cinematics, music, hotspot_files):
    """Appends the mothership's world, nodes, cinematics, music entries and hotspot file to the overlay's lists (P: make_doom.P, the rail place builder)."""
    worlds.append(WORLD)
    for sid, short, title, exit_scene, nxt, slot in SCENES:
        r = _rail(P)
        r["glances"] = [{"by": -10, "bars": 2}, {"by": 12, "bars": 2}, {"by": -6, "pitch": 3, "bars": 2}]  # restrained: the pads and the guides stay in view
        r["strolls"] = [{"fwd": 0.6, "bars": 3}]
        nodes.append({"id": sid, "world": "doom_mothership", "scene": short, "title": title, "entry": sid == "doom_mothership", "exit_scene": exit_scene, "role": "dancer",
                      "blurb": WORLD["blurb"] if sid == "doom_mothership" else title,
                      "next": [{"to": t[0], "dir": t[1], "label": t[2], **({"loop": True} if t[3] else {})} for t in nxt],
                      "place": {"waypoint": "ms_ref", "rail": r}})
        music.append({"id": sid, "arrangement": "warehouse_1", "slot": slot, "alternates": ["warehouse_2", "warehouse_3"], "treatment": "none", "temporary": False})
    hotspot_files["doom_mothership"] = _hotspots(cinematics)
