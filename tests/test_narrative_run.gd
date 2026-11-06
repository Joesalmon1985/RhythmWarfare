extends TestCase
## Work package N2.2: the quest router in the REAL run scene (RunPlay on its virtual clock, the real TransitionDirector, the real engine, the real save code), docs/narrative/N2_2_ROUTER.md.
## The owner's three illustrative routes of NARRATIVE_GRAPH.md section 4 (route 2 in ruling 18's walkable order), with the route state and the save checked at every step; quest progress kept
## across leaving and entering again; the save reloaded mid-route gives the same continuation; an entry honoured after a missed block; a changed mind before the lock leaves the state untouched;
## an old save migrates; a "keep:" flag is saved at `switched`, not at the lock; the Bassment entered at a lap's end from a hub and left to that hub.
##
## FIXTURES (nothing of this is game content): the hubs outside the Warehouse have no quest entrances yet (N2.4) and the paths no return objects (N2.5). HotspotContract.extra_rows adds, for these
## tests only, an ungated entrance for each quest to the hub of each of the four other locations (ids as in content/narrative/graph.json: hospital.enter_gospel, ...), the Floor's hatch
## warehouse.enter_bassment, and a return object <quest>.return to every authored path scene. They carry the per-run flag fx_n22 (set by the test) only so that the hubs' data cap of choices at the
## start is not exceeded by four extra rows; it is no rhythm gate.

const TMP_SAVE := "user://test_narrative_run_save.json"
const FX_FLAG := "fx_n22"
const STEP := 1.0 / 30.0

var _saved: RunProgress
var _violations: Array = []  # route state changes not reported as a switch or a Bassment commit


# --- fixtures -------------------------------------------------------------------------------------------------------------

static func _anchor_of(d: RunData, sid: String) -> Dictionary:
	for h in d.hotspots_of(sid):
		var a: Variant = h.get("anchor", null)
		if typeof(a) == TYPE_DICTIONARY and not (a as Dictionary).is_empty():
			return (a as Dictionary).duplicate(true)
	return {}


static func _entrance_row(id: String, world: String, scene: String, anchor: Dictionary, route: String) -> Dictionary:
	return {"id": id, "world": world, "scene": scene, "anchor": anchor, "kind": "secret", "look": {"available": "pulse"}, "available": {"flags_all": [FX_FLAG]},
		"on_success": {"route": route}, "on_failure": {"energy": -4}, "repeatable": true}


static func fixture_rows() -> Dictionary:
	var main := RunData.load_default()
	var rows := {"main": []}
	for hub in ["hospital", "ward", "mothership", "underworld"]:
		var w := str(main.nodes[hub]["world"])
		for q in ["bassment", "gospel", "squadron", "ember"]:
			rows["main"].append(_entrance_row("%s.enter_%s" % [hub, q], w, hub, _anchor_of(main, hub), "bassment" if q == "bassment" else "path:" + q))
	rows["main"].append(_entrance_row("warehouse.enter_bassment", "warehouse", "warehouse", _anchor_of(main, "warehouse.bar"), "bassment"))
	rows["main"].back()["anchor"] = _anchor_of(main, "warehouse")
	for p in ["gospel", "squadron", "ember"]:
		var pd := RunData.load_path(p)
		rows[p] = []
		for sid in pd.node_order:
			if not pd.hotspots_authored.has(sid):
				continue
			rows[p].append({"id": "%s.return" % p, "world": str(pd.nodes[sid]["world"]), "scene": sid, "anchor": _anchor_of(pd, sid), "kind": "exit",
				"available": {"flags_all": [FX_FLAG]}, "on_success": {"route": "run:warehouse"}})
	return rows


func _fixtures_on() -> void:
	HotspotContract.extra_rows = {}
	HotspotContract.extra_rows = fixture_rows()
	NarrativeGraph.clear_cache()


func _fixtures_off() -> void:
	HotspotContract.extra_rows = {}
	NarrativeGraph.clear_cache()


# --- the scene ------------------------------------------------------------------------------------------------------------

func _rm(p: String) -> void:
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(p)


