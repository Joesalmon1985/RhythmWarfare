"""Authors the Chill-out Lounge scene into content/story/maps/doom_lounge.json (docs/doom/scenes/lounge.md), on the Warehouse pilot's pipeline.

    python -I tools/doom/trace/lounge_scene.py; python -I tools/doom/convert.py --scene lounge --trace tools/doom/trace/lounge_pilot.json     # the geometry (this script's input)
    python -I tools/doom/art/make_lounge_art.py; python -I tools/doom/art/make_lounge_guides.py                                                 # textures, props, the two new guides
    python -I tools/doom/author_lounge.py                                                         # waypoints, textures, things, decals, lights, spots (idempotent; run after every convert)

Reference: art/reference/doom_worlds/Mustard octagonal lounge of three routes-2.png. Routing (docs/briefs/DOOM_WORLDS_BRIEF.md): ahead = Dock (N face, a rain-slick street), left = Bar (NW face, a bar room
with a counter and bottle shelves), right = Floor (NE face, a blue-lit passage back to the Warehouse). All coordinates are Doom units (32 = 1 m, x east, y north), converted like convert.py does.
Waypoints are named lg_*; names starting lg_v_ are via points only (corners of the polyline moves), never stood on. The Magic rave borrows this geography: the octagon's rooms keep the names of
tools/doom/trace/lounge_scene.py and the ring of via points `lg_v_*` goes round the pit.
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "trace"))
import author_warehouse as aw  # noqa: E402  (helpers only: m, face, lift, sector_of, dist_to_edges)
from lounge_scene import to_world  # noqa: E402

ROOT = aw.ROOT
MAP = os.path.join(ROOT, "content", "story", "maps", "doom_lounge.json")
TRACE = os.path.join(HERE, "trace", "lounge_pilot.json")
OWN = "textures/"
SHARED = "res://assets/story/doom_warehouse/textures/"  # the Bar guide's sprites are the Warehouse's
NIGHT = "res://assets/story/night_one/textures/"
MARGIN = 0.5
MAX_STEP = 0.5
LIGHT_GAIN, LIGHT_FLOOR, TINT_LIFT, LAMP_GAIN = 2.0, 0.85, 0.72, 2.5
STATES = {"idle": 1, "available": 5, "selected": 2, "committed": 2}
m, face, lift, sector_of, dist_to_edges = aw.m, aw.face, aw.lift, aw.sector_of, aw.dist_to_edges
aw.TINT_LIFT = TINT_LIFT


def W(face_, u, v):
    return to_world(face_, u, v)


# sector (by the trace's name) -> floor, wall, ceiling, tint, step_tex (the riser up onto it), lip_tex (the lintel / lip where its ceiling is the lower one), light override
S = {}


def style(names, floor, wall, ceil, tint, step=None, lip=None, light=None):
    for n in names.split():
        S[n] = (floor, wall, ceil, tint, step or wall, lip or wall, light)


style("concourse", "floor_marble", "wall_stone", "ceil_beam", "#e8c890", step="wall_marble", lip="wall_beam", light=0.9)
style("step_ring", "floor_marble", "wall_marble", "ceil_beam", "#ffd8a0", step="wall_marble", lip="wall_beam", light=0.9)
style("back_n back_s", "floor_sofa", "wall_sofa", "ceil_beam", "#ffe0a0", step="wall_sofa", light=0.95)
style("seat_n seat_s", "floor_sofa", "wall_sofa", "ceil_beam", "#ffe0a0", step="wall_sofa", light=0.95)
style("gap_e gap_w", "floor_marble", "wall_stone", "ceil_beam", "#ffd8a0", step="wall_marble", light=0.9)
style("rug_rim rug_mid", "floor_rug_red", "wall_sofa", "ceil_beam", "#ffe0b0", step="wall_sofa", light=0.95)
style("rug_stripe_a rug_stripe_b", "floor_rug_cream", "wall_sofa", "ceil_beam", "#fff0d0", step="wall_sofa", light=0.95)
style("rug_in", "floor_rug_orange", "wall_sofa", "ceil_beam", "#ffe0b0", step="wall_table", light=0.95)
style("table", "floor_table", "wall_table", "ceil_beam", "#ffe8c0", step="wall_table", light=1.0)
style("ahead_step_a ahead_step_b", "floor_marble", "wall_stone", "ceil_street", "#c8d4e8", step="wall_stone", lip="wall_stone", light=0.85)
style("ahead_street", "floor_street", "wall_street", "ceil_street", "#b8c8e8", step="wall_stone", lip="wall_stone", light=1.0)
style("left_vest", "floor_wood", "wall_wood", "ceil_beam", "#ffd0a0", step="wall_wood", lip="wall_stone", light=0.9)
style("left_bar", "floor_wood", "wall_wood", "ceil_beam", "#ffc890", step="wall_copper", lip="wall_stone", light=0.9)
style("left_counter", "floor_table", "wall_copper", "ceil_beam", "#ffd8a8", step="wall_copper", light=1.0)
style("right_vest", "floor_blue", "wall_blue", "ceil_street", "#a8c0ff", step="wall_blue", lip="wall_stone", light=1.0)
style("right_passage", "floor_blue", "wall_blue", "ceil_street", "#8ca8ff", step="wall_blue", lip="wall_blue", light=1.0)
style("niche_e niche_w niche_s niche_se niche_sw", "floor_curtain", "wall_curtain", "ceil_beam", "#ffc8a0", step="wall_curtain", lip="wall_stone", light=0.85)
OWN_TEX = ["wall_stone", "wall_marble", "wall_sofa", "wall_curtain", "wall_wood", "wall_copper", "wall_table", "wall_street", "wall_blue", "wall_beam",
           "floor_marble", "floor_rug_red", "floor_rug_cream", "floor_rug_orange", "floor_sofa", "floor_table", "floor_wood", "floor_street", "floor_blue", "floor_curtain",
           "ceil_beam", "ceil_street", "thing_plant", "thing_lamp", "thing_vase", "thing_cushion", "thing_cushion_b",
           "deco_studs", "deco_vinyl", "deco_sconce", "deco_bottles", "deco_beads", "wall_stone_b", "wall_stone_c", "lg_p_sofa", "lg_p_palm_l", "lg_p_palm_r"]
RAIN_IN = ("ahead_street",)
WET = {"concourse": 0.45, "step_ring": 0.45, "ahead_street": 0.9, "ahead_step_a": 0.6, "ahead_step_b": 0.6, "right_vest": 0.5, "right_passage": 0.5}  # stage D: the painting's polished marble and the rain street (gloss)
STONES = ["wall_stone", "wall_stone_b", "wall_stone_c"]  # the stone's three variants, one per piece (a hash of its id): no wall repeats one tile
GUIDE_OWN = {"dock": OWN, "floor": OWN, "bar": SHARED}  # where each guide's sprite set lives

# id, doom point, look-at doom point, hold_bars (0 = a moving place), what it is
WAYPOINTS = [
    ("lg_arrive", W("ne", 0, 20), (0, -196), 0, "arrival: the mouth of the blue passage (from the Floor), facing the lounge"),
    ("lg_ref", (0, -196), (0, 300), 8, "THE reference viewpoint: the south walkway behind the near sofa, the pit before you, the Dock street ahead, the Bar arch left, the blue passage right"),
    ("lg_ref_back", (40, -214), (0, 300), 0, "recovery: a stumble back to the south wall"),
    ("lg_sw_corner", (-100, -200), (0, 300), 0, "recovery: along the south-west walkway"),
    ("lg_west", (-196, -50), (150, 0), 2, "reveal: the west walkway, the pit and its sofas across to the blue passage"),
    ("lg_north", (0, 200), (0, 400), 2, "reveal: the north walkway under the door, the rain street beyond the steps and the Dock guide"),
    ("lg_east", (196, 45), (-175, 175), 2, "reveal: the east walkway looking back across the pit to the Bar arch"),
    ("lg_ahead_door", W("n", 0, -6), (0, 330), 0, "THRESHOLD ahead (Dock): at the foot of the steps, 3.2 m before the Dock guide (stage D: held a step back so the pads do not cover him); the world transition happens here"),
    ("lg_bar_door", W("nw", 0, 22), (-220, 262), 0, "THRESHOLD left (Bar): inside the arch, before the Bar guide"),
    ("lg_floor_door", W("ne", 0, 2), (233, 205), 0, "THRESHOLD right (Floor): at the blue passage's mouth, a step back from the Floor guide (stage D)"),
    # via points: the ring round the pit (octagon of inradius 196), and the way in at each door
    ("lg_v_ene", (196, 81), (81, 196), 0, "via: the walkway, east-north-east corner"),
    ("lg_v_nne", (81, 196), (-81, 196), 0, "via: north-north-east"),
    ("lg_v_nnw", (-81, 196), (-196, 81), 0, "via: north-north-west"),
    ("lg_v_wnw", (-196, 81), (-196, -81), 0, "via: west-north-west"),
    ("lg_v_wsw", (-196, -81), (-81, -196), 0, "via: west-south-west"),
    ("lg_v_ssw", (-81, -196), (81, -196), 0, "via: south-south-west"),
    ("lg_v_sse", (81, -196), (196, -81), 0, "via: south-south-east"),
    ("lg_v_ese", (196, -81), (196, 81), 0, "via: east-south-east"),
    ("lg_v_n", (0, 205), (0, 330), 0, "via: in front of the Dock door"),
]
ROUTES = {  # the three routes and the stay loop as waypoint ids, via points included; tools/run/make_doom_lounge.py cuts them into moves
    "ahead": ["lg_v_sse", "lg_v_ese", "lg_v_ene", "lg_v_nne", "lg_v_n", "lg_ahead_door"],
    "left": ["lg_v_ssw", "lg_v_wsw", "lg_v_wnw", "lg_bar_door"],
    "right": ["lg_v_sse", "lg_v_ese", "lg_v_ene", "lg_floor_door"],
    "stay": ["lg_v_ssw", "lg_v_wsw", "lg_west", "lg_v_wnw", "lg_v_nnw", "lg_north", "lg_v_nne", "lg_v_ene", "lg_east", "lg_v_ese", "lg_v_sse", "lg_ref"],
    "arrive": ["lg_arrive", "lg_v_ene", "lg_v_ese", "lg_v_sse", "lg_ref"],
    "stumble": ["lg_ref_back", "lg_sw_corner", "lg_ref"],
}
GUIDES = {  # id suffix: doom point, size (height m), lamp point
    "dock": (W("n", 0, 98), 2.35, W("n", 0, 70)),
    "bar": (W("nw", -30, 100), 2.2, W("nw", -30, 80)),
    "floor": (W("ne", -26, 60), 2.2, W("ne", -26, 42)),
}
THINGS = [  # id, sprite, doom point, y centre above the sector's floor, size (height)
    ("lg_plant_n1", "thing_plant", (-88, 226), 1.05, 2.1), ("lg_plant_n2", "thing_plant", (88, 226), 1.05, 2.1),
    ("lg_plant_w", "thing_plant", (-208, -90), 1.0, 2.0), ("lg_plant_e", "thing_plant", (208, -90), 1.0, 2.0),
    ("lg_plant_sw", "thing_plant", (-208, 92), 1.0, 2.0), ("lg_plant_se", "thing_plant", (208, 92), 1.0, 2.0),
    ("lg_plant_bar", "thing_plant", W("nw", 85, 60), 1.0, 2.0),
    ("lg_lamp_table", "thing_lamp", (0, 0), 0.34, 0.7), ("lg_vase", "thing_vase", (16, 10), 0.4, 0.8),
    ("lg_cushion_a", "thing_cushion", (-34, 106), 0.36, 0.55), ("lg_cushion_b", "thing_cushion_b", (-14, 108), 0.34, 0.5),
    ("lg_cushion_c", "thing_cushion_b", (50, -104), 0.34, 0.5), ("lg_cushion_d", "thing_cushion", (-50, -102), 0.36, 0.55),
    # the painting's foreground (stage D polish), cut from it: the near sofa with the patterned cushion 1.4 m before the reference viewpoint (on the pit's step ring, -0.375 m:
    # its top is 0.9 m over the walkway) and the two palms at the frame's edges
    ("lg_fg_sofa", "lg_p_sofa", (0, -150), 0.82, 0.9), ("lg_fg_palm_l", "lg_p_palm_l", (-52, -145), 1.15, 1.6), ("lg_fg_palm_r", "lg_p_palm_r", (56, -148), 1.25, 1.8),
]
LIGHTS = [  # id, doom point, y, radius, colour, strength   (warm lamps in the hub, a cool pool beyond each doorway: grey-blue rain, amber bar, cobalt passage)
    ("lg_lt_table", (0, 0), 1.6, 9.0, "#ffa43c", 1.8), ("lg_lt_dome", (0, 0), 5.2, 15.0, "#ffb860", 1.1),
    ("lg_lt_ring_ne", (150, 150), 3.4, 9.0, "#ffb050", 1.4), ("lg_lt_ring_nw", (-150, 150), 3.4, 9.0, "#ffb050", 1.4),
    ("lg_lt_ring_se", (150, -150), 3.4, 9.0, "#ffb050", 1.4), ("lg_lt_ring_sw", (-150, -150), 3.4, 9.0, "#ffb050", 1.4),
    ("lg_lt_ref", (0, -200), 3.4, 8.0, "#ffc070", 1.2),
    ("lg_lt_dock", (0, 330), 3.0, 8.0, "#8cacd8", 1.5), ("lg_lt_dock2", (0, 250), 3.0, 6.0, "#9ab4d8", 1.1),
    ("lg_lt_bar", W("nw", 0, 110), 2.8, 7.0, "#ffa040", 1.8), ("lg_lt_bar2", W("nw", 60, 150), 2.6, 5.0, "#ffb860", 1.4),
    # stage D: the Dock guide is lit from the street lamp over him and the hub's amber behind the viewer (the first pass left him a silhouette in the doorway)
    ("lg_lt_dock_key", W("n", 0, 80), 2.7, 3.5, "#dce6ff", 1.8), ("lg_lt_dock_warm", W("n", 0, 30), 2.2, 4.0, "#ffc080", 1.4),
    ("lg_lt_st_w", (-60, 330), 2.2, 4.5, "#ffd090", 1.6), ("lg_lt_st_e", (60, 390), 2.2, 4.5, "#c8d8ff", 1.6), ("lg_lt_st_n", (-40, 420), 2.4, 4.5, "#ffd090", 1.4),
    ("lg_lt_floor", W("ne", 0, 100), 2.8, 8.0, "#3c64ff", 1.7), ("lg_lt_floor2", W("ne", 0, 40), 2.6, 5.0, "#5a80ff", 1.3),
]
DECALS = [  # id, sprite, doom point (a metre of the wall at most), bottom m, height m, emissive
    ("lg_sc_n1", "deco_sconce", (-74, 237), 1.6, 1.25, True), ("lg_sc_n2", "deco_sconce", (74, 237), 1.6, 1.25, True),
    ("lg_sc_e1", "deco_sconce", (237, -74), 1.6, 1.25, True), ("lg_sc_w1", "deco_sconce", (-237, -74), 1.6, 1.25, True),
    ("lg_sc_e2", "deco_sconce", (237, 74), 1.6, 1.25, True), ("lg_sc_w2", "deco_sconce", (-237, 74), 1.6, 1.25, True),
    ("lg_sc_s1", "deco_sconce", (-74, -237), 1.6, 1.25, True), ("lg_sc_s2", "deco_sconce", (74, -237), 1.6, 1.25, True),
    ("lg_studs_nw1", "deco_studs", W("nw", 98, -2), 0.9, 1.9, False), ("lg_studs_nw2", "deco_studs", W("nw", -98, -2), 0.9, 1.9, False),
    ("lg_studs_ne1", "deco_studs", W("ne", 98, -2), 0.9, 1.9, False), ("lg_studs_ne2", "deco_studs", W("ne", -98, -2), 0.9, 1.9, False),
    ("lg_studs_se1", "deco_studs", W("se", 94, -2), 0.9, 1.9, False), ("lg_studs_se2", "deco_studs", W("se", -94, -2), 0.9, 1.9, False),
    ("lg_studs_sw1", "deco_studs", W("sw", 94, -2), 0.9, 1.9, False), ("lg_studs_sw2", "deco_studs", W("sw", -94, -2), 0.9, 1.9, False),
    ("lg_bottles", "deco_bottles", W("nw", -40, 188), 1.2, 1.3, True), ("lg_vinyl", "deco_vinyl", W("nw", 50, 188), 1.7, 1.0, False),
    ("lg_beads_w", "deco_beads", (-281, 0), 0.0, 2.6, False), ("lg_beads_e", "deco_beads", (281, 0), 0.0, 2.6, False),
    ("lg_beads_s", "deco_beads", (0, -281), 0.0, 2.6, False),
    # stage D: the street's wall lamps (the painting's rain street is lined with them), each with a cool pool (LIGHTS)
    ("lg_st_lamp_w", "deco_sconce", (-78, 330), 2.2, 0.8, True), ("lg_st_lamp_e", "deco_sconce", (78, 390), 2.2, 0.8, True),
    ("lg_st_lamp_n", "deco_sconce", (-40, 438), 2.4, 0.8, True),
]


def barriers(d):
    """As the Warehouse's: a portal whose floors differ by more than MAX_STEP is shut to walkers (`blocked`: the sofa backs, the counter) as long as every piece stays reachable."""
    sec = {s["id"]: s for s in d["sectors"]}
    walls = [w for w in d["walls"] if w.get("portal")]
    start = next(w for w in d["waypoints"] if w["id"] == d["start"])["sector"]

    def all_reachable():
        adj = {}
        for w in walls:
            if not w.get("blocked"):
                adj.setdefault(w["sector"], set()).add(w["portal"])
                adj.setdefault(w["portal"], set()).add(w["sector"])
        seen, queue = {start}, [start]
        while queue:
            for n in adj.get(queue.pop(), ()):
                if n not in seen:
                    seen.add(n)
                    queue.append(n)
        return len(seen) == len(sec)

    def drop_of(w):
        return abs(float(sec[w["sector"]]["floor"]) - float(sec[w["portal"]]["floor"]))

    def mid_dist(w):
        return math.hypot((w["from"][0] + w["to"][0]) / 2.0, (w["from"][1] + w["to"][1]) / 2.0)

    for w in sorted((w for w in walls if drop_of(w) > MAX_STEP + 1e-6 and not w.get("blocked")), key=mid_dist):
        w["blocked"] = True
        if not all_reachable():
            del w["blocked"]


