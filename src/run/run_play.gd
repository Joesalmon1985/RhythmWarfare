extends Control
## The continuous story run: one scene hosts the whole run. RunEngine decides the cues, the mix and the route from the song clock; RunAudio plays
## it; the existing StoryStage / StoryPadView / StoryNoteLane / StoryDeck draw it. A world transition swaps which prebuilt StoryStage is shown on
## the downbeat; the clock, the beat grid, the judge and the crowd energy never restart.
##
## Scripted play for tests and recordings: RW_RUN_BOT=perfect|none|accuracy:<f>|blocks:<10110...>, RW_RUN_ROUTES=left,right,... (a direction per
## phase: the bot taps the hotspot that leads there), RW_RUN_TAPS=scripted|none|changed|failure (the tap policy: the scripted taps, no taps at all (the default exits), a decoy tapped first and
## then the scripted one, the scripted taps with the last block of every phase missed), RW_RUN_VIRTUAL=1 (no audio, a stepped clock), RW_RUN_UNTIL_PHASE=<n>, RW_RUN_START=<node id>,
## RW_RUN_ARROWS=1 (the old route arrows and lit doors instead of the hotspots, until the data is converted).
##
## The route window is the hotspot window (docs/CONTINUOUS_RUN.md "Hotspots"): the player touches the world (HotspotView, RunHotspots); the last block's result picks the outcome.

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
var trial_launcher: Callable  # called when the wizard is chosen and the block he waited for is passed (tests replace it)
var hotspots: RunHotspots  # the scene's hotspots (null with RW_RUN_ARROWS=1: the old arrows)
var arrows := false  # RW_RUN_ARROWS=1
var hotspot_log: Array = []  # [{kind: select | tap_miss | commit, t, ...}] for the tests and the walks
var tap_policy := "scripted"
var _sel_t: Dictionary = {}  # hotspot id -> song time it was selected
var _commit_view: Dictionary = {}  # {id, t, hotspot}: the committed hotspot stays drawn for a moment (the flash)
var _last_tap_ms := -1000
var _last_tap_pos := Vector2(-9999, -9999)
var _bot_decoy_done := -1
var _gate: Control
var _gate_btn: Button
var _gate_wizard: TextureRect

var _stage_host: Control
var _pause_btn: Button
var _dim: ColorRect
var _pause_panel: PanelContainer
var _settings_panel: Control
var _route_box: Control
var _route_buttons: Dictionary = {}  # dir -> Button
var _debug_label: Label
var _resume_at_wall := -1.0
var _vt := -COUNTDOWN_S
var _ended := false
var _over_at := -1.0
var _prewarmed: Dictionary = {}  # world id -> true once its sheets were handed to a worker thread
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
var _last_frame_us := 0
var event_log: Array = []  # every engine event except judge/cues (scripted checks and recordings read it)
var build_log: Array = []  # [{world, ms}] how long each world stage took to build (the main thread stalls that long)
var phase_log: Array = []  # [{phase, node, t}] for scripted checks
var journey: RunJourney  # the player's rails (pure logic; the scene only hands its actions to the stages)
var journey_log: Array = []  # every journey action given to a stage: {world, t0, action, args}
var _passage_swap := -1.0  # song time of the downbeat a world swap walks through (-1: none under way)
var _door_phase := -1  # the phase whose door walk (a path inside the world) was started
var _run_world := ""  # the run world of the phase before the current one (a change closes the passage frame)
var _passage: RunPassageView
var _exits: RunExitsView
var trial: TrialScene  # the Bassment, hosted here: the same scene, clock, pads and audio (docs/TRIAL_OPENING.md)
var tdata: TrialData
var trial_state := ""  # "" | "armed" (the wizard was chosen: the walk to the hatch is scheduled) | "in" (the dungeon owns the pads) | "leaving"
var trial_entry_t := -1.0  # the downbeat the dungeon is entered on
var _trial_g1 := -1.0  # the cue-free guard the walk to the hatch starts on
var _trial_g2 := -1.0  # the guard the dungeon takes the pads on
var _trial_direct := false
var _stage_hidden := ""
var trial_log: Array = []  # [{kind, t, ...}] the entry and exit, for the transition tests and recordings


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
	tdata = TrialData.load_default()
	if not tdata.errors.is_empty():
		_fatal("The dungeon data is invalid:\n" + "\n".join(PackedStringArray(tdata.errors)))
		return
	_trial_direct = OS.get_environment("RW_TRIAL_START") != "" or OS.get_environment("RW_TRIAL_DIRECT") == "1" or Session.trial_direct
	Session.trial_direct = false
	if _trial_direct:
		start = "warehouse" if data.nodes.has("warehouse") else start
	engine = RunEngine.new(data)
	journey = RunJourney.new(data)
	arrows = OS.get_environment("RW_RUN_ARROWS") == "1"
	tap_policy = OS.get_environment("RW_RUN_TAPS") if OS.has_environment("RW_RUN_TAPS") and OS.get_environment("RW_RUN_TAPS") != "" else "scripted"
	if not arrows:
		hotspots = RunHotspots.new(data, Session.run_progress.run_flags, Session.run_progress.flags)
		engine.hotspots = hotspots
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
	if _trial_direct:  # a launch straight into the dungeon: the run's first phase is never heard
		var sp := int(OS.get_environment("RW_TRIAL_START")) if OS.get_environment("RW_TRIAL_START") != "" else -1
		trial.bot = OS.get_environment("RW_TRIAL_BOT") if OS.get_environment("RW_TRIAL_BOT") != "" else str(_bot.get("policy", ""))
		trial_state = "in"
		trial_begin_now(0.0, sp, true)
		var ci: float = trial.engine.count_in_s()
		_vt = -ci
		hud.visible = false
		_gate.visible = false
		if virtual_mode:
			_step_virtual(_vt)
		else:
			clock.begin_countdown(ci)
		return
	_handle(engine.update(-5.0))  # the first phase's events (phase_start, mix, charted cues)
	if _build_hatch_early():
		pass
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

