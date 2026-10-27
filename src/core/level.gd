class_name Level
extends RefCounted
## One loaded song pack: the level definition plus resolved stem paths.
## Timing authority: integer ticks (ticks_per_beat per quarter note), bar 1 at tick 0.
## event_seconds = song_offset_ms / 1000 + tick * 60 / (bpm * ticks_per_beat)

const LANES := ["kick", "snare", "bass"]
const ACTIONS := ["kick", "snare", "bass"]
const NOTE_TYPES := ["tap", "hold"]
const STEM_KEYS := ["kick", "snare", "bass", "other"]

var pack_dir: String = ""
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
var notes: Array = []  # [{id, tick, lane, type, duration_ticks, time, end_time}] sorted by tick then lane
var enemy_events: Array = []  # [{id, tick, action, time}] sorted by tick
var stem_lengths: Dictionary = {}  # stem key -> seconds, when the loader could decode them


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


func notes_in_lane(lane: String) -> Array:
	var out: Array = []
	for n in notes:
		if n["lane"] == lane:
			out.append(n)
	return out


func rule(key: String, default: Variant) -> Variant:
	return rules.get(key, default)
