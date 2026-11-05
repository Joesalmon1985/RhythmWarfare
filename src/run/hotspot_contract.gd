class_name HotspotContract
extends RefCounted
## The hotspot data contract (docs/VISUAL_RHYTHM_ADVENTURE_PLAN.md section 2, docs/CONTINUOUS_RUN.md "Hotspots"): the field names, the allowed values and the validator both
## RunData (content/run/hotspots/<world>.json) and TrialData (content/trial/hotspots.json) call. Pure: it reads the map json (cached) and the context it is given, nothing else.
##
## A file is {"world": "<run world id | bassment>", "hotspots": [ hotspot, ... ]}; a hotspot (every field except id, scene, anchor, kind, on_success is optional):
##   id, world, scene (a run scene id, or a Bassment passage number), map, anchor, kind, radius_m (0.8), min_px (72, never less), available, look, challenge, on_success, on_failure,
##   cinematic, default, repeatable.

const KINDS := ["exit", "object", "character", "feature", "encounter", "secret"]
const ANCHORS := ["thing", "waypoint", "actor", "pos"]
const LOOK_AVAILABLE := ["glow", "pulse", "beckon", "flicker", "open", "crack"]
const LOOK_SELECTED := ["ring"]
const LOOK_COMMITTED := ["flash"]
const FAMILIES := ["drums", "bass"]
const MIN_PX := 72.0
const MIN_PER_SCENE := 2
const MAX_PER_SCENE := 4
const MAX_FAIL_ENERGY := -20.0  # a failure may cost at most this much energy (it must stay recoverable)
const MAX_GAIN_ENERGY := 20.0
const TRIAL_PREFIX := "trial:"  # a run route "trial:<passage>", or just "<passage>" ("1": the first), is the wizard's way into the Bassment
const KEEP_PREFIX := "keep:"  # a flag name with this prefix is persistent (RunProgress.flags, saved); any other is per run (RunProgress.run_flags)
const OUTCOME_KEYS := ["route", "flags_set", "cinematic", "energy", "music"]
const CINEMATIC_KEYS := ["move", "to", "bars", "look_at", "role", "style"]
const MOVES := ["place", "walk", "stagger", "run", "climb", "carried"]  # `place` is a cut (the drag to the cage); the others are RunRail styles (`walk` with a `style`)
const MUSIC := ["variation", "dip", "lift", "drop", "fill", "none"]

static var _maps: Dictionary = {}  # map id -> index


## What a map offers anchors: {ok, waypoints: {id: true}, things: {id: true}, actors: {id: true}, sectors: [{poly: PackedVector2Array, floor: float}]}.
static func map_index(map_id: String) -> Dictionary:
	if _maps.has(map_id):
		return _maps[map_id]
	var idx := {"ok": false, "waypoints": {}, "things": {}, "actors": {}, "sectors": []}
	var path: String = StoryMap.PATH % map_id
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path)) if FileAccess.file_exists(path) else null
	if typeof(parsed) == TYPE_DICTIONARY:
		idx["ok"] = true
		for w in parsed.get("waypoints", []):
			idx["waypoints"][str(w["id"])] = true
		for t in parsed.get("things", []):
			idx["things"][str(t["id"])] = true
		for h in parsed.get("homes", []):
			idx["actors"][str(h["actor"])] = true
		for s in parsed.get("sectors", []):
			var poly := PackedVector2Array()
			for p in s.get("polygon", []):
				poly.append(Vector2(float(p[0]), float(p[1])))
			idx["sectors"].append({"poly": poly, "floor": float(s.get("floor", 0.0))})
	_maps[map_id] = idx
	return idx


## A run route that is not a scene but a Bassment passage: "trial:1" or "1".
static func is_trial_route(route: String) -> bool:
	return route.begins_with(TRIAL_PREFIX) or (route != "" and route.is_valid_int())


static func is_keep(flag: String) -> bool:
	return flag.begins_with(KEEP_PREFIX)


