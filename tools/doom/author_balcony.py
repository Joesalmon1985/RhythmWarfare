"""Authors the Balcony scene into content/story/maps/doom_balcony.json (docs/doom/scenes/balcony.md), the Booth's pipeline (tools/doom/author_booth.py) for MAP15.

    python -I tools/doom/trace/balcony_scene.py; python -I tools/doom/convert.py --scene balcony --trace tools/doom/trace/balcony_pilot.json     # the geometry (this script's input)
    python -I tools/doom/author_balcony.py                                                       # waypoints, textures, things, decals, lights, spots (idempotent; run after every convert)

Coordinates in this file are METRES (x east, y north, as the trace) and are turned into the map's (x, z = -y) by `M`. A waypoint names the sector that holds it and keeps the 0.5 m margin
StoryMap wants (less in the stair treads and the door); the script moves nothing but a point too close to a wall, and says so.

Routes are lists of waypoint ids (`ROUTES`); tools/run/make_doom_balcony.py cuts them into the rail's polyline moves. `hold_bars` on a waypoint is the number of bars the camera holds still.
The four pits round the roof are VOIDS (marked here: the depth rule cannot see the two that touch only another void).
"""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MAP = os.path.join(ROOT, "content", "story", "maps", "doom_balcony.json")
TRACE = os.path.join(ROOT, "tools", "doom", "trace", "balcony_pilot.json")
NIGHT = "res://assets/story/night_one/textures/"
OWN = "textures/"
MARGIN = 0.5
MARGINS = {"bc_stair_foot": 0.35, "bc_v_s_a": 0.4, "bc_v_s_b": 0.4, "bc_v_s_c": 0.4, "bc_v_s_d": 0.4, "bc_v_land": 0.4, "bc_v_door": 0.33, "bc_v_ba": 0.4, "bc_v_bb": 0.4, "bc_v_bc": 0.4}
MAX_STEP = 0.5
RAIL_HEIGHT = 1.1  # metres above the higher floor
RAIL_TEX = "bc_rail"
VOIDS = ["vw1", "vw2", "ve1", "ve2", "vn"]
LIGHT_GAIN, LIGHT_FLOOR, TINT_LIFT, LAMP_GAIN = 1.4, 0.52, 0.35, 2.4  # exposure (the booth's A1 night values: each sector is lit at least LIGHT_FLOOR)
# stage D polish (docs/briefs/DOOM_POLISH_BRIEF.md): the open sectors take the map's moon sky (no ceiling tile), the drops' ceilings are low (balcony_scene.py) so the city shows
# over their far walls; exposure: every sector's song-time light at LIGHT (a gain of 1.5) with the flat light away from the lamps cut to AMBIENT, so the lamp pools, the emissive
# windows and doors carry the picture; the rain on the open sectors, drips at the cabin's eave and the stair's head, the cabin floor wet from the door
SKY = {"tex": "textures/bc_sky.png", "mode": "cylinder"}
SKY_SECTORS = ["deck", "landing", "s_a", "s_b", "s_c", "s_d", "s_e", "alley", "b_a", "b_b", "b_c", "bridge", "isle", "vw1", "vw2", "ve1", "ve2", "vn"]
LIGHT = 1.0
AMBIENT = {"deck": 0.4, "landing": 0.45, "s_a": 0.45, "s_b": 0.45, "s_c": 0.45, "s_d": 0.45, "s_e": 0.42, "alley": 0.4, "b_a": 0.9, "b_b": 0.9, "b_c": 0.9, "bridge": 0.9, "isle": 0.9, "bdoor": 0.6, "cabin": 0.45, "cback": 0.5, "vw1": 1.0, "vw2": 1.0, "ve1": 1.0, "ve2": 1.0, "vn": 1.0}
WEATHER = {"rain": 0.85, "wind": -12, "drips": [{"at": [3.3, -4.0], "h": 2.4}, {"at": [3.3, -6.2], "h": 2.4}, {"at": [-3.7, -6.0], "h": 3.0}]}
WET = {"bdoor": 0.5, "cabin": 0.15}


def M(x, y):
    return (round(x, 4), round(-y, 4))


def face(a, b):
    """The yaw of a view from the point a (metres, x east, y north) towards b (0 faces north / -z, 90 faces -x)."""
    return round(math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1])), 1)


