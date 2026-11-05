"""Tests of the Gospel path's authored data (Stage 3): the maps, the people, the directed acts, the music prompts, and that nothing in the data is text for play."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "story"))

from art import directed, gospel_maps, wardrobe  # noqa: E402

PATH = ROOT / "content" / "paths" / "gospel"


class GospelData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.built = gospel_maps.build_all(False)
        cls.runj = json.loads((PATH / "run.json").read_text(encoding="utf-8"))
        cls.music = json.loads((PATH / "music.json").read_text(encoding="utf-8"))

    def test_four_maps_with_seventeen_views(self):
        self.assertEqual(sorted(self.built), sorted(["galilee_shore", "hillside", "bethany", "jerusalem"]))
        self.assertEqual(len(gospel_maps.VIEWS), 17)
        for mid, (m, sd) in self.built.items():
            ids = [a["id"] for a in sd["actors"]]
            self.assertEqual(len(ids), len(set(ids)), f"{mid}: actor ids are unique")
            homes = [h["actor"] for h in m["homes"]]
            self.assertEqual(sorted(homes), sorted(ids), f"{mid}: every person has one home")
            for t in m["things"]:
                if t.get("kind") != "light":
                    self.assertIn(t["sprite"], m["textures"], f"{mid}: {t['id']} names a texture")

    def test_a_disciple_is_the_same_person_in_every_map(self):
        specs = {}
        for mid, (m, sd) in self.built.items():
            cast = wardrobe.cast_chapter(mid, sd["actors"])
            for a in sd["actors"]:
                base = a["id"].split("_")[0]
                if base[0] == "d" and base[1:].isdigit():
                    c = cast[a["id"]]
                    key = (c["colours"]["skin"], c["colours"]["top"], c["colours"]["hair"], c["hair"]["style"], c["top"]["kind"])
                    specs.setdefault(base, set()).add(key)
        self.assertTrue(len(specs) >= 6, "several disciples recur")
        for base, keys in specs.items():
            self.assertEqual(len(keys), 1, f"{base} looks the same wherever they stand: {keys}")

    def test_the_directed_acts_come_from_the_paths_own_data(self):
        for mid, (m, sd) in self.built.items():
            d = directed.directed(mid)
            ids = {a["id"] for a in sd["actors"]}
            self.assertTrue(set(d) <= ids, f"{mid}: only people of the map are directed")
        jer = directed.directed("jerusalem")
        self.assertIn("x1", jer, "the Golgotha witnesses are directed by the block staging")
        self.assertTrue(any(act == "kneel" for act, face, fc in jer["x1"]))

    def test_every_scene_has_a_verbatim_music_prompt_and_a_temporary_pack(self):
        prompts = json.loads((PATH / "prompts.json").read_text(encoding="utf-8"))
        self.assertEqual(len(prompts), 17)
        for n in self.music["nodes"]:
            self.assertTrue(n["prompt"].startswith("124 BPM "), n["id"])
            self.assertTrue(n["prompt"].endswith("Separate editable MIDI tracks."), n["id"])
            self.assertTrue(n["temporary"])
        self.assertEqual(self.music["placeholder"]["levels_db"]["bass"], -12.0)

    def test_no_data_carries_text_for_play(self):
        bad = {"text", "caption", "label_text", "title_text"}

        def walk(x, where):
            if isinstance(x, dict):
                for k, v in x.items():
                    self.assertNotIn(k, bad, f"{where}: {k}")
                    walk(v, where + "/" + k)
            elif isinstance(x, list):
                for i, v in enumerate(x):
                    walk(v, where + f"[{i}]")
        for fn in (PATH / "hotspots").glob("*.json"):
            walk(json.loads(fn.read_text(encoding="utf-8")), fn.name)
        for n in self.runj["nodes"]:
            walk(n.get("cast", []), n["id"])


if __name__ == "__main__":
    unittest.main()
