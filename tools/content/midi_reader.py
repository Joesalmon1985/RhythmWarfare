"""A small Standard MIDI File reader and writer (no third-party module): type 0/1 files, PPQ division, note on/off, tempo,
time signature, track names. The `mido` package is not needed anywhere in the content tools.

Reading: `parse_midi(data)` gives every track's events with absolute ticks; `read_midi_bytes(data)` gives the notes in beats
(what beatshaper.py and catalogue.py use). `common.read_midi` builds the 960 PPQ note list the loop library uses on top of
`parse_midi`.

Writing: `build_midi(ppq, tracks)` where a track is a list of `(tick, order, bytes)` events (build them with the helpers below);
the bytes are the same ones mido wrote (running status for repeated channel messages, a track-name meta first, the end-of-track delta as given), so a
file rewritten from the same notes is byte-identical.
"""
from __future__ import annotations

import struct

META_TRACK_NAME, META_TEMPO, META_TIME_SIG, META_END = 0x03, 0x51, 0x58, 0x2F


class MidiError(ValueError):
    """A file that is not a readable Standard MIDI File (the callers turn it into a ContentError with the path)."""


def _vlq(data: bytes, i: int) -> tuple[int, int]:
    v = 0
    for _ in range(4):
        b = data[i]
        i += 1
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            return v, i
    raise MidiError("a variable-length number is longer than four bytes")


def encode_vlq(v: int) -> bytes:
    out = [v & 0x7F]
    v >>= 7
    while v:
        out.append((v & 0x7F) | 0x80)
        v >>= 7
    return bytes(reversed(out))


def parse_midi(data: bytes) -> dict:
    """{format, division, tracks: [{name, length, events: [{tick, type, ...}]}]}.

    Event types: note_on (channel, note, velocity > 0), note_off (a note-on with velocity 0 is a note_off), set_tempo (tempo us per quarter),
    time_signature (numerator, denominator). Other messages are skipped. `length` is the tick of the track's last event (end of track)."""
    if data[:4] != b"MThd":
        raise MidiError("no MThd header")
    try:
        fmt, ntrk, division = struct.unpack(">HHH", data[8:14])
        if division & 0x8000:
            raise MidiError("SMPTE time division is not supported")
        if division == 0:
            raise MidiError("a time division of zero")
        pos = 8 + int.from_bytes(data[4:8], "big")
        tracks = []
        for _ in range(ntrk):
            if data[pos:pos + 4] != b"MTrk":
                break
            end = pos + 8 + int.from_bytes(data[pos + 4:pos + 8], "big")
            i, t, status = pos + 8, 0, 0
            events, name = [], None
            while i < end:
                d, i = _vlq(data, i)
                t += d
                if data[i] & 0x80:
                    status = data[i]
                    i += 1
                if status == 0xFF:
                    typ = data[i]
                    ln, i = _vlq(data, i + 1)
                    body = data[i:i + ln]
                    if typ == META_TEMPO and ln == 3:
                        events.append({"tick": t, "type": "set_tempo", "tempo": int.from_bytes(body, "big")})
                    elif typ == META_TIME_SIG and ln >= 2:
                        events.append({"tick": t, "type": "time_signature", "numerator": body[0], "denominator": 1 << body[1]})
                    elif typ == META_TRACK_NAME and name is None:
                        name = body.decode("latin-1")
                    i += ln
                elif status in (0xF0, 0xF7):
                    ln, i = _vlq(data, i)
                    i += ln
                else:
                    kind, ch = status & 0xF0, status & 0x0F
                    n_args = 1 if kind in (0xC0, 0xD0) else 2
                    a = data[i:i + n_args]
                    if len(a) < n_args:
                        raise MidiError("a message is cut off")
                    i += n_args
                    if kind == 0x90 and a[1] > 0:
                        events.append({"tick": t, "type": "note_on", "channel": ch, "note": a[0], "velocity": a[1]})
                    elif kind in (0x80, 0x90):
                        events.append({"tick": t, "type": "note_off", "channel": ch, "note": a[0], "velocity": a[1]})
            tracks.append({"name": name, "length": t, "events": events})
            pos = end
    except (IndexError, struct.error) as exc:
        raise MidiError("the file is cut off or damaged") from exc
    return {"format": fmt, "division": division, "tracks": tracks}


