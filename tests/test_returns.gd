extends TestCase
## Work package N2.5: the return objects of the three quest paths (tools/run/returns_common.py). Every scene of gospel, squadron and ember has `<quest>.return`, a touchable object whose
## success leads to the main run (`run:warehouse`; the router lands it on the checkpoint, docs/narrative/N2_2_ROUTER.md); it is never gated by rhythm (a miss leads the same way), never
## the default, and never within 0.75 m of another hotspot's anchor; and a return taken from a quest entered at a hub outside the Warehouse lands on that hub, also after a missed block.
##
## The extra routes of lead ruling 17 (tools/run/path_routes.py): every ending's restart to its quest's first scene (it sets the ending's keep flag too), the two entry scenes' second
## routes, and the back routes of the two scenes that had one onward route and of every ending; with them no path scene is under three destinations (KNOWN_UNDER_THREE is empty). The Bassment's own way
## back (tools/trial/returns.py): every passage without a way out has one more choice that leads out, never the default, with its own exit hotspot.

const PATHS := ["gospel", "squadron", "ember"]
const MIN_GAP_M := 0.75
const FX_FLAG := "fx_n25"
const TMP_SAVE := "user://test_returns_save.json"
const STEP := 1.0 / 30.0

## Scenes whose distinct destinations (onward routes plus the return) are under three: none since the restarts, the second routes and the back routes.
const KNOWN_UNDER_THREE := []
## Bassment passages whose camera shows no spot for the return beside their own choices (tools/trial/return_spots.gd): their way out stays the back key.
const NO_RETURN_SPOT := [1, 2, 7, 9, 14, 34, 38]
## (quest, scene, kind, to): the routes of tools/run/path_routes.py
const EXTRA := [["gospel", "jerusalem.tomb", "restart", "jordan"], ["gospel", "jerusalem.road", "restart", "jordan"], ["squadron", "escape.c13", "restart", "base"],
	["ember", "mountain.spring", "restart", "hollow"], ["ember", "mountain.keeper", "restart", "hollow"], ["gospel", "jordan", "skip", "jordan.nazareth"],
	["ember", "hollow", "skip", "hollow.inn"], ["gospel", "jerusalem.golgotha", "back", "jerusalem.trial"], ["ember", "deeps", "back", "north"],
	["gospel", "jerusalem.tomb", "back", "jerusalem.golgotha"], ["gospel", "jerusalem.road", "back", "jerusalem.trial"], ["squadron", "escape.c13", "back", "escape.c12"],
	["ember", "mountain.spring", "back", "mountain"], ["ember", "mountain.keeper", "back", "mountain"]]

var _saved: RunProgress


func _rows(d: RunData, sid: String, id: String) -> Array:
	return d.hotspots_of(sid).filter(func(h: Dictionary) -> bool: return str(h["id"]) == id)


func _pos_of(h: Dictionary) -> Vector3:
	var a: Dictionary = h["anchor"]
	var v: Array = a["pos"]
	return Vector3(float(v[0]), float(v[1]), float(v[2]))


func test_every_path_scene_has_its_quests_return() -> void:
	var n := 0
	for p in PATHS:
		var d := RunData.load_path(p)
		assert_eq(d.errors, [], "%s loads clean" % p)
		for sid in d.node_order:
			n += 1
			var rows := _rows(d, sid, "%s.return" % p)
			assert_eq(rows.size(), 1, "%s/%s: one return" % [p, sid])
			if rows.size() != 1:
				continue
			var h: Dictionary = rows[0]
			assert_eq(str((h["on_success"] as Dictionary).get("route", "")), "run:warehouse", "%s/%s: the return leads to the main run" % [p, sid])
			assert_eq(str((h["on_failure"] as Dictionary).get("route", "")), "run:warehouse", "%s/%s: a missed block leads the same way (no refusal)" % [p, sid])
			assert_true(bool(h["repeatable"]) and not bool(h["default"]), "%s/%s: repeatable, never the default" % [p, sid])
			var av: Dictionary = h["available"]
			assert_true((av["flags_all"] as Array).is_empty() and (av["flags_none"] as Array).is_empty() and float(av["energy_min"]) == 0.0 and not bool(av["once"]), "%s/%s: always available" % [p, sid])
			assert_true(float(h["min_px"]) >= 88.0, "%s/%s: the touch target is at least 88 px" % [p, sid])
			assert_eq(str(h["kind"]), "object")
	assert_eq(n, 46, "the three paths have 46 scenes")


