"""The DJ Booth's scene trace (MAP04 The Focus; docs/doom/scenes/booth.md): writes tools/doom/trace/booth_pilot.json, which convert.py takes as the scene's trace.

    python -I tools/doom/trace/booth_scene.py
    python -I tools/doom/convert.py --scene booth --trace tools/doom/trace/booth_pilot.json
    python -I tools/doom/author_booth.py

Why this does not start from tools/doom/trace/booth.json: that trace is the render's macro footprint of MAP04 (a big dark hall, an S-corridor, a brown complex); the render does not
show the tight windowed control rooms the painting (`art/reference/doom_worlds/Rhythm Booth, Three Hidden Routes-5.png`) shows, and the brief says so (booth.json's `uncertain`). So the
scene is INVENTED FROM THE PAINTING and every sector below is an invention, flagged `approximate`; booth.json stays as the record of what the render could and could not give.

The painting's room (all metres, x east, y north; the viewer stands at the south end of the aisle and looks north):
  * a narrow control-room AISLE (3.5 m wide, 11 m long, 2.75 m ceiling);
  * on the left the raised DJ DAIS (+1 m: the desk with decks, mixer, lamp, racks under it) with a long WINDOW in its west wall onto a rainy iron BALCONY (the Balcony guide stands outside);
  * on the right a steel DOOR (open) onto the loading DOCK annex (flight cases, yellow floor stripes; the Dock guide stands inside);
  * ahead a HATCH at the aisle's end onto a violet chamber (the Mothership guide stands in it);
  * the balcony's STAIR (three 0.375 m steps) climbs at the porch beyond the double door at the aisle's north-west corner.
Everything is on a 0.25 m grid so every Doom coordinate is an integer.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "booth_pilot.json")
U = 32.0


def r(x0, y0, x1, y1):
    return (x0, y0, x1, y1)


# name, rect (m), floor (m), ceiling (m), light 0..255, floor flat, ceil flat
SECTORS = [
    ("aisle", r(-1.75, 0, 1.75, 11), 0.0, 2.75, 150, "FLOOR5_1", "CEIL3_5"),
    ("dais", r(-4, 0, -1.75, 7.5), 1.0, 2.75, 170, "FLOOR5_1", "CEIL3_5"),
    ("dstep_b", r(-4, 7.5, -1.75, 8.0), 0.75, 2.75, 160, "STEP1", "CEIL3_5"),
    ("dstep_a", r(-4, 8.0, -1.75, 8.5), 0.375, 2.75, 155, "STEP1", "CEIL3_5"),
    ("landing", r(-4, 8.5, -1.75, 11), 0.0, 2.75, 150, "FLOOR5_1", "CEIL3_5"),
    ("bal_door", r(-4.75, 8.5, -4, 11), 0.0, 2.25, 140, "FLOOR5_1", "CEIL3_5"),
    ("porch", r(-6, 8.5, -4.75, 11), 0.0, 3.5, 120, "FLOOR5_1", "CEIL3_5"),
    ("terrace", r(-9.75, 0, -4, 8.5), 0.0, 3.5, 120, "FLOOR5_1", "CEIL3_5"),
    ("bal_step_a", r(-7.25, 8.5, -6, 11), 0.375, 3.5, 120, "STEP1", "CEIL3_5"),
    ("bal_step_b", r(-8.5, 8.5, -7.25, 11), 0.75, 3.5, 120, "STEP1", "CEIL3_5"),
    ("bal_top", r(-9.75, 8.5, -8.5, 11), 1.125, 3.5, 130, "STEP1", "CEIL3_5"),
    ("hatch", r(-1, 11, 1, 12), 0.0, 2.5, 140, "FLOOR5_1", "CEIL3_5"),
    ("moth", r(-3, 12, 3, 17.5), 0.25, 4.25, 160, "FLOOR0_1", "CEIL3_5"),
    ("dock_door", r(1.75, 3, 2.5, 5.5), 0.0, 2.5, 150, "FLOOR5_1", "CEIL3_5"),
    ("dock", r(2.5, 0, 9, 9), 0.0, 4.0, 150, "FLOOR0_1", "CEIL3_5"),
]
# railings (flags impassable): the desk's edge on the aisle and on the landing, and the window onto the balcony (pairs of sector names)
RAILS = [("dais", "aisle"), ("dais", "terrace"), ("dstep_a", "terrace"), ("dstep_b", "terrace")]
START = (0.5, 1.75)


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
        "name": "MAP04",
        "title": "The Focus (the DJ Booth invented from the painting: aisle, dais, window, hatch, dock door, balcony stair)",
        "approximate": True,
        "uncertain": [
            "INVENTED FROM THE PAINTING (tools/doom/trace/booth_scene.py), not read from the render or the WAD (the supplied WAD has empty map lumps; the render of MAP04 gives only the macro footprint, see tools/doom/trace/booth.json).",
            "Every size, height and place is a guess from the painting: a 3.5 x 11 m aisle, the +1 m desk dais with a window onto a balcony, the dock door and annex on the right, the hatch and chamber ahead, the balcony porch and its three-step stair at the north-west corner.",
            "The brief's 'dance pit in front' is NOT modelled: the painting shows no pit; the crowd of the other scenes does not appear here.",
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
