"""Unit tests on short synthetic audio made here (clicks and tones at a known tempo). No recordings, no Demucs.

    /home/joe/.venvs/rw-audio/bin/python -m unittest discover -s tools/audio_import -p 'test_*.py' -v
"""
from __future__ import annotations

import copy
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis import fit_grid, pick_onsets, tempo_candidates  # noqa: E402
from audio_io import PACK_RATE, encode_ogg  # noqa: E402
from chart import Cue, Event, Grid, build_charts, resolve  # noqa: E402
from validate_track import playability_violations, validate  # noqa: E402

RATE = 44100


def click_track(times, rate=RATE, dur=None, hz=2000.0, amp=0.8, noise=0.0, seed=0):
    dur = dur or (max(times) + 1.0)
    x = np.zeros(int(dur * rate), np.float32)
    k = np.arange(int(0.03 * rate)) / rate
    burst = (np.sin(2 * np.pi * hz * k) * np.exp(-k / 0.006)).astype(np.float32)
    for t in times:
        a = int(round(t * rate))
        x[a:a + len(burst)] += amp * burst[: len(x) - a]
    if noise:
        x += noise * np.random.default_rng(seed).standard_normal(len(x)).astype(np.float32)
    return x


class GridTests(unittest.TestCase):
    def test_recovers_tempo_and_offset(self):
        bpm, off = 174.37, 0.4321
        B = 60 / bpm
        rng = np.random.default_rng(1)
        # a two-step-like pattern of 16ths over 60 s, with 2 ms jitter
        pattern = [0, 1.0, 2.5, 3.0]
        times = [off + (bar * 4 + p) * B for bar in range(int(58 / (4 * B))) for p in pattern]
        times = np.array(times) + rng.normal(0, 0.002, len(times))
        x = click_track(times, noise=0.002)
        t, w = pick_onsets(x, RATE)
        tc = tempo_candidates(t, w)
        self.assertAlmostEqual(tc["chosen_bpm"], bpm, delta=0.05)
        g = fit_grid(t, w, tc["chosen_bpm"])
        self.assertAlmostEqual(g["bpm"], bpm, delta=0.01)
        # t0 is a beat line: the offset modulo one beat
        d = (g["t0"] - off) % B
        self.assertLess(min(d, B - d), 0.004)
        self.assertLess(g["drift_ms_max_abs"], 3.0)

    def test_half_time_reading_maps_to_dnb_range(self):
        bpm = 87.0
        B = 60 / bpm
        times = [0.25 + i * B for i in range(60)]
        t, w = pick_onsets(click_track(times), RATE)
        tc = tempo_candidates(t, w)
        self.assertTrue(110 <= tc["chosen_bpm"] <= 200)
        self.assertAlmostEqual(tc["chosen_bpm"], 174.0, delta=0.1)

    def test_drift_is_reported(self):
        # tempo slides from 170 to 178 BPM: a single grid must not look clean
        t, b = 0.5, []
        while t < 60:
            b.append(t)
            t += 60 / (170 + 8 * t / 60)
        tt, w = pick_onsets(click_track(b), RATE)
        g = fit_grid(tt, w, tempo_candidates(tt, w)["chosen_bpm"])
        self.assertGreater(g["drift_ms_max_abs"], 12.0)


class OnsetTests(unittest.TestCase):
    def test_finds_known_events(self):
        rng = np.random.default_rng(3)
        times = np.sort(rng.uniform(0.5, 9.5, 25))
        times = times[np.r_[True, np.diff(times) > 0.12]]
        amps = rng.uniform(0.2, 0.9, len(times))
        x = np.zeros(int(10.5 * RATE), np.float32)
        for t, a in zip(times, amps):
            x += click_track([t], dur=10.5, amp=a)
        found, _ = pick_onsets(x, RATE)
        self.assertEqual(len(found), len(times))
        err = np.abs(found - times)
        self.assertLess(err.max(), 0.004)

    def test_tone_starts_on_bass(self):
        x = np.zeros(int(6 * RATE), np.float32)
        starts = [0.5, 1.7, 3.1, 4.6]
        for s, f in zip(starts, (55, 73.4, 49, 65.4)):
            k = np.arange(int(0.9 * RATE))
            x[int(s * RATE):int(s * RATE) + len(k)] += 0.6 * np.sin(2 * np.pi * f * k / RATE) * np.minimum(1, k / 200)
        found, _ = pick_onsets(x, RATE)
        for s in starts:
            self.assertLess(np.min(np.abs(found - s)), 0.015)


