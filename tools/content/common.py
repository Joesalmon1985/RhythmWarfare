"""Shared constants and file helpers for the content build (tools/content/build.py).

Timing authority: integer ticks at 960 per quarter note, bar 1 = tick 0, 174 BPM, 4/4. A sample position is always
computed from an absolute tick (never accumulated), so placements cannot drift.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import tempfile
import wave
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from midi_reader import (MidiError, build_midi, ev_name, ev_tempo, ev_time_sig, note_events,  # noqa: E402
                         parse_midi)

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "content"
LIBRARY = CONTENT / "library"
MISSIONS = CONTENT / "missions"
MISSIONS_LEGACY = CONTENT / "missions_legacy"  # the old per-mission authoring (choices, phases); read only by export_midi.py
SONGS = ROOT / "songs"
SONGS_LIBRARY = SONGS / "library"  # index.json and the 8-bar loops the game plays
INSTRUMENTS = ROOT / "data" / "campaign" / "instruments.json"
RULES_PATH = ROOT / "data" / "campaign" / "rules.json"

BPM = 174
PPQ = 960
BEATS_PER_BAR = 4
TICKS_PER_BAR = PPQ * BEATS_PER_BAR  # 3840
SAMPLE_RATE = 48000
CHANNELS = 2
SAMPLE_WIDTH = 2  # bytes: 16-bit PCM
TAIL_BARS = 1  # a render may run at most one bar past its musical end (release tail)
HOLD_MIN_TICKS = 480  # a bass note of at least an eighth becomes a hold cue, shorter ones are taps
FAMILIES = ("kick", "snare", "bass", "other")
KINDS = {"groove": ("kick", "snare"), "fill": ("kick", "snare"), "bass": ("bass",), "accompaniment": ("other",)}

SAMPLES_PER_TICK = Fraction(SAMPLE_RATE * 60, BPM * PPQ)


def tick_to_sample(tick: int) -> int:
    """Absolute tick -> absolute sample frame (rounded once, from the tick itself)."""
    return int(round(Fraction(tick) * SAMPLES_PER_TICK))


def tick_to_seconds(tick: int) -> float:
    return tick * 60.0 / (BPM * PPQ)


def bars_to_frames(bars: int) -> int:
    return tick_to_sample(bars * TICKS_PER_BAR)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _inline(value, indent: int, level: int, depth: int) -> str:
    """JSON text: objects spread over lines down to `depth` levels, everything below on one line."""
    if level >= depth or not isinstance(value, dict) or not value:
        return json.dumps(value)
    pad = " " * (indent * (level + 1))
    rows = [f"{pad}{json.dumps(k)}: {_inline(v, indent, level + 1, depth)}" for k, v in value.items()]
    return "{\n" + ",\n".join(rows) + "\n" + " " * (indent * level) + "}"


def write_text_lf(path: Path, text: str) -> bool:
    """Write text with LF line endings (never CRLF, even on Windows); untouched when the bytes are the same."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    if path.exists() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True


def write_json(path: Path, data: dict, indent: int | None = 1, depth: int | None = None) -> None:
    """Write JSON with LF endings. `depth` (with indent) spreads that many object levels over lines and puts everything
    below on one line, which keeps long cue lists compact."""
    text = (_inline(data, indent or 1, 0, depth) if depth is not None else json.dumps(data, indent=indent)) + "\n"
    write_text_lf(path, text)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


class ContentError(Exception):
    """A problem the owner must fix; the message says what and how."""


# --- MIDI ---------------------------------------------------------------------------------------------------------

