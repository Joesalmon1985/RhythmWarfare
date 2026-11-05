extends Control
## Debug / Playtest: every playable scene of the main 174 BPM run and of the paths, grouped by run and world. A row shows the scene id, its title, the BPM, the difficulty tier and a compact audio line
## (set names, pack ids, OWNER or PLACEHOLDER); tapping the row starts the game AT that scene (the run machinery's own start, PlaytestMode.start); "Info" opens the scene's full identity (the
## audio files named as the owner's files are, the mix in force, the visual ids, the hotspots) with a START HERE button. The options at the top are PlaytestMode's. docs/DEBUG_MODE.md.

const ROW_FONT := 17

var runs: Array = []  # PlaytestCatalog.runs()
var rows: Dictionary = {}  # "<run id>/<scene id>" -> the start Button (the tests press them)
var info_buttons: Dictionary = {}  # same key -> the Info Button
var headers: Dictionary = {}  # run id -> its heading Label (the jump chips scroll to it)
var detail_info: Dictionary = {}  # the scene whose detail is open ({} when the list shows)

var _scroll: ScrollContainer
var _content: VBoxContainer
var _list_view: VBoxContainer
var _detail_view: VBoxContainer
var _detail_scroll: ScrollContainer
var _detail_body: VBoxContainer
var _detail_title: Label
var _detail_start: Button
var _notes_btn: Button
var _infos: Dictionary = {}  # key -> scene info (built with the rows)
var _run_id_of := {}  # key -> run id
var _scene_of := {}  # key -> scene id


func _ready() -> void:
	theme = UiStyle.theme()
	var bg := ColorRect.new()
	bg.color = UiStyle.BG
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	var safe := UiStyle.safe_margins(self)
	margin.add_theme_constant_override("margin_left", int(safe.x) + 12)
	margin.add_theme_constant_override("margin_right", int(safe.y) + 12)
	margin.add_theme_constant_override("margin_top", 10)
	margin.add_theme_constant_override("margin_bottom", 10)
	add_child(margin)
	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 8)
	margin.add_child(root)
	_list_view = VBoxContainer.new()
	_list_view.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_list_view.add_theme_constant_override("separation", 8)
	root.add_child(_list_view)
	_detail_view = VBoxContainer.new()
	_detail_view.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_detail_view.add_theme_constant_override("separation", 8)
	_detail_view.visible = false
	root.add_child(_detail_view)
	_build_list()
	_build_detail()
	var want := OS.get_environment("RW_DEBUG_DETAIL")  # screenshot aid: open <run id>/<scene id> straight away (docs/DEBUG_MODE.md)
	if want.contains("/") and rows.has(want):
		open_detail(want.get_slice("/", 0), want.get_slice("/", 1))


# --- the list ---------------------------------------------------------------------------------------------------------------------

func _build_list() -> void:
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 10)
	_list_view.add_child(header)
	header.add_child(UiStyle.button("Back", func() -> void: get_tree().change_scene_to_file(PlaytestMode.HOME_SCENE), 96, 48))
	var t := UiStyle.title("DEBUG / PLAYTEST", 28)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(t)
	_notes_btn = UiStyle.button("Notes (%d)" % PlaytestNotes.count(), func() -> void: get_tree().change_scene_to_file(PlaytestMode.NOTES_SCENE), 120, 48)
	header.add_child(_notes_btn)
	_scroll = ScrollContainer.new()
	_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_list_view.add_child(_scroll)
	_content = VBoxContainer.new()
	_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_content.add_theme_constant_override("separation", 8)
	_scroll.add_child(_content)
	_content.add_child(UiStyle.note("Tap a scene to start the game at it. Info shows what plays and what is drawn. Pause > Back to scene list returns here. Your verdict buttons write playtest_notes.md.", UiStyle.MUTED, 15))
	_build_options()
	runs = PlaytestCatalog.runs()
	var chips := HFlowContainer.new()
	chips.add_theme_constant_override("h_separation", 8)
	chips.add_theme_constant_override("v_separation", 8)
	_content.add_child(chips)
	for r in runs:
		var rid := str(r["id"])
		chips.add_child(UiStyle.button("%s (%d)" % [("Main 174" if rid == "main" else str(r["title"])), int(r["scene_count"])], func() -> void: _jump(rid), 0, 44))
	for r in runs:
		_build_run(r)
	var keep := PlaytestMode.list_scroll
	PlaytestMode.list_scroll = 0
	var jump := OS.get_environment("RW_DEBUG_SCROLL")  # screenshot aid: scroll to a run's heading
	if keep > 0 or headers.has(jump):
		await get_tree().process_frame
		await get_tree().process_frame
		_scroll.scroll_vertical = keep if keep > 0 else int((headers[jump] as Control).position.y)


