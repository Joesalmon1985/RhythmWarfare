class_name TrialData
extends RefCounted
## The dungeon's data (content/trial/passages.json): the zones, the passages with their text, scene, tier and choices, the rhythm phrases, the creatures, the items
## and the music. validate() checks everything a run of it depends on; errors name the passage. docs/TRIAL_OPENING.md describes the format.

const PATH := "res://content/trial/passages.json"
const MAX_DEFAULT_WALK := 120
const HOTSPOTS_PATH := "res://content/trial/hotspots.json"  # the passages' hotspots (HotspotContract), keyed by passage

var raw: Dictionary = {}
var passages: Dictionary = {}  # int passage -> entry (passage 0 is the one a lost fight leads to)
var phrases: Dictionary = {}
var encounters: Dictionary = {}
var scenes: Dictionary = {}
var zones: Dictionary = {}
var items: Dictionary = {}
var start := 1
var hotspots: Dictionary = {}  # int passage -> Array of normalised hotspot dictionaries (authored in content/trial/hotspots.json; a passage with none has no entry)
var errors: Array = []
static var _maps: Dictionary = {}  # map id -> StoryMap (the zone maps are read once)


static func load_default() -> TrialData:
	return load_file(PATH)


static func load_file(path: String, run_data: RunData = null) -> TrialData:
	var d := TrialData.new()
	if not FileAccess.file_exists(path):
		d.errors.append("%s not found" % path)
		return d
	var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(v) != TYPE_DICTIONARY:
		d.errors.append("%s is not a JSON object" % path)
		return d
	d.raw = v
	d.start = int(v.get("start", 1))
	for k in (v.get("passages", {}) as Dictionary):
		d.passages[int(k)] = v["passages"][k]
	d.phrases = v.get("phrases", {})
	d.encounters = v.get("encounters", {})
	d.scenes = v.get("scenes", {})
	d.zones = v.get("zones", {})
	d.items = v.get("items", {})
	d.validate(run_data if run_data != null else RunData.load_default())
	if path == PATH and d.errors.is_empty():  # the Bassment's hotspots (content/trial/hotspots.json) are read with the default data only
		d.load_hotspots(HOTSPOTS_PATH)
	return d


func passage(n: int) -> Dictionary:
	return passages.get(n, {})


func choices(n: int) -> Array:
	return passage(n).get("choices", [])


func zone_name(n: int) -> String:
	return str((zones.get(str(passage(n).get("zone", "")), {}) as Dictionary).get("name", ""))


## The choices of passage `n` that a player holding `flags` may see (a choice with "requires" is hidden until that item is held).
func choices_for(n: int, flags: Array) -> Array:
	return choices(n).filter(func(c: Dictionary) -> bool: return str(c.get("requires", "")) == "" or str(c["requires"]) in flags)


