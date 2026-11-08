"""Authors the Mothership scene into content/story/maps/doom_mothership.json (docs/doom/scenes/mothership.md), the Booth's pipeline (tools/doom/author_booth.py) for MAP11.

    python -I tools/doom/trace/mothership_scene.py; python -I tools/doom/convert.py --scene mothership --trace tools/doom/trace/mothership_pilot.json     # the geometry (this script's input)
    python -I tools/doom/author_mothership.py          # waypoints, textures, things, decals, lights, spots, crowd (idempotent; run after every convert)

Coordinates in this file are METRES (x east, y north, as the trace); `M` turns them into the map's (x, z = -y). Places on the ring are written as (radius, angle) about the centre of the atrium.
A waypoint keeps the 0.5 m margin StoryMap wants; the script moves nothing but a point too close to a wall, and says so. Routes are lists of waypoint ids (`ROUTES`);
tools/run/make_doom_mothership.py cuts them into the rail's polyline moves. `hold_bars` on a waypoint is the number of bars the camera holds still.
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "trace"))
import mothership_scene as sc  # noqa: E402  (the same centre, radii and rails)

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
MAP = os.path.join(ROOT, "content", "story", "maps", "doom_mothership.json")
TRACE = os.path.join(ROOT, "tools", "doom", "trace", "mothership_pilot.json")
NIGHT = "res://assets/story/night_one/textures/"
OWN = "textures/"
MARGIN = 0.5
MARGINS = {"ms_v_br": 0.4, "ms_booth_hatch": 0.45}
MAX_STEP = 0.5
RAIL_HEIGHT = 0.95  # (round 2: 1.1 -> 0.95, the parapet opened: the pool shows over it and through its ovals in the pitched choice view) the balustrade round the void, metres above the ring's floor
LIGHT_GAIN, LIGHT_FLOOR, TINT_LIFT, LAMP_GAIN = 1.3, 0.45, 0.08, 2.4
REF_BEARING = 47.0  # the reference viewpoint looks this many degrees north of east
PAINTING = "art/reference/doom_worlds/Mothership Ringwalk Over the Void-7.png"


def M(x, y):
    return (round(x, 4), round(-y, 4))


def P(r, ang):
    """A point (m) at radius r and angle ang (degrees, 0 east, counter-clockwise) about the atrium's centre."""
    a = math.radians(ang)
    return (round(sc.CX + r * math.cos(a), 3), round(sc.CY + r * math.sin(a), 3))


def face(a, b):
    """The yaw of a view from the point a (metres, x east, y north) towards b (0 faces north / -z, 90 faces -x)."""
    return round(math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1])), 1)


RING = 7.75  # the walkway's centre line
REF_AT = P(6.9, -112.5)  # (round 2: 0.85 m nearer the rim, so the pitched view looks over the parapet into the pool)
REF_LOOK = (REF_AT[0] + 10 * math.cos(math.radians(REF_BEARING)), REF_AT[1] + 10 * math.sin(math.radians(REF_BEARING)))


def ahead(at_r, at_ang, deg=14.0):
    """A look point a little further round the ring (the direction of travel, counter-clockwise)."""
    return P(at_r, at_ang + deg)


GUIDE_AT = {"underworld": P(11.6, 6.0), "booth": (0.0, 15.6), "dock": P(10.5, -38.0)}

