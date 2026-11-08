class_name HotspotContract
extends RefCounted
## The hotspot data contract (docs/VISUAL_RHYTHM_ADVENTURE_PLAN.md section 2, docs/CONTINUOUS_RUN.md "Hotspots"): the field names, the allowed values and the validator both
## RunData (content/run/hotspots/<world>.json) and TrialData (content/trial/hotspots.json) call. Pure: it reads the map json (cached) and the context it is given, nothing else.
##
## A file is {"world": "<run world id | bassment>", "hotspots": [ hotspot, ... ]}; a hotspot (every field except id, scene, anchor, kind, on_success is optional):
##   id, world, scene (a run scene id, or a Bassment passage number), map, anchor, kind, radius_m (0.8), min_px (88, never less; the Bassment 72), available, look, challenge, on_success, on_failure,
##   cinematic, default, repeatable, window ("final" | "any"), on_select ({cinematic}), look.ring_m, pass_credit (0 to 1, with an activity), trial_kind (the Bassment's name for `kind`: when present it is one of KINDS and equals `kind`), acting (what a person does in each state of the hotspot and
##   after its outcome, docs/THREE_PATHS_AND_FACES_PLAN.md 2.3a: see validate_acting; a Bassment creature names a `figure` instead of an `actor`).
##
## The same family carries the other half of the acting contract, the `cast` lines of a scene node of run.json and of a cinematic (2.3b, 2.3c), validated by validate_cast.
##
## Defaults. A run scene's default is always an exit (the way on when nothing is tapped). The Bassment's passages have no such rule: a passage's default choice may be a fight, a luck test or
## an item, so TrialData passes ctx `default_any_kind` and the default may be any kind (it must still be unconditional). Failure semantics are not the contract's there: TrialFlow keeps them
## (a failed plain choice holds the place and becomes the default, a lost fight counts toward three, a luck miss goes its other way, and an outcome's `hold`, `lives`, `caption` and `on_defeat` are the
## Bassment's extras).

