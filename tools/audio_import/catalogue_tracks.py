#!/usr/bin/env python3
"""A catalogue of recordings for the game's track mode: what each one is, and what it is like.

    python tools/audio_import/catalogue_tracks.py <folder or files ...> [--packs DIR] [--out content/music/tracks]

For every recording: its tags (artist, title, album, year), length, and a quick look at the whole mix that
needs no separation: tempo, loudness, how bass-heavy and how bright it is, how busy, and a rough map of where
the loud and quiet parts are. For a recording that has already been imported (a pack exists under --packs) the
measured facts of the import are added: tempo, bar-accurate sections, which instrument is played when, and how
many cues each chart has.

It writes metadata only, never audio:
    <out>/catalogue.json     every recording, one entry each
    <out>/<id>.json          one file per imported recording, in full
    docs/MUSIC_TRACKS.md     the same as tables, for reading

The quick look takes a few seconds per recording and is cached, so rerunning after adding recordings or
importing some is cheap. numpy and ffmpeg only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audio_io import decode  # noqa: E402
from import_track import AUDIO_EXT, guess_meta  # noqa: E402

FORMAT = "rhythm_warfare.track_catalogue.v1"
VERSION = "catalogue_tracks 0.4"
RATE = 22050
N_FFT = 1024
HOP = 256
BPM_LO, BPM_HI, BPM_STEP = 120.0, 200.0, 0.02
REPO = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------- the quick look

def _spectrogram(y: np.ndarray) -> np.ndarray:
    """Magnitude spectrogram, frames x bins, float32."""
    n = 1 + max(0, (len(y) - N_FFT) // HOP)
    win = np.hanning(N_FFT).astype(np.float32)
    out = np.empty((n, N_FFT // 2 + 1), dtype=np.float32)
    step = 4096
    for a in range(0, n, step):
        b = min(n, a + step)
        idx = (np.arange(a, b)[:, None] * HOP) + np.arange(N_FFT)[None, :]
        out[a:b] = np.abs(np.fft.rfft(y[idx] * win, axis=1)).astype(np.float32)
    return out


def _tempo(env: np.ndarray) -> dict:
    """One constant tempo from the onset envelope: the beat period whose multiples line up best with the
    envelope's own repetition (32 beats deep, so two tempos 0.05 BPM apart are told apart)."""
    x = env - env.mean()
    n = len(x)
    size = 1 << int(np.ceil(np.log2(2 * n)))
    spec = np.fft.rfft(x, size)
    acf = np.fft.irfft(spec * np.conj(spec))[:n]
    acf = acf / np.maximum(1, n - np.arange(n))  # unbiased: long lags are not penalised
    acf = acf / max(acf[0], 1e-12)
    hop_s = HOP / RATE
    bpms = np.arange(BPM_LO, BPM_HI + 1e-9, BPM_STEP)
    lags = np.arange(n, dtype=np.float64)
    score = np.zeros(len(bpms))
    beats = np.arange(1, 33)
    for i, bpm in enumerate(bpms):
        at = beats * (60.0 / bpm / hop_s)
        at = at[at < n - 1]
        score[i] = np.interp(at, lags, acf).mean() if len(at) else 0.0
    best = int(np.argmax(score))
    spread = float(score.std()) or 1e-9
    z = float((score[best] - score.mean()) / spread)
    # the best tempo more than 3 BPM away, to say how clear the winner is
    far = np.abs(bpms - bpms[best]) > 3.0
    second = float(score[far].max()) if far.any() else 0.0
    return {"bpm": round(float(bpms[best]), 2), "clarity": round(z, 1),
            "runner_up_bpm": round(float(bpms[far][int(np.argmax(score[far]))]), 2) if far.any() else None,
            "margin": round(float(score[best] - second), 3)}


def _rough_sections(block_db: np.ndarray, block_s: float, duration: float) -> list[dict]:
    """Loud, middling and quiet runs of 8-bar blocks, named by where they fall (opening, lift, loud, quieter,
    ending). Rough: blocks are counted from the start of the file, not from a detected bar line, and "loud" is
    not the same as a drop: a busy vocal passage over bass reads as loud. An import measures the real sections."""
    ref = float(np.percentile(block_db, 85))
    level = np.where(block_db >= ref - 2.5, 2, np.where(block_db <= ref - 9.0, 0, 1))
    runs = []
    a = 0
    for i in range(1, len(level) + 1):
        if i == len(level) or level[i] != level[a]:
            runs.append((a, i, int(level[a])))
            a = i
    highs = [k for k, r in enumerate(runs) if r[2] == 2]
    out = []
    for k, (a, b, lv) in enumerate(runs):
        if lv == 2:
            role = "loud"
        elif not highs or k < highs[0]:
            role = "lift" if (lv == 1 and highs and k == highs[0] - 1 and b - a <= 2) else "opening"
        elif k > highs[-1]:
            role = "ending"
        else:
            role = "quieter"
        out.append({"role": role, "start_s": round(a * block_s, 1), "end_s": round(min(duration, b * block_s), 1),
                    "bars": (b - a) * 8, "level_db": round(float(np.mean(block_db[a:b]) - ref), 1)})
    return out


