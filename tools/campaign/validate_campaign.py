"""Independent structural checks for the first-three authoring examples, not battle balance.

Usage: python validate_campaign.py PACK_ROOT
Requires mido==1.3.3. Runs negative converter checks in temporary directories.
"""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

import mido
from compile_chart import compile_chart, read_notes, validate_thumb_layout

root = Path(sys.argv[1])
checks, summaries = [], []


def check(name, value):
    checks.append({"check": name, "passed": bool(value)})


campaign = json.loads((root / "Plan/campaign.proposed.json").read_text())
catalogue = json.loads((root / "Plan/instrument_catalogue.proposed.json").read_text())["instruments"]
catalogue = {p["id"]: p for p in catalogue}
check("ten ordered levels and caps 2 kick / 2 snare / 3 bass", len(campaign["levels"]) == 10 and [l["number"] for l in campaign["levels"]] == list(range(1, 11)) and campaign["loadout_caps"] == {"kick": 2, "snare": 2, "bass": 3})
check("duration is not used as a mandatory difficulty ladder", len({l["bars"] for l in campaign["levels"]}) < len(campaign["levels"]) and len({l["learning_goal"] for l in campaign["levels"]}) == 10)
check("future levels are plans, not claimed generated music", all(l["status"] == "planned" for l in campaign["levels"][3:]))
check("kick can produce infantry independently of button/family", catalogue["kick_march"]["production"]["steps"][0]["units"] == [{"actor": "e1", "count": 2}])
check("heavy kick deterministically alternates heavy and light tanks", [s["units"][0]["actor"] for s in catalogue["kick_heavy"]["production"]["steps"]] == ["3tnk", "1tnk"])

