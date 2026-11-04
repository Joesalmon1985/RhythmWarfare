extends Control
## The continuous story run: one scene hosts the whole run. RunEngine decides the cues, the mix and the route from the song clock; RunAudio plays
## it; the existing StoryStage / StoryPadView / StoryNoteLane / StoryDeck draw it. A world transition swaps which prebuilt StoryStage is shown on
## the downbeat; the clock, the beat grid, the judge and the crowd energy never restart.
##
## Scripted play for tests and recordings: RW_RUN_BOT=perfect|none|accuracy:<f>|blocks:<10110...>, RW_RUN_ROUTES=left,right,... (a direction per
## phase), RW_RUN_VIRTUAL=1 (no audio, a stepped clock), RW_RUN_UNTIL_PHASE=<n>, RW_RUN_START=<node id>.

const COUNTDOWN_S := 2.0
const RESUME_COUNTDOWN_S := 3.0
const ARROW_GLYPH := {"left": "<", "right": ">", "up": "^", "down": "v"}

var data: RunData
var engine: RunEngine
var audio: RunAudio
var transport: StemTransport:  # the audio under the name the recording harness (tools/story/record_music.gd) looks for
	get:
		return audio
var clock: SongClock
var pad_view: StoryPadView
var note_lane: StoryNoteLane
var lane_input: LaneInput
var hud: RunHud
var proxy: StoryRun  # what StoryStage and StoryDeck read: level.bpm and crowd.energy
var stages: Dictionary = {}  # world id -> {stage, assets, data, deck, waypoint}
var active_world := ""
var virtual_mode := false

var _stage_host: Control
var _pause_btn: Button
var _dim: ColorRect
var _pause_panel: PanelContainer
var _settings_panel: Control
var _route_box: Control
var _route_buttons: Dictionary = {}  # dir -> Button
var _flash: ColorRect
var _debug_label: Label
var _resume_at_wall := -1.0
var _vt := -COUNTDOWN_S
var _ended := false
var _over_at := -1.0
var _prebuild: Array = []  # world ids still to build (one per cue-free guard)
var _last_guard_key := -1
var _bot := {}
var _bot_pressed: Dictionary = {}
var _bot_released: Dictionary = {}
var _bot_rng := RandomNumberGenerator.new()
var _bot_routes: PackedStringArray = PackedStringArray()
var _bot_route_done := -1
var _until_phase := -1
var _frame_ms: PackedFloat32Array = PackedFloat32Array()
var event_log: Array = []  # every engine event except judge/cues (scripted checks and recordings read it)
var build_log: Array = []  # [{world, ms}] how long each world stage took to build (the main thread stalls that long)
var phase_log: Array = []  # [{phase, node, t}] for scripted checks


func _ready() -> void:
	theme = UiStyle.theme()
	data = RunData.load_default()
	if not data.errors.is_empty():
		_fatal("The run data is invalid:\n" + "\n".join(PackedStringArray(data.errors)))
		return
	virtual_mode = OS.get_environment("RW_RUN_VIRTUAL") == "1"
	var start := OS.get_environment("RW_RUN_START") if OS.has_environment("RW_RUN_START") else Session.run_start_node
	if start == "" or not data.nodes.has(start):
		start = data.start_node()
	if OS.has_environment("RW_RUN_UNTIL_PHASE"):
		_until_phase = int(OS.get_environment("RW_RUN_UNTIL_PHASE"))
	engine = RunEngine.new(data)
	engine.begin(start)
	proxy = StoryRun.new()
	proxy.level = engine.level
	proxy.crowd = CrowdController.new()
	if virtual_mode:
		clock = SongClock.new(null)
	else:
		audio = RunAudio.new()
		add_child(audio)
		audio.configure(data)
		clock = SongClock.new(audio)
		clock.calibration_ms = Session.calibration_ms
	_build_layout(start)
	_setup_bot()
	Session.run_progress.run_started()
	_handle(engine.update(-5.0))  # the first phase's events (phase_start, mix, charted cues)
	if virtual_mode:
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


# --- layout ---------------------------------------------------------------------------------------------------------------

func _world_of(node_id: String) -> String:
	return str(data.nodes[node_id]["world"])


