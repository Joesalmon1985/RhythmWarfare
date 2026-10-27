class_name LevelLoader
extends RefCounted
## Reads and validates a song pack (PRD section 9). Returns {"level": Level or null, "errors": [], "warnings": []}.
## A pack is a directory holding level.json and the stems it names (paths relative to the pack root).

const SCHEMA_VERSION := 1
const STEM_ALIGNMENT_TOLERANCE_S := 0.005
const SAME_LANE_MIN_GAP_TICKS := 0  # same-tick notes on one lane are a conflict; closer spacing is warned below
const SAME_LANE_WARN_GAP_MS := 200.0  # two notes on one lane closer than twice the Good window cannot both be judged cleanly


static func load_pack(pack_dir: String) -> Dictionary:
	var result := {"level": null, "errors": [], "warnings": []}
	var errors: Array = result["errors"]
	var warnings: Array = result["warnings"]
	var dir := pack_dir.rstrip("/")
	var json_path := dir.path_join("level.json")
	if not FileAccess.file_exists(json_path):
		errors.append("level.json not found in %s" % dir)
		return result
	var text := FileAccess.get_file_as_string(json_path)
	var parsed: Variant = JSON.parse_string(text)
	if typeof(parsed) != TYPE_DICTIONARY:
		errors.append("level.json is not a JSON object")
		return result
	var level := parse(parsed, dir, errors, warnings)
	if errors.is_empty():
		_check_stems(level, errors, warnings)
	if errors.is_empty():
		result["level"] = level
	return result


