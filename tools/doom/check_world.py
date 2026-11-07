"""Validate a converted Doom map (a StoryMap JSON written by convert.py).

  python tools/doom/check_world.py content/story/maps/doom_warehouse.json [...]      (exit 1 on any error)
  python tools/doom/check_world.py --all                                             (all eight scenes of scenes.json)

Errors: non-convex / degenerate / clockwise polygon, repeated points, ceiling not above floor, duplicate ids, an edge used by more than
two pieces, a shared edge whose two pieces do not run it in opposite directions, a shared edge without a portal (it would draw a wall
through the room), a portal that is not a whole edge shared by exactly two pieces with equal endpoints, a T-junction crack (a vertex
on the interior of another piece's edge), crossing edges, a piece not reachable from the start through unblocked portals, a start
waypoint outside its piece. Warnings and report: low clearance, steps and drops above 0.6 m, pieces not reachable on foot (step up
limit 0.75 m, the Doom player's 24 units).
Standard library only.
"""
import json
import os
import sys
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
STEP_REPORT_M = 0.6
STEP_CLIMB_M = 0.75
MIN_CLEARANCE_M = 1.6
EPS = 1e-6


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _area(p):
    return sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))) / 2.0


def _seg_cross(a, b, c, d):
    """Proper crossing (interiors cross at a point that is on neither endpoint set)."""
    d1, d2, d3, d4 = _cross(a, b, c), _cross(a, b, d), _cross(c, d, a), _cross(c, d, b)
    return ((d1 > EPS and d2 < -EPS) or (d1 < -EPS and d2 > EPS)) and ((d3 > EPS and d4 < -EPS) or (d3 < -EPS and d4 > EPS))


def _on_open_segment(p, a, b):
    if abs(_cross(a, b, p)) > 1e-7:
        return False
    L2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
    t = ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / L2
    return 1e-9 < t < 1 - 1e-9


def _key(a, b):
    return (a, b) if a <= b else (b, a)


