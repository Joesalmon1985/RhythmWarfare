class_name StoryTrace
extends RefCounted
## Scripted-run helpers for the campaign walk-through (tools/story/walk_campaign.sh): RW_STORY_TRACE=<file> appends one line per scene, RW_STORY_AUTO_ADVANCE=1 makes
## the result and interlude scenes move on by themselves, RW_STORY_POLICIES="night_one=perfect;mothership=accuracy:0.8@2" picks the input policy (and seed) per chapter,
## RW_STORY_RECORD=1 lets a scripted run write the story save (the script points the user data directory at a throwaway folder, never the owner's save).


const INTERLUDE_SPEED := 12.0


static func auto_advance() -> bool:
	return OS.get_environment("RW_STORY_AUTO_ADVANCE") == "1"


static func record_scripted() -> bool:
	return OS.get_environment("RW_STORY_RECORD") == "1"


## One line, key=value pairs, appended to the trace file (a no-op without RW_STORY_TRACE).
static func line(scene: String, fields: Dictionary) -> void:
	var path := OS.get_environment("RW_STORY_TRACE")
	if path == "":
		return
	var parts: Array = [scene]
	for k in fields:
		parts.append("%s=%s" % [k, str(fields[k])])
	var f := FileAccess.open(path, FileAccess.READ_WRITE if FileAccess.file_exists(path) else FileAccess.WRITE)
	if f == null:
		return
	f.seek_end()
	f.store_line(" ".join(PackedStringArray(parts)))
	f.close()


## {policy, seed} for a chapter: the RW_STORY_POLICIES entry, else RW_AUTOPLAY and RW_SEED ("" when the run is played by hand).
static func policy_for(chapter: String) -> Dictionary:
	var pol := OS.get_environment("RW_AUTOPLAY")
	var sd := int(OS.get_environment("RW_SEED")) if OS.has_environment("RW_SEED") else 1
	for entry in OS.get_environment("RW_STORY_POLICIES").split(";", false):
		var kv := entry.split("=", false, 1)
		if kv.size() == 2 and kv[0] == chapter:
			var ps := kv[1].split("@", false, 1)
			pol = ps[0]
			sd = int(ps[1]) if ps.size() > 1 else 1
	return {"policy": pol, "seed": sd}


## The chapters the Story Campaign menu offers as playable (available and unlocked), in order.
static func unlocked_ids() -> Array:
	var chapters := StoryChapters.load_default()
	var out: Array = []
	for c in chapters.chapters:
		if chapters.available(str(c["id"])) and chapters.unlocked(str(c["id"]), Session.story_progress):
			out.append(str(c["id"]))
	return out