func test_a_return_keeps_its_distance_from_every_other_anchor() -> void:
	for p in PATHS:
		var d := RunData.load_path(p)
		for sid in d.node_order:
			var rows := _rows(d, sid, "%s.return" % p)
			if rows.size() != 1:
				continue
			var m := TrialData.map_of(str(d.nodes[sid]["map"]))
			var mine := _pos_of(rows[0])
			for h in d.hotspots_of(sid):
				if str(h["id"]) == "%s.return" % p:
					continue
				var an: Dictionary = h["anchor"]
				var at := Vector2.INF
				if an.has("actor"):
					var hm: Dictionary = m.home(str(an["actor"]))
					if not hm.is_empty():
						at = hm["at"]
				else:
					var r := HotspotView.resolve(an, m, {})
					if bool(r.get("ok", false)):
						at = Vector2((r["pos"] as Vector3).x, (r["pos"] as Vector3).z)
				if at != Vector2.INF:
					assert_true(Vector2(mine.x, mine.z).distance_to(at) >= MIN_GAP_M, "%s/%s: the return is %.2f m from %s" % [p, sid, Vector2(mine.x, mine.z).distance_to(at), h["id"]])


func test_a_path_scene_offers_three_destinations_but_the_known_gap() -> void:
	var under: Array = []
	for p in PATHS:
		var d := RunData.load_path(p)
		for sid in d.node_order:
			var dest := {}
			for h in d.hotspots_of(sid):
				if not ((h["available"] as Dictionary)["flags_all"] as Array).is_empty():
					continue  # (a choice that needs a flag is not counted: lead ruling 19)
				var r := str((h["on_success"] as Dictionary).get("route", ""))
				if r != "":
					dest[r] = true
			if dest.size() < 3:
				under.append("%s/%s" % [p, sid])
	under.sort()
	var want: Array = KNOWN_UNDER_THREE.duplicate()
	want.sort()
	assert_eq(under, want, "the scenes under three destinations are exactly the known ones")


# --- a return taken in the run ------------------------------------------------------------------------------------------------

func _rm(p: String) -> void:
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(p)


## The real run scene on its virtual clock (the pattern of tests/test_narrative_run.gd), with a fixture entrance into the Gospel on the Hell hub.
func _scene(tap_policy := "") -> Dictionary:
	if _saved == null:
		_saved = Session.run_progress
	_rm(TMP_SAVE)
	_rm(TMP_SAVE + ".tmp")
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	var main := RunData.load_default()
	var anchor := {}
	for h in main.hotspots_of("underworld"):
		if typeof(h.get("anchor", null)) == TYPE_DICTIONARY:
			anchor = (h["anchor"] as Dictionary).duplicate(true)
			break
	var has_real := false
	for h in main.hotspots_of("underworld"):
		if str(h.get("id", "")) == "underworld.enter_gospel":
			has_real = true  # (Hell's entrances are authored since N2.4: the fixture would duplicate the real row and RunData would refuse the data)
	HotspotContract.extra_rows = {} if has_real else {"main": [{"id": "underworld.enter_gospel", "world": str(main.nodes["underworld"]["world"]), "scene": "underworld", "anchor": anchor, "kind": "secret",
		"look": {"available": "pulse"}, "available": {"flags_all": [FX_FLAG]}, "on_success": {"route": "path:gospel"}, "on_failure": {"energy": -4}, "repeatable": true}]}
	NarrativeGraph.clear_cache()
	var env := {"RW_RUN_VIRTUAL": "1", "RW_RUN_BOT": "perfect", "RW_RUN_ROUTES": "", "RW_RUN_TAPS": "none", "RW_RUN_FLAGS": FX_FLAG}
	for k in env:
		OS.set_environment(k, str(env[k]))
	Session.run_start_node = ""
	Session.run_start_path = ""
	var host := Control.new()
	host.size = Vector2(1280, 720)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = host.size
	return {"host": host, "scene": scene, "env": env.keys()}


func _free(d: Dictionary) -> void:
	(d["host"] as Control).queue_free()
	for k in d["env"]:
		OS.unset_environment(str(k))
	HotspotContract.extra_rows = {}
	NarrativeGraph.clear_cache()
	Session.run_progress = _saved
	_saved = null
	_rm(TMP_SAVE)


func _until(scene: Node, cond: Callable, max_s := 120.0) -> bool:
	var t_end: float = scene._vt + max_s
	while scene._vt < t_end:
		if cond.call():
			return true
		scene._vt += STEP
		scene._step_virtual(scene._vt)
	return cond.call()


func _at(scene: Node, path: String, node: String) -> bool:
	return scene.trial_state == "" and scene.run_path == path and scene.engine.node_id == node


func _pick(scene: Node, id: String) -> bool:
	var ok := _until(scene, func() -> bool: return scene.selection_open() and scene.hotspots.is_shown(id, scene.engine.block, true) and scene.engine.phase_beat_at(scene._vt) > 1.0, 60.0)
	return ok and scene.hotspot_select(id)