def adversarial_events(rng, dur, kind):
    evs = []
    t = 1.0
    while t < dur:
        t += rng.choice([0.001, 0.02, 0.05, 0.1, 0.17, 0.3])
        evs.append(Event(t=float(t), strength=float(rng.uniform(0, 1.2)), rel_db=float(rng.uniform(-10, 0)),
                         own_db=float(rng.uniform(-10, 0)), length=float(rng.choice([0, 0.1, 0.3, 0.6, 2.0, 9.0])),
                         kind=str(rng.choice(["kick", "snare", "hat", "onset"])), pos=float(t * 174 / 60),
                         dev_ms=0.0, score=float(rng.uniform(0, 1))))
    return evs


class ChartTests(unittest.TestCase):
    def test_never_breaks_playability_on_adversarial_input(self):
        for seed in range(6):
            rng = np.random.default_rng(seed)
            dur = 40.0
            bpm = float(rng.choice([87.0, 140.0, 174.0, 200.0]))
            g = Grid(bpm=bpm, first_downbeat=0.3)
            kinds = {"drums": "drums", "bass": "bass", "other": "melodic", "vocals": "vocal"}
            pads = dict(zip(kinds, rng.permutation([1, 2, 3, 4]).tolist()))
            ve = {k: adversarial_events(rng, dur - 0.2, kinds[k]) for k in kinds}
            for evs in ve.values():
                for e in evs:
                    e.pos = float(g.position(np.array([e.t]))[0])
            secs = [{"id": "intro1", "role": "intro", "start_s": 0, "end_s": 10},
                    {"id": "drop1", "role": "drop", "start_s": 10, "end_s": dur}]
            charts = build_charts(ve, pads, kinds, secs, g, dur, {k: 0.8 for k in kinds})
            prev = None
            for d in ("hard", "normal", "easy"):
                cj = [c.as_json() for c in charts[d]]
                self.assertEqual(playability_violations(cj, bpm), [], f"seed {seed} {d}")
                for c in cj:
                    self.assertGreaterEqual(c["t"], 1.0)
                    self.assertLessEqual(c["t"] + c["dur"], dur - 0.5)
                self.assertEqual(cj, sorted(cj, key=lambda c: c["t"]))
                cur = {(c["t"], c["pad"]) for c in cj}
                if prev is not None:
                    self.assertTrue(cur <= prev, f"{d} is not a thinning of the harder chart")
                prev = cur
            self.assertGreater(len(charts["hard"]), len(charts["easy"]))

    def test_resolve_on_pathological_cues(self):
        rng = random.Random(7)
        B = 60 / 174
        cues = [Cue(t=1 + rng.random() * 20, pad=rng.randint(1, 4), dur=0.0, conf=0.5, score=rng.random(),
                    voice=rng.choice(["a", "b"]), natural=rng.choice([0.0, 0.2, 1.0, 5.0])) for _ in range(800)]
        out = resolve(cues, B, 30.0, {"bass"}, {"a": "bass", "b": "drums"})
        cj = [c.as_json() for c in out]
        self.assertEqual(playability_violations(cj, 174.0), [])
        self.assertTrue(any(c["dur"] > 0 for c in cj))

    def test_rule_checker_catches_each_rule(self):
        B = 60 / 120  # 0.5 s
        ok = [{"t": 1.0, "pad": 1, "dur": 0, "conf": 1}, {"t": 1.25, "pad": 3, "dur": 0, "conf": 1}]
        self.assertEqual(playability_violations(ok, 120), [])
        bad = {
            "same pad": [{"t": 1.0, "pad": 1, "dur": 0}, {"t": 1.2, "pad": 1, "dur": 0}],
            "inside own hold": [{"t": 1.0, "pad": 2, "dur": 1.0}, {"t": 1.6, "pad": 2, "dur": 0}],
            "too soon after hold": [{"t": 1.0, "pad": 2, "dur": 0.5}, {"t": 1.55, "pad": 2, "dur": 0}],
            "same thumb": [{"t": 1.0, "pad": 3, "dur": 0}, {"t": 1.1, "pad": 4, "dur": 0}],
            "same thumb held": [{"t": 1.0, "pad": 3, "dur": 2.0}, {"t": 2.0, "pad": 4, "dur": 0}],
            "short hold": [{"t": 1.0, "pad": 1, "dur": 0.1}],
            "three at once": [{"t": 1.0, "pad": 1, "dur": 2.0}, {"t": 1.0, "pad": 3, "dur": 0},
                              {"t": 1.5, "pad": 2, "dur": 0}],
        }
        for name, cues in bad.items():
            cues = [dict(c, conf=1) for c in cues]
            self.assertTrue(playability_violations(cues, 120), name)


