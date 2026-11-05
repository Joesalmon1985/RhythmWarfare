extends Control
## Track mode, a developer test scene: a whole recorded track plays start to finish. At any moment one instrument (the
## focus) is the player's and all four pads play its part; the focus moves from instrument to instrument. A missed cue
## silences the instrument being played until the player hits it again, the others keep playing. No battle, no
## failing, no menus.
## Environment: RW_TRACK (absolute pack folder), RW_TRACK_CHART, RW_AUTOPLAY (perfect | accuracy:<f> | none),
## RW_TRACK_START (seconds), RW_TRACK_QUIT=1 (quit when the track ends, or at once with exit code 2 if the pack is
## refused). At the end it prints one line: TRACK_SUMMARY <json>.

signal track_finished(summary: Dictionary)

const COUNTDOWN_S := 2.0
const RESUME_COUNTDOWN_S := 3.0
const END_FADE_S := 0.6

var pack: TrackPack
var game: TrackGame
var transport: TrackTransport
var clock: SongClock
var lane_input: LaneInput
var pad_view: TrackPadView
var note_lane: NoteLane
var autoplay: TrackAutoplay
var summary: Dictionary = {}
var refused: Array = []  # the pack's problems when it was refused
var ended := false

var _info: Label
var _focus_label: Label
var _next_label: Label
var _status: Label
var _countdown: Label
var _pause_label: Label
var _result: Label
var _resume_at_wall := -1.0
var _start_s := 0.0
var _quit_on_end := false


func _ready() -> void:
	_quit_on_end = OS.get_environment("RW_TRACK_QUIT") == "1"
	var folder := OS.get_environment("RW_TRACK")
	if folder.is_empty():
		_refuse(["RW_TRACK is not set: give the absolute path of a track pack folder."])
		return
	var loaded := TrackPack.load_pack(folder)
	if loaded["pack"] == null:
		_refuse(loaded["errors"])
		return
	pack = loaded["pack"]
	var chart := OS.get_environment("RW_TRACK_CHART")
	if chart.is_empty():
		chart = pack.default_chart
	if not pack.charts.has(chart):
		_refuse(["The pack has no chart named '%s' (it has: %s)." % [chart, ", ".join(PackedStringArray(pack.charts.keys()))]])
		return
	if OS.has_environment("RW_TRACK_START"):
		_start_s = float(OS.get_environment("RW_TRACK_START"))
		if _start_s < 0.0 or _start_s >= pack.duration_s:
			_refuse(["RW_TRACK_START %.3f is outside the track (0 to %.3f s)." % [_start_s, pack.duration_s]])
			return
	var policy := OS.get_environment("RW_AUTOPLAY")
	if OS.has_environment("RW_AUTOPLAY") and not TrackAutoplay.is_valid_policy(policy):
		_refuse(["RW_AUTOPLAY '%s' is not perfect, none or accuracy:<0..1>." % policy])
		return

	game = TrackGame.new()
	game.setup(pack, chart, _start_s)
	transport = TrackTransport.new()
	add_child(transport)
	var err := transport.load_pack_streams(pack)
	_limit_music_bus()
	if not err.is_empty():
		_refuse([err])
		return
	transport.start_at = _start_s
	clock = SongClock.new(transport)
	clock.calibration_ms = Session.calibration_ms
	transport.song_finished.connect(_finish)
	_build_layout()
	lane_input = LaneInput.new()
	add_child(lane_input)
	lane_input.rect_provider = pad_view.button_rects
	lane_input.button_pressed.connect(_on_button_pressed)
	lane_input.button_released.connect(_on_button_released)
	if not policy.is_empty():
		autoplay = TrackAutoplay.new()
		autoplay.setup(game.cues, policy)
	clock.begin_countdown(COUNTDOWN_S)


## The pack was refused (or the scene was set up wrongly): say why, and under RW_TRACK_QUIT leave at once.
func _refuse(errors: Array) -> void:
	refused = errors
	ended = true
	var text := "Track pack refused:\n" + "\n".join(PackedStringArray(errors))
	print("TRACK_REFUSED ", JSON.stringify(errors))
	printerr(text)
	var l := Label.new()
	l.text = text
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.anchor_right = 1.0
	l.anchor_bottom = 1.0
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(l)
	if _quit_on_end:
		get_tree().quit(2)


