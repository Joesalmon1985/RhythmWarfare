"""Tests for tools/content/catalogue.py with synthetic exports: discovery, pairing, tempo at both profiles, tails, roles, MIDI facts, keys, loudness,
compatibility rules and the determinism of the output. No real recordings are needed."""
import json
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import catalogue as cat  # noqa: E402
from midi_reader import build_midi, ev_note_off, ev_note_on  # noqa: E402
from test_beatshaper import export_set  # noqa: E402

SR_IN = 44100


def wav44(frames: np.ndarray, width: int = 2) -> bytes:
    """A 44.1 kHz stereo PCM WAV like the Ableton renders."""
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(width)
        wf.setframerate(SR_IN)
        wf.writeframes((np.clip(frames, -1, 1) * 32767).astype("<i2").tobytes())
    return buf.getvalue()


def ableton_midi(notes: list[tuple]) -> bytes:
    """(beat, pitch, length) notes at 96 PPQ with no tempo event: Ableton's clip export."""
    ev = []
    for beat, pitch, ln in notes:
        ev += [ev_note_on(round(beat * 96), pitch, 100), ev_note_off(round((beat + ln) * 96), pitch)]
    return build_midi(96, [ev], 0)


def stereo(x: np.ndarray) -> np.ndarray:
    return np.stack([x, x], axis=1)


def clicks(beats: list[float], seconds: float, bpm: float = 174.0, amp: float = 0.8) -> np.ndarray:
    n = int(seconds * SR_IN)
    out = np.zeros(n)
    rng = np.random.default_rng(3)
    for b in beats:
        i = int(b * 60.0 / bpm * SR_IN)
        m = int(0.03 * SR_IN)
        if i + m < n:
            out[i:i + m] += amp * rng.standard_normal(m) * np.exp(-np.arange(m) / (0.006 * SR_IN))
    return out


def tones(seq: list[tuple], seconds: float, bpm: float = 174.0, tail: float = 0.0) -> np.ndarray:
    """(beat, pitch, length in beats) as sine notes with a release of `tail` seconds."""
    n = int(seconds * SR_IN)
    out = np.zeros(n)
    t = np.arange(n) / SR_IN
    for beat, pitch, ln in seq:
        a, z = int(beat * 60.0 / bpm * SR_IN), int((beat + ln) * 60.0 / bpm * SR_IN)
        f = 440.0 * 2 ** ((pitch - 69) / 12)
        env = np.ones(z - a)
        sig = 0.4 * np.sin(2 * np.pi * f * t[a:z]) * env
        out[a:z] += sig
        if tail:
            m = min(int(tail * SR_IN), n - z)
            if m > 0:
                out[z:z + m] += 0.4 * np.sin(2 * np.pi * f * t[z:z + m]) * np.exp(-np.arange(m) / (0.15 * SR_IN))
    return out


BAR = 4 * 60.0 / 174.0


