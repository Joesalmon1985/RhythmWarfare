extends TestCase
## The rails and activities on the real run scene (virtual clock, no audio): a perfect phase climbs the Warehouse rail on the stage, a missed one goes down the bad rail with the
## queasy look and the sick beat, the route window lights the exits and the world swap is a walk through the passage frame, and the crowd's activities follow the run's energy.

const BEAT := 60.0 / 174.0
const TMP_SAVE := "user://test_run_rail_save.json"


func _scene(size: Vector2, bot: String, routes := "") -> Dictionary:
	var saved := Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", bot)
	OS.set_environment("RW_RUN_ROUTES", routes)
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


func _run_to(scene: Node, t_end: float) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func test_a_perfect_phase_climbs_the_warehouse_rail_on_the_stage() -> void:
	var d := _scene(Vector2(1152, 648), "perfect", "up")
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
	var d := _scene(Vector2(1152, 648), "none", "up")
	var scene: Node = d["scene"]
	_run_to(scene, 50.0 * BEAT)
	var places: Array = (scene.journey.log as Array).map(func(e: Dictionary) -> String: return e["place"])
	assert_eq(places, ["floor_edge", "corridor", "cubicle"])
	var st: StoryStage = scene.stages["night_one"]["stage"]
	assert_true(st.player.queasy_at(46.0 * BEAT) > 0.0, "the queasy look has begun")
	assert_eq(st.player.pose_at(62.0 * BEAT)["sector"], "cubicle_b", "the cubicle at the bottom of the rail")
	_free(d)


func test_the_route_window_lights_the_exits_and_the_swap_walks_through_the_frame() -> void:
	var d := _scene(Vector2(1152, 648), "perfect", "up")
	var scene: Node = d["scene"]
	_run_to(scene, 50.0 * BEAT)
	assert_true(scene._exits.visible, "the exits are lit while the window is open")
	assert_eq(scene._exits.items.size(), 2, "one doorway per candidate world")
	assert_eq(scene._route_buttons.size(), 2, "and the touch arrows stay")
	assert_eq(scene._passage.aperture, 1.0, "the frame is open mid-window")
	_run_to(scene, 63.9 * BEAT)
	assert_true(scene._passage.aperture < 0.3, "shut to the doorway on the last beat before the swap (%f)" % scene._passage.aperture)
	assert_eq(scene.active_world, "night_one")
	_run_to(scene, 64.4 * BEAT)
	assert_eq(scene.active_world, "mothership", "the world swapped on the downbeat")
	assert_true(scene._passage.aperture < 0.5, "and opens from the doorway")
	assert_false(scene._exits.visible, "the lights go out with the window")
	var st: StoryStage = scene.stages["mothership"]["stage"]
	assert_eq(st.player.pose_at(62.0 * BEAT)["sector"], "airlock", "in from the airlock")
	assert_true(str(st.player.pose_at(64.0 * BEAT)["sector"]) != "deck", "still walking in on the downbeat")
	_run_to(scene, 80.0 * BEAT)
	assert_eq(scene._passage.aperture, 1.0, "fully open")
	assert_eq(st.player.pose_at(80.0 * BEAT)["sector"], "deck", "arrived at the new world's start waypoint")
	_free(d)


func test_the_activities_follow_the_crowd_energy() -> void:
	var d := _scene(Vector2(1152, 648), "none", "up")
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
