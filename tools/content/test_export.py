"""Tests of the MIDI export for missions 2 to 10 (tools/content/export_midi.py): determinism, file format, the A loops
against the library clips, the B/C variations, the import manifests, and a round trip through the importer.

    python -m unittest discover -s tools/content -p "test_*.py"      (tools/test.sh runs it too)
    python -m unittest tools.content.test_export -v

Everything is written into temporary folders; nothing touches midi_export/, content/imports/ or content/library/.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

import mido
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import export_midi as ex  # noqa: E402
import synth  # noqa: E402
from common import BPM, LIBRARY, PPQ, ROOT, SAMPLE_RATE, TICKS_PER_BAR, read_json, read_midi  # noqa: E402

LEVELS = list(range(2, 11))
NO_BASS_PHASE = {2, 4, 6, 8}
LONG_BACKING = {2: 40, 3: 48}
LOOP_FILES = ["Kick_A", "Snare_A", "Bass_A", "Kick_B", "Kick_C", "Snare_B", "Snare_C", "Bass_B", "Bass_C"]


def key(n: dict) -> tuple:
    return (n["tick"], n["duration_ticks"], n["pitch"], n["velocity"])


def keys(notes: list[dict]) -> list[tuple]:
    return sorted(key(n) for n in notes)


def track_ticks(path: Path) -> list[int]:
    """The length in ticks of every track of a MIDI file (sum of delta times, end-of-track included)."""
    return [sum(msg.time for msg in tr) for tr in mido.MidiFile(str(path)).tracks]


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp(prefix="rw_export_"))
        cls.out1, cls.imp1 = cls.tmp / "out1", cls.tmp / "imports1"
        cls.out2, cls.imp2 = cls.tmp / "out2", cls.tmp / "imports2"
        cls.info = ex.export_all(cls.out1, cls.imp1)
        ex.export_all(cls.out2, cls.imp2)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def folder(self, n: int) -> Path:
        return self.out1 / self.info[f"level_{n:02d}"]["folder_name"]

    def notes(self, n: int, name: str) -> list[dict]:
        return read_midi(self.folder(n) / f"{name}.mid")["notes"]

    # --- determinism and format ---------------------------------------------------------------------------------------
    def test_two_runs_are_byte_identical(self) -> None:
        a = sorted(p.relative_to(self.out1) for p in self.out1.rglob("*") if p.is_file())
        b = sorted(p.relative_to(self.out2) for p in self.out2.rglob("*") if p.is_file())
        self.assertEqual(a, b)
        self.assertEqual(len(a), 9 * 13 + 1)  # 12 MIDI + README per mission, plus the overview README
        for rel in a:
            self.assertEqual((self.out1 / rel).read_bytes(), (self.out2 / rel).read_bytes(), str(rel))
        for n in LEVELS:
            m1, m2 = self.imp1 / f"level_{n:02d}.json", self.imp2 / f"level_{n:02d}.json"
            self.assertEqual(m1.read_bytes(), m2.read_bytes(), m1.name)

    def test_text_files_use_lf(self) -> None:
        for p in list(self.out1.rglob("*.md")) + list(self.imp1.glob("*.json")):
            self.assertNotIn(b"\r", p.read_bytes(), str(p))

    def test_every_midi_reads_back(self) -> None:
        for n in LEVELS:
            for p in sorted(self.folder(n).glob("*.mid")):
                info = read_midi(p)
                self.assertEqual(info["ppq"], PPQ, p.name)
                self.assertEqual(info["tempo_bpm"], BPM, p.name)
                self.assertEqual(info["tempo_source"], "midi", p.name)
                self.assertEqual(info["meter"], [4, 4])
                mid = mido.MidiFile(str(p))
                self.assertEqual(mid.type, 1)
                if p.stem.startswith("Other"):
                    bars = LONG_BACKING.get(n, 8)
                elif p.stem == "Arrangement_A":
                    bars = read_json(ROOT / "content" / "missions" / f"level_{n:02d}.json")["bars"]
                else:
                    bars = 8
                for ticks in track_ticks(p):
                    self.assertEqual(ticks, bars * TICKS_PER_BAR, f"level {n} {p.name}")
                self.assertTrue(info["notes"], f"level {n} {p.name} has no notes")
                for note in info["notes"]:
                    self.assertLessEqual(note["tick"] + note["duration_ticks"], bars * TICKS_PER_BAR, f"level {n} {p.name}")

    def test_arrangement_has_four_named_tracks(self) -> None:
        for n in LEVELS:
            mid = mido.MidiFile(str(self.folder(n) / "Arrangement_A.mid"))
            self.assertEqual([t.name for t in mid.tracks[1:]], ["Kick", "Snare", "Bass", "Other"])
            self.assertEqual(len(mid.tracks), 5)

    # --- the A loops against the library ----------------------------------------------------------------------------
    @staticmethod
    def expected_drums(part: str, groove: str, fill: str | None) -> list[tuple]:
        """Bar by bar: the fill replaces the last bar of the 8; every other bar is the groove's bar (bar mod its length)."""
        g_bars = read_json(LIBRARY / groove / "clip.json")["bars"]
        g = read_midi(LIBRARY / groove / f"{part}.mid")["notes"]
        f = read_midi(LIBRARY / fill / f"{part}.mid")["notes"] if fill else []
        out = []
        for bar in range(8):
            if fill and bar == 7:
                src, base = f, 0
            else:
                src, base = g, (bar % g_bars) * TICKS_PER_BAR
            for note in src:
                if base <= note["tick"] < base + TICKS_PER_BAR:
                    out.append((bar * TICKS_PER_BAR + note["tick"] - base, note["duration_ticks"], note["pitch"], note["velocity"]))
        return sorted(out)

    def test_a_loops_equal_the_library_clips(self) -> None:
        for n in LEVELS:
            info = self.info[f"level_{n:02d}"]
            m = read_json(ROOT / "content" / "missions" / f"level_{n:02d}.json")
            self.assertEqual(info["fill"] is not None, any("fill" in ph for ph in m["phases"]), f"level {n}")
            for part, name in (("kick", "Kick_A"), ("snare", "Snare_A")):
                self.assertEqual(keys(self.notes(n, name)), self.expected_drums(part, info["groove"], info["fill"]), f"level {n} {name}")
            acc = read_midi(LIBRARY / info["acc"] / "other.mid")["notes"]
            pad, hats = self.notes(n, "Other_Pad"), self.notes(n, "Other_Hats")
            self.assertTrue(all(h["pitch"] in (42, 46) for h in hats))
            self.assertTrue(all(p["pitch"] not in (42, 46) for p in pad))
            self.assertEqual(keys(pad + hats), keys(acc), f"level {n} backing")
            self.assertEqual(max(h["tick"] for h in hats + pad) < LONG_BACKING.get(n, 8) * TICKS_PER_BAR, True)
            bass_a = self.notes(n, "Bass_A")
            if n in NO_BASS_PHASE:
                self.assertTrue(info["new_bass"])
                self.assertEqual([b["tick"] for b in bass_a], [0, 2 * TICKS_PER_BAR, 4 * TICKS_PER_BAR, 6 * TICKS_PER_BAR])
                self.assertTrue(all(32 <= b["pitch"] <= 42 and b["pitch"] % 12 in ex.SCALE_PCS for b in bass_a))
            else:
                self.assertFalse(info["new_bass"])
                self.assertEqual(keys(bass_a), keys(read_midi(LIBRARY / info["bass"] / "bass.mid")["notes"]), f"level {n} Bass_A")

    def test_root_lines_follow_the_chords(self) -> None:
        roots = {4: [37, 33, 40, 35], 2: [37, 33, 40, 35], 6: [37, 33, 42, 32], 8: [37, 35, 33, 32]}
        for n, expect in roots.items():
            self.assertEqual([b["pitch"] for b in self.notes(n, "Bass_A")], expect, f"level {n}")

    def test_arrangement_follows_the_phases(self) -> None:
        for n in LEVELS:
            m = read_json(ROOT / "content" / "missions" / f"level_{n:02d}.json")
            mid = mido.MidiFile(str(self.folder(n) / "Arrangement_A.mid"))
            per_track = {}
            for tr in mid.tracks[1:]:
                single = mido.MidiFile(type=1, ticks_per_beat=PPQ)
                single.tracks.append(tr)
                tmp = self.tmp / "one.mid"
                single.save(str(tmp))
                per_track[tr.name] = read_midi(tmp)["notes"]
            start = 0
            for ph in m["phases"]:
                end = start + ph["bars"] * TICKS_PER_BAR
                groove = ex.resolve(m, "groove", ph["groove"])
                fill = ex.resolve(m, "fill", ph["fill"]) if "fill" in ph else None
                for part, name in (("kick", "Kick"), ("snare", "Snare")):
                    got = sorted((k[0] - start,) + k[1:] for k in map(key, per_track[name]) if start <= k[0] < end)
                    # an 8-bar phase is exactly the 8-bar loop
                    self.assertEqual(got, self.expected_drums(part, groove, fill), f"level {n} {name} phase at {start}")
                bass = sorted((k[0] - start,) + k[1:] for k in map(key, per_track["Bass"]) if start <= k[0] < end)
                if "bass" in ph:
                    want = keys(read_midi(LIBRARY / ex.resolve(m, "bass", ph["bass"]) / "bass.mid")["notes"])
                    self.assertEqual(bass, want, f"level {n} bass phase at {start}")
                else:
                    self.assertEqual(bass, [])
                start = end
            acc = ex.resolve(m, "accompaniment", m["accompaniment"][0]["clip"])
            src = read_midi(LIBRARY / acc / "other.mid")["notes"]
            loop = read_json(LIBRARY / acc / "clip.json")["bars"] * TICKS_PER_BAR
            want = sorted((rep * loop + k[0],) + k[1:] for rep in range(m["bars"] * TICKS_PER_BAR // loop) for k in map(key, src))
            self.assertEqual(keys(per_track["Other"]), want, f"level {n} backing")

    # --- the alternatives --------------------------------------------------------------------------------------------
    def test_alternatives_stay_within_bounds(self) -> None:
        for n in LEVELS:
            for part in ("Kick", "Snare", "Bass"):
                a = self.notes(n, f"{part}_A")
                self.assertTrue(ex.gap_ok(a), f"level {n} {part}_A breaks the gap rule")
                limit = max(-(-len(a) // 4), 4)
                self.assertEqual(ex.variation_limit(len(a)), limit)
                variants = {v: self.notes(n, f"{part}_{v}") for v in "BC"}
                for v, b in variants.items():
                    tag = f"level {n} {part}_{v}"
                    self.assertTrue(ex.gap_ok(b), f"{tag} breaks the same-pad gap or overlaps")
                    self.assertLessEqual(max(x["tick"] + x["duration_ticks"] for x in b), 8 * TICKS_PER_BAR, tag)
                    self.assertGreaterEqual(min(x["tick"] for x in b), 0, tag)
                    for w in range(4):
                        self.assertGreaterEqual(ex.window_edits(a, b, w), 1, f"{tag}: bars {2 * w + 1}-{2 * w + 2} unchanged")
                    self.assertLessEqual(ex.edit_distance(a, b), limit, f"{tag}: {ex.edit_distance(a, b)} edits > {limit}")
                    if part == "Bass":
                        self.assertTrue(all(x["pitch"] % 12 in ex.SCALE_PCS for x in b), f"{tag} leaves C# natural minor")
                    else:
                        self.assertTrue(all(x["pitch"] in (36, 38, 48) for x in b), tag)
                self.assertNotEqual(keys(variants["B"]), keys(variants["C"]), f"level {n} {part}: B equals C")

    def test_alternatives_depend_on_the_seed_only(self) -> None:
        a = self.notes(7, "Snare_A")
        b1 = ex.vary("snare", a, 1007, "B")[0]
        b2 = ex.vary("snare", a, 1007, "B")[0]
        b3 = ex.vary("snare", a, 4242, "B")[0]
        self.assertEqual(keys(b1), keys(b2))
        self.assertEqual(keys(b1), keys(self.notes(7, "Snare_B")))
        self.assertTrue(ex.gap_ok(b3))

    # --- manifests ---------------------------------------------------------------------------------------------------
    def test_manifests_name_existing_midi(self) -> None:
        first = read_json(ROOT / "content" / "imports" / "first_watch.json")
        for n in LEVELS:
            p = f"m{n:02d}"
            m = read_json(self.imp1 / f"level_{n:02d}.json")
            folder_name = self.info[f"level_{n:02d}"]["folder_name"]
            self.assertEqual(m["source_dir"], f"midi_export/{folder_name}")
            self.assertEqual(m["bars"], 8)
            self.assertEqual((m["levels"], m["trim_db"], m["end_fade_ms"]), (first["levels"], first["trim_db"], first["end_fade_ms"]))
            self.assertTrue(m["note"])
            sounds = {s["id"]: s["family"] for s in m["sounds"]}
            want = {f"{p}_{f}_{v}": f for f in ("kick", "snare", "bass") for v in "abc"}
            want.update({f"{p}_pad": "other", f"{p}_hats": "other"})
            self.assertEqual(sounds, want)
            self.assertEqual([c["id"] for c in m["clips"]], [f"{p}_{k}_{v}" for k in ("groove",) for v in "abc"]
                             + [f"{p}_bass_{v}" for v in "abc"] + [f"{p}_backing"])
            used = set()
            for c in m["clips"]:
                for part, spec in c["parts"].items():
                    if "midi" in spec:
                        self.assertTrue((self.out1 / folder_name / spec["midi"]).is_file(), f"{c['id']}: {spec['midi']}")
                        self.assertTrue(spec["midi"].endswith(".mid"))
                    for sid, wav in spec["renders"].items():
                        self.assertEqual(sounds[sid], part)
                        used.add(sid)
                        if "midi" in spec:
                            self.assertEqual(wav, spec["midi"][:-4] + ".wav")
                        else:
                            self.assertTrue((self.out1 / folder_name / (wav[:-4] + ".mid")).is_file())
                if c["kind"] == "bass":
                    self.assertEqual(c["key"], "C# minor")
            self.assertEqual(used, set(sounds))
            backing = m["clips"][-1]
            self.assertEqual((backing["kind"], backing["audio_only"]), ("accompaniment", True))
            if n in LONG_BACKING:
                self.assertIn(str(LONG_BACKING[n]), backing["note"])

    def test_gitignore_ignores_the_wavs(self) -> None:
        lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("midi_export/**/*.wav", lines)

    # --- the round trip ----------------------------------------------------------------------------------------------
    def test_round_trip_through_the_importer(self) -> None:
        """Render every WAV the level_04 manifest names with the placeholder synth into a copy of the export folder and
        run the importer's --check on a manifest that points there."""
        sounds = {s["id"]: s["synth"] for s in read_json(ROOT / "content" / "sounds.json")["sounds"] if s.get("synth")}
        placeholder = {"kick": "kick_march", "snare": "snare_guard", "bass": "bass_patrol", "other": "ensemble"}
        manifest = read_json(self.imp1 / "level_04.json")
        src = self.out1 / self.info["level_04"]["folder_name"]
        rt = self.tmp / "roundtrip"
        shutil.copytree(src, rt)
        count = 0
        for clip in manifest["clips"]:
            for part, spec in clip["parts"].items():
                for sid, wav in spec["renders"].items():
                    notes = read_midi(rt / (wav[:-4] + ".mid"))["notes"]
                    audio = synth.render_part(part, notes, 8, sounds[placeholder[part]], f"{sid}")
                    stereo = np.stack([audio, audio], axis=1)
                    with wave.open(str(rt / wav), "wb") as wf:
                        wf.setnchannels(2)
                        wf.setsampwidth(2)
                        wf.setframerate(SAMPLE_RATE)
                        wf.writeframes((np.clip(stereo, -1, 1) * 32767).astype("<i2").tobytes())
                    count += 1
        self.assertEqual(count, 11)
        manifest["source_dir"] = str(rt)
        mpath = self.tmp / "level_04_roundtrip.json"
        mpath.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        run = subprocess.run([sys.executable, str(ROOT / "tools" / "content" / "import_ableton.py"), str(mpath), "--check"],
                             capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("checked: 11 renders, 9 MIDI parts, 7 clips", run.stdout)
        (rt / "Kick_B.wav").unlink()  # a missing recording is reported, not ignored
        run = subprocess.run([sys.executable, str(ROOT / "tools" / "content" / "import_ableton.py"), str(mpath), "--check"],
                             capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(run.returncode, 1)
        self.assertIn("Kick_B.wav", run.stdout)


if __name__ == "__main__":
    unittest.main()
