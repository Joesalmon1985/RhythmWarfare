"""Tests of the content build: the loop library (loops, cues, chart rules, index, instruments), the mission packs (schema 4)
and the owner path (drop-in WAV renders, edited MIDI, validation).

    python -m unittest discover -s tools/content -p "test_*.py"      (tools/test.sh runs it too)

Most tests build into a temporary copy of a few library clips (never the real content/ or songs/), using the fixtures in
content/fixtures/ (see make_fixtures.py). The "real content" classes read the committed index and packs.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build  # noqa: E402
import chart  # noqa: E402
from common import (CONTENT, INSTRUMENTS, LIBRARY, MISSIONS, MISSIONS_LEGACY, ROOT, SONGS, TICKS_PER_BAR, bars_to_frames, read_json,  # noqa: E402
                    read_wav, sha256_file, tick_to_sample, write_json, write_midi, write_wav)
from library import Library  # noqa: E402
import mission as mission_mod  # noqa: E402

FIX = CONTENT / "fixtures"
CLIPS = ["groove_watch", "fill_break", "bass_hold_b", "acc_second_pulse"]
LOOP = bars_to_frames(8)
DEFAULTS = {"groove": "groove_watch", "fill": "fill_break", "kick_sound": "kick_march", "snare_sound": "snare_guard",
            "bass": "bass_hold_b", "bass_sound": "bass_patrol", "backing": "acc_second_pulse"}
CONTRACT_PACK_KEYS = {"schema_version", "level_id", "number", "title", "bpm", "ticks_per_beat", "time_signature", "duration_ticks",
                      "seed", "battlefield", "roster", "rules", "sequence_threshold", "sequence_bars", "phases", "waves", "intros", "base"}
CONTRACT_CLIP_KEYS = {"kind", "name", "key", "bars", "parts", "bound", "sounds", "cues", "loops", "peak_db"}
CONTRACT_SOUND_KEYS = {"family", "name", "placeholder", "produces", "blurb"}
REAL_DEFAULTS = {"groove": "groove_half_time", "fill": "", "kick_sound": "kick_half_time", "snare_sound": "snare_backbeat",
                 "bass": "bass_sub_line", "bass_sound": "bass_sub_deep", "backing": "acc_hats_driving"}


def decode(path: Path) -> np.ndarray:
    """An Ogg as int16 frames x 2 (ffmpeg)."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "2", "-ar", "48000", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, dtype="<i2").reshape(-1, 2)


def tree(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): sha256_file(p) for p in sorted(root.rglob("*")) if p.is_file()}


def write_slim_mission(folder: Path, waves: Path, **over) -> Path:
    m = {"level_id": "level_fixture", "number": 99, "title": "Fixture", "pack": "fixture_mission", "bars": 16, "seed": 99, "form": "DB",
         "battle": {"battlefield": "defense_02", "waves": str(waves)}, "intros": [], "note": "test"}
    m.update(over)
    path = folder / "level_fixture.json"
    write_json(path, m)
    return path


TEMPLATE: "Workspace | None" = None  # one fully built workspace; the others start as copies of it (placeholders and loops included)


def setUpModule() -> None:
    global TEMPLATE
    TEMPLATE = Workspace(seeded=False)
    assert TEMPLATE.build()["ok"]


def tearDownModule() -> None:
    if TEMPLATE is not None:
        TEMPLATE.close()


