class_name MissionLoader
extends RefCounted
## Schema 3 mission packs (songs/<pack>/level.json, written by tools/content/build.py; PRD section 15). Builds a Level
## for one selection of the mission's choices: the cues of the chosen clips (pad, tap or hold, sequence), the stems of
## the chosen clip and sound combinations, the sequences with their rewards, the phases and the waves.
##
## A selection is {choice id: [option ids, in slot order]}; anything missing or invalid falls back to the defaults
## with a warning, so a stale save can never break a mission.

const SCHEMA_VERSION := 3


static func parse(d: Dictionary, pack_dir: String, options: Dictionary, errors: Array, warnings: Array) -> Level:
	var level := Level.new()
	level.pack_dir = pack_dir
	level.schema_version = SCHEMA_VERSION
	level.mode = "defense"
	level.level_id = str(d.get("level_id", ""))
	level.title = str(d.get("title", level.level_id))
	level.campaign_level = int(d.get("campaign_level", 0))
	level.bpm = float(d.get("bpm", 174))
	level.ticks_per_beat = int(d.get("ticks_per_beat", 960))
	var ts: Array = d.get("time_signature", [4, 4])
	level.beats_per_bar = int(ts[0])
	level.song_offset_ms = int(d.get("song_offset_ms", 0))
	level.duration_ticks = int(d.get("duration_ticks", 0))
	level.seed = int(d.get("seed", 0))
	level.battlefield = str(d.get("battlefield", "defense_02"))
	level.roster = str(d.get("roster", "openra_mvp_01"))
	level.rules = d.get("rules", {})
	level.sequence_threshold = float(d.get("sequence_threshold", 0.6))
	level.intro = str(d.get("intro", ""))
	level.choices = d.get("choices", [])
	level.names = d.get("names", {})
	level.previews = d.get("previews", {})
	level.content = d.get("content", {})
	level.placeholder = bool(d.get("placeholder", false))
	level.play_mode = "practice" if bool(options.get("practice", false)) else "campaign"
	level.progression = level.play_mode == "campaign"
	if level.level_id.is_empty() or level.duration_ticks <= 0 or level.bpm <= 0.0:
		errors.append("level_id, bpm and duration_ticks are required")
		return level
	level.selection = resolve_selection(level.choices, options.get("selection", {}), warnings)
	for p in d.get("phases", []):
		level.sections.append({"id": str(p["id"]), "start_tick": int(p["start_tick"]), "end_tick": int(p["end_tick"]),
			"length_bars": (int(p["end_tick"]) - int(p["start_tick"])) / level.ticks_per_bar(), "mode": str(p["mode"]), "pads": p.get("pads", {})})
	_stems(d, level, errors)
	_cues(d, level, errors)
	_sequences(d, level, errors)
	var waves: Variant = d.get("waves", [])
	level.waves = waves if typeof(waves) == TYPE_ARRAY else []
	level.waves.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a["start_tick"]) < int(b["start_tick"]))
	if level.placeholder:
		warnings.append("placeholder (generated) audio in use; owner renders replace it through tools/content/build.py")
	return level


## Defaults for anything not chosen; a chosen option must be in the pool, distinct, and the right count.
static func resolve_selection(choices: Array, wanted: Dictionary, warnings: Array) -> Dictionary:
	var out := {}
	for c in choices:
		var cid := str(c["id"])
		var pool: Array = []
		for o in c["pool"]:
			pool.append(str(o["id"]))
		var pick: Array = []
		var w: Variant = wanted.get(cid, [])
		if typeof(w) == TYPE_ARRAY:
			for o in w:
				if pool.has(str(o)) and not pick.has(str(o)):
					pick.append(str(o))
		if pick.size() != int(c["count"]):
			if not wanted.is_empty() and wanted.has(cid):
				warnings.append("choice %s: %s is not a valid pick, using the default" % [cid, str(w)])
			pick = []
			for o in c["default"]:
				pick.append(str(o))
		out[cid] = pick
	return out


