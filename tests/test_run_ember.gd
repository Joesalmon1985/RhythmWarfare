extends TestCase
## The Ember Road (docs/THREE_PATHS_AND_FACES_PLAN.md section 6, stage 5): the path's data (15 scenes at 145 BPM, five worlds on four maps, the relaxed graph rules, two endings and a setback), the flags
## that change later scenes (ember_no_vial, ember_warden_lost, ember_alone), the acting and cast of its people, the set-piece and hide cast lines it added to the acting contract, and the registry of
## the path's maps. The real scene is walked by tools/run/walk_run.sh --path ember.


func _data() -> RunData:
	var d := RunData.load_path("ember")
	assert_eq(d.errors, [], "the ember path validates")
	return d


func _flags(d: RunData, run_flags: Dictionary = {}) -> RunHotspots:
	return RunHotspots.new(d, run_flags, {})


## The cast events of one scene's phase from its downbeat, nobody touching anything (the cast does not depend on play).
func _cast_of(d: RunData, scene: String, run_flags: Dictionary = {}) -> Array:
	var e := RunEngine.new(d)
	e.hotspots = _flags(d, run_flags)
	e.begin(scene)
	var out: Array = []
	var t := 0.0
	var guard := 0
	while e.scene_index() < 2 and not e.over and guard < 40000:  # (the scene's laps: its cast lines count beats from its first downbeat)
		guard += 1
		e.energy = maxf(e.energy, 60.0)  # (nobody plays: two laps of misses would end the run, the cast does not depend on it)
		for ev in e.update(t):
			if str(ev["kind"]) == "cast":
				out.append(ev)
		t += 1.0 / 30.0
	return out


func _available_ids(d: RunData, rh: RunHotspots, scene: String) -> Array:
	return d.hotspots_of(scene).filter(func(h: Dictionary) -> bool: return rh.is_available(h)).map(func(h: Dictionary) -> String: return str(h["id"]))


func test_the_path_has_fifteen_scenes_at_145_bpm_in_five_worlds_on_four_maps() -> void:
	var d := _data()
	assert_eq(d.nodes.size(), 15)
	assert_eq(int(d.cfg["timing"]["bpm"]), 145)
	assert_eq(d.world_order, ["hollow", "north", "deeps", "marsh", "mountain"])
	var maps := {}
	for w in d.worlds:
		maps[str(d.worlds[w]["map"])] = true
	assert_eq(maps.keys(), ["orchard", "birch_hall", "deep_halls", "ash_land"])
	var codes: Array = []
	for id in d.node_order:
		codes.append(str(d.nodes[id]["blurb"]).substr(0, 3))
	assert_eq(codes, ["E00", "E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10", "E11", "E12", "E13", "E14"], "the plan's scene codes, in order")
	for id in d.nodes:
		assert_true(bool(d.nodes[id]["temporary"]), "%s plays a placeholder until the owner's loop lands" % id)
		assert_true(d.packs.has(str(d.nodes[id]["audio"])), "%s has its pack" % id)
		assert_eq(int(d.packs[str(d.nodes[id]["audio"])]["bpm"]), 145)


func test_two_endings_and_a_setback_with_their_flags() -> void:
	var d := _data()
	var ends := {}
	for id in d.nodes:
		if str(d.nodes[id]["ending"]) != "":
			ends[str(d.nodes[id]["ending"])] = id
	assert_eq(ends, {"quenched": "mountain.spring", "kept": "mountain.keeper"})
	for name in ends:
		var found := false
		for h in d.hotspots_of(str(ends[name])):
			if bool(h["default"]):
				found = (h["on_success"]["flags_set"] as Array).has("keep:path_ember_%s" % name)
		assert_true(found, "%s: the default exit sets keep:path_ember_%s" % [name, name])
	var taken_from: Array = []
	for id in d.nodes:
		for r in d.nodes[id]["next"]:
			if str(r["to"]) == "mountain.taken":
				taken_from.append(id)
	assert_eq(taken_from, ["deeps.falls", "marsh.wall", "marsh.stair", "marsh.plain"], "Taken is the setback of the horn, the gate, the stair and the plain")
	for r in d.nodes["mountain.taken"]["next"]:
		assert_true(bool(r["loop"]), "the way out of Taken goes back (a loop route)")
	var pool: Dictionary = d.hotspots_of("mountain.spring").filter(func(h: Dictionary) -> bool: return str(h["id"]).ends_with(".pool"))[0]
	assert_eq(str(pool["on_failure"]["route"]), "run:warehouse", "the snatched failure is the same ending reached another way")
	assert_eq(str(pool["on_failure"]["cinematic"]), "ember.snatched")
	assert_true((pool["on_failure"]["flags_set"] as Array).has("keep:path_ember_quenched"))