const KINDS := ["exit", "object", "character", "feature", "encounter", "secret"]
const ANCHORS := ["thing", "waypoint", "actor", "pos"]
const LOOK_AVAILABLE := ["glow", "pulse", "beckon", "flicker", "open", "crack"]
const LOOK_SELECTED := ["ring", "claim"]
const LOOK_COMMITTED := ["flash"]
const LOOK_FINISHED := ["crown"]  # look.finished.available: what a portal shows once its path has been finished (plan D10): the pulse ringed by three orbiting motes, in the finished tint
const FINISHED_TINT := "#ffd25a"
const WINDOWS := ["final", "any"]  # `window`: "any" (a hotspot with an activity) is on show and commits in every block of the phase
const FAMILIES := ["drums", "bass"]
const MIN_PX := 88.0  # the smallest touch target of a run choice in the 1280x720 design, both directions (lead ruling 3; INTERACTION_DESIGN.md 3.5)
const BASSMENT_MIN_PX := 72.0  # the Bassment keeps its own rules (lead ruling 20): TrialData passes it as ctx `min_px_floor`
const TOUCH_MARGIN_PX := 24.0  # a choice's touch region lies within its object's visual bounds grown by at most this (INTERACTION_DESIGN.md 3.6, T5a)
const MIN_PER_SCENE := 2
const MAX_PER_SCENE := 8  # choices available at once (lead ruling 1: reactive objects are a separate list and never count)
const MAX_PER_HUB := 10  # the most a scene's own `max_hotspots` may allow (lead ruling 16)
## Reactive objects (INTERACTION_DESIGN.md 2.1, 2.5; lead ruling 1): a file's `reactives` list beside `hotspots`. A reactive object reacts to a tap and leads nowhere: no route, no default, no
## outcome, never counted in the cap, never sent to the port. {id, scene, anchor (thing | actor | pos), reaction, touch? {w, h} metres, effect? {flags_set: per-run flags}} (assumption A5: cosmetic
## unless `effect` names a per-run flag). The reactions are drawn in code (HotspotView), no new art.
const REACTIONS := ["flare", "pulse", "shake", "squash"]
const REACTIVE_KEYS := ["id", "world", "scene", "map", "anchor", "reaction", "touch", "effect"]
const MAX_FAIL_ENERGY := -20.0  # a failure may cost at most this much energy (it must stay recoverable)
const MAX_GAIN_ENERGY := 20.0
const TRIAL_PREFIX := "trial:"  # a run route "trial:<passage>", or just "<passage>" ("1": the first), is the wizard's way into the Bassment
const PATH_PREFIX := "path:"  # a run route "path:<id>" is a portal into a sister run (content/paths/<id>/run.json) at its own tempo (docs/THREE_PATHS_AND_FACES_PLAN.md 3.3)
const RUN_PREFIX := "run:"  # a path ending's route "run:warehouse" leads back to the main run
const RUN_ROUTES := ["run:warehouse"]
const DUNGEON_ROUTE := "bassment"  # a run route "bassment" is a quest entrance into the Bassment taken at the lap's end (a hub's hatch, lead ruling 15; work package N2.2). Unlike the wizard's "trial:<n>" (the early
## window, mid-scene) it is a final-window choice; the passage it starts on is the narrative router's (the saved passage of an unfinished visit, else the first). RunPlay arms the dungeon at the lock.
## Test fixtures (work package N2.2): hotspot rows added to the content as it is read, {"main" | "<path id>": [row, ...]} (each row names its `world` and `scene`). RunData and NarrativeGraph read them
## beside the files; empty in the game. Only tests set this (tests/test_narrative_run.gd), and they clear it.
static var extra_rows: Dictionary = {}
const KEEP_PREFIX := "keep:"  # a flag name with this prefix is persistent (RunProgress.flags, saved); any other is per run (RunProgress.run_flags)
const OUTCOME_KEYS := ["route", "flags_set", "cinematic", "energy", "music", "pieces", "activity"]  # `pieces`: {on: [piece ids], off: [...]}, the map's set pieces a result switches (the storm goes, the tables fall); `activity`: a minigame the success sits the player into
const CINEMATIC_KEYS := ["move", "to", "bars", "look_at", "role", "style", "hold_bars"]  # hold_bars: a route leg's still hold after the move (CONTRACTS.md 3)
const MOVES := ["place", "walk", "stagger", "run", "climb", "carried"]  # `place` is a cut (the drag to the cage); the others are RunRail styles (`walk` with a `style`)
const MUSIC := ["variation", "dip", "lift", "drop", "fill", "none"]
## The acting contract. The faces and the directed acts are StoryCharacter's (the Stage 1a sheets bake exactly these); a story may also direct the older states (DIRECTABLE_OLD).
const FACES: Array = StoryCharacter.FACES
const ACTS: Array = StoryCharacter.ACTS + StoryCharacter.DIRECTABLE_OLD
const ACTING_PHASES := ["available", "selected", "committed", "success", "failure"]
const LOOK_TARGETS := ["camera", "actor", "thing", "waypoint"]  # `look_at` is the word camera, or the id of an actor (a home), a thing or a waypoint of the scene's map
const ACTING_KEYS := ["actor", "figure"]  # besides the phases
const ACT_KEYS := ["act", "face", "look_at", "beats", "then"]
const CAST_KEYS := ["actor", "at_beat", "act", "face", "look_at", "beats", "if_energy_below", "if_energy_above", "if_flags_all", "if_flags_none", "piece", "op", "hide"]
const PIECE_OPS := ["on", "off", "pulse"]  # a cast line with `piece` + `op` switches a set piece of the map (a thing with "piece": id) instead of directing a person; with `hide: true` it removes a person from the scene
const CAST_LAST_BEAT := 63.0  # a scene's cast line fires inside its own 64 beats
const CINE_CAST_LAST_BEAT := 16.0  # a cinematic's lines are relative to its start and run a few bars at most

static var _maps: Dictionary = {}  # map id -> index


