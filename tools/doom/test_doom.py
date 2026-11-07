"""Tests for the Doom conversion tools, on a tiny synthetic WAD built in memory (no real Doom data needed).
Run:  python -I tools/doom/test_doom.py
"""
import copy
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_world  # noqa: E402
import convert  # noqa: E402
import geom  # noqa: E402
import render_plan  # noqa: E402
import wad  # noqa: E402


def name8(s):
    return s.encode("ascii").ljust(8, b"\0")


def build_wad(verts, lines, sides, sectors, things=()):
    """lines: (v1, v2, flags, right_side, left_side); sides: (sector,); sectors: (floor, ceil, light)."""
    lump = {}
    lump["THINGS"] = b"".join(struct.pack("<hhhhh", *t) for t in things)
    lump["LINEDEFS"] = b"".join(struct.pack("<hhhhhhh", v1, v2, fl, 0, 0, r, l) for v1, v2, fl, r, l in lines)
    lump["SIDEDEFS"] = b"".join(struct.pack("<hh8s8s8sh", 0, 0, name8("-"), name8("-"), name8("STARTAN3"), s) for (s,) in sides)
    lump["VERTEXES"] = b"".join(struct.pack("<hh", *v) for v in verts)
    lump["SECTORS"] = b"".join(struct.pack("<hh8s8shhh", f, c, name8("FLOOR4_8"), name8("CEIL3_5"), li, 0, 0) for f, c, li in sectors)
    order = ["THINGS", "LINEDEFS", "SIDEDEFS", "VERTEXES", "SEGS", "SSECTORS", "NODES", "SECTORS", "REJECT", "BLOCKMAP"]
    entries = [("MAP01", b"")] + [(n, lump.get(n, b"")) for n in order]
    data = b"IWAD" + struct.pack("<ii", len(entries), 12)
    body, directory, pos = b"", b"", 12
    for n, b in entries:
        directory += struct.pack("<ii8s", pos + len(body), len(b), name8(n))
        body += b
    return data[:8] + struct.pack("<i", 12 + len(body)) + b"" + body + directory


class Geom(unittest.TestCase):
    def test_square_with_hole_decomposes_without_loss(self):
        outer = [(0, 0), (256, 0), (256, 256), (0, 256)]
        hole = [(96, 96), (96, 160), (160, 160), (160, 96)]  # clockwise
        pieces = geom.decompose(outer, [hole])
        self.assertIsNotNone(pieces)
        self.assertEqual(sum(geom.area2(p) for p in pieces), geom.area2(outer) + geom.area2(hole))
        for p in pieces:
            self.assertTrue(geom.is_convex(p), p)

    def test_l_shape_gives_convex_pieces_keeping_vertices(self):
        L = [(0, 0), (256, 0), (256, 128), (128, 128), (128, 256), (0, 256)]
        pieces = geom.decompose(L, [])
        self.assertGreaterEqual(len(pieces), 2)
        self.assertEqual(sum(geom.area2(p) for p in pieces), geom.area2(L))
        verts = set(v for p in pieces for v in p)
        self.assertTrue(set(L) <= verts)

    def test_colinear_vertex_is_kept(self):
        sq = [(0, 0), (128, 0), (256, 0), (256, 256), (0, 256)]
        pieces = geom.decompose(sq, [])
        self.assertTrue(any((128, 0) in p for p in pieces))


def synthetic_map():
    """Two rooms (A floor 0, B floor 24 units: one step, one portal) plus a pillar hole in A and an L shaped room C south of A."""
    V = [(0, 0), (0, 256), (256, 256), (256, 0), (512, 256), (512, 0),   # 0..5
         (96, 96), (96, 160), (160, 160), (160, 96),                      # 6..9 pillar
         (256, -128), (128, -128), (128, -256), (0, -256)]                # 10..13 for C
    sides, lines = [], []

    def S(s):
        sides.append((s,))
        return len(sides) - 1
    lines += [(0, 1, 1, S(0), -1), (1, 2, 1, S(0), -1),                  # A west, north (clockwise, A on the right)
              (2, 3, 4, S(0), S(1)),                                     # A | B portal, going south: A west of it (right), B east (left)
              (3, 0, 4, S(0), S(2))]                                     # A | C, going west: A north (right), C south (left)
    lines += [(2, 4, 1, S(1), -1), (4, 5, 1, S(1), -1), (5, 3, 1, S(1), -1)]  # B walls... B on the right of the clockwise ring 2->4->5->3
    # B ring: (256,256) -> (512,256) east, -> (512,0) south, -> (256,0) west: clockwise, B on the right. ok.
    lines += [(3, 10, 1, S(2), -1), (10, 11, 1, S(2), -1), (11, 12, 1, S(2), -1), (12, 13, 1, S(2), -1), (13, 0, 1, S(2), -1)]
    # C ring clockwise (C on the right): the shared line 3 -> 0 above has C on its left, then 3 -> (256,-128) -> (128,-128) -> (128,-256) -> (0,-256) -> 0
    # pillar, clockwise, pillar sector 3 on the right, A (sector 0) on the left
    lines += [(6, 7, 4, S(3), S(0)), (7, 8, 4, S(3), S(0)), (8, 9, 4, S(3), S(0)), (9, 6, 4, S(3), S(0))]
    sectors = [(0, 128, 200), (24, 128, 150), (0, 128, 120), (64, 128, 255)]
    things = [(24, 128, 90, 1, 7)]
    return V, lines, sides, sectors, things


