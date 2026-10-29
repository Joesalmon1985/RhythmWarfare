"""Reference offline MIDI-to-chart converter for the defense campaign authoring pack.

Requires mido==1.3.3. Usage: python compile_chart.py LEVEL_DIR
Reads song.json, chart_rules.json and musical MIDI; writes a proposed authoring chart.
It does not write a runtime Godot level, process WAV files, or implement battle logic.
"""
from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import sys

import mido


def read_notes(path, target_ppq):
    midi = mido.MidiFile(path)
    if midi.type not in (0, 1) or midi.ticks_per_beat <= 0:
        raise ValueError("Only synchronous PPQ MIDI type 0/1 is supported")
    notes, tempos, meters = [], [], []
    scale = target_ppq / midi.ticks_per_beat
    for track in midi.tracks:
        tick, active = 0, defaultdict(list)
        for msg in track:
            tick += msg.time
            scaled = tick * scale
            if abs(scaled - round(scaled)) > 1e-8:
                raise ValueError("MIDI cannot be rescaled exactly to the target grid")
            when = round(scaled)
            if msg.type == "note_on" and msg.velocity:
                active[msg.channel, msg.note].append((when, msg.velocity))
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                key = msg.channel, msg.note
                if not active[key]:
                    raise ValueError("Unmatched MIDI note-off")
                start, velocity = active[key].pop(0)
                if when <= start:
                    raise ValueError("Nonpositive MIDI note duration")
                notes.append({"tick": start, "duration_ticks": when - start, "midi_note": msg.note, "velocity": velocity})
            elif msg.type == "set_tempo":
                tempos.append((when, msg.tempo))
            elif msg.type == "time_signature":
                meters.append((when, msg.numerator, msg.denominator))
        if any(active.values()):
            raise ValueError("Unclosed MIDI notes")
    return sorted(notes, key=lambda n: (n["tick"], n["midi_note"])), tempos, meters


def validate_thumb_layout(notes, rules):
    """Two-touch count alone cannot establish two-thumb playability."""
    constraints = rules.get("thumb_constraints")
    if not constraints:
        return
    for buttons in ([1, 2], [3, 4]):
        row = sorted([n for n in notes if n["button"] in buttons], key=lambda n: n["tick"])
        for a, b in zip(row, row[1:]):
            if a["type"] == "hold":
                gap = b["tick"] - a["tick"] - a["duration_ticks"]
                if gap < constraints["min_hold_release_to_same_thumb_press_ticks"]:
                    raise ValueError(f"Thumb hold/reach conflict: {a['id']} -> {b['id']}")
            elif b["tick"] - a["tick"] < constraints["min_same_thumb_onset_gap_ticks"]:
                raise ValueError(f"Same-thumb onset gap too small: {a['id']} -> {b['id']}")


