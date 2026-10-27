extends Control
## The level screen: song transport, clock, judgement, lanes and (from M1) the battle. Milestone M0 version:
## the battlefield area holds the debug panel that proves stem muting and restoration without a restart.

const COUNTDOWN_S := 2.0
const RESUME_COUNTDOWN_S := 3.0
const BATTLE_FRACTION := 0.625

var level: Level
var transport: StemTransport
var clock: SongClock
var judge: Judge
var lane_input: LaneInput
var lane_view: LaneView

var _battle_area: Control
var _hud: VBoxContainer
var _stats: Label
var _countdown_label: Label
var _pause_panel: PanelContainer
var _resume_at_wall := -1.0
var _ended := false
var _started_wall := 0.0
var _mute_toggles: Dictionary = {}


func _ready() -> void:
	var pack := Session.pack_dir
	if pack.is_empty():
		var packs := Session.available_packs()
		if packs.is_empty():
			_fatal("No song packs found in songs/")
			return
		pack = packs[0]["dir"]
	var loaded := LevelLoader.load_pack(pack)
	if loaded["level"] == null:
		_fatal("Song pack rejected:\n" + "\n".join(PackedStringArray(loaded["errors"])))
		return
	level = loaded["level"]
	for w in loaded["warnings"]:
		print("warning: ", w)

	transport = StemTransport.new()
	add_child(transport)
	var err := transport.load_level(level)
	if not err.is_empty():
		_fatal(err)
		return
	clock = SongClock.new(transport)
	clock.calibration_ms = Session.calibration_ms
	judge = Judge.new()
	judge.setup(level.notes)

	_build_layout()
	lane_input = LaneInput.new()
	add_child(lane_input)
	lane_input.rect_provider = lane_view.button_rects
	lane_input.lane_pressed.connect(_on_lane_pressed)
	lane_input.lane_released.connect(_on_lane_released)
	transport.song_finished.connect(_on_song_finished)

	_started_wall = float(Time.get_ticks_msec()) / 1000.0
	clock.begin_countdown(COUNTDOWN_S)


func _build_layout() -> void:
	_battle_area = Control.new()
	_battle_area.name = "BattleArea"
	_battle_area.anchor_right = 1.0
	_battle_area.anchor_bottom = BATTLE_FRACTION
	add_child(_battle_area)
	var bg := ColorRect.new()
	bg.color = Color(0.16, 0.2, 0.14)
	bg.anchor_right = 1.0
	bg.anchor_bottom = 1.0
	_battle_area.add_child(bg)
	var placeholder := Label.new()
	placeholder.text = "battlefield (milestone M1)"
	placeholder.anchor_left = 0.5
	placeholder.anchor_right = 0.5
	placeholder.anchor_top = 0.5
	placeholder.anchor_bottom = 0.5
	placeholder.grow_horizontal = Control.GROW_DIRECTION_BOTH
	placeholder.modulate = Color(1, 1, 1, 0.4)
	_battle_area.add_child(placeholder)

	lane_view = LaneView.new()
	lane_view.name = "Lanes"
	lane_view.anchor_top = BATTLE_FRACTION
	lane_view.anchor_right = 1.0
	lane_view.anchor_bottom = 1.0
	lane_view.setup(level, judge, clock)
	add_child(lane_view)

	# debug and status panel (M0): proves muting and restoration without a restart
	_hud = VBoxContainer.new()
	_hud.position = Vector2(12, 12)
	_hud.add_theme_constant_override("separation", 2)
	_battle_area.add_child(_hud)
	_stats = Label.new()
	_stats.add_theme_font_size_override("font_size", 18)
	_hud.add_child(_stats)
	var row := HBoxContainer.new()
	_hud.add_child(row)
	for key in StemTransport.STEM_ORDER:
		var cb := CheckButton.new()
		cb.text = "mute " + key
		cb.focus_mode = Control.FOCUS_NONE
		cb.toggled.connect(func(on: bool) -> void: _on_mute_toggled(key, on))
		row.add_child(cb)
		_mute_toggles[key] = cb
	var hint := Label.new()
	hint.text = "Keys: F = kick, Space = bass (hold), J = snare, Esc = pause. Muting kick/snare here stands in for losing the factory/barracks."
	hint.add_theme_font_size_override("font_size", 14)
	hint.modulate = Color(1, 1, 1, 0.6)
	_hud.add_child(hint)

	var pause_btn := Button.new()
	pause_btn.text = "II"
	pause_btn.focus_mode = Control.FOCUS_NONE
	pause_btn.custom_minimum_size = Vector2(64, 48)
	pause_btn.anchor_left = 1.0
	pause_btn.anchor_right = 1.0
	pause_btn.offset_left = -76
	pause_btn.offset_top = 12
	pause_btn.offset_right = -12
	pause_btn.offset_bottom = 60
	pause_btn.pressed.connect(_pause)
	_battle_area.add_child(pause_btn)

	_countdown_label = Label.new()
	_countdown_label.add_theme_font_size_override("font_size", 96)
	_countdown_label.anchor_left = 0.5
	_countdown_label.anchor_right = 0.5
	_countdown_label.anchor_top = 0.35
	_countdown_label.anchor_bottom = 0.35
	_countdown_label.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_countdown_label.grow_vertical = Control.GROW_DIRECTION_BOTH
	_countdown_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_countdown_label)

	_pause_panel = PanelContainer.new()
	_pause_panel.anchor_left = 0.5
	_pause_panel.anchor_right = 0.5
	_pause_panel.anchor_top = 0.5
	_pause_panel.anchor_bottom = 0.5
	_pause_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_pause_panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	_pause_panel.visible = false
	add_child(_pause_panel)
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 12)
	_pause_panel.add_child(pv)
	var title := Label.new()
	title.text = "Paused"
	title.add_theme_font_size_override("font_size", 36)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pv.add_child(title)
	for item in [["Resume", _resume], ["Retry", _retry], ["Quit to menu", _quit]]:
		var b := Button.new()
		b.text = item[0]
		b.custom_minimum_size = Vector2(320, 56)
		b.add_theme_font_size_override("font_size", 24)
		b.pressed.connect(item[1])
		pv.add_child(b)