# id, point (m), look-at point (m), hold_bars (0 = a moving place), what it is.  Names starting bc_v_ are via points only: corners of the polyline moves, never stood on.
WAYPOINTS = [
    ("bc_arrive", (0.9, 0.5), (0.3, 16), 0, "arrival: the roof deck's south end (a cut, then a three bar walk to the reference viewpoint)"),
    ("bc_ref", (0.5, 1.9), (0.3, 16), 8, "THE reference viewpoint: the deck's south end looking north, the stair landing and the floor guide left, the cabin door and its guide right, the bridge and the mothership guide ahead"),
    ("bc_ref_back", (1.1, 0.7), (0.3, 16), 0, "recovery: a stumble back into the corner"),
    ("bc_sw_corner", (-1.1, 1.0), (0.3, 16), 0, "recovery: along the south wall"),
    ("bc_bridge_view", (0.0, 6.5), (0.0, 17.5), 2, "reveal: up the deck at the bridge, the drop either side and the mothership guide on the platform"),
    ("bc_stair_view", (-1.8, 3.8), (-5.5, 10.0), 2, "reveal: the deck's west side looking over the railing at the brick stair and the landing"),
    ("bc_cabin_view", (1.9, 6.0), (6.0, 10.0), 2, "reveal: the deck's east side looking through the open cabin door at the lit control room"),
    ("bc_bridge_end", (0.0, 15.2), (0.4, 19), 1, "THRESHOLD ahead (Mothership): the far end of the bridge facing the tower's lit violet door under the lace dome; the world transition happens here"),
    ("bc_stair_foot", (-5.0, -4.5), (-5.0, -7), 1, "THRESHOLD left (Floor): down the brick stair and along the alley, before the club's lit side door; the world transition happens here"),
    ("bc_cabin_in", (8.1, 5.0), (10.5, 5.0), 1, "THRESHOLD right (Booth): through the cabin, at its open back door onto the lit stairwell down; the world transition happens here"),
    # via points (corners of the polyline moves)
    ("bc_v_a1", (0.0, 4.5), (0.0, 8), 0, "via: the deck, mid way"),
    ("bc_v_a2", (-0.8, 5.0), (-3, 5.5), 0, "via: the deck's middle, before the stair view"),
    ("bc_v_a3", (0.8, 5.0), (1.9, 6.0), 0, "via: the deck's middle, before the cabin view"),
    ("bc_v_a4", (0.9, 3.2), (0.5, 1.9), 0, "via: the deck, south of the cabin door"),
    ("bc_v_n", (0.0, 8.4), (0.0, 12), 0, "via: the deck's north edge, before the bridge steps"),
    ("bc_v_ba", (0.0, 9.5), (0.0, 12), 0, "via: the bridge's first step"),
    ("bc_v_bb", (0.0, 10.5), (0.0, 12), 0, "via: the bridge's second step"),
    ("bc_v_bc", (0.0, 11.5), (0.0, 12), 0, "via: the bridge's third step"),
    ("bc_v_land", (-4.0, 5.55), (-5.0, 4.5), 0, "via: the landing, at the stair's head"),
    ("bc_v_s_a", (-4.9, 4.5), (-5.0, 3.5), 0, "via: the first stair tread"),
    ("bc_v_s_b", (-5.0, 3.5), (-5.0, 2.5), 0, "via: the second stair tread"),
    ("bc_v_s_c", (-5.0, 2.5), (-5.0, 1.5), 0, "via: the third stair tread"),
    ("bc_v_s_d", (-5.0, 1.5), (-5.0, 0.5), 0, "via: the fourth stair tread"),
    ("bc_v_e1", (2.0, 4.6), (3.9, 5.2), 0, "via: the deck in front of the cabin door"),
    ("bc_v_door", (3.875, 5.2), (5.0, 5.0), 0, "via: the cabin door"),
]
ROUTES = {
    "ahead": ["bc_v_a1", "bc_v_n", "bc_v_ba", "bc_v_bb", "bc_v_bc", "bc_bridge_end"],
    "left": ["bc_v_a2", "bc_v_land", "bc_v_s_a", "bc_v_s_b", "bc_v_s_c", "bc_v_s_d", "bc_stair_foot"],
    "right": ["bc_v_e1", "bc_v_door", "bc_cabin_in"],
    "stay": ["bc_v_a1", "bc_bridge_view", "bc_v_a2", "bc_stair_view", "bc_v_a3", "bc_cabin_view", "bc_v_a4", "bc_ref"],
    "arrive": ["bc_arrive", "bc_ref"],
    "stumble": ["bc_ref_back", "bc_sw_corner", "bc_ref"],
}
# sector name -> floor, wall, ceiling texture, tint, step_tex (the riser of a step up onto it)
STYLE = {
    "deck": ("bc_floor_wet", "bc_wall_conc", "bc_ceil", "#e0e8ff", "bc_wall_steel"),
    "landing": ("bc_floor_stair", "bc_wall_brick", "bc_ceil", "#ffb890", "bc_wall_steel"),
    "s_a": ("bc_floor_stair", "bc_wall_brick", "bc_ceil", "#ffb890", "bc_wall_steel"),
    "s_b": ("bc_floor_stair", "bc_wall_brick", "bc_ceil", "#ffb890", "bc_wall_steel"),
    "s_c": ("bc_floor_stair", "bc_wall_brick", "bc_ceil", "#ffb890", "bc_wall_steel"),
    "s_d": ("bc_floor_stair", "bc_wall_brick", "bc_ceil", "#ffb890", "bc_wall_steel"),
    "s_e": ("bc_floor_stair", "bc_wall_brick", "bc_ceil", "#ffb890", "bc_wall_steel"),
    "bdoor": ("bc_floor_cabin", "bc_wall_steel", "bc_ceil", "#ffc080", "bc_wall_steel"),
    "cabin": ("bc_floor_cabin", "bc_wall_cabin", "bc_ceil", "#ffc080", "bc_wall_steel"),
    "b_a": ("bc_floor_grate", "bc_wall_steel", "bc_ceil", "#e0e8ff", "bc_wall_steel"),
    "b_b": ("bc_floor_grate", "bc_wall_steel", "bc_ceil", "#e0e8ff", "bc_wall_steel"),
    "b_c": ("bc_floor_grate", "bc_wall_steel", "bc_ceil", "#e0e8ff", "bc_wall_steel"),
    "bridge": ("bc_floor_grate", "bc_wall_steel", "bc_ceil", "#e0e8ff", "bc_wall_steel"),
    "isle": ("bc_floor_wet", "bc_wall_conc", "bc_ceil", "#ece4ff", "bc_wall_steel"),
    "alley": ("bc_floor_alley", "bc_wall_brick_b", "bc_ceil", "#f8e8f0", "bc_wall_steel"),
    "cback": ("bc_floor_cabin", "bc_wall_steel", "bc_ceil", "#ffc080", "bc_wall_steel"),
    "vw1": ("bc_floor_conc", "bc_facade_a", "bc_ceil", "#e0e8ff", "bc_facade_a"),
    "vw2": ("bc_floor_conc", "bc_facade_b", "bc_ceil", "#e0e8ff", "bc_facade_b"),
    "ve1": ("bc_floor_conc", "bc_facade_c", "bc_ceil", "#e0e8ff", "bc_facade_c"),
    "ve2": ("bc_floor_conc", "bc_facade_a", "bc_ceil", "#e0e8ff", "bc_facade_a"),
    "vn": ("bc_floor_conc", "bc_facade_b", "bc_ceil", "#e0e8ff", "bc_facade_b"),
}
BORROWED = ["thing_pendant", "trim"]
STATES = {"idle": 1, "available": 5, "selected": 2, "committed": 2}
GUIDES = {  # id suffix: point (m), size (height m), lamp point (m)
    "mothership": ((-0.7, 16.7), 2.4, (-0.7, 15.6)),
    "floor": ((-5.2, 7.2), 2.2, (-5.2, 6.4)),
    "booth": ((5.6, 7.0), 2.2, (6.5, 7.0)),
}
# billboards: id, sprite, point (m), size (height m); y is the centre (half the size) unless a fifth value is given (the bottom edge above the floor, when it is a `y` it floats)
THINGS = [  # round 2: no tower billboards in the drop (they hid the moon and walled the view); the dish stands on the cabin's roof
    ("bc_case_a", "bc_case", (3.0, 1.2), 0.95), ("bc_case_b", "bc_case", (3.05, 2.55), 0.75), ("bc_cables_a", "bc_cables", (2.3, 0.7), 0.5), ("bc_case_c", "bc_case", (-3.0, 8.3), 0.7),
    ("bc_dish", "bc_dish", (7.6, 7.6), 2.0, 3.5), ("bc_lamp_brick", "bc_cage_lamp", (-6.2, 6.0), 0.5, 2.6),
    ("bc_rack_a", "bc_rack", (8.5, 3.1), 1.5), ("bc_rack_b", "bc_rack", (8.5, 7.4), 1.5), ("bc_case_d", "bc_case", (7.4, 8.0), 0.8), ("bc_cage_cabin", "bc_cage_lamp", (6.0, 4.4), 0.4, 3.0),
    ("bc_forklift", "bc_forklift", (5.0, 30.0), 1.6), ("bc_yard_case_a", "bc_case", (7.5, 31.2), 1.2), ("bc_yard_case_b", "bc_case", (-6.0, 31.0), 1.2), ("bc_yard_case_c", "bc_case", (-4.6, 31.6), 0.9),
]
# decals (hung on a solid wall within 0.35 m): id, sprite, point (m), size (height m), bottom y above that sector's floor, emissive (the wall's own yaw: StoryMap places it)
DECALS = [  # round 2: the pink equaliser graffiti is gone (the lead's list); the drop's far walls are lit facades: shutters at the yard's floor, single windows in rows above
    ("bc_dc_window", "bc_window_glow", (3.3, 1.7), 1.8, 0.9, True), ("bc_dc_window_b", "bc_window_glow", (3.4, 8.05), 1.4, 1.0, True),  # (the cabin's lit windows; round 2: the pipe decal gives way to the second)
    ("bc_dc_led_a", "bc_led", (4.4, 3.0), 0.22, 2.4, True), ("bc_dc_led_b", "bc_led", (8.85, 6.2), 0.22, 2.4, True),
    ("bc_dc_lace", "bc_lace", (0.0, 18.8), 4.2, 2.4, True), ("bc_dc_tower_door", "bc_tower_door", (0.5, 18.8), 2.4, 0.0, True), ("bc_dc_led_c", "bc_led", (-1.2, 18.8), 0.2, 2.0, True),
    ("bc_dc_alley_door", "bc_alley_door", (-5.0, -6.9), 2.6, 0.0, True),
    ("bc_dc_stair_glow", "bc_stair_glow", (10.4, 5.0), 2.3, 0.0, True),
    ("bc_dc_shut_a", "bc_shutters", (-6.0, 32.9), 3.4, 0.0, True), ("bc_dc_shut_b", "bc_shutters", (5.5, 32.9), 3.4, 0.0, True), ("bc_dc_shut_c", "bc_shutters", (-15.9, 26.0), 3.0, 0.0, True),
]
def facade_windows():
    """Round 2: the far walls of the drop are the facades of the city below, and the void's haze darkens their concrete with depth, so their light is their windows: rows of single
    windows (emissive when lit, about half of them), placed one by one on a jittered grid (no two neighbours alike, no tile repeat), on the north wall and the two side walls."""
    import random
    rnd = random.Random(615)
    out = []
    walls = [((-15.0, 32.9), (15.0, 32.9), 2.9), ((-15.9, 10.5), (-15.9, 31.5), 3.1), ((15.9, 10.5), (15.9, 31.5), 3.1)]
    sprites = ["bc_win_amber", "bc_win_amber", "bc_win_violet", "bc_win_cyan", "bc_win_dark", "bc_win_dark"]
    k = 0
    for (x0, y0), (x1, y1), step in walls:
        n = int(math.hypot(x1 - x0, y1 - y0) / step) + 1
        for i in range(n):
            t = i / max(1, n - 1)
            x, y = round(x0 + (x1 - x0) * t, 2), round(y0 + (y1 - y0) * t, 2)
            for row in (3.6, 6.0, 8.2):
                if rnd.random() < 0.18:
                    continue
                spr = rnd.choice(sprites)
                out.append(("bc_dc_w%02d" % k, spr, (x, y), round(1.9 + rnd.random() * 0.5, 2), round(row + rnd.random() * 0.4, 2), spr != "bc_win_dark"))
                k += 1
    return out