## True when the hotspot has no condition at all (no flag, no energy, not once): the shape the default exit must have.
static func unconditional(h: Dictionary) -> bool:
	var a: Dictionary = h.get("available", {})
	return (a.get("flags_all", []) as Array).is_empty() and (a.get("flags_none", []) as Array).is_empty() and float(a.get("energy_min", 0.0)) <= 0.0 and not bool(a.get("once", false))


## True when the hotspot shows with empty world state and the run's starting energy (the "available at start" set the 2 to 4 rule counts).
static func at_start(h: Dictionary, start_energy: float) -> bool:
	var a: Dictionary = h.get("available", {})
	return (a.get("flags_all", []) as Array).is_empty() and float(a.get("energy_min", 0.0)) <= start_energy


## A hotspot with every optional field filled in (a copy): world, map, radius_m, min_px, available, look, default, repeatable.
static func normalize(h: Dictionary, world: String, map_id: String) -> Dictionary:
	var out: Dictionary = h.duplicate(true)
	out["scene"] = str(out.get("scene", ""))
	out["world"] = str(out.get("world", world))
	out["map"] = str(out.get("map", map_id))
	out["radius_m"] = float(out.get("radius_m", 0.8))
	out["min_px"] = float(out.get("min_px", MIN_PX))
	var av: Dictionary = out.get("available", {}) if typeof(out.get("available", {})) == TYPE_DICTIONARY else {}
	av["flags_all"] = av.get("flags_all", [])
	av["flags_none"] = av.get("flags_none", [])
	av["energy_min"] = float(av.get("energy_min", 0.0))
	av["once"] = bool(av.get("once", false))
	out["available"] = av
	var lk: Dictionary = out.get("look", {}) if typeof(out.get("look", {})) == TYPE_DICTIONARY else {}
	lk["available"] = str(lk.get("available", "glow"))
	lk["selected"] = str(lk.get("selected", "ring"))
	lk["committed"] = str(lk.get("committed", "flash"))
	out["look"] = lk
	out["default"] = bool(out.get("default", false))
	out["repeatable"] = bool(out.get("repeatable", false))
	return out


## The cinematic an outcome names, as {"steps": [step, ...]} (a step: {move, to, bars, role, style, look_at}); {} when none or unresolved. The outcome's `cinematic` is a name looked up in `named`
## (run.json `cinematics`: name -> {world, steps}), else in the hotspot's own `cinematic` (one spec, which every name of the hotspot is, or a map name -> spec), or an object written inline.
static func resolve_cinematic(h: Dictionary, outcome: Dictionary, named: Dictionary = {}) -> Dictionary:
	if not outcome.has("cinematic"):
		return {}
	var c: Variant = outcome["cinematic"]
	if typeof(c) == TYPE_DICTIONARY:
		return c if (c as Dictionary).has("steps") else {"steps": [c]}
	if named.has(str(c)) and typeof(named[str(c)]) == TYPE_DICTIONARY and (named[str(c)] as Dictionary).has("steps"):
		return {"steps": (named[str(c)] as Dictionary)["steps"]}
	var spec: Variant = h.get("cinematic", null)
	if typeof(spec) != TYPE_DICTIONARY:
		return {}
	for k in CINEMATIC_KEYS:
		if (spec as Dictionary).has(k):
			return {"steps": [spec]}
	var one: Variant = (spec as Dictionary).get(str(c), null)
	return {"steps": [one]} if typeof(one) == TYPE_DICTIONARY else {}


