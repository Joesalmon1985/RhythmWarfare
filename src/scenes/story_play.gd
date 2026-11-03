extends Control
## Story Campaign play screen: the existing song transport, clock, judge and pads (PadView / NoteLane / LaneInput) with a fixed
## nightclub (StoryStage) instead of the battlefield. StoryRun holds the judgement (Match in rhythm-only mode), the crowd energy and
## the director; this scene only hosts input, audio, pause and presentation. No battle simulation, no rewards, no campaign saves.
## Scripted runs: RW_AUTOPLAY=perfect|none|beginner|sloppy|accuracy:<f>; RW_STORY_VIRTUAL=1 steps a virtual song clock (no audio)
## up to RW_STORY_UNTIL_BAR so screenshots and fast-forward checks need no real-time wait.

const COUNTDOWN_S := 2.0
const RESUME_COUNTDOWN_S := 3.0
const TAIL_S := 3.6  # the closing tableau holds this long (music fading) before the result screen

var run: StoryRun
var assets: StoryAssets
var stage: StoryStage
var transport: StemTransport
var clock: SongClock
var pad_view: PadView
var note_lane: NoteLane
var lane_input: LaneInput
var deck: StoryDeck

var _countdown_label: Label
var _title_card: Label
var _act_label: Label
var _toast: Label
var _debug_label: Label
var _pause_btn: Button
var _dim: ColorRect
var _pause_panel: PanelContainer
var _settings_panel: Control
var _resume_at_wall := -1.0
var _ended := false
var _virtual := false
var _vt := -COUNTDOWN_S
var _until_bar := -1.0
var _tail_until := -1.0
var _toast_until := 0.0
var _act_until := 0.0
var _act_index := -1
var _auto_plan: Array = []
var _auto_next := 0
var _auto_down: Dictionary = {}
var _perf: PackedFloat32Array = PackedFloat32Array()


func _ready() -> void:
	theme = UiStyle.theme()
	var opts := {"loadout": Session.loadout(), "library": Session.library(), "unlocked": Session.campaign.unlocked_items()}
	run = StoryRun.create(opts)
	if not run.errors.is_empty():
		_fatal("Story level rejected:\n" + "\n".join(PackedStringArray(run.errors)))
		return
	for w in run.warnings:
		print("warning: ", w)
	assets = StoryAssets.load_default()
	if not assets.ok():
		_fatal("Story art missing:\n" + "\n".join(PackedStringArray(assets.errors)))
		return
	_virtual = OS.get_environment("RW_STORY_VIRTUAL") == "1"
	if OS.has_environment("RW_STORY_UNTIL_BAR"):
		_until_bar = float(OS.get_environment("RW_STORY_UNTIL_BAR"))
	if not _virtual:
		transport = StemTransport.new()
		add_child(transport)
		var err := transport.load_level(run.level)
		if not err.is_empty():
			_fatal(err)
			return
		clock = SongClock.new(transport)
		clock.calibration_ms = Session.calibration_ms
		transport.song_finished.connect(func() -> void: pass)
	else:
		clock = SongClock.new(null)
	_build_layout()
	lane_input = LaneInput.new()
	add_child(lane_input)
	lane_input.rect_provider = pad_view.button_rects
	lane_input.button_pressed.connect(_on_button_pressed)
	lane_input.button_released.connect(_on_button_released)
	_setup_autoplay()
	if _virtual:
		_step_virtual(_vt)
	else:
		clock.begin_countdown(COUNTDOWN_S)


func _fatal(message: String) -> void:
	push_error(message)
	var l := Label.new()
	l.text = message + "\n\n(Esc to return)"
	l.set_anchors_preset(Control.PRESET_FULL_RECT)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(l)
	_ended = true


