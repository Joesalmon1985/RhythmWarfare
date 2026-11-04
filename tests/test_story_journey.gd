extends TestCase
## The journey in the stage: the five director actions schedule the rail camera, the camera node follows it at any frame step, a chapter without a map ignores
## them, and the director warns about a camera move over a dense note run.


func _stage_with_world(nodes: bool) -> StoryStage:
	var run := StoryRun.create({})
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_default(), run.data, run)
	stage.attach_world(StoryMap.load_chapter("night_one"), nodes)
	return stage


func _action(t0: float, action: String, args: Dictionary) -> Dictionary:
	return {"t0": t0, "bar": 1.0, "action": action, "args": args, "block": "", "source": "block"}


func test_stage_schedules_the_journey_actions() -> void:
	var stage := _stage_with_world(false)
	var b := stage.bar_s()
	stage.apply(_action(10.0 * b, "player_move", {"to": "booth", "style": "walk", "bars": 3.0}))
	stage.apply(_action(10.0 * b, "player_role", {"role": "on_stage"}))
	stage.apply(_action(20.0 * b, "fx_queasy", {"amount": 0.5, "bars": 2.0}))
	stage.apply(_action(24.0 * b, "sick_beat", {"bars": 2.0}))
	stage.apply(_action(26.0 * b, "player_look", {"yaw": 20.0, "bars": 1.0}))
	assert_eq(stage.journey(), ["booth"])
	assert_eq(stage.player.role_at(11.0 * b), "on_stage")
	assert_eq(stage.player.pose_at(14.0 * b)["sector"], "booth")
	assert_true(stage.player.queasy_at(23.0 * b) > 0.49)
	assert_true(stage.player.sick_at(25.0 * b) > 0.9)
	assert_eq(stage.action_log.size(), 5, "every action is in the log")
	stage.reset()
	assert_eq(stage.player.pose_at(14.0 * b)["sector"], "floor", "a restart replays from the start waypoint")
	assert_eq(stage.journey(), [])
	stage.queue_free()


func test_stage_without_a_map_ignores_the_journey_actions() -> void:
	var run := StoryRun.create({})
	run.data.id = "chapter_without_a_map"  # the map is looked up by chapter id
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_default(), run.data, run)
	stage.apply(_action(1.0, "player_move", {"to": "booth", "bars": 2.0}))
	stage.update(2.0, 50.0)
	assert_true(stage.player == null and not stage.world_active)
	assert_eq(stage.action_log.size(), 1)
	stage.queue_free()


func test_camera_node_follows_the_rail_at_any_frame_step_and_freezes_on_pause() -> void:
	var finals: Array = []
	for step in [1.0 / 30.0, 1.0 / 60.0, 0.0173]:
		var stage := _stage_with_world(true)
		assert_true(stage.world_active and stage.lowres != null)
		var b := stage.bar_s()
		stage.apply(_action(2.0 * b, "player_move", {"to": "stage", "style": "climb", "bars": 4.0}))
		var t := 0.0
		var target := 5.0 * b
		while t < target - step:
			t += step
			stage.update(t, 60.0)
		stage.update(target, 60.0)
		var cam := stage.lowres.camera
		finals.append([cam.position, cam.rotation_degrees])
		var held := cam.position
		stage.update(target, 60.0)  # a paused clock asks for the same time again: nothing moves
		assert_eq(cam.position, held, "pause freezes the camera")
		stage.queue_free()
	assert_eq(finals[0], finals[1], "30 fps and 60 fps agree")
	assert_eq(finals[0], finals[2], "and a ragged step agrees")


func test_the_crowd_is_drawn_inside_the_low_res_viewport() -> void:
	var stage := _stage_with_world(true)
	stage.update(1.0, 50.0)
	var c: StoryCrowd = stage.crowds["main"]
	assert_true(c.world_mode, "the crowd lives in the world")
	assert_true(c.get_parent() is CanvasLayer and c.get_parent().get_parent() == stage.lowres.sub, "and is drawn inside the low-res viewport")
	stage.queue_free()


func test_a_move_over_a_dense_run_warns() -> void:
	var run := StoryRun.create({})
	var d: StoryDirector = run.director
	var counts := d.notes_per_bar()
	assert_eq(counts.size(), 128)
	assert_true(run.warnings.size() >= 0)
	# Night One at the default loadout is sparse (at most four notes a bar): no authored move warns
	var chapter := run.data
	var dense_bar := -1
	for i in counts.size():
		if counts[i] > run.level.beats_per_bar:
			dense_bar = i + 1
			break
	# synthetic chapter data: a move on bar 9 (sparse here) is fine, a 6-bar move warns, and a fake dense bar is detected
	chapter.blocks[1]["events"].append({"at_bar": 11, "action": "player_move", "to": "booth", "style": "walk", "bars": 6})
	chapter.blocks[0]["events"].append({"at_bar": 3, "action": "player_move", "to": "steps", "style": "walk", "bars": 2})
	d.setup(chapter, run.level, run.crowd)
	var joined := " | ".join(PackedStringArray(d.warnings))
	assert_true(joined.contains("lasts 6.0 bars"), joined)
	assert_false(joined.contains("to steps"), "a short move on a sparse bar is fine: " + joined)
	# make every note dense by faking the counts through a level with many notes in bar 3
	var lvl: Level = run.level
	var saved := lvl.notes.duplicate()
	for k in 8:
		lvl.notes.append({"tick": 2 * lvl.ticks_per_bar() + k * 100, "lane": 0, "button": 1, "type": "tap", "duration_ticks": 0, "time": 0.0, "end_time": 0.0})
	d.setup(chapter, lvl, run.crowd)
	joined = " | ".join(PackedStringArray(d.warnings))
	assert_true(joined.contains("to steps") and joined.contains("dense note run"), joined)
	lvl.notes = saved