class Fixture(unittest.TestCase):
    """A source folder with two Beat Shaper sets (174 and 87), an Ableton pattern family with timbres and tails, an audio-only loop and noise files."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        cls.repo = root / "repo"
        cls.repo.mkdir()
        cls.src = root / "Owner"
        sub = cls.src / "Cold"
        sub.mkdir(parents=True)
        for name, data in export_set(174.0, project="Lv9 Fast").items():
            (sub / name).write_bytes(data)
        for name, data in export_set(174.0, project="Lv9 Fast", suffix="1").items():
            (sub / name).write_bytes(data)
        for name, data in export_set(87.0, project="Lv8 Slow").items():
            (cls.src / name).write_bytes(data)
        # Ableton: a 4-bar kick pattern whose MIDI runs 8 bars (the second half repeats), a bass pattern with two timbres, a snare, an audio-only loop
        kick_notes = [(0, 67, 0.4), (2.5, 67, 0.4), (4, 67, 0.4), (6.5, 67, 0.4), (8, 67, 0.4), (10.5, 67, 0.4), (12, 67, 0.4), (15, 67, 0.4)]
        kick_notes += [(b + 16, p, d) for b, p, d in kick_notes]
        (sub / "Kick2.mid").write_bytes(ableton_midi(kick_notes))
        kick = clicks([n[0] for n in kick_notes[:8]], 4 * BAR + 0.3, amp=1.4)
        (sub / "Kick2.wav").write_bytes(wav44(stereo(kick)))
        (sub / "Snare2.mid").write_bytes(ableton_midi([(b, 66, 0.5) for b in (1, 3, 5, 7, 9, 11, 13, 15)]))
        (sub / "Snare2.wav").write_bytes(wav44(stereo(clicks([1, 3, 5, 7, 9, 11, 13, 15], 4 * BAR))))
        line = [(0, 41, 3.5), (4, 44, 3.5), (8, 41, 3.5), (12, 46, 3.5)]  # F, G#, F, A#: F minor-ish
        (sub / "Bass3.mid").write_bytes(ableton_midi(line * 1))
        (sub / "Bass3Trap.wav").write_bytes(wav44(stereo(tones(line, 4 * BAR + 0.5, tail=0.4))))
        (sub / "Bass3HardHarmonic.wav").write_bytes(wav44(stereo(0.5 * tones(line, 4 * BAR + 0.5, tail=0.4))))
        rng = np.random.default_rng(5)
        other = np.zeros(int(8 * BAR * SR_IN + 3 * BAR * SR_IN))  # 8 bars of hats then silence
        for k in range(8 * 16):
            i = int(k * 60.0 / 174 / 4 * SR_IN)
            m = int(0.02 * SR_IN)
            other[i:i + m] += 0.15 * rng.standard_normal(m) * np.exp(-np.arange(m) / (0.004 * SR_IN))
        (sub / "Other1.wav").write_bytes(wav44(stereo(other)))
        (sub / "Bass3.wav.asd").write_bytes(b"ignored")
        (sub / "Kick2.wav.import").write_bytes(b"ignored")
        (sub / "readme.txt").write_bytes(b"ignored")
        cls.cat = cat.build_catalogue([cls.src], cls.repo)
        cls.files = {f["name"]: f for f in cls.cat["files"]}
        cls.midis = {m["name"]: m for m in cls.cat["midis"]}

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()


class Discovery(Fixture):
    def test_finds_wav_and_mid_recursively_and_ignores_the_rest(self) -> None:
        names = sorted(e["name"] for e in cat.discover([self.src]))
        self.assertNotIn("Bass3.wav.asd", names)
        self.assertNotIn("Kick2.wav.import", names)
        self.assertNotIn("readme.txt", names)
        self.assertIn("Kick2.wav", names)
        self.assertIn("Beat Shaper - Lv8 Slow-Drums.wav", names)
        ids = [e["id"] for e in cat.discover([self.src])]
        self.assertIn("Owner/Cold/Kick2.wav", ids)
        self.assertIn("Owner/Beat Shaper - Lv8 Slow-Drums.mid", ids)
        self.assertTrue(all(not i.startswith("/") and ":" not in i for i in ids), "paths are relative: no machine path in the output")

    def test_sources_are_found_by_name_in_parent_folders(self) -> None:
        deep = self.src / "Cold"
        found, missing = cat.find_sources(["Owner", "Nowhere"], root=deep)
        self.assertEqual([p.name for p in found], ["Owner"])
        self.assertEqual(missing, ["Nowhere"])
        found, _ = cat.find_sources([str(self.src)])
        self.assertEqual(found, [self.src])

    def test_counts(self) -> None:
        s = self.cat["summary"]
        # 3 Fast + 3 Fast (1) + 3 Slow Beat Shaper WAVs, then Kick2, Snare2, Bass3Trap, Bass3HardHarmonic, Other1
        self.assertEqual(s["wavs"], 14)
        self.assertEqual(s["midis"], 9 + 3)


class Pairing(Fixture):
    def test_beat_shaper_variants_stay_with_their_own_files(self) -> None:
        d0 = self.files["Beat Shaper - Lv9 Fast-Drums.wav"]
        d1 = self.files["Beat Shaper - Lv9 Fast-Drums (1).wav"]
        self.assertEqual((d0["family"], d0["variant"]), ("bs_lv9_fast", 0))
        self.assertEqual((d1["family"], d1["variant"]), ("bs_lv9_fast", 1))
        self.assertEqual(d0["midi"], "Owner/Cold/Beat Shaper - Lv9 Fast-Drums.mid")
        self.assertEqual(d1["midi"], "Owner/Cold/Beat Shaper - Lv9 Fast-Drums (1).mid")
        fam = next(f for f in self.cat["families"] if f["id"] == "bs_lv9_fast")
        self.assertEqual([s["variant"] for s in fam["sets"]], [0, 1])
        self.assertEqual(sorted(fam["sets"][1]["parts"]), ["bass", "drums", "synth"])

    def test_ableton_timbres_share_one_midi_and_one_family(self) -> None:
        trap, hard = self.files["Bass3Trap.wav"], self.files["Bass3HardHarmonic.wav"]
        self.assertEqual(trap["midi"], hard["midi"])
        self.assertEqual(trap["midi"], "Owner/Cold/Bass3.mid")
        self.assertEqual(trap["family"], hard["family"])
        self.assertEqual(trap["family"], "ab_cold_bass3")
        self.assertEqual({trap["timbre"], hard["timbre"]}, {"Trap", "HardHarmonic"})
        fam = next(f for f in self.cat["families"] if f["id"] == "ab_cold_bass3")
        self.assertEqual(fam["timbres"], ["HardHarmonic", "Trap"])
        self.assertEqual(self.midis["Bass3.mid"]["audio"], sorted([trap["id"], hard["id"]]))

    def test_audio_only_files_have_no_midi(self) -> None:
        self.assertIsNone(self.files["Other1.wav"]["midi"])
        self.assertEqual(self.files["Kick2.wav"]["midi"], "Owner/Cold/Kick2.mid")


class Tempo(Fixture):
    def test_174_profile_is_measured_not_read_from_the_header(self) -> None:
        f = self.files["Beat Shaper - Lv9 Fast-Drums.wav"]
        self.assertEqual(f["tempo"]["header_bpm"], 120.0)
        self.assertEqual(f["tempo"]["profile"], "174x1")
        self.assertEqual(f["tempo"]["method"], "drum_transient_fit")
        self.assertAlmostEqual(f["tempo"]["measured_bpm"], 174.0, delta=0.5)
        self.assertEqual(f["bars"]["musical"], 4)

    def test_87_profile(self) -> None:
        f = self.files["Beat Shaper - Lv8 Slow-Drums.wav"]
        self.assertEqual(f["tempo"]["profile"], "87x2")
        self.assertAlmostEqual(f["tempo"]["measured_bpm"], 87.0, delta=0.5)
        self.assertEqual(f["bars"]["musical"], 8)
        self.assertEqual(self.files["Beat Shaper - Lv8 Slow-Drums.wav"]["tempo"]["header_bpm"], 120.0)

    def test_pitched_parts_get_their_profile_from_the_spectrum_or_the_length(self) -> None:
        self.assertEqual(self.files["Beat Shaper - Lv9 Fast-Bass.wav"]["tempo"]["profile"], "174x1")
        self.assertEqual(self.files["Beat Shaper - Lv8 Slow-Bass.wav"]["tempo"]["profile"], "87x2")
        self.assertEqual(self.files["Bass3Trap.wav"]["tempo"]["profile"], "174x1")

    def test_ableton_midi_without_tempo_is_fitted_to_the_audio(self) -> None:
        f = self.files["Kick2.wav"]
        self.assertIsNone(f["tempo"]["header_bpm"])
        self.assertEqual(f["tempo"]["profile"], "174x1")
        self.assertEqual(f["tempo"]["method"], "drum_transient_fit")

    def test_audio_only_loop_uses_the_bar_grid(self) -> None:
        f = self.files["Other1.wav"]
        self.assertEqual(f["tempo"]["profile"], "174x1")
        self.assertEqual(f["tempo"]["method"], "grid_fit")

    def test_a_tempo_that_fits_no_profile_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "Odd"
            d.mkdir()
            (d / "Kick9.mid").write_bytes(ableton_midi([(b, 36, 0.3) for b in range(0, 32, 2)]))
            (d / "Kick9.wav").write_bytes(wav44(stereo(clicks([b for b in range(0, 32, 2)], 12.0, bpm=150.0))))
            c = cat.build_catalogue([d], Path(tempfile.gettempdir()) / 'no_repo')
            self.assertEqual(c["files"][0]["tempo"]["profile"], "unknown")
            self.assertIsNone(c["files"][0]["tempo"]["measured_bpm"])


class Bars(Fixture):
    def test_bar_count_pattern_and_midi_longer_than_audio(self) -> None:
        f = self.files["Kick2.wav"]
        self.assertEqual(f["bars"]["musical"], 4)
        self.assertEqual(f["bars"]["pattern"], 4)
        self.assertTrue(f["bars"]["midi_longer_than_audio"], "the MIDI has 8 bars, the recording 4")
        self.assertEqual(self.midis["Kick2.mid"]["bars_estimate"], 8)

    def test_a_repeating_pattern_is_found(self) -> None:
        m = self.midis["Snare2.mid"]
        self.assertEqual(m["pattern_bars"], 1)
        self.assertEqual(self.files["Snare2.wav"]["bars"]["pattern"], 1)
        self.assertEqual(self.files["Snare2.wav"]["bars"]["repeats"], 4)

    def test_release_tail_is_measured(self) -> None:
        f = self.files["Bass3Trap.wav"]
        self.assertEqual(f["bars"]["musical"], 4)
        self.assertAlmostEqual(f["tail"]["seconds"], 0.5, delta=0.03)
        self.assertEqual(f["tail"]["class"], "release")
        self.assertFalse(f["tail"]["sounding_at_end"])

    def test_trailing_silence_is_not_a_bar_of_music(self) -> None:
        f = self.files["Other1.wav"]
        self.assertEqual(f["bars"]["musical"], 8)
        self.assertEqual(f["tail"]["class"], "silence")
        self.assertAlmostEqual(f["tail"]["bars"], 3.0, delta=0.15)

    def test_a_tail_still_sounding_at_the_end_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "S"
            d.mkdir()
            line = [(0, 41, 4.0), (4, 44, 4.0), (8, 41, 4.0), (12, 44, 4.0)]
            (d / "Bass1.mid").write_bytes(ableton_midi(line))
            frames = tones(line, 4 * BAR + 1.2)
            frames[int(4 * BAR * SR_IN):] = 0.3 * np.sin(2 * np.pi * 110 * np.arange(len(frames) - int(4 * BAR * SR_IN)) / SR_IN)
            (d / "Bass1a.wav").write_bytes(wav44(stereo(frames)))
            f = cat.build_catalogue([d], Path(tempfile.gettempdir()) / 'no_repo')["files"][0]
            self.assertEqual(f["tail"]["class"], "cut while sounding")
            self.assertEqual(f["bars"]["musical"], 4)

    def test_leading_silence_and_format(self) -> None:
        f = self.files["Other1.wav"]
        self.assertEqual(f["format"]["sample_rate"], 44100)
        self.assertEqual(f["format"]["bits"], 16)
        self.assertGreaterEqual(f["leading_silence_ms"], 0)
        g = self.files["Beat Shaper - Lv9 Fast-Drums.wav"]
        self.assertEqual((g["format"]["sample_rate"], g["format"]["bits"], g["format"]["encoding"]), (48000, 32, "float"))
        self.assertGreater(g["duration_s"], 4 * BAR)


class UsedBy(Fixture):
    def test_packs_and_clips_built_from_a_file_are_listed(self) -> None:
        pack = self.repo / "songs" / "packs" / "fast_pack"
        pack.mkdir(parents=True, exist_ok=True)
        (pack / "pack.json").write_text(json.dumps({"id": "fast_pack", "source": {"project": "Lv9 Fast", "variant": 1, "files": {"Drums": {}, "Bass": {}}}}))
        clip = self.repo / "content" / "library" / "kick_clip"
        clip.mkdir(parents=True, exist_ok=True)
        (clip / "clip.json").write_text(json.dumps({"id": "kick_clip", "source": {"type": "imported", "source_dir": "Owner", "parts": {"kick": {"midi": "Cold/Kick2.mid"}},
                                                                                  "renders": {"kick__k": {"file": "Cold/Kick2.wav"}}}}))
        c = cat.build_catalogue([self.src], self.repo)
        files = {f["name"]: f for f in c["files"]}
        self.assertEqual(files["Beat Shaper - Lv9 Fast-Drums (1).wav"]["used_by"], [{"type": "pack", "id": "fast_pack"}])
        self.assertNotIn("used_by", files["Beat Shaper - Lv9 Fast-Drums.wav"], "only the variant the pack was built from")
        self.assertEqual(files["Kick2.wav"]["used_by"], [{"type": "clip", "id": "kick_clip"}])
        self.assertEqual(next(m for m in c["midis"] if m["name"] == "Kick2.mid")["used_by"], [{"type": "clip", "id": "kick_clip"}])
        self.assertEqual(c["summary"]["wavs_used_in_game"], 3)


class Roles(Fixture):
    def test_roles(self) -> None:
        self.assertEqual(self.files["Kick2.wav"]["role"], "kick")
        self.assertEqual(self.files["Snare2.wav"]["role"], "snare")
        self.assertEqual(self.files["Bass3Trap.wav"]["role"], "bass")
        self.assertEqual(self.files["Beat Shaper - Lv9 Fast-Drums.wav"]["role"], "drums")
        self.assertEqual(self.files["Beat Shaper - Lv9 Fast-Synth.wav"]["role"], "synth")
        self.assertEqual(self.files["Other1.wav"]["role"], "perc", "bright, regular onsets: percussion")

    def test_a_sustained_tonal_other_is_not_percussion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "P"
            d.mkdir()
            t = np.arange(int(8 * BAR * SR_IN)) / SR_IN
            pad = 0.2 * (np.sin(2 * np.pi * 220 * t) + 0.5 * np.sin(2 * np.pi * 440 * t) + 0.3 * np.sin(2 * np.pi * 660 * t))  # one steady note
            (d / "Other4.wav").write_bytes(wav44(stereo(pad)))
            f = cat.build_catalogue([d], Path(tempfile.gettempdir()) / 'no_repo')["files"][0]
            self.assertIn(f["role"], ("pad", "synth"))
            self.assertFalse(f["tonal"]["atonal"])
            self.assertEqual(f["tonal"]["basis"], "audio chroma")

    def test_midi_drum_notes(self) -> None:
        m = self.midis["Beat Shaper - Lv9 Fast-Drums.mid"]
        self.assertEqual(set(m["drum_notes"]), {"hat", "kick", "snare"})
        self.assertEqual(m["drum_notes"]["kick"], 8)


class MidiFacts(Fixture):
    def test_notes_density_velocity_and_game_beats(self) -> None:
        m = self.midis["Beat Shaper - Lv8 Slow-Bass.mid"]
        self.assertEqual(m["profile"], "87x2")
        self.assertEqual(m["scale"], 2)
        self.assertEqual([n[2] for n in m["notes"]], [40, 45, 38, 48])
        self.assertEqual([n[0] for n in m["notes"]], [0.0, 8.0, 16.0, 24.0], "source quarters are two game beats each at 87x2")
        self.assertEqual(sum(m["density_per_bar"]), 4)
        self.assertEqual(len(m["density_per_bar"]), 8)
        self.assertEqual(m["velocity"]["max"], 100)
        self.assertEqual(m["header_bpm"], 120.0)

    def test_key_estimate_and_pitch_classes(self) -> None:
        h = np.zeros(12)
        for pc, w in ((0, 4), (2, 1), (4, 2), (5, 1), (7, 3), (9, 1), (11, 1)):
            h[pc] = w
        k = cat.key_estimate(h)
        self.assertEqual((k["tonic"], k["mode"]), ("C", "major"))
        self.assertGreater(k["confidence"], 0.5)
        flat = cat.key_estimate(np.ones(12))
        self.assertTrue(flat is None or flat["confidence"] < 0.3, "a flat histogram is not a key")
        f = self.files["Bass3Trap.wav"]
        self.assertFalse(f["tonal"]["atonal"])
        self.assertEqual(f["tonal"]["basis"], "midi")
        self.assertAlmostEqual(sum(f["tonal"]["pitch_classes"]), 1.0, delta=0.01)
        self.assertTrue(self.files["Kick2.wav"]["tonal"]["atonal"])

    def test_rhythm_measures(self) -> None:
        straight = cat.rhythm_measures([0, 1, 2, 3], 1)
        synco = cat.rhythm_measures([0.25, 1.5, 2.75, 3.5], 1)
        self.assertEqual(straight["syncopation"], 0.0)
        self.assertGreater(synco["syncopation"], 0.5)
        self.assertEqual(straight["per_beat"], 1.0)

    def test_loudness_and_clipping(self) -> None:
        loud = self.files["Kick2.wav"]["loudness"]  # clicks at 1.4 amplitude, clipped in the 16-bit file
        self.assertGreater(loud["clipping_samples"], 0)
        self.assertEqual(loud["clipping_risk"], "clipped")
        self.assertEqual(loud["peak_db"], 0.0)
        quiet = self.files["Beat Shaper - Lv9 Fast-Synth.wav"]["loudness"]
        self.assertEqual(quiet["clipping_risk"], "none")
        self.assertLess(quiet["rms_db"], -25)


class Compatibility(unittest.TestCase):
    @staticmethod
    def fam(fid, folder, roles) -> dict:
        return {"id": fid, "kind": "ableton_pattern", "folder": folder, "roles": roles, "members": [], "sets": []}

    @staticmethod
    def role(bars, profile, key=None, atonal=False) -> dict:
        d = {"files": [], "bars": [bars], "phrase_bars": [bars], "profile": profile, "atonal": atonal}
        if not atonal:
            d["key"] = key
        return d

    def key(self, tonic, mode, conf=0.9) -> dict:
        pc = cat.PC_NAMES.index(tonic)
        return {"tonic": tonic, "pc": pc, "mode": mode, "name": f"{tonic} {mode}", "correlation": 0.9, "confidence": conf}

    def rows(self, a, b) -> dict:
        r = cat.compatibility([a, b])
        self.assertEqual(len(r), 1)
        return r[0]

    def test_same_key_equal_length_and_profile_is_compatible(self) -> None:
        a = self.fam("a", "S/x", {"bass": self.role(4, "174x1", self.key("F", "minor"))})
        b = self.fam("b", "S/x", {"synth": self.role(4, "174x1", self.key("F", "minor"))})
        r = self.rows(a, b)
        self.assertTrue(r["compatible"])
        self.assertFalse(r["uncertain"])

    def test_different_keys_are_incompatible_even_at_the_same_tempo(self) -> None:
        a = self.fam("a", "S/x", {"bass": self.role(4, "174x1", self.key("F", "minor"))})
        b = self.fam("b", "S/x", {"synth": self.role(4, "174x1", self.key("B", "major"))})
        r = self.rows(a, b)
        self.assertFalse(r["compatible"])
        self.assertIn("tonal centres disagree", r["combos"][0]["against"])

    def test_profile_or_length_mismatch_is_incompatible(self) -> None:
        a = self.fam("a", "S/x", {"kick": self.role(4, "174x1", atonal=True)})
        slow = self.fam("b", "S/x", {"bass": self.role(4, "87x2", self.key("F", "minor"))})
        self.assertFalse(self.rows(a, slow)["compatible"])
        long = self.fam("c", "S/x", {"bass": self.role(3, "174x1", self.key("F", "minor"))})
        self.assertFalse(self.rows(self.fam("a", "S/x", {"kick": self.role(4, "174x1", atonal=True)}), long)["compatible"])
        unknown = self.fam("d", "S/x", {"bass": self.role(4, "unknown", self.key("F", "minor"))})
        self.assertFalse(self.rows(a, unknown)["compatible"], "an unmeasured tempo is not assumed to fit")

    def test_atonal_parts_fit_and_low_confidence_is_uncertain(self) -> None:
        kick = self.fam("k", "S/x", {"kick": self.role(4, "174x1", atonal=True)})
        bass = self.fam("b", "S/x", {"bass": self.role(4, "174x1", self.key("F", "minor", 0.1))})
        r = self.rows(kick, bass)
        self.assertTrue(r["compatible"])
        self.assertFalse(r["uncertain"], "an atonal part does not depend on the key estimate")
        weak_a = self.fam("a", "S/x", {"bass": self.role(4, "174x1", self.key("F", "minor", 0.1))})
        weak_b = self.fam("b", "S/x", {"synth": self.role(4, "174x1", self.key("F", "minor", 0.9))})
        r = self.rows(weak_a, weak_b)
        self.assertTrue(r["compatible"])
        self.assertTrue(r["uncertain"])

    def test_atonal_pairing_across_source_folders_is_flagged(self) -> None:
        kick = self.fam("k", "One/x", {"kick": self.role(4, "174x1", atonal=True)})
        bass = self.fam("b", "Two/y", {"bass": self.role(4, "174x1", self.key("F", "minor"))})
        r = self.rows(kick, bass)
        self.assertTrue(r["compatible"])
        self.assertTrue(r["uncertain"], "only the rules, no shared folder, support it")

    def test_relative_keys_agree_and_parallel_keys_are_nearby(self) -> None:
        self.assertEqual(cat.key_distance(self.key("A", "minor"), self.key("C", "major")), "relative")
        self.assertEqual(cat.key_distance(self.key("C", "minor"), self.key("C", "major")), "near")
        self.assertEqual(cat.key_distance(self.key("C", "minor"), self.key("F#", "minor")), "disagree")

    def test_tiling_phrases_are_uncertain_and_overlapping_roles_are_skipped(self) -> None:
        a = self.fam("a", "S/x", {"kick": self.role(8, "174x1", atonal=True)})
        b = self.fam("b", "S/x", {"bass": self.role(4, "174x1", self.key("F", "minor"))})
        r = self.rows(a, b)
        self.assertEqual(r["combos"][0]["length"], "tiles")
        self.assertTrue(r["uncertain"])
        two_basses = [self.fam("a", "S/x", {"bass": self.role(4, "174x1", self.key("F", "minor"))}),
                      self.fam("b", "S/x", {"bass": self.role(4, "174x1", self.key("F", "minor"))})]
        self.assertEqual(cat.compatibility(two_basses), [], "two basses are alternatives, not layers")

    def test_synthetic_catalogue_rows(self) -> None:
        # the fixture's 174 set and 87 set can never be paired; the Ableton kick (174) fits the 174 set's bass only when the length matches
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "Owner"
            src.mkdir()
            for name, data in export_set(174.0, project="Lv9 Fast").items():
                (src / name).write_bytes(data)
            for name, data in export_set(87.0, project="Lv8 Slow").items():
                (src / name).write_bytes(data)
            c = cat.build_catalogue([src], Path(tmp) / 'no_repo')
            row = next(r for r in c["compatibility"] if {r["a"], r["b"]} == {"bs_lv8_slow", "bs_lv9_fast"})
            self.assertFalse(row["compatible"], "an 87x2 set and a 174x1 set are not mixed")
            self.assertTrue(all("profiles differs" in x for cb in row["combos"] for x in cb.get("against", [])))


class Output(Fixture):
    def test_output_is_deterministic_and_machine_independent(self) -> None:
        a = cat.catalogue_text(cat.build_catalogue([self.src], self.repo))
        b = cat.catalogue_text(cat.build_catalogue([self.src], self.repo))
        self.assertEqual(a, b)
        self.assertEqual(cat.markdown(json.loads(a)), cat.markdown(json.loads(b)))
        self.assertNotIn(self.tmp.name, a, "no absolute path in the catalogue")
        self.assertNotIn("\r", a)
        data = json.loads(a)
        self.assertEqual(data["schema"], 1)
        self.assertEqual(sorted(data), ["compatibility", "families", "files", "midis", "schema", "sources", "summary", "tool", "within_family"])
        self.assertEqual([f["id"] for f in data["files"]], sorted(f["id"] for f in data["files"]))

    def test_markdown_states_the_facts_the_brief_asks_for(self) -> None:
        md = cat.markdown(self.cat)
        self.assertIn("MIDI headers say 120 BPM", md)
        self.assertIn("174x1", md)
        self.assertIn("Flagged for the owner's ear", md)

    def test_check_mode_compares_with_the_files_on_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            js, md, _ = cat.run([self.src], self.repo)
            out, mdp = Path(tmp) / "c.json", Path(tmp) / "c.md"
            out.write_text(js, encoding="utf-8")
            mdp.write_text(md, encoding="utf-8")
            self.assertEqual(out.read_text(encoding="utf-8"), cat.run([self.src], self.repo)[0])


if __name__ == "__main__":
    unittest.main()
