"""The Warehouse pilot's additions to the render trace of MAP07 (docs/doom/scenes/warehouse.md): reads tools/doom/trace/warehouse.json (traced from the render by
render_trace.py) and writes tools/doom/trace/warehouse_pilot.json, which convert.py takes as the scene's trace.

    python -I tools/doom/trace/warehouse_scene.py
    python -I tools/doom/convert.py --scene warehouse --trace tools/doom/trace/warehouse_pilot.json

All in Doom units (y up). What it does to the render's trace (nothing else changes):
  * the inner courtyard keeps the render's guessed +32: its ledge over the ring is a 1 m solid wall all round (the railing wall; impassable lines), with two GATES, each a 0.5 m step island;
  * two stair strips climb the central pedestal's south side (the pedestal is the lit cube; 16 -> 28 -> 40 -> 64);
  * the STAGE: a platform island in the courtyard (+68) with two steps on its east side, about 16 m from the reference viewpoint;
  * the BAR and the LOUNGE: rooms cut out of the stone ring, each with three solid walls (8 units thick, void between the room and the ring) and a 5 m opening towards the
    reference viewpoint, floor +24 / +12, 4 m ceiling.
  * the edge splitting that gates, stairs and rooms need is done here (a linedef is cut where a new vertex lies on it).
All of it is INVENTED from the concept image, not read from the render or the WAD: it is added to `uncertain`.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "warehouse.json")
OUT = os.path.join(HERE, "warehouse_pilot.json")


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# name, ring (counter-clockwise), floor, ceiling, light, floor_tex, ceil_tex, parent sector name, options: hole (the parent's cut-out, counter-clockwise, rooms only)
ISLANDS = [
    ("bar", rect(-740, -400, -570, -200), 24, 128, 150, "FLOOR5_1", "CEIL3_5", "stone_ring", {"hole": rect(-748, -400, -562, -192), "room": True}),
    ("lounge", rect(-540, -740, -400, -570), 12, 128, 140, "FLOOR5_1", "CEIL3_5", "stone_ring", {"hole": rect(-540, -748, -392, -562), "room": True}),
    ("stage_step_a", rect(-146, -180, -122, -120), 44, 320, 200, "STEP1", "CEIL3_5", "courtyard", {}),
    ("stage_step_b", rect(-170, -180, -146, -120), 56, 320, 215, "STEP1", "CEIL3_5", "courtyard", {}),
    ("stage", rect(-330, -205, -170, -85), 68, 320, 240, "FLOOR0_1", "CEIL3_5", "courtyard", {}),
    ("ped_step_a", rect(30, -107, 110, -83), 40, 320, 230, "STEP1", "CEIL3_5", "courtyard", {}),
    ("ped_step_b", rect(30, -83, 110, -59), 52, 320, 240, "STEP1", "CEIL3_5", "courtyard", {}),
]
# the gates: a 0.5 m step in front of each of the two openings in the courtyard's 1 m ledge (south x -400..-320, west y -120..-40); the rest of the ledge is the railing wall
ISLANDS.append(("gate_step_s", rect(-400, -541, -320, -517), 16, 320, 190, "STEP1", "CEIL3_5", "stone_ring", {}))
ISLANDS.append(("gate_step_w", rect(-541, -120, -517, -40), 16, 320, 190, "STEP1", "CEIL3_5", "stone_ring", {}))
GATES = [((-400, -517), (-320, -517)), ((-517, -120), (-517, -40))]  # on the courtyard's south and west edges (the railing leaves them open)


def main():
    t = json.load(open(SRC, encoding="utf-8"))
    names = t["sector_names"]
    V = [tuple(v) for v in t["vertices"]]
    L, SD, SEC = t["linedefs"], t["sidedefs"], t["sectors"]
    court = names.index("courtyard")
    ring_i = names.index("stone_ring")

    def vid(p):
        if p not in V:
            V.append(p)
        return V.index(p)

    def sidedef(sec):
        SD.append({"xoff": 0, "yoff": 0, "upper": "-", "lower": "-", "middle": "STARTAN3", "sector": sec})
        return len(SD) - 1

    def split_at(p):
        """Cut the linedef that has the point strictly inside it (vertex p is added); nothing when none does."""
        for ld in L:
            a, b = V[ld["v1"]], V[ld["v2"]]
            if p in (a, b):
                return
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

    isl = list(ISLANDS)
    idx = {}
    for name, rg, fl, ce, li, ft, ct, parent, opt in isl:
        idx[name] = len(SEC)
        SEC.append({"floor": fl, "ceiling": ce, "light": li, "special": 0, "tag": 0, "floor_tex": ft, "ceil_tex": ct})
        names.append(name)
    allv = set()
    for name, rg, fl, ce, li, ft, ct, parent, opt in isl:
        allv.update(rg)
        allv.update(opt.get("hole", []))
    for g in GATES:
        allv.update(g)
    for p in sorted(allv):
        split_at(p)

    def refine(rg):  # insert every other authored vertex that lies on this ring's edges (no T-junction cracks)
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

    edges, wall_keys, wall_owner = {}, set(), set()
    for name, rg, fl, ce, li, ft, ct, parent, opt in isl:
        r = refine(rg)
        for i in range(len(r)):
            edges[(r[i], r[(i + 1) % len(r)])] = idx[name]
        if opt.get("room"):
            wall_owner.add(idx[name])
        if "hole" in opt:  # the parent's cut-out: its edges run the other way round (the parent on their left)
            h = refine(opt["hole"])
            for i in range(len(h)):
                a, b = h[i], h[(i + 1) % len(h)]
                edges[(b, a)] = names.index(parent)
                wall_keys.add((b, a))
    done = set()
    for (a, b), owner in sorted(edges.items(), key=lambda kv: (kv[0], kv[1])):
        if (a, b) in done:
            continue
        other = edges.get((b, a))
        if other is not None:
            done.update([(a, b), (b, a)])
            L.append({"v1": vid(a), "v2": vid(b), "flags": 4, "special": 0, "tag": 0, "right": sidedef(other), "left": sidedef(owner)})
            continue
        done.add((a, b))
        if owner in wall_owner or (a, b) in wall_keys:  # a wall: one-sided, the sector on the right of b -> a
            L.append({"v1": vid(b), "v2": vid(a), "flags": 1, "special": 0, "tag": 0, "right": sidedef(owner), "left": -1})
            continue
        parent = next(i for i in isl if idx[i[0]] == owner)[7]
        pi = names.index(parent)
        existing = [ld for ld in L if {V[ld["v1"]], V[ld["v2"]]} == {a, b}]
        if existing:  # the edge lies on an existing line (the pedestal's, the courtyard's): the island takes the parent's side along it
            for k in ("right", "left"):
                if existing[0][k] >= 0 and SD[existing[0][k]]["sector"] == pi:
                    SD[existing[0][k]]["sector"] = owner
            continue
        L.append({"v1": vid(a), "v2": vid(b), "flags": 4, "special": 0, "tag": 0, "right": sidedef(pi), "left": sidedef(owner)})
    for ld in L:  # the 1 m ledge is a railing: impassable everywhere between the ring and the courtyard (the gates now border the steps, not the ring)
        if ld["left"] >= 0 and ld["right"] >= 0 and {SD[ld["left"]]["sector"], SD[ld["right"]]["sector"]} == {court, ring_i}:
            ld["flags"] = 5
    t["vertices"] = [list(v) for v in V]
    t["name"] = "MAP07"
    t["title"] = "Dead Simple (render trace plus the pilot's stage, bar, lounge, railing and stairs)"
    t["uncertain"] = list(t["uncertain"]) + [
        "PILOT ADDITIONS (tools/doom/trace/warehouse_scene.py), read from the concept image, not from the render or the WAD: the courtyard ledge (+32, the render's guess) is the 1 m railing wall, impassable all round, with two gates (south, west) each a 0.5 m step island.",
        "PILOT ADDITIONS: the stage (a +68 platform in the courtyard with two steps, 16 m from the reference viewpoint, so its guide reads), the bar (west band) and the lounge (south band) as walled rooms cut out of the stone ring with an opening towards the reference viewpoint. Sizes and places are inventions.",
        "PILOT ADDITIONS: two stair strips climb the central pedestal's south side (32 -> 40 -> 52 -> 64), so the lit cube can be stood on.",
        "NOT connected: the terrace (+96, 3 m above the ring) and the north-west nub have no stairs to the ring (the render draws ramps, untraced): the scene's arrival is on the ring, not in the nub.",
    ]
    json.dump(t, open(OUT, "w", encoding="utf-8", newline="\n"), indent=0, separators=(",", ":"))
    open(OUT, "a", encoding="utf-8", newline="\n").write("\n")
    print("wrote %s: %d sectors, %d linedefs" % (OUT, len(SEC), len(L)))


if __name__ == "__main__":
    main()