func validate(run_data: RunData) -> void:
	if not passages.has(start):
		errors.append("start passage %d does not exist" % start)
	if not passages.has(0):
		errors.append("passage 0 (the one a lost fight leads to) is missing")
	var music: Dictionary = raw.get("music", {})
	for key in ["audio", "chart", "fight_audio", "fight_chart"]:
		if music.has(key) or key in ["audio", "chart"]:
			if not run_data.packs.has(str(music.get(key, ""))):
				errors.append("music.%s pack '%s' does not exist" % [key, music.get(key, "")])
	if not (run_data.cfg.get("treatments", {}) as Dictionary).has(str(music.get("treatment", "none"))):
		errors.append("music.treatment '%s' is not in run.json" % music.get("treatment", ""))
	for pid in phrases:
		var ph: Dictionary = phrases[pid]
		if str(ph.get("family", "")) not in ["drums", "bass"]:
			errors.append("phrase %s: family must be drums or bass" % pid)
		if int(ph.get("tier", 0)) < 1 or int(ph.get("tier", 0)) > RunData.TIERS:
			errors.append("phrase %s: tier must be 1 to %d" % [pid, RunData.TIERS])
	for zid in zones:
		var z: Dictionary = zones[zid]
		if str(z.get("name", "")) == "" or str(z.get("look", "")) == "":
			errors.append("zone %s needs a name and a one-line look" % zid)
		if not scenes.has(str(z.get("scene", ""))):
			errors.append("zone %s: scene '%s' is not defined" % [zid, z.get("scene", "")])
		if int(z.get("tier", 0)) < 1 or int(z.get("tier", 0)) > RunData.TIERS:
			errors.append("zone %s: tier must be 1 to %d" % [zid, RunData.TIERS])
	# (the flat scene pictures were deleted: a scene is now only an id that zones and passages name; each zone is a 2.5D map)
	var victories := 0
	for n in passages:
		var p: Dictionary = passages[n]
		var kind := str(p.get("kind", "normal"))
		if kind not in ["normal", "death", "victory"]:
			errors.append("passage %d: kind must be normal, death or victory" % n)
		if kind == "victory":
			victories += 1
		if n < 0:
			errors.append("passage %d: ids are 0 or more" % n)
		if str(p.get("title", "")) == "" or str(p.get("text", "")).length() < 40:
			errors.append("passage %d: needs a title and real text" % n)
		if not zones.has(str(p.get("zone", ""))):
			errors.append("passage %d: zone '%s' is not defined" % [n, p.get("zone", "")])
		if not scenes.has(str(p.get("scene", ""))):
			errors.append("passage %d: scene '%s' is not defined" % [n, p.get("scene", "")])
		if int(p.get("tier", 1)) < 1 or int(p.get("tier", 1)) > RunData.TIERS:
			errors.append("passage %d: tier must be 1 to %d" % [n, RunData.TIERS])
		for g in p.get("grants", []):
			if not items.has(str(g)):
				errors.append("passage %d grants '%s', which is not an item" % [n, g])
		var cs: Array = p.get("choices", [])
		if cs.is_empty():
			errors.append("passage %d has no choices (an ending still offers a way out)" % n)
		var defaults := 0
		for c0 in cs:
			if str(c0.get("requires", "")) == "":
				if bool(c0.get("default", false)):
					defaults += 1
			elif bool(c0.get("default", false)):
				errors.append("passage %d: a choice that needs an item cannot be the default" % n)
			elif not items.has(str(c0["requires"])):
				errors.append("passage %d: choice '%s' needs '%s', which is not an item" % [n, c0.get("label", ""), c0["requires"]])
		if not cs.is_empty() and defaults != 1:
			errors.append("passage %d: exactly one choice without a requirement must be the default (taken when nobody chooses within four bars), found %d" % [n, defaults])
		var exits := 0
		for c in cs:
			var to: Variant = c.get("to", null)
			if to == null:
				exits += 1
				if str(c.get("exit", "")) == "":
					errors.append("passage %d: choice '%s' has neither a destination nor an exit" % [n, c.get("label", "")])
			elif not passages.has(int(to)):
				errors.append("passage %d: choice '%s' leads to %d, which has no entry" % [n, c.get("label", ""), int(to)])
			var ph: Variant = c.get("phrase", null)
			if ph != null and not phrases.has(str(ph)):
				errors.append("passage %d: choice '%s' uses phrase '%s', which is not defined" % [n, c.get("label", ""), ph])
			if to != null and ph == null:
				errors.append("passage %d: choice '%s' needs a phrase (a rhythm to play)" % [n, c.get("label", "")])
			if c.has("encounter"):
				if not encounters.has(str(c["encounter"])):
					errors.append("passage %d: encounter '%s' is not defined" % [n, c["encounter"]])
				if int(c.get("lives", 0)) < 1:
					errors.append("passage %d: a fight needs lives (3: the third lost phrase ends the trial)" % n)
			if c.has("test"):
				for key in ["pass", "fail"]:
					if not passages.has(int(c["test"][key])):
						errors.append("passage %d: the luck test's %s leads to %d, which has no entry" % [n, key, int(c["test"][key])])
				if ph == null:
					errors.append("passage %d: a luck test needs a phrase" % n)
				if int(c["test"]["pass"]) != int(to if to != null else -1):
					errors.append("passage %d: a luck test's 'to' must be its pass passage" % n)
			if str(c.get("label", "")) == "":
				errors.append("passage %d: every choice needs a label" % n)
		if kind in ["death", "victory"] and exits != cs.size():
			errors.append("passage %d: a %s only offers the way back to the Warehouse" % [n, kind])
		if kind == "normal" and exits > 0:
			errors.append("passage %d: only deaths and the victory lead out of the dungeon" % n)
	if victories != 1:
		errors.append("the dungeon needs exactly one victory passage (found %d)" % victories)
	for eid in encounters:
		var e: Dictionary = encounters[eid]
		for key in ["portrait", "portrait_hit"]:
			if not ResourceLoader.exists(str(e.get(key, ""))) and not FileAccess.file_exists(str(e.get(key, ""))):
				errors.append("encounter %s: %s %s is missing" % [eid, key, e.get(key, "")])
		for key in ["name", "intro", "on_win", "on_fail", "on_defeat"]:
			if str(e.get(key, "")) == "":
				errors.append("encounter %s needs %s" % [eid, key])
	_validate_maps()
	if errors.is_empty():
		_validate_graph()


