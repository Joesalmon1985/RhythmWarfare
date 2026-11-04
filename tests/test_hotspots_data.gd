extends TestCase
## The hotspot data contract: content/run/hotspots/<world>.json and content/trial/hotspots.json load, normalise and validate (HotspotContract). The shipped sample passes; each
## rule of the contract fails with a message that names the scene and the hotspot.

const TMP := "user://test_hotspots_data"


func _hs(extra: Dictionary = {}, id := "t1") -> Dictionary:
	var h := {"id": "warehouse.t." + id, "world": "warehouse", "scene": "warehouse", "map": "night_one", "anchor": {"waypoint": "to_bar"}, "kind": "exit", "on_success": {"route": "warehouse.bar"},
		"on_failure": {"route": "warehouse.balcony"}, "default": false}
	for k in extra:
		h[k] = extra[k]
	return h


func _good_list() -> Array:
	return [_hs({"default": true}, "a"), _hs({"anchor": {"waypoint": "to_balcony"}, "on_success": {"route": "warehouse.balcony"}, "on_failure": {"route": "warehouse.bar"}}, "b")]


func _load_with(list: Array, world := "warehouse") -> RunData:
	DirAccess.make_dir_recursive_absolute(TMP)
	var f := FileAccess.open(TMP + "/%s.json" % world, FileAccess.WRITE)
	f.store_string(JSON.stringify({"world": world, "hotspots": list}))
	f.close()
	return RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, TMP)


func _clean() -> void:
	for f in DirAccess.get_files_at(TMP):
		DirAccess.remove_absolute(TMP + "/" + f)


func _has_error(d: RunData, needle: String) -> bool:
	for e in d.errors:
		if str(e).contains(needle):
			return true
	return false


func test_the_shipped_data_is_valid_and_every_scene_has_one_default_exit() -> void:
	var d := RunData.load_default()
	assert_eq(d.errors, [], "no errors")
	assert_true(d.hotspots_authored.has("warehouse"), "the sample authors the Warehouse entry scene")
	for sid in d.node_order:
		var list: Array = d.hotspots_of(sid)
		assert_true(list.size() >= 1, "%s has hotspots" % sid)
		var defaults := 0
		for h in list:
			if bool(h["default"]):
				defaults += 1
		assert_eq(defaults, 1, "%s has exactly one default exit" % sid)
		if not d.hotspots_authored.has(sid):
			var routes: Array = (d.nodes[sid]["next"] as Array).map(func(e: Dictionary) -> String: return str(e["to"]))
			var got: Array = list.map(func(h: Dictionary) -> String: return str(h["on_success"]["route"]))
			assert_eq(got, routes, "%s: a made exit for every route, in order (the first is the default)" % sid)
			assert_true(bool(list[0]["default"]))


func test_a_hotspot_is_normalised_with_the_contract_defaults() -> void:
	var d := RunData.load_default()
	var h: Dictionary = d.hotspots_of("warehouse")[0]
	for k in ["id", "world", "scene", "map", "anchor", "kind", "radius_m", "min_px", "available", "look", "on_success", "default", "repeatable"]:
		assert_true(h.has(k), "has " + k)
	assert_eq(h["map"], "night_one")
	assert_true(float(h["min_px"]) >= 72.0)
	var dancer := (d.hotspots_of("warehouse") as Array).filter(func(x: Dictionary) -> bool: return str(x["id"]).ends_with("dancer"))[0] as Dictionary
	assert_eq(dancer["anchor"], {"actor": "c01"})
	assert_eq(dancer["available"]["flags_none"], ["danced_with"])


func test_a_good_authored_scene_passes() -> void:
	var d := _load_with(_good_list())
	assert_eq(d.errors, [], "a minimal good scene: two exits, one default")
	assert_true(d.hotspots_authored.has("warehouse"))
	_clean()


func test_the_two_to_four_rule_and_the_single_default() -> void:
	var d := _load_with([_hs({"default": true}, "a")])
	assert_true(_has_error(d, "1 hotspots are available at the start"), str(d.errors))
	var five: Array = []
	for i in 5:
		five.append(_hs({"default": i == 0, "anchor": {"waypoint": ["to_bar", "to_balcony", "floor_centre", "steps", "stage"][i]}}, "n%d" % i))
	d = _load_with(five)
	assert_true(_has_error(d, "5 hotspots are available at the start"), str(d.errors))
	var two_defaults := _good_list()
	two_defaults[1]["default"] = true
	d = _load_with(two_defaults)
	assert_true(_has_error(d, "exactly one default exit is needed (found 2)"), str(d.errors))
	var none := _good_list()
	none[0]["default"] = false
	d = _load_with(none)
	assert_true(_has_error(d, "(found 0)"), str(d.errors))
	_clean()