func _fatal(message: String) -> void:
	push_error(message)
	var l := Label.new()
	l.text = message + "\n\n(Esc to return)"
	l.anchor_right = 1.0
	l.anchor_bottom = 1.0
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(l)
	_ended = true


func _process(_delta: float) -> void:
	if _ended or clock == null:
		return
	if _resume_at_wall >= 0.0:
		var remaining := _resume_at_wall - float(Time.get_ticks_msec()) / 1000.0
		if remaining <= 0.0:
			_resume_at_wall = -1.0
			_countdown_label.text = ""
			clock.resume()
			lane_input.enabled = true
		else:
			_countdown_label.text = str(ceili(remaining))
		return
	if clock.state == SongClock.State.PAUSED:
		return
	clock.tick()
	var t := clock.judge_time()
	if clock.state == SongClock.State.COUNTDOWN:
		_countdown_label.text = str(ceili(clock.countdown_remaining()))
	elif clock.state == SongClock.State.PLAYING and not _countdown_label.text.is_empty():
		_countdown_label.text = ""
	judge.update(t)
	var wall := float(Time.get_ticks_msec()) / 1000.0
	for ev in judge.drain_events():
		_on_judge_event(ev, wall)
	for lane in LaneView.LANE_ORDER:
		lane_view.lane_down[lane] = lane_input.is_lane_down(lane)
	_stats.text = "%s   t=%6.2f s  bar %d   combo %d (best %d)   acc %.1f%%   P %d  G %d  M %d  stray %d   latency %.1f ms  cal %+.0f ms" % [
		level.title, t, level.bar_of_tick(level.seconds_to_tick(maxf(t, 0.0))), judge.combo, judge.best_combo, judge.accuracy() * 100.0,
		judge.perfect, judge.good, judge.misses, judge.strays, clock.output_latency * 1000.0, clock.calibration_ms]
	if clock.state == SongClock.State.PLAYING and t >= level.duration_seconds():
		_finish("song_end")


func _on_judge_event(ev: Dictionary, wall: float) -> void:
	var lane: String = ev.get("lane", "")
	match ev["kind"]:
		"perfect":
			lane_view.show_feedback(lane, "PERFECT", Color(1.0, 0.95, 0.6), wall)
		"good":
			lane_view.show_feedback(lane, "GOOD", Color(0.7, 0.95, 0.7), wall)
		"hold_start":
			lane_view.show_feedback(lane, "HOLD", Color(0.7, 0.85, 1.0), wall)
		"miss", "hold_fail":
			lane_view.show_feedback(lane, "MISS", Color(1.0, 0.45, 0.4), wall)
		"stray":
			lane_view.show_feedback(lane, "...", Color(0.7, 0.7, 0.7), wall)


func _on_lane_pressed(lane: String, touch_id: int) -> void:
	if _ended or clock.state == SongClock.State.PAUSED:
		return
	judge.press(lane, clock.judge_time(), touch_id)


func _on_lane_released(lane: String, touch_id: int) -> void:
	if _ended:
		return
	judge.release(lane, clock.judge_time(), touch_id)


func _on_mute_toggled(key: String, on: bool) -> void:
	transport.set_stem_muted(key, on)
	if key == "kick" or key == "snare":
		judge.set_lane_available(key, not on)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if _ended:
			_quit()
		elif clock.state == SongClock.State.PAUSED:
			_resume()
		else:
			_pause()
		get_viewport().set_input_as_handled()


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_APPLICATION_PAUSED:
		if clock != null and not _ended and clock.state in [SongClock.State.PLAYING, SongClock.State.COUNTDOWN]:
			_pause()


func _pause() -> void:
	if _ended or clock.state == SongClock.State.PAUSED or _resume_at_wall >= 0.0:
		return
	clock.pause()
	judge.void_active_holds()
	lane_input.clear()
	lane_input.enabled = false
	_pause_panel.visible = true
	_countdown_label.text = ""


func _resume() -> void:
	if clock.state != SongClock.State.PAUSED:
		return
	_pause_panel.visible = false
	_resume_at_wall = float(Time.get_ticks_msec()) / 1000.0 + RESUME_COUNTDOWN_S


func _retry() -> void:
	transport.stop()
	get_tree().reload_current_scene()


func _quit() -> void:
	if transport != null:
		transport.stop()
	get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn")


func _on_song_finished() -> void:
	if not _ended:
		_finish("song_end")


func _finish(reason: String) -> void:
	_ended = true
	lane_input.enabled = false
	clock.end()
	transport.fade_out(0.6)
	Session.last_result = {
		"outcome": "incomplete",
		"reason": reason,
		"level": level.title,
		"accuracy": judge.accuracy(),
		"perfect": judge.perfect,
		"good": judge.good,
		"misses": judge.misses,
		"strays": judge.strays,
		"best_combo": judge.best_combo,
		"judged": judge.judged_count(),
		"rewards": judge.rewards.duplicate(),
		"duration_s": float(Time.get_ticks_msec()) / 1000.0 - _started_wall,
	}
	await get_tree().create_timer(0.7).timeout
	transport.stop()
	get_tree().change_scene_to_file("res://src/scenes/result.tscn")
