extends TestCase
## The run scene driven headless on its virtual clock (no audio): the route arrows are real buttons clear of the pads in a phone-sized landscape view,
## a tap changes the choice, the chosen level is entered on the downbeat and saved as reached, and a world swap keeps the beat grid.


var _saved: RunProgress
const TMP_SAVE := "user://test_run_scene_save.json"


func _isolate_save() -> void:  # the tests never touch the real save
	_saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")


func _restore_save() -> void:
	if _saved != null:
		Session.run_progress = _saved
		_saved = null
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)


func _scene(size: Vector2, start := "") -> Dictionary:
	_isolate_save()
	if start != "":
		OS.set_environment("RW_RUN_START", start)
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	Session.run_start_node = ""
	var host := Control.new()
	host.size = size
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = size
	return {"host": host, "scene": scene}


func _free(d: Dictionary) -> void:
	_restore_save()
	(d["host"] as Control).queue_free()
	OS.set_environment("RW_RUN_VIRTUAL", "")
	OS.set_environment("RW_RUN_BOT", "")
	OS.unset_environment("RW_RUN_START")


func _run_to(scene: Node, t_end: float) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func test_route_arrows_are_touch_targets_clear_of_the_pads() -> void:
	var d := _scene(Vector2(844, 390))
	var scene: Node = d["scene"]
	var beat: float = 60.0 / 174.0
	_run_to(scene, 52.0 * beat)
	var btns: Dictionary = scene._route_buttons
	assert_true(btns.size() >= 2, "at least two arrows are shown throughout beats 49 to 64")
	var pad_rects: Dictionary = scene.pad_view.button_rects()
	for dir in btns:
		var b: Button = btns[dir]
		var r := Rect2(b.global_position, b.size)
		assert_true(r.size.x >= 100.0 and r.size.y >= 48.0, "%s arrow is a big enough target (%s)" % [dir, str(r.size)])
		for p in pad_rects:
			assert_false(r.intersects(pad_rects[p] as Rect2), "the %s arrow does not touch pad %d" % [dir, p])
		assert_true(Rect2(Vector2.ZERO, Vector2(844, 390)).encloses(r), "%s arrow is on screen" % dir)
	var keys: Array = btns.keys()
	if keys.size() >= 2:
		var first := (btns[keys[0]] as Button)
		var second := (btns[keys[1]] as Button)
		assert_false(Rect2(first.global_position, first.size).intersects(Rect2(second.global_position, second.size)), "the arrows do not overlap each other")
		second.pressed.emit()
		assert_eq(scene.engine.choice, str(second.get_meta("to")), "tapping an arrow selects it")
		assert_true(second.text.contains("CHOSEN"))
		first.pressed.emit()
		assert_eq(scene.engine.choice, str(first.get_meta("to")), "and it can be changed")
	_free(d)


func test_the_chosen_world_starts_on_the_downbeat_and_is_saved_as_reached() -> void:
	var d := _scene(Vector2(1152, 648), "warehouse.exit")  # the scene that carries the Warehouse's exits
	var scene: Node = d["scene"]
	var beat: float = 60.0 / 174.0
	_run_to(scene, 54.0 * beat)
	assert_true(scene.engine.choose_dir("right"))
	var dest: String = scene.engine.selected_route()
	assert_eq(dest, "underworld")
	_run_to(scene, 64.0 * beat - 0.05)
	assert_eq(scene.engine.node_id, "warehouse.exit", "still on the same scene just before the downbeat")
	_run_to(scene, 64.0 * beat + 0.2)
	assert_eq(scene.engine.node_id, "underworld", "a world exit enters the next world's entry scene")
	assert_eq(scene.engine.stage, 0, "drums alone again")
	assert_true(Session.run_progress.is_reached("underworld"), "saved as reached on entry")
	assert_eq(scene.active_world, "underworld", "the world swapped with the level")
	assert_eq((scene.phase_log[1] as Dictionary)["t"], 64.0 * beat, "on the exact downbeat: the grid never restarted")
	_free(d)


func test_a_scene_inside_a_world_is_not_a_reached_level_and_the_hud_names_it() -> void:
	var d := _scene(Vector2(1152, 648))
	var scene: Node = d["scene"]
	var beat: float = 60.0 / 174.0
	_run_to(scene, 54.0 * beat)
	assert_true(scene.engine.choose_dir("up"))
	assert_eq(scene.engine.selected_route(), "warehouse.balcony")
	_run_to(scene, 64.0 * beat + 0.2)
	assert_eq(scene.engine.node_id, "warehouse.balcony")
	assert_eq(Session.run_progress.reached_ids(), ["warehouse"], "the save has worlds only: the balcony is not a level")
	assert_false(Session.run_progress.is_reached("warehouse.balcony"))
	var node: Dictionary = scene.data.nodes[scene.engine.node_id]
	assert_eq(node["world_title"], "Warehouse")
	assert_eq(node["title"], "The Balcony", "the HUD's second line is the room")
	assert_eq(scene.hud.title_card["text"], "THE BALCONY", "the title card names the room")
	assert_eq(scene.hud.title_card["kicker"], "WAREHOUSE", "under the world")
	_free(d)


func test_the_loss_and_level_screens_build_and_offer_retry_and_reached_levels() -> void:
	_isolate_save()
	Session.run_result = {"node": "mothership.reactor", "phases": 2, "energy": 0.0, "reason": "the crowd left"}
	Session.run_progress.enter("mothership")
	for path in ["res://src/run/run_over.tscn", "res://src/run/run_levels.tscn"]:
		var host := Control.new()
		host.size = Vector2(844, 390)
		tree.root.add_child(host)
		var scene: Control = (load(path) as PackedScene).instantiate()
		host.add_child(scene)
		var texts: Array = []
		var stack: Array = [scene]
		while not stack.is_empty():
			var n: Node = stack.pop_back()
			if n is Button:
				texts.append((n as Button).text)
			stack.append_array(n.get_children())
		if path.ends_with("run_over.tscn"):
			assert_true(texts.any(func(t: String) -> bool: return t.begins_with("Retry The Mothership")), "retry from the world's entry scene: " + str(texts))
			assert_true(texts.any(func(t: String) -> bool: return t.contains("reached level")), str(texts))
		else:
			assert_eq(texts.filter(func(t: String) -> bool: return t == "Start here").size(), 2, "the cards are worlds: the Warehouse and the Mothership are open: " + str(texts))
		host.queue_free()
	_restore_save()
