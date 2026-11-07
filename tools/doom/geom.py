"""Exact integer geometry for the conversion: ring building, triangulation with holes, Hertel-Mehlhorn merge.

All coordinates here are raw Doom integers (y up), so cross products are exact and shared edges stay exactly equal.
Polygons are lists of (x, y) tuples, counter-clockwise (positive area) unless stated.
"""
import math


def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def area2(p):
    """Twice the signed area (positive = counter-clockwise)."""
    s = 0
    for i in range(len(p)):
        q = p[(i + 1) % len(p)]
        s += p[i][0] * q[1] - q[0] * p[i][1]
    return s


def point_in_poly(pt, poly):
    """Ray test (boundary points give an arbitrary answer; callers use midpoints)."""
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if (a[1] > y) != (b[1] > y):
            xi = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if xi > x:
                inside = not inside
    return inside


def _on_seg(p, a, b):
    return cross(a, b, p) == 0 and min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1])


def segments_cross(a, b, c, d):
    """True when segments ab and cd cross, touch other than at a shared endpoint, or overlap collinearly."""
    if a == c or a == d or b == c or b == d:
        if cross(a, b, c) == 0 and cross(a, b, d) == 0:
            s = (b[0] - a[0], b[1] - a[1])
            t0 = (c[0] - a[0]) * s[0] + (c[1] - a[1]) * s[1]
            t1 = (d[0] - a[0]) * s[0] + (d[1] - a[1]) * s[1]
            length = s[0] * s[0] + s[1] * s[1]
            return min(max(t0, t1), length) - max(min(t0, t1), 0) > 0
        return False
    d1, d2 = cross(a, b, c), cross(a, b, d)
    d3, d4 = cross(c, d, a), cross(c, d, b)
    if d1 != 0 and d2 != 0 and d3 != 0 and d4 != 0 and ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return True
    return _on_seg(c, a, b) or _on_seg(d, a, b) or _on_seg(a, c, d) or _on_seg(b, c, d)


def build_rings(edges):
    """Chain directed edges (interior on the left) into closed rings. edges: list of ((x,y),(x,y)).
    At a vertex with several outgoing edges the sharpest left turn is taken (the face stays on the left).
    Returns (rings, open_chains) where open_chains counts chains that did not close."""
    out = {}
    for a, b in edges:
        out.setdefault(a, []).append(b)
    used = set()
    rings = []
    broken = 0
    for a, b in edges:
        if (a, b) in used:
            continue
        ring = [a]
        cur_a, cur_b = a, b
        guard = 0
        while True:
            used.add((cur_a, cur_b))
            if cur_b == a:
                break
            ring.append(cur_b)
            cands = [c for c in out.get(cur_b, []) if (cur_b, c) not in used]
            if not cands:
                ring = None
                break
            if len(cands) > 1:
                din = math.atan2(cur_b[1] - cur_a[1], cur_b[0] - cur_a[0])

                def turn(c, din=din, cur_b=cur_b):
                    t = math.atan2(c[1] - cur_b[1], c[0] - cur_b[0]) - din
                    while t <= -math.pi:
                        t += 2 * math.pi
                    while t > math.pi:
                        t -= 2 * math.pi
                    return -t  # smaller = more to the left
                cands.sort(key=turn)
            cur_a, cur_b = cur_b, cands[0]
            guard += 1
            if guard > 200000:
                ring = None
                break
        if ring is None:
            broken += 1
        elif len(ring) >= 3:
            rings.append(ring)
    return rings, broken


def split_rings(rings):
    """Group rings into (outer, [holes]) by orientation and containment. Holes stay clockwise."""
    groups = [(r, []) for r in rings if area2(r) > 0]
    for h in [r for r in rings if area2(r) < 0]:
        best = None
        for g in groups:
            if all(v in g[0] or point_in_poly(v, g[0]) for v in h):
                if best is None or abs(area2(g[0])) < abs(area2(best[0])):
                    best = g
        if best is not None:
            best[1].append(h)
    return groups