## What a map offers anchors: {ok, waypoints: {id: true}, things: {id: true}, actors: {id: true}, sectors: [{poly: PackedVector2Array, floor: float}]}.
static func map_index(map_id: String) -> Dictionary:
	if _maps.has(map_id):
		return _maps[map_id]
	var idx := {"ok": false, "waypoints": {}, "things": {}, "actors": {}, "sectors": [], "pieces": {}}
	var path: String = StoryMap.path_of(map_id)
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path)) if FileAccess.file_exists(path) else null
	if typeof(parsed) == TYPE_DICTIONARY:
		idx["ok"] = true
		for w in parsed.get("waypoints", []):
			idx["waypoints"][str(w["id"])] = true
		for t in parsed.get("things", []):
			idx["things"][str(t["id"])] = true
			if t.has("piece"):
				idx["pieces"][str(t["piece"])] = true
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


## A run route "path:<id>" (the three portals of the Warehouse).
static func is_path_route(route: String) -> bool:
	return route.begins_with(PATH_PREFIX) and route.length() > PATH_PREFIX.length()


static func path_of(route: String) -> String:
	return route.trim_prefix(PATH_PREFIX) if is_path_route(route) else ""


## "run:warehouse": the way back from a path to the main run.
static func is_run_route(route: String) -> bool:
	return route in RUN_ROUTES


## "bassment": a hub's entrance into the Bassment, taken at the lap's end (not the wizard's mid-scene "trial:<n>").
static func is_dungeon_route(route: String) -> bool:
	return route == DUNGEON_ROUTE


## A route that enters or leaves a quest: a portal into a path, the hub's Bassment entrance, the way back to the main run. Such a choice is never gated by rhythm (lead ruling 15).
static func is_quest_route(route: String) -> bool:
	return is_path_route(route) or is_dungeon_route(route) or is_run_route(route)


## A route that is not a scene of the run that carries it: the Bassment, a path, or the way back.
static func is_special_route(route: String) -> bool:
	return is_trial_route(route) or is_path_route(route) or is_run_route(route) or is_dungeon_route(route)


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
	if typeof(lk.get("finished", null)) == TYPE_DICTIONARY:
		var fin: Dictionary = lk["finished"]
		fin["flags_any"] = fin.get("flags_any", [])
		fin["available"] = str(fin.get("available", "crown"))
		fin["tint"] = str(fin.get("tint", FINISHED_TINT))
	out["look"] = lk
	out["default"] = bool(out.get("default", false))
	out["repeatable"] = bool(out.get("repeatable", false))
	out["window"] = str(out.get("window", "final"))
	return out


## The cinematic an outcome names, as {"steps": [step, ...]} (a step: {move, to, bars, role, style, look_at}) plus {"cast": [line, ...], "world"} when a named cinematic has cast lines; {} when none or unresolved. The outcome's `cinematic` is a name looked up in `named`
## (run.json `cinematics`: name -> {world, steps}), else in the hotspot's own `cinematic` (one spec, which every name of the hotspot is, or a map name -> spec), or an object written inline.
static func resolve_cinematic(h: Dictionary, outcome: Dictionary, named: Dictionary = {}) -> Dictionary:
	if not outcome.has("cinematic"):
		return {}
	var c: Variant = outcome["cinematic"]
	if typeof(c) == TYPE_DICTIONARY:
		return c if (c as Dictionary).has("steps") else {"steps": [c]}
	if named.has(str(c)) and typeof(named[str(c)]) == TYPE_DICTIONARY and (named[str(c)] as Dictionary).has("steps"):
		var nm: Dictionary = named[str(c)]
		var res := {"steps": nm["steps"]}
		if nm.has("cast"):  # (only when it has some: a cinematic with no cast resolves exactly as before)
			res["cast"] = nm["cast"]
			res["world"] = str(nm.get("world", ""))
		return res
	var spec: Variant = h.get("cinematic", null)
	if typeof(spec) != TYPE_DICTIONARY:
		return {}
	for k in CINEMATIC_KEYS:
		if (spec as Dictionary).has(k):
			return {"steps": [spec]}
	var one: Variant = (spec as Dictionary).get(str(c), null)
	return {"steps": [one]} if typeof(one) == TYPE_DICTIONARY else {}


