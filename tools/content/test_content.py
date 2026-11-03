"""Tests of the owner content path: the one build command, drop-in WAV renders, edited MIDI, validation and assembly.

    python -m unittest discover -s tools/content -p "test_*.py"      (tools/test.sh runs it too)

Every test builds into a temporary copy of the library (never the real content/ or songs/), using the fixtures in
content/fixtures/ (see make_fixtures.py).
"""
from __future__ import annotations

import hashlib
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
from common import (CONTENT, LIBRARY, MISSIONS, ROOT, TICKS_PER_BAR, bars_to_frames, read_json, read_wav, sha256_file, tick_to_sample,  # noqa: E402
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


DEFENSE_02_SHA256 = "29091ad2763ab22482aae0f2e7f8e79120008e8ff9244b8cd099cd95120a444c"  # data/battlefields/defense_02.json (LF)


class MissionOneTests(unittest.TestCase):
    """Mission 1 (the village level) as authored: parsed against the real library, no audio rendered, nothing written."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp(prefix="rw_m01_"))
        state = cls.tmp / "build_state.json"
        if (CONTENT / "build_state.json").exists():
            shutil.copy(CONTENT / "build_state.json", state)
        cls.lib = Library(LIBRARY, CONTENT / "sounds.json", state).load()
        cls.m = mission_mod.Mission(MISSIONS / "level_01.json", cls.lib)
        cls.m.parse()
        cls.m.arrange()
        cls.m.make_sequences()
        cls.m.check()
        stats = {"files": 0, "placeholder_files": 0, "owner_files": 0, "default_mix_peak_db": -3.0, "loudest_mix_bound_db": -3.0}
        cls.level = cls.m.level_json([], {}, stats)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_mission_one_is_128_bars_in_sixteen_phases_and_32_sequences(self):
        m = self.m
        self.assertEqual(m.errors, [])
        self.assertEqual(m.bars, 128)
        self.assertEqual(len(m.phases), 16)
        self.assertEqual(len(m.sequences), 32)
        self.assertEqual("".join("D" if p["mode"] == "drums" else "B" for p in m.phases), "DDBDBDDBDBDBDDBD")
        self.assertEqual([i["bar"] for i in m.intros], [1, 16])

    def test_rewards_follow_the_four_acts(self):
        rewards = [s["reward"] for s in self.m.sequences]
        acts = [rewards[i * 8:(i + 1) * 8] for i in range(4)]
        self.assertEqual(acts[0], ["pillbox", "rifle_squad"] * 4)
        self.assertEqual(acts[1], ["pillbox", "rifle_squad"] * 4)
        self.assertIn("grenadier_squad", acts[2])
        self.assertTrue({"pillbox", "rifle_squad"} <= set(acts[2]))
        self.assertEqual(set(acts[3]), {"grenadier_squad", "pillbox"})
        for r in ("rifle_squad", "grenadier_squad"):
            self.assertEqual(mission_mod.RULES["rewards"][r]["type"], "unit")
            self.assertEqual(mission_mod.RULES["rewards"][r]["count"], 3)

    def test_waves_carry_a_validated_target_and_the_barracks_objective(self):
        waves = self.level["waves"]
        self.assertGreaterEqual(len(waves), 20)
        for w in waves:
            self.assertIn(w["target"], ("defenses", "civilians", "core"))
            self.assertEqual(w["target_objective"], "barracks")
            self.assertLess(w["start_tick"], 116 * TICKS_PER_BAR + 1, "units need about 12 s to arrive")
        self.assertEqual({w["target"] for w in waves}, {"defenses", "civilians", "core"})
        self.assertGreaterEqual(sum(g["count"] for w in waves for g in w["groups"]), 130)
        self.assertEqual(sum(g["count"] for w in waves for g in w["groups"] if g["actor"] == "jeep"), 3)
        self.assertEqual({w["entry"] for w in waves if any(g["actor"] == "jeep" for g in w["groups"])}, {"left", "top", "right"})

    def test_a_bad_target_class_is_refused_and_a_group_may_override(self):
        m = mission_mod.Mission(MISSIONS / "level_01.json", self.lib)
        wave = {"id": "w", "start_bar": 1, "entry": "left", "groups": [{"actor": "e1", "count": 1}]}
        self.assertEqual(m._wave(wave)["target"], "core", "default class")
        self.assertEqual(m.errors, [])
        m._wave({**wave, "target": "tanks"})
        self.assertTrue(any("target 'tanks'" in e for e in m.errors), m.errors)
        m.errors.clear()
        out = m._wave({**wave, "groups": [{"actor": "e1", "count": 1, "target": "civilians"}]})
        self.assertEqual(out["groups"][0]["target"], "civilians")
        self.assertEqual(m.errors, [])
        m._wave({**wave, "groups": [{"actor": "e1", "count": 1, "target": "everything"}]})
        self.assertTrue(any("target 'everything'" in e for e in m.errors), m.errors)

    def test_objective_defaults_to_the_battlefield_and_falls_back_to_the_core(self):
        self.assertEqual(mission_mod.Mission.primary_objective("village_01"), "barracks")
        self.assertEqual(mission_mod.Mission.primary_objective("defense_02"), "command_core")
        self.assertEqual(mission_mod.Mission.primary_objective("no_such_field"), "command_core")

    def test_rules_carry_start_units_and_unit_capacity(self):
        rules = self.level["rules"]
        self.assertEqual(self.level["battlefield"], "village_01")
        self.assertEqual(rules["units_per_point"], 14)
        self.assertEqual(rules["objective_hp"], {"barracks": 60000})
        self.assertEqual([(u["actor"], u["count"], u["point"]) for u in rules["start_units"]],
                         [("e1", 5, "defense_1"), ("e1", 5, "defense_2"), ("e1", 5, "defense_3")])

    def test_defense_02_is_unchanged(self):
        raw = (ROOT / "data" / "battlefields" / "defense_02.json").read_bytes().replace(bytes([13, 10]), bytes([10]))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), DEFENSE_02_SHA256)

    def test_village_01_battlefield(self):
        bf = read_json(ROOT / "data" / "battlefields" / "village_01.json")
        d2 = read_json(ROOT / "data" / "battlefields" / "defense_02.json")
        self.assertEqual(bf["id"], "village_01")
        self.assertEqual(bf["objectives"], [{"id": "barracks", "role": "barracks", "required": True}])
        self.assertEqual(len(bf["defense_points"]), 3)
        self.assertEqual(bf["leash_cells"], d2["leash_cells"])
        self.assertEqual(bf["map"], "field_96x48")
        self.assertEqual((bf["width"], bf["height"]), (96, 48))
        self.assertEqual(bf["view"], {"center": [47.5, 23.5], "max_cells": [72.0, 27.0], "zoom": 0.75})
        self.assertEqual([(p["id"], p["x"], p["y"]) for p in bf["defense_points"]], [("defense_1", 29, 25), ("defense_2", 47, 15), ("defense_3", 65, 25)])
        self.assertEqual([(e["id"], e["x"], e["y"]) for e in bf["entries"]], [("left", 6, 25), ("top", 47, 0), ("right", 88, 25)])
        self.assertEqual(len(bf["sockets"]), 15)
        self.assertEqual([s["id"] for s in bf["sockets"]], [s["id"] for s in d2["sockets"]])
        self.assertEqual([(s["point"], s["order"]) for s in bf["sockets"]], [(s["point"], s["order"]) for s in d2["sockets"]])
        self.assertNotEqual([(s["x"], s["y"]) for s in bf["sockets"]], [(s["x"], s["y"]) for s in d2["sockets"]])
        village = [b for b in bf["buildings"] if b["role"] == "village"]
        self.assertGreaterEqual(len(village), 8)
        self.assertTrue(all(b["actor"].startswith("v0") for b in village))
        self.assertEqual([b["role"] for b in bf["buildings"] if b["role"] in ("main", "factory", "power", "dome")], [])
        self.assertEqual(sum(1 for b in bf["buildings"] if b["role"] == "barracks"), 1)
        self.assertEqual(len(bf["civilians"]), 10)
        self.assertEqual(sorted(c["actor"] for c in bf["civilians"]), ["c1", "c2"] + ["tecn"] * 8)
        blocked = {(b["x"] + i, b["y"] + j) for b in bf["buildings"] for i in range(b["w"]) for j in range(b["h"])}
        for c in bf["civilians"]:
            self.assertNotIn((c["x"], c["y"]), blocked)
        self.assertNotIn(tuple(bf["exits"]["barracks"]), blocked)
        self.assertEqual(set(bf["wander"]), {"rect", "radius", "flee_radius"})


class BassChartTests(unittest.TestCase):
    """Mission 1's bass chart (bass_chart: pads by pitch, a minimum gap, no holds), read from the built pack."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.level = read_json(ROOT / "songs" / "m01_first_watch" / "level.json")
        cls.bass_phases = [i for i, p in enumerate(cls.level["phases"]) if p["mode"] == "bass"]

    def blocks(self, phase: int) -> list:
        return [b for b in self.level["cue_blocks"] if b["phase"] == phase and b["family"] == "bass"]

    def option_cues(self, phase: int, option: str) -> list:
        """(tick, duration, pad) of one bass line option in one phase, in time order."""
        return sorted((t, d, b["pad"]) for b in self.blocks(phase) for t, d in b["options"][option])

    def test_pitch_pads_buckets_low_to_high_over_four_pads(self):
        self.assertEqual(mission_mod.pitch_pads([57]), {57: 2})
        self.assertEqual(mission_mod.pitch_pads([60, 60, 60]), {60: 2})
        self.assertEqual(mission_mod.pitch_pads([60, 50, 55]), {50: 1, 55: 2, 60: 3})
        seven = mission_mod.pitch_pads([51, 53, 56, 57, 58, 59, 60, 53, 51])
        self.assertEqual([seven[p] for p in (51, 53, 56, 57, 58, 59, 60)], [1, 1, 2, 2, 3, 3, 4])
        self.assertEqual(mission_mod.pitch_pads(range(40, 48)), {40 + i: i // 2 + 1 for i in range(8)})

    def test_bass_chart_defaults_and_validation(self):
        lib = Library(LIBRARY, CONTENT / "sounds.json", CONTENT / "build_state.json")
        m = mission_mod.Mission(MISSIONS / "level_01.json", lib)
        base = mission_mod.BASS_CHART_DEFAULT
        self.assertEqual(m._bass_chart(None, base, "x"), {"pads": "slot", "min_gap_ticks": 0, "holds": True})
        self.assertEqual(m._bass_chart({"pads": "pitch"}, base, "x"), {"pads": "pitch", "min_gap_ticks": 0, "holds": True})
        self.assertEqual(m.errors, [])
        for bad in ({"pads": "random"}, {"min_gap_ticks": -1}, {"min_gap_ticks": 1.5}, {"min_gap_ticks": True}, {"holds": "no"}, {"speed": 2}):
            m.errors.clear()
            self.assertEqual(m._bass_chart(bad, base, "x"), base, bad)
            self.assertEqual(len(m.errors), 1, bad)

    def test_mission_one_bass_cues_spread_over_at_least_three_pads(self):
        self.assertEqual(self.bass_phases, [2, 4, 7, 9, 11, 14])
        for ph in self.bass_phases:
            pads = {b["pad"] for b in self.blocks(ph)}
            self.assertGreaterEqual(len(pads), 3, f"phase {ph + 1}")
            self.assertTrue(pads <= {1, 2, 3, 4})
            for opt in self.blocks(ph)[0]["options"]:
                self.assertGreaterEqual(len({c[2] for c in self.option_cues(ph, opt)}), 3, f"phase {ph + 1} {opt}")

    def test_every_bass_cue_is_a_tap(self):
        for ph in self.bass_phases:
            for b in self.blocks(ph):
                for lst in b["options"].values():
                    self.assertTrue(all(d == 0 for _, d in lst), f"phase {ph + 1} pad {b['pad']}")

    def test_bass_cues_are_a_beat_and_a_half_apart_and_sparse(self):
        for ph in self.bass_phases:
            for opt in self.blocks(ph)[0]["options"]:
                cues = self.option_cues(ph, opt)
                self.assertTrue(8 <= len(cues) <= 16, f"phase {ph + 1} {opt}: {len(cues)} cues")
                for x, y in zip(cues, cues[1:]):
                    self.assertGreaterEqual(y[0] - x[0], 960, f"phase {ph + 1} {opt}")

    def test_each_pad_in_use_is_labelled_with_the_voice(self):
        for ph in self.bass_phases:
            labels = self.level["phases"][ph]["pads"]
            for b in self.blocks(ph):
                self.assertEqual(labels[str(b["pad"])], {"family": "bass", "ref": b["voice"]}, f"phase {ph + 1}")
            self.assertGreaterEqual(len(labels), 3)

    def test_blocks_of_one_line_share_voice_window_and_option_keys(self):
        for ph in self.bass_phases:
            blocks = self.blocks(ph)
            for key in ("voice", "deps", "start_tick", "end_tick"):
                self.assertEqual(len({json.dumps(b[key]) for b in blocks}), 1, key)
            self.assertEqual(len({tuple(b["options"]) for b in blocks}), 1)
            self.assertEqual(len({b["pad"] for b in blocks}), len(blocks), "one block per pad")

    def test_drum_cues_are_unchanged_by_the_bass_chart(self):
        drum = [b for b in self.level["cue_blocks"] if b["family"] in ("kick", "snare")]
        self.assertEqual({b["pad"] for b in drum if b["family"] == "kick"}, {1})
        self.assertEqual({b["pad"] for b in drum if b["family"] == "snare"}, {4})


if __name__ == "__main__":
    unittest.main()
