class_name Campaign
extends RefCounted
## Campaign data (data/campaign/campaign.json) and the player's saved progress (user://campaign.json): which levels
## are cleared with their best results, which instrument profiles are unlocked and the loadout chosen per level.
## Clearing a level (a survival win on a campaign chart) unlocks the next level and the profiles that enter with it.
## Replays never reset anything and only improve the stored bests; practice charts and rhythm-only runs write nothing.
## The save is written atomically (temp file, then rename) and a corrupt file is kept as ".bad" and replaced.

const DATA_PATH := "res://data/campaign/campaign.json"
const DEFAULT_SAVE_PATH := "user://campaign.json"
const SAVE_VERSION := 1

var levels: Array = []  # data/campaign/campaign.json "levels"
var caps: Dictionary = {}
var save_path := DEFAULT_SAVE_PATH
var catalogue: Catalogue
var progress: Dictionary = {}
var recovered_from_corrupt := false


static func load_data(path: String = DEFAULT_SAVE_PATH) -> Campaign:
	var c := Campaign.new()
	c.save_path = path
	c.catalogue = Catalogue.load_default()
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if typeof(parsed) == TYPE_DICTIONARY:
		c.levels = parsed.get("levels", [])
		c.caps = parsed.get("loadout_caps", {})
	c.load_progress()
	return c


static func _fresh() -> Dictionary:
	return {"version": SAVE_VERSION, "cleared": {}, "unlocked_profiles": [], "loadouts": {}}


func load_progress() -> void:
	recovered_from_corrupt = false
	progress = _fresh()
	if FileAccess.file_exists(save_path):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(save_path))
		if typeof(parsed) == TYPE_DICTIONARY and int(parsed.get("version", -1)) == SAVE_VERSION and typeof(parsed.get("cleared")) == TYPE_DICTIONARY \
				and typeof(parsed.get("loadouts")) == TYPE_DICTIONARY and typeof(parsed.get("unlocked_profiles")) == TYPE_ARRAY:
			progress = parsed
		else:
			recovered_from_corrupt = true
			DirAccess.rename_absolute(save_path, save_path + ".bad")
	_refresh_unlocks()


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


# --- levels -----------------------------------------------------------------------------------------------------

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


func is_playable(number: int) -> bool:
	return not str(level_data(number).get("pack", "")).is_empty()


func is_cleared(level_id: String) -> bool:
	return progress["cleared"].has(level_id)


## Level 1 is open from the start; clearing level n opens n + 1.
func is_unlocked(number: int) -> bool:
	if number <= 1:
		return true
	var prev := level_data(number - 1)
	return not prev.is_empty() and is_cleared(str(prev["level_id"]))


func highest_unlocked() -> int:
	var n := 1
	for l in levels:
		if is_unlocked(int(l["number"])):
			n = maxi(n, int(l["number"]))
	return n


## Profiles available now: those whose entry level is open (level n's profiles come with level n).
func unlocked_profiles() -> Array:
	var out: Array = []
	for id in catalogue.order:
		if progress["unlocked_profiles"].has(id) or catalogue.unlock_level(id) <= highest_unlocked():
			out.append(id)
	return out


func _refresh_unlocks() -> void:
	var list: Array = progress["unlocked_profiles"]
	for id in catalogue.order:
		if catalogue.unlock_level(id) <= highest_unlocked() and not list.has(id):
			list.append(id)


# --- results ------------------------------------------------------------------------------------------------------

## Feed a finished run. Only a victory on a progression chart changes anything. Returns
## {saved, first_clear, unlocked_level, new_profiles} (empty when nothing was recorded).
func record_result(result: Dictionary) -> Dictionary:
	if str(result.get("mode", "")) != "defense" or not bool(result.get("progression", false)) or str(result.get("play_mode", "")) != "campaign":
		return {}
	if not bool(result.get("battle", true)) or str(result.get("outcome", "")) != "victory":
		return {}
	var level_id := str(result.get("level_id", ""))
	var data := level_by_id(level_id)
	if data.is_empty():
		return {}
	var before_profiles := unlocked_profiles()
	var first := not is_cleared(level_id)
	var rec: Dictionary = progress["cleared"].get(level_id, {"clears": 0, "best_accuracy": 0.0, "best_combo": 0, "best_core_hp": 0.0})
	rec["clears"] = int(rec["clears"]) + 1
	rec["best_accuracy"] = maxf(float(rec["best_accuracy"]), float(result.get("accuracy", 0.0)))
	rec["best_combo"] = maxi(int(rec["best_combo"]), int(result.get("best_combo", 0)))
	var core: Dictionary = result.get("objective_hp", {}).get("command_core", {"hp": 0, "max": 1})
	rec["best_core_hp"] = maxf(float(rec["best_core_hp"]), float(core["hp"]) / maxf(float(core["max"]), 1.0))
	progress["cleared"][level_id] = rec
	_refresh_unlocks()
	var new_profiles: Array = []
	for id in unlocked_profiles():
		if not before_profiles.has(id):
			new_profiles.append(id)
	var saved := save()
	var next := level_data(int(data["number"]) + 1)
	return {"saved": saved, "first_clear": first, "unlocked_level": int(next.get("number", 0)) if first and not next.is_empty() else 0,
		"unlocked_title": str(next.get("title", "")), "new_profiles": new_profiles}


# --- loadouts -----------------------------------------------------------------------------------------------------

## The loadout stored for a level, completed with the level's defaults for any slot that has none.
func loadout_for(level_id: String, level_default: Dictionary, active_slots: Array) -> Dictionary:
	var saved: Dictionary = progress["loadouts"].get(level_id, {})
	var out := {}
	for slot in active_slots:
		var profile := str(saved.get(slot, ""))
		if profile.is_empty() or not unlocked_profiles().has(profile):
			profile = str(level_default.get(slot, ""))
		out[slot] = profile
	return out


func store_loadout(level_id: String, selection: Dictionary) -> void:
	progress["loadouts"][level_id] = selection.duplicate()
	save()


## Errors for a loadout on a loaded level: family, unlock, distinct profiles, required slots, caps and renders.
func validate_loadout(level: Level, selection: Dictionary) -> Array:
	var families := {}
	for p in level.parts:
		if p.get("slot_id") != null:
			families[str(p["slot_id"])] = str(p["family"])
	var errors := catalogue.validate_loadout(selection, families, level.loadout_active_slots, unlocked_profiles())
	for slot in selection:
		if level.renders.has(slot) and not level.renders[slot].has(str(selection[slot])):
			errors.append("slot %s: no render of %s for this song" % [slot, catalogue.display_name(str(selection[slot]))])
	return errors
