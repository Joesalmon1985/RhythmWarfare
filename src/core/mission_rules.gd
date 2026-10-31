class_name MissionRules
extends RefCounted
## The one campaign rule set (data/campaign/rules.json, PRD section 15): pad mapping, recognition windows, hold
## tolerance, sequence threshold, precision grades, capacity and the reward catalogue. Shared with tools/content.

const PATH := "res://data/campaign/rules.json"

static var _cache: Dictionary = {}


static func data() -> Dictionary:
	if _cache.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH))
		_cache = parsed if typeof(parsed) == TYPE_DICTIONARY else {}
	return _cache


static func window_s(name: String) -> float:
	return float(data().get("windows_ms", {}).get(name, 140.0)) / 1000.0


static func hold_complete_s() -> float:
	return float(data().get("hold", {}).get("complete_within_s", 0.15))


static func reward(id: String) -> Dictionary:
	return data().get("rewards", {}).get(id, {})


static func reward_name(id: String) -> String:
	return str(reward(id).get("name", id))


## Precision grade from the mean onset error (ms) and strays per cue: sharp, steady or loose.
static func grade(mean_abs_ms: float, strays: int, cues: int) -> String:
	var p: Dictionary = data().get("precision", {})
	var score := mean_abs_ms + float(p.get("stray_penalty_ms", 25.0)) * float(strays) / float(maxi(cues, 1))
	if score <= float(p.get("sharp_ms", 35.0)):
		return "sharp"
	if score <= float(p.get("steady_ms", 70.0)):
		return "steady"
	return "loose"


static func delay_s(grade_name: String) -> float:
	return float(data().get("precision", {}).get("delay_s", {}).get(grade_name, 3.0))


static func thumb_of_pad(pad: int) -> int:
	return int(data().get("thumb_of_pad", {}).get(str(pad), 0 if pad <= 2 else 1))