func _scene(env: Dictionary = {}, save_text: String = "", keep_save := false) -> Dictionary:
	if _saved == null:
		_saved = Session.run_progress
	if not keep_save:
		_rm(TMP_SAVE)
		_rm(TMP_SAVE + ".tmp")
		if save_text != "":
			var f := FileAccess.open(TMP_SAVE, FileAccess.WRITE)
			f.store_string(save_text)
			f.close()
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	var base := {"RW_RUN_VIRTUAL": "1", "RW_RUN_BOT": "perfect", "RW_RUN_ROUTES": "", "RW_RUN_TAPS": "none", "RW_RUN_FLAGS": FX_FLAG}
	for k in env:
		base[k] = env[k]
	for k in base:
		OS.set_environment(k, str(base[k]))
	Session.run_start_node = ""
	Session.run_start_path = ""
	var host := Control.new()
	host.size = Vector2(1280, 720)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = host.size
	_violations = []
	return {"host": host, "scene": scene, "env": base.keys()}


func _free(d: Dictionary, keep_save := false) -> void:
	(d["host"] as Control).queue_free()
	for k in d["env"]:
		OS.unset_environment(str(k))
	for k in ["RW_RUN_START", "RW_RUN_PATH"]:
		OS.unset_environment(k)
	if not keep_save:
		Session.run_progress = _saved
		_saved = null
		_rm(TMP_SAVE)


func _snap(scene: Node) -> String:
	return (scene.router as QuestRouter).state.snapshot()


## Steps the scene until `cond` holds (or `max_s` of song time). Every change of the committed route state must come with a route_log entry of a switch or a Bassment commit.
func _until(scene: Node, cond: Callable, max_s := 120.0) -> bool:
	var t_end: float = scene._vt + max_s
	var snap := _snap(scene)
	var logs: int = (scene.route_log as Array).size()
	while scene._vt < t_end:
		if cond.call():
			return true
		scene._vt += STEP
		scene._step_virtual(scene._vt)
		var now := _snap(scene)
		if now != snap:
			var new_logs: Array = (scene.route_log as Array).slice(logs)
			if new_logs.is_empty() or not new_logs.all(func(e: Dictionary) -> bool: return str(e["kind"]) in ["switched", "bassment_enter", "bassment_passage", "bassment_leave"]):
				_violations.append("t=%.2f: the route state changed without a switch: %s" % [scene._vt, str(new_logs)])
			snap = now
		logs = (scene.route_log as Array).size()
	return cond.call()


func _at(scene: Node, path: String, node: String) -> bool:
	return scene.trial_state == "" and scene.run_path == path and scene.engine.node_id == node


func _st(scene: Node) -> RouteState:
	return (scene.router as QuestRouter).state


## The `narrative` key of the save file on disk, compared with the committed state (both read through JSON, so whole numbers compare equal).
func _disk_matches(scene: Node, what: String) -> void:
	var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(TMP_SAVE))
	assert_true(typeof(v) == TYPE_DICTIONARY and (v as Dictionary).has("narrative"), "%s: the save has a narrative key" % what)
	if typeof(v) != TYPE_DICTIONARY:
		return
	var disk: Dictionary = (v as Dictionary).get("narrative", {})
	assert_eq(int(disk.get("version", 0)), RouteState.VERSION, "%s: the narrative key is versioned" % what)
	assert_eq(int((v as Dictionary).get("version", 0)), RunProgress.VERSION, "%s: the file's own version is unchanged" % what)
	assert_eq(JSON.stringify(disk, "", true), JSON.stringify(JSON.parse_string(_snap(scene)), "", true), "%s: the save on disk is the committed route state" % what)
	assert_false(FileAccess.file_exists(TMP_SAVE + ".tmp"), "%s: no temporary file is left (written, then renamed)" % what)


## Touches `id` once selection is open and it is on show (a final-window choice: from the scene's first beat). True when it was selected.
func _pick(scene: Node, id: String) -> bool:
	var ok := _until(scene, func() -> bool: return scene.selection_open() and scene.hotspots.is_shown(id, scene.engine.block, true) and scene.engine.phase_beat_at(scene._vt) > 1.0, 60.0)
	if not ok:
		return false
	return scene.hotspot_select(id)


## Takes the room's exit to `to` (a scene of the same run) and waits for it.
func _go(scene: Node, to: String, path := "") -> bool:
	var ok := _until(scene, func() -> bool: return scene.selection_open() and scene.engine.phase_beat_at(scene._vt) > 1.0, 60.0)
	if not ok:
		return false
	var hid := ""
	for h in scene.hotspots.shown(scene.engine.block, true):
		if RunHotspots.window_of(h) == "final" and str((h["on_success"] as Dictionary).get("route", "")) == to:
			hid = str(h["id"])
			break
	if hid == "" or not scene.hotspot_select(hid):
		return false
	return _until(scene, func() -> bool: return _at(scene, path, to), 200.0)