func test_every_scene_shows_two_to_four_things_and_every_person_you_touch_acts_in_five_states() -> void:
	var d := _data()
	for id in d.nodes:
		var n := 0
		for h in d.hotspots_of(str(id)):
			if HotspotContract.at_start(h, 60.0):
				n += 1
		assert_true(n >= 2 and n <= 4, "%s: %d hotspots at the start" % [id, n])
		assert_true((d.nodes[id]["cast"] as Array).size() >= 2, "%s has a cast" % id)
	var people := 0
	for id in d.nodes:
		for h in d.hotspots_of(str(id)):
			if str(h["kind"]) in ["character", "encounter"] and (h["anchor"] as Dictionary).has("actor"):
				people += 1
				assert_true(h.has("acting"), "%s acts" % h["id"])
				for ph in HotspotContract.ACTING_PHASES:
					assert_true((h["acting"] as Dictionary).has(ph), "%s: acting.%s" % [h["id"], ph])
	assert_eq(people, 7, "seven people to touch")


func test_the_flags_that_change_later_scenes() -> void:
	var d := _data()
	var set_by := {}
	for id in d.nodes:
		for h in d.hotspots_of(str(id)):
			for k in ["on_success", "on_failure"]:
				for f in (h.get(k, {}) as Dictionary).get("flags_set", []):
					set_by[str(f)] = str(h["id"]) + "." + k
	assert_eq(set_by["ember_no_vial"], "north.ladys_hand.on_failure", "the Lady withholds the vial on a failed touch")
	assert_eq(set_by["ember_warden_lost"], "deeps.lake.on_failure", "the Warden falls to the drowned thing")
	assert_eq(set_by["ember_alone"], "deeps.falls.boat.on_failure", "Bram's boat missed: you go on alone")
	var plain := _available_ids(d, _flags(d), "marsh.stair")
	var hard := _available_ids(d, _flags(d, {"ember_no_vial": true}), "marsh.stair")
	assert_true(plain.has("marsh.stair.bells") and not plain.has("marsh.stair.bells_hard"), "the vial given: the plain bells")
	assert_true(hard.has("marsh.stair.bells_hard") and not hard.has("marsh.stair.bells"), "no vial: the hard bells")
	var bh: Dictionary = d.hotspots_of("marsh.stair").filter(func(h: Dictionary) -> bool: return str(h["id"]).ends_with("bells_hard"))[0]
	assert_eq(str(bh["on_failure"]["route"]), "mountain.taken", "a failed hard bells is the setback")
	var horn_plain := _available_ids(d, _flags(d), "deeps.falls")
	var horn_lost := _available_ids(d, _flags(d, {"ember_warden_lost": true}), "deeps.falls")
	assert_true(horn_plain.has("deeps.falls.horn") and not horn_plain.has("deeps.falls.riders_horn"))
	assert_true(horn_lost.has("deeps.falls.riders_horn") and not horn_lost.has("deeps.falls.horn"), "the Warden lost: the horn is a rider's horn")


func test_a_scene_hides_the_people_the_flags_took_from_it_and_nobody_else() -> void:
	var d := _data()
	var plain := _cast_of(d, "north.pass")
	var lost := _cast_of(d, "north.pass", {"ember_warden_lost": true})
	var hides := func(log: Array) -> Array:
		return log.filter(func(c: Dictionary) -> bool: return bool(c["hide"])).map(func(c: Dictionary) -> String: return str(c["actor"]))
	assert_eq(hides.call(plain), [], "the Warden is in the pass while he lives")
	assert_eq(hides.call(lost), ["warden_p"], "and gone once he has fallen")
	assert_eq(hides.call(_cast_of(d, "marsh", {"ember_alone": true})), ["bram_m"], "alone: Bram is not in the marsh")
	assert_eq(hides.call(_cast_of(d, "marsh")), [])