func _build_stage(world: String) -> Dictionary:
	if stages.has(world):
		return stages[world]
	var t_build := Time.get_ticks_usec()
	var entry := StoryChapters.load_default().chapter(world)
	var loaded := StoryData.load_file(str(entry["data"]))
	var sd: StoryData = loaded["data"]
	var assets := StoryAssets.load_art(sd.art)
	var st := StoryStage.new()
	st.name = "Stage_" + world
	st.set_anchors_preset(Control.PRESET_FULL_RECT)
	st.reduced = Session.reduced_effects
	st.high_contrast = Session.high_contrast
	st.motion = Session.effective_story_motion()
	st.lines = StoryLowRes.LINE_CHOICES[clampi(Session.story_lines, 0, 2)]
	st.visible = false
	_stage_host.add_child(st)
	proxy.data = sd
	proxy.crowd.setup(sd)
	st.setup(assets, sd, proxy)
	if st.map != null:
		st.attach_world(st.map, true)
	var deck := StoryDeck.new()
	deck.setup(assets, proxy, st)
	deck.reduced = Session.reduced_effects
	var rec := {"stage": st, "assets": assets, "data": sd, "deck": deck, "waypoint": st.map.start_id if st.map != null else ""}
	stages[world] = rec
	build_log.append({"world": world, "ms": snappedf(float(Time.get_ticks_usec() - t_build) / 1000.0, 0.1)})
	return rec


func _show_world(world: String) -> void:
	var rec := _build_stage(world)
	for w in stages:
		(stages[w]["stage"] as StoryStage).visible = (w == world)
		(stages[w]["stage"] as StoryStage).process_mode = Node.PROCESS_MODE_INHERIT if w == world else Node.PROCESS_MODE_DISABLED
	active_world = world
	var deck: StoryDeck = rec["deck"]
	pad_view.deck_under = deck.draw_under
	pad_view.deck_over = deck.draw_over
	pad_view.setup_skin(deck)


func _build_layout(start: String) -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bg := ColorRect.new()
	bg.color = Color(0.02, 0.02, 0.06)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	var pad_share: float = Session.PAD_SIZES[clampi(Session.pad_size, 0, 2)]
	var split := 1.0 - pad_share
	_stage_host = Control.new()
	_stage_host.name = "StageHost"
	_stage_host.anchor_right = 1.0
	_stage_host.anchor_bottom = split
	_stage_host.clip_contents = true
	_stage_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_stage_host)
	pad_view = StoryPadView.new()
	pad_view.name = "Pads"
	pad_view.anchor_top = split
	pad_view.anchor_right = 1.0
	pad_view.anchor_bottom = 1.0
	pad_view.setup(engine.level, clock)
	pad_view.high_contrast = Session.high_contrast
	pad_view.reduced_effects = Session.reduced_effects
	pad_view.show_keys = Session.show_keys
	pad_view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pad_view.clip_contents = true
	pad_view.show_reward = false
	pad_view.holding_fn = engine.judge.hold_progress
	pad_view.progress_fn = engine.progress_at
	pad_view.muted_fn = func(_f: String) -> bool: return false
	pad_view.energy_fn = func() -> float: return engine.energy
	add_child(pad_view)
	_show_world(_world_of(start))
	var shade := StoryLaneShade.new()
	shade.pad_view = pad_view
	shade.strength = 0.5 if Session.high_contrast else 0.3
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)
	note_lane = StoryNoteLane.new()
	note_lane.name = "Notes"
	note_lane.glow_tex = (stages[active_world]["assets"] as StoryAssets).sprite("glow").get("tex", null)
	note_lane.anchor_right = 1.0
	note_lane.anchor_bottom = 1.0
	note_lane.mouse_filter = Control.MOUSE_FILTER_IGNORE
	note_lane.setup(engine.level, clock, pad_view)
	note_lane.travel_s = Session.cue_lead_in_s
	note_lane.high_contrast = Session.high_contrast
	note_lane.reduced_effects = Session.reduced_effects
	note_lane.state_fn = engine.judge.cue_state
	add_child(note_lane)
	lane_input = LaneInput.new()
	add_child(lane_input)
	lane_input.rect_provider = pad_view.button_rects
	lane_input.button_pressed.connect(_on_button_pressed)
	lane_input.button_released.connect(_on_button_released)
	hud = RunHud.new()
	hud.engine = engine
	hud.data = data
	hud.name = "Hud"
	hud.set_anchors_preset(Control.PRESET_FULL_RECT)
	hud.reduced = Session.reduced_effects
	hud.stage_h = 0.0
	add_child(hud)
	hud.resized.connect(func() -> void: hud.stage_h = hud.size.y * (1.0 - float(Session.PAD_SIZES[clampi(Session.pad_size, 0, 2)])))
	_route_box = Control.new()
	_route_box.set_anchors_preset(Control.PRESET_FULL_RECT)
	_route_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_route_box.visible = false
	add_child(_route_box)
	_flash = ColorRect.new()
	_flash.color = Color(1, 1, 1, 0)
	_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_flash)
	_debug_label = Label.new()
	_debug_label.position = Vector2(12, 8)
	_debug_label.add_theme_font_size_override("font_size", 13)
	_debug_label.visible = Session.debug
	add_child(_debug_label)
	_pause_btn = Button.new()
	_pause_btn.text = "II"
	_pause_btn.theme = StoryStyle.theme()
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
	_pause_panel.theme = StoryStyle.theme()
	_pause_panel.add_theme_stylebox_override("panel", StoryStyle.panel_box())
	_pause_panel.set_anchors_preset(Control.PRESET_CENTER)
	_pause_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_pause_panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	_pause_panel.visible = false
	add_child(_pause_panel)
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 12)
	_pause_panel.add_child(pv)
	pv.add_child(StoryStyle.title("PAUSED", 36))
	for item in [["Resume", _resume], ["Restart this level", _retry], ["Settings", _open_settings], ["Quit to home", _quit]]:
		pv.add_child(UiStyle.button(item[0], item[1], 360))


