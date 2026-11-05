class_name PlaytestOverlay
extends Control
## The in-play playtest overlay (docs/DEBUG_MODE.md): a corner panel with the live identity of the scene (run, scene, pack and stem file names, source, mix, visual ids) and the phase / block
## clock, three big feedback buttons ("Don't like the MUSIC", "Don't like the VISUALS", "Like it", hotkeys M, V, L) that append to the playtest notes, a toast confirming each press, and a small
## toggle (hotkey H) that hides the panel and the buttons. It exists only while PlaytestMode.on(); RunPlay builds it then and never otherwise, so regular play keeps its silent HUD.

var play: Node  # the RunPlay scene (engine, data, hud, audio, run_path, trial_state)
var shown := true
var log: Array = []  # every entry this overlay has written (the tests read it)
var last_text := ""

var _panel: PanelContainer
var _label: Label
var _row: HBoxContainer
var _toggle: Button
var _toast: Label
var _toast_until_ms := 0
var _key := -999999
var _cache: Dictionary = {}  # "<data id>/<scene id>" -> PlaytestCatalog.scene_info


func setup(p_play: Node) -> void:
	play = p_play
	name = "PlaytestOverlay"
	PlaytestCatalog.stem_users()  # (read every run's stems once, now, so no frame of play pays for it)
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel = PanelContainer.new()
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.02, 0.08, 0.62)
	sb.border_color = Color(0.3, 0.9, 1.0, 0.5)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 8
	sb.content_margin_right = 8
	sb.content_margin_top = 4
	sb.content_margin_bottom = 4
	_panel.add_theme_stylebox_override("panel", sb)
	add_child(_panel)
	_label = Label.new()
	_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_label.add_theme_color_override("font_color", Color(0.9, 1.0, 0.95))
	_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	_label.add_theme_constant_override("outline_size", 3)
	_panel.add_child(_label)
	_row = HBoxContainer.new()
	_row.add_theme_constant_override("separation", 8)
	add_child(_row)
	for spec in [["music_dislike", "Don't like\nthe MUSIC", Color(1.0, 0.62, 0.62)], ["visual_dislike", "Don't like\nthe VISUALS", Color(1.0, 0.82, 0.5)], ["like", "Like it", Color(0.62, 1.0, 0.75)]]:
		var b := Button.new()
		b.text = str(spec[1])
		b.name = "Btn_" + str(spec[0])
		b.custom_minimum_size = Vector2(124, 64)
		b.focus_mode = Control.FOCUS_NONE
		b.modulate = spec[2]
		b.add_theme_font_size_override("font_size", 15)
		var verdict := str(spec[0])
		b.pressed.connect(func() -> void: record(verdict))
		_row.add_child(b)
	_toggle = Button.new()
	_toggle.name = "Btn_toggle"
	_toggle.text = "PT"
	_toggle.focus_mode = Control.FOCUS_NONE
	_toggle.custom_minimum_size = Vector2(56, 56)
	_toggle.add_theme_font_size_override("font_size", 18)
	_toggle.pressed.connect(toggle)
	_toggle.anchor_left = 1.0
	_toggle.anchor_right = 1.0
	_toggle.offset_left = -152
	_toggle.offset_right = -100
	_toggle.offset_top = 8
	_toggle.offset_bottom = 64
	add_child(_toggle)
	_toast = Label.new()
	_toast.visible = false
	_toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_toast.add_theme_font_size_override("font_size", 16)
	_toast.add_theme_color_override("font_color", Color(1, 1, 1))
	_toast.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_toast.add_theme_constant_override("outline_size", 5)
	_toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_toast)
	shown = PlaytestMode.overlay_shown
	resized.connect(_layout)
	_layout()
	_apply_shown()


func _layout() -> void:
	if _row == null:
		return
	var wide := size.x >= 760.0
	var fs := clampi(int(size.y * (0.034 if size.y < 500.0 else 0.016)), 10, 15)
	_label.add_theme_font_size_override("font_size", fs)
	var row_w := 3.0 * 124.0 + 16.0
	_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART  # (a long hotspot list wraps inside a panel at most 46 % of the width)
	_label.custom_minimum_size.x = clampf(size.x * 0.46, 300.0, 760.0)
	_row.position = Vector2((size.x - row_w) * 0.5 if wide else 14.0, 8.0 if wide else 74.0)
	_panel.position = Vector2(14.0, 70.0 if wide else 134.0)
	_panel.size = Vector2.ZERO
	_toast.position = Vector2(0.0, _row.position.y + 70.0)
	_toast.size = Vector2(size.x, 28.0)


func toggle() -> void:
	shown = not shown
	PlaytestMode.overlay_shown = shown
	_apply_shown()