def quick_look(path: Path) -> dict:
    x, _ = decode(path, RATE, 1)
    y = x[:, 0]
    duration = len(y) / RATE
    S = _spectrogram(y)
    logS = np.log1p(100.0 * S)
    env = np.maximum(0.0, np.diff(logS, axis=0)).sum(axis=1)
    env = np.concatenate([[0.0], env]).astype(np.float64)
    tempo = _tempo(env)
    bpm = tempo["bpm"]

    freqs = np.fft.rfftfreq(N_FFT, 1.0 / RATE)
    power = (S.astype(np.float64) ** 2)
    total = power.sum()
    frame_e = power.sum(axis=1)
    loud = frame_e > np.percentile(frame_e, 30)
    centroid = (S[loud] * freqs).sum(axis=1) / np.maximum(S[loud].sum(axis=1), 1e-9)

    # events: peaks of the envelope that stand out from their surroundings
    med = np.median(env)
    mad = np.median(np.abs(env - med)) or 1e-9
    thr = med + 3.0 * mad
    gap = max(1, int(0.06 * RATE / HOP))
    peaks, last = 0, -gap
    for i in range(1, len(env) - 1):
        if env[i] > thr and env[i] >= env[i - 1] and env[i] > env[i + 1] and i - last >= gap:
            peaks += 1
            last = i

    bar_s = 240.0 / bpm
    block_s = 8 * bar_s
    nblk = max(1, int(np.ceil(duration / block_s)))
    block_db = np.empty(nblk)
    low_db = np.empty(nblk)
    hit_db = np.empty(nblk)
    low_power = power[:, freqs < 120.0].sum(axis=1)
    fps = RATE / HOP
    for i in range(nblk):
        seg = y[int(i * block_s * RATE): int(min(duration, (i + 1) * block_s) * RATE)]
        block_db[i] = 10 * np.log10(np.mean(seg.astype(np.float64) ** 2) + 1e-12) if len(seg) else -120.0
        a = min(int(i * block_s * fps), len(env) - 1)  # the last block may be a sliver past the last frame
        b = min(len(env), max(a + 1, int(min(duration, (i + 1) * block_s) * fps)))
        low_db[i] = 10 * np.log10(np.mean(low_power[a:b]) + 1e-12)
        hit_db[i] = 20 * np.log10(np.mean(env[a:b]) + 1e-9)
    # drive: how hard the low end and the hits are going together. A loud vocal or pad passage is loud in the
    # mix but has little drive; a drop has both.
    drive = 0.5 * (np.clip(low_db - np.percentile(low_db, 85), -30, 6)
                   + np.clip(hit_db - np.percentile(hit_db, 85), -30, 6))
    sections = _rough_sections(drive, block_s, duration)
    ref = float(np.percentile(block_db, 85))
    drops = [s for s in sections if s["role"] == "loud"]
    rms = float(np.sqrt(np.mean(y.astype(np.float64) ** 2)))
    return {
        "bpm": bpm, "bpm_clarity": tempo["clarity"], "bpm_runner_up": tempo["runner_up_bpm"],
        "ratio_to_174": round(bpm / 174.0, 4),
        "loudness_db": round(20 * np.log10(rms + 1e-12), 1),
        "low_share": round(float(power[:, freqs < 120.0].sum() / max(total, 1e-12)), 3),
        "brightness_hz": int(round(float(np.median(centroid)))),
        "events_per_s": round(peaks / max(duration, 1e-9), 2),
        "dynamic_db": round(float(np.percentile(block_db, 90) - np.percentile(block_db, 10)), 1),
        "loud_share": round(float(sum(s["end_s"] - s["start_s"] for s in drops) / max(duration, 1e-9)), 2),
        "first_drop_s": drops[0]["start_s"] if drops else None,
        "drops": len(drops),
        "block_s": round(block_s, 2),
        "blocks_db": [round(float(v - ref), 1) for v in block_db],
        "blocks_drive_db": [round(float(v - np.percentile(drive, 85)), 1) for v in drive],
        "rough_sections": sections,
    }