## The zone map of a passage's zone (null when it has none or fails to load).
static func map_of(map_id: String) -> StoryMap:
	if not _maps.has(map_id):
		_maps[map_id] = StoryMap.load_chapter(map_id)
	return _maps[map_id]


## Every zone names its map (content/story/maps/<id>.json, valid), every passage stands at a waypoint of its zone's map and every choice leads toward a waypoint of it (`exit_wp`).
func _validate_maps() -> void:
	for zid in zones:
		var mid := str(zones[zid].get("map", ""))
		if mid == "":
			errors.append("zone %s names no map" % zid)
			continue
		var m := map_of(mid)
		if not m.errors.is_empty():
			errors.append("zone %s: map %s is invalid: %s" % [zid, mid, "; ".join(PackedStringArray(m.errors))])
	for n in passages:
		var p: Dictionary = passages[n]
		var zmap := str((zones.get(str(p.get("zone", "")), {}) as Dictionary).get("map", ""))
		if zmap == "":
			continue
		if str(p.get("map", "")) != zmap:
			errors.append("passage %d: map '%s' is not its zone's map '%s'" % [n, p.get("map", ""), zmap])
			continue
		var m2 := map_of(zmap)
		if not m2.errors.is_empty():
			continue
		if not m2.has_waypoint(str(p.get("waypoint", ""))):
			errors.append("passage %d: waypoint '%s' is not in map %s" % [n, p.get("waypoint", ""), zmap])
		for c in p.get("choices", []):
			if not m2.has_waypoint(str(c.get("exit_wp", ""))):
				errors.append("passage %d: choice '%s' exit_wp '%s' is not a waypoint of map %s" % [n, c.get("label", ""), c.get("exit_wp", ""), zmap])
			elif str(c["exit_wp"]) == str(p.get("waypoint", "")):
				errors.append("passage %d: choice '%s' exit_wp is the passage's own waypoint (an exit is somewhere else in the room)" % [n, c.get("label", "")])


