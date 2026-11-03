extends Control
## Story Campaign level screen: Night One (available) and a placeholder for chapters to come. Needs no military campaign progress.


func _ready() -> void:
	var parts := UiStyle.screen(self, "Story Campaign", func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	var content: VBoxContainer = parts["content"]
	var loaded := StoryData.load_file()
	var data: StoryData = loaded["data"]
	var rec: Dictionary = Session.story_progress.level_record("night_one")
	var card := PanelContainer.new()
	card.add_theme_stylebox_override("panel", UiStyle.panel_box())
	content.add_child(card)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	card.add_child(v)
	v.add_child(UiStyle.title("Chapter 1   Night One", 40))
	if data == null or not (loaded["errors"] as Array).is_empty():
		v.add_child(UiStyle.note("This chapter's data could not be read:\n" + "\n".join(PackedStringArray(loaded["errors"])), UiStyle.WARN, 18))
	else:
		v.add_child(UiStyle.note(str(data.raw.get("description", "")), Color(0.85, 0.88, 0.95), 22))
	v.add_child(UiStyle.note("A full 128-bar drum and bass set from the decks, using your Loadout. Play the four pads on the beat: every two-bar sequence moves the room.", UiStyle.MUTED, 18))
	if not rec.is_empty():
		var names := {"legendary_set": "Legendary Set", "good_night": "Good Night", "lost_the_floor": "Lost the Floor"}
		v.add_child(UiStyle.note("Best ending: %s    Sets played: %d    Best crowd energy: %d" % [names.get(str(rec["best_ending"]), "-"), int(rec["plays"]), int(float(rec["best_energy"]))], UiStyle.GOOD, 18))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", UiStyle.GAP)
	v.add_child(row)
	var play := UiStyle.button("Play Night One", func() -> void: get_tree().change_scene_to_file("res://src/scenes/story_play.tscn"), 320, 72)
	play.add_theme_font_size_override("font_size", 28)
	play.disabled = data == null
	row.add_child(play)
	row.add_child(UiStyle.button("Loadout", func() -> void: get_tree().change_scene_to_file("res://src/scenes/loadout.tscn"), 200, 72))
	var next := UiStyle.button("Chapter 2   Coming later", Callable(), 0, 72)
	next.disabled = true
	content.add_child(next)
	play.grab_focus()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn")