# id, point (m), look-at point (m), hold_bars (0 = a moving place), what it is.  Names starting ms_v_ are via points only: corners of the polyline moves, never stood on.
WAYPOINTS = [
    ("ms_arrive", P(RING, -137.0), REF_LOOK, 0, "arrival: the ring's south west (a cut, then a three bar walk to the reference viewpoint)"),
    ("ms_ref", REF_AT, REF_LOOK, 8, "THE reference viewpoint: on the ring walk looking east-north-east, the void on the left with the platform and the Booth guide across it, the Underworld stair ahead, the Dock hatch on the right"),
    ("ms_ref_back", P(8.6, -122.0), REF_LOOK, 0, "recovery: a stumble back against the outer wall"),
    ("ms_sw_corner", P(RING, -140.0), REF_LOOK, 0, "recovery: along the rim"),
    ("ms_hub_view", P(RING, -72.0), (0.0, 15.5), 2, "reveal: the ring's south, the platform in the void and the Booth guide across the railing"),
    ("ms_stair_view", P(RING, -28.0), P(13.0, 0.0), 2, "reveal: the ring's east, the stair and the hatch up to the Underworld"),
    ("ms_bridge_view", P(4.0, -90.0), P(11.0, -48.0), 2, "reveal: the middle of the bridge, the void on both sides, looking back along the ring to the Dock hatch"),
    ("ms_uw_hatch", P(11.75, -2.0), P(14.0, 0.5), 1, "THRESHOLD ahead (Underworld): on the landing, a step back from the hatch so its arch and the lit alcove frame it (not a wall filling the frame); the world transition happens here"),
    ("ms_booth_hatch", (0.0, 13.6), (0.0, 17.0), 1, "THRESHOLD left (Booth): the hatch on the platform, the world transition happens here"),
    ("ms_dock_in", P(10.8, -46.0), P(13.4, -45.0), 1, "THRESHOLD right (Dock): in the alcove, held back 2.5 m from the hatch so the hatch, its lamps and the alcove's sides frame the way on; the world transition happens here"),
    # via points (corners of the polyline moves; the ring ones are 22.5 degrees apart: the chord stays 1.1 m off the rim)
    ("ms_v_a1", P(RING, -90.0), P(RING, -76.0), 0, "via: the ring's south, in front of the bridge"),
    ("ms_v_a2", P(RING, -67.5), P(RING, -53.0), 0, "via: the ring"),
    ("ms_v_a3", P(RING, -45.0), P(RING, -31.0), 0, "via: the ring in front of the Dock hatch"),
    ("ms_v_a4", P(RING, -22.5), P(RING, -8.0), 0, "via: the ring"),
    ("ms_v_uw", P(8.0, -8.0), P(13.0, -4.0), 0, "via: the foot of the Underworld stair"),
    ("ms_v_dk", P(8.2, -48.0), P(12.0, -49.0), 0, "via: in front of the Dock hatch"),
    ("ms_v_br", P(4.6, -90.0), (0.0, 13.6), 0, "via: the middle of the bridge"),
]
ROUTES = {
    "ahead": ["ms_v_a1", "ms_v_a2", "ms_v_a3", "ms_v_a4", "ms_v_uw", "ms_uw_hatch"],
    "left": ["ms_v_a1", "ms_v_br", "ms_booth_hatch"],
    "right": ["ms_v_a1", "ms_v_a2", "ms_v_dk", "ms_dock_in"],
    "stay": ["ms_v_a1", "ms_hub_view", "ms_v_a3", "ms_stair_view", "ms_v_a3", "ms_v_a2", "ms_v_a1", "ms_bridge_view", "ms_v_a1", "ms_ref"],
    "arrive": ["ms_arrive", "ms_ref"],
    "stumble": ["ms_ref_back", "ms_sw_corner", "ms_ref"],
}