def read_midi_bytes(data: bytes) -> dict:
    """Notes in quarter-note beats: {notes: [{beat, dur, pitch, velocity}], header_bpm, end_beat}. Notes are paired per (channel, pitch), first in first out."""
    mid = parse_midi(data)
    div = mid["division"]
    notes, tempos = [], []
    for tr in mid["tracks"]:
        on: dict = {}
        for ev in tr["events"]:
            if ev["type"] == "note_on":
                on.setdefault((ev["channel"], ev["note"]), []).append((ev["tick"], ev["velocity"]))
            elif ev["type"] == "note_off" and on.get((ev["channel"], ev["note"])):
                s0, v = on[(ev["channel"], ev["note"])].pop(0)
                notes.append({"beat": s0 / div, "dur": (ev["tick"] - s0) / div, "pitch": ev["note"], "velocity": v})
            elif ev["type"] == "set_tempo":
                tempos.append(60000000.0 / ev["tempo"])
    notes.sort(key=lambda n: (n["beat"], n["pitch"]))
    return {"notes": notes, "header_bpm": tempos[0] if tempos else None, "end_beat": max((n["beat"] + n["dur"] for n in notes), default=0.0)}


# --- writing ------------------------------------------------------------------------------------------------------

def bpm_to_tempo(bpm: float) -> int:
    return int(round(60000000.0 / bpm))


def ev_name(name: str, tick: int = 0) -> tuple:
    b = name.encode("latin-1", "replace")
    return (tick, -3, bytes([0xFF, META_TRACK_NAME]) + encode_vlq(len(b)) + b)


def ev_tempo(bpm: float, tick: int = 0) -> tuple:
    return (tick, -2, bytes([0xFF, META_TEMPO, 3]) + bpm_to_tempo(bpm).to_bytes(3, "big"))


def ev_time_sig(numerator: int = 4, denominator: int = 4, tick: int = 0) -> tuple:
    return (tick, -1, bytes([0xFF, META_TIME_SIG, 4, numerator, denominator.bit_length() - 1, 24, 8]))


def ev_note_on(tick: int, note: int, velocity: int, channel: int = 0) -> tuple:
    return (tick, 1, bytes([0x90 | channel, note, velocity]))


def ev_note_off(tick: int, note: int, channel: int = 0) -> tuple:
    return (tick, 0, bytes([0x80 | channel, note, 0]))


def ev_end(tick: int) -> tuple:
    return (tick, 9, bytes([0xFF, META_END, 0]))


def note_events(notes: list[dict]) -> list[tuple]:
    """Events for notes [{tick, duration_ticks, pitch, velocity}] in mido's order: by tick, offs before ons, then pitch."""
    evs = []
    for n in notes:
        evs.append(ev_note_on(n["tick"], n["pitch"], n["velocity"]))
        evs.append(ev_note_off(n["tick"] + n["duration_ticks"], n["pitch"]))
    return sorted(evs, key=lambda e: (e[0], e[1], e[2][1]))


def build_midi(ppq: int, tracks: list[list[tuple]], fmt: int = 1) -> bytes:
    """A Standard MIDI File. A track is a list of (tick, order, bytes) events, sorted by (tick, order) (stable); the deltas are written from the
    absolute ticks. An end-of-track is added at the last event's tick when the track has none."""
    out = b"MThd" + struct.pack(">IHHH", 6, fmt, len(tracks), ppq)
    for events in tracks:
        evs = sorted(events, key=lambda e: (e[0], e[1]))
        if not evs or evs[-1][2][:2] != bytes([0xFF, META_END]):
            evs.append(ev_end(evs[-1][0] if evs else 0))
        body, now, running = b"", 0, None
        for tick, _order, payload in evs:
            body += encode_vlq(tick - now)
            if payload[0] == 0xFF:  # a meta event ends running status
                running = None
                body += payload
            else:  # mido's writer repeats a channel message's status byte only when it changes
                body += payload[1:] if payload[0] == running else payload
                running = payload[0]
            now = tick
        out += b"MTrk" + struct.pack(">I", len(body)) + body
    return out
