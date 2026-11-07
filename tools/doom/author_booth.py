"""Authors the DJ Booth scene into content/story/maps/doom_booth.json (docs/doom/scenes/booth.md), the Warehouse pilot's pipeline (tools/doom/author_warehouse.py) for MAP04.

    python -I tools/doom/trace/booth_scene.py; python -I tools/doom/convert.py --scene booth --trace tools/doom/trace/booth_pilot.json     # the geometry (this script's input)
    python -I tools/doom/author_booth.py                                                          # waypoints, textures, things, decals, lights, spots (idempotent; run after every convert)

Coordinates in this file are METRES (x east, y north, as the trace) and are turned into the map's (x, z = -y) by `M`. A waypoint names the sector that holds it and keeps the 0.5 m margin
StoryMap wants (0.33 in the narrow door pieces); the script moves nothing but a point too close to a wall, and says so.

Routes are lists of waypoint ids (`ROUTES`); tools/run/make_doom_booth.py cuts them into the rail's polyline moves. `hold_bars` on a waypoint is the number of bars the camera holds still.
"""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MAP = os.path.join(ROOT, "content", "story", "maps", "doom_booth.json")
TRACE = os.path.join(ROOT, "tools", "doom", "trace", "booth_pilot.json")
NIGHT = "res://assets/story/night_one/textures/"
OWN = "textures/"
MARGIN = 0.5
MARGINS = {"bt_bal_door": 0.33, "bt_v_door": 0.33, "bt_v_dockdoor": 0.33, "bt_hatch": 0.45}
MAX_STEP = 0.5
RAIL_HEIGHTS = {"dais|aisle": 1.0, "dais|terrace": 1.75, "dstep_a|terrace": 2.375, "dstep_b|terrace": 2.0}  # metres above the higher floor (the window tops out at the 2.75 m ceiling)
RAIL_TEX = {"dais|aisle": "bt_rail"}  # every other railing is the window mesh
WINDOW_TEX = "bt_window"
LIGHT_GAIN, LIGHT_FLOOR, TINT_LIFT, LAMP_GAIN = 1.6, 0.66, 0.6, 2.2  # exposure (A1 night interior): the Doom lights are low for this renderer, so each sector is lit at least LIGHT_FLOOR


def M(x, y):
    return (round(x, 4), round(-y, 4))


def face(a, b):
    """The yaw of a view from the point a (metres, x east, y north) towards b (0 faces north / -z, 90 faces -x)."""
    return round(math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1])), 1)