func test_a_conditional_hotspot_does_not_count_at_the_start_and_the_default_is_unconditional() -> void:
	var list := _good_list()
	list.append(_hs({"kind": "object", "anchor": {"thing": "bar_glow"}, "available": {"flags_all": ["bar_key"]}, "on_success": {"flags_set": ["x"]}}, "c"))
	var d := _load_with(list)
	assert_eq(d.errors, [], "a hotspot behind a flag is not in the 2 to 4 at the start")
	var cond := _good_list()
	cond[0]["available"] = {"energy_min": 70}
	d = _load_with(cond)
	assert_true(_has_error(d, "must always be available"), str(d.errors))
	_clean()


func test_routes_anchors_sizes_and_kinds_are_checked() -> void:
	var cases := [
		["route 'nowhere'", {"on_success": {"route": "nowhere"}}],
		["anchor thing 'no_such_thing'", {"anchor": {"thing": "no_such_thing"}}],
		["anchor waypoint 'no_wp'", {"anchor": {"waypoint": "no_wp"}}],
		["anchor actor 'zz9'", {"anchor": {"actor": "zz9"}}],
		["is not inside any sector", {"anchor": {"pos": [500.0, 1.0, 500.0]}}],
		["anchor must be exactly one of", {"anchor": {"thing": "bar_glow", "waypoint": "to_bar"}}],
		["min_px must be at least 72", {"min_px": 40}],
		["radius_m must be above 0", {"radius_m": 0}],
		["kind 'door' is not one of", {"kind": "door"}],
		["look.available 'sparkle'", {"look": {"available": "sparkle"}}],
		["challenge is null or", {"challenge": {"family": "synth", "tier": 2}}],
		["energy -50", {"on_failure": {"route": "warehouse.bar", "energy": -50}}],
		["a failure must not give energy", {"on_failure": {"route": "warehouse.bar", "energy": 5}}],
		["does not resolve", {"on_success": {"route": "warehouse.bar", "cinematic": "ghost"}}],
		["is not a field", {"on_success": {"route": "warehouse.bar", "teleport": true}}],
		["flags_set holds an empty flag", {"on_success": {"route": "warehouse.bar", "flags_set": [""]}}],
	]
	for c in cases:
		var list := _good_list()
		for k in c[1]:
			list[1][k] = c[1][k]
		var d := _load_with(list)
		assert_true(_has_error(d, str(c[0])), "'%s' is reported: %s" % [c[0], str(d.errors)])
		assert_true(_has_error(d, "warehouse.t.b"), "the message names the hotspot")
	_clean()


func test_a_cinematic_resolves_and_is_validated() -> void:
	var list := _good_list()
	list.append(_hs({"kind": "object", "anchor": {"thing": "bar_glow"}, "cinematic": {"move": "walk", "to": "bar_taps", "bars": 3, "look_at": "c01"}, "on_success": {"flags_set": ["drink"], "cinematic": "drink_at_bar", "energy": 6},
		"on_failure": {"cinematic": "spill", "energy": -8}}, "c"))
	var d := _load_with(list)
	assert_eq(d.errors, [], "one spec serves every named cinematic")
	var bad := list.duplicate(true)
	bad[2]["cinematic"] = {"move": "moonwalk", "to": "nowhere", "bars": 9, "look_at": "ghost"}
	d = _load_with(bad)
	for needle in ["cinematic.move 'moonwalk'", "cinematic.to 'nowhere'", "moves last 2 to 4 bars", "cinematic.look_at 'ghost'"]:
		assert_true(_has_error(d, needle), needle + " in " + str(d.errors))
	var named := list.duplicate(true)
	named[2]["cinematic"] = {"drink_at_bar": {"move": "walk", "to": "bar_taps"}}
	d = _load_with(named)
	assert_true(_has_error(d, "on_failure.cinematic 'spill' does not resolve"), "a named map must define every name used: " + str(d.errors))
	assert_false(_has_error(d, "drink_at_bar' does not resolve"))
	_clean()