# ---------------------------------------------------------------- what an import measured

def import_facts(pack: Path) -> dict | None:
    tj = pack / "track.json"
    if not tj.exists():
        return None
    t = json.loads(tj.read_text())
    rj = pack / "report.json"
    r = json.loads(rj.read_text()) if rj.exists() else {}
    bpm = float(t["tempo"]["bpm"])
    bar_s = 240.0 / bpm
    d0 = float(t["tempo"].get("first_downbeat_s", 0.0))

    def bar(s: float) -> int:
        return int(round((s - d0) / bar_s))

    rsec = {s["id"]: s for s in r.get("sections", [])}
    sections = [{"id": s["id"], "role": s["role"], "start_s": round(s["start_s"], 2), "end_s": round(s["end_s"], 2),
                 "bar_from": bar(s["start_s"]), "bar_to": bar(s["end_s"]),
                 "intensity_db": rsec.get(s["id"], {}).get("intensity_db")} for s in t.get("sections", [])]
    rstr = r.get("focus", {}).get("stretches", [])
    focus = []
    for i, f in enumerate(t.get("focus", [])):
        extra = rstr[i] if i < len(rstr) and rstr[i].get("voice") == f["voice"] else {}
        focus.append({"voice": f["voice"], "start_s": round(f["start_s"], 2), "end_s": round(f["end_s"], 2),
                      "bar_from": bar(f["start_s"]), "bar_to": bar(f["end_s"]),
                      "sections": extra.get("sections"), "share": extra.get("share"),
                      "runner_up": extra.get("runner_up")})
    charts = {}
    for name, cues in t.get("charts", {}).items():
        rc = r.get("charts", {}).get(name, {})
        per_voice: dict[str, int] = {}
        for c in cues:
            per_voice[c["voice"]] = per_voice.get(c["voice"], 0) + 1
        charts[name] = {"cues": len(cues), "holds": sum(1 for c in cues if c.get("dur", 0) > 0),
                        "per_s": rc.get("per_s"), "per_beat_of_focus": rc.get("per_beat_of_focus"),
                        "by_voice": per_voice}
    val = r.get("validation", {})
    tdet = t.get("source", {}).get("tempo_detail", {})
    played = {}
    for f in focus:
        played[f["voice"]] = played.get(f["voice"], 0.0) + (f["end_s"] - f["start_s"])
    return {
        "format": t["format"], "tool": t.get("source", {}).get("tool"),
        "duration_s": t["duration_s"],
        "tempo": {"bpm": bpm, "first_downbeat_s": d0, "constant": tdet.get("constant"),
                  "drift_ms_max": tdet.get("drift_ms_max_abs"), "confidence": t["tempo"].get("confidence"),
                  "ratio_to_174": round(bpm / 174.0, 5)},
        "voices": [{"key": v["key"], "label": v["label"], "kind": v.get("kind"),
                    "separation": r.get("separation", {}).get("words", {}).get(v["key"]),
                    "focus_share_of_track": round(played.get(v["key"], 0.0) / t["duration_s"], 3)}
                   for v in t["voices"]],
        "sections": sections,
        "focus": focus,
        "focus_timeline_bars": r.get("focus", {}).get("timeline"),
        "nothing_to_play": [{"start_s": round(g["start_s"], 2), "end_s": round(g["end_s"], 2), "bars": g.get("bars"),
                             "why": g.get("why")} for g in r.get("focus", {}).get("gaps", [])],
        "charts": charts, "default_chart": t.get("default_chart"),
        "validation": {"violations": val.get("violations"), "stems_sum_error_db": val.get("sum_error_db")},
    }


# ---------------------------------------------------------------- catalogue

def _files(inputs: list[str]) -> list[Path]:
    out = []
    for i in inputs:
        p = Path(i)
        if p.is_dir():
            out += sorted(q for q in p.iterdir() if q.suffix.lower() in AUDIO_EXT)
        elif p.suffix.lower() in AUDIO_EXT:
            out.append(p)
    return out


def _year(tags: dict) -> int | None:
    for k in ("date", "year", "originaldate"):
        v = str(tags.get(k, ""))[:4]
        if v.isdigit():
            return int(v)
    return None


def _mmss(s: float | None) -> str:
    return "-" if s is None else f"{int(s // 60)}:{int(s % 60):02d}"


