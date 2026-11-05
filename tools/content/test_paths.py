"""Tests for the path tooling (stage 2): make_path_placeholders.py and beatshaper.py --path.

    python -m unittest discover -s tools/content -p "test_paths.py"
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import beatshaper  # noqa: E402
import make_path_placeholders as mpp  # noqa: E402
from common import ROOT, SAMPLE_RATE  # noqa: E402
from midi_reader import read_midi_bytes  # noqa: E402


def make_path(tmp: Path, bpm: int, genre: str) -> Path:
    paths = tmp / "paths"
    d = paths / "t"
    d.mkdir(parents=True)
    run = {"path": {"id": "t", "title": "T"}, "timing": {"bpm": bpm}, "nodes": [{"id": "t", "scene": "one"}, {"id": "t.two", "scene": "two"}]}
    (d / "run.json").write_text(json.dumps(run), encoding="utf-8")
    (d / "music.json").write_text(json.dumps({"schema": 1, "placeholder": {"genre": genre}, "nodes": []}), encoding="utf-8")
    return paths


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as w:
        assert w.getframerate() == SAMPLE_RATE
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, w.getnchannels()).astype(np.float64) / 32768.0


class Placeholders(unittest.TestCase):
    def test_every_genre_at_its_tempo_is_bass_forward_in_the_pack_format(self):
        for bpm, genre in ((124, "house"), (140, "dubstep"), (145, "psytrance")):
            with tempfile.TemporaryDirectory() as t:
                tmp = Path(t)
                paths = make_path(tmp, bpm, genre)
                out = tmp / "packs"
                done = mpp.generate("t", out, paths_root=paths, imports_root=tmp / "imports")
                self.assertEqual(done, ["t_one", "t_two"])
                p = json.loads((out / "t_one" / "pack.json").read_text(encoding="utf-8"))
                self.assertEqual((p["bpm"], p["path"], p["profile"], p["placeholder"], p["phrase_beats"]), (bpm, "t", "t_x1", True, 32))
                self.assertEqual(p["loop_frames"], round(32 * 60.0 / bpm * SAMPLE_RATE))
                for stem in ("drums", "bass", "other"):
                    x = read_wav(out / "t_one" / p["stems"][stem])
                    self.assertEqual(len(x), p["loop_frames"], f"{genre} {stem}: exactly one loop of frames")
                    self.assertIn(x.shape[1], (1, 2), "mono where the channels are equal (tools/content/stems.py)")
                    self.assertLess(np.abs(x).max(), 1.0)
                lv = p["levels"]
                self.assertGreater(lv["bass"]["rms_db"], lv["drums"]["rms_db"], f"{genre}: the bass is louder than the drums")
                self.assertGreaterEqual(lv["bass"]["rms_db"] - lv["other"]["rms_db"], 8.0, f"{genre}: the bass is clearly the loudest tonal stem")
                self.assertGreaterEqual(lv["bass"]["sub_share"], 0.4, f"{genre}: the sub is there")
                for tier in "1234":  # a chart in every tier, drums and bass
                    self.assertTrue(p["tiers"][tier]["drums"] and p["tiers"][tier]["bass"], f"{genre} tier {tier}")
                for f in ("drums", "bass", "synth"):  # the MIDI the chart was made from
                    m = read_midi_bytes((out / "t_one" / "midi" / f"{f}.mid").read_bytes())
                    self.assertTrue(m["notes"], f)
                m = json.loads((paths / "t" / "music.json").read_text(encoding="utf-8"))
                self.assertEqual([n["temporary"] for n in m["nodes"]], [True, True])
                self.assertEqual(m["placeholder"]["levels_db"]["bass"], -13.0, "the mix levels live in music.json")

    def test_levels_come_from_music_json_and_are_deterministic(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            paths = make_path(tmp, 124, "house")
            m = json.loads((paths / "t" / "music.json").read_text(encoding="utf-8"))
            m["placeholder"]["levels_db"] = {"bass": -10.0}
            (paths / "t" / "music.json").write_text(json.dumps(m), encoding="utf-8")
            mpp.generate("t", tmp / "a", paths_root=paths, imports_root=tmp / "i")
            mpp.generate("t", tmp / "b", paths_root=paths, imports_root=tmp / "i")
            pa = json.loads((tmp / "a" / "t_one" / "pack.json").read_text(encoding="utf-8"))
            self.assertAlmostEqual(pa["levels"]["bass"]["rms_db"], -10.0, places=1)
            stem = lambda root: (root / "t_one" / json.loads((root / "t_one" / "pack.json").read_text(encoding="utf-8"))["stems"]["bass"]).resolve()  # noqa: E731
            self.assertEqual(stem(tmp / "a").read_bytes(), stem(tmp / "b").read_bytes(), "same bytes twice")
            self.assertEqual(stem(tmp / "a").name, stem(tmp / "b").name, "the shared file is named by its content: the same name twice")

    def test_a_scene_with_an_import_gets_no_placeholder(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            paths = make_path(tmp, 140, "dubstep")
            drop = tmp / "imports" / "t" / "TWO"  # the owner's drop for the second scene, named like the scene, case ignored
            drop.mkdir(parents=True)
            (drop / "Beat Shaper - TWO-Drums.wav").write_bytes(b"RIFF")
            done = mpp.generate("t", tmp / "packs", paths_root=paths, imports_root=tmp / "imports")
            self.assertEqual(done, ["t_one"], "only the scene without a drop is synthesised")
            self.assertFalse((tmp / "packs" / "t_two").exists())
            # an imported pack already on disk (not ours) is never overwritten, even with --force
            (tmp / "packs" / "t_one" / "pack.json").write_text(json.dumps({"id": "t_one", "bpm": 140, "path": "t"}), encoding="utf-8")
            self.assertEqual(mpp.generate("t", tmp / "packs", force=True, paths_root=paths, imports_root=tmp / "imports"), [])


class BeatshaperPath(unittest.TestCase):
    def tearDown(self):
        beatshaper.PATH_ID = ""
        beatshaper.BPM = 174
        beatshaper.MUSIC_JSON = ROOT / "content" / "story" / "music.json"
        beatshaper.RUN_JSON = ROOT / "content" / "run" / "run.json"
        beatshaper.PROFILES.clear()
        beatshaper.PROFILES.update({"beat_shaper_87x2": {"source_bpm": 87.0, "scale": 2, "verified_on": "Lv1 Warehouse"},
                                    "beat_shaper_174x1": {"source_bpm": 174.0, "scale": 1, "verified_on": "Lv2 Alien Spaceship"}})

    def test_select_path_takes_the_tempo_and_profile_of_the_path(self):
        beatshaper.select_path("stub")
        self.assertEqual((beatshaper.BPM, beatshaper.PATH_ID), (124, "stub"))
        self.assertEqual(list(beatshaper.PROFILES), ["stub_x1"])
        self.assertEqual(beatshaper.PROFILES["stub_x1"]["source_bpm"], 124.0)
        errors, _ = beatshaper.validate()
        self.assertEqual(errors, [], "the stub path validates at its own tempo")

    def test_a_planned_path_works_before_its_run_json_exists(self):
        beatshaper.select_path("squadron")
        self.assertEqual(beatshaper.BPM, 140)
        beatshaper.select_path("squadron", 140)
        with self.assertRaises(beatshaper.ContentError):
            beatshaper.select_path("nowhere")

    def test_validate_refuses_a_pack_at_the_wrong_tempo(self):
        with tempfile.TemporaryDirectory() as t:
            packs = Path(t) / "packs"
            shutil.copytree(ROOT / "songs" / "packs" / "stub_start", packs / "stub_start")
            pj = packs / "stub_start" / "pack.json"
            p = json.loads(pj.read_text(encoding="utf-8"))
            p["bpm"] = 174
            pj.write_text(json.dumps(p), encoding="utf-8")
            beatshaper.select_path("stub")
            errors, _ = beatshaper.validate(packs_dir=packs)
            self.assertTrue(any("174 BPM, the path stub is 124" in e for e in errors), errors)

    def test_the_main_validate_ignores_path_packs(self):
        errors, notes = beatshaper.validate()
        self.assertEqual(errors, [])
        self.assertFalse(any("stub_start" in n for n in notes))


if __name__ == "__main__":
    unittest.main()
