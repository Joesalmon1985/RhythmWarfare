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
        # a leads by 6.5 to 9 dB with phrase-to-phrase noise: b never comes near enough, no switch
        rng = np.random.default_rng(4)
        rows = self.scored_rows({"a": [0.0] * 10, "b": list(-rng.uniform(6.5, 9.0, 10))})
        self.assertEqual(decide(rows, ["a", "b"]), ["a"] * 10)
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