## Validates one scene's hotspot list. `ctx`: {where (a prefix for messages), map (map id), world, routes (Array of allowed route strings), start_energy, min_available (2), max_available (8), min_px_floor (88),
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
			if str(h.get("kind", "")) != "exit" and not bool(ctx.get("default_any_kind", false)):
				errors.append("%s: only an exit can be the default" % hw)
			elif not unconditional(h):
				errors.append("%s: the default must always be available (no flags_all, flags_none, energy_min or once)" % hw)
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
	if h.has("trial_kind") and (str(h["trial_kind"]) not in KINDS or str(h["trial_kind"]) != kind):
		errors.append("%s: trial_kind '%s' must be a kind and equal `kind` '%s'" % [hw, h["trial_kind"], kind])
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
	var floor_px := float(ctx.get("min_px_floor", MIN_PX))
	if float(h.get("min_px", MIN_PX)) < floor_px:
		errors.append("%s: min_px must be at least %d (a phone fingertip)" % [hw, int(floor_px)])
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
		if (lk as Dictionary).has("finished"):
			_validate_finished(lk["finished"], hw, errors)
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
		_validate_outcome(h, key, oc, hw, routes, idx, ctx.get("cinematics", {}), errors, ctx.get("activities", null))
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
	var has_act := typeof(h.get("on_success", null)) == TYPE_DICTIONARY and str((h["on_success"] as Dictionary).get("activity", "")) != ""
	if h.has("window") and (typeof(h["window"]) != TYPE_STRING or str(h["window"]) not in WINDOWS):
		errors.append("%s: window '%s' is not one of %s" % [hw, h["window"], ", ".join(PackedStringArray(WINDOWS))])
	elif str(h.get("window", "final")) == "any" and not has_act:
		errors.append("%s: window 'any' needs an on_success activity" % hw)
	if h.has("pass_credit"):
		var pc: Variant = h["pass_credit"]
		if (typeof(pc) != TYPE_FLOAT and typeof(pc) != TYPE_INT) or float(pc) < 0.0 or float(pc) > 1.0:
			errors.append("%s: pass_credit must be a number from 0 to 1" % hw)
		elif not has_act:
			errors.append("%s: pass_credit needs an on_success activity" % hw)
	if h.has("on_select"):  # the walk the touch itself starts: {cinematic: <name>} resolved like an outcome's
		var osel: Variant = h["on_select"]
		if typeof(osel) != TYPE_DICTIONARY or (osel as Dictionary).keys() != ["cinematic"]:
			errors.append("%s: on_select must be {cinematic: <name>}" % hw)
		else:
			var spec := resolve_cinematic(h, osel, ctx.get("cinematics", {}))
			if spec.is_empty():
				errors.append("%s: on_select.cinematic '%s' does not resolve" % [hw, str((osel as Dictionary)["cinematic"])])
			else:
				for st in spec["steps"]:
					_validate_cine(st, "%s on_select" % hw, idx, errors)
	if typeof(lk) == TYPE_DICTIONARY and (lk as Dictionary).has("ring_m"):  # the drawn floor ring's radius when it is not the touch radius
		var rm: Variant = lk["ring_m"]
		if (typeof(rm) != TYPE_FLOAT and typeof(rm) != TYPE_INT) or float(rm) <= 0.0 or float(rm) > 4.0:
			errors.append("%s: look.ring_m must be above 0 and at most 4" % hw)
	if typeof(h.get("default", false)) != TYPE_BOOL or typeof(h.get("repeatable", false)) != TYPE_BOOL:
		errors.append("%s: default and repeatable are true or false" % hw)
	if h.has("acting"):
		validate_acting(h, hw, idx, ctx, errors)
	if h.has("staging"):  # how the option shows it is the current choice or not (docs/CHOICE_CLARITY.md): ChoiceStaging
		ChoiceStaging.validate(h, hw, idx, errors)
	if h.has("show"):  # how the option shows its state with its own artwork (lead ruling 35b, contract 9): ChoiceShow
		ChoiceShow.validate(h, hw, idx, errors)