# --- scripted player ------------------------------------------------------------------------------------------------------

func _setup_bot() -> void:
	var pol := OS.get_environment("RW_RUN_BOT")
	if pol == "":
		return
	_bot = {"policy": pol}
	_bot_rng.seed = int(OS.get_environment("RW_SEED")) if OS.has_environment("RW_SEED") else 1
	if OS.has_environment("RW_RUN_ROUTES"):
		_bot_routes = OS.get_environment("RW_RUN_ROUTES").split(",")


func _bot_wants(n: Dictionary, idx: int) -> bool:
	var pol := str(_bot["policy"])
	if pol == "perfect":
		return true
	if pol == "none":
		return false
	if pol.begins_with("accuracy:"):
		return _bot_rng.randf() < float(pol.get_slice(":", 1))
	if pol.begins_with("blocks:"):
		var pat := pol.get_slice(":", 1)
		var b := (int(n["phase"]) - 1) * 4 + int(n["block"])
		return b < pat.length() and pat[b] == "1"
	return true


func _bot_step(t: float) -> void:
	if _bot.is_empty():
		return
	var notes := engine.level.notes
	for i in range(maxi(notes.size() - 400, 0), notes.size()):
		var n: Dictionary = notes[i]
		if not _bot_pressed.has(i) and float(n["time"]) <= t:
			_bot_pressed[i] = _bot_wants(n, i)
			if _bot_pressed[i]:
				engine.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
				pad_view.button_down[int(n["pad"])] = true
		if _bot_pressed.get(i, false) and not _bot_released.has(i):
			var end_t := float(n["end_time"]) if n["type"] == "hold" else float(n["time"]) + 0.08
			if end_t <= t:
				_bot_released[i] = true
				engine.release(int(n["pad"]), end_t, int(n["pad"]))
				pad_view.button_down[int(n["pad"])] = false
	if engine.window_open and _bot_route_done != engine.phase_n and engine.phase_beat_at(t) > 52.0:
		_bot_route_done = engine.phase_n
		var k := engine.phase_n - 1
		if k < _bot_routes.size() and _bot_routes[k] != "":
			engine.choose_dir(_bot_routes[k])
			_sync_route_buttons()