func _progress(scene: Node, q: String) -> Dictionary:
	return _st(scene).progress_of(q)


# --- the three routes ------------------------------------------------------------------------------------------------------

## Route 1 (NARRATIVE_GRAPH.md 4.1): the wizard into the Bassment, a passage, the way out to the Floor; eight mainline choices to the Hospital Ward; its Gospel entrance, a scene, the return.
func test_route_1_warehouse_bassment_then_hospital_gospel() -> void:
	_fixtures_on()
	var d := _scene()
	var sc: Node = d["scene"]
	assert_true(sc.router != null, "the router runs in the game")
	assert_eq(_st(sc).location, "warehouse_rave")
	assert_eq(_st(sc).history, ["main/warehouse"])
	_disk_matches(sc, "step 1, a new run")
	# 2. the wizard (legacy, mid-scene): committed when the trial begins
	assert_true(_until(sc, func() -> bool: return sc.selection_open() and sc.engine.block == 0 and sc.engine.phase_beat_at(sc._vt) > 1.0, 20.0))
	var before := _snap(sc)
	assert_true(sc.hotspot_select("warehouse.wizard"), "the wizard is touched in block 1")
	assert_eq(sc.choice_request_id, 0, "the wizard is not sent to the port (ruling 15: outside the port)")
	assert_eq(_snap(sc), before, "a touch changes nothing committed")
	assert_true(_until(sc, func() -> bool: return sc.trial_state == "in", 30.0), "the wizard takes the run into the Bassment")
	assert_eq(_st(sc).quest, "bassment")
	assert_eq(_st(sc).entry_origin, "main/warehouse")
	assert_eq(_st(sc).checkpoint, "main/warehouse")
	assert_eq(_st(sc).current_scene(), "bassment/1")
	assert_eq(int(_progress(sc, "bassment")["visits"]), 1)
	assert_eq(str(sc.route_log.filter(func(e: Dictionary) -> bool: return e["kind"] == "bassment_enter")[0]["way"]), "legacy")
	_disk_matches(sc, "step 2, the wizard")
	# 3. passage 1: down the ladder (the default, played by the trial's bot)
	assert_true(_until(sc, func() -> bool: return sc.trial.engine.flow.passage == 3, 60.0), "passage 3 reached")
	sc._step_virtual(sc._vt)
	assert_eq(_st(sc).current_scene(), "bassment/3")
	assert_eq(str(_progress(sc, "bassment")["scene"]), "bassment/3")
	_disk_matches(sc, "step 3, passage 3")
	# 4. the way out (the back key: the Bassment's visible return object is N2.5's) lands on the checkpoint
	sc.trial.request_leave()
	assert_true(_until(sc, func() -> bool: return _at(sc, "", "warehouse"), 60.0), "back on the Floor")
	assert_eq(_st(sc).quest, "")
	assert_eq(_st(sc).entry_origin, "")
	assert_eq(_st(sc).checkpoint, "")
	assert_eq(str(_progress(sc, "bassment")["scene"]), "bassment/3", "the passage left is kept")
	assert_eq(_st(sc).current_scene(), "main/warehouse")
	_disk_matches(sc, "step 4, out of the Bassment")
	# 5 to 12: eight mainline choices
	for to in ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "hospital"]:
		assert_true(_go(sc, to), "mainline: %s" % to)
		assert_eq(_st(sc).current_scene(), "main/" + to)
	assert_eq(_st(sc).location, "hospital_ward")
	_disk_matches(sc, "step 12, the Hospital Ward hub")
	# 13: the figure of light at the Hospital Ward hub
	before = _snap(sc)
	assert_true(_pick(sc, "hospital.enter_gospel"))
	assert_true(sc.choice_request_id > 0, "the entrance is a port request")
	assert_eq(str(_st(sc).pending["dest"]["kind"]), "quest_entry")
	assert_false((_st(sc).pending["dest"] as Dictionary).has("on_miss"), "a quest entry has no miss route")
	assert_eq(_snap(sc), before, "requested: nothing committed yet")
	assert_true(_until(sc, func() -> bool: return _at(sc, "gospel", "jordan"), 60.0), "the run enters the Gospel at its first scene")
	assert_eq(_st(sc).quest, "gospel")
	assert_eq(_st(sc).entry_origin, "main/hospital")
	assert_eq(_st(sc).checkpoint, "main/hospital")
	assert_eq(_st(sc).location, "hospital_ward", "the location does not change in a quest")
	assert_eq(int(_progress(sc, "gospel")["visits"]), 1)
	_disk_matches(sc, "step 13, into the Gospel")
	# 14: follows the road
	assert_true(_go(sc, "jordan.baptism", "gospel"))
	assert_eq(_st(sc).current_scene(), "gospel/jordan.baptism")
	# 15: the return object lands on the hub the player came from
	assert_true(_pick(sc, "gospel.return"))
	assert_eq(str(_st(sc).pending["dest"]["id"]), "main/hospital", "a return is aimed at the checkpoint")
	assert_true(_until(sc, func() -> bool: return _at(sc, "", "hospital"), 120.0), "back on the Hospital Ward hub")
	var st := _st(sc)
	assert_eq([st.location, st.quest, st.entry_origin, st.checkpoint], ["hospital_ward", "", "", ""])
	assert_eq(str(_progress(sc, "gospel")["scene"]), "gospel/jordan.baptism")
	assert_eq(int(_progress(sc, "bassment")["visits"]), 1)
	assert_eq(str(_progress(sc, "bassment")["scene"]), "bassment/3")
	assert_eq(st.history, ["main/warehouse", "bassment/1", "bassment/3", "main/warehouse", "main/warehouse.bar", "main/warehouse.chill", "main/warehouse.exit", "main/mothership",
		"main/mothership.gallery", "main/mothership.bridge", "main/mothership.exit", "main/hospital", "gospel/jordan", "gospel/jordan.baptism", "main/hospital"], "the history of NARRATIVE_GRAPH.md 3.3")
	_disk_matches(sc, "step 15, the end of route 1")
	assert_eq(_violations, [], "the route state changed only at a switch (or a Bassment commit)")
	assert_eq(sc.router.errors, [])
	_free(d)
	_fixtures_off()


