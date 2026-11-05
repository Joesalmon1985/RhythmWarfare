"""tools/content/stems.py: mono where the channels are equal, one shared file per distinct stem, nothing audible changes."""
import json
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import stems  # noqa: E402


def write(path: Path, pcm: np.ndarray, rate: int = 48000) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(stems.wav_bytes(pcm, rate))


def make_pack(root: Path, name: str, drums: np.ndarray, bass: np.ndarray, other: np.ndarray) -> Path:
    d = root / name
    for k, x in (("drums", drums), ("bass", bass), ("other", other)):
        write(d / "loops" / f"{k}.wav", x)
    pack = {"schema": 1, "id": name, "stems": {k: f"loops/{k}.wav" for k in ("drums", "bass", "other")}, "loops": {"drums": {"loop_frames": 100}}}
    (d / "pack.json").write_text(json.dumps(pack, indent=1) + "\n", encoding="utf-8")
    return d


def pcm_of(pack_dir: Path, stem: str):
    return stems.read_pcm(stems.stem_files(pack_dir)[stem])[0]


class Stems(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(3)
        self.mono = rng.integers(-20000, 20000, size=(100, 1)).astype("<i2")
        self.dual = np.repeat(self.mono, 2, axis=1)
        self.stereo = rng.integers(-20000, 20000, size=(100, 2)).astype("<i2")

    def test_dual_mono_becomes_mono_true_stereo_stays_and_equal_stems_share_one_file(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            a = make_pack(root, "a", self.dual, self.dual, self.stereo)
            b = make_pack(root, "b", self.dual, self.dual[::-1].copy(), self.stereo)
            for p in (a, b):
                stems.finish_pack(p)
            self.assertFalse((a / "loops").exists(), "the emptied loops folder is removed")
            self.assertEqual(pcm_of(a, "drums").shape, (100, 1))
            self.assertEqual(pcm_of(a, "other").shape, (100, 2))
            self.assertEqual(stems.stem_files(a)["drums"], stems.stem_files(b)["drums"], "the same drums are one file")
            self.assertNotEqual(stems.stem_files(a)["bass"], stems.stem_files(b)["bass"])
            self.assertEqual(len(list((root / "_shared").glob("*.wav"))), 4, "drums, bass x2, other")
            # not one sample changed: both channels of the original are what the stored stem plays
            self.assertTrue(np.array_equal(pcm_of(a, "drums")[:, 0], self.dual[:, 0]))
            self.assertTrue(np.array_equal(pcm_of(b, "bass")[:, 0], self.dual[::-1][:, 1]))
            self.assertTrue(np.array_equal(pcm_of(a, "other"), self.stereo))
            self.assertEqual(json.loads((a / "pack.json").read_text())["loops"], {"drums": {"loop_frames": 100}}, "the rest of the manifest is untouched")
            self.assertTrue(stems.read_pcm(stems.stem_files(a)["drums"])[1] == 48000)

    def test_idempotent_and_prune(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            a = make_pack(root, "a", self.dual, self.dual, self.stereo)
            stems.finish_pack(a)
            first = {p.name: p.read_bytes() for p in (root / "_shared").glob("*.wav")}
            manifest = (a / "pack.json").read_text()
            stems.finish_pack(a)
            self.assertEqual({p.name: p.read_bytes() for p in (root / "_shared").glob("*.wav")}, first)
            self.assertEqual((a / "pack.json").read_text(), manifest)
            self.assertEqual(stems.prune_shared(root), [], "everything is referenced")
            (root / "_shared" / "bass_000000000000.wav").write_bytes(b"x")
            (root / "_shared" / "bass_000000000000.wav.import").write_text("x")
            self.assertEqual(stems.prune_shared(root), ["bass_000000000000.wav"])
            self.assertFalse((root / "_shared" / "bass_000000000000.wav.import").exists())


if __name__ == "__main__":
    unittest.main()
