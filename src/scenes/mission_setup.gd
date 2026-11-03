extends Control
## The mission briefing: what the mission is (its base, approaches, villagers and waves), your loadout (the same in
## every mission, with what its three instruments build) and, for practice, which part to play. Play is one tap away;
## "Change loadout" opens the Loadout screen and comes back here.

const SLOT_TITLES := {"groove": "Drum pattern", "fill": "Fill", "kick_sound": "Kick", "snare_sound": "Snare",
	"bass": "Bass line", "bass_sound": "Bass sound", "backing": "Backing"}
const INSTRUMENTS := ["kick_sound", "snare_sound", "bass_sound"]

var _data: Dictionary = {}
var _part := -1


func _ready() -> void:
	var c := Session.campaign
	var n := Session.mission_number
	var info := c.level_data(n)
	var parts := UiStyle.screen(self, "Mission %d: %s" % [n, str(info.get("title", "Mission"))],
		func() -> void: get_tree().change_scene_to_file("res://src/scenes/missions.tscn"))
	var content: VBoxContainer = parts["content"]
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(c.pack_dir(n).path_join("level.json")))
	if typeof(parsed) != TYPE_DICTIONARY:
		content.add_child(UiStyle.note("This mission's files are missing. Rebuild with tools/content/build.py.", UiStyle.WARN))
		return
	_data = parsed
	var base: Dictionary = _data.get("base", {})
	var has_factory: bool = (base.get("production", []) as Array).has("factory")
	_base_panel(content, base, has_factory)
	_loadout_panel(content, has_factory)
	if Session.practice:
		_practice_row(content)
	var play := UiStyle.button("Practice" if Session.practice else "Play", _start, 260, 72)
	play.add_theme_font_size_override("font_size", 30)
	(parts["header"] as HBoxContainer).add_child(play)
	play.grab_focus()


func _panel(content: VBoxContainer, heading: String, extra: Control = null) -> VBoxContainer:
	var panel := PanelContainer.new()
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_child(panel)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 6)
	panel.add_child(col)
	var head_row := HBoxContainer.new()
	col.add_child(head_row)
	var head := UiStyle.note(heading, UiStyle.ACCENT, 22)
	head.autowrap_mode = TextServer.AUTOWRAP_OFF
	head.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head_row.add_child(head)
	if extra != null:
		head_row.add_child(extra)
	return col


func _base_panel(content: VBoxContainer, base: Dictionary, has_factory: bool) -> void:
	var col := _panel(content, "The base")
	col.add_child(UiStyle.note("Barracks and war factory" if has_factory else "Barracks", UiStyle.TEXT, 22))
	if not has_factory:
		col.add_child(UiStyle.note("No war factory here: vehicle rewards from the bass become repairs", UiStyle.WARN, 19))
	var facts := HFlowContainer.new()
	facts.add_theme_constant_override("h_separation", 36)
	col.add_child(facts)
	var entries := int(base.get("entries", 0))
	var points := int(base.get("points", 0))
	if entries > 0:
		facts.add_child(_fact("%d approach%s, %d rally point%s" % [entries, "" if entries == 1 else "es", points, "" if points == 1 else "s"]))
	var civilians := int(base.get("civilians", 0))
	if civilians > 0:
		facts.add_child(_fact("%d villagers to protect" % civilians))
	facts.add_child(_fact(waves_line(_data)))


func _fact(text: String) -> Label:
	var l := UiStyle.note(text, UiStyle.TEXT, 22)
	l.autowrap_mode = TextServer.AUTOWRAP_OFF
	return l


## "25 waves over 2:56" from the pack's wave list and its length in ticks.
static func waves_line(data: Dictionary) -> String:
	var waves := (data.get("waves", []) as Array).size()
	var beats := float(data.get("duration_ticks", 0)) / maxf(float(data.get("ticks_per_beat", 960)), 1.0)
	var seconds := int(beats * 60.0 / maxf(float(data.get("bpm", 174)), 1.0))
	return "%d wave%s over %d:%02d" % [waves, "" if waves == 1 else "s", seconds / 60, seconds % 60]


func _loadout_panel(content: VBoxContainer, has_factory: bool) -> void:
	var change := UiStyle.button("Change loadout", func() -> void:
		get_tree().set_meta("loadout_return", "mission_setup")
		get_tree().change_scene_to_file("res://src/scenes/loadout.tscn"), 240, 48)
	var col := _panel(content, "Your loadout", change)
	var index := Session.library()
	var lo := Session.loadout()
	for slot: String in Loadout.SLOTS:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", UiStyle.GAP)
		col.add_child(row)
		var title := UiStyle.note(str(SLOT_TITLES[slot]), UiStyle.MUTED, 20)
		title.autowrap_mode = TextServer.AUTOWRAP_OFF
		title.custom_minimum_size = Vector2(150, 0)
		row.add_child(title)
		var id := str(lo.get(slot, ""))
		var label := UiStyle.note("None" if id.is_empty() else index.name(id), UiStyle.TEXT, 22)
		label.autowrap_mode = TextServer.AUTOWRAP_OFF
		label.custom_minimum_size = Vector2(250, 0)
		row.add_child(label)
		if INSTRUMENTS.has(slot) and not id.is_empty():
			var icons := UiStyle.reward_icons(index, id)
			if slot == "bass_sound" and not has_factory:
				icons = UiStyle.without_vehicles(icons)
			row.add_child(UiStyle.icon_strip(icons))


func _practice_row(content: VBoxContainer) -> void:
	content.add_child(UiStyle.note("Practice", UiStyle.ACCENT, 22))
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", UiStyle.GAP)
	content.add_child(row)
	var group := ButtonGroup.new()
	var whole := Button.new()
	whole.text = "Whole song"
	whole.toggle_mode = true
	whole.button_group = group
	whole.button_pressed = true
	whole.custom_minimum_size = Vector2(200, 56)
	whole.pressed.connect(func() -> void: _part = -1)
	row.add_child(whole)
	var phases: Array = _data.get("phases", [])
	for i in phases.size():
		var b := Button.new()
		b.text = "Part %d (%s)" % [i + 1, str(phases[i].get("mode", "")).substr(0, 1).to_upper()]
		b.toggle_mode = true
		b.button_group = group
		b.custom_minimum_size = Vector2(150, 56)
		b.pressed.connect(func() -> void: _part = i)
		row.add_child(b)


func _start() -> void:
	Session.start_mission(Session.mission_number, Session.practice, _part)
	get_tree().change_scene_to_file("res://src/scenes/play.tscn")


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file("res://src/scenes/missions.tscn")