func _build_layout() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bg := ColorRect.new()
	bg.color = Color(0.02, 0.02, 0.06)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	var pad_share: float = Session.PAD_SIZES[clampi(Session.pad_size, 0, 2)]
	var split := 1.0 - pad_share
	stage = StoryStage.new()
	stage.name = "Stage"
	stage.anchor_right = 1.0
	stage.anchor_bottom = split
	stage.reduced = Session.reduced_effects
	stage.high_contrast = Session.high_contrast
	add_child(stage)
	stage.setup(assets, run.data, run)
	stage.reduced = Session.reduced_effects

	pad_view = PadView.new()
	pad_view.name = "Pads"
	pad_view.anchor_top = split
	pad_view.anchor_right = 1.0
	pad_view.anchor_bottom = 1.0
	pad_view.setup(run.level, clock)
	pad_view.high_contrast = Session.high_contrast
	pad_view.reduced_effects = Session.reduced_effects
	pad_view.show_keys = Session.show_keys
	pad_view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pad_view.clip_contents = true
	pad_view.show_reward = false
	pad_view.holding_fn = run.match_ref.pad_judge.hold_progress
	pad_view.progress_fn = run.match_ref.tracker.progress_at
	pad_view.muted_fn = run.match_ref.family_muted
	deck = StoryDeck.new()
	deck.setup(assets, run, stage)
	deck.reduced = Session.reduced_effects
	pad_view.deck_under = deck.draw_under
	pad_view.deck_over = deck.draw_over
	add_child(pad_view)

	var shade := StoryLaneShade.new()
	shade.name = "LaneShade"
	shade.pad_view = pad_view
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)

	note_lane = NoteLane.new()
	note_lane.name = "Notes"
	note_lane.anchor_right = 1.0
	note_lane.anchor_bottom = 1.0
	note_lane.mouse_filter = Control.MOUSE_FILTER_IGNORE
	note_lane.setup(run.level, clock, pad_view)
	note_lane.travel_s = Session.cue_lead_in_s
	note_lane.high_contrast = Session.high_contrast
	note_lane.reduced_effects = Session.reduced_effects
	note_lane.state_fn = run.match_ref.pad_judge.cue_state
	add_child(note_lane)

	_title_card = _centre_label("NIGHT ONE", 84, 0.2)
	_act_label = _centre_label("", 30, 0.08)
	_toast = _centre_label("", 28, 0.15)
	_countdown_label = _centre_label("", 110, 0.34)
	_debug_label = Label.new()
	_debug_label.position = Vector2(12, 8)
	_debug_label.add_theme_font_size_override("font_size", 13)
	_debug_label.visible = Session.debug
	add_child(_debug_label)

	_pause_btn = Button.new()
	_pause_btn.text = "II"
	_pause_btn.focus_mode = Control.FOCUS_NONE
	_pause_btn.add_theme_font_size_override("font_size", 24)
	_pause_btn.anchor_left = 1.0
	_pause_btn.anchor_right = 1.0
	_pause_btn.offset_left = -92
	_pause_btn.offset_top = 8
	_pause_btn.offset_right = -20
	_pause_btn.offset_bottom = 64
	_pause_btn.pressed.connect(_pause)
	add_child(_pause_btn)

	_dim = ColorRect.new()
	_dim.color = Color(0, 0, 0, 0.6)
	_dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_dim.visible = false
	add_child(_dim)
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
	for item in [["Resume", _resume], ["Restart", _retry], ["Settings", _open_settings], ["Quit to Story Campaign", _quit]]:
		pv.add_child(UiStyle.button(item[0], item[1], 360))


func _centre_label(text: String, font_size: int, anchor_y: float) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_outline_color", Color(0.02, 0.0, 0.12))
	l.add_theme_constant_override("outline_size", 12)
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


# --- scripted input ---------------------------------------------------------------------------------------------------------

func _setup_autoplay() -> void:
	if not OS.has_environment("RW_AUTOPLAY"):
		return
	var harness: Script = load("res://tools/autoplay.gd")
	var rng := RandomNumberGenerator.new()
	rng.seed = int(OS.get_environment("RW_SEED")) if OS.has_environment("RW_SEED") else 1
	_auto_plan = harness.plan_inputs(run.level, OS.get_environment("RW_AUTOPLAY"), rng)


func _autoplay_step(t: float) -> void:
	while _auto_next < _auto_plan.size() and float(_auto_plan[_auto_next]["t"]) <= t:
		var e: Dictionary = _auto_plan[_auto_next]
		var pad := int(e["pad"])
		if e["down"]:
			if _auto_down.has(pad):
				run.match_ref.release(pad, float(e["t"]), pad)
			_auto_down[pad] = e["id"]
			run.match_ref.press(pad, float(e["t"]), pad)
			pad_view.button_down[pad] = true
		elif _auto_down.get(pad, null) == e["id"]:
			_auto_down.erase(pad)
			run.match_ref.release(pad, float(e["t"]), pad)
			pad_view.button_down[pad] = false
		_auto_next += 1


# --- frame loop -------------------------------------------------------------------------------------------------------------

func _process(delta: float) -> void:
	if clock == null or run == null:
		return
	if _virtual:
		_process_virtual(delta)
		return
	if _ended and _tail_until < 0.0:
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
	var audio_t := clock.audio_time()
	if clock.state == SongClock.State.COUNTDOWN:
		_countdown_label.text = str(ceili(clock.countdown_remaining()))
	elif not _countdown_label.text.is_empty():
		_countdown_label.text = ""
	if clock.state == SongClock.State.PLAYING:
		_perf.append(delta * 1000.0)
	if not _ended:
		_autoplay_step(t)
		_advance(t, audio_t)
	else:
		stage.update(audio_t, run.crowd.energy)
		if Time.get_ticks_msec() / 1000.0 >= _tail_until:
			_go_to_result()
	_ui(t)


