"""The Underworld's scene trace (MAP29 The Living End; docs/doom/scenes/underworld.md): writes tools/doom/trace/underworld_pilot.json, which convert.py takes as the scene's trace.

    python -I tools/doom/trace/underworld_scene.py
    python -I tools/doom/convert.py --scene underworld --trace tools/doom/trace/underworld_pilot.json
    python -I tools/doom/author_underworld.py

Why this does not start from tools/doom/trace/underworld.json: that trace is the render's lava basin (a ten-sided basin, a central rock mass, no path across it: its `uncertain` says so). The
painting (`art/reference/doom_worlds/Three Paths Across the Basalt Abyss-4.png`) is a viewer on a basalt plateau looking across a lava chasm at a stepped rock tower, with three ways on. So the
scene is INVENTED FROM THE PAINTING, every sector below is a guess, flagged `approximate`; underworld.json stays as the record of what the render could and could not give.

The painting's world (metres, x east, y north; the viewer stands at the south of the plateau and looks north; floors in metres, the cavern is open to a 22 m ceiling):
  * the PLATEAU (floor 0, 12.5 x 7.5 m, its north edge only 4 m from the viewer so that the lava shows beyond it), foreground basalt slabs, a rock wall on the left (the cliff the bone chimes hang from) and one on the right;
  * LEFT: the mouth of a blue-lit CAVE tunnel in the west wall (the Floor guide stands at its mouth);
  * AHEAD: a ledge (3.5 m wide, a 0.375 m step every 2 m up to +1.5) hugging the west cliff, then a gate pad and a causeway over the void to the foot of the TOWER (the Mothership guide stands on the
    ledge), four more steps up onto the tower terrace (+3 m) and a small stair to its top (+5 m);
  * RIGHT: a four-step stair (0.375 m risers) along the plateau's east side up to a SHELF at +1.5 m under a tent (the Dock guide stands on it);
  * between and beyond them the ABYSS: a void 4 m down (the lava, drawn far below and hazed by the engine's void rule), made of rectangles by the decomposition below, every rim a railing.
Everything is on a 0.5 m grid (walkable pieces on 0.25 m) so every Doom coordinate is an integer.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "underworld_pilot.json")
U = 32.0
CEIL = 12.0  # (every ceiling but the cave's is the map's red cloud sky: 12 m is the height of the far cliffs)
ABYSS_FLOOR = -5.0
BOX = (-4.5, 5.5, 30.0, 50.0)  # the abyss's bounding box (x0, y0, x1, y1): its edge on the walls is the far cliff  # (west of x = -4.5 the ledge and the tower stand against the solid cliff wall)

# name, rect (x0, y0, x1, y1) in m, floor, ceiling, light 0..255
WALK = [
    ("plateau_s", (-6.5, -2, 9.5, 3), 0.0, CEIL, 150),
    ("plateau_n", (-6.5, 3, 5, 5.5), 0.0, CEIL, 150),
    ("plateau_w", (-6.5, 5.5, -4.5, 9.5), 0.0, CEIL, 150),
    ("cave_mouth", (-8.5, 4.5, -6.5, 9.5), 0.0, 4.5, 130),
    ("cave", (-16, 4.5, -8.5, 9.5), 0.0, 3.5, 110),
    # the right: stair up to the shelf
    ("dstair_1", (5, 3, 9.5, 4.5), 0.375, CEIL, 150),
    ("dstair_2", (5, 4.5, 9.5, 6), 0.75, CEIL, 150),
    ("dstair_3", (5, 6, 9.5, 7.5), 1.125, CEIL, 150),
    ("dstair_4", (5, 7.5, 9.5, 9), 1.5, CEIL, 150),
    ("shelf", (5, 9, 14, 16), 1.5, CEIL, 160),
    # ahead: the ledge, the gate pad, the causeway, the tower's stair and terrace
    ("ledge_1", (-4.5, 5.5, -1, 7.5), 0.375, CEIL, 150),
    ("ledge_2", (-4.5, 7.5, -1, 9.5), 0.75, CEIL, 150),
    ("ledge_3", (-4.5, 9.5, -1, 11.5), 1.125, CEIL, 150),
    ("ledge_4", (-4.5, 11.5, -1, 13.5), 1.5, CEIL, 150),
    ("gate_pad", (-4.5, 13.5, -1, 17.5), 1.5, CEIL, 160),
    ("causeway", (-4.5, 17.5, -1, 27.5), 1.5, CEIL, 150),
    ("tstair_1", (-4.5, 27.5, -1, 28.5), 1.875, CEIL, 150),
    ("tstair_2", (-4.5, 28.5, -1, 29.5), 2.25, CEIL, 150),
    ("tstair_3", (-4.5, 29.5, -1, 30.5), 2.625, CEIL, 150),
    ("tstair_4", (-4.5, 30.5, -1, 31.5), 3.0, CEIL, 150),
    ("tower_s", (-6.5, 31.5, 9, 35.5), 3.0, CEIL, 170),
    ("tower_w", (-6.5, 35.5, -3, 39.5), 3.0, CEIL, 170),
    ("tower_e", (3, 35.5, 9, 39.5), 3.0, CEIL, 170),
    ("ttop_1", (-3, 35.5, 3, 36.5), 3.5, CEIL, 170),
    ("ttop_2", (-3, 36.5, 3, 37.5), 4.0, CEIL, 170),
    ("ttop_3", (-3, 37.5, 3, 38.5), 4.5, CEIL, 170),
    ("ttop_4", (-3, 38.5, 3, 39.5), 5.0, CEIL, 170),
]


def abyss_rects():
    """The box minus the walkable pieces, cut into rectangles on a 0.5 m grid (greedy: the longest run in a row, extended down while the whole span is free)."""
    x0, y0, x1, y1 = BOX
    nx, ny = int(round((x1 - x0) * 2)), int(round((y1 - y0) * 2))
    free = [[True] * nx for _ in range(ny)]
    for _n, (a, b, c, d), *_r in WALK:
        for j in range(ny):
            cy = y0 + (j + 0.5) / 2.0
            for i in range(nx):
                cx = x0 + (i + 0.5) / 2.0
                if a < cx < c and b < cy < d:
                    free[j][i] = False
    out = []
    for j in range(ny):
        i = 0
        while i < nx:
            if not free[j][i]:
                i += 1
                continue
            i2 = i
            while i2 < nx and free[j][i2]:
                i2 += 1
            j2 = j + 1
            while j2 < ny and all(free[j2][k] for k in range(i, i2)):
                j2 += 1
            for jj in range(j, j2):
                for k in range(i, i2):
                    free[jj][k] = False
            out.append((x0 + i / 2.0, y0 + j / 2.0, x0 + i2 / 2.0, y0 + j2 / 2.0))
            i = i2
    return out


SECTORS = list(WALK)
for k, rc in enumerate(abyss_rects()):
    SECTORS.append(("abyss_%02d" % k, rc, ABYSS_FLOOR, CEIL, 190))
START = (0.0, 1.6)


def main():
    names = [s[0] for s in SECTORS]
    rings, V, L, SD, SEC = {}, [], [], [], []

    def u(v):
        return int(round(v * U))

    for nm, rc, fl, ce, li in SECTORS:
        x0, y0, x1, y1 = (u(v) for v in rc)
        rings[nm] = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]  # counter-clockwise in (x, y)
        SEC.append({"floor": u(fl), "ceiling": u(ce), "light": li, "special": 0, "tag": 0, "floor_tex": "FLOOR4_8", "ceil_tex": "CEIL3_5"})
    allv = set(p for rg in rings.values() for p in rg)

    def vid(p):
        if p not in V:
            V.append(p)
        return V.index(p)

    def sidedef(sec):
        SD.append({"xoff": 0, "yoff": 0, "upper": "-", "lower": "-", "middle": "STARTAN3", "sector": sec})
        return len(SD) - 1

    def refine(rg):  # every other corner that lies on an edge of this ring cuts it (no T-junction cracks)
        out = []
        for i in range(len(rg)):
            a, b = rg[i], rg[(i + 1) % len(rg)]
            on = []
            for p in allv:
                if p != a and p != b and (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) == 0:
                    tt = (p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])
                    if 0 < tt < (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2:
                        on.append((tt, p))
            out.append(a)
            out.extend(p for _, p in sorted(on))
        return out

    edges = {}
    for nm in names:
        rg = refine(rings[nm])
        for i in range(len(rg)):
            k = (rg[i], rg[(i + 1) % len(rg)])
            if k in edges:
                raise SystemExit("edge %s owned twice: the sectors %s and %s overlap" % (k, names[edges[k]], nm))
            edges[k] = names.index(nm)
    done = set()
    for (a, b), owner in sorted(edges.items()):
        if (a, b) in done:
            continue
        other = edges.get((b, a))
        if other is None:  # a wall: one-sided, the sector on the right of b -> a
            done.add((a, b))
            L.append({"v1": vid(b), "v2": vid(a), "flags": 1, "special": 0, "tag": 0, "right": sidedef(owner), "left": -1})
            continue
        done.update([(a, b), (b, a)])
        L.append({"v1": vid(a), "v2": vid(b), "flags": 4, "special": 0, "tag": 0, "right": sidedef(other), "left": sidedef(owner)})
    trace = {
        "name": "MAP29",
        "title": "The Living End (the Underworld invented from the painting: plateau, cave, ledge and causeway, stair and shelf, the abyss, the tower)",
        "approximate": True,
        "uncertain": [
            "INVENTED FROM THE PAINTING (tools/doom/trace/underworld_scene.py), not read from the render or the WAD (the supplied WAD has empty map lumps; the render of MAP29 gives only a lava basin and a rock mass with no way across, see tools/doom/trace/underworld.json).",
            "Every size, height and place is a guess from the painting: a 12.5 x 7.5 m plateau, a cave mouth in the west wall, a 3.5 m ledge with 0.375 m steps along the west cliff to a gate pad and a causeway to the tower, a four step stair and a shelf on the east, a lava abyss 4 m down between them.",
            "NOT built: the winding lava river and the lava falls (decals and haze stand in), the tower's nested rings (a terrace and a small stair), the far terraced cliffs, the path beyond each guide (a wall).",
        ],
        "vertices": [list(v) for v in V], "linedefs": L, "sidedefs": SD, "sectors": SEC, "sector_names": names,
        "things": [{"x": u(START[0]), "y": u(START[1]), "angle": 90, "type": 1, "flags": 7}],
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(trace, f, indent=0, separators=(",", ":"))
        f.write("\n")
    print("wrote %s: %d sectors (%d abyss rectangles), %d linedefs" % (OUT, len(SEC), len(SEC) - len(WALK), len(L)))


if __name__ == "__main__":
    main()