func _build_layout() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bg := ColorRect.new()
	bg.color = Color(0.07, 0.08, 0.1)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	var split := 1.0 - float(Session.PAD_SIZES[clampi(Session.pad_size, 0, 2)]) * 1.2
	pad_view = TrackPadView.new()
	pad_view.name = "Pads"
	pad_view.anchor_top = split
	pad_view.anchor_right = 1.0
	pad_view.anchor_bottom = 1.0
	pad_view.clock = clock
	pad_view.high_contrast = Session.high_contrast
	pad_view.reduced_effects = Session.reduced_effects
	pad_view.show_keys = Session.show_keys
	pad_view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pad_view.clip_contents = true
	pad_view.state_fn = _pad_state
	pad_view.holding_fn = func(pad: int, now: float) -> float: return game.hold_progress(pad, now)
	add_child(pad_view)

	# NoteLane reads only level.notes: the cues, each tinted by its pad's voice colour through "family"
	var level := Level.new()
	var tint := {1: "kick", 2: "snare", 3: "bass", 4: "other"}
	for c in game.cues:
		var n: Dictionary = c.duplicate()
		n["family"] = tint[int(c["pad"])]
		level.notes.append(n)
	note_lane = NoteLane.new()
	note_lane.name = "Notes"
	note_lane.anchor_right = 1.0
	note_lane.anchor_bottom = 1.0
	note_lane.mouse_filter = Control.MOUSE_FILTER_IGNORE
	note_lane.setup(level, clock, pad_view)
	note_lane.travel_s = Session.cue_lead_in_s
	note_lane.high_contrast = Session.high_contrast
	note_lane.reduced_effects = Session.reduced_effects
	note_lane.state_fn = game.cue_state
	add_child(note_lane)

	_info = _label(22, 0.02, 0.0, 14)
	_status = _label(18, 0.02, 0.0, 70)
	_focus_label = _label(44, 0.02, 0.5, 100)
	_focus_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_next_label = _label(30, 0.02, 0.5, 160)
	_next_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_countdown = _label(110, 0.3, 0.5, 0)
	_countdown.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_pause_label = _label(48, 0.3, 0.5, 0)
	_pause_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_result = _label(20, 0.08, 0.0, 0)
	_result.anchor_left = 0.5
	_result.anchor_right = 0.5
	_result.grow_horizontal = Control.GROW_DIRECTION_BOTH


func _label(font_size: int, anchor_y: float, anchor_x: float, offset_y: int) -> Label:
	var l := Label.new()
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_outline_color", Color.BLACK)
	l.add_theme_constant_override("outline_size", 6)
	l.anchor_left = anchor_x
	l.anchor_right = anchor_x
	l.anchor_top = anchor_y
	l.anchor_bottom = anchor_y
	l.offset_left = 16 if anchor_x == 0.0 else 0
	l.offset_top = offset_y
	l.grow_horizontal = Control.GROW_DIRECTION_BOTH if anchor_x > 0.0 else Control.GROW_DIRECTION_END
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(l)
	return l


func _process(_delta: float) -> void:
	if ended or clock == null:
		return
	if _resume_at_wall >= 0.0:
		var remaining := _resume_at_wall - float(Time.get_ticks_msec()) / 1000.0
		if remaining <= 0.0:
			_resume_at_wall = -1.0
			_countdown.text = ""
			clock.resume()
			lane_input.enabled = true
		else:
			_countdown.text = str(ceili(remaining))
		return
	if clock.state == SongClock.State.PAUSED:
		return
	clock.tick()
	var t := clock.judge_time()
	if clock.state == SongClock.State.COUNTDOWN:
		_countdown.text = str(ceili(clock.countdown_remaining()))
	elif not _countdown.text.is_empty():
		_countdown.text = ""
	if autoplay != null and clock.state == SongClock.State.PLAYING:
		autoplay.step(game, t)
	if clock.state == SongClock.State.PLAYING:
		game.advance(t)
	var wall := float(Time.get_ticks_msec()) / 1000.0
	for ev in game.drain_events():
		_on_game_event(ev, wall)
	for b in range(1, PadView.BUTTONS + 1):
		pad_view.button_down[b] = lane_input.is_button_down(b)
	_update_text(t)
	if clock.state == SongClock.State.PLAYING and t >= pack.duration_s:
		_finish()


func _update_text(t: float) -> void:
	var shown := maxf(t, 0.0)
	_info.text = "%s%s   %s" % [pack.title, (" - " + pack.artist) if not pack.artist.is_empty() else "", "AUTOPLAY " + autoplay.policy if autoplay != null else ""]
	var muted := game.muted_keys()
	_status.text = "%.1f / %.1f s   section: %s   chart: %s   hits %d   misses %d   silent: %s" % [shown, pack.duration_s,
		pack.section_at(shown), game.chart_name, game.total_hits(), game.total_misses(), ", ".join(PackedStringArray(muted)) if not muted.is_empty() else "none"]
	_focus_label.text = focus_text(t)
	_next_label.text = next_text(t)


## The state the pads are drawn in: "play", "muted" (the played voice is silent) or "rest" (nothing to play).
func _pad_state() -> String:
	return _pad_state_at(clock.judge_time())


func _pad_state_at(t: float) -> String:
	var voice := game.focus_voice(t)
	if voice.is_empty():
		return "rest"
	return "muted" if game.is_muted(voice) else "play"


## The big line: which instrument the player is playing at song time `t`, whether it is silent, or that there is nothing to play.
func focus_text(t: float) -> String:
	var voice := game.focus_voice(t)
	if voice.is_empty():
		return "Nothing to play"
	var text := "Playing: " + game.label_of(voice)
	if game.is_muted(voice):
		text += "  (MUTED - hit a cue to bring it back)"
	return text