def check(d, quiet=False):
    """Returns (errors, warnings, report dict)."""
    errors, warnings = [], []
    secs = d.get("sectors", [])
    by_id = {}
    for s in secs:
        if s["id"] in by_id:
            errors.append("duplicate sector id %s" % s["id"])
        by_id[s["id"]] = s
    polys = {}
    for s in secs:
        p = [tuple(map(float, q)) for q in s["polygon"]]
        polys[s["id"]] = p
        n = len(p)
        if n < 3:
            errors.append("%s: fewer than 3 points" % s["id"])
            continue
        if len(set(p)) != n:
            errors.append("%s: repeated point" % s["id"])
            continue
        if _area(p) < 0.01:
            errors.append("%s: %s" % (s["id"], "clockwise polygon" if _area(p) < -0.01 else "degenerate (no area)"))
            continue
        for i in range(n):
            if _cross(p[i], p[(i + 1) % n], p[(i + 2) % n]) < -EPS:
                errors.append("%s: not convex" % s["id"])
                break
        if float(s["ceiling"]) <= float(s["floor"]) + 1e-3:
            errors.append("%s: ceiling %.3f not above floor %.3f" % (s["id"], s["ceiling"], s["floor"]))
        elif float(s["ceiling"]) - float(s["floor"]) < MIN_CLEARANCE_M:
            warnings.append("%s: clearance %.2f m is below the eye height line of %.1f m" % (s["id"], s["ceiling"] - s["floor"], MIN_CLEARANCE_M))
    # --- edge ownership ---------------------------------------------------------------------------------------------------------------
    owners = {}
    for sid, p in polys.items():
        n = len(p)
        for i in range(n):
            owners.setdefault(_key(p[i], p[(i + 1) % n]), []).append((sid, p[i], p[(i + 1) % n]))
    portal_edges = {}
    for w in d.get("walls", []):
        if not w.get("portal"):
            continue
        a, b = tuple(map(float, w["from"])), tuple(map(float, w["to"]))
        k = _key(a, b)
        pa, pb = w["sector"], w["portal"]
        ow = owners.get(k, [])
        if pa not in polys or pb not in polys:
            errors.append("portal %s-%s names an unknown sector" % (pa, pb))
            continue
        if sorted(o[0] for o in ow) != sorted([pa, pb]):
            errors.append("portal %s-%s %s: not a whole edge shared by exactly those two pieces (owners %s)" % (pa, pb, k, [o[0] for o in ow]))
            continue
        if k in portal_edges:
            errors.append("portal edge %s declared twice" % (k,))
        portal_edges[k] = w
    shared = 0
    for k, ow in owners.items():
        if len(ow) > 2:
            errors.append("edge %s used by %d pieces: %s" % (k, len(ow), [o[0] for o in ow]))
        elif len(ow) == 2:
            shared += 1
            if ow[0][1] == ow[1][1]:
                errors.append("edge %s runs the same direction in %s and %s (inconsistent winding)" % (k, ow[0][0], ow[1][0]))
            if k not in portal_edges:
                errors.append("edge %s shared by %s and %s has no portal (it would be drawn as a wall)" % (k, ow[0][0], ow[1][0]))
    # --- cracks (a vertex on the interior of another edge) and crossing edges, on a grid -----------------------------------------------
    cell = 4.0
    grid = {}
    verts = set(v for p in polys.values() for v in p)
    for v in verts:
        grid.setdefault((int(v[0] // cell), int(v[1] // cell)), []).append(v)
    seg_grid = {}
    segs = list(owners.keys())
    for si, (a, b) in enumerate(segs):
        for cx in range(int(min(a[0], b[0]) // cell), int(max(a[0], b[0]) // cell) + 1):
            for cz in range(int(min(a[1], b[1]) // cell), int(max(a[1], b[1]) // cell) + 1):
                seg_grid.setdefault((cx, cz), []).append(si)
        for cx in range(int(min(a[0], b[0]) // cell) - 0, int(max(a[0], b[0]) // cell) + 1):
            for cz in range(int(min(a[1], b[1]) // cell), int(max(a[1], b[1]) // cell) + 1):
                for v in grid.get((cx, cz), []):
                    if v != a and v != b and _on_open_segment(v, a, b):
                        errors.append("crack: vertex %s lies on the interior of edge %s-%s" % (v, a, b))
    seen_pairs = set()
    crossing = 0
    for cellsegs in seg_grid.values():
        for i in range(len(cellsegs)):
            for j in range(i + 1, len(cellsegs)):
                pr = (cellsegs[i], cellsegs[j])
                if pr in seen_pairs:
                    continue
                seen_pairs.add(pr)
                if _seg_cross(*segs[pr[0]], *segs[pr[1]]):
                    crossing += 1
                    if crossing <= 20:
                        errors.append("edges %s and %s cross" % (segs[pr[0]], segs[pr[1]]))
    # --- connectivity ----------------------------------------------------------------------------------------------------------------
    adj, foot = {sid: set() for sid in polys}, {sid: set() for sid in polys}
    steps, drops = [], []
    for k, w in portal_edges.items():
        a, b = w["sector"], w["portal"]
        if not w.get("blocked"):
            adj[a].add(b)
            adj[b].add(a)
        fa, fb = float(by_id[a]["floor"]), float(by_id[b]["floor"])
        dz = fb - fa
        if abs(dz) > STEP_REPORT_M:
            rec = {"from": a, "to": b, "dz": round(dz, 3), "edge": [list(k[0]), list(k[1])]}
            (steps if abs(dz) <= STEP_CLIMB_M else drops).append(rec)
        if not w.get("blocked"):
            if dz <= STEP_CLIMB_M:
                foot[a].add(b)
            if -dz <= STEP_CLIMB_M:
                foot[b].add(a)
    wp = {x["id"]: x for x in d.get("waypoints", [])}
    start = wp.get(d.get("start", ""))
    unreachable, off_foot = [], []
    if start is None:
        errors.append("start waypoint %s is not a waypoint" % d.get("start"))
    else:
        sp = polys.get(start["sector"])
        if sp is None:
            errors.append("start sector %s is unknown" % start["sector"])
        else:
            q = tuple(start["at"])
            inside = all(_cross(sp[i], sp[(i + 1) % len(sp)], q) >= 0.3 * (((sp[(i + 1) % len(sp)][0] - sp[i][0]) ** 2 + (sp[(i + 1) % len(sp)][1] - sp[i][1]) ** 2) ** 0.5) - 1e-6 for i in range(len(sp)))
            if not inside:
                errors.append("start waypoint is not inside %s with a 0.3 m margin" % start["sector"])
            for name, graph, out in (("portals", adj, unreachable), ("foot", foot, off_foot)):
                seen = {start["sector"]}
                dq = deque([start["sector"]])
                while dq:
                    c = dq.popleft()
                    for n in graph[c]:
                        if n not in seen:
                            seen.add(n)
                            dq.append(n)
                out.extend(sorted(set(polys) - seen))
            if unreachable:
                errors.append("%d piece(s) not reachable from the start through unblocked portals: %s" % (len(unreachable), unreachable[:8]))
            if off_foot:
                warnings.append("%d piece(s) not reachable on foot (steps up of at most %.2f m): %s" % (len(off_foot), STEP_CLIMB_M, off_foot[:8]))
    report = {"pieces": len(polys), "portals": len(portal_edges), "blocked_portals": sum(1 for w in portal_edges.values() if w.get("blocked")),
              "steps_over_0_6m": len(steps), "drops_or_ledges": len(drops), "max_dz": round(max([abs(x["dz"]) for x in steps + drops] or [0]), 3),
              "unreachable": len(unreachable), "unreachable_on_foot": len(off_foot), "steps": steps[:50], "drops": drops[:50]}
    return errors, warnings, report


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    paths = []
    if "--all" in argv:
        with open(os.path.join(HERE, "scenes.json"), encoding="utf-8") as f:
            paths = [os.path.join(ROOT, e["output"]) for e in json.load(f).values()]
        argv.remove("--all")
    paths += argv
    if not paths:
        print(__doc__)
        return 2
    bad = 0
    for p in paths:
        if not os.path.exists(p):
            print("%s: MISSING" % p)
            bad += 1
            continue
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        errors, warnings, rep = check(d)
        print("%s: %d pieces, %d portals (%d blocked), %d steps >0.6 m, %d drops/ledges >0.75 m (max %.2f m), %d unreachable, %d off foot -> %s" % (
            os.path.basename(p), rep["pieces"], rep["portals"], rep["blocked_portals"], rep["steps_over_0_6m"], rep["drops_or_ledges"], rep["max_dz"],
            rep["unreachable"], rep["unreachable_on_foot"], "OK" if not errors else "%d ERROR(S)" % len(errors)))
        for e in errors[:40]:
            print("  ERROR", e)
        if len(errors) > 40:
            print("  ... %d more errors" % (len(errors) - 40))
        for w in warnings[:10]:
            print("  warning", w)
        if len(warnings) > 10:
            print("  ... %d more warnings" % (len(warnings) - 10))
        bad += len(errors)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
