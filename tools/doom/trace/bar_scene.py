"""The Copper Bar's room (docs/doom/scenes/bar.md): writes tools/doom/trace/bar_pilot.json, which convert.py takes as the scene's trace.

    python -I tools/doom/trace/bar_scene.py
    python -I tools/doom/convert.py --scene bar --trace tools/doom/trace/bar_pilot.json

The Warehouse pilot cut its rooms out of the render of MAP07 (a 2100 unit arena that is roughly the painting's room). MAP02 Underhalls is the opposite: the render
(tools/doom/trace/bar.json, 2400 units of nukage channel, plateau and plazas) is a hall complex, while the painting is a brick passage about 10 m long with a drain channel
beside it. So this trace keeps MAP02's IDEAS (the drain channel with its crossings, the brown-brick rooms, the short stairs up to a raised room) and lays them out as the PAINTING
shows them; none of it is read from the render or the WAD. Everything is INVENTED from `art/reference/doom_worlds/Copper Basement Bar, Three Hidden Routes-3.png` and is
listed in `uncertain`.

The room is a set of non-overlapping axis-aligned rectangles (metres, x east, y north, the painting's camera looks north from the south end of the passage). Each rectangle is one
Doom sector (convert.py cuts it into convex pieces; a rectangle is one). Edges are split wherever a neighbour has a corner on them, so two rectangles that share part of an edge
share exactly that part: a two-sided line where a neighbour is, a one-sided wall where none is.

    south  pass (the passage, paved)  .  channel (drain, grated crossings)  .  bar_* (the bar, the counter an island)
    west   way_w (the way to the Floor)          north  four stairs up, the booth landing, the desk, the booth behind it
    east   lounge_n (the way to the Chill-out): over the grated crossings, a step up
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "bar.json")
OUT = os.path.join(HERE, "bar_pilot.json")
U = 32.0

# name, x0, y0, x1, y1 (m), floor (m), ceiling (m), light, doom floor flat, doom ceiling flat
RECTS = [
    ("pass", -1.8, -3.0, 1.4, 6.2, 0.0, 3.25, 150, "FLOOR4_8", "CEIL3_5"),
    ("way_w", -7.0, 0.9, -1.8, 3.6, 0.0, 3.0, 140, "FLOOR5_1", "CEIL3_5"),
    ("stair_1", -1.2, 6.2, 1.4, 6.6, 0.3, 3.5, 150, "STEP1", "CEIL3_5"),
    ("stair_2", -1.2, 6.6, 1.4, 7.0, 0.6, 3.7, 150, "STEP1", "CEIL3_5"),
    ("stair_3", -1.2, 7.0, 1.4, 7.4, 0.9, 3.9, 150, "STEP1", "CEIL3_5"),
    ("stair_4", -1.2, 7.4, 1.4, 7.8, 1.2, 4.0, 150, "STEP1", "CEIL3_5"),
    ("booth", -1.2, 7.8, 1.4, 10.2, 1.5, 4.2, 160, "FLOOR0_1", "CEIL3_5"),
    ("desk", -1.2, 10.2, 1.4, 10.8, 2.5, 4.2, 170, "FLOOR0_1", "CEIL3_5"),
    ("booth_back", -1.2, 10.8, 1.4, 12.6, 1.5, 4.2, 170, "FLOOR0_1", "CEIL3_5"),
    ("chan_a", 1.4, 3.4, 2.6, 3.8, -0.6, 3.25, 110, "NUKAGE1", "CEIL3_5"),
    ("bridge_1", 1.4, 3.8, 2.6, 4.8, 0.0, 3.25, 150, "GRATE", "CEIL3_5"),
    ("chan_b", 1.4, 4.8, 2.6, 5.2, -0.6, 3.25, 110, "NUKAGE1", "CEIL3_5"),
    ("bridge_2", 1.4, 5.2, 2.6, 6.2, 0.0, 3.25, 150, "GRATE", "CEIL3_5"),
    ("chan_c", 1.4, 6.2, 2.6, 10.2, -0.6, 3.25, 110, "NUKAGE1", "CEIL3_5"),
    ("bar_w", 1.4, 0.2, 3.2, 2.2, 0.3, 3.25, 160, "FLOOR5_1", "CEIL3_5"),
    ("bar_back", 3.2, 0.2, 6.6, 1.5, 0.3, 3.25, 170, "FLOOR5_1", "CEIL3_5"),
    ("bar_e", 6.6, 0.2, 7.0, 2.2, 0.3, 3.25, 160, "FLOOR5_1", "CEIL3_5"),
    ("counter", 3.2, 1.5, 6.6, 2.2, 1.3, 3.0, 170, "FLOOR0_1", "CEIL3_5"),
    ("bar_front", 1.4, 2.2, 7.0, 3.4, 0.3, 3.25, 160, "FLOOR5_1", "CEIL3_5"),
    ("lounge_n", 2.6, 3.4, 7.0, 8.6, 0.4, 3.25, 150, "FLOOR5_1", "CEIL3_5"),
    # round 2: the way's west end is no longer a flat blue door but the painting's left doorway: an arch (a 1.9 m opening under a 2.5 m lintel) and a short wet passage
    # beyond it, blue-lit, ending 4 m on at the Floor's glow
    ("way_arch", -7.6, 1.3, -7.0, 3.2, 0.0, 2.5, 140, "FLOOR5_1", "CEIL3_5"),
    ("way_out", -11.0, 1.0, -7.6, 3.5, 0.0, 2.9, 150, "FLOOR5_1", "CEIL3_5"),
]
THINGS = [{"x": int(0.1 * U), "y": int(-0.5 * U), "angle": 90, "type": 1, "flags": 7}]


def q(v):
    return int(round(v * U))


def main():
    src = json.load(open(SRC, encoding="utf-8"))
    rects = []
    for name, x0, y0, x1, y1, fl, ce, li, ft, ct in RECTS:
        rects.append((name, q(x0), q(y0), q(x1), q(y1), q(fl), q(ce), li, ft, ct))
    names = [r[0] for r in rects]
    # overlap check: rectangles may touch, never overlap
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            if a[1] < b[3] and b[1] < a[3] and a[2] < b[4] and b[2] < a[4]:
                raise SystemExit("rectangles %s and %s overlap" % (a[0], b[0]))
    corners = set()
    for r in rects:
        for p in ((r[1], r[2]), (r[3], r[2]), (r[3], r[4]), (r[1], r[4])):
            corners.add(p)

    def owner(x2, y2):
        """The rectangle holding the point (in doubled units, so a midpoint stays an integer)."""
        for i, r in enumerate(rects):
            if r[1] * 2 < x2 < r[3] * 2 and r[2] * 2 < y2 < r[4] * 2:
                return i
        return None

    V, VI = [], {}

    def vid(p):
        if p not in VI:
            VI[p] = len(V)
            V.append(list(p))
        return VI[p]

    SD, LD = [], []

    def sidedef(sec):
        SD.append({"xoff": 0, "yoff": 0, "upper": "-", "lower": "-", "middle": "STARTAN3", "sector": sec})
        return len(SD) - 1

    done = set()
    for i, r in enumerate(rects):
        _, x0, y0, x1, y1 = r[:5]
        ring = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]  # counter-clockwise
        for k in range(4):
            a, b = ring[k], ring[(k + 1) % 4]
            on = sorted([p for p in corners if p != a and p != b and (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) == 0
                         and min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])],
                        key=lambda p: (p[0] - a[0]) ** 2 + (p[1] - a[1]) ** 2)
            pts = [a] + on + [b]
            for s in range(len(pts) - 1):
                p, qq = pts[s], pts[s + 1]
                key = (p, qq)
                if key in done:
                    continue
                done.add(key)
                done.add((qq, p))
                # the other side: the midpoint pushed outward (to the right of p -> qq, since the interior is on the left)
                dx, dy = qq[0] - p[0], qq[1] - p[1]
                mx2, my2 = p[0] + qq[0], p[1] + qq[1]
                nx, ny = (dy > 0) - (dy < 0), -((dx > 0) - (dx < 0))  # unit step to the right of the direction
                j = owner(mx2 + nx, my2 + ny)
                if j is None:  # a wall: one-sided, the owner on the right of the reversed line
                    LD.append({"v1": vid(qq), "v2": vid(p), "flags": 1, "special": 0, "tag": 0, "right": sidedef(i), "left": -1})
                else:
                    LD.append({"v1": vid(p), "v2": vid(qq), "flags": 4, "special": 0, "tag": 0, "right": sidedef(j), "left": sidedef(i)})
    sectors = [{"floor": r[5], "ceiling": r[6], "light": r[7], "special": 0, "tag": 0, "floor_tex": r[8], "ceil_tex": r[9]} for r in rects]
    t = {
        "name": "MAP02",
        "title": "Underhalls (the Copper Bar: the painting's passage laid out by hand; MAP02's render is a hall complex)",
        "approximate": True,
        "uncertain": list(src.get("uncertain", [])) + [
            "THE COPPER BAR (tools/doom/trace/bar_scene.py) is NOT read from the render or the WAD: the render of MAP02 (2400 units, channel loop, plateau, plazas) does not contain the painting's room (a 10 m brick passage). "
            "The scene keeps MAP02's ideas (the drain channel with crossings, brown brick rooms, short stairs up) and lays them out as the painting shows them. Every size and place is an invention.",
            "Heights are guessed from the painting: the channel 0.6 m under the paving (round 2: was 1 m; the water now shows from the reference viewpoint; two grated crossings), the bar 0.3 m up, the Chill-out nook 0.4 m up, four 0.3 m stairs to the booth landing (+1.5 m), the booth desk +1 m.",
        ],
        "vertices": V, "linedefs": LD, "sidedefs": SD, "sectors": sectors, "sector_names": names, "things": THINGS,
    }
    json.dump(t, open(OUT, "w", encoding="utf-8", newline="\n"), indent=0, separators=(",", ":"))
    open(OUT, "a", encoding="utf-8", newline="\n").write("\n")
    print("wrote %s: %d sectors, %d linedefs, %d vertices" % (OUT, len(rects), len(LD), len(V)))


if __name__ == "__main__":
    sys.exit(main())