for level_number, expected_notes, expected_holds, expected_buttons in [(1, 64, 0, {1, 4}), (2, 96, 0, {1, 2, 4}), (3, 89, 29, {1, 2, 3, 4})]:
    level = root / "First_Three" / f"level_{level_number:02d}"
    song = json.loads((level / "song.json").read_text())
    chart = json.loads((level / "player_chart.json").read_text())
    rules = json.loads((level / "chart_rules.json").read_text())
    notes = chart["notes"]
    prefix = song["level_id"] + ": "
    check(prefix + "expected event/hold/button progression", len(notes) == expected_notes and sum(n["type"] == "hold" for n in notes) == expected_holds and {n["button"] for n in notes} == expected_buttons)
    check(prefix + "positive, ordered unique inputs", notes == sorted(notes, key=lambda n: (n["tick"], n["button"])) and len({n["id"] for n in notes}) == len(notes))
    check(prefix + "proposed chart does not claim runtime compatibility", "schema_version" not in chart and chart["format"] == "rhythm_warfare.defense_authoring_chart.v1" and "Proposed" in chart["runtime_compatibility"])
    check(prefix + "slots have unlocked family-compatible default profiles", all(slot in song["active_loadout_slots"] and catalogue[profile]["available_from_level"] <= level_number and slot.startswith(catalogue[profile]["family"]) for slot, profile in song["default_loadout"].items()))
    counts = Counter(slot.split("_")[0] for slot in song["active_loadout_slots"])
    check(prefix + "slot caps respected", all(counts[f] <= campaign["loadout_caps"][f] for f in counts))
    check(prefix + "every required part has an equipped default", set(song["active_loadout_slots"]) == set(song["default_loadout"]))
    expected_selected, score_lookup, all_musical = [], {}, []
    for part in song["parts"]:
        path = level / part["midi"]
        musical, tempos, meters = read_notes(path, 960)
        midi = mido.MidiFile(path)
        check(prefix + part["id"] + " exact tempo and common MIDI end", tempos == [(0, 344828)] and meters == [(0, 4, 4)] and all(sum(msg.time for msg in tr) == chart["duration_ticks"] for tr in midi.tracks))
        check(prefix + part["id"] + " source hash matches", hashlib.sha256(path.read_bytes()).hexdigest() == chart["source_sha256"][part["id"]])
        all_musical.extend((n["tick"], n["duration_ticks"], n["midi_note"], n["velocity"]) for n in musical)
        for i, n in enumerate(musical, 1):
            sid = f"{part['id']}:{i:04d}"
            score_lookup[sid] = n
            s = next(s for s in chart["sections"] if s["start_tick"] <= n["tick"] < s["start_tick"] + s["length_bars"] * 3840)
            playable = part["family"] in ("kick", "snare", "bass") and ((part["family"] == "bass") == (s["mode"] == "bass"))
            if playable:
                expected_selected.append(sid)
    check(prefix + "all and only selected-family source notes charted", {n["source_note_id"] for n in notes} == set(expected_selected))
    check(prefix + "chart retains actual musical timing/pitch/velocity", all((n["tick"], n["midi_note"], n["velocity"]) == (score_lookup[n["source_note_id"]]["tick"], score_lookup[n["source_note_id"]]["midi_note"], score_lookup[n["source_note_id"]]["velocity"]) for n in notes))
    check(prefix + "long holds retain full source durations", all(n["duration_ticks"] == score_lookup[n["source_note_id"]]["duration_ticks"] for n in notes if n["type"] == "hold"))
    master, _, _ = read_notes(level / "References/Full_Music_Master.mid", 960)
    check(prefix + "full musical master is exact union, not chart subset", sorted(all_musical) == sorted((n["tick"], n["duration_ticks"], n["midi_note"], n["velocity"]) for n in master))
    mixed, conflicts = [], []
    for b in range(song["bars"]):
        active = [n for n in notes if b * 3840 <= n["tick"] < (b + 1) * 3840 or (n["type"] == "hold" and n["tick"] < b * 3840 < n["tick"] + n["duration_ticks"])]
        if len({"bass" if n["family"] == "bass" else "drums" for n in active}) > 1:
            mixed.append(b + 1)
    check(prefix + "no mixed drum/bass bars including held tails", not mixed)
    for button in range(1, 5):
        row = [n for n in notes if n["button"] == button]
        for a, b in zip(row, row[1:]):
            if b["tick"] <= a["tick"] + a.get("duration_ticks", 0):
                conflicts.append((a["id"], b["id"]))
    check(prefix + "no same-button conflicts", not conflicts)
    peak = max(len({n["button"] for n in notes if n["tick"] == t or (n["type"] == "hold" and n["tick"] < t < n["tick"] + n["duration_ticks"])}) for t in {n["tick"] for n in notes})
    check(prefix + "at most two required touches", peak <= 2)
    validate_thumb_layout(notes, rules)
    check(prefix + "per-thumb occupancy and release gaps validated", bool(rules.get("thumb_constraints")))
    waves = json.loads((level / "waves.proposed.json").read_text())
    check(prefix + "waves start after teaching/build-up and finish spawning before song end", min(w["start_tick"] for w in waves["waves"]) >= 4 * 3840 and all(w["start_tick"] + (g["count"] - 1) * g["spawn_spacing_ticks"] < chart["duration_ticks"] for w in waves["waves"] for g in w["groups"]))
    check(prefix + "waves explicitly untuned", "Untuned" in waves["status"])
    check(prefix + "separate equipped-slot renders plus Other", song["recommended_export"]["separate_buses"] == song["active_loadout_slots"] + ["other"] and song["recommended_export"]["end_bar_exclusive"] == song["bars"] + 2)
    if level_number == 3:
        check(prefix + "one bass instrument uses all four physical buttons", {n["button"] for n in notes if n["part_id"] == "bass_1"} == {1, 2, 3, 4})
        check(prefix + "half/full/two-bar bass holds all present", {1920, 3840, 7680}.issubset({n["duration_ticks"] for n in notes if n["type"] == "hold"}))
        check(prefix + "music drums remain audible candidates during bass sections", len([n for n in score_lookup if n.startswith("kick_1")]) > len([n for n in notes if n["part_id"] == "kick_1"]))
        bass = [n for n in notes if n["family"] == "bass"]
        for section in [s for s in chart["sections"] if s["mode"] == "bass"]:
            phrase = [n for n in bass if section["start_tick"] <= n["tick"] < section["start_tick"] + section["length_bars"] * 3840]
            check(prefix + section["id"] + " bass motif alternates thumbs", all((a["button"] <= 2) != (b["button"] <= 2) for a, b in zip(phrase, phrase[1:])))
    if level_number == 2:
        practice = json.loads((level / "player_chart.practice.json").read_text())
        check(prefix + "practice and campaign share identical source audio/MIDI identity", practice["source_sha256"] == chart["source_sha256"])
        check(prefix + "practice selects 80 essential notes while 16 extra kicks remain in music", len(practice["notes"]) == 80 and all(n["part_id"] != "kick_2" for n in practice["notes"]) and len(notes) == 96)
        check(prefix + "practice has separate chart ID and no progression", practice["chart_id"] != chart["chart_id"] and practice["play_mode"] == "practice" and practice["progression_enabled"] is False)
    summaries.append({"level_id": song["level_id"], "notes": len(notes), "holds": expected_holds, "maximum_required_touches": peak, "balance_tested": False})