SKY = "sky"  # the atrium is open to the map's sky (ms_sky: the vault's dark arches over the void's haze); the alcoves keep a ceiling
RIBS = ["ms_wall_rib", "ms_wall_rib_b", "ms_wall_rib_c"]  # the outer wall's bone lattice: three variants, one per ring piece in turn, so no wall repeats its neighbour's
STYLE = {  # sector class -> floor, wall, ceiling texture, tint, step_tex (the riser of a step up onto it: the ring's, bridge's and platform's is the cliff down into the void)
    "ring": ("ms_floor_walk", "ms_wall_rib", SKY, "#cdb8ff", "ms_void_cliff"),
    "void": ("ms_floor_void", "ms_void_cliff", SKY, "#9ad8b0", "ms_void_cliff"),
    "bridge": ("ms_floor_walk", "ms_wall_rib", SKY, "#d8c8ff", "ms_void_cliff"),
    "platform": ("ms_floor_plate", "ms_wall_rib", SKY, "#e0c8ff", "ms_void_cliff"),
    "dk": ("ms_floor_walk", "ms_wall_bone", "ms_ceil", "#ffc890", "ms_wall_dark"),  # (round 2: the alcoves keep the close warm bone lattice: ms_wall_bone)  # (the alcoves are bone too, warm-lit: the painting frames each hatch in ribs)
    "uw_s": ("ms_floor_walk", "ms_wall_bone", "ms_ceil", "#ffb8a8", "ms_wall_dark"),
    "uw": ("ms_floor_walk", "ms_wall_bone", "ms_ceil", "#ffa8a0", "ms_wall_dark"),
}


def style_of(name):
    if name.startswith("ring_"):
        return STYLE["ring"]
    if name.startswith("void_"):
        return STYLE["void"]
    if name.startswith("dk_"):
        return STYLE["dk"]
    if name.startswith("uw_s"):
        return STYLE["uw_s"]
    if name.startswith("uw_"):
        return STYLE["uw"]
    return STYLE[name]


STATES = {"idle": 1, "available": 5, "selected": 2, "committed": 2}
GUIDES = {  # id suffix: point (m), size (height m), lamp point (m)
    "underworld": (GUIDE_AT["underworld"], 2.2, P(11.6, -6.0)),
    "booth": (GUIDE_AT["booth"], 2.2, (-1.0, 15.5)),
    "dock": (GUIDE_AT["dock"], 2.2, P(10.5, -45.0)),
}
BORROWED = ["thing_pendant"]


def ring_pt(j, r, off=0.0):
    return P(r, sc.centre(j) + off)


# billboards: id, sprite, point (m), size (height m); y is the centre (half the size) above the sector's floor unless a fifth value is given (height of the centre above the floor)
THINGS = [
    # (round 2: the platform is 2.25 m in radius: its props drawn in)
    ("ms_dj_rig", "ms_dj_rig", (-1.4, 15.0), 1.5), ("ms_speaker_a", "ms_speaker", (-1.7, 13.9), 1.3), ("ms_pipes", "ms_organ", (-1.0, 15.9), 2.4),
    ("ms_armillary", "ms_armillary", (1.4, 13.1), 1.5), ("ms_booth_arch", "ms_hatch_arch", (0.0, 16.05), 2.8),
    ("ms_orb", "ms_orb", (-3.2, 16.4), 3.8, 7.6),  # (round 2: higher and smaller, off the Booth guide in the pitched view) ("ms_cables_b", "ms_cables_hang", (3.2, 18.0), 3.0, 7.2),  # (round 2: the near cable bundle hid the Booth guide in the pitched view)
    ("ms_crystal_a", "ms_crystal", (1.6, 15.0), 1.6), ("ms_crystal_b", "ms_crystal", (0.9, 12.5), 1.1),
    ("ms_console_a", "ms_console", ring_pt(7, RING + 0.9), 1.0), ("ms_console_b", "ms_console", ring_pt(9, RING + 0.9), 1.0), ("ms_console_c", "ms_console", ring_pt(11, RING + 0.9), 1.0),
    ("ms_console_d", "ms_console", ring_pt(13, RING + 0.9), 1.0), ("ms_console_e", "ms_console", ring_pt(5, RING + 0.9, 8.0), 1.0),
    ("ms_crystal_c", "ms_crystal", ring_pt(6, 8.8, -4.0), 2.0), ("ms_crystal_d", "ms_crystal", ring_pt(8, 8.9, 3.0), 2.4), ("ms_crystal_e", "ms_crystal", ring_pt(10, 8.8, -3.0), 1.8),
    ("ms_crystal_f", "ms_crystal", ring_pt(12, 8.9, 2.0), 2.2), ("ms_crystal_g", "ms_crystal", ring_pt(14, 8.8, -3.0), 1.9), ("ms_crystal_h", "ms_crystal", ring_pt(3, 8.9, 7.0), 1.7),
    ("ms_crystal_i", "ms_crystal", ring_pt(1, 8.9, 2.0), 1.5), ("ms_crystal_j", "ms_crystal", P(13.0, -52.0), 1.4),
    ("ms_dock_case_a", "ms_case", P(13.0, -34.0), 0.9), ("ms_dock_lamp", "ms_lamp_post", P(11.5, -35.0), 1.8),
    ("ms_uw_brazier", "ms_brazier", P(13.1, 8.5), 1.2),
]
# the rim's amber floor lamps (the painting's warm practicals along the railing's foot, against the cool violet and the pool's green): one on the ring's inner edge every 22.5 degrees, each
# with a small warm pool of light; none on the bridge's mouth
RIM_LAMPS = [a for a in [-90.0 + 22.5 * k + 11.25 for k in range(16)]]
for _k, _a in enumerate(RIM_LAMPS):
    THINGS.append(("ms_rimlamp_%d" % _k, "ms_rim_lamp", P(6.35, _a), 0.16))
