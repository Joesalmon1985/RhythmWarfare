"""Clip lengths other than 8 bars in the loop library (Cold/Meta imports): a 4-bar bass line is tiled over its 8-bar loop, a render longer than its
pattern is cut (and the cut is recorded), an atonal percussion backing needs no key, and an owner's folder beside the checkout is found by name."""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import import_ableton as ia  # noqa: E402
from common import ContentError, TICKS_PER_BAR, bars_to_frames, read_json, read_wav, write_json  # noqa: E402
from import_ableton import Importer  # noqa: E402
from test_import import BAR_S, SR_IN, ImportWorkspace, clicks, midi96, sine, wav44  # noqa: E402


class ClipLengths(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = ImportWorkspace()
        Importer(self.ws.manifest, library=self.ws.lib, sounds_path=self.ws.sounds).run()
        bar96 = 96 * 4
        src = self.ws.src
        # a 4-bar pattern: F for two bars, A# for one, C for one; the second render is 16 bars of it (the pattern repeated), the first rings on for 0.5 bar
        midi96(src / "Bass4.mid", [(0, 2 * bar96, 41), (2 * bar96, bar96, 46), (3 * bar96, bar96, 48)])
        wav44(src / "bass4a.wav", np.vstack([sine(4, level=0.6), sine(0.5, level=0.2)]))
        wav44(src / "bass16.wav", sine(16, level=0.6))
        wav44(src / "Other16.wav", clicks(16, [0, 2], level=0.5))
        self.manifest = self.ws.tmp / "manifest2.json"
        write_json(self.manifest, {
            "source_dir": str(src), "bars": 8, "trim_db": -8.0, "end_fade_ms": 10,
            "levels": {"bass": {"peak_db": -4.0, "rms_db": -17.0}, "other": {"peak_db": -3.0}},
            "clips": [
                {"id": "t_bass_four", "kind": "bass", "name": "Bass Four", "key": "F minor", "bars": 4, "parts": {
                    "bass": {"midi": "Bass4.mid", "renders": {"t_bass_a": "bass4a.wav", "t_bass_b": {"file": "bass16.wav", "tail_bars": 0}}}}},
                {"id": "t_acc_perc", "kind": "accompaniment", "name": "Perc Sixteen", "audio_only": True, "atonal": True, "bars": 16, "tail_bars": 0, "parts": {
                    "other": {"renders": {"t_other_1": "Other16.wav"}}}},
            ]})

    def tearDown(self) -> None:
        self.ws.close()

    def run_import(self) -> Importer:
        imp = Importer(self.manifest, library=self.ws.lib, sounds_path=self.ws.sounds)
        imp.run()
        return imp

    def test_clip_length_tail_and_cut_are_per_clip(self) -> None:
        imp = self.run_import()
        clip = read_json(self.ws.lib / "t_bass_four" / "clip.json")
        self.assertEqual(clip["bars"], 4)
        a, _ = read_wav(self.ws.lib / "t_bass_four" / "bass__t_bass_a.wav")
        b, _ = read_wav(self.ws.lib / "t_bass_four" / "bass__t_bass_b.wav")
        self.assertAlmostEqual(len(a), bars_to_frames(4) + 0.5 * BAR_S * 48000, delta=30, msg="the 4 bars plus the half bar that still rings")
        self.assertEqual(len(b), bars_to_frames(4), "tail_bars 0: the 16-bar render is cut at the clip's 4 bars")
        rend = clip["source"]["renders"]["bass__t_bass_b"]
        self.assertEqual(rend["bars_in"], 16.0, "the cut is recorded, nothing is dropped silently")
        self.assertGreater(rend["dropped_frames"], 0)
        self.assertNotIn("dropped_frames", clip["source"]["renders"]["bass__t_bass_a"], "a render that fits loses nothing")
        self.assertFalse([w for w in imp.warnings if "bass16" in w], "a deliberate cut is not a warning")
        self.assertEqual(clip["source"]["parts"]["bass"]["bars"], [1, 4])

    def test_a_four_bar_bass_is_tiled_over_the_loop_and_charted_twice(self) -> None:
        self.run_import()
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        entry = res["index"]["clips"]["t_bass_four"]
        self.assertEqual(entry["bars"], 8, "the game plays 8-bar loops")
        cues = entry["cues"]["bass"]
        half = [c for c in cues if c[0] < 4 * TICKS_PER_BAR]
        rest = [[c[0] - 4 * TICKS_PER_BAR, c[1], c[2]] for c in cues if c[0] >= 4 * TICKS_PER_BAR]
        self.assertTrue(half)
        self.assertEqual(half, rest, "the pattern repeats in bars 5 to 8")
        self.assertEqual(sorted(entry["sounds"]["bass"]), ["t_bass_a", "t_bass_b"])
        # the 4-bar render tiled: the loop is 8 bars and the second copy starts at bar 5
        import subprocess
        ogg = self.ws.songs / "library" / entry["loops"]["bass"]["t_bass_b"]
        raw = Path(tempfile.mkdtemp()) / "x.f32"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(ogg), "-f", "f32le", "-ac", "2", str(raw)], check=True)
        samples = np.frombuffer(raw.read_bytes(), dtype="<f4").reshape(-1, 2)
        self.assertAlmostEqual(len(samples), bars_to_frames(8), delta=1200)

    def test_atonal_backing_has_no_key_and_a_sixteen_bar_loop(self) -> None:
        self.run_import()
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        entry = res["index"]["clips"]["t_acc_perc"]
        self.assertEqual(entry["key"], "")
        self.assertEqual(entry["bars"], 16)

    def test_a_pitched_backing_still_needs_its_key_and_atonal_is_only_for_percussion(self) -> None:
        self.run_import()
        clip = self.ws.lib / "t_acc_perc" / "clip.json"
        d = read_json(clip)
        d.pop("atonal")
        write_json(clip, d)
        res = self.ws.build()
        self.assertFalse(res["ok"])
        self.assertTrue(any("declare their key" in e for e in res["errors"]), res["errors"])
        bass = self.ws.lib / "t_bass_four" / "clip.json"
        d2 = read_json(bass)
        d2["atonal"] = True
        write_json(bass, d2)
        d["atonal"] = True
        write_json(clip, d)
        res = self.ws.build()
        self.assertFalse(res["ok"])
        self.assertTrue(any("only an audio_only accompaniment" in e for e in res["errors"]), res["errors"])

    def test_a_bass_line_must_tile_the_loop(self) -> None:
        import chart
        from types import SimpleNamespace
        notes = [{"tick": 0, "duration_ticks": 960, "pitch": 40, "velocity": 100}]
        clip = SimpleNamespace(id="x", kind="bass", bars=3, audio_only=False, notes={"bass": notes}, length_ticks=3 * TICKS_PER_BAR,
                               cue_notes=lambda part: notes)
        with self.assertRaises(ContentError) as ctx:
            chart.clip_cues(clip, "bass", chart.load_rules())
        self.assertIn("does not tile an 8-bar loop", str(ctx.exception))
        clip.bars, clip.length_ticks = 2, 2 * TICKS_PER_BAR
        self.assertEqual([c[0] for c in chart.clip_cues(clip, "bass", chart.load_rules())], [k * 2 * TICKS_PER_BAR for k in range(4)])

    def test_a_relative_source_folder_is_found_beside_the_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            owner = Path(tmp) / "Owner" / "Cold"
            owner.mkdir(parents=True)
            project = Path(tmp) / "work" / "checkout"
            project.mkdir(parents=True)
            saved = ia.ROOT
            ia.ROOT = project
            try:
                self.assertEqual(ia.resolve_source("Owner/Cold"), owner)
                self.assertEqual(ia.resolve_source("Missing"), project / "Missing")
            finally:
                ia.ROOT = saved
            self.assertEqual(ia.resolve_source(str(owner)), owner)

    def test_trim_keeps_a_tail_only_up_to_tail_bars(self) -> None:
        frames = np.vstack([sine(4, level=0.5), sine(2, level=0.5)])
        out, info = ia.trim_to_clip(frames.astype(np.float32), 4, 1)
        self.assertEqual(len(out), bars_to_frames(5))
        self.assertTrue(info["tail_cut_while_sounding"])
        out0, info0 = ia.trim_to_clip(frames.astype(np.float32), 4, 0)
        self.assertEqual(len(out0), bars_to_frames(4))
        self.assertFalse(info0["tail_cut_while_sounding"])
        with self.assertRaises(ContentError):
            ia.trim_to_clip(sine(3).astype(np.float32), 4)


if __name__ == "__main__":
    unittest.main()
