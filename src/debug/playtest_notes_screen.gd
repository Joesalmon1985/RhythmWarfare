extends Control
## The playtest notes so far (docs/DEBUG_MODE.md): newest first, with Copy all (the readable file) and Copy JSON lines, and where the files live so the notes can be pasted back to Claude.

var copied := ""  # the last text handed to the clipboard (the tests read it)


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
	var entries := PlaytestNotes.read_all()
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 10)
	root.add_child(header)
	header.add_child(UiStyle.button("Back", func() -> void: get_tree().change_scene_to_file(PlaytestMode.LIST_SCENE), 96, 48))
	var t := UiStyle.title("PLAYTEST NOTES (%d)" % entries.size(), 28)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(t)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 10)
	root.add_child(actions)
	var status := UiStyle.note("", UiStyle.GOOD, 15)
	var copy_all := UiStyle.button("Copy all", func() -> void:
		copy_text(PlaytestNotes.all_markdown())
		status.text = "Copied %d notes to the clipboard: paste them into the chat." % PlaytestNotes.count(), 0, 52)
	copy_all.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	copy_all.add_theme_font_size_override("font_size", 24)
	actions.add_child(copy_all)
	var copy_json := UiStyle.button("Copy JSON lines", func() -> void:
		copy_text(PlaytestNotes.all_jsonl())
		status.text = "Copied the machine-readable lines.", 0, 52)
	copy_json.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	actions.add_child(copy_json)
	root.add_child(status)
	root.add_child(UiStyle.note(where_text(), UiStyle.MUTED, 14))
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	root.add_child(scroll)
	var body := VBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 6)
	scroll.add_child(body)
	if entries.is_empty():
		body.add_child(UiStyle.note("No notes yet. Start a scene from the list and press the verdict buttons (or M, V, L on a keyboard) while it plays.", UiStyle.TEXT, 17))
	for i in range(entries.size() - 1, -1, -1):
		var e: Dictionary = entries[i]
		var card := PanelContainer.new()
		body.add_child(card)
		var v := VBoxContainer.new()
		card.add_child(v)
		var verdict := str(e.get("verdict", ""))
		var col := UiStyle.WARN if verdict.ends_with("dislike") else (UiStyle.GOOD if verdict == "like" else UiStyle.TEXT)
		v.add_child(UiStyle.note(PlaytestNotes.summary_line(e), col, 15))
		var st: Dictionary = e.get("stems", {})
		if not st.is_empty():
			v.add_child(UiStyle.note("%s   |   %s   |   %s" % [str(st.get("drums", "")), str(st.get("bass", "")), str(st.get("other", ""))], UiStyle.MUTED, 12))
		var vis: Dictionary = e.get("visual", {})
		v.add_child(UiStyle.note("phase %d block %d \"%s\"   visual: %s / %s / %s" % [int(e.get("phase", 0)), int(e.get("block", 0)), str(e.get("stage", "")), str(vis.get("map", "")), str(vis.get("view", "")), str(vis.get("light", ""))], UiStyle.MUTED, 12))


func copy_text(text: String) -> void:
	copied = text
	DisplayServer.clipboard_set(text)


## Where the two files are on this machine and how to get them off a phone.
static func where_text() -> String:
	var real := PlaytestNotes.real_dir().trim_suffix("/")
	return "Files: %s/%s and %s/%s.  Windows: %%APPDATA%%\\Godot\\app_userdata\\Rhythm Warfare\\.  Android: the app's private folder (Android/data/com.joesalmon.rhythmwarfare/files on most phones): easiest is Copy all and paste into the chat; with USB debugging, adb shell run-as com.joesalmon.rhythmwarfare cat files/playtest_notes.md." % [real, PlaytestNotes.MD_NAME, real, PlaytestNotes.JSONL_NAME]


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file(PlaytestMode.LIST_SCENE)
		get_viewport().set_input_as_handled()