DECALS += facade_windows()


LIGHTS = [  # id, point (m), y, radius, colour, strength   (moon blue over the deck, the orange wall lamp at the stair head, the amber cabin, the violet window glow, red mast lights, the yard's lamps far below, the bridge lamps)
    ("bc_lt_moon", (0.0, 4.5), 5.0, 7.0, "#5a80d8", 1.4), ("bc_lt_moon2", (0.0, 8.0), 5.0, 6.0, "#6a90e0", 1.2),
    ("bc_lt_brick", (-5.6, 6.0), 2.7, 4.0, "#ff8a40", 1.7), ("bc_lt_stair", (-5.0, 2.5), 2.0, 3.5, "#ff7a38", 1.3),
    ("bc_lt_cabin", (6.5, 5.0), 3.0, 4.5, "#ffa850", 1.8), ("bc_lt_cabin2", (4.0, 5.2), 2.2, 3.5, "#ffb868", 1.4),
    ("bc_lt_window", (3.0, 1.7), 1.8, 4.5, "#a050ff", 1.5), ("bc_lt_window_b", (2.9, 8.0), 1.8, 3.5, "#a050ff", 1.5), ("bc_lt_puddle", (1.8, 1.2), 0.6, 4.0, "#d03aa0", 1.2),
    ("bc_lt_bridge", (0.0, 13.0), 2.6, 5.0, "#ffb060", 1.4), ("bc_lt_isle", (-0.7, 15.4), 2.8, 4.0, "#ffe0c0", 1.8), ("bc_lt_moth_rim", (-0.4, 18.2), 2.2, 3.5, "#c090ff", 1.8),
    # stage D polish: the alley's lamps and its side door's blue spill, the stairwell's warm glow, more moonlight and puddle colour on the deck
    ("bc_lt_alley", (-5.0, -1.0), 3.0, 3.0, "#ff8a40", 1.0), ("bc_lt_alley_door", (-5.0, -6.2), 1.4, 5.0, "#5a7aff", 1.8),
    ("bc_lt_stairwell", (10.0, 5.0), 1.6, 4.5, "#ffa850", 1.8), ("bc_lt_deck_s", (0.5, 3.0), 3.5, 5.0, "#6a90e0", 1.2),
    ("bc_lt_deck_red", (2.0, 4.5), 0.8, 4.0, "#ff3a3a", 1.0), ("bc_lt_deck_cyan", (-1.5, 6.5), 0.8, 4.0, "#3ad0ff", 1.0),
    ("bc_lt_tower_door", (0.5, 18.0), 1.4, 4.5, "#a070ff", 1.8),
    ("bc_lt_door_spill", (3.0, 5.2), 1.6, 5.0, "#ffa850", 1.6), ("bc_lt_deck_n", (0.0, 8.0), 3.0, 5.0, "#8aa0e8", 1.2), ("bc_lt_brick_wash", (-3.8, 4.0), 3.0, 4.0, "#ff9a58", 1.2),
    # round 2: the drop has its own light: the yard's blue shutter lamps and sodium lamps on the floor far below, the lit windows' glow on the facades
    ("bc_lt_yard_a", (-6.0, 31.5), 2.5, 8.0, "#4a90ff", 1.8), ("bc_lt_yard_b", (5.5, 31.5), 2.5, 8.0, "#4a90ff", 1.8), ("bc_lt_yard_c", (0.0, 27.0), 4.0, 9.0, "#ffa850", 1.4),
    ("bc_lt_yard_d", (-13.0, 24.0), 3.0, 8.0, "#ffa850", 1.2), ("bc_lt_yard_e", (12.0, 20.0), 3.0, 8.0, "#ffa850", 1.2), ("bc_lt_yard_f", (-14.5, 26.0), 2.0, 6.0, "#4a90ff", 1.4),
    ("bc_lt_fac_n", (0.0, 31.0), 7.0, 10.0, "#7a80d0", 1.0), ("bc_lt_fac_w", (-14.5, 17.0), 6.5, 8.0, "#8a70d0", 1.0), ("bc_lt_fac_e", (14.5, 17.0), 6.5, 8.0, "#d09060", 1.0),
]
CROWD_SECTORS = ["deck", "cabin"]


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