# --- frame loop -----------------------------------------------------------------------------------------------------------

func _process(delta: float) -> void:
	if engine == null or clock == null:
		return
	if virtual_mode:
		_process_virtual()
		return
	if _ended and _over_at < 0.0:
		return
	if _resume_at_wall >= 0.0:
		var remaining := _resume_at_wall - float(Time.get_ticks_msec()) / 1000.0
		if remaining <= 0.0:
			_resume_at_wall = -1.0
			hud.countdown = ""
			clock.resume()
			event_log.append({"kind": "resumed", "t": clock.audio_time(), "usec": Time.get_ticks_usec()})
			lane_input.enabled = true
		else:
			hud.countdown = str(ceili(remaining))
			hud.countdown_frac = float(ceili(remaining)) - remaining
		hud.queue_redraw()
		return
	if clock.state == SongClock.State.PAUSED:
		return
	clock.tick()
	var t := clock.judge_time()
	var audio_t := clock.audio_time()
	if clock.state == SongClock.State.COUNTDOWN:
		var rem := clock.countdown_remaining()
		hud.countdown = str(ceili(rem))
		hud.countdown_frac = float(ceili(rem)) - rem
	elif not hud.countdown.is_empty():
		hud.countdown = ""
	if clock.state == SongClock.State.PLAYING:
		_frame_ms.append(delta * 1000.0)
	_advance(t, audio_t)
	_scripted_pause(audio_t)
	if _over_at >= 0.0 and float(Time.get_ticks_msec()) / 1000.0 >= _over_at:
		_go_over()


func _process_virtual() -> void:
	if _ended:
		return
	var rate := float(OS.get_environment("RW_STORY_RATE")) if OS.has_environment("RW_STORY_RATE") else 1.0 / 30.0
	var target := _vt + rate
	var guard := 0
	while _vt < target - 1e-9 and guard < 2000 and not _ended:
		guard += 1
		_vt = minf(_vt + 1.0 / 60.0, target)
		_step_virtual(_vt)


func _step_virtual(t: float) -> void:
	clock.state = SongClock.State.PAUSED
	clock._frozen = t
	_advance(t, t)
	hud.countdown = str(ceili(-t)) if t < 0.0 else ""


func _advance(t: float, audio_t: float) -> void:
	hud.now_t = audio_t
	_bot_step(t)
	_handle(engine.update(t))
	var rec: Dictionary = stages[active_world]
	(rec["stage"] as StoryStage).update(audio_t, engine.energy)
	proxy.crowd.energy = engine.energy
	for b in range(1, PadView.BUTTONS + 1):
		pad_view.button_down[b] = lane_input.is_button_down(b) or bool(pad_view.button_down.get(b, false)) and not _bot.is_empty()
	pad_view.banner_text = _banner(t)
	note_lane.queue_redraw()
	hud.queue_redraw()
	_prebuild_in_guard(t)
	if _debug_label.visible:
		_debug_label.text = "t=%6.2f phase %d (%s) block %d stage %d energy %.0f  fps %d" % [t, engine.phase_n, engine.node_id, engine.block, engine.stage, engine.energy, Engine.get_frames_per_second()]
	if _until_phase > 0 and engine.phase_n > _until_phase and not _ended:
		_ended = true
		print("RUN reached phase %d at %s, energy %.0f" % [engine.phase_n, engine.node_id, engine.energy])
		print("RUN stage builds ", JSON.stringify(build_log))
		if OS.get_environment("RW_STORY_QUIT") == "1":
			get_tree().quit()


func _banner(t: float) -> String:
	var fam := engine.cue_family(engine.block) if engine.block <= 3 else ""
	var beat := engine.phase_beat_at(t)
	var in_block := fmod(maxf(beat, 0.0), 16.0)
	if in_block < 4.0 and t >= 0.0:
		return "DRUMS" if fam == "drums" else "BASS"
	return ""


