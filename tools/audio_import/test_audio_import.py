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
from focus import decide, make_units, perceived_bar_power, stretches, unit_table  # noqa: E402
from layout import layout_stretch  # noqa: E402
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
            ve = {k: adversarial_events(rng, dur - 0.2, kinds[k]) for k in kinds}
            for evs in ve.values():
                for e in evs:
                    e.pos = float(g.position(np.array([e.t]))[0])
                    e.height = float(rng.uniform(30, 80))
                    e.feat = [float(rng.uniform(-30, 10)), float(rng.uniform(-30, 10))]
            secs = [{"id": "intro1", "role": "intro", "start_s": 0, "end_s": 10},
                    {"id": "drop1", "role": "drop", "start_s": 10, "end_s": dur}]
            bar = 4 * 60 / bpm
            cuts = [0.0, 3 * bar, 7 * bar, 9 * bar, 14 * bar, min(dur, 20 * bar)]
            order = list(rng.permutation(list(kinds)))
            focus = [{"start_s": a, "end_s": b, "voice": order[i % 4]} for i, (a, b) in enumerate(zip(cuts, cuts[1:])) if i != 2]
            charts, layouts = build_charts(ve, focus, kinds, secs, g, dur, {k: 0.8 for k in kinds})
            prev = None
            for d in ("hard", "normal", "easy"):
                cj = [c.as_json() for c in charts[d]]
                self.assertEqual(playability_violations(cj, bpm), [], f"seed {seed} {d}")
                for c in cj:
                    self.assertGreaterEqual(c["t"], 1.0)
                    self.assertLessEqual(c["t"] + c["dur"], dur - 0.5)
                    st = [f for f in focus if f["start_s"] <= c["t"] < f["end_s"]]
                    self.assertEqual(len(st), 1, f"cue at {c['t']} outside the focus")
                    self.assertEqual(st[0]["voice"], c["voice"])
                    self.assertLessEqual(c["t"] + c["dur"], st[0]["end_s"] + 1e-6)
                self.assertEqual(cj, sorted(cj, key=lambda c: c["t"]))
                cur = {(c["t"], c["pad"]) for c in cj}
                if prev is not None:
                    self.assertTrue(cur <= prev, f"{d} is not a thinning of the harder chart")
                prev = cur
            self.assertGreater(len(charts["hard"]), len(charts["easy"]))
            self.assertEqual(len(layouts), len(focus))

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


BPM_T = 174.0
B_T = 60 / BPM_T
BAR_T = 4 * B_T


def tone_hits(times, hz, amp, dur, decay=0.08, rate=RATE):
    """Short pitched hits (a sine with a fast attack) at the given times."""
    x = np.zeros(int(dur * rate), np.float32)
    k = np.arange(int(0.25 * rate)) / rate
    h = (np.sin(2 * np.pi * hz * k) * np.exp(-k / decay) * np.minimum(1, k / 0.002)).astype(np.float32)
    for t in times:
        a = int(round(t * rate))
        x[a:a + len(h)] += amp * h[: len(x) - a]
    return x


def synth_events(times, heights, strength=1.0, t0=0.0):
    """Events at the given times; t0 is the first downbeat (pos counts beats from it)."""
    return [Event(t=float(t), strength=strength, rel_db=-3.0, own_db=-3.0, kind="onset", pos=float((t - t0) / B_T),
                  height=float(h), feat=[float(h)]) for t, h in zip(times, heights)]


def focus_of(voices: dict, events: dict, n_bars: int, sections=None, **kw):
    """Run the focus logic of import_track.st_focus on synthetic audio: returns the stretches."""
    edges = np.arange(n_bars + 1) * BAR_T
    sections = sections or [{"id": "s1", "role": "drop", "start_s": 0.0, "end_s": float(edges[-1])}]
    units = make_units(sections, edges)
    power = {k: perceived_bar_power(x, RATE, edges) for k, x in voices.items()}
    rows = unit_table(power, events, units, edges, B_T)
    choice = decide(rows, list(voices), kw.get("min_bars", 8), kw.get("fixed"), kw.get("overrides"))
    return stretches(rows, choice, kw.get("fixed"), kw.get("overrides"), sections)[0], rows


