"""Generate first-three MIDI examples plus proposed campaign/loadout/wave data.

Requires mido==1.3.3. Usage: python build_campaign.py OUTPUT_DIR
Reference authoring data only; no engine changes or balance claims.
"""
from collections import Counter
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import sys

import mido

from compile_chart import compile_chart, read_notes

BPM, PPQ, BAR = 174, 960, 3840
TEMPO = mido.bpm2tempo(BPM)


def dump(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def group(*actors):
    return {"units": [{"actor": a, "count": count} for a, count in actors]}


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    road = [
        (1, "First Watch", 32, "Two outer buttons; steady half-time pulse", ["kick_1", "snare_1"], ["kick_march", "snare_guard"], "One approach; one core"),
        (2, "Second Pulse", 40, "Add a third input and a second kick", ["kick_1", "kick_2", "snare_1"], ["kick_armour"], "Alternating approaches; one core"),
        (3, "Hold the Line", 48, "Introduce bass mode and long holds across all four buttons", ["kick_1", "kick_2", "snare_1", "bass_1"], ["bass_patrol"], "Three approaches; one core"),
        (4, "Backbeat", 48, "Second snare and first full-time drum passages", ["kick_1", "kick_2", "snare_1", "snare_2", "bass_1"], ["snare_crack"], "Staggered infantry groups"),
        (5, "Counterpoint", 56, "Second bass voice; hold plus opposite-thumb answering line", ["kick_1", "kick_2", "snare_1", "snare_2", "bass_1", "bass_2"], ["bass_reese"], "Two simultaneous approach waves"),
        (6, "Fortress", 56, "Review learned rhythms; support loadout and two objectives", ["kick_1", "kick_2", "snare_1", "snare_2", "bass_1", "bass_2"], ["kick_siege"], "Armour support; two cores"),
        (7, "Airbridge", 64, "Three audible bass voices; chart at most two thumb roles", ["kick_1", "kick_2", "snare_1", "snare_2", "bass_1", "bass_2", "bass_3"], ["bass_growl"], "Ground threats pressure three points"),
        (8, "Crossfire", 64, "Opposite-hand accents; anti-air loadout before enemy air", ["kick_1", "kick_2", "snare_1", "snare_2", "bass_1", "bass_2", "bass_3"], ["snare_flak"], "Mixed ground/air waves"),
        (9, "Iron Rhythm", 64, "Heavy/light tank cycle and more syncopation", ["kick_1", "kick_2", "snare_1", "snare_2", "bass_1", "bass_2", "bass_3"], ["kick_heavy"], "Coordinated armour pushes"),
        (10, "Last Light", 80, "Combine rehearsed motifs with recovery phrases", ["kick_1", "kick_2", "snare_1", "snare_2", "bass_1", "bass_2", "bass_3"], ["bass_command"], "Final multi-route survival; two cores"),
    ]
    profiles = [
        ("kick_march", "March Kick", "kick", 1, [group(("e1", 2))], ["barracks"]),
        ("snare_guard", "Guard Snare", "snare", 1, [group(("jeep", 1))], ["war_factory"]),
        ("kick_armour", "Armour Kick", "kick", 2, [group(("1tnk", 1)), group(("jeep", 1))], ["war_factory"]),
        ("bass_patrol", "Patrol Sub", "bass", 3, [group(("e1", 2), ("e3", 1))], ["barracks"]),
        ("snare_crack", "Crack Snare", "snare", 4, [group(("e1", 2), ("e2", 1))], ["barracks"]),
        ("bass_reese", "Armoured Reese", "bass", 5, [group(("2tnk", 1)), group(("1tnk", 1))], ["war_factory"]),
        ("kick_siege", "Siege Kick", "kick", 6, [group(("arty", 1)), group(("1tnk", 1)), group(("jeep", 1))], ["war_factory"]),
        ("bass_growl", "Air Growl", "bass", 7, [], ["air_support"]),
        ("snare_flak", "Flak Snare", "snare", 8, [group(("ftrk", 1)), group(("e3", 2))], ["war_factory", "barracks"]),
        ("kick_heavy", "Heavy Kick", "kick", 9, [group(("3tnk", 1)), group(("1tnk", 1))], ["war_factory"]),
        ("bass_command", "Command Bass", "bass", 10, [group(("4tnk", 1)), group(("e1", 2), ("e3", 1))], ["war_factory", "barracks"]),
    ]
    instruments = []
    for ident, title, family, unlock, steps, producers in profiles:
        p = {"id": ident, "display_name": title, "family": family, "available_from_level": unlock,
             "sound_profile_id": ident + "_sound", "production_profile_id": ident + "_production",
             "production": {"type": "cycle", "steps": steps, "required_producers": producers, "advance_on": "successful_available_reward_only", "cycle_scope": "equipped_slot"},
             "sound": {"renderer": "owner_Ableton_export", "preset": None, "render_status": "not_rendered", "note": "Choose a stable patch/sample, save its settings, and render each song part that uses this profile."}}
        if ident == "bass_growl":
            p["production"] = {"type": "air_service", "aircraft_actor": "heli", "pad_actor": "hpad", "aircraft_limit": 5, "pad_limit": 5,
                               "ammo": 8, "required_producers": ["air_support"], "note": "Later-level recipe; adapt existing pad build/rearm/sortie rules explicitly. Not used by levels 1-3."}
        instruments.append(p)
    dump(out / "Plan/instrument_catalogue.proposed.json", {"format": "defense_instrument_catalogue.proposed.v1", "status": "Unbalanced design examples; render assets and engine integration required.", "instruments": instruments})
    progression = []
    for n, title, bars, skill, slots, unlocks, waves in road:
        progression.append({"number": n, "level_id": f"level_{n:02d}", "title": title, "bars": bars, "bpm": BPM,
                            "duration_seconds": bars * 4 * 60 / BPM, "learning_goal": skill, "active_slots": slots,
                            "profiles_available_on_entry": unlocks, "battle_goal": waves,
                            "critical_objectives": 1 if n <= 5 else 2, "status": "authored_reference" if n <= 3 else "planned"})
    dump(out / "Plan/campaign.proposed.json", {"format": "defense_campaign.proposed.v1", "unlock_policy": "Clearing level n unlocks level n+1 and its entry profiles; no accuracy threshold blocks the main ladder.", "loadout_caps": {"kick": 2, "snare": 2, "bass": 3}, "distinct_profiles_within_family": True, "levels": progression})
    dump(out / "Plan/defense_rules.proposed.json", {
        "format": "defense_rules.proposed.v1", "game_mode": "defense", "critical_objective_policy": "All required objectives must remain alive; lose immediately when any is destroyed; win at authored song end otherwise.",
        "outcome_tie_policy": "Process rewards and combat through the boundary, then objective losses, then song-end survival. Objective loss takes precedence in the same tick.",
        "defense_points": ["defense_1", "defense_2", "defense_3"], "assignment": "Round-robin per successful production group, not per member. Members go together; next group advances the point. Failed/unavailable rewards do not advance it.",
        "friendly_behavior": "Move to assigned point, defend locally, return after limited pursuit. Successive groups rotate points; troops are not required to patrol all three points.",
        "enemy_behavior": "Authored off-map/boundary entry waves; follow route via a defense point toward a critical objective, fighting nearby blockers. No enemy base or producer exists.",
        "producer_availability": "Each equipped instrument slot is enabled only while all of its production profile's required producer tags are available. Disable prompts and mute that slot's audio when unavailable; restore slot gain in place if eligibility returns. Mode changes do not mute audio.",
        "repair": "Reuse finite, data-driven OpenRA repair; tune per level. Required core destruction cannot be reversed to cancel a loss.",
        "hold_reward": "One successful reward at the held note's tail. No repeated income while held.",
        "input": {"physical_buttons": 4, "max_required_touches": 2, "labels": "unlabelled; musical placement is authored independently of instrument, slot and unit reward"},
        "level_01_to_03_objectives": ["command_core"], "level_06_onward_objectives": ["command_core", "tech_core"],
        "wave_balance_status": "untuned", "runtime_status": "proposal; requires new map/simulation/loader integration"
    })

    summaries = []
    for number, title, bars, _, slots, _, _ in road[:3]:
        level_id = f"level_{number:02d}"
        directory = out / "First_Three" / level_id
        directory.mkdir(parents=True, exist_ok=True)
        end = bars * BAR
        source = {slot: [] for slot in slots}
        source.update({"other_pad": [], "other_hats": []})

        def add(part, bar, beat, duration_beats, pitch, velocity=103):
            start = (bar - 1) * BAR + round(beat * PPQ)
            duration = round(duration_beats * PPQ)
            assert 0 <= start < start + duration <= end
            source[part].append({"tick": start, "duration": duration, "pitch": pitch, "velocity": velocity})

        def chord(bar):
            if bar == bars:
                return "C#m", 37
            return [("C#m", 37), ("A", 33), ("E", 40), ("B", 35)][((bar - 1) % 8) // 2]

        for bar in range(1, bars + 1):
            add("kick_1", bar, 0 if number > 1 or bar % 2 else 1, .125, 36, 110)
            add("snare_1", bar, 2, .125, 38, 108)
            if number >= 2 and bar % 2 and (number == 3 or bar >= 9):
                add("kick_2", bar, 3, .125, 48, 100)

        if number == 3:
            # The same bass instrument drives all four physical buttons by melodic contour.
            for first in (9, 25, 41):
                pattern = [(0, 0, 4, 37), (1, 0, 2, 40), (1, 2, 2, 37), (2, 0, 8, 33),
                           (4, 0, 4, 40), (5, 0, 2, 32), (5, 2, 2, 40), (6, 0, 4, 35)]
                pattern += [(7, 0, 2, 37)] if first == 41 else [(7, 0, 2, 39), (7, 2, 2, 42)]
                for offset, beat, length, pitch in pattern:
                    add("bass_1", first + offset, beat, length, pitch, 105)
            # Audible bass accompaniment remains present during drum-play passages.
            for bar in list(range(1, 9, 2)) + list(range(17, 25, 2)) + list(range(33, 41, 2)):
                add("bass_1", bar, 0, 8, chord(bar)[1], 87)

        voicings = {"C#m": [61, 64, 68], "A": [57, 61, 64], "E": [59, 64, 68], "B": [59, 63, 66]}
        for bar in range(1, bars + 1):
            for pitch in voicings[chord(bar)[0]]:
                add("other_pad", bar, 0, 3.75, pitch, 53)
            if bar >= 5:
                for beat in ([0, 2] if number == 1 else [0, 1, 2, 3]):
                    add("other_hats", bar, beat, .125, 42, 56)

        if number < 3:
            sections = [{"id": f"drums_{i//8+1}", "start_bar": i + 1, "bars": min(8, bars - i), "mode": "drums"} for i in range(0, bars, 8)]
        else:
            sections = [{"id": f"{'drums' if i%2==0 else 'bass'}_{i//2+1}", "start_bar": i * 8 + 1, "bars": 8, "mode": "drums" if i % 2 == 0 else "bass"} for i in range(6)]
        parts = []
        for part in source:
            family = "kick" if part.startswith("kick") else "snare" if part.startswith("snare") else "bass" if part.startswith("bass") else "other"
            parts.append({"id": part, "family": family, "slot_id": part if family != "other" else None,
                          "midi": f"Music/{part}.mid", "render_bus": part if family != "other" else "other"})

        def write_midi(path, selected_parts):
            path.parent.mkdir(parents=True, exist_ok=True)
            midi = mido.MidiFile(type=1, ticks_per_beat=PPQ)
            midi.tracks.append(mido.MidiTrack([mido.MetaMessage("track_name", name="Conductor"), mido.MetaMessage("set_tempo", tempo=TEMPO), mido.MetaMessage("time_signature", numerator=4, denominator=4), mido.MetaMessage("key_signature", key="C#m"), mido.MetaMessage("end_of_track", time=end)]))
            for index, part in enumerate(selected_parts):
                channel = 9 if part.startswith(("kick", "snare")) or part == "other_hats" else 0 if part == "bass_1" else 4
                events = [(0, -3, mido.MetaMessage("track_name", name=part))]
                for s in sections:
                    events.append(((s["start_bar"] - 1) * BAR, -2, mido.MetaMessage("marker", text=s["id"])))
                for note in source[part]:
                    events.append((note["tick"], 1, mido.Message("note_on", channel=channel, note=note["pitch"], velocity=note["velocity"])))
                    events.append((note["tick"] + note["duration"], 0, mido.Message("note_off", channel=channel, note=note["pitch"], velocity=0)))
                events.append((end, 9, mido.MetaMessage("end_of_track")))
                events.sort(key=lambda e: (e[0], e[1]))
                tr, previous = mido.MidiTrack(), 0
                for tick, _, msg in events:
                    tr.append(msg.copy(time=tick - previous))
                    previous = tick
                midi.tracks.append(tr)
            midi.save(path)

        for p in parts:
            write_midi(directory / p["midi"], [p["id"]])
        write_midi(directory / "References/Full_Music_Master.mid", list(source))
        button_rules = {"kick_1": {"button": 1}, "snare_1": {"button": 4}}
        if number >= 2:
            button_rules["kick_2"] = {"button": 2}
        if number == 3:
            button_rules["bass_1"] = {"pitch_ranges": [{"min": 0, "max": 33, "button": 1}, {"min": 34, "max": 35, "button": 2}, {"min": 36, "max": 39, "button": 3}, {"min": 40, "max": 127, "button": 4}]}
        default_loadout = {"kick_1": "kick_march", "snare_1": "snare_guard"}
        if number >= 2:
            default_loadout["kick_2"] = "kick_armour"
        if number == 3:
            default_loadout["bass_1"] = "bass_patrol"
        song = {"format": "rhythm_warfare.defense_song_authoring.v1", "level_id": level_id, "title": title,
                "bpm": BPM, "ticks_per_beat": PPQ, "time_signature": [4, 4], "key": "C# minor", "bars": bars,
                "parts": parts, "active_loadout_slots": slots, "default_loadout": default_loadout,
                "recommended_export": {"sample_rate_hz": 48000, "pcm_bits": 16, "start_bar": 1, "end_bar_exclusive": bars + 2,
                                       "seconds_including_one_bar_tail": (bars + 1) * 4 * 60 / BPM,
                                       "separate_buses": [*slots, "other"], "normalize": False},
                "runtime_status": "Authoring example only. WAVs, engine migration, map and balance validation are outstanding."}
        dump(directory / "song.json", song)
        chart_rules = {"format": "defense_chart_rules.v1", "chart_id": level_id + ".campaign", "play_mode": "campaign",
                       "hold_min_ticks": 480, "hold_release_gap_ticks": 240, "max_simultaneous_touches": 2,
                       "sections": sections, "button_rules": button_rules,
                       "thumb_constraints": {"min_hold_release_to_same_thumb_press_ticks": 480, "min_same_thumb_onset_gap_ticks": 960}}
        if number == 3:
            bass_notes, _, _ = read_notes(directory / "Music/bass_1.mid", PPQ)
            placement = [1, 4, 1, 3, 2, 3, 2, 3, 2, 4]
            overrides = {}
            for first in (9, 25, 41):
                phrase = [(i, n) for i, n in enumerate(bass_notes, 1) if (first - 1) * BAR <= n["tick"] < (first + 7) * BAR]
                for ordinal, (i, n) in enumerate(phrase):
                    # Repeated phrase footprint alternates thumbs; closing tonic returns to button 1.
                    overrides[f"bass_1:{i:04d}"] = 1 if first == 41 and ordinal == len(phrase) - 1 else placement[ordinal]
            chart_rules["note_button_overrides"] = overrides
            chart_rules["expected_source_sha256"] = {"bass_1": hashlib.sha256((directory / "Music/bass_1.mid").read_bytes()).hexdigest()}
        dump(directory / "chart_rules.json", chart_rules)
        chart = compile_chart(directory)
        if number == 2:
            practice = deepcopy(chart_rules)
            practice.update({"chart_id": level_id + ".practice", "play_mode": "practice", "selection": {"exclude_part_ids": ["kick_2"]}})
            dump(directory / "chart_rules.practice.json", practice)
            compile_chart(directory, "chart_rules.practice.json", "player_chart.practice.json")

        # Wave targets are symbolic entries/points. Claude maps these to the actual new battlefield.
        waves = []
        for i, start_bar in enumerate(range(5, bars, 4)):
            entry = "center" if number == 1 else ["left", "center", "right"][i % 3]
            point = {"left": "defense_1", "center": "defense_2", "right": "defense_3"}[entry]
            groups = [{"actor": "e1", "count": 4 + i + number, "spawn_spacing_ticks": 240}]
            if i >= 3:
                groups.append({"actor": "jeep", "count": 1 + (i >= 6), "spawn_spacing_ticks": 480})
            if number >= 2 and i >= 5:
                groups.append({"actor": "1tnk", "count": 1, "spawn_spacing_ticks": 480})
            waves.append({"id": f"wave_{i+1:02d}", "start_tick": (start_bar - 1) * BAR, "start_bar": start_bar,
                          "entry": entry, "via_defense_point": point, "target_objective": "command_core", "groups": groups})
        dump(directory / "waves.proposed.json", {"format": "defense_waves.proposed.v1", "status": "Untuned authored starting point, not tested battle balance. Spawn one burst per wave group, never an enemy producer/base.",
                                                 "parallel_groups_within_wave": True, "critical_objectives": ["command_core"], "waves": waves})
        with (directory / "Render_Checklist.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["level_id", "slot_or_bus", "instrument_profile", "WAV_name", "midi_source", "start_bar", "end_bar_exclusive"])
            for slot in slots:
                w.writerow([level_id, slot, default_loadout[slot], f"audio/{slot}__{default_loadout[slot]}.wav", f"Music/{slot}.mid", 1, bars + 2])
            w.writerow([level_id, "other", "accompaniment", "audio/other.wav", "Music/other_pad.mid + Music/other_hats.mid", 1, bars + 2])
        summaries.append({"level_id": level_id, "title": title, "bars": bars, "duration_seconds": bars * 4 * 60 / BPM,
                          "source_note_counts": {k: len(ns) for k, ns in source.items()}, "charted_notes": len(chart["notes"]),
                          "charted_parts": dict(Counter(n["part_id"] for n in chart["notes"])), "holds": sum(n["type"] == "hold" for n in chart["notes"]),
                          "physical_buttons_used": sorted({n["button"] for n in chart["notes"]}), "wave_count": len(waves), "balance_tested": False})
    dump(out / "First_Three/Build_Summary.json", summaries)
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    build(Path(sys.argv[1]))