## Builds a Level from an already parsed dictionary. Stem paths are resolved against pack_dir but not opened.
static func parse(d: Dictionary, pack_dir: String, errors: Array, warnings: Array) -> Level:
	var level := Level.new()
	level.pack_dir = pack_dir
	if int(d.get("schema_version", -1)) != SCHEMA_VERSION:
		errors.append("schema_version must be %d" % SCHEMA_VERSION)
	level.level_id = str(d.get("level_id", ""))
	level.title = str(d.get("title", level.level_id))
	if level.level_id.is_empty():
		errors.append("level_id is required")
	level.bpm = float(d.get("bpm", 0))
	if level.bpm <= 0.0:
		errors.append("bpm must be positive")
	var ts: Variant = d.get("time_signature", [4, 4])
	if typeof(ts) == TYPE_ARRAY and ts.size() == 2 and int(ts[0]) > 0:
		level.beats_per_bar = int(ts[0])
	else:
		errors.append("time_signature must be [beats, unit]")
	level.ticks_per_beat = int(d.get("ticks_per_beat", 0))
	if level.ticks_per_beat <= 0:
		errors.append("ticks_per_beat must be positive")
	level.song_offset_ms = int(d.get("song_offset_ms", 0))
	level.duration_ticks = int(d.get("duration_ticks", 0))
	if level.duration_ticks <= 0:
		errors.append("duration_ticks must be positive")
	level.seed = int(d.get("seed", 0))
	level.battlefield = str(d.get("battlefield", ""))
	level.roster = str(d.get("roster", ""))
	var rules: Variant = d.get("rules", {})
	level.rules = rules if typeof(rules) == TYPE_DICTIONARY else {}

	# stems
	var stems: Variant = d.get("stems", {})
	if typeof(stems) != TYPE_DICTIONARY:
		errors.append("stems must be an object")
		stems = {}
	for key in Level.STEM_KEYS:
		if not stems.has(key):
			errors.append("stem '%s' is required" % key)
			continue
		var rel := str(stems[key])
		if not _safe_relative(rel):
			errors.append("stem '%s' path escapes the pack root: %s" % [key, rel])
			continue
		level.stems[key] = pack_dir.path_join(rel)

	# sections
	var sections: Variant = d.get("sections", [])
	if typeof(sections) != TYPE_ARRAY:
		errors.append("sections must be an array")
		sections = []
	var tpb := level.ticks_per_bar() if level.ticks_per_beat > 0 else 1
	var expected_start := 0
	var section_ids := {}
	for raw in sections:
		if typeof(raw) != TYPE_DICTIONARY:
			errors.append("section entries must be objects")
			continue
		var s := {"id": str(raw.get("id", "")), "start_tick": int(raw.get("start_tick", -1)), "length_bars": int(raw.get("length_bars", 0))}
		if s["id"].is_empty() or section_ids.has(s["id"]):
			errors.append("section id missing or duplicated: '%s'" % s["id"])
		section_ids[s["id"]] = true
		if s["start_tick"] != expected_start:
			errors.append("section '%s' starts at tick %d, expected %d (sections must be contiguous from 0)" % [s["id"], s["start_tick"], expected_start])
		if s["length_bars"] <= 0:
			errors.append("section '%s' length_bars must be positive" % s["id"])
		expected_start = s["start_tick"] + s["length_bars"] * tpb
		level.sections.append(s)
	if sections.is_empty():
		errors.append("at least one section is required")
	elif expected_start != level.duration_ticks:
		errors.append("sections cover ticks 0..%d but duration_ticks is %d" % [expected_start, level.duration_ticks])

	# notes
	var ids := {}
	var raw_notes: Variant = d.get("notes", [])
	if typeof(raw_notes) != TYPE_ARRAY:
		errors.append("notes must be an array")
		raw_notes = []
	for raw in raw_notes:
		if typeof(raw) != TYPE_DICTIONARY:
			errors.append("note entries must be objects")
			continue
		var n := {
			"id": str(raw.get("id", "")),
			"tick": int(raw.get("tick", -1)),
			"lane": str(raw.get("lane", "")),
			"type": str(raw.get("type", "tap")),
			"duration_ticks": int(raw.get("duration_ticks", 0)),
		}
		if n["id"].is_empty() or ids.has(n["id"]):
			errors.append("note id missing or duplicated: '%s'" % n["id"])
		ids[n["id"]] = true
		if not Level.LANES.has(n["lane"]):
			errors.append("note %s has unsupported lane '%s'" % [n["id"], n["lane"]])
		if not Level.NOTE_TYPES.has(n["type"]):
			errors.append("note %s has unsupported type '%s'" % [n["id"], n["type"]])
		if n["tick"] < 0:
			errors.append("note %s has a negative tick" % n["id"])
		if n["tick"] >= level.duration_ticks and level.duration_ticks > 0:
			errors.append("note %s lies at or beyond the song end" % n["id"])
		if n["type"] == "hold":
			if n["lane"] != "bass":
				errors.append("note %s: holds are only allowed on the bass lane" % n["id"])
			if n["duration_ticks"] <= 0:
				errors.append("note %s: hold duration_ticks must be positive" % n["id"])
			elif n["tick"] + n["duration_ticks"] > level.duration_ticks and level.duration_ticks > 0:
				errors.append("note %s: hold ends beyond the song end" % n["id"])
		else:
			n["duration_ticks"] = 0
		n["time"] = level.tick_to_seconds(n["tick"]) if level.bpm > 0 and level.ticks_per_beat > 0 else 0.0
		n["end_tick"] = n["tick"] + n["duration_ticks"]
		n["end_time"] = level.tick_to_seconds(n["end_tick"]) if level.bpm > 0 and level.ticks_per_beat > 0 else 0.0
		level.notes.append(n)
	level.notes.sort_custom(_note_order)
	_check_lane_conflicts(level, errors, warnings)
	_check_chords(level, warnings)

	# enemy events
	var raw_events: Variant = d.get("enemy_events", [])
	if typeof(raw_events) != TYPE_ARRAY:
		errors.append("enemy_events must be an array")
		raw_events = []
	var last_tick := -1
	for raw in raw_events:
		if typeof(raw) != TYPE_DICTIONARY:
			errors.append("enemy event entries must be objects")
			continue
		var e := {"id": str(raw.get("id", "")), "tick": int(raw.get("tick", -1)), "action": str(raw.get("action", ""))}
		if e["id"].is_empty() or ids.has(e["id"]):
			errors.append("enemy event id missing or duplicated: '%s'" % e["id"])
		ids[e["id"]] = true
		if not Level.ACTIONS.has(e["action"]):
			errors.append("enemy event %s has unsupported action '%s'" % [e["id"], e["action"]])
		if e["tick"] < 0:
			errors.append("enemy event %s has a negative tick" % e["id"])
		if e["tick"] < last_tick:
			errors.append("enemy event %s is out of order (tick %d after %d)" % [e["id"], e["tick"], last_tick])
		last_tick = maxi(last_tick, e["tick"])
		if e["tick"] >= level.duration_ticks and level.duration_ticks > 0:
			errors.append("enemy event %s lies at or beyond the song end" % e["id"])
		e["time"] = level.tick_to_seconds(e["tick"]) if level.bpm > 0 and level.ticks_per_beat > 0 else 0.0
		level.enemy_events.append(e)
	return level


