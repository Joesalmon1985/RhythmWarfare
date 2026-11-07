extends TestCase
## Hotspot projection and hit testing (HotspotView.layout / hit): anchors project through StoryProjector, a touch target is at least min_px wide, the nearest hotspot within its radius wins,
## and an anchor out of sight has no target with the rings off (package A7; with RINGS on it was a touchable beacon at the edge of the picture).


func _entry(id: String, anchor: Dictionary, extra: Dictionary = {}) -> Dictionary:
	var h := {"id": id, "scene": "s", "kind": "exit", "anchor": anchor, "on_success": {"route": "x"}}
	for k in extra:
		h[k] = extra[k]
	return {"hotspot": HotspotContract.normalize(h, "warehouse", "night_one"), "state": "available", "t_state": 0.0}


func _pose_at(map: StoryMap, wp: String) -> Dictionary:
	var w: Dictionary = map.waypoint(wp)
	return {"cam": Vector3((w["at"] as Vector2).x, map.eye_height, (w["at"] as Vector2).y), "yaw": float(w["yaw"]), "pitch": 0.0}


func test_anchors_resolve_to_world_points() -> void:
	var m := StoryMap.load_chapter("night_one")
	var th := HotspotView.resolve({"thing": "bar_glow"}, m, {})
	assert_true(bool(th["ok"]))
	assert_near((th["pos"] as Vector3).x, 10.0, 0.001)
	assert_near((th["pos"] as Vector3).y, 1.8, 0.001, "a thing's y is above its floor")
	var wp := HotspotView.resolve({"waypoint": "to_bar"}, m, {})
	assert_true(bool(wp["ok"]))
	assert_true(float((wp["pos"] as Vector3).y) > float(wp["ground"]), "a doorway's centre is above the floor")
	var ps := HotspotView.resolve({"pos": [0.0, 1.2, 6.0]}, m, {})
	assert_true(bool(ps["ok"]))
	assert_near((ps["pos"] as Vector3).y, float(ps["ground"]) + 1.2, 0.001)
	assert_false(bool(HotspotView.resolve({"thing": "nope"}, m, {})["ok"]))
	assert_false(bool(HotspotView.resolve({"actor": "c01"}, m, {})["ok"]), "no crowd: an actor cannot be placed")


func test_a_touch_target_is_never_under_min_px_and_stays_inside_the_view() -> void:  # (N2.1: the floor is 88 px, lead ruling 3)
	var m := StoryMap.load_chapter("night_one")
	var view := Vector2(844, 240)
	var pose := _pose_at(m, "floor_centre")
	var ents := [_entry("a", {"waypoint": "to_bar"}), _entry("b", {"waypoint": "to_balcony"}), _entry("c", {"thing": "disco_ball"}), _entry("far", {"pos": [0.0, 1.0, -8.0]}, {"radius_m": 0.05})]
	var lay := HotspotView.layout(ents, m, {}, pose, view)
	assert_true(lay.size() >= (4 if HotspotView.RINGS else 3), "every anchor in the picture is laid out (one is out of sight from here: with the rings off it has no target) (%d)" % lay.size())
	for e in lay:
		assert_true(float(e["radius_px"]) * 2.0 >= 88.0 - 0.001, "%s is at least 88 px wide (%s)" % [e["id"], str(float(e["radius_px"]) * 2.0)])
		var c: Vector2 = e["centre"]
		assert_true(c.x >= 0.0 and c.x <= view.x and c.y >= 0.0 and c.y <= view.y, "%s is on screen: %s" % [e["id"], str(c)])
		assert_eq(HotspotView.hit(lay, c), str(e["id"]), "a tap on its centre hits it")


func test_the_nearest_hotspot_within_its_radius_wins_and_a_miss_hits_nothing() -> void:
	var lay := [
		{"id": "a", "centre": Vector2(100, 100), "radius_px": 40.0},
		{"id": "b", "centre": Vector2(160, 100), "radius_px": 40.0},
	]
	assert_eq(HotspotView.hit(lay, Vector2(120, 100)), "a", "inside both: the nearer centre")
	assert_eq(HotspotView.hit(lay, Vector2(140, 100)), "b")
	assert_eq(HotspotView.hit(lay, Vector2(100, 190)), "", "outside every radius")
	assert_eq(HotspotView.hit([], Vector2(1, 1)), "")


