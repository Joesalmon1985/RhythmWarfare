"""Tests of the Ableton import path and of paired pattern/render content: the importer (resampling, trimming, gain,
end fade, MIDI cut and tempo), declared renders (a clip plays only its own recordings), bound sounds, audio-only
accompaniment, the accompaniment choice, and the compatibility the pack carries for the game.

    python -m unittest discover -s tools/content -p "test_*.py"      (tools/test.sh runs it too)

Everything is synthetic and built into a temporary folder; nothing touches content/ or songs/.
"""
from __future__ import annotations

import json
import math
import shutil
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build  # noqa: E402
from common import BPM, TICKS_PER_BAR, bars_to_frames, read_json, read_midi, read_wav, write_json  # noqa: E402
from import_ableton import Importer  # noqa: E402
from midi_reader import build_midi, ev_note_off, ev_note_on, ev_tempo, ev_time_sig  # noqa: E402

SR_IN = 44100
BAR_S = 4 * 60.0 / BPM


def wav44(path: Path, frames: np.ndarray) -> None:
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR_IN)
        wf.writeframes((np.clip(frames, -1, 1) * 32767).astype("<i2").tobytes())


def midi96(path: Path, notes: list[tuple[int, int, int]], tempo: bool = False) -> None:
    """Ableton-style type 0 file at 96 PPQ: (tick, length, pitch) at 96 PPQ, no tempo unless asked."""
    events = [ev_time_sig(4, 4)]
    if tempo:
        events.append(ev_tempo(120))
    for tick, length, pitch in notes:
        events.append(ev_note_on(tick, pitch, 100))
        events.append(ev_note_off(tick + length, pitch))
    path.write_bytes(build_midi(96, [events], 0))


def clicks(bars: float, beats: list[float], level: float = 0.9, decay_s: float = 0.03) -> np.ndarray:
    """A 44.1 kHz stereo file of `bars` bars with a decaying click at each beat position (0-based, per bar)."""
    n = int(round(bars * BAR_S * SR_IN))
    x = np.zeros((n, 2), dtype=np.float32)
    d = int(decay_s * SR_IN)
    env = level * np.exp(-np.arange(d) / (0.3 * d))
    for b in range(int(math.ceil(bars))):
        for beat in beats:
            s = int(round((b * BAR_S + beat * BAR_S / 4) * SR_IN))
            if s + d <= n:
                x[s:s + d, 0] += env
                x[s:s + d, 1] += env
    return x


def sine(bars: float, hz: float = 55.0, level: float = 0.5) -> np.ndarray:
    n = int(round(bars * BAR_S * SR_IN))
    t = np.arange(n) / SR_IN
    y = (level * np.sin(2 * np.pi * hz * t)).astype(np.float32)
    return np.stack([y, y], axis=1)


