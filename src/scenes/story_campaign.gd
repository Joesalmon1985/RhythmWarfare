extends Control
## Story Campaign chapter list: one card per chapter with its blurb, lock state and best ending. Night One needs no military campaign
## progress; the later chapters unlock from the endings of the chapter before.


func _ready() -> void:
	var parts := UiStyle.screen(self, "Story Campaign", func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	var content: VBoxContainer = parts["content"]
	var chapters := StoryChapters.load_default()
	var focus: Button = null
	var n := 0
	for c in chapters.chapters:
		n += 1
		var id := str(c["id"])
		var rec: Dictionary = Session.story_progress.level_record(id)
		var open := chapters.available(id) and chapters.unlocked(id, Session.story_progress)
		var card := PanelContainer.new()
		card.add_theme_stylebox_override("panel", UiStyle.panel_box())
		content.add_child(card)
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 6)
		card.add_child(v)
		v.add_child(UiStyle.title("Chapter %d   %s" % [n, str(c["title"])], 32))
		v.add_child(UiStyle.note(str(c.get("blurb", "")), Color(0.85, 0.88, 0.95), 20))
		if not chapters.available(id):
			v.add_child(UiStyle.note("Coming later.", UiStyle.MUTED, 18))
		elif not open:
			v.add_child(UiStyle.note("Locked: reach an ending in %s." % str(chapters.chapter(str(c.get("unlock_from", "")))["title"] if chapters.chapter(str(c.get("unlock_from", ""))).has("title") else "the chapter before"), UiStyle.WARN, 18))
		elif not rec.is_empty():
			var data: StoryData = StoryData.load_file(str(c["data"]))["data"]
			var title := str(data.endings[str(rec["best_ending"])]["title"]) if data != null and data.endings.has(str(rec["best_ending"])) else "-"
			v.add_child(UiStyle.note("Best ending: %s    Sets played: %d    Best crowd energy: %d" % [title, int(rec["plays"]), int(float(rec["best_energy"]))], UiStyle.GOOD, 18))
		if open:
			var row := HBoxContainer.new()
			row.add_theme_constant_override("separation", UiStyle.GAP)
			v.add_child(row)
			var play := UiStyle.button("Play %s" % str(c["title"]), func() -> void:
				Session.story_chapter = id
				Session.story_interlude = {}
				get_tree().change_scene_to_file("res://src/scenes/story_play.tscn"), 320, 68)
			play.add_theme_font_size_override("font_size", 26)
			row.add_child(play)
			if focus == null:
				focus = play
			if id == "night_one":
				row.add_child(UiStyle.button("Loadout", func() -> void: get_tree().change_scene_to_file("res://src/scenes/loadout.tscn"), 200, 68))
	content.add_child(UiStyle.note("Each set plays your Loadout: the same four pads, falling notes and music as the campaign.", UiStyle.MUTED, 16))
	if focus != null:
		focus.grab_focus()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn")
