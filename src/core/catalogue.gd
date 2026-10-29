class_name Catalogue
extends RefCounted
## The instrument catalogue (data/instruments/catalogue.json): each profile names a musical family, the level whose
## clear unlocks it, a sound identity (rendered by the owner per song part) and a production recipe. A recipe is a
## deterministic cycle of steps; each step is a group of {actor, count}. `required_producers` tags decide when the
## slot the profile is equipped in is available. Family is musical metadata only.

const PATH := "res://data/instruments/catalogue.json"
const FAMILIES := ["kick", "snare", "bass"]
## Producer tag -> the building role in the simulation that has to be alive.
const PRODUCER_ROLE := {"barracks": "barracks", "war_factory": "factory", "air_support": "pad"}
## Production queue of an actor (openra_rules.json) -> the producer tag it needs.
const QUEUE_TAG := {"Infantry": "barracks", "Vehicle": "war_factory", "Aircraft": "air_support"}
const CAPS := {"kick": 2, "snare": 2, "bass": 3}
## actor -> [singular, plural] for the loadout screen's unit mix text
const UNIT_NAMES := {"e1": ["rifleman", "riflemen"], "e2": ["grenadier", "grenadiers"], "e3": ["rocket soldier", "rocket soldiers"],
	"e4": ["flamethrower", "flamethrowers"], "jeep": ["jeep", "jeeps"], "1tnk": ["light tank", "light tanks"], "2tnk": ["medium tank", "medium tanks"],
	"3tnk": ["heavy tank", "heavy tanks"], "4tnk": ["mammoth tank", "mammoth tanks"], "apc": ["APC", "APCs"], "arty": ["artillery", "artillery"],
	"ftrk": ["flak truck", "flak trucks"], "v2rl": ["V2 launcher", "V2 launchers"]}

var profiles: Dictionary = {}  # id -> profile dictionary
var order: Array = []          # ids in catalogue order


static func load_default() -> Catalogue:
	var c := Catalogue.new()
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if typeof(parsed) == TYPE_DICTIONARY:
		for p in parsed.get("instruments", []):
			c.profiles[str(p["id"])] = p
			c.order.append(str(p["id"]))
	return c


func has_profile(id: String) -> bool:
	return profiles.has(id)


func display_name(id: String) -> String:
	return str(profiles.get(id, {}).get("display_name", id))


func family_of(id: String) -> String:
	return str(profiles.get(id, {}).get("family", ""))


func unlock_level(id: String) -> int:
	return int(profiles.get(id, {}).get("available_from_level", 99))


func production_type(id: String) -> String:
	return str(profiles.get(id, {}).get("production", {}).get("type", "cycle"))


func steps(id: String) -> Array:
	return profiles.get(id, {}).get("production", {}).get("steps", [])


func required_producers(id: String) -> Array:
	return profiles.get(id, {}).get("production", {}).get("required_producers", [])


func profiles_of_family(family: String) -> Array:
	var out: Array = []
	for id in order:
		if profiles[id]["family"] == family:
			out.append(id)
	return out


## "2 riflemen" or "light tank, jeep" for the loadout screen.
func unit_mix_text(id: String) -> String:
	var parts: Array[String] = []
	for step in steps(id):
		var bits: Array[String] = []
		for u in step["units"]:
			var names: Array = UNIT_NAMES.get(str(u["actor"]), [str(u["actor"]), str(u["actor"])])
			bits.append("%d %s" % [int(u["count"]), names[1] if int(u["count"]) > 1 else names[0]])
		parts.append(" + ".join(PackedStringArray(bits)))
	if production_type(id) != "cycle":
		return "air service (not used before level 7)"
	return ("repeating: " if parts.size() > 1 else "") + ", then ".join(PackedStringArray(parts))


## Errors for a loaded catalogue: unknown families, recipe actors without art or rules, producer tags that disagree
## with where the simulation builds each actor, duplicate ids.
func validate(rules: Rules, sequences: Dictionary) -> Array:
	var errors: Array = []
	var seen := {}
	var images: Dictionary = sequences.get("images", {})
	for id in order:
		var p: Dictionary = profiles[id]
		if seen.has(id):
			errors.append("duplicate profile id %s" % id)
		seen[id] = true
		if not FAMILIES.has(str(p.get("family", ""))):
			errors.append("%s: unsupported family '%s'" % [id, p.get("family", "")])
		var prod: Dictionary = p.get("production", {})
		var declared: Array = prod.get("required_producers", [])
		for tag in declared:
			if not PRODUCER_ROLE.has(tag):
				errors.append("%s: unknown producer tag '%s'" % [id, tag])
		if str(prod.get("type", "cycle")) != "cycle":
			continue  # air service profiles are recognised but their recipe is not a ground cycle
		var needed := {}
		if prod.get("steps", []).is_empty():
			errors.append("%s: a cycle recipe needs at least one step" % id)
		for step in prod.get("steps", []):
			for u in step.get("units", []):
				var actor := str(u.get("actor", ""))
				if not rules.actors.has(actor):
					errors.append("%s: actor '%s' is not in openra_rules.json" % [id, actor])
					continue
				if not images.has(actor):
					errors.append("%s: actor '%s' has no art in assets/openra/sequences.json" % [id, actor])
				if int(u.get("count", 0)) <= 0:
					errors.append("%s: actor '%s' needs a positive count" % [id, actor])
				var tag: String = QUEUE_TAG.get(str(rules.actors[actor].get("queue", "")), "")
				if tag.is_empty():
					errors.append("%s: actor '%s' is not produced by a building" % [id, actor])
				needed[tag] = true
		for tag in needed:
			if not declared.has(tag):
				errors.append("%s: recipe needs producer '%s' but required_producers lists %s" % [id, tag, str(declared)])
		for tag in declared:
			if not needed.has(tag):
				errors.append("%s: required_producers lists '%s' which no recipe actor needs" % [id, tag])
	return errors


## Loadout validation (PRD section 14): `selection` maps slot id -> profile id; `slot_families` slot id -> family;
## `required_slots` must all be filled; profiles must exist, match the slot's family, be unlocked and be distinct
## within a family, and no family may exceed its cap (2 kick, 2 snare, 3 bass).
func validate_loadout(selection: Dictionary, slot_families: Dictionary, required_slots: Array, unlocked: Array) -> Array:
	var errors: Array = []
	var per_family := {}
	for slot in required_slots:
		if not selection.has(slot) or str(selection[slot]).is_empty():
			errors.append("required slot %s has no instrument" % slot)
	for slot in selection:
		var id := str(selection[slot])
		if not profiles.has(id):
			errors.append("slot %s: unknown instrument %s" % [slot, id])
			continue
		var fam: String = slot_families.get(slot, "")
		if family_of(id) != fam:
			errors.append("slot %s takes a %s instrument, not %s" % [slot, fam, family_of(id)])
		if not unlocked.has(id):
			errors.append("slot %s: %s is locked (unlocks after level %d)" % [slot, display_name(id), unlock_level(id) - 1])
		if not per_family.has(fam):
			per_family[fam] = []
		if per_family[fam].has(id):
			errors.append("%s is equipped twice in the %s family" % [display_name(id), fam])
		per_family[fam].append(id)
	for fam in per_family:
		if per_family[fam].size() > int(CAPS.get(fam, 0)):
			errors.append("at most %d %s instruments can be equipped" % [int(CAPS.get(fam, 0)), fam])
	return errors
