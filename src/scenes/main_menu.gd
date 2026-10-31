extends Control
## Home: Continue (the next mission to play), Campaign, Practice and Settings; the developer and testing tools sit
## behind one small button in the corner.


func _ready() -> void:
	if OS.has_environment("RW_SCENE") and OS.get_environment("RW_SCENE") == "play":
		# scripted runs on exported builds (which take no scene argument) jump straight into the level
		if OS.has_environment("RW_MISSION"):
			Session.start_mission(int(OS.get_environment("RW_MISSION")), {}, OS.get_environment("RW_PRACTICE") == "1")
		get_tree().change_scene_to_file.call_deferred("res://src/scenes/play.tscn")
		return
	theme = UiStyle.theme()
	var bg := ColorRect.new()
	bg.color = UiStyle.BG
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var centre := CenterContainer.new()
	centre.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(centre)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", UiStyle.GAP)
	box.custom_minimum_size = Vector2(460, 0)
	centre.add_child(box)
	box.add_child(UiStyle.title("RHYTHM WARFARE", 56))
	var c := Session.campaign
	var n := c.continue_number()
	var data := c.level_data(n)
	var started: bool = not c.progress["cleared"].is_empty() or not str(c.progress.get("last_played", "")).is_empty()
	var cont := UiStyle.button(("Continue: %s" if started else "Play: %s") % str(data.get("title", "")), func() -> void:
		Session.mission_number = n
		Session.practice = false
		get_tree().change_scene_to_file("res://src/scenes/mission_setup.tscn"), 0, 76)
	cont.add_theme_font_size_override("font_size", 28)
	cont.disabled = not c.is_playable(n)
	box.add_child(cont)
	box.add_child(UiStyle.button("Campaign", func() -> void: _missions(false)))
	box.add_child(UiStyle.button("Practice", func() -> void: _missions(true)))
	box.add_child(UiStyle.button("Settings", func() -> void: get_tree().change_scene_to_file("res://src/scenes/settings.tscn")))
	if c.migrated_from > 0:
		box.add_child(UiStyle.note("Your progress from the previous version was carried over.", UiStyle.GOOD, 16))
	if c.recovered_from_corrupt:
		box.add_child(UiStyle.note("Saved progress was unreadable and has been reset (the old file is kept beside it).", UiStyle.WARN, 16))
	if c.unlock_all:
		box.add_child(UiStyle.note("Developer unlock-all is on.", UiStyle.WARN, 16))
	cont.grab_focus()
	var dev := UiStyle.button("Developer", func() -> void: get_tree().change_scene_to_file("res://src/scenes/developer.tscn"), 150, 44)
	dev.add_theme_font_size_override("font_size", 16)
	dev.anchor_left = 1.0
	dev.anchor_right = 1.0
	dev.anchor_top = 1.0
	dev.anchor_bottom = 1.0
	dev.offset_left = -176 - UiStyle.safe_margins(self).y
	dev.offset_right = -26 - UiStyle.safe_margins(self).y
	dev.offset_top = -62
	dev.offset_bottom = -18
	add_child(dev)
	var ver := UiStyle.note("Godot %s" % Engine.get_version_info()["string"], UiStyle.MUTED.darkened(0.3), 13)
	ver.autowrap_mode = TextServer.AUTOWRAP_OFF
	ver.anchor_top = 1.0
	ver.anchor_bottom = 1.0
	ver.offset_left = 26 + UiStyle.safe_margins(self).x
	ver.offset_top = -40
	add_child(ver)


func _missions(practice: bool) -> void:
	Session.practice = practice
	get_tree().change_scene_to_file("res://src/scenes/missions.tscn")
