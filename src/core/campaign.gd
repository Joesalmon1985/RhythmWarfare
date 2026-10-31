class_name Campaign
extends RefCounted
## Campaign data (data/campaign/campaign.json) and the player's saved progress (user://campaign.json): cleared missions
## with their bests, and the musical choices made per mission. Clearing a mission (a survival win on its campaign run)
## unlocks the next one and the library options that enter with it. Replays only improve bests; practice and
## rhythm-only runs write nothing. The save is written atomically (temp file, read back, rename); a corrupt file is
## kept as ".bad" and replaced; a version 1 save (the schema 2 build) is migrated in place and kept as ".v1".

const DATA_PATH := "res://data/campaign/campaign.json"
const DEFAULT_SAVE_PATH := "user://campaign.json"
const SAVE_VERSION := 2
const UNLOCK_ENV := "RW_UNLOCK_ALL"  # "1" / "0" overrides "unlock_all" in the data file (scripted runs)
## Version 1 loadout slots -> version 2 choices (instrument profiles kept their ids as sound ids).
const V1_SLOT_CHOICE := {"kick_1": "kick_sound", "snare_1": "snare_sound", "bass_1": "bass_voice"}

var levels: Array = []  # data/campaign/campaign.json "levels"
var save_path := DEFAULT_SAVE_PATH
var progress: Dictionary = {}
var recovered_from_corrupt := false
var migrated_from := 0
## Developer switch: every playable mission is open and every option of its pools is offered. Clears and bests still
## save; the stored progress never depends on it. data/campaign/campaign.json "unlock_all" or RW_UNLOCK_ALL.
var unlock_all := false


## `unlock_override`: -1 reads the data file and RW_UNLOCK_ALL, 0 forces the normal ladder, 1 forces unlock-all.
static func load_data(path: String = DEFAULT_SAVE_PATH, unlock_override: int = -1) -> Campaign:
	var c := Campaign.new()
	c.save_path = path
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if typeof(parsed) == TYPE_DICTIONARY:
		c.levels = parsed.get("levels", [])
		c.unlock_all = bool(parsed.get("unlock_all", false))
	if OS.has_environment(UNLOCK_ENV):
		c.unlock_all = OS.get_environment(UNLOCK_ENV).to_lower() in ["1", "true", "on", "yes"]
	if unlock_override >= 0:
		c.unlock_all = unlock_override == 1
	c.load_progress()
	return c


static func _fresh() -> Dictionary:
	return {"version": SAVE_VERSION, "cleared": {}, "selections": {}, "last_played": ""}


func load_progress() -> void:
	recovered_from_corrupt = false
	migrated_from = 0
	progress = _fresh()
	if not FileAccess.file_exists(save_path):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(save_path))
	if typeof(parsed) != TYPE_DICTIONARY or typeof(parsed.get("cleared")) != TYPE_DICTIONARY:
		_set_aside(".bad")
		return
	var version := int(parsed.get("version", -1))
	if version == SAVE_VERSION and typeof(parsed.get("selections")) == TYPE_DICTIONARY:
		progress = parsed
		progress["last_played"] = str(progress.get("last_played", ""))
		return
	if version == 1 and typeof(parsed.get("loadouts", {})) == TYPE_DICTIONARY:
		progress = migrate_v1(parsed)
		migrated_from = 1
		DirAccess.copy_absolute(save_path, save_path + ".v1")
		save()
		return
	_set_aside(".bad")


func _set_aside(suffix: String) -> void:
	recovered_from_corrupt = true
	DirAccess.rename_absolute(save_path, save_path + suffix)


## Version 1 (instrument loadouts, 30 Oct 2026) -> version 2. Clears and bests carry over under the same level ids;
## loadouts become choices where the profile is now a sound; unlocked_profiles are derived from clears now.
static func migrate_v1(old: Dictionary) -> Dictionary:
	var out := _fresh()
	for level_id in old.get("cleared", {}):
		var rec: Dictionary = old["cleared"][level_id]
		out["cleared"][level_id] = {"clears": int(rec.get("clears", 1)), "best_accuracy": float(rec.get("best_accuracy", 0.0)),
			"best_sequences": 0.0, "best_core_hp": float(rec.get("best_core_hp", 0.0)), "best_combo": int(rec.get("best_combo", 0))}
	for level_id in old.get("loadouts", {}):
		var sel := {}
		var lo: Dictionary = old["loadouts"][level_id]
		for slot in lo:
			if V1_SLOT_CHOICE.has(slot):
				sel[V1_SLOT_CHOICE[slot]] = [str(lo[slot])]
		if not sel.is_empty():
			out["selections"][level_id] = sel
	out["migrated_from"] = 1
	return out


