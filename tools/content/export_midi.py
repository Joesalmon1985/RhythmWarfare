"""Export MIDI for missions 2 to 10, to be rendered in Ableton and imported the way mission 1 was.

    python tools/content/export_midi.py                 # missions 2 to 10 -> midi_export/ and content/imports/
    python tools/content/export_midi.py level_04 6      # only these missions
    python tools/content/export_midi.py --out DIR --imports DIR2   # somewhere else (the tests do this)

Missions 2 to 10 arrange library clips (content/missions/level_NN.json); none of them has a full-song MIDI. For every
mission this writes midi_export/level_NN_<slug>/ with a README, the default groove, bass line and backing as 8-bar
loops (Kick_A, Snare_A, Bass_A, Other_Pad, Other_Hats), two rule-based alternatives of every kick, snare and bass part
(B and C, deterministic from the mission's seed), and Arrangement_A.mid, a four-track reference of the whole mission
exactly as it plays. It also writes the import manifest content/imports/level_NN.json that names the WAVs the owner
renders from those MIDI files (`python tools/content/import_ableton.py content/imports/level_NN.json`).

The clips are read from content/library/<clip>/<part>.mid with common.read_midi (the library is never written), and the
phases are laid out the way mission.py's Mission.arrange lays them out: a groove loops from the phase start up to the
fill, a fill of F bars replaces the last F bars of the phase, a bass line loops from the phase start, an accompaniment
loops over its placement.

Every output is deterministic: same files, byte for byte, on every run. Files are written with LF line endings.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path

import mido

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (BPM, CONTENT, LIBRARY, MISSIONS, PPQ, ROOT, TICKS_PER_BAR, ContentError, read_json, read_midi,  # noqa: E402
                    rel)

EXPORT_DIR = ROOT / "midi_export"
IMPORTS_DIR = CONTENT / "imports"
LEVELS = tuple(range(2, 11))
LOOP_BARS = 8  # the length of every A/B/C loop (the library's clip length)
LOOP_TICKS = LOOP_BARS * TICKS_PER_BAR
WINDOW = 2 * TICKS_PER_BAR  # variations are made, and checked, per two bars
MIN_GAP = 480  # same-pad minimum gap in ticks (data/campaign/rules.json chart.same_pad_min_gap_ticks)
HAT_PITCHES = (42, 46)
SCALE_PCS = {1, 3, 4, 6, 8, 9, 11}  # C# natural minor: C# D# E F# G# A B
BASS_LOW, BASS_HIGH = 28, 52
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
CHORD_TEMPLATES = [("m", (0, 3, 7)), ("", (0, 4, 7)), ("m7", (0, 3, 7, 10)), ("sus4", (0, 5, 7)), ("sus2", (0, 2, 7))]
ROOT_REGISTER = (32, 43)  # a chord root becomes the pitch of that pitch class inside this range (C#=37, A=33, E=40, B=35)
FILES = ["Kick_A", "Snare_A", "Bass_A", "Other_Pad", "Other_Hats", "Kick_B", "Kick_C", "Snare_B", "Snare_C", "Bass_B",
         "Bass_C", "Arrangement_A"]
LEVELS_RULE = {"kick": {"peak_db": -4.0}, "snare": {"peak_db": -4.0}, "bass": {"peak_db": -4.0, "rms_db": -17.0},
               "other": {"peak_db": -3.0}}


# --- small helpers ------------------------------------------------------------------------------------------------

def note(tick: int, duration: int, pitch: int, velocity: int) -> dict:
    return {"tick": int(tick), "duration_ticks": int(duration), "pitch": int(pitch), "velocity": int(velocity)}


def key_of(n: dict) -> tuple:
    return (n["tick"], n["duration_ticks"], n["pitch"], n["velocity"])


def sort_notes(notes: list[dict]) -> list[dict]:
    return sorted((dict(n) for n in notes), key=lambda n: (n["tick"], n["pitch"], n["duration_ticks"]))


def pos(tick: int) -> str:
    """'bar 2 beat 4-and' for a tick (bar 1 = tick 0; -e, -and, -a are the sixteenth positions)."""
    bar, rest = divmod(tick, TICKS_PER_BAR)
    beat, sub = divmod(rest, PPQ)
    name = {0: "", 240: "-e", 480: "-and", 720: "-a"}.get(sub, f"+{sub}t")
    return f"bar {bar + 1} beat {beat + 1}{name}"


def pitch_name(p: int) -> str:
    return f"{NOTE_NAMES[p % 12]}{p // 12 - 2}"  # Ableton's names: middle C (60) is C3, so pitch 37 is C#1


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)


def write_text(path: Path, text: str) -> None:
    """Text with LF line endings, whatever the platform."""
    write_bytes(path, text.replace("\r\n", "\n").encode("utf-8"))


# --- clips and missions -------------------------------------------------------------------------------------------

_clip_cache: dict[tuple[str, str], list[dict]] = {}


def clip_bars(clip_id: str) -> int:
    return int(read_json(LIBRARY / clip_id / "clip.json")["bars"])


def clip_notes(clip_id: str, part: str) -> list[dict]:
    key = (clip_id, part)
    if key not in _clip_cache:
        path = LIBRARY / clip_id / f"{part}.mid"
        if not path.exists():
            raise ContentError(f"{rel(path)}: missing (is {clip_id} an audio-only clip?)")
        _clip_cache[key] = read_midi(path)["notes"]
    return [dict(n) for n in _clip_cache[key]]


def resolve(mission: dict, fld: str, ref) -> str:
    """A phase field is a clip id or a 1-based slot of the mission's choice: the slot's default clip."""
    if isinstance(ref, int):
        return mission["choices"][fld]["default"][ref - 1]
    return str(ref)


def default_clip(mission: dict, fld: str) -> str | None:
    """The mission's default groove / fill / bass clip: the choice's first default, else the first phase that names one."""
    choice = mission["choices"].get(fld)
    if choice:
        return choice["default"][0]
    for ph in mission["phases"]:
        if fld in ph:
            return resolve(mission, fld, ph[fld])
    return None


def tile(notes: list[dict], loop_ticks: int, start: int, end: int) -> list[dict]:
    """Repeat a clip from `start` until `end` (the last repetition is cut at `end`)."""
    out = []
    at = start
    while at < end:
        for n in notes:
            t = at + n["tick"]
            if t < end:
                m = dict(n)
                m["tick"] = t
                m["duration_ticks"] = min(n["duration_ticks"], end - t)
                out.append(m)
        at += loop_ticks
    return out


def drum_loop(part: str, groove: str, fill: str | None) -> list[dict]:
    """The groove tiled over the 8-bar loop, the fill (if any) replacing its last bar(s)."""
    fill_at = LOOP_TICKS - (clip_bars(fill) * TICKS_PER_BAR if fill else 0)
    out = tile(clip_notes(groove, part), clip_bars(groove) * TICKS_PER_BAR, 0, fill_at)
    if fill:
        out += tile(clip_notes(fill, part), clip_bars(fill) * TICKS_PER_BAR, fill_at, LOOP_TICKS)
    return sort_notes(out)


def chord_root(pitches: list[int]) -> int:
    """The root pitch class of a chord given by its pitches (inversions and clamped octaves allowed)."""
    pcs = {p % 12 for p in pitches}
    for _, intervals in CHORD_TEMPLATES:
        for r in sorted(pcs):
            if {(r + iv) % 12 for iv in intervals} == pcs:
                return r
    return min(pitches) % 12


def root_pitch(pc: int) -> int:
    lo, hi = ROOT_REGISTER
    return next(p for p in range(lo, hi + 1) if p % 12 == pc)


def root_line(acc_notes: list[dict]) -> list[dict]:
    """A new bass line for a mission with no bass phase: one root note per two bars, the root of the backing's chord."""
    out = []
    for w in range(LOOP_BARS // 2):
        chord = [n["pitch"] for n in acc_notes if n["pitch"] not in HAT_PITCHES and w * WINDOW <= n["tick"] < w * WINDOW + TICKS_PER_BAR]
        if not chord:
            raise ContentError(f"the backing has no chord in bar {2 * w + 1}")
        out.append(note(w * WINDOW, WINDOW - 240, root_pitch(chord_root(chord)), 100))
    return out


def split_other(acc_notes: list[dict]) -> tuple[list[dict], list[dict]]:
    pad = [n for n in acc_notes if n["pitch"] not in HAT_PITCHES]
    hats = [n for n in acc_notes if n["pitch"] in HAT_PITCHES]
    return pad, hats


# --- the whole mission, phase by phase --------------------------------------------------------------------------

def arrangement(mission: dict) -> dict[str, list[dict]]:
    """Kick, Snare, Bass and Other notes of the whole mission with the default choices, as Mission.arrange places them."""
    parts: dict[str, list[dict]] = {"Kick": [], "Snare": [], "Bass": [], "Other": []}
    s = 0
    for ph in mission["phases"]:
        e = s + int(ph["bars"]) * TICKS_PER_BAR
        fill_at = e
        fill = resolve(mission, "fill", ph["fill"]) if "fill" in ph else None
        if fill:
            fill_at = e - clip_bars(fill) * TICKS_PER_BAR
        if "groove" in ph:
            groove = resolve(mission, "groove", ph["groove"])
            for name, part in (("Kick", "kick"), ("Snare", "snare")):
                parts[name] += tile(clip_notes(groove, part), clip_bars(groove) * TICKS_PER_BAR, s, fill_at)
                if fill:
                    parts[name] += tile(clip_notes(fill, part), clip_bars(fill) * TICKS_PER_BAR, fill_at, e)
        if "bass" in ph:
            bass = resolve(mission, "bass", ph["bass"])
            parts["Bass"] += tile(clip_notes(bass, "bass"), clip_bars(bass) * TICKS_PER_BAR, s, e)
        s = e
    for a in mission.get("accompaniment", []):
        clip = resolve(mission, "accompaniment", a["clip"])
        start = (int(a.get("start_bar", 1)) - 1) * TICKS_PER_BAR
        end = start + int(a.get("bars", clip_bars(clip))) * TICKS_PER_BAR
        parts["Other"] += tile(clip_notes(clip, "other"), clip_bars(clip) * TICKS_PER_BAR, start, end)
    return {k: sort_notes(v) for k, v in parts.items()}


# --- variations -------------------------------------------------------------------------------------------------

def edit_distance(a: list[dict], b: list[dict]) -> int:
    """Notes changed, added or removed between two parts: the larger of what is only in a and what is only in b
    (a moved note counts once, a split note twice)."""
    ca, cb = Counter(map(key_of, a)), Counter(map(key_of, b))
    return max(sum((ca - cb).values()), sum((cb - ca).values()))


def window_edits(a: list[dict], b: list[dict], w: int) -> int:
    lo, hi = w * WINDOW, (w + 1) * WINDOW
    return edit_distance([n for n in a if lo <= n["tick"] < hi], [n for n in b if lo <= n["tick"] < hi])


def variation_limit(count: int, windows: int = LOOP_BARS // 2) -> int:
    """At most a quarter of the part's notes may change, but never fewer than one edit per two bars (sparse parts such
    as four two-bar bass notes could not be varied in every window otherwise)."""
    return max(math.ceil(count / 4), windows)


def gap_ok(notes: list[dict], total: int = LOOP_TICKS) -> bool:
    """Inside the loop, no two notes of the part closer than the same-pad gap, none overlapping."""
    ns = sorted(notes, key=lambda n: (n["tick"], n["pitch"]))
    for i, n in enumerate(ns):
        if n["tick"] < 0 or n["tick"] + n["duration_ticks"] > total:
            return False
        if i + 1 < len(ns):
            nx = ns[i + 1]
            if nx["tick"] - n["tick"] < MIN_GAP or n["tick"] + n["duration_ticks"] > nx["tick"]:
                return False
    return True


def _in_window(notes: list[dict], w: int) -> list[dict]:
    return [n for n in notes if w * WINDOW <= n["tick"] < (w + 1) * WINDOW]


def _kick_candidates(cur: list[dict], w: int, rng: random.Random) -> list[tuple[str, list[dict]]]:
    b0 = w * WINDOW
    adds, moves, drops = [], [], []
    for off in (3360, 1440, TICKS_PER_BAR + 3360, TICKS_PER_BAR + 1440):  # the "and" of beat 4, the eighth before beat 3
        t = b0 + off
        kind = "a pickup on the and of beat 4" if off % TICKS_PER_BAR == 3360 else "an extra eighth before beat 3"
        adds.append((f"added {kind}: kick at {pos(t)}", cur + [note(t, 120, 36, 100)]))
    for n in _in_window(cur, w):
        if n["pitch"] != 36 or n["tick"] % TICKS_PER_BAR == 0:
            continue
        for d in (-480, 480, -240, 240):
            t = n["tick"] + d
            if b0 <= t < b0 + WINDOW and t % TICKS_PER_BAR != 0:
                moved = [dict(m) for m in cur if m is not n] + [note(t, n["duration_ticks"], n["pitch"], n["velocity"])]
                moves.append((f"moved the kick at {pos(n['tick'])} to {pos(t)}", moved))
    for n in _in_window(cur, w):
        if n["pitch"] == 36 and n["tick"] != b0:
            drops.append((f"dropped the kick at {pos(n['tick'])}", [m for m in cur if m is not n]))
    rng.shuffle(adds)
    rng.shuffle(moves)
    rng.shuffle(drops)
    pools = [adds, moves]
    rng.shuffle(pools)
    return pools[0] + pools[1] + drops


def _snare_candidates(cur: list[dict], w: int, rng: random.Random) -> list[tuple[str, list[dict]]]:
    b0 = w * WINDOW
    backbeats = [n for n in _in_window(cur, w) if n["velocity"] >= 100]
    ghosts, displaced, beat4, nudges = [], [], [], []
    for n in backbeats:  # a ghost an eighth before the backbeat (a sixteenth would break the 480-tick same-pad gap)
        t = n["tick"] - 480
        if t >= b0:
            ghosts.append((f"added a ghost (velocity 46) at {pos(t)}, an eighth before the backbeat at {pos(n['tick'])}",
                           cur + [note(t, 120, 38, 46)]))
        t = n["tick"] - n["tick"] % TICKS_PER_BAR + 2400
        if t != n["tick"]:
            displaced.append((f"moved the backbeat at {pos(n['tick'])} to {pos(t)}",
                              [dict(m) for m in cur if m is not n] + [note(t, n["duration_ticks"], 38, n["velocity"])]))
        for d in (-240, 240):
            t = n["tick"] + d
            if b0 <= t < b0 + WINDOW:
                nudges.append((f"nudged the snare at {pos(n['tick'])} to {pos(t)}",
                               [dict(m) for m in cur if m is not n] + [note(t, n["duration_ticks"], 38, n["velocity"])]))
    t = b0 + TICKS_PER_BAR + 2880
    beat4.append((f"added a hit on beat 4 of bar {t // TICKS_PER_BAR + 1}: snare at {pos(t)}", cur + [note(t, 120, 38, 108)]))
    pools = [ghosts, displaced, beat4]
    for p in pools:
        rng.shuffle(p)
    rng.shuffle(pools)
    rng.shuffle(nudges)
    return [c for p in pools for c in p] + nudges


def _bass_candidates(cur: list[dict], w: int, rng: random.Random, variant: str) -> list[tuple[str, list[dict]]]:
    b0 = w * WINDOW
    inw = _in_window(cur, w)
    moves_by_note, splits, ties = [], [], []
    for n in inw:
        p = n["pitch"]
        fifths = [p + iv for iv in (7, -5) if (p + iv) % 12 in SCALE_PCS and BASS_LOW <= p + iv <= BASS_HIGH]
        if not fifths:
            fifths = [p + iv for iv in (6, -6) if (p + iv) % 12 in SCALE_PCS and BASS_LOW <= p + iv <= BASS_HIGH]
        octave = p + 12 if p + 12 <= BASS_HIGH else p - 12
        options = [("the fifth", q) for q in fifths] + [("the octave", octave)]
        if variant == "C":
            options.reverse()
        note_moves = []
        for what, q in options:
            note_moves.append((f"moved {pitch_name(p)} at {pos(n['tick'])} to {what} ({pitch_name(q)})",
                               [dict(m) for m in cur if m is not n] + [note(n["tick"], n["duration_ticks"], q, n["velocity"])]))
        moves_by_note.append(note_moves)
        d = n["duration_ticks"]
        half = d // 2 // 240 * 240
        if d >= 1920 and half >= 960 and n["tick"] + half < b0 + WINDOW:
            rest = [dict(m) for m in cur if m is not n]
            splits.append((f"split {pitch_name(p)} at {pos(n['tick'])} into two notes",
                           rest + [note(n["tick"], half - 120, p, n["velocity"]), note(n["tick"] + half, d - half, p, n["velocity"])]))
    ordered = sorted(inw, key=lambda m: m["tick"])
    for a, b in zip(ordered, ordered[1:]):
        if a["pitch"] == b["pitch"] and b["tick"] - (a["tick"] + a["duration_ticks"]) <= 240:
            rest = [dict(m) for m in cur if m is not a and m is not b]
            ties.append((f"tied the two {pitch_name(a['pitch'])} notes at {pos(a['tick'])} and {pos(b['tick'])}",
                         rest + [note(a["tick"], b["tick"] + b["duration_ticks"] - a["tick"], a["pitch"], a["velocity"])]))
    pools = [splits, ties]
    for p in pools:
        rng.shuffle(p)
    rng.shuffle(pools)
    rng.shuffle(moves_by_note)  # which note moves is random; the variant decides fifth-first (B) or octave-first (C)
    ordered_moves = [c for note_moves in moves_by_note for c in note_moves]
    return pools[0] + ordered_moves + pools[1]


def vary(part: str, notes: list[dict], seed: int, variant: str, attempt: int = 0, avoid: list[str] | None = None) -> tuple[list[dict], list[str]]:
    """A rule-based variation of an 8-bar loop: one edit per two bars (more in a dense part, up to a quarter of its notes).
    Returns the new notes and one description per two-bar window. Deterministic from (seed, part, variant, attempt)."""
    rng = random.Random(f"{seed}|{part}|{variant}|{attempt}")
    cur = sort_notes(notes)
    windows = LOOP_TICKS // WINDOW
    cap = variation_limit(len(cur), windows)
    used = 0
    log: list[str] = []
    for w in range(windows):
        budget = cap - used - (windows - 1 - w)
        if part == "bass":
            cands = _bass_candidates(cur, w, rng, variant)
        elif part == "kick":
            cands = _kick_candidates(cur, w, rng)
        else:
            cands = _snare_candidates(cur, w, rng)
        chosen = None
        for skip_avoid in (True, False):
            for label, new in cands:
                if skip_avoid and avoid and label == avoid[w]:
                    continue
                cost = edit_distance(cur, new)
                if cost <= budget and gap_ok(new) and (cost >= 1):
                    chosen = (label, new, cost)
                    break
            if chosen:
                break
        if chosen is None:
            raise ContentError(f"cannot vary {part} in bars {2 * w + 1}-{2 * w + 2} within the rules")
        log.append(chosen[0])
        cur = sort_notes(chosen[1])
        used += chosen[2]
    return cur, log


def variations(part: str, notes: list[dict], seed: int) -> dict[str, tuple[list[dict], list[str]]]:
    """B and C of a part, different from each other."""
    b_notes, b_log = vary(part, notes, seed, "B")
    for attempt in range(60):
        c_notes, c_log = vary(part, notes, seed, "C", attempt, avoid=b_log)
        if [key_of(n) for n in c_notes] != [key_of(n) for n in b_notes]:
            return {"B": (b_notes, b_log), "C": (c_notes, c_log)}
    raise ContentError(f"could not make {part} C differ from B")


# --- MIDI files -------------------------------------------------------------------------------------------------

def midi_bytes(tracks: list[tuple[str, list[dict]]], bars: int, title: str) -> bytes:
    """A type 1 file at 960 PPQ: a tempo track (174 BPM, 4/4) and one named track per part. Every track ends at the last
    bar line, so a DAW imports the clip at exactly `bars` bars."""
    total = bars * TICKS_PER_BAR
    mid = mido.MidiFile(type=1, ticks_per_beat=PPQ)
    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage("track_name", name=title, time=0))
    meta.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
    meta.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, time=0))
    meta.append(mido.MetaMessage("end_of_track", time=total))
    mid.tracks.append(meta)
    for name, notes in tracks:
        tr = mido.MidiTrack()
        tr.append(mido.MetaMessage("track_name", name=name, time=0))
        events = []
        for n in notes:
            if n["tick"] + n["duration_ticks"] > total:
                raise ContentError(f"{name}: a note runs past the end of the file")
            events.append((n["tick"], 1, mido.Message("note_on", note=n["pitch"], velocity=n["velocity"], channel=0)))
            events.append((n["tick"] + n["duration_ticks"], 0, mido.Message("note_off", note=n["pitch"], velocity=0, channel=0)))
        events.sort(key=lambda e: (e[0], e[1], e[2].note))
        now = 0
        for tick, _, msg in events:
            msg.time = tick - now
            now = tick
            tr.append(msg)
        tr.append(mido.MetaMessage("end_of_track", time=total - now))
        mid.tracks.append(tr)
    import io
    buf = io.BytesIO()
    mid.save(file=buf)
    return buf.getvalue()


