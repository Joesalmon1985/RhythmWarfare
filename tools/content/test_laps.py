"""Tests for the two laps (tools/run/laps.py, docs/CONTINUOUS_RUN.md "Two laps"): the cast re-timing rule, and the shipped run.json of the three paths."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "run"))
import laps  # noqa: E402

SINGLE = {"gospel": {"jordan", "jerusalem.golgotha"}, "squadron": set(), "ember": {"hollow"}}


def load(pid: str) -> dict:
    return json.loads((ROOT / "content" / "paths" / pid / "run.json").read_text(encoding="utf-8"))


class RetimeRule(unittest.TestCase):
    def test_one_lap_is_unchanged(self):
        for b in (0, 16, 32, 48, 61.5, 63):
            self.assertEqual(laps.retime_beat(b, 1), b)

    def test_the_story_is_spread_and_the_last_block_keeps_its_place_in_the_last_lap(self):
        self.assertEqual([laps.retime_beat(b, 2) for b in (0, 16, 32, 40, 47.5)], [0, 32, 64, 80, 95])
        self.assertEqual([laps.retime_beat(b, 2) for b in (48, 56, 61, 61.5, 63)], [112, 120, 125, 125.5, 127])
        self.assertEqual(laps.retime_beat(61, 3), 61 + 128)

    def test_the_order_is_kept_and_nothing_lands_between_the_stretch_and_the_last_block(self):
        beats = [x / 2.0 for x in range(0, 127)]
        out = [laps.retime_beat(b, 2) for b in beats]
        self.assertEqual(out, sorted(out))
        self.assertFalse([o for o in out if 95 < o < 112], "the stretched part ends before beat 96, the last block starts at 112")
        self.assertTrue(all(0 <= o <= 127 for o in out))

    def test_a_line_that_holds_until_the_next_beat_of_the_story_holds_twice_as_long(self):
        self.assertEqual(laps.retime_line({"actor": "a", "at_beat": 16, "act": "stare", "beats": 16}, 2), {"actor": "a", "at_beat": 32, "act": "stare", "beats": 32})
        self.assertEqual(laps.retime_line({"actor": "a", "at_beat": 16, "act": "nod", "beats": 4}, 2)["beats"], 4, "a short act stays short")
        self.assertNotIn("beats", laps.retime_line({"actor": "a", "at_beat": 16, "act": "nod"}, 2))
        self.assertEqual(laps.retime_line({"actor": "a", "at_beat": 50, "act": "stare", "beats": 14}, 2)["beats"], 14, "the last block's lines keep their hold")
        self.assertLessEqual(laps.retime_line({"actor": "a", "at_beat": 0, "act": "stare", "beats": 40}, 2)["beats"], 64)

    def test_nothing_is_added_or_removed_and_the_other_fields_stay(self):
        cast = [{"actor": "a", "at_beat": 0, "act": "stare", "face": "grief", "if_energy_below": 40}, {"piece": "p", "op": "on", "at_beat": 34}]
        out = laps.retime_cast(cast, 2)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0], {"actor": "a", "at_beat": 0, "act": "stare", "face": "grief", "if_energy_below": 40})
        self.assertEqual(out[1], {"piece": "p", "op": "on", "at_beat": 68})
        self.assertEqual(cast[1]["at_beat"], 34, "the input is not changed")

    def test_finish_run_sets_the_path_laps_the_exceptions_and_the_canonical_order(self):
        run = {"schema": 1, "path": {"id": "x"}, "timing": {}, "start_node": "a", "worlds": [], "mix": {"gain_db": 0}, "cinematics": {},
               "nodes": [{"id": "a", "blurb": "b", "cast": [{"actor": "q", "at_beat": 32, "act": "nod"}]}, {"id": "b", "blurb": "b", "cast": [{"actor": "q", "at_beat": 32, "act": "nod"}]}]}
        out = laps.finish_run(run, 2, ("a",))
        self.assertEqual(out["path"]["laps"], 2)
        self.assertEqual(list(out)[:4], ["schema", "path", "timing", "mix"])
        a, b = out["nodes"]
        self.assertEqual(a["laps"], 1)
        self.assertEqual(a["cast"][0]["at_beat"], 32, "a scene that stays at one lap keeps its cast")
        self.assertNotIn("laps", b)
        self.assertEqual(b["cast"][0]["at_beat"], 64)
        with self.assertRaises(SystemExit):
            laps.finish_run(run, 2, ("nope",))


class ShippedPaths(unittest.TestCase):
    def test_every_path_scene_plays_two_laps_except_the_named_ones(self):
        for pid, single in SINGLE.items():
            run = load(pid)
            self.assertEqual(run["path"]["laps"], 2, pid)
            for n in run["nodes"]:
                want = 1 if n["id"] in single else 2
                self.assertEqual(int(n.get("laps", run["path"]["laps"])), want, f"{pid} {n['id']}")

    def test_the_cast_of_a_two_lap_scene_fits_its_laps_and_leaves_no_gap_before_the_last_block(self):
        for pid in SINGLE:
            run = load(pid)
            for n in run["nodes"]:
                n_laps = int(n.get("laps", run["path"]["laps"]))
                for c in n.get("cast", []):
                    b = float(c["at_beat"])
                    self.assertTrue(0 <= b <= 64 * n_laps - 1, f"{pid} {n['id']} beat {b}")
                    if n_laps == 2:
                        self.assertFalse(95.0 < b < 112.0, f"{pid} {n['id']}: beat {b} is neither stretched nor in the last block")
                    if "text" in c:
                        self.fail("a cast line carries text")

    def test_the_main_run_and_the_stub_stay_at_one_lap(self):
        main = json.loads((ROOT / "content/run/run.json").read_text(encoding="utf-8"))
        self.assertNotIn("laps", main.get("path", {}))
        self.assertTrue(all("laps" not in n for n in main["nodes"]))
        stub = load("stub")
        self.assertEqual(int(stub["path"].get("laps", 1)), 1)


if __name__ == "__main__":
    unittest.main()
