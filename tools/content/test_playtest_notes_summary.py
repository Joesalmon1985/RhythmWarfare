"""tools/run/playtest_notes_summary.py ranks the songs and visuals a playtest disliked (docs/DEBUG_MODE.md)."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "run"))
import playtest_notes_summary as pns  # noqa: E402


def entry(verdict, pack, scene, run="main", source="owner", temporary=False, bass="", view="bar", text=""):
    stems = {"drums": bass.replace("Bass", "Drums"), "bass": bass, "other": bass.replace("Bass", "Synth")} if bass else {}
    return {"ts": "2026-11-05 14:00:00", "verdict": verdict, "run": run, "scene": scene, "pack_playing": pack, "source": source, "temporary": temporary, "stems": stems,
            "visual": {"map": "night_one", "view": view}, "text": text}


class SummaryTest(unittest.TestCase):
    def sample(self):
        return [
            entry("music_dislike", "squadron_c05", "city", run="squadron", bass="Beat Shaper - C05-Bass.wav"),
            entry("music_dislike", "squadron_c05", "air.c05", run="squadron", bass="Beat Shaper - C05-Bass.wav"),
            entry("music_dislike", "gospel_baptism", "jordan.baptism", run="gospel", source="placeholder", temporary=True, bass="synthesised"),
            entry("like", "squadron_c05", "city", run="squadron", bass="Beat Shaper - C05-Bass.wav"),
            entry("visual_dislike", "lv1_warehouse", "warehouse.bar", view="bar"),
            entry("visual_dislike", "lv1_warehouse", "warehouse.booth", view="booth"),
            entry("visual_dislike", "lv1_warehouse", "warehouse.bar", view="bar"),
            entry("note", "lv1_warehouse", "warehouse.bar", text="the bar is too dark"),
        ]

    def test_counts_and_ranking(self):
        s = pns.summarise(self.sample())
        self.assertEqual(s["verdicts"]["music_dislike"], 3)
        self.assertEqual(s["songs"]["squadron_c05"]["dislike"], 2)
        self.assertEqual(s["songs"]["squadron_c05"]["like"], 1)
        self.assertEqual(s["visuals"]["night_one / bar"]["dislike"], 2)
        self.assertEqual(s["scenes"]["main/warehouse.bar"]["visual"], 2)
        self.assertEqual(s["notes"][0]["text"], "the bar is too dark")
        self.assertIn("Beat Shaper - C05", s["sets"])

    def test_set_name_strips_the_voice(self):
        self.assertEqual(pns.set_name({"bass": "Beat Shaper - C07-Bass.wav"}), "Beat Shaper - C07")
        self.assertEqual(pns.set_name({"bass": "Beat Shaper - Lv2 Alien Spaceship-Bass (3).wav"}), "Beat Shaper - Lv2 Alien Spaceship (3)")
        self.assertEqual(pns.set_name({"bass": "synthesised"}), "")

    def test_report_names_the_most_disliked_first(self):
        text = pns.report(self.sample())
        self.assertLess(text.index("squadron_c05"), text.index("gospel_baptism"))
        self.assertIn("Beat Shaper - C05-Bass.wav", text)
        self.assertIn("PLACEHOLDER", text)
        self.assertIn("night_one / bar", text)
        self.assertIn("the bar is too dark", text)

    def test_reads_a_file_skipping_bad_lines_and_the_md_name(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "playtest_notes.jsonl"
            p.write_text("\n".join(json.dumps(e) for e in self.sample()) + "\nnot json\n\n", encoding="utf-8")
            (Path(d) / "playtest_notes.md").write_text("# notes\n", encoding="utf-8")
            self.assertEqual(len(pns.load(p)), 8)
            self.assertEqual(len(pns.load(Path(d) / "playtest_notes.md")), 8)
            self.assertEqual(len(pns.load(d)), 8)
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(pns.main([str(p), "--top", "3"]), 0)
                self.assertEqual(pns.main([str(p), "--json"]), 0)
                self.assertEqual(pns.main([str(Path(d) / "missing.jsonl")]), 2)

    def test_an_empty_file_is_fine(self):
        self.assertIn("0 entries", pns.report([]))


if __name__ == "__main__":
    unittest.main()