## The announcement line: from 8 beats before a change, the next instrument and the beats still to go ("" otherwise).
func next_text(t: float) -> String:
	var a := game.focus.announcement(t)
	if not bool(a["showing"]):
		return ""
	return "Next: %s in %d" % [game.label_of(str(a["voice"])), int(a["count"])]


func _on_game_event(ev: Dictionary, wall: float) -> void:
	var pad := int(ev["pad"])
	match str(ev["kind"]):
		"hit":
			var grade := str(ev["grade"]).to_upper()
			pad_view.show_feedback(pad, "HOLD" if ev["hold"] else grade, Color(1.0, 0.95, 0.6), wall)
		"miss":
			pad_view.show_feedback(pad, "MISS", Color(1.0, 0.5, 0.45), wall)
		"hold_let_go":
			pad_view.show_feedback(pad, "LET GO", Color(0.85, 0.8, 0.7), wall)
		"hold_kept":
			pad_view.flash_complete(pad, wall)
		"mute":
			transport.set_stem_muted(str(ev["voice"]), true)
		"restore":
			transport.set_stem_muted(str(ev["voice"]), false)


func _on_button_pressed(button: int, touch_id: int) -> void:
	if ended or clock.state != SongClock.State.PLAYING:
		return
	game.press(button, clock.judge_time(), touch_id)


func _on_button_released(button: int, touch_id: int) -> void:
	if ended or clock.state != SongClock.State.PLAYING:
		return
	game.release(button, clock.judge_time(), touch_id)


func _unhandled_input(event: InputEvent) -> void:
	if clock == null:
		return
	if event.is_action_pressed("ui_cancel") and autoplay == null:
		if ended:
			return
		if clock.state == SongClock.State.PAUSED:
			_resume()
		else:
			_pause()
		get_viewport().set_input_as_handled()


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_APPLICATION_PAUSED:
		if autoplay == null and clock != null and not ended and clock.state in [SongClock.State.PLAYING, SongClock.State.COUNTDOWN]:
			_pause()


func _pause() -> void:
	if ended or clock.state == SongClock.State.PAUSED or _resume_at_wall >= 0.0:
		return
	var was_playing := clock.state == SongClock.State.PLAYING
	clock.pause()
	if was_playing:
		game.pause(clock.judge_time())
	lane_input.clear()
	lane_input.enabled = false
	_pause_label.text = "PAUSED (Esc)"
	_countdown.text = ""


func _resume() -> void:
	if clock.state != SongClock.State.PAUSED:
		return
	_pause_label.text = ""
	_resume_at_wall = float(Time.get_ticks_msec()) / 1000.0 + RESUME_COUNTDOWN_S


## The track is over: settle the books, show and print the per-voice summary.
func _finish() -> void:
	if ended:
		return
	ended = true
	lane_input.enabled = false
	game.finish(pack.duration_s)
	for ev in game.drain_events():
		_on_game_event(ev, 0.0)
	clock.end()
	transport.fade_out(END_FADE_S)
	summary = game.summary()
	summary["autoplay"] = autoplay.policy if autoplay != null else ""
	print("TRACK_SUMMARY ", JSON.stringify(summary))
	_result.text = _summary_text(summary)
	_status.text = "Track finished. Esc or close the window to leave."
	track_finished.emit(summary)
	if _quit_on_end:
		await get_tree().create_timer(0.2).timeout
		transport.stop()
		get_tree().quit(0)


func _summary_text(s: Dictionary) -> String:
	var lines: Array[String] = ["%s: %d cues, %d hits, %d misses" % [str(s["title"]), int(s["cues"]), int(s["hits"]), int(s["misses"])], ""]
	for v in s["voices"]:
		lines.append("%-8s cues %3d   hit %3d (P %d G %d O %d)   missed %3d   let go %d   sounding %5.1f%%" % [
			str(v["label"]), int(v["cues"]), int(v["hit_total"]), int(v["hits"]["perfect"]), int(v["hits"]["great"]),
			int(v["hits"]["ok"]), int(v["misses"]), int(v["hold_let_go"]), float(v["sounding_share"]) * 100.0])
	return "\n".join(PackedStringArray(lines))


## Separated stems partly cancel each other, so their sum peaks above full scale where the recording itself does
## (about +2 dB on a loud master). A hard limiter on the music bus keeps that from clipping at the output; it is
## added once and left there, and does nothing to quieter material.
func _limit_music_bus() -> void:
	var bus := StemTransport.ensure_music_bus()
	for i in AudioServer.get_bus_effect_count(bus):
		if AudioServer.get_bus_effect(bus, i) is AudioEffectHardLimiter:
			return
	var limiter := AudioEffectHardLimiter.new()
	limiter.ceiling_db = -0.3
	limiter.pre_gain_db = 0.0
	AudioServer.add_bus_effect(bus, limiter)