def compile_chart(directory, rules_name="chart_rules.json", output_name="player_chart.json", write=True):
    directory = Path(directory).resolve()
    song = json.loads((directory / "song.json").read_text())
    rules_path, output_path = (directory / rules_name).resolve(), (directory / output_name).resolve()
    if directory not in rules_path.parents or directory not in output_path.parents:
        raise ValueError("Chart/rules path escapes level directory")
    rules = json.loads(rules_path.read_text())
    ppq, bpm = song["ticks_per_beat"], song["bpm"]
    if song["time_signature"] != [4, 4] or ppq <= 0 or bpm <= 0:
        raise ValueError("This reference converter requires positive PPQ/BPM and 4/4 meter")
    bar_ticks = ppq * song["time_signature"][0]
    end = song["bars"] * bar_ticks
    sections = []
    cursor = 0
    for s in rules["sections"]:
        if (s["start_bar"] - 1) * bar_ticks != cursor or s["bars"] <= 0:
            raise ValueError("Sections must cover the song contiguously in whole bars")
        s = {**s, "start_tick": cursor, "length_bars": s["bars"]}
        cursor += s["bars"] * bar_ticks
        sections.append(s)
    if cursor != end:
        raise ValueError("Section coverage does not equal song duration")

    def section_at(tick):
        return next(s for s in sections if s["start_tick"] <= tick < s["start_tick"] + s["length_bars"] * bar_ticks)

    notes, omitted, source_hashes, known_ids = [], [], {}, set()
    selection = rules.get("selection", {})
    included_ids = selection.get("include_source_note_ids")
    excluded_ids = set(selection.get("exclude_source_note_ids", []))
    excluded_parts = set(selection.get("exclude_part_ids", []))
    expected_tempo = mido.bpm2tempo(bpm)
    for part in song["parts"]:
        path = (directory / part["midi"]).resolve()
        if directory not in path.parents or not path.is_file():
            raise ValueError("MIDI path escapes level directory or does not exist")
        source_hashes[part["id"]] = hashlib.sha256(path.read_bytes()).hexdigest()
        expected_hash = rules.get("expected_source_sha256", {}).get(part["id"])
        if expected_hash and source_hashes[part["id"]] != expected_hash:
            raise ValueError("Source MIDI changed; review source-note button overrides before regenerating")
        musical, tempos, meters = read_notes(path, ppq)
        if not tempos or any(t != 0 or tempo != expected_tempo for t, tempo in tempos):
            raise ValueError("MIDI tempo must explicitly match the song's fixed tempo")
        if any((n, d) != tuple(song["time_signature"]) for _, n, d in meters):
            raise ValueError("MIDI meter differs from song")
        for i, n in enumerate(musical, 1):
            sid = f"{part['id']}:{i:04d}"
            known_ids.add(sid)
            if n["tick"] >= end or n["tick"] + n["duration_ticks"] > end:
                raise ValueError("Source musical note exceeds song duration")
            section = section_at(n["tick"])
            family = part["family"]
            playable = family in ("kick", "snare", "bass") and ((family == "bass") == (section["mode"] == "bass"))
            if not playable:
                omitted.append({"source_note_id": sid, "part_id": part["id"], "reason": "accompaniment"})
                continue
            if part["id"] in excluded_parts or sid in excluded_ids or (included_ids is not None and sid not in included_ids):
                omitted.append({"source_note_id": sid, "part_id": part["id"], "reason": "authored_difficulty_selection"})
                continue
            rule = rules["button_rules"][part["id"]]
            # A section can override placement independently of the instrument or its production profile.
            rule = section.get("button_overrides", {}).get(part["id"], rule)
            if "button" in rule:
                button = rule["button"]
            else:
                button = next(r["button"] for r in rule["pitch_ranges"] if r["min"] <= n["midi_note"] <= r["max"])
            button = rules.get("note_button_overrides", {}).get(sid, button)
            is_hold = family == "bass" and n["duration_ticks"] >= rules["hold_min_ticks"]
            event = {"tick": n["tick"], "source_note_id": sid, "part_id": part["id"], "slot_id": part["slot_id"],
                     "family": family, "button": button, "type": "hold" if is_hold else "tap", "midi_note": n["midi_note"], "velocity": n["velocity"]}
            if is_hold:
                event["duration_ticks"] = n["duration_ticks"]
                # Preserve musical lengths. Any mode-boundary issue is an authoring error to resolve explicitly.
                for s in sections:
                    if s["mode"] == "drums" and max(n["tick"], s["start_tick"]) < min(n["tick"] + n["duration_ticks"], s["start_tick"] + s["length_bars"] * bar_ticks):
                        raise ValueError(f"Bass hold {sid} crosses into drum mode; revise MIDI or section map")
            notes.append(event)
    referenced_ids = set(rules.get("note_button_overrides", {})) | excluded_ids | set(included_ids or [])
    if referenced_ids - known_ids:
        raise ValueError("Chart rules refer to unknown source-note IDs")
    notes.sort(key=lambda n: (n["tick"], n["button"]))
    for i, n in enumerate(notes, 1):
        n["id"] = f"n{i:04d}"
        if n["button"] not in (1, 2, 3, 4):
            raise ValueError("Invalid physical button")
    for b in range(1, 5):
        row = [n for n in notes if n["button"] == b]
        for a, c in zip(row, row[1:]):
            gap = c["tick"] - a["tick"] - a.get("duration_ticks", 0)
            minimum = rules["hold_release_gap_ticks"] if a["type"] == "hold" else 1
            if gap < minimum:
                raise ValueError(f"Button conflict/release gap: {a['id']} -> {c['id']}")
    peak = 0
    for tick in {n["tick"] for n in notes}:
        active = {n["button"] for n in notes if n["tick"] == tick or (n["type"] == "hold" and n["tick"] < tick < n["tick"] + n["duration_ticks"])}
        peak = max(peak, len(active))
    if peak > rules["max_simultaneous_touches"]:
        raise ValueError("Chart exceeds touch budget")
    validate_thumb_layout(notes, rules)
    out = {"format": "rhythm_warfare.defense_authoring_chart.v1", "level_id": song["level_id"], "bpm": bpm,
           "chart_id": rules.get("chart_id", song["level_id"] + ".campaign"), "play_mode": rules.get("play_mode", "campaign"),
           "progression_enabled": rules.get("play_mode", "campaign") == "campaign",
           "time_signature": song["time_signature"], "ticks_per_beat": ppq, "song_offset_ms": 0, "duration_ticks": end,
           "sections": sections, "notes": notes, "source_sha256": source_hashes,
           "runtime_compatibility": "Proposed interchange; Claude must adapt the game's loader and reward path."}
    if not write:
        out["omitted_notes"] = omitted
        return out
    output_path.write_text(json.dumps(out, indent=2) + "\n")
    audit_name = "chart_audit.json" if output_name == "player_chart.json" else output_path.stem + "_audit.json"
    (output_path.parent / audit_name).write_text(json.dumps({"omitted_notes": omitted, "max_required_touches": peak, "changed_musical_lengths": [], "changed_musical_onsets": []}, indent=2) + "\n")
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--rules", default="chart_rules.json")
    parser.add_argument("--out", default="player_chart.json")
    args = parser.parse_args()
    result = compile_chart(args.directory, args.rules, args.out)
    print(json.dumps({"level_id": result["level_id"], "notes": len(result["notes"]), "duration_ticks": result["duration_ticks"]}))
