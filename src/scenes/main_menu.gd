extends Control
## Level select: the available song packs, the control explanation and calibration.


func _ready() -> void:
	if OS.has_environment("RW_SCENE") and OS.get_environment("RW_SCENE") == "play":
		# scripted runs on exported builds (which take no scene argument) jump straight into the level
		get_tree().change_scene_to_file.call_deferred("res://src/scenes/play.tscn")
		return
	var list: VBoxContainer = $Box/Packs
	var packs := Session.available_packs()
	if packs.is_empty():
		var l := Label.new()
		l.text = "No song packs found. Put a pack in songs/ (see songs/README.md)."
		list.add_child(l)
	for p in packs:
		if int(p["schema"]) == 2:
			for c in p["charts"]:
				var tag: String = "practice chart" if c["play_mode"] == "practice" else "chart"
				_add_play_button(list, "Rhythm playtest: %s  (%s %s, %d notes)" % [p["title"], tag, c["chart_id"], c["notes"]], p, str(c["chart_id"]), false)
		else:
			_add_play_button(list, "Play: %s" % p["title"], p, "", true)
	_add_lookahead_row()
	$Box/Calibrate.text = "Calibrate timing (now %+.0f ms)" % Session.calibration_ms
	$Box/Calibrate.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://src/scenes/calibration.tscn"))
	$Box/Help.text = "Four buttons, no labels: the notes tell you what they make. Round notes on the left button are kicks (vehicles), diamonds on the right button are snares (an infantry squad), bars are bass (tap or hold: helipads and helicopter sorties) and run across all four buttons.
Hit each note as it reaches the line. Lose a factory and its instrument falls silent. Destroy the enemy base before the song ends. Keys: D F J K."
	$Box/Version.text = "Rhythm Warfare  ·  Godot %s" % Engine.get_version_info()["string"]


func _add_play_button(list: VBoxContainer, text: String, p: Dictionary, chart_id: String, battle: bool) -> void:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(0, 56)
	b.add_theme_font_size_override("font_size", 22)
	b.pressed.connect(func() -> void:
		Session.pack_dir = p["dir"]
		Session.chart_id = chart_id
		Session.battle_on = battle if not OS.has_environment("RW_BATTLE") else Session.battle_on
		Session.loadout = {}
		Session.save_settings()
		get_tree().change_scene_to_file("res://src/scenes/play.tscn"))
	list.add_child(b)
	if Session.pack_dir == p["dir"] and (chart_id.is_empty() or chart_id == Session.chart_id):
		b.grab_focus()


## Note approach window (readability), independent of tempo and timing calibration.
func _add_lookahead_row() -> void:
	var row := HBoxContainer.new()
	var label := Label.new()
	label.text = "Note approach %.1f s" % Session.lookahead_s
	label.custom_minimum_size = Vector2(220, 0)
	var slider := HSlider.new()
	slider.min_value = Session.LOOKAHEAD_MIN_S
	slider.max_value = Session.LOOKAHEAD_MAX_S
	slider.step = 0.1
	slider.value = Session.lookahead_s
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider.custom_minimum_size = Vector2(0, 40)
	slider.value_changed.connect(func(v: float) -> void:
		Session.lookahead_s = v
		label.text = "Note approach %.1f s" % v
		Session.save_settings())
	row.add_child(label)
	row.add_child(slider)
	$Box.add_child(row)
	$Box.move_child(row, $Box/Calibrate.get_index() + 1)