# --- one mission ------------------------------------------------------------------------------------------------

def load_mission(number: int) -> dict:
    return read_json(MISSIONS / f"level_{number:02d}.json")


def build_mission(number: int, out_dir: Path, imports_dir: Path | None) -> dict:
    m = load_mission(number)
    seed = int(m["seed"])
    level_id = m["level_id"]
    title = m["title"]
    folder_name = f"{level_id}_{slugify(title)}"
    folder = out_dir / folder_name
    groove = default_clip(m, "groove")
    has_fill = any("fill" in ph for ph in m["phases"])
    fill = default_clip(m, "fill") if has_fill else None
    bass = default_clip(m, "bass")
    acc_ref = m["accompaniment"][0]["clip"]
    acc = resolve(m, "accompaniment", acc_ref)
    acc_notes = clip_notes(acc, "other")
    acc_bars = clip_bars(acc)
    if groove is None:
        raise ContentError(f"{level_id}: no groove")
    kick_a, snare_a = drum_loop("kick", groove, fill), drum_loop("snare", groove, fill)
    new_bass = bass is None
    bass_a = root_line(acc_notes) if new_bass else sort_notes(tile(clip_notes(bass, "bass"), clip_bars(bass) * TICKS_PER_BAR, 0, LOOP_TICKS))
    pad, hats = split_other(acc_notes)
    files: dict[str, tuple[list, int, str]] = {}  # name -> (tracks, bars, title)

    def put(name: str, notes: list[dict], bars: int = LOOP_BARS) -> None:
        files[name] = ([(name, notes)], bars, f"{title} {name}")

    put("Kick_A", kick_a)
    put("Snare_A", snare_a)
    put("Bass_A", bass_a)
    put("Other_Pad", pad, acc_bars)
    put("Other_Hats", hats, acc_bars)
    logs: dict[str, list[str]] = {}
    for part, a_notes, label in (("kick", kick_a, "Kick"), ("snare", snare_a, "Snare"), ("bass", bass_a, "Bass")):
        for variant, (notes, log) in variations(part, a_notes, seed).items():
            put(f"{label}_{variant}", notes)
            logs[f"{label}_{variant}"] = log
    arr = arrangement(m)
    files["Arrangement_A"] = ([(k, arr[k]) for k in ("Kick", "Snare", "Bass", "Other")], int(m["bars"]), f"{title} Arrangement_A")
    written = []
    for name, (tracks, bars, ttl) in files.items():
        write_bytes(folder / f"{name}.mid", midi_bytes(tracks, bars, ttl))
        written.append(folder / f"{name}.mid")
    info = {"number": number, "level_id": level_id, "title": title, "bars": int(m["bars"]), "groove": groove, "fill": fill,
            "bass": bass, "acc": acc, "acc_bars": acc_bars, "new_bass": new_bass, "folder_name": folder_name,
            "counts": {k: sum(len(t[1]) for t in v[0]) for k, v in files.items()}, "logs": logs,
            "has_bass_phase": not new_bass, "phase_count": len(m["phases"])}
    write_text(folder / "README.md", mission_readme(info))
    written.append(folder / "README.md")
    if imports_dir is not None:
        write_text(imports_dir / f"{level_id}.json", manifest_text(info))
        written.append(imports_dir / f"{level_id}.json")
    info["files"] = written
    return info


