class_name Rules
extends RefCounted
## Actor, weapon, roster and battlefield data for the simulation, loaded from data/.

var actors: Dictionary = {}
var weapons: Dictionary = {}
var roster: Dictionary = {}
var battlefield: Dictionary = {}
var map: Dictionary = {}  # terrain: tiles, decorations and blocked cells (data/maps/<id>.json), may be empty
var repair: Dictionary = {}
var aircraft: Dictionary = {}
var locomotors: Dictionary = {}
var vehicle_cycle: Array = []      # actor ids produced by successive kicks (round robin)
var infantry_pattern: Array = []   # actor ids produced by successive snares (infantry_per_snare at a time)


static func load_default(roster_id: String = "openra_mvp_01", battlefield_id: String = "mvp_mirrored_01") -> Rules:
	var r := Rules.new()
	var rules: Dictionary = _read_json("res://data/openra_rules.json")
	r.actors = rules.get("actors", {})
	r.weapons = rules.get("weapons", {})
	r.locomotors = rules.get("locomotors", {})
	var ros: Dictionary = _read_json("res://data/rosters/%s.json" % roster_id)
	r.roster = ros.get("roles", {})
	r.repair = ros.get("repair", {})
	r.aircraft = ros.get("aircraft", {})
	r.vehicle_cycle = ros.get("vehicle_cycle", [])
	r.infantry_pattern = ros.get("infantry_pattern", [])
	r.battlefield = _read_json("res://data/battlefields/%s.json" % battlefield_id)
	var map_id := str(r.battlefield.get("map", ""))
	if not map_id.is_empty() and FileAccess.file_exists("res://data/maps/%s.json" % map_id):
		r.map = _read_json("res://data/maps/%s.json" % map_id)
	return r


## Cells no ground unit can enter because of terrain (trees, rocks), as Vector2i.
func terrain_blocked() -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	for c in map.get("blocked", []):
		out.append(Vector2i(int(c[0]), int(c[1])))
	return out


static func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		push_error("missing data file: " + path)
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	return parsed if typeof(parsed) == TYPE_DICTIONARY else {}


func actor_for_role(role: String) -> Dictionary:
	return actors.get(roster.get(role, ""), {})


func actor_id_for_role(role: String) -> String:
	return str(roster.get(role, ""))


func weapon(name: String) -> Dictionary:
	return weapons.get(name, {})


## Damage after the warhead's armour table (percent; a missing armour entry means 100%).
static func damage_versus(warhead: Dictionary, armor: String) -> int:
	var versus: Dictionary = warhead.get("versus", {})
	var pct := int(versus.get(armor, 100))
	return int(warhead.get("damage", 0)) * pct / 100
