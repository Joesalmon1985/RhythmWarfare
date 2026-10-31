class_name Level
extends RefCounted
## One loaded song pack: the level definition plus resolved stem paths.
## Timing authority: integer ticks (ticks_per_beat per quarter note), bar 1 at tick 0.
## event_seconds = song_offset_ms / 1000 + tick * 60 / (bpm * ticks_per_beat)
##
## A note has a lane (kick, snare or bass: what it rewards and which stem it belongs to) and a button (1 to 4:
## which of the four unlabelled touch buttons it is played on). Kick notes are always button 1 and snare notes
## always button 4; bass notes may use any button, so a bass pattern can run across all four.

const LANES := ["kick", "snare", "bass"]
const ACTIONS := ["kick", "snare", "bass"]
const NOTE_TYPES := ["tap", "hold"]
const STEM_KEYS := ["kick", "snare", "bass", "other"]
const BUTTONS := 4
const FAMILIES := ["kick", "snare", "bass"]
## Left thumb plays buttons 1 and 2, right thumb 3 and 4 (schema 2 charts are validated per thumb).
const THUMB_OF_BUTTON := {1: 0, 2: 0, 3: 1, 4: 1}
const FIXED_BUTTON := {"kick": 1, "snare": 4}
## Bass notes that carry no button alternate between the two inner buttons, which kick and snare never use.
const DEFAULT_BASS_BUTTONS := [2, 3]

var pack_dir: String = ""
var schema_version := 1
var mode := "duel"  # "duel" (schema 1) or "defense" (schema 2)
var campaign_level := 0
var chart_id := ""
var play_mode := "campaign"  # "campaign" or "practice" (schema 2 chart)
var progression := true
var charts: Array = []  # schema 2: every chart of the pack ({chart_id, play_mode, progression, sections, notes})
var renders: Dictionary = {}  # schema 2: slot id -> profile id -> {file, source_sha256, sample_rate, frames, placeholder}
var loadout_active_slots: Array = []
var loadout_default: Dictionary = {}
var loadout: Dictionary = {}  # slot id -> profile id actually equipped for this load
var waves: Array = []
var source: Dictionary = {}
var parts: Array = []
var level_id: String = ""
var title: String = ""
var bpm: float = 174.0
var beats_per_bar: int = 4
var ticks_per_beat: int = 960
var song_offset_ms: int = 0
var duration_ticks: int = 0
var seed: int = 0
var stems: Dictionary = {}  # stem key -> absolute file path
var battlefield: String = ""
var roster: String = ""
var rules: Dictionary = {}
var sections: Array = []  # [{id, start_tick, length_bars}]
var notes: Array = []  # schema 1: [{id, tick, lane, button, type, duration_ticks, time, end_time}] sorted by tick then button
var enemy_events: Array = []  # [{id, tick, action, time}] sorted by tick
var stem_lengths: Dictionary = {}  # stem key -> seconds, when the loader could decode them
# schema 3 (missions, MissionLoader): the player's choices, the chosen selection, sequences with rewards
var choices: Array = []  # [{id, label, count, default, pool: [{id, name}]}]
var selection: Dictionary = {}  # choice id -> [option ids in slot order]
var names: Dictionary = {}  # library id -> friendly name
var previews: Dictionary = {}  # choice id -> option id -> preview file (relative to the pack)
var content: Dictionary = {}  # build report: files, placeholder_files, owner_files, default_mix_peak_db
var placeholder := false
var placeholder_stems := 0
var stem_family: Dictionary = {}  # stem key -> kick, snare, bass, other
var sequences: Array = []  # [{index, phase, mode, start_tick, end_tick, start_time, end_time, reward, cues}]
var sequence_threshold := 0.6
var intro := ""


func ticks_per_bar() -> int:
	return ticks_per_beat * beats_per_bar


func tick_to_seconds(tick: int) -> float:
	return float(song_offset_ms) / 1000.0 + float(tick) * 60.0 / (bpm * float(ticks_per_beat))


func seconds_to_tick(seconds: float) -> int:
	return int(round((seconds - float(song_offset_ms) / 1000.0) * bpm * float(ticks_per_beat) / 60.0))


func duration_seconds() -> float:
	return tick_to_seconds(duration_ticks)


func bar_of_tick(tick: int) -> int:
	return tick / ticks_per_bar() + 1


func is_defense() -> bool:
	return mode == "defense"


func is_mission() -> bool:
	return schema_version == 3


## The phase (section) at a song tick, or {} outside the song.
func phase_at(tick: int) -> Dictionary:
	for s in sections:
		if tick >= int(s["start_tick"]) and tick < int(s["end_tick"]):
			return s
	return {}


## Friendly name of a selected voice reference such as "kick_sound#1" or a fixed sound id.
func voice_name(ref: String) -> String:
	if ref.contains("#"):
		var bits := ref.split("#")
		var picked: Array = selection.get(bits[0], [])
		var slot := int(bits[1]) - 1
		if slot >= 0 and slot < picked.size():
			return str(names.get(picked[slot], picked[slot]))
		return ref
	return str(names.get(ref, ref))


func chart_ids() -> Array:
	var out: Array = []
	for c in charts:
		out.append(c["chart_id"])
	return out


## Slot ids of the notes of the loaded chart in first-appearance order.
func slot_ids() -> Array:
	var out: Array = []
	for n in notes:
		if not out.has(n["slot_id"]):
			out.append(n["slot_id"])
	return out


func is_placeholder_audio() -> bool:
	if is_mission():
		return placeholder_stems > 0
	for slot in loadout:
		var r: Dictionary = renders.get(slot, {}).get(loadout[slot], {})
		if r.get("placeholder", false):
			return true
	return false


func notes_in_lane(lane: String) -> Array:
	var out: Array = []
	for n in notes:
		if n["lane"] == lane:
			out.append(n)
	return out


func notes_on_button(button: int) -> Array:
	var out: Array = []
	for n in notes:
		if int(n["button"]) == button:
			out.append(n)
	return out


func rule(key: String, default: Variant) -> Variant:
	return rules.get(key, default)