def build(args: argparse.Namespace) -> int:
    packs = Path(args.packs)
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    files = _files(args.inputs)
    tracks, seen, failed = [], {}, []
    for n, f in enumerate(files, 1):
        try:
            meta = guess_meta(f)
        except Exception as e:  # unreadable file: say so and go on
            failed.append({"file": f.name, "error": str(e).strip()[:200]})
            print(f"[{n}/{len(files)}] {f.name}: cannot read ({e})", flush=True)
            continue
        tid = meta["id"]
        seen[tid] = seen.get(tid, 0) + 1
        if seen[tid] > 1:
            tid = f"{tid}_{seen[tid]}"
        info, tags = meta["probe"], meta["probe"]["tags"]
        st = f.stat()
        cf = cache / f"{tid}.json"
        look = None
        if cf.exists():
            c = json.loads(cf.read_text())
            if c.get("size") == st.st_size and c.get("mtime") == int(st.st_mtime) and c.get("tool") == VERSION:
                look = c["look"]
        if look is None:
            try:
                look = quick_look(f)
                cf.write_text(json.dumps({"size": st.st_size, "mtime": int(st.st_mtime), "tool": VERSION, "look": look}))
            except Exception as e:
                failed.append({"file": f.name, "error": str(e).strip()[:200]})
                print(f"[{n}/{len(files)}] {f.name}: quick look failed ({e})", flush=True)
                continue
        facts = import_facts(packs / tid)
        entry = {
            "id": tid, "file": f.name, "artist": meta["artist"], "title": meta["title"],
            "album": tags.get("album"), "year": _year(tags), "genre": tags.get("genre"),
            "codec": info["codec"], "duration_s": round(info["duration"], 2),
            "quick": look, "imported": facts is not None,
        }
        if facts:
            entry["import"] = {"bpm": facts["tempo"]["bpm"], "tempo_constant": facts["tempo"]["constant"],
                               "sections": [f"{s['role']} {s['bar_from']}-{s['bar_to']}" for s in facts["sections"]],
                               "focus_share_of_track": {v["key"]: v["focus_share_of_track"] for v in facts["voices"]},
                               "cues": {k: v["cues"] for k, v in facts["charts"].items()},
                               "detail": f"{tid}.json"}
            (out / f"{tid}.json").write_text(json.dumps(
                {"format": "rhythm_warfare.track_metadata.v1", "id": tid, "file": f.name, "artist": meta["artist"],
                 "title": meta["title"], "album": tags.get("album"), "year": _year(tags), "genre": tags.get("genre"),
                 **facts, "quick": look}, indent=1) + "\n")
        tracks.append(entry)
        print(f"[{n}/{len(files)}] {tid}: {look['bpm']} BPM, {_mmss(info['duration'])}"
              f"{', imported' if facts else ''}", flush=True)
    tracks.sort(key=lambda e: e["id"])
    cat = {
        "format": FORMAT, "tool": VERSION, "generated": datetime.date.today().isoformat(),
        "about": ("Recordings available to the game's track mode (docs/TRACK_PACK_FORMAT.md). Metadata only: the "
                  "audio is other people's music and is never in this repository. 'quick' is a few seconds' look at "
                  "the whole mix (tempo, loudness, low_share = share of energy below 120 Hz, brightness, "
                  "events_per_s, blocks_db = level of each 8-bar block relative to the track's loud level, "
                  "blocks_drive_db = how hard the low end and the hits are going in each block, "
                  "rough_sections from that drive); it is approximate and its sections are not bar-aligned. 'import' is present "
                  "once tools/audio_import/import_track.py has been run on the recording, and is measured."),
        "source_folders": sorted({str(Path(i).resolve().name) for i in args.inputs if Path(i).is_dir()}),
        "packs_live_at": str(packs),
        "counts": {"recordings": len(tracks), "imported": sum(1 for e in tracks if e["imported"]),
                   "unreadable": len(failed)},
        "unreadable": failed,
        "tracks": tracks,
    }
    (out / "catalogue.json").write_text(json.dumps(cat, indent=1, allow_nan=False) + "\n")
    if args.doc:
        Path(args.doc).write_text(_doc(cat, out))
    print(f"{len(tracks)} recordings, {cat['counts']['imported']} imported, {len(failed)} unreadable -> {out}")
    return 0


