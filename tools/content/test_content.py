"""Tests of the owner content path: the one build command, drop-in WAV renders, edited MIDI, validation and assembly.

    python -m unittest discover -s tools/content -p "test_*.py"      (tools/test.sh runs it too)

Every test builds into a temporary copy of the library (never the real content/ or songs/), using the fixtures in
content/fixtures/ (see make_fixtures.py).
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

import build  # noqa: E402
from common import (CONTENT, LIBRARY, TICKS_PER_BAR, bars_to_frames, read_json, read_wav, sha256_file, tick_to_sample,  # noqa: E402
                    write_json, write_midi, write_wav)
from library import Library  # noqa: E402
import mission as mission_mod  # noqa: E402

FIX = CONTENT / "fixtures"
CLIPS = ["groove_watch", "groove_straight", "bass_hold_b"]


class Workspace:
    """A throwaway content tree: a few library clips, the fixture mission, its own state, report and songs."""

    def __init__(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="rw_content_"))
        self.lib = self.tmp / "library"
        for c in CLIPS:
            shutil.copytree(LIBRARY / c, self.lib / c, ignore=shutil.ignore_patterns("placeholder"))
        shutil.copytree(FIX / "example_groove", self.lib / "example_groove")
        self.missions = self.tmp / "missions"
        self.missions.mkdir()
        shutil.copy(FIX / "mission_fixture.json", self.missions / "level_fixture.json")
        self.songs = self.tmp / "songs"
        self.state = self.tmp / "build_state.json"

    def build(self) -> dict:
        return build.run(library=self.lib, missions=self.missions, songs=self.songs, sounds=CONTENT / "sounds.json",
                         state=self.state, report=self.tmp / "REPORT.md", quiet=True)

    def level(self) -> dict:
        return read_json(self.songs / "fixture_mission" / "level.json")

    def close(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


def kick_cues(level: dict, option: str = "groove_watch") -> list:
    out = []
    for b in level["cue_blocks"]:
        if b["family"] == "kick":
            out += b["options"][option]
    return sorted(out)


class ContentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Workspace()

    def tearDown(self) -> None:
        self.ws.close()

    def test_placeholder_build_is_complete_and_labelled(self):
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        lv = self.ws.level()
        self.assertTrue(lv["placeholder"])
        self.assertEqual(lv["content"]["owner_files"], 0)
        for s in lv["stems"]:
            for f in s["files"].values():
                self.assertTrue((self.ws.songs / "fixture_mission" / f["file"]).exists())
        self.assertTrue((self.ws.lib / "groove_watch" / "placeholder" / "kick__kick_march.wav").exists())
        self.assertIn("groove", lv["previews"], "every offered option has an audition")
        self.assertEqual(len(kick_cues(lv)), 8, "8 bars of the two-bar groove: one kick per bar")

    def test_owner_wav_replaces_the_placeholder_without_touching_either_file(self):
        self.assertTrue(self.ws.build()["ok"])
        ph = self.ws.lib / "groove_watch" / "placeholder" / "kick__kick_march.wav"
        ph_hash = sha256_file(ph)
        stem_before = self._stem_bytes("kick", "groove_watch|kick_march")
        owner = self.ws.lib / "groove_watch" / "kick__kick_march.wav"
        shutil.copy(FIX / "replacement" / "groove_watch" / "kick__kick_march.wav", owner)
        owner_hash = sha256_file(owner)
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        lv = self.ws.level()
        f = self._stem_entry(lv, "kick", "groove_watch|kick_march")
        self.assertFalse(f["placeholder"], "the owner render is used")
        self.assertEqual(lv["content"]["owner_files"], 1)
        self.assertNotEqual(self._stem_bytes("kick", "groove_watch|kick_march"), stem_before)
        self.assertEqual(sha256_file(owner), owner_hash, "the build never writes an owner file")
        self.assertEqual(sha256_file(ph), ph_hash, "the reference placeholder stays")
        self.assertTrue(self._stem_entry(lv, "kick", "groove_watch|kick_armour")["placeholder"], "other sounds stay placeholder")
        report = (self.ws.tmp / "REPORT.md").read_text()
        self.assertIn("owner `", report)
        owner.unlink()
        self.assertTrue(self.ws.build()["ok"])
        self.assertTrue(self._stem_entry(self.ws.level(), "kick", "groove_watch|kick_march")["placeholder"], "deleting it reverts to the placeholder")

    def test_edited_midi_regenerates_cues_and_flags_a_stale_render(self):
        owner = self.ws.lib / "groove_watch" / "kick__kick_march.wav"
        shutil.copy(FIX / "replacement" / "groove_watch" / "kick__kick_march.wav", owner)
        self.assertTrue(self.ws.build()["ok"])
        before = kick_cues(self.ws.level())
        ph = self.ws.lib / "groove_watch" / "placeholder" / "kick__kick_armour.wav"
        ph_before = sha256_file(ph)
        edited = FIX / "replacement" / "groove_watch" / "kick.mid"
        shutil.copy(edited, self.ws.lib / "groove_watch" / "kick.mid")
        res = self.ws.build()
        self.assertFalse(res["ok"], "a render made from the old MIDI is rejected")
        self.assertTrue(any("rendered from an earlier kick.mid" in e for e in res["errors"]), res["errors"])
        owner.unlink()
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        after = kick_cues(self.ws.level())
        self.assertEqual(len(after), len(before) + 4, "the extra kick in each of the four loops is a new cue")
        self.assertIn([2880, 0], after)
        self.assertEqual(sha256_file(self.ws.lib / "groove_watch" / "kick.mid"), sha256_file(edited), "the edited MIDI is kept")
        self.assertNotEqual(sha256_file(ph), ph_before, "placeholders follow the new MIDI")
        self.assertEqual(res["library"].clips["groove_watch"].midi_origin["kick"], "owner_edited")
        self.assertEqual(res["library"].clips["groove_watch"].tempo_source["kick"], "recorded_default", "no tempo in the file: 174 BPM recorded")
        shutil.copy(FIX / "replacement" / "groove_watch" / "kick__kick_march.wav", owner)
        self.assertTrue(self.ws.build()["ok"], "a render dropped in after the MIDI edit is accepted against the new MIDI")

    def test_copied_example_folder_becomes_a_choice(self):
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        lv = self.ws.level()
        groove = next(c for c in lv["choices"] if c["id"] == "groove")
        self.assertIn({"id": "example_groove", "name": "Example Groove"}, groove["pool"])
        self.assertTrue((self.ws.songs / "fixture_mission" / "preview" / "groove__example_groove.ogg").exists())
        self.assertEqual(kick_cues(lv, "example_groove")[:3], [[0, 0], [2400, 0], [3840, 0]])

    def test_bad_renders_are_rejected_with_a_helpful_message(self):
        good, _ = read_wav(FIX / "replacement" / "groove_watch" / "kick__kick_march.wav")
        owner = self.ws.lib / "groove_watch" / "kick__kick_march.wav"
        cases = {
            "44100 Hz": lambda p: self._raw_wav(p, good, rate=44100),
            "channel": lambda p: self._raw_wav(p, good[:, :1], channels=1),
            "24-bit": lambda p: self._raw_wav(p, good, width=3),
            "shorter than": lambda p: write_wav(p, good[: bars_to_frames(1)]),
            "longer than": lambda p: write_wav(p, np.vstack([good, good])),
            "silent": lambda p: write_wav(p, good * 0.0),
        }
        for needle, make in cases.items():
            make(owner)
            res = self.ws.build()
            self.assertFalse(res["ok"], needle)
            self.assertTrue(any(needle in e for e in res["errors"]), (needle, res["errors"]))
        owner.unlink()

    def test_bad_midi_is_rejected(self):
        mid = self.ws.lib / "groove_watch" / "snare.mid"
        import mido
        m = mido.MidiFile(type=1, ticks_per_beat=960)
        t = mido.MidiTrack()
        t.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(170), time=0))
        t.append(mido.Message("note_on", note=38, velocity=100, time=1920))
        t.append(mido.Message("note_off", note=38, velocity=0, time=120))
        m.tracks.append(t)
        m.save(str(mid))
        res = self.ws.build()
        self.assertFalse(res["ok"])
        self.assertTrue(any("170.00 BPM" in e for e in res["errors"]), res["errors"])
        t[0] = mido.MetaMessage("time_signature", numerator=3, denominator=4, time=0)
        m.save(str(mid))
        res = self.ws.build()
        self.assertTrue(any("4/4" in e for e in res["errors"]), res["errors"])

    def test_a_hold_through_a_sequence_boundary_is_rejected(self):
        bass = self.ws.lib / "bass_hold_b" / "bass.mid"
        write_midi(bass, [{"tick": 3 * TICKS_PER_BAR, "duration_ticks": 2 * TICKS_PER_BAR, "pitch": 37, "velocity": 100}], "bad bass")
        m = read_json(self.ws.missions / "level_fixture.json")
        m["choices"]["bass_voice"] = {"count": 1, "pool": ["bass_patrol"], "default": ["bass_patrol"]}
        m["phases"][1] = {"bars": 4, "mode": "bass", "groove": 1, "kick_sound": 1, "snare_sound": "snare_guard", "bass": "bass_hold_b",
                          "bass_voice": 1, "sequence_bars": 4, "rewards": ["e3"]}
        m["bars"] = 12
        m["phases"].append({"bars": 4, "mode": "drums", "groove": 1, "kick_sound": 1, "snare_sound": "snare_guard", "sequence_bars": 4, "rewards": ["pillbox"]})
        write_json(self.ws.missions / "level_fixture.json", m)
        res = self.ws.build()
        self.assertFalse(res["ok"])
        self.assertTrue(any("runs past the phase end" in e or "crosses the sequence boundary" in e for e in res["errors"]), res["errors"])

    def test_assembly_places_every_loop_on_its_exact_sample_without_drift(self):
        lib = Library(self.ws.lib, CONTENT / "sounds.json", self.ws.state).load()
        clicks = np.zeros((bars_to_frames(3), 2), dtype=np.float32)
        clicks[0] = 0.9
        clicks[tick_to_sample(TICKS_PER_BAR)] = 0.5
        write_wav(self.ws.lib / "groove_watch" / "kick__kick_march.wav", clicks)
        lib = Library(self.ws.lib, CONTENT / "sounds.json", self.ws.state).load()
        m = mission_mod.Mission(self.ws.missions / "level_fixture.json", lib)
        m.parse()
        m.arrange()
        u = next(u for u in m.usages.values() if u.family == "kick")
        frames, ph = m._render_usage(u, "groove_watch", "kick_march", bars_to_frames(9))
        self.assertFalse(ph)
        loud = np.nonzero(frames[:, 0] > 0.8)[0].tolist()
        self.assertEqual(loud, [tick_to_sample(2 * TICKS_PER_BAR * k) for k in range(4)], "loop starts land on exact sample frames")
        half = np.nonzero(np.abs(frames[:, 0] - 0.5) < 0.01)[0].tolist()
        want = [tick_to_sample((2 * k + 1) * TICKS_PER_BAR) for k in range(4)]
        self.assertEqual(len(half), 4)
        for got, exp in zip(half, want):  # inside a clip the render keeps its own timing: one-sample rounding, never growing
            self.assertLessEqual(abs(got - exp), 1)

    def test_real_campaign_sources_are_untouched(self):
        integrity = read_json(CONTENT.parent / "campaign" / "Musical_Source_Integrity.json")["after_sha256"]
        for key, digest in integrity.items():
            path = CONTENT.parent / "campaign" / key
            if path.suffix == ".mid" and path.exists():
                self.assertEqual(sha256_file(path), digest, key)

    # --- helpers ---
    def _stem_entry(self, lv: dict, family: str, key: str) -> dict:
        for s in lv["stems"]:
            if s["family"] == family and key in s["files"]:
                return s["files"][key]
        raise AssertionError(f"no {family} stem for {key}")

    def _stem_bytes(self, family: str, key: str) -> bytes:
        f = self._stem_entry(self.ws.level(), family, key)
        return (self.ws.songs / "fixture_mission" / f["file"]).read_bytes()

    @staticmethod
    def _raw_wav(path: Path, frames: np.ndarray, rate: int = 48000, channels: int = 2, width: int = 2) -> None:
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(width)
            wf.setframerate(rate)
            if width == 2:
                wf.writeframes((np.clip(frames, -1, 1) * 32767).astype("<i2").tobytes())
            else:
                ints = (np.clip(frames, -1, 1) * 8388607).astype("<i4").reshape(-1)
                wf.writeframes(b"".join(int(v).to_bytes(4, "little", signed=True)[:3] for v in ints[:20000]))


if __name__ == "__main__":
    unittest.main()
