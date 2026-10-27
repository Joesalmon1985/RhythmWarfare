extends Control
## The level screen: song transport and clock, the match (judgement + enemy schedule + battle), the battlefield
## view, the HUD and the lanes. Pause freezes music, notes, enemy events, combat and repair together.

const COUNTDOWN_S := 2.0
const RESUME_COUNTDOWN_S := 3.0
const BATTLE_FRACTION := 0.625
const END_FADE_S := 0.6

var level: Level
var transport: StemTransport
var clock: SongClock
var match_ref: Match
var lane_input: LaneInput
var lane_view: LaneView
var battle_view: BattleView
var hud: Hud

var _battle_area: Control
var _debug_panel: VBoxContainer
var _debug_label: Label
var _countdown_label: Label
var _banner: Label
var _pause_panel: PanelContainer
var _resume_at_wall := -1.0
var _ended := false
var _started_wall := 0.0


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
	match_ref = Match.new()
	match_ref.setup(level)

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

	battle_view = BattleView.new()
	battle_view.name = "Battlefield"
	battle_view.anchor_right = 1.0
	battle_view.anchor_bottom = 1.0
	battle_view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_battle_area.add_child(battle_view)
	battle_view.setup(match_ref.sim)

	hud = Hud.new()
	hud.name = "Hud"
	hud.anchor_right = 1.0
	hud.anchor_bottom = 1.0
	hud.match_ref = match_ref
	_battle_area.add_child(hud)

	lane_view = LaneView.new()
	lane_view.name = "Lanes"
	lane_view.anchor_top = BATTLE_FRACTION
	lane_view.anchor_right = 1.0
	lane_view.anchor_bottom = 1.0
	lane_view.setup(level, match_ref.judge, clock)
	add_child(lane_view)

	# debug panel (F3): stem toggles prove muting and restoration without a restart (M0 evidence)
	_debug_panel = VBoxContainer.new()
	_debug_panel.position = Vector2(12, 110)
	_debug_panel.visible = Session.debug
	_battle_area.add_child(_debug_panel)
	_debug_label = Label.new()
	_debug_label.add_theme_font_size_override("font_size", 13)
	_debug_panel.add_child(_debug_label)
	var row := HBoxContainer.new()
	_debug_panel.add_child(row)
	for key in StemTransport.STEM_ORDER:
		var cb := CheckButton.new()
		cb.text = "mute " + key
		cb.focus_mode = Control.FOCUS_NONE
		cb.toggled.connect(func(on: bool) -> void: transport.set_stem_muted(key, on))
		row.add_child(cb)

	var pause_btn := Button.new()
	pause_btn.text = "II"
	pause_btn.focus_mode = Control.FOCUS_NONE
	pause_btn.custom_minimum_size = Vector2(64, 48)
	pause_btn.anchor_left = 0.5
	pause_btn.anchor_right = 0.5
	pause_btn.offset_left = -32
	pause_btn.offset_top = 52
	pause_btn.offset_right = 32
	pause_btn.offset_bottom = 96
	pause_btn.pressed.connect(_pause)
	_battle_area.add_child(pause_btn)

	_countdown_label = _centre_label(96, 0.35)
	_banner = _centre_label(64, 0.5)

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


func _centre_label(font_size: int, anchor_y: float) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", font_size)
	l.anchor_left = 0.5
	l.anchor_right = 0.5
	l.anchor_top = anchor_y
	l.anchor_bottom = anchor_y
	l.grow_horizontal = Control.GROW_DIRECTION_BOTH
	l.grow_vertical = Control.GROW_DIRECTION_BOTH
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(l)
	return l


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
	var wall := float(Time.get_ticks_msec()) / 1000.0
	for ev in match_ref.advance(t):
		_on_judge_event(ev, wall)
	var events := match_ref.drain_events()
	for ev in events:
		match ev["kind"]:
			"stem":
				transport.set_stem_muted(ev["stem"], ev["muted"])
			"air_busy":
				if ev["side"] == 0:
					lane_view.show_feedback("bass", "AIR WING BUSY", Color(0.8, 0.85, 1.0), wall)
			"production":
				if ev["side"] == 0 and ev["action"] == "bass":
					var res: String = ev["result"]["result"]
					if res == "pad_built":
						lane_view.show_feedback("bass", "PAD BUILT", Color(0.7, 0.9, 1.0), wall)
					elif res == "sortie" or res == "aircraft_replaced":
						lane_view.show_feedback("bass", "SORTIE", Color(0.7, 0.9, 1.0), wall)
	battle_view.push_events(events)
	for lane in LaneView.LANE_ORDER:
		lane_view.lane_down[lane] = lane_input.is_lane_down(lane)
	if _debug_panel.visible:
		var j := match_ref.judge
		_debug_label.text = "t=%6.2f s  bar %d  tick %d  P %d G %d M %d stray %d  latency %.1f ms  cal %+.0f ms  fps %d" % [
			t, level.bar_of_tick(level.seconds_to_tick(maxf(t, 0.0))), match_ref.sim_ticks, j.perfect, j.good, j.misses, j.strays,
			clock.output_latency * 1000.0, clock.calibration_ms, Engine.get_frames_per_second()]
	if not match_ref.outcome.is_empty():
		_finish()


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
	match_ref.press(lane, clock.judge_time(), touch_id)


func _on_lane_released(lane: String, touch_id: int) -> void:
	if _ended:
		return
	match_ref.release(lane, clock.judge_time(), touch_id)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if _ended:
			_quit()
		elif clock.state == SongClock.State.PAUSED:
			_resume()
		else:
			_pause()
		get_viewport().set_input_as_handled()
	elif event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F3:
		Session.debug = not Session.debug
		_debug_panel.visible = Session.debug


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_APPLICATION_PAUSED:
		if clock != null and not _ended and clock.state in [SongClock.State.PLAYING, SongClock.State.COUNTDOWN]:
			_pause()


func _pause() -> void:
	if _ended or clock.state == SongClock.State.PAUSED or _resume_at_wall >= 0.0:
		return
	clock.pause()
	match_ref.pause_interrupt()
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
	if not _ended and match_ref.outcome.is_empty():
		match_ref.sim.end_by_song()
		match_ref.advance(level.duration_seconds())
		_finish()


## Victory or defeat: stop input and combat now, fade the stems, show the result.
func _finish() -> void:
	if _ended:
		return
	_ended = true
	lane_input.enabled = false
	clock.end()
	transport.fade_out(END_FADE_S)
	var r := match_ref.result()
	r["duration_s"] = float(Time.get_ticks_msec()) / 1000.0 - _started_wall
	Session.last_result = r
	_banner.text = {"victory": "VICTORY", "defeat": "DEFEAT"}.get(r["outcome"], "SONG OVER")
	await get_tree().create_timer(1.4).timeout
	transport.stop()
	get_tree().change_scene_to_file("res://src/scenes/result.tscn")