## Validates one scene's hotspot list. `ctx`: {where (a prefix for messages), map (map id), world, routes (Array of allowed route strings), start_energy, min_available (2), max_available (4),
## default_route (the route the default exit must lead to, "" = any), exit_routes_required (every one must be the success or failure route of some hotspot)}. Appends to `errors`.
static func validate_scene(list: Array, ctx: Dictionary, errors: Array) -> void:
	var where := str(ctx.get("where", "scene"))
	var start_e := float(ctx.get("start_energy", 60.0))
	var ids := {}
	var n_start := 0
	var defaults := 0
	var reached := {}
	for h in list:
		if typeof(h) != TYPE_DICTIONARY:
			errors.append("%s: a hotspot is not an object" % where)
			continue
		var hid := str(h.get("id", ""))
		var hw := "%s hotspot %s" % [where, hid if hid != "" else "(no id)"]
		if hid == "" or ids.has(hid):
			errors.append("%s: id missing or duplicated" % hw)
		ids[hid] = true
		_validate_one(h, hw, ctx, errors)
		if at_start(h, start_e):
			n_start += 1
		if bool(h.get("default", false)):
			if str(h.get("kind", "")) != "exit":
				errors.append("%s: only an exit can be the default" % hw)
			elif not unconditional(h):
				errors.append("%s: the default exit must always be available (no flags_all, flags_none, energy_min or once)" % hw)
			defaults += 1
			var dr := str((h.get("on_success", {}) as Dictionary).get("route", ""))
			var want := str(ctx.get("default_route", ""))
			if want != "" and dr != want:
				errors.append("%s: the default exit leads to '%s', the scene's default route is '%s'" % [hw, dr, want])
		for key in ["on_success", "on_failure"]:
			var oc: Variant = h.get(key, null)
			if typeof(oc) == TYPE_DICTIONARY and str((oc as Dictionary).get("route", "")) != "":
				reached[str(oc["route"])] = true
	var lo := int(ctx.get("min_available", MIN_PER_SCENE))
	var hi := int(ctx.get("max_available", MAX_PER_SCENE))
	if n_start < lo or n_start > hi:
		errors.append("%s: %d hotspots are available at the start; a scene shows %d to %d" % [where, n_start, lo, hi])
	if defaults != 1:
		errors.append("%s: exactly one default exit is needed (found %d)" % [where, defaults])
	for r in ctx.get("exit_routes_required", []):
		if not reached.has(str(r)):
			errors.append("%s: the route '%s' is not the outcome of any hotspot (every route must stay reachable)" % [where, r])