## The art world (the stage key) a scene is built on; the run world (the save's id, the passage frame) is node["world"].
func _world_of(node_id: String) -> String:
	return str(data.nodes[node_id]["map"])


func _run_world_of(node_id: String) -> String:
	return str(data.nodes[node_id]["world"])


func _build_stage(world: String) -> Dictionary:
	if stages.has(world):
		return stages[world]
	var t_build := Time.get_ticks_usec()
	var entry := StoryChapters.load_default().chapter(world)
	var loaded := StoryData.load_file(str(entry["data"]))
	var sd: StoryData = loaded["data"]
	var t_art := Time.get_ticks_usec()
	var assets := StoryAssets.load_art(sd.art)
	var t_stage := Time.get_ticks_usec()
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
	var t_world := Time.get_ticks_usec()
	if st.map != null:
		st.attach_world(st.map, true)
	var t_deck := Time.get_ticks_usec()
	var deck := StoryDeck.new()
	deck.setup(assets, proxy, st)
	deck.reduced = Session.reduced_effects
	var rec := {"stage": st, "assets": assets, "data": sd, "deck": deck, "waypoint": st.map.start_id if st.map != null else ""}
	if hotspots != null and st.lowres != null:  # the hotspots are drawn inside the picture, above the crowd
		var hv := HotspotView.new()
		hv.name = "Hotspots"
		hv.stage = st
		hv.beat_s = engine.beat_s
		hv.items_fn = hotspot_items
		hv.pose_fn = _exit_pose
		hv.now_fn = func() -> float: return hud.now_t
		hv.reduced = Session.reduced_effects
		hv.high_contrast = Session.high_contrast
		hv.glow_tex = assets.sprite("glow").get("tex", null)
		var warm: Array = st.palettes.get("warm", [])
		if not warm.is_empty():
			hv.tint = (warm[0] as Color).lerp(Color(1.0, 0.9, 0.6), 0.55)
		hv.set_anchors_preset(Control.PRESET_FULL_RECT)
		var layer := st.lowres.add_overlay(hv, "Hotspots")
		layer.layer = 2
		rec["hotspot_view"] = hv
	stages[world] = rec
	var now := Time.get_ticks_usec()
	build_log.append({"world": world, "ms": snappedf(float(now - t_build) / 1000.0, 0.1), "parts_ms": {"data": snappedf(float(t_art - t_build) / 1000.0, 1.0), "art": snappedf(float(t_stage - t_art) / 1000.0, 1.0),
		"stage": snappedf(float(t_world - t_stage) / 1000.0, 1.0), "world": snappedf(float(t_deck - t_world) / 1000.0, 1.0), "deck": snappedf(float(now - t_deck) / 1000.0, 1.0)}})
	return rec


## Decodes the people sheets of the worlds this level can lead to on worker threads (the stage build then only uploads them, see StoryPeople.prewarm).
func _prewarm_routes(node_id: String) -> void:
	if virtual_mode:
		return
	for e in data.nodes[node_id]["next"]:
		var w := _world_of(str(e["to"]))
		if stages.has(w) or _prewarmed.has(w):
			continue
		_prewarmed[w] = true
		var entry := StoryChapters.load_default().chapter(w)
		var sd: StoryData = StoryData.load_file(str(entry["data"]))["data"]
		StoryPeople.prewarm(StoryAssets.load_art(sd.art))


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
	_build_gate()
	_passage = RunPassageView.new()
	_passage.name = "Passage"
	_passage.anchor_right = 1.0
	_passage.anchor_bottom = split
	_passage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_passage)
	_exits = RunExitsView.new()
	_exits.name = "Exits"
	_exits.anchor_right = 1.0
	_exits.anchor_bottom = split
	_exits.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_exits.visible = false
	_exits.beat_s = engine.beat_s
	_exits.pose_fn = _exit_pose
	_exits.process_mode = Node.PROCESS_MODE_INHERIT if arrows else Node.PROCESS_MODE_DISABLED
	_exits.now_fn = func() -> float: return hud.now_t
	add_child(_exits)
	trial = TrialScene.new()
	trial.name = "Trial"
	add_child(trial)
	trial.setup(self, tdata, data)
	_route_box = Control.new()
	_route_box.set_anchors_preset(Control.PRESET_FULL_RECT)
	_route_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_route_box.visible = false
	add_child(_route_box)
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