## Builds the next candidate worlds during cue-free guards (the last 3 beats of a block), one per guard, so a world swap never builds on the downbeat.
func _prebuild_in_guard(t: float) -> void:
	if virtual_mode or t < 0.0:
		return
	var beat := engine.phase_beat_at(t)
	var in_block := fmod(maxf(beat, 0.0), 16.0)
	var key := engine.phase_n * 8 + int(beat / 16.0)
	if in_block >= 13.2 and in_block < 15.0 and key != _last_guard_key:
		_last_guard_key = key
		for opt in engine.options():
			var w := _world_of(str(opt["to"]))
			if not stages.has(w):
				_build_stage(w)
				break


## RW_RUN_PAUSE_AT=<song seconds>: pauses there once and resumes a second later (the recording checks nothing drifts across it).
var _pause_done := false


func _scripted_pause(audio_t: float) -> void:
	if _pause_done or not OS.has_environment("RW_RUN_PAUSE_AT") or clock.state != SongClock.State.PLAYING:
		return
	if audio_t >= float(OS.get_environment("RW_RUN_PAUSE_AT")):
		_pause_done = true
		_pause()
		get_tree().create_timer(1.0).timeout.connect(_resume)


# --- engine events --------------------------------------------------------------------------------------------------------

func _handle(events: Array) -> void:
	for ev in events:
		if str(ev["kind"]) != "judge" and str(ev["kind"]) != "cues":
			event_log.append(ev)
		if audio != null:
			audio.on_event(ev)
		match str(ev["kind"]):
			"judge":
				_on_judge_event(ev["event"], float(Time.get_ticks_msec()) / 1000.0)
			"cues":
				pad_view.refresh()
				note_lane.refresh()
			"phase_start":
				_on_phase_start(ev)
			"mix":
				_on_mix(ev)
			"reveal":
				hud.caption("BASS ENTERS", "good", float(ev["t"]))
			"block_result":
				_on_block_result(ev)
			"route_window":
				_open_routes(ev)
			"route_commit":
				_close_routes(ev)
			"depleted":
				hud.caption("THE CROWD DRIFTS AWAY", "bad", float(ev["t"]), 2.4)
				_end_fade(float(ev["t"]), float(ev["fade_s"]))
			"run_over":
				_over_at = float(Time.get_ticks_msec()) / 1000.0 + (0.4 if not virtual_mode else 0.0)
				_ended = true if virtual_mode else _ended
				Session.run_result = {"node": ev["node"], "phases": ev["phase"], "energy": ev["energy"], "reason": "the crowd left", "start": engine.node_id}
				if virtual_mode:
					Session.run_progress.run_ended(int(ev["phase"]))
					print("RUN over at phase %d (%s)" % [int(ev["phase"]), str(ev["node"])])
					if OS.get_environment("RW_STORY_QUIT") == "1":
						get_tree().quit()


func _on_phase_start(ev: Dictionary) -> void:
	var node: Dictionary = data.nodes[str(ev["node"])]
	var world := str(node["world"])
	var t0 := float(ev["t"])
	phase_log.append({"phase": ev["phase"], "node": ev["node"], "t": t0})
	Session.run_progress.enter(str(ev["node"]))
	hud.show_title("LEVEL %d" % int(ev["phase"]), str(node["title"]).to_upper(), t0)
	var first := stages.is_empty() or active_world == ""
	if world != active_world or t0 > 0.0 and not stages.has(world):
		if not first:
			_flash_world(t0)
		_show_world(world)
	var rec: Dictionary = stages[world]
	var st: StoryStage = rec["stage"]
	var wp := str(node["waypoint"])
	st.apply({"t0": t0, "action": "player_role", "args": {"role": str(node["role"])}, "bar": 0.0, "block": "run", "source": "run"})
	if wp != "" and wp != str(rec["waypoint"]):
		st.apply({"t0": t0, "action": "player_move", "args": {"to": wp, "bars": 3.0, "style": "walk"}, "bar": 0.0, "block": "run", "source": "run"})
		rec["waypoint"] = wp
	_stage_action(st, "lights_low_pulse", t0)
	if int(ev["phase"]) == 1:
		_stage_action(st, "doors_open", t0)


func _stage_action(st: StoryStage, name: String, t0: float, args: Dictionary = {}) -> void:
	st.apply({"t0": t0, "action": name, "args": args, "bar": 0.0, "block": "run", "source": "run"})


