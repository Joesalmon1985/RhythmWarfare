extends Control
## Start from a reached level: one card per level of the route map; levels not entered yet are locked and say how they open.


func _ready() -> void:
	var parts := StoryStyle.screen(self, "START FROM A LEVEL", func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	var content: VBoxContainer = parts["content"]
	var data := RunData.load_default()
	if not data.errors.is_empty():
		content.add_child(StoryStyle.note("\n".join(PackedStringArray(data.errors)), StoryStyle.WARN, 18))
		return
	content.add_child(StoryStyle.note("A level opens the moment you enter it. Starting from one gives you its opening and a full crowd.", StoryStyle.MUTED, 20))
	var focus: Button = null
	for id in data.node_order:
		var n: Dictionary = data.nodes[id]
		var open := Session.run_progress.is_reached(id, data.start_node())
		var card := PanelContainer.new()
		card.add_theme_stylebox_override("panel", StoryStyle.panel_box(StoryStyle.CYAN if open else StoryStyle.EDGE.darkened(0.4)))
		content.add_child(card)
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 22)
		card.add_child(row)
		var v := VBoxContainer.new()
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(v)
		v.add_child(StoryStyle.note("DEPTH %d   %s" % [int(n["depth"]), str(n["world"]).replace("_", " ").to_upper()], Color(StoryStyle.AMBER, 0.9 if open else 0.5), 15))
		v.add_child(StoryStyle.title(str(n["title"]).to_upper(), 28, StoryStyle.TEXT if open else StoryStyle.MUTED, StoryStyle.MAGENTA))
		v.add_child(StoryStyle.note(str(n["blurb"]) if open else "Locked: reach it by playing a route that leads here.", Color(0.88, 0.88, 1.0, 1.0 if open else 0.6), 18))
		if open:
			var b := UiStyle.button("Start here", func() -> void:
				Session.run_start_node = id
				get_tree().change_scene_to_file("res://src/run/run_play.tscn"), 240, 60)
			row.add_child(b)
			if focus == null:
				focus = b
	if focus != null:
		focus.grab_focus()