static func _note_order(a: Dictionary, b: Dictionary) -> bool:
	if a["tick"] != b["tick"]:
		return a["tick"] < b["tick"]
	return Level.LANES.find(a["lane"]) < Level.LANES.find(b["lane"])


static func _safe_relative(rel: String) -> bool:
	if rel.is_empty() or rel.is_absolute_path() or rel.begins_with("/") or rel.begins_with("\\"):
		return false
	for part in rel.replace("\\", "/").split("/"):
		if part == "..":
			return false
	return true


static func _check_lane_conflicts(level: Level, errors: Array, warnings: Array) -> void:
	for lane in Level.LANES:
		var prev: Dictionary = {}
		for n in level.notes:
			if n["lane"] != lane:
				continue
			if not prev.is_empty():
				if n["tick"] == prev["tick"]:
					errors.append("notes %s and %s share lane %s at tick %d" % [prev["id"], n["id"], lane, n["tick"]])
				elif n["tick"] < prev["end_tick"]:
					errors.append("note %s starts inside hold %s on lane %s" % [n["id"], prev["id"], lane])
				elif (n["time"] - prev["end_time"]) * 1000.0 < SAME_LANE_WARN_GAP_MS:
					warnings.append("notes %s and %s on lane %s are only %.0f ms apart" % [prev["id"], n["id"], lane, (n["time"] - prev["end_time"]) * 1000.0])
			prev = n


## Flags unavoidable three-touch chords: a kick and a snare on the same tick while a bass hold is active.
static func _check_chords(level: Level, warnings: Array) -> void:
	var holds: Array = []
	for n in level.notes:
		if n["type"] == "hold":
			holds.append(n)
	var by_tick := {}
	for n in level.notes:
		if n["lane"] == "bass":
			continue
		by_tick[n["tick"]] = by_tick.get(n["tick"], 0) + 1
	for tick in by_tick:
		if by_tick[tick] < 2:
			continue
		for h in holds:
			if tick > h["tick"] and tick < h["end_tick"]:
				warnings.append("three-touch chord at tick %d inside bass hold %s (author review)" % [tick, h["id"]])
				break


## Decodes each stem to check it exists and that all four have the same length.
static func _check_stems(level: Level, errors: Array, warnings: Array) -> void:
	var lengths: Dictionary = {}
	for key in level.stems:
		var path: String = level.stems[key]
		if not stream_exists(path):
			errors.append("stem '%s' file not found: %s" % [key, path])
			continue
		var stream := load_stream(path)
		if stream == null:
			errors.append("stem '%s' could not be decoded: %s" % [key, path])
			continue
		lengths[key] = stream.get_length()
	level.stem_lengths = lengths
	if lengths.size() < Level.STEM_KEYS.size():
		return
	var lo: float = INF
	var hi: float = -INF
	for key in lengths:
		lo = minf(lo, lengths[key])
		hi = maxf(hi, lengths[key])
	if hi - lo > STEM_ALIGNMENT_TOLERANCE_S:
		errors.append("stem lengths differ by %.1f ms (tolerance %.0f ms); export every stem from the same timeline start" % [(hi - lo) * 1000.0, STEM_ALIGNMENT_TOLERANCE_S * 1000.0])
	if lo + 0.001 < level.duration_seconds():
		errors.append("stems are %.2f s long but the chart runs to %.2f s" % [lo, level.duration_seconds()])


## In an exported build only the imported form of a res:// audio file is packed, so the original path fails a
## plain file check; ResourceLoader knows about it. Absolute (user://) packs are checked on disk.
static func stream_exists(path: String) -> bool:
	if path.begins_with("res://"):
		return ResourceLoader.exists(path) or FileAccess.file_exists(path)
	return FileAccess.file_exists(path)


## Loads an audio file from an absolute path or a res:// path, by extension.
static func load_stream(path: String) -> AudioStream:
	if path.begins_with("res://"):
		var res: Variant = load(path)
		return res as AudioStream
	var ext := path.get_extension().to_lower()
	match ext:
		"ogg":
			return AudioStreamOggVorbis.load_from_file(path)
		"mp3":
			return AudioStreamMP3.load_from_file(path)
		"wav":
			return AudioStreamWAV.load_from_file(path)
	return null