func _process_virtual(_delta: float) -> void:
	if _ended and _tail_until < 0.0 and _until_bar <= 0.0:
		return
	var until_t := run.director.bar_time(_until_bar) if _until_bar > 0.0 else INF
	if _vt >= until_t:
		return
	var rate := float(OS.get_environment("RW_STORY_RATE")) if OS.has_environment("RW_STORY_RATE") else 1.0 / 30.0
	var chunk := rate if _vt < until_t - 1.0 else 1.0 / 30.0  # the last second runs at a normal pace so poses settle
	var target := minf(_vt + chunk, until_t)
	while _vt < target - 1e-9:
		_vt = minf(_vt + 1.0 / 60.0, target)
		_autoplay_step(_vt)
		_advance(_vt, _vt, _vt >= target - 1e-9)
	_ui(_vt)


func _step_virtual(t: float) -> void:
	_advance(t, t)
	_ui(t)


func _advance(t: float, audio_t: float, render := true) -> void:
	var wall := float(Time.get_ticks_msec()) / 1000.0
	var r := run.step(t)
	for ev in r["judge"]:
		_on_judge_event(ev, wall)
	for ev in r["events"]:
		match ev["kind"]:
			"stem":
				if transport != null:
					transport.set_stem_muted(ev["stem"], ev["muted"])
			"program":
				if transport != null:
					transport.apply_program(ev["on"])
			"sequence":
				_on_sequence(ev["result"], wall)
	for a in r["actions"]:
		_on_action(a)
	if render:
		stage.update(audio_t, run.crowd.energy)
	for b in range(1, PadView.BUTTONS + 1):
		pad_view.button_down[b] = lane_input.is_button_down(b) or (_auto_plan.size() > 0 and _auto_down.has(b))
	note_lane.queue_redraw()
	if not _ended and run.finished:
		_finish()


func _ui(t: float) -> void:
	var bar := run.level.bar_of_tick(run.level.seconds_to_tick(maxf(t, 0.0)))
	var wall := float(Time.get_ticks_msec()) / 1000.0
	_title_card.modulate.a = clampf(1.0 - (t - 0.8) / 1.2, 0.0, 1.0) if t > 0.8 else 1.0
	_title_card.visible = _title_card.modulate.a > 0.01
	var act_i := run.data.act_of_bar(float(bar))
	if t >= 0.0 and act_i != _act_index:
		_act_index = act_i
		_act_label.text = "ACT %s   %s" % [run.data.acts[act_i]["id"], str(run.data.acts[act_i]["title"]).to_upper()]
		_act_until = wall + 3.5
	_act_label.modulate.a = clampf(_act_until - wall, 0.0, 1.0) if t > 0.8 else 0.0
	_toast.modulate.a = clampf(_toast_until - wall, 0.0, 1.0)
	pad_view.banner_text = _banner(t)
	if _debug_label.visible:
		_debug_label.text = "t=%6.2f bar %d  energy %.0f (%s)  seq %d/%d  crowd %d  fps %d" % [t, bar, run.crowd.energy, run.crowd.band(),
			run.crowd.history.size(), run.total_sequences(), stage.crowd.present_count(), Engine.get_frames_per_second()]


func _banner(t: float) -> String:
	var lvl := run.level
	var tick := lvl.seconds_to_tick(maxf(t, 0.0))
	var bar := lvl.ticks_per_bar()
	for i in lvl.sections.size():
		var s: Dictionary = lvl.sections[i]
		var start := int(s["start_tick"])
		var prev := str(lvl.sections[i - 1]["mode"]) if i > 0 else ""
		if prev == str(s["mode"]):
			continue
		if tick >= start - bar and tick < start and i > 0:
			return "%s NEXT" % str(s["mode"]).to_upper()
		if tick >= start and tick < start + bar:
			return str(s["mode"]).to_upper()
	return ""


func _on_judge_event(ev: Dictionary, wall: float) -> void:
	var pad: int = int(ev.get("pad", ev.get("button", 0)))
	match ev["kind"]:
		"perfect":
			pad_view.show_feedback(pad, "PERFECT", Color(1.0, 0.95, 0.6), wall)
			_buzz()
		"great", "good":
			pad_view.show_feedback(pad, "GREAT", Color(0.7, 0.95, 0.7), wall)
			_buzz()
		"ok":
			pad_view.show_feedback(pad, "OK", Color(0.75, 0.85, 0.9), wall)
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