class FocusTests(unittest.TestCase):
    N = 32  # bars: four 8-bar phrases

    def eighths(self, a_bar, b_bar):
        return [t for t in np.arange(a_bar * BAR_T, b_bar * BAR_T - 1e-9, B_T / 2)]

    def test_voice_that_gets_louder_takes_the_focus(self):
        dur = self.N * BAR_T + 0.5
        ts = self.eighths(0, self.N)
        amp_a = np.where(np.array(ts) < 16 * BAR_T, 0.5, 0.05)
        amp_b = np.where(np.array(ts) < 16 * BAR_T, 0.05, 0.5)
        a = sum(tone_hits([t], 880, float(m), dur) for t, m in zip(ts, amp_a))
        b = sum(tone_hits([t], 660, float(m), dur) for t, m in zip(ts, amp_b))
        ev = {"a": synth_events(ts, [69, 71] * (len(ts) // 2)), "b": synth_events(ts, [64, 66] * (len(ts) // 2))}
        st, _ = focus_of({"a": a, "b": b}, ev, self.N)
        self.assertEqual([(f["voice"], f["bar_range"]) for f in st], [("a", [0, 16]), ("b", [16, 32])])

    def test_sub_heavy_bass_does_not_win_by_power_alone(self):
        dur = self.N * BAR_T + 0.5
        n = int(dur * RATE)
        t = np.arange(n) / RATE
        ts = self.eighths(0, self.N)
        drums = tone_hits(ts, 2500, 0.5, dur, decay=0.02)
        raw_d = float((drums ** 2).mean())
        # a held 45 Hz sub with 9 dB more raw power than the drums (as in a drum and bass drop)
        bass = (np.sqrt(2 * raw_d * 10 ** 0.9) * np.sin(2 * np.pi * 45 * t)).astype(np.float32)
        raw_b = float((bass ** 2).mean())
        self.assertAlmostEqual(10 * np.log10(raw_b / raw_d), 9.0, delta=0.2)
        ev = {"bass": synth_events(ts[::4], [33, 35] * (len(ts) // 8)), "drums": synth_events(ts, [11, 12] * (len(ts) // 2))}
        st, rows = focus_of({"bass": bass, "drums": drums}, ev, self.N)
        self.assertTrue(st)
        self.assertTrue(all(f["voice"] == "drums" for f in st), st)
        self.assertGreater(rows[0]["voices"]["drums"]["share"], rows[0]["voices"]["bass"]["share"])

    def scored_rows(self, scores: dict[str, list[float]], bars_per_unit=8):
        n = len(next(iter(scores.values())))
        rows = []
        for u in range(n):
            a = u * bars_per_unit
            rows.append({"bars": [a, a + bars_per_unit], "start_s": a * BAR_T, "end_s": (a + bars_per_unit) * BAR_T,
                         "voices": {k: {"share": 0.3, "events": 32, "rate": 1.0, "motion": 0.5, "entry": False,
                                        "score": v[u], "eligible": v[u] > -50} for k, v in scores.items()}})
        return rows

    def test_no_stretch_shorter_than_the_minimum(self):
        rng = np.random.default_rng(5)
        for seed in range(20):
            sc = {k: list(rng.normal(0, 4, 12)) for k in ("a", "b", "c")}
            rows = self.scored_rows(sc, bars_per_unit=8)
            for mb in (8, 16, 24):
                ch = decide(rows, list(sc), min_bars=mb)
                st, _ = stretches(rows, ch, None, None, [])
                for f in st:
                    self.assertGreaterEqual(f["bars"], mb, (seed, mb, f))
                    self.assertEqual(f["bar_range"][0] % 8, 0)

    def test_no_flicker(self):
        # a leads by 6.5 to 9 dB with phrase-to-phrase noise: b never comes near enough, no switch (within
        # MAX_RUN_BARS: beyond it a long stretch hands over, test_long_stretch_hands_over)
        rng = np.random.default_rng(4)
        rows = self.scored_rows({"a": [0.0] * 3, "b": list(-rng.uniform(6.5, 9.0, 3))})
        self.assertEqual(decide(rows, ["a", "b"]), ["a"] * 3)
        # leadership changing back and forth by small margins inside a close pair hands over at most once a phrase
        rng = np.random.default_rng(2)
        rows = self.scored_rows({"a": list(rng.normal(0, 0.5, 10)), "b": list(rng.normal(-1, 0.5, 10))}, bars_per_unit=4)
        st, _ = stretches(rows, decide(rows, ["a", "b"], min_bars=8), None, None, [])
        self.assertTrue(all(f["bars"] >= 8 for f in st))

    def test_close_voices_hand_over_phrase_by_phrase(self):
        rows = self.scored_rows({"a": [0.0] * 5, "b": [-3.0] * 5, "c": [-20.0] * 5})
        self.assertEqual(decide(rows, ["a", "b", "c"]), ["a", "b", "a", "b", "a"])

    def test_fixed_focus_and_overrides_are_honoured(self):
        rows = self.scored_rows({"a": [0.0] * 6, "b": [-12.0] * 6})
        self.assertEqual(decide(rows, ["a", "b"], fixed="b"), ["b"] * 6)
        ov = [(rows[2]["start_s"], rows[4]["end_s"], "b"), (rows[5]["start_s"], rows[5]["end_s"], None)]
        self.assertEqual(decide(rows, ["a", "b"], overrides=ov), ["a", "a", "b", "b", "b", None])

    def test_silent_or_eventless_voice_never_gets_focus(self):
        rows = self.scored_rows({"a": [0.0] * 4, "b": [5.0] * 4})
        for r in rows:
            r["voices"]["b"]["eligible"] = False
        self.assertEqual(decide(rows, ["a", "b"]), ["a"] * 4)
        for r in rows:
            r["voices"]["a"]["eligible"] = False
        self.assertEqual(decide(rows, ["a", "b"]), [None] * 4)


class LayoutTests(unittest.TestCase):
    def test_ascending_line_gives_ascending_pads(self):
        ts = [1.0 + i * B_T for i in range(16)]
        hs = [40 + i // 2 for i in range(16)]  # 8 notes rising, two presses each
        pads = layout_stretch(synth_events(ts, hs), "melodic", B_T)["pads"]
        self.assertEqual(pads, sorted(pads))
        self.assertEqual((pads[0], pads[-1]), (1, 4))

    def test_repeated_phrase_gets_the_same_pads(self):
        phrase = [(0, 45), (0.5, 48), (1.5, 52), (2, 50), (3, 45), (3.5, 43)]
        ts, hs = [], []
        for rep in range(4):
            for b, h in phrase:
                ts.append(1.0 + (rep * 4 + b) * B_T)
                hs.append(h)
        pads = layout_stretch(synth_events(ts, hs), "bass", B_T)["pads"]
        n = len(phrase)
        for rep in range(1, 4):
            self.assertEqual(pads[rep * n:(rep + 1) * n], pads[:n])
        self.assertGreaterEqual(len(set(pads)), 3)

    def test_fast_alternation_lands_on_two_thumbs(self):
        ts = [1.0 + i * B_T / 4 for i in range(32)]  # 16ths
        hs = [50, 51] * 16                          # a trill a semitone apart: neighbours by height
        pads = layout_stretch(synth_events(ts, hs), "melodic", B_T)["pads"]
        thumbs = {h: {(p - 1) // 2 for p, hh in zip(pads, hs) if hh == h} for h in (50, 51)}
        self.assertEqual(len(thumbs[50]), 1)
        self.assertNotEqual(thumbs[50], thumbs[51])
        self.assertLess(min(pads[i] for i in range(0, 32, 2)), min(pads[i] for i in range(1, 32, 2)) + 1)

    def test_two_step_kick_and_snare_on_two_thumbs_hats_highest(self):
        evs = []
        for bar in range(8):
            for b, h, f in ((0, 8.5, [-2, -17]), (1, 12.1, [-17, -1]), (2.5, 8.5, [-2, -17]), (3, 12.1, [-17, -1]),
                            (0.5, 12.9, [-6, 15]), (1.5, 12.9, [-6, 15]), (2, 12.9, [-6, 15]), (3.5, 12.9, [-6, 15])):
                t = 1.0 + (bar * 4 + b) * B_T
                evs.append(Event(t=t, strength=1, rel_db=-3, own_db=-3, pos=(bar * 4 + b), height=h, feat=f))
        evs.sort(key=lambda e: e.t)
        lay = layout_stretch(evs, "drums", B_T)
        pad = {round(e.height, 1): p for e, p in zip(evs, lay["pads"])}
        self.assertEqual(len(lay["sounds"]), 3)
        self.assertNotEqual((pad[8.5] - 1) // 2, (pad[12.1] - 1) // 2, f"kick and snare on one thumb: {pad}")
        self.assertEqual(pad[8.5], 1)
        self.assertEqual(max(pad.values()), pad[12.9])

    def test_one_note_rhythm_uses_two_pads(self):
        ts = [1.0 + b * B_T for bar in range(8) for b in (bar * 4 + 0, bar * 4 + 0.75, bar * 4 + 1.5, bar * 4 + 2, bar * 4 + 3.5)]
        lay = layout_stretch(synth_events(ts, [40] * len(ts), t0=1.0), "bass", B_T)
        self.assertEqual(len(set(lay["pads"])), 2)
        self.assertTrue(lay["split"])


def make_pack(root: Path, dur: float = 10.0) -> tuple[Path, Path]:
    """A valid 4-voice v2 pack from tones and clicks, and the 'recording' they sum to. 120 BPM, bars from 0.5 s."""
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
    kinds = {"drums": "drums", "lead": "pitched", "bass": "pitched", "pads": "pitched"}
    tj = {"format": "rhythm_warfare.track.v2", "id": pid, "title": "T", "artist": "A", "duration_s": round(length, 4),
          "tempo": {"bpm": bpm, "first_downbeat_s": 0.5, "beats_per_bar": 4, "confidence": 0.9},
          "voices": [{"key": k, "label": k.title(), "kind": kinds[k], "stem": f"stems/{k}.ogg", "gain": 1.0}
                     for k in ["drums", "lead", "bass", "pads"]],
          "backing": [{"key": "backing", "stem": "stems/backing.ogg", "gain": 1.0}],
          "sections": [{"id": "a", "role": "intro", "start_s": 0.0, "end_s": 4.5},
                       {"id": "b", "role": "drop", "start_s": 4.5, "end_s": round(length, 4)}],
          "focus": [{"start_s": 0.5, "end_s": 4.5, "voice": "drums"}, {"start_s": 4.5, "end_s": 8.5, "voice": "bass"}],
          "charts": {"normal": [{"t": 1.5, "pad": 1, "dur": 0.0, "conf": 0.9, "voice": "drums"},
                                {"t": 2.0, "pad": 3, "dur": 0.0, "conf": 0.8, "voice": "drums"},
                                {"t": 2.5, "pad": 1, "dur": 0.0, "conf": 0.7, "voice": "drums"},
                                {"t": 3.0, "pad": 4, "dur": 0.0, "conf": 0.9, "voice": "drums"},
                                {"t": 5.0, "pad": 2, "dur": 0.5, "conf": 0.5, "voice": "bass"},
                                {"t": 6.5, "pad": 3, "dur": 0.0, "conf": 0.5, "voice": "bass"}]},
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
        self.assertLess(stats["sum_error_db"], -30)

    def test_rejects_each_kind_of_broken_pack(self):
        cases = {
            "format": lambda j: j.update(format="v0"),
            "id": lambda j: j.update(id="Other"),
            "duration": lambda j: j.update(duration_s=0),
            "no voices": lambda j: j.update(voices=[]),
            "seven voices": lambda j: j["voices"].extend(dict(j["voices"][0], key=f"x{i}") for i in range(3)),
            "voice with a pad": lambda j: j["voices"][1].update(pad=1),
            "voice kind": lambda j: j["voices"][1].update(kind="bass"),
            "no focus": lambda j: j.update(focus=[]),
            "focus unknown voice": lambda j: j["focus"][0].update(voice="vocals"),
            "focus too short": lambda j: j["focus"][1].update(end_s=7.0),
            "focus overlap": lambda j: j["focus"][1].update(start_s=4.0),
            "focus outside": lambda j: j["focus"][1].update(end_s=99.0),
            "focus unsorted": lambda j: j["focus"].reverse(),
            "cue without voice": lambda j: j["charts"]["normal"][0].pop("voice"),
            "cue of another voice": lambda j: j["charts"]["normal"][0].update(voice="lead"),
            "cue outside focus": lambda j: j["charts"]["normal"].append({"t": 9.0, "pad": 1, "dur": 0, "conf": 1, "voice": "bass"}),
            "cue of the wrong stretch": lambda j: j["charts"]["normal"][3].update(voice="bass"),
            "hold past its stretch": lambda j: j["charts"]["normal"][3].update(dur=1.6),
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
            "same pad": lambda j: j["charts"]["normal"][1].update(t=1.6, pad=1),
            "short hold": lambda j: j["charts"]["normal"][4].update(dur=0.1),
            "idle rule": lambda j: j.update(rules={"restore_after_idle_beats": -1}),
            "other chart broken": lambda j: j["charts"].update(hard=[{"t": 2.0, "pad": 1, "dur": 0, "conf": 1, "voice": "drums"},
                                                                    {"t": 2.1, "pad": 2, "dur": 0, "conf": 1, "voice": "drums"}]),
        }
        for name, m in cases.items():
            self.assertTrue(self.run_with(m), f"validator accepted a pack with a broken {name}")

    def test_rejects_cue_on_silence(self):
        # the bass rests from 1.5 to 2.0 s in every 2 s: a bass cue at 7.6 s sits on its silence
        def m(j):
            j["charts"]["normal"] = [{"t": 1.5, "pad": 1, "dur": 0.0, "conf": 0.9, "voice": "drums"},
                                     {"t": 7.6, "pad": 2, "dur": 0.0, "conf": 0.9, "voice": "bass"}]
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


# ---------------------------------------------------------------- hardening rules (version 0.3)

class AudibilityTests(unittest.TestCase):
    """Rule A: the chart stage and the validator share one audibility test; no cue the validator rejects."""

    def test_charter_never_emits_a_cue_the_validator_rejects(self):
        from validate_track import SoundLevels
        dur = 20.0
        g = Grid(bpm=BPM_T, first_downbeat=0.0)
        ts = [t for t in np.arange(1.0, dur - 1, B_T / 2)]
        # the drum voice sounds only in the first half; its events go on into the silent half (bad separation,
        # or a detector fooled by bleed), all claimed audible
        x = tone_hits([t for t in ts if t < 10.0], 3000, 0.5, dur, decay=0.02)
        mix = x + tone_hits(ts, 200, 0.3, dur, decay=0.2)
        evs = synth_events(ts, [10.0, 11.0] * (len(ts) // 2 + 1))
        for e in evs:
            e.kind, e.feat = "kick", [0.0, 0.0]
        focus = [{"start_s": 0.0, "end_s": dur, "voice": "drums"}]
        lv = SoundLevels({"drums": x}, mix, RATE)
        stats = {}
        charts, _ = build_charts({"drums": evs}, focus, {"drums": "drums"}, [], g, dur, {"drums": 1.0},
                                 sound_check=lambda c: lv.problem(c, 1.5), stats=stats)
        self.assertGreater(stats["sound_check_removed"]["hard"], 0)
        for d, cues in charts.items():
            self.assertTrue(cues, d)
            for c in cues:
                self.assertIsNone(lv.problem(c.as_json()), (d, c.t))
                self.assertLess(c.t, 10.2)

    def test_self_check_turns_a_failing_hold_into_a_tap(self):
        from chart import self_check
        cues = [Cue(t=2.0, pad=1, dur=2.0, conf=1, score=1, voice="v"), Cue(t=5.0, pad=2, dur=0, conf=1, score=1, voice="v")]
        chk = lambda c: "hold" if c["dur"] > 0 else ("silent" if c["t"] > 4 else None)  # noqa: E731
        out, removed, shortened = self_check(cues, chk)
        self.assertEqual([(c.t, c.dur) for c in out], [(2.0, 0.0)])
        self.assertEqual((removed, shortened), (1, 1))


class TempoTests(unittest.TestCase):
    """Rule B: a constant tempo with sparse and drumless stretches is not flagged; a slide still is."""

    def test_sparse_and_drumless_stretches_do_not_raise_a_false_alarm(self):
        from analysis import constant_tempo_ok
        bpm = 175.0
        B = 60 / bpm
        rng = np.random.default_rng(3)
        times = []
        for k in range(int(150 / B)):
            t = 0.3 + k * B
            if 50 < t < 100:
                continue  # a drumless breakdown
            if 30 < t < 50 and rng.random() < 0.6:
                continue  # sparse drums: a local reading is noisy here
            times += [t, t + B / 2] if rng.random() < 0.5 else [t]
        times = np.array(times) + rng.normal(0, 0.004, len(times))
        tt, w = pick_onsets(click_track(times, noise=0.002), RATE)
        g = fit_grid(tt, w, tempo_candidates(tt, w)["chosen_bpm"])
        self.assertTrue(constant_tempo_ok(g), g["drift_windows_ms"])
        self.assertLess(g["drift_windows_judged"], g["drift_windows_total"])

    def test_slide_still_detected(self):
        from analysis import constant_tempo_ok
        t, b = 0.5, []
        while t < 90:
            b.append(t)
            t += 60 / (170 + 8 * t / 90)
        tt, w = pick_onsets(click_track(b), RATE)
        g = fit_grid(tt, w, tempo_candidates(tt, w)["chosen_bpm"])
        self.assertFalse(constant_tempo_ok(g))


class FocusRuleTests(unittest.TestCase):
    """Rule C: something to play wherever a voice is clearly audible; clean separation preferred; long stretches
    hand over; a breakdown prefers the pitched voice; voices never played are folded into the backing."""
    N = 32

    def test_held_voice_with_soft_attacks_gets_the_focus_where_nothing_else_plays(self):
        dur = self.N * BAR_T + 0.5
        ts = [t for t in np.arange(0, self.N * BAR_T - 1e-9, B_T)]
        pad_ = tone_hits(ts, 440, 0.3, dur, decay=0.5)
        drums = tone_hits([t for t in ts if t < 16 * BAR_T], 3000, 0.6, dur, decay=0.02)
        soft = synth_events(ts, [57, 60, 64, 62] * (len(ts) // 4 + 1), strength=0.2)
        for e in soft:
            e.audible = False  # under the attack threshold of the strict rules
        dev = synth_events([t for t in ts if t < 16 * BAR_T], [10, 11] * len(ts))
        st, rows = focus_of({"drums": drums, "pad": pad_}, {"drums": dev, "pad": soft}, self.N)
        late = [f for f in st if f["bar_range"][1] > 16]
        self.assertTrue(late, st)
        self.assertEqual(late[-1]["voice"], "pad")
        self.assertTrue(late[-1]["relaxed_spans"])
        self.assertTrue(any(r["voices"]["pad"]["relaxed"] for r in rows))

    def test_quiet_voice_under_the_floor_gives_a_gap(self):
        from focus import FLOOR_DB
        dur = self.N * BAR_T + 0.5
        ts = [t for t in np.arange(0, self.N * BAR_T - 1e-9, B_T)]
        loud = tone_hits([t for t in ts if t < 16 * BAR_T], 3000, 0.6, dur, decay=0.02)
        faint = tone_hits([t for t in ts if t >= 16 * BAR_T], 440, 0.6 * 10 ** (-(FLOOR_DB + 10) / 20), dur, decay=0.5)
        ev = {"d": synth_events([t for t in ts if t < 16 * BAR_T], [10, 11] * len(ts)),
              "p": synth_events([t for t in ts if t >= 16 * BAR_T], [60, 62] * len(ts), strength=0.2)}
        for e in ev["p"]:
            e.audible = False
        st, _ = focus_of({"d": loud, "p": faint}, ev, self.N)
        self.assertTrue(all(f["bar_range"][1] <= 16 for f in st), st)

    def rows(self, scores, quality=None):
        return FocusTests.scored_rows(FocusTests(), scores)

    def test_badly_separated_voice_loses_when_close(self):
        from focus import sep_penalty
        self.assertEqual(sep_penalty(1.0), 0.0)
        self.assertEqual(sep_penalty(0.9), 0.0)
        self.assertGreater(sep_penalty(0.61), 3.0)

    def test_long_stretch_hands_over(self):
        from focus import MAX_RUN_BARS
        rows = self.rows({"a": [0.0] * 8, "b": [-10.0] * 8})
        ch = decide(rows, ["a", "b"])
        self.assertIn("b", ch)
        run = longest = 0
        for k in ch:
            run = run + 8 if k == "a" else 0
            longest = max(longest, run)
        self.assertLessEqual(longest, MAX_RUN_BARS + 8)
        # with nobody else eligible the leader keeps it
        self.assertEqual(decide(self.rows({"a": [0.0] * 8, "b": [-99.0] * 8}), ["a", "b"]), ["a"] * 8)

    def test_breakdown_prefers_the_pitched_voice(self):
        from focus import BREAKDOWN_DRUMS_DB
        dur = 16 * BAR_T + 0.5
        ts = [t for t in np.arange(0, 16 * BAR_T - 1e-9, B_T / 2)]
        drums = tone_hits(ts, 3000, 0.5, dur, decay=0.02)
        lead = tone_hits(ts[::2], 660, 0.5, dur, decay=0.1)
        ev = {"drums": synth_events(ts, [10, 11] * len(ts)), "lead": synth_events(ts[::2], [64, 67] * len(ts))}
        edges = np.arange(17) * BAR_T
        out = {}
        for role in ("drop", "breakdown"):
            secs = [{"id": "s", "role": role, "start_s": 0.0, "end_s": float(edges[-1])}]
            units = make_units(secs, edges)
            power = {k: perceived_bar_power(x, RATE, edges) for k, x in {"drums": drums, "lead": lead}.items()}
            rows = unit_table(power, ev, units, edges, B_T, kinds={"drums": "drums", "lead": "melodic"}, sections=secs)
            out[role] = rows[0]["voices"]["drums"]["score"] - rows[0]["voices"]["lead"]["score"]
        self.assertAlmostEqual(out["drop"] - out["breakdown"], BREAKDOWN_DRUMS_DB, delta=0.01)

    def test_voice_never_played_is_folded_into_the_backing(self):
        from import_track import folded_voices
        vj = {"voices": {"kick": {}, "tops": {}, "bass": {}}}
        fj = {"focus": [{"voice": "tops"}, {"voice": "bass"}]}
        ch = {"charts": {"hard": [{"voice": "tops"}]}}
        self.assertEqual(folded_voices(vj, fj, ch), ["kick"])
        self.assertEqual(len(folded_voices(vj, {"focus": []}, {"charts": {}})), 2)  # one voice always stays


class PadAndDensityTests(unittest.TestCase):
    """Rules D and E: no rhythm on one pad; density under the ceilings."""

    def test_one_pad_stretch_is_spread_by_position_in_the_bar(self):
        from chart import spread_one_pad
        ts = [1.0 + i * B_T / 2 for i in range(32)]
        evs = synth_events(ts, [40] * 32, t0=1.0)
        cues = [Cue(t=e.t, pad=2, dur=0, conf=1, score=1, voice="v", ev=e, stretch=0) for e in evs]
        out, n = spread_one_pad(cues)
        self.assertEqual(n, 1)
        self.assertEqual({c.pad for c in out}, {2, 3})
        by_pos = {}
        for c in out:
            by_pos.setdefault(c.ev.pos % 4, set()).add(c.pad)
        self.assertTrue(all(len(p) == 1 for p in by_pos.values()), by_pos)  # same place in the bar, same pad

    def test_dense_drums_stay_under_the_ceilings(self):
        from chart import CAP, CEILING
        dur = 60.0
        g = Grid(bpm=BPM_T, first_downbeat=0.0)
        ts = [t for t in np.arange(1.0, dur - 1, B_T / 4)]  # every 16th, all strong
        evs = synth_events(ts, [6.0, 7.0, 8.0, 9.0] * len(ts))
        for i, e in enumerate(evs):
            e.kind = ("kick", "hat", "snare", "hat")[i % 4]
            e.feat = [[20.0, -20.0], [-20.0, 20.0], [0.0, 0.0], [-20.0, 20.0]][i % 4]
            e.score = 0.5 + 0.1 * (i % 4 == 0)
        focus = [{"start_s": 0.0, "end_s": dur, "voice": "drums"}]
        secs = [{"id": "drop1", "role": "drop", "start_s": 0.0, "end_s": dur}]
        charts, _ = build_charts({"drums": evs}, focus, {"drums": "drums"}, secs, g, dur, {"drums": 1.0})
        beats = dur / B_T
        for d, cues in charts.items():
            self.assertLessEqual(len(cues) / beats, min(CAP[d]["drums"], CEILING[d]) + 1e-6, d)
            self.assertEqual(playability_violations([c.as_json() for c in cues], BPM_T), [], d)


class BatchTests(unittest.TestCase):
    """Rule G: verdicts, and ids that would collide."""

    def test_verdicts(self):
        from import_track import verdict
        self.assertEqual(verdict(None, [], 0), "ok")
        self.assertEqual(verdict(None, ["tempo confidence 0.4"], 0), "ok with warnings")
        self.assertEqual(verdict(None, ["validator: 2 violation(s)"], 2), "FAILED")
        self.assertEqual(verdict("ValueError: x", [], None), "FAILED")

    def test_two_recordings_with_one_id_do_not_overwrite_each_other(self):
        import argparse
        from import_track import Ctx
        with tempfile.TemporaryDirectory() as d:
            a = argparse.Namespace(out=d, id=None, model="htdemucs", focus_auto=False, min_bars=None, focus=None,
                                   focus_at=None)
            meta = {"artist": "A", "title": "T", "id": "a_t", "probe": {}}
            f1, f2 = Path(d) / "one.flac", Path(d) / "two.flac"
            taken = set()
            c1 = Ctx(f1, a, meta=meta, taken=taken)
            taken.add(c1.id)
            c2 = Ctx(f2, a, meta=meta, taken=taken)
            self.assertEqual((c1.id, c2.id, c2.renamed_from), ("a_t", "a_t_2", "a_t"))
            # a later run, alone: the second file still finds its own id, the first keeps its own
            self.assertEqual(Ctx(f2, a, meta=meta, taken=set()).id, "a_t_2")
            self.assertEqual(Ctx(f1, a, meta=meta, taken=set()).id, "a_t")