static func _key(deps: Array, selection: Dictionary) -> String:
	var parts: PackedStringArray = []
	for dep in deps:
		var bits := str(dep).split("#")
		var picked: Array = selection.get(bits[0], [])
		var slot := int(bits[1]) - 1
		parts.append(str(picked[slot]) if slot >= 0 and slot < picked.size() else "")
	return "|".join(parts)


static func _stems(d: Dictionary, level: Level, errors: Array) -> void:
	for s in d.get("stems", []):
		var key := _key(s["deps"], level.selection)
		var files: Dictionary = s["files"]
		if not files.has(key):
			errors.append("stem %s has no render for %s (rebuild with tools/content/build.py)" % [s["key"], key])
			continue
		var f: Dictionary = files[key]
		if not LevelLoader._safe_relative(str(f["file"])):
			errors.append("stem %s path escapes the pack" % s["key"])
			continue
		level.stems[str(s["key"])] = level.pack_dir.path_join(str(f["file"]))
		level.stem_family[str(s["key"])] = str(s["family"])
		if f.get("placeholder", false):
			level.placeholder_stems += 1


static func _cues(d: Dictionary, level: Level, errors: Array) -> void:
	var raw: Array = []
	for b in d.get("cue_blocks", []):
		var key := _key(b["deps"], level.selection) if not b["deps"].is_empty() else ""
		var opts: Dictionary = b["options"]
		var list: Array = []
		if key.is_empty():
			list = opts.values()[0] if opts.size() == 1 else []
		elif opts.has(key):
			list = opts[key]
		else:
			errors.append("cue block of phase %d has no cues for %s" % [int(b["phase"]), key])
			continue
		for c in list:
			raw.append({"tick": int(c[0]), "duration_ticks": int(c[1]), "pad": int(b["pad"]), "family": str(b["family"]),
				"voice": str(b["voice"]), "phase": int(b["phase"])})
	raw.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return a["tick"] < b["tick"] if a["tick"] != b["tick"] else a["pad"] < b["pad"])
	var i := 0
	for n in raw:
		n["id"] = "c%04d" % i
		n["type"] = "hold" if int(n["duration_ticks"]) > 0 else "tap"
		n["end_tick"] = int(n["tick"]) + int(n["duration_ticks"])
		n["time"] = level.tick_to_seconds(n["tick"])
		n["end_time"] = level.tick_to_seconds(n["end_tick"])
		n["button"] = n["pad"]
		n["lane"] = n["family"]
		n["slot_id"] = n["voice"]
		n["seq"] = -1
		level.notes.append(n)
		i += 1


static func _sequences(d: Dictionary, level: Level, errors: Array) -> void:
	for s in d.get("sequences", []):
		var seq := {"index": int(s["index"]), "phase": int(s["phase"]), "mode": str(s["mode"]), "start_tick": int(s["start_tick"]),
			"end_tick": int(s["end_tick"]), "reward": str(s["reward"])}
		seq["start_time"] = level.tick_to_seconds(seq["start_tick"])
		seq["end_time"] = level.tick_to_seconds(seq["end_tick"])
		if MissionRules.reward(seq["reward"]).is_empty():
			errors.append("sequence %d: unknown reward %s" % [seq["index"], seq["reward"]])
		level.sequences.append(seq)
	for n in level.notes:
		for s in level.sequences:
			if n["tick"] >= s["start_tick"] and n["tick"] < s["end_tick"]:
				n["seq"] = s["index"]
				if n["end_tick"] > s["end_tick"]:
					errors.append("cue %s holds past the end of its sequence" % n["id"])
				break
		if int(n["seq"]) < 0:
			errors.append("cue %s lies in no sequence" % n["id"])
	for s in level.sequences:
		var count := 0
		for n in level.notes:
			if int(n["seq"]) == int(s["index"]):
				count += 1
		s["cues"] = count
		if count == 0:
			errors.append("sequence %d has no cues" % int(s["index"]))
