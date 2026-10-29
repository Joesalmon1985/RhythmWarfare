class_name DefenseLoader
extends RefCounted
## Schema 2 (defense campaign) packs, PRD section 14. Builds a Level from level.json: the selected chart's notes
## (explicit button, slot_id, part_id, source_note_id, family; never a lane), sections with mode, the equipped
## renders as stems keyed by slot id plus "other", waves, and the loadout. Chart problems are errors for the
## author; nothing is moved, shortened or dropped silently.

const SCHEMA_VERSION := 2
const MODES := ["drums", "bass"]
const PLAY_MODES := ["campaign", "practice"]
const SAME_THUMB_TAP_GAP_TICKS := 960
const SAME_THUMB_HOLD_GAP_TICKS := 480
const MAX_TOUCHES := 2


static func parse(d: Dictionary, pack_dir: String, options: Dictionary, errors: Array, warnings: Array) -> Level:
	var level := Level.new()
	level.pack_dir = pack_dir
	level.schema_version = SCHEMA_VERSION
	level.mode = "defense"
	if str(d.get("mode", "")) != "defense":
		errors.append("schema 2 packs need mode \"defense\"")
	level.level_id = str(d.get("level_id", ""))
	level.title = str(d.get("title", level.level_id))
	level.campaign_level = int(d.get("campaign_level", 0))
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
	var src: Variant = d.get("source", {})
	level.source = src if typeof(src) == TYPE_DICTIONARY else {}
	var parts: Variant = d.get("parts", [])
	level.parts = parts if typeof(parts) == TYPE_ARRAY else []
	var part_slot := {}
	for p in level.parts:
		if typeof(p) == TYPE_DICTIONARY:
			part_slot[str(p.get("id", ""))] = p.get("slot_id")
			if not Level.FAMILIES.has(str(p.get("family", ""))) and str(p.get("family", "")) != "other":
				errors.append("part '%s' has unsupported family '%s'" % [p.get("id", ""), p.get("family", "")])

	_parse_loadout(d, level, errors)
	_parse_renders(d, level, part_slot, errors, warnings)
	_resolve_stems(d, level, pack_dir, errors)
	var wanted: Variant = options.get("loadout", {})
	if typeof(wanted) == TYPE_DICTIONARY:
		for slot in wanted:
			if not level.loadout_active_slots.has(slot):
				errors.append("loadout names slot '%s', which this level does not use" % slot)
			elif str(wanted[slot]) != str(level.loadout.get(slot, "")):
				var why := equip(level, str(slot), str(wanted[slot]))
				if not why.is_empty():
					errors.append(why)
	_parse_chart(d, level, str(options.get("chart_id", "")), errors, warnings)
	_parse_waves(d, level, errors)
	return level


static func _parse_loadout(d: Dictionary, level: Level, errors: Array) -> void:
	var lo: Variant = d.get("loadout", {})
	if typeof(lo) != TYPE_DICTIONARY:
		errors.append("loadout must be an object")
		return
	level.loadout_active_slots = lo.get("active_slots", []) if typeof(lo.get("active_slots", [])) == TYPE_ARRAY else []
	var def: Variant = lo.get("default", {})
	level.loadout_default = def if typeof(def) == TYPE_DICTIONARY else {}
	if level.loadout_active_slots.is_empty():
		errors.append("loadout.active_slots is required")
	for slot in level.loadout_active_slots:
		if not level.loadout_default.has(slot):
			errors.append("loadout.default has no profile for slot '%s'" % slot)


static func _parse_renders(d: Dictionary, level: Level, part_slot: Dictionary, errors: Array, warnings: Array) -> void:
	var renders: Variant = d.get("renders", {})
	if typeof(renders) != TYPE_DICTIONARY or renders.is_empty():
		errors.append("renders is required")
		return
	level.renders = renders
	var hashes: Dictionary = level.source.get("midi_sha256", {})
	var placeholder := false
	var other_hash := ""
	for p in level.parts:
		if p.get("slot_id") == null and hashes.has(str(p["id"])):
			other_hash += str(hashes[str(p["id"])])
	other_hash = other_hash.sha256_text()
	for slot in renders:
		for profile in renders[slot]:
			var r: Dictionary = renders[slot][profile]
			if not LevelLoader._safe_relative(str(r.get("file", ""))):
				errors.append("render %s/%s path escapes the pack root" % [slot, profile])
			var expect := other_hash if slot == "other" else str(hashes.get(slot, ""))
			if expect.is_empty() or str(r.get("source_sha256", "")) != expect:
				errors.append("render %s/%s: source_sha256 does not match the part MIDI hash (edited MIDI with a stale render?)" % [slot, profile])
			if r.get("placeholder", false):
				placeholder = true
	if placeholder:
		warnings.append("placeholder (synthesised) audio in use; owner renders replace it file for file")
	for slot in level.loadout_active_slots:
		if not part_slot.has(slot) and not part_slot.values().has(slot):
			errors.append("active slot '%s' has no part" % slot)


