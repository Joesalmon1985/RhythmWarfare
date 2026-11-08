"""Writes the hand-traced approximate maps tools/doom/trace/<scene>.json (python -I tools/doom/trace/make_traces.py).

These are NOT read from a WAD: the supplied doom2.wad has no map geometry. Each trace is an estimate of the Doom II map's footprint from
knowledge of the level and the ian-albert renders' general shape (the render images could not be inspected here), written in the form a WAD
gives (vertices, linedefs with sidedefs, sectors, things) so convert.py --trace takes it through the identical chain. Sectors are authored as
polygon rings (outer counter-clockwise, holes clockwise, Doom units, y up); linedefs and sidedefs are derived from shared edges, and a vertex
that lies on another sector's edge splits that edge. Every trace is marked approximate with a list of uncertain notes.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def area2(p):
    return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def rot(p, k):
    for _ in range(k % 4):
        p = (-p[1], p[0])
    return p


def sector(sid, rings, floor, ceil, light, ftex="FLOOR4_8", ctex="CEIL3_5"):
    return {"id": sid, "rings": rings, "floor": floor, "ceiling": ceil, "light": light, "floor_tex": ftex, "ceil_tex": ctex}


def build(name, title, sectors, uncertain, things, xf=None):
    # normalise orientation: first ring outer ccw, the rest holes cw
    flip = False  # a transform with a negative determinant (image y points down) reverses orientation: author rings clockwise then
    if xf is not None:
        o, a, b = xf((0, 0)), xf((100, 0)), xf((0, 100))
        flip = (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]) < 0
    norm = []
    for s in sectors:
        rings = []
        for i, r in enumerate(s["rings"]):
            r = [tuple(p) for p in r]
            if ((area2(r) > 0) != flip) != (i == 0):
                r.reverse()
            rings.append(r)
        norm.append((s, rings))
    allv = {p for _, rings in norm for r in rings for p in r}
    # split edges at vertices lying on them
    def split(r):
        out = []
        for i in range(len(r)):
            a, b = r[i], r[(i + 1) % len(r)]
            on = []
            for v in allv:
                if v != a and v != b and (b[0] - a[0]) * (v[1] - a[1]) - (b[1] - a[1]) * (v[0] - a[0]) == 0:
                    t = (v[0] - a[0]) * (b[0] - a[0]) + (v[1] - a[1]) * (b[1] - a[1])
                    if 0 < t < (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2:
                        on.append((t, v))
            out.append(a)
            out.extend(v for _, v in sorted(on))
        return out
    edges = {}  # (a, b) -> sector index, interior on the left
    for si, (s, rings) in enumerate(norm):
        for r in rings:
            r = split(r)
            for i in range(len(r)):
                key = (r[i], r[(i + 1) % len(r)])
                assert key not in edges, "%s: edge %s used twice" % (name, key)
                edges[key] = si
    verts = sorted(allv)
    vi = {v: i for i, v in enumerate(verts)}
    if xf is not None:
        out_v = [tuple(xf(v)) for v in verts]
        assert len(set(out_v)) == len(out_v), "%s: two authored vertices collapse after the transform" % name
    sides, lines, done = [], [], set()

    def side(si):
        sides.append({"xoff": 0, "yoff": 0, "upper": "-", "lower": "-", "middle": "STARTAN3", "sector": si})
        return len(sides) - 1
    for (a, b), si in sorted(edges.items()):
        if (a, b) in done:
            continue
        other = edges.get((b, a))
        if other is None:  # one-sided: the sector is on the right of b -> a
            lines.append({"v1": vi[b], "v2": vi[a], "flags": 1, "special": 0, "tag": 0, "right": side(si), "left": -1})
        else:  # two-sided: other on the right of a -> b, this sector on the left
            done.add((b, a))
            lines.append({"v1": vi[a], "v2": vi[b], "flags": 4, "special": 0, "tag": 0, "right": side(other), "left": side(si)})
        done.add((a, b))
    d = {"name": name, "title": title, "approximate": True, "uncertain": uncertain,
         "vertices": [list(v) for v in (out_v if xf is not None else verts)], "linedefs": lines, "sidedefs": sides,
         "sectors": [{"floor": s["floor"], "ceiling": s["ceiling"], "light": s["light"], "special": 0, "tag": 0,
                      "floor_tex": s["floor_tex"], "ceil_tex": s["ceil_tex"]} for s, _ in norm],
         "sector_names": [s["id"] for s, _ in norm], "things": things}
    return d


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def oct_(apothem, side_half):
    a, b = apothem, side_half
    return [(a, -b), (a, b), (b, a), (-b, a), (-a, b), (-a, -b), (-b, -a), (b, -a)]



if __name__ == "__main__":
    import render_trace
    render_trace.main()
