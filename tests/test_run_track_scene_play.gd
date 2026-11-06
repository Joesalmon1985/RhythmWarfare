extends TestCase
## Track scenes in the real run scene (RunPlay) on its virtual clock, with a synthetic pack: the bot plays a track scene to its default end, or leaves it at the first open lap (RW_RUN_TRACK_EXIT=first);
## on an open lap before the last the doors show staying until an exit is touched (route_window.last false); the tempo event gives the stages and the hotspot views the track's beat; the walks'
## summary lists the track scene with its laps.

const Fx := preload("res://tests/fixtures/track_scenes/track_scene_fixtures.gd")
const TMP_SAVE := "user://test_track_play_save.json"

var _saved: RunProgress


func _scene(env: Dictionary) -> Dictionary:
	Fx.clear()
	Fx.write_pack("acuna_go_back", Fx.go_back_spec())
	RunTrackScenes.enabled = 1
	RunTrackScenes.packs_dir_override = Fx.root()
	RunTrackScenes.json_path_override = Fx.write_scenes({"main": {"warehouse": {"track": "acuna_go_back"}}})
	_saved = Session.run_progress
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TMP_SAVE))
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "right")
	OS.set_environment("RW_RUN_TAPS", "scripted")
	for k in env:
		OS.set_environment(str(k), str(env[k]))
	Session.run_start_node = ""
	Session.run_start_path = ""
	var host := Control.new()
	host.size = Vector2(844, 390)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = host.size
	return {"host": host, "scene": scene, "env": env.keys()}


func _free(d: Dictionary) -> void:
	(d["host"] as Control).queue_free()
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_TAPS"] + (d["env"] as Array):
		OS.unset_environment(str(k))
	RunTrackScenes.enabled = -1
	RunTrackScenes.packs_dir_override = ""
	RunTrackScenes.json_path_override = ""
	if _saved != null:
		Session.run_progress = _saved
		_saved = null
	DirAccess.remove_absolute(ProjectSettings.globalize_path(TMP_SAVE))
	Fx.clear()


func _run_until(scene: Node, t_end: float, stop: Callable, each: Callable = Callable()) -> void:
	var t: float = scene._vt
	while t < t_end and not stop.call():
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)
		if each.is_valid():
			each.call(t)


func test_the_bot_plays_a_track_scene_to_its_default_end_and_the_doors_show_staying_on_open_laps() -> void:
	var d := _scene({})
	var scene: Node = d["scene"]
	var e: RunEngine = scene.engine
	assert_true(e.is_track_scene(), "the warehouse is a track scene")
	var beat := e.beat_s
	var lap_s := 64.0 * beat
	var seen := {"stay": false, "bpm": 0.0, "hv": 0.0, "last_default": false}
	var each := func(t: float) -> void:
		var en: RunEngine = scene.engine
		if en.node_id != "warehouse":
			return
		var c: Dictionary = scene.choice_state()
		if en.lap == 2 and en.window_open and en.phase_beat_at(t) > 49.0 and en.phase_beat_at(t) < 50.0:
			seen["stay"] = str(c.get("current", "x")) == "" and str(c.get("dest", "")) == "warehouse"
			var st: StoryStage = scene.stages[scene.active_world]["stage"]
			seen["bpm"] = st.bpm
			if scene.stages[scene.active_world].has("hotspot_view"):
				seen["hv"] = (scene.stages[scene.active_world]["hotspot_view"] as HotspotView).beat_s
		if en.lap == 4 and en.window_open and en.phase_beat_at(t) > 49.0 and en.phase_beat_at(t) < 50.0:
			seen["last_default"] = str(c.get("current", "")) != ""
	_run_until(scene, 4.0 * lap_s + 5.0, func() -> bool: return scene.engine.scene_index() >= 2, each)
	assert_eq(scene.engine.node_id, "warehouse.bar", "left by the scripted route")
	assert_true(seen["stay"], "lap 2's window, nothing touched: no door is the way, the destination is the room itself")
	assert_true(seen["last_default"], "the final lap's window shows the default as today")
	assert_near(float(seen["bpm"]), 174.0032, 1e-6, "the stage dances at the track's tempo")
	if float(seen["hv"]) > 0.0:
		assert_near(float(seen["hv"]), beat, 1e-12, "the hotspot view's beat is the track's")
	var tr: Array = scene.summary()["tracks"]
	assert_eq(tr.size(), 1)
	assert_eq(str(tr[0]["node"]), "warehouse")
	assert_eq(int(tr[0]["laps"]), 4, "played to the default end: all four laps")
	assert_eq(int(tr[0]["planned"]), 4)
	assert_false(bool(tr[0]["left_early"]))
	assert_eq(str(tr[0].get("end", "")), "route")
	assert_near(float(tr[0]["seconds"]), 4.0 * lap_s, 0.001)
	for w in scene.stages:
		assert_near((scene.stages[w]["stage"] as StoryStage).bpm, 174.0, 1e-9, "back at the run's tempo after it")
	_free(d)


func test_the_bot_leaves_at_the_first_open_lap_when_asked() -> void:
	var d := _scene({"RW_RUN_TRACK_EXIT": "first"})
	var scene: Node = d["scene"]
	var lap_s := 64.0 * (scene.engine as RunEngine).beat_s
	_run_until(scene, 4.0 * lap_s + 5.0, func() -> bool: return scene.engine.scene_index() >= 2)
	assert_eq(scene.engine.node_id, "warehouse.bar")
	var tr: Array = scene.summary()["tracks"]
	assert_eq(int(tr[0]["laps"]), 2, "left at lap 2, the first open lap")
	assert_true(bool(tr[0]["left_early"]))
	assert_near(float(tr[0]["seconds"]), 2.0 * lap_s, 0.001)
	_free(d)
