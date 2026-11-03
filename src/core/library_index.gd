class_name LibraryIndex
extends RefCounted
## The loop library (songs/library/index.json, written by tools/content/build.py): every clip (groove, fill, bass line,
## backing) with its eight-bar cue patterns and one Ogg loop per part and sound, and every sound (instrument) with the
## rewards it produces. A mission authors none of this; the player's loadout picks from it.

const DEFAULT_DIR := "res://songs/library"

static var _default: LibraryIndex = null

var dir := ""  # the folder holding index.json and loops/
var clips: Dictionary = {}  # clip id -> {kind, name, key, bars, parts, bound, sounds, cues, loops, peak_db}
var sounds: Dictionary = {}  # sound id -> {family, name, placeholder, produces: [{reward, share}], blurb}
var defaults: Dictionary = {}  # the default loadout
var bpm := 174.0
var ticks_per_beat := 960
var loop_bars := 8
var error := ""


## songs/library/index.json of the project; cached once it has loaded. An absent or broken index gives an empty
## LibraryIndex (clips empty, `error` says why) that is not cached, so a library built later is picked up.
static func load_default() -> LibraryIndex:
	if _default != null:
		return _default
	var idx := load_from(DEFAULT_DIR.path_join("index.json"))
	if idx.error.is_empty():
		_default = idx
	return idx


static func clear_cache() -> void:
	_default = null


static func load_from(path: String) -> LibraryIndex:
	var idx := LibraryIndex.new()
	idx.dir = path.get_base_dir()
	if not FileAccess.file_exists(path):
		idx.error = "%s not found (build the library with tools/content/build.py)" % path
		return idx
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY or typeof(parsed.get("clips")) != TYPE_DICTIONARY or typeof(parsed.get("sounds")) != TYPE_DICTIONARY:
		idx.error = "%s is not a library index" % path
		return idx
	idx.clips = parsed["clips"]
	idx.sounds = parsed["sounds"]
	idx.defaults = parsed.get("defaults", {}) if typeof(parsed.get("defaults", {})) == TYPE_DICTIONARY else {}
	idx.bpm = float(parsed.get("bpm", 174))
	idx.ticks_per_beat = int(parsed.get("ticks_per_beat", 960))
	idx.loop_bars = int(parsed.get("loop_bars", 8))
	return idx


func is_empty() -> bool:
	return clips.is_empty()


func has_id(id: String) -> bool:
	return clips.has(id) or sounds.has(id)


## "groove", "fill", "bass", "backing" for a clip, "sound" for a sound, "" for an unknown id.
func kind(id: String) -> String:
	if clips.has(id):
		return str(clips[id].get("kind", ""))
	return "sound" if sounds.has(id) else ""


func name(id: String) -> String:
	if clips.has(id):
		return str(clips[id].get("name", id))
	if sounds.has(id):
		return str(sounds[id].get("name", id))
	return id


## [{reward, share}] of a sound (what a passed sequence of its instrument produces); [] when it has none.
func produces(sound: String) -> Array:
	var p: Variant = sounds.get(sound, {}).get("produces", [])
	return p if typeof(p) == TYPE_ARRAY else []


func clip_bars(clip: String) -> int:
	return int(clips.get(clip, {}).get("bars", loop_bars))


## The cues of one part of a clip inside one loop: [[tick, duration_ticks, pad], ...].
func cues(clip: String, part: String) -> Array:
	var c: Variant = clips.get(clip, {}).get("cues", {}).get(part, [])
	return c if typeof(c) == TYPE_ARRAY else []


## The loop file of a clip's part for a sound: an absolute (or res://) path, "" when the clip has none. A backing track
## has no sounds; its one loop is found under an empty sound id or as the part's only entry.
func loop_path(clip: String, part: String, sound: String) -> String:
	var by_sound: Variant = clips.get(clip, {}).get("loops", {}).get(part, {})
	if typeof(by_sound) != TYPE_DICTIONARY or by_sound.is_empty():
		return ""
	var rel := ""
	if by_sound.has(sound):
		rel = str(by_sound[sound])
	elif sound.is_empty() or not (clips[clip].get("sounds", {}) as Dictionary).has(part):
		rel = str(by_sound[""]) if by_sound.has("") else (str(by_sound.values()[0]) if by_sound.size() == 1 else "")
	return dir.path_join(rel) if not rel.is_empty() else ""


## Clip ids of one kind, in index order.
func clips_of(kind_name: String) -> Array:
	var out: Array = []
	for id in clips:
		if str(clips[id].get("kind", "")) == kind_name:
			out.append(str(id))
	return out


func _part_sounds(clip: String, part: String) -> Array:
	var s: Variant = clips.get(clip, {}).get("sounds", {}).get(part, [])
	return s if typeof(s) == TYPE_ARRAY else []


func _key_of(clip: String) -> String:
	return str(clips.get(clip, {}).get("key", ""))


## The ids valid for a loadout slot given the other picks in `loadout` (see Loadout.SLOTS): every groove; "" and the
## fills that play the picked kick and snare sounds; the kick and snare sounds of the picked groove (narrowed to the
## picked fill's when one is equipped); every bass line; the bass sounds of the picked line; the backing tracks in the
## bass line's key (or of no key). A pick that is not set yet restricts nothing it depends on only through that pick.
func compatible(slot: String, loadout: Dictionary) -> Array:
	var out: Array = []
	match slot:
		"groove", "bass":
			return clips_of(slot)
		"fill":
			out.append("")
			var kick := str(loadout.get("kick_sound", ""))
			var snare := str(loadout.get("snare_sound", ""))
			for id in clips_of("fill"):
				if (kick.is_empty() or _part_sounds(id, "kick").has(kick)) and (snare.is_empty() or _part_sounds(id, "snare").has(snare)):
					out.append(id)
		"kick_sound", "snare_sound":
			var part := "kick" if slot == "kick_sound" else "snare"
			var groove := str(loadout.get("groove", ""))
			if not clips.has(groove):
				return out
			var fill := str(loadout.get("fill", ""))
			for s in _part_sounds(groove, part):
				if fill.is_empty() or not clips.has(fill) or _part_sounds(fill, part).has(s):
					out.append(str(s))
		"bass_sound":
			var bass := str(loadout.get("bass", ""))
			for s in _part_sounds(bass, "bass"):
				out.append(str(s))
		"backing":
			var key := _key_of(str(loadout.get("bass", "")))
			for id in clips_of("backing"):
				var k := _key_of(id)
				if key.is_empty() or k.is_empty() or k == key:
					out.append(id)
	return out
