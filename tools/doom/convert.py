"""Doom map -> StoryMap JSON (content/story/maps/doom_<scene>.json).

  python tools/doom/convert.py --scene warehouse          (one scene of tools/doom/scenes.json)
  python tools/doom/convert.py --scene warehouse --trace tools/doom/trace/warehouse.json   (approximate, hand-traced, no WAD)
  python tools/doom/convert.py --all                      (all eight)
  python tools/doom/convert.py --map MAP07 --out x.json [--bbox x0,y0,x1,y1] [--sectors 1,2,3]

Conventions (details and reasons in docs/doom/CONVERSION.md):
  * horizontal: 32 Doom units = 1 m; vertical: 32 Doom units = 1 m times --vscale (default 1.0)
  * x_m = x / 32, z_m = -y / 32 (Doom north, y up, becomes -z: the top of a plan view stays the top, nothing is mirrored)
  * StoryMap sector polygons are counter-clockwise in its (x, z) shoelace sense; Doom sector rings are traced counter-clockwise in
    (x, y) and then reversed after the flip, because the flip mirrors orientation
  * every piece edge that two pieces share becomes a portal wall declared once, including the diagonals between pieces of one Doom sector
Standard library only. The WAD is read from RW_DOOM_WAD (default in wad.py) and is never copied.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geom  # noqa: E402
import wad as wadmod  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
UNITS_PER_M = 32.0
MIN_AREA_M2 = 0.05
MIN_CLEARANCE_M = 1.2        # a two-sided line whose opening is lower than this is a window, not a passage (blocked)
PLAYER_STEP_UNITS = 24       # Doom's own step limit, used for reports
DOOR_OPEN_FALLBACK_M = 2.25  # a closed door (ceiling == floor) with no neighbour to borrow a ceiling from
ART = "mothership"           # placeholder art folder (assets/story/mothership/textures); the art agents replace the ids per scene
PLACEHOLDER_TEX = {
    "floor": ["floor_grate", "floor_bridge", "floor_airlock"],
    "ceil": "ceil_hull", "wall": "wall_hull", "trim": "trim",
}
SKY_TEX = "textures/sky_space.png"


def placeholder_textures():
    names = PLACEHOLDER_TEX["floor"] + [PLACEHOLDER_TEX["ceil"], PLACEHOLDER_TEX["wall"], PLACEHOLDER_TEX["trim"]]
    return {n: "textures/%s.png" % n for n in names}


def _floor_tex(flat):
    h = sum(ord(c) for c in flat) if flat else 0
    return PLACEHOLDER_TEX["floor"][h % len(PLACEHOLDER_TEX["floor"])]


def load_scenes():
    with open(os.path.join(HERE, "scenes.json"), encoding="utf-8") as f:
        return json.load(f)


def convert_map(m, vscale=1.0, bbox=None, sectors_only=None, name="doom"):
    """DoomMap -> (StoryMap dict). Pure function of the map: no files."""
    U = UNITS_PER_M
    vs = vscale / U
    info = {"dropped_tiny": [], "dropped_unreachable": [], "dropped_unbuildable": [], "doors_opened": [], "outside_cut": [],
            "broken_sectors": [], "warnings": []}
    # --- sector selection (a curated region) ------------------------------------------------------------------------------------------
    selected = set(range(len(m.sectors)))
    if sectors_only is not None:
        selected = set(sectors_only) & selected
    if bbox is not None:
        x0, y0, x1, y1 = bbox
        inb = set()
        for ld in m.linedefs:
            for vi in (ld["v1"], ld["v2"]):
                x, y = m.vertices[vi]
                if x0 <= x <= x1 and y0 <= y <= y1:
                    for sd in (ld["right"], ld["left"]):
                        if sd != -1:
                            inb.add(m.sidedefs[sd]["sector"])
        selected &= inb
    info["outside_cut"] = sorted(set(range(len(m.sectors))) - selected)
    # --- neighbours (for doors) and the linedef of every edge ---------------------------------------------------------------------------
    nbr = {i: set() for i in range(len(m.sectors))}
    by_pair = {}
    edges = {i: [] for i in range(len(m.sectors))}
    for ld in m.linedefs:
        a, b = m.vertices[ld["v1"]], m.vertices[ld["v2"]]
        if a == b:
            continue
        rs = m.sidedefs[ld["right"]]["sector"] if ld["right"] != -1 else None
        ls = m.sidedefs[ld["left"]]["sector"] if ld["left"] != -1 else None
        by_pair[frozenset((a, b))] = ld
        if rs is not None and ls is not None and rs != ls:
            nbr[rs].add(ls)
            nbr[ls].add(rs)
        if rs is not None and rs != ls:
            edges[rs].append((b, a))  # interior of the right side is on the left of b -> a
        if ls is not None and rs != ls:
            edges[ls].append((a, b))
    # --- effective heights -------------------------------------------------------------------------------------------------------------
    height = {}
    for i, s in enumerate(m.sectors):
        fl, ce = s["floor"], s["ceiling"]
        if ce - fl <= 0:
            cands = [m.sectors[n]["ceiling"] for n in nbr[i] if m.sectors[n]["ceiling"] > fl]
            ce = max(cands) if cands else fl + int(DOOR_OPEN_FALLBACK_M * U)
            info["doors_opened"].append(i)
        height[i] = (fl, ce)
    # --- rings, area, decomposition (exact integers) -------------------------------------------------------------------------------------
    pieces = {}  # piece id -> {"ring": [(x,y)...] doom ccw, "sector": i}
    sector_pieces = {}
    for i in sorted(selected):
        if not edges[i]:
            continue
        rings, broken = geom.build_rings(edges[i])
        if broken:
            info["broken_sectors"].append(i)
        groups = geom.split_rings(rings)
        total2 = sum(geom.area2(o) + sum(geom.area2(h) for h in hs) for o, hs in groups)
        if total2 / 2.0 / (U * U) < MIN_AREA_M2:
            info["dropped_tiny"].append({"sector": i, "area_m2": round(total2 / 2.0 / (U * U), 4)})
            continue
        polys = []
        ok = True
        for outer, holes in groups:
            if geom.area2(outer) / 2.0 / (U * U) < MIN_AREA_M2:
                continue
            res = geom.decompose(outer, holes)
            if res is None:
                ok = False
                break
            polys.extend(res)
        if not ok or not polys:
            info["dropped_unbuildable"].append(i)
            continue
        ids = []
        for n, p in enumerate(polys):
            pid = "%d_%d" % (i, n)
            pieces[pid] = {"ring": p, "sector": i}
            ids.append(pid)
        sector_pieces[i] = ids
    # --- edge ownership and portals ----------------------------------------------------------------------------------------------------
    def edge_owners():
        owners = {}
        for pid, pc in pieces.items():
            r = pc["ring"]
            for k in range(len(r)):
                owners.setdefault(frozenset((r[k], r[(k + 1) % len(r)])), []).append(pid)
        return owners

    def blocked(pa, pb, a, b):
        if pieces[pa]["sector"] == pieces[pb]["sector"]:
            return False
        ld = by_pair.get(frozenset((a, b)))
        if ld is not None and ld["flags"] & wadmod.IMPASSABLE:
            return True
        fa, ca = height[pieces[pa]["sector"]]
        fb, cb = height[pieces[pb]["sector"]]
        return (min(ca, cb) - max(fa, fb)) < MIN_CLEARANCE_M * U

    # --- start ------------------------------------------------------------------------------------------------------------------------
    def margin_pole(ring):
        pts = [(x / U, -y / U) for x, y in ring]
        xs = [p[0] for p in pts]
        zs = [p[1] for p in pts]
        best = (-1.0, None)
        N = 24
        for ix in range(N + 1):
            for iz in range(N + 1):
                q = (min(xs) + (max(xs) - min(xs)) * ix / N, min(zs) + (max(zs) - min(zs)) * iz / N)
                d = _inside_margin(q, pts)
                if d > best[0]:
                    best = (d, q)
        return best

    start_pid = None
    start_at = None
    start_yaw = 0.0
    for t in m.things:
        if t["type"] == 1:
            for pid, pc in pieces.items():
                if geom.point_in_poly((t["x"], t["y"]), pc["ring"]):
                    q = (t["x"] / U, -t["y"] / U)
                    pts = [(x / U, -y / U) for x, y in pc["ring"]]
                    if _inside_margin(q, pts) >= 0.3:
                        start_pid, start_at, start_yaw = pid, q, float(t["angle"]) - 90.0
                    else:  # on a diagonal or near a wall: the roomiest spot of the same piece, facing the same way
                        dd, qq = margin_pole(pc["ring"])
                        if dd >= 0.3:
                            start_pid, start_at, start_yaw = pid, qq, float(t["angle"]) - 90.0
                    break
            break
    # --- reachability from the start ----------------------------------------------------------------------------------------------------
    def components():
        owners = edge_owners()
        adj = {pid: set() for pid in pieces}
        for key, ow in owners.items():
            if len(ow) == 2:
                a, b = tuple(key)
                if not blocked(ow[0], ow[1], a, b):
                    adj[ow[0]].add(ow[1])
                    adj[ow[1]].add(ow[0])
        return adj
    if not pieces:
        raise ValueError("no sectors left after the cut")
    if start_pid is None:
        scored = sorted(pieces, key=lambda p: -abs(geom.area2(pieces[p]["ring"])))
        for pid in scored[:40]:
            d, q = margin_pole(pieces[pid]["ring"])
            if d >= 0.3:
                start_pid, start_at = pid, q
                break
        if start_pid is None:
            raise ValueError("no piece is wide enough for the start waypoint")
    adj = components()
    seen = {start_pid}
    queue = [start_pid]
    while queue:
        cur = queue.pop()
        for n in adj[cur]:
            if n not in seen:
                seen.add(n)
                queue.append(n)
    for pid in list(pieces):
        if pid not in seen:
            info["dropped_unreachable"].append(pid)
            del pieces[pid]
    for i in list(sector_pieces):
        sector_pieces[i] = [p for p in sector_pieces[i] if p in pieces]
        if not sector_pieces[i]:
            del sector_pieces[i]
    owners = edge_owners()
    # --- output -------------------------------------------------------------------------------------------------------------------------
    sectors_out = []
    sector_map = {}
    for pid in sorted(pieces, key=lambda p: tuple(int(x) for x in p.split("_"))):
        pc = pieces[pid]
        s = m.sectors[pc["sector"]]
        fl, ce = height[pc["sector"]]
        ring = [(x / U, -y / U) for x, y in reversed(pc["ring"])]
        sky = s["ceil_tex"] == "F_SKY1"
        sectors_out.append({
            "id": pid, "polygon": [[x, z] for x, z in ring], "floor": fl * vs, "ceiling": ce * vs,
            "floor_tex": _floor_tex(s["floor_tex"]), "ceil_tex": "sky" if sky else PLACEHOLDER_TEX["ceil"], "wall_tex": PLACEHOLDER_TEX["wall"],
            "light": round(0.2 + 0.7 * max(0, min(255, s["light"])) / 255.0, 4), "tint": "#ffffff", "room": "main", "flags": [],
            "doom_sector": pc["sector"]})
    for i, ids in sorted(sector_pieces.items()):
        s = m.sectors[i]
        sector_map[str(i)] = {"pieces": ids, "floor": s["floor"], "ceiling": s["ceiling"], "light": s["light"],
                              "floor_flat": s["floor_tex"], "ceil_flat": s["ceil_tex"], "special": s["special"], "tag": s["tag"]}
    walls = []
    nportal = 0
    for key, ow in sorted(owners.items(), key=lambda kv: sorted(kv[0])):
        if len(ow) == 1:
            continue
        a, b = sorted(tuple(key))
        if len(ow) != 2:
            info["warnings"].append("edge %s shared by %d pieces: %s" % (sorted(tuple(key)), len(ow), ow))
            continue
        pa, pb = sorted(ow)
        r = pieces[pa]["ring"]  # the portal runs along pa's ccw direction after the flip: from b-to-a order of the reversed ring
        ra = list(reversed(r))
        pos = None
        for k in range(len(ra)):
            if {ra[k], ra[(k + 1) % len(ra)]} == {a, b}:
                pos = (ra[k], ra[(k + 1) % len(ra)])
        fa, ca = height[pieces[pa]["sector"]]
        fb, cb = height[pieces[pb]["sector"]]
        w = {"from": [pos[0][0] / U, -pos[0][1] / U], "to": [pos[1][0] / U, -pos[1][1] / U], "sector": pa, "portal": pb,
             "lower_tex": PLACEHOLDER_TEX["trim"] if fa != fb else "", "upper_tex": PLACEHOLDER_TEX["trim"] if ca != cb else ""}
        if blocked(pa, pb, a, b):
            w["blocked"] = True
        walls.append(w)
        nportal += 1
    sx, sz = start_at
    out = {
        "units_per_m": 1, "eye_height": 1.6, "art": ART, "start": "doom_start",
        "textures": placeholder_textures(),
        "sky": {"tex": SKY_TEX, "mode": "cylinder"},
        "sectors": sectors_out, "walls": walls, "things": [], "homes": [], "spots": {}, "silhouettes": [], "occluders": [],
        "waypoints": [{"id": "doom_start", "at": [sx, sz], "yaw": start_yaw, "sector": start_pid}],
        "doom": {
            "map": name, "units_per_m": UNITS_PER_M, "vscale": vscale, "axis": "x_m = x/32, z_m = -y/32 (Doom y up -> StoryMap -z)",
            "sector_map": sector_map, "dropped_tiny": info["dropped_tiny"], "dropped_unreachable_pieces": info["dropped_unreachable"],
            "dropped_unbuildable_sectors": info["dropped_unbuildable"], "broken_sectors": info["broken_sectors"],
            "doors_opened": info["doors_opened"], "outside_cut_sectors": len(info["outside_cut"]), "warnings": info["warnings"],
            "approximate": bool(getattr(m, "approximate", False)), "uncertain": list(getattr(m, "uncertain", [])),
            "stats": {"doom_sectors": len(sector_map), "pieces": len(sectors_out), "portals": nportal},
        },
    }
    return out


def _inside_margin(q, pts):
    """Distance from q to the nearest edge of the convex ccw/cw polygon pts when q is inside, else -1."""
    n = len(pts)
    sign = 0
    best = 1e18
    for k in range(n):
        a, b = pts[k], pts[(k + 1) % n]
        cr = (b[0] - a[0]) * (q[1] - a[1]) - (b[1] - a[1]) * (q[0] - a[0])
        s = 1 if cr > 0 else -1 if cr < 0 else 0
        if s != 0:
            if sign and s != sign:
                return -1.0
            sign = s
        L = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        if L > 0:
            best = min(best, abs(cr) / L)
    return best


def write_json(d, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1)
        f.write("\n")


def run_scene(scene, entry, w, vscale=1.0, out=None, bbox=None, sectors=None, trace=None):
    m = wadmod.load_trace(trace) if trace else w.read_map(entry["map"])
    bbox = bbox if bbox is not None else entry.get("bbox")
    sectors = sectors if sectors is not None else entry.get("sectors")
    d = convert_map(m, vscale, bbox, sectors, name=entry["map"])
    path = out or os.path.join(ROOT, entry["output"])
    write_json(d, path)
    st = d["doom"]["stats"]
    print("%s (%s): %d Doom sectors -> %d pieces, %d portals -> %s" % (scene, entry["map"], st["doom_sectors"], st["pieces"], st["portals"], path))
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scene", help="a scene of tools/doom/scenes.json")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--map", help="a map lump name, e.g. MAP07 (with --out)")
    ap.add_argument("--out")
    ap.add_argument("--wad")
    ap.add_argument("--trace", help="a hand-traced map (tools/doom/trace/<scene>.json) used instead of the WAD; the output is marked approximate")
    ap.add_argument("--vscale", type=float, default=1.0)
    ap.add_argument("--bbox", help="x0,y0,x1,y1 in Doom units: keep sectors with a line vertex inside")
    ap.add_argument("--sectors", help="comma separated Doom sector indices to keep")
    a = ap.parse_args(argv)
    bbox = tuple(int(v) for v in a.bbox.split(",")) if a.bbox else None
    secs = [int(v) for v in a.sectors.split(",")] if a.sectors else None
    scenes = load_scenes()
    try:
        w = None if a.trace else wadmod.Wad.open(a.wad)
    except OSError as e:
        print("cannot read the WAD (%s); set RW_DOOM_WAD" % e, file=sys.stderr)
        return 2
    try:
        if a.map:
            run_scene(a.map, {"map": a.map, "output": a.out or "doom_%s.json" % a.map.lower()}, w, a.vscale, a.out, bbox, secs)
        else:
            names = list(scenes) if a.all else [a.scene] if a.scene else []
            if not names:
                ap.error("give --scene, --all or --map")
            for n in names:
                run_scene(n, scenes[n], w, a.vscale, a.out if a.scene else None, bbox, secs, a.trace)
    except (ValueError, KeyError) as e:
        print("conversion failed: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
