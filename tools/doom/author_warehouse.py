"""Authors the Warehouse pilot scene into content/story/maps/doom_warehouse.json (docs/doom/scenes/warehouse.md).

    python -I tools/doom/trace/warehouse_scene.py; python -I tools/doom/convert.py --scene warehouse --trace tools/doom/trace/warehouse_pilot.json     # the geometry (this script's input)
    python -I tools/doom/author_warehouse.py                                                      # waypoints, textures, things, lights, spots (idempotent; run after every convert)

All coordinates below are Doom units (32 = 1 m, x east, y north) and are converted like convert.py does (x_m = x / 32, z_m = -y / 32). A waypoint names the sector that holds it and
keeps the 0.5 m margin StoryMap wants (the script moves nothing: it stops with the id when a point is too close to a wall).

Routes are lists of waypoint ids (`ROUTES`): one hop today (the rail's player_move goes to the last id), the whole polyline when the rail extension lands. `hold_bars` on a choice
viewpoint is the number of bars the camera holds still there (today's rail ignores it).
"""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MAP = os.path.join(ROOT, "content", "story", "maps", "doom_warehouse.json")
TRACE = os.path.join(ROOT, "tools", "doom", "trace", "warehouse_pilot.json")
NIGHT = "res://assets/story/night_one/textures/"
OWN = "textures/"
MARGIN = 0.5
MARGINS = {"wh_v_bar_e1": 0.33, "wh_v_bar_mid": 0.33, "wh_v_bar_e2": 0.33}  # via points in the narrow walkway east of the bar: the loader's 0.3 m (StoryMap.WAYPOINT_MARGIN) plus a little
MAX_STEP = 0.5  # metres: a floor change across a portal up to this is a step a walker takes (the map key `max_step`, docs/story/HEIGHTS_AND_PATHS.md); taller is a drop
RAIL_TEX = "wh_railing"  # the lattice tile with alpha (tools/doom/art/make_railing.py)
RAIL_HEIGHT = 1.0
VOID_DEPTH = -2.0  # a sector with a floor this low (the ring's four slots, -3 m) is a pit: its rim gets a railing


def m(x, y):
    return (round(x / 32.0, 4), round(-y / 32.0, 4))


def face(a, b):
    """The yaw of a view from doom point a towards doom point b (0 faces -z, 90 faces -x)."""
    dx, dy = (b[0] - a[0]) / 32.0, (b[1] - a[1]) / 32.0
    return round(math.degrees(math.atan2(-dx, dy)), 1)