func _jump(run_id: String) -> void:
	if headers.has(run_id):
		_scroll.scroll_vertical = int((headers[run_id] as Control).position.y)


func _build_options() -> void:
	var box := PanelContainer.new()
	_content.add_child(box)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	box.add_child(v)
	v.add_child(UiStyle.note("OPTIONS (for scenes started from this list)", UiStyle.ACCENT, 15))
	var flow := HFlowContainer.new()
	flow.add_theme_constant_override("h_separation", 16)
	flow.add_theme_constant_override("v_separation", 4)
	v.add_child(flow)
	var toggles: Array = [
		["Continue into the next scene when it ends (off: back to this list)", PlaytestMode.continue_run, func(on: bool) -> void: PlaytestMode.continue_run = on],
		["Autoplay the pads (the test bot, perfect play)", PlaytestMode.autoplay, func(on: bool) -> void: PlaytestMode.autoplay = on],
		["Give the hotspot flags this scene needs", PlaytestMode.give_flags, func(on: bool) -> void: PlaytestMode.give_flags = on],
		["Also show the old play text (titles, captions)", PlaytestMode.dev_text, func(on: bool) -> void: PlaytestMode.dev_text = on],
	]
	for tg in toggles:
		var cb := CheckButton.new()
		cb.text = str(tg[0])
		cb.button_pressed = bool(tg[1])
		cb.add_theme_font_size_override("font_size", 15)
		cb.focus_mode = Control.FOCUS_NONE
		var cbk: Callable = tg[2]
		cb.toggled.connect(func(on: bool) -> void: cbk.call(on))
		flow.add_child(cb)
	var row := HFlowContainer.new()
	row.add_theme_constant_override("h_separation", 10)
	v.add_child(row)
	row.add_child(_flat_label("Start energy"))
	var ob := OptionButton.new()
	for c in PlaytestMode.ENERGY_CHOICES:
		ob.add_item(str((c as Array)[0]))
	ob.selected = PlaytestMode.energy_choice
	ob.custom_minimum_size = Vector2(230, 44)
	ob.item_selected.connect(func(i: int) -> void: PlaytestMode.energy_choice = i)
	row.add_child(ob)
	row.add_child(_flat_label("   Main-run arrangement"))
	var ab := OptionButton.new()  # every main-run scene has three arrangements of its music family; the game picks one by the per-run seed
	ab.add_item("As the game picks (seed %d)" % RunData.run_seed())
	ab.add_item("1st arrangement of every scene")
	ab.add_item("2nd arrangement of every scene")
	ab.add_item("3rd arrangement of every scene")
	ab.selected = PlaytestMode.arrangement
	ab.custom_minimum_size = Vector2(300, 44)
	ab.item_selected.connect(func(i: int) -> void:
		PlaytestMode.set_arrangement(i)
		PlaytestMode.list_scroll = _scroll.scroll_vertical
		get_tree().reload_current_scene())
	row.add_child(ab)


## A label that does not wrap (a wrapping label has no width inside a flow container).
func _flat_label(text: String) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", 15)
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.custom_minimum_size.y = 48
	return l


func _build_run(r: Dictionary) -> void:
	var rid := str(r["id"])
	var h := UiStyle.title("%s   %d BPM   %d scenes" % [str(r["title"]).to_upper(), int(r["bpm"]), int(r["scene_count"])], 20)
	h.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	h.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_content.add_child(h)
	headers[rid] = h
	if not (r["errors"] as Array).is_empty():
		_content.add_child(UiStyle.note("DATA ERRORS: " + "; ".join(PackedStringArray(r["errors"])), UiStyle.WARN, 15))
	var data: RunData = r["data"]
	for w in r["worlds"]:
		var wl := UiStyle.note("%s   (%s)" % [str(w["title"]).to_upper(), str(w["id"])], UiStyle.GOOD, 16)
		_content.add_child(wl)
		for sid in w["scenes"]:
			_build_row(rid, data, str(sid))


