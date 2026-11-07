"""The Loading Dock scene's geometry (MAP13 Downtown; docs/doom/scenes/dock.md): writes tools/doom/trace/dock_pilot.json, which convert.py takes as the scene's trace.

    python -I tools/doom/trace/dock_scene.py
    python -I tools/doom/convert.py --scene dock --trace tools/doom/trace/dock_pilot.json
    python -I tools/doom/author_dock.py

Why this does not start from tools/doom/trace/dock.json: that trace is the render's macro footprint of MAP13 (one huge plaza with fourteen diamond city blocks, no doors, no props); it holds no
loading dock, no shutter, no brick wall with a door. So, as with the Booth, the room is INVENTED FROM THE PAINTING (`art/reference/doom_worlds/Rainy Rhythm Club Loading Dock-6.png`) on a 0.25 m
grid, every sector flagged `approximate`; dock.json stays as the record of what the render could and could not give (it does give the open sky and the loose grid of blocks: the street is open, the
blocks are walls round it).

The painting's place (metres, x east, y north; the viewer stands on the concrete apron at the south and looks north):
  * the club's concrete loading APRON (+0.25 m, yellow-striped edge, drain grate, bollards, flight cases, pallets); its east part is under a steel CANOPY (a hanging caged lamp and a chain) against the
    club's roller SHUTTER (the east wall);
  * on the left the red BRICK wall of the club with a steel door ajar (the blue-lit passage back to the dance floor: the Floor guide stands in it) and the SIDEWALK along the wall;
  * ahead the wet asphalt STREET running north between dark towers, a sodium street lamp, the MOTHERSHIP guide (violet, white hair, horns) at its far end;
  * on the right, past the shutter wall, the service YARD: a parked van, pallet stacks, chain-link fence, a domed boiler furnace with a glowing mouth where the UNDERWORLD guide (red, horned, on
    crates with a drum) sits.
NOT modelled: the street's curve to the left, the fence as geometry (a wall decal), the rain (nothing falls) and the puddle reflections.
Everything is on a 0.25 m grid so every Doom coordinate is an integer.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "dock_pilot.json")

U = 32.0


def r(x0, y0, x1, y1):
    return (x0, y0, x1, y1)


# name, rect (m), floor (m), ceiling (m), light 0..255, floor flat, ceil flat.  Outdoor ceilings are the night sky: 7.5 m, a dark tile.
SECTORS = [
    ("apron", r(-4, 0, 4, 4.5), 0.25, 7.5, 120, "FLOOR5_1", "CEIL3_5"),
    ("canopy", r(4, 0, 7.5, 4.5), 0.25, 3.5, 140, "FLOOR5_1", "CEIL3_5"),
    ("walk", r(-4, 4.5, -1.5, 20), 0.25, 7.5, 110, "FLOOR5_1", "CEIL3_5"),
    ("street", r(-1.5, 4.5, 7.5, 20), 0.0, 7.5, 100, "FLOOR0_1", "CEIL3_5"),
    ("yard", r(7.5, 8.5, 13.5, 16), 0.0, 7.5, 110, "FLOOR0_1", "CEIL3_5"),
    ("floor_door", r(-5.5, 6, -4, 10), 0.25, 2.75, 110, "FLOOR5_1", "CEIL3_5"),
    ("floor_hall", r(-10, 6, -5.5, 11.5), 0.25, 3.2, 110, "FLOOR5_1", "CEIL3_5"),
]
RAILS = []
START = (2.0, 0.75)


def main():
    names = [s[0] for s in SECTORS]
    rings, V, L, SD, SEC = {}, [], [], [], []

    def u(v):
        return int(round(v * U))

    def rect_ring(rc):
        x0, y0, x1, y1 = (u(v) for v in rc)
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]  # counter-clockwise in (x, y)

    for nm, rc, fl, ce, li, ft, ct in SECTORS:
        rings[nm] = rect_ring(rc)
        SEC.append({"floor": u(fl), "ceiling": u(ce), "light": li, "special": 0, "tag": 0, "floor_tex": ft, "ceil_tex": ct})
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
    rail_pairs = {frozenset((names.index(a), names.index(b))) for a, b in RAILS}
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
        flags = 5 if frozenset((owner, other)) in rail_pairs else 4
        L.append({"v1": vid(a), "v2": vid(b), "flags": flags, "special": 0, "tag": 0, "right": sidedef(other), "left": sidedef(owner)})
    trace = {
        "name": "MAP13",
        "title": "Downtown (the Loading Dock invented from the painting: apron, canopy, sidewalk, street, yard, the club door and passage)",
        "approximate": True,
        "uncertain": [
            "INVENTED FROM THE PAINTING (tools/doom/trace/dock_scene.py), not read from the render or the WAD (the supplied WAD has empty map lumps; the render of MAP13 gives only the street grid, see tools/doom/trace/dock.json).",
            "Every size, height and place is a guess from the painting: an 11.5 x 4.5 m concrete apron (the east third under a 3.5 m canopy), a sidewalk and a 9 m wide street running 15 m north, a service yard on the east, the club's brick wall with a 4 m door and a short blue passage on the west.",
            "The painting's street curves left and its fence runs behind the van; here the street is straight and the fence is a wall decal.",
        ],
        "vertices": [list(v) for v in V], "linedefs": L, "sidedefs": SD, "sectors": SEC, "sector_names": names,
        "things": [{"x": u(START[0]), "y": u(START[1]), "angle": 90, "type": 1, "flags": 7}],
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(trace, f, indent=0, separators=(",", ":"))
        f.write("\n")
    print("wrote %s: %d sectors, %d linedefs" % (OUT, len(SEC), len(L)))


if __name__ == "__main__":
    main()
