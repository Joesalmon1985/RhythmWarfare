#!/usr/bin/env python3
"""Turn finished recordings into track packs (docs/TRACK_PACK_FORMAT.md, version 2). No MIDI: all from audio.

    /home/joe/.venvs/rw-audio/bin/python tools/audio_import/import_track.py FILE_OR_FOLDER [...]
        [--id ID] [--out /home/joe/rw-audio-work] [--model htdemucs] [--from STAGE | --only STAGE]
        [--min-bars 8] [--focus VOICE] [--focus-at WHERE=VOICE ...] [--focus-auto] [--skip-imported] [--prune-cache]
    /home/joe/.venvs/rw-audio/bin/python tools/audio_import/import_track.py --rechart [ID ...]

--rechart reruns focus, chart, pack, preview and validate of existing packs from the cached analysis and the
encoded stems (no recording, no Demucs). Every summary line ends with ok, ok with warnings or FAILED; the exit
code is 0 unless a pack has validator violations (1) or a track failed (2).

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
VERSION = "audio_import 0.3 (track format v2)"
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
    def __init__(self, src: Path | None, a: argparse.Namespace, pack_id: str | None = None, meta: dict | None = None,
                 taken: set | None = None):
        """One recording. src: the audio file (None to work from an existing pack: --rechart). taken: ids
        already used in this run; an id used by another recording gets a suffix (_2, _3, ...)."""
        self.out = Path(a.out)
        self.renamed_from = None
        if src is None:
            tj = json.loads((self.out / "packs" / pack_id / "track.json").read_text())
            self.src = Path(tj.get("source", {}).get("input_path") or tj.get("source", {}).get("input_file", "unknown"))
            self.meta = {"artist": tj["artist"], "title": tj["title"], "id": pack_id,
                         "probe": {"codec": None, "rate": None, "channels": None, "duration": tj["duration_s"],
                                   **{k: v for k, v in tj.get("source", {}).get("input", {}).items()}}}
            self.id = pack_id
        else:
            self.src = Path(src).resolve()
            self.meta = meta or guess_meta(self.src)
            base = a.id or self.meta["id"]
            self.id = base
            n = 2
            while (taken and self.id in taken) or self._owned_by_other(self.id):
                self.id = f"{base}_{n}"
                n += 1
            if self.id != base:
                self.renamed_from = base
        self.cache = self.out / "cache" / self.id
        self.pack = self.out / "packs" / self.id
        self.model = a.model
        self.sep_dir = self.cache / f"sep_{self.model}"
        self.timings: dict[str, float] = {}
        self.cache.mkdir(parents=True, exist_ok=True)
        if src is not None:
            (self.cache / "source.txt").write_text(str(self.src) + "\n")
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

    def _owned_by_other(self, pid: str) -> bool:
        """The id's cache or pack was made from another recording (same artist and title, another file)."""
        f = self.out / "cache" / pid / "source.txt"
        if f.is_file():
            return f.read_text().strip() != str(self.src)
        try:
            tj = json.loads((self.out / "packs" / pid / "track.json").read_text())
            return Path(tj["source"]["input_path"]).resolve() != self.src
        except (OSError, ValueError, KeyError):
            return False

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


def _has_sep(c: Ctx) -> bool:
    return (c.sep_dir / "meta.json").is_file() and (c.cache / "voices" / "backing.npy").is_file()


def _stem_src(c: Ctx) -> Path | None:
    """The encoded voices and backing, every voice of voices.json, as they came from the separation: the
    cache's stem_src (hard links to the pack's stems where they are the same file), or, for a pack made before
    there was one, the pack's own stems when none of its voices was folded into the backing."""
    vj = c.jload("voices.json")
    keys = [*vj["voices"], "backing"]
    d = c.cache / "stem_src"
    if (d / ".made_from").is_file() and all((d / f"{k}.ogg").is_file() for k in keys):
        return d
    p = c.pack / "stems"
    if (p / ".made_from").is_file() and all((p / f"{k}.ogg").is_file() for k in keys):
        info = json.loads((p / ".made_from").read_text())
        if not info.get("folded"):
            import shutil
            shutil.rmtree(d, ignore_errors=True)
            d.mkdir(parents=True)
            for k in keys:
                _link(p / f"{k}.ogg", d / f"{k}.ogg")
            (d / ".made_from").write_text(json.dumps(info))
            return d
    return None


def _link(a: Path, b: Path) -> None:
    import shutil
    if b.exists():
        b.unlink()
    try:
        os.link(a, b)
    except OSError:
        shutil.copy2(a, b)