static func _validate_one(h: Dictionary, hw: String, ctx: Dictionary, errors: Array) -> void:
	var routes: Array = ctx.get("routes", [])
	var map_id := str(ctx.get("map", ""))
	var idx := map_index(map_id)
	if not bool(idx["ok"]):
		errors.append("%s: map %s not found" % [hw, map_id])
	if str(h.get("map", map_id)) != map_id:
		errors.append("%s: map '%s' is not the scene's map '%s'" % [hw, h.get("map", ""), map_id])
	if ctx.has("world") and str(h.get("world", ctx["world"])) != str(ctx["world"]):
		errors.append("%s: world '%s' is not '%s'" % [hw, h.get("world", ""), ctx["world"]])
	var kind := str(h.get("kind", ""))
	if kind not in KINDS:
		errors.append("%s: kind '%s' is not one of %s" % [hw, kind, ", ".join(PackedStringArray(KINDS))])
	var an: Variant = h.get("anchor", null)
	if typeof(an) != TYPE_DICTIONARY or (an as Dictionary).size() != 1 or str((an as Dictionary).keys()[0]) not in ANCHORS:
		errors.append("%s: anchor must be exactly one of {thing}, {waypoint}, {actor}, {pos: [x, y, z]}" % hw)
	elif bool(idx["ok"]):
		var key := str((an as Dictionary).keys()[0])
		var val: Variant = an[key]
		match key:
			"thing":
				if not (idx["things"] as Dictionary).has(str(val)):
					errors.append("%s: anchor thing '%s' is not in map %s" % [hw, val, map_id])
			"waypoint":
				if not (idx["waypoints"] as Dictionary).has(str(val)):
					errors.append("%s: anchor waypoint '%s' is not in map %s" % [hw, val, map_id])
			"actor":
				if not (idx["actors"] as Dictionary).has(str(val)):
					errors.append("%s: anchor actor '%s' has no home in map %s" % [hw, val, map_id])
			"pos":
				if typeof(val) != TYPE_ARRAY or (val as Array).size() != 3:
					errors.append("%s: anchor pos must be [x, y, z]" % hw)
				else:
					var p := Vector2(float(val[0]), float(val[2]))
					var inside := false
					for s in idx["sectors"]:
						if Geometry2D.is_point_in_polygon(p, s["poly"]):
							inside = true
							break
					if not inside:
						errors.append("%s: anchor pos %s is not inside any sector of map %s" % [hw, str(val), map_id])
	var r := float(h.get("radius_m", 0.8))
	if r <= 0.0 or r > 4.0:
		errors.append("%s: radius_m must be above 0 and at most 4" % hw)
	if float(h.get("min_px", MIN_PX)) < MIN_PX:
		errors.append("%s: min_px must be at least %d (a phone fingertip)" % [hw, int(MIN_PX)])
	var av: Variant = h.get("available", {})
	if typeof(av) != TYPE_DICTIONARY:
		errors.append("%s: available must be an object" % hw)
	else:
		for k in av:
			if str(k) not in ["flags_all", "flags_none", "energy_min", "once"]:
				errors.append("%s: available.%s is not a field" % [hw, k])
		for k in ["flags_all", "flags_none"]:
			if typeof(av.get(k, [])) != TYPE_ARRAY:
				errors.append("%s: available.%s must be a list" % [hw, k])
			else:
				for f in av[k]:
					if str(f) == "":
						errors.append("%s: available.%s holds an empty flag" % [hw, k])
	var lk: Variant = h.get("look", {})
	if typeof(lk) != TYPE_DICTIONARY:
		errors.append("%s: look must be an object" % hw)
	else:
		if str(lk.get("available", "glow")) not in LOOK_AVAILABLE:
			errors.append("%s: look.available '%s' is not one of %s" % [hw, lk.get("available"), ", ".join(PackedStringArray(LOOK_AVAILABLE))])
		if str(lk.get("selected", "ring")) not in LOOK_SELECTED:
			errors.append("%s: look.selected '%s' is not one of %s" % [hw, lk.get("selected"), ", ".join(PackedStringArray(LOOK_SELECTED))])
		if str(lk.get("committed", "flash")) not in LOOK_COMMITTED:
			errors.append("%s: look.committed '%s' is not one of %s" % [hw, lk.get("committed"), ", ".join(PackedStringArray(LOOK_COMMITTED))])
	var ch: Variant = h.get("challenge", null)
	if ch != null:
		if typeof(ch) != TYPE_DICTIONARY or str((ch as Dictionary).get("family", "")) not in FAMILIES or int((ch as Dictionary).get("tier", 0)) < 1 or int((ch as Dictionary).get("tier", 0)) > RunData.TIERS:
			errors.append("%s: challenge is null or {family: drums|bass, tier: 1..%d}" % [hw, RunData.TIERS])
	if typeof(h.get("on_success", null)) != TYPE_DICTIONARY:
		errors.append("%s: on_success is required" % hw)
	for key in ["on_success", "on_failure"]:
		var oc: Variant = h.get(key, null)
		if oc == null:
			continue
		if typeof(oc) != TYPE_DICTIONARY:
			errors.append("%s: %s must be an object" % [hw, key])
			continue
		_validate_outcome(h, key, oc, hw, routes, idx, ctx.get("cinematics", {}), errors)
	if kind == "exit" and str((h.get("on_success", {}) as Dictionary).get("route", "")) == "":
		errors.append("%s: an exit's on_success needs a route" % hw)
	var cin: Variant = h.get("cinematic", null)
	if cin != null:
		if typeof(cin) != TYPE_DICTIONARY:
			errors.append("%s: cinematic must be an object" % hw)
		else:
			var single := false
			for k in CINEMATIC_KEYS:
				if (cin as Dictionary).has(k):
					single = true
			if single:
				_validate_cine(cin, hw, idx, errors)
			else:
				for cname in cin:
					if typeof(cin[cname]) != TYPE_DICTIONARY:
						errors.append("%s: cinematic '%s' must be an object" % [hw, cname])
					else:
						_validate_cine(cin[cname], "%s cinematic '%s'" % [hw, cname], idx, errors)
	if typeof(h.get("default", false)) != TYPE_BOOL or typeof(h.get("repeatable", false)) != TYPE_BOOL:
		errors.append("%s: default and repeatable are true or false" % hw)