## Route 2 in ruling 18's walkable order: Alien Spaceship, the Ember and back; the Mental Hospital, the Squadron, back, and in again (it resumes). The save is reloaded mid-route.
func test_route_2_alien_ember_then_mental_hospital_squadron_and_in_again() -> void:
	_fixtures_on()
	var d := _scene()
	var sc: Node = d["scene"]
	for to in ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership"]:
		assert_true(_go(sc, to), "mainline: %s" % to)
	assert_eq(_st(sc).location, "alien_spaceship")
	# 5 to 7: the ember in the jar, the orchard gate, the return
	assert_true(_pick(sc, "mothership.enter_ember"))
	assert_true(_until(sc, func() -> bool: return _at(sc, "ember", "hollow"), 60.0))
	assert_eq([_st(sc).quest, _st(sc).entry_origin, _st(sc).checkpoint], ["ember", "main/mothership", "main/mothership"])
	assert_true(_go(sc, "hollow.ford", "ember"))
	assert_true(_pick(sc, "ember.return"))
	assert_true(_until(sc, func() -> bool: return _at(sc, "", "mothership"), 120.0), "back on the Alien Spaceship hub")
	assert_eq(str(_progress(sc, "ember")["scene"]), "ember/hollow.ford")
	assert_eq(_st(sc).quest, "")
	_disk_matches(sc, "step 7")
	# THE SAVE RELOADED MID-ROUTE: a fresh run on this save continues the same way (the Ember resumes at the Ford)
	var text := FileAccess.get_file_as_string(TMP_SAVE)
	var reload := RunProgress.load_data(TMP_SAVE, "user://none.json")
	var r2 := QuestRouter.new(sc.router.graph, NarrativeRunStore.new(reload))
	r2.load_state(NarrativeRunStore.new(reload).extra())
	assert_eq(r2.state.snapshot(), _snap(sc), "the reloaded route state is the committed one")
	assert_eq(str(r2.destination_for("mothership.enter_ember", "main/mothership").get("id", "")), "ember/hollow.ford", "and entering the Ember again resumes at the Ford")
	assert_eq(FileAccess.get_file_as_string(TMP_SAVE), text, "reading the save writes nothing")
	# 8 to 11: on to the Mental Hospital (the airlock's other door)
	for to in ["mothership.gallery", "mothership.bridge", "mothership.exit", "ward"]:
		assert_true(_go(sc, to), "mainline: %s" % to)
	assert_eq(_st(sc).location, "mental_hospital")
	# 12 to 14: the radio, the cot, the return
	assert_true(_pick(sc, "ward.enter_squadron"))
	assert_true(_until(sc, func() -> bool: return _at(sc, "squadron", "base"), 60.0))
	assert_eq([_st(sc).quest, _st(sc).entry_origin, _st(sc).checkpoint], ["squadron", "main/ward", "main/ward"])
	assert_true(_go(sc, "base.c03", "squadron"))
	assert_true(_pick(sc, "squadron.return"))
	assert_true(_until(sc, func() -> bool: return _at(sc, "", "ward"), 120.0), "back on the Mental Hospital hub")
	assert_eq(str(_progress(sc, "squadron")["scene"]), "squadron/base.c03")
	_disk_matches(sc, "step 14")
	# 15: the radio again: the saved scene, not the Briefing Room
	assert_true(_pick(sc, "ward.enter_squadron"))
	assert_eq(str(_st(sc).pending["dest"]["id"]), "squadron/base.c03")
	assert_true(_until(sc, func() -> bool: return _at(sc, "squadron", "base.c03"), 60.0), "it resumes at the scene left")
	assert_eq(int(_progress(sc, "squadron")["visits"]), 2)
	assert_eq(str(_progress(sc, "ember")["scene"]), "ember/hollow.ford", "the Ember is still unfinished, with its saved scene")
	assert_eq(_st(sc).checkpoint, "main/ward")
	_disk_matches(sc, "step 15")
	assert_eq(_violations, [])
	assert_eq(sc.router.errors, [])
	_free(d)
	_fixtures_off()