# --- the wizard and the Trial ----------------------------------------------------------------------------------------------

## A wizard waits at the edge of the Warehouse floor with a floating "Enter the Trial". Choosing it leaves the run for the Deathtrap Dungeon opening
## (res://src/trial/trial_play.tscn); ignoring it changes nothing: the run, its pads and its routes go on as before.
func _build_gate() -> void:
	_gate = Control.new()
	_gate.name = "TrialGate"
	_gate.set_anchors_preset(Control.PRESET_FULL_RECT)
	_gate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_gate.visible = false
	add_child(_gate)
	_gate_wizard = TextureRect.new()
	_gate_wizard.texture = load("res://assets/trial/art/wizard.png") as Texture2D
	_gate_wizard.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_gate_wizard.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	_gate_wizard.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_gate_wizard.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_gate.add_child(_gate_wizard)
	if arrows:  # the old floating button (RW_RUN_ARROWS=1); otherwise the wizard is a character hotspot and carries no text
		_gate_btn = Button.new()
		_gate_btn.text = "Enter the Trial"
		_gate_btn.theme = StoryStyle.theme()
		_gate_btn.focus_mode = Control.FOCUS_NONE
		_gate_btn.modulate = Color(1.0, 0.9, 0.6)
		_gate_btn.pressed.connect(func() -> void: trial_launcher.call())
		_gate.add_child(_gate_btn)
	_gate_wizard.visible = arrows  # with hotspots the wizard is a thing of the map
	trial_launcher = func() -> void: arm_trial()
	resized.connect(_layout_gate)
	_layout_gate()


func _layout_gate() -> void:
	if _gate == null:
		return
	var stage_h := size.y * (1.0 - float(Session.PAD_SIZES[clampi(Session.pad_size, 0, 2)]))
	var s := clampf(stage_h * 0.42, 64.0, 150.0)
	_gate_wizard.size = Vector2(s, s)
	_gate_wizard.position = Vector2(size.x * 0.02, stage_h - s - 4.0)
	if _gate_btn == null:
		return
	_gate_btn.add_theme_font_size_override("font_size", int(clampf(stage_h * 0.05, 13.0, 22.0)))
	_gate_btn.size = Vector2(maxf(s * 1.9, 150.0), clampf(stage_h * 0.13, 40.0, 60.0))
	_gate_btn.position = Vector2(size.x * 0.02, _gate_wizard.position.y - _gate_btn.size.y - 6.0)


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
	if tap_policy == "failure" and int(n["block"]) == 3:  # the failure taps: the last block of every phase is missed, so the selected hotspot fails
		return false
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
	if hotspots != null:
		_bot_taps(t)
		return
	if engine.window_open and _bot_route_done != engine.phase_n and engine.phase_beat_at(t) > 52.0:
		_bot_route_done = engine.phase_n
		var k := engine.phase_n - 1
		if k < _bot_routes.size() and _bot_routes[k] != "":
			engine.choose_dir(_bot_routes[k])
			_sync_route_buttons()


## The scripted taps (RW_RUN_TAPS): `scripted` taps the hotspot that leads where RW_RUN_ROUTES says (a direction per phase) at beat 52; `none` never taps; `changed` first taps a decoy at beat 50;
## `failure` is `scripted` with the last block missed (see _bot_wants). Taps go through hotspot_select exactly as a finger would (the same availability, the same window).
func _bot_taps(t: float) -> void:
	if tap_policy == "none" or not engine.window_open:
		return
	var beat := engine.phase_beat_at(t)
	var k := engine.phase_n - 1
	if tap_policy == "changed" and _bot_decoy_done != engine.phase_n and beat > 50.0:
		_bot_decoy_done = engine.phase_n
		var want := _route_for_dir(k)
		for h in hotspots.shown(engine.block, engine.window_open):
			if str(h["on_success"].get("route", "")) != want:
				hotspot_select(str(h["id"]))
				break
	if _bot_route_done != engine.phase_n and beat > 52.0:
		_bot_route_done = engine.phase_n
		var to := _route_for_dir(k)
		if to != "":
			for h in hotspots.shown(engine.block, engine.window_open):
				if str(h["on_success"].get("route", "")) == to:
					hotspot_select(str(h["id"]))
					break


