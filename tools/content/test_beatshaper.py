"""Tests for tools/content/beatshaper.py with synthetic Beat Shaper exports (no real recordings needed): grouping by project and variant,
tempo-profile verification, loops, tiers, the validator and assigning a pack to a level."""
import io
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np

try:  # the tests also run without mido: a tiny writer produces the same kind of file the exports are
    import mido
except ImportError:
    mido = None

sys.path.insert(0, str(Path(__file__).resolve().parent))

import beatshaper as bs  # noqa: E402
from common import ContentError, write_json  # noqa: E402

SR = 48000


def float_wav(frames: np.ndarray) -> bytes:
    """A 32-bit float stereo WAV like the owner's exports."""
    data = frames.astype("<f4").tobytes()
    fmt = struct.pack("<HHIIHH", 3, 2, SR, SR * 8, 8, 32)
    return b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt " + struct.pack("<I", 16) + fmt + b"data" + struct.pack("<I", len(data)) + data


def _vlq(v: int) -> bytes:
    out = [v & 0x7F]
    v >>= 7
    while v:
        out.append((v & 0x7F) | 0x80)
        v >>= 7
    return bytes(reversed(out))


def midi_bytes(notes: list[tuple], ppq: int = 120) -> bytes:
    if mido is None:
        events = []
        for beat, pitch, dur in notes:
            events.append((round(beat * ppq), 1, bytes([0x90, pitch, 100])))
            events.append((round((beat + dur) * ppq), 0, bytes([0x80, pitch, 0])))
        trk = b"\x00\xff\x51\x03" + (500000).to_bytes(3, "big")  # the headers lie: 120 BPM
        t = 0
        for tick, _o, msg in sorted(events, key=lambda e: (e[0], e[1])):
            trk += _vlq(tick - t) + msg
            t = tick
        trk += b"\x00\xff\x2f\x00"
        return b"MThd" + struct.pack(">IHHH", 6, 0, 1, ppq) + b"MTrk" + struct.pack(">I", len(trk)) + trk
    mid = mido.MidiFile(ticks_per_beat=ppq)
    tr = mido.MidiTrack()
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120)))  # the headers lie: 120 BPM
    events = []
    for beat, pitch, dur in notes:
        events.append((round(beat * ppq), 1, mido.Message("note_on", note=pitch, velocity=100)))
        events.append((round((beat + dur) * ppq), 0, mido.Message("note_off", note=pitch, velocity=0)))
    t = 0
    for tick, _o, msg in sorted(events, key=lambda e: (e[0], e[1])):
        msg.time = tick - t
        t = tick
        tr.append(msg)
    mid.tracks.append(tr)
    buf = io.BytesIO()
    mid.save(file=buf)
    return buf.getvalue()


def export_set(bpm: float, project: str = "Lv9 Test", suffix: str = "", beats: int = 16, kick: int = 36, snare: int = 40, bass_shift_s: float = 0.0,
               ghost_s: float = 0.0) -> dict[str, bytes]:
    """Drums with a click per kick/snare note at `bpm`, a bass changing note every 4 beats, a quiet synth; 120 BPM in every MIDI header."""
    spb = 60.0 / bpm
    n = int((beats * spb + 0.6) * SR)
    rng = np.random.default_rng(1)
    drums = np.zeros(n)
    dn = []
    for b in range(beats):
        if b % 2 == 0:
            dn.append((float(b), kick, 0.25))
        else:
            dn.append((float(b), snare, 0.25))
        dn.append((b + 0.5, 42, 0.25))  # hats are in the MIDI but not cues
        for off, amp in ((0.0, 1.0),) if b % 2 == 0 else ((0.0, 0.8),):
            i = int((b + off) * spb * SR) + (int(ghost_s * SR) if b == 5 else 0)  # `ghost_s`: one snare sounds late (a soft transient)
            burst = 0.25 * rng.standard_normal(int(0.03 * SR)) * np.exp(-np.arange(int(0.03 * SR)) / (0.006 * SR)) * amp
            drums[i:i + len(burst)] += burst
    t = np.arange(n) / SR
    bass = np.zeros(n)
    bn = []
    for k, pitch in enumerate((40, 45, 38, 48)):
        a, z = int(k * 4 * spb * SR), int((k + 1) * 4 * spb * SR)
        f = 440.0 * 2 ** ((pitch - 69) / 12)
        bass[a:z] = 0.3 * np.sin(2 * np.pi * f * t[a:z]) + 0.1 * np.sin(2 * np.pi * 2 * f * t[a:z])
        bn.append((k * 4.0, pitch, 4.0))
    if bass_shift_s:  # the bass sounds late against its MIDI: the audio detector cannot confirm the notes
        bass = np.roll(bass, int(bass_shift_s * SR))
    synth = 0.05 * np.sin(2 * np.pi * 330 * t)
    sn = [(float(b), 60 + (b % 5), 0.5) for b in range(0, beats, 2)]
    stereo = lambda x: np.stack([x, x], axis=1)  # noqa: E731
    p = f"Beat Shaper - {project}"
    sfx = f" ({suffix})" if suffix else ""
    return {f"{p}-Drums{sfx}.wav": float_wav(stereo(drums)), f"{p}-Drums{sfx}.mid": midi_bytes(dn + [(beats - 0.01, 42, 0.01)]),
            f"{p}-Bass{sfx}.wav": float_wav(stereo(bass)), f"{p}-Bass{sfx}.mid": midi_bytes(bn),
            f"{p}-Synth{sfx}.wav": float_wav(stereo(synth)), f"{p}-Synth{sfx}.mid": midi_bytes(sn)}


