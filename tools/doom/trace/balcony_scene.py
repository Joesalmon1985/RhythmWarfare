"""The Balcony's scene trace (MAP15 Industrial Zone; docs/doom/scenes/balcony.md): writes tools/doom/trace/balcony_pilot.json, which convert.py takes as the scene's trace.

    python -I tools/doom/trace/balcony_scene.py
    python -I tools/doom/convert.py --scene balcony --trace tools/doom/trace/balcony_pilot.json
    python -I tools/doom/author_balcony.py

Why this does not start from tools/doom/trace/balcony.json: that trace is the render's macro footprint of MAP15 (a grass plateau, a lake, brown towers, a ring building); it shows no rooftop,
no roof ledges and no bridges (balcony.json's `uncertain` says so). So the scene is INVENTED FROM THE PAINTING (`art/reference/doom_worlds/Rainy industrial rooftop, three musical paths-8.png`)
and every sector below is an invention, flagged `approximate`; balcony.json stays as the record of what the render could and could not give.

The painting's place (all metres, x east, y north; the viewer stands at the roof deck's south end and looks north):
  * a wet concrete ROOF DECK (7 x 9 m) with flight cases and cable at the viewer's right and a rusty railing along its open north edge;
  * on the left, in a brick wall, an iron STAIR running down past the deck's west edge, with a LANDING at its head (the Floor guide stands at the landing's rail);
  * on the right a control CABIN with a lit window and an open door (the Booth guide stands in the doorway);
  * ahead a short iron BRIDGE (three steps up) over the dark drop to a platform at the foot of a tower (the Mothership guide stands there); the drop is three or more storeys (the pits are VOIDS).
Everything is on a 0.25 m grid so every Doom coordinate is an integer.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "balcony_pilot.json")
U = 32.0


def r(x0, y0, x1, y1):
    return (x0, y0, x1, y1)


# name, rect (m), floor (m), ceiling (m), light 0..255, floor flat, ceil flat
SECTORS = [
    ("deck", r(-3.5, 0, 3.5, 9), 0.0, 8.0, 110, "FLOOR5_1", "CEIL3_5"),
    ("landing", r(-6.5, 5, -3.5, 8), 0.0, 8.0, 120, "FLOOR5_1", "CEIL3_5"),
    ("s_a", r(-6.5, 4, -3.5, 5), -0.375, 8.0, 110, "STEP1", "CEIL3_5"),
    ("s_b", r(-6.5, 3, -3.5, 4), -0.75, 8.0, 105, "STEP1", "CEIL3_5"),
    ("s_c", r(-6.5, 2, -3.5, 3), -1.125, 8.0, 100, "STEP1", "CEIL3_5"),
    ("s_d", r(-6.5, 1, -3.5, 2), -1.5, 8.0, 100, "STEP1", "CEIL3_5"),
    ("s_e", r(-6.5, 0, -3.5, 1), -1.875, 8.0, 100, "STEP1", "CEIL3_5"),
    ("bdoor", r(3.5, 3.5, 4.25, 7), 0.0, 2.5, 150, "FLOOR5_1", "CEIL3_5"),
    ("cabin", r(4.25, 2.5, 9, 8.5), 0.0, 3.5, 150, "FLOOR5_1", "CEIL3_5"),
    ("b_a", r(-1, 9, 1, 10), 0.375, 8.0, 105, "STEP1", "CEIL3_5"),
    ("b_b", r(-1, 10, 1, 11), 0.75, 8.0, 105, "STEP1", "CEIL3_5"),
    ("b_c", r(-1, 11, 1, 12), 1.125, 8.0, 105, "STEP1", "CEIL3_5"),
    ("bridge", r(-1, 12, 1, 16), 1.125, 8.0, 105, "FLOOR5_1", "CEIL3_5"),
    ("isle", r(-2, 16, 2, 19), 1.125, 8.0, 130, "FLOOR5_1", "CEIL3_5"),
    ("vw1", r(-9, 9, -1, 16), -9.0, 8.0, 60, "FLOOR0_1", "CEIL3_5"),
    ("vw2", r(-9, 16, -2, 19), -9.0, 8.0, 60, "FLOOR0_1", "CEIL3_5"),
    ("ve1", r(1, 9, 9, 16), -9.0, 8.0, 60, "FLOOR0_1", "CEIL3_5"),
    ("ve2", r(2, 16, 9, 19), -9.0, 8.0, 60, "FLOOR0_1", "CEIL3_5"),
]
# railings (flags impassable): the deck's open edges, the stair's open side, the bridge and the platform (pairs of sector names). isle|vw2 and isle|ve2 stay plain drops (the voids
# must stay connected to the map through one open portal each: the loader demands every sector reachable; a walker cannot cross a drop, the rail check proves it).
RAILS = [("deck", "s_a"), ("deck", "s_b"), ("deck", "s_c"), ("deck", "s_d"), ("deck", "s_e"), ("deck", "vw1"), ("deck", "ve1"),
         ("b_a", "vw1"), ("b_a", "ve1"), ("b_b", "vw1"), ("b_b", "ve1"), ("b_c", "vw1"), ("b_c", "ve1"), ("bridge", "vw1"), ("bridge", "ve1"), ("isle", "vw1"), ("isle", "ve1")]
START = (0.9, 0.5)


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
        "name": "MAP15",
        "title": "Industrial Zone (the rainy rooftop invented from the painting: deck, brick stair, cabin, bridge over the drop)",
        "approximate": True,
        "uncertain": [
            "INVENTED FROM THE PAINTING (tools/doom/trace/balcony_scene.py), not read from the render or the WAD (the supplied WAD has empty map lumps; the render of MAP15 gives only the macro footprint, see tools/doom/trace/balcony.json).",
            "Every size, height and place is a guess from the painting: a 7 x 9 m roof deck, the brick stair down the west side (five 0.375 m steps), the cabin on the east side, the three-step bridge north (1 m treads) and its platform; the surrounding drop is four voids nine metres deep.",
            "The painting's far roofs, towers, the forklift in the yard below and the walkway on the right are NOT modelled as geometry: they are billboards and decals in the voids.",
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
