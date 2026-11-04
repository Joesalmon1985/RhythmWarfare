class_name StoryChapters
extends RefCounted
## The chapter registry (content/story/chapters.json): which chapters exist, how a chapter's ending routes to the next (and the
## interlude cutscene between them), and which are unlocked by the story saves. Chapters whose data file is not shipped yet are
## listed as unavailable rather than failing.

const PATH := "res://content/story/chapters.json"
const INTERLUDES := "res://content/story/interludes.json"

var chapters: Array = []


static func load_default() -> StoryChapters:
	var c := StoryChapters.new()
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if typeof(parsed) == TYPE_DICTIONARY:
		c.chapters = parsed.get("chapters", [])
	return c


func chapter(id: String) -> Dictionary:
	for c in chapters:
		if str(c["id"]) == id:
			return c
	return {}


func available(id: String) -> bool:
	var c := chapter(id)
	return not c.is_empty() and FileAccess.file_exists(str(c["data"]))


## The route a finished `ending` of chapter `id` takes: {to, interlude, label} or {} (the story's current end).
func route(id: String, ending: String) -> Dictionary:
	for r in chapter(id).get("routes", []):
		if ending in r["on"] and available(str(r["to"])):
			return r
	return {}


## A chapter is unlocked when it is the first, or an earlier chapter was finished with an ending that routes to it.
func unlocked(id: String, progress: StoryProgress) -> bool:
	var c := chapter(id)
	if c.is_empty():
		return false
	if str(c.get("unlock_from", "")).is_empty():
		return true
	for other in chapters:
		var rec := progress.level_record(str(other["id"]))
		if rec.is_empty():
			continue
		for r in other.get("routes", []):
			if str(r["to"]) != id:
				continue
			for e in r["on"]:
				if rec.get("endings", {}).has(e):
					return true
	return false


static func interlude(name: String) -> Dictionary:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(INTERLUDES))
	return parsed.get(name, {}) if typeof(parsed) == TYPE_DICTIONARY else {}