static func _validate_outcome(h: Dictionary, key: String, oc: Dictionary, hw: String, routes: Array, idx: Dictionary, named: Dictionary, errors: Array, ctx_activities: Variant = null) -> void:
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
	if oc.has("pieces"):
		validate_pieces(oc["pieces"], "%s: %s.pieces" % [hw, key], idx, errors)
	if oc.has("activity"):  # a minigame the success sits the player into (MinigameController): only on success, never with a route, an id the registry knows
		var act := str(oc["activity"]) if typeof(oc["activity"]) == TYPE_STRING else ""
		if act == "":
			errors.append("%s: %s.activity must be a non-empty string" % [hw, key])
		else:
			if key != "on_success":
				errors.append("%s: activity is only allowed in on_success" % hw)
			if route != "":
				errors.append("%s: %s.activity cannot be combined with a route" % [hw, key])
			if typeof(ctx_activities) == TYPE_ARRAY and act not in (ctx_activities as Array):
				errors.append("%s: %s.activity '%s' is not a registered minigame (%s)" % [hw, key, act, ", ".join(PackedStringArray(ctx_activities as Array))])
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


# --- reactive objects (INTERACTION_DESIGN.md 2.5) ------------------------------------------------------------------------------------

## A reactive object with every optional field filled in (a copy), shaped like a hotspot so that HotspotView.layout and hit place it the same way: kind "reactive", reactive true, a ring
## radius, min_px, a look, never a default, no outcome.
static func normalize_reactive(r: Dictionary, world: String, map_id: String) -> Dictionary:
	var out: Dictionary = r.duplicate(true)
	out["scene"] = str(out.get("scene", ""))
	out["world"] = str(out.get("world", world))
	out["map"] = str(out.get("map", map_id))
	out["kind"] = "reactive"
	out["reactive"] = true
	out["reaction"] = str(out.get("reaction", "flare"))
	out["radius_m"] = 0.6
	out["min_px"] = MIN_PX
	out["touch"] = (out.get("touch", {}) as Dictionary).duplicate() if typeof(out.get("touch", {})) == TYPE_DICTIONARY else {}
	out["effect"] = (out.get("effect", {}) as Dictionary).duplicate(true) if typeof(out.get("effect", {})) == TYPE_DICTIONARY else {}
	out["available"] = {"flags_all": [], "flags_none": [], "energy_min": 0.0, "once": false}
	out["look"] = {"available": "glow", "selected": "ring", "committed": "flash"}
	out["default"] = false
	out["repeatable"] = true
	out["window"] = "final"
	out["on_success"] = {}
	return out


## True for a reactive object (a normalised reactive row); a hotspot (a choice) never is one.
static func is_reactive(h: Dictionary) -> bool:
	return bool(h.get("reactive", false))


