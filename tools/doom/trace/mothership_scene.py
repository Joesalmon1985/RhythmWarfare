"""The Mothership's scene trace (MAP11 Circle of Death; docs/doom/scenes/mothership.md): writes tools/doom/trace/mothership_pilot.json, which convert.py takes as the scene's trace.

    python -I tools/doom/trace/mothership_scene.py
    python -I tools/doom/convert.py --scene mothership --trace tools/doom/trace/mothership_pilot.json
    python -I tools/doom/author_mothership.py

Why this does not start from tools/doom/trace/mothership.json: that trace is the render's macro footprint of MAP11 (a grass basin, a ten sided ring, two black voids beside it); the painting
(`art/reference/doom_worlds/Mothership Ringwalk Over the Void-7.png`) wants one violet atrium: a RING WALKWAY (3.5 m wide) running round a circular VOID, a platform standing in the void on a
short bridge, and three hatches (one in the outer wall near the viewer on the right, one at the top of a stair far ahead). So, like the Booth, the scene is INVENTED FROM THE PAINTING and every
sector below is an invention, flagged `approximate`; mothership.json stays as the record of what the render could and could not give.

The room (metres, x east, y north, centre C = (0, 14), the viewer stands on the south of the ring and looks east-north-east, the void on the left):
  * the RING: 16 trapezoid pieces between radius 6.0 m (the inner rim, a railing) and 9.5 m (the outer wall), 9 m high (the atrium's vault);
  * the VOID: 15 wedge pieces between radius 3.0 and 6.0 m, floor -9 m (the painting's glowing green pool far below), shut by railings to every walker; one wedge (west) keeps an open edge to the
    ring only because StoryMap demands every sector reachable through portals (nobody can step across it: it is a void, `floor_change` kind void, and the rail check rejects any sample in one);
  * the BRIDGE: the wedge at the south, a 2 m to 1 m gangway from the ring's inner rim to the PLATFORM (a 16-gon of 3 m radius at C, the Booth guide's hatch at its north);
  * the DOCK hatch: an alcove in the outer wall on the right (two flat pieces, the vestibule);
  * the UNDERWORLD hatch: an alcove ahead with a four-piece stair (0.375 m risers) up to a landing and the hatch.
Coordinates snap to a 0.125 m grid (the arcs do not fit the Booth's 0.25 m grid without breaking convexity), so every Doom coordinate is an integer.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mothership_pilot.json")
U = 32.0
SNAP = 0.125
CX, CY = 0.0, 14.0
RI, RO, RH = 6.0, 9.5, 2.25  # (round 2: the platform 2.25 m (was 3): the pool between it and the ring is 3.75 m wide and shows over the parapet)
# the ring's inner and outer radius, the platform's radius
N = 16
STEP = 360.0 / N
CEIL, VOID_FLOOR = 5.5, -3.0  # round 2: the atrium's walls 5.5 m (were 9: the vault sky now shows over the ring), the pool 3 m down (was 9: its glow is in the pitched choice view)
BRIDGE_J = 0  # the ring piece / wedge centred at -90 degrees (south)
OPEN_WEDGE = 12  # the void wedge that keeps an unrailed portal to the ring (west, centred 180 degrees: out of every guide view)
DOCK_J = 2  # alcove centred -45 degrees
UW_J = 4  # alcove centred 0 degrees


def centre(j):
    return -90.0 + STEP * j


def snap(v):
    return round(round(v / SNAP) * SNAP, 4)


def pt(r, ang):
    a = math.radians(ang)
    return (snap(CX + r * math.cos(a)), snap(CY + r * math.sin(a)))


def band(j, r0, r1):
    """The quad between radius r0 and r1 over the piece j's angles: counter-clockwise (inner a0, outer a0, outer a1, inner a1)."""
    a0, a1 = centre(j) - STEP / 2, centre(j) + STEP / 2
    return [pt(r0, a0), pt(r1, a0), pt(r1, a1), pt(r0, a1)]


def area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))


def convex(poly):
    sg = 0
    for i in range(len(poly)):
        a, b, c = poly[i], poly[(i + 1) % len(poly)], poly[(i + 2) % len(poly)]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cr) < 1e-9:
            return False
        if sg and (cr > 0) != (sg > 0):
            return False
        sg = cr
    return True


