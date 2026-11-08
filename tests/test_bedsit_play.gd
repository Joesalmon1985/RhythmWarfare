extends TestCase
## The bedsit played by touch (play round 2; docs/bedsit/LAUNCH.md "Playing it"): the running scene (RW_RUN_PATH=bedsit, virtual clock) driven by taps through RunPlay.dispatch_tap,
## the one dispatcher (CONTRACTS.md 5, H5.5), never BedsitNav.press directly. Left and right turn the camera on the spot and hold it still (ruling 35a), the facing reaches the save
## and the homecoming uses it, the top region leaves by the facing's threshold, and the way out (ruling 41) is hit by a tap at its screen position once one rave's three activities
## are done, and not before.

const TMP_SAVE := "user://test_bedsit_play_save.json"
const RAVES := {"N": "space_rave", "E": "dino_rave", "S": "magic_rave", "W": "transport_rave"}
const AT := {"left": Vector2(0.1, 0.5), "right": Vector2(0.9, 0.5), "bottom": Vector2(0.5, 0.86), "top": Vector2(0.5, 0.2)}

var _saved: RunProgress


func _scene() -> Dictionary:
	_saved = Session.run_progress
	for f in [TMP_SAVE, TMP_SAVE + ".tmp"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	for kv in [["RW_RUN_VIRTUAL", "1"], ["RW_RUN_BOT", "perfect"], ["RW_RUN_ROUTES", ""], ["RW_RUN_TAPS", "none"], ["RW_MINIGAME_TAPS", ""], ["RW_RUN_PATH", "bedsit"]]:
		OS.set_environment(kv[0], kv[1])
	Session.run_start_node = ""
	var host := Control.new()
	host.size = Vector2(1152, 648)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = Vector2(1152, 648)
	return {"host": host, "scene": scene}


func _free(d: Dictionary) -> void:
	Session.run_progress = _saved
	for f in [TMP_SAVE, TMP_SAVE + ".tmp"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	(d["host"] as Control).queue_free()
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_TAPS", "RW_MINIGAME_TAPS", "RW_RUN_PATH"]:
		OS.unset_environment(k)


func _run_to(scene: Node, t_end: float) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func _run_until(scene: Node, t_max: float, stop: Callable) -> bool:
	var t: float = scene._vt
	while t < t_max:
		if stop.call():
			return true
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)
	return stop.call()


func _bar(scene: Node) -> float:
	return 4.0 * float(scene.engine.beat_s)


## A tap at fractions `f` of the stage area, through the dispatcher.
func _tap(scene: Node, f: Vector2) -> String:
	var host: Control = scene._stage_host
	return scene.dispatch_tap(host.global_position + host.size * f)


func _region(scene: Node, region: String) -> String:
	var owner := _tap(scene, AT[region])
	assert_eq(owner, "world_regions", "a tap in the %s region is the world regions'" % region)
	assert_eq(str((scene.input_log as Array).back()["target"]), region)
	return owner


func _yaw(scene: Node) -> float:
	return float(scene._exit_pose()["yaw"])


func _yaw_is(scene: Node, f: String, msg: String) -> void:
	var d := fposmod(_yaw(scene) - BedsitNav.yaw_of(f) + 180.0, 360.0) - 180.0
	assert_near(d, 0.0, 0.5, "%s: the camera faces %s (yaw %.2f)" % [msg, f, _yaw(scene)])


## A turn by tap: the facing changes at once (and is in the save); the camera is there after one bar and then holds still (no drift).
func _turn(scene: Node, region: String) -> String:
	_region(scene, region)
	var f: String = scene.bedsit.facing
	assert_eq(Session.run_progress.bedsit_facing(), f, "the facing reaches the save")
	var saved: Variant = JSON.parse_string(FileAccess.get_file_as_string(TMP_SAVE))
	assert_eq(str((saved as Dictionary).get("bedsit_facing", "")), f, "and the save file")
	_run_to(scene, scene._vt + _bar(scene) + 0.05)
	_yaw_is(scene, f, "one bar after the %s tap" % region)
	var y0 := _yaw(scene)
	var c0: Vector3 = scene._exit_pose()["cam"]
	_run_to(scene, scene._vt + _bar(scene))
	assert_near(_yaw(scene), y0, 0.05, "held still a bar later: no drift")
	assert_true((scene._exit_pose()["cam"] as Vector3).distance_to(c0) < 0.02, "the camera stays on the spot")
	return f


func _wait_for_node(scene: Node, id: String) -> bool:
	return _run_until(scene, scene._vt + 6.0 * 64.0 * float(scene.engine.beat_s), func() -> bool: return str(scene.engine.node_id) == id)


func _wait_open(scene: Node) -> void:
	_run_until(scene, scene._vt + 64.0 * float(scene.engine.beat_s), func() -> bool: return scene.selection_open())


# --- turning and leaving ------------------------------------------------------------------------------------------------------

func test_the_regions_turn_the_room_by_tap_and_bottom_stays() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	assert_eq(str(scene.engine.node_id), "bedsit")
	assert_true(scene.bedsit.active, "the bedsit is the scene")
	assert_eq((scene.world_regions as Dictionary).keys().size(), 4, "its four regions are the world regions")
	_run_to(scene, 4.0 * float(scene.engine.beat_s))
	_yaw_is(scene, "N", "the start")
	var seen: Array = []
	for i in 4:
		seen.append(_turn(scene, "right"))
	assert_eq(seen, ["E", "S", "W", "N"], "right turns go east, south, west, north")
	seen.clear()
	for i in 4:
		seen.append(_turn(scene, "left"))
	assert_eq(seen, ["W", "S", "E", "N"], "left turns go west, south, east, north")
	_region(scene, "bottom")
	assert_eq(scene.bedsit.facing, "N", "bottom keeps the facing")
	_region(scene, "top")
	assert_eq(scene.hotspots.selected, "bedsit.threshold_n", "top is the facing's threshold")
	_region(scene, "bottom")
	assert_eq(scene.hotspots.selected, "", "bottom withdraws the pick: stay")
	_region(scene, "top")
	_turn(scene, "right")
	assert_eq(scene.hotspots.selected, "", "a turn withdraws the pick of the old facing")
	var shown: Array = (scene.hotspot_items() as Array).map(func(e: Dictionary) -> String: return str(e["hotspot"]["id"]))
	assert_true(shown.has("bedsit.threshold_e") and not shown.has("bedsit.threshold_n"), "only the facing's threshold is on show: %s" % str(shown))
	assert_eq(scene.dispatch_tap((scene.pad_view.button_rects()[1] as Rect2).get_center()), "pads", "the pads are not the regions")
	_free(d)


func test_each_facing_leaves_for_its_rave_by_tap_and_comes_home_facing_the_same_way() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_run_to(scene, 4.0 * float(scene.engine.beat_s))
	for f in ["N", "E", "S", "W"]:
		_wait_open(scene)
		while scene.bedsit.facing != f:
			_turn(scene, "right")
		_wait_open(scene)
		_region(scene, "top")
		assert_eq(scene.hotspots.selected, "bedsit.threshold_" + f.to_lower(), "%s: the top region picks the threshold" % f)
		assert_true(_wait_for_node(scene, RAVES[f]), "%s: the tap leads to %s (at %s)" % [f, RAVES[f], scene.engine.node_id])
		assert_false(scene.bedsit.active, "%s: away from the bedsit the regions are off" % f)
		assert_true((scene.world_regions as Dictionary).is_empty())
		_wait_open(scene)
		var pre: String = str(RAVES[f]).split("_")[0]
		assert_true(scene.hotspot_select("%s_rave.home" % pre), "%s: the rave's way home" % f)
		assert_true(_wait_for_node(scene, "bedsit"), "%s: home again (at %s)" % [f, scene.engine.node_id])
		assert_eq(Session.run_progress.bedsit_facing(), f, "%s: the save kept the facing" % f)
		assert_eq(scene.bedsit.facing, f, "%s: the homecoming reads it" % f)
		_run_to(scene, scene._vt + 0.2)
		_yaw_is(scene, f, "%s: home" % f)
		var enters: Array = (scene.bedsit.log as Array).filter(func(e: Dictionary) -> bool: return e["kind"] == "enter")
		assert_eq(str(enters.back()["facing"]), f)
	_free(d)


# --- the way out (ruling 41) -------------------------------------------------------------------------------------------------

func test_the_way_out_is_hit_at_its_screen_position_only_once_one_rave_is_done() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_run_to(scene, 4.0 * float(scene.engine.beat_s))
	assert_true(scene.bedsit.way_out_point() == null, "the way out is not in the north picture")
	_turn(scene, "left")
	assert_eq(scene.bedsit.facing, "W")
	var p: Variant = scene.bedsit.way_out_point()
	assert_true(p != null, "the way out is in the west picture (the door)")
	var host: Control = scene._stage_host
	var at: Vector2 = ((p as Vector2) - host.global_position) / host.size
	assert_true(BedsitRoom.gap(scene.world_regions).has_point(at), "it stands in the gap between the regions: %s" % str(at))
	assert_eq(scene.dispatch_tap(p), "world_regions")
	assert_eq(scene.hotspots.selected, "", "closed: a tap on the door does nothing")
	assert_false(scene.run_flag_set(SpaceRaveHost.WAY_OUT_FLAG))
	for pz in RaveSave.PUZZLES:  # one rave's three activities (each is played and tested in its own suite; here their results land in the save)
		Session.run_progress.apply_activity_flag("rave.space.%s" % pz)
	var phase0: int = scene.engine.phase_n
	assert_true(_run_until(scene, scene._vt + 2.0 * 64.0 * float(scene.engine.beat_s), func() -> bool: return int(scene.engine.phase_n) > phase0), "the bedsit's next scene start")
	assert_eq(str(scene.engine.node_id), "bedsit", "nothing touched: the bedsit stays")
	assert_true(scene.run_flag_set(SpaceRaveHost.WAY_OUT_FLAG), "the way out is open")
	assert_eq(scene.bedsit.facing, "W", "still facing west")
	_run_to(scene, scene._vt + 0.2)
	p = scene.bedsit.way_out_point()
	var shown: Array = (scene.hotspot_items() as Array).map(func(e: Dictionary) -> String: return str(e["hotspot"]["id"]))
	assert_true(shown.has(BedsitRoom.WAY_OUT), "it is on show")
	assert_eq(scene.dispatch_tap(p), "world_regions")
	assert_eq(str((scene.input_log as Array).back()["target"]), BedsitRoom.WAY_OUT, "the tap at its screen position hits it")
	assert_eq(scene.hotspots.selected, BedsitRoom.WAY_OUT)
	_tap(scene, AT["top"])
	assert_eq(scene.hotspots.selected, "bedsit.threshold_w", "the top of the same door is still the Transport threshold")
	scene.dispatch_tap(p)
	assert_eq(scene.hotspots.selected, BedsitRoom.WAY_OUT)
	assert_true(_wait_for_node(scene, "bedsit.end"), "the way out leads to bedsit.end (at %s)" % scene.engine.node_id)
	_free(d)