func _apply_shown() -> void:
	_panel.visible = shown
	_row.visible = shown
	_toggle.modulate = Color(1, 1, 1, 0.9 if shown else 0.5)


func _unhandled_key_input(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k == null or not k.pressed or k.echo or k.ctrl_pressed or k.alt_pressed or k.meta_pressed:
		return
	var focus := get_viewport().gui_get_focus_owner() if is_inside_tree() else null
	if focus is LineEdit or focus is TextEdit:
		return
	match k.keycode:
		KEY_M:
			record("music_dislike")
		KEY_V:
			record("visual_dislike")
		KEY_L:
			record("like")
		KEY_H:
			toggle()
		_:
			return
	get_viewport().set_input_as_handled()


func _process(_delta: float) -> void:
	if _toast.visible and Time.get_ticks_msec() >= _toast_until_ms:
		_toast.visible = false


func show_toast(text: String, col: Color) -> void:
	_toast.text = text
	_toast.add_theme_color_override("font_color", col)
	_toast.visible = true
	_toast_until_ms = Time.get_ticks_msec() + 2200


# --- what is on screen now ---------------------------------------------------------------------------------------------------------

## The scene identity of the scene being played (cached per data and scene).
func current_info() -> Dictionary:
	var data: RunData = play.data
	var id := str(play.engine.node_id)
	var key := "%d/%s" % [data.get_instance_id(), id]
	if not _cache.has(key):
		_cache[key] = PlaytestCatalog.scene_info(data, id)
	return _cache[key]


## The clock and what plays at this moment: {phase, block (1 to 4), stage, stage_label, beat, t, energy, section, sections, pack, chart_pack, gains, counting_in, bassment}.
func live_state() -> Dictionary:
	var e: RunEngine = play.engine
	var data: RunData = play.data
	var t := float(play.hud.now_t)
	var beat := e.phase_beat_at(t)
	var node: Dictionary = data.nodes[e.node_id]
	var sec := data.section_at(e.node_id, maxf(beat, 0.0))
	var sections: Array = node.get("sections", [])
	var sec_idx := 0
	for i in sections.size():
		if sections[i] == sec:
			sec_idx = i
	var pack := str(sec["pack"]) if not sec.is_empty() else str(node["audio"])
	var gains: Dictionary = (play.audio.gains() if play.audio != null else {})
	var stage_g: Dictionary = e.cfg["stages"][e.stage]["gains"]
	return {"phase": e.phase_n, "block": clampi(e.block, 0, 3) + 1, "stage": e.stage, "stage_label": str(e.cfg["stages"][e.stage]["label"]), "cue": str(e.cfg["stages"][e.stage]["cue"]), "beat": beat, "t": t,
		"energy": e.energy, "section": sec_idx + 1, "sections": maxi(sections.size(), 1), "pack": pack, "chart_pack": data.chart_pack_at(e.node_id, maxf(beat, 0.0)), "gains": gains, "stage_gains": stage_g,
		"counting_in": t < 0.0, "bassment": str(play.trial_state) != "", "bass_in": e.bass_origin >= 0}


## The panel's lines for a scene identity and a live state (pure: the tests call it with hand-made input).
static func lines(info: Dictionary, live: Dictionary) -> Array:
	var out: Array = []
	if bool(live.get("bassment", false)):
		return ["%s  THE BASSMENT (the dungeon between two scenes: not a run scene)" % str(info.get("run", "")).to_upper(), "phase %d" % int(live.get("phase", 0))]
	var a: Dictionary = info["audio"]
	var v: Dictionary = info["visual"]
	out.append("%s  %s  \"%s\"   %d BPM" % [str(info["run"]).to_upper(), str(info["id"]), str(info["title"]), int(info["bpm"])])
	var beat := float(live["beat"])
	out.append("phase %d | block %d/4 | stage %d %s (%s cues) | %s | energy %.0f" % [int(live["phase"]), int(live["block"]), int(live["stage"]) + 1, str(live["stage_label"]), str(live["cue"]),
		("count-in" if bool(live.get("counting_in", false)) else "beat %.1f/%d" % [beat, int(info["phase_beats"])]), float(live["energy"])])
	var cur: Dictionary = a["sections"][0]
	for s in a["sections"]:
		if str(s["pack"]) == str(live["pack"]):
			cur = s
	var ident: Dictionary = cur["audio"]
	var sec_txt := (" | section %d/%d of %s" % [int(live["section"]), int(live["sections"]), PlaytestCatalog.packs_line(info)]) if a["switches"] else ""
	if (a["arrangement_ids"] as Array).size() > 1:
		sec_txt += " | arr %s (%d/%d)" % [str(a["arrangement"]), int(a["arrangement_pick"]) + 1, (a["arrangement_ids"] as Array).size()]
	out.append("MUSIC %s (%s) | %s | tier %d%s" % [str(live["pack"]), str(ident["label"]), str(a["source_label"]), int(a["tier"]), sec_txt])
	for pair in PlaytestCatalog.VOICES:
		var vv: Dictionary = (ident["voices"] as Dictionary).get(str(pair[0]), {})
		var sw: Array = vv.get("shared_with", [])
		out.append("   %s  %s   (%s%s)" % [str(vv.get("role", pair[1])), str(vv.get("file", "?")), str(vv.get("shared_file", "?")), (", shared with %d scenes" % sw.size()) if not sw.is_empty() else ""])
	var ch: Dictionary = (cur["chart"] as Dictionary).get("charts", {})
	if str(live.get("chart_pack", live["pack"])) != str(live["pack"]):
		out.append("   cues from %s" % str(live["chart_pack"]))
	out.append("   cues: %s / %s" % [str(ch.get("drums", "?")), str(ch.get("bass", "?"))])
	var sg: Dictionary = live["stage_gains"]
	var m: Dictionary = info["mix"]
	var carry: Dictionary = m["carry"]
	var live_g: Dictionary = live.get("gains", {})
	out.append("MIX stage gains d%.2f b%.2f s%.2f%s | bass bus %s | level %+.1f dB | carry %s" % [float(sg.get("drums", 0.0)), float(sg.get("bass", 0.0)), float(sg.get("other", 0.0)),
		(" (heard d%.2f b%.2f s%.2f)" % [float(live_g.get("drums", 0.0)), float(live_g.get("bass", 0.0)), float(live_g.get("other", 0.0))]) if not live_g.is_empty() else "",
		"on" if bool(m["bass_bus"]["enabled"]) else "off", float(m["gain_db"]), ("%.2f/%.0f beats" % [float(carry.get("gain", 0.0)), float(carry.get("beats", 0.0))]) if float(carry.get("gain", 0.0)) > 0.0 else "off"])
	out.append("VISUAL map %s | view %s | %s, light %.2f | pieces on: %s" % [str(v["map"]), str(v["view"]), str(v["time_of_day"]), float(v["light"]), ", ".join(PackedStringArray(v["pieces_on"])) if not (v["pieces_on"] as Array).is_empty() else "none"])
	var hs: Array = (v["hotspots"] as Array).map(func(h: Dictionary) -> String: return str(h["id"]))
	out.append("   cast: %s | hotspots: %s" % [", ".join(PackedStringArray(v["cast"])) if not (v["cast"] as Array).is_empty() else "none", ", ".join(PackedStringArray(hs)) if not hs.is_empty() else "none"])
	return out


## Called every frame by RunPlay (cheap: the text is rebuilt four times per song second and when the scene changes).
func refresh() -> void:
	if play == null or play.engine == null:
		return
	var key: int = int(floor(float(play.hud.now_t) * 4.0)) * 1000 + int(play.engine.phase_n)
	if key == _key:
		return
	_key = key
	var info := _bassment_info() if str(play.trial_state) != "" else current_info()
	var live := live_state()
	last_text = "\n".join(PackedStringArray(lines(info, live)))
	_label.text = last_text


func _bassment_info() -> Dictionary:
	return {"run": str(play.run_path) if str(play.run_path) != "" else "main", "id": "bassment", "title": "The Bassment", "world": "bassment", "bpm": int(play.data.cfg["timing"]["bpm"]), "audio": {}, "visual": {}}


# --- feedback ----------------------------------------------------------------------------------------------------------------------

## Appends one entry (music_dislike | visual_dislike | like | note) to the notes files and shows the toast. Returns the entry.
func record(verdict: String, text := "") -> Dictionary:
	var info := _bassment_info() if str(play.trial_state) != "" else current_info()
	var live := live_state()
	var e := PlaytestNotes.make_entry(info, live, verdict, text)
	var ok := PlaytestNotes.append(e)
	log.append(e)
	var what: String = str(PlaytestNotes.VERDICTS.get(verdict, verdict))
	var col := Color(1.0, 0.7, 0.7) if verdict == "music_dislike" else (Color(1.0, 0.85, 0.55) if verdict == "visual_dislike" else Color(0.7, 1.0, 0.8))
	show_toast(("Saved: %s  |  %s  |  %s" % [what, str(e["scene"]), str(e["pack_playing"])]) if ok else "COULD NOT WRITE THE NOTES FILE", col if ok else Color(1, 0.3, 0.3))
	return e
