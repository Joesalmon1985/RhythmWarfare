extends Control
## Home: Play (the continuous run from the first level), Story chapters (the finished chapter campaign, with its own saves), Start from a reached level, and
## Settings. The military campaign, practice, loadout and duel screens are not reachable from here; the developer tools stay behind one small button, shown only in
## the editor or with RW_DEV=1.

const RUN_SCENE := "res://src/run/run_play.tscn"
const CHAPTERS_SCENE := "res://src/scenes/story_campaign.tscn"
const LEVELS_SCENE := "res://src/run/run_levels.tscn"
const SETTINGS_SCENE := "res://src/scenes/settings.tscn"


var _box: VBoxContainer
var _title: Label
var _buttons: Array = []  # [chapters, reached, settings, play]


## A short window (a phone held sideways) gets a smaller title, tighter gaps and lower buttons so all four fit.
func _fit() -> void:
	var compact := size.y > 0.0 and size.y < 520.0
	_title.add_theme_font_size_override("font_size", 38 if compact else 56)
	_box.add_theme_constant_override("separation", 8 if compact else UiStyle.GAP)
	for b in _buttons:
		(b as Button).custom_minimum_size.y = (56.0 if b == _buttons[3] else 48.0) if compact else (76.0 if b == _buttons[3] else 60.0)


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
	_box = box
	_title = UiStyle.title("RHYTHM WARFARE", 56)
	box.add_child(_title)
	var prog := Session.run_progress
	var play := UiStyle.button("Play", func() -> void:
		Session.run_start_node = ""
		get_tree().change_scene_to_file(RUN_SCENE), 0, 76)
	play.add_theme_font_size_override("font_size", 30)
	play.set_meta("scene", RUN_SCENE)
	box.add_child(play)
	var chapters := UiStyle.button("Story chapters", func() -> void: get_tree().change_scene_to_file(CHAPTERS_SCENE))
	chapters.set_meta("scene", CHAPTERS_SCENE)
	box.add_child(chapters)
	var reached := UiStyle.button("Start from a reached level", func() -> void: get_tree().change_scene_to_file(LEVELS_SCENE))
	reached.set_meta("scene", LEVELS_SCENE)
	reached.disabled = prog.reached_ids().is_empty()
	box.add_child(reached)
	var settings := UiStyle.button("Settings", func() -> void: get_tree().change_scene_to_file(SETTINGS_SCENE))
	settings.set_meta("scene", SETTINGS_SCENE)
	box.add_child(settings)
	for b in [chapters, reached, settings]:
		_buttons.append(b)
	_buttons.append(play)
	resized.connect(_fit)
	_fit()
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
