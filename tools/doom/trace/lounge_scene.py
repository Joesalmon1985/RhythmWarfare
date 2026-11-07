"""The Chill-out Lounge scene's geometry (docs/doom/scenes/lounge.md): writes tools/doom/trace/lounge_pilot.json, which convert.py takes as the scene's trace.

    python -I tools/doom/trace/lounge_scene.py
    python -I tools/doom/convert.py --scene lounge --trace tools/doom/trace/lounge_pilot.json
    python -I tools/doom/author_lounge.py

All in Doom units (32 = 1 m, x east, y north). WHAT IS READ AND WHAT IS INVENTED:
  * read from the MAP08 render trace (tools/doom/trace/lounge.json): the central octagonal hub, about 510 units across (here an octagon of inradius 240, vertices at +-100/+-240), whose
    middle is a sunken pit (the render's blue pool, floor -24, here the conversation pit) with eight faces (the brief's "eight doors");
  * invented from the painting (art/reference/doom_worlds/Mustard octagonal lounge of three routes-2.png): the concentric rings (the 0.375 m steps down to the pit, the sofa seats and
    backs, the rug's stripes, the low octagonal table), the three open doorways (ahead = N face, left = NW face, right = NE face) with the short rooms behind them, the five curtained niches.
    The rooms the render shows radiating from the hub (a long brown room, a large grey room, ...) are NOT built: only a few metres behind each doorway, enough to see and to walk to the threshold.

Room names (stable: the Magic rave will borrow this geography): hub = `concourse` (the walkway ring), `step_ring`, `seat_n/seat_s`, `back_n/back_s`, `gap_e/gap_w` (the pit stairs), the rug bands, `table`;
  ahead (Dock): `ahead_step_a/b`, `ahead_street`; left (Bar): `left_vest`, `left_bar`, `left_counter`; right (Floor): `right_vest`, `right_passage`; niches: `niche_e/w/s/se/sw`.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "lounge_pilot.json")
SRC = os.path.join(HERE, "lounge.json")

R_OUT = 240
FLOORS = {}  # filled by SECTORS below


def oct_pts(r):
    """Octagon of inradius r, counter-clockwise from (r, a): indices 0..7 = (r,a) (a,r) (-a,r) (-r,a) (-r,-a) (-a,-r) (a,-r) (r,-a)."""
    a = 100 if r == 240 else int(round(r * 0.41421356))  # (the outer octagon's diagonal faces are centred on (+-170, +-170): the doorways' frames)
    return [(r, a), (a, r), (-a, r), (-r, a), (-r, -a), (-a, -r), (a, -r), (r, -a)]


def area2(p):
    return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def ccw(p):
    return list(p) if area2(p) > 0 else list(reversed(p))


def cw(p):
    return list(reversed(ccw(p)))


def band(r_out, r_in, i0=0, i1=7, whole=False):
    """The ring between two octagons (with a hole), or an arc of it from vertex i0 to i1 (counter-clockwise)."""
    if whole:
        return [ccw(oct_pts(r_out)), cw(oct_pts(r_in))]
    o, n = oct_pts(r_out), oct_pts(r_in)
    idx = list(range(i0, i1 + 1))
    return [[o[i] for i in idx] + [n[i] for i in reversed(idx)]]


# --- doorways: a frame on an octagon face (centre c, outward normal n, tangent t = (-ny, nx)); a point is c + u t + v n in coordinate units, so the diagonal faces use units of 1/sqrt 2 m
FACES = {  # name: (centre, normal, scale: coordinate units per Doom unit of length)
    "n": ((0, 240), (0, 1), 1.0), "e": ((240, 0), (1, 0), 1.0), "w": ((-240, 0), (-1, 0), 1.0), "s": ((0, -240), (0, -1), 1.0),
    "ne": ((170, 170), (1, 1), 0.70711), "nw": ((-170, 170), (-1, 1), 0.70711), "se": ((170, -170), (1, -1), 0.70711), "sw": ((-170, -170), (-1, -1), 0.70711),
}


def frame(face, u0, u1, v0, v1):
    """A rectangle in a face's frame (lengths in Doom units: width u0..u1 along the face, depth v0..v1 out of the room), as a counter-clockwise ring of integers."""
    c, n, s = FACES[face]
    t = (-n[1], n[0])
    pts = []
    for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
        uu, vv = int(round(u * s)), int(round(v * s))
        pts.append((c[0] + uu * t[0] + vv * n[0], c[1] + uu * t[1] + vv * n[1]))
    return ccw(pts)