func _route_for_dir(k: int) -> String:
	if k < 0 or k >= _bot_routes.size() or _bot_routes[k] == "":
		return ""
	for o in engine.options():
		if str(o["dir"]) == _bot_routes[k]:
			return str(o["to"])
	return ""


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
		var now_us := Time.get_ticks_usec()  # wall time between frames (delta is clamped by the engine, so a stall would hide in it)
		if _last_frame_us > 0:
			_frame_ms.append(float(now_us - _last_frame_us) / 1000.0)
		_last_frame_us = now_us
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
	if trial_state == "in" or trial_state == "leaving":
		if OS.has_environment("RW_TRIAL_LEAVE_AT") and audio_t >= float(OS.get_environment("RW_TRIAL_LEAVE_AT")) and trial.active:
			trial.request_leave()  # scripted: the back key, for the recordings
		trial.update(t, audio_t)
		return
	_bot_step(t)
	_trial_step(t)
	if trial_state == "in":
		trial.update(t, audio_t)
		return
	if _gate.visible and _gate_btn != null:  # the option floats
		var bob := sin(audio_t * 2.0) * 4.0
		_gate_btn.position.y = _gate_wizard.position.y - _gate_btn.size.y - 6.0 + bob
	elif hotspots != null:
		_place_wizard(audio_t)
	if trial_state == "armed" and trial_entry_t >= 0.0:
		_handle(engine.update(minf(t, trial_entry_t - 0.001)))
	else:
		_handle(engine.update(t))
	if trial_state == "":
		_update_passage(t, audio_t)
	else:
		_passage.set_aperture(RunPassage.aperture(audio_t, trial_entry_t, engine.beat_s))
	if trial_state == "in" or trial_state == "leaving":
		return
	var rec: Dictionary = stages[active_world]
	(rec["stage"] as StoryStage).update(audio_t, engine.energy)
	proxy.crowd.energy = engine.energy
	for b in range(1, PadView.BUTTONS + 1):
		pad_view.button_down[b] = lane_input.is_button_down(b) or bool(pad_view.button_down.get(b, false)) and not _bot.is_empty()
	pad_view.banner_text = _banner(t)
	note_lane.queue_redraw()
	hud.queue_redraw()
	if trial_state == "":
		_prebuild_in_guard(t)
	if _debug_label.visible:
		_debug_label.text = "t=%6.2f phase %d (%s) block %d stage %d energy %.0f rail %s (%s)  fps %d" % [t, engine.phase_n, engine.node_id, engine.block, engine.stage, engine.energy, journey.rail.place() if journey.rail != null else "-", journey.rail.role if journey.rail != null else "-", Engine.get_frames_per_second()]
	if _until_phase > 0 and engine.phase_n > _until_phase and not _ended:
		_ended = true
		print("RUN reached phase %d at %s, energy %.0f" % [engine.phase_n, engine.node_id, engine.energy])
		print("RUN stage builds ", JSON.stringify(build_log))
		print("RUN ", frame_stats())
		print("RUN summary ", JSON.stringify(summary()))
		if OS.get_environment("RW_STORY_QUIT") == "1":
			get_tree().quit()


## A world change is a walk through a doorway: from beat 62 of a phase whose chosen route leads to another world the frame closes to a lit door, and it opens on the
## new world after the downbeat. The latch is decided once per phase at beat 62 (a change of mind in the last two beats cuts instead).
## A path inside the world is a plain door walk (no frame, the stage stays): from beat 61 the camera walks to the doorway of the selected route, and on the downbeat on
## through it into the next scene (RunJourney.door_walk). Also latched once per phase.
func _update_passage(t: float, audio_t: float) -> void:
	if engine.window_open and t >= 0.0 and _door_phase != engine.phase_n and engine.phase_beat_at(t) >= 64.0 - RunPassage.DOOR_BEATS:
		_door_phase = engine.phase_n
		var to0 := engine.selected_route()
		if _run_world_of(to0) == _run_world_of(engine.node_id) and to0 != engine.node_id:
			for a in journey.leave_walk(engine.t_of(64.0 - RunPassage.DOOR_BEATS), to0, engine):
				_journey_apply(a)
	if engine.window_open and _passage_swap < 0.0 and engine.phase_beat_at(t) >= 64.0 - RunPassage.CLOSE_BEATS and t >= 0.0:
		var to := engine.selected_route()
		if _run_world_of(to) != _run_world_of(engine.node_id):
			_passage_swap = engine.t_of(64.0)
	if _passage_swap >= 0.0 and audio_t > _passage_swap + RunPassage.OPEN_BEATS * engine.beat_s + 0.5:
		_passage_swap = -1.0
	_passage.set_aperture(RunPassage.aperture(audio_t, _passage_swap, engine.beat_s))


func _exit_pose() -> Dictionary:
	var st: StoryStage = stages[active_world]["stage"]
	if st.player == null:
		return {}
	var pose := st.player.pose_at(hud.now_t)
	return {"cam": pose["cam"], "yaw": float(pose["yaw"]) + st.free_look.offset, "pitch": float(pose.get("pitch", 0.0))}


## The exits to light while the window is open: [{dir, glyph, at, ground, chosen}] for the routes whose doorway the rail knows.
func exit_items() -> Array:
	var out: Array = []
	var st: StoryStage = stages[active_world]["stage"]
	if st.map == null or journey.rail == null:
		return out
	var picked := engine.selected_route()
	for o in engine.options():
		var dir := str(o["dir"])
		var wid := str(journey.rail.exits.get(dir, ""))
		if wid == "" or not st.map.has_waypoint(wid):
			continue
		var w: Dictionary = st.map.waypoint(wid)
		out.append({"dir": dir, "glyph": ARROW_GLYPH.get(dir, "?"), "at": w["at"], "ground": float(st.map.sector(str(w["sector"])).get("floor", 0.0)), "chosen": str(o["to"]) == picked})
	return out


