"""Writes data/maps/field_80x40.json and data/battlefields/defense_01.json (the centred-base defense map).

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
