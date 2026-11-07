extends TestCase
## A real cut between two Doom geography worlds (docs/engine/GEOGRAPHY_WORLDS.md, hook H1.6), on the real run scene with the overlay (RW_DOOM_WORLDS=1): from the Warehouse floor
## the Bar's guide (left): the lock handler walks the Warehouse's `left` polyline to its threshold by the boundary, the passage frame shuts, the stage swaps to doom_bar on the
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
	assert_eq(w1.size(), 1, "the lock handler walked to the Warehouse's left threshold")
	if w1.size() == 1:
		assert_near(float(w1[0]["t0"]), 61.0 * B, 0.01, "from beat 61")
		assert_eq(str(w1[0]["args"]["to"]), str(wh_rail["exits"]["left"]), "to the threshold wh_bar_door")
		assert_eq(w1[0]["args"]["via"], wh_rail["routes"]["left"]["via"], "along the Warehouse's left polyline")
	var wh: StoryStage = scene.stages["doom_warehouse"]["stage"]
	assert_true(_near(wh, 64.0 * B, "wh_bar_door") < 0.05, "at the threshold on the boundary (%f m)" % _near(wh, 64.0 * B, "wh_bar_door"))
	assert_true(scene._passage.aperture < 0.3, "the frame shut to the doorway before the swap (%f)" % scene._passage.aperture)
	assert_eq(scene.active_world, "doom_warehouse")
	_run_to(scene, 64.4 * B)
	assert_eq(scene.engine.node_id, "doom_bar")
	assert_eq(scene.active_world, "doom_bar", "the stage swapped to the Bar on the downbeat")
	var bar: StoryStage = scene.stages["doom_bar"]["stage"]
	_run_to(scene, 76.0 * B)
	assert_true(_near(bar, 76.0 * B, "wb_ref") < 0.05, "the arrival walked home to wb_ref (%f m)" % _near(bar, 76.0 * B, "wb_ref"))
	assert_eq(scene._passage.aperture, 1.0, "the frame is open again")
	# the Bar, phase 2: the Floor's guide, back to the Warehouse
	_run_to(scene, 127.9 * B)
	assert_eq(scene.engine.selected_route(), "doom_warehouse", "the scripted tap is on the Floor's guide (left)")
	var w2 := _walks(scene, "doom_bar")
	assert_eq(w2.size(), 1, "the lock handler walked to the Bar's left threshold")
	if w2.size() == 1:
		assert_near(float(w2[0]["t0"]), 125.0 * B, 0.01, "from beat 61 of the Bar's phase")
		assert_eq(str(w2[0]["args"]["to"]), str(bar_rail["exits"]["left"]), "to the threshold wb_floor_door")
		assert_eq(w2[0]["args"]["via"], bar_rail["routes"]["left"]["via"], "along the Bar's left polyline")
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
