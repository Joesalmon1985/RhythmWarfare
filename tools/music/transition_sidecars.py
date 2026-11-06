#!/usr/bin/env python3
"""Transition sidecars and the first-drop sheet (docs/parallel-development/MUSIC_TRANSITIONS.md sections 3.2 to 3.5).

    PY=C:/Users/joesa/rw-audio-work/venv/Scripts/python.exe
    $PY tools/music/transition_sidecars.py generate            # sidecars + docs/music/FIRST_DROPS.{md,csv}; a rerun changes nothing
    $PY tools/music/transition_sidecars.py apply [--csv FILE]  # the owner's corrected sheet back into the sidecars
    $PY tools/music/transition_sidecars.py check               # validate every sidecar (exit 1 on any error)

Reads, for each track: the pack's `track.json` (tempo, grid, sections; packs live in $RW_AUDIO_WORK/packs, read only) and the committed
`content/music/tracks/<id>.json` (title, artist, drift; also the fallback when a pack is missing). Writes `content/music/transitions/<id>.json`.

Detected versus owner values: `origin` in a sidecar says, per field, "detected" (the tool's, recomputed on every run from the pack) or "owner" (typed or
confirmed on the sheet; never overwritten by the tool). Fields the tool cannot detect (downbeat_offset_beats, mix_in_bar, mix_out_bar, intro_start_s,
no_blend, linger, note) are never touched by `generate`.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import io
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORMAT = "rhythm_warfare.transition.v1"
SIDECAR_DIR = ROOT / "content" / "music" / "transitions"
TRACKS_DIR = ROOT / "content" / "music" / "tracks"
SHEET_MD = ROOT / "docs" / "music" / "FIRST_DROPS.md"
SHEET_CSV = ROOT / "docs" / "music" / "FIRST_DROPS.csv"
DEFAULT_PACKS = Path(os.environ.get("RW_AUDIO_WORK", "C:/Users/joesa/rw-audio-work")) / "packs"

BEATS_PER_BAR = 4
LEAD_IN_BARS = 16          # RunTrackPlan.DEFAULTS.lead_in_bars
MIN_LEAD_IN = 5            # lead ruling 7
GRID_DRIFT_MS = 20.0       # section 3.5: grid_ok needs drift_ms_max_abs <= 20
AGREE_BEATS = 0.25         # section 3.3
SNAP_LARGE_BEATS = 0.25

# Section 3.2's keys in file order, then the keys this tool adds (see the report: first_drop_bar, first_drop_snap_ms, origin).
KEYS_3_2 = ["format", "track", "first_drop_s", "second_drop_s", "downbeat_offset_beats", "intro_start_s", "outro_start_s", "mix_in_bar", "mix_out_bar",
            "no_blend", "linger", "checked", "note"]
KEYS_EXTRA = ["first_drop_bar", "first_drop_snap_ms", "origin"]
KEYS = KEYS_3_2 + KEYS_EXTRA
DETECTABLE = ["first_drop_s", "second_drop_s", "outro_start_s"]   # fields with an "origin" entry
ORIGINS = ("detected", "owner")

CSV_COLUMNS = ["track", "title", "artist", "bpm", "first_downbeat_s", "beat_ms", "detected_drop_s", "detected_drop_mmss", "detected_drop_bar", "lead_in_bars",
               "snap_ms", "snap_beats", "drift_ms", "drop_s", "origin", "flags", "owner_drop", "owner_offset_beats", "owner_no_blend", "owner_note"]
OWNER_COLUMNS = ["owner_drop", "owner_offset_beats", "owner_no_blend", "owner_note"]


# ---------------------------------------------------------------------------------------------------------------- the grid

def r4(x: float | None) -> float | None:
    return None if x is None else round(float(x), 4)


def snap(time_s: float, first_downbeat_s: float, bpm: float, offset_beats: int = 0) -> dict:
    """Section 3.3. The nearest bar line (never before bar 0) of the grid fd' + n * bar, and how far the time is from it.

    Returns {bar, time_s, err_s, err_beats, verdict, offset}; verdict "agrees" (|e| <= 0.25 beat), "phase_suspect" (within 0.25 of a whole number of beats,
    offset = that number, the tool proposes downbeat_offset_beats) or "grid_suspect"."""
    beat = 60.0 / bpm
    bar = beat * BEATS_PER_BAR
    fd = first_downbeat_s + offset_beats * beat
    if fd < 0:
        fd += bar
    if round((time_s - fd) / bar) < 0:  # the drop is before the first downbeat (a drop section that starts the track): bar 0, nothing to snap to
        return {"bar": 0, "time_s": time_s, "err_s": 0.0, "err_beats": 0.0, "verdict": "agrees", "offset": 0, "before_grid": True}
    bar_n = int(round((time_s - fd) / bar))
    snapped = fd + bar_n * bar
    err_s = time_s - snapped
    eb = err_s / beat
    k = int(round(eb))
    if abs(eb) <= AGREE_BEATS:
        verdict, off = "agrees", 0
    elif abs(eb - k) <= AGREE_BEATS:
        verdict, off = "phase_suspect", k
    else:
        verdict, off = "grid_suspect", 0
    return {"bar": bar_n, "time_s": snapped, "err_s": err_s, "err_beats": eb, "verdict": verdict, "offset": off}


def mmss(t: float | None) -> str:
    if t is None:
        return ""
    m = int(t // 60)
    return "%d:%06.3f" % (m, t - 60 * m)


def lead_in_bars(drop_bar: int | None, mix_in_bar: int | None = None) -> int | None:
    """Bars from the scene's entry bar to the first drop with the default `drop1` entry (entry = drop bar - 16, not below 0), or a sidecar mix_in_bar."""
    if drop_bar is None:
        return None
    if mix_in_bar is not None:
        return max(drop_bar - mix_in_bar, 0)
    return min(LEAD_IN_BARS, drop_bar)