def _doc(cat: dict, out: Path) -> str:
    try:
        rel = out.resolve().relative_to(REPO)
    except ValueError:
        rel = out
    L = ["# Recordings for track mode", "",
         f"Generated by `tools/audio_import/catalogue_tracks.py` on {cat['generated']}; do not edit by hand. "
         f"The same data, in full, is in `{rel}/catalogue.json` (and one `{rel}/<id>.json` per imported recording).",
         "",
         "Metadata only. The recordings are other people's music and are never in this repository: the files "
         f"are in the owner's `{', '.join(cat['source_folders']) or 'music'}` folder and imported packs are in "
         f"`{cat['packs_live_at']}` on the owner's laptop. How a recording becomes playable: "
         "`tools/audio_import/README.md`. What a pack is: `docs/TRACK_PACK_FORMAT.md`.", "",
         f"{cat['counts']['recordings']} recordings, {cat['counts']['imported']} imported.", "",
         "## All recordings", "",
         "The numbers here come from a quick look at the whole mix and are approximate: BPM (and how it sits "
         "against the game's 174), where the first loud part starts, how many loud parts there are and what "
         "share of the track they fill, low = share of energy below 120 Hz (how bass-heavy), bright = spectral "
         "centre in Hz, busy = sound events per second, range = loud blocks minus quiet blocks in dB.", "",
         "| id | artist | title | year | length | BPM | first loud | loud parts | loud share | low | bright | busy | range | imported |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for e in cat["tracks"]:
        q = e["quick"]
        L.append(f"| `{e['id']}` | {e['artist']} | {e['title']} | {e['year'] or ''} | {_mmss(e['duration_s'])} | "
                 f"{q['bpm']:.2f} | {_mmss(q['first_drop_s'])} | {q['drops']} | {q['loud_share']:.2f} | "
                 f"{q['low_share']:.2f} | {q['brightness_hz']} | {q['events_per_s']:.1f} | {q['dynamic_db']:.0f} | "
                 f"{'yes' if e['imported'] else ''} |")
    if cat["unreadable"]:
        L += ["", "Could not be read: " + ", ".join(f"`{u['file']}`" for u in cat["unreadable"]) + "."]
    L += ["", "## Rough shape of each recording", "",
          "Loud, middling and quiet runs of 8-bar blocks counted from the start of the file (not bar-aligned; an "
          "import replaces this with measured sections). Times are minutes:seconds.", ""]
    for e in cat["tracks"]:
        parts = [f"{s['role']} {_mmss(s['start_s'])}-{_mmss(s['end_s'])}" for s in e["quick"]["rough_sections"]]
        L.append(f"- `{e['id']}`: " + ", ".join(parts))
    done = [e for e in cat["tracks"] if e["imported"]]
    if done:
        L += ["", "## Imported recordings", ""]
    for e in done:
        d = json.loads((out / f"{e['id']}.json").read_text())
        L += [f"### {e['artist']}: {e['title']} (`{e['id']}`)", "",
              f"{d['tempo']['bpm']:.4f} BPM ({d['tempo']['ratio_to_174']:.4f} x 174), "
              f"{'constant' if d['tempo']['constant'] else 'NOT constant'}; {_mmss(d['duration_s'])}; "
              f"cues " + ", ".join(f"{k} {v['cues']}" for k, v in d["charts"].items()) +
              f"; default chart `{d['default_chart']}`.", "",
              "| section | role | from | to | bars | level dB |", "| --- | --- | --- | --- | --- | --- |"]
        for s in d["sections"]:
            L.append(f"| {s['id']} | {s['role']} | {_mmss(s['start_s'])} | {_mmss(s['end_s'])} | "
                     f"{s['bar_from']}-{s['bar_to']} | {s['intensity_db'] if s['intensity_db'] is not None else ''} |")
        L += ["", "Instrument the player plays (the focus), in order: " +
              ", ".join(f"{f['voice']} bars {f['bar_from']}-{f['bar_to']}" for f in d["focus"]) + ".", "",
              "Share of the track each instrument is played for: " +
              ", ".join(f"{v['label']} {v['focus_share_of_track']:.0%}" for v in d["voices"]) + ".", ""]
    return "\n".join(L).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("inputs", nargs="+", help="folders and/or audio files")
    ap.add_argument("--packs", default="/home/joe/rw-audio-work/packs", help="where imported packs live")
    ap.add_argument("--cache", default="/home/joe/rw-audio-work/cache/_catalogue", help="quick-look cache")
    ap.add_argument("--out", default=str(REPO / "content" / "music" / "tracks"))
    ap.add_argument("--doc", default=str(REPO / "docs" / "MUSIC_TRACKS.md"), help="'' to skip the table")
    return build(ap.parse_args())


if __name__ == "__main__":
    sys.exit(main())