static func _validate_outcome(h: Dictionary, key: String, oc: Dictionary, hw: String, routes: Array, idx: Dictionary, named: Dictionary, errors: Array) -> void:
	for k in oc:
		if str(k) not in OUTCOME_KEYS:
			errors.append("%s: %s.%s is not a field (%s)" % [hw, key, k, ", ".join(PackedStringArray(OUTCOME_KEYS))])
	var route := str(oc.get("route", ""))
	if route != "" and route not in routes:  # (a Bassment passage is a route when the scene has the trial gate: RunData adds it to `routes`)
		errors.append("%s: %s route '%s' is not a route of the scene (%s)" % [hw, key, route, ", ".join(PackedStringArray(routes))])
	if typeof(oc.get("flags_set", [])) != TYPE_ARRAY:
		errors.append("%s: %s.flags_set must be a list" % [hw, key])
	else:
		for f in oc.get("flags_set", []):
			if str(f) == "":
				errors.append("%s: %s.flags_set holds an empty flag" % [hw, key])
	if oc.has("energy"):
		var e := float(oc["energy"])
		if e < MAX_FAIL_ENERGY or e > MAX_GAIN_ENERGY:
			errors.append("%s: %s.energy %s is outside %d..%d" % [hw, key, str(e), int(MAX_FAIL_ENERGY), int(MAX_GAIN_ENERGY)])
		if key == "on_failure" and e > 0.0:
			errors.append("%s: a failure must not give energy" % hw)
	if oc.has("music") and str(oc["music"]) not in MUSIC:
		errors.append("%s: %s.music '%s' is not one of %s" % [hw, key, oc["music"], ", ".join(PackedStringArray(MUSIC))])
	if oc.has("cinematic"):
		var spec := resolve_cinematic(h, oc, named)
		if spec.is_empty():
			errors.append("%s: %s.cinematic '%s' does not resolve (name an entry of run.json cinematics, define the hotspot's cinematic, or give the outcome a cinematic object)" % [hw, key, str(oc["cinematic"])])
		else:
			for st in spec["steps"]:
				_validate_cine(st, "%s %s" % [hw, key], idx, errors)
	# failure never dead-ends: with no route the scene's default exit takes the player on (the engine's rule), and the energy cost is bounded above


static func _validate_cine(c: Dictionary, where: String, idx: Dictionary, errors: Array) -> void:
	for k in c:
		if str(k) not in CINEMATIC_KEYS:
			errors.append("%s: cinematic.%s is not a field (%s)" % [where, k, ", ".join(PackedStringArray(CINEMATIC_KEYS))])
	if c.has("move") and str(c["move"]) not in MOVES:
		errors.append("%s: cinematic.move '%s' is not one of %s" % [where, c["move"], ", ".join(PackedStringArray(MOVES))])
	if c.has("style") and str(c["style"]) not in RunRail.STYLES:
		errors.append("%s: cinematic.style '%s' is not one of %s" % [where, c["style"], ", ".join(PackedStringArray(RunRail.STYLES))])
	if c.has("role") and str(c["role"]) not in RunRail.ROLES:
		errors.append("%s: cinematic.role '%s' is not a role" % [where, c["role"]])
	if c.has("bars") and (float(c["bars"]) < RunRail.MOVE_BARS_MIN or float(c["bars"]) > RunRail.MOVE_BARS_MAX):
		errors.append("%s: cinematic.bars %s: moves last %d to %d bars" % [where, str(c["bars"]), int(RunRail.MOVE_BARS_MIN), int(RunRail.MOVE_BARS_MAX)])
	if bool(idx["ok"]):
		if c.has("to") and not (idx["waypoints"] as Dictionary).has(str(c["to"])):
			errors.append("%s: cinematic.to '%s' is not a waypoint of the map" % [where, c["to"]])
		if c.has("move") and not c.has("to"):
			errors.append("%s: cinematic.move needs cinematic.to" % where)
		if c.has("look_at"):
			var l := str(c["look_at"])
			if not ((idx["actors"] as Dictionary).has(l) or (idx["things"] as Dictionary).has(l) or (idx["waypoints"] as Dictionary).has(l)):
				errors.append("%s: cinematic.look_at '%s' is no actor, thing or waypoint of the map" % [where, l])