## Route 3: Hell to the Bassment by the hub's hatch (at the lap's end) and back; the figure of light, a change of mind before the lock, then in; the return at once; in again.
func test_route_3_hell_bassment_then_gospel_with_a_change_of_mind() -> void:
	_fixtures_on()
	var d := _scene()
	var sc: Node = d["scene"]
	for to in ["warehouse.bar", "warehouse.chill", "warehouse.exit", "underworld"]:
		assert_true(_go(sc, to), "mainline: %s" % to)
	assert_eq(_st(sc).location, "hell")
	# 5: the trapdoor: held by the run (the port does not carry the Bassment), armed at the lock, entered on the boundary
	var before := _snap(sc)
	assert_true(_pick(sc, "underworld.enter_bassment"))
	assert_eq(sc.choice_request_id, 0, "the Bassment entrance is not sent to the port (ruling 20)")
	assert_eq(_snap(sc), before)
	var boundary: float = sc.engine.scene_t0 + float(sc.engine.laps) * 64.0 * sc.engine.beat_s
	assert_true(_until(sc, func() -> bool: return sc.trial_state == "in", 60.0), "the hatch takes the run into the Bassment")
	assert_near(float(sc.trial_entry_t), boundary, 1e-6, "on the scene's boundary (the lap's end), not mid-scene")
	var armed: Array = sc.trial_log.filter(func(e: Dictionary) -> bool: return e["kind"] == "armed")
	assert_eq(str(armed.back()["way"]), "hatch")
	assert_true(float(armed.back()["beat"]) >= 60.0, "armed at the lock (beat %.2f)" % float(armed.back()["beat"]))
	assert_eq([_st(sc).quest, _st(sc).entry_origin, _st(sc).checkpoint, _st(sc).current_scene()], ["bassment", "main/underworld", "main/underworld", "bassment/1"])
	assert_eq(sc.director.lock_log.filter(func(e: Dictionary) -> bool: return str(e["dest"]).begins_with("bassment")), [], "the director locked nothing for it")
	# 6, 7: the ladder, the way out to the Hell hub
	assert_true(_until(sc, func() -> bool: return sc.trial.engine.flow.passage == 3, 60.0))
	sc.trial.request_leave()
	assert_true(_until(sc, func() -> bool: return _at(sc, "", "underworld"), 60.0), "the way out lands on the checkpoint, the Hell hub")
	assert_eq(str(_progress(sc, "bassment")["scene"]), "bassment/3")
	assert_eq(_st(sc).quest, "")
	_disk_matches(sc, "step 7")
	# 8: the figure of light, then a change of mind before the lock (deselect: the request is cancelled)
	before = _snap(sc)
	var disk_before := FileAccess.get_file_as_string(TMP_SAVE)
	assert_true(_pick(sc, "underworld.enter_gospel"))
	var rid: int = sc.choice_request_id
	assert_true(rid > 0)
	assert_true(sc.hotspot_deselect("underworld.enter_gospel"), "the player withdraws the pick before the lock")
	assert_true(sc.director.log.any(func(e: Dictionary) -> bool: return e["signal"] == &"request_closed" and int(e["args"][0]) == rid and e["args"][1] == &"cancelled"))
	assert_true(_st(sc).pending.is_empty(), "the router discarded the held change")
	assert_eq(_snap(sc), before, "committed state byte for byte as after step 7")
	assert_eq(FileAccess.get_file_as_string(TMP_SAVE), disk_before, "and nothing was written")
	# a replaced pick too: the figure, then the radio, then the figure again; only the last one goes
	assert_true(_pick(sc, "underworld.enter_gospel"))
	assert_true(_pick(sc, "underworld.enter_squadron"))
	assert_eq(_snap(sc), before)
	# 9: the figure of light again
	assert_true(_pick(sc, "underworld.enter_gospel"))
	assert_true(_until(sc, func() -> bool: return _at(sc, "gospel", "jordan"), 60.0))
	assert_eq([_st(sc).quest, _st(sc).entry_origin, _st(sc).checkpoint], ["gospel", "main/underworld", "main/underworld"])
	assert_eq(int(_progress(sc, "squadron")["visits"]), 0, "the replaced radio entered nothing")
	# 10: the return at once
	assert_true(_pick(sc, "gospel.return"))
	assert_true(_until(sc, func() -> bool: return _at(sc, "", "underworld"), 120.0))
	assert_eq(str(_progress(sc, "gospel")["scene"]), "gospel/jordan")
	# 11: in again: the saved scene is the first one, visits 2
	assert_true(_pick(sc, "underworld.enter_gospel"))
	assert_true(_until(sc, func() -> bool: return _at(sc, "gospel", "jordan"), 60.0))
	assert_eq(int(_progress(sc, "gospel")["visits"]), 2)
	_disk_matches(sc, "step 11")
	assert_eq(_violations, [])
	assert_eq(sc.router.errors, [])
	_free(d)
	_fixtures_off()