def main():
    d = json.load(open(MAP, encoding="utf-8"))
    names = json.load(open(TRACE, encoding="utf-8"))["sector_names"]
    d["art"] = "doom_lounge"
    used = {}
    for s in d["sectors"]:
        nm = names[int(s["doom_sector"])]
        f, w, c, tint, step, lip, light = S[nm]
        if w == "wall_stone":
            w = STONES[sum(ord(ch) * (i + 1) for i, ch in enumerate(str(s["id"]))) % len(STONES)]
        s["floor_tex"], s["wall_tex"], s["ceil_tex"], s["tint"] = f, w, c, lift(tint)
        s["step_tex"], s["lip_tex"] = step, lip
        s["room"] = "main"
        s["light"] = round(light if light is not None else min(1.0, max(LIGHT_FLOOR, float(s["light"]) * LIGHT_GAIN)), 3)
        if nm in RAIN_IN:
            s["rain"] = True
        else:
            s.pop("rain", None)
        if nm in WET:
            s["wet"] = WET[nm]
        else:
            s.pop("wet", None)
        s["room_name"] = nm  # (readable by the Magic rave's authoring; the engine ignores unknown keys)
        for k in ("floor_tex", "wall_tex", "ceil_tex", "step_tex", "lip_tex"):
            used[s[k]] = True
    for w in d["walls"]:
        for k in ("lower_tex", "upper_tex"):
            w[k] = ""  # the sector's step_tex / lip_tex decide (the converter's placeholder trim is not wanted)
    tex = {k: OWN + k + ".png" for k in OWN_TEX}
    for who in GUIDES:
        for st, n in STATES.items():
            for i in range(n):
                tex["guide_%s_%s_%d" % (who, st, i)] = GUIDE_OWN[who] + "guide_%s_%s_%d.png" % (who, st, i)
    d["textures"] = tex
    d["max_step"] = MAX_STEP
    d["visibility"] = {"mode": "clip", "depth": 48, "far": 0}
    barriers(d)
    d["sky"] = {}
    d["fog"] = {"color": "#2a1608", "density": 0.016}
    d["weather"] = {"rain": 0.8, "wind": 6}  # stage D: the painting's rain in the street beyond the Dock door (only `ahead_street` lets it in: RAIN_IN)
    d["palette_weight"] = 1.0
    keep = [w for w in d["waypoints"] if not w["id"].startswith("lg_")]
    for wid, at, look, hold, _why in WAYPOINTS:
        at = (float(at[0]), float(at[1]))
        x, z = m(*at)
        s = sector_of(d, x, z)
        floor0 = s["floor"] if s else None
        margin = MARGIN
        if s is None or dist_to_edges(s["polygon"], x, z) < margin:
            best = None
            for r in range(1, 41):
                for k in range(16):
                    a = 2 * math.pi * k / 16
                    qx, qz = x + math.cos(a) * r * 0.1, z + math.sin(a) * r * 0.1
                    q = sector_of(d, qx, qz)
                    if q is not None and (floor0 is None or abs(q["floor"] - floor0) < 0.01) and dist_to_edges(q["polygon"], qx, qz) >= margin + 0.02:
                        best = (qx, qz, q)
                        break
                if best:
                    break
            if best is None:
                raise SystemExit("waypoint %s at %s: no free spot within 4 m" % (wid, at))
            print("  %s moved %.1f m off a piece edge" % (wid, math.hypot(best[0] - x, best[1] - z)))
            x, z, s = round(best[0], 4), round(best[1], 4), best[2]
            at = (x * 32.0, -z * 32.0)
        wp = {"id": wid, "at": [x, z], "yaw": face(at, look), "sector": s["id"]}
        if hold:
            wp["hold_bars"] = hold
        keep.append(wp)
    d["waypoints"] = keep
    ref = next(w for w in keep if w["id"] == "lg_ref")
    for w in keep:
        if w["id"] == "doom_start":
            w["at"], w["yaw"], w["sector"] = list(ref["at"]), ref["yaw"], ref["sector"]
    # things
    things = [t for t in d["things"] if not str(t["id"]).startswith("lg_")]
    for who, (at, size, lamp) in GUIDES.items():
        x, z = m(*at)
        things.append({"id": "lg_guide_" + who, "kind": "billboard", "sprite": "guide_%s_idle_0" % who, "at": [x, z], "y": round(size * 0.5, 3), "size": size, "anim": "none"})
    for tid, spr, at, y, size in THINGS:
        x, z = m(*at)
        things.append({"id": tid, "kind": "billboard", "sprite": spr, "at": [x, z], "y": y, "size": size, "anim": "none"})
    for lid, at, y, rad, col, st in LIGHTS:
        x, z = m(*at)
        things.append({"id": lid, "kind": "light", "at": [x, z], "y": y, "radius": round(rad * 1.3, 1), "color": col, "strength": round(min(2.5, st * LAMP_GAIN), 2)})
    for who, (at, size, lamp) in GUIDES.items():  # the lamp over each guide (the choice layer brightens it)
        x, z = m(*lamp)
        things.append({"id": "lg_lamp_" + who, "kind": "light", "at": [x, z], "y": 2.8, "radius": 3.0, "color": "#ffd9a0", "strength": 0.6})
    for did, spr, at, y, size, emi in DECALS:
        x, z = m(*at)
        sec = sector_of(d, x, z)
        if sec is None:
            raise SystemExit("decal %s at %s is in no sector" % (did, at))
        t = {"id": did, "kind": "decal", "sprite": spr, "at": [x, z], "y": y, "size": size}
        if emi:
            t["emissive"] = True
        things.append(t)
    for t in things:
        if t.get("kind") == "billboard":
            t.pop("sector", None)
    d["things"] = things
    spots = {k: v for k, v in d.get("spots", {}).items() if not k.startswith("lg_")}
    for who, (at, size, lamp) in GUIDES.items():
        x, z = m(*at)
        spots["lg_guide_" + who] = {"sector": sector_of(d, x, z)["id"], "at": [x, z]}
    d["spots"] = spots
    d["homes"], d["silhouettes"] = [], []  # the painting's lounge has no crowd: the three guides are the people (the world's story has an empty cast: tools/run/make_doom_lounge.py)
    d["scene"] = {"id": "doom_lounge", "reference": "art/reference/doom_worlds/Mustard octagonal lounge of three routes-2.png", "routes": ROUTES,
                  "note": "authored by tools/doom/author_lounge.py; routes are lists of waypoint ids (via points included); hold_bars on a waypoint is the still hold at a choice window"}
    d["doom"]["authored"] = True
    json.dump(d, open(MAP, "w", encoding="utf-8", newline="\n"), indent=1)
    open(MAP, "a", encoding="utf-8", newline="\n").write("\n")
    print("authored %d waypoints, %d things, %d spots into %s" % (len(WAYPOINTS), len(things), len(spots), MAP))


if __name__ == "__main__":
    sys.exit(main())
