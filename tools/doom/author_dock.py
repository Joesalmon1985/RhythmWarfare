"""Authors the Loading Dock scene into content/story/maps/doom_dock.json (docs/doom/scenes/dock.md), the Booth's pipeline (tools/doom/author_booth.py) for MAP13.

    python -I tools/doom/trace/dock_scene.py; python -I tools/doom/convert.py --scene dock --trace tools/doom/trace/dock_pilot.json     # the geometry (this script's input)
    python -I tools/doom/author_dock.py                                                          # waypoints, textures, things, decals, lights, spots (idempotent; run after every convert)

Coordinates in this file are METRES (x east, y north, as the trace) and are turned into the map's (x, z = -y) by `M`. A waypoint names the sector that holds it and keeps the 0.5 m margin
StoryMap wants (0.33 in the narrow door pieces); the script moves nothing but a point too close to a wall, and says so.

Routes are lists of waypoint ids (`ROUTES`); tools/run/make_doom_dock.py cuts them into the rail's polyline moves. `hold_bars` on a waypoint is the number of bars the camera holds still.
Waypoints are `dk_*`; the three thresholds (`dk_moth`, `dk_floor_door`, `dk_under`) are where the engine's world transition (hook H1.6) will happen.
The small geometry helpers (point in polygon, distance to edges) are the Booth's (tools/doom/author_booth.py).
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from author_booth import dist_to_edges, inside, lift, sector_of  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
MAP = os.path.join(ROOT, "content", "story", "maps", "doom_dock.json")
TRACE = os.path.join(ROOT, "tools", "doom", "trace", "dock_pilot.json")
OWN = "textures/"
MARGIN = 0.5
MARGINS = {"dk_v_d": 0.33}
MAX_STEP = 0.5
LIGHT_GAIN, LIGHT_FLOOR, LAMP_GAIN, REACH = 1.4, 0.72, 2.4, 1.3  # exposure (A1 night interior): the Doom lights are low for this renderer, so each sector is lit at least LIGHT_FLOOR
# stage D polish, exposure (the brief's rule p50 0.25 to 0.38, p95 - p5 over 0.4): every sector's song-time light is raised to LIGHT (a gain of 1.5 on the baked light) and the
# flat light away from the lamps is cut to AMBIENT of it, so the lamp pools and the emissives carry the picture and the dark between them stays dark (contrast, not a flat lift)
LIGHT = {"apron": 1.0, "canopy": 1.0, "walk": 1.0, "street": 1.0, "street_far": 1.0, "bend": 0.95, "yard": 1.0, "floor_door": 1.0, "floor_hall": 1.0, "floor_run": 1.0}
# round 2: the wet street reads as the painting's, warm sodium pools on wet tarmac with deep shadow between them: the flat light away from the lamps is cut further (AMBIENT) and the
# lamps' pools are the brightest thing on the ground; the club passage is a dark brick tunnel lit by its violet door at the end
AMBIENT = {"apron": 0.42, "canopy": 0.5, "walk": 0.36, "street": 0.55, "street_far": 0.62, "bend": 0.5, "yard": 0.46, "floor_door": 0.5, "floor_hall": 0.34, "floor_run": 0.34}
# the rain (docs/engine/WEATHER.md): it falls on the six sky sectors, the canopy and the club passage stay dry; drips from the canopy's edge and the club door's lintel
WEATHER = {"rain": 0.8, "wind": 10, "drips": [{"at": [4.15, -1.2], "h": 3.2}, {"at": [3.9, -2.6], "h": 3.2}, {"at": [-3.7, -8.0], "h": 2.6}, {"at": [-3.7, -9.7], "h": 2.6}]}
WET = {"canopy": 0.35, "apron": 1.0, "walk": 1.0, "street": 1.0, "street_far": 1.0, "bend": 1.0, "yard": 0.9, "floor_door": 0.4, "floor_hall": 0.8, "floor_run": 1.0}  # round 2: the passage floor is wet (the violet door and the lamps lay gloss bands on it)


SKY = {"tex": "textures/dk_sky.png", "mode": "cylinder"}  # stage D polish: the storm sky strip over the open sectors (make_dock_art.p_sky)
LIP = {"floor_door": "dk_wall_brick", "canopy": "dk_wall_shutter", "floor_hall": "dk_wall_tunnel", "floor_run": "dk_wall_tunnel"}  # the wall above a lower-ceilinged opening (Doom's upper texture)
SKY_SECTORS = ["apron", "walk", "street", "yard", "street_far", "bend"]


def M(x, y):
    return (round(x, 4), round(-y, 4))


def face(a, b):
    """The yaw of a view from the point a (metres, x east, y north) towards b (0 faces north / -z, 90 faces -x)."""
    return round(math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1])), 1)


# id, point (m), look-at point (m), hold_bars (0 = a moving place), what it is.  Names starting dk_v_ are via points only: corners of the polyline moves, never stood on.
WAYPOINTS = [
    ("dk_arrive", (2.0, 0.75), (0.5, 12), 0, "arrival: the south edge of the apron (a cut, then a three bar walk to the reference viewpoint)"),
    ("dk_ref", (1.0, 1.5), (0.0, 12), 8, "THE reference viewpoint: on the apron looking up the wet street; the club door and the Floor guide left, the Mothership guide at the street's end, the furnace and the Underworld guide right"),
    ("dk_ref_back", (2.4, 0.8), (0.0, 12), 0, "recovery: a stumble back to the apron's edge"),
    ("dk_sw_corner", (-1.8, 1.2), (0.0, 12), 0, "recovery: along the brick wall"),
    ("dk_street_view", (0.6, 9.0), (-0.5, 19), 2, "reveal: up the street at the lamp, the towers and the Mothership guide"),
    ("dk_door_view", (-2.7, 6.2), (-8.0, 8.4), 2, "reveal: on the sidewalk at the club door, the blue passage and the Floor guide"),
    ("dk_yard_view", (5.0, 6.5), (11.0, 13.0), 2, "reveal: from the street's east side across to the yard, the van, the furnace and the Underworld guide"),
    ("dk_moth", (0.4, 12.4), (-2.4, 23.0), 1, "THRESHOLD ahead (Mothership): up the street to the Mothership guide at the corner, the brown building's lit doorway and the fourth lamp's pool behind her, the street turning left; the world transition happens here"),
    ("dk_floor_door", (-11.8, 8.75), (-16, 8.75), 1, "THRESHOLD left (Floor): in the dark brick passage behind the club door, near its violet-lit door to the dance floor; the world transition happens here"),
    ("dk_under", (8.3, 15.4), (12.5, 12.4), 1, "THRESHOLD right (Underworld): in the yard's north-west corner facing the furnace's glowing mouth (the way down), the guide before it; the world transition happens here"),
    # via points (corners of the polyline moves)
    ("dk_v_s1", (0.6, 5.5), (0.6, 12), 0, "via: the street, just past the apron's edge"),
    ("dk_v_a1", (-1.0, 3.0), (-2.8, 5.5), 0, "via: the apron, towards the sidewalk"),
    ("dk_v_w1", (-2.8, 5.5), (-2.8, 8.8), 0, "via: the sidewalk, just north of the apron"),
    ("dk_v_w2", (-2.8, 8.8), (-4.75, 9.0), 0, "via: the sidewalk in front of the club door"),
    ("dk_v_d", (-4.75, 9.0), (-8.0, 9.0), 0, "via: the club door"),
    ("dk_v_u1", (4.5, 5.5), (6.8, 10.0), 0, "via: the street, east of the apron"),
    ("dk_v_u2", (6.8, 10.0), (9.2, 10.0), 0, "via: the street's east edge, at the yard's mouth"),
    ("dk_v_u3", (8.4, 11.6), (8.3, 15.4), 0, "via: the yard's west side, past the van"),
    ("dk_v_r1", (1.2, 3.2), (1.0, 1.5), 0, "via: the apron, back to the reference viewpoint"),
]
ROUTES = {
    "ahead": ["dk_v_s1", "dk_moth"],
    "left": ["dk_v_a1", "dk_v_w1", "dk_v_w2", "dk_v_d", "dk_floor_door"],
    "right": ["dk_v_u1", "dk_v_u2", "dk_v_u3", "dk_under"],
    "stay": ["dk_v_s1", "dk_street_view", "dk_v_a1", "dk_door_view", "dk_v_u1", "dk_yard_view", "dk_v_r1", "dk_ref"],
    "arrive": ["dk_arrive", "dk_ref"],
    "stumble": ["dk_ref_back", "dk_sw_corner", "dk_ref"],
}
# sector name -> floor, wall, ceiling texture, tint, step_tex (the riser of a step up onto it)
STYLE = {
    "apron": ("dk_floor_conc", "dk_wall_brick", "dk_ceil_sky", "#e4d0c4", "dk_trim"),
    "canopy": ("dk_floor_conc", "dk_wall_shutter", "dk_ceil_truss", "#ffc078", "dk_trim"),
    "walk": ("dk_floor_walk", "dk_wall_brick", "dk_ceil_sky", "#d4cce8", "dk_trim"),
    "street": ("dk_floor_asphalt", "dk_wall_corr", "dk_ceil_sky", "#ccd2f0", "dk_trim"),
    "street_far": ("dk_floor_asphalt", "dk_wall_brown_a", "dk_ceil_sky", "#e0d0dc", "dk_trim"),
    "bend": ("dk_floor_asphalt", "dk_wall_bldg_a", "dk_ceil_sky", "#c8cef0", "dk_trim"),
    "floor_run": ("dk_floor_walk", "dk_wall_tunnel", "dk_ceil_tunnel", "#ffe4d0", "dk_wall_steel"),
    "yard": ("dk_floor_asphalt", "dk_wall_bldg_a", "dk_ceil_sky", "#ecccb0", "dk_trim"),
    "floor_door": ("dk_floor_walk", "dk_wall_brick", "dk_ceil_tunnel", "#98a8ff", "dk_wall_steel"),
    "floor_hall": ("dk_floor_walk", "dk_wall_tunnel", "dk_ceil_tunnel", "#ffe0d0", "dk_wall_steel"),
}
# explicit solid-wall textures where the sector's own wall texture is not the right one: sector, from (m), to (m), texture
WALL_TEX = [  # round 2: no tower tile; the near walls are the club's brick and corrugated steel, the far ones dark facades in 3-4 m stretches of three variants (no tile repeats across a wall)
    ("walk", (-4, 4.5), (-4, 6), "dk_wall_brick_b"), ("walk", (-4, 10), (-4, 13.5), "dk_wall_brick_b"),
    ("street", (7.5, 4.5), (7.5, 8.5), "dk_wall_shutter"), ("street", (7.5, 16), (7.5, 17), "dk_wall_corr_b"),
    ("street_far", (7.5, 17), (7.5, 20), "dk_wall_corr_b"), ("street_far", (7.5, 20), (7.5, 24), "dk_wall_bldg_c"),
    ("street_far", (-1.5, 24), (1.5, 24), "dk_wall_brown_b"), ("street_far", (4.5, 24), (7.5, 24), "dk_wall_brown_b"),
    ("bend", (-14, 24), (-10, 24), "dk_wall_bldg_b"), ("bend", (-6, 24), (-1.5, 24), "dk_wall_bldg_c"), ("bend", (-14, 17), (-14, 24), "dk_wall_bldg_b"),
    ("bend", (-14, 17), (-10, 17), "dk_wall_bldg_c"), ("bend", (-10, 17), (-4, 17), "dk_wall_brick_b"),
    ("yard", (13.5, 8.5), (13.5, 16), "dk_wall_corr"), ("yard", (7.5, 8.5), (13.5, 8.5), "dk_wall_steel"),
]
STATES = {"idle": 1, "available": 5, "selected": 2, "committed": 2}
GUIDES = {  # id suffix: point (m), size (height m), lamp point (m)
    "mothership": ((-0.6, 16.0), 2.3, (-0.6, 15.0)),
    "floor": ((-4.8, 7.3), 2.2, (-4.2, 7.3)),
    "underworld": ((10.0, 12.6), 2.3, (9.0, 12.6)),  # the crop leaves his hidden legs out: the seat crates stand in front of them
}
# billboards: id, sprite, point (m), size (height m); y is the centre (half the size) unless a fifth value is given (height of the centre above the floor)
THINGS = [
    ("dk_bollard_a", "dk_bollard", (-0.5, 4.3), 1.1), ("dk_bollard_b", "dk_bollard", (2.6, 3.9), 1.1), ("dk_bollard_c", "dk_bollard", (-0.9, 2.6), 1.1),
    ("dk_pallets_near", "dk_pallets_near", (5.4, 5.3), 1.2), ("dk_case_e", "dk_case", (6.6, 6.4), 0.9),
    ("dk_case_a", "dk_case", (6.3, 0.9), 1.2), ("dk_case_b", "dk_case", (5.2, 0.8), 0.7),
    ("dk_pallet_a", "dk_pallet", (6.2, 2.6), 0.4), ("dk_pallet_stack_a", "dk_pallet_stack", (6.5, 3.6), 1.1), ("dk_crate_a", "dk_crate", (6.6, 1.8), 0.8),
    ("dk_hang_lamp", "dk_hang_lamp", (6.8, 2.2), 0.9, 2.95), ("dk_chain", "dk_chain", (4.7, 1.0), 1.5, 2.75),
    ("dk_van", "dk_van", (5.0, 14.6), 1.9), ("dk_stack_a", "dk_pallet_stack", (6.2, 17.8), 1.3), ("dk_stack_b", "dk_pallet_stack", (2.9, 18.6), 1.2), ("dk_pallet_b", "dk_pallet", (5.2, 18.0), 0.4),
    ("dk_street_lamp_a", "dk_street_lamp", (-2.0, 11.0), 5.0), ("dk_street_lamp_b", "dk_street_lamp", (-2.2, 18.0), 4.6), ("dk_street_lamp_c", "dk_street_lamp", (-8.0, 23.3), 4.6), ("dk_street_lamp_d", "dk_street_lamp", (6.8, 19.6), 4.6),
    ("dk_door_lamp", "dk_wall_lamp", (-3.75, 6.2), 0.5, 2.7), ("dk_tunnel_lamp", "dk_wall_lamp", (-11.5, 10.2), 0.45, 2.5), ("dk_tunnel_lamp_b", "dk_wall_lamp", (-8.0, 6.2), 0.45, 2.5), ("dk_tunnel_lamp_c", "dk_wall_lamp", (-14.0, 7.2), 0.45, 2.4),
    ("dk_furnace", "dk_furnace", (12.7, 12.4), 3.2), ("dk_seat_a", "dk_crate", (9.7, 12.3), 0.55), ("dk_seat_b", "dk_crate", (10.35, 12.35), 0.5), ("dk_crate_b", "dk_crate", (10.9, 13.6), 0.7), ("dk_crate_c", "dk_crate", (11.4, 13.2), 0.9),
    ("dk_case_c", "dk_case", (9.0, 9.4), 0.8),
]
# decals (hung on a solid wall within 0.35 m): id, sprite, point (m), size (height m), bottom y, emissive (the wall's own yaw: StoryMap places it)
DECALS = [
    ("dk_dc_door_leaf", "dk_door_leaf", (-3.9, 5.25), 2.1, 0.0, False), ("dk_dc_clef", "dk_clef", (-3.9, 11.0), 2.2, 0.8, False),
    ("dk_dc_pipe_a", "dk_pipe_vert", (-3.9, 4.6), 3.6, 0.0, False), ("dk_dc_pipe_b", "dk_pipe_vert", (-3.9, 11.8), 3.6, 0.0, False), ("dk_dc_pipe_c", "dk_pipe_vert", (-3.9, 2.0), 3.6, 0.0, False),
    # round 2: single windows, placed one by one, few of them lit (the painting's dark buildings); the brown building's lit doorway at the street's end; the passage's violet door
    ("dk_dc_win_a", "dk_win_dark", (-3.9, 13.4), 1.1, 3.4, False), ("dk_dc_win_b", "dk_win_amber", (-3.9, 15.6), 1.1, 4.4, True),
    ("dk_dc_win_c", "dk_win_dark_b", (7.4, 18.6), 1.0, 3.0, False), ("dk_dc_win_d", "dk_win_amber_b", (7.4, 21.4), 1.0, 2.6, True), ("dk_dc_win_e", "dk_win_dark", (7.4, 22.9), 1.0, 3.6, False),
    ("dk_dc_far_door", "dk_far_door", (3.0, 23.9), 3.0, 0.0, True),
    ("dk_dc_win_g", "dk_win_amber", (0.1, 23.9), 1.0, 3.0, True), ("dk_dc_win_h", "dk_win_dark", (5.6, 23.9), 1.0, 3.0, False), ("dk_dc_win_i", "dk_win_amber_b", (6.7, 23.9), 1.0, 3.7, True),
    ("dk_dc_win_j", "dk_win_cold", (-4.2, 23.9), 1.0, 3.0, True), ("dk_dc_win_k", "dk_win_dark_b", (-7.0, 23.9), 1.0, 2.4, False), ("dk_dc_win_l", "dk_win_amber", (-10.6, 23.9), 1.0, 3.3, True),
    ("dk_dc_win_m", "dk_win_dark", (-12.4, 23.9), 1.0, 2.4, False), ("dk_dc_win_n", "dk_win_amber_b", (-13.9, 20.4), 1.0, 2.8, True),
    ("dk_dc_win_p", "dk_win_amber", (1.3, 23.9), 1.0, 3.7, True), ("dk_dc_win_q", "dk_win_amber_b", (-2.6, 23.9), 1.0, 2.6, True), ("dk_dc_win_r", "dk_win_amber", (-8.8, 23.9), 1.0, 2.5, True),
    ("dk_dc_win_s", "dk_win_cold", (7.4, 19.9), 1.0, 2.5, True), ("dk_dc_win_t", "dk_win_amber_b", (-3.9, 14.6), 1.0, 2.4, True),
    ("dk_dc_shop_a", "dk_win_amber", (0.7, 23.9), 1.9, 0.35, True), ("dk_dc_shop_b", "dk_win_amber_b", (5.6, 23.9), 1.9, 0.35, True), ("dk_dc_shop_c", "dk_win_amber", (-5.6, 23.9), 1.7, 0.4, True),
    ("dk_dc_led_a", "dk_neon_blue", (-4.8, 6.1), 0.9, 0.7, True), ("dk_dc_led_b", "dk_neon_blue", (-4.8, 9.9), 0.9, 0.7, True),
    ("dk_dc_violet_door", "dk_violet_door", (-15.9, 8.75), 2.9, 0.0, True),
    ("dk_dc_win_f", "dk_win_amber", (8.9, 15.9), 1.0, 3.6, True), ("dk_dc_win_o", "dk_win_dark_b", (12.6, 15.9), 1.0, 3.2, False), ("dk_dc_fence", "dk_fence", (11.2, 15.9), 2.4, 0.0, False),
    ("dk_dc_pipes_yard", "dk_pipes_yard", (13.4, 12.0), 2.8, 0.5, False), ("dk_dc_yard_shutter", "dk_shutter", (10.5, 8.6), 3.0, 0.0, False),
    ("dk_dc_shutter", "dk_shutter", (7.4, 2.3), 3.3, 0.0, False),
]
LIGHTS = [  # id, point (m), y, radius, colour, strength   (sodium under the canopy and at the street lamps, blue spill from the club door, cold moonlight, the furnace's fire, violet round the Mothership guide)
    ("dk_lt_canopy", (6.8, 2.0), 3.0, 8.0, "#ffa850", 1.8), ("dk_lt_apron", (0.5, 2.2), 3.2, 8.0, "#d8a070", 1.1),
    ("dk_lt_door", (-3.4, 6.2), 2.6, 5.0, "#ffb050", 1.6), ("dk_lt_blue", (-6.5, 8.0), 1.8, 5.0, "#3a60ff", 1.6), ("dk_lt_blue_spill", (-3.4, 8.0), 1.2, 4.5, "#3a60ff", 1.2),
    ("dk_lt_lamp_a", (-1.9, 11.0), 4.6, 6.0, "#ffb860", 1.9), ("dk_lt_lamp_b", (-2.1, 18.0), 4.4, 6.0, "#ffb860", 1.7),
    ("dk_lt_moon", (3.0, 9.0), 6.0, 14.0, "#6a80c0", 0.3),
    ("dk_lt_furnace", (12.2, 12.4), 1.3, 9.0, "#ff7020", 2.0), ("dk_lt_yard", (9.5, 10.0), 3.0, 6.0, "#ffa850", 1.0),
    ("dk_lt_moth", (-0.6, 16.0), 1.6, 5.0, "#a070ff", 1.4), ("dk_lt_hall", (-7.8, 8.7), 2.0, 3.0, "#6a48d0", 0.6),
    # stage D polish, round 2: the lamps' pools are the brightest ground (sodium on the wet tarmac), the dark between them; the far end lit by the brown building's door and the fourth lamp
    ("dk_lt_pool_apron", (2.0, 3.2), 2.8, 7.0, "#ffb060", 1.4), ("dk_lt_pool_door", (-3.0, 7.2), 2.4, 5.0, "#ffb868", 1.2), ("dk_lt_far", (2.0, 21.0), 4.0, 8.0, "#8a70e0", 0.9),
    ("dk_lt_far_lamp", (-8.0, 23.0), 4.5, 8.0, "#ffb860", 1.6), ("dk_lt_run", (-14.6, 8.75), 2.2, 3.6, "#9a5aff", 1.2), ("dk_lt_mouth", (11.0, 13.4), 1.0, 5.0, "#ff9040", 1.6),
    ("dk_lt_pool_s1", (-1.0, 11.2), 3.0, 6.5, "#ffa850", 2.0), ("dk_lt_pool_s2", (3.5, 12.0), 4.0, 9.0, "#7a90e0", 0.3), ("dk_lt_pool_s3", (-1.4, 18.0), 3.0, 6.0, "#ffa850", 1.8),
    ("dk_lt_pool_s4", (4.5, 7.0), 3.0, 6.0, "#ffb060", 1.1), ("dk_lt_pool_walk", (-2.8, 13.0), 2.0, 3.5, "#ffb060", 1.1),
    ("dk_lt_far_lamp_b", (6.5, 19.6), 4.4, 7.0, "#ffb860", 1.6), ("dk_lt_far_door", (3.0, 22.8), 2.4, 6.0, "#ffb060", 2.0),
    ("dk_lt_tunnel_door", (-15.2, 8.75), 0.3, 3.2, "#b070ff", 1.8), ("dk_lt_tunnel_lamp", (-11.5, 9.7), 2.5, 2.6, "#ffa860", 1.4), ("dk_lt_tunnel_lamp_b", (-8.0, 6.6), 2.5, 2.6, "#ffa860", 1.4), ("dk_lt_tunnel_lamp_c", (-14.0, 7.5), 2.4, 2.4, "#ffa860", 1.2), ("dk_lt_doorway", (-4.8, 8.0), 2.0, 3.5, "#4a6aff", 1.6),
]

def barriers(d):
    """Every portal whose floors differ by more than MAX_STEP is a drop and is shut to walkers (`blocked`) while every sector stays reachable from the start; the dock has none (the kerb is 0.25 m)."""
    sec = {s["id"]: s for s in d["sectors"]}
    for w in d["walls"]:
        if w.get("portal") and abs(float(sec[w["sector"]]["floor"]) - float(sec[w["portal"]]["floor"])) > MAX_STEP + 1e-6:
            print("  a drop of more than max_step between %s and %s" % (w["sector"], w["portal"]))


def main():
    d = json.load(open(MAP, encoding="utf-8"))
    names = json.load(open(TRACE, encoding="utf-8"))["sector_names"]
    d["art"] = "doom_dock"
    used = {}
    for s in d["sectors"]:
        nm = names[int(s["doom_sector"])]
        f, w, c, tint, step = STYLE[nm]
        s["floor_tex"], s["wall_tex"], s["ceil_tex"], s["tint"], s["step_tex"] = f, w, ("sky" if nm in SKY_SECTORS else c), lift(tint), step
        s["lip_tex"] = LIP.get(nm, "dk_trim")
        s["room"] = "main"
        s["light"] = LIGHT.get(nm, round(min(1.0, max(LIGHT_FLOOR, float(s["light"]) * LIGHT_GAIN)), 3))
        if nm in AMBIENT:
            s["ambient"] = AMBIENT[nm]
        s.pop("wet", None)
        if nm in WET:
            s["wet"] = WET[nm]
        for k in ("floor_tex", "wall_tex", "ceil_tex", "step_tex", "lip_tex"):
            if s[k] != "sky":
                used[s[k]] = True
    # explicit solid walls with their own texture (one record per stretch; the loader paints the rest of the edge with the sector's wall_tex)
    by_name = {names[int(s["doom_sector"])]: s for s in d["sectors"]}
    d["walls"] = [w for w in d["walls"] if not w.get("dock_solid")]
    for nm, a, b, tex in WALL_TEX:
        d["walls"].append({"from": list(M(*a)), "to": list(M(*b)), "sector": by_name[nm]["id"], "portal": "", "tex": tex, "lower_tex": "", "upper_tex": "", "dock_solid": True})
        used[tex] = True
    sky_ids = {by_name[nm]["id"] for nm in SKY_SECTORS}
    for w in d["walls"]:
        if w.get("portal") and w["sector"] in sky_ids and w["portal"] in sky_ids:
            w["upper_tex"] = "sky"  # two open sectors with different wall heights: no lip band in the air between them, the sky shows
        elif w.get("upper_tex") == "trim":
            w["upper_tex"] = ""  # the loader paints the lip with the lower-ceilinged sector's lip_tex (LIP)
        for k in ("lower_tex", "upper_tex"):
            if w.get(k) == "trim":  # (convert.py's generic kerb name: this scene's own kerb tile)
                w[k] = "dk_trim"
            if w.get(k) and w[k] != "sky":
                used[w[k]] = True
    tex = {}
    for k in sorted(used):
        tex[k] = OWN + k + ".png"
    for _id, spr, *_r in THINGS:
        tex.setdefault(spr, OWN + spr + ".png")
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
    keep = [w for w in d["waypoints"] if not w["id"].startswith("dk_")]
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
    d["start"] = "dk_arrive"
    barriers(d)
    d["sky"] = dict(SKY)
    d["weather"] = json.loads(json.dumps(WEATHER))
    d["fog"] = {"color": "#17152e", "density": 0.014}  # stage D: the rain haze is a lit violet-grey (the painting), thinner
    d["palette_weight"] = 1.0
    # things
    things = [t for t in d["things"] if not str(t["id"]).startswith("dk_")]
    for who, (at, size, lamp) in GUIDES.items():
        x, z = M(*at)
        things.append({"id": "dk_guide_" + who, "kind": "billboard", "sprite": "guide_%s_idle_0" % who, "at": [x, z], "y": round(size * 0.5, 3), "size": size, "anim": "none"})
    for row in THINGS:
        tid, spr, at, size = row[:4]
        x, z = M(*at)
        things.append({"id": tid, "kind": "billboard", "sprite": spr, "at": [x, z], "y": row[4] if len(row) > 4 else round(size * 0.5, 3), "size": size, "anim": "none"})
    for tid, spr, at, size, y, emissive in DECALS:
        x, z = M(*at)
        t = {"id": tid, "kind": "decal", "sprite": spr, "at": [x, z], "y": y, "size": size}
        if emissive:
            t["emissive"] = True
        things.append(t)
    for lid, at, y, rad, col, st in LIGHTS:
        x, z = M(*at)
        things.append({"id": lid, "kind": "light", "at": [x, z], "y": y, "radius": round(rad * REACH, 1), "color": col, "strength": round(min(2.5, st * LAMP_GAIN), 2)})
    for who, (at, size, lamp) in GUIDES.items():  # the lamp over each guide (the choice layer brightens it)
        x, z = M(*lamp)
        things.append({"id": "dk_lamp_" + who, "kind": "light", "at": [x, z], "y": 2.6, "radius": 3.0, "color": "#ffd9a0", "strength": 0.6})
    d["things"] = things
    spots = {k: v for k, v in d.get("spots", {}).items() if not k.startswith("dk_")}
    for who, (at, size, lamp) in GUIDES.items():
        x, z = M(*at)
        spots["dk_guide_" + who] = {"sector": sector_of(d, x, z)["id"], "at": [x, z]}
    d["spots"] = spots
    # the cast: nobody (the painting has only its three guides); content/run/doom/story_doom_dock.json is the world's StoryData, the Night One chapter with an empty cast and the camera moves taken out
    ch = json.load(open(os.path.join(ROOT, "content", "story", "night_one.json"), encoding="utf-8"))
    ch["id"], ch["title"] = "doom_dock", "Doom Dock"
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
    open(os.path.join(ROOT, "content", "run", "doom", "story_doom_dock.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(ch, indent=1) + "\n")
    d["homes"], d["silhouettes"] = [], []
    d["scene"] = {"id": "doom_dock", "reference": "art/reference/doom_worlds/Rainy Rhythm Club Loading Dock-6.png", "routes": ROUTES,
                  "note": "authored by tools/doom/author_dock.py; routes are lists of waypoint ids (the polyline); hold_bars on a waypoint is the still hold at a choice window"}
    d["doom"]["authored"] = True
    json.dump(d, open(MAP, "w", encoding="utf-8", newline="\n"), indent=1)
    open(MAP, "a", encoding="utf-8", newline="\n").write("\n")
    print("authored %d waypoints, %d things (%d decals), %d spots into %s" % (len(WAYPOINTS), len(things), len(DECALS), len(spots), MAP))


if __name__ == "__main__":
    sys.exit(main())
