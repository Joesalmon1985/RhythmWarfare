extends TestCase
## The rails and activities on the real run scene (virtual clock, no audio): a perfect phase climbs the Warehouse rail on the stage, a missed one goes down the bad rail with the
## queasy look and the sick beat, the route window lights the exits and the world swap is a walk through the passage frame, and the crowd's activities follow the run's energy.

const BEAT := 60.0 / 174.0
const TMP_SAVE := "user://test_run_rail_save.json"


func _scene(size: Vector2, bot: String, routes := "", start := "") -> Dictionary:
	var saved := Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", bot)
	OS.set_environment("RW_RUN_ROUTES", routes)
	if start != "":
		OS.set_environment("RW_RUN_START", start)
	Session.run_start_node = ""
	var host := Control.new()
	host.size = size
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = size
	return {"host": host, "scene": scene, "saved": saved}


func _free(d: Dictionary) -> void:
	Session.run_progress = d["saved"]
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	(d["host"] as Control).queue_free()
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


func test_a_perfect_phase_climbs_the_warehouse_rail_on_the_stage() -> void:
	var d := _scene(Vector2(1152, 648), "perfect", "right")
	var scene: Node = d["scene"]
	_run_to(scene, 62.0 * BEAT)
	var places: Array = (scene.journey.log as Array).map(func(e: Dictionary) -> String: return e["place"])
	assert_eq(places, ["steps", "stage", "balcony", "booth"], "four passes, four places up the rail")
	var st: StoryStage = scene.stages["night_one"]["stage"]
	assert_eq(st.player.pose_at(58.0 * BEAT)["sector"], "balcony", "the camera is on the balcony before the last step")
	assert_eq(st.player.role_at(40.0 * BEAT), "on_stage")
	assert_true((scene.journey_log as Array).any(func(a: Dictionary) -> bool: return a["action"] == "player_look"), "glances reach the stage")
	assert_true((scene.journey_log as Array).any(func(a: Dictionary) -> bool: return a["action"] == "player_walk"), "and strolls")
	_free(d)


func test_a_missed_phase_goes_down_the_bad_rail_with_the_sick_beat() -> void:
	var d := _scene(Vector2(1152, 648), "none", "right")
	var scene: Node = d["scene"]
	_run_to(scene, 50.0 * BEAT)
	var places: Array = (scene.journey.log as Array).map(func(e: Dictionary) -> String: return e["place"])
	assert_eq(places, ["floor_edge", "corridor", "cubicle"])
	var st: StoryStage = scene.stages["night_one"]["stage"]
	assert_true(st.player.queasy_at(46.0 * BEAT) > 0.0, "the queasy look has begun")
	assert_eq(st.player.pose_at(62.0 * BEAT)["sector"], "cubicle_b", "the cubicle at the bottom of the rail")
	_free(d)


func test_a_path_inside_a_world_is_a_door_walk_with_no_passage_frame() -> void:
	var d := _scene(Vector2(1152, 648), "perfect", "right")  # the floor: right is the bar
	var scene: Node = d["scene"]
	_run_to(scene, 50.0 * BEAT)
	assert_true(scene._exits.visible, "the doorways are lit while the window is open")
	assert_eq(scene._exits.items.size(), 2, "one lit door per path: the bar and the balcony")
	assert_eq(scene._route_buttons.size(), 2, "and the touch arrows stay")
	assert_eq((scene._route_buttons["right"] as Button).text.begins_with(">  The Bar"), true, "the button names the room")
	assert_true((scene._route_buttons["right"] as Button).text.contains("[CHOSEN]") or (scene._route_buttons["right"] as Button).text.contains("[DEFAULT]"))
	_run_to(scene, 60.0 * BEAT)
	var walked_before: int = (scene.journey_log as Array).filter(func(a: Dictionary) -> bool: return a["action"] == "player_move" and float(a["t0"]) > 60.5 * BEAT).size()
	assert_eq(walked_before, 0, "no door walk before beat 61")
	_run_to(scene, 63.9 * BEAT)
	assert_eq(scene._passage.aperture, 1.0, "no frame: the picture stays open")
	assert_eq(scene.active_world, "night_one")
	var door_moves: Array = (scene.journey_log as Array).filter(func(a: Dictionary) -> bool: return a["action"] == "player_move" and absf(float(a["t0"]) - 61.0 * BEAT) < 0.05)
	assert_eq(door_moves.size(), 1, "one door walk, started at beat 61")
	assert_eq((door_moves[0]["args"] as Dictionary)["to"], "bar_door", "toward the bar's door")
	assert_false(bool((door_moves[0]["args"] as Dictionary).get("cut", false)), "a walk, not a cut")
	_run_to(scene, 64.4 * BEAT)
	assert_eq(scene.engine.node_id, "warehouse.bar", "the next scene began on the downbeat")
	assert_eq(scene.active_world, "night_one", "the same world stage stays")
	assert_eq(scene.stages.size(), 1, "no second stage was built")
	assert_eq(scene.journey.rail.node_id, "warehouse.bar", "the new scene's rail starts")
	assert_false(scene._exits.visible, "the lights go out with the window")
	var st: StoryStage = scene.stages["night_one"]["stage"]
	assert_true(str(st.player.pose_at(64.4 * BEAT)["sector"]) != "bar", "still walking through the door a little after the downbeat")
	_run_to(scene, 76.0 * BEAT)
	assert_eq(st.player.pose_at(76.0 * BEAT)["sector"], "bar", "arrived in the bar")
	assert_eq(Session.run_progress.reached_ids(), ["warehouse"], "reached stays per world: the bar is not a level of its own")
	_free(d)