# pillars rising from the abyss (in the void wedges, so their floor is the pool, 9 m down): id, wedge, radius, angle offset, height
PILLARS = [(2, 5.2, 0.0, 3.2), (4, 4.2, -3.0, 3.1), (6, 5.2, 2.0, 3.2), (8, 4.2, 0.0, 3.1), (10, 5.2, -2.0, 3.2), (12, 4.2, 3.0, 3.1), (14, 5.2, 0.0, 3.2), (15, 4.0, 2.0, 3.1), (1, 4.0, -2.0, 3.1)]  # (round 2: the pool is 3.5 m down: the arch legs reach the rim)
# decals (hung on a solid wall within 0.35 m): id, sprite, point (m), size (height m), bottom y, emissive
DECALS = []  # (the old oval windows are gone: the rib lattice is the wall now)
for _k, (_j, _off) in enumerate(((sc.DOCK_J, -10.0), (sc.DOCK_J, 10.0), (sc.UW_J, -10.0), (sc.UW_J, 10.0), (1, 0.0), (3, 0.0), (5, 0.0), (15, 0.0))):
    DECALS.append(("ms_dc_lamp_%d" % _k, "ms_wall_lamp", P(11.2 if _j in (sc.DOCK_J, sc.UW_J) else 9.16, sc.centre(_j) + _off), 0.5, 1.3, True))
# round 2: the ribs as a few sweeping ARCHES (the painting's bone arches, not a fine mesh): one tall arch decal on the outer wall of every ring piece but the two hatches, two variants
# in turn, 3.7 m apart (the wall between them is the low-contrast rib tile)
for _j in range(sc.N):
    if _j in (sc.DOCK_J, sc.UW_J):
        continue
    DECALS.append(("ms_dc_arch_%d" % _j, "ms_arch_a" if _j % 2 == 0 else "ms_arch_b", P(9.2, sc.centre(_j)), 5.3, 0.0, False))
DECALS += [("ms_dc_hatch_dock", "ms_hatch_dock", P(16.25, -45.0), 2.6, 0.0, True), ("ms_dc_hatch_uw", "ms_hatch_uw", P(13.6, 0.0), 2.8, 0.0, True),
           ("ms_dc_uw_runes", "ms_runes", P(13.55, 7.0), 1.4, 1.2, True)]  # (round 2: the dock's flat shutter is gone: the hatch opens on the lit passage dk_c, its doorway at the far end)