def make_zip(path: Path, *sets: dict) -> None:
    with zipfile.ZipFile(path, "w") as z:
        for s in sets:
            for name, data in s.items():
                z.writestr("Export/" + name, data)


class Grouping(unittest.TestCase):
    def test_variants_stay_with_their_own_stems(self):
        with tempfile.TemporaryDirectory() as tmp:
            z = Path(tmp) / "pack.zip"
            make_zip(z, export_set(174.0), export_set(174.0, suffix="1"), export_set(174.0, suffix="2"), export_set(174.0, project="Lv2 Other"))
            groups, odd = bs.Source(z).groups()
            self.assertEqual(sorted(groups), [("Lv2 Other", 0), ("Lv9 Test", 0), ("Lv9 Test", 1), ("Lv9 Test", 2)])
            self.assertEqual(odd, [])
            self.assertEqual(groups[("Lv9 Test", 2)]["Bass"]["wav"], "Beat Shaper - Lv9 Test-Bass (2).wav")
            self.assertEqual(bs.slug("Lv9 Test", 2), "lv9_test_v2")

    def test_missing_and_odd_files_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            s = export_set(174.0)
            del s["Beat Shaper - Lv9 Test-Synth.mid"]
            s["notes.txt.wav"] = b"x"
            z = Path(tmp) / "pack.zip"
            make_zip(z, s)
            src = bs.Source(z)
            groups, odd = src.groups()
            self.assertEqual(bs.set_status(groups[("Lv9 Test", 0)]), ["Synth.mid"])
            self.assertEqual(odd, ["notes.txt.wav"])
            self.assertEqual(bs.fatal_missing(groups[("Lv9 Test", 0)]), [], "a missing Synth file never stops an import")
            parts, audio, midi = bs.load_set(src, "Lv9 Test", 0)
            self.assertEqual(sorted(midi), ["Bass", "Drums"])
            s2 = export_set(174.0)
            del s2["Beat Shaper - Lv9 Test-Bass.mid"]
            make_zip(Path(tmp) / "b.zip", s2)
            with self.assertRaises(ContentError) as ctx:
                bs.load_set(bs.Source(Path(tmp) / "b.zip"), "Lv9 Test", 0)
            self.assertIn("Bass.mid", str(ctx.exception))

    def test_folder_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, data in export_set(174.0).items():
                (Path(tmp) / name).write_bytes(data)
            groups, _ = bs.Source(Path(tmp)).groups()
            self.assertEqual(list(groups), [("Lv9 Test", 0)])