# --- the rules around the routes -------------------------------------------------------------------------------------------

## Ruling 15: a missed block never refuses a quest entrance or changes where it leads. The Warehouse's own radio (an existing portal, today on_failure "flicker out") with the last block missed.
func test_an_entry_is_honoured_after_a_missed_block() -> void:
	var d := _scene({"RW_RUN_START": "warehouse.booth"})
	var sc: Node = d["scene"]
	sc.tap_policy = "failure"  # the bot misses the last block of every scene
	assert_true(_pick(sc, "warehouse.booth.radio"))
	assert_false((_st(sc).pending["dest"] as Dictionary).has("on_miss"))
	assert_true(_until(sc, func() -> bool: return _at(sc, "squadron", "base"), 60.0), "the radio still leads into the Squadron")
	var commit: Array = sc.hotspot_log.filter(func(e: Dictionary) -> bool: return e["kind"] == "commit" and e["hotspot"] == "warehouse.booth.radio")
	assert_eq(commit.size(), 1)
	assert_true(bool(commit[0]["success"]), "the entrance commits as a success (its failure outcome is never taken)")
	var blk: Array = sc.event_log.filter(func(e: Dictionary) -> bool: return e["kind"] == "block_result" and int(e["block"]) == 3 and str(e["node"]) == "warehouse.booth")
	assert_false(bool(blk.back()["passed"]), "the last block really was missed")
	assert_eq([_st(sc).quest, _st(sc).checkpoint], ["squadron", "main/warehouse"])
	_free(d)


## A scene door keeps its rhythm: the bouncer at the Door (success the Spaceship, failure Hell) goes to Hell on a missed last block, through the port (its on_miss).
func test_a_scene_choice_still_takes_its_miss_route() -> void:
	var d := _scene({"RW_RUN_START": "warehouse.exit"})
	var sc: Node = d["scene"]
	sc.tap_policy = "failure"
	assert_true(_pick(sc, "warehouse.exit.bouncer"))
	assert_eq(str((_st(sc).pending["dest"] as Dictionary).get("on_miss", {}).get("id", "")), "main/underworld")
	assert_true(_until(sc, func() -> bool: return sc.engine.node_id != "warehouse.exit", 60.0))
	assert_eq(sc.engine.node_id, "underworld")
	assert_eq(_st(sc).location, "hell")
	_free(d)


