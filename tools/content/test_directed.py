"""Tests for tools/story/art/directed.py: the readers of the acting data (hotspot `acting` blocks, scene `cast` lines, cinematic `cast` lines, the hand-kept
directed_actors.json). They run against the shipped data (it must read without an error, and every act and face it names must exist) and against a small synthetic
tree that has every shape of the format, including a `then` chain, a Bassment `figure` block and a hotspot that names its actor on a thing anchor."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "story" / "art"))

import directed  # noqa: E402

POSES = json.loads((ROOT / "assets" / "story" / "people_poses.json").read_text(encoding="utf-8"))


def write(root: Path, rel: str, doc) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc), encoding="utf-8")


def synthetic_root() -> Path:
    root = Path(tempfile.mkdtemp())
    write(root, "content/run/run.json", {
        "worlds": [{"id": "hospital", "map": "ward_map"}, {"id": "warehouse", "map": "night_one"}],
        "nodes": [
            {"id": "hospital", "world": "hospital", "cast": [
                {"actor": "h03", "at_beat": 0, "act": "stare", "face": "fear", "look_at": "camera", "beats": 16},
                {"actor": "h03", "at_beat": 32, "act": "plead", "face": "plea"},
                {"actor": "h03", "at_beat": 48, "act": "cover_face", "face": "grief", "if_energy_below": 40},
                {"actor": "h02", "at_beat": 48, "act": "point", "face": "resolve", "look_at": "to_garden"}]},
            {"id": "warehouse", "world": "warehouse", "cast": [{"actor": "g07", "at_beat": 4, "act": "nod"}]},
        ],
        "cinematics": {"hospital.setback": {"world": "hospital", "steps": [], "cast": [{"actor": "h09", "at_beat": 2, "act": "block", "face": "anger"}]}},
    })
    write(root, "content/run/hotspots/hospital.json", {"world": "hospital", "hotspots": [
        {"id": "hospital.nurse", "map": "ward_map", "anchor": {"actor": "h02"}, "acting": {
            "available": {"act": "beckon", "face": "plea", "look_at": "camera"},
            "selected": {"act": "nod", "face": "relief"},
            "committed": {"act": "point", "face": "resolve", "look_at": "to_garden"},
            "success": {"act": "cheer", "face": "cheer", "beats": 8},
            "failure": {"act": "shake_head", "face": "doubt", "beats": 8, "then": {"act": "stare", "face": "sad"}}}},
        {"id": "hospital.thing", "map": "ward_map", "anchor": {"thing": "wizard_floor"}, "acting": {"actor": "h11", "available": {"act": "beckon"}}},
        {"id": "hospital.no_acting", "map": "ward_map", "anchor": {"actor": "h04"}},
        {"id": "hospital.creature", "map": "ward_map", "anchor": {"thing": "hs_x"}, "acting": {"figure": "bouncer", "available": {"act": "block", "face": "anger"}}},
        {"id": "other.chapter", "map": "night_one", "anchor": {"actor": "g07"}, "acting": {"available": {"act": "beckon"}}},
    ]})
    return root


class DirectedReaders(unittest.TestCase):
    def test_shipped_data_reads_and_every_act_and_face_exists(self):
        run = json.loads((ROOT / "content/run/run.json").read_text(encoding="utf-8"))
        for w in run["worlds"]:
            found = directed.directed(w["map"], POSES)
            for aid, entries in found.items():
                for act, face, facings in entries:
                    self.assertIn(face, POSES["faces"], f"{w['map']}/{aid}")
                    self.assertTrue(set(facings) <= {"front", "side", "back"})

    def test_hotspot_acting_blocks_name_their_people_acts_and_faces(self):
        root = synthetic_root()
        found = directed.directed("ward_map", POSES, str(root))
        h02 = {(a, f) for a, f, _ in found["h02"]}
        # the plain act for its own default face, the acted face otherwise; every state and the `then` of failure are read
        self.assertIn(("beckon", "plea"), h02)
        self.assertIn(("nod", "relief"), h02)
        self.assertIn(("point", "resolve"), h02)
        self.assertIn(("cheer", "cheer"), h02)
        self.assertIn(("shake_head", "doubt"), h02)
        self.assertIn(("stare", "sad"), h02)
        self.assertEqual(directed.state_key("beckon", "plea", POSES["face_of"]), "beckon@plea")
        self.assertEqual(directed.state_key("shake_head", "doubt", POSES["face_of"]), "shake_head", "doubt is shake_head's own face")
        self.assertEqual(directed.state_key("cheer", "cheer", POSES["face_of"]), "cheer")

    def test_acting_actor_overrides_the_anchor_and_a_creature_figure_is_skipped(self):
        found = directed.directed("ward_map", directed_poses(), str(synthetic_root()))
        self.assertIn("h11", found, "a hotspot on a thing may name its actor")
        self.assertNotIn("h04", found, "no acting block, nothing to bake")
        self.assertNotIn("bouncer", found, "a Bassment creature is a billboard, not a baked person")
        self.assertNotIn("g07", found, "another chapter's hotspot is not this chapter's")

    def test_cast_lines_of_scenes_and_cinematics_are_read_by_chapter(self):
        found = directed.directed("ward_map", directed_poses(), str(synthetic_root()))
        h03 = {(a, f) for a, f, _ in found["h03"]}
        self.assertEqual(h03, {("stare", "fear"), ("plead", "plea"), ("cover_face", "grief")})
        self.assertIn(("block", "anger"), {(a, f) for a, f, _ in found["h09"]}, "a cinematic's cast line")
        other = directed.directed("night_one", directed_poses(), str(synthetic_root()))
        self.assertIn(("nod", "happy"), {(a, f) for a, f, _ in other["g07"]}, "a cast line with no face takes the act's own")

    def test_facings_follow_the_act(self):
        found = directed.directed("ward_map", directed_poses(), str(synthetic_root()))
        by_act = {a: fc for a, f, fc in found["h03"]}
        self.assertEqual(by_act["stare"], ("front", "side", "back"), "an old targeted act keeps its own facings")
        self.assertEqual(by_act["cover_face"], ("front", "side"))
        root = synthetic_root()
        write(root, "content/run/hotspots/more.json", {"world": "hospital", "hotspots": [
            {"id": "x", "map": "ward_map", "anchor": {"actor": "h20"}, "acting": {"failure": {"act": "collapse", "face": "grief"}}}]})
        found2 = directed.directed("ward_map", directed_poses(), str(root))
        self.assertEqual(found2["h20"][0][2], ("front", "side", "back"), "a collapse is also seen from behind")

    def test_unknown_acts_and_faces_are_errors_not_skipped(self):
        root = synthetic_root()
        write(root, "content/run/hotspots/bad.json", {"world": "hospital", "hotspots": [
            {"id": "b", "map": "ward_map", "anchor": {"actor": "h30"}, "acting": {"available": {"act": "moonwalk"}}}]})
        with self.assertRaises(ValueError):
            directed.directed("ward_map", directed_poses(), str(root))
        root2 = synthetic_root()
        write(root2, "content/run/hotspots/bad.json", {"world": "hospital", "hotspots": [
            {"id": "b", "map": "ward_map", "anchor": {"actor": "h30"}, "acting": {"available": {"act": "nod", "face": "smug"}}}]})
        with self.assertRaises(ValueError):
            directed.directed("ward_map", directed_poses(), str(root2))


def directed_poses() -> dict:
    return POSES


if __name__ == "__main__":
    unittest.main()
