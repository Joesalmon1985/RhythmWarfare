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


def m(x, y):
    return (round(x / 32.0, 4), round(-y / 32.0, 4))


def face(a, b):
    """The yaw of a view from doom point a towards doom point b (0 faces -z, 90 faces -x)."""
    dx, dy = (b[0] - a[0]) / 32.0, (b[1] - a[1]) / 32.0
    return round(math.degrees(math.atan2(-dx, dy)), 1)


# id, doom point, look-at doom point (or a yaw), hold_bars (0 = a moving place), what it is
WAYPOINTS = [
    ("wh_arrive", (-700, 640), (-690, 440), 0, "arrival: the ring's north-west corner (the nub off the terrace is not connected)"),
    ("wh_door", (-690, 440), (-650, -600), 0, "arrival: down the west band"),
    ("wh_ref", (-650, -600), (500, 500), 8, "THE reference viewpoint: the ring's south-west corner looking across the fenced floor, the stage ahead (NE), bar left, lounge right"),
    ("wh_ref_back", (-715, -690), (500, 500), 0, "recovery: a stumble back into the corner"),
    ("wh_sw_corner", (-710, -520), (500, 500), 0, "recovery: along the west band"),
    ("wh_fence", (60, -640), (400, -500), 4, "reveal: along the south fence, the platforms across the floor"),
    ("wh_plinths", (-640, 100), (0, 0), 4, "reveal: the west band, the platforms across the fence"),
    ("wh_platform", (66, 22), (660, 700), 4, "reveal: up on the central pedestal (the lit cube), the stage across the floor"),
    ("wh_stage_approach", (640, 300), (660, 715), 2, "approach to the stage, the east band"),
    ("wh_stage_steps", (660, 535), (660, 715), 0, "approach: the foot of the stage steps"),
    ("wh_stage_top", (660, 625), (660, 715), 0, "THRESHOLD ahead: on the stage, the world transition happens here"),
    ("wh_bar_approach", (-655, -490), (-655, -300), 2, "approach to the bar"),
    ("wh_bar_door", (-655, -420), (-655, -300), 0, "THRESHOLD left: the bar's canopy edge"),
    ("wh_lounge_approach", (-705, -610), (-470, -600), 2, "approach to the lounge"),
    ("wh_lounge_door", (-578, -600), (-470, -600), 0, "THRESHOLD right: the lounge's canopy edge"),
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
    "stone_ring": ("floor_dark", "wall_panel", "ceil_truss", "#8fa8ff"),
    "courtyard": ("floor_led", "wall_led", "ceil_truss", "#5f7fff"),
    "terrace": ("floor_boards", "wall_brick", "ceil_truss", "#7f90d8"),
    "nub": ("floor_dark", "wall_corridor", "ceil_low", "#8aa0e0"),
    "pedestal": ("floor_stage", "wall_led", "ceil_truss", "#ff7a9a"),
    "ped_step_a": ("floor_stage", "trim", "ceil_truss", "#ff9ab0"),
    "ped_step_b": ("floor_stage", "trim", "ceil_truss", "#ff9ab0"),
    "stage_step_a": ("floor_stage", "trim", "ceil_truss", "#b0b8ff"),
    "stage_step_b": ("floor_stage", "trim", "ceil_truss", "#b0b8ff"),
    "stage": ("floor_stage", "wall_panel", "ceil_truss", "#b8c4ff"),
    "bar": ("floor_boards", "wall_bar", "ceil_low", "#ffb070"),
    "lounge": ("floor_carpet", "wall_chill", "ceil_low", "#ffc080"),
}
for k in ("plat_n", "plat_e", "plat_w", "plat_s"):
    STYLE[k] = ("floor_dark", "wall_speaker", "ceil_truss", "#8fa8ff")
for k in ("pit_n1", "pit_n2", "pit_s1", "pit_s2"):
    STYLE[k] = ("floor_dark", "wall_panel", "ceil_truss", "#3a4a9a")
BORROWED = ["floor_dark", "floor_led", "floor_stage", "floor_boards", "floor_carpet", "wall_panel", "wall_led", "wall_bar", "wall_chill", "wall_corridor", "wall_speaker", "wall_brick",
            "ceil_truss", "ceil_low", "trim", "thing_pendant", "thing_truss_tower", "thing_sofa", "thing_rail"]
STATES = {"idle": 1, "available": 5, "selected": 2, "committed": 2}
GUIDES = {  # id suffix: doom point, size (height m), lamp point
    "stage": ((660, 715), 2.2, (660, 738)),
    "bar": ((-655, -300), 2.2, (-655, -250)),
    "lounge": ((-470, -600), 2.2, (-440, -600)),
}
THINGS = [  # extra dressing: id, sprite, doom point, y, size
    ("wh_pendant_a", "thing_pendant", (-300, -300), 3.2, 1.0), ("wh_pendant_b", "thing_pendant", (300, -300), 3.2, 1.0),
    ("wh_pendant_c", "thing_pendant", (-300, 300), 3.2, 1.0), ("wh_pendant_d", "thing_pendant", (300, 300), 3.2, 1.0),
    ("wh_truss_a", "thing_truss_tower", (-720, 720), 2.5, 5.0), ("wh_truss_b", "thing_truss_tower", (720, -720), 2.5, 5.0),
    ("wh_truss_c", "thing_truss_tower", (730, 540), 2.5, 5.0), ("wh_sofa", "thing_sofa", (-440, -690), 0.75, 1.5),
]
LIGHTS = [  # id, doom point, y, radius, colour, strength
    ("wh_lt_floor", (0, 0), 6.0, 14.0, "#3a62ff", 1.3), ("wh_lt_cube", (66, 22), 3.2, 4.5, "#ff4b6e", 1.1),
    ("wh_lt_spot_l", (-300, -150), 6.0, 9.0, "#4f7bff", 1.0), ("wh_lt_spot_r", (300, 150), 6.0, 9.0, "#4f7bff", 1.0),
    ("wh_lt_stage", (660, 700), 3.6, 7.0, "#9fc4ff", 1.1), ("wh_lt_bar", (-655, -300), 2.7, 5.5, "#ffb060", 1.2), ("wh_lt_lounge", (-470, -600), 2.7, 5.5, "#ffcf80", 1.2),
    ("wh_lt_ref", (-600, -550), 3.0, 8.0, "#6f90ff", 0.9),
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
    # the crowd: the night_one chapter's cast (copied to content/run/doom/story_doom_warehouse.json, the world's StoryData) dances on the fenced floor
    ch = json.load(open(os.path.join(ROOT, "content", "story", "night_one.json"), encoding="utf-8"))
    ch["id"], ch["title"] = "doom_warehouse", "Doom Warehouse (pilot)"
    ch["art"] = "night_one"
    for b in ch["blocks"]:  # the legacy night's camera moves belong to its own map: the Doom scene's camera is the run's rail (crowd and light events stay)
        b["events"] = [e for e in b.get("events", []) if not str(e.get("action", "")).startswith("player_")]
    for dec in ch["decisions"]:
        for k in ("good", "bad"):
            dec[k] = [e for e in dec.get(k, []) if not (isinstance(e, dict) and str(e.get("action", "")).startswith("player_"))]
    for e in ch["endings"].values():
        e["journey"] = []
    open(os.path.join(ROOT, "content", "run", "doom", "story_doom_warehouse.json"), "w", encoding="utf-8", newline="\n").write(json.dumps(ch, indent=1) + "\n")
    floor_secs = [s for s in d["sectors"] if abs(s["floor"] - 0.5) < 0.01 and s["doom_sector"] == names.index("courtyard")]
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