# Meaningful failure cases: stale tempo, hold/mode leakage and authored button collisions must fail.
for case in ("tempo_mismatch", "hold_crosses_mode", "button_collision", "thumb_reach_conflict", "source_override_stale"):
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / "level"
        shutil.copytree(root / "First_Three/level_03", dest)
        song = json.loads((dest / "song.json").read_text())
        rules = json.loads((dest / "chart_rules.json").read_text())
        if case == "tempo_mismatch":
            song["bpm"] = 175
            (dest / "song.json").write_text(json.dumps(song))
        elif case == "hold_crosses_mode":
            # Move the first bass/drum switch one bar earlier: a two-half-note bass bar now leaks into drums.
            rules["sections"][1]["bars"] = 7
            rules["sections"][2]["start_bar"] = 16
            rules["sections"][2]["bars"] = 9
            rules.pop("expected_source_sha256", None)
            (dest / "chart_rules.json").write_text(json.dumps(rules))
            # Extend the first bass note of bar 15 through bar 16 so its onset remains in bass mode.
            path = dest / "Music/bass_1.mid"
            midi = mido.MidiFile(path)
            tr = midi.tracks[1]
            absolute, tick = [], 0
            for msg in tr:
                tick += msg.time
                if msg.type == "note_off" and tick == 15 * 3840 and msg.note == 35:
                    tick_target = 16 * 3840
                else:
                    tick_target = tick
                absolute.append((tick_target, msg))
            absolute.sort(key=lambda p: p[0])
            previous = 0
            for i, (when, msg) in enumerate(absolute):
                tr[i] = msg.copy(time=when - previous)
                previous = when
            midi.save(path)
        elif case == "button_collision":
            rules["button_rules"]["bass_1"] = {"button": 1}
            rules.pop("note_button_overrides", None)
            (dest / "chart_rules.json").write_text(json.dumps(rules))
        elif case == "thumb_reach_conflict":
            rules.pop("note_button_overrides", None)
            (dest / "chart_rules.json").write_text(json.dumps(rules))
        else:
            path = dest / "Music/bass_1.mid"
            midi = mido.MidiFile(path)
            midi.tracks[0].name = "changed source revision"
            midi.save(path)
        try:
            compile_chart(dest)
            rejected = False
        except ValueError as error:
            expected = {"tempo_mismatch": "tempo", "hold_crosses_mode": "crosses into drum", "button_collision": "Button conflict", "thumb_reach_conflict": "Thumb hold/reach", "source_override_stale": "Source MIDI changed"}[case]
            rejected = expected in str(error)
        check("converter rejects " + case, rejected)

try:
    validate_thumb_layout([{"id": "hold_left", "tick": 0, "button": 1, "type": "hold", "duration_ticks": 3840}, {"id": "tap_left_other_column", "tick": 1920, "button": 2, "type": "tap"}],
                          {"thumb_constraints": {"min_hold_release_to_same_thumb_press_ticks": 480, "min_same_thumb_onset_gap_ticks": 960}})
    same_hand_rejected = False
except ValueError:
    same_hand_rejected = True
check("two touches on one thumb's side are rejected despite global two-touch allowance", same_hand_rejected)

baseline_path = root / "Musical_Source_Integrity.json"
if baseline_path.exists():
    baseline = json.loads(baseline_path.read_text())["before_sha256"]
    check("all 18 musical MIDI files byte-identical to the pre-research pack", len(baseline) == 18 and all(hashlib.sha256((root / rel).read_bytes()).hexdigest() == digest for rel, digest in baseline.items()))

report = {"passed": all(c["passed"] for c in checks), "checks_passed": sum(c["passed"] for c in checks), "checks_total": len(checks), "levels": summaries,
          "godot_integration_tested": False, "wave_balance_tested": False, "audio_rendered_or_aligned": False, "checks": checks}
(root / "Validation_Report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: report[k] for k in ("passed", "checks_passed", "checks_total", "levels")}, indent=2))
if not report["passed"]:
    print(json.dumps([c for c in checks if not c["passed"]], indent=2))
    raise SystemExit(1)