## What a scripted run did, for tools/run/walk_run.sh: the levels in order, the rail places per level, the journey's moves and glances, the worlds shown.
func summary() -> Dictionary:
	var rails: Array = []
	for e in journey.log:
		rails.append("%d.%d:%s:%s" % [int(e["phase"]), int(e["block"]), str(e["node"]), str(e["place"])])
	var moves := 0
	var looks := 0
	var walks := 0
	for a in journey_log:
		match str(a["action"]):
			"player_move":
				moves += 1
			"player_look":
				looks += 1
			"player_walk":
				walks += 1
	var worlds_seen: Array = []
	for p in phase_log:
		var wid := str(data.nodes[str(p["node"])]["world"])
		if worlds_seen.is_empty() or worlds_seen[worlds_seen.size() - 1] != wid:
			worlds_seen.append(wid)
	return {"nodes": phase_log.map(func(p: Dictionary) -> String: return str(p["node"])), "worlds_seen": worlds_seen, "rail": rails, "moves": moves, "glances": looks, "strolls": walks, "worlds": stages.keys(),
		"energy": snappedf(engine.energy, 0.1), "reached": Session.run_progress.reached_ids()}


## "FRAMES n mean .. p95 .. max .. ms" of the frames played so far, and how many ran over 50 ms (a stage build or a stall). Real-time runs only.
func frame_stats() -> String:
	if _frame_ms.is_empty():
		return "FRAMES none (a virtual run has no real frame times)"
	var sorted := _frame_ms.duplicate()
	sorted.sort()
	var sum := 0.0
	var over := 0
	for v in sorted:
		sum += v
		if v > 50.0:
			over += 1
	return "FRAMES %d mean %.1f p95 %.1f max %.0f ms, %d over 50 ms" % [sorted.size(), sum / sorted.size(), sorted[int(sorted.size() * 0.95)], sorted[sorted.size() - 1], over]


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
	if in_block >= 12.6 and in_block < 15.0 and key != _last_guard_key:
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
		if str(ev["kind"]) in ["phase_start", "block_result"] and trial_state == "":  # the journey first: the stage already holds its actions when the scene reacts
			for a in journey.on_event(ev, engine):
				_journey_apply(a)
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
				if trial_state == "":
					_open_routes(ev)
			"hotspot_commit":
				_on_hotspot_commit(ev)
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
					print("RUN summary ", JSON.stringify(summary()))
					if OS.get_environment("RW_STORY_QUIT") == "1":
						get_tree().quit()


func _on_phase_start(ev: Dictionary) -> void:
	var node: Dictionary = data.nodes[str(ev["node"])]
	var world := str(node["map"])
	var t0 := float(ev["t"])
	phase_log.append({"phase": ev["phase"], "node": ev["node"], "t": t0})
	_sel_t.clear()
	if int(ev["phase"]) > 1 or trial_state == "":
		_commit_view = {}
	Session.run_progress.enter(str(node["world"]))  # "reached" is per world: a restart begins at the world's entry scene
	var first := int(ev["phase"]) == 1
	var world_changed := not first and str(node["world"]) != _run_world
	if world_changed or first:
		hud.show_title("%s   LEVEL %d" % [str(node["world_title"]).to_upper(), int(ev["phase"])], str(node["title"]).to_upper(), t0)
	else:
		hud.show_title(str(node["world_title"]).to_upper(), str(node["title"]).to_upper(), t0)
	if world_changed and _passage_swap < 0.0:
		_passage_swap = t0  # the route changed in the last two beats: the frame opens from shut on the new world
	if world != active_world:
		_show_world(world)
	_run_world = str(node["world"])
	_gate.visible = str(node.get("trial_gate", "")) != "" and trial_state == ""  # the wizard only waits in the Warehouse
	_prewarm_routes(str(ev["node"]))
	var rec: Dictionary = stages[world]
	var st: StoryStage = rec["stage"]
	var wp := str(node["waypoint"])
	if first and wp != "" and wp != str(rec["waypoint"]):  # starting on a level whose home is not the map's start: walk there during the countdown
		_journey_apply({"world": world, "t0": t0 - 4.0 * engine.beat_s, "action": "player_move", "args": {"to": wp, "bars": 3.0, "style": "walk"}})
		rec["waypoint"] = wp
	_stage_action(st, "lights_low_pulse", t0)
	if int(ev["phase"]) == 1:
		_stage_action(st, "doors_open", t0)


## Hands one journey action {world, t0, action, args} to its world's stage and keeps it in the log.
func _journey_apply(a: Dictionary) -> void:
	journey_log.append(a)
	var st: StoryStage = _build_stage(str(a["world"]))["stage"]
	st.apply({"t0": float(a["t0"]), "action": str(a["action"]), "args": a["args"], "bar": 0.0, "block": "run", "source": "run"})


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
	if int(ev["block"]) == 3 and not _route_buttons.is_empty():
		_sync_route_buttons()  # the route lock has fallen: routes with another chart pack grey out
	var t := float(ev["t"]) + 0.2
	if bool(ev["passed"]):
		if int(ev["block"]) < 3:
			pad_view.show_status("Nice: the mix moves on", Color(0.7, 1.0, 0.8), float(Time.get_ticks_msec()) / 1000.0)
	else:
		hud.caption("HOLDING THE MIX: HAVE ANOTHER GO", "bad", t, 2.2)
		pad_view.show_status("Missed it: same cues again", Color(1.0, 0.75, 0.55), float(Time.get_ticks_msec()) / 1000.0)