# --- documents --------------------------------------------------------------------------------------------------

def mission_readme(i: dict) -> str:
    n, lid, title = i["number"], i["level_id"], i["title"]
    c = i["counts"]
    fill_text = (f", with the fill {i['fill']} replacing bar 8" if i["fill"] else ", no fill (this mission's phases use none)")
    long_other = i["acc_bars"] != LOOP_BARS
    bass_desc = (f"The mission's default bass line, {i['bass']}, tiled over 8 bars (it is already 8 bars)" if not i["new_bass"] else
                 "NEW: this mission has no bass phase, so this is a root-note line, one note per two bars at the root of the "
                 "backing's chord (taken from bars 1-8 of the backing), in the C#1 register (Ableton names, MIDI pitches 32 to 42). The mission does not play it today")
    other_len = str(i["acc_bars"])
    other_long = (" The backing is that long in this mission, so it is not shortened to 8 bars." if long_other else "")
    lines = [
        f"# Mission {n}: {title}",
        "",
        f"- Mission length: {i['bars']} bars at 174 BPM, 4/4, key C# minor (960 PPQ, bar 1 = tick 0).",
        f"- Default content: groove {i['groove']}{fill_text}; bass {('line ' + i['bass']) if i['bass'] else 'none in the mission (new root line below)'}; "
        f"backing {i['acc']} ({i['acc_bars']} bars).",
        "",
        "## Files",
        "",
        "| File | Bars | What it is |",
        "|---|---|---|",
        f"| Kick_A.mid | 8 | The default groove ({i['groove']}) tiled to 8 bars{fill_text}; kick notes only (any pitch 48 kick of the push groove is kept) ({c['Kick_A']} notes). |",
        f"| Snare_A.mid | 8 | The same groove and fill, snare notes only ({c['Snare_A']} notes). |",
        f"| Bass_A.mid | 8 | {bass_desc} ({c['Bass_A']} notes). |",
        f"| Other_Pad.mid | {other_len} | The backing's chords (everything except pitches 42 and 46) from {i['acc']} ({c['Other_Pad']} notes).{other_long} |",
        f"| Other_Hats.mid | {other_len} | The backing's hi-hats (pitches 42 closed and 46 open) from {i['acc']} ({c['Other_Hats']} notes).{other_long} |",
        f"| Kick_B.mid, Kick_C.mid | 8 | Alternatives of Kick_A: one hit added, moved or dropped every two bars. |",
        f"| Snare_B.mid, Snare_C.mid | 8 | Alternatives of Snare_A: a ghost added, a backbeat moved to beat 3 and, or a hit added on beat 4. |",
        f"| Bass_B.mid, Bass_C.mid | 8 | Alternatives of Bass_A: a note moved to the fifth or the octave, a long note split or two notes tied; always C# natural minor. |",
        f"| Arrangement_A.mid | {i['bars']} | Reference only, do not render: four tracks (Kick, Snare, Bass, Other) laying out the whole mission phase by phase with the default choices, exactly as it plays. "
        + ("The Bass track is empty: this mission has no bass phase." if i["new_bass"] else "") + " |",
        "",
    ]
    if long_other:
        lines += [f"The two Other files keep the backing's full {i['acc_bars']} bars (render all of them, plus at most one tail bar; the other parts are 8). The manifest content/imports/{lid}.json imports the first 8 bars "
                  f"(its `bars` is 8); to import the whole backing later use a second manifest with `\"bars\": {i['acc_bars']}`.", ""]
    lines += ["## What the alternatives change", "",
              "Each alternative differs from its A in at least one note per two bars and in at most a quarter of A's notes "
              "(a sparse part may reach one edit per two bars), keeps every note inside the 8 bars and keeps the same-pad gap "
              "(no two notes of one part closer than 480 ticks, none overlapping). B and C are made from the mission's seed, "
              "so they are the same every time the exporter runs.", ""]
    for label in ("Kick_B", "Kick_C", "Snare_B", "Snare_C", "Bass_B", "Bass_C"):
        lines.append(f"{label}:")
        for w, text in enumerate(i["logs"][label]):
            lines.append(f"- bars {2 * w + 1}-{2 * w + 2}: {text}")
        lines.append("")
    lines += [
        "## Render rules (Ableton)",
        "",
        "- Import each MIDI file into a clip at 174 BPM, 4/4, with the project start as bar 1 (no pre-roll).",
        "- Render each part to a WAV: 48 kHz, stereo, 16-bit, starting at bar 1, 8 bars plus at most one bar of tail "
        "(the importer keeps the 8 bars and any tail that still sounds, up to one bar, and never stretches).",
        "- Name the WAV after its MIDI file: Kick_A.mid -> Kick_A.wav, Snare_B.mid -> Snare_B.wav, Other_Pad.mid -> Other_Pad.wav, "
        "and so on. Put the WAVs in this folder (they are ignored by git).",
        f"- A second recording of the same part with another instrument is Kick_A2.wav: add it to `content/imports/{lid}.json` "
        f"as a sound (`{{\"id\": \"m{n:02d}_kick_a2\", \"family\": \"kick\", \"name\": \"...\"}}`) and as a second entry in that clip's "
        f"`renders` (`\"m{n:02d}_kick_a2\": \"Kick_A2.wav\"`).",
        "- Every WAV the manifest names must exist. If you skip a part, delete its sounds and clip from the manifest first.",
        "",
        "## Then run",
        "",
        "```",
        f"python tools/content/import_ableton.py content/imports/{lid}.json --check",
        f"python tools/content/import_ableton.py content/imports/{lid}.json",
        f"python tools/content/build.py {lid}",
        "```",
        "",
        f"The import makes the clips m{n:02d}_groove_a/b/c, m{n:02d}_bass_a/b/c and m{n:02d}_backing in content/library/. "
        f"The mission is then rewired to the imported clips in a follow-up, as mission 1 was; until then {lid} plays the placeholder library clips as before.",
        "",
    ]
    return "\n".join(lines)


