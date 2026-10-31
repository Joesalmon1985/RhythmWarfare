extends Control
## The play screen: song transport and clock, the match (recognition, sequences, rewards, waves, battle), the battlefield
## view with its HUD on top and the four pads below. Pause freezes music, cues, construction, waves and combat together.
## Missions (schema 3) and the legacy duel (schema 1) both play on the pads.

const COUNTDOWN_S := 2.0
const RESUME_COUNTDOWN_S := 3.0
const END_FADE_S := 0.6

var level: Level
var transport: StemTransport
var clock: SongClock
var match_ref: Match
var lane_input: LaneInput
var pad_view: PadView
var battle_view: BattleView
var hud: Hud
var battle_on := true

var _battle_area: Control
var _debug_panel: VBoxContainer
var _debug_label: Label
var _info_label: Label
var _intro_label: Label
var _countdown_label: Label
var _banner: Label
var _pause_panel: PanelContainer
var _settings_panel: Control
var _resume_at_wall := -1.0
var _ended := false
var _started_wall := 0.0
var _start_s := 0.0  # practice of one phase starts the song here


func _ready() -> void:
	var pack := Session.pack_dir
	if pack.is_empty():
		_fatal("No mission selected")
		return
	var opts := {"chart_id": Session.chart_id, "selection": Session.selection, "practice": Session.practice}
	var loaded := LevelLoader.load_pack(pack, opts)
	if loaded["level"] == null:
		_fatal("Song pack rejected:\n" + "\n".join(PackedStringArray(loaded["errors"])))
		return
	level = loaded["level"]
	for w in loaded["warnings"]:
		print("warning: ", w)
	if level.is_mission() and Session.practice and Session.practice_phase >= 0:
		_trim_to_phase(Session.practice_phase)

	transport = StemTransport.new()
	add_child(transport)
	var err := transport.load_level(level)
	if not err.is_empty():
		_fatal(err)
		return
	transport.start_at = _start_s
	clock = SongClock.new(transport)
	clock.calibration_ms = Session.calibration_ms
	battle_on = Session.battle_on or not level.is_defense()  # the duel always has its battlefield
	match_ref = Match.new()
	match_ref.setup(level, null, battle_on)

	_build_layout()
	lane_input = LaneInput.new()
	add_child(lane_input)
	lane_input.rect_provider = pad_view.button_rects
	lane_input.button_pressed.connect(_on_button_pressed)
	lane_input.button_released.connect(_on_button_released)
	transport.song_finished.connect(_on_song_finished)

	_started_wall = float(Time.get_ticks_msec()) / 1000.0
	_setup_autoplay()
	clock.begin_countdown(COUNTDOWN_S)


## Practice of one phase: only its cues and sequences, the song from one bar before it to its end.
func _trim_to_phase(index: int) -> void:
	var ph: Dictionary = level.sections[clampi(index, 0, level.sections.size() - 1)]
	var a := int(ph["start_tick"])
	var b := int(ph["end_tick"])
	var notes: Array = []
	for n in level.notes:
		if int(n["tick"]) >= a and int(n["tick"]) < b:
			notes.append(n)
	level.notes = notes
	var seqs: Array = []
	for s in level.sequences:
		if int(s["start_tick"]) >= a and int(s["end_tick"]) <= b:
			seqs.append(s)
	level.sequences = seqs
	level.duration_ticks = b
	_start_s = maxf(level.tick_to_seconds(a - level.ticks_per_bar()), 0.0)


# --- scripted play for device performance runs and screenshots (RW_AUTOPLAY=perfect|accuracy:<f>|none) ---
var _auto_plan: Array = []
var _auto_next := 0
var _auto_holding: Dictionary = {}


func _setup_autoplay() -> void:
	if not OS.has_environment("RW_AUTOPLAY"):
		return
	var policy := OS.get_environment("RW_AUTOPLAY")
	var prob := 1.0
	if policy.begins_with("accuracy:"):
		prob = float(policy.substr(9))
	elif policy == "none":
		prob = 0.0
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	for n in level.notes:
		_auto_plan.append(rng.randf() < prob)


func _autoplay_step(t: float) -> void:
	if _auto_plan.is_empty():
		return
	for pad in _auto_holding.keys():
		if t >= _auto_holding[pad]:
			match_ref.release(pad, _auto_holding[pad], 1)
			_auto_holding.erase(pad)
	while _auto_next < level.notes.size() and level.notes[_auto_next]["time"] <= t:
		var n: Dictionary = level.notes[_auto_next]
		var pad := PadView._pad_of(n)
		if _auto_plan[_auto_next]:
			match_ref.press(pad, n["time"], 1)
			if n["type"] == "hold":
				_auto_holding[pad] = float(n["end_time"])
		_auto_next += 1


