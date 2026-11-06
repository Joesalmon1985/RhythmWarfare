#!/usr/bin/env python3
"""Tests of tools/music/transition_sidecars.py on synthetic packs (no recordings, no real packs needed), plus the committed sidecars.

    <the audio venv python> -m unittest discover -s tools/music -p "test_*.py"
"""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import transition_sidecars as T  # noqa: E402

BPM = 174.0
FD = 0.3
BAR = 240.0 / BPM


def section(sid, role, start_s, end_s):
    return {"id": sid, "role": role, "start_s": start_s, "end_s": end_s}


def make_world(root: Path, tracks: dict) -> tuple[Path, Path, Path]:
    """tracks: id -> dict(bpm, fd, duration, sections, drift, constant). Writes packs and committed metadata; returns (packs, tracks_dir, sidecar_dir)."""
    packs, tdir, sdir = root / "packs", root / "tracks", root / "transitions"
    tdir.mkdir()
    for tid, t in tracks.items():
        (packs / tid).mkdir(parents=True, exist_ok=True)
        body = {"id": tid, "title": "T " + tid, "artist": "A", "duration_s": t["duration"], "tempo": {"bpm": t["bpm"], "first_downbeat_s": t["fd"], "beats_per_bar": 4},
                "voices": [{"key": "drums"}, {"key": "bass"}, {"key": "other"}, {"key": "vocals"}], "sections": t["sections"]}
        (packs / tid / "track.json").write_text(json.dumps(body), encoding="utf-8")
        committed = dict(body)
        committed["tempo"] = {"bpm": t["bpm"], "first_downbeat_s": t["fd"], "constant": t.get("constant", True), "drift_ms_max": t.get("drift", 1.0)}
        (tdir / (tid + ".json")).write_text(json.dumps(committed), encoding="utf-8")
    return packs, tdir, sdir


def good_track(drop_bar=32, **kw):
    drop_s = FD + drop_bar * BAR
    secs = [section("intro1", "intro", 0.0, drop_s), section("drop1", "drop", drop_s, drop_s + 40 * BAR), section("drop2", "drop", drop_s + 60 * BAR, drop_s + 90 * BAR),
            section("outro1", "outro", drop_s + 90 * BAR, drop_s + 110 * BAR)]
    d = {"bpm": BPM, "fd": FD, "duration": drop_s + 110 * BAR + 5, "sections": secs}
    d.update(kw)
    return d


class SnapTests(unittest.TestCase):
    def test_exact_bar_agrees(self):
        s = T.snap(FD + 31 * BAR, FD, BPM)
        self.assertEqual(s["bar"], 31)
        self.assertAlmostEqual(s["err_s"], 0.0, places=9)
        self.assertEqual(s["verdict"], "agrees")

    def test_spec_example_stimpy(self):
        s = T.snap(43.80, 0.5787, 172.0)  # section 3.3: bar 31, e = -34.5 ms, -0.10 beat
        self.assertEqual(s["bar"], 31)
        self.assertAlmostEqual(s["err_s"] * 1000.0, -34.5, delta=0.6)
        self.assertAlmostEqual(s["err_beats"], -0.10, delta=0.01)
        self.assertEqual(s["verdict"], "agrees")

    def test_one_beat_late_is_phase_suspect(self):
        s = T.snap(44.18, 0.5787, 172.0)
        self.assertEqual(s["verdict"], "phase_suspect")
        self.assertEqual(s["offset"], 1)
        self.assertAlmostEqual(s["err_beats"], 0.99, delta=0.02)

    def test_half_beat_is_grid_suspect(self):
        s = T.snap(FD + 20 * BAR + 0.5 * 60.0 / BPM, FD, BPM)
        self.assertEqual(s["verdict"], "grid_suspect")

    def test_boundaries_of_agrees(self):
        beat = 60.0 / BPM
        self.assertEqual(T.snap(FD + 5 * BAR + 0.249 * beat, FD, BPM)["verdict"], "agrees")
        self.assertEqual(T.snap(FD + 5 * BAR + 0.251 * beat, FD, BPM)["verdict"], "grid_suspect")
        self.assertEqual(T.snap(FD + 5 * BAR + 0.76 * beat, FD, BPM)["verdict"], "phase_suspect")  # within 0.25 of one beat

    def test_offset_moves_the_grid(self):
        beat = 60.0 / BPM
        t = FD + 10 * BAR + beat  # one beat after a bar line of the pack's grid
        self.assertEqual(T.snap(t, FD, BPM)["verdict"], "phase_suspect")
        s = T.snap(t, FD, BPM, offset_beats=1)
        self.assertEqual(s["verdict"], "agrees")
        self.assertEqual(s["bar"], 10)

    def test_before_first_downbeat_is_bar_zero(self):
        s = T.snap(0.0, 1.1, BPM)
        self.assertEqual(s["bar"], 0)
        self.assertTrue(s["before_grid"])

    def test_lead_in(self):
        self.assertEqual(T.lead_in_bars(47), 16)
        self.assertEqual(T.lead_in_bars(15), 15)
        self.assertEqual(T.lead_in_bars(0), 0)
        self.assertEqual(T.lead_in_bars(47, mix_in_bar=40), 7)
        self.assertIsNone(T.lead_in_bars(None))