## The stems this load plays: one per active slot (the equipped profile's render) plus "other".
static func _resolve_stems(d: Dictionary, level: Level, pack_dir: String, errors: Array) -> void:
	for slot in level.loadout_active_slots:
		var profile := str(level.loadout_default.get(slot, ""))
		var per_slot: Dictionary = level.renders.get(slot, {})
		if not per_slot.has(profile):
			errors.append("slot '%s' has no render for profile '%s'" % [slot, profile])
			continue
		level.loadout[slot] = profile
		level.stems[slot] = pack_dir.path_join(str(per_slot[profile]["file"]))
	var other: Dictionary = level.renders.get("other", {}).get("accompaniment", {})
	if other.is_empty():
		errors.append("renders.other.accompaniment is required")
	else:
		level.stems["other"] = pack_dir.path_join(str(other["file"]))


## Swap the equipped profile of a slot after loading (loadout screen). Returns an error string, empty on success.
static func equip(level: Level, slot: String, profile: String) -> String:
	var per_slot: Dictionary = level.renders.get(slot, {})
	if not per_slot.has(profile):
		return "no render of profile '%s' for slot '%s'" % [profile, slot]
	level.loadout[slot] = profile
	level.stems[slot] = level.pack_dir.path_join(str(per_slot[profile]["file"]))
	return ""