def _audio(c: Ctx, need_mix: bool = True) -> dict:
    """The audio the later stages work on: the separation cache if it is there, else the encoded stems (the
    same audio, already in the pack): {rate, mix, voices: {key: (frames, 2)}, backing, source}. So focus, chart,
    pack, preview and validate run after --prune-cache in seconds, without separating again."""
    vj = c.jload("voices.json")
    if _has_sep(c):
        mix, _stems, meta = _load_sep(c)
        return {"rate": meta["rate"], "mix": mix, "voices": _voice_audio(c),
                "backing": np.load(c.cache / "voices" / "backing.npy"), "source": "separation cache"}
    d = _stem_src(c)
    if d is None:
        raise RuntimeError(f"{c.id}: the separated audio is gone (pruned) and there are no encoded stems of every "
                           f"voice to work from; import the recording again without --from to separate it again")
    from audio_io import PACK_RATE, decode
    info = json.loads((d / ".made_from").read_text())
    g = float(info.get("gain", 1.0))
    voices = {k: decode(d / f"{k}.ogg", rate=PACK_RATE)[0] * g for k in vj["voices"]}
    backing = decode(d / "backing.ogg", rate=PACK_RATE)[0] * g
    n = min([len(backing), *(len(v) for v in voices.values())])
    voices = {k: v[:n] for k, v in voices.items()}
    backing = backing[:n]
    mix = backing + sum(voices.values()) if need_mix else None
    return {"rate": PACK_RATE, "mix": mix, "voices": voices, "backing": backing, "source": f"encoded stems ({d})"}


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
        if len(beats) > 1:  # the grid's origin is the start of the audio: carry the first beats back to 0
            b0 = float(np.median(np.diff(beats[:9])))
            back = beats[0] - b0 * np.arange(int(beats[0] / b0), 0, -1)
            beats = np.r_[back[back >= 0], beats]
        beat_source = "detected beats (tempo not constant; no stretching), carried back to the start at the first beats' period"
    kick = beat_strengths(onset_envelope(band_filter(dm, rate, None, 150.0), rate), rate, 256, beats)
    snare = beat_strengths(onset_envelope(band_filter(dm, rate, 150.0, 2500.0), rate), rate, 256, beats)
    drive = sum(mono(stems[k]) for k in ("drums", "bass") if k in stems)
    e = db(frame_rms(drive, rate, 0.01, 0.02))
    edb = np.array([e[int(b / 0.01):int((b + B) / 0.01)].mean() if int(b / 0.01) < len(e) else -100 for b in beats])
    dbt = find_downbeat(beats, kick, snare, edb)
    first_db = float(beats[dbt["phase"]])  # the first bar line from the start of the audio (beats start within a beat of 0)
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
    au = _audio(c)
    mix, rate = au["mix"], au["rate"]
    an, g = _grid(c)
    vj = c.jload("voices.json")
    edges = np.array(an["bar_edges"])
    out, power = {}, {}
    for k, x in au["voices"].items():
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
    rep = an["stem_report"]
    quality = {k: sep_quality(v["from"][0], rep) for k, v in vj["voices"].items()}
    kinds = {k: v["kind"] for k, v in vj["voices"].items()}
    rows = F.unit_table(power, ve, units, edges, g.beat_s, quality, kinds, an["sections"])
    choice = F.decide(rows, keys, o["min_bars"], o["fixed"], overrides)
    stretches, gaps = F.stretches(rows, choice, o["fixed"], overrides, an["sections"])
    c.jsave("focus.json", {"options": o, "focus": stretches, "gaps": gaps, "units": rows,
                           "timeline": F.short_timeline(stretches, gaps),
                           "constants": {k: getattr(F, k) for k in ("MIN_SHARE", "MIN_EVENTS_PER_BAR", "PLAYABLE_STRENGTH",
                                                                     "ACT_DB", "MOTION_DB", "ENTRY_DB", "CLOSE_DB",
                                                                     "SWITCH_DB", "FATIGUE_DB", "GAP_DB", "PHRASE_BARS",
                                                                     "RELAXED_MIN_SHARE", "RELAXED_LOCAL",
                                                                     "RELAXED_MIN_STRENGTH", "FLOOR_DB", "SEP_DB",
                                                                     "SEP_OK", "MAX_RUN_BARS", "LONG_DB",
                                                                     "BREAKDOWN_DRUMS_DB")},
                           "voice_quality": quality})


SOUND_MARGIN_DB = 1.5  # the chart's self-check is this much stricter than the validator (Vorbis coding of the stems)


