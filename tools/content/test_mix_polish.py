"""Tests for the audio polish (docs/HANDOVER.md "Audio polish"): the offline mix model (tools/run/measure_mix.py) and the rules it holds the shipped data to.

    python -m unittest tools/content/test_mix_polish.py

The master peak rule renders every scene of the main run and of every path the way RunAudio plays it (about a minute and a half).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "run"))
sys.path.insert(0, str(ROOT / "tools" / "content"))

import measure_mix as mm  # noqa: E402
import make_path_placeholders as mpp  # noqa: E402

PEAK_LIMIT_DB = -0.5


class BassBusModel(unittest.TestCase):
    def setUp(self):
        t = np.arange(48000) / 48000.0
        x = 0.5 * np.sin(2 * np.pi * 55 * t) + 0.1 * np.sin(2 * np.pi * 440 * t)
        self.x = np.stack([x, x], axis=1)

    def test_a_disabled_bus_is_the_player_gain_only(self):
        bb = {**mm.DEFAULT_BUS, "enabled": False, "drive": 0.8, "shelf_db": 6.0}
        np.testing.assert_allclose(mm.bass_bus(self.x, 0.7, bb), self.x * 0.7)

    def test_an_enabled_bus_with_nothing_set_passes_the_signal(self):
        bb = {**mm.DEFAULT_BUS, "enabled": True}
        np.testing.assert_allclose(mm.bass_bus(self.x, 1.0, bb), self.x, atol=1e-9)

    def test_the_waveshaper_never_exceeds_its_post_gain(self):
        bb = {**mm.DEFAULT_BUS, "enabled": True, "drive": 0.9, "pre_gain_db": 20.0, "gain_db": -6.0}
        y = mm.bass_bus(self.x, 1.0, bb)
        self.assertLessEqual(float(np.abs(y).max()), 10 ** (-6 / 20) + 0.03, "a soft clipper: bounded by the post gain (plus the little above keep_hf_hz that passes unshaped)")

    def test_a_low_shelf_lifts_the_sub_and_leaves_the_top(self):
        bb = {**mm.DEFAULT_BUS, "enabled": True, "shelf_hz": 100.0, "shelf_db": 6.0}
        y = mm.bass_bus(self.x, 1.0, bb)
        lo = mm.band_energy(y, 40, 70) / mm.band_energy(self.x, 40, 70)
        hi = mm.band_energy(y, 400, 480) / mm.band_energy(self.x, 400, 480)
        self.assertGreater(10 * np.log10(lo), 4.0)
        self.assertLess(abs(10 * np.log10(hi)), 0.6)

    def test_a_scene_override_is_merged_key_by_key(self):
        mix = mm.merged_mix({"gain_db": 2.0, "bass_bus": {"enabled": True, "drive": 0.6, "shelf_db": 2.0}}, {"bass_bus": {"drive": 0.4}})
        bb = mm.bass_bus_of(mix, {"shelf_db": 4.0, "note": "why"})
        self.assertEqual((bb["drive"], bb["shelf_db"], bb["enabled"], mix["gain_db"]), (0.4, 4.0, True, 2.0))
        self.assertNotIn("note", bb)


class ShippedMix(unittest.TestCase):
    def test_no_scene_of_any_run_clips_the_master(self):
        worst = []
        for rid in mm.RUNS:
            R = mm.load_run(rid)
            for nid in R["order"]:
                pk = mm._db(float(np.abs(mm.render(R, nid)["mix"]).max()))
                worst.append((pk, rid, nid))
            mm._BUSSED.clear()
        bad = [w for w in worst if w[0] > PEAK_LIMIT_DB]
        self.assertEqual(bad, [], f"scenes over {PEAK_LIMIT_DB} dBFS before any limiter (the run has none): {bad}")

    def test_every_scene_has_a_bass_bus_and_a_family(self):
        for rid in mm.RUNS:
            R = mm.load_run(rid)
            for nid, n in R["nodes"].items():
                self.assertEqual(set(n["bass_bus"]), set(mm.DEFAULT_BUS), f"{rid} {nid}")
                self.assertTrue(n["family"], f"{rid} {nid}")
            for k in ("gain_db", "dip_gain", "dip_beats", "recipe_bass_floor", "carry_bass", "bass_bus"):
                self.assertIn(k, R["run"]["mix"], f"{rid}: mix.{k}")


class PlaceholderBass(unittest.TestCase):
    def test_every_genre_has_a_sub_and_a_mid_layer_a_phone_can_play(self):
        for genre, v in mpp.BASS_VOICES.items():
            for midi in (28, 33, 37):
                x = mpp.bass_note(mpp.hz(midi), 0.4, 0.0, voice=v)
                tot = mm.band_energy(x, 0, 24000)
                self.assertGreaterEqual(mm.band_energy(x, 0, 90) / tot, 0.4, f"{genre} {midi}: the sub")
                self.assertGreaterEqual(mm.band_energy(x, 150, 1000) / tot, 0.28, f"{genre} {midi}: the mid layer (what a phone speaker plays)")

    def test_the_psytrance_bass_is_a_pulse(self):
        x = mpp.bass_note(mpp.hz(28), 0.09, 0.0, voice=mpp.BASS_VOICES["psytrance"])
        n = int(0.02 * 48000)
        start, end = float(np.sqrt((x[:n] ** 2).mean())), float(np.sqrt((x[4 * n:5 * n] ** 2).mean()))
        self.assertGreater(20 * np.log10(start / end), 4.0, "every sixteenth decays: a clear pulse between the kicks")


if __name__ == "__main__":
    unittest.main()