## NARRATIVE_GRAPH.md 3.3: a save written before the narrative key loads with nothing lost; a path with an ending makes its quest completed; the first save adds the versioned key.
func test_an_old_save_migrates_and_keeps_the_players_progress() -> void:
	var old := {"version": 2, "reached": {"warehouse": {"entries": 4}, "mothership": {"entries": 1}}, "runs": 7, "best_phases": 12, "migrated_from": "",
		"flags": {"keep:path_gospel_tomb": true}, "paths": {"gospel": {"reached": ["jordan", "jerusalem"], "endings": ["tomb"]}, "ember": {"reached": ["hollow"], "endings": []}},
		"wallet": {"pence": 3500, "held": {}}, "seed": 1234}
	var d := _scene({}, JSON.stringify(old))
	var sc: Node = d["scene"]
	assert_true(sc.router != null)
	assert_true(bool(_progress(sc, "gospel")["completed"]), "the Gospel has an ending: completed")
	assert_false(bool(_progress(sc, "ember")["completed"]))
	var v: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(TMP_SAVE))
	assert_eq(int(v["version"]), 2)
	assert_eq(int(v["runs"]), 8, "the run count goes on")
	assert_eq(int(v["best_phases"]), 12)
	assert_true((v["reached"] as Dictionary).has("mothership"), "the reached levels are kept")
	assert_true((v["flags"] as Dictionary).has("keep:path_gospel_tomb"), "the kept flags are kept")
	assert_eq(v["paths"]["gospel"]["endings"], ["tomb"], "the paths are kept")
	assert_eq(int(v["narrative"]["version"]), 1)
	assert_true(bool(v["narrative"]["quest_progress"]["gospel"]["completed"]))
	_disk_matches(sc, "migrated")
	# a completed quest restarts at its first scene and stays completed
	assert_eq(str(sc.router.destination_for("warehouse.balcony.star", "main/warehouse.balcony").get("id", "")), "gospel/jordan")
	_free(d)


## A save written in the middle of a quest (the player quit there) is closed on load: the run starts on the checkpoint's world as ever, the quest's progress is kept.
func test_a_save_from_the_middle_of_a_quest_is_closed_on_load() -> void:
	var mid := {"version": 2, "reached": {}, "runs": 1, "best_phases": 0, "migrated_from": "", "flags": {}, "paths": {}, "wallet": {"pence": 2000, "held": {}}, "seed": 1,
		"narrative": {"version": 1, "location": "hospital_ward", "quest": "ember", "entry_origin": "main/hospital", "checkpoint": "main/hospital",
			"quest_progress": {"ember": {"scene": "ember/hollow.ford", "completed": false, "visits": 1, "flags": ["ember_held"]}}, "history": ["main/hospital", "ember/hollow", "ember/hollow.ford"]}}
	var d := _scene({}, JSON.stringify(mid))
	var sc: Node = d["scene"]
	assert_true(_st(sc).closed_on_load)
	assert_eq(_st(sc).quest, "")
	assert_eq(_st(sc).current_scene(), "main/warehouse", "a new run starts on the Floor")
	assert_eq(str(_progress(sc, "ember")["scene"]), "ember/hollow.ford", "the quest's progress is kept")
	_free(d)


## A newer narrative version is ignored and never overwritten (the build cannot read it).
func test_a_newer_narrative_version_is_left_alone() -> void:
	var newer := {"version": 2, "reached": {}, "runs": 1, "best_phases": 0, "migrated_from": "", "flags": {}, "paths": {}, "wallet": {"pence": 2000, "held": {}}, "seed": 1,
		"narrative": {"version": 99, "whatever": [1, 2, 3]}}
	var d := _scene({}, JSON.stringify(newer))
	var sc: Node = d["scene"]
	assert_true(_st(sc).newer_than_known)
	assert_true(_go(sc, "warehouse.bar"))
	var v: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(TMP_SAVE))
	assert_eq(int(v["narrative"]["version"]), 99, "the newer value is not overwritten")
	_free(d)