func _on_mix(ev: Dictionary) -> void:
	var st: StoryStage = stages[active_world]["stage"]
	var t0 := float(ev["t"])
	match int(ev["stage"]):
		1:
			_stage_action(st, "bass_reveal", t0)
		2:
			_stage_action(st, "lights_warm", t0)
			_stage_action(st, "beams_sweep", t0)
		3:
			_stage_action(st, "lights_rave", t0)
			_stage_action(st, "beams_fan", t0)
			_stage_action(st, "led_eq", t0)


func _on_block_result(ev: Dictionary) -> void:
	var t := float(ev["t"]) + 0.2
	if bool(ev["passed"]):
		if int(ev["block"]) < 3:
			pad_view.show_status("Nice: the mix moves on", Color(0.7, 1.0, 0.8), float(Time.get_ticks_msec()) / 1000.0)
	else:
		hud.caption("HOLDING THE MIX: HAVE ANOTHER GO", "bad", t, 2.2)
		pad_view.show_status("Missed it: same cues again", Color(1.0, 0.75, 0.55), float(Time.get_ticks_msec()) / 1000.0)


func _flash_world(t0: float) -> void:
	_flash.color = Color(1, 1, 1, 0.0)
	var tw := create_tween()
	tw.tween_property(_flash, "color:a", 0.0, 0.0)
	tw.tween_property(_flash, "color:a", 0.85, 0.12)
	tw.tween_property(_flash, "color:a", 0.0, 0.5)


func _end_fade(_t: float, seconds: float) -> void:
	var tw := create_tween()
	tw.tween_interval(maxf(_t - hud.now_t, 0.0))
	tw.tween_property(hud, "fade", 1.0, maxf(seconds, 0.2))


# --- routes ---------------------------------------------------------------------------------------------------------------

func _open_routes(ev: Dictionary) -> void:
	for c in _route_box.get_children():
		c.queue_free()
	_route_buttons.clear()
	var opts: Array = ev["options"]
	var w := size.x
	var h := size.y * (1.0 - float(Session.PAD_SIZES[clampi(Session.pad_size, 0, 2)]))
	for o in opts:
		var dir := str(o["dir"])
		var b := Button.new()
		b.theme = StoryStyle.theme()
		b.focus_mode = Control.FOCUS_NONE
		b.add_theme_font_size_override("font_size", int(clampf(h * 0.09, 16.0, 30.0)))
		b.custom_minimum_size = Vector2(minf(w * 0.3, 360.0), clampf(h * 0.22, 64.0, 120.0))
		b.size = b.custom_minimum_size
		var pos := Vector2.ZERO
		match dir:
			"left":
				pos = Vector2(w * 0.02, h * 0.42)
			"right":
				pos = Vector2(w * 0.98 - b.size.x, h * 0.42)
			"up":
				pos = Vector2((w - b.size.x) * 0.5, h * 0.08)
			_:
				pos = Vector2((w - b.size.x) * 0.5, h * 0.62)
		b.position = pos
		b.set_meta("to", str(o["to"]))
		b.set_meta("label", str(o["label"]))
		b.set_meta("default", bool(o["default"]))
		b.pressed.connect(func() -> void:
			engine.choose(str(o["to"]))
			_sync_route_buttons())
		_route_box.add_child(b)
		_route_buttons[dir] = b
	_route_box.visible = true
	_sync_route_buttons()
	if audio != null:
		for o in opts:
			audio.preload_pack(str(data.nodes[str(o["to"])]["audio"]))
	hud.caption("RISER: CHOOSE YOUR WAY" if str(ev["effect"]) == "riser" else "FALL: CHOOSE YOUR WAY", "info", float(ev["t"]), 3.0)


func _sync_route_buttons() -> void:
	var picked := engine.selected_route()
	for dir in _route_buttons:
		var b: Button = _route_buttons[dir]
		var to := str(b.get_meta("to"))
		var chosen := to == picked
		var tag := ""
		if chosen:
			tag = "  [DEFAULT]" if engine.choice == "" else "  [CHOSEN]"
		b.text = "%s  %s%s\n%s" % [ARROW_GLYPH.get(dir, "?"), str(data.nodes[to]["title"]), tag, str(b.get_meta("label"))]
		b.modulate = Color(1.0, 0.95, 0.6) if chosen else Color(0.85, 0.88, 1.0, 0.9)
	hud.route_hint = "Tap an arrow to choose where to go (arrow keys work too). Changes count until the downbeat."


