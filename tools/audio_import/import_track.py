#!/usr/bin/env python3
"""Turn one finished recording into a track pack (docs/TRACK_PACK_FORMAT.md). No MIDI: everything from audio.

    /home/joe/.venvs/rw-audio/bin/python tools/audio_import/import_track.py "<audio file>" [--id ID]
        [--out /home/joe/rw-audio-work] [--model htdemucs] [--from STAGE | --only STAGE]

Stages, each cached under <out>/cache/<id>/ and skipped when its output exists (unless --from/--only reruns it):
    separate  Demucs on the whole file           -> sep_<model>/{mix,<stem>}.npy, meta.json
    analyse   tempo, grid, downbeat, sections    -> analysis.json
    voices    four voices + backing, pads        -> voices.json, voices/<key>.npy
    chart     events, ranking, easy/normal/hard  -> charts.json
    pack      stems/*.ogg + track.json           -> <out>/packs/<id>/
    preview   listening files                    -> <out>/packs/<id>/preview/
    validate  validate_track.py on the pack, then the report -> <out>/packs/<id>/report.{json,txt}
Heavy work runs on whatever OMP_NUM_THREADS says (use 3 and nice -n 10 on the shared laptop).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_io import mono, probe  # noqa: E402

STAGES = ("separate", "analyse", "voices", "chart", "pack", "preview", "validate")
VERSION = "audio_import 0.1"


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
    def __init__(self, a: argparse.Namespace):
        self.src = Path(a.audio).resolve()
        self.meta = guess_meta(self.src)
        self.id = a.id or self.meta["id"]
        self.out = Path(a.out)
        self.cache = self.out / "cache" / self.id
        self.pack = self.out / "packs" / self.id
        self.model = a.model
        self.sep_dir = self.cache / f"sep_{self.model}"
        self.timings: dict[str, float] = {}
        tf = self.cache / "timings.json"
        if tf.exists():
            self.timings = json.loads(tf.read_text())
        self.cache.mkdir(parents=True, exist_ok=True)

    def save_timings(self) -> None:
        (self.cache / "timings.json").write_text(json.dumps(self.timings, indent=1))

    def jload(self, name: str) -> dict:
        return json.loads((self.cache / name).read_text())

    def jsave(self, name: str, obj) -> None:
        (self.cache / name).write_text(json.dumps(obj, indent=1, default=_np))


def _np(o):
    if isinstance(o, (np.floating, np.integer)):
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
                         "bars": s["bar_end"] - s["bar_start"], "intensity_db": s["intensity_db"]})
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


def st_voices(c: Ctx) -> None:
    from chart import events
    from voices import LABELS, assign_pads, choose_voices, co_occurrence
    mix, stems, meta = _load_sep(c)
    rate = meta["rate"]
    an, g = _grid(c)
    ch = choose_voices(mix, stems, rate, an["stem_report"])
    vdir = c.cache / "voices"
    vdir.mkdir(exist_ok=True)
    strong = {}
    for k, v in ch["voices"].items():
        np.save(vdir / f"{k}.npy", v["audio"].astype(np.float32))
        evs = events(v["audio"], mix, rate, v["kind"], g)
        ss = np.array([e.strength for e in evs if e.audible])
        thr = np.percentile(ss, 50) if len(ss) else 0
        strong[k] = np.array([e.t for e in evs if e.audible and e.strength >= thr])
    np.save(vdir / "backing.npy", ch["backing"])
    co = co_occurrence(strong, g.beat_s)
    pads, why = assign_pads(list(ch["voices"]), co)
    rep = an["stem_report"]
    info = {k: {"pad": pads[k], "label": LABELS.get(k, k.title()), "from": v["from"], "op": v["op"], "kind": v["kind"],
                "sep_quality": sep_quality(v["from"][0], rep) if v["op"] == "stem" else 0.6}
            for k, v in ch["voices"].items()}
    c.jsave("voices.json", {"voices": info, "backing_from": ch["backing_from"], "notes": ch["notes"],
                            "pads": why})


def _voice_audio(c: Ctx) -> dict[str, np.ndarray]:
    vj = c.jload("voices.json")
    return {k: np.load(c.cache / "voices" / f"{k}.npy") for k in vj["voices"]}


def st_chart(c: Ctx) -> None:
    from chart import build_charts, events, rank
    mix, _stems, meta = _load_sep(c)
    rate = meta["rate"]
    an, g = _grid(c)
    vj = c.jload("voices.json")
    va = _voice_audio(c)
    kinds = {k: v["kind"] for k, v in vj["voices"].items()}
    pads = {k: v["pad"] for k, v in vj["voices"].items()}
    ve = {}
    for k, x in va.items():
        evs = events(x, mix, rate, kinds[k], g)
        rank(evs, kinds[k], an["sections"])
        ve[k] = evs
    charts = build_charts(ve, pads, kinds, an["sections"], g, an["duration_s"],
                          {k: v["sep_quality"] for k, v in vj["voices"].items()})
    out = {"charts": {d: [dict(cu.as_json(), voice=cu.voice, score=round(cu.score, 3), ev_t=round(cu.ev.t, 4),
                               natural=round(cu.natural, 3), kind=cu.ev.kind, dev_ms=round(cu.ev.dev_ms, 1))
                          for cu in cues] for d, cues in charts.items()},
           "events": {k: [{"t": round(e.t, 4), "s": round(e.strength, 3), "rel": round(e.rel_db, 1),
                           "own": round(e.own_db, 1), "len": round(e.length, 3), "kind": e.kind, "pos": e.pos,
                           "dev": round(e.dev_ms, 1), "score": round(e.score, 3), "aud": e.audible}
                          for e in evs] for k, evs in ve.items()}}
    c.jsave("charts.json", out)


def st_pack(c: Ctx) -> None:
    from pack import write_pack
    _mix, _stems, meta = _load_sep(c)
    rate = meta["rate"]
    an = c.jload("analysis.json")
    vj = c.jload("voices.json")
    ch = c.jload("charts.json")
    va = _voice_audio(c)
    voices = [{"key": k, "label": v["label"], "pad": v["pad"], "audio": va[k]} for k, v in vj["voices"].items()]
    backing = [{"key": "backing", "audio": np.load(c.cache / "voices" / "backing.npy")}]
    clean = {d: [{k: cu[k] for k in ("t", "pad", "dur", "conf")} for cu in cues] for d, cues in ch["charts"].items()}
    m = c.meta
    tj_meta = {
        "id": c.id, "title": m["title"], "artist": m["artist"],
        "tempo": {"bpm": round(an["grid"]["bpm"], 4), "first_downbeat_s": round(an["first_downbeat_s"], 4),
                  "beats_per_bar": 4, "confidence": an["tempo_confidence"]},
        "sections": [{k: s[k] for k in ("id", "role", "start_s", "end_s")} for s in an["sections"]],
        "charts": {d: clean[d] for d in ("easy", "normal", "hard")},
        "source": {"input_file": c.src.name, "input_path": str(c.src), "input": {k: m["probe"][k] for k in ("codec", "rate", "channels", "duration")},
                   "tool": VERSION, "separation": {"model": c.model, "residual_db": an["stem_report"]["residual_db"]},
                   "voices": {k: {kk: v[kk] for kk in ("from", "op", "kind", "sep_quality")} for k, v in vj["voices"].items()},
                   "backing_from": vj["backing_from"], "voice_notes": vj["notes"], "pad_choice": vj["pads"],
                   "tempo_detail": {"constant": an["constant_tempo"], "beat_source": an["beat_source"],
                                    "residual_ms_rms": an["grid"]["residual_ms_rms"],
                                    "drift_ms_max_abs": an["grid"]["drift_ms_max_abs"],
                                    "candidates": an["tempo_candidates"]["candidates"],
                                    "downbeat_confidence": an["downbeat"]["confidence"]},
                   "sections_detail": [{k: s[k] for k in ("id", "bars", "intensity_db")} for s in an["sections"]],
                   "chart_note": "cue times are the detected attack in the voice's own stem, or the 16th grid line "
                                 "when the attack is within 6 ms of it; conf blends separation quality, attack "
                                 "strength and how loud the voice is against the whole track there"}}
    write_pack(c.pack, tj_meta, voices, backing, rate)


def pick_miss(an: dict, cues: list[dict], vj: dict) -> dict:
    """A 30 s stretch of the loudest drop, with the bass (else the busiest voice) dropped for 4 bars from a cue
    in the middle until its first cue after those bars, like a run of missed presses."""
    drops = [s for s in an["sections"] if s["role"] == "drop"] or an["sections"]
    s = max(drops, key=lambda s: s["intensity_db"] + 0.01 * (s["end_s"] - s["start_s"]))
    start = s["start_s"]
    end = min(start + 30.0, an["duration_s"] - 0.5)
    key = "bass" if "bass" in vj["voices"] else max(vj["voices"], key=lambda k: sum(1 for c in cues if c["pad"] == vj["voices"][k]["pad"]))
    pad = vj["voices"][key]["pad"]
    mine = [c for c in cues if c["pad"] == pad and start + 8 <= c["t"] < end]
    bar = 4 * 60.0 / an["grid"]["bpm"]
    m0 = mine[0]["t"] if mine else start + 8
    after = [c["t"] for c in cues if c["pad"] == pad and c["t"] >= m0 + 4 * bar]
    m1 = after[0] if after else min(end - 1, m0 + 4 * bar)
    return {"key": key, "start_s": start, "end_s": end, "mute_from_s": m0, "mute_to_s": min(m1, end - 0.5)}


def st_preview(c: Ctx) -> None:
    from pack import write_previews
    mix, _stems, meta = _load_sep(c)
    an = c.jload("analysis.json")
    vj = c.jload("voices.json")
    tj = json.loads((c.pack / "track.json").read_text())
    va = _voice_audio(c)
    voices = [{"key": k, "pad": v["pad"], "audio": va[k]} for k, v in vj["voices"].items()]
    miss = pick_miss(an, tj["charts"]["normal"], vj)
    write_previews(c.pack / "preview", mix, voices, tj["charts"]["normal"], meta["rate"], miss)
    c.jsave("miss.json", miss)


def st_validate(c: Ctx) -> int:
    import report
    from validate_track import validate
    r, stats = validate(c.pack)
    for n in r.notes:
        print(n)
    for e in r.errors[:50]:
        print("VIOLATION:", e)
    print(f"{'FAIL' if r.errors else 'OK'}: {len(r.errors)} violation(s)")
    report.write(c, stats, r)
    return 1 if r.errors else 0


FUNCS = {"separate": st_separate, "analyse": st_analyse, "voices": st_voices, "chart": st_chart,
         "pack": st_pack, "preview": st_preview, "validate": st_validate}
OUTPUTS = {"separate": lambda c: c.sep_dir / "meta.json", "analyse": lambda c: c.cache / "analysis.json",
           "voices": lambda c: c.cache / "voices.json", "chart": lambda c: c.cache / "charts.json",
           "pack": lambda c: c.pack / "track.json", "preview": lambda c: c.pack / "preview" / "mix_clicks_normal.ogg",
           "validate": lambda c: None}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--id", help="pack id (default: artist_title from tags or file name)")
    ap.add_argument("--out", default="/home/joe/rw-audio-work")
    ap.add_argument("--model", default="htdemucs", choices=("htdemucs", "htdemucs_ft", "htdemucs_6s"))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--from", dest="start", choices=STAGES, help="rerun this stage and every later one")
    g.add_argument("--only", choices=STAGES, help="run just this stage (earlier caches must exist)")
    a = ap.parse_args(argv)
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    c = Ctx(a)
    print(f"track {c.src.name} -> id {c.id}\n cache {c.cache}\n pack  {c.pack}")
    todo = [a.only] if a.only else STAGES[STAGES.index(a.start):] if a.start else STAGES
    rc = 0
    for st in STAGES:
        rerun = st in todo and (a.only or a.start)
        out = OUTPUTS[st](c)
        if st not in todo or (out is not None and out.exists() and not rerun and st != "validate"):
            if st in todo:
                print(f"[{st}] cached")
            continue
        if st == "separate" and rerun and (c.sep_dir / "meta.json").exists():
            (c.sep_dir / "meta.json").unlink()
        t0 = time.time()
        print(f"[{st}] running", flush=True)
        res = FUNCS[st](c)
        c.timings[st] = round(time.time() - t0, 1)
        c.save_timings()
        print(f"[{st}] {c.timings[st]} s", flush=True)
        if st == "validate":
            rc = res
    return rc


if __name__ == "__main__":
    sys.exit(main())
