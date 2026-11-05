extends Control
## Start from a reached level: one card per level of the route map; levels not entered yet are locked and say how they open. Below them, each path that has data (docs/CONTINUOUS_RUN.md "Paths")
## lists its worlds in a section of its own once one of them has been reached; a locked card says how the path opens (the portal's room).

var _focus: Button = null


func _ready() -> void:
	var parts := StoryStyle.screen(self, "START FROM A LEVEL", func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	var content: VBoxContainer = parts["content"]
	var data := RunData.load_default()
	if not data.errors.is_empty():
		content.add_child(StoryStyle.note("\n".join(PackedStringArray(data.errors)), StoryStyle.WARN, 18))
		return
	content.add_child(StoryStyle.note("A level opens the moment you enter it. Starting from one gives you its opening and a full crowd.", StoryStyle.MUTED, 20))
	for id in data.world_order:  # the cards are worlds; a world starts at its entry scene (its id)
		var n: Dictionary = data.nodes[data.entry_of(str(id))]
		var open := Session.run_progress.is_reached(id, data.start_node())
		var wid := str(id)
		_card(content, n, open, "Locked: reach it by playing a route that leads here.", func() -> void:
			Session.run_start_node = wid
			Session.run_start_path = ""
			get_tree().change_scene_to_file("res://src/run/run_play.tscn"))
	for pid in RunData.path_ids():  # the paths: their worlds once reached
		var pd := RunData.load_path(str(pid))
		if not pd.errors.is_empty() or not pd.is_path():
			continue
		var any_reached := false
		for w in pd.world_order:
			any_reached = any_reached or Session.run_progress.path_world_reached(pd.path_id, str(w))
		if bool(pd.path_info.get("dev", false)) and not any_reached:
			continue  # (a test path is listed only once someone has been in it)
		content.add_child(StoryStyle.title(str(pd.path_info.get("title", pd.path_id)).to_upper(), 22, StoryStyle.AMBER, StoryStyle.MAGENTA))
		var endings: Array = Session.run_progress.path_endings(pd.path_id)
		if not endings.is_empty():
			content.add_child(StoryStyle.note("Endings found: %d" % endings.size(), StoryStyle.MUTED, 16))
		for w in pd.world_order:
			var wn: Dictionary = pd.nodes[pd.entry_of(str(w))]
			var open2 := Session.run_progress.path_world_reached(pd.path_id, str(w))
			var how := "Locked: " + str(pd.path_info.get("opens", "reach it through its portal in the Warehouse."))
			if str(w) != str(pd.nodes[pd.start_node()]["world"]):
				how = "Locked: reach it by playing %s." % str(pd.path_info.get("title", pd.path_id))
			var path_id := pd.path_id
			var entry := str(wn["id"])
			_card(content, wn, open2, how, func() -> void:
				Session.run_start_node = entry
				Session.run_start_path = path_id
				get_tree().change_scene_to_file("res://src/run/run_play.tscn"))
	if _focus != null:
		_focus.grab_focus()


func _card(content: VBoxContainer, n: Dictionary, open: bool, locked_text: String, start: Callable) -> void:
	var card := PanelContainer.new()
	card.add_theme_stylebox_override("panel", StoryStyle.panel_box(StoryStyle.CYAN if open else StoryStyle.EDGE.darkened(0.4)))
	content.add_child(card)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 22)
	card.add_child(row)
	var v := VBoxContainer.new()
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(v)
	v.add_child(StoryStyle.note("DEPTH %d   %s" % [int(n["depth"]), str(n["map"]).replace("_", " ").to_upper()], Color(StoryStyle.AMBER, 0.9 if open else 0.5), 15))
	v.add_child(StoryStyle.title(str(n["world_title"]).to_upper(), 28, StoryStyle.TEXT if open else StoryStyle.MUTED, StoryStyle.MAGENTA))
	v.add_child(StoryStyle.note(str(n["blurb"]) if open else locked_text, Color(0.88, 0.88, 1.0, 1.0 if open else 0.6), 18))
	if open:
		var b := UiStyle.button("Start here", start, 240, 60)
		row.add_child(b)
		if _focus == null:
			_focus = b
