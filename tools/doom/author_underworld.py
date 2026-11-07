"""Authors the Underworld scene into content/story/maps/doom_underworld.json (docs/doom/scenes/underworld.md), the Booth's pipeline (tools/doom/author_booth.py) for MAP29.

    python -I tools/doom/trace/underworld_scene.py; python -I tools/doom/convert.py --scene underworld --trace tools/doom/trace/underworld_pilot.json     # the geometry (this script's input)
    python -I tools/doom/art/make_underworld_art.py; python -I tools/doom/art/make_underworld_guides.py                                                    # textures, props, guides
    python -I tools/doom/author_underworld.py                                                     # waypoints, textures, things, decals, lights, spots (idempotent; run after every convert)

Coordinates in this file are METRES (x east, y north, as the trace) and are turned into the map's (x, z = -y) by `M`. A waypoint names the sector that holds it and keeps a 0.5 m margin from
the piece's edge; the script moves nothing but a point too close to a wall, and says so.

The abyss: every sector `abyss_*` is a void (the engine draws it far below, hazed, and never lets a walker or the camera in). Every portal between a walkable piece and the abyss is a RAILING
(a see-through chain strip, shut to walkers) except one: the map loader demands that every sector be reachable through open portals, so the abyss keeps ONE open portal, the one farthest from
the origin (a dead end behind the tower; no route, waypoint or thing goes near it, and the rail check refuses to step into a void).

Routes are lists of waypoint ids (`ROUTES`); tools/run/make_doom_underworld.py cuts them into the rail's polyline moves. `hold_bars` on a waypoint is the number of bars the camera holds still.
"""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
MAP = os.path.join(ROOT, "content", "story", "maps", "doom_underworld.json")
TRACE = os.path.join(ROOT, "tools", "doom", "trace", "underworld_pilot.json")
OWN = "textures/"
MARGIN = 0.5
MAX_STEP = 0.5
RAIL_TEX, RAIL_H = "uw_rail", 0.9
LIGHT_GAIN, LIGHT_FLOOR, TINT_LIFT, LAMP_GAIN = 1.4, 0.6, 0.55, 3.0


def M(x, y):
    return (round(x, 4), round(-y, 4))


def face(a, b):
    """The yaw of a view from the point a (metres, x east, y north) towards b (0 faces north / -z, 90 faces -x)."""
    return round(math.degrees(math.atan2(-(b[0] - a[0]), b[1] - a[1])), 1)