class Reader(unittest.TestCase):
    def setUp(self):
        self.w = wad.Wad(build_wad(*synthetic_map()))

    def test_header_and_directory(self):
        self.assertEqual(self.w.ident, "IWAD")
        self.assertEqual(self.w.map_names(), ["MAP01"])
        self.assertEqual(len(self.w.lumps), 11)

    def test_map_lumps(self):
        m = self.w.read_map("MAP01")
        self.assertEqual((len(m.vertices), len(m.linedefs), len(m.sidedefs), len(m.sectors), len(m.things)), (14, 16, 22, 4, 1))
        self.assertEqual(m.sectors[1]["floor"], 24)
        self.assertEqual(m.sidedefs[0]["middle"], "STARTAN3")
        self.assertEqual(m.sectors[0]["floor_tex"], "FLOOR4_8")

    def test_empty_geometry_is_reported(self):
        data = build_wad([], [], [], [])
        w = wad.Wad(data)
        with self.assertRaises(ValueError):
            w.read_map("MAP01")

    def test_bad_header(self):
        with self.assertRaises(ValueError):
            wad.Wad(b"NOPE" + b"\0" * 20)


class Convert(unittest.TestCase):
    def setUp(self):
        self.m = wad.Wad(build_wad(*synthetic_map())).read_map("MAP01")
        self.d = convert.convert_map(self.m, name="MAP01")

    def test_scale_axis_and_start(self):
        wp = self.d["waypoints"][0]
        self.assertAlmostEqual(wp["at"][0], 0.75)   # x 24 -> 0.75 m
        self.assertAlmostEqual(wp["at"][1], -4.0)   # y 128 -> z -4 m (flipped)
        self.assertAlmostEqual(wp["yaw"], 0.0)      # Doom angle 90 = north = yaw 0
        self.assertEqual(self.d["units_per_m"], 1)
        self.assertEqual(self.d["eye_height"], 1.6)

    def test_heights_and_light(self):
        b = [s for s in self.d["sectors"] if s["doom_sector"] == 1][0]
        self.assertAlmostEqual(b["floor"], 0.75)
        self.assertAlmostEqual(b["ceiling"], 4.0)
        self.assertTrue(0.2 <= b["light"] <= 0.9)

    def test_pieces_cover_the_sectors_and_ids(self):
        sm = self.d["doom"]["sector_map"]
        self.assertEqual(sorted(sm), ["0", "1", "2", "3"])
        for k, v in sm.items():
            for pid in v["pieces"]:
                self.assertTrue(pid.startswith(k + "_"))
        area = lambda ids: sum(check_world._area(s["polygon"]) for s in self.d["sectors"] if s["id"] in ids)
        self.assertAlmostEqual(area(sm["0"]["pieces"]), 8 * 8 - 2 * 2)   # room minus the pillar hole, in square metres
        self.assertAlmostEqual(area(sm["2"]["pieces"]), 8 * 4 + 4 * 4)   # the L: 256x128 plus 128x128 units
        self.assertAlmostEqual(area(sm["1"]["pieces"]), 8 * 8)

    def test_validator_passes_and_reports_the_step(self):
        errors, warnings, rep = check_world.check(self.d)
        self.assertEqual(errors, [])
        self.assertEqual(rep["unreachable"], 0)
        self.assertEqual(rep["steps_over_0_6m"], 1)  # the 24 unit (0.75 m) step A -> B; the pillar plinth rises 2 m but is a hole's own sector
        self.assertGreaterEqual(rep["steps_over_0_6m"], 1)
        self.assertGreaterEqual(rep["portals"], 3)

    def test_portals_are_whole_shared_edges_between_exactly_two_pieces(self):
        _, _, _ = check_world.check(self.d)
        keys = {}
        for s in self.d["sectors"]:
            p = [tuple(q) for q in s["polygon"]]
            for i in range(len(p)):
                a, b = p[i], p[(i + 1) % len(p)]
                keys.setdefault(frozenset((a, b)), []).append(s["id"])
        for w in self.d["walls"]:
            self.assertEqual(len(keys[frozenset((tuple(w["from"]), tuple(w["to"])))]), 2)

    def test_winding_is_counter_clockwise_in_x_z(self):
        for s in self.d["sectors"]:
            self.assertGreater(check_world._area(s["polygon"]), 0)

    def test_tiny_sector_is_dropped_and_recorded(self):
        m = copy.deepcopy(self.m)
        m.sectors[3]["floor"] = 0
        # shrink the pillar to a 2 unit square (0.0039 m2)
        m.vertices[6:10] = [(96, 96), (96, 98), (98, 98), (98, 96)]
        d = convert.convert_map(m, name="MAP01")
        self.assertEqual([t["sector"] for t in d["doom"]["dropped_tiny"]], [3])
        self.assertEqual(check_world.check(d)[0], [])

    def test_closed_door_is_opened(self):
        m = copy.deepcopy(self.m)
        m.sectors[3]["floor"] = 128  # ceiling == floor
        d = convert.convert_map(m, name="MAP01")
        self.assertEqual(d["doom"]["doors_opened"], [3])
        self.assertEqual(check_world.check(d)[0], [])

    def test_cut_by_sectors_and_unreachable_pruning(self):
        d = convert.convert_map(self.m, sectors_only=[0, 1, 3], name="MAP01")
        self.assertEqual(sorted(d["doom"]["sector_map"]), ["0", "1", "3"])
        self.assertEqual(check_world.check(d)[0], [])

    def test_impassable_line_blocks_walking(self):
        m = copy.deepcopy(self.m)
        m.linedefs[2]["flags"] |= wad.IMPASSABLE  # the A | B portal
        d = convert.convert_map(m, name="MAP01")  # B becomes unreachable and is pruned
        self.assertNotIn("1", d["doom"]["sector_map"])
        self.assertTrue(d["doom"]["dropped_unreachable_pieces"])
        self.assertEqual(check_world.check(d)[0], [])

    def test_vscale(self):
        d = convert.convert_map(self.m, vscale=1.2, name="MAP01")
        b = [s for s in d["sectors"] if s["doom_sector"] == 1][0]
        self.assertAlmostEqual(b["floor"], 0.75 * 1.2)


