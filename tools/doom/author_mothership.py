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
RAIL_HEIGHT = 1.1  # the balustrade round the void, metres above the ring's floor
LIGHT_GAIN, LIGHT_FLOOR, TINT_LIFT, LAMP_GAIN = 1.3, 0.45, 0.08, 2.4
REF_BEARING = 32.0  # the reference viewpoint looks this many degrees north of east
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
REF_AT = P(RING, -112.5)
REF_LOOK = (REF_AT[0] + 10 * math.cos(math.radians(REF_BEARING)), REF_AT[1] + 10 * math.sin(math.radians(REF_BEARING)))


def ahead(at_r, at_ang, deg=14.0):
    """A look point a little further round the ring (the direction of travel, counter-clockwise)."""
    return P(at_r, at_ang + deg)


GUIDE_AT = {"underworld": P(11.6, 6.0), "booth": (0.0, 15.8), "dock": P(10.5, -38.0)}
UW_AT, DK_AT = P(12.9, -3.0), P(12.4, -46.0)

# id, point (m), look-at point (m), hold_bars (0 = a moving place), what it is.  Names starting ms_v_ are via points only: corners of the polyline moves, never stood on.
WAYPOINTS = [
    ("ms_arrive", P(RING, -137.0), REF_LOOK, 0, "arrival: the ring's south west (a cut, then a three bar walk to the reference viewpoint)"),
    ("ms_ref", REF_AT, REF_LOOK, 8, "THE reference viewpoint: on the ring walk looking east-north-east, the void on the left with the platform and the Booth guide across it, the Underworld stair ahead, the Dock hatch on the right"),
    ("ms_ref_back", P(8.6, -122.0), REF_LOOK, 0, "recovery: a stumble back against the outer wall"),
    ("ms_sw_corner", P(RING, -140.0), REF_LOOK, 0, "recovery: along the rim"),
    ("ms_hub_view", P(RING, -72.0), (0.0, 15.5), 2, "reveal: the ring's south, the platform in the void and the Booth guide across the railing"),
    ("ms_stair_view", P(RING, -28.0), P(13.0, 0.0), 2, "reveal: the ring's east, the stair and the hatch up to the Underworld"),
    ("ms_bridge_view", P(4.0, -90.0), P(11.0, -48.0), 2, "reveal: the middle of the bridge, the void on both sides, looking back along the ring to the Dock hatch"),
    ("ms_uw_hatch", UW_AT, P(14.0, 0.0), 1, "THRESHOLD ahead (Underworld): the hatch at the top of the stair, the world transition happens here"),
    ("ms_booth_hatch", (0.0, 13.6), (0.0, 17.0), 1, "THRESHOLD left (Booth): the hatch on the platform, the world transition happens here"),
    ("ms_dock_in", DK_AT, P(13.1, -45.0), 1, "THRESHOLD right (Dock): through the outer wall's hatch onto the dock, the world transition happens here"),
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

STYLE = {  # sector class -> floor, wall, ceiling texture, tint, step_tex (the riser of a step up onto it)
    "ring": ("ms_floor_walk", "ms_wall_rib", "ms_ceil", "#cdb8ff", "ms_wall_dark"),
    "void": ("ms_floor_void", "ms_wall_rib", "ms_ceil", "#9ad8b0", "ms_wall_dark"),
    "bridge": ("ms_floor_walk", "ms_wall_rib", "ms_ceil", "#d8c8ff", "ms_wall_dark"),
    "platform": ("ms_floor_plate", "ms_wall_rib", "ms_ceil", "#e0c8ff", "ms_wall_dark"),
    "dk": ("ms_floor_walk", "ms_wall_dark", "ms_ceil", "#ffc890", "ms_wall_dark"),
    "uw_s": ("ms_floor_walk", "ms_wall_dark", "ms_ceil", "#ffb8a8", "ms_wall_dark"),
    "uw": ("ms_floor_walk", "ms_wall_dark", "ms_ceil", "#ffa8a0", "ms_wall_dark"),
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
    "booth": (GUIDE_AT["booth"], 2.2, (-1.1, 15.8)),
    "dock": (GUIDE_AT["dock"], 2.2, P(10.5, -45.0)),
}
BORROWED = ["thing_pendant", "trim"]


def ring_pt(j, r, off=0.0):
    return P(r, sc.centre(j) + off)


# billboards: id, sprite, point (m), size (height m); y is the centre (half the size) above the sector's floor unless a fifth value is given (height of the centre above the floor)
THINGS = [
    ("ms_dj_rig", "ms_dj_rig", (-1.9, 15.4), 1.5), ("ms_speaker_a", "ms_speaker", (-2.3, 14.2), 1.3), ("ms_pipes", "ms_organ", (-1.3, 16.9), 2.4),
    ("ms_armillary", "ms_armillary", (1.9, 13.0), 1.5), ("ms_booth_arch", "ms_hatch_arch", (0.0, 16.9), 2.8),
    ("ms_orb", "ms_orb", (-2.4, 14.8), 4.8, 6.0), ("ms_cables_a", "ms_cables_hang", (-4.5, 10.8), 3.4, 7.0), ("ms_cables_b", "ms_cables_hang", (3.2, 18.0), 3.0, 7.2),
    ("ms_crystal_a", "ms_crystal", (2.3, 15.1), 1.6), ("ms_crystal_b", "ms_crystal", (1.2, 12.0), 1.1),
    ("ms_console_a", "ms_console", ring_pt(7, RING + 0.9), 1.0), ("ms_console_b", "ms_console", ring_pt(9, RING + 0.9), 1.0), ("ms_console_c", "ms_console", ring_pt(11, RING + 0.9), 1.0),
    ("ms_console_d", "ms_console", ring_pt(13, RING + 0.9), 1.0), ("ms_console_e", "ms_console", ring_pt(5, RING + 0.9, 8.0), 1.0),
    ("ms_crystal_c", "ms_crystal", ring_pt(6, 8.8, -4.0), 2.0), ("ms_crystal_d", "ms_crystal", ring_pt(8, 8.9, 3.0), 2.4), ("ms_crystal_e", "ms_crystal", ring_pt(10, 8.8, -3.0), 1.8),
    ("ms_crystal_f", "ms_crystal", ring_pt(12, 8.9, 2.0), 2.2), ("ms_crystal_g", "ms_crystal", ring_pt(14, 8.8, -3.0), 1.9), ("ms_crystal_h", "ms_crystal", ring_pt(3, 8.9, 7.0), 1.7),
    ("ms_crystal_i", "ms_crystal", ring_pt(1, 8.9, 2.0), 1.5), ("ms_crystal_j", "ms_crystal", P(13.0, -52.0), 1.4),
    ("ms_dock_case_a", "ms_case", P(13.0, -34.0), 0.9), ("ms_dock_lamp", "ms_lamp_post", P(11.5, -35.0), 1.8),
    ("ms_uw_brazier", "ms_brazier", P(13.1, 8.5), 1.2),
]
# pillars rising from the abyss (in the void wedges, so their floor is the pool, 9 m down): id, wedge, radius, angle offset, height
PILLARS = [(2, 5.2, 0.0, 9.0), (4, 4.6, -3.0, 8.6), (6, 5.2, 2.0, 9.0), (8, 4.6, 0.0, 8.8), (10, 5.2, -2.0, 9.0), (12, 4.6, 3.0, 8.6), (14, 5.2, 0.0, 9.0), (15, 4.4, 2.0, 8.8), (1, 4.4, -2.0, 8.8)]
# decals (hung on a solid wall within 0.35 m): id, sprite, point (m), size (height m), bottom y, emissive
DECALS = []
for _j in range(sc.N):
    if _j in (sc.DOCK_J, sc.UW_J):
        continue
    DECALS.append(("ms_dc_oval_%d" % _j, "ms_oval_window", P(9.18, sc.centre(_j)), 2.2, 1.7, True))
for _k, (_j, _off) in enumerate(((sc.DOCK_J, -10.0), (sc.DOCK_J, 10.0), (sc.UW_J, -10.0), (sc.UW_J, 10.0), (1, 0.0), (3, 0.0), (5, 0.0), (15, 0.0))):
    DECALS.append(("ms_dc_lamp_%d" % _k, "ms_wall_lamp", P(11.2 if _j in (sc.DOCK_J, sc.UW_J) else 9.16, sc.centre(_j) + _off), 0.5, 1.3, True))
DECALS += [("ms_dc_hatch_dock", "ms_hatch_dock", P(13.1, -45.0), 2.6, 0.0, True), ("ms_dc_hatch_uw", "ms_hatch_uw", P(13.6, 0.0), 2.8, 0.0, True),
           ("ms_dc_dock_shutter", "ms_shutter_panel", P(13.1, -52.0), 1.6, 0.4, False), ("ms_dc_uw_runes", "ms_runes", P(13.55, 7.0), 1.4, 1.2, True)]
LIGHTS = [  # id, point (m), y, radius, colour, strength   (cold lilac and teal pools on the ring, amber at the hatches, green glow from the abyss, warm light on the platform)
    ("ms_lt_ring_a", P(RING, -112.5), 3.2, 8.0, "#9a88ff", 1.5), ("ms_lt_ring_b", P(RING, -67.5), 3.2, 8.0, "#80e0d0", 1.4), ("ms_lt_ring_c", P(RING, -22.5), 3.2, 8.0, "#a090ff", 1.4),
    ("ms_lt_ring_d", P(RING, 22.5), 3.2, 8.0, "#80e0d0", 1.3), ("ms_lt_ring_e", P(RING, 67.5), 3.2, 8.0, "#a090ff", 1.3), ("ms_lt_ring_f", P(RING, 112.5), 3.2, 8.0, "#80e0d0", 1.2),
    ("ms_lt_ring_g", P(RING, 157.5), 3.2, 8.0, "#a090ff", 1.2), ("ms_lt_ring_h", P(RING, 202.5), 3.2, 8.0, "#80e0d0", 1.3),
    ("ms_lt_dock", P(11.0, -45.0), 2.4, 5.0, "#ffb060", 1.8), ("ms_lt_dock_in", P(13.0, -45.0), 2.4, 4.0, "#ff9840", 1.4), ("ms_lt_uw", P(11.6, 0.0), 3.0, 5.5, "#ff6a50", 1.6), ("ms_lt_uw_in", P(13.4, 0.0), 2.6, 4.0, "#ff5a3a", 1.3),
    ("ms_lt_plat_a", (0.0, 14.5), 3.4, 6.5, "#ffc080", 1.6), ("ms_lt_plat_b", (-1.4, 16.2), 2.0, 4.5, "#ffa050", 1.3),
    ("ms_lt_void_a", P(4.5, -60.0), -4.0, 9.0, "#40ff90", 1.6), ("ms_lt_void_b", P(4.5, 30.0), -4.0, 9.0, "#40ffa0", 1.5), ("ms_lt_void_c", P(4.5, 120.0), -4.0, 9.0, "#50ff90", 1.5),
    ("ms_lt_void_d", P(4.5, 210.0), -4.0, 9.0, "#40ff90", 1.5),
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
        s["floor_tex"], s["wall_tex"], s["ceil_tex"], s["tint"], s["step_tex"] = f, w, c, lift(tint), step
        s["lip_tex"] = "ms_trim"
        if nm.startswith("void_"):
            s["void"] = True  # marked: the depth rule cannot see it (its neighbours include the other wedges, as deep)
        s["room"] = "main"
        s["light"] = round(min(1.0, max(LIGHT_FLOOR if not nm.startswith("void_") else 0.35, float(s["light"]) * LIGHT_GAIN)), 3)
        for k in ("floor_tex", "wall_tex", "ceil_tex", "step_tex", "lip_tex"):
            used[s[k]] = True
    for w in d["walls"]:
        for k in ("lower_tex", "upper_tex"):
            if w.get(k):
                used[w[k]] = True
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
    d["sky"] = {}
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
    need = len(ch["actors"]) + len(ch["silhouettes"])
    if len(pts) < need:
        raise SystemExit("only %d ring spots for %d people" % (len(pts), need))
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