func test_the_world_swap_keeps_the_passage_frame() -> void:
	var d := _scene(Vector2(1152, 648), "perfect", "left", "mothership.exit")  # the airlock: left is the hospital
	var scene: Node = d["scene"]
	_run_to(scene, 50.0 * BEAT)
	assert_true(scene._exits.visible)
	assert_eq(scene._exits.items.size(), 2, "one doorway per candidate world")
	assert_eq(scene._passage.aperture, 1.0, "the frame is open mid-window")
	_run_to(scene, 63.9 * BEAT)
	assert_true(scene._passage.aperture < 0.3, "shut to the doorway on the last beat before the swap (%f)" % scene._passage.aperture)
	assert_eq(scene.active_world, "mothership")
	_run_to(scene, 64.4 * BEAT)
	assert_eq(scene.engine.node_id, "hospital")
	assert_eq(scene.active_world, "hospital", "the world swapped on the downbeat")
	assert_true(scene._passage.aperture < 0.5, "and opens from the doorway")
	assert_false(scene._exits.visible, "the lights go out with the window")
	var st: StoryStage = scene.stages["hospital"]["stage"]
	assert_eq(st.player.pose_at(62.0 * BEAT)["sector"], "ward", "in at the ward door")
	assert_eq(Session.run_progress.reached_ids().has("hospital"), true)
	_run_to(scene, 80.0 * BEAT)
	assert_eq(scene._passage.aperture, 1.0, "fully open")
	assert_eq(st.player.pose_at(80.0 * BEAT)["sector"], "bed", "arrived at the new world's start waypoint")
	_free(d)


func test_the_activities_follow_the_crowd_energy() -> void:
	var d := _scene(Vector2(1152, 648), "none", "right")
	var scene: Node = d["scene"]
	_run_to(scene, 20.0 * BEAT)
	var st: StoryStage = scene.stages["night_one"]["stage"]
	assert_true(scene.engine.energy < 60.0, "missing the first block costs energy (%f)" % scene.engine.energy)
	assert_near(st.energy, scene.engine.energy, 0.01, "the stage reads the run's energy")
	var crowd: StoryCrowd = st.crowds["main"]
	var quiet := {}
	var high := {}
	for id in crowd.actors:
		var a: Dictionary = crowd.actors[id]
		if str(a["lock"]) != "":
			continue
		var q := crowd.pick_activity(a, "quiet")
		var h := crowd.pick_activity(a, "euphoric")
		quiet[q] = int(quiet.get(q, 0)) + 1
		high[h] = int(high.get(h, 0)) + 1
	assert_true(JSON.stringify(quiet) != JSON.stringify(high), "the quiet and the euphoric bands give the crowd different things to do: %s vs %s" % [JSON.stringify(quiet), JSON.stringify(high)])
	assert_eq(st.data.band_of(10.0), "quiet")
	assert_eq(st.data.band_of(95.0), "euphoric")
	_free(d)
