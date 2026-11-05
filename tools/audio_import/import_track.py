#!/usr/bin/env python3
"""Turn finished recordings into track packs (docs/TRACK_PACK_FORMAT.md, version 2). No MIDI: all from audio.

    /home/joe/.venvs/rw-audio/bin/python tools/audio_import/import_track.py FILE_OR_FOLDER [...]
        [--id ID] [--out /home/joe/rw-audio-work] [--model htdemucs] [--from STAGE | --only STAGE]
        [--min-bars 8] [--focus VOICE] [--focus-at WHERE=VOICE ...] [--focus-auto]

Several files or folders are processed one after another; one bad file never stops the batch, and the run ends
with one summary line per track (also written to <out>/batch_summary.txt and a time-stamped copy).

Stages, each cached under <out>/cache/<id>/ and skipped when its output exists; once a stage runs, every later
stage runs too:
    separate  Demucs on the whole file                -> sep_<model>/{mix,<stem>}.npy, meta.json
    analyse   tempo, grid, downbeat, sections         -> analysis.json
    voices    voices + backing                        -> voices.json, voices/<key>.npy
    events    what each voice plays, how high, and its loudness as heard per bar -> events.json
    focus     which voice is the player's, bar by bar -> focus.json
    chart     pads by height, easy / normal / hard    -> charts.json
    pack      stems/*.ogg (only when the voices changed) + track.json -> <out>/packs/<id>/
    preview   listening files                         -> <out>/packs/<id>/preview/
    validate  validate_track.py on the pack, then the evidence report -> <out>/packs/<id>/report.{json,txt}
Focus options (--min-bars, --focus, --focus-at) are remembered per track in cache/<id>/focus_options.json and
used again on later runs until --focus-auto clears them; changing them reruns from the focus stage.
Heavy work runs on whatever OMP_NUM_THREADS says (use 3 and nice -n 10 on the shared laptop).
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_io import mono, probe  # noqa: E402

STAGES = ("separate", "analyse", "voices", "events", "focus", "chart", "pack", "preview", "validate")
VERSION = "audio_import 0.2 (track format v2)"
AUDIO_EXT = {".flac", ".mp3", ".wav", ".ogg", ".m4a", ".aiff", ".aif", ".opus", ".wma", ".aac"}
CONTRACT_KIND = {"drums": "drums", "bass": "pitched", "melodic": "pitched", "vocal": "pitched"}
VOICE_ORDER = ("drums", "kick", "tops", "bass", "other", "lead", "pads", "guitar", "piano", "vocals")


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s or "track"


def guess_meta(path: Path) -> dict:
    info = probe(path)
    tags = info["tags"]
    stem = path.stem
    artist, title = tags.get("artist"), tags.get("title")
    if not (artist and title):
        parts = [p.strip() for p in stem.split(" - ")]
        artist = artist or parts[0]
        title = title or re.sub(r"^\d+\s+", "", parts[-1])
    return {"artist": artist, "title": title, "id": slug(f"{artist} {title}"), "probe": info}


class Ctx:
    def __init__(self, src: Path, a: argparse.Namespace):
        self.src = Path(src).resolve()
        self.meta = guess_meta(self.src)
        self.id = a.id or self.meta["id"]
        self.out = Path(a.out)
        self.cache = self.out / "cache" / self.id
        self.pack = self.out / "packs" / self.id
        self.model = a.model
        self.sep_dir = self.cache / f"sep_{self.model}"
        self.timings: dict[str, float] = {}
        self.cache.mkdir(parents=True, exist_ok=True)
        tf = self.cache / "timings.json"
        if tf.exists():
            self.timings = json.loads(tf.read_text())
        # focus options: the command line wins and is remembered; --focus-auto forgets
        of = self.cache / "focus_options.json"
        saved = json.loads(of.read_text()) if of.exists() else {}
        if a.focus_auto:
            saved = {}
        given = {k: v for k, v in (("min_bars", a.min_bars), ("fixed", a.focus), ("overrides", a.focus_at)) if v}
        self.focus_opts = {"min_bars": 8, "fixed": None, "overrides": [], **saved, **given}
        stored = {k: v for k, v in self.focus_opts.items() if v and not (k == "min_bars" and v == 8)}
        if stored:
            of.write_text(json.dumps(stored, indent=1))
        elif of.exists():
            of.unlink()

    def save_timings(self) -> None:
        (self.cache / "timings.json").write_text(json.dumps(self.timings, indent=1))

    def jload(self, name: str) -> dict:
        return json.loads((self.cache / name).read_text())

    def jsave(self, name: str, obj) -> None:
        (self.cache / name).write_text(json.dumps(obj, indent=1, default=_np))


def _np(o):
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


# ---------------------------------------------------------------- stages

def st_separate(c: Ctx) -> bool:
    from separate import separate
    if (c.sep_dir / "meta.json").exists():
        return False
    separate(c.src, c.sep_dir, c.model)
    return True


def _load_sep(c: Ctx):
    from separate import load
    return load(c.sep_dir)


def st_analyse(c: Ctx) -> None:
    from analysis import (band_filter, bar_levels, beat_strengths, constant_tempo_ok, find_downbeat, fit_grid,
                          label_sections, onset_envelope, pick_onsets, segment, tempo_candidates)
    from audio_io import db, frame_rms
    from voices import stem_report
    mix, stems, meta = _load_sep(c)
    rate = meta["rate"]
    dur = len(mix) / rate
    dm = mono(stems["drums"]) if "drums" in stems else mono(mix)
    env = onset_envelope(dm, rate)
    t, w = pick_onsets(dm, rate, env=env, min_gap=0.06)
    strong = w >= 0.15
    tc = tempo_candidates(t[strong], w[strong])
    grid = fit_grid(t[strong], w[strong], tc["chosen_bpm"])
    bpm, B = grid["bpm"], grid["beat_s"]
    constant = constant_tempo_ok(grid)
    if constant:
        beats = grid["t0"] + B * np.arange(int((dur - grid["t0"]) / B) + 1)
        beat_source = "constant grid fitted to every drum onset"
    else:
        import librosa
        _, bf = librosa.beat.beat_track(onset_envelope=env, sr=rate, hop_length=256, start_bpm=bpm, tightness=400)
        beats = bf * 256 / rate
        beat_source = "detected beats (tempo not constant; no stretching)"
    kick = beat_strengths(onset_envelope(band_filter(dm, rate, None, 150.0), rate), rate, 256, beats)
    snare = beat_strengths(onset_envelope(band_filter(dm, rate, 150.0, 2500.0), rate), rate, 256, beats)
    drive = sum(mono(stems[k]) for k in ("drums", "bass") if k in stems)
    e = db(frame_rms(drive, rate, 0.01, 0.02))
    edb = np.array([e[int(b / 0.01):int((b + B) / 0.01)].mean() if int(b / 0.01) < len(e) else -100 for b in beats])
    dbt = find_downbeat(beats, kick, snare, edb)
    first_db = float(beats[dbt["phase"]])
    bar = 4 * B
    bars = np.arange(first_db - bar * np.floor(first_db / bar), dur, bar)
    if constant:
        edges = np.unique(np.r_[0.0, bars[bars > 0.02], dur])
    else:
        edges = np.unique(np.r_[0.0, beats[dbt["phase"]::4], dur])
    levels = bar_levels(stems, rate, edges)
    bounds = segment(levels, edges)
    secs = label_sections(levels, bounds, edges, ("drums", "bass"))
    sections = []
    for s in secs:
        a, b = float(edges[s["bar_start"]]), float(edges[s["bar_end"]])
        sections.append({"id": s["id"], "role": s["role"], "start_s": round(a, 4), "end_s": round(b, 4),
                         "bars": s["bar_end"] - s["bar_start"], "intensity_db": s["intensity_db"], "parts_db": s["parts_db"]})
    rep = stem_report(mix, stems, rate, sections, drum_onsets=t[w >= 0.3])
    conf = float(np.clip(grid["share_on_grid"] * (1 - grid["drift_ms_max_abs"] / 40.0)
                         * (0.7 + 0.3 * dbt["confidence"] / max(dbt["confidence"], 0.3)), 0, 1))
    c.jsave("analysis.json", {
        "duration_s": dur, "rate": rate, "tempo_candidates": tc, "grid": grid, "constant_tempo": constant,
        "beat_source": beat_source, "beats": beats, "downbeat": dbt, "first_downbeat_s": first_db,
        "tempo_confidence": round(conf, 3), "bar_edges": edges, "bar_levels": levels, "sections": sections,
        "stem_report": rep, "drum_onsets": {"t": t, "w": w},
        "vs_174": {"ratio": round(bpm / 174.0, 5), "ratio_87": round(bpm / 87.0, 5)}})


def _grid(c: Ctx):
    from chart import Grid
    an = c.jload("analysis.json")
    g = Grid(bpm=an["grid"]["bpm"], first_downbeat=an["first_downbeat_s"],
             beats=None if an["constant_tempo"] else np.array(an["beats"]))
    return an, g


def sep_quality(name: str, rep: dict) -> float:
    """0..1 for cue confidence: lower when the part's attacks coincide with drum hits much more than chance
    (likely bleed) or its envelope moves with another stem."""
    q = 1.0
    bleed = rep.get("transient_bleed", {}).get(name)
    if bleed is not None:
        q -= min(0.4, max(0.0, bleed - 1.2) * 0.2)
    corr = [v for k, v in rep["env_corr"].items() if name in k.split("-")]
    if corr and max(corr) > 0.5:
        q -= 0.2
    return round(max(0.3, q), 2)




def sep_word(name: str, rep: dict) -> str:
    """Separation quality of a voice in one word for the batch summary."""
    st = rep["stems"].get(name)
    q = sep_quality(name, rep)
    if st is None:
        return "derived"
    if q >= 0.9 and st["active_share"] >= 0.25:
        return "clean"
    if q >= 0.7:
        return "fair"
    return "poor"


def st_voices(c: Ctx) -> None:
    from voices import LABELS, choose_voices
    mix, stems, meta = _load_sep(c)
    an = c.jload("analysis.json")
    ch = choose_voices(mix, stems, meta["rate"], an["stem_report"])
    vdir = c.cache / "voices"
    vdir.mkdir(exist_ok=True)
    for k, v in ch["voices"].items():
        np.save(vdir / f"{k}.npy", v["audio"].astype(np.float32))
    np.save(vdir / "backing.npy", ch["backing"])
    rep = an["stem_report"]
    info = {k: {"label": LABELS.get(k, k.title()), "from": v["from"], "op": v["op"], "kind": v["kind"],
                "sep_quality": sep_quality(v["from"][0], rep) if v["op"] == "stem" else 0.6}
            for k, v in ch["voices"].items()}
    c.jsave("voices.json", {"voices": info, "backing_from": ch["backing_from"], "notes": ch["notes"]})


def _voice_audio(c: Ctx) -> dict[str, np.ndarray]:
    vj = c.jload("voices.json")
    return {k: np.load(c.cache / "voices" / f"{k}.npy") for k in vj["voices"]}


def st_events(c: Ctx) -> None:
    from chart import describe, events
    from focus import perceived_bar_power
    mix, _stems, meta = _load_sep(c)
    rate = meta["rate"]
    an, g = _grid(c)
    vj = c.jload("voices.json")
    edges = np.array(an["bar_edges"])
    out, power = {}, {}
    for k, x in _voice_audio(c).items():
        kind = vj["voices"][k]["kind"]
        evs = events(x, mix, rate, kind, g)
        describe(evs, x, rate, kind)
        out[k] = [e.to_json() for e in evs]
        power[k] = perceived_bar_power(x, rate, edges)
    c.jsave("events.json", {"events": out, "bar_power_weighted": power,
                            "note": "bar_power_weighted: mean power per bar after the half-A weighting (focus.py)"})


def _events(c: Ctx) -> dict:
    from chart import Event
    ej = c.jload("events.json")
    return {k: [Event.from_json(d) for d in v] for k, v in ej["events"].items()}, ej


def st_focus(c: Ctx) -> None:
    import focus as F
    an, g = _grid(c)
    vj = c.jload("voices.json")
    ve, ej = _events(c)
    edges = np.array(an["bar_edges"])
    keys = list(vj["voices"])
    o = c.focus_opts
    if o["fixed"] and o["fixed"] not in keys:
        raise ValueError(f"--focus {o['fixed']!r}: voices are {keys}")
    overrides = F.parse_overrides(o["overrides"], an["sections"], keys)
    units = F.make_units(an["sections"], edges)
    power = {k: np.array(ej["bar_power_weighted"][k]) for k in keys}
    rows = F.unit_table(power, ve, units, edges, g.beat_s)
    choice = F.decide(rows, keys, o["min_bars"], o["fixed"], overrides)
    stretches, gaps = F.stretches(rows, choice, o["fixed"], overrides, an["sections"])
    c.jsave("focus.json", {"options": o, "focus": stretches, "gaps": gaps, "units": rows,
                           "timeline": F.short_timeline(stretches, gaps),
                           "constants": {k: getattr(F, k) for k in ("MIN_SHARE", "MIN_EVENTS_PER_BAR", "PLAYABLE_STRENGTH",
                                                                     "ACT_DB", "MOTION_DB", "ENTRY_DB", "CLOSE_DB",
                                                                     "SWITCH_DB", "FATIGUE_DB", "GAP_DB", "PHRASE_BARS")}})


def st_chart(c: Ctx) -> None:
    from chart import build_charts, rank
    an, g = _grid(c)
    vj = c.jload("voices.json")
    fj = c.jload("focus.json")
    ve, _ = _events(c)
    kinds = {k: v["kind"] for k, v in vj["voices"].items()}
    focus = fj["focus"]
    for k, evs in ve.items():
        rank(evs, kinds[k], [f for f in focus if f["voice"] == k])
    sq = {k: v["sep_quality"] for k, v in vj["voices"].items()}
    charts, layouts = build_charts(ve, focus, kinds, an["sections"], g, an["duration_s"], sq)
    c.jsave("charts.json", {
        "charts": {d: [dict(cu.as_json(), score=round(cu.score, 3), ev_t=round(cu.ev.t, 4), stretch=cu.stretch,
                            natural=round(cu.natural, 3), kind=cu.ev.kind, dev_ms=round(cu.ev.dev_ms, 1),
                            h=None if not np.isfinite(cu.ev.height) else round(cu.ev.height, 2), s=round(cu.ev.strength, 3))
                       for cu in cues] for d, cues in charts.items()},
        "layouts": layouts})


def _stamp(c: Ctx) -> str:
    vd = c.cache / "voices"
    return json.dumps({p.name: [p.stat().st_size, int(p.stat().st_mtime)] for p in sorted(vd.glob("*.npy"))})


def st_pack(c: Ctx) -> None:
    from pack import write_pack
    _mix, _stems, meta = _load_sep(c)
    rate = meta["rate"]
    an = c.jload("analysis.json")
    vj = c.jload("voices.json")
    ch = c.jload("charts.json")
    fj = c.jload("focus.json")
    keys = sorted(vj["voices"], key=lambda k: VOICE_ORDER.index(k) if k in VOICE_ORDER else len(VOICE_ORDER))
    va = _voice_audio(c)
    voices = [{"key": k, "label": vj["voices"][k]["label"], "kind": CONTRACT_KIND.get(vj["voices"][k]["kind"], "pitched"),
               "audio": va[k]} for k in keys]
    backing = [{"key": "backing", "audio": np.load(c.cache / "voices" / "backing.npy")}]
    clean = {d: [{k: cu[k] for k in ("t", "pad", "dur", "conf", "voice")} for cu in cues] for d, cues in ch["charts"].items()}
    m = c.meta
    lay = {x["stretch"]: {k: v for k, v in x.items() if k != "stretch"} for x in ch["layouts"]}
    tj_meta = {
        "id": c.id, "title": m["title"], "artist": m["artist"],
        "tempo": {"bpm": round(an["grid"]["bpm"], 4), "first_downbeat_s": round(an["first_downbeat_s"], 4),
                  "beats_per_bar": 4, "confidence": an["tempo_confidence"]},
        "sections": [{k: s[k] for k in ("id", "role", "start_s", "end_s")} for s in an["sections"]],
        "focus": [{k: f[k] for k in ("start_s", "end_s", "voice")} for f in fj["focus"]],
        "charts": {d: clean[d] for d in ("easy", "normal", "hard")},
        "source": {"input_file": c.src.name, "input_path": str(c.src),
                   "input": {k: m["probe"][k] for k in ("codec", "rate", "channels", "duration")},
                   "tool": VERSION, "separation": {"model": c.model, "residual_db": an["stem_report"]["residual_db"]},
                   "voices": {k: {kk: v[kk] for kk in ("from", "op", "kind", "sep_quality")} for k, v in vj["voices"].items()},
                   "backing_from": vj["backing_from"], "voice_notes": vj["notes"],
                   "tempo_detail": {"constant": an["constant_tempo"], "beat_source": an["beat_source"],
                                    "residual_ms_rms": an["grid"]["residual_ms_rms"],
                                    "drift_ms_max_abs": an["grid"]["drift_ms_max_abs"],
                                    "candidates": an["tempo_candidates"]["candidates"],
                                    "downbeat_confidence": an["downbeat"]["confidence"]},
                   "sections_detail": [{k: s[k] for k in ("id", "bars", "intensity_db")} for s in an["sections"]],
                   "focus_options": fj["options"],
                   "focus_detail": [{**{k: f[k] for k in ("start_s", "end_s", "voice", "bars", "sections", "share",
                                                          "runner_up", "runner_up_share", "why")},
                                     "pads": lay.get(i)} for i, f in enumerate(fj["focus"])],
                   "gaps": fj["gaps"],
                   "focus_rule": "perceived loudness (half-A weighting) share per 8-bar phrase plus activity, "
                                 "movement and entry bonuses; stretches by dynamic programming with hysteresis, a "
                                 "minimum length and a handover between voices within 6 dB (see tools/audio_import/focus.py)",
                   "pad_rule": "per stretch, sounds (semitones; drum hits clustered by band balance) laid out by "
                               "height, split across thumbs so quick alternations land on two thumbs "
                               "(tools/audio_import/layout.py)",
                   "chart_note": "cue times are the detected attack in the voice's own stem, or the 16th grid line "
                                 "when the attack is within 6 ms of it; conf blends separation quality, attack "
                                 "strength and how loud the voice is against the whole track there"}}
    write_pack(c.pack, tj_meta, voices, backing, rate, _stamp(c))


def pick_miss(an: dict, tj: dict) -> dict:
    """30 s around the longest focus stretch, inside a drop, of the voice that has the focus most of the drops'
    time: that voice plays for a few seconds, then is silent from one of its cues until its first cue at least 4
    bars later (a run of missed presses; the game brings it back on the next hit), and plays on."""
    drops = [s for s in an["sections"] if s["role"] == "drop"] or an["sections"]

    def inside(f):
        return sum(max(0.0, min(f["end_s"], d["end_s"]) - max(f["start_s"], d["start_s"])) for d in drops)
    time_of: dict[str, float] = {}
    for f in tj["focus"]:
        time_of[f["voice"]] = time_of.get(f["voice"], 0.0) + inside(f)
    key = max(time_of, key=lambda k: (time_of[k], k))
    st = max((f for f in tj["focus"] if f["voice"] == key), key=lambda f: (inside(f), -f["start_s"]))
    B = 60.0 / an["grid"]["bpm"]
    start = max(0.0, st["start_s"] - 2.0)
    end = min(start + 30.0, an["duration_s"] - 0.5)
    mine = [x["t"] for x in tj["charts"]["normal"] if x["voice"] == key and st["start_s"] <= x["t"] < st["end_s"]]
    m0 = next((t for t in mine if t >= st["start_s"] + 5.0), st["start_s"] + 5.0)
    m1 = next((t for t in mine if t >= m0 + 16 * B), min(st["end_s"], m0 + 16 * B))
    return {"key": key, "start_s": round(start, 4), "end_s": round(end, 4), "mute_from_s": round(m0, 4),
            "mute_to_s": round(min(m1, end - 0.5), 4), "stretch": [st["start_s"], st["end_s"]]}


def st_preview(c: Ctx) -> None:
    from pack import write_previews
    mix, _stems, meta = _load_sep(c)
    an = c.jload("analysis.json")
    tj = json.loads((c.pack / "track.json").read_text())
    miss = pick_miss(an, tj)
    write_previews(c.pack / "preview", mix, _voice_audio(c), tj["charts"]["normal"], tj["focus"], meta["rate"], miss)
    c.jsave("miss.json", miss)


def st_validate(c: Ctx) -> int:
    import report
    from validate_track import validate
    r, stats = validate(c.pack)
    for e in r.errors[:50]:
        print("VIOLATION:", e)
    print(f"{'FAIL' if r.errors else 'OK'}: {len(r.errors)} violation(s)")
    report.write(c, stats, r)
    return 1 if r.errors else 0


FUNCS = {"separate": st_separate, "analyse": st_analyse, "voices": st_voices, "events": st_events, "focus": st_focus,
         "chart": st_chart, "pack": st_pack, "preview": st_preview, "validate": st_validate}
OUTPUTS = {"separate": lambda c: c.sep_dir / "meta.json", "analyse": lambda c: c.cache / "analysis.json",
           "voices": lambda c: c.cache / "voices.json", "events": lambda c: c.cache / "events.json",
           "focus": lambda c: c.cache / "focus.json", "chart": lambda c: c.cache / "charts.json",
           "pack": lambda c: c.pack / "track.json", "preview": lambda c: c.pack / "preview" / "focus_forward_normal.ogg",
           "validate": lambda c: None}


def _stale(c: Ctx, st: str) -> bool:
    """A cached output made by older code or other options."""
    try:
        if st == "voices":
            return any("pad" in v for v in c.jload("voices.json")["voices"].values())
        if st == "focus":
            return c.jload("focus.json").get("options") != c.focus_opts
        if st == "pack":
            return json.loads((c.pack / "track.json").read_text()).get("format") != "rhythm_warfare.track.v2"
    except (OSError, ValueError, KeyError):
        return True
    return False


def run_track(c: Ctx, a: argparse.Namespace) -> dict:
    """All stages for one track; returns what the summary line needs."""
    print(f"\n=== {c.src.name} -> id {c.id}\n cache {c.cache}\n pack  {c.pack}", flush=True)
    todo = [a.only] if a.only else STAGES[STAGES.index(a.start):] if a.start else STAGES
    rc = 0
    running = False
    for st in STAGES:
        forced = bool(a.only or a.start) and st in todo
        out = OUTPUTS[st](c)
        need = st == "validate" or forced or running or out is None or not out.exists() or _stale(c, st)
        if st not in todo or not need:
            if st in todo:
                print(f"[{st}] cached", flush=True)
            continue
        if st == "separate" and (c.sep_dir / "meta.json").exists():
            (c.sep_dir / "meta.json").unlink()
        t0 = time.time()
        print(f"[{st}] running", flush=True)
        res = FUNCS[st](c)
        c.timings[st] = round(time.time() - t0, 1)
        c.save_timings()
        print(f"[{st}] {c.timings[st]} s", flush=True)
        running = not a.only
        if st == "validate":
            rc = res
    return {"rc": rc}


def summary_line(c: Ctx | None, src: Path, err: str | None = None) -> tuple[str, list[str]]:
    """One line a person can scan, and the warnings behind it."""
    warn: list[str] = []
    if c is None:
        return f"{src.name}: ERROR {err}", [f"ERROR {err}"]
    parts = [c.id]
    try:
        an = c.jload("analysis.json")
        g = an["grid"]
        parts.append(f"{g['bpm']:.2f} BPM {'constant' if an['constant_tempo'] else 'NOT constant'}"
                     f" (drift {g['drift_ms_max_abs']:.0f} ms, conf {an['tempo_confidence']:.2f})")
        if not an["constant_tempo"]:
            warn.append(f"tempo not constant (drift {g['drift_ms_max_abs']} ms, {g['share_on_grid']:.0%} of drum onsets on the grid): check the cue timing by ear")
        elif an["tempo_confidence"] < 0.5:
            warn.append(f"tempo confidence {an['tempo_confidence']}: check the grid by ear")
        vj = c.jload("voices.json")
        words = {k: sep_word(v["from"][0], an["stem_report"]) if v["op"] == "stem" else "derived" for k, v in vj["voices"].items()}
        parts.append("sep " + " ".join(f"{k}:{w}" for k, w in words.items()))
        for k, w in words.items():
            if w == "poor":
                warn.append(f"{k} separated badly (cue confidence low; a miss on it may sound odd)")
        fj = c.jload("focus.json")
        B = 60.0 / g["bpm"]
        parts.append("focus " + fj["timeline"])
        if fj["options"].get("fixed") or fj["options"].get("overrides"):
            parts.append(f"(overridden: {json.dumps({k: v for k, v in fj['options'].items() if v and k != 'min_bars'})})")
        for gp in fj["gaps"]:
            if gp["bars"] >= 16 and "forced" not in gp["why"]:
                warn.append(f"{gp['bars']} bars with nothing to play ({gp['start_s']:.0f}-{gp['end_s']:.0f} s)")
        total = sum(f["end_s"] - f["start_s"] for f in fj["focus"])
        for k in vj["voices"]:
            share = sum(f["end_s"] - f["start_s"] for f in fj["focus"] if f["voice"] == k) / max(total, 1e-9)
            if share > 0.8 and len(vj["voices"]) > 1:
                warn.append(f"{k} has the focus {share:.0%} of the playable time (little variety)")
        tj = json.loads((c.pack / "track.json").read_text())
        parts.append("cues " + " ".join(f"{d}:{len(tj['charts'][d])}" for d in ("easy", "normal", "hard")))
        rj = json.loads((c.pack / "report.json").read_text()) if (c.pack / "report.json").exists() else {}
        nv = rj.get("validation", {}).get("violations")
        if nv:
            warn.append(f"validator: {nv} violation(s), see {c.pack / 'report.txt'}")
        elif nv is None:
            warn.append("no validation result")
        _ = B
    except Exception as e:  # noqa: BLE001  a summary must never stop the batch
        warn.append(f"summary incomplete: {type(e).__name__}: {e}")
    if err:
        warn.insert(0, f"ERROR {err}")
    line = " | ".join(parts) + (" | " + " ; ".join(f"WARNING {w}" for w in warn) if warn else " | ok")
    return line, warn


def inputs(paths: list[str]) -> list[Path]:
    out = []
    for p in paths:
        q = Path(p)
        if q.is_dir():
            out += sorted(x for x in q.iterdir() if x.is_file() and x.suffix.lower() in AUDIO_EXT)
        else:
            out.append(q)
    return out


def _imported(c: Ctx) -> bool:
    """A pack exists for this recording and its last validation found nothing wrong."""
    try:
        rep = json.loads((c.pack / "report.json").read_text())
        return (c.pack / "track.json").exists() and rep.get("validation", {}).get("violations") == 0
    except (OSError, ValueError):
        return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", nargs="+", help="audio files and/or folders of audio files")
    ap.add_argument("--id", help="pack id (default: artist_title from tags or file name); one input only")
    ap.add_argument("--out", default="/home/joe/rw-audio-work")
    ap.add_argument("--model", default="htdemucs", choices=("htdemucs", "htdemucs_ft", "htdemucs_6s"))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--from", dest="start", choices=STAGES, help="rerun this stage and every later one")
    g.add_argument("--only", choices=STAGES, help="run just this stage (earlier caches must exist)")
    ap.add_argument("--min-bars", type=int, help="shortest focus stretch in bars (default 8)")
    ap.add_argument("--focus", help="give the focus to this voice wherever it plays (drums, bass, other, vocals)")
    ap.add_argument("--focus-at", action="append", metavar="WHERE=VOICE",
                    help="force the focus in a section id or a time range: drop1=bass, 77.2-132.4=drums, "
                         "breakdown1=none; repeatable")
    ap.add_argument("--focus-auto", action="store_true", help="forget focus options remembered for the track")
    ap.add_argument("--skip-imported", action="store_true",
                    help="leave alone any recording whose pack already exists and validated (for resuming a batch)")
    ap.add_argument("--prune-cache", action="store_true",
                    help="after a recording is packed and validated, delete its cached separated audio (about "
                         "1 GB each); a later rerun of that recording separates it again")
    a = ap.parse_args(argv)
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    files = inputs(a.audio)
    if a.id and len(files) != 1:
        ap.error("--id needs exactly one input file")
    lines, rc = [], 0
    for f in files:
        c, err = None, None
        try:
            if not f.is_file():
                raise FileNotFoundError(f"{f} not found")
            c = Ctx(f, a)
            if a.skip_imported and _imported(c):
                lines.append(f"{c.id} | already imported (pack validated), skipped")
                print(lines[-1], flush=True)
                continue
            res = run_track(c, a)
            rc = max(rc, res["rc"])
            if a.prune_cache and res["rc"] == 0:
                import shutil
                for d in [*c.cache.glob("sep_*"), c.cache / "voices"]:
                    shutil.rmtree(d, ignore_errors=True)
        except Exception as e:  # noqa: BLE001  one bad file never stops the batch
            traceback.print_exc()
            import subprocess
            if isinstance(e, subprocess.CalledProcessError) and c is None:
                err = "cannot read the audio (ffprobe failed on it)"
            else:
                err = f"{type(e).__name__}: {e}"
            rc = 2
        line, _ = summary_line(c, f, err)
        lines.append(line)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    text = f"# import_track.py {stamp}: {len(files)} track(s)\n" + "\n".join(lines) + "\n"
    print("\n" + text)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "batch_summary.txt").write_text(text)
    (out / f"batch_summary_{stamp}.txt").write_text(text)
    return rc


if __name__ == "__main__":
    sys.exit(main())