func _build_row(rid: String, data: RunData, sid: String) -> void:
	var info := PlaytestCatalog.scene_info(data, sid)
	var key := "%s/%s" % [rid, sid]
	_infos[key] = info
	_run_id_of[key] = rid
	_scene_of[key] = sid
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	_content.add_child(row)
	var b := Button.new()
	b.text = "%s%s   %s\n%d BPM  tier %d   %s" % ["! " if not (info["audio"]["problems"] as Array).is_empty() else "", sid, str(info["title"]), int(info["bpm"]), int(info["tier"]), PlaytestCatalog.row_audio_line(info)]
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	b.clip_text = false
	b.custom_minimum_size = Vector2(120, 76)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.add_theme_font_size_override("font_size", ROW_FONT)
	b.pressed.connect(func() -> void: start_scene(rid, sid))
	row.add_child(b)
	rows[key] = b
	var ib := UiStyle.button("Info", func() -> void: open_detail(rid, sid), 88, 76)
	ib.add_theme_font_size_override("font_size", ROW_FONT)
	row.add_child(ib)
	info_buttons[key] = ib


func start_scene(run_id: String, scene_id: String) -> void:
	PlaytestMode.start(get_tree(), run_id, scene_id)


# --- the detail ---------------------------------------------------------------------------------------------------------------------

func _build_detail() -> void:
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 10)
	_detail_view.add_child(header)
	header.add_child(UiStyle.button("List", close_detail, 96, 48))
	_detail_title = UiStyle.title("", 22)
	_detail_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	_detail_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_detail_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	header.add_child(_detail_title)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 10)
	_detail_view.add_child(actions)
	_detail_start = UiStyle.button("START HERE", func() -> void:
		start_scene(str(detail_info["run"]), str(detail_info["id"])), 0, 56)
	_detail_start.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_detail_start.add_theme_font_size_override("font_size", 24)
	actions.add_child(_detail_start)
	actions.add_child(UiStyle.button("Copy these details", func() -> void: DisplayServer.clipboard_set(PlaytestCatalog.identity_text(detail_info)), 220, 56))
	_detail_scroll = ScrollContainer.new()
	_detail_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_detail_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_detail_view.add_child(_detail_scroll)
	_detail_body = VBoxContainer.new()
	_detail_body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_detail_body.add_theme_constant_override("separation", 4)
	_detail_scroll.add_child(_detail_body)


func open_detail(run_id: String, scene_id: String) -> void:
	var key := "%s/%s" % [run_id, scene_id]
	detail_info = _infos[key]
	_detail_title.text = "%s  %s" % [scene_id, str(detail_info["title"])]
	for c in _detail_body.get_children():
		c.queue_free()
	_detail_body.add_child(UiStyle.note(PlaytestCatalog.scene_heading(detail_info), UiStyle.TEXT, 16))
	for group in [PlaytestCatalog.audio_sections(detail_info), PlaytestCatalog.mix_sections(detail_info), PlaytestCatalog.visual_sections(detail_info)]:
		for sec in group:
			var hl := UiStyle.note(str(sec[0]), UiStyle.ACCENT, 15)
			_detail_body.add_child(hl)
			for l in sec[1]:
				var lab := UiStyle.note(str(l), UiStyle.WARN if str(sec[0]) == "PROBLEMS" else UiStyle.TEXT, 15)
				_detail_body.add_child(lab)
	_list_view.visible = false
	_detail_view.visible = true
	_detail_scroll.scroll_vertical = 0


func close_detail() -> void:
	detail_info = {}
	_detail_view.visible = false
	_list_view.visible = true


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if _detail_view.visible:
			close_detail()
		else:
			get_tree().change_scene_to_file(PlaytestMode.HOME_SCENE)
		get_viewport().set_input_as_handled()