def to_world(face, u, v):
    c, n, s = FACES[face]
    t = (-n[1], n[0])
    uu, vv = u * s, v * s
    return (c[0] + uu * t[0] + vv * n[0], c[1] + uu * t[1] + vv * n[1])


# name, rings (outer counter-clockwise, holes clockwise), floor, ceiling, light, floor_tex, ceil_tex
SEC = []


def add(name, rings, floor, ceiling, light=170):
    SEC.append((name, rings, floor, ceiling, light))


# the hub (read from the render: an octagon with a sunken middle)
CEIL_HUB, CEIL_DOME = 176, 224
add("concourse", band(240, 152, whole=True), 0, CEIL_HUB, 160)
add("step_ring", band(152, 128, whole=True), -12, CEIL_DOME, 150)
add("back_n", band(128, 114, 0, 3), 2, CEIL_DOME, 150)
add("back_s", band(128, 114, 4, 7), 2, CEIL_DOME, 150)
add("seat_n", band(114, 100, 0, 3), -10, CEIL_DOME, 160)
add("seat_s", band(114, 100, 4, 7), -10, CEIL_DOME, 160)
o128, o100 = oct_pts(128), oct_pts(100)
add("gap_e", [[o128[7], o128[0], o100[0], o100[7]]], -18, CEIL_DOME, 150)  # the pit stairs, east and west (a 6 unit step each way)
add("gap_w", [[o128[3], o128[4], o100[4], o100[3]]], -18, CEIL_DOME, 150)
add("rug_rim", band(100, 92, whole=True), -24, CEIL_DOME, 165)
add("rug_stripe_a", band(92, 88, whole=True), -24, CEIL_DOME, 190)
add("rug_mid", band(88, 70, whole=True), -24, CEIL_DOME, 165)
add("rug_stripe_b", band(70, 66, whole=True), -24, CEIL_DOME, 190)
add("rug_in", band(66, 34, whole=True), -24, CEIL_DOME, 170)
add("table", [ccw(oct_pts(34))], -10, CEIL_DOME, 200)

# ahead (N, to the Dock): two shallow steps up through the doorway to a rain-slick street
add("ahead_step_a", [frame("n", -48, 48, 0, 16)], 8, 128, 150)
add("ahead_step_b", [frame("n", -48, 48, 16, 32)], 16, 128, 140)
add("ahead_street", [frame("n", -80, 80, 32, 200)], 16, 144, 120)
# left (NW, to the Bar): an open arch into the bar room, the counter an island (1.1 m: shut to walkers)
add("left_vest", [frame("nw", -64, 64, 0, 34)], 0, 128, 160)
add("left_bar", [frame("nw", -110, 110, 34, 190), cw(frame("nw", -4, 100, 96, 118))], 0, 128, 150)
add("left_counter", [frame("nw", -4, 100, 96, 118)], 36, 128, 170)
# right (NE, to the Floor): a blue-lit passage with a bridge's rail (the painting)
add("right_vest", [frame("ne", -64, 64, 0, 34)], 0, 128, 150)
add("right_passage", [frame("ne", -80, 80, 34, 220)], 0, 128, 130)
# five curtained niches (the hub's other faces)
for fc in ("e", "w", "s", "se", "sw"):
    add("niche_" + fc, [frame(fc, -48, 48, 0, 44)], 0, 128, 150)


