class_name SettingsPanel
extends Control
## Player settings, saved to user://settings.cfg as they change: music volume, timing calibration, cue lead-in, pad
## size, high contrast, reduced effects, vibration, desktop key labels, and a reset. Used as the Settings screen and
## as an overlay from the pause menu (in_game: calibration opens only from the menus, which need the audio to itself).

signal closed

var in_game := false
var _rows: VBoxContainer


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var parts := UiStyle.screen(self, "Settings", func() -> void: closed.emit())
	_rows = parts["content"]
	_build()


func _build() -> void:
	for c in _rows.get_children():
		c.queue_free()
	_slider("Music volume", 0.0, 1.0, 0.05, Session.music_volume, func(v: float) -> String: return "%d%%" % int(round(v * 100.0)),
		func(v: float) -> void:
			Session.music_volume = v
			Session.apply_volume())
	_slider("Cue lead-in (how early a ring appears)", Session.LEAD_IN_MIN_S, Session.LEAD_IN_MAX_S, 0.05, Session.cue_lead_in_s,
		func(v: float) -> String: return "%.2f s" % v, func(v: float) -> void: Session.cue_lead_in_s = v)
	_slider("Pad size", 0, Session.PAD_SIZES.size() - 1, 1, Session.pad_size,
		func(v: float) -> String: return ["Compact", "Standard", "Large"][int(v)], func(v: float) -> void: Session.pad_size = int(v))
	_toggle("High contrast pads", Session.high_contrast, func(on: bool) -> void: Session.high_contrast = on)
	_toggle("Reduced effects", Session.reduced_effects, func(on: bool) -> void: Session.reduced_effects = on)
	_toggle("Vibrate on hits (phones)", Session.vibration, func(on: bool) -> void: Session.vibration = on)
	_toggle("Show keyboard keys on pads (D F J K)", Session.show_keys, func(on: bool) -> void: Session.show_keys = on)
	var cal := HBoxContainer.new()
	cal.add_theme_constant_override("separation", UiStyle.GAP)
	var cl := UiStyle.note("Timing calibration: %+.0f ms" % Session.calibration_ms, UiStyle.TEXT, 20)
	cl.autowrap_mode = TextServer.AUTOWRAP_OFF
	cl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cal.add_child(cl)
	if not in_game:
		cal.add_child(UiStyle.button("Calibrate", func() -> void: get_tree().change_scene_to_file("res://src/scenes/calibration.tscn"), 200))
	else:
		cal.add_child(UiStyle.note("(calibrate from the main menu's Settings)", UiStyle.MUTED, 16))
	_rows.add_child(cal)
	_rows.add_child(UiStyle.button("Reset to defaults (keeps calibration)", func() -> void:
		Session.reset_settings(false)
		_build(), 0, 56))


func _slider(label: String, lo: float, hi: float, step: float, value: float, fmt: Callable, apply: Callable) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", UiStyle.GAP)
	var l := UiStyle.note(label, UiStyle.TEXT, 20)
	l.autowrap_mode = TextServer.AUTOWRAP_OFF
	l.custom_minimum_size = Vector2(380, 0)
	row.add_child(l)
	var s := HSlider.new()
	s.min_value = lo
	s.max_value = hi
	s.step = step
	s.value = value
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.custom_minimum_size = Vector2(240, 48)
	row.add_child(s)
	var v := UiStyle.note(fmt.call(value), UiStyle.ACCENT, 20)
	v.autowrap_mode = TextServer.AUTOWRAP_OFF
	v.custom_minimum_size = Vector2(120, 0)
	row.add_child(v)
	s.value_changed.connect(func(x: float) -> void:
		apply.call(x)
		v.text = fmt.call(x)
		Session.save_settings())
	_rows.add_child(row)


func _toggle(label: String, value: bool, apply: Callable) -> void:
	var b := CheckButton.new()
	b.text = label
	b.button_pressed = value
	b.custom_minimum_size = Vector2(0, 52)
	b.toggled.connect(func(on: bool) -> void:
		apply.call(on)
		Session.save_settings())
	_rows.add_child(b)