# id, point (m), look-at point (m), hold_bars (0 = a moving place), what it is.  Names starting uw_v_ are via points only: corners of the polyline moves, never stood on.
WAYPOINTS = [
    ("uw_arrive", (0.8, 0.2), (-1.2, 14), 0, "arrival: the plateau's south edge (a cut, then a short walk to the reference viewpoint)"),
    ("uw_ref", (0.0, 1.6), (-1.2, 14), 8, "THE reference viewpoint: the plateau looking north over the abyss, the Floor guide at the cave mouth left, the Mothership guide up the ledge ahead, the Dock guide on the shelf right"),
    ("uw_ref_back", (1.0, 0.1), (0.0, 14), 0, "recovery: a stumble back to the south edge"),
    ("uw_sw_corner", (-3.5, 0.8), (0.0, 14), 0, "recovery: along the south-west rock"),
    ("uw_ledge_view", (-2.4, 4.2), (-2.75, 14), 2, "reveal: the foot of the ledge, up the steps to the Mothership guide and the causeway to the tower"),
    ("uw_cave_view", (-3.8, 4.0), (-11, 7.0), 2, "reveal: the west wall, the cave mouth and the Floor guide, the blue tunnel behind her"),
    ("uw_stair_view", (1.6, 4.2), (9, 11), 2, "reveal: the plateau's east side, the stair up to the shelf, the tent and the Dock guide"),
    ("uw_gate", (-2.75, 22.0), (-2.0, 33), 1, "THRESHOLD ahead (Mothership): the causeway past the Mothership guide, the tower ahead; the world transition happens here"),
    ("uw_cave_in", (-10.5, 7.0), (-16, 7.0), 1, "THRESHOLD left (Floor): inside the cave, facing the lit tunnel that runs on (the `uw_tunnel` decal on the cave's end); the world transition happens here"),
    ("uw_shelf_end", (11.0, 12.6), (20, 40), 1, "THRESHOLD right (Dock): the far end of the shelf beside the tent, facing north-east over the lava to the lit path up the far cliff (`uw_passage`); the world transition happens here"),
    # via points (corners of the polyline moves)
    ("uw_v_s1", (-0.5, 3.6), (-0.5, 12), 0, "via: the plateau, north of the reference viewpoint"),
    ("uw_v_s2", (-3.0, 4.6), (-3.0, 12), 0, "via: the plateau, west of the ledge foot"),
    ("uw_v_a1", (-0.8, 3.8), (-1.8, 11), 0, "via: ahead, the plateau"),
    ("uw_v_a2", (-2.0, 6.5), (-1.9, 13), 0, "via: ahead, the foot of the ledge"),
    ("uw_v_a3", (-1.9, 12.5), (-1.9, 17), 0, "via: ahead, up the ledge"),
    ("uw_v_a4", (-1.9, 17.0), (-2.75, 22), 0, "via: ahead, past the Mothership guide"),
    ("uw_v_l1", (-3.0, 4.6), (-5.2, 5.0), 0, "via: left, the plateau"),
    ("uw_v_l2", (-5.2, 5.0), (-7.5, 6.0), 0, "via: left, below the Floor guide"),
    ("uw_v_l3", (-7.5, 6.0), (-10.5, 7.0), 0, "via: left, the cave mouth"),
    ("uw_v_r1", (6.6, 2.2), (7.2, 6.5), 0, "via: right, the plateau's east side"),
    ("uw_v_r2", (7.2, 6.5), (6.6, 10), 0, "via: right, up the stair"),
    ("uw_v_r3", (6.6, 9.8), (7.5, 14.2), 0, "via: right, the shelf"),
    ("uw_v_r4", (7.5, 14.2), (11.0, 12.6), 0, "via: right, behind the Dock guide"),
]
ROUTES = {
    "ahead": ["uw_v_a1", "uw_v_a2", "uw_v_a3", "uw_v_a4", "uw_gate"],
    "left": ["uw_v_l1", "uw_v_l2", "uw_v_l3", "uw_cave_in"],
    "right": ["uw_v_r1", "uw_v_r2", "uw_v_r3", "uw_v_r4", "uw_shelf_end"],
    "stay": ["uw_v_s1", "uw_ledge_view", "uw_v_s2", "uw_cave_view", "uw_v_s1", "uw_stair_view", "uw_v_s1", "uw_ref"],
    "arrive": ["uw_arrive", "uw_ref"],
    "stumble": ["uw_ref_back", "uw_sw_corner", "uw_ref"],
}
SKY = "sky"  # the open ceiling: the map's red cloud sky at infinity (only the cave keeps a rock roof)
STYLE = {  # floor, wall, ceiling, tint, step_tex (the face under a higher floor next to it), lip_tex, (unused)
    "plateau": ("uw_floor_slab", "uw_wall_rock", SKY, "#e8b8a8", "uw_wall_cliff", "uw_wall_rock", 0.85),
    "cave": ("uw_floor_cave", "uw_wall_cave", "uw_ceil", "#8090e8", "uw_wall_cave", "uw_wall_rock", 0.8),
    "dstair": ("uw_floor_stone", "uw_wall_rock", SKY, "#e8b8a8", "uw_wall_step", "uw_wall_rock", 0.88),
    "shelf": ("uw_floor_stone", "uw_wall_rock", SKY, "#f0c0a8", "uw_wall_cliff", "uw_wall_rock", 0.9),
    "ledge": ("uw_floor_stone", "uw_wall_rock", SKY, "#e8b8a8", "uw_wall_step", "uw_wall_rock", 0.88),
    "gate": ("uw_floor_stone", "uw_wall_rock", SKY, "#f0c0a8", "uw_wall_cliff", "uw_wall_rock", 0.9),
    "causeway": ("uw_floor_stone", "uw_wall_rock", SKY, "#e8b8a8", "uw_wall_cliff", "uw_wall_rock", 0.88),
    "tstair": ("uw_floor_stone", "uw_wall_rock", SKY, "#e8b8a8", "uw_wall_step", "uw_wall_rock", 0.88),
    "tower": ("uw_floor_tower", "uw_wall_tower", SKY, "#f0c0a8", "uw_wall_cliff", "uw_wall_tower", 0.9),
    "ttop": ("uw_floor_tower", "uw_wall_tower", SKY, "#f0c0a8", "uw_wall_step", "uw_wall_tower", 0.95),
    # the abyss: the lava floor reads as an emissive surface (white tint, the lava lamps 0.6 m above it saturate it) and its cliffs glow from the bottom up, ABYSS_AMBIENT at their tops
    "abyss": ("uw_floor_lava", "uw_wall_far", SKY, "#ffffff", "uw_wall_abyss", "uw_wall_far", 1.0),
}
ABYSS_AMBIENT = 0.55
LAVA_GRID, LAVA_Y, LAVA_R, LAVA_COL, LAVA_ST = 6.0, 0.6, 9.0, "#ff6418", 2.4  # the lava lamps: a grid every 6 m over the abyss, 0.6 m above the lava, each reaching every abyss piece
SKY_TEX = {"tex": "textures/uw_sky.png", "mode": "cylinder", "horizon": 0.76}
STATES = {"idle": 1, "available": 5, "selected": 2, "committed": 2}
GUIDES = {  # id suffix: point (m), size (height m), lamp point (m)
    "mothership": ((-3.7, 16.2), 2.6, (-3.7, 15.0)),
    "floor": ((-5.4, 7.2), 2.2, (-5.4, 6.4)),
    "dock": ((8.5, 10.6), 2.3, (9.4, 10.6)),
}
# billboards: id, sprite, point (m), size (height m); y is the centre (half the size) unless a fifth value is given (height of the centre above the floor)
# the painting's left foreground (gong, drums) stands inside the reference view's left edge, below the Floor guide's feet; the cloth and the far drum stay by the west wall (the walk's foreground)
THINGS = [
    ("uw_gong", "uw_gong", (-3.4, 3.6), 1.6), ("uw_drum_a", "uw_drum", (-2.0, 3.2), 0.8), ("uw_drum_b", "uw_drum", (-2.7, 4.1), 0.6), ("uw_cloth", "uw_cloth", (-5.7, -1.0), 1.0),
    ("uw_drum_c", "uw_drum", (-5.3, 0.8), 0.9),
    ("uw_stub_a", "uw_stub", (6.6, 0.6), 1.3), ("uw_stub_b", "uw_stub", (3.4, -1.0), 0.9), ("uw_stub_c", "uw_stub", (-1.6, -1.3), 0.8), ("uw_stub_d", "uw_stub", (4.2, 2.6), 1.1),
    ("uw_tusks", "uw_tusks", (-3.0, 17.0), 2.8),
    ("uw_tent", "uw_tent", (11.8, 10.6), 3.0), ("uw_lantern", "uw_lantern", (10.4, 14.6), 0.9, 2.2), ("uw_crate_a", "uw_crate", (10.4, 9.8), 0.95), ("uw_crate_b", "uw_crate", (10.9, 15.2), 0.75),
    ("uw_pillar_a", "uw_pillar", (-4.0, 39.0), 11.0), ("uw_pillar_b", "uw_pillar", (6.0, 39.0), 12.0), ("uw_pillar_c", "uw_pillar", (0.0, 39.2), 10.0), ("uw_pillar_d", "uw_pillar", (-1.0, 34.9), 6.0),
    ("uw_pillar_e", "uw_pillar", (7.6, 33.0), 7.0),
    # lantern posts: the warm practicals of the paths (each with its lamp in LIGHTS)
    ("uw_post_a", "uw_lantern", (-4.1, 5.0), 0.9, 1.9), ("uw_post_b", "uw_lantern", (4.5, 4.9), 0.9, 1.9), ("uw_post_c", "uw_lantern", (-1.5, 12.2), 0.9, 1.9),
    ("uw_post_d", "uw_lantern", (-1.5, 20.0), 0.9, 1.9),
]
# decals: id, sprite, point (m), size (height m), bottom y above the sector's floor, emissive, yaw (None: the wall's own facing; a decal on a cliff face or a lip gives its yaw)
DECALS = [
    ("uw_dc_bones_a", "uw_bones", (-6.45, 6.2), 1.7, 2.9, False, -90.0), ("uw_dc_bones_b", "uw_bones", (-5.5, 9.45), 1.8, 2.3, False, 180.0),
    ("uw_dc_bones_c", "uw_bones", (-6.5, 1.0), 2.4, 0.9, False, None),
    ("uw_dc_fall_a", "uw_lavafall", (3.0, 49.95), 15.0, 0.0, True, None), ("uw_dc_fall_b", "uw_lavafall", (15.0, 49.95), 16.0, 0.0, True, None),
    ("uw_dc_fall_c", "uw_lavafall", (29.95, 30.0), 14.0, 0.0, True, None), ("uw_dc_fall_d", "uw_lavafall", (24.0, 49.95), 13.0, 0.0, True, None),
    ("uw_dc_tunnel", "uw_tunnel", (-15.95, 7.0), 3.4, 0.0, True, None), ("uw_dc_passage", "uw_passage", (21.0, 49.95), 12.0, 3.0, True, None),
]
LIGHTS = [  # id, point (m), y, radius, colour, strength   (lava glow up the plateau's rim, the cave's blue, a lantern on the shelf, red fire on the tower; the lava lamps are LAVA_*)
    ("uw_lt_ref", (0.0, 3.0), 0.4, 8.0, "#ff7a3a", 1.0), ("uw_lt_rim", (2.0, 5.0), 0.3, 8.0, "#ff5a20", 1.2), ("uw_lt_rim2", (-2.5, 5.0), 0.3, 6.0, "#ff5a20", 0.9),
    ("uw_lt_ledge", (-2.8, 13.5), 3.0, 12.0, "#ff6a30", 1.4),
    ("uw_lt_causeway", (-2.8, 23.5), 3.0, 12.0, "#ff5a20", 1.4), ("uw_lt_cave", (-11.0, 7.0), 2.0, 8.0, "#5070ff", 2.2), ("uw_lt_cave2", (-7.5, 7.0), 2.0, 5.0, "#7a90ff", 1.6), ("uw_lt_cave3", (-14.5, 7.0), 1.6, 5.0, "#8aa0ff", 1.8),
    ("uw_lt_gong", (-4.4, 3.4), 2.4, 4.5, "#ffb060", 1.0),
    ("uw_lt_shelf", (10.4, 14.0), 2.4, 7.0, "#ffb860", 1.7), ("uw_lt_stair", (7.2, 6.0), 2.4, 7.0, "#ff8a40", 1.0), ("uw_lt_tower", (1.0, 33.5), 6.0, 14.0, "#ff6a40", 1.4),
    ("uw_lt_tower2", (-3.0, 37.5), 5.0, 10.0, "#d84a30", 1.2),
    ("uw_lt_post_a", (-4.1, 5.0), 1.9, 6.0, "#ffb060", 1.2), ("uw_lt_post_b", (4.5, 4.9), 1.9, 6.0, "#ffb060", 1.2), ("uw_lt_post_c", (-1.5, 12.2), 1.9, 6.0, "#ffb060", 1.1),
    ("uw_lt_post_d", (-1.5, 20.0), 1.9, 6.0, "#ffb060", 1.1), ("uw_lt_wall_w", (-5.8, 2.0), 2.6, 6.0, "#ff8a50", 0.9),
]


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