## Validates one scene's reactive list (the raw rows). `ctx`: {where, map, ids (the scene's hotspot ids: a reactive object may not reuse one)}. Appends to `errors`.
static func validate_reactives(list: Array, ctx: Dictionary, errors: Array) -> void:
	var where := str(ctx.get("where", "scene"))
	var map_id := str(ctx.get("map", ""))
	var idx := map_index(map_id)
	var taken: Dictionary = (ctx.get("ids", {}) as Dictionary).duplicate()
	for r in list:
		if typeof(r) != TYPE_DICTIONARY:
			errors.append("%s: a reactive object is not an object" % where)
			continue
		var rid := str(r.get("id", ""))
		var rw := "%s reactive %s" % [where, rid if rid != "" else "(no id)"]
		if rid == "" or taken.has(rid):
			errors.append("%s: id missing or duplicated (unique among the scene's hotspots and reactive objects)" % rw)
		taken[rid] = true
		for k in r:
			if str(k) not in REACTIVE_KEYS:
				errors.append("%s: '%s' is not a field (%s): a reactive object leads nowhere" % [rw, k, ", ".join(PackedStringArray(REACTIVE_KEYS))])
		if str(r.get("map", map_id)) != map_id:
			errors.append("%s: map '%s' is not the scene's map '%s'" % [rw, r.get("map", ""), map_id])
		var an: Variant = r.get("anchor", null)
		if typeof(an) != TYPE_DICTIONARY or (an as Dictionary).size() != 1 or str((an as Dictionary).keys()[0]) not in ["thing", "actor", "pos"]:
			errors.append("%s: anchor must be exactly one of {thing}, {actor}, {pos: [x, y, z]} (something drawn in the picture)" % rw)
		elif bool(idx["ok"]):
			var key := str((an as Dictionary).keys()[0])
			var val: Variant = an[key]
			if key == "thing" and not (idx["things"] as Dictionary).has(str(val)):
				errors.append("%s: anchor thing '%s' is not in map %s" % [rw, val, map_id])
			elif key == "actor" and not (idx["actors"] as Dictionary).has(str(val)):
				errors.append("%s: anchor actor '%s' has no home in map %s" % [rw, val, map_id])
			elif key == "pos" and (typeof(val) != TYPE_ARRAY or (val as Array).size() != 3):
				errors.append("%s: anchor pos must be [x, y, z]" % rw)
		if str(r.get("reaction", "")) not in REACTIONS:
			errors.append("%s: reaction '%s' is not one of %s" % [rw, r.get("reaction", ""), ", ".join(PackedStringArray(REACTIONS))])
		if r.has("touch"):
			var t: Variant = r["touch"]
			var ok := typeof(t) == TYPE_DICTIONARY
			if ok:
				for k in ["w", "h"]:
					var v: Variant = (t as Dictionary).get(k, 0.0)
					ok = ok and (typeof(v) == TYPE_FLOAT or typeof(v) == TYPE_INT) and float(v) > 0.0 and float(v) <= 6.0
			if not ok:
				errors.append("%s: touch must be {w, h} in metres, each above 0 and at most 6" % rw)
		if r.has("effect"):
			var e: Variant = r["effect"]
			var only_flags := typeof(e) == TYPE_DICTIONARY
			if only_flags:
				for k in (e as Dictionary):
					only_flags = only_flags and str(k) == "flags_set"
			if not only_flags:
				errors.append("%s: effect may only be {flags_set: [...]} (a reactive object never routes; assumption A5)" % rw)
			else:
				for f in (e as Dictionary).get("flags_set", []):
					if str(f) == "" or is_keep(str(f)):
						errors.append("%s: effect flag '%s' must be a per-run flag (not empty, not keep:)" % [rw, f])


# --- the acting contract (docs/THREE_PATHS_AND_FACES_PLAN.md 2.3) ----------------------------------------------------------------

## True when `target` is something a person can look at in the map `idx` (map_index): the word camera, an actor (a home), a thing or a waypoint.
## look.finished {flags_any, available?, tint?}: the look a hotspot takes once any of those persistent (keep:) flags is held (a portal whose path has been finished).
static func _validate_finished(fin: Variant, hw: String, errors: Array) -> void:
	if typeof(fin) != TYPE_DICTIONARY:
		errors.append("%s: look.finished must be an object" % hw)
		return
	var fl: Variant = (fin as Dictionary).get("flags_any", [])
	if typeof(fl) != TYPE_ARRAY or (fl as Array).is_empty():
		errors.append("%s: look.finished.flags_any must be a non-empty list" % hw)
	else:
		for f in fl:
			if not is_keep(str(f)):
				errors.append("%s: look.finished.flags_any '%s' must be a keep: flag (it outlives the run)" % [hw, f])
	var av := str((fin as Dictionary).get("available", "crown"))
	if av not in LOOK_FINISHED and av not in LOOK_AVAILABLE:
		errors.append("%s: look.finished.available '%s' is not one of %s" % [hw, av, ", ".join(PackedStringArray(LOOK_FINISHED + LOOK_AVAILABLE))])
	if not Color.html_is_valid(str((fin as Dictionary).get("tint", FINISHED_TINT))):
		errors.append("%s: look.finished.tint '%s' is not a colour" % [hw, (fin as Dictionary).get("tint")])


## Whether a hotspot shows its finished look: one of look.finished.flags_any is held (`has_flag`: Callable(String) -> bool).
static func finished_look(h: Dictionary, has_flag: Callable) -> bool:
	var fin: Variant = (h.get("look", {}) as Dictionary).get("finished", null)
	if typeof(fin) != TYPE_DICTIONARY or not has_flag.is_valid():
		return false
	for f in (fin as Dictionary).get("flags_any", []):
		if bool(has_flag.call(str(f))):
			return true
	return false


