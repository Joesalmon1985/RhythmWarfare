"""Tests for tools/extract_openra_sounds.py: the AUD decoder (both formats) on synthetic
files, the WAV writer and the sfx.json manifest.

    python -m unittest discover -s tools -p "test_extract_openra_sounds.py"
"""
from __future__ import annotations

import json
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_openra_sounds as eos  # noqa: E402

SFX_DIR = Path(__file__).resolve().parent.parent / "assets" / "sfx"


def aud_header(rate: int, data_size: int, out_size: int, flags: int, fmt: int) -> bytes:
    return struct.pack("<HiiBB", rate, data_size, out_size, flags, fmt)


def chunk(compressed: bytes, out_size: int) -> bytes:
    return struct.pack("<HHI", len(compressed), out_size, 0xDEAF) + compressed


def ima_encode(samples: list[int]) -> bytes:
    """Closed-loop reference encoder for Westwood's IMA variant: for every target pick the
    nibble whose decoded value (using the decoder's own state machine) is nearest."""
    index = 0
    current = 0
    nibbles = []
    for target in samples:
        best = None
        for nib in range(16):
            s, i2, c2 = eos.ima_decode_nibble(nib, index, current)
            err = abs(s - target)
            if best is None or err < best[0]:
                best = (err, nib, i2, c2)
        _, nib, index, current = best
        nibbles.append(nib)
    if len(nibbles) % 2:
        nibbles.append(0)
    return bytes(nibbles[i] | (nibbles[i + 1] << 4) for i in range(0, len(nibbles), 2))


def make_ima_aud(samples: list[int], rate: int = 22050, chunk_bytes: int = 256) -> bytes:
    body = ima_encode(samples)
    chunks = b""
    for i in range(0, len(body), chunk_bytes):
        part = body[i:i + chunk_bytes]
        chunks += chunk(part, len(part) * 4)
    return aud_header(rate, len(chunks), len(samples) * 2, 0x02, eos.FMT_IMA) + chunks


class DecoderTests(unittest.TestCase):
    def test_ima_ramp_roundtrip(self) -> None:
        # a slow triangle ramp, longer than one chunk so the predictor state must carry across chunks
        up = list(range(0, 6000, 12))
        ramp = up + up[::-1]
        aud = eos.decode_aud(make_ima_aud(ramp, chunk_bytes=100))
        self.assertEqual(aud.fmt, eos.FMT_IMA)
        self.assertEqual(aud.format_name, "ima_adpcm")
        self.assertEqual(aud.rate, 22050)
        self.assertEqual(aud.channels, 1)
        out = struct.unpack(f"<{len(aud.pcm16) // 2}h", aud.pcm16)
        self.assertEqual(len(out), len(ramp))
        err = max(abs(a - b) for a, b in zip(out[50:], ramp[50:]))
        self.assertLess(err, 400)
        self.assertAlmostEqual(aud.seconds, len(ramp) / 22050, places=6)

    def test_ima_odd_sample_count_drops_padding_nibble(self) -> None:
        samples = [i * 20 for i in range(101)]
        aud = eos.decode_aud(make_ima_aud(samples))
        self.assertEqual(aud.frames, 101)

    def test_ima_clamps(self) -> None:
        s, idx, cur = eos.ima_decode_nibble(0x7, 88, 32000)
        self.assertEqual(s, 32767)
        self.assertEqual(idx, 88)
        s, idx, cur = eos.ima_decode_nibble(0xF, 0, -32760)
        self.assertGreaterEqual(s, -32768)

    def test_westwood_all_opcodes(self) -> None:
        # one chunk exercising every opcode; expected values worked out by hand from the tables
        data = bytes([
            0x00, 0xFF,                    # 2-bit deltas: 4 codes of 3 (+1) -> 129..132
            0x40, 0x99,                    # 4-bit: low nibble 9 (+1), high nibble 9 (+1) -> 133, 134
            0xC2,                          # run of 3 copies of the sample -> 134 x3
            0x80 | 1,                      # raw copy of 2 bytes
            10, 200,
            0xA0 | 0x03,                   # small delta +3 from last literal (200) -> 203
            0xA0 | 0x1F,                   # small delta -1 -> 202
        ])
        expected = [129, 130, 131, 132, 133, 134, 134, 134, 134, 10, 200, 203, 202]
        out = eos.ws_decode_chunk(data, len(expected))
        self.assertEqual(list(out), expected)

    def test_westwood_raw_chunk_copy(self) -> None:
        raw = bytes(range(40))
        self.assertEqual(eos.ws_decode_chunk(raw, len(raw)), raw)

    def test_westwood_aud_converts_8bit_to_16bit(self) -> None:
        # ramp 128..(128+63) via 2-bit deltas of +1, in two chunks (state restarts per chunk)
        one = bytes([0x0F]) + bytes([0xFF] * 16)   # opcode 0, count 15: 16 codes of +1,+1,+1,+1
        out_size = 64
        chunks = chunk(one, out_size) + chunk(one, out_size)
        blob = aud_header(11025, len(chunks), 2 * out_size, 0x00, eos.FMT_WS) + chunks
        aud = eos.decode_aud(blob)
        self.assertEqual(aud.format_name, "ws_adpcm")
        self.assertEqual(aud.rate, 11025)
        pcm = struct.unpack(f"<{len(aud.pcm16) // 2}h", aud.pcm16)
        self.assertEqual(len(pcm), 128)
        for i in range(64):
            self.assertEqual(pcm[i], (129 + i - 128) << 8)
            self.assertEqual(pcm[64 + i], (129 + i - 128) << 8)  # each chunk restarts at 0x80

    def test_bad_chunk_magic_rejected(self) -> None:
        blob = aud_header(22050, 12, 8, 0x02, eos.FMT_IMA) + struct.pack("<HHI", 4, 16, 0x1234) + b"\0\0\0\0"
        with self.assertRaises(ValueError):
            eos.decode_aud(blob)

    def test_unknown_format_rejected(self) -> None:
        with self.assertRaises(ValueError):
            eos.decode_aud(aud_header(22050, 0, 0, 0x02, 7) + b"")


