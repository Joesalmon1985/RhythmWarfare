"""Build a Rhythm Warfare song pack from the owner's 174 BPM MIDI clip library.

Run from the project root, pointing at the EXTRACTED library (the folder that holds
01_Assembly_Placements.csv), e.g.:

    python -I tools/make_song_pack.py --library <extracted dir> --out songs/dev_dnb \
        --bars 513-832 --seed 27 --level-id dev_dnb --title "Dev: DnB section"

What it does:
  1. Walks 01_Assembly_Placements.csv for the requested global bar range, applying repeats,
     and collects every drum note-on (track 13_Drums, General MIDI note numbers) plus the
     sub-bass notes (11_Sub preferred, then 09_Reese, then 08_Growl per bar).
  2. Picks a deterministic, evenly spread, strong-beat-preferring subset of the real hits
     as the chart (see --kicks-per-bar / --snares-per-bar / --bass-per-bar), mirrors them
     as enemy events at --enemy-accuracy, and derives sections from 02_Section_Roadmap.csv.
  3. Synthesises four aligned placeholder stems (kick, snare, bass, other) with numpy from
     EVERY hit in the MIDI, writes them as Ogg Vorbis via ffmpeg, verifies their lengths
     with ffprobe, writes level.json and validates it the way the importer will.

The library is untrusted downloaded data: this script only reads bytes and CSV text from it
and never executes anything found there. Run it with `python -I`.
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
from dataclasses import dataclass
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

HOLD_MIN_TICKS = TICKS_PER_BEAT          # a sub note >= 1 beat becomes a hold
HOLD_MAX_TICKS = 4 * TICKS_PER_BAR       # holds are clamped to 4 bars
BASS_GAP_TICKS = 480                     # minimum gap between a bass note's end and the next start
HOLD_PRESS_GUARD_TICKS = 240             # kicks/snares keep clear of a hold's press moment +/- this

LANE_ORDER = {"kick": 0, "snare": 1, "bass": 2}
STEM_FILES = {"kick": "01_Kicks", "snare": "02_Snares", "bass": "03_Bass", "other": "04_Other"}

RULES = {
    "airfield_limit": 5,
    "aircraft_limit": 5,
    "initial_airfields": 0,
    "tank_per_kick": 1,
    "infantry_per_snare": 5,
    "repair_budget_credits_per_side": 5000,
    "song_end_result": "defeat",
}


# --------------------------------------------------------------------------------------
# Minimal Standard MIDI File parser (format 0/1, PPQ division, running status)
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class MidiNote:
    channel: int
    pitch: int
    velocity: int
    start: int   # chart ticks (960 per beat) relative to the clip's bar 1
    end: int     # chart ticks, exclusive


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


def _parse_track(chunk: bytes, ppq: int) -> list[MidiNote]:
    """Walk one MTrk chunk body and return the completed notes in chart ticks."""
    notes: list[MidiNote] = []
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
                notes.append(MidiNote(channel, pitch, vel, to_chart(start), to_chart(tick)))

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
            pos += length
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
        elif kind == 0x80 or (kind == 0x90 and d2 == 0):
            close(channel, d1, abs_tick)

    # Notes never switched off end where the track ends.
    for (channel, pitch), stack in open_notes.items():
        for start, vel in stack:
            if abs_tick > start:
                notes.append(MidiNote(channel, pitch, vel, to_chart(start), to_chart(abs_tick)))
    return notes


def parse_midi(path: Path) -> list[MidiNote]:
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
    pos = 8 + header_len
    notes: list[MidiNote] = []
    seen = 0
    while pos + 8 <= len(data) and seen < ntracks:
        chunk_id = data[pos:pos + 4]
        chunk_len = struct.unpack(">I", data[pos + 4:pos + 8])[0]
        body = data[pos + 8:pos + 8 + chunk_len]
        pos += 8 + chunk_len
        if chunk_id == b"MTrk":
            notes.extend(_parse_track(body, division))
            seen += 1
    notes.sort(key=lambda n: (n.start, n.channel, n.pitch))
    return notes


# --------------------------------------------------------------------------------------
# Placement sheet -> notes in the requested bar range
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
# Chart selection
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

    @property
    def end(self) -> int:
        return self.tick + self.duration


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
            out.append(BassNote(h.tick, "hold", dur))
            prev_end = h.tick + dur
        else:
            out.append(BassNote(h.tick, "tap", 0))
            prev_end = h.tick
    return out


def near_hold_press(tick: int, hold_starts: Sequence[int]) -> bool:
    k = bisect.bisect_left(hold_starts, tick - HOLD_PRESS_GUARD_TICKS)
    return k < len(hold_starts) and hold_starts[k] <= tick + HOLD_PRESS_GUARD_TICKS


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


# --------------------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------------------
def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s or "section"


def build_sections(library: Path, first_bar: int, last_bar: int) -> list[dict[str, int | str]]:
    roadmap = library / "02_Section_Roadmap.csv"
    pieces: list[tuple[int, int, str]] = []
    if roadmap.is_file():
        for row in read_csv_rows(roadmap):
            a, b = int(row["start_bar"]), int(row["end_bar"])
            a2, b2 = max(a, first_bar), min(b, last_bar)
            if a2 <= b2:
                pieces.append((a2, b2, row.get("section", "").strip() or f"bars_{a2}_{b2}"))
    pieces.sort()
    contiguous = bool(pieces) and pieces[0][0] == first_bar and pieces[-1][1] == last_bar and all(
        pieces[i][1] + 1 == pieces[i + 1][0] for i in range(len(pieces) - 1))
    if not contiguous:
        pieces = []
        bar = first_bar
        n = 1
        while bar <= last_bar:
            end = min(bar + 15, last_bar)
            pieces.append((bar, end, f"part_{n}"))
            bar = end + 1
            n += 1
    sections: list[dict[str, int | str]] = []
    used: set[str] = set()
    for a, b, name in pieces:
        sid = slug(name)
        if sid in used:
            sid = f"{sid}_{a}"
        used.add(sid)
        sections.append({"id": sid, "start_tick": (a - first_bar) * TICKS_PER_BAR, "length_bars": b - a + 1})
    return sections


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
class AudioSources:
    drums: list[PlacedNote]
    bass: list[PlacedNote]
    chords: list[PlacedNote]
    chord_bars: set[int]  # pack-local bar numbers (1-based) the chord placements cover


def render_stems(sources: AudioSources, total_samples: int, sr: int, bars: int, seed: int,
                 out_dir: Path) -> dict[str, Path]:
    """Render the four stems (equal length) to WAV files; returns stem name -> path."""
    paths: dict[str, Path] = {}

    # kick stem
    rng = np.random.default_rng(seed + 1)
    buf = np.zeros(total_samples, dtype=np.float32)
    for n in sources.drums:
        if n.pitch in GM_KICK:
            add_at(buf, tick_to_sample(n.tick, sr), synth_kick(sr, rng, n.velocity))
    paths["kick"] = out_dir / f"{STEM_FILES['kick']}.wav"
    write_wav(paths["kick"], finalize(buf), sr)

    # snare stem
    rng = np.random.default_rng(seed + 2)
    buf = np.zeros(total_samples, dtype=np.float32)
    for n in sources.drums:
        if n.pitch in GM_SNARE:
            add_at(buf, tick_to_sample(n.tick, sr), synth_snare(sr, rng, n.velocity, "snare"))
        elif n.pitch in GM_RIM:
            add_at(buf, tick_to_sample(n.tick, sr), synth_snare(sr, rng, n.velocity, "rim"))
        elif n.pitch in GM_CLAP:
            add_at(buf, tick_to_sample(n.tick, sr), synth_snare(sr, rng, n.velocity, "clap"))
    paths["snare"] = out_dir / f"{STEM_FILES['snare']}.wav"
    write_wav(paths["snare"], finalize(buf), sr)

    # bass stem
    buf = np.zeros(total_samples, dtype=np.float32)
    for n in sources.bass:
        s0 = tick_to_sample(n.tick, sr)
        s1 = min(tick_to_sample(n.end, sr), total_samples)
        if s1 > s0:
            add_at(buf, s0, synth_bass_note(sr, n.pitch, n.velocity, s1 - s0))
    paths["bass"] = out_dir / f"{STEM_FILES['bass']}.wav"
    write_wav(paths["bass"], finalize(buf), sr)

    # other stem: hats, cymbals, toms, anything else on the drum track, plus a quiet pad
    rng = np.random.default_rng(seed + 4)
    buf = np.zeros(total_samples, dtype=np.float32)
    for n in sources.drums:
        s = tick_to_sample(n.tick, sr)
        if n.pitch in GM_KICK | GM_SNARE | GM_RIM | GM_CLAP:
            continue
        if n.pitch in GM_CLOSED_HAT:
            add_at(buf, s, synth_hat(sr, rng, n.velocity, "closed"))
        elif n.pitch in GM_PEDAL_HAT:
            add_at(buf, s, synth_hat(sr, rng, n.velocity, "pedal"))
        elif n.pitch in GM_OPEN_HAT:
            add_at(buf, s, synth_hat(sr, rng, n.velocity, "open"))
        elif n.pitch in GM_CRASH:
            add_at(buf, s, synth_hat(sr, rng, n.velocity, "crash"))
        elif n.pitch in GM_RIDE:
            add_at(buf, s, synth_hat(sr, rng, n.velocity, "ride"))
        else:
            add_at(buf, s, synth_tom(sr, n.velocity, n.pitch))
    chord_notes = sorted(sources.chords, key=lambda c: c.tick)
    last_pitches: list[int] = [49, 56]  # C#3 + G#3 drone, the piece's home key
    for bar in range(1, bars + 1):
        b0 = (bar - 1) * TICKS_PER_BAR
        b1 = b0 + TICKS_PER_BAR
        on_downbeat = sorted({c.pitch for c in chord_notes if c.tick < b0 + TICKS_PER_BEAT and c.end > b0})
        anywhere = sorted({c.pitch for c in chord_notes if c.tick < b1 and c.end > b0})
        if on_downbeat:
            pitches = on_downbeat
        elif anywhere:
            pitches = anywhere
        elif bar in sources.chord_bars:
            pitches = last_pitches     # a rest inside a chord placement: carry the chord
        else:
            pitches = [49, 56]
        last_pitches = pitches
        s0, s1 = tick_to_sample(b0, sr), tick_to_sample(b1, sr)
        add_at(buf, s0, synth_pad_bar(sr, pitches[:6], s1 - s0))
    paths["other"] = out_dir / f"{STEM_FILES['other']}.wav"
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
    lane_busy_until: dict[str, int] = {}
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
        if tick < lane_busy_until.get(lane, -1):
            errors.append(f"{nid}: overlaps the previous {lane} note")
        lane_busy_until[lane] = max(end, tick + 1)

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

    # Three-touch chords cannot be produced by this tool (kick and snare never share a tick),
    # but flag them anyway for author review.
    by_tick: dict[int, set[str]] = {}
    for note in level["notes"]:
        by_tick.setdefault(note["tick"], set()).add(note["lane"])
    for tick, lanes in by_tick.items():
        if len(lanes) >= 3:
            errors.append(f"three-touch chord at tick {tick}")
    return errors


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
    ap.add_argument("--library", type=Path, required=True, help="extracted clip library folder")
    ap.add_argument("--out", type=Path, required=True, help="song pack folder to write")
    ap.add_argument("--bars", type=parse_bars, required=True, help="global bar range, e.g. 513-832")
    ap.add_argument("--seed", type=int, default=27)
    ap.add_argument("--title", default=None)
    ap.add_argument("--level-id", default=None)
    ap.add_argument("--kicks-per-bar", type=float, default=0.25, help="max average charted kicks per bar")
    ap.add_argument("--snares-per-bar", type=float, default=0.1, help="max average charted snares per bar")
    ap.add_argument("--bass-per-bar", type=float, default=0.125, help="max average charted bass notes per bar")
    ap.add_argument("--all-hits", action="store_true", help="chart every hit (stress testing)")
    ap.add_argument("--enemy-accuracy", type=float, default=0.85)
    ap.add_argument("--sample-rate", type=int, default=48000)
    ap.add_argument("--keep-wav", action="store_true")
    args = ap.parse_args(argv)

    first_bar, last_bar = args.bars
    bars = last_bar - first_bar + 1
    duration_ticks = bars * TICKS_PER_BAR
    level_id = args.level_id or args.out.name
    title = args.title or level_id
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        sys.exit("error: ffmpeg and ffprobe must be on PATH")

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
    chords = [n for n in notes if n.track == chord_track] if chord_track else []
    chord_bars = ({b - first_bar + 1 for b in bars_covered(placements, chord_track, first_bar, last_bar)}
                  if chord_track else set())

    # ---- chart selection (seeded) ----
    rng = random.Random(args.seed)
    kick_cands = unique_hits(drums, GM_KICK)
    snare_cands = unique_hits(drums, GM_SNARE)
    bass_cands = bass_candidates(bass_notes)

    if args.all_hits:
        bass_sel = bass_cands
    else:
        bass_budget = int(math.floor(args.bass_per_bar * bars))
        bass_sel = spread_select(bass_cands, bass_budget, duration_ticks,
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

    chart: list[dict] = []
    for h in kick_chart:
        chart.append({"tick": h.tick, "lane": "kick", "type": "tap"})
    for h in snare_chart:
        chart.append({"tick": h.tick, "lane": "snare", "type": "tap"})
    for b in bass_chart:
        entry: dict = {"tick": b.tick, "lane": "bass", "type": b.kind}
        if b.kind == "hold":
            entry["duration_ticks"] = b.duration
        chart.append(entry)
    chart.sort(key=lambda n: (n["tick"], LANE_ORDER[n["lane"]]))
    level_notes = [{"id": f"n{i + 1:04d}", **n} for i, n in enumerate(chart)]

    keep = even_subset(len(chart), args.enemy_accuracy, rng)
    enemy_events = [{"tick": n["tick"], "action": n["lane"]} for n, k in zip(chart, keep) if k]
    enemy_events.sort(key=lambda e: (e["tick"], LANE_ORDER[e["action"]]))
    enemy_events = [{"id": f"e{i + 1:03d}", **e} for i, e in enumerate(enemy_events)]

    sections = build_sections(args.library, first_bar, last_bar)

    # ---- audio ----
    sr = args.sample_rate
    duration_seconds = duration_ticks * SECONDS_PER_TICK
    total_samples = int(math.ceil(duration_seconds * sr)) + int(TAIL_SECONDS * sr)
    audio_dir = args.out / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    wavs = render_stems(AudioSources(drums, bass_notes, chords, chord_bars), total_samples, sr, bars,
                        args.seed, audio_dir)
    stems: dict[str, str] = {}
    ogg_durations: dict[str, float] = {}
    for stem, wav in wavs.items():
        ogg = audio_dir / f"{STEM_FILES[stem]}.ogg"
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
        "battlefield": "mvp_mirrored_01",
        "roster": "openra_mvp_01",
        "rules": dict(RULES),
        "sections": sections,
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
    taps = sum(1 for b in bass_chart if b.kind == "tap")
    holds = len(bass_chart) - taps
    gm_counts: dict[int, int] = {}
    for n in drums:
        gm_counts[n.pitch] = gm_counts.get(n.pitch, 0) + 1
    print(f"pack:            {args.out}  ({level_id}: {title!r})")
    print(f"bars:            {bars} (global {first_bar}-{last_bar}), seed {args.seed}")
    print(f"duration:        {duration_ticks} ticks = {duration_seconds:.3f} s (+{TAIL_SECONDS:.0f} s audio tail)")
    print(f"drum hits (GM):  " + ", ".join(f"{k}:{v}" for k, v in sorted(gm_counts.items())))
    print(f"bass source:     " + ", ".join(f"{t} {c} bars" for t, c in source_counts.items() if c)
          + (f", {uncovered} bars without bass" if uncovered else "") + f"; {len(bass_cands)} notes")
    print(f"pad source:      {chord_track or 'drone only'} ({len(chords)} notes)")
    print(f"candidates:      kicks {len(unique_hits(drums, GM_KICK))}, snares {len(unique_hits(drums, GM_SNARE))}")
    print(f"charted:         kicks {len(kick_chart)}, snares {len(snare_chart)}, bass taps {taps}, bass holds {holds}"
          f" (total {len(level_notes)})")
    print(f"enemy events:    {len(enemy_events)} ({args.enemy_accuracy:.0%} of {len(level_notes)})")
    print(f"max per side:    {len(kick_chart)} tanks, {len(snare_chart) * RULES['infantry_per_snare']} infantry")
    print(f"sections:        {len(sections)}: " + ", ".join(str(s['id']) for s in sections))
    print("audio (ogg):     " + ", ".join(f"{STEM_FILES[k]} {v:.3f} s" for k, v in ogg_durations.items())
          + f" (spread {spread * 1000:.2f} ms)")
    print(f"wrote:           {level_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