func _end_fade(_t: float, seconds: float) -> void:
	var tw := create_tween()
	tw.tween_interval(maxf(_t - hud.now_t, 0.0))
	tw.tween_property(hud, "fade", 1.0, maxf(seconds, 0.2))


# --- routes ---------------------------------------------------------------------------------------------------------------

func _open_routes(ev: Dictionary) -> void:
	if hotspots != null:  # the hotspot window: the world is the menu, nothing to build
		if audio != null:
			for o in ev["options"]:
				audio.preload_pack(str(data.nodes[str(o["to"])]["audio"]))
		hud.caption("RISER" if str(ev["effect"]) == "riser" else "FALL", "info", float(ev["t"]), 2.0)
		return
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
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART  # a long room name or label wraps inside the button
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
	_exits.fade_from = float(ev["t"])
	_exits.visible = true
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
		b.text = "%s  %s%s\n%s" % [ARROW_GLYPH.get(dir, "?"), data.route_title(engine.node_id, to), tag, str(b.get_meta("label"))]
		b.modulate = Color(1.0, 0.95, 0.6) if chosen else Color(0.85, 0.88, 1.0, 0.9)
		b.disabled = not engine.route_allowed(to)  # after beat 60.5 only routes that play the chart already charted
	_exits.items = exit_items()
	hud.route_hint = "Tap an arrow to choose where to go (arrow keys work too). Changes count until the downbeat."


func _close_routes(_ev: Dictionary) -> void:
	if hotspots != null:
		return
	_route_box.visible = false
	_exits.visible = false
	_exits.items = []
	hud.route_hint = ""
	for c in _route_box.get_children():
		c.queue_free()
	_route_buttons.clear()


func _unhandled_key_input(event: InputEvent) -> void:
	if hotspots != null and event is InputEventKey and event.pressed and not event.echo and trial_state == "":
		var kc := (event as InputEventKey).keycode  # desktop: 1 to 4 pick the hotspots on show in order, the arrow keys the hotspot that leads that way
		if kc >= KEY_1 and kc <= KEY_4:
			var shown := hotspots.shown(engine.block, engine.window_open)
			if kc - KEY_1 < shown.size():
				hotspot_select(str(shown[kc - KEY_1]["id"]))
			return
		var d := "left" if kc == KEY_LEFT else "right" if kc == KEY_RIGHT else "up" if kc == KEY_UP else ""
		if d != "":
			for o in engine.options():
				if str(o["dir"]) == d:
					for h in hotspots.shown(engine.block, engine.window_open):
						if str(h["on_success"].get("route", "")) == str(o["to"]):
							hotspot_select(str(h["id"]))
		return
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


# --- hotspots -------------------------------------------------------------------------------------------------------------

## What the hotspot view draws and the taps hit: [{hotspot, state, t_state}] for the hotspots on show now, plus the one that has just committed (it stays for its flash).
func hotspot_items() -> Array:
	var out: Array = []
	if hotspots == null or trial_state != "" or engine == null:
		return out
	for h in hotspots.shown(engine.block, engine.window_open):
		var id := str(h["id"])
		var sel := id == hotspots.selected
		out.append({"hotspot": h, "state": "selected" if sel else "available", "t_state": float(_sel_t.get(id, 0.0)) if sel else 0.0})
	if not _commit_view.is_empty():
		if hud.now_t - float(_commit_view["t"]) < 2.5 * engine.beat_s:
			out.append({"hotspot": _commit_view["hotspot"], "state": "committed", "t_state": float(_commit_view["t"])})
		else:
			_commit_view = {}
	return out


## The player (or the bot) touches a hotspot by id. Allowed while it is on show and nothing has committed; the selection can be changed until the commit. Returns whether it was selected.
func hotspot_select(id: String) -> bool:
	if hotspots == null or _ended or trial_state != "":
		return false
	var ok := hotspots.select(id, engine.block, engine.window_open)
	if ok:
		_sel_t[id] = hud.now_t
		hotspot_log.append({"kind": "select", "t": hud.now_t, "hotspot": id, "block": engine.block, "phase": engine.phase_n})
	return ok