# id, doom point, look-at doom point (or a yaw), hold_bars (0 = a moving place), what it is.
# Names starting wh_v_ are via points only: corners of the polyline moves (tools/run/make_doom.py), never stood on.
WAYPOINTS = [
    ("wh_arrive", (-720, -715), (500, 500), 0, "arrival: the ring's south-west corner facing the floor (a cut, then a short walk to the reference viewpoint)"),
    ("wh_ref", (-620, -600), (500, 500), 8, "THE reference viewpoint: the ring's south-west corner looking across the fenced floor, the stage ahead, bar left, lounge right"),
    ("wh_ref_back", (-705, -660), (500, 500), 0, "recovery: a stumble back into the corner"),
    ("wh_sw_corner", (-710, -520), (500, 500), 0, "recovery: along the west band"),
    ("wh_fence", (-48, -474), (400, -500), 2, "reveal: on the floor against the south railing, looking along it, the platforms across the floor"),
    ("wh_plinths", (-640, 100), (0, 0), 2, "reveal: the west band north of the bar, the platforms across the railing"),
    ("wh_platform", (66, 22), (-300, -190), 2, "reveal: up on the central pedestal (the lit cube), the stage across the floor"),
    ("wh_stage_approach", (-360, -470), (-300, -190), 2, "approach to the stage, leg 1: through the south gate onto the floor"),
    ("wh_stage_steps", (-410, -150), (-300, -190), 0, "approach to the stage, leg 2: the foot of the stage steps (west side)"),
    ("wh_stage_top", (-224, -150), (-300, -190), 0, "THRESHOLD ahead: on the stage, the world transition happens here"),
    ("wh_bar_approach", (-640, -500), (-600, -300), 2, "approach to the bar"),
    ("wh_bar_door", (-640, -425), (-600, -300), 0, "THRESHOLD left: the bar room's opening"),
    ("wh_lounge_approach", (-650, -585), (-465, -604), 2, "approach to the lounge"),
    ("wh_lounge_door", (-575, -585), (-465, -604), 0, "THRESHOLD right: the lounge room's opening"),
    # via points (corners of the polyline moves)
    ("wh_v_lounge_w", (-595, -557), (-360, -560), 0, "via: the ring west of the lounge, before the walkway between the lounge and the railing"),
    ("wh_v_gate_s", (-360, -560), (-360, -470), 0, "via: the walkway outside the south gate (between the lounge's north wall and the gate)"),
    ("wh_v_court_sw", (-352, -474), (-360, -560), 0, "via: the floor inside the south gate, west of the south plinth"),
    ("wh_v_bar_e1", (-531, -448), (-534, -320), 0, "via: the walkway east of the bar, south end"),
    ("wh_v_bar_mid", (-534, -320), (-564, -115), 0, "via: the walkway east of the bar, middle (keeps the line off the bar wall's north-east corner)"),
    ("wh_v_bar_e2", (-564, -115), (-640, 100), 0, "via: the west band north of the bar"),
    ("wh_v_gate_w_out", (-586, -80), (-464, -64), 0, "via: the west band outside the west gate"),
    ("wh_v_gate_w_in", (-464, -64), (-128, -32), 0, "via: the floor inside the west gate"),
    ("wh_v_court_n", (-128, -32), (67, -134), 0, "via: the floor north of the stage, west of the pedestal"),
    ("wh_ped_foot", (67, -134), (66, 22), 0, "via: the foot of the pedestal stairs"),
]
ROUTES = {  # the destination routes and the stay loop as lists of waypoint ids, via points included (the last is the threshold / the return); tools/run/make_doom.py cuts them into moves
    "ahead": ["wh_v_lounge_w", "wh_v_gate_s", "wh_stage_approach", "wh_stage_steps", "wh_stage_top"],
    "left": ["wh_bar_approach", "wh_bar_door"],
    "right": ["wh_lounge_approach", "wh_lounge_door"],
    "stay": ["wh_v_bar_e1", "wh_v_bar_mid", "wh_v_bar_e2", "wh_plinths", "wh_v_gate_w_out", "wh_v_gate_w_in", "wh_v_court_n", "wh_ped_foot", "wh_platform", "wh_ped_foot", "wh_fence",
             "wh_v_court_sw", "wh_v_gate_s", "wh_v_lounge_w", "wh_ref"],
    "arrive": ["wh_arrive", "wh_ref"],
    "stumble": ["wh_ref_back", "wh_sw_corner", "wh_ref"],
}
# sector (by the trace's name) -> floor, wall, ceiling texture, tint. The Warehouse's own tiles (tools/doom/art/make_warehouse_art.py, stage D polish); a wall named WALLS gets one of
# its variants per piece (a hash of the piece id), so no long wall repeats one tile.
STYLE = {
    "stone_ring": ("wh_walk", "WALLS", "wh_roof", "#b8c8ff"),
    "plate": ("wh_walk", "WALLS", "wh_roof", "#c8d4ff"),
    "courtyard": ("wh_dance", "wh_steel_b", "wh_roof", "#8aa4ff"),
    "terrace": ("wh_walk", "BRICKS", "wh_roof", "#9fb0e8"),
    "nub": ("wh_walk", "wh_steel_c", "wh_ceil_bar", "#aab8f0"),
    "pedestal": ("wh_stage_boards", "wh_cube", "wh_roof", "#ff8aa8"),
    "ped_step_a": ("wh_stage_boards", "wh_trim", "wh_roof", "#ffa8bc"),
    "ped_step_b": ("wh_stage_boards", "wh_trim", "wh_roof", "#ffa8bc"),
    "stage_step_a": ("wh_stage_boards", "wh_trim", "wh_roof", "#c8d0ff"),
    "stage_step_b": ("wh_stage_boards", "wh_trim", "wh_roof", "#c8d0ff"),
    "stage": ("wh_stage_boards", "wh_steel_c", "wh_roof", "#d0d8ff"),
    "gate_step_s": ("wh_walk", "wh_trim", "wh_roof", "#b8c8ff"),
    "gate_step_w": ("wh_walk", "wh_trim", "wh_roof", "#b8c8ff"),
    "bar": ("wh_boards", "wh_bar_brick", "wh_ceil_bar", "#ffc080"),
    "lounge": ("wh_carpet", "wh_velvet", "wh_ceil_lounge", "#ffd090"),
}
for k in ("plat_n", "plat_e", "plat_w", "plat_s"):
    STYLE[k] = ("wh_walk", "wh_speaker", "wh_roof", "#b8c8ff")