static func _parse_chart(d: Dictionary, level: Level, want: String, errors: Array, warnings: Array) -> void:
	var charts: Variant = d.get("charts", [])
	if typeof(charts) != TYPE_ARRAY or charts.is_empty():
		errors.append("charts must hold at least one chart")
		return
	level.charts = charts
	var chosen: Dictionary = {}
	var seen := {}
	for c in charts:
		if typeof(c) != TYPE_DICTIONARY:
			errors.append("chart entries must be objects")
			return
		var cid := str(c.get("chart_id", ""))
		if cid.is_empty() or seen.has(cid):
			errors.append("chart_id missing or duplicated: '%s'" % cid)
		seen[cid] = true
		if not PLAY_MODES.has(str(c.get("play_mode", ""))):
			errors.append("chart %s: play_mode must be campaign or practice" % cid)
		if (want.is_empty() and chosen.is_empty()) or want == cid:
			chosen = c
	if chosen.is_empty():
		errors.append("chart '%s' not found in this pack (has: %s)" % [want, ", ".join(PackedStringArray(level.chart_ids()))])
		return
	level.chart_id = str(chosen["chart_id"])
	level.play_mode = str(chosen["play_mode"])
	level.progression = bool(chosen.get("progression", false))
	# sections
	var tpb := level.ticks_per_bar() if level.ticks_per_beat > 0 else 1
	var expected := 0
	var sid := {}
	for raw in chosen.get("sections", []):
		var s := {"id": str(raw.get("id", "")), "start_tick": int(raw.get("start_tick", -1)),
			"length_bars": int(raw.get("length_bars", 0)), "mode": str(raw.get("mode", ""))}
		if s["id"].is_empty() or sid.has(s["id"]):
			errors.append("section id missing or duplicated: '%s'" % s["id"])
		sid[s["id"]] = true
		if not MODES.has(s["mode"]):
			errors.append("section '%s' mode must be drums or bass" % s["id"])
		if s["start_tick"] != expected:
			errors.append("section '%s' starts at tick %d, expected %d" % [s["id"], s["start_tick"], expected])
		if s["length_bars"] <= 0:
			errors.append("section '%s' length_bars must be positive" % s["id"])
		expected = s["start_tick"] + s["length_bars"] * tpb
		s["end_tick"] = expected
		level.sections.append(s)
	if level.sections.is_empty():
		errors.append("at least one section is required")
	elif expected != level.duration_ticks:
		errors.append("sections cover ticks 0..%d but duration_ticks is %d" % [expected, level.duration_ticks])
	# notes
	var ids := {}
	for raw in chosen.get("notes", []):
		if typeof(raw) != TYPE_DICTIONARY:
			errors.append("note entries must be objects")
			continue
		var n := {
			"id": str(raw.get("id", "")), "tick": int(raw.get("tick", -1)), "type": str(raw.get("type", "tap")),
			"duration_ticks": int(raw.get("duration_ticks", 0)), "button": int(raw.get("button", 0)),
			"slot_id": str(raw.get("slot_id", "")), "part_id": str(raw.get("part_id", "")),
			"source_note_id": str(raw.get("source_note_id", "")), "family": str(raw.get("family", "")),
		}
		if raw.has("lane"):
			errors.append("note %s: schema 2 notes carry slot_id, not lane" % n["id"])
		if n["id"].is_empty() or ids.has(n["id"]):
			errors.append("note id missing or duplicated: '%s'" % n["id"])
		ids[n["id"]] = true
		if not raw.has("button") or n["button"] < 1 or n["button"] > Level.BUTTONS:
			errors.append("note %s: an explicit button 1..%d is required" % [n["id"], Level.BUTTONS])
		if not Level.FAMILIES.has(n["family"]):
			errors.append("note %s has unsupported family '%s'" % [n["id"], n["family"]])
		if not level.loadout_active_slots.has(n["slot_id"]):
			errors.append("note %s: slot '%s' is not an active slot of this level" % [n["id"], n["slot_id"]])
		if n["source_note_id"].is_empty() or n["part_id"].is_empty():
			errors.append("note %s: source_note_id and part_id are required" % n["id"])
		if not ["tap", "hold"].has(n["type"]):
			errors.append("note %s has unsupported type '%s'" % [n["id"], n["type"]])
		if n["tick"] < 0 or (level.duration_ticks > 0 and n["tick"] >= level.duration_ticks):
			errors.append("note %s lies outside the song (tick %d)" % [n["id"], n["tick"]])
		if n["type"] == "hold":
			if n["family"] != "bass":
				errors.append("note %s: holds are only allowed on the bass family" % n["id"])
			if n["duration_ticks"] <= 0:
				errors.append("note %s: hold duration_ticks must be positive" % n["id"])
			elif level.duration_ticks > 0 and n["tick"] + n["duration_ticks"] > level.duration_ticks:
				errors.append("note %s: hold ends beyond the song end" % n["id"])
		else:
			n["duration_ticks"] = 0
		n["lane"] = n["family"]  # drawing only (shape and colour); never used for production
		n["end_tick"] = n["tick"] + n["duration_ticks"]
		if level.bpm > 0.0 and level.ticks_per_beat > 0:
			n["time"] = level.tick_to_seconds(n["tick"])
			n["end_time"] = level.tick_to_seconds(n["end_tick"])
		else:
			n["time"] = 0.0
			n["end_time"] = 0.0
		level.notes.append(n)
	level.notes.sort_custom(LevelLoader._note_order)
	if not errors.is_empty():
		return
	LevelLoader._check_button_conflicts(level, errors, warnings)
	_check_modes(level, errors)
	_check_thumbs(level, errors, warnings)
	_check_touches(level, errors)


## Whole-bar exclusivity: kick and snare only in drum sections, bass only in bass sections, and a hold may not
## reach past the end of its section (a focus change).
static func _check_modes(level: Level, errors: Array) -> void:
	for n in level.notes:
		var section := _section_at(level, int(n["tick"]))
		if section.is_empty():
			continue
		var want := "bass" if n["family"] == "bass" else "drums"
		if section["mode"] != want:
			errors.append("note %s (%s) lies in %s section '%s'" % [n["id"], n["family"], section["mode"], section["id"]])
		elif n["type"] == "hold" and n["end_tick"] > section["end_tick"]:
			errors.append("hold %s crosses a focus change at the end of section '%s'" % [n["id"], section["id"]])


static func _section_at(level: Level, tick: int) -> Dictionary:
	for s in level.sections:
		if tick >= s["start_tick"] and tick < s["end_tick"]:
			return s
	return {}