def grid_ok(sidecar: dict, drift_ms_max: float, bpm: float) -> bool:
    """Section 3.5: drift <= 20 ms and the sidecar's snap verdict is not "grid suspect"."""
    if drift_ms_max > GRID_DRIFT_MS:
        return False
    if sidecar.get("first_drop_snap_ms") is None:
        return True
    eb = sidecar["first_drop_snap_ms"] / 1000.0 / (60.0 / bpm)
    return abs(eb - round(eb)) <= AGREE_BEATS  # "agrees" or "phase suspect"; only "grid suspect" distrusts the grid


# ---------------------------------------------------------------------------------------------------------------- facts of a track

def read_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def track_facts(track_id: str, packs_dir: Path | None, tracks_dir: Path = TRACKS_DIR) -> dict | None:
    """What the tool needs of one track: {id, title, artist, bpm, first_downbeat_s, duration_s, sections, constant, drift_ms, source}. `source` is "pack"
    or "committed" (the committed metadata is used when the pack is missing). None when neither exists."""
    committed = None
    cp = tracks_dir / (track_id + ".json")
    if cp.exists():
        committed = read_json(cp)
    pack = None
    if packs_dir is not None:
        pp = Path(packs_dir) / track_id / "track.json"
        if pp.exists():
            pack = read_json(pp)
    base = pack if pack is not None else committed
    if base is None:
        return None
    tempo = base.get("tempo", {})
    ctempo = (committed or {}).get("tempo", {})
    detail = (pack or {}).get("source", {}).get("tempo_detail", {}) if pack is not None else {}
    drift = ctempo.get("drift_ms_max", detail.get("drift_ms_max_abs", tempo.get("drift_ms_max", 0.0)))
    constant = ctempo.get("constant", detail.get("constant", tempo.get("constant", True)))
    ident = committed or base
    return {"id": track_id, "title": ident.get("title", ""), "artist": ident.get("artist", ""), "bpm": float(tempo["bpm"]),
            "first_downbeat_s": float(tempo.get("first_downbeat_s", 0.0)), "duration_s": float(base.get("duration_s", 0.0)), "sections": base.get("sections", []),
            "voices": [v["key"] for v in base.get("voices", [])], "constant": bool(constant), "drift_ms": float(drift or 0.0),
            "source": "pack" if pack is not None else "committed"}