# id, point (m), look-at point (m), hold_bars (0 = a moving place), what it is.  Names starting bt_v_ are via points only: corners of the polyline moves, never stood on.
WAYPOINTS = [
    ("bt_arrive", (0.9, 0.5), (0.5, 11), 0, "arrival: the south end of the aisle (a cut, then a three bar walk to the reference viewpoint)"),
    ("bt_ref", (0.5, 1.9), (0.5, 11), 8, "THE reference viewpoint: the aisle's south end looking north, the window and the balcony guide left, the dock door and its guide right, the hatch and the mothership guide ahead"),
    ("bt_ref_back", (1.1, 0.6), (0.5, 11), 0, "recovery: a stumble back into the corner"),
    ("bt_sw_corner", (-1.1, 1.0), (0.5, 11), 0, "recovery: along the desk"),
    ("bt_hatch_view", (0.0, 8.0), (0.0, 17), 2, "reveal: down the aisle at the hatch, the violet chamber and its guide"),
    ("bt_window_view", (-2.9, 9.8), (-7.5, 6.0), 2, "reveal: the landing at the balcony door, the rain and the iron balcony through the double door and the window"),
    ("bt_dock_view", (1.1, 4.2), (6.5, 4.4), 2, "reveal: against the aisle's east wall looking through the open steel door into the dock"),
    ("bt_hatch", (0.0, 11.5), (0.0, 17), 1, "THRESHOLD ahead (Mothership): in the hatch, the world transition happens here"),
    ("bt_bal_top", (-9.1, 9.75), (-9.1, 3), 1, "THRESHOLD left (Balcony): the top of the balcony stair, the world transition happens here"),
    ("bt_dock_in", (3.6, 4.25), (8.5, 4.5), 1, "THRESHOLD right (Dock): through the steel door onto the dock, the world transition happens here"),
    # via points (corners of the polyline moves)
    ("bt_v_a1", (0.0, 5.0), (0.0, 8), 0, "via: the aisle, mid way"),
    ("bt_v_a2", (-0.5, 9.6), (-2.9, 9.8), 0, "via: the aisle's north end, at the landing"),
    ("bt_v_a3", (-0.4, 8.7), (1.1, 4.2), 0, "via: the aisle north of the desk's stairs"),
    ("bt_v_a4", (0.9, 3.0), (0.5, 1.9), 0, "via: the aisle, south of the dock door"),
    ("bt_v_a5", (0.0, 9.6), (0.0, 11.5), 0, "via: the aisle's north end, before the hatch"),
    ("bt_v_land", (-2.9, 9.75), (-4.4, 9.75), 0, "via: the landing"),
    ("bt_v_door", (-4.375, 9.75), (-5.4, 9.75), 0, "via: the balcony double door"),
    ("bt_v_porch", (-5.4, 9.75), (-6.6, 9.75), 0, "via: the balcony porch"),
    ("bt_v_step_a", (-6.625, 9.75), (-7.9, 9.75), 0, "via: the first stair step"),
    ("bt_v_step_b", (-7.875, 9.75), (-9.1, 9.75), 0, "via: the second stair step"),
    ("bt_v_dock_a", (1.0, 4.25), (2.125, 4.25), 0, "via: the aisle in front of the dock door"),
    ("bt_v_dockdoor", (2.125, 4.25), (3.6, 4.25), 0, "via: the dock door"),
]
ROUTES = {
    "ahead": ["bt_v_a1", "bt_v_a5", "bt_hatch"],
    "left": ["bt_v_a2", "bt_v_land", "bt_v_door", "bt_v_porch", "bt_v_step_a", "bt_v_step_b", "bt_bal_top"],
    "right": ["bt_v_dock_a", "bt_v_dockdoor", "bt_dock_in"],
    "stay": ["bt_v_a1", "bt_hatch_view", "bt_v_a2", "bt_window_view", "bt_v_a3", "bt_dock_view", "bt_v_a4", "bt_ref"],
    "arrive": ["bt_arrive", "bt_ref"],
    "stumble": ["bt_ref_back", "bt_sw_corner", "bt_ref"],
}
# sector name -> floor, wall, ceiling texture, tint, step_tex (the riser of a step up onto it)
STYLE = {
    "aisle": ("bt_floor_grate", "bt_wall_foam", "bt_ceil", "#ffc890", "bt_wall_steel"),
    "dais": ("bt_floor_plate", "bt_wall_foam", "bt_ceil", "#ffc080", "bt_wall_steel"),
    "dstep_a": ("bt_floor_plate", "bt_wall_steel", "bt_ceil", "#ffc080", "bt_wall_steel"),
    "dstep_b": ("bt_floor_plate", "bt_wall_steel", "bt_ceil", "#ffc080", "bt_wall_steel"),
    "landing": ("bt_floor_grate", "bt_wall_foam", "bt_ceil", "#ffc890", "bt_wall_steel"),
    "bal_door": ("bt_floor_plate", "bt_wall_steel", "bt_ceil", "#ffc890", "bt_wall_steel"),
    "porch": ("bt_floor_plate", "bt_wall_dock", "bt_ceil", "#9ab0f0", "bt_wall_steel"),
    "terrace": ("bt_floor_plate", "bt_wall_dock", "bt_ceil", "#8aa0e8", "bt_wall_steel"),
    "bal_step_a": ("bt_floor_plate", "bt_wall_dock", "bt_ceil", "#9ab0f0", "bt_wall_steel"),
    "bal_step_b": ("bt_floor_plate", "bt_wall_dock", "bt_ceil", "#9ab0f0", "bt_wall_steel"),
    "bal_top": ("bt_floor_plate", "bt_wall_dock", "bt_ceil", "#9ab0f0", "bt_wall_steel"),
    "hatch": ("bt_floor_plate", "bt_wall_steel", "bt_ceil", "#d0b0ff", "bt_wall_steel"),
    "moth": ("bt_floor_moth", "bt_wall_moth", "bt_ceil", "#c8a8ff", "bt_wall_steel"),
    "dock_door": ("bt_floor_plate", "bt_wall_steel", "bt_ceil", "#ffc080", "bt_wall_steel"),
    "dock": ("bt_floor_conc", "bt_wall_dock", "bt_ceil", "#ffb870", "bt_wall_steel"),
}
BORROWED = ["thing_pendant", "trim"]
STATES = {"idle": 1, "available": 5, "selected": 2, "committed": 2}
GUIDES = {  # id suffix: point (m), size (height m), lamp point (m)
    "mothership": ((0.25, 14.2), 2.2, (-0.7, 14.2)),
    "balcony": ((-5.6, 7.8), 2.2, (-5.6, 7.0)),
    "dock": ((4.0, 6.8), 2.2, (4.9, 6.8)),
}
# billboards: id, sprite, point (m), size (height m); y is the centre (half the size) unless a fifth value is given (height of the centre above the floor)
THINGS = [
    ("bt_deck_a", "bt_turntable", (-3.2, 1.2), 0.5), ("bt_mixer", "bt_mixer", (-3.2, 2.6), 0.55), ("bt_deck_b", "bt_turntable", (-3.2, 4.0), 0.5),
    ("bt_desk_lamp", "bt_lamp", (-3.6, 5.2), 0.9), ("bt_stool", "bt_stool", (-2.55, 3.2), 0.75), ("bt_records", "bt_records", (-3.55, 0.55), 0.5),
    ("bt_dais_cables", "bt_cables", (-2.4, 0.7), 0.4), ("bt_deck_c", "bt_turntable", (-3.2, 6.4), 0.5),
    ("bt_rack_a", "bt_rack", (1.35, 7.4), 1.5), ("bt_rack_b", "bt_rack", (1.35, 8.7), 1.5), ("bt_case_a", "bt_case", (1.3, 9.9), 0.7), ("bt_case_b", "bt_case", (1.3, 1.0), 0.6),
    ("bt_floor_cables", "bt_cables", (0.7, 6.4), 0.35), ("bt_rack_c", "bt_rack_short", (-1.35, 10.3), 1.0),
    ("bt_case_t", "bt_case", (-8.9, 2.6), 0.7),
    ("bt_dock_case_a", "bt_case", (4.6, 1.3), 0.9), ("bt_dock_case_b", "bt_case", (5.6, 1.1), 0.7), ("bt_dock_case_c", "bt_case", (8.2, 2.2), 1.0), ("bt_dock_case_d", "bt_case", (8.4, 7.6), 0.9),
    ("bt_dock_pend_a", "thing_pendant", (4.6, 4.6), 1.0, 3.3), ("bt_dock_pend_b", "thing_pendant", (6.9, 2.6), 1.0, 3.3),
    ("bt_crystal_a", "bt_crystal", (1.9, 15.9), 2.2), ("bt_crystal_b", "bt_crystal", (-2.0, 16.0), 1.8), ("bt_moth_console", "bt_moth_console", (0.0, 16.9), 0.9),
]
# decals (hung on a solid wall within 0.35 m): id, sprite, point (m), size (height m), bottom y, emissive (the wall's own yaw: StoryMap places it)
DECALS = [
    ("bt_dc_vent_door", "bt_vent_door", (1.6, 6.15), 2.2, 0.0, False), ("bt_dc_pipes", "bt_pipes", (1.65, 7.55), 2.6, 0.0, False), ("bt_dc_shelf", "bt_cable_shelf", (1.6, 9.0), 1.3, 0.55, False),
    ("bt_dc_led_a", "bt_led", (1.6, 1.5), 0.22, 2.1, True), ("bt_dc_led_b", "bt_led", (1.6, 9.9), 0.22, 2.1, True), ("bt_dc_led_c", "bt_led", (-1.6, 10.8), 0.2, 2.15, True),
    ("bt_dc_screen_a", "bt_screen", (-3.3, 10.8), 0.55, 1.5, True), ("bt_dc_screen_b", "bt_screen_wave", (-2.5, 10.8), 0.55, 1.5, True), ("bt_dc_screen_c", "bt_screen", (1.5, 10.85), 0.5, 1.5, True),
    ("bt_dc_skyline", "bt_skyline", (-9.6, 4.25), 3.0, 0.3, True), ("bt_dc_shutter", "bt_shutter", (8.85, 4.5), 2.2, 0.0, False),
    ("bt_dc_led_d", "bt_led", (0.0, 0.2), 0.3, 2.2, True),
]
LIGHTS = [  # id, point (m), y, radius, colour, strength   (amber task light over the desk, red LED glow at the racks, the caged lamps in the aisle, moonlight on the balcony, violet ahead, sodium on the dock)
    ("bt_lt_desk_a", (-3.2, 2.2), 2.1, 4.5, "#ffa040", 1.7), ("bt_lt_desk_b", (-3.4, 5.6), 2.0, 4.5, "#ffb050", 1.6),
    ("bt_lt_aisle_a", (0.0, 2.5), 2.5, 7.0, "#ffb060", 1.5), ("bt_lt_aisle_b", (0.0, 6.5), 2.5, 7.0, "#ffb060", 1.5), ("bt_lt_aisle_c", (0.0, 9.8), 2.5, 6.0, "#ffa850", 1.3),
    ("bt_lt_rack", (1.1, 7.9), 1.2, 3.5, "#ff3028", 1.3), ("bt_lt_landing", (-2.9, 10.0), 2.3, 4.0, "#ff6a30", 1.1),
    ("bt_lt_balcony", (-6.8, 4.2), 3.0, 9.0, "#5a80d8", 1.5), ("bt_lt_balcony2", (-6.5, 9.8), 3.0, 6.0, "#6a90e0", 1.2),
    ("bt_lt_hatch", (0.0, 11.5), 2.2, 3.0, "#d0a0ff", 1.2), ("bt_lt_moth", (0.0, 14.5), 3.4, 8.0, "#a070ff", 1.6), ("bt_lt_moth2", (0.0, 16.6), 2.0, 4.5, "#70ffc8", 1.2),
    ("bt_lt_dock", (4.6, 4.6), 3.0, 8.0, "#ffa850", 1.8), ("bt_lt_dock2", (6.9, 2.6), 3.0, 6.0, "#ffb860", 1.5), ("bt_lt_dock3", (7.0, 7.0), 3.0, 6.0, "#ff9840", 1.2),
]
CROWD_POINTS_SECTOR = "terrace"


