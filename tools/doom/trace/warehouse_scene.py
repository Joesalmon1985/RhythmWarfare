"""The Warehouse pilot's additions to the render trace of MAP07 (docs/doom/scenes/warehouse.md): reads tools/doom/trace/warehouse.json (traced from the render by
render_trace.py) and writes tools/doom/trace/warehouse_pilot.json, which convert.py takes as the scene's trace.

    python -I tools/doom/trace/warehouse_scene.py
    python -I tools/doom/convert.py --scene warehouse --trace tools/doom/trace/warehouse_pilot.json

All in Doom units (y up). What it does to the render's trace (nothing else changes):
  * the inner courtyard (the dance floor) is lowered from +32 to +16 so its ledge over the stone ring is a 0.5 m step, and its four edges become a FENCE (impassable lines,
    Doom's flag 1) with two gates (south and west), the way into the floor;
  * four small stairs of two risers climb the central pedestal's south side (the pedestal is the lit cube; heights 16 -> 28 -> 40 -> 64);
  * three islands stand in the stone ring, each a hole of the ring: the BAR (west band, floor +24, low canopy), the LOUNGE (south band, +12, low canopy) and the STAGE
    (north-east corner of the ring, +60) with two steps on its south side. They hold the three guides; none touches the ring's outer edge;
  * the edge splitting that gates and stairs need is done here (a linedef is cut where a new vertex lies on it).
The islands, the gates, the stairs and the lowered courtyard are INVENTIONS read from the concept image, not from the render or the WAD: they are added to `uncertain`.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "warehouse.json")
OUT = os.path.join(HERE, "warehouse_pilot.json")


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# name, ring (counter-clockwise), floor, ceiling, light, floor_tex, ceil_tex, parent sector name
ISLANDS = [
    ("bar", rect(-740, -400, -570, -200), 24, 128, 150, "FLOOR5_1", "CEIL3_5", "stone_ring"),
    ("lounge", rect(-540, -740, -400, -570), 12, 128, 140, "FLOOR5_1", "CEIL3_5", "stone_ring"),
    ("stage_step_a", rect(610, 562, 710, 586), 20, 320, 200, "STEP1", "CEIL3_5", "stone_ring"),
    ("stage_step_b", rect(610, 586, 710, 610), 40, 320, 215, "STEP1", "CEIL3_5", "stone_ring"),
    ("stage", rect(580, 610, 740, 740), 60, 320, 240, "FLOOR0_1", "CEIL3_5", "stone_ring"),
    ("ped_step_a", rect(30, -107, 110, -83), 28, 320, 230, "STEP1", "CEIL3_5", "courtyard"),
    ("ped_step_b", rect(30, -83, 110, -59), 40, 320, 240, "STEP1", "CEIL3_5", "courtyard"),
]
GATES = [((-400, -517), (-320, -517)), ((-517, -120), (-517, -40))]  # on the courtyard's south and west edges


def main():
    t = json.load(open(SRC, encoding="utf-8"))
    names = t["sector_names"]
    V = [tuple(v) for v in t["vertices"]]
    L, SD, SEC = t["linedefs"], t["sidedefs"], t["sectors"]
    court, ring = names.index("courtyard"), names.index("stone_ring")
    SEC[court]["floor"] = 16

    def vid(p):
        if p not in V:
            V.append(p)
        return V.index(p)

    def sidedef(sec):
        SD.append({"xoff": 0, "yoff": 0, "upper": "-", "lower": "-", "middle": "STARTAN3", "sector": sec})
        return len(SD) - 1

    def split_at(p):
        """Cut the linedef that has the point strictly inside it (vertex p is added)."""
        if p in V:
            for ld in L:
                if V[ld["v1"]] == p or V[ld["v2"]] == p:
                    return  # already a vertex of a line there
        for ld in L:
            a, b = V[ld["v1"]], V[ld["v2"]]
            if (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) == 0:
                tt = (p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])
                if 0 < tt < (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2:
                    w = vid(p)
                    new = dict(ld)
                    new["v1"], new["v2"] = w, ld["v2"]
                    for k in ("right", "left"):
                        if ld[k] >= 0:
                            new[k] = len(SD)
                            SD.append(dict(SD[ld[k]]))
                    ld["v2"] = w
                    L.append(new)
                    return
        raise SystemExit("no linedef passes through %s" % (p,))

    # gates: cut the courtyard edges at the gate's ends
    for g in GATES:
        for p in g:
            split_at(p)
    # islands: split the lines they touch (pedestal steps share a stretch of the pedestal's edge), then add them
    sec_index = {}
    for name, rg, fl, ce, li, ft, ct, parent in ISLANDS:
        sec_index[name] = len(SEC)
        SEC.append({"floor": fl, "ceiling": ce, "light": li, "special": 0, "tag": 0, "floor_tex": ft, "ceil_tex": ct})
        names.append(name)
    allv = {p for _, rg, *_ in ISLANDS for p in rg}
    for p in sorted(allv):
        try:
            split_at(p)
        except SystemExit:
            pass  # not on an existing line: it is a free vertex of an island
    def refine(rg):  # insert the other islands' vertices that lie on this ring's edges (no T-junction cracks)
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
    for name, rg, *_ in ISLANDS:
        rg = refine(rg)
        for i in range(len(rg)):
            edges[(rg[i], rg[(i + 1) % len(rg)])] = name
    done = set()
    for (a, b), name in sorted(edges.items()):
        if (a, b) in done:
            continue
        other = edges.get((b, a))
        parent = next(i for i in ISLANDS if i[0] == name)[7]
        if other is not None:  # between two islands
            done.add((b, a))
            L.append({"v1": vid(a), "v2": vid(b), "flags": 4, "special": 0, "tag": 0, "right": sidedef(sec_index[other]), "left": sidedef(sec_index[name])})
        else:
            existing = [ld for ld in L if {V[ld["v1"]], V[ld["v2"]]} == {a, b}]
            if existing:  # an island edge on the pedestal's edge: the line already has the pedestal and the courtyard; replace the courtyard side by the island
                ld = existing[0]
                # the pedestal is on one side, the courtyard on the other: the island takes the courtyard's place along this stretch
                for k in ("right", "left"):
                    if SD[ld[k]]["sector"] == court:
                        SD[ld[k]]["sector"] = sec_index[name]
                continue
            L.append({"v1": vid(a), "v2": vid(b), "flags": 4, "special": 0, "tag": 0, "right": sidedef(names.index(parent)), "left": sidedef(sec_index[name])})
        done.add((a, b))
    # the fence: lines between the courtyard and the stone ring, except the gates
    gate_set = {frozenset(g) for g in GATES}
    for ld in L:
        if ld["left"] < 0 or ld["right"] < 0:
            continue
        s = {SD[ld["left"]]["sector"], SD[ld["right"]]["sector"]}
        if s == {court, ring} and frozenset((V[ld["v1"]], V[ld["v2"]])) not in gate_set:
            ld["flags"] = 5
    t["vertices"] = [list(v) for v in V]
    t["name"] = "MAP07"
    t["title"] = "Dead Simple (render trace plus the pilot's stage, bar, lounge, fence and stairs)"
    t["uncertain"] = list(t["uncertain"]) + [
        "PILOT ADDITIONS (tools/doom/trace/warehouse_scene.py), read from the concept image, not from the render or the WAD: the courtyard (the dance floor) is lowered from +32 to +16 so its ledge is a 0.5 m step; its four edges are a fence (impassable) with two gates (south and west).",
        "PILOT ADDITIONS: three islands stand in the stone ring: the bar (west band, +24, 4 m canopy), the lounge (south band, +12, canopy) and the stage (north-east corner, +60, two steps on its south side). Their sizes and places are inventions.",
        "PILOT ADDITIONS: two stair strips climb the central pedestal's south side (16 -> 28 -> 40 -> 64), so the lit cube can be stood on.",
        "NOT connected: the terrace (+96, 3 m above the ring) and the north-west nub have no stairs to the ring (the render draws ramps, untraced): the scene's arrival is on the ring, not in the nub.",
    ]
    json.dump(t, open(OUT, "w", encoding="utf-8", newline="\n"), indent=0, separators=(",", ":"))
    open(OUT, "a", encoding="utf-8", newline="\n").write("\n")
    print("wrote %s: %d sectors, %d linedefs" % (OUT, len(SEC), len(L)))


if __name__ == "__main__":
    main()