func _on_sequence(r: Dictionary, wall: float) -> void:
	var band := run.crowd.band()
	if r["passed"]:
		var word: String = {"sharp": "Sharp! The floor is with you", "steady": "Steady: the crowd moves", "loose": "Loose, but they're still dancing"}.get(str(r["grade"]), "Nice")
		pad_view.show_status(word, Color(0.7, 1.0, 0.8), wall)
	else:
		pad_view.show_status("Lost them: the crowd cools" if band != "quiet" else "The floor is losing interest", Color(1.0, 0.7, 0.6), wall)
	stage.on_sequence(r, float(r.get("resolve_time", 0.0)))


func _on_action(a: Dictionary) -> void:
	stage.apply(a)
	if a["source"] == "decision" and a["args"].has("outcome"):
		for d in run.crowd.decisions_log:
			if d["id"] == a["args"]["decision"] and str(d["text"]) != "":
				_toast.text = str(d["text"])
				_toast_until = float(Time.get_ticks_msec()) / 1000.0 + 4.5
				break
	elif a["action"] == "ending":
		var e: Dictionary = run.data.endings[a["args"]["ending"]]
		_toast.text = str(e["title"]).to_upper()
		_toast_until = float(Time.get_ticks_msec()) / 1000.0 + TAIL_S


# --- input ------------------------------------------------------------------------------------------------------------------

func _on_button_pressed(button: int, touch_id: int) -> void:
	if _ended or clock.state == SongClock.State.PAUSED:
		return
	run.match_ref.press(button, clock.judge_time(), touch_id)


func _on_button_released(button: int, touch_id: int) -> void:
	if _ended:
		return
	run.match_ref.release(button, clock.judge_time(), touch_id)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if clock == null or run == null or _ended and _tail_until < 0.0:
			_quit()
		elif _settings_panel != null:
			_close_settings()
		elif clock.state == SongClock.State.PAUSED:
			_resume()
		else:
			_pause()
		get_viewport().set_input_as_handled()
	elif event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F3 and _debug_label != null:
		Session.debug = not Session.debug
		_debug_label.visible = Session.debug


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_APPLICATION_PAUSED:
		if not _virtual and _auto_plan.is_empty() and clock != null and not _ended and clock.state in [SongClock.State.PLAYING, SongClock.State.COUNTDOWN]:
			_pause()


func _pause() -> void:
	if _virtual or _ended or clock.state == SongClock.State.PAUSED or _resume_at_wall >= 0.0:
		return
	clock.pause()
	run.match_ref.pause_interrupt(clock.judge_time())
	lane_input.clear()
	lane_input.enabled = false
	_pause_panel.visible = true
	_dim.visible = true
	_countdown_label.text = ""


func _resume() -> void:
	if clock.state != SongClock.State.PAUSED:
		return
	_pause_panel.visible = false
	_dim.visible = false
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
	pad_view.high_contrast = Session.high_contrast
	pad_view.reduced_effects = Session.reduced_effects
	pad_view.show_keys = Session.show_keys
	note_lane.travel_s = Session.cue_lead_in_s
	note_lane.high_contrast = Session.high_contrast
	note_lane.reduced_effects = Session.reduced_effects
	stage.reduced = Session.reduced_effects
	stage.high_contrast = Session.high_contrast
	deck.reduced = Session.reduced_effects
	clock.calibration_ms = Session.calibration_ms
	_pause_panel.visible = true


func _retry() -> void:
	if transport != null:
		transport.stop()
	get_tree().reload_current_scene()


func _quit() -> void:
	if transport != null:
		transport.stop()
	get_tree().change_scene_to_file("res://src/scenes/story_campaign.tscn")


# --- the end ----------------------------------------------------------------------------------------------------------------

func _finish() -> void:
	if _ended:
		return
	_ended = true
	lane_input.enabled = false
	if transport != null:
		transport.fade_out(TAIL_S)
	_tail_until = float(Time.get_ticks_msec()) / 1000.0 + TAIL_S
	var s := run.summary()
	s["level_id"] = run.data.id
	s["title"] = run.data.title
	s["scripted"] = not _auto_plan.is_empty()
	if not _perf.is_empty():
		var sorted := _perf.duplicate()
		sorted.sort()
		s["p95_ms"] = snappedf(sorted[mini(int(floor(sorted.size() * 0.95)), sorted.size() - 1)], 0.01)
		print("PERF frames=%d p95=%.2f max=%.2f" % [sorted.size(), s["p95_ms"], sorted[sorted.size() - 1]])
	if _auto_plan.is_empty():  # scripted runs never touch the save
		s["record"] = Session.story_progress.record(run.data.id, s)
	Session.story_result = s
	print("STORY ", JSON.stringify({"ending": s["ending"], "energy": s["energy"], "passed": s["sequences_passed"], "total": s["sequences_total"]}))
	if _virtual:
		_tail_until = -1.0


func _go_to_result() -> void:
	if transport != null:
		transport.stop()
	set_process(false)
	get_tree().change_scene_to_file("res://src/scenes/story_result.tscn")