# the void's depth haze (hook work-around: with the void in wedges StoryMap's void_top equals the pool's floor and the engine's void haze is off): a ms_void_haze band on the cliff of every
# wedge, the ring's (radius 5.83, facing the centre) and the platform's (radius 3.0, facing out), from the pool up; emissive (the pool's mist is lit by the pool). id, wedge, radius, faces out
HAZE_SIZE = 3.0  # (round 2: the pool is 3 m down) metres tall: the sprite's 96 x 256 makes it 2.36 m wide, a wedge's chord at the ring's rim
HAZE = []
for _j in range(sc.N):
    if _j == sc.BRIDGE_J:
        continue
    HAZE.append(("ms_dc_haze_r%d" % _j, _j, 5.83, False))  # (the rim is a chord: 5.885 m out at the wedge's centre line)
    HAZE.append(("ms_dc_haze_p%d" % _j, _j, sc.RH, True))  # (the platform's face)
# the pool's lamps: low green lights 1 m over the pool in every other wedge (the old ones stood 4 m BELOW the pool floor: a light's y is above its sector's floor), reaching the void only
POOL_LAMPS = [j for j in range(sc.N) if j % 2 == 1]
POOL_R, POOL_Y, POOL_RAD, POOL_COL, POOL_ST = 4.5, 1.5, 8.0, "#50ffa0", 2.5  # (round 2: higher and wider: the cliffs glow to the rim)
LIGHTS = [  # id, point (m), y, radius, colour, strength   (cold lilac and teal pools on the ring, amber at the hatches, green glow from the abyss, warm light on the platform)
    ("ms_lt_ring_a", P(RING, -112.5), 3.2, 8.0, "#9a88ff", 1.5), ("ms_lt_ring_b", P(RING, -67.5), 3.2, 8.0, "#80e0d0", 1.4), ("ms_lt_ring_c", P(RING, -22.5), 3.2, 8.0, "#a090ff", 1.4),
    ("ms_lt_ring_d", P(RING, 22.5), 3.2, 8.0, "#80e0d0", 1.3), ("ms_lt_ring_e", P(RING, 67.5), 3.2, 8.0, "#a090ff", 1.3), ("ms_lt_ring_f", P(RING, 112.5), 3.2, 8.0, "#80e0d0", 1.2),
    ("ms_lt_ring_g", P(RING, 157.5), 3.2, 8.0, "#a090ff", 1.2), ("ms_lt_ring_h", P(RING, 202.5), 3.2, 8.0, "#80e0d0", 1.3),
] + [("ms_lt_rim_%d" % k, P(6.5, a), 0.3, 2.4, "#ffb050", 1.0) for k, a in enumerate(RIM_LAMPS)] + [
    ("ms_lt_dock", P(11.0, -45.0), 2.4, 5.0, "#ffb060", 1.8), ("ms_lt_dock_in", P(13.0, -45.0), 2.4, 4.0, "#ff9840", 1.4),
    ("ms_lt_dock_far", P(15.6, -45.0), 2.0, 4.5, "#ffb060", 2.0), ("ms_lt_dock_mid", P(12.4, -45.0), 2.6, 5.0, "#ffc070", 1.6), ("ms_lt_dock_floor_a", P(14.6, -49.0), 0.2, 2.5, "#ffc070", 1.2), ("ms_lt_dock_floor_b", P(14.6, -41.0), 0.2, 2.5, "#ffc070", 1.2), ("ms_lt_uw", P(11.6, 0.0), 3.0, 5.5, "#ff6a50", 1.6), ("ms_lt_uw_in", P(13.4, 0.0), 2.6, 4.0, "#ff5a3a", 1.3),
    ("ms_lt_plat_a", (0.0, 14.5), 3.4, 6.5, "#ffc080", 1.3), ("ms_lt_plat_b", (-1.0, 15.6), 2.0, 4.5, "#ffa050", 1.3),
    # the rim's green: the pool's glow rising, a lamp under the rim's lip every quarter (inside the void wedges, 7.5 m over the pool: it lights the cliff tops and the railing from below)
    ("ms_lt_void_a", P(5.4, -60.0), 7.5, 5.0, "#40ff90", 1.0), ("ms_lt_void_b", P(5.4, 30.0), 7.5, 5.0, "#40ffa0", 1.0), ("ms_lt_void_c", P(5.4, 120.0), 7.5, 5.0, "#50ff90", 1.0),
    ("ms_lt_void_d", P(5.4, 210.0), 7.5, 5.0, "#40ff90", 1.0),
]
CROWD_FROM, CROWD_TO = 30.0, 205.0  # degrees: the crowd dances on the ring's north and west, off the routes and the guides' sight lines


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
    """Every railing pair of the scene (the void's rim, the platform's edge, the bridge's sides) becomes a `railing` wall, shut to walkers; every other drop (more than MAX_STEP) is shut too
    while every sector stays reachable from the start (the map loader demands that): the one void wedge kept open is the loader's price, the rail check never lets a move cross a void."""
    sec = {s["id"]: s for s in d["sectors"]}
    walls = [w for w in d["walls"] if w.get("portal")]
    start = next(w for w in d["waypoints"] if w["id"] == d["start"])["sector"]
    pairs = {frozenset(p) for p in sc.rails(names)}

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

    n_rail = 0
    for w in walls:
        a, b = sec[w["sector"]], sec[w["portal"]]
        key = frozenset((names[int(a["doom_sector"])], names[int(b["doom_sector"])]))
        if key in pairs:
            w["kind"], w["tex"], w["height"] = "railing", "ms_rail", RAIL_HEIGHT
            w["blocked"] = True
            n_rail += 1
    for w in walls:
        a, b = sec[w["sector"]], sec[w["portal"]]
        if abs(float(a["floor"]) - float(b["floor"])) > MAX_STEP + 1e-6 and not w.get("blocked"):
            w["blocked"] = True
            if not all_reachable():
                del w["blocked"]
                print("  a drop of %.2f m between %s and %s stays open (it keeps the map connected; a void, never walked)" % (abs(float(a["floor"]) - float(b["floor"])), names[int(a["doom_sector"])], names[int(b["doom_sector"])]))
    print("  %d railing pieces" % n_rail)