func _build_layout() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bg := ColorRect.new()
	bg.color = UiStyle.BG
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	var pad_share: float = Session.PAD_SIZES[clampi(Session.pad_size, 0, 2)]
	if not battle_on:
		pad_share = 0.5
	var split := 1.0 - pad_share
	_battle_area = Control.new()
	_battle_area.name = "BattleArea"
	_battle_area.anchor_right = 1.0
	_battle_area.anchor_bottom = split
	_battle_area.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_battle_area)

	if battle_on:
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
		hud.view = battle_view
		_battle_area.add_child(hud)
	else:
		_info_label = Label.new()
		_info_label.set_anchors_preset(Control.PRESET_FULL_RECT)
		_info_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		_info_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		_info_label.add_theme_font_size_override("font_size", 26)
		_info_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_battle_area.add_child(_info_label)

	pad_view = PadView.new()
	pad_view.name = "Pads"
	pad_view.anchor_top = split
	pad_view.anchor_right = 1.0
	pad_view.anchor_bottom = 1.0
	pad_view.setup(level, clock)
	pad_view.lead_in_s = Session.cue_lead_in_s
	pad_view.high_contrast = Session.high_contrast
	pad_view.reduced_effects = Session.reduced_effects
	pad_view.show_keys = Session.show_keys
	pad_view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if level.is_mission():
		pad_view.holding_fn = match_ref.pad_judge.hold_progress
		pad_view.progress_fn = match_ref.tracker.progress_at
	else:
		pad_view.holding_fn = func(pad: int, _now: float) -> float: return match_ref.judge.active_hold_progress(pad)
	add_child(pad_view)

	_intro_label = Label.new()
	_intro_label.anchor_left = 0.2
	_intro_label.anchor_right = 0.8
	_intro_label.anchor_top = split - 0.09
	_intro_label.anchor_bottom = split - 0.01
	_intro_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_intro_label.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	_intro_label.add_theme_font_size_override("font_size", 22)
	_intro_label.add_theme_color_override("font_outline_color", Color.BLACK)
	_intro_label.add_theme_constant_override("outline_size", 6)
	_intro_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_intro_label)

	# debug panel (F3): stem toggles prove muting and restoration without a restart
	_debug_panel = VBoxContainer.new()
	_debug_panel.position = Vector2(12, 300)
	_debug_panel.visible = Session.debug
	_battle_area.add_child(_debug_panel)
	_debug_label = Label.new()
	_debug_label.add_theme_font_size_override("font_size", 13)
	_debug_panel.add_child(_debug_label)

	var pause_btn := Button.new()
	pause_btn.text = "II"
	pause_btn.focus_mode = Control.FOCUS_NONE
	pause_btn.add_theme_font_size_override("font_size", 24)
	pause_btn.anchor_left = 1.0  # top right: the top defense point sits under the centre of the battle area
	pause_btn.anchor_right = 1.0
	pause_btn.offset_left = -92
	pause_btn.offset_top = 8
	pause_btn.offset_right = -20
	pause_btn.offset_bottom = 64
	pause_btn.pressed.connect(_pause)
	add_child(pause_btn)

	_countdown_label = _centre_label(110, 0.32)
	_banner = _centre_label(64, 0.4)

	_pause_panel = PanelContainer.new()
	_pause_panel.add_theme_stylebox_override("panel", UiStyle.panel_box())
	_pause_panel.set_anchors_preset(Control.PRESET_CENTER)
	_pause_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_pause_panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	_pause_panel.visible = false
	add_child(_pause_panel)
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 12)
	_pause_panel.add_child(pv)
	pv.add_child(UiStyle.title("Paused", 36))
	var items := [["Resume", _resume], ["Restart", _retry], ["Settings", _open_settings]]
	if level.is_mission():
		items.append(["Mission setup", _to_setup])
	items.append(["Quit to menu", _quit])
	for item in items:
		pv.add_child(UiStyle.button(item[0], item[1], 340))


func _centre_label(font_size: int, anchor_y: float) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_outline_color", Color.BLACK)
	l.add_theme_constant_override("outline_size", 10)
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
	_perf_sample(_delta)
	_autoplay_step(t)
	for ev in match_ref.advance(t):
		_on_judge_event(ev, wall)
	var events := match_ref.drain_events()
	for ev in events:
		_on_match_event(ev, wall)
	if battle_view != null:
		battle_view.push_events(events)
	for b in range(1, PadView.BUTTONS + 1):
		pad_view.button_down[b] = lane_input.is_button_down(b)
	_update_banner(t)
	if _info_label != null:
		_info_label.text = "%s\n%s" % [level.title, "PRACTICE (no battle, nothing saved)" if Session.practice else "RHYTHM PLAYTEST (battlefield hidden)"]
	if _debug_panel.visible:
		_debug_label.text = "t=%6.2f s  bar %d  tick %d  latency %.1f ms  cal %+.0f ms  fps %d" % [
			t, level.bar_of_tick(level.seconds_to_tick(maxf(t, 0.0))), match_ref.sim_ticks,
			clock.output_latency * 1000.0, clock.calibration_ms, Engine.get_frames_per_second()]
	if not match_ref.outcome.is_empty():
		_finish()


