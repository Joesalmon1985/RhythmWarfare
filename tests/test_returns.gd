extends TestCase
## Work package N2.5: the return objects of the three quest paths (tools/run/returns_common.py). Every scene of gospel, squadron and ember has `<quest>.return`, a touchable object whose
## success leads to the main run (`run:warehouse`; the router lands it on the checkpoint, docs/narrative/N2_2_ROUTER.md); it is never gated by rhythm (a miss leads the same way), never
## the default, and never within 0.75 m of another hotspot's anchor; and a return taken from a quest entered at a hub outside the Warehouse lands on that hub, also after a missed block.
##
## NOT BUILT, so not tested: the "back" rows and the seven extra routes of lead ruling 17 (a hotspot's route must be a `next` edge of its scene, and an ending has the one route
## `run:warehouse`: src/run/run_data.gd `_validate_routes` and `_load_hotspots`), and the Bassment's visible return. KNOWN_UNDER_THREE names the path scenes that have fewer than three distinct destinations today;
## the test pins that list, so the package that builds the back and restart routes has to empty it.

const PATHS := ["gospel", "squadron", "ember"]
const MIN_GAP_M := 0.75
const FX_FLAG := "fx_n25"
const TMP_SAVE := "user://test_returns_save.json"
const STEP := 1.0 / 30.0

## Scenes whose distinct destinations (onward routes plus the return) are under three: the two entry scenes (one onward route), the five endings (the return alone) and the two scenes
## with one onward route and a predecessor (back would be the third).
const KNOWN_UNDER_THREE := ["ember/deeps", "ember/hollow", "ember/mountain.keeper", "ember/mountain.spring", "gospel/jerusalem.golgotha", "gospel/jerusalem.road", "gospel/jerusalem.tomb",
	"gospel/jordan", "squadron/escape.c13"]

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
	HotspotContract.extra_rows = {"main": [{"id": "underworld.enter_gospel", "world": str(main.nodes["underworld"]["world"]), "scene": "underworld", "anchor": anchor, "kind": "secret",
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