def st_chart(c: Ctx) -> None:
    from audio_io import mono
    from chart import apply_relaxed, build_charts, rank
    from validate_track import SoundLevels
    an, g = _grid(c)
    vj = c.jload("voices.json")
    fj = c.jload("focus.json")
    ve, _ = _events(c)
    kinds = {k: v["kind"] for k, v in vj["voices"].items()}
    focus = fj["focus"]
    n_relaxed = apply_relaxed(ve, focus)
    for k, evs in ve.items():
        rank(evs, kinds[k], [f for f in focus if f["voice"] == k])
    sq = {k: v["sep_quality"] for k, v in vj["voices"].items()}
    au = _audio(c)
    lv = SoundLevels({k: mono(x) for k, x in au["voices"].items()}, mono(au["mix"]), au["rate"])
    del au
    stats: dict = {"relaxed_events": n_relaxed}
    charts, layouts = build_charts(ve, focus, kinds, an["sections"], g, an["duration_s"], sq,
                                   sound_check=lambda cj: lv.problem(cj, SOUND_MARGIN_DB), stats=stats)
    for d, n in stats["sound_check_removed"].items():
        if n:
            print(f"[chart] {d}: {n} cue(s) failed the audibility self-check and were removed", flush=True)
    c.jsave("charts.json", {
        "stats": stats,
        "charts": {d: [dict(cu.as_json(), score=round(cu.score, 3), ev_t=round(cu.ev.t, 4), stretch=cu.stretch,
                            natural=round(cu.natural, 3), kind=cu.ev.kind, dev_ms=round(cu.ev.dev_ms, 1),
                            h=None if not np.isfinite(cu.ev.height) else round(cu.ev.height, 2), s=round(cu.ev.strength, 3))
                       for cu in cues] for d, cues in charts.items()},
        "layouts": layouts})


def _stamp(c: Ctx) -> str:
    vd = c.cache / "voices"
    return json.dumps({p.name: [p.stat().st_size, int(p.stat().st_mtime)] for p in sorted(vd.glob("*.npy"))})


def folded_voices(vj: dict, fj: dict, ch: dict) -> list[str]:
    """Voices that never have the focus and have no cue on any chart: they are not written as voices but go
    into the backing (a voice the player never plays is only something to mute by mistake)."""
    used = {f["voice"] for f in fj["focus"]} | {cu["voice"] for cues in ch["charts"].values() for cu in cues}
    out = [k for k in vj["voices"] if k not in used]
    return out if len(out) < len(vj["voices"]) else out[:-1]  # the format needs one voice at least


def st_pack(c: Ctx) -> None:
    from pack import write_pack, write_stems
    an = c.jload("analysis.json")
    vj = c.jload("voices.json")
    ch = c.jload("charts.json")
    fj = c.jload("focus.json")
    folded = folded_voices(vj, fj, ch)
    keys = sorted((k for k in vj["voices"] if k not in folded),
                  key=lambda k: VOICE_ORDER.index(k) if k in VOICE_ORDER else len(VOICE_ORDER))
    voices = [{"key": k, "label": vj["voices"][k]["label"], "kind": CONTRACT_KIND.get(vj["voices"][k]["kind"], "pitched")}
              for k in keys]
    backing = [{"key": "backing"}]
    if _has_sep(c):  # the encoded stems of every voice as separated, kept in the cache for later re-charting
        va = _voice_audio(c)
        _m, _s, meta = _load_sep(c)
        write_stems(c.cache / "stem_src", [{"key": k, "audio": va[k]} for k in vj["voices"]],
                    [{"key": "backing", "audio": np.load(c.cache / "voices" / "backing.npy")}], meta["rate"], _stamp(c))
        del va
    src = _stem_src(c)
    if src is None:
        raise RuntimeError(f"{c.id}: no separated audio and no encoded stems to build the pack from")
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
                   "folded_into_backing": folded,
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
    write_pack(c.pack, tj_meta, voices, backing, src, folded)


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
    au = _audio(c)
    an = c.jload("analysis.json")
    tj = json.loads((c.pack / "track.json").read_text())
    miss = pick_miss(an, tj)
    write_previews(c.pack / "preview", au["mix"], au["voices"], tj["charts"]["normal"], tj["focus"], au["rate"], miss)
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


