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


def build(name, title, sectors, uncertain, things):
    # normalise orientation: first ring outer ccw, the rest holes cw
    norm = []
    for s in sectors:
        rings = []
        for i, r in enumerate(s["rings"]):
            r = [tuple(p) for p in r]
            if (area2(r) > 0) != (i == 0):
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
         "vertices": [list(v) for v in verts], "linedefs": lines, "sidedefs": sides,
         "sectors": [{"floor": s["floor"], "ceiling": s["ceiling"], "light": s["light"], "special": 0, "tag": 0,
                      "floor_tex": s["floor_tex"], "ceil_tex": s["ceil_tex"]} for s, _ in norm],
         "sector_names": [s["id"] for s, _ in norm], "things": things}
    return d


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def oct_(apothem, side_half):
    a, b = apothem, side_half
    return [(a, -b), (a, b), (b, a), (-b, a), (-a, b), (-a, -b), (-b, -a), (b, -a)]


def warehouse():
    S = []
    notch = [(-500, -700), (500, -700), (500, -500), (700, -500), (700, 500), (500, 500), (500, 700), (-500, 700), (-500, 500), (-700, 500), (-700, -500), (-500, -500)]
    plus = [(-100, -380), (100, -380), (100, -300), (300, -300), (300, -100), (380, -100), (380, 100), (300, 100), (300, 300), (100, 300), (100, 380),
            (-100, 380), (-100, 300), (-300, 300), (-300, 100), (-380, 100), (-380, -100), (-300, -100), (-300, -300), (-100, -300)]
    S.append(sector("arena_floor", [notch, plus], 0, 256, 190))
    S.append(sector("platform", [rect(-300, -300, 300, 300)], 64, 256, 255, "FLOOR0_1"))
    for k in range(4):
        r1 = [rot(p, k) for p in rect(-100, -340, 100, -300)]
        r2 = [rot(p, k) for p in rect(-100, -380, 100, -340)]
        S.append(sector("step_a%d" % k, [r1], 48, 256, 220, "STEP1"))
        S.append(sector("step_b%d" % k, [r2], 24, 256, 210, "STEP1"))
    for k in range(4):
        S.append(sector("alcove%d" % k, [[rot(p, k) for p in rect(500, 500, 700, 700)]], 24, 192, 110, "FLOOR5_1"))
    S.append(sector("exit_corridor", [rect(-64, 700, 64, 900)], 0, 128, 140, "FLOOR4_8"))
    S.append(sector("exit_room", [rect(-200, 900, 200, 1100)], 0, 160, 120, "FLOOR5_1"))
    return build("MAP07", "Dead Simple (approximate trace)", S, [
        "The whole footprint is an estimate from knowledge of the level, not read from the WAD or measured on the render.",
        "Arena about 1400 units across, estimated; the real map's proportions, outer rim and ceiling heights may differ.",
        "Central platform size (600) and its four stair arms (two 16 or 24 unit risers) are guesses; the real raised areas may be platforms for the mancubi rather than one square.",
        "Four corner alcoves (200 x 200, floor +24, lower ceiling) are a guess at the corner recesses.",
        "The exit corridor and room on the north side are placeholders so the map has a way out; the real exits differ.",
        "Floors, ceilings and light values are invented in the Doom style; heights are relative only."],
        [{"x": 0, "y": -560, "angle": 90, "type": 1, "flags": 7}])


def mothership():
    S = []
    outer = oct_(640, 265)
    inner = oct_(440, 182)
    S.append(sector("walkway", [outer, inner], 0, 320, 170, "FLOOR0_1"))
    S.append(sector("pit_north", [[(-440, 48), (440, 48), (440, 182), (182, 440), (-182, 440), (-440, 182)]], -256, 512, 80, "LAVA1"))
    S.append(sector("pit_south", [[(-440, -182), (-182, -440), (182, -440), (440, -182), (440, -48), (-440, -48)]], -256, 512, 80, "LAVA1"))
    S.append(sector("bridge", [rect(-440, -48, 440, 48)], 0, 320, 200, "FLOOR3_3"))
    S.append(sector("room_east", [rect(640, -200, 1000, 200)], 0, 160, 130))
    S.append(sector("room_east_step1", [rect(1000, -200, 1080, 200)], 20, 160, 140, "STEP1"))
    S.append(sector("room_east_dais", [rect(1080, -200, 1280, 200)], 40, 160, 160, "FLOOR5_1"))
    S.append(sector("room_west", [rect(-1000, -200, -640, 200)], 0, 160, 110))
    S.append(sector("room_north", [rect(-150, 640, 150, 900)], 0, 160, 100))
    S.append(sector("room_south", [rect(-150, -900, 150, -640)], 0, 160, 100))
    return build("MAP11", "Circle of Death (approximate trace)", S, [
        "Footprint is an estimate from knowledge of the level, not read from the WAD or measured on the render.",
        "Whether the real ring is an octagon, a circle or a many-sided polygon, and its true radius, are unknown: an octagon of 1280 units across is assumed.",
        "Walkway width (about 200 units), pit depth (-256) and the central bridge (96 wide, one only) are guesses; the real pit may have several bridges or platforms.",
        "The four side rooms and the east dais steps are placeholders for the side rooms the brief names; their count, size and positions are unknown.",
        "Ceiling heights are invented; the pit sector is given a taller ceiling than the walkway so the void reads as open."],
        [{"x": 0, "y": -540, "angle": 90, "type": 1, "flags": 7}])


def lounge():
    S = []
    hub = oct_(256, 106)
    S.append(sector("hub", [hub, rect(-64, -64, 64, 64)], 0, 192, 190, "FLOOR4_8"))
    S.append(sector("hub_dais", [rect(-64, -64, 64, 64)], 16, 192, 230, "FLOOR0_1"))
    for k in range(4):
        S.append(sector("room_axis%d" % k, [[rot(p, k) for p in [(-80, 256), (80, 256), (80, 500), (-80, 500)]]], 6 * k, 128 + 16 * (k % 2), 120 + 10 * k, "FLOOR5_1"))
        S.append(sector("room_diag%d" % k, [[rot(p, k) for p in [(156, 206), (206, 156), (356, 306), (306, 356)]]], 6 * k + 4, 128, 110 + 10 * k, "FLOOR5_1"))
    return build("MAP08", "Tricks and Traps (approximate trace)", S, [
        "Footprint is an estimate from knowledge of the level, not read from the WAD or measured on the render.",
        "An octagonal central hub (512 across) with eight doors is taken from the brief; the real map's hub size, door positions and the traps are unknown.",
        "The eight rooms are identical closets of invented size and heights; the real rooms are different shapes and connect to each other and to further areas.",
        "The central dais is invented."],
        [{"x": 0, "y": -180, "angle": 90, "type": 1, "flags": 7}])


def main():
    for scene, fn in (("warehouse", warehouse), ("mothership", mothership), ("lounge", lounge)):
        d = fn()
        with open(os.path.join(HERE, scene + ".json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(d, f, indent=0, separators=(",", ":"))
            f.write("\n")
        print(scene, len(d["vertices"]), "vertices", len(d["linedefs"]), "linedefs", len(d["sectors"]), "sectors")


if __name__ == "__main__":
    main()
