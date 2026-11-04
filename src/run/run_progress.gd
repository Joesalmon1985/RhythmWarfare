class_name RunProgress
extends RefCounted
## The continuous run's save: user://story_run.json (versioned, atomic, an unreadable file is set aside as .corrupt). A level (a route-map node)
## is saved as reached when the player enters it. The old chapter-by-chapter save (user://story_campaign.json) is never modified or deleted; on the
## first load of the new save it is read once and its chapters become reached levels, so nobody loses a place they had opened.

const SAVE_PATH := "user://story_run.json"
const OLD_PATH := "user://story_campaign.json"
const VERSION := 2
const CHAPTER_TO_NODE := {"night_one": "warehouse", "mothership": "mothership", "underworld": "underworld", "hospital": "hospital", "mental_hospital": "ward"}

var path := SAVE_PATH
var old_path := OLD_PATH
var data: Dictionary = {}
var recovered_from_corrupt := false
var migrated: Array = []  # level ids carried over from the old chapter save on this load


static func load_data(p_path: String = SAVE_PATH, p_old: String = OLD_PATH) -> RunProgress:
	var p := RunProgress.new()
	p.path = p_path
	p.old_path = p_old
	p.data = _fresh()
	if FileAccess.file_exists(p_path):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(p_path))
		if typeof(parsed) == TYPE_DICTIONARY and int(parsed.get("version", 0)) == VERSION and typeof(parsed.get("reached", null)) == TYPE_DICTIONARY:
			p.data = parsed
		else:
			p.recovered_from_corrupt = true
			DirAccess.rename_absolute(p_path, p_path + ".corrupt")
	elif FileAccess.file_exists(p_old):
		p._migrate_old()
	if not p.data.has("seed"):  # saves from before the arrangements: the field is added on load, the file is rewritten at the next save (the version stays 2)
		var rng := RandomNumberGenerator.new()
		rng.randomize()
		p.data["seed"] = rng.randi() & 0x7fffffff
	return p


## The per-run seed arrangements are picked with (RunData.run_seed reads it; RW_RUN_SEED overrides it). A new one is drawn each time a run starts, after the run's data loaded.
func run_seed() -> int:
	return int(data.get("seed", 0))


static func _fresh() -> Dictionary:
	return {"version": VERSION, "reached": {}, "runs": 0, "best_phases": 0, "migrated_from": ""}  # "seed" is added by load_data


## Reads the old chapter save (never writes it) and marks the matching levels reached. Night One is always reached.
func _migrate_old() -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(old_path))
	if typeof(parsed) != TYPE_DICTIONARY or typeof(parsed.get("levels", null)) != TYPE_DICTIONARY:
		return
	for chapter in (parsed["levels"] as Dictionary):
		var node: String = CHAPTER_TO_NODE.get(chapter, "")
		if node != "" and int((parsed["levels"][chapter] as Dictionary).get("plays", 0)) > 0:
			data["reached"][node] = {"entries": 0, "migrated": true}
			migrated.append(node)
	data["migrated_from"] = "story_campaign.json"
	if not migrated.is_empty():
		save()


func is_reached(node_id: String, start_node: String = "warehouse") -> bool:
	return node_id == start_node or data["reached"].has(node_id)


func reached_ids() -> Array:
	return (data["reached"] as Dictionary).keys()


## Called when the player enters a level (a phase begins on it). Returns true when it was new.
func enter(node_id: String) -> bool:
	var fresh: bool = not data["reached"].has(node_id)
	var rec: Dictionary = data["reached"].get(node_id, {"entries": 0})
	rec["entries"] = int(rec.get("entries", 0)) + 1
	data["reached"][node_id] = rec
	save()
	return fresh


func run_started() -> void:
	data["runs"] = int(data["runs"]) + 1
	data["seed"] = (int(data.get("seed", 0)) * 1103515245 + 12345 + int(data["runs"])) & 0x7fffffff  # the next run's seed: this run already loaded its data
	save()


func run_ended(phases: int) -> void:
	data["best_phases"] = maxi(int(data["best_phases"]), phases)
	save()


func save() -> bool:
	var tmp := path + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(data, "\t"))
	f.close()
	return DirAccess.rename_absolute(tmp, path) == OK


## One line for the home screen when old progress was carried over.
func migration_note() -> String:
	if migrated.is_empty():
		return ""
	return "Your Story Campaign progress was carried over: %d level%s from your chapters are open. The old save file is untouched." % [migrated.size(), "" if migrated.size() == 1 else "s"]