## A touch or click at `pos` (viewport coordinates). Only the stage area counts (the pads are below it and never reach this), and never a point over a pad. The nearest hotspot within its projected
## radius, at least min_px wide, is selected. Returns the id selected ("" for a tap on nothing).
func hotspot_tap(pos: Vector2) -> String:
	if hotspots == null or _ended or trial_state != "" or _stage_host == null or not stages.has(active_world):
		return ""
	var rect := Rect2(_stage_host.global_position, _stage_host.size)
	if not rect.has_point(pos):
		return ""
	for p in pad_view.button_rects():
		if (pad_view.button_rects()[p] as Rect2).has_point(pos):
			return ""
	var st: StoryStage = stages[active_world]["stage"]
	var pose := _exit_pose()
	if st.map == null or pose.is_empty():
		return ""
	var items := hotspot_items().filter(func(e: Dictionary) -> bool: return str(e["state"]) != "committed")
	var id := HotspotView.hit(HotspotView.layout(items, st.map, st.crowds, pose, rect.size), pos - rect.position)
	if id == "":
		hotspot_log.append({"kind": "tap_miss", "t": hud.now_t, "pos": pos})
		return ""
	return id if hotspot_select(id) else ""


func _input(event: InputEvent) -> void:
	if hotspots == null or engine == null or clock == null or _ended or clock.state == SongClock.State.PAUSED or _pause_panel.visible or _settings_panel != null:
		return
	var pos := Vector2.ZERO
	if event is InputEventScreenTouch and (event as InputEventScreenTouch).pressed:
		pos = (event as InputEventScreenTouch).position
	elif event is InputEventMouseButton and (event as InputEventMouseButton).pressed and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		pos = (event as InputEventMouseButton).position
	else:
		return
	var now := Time.get_ticks_msec()  # a touch also arrives as an emulated click (or the reverse): one tap is one selection
	if now - _last_tap_ms < 80 and pos.distance_to(_last_tap_pos) < 3.0:
		return
	_last_tap_ms = now
	_last_tap_pos = pos
	hotspot_tap(pos)


## The wizard is a character hotspot anchored on a thing of the map (wizard_floor, wizard_chill): his picture is in the room, so the old overlay is never shown with hotspots.
func _place_wizard(_t: float) -> void:
	_gate_wizard.visible = false


func _on_hotspot_commit(ev: Dictionary) -> void:
	var out: Dictionary = ev["outcome"]
	var t := float(ev["t"])
	hotspot_log.append({"kind": "commit", "t": t, "hotspot": str(out["hotspot"]), "success": bool(out["success"]), "route": str(out["route"]), "window": str(out["window"]), "tapped": bool(out["tapped"]),
		"energy": float(ev["energy"]), "phase": int(ev["phase"]), "node": str(ev["node"]), "continued": bool(out["continued"]), "flags": out["flags_set"]})
	_commit_view = {"id": str(out["hotspot"]), "t": t, "hotspot": hotspots.get_hotspot(str(out["hotspot"]))}
	if hotspots.persist_dirty:
		Session.run_progress.save()
		hotspots.persist_dirty = false
	if not (out["cinematic"] as Dictionary).is_empty():
		_hotspot_cinematic(out, t)
	if str(out["window"]) == "early" and bool(out["success"]) and HotspotContract.is_trial_route(str(out["route"])):
		trial_launcher.call()  # the wizard's way in: the walk to the hatch is scheduled by arm_trial on the next cue-free guard


## An outcome's cinematic is rail actions (RunJourney.hotspot_actions): steps of role, look and move. The move replaces the door walk only when the scene simply continues by its default exit;
## when the outcome names a route the door walk toward it is the camera's move.
func _hotspot_cinematic(out: Dictionary, t: float) -> void:
	var spec: Dictionary = out["cinematic"]
	var move_ok := bool(out["continued"]) or str(out["window"]) == "early"
	var steps_move := false
	for st in spec.get("steps", []):
		steps_move = steps_move or (st.has("move") and st.has("to"))
	for a in journey.hotspot_actions(spec, t, engine, _look_by, move_ok):
		_journey_apply(a)
	if move_ok and steps_move and str(out["window"]) == "final":
		_door_phase = engine.phase_n  # the cinematic is the move: no door walk is latched for this phase


## The turn (degrees, relative to the camera's facing now) toward an actor, thing or waypoint of the scene's map; NAN when it cannot be placed.
func _look_by(target: String) -> float:
	if not stages.has(active_world):
		return NAN
	var st: StoryStage = stages[active_world]["stage"]
	var pose := _exit_pose()
	if st.map == null or pose.is_empty():
		return NAN
	for key in ["actor", "thing", "waypoint"]:
		var r := HotspotView.resolve({key: target}, st.map, st.crowds)
		if bool(r["ok"]):
			var p: Vector3 = r["pos"]
			var cam: Vector3 = pose["cam"]
			return wrapf(rad_to_deg(atan2(-(p.x - cam.x), -(p.z - cam.z))) - float(pose["yaw"]), -180.0, 180.0)
	return NAN


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
	live_engine().press(button, clock.judge_time(), touch_id)


func _on_button_released(button: int, touch_id: int) -> void:
	if _ended:
		return
	live_engine().release(button, clock.judge_time(), touch_id)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") and trial_state == "in" and trial.active and clock != null and clock.state == SongClock.State.PLAYING:
		trial.request_leave()  # the system back key leaves the dungeon by the same walk back up the hatch
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_cancel"):
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
	Session.run_start_node = _run_world_of(engine.node_id)  # a restart begins at the world's entry scene (its id is the world's id)
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


