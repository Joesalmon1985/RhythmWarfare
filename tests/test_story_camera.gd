extends TestCase
## The moving camera: rooms (views), forward dolly and turn moves, the active crowd following the camera, determinism at a given song
## time, restart, and Night One staying fixed. Uses a synthetic second room built from Night One's own art so it needs no new assets.


func _stage_with_room(extra: bool) -> Dictionary:
	var run := StoryRun.create({})
	var assets := StoryAssets.load_default()
	if extra:
		var st: Dictionary = assets.manifest["stage"]
		st["views"] = [{"id": "alt", "layers": st["layers"], "anchors": st["anchors"].duplicate(true), "pieces": [], "palette_hint": "cool"}]
		st["views"][0]["anchors"]["vanish"] = [500, 140]
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(assets, run.data, run)
	return {"stage": stage, "run": run}


func _move(stage: StoryStage, view: String, style: String, t0: float, bars := 2.0) -> void:
	stage.apply({"t0": t0, "bar": 1.0, "action": "move_to", "args": {"view": view, "style": style, "bars": bars}, "block": "", "source": "block"})


func test_night_one_stays_fixed() -> void:
	var ctx := _stage_with_room(false)
	var stage: StoryStage = ctx["stage"]
	assert_false(stage.moving_camera)
	assert_eq(stage.views.size(), 1)
	_move(stage, "alt", "walk", 1.0)  # an unknown room or a fixed camera ignores the move
	assert_eq(stage.current_view, "main")
	stage.update(3.0, 50.0)
	assert_eq(stage.views["main"].position, Vector2.ZERO, "no sway on a fixed camera")
	stage.queue_free()


func test_walk_dollies_into_the_next_room_and_the_active_crowd_follows() -> void:
	var ctx := _stage_with_room(true)
	var stage: StoryStage = ctx["stage"]
	assert_true(stage.moving_camera)
	assert_eq(stage.views.size(), 2)
	var bar_s := stage.bar_s()
	stage.update(0.5, 50.0)
	assert_true(stage.views["main"].visible)
	assert_false(stage.views["alt"].visible, "the other room is not drawn")
	_move(stage, "alt", "walk", 1.0, 2.0)
	assert_eq(stage.current_view, "alt", "actions after the move direct the new room")
	assert_true(stage.crowd == stage.views["alt"].crowd)
	stage.update(0.9, 50.0)
	assert_true(stage.views["main"].visible and not stage.views["alt"].visible, "before t0 the old room is still alone on screen")
	stage.update(1.0 + bar_s, 50.0)  # half way through the move
	assert_true(stage.views["main"].visible and stage.views["alt"].visible, "both rooms during the move")
	var out_scale: float = stage.views["main"].scale.x
	var in_scale: float = stage.views["alt"].scale.x
	assert_true(out_scale > 1.2, "the room we leave swells toward its vanishing point (%.2f)" % out_scale)
	assert_true(in_scale < 1.0 and in_scale > 0.55, "the room we arrive in grows into place (%.2f)" % in_scale)
	assert_true(stage.views["main"].modulate.a < 1.0 and stage.views["alt"].modulate.a > 0.5, "crossfade")
	stage.update(1.0 + 2.0 * bar_s + 0.05, 50.0)
	assert_false(stage.views["main"].visible)
	assert_true(stage.views["alt"].visible)
	assert_near(stage.views["alt"].modulate.a, 1.0, 0.001)
	assert_near(stage.views["alt"].scale.x, 1.0, 0.001, "settled at full size")
	stage.queue_free()


func test_turn_slides_rooms_past_each_other() -> void:
	var ctx := _stage_with_room(true)
	var stage: StoryStage = ctx["stage"]
	_move(stage, "alt", "turn_right", 1.0, 2.0)
	stage.update(1.0 + stage.bar_s(), 50.0)
	var a: float = stage.views["main"].position.x
	var b: float = stage.views["alt"].position.x
	assert_true(a < -300.0 and b > 300.0, "the old room slides out left (%.0f) as the new one slides in from the right (%.0f)" % [a, b])
	stage.update(1.0 + 2.0 * stage.bar_s() + 0.01, 50.0)
	assert_near(stage.views["alt"].position.x, 0.0, 6.0, "arrives centred")
	stage.queue_free()


func test_camera_is_a_function_of_song_time_and_restarts() -> void:
	var ctx := _stage_with_room(true)
	var stage: StoryStage = ctx["stage"]
	_move(stage, "alt", "walk", 1.0, 2.0)
	var t := 1.0 + 0.7 * stage.bar_s()
	stage.update(t, 50.0)
	var first: Array = [stage.views["main"].scale, stage.views["main"].position, stage.views["alt"].scale, stage.views["alt"].modulate.a]
	stage.update(t + 0.4, 50.0)
	stage.update(t, 50.0)  # the same song time again (a paused frame): the same camera
	var again: Array = [stage.views["main"].scale, stage.views["main"].position, stage.views["alt"].scale, stage.views["alt"].modulate.a]
	assert_eq(again, first, "no hidden state beyond song time")
	stage.reset()
	assert_eq(stage.current_view, "main", "restart returns to the first room")
	stage.update(0.2, 50.0)
	assert_true(stage.views["main"].visible and not stage.views["alt"].visible)
	stage.queue_free()


func test_camera_look_and_push_return_to_rest() -> void:
	var ctx := _stage_with_room(true)
	var stage: StoryStage = ctx["stage"]
	stage.reduced = true  # no sway: only the authored move shows
	stage.apply({"t0": 1.0, "bar": 1.0, "action": "camera_push", "args": {"zoom": 0.2, "bars": 2}, "block": "", "source": "block"})
	stage.update(1.0 + stage.bar_s(), 50.0)
	assert_near(stage.views["main"].scale.x, 1.2, 0.01, "a punch-in at its peak")
	stage.update(1.0 + 2.0 * stage.bar_s() + 0.1, 50.0)
	assert_near(stage.views["main"].scale.x, 1.0, 0.001, "and back to rest")
	stage.queue_free()