func _close_routes(_ev: Dictionary) -> void:
	_route_box.visible = false
	hud.route_hint = ""
	for c in _route_box.get_children():
		c.queue_free()
	_route_buttons.clear()


func _unhandled_key_input(event: InputEvent) -> void:
	if not (event is InputEventKey) or not event.pressed or event.echo or not engine.window_open:
		return
	var dir := ""
	match (event as InputEventKey).keycode:
		KEY_LEFT:
			dir = "left"
		KEY_RIGHT:
			dir = "right"
		KEY_UP:
			dir = "up"
	if dir != "" and engine.choose_dir(dir):
		_sync_route_buttons()


# --- judge feedback and input ---------------------------------------------------------------------------------------------

func _on_judge_event(ev: Dictionary, wall: float) -> void:
	var pad: int = int(ev.get("pad", ev.get("button", 0)))
	match ev["kind"]:
		"perfect":
			pad_view.show_feedback(pad, "PERFECT", Color(1.0, 0.95, 0.6), wall)
		"great", "good":
			pad_view.show_feedback(pad, "GREAT", Color(0.7, 0.95, 0.7), wall)
		"ok":
			pad_view.show_feedback(pad, "OK", Color(0.75, 0.85, 0.9), wall)
		"hold_start":
			pad_view.show_feedback(pad, "HOLD", Color(0.75, 0.85, 1.0), wall)
		"hold_complete":
			pad_view.flash_complete(pad, wall)
			pad_view.show_feedback(pad, "HELD", Color(0.8, 1.0, 0.8), wall)
		"hold_partial":
			pad_view.show_feedback(pad, "LET GO", Color(0.85, 0.8, 0.7), wall)
		"miss", "hold_fail":
			pad_view.show_feedback(pad, "MISS", Color(1.0, 0.5, 0.45), wall)
	if ev["kind"] in ["perfect", "great", "good", "ok", "hold_start"] and Session.vibration and OS.has_feature("mobile"):
		Input.vibrate_handheld(18)


func _on_button_pressed(button: int, touch_id: int) -> void:
	if _ended or clock.state == SongClock.State.PAUSED:
		return
	engine.press(button, clock.judge_time(), touch_id)


func _on_button_released(button: int, touch_id: int) -> void:
	if _ended:
		return
	engine.release(button, clock.judge_time(), touch_id)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if clock == null or engine == null or _ended and _over_at < 0.0:
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
		if not virtual_mode and _bot.is_empty() and clock != null and not _ended and clock.state in [SongClock.State.PLAYING, SongClock.State.COUNTDOWN]:
			_pause()


# --- pause ----------------------------------------------------------------------------------------------------------------

func _pause() -> void:
	if virtual_mode or _ended or clock.state == SongClock.State.PAUSED or _resume_at_wall >= 0.0:
		return
	clock.pause()
	event_log.append({"kind": "paused", "t": clock.audio_time(), "usec": Time.get_ticks_usec()})
	engine.judge.pause_interrupt(clock.judge_time())
	lane_input.clear()
	lane_input.enabled = false
	_pause_panel.visible = true
	_dim.visible = true
	hud.countdown = ""


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
	hud.reduced = Session.reduced_effects
	clock.calibration_ms = Session.calibration_ms
	_pause_panel.visible = true


## Restart the level the player is on, with fresh energy and its authored opening.
func _retry() -> void:
	if audio != null:
		audio.stop()
	Session.run_start_node = engine.node_id
	get_tree().reload_current_scene()


func _quit() -> void:
	if audio != null:
		audio.stop()
	get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn")


func _go_over() -> void:
	if audio != null:
		audio.stop()
	Session.run_progress.run_ended(int(Session.run_result.get("phases", 0)))
	set_process(false)
	get_tree().change_scene_to_file("res://src/run/run_over.tscn")