def dist_to_segment(p, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / (dx * dx + dz * dz or 1)))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dz))


def barriers(d, names):
    """The railings first (every pair of RAILS in the trace: see-through, shut to walkers), then every other drop of more than MAX_STEP is shut to walkers (`blocked`) while every sector
    stays reachable from the start (the map loader demands that): the two plain drops from the platform into the far pits stay open, the one way each pit is joined to the map."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("balcony_scene", os.path.join(ROOT, "tools", "doom", "trace", "balcony_scene.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    rails = {frozenset(p) for p in bs.RAILS}
    sec = {s["id"]: s for s in d["sectors"]}
    walls = [w for w in d["walls"] if w.get("portal")]
    start = next(w for w in d["waypoints"] if w["id"] == d["start"])["sector"]

    def nm(sid):
        return names[int(sec[sid]["doom_sector"])]

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
        if frozenset((nm(w["sector"]), nm(w["portal"]))) in rails:
            w["kind"], w["tex"], w["height"] = "railing", RAIL_TEX, RAIL_HEIGHT
            w["blocked"] = True
    for w in walls:
        a, b = sec[w["sector"]], sec[w["portal"]]
        if w.get("kind") == "railing":
            continue
        if abs(float(a["floor"]) - float(b["floor"])) > MAX_STEP + 1e-6 and not w.get("blocked"):
            w["blocked"] = True
            if not all_reachable():
                del w["blocked"]
                print("  a drop of %.2f m between %s and %s stays open (it keeps the map connected)" % (abs(float(a["floor"]) - float(b["floor"])), nm(w["sector"]), nm(w["portal"])))
    if not all_reachable():
        raise SystemExit("some sector cannot be reached from the start: check RAILS")


def main():
    d = json.load(open(MAP, encoding="utf-8"))
    names = json.load(open(TRACE, encoding="utf-8"))["sector_names"]
    d["art"] = "doom_balcony"
    used = {}
    for s in d["sectors"]:
        nm = names[int(s["doom_sector"])]
        f, w, c, tint, step = STYLE[nm]
        s["floor_tex"], s["wall_tex"], s["ceil_tex"], s["tint"], s["step_tex"] = f, w, c, lift(tint), step
        s["lip_tex"] = "bc_trim"
        s["room"] = "main"
        s["light"] = LIGHT
        s["ambient"] = AMBIENT.get(nm, 0.5)
        s.pop("wet", None)
        if nm in WET:
            s["wet"] = WET[nm]
        if nm in SKY_SECTORS:
            s["ceil_tex"] = "sky"
        if nm in VOIDS:
            s["void"] = True
        for k in ("floor_tex", "wall_tex", "ceil_tex", "step_tex", "lip_tex"):
            if s[k] != "sky":
                used[s[k]] = True
    sky_ids = {s["id"] for s in d["sectors"] if names[int(s["doom_sector"])] in SKY_SECTORS}
    for w in d["walls"]:
        if w.get("portal") and w["sector"] in sky_ids and w["portal"] in sky_ids:
            w["upper_tex"] = "sky"  # two open sectors with different wall heights (the deck and the low-ceilinged drops): no band in the air, the sky shows
        for k in ("lower_tex", "upper_tex"):
            if w.get(k) and w[k] != "sky":
                used[w[k]] = True
    used[RAIL_TEX] = True
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
    keep = [w for w in d["waypoints"] if not w["id"].startswith("bc_")]
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
    d["start"] = "bc_arrive"
    barriers(d, names)
    d["sky"] = dict(SKY)
    d["weather"] = {"rain": WEATHER["rain"], "wind": WEATHER["wind"], "drips": [dict(x) for x in WEATHER["drips"]]}
    d["fog"] = {"color": "#1c2848", "density": 0.008}  # round 2: thinner, so the far lit windows keep their light
    d["palette_weight"] = 1.0
    # things
    things = [t for t in d["things"] if not str(t["id"]).startswith("bc_")]
    for who, (at, size, lamp) in GUIDES.items():
        x, z = M(*at)
        things.append({"id": "bc_guide_" + who, "kind": "billboard", "sprite": "guide_%s_idle_0" % who, "at": [x, z], "y": round(size * 0.5, 3), "size": size, "anim": "none"})
    for row in THINGS:
        tid, spr, at, size = row[:4]
        x, z = M(*at)
        t = {"id": tid, "kind": "billboard", "sprite": spr, "at": [x, z], "size": size, "anim": "none"}
        t["y"] = round(row[4] + size * 0.5, 3) if len(row) > 4 else round(size * 0.5, 3)
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
        things.append({"id": "bc_lamp_" + who, "kind": "light", "at": [x, z], "y": 2.6, "radius": 3.0, "color": "#ffd9a0", "strength": 0.6})
    d["things"] = things
    spots = {k: v for k, v in d.get("spots", {}).items() if not k.startswith("bc_")}
    for who, (at, size, lamp) in GUIDES.items():
        x, z = M(*at)
        spots["bc_guide_" + who] = {"sector": sector_of(d, x, z)["id"], "at": [x, z]}
    d["spots"] = spots
    # the crowd: the night_one chapter's cast dances on the roof deck and in the cabin, clear of the sightlines and every walk (content/run/doom/story_doom_balcony.json is the world's StoryData)
    ch = json.load(open(os.path.join(ROOT, "content", "story", "night_one.json"), encoding="utf-8"))
    ch["id"], ch["title"] = "doom_balcony", "Doom Balcony"
    ch["art"] = "night_one"
    for b in ch["blocks"]:
        b["events"] = [e for e in b.get("events", []) if not str(e.get("action", "")).startswith("player_") and str(e.get("action", "")) != "doors_open"]
    for dec in ch["decisions"]:
        for k in ("good", "bad"):
            dec[k] = [e for e in dec.get(k, []) if not (isinstance(e, dict) and str(e.get("action", "")).startswith("player_"))]
    for e in ch["endings"].values():
        e["journey"] = []
    ch["actors"], ch["silhouettes"] = [], []  # stage D polish: nobody on the roof but the three guides (the painting)
    ch["groups"] = {k: [] for k in ch["groups"]}
    open(os.path.join(ROOT, "content", "run", "doom", "story_doom_balcony.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(ch, indent=1) + "\n")
    wp = {w["id"]: (w["at"][0], w["at"][1]) for w in d["waypoints"]}
    segs = []
    for route in ROUTES.values():
        for a, b in zip(route, route[1:]):
            segs.append((wp[a], wp[b]))
    for who in GUIDES.values():  # the sightlines from the reference viewpoint to each guide
        segs.append((wp["bc_ref"], M(*who[0])))
    guide_pts = [M(*g[0]) for g in GUIDES.values()]
    pts = []
    for sname in CROWD_SECTORS:
        sec = next(s for s in d["sectors"] if names[int(s["doom_sector"])] == sname)
        xs = [p[0] for p in sec["polygon"]]
        zs = [p[1] for p in sec["polygon"]]
        gx = min(xs) + 0.4
        while gx <= max(xs) - 0.4:
            gz = min(zs) + 0.4
            while gz <= max(zs) - 0.4:
                if inside(sec["polygon"], gx, gz) and dist_to_edges(sec["polygon"], gx, gz) >= 0.35 and all(math.hypot(gx - p[0], gz - p[1]) > 1.3 for p in guide_pts) \
                        and all(dist_to_segment((gx, gz), a, b) > 0.9 for a, b in segs) and all(math.hypot(gx - p[0], gz - p[1]) > 0.9 for p in wp.values()):
                    pts.append((round(gx, 2), round(gz, 2), sec["id"]))
                gz += 0.6
            gx += 0.6
    pts.sort(key=lambda p: (int(p[0] * 977 + p[1] * 1931) * 2654435761) % 4294967296)
    need = len(ch["actors"]) + len(ch["silhouettes"])
    if len(pts) < need:
        raise SystemExit("only %d roof spots for %d people" % (len(pts), need))
    d["homes"] = [{"actor": a["id"], "sector": pts[i][2], "at": [pts[i][0], pts[i][1]]} for i, a in enumerate(ch["actors"])]
    d["silhouettes"] = [{"id": s["id"], "at": [pts[len(ch["actors"]) + i][0], pts[len(ch["actors"]) + i][1]]} for i, s in enumerate(ch["silhouettes"])]
    d["scene"] = {"id": "doom_balcony", "reference": "art/reference/doom_worlds/Rainy industrial rooftop, three musical paths-8.png", "routes": ROUTES,
                  "note": "authored by tools/doom/author_balcony.py; routes are lists of waypoint ids (the polyline); hold_bars on a waypoint is the still hold at a choice window"}
    d["doom"]["authored"] = True
    json.dump(d, open(MAP, "w", encoding="utf-8", newline="\n"), indent=1)
    open(MAP, "a", encoding="utf-8", newline="\n").write("\n")
    print("authored %d waypoints, %d things (%d decals), %d spots into %s (%d crowd spots free for %d people)" % (len(WAYPOINTS), len(things), len(DECALS), len(spots), MAP, len(pts), need))


if __name__ == "__main__":
    sys.exit(main())