def prefix(name):
    for k in STYLE:
        if name.startswith(k):
            return k
    raise SystemExit("no style for sector %s" % name)


def barriers(d, names):
    """Closes what a walker must not cross: every portal whose floors differ by more than MAX_STEP is a drop and is shut to walkers (`blocked`) while every sector stays reachable from the start
    (the map loader demands that: the abyss keeps one open portal, the farthest from the origin); every shut portal onto the abyss is the railing kind (a chain strip, see-through)."""
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

    kept = []
    for w in sorted((w for w in walls if drop_of(w) > MAX_STEP + 1e-6 and not w.get("blocked")), key=mid_dist):
        w["blocked"] = True
        if not all_reachable():
            del w["blocked"]
            kept.append(w)
    for w in kept:
        print("  a drop of %.1f m between %s and %s stays open at (%.1f, %.1f) (it keeps the map connected)" % (drop_of(w), w["sector"], w["portal"], (w["from"][0] + w["to"][0]) / 2, -(w["from"][1] + w["to"][1]) / 2))
    for w in walls:
        a, b = sec[w["sector"]], sec[w["portal"]]
        pa, pb = names[int(a["doom_sector"])].startswith("abyss"), names[int(b["doom_sector"])].startswith("abyss")
        if pa != pb and w.get("blocked"):
            w["kind"], w["tex"], w["height"] = "railing", RAIL_TEX, RAIL_H
            w["blocked"] = True