func test_an_anchor_out_of_sight_is_a_beacon_at_the_edge_that_can_still_be_touched() -> void:
	var m := StoryMap.load_chapter("night_one")
	var view := Vector2(844, 240)
	var pose := _pose_at(m, "stage")  # looking at the back wall; the bar is off to the side
	pose["yaw"] = 0.0
	var ents := [_entry("bar", {"thing": "bar_glow"}), _entry("behind", {"pos": [0.0, 1.0, 12.0]})]
	var lay := HotspotView.layout(ents, m, {}, pose, view)
	if not HotspotView.RINGS:  # (package A7, ruling 35b: no beacon; what is out of the picture has no target and a tap at the edge selects nothing)
		assert_false(lay.any(func(e: Dictionary) -> bool: return str(e["id"]) == "behind"), "an anchor out of sight is not laid out: no beacon, no target")
		assert_false(lay.any(func(e: Dictionary) -> bool: return bool(e["edge"])), "nothing stacked at the edge")
		assert_eq(HotspotView.hit(lay, Vector2(view.x - 20.0, view.y * 0.3)), "", "a tap where the beacon stood selects nothing")
		return
	var edge := 0
	for e in lay:
		if bool(e["edge"]):
			edge += 1
			var c: Vector2 = e["centre"]
			assert_true(c.x < view.x * 0.2 or c.x > view.x * 0.8, "a beacon sits at a side of the picture: %s" % str(c))
			assert_true(c.x >= 0.0 and c.x <= view.x and c.y >= 0.0 and c.y <= view.y)
			assert_eq(HotspotView.hit(lay, c), str(e["id"]), "and a tap there selects it")
	assert_true(edge >= 1, "at least one anchor is out of sight from the stage")


func test_the_projection_is_the_stage_camera() -> void:
	var m := StoryMap.load_chapter("night_one")
	var view := Vector2(800, 400)
	var pose := _pose_at(m, "floor_centre")
	var lay := HotspotView.layout([_entry("a", {"pos": [0.0, 1.6, 0.0]})], m, {}, pose, view)
	var want := StoryProjector.project(lay[0]["world"], pose, view)
	assert_eq(lay[0]["centre"], want["screen"], "the layout is StoryProjector's")
	var big := HotspotView.layout([_entry("a", {"pos": [0.0, 1.6, 0.0]})], m, {}, pose, view * 2.0)
	assert_near((big[0]["centre"] as Vector2).x, (lay[0]["centre"] as Vector2).x * 2.0, 0.5, "it scales with the view, so the low-res draw and the screen hit test agree")


func test_the_layout_carries_t_commit_and_success_through() -> void:
	var m := StoryMap.load_chapter("night_one")
	var e := _entry("a", {"pos": [0.0, 1.6, 0.0]})
	e["t_commit"] = 12.5
	e["success"] = false
	var lay := HotspotView.layout([e, _entry("b", {"pos": [0.5, 1.6, 0.0]})], m, {}, _pose_at(m, "floor_centre"), Vector2(800, 400))
	assert_near(float(lay[0]["t_commit"]), 12.5, 1e-9)
	assert_false(bool(lay[0]["success"]))
	assert_true(bool(lay[1]["success"]), "success defaults to true")


# ---- the "claim" look, drawn: the real run scene's view on the ward's table --------------------------------------------------------------------

const TMP_SAVE := "user://test_hotspots_view_save.json"


func _ward_scene() -> Dictionary:
	var saved := Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_START", "ward")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_TAPS", "none")
	Session.run_start_node = ""
	var host := Control.new()
	host.size = Vector2(1152, 648)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = Vector2(1152, 648)
	return {"host": host, "scene": scene, "saved": saved}


func _free_ward(d: Dictionary) -> void:
	Session.run_progress = d["saved"]
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	(d["host"] as Control).queue_free()
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_TAPS"]:
		OS.set_environment(k, "")
	OS.unset_environment("RW_RUN_START")


func _ward_to(scene: Node, beat: float) -> void:
	var t_end: float = scene.engine.t_of(beat)
	var t: float = scene._vt
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func test_hotspot_items_carry_the_decision_time_and_the_outcome() -> void:
	var d := _ward_scene()
	var scene: Node = d["scene"]
	_ward_to(scene, 6.0)
	var e: RunEngine = scene.engine
	var items: Array = scene.hotspot_items()
	var table: Dictionary = (items.filter(func(x: Dictionary) -> bool: return str(x["hotspot"]["id"]) == "ward.cards"))[0]
	assert_near(float(table["t_commit"]), e.t_of(e._decision_beat()), 1e-6, "the touch would be judged at block 0's decision")
	var finals := items.filter(func(x: Dictionary) -> bool: return RunHotspots.window_of(x["hotspot"]) == "final")
	assert_eq(finals.size(), items.size() - 1, "in block 0 the table and every choice of the room are on show (N2.1: selection is open for the whole scene)")
	for it in finals:
		assert_near(float(it["t_commit"]), e.t_of(48.0 + e._decision_beat()), 1e-6, "a choice touched in block 0 still waits for the lock at the last block's decision")
	_ward_to(scene, 20.0)
	items = scene.hotspot_items()
	table = (items.filter(func(x: Dictionary) -> bool: return str(x["hotspot"]["id"]) == "ward.cards"))[0]
	assert_near(float(table["t_commit"]), e.t_of(16.0 + e._decision_beat()), 1e-6, "block 1 once block 0's decision has passed")
	_ward_to(scene, 52.0)
	scene.hotspot_select("ward.exit_art")
	for it in scene.hotspot_items():
		assert_near(float(it["t_commit"]), e.t_of(48.0 + e._decision_beat()), 1e-6, "the final window's hotspots wait for the last block")
	_ward_to(scene, 61.0)
	var committed: Array = (scene.hotspot_items() as Array).filter(func(x: Dictionary) -> bool: return str(x["state"]) == "committed")
	assert_eq(committed.size(), 1)
	assert_true(committed[0].has("success"))
	_free_ward(d)