class ImportWorkspace:
    """A source folder of fake Ableton exports, a manifest, an empty library and sounds file, a mission."""

    def __init__(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="rw_import_"))
        self.src = self.tmp / "exports"
        self.src.mkdir()
        self.lib = self.tmp / "library"
        self.lib.mkdir()
        self.sounds = self.tmp / "sounds.json"
        self.missions = self.tmp / "missions"
        self.missions.mkdir()
        self.songs = self.tmp / "songs"
        self.state = self.tmp / "build_state.json"
        self.instruments = self.tmp / "instruments.json"
        mix = {"t_kick_a": "rifle_squad", "t_kick_b": "grenadier_squad", "t_snare": "pillbox", "t_bass_a": "jeep", "t_bass_b": "apc", "t_bass_c": "1tnk"}
        write_json(self.instruments, {**{k: {"produces": [{"reward": v, "share": 1}], "blurb": k} for k, v in mix.items()},
                                      "t_other_1": {"produces": [], "blurb": "backing"}, "t_other_2": {"produces": [], "blurb": "backing"}})
        self.defaults = {"groove": "t_groove_a", "fill": "", "kick_sound": "t_kick_a", "snare_sound": "t_snare", "bass": "t_bass_one",
                         "bass_sound": "t_bass_b", "backing": "t_acc_one"}
        bar96 = 96 * 4
        # drums: 16 bars of MIDI (the clip is 8), 8-bar recordings; kick on beat 1 (and beat 3 in bar 2 of every pair)
        midi96(self.src / "KickA.mid", [(b * bar96, 96, 36) for b in range(16)] + [(b * bar96 + 2 * 96, 96, 36) for b in range(1, 16, 2)])
        midi96(self.src / "KickB.mid", [(b * bar96, 96, 36) for b in range(16)])
        midi96(self.src / "Snare.mid", [(b * bar96 + 2 * 96, 48, 38) for b in range(16)])
        extra = clicks(8, [2])
        for b in range(0, 8, 2):  # the beat-3 kick only in the even bars (bar 2, 4, ...)
            extra[int(round(b * BAR_S * SR_IN)):int(round((b + 1) * BAR_S * SR_IN))] = 0.0
        wav44(self.src / "KickA.wav", clicks(8, [0]) + extra)
        wav44(self.src / "KickB.wav", clicks(8, [0]))
        wav44(self.src / "Snare.wav", clicks(8, [2], level=0.95))
        # bass: 8 bars, one two-bar note then whole-bar notes; recordings: one ends mid-note (sine to the last sample),
        # one with a silent ninth bar, one with a long ringing tail
        midi96(self.src / "Bass.mid", [(0, 2 * bar96, 41)] + [(b * bar96, bar96, 41) for b in range(2, 8)])
        wav44(self.src / "bassA.wav", sine(8))
        wav44(self.src / "bassB.wav", np.vstack([sine(7.5, level=0.9), np.zeros((int(1.5 * BAR_S * SR_IN), 2), np.float32)]))
        wav44(self.src / "bassC.wav", np.vstack([sine(8), sine(2, level=0.2)]))
        # backing: 14 bars with silence after bar 8, and a plain 8-bar loop
        wav44(self.src / "Other1.wav", np.vstack([clicks(8, [1, 3], level=0.4), np.zeros((int(6 * BAR_S * SR_IN), 2), np.float32)]))
        wav44(self.src / "Other2.wav", clicks(8, [0.5, 1.5, 2.5, 3.5], level=0.4))
        self.manifest = self.tmp / "manifest.json"
        write_json(self.manifest, {
            "source_dir": str(self.src), "bars": 8, "trim_db": -8.0, "end_fade_ms": 10,
            "levels": {"kick": {"peak_db": -4.0}, "snare": {"peak_db": -4.0}, "bass": {"peak_db": -4.0, "rms_db": -17.0}, "other": {"peak_db": -3.0}},
            "sounds": [
                {"id": "t_kick_a", "family": "kick", "name": "Kick A"}, {"id": "t_kick_b", "family": "kick", "name": "Kick B"},
                {"id": "t_snare", "family": "snare", "name": "Snare T"},
                {"id": "t_bass_a", "family": "bass", "name": "Bass A"}, {"id": "t_bass_b", "family": "bass", "name": "Bass B"},
                {"id": "t_bass_c", "family": "bass", "name": "Bass C"},
                {"id": "t_other_1", "family": "other", "name": "Backing 1"}, {"id": "t_other_2", "family": "other", "name": "Backing 2"}],
            "clips": [
                {"id": "t_groove_a", "kind": "groove", "name": "Groove A", "parts": {
                    "kick": {"midi": "KickA.mid", "renders": {"t_kick_a": "KickA.wav"}},
                    "snare": {"midi": "Snare.mid", "renders": {"t_snare": "Snare.wav"}}}},
                {"id": "t_groove_b", "kind": "groove", "name": "Groove B", "parts": {
                    "kick": {"midi": "KickB.mid", "renders": {"t_kick_b": "KickB.wav"}},
                    "snare": {"midi": "Snare.mid", "renders": {"t_snare": "Snare.wav"}}}},
                {"id": "t_bass_one", "kind": "bass", "name": "Bass One", "key": "F minor", "parts": {
                    "bass": {"midi": "Bass.mid", "renders": {"t_bass_a": "bassA.wav", "t_bass_b": "bassB.wav"}}}},
                {"id": "t_bass_two", "kind": "bass", "name": "Bass Two", "key": "F minor", "parts": {
                    "bass": {"midi": "Bass.mid", "renders": {"t_bass_c": "bassC.wav"}}}},
                {"id": "t_acc_one", "kind": "accompaniment", "name": "Backing One", "key": "F minor", "audio_only": True, "parts": {
                    "other": {"renders": {"t_other_1": "Other1.wav"}}}},
                {"id": "t_acc_two", "kind": "accompaniment", "name": "Backing Two", "key": "F minor", "audio_only": True, "parts": {
                    "other": {"renders": {"t_other_2": "Other2.wav"}}}},
            ]})
        shutil.copy(Path(__file__).resolve().parents[2] / "content" / "fixtures" / "waves_fixture.json", self.tmp / "waves.json")

    def mission(self, **over) -> Path:
        m = {"level_id": "level_import", "number": 98, "title": "Import", "pack": "import_mission", "bars": 16, "seed": 98, "form": "DB",
             "battle": {"battlefield": "defense_02", "waves": str(self.tmp / "waves.json")}}
        m.update(over)
        path = self.missions / "level_import.json"
        write_json(path, m)
        return path

    def build(self) -> dict:
        self.mission()
        return build.run(library=self.lib, missions=self.missions, songs=self.songs, sounds=self.sounds, state=self.state,
                         report=self.tmp / "REPORT.md", instruments=self.instruments, defaults=self.defaults, quiet=True)

    def index(self) -> dict:
        return read_json(self.songs / "library" / "index.json")

    def level(self) -> dict:
        return read_json(self.songs / "import_mission" / "level.json")

    def close(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


class ImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = ImportWorkspace()
        self.imp = Importer(self.ws.manifest, library=self.ws.lib, sounds_path=self.ws.sounds)
        self.imp.run()

    def tearDown(self) -> None:
        self.ws.close()

    def test_wavs_are_48k_stereo_16bit_at_the_clip_length_with_the_originals_untouched(self):
        for clip, name in [("t_groove_a", "kick__t_kick_a"), ("t_groove_a", "snare__t_snare"), ("t_bass_one", "bass__t_bass_a"), ("t_acc_two", "other__t_other_2")]:
            frames, fmt = read_wav(self.ws.lib / clip / f"{name}.wav")
            self.assertEqual((fmt["sample_rate"], fmt["channels"], fmt["sample_width"]), (48000, 2, 2), name)
            self.assertEqual(fmt["frames"], bars_to_frames(8), f"{name}: exactly the clip's bars (no tail to keep)")
        with wave.open(str(self.ws.src / "KickA.wav")) as wf:
            self.assertEqual((wf.getframerate(), wf.getnframes()), (SR_IN, int(round(8 * BAR_S * SR_IN))), "the export is left as it was")

    def test_resampling_keeps_the_timing_of_every_attack(self):
        frames, _ = read_wav(self.ws.lib / "t_groove_a" / "kick__t_kick_a.wav")
        mono = np.abs(frames[:, 0])
        clip = read_midi(self.ws.lib / "t_groove_a" / "kick.mid")["notes"]
        self.assertEqual(len(clip), 8 + 4, "16 bars of MIDI cut to the clip's 8")
        for n in clip:
            s = int(round(n["tick"] * 48000 * 60 / (BPM * 960)))
            self.assertLess(mono[max(s - 240, 0):s - 24].max() if s > 240 else 0.0, 0.05, "quiet just before the attack")
            self.assertGreater(mono[s:s + 48].max(), 0.15, f"attack at MIDI tick {n['tick']} within a millisecond (peak -12 dBFS = 0.25)")

    def test_midi_is_cut_to_the_clip_and_carries_the_tempo(self):
        info = read_midi(self.ws.lib / "t_groove_a" / "snare.mid")
        self.assertEqual(info["tempo_source"], "midi")
        self.assertAlmostEqual(info["tempo_bpm"], 174.0, places=3)
        self.assertEqual([n["tick"] for n in info["notes"]], [b * TICKS_PER_BAR + 2 * 960 for b in range(8)])
        self.assertEqual({n["duration_ticks"] for n in info["notes"]}, {480}, "lengths kept exactly (96 -> 960 PPQ)")
        bass = read_midi(self.ws.lib / "t_bass_one" / "bass.mid")["notes"]
        self.assertEqual(bass[0]["duration_ticks"], 2 * TICKS_PER_BAR, "a two-bar hold stays two bars")

    def test_gain_rules_trim_and_end_fade(self):
        rows = {(r["clip"], r["file"]): r for r in self.imp.rows if r["kind"] == "wav"}
        self.assertAlmostEqual(rows[("t_groove_a", "KickA.wav")]["peak_db"], -12.0, delta=0.05, msg="peak_db -4 plus trim -8")
        self.assertAlmostEqual(rows[("t_acc_two", "Other2.wav")]["peak_db"], -11.0, delta=0.05)
        a = rows[("t_bass_one", "bassA.wav")]
        self.assertLessEqual(a["peak_db"], -12.0 + 0.05, "the peak ceiling holds when the RMS target would exceed it")
        self.assertTrue(a["faded"], "a recording cut mid-note is faded at its end")
        frames, _ = read_wav(self.ws.lib / "t_bass_one" / "bass__t_bass_a.wav")
        self.assertLess(abs(float(frames[-1, 0])), 0.002, "the last sample is at zero: no click at the loop point")
        self.assertGreater(abs(frames[-2000:-1500, 0]).max(), 0.05, "the fade is short: 40 ms before the end the note is still there")
        b = rows[("t_bass_one", "bassB.wav")]
        self.assertFalse(b["faded"], "a recording whose note ends inside the clip is not touched")
        self.assertEqual(b["tail_frames"], 0, "a silent ninth bar is dropped")
        c = rows[("t_bass_two", "bassC.wav")]
        self.assertEqual(c["tail_frames"], bars_to_frames(1), "a ringing tail is kept up to one bar")
        self.assertTrue(any("still sounding" in w for w in self.imp.warnings), "and the owner is told it was cut there")
        o = rows[("t_acc_one", "Other1.wav")]
        self.assertAlmostEqual(o["dropped_frames"], bars_to_frames(14) - bars_to_frames(8), delta=2, msg="six silent bars dropped")
        frames, fmt = read_wav(self.ws.lib / "t_acc_one" / "other__t_other_1.wav")
        self.assertEqual(fmt["frames"], bars_to_frames(8))

    def test_clips_declare_their_renders_and_sounds_are_registered(self):
        clip = read_json(self.ws.lib / "t_bass_one" / "clip.json")
        self.assertEqual(clip["sounds"], {"bass": ["t_bass_a", "t_bass_b"]})
        self.assertEqual(clip["source"]["type"], "imported")
        self.assertEqual(clip["source"]["parts"]["bass"]["notes_kept"], 7)
        acc = read_json(self.ws.lib / "t_acc_one" / "clip.json")
        self.assertTrue(acc["audio_only"])
        self.assertFalse((self.ws.lib / "t_acc_one" / "other.mid").exists())
        sounds = {s["id"]: s for s in read_json(self.ws.sounds)["sounds"]}
        self.assertEqual(sounds["t_bass_c"], {"id": "t_bass_c", "family": "bass", "name": "Bass C"})
        self.assertNotIn("synth", sounds["t_kick_a"], "an imported sound has no placeholder synth")

    def test_rerun_is_idempotent(self):
        before = {p.name: p.read_bytes() for p in (self.ws.lib / "t_bass_one").iterdir()}
        Importer(self.ws.manifest, library=self.ws.lib, sounds_path=self.ws.sounds).run()
        after = {p.name: p.read_bytes() for p in (self.ws.lib / "t_bass_one").iterdir()}
        self.assertEqual(before, after)

    def test_library_pairs_patterns_with_their_own_recordings(self):
        res = self.ws.build()
        self.assertTrue(res["ok"], res["errors"])
        idx = self.ws.index()
        self.assertEqual(set(idx["clips"]), {"t_groove_a", "t_groove_b", "t_bass_one", "t_bass_two", "t_acc_one", "t_acc_two"})
        self.assertTrue(all(c["bound"] for c in idx["clips"].values()), "every imported clip declares its renders")
        self.assertEqual(idx["clips"]["t_groove_a"]["sounds"], {"kick": ["t_kick_a"], "snare": ["t_snare"]})
        self.assertEqual(idx["clips"]["t_groove_b"]["sounds"], {"kick": ["t_kick_b"], "snare": ["t_snare"]})
        self.assertEqual(idx["clips"]["t_bass_one"]["sounds"], {"bass": ["t_bass_a", "t_bass_b"]}, "no loop for a recording with another clip's pattern")
        self.assertEqual(idx["clips"]["t_bass_two"]["sounds"], {"bass": ["t_bass_c"]})
        self.assertEqual(idx["clips"]["t_acc_one"]["sounds"], {"other": ["t_other_1"]})
        self.assertEqual((idx["clips"]["t_acc_one"]["kind"], idx["clips"]["t_acc_one"]["cues"], idx["clips"]["t_acc_one"]["parts"]), ("backing", {}, ["other"]))
        self.assertEqual(idx["clips"]["t_acc_one"]["key"], "F minor")
        self.assertFalse(any(s["placeholder"] for s in idx["sounds"].values()), "every sound is a recording")
        self.assertEqual(idx["sounds"]["t_kick_b"]["name"], "Kick B")
        self.assertEqual(idx["sounds"]["t_kick_b"]["produces"], [{"reward": "grenadier_squad", "share": 1}])
        for cid, c in idx["clips"].items():
            for part in c["parts"]:
                for sid, f in c["loops"][part].items():
                    self.assertTrue((self.ws.songs / "library" / f).exists(), f)
        self.assertEqual(len(idx["clips"]["t_groove_a"]["cues"]["kick"]), 12)
        self.assertEqual(len(idx["clips"]["t_groove_b"]["cues"]["kick"]), 8)
        self.assertEqual({q[2] for q in idx["clips"]["t_groove_a"]["cues"]["snare"]}, {4})
        bass = idx["clips"]["t_bass_one"]["cues"]["bass"]
        self.assertEqual(bass[:2], [[0, 0, 2], [2 * TICKS_PER_BAR, 0, 2]], "one pitch: pad 2; the two-bar note is a tap like the rest")
        self.assertTrue(all(q[1] == 0 for q in bass))
        self.assertEqual(self.ws.level()["base"]["production"], ["barracks", "factory"])

    def test_an_incompatible_default_or_a_missing_declared_render_is_refused(self):
        self.ws.defaults["bass"] = "t_bass_two"  # t_bass_b is a recording of the other bass line
        res = self.ws.build()
        self.assertFalse(res["ok"])
        self.assertTrue(any("does not play the default" in e for e in res["errors"]), res["errors"])
        self.ws.defaults["bass"] = "t_bass_one"
        (self.ws.lib / "t_bass_two" / "bass__t_bass_c.wav").unlink()
        res = self.ws.build()
        self.assertFalse(res["ok"])
        self.assertTrue(any("declares the render bass__t_bass_c.wav but the file is missing" in e for e in res["errors"]), res["errors"])

    def test_check_mode_writes_nothing(self):
        ws = ImportWorkspace()
        try:
            imp = Importer(ws.manifest, check=True, library=ws.lib, sounds_path=ws.sounds)
            imp.run()
            self.assertEqual(list(ws.lib.iterdir()), [])
            self.assertFalse(ws.sounds.exists())
            self.assertEqual(len([r for r in imp.rows if r["kind"] == "wav"]), 9, "the snare is imported once per groove")
        finally:
            ws.close()


if __name__ == "__main__":
    unittest.main()