for k in ("pit_n1", "pit_n2", "pit_s1", "pit_s2"):
    STYLE[k] = ("wh_grate", "wh_steel_a", "wh_roof", "#6a80d0")
VARIANTS = {"WALLS": ["wh_steel_a", "wh_brick_a", "wh_steel_b", "wh_brick_b", "wh_steel_c", "wh_brick_c"], "BRICKS": ["wh_brick_a", "wh_brick_b", "wh_brick_c"]}
OWN_TILES = ["wh_walk", "wh_grate", "wh_dance", "wh_boards", "wh_stage_boards", "wh_carpet", "wh_steel_a", "wh_steel_b", "wh_steel_c", "wh_brick_a", "wh_brick_b", "wh_brick_c",
             "wh_bar_brick", "wh_velvet", "wh_roof", "wh_ceil_bar", "wh_ceil_lounge", "wh_trim", "wh_speaker", "wh_cube"]
PROPS = ["wh_p_banner", "wh_p_banner_b", "wh_p_speaker", "wh_p_backbar", "wh_p_counter", "wh_p_lamp_cu", "wh_p_lamp_lg", "wh_p_pelmet", "wh_p_case", "wh_p_window", "wh_p_beam",
         "wh_p_case2", "wh_p_plant", "wh_p_sofa", "wh_p_pendant", "wh_p_sconce"]