def track_ids(tracks_dir: Path = TRACKS_DIR) -> list[str]:
    return sorted(p.stem for p in tracks_dir.glob("*.json") if p.stem != "catalogue")


def detect(f: dict, offset_beats: int = 0) -> dict:
    """The tool's own values for a track: first and second drop (the first two `drop` sections, as RunTrackPlan reads them) snapped to the grid, the first
    `outro` section's start. Returns {first: snap-dict|None, second: ..., outro_s, raw_first_s}."""
    drops = [s for s in f["sections"] if s.get("role") == "drop"]
    out: dict = {"first": None, "second": None, "outro_s": None, "raw_first_s": None}
    if drops:
        out["raw_first_s"] = float(drops[0]["start_s"])
        out["first"] = snap(float(drops[0]["start_s"]), f["first_downbeat_s"], f["bpm"], offset_beats)
    if len(drops) > 1:
        out["second"] = snap(float(drops[1]["start_s"]), f["first_downbeat_s"], f["bpm"], offset_beats)
    outros = [s for s in f["sections"] if s.get("role") == "outro"]
    if outros:
        out["outro_s"] = float(outros[0]["start_s"])
    return out


# ---------------------------------------------------------------------------------------------------------------- the sidecar

def blank_sidecar(track_id: str) -> dict:
    d = {k: None for k in KEYS}
    d.update({"format": FORMAT, "track": track_id, "downbeat_offset_beats": 0, "no_blend": False, "note": "", "origin": {}})
    return d


def ordered(d: dict) -> dict:
    return {k: d[k] for k in KEYS if k in d}


def build_sidecar(f: dict, existing: dict | None) -> dict:
    """The sidecar for track facts `f`: detected fields recomputed, owner fields and everything the tool cannot detect kept from `existing`."""
    d = blank_sidecar(f["id"])
    if existing:
        for k in KEYS:
            if k in existing:
                d[k] = existing[k]
        d["origin"] = dict(existing.get("origin") or {})
    origin: dict = d["origin"]
    det = detect(f, int(d["downbeat_offset_beats"] or 0))
    first_owner = origin.get("first_drop_s") == "owner" and d["first_drop_s"] is not None
    if not first_owner:
        if det["first"] is None:
            d["first_drop_s"], d["first_drop_bar"], d["first_drop_snap_ms"] = None, None, None
        else:
            s = det["first"]
            d["first_drop_s"], d["first_drop_bar"], d["first_drop_snap_ms"] = r4(s["time_s"]), s["bar"], round(s["err_s"] * 1000.0, 1)
        origin["first_drop_s"] = "detected"
    if origin.get("second_drop_s") != "owner" or d["second_drop_s"] is None:
        d["second_drop_s"] = r4(det["second"]["time_s"]) if det["second"] is not None else None
        origin["second_drop_s"] = "detected"
    if origin.get("outro_start_s") != "owner" or d["outro_start_s"] is None:
        d["outro_start_s"] = r4(det["outro_s"])
        origin["outro_start_s"] = "detected"
    d["origin"] = {k: origin[k] for k in DETECTABLE if k in origin}
    return ordered(d)