func test_set_pieces_are_switched_by_cast_lines_at_their_beats() -> void:
	var d := _data()
	var sig := func(log: Array) -> Array:
		return log.filter(func(c: Dictionary) -> bool: return str(c["piece"]) != "").map(func(c: Dictionary) -> String: return "%s:%s:%d" % [c["piece"], c["op"], int(c["beat"])])
	assert_eq(sig.call(_cast_of(d, "marsh.wall")), ["gate_mouths:off:0", "gate_mouths:on:68"], "the gate's mouths open at beat 34 of the single phase: beat 68, early in the second lap")
	assert_eq(sig.call(_cast_of(d, "hollow.inn")), ["rider_shadow:on:112", "rider_shadow:off:125"], "a rider's shadow crosses the window (beat 48 and 61 of the last lap)")
	for c in _cast_of(d, "marsh.wall"):
		if str(c["piece"]) != "":
			assert_eq(str(c["actor"]), "", "a piece line directs nobody")


func test_the_validator_takes_piece_and_hide_lines_and_refuses_bad_ones() -> void:
	var idx := HotspotContract.map_index("ash_land")
	var errs: Array = []
	HotspotContract.validate_cast([{"piece": "gate_mouths", "op": "on", "at_beat": 4}, {"actor": "bram_m", "hide": true, "at_beat": 0, "if_flags_all": ["ember_alone"]}], "t", idx, errs)
	assert_eq(errs, [])
	for bad in [{"piece": "nope", "op": "on", "at_beat": 4}, {"piece": "gate_mouths", "op": "explode", "at_beat": 4}, {"piece": "gate_mouths", "op": "on", "at_beat": 4, "actor": "bram_m"}, {"hide": true, "at_beat": 0}]:
		var e2: Array = []
		HotspotContract.validate_cast([bad], "t", idx, e2)
		assert_false(e2.is_empty(), "refused: %s" % JSON.stringify(bad))


func test_the_worlds_name_their_story_files_and_the_maps_stay_out_of_the_chapter_menu() -> void:
	var c := StoryChapters.load_default()
	assert_eq(c.chapters.size(), 5, "the Story Campaign menu still shows its five chapters")
	var d := _data()
	for w in d.worlds:
		var m := str(d.worlds[w]["map"])
		assert_eq(str(d.worlds[w]["story"]), "res://content/story/%s.json" % m, "world %s names its story file" % w)
		assert_true(c.chapter(m).is_empty(), "%s is not a chapter" % m)
		var loaded := StoryData.load_file(str(d.worlds[w]["story"]))
		assert_eq(loaded["errors"], [], m)
		var map := StoryMap.load_chapter(m)
		assert_eq(map.errors, [], "%s map" % m)
		map.validate_chapter((loaded["data"] as StoryData).raw)
		assert_eq(map.errors, [], "%s chapter against its map" % m)


func test_every_person_the_story_names_stands_in_the_map_of_their_scene() -> void:
	var d := _data()
	for id in d.nodes:
		var idx := HotspotContract.map_index(str(d.nodes[id]["map"]))
		for line in d.nodes[id]["cast"]:
			if line.has("actor"):
				assert_true((idx["actors"] as Dictionary).has(str(line["actor"])), "%s: %s has a home" % [id, line["actor"]])


func test_the_bass_leads_the_placeholder_mix() -> void:
	var m: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://content/paths/ember/music.json"))
	var lv: Dictionary = m["placeholder"]["levels_db"]
	assert_eq(m["placeholder"]["genre"], "psytrance")
	assert_true(float(lv["bass"]) > float(lv["drums"]) + 6.0 and float(lv["bass"]) > float(lv["other"]) + 12.0, "the bass is clearly the loudest stem")
	for n in m["nodes"]:
		assert_true(bool(n["temporary"]))
		assert_true(str(n["prompt"]).begins_with("145 BPM"), "the owner's prompt rides on the scene")


# --- the real scene ---------------------------------------------------------------------------------------------------------------------------

const TMP_SAVE := "user://test_run_ember_save.json"
var _saved: RunProgress


func _scene(env: Dictionary, size := Vector2(844, 390)) -> Dictionary:
	_saved = Session.run_progress
	DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	for k in env:
		OS.set_environment(str(k), str(env[k]))
	Session.run_start_node = ""
	Session.run_start_path = ""
	var host := Control.new()
	host.size = size
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = size
	return {"host": host, "scene": scene}