BORROWED = ["thing_truss_tower"]
LIGHT_GAIN, LIGHT_FLOOR, TINT_LIFT, LAMP_GAIN = 2.0, 0.9, 0.75, 2.5  # exposure (docs/doom/scenes/warehouse.md): the Doom lights are low for this renderer; A1's night-interior median is 0.25 to 0.38
STATES = {"idle": 1, "available": 5, "selected": 2, "committed": 2}
GUIDES = {  # id suffix: doom point, size (height m), lamp point
    "stage": ((-300, -190), 2.2, (-330, -190)),
    "bar": ((-600, -300), 2.2, (-600, -250)),
    "lounge": ((-465, -604), 2.2, (-440, -604)),
}
# stage D exposure pass: the painting's caged wall lanterns along the hall's walls (here the faces of the 3 m terrace riser round the walkway), each a small emissive
# billboard 0.25 m off the wall with an amber wall-wash light (SCONCE_LIGHTS): warm practicals against the cobalt, as the painting's far wall has them
SCONCES = [(-735, -300), (-735, 120), (-735, 520), (-300, -735), (120, -735), (520, -735), (-300, 735), (120, 735), (520, 735), (735, -300), (735, 120), (735, 520)]
THINGS = [  # extra dressing: id, sprite, doom point, y (centre over the floor), size (height m), extra keys (blend, emissive)
    # over the floor (the painting's rig): two hanging speaker stacks, treble-clef banners at the hall's far sides, four spotlight shafts (additive), the truss towers
    ("wh_spk_a", "wh_p_speaker", (-120, 60), 6.4, 2.6, {}), ("wh_spk_b", "wh_p_speaker", (180, -170), 6.4, 2.6, {}),
    ("wh_banner_a", "wh_p_banner", (-360, 560), 5.6, 3.4, {}), ("wh_banner_b", "wh_p_banner_b", (560, -380), 5.6, 3.4, {}), ("wh_banner_c", "wh_p_banner", (300, 600), 5.6, 3.4, {}),
    ("wh_beam_a", "wh_p_beam", (-250, 120), 4.8, 8.0, {"blend": "add"}), ("wh_beam_b", "wh_p_beam", (-20, -60), 4.8, 8.0, {"blend": "add"}),
    ("wh_beam_c", "wh_p_beam", (200, 230), 4.8, 8.0, {"blend": "add"}), ("wh_beam_d", "wh_p_beam", (260, -20), 4.8, 8.0, {"blend": "add"}),
    # stage D exposure pass: more of the painting's shafts (it has six or more over the floor), so every view across the floor has one
    ("wh_beam_e", "wh_p_beam", (150, -380), 4.8, 8.0, {"blend": "add"}), ("wh_beam_f", "wh_p_beam", (420, -330), 4.8, 8.0, {"blend": "add"}),
    ("wh_beam_g", "wh_p_beam", (-380, 360), 4.8, 8.0, {"blend": "add"}), ("wh_beam_h", "wh_p_beam", (380, 420), 4.8, 8.0, {"blend": "add"}),
    ("wh_beam_i", "wh_p_beam", (-120, 420), 4.8, 8.0, {"blend": "add"}),
    ("wh_truss_a", "thing_truss_tower", (-720, 720), 2.5, 5.0, {}), ("wh_truss_b", "thing_truss_tower", (720, -720), 2.5, 5.0, {}),
    ("wh_truss_c", "thing_truss_tower", (730, 540), 2.5, 5.0, {}),
    # the stage: the window onto the night city behind the guide (a backdrop billboard: there is no wall there)
    ("wh_window", "wh_p_window", (-230, -120), 3.1, 3.2, {"emissive": True}),
    ("wh_pend_stage_a", "wh_p_pendant", (-330, -250), 3.9, 1.0, {"emissive": True}), ("wh_pend_stage_b", "wh_p_pendant", (-330, -130), 3.9, 1.0, {"emissive": True}),
    ("wh_pend_bar_in", "wh_p_pendant", (-680, -260), 3.0, 0.8, {"emissive": True}),
    # the bar: counter in front of the guide (two halves), the copper lamp over him, the flight cases and a plant on the walkway at its mouth
    ("wh_counter_a", "wh_p_counter", (-622, -335), 0.65, 1.3, {}), ("wh_counter_b", "wh_p_counter", (-588, -337), 0.65, 1.3, {}),
    ("wh_pend_copper", "wh_p_lamp_cu", (-606, -300), 3.0, 0.9, {"emissive": True}), ("wh_case_a", "wh_p_case", (-700, -440), 0.55, 1.1, {}),
    ("wh_case_b", "wh_p_case2", (-725, -470), 0.35, 0.7, {}), ("wh_plant_bar", "wh_p_plant", (-575, -420), 0.75, 1.5, {}),
    # the lounge: the lamp beside the guide, the oxblood sofa behind him, a plant at its mouth
    ("wh_stdlamp_lounge", "wh_p_lamp_lg", (-440, -625), 0.85, 1.7, {"emissive": True}), ("wh_sofa", "wh_p_sofa", (-430, -700), 0.5, 0.95, {}),
    ("wh_plant_lounge", "wh_p_plant", (-530, -728), 0.75, 1.5, {}),
    # stage D exposure pass: the painting's hanging pendants over the walkway (emissive, each with its amber pool below: WALK_PENDANTS)
] + [("wh_sconce_%d" % i, "wh_p_sconce", at, 2.3, 1.1, {"emissive": True}) for i, at in enumerate(SCONCES)] + [("wh_pend_%d" % i, "wh_p_pendant", at, 3.4, 1.0, {"emissive": True}) for i, at in enumerate(((-640, -470), (-470, -545), (-660, -120), (-120, -660), (-660, 260), (260, -660), (-660, 620), (620, -660)))]
WET = {  # stage D: the painting's wet floor (the weather engine's gloss, a dry map: the practicals' highlights smeared on the floor toward the eye)
    "stone_ring": 0.75, "plate": 0.75, "gate_step_s": 0.6, "gate_step_w": 0.6, "courtyard": 0.55, "terrace": 0.5,
}
DECALS = [  # on a wall: id, sprite, doom point (within 0.35 m of a wall of its sector), y (bottom edge), height m, emissive
    ("wh_backbar_a", "wh_p_backbar", (-690, -206), 1.0, 1.7, True), ("wh_backbar_b", "wh_p_backbar", (-620, -206), 1.0, 1.7, True),
    ("wh_pelmet", "wh_p_pelmet", (-406, -662), 2.2, 1.6, False),
    ("wh_sconce_bar", "wh_p_sconce", (-562, -300), 1.8, 1.0, True),  # stage D: the caged lantern on the bar's outer wall, facing the walkway
]
LIGHTS = [  # id, doom point, y, radius, colour, strength   (cobalt over the floor and the walkway, amber in the bar and the lounge, a cool pool on the stage)
    ("wh_lt_floor", (0, 0), 6.0, 16.0, "#4a72ff", 1.6), ("wh_lt_cube", (66, 22), 3.2, 5.0, "#ff4b6e", 1.4),
    ("wh_lt_spot_nw", (-300, 300), 6.0, 11.0, "#5f88ff", 1.4), ("wh_lt_spot_ne", (300, 300), 6.0, 11.0, "#5f88ff", 1.4),
    ("wh_lt_spot_se", (300, -300), 6.0, 11.0, "#5f88ff", 1.4), ("wh_lt_spot_sw", (-300, -300), 6.0, 11.0, "#5f88ff", 1.4),
    ("wh_lt_stage", (-300, -190), 4.5, 7.0, "#a8c8ff", 1.5), ("wh_lt_stage_key", (-320, -215), 3.6, 3.2, "#ffc890", 2.4),
    ("wh_lt_bar", (-640, -300), 3.4, 6.5, "#ffa84a", 1.8), ("wh_lt_bar2", (-600, -380), 3.0, 5.0, "#ffb860", 1.4),
    ("wh_lt_lounge", (-465, -640), 3.4, 6.5, "#ffb860", 1.8), ("wh_lt_lounge2", (-480, -604), 3.0, 5.0, "#ffc878", 1.4),
    ("wh_lt_ref", (-620, -540), 3.4, 11.0, "#7a98ff", 1.4), ("wh_lt_ring_w", (-640, 100), 3.4, 11.0, "#6a88ff", 1.2), ("wh_lt_ring_s", (60, -640), 3.4, 11.0, "#6a88ff", 1.2),
    ("wh_lt_ring_e", (640, 100), 3.4, 11.0, "#6a88ff", 1.2), ("wh_lt_ring_n", (0, 640), 3.4, 11.0, "#6a88ff", 1.2),
    # stage D: the painting's amber floor lights at the speaker plinths' feet and the walkway's pendant pools (warm practicals against the cobalt), lifting the mid-tones
    ("wh_lt_plinth_sw", (-330, -330), 0.7, 5.0, "#ffa040", 2.0), ("wh_lt_plinth_nw", (-330, 330), 0.7, 5.0, "#ffa040", 2.0),
    ("wh_lt_plinth_se", (330, -330), 0.7, 5.0, "#ffa040", 2.0), ("wh_lt_plinth_ne", (330, 330), 0.7, 5.0, "#ffa040", 2.0),
    ("wh_lt_walk_w", (-640, -470), 3.0, 5.5, "#ffb860", 1.6), ("wh_lt_walk_s", (-470, -540), 3.0, 5.5, "#ffb860", 1.6),
    # stage D exposure pass: an amber pool under every walkway pendant (the painting's warm pools on the wet steel against the cobalt hall) and the bar's wall lantern
    ("wh_lt_pend_w2", (-660, -120), 2.8, 5.0, "#ffb050", 1.6), ("wh_lt_pend_s2", (-120, -660), 2.8, 5.0, "#ffb050", 1.6),
    ("wh_lt_pend_w3", (-660, 260), 2.8, 5.0, "#ffb050", 1.6), ("wh_lt_pend_s3", (260, -660), 2.8, 5.0, "#ffb050", 1.6),
    ("wh_lt_pend_w4", (-660, 620), 2.8, 5.0, "#ffb050", 1.6), ("wh_lt_pend_s4", (620, -660), 2.8, 5.0, "#ffb050", 1.6),
    ("wh_lt_sconce_bar", (-575, -300), 2.0, 3.5, "#ffa040", 1.4),
] + [("wh_lt_sconce_%d" % i, (x - 30 * (x > 0) + 30 * (x < 0) if abs(x) == 735 else x, y - 30 * (y > 0) + 30 * (y < 0) if abs(y) == 735 else y), 2.3, 5.0, "#ffa848", 1.8)
     for i, (x, y) in enumerate(SCONCES)]


