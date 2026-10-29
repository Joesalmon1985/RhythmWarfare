extends Control
## Main menu: the campaign (levels 1 to 3 playable, later levels planned), free play (the legacy duel packs), the
## developer rhythm playtest per chart, timing calibration and the note approach setting.


func _ready() -> void:
	if OS.has_environment("RW_SCENE") and OS.get_environment("RW_SCENE") == "play":
		# scripted runs on exported builds (which take no scene argument) jump straight into the level
		get_tree().change_scene_to_file.call_deferred("res://src/scenes/play.tscn")
		return
	var campaign := Session.campaign
	var box: VBoxContainer = $Scroll/Box
	var camp: VBoxContainer = $Scroll/Box/Campaign
	var list: VBoxContainer = $Scroll/Box/Packs
	if campaign.recovered_from_corrupt:
		camp.add_child(_header("Saved progress was unreadable and has been reset (the old file is kept as campaign.json.bad)."))
	camp.add_child(_header("CAMPAIGN"))
	var shown_planned := false
	var focus_btn: Button = null
	var last_open: Button = null
	for l in campaign.levels:
		var n := int(l["number"])
		if not campaign.is_playable(n):
			if not shown_planned:
				shown_planned = true
				camp.add_child(_header("Levels %d to %d: planned, data only." % [n, campaign.levels.size()]))
			continue
		var unlocked := campaign.is_unlocked(n)
		var cleared := campaign.is_cleared(str(l["level_id"]))
		var b := Button.new()
		b.custom_minimum_size = Vector2(0, 56)
		b.add_theme_font_size_override("font_size", 22)
		if unlocked:
			var rec: Dictionary = campaign.progress["cleared"].get(str(l["level_id"]), {})
			b.text = "Level %d  %s%s" % [n, l["title"], ("   cleared  best %.0f%%" % (float(rec.get("best_accuracy", 0.0)) * 100.0)) if cleared else ""]
			b.pressed.connect(func() -> void:
				Session.loadout_level_number = n
				get_tree().change_scene_to_file("res://src/scenes/loadout.tscn"))
			last_open = b
			if focus_btn == null and not cleared:
				focus_btn = b
		else:
			b.text = "Level %d  %s   locked: clear level %d first" % [n, l["title"], n - 1]
			b.disabled = true
		camp.add_child(b)

	if focus_btn == null:
		focus_btn = last_open
	if focus_btn != null:
		focus_btn.grab_focus()
	var packs := Session.available_packs()
	var free := false
	for p in packs:
		if int(p["schema"]) != 2:
			if not free:
				free = true
				list.add_child(_header("FREE PLAY (the legacy two-sided duel)"))
			_add_play_button(list, "Play: %s" % p["title"], p, "", true)
	var tests := false
	for p in packs:
		if int(p["schema"]) == 2:
			if not tests:
				tests = true
				list.add_child(_header("RHYTHM PLAYTEST (no battle; the chart over its placeholder stems)"))
			for c in p["charts"]:
				var tag: String = "practice chart" if c["play_mode"] == "practice" else "chart"
				_add_play_button(list, "%s  (%s %s, %d notes)" % [p["title"], tag, c["chart_id"], c["notes"]], p, str(c["chart_id"]), false)
	_add_lookahead_row()
	$Scroll/Box/Calibrate.text = "Calibrate timing (now %+.0f ms)" % Session.calibration_ms
	$Scroll/Box/Calibrate.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://src/scenes/calibration.tscn"))
	$Scroll/Box/Help.text = "Four buttons, no labels. Play the notes as they reach the line: every note you hit builds a defending group that holds one of three points in front of your base. Survive until the song ends. Keys: D F J K."
	$Scroll/Box/Version.text = "Rhythm Warfare  ·  Godot %s" % Engine.get_version_info()["string"]
	box.queue_sort()


func _header(text: String) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", 18)
	l.modulate = Color(0.75, 0.85, 1.0)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


func _add_play_button(list: VBoxContainer, text: String, p: Dictionary, chart_id: String, battle: bool) -> void:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(0, 52)
	b.add_theme_font_size_override("font_size", 20)
	b.pressed.connect(func() -> void:
		Session.pack_dir = p["dir"]
		Session.chart_id = chart_id
		Session.battle_on = battle if not OS.has_environment("RW_BATTLE") else Session.battle_on
		Session.loadout = {}
		Session.practice = false
		Session.campaign_level_id = ""
		Session.save_settings()
		get_tree().change_scene_to_file("res://src/scenes/play.tscn"))
	list.add_child(b)


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
	$Scroll/Box.add_child(row)
	$Scroll/Box.move_child(row, $Scroll/Box/Calibrate.get_index() + 1)