## The in-play banner: the incoming family one bar before a mode change and the first bar of a new mode. The intro line
## of the mission shows during its first bars. Neither reveals anything beyond the next change.
func _update_banner(t: float) -> void:
	if not level.is_mission():
		return
	var tick := level.seconds_to_tick(maxf(t, 0.0))
	var bar := level.ticks_per_bar()
	var text := ""
	for i in level.sections.size():
		var s: Dictionary = level.sections[i]
		var start := int(s["start_tick"])
		var prev_mode := str(level.sections[i - 1]["mode"]) if i > 0 else ""
		if prev_mode == str(s["mode"]):
			continue
		if tick >= start - bar and tick < start:
			text = ("%s NEXT" % str(s["mode"]).to_upper()) if i > 0 else ""
		elif tick >= start and tick < start + bar:
			text = str(s["mode"]).to_upper()
	pad_view.banner_text = text
	var intro_from := level.tick_to_seconds((level.intro_bar - 1) * bar)
	var intro_on := not level.intro.is_empty() and t >= intro_from - 0.5 and t < intro_from + level.tick_to_seconds(4 * bar)
	_intro_label.text = level.intro if intro_on and not Session.practice else ""


func _on_judge_event(ev: Dictionary, wall: float) -> void:
	var pad: int = int(ev.get("pad", ev.get("button", 0)))
	var offset := ""
	if Session.debug and ev.has("delta_ms"):
		offset = " %+d" % int(round(float(ev["delta_ms"])))
	match ev["kind"]:
		"perfect":
			pad_view.show_feedback(pad, "PERFECT" + offset, Color(1.0, 0.95, 0.6), wall)
			_buzz()
		"great", "good":
			pad_view.show_feedback(pad, "GREAT" + offset, Color(0.7, 0.95, 0.7), wall)
			_buzz()
		"ok":
			pad_view.show_feedback(pad, "OK" + offset, Color(0.75, 0.85, 0.9), wall)
			_buzz()
		"hold_start":
			pad_view.show_feedback(pad, "HOLD", Color(0.75, 0.85, 1.0), wall)
			_buzz()
		"hold_complete":
			pad_view.flash_complete(pad, wall)
			pad_view.show_feedback(pad, "HELD", Color(0.8, 1.0, 0.8), wall)
		"hold_partial":
			pad_view.show_feedback(pad, "LET GO", Color(0.85, 0.8, 0.7), wall)
		"miss", "hold_fail":
			pad_view.show_feedback(pad, "MISS", Color(1.0, 0.5, 0.45), wall)
		"stray":
			pad_view.show_feedback(pad, "·", Color(0.7, 0.7, 0.7), wall)


func _buzz() -> void:
	if Session.vibration and OS.has_feature("mobile"):
		Input.vibrate_handheld(18)


func _on_match_event(ev: Dictionary, wall: float) -> void:
	match ev["kind"]:
		"stem":
			transport.set_stem_muted(ev["stem"], ev["muted"])
		"sequence":
			var r: Dictionary = ev["result"]
			if r["passed"]:
				var what := MissionRules.reward_name(str(r["reward"]))
				pad_view.show_status("%s earned · %s %.1f s" % [what, str(r["grade"]), float(r["delay_s"])], Color(0.7, 1.0, 0.7), wall)
			else:
				pad_view.show_status("Sequence missed: no reward", Color(1.0, 0.7, 0.6), wall)
		"reward_done":
			var res := str(ev.get("result", ""))
			var msg := ""
			match res:
				"built", "unit":
					msg = "%s ready" % str(ev["label"])
				"repaired":
					msg = "All sockets full: repaired %d defenses" % int(ev.get("count", 0)) if ev.get("capacity", false) else "Repair crew: %d defenses repaired" % int(ev.get("count", 0))
				"reinforced":
					msg = "Sockets full: a defense was reinforced"
				"full_strength":
					msg = "Every defense is at full strength"
				_:
					msg = "%s: %s" % [str(ev["label"]), res]
			pad_view.show_status(msg, Color(0.75, 0.95, 1.0), wall)