## Write the progress file: temp file first, verified by reading it back, then moved into place.
func save() -> bool:
	var tmp := save_path + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(progress, "\t"))
	f.close()
	var check: Variant = JSON.parse_string(FileAccess.get_file_as_string(tmp))
	if typeof(check) != TYPE_DICTIONARY:
		DirAccess.remove_absolute(tmp)
		return false
	if FileAccess.file_exists(save_path):
		DirAccess.remove_absolute(save_path)
	return DirAccess.rename_absolute(tmp, save_path) == OK


# --- missions -----------------------------------------------------------------------------------------------------

func level_data(number: int) -> Dictionary:
	for l in levels:
		if int(l["number"]) == number:
			return l
	return {}


func level_by_id(level_id: String) -> Dictionary:
	for l in levels:
		if str(l["level_id"]) == level_id:
			return l
	return {}


func pack_dir(number: int) -> String:
	var p := str(level_data(number).get("pack", ""))
	return "" if p.is_empty() else "res://songs/" + p


func is_playable(number: int) -> bool:
	var dir := pack_dir(number)
	return not dir.is_empty() and FileAccess.file_exists(dir.path_join("level.json"))


func is_cleared(level_id: String) -> bool:
	return progress["cleared"].has(level_id)


## Mission 1 is open from the start; clearing mission n opens n + 1. With unlock_all every playable mission is open.
func is_unlocked(number: int) -> bool:
	if unlock_all and is_playable(number):
		return true
	return _ladder_unlocked(number)


func _ladder_unlocked(number: int) -> bool:
	if number <= 1:
		return true
	var prev := level_data(number - 1)
	return not prev.is_empty() and is_cleared(str(prev["level_id"]))


## The mission Continue should open: the first unlocked, playable, uncleared one, else the last one played.
func continue_number() -> int:
	for l in levels:
		var n := int(l["number"])
		if is_playable(n) and _ladder_unlocked(n) and not is_cleared(str(l["level_id"])):
			return n
	var last := level_by_id(str(progress.get("last_played", "")))
	return int(last.get("number", 1))


## Whether a library option may be picked in mission `number`: it entered with a mission that is open, or it is one of
## the mission's defaults; unlock_all offers everything. Returns "" when available, else what unlocks it.
func option_lock(number: int, option: String, defaults: Array) -> String:
	if unlock_all or defaults.has(option):
		return ""
	for l in levels:
		if (l.get("new_options", []) as Array).has(option):
			if _ladder_unlocked(int(l["number"])):
				return ""
			var prev := level_data(int(l["number"]) - 1)
			return "Clear %s to unlock" % str(prev.get("title", "the previous mission"))
	return ""


# --- results ------------------------------------------------------------------------------------------------------

## Feed a finished run. Only a victory on a campaign run (battle on, not practice) changes anything. Returns
## {saved, first_clear, unlocked_level, unlocked_title, new_options} (empty when nothing was recorded).
func record_result(result: Dictionary) -> Dictionary:
	if str(result.get("mode", "")) != "mission" or not bool(result.get("progression", false)) or str(result.get("play_mode", "")) != "campaign":
		return {}
	if not bool(result.get("battle", true)) or str(result.get("outcome", "")) != "victory":
		return {}
	var level_id := str(result.get("level_id", ""))
	var data := level_by_id(level_id)
	if data.is_empty():
		return {}
	var first := not is_cleared(level_id)
	var rec: Dictionary = progress["cleared"].get(level_id, {"clears": 0, "best_accuracy": 0.0, "best_sequences": 0.0, "best_core_hp": 0.0, "best_combo": 0})
	rec["clears"] = int(rec.get("clears", 0)) + 1
	rec["best_accuracy"] = maxf(float(rec.get("best_accuracy", 0.0)), float(result.get("accuracy", 0.0)))
	var seq_share := float(result.get("sequences_passed", 0)) / maxf(float(result.get("sequences", 1)), 1.0)
	rec["best_sequences"] = maxf(float(rec.get("best_sequences", 0.0)), seq_share)
	rec["best_combo"] = maxi(int(rec.get("best_combo", 0)), int(result.get("best_combo", 0)))
	var core: Dictionary = result.get("objective_hp", {}).get("command_core", {"hp": 0, "max": 1})
	rec["best_core_hp"] = maxf(float(rec.get("best_core_hp", 0.0)), float(core["hp"]) / maxf(float(core["max"]), 1.0))
	progress["cleared"][level_id] = rec
	var saved := save()
	var next := level_data(int(data["number"]) + 1)
	var new_options: Array = next.get("new_options", []) if first and not next.is_empty() else []
	return {"saved": saved, "first_clear": first, "unlocked_level": int(next.get("number", 0)) if first and not next.is_empty() else 0,
		"unlocked_title": str(next.get("title", "")), "new_options": new_options}


# --- selections ---------------------------------------------------------------------------------------------------

func selection_for(level_id: String) -> Dictionary:
	return (progress["selections"].get(level_id, {}) as Dictionary).duplicate(true)


func store_selection(level_id: String, selection: Dictionary) -> void:
	progress["selections"][level_id] = selection.duplicate(true)
	progress["last_played"] = level_id
	save()