def main():
    d = json.load(open(MAP, encoding="utf-8"))
    names = json.load(open(TRACE, encoding="utf-8"))["sector_names"]
    d["art"] = "doom_mothership"
    used = {}
    for s in d["sectors"]:
        nm = names[int(s["doom_sector"])]
        f, w, c, tint, step = style_of(nm)
        if nm.startswith("ring_"):
            w = RIBS[int(nm.split("_")[1]) % len(RIBS)]
        s["floor_tex"], s["wall_tex"], s["ceil_tex"], s["tint"], s["step_tex"] = f, w, c, lift(tint), step
        s["lip_tex"] = "ms_trim"
        if nm.startswith("void_") and nm != "void_%d" % sc.OPEN_WEDGE:
            s["void"] = True  # marked: the depth rule cannot see it (its neighbours include the other wedges, as deep)
        # round 2: the open wedge (west, behind every guide view) is the POOL SHORE: at the pool's level and NOT a void. StoryMap gives the void's connected group the lowest floor
        # round it as void_top (docs/story/HEIGHTS_AND_PATHS.md, split voids); with the shore at the pool's depth that is the pool itself, so the engine's depth haze (a multiplier toward
        # 30 % of the violet fog) does not turn the green pool dark: the pool glows, lit by its lamps, as the painting's main light. Nobody can reach it (its edge to the ring is the drop
        # the loader needs, never walked; the rail check refuses a drop)
        s["room"] = "main"
        s["light"] = round(min(1.0, max(LIGHT_FLOOR if not nm.startswith("void_") else 0.35, float(s["light"]) * LIGHT_GAIN)), 3)
        for k in ("floor_tex", "wall_tex", "ceil_tex", "step_tex", "lip_tex"):
            if s[k] != SKY:
                used[s[k]] = True
    for w in d["walls"]:
        for k in ("lower_tex", "upper_tex"):
            w[k] = ""  # round 2: the sectors' step_tex / lip_tex decide (convert.py's placeholder `trim`, Night One's brass truss, was drawn on every cliff into the void)
    used["ms_rail"] = True
    tex = {}
    for k in sorted(used):
        tex[k] = OWN + k + ".png"
    for k in BORROWED:
        tex[k] = NIGHT + k + ".png"
    for _id, spr, *_r in THINGS:
        tex.setdefault(spr, OWN + spr + ".png")
    for _id, spr, *_r in DECALS:
        tex[spr] = OWN + spr + ".png"
    tex["ms_pillar"] = OWN + "ms_pillar.png"
    tex["ms_void_haze"] = OWN + "ms_void_haze.png"
    tex["ms_sky"] = OWN + "ms_sky.png"
    for who in GUIDES:
        for st, n in STATES.items():
            for i in range(n):
                tex["guide_%s_%s_%d" % (who, st, i)] = OWN + "guide_%s_%s_%d.png" % (who, st, i)
    d["textures"] = tex
    d["max_step"] = MAX_STEP
    d["visibility"] = {"mode": "clip", "depth": 48, "far": 0}
    # waypoints
    keep = [w for w in d["waypoints"] if not w["id"].startswith("ms_")]
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
    d["start"] = "ms_arrive"
    barriers(d, names)
    d["sky"] = {"tex": OWN + "ms_sky.png", "mode": "cylinder", "horizon": 0.76}
    d["fog"] = {"color": "#1a1030", "density": 0.018}
    d["palette_weight"] = 1.0
    # things
    things = [t for t in d["things"] if not str(t["id"]).startswith("ms_")]
    for who, (at, size, lamp) in GUIDES.items():
        x, z = M(*at)
        things.append({"id": "ms_guide_" + who, "kind": "billboard", "sprite": "guide_%s_idle_0" % who, "at": [x, z], "y": round(size * 0.5, 3), "size": size, "anim": "none"})
    for row in THINGS:
        tid, spr, at, size = row[:4]
        x, z = M(*at)
        things.append({"id": tid, "kind": "billboard", "sprite": spr, "at": [x, z], "y": row[4] if len(row) > 4 else round(size * 0.5, 3), "size": size, "anim": "none"})
    for k, (j, r, off, h) in enumerate(PILLARS):
        x, z = M(*P(r, sc.centre(j) + off))
        things.append({"id": "ms_pillar_%d" % k, "kind": "billboard", "sprite": "ms_pillar", "at": [x, z], "y": round(h * 0.5, 3), "size": h, "anim": "none"})
    for tid, spr, at, size, y, emissive in DECALS:
        x, z = M(*at)
        t = {"id": tid, "kind": "decal", "sprite": spr, "at": [x, z], "y": y, "size": size}
        if emissive:
            t["emissive"] = True
        things.append(t)
    for hid, j, r, out in HAZE:
        at = P(r, sc.centre(j))
        yaw = face(at, (2 * at[0] - sc.CX, 2 * at[1] - sc.CY)) if out else face(at, (sc.CX, sc.CY))
        x, z = M(*at)
        things.append({"id": hid, "kind": "decal", "sprite": "ms_void_haze", "at": [x, z], "y": 0.0, "size": HAZE_SIZE, "emissive": True, "yaw": yaw})
    void_ids = [s["id"] for s in d["sectors"] if names[int(s["doom_sector"])].startswith("void_")]
    for j in POOL_LAMPS:
        x, z = M(*P(POOL_R, sc.centre(j)))
        things.append({"id": "ms_lt_pool_%d" % j, "kind": "light", "at": [x, z], "y": POOL_Y, "radius": POOL_RAD, "color": POOL_COL, "strength": POOL_ST, "sectors": void_ids})
    for lid, at, y, rad, col, st in LIGHTS:
        x, z = M(*at)
        things.append({"id": lid, "kind": "light", "at": [x, z], "y": y, "radius": round(rad * 1.3, 1), "color": col, "strength": round(min(2.5, st * LAMP_GAIN), 2)})
    for who, (at, size, lamp) in GUIDES.items():  # the lamp over each guide (the choice layer brightens it)
        x, z = M(*lamp)
        things.append({"id": "ms_lamp_" + who, "kind": "light", "at": [x, z], "y": 2.6, "radius": 3.0, "color": "#ffd9a0", "strength": 0.6})
    d["things"] = things
    spots = {k: v for k, v in d.get("spots", {}).items() if not k.startswith("ms_")}
    for who, (at, size, lamp) in GUIDES.items():
        x, z = M(*at)
        spots["ms_guide_" + who] = {"sector": sector_of(d, x, z)["id"], "at": [x, z]}
    d["spots"] = spots
    # the crowd: the night_one chapter's cast dances on the ring's north and west; content/run/doom/story_doom_mothership.json is the world's StoryData
    ch = json.load(open(os.path.join(ROOT, "content", "story", "night_one.json"), encoding="utf-8"))
    ch["id"], ch["title"] = "doom_mothership", "Doom Mothership"
    ch["art"] = "night_one"
    for b in ch["blocks"]:
        b["events"] = [e for e in b.get("events", []) if not str(e.get("action", "")).startswith("player_") and str(e.get("action", "")) != "doors_open"]
    for dec in ch["decisions"]:
        for k in ("good", "bad"):
            dec[k] = [e for e in dec.get(k, []) if not (isinstance(e, dict) and str(e.get("action", "")).startswith("player_"))]
    for e in ch["endings"].values():
        e["journey"] = []
    ch["actors"], ch["silhouettes"] = [], []  # the painting's atrium has no crowd: the three guides are the people (as the Underworld)
    ch["groups"] = {k: [] for k in ch["groups"]}
    open(os.path.join(ROOT, "content", "run", "doom", "story_doom_mothership.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(ch, indent=1) + "\n")
    pts = []
    for j in range(sc.N):
        for rr in (6.9, 7.8, 8.6):
            for off in (-7.0, 0.0, 7.0):
                ang = sc.centre(j) + off
                a = ang % 360.0
                if not (CROWD_FROM <= a <= CROWD_TO):
                    continue
                x, y = P(rr, ang)
                s = sector_of(d, x, -y)
                if s is None or not names[int(s["doom_sector"])].startswith("ring_") or dist_to_edges(s["polygon"], x, -y) < 0.4:
                    continue
                if all(math.hypot(x - g[0][0], y - g[0][1]) > 1.6 for g in GUIDES.values()):
                    pts.append((round(x, 2), round(-y, 2), s["id"]))
    pts.sort(key=lambda p: (int(p[0] * 977 + p[1] * 1931) * 2654435761) % 4294967296)
    d["homes"] = [{"actor": a["id"], "sector": pts[i][2], "at": [pts[i][0], pts[i][1]]} for i, a in enumerate(ch["actors"])]
    d["silhouettes"] = [{"id": s["id"], "at": [pts[len(ch["actors"]) + i][0], pts[len(ch["actors"]) + i][1]]} for i, s in enumerate(ch["silhouettes"])]
    d["scene"] = {"id": "doom_mothership", "reference": PAINTING, "routes": ROUTES,
                  "note": "authored by tools/doom/author_mothership.py; routes are lists of waypoint ids (the polyline); hold_bars on a waypoint is the still hold at a choice window"}
    d["doom"]["authored"] = True
    json.dump(d, open(MAP, "w", encoding="utf-8", newline="\n"), indent=1)
    open(MAP, "a", encoding="utf-8", newline="\n").write("\n")
    print("authored %d waypoints, %d things (%d decals), %d spots, %d crowd places into %s" % (len(WAYPOINTS), len(things), len(DECALS), len(spots), len(pts), MAP))


if __name__ == "__main__":
    sys.exit(main())