# --- the Bassment: the seamless entry and exit -----------------------------------------------------------------------------------

func live_engine() -> Object:
	return trial.engine if trial_state == "in" and trial != null and trial.engine != null else engine


func on_judge(ev: Dictionary) -> void:
	_on_judge_event(ev, float(Time.get_ticks_msec()) / 1000.0)


func hide_run_stage() -> void:
	if stages.has(active_world):
		var st: StoryStage = stages[active_world]["stage"]
		st.visible = false
		st.process_mode = Node.PROCESS_MODE_DISABLED


func _build_hatch_early() -> bool:
	if str(data.nodes[engine.node_id].get("trial_gate", "")) == "":
		return false
	trial.build_zone(tdata.zone_of_passage(tdata.start))
	return true


## The wizard's "Enter the Trial" was chosen. The walk to the hatch is scheduled on the next cue-free guard (3 beats before a block ends); the dungeon's pack is loaded on a thread while
## the current block plays; the dungeon takes the pads on the guard after that and the passage frame closes on the hatch and opens in the Service Hatch on the downbeat that follows.
## Returns false when the phase is too far on (the last two blocks are left to the run's own route choice).
func arm_trial() -> bool:
	if trial_state != "" or str(data.nodes[engine.node_id].get("trial_gate", "")) == "":
		return false
	var t := hud.now_t
	var beat := engine.phase_beat_at(t)
	var k := 0
	while k < 3 and engine.t_of(float(k * 16) + 12.75) < t + 0.05:
		k += 1
	if k > 2:
		return false
	trial_state = "armed"
	_trial_g1 = engine.t_of(float(k * 16) + 12.75)
	_trial_g2 = _trial_g1 + 16.0 * engine.beat_s
	trial_entry_t = _trial_g2 + 3.25 * engine.beat_s
	_gate.visible = false
	if audio != null:
		audio.preload_pack(str(tdata.raw["music"]["audio"]))
	trial.build_zone(tdata.zone_of_passage(tdata.start))
	trial_log.append({"kind": "armed", "t": t, "g1": _trial_g1, "g2": _trial_g2, "entry": trial_entry_t, "beat": beat})
	return true


func _trial_step(t: float) -> void:
	if trial_state == "" and OS.get_environment("RW_TRIAL_ENTER") == "1" and t > 2.0 * engine.beat_s and _gate.visible:
		arm_trial()  # scripted: the wizard is chosen as soon as the level is under way
	if trial_state != "armed":
		return
	if _trial_g1 >= 0.0 and t >= _trial_g1:
		var bars := maxf((trial_entry_t - _trial_g1) / engine.beat_s / 4.0 - 0.4, 1.0)
		_journey_apply({"world": active_world, "t0": _trial_g1, "action": "player_move", "args": {"to": "hatch", "bars": bars, "style": "walk"}})
		trial_log.append({"kind": "walk", "t": _trial_g1, "bars": bars})
		_trial_g1 = -1.0
	if t >= _trial_g2:
		_handle(engine.update(_trial_g2 + 0.001))
		trial_begin_now(trial_entry_t, -1, false)


func trial_begin_now(entry_t: float, start_passage: int, direct: bool) -> void:
	if not direct:
		_close_routes({})
		hud.visible = false
		_gate.visible = false
	trial_state = "in"
	if trial.bot == "":
		trial.bot = str(_bot.get("policy", "")) if str(_bot.get("policy", "")) in ["perfect", "none"] else ""
	trial.begin(entry_t, start_passage, direct)
	engine.phase_n += 1
	trial_log.append({"kind": "entered", "t": hud.now_t, "entry": entry_t})


## Left by a death, the victory or the back key: on the downbeat `t_swap` the frame opens on the Warehouse at the hatch, its pack re-enters and the run begins a fresh phase.
func trial_leave(t_swap: float, reason: String) -> void:
	trial.deactivate()
	trial_state = ""
	var node := "warehouse" if data.nodes.has("warehouse") else engine.node_id
	var w := _world_of(node)
	_show_world(w)
	journey.skip_arrival = true  # the walk below puts the camera back on the floor: no door walk for the resumed scene
	engine.resume(node, t_swap)
	pad_view.setup(engine.level, clock)
	pad_view.holding_fn = engine.judge.hold_progress
	pad_view.progress_fn = engine.progress_at
	note_lane.setup(engine.level, clock, pad_view)
	note_lane.state_fn = engine.judge.cue_state
	hud.visible = true
	_passage_swap = t_swap
	_last_guard_key = -1
	_handle(engine.update(t_swap))
	_journey_apply({"world": w, "t0": t_swap, "action": "player_move", "args": {"to": str(stages[w]["waypoint"]), "bars": 2.0, "style": "walk"}})
	trial_log.append({"kind": "left", "t": t_swap, "reason": reason})
	print("TRIAL left (%s) on the downbeat t=%.3f; the run resumes at phase %d, energy %.1f" % [reason, t_swap, engine.phase_n, engine.energy])
	if OS.get_environment("RW_STORY_QUIT") == "1" and OS.get_environment("RW_TRIAL_LEAVE_QUIT") == "1":
		get_tree().quit()
