extends TestCase
## The home screen: Play (the run), Story chapters (the chapter campaign), Start from a reached level, Settings; the Wizard Duel (wifi) button; the military campaign and loadout stay hidden
## (a developer button only in the editor or with RW_DEV=1). Every button points at a scene that exists, all five fit a phone held sideways, and the chapter menu
## builds from home with its own saves untouched.

const TMP_RUN := "user://test_home_run.json"


func _home(size: Vector2) -> Dictionary:
	var host := Control.new()
	host.size = size
	tree.root.add_child(host)
	var scene: Control = (load("res://src/scenes/main_menu.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = size
	return {"host": host, "scene": scene}


func _buttons(root: Node) -> Array:
	var out: Array = []
	var stack: Array = [root]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n is Button:
			out.append(n)
		stack.append_array(n.get_children())
	return out


func test_home_offers_play_chapters_levels_and_settings() -> void:
	var saved := Session.run_progress
	Session.run_progress = RunProgress.load_data(TMP_RUN, "user://none.json")
	Session.run_progress.enter("warehouse")
	var d := _home(Vector2(1152, 648))
	var texts: Array = _buttons(d["scene"]).map(func(b: Button) -> String: return b.text)
	for want in ["Play", "Story chapters", "Start from a reached level", "Wizard Duel (wifi)", "Settings"]:
		assert_true(want in texts, "home has %s: %s" % [want, str(texts)])
	for hidden in ["Campaign", "Loadout", "Practice", "Missions", "Battle"]:
		assert_false(texts.any(func(t: String) -> bool: return t.contains(hidden)), "%s is not on home: %s" % [hidden, str(texts)])
	for b in _buttons(d["scene"]):
		var btn := b as Button
		if btn.has_meta("scene"):
			assert_true(ResourceLoader.exists(str(btn.get_meta("scene"))), "%s opens a scene that exists" % btn.text)
	var by := {}
	for b in _buttons(d["scene"]):
		by[(b as Button).text] = b
	assert_eq((by["Play"] as Button).get_meta("scene"), "res://src/run/run_play.tscn")
	assert_eq((by["Story chapters"] as Button).get_meta("scene"), "res://src/scenes/story_campaign.tscn")
	assert_eq((by["Wizard Duel (wifi)"] as Button).get_meta("scene"), "res://src/duel/duel_lobby.tscn")
	assert_false((by["Start from a reached level"] as Button).disabled, "a reached level is startable")
	(d["host"] as Control).queue_free()
	Session.run_progress = saved
	if FileAccess.file_exists(TMP_RUN):
		DirAccess.remove_absolute(TMP_RUN)


func test_all_five_buttons_fit_a_phone_held_sideways() -> void:
	var saved := Session.run_progress
	Session.run_progress = RunProgress.load_data(TMP_RUN, "user://none.json")
	for size in [Vector2(844, 390), Vector2(1152, 648), Vector2(1024, 768)]:
		var d := _home(size)
		await tree.process_frame
		await tree.process_frame
		var rects: Array = []
		for b in _buttons(d["scene"]):
			var btn := b as Button
			if btn.text in ["Play", "Story chapters", "Start from a reached level", "Wizard Duel (wifi)", "Settings"]:
				var r := Rect2(btn.global_position, btn.size)
				rects.append(r)
				assert_true(Rect2(Vector2.ZERO, size).encloses(r), "%s is on screen in %s (%s)" % [btn.text, str(size), str(r)])
				assert_true(r.size.y >= 44.0, "%s is a big enough target" % btn.text)
		assert_eq(rects.size(), 5)
		for i in rects.size():
			for k in range(i + 1, rects.size()):
				assert_false((rects[i] as Rect2).intersects(rects[k]), "buttons do not overlap in %s" % str(size))
		(d["host"] as Control).queue_free()
	Session.run_progress = saved
	if FileAccess.file_exists(TMP_RUN):
		DirAccess.remove_absolute(TMP_RUN)


func test_the_chapter_menu_builds_from_home_and_leaves_its_save_alone() -> void:
	var before := Session.story_progress.data.duplicate(true)
	var host := Control.new()
	host.size = Vector2(1152, 648)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/scenes/story_campaign.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	var texts: Array = _buttons(scene).map(func(b: Button) -> String: return b.text)
	assert_true(texts.size() >= 2, "chapter cards and a back button: %s" % str(texts))
	assert_true(texts.any(func(t: String) -> bool: return t.contains("Play") or t.contains("Start") or t.contains("Replay")), "the first chapter can be started: %s" % str(texts))
	assert_eq(Session.story_progress.data, before, "opening the menu changes no chapter save")
	host.queue_free()
