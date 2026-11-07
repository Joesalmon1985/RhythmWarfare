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
    ("wh_arrive", (-720, -715), (500, 500), 0, "arrival: the ring's south-west corner facing the floor (a cut, then a short walk to the reference viewpoint)"),
    ("wh_ref", (-620, -600), (500, 500), 8, "THE reference viewpoint: the ring's south-west corner looking across the fenced floor, the stage ahead, bar left, lounge right"),
    ("wh_ref_back", (-705, -660), (500, 500), 0, "recovery: a stumble back into the corner"),
    ("wh_sw_corner", (-710, -520), (500, 500), 0, "recovery: along the west band"),
    ("wh_fence", (60, -640), (400, -500), 4, "reveal: along the south railing, the platforms across the floor"),
    ("wh_plinths", (-640, 100), (0, 0), 4, "reveal: the west band, the platforms across the railing"),
    ("wh_platform", (66, 22), (-300, -190), 4, "reveal: up on the central pedestal (the lit cube), the stage across the floor"),
    ("wh_stage_approach", (-360, -470), (-300, -190), 2, "approach to the stage, leg 1: through the south gate onto the floor"),
    ("wh_stage_steps", (-100, -150), (-300, -190), 0, "approach to the stage, leg 2: the foot of the stage steps"),
    ("wh_stage_top", (-215, -150), (-300, -190), 0, "THRESHOLD ahead: on the stage, the world transition happens here"),
    ("wh_bar_approach", (-640, -500), (-600, -300), 2, "approach to the bar"),
    ("wh_bar_door", (-640, -425), (-600, -300), 0, "THRESHOLD left: the bar room's opening"),
    ("wh_lounge_approach", (-650, -585), (-465, -590), 2, "approach to the lounge"),
    ("wh_lounge_door", (-575, -585), (-465, -590), 0, "THRESHOLD right: the lounge room's opening"),
]
ROUTES = {  # the three destination routes and the stay loop as lists of waypoint ids (the last is the threshold / the return)
    "ahead": ["wh_stage_approach", "wh_stage_steps", "wh_stage_top"],
    "left": ["wh_bar_approach", "wh_bar_door"],
    "right": ["wh_lounge_approach", "wh_lounge_door"],
    "stay": ["wh_fence", "wh_plinths", "wh_platform", "wh_ref"],
    "arrive": ["wh_arrive", "wh_ref"],
    "stumble": ["wh_ref_back", "wh_sw_corner", "wh_ref"],
}
# sector (by the trace's name) -> floor, wall, ceiling texture, tint
STYLE = {
    "stone_ring": ("floor_dark", "wall_panel", "ceil_truss", "#b8c8ff"),
    "courtyard": ("floor_led", "trim", "ceil_truss", "#8aa4ff"),
    "terrace": ("floor_boards", "wall_brick", "ceil_truss", "#9fb0e8"),
    "nub": ("floor_dark", "wall_corridor", "ceil_low", "#aab8f0"),
    "pedestal": ("floor_stage", "wall_led", "ceil_truss", "#ff8aa8"),
    "ped_step_a": ("floor_stage", "trim", "ceil_truss", "#ffa8bc"),
    "ped_step_b": ("floor_stage", "trim", "ceil_truss", "#ffa8bc"),
    "stage_step_a": ("floor_stage", "trim", "ceil_truss", "#c8d0ff"),
    "stage_step_b": ("floor_stage", "trim", "ceil_truss", "#c8d0ff"),
    "stage": ("floor_stage", "wall_panel", "ceil_truss", "#d0d8ff"),
    "gate_step_s": ("floor_dark", "trim", "ceil_truss", "#b8c8ff"),
    "gate_step_w": ("floor_dark", "trim", "ceil_truss", "#b8c8ff"),
    "bar": ("floor_boards", "wall_bar", "ceil_low", "#ffc080"),
    "lounge": ("floor_carpet", "wall_chill", "ceil_low", "#ffd090"),
}
for k in ("plat_n", "plat_e", "plat_w", "plat_s"):
    STYLE[k] = ("floor_dark", "wall_speaker", "ceil_truss", "#b8c8ff")