def overview_readme() -> str:
    return """# MIDI for missions 2 to 10

Mission 1 was rebuilt on your own Ableton recordings. Missions 2 to 10 still play placeholder clips from the loop library.
This folder gives you MIDI to record the same way: one sub-folder per mission, `level_NN_<title>/`.

## What is in a mission folder

Each folder has a README with the details, plus:

- 8-bar loops at 174 BPM, 4/4: `Kick_A`, `Snare_A` (the mission's default groove, with its fill in bar 8), `Bass_A` (its default
  bass line; missions 2, 4, 6 and 8 have no bass phase, so theirs is a new root-note line) and `Other_Pad` / `Other_Hats`
  (the backing, split into chords and hi-hats; missions 2 and 3 keep their 40 and 48 bars).
- Alternatives `Kick_B`, `Kick_C`, `Snare_B`, `Snare_C`, `Bass_B`, `Bass_C`: small rule-based variations of A (a pickup, a
  ghost, a note moved to the fifth). They are generated from the mission's seed, so re-running the exporter never changes them.
- `Arrangement_A.mid`: a four-track reference of the whole mission with the default choices. Listen to it, do not render it.

## How to use them

1. Load a loop into Ableton, play it with your instrument and render a WAV: 48 kHz stereo 16-bit, from bar 1 with no
   pre-roll, 8 bars plus at most one bar of tail. Name it after the MIDI file (`Kick_A.mid` gives `Kick_A.wav`) and keep it in the
   same folder. A second recording of one part is `Kick_A2.wav`; add it to the mission's manifest.
2. The manifest `content/imports/level_NN.json` already lists every file and sound id. Check it, then import:
   `python tools/content/import_ableton.py content/imports/level_NN.json --check`, then the same without `--check`, then
   `python tools/content/build.py level_NN`. The importer converts, trims, gain-stages and writes the clips into content/library/.
3. Every WAV a manifest names must exist, so delete the parts you do not record from the manifest first.

The `.wav` files are not committed (`midi_export/**/*.wav` is ignored); the MIDI and READMEs are.

## What happens next

Importing only adds clips to the library. The missions are rewired to the imported clips in a follow-up per mission, as mission 1
was: the choices, phases and sounds of `content/missions/level_NN.json` then point at the new clips and the placeholder ones
step aside. To regenerate this folder: `python tools/content/export_midi.py` (the same bytes every time).
"""