def validate_sidecar(d: object, track_id: str, facts: dict | None = None) -> list[str]:
    """Section 3.2's validation as sentences (empty list = valid). `facts` (track_facts) adds the checks that need the pack: the duration and the voices."""
    name = "%s.json" % track_id
    if not isinstance(d, dict):
        return ["%s: the sidecar is not an object" % name]
    errs: list[str] = []
    for k in d:
        if k not in KEYS:
            errs.append("%s: unknown key '%s'" % (name, k))
    if d.get("format") != FORMAT:
        errs.append("%s: format must be exactly %s" % (name, FORMAT))
    if d.get("track") != track_id:
        errs.append("%s: track must be '%s' (the file name)" % (name, track_id))

    def num(key: str, lo: float | None = None) -> float | None:
        v = d.get(key)
        if v is None:
            return None
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            errs.append("%s: %s must be a number or null" % (name, key))
            return None
        if lo is not None and v < lo:
            errs.append("%s: %s must be at least %s" % (name, key, lo))
        return float(v)

    bar_s = 240.0 / facts["bpm"] if facts else None
    first = num("first_drop_s", 0.0)
    second = num("second_drop_s", 0.0)
    if facts and facts["duration_s"] > 0:
        for key, v in (("first_drop_s", first), ("second_drop_s", second)):
            if v is not None and v > facts["duration_s"] - 16 * bar_s + 1e-6:
                errs.append("%s: %s %.3f is inside the last 16 bars (duration %.3f)" % (name, key, v, facts["duration_s"]))
    if first is not None and second is not None and bar_s is not None and second <= first + 16 * bar_s - 1e-6:
        errs.append("%s: second_drop_s must be more than 16 bars after first_drop_s" % name)
    off = d.get("downbeat_offset_beats")
    if isinstance(off, bool) or not isinstance(off, int) or not -3 <= off <= 3:
        errs.append("%s: downbeat_offset_beats must be an integer from -3 to 3" % name)
    intro = num("intro_start_s", 0.0)
    num("outro_start_s", 0.0)
    if intro is not None and first is not None and intro >= first:
        errs.append("%s: intro_start_s must be before first_drop_s" % name)
    for key in ("mix_in_bar", "mix_out_bar", "first_drop_bar"):
        v = d.get(key)
        if v is not None and (isinstance(v, bool) or not isinstance(v, int) or v < 0):
            errs.append("%s: %s must be a whole bar number or null" % (name, key))
    mix_in = d.get("mix_in_bar")
    fb = d.get("first_drop_bar")
    if isinstance(mix_in, int) and not isinstance(mix_in, bool) and isinstance(fb, int) and not (fb - 16 <= mix_in <= fb - 6):
        errs.append("%s: mix_in_bar must lie between first drop bar - 16 and first drop bar - 6" % name)
    if not isinstance(d.get("no_blend"), bool):
        errs.append("%s: no_blend must be true or false" % name)
    lg = d.get("linger")
    if lg is not None:
        if not isinstance(lg, list) or not all(isinstance(x, str) for x in lg):
            errs.append("%s: linger must be a list of voice keys or null" % name)
        elif facts:
            for x in lg:
                if x not in facts["voices"] and x != "backing":
                    errs.append("%s: linger key '%s' is not a voice of the pack" % (name, x))
    ch = d.get("checked")
    if ch is not None and not (isinstance(ch, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", ch)):
        errs.append("%s: checked must be a date string YYYY-MM-DD or null" % name)
    if not isinstance(d.get("note"), str):
        errs.append("%s: note must be a string" % name)
    sn = d.get("first_drop_snap_ms")
    if sn is not None and (isinstance(sn, bool) or not isinstance(sn, (int, float))):
        errs.append("%s: first_drop_snap_ms must be a number or null" % name)
    org = d.get("origin")
    if org is not None and not isinstance(org, dict):
        errs.append("%s: origin must be an object" % name)
    elif org is not None:
        for k, v in org.items():
            if k not in DETECTABLE:
                errs.append("%s: origin has an unknown field '%s'" % (name, k))
            if v not in ORIGINS:
                errs.append("%s: origin.%s must be 'detected' or 'owner'" % (name, k))
    return errs


def dump(d: dict) -> str:
    return json.dumps(d, indent=2, ensure_ascii=False) + "\n"


def write_text(path: Path, text: str) -> bool:
    """Write only when the content differs. Returns True when the file changed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return True


def read_sidecar(track_id: str, sidecar_dir: Path = SIDECAR_DIR) -> dict | None:
    p = sidecar_dir / (track_id + ".json")
    return read_json(p) if p.exists() else None


# ---------------------------------------------------------------------------------------------------------------- the sheet

def flags_for(f: dict, sidecar: dict) -> list[str]:
    flags: list[str] = []
    if sidecar.get("first_drop_s") is None:
        flags.append("no drop found")
    else:
        eb = sidecar["first_drop_snap_ms"] / 1000.0 / (60.0 / f["bpm"])
        if abs(eb) > SNAP_LARGE_BEATS:
            k = int(round(eb))
            if k != 0 and abs(eb - k) <= AGREE_BEATS:
                flags.append("snap %+.2f beat: bar phase suspect (grid looks %d beats out)" % (eb, k))
            else:
                flags.append("snap %+.2f beat: grid suspect (probably a wrong grid)" % eb)
        if sidecar["first_drop_bar"] == 0 and sidecar["first_drop_s"] < f["first_downbeat_s"] - 1e-6:
            flags.append("drop before the first downbeat (the track starts on its drop)")
        li = lead_in_bars(sidecar["first_drop_bar"], sidecar.get("mix_in_bar"))
        if li is not None and li < MIN_LEAD_IN:
            flags.append("lead-in %d bars: entered with cut" % li)
    if not f["constant"]:
        flags.append("tempo not constant")
    if f["drift_ms"] > GRID_DRIFT_MS:
        flags.append("drift %.0f ms: no beat matching (echo_out)" % f["drift_ms"])
    if sidecar.get("no_blend"):
        flags.append("no_blend")
    return flags


def sheet_row(f: dict, sidecar: dict, det: dict, previous: dict | None = None) -> dict:
    first = det["first"]
    bar_s = 240.0 / f["bpm"]
    row = {
        "track": f["id"], "title": f["title"], "artist": f["artist"], "bpm": "%.4f" % f["bpm"], "first_downbeat_s": "%.4f" % f["first_downbeat_s"],
        "beat_ms": "%.1f" % (60000.0 / f["bpm"]),
        "detected_drop_s": "" if first is None else "%.3f" % first["time_s"], "detected_drop_mmss": "" if first is None else mmss(first["time_s"]),
        "detected_drop_bar": "" if first is None else str(first["bar"]),
        "lead_in_bars": "" if sidecar["first_drop_bar"] is None else str(lead_in_bars(sidecar["first_drop_bar"], sidecar.get("mix_in_bar"))),
        "snap_ms": "" if first is None else "%.1f" % (first["err_s"] * 1000.0), "snap_beats": "" if first is None else "%.2f" % first["err_beats"],
        "drift_ms": "%.1f" % f["drift_ms"], "drop_s": "" if sidecar["first_drop_s"] is None else "%.3f" % sidecar["first_drop_s"],
        "origin": sidecar["origin"].get("first_drop_s", ""), "flags": "; ".join(flags_for(f, sidecar)),
        "owner_drop": "", "owner_offset_beats": "", "owner_no_blend": "", "owner_note": "",
    }
    _ = bar_s
    if previous:
        for c in OWNER_COLUMNS:
            row[c] = previous.get(c, "") or ""
    return row


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def make_csv_text(rows: list[dict]) -> str:
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


MD_COLUMNS = [("track", "Track"), ("title", "Title"), ("artist", "Artist"), ("bpm", "BPM"), ("detected_drop_mmss", "First drop"), ("detected_drop_bar", "Bar"),
              ("lead_in_bars", "Lead-in bars"), ("snap_ms", "Snap ms"), ("origin", "Origin"), ("flags", "Flags")]


def make_md_text(rows: list[dict]) -> str:
    n_flag = sum(1 for r in rows if r["flags"])
    out = [
        "# First drops of the 61 tracks",
        "",
        "Generated by `tools/music/transition_sidecars.py generate`; do not edit this file, edit `FIRST_DROPS.csv` (it opens in Excel). The doubtful tracks are first.",
        "",
        "How to use it: listen to the track at the first drop. If the drop time and bar are right, leave the owner columns blank (or write `ok` in `owner_drop` to say you have",
        "checked it). If not, write the right time in `owner_drop` (`43.80`, `0:43.8`, `bar 31` or `+1 beat` / `-1 beat` from the detected drop); `owner_offset_beats` (-3 to 3) when the",
        "grid is a whole number of beats out; `owner_no_blend` (`yes`) for a track that must never be overlapped; `owner_note` is free text. Then run",
        "`python tools/music/transition_sidecars.py apply` and `generate`. A blank cell never changes anything. Your values are kept on every later run.",
        "",
        "Columns: First drop = the drop the tool detected, as m:ss.mmm and as a bar number counted from the first downbeat; Lead-in bars = bars from the scene's entry to the drop",
        "(16 normally); Snap ms = how far the detected time is from the nearest bar line of the pack's grid (a large one means the grid is probably wrong); Origin = detected or owner.",
        "",
        "Flags: **lead-in under 5 bars** = scenes with this track are entered with a plain cut (ruling 7); **grid suspect / bar phase suspect** = the snap distance is large;",
        "**tempo not constant** / **drift over 20 ms** = no beat matching, the transition into or out of the track is an echo-out; **no drop found**.",
        "",
        "%d tracks, %d with at least one flag." % (len(rows), n_flag),
        "",
        "| " + " | ".join(h for _, h in MD_COLUMNS) + " |",
        "|" + "|".join("---" for _ in MD_COLUMNS) + "|",
    ]
    for r in rows:
        out.append("| " + " | ".join(str(r[k]).replace("|", "/") for k, _ in MD_COLUMNS) + " |")
    return "\n".join(out) + "\n"


def sort_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda r: (0 if r["flags"] else 1, r["track"]))


# ---------------------------------------------------------------------------------------------------------------- commands

def generate(packs_dir: Path | None, tracks_dir: Path = TRACKS_DIR, sidecar_dir: Path = SIDECAR_DIR, csv_path: Path = SHEET_CSV, md_path: Path = SHEET_MD,
             log=print) -> dict:
    prev = {r["track"]: r for r in read_csv(csv_path)}
    rows = []
    changed = 0
    for tid in track_ids(tracks_dir):
        f = track_facts(tid, packs_dir, tracks_dir)
        if f is None:
            log("skip %s: no pack and no committed metadata" % tid)
            continue
        existing = read_sidecar(tid, sidecar_dir)
        if f["source"] == "committed" and existing is not None:
            sc = existing  # no pack: do not recompute (the committed metadata is rounded coarser); keep what is there
        else:
            sc = build_sidecar(f, existing)
            if f["source"] == "committed":
                log("note %s: no pack, sidecar made from the committed metadata" % tid)
        errs = validate_sidecar(sc, tid, f)
        for e in errs:
            log("ERROR " + e)
        if write_text(sidecar_dir / (tid + ".json"), dump(sc)):
            changed += 1
        rows.append(sheet_row(f, sc, detect(f, int(sc["downbeat_offset_beats"] or 0)), prev.get(tid)))
    rows = sort_rows(rows)
    c1 = write_text(csv_path, make_csv_text(rows))
    c2 = write_text(md_path, make_md_text(rows))
    return {"tracks": len(rows), "sidecars_changed": changed, "csv_changed": c1, "md_changed": c2, "rows": rows}


def parse_owner_drop(text: str, current_s: float | None, first_downbeat_s: float, bpm: float, offset_beats: int = 0) -> float | None:
    """The forms of the `owner_drop` cell: `43.80` (seconds), `0:43.8` or `1:02` (m:ss), `bar 31`, `+1 beat` / `-2 beats` (from the current drop). Blank and `ok` are
    not times (None). Raises ValueError with a sentence on anything else."""
    t = text.strip().lower()
    if t in ("", "ok"):
        return None
    beat = 60.0 / bpm
    fd = first_downbeat_s + offset_beats * beat
    m = re.fullmatch(r"bar\s*(\d+)", t)
    if m:
        return fd + int(m.group(1)) * beat * BEATS_PER_BAR
    m = re.fullmatch(r"([+-])\s*(\d+(?:\.\d+)?)\s*beats?", t)
    if m:
        if current_s is None:
            raise ValueError("'%s' needs a current drop to move from" % text)
        return current_s + (1 if m.group(1) == "+" else -1) * float(m.group(2)) * beat
    m = re.fullmatch(r"(\d+):(\d+(?:\.\d+)?)", t)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    m = re.fullmatch(r"\d+(?:\.\d+)?", t)
    if m:
        return float(t)
    raise ValueError("cannot read owner_drop '%s' (use seconds, m:ss, 'bar N', or '+1 beat')" % text)


def _truthy(s: str) -> bool | None:
    t = s.strip().lower()
    if t in ("yes", "y", "true", "1"):
        return True
    if t in ("no", "n", "false", "0"):
        return False
    return None


def apply_row(f: dict, existing: dict | None, row: dict, today: str, log=print) -> dict | None:
    """The sidecar after the owner's row, or None when the row changes nothing (all owner cells blank). Prints the snap verdict of a typed drop."""
    owner_drop = (row.get("owner_drop") or "").strip()
    owner_off = (row.get("owner_offset_beats") or "").strip()
    owner_nb = (row.get("owner_no_blend") or "").strip()
    owner_note = (row.get("owner_note") or "").strip()
    if not (owner_drop or owner_off or owner_nb or owner_note):
        return None
    base = build_sidecar(f, existing)
    d = json.loads(json.dumps(base))
    origin = d["origin"]
    tid = f["id"]
    touched = False
    if owner_off:
        try:
            k = int(owner_off)
        except ValueError:
            raise ValueError("%s: owner_offset_beats '%s' is not an integer" % (tid, owner_off))
        if not -3 <= k <= 3:
            raise ValueError("%s: owner_offset_beats must be from -3 to 3" % tid)
        if k != d["downbeat_offset_beats"]:
            raw = None if d["first_drop_s"] is None else d["first_drop_s"] + (d["first_drop_snap_ms"] or 0.0) / 1000.0
            d["downbeat_offset_beats"] = k
            if raw is not None:  # the grid moved, the audio did not: snap the same time to the new grid
                s = snap(raw, f["first_downbeat_s"], f["bpm"], k)
                d["first_drop_s"], d["first_drop_bar"], d["first_drop_snap_ms"] = r4(s["time_s"]), s["bar"], round(s["err_s"] * 1000.0, 1)
            touched = True
    if owner_drop:
        cur = d["first_drop_s"]
        t = parse_owner_drop(owner_drop, cur, f["first_downbeat_s"], f["bpm"], int(d["downbeat_offset_beats"]))
        if t is not None:
            s = snap(t, f["first_downbeat_s"], f["bpm"], int(d["downbeat_offset_beats"]))
            d["first_drop_s"], d["first_drop_bar"], d["first_drop_snap_ms"] = r4(s["time_s"]), s["bar"], round(s["err_s"] * 1000.0, 1)
            if s["verdict"] == "phase_suspect":
                log("WARNING %s: %.3f s is %+.2f beat from a bar line; the grid looks %d beats out. Set owner_offset_beats to %d if so." % (tid, t, s["err_beats"], s["offset"], s["offset"]))
            elif s["verdict"] == "grid_suspect":
                log("ERROR %s: %.3f s is %+.2f beat from the nearest bar line: the grid is suspect (wrong tempo, drifting, or a typo)" % (tid, t, s["err_beats"]))
            else:
                log("ok %s: drop %.3f s, bar %d, snap %+.1f ms" % (tid, s["time_s"], s["bar"], s["err_s"] * 1000.0))
        if d["first_drop_s"] is not None:
            origin["first_drop_s"] = "owner"
        touched = True
    if owner_nb:
        v = _truthy(owner_nb)
        if v is None:
            raise ValueError("%s: owner_no_blend '%s' is not yes or no" % (tid, owner_nb))
        if v != d["no_blend"]:
            d["no_blend"] = v
        touched = True
    if owner_note and d["note"] != owner_note:
        d["note"] = owner_note
        touched = True
    d["origin"] = {k: origin[k] for k in DETECTABLE if k in origin}
    if touched:
        before = {k: v for k, v in (existing or {}).items() if k != "checked"}
        after = {k: v for k, v in d.items() if k != "checked"}
        d["checked"] = (existing or {}).get("checked") if (existing and before == after and existing.get("checked")) else today
    return ordered(d)


def apply(csv_path: Path, packs_dir: Path | None, tracks_dir: Path = TRACKS_DIR, sidecar_dir: Path = SIDECAR_DIR, today: str | None = None, log=print) -> dict:
    today = today or datetime.date.today().isoformat()
    changed = 0
    errors = 0
    for row in read_csv(csv_path):
        tid = row["track"]
        f = track_facts(tid, packs_dir, tracks_dir)
        if f is None:
            log("skip %s: no pack and no committed metadata (kept for later)" % tid)
            continue
        try:
            sc = apply_row(f, read_sidecar(tid, sidecar_dir), row, today, log)
        except ValueError as e:
            log("ERROR " + str(e))
            errors += 1
            continue
        if sc is None:
            continue
        for e in validate_sidecar(sc, tid, f):
            log("ERROR " + e)
            errors += 1
        if write_text(sidecar_dir / (tid + ".json"), dump(sc)):
            changed += 1
    return {"changed": changed, "errors": errors}


def check(packs_dir: Path | None, tracks_dir: Path = TRACKS_DIR, sidecar_dir: Path = SIDECAR_DIR, log=print) -> int:
    bad = 0
    ids = track_ids(tracks_dir)
    for tid in ids:
        sc = read_sidecar(tid, sidecar_dir)
        if sc is None:
            log("ERROR %s.json: missing" % tid)
            bad += 1
            continue
        for e in validate_sidecar(sc, tid, track_facts(tid, packs_dir, tracks_dir)):
            log("ERROR " + e)
            bad += 1
    extra = sorted(p.stem for p in sidecar_dir.glob("*.json") if p.stem not in ids)
    for e in extra:
        log("ERROR %s.json: no such track in the catalogue" % e)
        bad += 1
    log("%d sidecars checked, %d errors" % (len(ids), bad))
    return bad


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["generate", "apply", "check"])
    ap.add_argument("--packs", default=str(DEFAULT_PACKS), help="folder of track packs (read only); default $RW_AUDIO_WORK/packs")
    ap.add_argument("--csv", default=str(SHEET_CSV), help="the sheet (apply reads it, generate writes it)")
    ap.add_argument("--date", default=None, help="the `checked` date apply writes (default today)")
    a = ap.parse_args(argv)
    packs = Path(a.packs) if Path(a.packs).exists() else None
    if packs is None:
        print("note: no packs folder at %s; using the committed metadata" % a.packs)
    if a.command == "generate":
        r = generate(packs, csv_path=Path(a.csv))
        flagged = sum(1 for x in r["rows"] if x["flags"])
        print("%d tracks, %d with flags; %d sidecars written, sheet csv %s, md %s" % (r["tracks"], flagged, r["sidecars_changed"], "changed" if r["csv_changed"] else "unchanged",
                                                                                "changed" if r["md_changed"] else "unchanged"))
        return 0
    if a.command == "apply":
        r = apply(Path(a.csv), packs, today=a.date)
        print("%d sidecars updated, %d errors" % (r["changed"], r["errors"]))
        return 1 if r["errors"] else 0
    return 1 if check(packs) else 0


if __name__ == "__main__":
    sys.exit(main())