## Loads and validates content/trial/hotspots.json ({"world": "bassment", "hotspots": [...]}, each hotspot's `scene` the passage number) with HotspotContract. A route is a passage number as a string
## ("12") or "exit" (the way back to the Warehouse); the allowed ones are the passage's choice destinations, a luck test's fail passage, "0" where it has a fight. A Bassment passage shows 1 to 4
## hotspots (37 passages have a single way on, so the run's minimum of 2 is 1 here); the default exit leads where the passage's default choice does. A missing file is fine (not authored yet).
func load_hotspots(path: String) -> void:
	if not FileAccess.file_exists(path):
		return
	var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(v) != TYPE_DICTIONARY:
		errors.append("%s is not a JSON object" % path)
		return
	var by_passage: Dictionary = {}
	for h in v.get("hotspots", []):
		if typeof(h) != TYPE_DICTIONARY:
			errors.append("%s: a hotspot is not an object" % path)
			continue
		var sc := str(h.get("scene", ""))
		if not sc.is_valid_int() or not passages.has(int(sc)):
			errors.append("%s: hotspot %s: scene '%s' is not a passage" % [path, h.get("id", ""), sc])
			continue
		var n := int(sc)
		var p: Dictionary = passages[n]
		if not by_passage.has(n):
			by_passage[n] = []
		by_passage[n].append(HotspotContract.normalize(h, str(v.get("world", "bassment")), str(p.get("map", ""))))
	for n in by_passage:
		var p2: Dictionary = passages[n]
		var routes: Array = []
		var default_route := ""
		for c in p2.get("choices", []):
			var dest := "exit" if c.get("to", null) == null else str(int(c["to"]))
			if dest not in routes:
				routes.append(dest)
			if bool(c.get("default", false)):
				default_route = dest
			if c.has("test"):
				var f := str(int(c["test"]["fail"]))
				if f not in routes:
					routes.append(f)
			if c.has("encounter") and "0" not in routes:
				routes.append("0")
		var required: Array = []
		for c in p2.get("choices", []):
			required.append("exit" if c.get("to", null) == null else str(int(c["to"])))
		HotspotContract.validate_scene(by_passage[n], {"where": "passage %d" % n, "map": str(p2.get("map", "")), "world": str(v.get("world", "bassment")), "routes": routes,
			"start_energy": 60.0, "min_available": 1, "max_available": 4, "min_px_floor": HotspotContract.BASSMENT_MIN_PX, "default_any_kind": true, "default_route": default_route, "exit_routes_required": required, "figures": encounters.keys()}, errors)
		hotspots[n] = by_passage[n]


func hotspots_of(passage_n: int) -> Array:
	return hotspots.get(passage_n, [])


## The zone's start waypoint (where the camera comes in) and the map id.
func zone_map(zone: String) -> String:
	return str((zones.get(zone, {}) as Dictionary).get("map", ""))


## Reachability, the walk by defaults and the tier rule, once the links are known to be sound.
func _validate_graph() -> void:
	var reach := reachable()
	for n in passages:
		if n != 0 and n not in reach:
			errors.append("passage %d cannot be reached from the start" % n)
	var walk := default_walk()
	if walk.is_empty() or str(passage(int(walk[walk.size() - 1])).get("kind", "")) != "victory":
		errors.append("the default choices alone do not walk from the start to the victory (%s)" % str(walk))
	var last_tier := 0
	for n in walk:
		var t := int(passage(int(n)).get("tier", 1))
		if t < last_tier:
			errors.append("passage %d: the tier falls from %d to %d along the default walk (it must rise with depth)" % [n, last_tier, t])
		last_tier = t


## Passages reachable from the start (items ignored: a choice that needs one still counts as a link).
func reachable() -> Array:
	var seen := {}
	var queue: Array = [start]
	while not queue.is_empty():
		var n: int = queue.pop_back()
		if seen.has(n) or not passages.has(n):
			continue
		seen[n] = true
		for c in choices(n):
			if c.get("to", null) != null:
				queue.append(int(c["to"]))
			if c.has("test"):
				queue.append(int(c["test"]["fail"]))
	var out: Array = seen.keys()
	out.sort()
	return out


## The passages visited when nobody ever picks anything and every phrase is passed: [start, ..., ending]. Empty when it loops or runs past MAX_DEFAULT_WALK.
func default_walk() -> Array:
	var walk: Array = [start]
	var n := start
	while walk.size() <= MAX_DEFAULT_WALK:
		var next := -1
		var is_exit := false
		for c in choices(n):
			if bool(c.get("default", false)):
				if c.get("to", null) == null:
					is_exit = true
				else:
					next = int(c["to"])
				break
		if is_exit:
			return walk
		if next < 0 or next in walk:
			return []
		walk.append(next)
		n = next
	return []


func zone_of_passage(n: int) -> String:
	return str(passage(n).get("zone", ""))