func _on_button_pressed(button: int, touch_id: int) -> void:
	if _ended or clock.state == SongClock.State.PAUSED:
		return
	match_ref.press(button, clock.judge_time(), touch_id)


func _on_button_released(button: int, touch_id: int) -> void:
	if _ended:
		return
	match_ref.release(button, clock.judge_time(), touch_id)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if _ended:
			_quit()
		elif _settings_panel != null:
			_close_settings()
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
		if _auto_plan.is_empty() and clock != null and not _ended and clock.state in [SongClock.State.PLAYING, SongClock.State.COUNTDOWN]:
			_pause()


func _pause() -> void:
	if _ended or clock.state == SongClock.State.PAUSED or _resume_at_wall >= 0.0:
		return
	clock.pause()
	match_ref.pause_interrupt(clock.judge_time())
	lane_input.clear()
	lane_input.enabled = false
	_pause_panel.visible = true
	_countdown_label.text = ""


func _resume() -> void:
	if clock.state != SongClock.State.PAUSED:
		return
	_pause_panel.visible = false
	_resume_at_wall = float(Time.get_ticks_msec()) / 1000.0 + RESUME_COUNTDOWN_S


func _open_settings() -> void:
	_pause_panel.visible = false
	_settings_panel = SettingsPanel.new()
	_settings_panel.in_game = true
	_settings_panel.closed.connect(_close_settings)
	add_child(_settings_panel)


func _close_settings() -> void:
	if _settings_panel != null:
		_settings_panel.queue_free()
		_settings_panel = null
	pad_view.lead_in_s = Session.cue_lead_in_s
	pad_view.high_contrast = Session.high_contrast
	pad_view.reduced_effects = Session.reduced_effects
	pad_view.show_keys = Session.show_keys
	clock.calibration_ms = Session.calibration_ms
	_pause_panel.visible = true


func _retry() -> void:
	transport.stop()
	get_tree().reload_current_scene()


func _to_setup() -> void:
	transport.stop()
	get_tree().change_scene_to_file("res://src/scenes/mission_setup.tscn")


func _quit() -> void:
	if transport != null:
		transport.stop()
	get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn")


func _on_song_finished() -> void:
	if not _ended and match_ref.outcome.is_empty():
		if not level.is_defense():
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
	r["practice"] = Session.practice
	if Session.campaign_level_id != "" and not Session.practice and _auto_plan.is_empty():  # scripted runs never touch the save
		r["campaign"] = Session.campaign.record_result(r)
	r["duration_s"] = float(Time.get_ticks_msec()) / 1000.0 - _started_wall
	r["perf"] = _perf_report()
	Session.last_result = r
	if not _perf_frames.is_empty():
		print("PERF ", JSON.stringify(r["perf"]))
	_banner.text = {"victory": "VICTORY", "defeat": "DEFEAT", "complete": "PRACTICE COMPLETE" if Session.practice else "SONG COMPLETE"}.get(r["outcome"], "SONG OVER")
	await get_tree().create_timer(1.4).timeout
	transport.stop()
	get_tree().change_scene_to_file("res://src/scenes/result.tscn")


# --- frame-time evidence (always sampled while playing; printed when the run ends) ---
var _perf_frames: PackedFloat32Array = PackedFloat32Array()
var _perf_peak_units := 0


func _perf_sample(delta: float) -> void:
	if clock.state != SongClock.State.PLAYING:
		return
	_perf_frames.append(delta * 1000.0)
	if not battle_on:
		return
	var live := match_ref.sim.count_alive(0, BattleSim.Kind.UNIT) + match_ref.sim.count_alive(1, BattleSim.Kind.UNIT)
	_perf_peak_units = maxi(_perf_peak_units, live)


func _perf_report() -> Dictionary:
	if _perf_frames.is_empty():
		return {}
	var sorted := _perf_frames.duplicate()
	sorted.sort()
	var sum := 0.0
	for v in sorted:
		sum += v
	var p95: float = sorted[mini(int(floor(sorted.size() * 0.95)), sorted.size() - 1)]
	var over33 := 0
	for v in sorted:
		if v > 33.0:
			over33 += 1
	return {
		"frames": sorted.size(), "avg_ms": snappedf(sum / sorted.size(), 0.01), "p95_ms": snappedf(p95, 0.01),
		"max_ms": snappedf(sorted[sorted.size() - 1], 0.01), "frames_over_33ms": over33,
		"peak_live_units": _perf_peak_units, "static_memory_mb": snappedf(float(OS.get_static_memory_usage()) / 1048576.0, 0.1),
		"streams": level.stems.size(), "device": OS.get_model_name(), "os": OS.get_name(), "renderer": RenderingServer.get_video_adapter_name(),
	}