def read_midi(path: Path, default_bpm: float = BPM) -> dict:
    """Read an Ableton-style type 0/1 PPQ MIDI file into notes at 960 PPQ.

    Returns {notes: [{tick, duration_ticks, pitch, velocity}], tempo_bpm, tempo_source, meter, ppq}. Note durations
    and the starting silence are kept exactly; a file whose PPQ cannot be rescaled exactly to 960 is rejected. When the
    file carries no tempo the recorded `default_bpm` is used (never a guess from audio)."""
    try:
        midi = parse_midi(path.read_bytes())
    except (MidiError, OSError) as exc:
        raise ContentError(f"{rel(path)}: not a readable MIDI file ({exc})") from exc
    if midi["format"] not in (0, 1):
        raise ContentError(f"{rel(path)}: only type 0/1 PPQ MIDI is supported (this is type {midi['format']})")
    division = midi["division"]
    scale = Fraction(PPQ, division)
    notes, tempos, meters = [], [], []
    for track in midi["tracks"]:
        active: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
        for msg in track["events"]:
            scaled = Fraction(msg["tick"]) * scale
            if scaled.denominator != 1:
                raise ContentError(f"{rel(path)}: a MIDI event at source tick {msg['tick']} does not land on the 960 PPQ grid")
            when = int(scaled)
            if msg["type"] == "note_on":
                active[(msg["channel"], msg["note"])].append((when, msg["velocity"]))
            elif msg["type"] == "note_off":
                key = (msg["channel"], msg["note"])
                if not active[key]:
                    raise ContentError(f"{rel(path)}: note-off without a note-on (pitch {msg['note']} at tick {when})")
                start, vel = active[key].pop(0)
                if when <= start:
                    raise ContentError(f"{rel(path)}: a note at tick {start} has no length")
                notes.append({"tick": start, "duration_ticks": when - start, "pitch": msg["note"], "velocity": vel})
            elif msg["type"] == "set_tempo":
                tempos.append((when, 60000000.0 / msg["tempo"]))
            elif msg["type"] == "time_signature":
                meters.append((when, msg["numerator"], msg["denominator"]))
        if any(active.values()):
            raise ContentError(f"{rel(path)}: a note is never released (missing note-off)")
    notes.sort(key=lambda n: (n["tick"], n["pitch"]))
    distinct = sorted({round(b, 3) for _, b in tempos})
    if len(distinct) > 1:
        raise ContentError(f"{rel(path)}: tempo changes inside a clip are not supported ({distinct})")
    meter = [4, 4]
    if meters:
        kinds = {(n, d) for _, n, d in meters}
        if len(kinds) > 1 or (4, 4) not in kinds:
            raise ContentError(f"{rel(path)}: the clip must be in 4/4 (found {sorted(kinds)})")
    return {
        "notes": notes,
        "tempo_bpm": distinct[0] if distinct else float(default_bpm),
        "tempo_source": "midi" if distinct else "recorded_default",
        "meter": meter,
        "ppq": division,
    }


def write_midi(path: Path, notes: list[dict], name: str) -> None:
    """Write a type 1 MIDI file at 960 PPQ and 174 BPM in 4/4 (generated and derived library clips)."""
    meta = [ev_name(name), ev_tempo(BPM), ev_time_sig(4, 4)]
    track = [ev_name(name)] + note_events(notes)
    data = build_midi(PPQ, [meta, track], 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)


def notes_signature(notes: list[dict]) -> str:
    return sha256_bytes(json.dumps([[n["tick"], n["duration_ticks"], n["pitch"], n["velocity"]] for n in notes]).encode())


# --- WAV ----------------------------------------------------------------------------------------------------------

def read_wav(path: Path) -> tuple[np.ndarray, dict]:
    """Read a 16-bit PCM WAV. Returns float32 frames x channels in [-1, 1] and its format."""
    try:
        with wave.open(str(path), "rb") as wf:
            fmt = {"channels": wf.getnchannels(), "sample_width": wf.getsampwidth(), "sample_rate": wf.getframerate(),
                   "frames": wf.getnframes()}
            raw = wf.readframes(wf.getnframes())
    except (wave.Error, EOFError) as exc:
        raise ContentError(f"{rel(path)}: not a PCM WAV file the build can read ({exc}); export 16-bit PCM WAV") from exc
    if fmt["sample_width"] != SAMPLE_WIDTH:
        raise ContentError(f"{rel(path)}: {8 * fmt['sample_width']}-bit audio; export 16-bit PCM")
    data = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    data = data.reshape(-1, fmt["channels"])
    return data, fmt


def write_wav(path: Path, frames: np.ndarray) -> None:
    """Write float frames (n x 2, or n for mono which is duplicated) as 48 kHz stereo 16-bit PCM."""
    if frames.ndim == 1:
        frames = np.stack([frames, frames], axis=1)
    pcm = np.round(np.clip(frames, -1.0, 32767.0 / 32768.0) * 32768.0).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".wav.tmp")
    with wave.open(str(tmp), "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())
    data = tmp.read_bytes()
    tmp.unlink()
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)


def encode_ogg(frames: np.ndarray, ogg: Path, quality: float = 3.0) -> None:
    """Encode float stereo frames to Ogg Vorbis with ffmpeg (stems and previews the game plays)."""
    ogg.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "x.wav"
        write_wav(wav, frames)
        out = Path(tmp) / "x.ogg"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-c:a", "libvorbis", "-q:a", str(quality),
                        "-ar", str(SAMPLE_RATE), "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:a", "+bitexact",
                        str(out)], check=True)
        data = out.read_bytes()
    if not ogg.exists() or ogg.read_bytes() != data:
        ogg.write_bytes(data)


def peak_db(frames: np.ndarray) -> float:
    peak = float(np.max(np.abs(frames))) if frames.size else 0.0
    return -math.inf if peak <= 0 else 20.0 * math.log10(peak)