def lift(h):
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(int(v + (255 - v) * TINT_LIFT) for v in (r, g, b))


def inside(poly, x, z):
    c = False
    n = len(poly)
    for i in range(n):
        (x1, z1), (x2, z2) = poly[i], poly[(i + 1) % n]
        if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1):
            c = not c
    return c


def dist_to_edges(poly, x, z):
    best = 1e9
    for i in range(len(poly)):
        (x1, z1), (x2, z2) = poly[i], poly[(i + 1) % len(poly)]
        dx, dz = x2 - x1, z2 - z1
        t = max(0.0, min(1.0, ((x - x1) * dx + (z - z1) * dz) / (dx * dx + dz * dz or 1)))
        best = min(best, math.hypot(x - (x1 + t * dx), z - (z1 + t * dz)))
    return best


def sector_of(d, x, z):
    for s in d["sectors"]:
        if inside(s["polygon"], x, z):
            return s
    return None


def barriers(d, names):
    """Closes what a walker must not cross: every portal whose floors differ by more than MAX_STEP is a drop and is shut to walkers (`blocked`) while every sector stays reachable
    from the start (the map loader demands that); the desk dais and the window are the railing kind (a see-through strip; closed to walkers), the dais's edge a handrail tile and the
    window the wire mesh."""
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

    for w in walls:
        a, b = sec[w["sector"]], sec[w["portal"]]
        if abs(float(a["floor"]) - float(b["floor"])) > MAX_STEP + 1e-6 and not w.get("blocked"):
            w["blocked"] = True
            if not all_reachable():
                del w["blocked"]
                print("  a drop of %.2f m between %s and %s stays open (it keeps the map connected)" % (abs(float(a["floor"]) - float(b["floor"])), w["sector"], w["portal"]))
    for w in walls:
        a, b = sec[w["sector"]], sec[w["portal"]]
        key = "|".join(sorted((names[int(a["doom_sector"])], names[int(b["doom_sector"])]), key=lambda n: -RAIL_ORDER.get(n, 0)))
        if key in RAIL_HEIGHTS:
            w["kind"], w["tex"], w["height"] = "railing", RAIL_TEX.get(key, WINDOW_TEX), RAIL_HEIGHTS[key]
            w["blocked"] = True


