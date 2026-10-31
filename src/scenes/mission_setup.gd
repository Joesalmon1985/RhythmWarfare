extends Control
## Mission setup: only the musical choices this mission asks for (none for some), each as a row of cards with a short
## audition, a clear "choose n" count, good defaults (the last selection, else the mission's) and locked options that
## say what unlocks them. Practice adds a choice of the whole song or one part of it. Play is always one tap away.

var _pack := ""
var _data: Dictionary = {}
var _picks: Dictionary = {}  # choice id -> Array of option ids in slot order
var _cards: Dictionary = {}  # choice id -> {option id: Button}
var _count_labels: Dictionary = {}
var _play: Button
var _audition: AudioStreamPlayer
var _part := -1


func _ready() -> void:
	var c := Session.campaign
	var n := Session.mission_number
	var info := c.level_data(n)
	_pack = c.pack_dir(n)
	var parts := UiStyle.screen(self, str(info.get("title", "Mission")),
		func() -> void: get_tree().change_scene_to_file("res://src/scenes/missions.tscn"))
	var content: VBoxContainer = parts["content"]
	_audition = AudioStreamPlayer.new()
	add_child(_audition)
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(_pack.path_join("level.json")))
	if typeof(parsed) != TYPE_DICTIONARY:
		content.add_child(UiStyle.note("This mission's files are missing. Rebuild with tools/content/build.py.", UiStyle.WARN))
		return
	_data = parsed
	var saved := c.selection_for(str(info["level_id"]))
	var warnings: Array = []
	_picks = MissionLoader.resolve_selection(_data["choices"], saved, warnings)
	var shown := 0
	for ch in _data["choices"]:
		if (ch["pool"] as Array).size() > int(ch["count"]):
			_choice_row(content, ch, n)
			shown += 1
	if shown == 0:
		content.add_child(UiStyle.note("No choices in this mission: the music is set. Press Play.", UiStyle.MUTED))
	if Session.practice:
		_practice_row(content)
	if bool(_data.get("placeholder", false)):
		content.add_child(UiStyle.note("Placeholder music (generated stand-in sounds).", UiStyle.MUTED, 15))
	_play = UiStyle.button("Practice" if Session.practice else "Play", _start, 260, 72)
	_play.add_theme_font_size_override("font_size", 30)
	(parts["header"] as HBoxContainer).add_child(_play)
	_refresh()
	_play.grab_focus()


func _choice_row(content: VBoxContainer, ch: Dictionary, number: int) -> void:
	var cid := str(ch["id"])
	var head := HBoxContainer.new()
	var title := UiStyle.note(str(ch["label"]), UiStyle.ACCENT, 22)
	title.autowrap_mode = TextServer.AUTOWRAP_OFF
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(title)
	var count := UiStyle.note("", UiStyle.MUTED, 18)
	count.autowrap_mode = TextServer.AUTOWRAP_OFF
	head.add_child(count)
	_count_labels[cid] = count
	content.add_child(head)
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", UiStyle.GAP)
	row.add_theme_constant_override("v_separation", UiStyle.GAP)
	content.add_child(row)
	_cards[cid] = {}
	for o in ch["pool"]:
		var oid := str(o["id"])
		var lock := Session.campaign.option_lock(number, oid, ch["default"])
		var card := VBoxContainer.new()
		card.add_theme_constant_override("separation", 4)
		var b := Button.new()
		b.toggle_mode = true
		b.custom_minimum_size = Vector2(230, 64)
		b.text = str(o["name"]) if lock.is_empty() else "%s\n%s" % [str(o["name"]), lock]
		b.disabled = not lock.is_empty()
		b.pressed.connect(func() -> void: _toggle(cid, oid, int(ch["count"])))
		card.add_child(b)
		var prev := str(_data.get("previews", {}).get(cid, {}).get(oid, ""))
		if not prev.is_empty() and lock.is_empty():
			var listen := UiStyle.button("Listen", func() -> void: _listen(prev), 230, 44)
			listen.add_theme_font_size_override("font_size", 17)
			card.add_child(listen)
		row.add_child(card)
		_cards[cid][oid] = b


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
		b.text = "Part %d (%s)" % [i + 1, str(phases[i]["mode"])]
		b.toggle_mode = true
		b.button_group = group
		b.custom_minimum_size = Vector2(170, 56)
		b.pressed.connect(func() -> void: _part = i)
		row.add_child(b)


func _toggle(cid: String, oid: String, count: int) -> void:
	var picks: Array = _picks[cid]
	if count == 1:
		picks.clear()
		picks.append(oid)
	elif picks.has(oid):
		picks.erase(oid)
	elif picks.size() < count:
		picks.append(oid)
	_refresh()


func _refresh() -> void:
	var ready := true
	for ch in _data.get("choices", []):
		var cid := str(ch["id"])
		if not _cards.has(cid):
			continue
		var picks: Array = _picks[cid]
		var count := int(ch["count"])
		for oid in _cards[cid]:
			var b: Button = _cards[cid][oid]
			b.set_pressed_no_signal(picks.has(oid))
			var idx := picks.find(oid)
			var base := b.text.split("\n")[0].trim_prefix("1 · ").trim_prefix("2 · ").trim_prefix("3 · ").trim_prefix("4 · ")
			var rest := b.text.substr(b.text.split("\n")[0].length())
			b.text = ("%d · %s" % [idx + 1, base] if count > 1 and idx >= 0 else base) + rest
		var lab: Label = _count_labels[cid]
		lab.text = "choose %d   %d selected" % [count, picks.size()] if count > 1 else "choose 1"
		if picks.size() != count:
			ready = false
	_play.disabled = not ready
	_play.text = ("Practice" if Session.practice else "Play") if ready else "Choose all"


func _listen(rel_path: String) -> void:
	var stream := LevelLoader.load_stream(_pack.path_join(rel_path))
	if stream != null:
		_audition.stream = stream
		_audition.play()


func _start() -> void:
	_audition.stop()
	Session.start_mission(Session.mission_number, _picks, Session.practice, _part)
	get_tree().change_scene_to_file("res://src/scenes/play.tscn")


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file("res://src/scenes/missions.tscn")