## NARRATIVE_GRAPH.md 3.2 rule 7: a "keep:" flag set at the lock is in memory from the lock and on disk from `switched`.
func test_a_keep_flag_is_saved_at_switched_not_at_the_lock() -> void:
	var d := _scene({"RW_RUN_PATH": "squadron", "RW_RUN_START": "base.c03"})
	var sc: Node = d["scene"]
	assert_eq(sc.run_path, "squadron")
	assert_eq([_st(sc).quest, _st(sc).checkpoint], ["squadron", "main/warehouse"], "a run started inside a quest enters it from the Warehouse hub (no earlier location saved)")
	assert_true(_pick(sc, "base.c03.clipboard"))
	var flag := "keep:path_squadron_met_surgeon"
	assert_true(_until(sc, func() -> bool: return Session.run_progress.flags.has(flag), 120.0), "the flag is set at the lock")
	assert_false(FileAccess.get_file_as_string(TMP_SAVE).contains(flag), "not yet on disk at the lock")
	assert_true(_until(sc, func() -> bool: return sc.engine.node_id == "air.c06", 30.0))
	assert_true(FileAccess.get_file_as_string(TMP_SAVE).contains(flag), "on disk after the switch")
	_free(d)


## The pause menu's "leave" on a departure lap is a port request (the hidden leave, a quest return) and lands on the checkpoint.
func test_the_pause_menus_leave_goes_through_the_port_to_the_checkpoint() -> void:
	_fixtures_on()
	var d := _scene()
	var sc: Node = d["scene"]
	for to in ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership"]:
		assert_true(_go(sc, to))
	assert_true(_pick(sc, "mothership.enter_gospel"))
	assert_true(_until(sc, func() -> bool: return _at(sc, "gospel", "jordan"), 60.0))
	# jordan has one lap (a departure lap): the leave is requested at once
	assert_true(_until(sc, func() -> bool: return sc.selection_open() and sc.engine.phase_beat_at(sc._vt) > 4.0, 20.0))
	assert_true(sc.request_path_leave())
	assert_true(sc.route_log.any(func(e: Dictionary) -> bool: return e["kind"] == "leave_request"), "a port request")
	assert_false(sc.path_leave_requested, "not today's force_leave")
	assert_true(_until(sc, func() -> bool: return _at(sc, "", "mothership"), 60.0), "it lands on the Alien Spaceship hub, not the Floor")
	var sw: Array = sc.route_log.filter(func(e: Dictionary) -> bool: return e["kind"] == "switched")
	assert_eq(str(sw.back()["landed"]), "main/mothership")
	assert_false(bool(sw.back()["fallback"]), "a clean landing")
	assert_eq(str(_progress(sc, "gospel")["scene"]), "gospel/jordan")
	_free(d)
	_fixtures_off()


## The Floor's own hatch (ruling 15), the Bassment through the router at the lap's end, with the items carried kept for the next visit.
func test_the_floors_hatch_enters_the_bassment_at_the_lap_end_and_items_come_back() -> void:
	_fixtures_on()
	var d := _scene()
	var sc: Node = d["scene"]
	assert_true(_pick(sc, "warehouse.enter_bassment"))
	assert_true(_until(sc, func() -> bool: return sc.trial_state == "in", 40.0))
	assert_eq([_st(sc).quest, _st(sc).checkpoint], ["bassment", "main/warehouse"])
	sc.trial.engine.flow.flags.append("lamp")  # (a pickup, as a passage's grant would do)
	sc.trial.request_leave()
	assert_true(_until(sc, func() -> bool: return _at(sc, "", "warehouse"), 60.0))
	assert_eq(_progress(sc, "bassment").get("items", []), ["lamp"], "the items carried are saved with the quest")
	assert_true(_pick(sc, "warehouse.enter_bassment"))
	assert_true(_until(sc, func() -> bool: return sc.trial_state == "in", 60.0))
	assert_true((sc.trial.engine.flow.flags as Array).has("lamp"), "and held again on the next visit")
	assert_eq(int(_progress(sc, "bassment")["visits"]), 2)
	_free(d)
	_fixtures_off()


## Without the fixtures the run has exactly today's entrances; the router is on and the safety switch turns it off.
func test_the_router_is_on_in_the_game_and_off_with_its_switch_or_a_remap() -> void:
	var d := _scene()
	assert_true(d["scene"].router != null)
	assert_true(d["scene"].hotspots.ungated_quest_routes)
	_free(d)
	var d2 := _scene({"RW_NARRATIVE": "0"})
	assert_true(d2["scene"].router == null, "RW_NARRATIVE=0: the run as in N2.1")
	assert_false(d2["scene"].hotspots.ungated_quest_routes)
	_free(d2)
	var d3 := _scene({"RW_PATH_REMAP": "gospel=stub"})
	assert_true(d3["scene"].router == null, "a remapped path is outside the graph")
	_free(d3)