# name, polygon (m), floor (m), ceiling (m), light 0..255, floor flat, ceil flat
def sectors():
    out = []
    for j in range(N):
        out.append(("ring_%d" % j, band(j, RI, RO), 0.0, CEIL, 150, "FLOOR0_1", "CEIL3_5"))
    for j in range(N):
        if j == BRIDGE_J:
            out.append(("bridge", band(j, RH, RI), 0.0, CEIL, 150, "FLOOR0_1", "CEIL3_5"))
        else:
            out.append(("void_%d" % j, band(j, RH, RI), VOID_FLOOR, CEIL, 90, "FLOOR0_1", "CEIL3_5"))
    hub = [pt(RH, centre(j) - STEP / 2) for j in range(N)]
    out.append(("platform", hub, 0.0, CEIL, 160, "FLOOR0_1", "CEIL3_5"))
    # the dock hatch (right): the vestibule behind the outer wall
    out.append(("dk_a", band(DOCK_J, RO, 12.0), 0.0, 3.5, 140, "FLOOR0_1", "CEIL3_5"))
    out.append(("dk_b", band(DOCK_J, 12.0, 13.5), 0.0, 3.0, 130, "FLOOR0_1", "CEIL3_5"))
    # round 2: the dock hatch opens on a lit passage (the painting's right-hand corridor): a narrower, lower piece 3 m deep past the hatch, its far end the lit doorway decal
    out.append(("dk_c", [pt(13.5, centre(DOCK_J) - STEP / 2), pt(16.5, centre(DOCK_J) - 7.0), pt(16.5, centre(DOCK_J) + 7.0), pt(13.5, centre(DOCK_J) + STEP / 2)], 0.0, 2.6, 120, "FLOOR0_1", "CEIL3_5"))
    # the underworld hatch (ahead): a stair of 0.375 m risers, the landing and the hatch
    out.append(("uw_s1", band(UW_J, RO, 10.25), 0.375, 5.0, 150, "STEP1", "CEIL3_5"))
    out.append(("uw_s2", band(UW_J, 10.25, 11.0), 0.75, 5.0, 150, "STEP1", "CEIL3_5"))
    out.append(("uw_land", band(UW_J, 11.0, 12.5), 1.125, 5.0, 160, "FLOOR0_1", "CEIL3_5"))
    out.append(("uw_hatch", band(UW_J, 12.5, 14.0), 1.125, 4.0, 140, "FLOOR0_1", "CEIL3_5"))
    return out


# railings: (a, b) sector names; every pair that meets across the void's rim or the platform / bridge edges
def rails(names):
    pairs = []
    for j in range(N):
        if j != BRIDGE_J and j != OPEN_WEDGE:
            pairs.append(("ring_%d" % j, "void_%d" % j))
    for j in range(N):
        if j != BRIDGE_J:
            pairs.append(("platform", "void_%d" % j))
    for j in (1, N - 1):  # the bridge's sides
        pairs.append(("bridge", "void_%d" % j))
    return pairs


START = (-3.0, 7.0)


def main():
    secs = sectors()
    names = [s[0] for s in secs]
    for nm, poly, *_r in secs:
        if area(poly) < 0:
            raise SystemExit("sector %s is clockwise" % nm)
        if not convex(poly):
            raise SystemExit("sector %s is not convex after snapping: %s" % (nm, poly))
    rings, V, L, SD, SEC = {}, [], [], [], []

    def u(v):
        return int(round(v * U))

    for nm, poly, fl, ce, li, ft, ct in secs:
        rings[nm] = [(u(x), u(y)) for x, y in poly]
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
    rail_pairs = {frozenset((names.index(a), names.index(b))) for a, b in rails(names)}
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
        "name": "MAP11",
        "title": "Circle of Death (the Mothership invented from the painting: ring walk, void, platform on a bridge, two hatches)",
        "approximate": True,
        "uncertain": [
            "INVENTED FROM THE PAINTING (tools/doom/trace/mothership_scene.py), not read from the render or the WAD (the supplied WAD has empty map lumps; the render of MAP11 gives only the macro footprint, see tools/doom/trace/mothership.json).",
            "Every size, height and place is a guess from the painting: a 3.5 m wide ring walk of 6 to 9.5 m radius round a circular void 6 m in radius, a 3 m radius platform in the void on a tapering bridge, the dock hatch in the outer wall on the right, the stair and hatch ahead.",
            "The painting's pedestal in the void and the free standing arches are not modelled as geometry (the armillary and the ribs are billboards).",
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