def main():
    d = json.load(open(MAP, encoding="utf-8"))
    names = json.load(open(TRACE, encoding="utf-8"))["sector_names"]
    d["art"] = "doom_underworld"
    used = {}
    for s in d["sectors"]:
        nm = names[int(s["doom_sector"])]
        st = prefix(nm)
        f, w, c, tint, step, lip, light = STYLE[st]
        s["floor_tex"], s["wall_tex"], s["ceil_tex"], s["tint"], s["step_tex"], s["lip_tex"] = f, w, c, lift(tint), step, lip
        s["room"] = "main"
        s["light"] = 1.0  # (sector light is at its ceiling: the lamps and the tint carry the exposure)
        s["room_name"] = nm
        if st == "abyss":
            s["void"] = True
            s["ambient"] = ABYSS_AMBIENT  # (the cliffs' tops; the lava lamps carry the floor and the cliffs' feet to full)
        for k in ("floor_tex", "wall_tex", "ceil_tex", "step_tex", "lip_tex"):
            if s[k] != SKY:
                used[s[k]] = True
    for w in d["walls"]:
        for k in ("lower_tex", "upper_tex"):
            w[k] = ""  # the sector's step_tex / lip_tex decide
    used[RAIL_TEX] = True
    used["uw_sky"] = True
    tex = {k: OWN + k + ".png" for k in sorted(used)}
    for row in THINGS:
        tex.setdefault(row[1], OWN + row[1] + ".png")
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
    keep = [w for w in d["waypoints"] if not w["id"].startswith("uw_")]
    for wid, at, look, hold, _why in WAYPOINTS:
        x, z = M(*at)
        s = sector_of(d, x, z)
        floor0 = s["floor"] if s else None
        if s is None or dist_to_edges(s["polygon"], x, z) < MARGIN:
            best = None
            for r in range(1, 41):
                for k in range(16):
                    a = 2 * math.pi * k / 16
                    qx, qz = x + math.cos(a) * r * 0.1, z + math.sin(a) * r * 0.1
                    q = sector_of(d, qx, qz)
                    if q is not None and (floor0 is None or abs(q["floor"] - floor0) < 0.01) and dist_to_edges(q["polygon"], qx, qz) >= MARGIN + 0.02:
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
    d["start"] = "uw_arrive"
    barriers(d, names)
    d["sky"] = dict(SKY_TEX)
    d["fog"] = {"color": "#4a120c", "density": 0.011}
    d["palette_weight"] = 1.0
    # things
    things = [t for t in d["things"] if not str(t["id"]).startswith("uw_")]
    for who, (at, size, lamp) in GUIDES.items():
        x, z = M(*at)
        things.append({"id": "uw_guide_" + who, "kind": "billboard", "sprite": "guide_%s_idle_0" % who, "at": [x, z], "y": round(size * 0.5, 3), "size": size, "anim": "none"})
    for row in THINGS:
        tid, spr, at, size = row[:4]
        x, z = M(*at)
        things.append({"id": tid, "kind": "billboard", "sprite": spr, "at": [x, z], "y": row[4] if len(row) > 4 else round(size * 0.5, 3), "size": size, "anim": "none"})
    for tid, spr, at, size, y, emissive, yaw in DECALS:
        x, z = M(*at)
        t = {"id": tid, "kind": "decal", "sprite": spr, "at": [x, z], "y": y, "size": size}
        if emissive:
            t["emissive"] = True
        if yaw is not None:
            t["yaw"] = yaw
        things.append(t)
    abyss = [s for s in d["sectors"] if names[int(s["doom_sector"])].startswith("abyss")]
    ids = [s["id"] for s in abyss]
    n_lava = 0
    gy = 5.5 + LAVA_GRID / 2
    while gy < 50.0:
        gx = -4.5 + LAVA_GRID / 2
        while gx < 30.0:
            x, z = M(gx, gy)
            s = sector_of(d, x, z)
            if s is not None and s["id"] in ids:
                things.append({"id": "uw_lt_lava_%02d" % n_lava, "kind": "light", "at": [x, z], "y": LAVA_Y, "radius": LAVA_R, "color": LAVA_COL, "strength": LAVA_ST, "sectors": ids})
                n_lava += 1
            gx += LAVA_GRID
        gy += LAVA_GRID
    for lid, at, y, rad, col, st in LIGHTS:
        x, z = M(*at)
        things.append({"id": lid, "kind": "light", "at": [x, z], "y": y, "radius": round(rad * 1.3, 1), "color": col, "strength": round(min(2.5, st * LAMP_GAIN), 2)})
    for who, (at, size, lamp) in GUIDES.items():  # the lamp over each guide (the choice layer brightens it)
        x, z = M(*lamp)
        things.append({"id": "uw_lamp_" + who, "kind": "light", "at": [x, z], "y": 2.8, "radius": 3.0, "color": "#ffd9a0", "strength": 0.6})
    d["things"] = things
    spots = {k: v for k, v in d.get("spots", {}).items() if not k.startswith("uw_")}
    for who, (at, size, lamp) in GUIDES.items():
        x, z = M(*at)
        spots["uw_guide_" + who] = {"sector": sector_of(d, x, z)["id"], "at": [x, z]}
    d["spots"] = spots
    d["homes"], d["silhouettes"] = [], []  # the painting's abyss has no crowd: the three guides are the people (the world's story has an empty cast: tools/run/make_doom_underworld.py)
    d["scene"] = {"id": "doom_underworld", "reference": "art/reference/doom_worlds/Three Paths Across the Basalt Abyss-4.png", "routes": ROUTES,
                  "note": "authored by tools/doom/author_underworld.py; routes are lists of waypoint ids (the polyline); hold_bars on a waypoint is the still hold at a choice window"}
    d["doom"]["authored"] = True
    json.dump(d, open(MAP, "w", encoding="utf-8", newline="\n"), indent=1)
    open(MAP, "a", encoding="utf-8", newline="\n").write("\n")
    print("authored %d waypoints, %d things (%d decals), %d spots into %s" % (len(WAYPOINTS), len(things), len(DECALS), len(spots), MAP))


if __name__ == "__main__":
    sys.exit(main())