func _free(d: Dictionary) -> void:
	if _saved != null:
		Session.run_progress = _saved
		_saved = null
	DirAccess.remove_absolute(TMP_SAVE)
	(d["host"] as Control).queue_free()
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_FLAGS", "RW_RUN_PORTAL", "RW_RUN_START", "RW_RUN_PATH", "RW_RUN_TAPS"]:
		OS.unset_environment(k)


func _run_until(scene: Node, t_end: float, stop: Callable) -> void:
	var t: float = scene._vt
	while t < t_end and not stop.call():
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func test_the_bar_portal_leads_into_the_ember_road_at_145_bpm() -> void:
	var d := _scene({"RW_RUN_FLAGS": "wh_vip_pass", "RW_RUN_PORTAL": "warehouse.bar.ember", "RW_RUN_START": "warehouse.bar", "RW_RUN_TAPS": "scripted"})
	var scene: Node = d["scene"]
	_run_until(scene, 120.0, func() -> bool: return scene.phase_log.size() >= 4)
	assert_eq(scene.path_log.size(), 1, "the portal was entered")
	assert_eq(scene.path_log[0]["path"], "ember")
	assert_near(float(scene.path_log[0]["beat_s_before"]), 60.0 / 174.0, 1e-12)
	assert_near(float(scene.path_log[0]["beat_s_after"]), 60.0 / 145.0, 1e-12)
	assert_eq(scene.phase_log.slice(0, 4).map(func(p: Dictionary) -> String: return "%s:%s" % [p["path"], p["node"]]), [":warehouse.bar", "ember:hollow", "ember:hollow.ford", "ember:hollow.inn"], "the Orchard, the Ford and the Inn in order")
	assert_true(scene.stages.has("orchard"), "the orchard's stage was built for the path")
	assert_true(Session.run_progress.path_world_reached("ember", "hollow"))
	assert_near(scene.engine.beat_s, 60.0 / 145.0, 1e-12)
	_free(d)


func test_an_ember_ending_sets_its_flag_and_leaves_to_the_warehouse() -> void:
	var d := _scene({"RW_RUN_PATH": "ember", "RW_RUN_START": "mountain.keeper", "RW_RUN_TAPS": "scripted"})
	var scene: Node = d["scene"]
	assert_eq(scene.run_path, "ember")
	_run_until(scene, 80.0, func() -> bool: return scene.path_log.size() >= 1)
	assert_eq(scene.path_log.size(), 1)
	assert_eq(scene.path_log[0]["kind"], "leave")
	assert_eq(scene.path_log[0]["ending"], "kept")
	assert_true(Session.run_progress.flags.has("keep:path_ember_kept"), "the Keeper's flag is saved")
	assert_eq(Session.run_progress.path_endings("ember"), ["kept"])
	assert_eq(scene.engine.node_id, "warehouse")
	_free(d)


func test_the_snatched_failure_of_the_pool_is_the_same_ending_with_its_cinematic() -> void:
	var d := _scene({"RW_RUN_PATH": "ember", "RW_RUN_START": "mountain.spring", "RW_RUN_BOT": "blocks:1110", "RW_RUN_SELECT": "mountain.spring.pool@52"})
	var scene: Node = d["scene"]
	_run_until(scene, 80.0, func() -> bool: return scene.path_log.size() >= 1)
	OS.unset_environment("RW_RUN_SELECT")
	assert_eq(scene.path_log.size(), 1, "the failed touch still leaves the path")
	assert_eq(scene.path_log[0]["ending"], "quenched", "the same ending reached another way")
	assert_true(Session.run_progress.flags.has("keep:path_ember_quenched"))
	var snatched: Array = scene.cast_log.filter(func(c: Dictionary) -> bool: return str(c.get("source", "")) == "cinematic")
	assert_true(snatched.size() >= 4, "the Hollow One and Bram act the cinematic (%d lines)" % snatched.size())
	assert_true(snatched.any(func(c: Dictionary) -> bool: return str(c.get("actor", "")) == "ho_s" and str(c.get("act", "")) == "collapse"), "the Hollow One falls in with it")
	_free(d)