func test_every_route_of_an_authored_scene_stays_reachable_and_the_wizard_needs_a_gate() -> void:
	var list := _good_list()
	list[0]["on_failure"] = {"route": "warehouse.bar"}
	list[1]["on_success"] = {"route": "warehouse.bar"}
	list[1]["on_failure"] = {"route": "warehouse.bar"}
	var d := _load_with(list)
	assert_true(_has_error(d, "the route 'warehouse.balcony' is not the outcome of any hotspot"), str(d.errors))
	var wiz := _good_list()
	wiz.append(_hs({"kind": "character", "anchor": {"waypoint": "hatch"}, "on_success": {"route": "trial:1"}, "on_failure": {"flags_set": ["shrug"]}}, "w"))
	d = _load_with(wiz)
	assert_eq(d.errors, [], "the warehouse floor has the trial gate")
	_clean()
	var other := _load_with([_hs({"scene": "warehouse.bar", "default": true, "on_success": {"route": "warehouse.chill"}, "on_failure": {"route": "warehouse.booth"}}, "o1"),
		_hs({"scene": "warehouse.bar", "on_success": {"route": "warehouse.booth"}, "on_failure": {"route": "warehouse.chill"}}, "o2"),
		_hs({"scene": "warehouse.bar", "kind": "character", "on_success": {"route": "trial:1"}}, "o3")])
	assert_true(_has_error(other, "only for a scene with a trial_gate"), str(other.errors))
	_clean()


func test_a_hotspot_for_another_scene_or_world_is_refused() -> void:
	var d := _load_with([_hs({"scene": "mothership.deck"}, "x")])
	assert_true(_has_error(d, "is not a scene of world warehouse"), str(d.errors))
	_clean()


# --- the Bassment ----------------------------------------------------------------------------------------------------------------

func _trial_load(list: Array) -> TrialData:
	DirAccess.make_dir_recursive_absolute(TMP)
	var f := FileAccess.open(TMP + "/trial_hotspots.json", FileAccess.WRITE)
	f.store_string(JSON.stringify({"world": "bassment", "hotspots": list}))
	f.close()
	var td := TrialData.load_default()
	td.errors.clear()
	td.hotspots.clear()
	td.load_hotspots(TMP + "/trial_hotspots.json")
	return td


func _th(extra: Dictionary = {}, id := "a") -> Dictionary:
	var h := {"id": "bassment.1." + id, "scene": "1", "map": "bassment_hatch", "anchor": {"waypoint": "ladder_top"}, "kind": "exit", "on_success": {"route": "3"}, "default": true}
	for k in extra:
		h[k] = extra[k]
	return h


func test_the_bassment_loads_passage_keyed_hotspots() -> void:
	var td := _trial_load([_th(), _th({"anchor": {"waypoint": "chalk_wall"}, "on_success": {"route": "2"}, "default": false}, "b")])
	assert_eq(td.errors, [], "passage 1: the ladder (the default) and the chalk")
	assert_eq(td.hotspots_of(1).size(), 2)
	assert_eq(td.hotspots_of(2).size(), 0, "a passage with none authored has none")
	assert_eq(td.hotspots_of(1)[0]["world"], "bassment")
	_clean()


func test_the_bassment_rules() -> void:
	var td := _trial_load([_th()])
	assert_true(td.errors.any(func(e: String) -> bool: return e.contains("the route '2' is not the outcome of any hotspot")), str(td.errors))
	td = _trial_load([_th({"on_success": {"route": "2"}}), _th({"anchor": {"waypoint": "chalk_wall"}, "on_success": {"route": "3"}, "default": false}, "b")])
	assert_true(td.errors.any(func(e: String) -> bool: return e.contains("the default exit leads to '2', the scene's default route is '3'")), str(td.errors))
	td = _trial_load([_th({"scene": "9999"})])
	assert_true(td.errors.any(func(e: String) -> bool: return e.contains("is not a passage")), str(td.errors))
	td = _trial_load([_th({"on_success": {"route": "44"}})])
	assert_true(td.errors.any(func(e: String) -> bool: return e.contains("route '44' is not a route of the scene")), str(td.errors))
	td = _trial_load([_th({"anchor": {"waypoint": "nowhere"}})])
	assert_true(td.errors.any(func(e: String) -> bool: return e.contains("anchor waypoint 'nowhere'")), str(td.errors))
	_clean()


func test_the_shipped_bassment_data_still_loads() -> void:
	var td := TrialData.load_default()
	assert_eq(td.errors, [])