RAIL_ORDER = {"dais": 3, "dstep_a": 2, "dstep_b": 2, "aisle": 1, "terrace": 1}


def main():
    d = json.load(open(MAP, encoding="utf-8"))
    names = json.load(open(TRACE, encoding="utf-8"))["sector_names"]
    d["art"] = "doom_booth"
    used = {}
    for s in d["sectors"]:
        nm = names[int(s["doom_sector"])]
        f, w, c, tint, step = STYLE[nm]
        s["floor_tex"], s["wall_tex"], s["ceil_tex"], s["tint"], s["step_tex"] = f, w, c, lift(tint), step
        s["lip_tex"] = "bt_trim"
        s["room"] = "main"
        s["light"] = round(min(1.0, max(LIGHT_FLOOR, float(s["light"]) * LIGHT_GAIN)), 3)
        for k in ("floor_tex", "wall_tex", "ceil_tex", "step_tex", "lip_tex"):
            used[s[k]] = True
    for w in d["walls"]:
        for k in ("lower_tex", "upper_tex"):
            if w.get(k):
                used[w[k]] = True
    used.update({"bt_rail": True, WINDOW_TEX: True})
    tex = {}
    for k in sorted(used):
        tex[k] = OWN + k + ".png"
    for k in BORROWED:
        tex[k] = NIGHT + k + ".png"
    for _id, spr, *_r in THINGS:
        if spr not in tex:
            tex[spr] = OWN + spr + ".png"
    for _id, spr, *_r in DECALS:
        tex[spr] = OWN + spr + ".png"
    for who in GUIDES:
        for st, n in STATES.items():
            for i in range(n):
                tex["guide_%s_%s_%d" % (who, st, i)] = OWN + "guide_%s_%s_%d.png" % (who, st, i)
    d["textures"] = tex
    d["max_step"] = MAX_STEP
    d["visibility"] = {"mode": "clip", "depth": 48, "far": 0}
    # waypoints
    keep = [w for w in d["waypoints"] if not w["id"].startswith("bt_")]
    for wid, at, look, hold, _why in WAYPOINTS:
        x, z = M(*at)
        s = sector_of(d, x, z)
        floor0 = s["floor"] if s else None
        margin = MARGINS.get(wid, MARGIN)
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
            at = (x, -z)
        w = {"id": wid, "at": [x, z], "yaw": face(at, look), "sector": s["id"]}
        if hold:
            w["hold_bars"] = hold
        keep.append(w)
    d["waypoints"] = keep
    d["start"] = "bt_arrive"
    barriers(d, names)
    d["sky"] = {}
    d["fog"] = {"color": "#2a1618", "density": 0.022}
    d["palette_weight"] = 1.0
    # things
    things = [t for t in d["things"] if not str(t["id"]).startswith("bt_")]
    for who, (at, size, lamp) in GUIDES.items():
        x, z = M(*at)
        things.append({"id": "bt_guide_" + who, "kind": "billboard", "sprite": "guide_%s_idle_0" % who, "at": [x, z], "y": round(size * 0.5, 3), "size": size, "anim": "none"})
    for row in THINGS:
        tid, spr, at, size = row[:4]
        x, z = M(*at)
        t = {"id": tid, "kind": "billboard", "sprite": spr, "at": [x, z], "y": row[4] if len(row) > 4 else round(size * 0.5, 3), "size": size, "anim": "none"}
        things.append(t)
    for tid, spr, at, size, y, emissive in DECALS:
        x, z = M(*at)
        t = {"id": tid, "kind": "decal", "sprite": spr, "at": [x, z], "y": y, "size": size}
        if emissive:
            t["emissive"] = True
        things.append(t)
    for lid, at, y, rad, col, st in LIGHTS:
        x, z = M(*at)
        things.append({"id": lid, "kind": "light", "at": [x, z], "y": y, "radius": round(rad * 1.3, 1), "color": col, "strength": round(min(2.5, st * LAMP_GAIN), 2)})
    for who, (at, size, lamp) in GUIDES.items():  # the lamp over each guide (the choice layer brightens it)
        x, z = M(*lamp)
        things.append({"id": "bt_lamp_" + who, "kind": "light", "at": [x, z], "y": 2.6, "radius": 3.0, "color": "#ffd9a0", "strength": 0.6})
    d["things"] = things
    spots = {k: v for k, v in d.get("spots", {}).items() if not k.startswith("bt_")}
    for who, (at, size, lamp) in GUIDES.items():
        x, z = M(*at)
        spots["bt_guide_" + who] = {"sector": sector_of(d, x, z)["id"], "at": [x, z]}
    d["spots"] = spots
    # the crowd: the night_one chapter's cast dances on the iron balcony outside the window (the booth's pit); content/run/doom/story_doom_booth.json is the world's StoryData
    ch = json.load(open(os.path.join(ROOT, "content", "story", "night_one.json"), encoding="utf-8"))
    ch["id"], ch["title"] = "doom_booth", "Doom Booth"
    ch["art"] = "night_one"
    for b in ch["blocks"]:
        b["events"] = [e for e in b.get("events", []) if not str(e.get("action", "")).startswith("player_") and str(e.get("action", "")) != "doors_open"]
    for dec in ch["decisions"]:
        for k in ("good", "bad"):
            dec[k] = [e for e in dec.get(k, []) if not (isinstance(e, dict) and str(e.get("action", "")).startswith("player_"))]
    for e in ch["endings"].values():
        e["journey"] = []
    open(os.path.join(ROOT, "content", "run", "doom", "story_doom_booth.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(ch, indent=1) + "\n")
    terrace = next(s for s in d["sectors"] if names[int(s["doom_sector"])] == CROWD_POINTS_SECTOR)
    guide_pts = [M(*g[0]) for g in GUIDES.values()]
    pts = []
    gx = -9.4
    while gx <= -4.4:
        gz = 0.5
        while gz <= 8.2:
            if inside(terrace["polygon"], gx, -gz) and dist_to_edges(terrace["polygon"], gx, -gz) >= 0.33 and all(math.hypot(gx - p[0], -gz - p[1]) > 1.3 for p in guide_pts):
                pts.append((round(gx, 2), round(-gz, 2), terrace["id"]))
            gz += 0.75
        gx += 0.75
    pts.sort(key=lambda p: (int(p[0] * 977 + p[1] * 1931) * 2654435761) % 4294967296)
    need = len(ch["actors"]) + len(ch["silhouettes"])
    if len(pts) < need:
        raise SystemExit("only %d balcony spots for %d people" % (len(pts), need))
    d["homes"] = [{"actor": a["id"], "sector": pts[i][2], "at": [pts[i][0], pts[i][1]]} for i, a in enumerate(ch["actors"])]
    d["silhouettes"] = [{"id": s["id"], "at": [pts[len(ch["actors"]) + i][0], pts[len(ch["actors"]) + i][1]]} for i, s in enumerate(ch["silhouettes"])]
    d["scene"] = {"id": "doom_booth", "reference": "art/reference/doom_worlds/Rhythm Booth, Three Hidden Routes-5.png", "routes": ROUTES,
                  "note": "authored by tools/doom/author_booth.py; routes are lists of waypoint ids (the polyline); hold_bars on a waypoint is the still hold at a choice window"}
    d["doom"]["authored"] = True
    json.dump(d, open(MAP, "w", encoding="utf-8", newline="\n"), indent=1)
    open(MAP, "a", encoding="utf-8", newline="\n").write("\n")
    print("authored %d waypoints, %d things (%d decals), %d spots into %s" % (len(WAYPOINTS), len(things), len(DECALS), len(spots), MAP))


if __name__ == "__main__":
    sys.exit(main())