def manifest_text(i: dict) -> str:
    n, title = i["number"], i["title"]
    p = f"m{n:02d}"
    j = json.dumps
    long_other = i["acc_bars"] != LOOP_BARS
    note_text = (f"Mission {n} ({title}) content: the MIDI exported to midi_export/{i['folder_name']}/ (the mission's default groove, bass line and backing "
                 f"as 8-bar loops, with rule-based alternatives B and C of every kick, snare and bass part), to be rendered in Ableton as WAVs named after the MIDI "
                 f"files. Run: python tools/content/import_ableton.py content/imports/{i['level_id']}.json --check, then without --check, then "
                 f"python tools/content/build.py {i['level_id']}. The mission is rewired to these clips in a follow-up, as mission 1 was. Names are provisional. "
                 f"Levels as in first_watch.json: drums and bass peak at -4 dBFS, bass RMS-matched to -17 dBFS where that peak allows, backing at -3 dBFS, then a global trim of -7 dB.")
    sounds = []
    for fam, label in (("kick", "Kick"), ("snare", "Snare"), ("bass", "Bass")):
        for v in "abc":
            sounds.append((f"{p}_{fam}_{v}", fam, f"{title} {label} {v.upper()}"))
    sounds.append((f"{p}_pad", "other", f"{title} Pad"))
    sounds.append((f"{p}_hats", "other", f"{title} Hats"))
    bass_src = (f"the new root-note line (the mission has no bass phase)" if i["new_bass"] else f"the default bass line {i['bass']}")
    fill_src = f" with {i['fill']} replacing bar 8" if i["fill"] else ""
    lines = ["{", f' "note": {j(note_text)},', f' "source_dir": {j("midi_export/" + i["folder_name"])},', ' "bars": 8,', ' "levels": {']
    items = list(LEVELS_RULE.items())
    for k, (fam, rule) in enumerate(items):
        lines.append(f'  {j(fam)}: {j(rule)}{"," if k < len(items) - 1 else ""}')
    lines += [" },", ' "trim_db": -7.0,', ' "end_fade_ms": 10,', ' "sounds": [']
    for k, (sid, fam, nm) in enumerate(sounds):
        lines.append(f'  {{"id": {j(sid)}, "family": {j(fam)}, "name": {j(nm)}}}{"," if k < len(sounds) - 1 else ""}')
    lines += [" ],", ' "clips": [']
    clips = []
    for v in "abc":
        V = v.upper()
        clips.append(
            f'  {{"id": {j(f"{p}_groove_{v}")}, "kind": "groove", "name": {j(f"{title} Groove {V}")},\n'
            f'   "note": {j(f"Kick_{V} with Snare_{V}: " + (f"the default groove {i['groove']} tiled to 8 bars{fill_src}." if v == "a" else "rule-based variation of Kick_A and Snare_A (kick: a hit added, moved or dropped every two bars; snare: a ghost, a moved backbeat or a beat 4 hit)."))},\n'
            f'   "parts": {{"kick": {{"midi": "Kick_{V}.mid", "renders": {{{j(f"{p}_kick_{v}")}: "Kick_{V}.wav"}}}},\n'
            f'             "snare": {{"midi": "Snare_{V}.mid", "renders": {{{j(f"{p}_snare_{v}")}: "Snare_{V}.wav"}}}}}}}}')
    for v in "abc":
        V = v.upper()
        txt = (f"Bass_A: {bass_src}, 8 bars." if v == "a" else "Bass_%s: a rule-based variation of Bass_A (a note moved to the fifth or octave, a long note split or two tied), C# natural minor." % V)
        clips.append(
            f'  {{"id": {j(f"{p}_bass_{v}")}, "kind": "bass", "name": {j(f"{title} Bass {V}")}, "key": "C# minor",\n'
            f'   "note": {j(txt)},\n'
            f'   "parts": {{"bass": {{"midi": "Bass_{V}.mid", "renders": {{{j(f"{p}_bass_{v}")}: "Bass_{V}.wav"}}}}}}}}')
    back = f"Other_Pad and Other_Hats: the backing {i['acc']}, the chords and the hi-hats rendered separately."
    if long_other:
        back += (f" The exported MIDI is {i['acc_bars']} bars long (render all of it); this manifest imports the first 8 bars (bars: 8). "
                 f"Import the full length with a second manifest whose bars is {i['acc_bars']}.")
    clips.append(
        f'  {{"id": {j(f"{p}_backing")}, "kind": "accompaniment", "name": {j(f"{title} Backing")}, "key": "C# minor", "audio_only": true,\n'
        f'   "note": {j(back)},\n'
        f'   "parts": {{"other": {{"renders": {{{j(f"{p}_pad")}: "Other_Pad.wav", {j(f"{p}_hats")}: "Other_Hats.wav"}}}}}}}}')
    lines.append(",\n".join(clips))
    lines += [" ]", "}", ""]
    return "\n".join(lines)


