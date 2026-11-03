class_name StoryProgress
extends RefCounted
## Story Campaign saves: user://story_campaign.json, versioned, written atomically, never touching user://campaign.json. An
## unreadable file is set aside (.corrupt) and replaced by a fresh one; nothing here can affect the military campaign.

const SAVE_PATH := "user://story_campaign.json"
const VERSION := 1

var path := SAVE_PATH
var data: Dictionary = {}
var recovered_from_corrupt := false


static func load_data(p_path: String = SAVE_PATH) -> StoryProgress:
	var p := StoryProgress.new()
	p.path = p_path
	p.data = _fresh()
	if FileAccess.file_exists(p_path):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(p_path))
		if typeof(parsed) == TYPE_DICTIONARY and int(parsed.get("version", 0)) == VERSION and typeof(parsed.get("levels", null)) == TYPE_DICTIONARY:
			p.data = parsed
		else:
			p.recovered_from_corrupt = true
			DirAccess.rename_absolute(p_path, p_path + ".corrupt")
	return p


static func _fresh() -> Dictionary:
	return {"version": VERSION, "levels": {}}


func level_record(level_id: String) -> Dictionary:
	return data["levels"].get(level_id, {})


## Records one finished set (a summary from StoryRun.summary()). Returns the updated record.
func record(level_id: String, s: Dictionary) -> Dictionary:
	var rec: Dictionary = data["levels"].get(level_id, {"plays": 0, "clears": 0, "best_energy": 0.0, "best_accuracy": 0.0, "best_combo": 0,
		"best_passed": 0, "best_ending": "", "last_ending": "", "endings": {}, "branches_seen": {}})
	rec["plays"] = int(rec["plays"]) + 1
	rec["clears"] = int(rec["clears"]) + 1  # a set always plays to the end; every finished set counts
	rec["best_energy"] = maxf(float(rec["best_energy"]), float(s["energy"]))
	rec["best_accuracy"] = maxf(float(rec["best_accuracy"]), float(s["accuracy"]))
	rec["best_combo"] = maxi(int(rec["best_combo"]), int(s["best_combo"]))
	rec["best_passed"] = maxi(int(rec["best_passed"]), int(s["sequences_passed"]))
	var ending := str(s["ending"])
	rec["last_ending"] = ending
	rec["endings"][ending] = int(rec["endings"].get(ending, 0)) + 1
	var rank := int(s.get("ending_rank", 0))
	if rec["best_ending"] == "" or rank > int(rec.get("best_rank", -1)):
		rec["best_ending"] = ending
		rec["best_rank"] = rank
	for b in s.get("branches", []):
		var key := "%s:%s" % [b["id"], b["outcome"]]
		rec["branches_seen"][key] = int(rec["branches_seen"].get(key, 0)) + 1
	data["levels"][level_id] = rec
	save()
	return rec


func save() -> bool:
	var tmp := path + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(data, "\t"))
	f.close()
	return DirAccess.rename_absolute(tmp, path) == OK
