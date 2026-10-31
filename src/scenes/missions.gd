extends Control
## The mission list (Campaign or Practice): names with only what navigation needs (cleared, locked). No lengths,
## enemies, lessons or structure on the cards.


func _ready() -> void:
	var practice := Session.practice
	var parts := UiStyle.screen(self, "Practice" if practice else "Campaign",
		func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	var content: VBoxContainer = parts["content"]
	if practice:
		content.add_child(UiStyle.note("Same cues and timing as the campaign, no battle, nothing saved.", UiStyle.MUTED, 18))
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", UiStyle.GAP)
	grid.add_theme_constant_override("v_separation", UiStyle.GAP)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_child(grid)
	var c := Session.campaign
	var focus: Button = null
	for l in c.levels:
		var n := int(l["number"])
		var cleared := c.is_cleared(str(l["level_id"]))
		var open := c.is_unlocked(n) and c.is_playable(n)
		var tag := ""
		if not c.is_playable(n):
			tag = "not built yet"
		elif not open:
			tag = "locked: clear %s" % str(c.level_data(n - 1).get("title", ""))
		elif cleared:
			tag = "cleared"
		var b := UiStyle.button("%d   %s%s" % [n, str(l["title"]), ("\n" + tag) if not tag.is_empty() else ""], func() -> void:
			Session.mission_number = n
			get_tree().change_scene_to_file("res://src/scenes/mission_setup.tscn"), 0, 84)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.disabled = not open
		if cleared and open:
			b.add_theme_color_override("font_color", UiStyle.GOOD)
		grid.add_child(b)
		if open and (focus == null or (n == c.continue_number())):
			focus = b
	if focus != null:
		focus.grab_focus()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn")