class OwnerDropParsing(unittest.TestCase):
    def test_forms(self):
        p = lambda s, cur=40.0: T.parse_owner_drop(s, cur, FD, BPM)  # noqa: E731
        self.assertAlmostEqual(p("43.80"), 43.80)
        self.assertAlmostEqual(p("0:43.8"), 43.8)
        self.assertAlmostEqual(p("1:02"), 62.0)
        self.assertAlmostEqual(p("bar 31"), FD + 31 * BAR)
        self.assertAlmostEqual(p("+1 beat"), 40.0 + 60.0 / BPM)
        self.assertAlmostEqual(p("-2 beats"), 40.0 - 2 * 60.0 / BPM)
        self.assertIsNone(p(""))
        self.assertIsNone(p("OK"))
        with self.assertRaises(ValueError):
            p("sometime")


class GenerateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.tracks = {"good": good_track(32), "short": good_track(3), "wobbly": good_track(32, drift=90.0, constant=False),
                       "nodrop": {"bpm": BPM, "fd": FD, "duration": 200.0, "sections": [section("a", "intro", 0.0, 100.0), section("b", "breakdown", 100.0, 200.0)]}}
        self.packs, self.tdir, self.sdir = make_world(self.root, self.tracks)
        self.csv, self.md = self.root / "sheet.csv", self.root / "sheet.md"
        self.log: list[str] = []

    def tearDown(self):
        self.tmp.cleanup()

    def gen(self):
        return T.generate(self.packs, self.tdir, self.sdir, self.csv, self.md, log=self.log.append)

    def sidecar(self, tid):
        return json.loads((self.sdir / (tid + ".json")).read_text(encoding="utf-8"))

    def test_sidecar_content_and_validity(self):
        r = self.gen()
        self.assertEqual(r["tracks"], 4)
        self.assertEqual([m for m in self.log if m.startswith("ERROR")], [])
        d = self.sidecar("good")
        self.assertEqual(list(d.keys()), T.KEYS)
        self.assertEqual(d["first_drop_bar"], 32)
        self.assertAlmostEqual(d["first_drop_s"], FD + 32 * BAR, places=3)
        self.assertEqual(d["origin"]["first_drop_s"], "detected")
        self.assertIsNone(d["checked"])
        self.assertFalse(d["no_blend"])
        self.assertAlmostEqual(d["second_drop_s"], FD + 92 * BAR, places=3)
        self.assertIsNone(self.sidecar("nodrop")["first_drop_s"])
        self.assertEqual(T.check(self.packs, self.tdir, self.sdir, log=self.log.append), 0)

    def test_rerun_changes_nothing(self):
        self.gen()
        before = {p.name: p.read_bytes() for p in list(self.sdir.glob("*.json")) + [self.csv, self.md]}
        r = self.gen()
        self.assertEqual(r["sidecars_changed"], 0)
        self.assertFalse(r["csv_changed"] or r["md_changed"])
        after = {p.name: p.read_bytes() for p in list(self.sdir.glob("*.json")) + [self.csv, self.md]}
        self.assertEqual(before, after)

    def test_flags(self):
        r = self.gen()
        by = {x["track"]: x["flags"] for x in r["rows"]}
        self.assertEqual(by["good"], "")
        self.assertIn("lead-in 3 bars: entered with cut", by["short"])
        self.assertIn("tempo not constant", by["wobbly"])
        self.assertIn("drift 90 ms", by["wobbly"])
        self.assertIn("no drop found", by["nodrop"])
        self.assertEqual(r["rows"][-1]["track"], "good")  # the flagged ones come first
        self.assertEqual(len(list(T.read_csv(self.csv))), 4)

    def test_snap_flag_for_a_grid_that_is_off(self):
        t = good_track(32)
        t["sections"][1]["start_s"] += 0.5 * 60.0 / BPM  # a drop half a beat off the grid
        t["sections"][0]["end_s"] = t["sections"][1]["start_s"]
        (self.root / "w2").mkdir()
        packs, tdir, sdir = make_world(self.root / "w2", {"off": t})
        r = T.generate(packs, tdir, sdir, self.root / "o.csv", self.root / "o.md", log=self.log.append)
        self.assertIn("grid suspect", r["rows"][0]["flags"])

    def test_owner_values_survive_a_rerun(self):
        self.gen()
        # the owner types a drop, confirms another track, marks one no_blend
        rows = list(T.read_csv(self.csv))
        for row in rows:
            if row["track"] == "good":
                row["owner_drop"] = "bar 33"
                row["owner_note"] = "listened"
            if row["track"] == "short":
                row["owner_drop"] = "ok"
                row["owner_no_blend"] = "yes"
        with open(self.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=T.CSV_COLUMNS, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        r = T.apply(self.csv, self.packs, self.tdir, self.sdir, today="2026-11-12", log=self.log.append)
        self.assertEqual(r["errors"], 0)
        g = self.sidecar("good")
        self.assertEqual(g["first_drop_bar"], 33)
        self.assertEqual(g["origin"]["first_drop_s"], "owner")
        self.assertEqual(g["checked"], "2026-11-12")
        self.assertEqual(g["note"], "listened")
        s = self.sidecar("short")
        self.assertEqual(s["origin"]["first_drop_s"], "owner")
        self.assertEqual(s["first_drop_bar"], 3)
        self.assertTrue(s["no_blend"])
        # the packs change (a re-import moves the detected drop): the owner's values stay, detected ones follow
        w = json.loads((self.packs / "good" / "track.json").read_text(encoding="utf-8"))
        w["sections"][2]["start_s"] += BAR
        w["sections"][1]["start_s"] += 2 * BAR
        (self.packs / "good" / "track.json").write_text(json.dumps(w), encoding="utf-8")
        self.gen()
        g2 = self.sidecar("good")
        self.assertEqual(g2["first_drop_bar"], 33)
        self.assertEqual(g2["checked"], "2026-11-12")
        self.assertAlmostEqual(g2["second_drop_s"], FD + 93 * BAR, places=3)
        # the sheet shows the owner column cell again (an unapplied edit would not be lost)
        rows2 = {x["track"]: x for x in T.read_csv(self.csv)}
        self.assertEqual(rows2["good"]["owner_drop"], "bar 33")
        self.assertEqual(rows2["good"]["origin"], "owner")

    def test_apply_is_idempotent_and_blank_cells_change_nothing(self):
        self.gen()
        before = {p.name: p.read_bytes() for p in self.sdir.glob("*.json")}
        r = T.apply(self.csv, self.packs, self.tdir, self.sdir, today="2026-11-12", log=self.log.append)  # nothing typed
        self.assertEqual(r["changed"], 0)
        rows = list(T.read_csv(self.csv))
        for row in rows:
            if row["track"] == "good":
                row["owner_drop"] = "0:43.8"
        with open(self.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=T.CSV_COLUMNS, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
        T.apply(self.csv, self.packs, self.tdir, self.sdir, today="2026-11-12", log=self.log.append)
        once = {p.name: p.read_bytes() for p in self.sdir.glob("*.json")}
        r2 = T.apply(self.csv, self.packs, self.tdir, self.sdir, today="2026-11-20", log=self.log.append)  # a later date, same sheet
        self.assertEqual(r2["changed"], 0)
        self.assertEqual(once, {p.name: p.read_bytes() for p in self.sdir.glob("*.json")})
        self.assertNotEqual(before["good.json"], once["good.json"])

    def test_owner_offset_resnaps_the_drop(self):
        self.gen()
        row = {"track": "good", "owner_offset_beats": "1"}
        f = T.track_facts("good", self.packs, self.tdir)
        d = T.apply_row(f, self.sidecar("good"), row, "2026-11-12", log=self.log.append)
        self.assertEqual(d["downbeat_offset_beats"], 1)
        # the drop was on a bar line of the old grid; on the shifted grid it is 1 beat off: phase suspect, snapped to the nearest bar line
        self.assertEqual(d["first_drop_bar"], 32)
        self.assertAlmostEqual(abs(d["first_drop_snap_ms"]), 60000.0 / BPM, delta=1.0)

    def test_bad_cells_are_errors(self):
        self.gen()
        f = T.track_facts("good", self.packs, self.tdir)
        with self.assertRaises(ValueError):
            T.apply_row(f, self.sidecar("good"), {"owner_drop": "soon"}, "2026-11-12")
        with self.assertRaises(ValueError):
            T.apply_row(f, self.sidecar("good"), {"owner_offset_beats": "7"}, "2026-11-12")
        with self.assertRaises(ValueError):
            T.apply_row(f, self.sidecar("good"), {"owner_no_blend": "maybe"}, "2026-11-12")


class ValidateTests(unittest.TestCase):
    def good(self):
        d = T.blank_sidecar("x")
        d["first_drop_s"] = 40.0
        d["first_drop_bar"] = 30
        d["first_drop_snap_ms"] = 0.0
        d["origin"] = {"first_drop_s": "detected"}
        return d

    def test_valid(self):
        self.assertEqual(T.validate_sidecar(self.good(), "x"), [])

    def test_sentences(self):
        for mutate, needle in [
            (lambda d: d.update(format="v0"), "format"),
            (lambda d: d.update(track="y"), "track must be 'x'"),
            (lambda d: d.update(bogus=1), "unknown key 'bogus'"),
            (lambda d: d.update(first_drop_s="soon"), "first_drop_s must be a number"),
            (lambda d: d.update(first_drop_s=-1.0), "first_drop_s must be at least"),
            (lambda d: d.update(downbeat_offset_beats=4), "downbeat_offset_beats"),
            (lambda d: d.update(no_blend="yes"), "no_blend"),
            (lambda d: d.update(checked="yesterday"), "checked"),
            (lambda d: d.update(mix_in_bar=2), "mix_in_bar must lie between"),
            (lambda d: d.update(intro_start_s=50.0), "intro_start_s must be before"),
            (lambda d: d.update(origin={"first_drop_s": "guess"}), "origin.first_drop_s"),
            (lambda d: d.update(linger=[1]), "linger"),
        ]:
            d = self.good()
            mutate(d)
            errs = T.validate_sidecar(d, "x")
            self.assertTrue(any(needle in e for e in errs), (needle, errs))
            self.assertTrue(all(e.startswith("x.json: ") for e in errs))

    def test_needs_facts_for_pack_checks(self):
        facts = {"bpm": BPM, "duration_s": 100.0, "voices": ["drums", "other"]}
        d = self.good()
        d["first_drop_s"] = 95.0
        self.assertTrue(any("last 16 bars" in e for e in T.validate_sidecar(d, "x", facts)))
        d = self.good()
        d["linger"] = ["other", "ghost"]
        self.assertTrue(any("'ghost'" in e for e in T.validate_sidecar(d, "x", facts)))
        d = self.good()
        d["second_drop_s"] = 41.0
        self.assertTrue(any("16 bars after" in e for e in T.validate_sidecar(d, "x", facts)))


class CommittedSidecars(unittest.TestCase):
    def test_every_catalogue_track_has_a_valid_sidecar(self):
        ids = T.track_ids()
        self.assertGreaterEqual(len(ids), 61)
        for tid in ids:
            sc = T.read_sidecar(tid)
            self.assertIsNotNone(sc, tid)
            self.assertEqual(T.validate_sidecar(sc, tid, T.track_facts(tid, None)), [], tid)


if __name__ == "__main__":
    unittest.main()
