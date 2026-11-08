extends TestCase
## A real cut between two Doom geography worlds (docs/engine/GEOGRAPHY_WORLDS.md, hook H1.6), on the real run scene with the overlay (RW_DOOM_WORLDS=1): from the Warehouse floor
## the Bar's guide (left): the lock handler walks the Warehouse's `left` polyline at a walking pace (ruling 42: 6 bars, the swap waits for the hold, beat 81), the passage frame shuts, the stage swaps to doom_bar 17 beats after the boundary (the Bar->Floor leg is 3 bars and swaps on the
## downbeat and the arrival walks home to wb_ref; then from the Bar the Floor's guide (left) back to doom_warehouse. The run scene is driven as tests/test_geography.gd drives it.
## Shot: docs/shots/doom/cuts/warehouse_to_bar.jpg (tools/doom/shoot_cut.py).

const TMP_SAVE := "user://test_doom_cuts_save.json"


func _doom_run() -> RunData:
	OS.set_environment("RW_DOOM_WORLDS", "1")
	var on := RunData.load_default()
	OS.set_environment("RW_DOOM_WORLDS", "")
	return on


func _scene(d: RunData, routes: String, start: String) -> Dictionary:
	var saved := Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", routes)
	OS.set_environment("RW_RUN_START", start)
	Session.run_start_node = ""
	var script: GDScript = load("res://src/run/run_play.gd")
	script.set("data_for_test", d)
	var host := Control.new()
	host.size = Vector2(1152, 648)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = host.size
	return {"host": host, "scene": scene, "saved": saved}


func _free(s: Dictionary) -> void:
	Session.run_progress = s["saved"]
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	(s["host"] as Control).queue_free()
	OS.set_environment("RW_RUN_VIRTUAL", "")
	OS.set_environment("RW_RUN_BOT", "")
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.unset_environment("RW_RUN_START")


func _run_to(scene: Node, t_end: float) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func _walks(scene: Node, world: String) -> Array:
	return (scene.journey_log as Array).filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_move" and bool((a["args"] as Dictionary).get("threshold", false)) and str(a["world"]) == world)


func _near(st: StoryStage, t: float, wp: String) -> float:
	return (st.player.pose_at(t)["pos"] as Vector2).distance_to(st.map.waypoint(wp)["at"])


