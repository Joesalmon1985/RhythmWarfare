extends Control
## Home: Play (the story run from the first level), Start from a reached level, and Settings. The old campaign, practice, loadout and duel
## screens are no longer reachable from here; the developer tools stay behind one small button, shown only in the editor or with RW_DEV=1.


func _ready() -> void:
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
	var prog := Session.run_progress
	var play := UiStyle.button("Play", func() -> void:
		Session.run_start_node = ""
		get_tree().change_scene_to_file("res://src/run/run_play.tscn"), 0, 76)
	play.add_theme_font_size_override("font_size", 30)
	box.add_child(play)
	var reached := UiStyle.button("Start from a reached level", func() -> void: get_tree().change_scene_to_file("res://src/run/run_levels.tscn"))
	reached.disabled = prog.reached_ids().is_empty()
	box.add_child(reached)
	box.add_child(UiStyle.button("Wizard Duel (wifi)", func() -> void: get_tree().change_scene_to_file("res://src/duel/duel_lobby.tscn")))
	box.add_child(UiStyle.button("Settings", func() -> void: get_tree().change_scene_to_file("res://src/scenes/settings.tscn")))
	var note := prog.migration_note()
	if note != "":
		box.add_child(UiStyle.note(note, UiStyle.GOOD, 16))
	if prog.recovered_from_corrupt:
		box.add_child(UiStyle.note("Saved progress was unreadable and has been reset (the old file is kept beside it).", UiStyle.WARN, 16))
	play.grab_focus()
	if OS.has_feature("editor") or OS.get_environment("RW_DEV") == "1":
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
