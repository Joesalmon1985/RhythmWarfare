extends Control
## The end-of-set summary: the ending reached, what the room did, the moments that went your way (or did not) and the energy over
## the set as a lit curve with the crowd bands, the acts and the authored moments marked. Retry, back to the story menu, or home.

const TONE := {"legendary": StoryStyle.MAGENTA, "good": StoryStyle.CYAN, "lost": StoryStyle.AMBER}


func _ready() -> void:
	if Session.story_result.is_empty() and OS.has_environment("RW_STORY_RESULT"):  # screenshots: a scripted set's summary
		var s := StoryRun.autoplay(OS.get_environment("RW_STORY_RESULT"), 1.0 / 30.0, int(OS.get_environment("RW_SEED")) if OS.has_environment("RW_SEED") else 1)
		s.erase("run")
		s["level_id"] = "night_one"
		s["title"] = "Night One"
		Session.story_result = s
	var r := Session.story_result
	var ending := str(r.get("ending", "lost_the_floor"))
	var chapters := StoryChapters.load_default()
	var chapter_id := str(r.get("level_id", Session.story_chapter))
	var entry := chapters.chapter(chapter_id)
	var data: StoryData = StoryData.load_file(str(entry.get("data", StoryData.PATH)))["data"]
	var ending_title := str(data.endings[ending]["title"]).to_upper() if data != null and data.endings.has(ending) else ""
	var tone: Color = TONE.get(data.tableau_of(ending) if data != null else "", StoryStyle.CYAN)
	var parts := StoryStyle.screen(self, str(r.get("title", "")).to_upper())
	var content: VBoxContainer = parts["content"]
	var head := StoryStyle.title(ending_title, 56, Color.WHITE, tone)
	head.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	content.add_child(head)
	if data != null and data.endings.has(ending):
		content.add_child(StoryStyle.note(str(data.endings[ending]["text"]), Color(0.92, 0.92, 1.0), 22))
	var tiles := HFlowContainer.new()
	tiles.add_theme_constant_override("h_separation", StoryStyle.GAP)
	tiles.add_theme_constant_override("v_separation", StoryStyle.GAP)
	content.add_child(tiles)
	var passed := int(r.get("sequences_passed", 0))
	var total := maxi(int(r.get("sequences_total", 0)), 1)
	tiles.add_child(_tile("SEQUENCES", "%d / %d" % [passed, total], StoryStyle.GOOD if passed * 2 >= total else StoryStyle.WARN))
	tiles.add_child(_tile("ACCURACY", "%d%%" % int(round(float(r.get("accuracy", 0.0)) * 100.0)), StoryStyle.CYAN))
	tiles.add_child(_tile("BEST COMBO", str(int(r.get("best_combo", 0))), StoryStyle.AMBER))
	tiles.add_child(_tile("AT CLOSE", "%d" % int(float(r.get("energy", 0.0))), tone))
	tiles.add_child(_tile("PEAK", "%d" % int(float(r.get("peak_energy", 0.0))), StoryStyle.MAGENTA))
	var curve_box := PanelContainer.new()
	curve_box.add_theme_stylebox_override("panel", StoryStyle.panel_box(tone))
	content.add_child(curve_box)
	var cv := VBoxContainer.new()
	curve_box.add_child(cv)
	var ct := StoryStyle.note("THE ROOM'S ENERGY THROUGH THE SET", StoryStyle.MUTED, 15)
	cv.add_child(ct)
	var curve := EnergyCurve.new()
	curve.values = r.get("energy_curve", [])
	curve.tone = tone
	if data != null:
		curve.bars = float(data.duration_bars)
		curve.acts = data.acts
		curve.moments = r.get("branches", [])
		var bands: Array = []
		for b in data.raw.get("energy", {}).get("bands", []):
			bands.append(float(b.get("max", 100)))
		curve.bands = bands
	curve.custom_minimum_size = Vector2(0, 150)
	cv.add_child(curve)
	content.add_child(StoryStyle.title("THE NIGHT IN MOMENTS", 24, StoryStyle.TEXT, StoryStyle.CYAN))
	for b in r.get("branches", []):
		var good := str(b["outcome"]) == "good"
		if str(b["text"]).is_empty():
			continue
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 12)
		content.add_child(row)
		var mark := StoryStyle.note("+" if good else "-", StoryStyle.GOOD if good else StoryStyle.WARN, 26)
		mark.custom_minimum_size = Vector2(26, 0)
		row.add_child(mark)
		var txt := StoryStyle.note("%s   (bar %d)\n%s" % [str(b["title"]), int(b["bar"]), str(b["text"])], StoryStyle.GOOD if good else StoryStyle.WARN, 18)
		txt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(txt)
	var buttons := HFlowContainer.new()
	buttons.add_theme_constant_override("h_separation", StoryStyle.GAP)
	content.add_child(buttons)
	var route := chapters.route(chapter_id, ending)
	var first: Button = null
	if not route.is_empty():
		var to_id := str(route["to"])
		first = UiStyle.button("Continue: %s" % str(chapters.chapter(to_id)["title"]), func() -> void:
			Session.story_chapter = to_id
			Session.story_interlude = {"name": str(route.get("interlude", "")), "from": chapter_id, "to": to_id, "ending": ending}
			get_tree().change_scene_to_file("res://src/scenes/story_interlude.tscn" if str(route.get("interlude", "")) != "" else "res://src/scenes/story_play.tscn"), 360, 64)
		buttons.add_child(first)
		content.add_child(StoryStyle.note(str(route.get("label", "")), StoryStyle.AMBER, 20))
	else:
		content.add_child(StoryStyle.note("To be continued...", StoryStyle.MUTED, 20))
	var retry := UiStyle.button("Play again", func() -> void:
		Session.story_chapter = chapter_id
		get_tree().change_scene_to_file("res://src/scenes/story_play.tscn"), 220, 64)
	buttons.add_child(retry)
	buttons.add_child(UiStyle.button("Story Campaign", func() -> void: get_tree().change_scene_to_file("res://src/scenes/story_campaign.tscn"), 240, 64))
	buttons.add_child(UiStyle.button("Menu", func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"), 160, 64))
	(first if first != null else retry).grab_focus()


func _tile(label: String, value: String, accent: Color) -> Control:
	var p := PanelContainer.new()
	var sb := StoryStyle.panel_box(accent)
	sb.content_margin_top = 10
	sb.content_margin_bottom = 10
	sb.shadow_size = 8
	p.add_theme_stylebox_override("panel", sb)
	p.custom_minimum_size = Vector2(170, 0)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 0)
	p.add_child(v)
	v.add_child(StoryStyle.note(label, Color(accent.lightened(0.3), 0.85), 14))
	var val := StoryStyle.title(value, 32, Color.WHITE, accent)
	val.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	v.add_child(val)
	return p


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file("res://src/scenes/story_campaign.tscn")


## Crowd energy after each two-bar sequence, over the set: the crowd bands as faint shelves, the act boundaries, the authored
## moments as markers (filled = went your way), and the line itself in the ending's colour with a soft glow and a filled area.
class EnergyCurve:
	extends Control
	var values: Array = []
	var tone := Color(0.35, 0.9, 1.0)
	var bars := 128.0
	var acts: Array = []
	var moments: Array = []
	var bands: Array = [29.0, 64.0, 84.0]

	func _y(v: float) -> float:
		return size.y - 6.0 - (size.y - 12.0) * clampf(v / 100.0, 0.0, 1.0)

	func _x(bar: float) -> float:
		return size.x * clampf((bar - 1.0) / maxf(bars, 1.0), 0.0, 1.0)

	func _draw() -> void:
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.02, 0.01, 0.07, 0.8))
		var lo := 0.0
		var k := 0
		for b in bands:  # the crowd bands: quiet, dancing, hype, euphoric
			var hi := minf(float(b), 100.0)
			draw_rect(Rect2(0, _y(hi), size.x, _y(lo) - _y(hi)), Color(tone, 0.03 + 0.025 * k))
			draw_line(Vector2(0, _y(hi)), Vector2(size.x, _y(hi)), Color(1, 1, 1, 0.07), 1.0)
			lo = hi
			k += 1
		var font := ThemeDB.fallback_font
		for a in acts:
			var x := _x(float(a["start_bar"]))
			draw_line(Vector2(x, 0), Vector2(x, size.y), Color(1, 1, 1, 0.12), 1.0)
			draw_string(font, Vector2(x + 6.0, size.y - 10.0), "ACT %s" % str(a["id"]), HORIZONTAL_ALIGNMENT_LEFT, -1, 13, Color(1, 1, 1, 0.45))
		if values.size() < 2:
			return
		var pts := PackedVector2Array()
		for i in values.size():
			pts.append(Vector2(size.x * float(i) / float(values.size() - 1), _y(float(values[i]))))
		var area := pts.duplicate()
		area.append(Vector2(size.x, size.y))
		area.append(Vector2(0, size.y))
		var cols := PackedColorArray()
		for i in area.size():
			cols.append(Color(tone, 0.22 if i < pts.size() else 0.0))
		draw_polygon(area, cols)
		draw_polyline(pts, Color(tone, 0.25), 9.0, true)
		draw_polyline(pts, Color(tone.lightened(0.35), 1.0), 3.0, true)
		for m in moments:
			var x := _x(float(m.get("bar", 1)))
			var i := clampi(int(round(x / size.x * float(values.size() - 1))), 0, values.size() - 1)
			var p := Vector2(x, _y(float(values[i])))
			var good := str(m.get("outcome", "")) == "good"
			draw_circle(p, 7.0, Color(0.02, 0.01, 0.07))
			if good:
				draw_circle(p, 5.0, StoryStyle.GOOD)
			else:
				draw_arc(p, 5.0, 0.0, TAU, 20, StoryStyle.WARN, 2.0, true)