class Analysis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _src(self, bpm: float) -> bs.Source:
        z = self.dir / "e.zip"
        make_zip(z, export_set(bpm))
        return bs.Source(z)

    def test_a_174_export_verifies_without_a_tempo_override(self):
        a = bs.analyse(self._src(174.0), "Lv9 Test", 0, {})
        self.assertEqual(a["profile"], "beat_shaper_174x1")
        self.assertEqual(a["phrase_beats"], 16)
        self.assertEqual(a["loop_frames"], round(16 * 60 / 174 * SR))
        self.assertEqual(a["problems"], [])
        self.assertEqual(len(a["cues"]["bass"]), 4)
        counts = [len(a["tiers"][str(t)]["drums"]) for t in (1, 2, 3, 4)]
        self.assertEqual(counts, sorted(counts), "a higher tier never charts fewer cues")
        self.assertTrue(all(c[3] in ("kick", "snare") for c in a["cues"]["drums"]))

    def test_an_87_export_maps_two_game_beats_per_source_beat(self):
        a = bs.analyse(self._src(87.0), "Lv9 Test", 0, {})
        self.assertEqual(a["profile"], "beat_shaper_87x2")
        self.assertEqual(a["phrase_beats"], 32)
        self.assertEqual(a["cues"]["drums"][1][0], 2 * 960 * 1, "the snare on source beat 1 is game beat 2")

    def test_an_unknown_tempo_is_refused_not_guessed(self):
        with self.assertRaises(ContentError) as ctx:
            bs.analyse(self._src(130.0), "Lv9 Test", 0, {})
        self.assertIn("no tempo profile", str(ctx.exception))

    def test_forcing_a_profile_does_not_skip_verification(self):
        with self.assertRaises(ContentError):
            bs.analyse(self._src(174.0), "Lv9 Test", 0, {"profile": "beat_shaper_87x2"})

    def test_a_set_without_kick_or_snare_notes_says_which_notes_it_has(self):
        with self.assertRaises(ContentError) as ctx:
            bs.analyse(self._src(174.0), "Lv9 Test", 0, {"kick_notes": [1], "snare_notes": [2]})
        self.assertIn("42", str(ctx.exception))

    def _src_of(self, **kw) -> bs.Source:
        z = self.dir / "x.zip"
        make_zip(z, export_set(kw.pop("bpm", 174.0), **kw))
        return bs.Source(z)

    def test_a_late_bass_is_charted_from_the_midi_with_a_recorded_fallback(self):
        a = bs.analyse(self._src_of(bass_shift_s=0.07), "Lv9 Test", 0, {})
        self.assertEqual(a["report"]["bass_timing"]["mode"], "midi_fallback")
        self.assertTrue(any("charted from the MIDI timing" in w for w in a["warnings"]))
        self.assertEqual(len(a["cues"]["bass"]), 4)
        self.assertEqual(a["problems"], [])

    def test_trust_midi_is_an_explicit_flag_and_is_recorded(self):
        ok = bs.analyse(self._src_of(), "Lv9 Test", 0, {})
        self.assertEqual(ok["report"]["bass_timing"]["mode"], "audio_checked")
        a = bs.analyse(self._src_of(bass_shift_s=0.07), "Lv9 Test", 0, {"trust_midi": True})
        self.assertEqual(a["report"]["bass_timing"]["mode"], "midi_flag")
        out = bs.write_pack(self._src_of(), "Lv9 Test", 0, "lv9_flag", a, {"drums": 0.0, "bass": 3.0, "other": 10.0}, "x", self.dir / "packs")
        rep = json.loads((out / "timing_report.json").read_text())
        self.assertEqual(rep["timing"]["bass_timing"]["mode"], "midi_flag")
        self.assertIn("drum_notes", rep["import_report"])

    def test_kick_and_snare_are_found_when_36_38_40_are_absent(self):
        a = bs.analyse(self._src_of(kick=35, snare=45), "Lv9 Test", 0, {})
        self.assertEqual((a["kick"], a["snare"]), ([35], [45]))
        self.assertEqual(a["report"]["drum_notes"]["mode"], "auto")
        self.assertTrue(any("most common low note 35 = kick" in d for d in a["report"]["decisions"]))
        self.assertEqual({c[3] for c in a["cues"]["drums"]}, {"kick", "snare"})
        b = bs.analyse(self._src_of(kick=35, snare=45), "Lv9 Test", 0, {"kick_notes": [35], "snare_notes": [45]})
        self.assertEqual(b["report"]["drum_notes"]["mode"], "explicit")

    def test_choice_skips_hats_and_handles_one_candidate(self):
        hats = [{"beat": float(i), "pitch": 42, "dur": 0.1, "velocity": 90} for i in range(20)]
        mid = [{"beat": float(i), "pitch": 43, "dur": 0.1, "velocity": 90} for i in range(6)]
        low = [{"beat": float(i) + 0.5, "pitch": 39, "dur": 0.1, "velocity": 90} for i in range(3)]
        k, sn, how = bs.drum_note_choice(hats + mid + low, {})
        self.assertEqual((k, sn, how["mode"]), ({39}, {43}, "auto"))
        k, sn, _ = bs.drum_note_choice(hats + mid, {})
        self.assertEqual((k, sn), (set(), {43}))
        k, sn, how = bs.drum_note_choice(hats + mid, {"kick_notes": [42]})
        self.assertEqual((k, how["mode"]), ({42}, "explicit"))

    def test_a_single_soft_transient_is_a_reported_outlier_not_a_refusal(self):
        a = bs.analyse(self._src_of(ghost_s=0.027), "Lv9 Test", 0, {})
        self.assertEqual(a["report"]["tempo"]["verified"], "loose")
        self.assertTrue(any("verified loosely" in d for d in a["report"]["decisions"]))

    def test_a_missing_synth_is_a_silent_backing(self):
        s = export_set(174.0)
        for k in [k for k in s if "-Synth" in k]:
            del s[k]
        z = self.dir / "n.zip"
        make_zip(z, s)
        a = bs.analyse(bs.Source(z), "Lv9 Test", 0, {})
        self.assertEqual(float(np.abs(a["audio"]["Synth"]).max()), 0.0)
        self.assertTrue(any("Synth.wav is missing" in d for d in a["report"]["decisions"]))
        self.assertEqual(a["problems"], [])

    def test_a_set_with_audio_but_no_midi_says_what_to_export(self):
        s = {k: v for k, v in export_set(174.0).items() if k.endswith(".wav")}
        z = self.dir / "w.zip"
        make_zip(z, s)
        with self.assertRaises(ContentError) as ctx:
            bs.analyse(bs.Source(z), "Lv9 Test", 0, {})
        self.assertIn("Drums.mid", str(ctx.exception))
        self.assertIn("export", str(ctx.exception))

    def test_a_phrase_a_quarter_long_or_short_is_the_16_quarter_phrase(self):
        a = bs.analyse(self._src_of(), "Lv9 Test", 0, {})
        self.assertEqual(a["phrase_beats"], 16)

    def test_thin_keeps_source_timing_and_prefers_whole_beats(self):
        cues = [[0, 0, 1, "kick"], [480, 0, 4, "snare"], [960, 0, 1, "kick"], [1440, 0, 4, "snare"], [1920, 0, 1, "kick"]]
        t1 = bs.thin(cues, 1, "drums")
        self.assertEqual([c[0] for c in t1], [0, 960, 1920], "tier 1 keeps whole beats, a beat apart")
        self.assertEqual(len(bs.thin(cues, 4, "drums")), 5)
        for c in t1:
            self.assertIn(c, cues)

    def test_import_assign_validate_round_trip(self):
        packs = self.dir / "packs"
        music = self.dir / "music.json"
        run = self.dir / "run.json"
        write_json(run, {"nodes": [{"id": "a", "depth": 1}, {"id": "b", "depth": 2}, {"id": "c", "depth": 2}]})
        self.addCleanup(setattr, bs, "RUN_JSON", bs.RUN_JSON)
        self.addCleanup(setattr, bs, "TRIAL_JSON", bs.TRIAL_JSON)
        bs.TRIAL_JSON = self.dir / "no_trial.json"
        bs.RUN_JSON = run
        a = bs.analyse(self._src(174.0), "Lv9 Test", 0, {})
        bs.write_pack(self._src(174.0), "Lv9 Test", 0, "lv9_test", a, {"drums": 0.0, "bass": 3.0, "other": 10.0}, "Lv9 Test", packs)
        bs.write_pack(self._src(174.0), "Lv9 Test", 0, "lv9_alt", a, {"drums": 0.0, "bass": 3.0, "other": 10.0}, "Lv9 Test alt render", packs)
        write_json(music, {"nodes": [{"id": n, "audio": "lv9_test", "chart": "lv9_test", "treatment": "none", "temporary": True} for n in "abc"]})
        errors, notes = bs.validate(packs, music)
        self.assertEqual(errors, [])
        # a later level gets other recordings with the same MIDI: audio only
        bs.assign("c", "lv9_alt", None, "none", False, music)
        self.assertEqual(bs.validate(packs, music)[0], [])
        # a different chart for one sibling is allowed (each world its own song) but flagged as a warning
        bs.assign("c", None, "lv9_alt", None, None, music)
        errors, notes = bs.validate(packs, music)
        self.assertEqual(errors, [])
        self.assertTrue(any(n_.startswith("WARNING depth 2") and "no longer share one chart" in n_ for n_ in notes), notes)
        # an alternate render whose MIDI differs is refused
        pj = packs / "lv9_alt" / "pack.json"
        p = json.loads(pj.read_text())
        p["tiers"]["1"]["drums"] = p["tiers"]["1"]["drums"][1:]
        pj.write_text(json.dumps(p))
        bs.assign("c", "lv9_alt", "lv9_test", None, None, music)
        errors, _ = bs.validate(packs, music)
        self.assertTrue(any("MIDI differs" in e for e in errors), errors)
        # unknown node
        with self.assertRaises(ContentError):
            bs.assign("zzz", "lv9_test", None, None, None, music)
        # a missing stem file is reported
        (packs / "lv9_test" / "loops" / "bass.wav").unlink()
        errors, _ = bs.validate(packs, music)
        self.assertTrue(any("bass file" in e or "stem bass" in e for e in errors), errors)


class Committed(unittest.TestCase):
    def test_the_committed_data_validates(self):
        errors, _ = bs.validate()
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