func _go(scene: Node, to: String) -> bool:
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
	return _until(scene, func() -> bool: return _at(scene, "", to), 200.0)


## The Gospel entered from the Hell hub; the return from its first scene (with the last block missed) lands on the Hell hub, the scene left is kept, and the Gospel can be entered again.
func test_a_return_lands_on_the_hub_the_quest_was_entered_from_also_after_a_missed_block() -> void:
	var d := _scene()
	var sc: Node = d["scene"]
	for to in ["warehouse.bar", "warehouse.chill", "warehouse.exit", "underworld"]:
		assert_true(_go(sc, to), "mainline: %s" % to)
	assert_true(_pick(sc, "underworld.enter_gospel"))
	assert_true(_until(sc, func() -> bool: return _at(sc, "gospel", "jordan"), 60.0), "in the Gospel")
	var router: QuestRouter = sc.router
	assert_eq([router.state.quest, router.state.entry_origin, router.state.checkpoint], ["gospel", "main/underworld", "main/underworld"])
	sc.tap_policy = "failure"  # the last block of the scene is missed
	assert_true(_pick(sc, "gospel.return"), "the return can be picked")
	assert_false((router.state.pending["dest"] as Dictionary).has("on_miss"), "no miss route: a miss does not change where it leads")
	assert_true(_until(sc, func() -> bool: return _at(sc, "", "underworld"), 120.0), "the return lands on the Hell hub, not the Floor")
	var blk: Array = sc.event_log.filter(func(e: Dictionary) -> bool: return e["kind"] == "block_result" and str(e["node"]) == "jordan" and int(e["block"]) == 3)
	assert_true(not blk.is_empty() and not bool(blk.back()["passed"]), "the last block really was missed")
	assert_eq(router.state.quest, "")
	assert_eq(str(router.state.progress_of("gospel")["scene"]), "gospel/jordan")
	assert_eq(router.errors, [])
	_free(d)


func test_the_restarts_second_routes_and_back_routes_are_touchable_never_gated_never_the_default() -> void:
	for x in EXTRA:
		var d := RunData.load_path(str(x[0]))
		assert_eq(d.errors, [], "%s loads clean" % x[0])
		var sid := str(x[1])
		var hid := "%s.%s" % [sid, "restart" if str(x[2]) == "restart" else str(x[2])]
		var rows := _rows(d, sid, hid)
		assert_eq(rows.size(), 1, "%s/%s: one %s" % [x[0], sid, hid])
		if rows.size() != 1:
			continue
		var h: Dictionary = rows[0]
		assert_eq(str(h["on_success"]["route"]), str(x[3]), "%s leads to %s" % [hid, x[3]])
		assert_eq(str(h["on_failure"]["route"]), str(x[3]), "%s: a miss leads the same way" % hid)
		assert_false(bool(h["default"]), "%s is never the default" % hid)
		assert_true((h["available"]["flags_all"] as Array).is_empty(), "%s is always on offer" % hid)
		var route := (d.nodes[sid]["next"] as Array).filter(func(e: Dictionary) -> bool: return str(e["to"]) == str(x[3]))
		assert_eq(route.size(), 1, "%s/%s: the route to %s is one of the scene's" % [x[0], sid, x[3]])
		if str(x[2]) == "restart":
			assert_eq(str(d.nodes[sid]["next"][0]["to"]), "run:warehouse", "%s: the ending's way back stays first" % sid)
			assert_eq(str(x[3]), d.start_node(), "%s: the restart leads to the quest's first scene" % sid)
			var keep: Array = (h["on_success"] as Dictionary).get("flags_set", [])
			assert_true(keep.any(func(f: String) -> bool: return f.begins_with("keep:path_")), "%s: the restart marks the ending reached too (%s)" % [hid, str(keep)])


func test_the_bassment_has_its_own_way_back_from_every_passage() -> void:
	var t := TrialData.load_default()
	assert_eq(t.errors, [], "the Bassment loads clean")
	var n := 0
	for k in t.passages:
		var p: Dictionary = t.passages[k]
		var ret: Array = (p["choices"] as Array).filter(func(c: Dictionary) -> bool: return bool(c.get("return", false)))
		if ret.is_empty():
			assert_true(str(p.get("kind", "")) in ["death", "victory"] or NO_RETURN_SPOT.has(int(k)), "passage %s: only a death, the victory or a room with no spot for it is without the return" % str(k))
			continue
		n += 1
		assert_false(bool(ret[0].get("default", false)), "passage %s: the return is never the default" % str(k))
		assert_eq(str(ret[0].get("exit", "")), "warehouse", "passage %s: the return leads out" % str(k))
	assert_eq(n, 56 - NO_RETURN_SPOT.size(), "every passage but the seven deaths, the victory and the rooms with no spot has the return")

