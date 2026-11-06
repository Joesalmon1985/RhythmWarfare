extends Control
## Story Campaign chapter list: one card per chapter with a glimpse of its room, its blurb, lock state and best ending. Night One
## needs no military campaign progress; the later chapters unlock from the endings of the chapter before.

const ACCENTS := [StoryStyle.MAGENTA, StoryStyle.CYAN, StoryStyle.AMBER]


func _dev() -> bool:
	return OS.has_feature("editor") or OS.get_environment("RW_DEV") == "1"


func _ready() -> void:
	var parts := StoryStyle.screen(self, "STORY CHAPTERS", func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	var content: VBoxContainer = parts["content"]
	var chapters := StoryChapters.load_default()
	var focus: Button = null
	var n := 0
	for c in chapters.chapters:
		n += 1
		var id := str(c["id"])
		var accent: Color = ACCENTS[(n - 1) % ACCENTS.size()]
		var rec: Dictionary = Session.story_progress.level_record(id)
		var open := chapters.available(id) and chapters.unlocked(id, Session.story_progress)
		var data: StoryData = StoryData.load_file(str(c["data"]))["data"] if chapters.available(id) else null
		var card := PanelContainer.new()
		card.add_theme_stylebox_override("panel", StoryStyle.panel_box(accent if open else StoryStyle.EDGE.darkened(0.4)))
		content.add_child(card)
		var row0 := HBoxContainer.new()
		row0.add_theme_constant_override("separation", 22)
		card.add_child(row0)
		var thumb := _thumbnail(data, open)
		if thumb != null:
			row0.add_child(thumb)
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 6)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row0.add_child(v)
		var kicker := StoryStyle.note("CHAPTER %d" % n, Color(accent.lightened(0.3), 0.9 if open else 0.5), 16)
		v.add_child(kicker)
		var tl := StoryStyle.title(str(c["title"]).to_upper(), 32, StoryStyle.TEXT if open else StoryStyle.MUTED, accent)
		tl.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
		v.add_child(tl)
		v.add_child(StoryStyle.note(str(c.get("blurb", "")), Color(0.88, 0.88, 1.0, 1.0 if open else 0.6), 20))
		if not chapters.available(id):
			v.add_child(StoryStyle.note("Coming later.", StoryStyle.MUTED, 18))
		elif not open:
			var from: Dictionary = chapters.chapter(str(c.get("unlock_from", "")))
			v.add_child(StoryStyle.note("LOCKED  -  reach an ending in %s to open it." % str(from.get("title", "the chapter before")), StoryStyle.WARN, 18))
		elif not rec.is_empty():
			var title := str(data.endings[str(rec["best_ending"])]["title"]) if data != null and data.endings.has(str(rec["best_ending"])) else "-"
			v.add_child(StoryStyle.note("Best ending: %s      Sets played: %d      Best crowd energy: %d" % [title, int(rec["plays"]), int(float(rec["best_energy"]))], StoryStyle.GOOD, 18))
		if open:
			var row := HBoxContainer.new()
			row.add_theme_constant_override("separation", StoryStyle.GAP)
			v.add_child(row)
			var play := UiStyle.button("Play %s" % str(c["title"]), func() -> void:
				Session.story_chapter = id
				Session.story_interlude = {}
				get_tree().change_scene_to_file("res://src/scenes/story_play.tscn"), 320, 64)
			play.add_theme_font_size_override("font_size", 26)
			row.add_child(play)
			if focus == null:
				focus = play
			if id == "night_one" and _dev():  # the loadout screen belongs to the military campaign: developers only, like the home screen's button
				row.add_child(UiStyle.button("Loadout", func() -> void: get_tree().change_scene_to_file("res://src/scenes/loadout.tscn"), 200, 64))
	if _dev():
		content.add_child(StoryStyle.note("Each set plays your Loadout: the same four pads, falling notes and music as the campaign.", StoryStyle.MUTED, 16))
	if focus != null:
		focus.grab_focus()
	if StoryTrace.auto_advance():  # the walk-through ends on the menu: log what it offers
		StoryTrace.line("menu", {"unlocked": ",".join(PackedStringArray(StoryTrace.unlocked_ids()))})
		get_tree().create_timer(0.5).timeout.connect(func() -> void: get_tree().quit())


## A small window onto the chapter's room, darkened when the chapter is locked: a frame of the room as the run draws it now
## (assets/run/thumbs/<art>.jpg, made by tools/art/make_thumbs.sh), else the chapter's old backdrop art.
func _thumbnail(data: StoryData, open: bool) -> Control:
	if data == null:
		return null
	var shot := "res://assets/run/thumbs/%s.jpg" % data.art
	var tex: Texture2D = load(shot) as Texture2D if ResourceLoader.exists(shot) else null
	if tex == null:
		var assets := StoryAssets.load_art(data.art, false)
		tex = assets.texture(str(assets.layer("backdrop").get("file", "")))
	if tex == null:
		return null
	var frame := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0.6)
	sb.border_color = Color(1, 1, 1, 0.18)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(8)
	sb.set_content_margin_all(3)
	frame.add_theme_stylebox_override("panel", sb)
	var tr := TextureRect.new()
	tr.texture = tex
	tr.custom_minimum_size = Vector2(256, 144)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	tr.modulate = Color.WHITE if open else Color(0.35, 0.33, 0.5)
	frame.add_child(tr)
	frame.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	return frame


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn")