static func look_ok(target: String, idx: Dictionary) -> bool:
	if target == "camera":
		return true
	return (idx["actors"] as Dictionary).has(target) or (idx["things"] as Dictionary).has(target) or (idx["waypoints"] as Dictionary).has(target)


## One act with its face, look and hold: {act, face?, look_at?, beats?, then?}; `then` is another such object (what the person settles into).
static func _validate_act(spec: Variant, where: String, idx: Dictionary, errors: Array, depth := 0) -> void:
	if typeof(spec) != TYPE_DICTIONARY:
		errors.append("%s: must be an object {act, face, look_at, beats, then}" % where)
		return
	var sp: Dictionary = spec
	for k in sp:
		if str(k) not in ACT_KEYS:
			errors.append("%s: '%s' is not a field (%s)" % [where, k, ", ".join(PackedStringArray(ACT_KEYS))])
	if str(sp.get("act", "")) not in ACTS:
		errors.append("%s: act '%s' is not one of the acts" % [where, sp.get("act", "")])
	if sp.has("face") and str(sp["face"]) not in FACES:
		errors.append("%s: face '%s' is not one of the %d faces" % [where, sp["face"], FACES.size()])
	if sp.has("look_at") and bool(idx["ok"]) and not look_ok(str(sp["look_at"]), idx):
		errors.append("%s: look_at '%s' is not camera, nor an actor, thing or waypoint of the map" % [where, sp["look_at"]])
	if sp.has("beats") and (typeof(sp["beats"]) not in [TYPE_INT, TYPE_FLOAT] or float(sp["beats"]) <= 0.0 or float(sp["beats"]) > 64.0):
		errors.append("%s: beats must be a number above 0 and at most 64" % where)
	if sp.has("then"):
		if depth >= 3:
			errors.append("%s: `then` goes three deep at most" % where)
		else:
			_validate_act(sp["then"], where + " then", idx, errors, depth + 1)


## A hotspot's `acting` block: {actor?, figure?, available?, selected?, committed?, success?, failure?}. `actor` (default: the anchor's) is a person of the scene's map; a Bassment creature is named by
## `figure` instead (ctx `figures`, the creature kinds). A hotspot anchored on a thing with no actor named has nobody to direct, which is an error.
static func validate_acting(h: Dictionary, hw: String, idx: Dictionary, ctx: Dictionary, errors: Array) -> void:
	var a: Variant = h.get("acting", null)
	if typeof(a) != TYPE_DICTIONARY:
		errors.append("%s: acting must be an object" % hw)
		return
	var ac: Dictionary = a
	for k in ac:
		if str(k) not in ACTING_PHASES and str(k) not in ACTING_KEYS:
			errors.append("%s: acting.%s is not a field (%s)" % [hw, k, ", ".join(PackedStringArray(ACTING_PHASES + ACTING_KEYS))])
	var an: Variant = h.get("anchor", {})
	var anchor_actor := str((an as Dictionary).get("actor", "")) if typeof(an) == TYPE_DICTIONARY else ""
	if ac.has("figure"):
		if ac.has("actor"):
			errors.append("%s: acting names an actor or a figure, not both" % hw)
		if not (ctx.get("figures", []) as Array).has(str(ac["figure"])):
			errors.append("%s: acting.figure '%s' is not a creature here" % [hw, ac["figure"]])
	else:
		var who := str(ac.get("actor", anchor_actor))
		if who == "":
			errors.append("%s: acting needs an actor (the anchor is not one: name acting.actor)" % hw)
		elif bool(idx["ok"]) and not (idx["actors"] as Dictionary).has(who):
			errors.append("%s: acting.actor '%s' has no home in map %s" % [hw, who, ctx.get("map", "")])
	for ph in ACTING_PHASES:
		if ac.has(ph):
			_validate_act(ac[ph], "%s acting.%s" % [hw, ph], idx, errors)


