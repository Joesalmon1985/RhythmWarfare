extends Control
## After a loss: how far the run got, Retry this level (fresh energy, its authored opening), pick any reached level, or go home.


func _ready() -> void:
	var parts := StoryStyle.screen(self, "THE CROWD HAS GONE HOME", func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	var content: VBoxContainer = parts["content"]
	var data := RunData.load_default()
	var r: Dictionary = Session.run_result
	var node := str(r.get("node", data.start_node()))
	var title := str(data.nodes[node]["title"]) if data.nodes.has(node) else node
	content.add_child(StoryStyle.note("You lost the floor on %s, level %d of this run." % [title, int(r.get("phases", 1))], StoryStyle.TEXT, 26))
	content.add_child(StoryStyle.note("Every level you entered stays open: start again from any of them.", StoryStyle.MUTED, 20))
	var retry := UiStyle.button("Retry %s" % title, func() -> void:
		Session.run_start_node = node
		get_tree().change_scene_to_file("res://src/run/run_play.tscn"), 420, 72)
	retry.add_theme_font_size_override("font_size", 28)
	content.add_child(retry)
	content.add_child(UiStyle.button("Choose a reached level", func() -> void: get_tree().change_scene_to_file("res://src/run/run_levels.tscn"), 420, 64))
	content.add_child(UiStyle.button("Home", func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"), 420, 64))
	retry.grab_focus()