# --- entry points -----------------------------------------------------------------------------------------------

def export_all(out_dir: Path | None = None, imports_dir: Path | None = None, levels=LEVELS, manifests: bool = True) -> dict[str, dict]:
    """Write the export for `levels` (numbers) into out_dir (default midi_export/) and the manifests into imports_dir
    (default content/imports/; skipped when manifests is False). Returns {level_id: info}."""
    out_dir = Path(out_dir) if out_dir else EXPORT_DIR
    if imports_dir is None and manifests:
        imports_dir = IMPORTS_DIR
    result = {}
    for number in levels:
        info = build_mission(int(number), out_dir, Path(imports_dir) if manifests else None)
        result[info["level_id"]] = info
    write_text(out_dir / "README.md", overview_readme())
    return result


def parse_levels(args: list[str]) -> list[int]:
    out = []
    for a in args:
        m = re.fullmatch(r"(?:level_)?0*(\d+)", a)
        if not m or not 2 <= int(m.group(1)) <= 10:
            raise ContentError(f"'{a}' is not a mission from 2 to 10 (level_02 ... level_10)")
        out.append(int(m.group(1)))
    return out or list(LEVELS)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("levels", nargs="*", help="level_02 ... level_10 (default: all)")
    ap.add_argument("--out", help="output folder (default midi_export/)")
    ap.add_argument("--imports", help="manifest folder (default content/imports/)")
    args = ap.parse_args()
    try:
        result = export_all(Path(args.out) if args.out else None, Path(args.imports) if args.imports else None, parse_levels(args.levels))
    except ContentError as exc:
        print(f"ERROR {exc}")
        return 1
    for lid, info in result.items():
        print(f"{lid}  {info['folder_name']}: {len(info['files'])} files "
              f"(groove {info['groove']}, fill {info['fill'] or '-'}, bass {info['bass'] or 'new root line'}, backing {info['acc']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