func test_the_claim_look_draws_selected_committed_and_refused_with_reduced_and_high_contrast() -> void:
	var d := _ward_scene()
	var scene: Node = d["scene"]
	_ward_to(scene, 10.0)
	var hv: HotspotView = (scene.stages[scene.active_world] as Dictionary)["hotspot_view"]
	var table: Dictionary = scene.hotspots.get_hotspot("ward.cards")
	assert_eq(str(table["look"]["selected"]), "claim")
	var now: float = scene.hud.now_t
	var drawn := [0]
	var states := [["selected", 0.05, true], ["selected", 1.0, true], ["committed", 0.1, true], ["committed", 0.5, true], ["committed", 0.1, false], ["committed", 0.6, false], ["available", 0.0, true]]
	for mode in [[false, false], [true, false], [false, true]]:
		hv.reduced = mode[0]
		hv.high_contrast = mode[1]
		for s in states:
			hv.items_fn = func() -> Array:
				drawn[0] += 1
				return [{"hotspot": table, "state": s[0], "t_state": now - float(s[1]), "t_commit": now + 1.5, "success": s[2]}]
			hv.queue_redraw()
			await tree.process_frame
			await tree.process_frame
	assert_true(drawn[0] >= states.size(), "the view drew every state (%d draws)" % drawn[0])
	_free_ward(d)


func test_only_the_card_table_takes_the_claim_path_every_other_hotspot_draws_the_plain_looks() -> void:
	var data := RunData.load_default()
	assert_true(data.errors.is_empty(), str(data.errors))
	var claim: Array = []
	var n := 0
	for scene_id in data.hotspots:
		for h in data.hotspots[scene_id]:
			n += 1
			if HotspotView.uses_claim_look(h):
				claim.append(str(h["id"]))
	assert_true(n > 50, "every shipped hotspot was looked at (%d)" % n)
	assert_eq(claim, ["ward.cards"], "the claim look (its free, touched, seated and refused drawing) belongs to the table alone")
	assert_false(HotspotView.uses_claim_look({"look": {"available": "beckon", "selected": "plain"}}))
	assert_false(HotspotView.uses_claim_look({}))


func test_light_tint_keeps_the_hue_at_full_brightness() -> void:
	for c in [Color(1.0, 0.7, 0.25), Color(0.2, 0.3, 0.9), Color(0.5, 0.5, 0.45), Color(0.9, 0.1, 0.6)]:
		var t := HotspotView.light_tint(c)
		assert_near(t.v, 1.0, 1e-4, "every world's lights are as bright")
		assert_true(t.s >= 0.35 - 1e-4 and t.s <= 0.6 + 1e-4, "and pale enough to read as light (%.2f)" % t.s)
		if c.s > 0.2:
			assert_near(absf(wrapf(t.h - c.h, -0.5, 0.5)), 0.0, 1e-3, "in the world's own hue")


func test_a_staged_option_is_lit_by_its_role_and_keeps_to_the_floor() -> void:
	var view := HotspotView.new()
	view.tint = HotspotView.light_tint(Color(1.0, 0.7, 0.25))
	var e := _entry("a", {"pos": [0.0, 1.6, 0.0]}, {"default": true})
	assert_eq(view._colours_of(e)[0], view.tint, "an unstaged hotspot is the world's light")
	assert_false(view._staged(e), "no role, not staged")
	assert_true(view._is_default(e), "its own default flag marks it")
	e["role"] = "current"
	assert_eq(view._colours_of(e)[0], HotspotView.CURRENT_COL, "the current choice is green")
	assert_true(view._staged(e) and view._is_default(e), "staged, and the current option is the doubled one")
	e["role"] = "other"
	assert_eq(view._colours_of(e)[0], HotspotView.OTHER_COL, "any other option is red")
	assert_false(view._is_default(e), "and single-ringed, even when it is the data's default")
	e["role"] = "committed"
	assert_eq(view._colours_of(e)[0], HotspotView.CURRENT_COL, "a committed option stays green")
	view.high_contrast = true
	assert_eq(view._colours_of(e)[0], Color(1.0, 1.0, 0.4), "high contrast overrides the role colour")
	view.free()


func test_a_finished_portal_keeps_its_own_tint_and_the_crown_look() -> void:
	var view := HotspotView.new()
	var e := _entry("p", {"pos": [0.0, 1.6, 0.0]}, {"look": {"available": "glow", "finished": {"flags_any": ["keep:done"], "tint": "#ffd25a"}}})
	assert_eq(view._look_of(e), "glow", "an unfinished portal has its own look")
	e["finished"] = true
	e["role"] = "other"
	assert_eq(view._look_of(e), "crown", "a finished portal has the crown look")
	assert_eq(view._colours_of(e)[0], Color.html("#ffd25a"), "and its own tint, whatever its role")
	view.free()