## The `cast` lines of a scene node or a cinematic (plan 2.3b and 2.3c): [{actor, at_beat, act, face?, look_at?, beats?, if_energy_below?, if_energy_above?, if_flags_all?, if_flags_none?}]. `idx` is the
## map's map_index. `last_beat` is the latest beat a line may name (a scene's 63; a cinematic's lines are relative to its start).
## A set-piece switch {on: [ids], off: [ids]} (a scene node's `pieces`, a block effect's, an outcome's): every id is a piece thing of the map.
static func validate_pieces(spec: Variant, where: String, idx: Dictionary, errors: Array) -> void:
	if typeof(spec) != TYPE_DICTIONARY:
		errors.append("%s: must be {on: [...], off: [...]}" % where)
		return
	for k in spec:
		if str(k) not in ["on", "off"]:
			errors.append("%s: '%s' is not a field (on, off)" % [where, k])
		elif typeof(spec[k]) != TYPE_ARRAY:
			errors.append("%s: %s must be a list of piece ids" % [where, k])
		elif bool(idx["ok"]):
			for pid in spec[k]:
				if not (idx["pieces"] as Dictionary).has(str(pid)):
					errors.append("%s: %s '%s' is not a piece thing of the map" % [where, k, pid])


static func validate_cast(lines: Variant, where: String, idx: Dictionary, errors: Array, last_beat := CAST_LAST_BEAT) -> void:
	if typeof(lines) != TYPE_ARRAY:
		errors.append("%s: cast must be a list of lines" % where)
		return
	var i := 0
	for line in lines:
		var lw := "%s cast[%d]" % [where, i]
		i += 1
		if typeof(line) != TYPE_DICTIONARY:
			errors.append("%s: not an object" % lw)
			continue
		var ln: Dictionary = line
		for k in ln:
			if str(k) not in CAST_KEYS:
				errors.append("%s: '%s' is not a field (%s)" % [lw, k, ", ".join(PackedStringArray(CAST_KEYS))])
		var who := str(ln.get("actor", ""))
		var is_piece := ln.has("piece")
		var is_hide := bool(ln.get("hide", false))
		if is_piece:
			if who != "" or ln.has("act") or is_hide:
				errors.append("%s: a piece line has `piece` and `op` only (no actor, act or hide)" % lw)
			if str(ln.get("op", "")) not in PIECE_OPS:
				errors.append("%s: op must be one of %s" % [lw, ", ".join(PackedStringArray(PIECE_OPS))])
			if bool(idx["ok"]) and not (idx["pieces"] as Dictionary).has(str(ln["piece"])):
				errors.append("%s: piece '%s' is not a piece of the scene's map" % [lw, ln["piece"]])
		elif who == "":
			errors.append("%s: actor is required" % lw)
		elif bool(idx["ok"]) and not (idx["actors"] as Dictionary).has(who):
			errors.append("%s: actor '%s' has no home in the scene's map" % [lw, who])
		if not ln.has("at_beat") or typeof(ln["at_beat"]) not in [TYPE_INT, TYPE_FLOAT] or float(ln["at_beat"]) < 0.0 or float(ln["at_beat"]) > last_beat:
			errors.append("%s: at_beat must be a number from 0 to %d" % [lw, int(last_beat)])
		var spec := {}
		for k in ["act", "face", "look_at", "beats"]:
			if ln.has(k):
				spec[k] = ln[k]
		if not is_piece and not is_hide:
			_validate_act(spec, lw, idx, errors)
		for k in ["if_energy_below", "if_energy_above"]:
			if ln.has(k) and (typeof(ln[k]) not in [TYPE_INT, TYPE_FLOAT] or float(ln[k]) < 0.0 or float(ln[k]) > 100.0):
				errors.append("%s: %s must be a number from 0 to 100" % [lw, k])
		for k in ["if_flags_all", "if_flags_none"]:
			if ln.has(k):
				if typeof(ln[k]) != TYPE_ARRAY:
					errors.append("%s: %s must be a list of flags" % [lw, k])
				else:
					for f in ln[k]:
						if str(f) == "":
							errors.append("%s: %s holds an empty flag" % [lw, k])