def _bridge(poly, hole, outer, holes, bridges):
    """Splice `hole` into `poly` (the outer with earlier holes bridged in) along the shortest visible segment."""
    best = None
    obstacles = [outer] + holes
    for hi, h in enumerate(hole):
        for oi, o in enumerate(poly):
            d = (h[0] - o[0]) ** 2 + (h[1] - o[1]) ** 2
            if d == 0 or (best is not None and d >= best[0]):
                continue
            mid = ((h[0] + o[0]) / 2.0, (h[1] + o[1]) / 2.0)
            if not point_in_poly(mid, outer) or any(point_in_poly(mid, hh) for hh in holes):
                continue
            ok = True
            for ring in obstacles:
                n = len(ring)
                if any(segments_cross(h, o, ring[i], ring[(i + 1) % n]) for i in range(n)):
                    ok = False
                    break
            if ok and any(segments_cross(h, o, bq, br) for bq, br in bridges):
                ok = False
            if ok:
                best = (d, oi, hi)
    if best is None:
        return None
    _, oi, hi = best
    return poly[:oi + 1] + hole[hi:] + hole[:hi + 1] + poly[oi:], (hole[hi], poly[oi])


def merge_holes(outer, holes):
    poly = list(outer)
    bridges = []
    for h in sorted(holes, key=lambda h: -max(v[0] for v in h)):
        res = _bridge(poly, h, outer, holes, bridges)
        if res is None:
            return None
        poly, br = res
        bridges.append(br)
    return poly


def _in_tri(p, a, b, c):
    return cross(a, b, p) >= 0 and cross(b, c, p) >= 0 and cross(c, a, p) >= 0


def winding(pt, poly):
    """Winding number of poly around pt (positive for counter-clockwise loops; a pinched polygon's clockwise lobes count negative)."""
    x, y = pt
    w = 0
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if a[1] <= y < b[1] or b[1] <= y < a[1]:
            xi = a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if xi > x:
                w += 1 if b[1] > a[1] else -1
    return w


def _diagonal_ok(pts, i, a, c):
    n = len(pts)
    for k in range(n):
        e1, e2 = pts[k], pts[(k + 1) % n]
        if segments_cross(a, c, e1, e2):
            return False
    mid = ((a[0] + c[0]) / 2.0, (a[1] + c[1]) / 2.0)
    return winding(mid, pts) > 0


def triangulate(poly):
    """Ear clipping of a counter-clockwise (possibly bridged, vertex-duplicating) polygon. Returns triangles or None.
    A colinear vertex is never the tip of an ear, so it stays a vertex and edges are not merged across it.
    When a pinched polygon has no ear left, it is split along an interior diagonal and both halves go on (recursion)."""
    return _tri(list(poly), 0)


def _tri(pts, depth):
    bridged = len(set(pts)) != len(pts)  # a polygon with bridged holes repeats vertices: also test each diagonal against every edge
    tris = []
    while len(pts) > 3:
        n = len(pts)
        clipped = False
        for i in range(n):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
            if cross(a, b, c) <= 0:
                continue
            if any(p != a and p != b and p != c and _in_tri(p, a, b, c) for p in pts):
                continue
            if bridged and not _diagonal_ok(pts, i, a, c):
                continue
            tris.append((a, b, c))
            del pts[i]
            clipped = True
            break
        if clipped:
            continue
        for i in range(n):  # a spike / colinear vertex may be dropped (the area check afterwards still holds)
            if cross(pts[i - 1], pts[i], pts[(i + 1) % n]) == 0:
                del pts[i]
                clipped = True
                break
        if clipped:
            continue
        if depth > 40:
            return None
        for i in range(n):  # no ear: split along an interior diagonal
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                a, c = pts[i], pts[j]
                if a == c:
                    continue
                if _diagonal_ok(pts, i, a, c):
                    left = _tri(pts[i:j + 1], depth + 1)
                    if left is None:
                        continue
                    right = _tri(pts[j:] + pts[:i + 1], depth + 1)
                    if right is None:
                        continue
                    return tris + left + right
        return None
    if len(pts) == 3 and cross(*pts) > 0:
        tris.append(tuple(pts))
    return tris