class WavTests(unittest.TestCase):
    def test_header(self) -> None:
        pcm = struct.pack("<4h", 1, -2, 3, -4)
        wav = eos.wav_bytes(pcm, 22050, 1)
        self.assertEqual(wav[:4], b"RIFF")
        self.assertEqual(struct.unpack_from("<I", wav, 4)[0], 36 + len(pcm))
        self.assertEqual(wav[8:16], b"WAVEfmt ")
        fmt = struct.unpack_from("<IHHIIHH", wav, 16)
        self.assertEqual(fmt, (16, 1, 1, 22050, 44100, 2, 16))
        self.assertEqual(wav[36:40], b"data")
        self.assertEqual(struct.unpack_from("<I", wav, 40)[0], len(pcm))
        self.assertEqual(wav[44:], pcm)

    def test_stereo_header(self) -> None:
        wav = eos.wav_bytes(b"\0" * 8, 11025, 2)
        fmt = struct.unpack_from("<IHHIIHH", wav, 16)
        self.assertEqual(fmt, (16, 1, 2, 11025, 44100, 4, 16))


class ManifestTests(unittest.TestCase):
    def test_sound_list_names(self) -> None:
        names = [eos.sound_name(f) for f, _, _ in eos.SOUNDS]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("ackno", names)
        self.assertIn("affirm1", names)
        self.assertTrue(all(n == n.lower() for n in names))

    @unittest.skipUnless((SFX_DIR / "sfx.json").exists(), "assets/sfx not extracted")
    def test_manifest_files_exist(self) -> None:
        manifest = json.loads((SFX_DIR / "sfx.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest)
        for name, entry in manifest.items():
            self.assertTrue((SFX_DIR / entry["file"]).is_file(), name)
            self.assertEqual(entry["file"], f"{name}.ogg")
            self.assertIn(entry["format"], ("ws_adpcm", "ima_adpcm"))
            self.assertIn(entry["source"], ("sounds.mix", "speech.mix", "allies.mix"))
            self.assertGreater(entry["seconds"], 0)
            self.assertGreater(entry["rate"], 0)


if __name__ == "__main__":
    unittest.main()
