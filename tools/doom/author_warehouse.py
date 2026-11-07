"""Authors the Warehouse pilot scene into content/story/maps/doom_warehouse.json (docs/doom/scenes/warehouse.md).

    python -I tools/doom/convert.py --scene warehouse --trace tools/doom/trace/warehouse.json     # the geometry (this script's input)
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
TRACE = os.path.join(ROOT, "tools", "doom", "trace", "warehouse.json")
NIGHT = "res://assets/story/night_one/textures/"
OWN = "textures/"
MARGIN = 0.5


def m(x, y):
    return (round(x / 32.0, 4), round(-y / 32.0, 4))


def face(a, b):
    """The yaw of a view from doom point a towards doom point b (0 faces -z, 90 faces -x)."""
    dx, dy = (b[0] - a[0]) / 32.0, (b[1] - a[1]) / 32.0
    return round(math.degrees(math.atan2(-dx, dy)), 1)


# id, doom point, look-at doom point (or a yaw), hold_bars (0 = a moving place), what it is
WAYPOINTS = [
    ("wh_arrive", (-390, 705), (-390, 540), 0, "arrival: the far end of the north corridor"),
    ("wh_door", (-390, 548), (-390, -300), 0, "arrival: the corridor mouth, the floor below"),
    ("wh_ref", (0, -520), (0, 400), 8, "THE reference viewpoint: the floor's corner, stage ahead, bar left, lounge right"),
    ("wh_ref_back", (0, -572), (0, 400), 0, "recovery: a stumble back along the walkway"),
    ("wh_sw_corner", (-140, -555), (0, 300), 0, "recovery: the south-west corner"),
    ("wh_fence", (330, -60), (500, 250), 4, "reveal: along the fence, the lounge opening beyond"),
    ("wh_plinths", (-330, 150), (-105, 145), 4, "reveal: behind the plinths, the floor across the fence"),
    ("wh_platform", (0, 0), (0, 500), 4, "reveal: up on the central platform, the stage across the floor"),
    ("wh_stage_approach", (0, 335), (0, 520), 2, "approach to the stage"),
    ("wh_stage_steps", (0, 398), (0, 520), 0, "approach: the foot of the stage steps"),
    ("wh_stage_top", (0, 472), (0, 520), 0, "THRESHOLD ahead: on the stage, the world transition happens here"),
    ("wh_bar_approach", (-60, -335), (-300, -335), 2, "approach to the bar"),
    ("wh_bar_door", (-130, -335), (-380, -335), 0, "THRESHOLD left: the bar's opening"),
    ("wh_lounge_approach", (60, -335), (300, -335), 2, "approach to the lounge"),
    ("wh_lounge_door", (130, -335), (380, -335), 0, "THRESHOLD right: the lounge's opening"),
]
ROUTES = {  # the three destination routes and the stay loop as lists of waypoint ids (the last is the threshold / the return)
    "ahead": ["wh_stage_approach", "wh_stage_steps", "wh_stage_top"],
    "left": ["wh_bar_approach", "wh_bar_door"],
    "right": ["wh_lounge_approach", "wh_lounge_door"],
    "stay": ["wh_fence", "wh_plinths", "wh_platform", "wh_ref"],
    "arrive": ["wh_arrive", "wh_door", "wh_ref"],
    "stumble": ["wh_ref_back", "wh_sw_corner", "wh_ref"],
}
# sector (by the trace's name) -> floor, wall, ceiling texture, tint
STYLE = {
    "arena_floor": ("floor_dark", "wall_panel", "ceil_truss", "#8fa8ff"),
    "dance_floor": ("floor_led", "wall_led", "ceil_truss", "#5f7fff"),
    "platform": ("floor_stage", "wall_panel", "ceil_truss", "#9fb4ff"),
    "platform_step_s": ("floor_stage", "trim", "ceil_truss", "#9fb4ff"),
    "platform_step_n": ("floor_stage", "trim", "ceil_truss", "#9fb4ff"),
    "stage_step_a": ("floor_stage", "trim", "ceil_truss", "#b0b8ff"),
    "stage_step_b": ("floor_stage", "trim", "ceil_truss", "#b0b8ff"),
    "stage": ("floor_stage", "wall_panel", "ceil_truss", "#b8c4ff"),
    "bar": ("floor_boards", "wall_bar", "ceil_low", "#ffb070"),
    "lounge": ("floor_carpet", "wall_chill", "ceil_low", "#ffc080"),
    "arrival_corridor": ("floor_dark", "wall_corridor", "ceil_low", "#8aa0e0"),
    "arrival_room": ("floor_dark", "wall_corridor", "ceil_low", "#8aa0e0"),
}
for k in range(4):
    STYLE["plinth%d" % k] = ("floor_dark", "wall_speaker", "ceil_truss", "#8fa8ff")
BORROWED = ["floor_dark", "floor_led", "floor_stage", "floor_boards", "floor_carpet", "wall_panel", "wall_led", "wall_bar", "wall_chill", "wall_corridor", "wall_speaker",
            "ceil_truss", "ceil_low", "trim", "thing_pendant", "thing_truss_tower", "thing_sofa", "thing_rail"]
STATES = {"idle": 1, "available": 5, "selected": 2, "committed": 2}
GUIDES = {  # id suffix: doom point, size (height m), lamp point
    "stage": ((0, 522), 2.2, (0, 540)),
    "bar": ((-205, -335), 2.2, (-300, -335)),
    "lounge": ((205, -335), 2.2, (300, -335)),
}
THINGS = [  # extra dressing: id, sprite, doom point, y, size
    ("wh_pendant_a", "thing_pendant", (-250, -60), 3.2, 1.0), ("wh_pendant_b", "thing_pendant", (250, -60), 3.2, 1.0),
    ("wh_pendant_c", "thing_pendant", (-250, 260), 3.2, 1.0), ("wh_pendant_d", "thing_pendant", (250, 260), 3.2, 1.0),
    ("wh_truss_a", "thing_truss_tower", (-470, -60), 2.5, 5.0), ("wh_truss_b", "thing_truss_tower", (470, -60), 2.5, 5.0),
    ("wh_truss_c", "thing_truss_tower", (470, 470), 2.5, 5.0), ("wh_sofa", "thing_sofa", (330, -300), 0.75, 1.5),
]
LIGHTS = [  # id, doom point, y, radius, colour, strength
    ("wh_lt_floor", (0, 40), 5.0, 9.0, "#3a62ff", 1.3), ("wh_lt_cube", (0, 40), 1.9, 3.2, "#ff4b6e", 1.1),
    ("wh_lt_spot_l", (-200, 150), 5.5, 6.0, "#4f7bff", 1.0), ("wh_lt_spot_r", (200, 150), 5.5, 6.0, "#4f7bff", 1.0),
    ("wh_lt_stage", (0, 520), 3.4, 6.0, "#9fc4ff", 1.1), ("wh_lt_bar", (-300, -335), 2.6, 4.5, "#ffb060", 1.2), ("wh_lt_lounge", (300, -335), 2.6, 4.5, "#ffcf80", 1.2),
    ("wh_lt_ref", (0, -450), 3.0, 8.0, "#6f90ff", 0.9),
]


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
        s["floor_tex"], s["wall_tex"], s["ceil_tex"], s["tint"] = f, w, c, tint
        s["room"] = "main"
    for s in d["sectors"]:
        for k in ("floor_tex", "wall_tex", "ceil_tex"):
            used[s[k]] = True
    for w in d["walls"]:
        for k in ("lower_tex", "upper_tex"):
            if w.get(k):
                used[w[k]] = True
    tex = {}
    for k in sorted(set(used) | set(BORROWED)):
        tex[k] = NIGHT + k + ".png"
    for g, n in STATES.items():
        pass
    for who in GUIDES:
        for st, n in STATES.items():
            for i in range(n):
                tex["guide_%s_%s_%d" % (who, st, i)] = OWN + "guide_%s_%s_%d.png" % (who, st, i)
    d["textures"] = tex
    d["sky"] = {}
    d["fog"] = {"color": "#050a22", "density": 0.018}
    d["palette_weight"] = 1.0
    # waypoints
    keep = [w for w in d["waypoints"] if not w["id"].startswith("wh_")]
    for wid, at, look, hold, _why in WAYPOINTS:
        x, z = m(*at)
        s = sector_of(d, x, z)
        floor0 = s["floor"] if s else None
        if s is None or dist_to_edges(s["polygon"], x, z) < MARGIN:  # too near a piece edge (the decomposition's diagonals count): the nearest free spot on the same floor height
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
    for tid, spr, at, y, size in THINGS:
        x, z = m(*at)
        things.append({"id": tid, "kind": "billboard", "sprite": spr, "at": [x, z], "y": y, "size": size, "anim": "none"})
    for lid, at, y, rad, col, st in LIGHTS:
        x, z = m(*at)
        things.append({"id": lid, "kind": "light", "at": [x, z], "y": y, "radius": rad, "color": col, "strength": st})
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
    d["scene"] = {"id": "doom_warehouse", "reference": "art/reference/doom_worlds/Cobalt Warehouse Dance Floor-1.png", "routes": ROUTES,
                  "note": "authored by tools/doom/author_warehouse.py; routes are lists of waypoint ids (one hop today, the polyline later); hold_bars on a waypoint is the still hold at a choice window"}
    d["doom"]["authored"] = True
    json.dump(d, open(MAP, "w", encoding="utf-8", newline="\n"), indent=1)
    open(MAP, "a", encoding="utf-8", newline="\n").write("\n")
    print("authored %d waypoints, %d things, %d spots into %s" % (len(WAYPOINTS), len(things), len(spots), MAP))


if __name__ == "__main__":
    sys.exit(main())