def barriers(d):
    """Closes what a walker must not cross and puts the railing where the painting has a fence.
    * A portal whose floors differ by more than MAX_STEP is a drop and is shut to walkers (`blocked`: the sides of the stage and pedestal stairs, the pits, the terrace) as long as
      every sector stays reachable from the start through the portals that are left (the map loader demands that): a pit or the terrace keeps one portal, the one farthest
      from the middle (a dead end: no route goes through it, and the rail check never puts a camera there).
    * The 1 m ledge between the dance floor and the walkway and every shut rim of a pit (a sector with a floor of VOID_DEPTH or lower) are the renderer's `railing` kind: a
      see-through lattice strip, so the floor is seen through the fence."""
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
        pit = min(float(a["floor"]), float(b["floor"])) <= VOID_DEPTH
        ledge = {a["doom_sector"], b["doom_sector"]} == {9, 10}  # courtyard over the stone ring: the render's 1 m ledge
        if w.get("blocked") and (ledge or pit):
            w["kind"], w["tex"], w["height"] = "railing", RAIL_TEX, RAIL_HEIGHT


def lift(h):
    """A tint paler by TINT_LIFT towards white (a tint multiplies the texture: a saturated cobalt eats most of its light)."""
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


def main():
    d = json.load(open(MAP, encoding="utf-8"))
    names = json.load(open(TRACE, encoding="utf-8"))["sector_names"]
    d["art"] = "doom_warehouse"
    used = {}
    for s in d["sectors"]:
        nm = names[int(s["doom_sector"])]
        f, w, c, tint = STYLE[nm]
        if w in VARIANTS:
            w = VARIANTS[w][sum(ord(ch) * (i + 1) for i, ch in enumerate(str(s["id"]))) % len(VARIANTS[w])]
        s["floor_tex"], s["wall_tex"], s["ceil_tex"], s["tint"] = f, w, c, lift(tint)
        s["room"] = "main"
        s["light"] = round(min(1.0, max(LIGHT_FLOOR, float(s["light"]) * LIGHT_GAIN)), 3)
        if nm in WET:
            s["wet"] = WET[nm]
        else:
            s.pop("wet", None)
    for s in d["sectors"]:
        for k in ("floor_tex", "wall_tex", "ceil_tex"):
            used[s[k]] = True
    for w in d["walls"]:
        for k in ("lower_tex", "upper_tex"):
            if w.get(k) == "trim":
                w[k] = "wh_trim"
            if w.get(k):
                used[w[k]] = True
    tex = {}
    for k in sorted(set(used) | set(BORROWED) | set(OWN_TILES) | set(PROPS)):
        tex[k] = (OWN if k.startswith("wh_") else NIGHT) + k + ".png"
    for g, n in STATES.items():
        pass
    for who in GUIDES:
        for st, n in STATES.items():
            for i in range(n):
                tex["guide_%s_%s_%d" % (who, st, i)] = OWN + "guide_%s_%s_%d.png" % (who, st, i)
    tex[RAIL_TEX] = OWN + RAIL_TEX + ".png"
    d["textures"] = tex
    d["max_step"] = MAX_STEP
    d["visibility"] = {"mode": "clip", "depth": 48, "far": 0}  # 72 pieces: the portal walk that narrows its window at every portal (the flood's 7 portals is too few for an open hall)
    barriers(d)
    d["sky"] = {}
    d["fog"] = {"color": "#3654b8", "density": 0.021}
    d["palette_weight"] = 1.0
    # waypoints
    keep = [w for w in d["waypoints"] if not w["id"].startswith("wh_")]
    for wid, at, look, hold, _why in WAYPOINTS:
        x, z = m(*at)
        s = sector_of(d, x, z)
        floor0 = s["floor"] if s else None
        margin = MARGINS.get(wid, MARGIN)
        if s is None or dist_to_edges(s["polygon"], x, z) < margin:  # too near a piece edge (the decomposition's diagonals count): the nearest free spot on the same floor height
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
        w = {"id": wid, "at": [x, z], "yaw": face(at, look), "sector": s["id"]}
        if hold:
            w["hold_bars"] = hold
        keep.append(w)
    d["waypoints"] = keep
    # things
    things = [t for t in d["things"] if not str(t["id"]).startswith("wh_")]
    for who, (at, size, lamp) in GUIDES.items():
        x, z = m(*at)
        things.append({"id": "wh_guide_" + who, "kind": "billboard", "sprite": "guide_%s_idle_0" % who, "at": [x, z], "y": round(size * 0.5, 3), "size": size, "anim": "none"})
    for tid, spr, at, y, size, extra in THINGS:
        x, z = m(*at)
        things.append({"id": tid, "kind": "billboard", "sprite": spr, "at": [x, z], "y": y, "size": size, "anim": "none", **extra})
    for tid, spr, at, y, size, emi in DECALS:
        x, z = m(*at)
        dd = {"id": tid, "kind": "decal", "sprite": spr, "at": [x, z], "y": y, "size": size}
        if emi:
            dd["emissive"] = True
        things.append(dd)
    for lid, at, y, rad, col, st in LIGHTS:
        x, z = m(*at)
        things.append({"id": lid, "kind": "light", "at": [x, z], "y": y, "radius": round(rad * 1.3, 1), "color": col, "strength": round(min(2.5, st * LAMP_GAIN), 2)})
    for who, (at, size, lamp) in GUIDES.items():  # the lamp over each guide: a light thing the choice layer brightens (needs the engine's choice-state contract)
        x, z = m(*lamp)
        things.append({"id": "wh_lamp_" + who, "kind": "light", "at": [x, z], "y": 2.8, "radius": 3.0, "color": "#ffd9a0", "strength": 0.6})
    for t in things:
        if t.get("kind") == "billboard":
            t.pop("sector", None)
    d["things"] = things
    # spots: named places for the guides and the loop (a spot needs a sector of its own)
    spots = {k: v for k, v in d.get("spots", {}).items() if not k.startswith("wh_")}
    for who, (at, size, lamp) in GUIDES.items():
        x, z = m(*at)
        spots["wh_guide_" + who] = {"sector": sector_of(d, x, z)["id"], "at": [x, z]}
    d["spots"] = spots
    # the crowd: the night_one chapter's cast (copied to content/run/doom/story_doom_warehouse.json, the world's StoryData) dances on the fenced floor
    ch = json.load(open(os.path.join(ROOT, "content", "story", "night_one.json"), encoding="utf-8"))
    ch["id"], ch["title"] = "doom_warehouse", "Doom Warehouse (pilot)"
    ch["art"] = "night_one"
    for b in ch["blocks"]:  # the legacy night's camera moves belong to its own map: the Doom scene's camera is the run's rail (crowd and light events stay)
        b["events"] = [e for e in b.get("events", []) if not str(e.get("action", "")).startswith("player_") and str(e.get("action", "")) != "doors_open"]
    for dec in ch["decisions"]:
        for k in ("good", "bad"):
            dec[k] = [e for e in dec.get(k, []) if not (isinstance(e, dict) and str(e.get("action", "")).startswith("player_"))]
    for e in ch["endings"].values():
        e["journey"] = []
    open(os.path.join(ROOT, "content", "run", "doom", "story_doom_warehouse.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(ch, indent=1) + "\n")
    floor_secs = [s for s in d["sectors"] if abs(s["floor"] - 1.0) < 0.01 and s["doom_sector"] == names.index("courtyard")]
    pts = []
    gx = -15.0
    while gx <= 15.0:
        gz = -15.0
        while gz <= 15.0:
            for s in floor_secs:
                if inside(s["polygon"], gx, gz) and dist_to_edges(s["polygon"], gx, gz) >= 0.32:
                    pts.append((round(gx, 2), round(gz, 2), s["id"]))
                    break
            gz += 0.8
        gx += 0.8
    pts.sort(key=lambda p: (int(p[0] * 977 + p[1] * 1931) * 2654435761) % 4294967296)
    rx, rz = m(-620, -600)  # the crowd packs the near half of the floor, between the fence and the stage, as the painting's does (the far half stays sparse)
    gx_, gz_ = m(*GUIDES["stage"][0])
    ux, uz = (gx_ - rx), (gz_ - rz)
    ul = math.hypot(ux, uz)

    def in_sightline(p):  # the lane from the reference viewpoint to the stage guide stays clear (the painting sees her over the crowd; here the eye is lower)
        t = ((p[0] - rx) * ux + (p[1] - rz) * uz) / (ul * ul)
        return 0.0 < t < 1.15 and abs((p[0] - rx) * uz - (p[1] - rz) * ux) / ul < 2.4

    pts = [p for p in pts if not in_sightline(p)]
    near = [p for p in pts if 4.5 <= math.hypot(p[0] - rx, p[1] - rz) <= 17.0]
    pts = near + [p for p in pts if p not in near]
    need = len(ch["actors"]) + len(ch["silhouettes"])
    if len(pts) < need:
        raise SystemExit("only %d floor spots for %d people" % (len(pts), need))
    d["homes"] = [{"actor": a["id"], "sector": pts[i][2], "at": [pts[i][0], pts[i][1]]} for i, a in enumerate(ch["actors"])]
    d["silhouettes"] = [{"id": s["id"], "at": [pts[len(ch["actors"]) + i][0], pts[len(ch["actors"]) + i][1]]} for i, s in enumerate(ch["silhouettes"])]
    d["scene"] = {"id": "doom_warehouse", "reference": "art/reference/doom_worlds/Cobalt Warehouse Dance Floor-1.png", "routes": ROUTES,
                  "note": "authored by tools/doom/author_warehouse.py; routes are lists of waypoint ids (one hop today, the polyline later); hold_bars on a waypoint is the still hold at a choice window"}
    d["doom"]["authored"] = True
    json.dump(d, open(MAP, "w", encoding="utf-8", newline="\n"), indent=1)
    open(MAP, "a", encoding="utf-8", newline="\n").write("\n")
    print("authored %d waypoints, %d things, %d spots into %s" % (len(WAYPOINTS), len(things), len(spots), MAP))


if __name__ == "__main__":
    sys.exit(main())
