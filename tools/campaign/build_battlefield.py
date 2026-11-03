"""Writes data/maps/field_80x40.json, data/battlefields/defense_01.json (the centred-base defense map of the schema 2
build, kept for its layout tests), data/battlefields/defense_02.json (the mission map: the same compound with no
pre-placed pillboxes, prepared sockets for rewarded buildings and a second and third optional objective) and
data/battlefields/village_01.json (defense_02's walls, openings, points, entries and sockets with the compound turned
into a village: the barracks in the centre, a ring of civilian houses, ten civilians and a wander area).

    python tools/campaign/build_battlefield.py

The map is 80 x 40 cells (24 px each). The player sees a window of it centred on the command core (53 x 20 cells on a
16:9 screen, `view` in the battlefield file); the three entries lie outside that window so wave units are already
walking when they appear. The base is one walled compound with an opening on the left, the right and the top; the
bottom of the screen belongs to the rhythm lane, so nothing comes from below. Tree clumps are the strip map's
decorations (same blocked footprints), placed away from the routes."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W, H = 80, 40
CX = 39.5  # the compound is mirror-symmetric about this x
VIEW_CENTER = [39.5, 20.5]

strip = json.loads((ROOT / "data/maps/strip_53x20.json").read_text())

# blocked footprint per decoration image, relative to the decoration's top-left, from the strip map
patterns = {}
for d in strip["decorations"]:
    cells = [(c[0] - d["x"], c[1] - d["y"]) for c in strip["blocked"] if d["x"] <= c[0] < d["x"] + d["w"] and d["y"] <= c[1] < d["y"] + d["h"]]
    patterns[d["image"]] = {"w": d["w"], "h": d["h"], "cells": cells}

rng = random.Random(8040)
tiles = [[{"t": "clear1", "f": rng.randrange(16)} for _ in range(W)] for _ in range(H)]

# tree clumps: well clear of the compound, the three routes and the entries
spots = [("tc03", 4, 27), ("t02", 18, 30), ("tc05", 24, 33), ("t06", 6, 12), ("tc04", 20, 4), ("t06", 31, 7), ("tc03", 14, 26),
         ("tc03", 70, 27), ("t02", 60, 30), ("tc05", 52, 33), ("t06", 70, 12), ("tc04", 54, 3), ("t06", 44, 7), ("tc03", 62, 26),
         ("tc03", 34, 34), ("t02", 46, 35), ("t06", 4, 3), ("t06", 74, 3), ("tc04", 3, 18), ("tc04", 72, 18)]
decorations, blocked = [], []
for image, x, y in spots:
    p = patterns[image]
    decorations.append({"image": image, "sequence": "idle", "x": x, "y": y, "w": p["w"], "h": p["h"]})
    blocked += [[x + dx, y + dy] for dx, dy in p["cells"]]

game_map = {"width": W, "height": H, "tileset": "temperat", "cell_px": 24, "seed": 8040, "tiles": tiles, "decorations": decorations,
            "blocked": blocked, "notes": "80 x 40 temperate field for the defense campaign. " + strip["notes"]}
(ROOT / "data/maps/field_80x40.json").write_text(json.dumps(game_map, separators=(",", ":")) + "\n")

# --- the compound -------------------------------------------------------------------------------------------------
X0, X1 = 28, 50  # ring columns (23 wide, centre 39.5)
Y0, Y1 = 16, 25  # ring rows (10 tall)
SIDE_OPEN = range(19, 24)  # rows of the left and right openings
TOP_OPEN = range(37, 42)   # columns of the top opening (centre 39.5)
pillboxes = {(X0, 18), (X1, 24), (36, Y0)}  # one at the end of each opening
buildings = [
    {"role": "main", "x": 38, "y": 19, "w": 3, "h": 3},
    {"role": "factory", "x": 33, "y": 17, "w": 3, "h": 3},
    {"role": "barracks", "x": 44, "y": 17, "w": 2, "h": 2},
    {"role": "power", "x": 33, "y": 23, "w": 2, "h": 2},
    {"role": "dome", "x": 45, "y": 23, "w": 2, "h": 2},
]
ring = set()
for x in range(X0, X1 + 1):
    ring |= {(x, Y0), (x, Y1)}
for y in range(Y0, Y1 + 1):
    ring |= {(X0, y), (X1, y)}
ring -= {(X0, y) for y in SIDE_OPEN} | {(X1, y) for y in SIDE_OPEN} | {(x, Y0) for x in TOP_OPEN}
for x, y in sorted(ring, key=lambda c: (c[1], c[0])):
    role = "pillbox" if (x, y) in pillboxes else ("brick" if x in (X0, X1) or y in (Y0, Y1) else "wall")
    buildings.append({"role": role, "x": x, "y": y, "w": 1, "h": 1})
for x, y in pillboxes:
    assert (x, y) in ring, (x, y)

bf = {
    "id": "defense_01",
    "mode": "defense",
    "map": "field_80x40",
    "width": W,
    "height": H,
    "view": {"center": VIEW_CENTER, "max_cells": [53.4, 20.0]},
    "note": ("One-sided defense with the base in the middle of the screen. The map is 80 x 40 cells; the player sees a 53 x 20 cell window "
             "centred on the command core, so the three entries (left x=8, right x=70, top y=0) are 4 to 10 cells outside it and wave units are "
             "already walking when they appear. One walled compound (brick ring, openings of five cells on the left, right and top, no gap at the "
             "bottom where the rhythm lane sits) with one pillbox at the end of each opening and no gun turrets or SAM sites. Each opening has a "
             "defense point 3.5 cells outside its wall. Riflemen (about 1.3 cells/s) need about 12 s from the left or right entry to its defense "
             "point and 10 s from the top, jeeps (about 4 cells/s) 4 s and 3 s (the pack build prints it per wave). Factory and barracks exits and "
             "the rally point lie inside the ring and never block the openings. Later levels add defenses through battlefield variants."),
    "objectives": [{"id": "command_core", "role": "main", "required": True}],
    "defense_points": [
        {"id": "defense_1", "x": 24, "y": 21},
        {"id": "defense_2", "x": 39, "y": 13},
        {"id": "defense_3", "x": 54, "y": 21},
    ],
    "entries": [
        {"id": "left", "x": 8, "y": 21},
        {"id": "top", "x": 39, "y": 0},
        {"id": "right", "x": 70, "y": 21},
    ],
    "leash_cells": 6.0,
    "buildings": buildings,
    "exits": {"factory": [34, 20], "barracks": [44, 19]},
    "rally": [39, 23],
    "air_hold": [39, 23],
    "air_wait": [39, 23],
}
(ROOT / "data/battlefields/defense_01.json").write_text(json.dumps(bf, indent=1) + "\n")
print(f"map {W}x{H}, {len(decorations)} decorations, {len(blocked)} blocked cells; battlefield with {len(buildings)} buildings")

# --- defense_02: the mission battlefield (sockets for rewarded defenses, no pre-placed pillboxes) -------------------
# Sockets flank each route outside the wall, inside the visible window, never on the route itself. Fill order is the
# list order per approach; missions open the first n of each (rules.sockets_per_point).
SOCKETS = {
    0: [(25, 18), (25, 24), (21, 17), (21, 25), (17, 18)],  # left
    1: [(35, 14), (43, 14), (34, 12), (44, 12), (31, 13)],  # top
    2: [(53, 18), (53, 24), (57, 17), (57, 25), (61, 18)],  # right (mirror x' = 78 - x)
}
b2 = [b if b["role"] != "pillbox" else {**b, "role": "brick"} for b in buildings]
taken = {(b["x"] + i, b["y"] + j) for b in b2 for i in range(b["w"]) for j in range(b["h"])} | {tuple(c) for c in blocked}
view_x = (VIEW_CENTER[0] - 26.7, VIEW_CENTER[0] + 26.7)
view_y = (VIEW_CENTER[1] - 10.0, VIEW_CENTER[1] + 10.0)
sockets = []
for point, cells in SOCKETS.items():
    for order, (x, y) in enumerate(cells):
        assert (x, y) not in taken, ("socket on a blocked cell", x, y)
        assert view_x[0] <= x and x + 1 <= view_x[1] and view_y[0] <= y and y + 1 <= view_y[1], ("socket outside the window", x, y)
        assert not (point in (0, 2) and 19 <= y <= 23) and not (point == 1 and 37 <= x <= 41), ("socket on a route", x, y)
        sockets.append({"id": f"s{point + 1}_{order + 1}", "point": point, "order": order, "x": x, "y": y})
bf2 = dict(bf)
bf2["id"] = "defense_02"
bf2["buildings"] = b2
bf2["sockets"] = sockets
bf2["objectives"] = [
    {"id": "command_core", "role": "main", "required": True},
    {"id": "power_plant", "role": "power", "required": False},
    {"id": "radar_dome", "role": "dome", "required": False},
]
bf2["note"] = ("The mission map (schema 3): defense_01's compound and routes with no pre-placed pillboxes. Rewarded buildings go to "
               "prepared sockets, five per approach, flanking each route outside the wall and inside the visible window (missions "
               "open the first sockets_per_point of each). The power plant and the radar dome are objectives a mission may make "
               "required (rules.required_objectives); the command core always is.")
(ROOT / "data/battlefields/defense_02.json").write_text(json.dumps(bf2, indent=1) + "\n")
print(f"defense_02: {len(sockets)} sockets")

# --- village_01: the level 1 map (a village around the infantry barracks) ----------------------------------------------
# Footprints are the OpenRA ones (mods/ra/rules/civilian.yaml, Building.Dimensions; V08 has none and is 1x1).
VILLAGE_FOOTPRINT = {"v01": (2, 2), "v02": (2, 2), "v03": (2, 2), "v04": (2, 2), "v05": (2, 1), "v06": (2, 1), "v07": (2, 1), "v08": (1, 1)}
# (actor, x, y): rows 21 and 22 stay clear from wall to wall, and columns 36..41 stay clear above the barracks, so every
# opening has a lane of at least two cells to the barracks exit.
HOUSES = [
    ("v01", 31, 17), ("v02", 46, 17), ("v03", 31, 23), ("v04", 46, 23),
    ("v05", 34, 19), ("v06", 43, 19), ("v07", 34, 23), ("v08", 43, 23),
    ("v05", 34, 17), ("v06", 44, 17),
]
BARRACKS = (38, 19)
BARRACKS_EXIT = (39, 21)
CIVILIANS = [("tecn", 33, 21), ("tecn", 35, 22), ("tecn", 37, 18), ("tecn", 41, 18), ("tecn", 43, 21), ("tecn", 45, 22),
             ("tecn", 30, 22), ("tecn", 48, 21), ("c1", 38, 23), ("c2", 40, 23)]
WANDER = {"rect": [29, 17, 49, 24], "radius": 5.0, "flee_radius": 6.0}

village_rules = ROOT / "data/openra_rules.json"
if village_rules.exists():  # cross-check the footprints against the extracted rules once the actors are in
    actors = json.loads(village_rules.read_text()).get("actors", {})
    for actor, (fw, fh) in VILLAGE_FOOTPRINT.items():
        if actor in actors:
            dim = actors[actor].get("building", {}).get("dimensions", f"{fw},{fh}")
            assert tuple(int(v) for v in dim.split(",")) == (fw, fh), ("footprint differs from data/openra_rules.json", actor, dim)

walls = [b for b in b2 if b["role"] in ("brick", "wall")]
village = [{"role": "barracks", "x": BARRACKS[0], "y": BARRACKS[1], "w": 2, "h": 2}]
village += [{"role": "village", "actor": a, "x": x, "y": y, "w": VILLAGE_FOOTPRINT[a][0], "h": VILLAGE_FOOTPRINT[a][1]} for a, x, y in HOUSES]
b3 = walls + village

tree_cells = {tuple(c) for c in blocked}
occupied = {}
for b in b3:
    for i in range(b["w"]):
        for j in range(b["h"]):
            cell = (b["x"] + i, b["y"] + j)
            assert cell not in occupied, ("buildings overlap", cell, b, occupied[cell])
            assert cell not in tree_cells, ("building on a tree", cell, b)
            assert 0 <= cell[0] < W and 0 <= cell[1] < H, ("building off the map", cell)
            occupied[cell] = b
for b in village:
    assert all(X0 < b["x"] + i < X1 and Y0 < b["y"] + j < Y1 for i in range(b["w"]) for j in range(b["h"])), ("building outside the compound", b)
for s_ in sockets:
    assert (s_["x"], s_["y"]) not in occupied and (s_["x"], s_["y"]) not in tree_cells, ("socket on a blocked cell", s_)


def free(c):
    return c not in occupied and c not in tree_cells and 0 <= c[0] < W and 0 <= c[1] < H


for a, x, y in CIVILIANS:
    assert free((x, y)) and X0 < x < X1 and Y0 < y < Y1, ("civilian on a blocked cell", a, x, y)
assert len({(x, y) for _, x, y in CIVILIANS}) == len(CIVILIANS), "two civilians on one cell"
assert free(BARRACKS_EXIT) and BARRACKS_EXIT[1] == BARRACKS[1] + 2 and BARRACKS[0] <= BARRACKS_EXIT[0] <= BARRACKS[0] + 1, ("barracks exit", BARRACKS_EXIT)
wx0, wy0, wx1, wy1 = WANDER["rect"]
assert X0 < wx0 < wx1 < X1 and Y0 < wy0 < wy1 < Y1, ("wander rect outside the compound", WANDER)


def reaches(starts, goals, ok):
    """4-connected flood fill from any start to any goal over the cells `ok` accepts."""
    seen = {c for c in starts if ok(c)}
    queue = list(seen)
    for cur in queue:
        if cur in goals:
            return True
        for nxt in ((cur[0] + 1, cur[1]), (cur[0] - 1, cur[1]), (cur[0], cur[1] + 1), (cur[0], cur[1] - 1)):
            if nxt not in seen and ok(nxt):
                seen.add(nxt)
                queue.append(nxt)
    return False


def block_free(c, width=2):
    return all(free((c[0] + i, c[1] + j)) for i in range(width) for j in range(width))


for point in bf["defense_points"]:
    start = (point["x"], point["y"])
    assert free(start) and reaches([start], {BARRACKS_EXIT}, free), ("no foot path from the defense point to the barracks exit", point["id"])
    # a lane of two cells: a free 2x2 block can slide from the point's surroundings to the exit's
    near = lambda c: [(c[0] + dx, c[1] + dy) for dx in (-1, 0) for dy in (-1, 0)]
    assert reaches(near(start), set(near(BARRACKS_EXIT)), block_free), ("the lane from the defense point to the barracks exit is narrower than two cells", point["id"])

bf3 = dict(bf2)
bf3["id"] = "village_01"
bf3["buildings"] = b3
bf3["objectives"] = [{"id": "barracks", "role": "barracks", "required": True}]
bf3["exits"] = {"barracks": list(BARRACKS_EXIT)}
bf3["civilians"] = [{"actor": a, "x": x, "y": y} for a, x, y in CIVILIANS]
bf3["wander"] = WANDER
bf3["note"] = ("The level 1 map (schema 3): defense_02's wall ring, openings, three defense points, entries, sockets and view, with the "
               "compound turned into a village. The infantry barracks (the one required objective) stands in the centre, ten civilian "
               "houses (v01..v08 at their OpenRA footprints) form a ring around it, and ten civilians (eight technicians, a man and a "
               "woman) wander inside the wander rectangle. Rows 21 and 22 stay clear from the left opening to the right one and columns "
               "36..41 stay clear above the barracks, so every opening has a lane of at least two cells to the barracks exit (checked "
               "by the generator with a flood fill). No command core, factory, power plant or radar dome.")
(ROOT / "data/battlefields/village_01.json").write_text(json.dumps(bf3, indent=1) + "\n")
print(f"village_01: {len(village)} village buildings, {len(CIVILIANS)} civilians, exit {BARRACKS_EXIT}")