def nothing_to_play(fj: dict, n_bars: int) -> tuple[int, int]:
    """Bars with no focus between bar 16 and the last 8 bars: (bars judged, bars with nothing to play)."""
    lo, hi = 16, max(16, n_bars - 8)
    have = np.zeros(n_bars, bool)
    for f in fj["focus"]:
        have[f["bar_range"][0]:f["bar_range"][1]] = True
    return hi - lo, int((~have[lo:hi]).sum())


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
                     f" (drift {g['drift_ms_max_abs']:.0f} ms over {g.get('drift_windows_judged', '?')} of "
                     f"{g.get('drift_windows_total', '?')} 8-bar windows, conf {an['tempo_confidence']:.2f})")
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
        nb, nothing = nothing_to_play(fj, len(an["bar_edges"]) - 1)
        parts.append(f"nothing to play {nothing}/{nb} bars ({nothing / max(nb, 1):.0%}) from bar 16 to the last 8")
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
    line = " | ".join(parts) + (" | " + " ; ".join(f"WARNING {w}" for w in warn) if warn else "")
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


def verdict(err: str | None, warn: list[str], violations) -> str:
    """ok: imported, nothing to check. ok with warnings: imported and playable, something worth a listen.
    FAILED: not imported (an error) or the pack breaks the format (validator violations)."""
    if err or violations or any(w.startswith("validator") or w.startswith("no validation") for w in warn):
        return "FAILED"
    return "ok with warnings" if warn else "ok"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", nargs="*", help="audio files and/or folders of audio files (with --rechart: pack ids, "
                                             "or nothing for every pack under <out>/packs)")
    ap.add_argument("--id", help="pack id (default: artist_title from tags or file name); one input only")
    ap.add_argument("--out", default="/home/joe/rw-audio-work")
    ap.add_argument("--model", default="htdemucs", choices=("htdemucs", "htdemucs_ft", "htdemucs_6s"))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--from", dest="start", choices=STAGES, help="rerun this stage and every later one")
    g.add_argument("--only", choices=STAGES, help="run just this stage (earlier caches must exist)")
    g.add_argument("--rechart", action="store_true",
                   help="rerun focus, chart, pack, preview and validate of existing packs (the ids given, or all "
                        "under <out>/packs) from their cached analysis and encoded stems: no recording, no Demucs")
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
                         "1 GB each); its encoded stems stay in the cache, so --rechart and --from focus still work")
    a = ap.parse_args(argv)
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    if a.rechart:
        a.start = "focus"
        packs = Path(a.out) / "packs"
        ids = a.audio or sorted(p.name for p in packs.iterdir() if (p / "track.json").is_file()) if packs.is_dir() else a.audio
        jobs = [(None, i) for i in ids]
    else:
        if not a.audio:
            ap.error("give audio files or folders (or --rechart)")
        jobs = [(f, None) for f in inputs(a.audio)]
    if a.id and len(jobs) != 1:
        ap.error("--id needs exactly one input file")
    lines, rc, taken = [], 0, set()
    n_ok = n_warn = n_failed = 0
    for f, pid in jobs:
        c, err = None, None
        name = f.name if f is not None else pid
        t0 = time.time()
        try:
            if f is not None and not f.is_file():
                raise FileNotFoundError(f"{f} not found")
            if f is None and not (Path(a.out) / "packs" / pid / "track.json").is_file():
                raise FileNotFoundError(f"no pack {pid} under {Path(a.out) / 'packs'}")
            c = Ctx(f, a, pack_id=pid, taken=taken)
            taken.add(c.id)
            if a.skip_imported and _imported(c):
                lines.append(f"{c.id} | already imported (pack validated), skipped | ok")
                print(lines[-1], flush=True)
                n_ok += 1
                continue
            res = run_track(c, a)
            rc = max(rc, res["rc"])
            if a.prune_cache and res["rc"] == 0 and (c.cache / "stem_src" / ".made_from").is_file():
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
        line, warn = summary_line(c, f if f is not None else Path(name), err)
        nv = None
        if c is not None:
            try:
                nv = json.loads((c.pack / "report.json").read_text()).get("validation", {}).get("violations")
            except (OSError, ValueError):
                nv = None
        v = verdict(err, warn, nv)
        n_ok += v == "ok"
        n_warn += v == "ok with warnings"
        n_failed += v == "FAILED"
        if c is not None and c.renamed_from:
            line += f" | NOTE id {c.renamed_from} is taken by another recording: this one is {c.id}"
        lines.append(f"{line} | {time.time() - t0:.0f} s | {v}")
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    text = (f"# import_track.py {stamp}: {len(jobs)} track(s): {n_ok} ok, {n_warn} ok with warnings, {n_failed} FAILED\n"
            + "\n".join(lines) + "\n")
    print("\n" + text)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "batch_summary.txt").write_text(text)
    (out / f"batch_summary_{stamp}.txt").write_text(text)
    return rc


if __name__ == "__main__":
    sys.exit(main())