class Validator(unittest.TestCase):
    def setUp(self):
        self.d = convert.convert_map(wad.Wad(build_wad(*synthetic_map())).read_map("MAP01"), name="MAP01")

    def test_catches_clockwise_polygon(self):
        d = copy.deepcopy(self.d)
        d["sectors"][0]["polygon"].reverse()
        self.assertTrue(any("clockwise" in e for e in check_world.check(d)[0]))

    def test_catches_missing_portal(self):
        d = copy.deepcopy(self.d)
        d["walls"].pop()
        self.assertTrue(any("no portal" in e or "not a whole edge" in e for e in check_world.check(d)[0]))

    def test_catches_ceiling_below_floor(self):
        d = copy.deepcopy(self.d)
        d["sectors"][0]["ceiling"] = d["sectors"][0]["floor"] - 1
        self.assertTrue(any("ceiling" in e for e in check_world.check(d)[0]))

    def test_catches_nonconvex(self):
        d = copy.deepcopy(self.d)
        d["sectors"].append({"id": "x_0", "polygon": [[20, 20], [24, 20], [22, 22], [24, 24], [20, 24]], "floor": 0, "ceiling": 3})
        errs = check_world.check(d)[0]
        self.assertTrue(any("not convex" in e for e in errs))

    def test_catches_crack(self):
        d = copy.deepcopy(self.d)
        d["sectors"].append({"id": "t_0", "polygon": [[-10, 0], [-8, 0], [-9, 2]], "floor": 0, "ceiling": 3})
        d["sectors"].append({"id": "t_1", "polygon": [[-9, 0], [-7, 0], [-8, -2]], "floor": 0, "ceiling": 3})
        self.assertTrue(any("crack" in e for e in check_world.check(d)[0]))

    def test_catches_unreachable_piece(self):
        d = copy.deepcopy(self.d)
        d["sectors"].append({"id": "far_0", "polygon": [[100, 100], [102, 100], [102, 102], [100, 102]], "floor": 0, "ceiling": 3})
        self.assertTrue(any("not reachable" in e for e in check_world.check(d)[0]))

    def test_plan_png(self):
        W, H, rows = render_plan.render(self.d, 300)
        self.assertEqual(len(rows), H)
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            n = render_plan.write_png(os.path.join(t, "p.png"), W, H, rows)
            with open(os.path.join(t, "p.png"), "rb") as f:
                self.assertEqual(f.read(8), b"\x89PNG\r\n\x1a\n")
        self.assertLess(n, 300 * 1024)


if __name__ == "__main__":
    unittest.main(verbosity=1)