def split_at_vertices(ring, verts):
    """Insert every vertex that lies strictly inside an edge of the ring (no T-junction cracks)."""
    out = []
    for i in range(len(ring)):
        a, b = ring[i], ring[(i + 1) % len(ring)]
        on = []
        for p in verts:
            if p == a or p == b:
                continue
            if (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) == 0:
                tt = (p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])
                if 0 < tt < (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2:
                    on.append((tt, p))
        out.append(a)
        out.extend(p for _, p in sorted(on))
    return out


def main():
    src = json.load(open(SRC, encoding="utf-8"))
    verts = set()
    for _n, rings, *_r in SEC:
        for rg in rings:
            verts.update(rg)
    V, L, SD, SECT, names = [], [], [], [], []

    def vid(p):
        if p not in V:
            V.append(p)
        return V.index(p)

    def sidedef(sec):
        SD.append({"xoff": 0, "yoff": 0, "upper": "-", "lower": "-", "middle": "STARTAN3", "sector": sec})
        return len(SD) - 1

    edges = {}
    for si, (name, rings, fl, ce, li) in enumerate(SEC):
        names.append(name)
        SECT.append({"floor": fl, "ceiling": ce, "light": li, "special": 0, "tag": 0, "floor_tex": "FLOOR4_8", "ceil_tex": "CEIL3_5"})
        for rg in rings:
            r = split_at_vertices(rg, verts)
            for i in range(len(r)):
                key = (r[i], r[(i + 1) % len(r)])
                if key in edges:
                    raise SystemExit("edge %s used twice (sectors overlap: %s and %s)" % (key, SEC[edges[key]][0], name))
                edges[key] = si
    done = set()
    for (a, b), owner in sorted(edges.items()):
        if (a, b) in done:
            continue
        other = edges.get((b, a))
        if other is not None:  # a two-sided line: the owner (interior on the left of a -> b) is the left side
            done.update([(a, b), (b, a)])
            L.append({"v1": vid(a), "v2": vid(b), "flags": 4, "special": 0, "tag": 0, "right": sidedef(other), "left": sidedef(owner)})
        else:  # a wall: one-sided, the owner on the right of b -> a
            done.add((a, b))
            L.append({"v1": vid(b), "v2": vid(a), "flags": 1, "special": 0, "tag": 0, "right": sidedef(owner), "left": -1})
    t = {
        "name": "MAP08", "title": "Tricks and Traps (the hub octagon of the render trace, plus the lounge's rings, doorways and niches)", "approximate": True,
        "uncertain": list(src["uncertain"][:1]) + [
            "READ from the render trace: the central octagonal hub (inradius 240 units = 7.5 m, the render's 510 unit octagon) with a sunken middle (the blue pool, here the conversation pit at -24).",
            "INVENTED from the concept image (tools/doom/trace/lounge_scene.py), not read from the render or the WAD: the rings round the pit (steps -12, sofa seat -10 and back +8, the pit stairs east and west, the rug bands, the low table), the three open doorways (ahead N, left NW, right NE) and the short rooms behind them (a rain-slick street, a bar room with a counter, a blue-lit passage), the five curtained niches on the other faces.",
            "NOT built: the render's big rooms round the hub (the long brown room, the large grey room, the south-west grey room, ...), the trap rooms and the small towers; the doors between them are not readable from the render (the brief's eight doors are the hub's eight faces here: three open, five curtained).",
        ],
        "vertices": [list(v) for v in V], "linedefs": L, "sidedefs": SD, "sectors": SECT, "sector_names": names,
        "things": [{"x": 0, "y": -196, "angle": 90, "type": 1, "flags": 7}],
    }
    json.dump(t, open(OUT, "w", encoding="utf-8", newline="\n"), indent=0, separators=(",", ":"))
    open(OUT, "a", encoding="utf-8", newline="\n").write("\n")
    print("wrote %s: %d sectors, %d linedefs, %d vertices" % (OUT, len(SECT), len(L), len(V)))


if __name__ == "__main__":
    main()
