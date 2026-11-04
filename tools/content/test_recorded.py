"""Tests for tools/content/import_recorded.py: tail folding, and the committed Warehouse pack against its manifest."""
import json
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import import_recorded as ir  # noqa: E402
from common import ROOT, bars_to_frames, read_wav  # noqa: E402


class FoldLoop(unittest.TestCase):
    def test_tail_wraps_onto_the_start_and_nothing_is_lost(self):
        x = np.zeros((1100, 2), dtype=np.float32)
        x[10] = 1.0  # inside a 900-frame loop
        x[1000] = 0.5  # 100 frames past the loop's end: lands on frame 100
        y, info = ir.fold_loop(x, 900)
        self.assertEqual(len(y), 900)
        self.assertEqual(info["tail_frames"], 200)
        self.assertAlmostEqual(float(y.sum()), float(x.sum()), places=5)
        self.assertAlmostEqual(float(y[10, 0]), 1.0)  # the music inside the loop is untouched
        self.assertAlmostEqual(float(y[100, 0]), 0.5)

    def test_short_render_is_padded(self):
        y, info = ir.fold_loop(np.ones((50, 2), dtype=np.float32), 80)
        self.assertEqual(len(y), 80)
        self.assertEqual(info["padded_frames"], 30)


class WarehousePack(unittest.TestCase):
    pack = ROOT / "songs" / "story_n1_warehouse"

    def test_three_loops_are_exactly_eight_bars(self):
        for name in ("drums", "bass", "other"):
            frames, fmt = read_wav(self.pack / "loops" / f"{name}.wav")
            self.assertEqual(len(frames), bars_to_frames(8))
            self.assertEqual(fmt["sample_rate"], 48000)

    def test_report_records_the_verified_tempo(self):
        r = json.loads((self.pack / "timing_report.json").read_text())
        self.assertAlmostEqual(r["timing"]["declared_source_bpm"], 87.0)
        self.assertAlmostEqual(r["timing"]["drums"]["fitted_bpm"], 87.0, delta=0.05)
        self.assertLess(r["timing"]["drums"]["error_ms_at_declared"]["max_abs"], 12.0)
        for n in r["timing"]["bass"]["notes"]:
            self.assertLess(abs(n["error_ms"]), 12.0)
        self.assertEqual(r["loop"]["frames"], bars_to_frames(8))


if __name__ == "__main__":
    unittest.main()