for k in ("pit_n1", "pit_n2", "pit_s1", "pit_s2"):
    STYLE[k] = ("floor_dark", "wall_panel", "ceil_truss", "#6a80d0")
BORROWED = ["floor_dark", "floor_led", "floor_stage", "floor_boards", "floor_carpet", "wall_panel", "wall_led", "wall_bar", "wall_chill", "wall_corridor", "wall_speaker", "wall_brick",
            "ceil_truss", "ceil_low", "trim", "thing_pendant", "thing_truss_tower", "thing_sofa", "thing_rail"]
LIGHT_GAIN, LIGHT_FLOOR, TINT_LIFT, LAMP_GAIN = 2.0, 0.9, 0.75, 2.5  # exposure (docs/doom/scenes/warehouse.md): the Doom lights are low for this renderer; A1's night-interior median is 0.25 to 0.38
STATES = {"idle": 1, "available": 5, "selected": 2, "committed": 2}
GUIDES = {  # id suffix: doom point, size (height m), lamp point
    "stage": ((-300, -190), 2.2, (-330, -190)),
    "bar": ((-600, -300), 2.2, (-600, -250)),
    "lounge": ((-465, -590), 2.2, (-440, -590)),
}
THINGS = [  # extra dressing: id, sprite, doom point, y, size
    ("wh_pendant_a", "thing_pendant", (-300, -300), 3.2, 1.0), ("wh_pendant_b", "thing_pendant", (300, -300), 3.2, 1.0),
    ("wh_pendant_c", "thing_pendant", (-300, 300), 3.2, 1.0), ("wh_pendant_d", "thing_pendant", (300, 300), 3.2, 1.0),
    ("wh_truss_a", "thing_truss_tower", (-720, 720), 2.5, 5.0), ("wh_truss_b", "thing_truss_tower", (720, -720), 2.5, 5.0),
    ("wh_truss_c", "thing_truss_tower", (730, 540), 2.5, 5.0), ("wh_sofa", "thing_sofa", (-440, -690), 0.75, 1.5),
]
LIGHTS = [  # id, doom point, y, radius, colour, strength   (cobalt over the floor and the walkway, amber in the bar and the lounge, a cool pool on the stage)
    ("wh_lt_floor", (0, 0), 6.0, 16.0, "#4a72ff", 1.6), ("wh_lt_cube", (66, 22), 3.2, 5.0, "#ff4b6e", 1.4),
    ("wh_lt_spot_nw", (-300, 300), 6.0, 11.0, "#5f88ff", 1.4), ("wh_lt_spot_ne", (300, 300), 6.0, 11.0, "#5f88ff", 1.4),
    ("wh_lt_spot_se", (300, -300), 6.0, 11.0, "#5f88ff", 1.4), ("wh_lt_spot_sw", (-300, -300), 6.0, 11.0, "#5f88ff", 1.4),
    ("wh_lt_stage", (-300, -190), 4.5, 7.0, "#a8c8ff", 1.5),
    ("wh_lt_bar", (-640, -300), 3.4, 6.5, "#ffa84a", 1.8), ("wh_lt_bar2", (-600, -380), 3.0, 5.0, "#ffb860", 1.4),
    ("wh_lt_lounge", (-465, -640), 3.4, 6.5, "#ffb860", 1.8), ("wh_lt_lounge2", (-480, -590), 3.0, 5.0, "#ffc878", 1.4),
    ("wh_lt_ref", (-620, -540), 3.4, 11.0, "#7a98ff", 1.4), ("wh_lt_ring_w", (-640, 100), 3.4, 11.0, "#6a88ff", 1.2), ("wh_lt_ring_s", (60, -640), 3.4, 11.0, "#6a88ff", 1.2),
    ("wh_lt_ring_e", (640, 100), 3.4, 11.0, "#6a88ff", 1.2), ("wh_lt_ring_n", (0, 640), 3.4, 11.0, "#6a88ff", 1.2),
]


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
        s["floor_tex"], s["wall_tex"], s["ceil_tex"], s["tint"] = f, w, c, lift(tint)
        s["room"] = "main"
        s["light"] = round(min(1.0, max(LIGHT_FLOOR, float(s["light"]) * LIGHT_GAIN)), 3)
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
    d["fog"] = {"color": "#2f48ac", "density": 0.021}
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