class Workspace:
    """A throwaway content tree: a few library clips, a fixture mission, its own state, report and songs. `seeded` starts
    from the template's finished build, so a test only pays for what it changes."""

    def __init__(self, seeded: bool = True) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="rw_content_"))
        self.lib = self.tmp / "library"
        self.songs = self.tmp / "songs"
        self.state = self.tmp / "build_state.json"
        if seeded and TEMPLATE is not None:
            shutil.copytree(TEMPLATE.lib, self.lib)
            shutil.copytree(TEMPLATE.songs, self.songs)
            shutil.copy(TEMPLATE.state, self.state)
            shutil.copytree(TEMPLATE.missions, self.tmp / "missions")
            shutil.copy(TEMPLATE.tmp / "waves.json", self.tmp / "waves.json")
            self.missions = self.tmp / "missions"
        else:
            for c in CLIPS:
                shutil.copytree(LIBRARY / c, self.lib / c, ignore=shutil.ignore_patterns("placeholder"))
            shutil.copytree(FIX / "example_groove", self.lib / "example_groove")
            self.missions = self.tmp / "missions"
            self.missions.mkdir()
            shutil.copy(FIX / "waves_fixture.json", self.tmp / "waves.json")
            write_slim_mission(self.missions, self.tmp / "waves.json")
        self.instruments = INSTRUMENTS
        self.defaults = dict(DEFAULTS)

    def build(self, check: bool = False) -> dict:
        return build.run(check=check, library=self.lib, missions=self.missions, songs=self.songs, sounds=CONTENT / "sounds.json",
                         state=self.state, report=self.tmp / "REPORT.md", instruments=self.instruments, defaults=self.defaults, quiet=True)

    def index(self) -> dict:
        return read_json(self.songs / "library" / "index.json")

    def loop(self, clip: str, part: str, sound: str) -> Path:
        return self.songs / "library" / "loops" / f"{clip}__{part}__{sound}.ogg"

    def add_groove(self, cid: str, kicks: list[int], snares: list[int], bars: int = 8) -> None:
        folder = self.lib / cid
        folder.mkdir()
        write_json(folder / "clip.json", {"id": cid, "kind": "groove", "name": cid, "bars": bars, "tempo_bpm": 174, "source": {"type": "owner"}})
        write_midi(folder / "kick.mid", [{"tick": t, "duration_ticks": 120, "pitch": 36, "velocity": 100} for t in kicks], "kick")
        write_midi(folder / "snare.mid", [{"tick": t, "duration_ticks": 120, "pitch": 38, "velocity": 100} for t in snares], "snare")

    def close(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


class LoopTests(unittest.TestCase):
    """How a render becomes the 8-bar loop the game plays (Library.loop_frames) and the files the build writes."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp(prefix="rw_loops_"))
        cls.lib = Library(LIBRARY, CONTENT / "sounds.json", cls.tmp / "state.json", write=False).load()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_every_loop_is_exactly_eight_bars_and_the_tail_folds_onto_the_start(self):
        for cid in ("groove_watch", "fill_break", "bass_hold_b"):
            clip = self.lib.clips[cid]
            src = np.zeros((bars_to_frames(clip.bars + 1), 2), dtype=np.float32)
            src[-1000:] = 0.25  # the end of the release tail
            out = self.lib.loop_frames(clip, src)
            self.assertEqual(out.shape, (LOOP, 2), cid)
        bass = self.lib.clips["bass_hold_b"]
        src = np.zeros((LOOP + 1000, 2), dtype=np.float32)
        src[LOOP:] = 0.25
        out = self.lib.loop_frames(bass, src)
        self.assertEqual(out.shape[0], LOOP)
        self.assertTrue(np.all(out[:1000] == 0.25), "the tail's energy appears at the loop start")
        self.assertTrue(np.all(out[1000:] == 0.0), "and nowhere else")

    def test_a_two_bar_groove_is_tiled_four_times_with_tails_overlapping_the_next_repetition(self):
        clip = self.lib.clips["groove_watch"]
        self.assertEqual(clip.bars, 2)
        src = np.zeros((bars_to_frames(3), 2), dtype=np.float32)
        src[0] = 0.9
        src[bars_to_frames(2) + 100] = 0.3  # in the tail: lands 100 frames after the next repetition's downbeat
        out = self.lib.loop_frames(clip, src)
        starts = [tick_to_sample(2 * TICKS_PER_BAR * k) for k in range(4)]
        self.assertEqual(np.nonzero(out[:, 0] > 0.8)[0].tolist(), starts, "starts land on exact sample frames")
        for k in range(1, 4):  # the previous repetition's tail (a sample either way: each start is rounded from its tick)
            self.assertAlmostEqual(float(out[starts[k] + 99:starts[k] + 102, 0].max()), 0.3, places=5)
        self.assertAlmostEqual(float(out[99:102, 0].max()), 0.3, places=5, msg="the last repetition's tail wraps onto the first bar")

    def test_a_fill_sits_in_bar_eight(self):
        clip = self.lib.clips["fill_break"]
        src = np.zeros((bars_to_frames(2), 2), dtype=np.float32)
        src[0] = 0.7
        src[bars_to_frames(1) + 10] = 0.2
        out = self.lib.loop_frames(clip, src)
        at = tick_to_sample(7 * TICKS_PER_BAR)
        self.assertEqual(np.nonzero(out[:, 0] > 0.5)[0].tolist(), [at])
        self.assertEqual(np.count_nonzero(out[10 + 1:at]), 0, "bars 1 to 7 are silent")
        self.assertAlmostEqual(float(out[10, 0]), 0.2, places=5, msg="the tail past bar 8 wraps to the start")
        self.assertEqual(out.shape[0], LOOP)

    def test_a_long_backing_is_cut_to_sixteen_bars_with_a_ten_ms_fade(self):
        clip = self.lib.clips["acc_second_pulse"]
        self.assertEqual(clip.bars, 40)
        src = np.full((bars_to_frames(41), 2), 0.5, dtype=np.float32)
        out = self.lib.loop_frames(clip, src)
        self.assertEqual(out.shape[0], bars_to_frames(16))
        self.assertAlmostEqual(float(out[1000, 0]), 0.5, places=5)
        self.assertAlmostEqual(float(out[-480 - 1000, 0]), 0.5, places=5)
        self.assertLess(float(out[-1, 0]), 0.001, "10 ms fade at the end")
        self.assertAlmostEqual(float(out[-240, 0]), 0.25, delta=0.02)

    def test_a_backing_of_eight_bars_is_the_loop_as_it_is(self):
        clip = type("C", (), {"index_kind": "backing", "bars": 8, "id": "x"})()
        src = np.zeros((LOOP + 500, 2), dtype=np.float32)
        src[10] = 0.5
        src[LOOP + 20] = 0.4
        out = self.lib.loop_frames(clip, src)
        self.assertEqual(out.shape[0], LOOP)
        self.assertAlmostEqual(float(out[10, 0]), 0.5, places=5)
        self.assertAlmostEqual(float(out[20, 0]), 0.4, places=5)


class LibraryBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = Workspace()

    def tearDown(self) -> None:
        self.ws.close()

    def test_build_writes_an_index_with_every_contract_key_and_a_loop_of_exact_length_for_each_sound(self):
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        idx = self.ws.index()
        self.assertEqual(list(idx), ["format", "bpm", "ticks_per_beat", "loop_bars", "defaults", "sounds", "clips"])
        self.assertEqual((idx["format"], idx["bpm"], idx["ticks_per_beat"], idx["loop_bars"]), ("rhythm_warfare.library.v1", 174, 960, 8))
        self.assertEqual(idx["defaults"], DEFAULTS)
        self.assertEqual(set(idx["clips"]), set(CLIPS) | {"example_groove"})
        for cid, c in idx["clips"].items():
            self.assertEqual(set(c), CONTRACT_CLIP_KEYS, cid)
            self.assertIn(c["kind"], ("groove", "fill", "bass", "backing"))
            self.assertIn(c["bars"], (8, 16))
            self.assertIn(c["key"], ("C# minor", "F minor", ""))
            for part in c["parts"]:
                self.assertTrue(c["sounds"][part], f"{cid} {part}: some sound plays it")
                for sid in c["sounds"][part]:
                    f = self.ws.songs / "library" / c["loops"][part][sid]
                    self.assertEqual(c["loops"][part][sid], f"loops/{cid}__{part}__{sid}.ogg")
                    frames = decode(f)
                    self.assertEqual(len(frames), bars_to_frames(c["bars"]), f"{cid} {part} {sid}")
                    self.assertIsInstance(c["peak_db"][part][sid], float)
                    self.assertLess(c["peak_db"][part][sid], 0.0)
        for sid, s in idx["sounds"].items():
            self.assertEqual(set(s), CONTRACT_SOUND_KEYS, sid)
        self.assertEqual(idx["clips"]["acc_second_pulse"]["bars"], 16)
        self.assertEqual(idx["clips"]["acc_second_pulse"]["kind"], "backing")
        self.assertEqual(idx["clips"]["acc_second_pulse"]["sounds"], {"other": ["ensemble"]})
        self.assertEqual(idx["clips"]["acc_second_pulse"]["cues"], {}, "a backing has no cues")
        self.assertEqual(len(decode(self.ws.loop("acc_second_pulse", "other", "ensemble"))), bars_to_frames(16))
        self.assertFalse(idx["clips"]["groove_watch"]["bound"])
        self.assertEqual(idx["clips"]["groove_watch"]["sounds"]["kick"], ["kick_march", "kick_armour", "kick_siege", "kick_heavy"])
        self.assertEqual(idx["clips"]["bass_hold_b"]["sounds"]["bass"], ["bass_patrol", "bass_reese", "bass_growl", "bass_command", "bass_hollow"])
        self.assertTrue(idx["sounds"]["kick_march"]["placeholder"])
        self.assertFalse((self.ws.songs / "fixture_mission" / "audio").exists(), "a mission has no stems")

    def test_cues_kick_pad_one_snare_pad_four_ghosts_excluded_fill_in_bar_eight(self):
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        c = self.ws.index()["clips"]
        lib = res["library"]
        notes = lib.clips["groove_watch"].notes["kick"]
        want = sorted([n["tick"] + k * 2 * TICKS_PER_BAR, 0, 1] for k in range(4) for n in notes)
        self.assertEqual(c["groove_watch"]["cues"]["kick"], want, "a 2-bar groove's cues are tiled 4 times")
        self.assertEqual({q[2] for q in c["groove_watch"]["cues"]["snare"]}, {4})
        self.assertTrue(all(q[1] == 0 for q in c["groove_watch"]["cues"]["kick"]))
        fill = c["fill_break"]["cues"]
        self.assertTrue(all(q[0] >= 7 * TICKS_PER_BAR for p in fill.values() for q in p), "the fill's cues sit in bar 8")
        ghost = 7 * TICKS_PER_BAR + 7 * 240
        self.assertTrue(any(n["velocity"] < 64 for n in lib.clips["fill_break"].notes["snare"]), "the fill has a ghost note")
        self.assertEqual(len(fill["snare"]), sum(1 for n in lib.clips["fill_break"].notes["snare"] if n["velocity"] >= 64))
        self.assertNotIn(ghost, [q[0] for q in fill["snare"]])
        self.assertEqual({q[2] for q in fill["kick"]}, {1})
        self.assertEqual({q[2] for q in fill["snare"]}, {4})

    def test_bass_cues_follow_pitch_are_taps_and_are_thinned(self):
        bass = self.ws.lib / "bass_hold_b" / "bass.mid"
        notes = [(0, 3840, 40), (3840, 960, 44), (4000, 480, 48), (5760, 3840, 52), (7680, 480, 40), (8000, 480, 52), (9120, 960, 44),
                 (11000, 480, 48)]
        write_midi(bass, [{"tick": t, "duration_ticks": d, "pitch": p, "velocity": 100} for t, d, p in notes], "bass")
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        cues = self.ws.index()["clips"]["bass_hold_b"]["cues"]["bass"]
        # pitches 40 44 48 52 -> pads 1 2 3 4; the notes at 4000 (160 after 3840) and 8000 (320 after 7680) are dropped; 9120 is 1440 after 7680
        self.assertEqual(cues, [[0, 0, 1], [3840, 0, 2], [5760, 0, 4], [7680, 0, 1], [9120, 0, 2], [11000, 0, 3]])
        self.assertTrue(all(q[1] == 0 for q in cues), "taps only, whatever the note length")
        self.assertEqual(chart.pitch_pads([57]), {57: 2})
        self.assertEqual(chart.pitch_pads([60, 50, 55]), {50: 1, 55: 2, 60: 3})
        self.assertEqual(chart.pitch_pads(range(40, 48)), {40 + i: i // 2 + 1 for i in range(8)})
        seven = chart.pitch_pads([51, 53, 56, 57, 58, 59, 60, 53, 51])
        self.assertEqual([seven[p] for p in (51, 53, 56, 57, 58, 59, 60)], [1, 1, 2, 2, 3, 3, 4])

    def test_two_kicks_too_close_are_a_chart_error_naming_the_clip(self):
        self.ws.add_groove("groove_tight", [0, 240], [1920])
        res = self.ws.build()
        self.assertFalse(res["ok"])
        self.assertTrue(any("groove_tight (kick)" in e and "pad 1" in e for e in res["errors"]), res["errors"])
        self.assertEqual(self.ws.index(), TEMPLATE.index(), "nothing is rebuilt from a library that fails its checks")
        self.assertFalse(list((self.ws.songs / "library" / "loops").glob("groove_tight*")))

    def test_a_thumb_jump_that_is_too_fast_is_a_chart_error(self):
        bass = self.ws.lib / "bass_hold_b" / "bass.mid"
        write_midi(bass, [{"tick": 0, "duration_ticks": 480, "pitch": 40, "velocity": 100}, {"tick": 1440, "duration_ticks": 480, "pitch": 44, "velocity": 100}], "bass")
        rules = chart.load_rules()
        rules["chart"]["bass"]["min_gap_ticks"] = 0
        cues = [[0, 0, 1], [240, 0, 2]]
        self.assertTrue(any("left thumb" in m for m in chart.check_cues(cues, rules)))
        self.assertEqual(chart.check_cues([[0, 0, 1], [480, 0, 2], [960, 0, 3]], rules), [])
        self.assertTrue(any("pad 1 cues" in m for m in chart.check_cues([[0, 0, 1], [479, 0, 1]], rules)))

    def test_a_groove_and_fill_that_collide_are_a_chart_error_naming_the_pair(self):
        # an 8-bar groove with a kick 240 ticks before bar 8: fine alone (bars 1-7 are checked with the fill's bar 8 only together)
        self.ws.add_groove("groove_late", [0, 7 * TICKS_PER_BAR - 240], [1920])
        res = self.ws.build()
        self.assertFalse(res["ok"])
        pair = [e for e in res["errors"] if "groove groove_late with fill fill_break" in e]
        self.assertTrue(pair, res["errors"])
        self.assertFalse(any(e.startswith("groove_late (") for e in res["errors"]), "the groove alone is fine")
        self.assertFalse(any("groove groove_watch with fill" in e for e in res["errors"]), "the other groove still passes with the fill")

    def test_every_sound_needs_an_instruments_entry_and_valid_rewards(self):
        ins = read_json(INSTRUMENTS)
        del ins["kick_march"]
        self.ws.instruments = self.ws.tmp / "instruments.json"
        write_json(self.ws.instruments, ins)
        res = self.ws.build()
        self.assertFalse(res["ok"])
        self.assertTrue(any("kick_march has no entry" in e for e in res["errors"]), res["errors"])
        ins = read_json(INSTRUMENTS)
        ins["kick_march"] = {"produces": [{"reward": "jeep", "share": 1}], "blurb": "x"}
        ins["snare_guard"] = {"produces": [{"reward": "no_such_unit", "share": 1}], "blurb": "x"}
        write_json(self.ws.instruments, ins)
        res = self.ws.build()
        self.assertTrue(any("a kick sound cannot produce 'jeep'" in e for e in res["errors"]), res["errors"])
        self.assertTrue(any("'no_such_unit', which is not in data/campaign/rules.json rewards" in e for e in res["errors"]), res["errors"])

    def test_defaults_must_exist_and_play_together(self):
        self.ws.defaults["bass_sound"] = "bass_sub_deep"  # a recorded sound that bass_hold_b does not offer
        res = self.ws.build()
        self.assertFalse(res["ok"])
        self.assertTrue(any("bass_sound 'bass_sub_deep' does not play the default bass bass_hold_b" in e for e in res["errors"]), res["errors"])
        self.ws.defaults = dict(DEFAULTS, groove="nope")
        self.assertTrue(any("default groove 'nope'" in e for e in self.ws.build()["errors"]))

    def test_check_mode_validates_and_writes_nothing(self):
        self.ws.close()
        self.ws = Workspace(seeded=False)  # no placeholders, no loops, no state yet
        before = tree(self.ws.tmp)
        res = self.ws.build(check=True)
        self.assertTrue(res["ok"], res["errors"])
        self.assertEqual(tree(self.ws.tmp), before, "no file is added or changed")
        self.ws.add_groove("groove_tight", [0, 240], [1920])
        before = tree(self.ws.tmp)
        res = self.ws.build(check=True)
        self.assertFalse(res["ok"], "check mode runs the chart rules")
        self.assertEqual(tree(self.ws.tmp), before)

    def test_a_second_build_is_byte_identical_and_encodes_nothing(self):
        self.ws.close()
        self.ws = Workspace(seeded=False)
        self.assertTrue(self.ws.build()["ok"])
        first = tree(self.ws.tmp)
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        self.assertEqual(res["library"].encoded, 0, "an unchanged source is not re-encoded")
        self.assertEqual(tree(self.ws.tmp), first)

    def test_mission_naming_is_independent_of_the_library_build(self):
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        self.assertTrue((self.ws.songs / "library" / "index.json").exists())
        self.assertTrue((self.ws.songs / "fixture_mission" / "level.json").exists())
        (self.ws.songs / "fixture_mission" / "level.json").unlink()
        res = build.run(["no_such_mission"], library=self.ws.lib, missions=self.ws.missions, songs=self.ws.songs, sounds=CONTENT / "sounds.json",
                        state=self.ws.state, report=self.ws.tmp / "REPORT.md", defaults=DEFAULTS, quiet=True)
        self.assertTrue(res["ok"])
        self.assertFalse((self.ws.songs / "fixture_mission" / "level.json").exists())
        self.assertTrue((self.ws.songs / "library" / "index.json").exists())

    # --- the owner path ---------------------------------------------------------------------------------------------
    def test_owner_wav_replaces_the_placeholder_without_touching_either_file(self):
        self.assertTrue(self.ws.build()["ok"])
        ph = self.ws.lib / "groove_watch" / "placeholder" / "kick__kick_march.wav"
        ph_hash = sha256_file(ph)
        loop = self.ws.loop("groove_watch", "kick", "kick_march")
        loop_before = loop.read_bytes()
        owner = self.ws.lib / "groove_watch" / "kick__kick_march.wav"
        shutil.copy(FIX / "replacement" / "groove_watch" / "kick__kick_march.wav", owner)
        owner_hash = sha256_file(owner)
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        self.assertFalse(res["loops"][("groove_watch", "kick", "kick_march")]["placeholder"], "the owner render is used")
        self.assertTrue(res["loops"][("groove_watch", "kick", "kick_armour")]["placeholder"], "other sounds stay placeholder")
        self.assertEqual(res["library"].encoded, 1, "only the loop whose source changed is re-encoded")
        self.assertNotEqual(loop.read_bytes(), loop_before)
        self.assertEqual(sha256_file(owner), owner_hash, "the build never writes an owner file")
        self.assertEqual(sha256_file(ph), ph_hash, "the reference placeholder stays")
        self.assertIn("owner `", (self.ws.tmp / "REPORT.md").read_text(encoding="utf-8"))
        owner.unlink()
        res = self.ws.build()
        self.assertTrue(res["ok"])
        self.assertTrue(res["loops"][("groove_watch", "kick", "kick_march")]["placeholder"], "deleting it reverts to the placeholder")
        self.assertEqual(loop.read_bytes(), loop_before, "and the loop is what it was")

    def test_edited_midi_regenerates_cues_and_flags_a_stale_render(self):
        owner = self.ws.lib / "groove_watch" / "kick__kick_march.wav"
        shutil.copy(FIX / "replacement" / "groove_watch" / "kick__kick_march.wav", owner)
        self.assertTrue(self.ws.build()["ok"])
        before = self.ws.index()["clips"]["groove_watch"]["cues"]["kick"]
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
        after = self.ws.index()["clips"]["groove_watch"]["cues"]["kick"]
        self.assertEqual(len(after), len(before) + 4, "the extra kick in each of the four tiles is a new cue")
        self.assertIn([2880, 0, 1], after)
        self.assertEqual(sha256_file(self.ws.lib / "groove_watch" / "kick.mid"), sha256_file(edited), "the edited MIDI is kept")
        self.assertNotEqual(sha256_file(ph), ph_before, "placeholders follow the new MIDI")
        self.assertEqual(res["library"].clips["groove_watch"].midi_origin["kick"], "owner_edited")
        self.assertEqual(res["library"].clips["groove_watch"].tempo_source["kick"], "recorded_default", "no tempo in the file: 174 BPM recorded")
        shutil.copy(FIX / "replacement" / "groove_watch" / "kick__kick_march.wav", owner)
        self.assertTrue(self.ws.build()["ok"], "a render dropped in after the MIDI edit is accepted against the new MIDI")

    def test_copied_example_folder_becomes_a_clip_with_loops(self):
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        c = self.ws.index()["clips"]["example_groove"]
        self.assertEqual((c["kind"], c["name"], c["bars"]), ("groove", "Example Groove", 8))
        self.assertTrue(self.ws.loop("example_groove", "kick", "kick_march").exists())
        self.assertEqual(c["cues"]["kick"][:3], [[0, 0, 1], [2400, 0, 1], [3840, 0, 1]])

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

    def test_real_campaign_sources_are_untouched(self):
        integrity = read_json(CONTENT.parent / "campaign" / "Musical_Source_Integrity.json")["after_sha256"]
        for key, digest in integrity.items():
            path = CONTENT.parent / "campaign" / key
            if path.suffix == ".mid" and path.exists():
                self.assertEqual(sha256_file(path), digest, key)

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


class InstrumentsTests(unittest.TestCase):
    """data/campaign/instruments.json: what every sound produces."""

    def test_every_sound_has_a_valid_entry(self):
        sounds = read_json(CONTENT / "sounds.json")["sounds"]
        ins = read_json(INSTRUMENTS)
        rewards = read_json(ROOT / "data" / "campaign" / "rules.json")["rewards"]
        self.assertEqual(set(ins), {s["id"] for s in sounds})
        self.assertEqual(len(sounds), 30)
        for s in sounds:
            e = ins[s["id"]]
            self.assertTrue(e["blurb"], s["id"])
            if s["family"] == "other":
                self.assertEqual(e["produces"], [], s["id"])
                continue
            self.assertTrue(e["produces"], s["id"])
            for p in e["produces"]:
                self.assertIn(p["reward"], rewards, s["id"])
                self.assertIsInstance(p["share"], int)
                self.assertGreaterEqual(p["share"], 1)
                if s["family"] == "kick":
                    self.assertIn(p["reward"], build.INFANTRY)
                elif s["family"] == "snare":
                    self.assertEqual(rewards[p["reward"]]["type"], "build")
                else:
                    self.assertIn(p["reward"], build.VEHICLES)
        mix = lambda sid: [(p["reward"], p["share"]) for p in ins[sid]["produces"]]  # noqa: E731
        self.assertEqual(mix("kick_half_time"), [("rifle_squad", 2), ("grenadier_squad", 1)])
        self.assertEqual(mix("snare_crack"), [("pillbox", 2), ("turret", 1)])
        self.assertEqual(mix("bass_command"), [("arty", 1), ("2tnk", 1)])
        self.assertEqual(mix("bass_hollow"), [("ftrk", 1), ("apc", 1)])


class RealLibraryTests(unittest.TestCase):
    """The committed songs/library/index.json (written by tools/content/build.py)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.idx = read_json(SONGS / "library" / "index.json")

    def test_header_and_defaults(self):
        self.assertEqual(self.idx["format"], "rhythm_warfare.library.v1")
        self.assertEqual((self.idx["bpm"], self.idx["ticks_per_beat"], self.idx["loop_bars"]), (174, 960, 8))
        self.assertEqual(self.idx["defaults"], REAL_DEFAULTS)
        d = self.idx["defaults"]
        g, b, k = self.idx["clips"][d["groove"]], self.idx["clips"][d["bass"]], self.idx["clips"][d["backing"]]
        self.assertIn(d["kick_sound"], g["sounds"]["kick"])
        self.assertIn(d["snare_sound"], g["sounds"]["snare"])
        self.assertIn(d["bass_sound"], b["sounds"]["bass"])
        self.assertTrue(k["sounds"]["other"])

    def test_every_clip_and_sound_has_its_keys_and_every_loop_exists(self):
        self.assertEqual(len(self.idx["clips"]), 31)
        self.assertEqual(len(self.idx["sounds"]), 30)
        count = 0
        for cid, c in self.idx["clips"].items():
            self.assertEqual(set(c), CONTRACT_CLIP_KEYS, cid)
            self.assertEqual(c["bars"], 16 if cid in ("acc_second_pulse", "acc_hold_the_line", "acc_first_watch") else 8, cid)
            for part in c["parts"]:
                for sid in c["sounds"][part]:
                    f = SONGS / "library" / c["loops"][part][sid]
                    self.assertTrue(f.exists() and f.stat().st_size > 1000, f)
                    self.assertIn(sid, self.idx["sounds"])
                    self.assertEqual(self.idx["sounds"][sid]["family"], part, f"{cid}: {sid} plays the {part} part")
                    count += 1
        self.assertEqual(count, 117)
        self.assertEqual(len(list((SONGS / "library" / "loops").glob("*.ogg"))), count, "no stale loops")
        for sid, s in self.idx["sounds"].items():
            self.assertEqual(set(s), CONTRACT_SOUND_KEYS, sid)
        self.assertEqual(self.idx["sounds"]["kick_half_time"]["produces"], [{"reward": "rifle_squad", "share": 2}, {"reward": "grenadier_squad", "share": 1}])

    def test_bound_clips_offer_only_their_recordings_and_generated_clips_every_free_sound(self):
        c = self.idx["clips"]
        self.assertTrue(all(c[x]["bound"] for x in ("groove_half_time", "groove_double_step", "groove_rolling", "bass_sub_line", "bass_reese_line", "acc_hats_driving")))
        self.assertEqual(c["groove_half_time"]["sounds"], {"kick": ["kick_half_time"], "snare": ["snare_backbeat"]})
        self.assertEqual(c["groove_double_step"]["sounds"]["kick"], ["kick_double_step"])
        self.assertEqual(c["groove_rolling"]["sounds"]["kick"], ["kick_rolling"])
        self.assertEqual(len(c["bass_sub_line"]["sounds"]["bass"]), 5)
        self.assertEqual(len(c["bass_reese_line"]["sounds"]["bass"]), 4)
        self.assertEqual(c["acc_hats_driving"]["sounds"], {"other": ["hats_driving"]})
        self.assertEqual(c["acc_hats_driving"]["cues"], {})
        free = {"kick": ["kick_march", "kick_armour", "kick_siege", "kick_heavy"], "snare": ["snare_guard", "snare_crack", "snare_clap", "snare_rim"]}
        for g in ("groove_push", "groove_roller", "groove_straight", "groove_twostep", "groove_watch", "fill_break", "fill_kick_drop", "fill_snare_run"):
            self.assertFalse(c[g]["bound"], g)
            self.assertEqual(c[g]["sounds"], free, g)
        for b in ("bass_hold_a", "bass_hold_b", "bass_hold_end", "bass_octaves", "bass_steps"):
            self.assertEqual(c[b]["sounds"]["bass"], ["bass_patrol", "bass_reese", "bass_growl", "bass_command", "bass_hollow"], b)
        self.assertEqual(c["acc_iron"]["sounds"], {"other": ["ensemble"]})
        for sid in ("kick_half_time", "bass_sub_bright", "hats_busy"):
            self.assertFalse(self.idx["sounds"][sid]["placeholder"], sid)
        self.assertTrue(self.idx["sounds"]["kick_march"]["placeholder"])

    def test_cue_rules_on_the_real_clips(self):
        c = self.idx["clips"]
        for cid, clip in c.items():
            for part, cues in clip["cues"].items():
                loop = clip["bars"] * TICKS_PER_BAR
                self.assertEqual(cues, sorted(cues), cid)
                for tick, dur, pad in cues:
                    self.assertTrue(0 <= tick < loop, cid)
                    self.assertEqual(dur, 0, "taps only")
                    if part == "kick":
                        self.assertEqual(pad, 1)
                    elif part == "snare":
                        self.assertEqual(pad, 4)
                    else:
                        self.assertIn(pad, (1, 2, 3, 4))
                if part == "bass":
                    for x, y in zip(cues, cues[1:]):
                        self.assertGreaterEqual(y[0] - x[0], 1440, cid)
            if clip["kind"] == "fill":
                self.assertTrue(all(q[0] >= 7 * TICKS_PER_BAR for p in clip["cues"].values() for q in p), cid)
        for cid in ("bass_sub_line", "bass_reese_line"):
            cues = c[cid]["cues"]["bass"]
            self.assertTrue(8 <= len(cues) <= 16, f"{cid}: {len(cues)} cues")
            self.assertGreaterEqual(len({q[2] for q in cues}), 3, "bass spreads over at least three pads")

    def test_every_groove_with_every_fill_passes_the_chart(self):
        rules = chart.load_rules()
        c = self.idx["clips"]
        seam = 7 * TICKS_PER_BAR
        grooves = [k for k, v in c.items() if v["kind"] == "groove"]
        fills = [k for k, v in c.items() if v["kind"] == "fill"]
        self.assertEqual((len(grooves), len(fills)), (8, 3))
        for g in grooves:
            for f in fills:
                cues = [q for p in c[g]["cues"].values() for q in p if q[0] < seam] + [q for p in c[f]["cues"].values() for q in p if q[0] >= seam]
                self.assertEqual(chart.check_cues(cues, rules), [], f"{g} with {f}")

    def test_rules_carry_the_bass_chart(self):
        rules = read_json(ROOT / "data" / "campaign" / "rules.json")
        self.assertEqual(rules["chart"]["bass"], {"pads": "pitch", "min_gap_ticks": 1440, "holds": False})
        self.assertEqual(rules["chart"]["same_pad_min_gap_ticks"], 480)


class MissionPackTests(unittest.TestCase):
    """Mission packs (schema 4) built from content/missions/level_NN.json."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp(prefix="rw_packs_"))
        cls.missions = {}
        cls.packs = {}
        for n in range(1, 11):
            m = mission_mod.build(MISSIONS / f"level_{n:02d}.json", cls.tmp, write=True)
            assert not m.errors, m.errors
            cls.missions[n] = m
            cls.packs[n] = read_json(cls.tmp / m.pack / "level.json")

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_ten_v4_packs_with_exactly_the_contract_keys(self):
        for n, pack in self.packs.items():
            self.assertEqual(set(pack), CONTRACT_PACK_KEYS, n)
            self.assertEqual(pack["schema_version"], 4)
            self.assertEqual((pack["number"], pack["level_id"]), (n, f"level_{n:02d}"))
            self.assertEqual(pack["bpm"], 174)
            self.assertEqual(pack["ticks_per_beat"], 960)
            self.assertEqual(pack["time_signature"], [4, 4])
            self.assertEqual(pack["roster"], "openra_mvp_01")
            self.assertEqual(pack["sequence_threshold"], 0.6)
            self.assertEqual(pack["sequence_bars"], 2, "sequences per phase are derived at runtime: bars / 2")
            for gone in ("stems", "cue_blocks", "choices", "previews", "names", "bound_sounds", "content", "placeholder", "intro", "mode"):
                self.assertNotIn(gone, pack)

    def test_packs_are_written_where_the_game_reads_them(self):
        folders = [read_json(MISSIONS / f"level_{n:02d}.json")["pack"] for n in range(1, 11)]
        legacy = [read_json(MISSIONS_LEGACY / f"level_{n:02d}.json")["pack"] for n in range(1, 11)]
        self.assertEqual(folders, legacy, "same pack folders as before")
        for n, folder in enumerate(folders, 1):
            self.assertEqual(read_json(SONGS / folder / "level.json"), self.packs[n], f"songs/{folder} is what the build writes")
            self.assertEqual(sorted(p.name for p in (SONGS / folder).iterdir()), ["level.json"], "no audio/ and no preview/")

    def test_phases_follow_the_form_and_cover_the_song(self):
        for n, pack in self.packs.items():
            legacy = read_json(MISSIONS_LEGACY / f"level_{n:02d}.json")
            src = read_json(MISSIONS / f"level_{n:02d}.json")
            self.assertEqual(src["form"], "".join(p["mode"][0].upper() for p in legacy["phases"]), n)
            self.assertEqual(src["bars"], legacy["bars"])
            self.assertEqual(src["bars"], 8 * len(src["form"]))
            self.assertEqual(pack["duration_ticks"], src["bars"] * TICKS_PER_BAR)
            self.assertEqual(len(pack["phases"]), len(src["form"]))
            for i, (ph, letter) in enumerate(zip(pack["phases"], src["form"])):
                self.assertEqual(ph, {"id": f"p{i + 1:02d}", "start_tick": i * 8 * TICKS_PER_BAR, "end_tick": (i + 1) * 8 * TICKS_PER_BAR,
                                      "mode": "drums" if letter == "D" else "bass"})
        self.assertEqual(read_json(MISSIONS / "level_01.json")["form"], "DDBDBDDBDBDBDDBD")
        for n in (2, 4, 6, 8):
            self.assertNotIn("B", read_json(MISSIONS / f"level_{n:02d}.json")["form"], f"mission {n} has no bass phase")

    def test_mission_one_waves_rules_and_base(self):
        pack = self.packs[1]
        waves = pack["waves"]
        self.assertEqual(len(waves), 25)
        for w in waves:
            self.assertIn(w["target"], ("defenses", "civilians", "core"))
            self.assertEqual(w["target_objective"], "barracks")
            self.assertLess(w["start_tick"], 116 * TICKS_PER_BAR + 1, "units need about 12 s to arrive")
        self.assertEqual({w["target"] for w in waves}, {"defenses", "civilians", "core"})
        self.assertGreaterEqual(sum(g["count"] for w in waves for g in w["groups"]), 260)
        self.assertEqual(sum(g["count"] for w in waves for g in w["groups"] if g["actor"] == "jeep"), 6)
        self.assertEqual({w["entry"] for w in waves if any(g["actor"] == "jeep" for g in w["groups"])}, {"left", "top", "right"})
        rules = pack["rules"]
        self.assertEqual(pack["battlefield"], "village_01")
        self.assertEqual(rules["units_per_point"], 14)
        self.assertEqual(rules["objective_hp"], {"barracks": 60000})
        self.assertEqual([(u["actor"], u["count"], u["point"]) for u in rules["start_units"]],
                         [("e1", 5, "defense_1"), ("e1", 5, "defense_2"), ("e1", 5, "defense_3")])
        self.assertEqual(pack["base"], {"production": ["barracks"], "entries": 3, "points": 3, "civilians": 10})
        self.assertEqual([i["bar"] for i in pack["intros"]], [1, 16])

    def test_the_base_follows_the_battlefield(self):
        self.assertEqual(self.packs[2]["base"], {"production": ["barracks", "factory"], "entries": 3, "points": 3, "civilians": 0})
        for n in range(2, 11):
            self.assertEqual(self.packs[n]["battlefield"], "defense_02")
            self.assertEqual(self.packs[n]["base"]["production"], ["barracks", "factory"])
            self.assertEqual(self.packs[n]["base"]["civilians"], 0)
        bf = read_json(ROOT / "data" / "battlefields" / "defense_02.json")
        self.assertEqual(self.packs[2]["base"]["entries"], len(bf["entries"]))
        self.assertEqual(self.packs[2]["base"]["points"], len(bf["defense_points"]))

    def test_waves_are_baked_as_before(self):
        for n, pack in self.packs.items():
            raw = read_json(ROOT / "data" / "campaign" / "waves" / f"level_{n:02d}.json")
            self.assertEqual(len(pack["waves"]), len(raw["waves"]), n)
            for w, r in zip(pack["waves"], raw["waves"]):
                self.assertEqual(w["id"], r["id"])
                self.assertEqual(w["via_defense_point"], {"left": "defense_1", "top": "defense_2", "right": "defense_3"}[r["entry"]])
                for g in w["groups"]:
                    self.assertIn("spawn_spacing_ticks", g)
                self.assertTrue(0 <= w["start_tick"] < pack["duration_ticks"])
            self.assertEqual({k: v for k, v in pack["rules"].items() if k in raw.get("rules", {})}, raw.get("rules", {}))

    def test_a_bad_target_class_is_refused_and_a_group_may_override(self):
        m = mission_mod.Mission(MISSIONS / "level_01.json")
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

    def test_a_form_that_does_not_match_the_bars_or_uses_other_letters_is_refused(self):
        tmp = Path(tempfile.mkdtemp(prefix="rw_form_"))
        try:
            waves = FIX / "waves_fixture.json"
            ok = mission_mod.build(write_slim_mission(tmp, waves), tmp / "songs", write=False)
            self.assertEqual(ok.errors, [])
            bad = mission_mod.build(write_slim_mission(tmp, waves, bars=24, form="DB"), tmp / "songs", write=False)
            self.assertTrue(any("16 bars" in e or "has 2 phases" in e for e in bad.errors), bad.errors)
            bad = mission_mod.build(write_slim_mission(tmp, waves, form="DX"), tmp / "songs", write=False)
            self.assertTrue(any("must be letters D (drums) and B (bass)" in e for e in bad.errors), bad.errors)
            self.assertFalse((tmp / "songs").exists(), "a refused mission writes nothing")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_slim_mission_files_carry_no_music(self):
        for n in range(1, 11):
            d = read_json(MISSIONS / f"level_{n:02d}.json")
            self.assertEqual(set(d) - {"note", "intros"}, {"level_id", "number", "title", "pack", "bars", "seed", "form", "battle"}, n)
            for fld in ("choices", "phases", "accompaniment", "bass_chart"):
                self.assertNotIn(fld, d)
        self.assertEqual([k for k in read_json(MISSIONS / "level_01.json")], ["level_id", "number", "title", "pack", "bars", "seed", "form", "battle", "intros", "note"])


DEFENSE_02_SHA256 = "29091ad2763ab22482aae0f2e7f8e79120008e8ff9244b8cd099cd95120a444c"  # data/battlefields/defense_02.json (LF)


class BattlefieldTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