## Left thumb 1/2, right thumb 3/4. A press while the same thumb holds another button is an error; short
## same-thumb gaps are design-target warnings (to be tested on a phone).
static func _check_thumbs(level: Level, errors: Array, warnings: Array) -> void:
	for thumb in range(2):
		var row: Array = []
		for n in level.notes:
			if int(Level.THUMB_OF_BUTTON[int(n["button"])]) == thumb:
				row.append(n)
		for i in range(row.size() - 1):
			var a: Dictionary = row[i]
			var b: Dictionary = row[i + 1]
			if a["type"] == "hold":
				if b["tick"] < a["end_tick"]:
					if b["button"] != a["button"]:
						errors.append("same-thumb hold-plus-tap: %s on button %d while %s holds button %d" % [b["id"], b["button"], a["id"], a["button"]])
				elif b["tick"] - a["end_tick"] < SAME_THUMB_HOLD_GAP_TICKS:
					warnings.append("thumb %d: %s starts %d ticks after hold %s ends (target %d)" % [thumb, b["id"], b["tick"] - a["end_tick"], a["id"], SAME_THUMB_HOLD_GAP_TICKS])
			elif b["tick"] - a["tick"] < SAME_THUMB_TAP_GAP_TICKS:
				warnings.append("thumb %d: %s follows tap %s after %d ticks (target %d)" % [thumb, b["id"], a["id"], b["tick"] - a["tick"], SAME_THUMB_TAP_GAP_TICKS])


static func _check_touches(level: Level, errors: Array) -> void:
	var ticks := {}
	for n in level.notes:
		ticks[n["tick"]] = true
	for tick in ticks:
		var held := {}
		for n in level.notes:
			if n["tick"] == tick or (n["type"] == "hold" and n["tick"] < tick and tick < n["end_tick"]):
				held[n["button"]] = true
		if held.size() > MAX_TOUCHES:
			errors.append("more than %d simultaneous touches at tick %d" % [MAX_TOUCHES, tick])
			return


## Checks that need the battlefield: every wave names a known entry, defense point and objective, and every actor
## exists. Returns error strings.
static func validate_battlefield(level: Level, bf: Dictionary, actors: Dictionary) -> Array:
	var errors: Array = []
	var entry_ids := {}
	for e in bf.get("entries", []):
		entry_ids[str(e["id"])] = true
	var point_ids := {}
	for p in bf.get("defense_points", []):
		point_ids[str(p["id"])] = true
	var objective_ids := {}
	for o in bf.get("objectives", []):
		objective_ids[str(o["id"])] = true
	if point_ids.size() != 3:
		errors.append("a defense battlefield needs exactly three defense points")
	for w in level.waves:
		if not entry_ids.has(str(w.get("entry", ""))):
			errors.append("wave %s: unknown entry '%s'" % [w["id"], w.get("entry", "")])
		if not point_ids.has(str(w.get("via_defense_point", ""))):
			errors.append("wave %s: unknown defense point '%s'" % [w["id"], w.get("via_defense_point", "")])
		if not objective_ids.has(str(w.get("target_objective", ""))):
			errors.append("wave %s: unknown objective '%s'" % [w["id"], w.get("target_objective", "")])
		for g in w["groups"]:
			if not actors.has(str(g["actor"])):
				errors.append("wave %s: unknown actor '%s'" % [w["id"], g["actor"]])
	return errors


static func _parse_waves(d: Dictionary, level: Level, errors: Array) -> void:
	var waves: Variant = d.get("waves", [])
	if typeof(waves) != TYPE_ARRAY:
		errors.append("waves must be an array")
		return
	var ids := {}
	for w in waves:
		if typeof(w) != TYPE_DICTIONARY:
			errors.append("wave entries must be objects")
			continue
		var wid := str(w.get("id", ""))
		if wid.is_empty() or ids.has(wid):
			errors.append("wave id missing or duplicated: '%s'" % wid)
		ids[wid] = true
		var tick := int(w.get("start_tick", -1))
		if tick < 0 or tick >= level.duration_ticks:
			errors.append("wave %s starts at tick %d, outside the song (a wave after the deadline can never matter)" % [wid, tick])
		if typeof(w.get("groups", [])) != TYPE_ARRAY or w.get("groups", []).is_empty():
			errors.append("wave %s has no groups" % wid)
		for g in w.get("groups", []):
			if int(g.get("count", 0)) <= 0 or str(g.get("actor", "")).is_empty():
				errors.append("wave %s has a group without actor or count" % wid)
		level.waves.append(w)
	level.waves.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return int(a["start_tick"]) < int(b["start_tick"]))
