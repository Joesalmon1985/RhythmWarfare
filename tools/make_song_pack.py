"""Build a Rhythm Warfare song pack (level.json + four aligned placeholder stems).

Two sources are supported. Run from the project root with `python -I` because both read
untrusted downloaded data (this script only reads bytes/CSV/JSON from them, never code):

1. A MIDI pack (the owner's per-lane MIDI files plus Authoring_Manifest.json), the source of
   truth for a real level. Every positive-velocity note-on in the kick and snare files is one
   tap; every bass note-on is a tap (< 480 ticks) or a hold (>= 480 ticks, duration = note
   length). Nothing is subsetted. If Player_Chart_Fragment.json is present the generated chart
   must equal it exactly, and sections come from the MIDI section markers.

       python -I tools/make_song_pack.py --midi-pack <dir> --out songs/level_01 \
           --level-id level_01 --title "First Contact" --seed 27

2. The 174 BPM clip library (01_Assembly_Placements.csv + MIDI clips), for placeholder packs:
   a bar range is assembled from the placement sheet, and a deterministic, evenly spread,
   strong-beat-preferring subset of the real hits is charted (--kicks-per-bar etc., or
   --all-hits).

       python -I tools/make_song_pack.py --library <dir> --out songs/test_16 --bars 513-528 \
           --seed 7 --level-id test_16 --title "Test: 16 bars" --all-hits

In both modes the enemy schedule mirrors the player's notes at a seeded accuracy
(--enemy-profile mirror|ramp), the four stems are synthesised with numpy from every note,
encoded to Ogg Vorbis with ffmpeg, length-checked with ffprobe, and level.json is validated
the way the importer will.

Buttons: the game has four unlabelled buttons. Kick notes are button 1 and snare notes button 4;
bass notes carry a `button` (1 to 4) chosen from the note's MIDI pitch (lowest pitch in the
song on the left, highest on the right), so a bass line runs across all four buttons. A bass
note that would land on button 1 or 4 while a kick or snare is within HOLD_PRESS_GUARD_TICKS
of it (or inside its hold) is moved to the nearest inner button instead.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import json
import math
import random
import re
import shutil
import struct
import subprocess
import sys
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Sequence

import numpy as np

# --------------------------------------------------------------------------------------
# Musical constants (fixed by the PRD and the clip library)
# --------------------------------------------------------------------------------------
BPM = 174
TICKS_PER_BEAT = 960
BEATS_PER_BAR = 4
TICKS_PER_BAR = TICKS_PER_BEAT * BEATS_PER_BAR  # 3840
SECONDS_PER_TICK = 60.0 / (BPM * TICKS_PER_BEAT)
TAIL_SECONDS = 1.0

DRUM_TRACK = "13_Drums"
BASS_TRACKS = ["11_Sub", "09_Reese", "08_Growl"]  # in order of preference, per bar
CHORD_TRACKS = ["06_SynthChords", "03_StringEnsemble"]

# General MIDI percussion numbers (05_GM_Drum_Note_Map.csv plus the usual GM aliases).
GM_KICK = {35, 36}
GM_SNARE = {38, 40}
GM_RIM = {37}
GM_CLAP = {39}
GM_CLOSED_HAT = {42}
GM_PEDAL_HAT = {44}
GM_OPEN_HAT = {46}
GM_CRASH = {49, 57, 55, 52}
GM_RIDE = {51, 59, 53}
GM_TOMS = {41, 43, 45, 47, 48, 50}

# Clip-library chart rules.
HOLD_MIN_TICKS = TICKS_PER_BEAT          # a sub note >= 1 beat becomes a hold
HOLD_MAX_TICKS = 4 * TICKS_PER_BAR       # holds are clamped to 4 bars
BASS_GAP_TICKS = 480                     # minimum gap between a bass note's end and the next start
HOLD_PRESS_GUARD_TICKS = 240             # kicks/snares keep clear of a hold's press moment +/- this

LANE_ORDER = {"kick": 0, "snare": 1, "bass": 2}
LIBRARY_STEM_FILES = {"kick": "01_Kicks", "snare": "02_Snares", "bass": "03_Bass", "other": "04_Other"}

RULES = {
    "airfield_limit": 5,
    "aircraft_limit": 5,
    "initial_airfields": 0,
    "tank_per_kick": 1,
    "infantry_per_snare": 5,
    "repair_budget_credits_per_side": 500,
    "song_end_result": "defeat",
}
BATTLEFIELD = "mvp_mirrored_01"
ROSTER = "openra_mvp_01"


# --------------------------------------------------------------------------------------
# Minimal Standard MIDI File parser (format 0/1, PPQ division, running status)
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class MidiNote:
    channel: int
    pitch: int
    velocity: int
    start: int   # chart ticks (960 per beat) relative to the file's bar 1
    end: int     # chart ticks, exclusive


@dataclass(frozen=True)
class NoteOn:
    channel: int
    pitch: int
    velocity: int
    tick: int    # chart ticks


@dataclass
class MidiFile:
    ppq: int
    fmt: int
    notes: list[MidiNote] = field(default_factory=list)       # note-on/off pairs
    note_ons: list[NoteOn] = field(default_factory=list)      # every positive-velocity note-on
    markers: list[tuple[int, str]] = field(default_factory=list)  # (chart tick, text) meta 0x06
    end_tick: int = 0                                         # latest track end, chart ticks


class MidiParseError(ValueError):
    pass


def _read_vlq(data: bytes, pos: int) -> tuple[int, int]:
    value = 0
    for _ in range(4):
        if pos >= len(data):
            raise MidiParseError("truncated variable-length quantity")
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            return value, pos
    raise MidiParseError("variable-length quantity longer than 4 bytes")


def _parse_track(chunk: bytes, ppq: int, out: MidiFile) -> None:
    """Walk one MTrk chunk body, appending notes, note-ons and markers (in chart ticks)."""
    open_notes: dict[tuple[int, int], list[tuple[int, int]]] = {}  # (ch, pitch) -> [(start_tick, vel)]
    pos = 0
    abs_tick = 0
    running_status: int | None = None

    def to_chart(tick: int) -> int:
        return int(round(tick * TICKS_PER_BEAT / ppq))

    def close(channel: int, pitch: int, tick: int) -> None:
        stack = open_notes.get((channel, pitch))
        if stack:
            start, vel = stack.pop(0)
            if tick > start:
                out.notes.append(MidiNote(channel, pitch, vel, to_chart(start), to_chart(tick)))

    while pos < len(chunk):
        delta, pos = _read_vlq(chunk, pos)
        abs_tick += delta
        if pos >= len(chunk):
            raise MidiParseError("event missing after delta time")
        status = chunk[pos]
        if status & 0x80:
            pos += 1
            if status < 0xF0:
                running_status = status
        else:
            if running_status is None:
                raise MidiParseError("data byte without running status")
            status = running_status

        if status == 0xFF:  # meta event
            if pos >= len(chunk):
                raise MidiParseError("truncated meta event")
            meta_type = chunk[pos]
            pos += 1
            length, pos = _read_vlq(chunk, pos)
            payload = chunk[pos:pos + length]
            pos += length
            if meta_type == 0x06:
                out.markers.append((to_chart(abs_tick), payload.decode("utf-8", "replace").strip()))
            if meta_type == 0x2F:  # end of track
                break
            continue
        if status in (0xF0, 0xF7):  # sysex / escape
            length, pos = _read_vlq(chunk, pos)
            pos += length
            continue
        if status >= 0xF0:  # other system messages carry no data we care about
            continue

        kind = status & 0xF0
        channel = status & 0x0F
        if kind in (0xC0, 0xD0):  # program change / channel pressure: one data byte
            pos += 1
            continue
        if pos + 2 > len(chunk):
            raise MidiParseError("truncated channel message")
        d1, d2 = chunk[pos], chunk[pos + 1]
        pos += 2
        if kind == 0x90 and d2 > 0:
            open_notes.setdefault((channel, d1), []).append((abs_tick, d2))
            out.note_ons.append(NoteOn(channel, d1, d2, to_chart(abs_tick)))
        elif kind == 0x80 or (kind == 0x90 and d2 == 0):
            close(channel, d1, abs_tick)

    # Notes never switched off end where the track ends.
    for (channel, pitch), stack in open_notes.items():
        for start, vel in stack:
            if abs_tick > start:
                out.notes.append(MidiNote(channel, pitch, vel, to_chart(start), to_chart(abs_tick)))
    out.end_tick = max(out.end_tick, to_chart(abs_tick))


def parse_midi_file(path: Path) -> MidiFile:
    data = path.read_bytes()
    if data[:4] != b"MThd":
        raise MidiParseError(f"{path.name}: not a Standard MIDI File")
    header_len, fmt, ntracks, division = struct.unpack(">IHHH", data[4:14])
    if fmt not in (0, 1):
        raise MidiParseError(f"{path.name}: unsupported MIDI format {fmt}")
    if division & 0x8000:
        raise MidiParseError(f"{path.name}: SMPTE time division is not supported")
    if division == 0:
        raise MidiParseError(f"{path.name}: zero PPQ")
    out = MidiFile(ppq=division, fmt=fmt)
    pos = 8 + header_len
    seen = 0
    while pos + 8 <= len(data) and seen < ntracks:
        chunk_id = data[pos:pos + 4]
        chunk_len = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        body = data[pos + 8:pos + 8 + chunk_len]
        pos += 8 + chunk_len
        if chunk_id == b"MTrk":
            _parse_track(body, division, out)
            seen += 1
    out.notes.sort(key=lambda n: (n.start, n.channel, n.pitch))
    out.note_ons.sort(key=lambda n: (n.tick, n.channel, n.pitch))
    out.markers.sort(key=lambda m: m[0])
    return out


def parse_midi(path: Path) -> list[MidiNote]:
    return parse_midi_file(path).notes


# --------------------------------------------------------------------------------------
# Placement sheet -> notes in the requested bar range (clip-library mode)
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Placement:
    start_bar: int
    end_bar: int
    track: str
    clip: str
    clip_bars: int
    repeats: int
    path: Path


@dataclass(frozen=True)
class PlacedNote:
    track: str
    pitch: int
    velocity: int
    tick: int       # pack-local chart tick (pack bar 1 = tick 0)
    end: int        # pack-local chart tick, exclusive, may exceed the pack end


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def load_placements(library: Path) -> list[Placement]:
    sheet = library / "01_Assembly_Placements.csv"
    if not sheet.is_file():
        sys.exit(f"error: {sheet} not found; --library must be the extracted folder that holds it")
    lib_root = library.resolve()
    placements: list[Placement] = []
    for row in read_csv_rows(sheet):
        rel = row["relative_path"].strip().replace("\\", "/")
        full = (library / rel).resolve()
        if lib_root not in full.parents:
            sys.exit(f"error: placement path escapes the library: {rel}")
        placements.append(Placement(
            start_bar=int(row["start_bar"]), end_bar=int(row["end_bar"]), track=row["track"].strip(),
            clip=row["clip"].strip(), clip_bars=int(row["clip_bars"]), repeats=int(row["repeats"]),
            path=full,
        ))
    return placements


def assemble_notes(placements: Sequence[Placement], first_bar: int, last_bar: int) -> list[PlacedNote]:
    """Every note that STARTS inside global bars [first_bar, last_bar], in pack-local ticks."""
    pack_offset = (first_bar - 1) * TICKS_PER_BAR
    range_start = pack_offset
    range_end = last_bar * TICKS_PER_BAR
    cache: dict[Path, list[MidiNote]] = {}
    out: list[PlacedNote] = []
    for p in placements:
        if p.end_bar < first_bar or p.start_bar > last_bar:
            continue
        if p.path not in cache:
            cache[p.path] = parse_midi(p.path)
        clip_notes = cache[p.path]
        clip_len = p.clip_bars * TICKS_PER_BAR
        for rep in range(p.repeats):
            base = (p.start_bar - 1 + rep * p.clip_bars) * TICKS_PER_BAR
            if base >= range_end or base + clip_len <= range_start:
                continue
            for n in clip_notes:
                g_start = base + n.start
                if g_start < range_start or g_start >= range_end:
                    continue
                g_end = base + min(n.end, clip_len)  # a clip never rings past its own length
                out.append(PlacedNote(p.track, n.pitch, n.velocity, g_start - pack_offset, g_end - pack_offset))
    out.sort(key=lambda n: (n.tick, n.track, n.pitch))
    return out


def bars_covered(placements: Sequence[Placement], track: str, first_bar: int, last_bar: int) -> set[int]:
    bars: set[int] = set()
    for p in placements:
        if p.track != track:
            continue
        for bar in range(max(p.start_bar, first_bar), min(p.end_bar, last_bar) + 1):
            bars.add(bar)
    return bars


# --------------------------------------------------------------------------------------
# Chart selection (clip-library mode)
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Hit:
    tick: int
    velocity: int
    duration: int = 0   # bass only (chart ticks)
    pitch: int = 0


def beat_score(tick: int, lane: str) -> int:
    """Higher is 'stronger': quarter-note beats first (downbeat best), then 8ths, then 16ths."""
    pos = tick % TICKS_PER_BAR
    beat, sub = divmod(pos, TICKS_PER_BEAT)
    if sub == 0:
        if beat == 0:
            return 6
        if lane == "snare":
            return 5 if beat in (1, 3) else 4   # backbeat snares read best
        return 5 if beat == 2 else 4
    if sub == TICKS_PER_BEAT // 2:
        return 3
    if sub % (TICKS_PER_BEAT // 4) == 0:
        return 2
    if sub % (TICKS_PER_BEAT // 8) == 0:
        return 1
    return 0


def spread_select(cands: Sequence[Hit], budget: int, span_ticks: int,
                  key_fn: Callable[[Hit], tuple[int, ...]], rng: random.Random) -> list[Hit]:
    """Keep up to `budget` of `cands` (sorted by tick), one per equal time slot where possible.

    Within a slot the best key wins; ties break on a seeded jitter so the result is reproducible.
    If some slots are empty, a second pass tops up from the strongest leftovers that keep at
    least half a slot of distance from everything already chosen. Hits are never invented.
    """
    cands = sorted(cands, key=lambda h: h.tick)
    if budget >= len(cands):
        return list(cands)
    if budget <= 0:
        return []
    jitter = [rng.random() for _ in cands]
    slot = span_ticks / budget
    best: dict[int, int] = {}
    for i, h in enumerate(cands):
        s = min(int(h.tick // slot), budget - 1)
        if s not in best or (key_fn(h), jitter[i]) > (key_fn(cands[best[s]]), jitter[best[s]]):
            best[s] = i
    chosen = set(best.values())
    if len(chosen) < budget:
        chosen_ticks = sorted(cands[i].tick for i in chosen)
        min_gap = slot / 2
        rest = sorted((i for i in range(len(cands)) if i not in chosen),
                      key=lambda i: (key_fn(cands[i]), jitter[i]), reverse=True)
        for i in rest:
            t = cands[i].tick
            k = bisect.bisect_left(chosen_ticks, t)
            near = min(
                abs(t - chosen_ticks[k - 1]) if k > 0 else math.inf,
                abs(chosen_ticks[k] - t) if k < len(chosen_ticks) else math.inf,
            )
            if near >= min_gap:
                chosen.add(i)
                bisect.insort(chosen_ticks, t)
                if len(chosen) >= budget:
                    break
    return sorted((cands[i] for i in chosen), key=lambda h: h.tick)


def unique_hits(notes: Iterable[PlacedNote], pitches: set[int]) -> list[Hit]:
    """One candidate per tick (loudest velocity) for the given GM note numbers."""
    by_tick: dict[int, int] = {}
    for n in notes:
        if n.pitch in pitches:
            by_tick[n.tick] = max(by_tick.get(n.tick, 0), n.velocity)
    return [Hit(t, v) for t, v in sorted(by_tick.items())]


def bass_candidates(notes: Iterable[PlacedNote]) -> list[Hit]:
    """One candidate per start tick: the longest note starting there (lowest pitch on ties)."""
    by_tick: dict[int, Hit] = {}
    for n in notes:
        h = Hit(n.tick, n.velocity, n.end - n.tick, n.pitch)
        cur = by_tick.get(n.tick)
        if cur is None or (h.duration, -h.pitch) > (cur.duration, -cur.pitch):
            by_tick[n.tick] = h
    return [by_tick[t] for t in sorted(by_tick)]


@dataclass(frozen=True)
class BassNote:
    tick: int
    kind: str          # "tap" or "hold"
    duration: int      # hold length in ticks, 0 for taps
    pitch: int = 0     # MIDI pitch, used to spread the bass line over the four buttons


def resolve_bass(selected: Sequence[Hit], duration_ticks: int) -> list[BassNote]:
    """Turn selected sub notes into taps/holds that never overlap and all end inside the song."""
    sel = sorted(selected, key=lambda h: h.tick)
    out: list[BassNote] = []
    prev_end = -math.inf
    for i, h in enumerate(sel):
        if h.tick < prev_end + BASS_GAP_TICKS:
            continue  # too close to the previous bass note: drop it
        dur = min(h.duration, HOLD_MAX_TICKS, duration_ticks - h.tick)
        if i + 1 < len(sel):
            dur = min(dur, sel[i + 1].tick - BASS_GAP_TICKS - h.tick)
        if dur >= HOLD_MIN_TICKS:
            out.append(BassNote(h.tick, "hold", dur, h.pitch))
            prev_end = h.tick + dur
        else:
            out.append(BassNote(h.tick, "tap", 0, h.pitch))
            prev_end = h.tick
    return out


# --------------------------------------------------------------------------------------
# Buttons (four unlabelled touch buttons; kick = 1, snare = 4, bass anywhere)
# --------------------------------------------------------------------------------------
BUTTONS = 4
FIXED_BUTTON = {"kick": 1, "snare": 4}


def pitch_buttons(pitches: Iterable[int]) -> dict[int, int]:
    """Distinct pitches, low to high, spread evenly over buttons 1..4 (one pitch: button 2)."""
    distinct = sorted(set(pitches))
    if not distinct:
        return {}
    if len(distinct) == 1:
        return {distinct[0]: 2}
    n = len(distinct)
    return {pch: 1 + int(round((BUTTONS - 1) * i / (n - 1))) for i, pch in enumerate(distinct)}


def assign_buttons(chart: list[dict], pitches: dict[int, int]) -> None:
    """Set `button` on every note in place. `pitches` maps a bass note's tick to its MIDI pitch.

    Kick and snare are fixed. A bass note takes the button of its pitch, then moves inward (1 -> 2,
    4 -> 3) when a kick or snare on that button lies within HOLD_PRESS_GUARD_TICKS of its press or
    anywhere inside its hold, so one button is never asked for two things at once.
    """
    by_pitch = pitch_buttons(pitches.values())
    drum_ticks: dict[int, list[int]] = {1: [], 4: []}
    for n in chart:
        if n["lane"] in FIXED_BUTTON:
            n["button"] = FIXED_BUTTON[n["lane"]]
            drum_ticks[n["button"]].append(n["tick"])
    for ticks in drum_ticks.values():
        ticks.sort()
    for n in chart:
        if n["lane"] != "bass":
            continue
        button = by_pitch.get(pitches.get(n["tick"], 0), 2)
        if button in drum_ticks:
            start = n["tick"] - HOLD_PRESS_GUARD_TICKS
            end = n["tick"] + int(n.get("duration_ticks", 0)) + HOLD_PRESS_GUARD_TICKS
            ticks = drum_ticks[button]
            k = bisect.bisect_left(ticks, start)
            if k < len(ticks) and ticks[k] <= end:
                button = 2 if button == 1 else 3
        n["button"] = button


def near_hold_press(tick: int, hold_starts: Sequence[int]) -> bool:
    k = bisect.bisect_left(hold_starts, tick - HOLD_PRESS_GUARD_TICKS)
    return k < len(hold_starts) and hold_starts[k] <= tick + HOLD_PRESS_GUARD_TICKS


# --------------------------------------------------------------------------------------
# Enemy schedule
# --------------------------------------------------------------------------------------
ENEMY_PROFILES = ("mirror", "ramp")


def even_subset(count: int, fraction: float, rng: random.Random) -> list[bool]:
    """A keep-mask with round(count*fraction) True entries, the False ones spread evenly."""
    keep = [True] * count
    drop = count - int(round(count * fraction))
    if drop <= 0 or count == 0:
        return keep
    phase = rng.random()
    for j in range(drop):
        idx = min(int((j + phase) * count / drop), count - 1)
        while idx < count and not keep[idx]:
            idx += 1
        if idx < count:
            keep[idx] = False
    return keep


def enemy_schedule(chart: Sequence[dict], sections: Sequence[dict], bars: int, profile: str,
                   accuracy: float, ramp_start: float, ramp_end: float,
                   rng: random.Random) -> tuple[list[dict], list[tuple[str, float]]]:
    """Mirror the player's notes as enemy events, keeping a seeded fraction of them.

    mirror: one accuracy for the whole song.
    ramp:   per section, accuracy interpolates linearly from ramp_start at bar 1 to ramp_end
            at the last bar, evaluated at the section's middle bar, so early bars are easy.
    Returns the events (ids assigned, sorted) and the (section id, accuracy) pairs used.
    """
    chart = sorted(chart, key=lambda n: (n["tick"], LANE_ORDER[n["lane"]]))
    used: list[tuple[str, float]] = []
    kept: list[dict] = []
    if profile == "mirror":
        keep = even_subset(len(chart), accuracy, rng)
        kept = [n for n, k in zip(chart, keep) if k]
        used.append(("all", accuracy))
    elif profile == "ramp":
        for sec in sections:
            start = int(sec["start_tick"])
            end = start + int(sec["length_bars"]) * TICKS_PER_BAR
            mid_bar = start / TICKS_PER_BAR + (int(sec["length_bars"]) - 1) / 2.0  # 0-based
            frac = mid_bar / (bars - 1) if bars > 1 else 1.0
            acc = ramp_start + (ramp_end - ramp_start) * frac
            notes = [n for n in chart if start <= n["tick"] < end]
            keep = even_subset(len(notes), acc, rng)
            kept.extend(n for n, k in zip(notes, keep) if k)
            used.append((str(sec["id"]), acc))
    else:
        raise ValueError(f"unknown enemy profile {profile}")
    kept.sort(key=lambda n: (n["tick"], LANE_ORDER[n["lane"]]))
    events = [{"id": f"e{i + 1:03d}", "tick": n["tick"], "action": n["lane"]} for i, n in enumerate(kept)]
    return events, used


# --------------------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------------------
def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s or "section"


def dedupe_ids(pieces: Sequence[tuple[int, int, str]]) -> list[dict[str, int | str]]:
    """(start_tick, length_bars, name) -> section dicts with unique slug ids."""
    sections: list[dict[str, int | str]] = []
    used: set[str] = set()
    for start_tick, length_bars, name in pieces:
        sid = slug(name)
        if sid in used:
            sid = f"{sid}_{start_tick // TICKS_PER_BAR + 1}"
        used.add(sid)
        sections.append({"id": sid, "start_tick": start_tick, "length_bars": length_bars})
    return sections


def sixteen_bar_sections(bars: int) -> list[dict[str, int | str]]:
    pieces: list[tuple[int, int, str]] = []
    bar = 0
    while bar < bars:
        length = min(16, bars - bar)
        pieces.append((bar * TICKS_PER_BAR, length, f"part_{len(pieces) + 1}"))
        bar += length
    return dedupe_ids(pieces)


def build_sections_from_roadmap(library: Path, first_bar: int, last_bar: int) -> list[dict[str, int | str]]:
    roadmap = library / "02_Section_Roadmap.csv"
    rows: list[tuple[int, int, str]] = []
    if roadmap.is_file():
        for row in read_csv_rows(roadmap):
            a, b = int(row["start_bar"]), int(row["end_bar"])
            a2, b2 = max(a, first_bar), min(b, last_bar)
            if a2 <= b2:
                rows.append((a2, b2, row.get("section", "").strip() or f"bars_{a2}_{b2}"))
    rows.sort()
    contiguous = bool(rows) and rows[0][0] == first_bar and rows[-1][1] == last_bar and all(
        rows[i][1] + 1 == rows[i + 1][0] for i in range(len(rows) - 1))
    if not contiguous:
        return sixteen_bar_sections(last_bar - first_bar + 1)
    return dedupe_ids([((a - first_bar) * TICKS_PER_BAR, b - a + 1, name) for a, b, name in rows])


def sections_from_markers(markers: Sequence[tuple[int, str]], duration_ticks: int) -> list[dict[str, int | str]] | None:
    """Sections bounded by MIDI markers; None if they do not tile the song in whole bars."""
    marks = sorted((t, name) for t, name in markers if 0 <= t < duration_ticks)
    if not marks or marks[0][0] != 0:
        return None
    pieces: list[tuple[int, int, str]] = []
    for i, (t, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else duration_ticks
        if end <= t or (end - t) % TICKS_PER_BAR != 0:
            return None
        pieces.append((t, (end - t) // TICKS_PER_BAR, name))
    return dedupe_ids(pieces)


# --------------------------------------------------------------------------------------
# Audio synthesis
# --------------------------------------------------------------------------------------
def midi_to_hz(pitch: int) -> float:
    return 440.0 * 2.0 ** ((pitch - 69) / 12.0)


def tick_to_sample(tick: int, sr: int) -> int:
    return int(round(tick * SECONDS_PER_TICK * sr))


def add_at(buf: np.ndarray, start: int, sig: np.ndarray) -> None:
    if start >= len(buf) or start < 0:
        return
    n = min(len(sig), len(buf) - start)
    buf[start:start + n] += sig[:n].astype(np.float32)


def shaped_noise(rng: np.random.Generator, n: int, sr: int, lo: float, hi: float) -> np.ndarray:
    """White noise restricted to [lo, hi] Hz with soft edges, normalised to peak 1."""
    noise = rng.standard_normal(n)
    spec = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    width = max((hi - lo) * 0.15, 50.0)
    mask = 1.0 / (1.0 + np.exp(-(freqs - lo) / width)) * (1.0 - 1.0 / (1.0 + np.exp(-(freqs - hi) / width)))
    out = np.fft.irfft(spec * mask, n)
    peak = float(np.max(np.abs(out)))
    return out / peak if peak > 0 else out


def vel_gain(velocity: int) -> float:
    return 0.55 + 0.45 * (velocity / 127.0)


def synth_kick(sr: int, rng: np.random.Generator, velocity: int) -> np.ndarray:
    n = int(0.35 * sr)
    t = np.arange(n) / sr
    freq = 45.0 + 115.0 * np.exp(-t / 0.013)            # 160 -> 45 Hz, mostly done by 40 ms
    phase = 2.0 * np.pi * np.cumsum(freq) / sr
    body = np.sin(phase) * np.exp(-t / 0.085)           # ~ -50 dB at 350 ms, audibly ~250 ms
    click_n = int(0.002 * sr)
    click = np.zeros(n)
    click[:click_n] = rng.standard_normal(click_n) * np.linspace(1.0, 0.0, click_n) * 0.35
    return (body + click) * 0.95 * vel_gain(velocity)


def synth_snare(sr: int, rng: np.random.Generator, velocity: int, kind: str) -> np.ndarray:
    if kind == "rim":
        n = int(0.06 * sr)
        t = np.arange(n) / sr
        noise = shaped_noise(rng, n, sr, 1500.0, 6000.0) * np.exp(-t / 0.012)
        tone = np.sin(2.0 * np.pi * 420.0 * t) * np.exp(-t / 0.01)
        return (noise * 0.7 + tone * 0.5) * 0.45 * vel_gain(velocity)
    n = int(0.18 * sr)
    t = np.arange(n) / sr
    noise = shaped_noise(rng, n, sr, 1200.0, 7500.0) * np.exp(-t / 0.045)
    if kind == "clap":
        burst = np.zeros(n)
        for k in range(3):
            off = int(0.011 * k * sr)
            burst[off:] += noise[:n - off] * (0.6 if k < 2 else 1.0)
        noise = burst / max(float(np.max(np.abs(burst))), 1e-9)
    tone = np.sin(2.0 * np.pi * 190.0 * t) * np.exp(-t / 0.04)
    return (noise * 0.8 + tone * 0.6) * 0.85 * vel_gain(velocity)


def synth_hat(sr: int, rng: np.random.Generator, velocity: int, kind: str) -> np.ndarray:
    if kind == "crash":
        n, decay, lo, hi, amp = int(1.2 * sr), 0.3, 3000.0, 14000.0, 0.5
    elif kind == "ride":
        n, decay, lo, hi, amp = int(0.45 * sr), 0.12, 4000.0, 12000.0, 0.35
    elif kind == "open":
        n, decay, lo, hi, amp = int(0.22 * sr), 0.06, 6000.0, 16000.0, 0.35
    elif kind == "pedal":
        n, decay, lo, hi, amp = int(0.02 * sr), 0.006, 6000.0, 16000.0, 0.25
    else:  # closed
        n, decay, lo, hi, amp = int(0.03 * sr), 0.008, 6000.0, 16000.0, 0.35
    t = np.arange(n) / sr
    return shaped_noise(rng, n, sr, lo, hi) * np.exp(-t / decay) * amp * vel_gain(velocity)


TOM_HZ = {41: 110.0, 43: 130.0, 45: 150.0, 47: 170.0, 48: 190.0, 50: 210.0}


def synth_tom(sr: int, velocity: int, pitch: int) -> np.ndarray:
    base = TOM_HZ.get(pitch, 160.0)
    n = int(0.28 * sr)
    t = np.arange(n) / sr
    freq = base * (1.0 + 0.35 * np.exp(-t / 0.03))
    phase = 2.0 * np.pi * np.cumsum(freq) / sr
    return np.sin(phase) * np.exp(-t / 0.12) * 0.6 * vel_gain(velocity)


def synth_riser(sr: int, rng: np.random.Generator, n: int) -> np.ndarray:
    """Band-passed noise whose centre climbs 200 Hz -> 6 kHz while the level swells, cut at the end."""
    hop = max(n // 64, 1)
    win_n = 2 * hop
    window = np.hanning(win_n)
    out = np.zeros(n + win_n)
    steps = int(math.ceil(n / hop))
    for i in range(steps):
        frac = i / max(steps - 1, 1)
        centre = 200.0 * (30.0 ** frac)
        chunk = shaped_noise(rng, win_n, sr, centre / 1.4, centre * 1.4) * window
        out[i * hop:i * hop + win_n] += chunk
    out = out[:n]
    env = np.linspace(0.0, 1.0, n) ** 2 * 0.45
    return out * env


def adsr(n: int, sr: int, sustain: float = 0.85) -> np.ndarray:
    """Attack/decay to `sustain`, with 10 ms linear fades at both ends so nothing clicks."""
    fade = max(1, min(int(0.010 * sr), n // 2))
    env = np.full(n, sustain)
    decay_n = min(int(0.06 * sr), n)
    env[:decay_n] = sustain + (1.0 - sustain) * np.exp(-np.arange(decay_n) / (0.02 * sr))
    env[:fade] *= np.linspace(0.0, 1.0, fade, endpoint=False)
    env[n - fade:] *= np.linspace(1.0, 0.0, fade)
    return env


def synth_bass_note(sr: int, pitch: int, velocity: int, n: int) -> np.ndarray:
    n = max(n, int(0.03 * sr))
    t = np.arange(n) / sr
    f = midi_to_hz(pitch)
    sig = np.sin(2.0 * np.pi * f * t) + 0.12 * np.sin(4.0 * np.pi * f * t)
    return sig * adsr(n, sr) * 0.7 * vel_gain(velocity)


def synth_pad_bar(sr: int, pitches: Sequence[int], n: int) -> np.ndarray:
    t = np.arange(n) / sr
    sig = np.zeros(n)
    for p in pitches:
        f = midi_to_hz(p)
        sig += (np.sin(2.0 * np.pi * f * 1.001 * t) + np.sin(2.0 * np.pi * f * 0.999 * t)
                + 0.25 * np.sin(4.0 * np.pi * f * t) + 0.08 * np.sin(6.0 * np.pi * f * t))
    fade = max(1, min(int(0.06 * sr), n // 2))
    env = np.ones(n)
    env[:fade] = np.linspace(0.0, 1.0, fade, endpoint=False)
    env[n - fade:] = np.linspace(1.0, 0.0, fade)
    return sig * env * (0.11 / math.sqrt(max(len(pitches), 1)))


def finalize(buf: np.ndarray) -> np.ndarray:
    """Scale so the raw peak is at most 1, then a gentle tanh soft clip with peak 0.8."""
    peak = float(np.max(np.abs(buf))) if len(buf) else 0.0
    if peak > 1.0:
        buf = buf / peak
    out = np.tanh(buf.astype(np.float64)) * (0.8 / math.tanh(1.0))
    return np.clip(out, -0.8, 0.8)


def write_wav(path: Path, samples: np.ndarray, sr: int) -> None:
    pcm = np.round(samples * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


@dataclass
class StemPlan:
    """Everything the renderer needs: notes to voice on each stem, in pack-local ticks."""
    kicks: list[PlacedNote] = field(default_factory=list)
    snares: list[tuple[PlacedNote, str]] = field(default_factory=list)       # kind: snare/rim/clap
    bass: list[PlacedNote] = field(default_factory=list)
    percussion: list[tuple[PlacedNote, str]] = field(default_factory=list)   # kind: closed/pedal/open/crash/ride/tom
    pad_bars: list[list[int]] = field(default_factory=list)                  # chord pitches, one list per bar
    riser_ends: list[int] = field(default_factory=list)                      # ticks a 4-bar riser lands on
    file_names: dict[str, str] = field(default_factory=lambda: dict(LIBRARY_STEM_FILES))


def render_stems(plan: StemPlan, total_samples: int, sr: int, seed: int, out_dir: Path) -> dict[str, Path]:
    """Render the four stems (equal length) to WAV files; returns stem name -> path."""
    paths: dict[str, Path] = {}

    rng = np.random.default_rng(seed + 1)
    buf = np.zeros(total_samples, dtype=np.float32)
    for n in plan.kicks:
        add_at(buf, tick_to_sample(n.tick, sr), synth_kick(sr, rng, n.velocity))
    paths["kick"] = out_dir / f"{plan.file_names['kick']}.wav"
    write_wav(paths["kick"], finalize(buf), sr)

    rng = np.random.default_rng(seed + 2)
    buf = np.zeros(total_samples, dtype=np.float32)
    for n, kind in plan.snares:
        add_at(buf, tick_to_sample(n.tick, sr), synth_snare(sr, rng, n.velocity, kind))
    paths["snare"] = out_dir / f"{plan.file_names['snare']}.wav"
    write_wav(paths["snare"], finalize(buf), sr)

    buf = np.zeros(total_samples, dtype=np.float32)
    for n in plan.bass:
        s0 = tick_to_sample(n.tick, sr)
        s1 = min(tick_to_sample(n.end, sr), total_samples)
        if s1 > s0:
            add_at(buf, s0, synth_bass_note(sr, n.pitch, n.velocity, s1 - s0))
    paths["bass"] = out_dir / f"{plan.file_names['bass']}.wav"
    write_wav(paths["bass"], finalize(buf), sr)

    rng = np.random.default_rng(seed + 4)
    buf = np.zeros(total_samples, dtype=np.float32)
    for n, kind in plan.percussion:
        s = tick_to_sample(n.tick, sr)
        if kind == "tom":
            add_at(buf, s, synth_tom(sr, n.velocity, n.pitch))
        else:
            add_at(buf, s, synth_hat(sr, rng, n.velocity, kind))
    for bar, pitches in enumerate(plan.pad_bars):
        s0, s1 = tick_to_sample(bar * TICKS_PER_BAR, sr), tick_to_sample((bar + 1) * TICKS_PER_BAR, sr)
        if pitches:
            add_at(buf, s0, synth_pad_bar(sr, pitches[:6], s1 - s0))
    for end_tick in plan.riser_ends:
        start_tick = max(end_tick - 4 * TICKS_PER_BAR, 0)
        s0, s1 = tick_to_sample(start_tick, sr), tick_to_sample(end_tick, sr)
        if s1 > s0:
            add_at(buf, s0, synth_riser(sr, rng, s1 - s0))
    paths["other"] = out_dir / f"{plan.file_names['other']}.wav"
    write_wav(paths["other"], finalize(buf), sr)
    return paths


def encode_ogg(wav: Path, ogg: Path, sr: int) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libvorbis", "-q:a", "5",
           "-ar", str(sr), str(ogg)]
    subprocess.run(cmd, check=True)


def probe_duration(path: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)]
    res = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return float(res.stdout.strip())


# --------------------------------------------------------------------------------------
# Validation (the importer checks from PRD section 9 that apply to level.json itself)
# --------------------------------------------------------------------------------------
VALID_LANES = {"kick", "snare", "bass"}
VALID_TYPES = {"tap", "hold"}


def validate_level(level: dict, pack_dir: Path) -> list[str]:
    errors: list[str] = []
    if level.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    for key in ("level_id", "title", "bpm", "time_signature", "ticks_per_beat", "song_offset_ms",
                "duration_ticks", "seed", "stems", "battlefield", "roster", "rules", "sections",
                "notes", "enemy_events"):
        if key not in level:
            errors.append(f"missing key {key}")
    if errors:
        return errors
    duration = int(level["duration_ticks"])
    if duration <= 0:
        errors.append("duration_ticks must be positive")
    for stem in ("kick", "snare", "bass", "other"):
        rel = level["stems"].get(stem)
        if not rel:
            errors.append(f"missing stem {stem}")
            continue
        full = (pack_dir / rel).resolve()
        if pack_dir.resolve() not in full.parents:
            errors.append(f"stem {stem} escapes the pack root: {rel}")
        elif not full.is_file():
            errors.append(f"stem file missing: {rel}")

    ids: set[str] = set()
    last_tick = -1
    button_busy_until: dict[int, int] = {}
    for note in level["notes"]:
        nid = note.get("id")
        if nid in ids:
            errors.append(f"duplicate note id {nid}")
        ids.add(nid)
        tick = note.get("tick")
        if not isinstance(tick, int) or tick < 0:
            errors.append(f"{nid}: tick must be a non-negative integer")
            continue
        if tick >= duration:
            errors.append(f"{nid}: tick {tick} is at or beyond the song end {duration}")
        if tick < last_tick:
            errors.append(f"{nid}: notes are not sorted by tick")
        last_tick = tick
        lane = note.get("lane")
        if lane not in VALID_LANES:
            errors.append(f"{nid}: invalid lane {lane!r}")
            continue
        ntype = note.get("type")
        if ntype not in VALID_TYPES:
            errors.append(f"{nid}: invalid type {ntype!r}")
            continue
        end = tick
        if ntype == "hold":
            dur = note.get("duration_ticks")
            if lane != "bass":
                errors.append(f"{nid}: only the bass lane may hold")
            if not isinstance(dur, int) or dur <= 0:
                errors.append(f"{nid}: hold needs a positive duration_ticks")
            else:
                end = tick + dur
                if end > duration:
                    errors.append(f"{nid}: hold ends at {end}, beyond the song end {duration}")
        elif "duration_ticks" in note:
            errors.append(f"{nid}: taps must not carry duration_ticks")
        button = note.get("button")
        if not isinstance(button, int) or not 1 <= button <= BUTTONS:
            errors.append(f"{nid}: button must be 1..{BUTTONS}")
            continue
        if lane in FIXED_BUTTON and button != FIXED_BUTTON[lane]:
            errors.append(f"{nid}: {lane} notes are played on button {FIXED_BUTTON[lane]}")
        if tick < button_busy_until.get(button, -1):
            errors.append(f"{nid}: overlaps the previous note on button {button}")
        button_busy_until[button] = max(end, tick + 1)

    eids: set[str] = set()
    last_tick = -1
    for ev in level["enemy_events"]:
        eid = ev.get("id")
        if eid in eids or eid in ids:
            errors.append(f"duplicate id {eid}")
        eids.add(eid)
        tick = ev.get("tick")
        if not isinstance(tick, int) or tick < 0:
            errors.append(f"{eid}: tick must be a non-negative integer")
            continue
        if tick >= duration:
            errors.append(f"{eid}: tick {tick} is at or beyond the song end {duration}")
        if tick < last_tick:
            errors.append(f"{eid}: enemy events are not sorted by tick")
        last_tick = tick
        if ev.get("action") not in VALID_LANES:
            errors.append(f"{eid}: invalid action {ev.get('action')!r}")

    expected = 0
    sids: set[str] = set()
    for sec in level["sections"]:
        sid = sec.get("id")
        if sid in sids:
            errors.append(f"duplicate section id {sid}")
        sids.add(sid)
        if sec.get("start_tick") != expected:
            errors.append(f"section {sid} starts at {sec.get('start_tick')}, expected {expected}")
        length = sec.get("length_bars")
        if not isinstance(length, int) or length <= 0:
            errors.append(f"section {sid}: length_bars must be a positive integer")
            break
        expected = int(sec.get("start_tick", expected)) + length * TICKS_PER_BAR
    if expected != duration:
        errors.append(f"sections cover ticks 0..{expected}, song is {duration}")

    # Flag three-touch chords (three buttons needed at one tick, holds included) for author review.
    by_tick: dict[int, set[int]] = {}
    holds = [(n["tick"], n["tick"] + int(n.get("duration_ticks", 0)), n.get("button"))
             for n in level["notes"] if n.get("type") == "hold"]
    for note in level["notes"]:
        by_tick.setdefault(note["tick"], set()).add(note.get("button"))
    for tick, buttons in by_tick.items():
        pressed = set(buttons)
        for start, end, button in holds:
            if start < tick < end:
                pressed.add(button)
        if len(pressed) >= 3:
            errors.append(f"three-touch chord at tick {tick}")
    return errors


# --------------------------------------------------------------------------------------
# Build results shared by both modes
# --------------------------------------------------------------------------------------
@dataclass
class Build:
    bars: int
    chart: list[dict]                    # notes without ids: tick, lane, type[, duration_ticks]
    sections: list[dict[str, int | str]]
    plan: StemPlan
    info: list[str]                      # extra summary lines
    bar_label: str                       # e.g. "global 513-832"


# --------------------------------------------------------------------------------------
# Mode 1: clip library + placement sheet
# --------------------------------------------------------------------------------------
def build_from_library(args: argparse.Namespace) -> Build:
    first_bar, last_bar = args.bars
    bars = last_bar - first_bar + 1
    duration_ticks = bars * TICKS_PER_BAR
    placements = load_placements(args.library)
    piece_end = max(p.end_bar for p in placements)
    if last_bar > piece_end:
        sys.exit(f"error: --bars ends at {last_bar} but the placement sheet ends at bar {piece_end}")

    notes = assemble_notes(placements, first_bar, last_bar)
    drums = [n for n in notes if n.track == DRUM_TRACK]

    # Bass source per bar: the first of 11_Sub / 09_Reese / 08_Growl that has a placement there.
    coverage = {t: bars_covered(placements, t, first_bar, last_bar) for t in BASS_TRACKS}
    bar_source: dict[int, str] = {}
    for bar in range(first_bar, last_bar + 1):
        for t in BASS_TRACKS:
            if bar in coverage[t]:
                bar_source[bar] = t
                break
    bass_notes = [n for n in notes if n.track in BASS_TRACKS
                  and bar_source.get(first_bar + n.tick // TICKS_PER_BAR) == n.track]
    source_counts = {t: sum(1 for b in bar_source.values() if b == t) for t in BASS_TRACKS}
    uncovered = bars - sum(source_counts.values())

    chord_track = next((t for t in CHORD_TRACKS if bars_covered(placements, t, first_bar, last_bar)), None)
    chords = sorted((n for n in notes if n.track == chord_track), key=lambda c: c.tick) if chord_track else []
    chord_bars = ({b - first_bar + 1 for b in bars_covered(placements, chord_track, first_bar, last_bar)}
                  if chord_track else set())

    # ---- chart selection (seeded) ----
    rng = random.Random(args.seed)
    kick_cands = unique_hits(drums, GM_KICK)
    snare_cands = unique_hits(drums, GM_SNARE)
    bass_cands = bass_candidates(bass_notes)
    n_kick_cands, n_snare_cands = len(kick_cands), len(snare_cands)

    if args.all_hits:
        bass_sel = bass_cands
    else:
        bass_sel = spread_select(bass_cands, int(math.floor(args.bass_per_bar * bars)), duration_ticks,
                                 lambda h: (h.duration, h.velocity, -h.pitch), rng)
    bass_chart = resolve_bass(bass_sel, duration_ticks)
    hold_starts = sorted(b.tick for b in bass_chart if b.kind == "hold")

    kick_cands = [h for h in kick_cands if not near_hold_press(h.tick, hold_starts)]
    if args.all_hits:
        kick_chart = kick_cands
    else:
        kick_chart = spread_select(kick_cands, int(math.floor(args.kicks_per_bar * bars)), duration_ticks,
                                   lambda h: (beat_score(h.tick, "kick"), h.velocity), rng)
    kick_ticks = {h.tick for h in kick_chart}
    snare_cands = [h for h in snare_cands if h.tick not in kick_ticks and not near_hold_press(h.tick, hold_starts)]
    if args.all_hits:
        snare_chart = snare_cands
    else:
        snare_chart = spread_select(snare_cands, int(math.floor(args.snares_per_bar * bars)), duration_ticks,
                                    lambda h: (beat_score(h.tick, "snare"), h.velocity), rng)

    chart: list[dict] = [{"tick": h.tick, "lane": "kick", "type": "tap"} for h in kick_chart]
    chart += [{"tick": h.tick, "lane": "snare", "type": "tap"} for h in snare_chart]
    bass_pitches: dict[int, int] = {}
    for b in bass_chart:
        entry: dict = {"tick": b.tick, "lane": "bass", "type": b.kind}
        if b.kind == "hold":
            entry["duration_ticks"] = b.duration
        chart.append(entry)
        bass_pitches[b.tick] = b.pitch
    assign_buttons(chart, bass_pitches)

    # ---- audio plan: every real hit ----
    plan = StemPlan(file_names=dict(LIBRARY_STEM_FILES))
    for n in drums:
        if n.pitch in GM_KICK:
            plan.kicks.append(n)
        elif n.pitch in GM_SNARE:
            plan.snares.append((n, "snare"))
        elif n.pitch in GM_RIM:
            plan.snares.append((n, "rim"))
        elif n.pitch in GM_CLAP:
            plan.snares.append((n, "clap"))
        elif n.pitch in GM_CLOSED_HAT:
            plan.percussion.append((n, "closed"))
        elif n.pitch in GM_PEDAL_HAT:
            plan.percussion.append((n, "pedal"))
        elif n.pitch in GM_OPEN_HAT:
            plan.percussion.append((n, "open"))
        elif n.pitch in GM_CRASH:
            plan.percussion.append((n, "crash"))
        elif n.pitch in GM_RIDE:
            plan.percussion.append((n, "ride"))
        else:
            plan.percussion.append((n, "tom"))
    plan.bass = list(bass_notes)
    drone = [49, 56]  # C#3 + G#3, the piece's home key
    last_pitches = drone
    for bar in range(1, bars + 1):
        b0 = (bar - 1) * TICKS_PER_BAR
        b1 = b0 + TICKS_PER_BAR
        on_downbeat = sorted({c.pitch for c in chords if c.tick < b0 + TICKS_PER_BEAT and c.end > b0})
        anywhere = sorted({c.pitch for c in chords if c.tick < b1 and c.end > b0})
        if on_downbeat:
            pitches = on_downbeat
        elif anywhere:
            pitches = anywhere
        elif bar in chord_bars:
            pitches = last_pitches     # a rest inside a chord placement: carry the chord
        else:
            pitches = drone
        last_pitches = pitches
        plan.pad_bars.append(pitches)

    gm_counts: dict[int, int] = {}
    for n in drums:
        gm_counts[n.pitch] = gm_counts.get(n.pitch, 0) + 1
    info = [
        "drum hits (GM):  " + ", ".join(f"{k}:{v}" for k, v in sorted(gm_counts.items())),
        "bass source:     " + ", ".join(f"{t} {c} bars" for t, c in source_counts.items() if c)
        + (f", {uncovered} bars without bass" if uncovered else "") + f"; {len(bass_cands)} notes",
        f"pad source:      {chord_track or 'drone only'} ({len(chords)} notes)",
        f"candidates:      kicks {n_kick_cands}, snares {n_snare_cands}",
    ]
    sections = build_sections_from_roadmap(args.library, first_bar, last_bar)
    return Build(bars, chart, sections, plan, info, f"global {first_bar}-{last_bar}")


# --------------------------------------------------------------------------------------
# Mode 2: per-lane MIDI pack with an authoring manifest
# --------------------------------------------------------------------------------------
# README chord table for the first level, used only for the placeholder pad in the "other" stem.
# Voicings sit in a higher register (C#4..F#5) so they support rather than double the bass.
CHORD_VOICINGS = {
    "C#m": [61, 64, 68],        # C#4 E4 G#4
    "A": [64, 69, 73],          # E4 A4 C#5
    "E": [64, 68, 71],          # E4 G#4 B4
    "B": [63, 66, 71],          # D#4 F#4 B4
    "G#7": [63, 66, 68, 72],    # D#4 F#4 G#4 B#4
}


def level_01_chord_for_bar(bar: int) -> str:
    """The README's optional chord table, bar (1-based) -> chord name."""
    if bar <= 8:
        return "C#m"
    if bar <= 16:
        return ["C#m", "A", "E", "G#7"][(bar - 9) // 2]
    if bar <= 32:
        return ["C#m", "A", "E", "B"][((bar - 17) // 2) % 4]
    if bar <= 40:
        return ["C#m", "A", "E", "B"][(bar - 33) // 2]
    if bar <= 56:
        return ["C#m", "A", "E", "B"][((bar - 41) // 2) % 4]
    if bar <= 62:
        return ["C#m", "A", "E"][(bar - 57) // 2]
    if bar == 63:
        return "G#7"
    return "C#m"


def load_manifest(pack: Path) -> dict:
    path = pack / "Authoring_Manifest.json"
    if not path.is_file():
        sys.exit(f"error: {path} not found; --midi-pack must be the folder that holds it")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if int(manifest.get("bpm", 0)) != BPM:
        sys.exit(f"error: manifest bpm {manifest.get('bpm')} differs from the game's fixed {BPM}")
    if int(manifest.get("ticks_per_beat", 0)) != TICKS_PER_BEAT:
        sys.exit(f"error: manifest ticks_per_beat {manifest.get('ticks_per_beat')} is not {TICKS_PER_BEAT}")
    if list(manifest.get("time_signature", [])) != [4, 4]:
        sys.exit("error: manifest time_signature is not 4/4")
    bars = int(manifest["bars"])
    if int(manifest.get("duration_ticks", bars * TICKS_PER_BAR)) != bars * TICKS_PER_BAR:
        sys.exit("error: manifest duration_ticks does not equal bars x 3840")
    for lane in ("kick", "snare", "bass"):
        rel = str(manifest["midi_files"][lane]).replace("\\", "/")
        full = (pack / rel).resolve()
        if pack.resolve() not in full.parents or not full.is_file():
            sys.exit(f"error: manifest midi file for {lane} is missing or escapes the pack: {rel}")
    return manifest


def pack_midi_path(pack: Path, manifest: dict, lane: str) -> Path:
    return (pack / str(manifest["midi_files"][lane]).replace("\\", "/")).resolve()


def chart_matches_fragment(chart: Sequence[dict], fragment_notes: Sequence[dict]) -> list[str]:
    """Differences between the generated notes (with ids) and the reference conversion."""
    diffs: list[str] = []
    if len(chart) != len(fragment_notes):
        diffs.append(f"note count {len(chart)} != fragment {len(fragment_notes)}")
    keys = ("id", "tick", "lane", "type", "duration_ticks")
    for i, (a, b) in enumerate(zip(chart, fragment_notes)):
        ta = tuple(a.get(k) for k in keys)
        tb = tuple(b.get(k) for k in keys)
        if ta != tb:
            diffs.append(f"note {i + 1}: generated {ta} != fragment {tb}")
            if len(diffs) >= 10:
                diffs.append("...")
                break
    return diffs


def build_from_midi_pack(args: argparse.Namespace) -> Build:
    pack: Path = args.midi_pack
    manifest = load_manifest(pack)
    bars = int(manifest["bars"])
    duration_ticks = bars * TICKS_PER_BAR
    rules = manifest.get("midi_interpretation", {}).get("bass", {})
    hold_min = int(rules.get("hold_if_duration_at_least_ticks", 480))

    files = {lane: parse_midi_file(pack_midi_path(pack, manifest, lane)) for lane in ("kick", "snare", "bass")}
    for lane, mf in files.items():
        if mf.ppq != TICKS_PER_BEAT:
            print(f"note: {lane} MIDI uses {mf.ppq} PPQ; ticks were rescaled to {TICKS_PER_BEAT}")
        bad = [n for n in mf.note_ons if n.tick >= duration_ticks]
        if bad:
            sys.exit(f"error: {lane} MIDI has {len(bad)} note-ons at or beyond the song end")

    # Kick / snare: every positive-velocity note-on is a tap (lane = file, not channel).
    chart: list[dict] = []
    for lane in ("kick", "snare"):
        chart += [{"tick": n.tick, "lane": lane, "type": "tap"} for n in files[lane].note_ons]
    # Bass: one event per note-on; duration from its note-off; hold if long enough.
    bass_mf = files["bass"]
    if len(bass_mf.notes) != len(bass_mf.note_ons):
        sys.exit(f"error: bass MIDI has {len(bass_mf.note_ons)} note-ons but {len(bass_mf.notes)} "
                 "note-on/off pairs; every note-on needs a note-off")
    taps = holds = 0
    bass_pitches: dict[int, int] = {}
    for n in bass_mf.notes:
        length = n.end - n.start
        if length >= hold_min:
            chart.append({"tick": n.start, "lane": "bass", "type": "hold", "duration_ticks": length})
            holds += 1
        else:
            chart.append({"tick": n.start, "lane": "bass", "type": "tap"})
            taps += 1
        bass_pitches[n.start] = n.pitch
    chart.sort(key=lambda n: (n["tick"], LANE_ORDER[n["lane"]]))
    assign_buttons(chart, bass_pitches)

    # Expected totals from the manifest.
    expected = manifest.get("player_event_counts", {})
    for lane, count in expected.items():
        got = sum(1 for n in chart if n["lane"] == lane)
        if int(count) != got:
            sys.exit(f"error: manifest expects {count} {lane} events, the MIDI gives {got}")
    if "bass_holds" in manifest and int(manifest["bass_holds"]) != holds:
        sys.exit(f"error: manifest expects {manifest['bass_holds']} bass holds, the MIDI gives {holds}")
    if "bass_taps" in manifest and int(manifest["bass_taps"]) != taps:
        sys.exit(f"error: manifest expects {manifest['bass_taps']} bass taps, the MIDI gives {taps}")

    # Sections: MIDI markers (from the kick file's conductor track; all files must agree).
    info: list[str] = []
    marker_sets = {lane: tuple(mf.markers) for lane, mf in files.items()}
    if len(set(marker_sets.values())) != 1:
        print("note: the three MIDI files carry different section markers; using the kick file's")
    marker_sections = sections_from_markers(files["kick"].markers, duration_ticks)
    fragment_path = pack / "Player_Chart_Fragment.json"
    fragment = json.loads(fragment_path.read_text(encoding="utf-8")) if fragment_path.is_file() else None
    if fragment is not None:
        frag_sections = [dict(s) for s in fragment.get("sections", [])]
        same_bounds = marker_sections is not None and [(s["start_tick"], s["length_bars"]) for s in marker_sections] \
            == [(s["start_tick"], s["length_bars"]) for s in frag_sections]
        if same_bounds and marker_sections is not None:
            # Boundaries agree: keep the marker boundaries with the fragment's short ids.
            sections = [{"id": f["id"], "start_tick": m["start_tick"], "length_bars": m["length_bars"]}
                        for m, f in zip(marker_sections, frag_sections)]
            info.append("sections:        MIDI markers agree with the fragment ("
                        + ", ".join(f"{m['id']}={f['id']}" for m, f in zip(marker_sections, frag_sections)) + ")")
        else:
            print("warning: MIDI section markers do not match the fragment's sections; using the fragment's")
            sections = frag_sections
        if int(fragment.get("duration_ticks", duration_ticks)) != duration_ticks:
            sys.exit("error: fragment duration_ticks differs from the manifest")
        with_ids = [{"id": f"n{i + 1:04d}", **n} for i, n in enumerate(chart)]
        diffs = chart_matches_fragment(with_ids, fragment.get("notes", []))
        if diffs:
            print("error: the chart generated from the MIDI does not equal Player_Chart_Fragment.json:")
            for d in diffs:
                print("  -", d)
            sys.exit(1)
        info.append(f"fragment check:  {len(with_ids)} notes identical to Player_Chart_Fragment.json")
    elif marker_sections is not None:
        sections = marker_sections
        info.append("sections:        from MIDI markers")
    else:
        sections = sixteen_bar_sections(bars)
        info.append("sections:        16-bar fallback (no usable markers, no fragment)")

    # ---- audio plan ----
    names = {}
    for stem in ("kick", "snare", "bass", "other"):
        future = str(manifest.get("expected_future_audio", {}).get(stem, f"audio/0{LANE_ORDER.get(stem, 3) + 1}_{stem.title()}.wav"))
        names[stem] = Path(future).stem
    plan = StemPlan(file_names=names)
    plan.kicks = [PlacedNote("kick", n.pitch, n.velocity, n.tick, n.tick) for n in files["kick"].note_ons]
    plan.snares = [(PlacedNote("snare", n.pitch, n.velocity, n.tick, n.tick), "snare") for n in files["snare"].note_ons]
    plan.bass = [PlacedNote("bass", n.pitch, n.velocity, n.start, n.end) for n in bass_mf.notes]
    # Other: closed hats on every 8th from bar 5, a 4-bar riser into bars 17 and 41, and the chord pad.
    hat_start_bar = 5
    for tick in range((hat_start_bar - 1) * TICKS_PER_BAR, duration_ticks, TICKS_PER_BEAT // 2):
        vel = 96 if tick % TICKS_PER_BEAT == 0 else 72
        plan.percussion.append((PlacedNote("hat", 42, vel, tick, tick), "closed"))
    plan.riser_ends = [t for t in (16 * TICKS_PER_BAR, 40 * TICKS_PER_BAR) if t <= duration_ticks]
    plan.pad_bars = [CHORD_VOICINGS[level_01_chord_for_bar(bar)] for bar in range(1, bars + 1)]

    info.insert(0, f"midi pack:       {pack} ({manifest.get('title', '')!r}), {bars} bars, "
                   f"PPQ {files['kick'].ppq}, {len(files['kick'].markers)} markers")
    return Build(bars, chart, sections, plan, info, f"bars 1-{bars}")


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------
def parse_bars(text: str) -> tuple[int, int]:
    m = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", text)
    if not m:
        raise argparse.ArgumentTypeError("--bars must look like 513-832")
    a, b = int(m.group(1)), int(m.group(2))
    if a < 1 or b < a:
        raise argparse.ArgumentTypeError("--bars must be 1-based with start <= end")
    return a, b


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--midi-pack", type=Path, help="folder holding Authoring_Manifest.json and the lane MIDIs")
    src.add_argument("--library", type=Path, help="extracted 174 BPM clip library folder")
    ap.add_argument("--out", type=Path, required=True, help="song pack folder to write")
    ap.add_argument("--bars", type=parse_bars, help="(library) global bar range, e.g. 513-832")
    ap.add_argument("--seed", type=int, default=27)
    ap.add_argument("--title", default=None)
    ap.add_argument("--level-id", default=None)
    ap.add_argument("--kicks-per-bar", type=float, default=0.25, help="(library) max average charted kicks per bar")
    ap.add_argument("--snares-per-bar", type=float, default=0.1, help="(library) max average charted snares per bar")
    ap.add_argument("--bass-per-bar", type=float, default=0.125, help="(library) max average charted bass notes per bar")
    ap.add_argument("--all-hits", action="store_true", help="(library) chart every hit, for stress testing")
    ap.add_argument("--enemy-profile", choices=ENEMY_PROFILES, default="mirror",
                    help="mirror: keep --enemy-accuracy of the player's notes; "
                         "ramp: accuracy climbs per section from --enemy-start to --enemy-end")
    ap.add_argument("--enemy-accuracy", type=float, default=0.85)
    ap.add_argument("--enemy-start", type=float, default=0.6, help="(ramp) accuracy at bar 1")
    ap.add_argument("--enemy-end", type=float, default=0.95, help="(ramp) accuracy at the last bar")
    ap.add_argument("--sample-rate", type=int, default=48000)
    ap.add_argument("--keep-wav", action="store_true")
    args = ap.parse_args(argv)
    if args.library is not None and args.bars is None:
        ap.error("--bars is required with --library")
    for name in ("enemy_accuracy", "enemy_start", "enemy_end"):
        if not 0.0 <= getattr(args, name) <= 1.0:
            ap.error(f"--{name.replace('_', '-')} must be between 0 and 1")
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        sys.exit("error: ffmpeg and ffprobe must be on PATH")

    build = build_from_midi_pack(args) if args.midi_pack is not None else build_from_library(args)
    bars = build.bars
    duration_ticks = bars * TICKS_PER_BAR
    level_id = args.level_id or args.out.name
    title = args.title or level_id

    chart = sorted(build.chart, key=lambda n: (n["tick"], LANE_ORDER[n["lane"]]))
    level_notes = [{"id": f"n{i + 1:04d}", **n} for i, n in enumerate(chart)]
    rng = random.Random(args.seed ^ 0x5EED)
    enemy_events, accuracies = enemy_schedule(chart, build.sections, bars, args.enemy_profile,
                                              args.enemy_accuracy, args.enemy_start, args.enemy_end, rng)

    # ---- audio ----
    sr = args.sample_rate
    duration_seconds = duration_ticks * SECONDS_PER_TICK
    total_samples = int(math.ceil(duration_seconds * sr)) + int(TAIL_SECONDS * sr)
    audio_dir = args.out / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    wavs = render_stems(build.plan, total_samples, sr, args.seed, audio_dir)
    stems: dict[str, str] = {}
    ogg_durations: dict[str, float] = {}
    for stem, wav in wavs.items():
        ogg = wav.with_suffix(".ogg")
        encode_ogg(wav, ogg, sr)
        if not args.keep_wav:
            wav.unlink()
        stems[stem] = f"audio/{ogg.name}"
        ogg_durations[stem] = probe_duration(ogg)
    spread = max(ogg_durations.values()) - min(ogg_durations.values())
    if spread > 0.005:
        sys.exit(f"error: stem durations differ by {spread * 1000:.1f} ms: {ogg_durations}")

    # ---- level.json ----
    level = {
        "schema_version": 1,
        "level_id": level_id,
        "title": title,
        "bpm": BPM,
        "time_signature": [4, 4],
        "ticks_per_beat": TICKS_PER_BEAT,
        "song_offset_ms": 0,
        "duration_ticks": duration_ticks,
        "seed": args.seed,
        "stems": {k: stems[k] for k in ("kick", "snare", "bass", "other")},
        "battlefield": BATTLEFIELD,
        "roster": ROSTER,
        "rules": dict(RULES),
        "sections": build.sections,
        "notes": level_notes,
        "enemy_events": enemy_events,
    }
    level_path = args.out / "level.json"
    level_path.write_text(json.dumps(level, indent=2) + "\n", encoding="utf-8")
    errors = validate_level(json.loads(level_path.read_text(encoding="utf-8")), args.out)
    if errors:
        print("level.json FAILED validation:")
        for e in errors:
            print("  -", e)
        return 1

    # ---- summary ----
    kicks = sum(1 for n in chart if n["lane"] == "kick")
    snares = sum(1 for n in chart if n["lane"] == "snare")
    taps = sum(1 for n in chart if n["lane"] == "bass" and n["type"] == "tap")
    holds = sum(1 for n in chart if n["lane"] == "bass" and n["type"] == "hold")
    print(f"pack:            {args.out}  ({level_id}: {title!r})")
    print(f"bars:            {bars} ({build.bar_label}), seed {args.seed}")
    print(f"duration:        {duration_ticks} ticks = {duration_seconds:.3f} s (+{TAIL_SECONDS:.0f} s audio tail)")
    for line in build.info:
        print(line)
    print(f"charted:         kicks {kicks}, snares {snares}, bass taps {taps}, bass holds {holds}"
          f" (total {len(level_notes)})")
    acc_text = ", ".join(f"{sid} {acc:.0%}" for sid, acc in accuracies)
    print(f"enemy events:    {len(enemy_events)} of {len(level_notes)} (profile {args.enemy_profile}: {acc_text})")
    print(f"max per side:    {kicks} tanks, {snares * RULES['infantry_per_snare']} infantry")
    print(f"sections:        {len(build.sections)}: " + ", ".join(str(s['id']) for s in build.sections))
    print("audio (ogg):     " + ", ".join(f"{Path(stems[k]).stem} {v:.3f} s" for k, v in ogg_durations.items())
          + f" (spread {spread * 1000:.2f} ms)")
    print(f"wrote:           {level_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
