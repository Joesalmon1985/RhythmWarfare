"""Tests for tools/content/arrange.py with synthetic packs (no real recordings needed): the generator's determinism and variation, the family and identity
rules, section legality, the chart legality checks, the chapter render (frames, crossfades, limiter, cues) and the audition length."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import arrange as ar  # noqa: E402
from chart import load_rules  # noqa: E402
from common import SAMPLE_RATE, TICKS_PER_BAR, bars_to_frames, read_wav, write_wav  # noqa: E402

RULES = load_rules()
RECIPES = ar.load_recipes()
PALETTES = {
    "alpha": {"label": "test", "filters": {"family_glob": ["fam_a", "fam_c"], "profile": ["beat_shaper_174x1"], "min_density": 1.0},
              "recipes": {"intro": "intro", "build": "build", "drop": "drop", "breakdown": "breakdown", "variation": "variation", "ending": "ending"},
              "lead": ["intro", "build"], "tail": ["drop", "ending"], "fills": True, "long_p": 0.5},
    "beta": {"label": "other", "filters": {"family_glob": ["fam_b"], "profile": ["beat_shaper_174x1"]},
             "recipes": {"intro": "fragile", "build": "fragile", "drop": "uplift", "breakdown": "fragile", "variation": "uplift", "ending": "uplift"},
             "lead": ["intro"], "tail": ["ending"], "fills": False, "long_p": 0.0},
}


def cues(kicks=(0, 2, 4, 8, 10, 12), snares=(1, 3, 5, 9, 11, 13)):
    """Drum cues [tick, dur, pad, family] on whole beats, bass [tick, dur, pad, 'bass'] every 4 beats."""
    d = [[int(b * 960), 0, 1, "kick"] for b in kicks] + [[int(b * 960), 0, 4, "snare"] for b in snares]
    return sorted(d), [[b * 960, 0, 2 + (b // 4) % 2, "bass"] for b in range(0, 16, 4)]


def make_pack(root: Path, pid: str, family: str, variant: int, phrase=16, drums=None, bass=None, loop=2000) -> None:
    d, b = cues()
    d = drums if drums is not None else d
    b = bass if bass is not None else b
    tiers = {t: {"drums": d, "bass": b} for t in "1234"}
    folder = root / pid
    (folder / "loops").mkdir(parents=True)
    for v, amp in (("drums", 0.3), ("bass", 0.25), ("other", 0.2)):
        x = np.sin(np.arange(loop) * 0.05 * (1 + variant))[:, None] * amp
        write_wav(folder / "loops" / f"{v}.wav", np.repeat(x, 2, axis=1).astype(np.float32))
    pack = {"schema": 1, "id": pid, "label": pid, "bpm": 174, "phrase_beats": phrase, "loop_frames": loop, "profile": "beat_shaper_174x1",
            "stems": {"drums": "loops/drums.wav", "bass": "loops/bass.wav", "other": "loops/other.wav"}, "tiers": tiers,
            "source": {"project": family, "variant": variant}}
    (folder / "pack.json").write_text(json.dumps(pack), encoding="utf-8")


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        for v in range(3):
            make_pack(root, f"fam_a_v{v}" if v else "fam_a", "fam_a", v)
        for v in range(2):
            make_pack(root, f"fam_b_v{v}" if v else "fam_b", "fam_b", v)
        make_pack(root, "fam_c", "fam_c", 0, phrase=32, drums=cues(range(0, 32, 2), range(1, 32, 2))[0], bass=[[b * 960, 0, 2, "bass"] for b in range(0, 32, 4)])
        # illegal packs: a gap of 8 beats in the drums, two kicks 0.25 beat apart
        make_pack(root, "fam_d", "fam_d", 0, drums=[[0, 0, 1, "kick"], [8 * 960, 0, 4, "snare"]])
        make_pack(root, "fam_e", "fam_e", 0, drums=[[0, 0, 1, "kick"], [240, 0, 1, "kick"], [4 * 960, 0, 4, "snare"], [8 * 960, 0, 1, "kick"], [12 * 960, 0, 4, "snare"]])
        cls.root = root
        cls.packs = ar.load_packs(root, None)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def gen(self, pal="alpha", seed=1, bars=64, packs=None, use="run"):
        return ar.generate(pal, seed, bars, packs or self.packs, RULES, PALETTES, None, use)

    def problems(self, arr, packs=None):
        return ar.validate_arrangement(arr, packs or self.packs, RULES, PALETTES, RECIPES)


class Generator(Base):
    def test_same_seed_same_arrangement(self):
        self.assertEqual(self.gen(seed=7), self.gen(seed=7))
        self.assertEqual(json.dumps(self.gen(seed=7), sort_keys=True), json.dumps(self.gen(seed=7), sort_keys=True))

    def test_seeds_vary_the_result(self):
        seen = {json.dumps(self.gen(seed=s)["sections"]) for s in range(1, 12)}
        self.assertGreater(len(seen), 4, "different seeds give different section plans")

    def test_every_generated_arrangement_is_legal(self):
        for pal in PALETTES:
            for seed in range(1, 25):
                for bars in (16, 32, 64, 80):
                    arr = self.gen(pal, seed, bars)
                    self.assertEqual(self.problems(arr), [], f"{pal} seed {seed} bars {bars}")

    def test_sections_tile_the_length_on_eight_bar_boundaries(self):
        for seed in range(1, 20):
            arr = self.gen("alpha", seed, 64)
            self.assertEqual(sum(s["bars"] for s in arr["sections"]), 64)
            self.assertTrue(all(s["bars"] in (8, 16) for s in arr["sections"]))
            pos = 0
            for s in arr["sections"]:
                self.assertEqual(pos % 8, 0)
                if s["bars"] == 16:
                    self.assertEqual(pos % 16, 0, "a 16-bar section sits on a 16-bar line (one scene's phase)")
                pos += s["bars"]

    def test_long_sections_occur(self):
        self.assertTrue(any(any(s["bars"] == 16 for s in self.gen("alpha", seed)["sections"]) for seed in range(1, 30)))

    def test_run_use_needs_whole_phases(self):
        with self.assertRaises(Exception):
            self.gen(bars=56)
        arr = self.gen(bars=56, use="chapter")
        self.assertEqual(self.problems(arr), [])
        self.assertEqual(arr["bars"], 56)

    def test_one_family_and_one_identity(self):
        for seed in range(1, 20):
            arr = self.gen("alpha", seed)
            fams = {self.packs[s["pack"]]["family"] for s in arr["sections"]}
            self.assertEqual(fams, {arr["family"]})
            self.assertIn(arr["family"], ("fam_a", "fam_c"))
            self.assertEqual({s["mix"] for s in arr["sections"]} - set(PALETTES["alpha"]["recipes"].values()), set())
            self.assertEqual(arr["identity"]["palette"], "alpha")

    def test_illegal_packs_are_never_chosen(self):
        wide = dict(PALETTES, gamma={"label": "x", "filters": {"family_glob": ["fam_d", "fam_e", "fam_a"], "profile": ["beat_shaper_174x1"]},
                                     "recipes": PALETTES["alpha"]["recipes"], "lead": ["intro"], "tail": ["ending"]})
        for seed in range(1, 15):
            arr = ar.generate("gamma", seed, 32, self.packs, RULES, wide)
            self.assertEqual(arr["family"], "fam_a")
        self.assertTrue(ar.pack_problems(self.packs["fam_d"], RULES), "a gap of 8 beats in the drum chart")
        self.assertTrue(ar.pack_problems(self.packs["fam_e"], RULES), "same-pad cues 0.25 beat apart")

    def test_palettes_pick_their_own_families(self):
        for seed in range(1, 10):
            self.assertEqual(self.gen("beta", seed)["family"], "fam_b")

    def test_cross_family_only_when_the_catalogue_says_compatible(self):
        cat = Path(self.tmp.name) / "catalogue.json"
        cat.write_text(json.dumps({"compatible": {"fam_a": ["fam_c"]}}), encoding="utf-8")
        packs = ar.load_packs(self.root, cat)
        self.assertEqual(packs["fam_a"]["compatible"], ["fam_c"])
        crossed = 0
        for seed in range(1, 60):
            arr = self.gen("alpha", seed, 64, packs)
            fams = {packs[s["pack"]]["family"] for s in arr["sections"]}
            self.assertLessEqual(fams, {arr["family"], *arr["compatible"]})
            self.assertEqual(self.problems(arr, packs), [])
            if len(fams) > 1:
                crossed += 1
                self.assertEqual(arr["compatible"], [({"fam_a", "fam_c"} - {arr["family"]}).pop()])
        self.assertGreater(crossed, 0, "compatible families do mix in variations")
        plain = ar.load_packs(self.root, None)
        for seed in range(1, 30):
            arr = self.gen("alpha", seed, 64, plain)
            self.assertEqual({plain[s["pack"]]["family"] for s in arr["sections"]}, {arr["family"]})


class Validation(Base):
    def setUp(self):
        self.arr = self.gen("alpha", 3, 64)

    def test_bars_must_tile(self):
        a = copy.deepcopy(self.arr)
        a["sections"][0]["bars"] = 16
        self.assertTrue(any("add up" in m or "16-bar line" in m for m in self.problems(a)))
        a = copy.deepcopy(self.arr)
        a["sections"][0]["bars"] = 12
        self.assertTrue(any("8 or 16" in m for m in self.problems(a)))

    def test_a_long_section_off_the_phase_line(self):
        a = copy.deepcopy(self.arr)
        a["sections"] = [{"bars": 8, "role": "intro", "pack": "fam_a", "mix": "intro", "fills": []}, {"bars": 16, "role": "drop", "pack": "fam_a", "mix": "drop", "fills": []},
                         {"bars": 8, "role": "ending", "pack": "fam_a", "mix": "ending", "fills": []}]
        a["bars"] = 32
        self.assertTrue(any("16-bar line" in m for m in self.problems(a)))

    def test_missing_pack_and_profile(self):
        a = copy.deepcopy(self.arr)
        a["sections"][1]["pack"] = "nope"
        self.assertTrue(any("does not exist" in m for m in self.problems(a)))
        packs = copy.deepcopy(self.packs)
        packs["fam_a"]["bpm"] = 87
        a2 = {"id": "x", "family": "fam_a", "seed": 1, "bars": 16, "use": "run", "identity": {"palette": "alpha"},
              "sections": [{"bars": 16, "role": "drop", "pack": "fam_a", "mix": "drop", "fills": []}]}
        self.assertTrue(any("87 BPM" in m for m in self.problems(a2, packs)))

    def test_family_and_identity_rules(self):
        a = copy.deepcopy(self.arr)
        a["sections"][1]["pack"] = "fam_b"
        self.assertTrue(any("family" in m for m in self.problems(a)))
        a = copy.deepcopy(self.arr)
        a["sections"][1]["mix"] = "fragile"
        self.assertTrue(any("one identity" in m for m in self.problems(a)))
        a = copy.deepcopy(self.arr)
        a["identity"]["palette"] = "beta"
        self.assertTrue(any("family filter" in m for m in self.problems(a)))

    def test_mix_gains(self):
        a = copy.deepcopy(self.arr)
        a["sections"][1]["mix"] = {"drums": 1.0, "bass": 0.2, "other": 1.0}
        self.assertTrue(any("under 0.5" in m for m in self.problems(a)))
        a["sections"][1]["mix"] = {"drums": 1.5}
        self.assertTrue(any("0..1" in m for m in self.problems(a)))

    def test_a_pack_with_an_illegal_chart_fails_the_arrangement(self):
        a = copy.deepcopy(self.arr)
        a["family"] = "fam_e"
        a["compatible"] = []
        a["sections"] = [{"bars": 16, "role": "drop", "pack": "fam_e", "mix": "drop", "fills": []}]
        a["bars"] = 16
        pal = dict(PALETTES, alpha=dict(PALETTES["alpha"], filters={"family_glob": ["*"]}))
        msgs = ar.validate_arrangement(a, self.packs, RULES, pal, RECIPES)
        self.assertTrue(any("apart" in m for m in msgs), msgs)

    def test_gap_over_six_beats(self):
        a = {"id": "x", "family": "fam_d", "seed": 1, "bars": 16, "use": "run", "identity": {"palette": "alpha"},
             "sections": [{"bars": 16, "role": "drop", "pack": "fam_d", "mix": "drop", "fills": []}]}
        pal = dict(PALETTES, alpha=dict(PALETTES["alpha"], filters={"family_glob": ["*"]}))
        msgs = ar.validate_arrangement(a, self.packs, RULES, pal, RECIPES)
        self.assertTrue(any("gap of" in m for m in msgs), msgs)

    def test_stems_sections_are_validated_structurally(self):
        a = copy.deepcopy(self.arr)
        a["sections"][1] = {"bars": 8, "role": "drop", "stems": {"drums": "groove_a", "bass": "bass_b", "synth": "pad_c"}, "mix": "drop", "fills": []}
        self.assertEqual(self.problems(a), [])
        a["sections"][1]["stems"] = {"drums": ""}
        self.assertTrue(any("stems must" in m for m in self.problems(a)))

    def test_the_seam_between_two_packs_is_checked(self):
        # each pack alone passes; a drum chart whose first cue is late would leave a long gap at the seam
        late = copy.deepcopy(self.packs["fam_a"])
        late["id"] = "fam_a_late"
        late["tiers"] = {t: {"drums": [[4 * 960, 0, 1, "kick"], [9 * 960, 0, 4, "snare"], [14 * 960, 0, 1, "kick"]], "bass": self.packs["fam_a"]["tiers"][t]["bass"]} for t in "1234"}
        self.assertEqual(ar.pack_problems(late, RULES), [], "inside its own phrase the biggest gap is 6 beats (cyclic)")
        packs = dict(self.packs, fam_a_late=late)
        a = {"id": "x", "family": "fam_a", "seed": 1, "bars": 16, "use": "run", "identity": {"palette": "alpha"},
             "sections": [{"bars": 8, "role": "intro", "pack": "fam_a", "mix": "intro", "fills": []}, {"bars": 8, "role": "drop", "pack": "fam_a_late", "mix": "drop", "fills": []}]}
        self.assertTrue(any("gap of 7.0 beats" in m for m in self.problems(a, packs)), "fam_a's last cue (beat 13) to the late pack's first (beat 36)")


class Charts(Base):
    def test_the_chart_follows_the_section_playing(self):
        a = {"sections": [{"bars": 8, "pack": "fam_a"}, {"bars": 8, "pack": "fam_c"}]}
        ch = ar.arrangement_chart(a, self.packs, "4", guard=False)
        first = [c for c in ch["drums"] if c[0] < 32 * 960]
        second = [c for c in ch["drums"] if c[0] >= 32 * 960]
        self.assertEqual(len(first), 2 * 12)
        self.assertEqual(len(second), 32)
        self.assertEqual(second[0][0], 32 * 960)

    def test_the_guard_drops_cues_in_the_last_four_beats_of_a_block(self):
        pack = self.packs["fam_a"]
        guarded = ar.section_chart(pack, "4", 0, 32, "drums", True)
        self.assertTrue(all((c[0] % (16 * 960)) / 960 <= 12 for c in guarded))
        self.assertLess(len(guarded), len(ar.section_chart(pack, "4", 0, 32, "drums", False)) + 1)

    def test_chapter_cues_cover_every_sequence(self):
        arr = self.gen("alpha", 2, 32)
        phases = [{"start_tick": 0, "end_tick": 8 * TICKS_PER_BAR, "mode": "drums"}, {"start_tick": 8 * TICKS_PER_BAR, "end_tick": 16 * TICKS_PER_BAR, "mode": "bass"},
                  {"start_tick": 16 * TICKS_PER_BAR, "end_tick": 24 * TICKS_PER_BAR, "mode": "drums"}, {"start_tick": 24 * TICKS_PER_BAR, "end_tick": 32 * TICKS_PER_BAR, "mode": "bass"}]
        chart, notes = ar.chapter_cues(arr, self.packs, "2", 32, phases)
        self.assertFalse([n for n in notes if n.startswith("ERROR")])
        for ph in phases:
            fams = ["kick", "snare"] if ph["mode"] == "drums" else ["bass"]
            for w in range(ph["start_tick"], ph["end_tick"], 2 * TICKS_PER_BAR):
                got = [c for f in fams for c in chart[f] if w <= c[0] < w + 2 * TICKS_PER_BAR]
                self.assertTrue(got, f"a cue in the sequence at {w}")


class Render(Base):
    def test_stems_have_the_exact_length_and_no_clipping(self):
        arr = self.gen("alpha", 2, 16)
        stems = ar.render_stems(arr, self.packs, RECIPES)
        for v in ar.VOICES:
            self.assertEqual(stems[v].shape, (bars_to_frames(16), 2))
        self.assertLessEqual(float(np.abs(sum(stems.values())).max()), 0.9701)

    def test_a_section_switch_is_a_short_crossfade_not_a_gap(self):
        arr = {"id": "t", "seed": 1, "bars": 16, "identity": {"palette": "alpha"}, "family": "fam_a",
               "sections": [{"bars": 8, "role": "drop", "pack": "fam_a", "mix": "full", "fills": []}, {"bars": 8, "role": "drop", "pack": "fam_a_v1", "mix": "full", "fills": []}]}
        stems = ar.render_stems(arr, self.packs, RECIPES)
        b = bars_to_frames(8)
        d = stems["drums"][:, 0]
        a = ar.pack_loops(self.packs["fam_a"])["drums"][:, 0]
        c = ar.pack_loops(self.packs["fam_a_v1"])["drums"][:, 0]
        h = 240
        self.assertTrue(np.allclose(d[1000:b - 3 * h], a[np.mod(np.arange(1000, b - 3 * h), len(a))], atol=1e-5), "before the seam: the first pack alone")
        self.assertTrue(np.allclose(d[b + 3 * h:b + 5000], c[np.mod(np.arange(3 * h, 5000 + 0 - 0), len(c))][:len(d[b + 3 * h:b + 5000])], atol=1e-5), "after it: the second from its own start")
        self.assertLess(float(np.abs(d[b - 2 * h:b + 2 * h]).max()), 0.51)

    def test_recipes_scale_the_voices(self):
        arr = {"id": "t", "seed": 1, "bars": 8, "identity": {"palette": "alpha"}, "family": "fam_a",
               "sections": [{"bars": 8, "role": "breakdown", "pack": "fam_a", "mix": "breakdown", "fills": []}]}
        s = ar.render_stems(arr, self.packs, RECIPES)
        loops = ar.pack_loops(self.packs["fam_a"])
        self.assertAlmostEqual(float(np.abs(s["drums"][:2000]).max()), float(np.abs(loops["drums"]).max()) * 0.55, places=3)
        self.assertAlmostEqual(float(np.abs(s["bass"][:2000]).max()), float(np.abs(loops["bass"]).max()), places=3)

    def test_fills_gate_the_last_beat_of_the_bar(self):
        arr = {"id": "t", "seed": 1, "bars": 8, "identity": {"palette": "alpha"}, "family": "fam_a",
               "sections": [{"bars": 8, "role": "build", "pack": "fam_a", "mix": "full", "fills": [4]}]}
        s = ar.render_stems(arr, self.packs, RECIPES)
        end = bars_to_frames(4)
        beat = int(round(SAMPLE_RATE * 60.0 / 174.0))
        self.assertLess(float(np.abs(s["bass"][end - beat + 400:end - 400]).max()), 1e-6)
        self.assertGreater(float(np.abs(s["drums"][end - beat + 400:end - 400]).max()), 0.1, "the drums keep playing through the fill")
        self.assertGreater(float(np.abs(s["bass"][end + 1000:end + 3000]).max()), 0.1)

    def test_limiter_keeps_the_balance_and_the_ceiling(self):
        n = 20000
        stems = {"drums": np.ones((n, 2)) * 0.8, "bass": np.ones((n, 2)) * 0.8, "other": np.zeros((n, 2))}
        out = ar.limit(stems)
        self.assertLessEqual(float(np.abs(sum(out.values())).max()), 0.9701)
        self.assertTrue(np.allclose(out["drums"], out["bass"]))

    def test_render_a_chapter_pack(self):
        arr = self.gen("alpha", 4, 16, use="chapter")
        base = {"schema_version": 4, "title": "Base", "duration_ticks": 16 * TICKS_PER_BAR,
                "phases": [{"id": "p01", "start_tick": 0, "end_tick": 8 * TICKS_PER_BAR, "mode": "drums"}, {"id": "p02", "start_tick": 8 * TICKS_PER_BAR, "end_tick": 16 * TICKS_PER_BAR, "mode": "bass"}]}
        with tempfile.TemporaryDirectory() as tmp:
            bl = Path(tmp) / "base" / "level.json"
            bl.parent.mkdir()
            bl.write_text(json.dumps(base), encoding="utf-8")
            out = Path(tmp) / "out"
            info = ar.render_chapter(arr, self.packs, RECIPES, "test", out, 16, bl, "2")
            level = json.loads((out / "level.json").read_text())
            rec = level["recorded_music"]
            self.assertEqual(rec["loop_bars"], 16)
            self.assertEqual(sorted(rec["stems"]), ["bass", "drums", "other"])
            for v in rec["stems"].values():
                frames, fmt = read_wav(out / v["file"])
                self.assertEqual((len(frames), fmt["sample_rate"], fmt["sample_width"]), (bars_to_frames(16), 48000, 2))
            self.assertTrue(rec["cues"]["kick"] and rec["cues"]["snare"] and rec["cues"]["bass"])
            self.assertEqual(level["phases"], base["phases"])
            with self.assertRaises(Exception):
                ar.render_chapter(arr, self.packs, RECIPES, "test", out, 8, bl, "2")  # the base chapter has 16 bars


class Audition(Base):
    def test_between_thirty_and_sixty_seconds(self):
        for seed in range(1, 15):
            arr = self.gen("alpha", seed, 64)
            secs = ar.audition_bars(arr) * 4 * 60.0 / 174.0
            self.assertGreaterEqual(secs, 30.0)
            self.assertLessEqual(secs, 60.0)

    def test_the_wav_is_16_bit_48k(self):
        arr = self.gen("alpha", 1, 32)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "a.wav"
            secs = ar.audition(arr, self.packs, RECIPES, p)
            frames, fmt = read_wav(p)
            self.assertEqual((fmt["sample_rate"], fmt["sample_width"]), (48000, 2))
            self.assertAlmostEqual(len(frames) / 48000.0, secs, places=3)


class Catalogue(unittest.TestCase):
    def test_tolerant_reading(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "c.json"
            self.assertEqual(ar.load_catalogue(p), {})
            p.write_text(json.dumps({"packs": [{"id": "x", "family": "fx"}], "compatible": [["fx", "fy"]]}), encoding="utf-8")
            c = ar.load_catalogue(p)
            self.assertEqual(c["pack_family"], {"x": "fx"})
            self.assertEqual(c["compatible"]["fy"], {"fx"})
            p.write_text("not json", encoding="utf-8")
            self.assertEqual(ar.load_catalogue(p), {})


class RealPacks(unittest.TestCase):
    def test_committed_arrangements_validate(self):
        packs = ar.load_packs()
        for f in sorted(ar.ARR_DIR.glob("*.json")):
            arr = json.loads(f.read_text())
            self.assertEqual(arr["id"], f.stem)
            self.assertEqual(ar.validate_arrangement(arr, packs, RULES), [], f.name)

    def test_the_five_palettes_each_generate_from_the_packs(self):
        packs = ar.load_packs()
        for pal in ar.load_palettes():
            arr = ar.generate(pal, 1, 64, packs, RULES)
            self.assertEqual(ar.validate_arrangement(arr, packs, RULES), [], pal)


if __name__ == "__main__":
    unittest.main()