def is_convex(p):
    n = len(p)
    if n < 3 or len(set(p)) != n:
        return False
    for i in range(n):
        if cross(p[i], p[(i + 1) % n], p[(i + 2) % n]) < 0:
            return False
    return area2(p) > 0


def hertel_mehlhorn(tris):
    """Merge pieces across shared diagonals while the result stays convex."""
    polys = [list(t) for t in tris]
    changed = True
    while changed:
        changed = False
        owner = {}
        for pi, p in enumerate(polys):
            for i in range(len(p)):
                owner.setdefault((p[i], p[(i + 1) % len(p)]), pi)
        for (u, v), pi in owner.items():
            pj = owner.get((v, u))
            if pj is None or pj == pi:
                continue
            A, B = polys[pi], polys[pj]
            ia = next(i for i in range(len(A)) if A[i] == u and A[(i + 1) % len(A)] == v)
            ib = next((i for i in range(len(B)) if B[i] == v and B[(i + 1) % len(B)] == u), None)
            if ib is None:
                continue
            a_part = [A[(ia + 1 + k) % len(A)] for k in range(len(A))]  # starts at v, ends at u
            b_part = [B[(ib + 2 + k) % len(B)] for k in range(len(B) - 2)]  # after u, before v
            merged = a_part + b_part
            if is_convex(merged):
                polys[pi] = merged
                del polys[pj]
                changed = True
                break
    return polys


def _visible(outer, holes, h, o):
    mid = ((h[0] + o[0]) / 2.0, (h[1] + o[1]) / 2.0)
    if winding(mid, outer) <= 0 or any(winding(mid, hh) != 0 for hh in holes):
        return False
    for ring in [outer] + holes:
        n = len(ring)
        if any(segments_cross(h, o, ring[i], ring[(i + 1) % n]) for i in range(n)):
            return False
    return True


def _split_by_hole(outer, holes):
    """Join holes[0] to the outer ring by two non-crossing visible segments: two simple polygons (the other holes are shared out
    between them). Returns [(outer, holes), (outer, holes)] or None."""
    hole = holes[0]
    rest = holes[1:]
    cands = []
    for hi, h in enumerate(hole):
        for oi, o in enumerate(outer):
            if h != o and _visible(outer, holes, h, o):
                cands.append(((h[0] - o[0]) ** 2 + (h[1] - o[1]) ** 2, hi, oi))
    cands.sort()
    for d1, h1, o1 in cands:
        for d2, h2, o2 in cands:
            if h2 == h1 or o2 == o1 or hole[h2] == hole[h1] or outer[o2] == outer[o1]:
                continue
            if segments_cross(hole[h1], outer[o1], hole[h2], outer[o2]):
                continue
            # polygon A: outer from o1 to o2, then the hole from h2 to h1 (its own clockwise order); polygon B: outer o2 to o1, hole h1 to h2
            def arc(ring, i, j):
                out = [ring[i]]
                k = i
                while k != j:
                    k = (k + 1) % len(ring)
                    out.append(ring[k])
                return out
            A = arc(outer, o1, o2) + arc(hole, h2, h1)
            B = arc(outer, o2, o1) + arc(hole, h1, h2)
            if area2(A) <= 0 or area2(B) <= 0 or area2(A) + area2(B) != area2(outer) + area2(hole):
                continue
            ha, hb = [], []
            for r in rest:
                (ha if winding(r[0], A) > 0 or (winding(r[0], A) == 0 and winding(r[0], B) <= 0) else hb).append(r)
            return [(A, ha), (B, hb)]
    return None


def _tri_holes(outer, holes):
    if not holes:
        return triangulate(outer)
    parts = _split_by_hole(outer, holes)
    if parts is None:
        return None
    out = []
    for o, hs in parts:
        t = _tri_holes(o, hs)
        if t is None:
            return None
        out.extend(t)
    return out


def decompose(outer, holes):
    """Convex pieces (CCW vertex lists) of a polygon with holes, or None on failure."""
    tris = _tri_holes(list(outer), [list(h) for h in holes])
    if tris is None:
        return None
    if sum(area2(t) for t in tris) != area2(outer) + sum(area2(h) for h in holes):
        return None
    return hertel_mehlhorn(tris)