def make_pack(root: Path, dur: float = 6.0) -> tuple[Path, Path]:
    """A valid 4-voice pack from tones and clicks, and the 'recording' they sum to."""
    pid = "synthetic_test"
    pack = root / pid
    n = int(dur * RATE)
    tt = np.arange(n) / RATE
    bpm = 120.0
    beats = np.arange(0.5, dur, 0.5)
    drums = click_track(beats, dur=dur, hz=3000)
    bass = (0.3 * np.sin(2 * np.pi * 55 * tt) * ((tt % 2.0) < 1.5)).astype(np.float32)
    lead = click_track(beats + 0.25, dur=dur, hz=880, amp=0.4)
    pads_ = (0.1 * np.sin(2 * np.pi * 440 * tt) * (tt > 1.0)).astype(np.float32)
    back = (0.02 * np.sin(2 * np.pi * 220 * tt)).astype(np.float32)
    st = {"drums": drums, "bass": bass, "lead": lead, "pads": pads_, "backing": back}
    for k, x in st.items():
        encode_ogg(np.stack([x, x], 1), RATE, pack / "stems" / f"{k}.ogg")
    rec = sum(st.values())
    recp = root / "recording.wav"
    from audio_io import write_wav, decode
    write_wav(np.stack([rec, rec], 1), RATE, recp)
    length = len(decode(pack / "stems" / "drums.ogg", rate=PACK_RATE)[0]) / PACK_RATE
    tj = {"format": "rhythm_warfare.track.v1", "id": pid, "title": "T", "artist": "A", "duration_s": round(length, 4),
          "tempo": {"bpm": bpm, "first_downbeat_s": 0.5, "beats_per_bar": 4, "confidence": 0.9},
          "voices": [{"key": k, "label": k.title(), "pad": i + 1, "stem": f"stems/{k}.ogg", "gain": 1.0}
                     for i, k in enumerate(["drums", "lead", "bass", "pads"])],
          "backing": [{"key": "backing", "stem": "stems/backing.ogg", "gain": 1.0}],
          "sections": [{"id": "a", "role": "intro", "start_s": 0.0, "end_s": 3.0},
                       {"id": "b", "role": "drop", "start_s": 3.0, "end_s": round(length, 4)}],
          "charts": {"normal": [{"t": 1.5, "pad": 1, "dur": 0.0, "conf": 0.9},
                                {"t": 2.0, "pad": 3, "dur": 1.0, "conf": 0.8},
                                {"t": 2.25, "pad": 2, "dur": 0.0, "conf": 0.7},
                                {"t": 2.5, "pad": 1, "dur": 0.0, "conf": 0.9},
                                {"t": 4.0, "pad": 4, "dur": 0.0, "conf": 0.5}]},
          "default_chart": "normal", "rules": {"restore_after_idle_beats": 8},
          "source": {"input_path": str(recp)}}
    (pack / "track.json").write_text(json.dumps(tj))
    return pack, recp


class ValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pack, cls.rec = make_pack(Path(cls.tmp.name))
        cls.good = json.loads((cls.pack / "track.json").read_text())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_with(self, mutate, quick=True):
        tj = copy.deepcopy(self.good)
        mutate(tj)
        (self.pack / "track.json").write_text(json.dumps(tj))
        try:
            r, _ = validate(self.pack, quick=quick)
        finally:
            (self.pack / "track.json").write_text(json.dumps(self.good))
        return r.errors

    def test_good_pack_passes_with_audio(self):
        r, stats = validate(self.pack)
        self.assertEqual(r.errors, [])
        self.assertLess(stats["sum_error_db"], -24)

    def test_rejects_each_kind_of_broken_pack(self):
        cases = {
            "format": lambda j: j.update(format="v0"),
            "id": lambda j: j.update(id="Other"),
            "duration": lambda j: j.update(duration_s=0),
            "three voices": lambda j: j["voices"].pop(),
            "pad twice": lambda j: j["voices"][1].update(pad=1),
            "dup key": lambda j: j["backing"][0].update(key="drums"),
            "bad key": lambda j: j["voices"][0].update(key="Drums!"),
            "abs stem": lambda j: j["voices"][0].update(stem="/etc/passwd"),
            "dotdot stem": lambda j: j["voices"][0].update(stem="../x.ogg"),
            "missing stem": lambda j: j["voices"][0].update(stem="stems/none.ogg"),
            "gain": lambda j: j["voices"][0].update(gain=3),
            "bpm": lambda j: j["tempo"].update(bpm=0),
            "bars": lambda j: j["tempo"].update(beats_per_bar=3),
            "tempo conf": lambda j: j["tempo"].update(confidence=2),
            "section role": lambda j: j["sections"][0].update(role="chorus"),
            "section overlap": lambda j: j["sections"][1].update(start_s=2.0),
            "section outside": lambda j: j["sections"][1].update(end_s=99),
            "default chart": lambda j: j.update(default_chart="hard"),
            "unsorted": lambda j: j["charts"]["normal"].reverse(),
            "first second": lambda j: j["charts"]["normal"][0].update(t=0.5),
            "past end": lambda j: j["charts"]["normal"][-1].update(t=j["duration_s"] - 0.2),
            "pad 5": lambda j: j["charts"]["normal"][0].update(pad=5),
            "conf": lambda j: j["charts"]["normal"][0].update(conf=1.5),
            "same pad": lambda j: j["charts"]["normal"][3].update(t=1.6, pad=1),
            "short hold": lambda j: j["charts"]["normal"][1].update(dur=0.1),
            "idle rule": lambda j: j.update(rules={"restore_after_idle_beats": -1}),
            "other chart broken": lambda j: j["charts"].update(hard=[{"t": 2.0, "pad": 1, "dur": 0, "conf": 1},
                                                                    {"t": 2.1, "pad": 2, "dur": 0, "conf": 1}]),
        }
        for name, m in cases.items():
            self.assertTrue(self.run_with(m), f"validator accepted a pack with a broken {name}")

    def test_rejects_cue_on_silence(self):
        # the pads stem is silent before 1.0 s and the lead clicks only on off-beats: a lead cue on a beat
        # where it is silent must be refused
        def m(j):
            j["charts"]["normal"] = [{"t": 1.5, "pad": 1, "dur": 0.0, "conf": 0.9},
                                     {"t": 3.0, "pad": 2, "dur": 0.0, "conf": 0.9}]
        self.assertTrue(any("silent" in e for e in self.run_with(m, quick=False)))

    def test_rejects_wrong_rate_and_misaligned_stems(self):
        from audio_io import decode
        x, _ = decode(self.pack / "stems" / "pads.ogg", rate=PACK_RATE)
        orig = (self.pack / "stems" / "pads.ogg").read_bytes()
        try:
            encode_ogg(x, PACK_RATE, self.pack / "stems" / "pads.ogg", out_rate=44100)
            r, _ = validate(self.pack)
            self.assertTrue(any("Hz" in e for e in r.errors))
            shifted = np.concatenate([np.zeros((240, 2), np.float32), x])[: len(x)]
            encode_ogg(shifted, PACK_RATE, self.pack / "stems" / "pads.ogg")
            r, _ = validate(self.pack)
            self.assertTrue(any("offset" in e or "sum" in e for e in r.errors), r.errors)
            encode_ogg(x[: len(x) - 4800], PACK_RATE, self.pack / "stems" / "pads.ogg")
            r, _ = validate(self.pack)
            self.assertTrue(any("length" in e or "differ" in e for e in r.errors), r.errors)
        finally:
            (self.pack / "stems" / "pads.ogg").write_bytes(orig)


if __name__ == "__main__":
    unittest.main()