func test_warehouse_to_bar_and_back_to_the_floor_on_the_run_scene() -> void:
	var d := _doom_run()
	assert_eq(d.errors, [], "the overlay loads clean")
	var s := _scene(d, "left,left", "doom_warehouse")  # the Warehouse: left is the Bar; the Bar: left is the Floor
	var scene: Node = s["scene"]
	assert_true(scene.engine != null and scene.data == d, "the scene plays the overlay's data")
	var B: float = scene.engine.beat_s
	var wh_rail: Dictionary = d.nodes["doom_warehouse"]["rail"]
	var bar_rail: Dictionary = d.nodes["doom_bar"]["rail"]
	# the Warehouse floor, phase 1: the Bar's guide
	_run_to(scene, 60.0 * B)
	assert_eq(scene.engine.node_id, "doom_warehouse")
	assert_eq(scene.engine.selected_route(), "doom_bar", "the scripted tap is on the Bar's guide (left)")
	_run_to(scene, 63.9 * B)
	var w1 := _walks(scene, "doom_warehouse")
	assert_eq(w1.size(), 1, "one threshold walk to the Warehouse's left threshold")
	if w1.size() == 1:
		assert_near(float(w1[0]["t0"]), 52.0 * B, 0.01, "from the scripted tap at beat 52 (ruling 39: the tap is the decision)")
		assert_eq(str(w1[0]["args"]["to"]), str(wh_rail["exits"]["left"]), "to the threshold wh_bar_door")
		assert_eq(w1[0]["args"]["via"], wh_rail["routes"]["left"]["via"], "along the Warehouse's left polyline")
	var wh: StoryStage = scene.stages["doom_warehouse"]["stage"]
	# ruling 42: the walk-out starts where the rail stands at the tap. Since polish A's stay rail that is the choice viewpoint wh_ref (5.5 m to wh_bar_door): the authored 2 bars
	# already walk it at pace, so from beat 52 the leg ends at beat 60, the doorway hold takes the last bar and the swap is on the boundary (beat 64). The hold-past-the-boundary
	# case of ruling 42b (cut_t on a whole beat by the next phase's beat 32) is proven in test_geography on the long legs.
	assert_eq(scene.journey.walk_offs.size(), 1, "one walk-out so far")
	var wo: Dictionary = scene.journey.walk_offs[0] if not (scene.journey.walk_offs as Array).is_empty() else {}
	var t_cut := 64.0 * B
	var t_arrive := 52.0 * B
	if not wo.is_empty():
		assert_eq(str(wo["from"]), "wh_ref", "from the choice viewpoint")
		assert_near(float(wo["length"]), 5.5, 0.1, "the leg is 5.5 m")
		assert_true(float(wo["length"]) <= RunRail.WALK_PACE_MAX * 2.0 * 4.0 * B + 1e-6, "the authored 2 bars walk it at no more than 3 m/s")
		assert_near(float(wo["bars"]), 2.0, 1e-6, "2 bars (the authored leg, not lengthened)")
		assert_eq(bool(wo["paced"]), false, "not paced: the leg is exactly as authored")
		if w1.size() == 1:
			assert_near(float(w1[0]["args"]["bars"]), 2.0, 1e-6, "the walk's own bars")
		assert_near(float(wo["hold_bars"]), 1.0, 0.01, "the doorway hold of about one bar fits before the boundary (the guard before it is a sliver short)")
		t_arrive = 52.0 * B + float(wo["bars"]) * 4.0 * B
		assert_true(float(wo["cut_t"]) < 0.0, "no cut time: the swap on the boundary (cut_t -1)")
	assert_true(_near(wh, t_arrive, "wh_bar_door") < 0.05, "at the threshold when the leg's bars are walked (%f m)" % _near(wh, t_arrive, "wh_bar_door"))
	assert_true(_near(wh, t_cut - 0.1 * B, "wh_bar_door") < 0.05, "and still there in the doorway's hold")
	assert_true(scene._passage.aperture < 0.3, "the frame shut to the doorway before the boundary (%f)" % scene._passage.aperture)
	assert_eq(scene.active_world, "doom_warehouse", "the Warehouse is shown up to the boundary")
	_run_to(scene, 64.4 * B)
	assert_eq(scene.engine.node_id, "doom_bar", "the engine and the music are in the Bar's phase from the boundary")
	assert_eq(scene.active_world, "doom_bar", "the stage swapped to the Bar on the boundary")
	var bar: StoryStage = scene.stages["doom_bar"]["stage"]
	_run_to(scene, t_cut + 12.0 * B)
	assert_true(_near(bar, t_cut + 12.0 * B, "wb_ref") < 0.05, "the arrival walked home to wb_ref (%f m)" % _near(bar, t_cut + 12.0 * B, "wb_ref"))
	assert_eq(scene._passage.aperture, 1.0, "the frame is open again")
	# the Bar, phase 2: the Floor's guide, back to the Warehouse
	_run_to(scene, 127.9 * B)
	assert_eq(scene.engine.selected_route(), "doom_warehouse", "the scripted tap is on the Floor's guide (left)")
	var w2 := _walks(scene, "doom_bar")
	assert_eq(w2.size(), 1, "one threshold walk to the Bar's left threshold")
	if w2.size() == 1:
		assert_near(float(w2[0]["t0"]), 116.0 * B, 0.01, "from the scripted tap at beat 52 of the Bar's phase")
		assert_eq(str(w2[0]["args"]["to"]), str(bar_rail["exits"]["left"]), "to the threshold wb_floor_door")
		assert_eq(w2[0]["args"]["via"], bar_rail["routes"]["left"]["via"], "along the Bar's left polyline")
	# the Bar's leg (from the choice viewpoint wb_ref, 7.2 m, 3 bars from beat 116) ends on the boundary with no hold: the downbeat swap as before
	assert_eq(scene.journey.walk_offs.size(), 2, "a second walk-out")
	if (scene.journey.walk_offs as Array).size() == 2:
		var wo2: Dictionary = scene.journey.walk_offs[1]
		assert_eq(str(wo2["from"]), "wb_ref", "from the Bar's choice viewpoint")
		assert_near(float(wo2["length"]), 7.2, 0.1, "the leg is 7.2 m")
		assert_near(float(wo2["bars"]), 3.0, 1e-6, "3 bars")
		assert_true(float(wo2["cut_t"]) < 0.0, "no cut time: the swap on the boundary (cut_t -1)")
	assert_true(_near(bar, 128.0 * B, "wb_floor_door") < 0.05, "at the Bar's threshold on the boundary (%f m)" % _near(bar, 128.0 * B, "wb_floor_door"))
	assert_true(scene._passage.aperture < 0.3, "the frame shut again (%f)" % scene._passage.aperture)
	_run_to(scene, 128.4 * B)
	assert_eq(scene.engine.node_id, "doom_warehouse", "back on the Floor")
	assert_eq(scene.active_world, "doom_warehouse", "the stage swapped back")
	assert_true(scene.stages["doom_warehouse"]["stage"] == wh, "the Warehouse's stage was kept, not rebuilt")
	_run_to(scene, 140.0 * B)
	assert_true(_near(wh, 140.0 * B, "wh_ref") < 0.05, "the arrival walked home to wh_ref (%f m)" % _near(wh, 140.0 * B, "wh_ref"))
	var reached: Array = Session.run_progress.reached_ids()
	assert_true(reached.has("doom_warehouse") and reached.has("doom_bar"), "both worlds reached: %s" % str(reached))
	_free(s)
