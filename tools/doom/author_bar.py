"""Authors the Copper Bar into content/story/maps/doom_bar.json (docs/doom/scenes/bar.md), on the Warehouse pilot's pipeline (tools/doom/author_warehouse.py).

    python -I tools/doom/trace/bar_scene.py; python -I tools/doom/convert.py --scene bar --trace tools/doom/trace/bar_pilot.json     # the geometry (this script's input)
    python -I tools/doom/art/make_bar_art.py; python -I tools/doom/art/make_bar_guides.py                                           # the art (assets/story/doom_bar/textures)
    python -I tools/doom/author_bar.py                                                           # waypoints, textures, decals, things, lights, spots, cast (idempotent; run after every convert)

All coordinates below are METRES (x east, y north, the way the painting's camera looks), converted to the map's frame like convert.py does (x_m = x, z_m = -y). A waypoint names the
sector that holds it and keeps MARGIN from every piece edge (it moves to the nearest free spot of the same floor when it does not, and says so).
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import author_warehouse as aw  # noqa: E402  (the pure helpers: inside, dist_to_edges, sector_of, lift)

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
MAP = os.path.join(ROOT, "content", "story", "maps", "doom_bar.json")
TRACE = os.path.join(HERE, "trace", "bar_pilot.json")
OWN = "textures/"
MARGIN = 0.45
MAX_STEP = 0.5
RAIL_TEX = "bar_railing"
RAIL_HEIGHT = 1.0
STATES = {"idle": 1, "available": 5, "selected": 2, "committed": 2}
LIGHT_GAIN, LIGHT_FLOOR, TINT_LIFT, LAMP_GAIN = 2.0, 0.66, 0.7, 2.5  # exposure (the Warehouse's figures; A1's night interior median is 0.25 to 0.38 under the renderer's own fog)


def mz(x, y):
    return (round(x, 4), round(-y, 4))


def face(a, b):
    """The yaw of a view from point a towards point b (metres, y north): 0 faces north (-z), 90 faces west."""
    return round(math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1])), 1)


# id, point (m), look-at point (m), hold_bars (0 = a moving place), what it is. wb_v_* are via points (corners of the polyline moves), never stood on.
WAYPOINTS = [
    ("wb_arrive", (-6.2, 1.5), (0.0, 1.5), 0, "arrival: the west end of the way from the Floor, facing east (you came in from the Floor); a walk to the reference viewpoint"),
    ("wb_ref", (0.1, -0.5), (0.1, 5.0), 8, "THE reference viewpoint: the south end of the passage looking north: the stairs to the booth ahead, the Floor way left, the bar and the lounge right"),
    ("wb_bridge", (2.0, 4.3), (2.0, 10.0), 2, "reveal: on the first grate crossing looking up the channel, the bar nook right, the stairs left"),
    ("wb_counter", (2.6, 2.8), (6.5, 2.0), 2, "reveal: in the bar looking along the counter, taps, bottles and pendants"),
    ("wb_way", (-4.8, 1.4), (-8.0, 1.4), 2, "reveal: in the way to the Floor looking west at its blue door"),
    ("wb_stairs_foot", (0.1, 5.4), (0.1, 10.0), 0, "ahead, leg 1: the foot of the four stairs, the booth above"),
    ("wb_booth_door", (0.1, 9.3), (0.2, 11.4), 0, "THRESHOLD ahead: on the booth landing before the desk; the world transition happens here"),
    ("wb_floor_door", (-5.8, 1.4), (-8.0, 1.4), 0, "THRESHOLD left: in the way to the Floor, before its blue door"),
    ("wb_chill_door", (3.2, 4.3), (4.2, 5.6), 0, "THRESHOLD right: over the crossing, at the Chill-out nook's step"),
    ("wb_ref_back", (0.6, -2.3), (0.1, 5.0), 0, "recovery: a stumble back into the passage's end"),
    ("wb_sw_corner", (-1.2, -2.1), (0.1, 5.0), 0, "recovery: against the west wall"),
    # via points
    ("wb_v_pass_e", (0.7, 4.3), (2.0, 4.3), 0, "via: the passage's east side, level with the first crossing"),
    ("wb_v_pass_n", (0.7, 2.8), (2.6, 2.8), 0, "via: the passage, level with the bar's front"),
    ("wb_v_jamb", (-0.6, 1.4), (-4.0, 1.4), 0, "via: the passage in front of the way to the Floor"),
]
ROUTES = {
    "ahead": ["wb_stairs_foot", "wb_booth_door"],
    "left": ["wb_v_jamb", "wb_floor_door"],
    "right": ["wb_v_pass_e", "wb_chill_door"],
    "stay": ["wb_v_pass_e", "wb_bridge", "wb_v_pass_e", "wb_v_pass_n", "wb_counter", "wb_v_pass_n", "wb_v_jamb", "wb_way", "wb_v_jamb", "wb_ref"],
    "arrive": ["wb_arrive", "wb_v_jamb", "wb_ref"],
    "stumble": ["wb_ref_back", "wb_sw_corner", "wb_ref"],
}
# sector (by the trace's name) -> floor, wall, ceiling texture, tint, step_tex (the riser drawn where a lower neighbour meets it)
STYLE = {
    "pass": ("bar_cobble", "bar_brick", "bar_ceiling", "#9a8cd8", "bar_quay"),
    "way_w": ("bar_cobble", "bar_brick", "bar_ceiling", "#7a90ff", "bar_quay"),
    "booth": ("bar_planks", "bar_brick", "bar_ceiling", "#a8e8f0", "bar_step"),
    "desk": ("bar_copper", "bar_brick", "bar_ceiling", "#ffc890", "bar_counter_front"),
    "booth_back": ("bar_planks", "bar_booth_wall", "bar_ceiling", "#a8e8f0", "bar_step"),
    "counter": ("bar_copper", "bar_brick_lit", "bar_ceiling", "#ffc080", "bar_counter_front"),
    "lounge_n": ("bar_planks", "bar_brick_lit", "bar_ceiling", "#ffd090", "bar_quay"),
}
for k in ("stair_1", "stair_2", "stair_3", "stair_4"):
    STYLE[k] = ("bar_step", "bar_brick", "bar_ceiling", "#c0b0e8", "bar_step")
for k in ("chan_a", "chan_b", "chan_c"):
    STYLE[k] = ("bar_water", "bar_quay", "bar_ceiling", "#60c8c8", "bar_quay")
for k in ("bridge_1", "bridge_2"):
    STYLE[k] = ("bar_grate", "bar_quay", "bar_ceiling", "#c8b0a0", "bar_quay")
for k in ("bar_w", "bar_back", "bar_e", "bar_front"):
    STYLE[k] = ("bar_planks", "bar_brick_lit", "bar_ceiling", "#ffc080", "bar_step")
OWN_TEX = ["bar_brick", "bar_brick_lit", "bar_cobble", "bar_planks", "bar_step", "bar_counter_front", "bar_copper", "bar_water", "bar_grate", "bar_quay", "bar_ceiling", "bar_booth_wall", "bar_railing",
           "bar_pendant", "bar_lantern", "bar_crate", "bar_crate_tall", "bar_jug", "bar_stool", "bar_taps", "bar_bottles", "bar_bottles_b", "bar_glass", "bar_pipe_col", "bar_sofa",
           "bar_tapestry", "bar_poster_a", "bar_poster_b", "bar_sign_booth", "bar_sign_floor", "bar_sign_chill", "bar_shelf", "bar_ivy", "bar_pipe_h", "bar_rack", "bar_window", "bar_door_floor",
           "bar_curtain"]
GUIDES = {  # id suffix: point (m), height (m), lamp point (m)
    "booth": ((0.2, 11.4), 1.8, (0.2, 11.0)),
    "floor": ((-2.5, 3.0), 1.8, (-2.5, 2.6)),
    "chill": ((4.2, 5.6), 1.8, (4.2, 5.2)),
}
# decals (pictures on a wall: kind "decal"): id, sprite, point (m, within 0.35 m of a solid wall of its sector), y (bottom edge above the floor), height (m), emissive
DECALS = [
    ("bar_d_tapestry_w", "bar_tapestry", (-1.75, 5.05), 0.75, 2.1, False), ("bar_d_lantern_w", "bar_lantern", (-1.75, 4.0), 1.55, 0.7, True),
    ("bar_d_pipe_w1", "bar_pipe_h", (-1.75, -1.0), 2.7, 0.34, False), ("bar_d_pipe_w2", "bar_pipe_h", (-1.75, 4.9), 2.85, 0.3, False),
    ("bar_d_poster_a", "bar_poster_a", (-1.75, -2.1), 1.0, 0.95, False), ("bar_d_poster_b", "bar_poster_b", (-1.75, -0.4), 1.05, 0.95, False),
    ("bar_d_ivy", "bar_ivy", (-1.75, 0.5), 1.0, 2.2, False), ("bar_d_poster_e", "bar_poster_b", (1.35, -1.6), 1.0, 0.95, False),
    ("bar_d_sign_floor", "bar_sign_floor", (-1.75, 3.95), 2.45, 0.42, True),
    ("bar_d_lantern_s", "bar_lantern", (-1.15, 7.0), 2.0, 0.7, True),
    ("bar_d_window", "bar_window", (0.1, 12.55), 0.85, 1.0, True), ("bar_d_sign_booth", "bar_sign_booth", (0.1, 12.55), 2.55, 0.5, True),
    ("bar_d_rack_w", "bar_rack", (-1.15, 11.6), 0.4, 1.5, True), ("bar_d_rack_e", "bar_rack", (1.35, 11.6), 0.4, 1.5, True),
    ("bar_d_shelf", "bar_shelf", (4.9, 0.25), 0.7, 1.6, False), ("bar_d_pipe_bar", "bar_pipe_h", (2.3, 0.25), 2.5, 0.34, False),
    ("bar_d_poster_bar", "bar_poster_a", (6.95, 2.8), 1.1, 0.9, False),
    ("bar_d_tapestry_n", "bar_tapestry", (6.95, 4.2), 0.9, 1.8, False), ("bar_d_curtain", "bar_curtain", (6.95, 6.0), 0.1, 2.3, False),
    ("bar_d_tapestry_s", "bar_tapestry", (6.95, 7.8), 0.9, 1.8, False), ("bar_d_sign_chill", "bar_sign_chill", (4.8, 8.55), 2.55, 0.42, True),
    ("bar_d_door_floor", "bar_door_floor", (-6.95, 2.25), 0.0, 2.3, True), ("bar_d_pipe_way", "bar_pipe_h", (-4.4, 3.55), 2.5, 0.3, False),
    ("bar_d_ivy_way", "bar_ivy", (-3.2, 3.55), 0.6, 2.3, False),
]
THINGS = [  # extra dressing, billboards: id, sprite, point (m), y (centre above the sector's floor), height (m)
    ("bar_pendant_c1", "bar_pendant", (3.8, 1.9), 2.55, 1.0), ("bar_pendant_c2", "bar_pendant", (5.0, 1.9), 2.55, 1.0), ("bar_pendant_c3", "bar_pendant", (6.2, 1.9), 2.55, 1.0),
    ("bar_pendant_l", "bar_pendant", (4.6, 5.0), 2.6, 1.0), ("bar_pendant_p", "bar_pendant", (1.0, 1.6), 2.7, 0.9), ("bar_pendant_b", "bar_pendant", (-0.3, 4.6), 2.7, 0.9),
    ("bar_taps", "bar_taps", (4.6, 1.85), 0.3, 0.62), ("bar_bottles", "bar_bottles", (3.7, 1.85), 0.25, 0.5), ("bar_bottles_b", "bar_bottles_b", (6.0, 1.85), 0.25, 0.5),
    ("bar_glass", "bar_glass", (5.5, 2.0), 0.1, 0.2), ("bar_jug", "bar_jug", (4.0, 1.8), 0.25, 0.5),
    ("bar_stool_1", "bar_stool", (3.4, 2.75), 0.45, 0.9), ("bar_stool_2", "bar_stool", (4.4, 2.75), 0.45, 0.9), ("bar_stool_3", "bar_stool", (5.4, 2.75), 0.45, 0.9), ("bar_stool_4", "bar_stool", (6.3, 2.75), 0.45, 0.9),
    ("bar_col_a", "bar_pipe_col", (-1.62, 3.75), 1.6, 3.2), ("bar_crate_a", "bar_crate_tall", (-1.15, 3.95), 0.55, 1.1), ("bar_crate_b", "bar_crate", (-0.75, 3.95), 0.3, 0.6),
    ("bar_jug_c", "bar_jug", (-1.15, 3.95), 1.32, 0.45), ("bar_col_b", "bar_pipe_col", (1.3, 0.1), 1.6, 3.2), ("bar_crate_c", "bar_crate", (1.0, -2.5), 0.3, 0.6),
    ("bar_sofa", "bar_sofa", (5.9, 5.9), 0.5, 1.0),
]
LIGHTS = [  # id, point (m), y, radius, colour, strength: warm practical lamps (pendants, lanterns) against cool depths (teal water, blue way, violet passage)
    ("bar_lt_counter", (4.8, 1.9), 2.6, 6.5, "#ffa84a", 1.8), ("bar_lt_front", (3.4, 2.9), 3.0, 5.0, "#ffb860", 1.4),
    ("bar_lt_lounge", (5.0, 5.5), 2.8, 6.0, "#ffb860", 1.6), ("bar_lt_lounge2", (6.2, 7.2), 2.6, 4.5, "#ff9a50", 1.2),
    ("bar_lt_pass", (1.0, 1.5), 2.8, 8.0, "#ffb050", 1.4), ("bar_lt_lantern_w", (-1.5, 4.0), 2.2, 5.5, "#ffa040", 1.6), ("bar_lt_ref", (0.0, -1.0), 2.8, 8.0, "#8a70e0", 1.2),
    ("bar_lt_stairs", (-0.8, 7.0), 2.6, 6.0, "#ffb050", 1.3), ("bar_lt_chan_a", (2.0, 4.3), 0.4, 5.5, "#2ab6b0", 1.4), ("bar_lt_chan_b", (2.0, 8.3), 0.6, 5.5, "#2ab6b0", 1.3),
    ("bar_lt_way", (-5.0, 2.2), 2.6, 7.0, "#4a6aff", 1.7), ("bar_lt_booth", (0.1, 9.4), 3.2, 6.0, "#40d0d8", 1.3), ("bar_lt_booth_red", (0.1, 12.0), 2.6, 4.0, "#ff4a3a", 0.9),
]
CAST = {"actors": ["c01", "c02", "c03", "c04", "c05", "c06", "c07"], "silhouettes": ["s01", "s02", "s03"]}
HOMES = {"c01": (3.8, 0.8), "c02": (4.8, 0.8), "c03": (5.8, 3.05), "c04": (6.4, 3.05), "c05": (6.4, 4.2), "c06": (6.2, 7.6), "c07": (3.4, 7.8)}  # (none stands in the picture at the reference viewpoint but the two far ones in the nook: the counter and the stools are the foreground)
SILS = {"s01": (6.5, 6.0), "s02": (2.4, 1.0), "s03": (5.0, 0.8)}


def barriers(d):
    """Closes what a walker must not cross and puts the railing where the painting's channel has its banks.
    * A portal whose floors differ by more than MAX_STEP is a drop and is shut to walkers (`blocked`: the channel's banks, the counter's sides, the booth desk) as long as every sector stays
      reachable from the start through the portals that are left (the map loader demands that): the channel, the counter and the booth behind the desk each keep one open portal, the
      one farthest from the middle (a dead end: no route goes through it, and the rail check never puts a camera there).
    * The long banks of the channel (the passage, the stairs, the booth landing and the Chill-out nook above the water) are the renderer's `railing` kind: a see-through copper lattice.
      The sides of the two grated crossings stay open drops without a rail (the painting has none)."""
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
    for w in walls:
        a, b = sec[w["sector"]], sec[w["portal"]]
        na, nb = a["name"], b["name"]
        chan = [n for n in (na, nb) if n.startswith("chan")]
        other = [n for n in (na, nb) if not n.startswith("chan")]
        if w.get("blocked") and chan and other and not other[0].startswith("bridge"):
            w["kind"], w["tex"], w["height"] = "railing", RAIL_TEX, RAIL_HEIGHT


def main():
    d = json.load(open(MAP, encoding="utf-8"))
    names = json.load(open(TRACE, encoding="utf-8"))["sector_names"]
    d["art"] = "doom_bar"
    for s in d["sectors"]:
        s["name"] = names[int(s["doom_sector"])]
        f, w, c, tint, step = STYLE[s["name"]]
        s["floor_tex"], s["wall_tex"], s["ceil_tex"], s["tint"], s["step_tex"] = f, w, c, _lift(tint), step
        s["room"] = "main"
        s["light"] = round(min(1.0, max(LIGHT_FLOOR, float(s["light"]) * LIGHT_GAIN)), 3)
    tex = {k: OWN + k + ".png" for k in OWN_TEX}
    for who in GUIDES:
        for st, n in STATES.items():
            for i in range(n):
                tex["guide_%s_%s_%d" % (who, st, i)] = OWN + "guide_%s_%s_%d.png" % (who, st, i)
    d["textures"] = tex
    d["max_step"] = MAX_STEP
    d["visibility"] = {"mode": "clip", "depth": 48, "far": 0}
    barriers(d)
    for w in d["walls"]:  # the converter's `trim` riser and lip: the sectors' own step_tex / lip_tex draw them (docs/story/HEIGHTS_AND_PATHS.md)
        for k in ("lower_tex", "upper_tex"):
            if w.get(k) == "trim":
                del w[k]
    for s in d["sectors"]:
        s["lip_tex"] = "bar_brick"
        s.pop("name", None)
    d["sky"] = {}
    d["fog"] = {"color": "#2a1838", "density": 0.032}
    d["palette_weight"] = 1.0
    # waypoints
    keep = [w for w in d["waypoints"] if not w["id"].startswith("wb_")]
    for wid, at, look, hold, _why in WAYPOINTS:
        x, z = mz(*at)
        s = aw.sector_of(d, x, z)
        floor0 = s["floor"] if s else None
        if s is None or aw.dist_to_edges(s["polygon"], x, z) < MARGIN:
            best = None
            for r in range(1, 41):
                for k in range(16):
                    a = 2 * math.pi * k / 16
                    qx, qz = x + math.cos(a) * r * 0.1, z + math.sin(a) * r * 0.1
                    q = aw.sector_of(d, qx, qz)
                    if q is not None and (floor0 is None or abs(q["floor"] - floor0) < 0.01) and aw.dist_to_edges(q["polygon"], qx, qz) >= MARGIN + 0.02:
                        best = (qx, qz, q)
                        break
                if best:
                    break
            if best is None:
                raise SystemExit("waypoint %s at %s: no free spot within 4 m" % (wid, at))
            print("  %s moved %.1f m off a piece edge" % (wid, math.hypot(best[0] - x, best[1] - z)))
            x, z, s = round(best[0], 4), round(best[1], 4), best[2]
            at = (x, -z)
        w = {"id": wid, "at": [x, z], "yaw": face(at, look), "sector": s["id"]}
        if hold:
            w["hold_bars"] = hold
        keep.append(w)
    d["waypoints"] = keep
    # things: guides, billboards, decals, lights, lamps
    things = [t for t in d["things"] if not str(t["id"]).startswith("bar_") and not str(t["id"]).startswith("wb_")]
    for who, (at, size, lamp) in GUIDES.items():
        x, z = mz(*at)
        things.append({"id": "wb_guide_" + who, "kind": "billboard", "sprite": "guide_%s_idle_0" % who, "at": [x, z], "y": round(size * 0.5, 3), "size": size, "anim": "none"})
    for tid, spr, at, y, size in THINGS:
        x, z = mz(*at)
        things.append({"id": tid, "kind": "billboard", "sprite": spr, "at": [x, z], "y": y, "size": size, "anim": "none"})
    for tid, spr, at, y, size, emi in DECALS:
        x, z = mz(*at)
        t = {"id": tid, "kind": "decal", "sprite": spr, "at": [x, z], "y": y, "size": size}
        if emi:
            t["emissive"] = True
        things.append(t)
    for lid, at, y, rad, col, st in LIGHTS:
        x, z = mz(*at)
        things.append({"id": lid, "kind": "light", "at": [x, z], "y": y, "radius": round(rad * 1.3, 1), "color": col, "strength": round(min(2.5, st * LAMP_GAIN), 2)})
    for who, (at, size, lamp) in GUIDES.items():  # the lamp over each guide: a light thing the choice layer brightens (hotspot show.light names it)
        x, z = mz(*lamp)
        things.append({"id": "wb_lamp_" + who, "kind": "light", "at": [x, z], "y": 2.8 if who != "booth" else 3.6, "radius": 3.0, "color": "#ffd9a0", "strength": 0.6})
    d["things"] = things
    spots = {k: v for k, v in d.get("spots", {}).items() if not k.startswith("wb_")}
    for who, (at, size, lamp) in GUIDES.items():
        x, z = mz(*at)
        spots["wb_guide_" + who] = {"sector": aw.sector_of(d, x, z)["id"], "at": [x, z]}
    d["spots"] = spots
    # the cast: a few patrons of the Night One chapter (copied to content/run/doom/story_doom_bar.json, the world's StoryData) at the stools and in the nook, no events
    ch = json.load(open(os.path.join(ROOT, "content", "story", "night_one.json"), encoding="utf-8"))
    ch["id"], ch["title"] = "doom_bar", "Doom Bar (the Copper Bar)"
    ch["art"] = "night_one"
    ch["actors"] = [a for a in ch["actors"] if a["id"] in CAST["actors"]]
    ch["silhouettes"] = [s for s in ch["silhouettes"] if s["id"] in CAST["silhouettes"]]
    for a in ch["actors"]:
        a["group"] = "core"
    ch["groups"] = {"circle": [], "all": [a["id"] for a in ch["actors"]]}
    for b in ch["blocks"]:
        b["events"] = []
    for dec in ch["decisions"]:
        for k in ("good", "bad"):
            dec[k] = [e for e in dec.get(k, []) if not (isinstance(e, dict) and e.get("action"))]
    for e in ch["endings"].values():
        e["journey"] = []
    open(os.path.join(ROOT, "content", "run", "doom", "story_doom_bar.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(ch, indent=1) + "\n")
    d["homes"] = []
    for aid, at in HOMES.items():
        x, z = mz(*at)
        s = aw.sector_of(d, x, z)
        assert s is not None and aw.dist_to_edges(s["polygon"], x, z) >= 0.32, "home %s at %s too near an edge" % (aid, at)
        d["homes"].append({"actor": aid, "sector": s["id"], "at": [x, z]})
    d["silhouettes"] = []
    for sid, at in SILS.items():
        x, z = mz(*at)
        d["silhouettes"].append({"id": sid, "at": [x, z]})
    d["scene"] = {"id": "doom_bar", "reference": "art/reference/doom_worlds/Copper Basement Bar, Three Hidden Routes-3.png", "routes": ROUTES,
                  "note": "authored by tools/doom/author_bar.py; routes are lists of waypoint ids; hold_bars on a waypoint is the still hold at a choice window"}
    d["doom"]["authored"] = True
    json.dump(d, open(MAP, "w", encoding="utf-8", newline="\n"), indent=1)
    open(MAP, "a", encoding="utf-8", newline="\n").write("\n")
    print("authored %d waypoints, %d things, %d decals, %d spots into %s" % (len(WAYPOINTS), len(things), len(DECALS), len(spots), MAP))


def _lift(h):
    return "#%02x%02x%02x" % tuple(int(v + (255 - v) * TINT_LIFT) for v in (int(h[i:i + 2], 16) for i in (1, 3, 5)))


if __name__ == "__main__":
    sys.exit(main())
