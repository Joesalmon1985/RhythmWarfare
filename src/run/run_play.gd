extends Control
## The continuous story run: one scene hosts the whole run. RunEngine decides the cues, the mix and the route from the song clock; RunAudio plays
## it; the existing StoryStage / StoryPadView / StoryNoteLane / StoryDeck draw it. A world transition swaps which prebuilt StoryStage is shown on
## the downbeat; the clock, the beat grid, the judge and the crowd energy never restart.
##
## Scripted play for tests and recordings: RW_RUN_BOT=perfect|none|accuracy:<f>|blocks:<10110...>, RW_RUN_ROUTES=left,right,... (a direction per
## phase: the bot taps the hotspot that leads there), RW_RUN_TAPS=scripted|none|changed|failure|early|mind (the tap policy: the scripted taps, no taps at all (the default exits), a decoy tapped first and
## then the scripted one, the scripted taps with the last block of every phase missed; early: the scripted choice touched at beat 2 of the scene and held; mind: early, then a decoy at beat 40
## and the scripted choice again at beat 58 of the departure lap), RW_RUN_VIRTUAL=1 (no audio, a stepped clock), RW_RUN_UNTIL_PHASE=<n>, RW_RUN_START=<node id>.
##
## The route window is the hotspot window (docs/CONTINUOUS_RUN.md "Hotspots"): the player touches the world (HotspotView, RunHotspots); the last block's result picks the outcome.
##
## A PATH (content/paths/<id>, RW_RUN_PATH=<id> starts one, RW_RUN_START names its scene) is a sister run at its own tempo with its own RunData, RunEngine, RunHotspots and RunJourney; the scene swaps them
## on a downbeat (the tempo handoff, `_path_swap`): the clock stream, the engine, the pads' level, the stages' tempo. RW_RUN_PORTAL=<hotspot id> makes the bot touch a portal in the final window,
## RW_RUN_FLAGS=a,b sets world-state flags after the run starts (a portal's flags), RW_PATH_REMAP=gospel=stub plays the stub path through the gospel portal.

const COUNTDOWN_S := 2.0
const RESUME_COUNTDOWN_S := 3.0

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
var hotspots: RunHotspots  # the scene's hotspots: the world is the menu
var hotspot_log: Array = []  # [{kind: select | tap_miss | commit, t, ...}] for the tests and the walks
var input_log: Array = []  # [{t, area: hud | strip | stage, owner (ContractShapes.tap_owner), target}] every tap the dispatcher routed (CONTRACTS.md 5, H5.5)
var world_regions: Dictionary = {}  # the scene's four screen regions when it has them (the bedsit; {} none): {top|bottom|left|right: [x, y, w, h] fractions of the stage area}
signal world_region_tapped(region: String, t: float)  # a tap in one of `world_regions` (the bedsit's turn, stay and leave)
var tap_policy := "scripted"
var _sel_t: Dictionary = {}  # hotspot id -> song time it was selected
var _refused: Dictionary = {}  # hotspot id -> {t, reason, hotspot}: a choice that did not take a touch recoils for HotspotView.REFUSE_S
var _react_t: Dictionary = {}  # reactive object id -> song time it was last touched (it reacts for HotspotView.REACT_S)
const CLAIM_TIP := -12.0  # degrees the camera tips down while a claim stands
var _claim_id := ""  # the hotspot whose on_select walk has the camera now ("" none): the rail stands still meanwhile
var _claim_to := ""  # the waypoint that walk goes to
var _commit_view: Dictionary = {}  # {id, t, hotspot}: the committed hotspot stays drawn for a moment (the flash)
var _last_tap_ms := -1000
var _last_tap_pos := Vector2(-9999, -9999)
var _bot_decoy_done := -1
var _gate: Control

var _stage_host: Control
var _pause_btn: Button
var _dim: ColorRect
var _pause_panel: PanelContainer
var _settings_panel: Control
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
var piece_log: Array = []  # [{t, on, off}] every set-piece switch (the tests and the walks read it)
var build_log: Array = []  # [{world, ms}] how long each world stage took to build (the main thread stalls that long)
var lap_log: Array = []  # [{phase, lap, laps, node, t, stage}] one per lap after the first (a scene that plays several laps)
var phase_log: Array = []  # [{phase, node, t}] for scripted checks
var journey: RunJourney  # the player's rails (pure logic; the scene only hands its actions to the stages)
var journey_log: Array = []  # every journey action given to a stage: {world, t0, action, args}
var _passage_swap := -1.0  # song time of the downbeat a world swap walks through (-1: none under way)
var _door_phase := -1  # the phase whose door walk (a path inside the world) was started
var _run_world := ""  # the run world of the phase before the current one (a change closes the passage frame)
var _passage: RunPassageView
var trial: TrialScene  # the Bassment, hosted here: the same scene, clock, pads and audio (docs/TRIAL_OPENING.md)
var tdata: TrialData
var trial_state := ""  # "" | "armed" (the wizard was chosen: the walk to the hatch is scheduled) | "in" (the dungeon owns the pads) | "leaving"
var trial_entry_t := -1.0  # the downbeat the dungeon is entered on
var _trial_g1 := -1.0  # the cue-free guard the walk to the hatch starts on
var _trial_g2 := -1.0  # the guard the dungeon takes the pads on
var _trial_direct := false
var _stage_hidden := ""
var rave_host := SpaceRaveHost.new()  # the Space rave's bass lock and stage change (src/bedsit/space_rave_host.gd; inert outside its scenes)
var minigames: MinigameController  # minigames: the activity that owns the scene while the player is seated at a table (docs/BLACKJACK_INTEGRATION.md section 5)
var _mg: RunMinigameHost
var race_host: RaceStageHost  # the street race's stage swap (src/minigames/race/race_stage_host.gd; inert outside a race)
var card_table: RunCardTable  # the day room's card table in the room: its players follow the table's hotspot (docs/BLACKJACK_INTEGRATION.md, "The table in the room")
var trial_log: Array = []  # [{kind, t, ...}] the entry and exit, for the transition tests and recordings
var run_path := ""  # the path being played ("" = the main run); `data`, `engine`, `hotspots` and `journey` are always the active run's
var main_data: RunData  # the main run's data while a path is played (null when the run started inside a path and has not been back yet)
var path_log: Array = []  # [{kind: enter | leave | failed, t, path, bpm_before, bpm_after, beat_s_before, beat_s_after, ...}] the tempo handoffs, for tests and recordings
var path_leave_requested := false
var _handoff: Dictionary = {}
var _leave_btn: Button
var _bot_portal_done := -1
var _path_cache: Dictionary = {}  # path id -> RunData read ahead (the portals' paths)
var cast_log: Array = []  # [{t, beat, actor, act, face, look_at, source, applied}] every cast line handed to the crowd (the acting contract, docs/THREE_PATHS_AND_FACES_PLAN.md 2.3b), for tests and walks
var acting_log: Array = []  # [{t, hotspot, actor, success, acts}] every outcome chain handed to the crowd (2.3a)
var playtest: Dictionary = {}  # the options of a start from the Debug / Playtest scene list ({} otherwise): see PlaytestMode, docs/DEBUG_MODE.md
var playtest_overlay: PlaytestOverlay  # the playtest overlay; null unless PlaytestMode.on()
var _pause_note: LineEdit
var track_log: Array = []  # the track scenes played (see _on_track_event)
var director: TransitionDirector  # the transition seam (src/transition/transition_director.gd): every engine event reaches it, it decides the music of each scene change; port() for the narrative side
var _track_stay_phase := -1  # the phase whose open window is not the last lap's (route_window.last false): touching nothing stays, so no door shows the way out


func _ready() -> void:
	theme = UiStyle.theme()
	var want_path := OS.get_environment("RW_RUN_PATH") if OS.get_environment("RW_RUN_PATH") != "" else Session.run_start_path
	if want_path == "" and BedsitNav.enabled():  # RW_BEDSIT=1 starts the new opening (content/paths/bedsit, docs/bedsit/LAUNCH.md); off by default, RW_RUN_PATH still wins
		want_path = BedsitNav.PATH_ID
	Session.run_start_path = ""
	playtest = PlaytestMode.consume_launch()
	data = RunData.load_path(want_path) if want_path != "" else RunData.load_default()
	if not data.errors.is_empty():
		_fatal("The run data is invalid:\n" + "\n".join(PackedStringArray(data.errors)))
		return
	run_path = data.path_id
	main_data = data if run_path == "" else null
	for sp in data.skipped_portals:
		print("RUN portal %s (scene %s) is hidden: the path '%s' has no run.json yet" % [sp["hotspot"], sp["scene"], sp["path"]])
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
	journey.face_fn = _window_face
	tap_policy = OS.get_environment("RW_RUN_TAPS") if OS.has_environment("RW_RUN_TAPS") and OS.get_environment("RW_RUN_TAPS") != "" else "scripted"
	hotspots = RunHotspots.new(data, Session.run_progress.run_flags, Session.run_progress.flags)
	hotspots.preselect = bool((data.cfg.get("choice", {}) as Dictionary).get("preselect", false)) or OS.get_environment("RW_CHOICE_PRESELECT") == "1"  # (an owner decision, off: touch only in the window; the env turns it on for a strip)
	engine.hotspots = hotspots
	director = TransitionDirector.new()
	minigames = MinigameController.new(engine, Session.run_progress.get("wallet"), Session.run_progress.run_seed())  # minigames: registry from content/minigames
	minigames.load_registry()
	_mg = RunMinigameHost.new(self)
	race_host = RaceStageHost.new(self)
	if not virtual_mode:  # (the audio before the first scene: a track scene's stems are decoded now, before the countdown, and the engine asks the audio whether a track is ready)
		audio = RunAudio.new()
		add_child(audio)
		audio.configure(data)
		_wire_track_audio()
		var prep_ms := audio.track.prepare(data, start)
		if prep_ms > 0.0:
			print("RUN track stems of the first scene decoded in %.0f ms (before the countdown)" % prep_ms)
	_wire_director()
	engine.begin(start)
	if float(playtest.get("energy", -1.0)) >= 0.0:  # the scene list's start-energy option
		engine.energy = float(playtest["energy"])
		hotspots.energy = engine.energy
	proxy = StoryRun.new()
	proxy.level = engine.level
	proxy.crowd = CrowdController.new()
	if virtual_mode:
		clock = SongClock.new(null)
	else:
		clock = SongClock.new(audio)
		clock.calibration_ms = Session.calibration_ms
	_preload_portals()
	if audio != null:
		audio.track.warm([data] + _path_cache.values())  # (every scene plan made on a worker thread: the engine never parses a track.json on a frame)
	_build_layout(start)
	_setup_bot()
	if OS.get_environment("RW_RUN_CLEAN") == "1":  # screenshot aid: no falling notes and no HUD over the picture (tools/run/capture.sh --acting)
		note_lane.visible = false
		hud.visible = false
	Session.run_progress.run_started()
	if bool(playtest.get("give_flags", false)):  # the scene list: the flags this scene's hotspots need, so all of them are on offer
		var need: Array = PlaytestCatalog.scene_info(data, start).get("visual", {}).get("flags_needed", [])
		for f in need:
			if str(f).begins_with("keep:"):
				Session.run_progress.flags[str(f)] = true
			else:
				hotspots.run_flags[str(f)] = true
	if OS.get_environment("RW_RUN_FLAGS") != "":  # screenshot aid (tools/run/capture.sh --acting): world-state flags to start the run with, so a hotspot that needs one is on show
		for f in OS.get_environment("RW_RUN_FLAGS").split(",", false):
			hotspots.run_flags[f] = true
	_setup_router(start)
	if _trial_direct:  # a launch straight into the dungeon: the run's first phase is never heard
		var sp := int(OS.get_environment("RW_TRIAL_START")) if OS.get_environment("RW_TRIAL_START") != "" else -1
		trial.bot = OS.get_environment("RW_TRIAL_BOT") if OS.get_environment("RW_TRIAL_BOT") != "" else str(_bot.get("policy", ""))
		trial_state = "in"
		trial_begin_now(0.0, sp, true)
		var ci: float = trial.engine.count_in_s()
		_vt = -ci
		hud.fade_out()
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


## TRACK SCENES: the engine asks the track audio whether a scene's stems are ready (else it is an ordinary scene this visit), and the mute rule reads the engine's cues. Again after every hand-off.
func _wire_track_audio() -> void:
	if audio == null or audio.track == null or engine == null:
		return
	engine.track_gate = director.track_gate if director != null else audio.track.is_ready  # (the director answers for the destination it locked, else asks the track audio as before)
	audio.track.notes_fn = func() -> Array: return engine.level.notes if engine != null and engine.level != null else []


## THE TRANSITION SEAM (stage M1.6, docs/parallel-development/MUSIC_TRANSITIONS.md section 12): the director sits on the engine (its lock point and track gate), hears every engine event
## (_handle), is stepped every frame (_advance) and learns from the audio when the outgoing music is silent. Again after every hand-off (a new engine). Nothing here changes what the run does.
func _wire_director() -> void:
	if director == null or engine == null:
		return
	director.attach(engine, data)
	var dir_hook: Callable = engine.lock_hook
	engine.lock_hook = func(info: Dictionary) -> Variant: return _on_lock_point(info, dir_hook)  # (the hub's Bassment entrance is armed here, before the director's say: N2.2, ruling 20)
	director.path_data_fn = _run_data_of
	if audio != null and audio.track != null and not director.audio_reports_silence:
		director.ready_fn = audio.track.is_ready
		director.load_fn = func(d: RunData, node: String) -> String: return audio.track.request_scene(d, node, true)
		director.release_fn = audio.track.release_pins
		director.recipe_fn = audio.prepare_transition
		audio.outgoing_silent.connect(director.on_outgoing_silent)
		director.audio_reports_silence = true


## The TransitionPort of this run (the narrative side's only way to ask for a scene change).
func port() -> TransitionPort:
	return director


## The run data a destination names, for the director (path_data_fn): "main" the main run's (read now when the run began inside a path), a path id that path's (read now when no portal of
## this run named it). Reading here is the fallback; the portals' paths are read before the countdown (_preload_portals).
func _run_data_of(key: String) -> Variant:
	if key == "main":
		if main_data != null:
			return main_data
		if _main_cache == null:
			_main_cache = RunData.load_default()
		return _main_cache
	if not _path_cache.has(key) and NarrativeGraph.SHIPPED_PATHS.has(key) and RunData.path_exists(key):
		_path_cache[key] = RunData.load_path(key)
	return _path_cache.get(key, null)


## The paths the Warehouse's portals lead to (those that exist): their data is read once, before the countdown (not on the downbeat of the handoff), and their start pack is loaded ahead on a thread.
func _preload_portals() -> void:
	if run_path != "":
		return
	for sid in data.node_order:
		for h in data.hotspots_of(sid):
			var r := str((h["on_success"] as Dictionary).get("route", ""))
			var pid := HotspotContract.path_of(r)
			if pid != "" and not _path_cache.has(pid):
				var pd := RunData.load_path(pid)
				_path_cache[pid] = pd
				if pd.errors.is_empty() and audio != null:
					audio.preload_pack(str(pd.nodes[pd.start_node()]["audio"]), pd)


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


## The story data file of an art world (a map): a chapter's entry of content/story/chapters.json, else the `story` path a world of a path's run.json names (a path's maps are not chapters:
## they never appear in the Story chapters menu). `from` is the path data to look in first (a portal's path read ahead).
func _story_entry(world: String, from: RunData = null) -> Dictionary:
	var entry := StoryChapters.load_default().chapter(world)
	if not entry.is_empty():
		return entry
	var sources: Array = [data]
	if from != null:
		sources.push_front(from)
	sources.append_array(_path_cache.values())
	if main_data != null:
		sources.append(main_data)
	for rd in sources:
		for wid in (rd as RunData).worlds:
			var wd: Dictionary = rd.worlds[wid]
			if str(wd.get("map", "")) == world and str(wd.get("story", "")) != "":
				return {"id": world, "data": str(wd["story"])}
	return {}


func _build_stage(world: String, from: RunData = null) -> Dictionary:
	if stages.has(world):
		return stages[world]
	var t_build := Time.get_ticks_usec()
	var entry := _story_entry(world, from)
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
		if card_table == null:
			card_table = RunCardTable.new()
			card_table.beat_s = engine.beat_s
			card_table.reduced = Session.reduced_effects
			card_table.high_contrast = Session.high_contrast
		card_table.attach(st)
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
		hv.choice_fn = choice_state  # the current choice staged in the world from the scene's first beat (docs/CHOICE_CLARITY.md)
		hv.reactives_fn = reactive_items  # the reactive objects' reactions to a tap (INTERACTION_DESIGN.md 2.5)
		hv.pose_fn = _exit_pose
		hv.now_fn = func() -> float: return hud.now_t
		hv.reduced = Session.reduced_effects
		hv.high_contrast = Session.high_contrast
		hv.glow_tex = assets.sprite("glow").get("tex", null)
		var warm: Array = st.palettes.get("warm", [])
		if not warm.is_empty():
			hv.tint = HotspotView.light_tint(warm[0] as Color)
		hv.set_anchors_preset(Control.PRESET_FULL_RECT)
		var layer := st.lowres.add_overlay(hv, "Hotspots")
		layer.layer = 2
		rec["hotspot_view"] = hv
	stages[world] = rec
	var now := Time.get_ticks_usec()
	build_log.append({"world": world, "phase": engine.phase_n if engine != null else 0, "node": engine.node_id if engine != null else "", "ms": snappedf(float(now - t_build) / 1000.0, 0.1), "parts_ms": {"data": snappedf(float(t_art - t_build) / 1000.0, 1.0), "art": snappedf(float(t_stage - t_art) / 1000.0, 1.0),
		"stage": snappedf(float(t_world - t_stage) / 1000.0, 1.0), "world": snappedf(float(t_deck - t_world) / 1000.0, 1.0), "deck": snappedf(float(now - t_deck) / 1000.0, 1.0)}})
	return rec


## Decodes the people sheets of the worlds this level can lead to on worker threads (the stage build then only uploads them, see StoryPeople.prewarm).
func _prewarm_routes(node_id: String) -> void:
	if virtual_mode:
		return
	for e in data.nodes[node_id]["next"]:
		if not data.nodes.has(str(e["to"])):
			continue  # (an ending's way back, or a portal: no scene of this run)
		var w := _world_of(str(e["to"]))
		if stages.has(w) or _prewarmed.has(w):
			continue
		_prewarmed[w] = true
		var entry := _story_entry(w)
		var sd: StoryData = StoryData.load_file(str(entry["data"]))["data"]
		StoryPeople.prewarm(StoryAssets.load_art(sd.art))
	for pw in _portal_worlds(node_id):  # a portal's path opens on its own art world: its sheets are decoded ahead too
		if stages.has(pw[0]) or _prewarmed.has(pw[0]):
			continue
		_prewarmed[pw[0]] = true
		var pentry := _story_entry(pw[0], pw[1])
		if not pentry.is_empty():
			var psd: StoryData = StoryData.load_file(str(pentry["data"]))["data"]
			StoryPeople.prewarm(StoryAssets.load_art(psd.art))


## The art worlds the path portals of a scene open on: [[map, the path's RunData], ...] (only paths that loaded; a portal hidden for want of data is not here).
func _portal_worlds(node_id: String) -> Array:
	var out: Array = []
	if run_path != "" or not data.nodes.has(node_id):
		return out
	for h in data.hotspots_of(node_id):
		var pid := HotspotContract.path_of(str((h["on_success"] as Dictionary).get("route", "")))
		if pid == "" or not _path_cache.has(pid):
			continue
		var pd: RunData = _path_cache[pid]
		if pd.errors.is_empty() and pd.nodes.has(pd.start_node()):
			out.append([str(pd.nodes[pd.start_node()]["map"]), pd])
	return out


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
	pad_view.show_crowd_label = DevText.on()
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
	trial = TrialScene.new()
	trial.name = "Trial"
	add_child(trial)
	trial.setup(self, tdata, data)
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
	if PlaytestMode.on():  # debug / playtest only: the identity panel and the feedback buttons (docs/DEBUG_MODE.md); regular play has no such node
		playtest_overlay = PlaytestOverlay.new()
		add_child(playtest_overlay)
		playtest_overlay.setup(self)
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
	var items: Array = [["Resume", _resume], ["Restart this level", _retry], ["Leave this path", _leave_path], ["Settings", _open_settings], ["Quit to home", _quit]]
	var holder: Container = pv
	if playtest_overlay != null:  # debug: a two-column panel with the way back to the list and a note field, short enough for a phone held sideways
		items.insert(1, ["Back to scene list", _playtest_back])
		var grid := GridContainer.new()
		grid.columns = 2
		grid.add_theme_constant_override("h_separation", 10)
		grid.add_theme_constant_override("v_separation", 8)
		pv.add_child(grid)
		holder = grid
	for item in items:
		var pb := UiStyle.button(item[0], item[1], 300 if playtest_overlay != null else 360, 52 if playtest_overlay != null else 60)
		holder.add_child(pb)
		if item[0] == "Leave this path":
			_leave_btn = pb
			pb.visible = false
	if playtest_overlay != null:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		pv.add_child(row)
		_pause_note = LineEdit.new()
		_pause_note.placeholder_text = "Type a note about this scene"
		_pause_note.custom_minimum_size = Vector2(430, 48)
		_pause_note.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(_pause_note)
		row.add_child(UiStyle.button("Save note", _playtest_save_note, 150, 48))


# --- the wizard and the Trial ----------------------------------------------------------------------------------------------

## A wizard waits in the Warehouse as a character hotspot (his picture is a thing of the map, no overlay and no text). Touching it leaves the run for the Deathtrap Dungeon opening
## (res://src/trial/trial_play.tscn); ignoring it changes nothing: the run, its pads and its routes go on as before.
func _build_gate() -> void:
	_gate = Control.new()
	_gate.name = "TrialGate"
	_gate.set_anchors_preset(Control.PRESET_FULL_RECT)
	_gate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_gate.visible = false
	add_child(_gate)
	trial_launcher = func() -> void: arm_trial()


# --- scripted player ------------------------------------------------------------------------------------------------------

func _setup_bot() -> void:
	var pol := OS.get_environment("RW_RUN_BOT")
	if pol == "" and bool(playtest.get("autoplay", false)):  # the scene list's autoplay option: the same perfect bot the tests use
		pol = "perfect"
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
			_bot_pressed[i] = _bot_wants(n, i) and not engine.judge.is_withdrawn(i) and not _mg.owns_strip()  # (a cue withdrawn while an activity owned the strip is no one's to play)
			if _bot_pressed[i]:
				engine.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
				pad_view.button_down[int(n["pad"])] = true
		if _bot_pressed.get(i, false) and not _bot_released.has(i):
			var end_t := float(n["end_time"]) if n["type"] == "hold" else float(n["time"]) + 0.08
			if end_t <= t:
				_bot_released[i] = true
				engine.release(int(n["pad"]), end_t, int(n["pad"]))
				pad_view.button_down[int(n["pad"])] = false
	_scripted_select(t)
	_bot_taps(t)


## The scripted taps (RW_RUN_TAPS): `scripted` taps the hotspot that leads where RW_RUN_ROUTES says (a direction per phase) at beat 52; `none` never taps; `changed` first taps a decoy at beat 50;
## `failure` is `scripted` with the last block missed (see _bot_wants). Taps go through hotspot_select exactly as a finger would (the same availability, the same window).
func _bot_taps(t: float) -> void:
	if tap_policy == "early" or tap_policy == "mind":
		_bot_whole_scene(t)
		return
	if tap_policy == "none" or not engine.window_open:
		return
	if engine.is_track_scene() and engine.lap < engine.laps:  # a track scene's open lap: a tap would leave now. RW_RUN_TRACK_EXIT=first leaves at the first open lap; otherwise (end) the bot plays to the default end
		if OS.get_environment("RW_RUN_TRACK_EXIT") != "first" or engine.lap != engine.doors_from_lap:
			return
	var beat := engine.phase_beat_at(t)
	var portal := OS.get_environment("RW_RUN_PORTAL")
	if portal != "" and run_path == "":  # the bot touches a portal (once per phase, at beat 51) and keeps it
		if hotspots.selected == portal:
			return
		if _bot_portal_done != engine.phase_n and beat > 51.0:
			_bot_portal_done = engine.phase_n
			if hotspot_select(portal):
				return
	var k := engine.scene_index() - 1  # (the routes of a scripted run are one per scene, whatever its laps)
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


## The taps of selection open for the whole scene (INTERACTION_DESIGN.md 2.2, N2.1): `early` touches the scripted choice (RW_RUN_ROUTES; the default exit when none is scripted) at beat 2 of the
## scene's first lap and keeps it; `mind` does the same, then changes its mind twice: a decoy (another choice of the room) at beat 40 of the departure lap, and the scripted choice again at beat 58,
## two and a half beats before the lock. Either way the pick commits once, at the lock, and the run goes where the routes say.
var _bot_scene_steps: Dictionary = {}  # scene index -> whole-scene steps done


func _bot_whole_scene(t: float) -> void:
	var idx := engine.scene_index()
	var done := int(_bot_scene_steps.get(idx, 0))
	var plan: Array = [[1, 2.0, "target"]] if tap_policy == "early" else [[1, 2.0, "target"], [0, 40.0, "decoy"], [0, 58.0, "target"]]  # [lap (1: the first, 0: the departure lap), beat, what]
	if done >= plan.size() or t < 0.0:
		return
	var step: Array = plan[done]
	var lap_ok := engine.lap == 1 if int(step[0]) == 1 else engine.is_departure_lap()
	if not lap_ok or engine.phase_beat_at(t) < float(step[1]):
		return
	_bot_scene_steps[idx] = done + 1
	var on_show := hotspots.shown(engine.block, selection_open())
	var want := _route_for_dir(idx - 1)
	if want == "":
		want = hotspots.default_route()
	var target := ""
	for h in on_show:
		if RunHotspots.window_of(h) == "final" and str((h["on_success"] as Dictionary).get("route", "")) == want:
			target = str(h["id"])
			break
	var pick := target
	if str(step[2]) == "decoy":
		pick = ""
		for h in on_show:
			var r := str((h["on_success"] as Dictionary).get("route", ""))
			if str(h["id"]) != target and RunHotspots.window_of(h) == "final" and not HotspotContract.is_special_route(r) and not h.has("on_select"):
				pick = str(h["id"])
				break
	if pick != "":
		hotspot_select(pick)


## RW_RUN_SELECT=<hotspot id>@<phase beat> (the screenshots): that hotspot is touched once, in the first phase, when its beat comes.
var _select_done := false


var _select_i := 0


func _scripted_select(t: float) -> void:  # (several touches in order: RW_RUN_SELECT=a@50,b@53,a@56, the choice-clarity strips)
	if _select_done or not OS.has_environment("RW_RUN_SELECT") or engine.scene_index() != 1 or engine.lap < engine.laps:  # (the hotspots are on show in the last lap only)
		return
	var specs := OS.get_environment("RW_RUN_SELECT").split(",", false)
	while _select_i < specs.size():
		var spec := specs[_select_i]
		if engine.phase_beat_at(t) < float(spec.get_slice("@", 1)):
			return
		if hotspot_select(spec.get_slice("@", 0)) or engine.phase_beat_at(t) > 62.0:
			_select_i += 1
		else:
			return
	_select_done = true


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
	if director != null:
		director.step(t)
	if playtest_overlay != null:
		playtest_overlay.refresh()
	hud.stage_h = hud.size.y * (1.0 - float(Session.PAD_SIZES[clampi(Session.pad_size, 0, 2)]))  # (the thin route-window bar sits on the bottom edge of the picture, above the pads)
	if trial_state == "in" or trial_state == "leaving":
		if OS.has_environment("RW_TRIAL_LEAVE_AT") and audio_t >= float(OS.get_environment("RW_TRIAL_LEAVE_AT")) and trial.active:
			trial.request_leave()  # scripted: the back key, for the recordings
		trial.update(t, audio_t)
		_trial_route_sync()
		return
	_bot_step(t)
	_trial_step(t)
	if trial_state == "in":
		trial.update(t, audio_t)
		_trial_route_sync()
		return
	if trial_state == "armed" and trial_entry_t >= 0.0:
		_handle(engine.update(minf(t, trial_entry_t - 0.001)))
	else:
		_handle(engine.update(t))
	if not playtest.is_empty() and not bool(playtest.get("continue_run", true)) and engine.scene_index() > 1 and not _ended:  # the list's "back to the list when the scene ends"
		_playtest_back()
		return
	minigames.update(t)  # minigames: after the engine, so a block's result reaches it before its own clock moves
	race_host.step(t)  # the race's street stage (before the host walks the camera home)
	_rave_step(t)
	_mg.step(t)
	_card_table_feed(t)
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
	pad_view.banner_text = _banner(t) if DevText.on() else ""
	note_lane.queue_redraw()
	hud.queue_redraw()
	if trial_state == "":
		_prebuild_in_guard(t)
	if _debug_label.visible:
		_debug_label.text = "t=%6.2f phase %d (%s) block %d stage %d energy %.0f rail %s (%s)  fps %d" % [t, engine.phase_n, engine.node_id, engine.block, engine.stage, engine.energy, journey.rail.place() if journey.rail != null else "-", journey.rail.role if journey.rail != null else "-", Engine.get_frames_per_second()] + _track_debug() + _route_debug() + _bedsit_debug()
	if _until_phase > 0 and engine.scene_index() > _until_phase and not _ended:
		_ended = true
		print("RUN reached phase %d at %s, energy %.0f" % [engine.scene_index(), engine.node_id, engine.energy])
		print("RUN stage builds ", JSON.stringify(build_log))
		print("RUN ", frame_stats())
		print("RUN summary ", JSON.stringify(summary()))
		if OS.get_environment("RW_STORY_QUIT") == "1":
			get_tree().quit()


## The F3 line's track part: " track <id> lap k/n entry bar E" in a track scene, "" elsewhere.
func _track_debug() -> String:
	var ti := engine.track_info()
	return "" if ti.is_empty() else "  track %s lap %d/%d entry bar %d %.2f BPM" % [str(ti["track"]), int(ti["lap"]), int(ti["laps"]), int(ti["entry_bar"]), float(ti["bpm"])]


## A world change is a walk through a doorway: from beat 62 of a phase whose chosen route leads to another world the frame closes to a lit door, and it opens on the
## new world after the downbeat. The latch is decided once per phase at beat 62 (a change of mind in the last two beats cuts instead).
## A path inside the world is a plain door walk (no frame, the stage stays): from beat 61 the camera walks to the doorway of the selected route, and on the downbeat on
## through it into the next scene (RunJourney.door_walk). Also latched once per phase.
func _update_passage(t: float, audio_t: float) -> void:
	if path_leave_requested and (engine.window_open or engine.lap < engine.laps) and engine.phase_beat_at(t) >= 64.0 - RunPassage.DOOR_BEATS and engine.force_leave():  # the pause menu's "leave this path": the way back is this phase's route (a lap before the last ends the scene)
		path_leave_requested = false
	if engine.window_open and t >= 0.0 and _door_phase != engine.phase_n and _claim_id == "" and engine.phase_beat_at(t) >= 64.0 - RunPassage.DOOR_BEATS:
		_door_phase = engine.phase_n
		var to0 := engine.selected_route()
		if data.nodes.has(to0) and _run_world_of(to0) == _run_world_of(engine.node_id) and to0 != engine.node_id:
			for a in journey.leave_walk(engine.t_of(64.0 - RunPassage.DOOR_BEATS), to0, engine):
				_journey_apply(a)
		elif data.nodes.has(to0) and to0 != engine.node_id and journey.threshold_of(engine.node_id, to0) != "":  # another world by a threshold (H1.6): walk there, then the frame and the swap
			for a in journey.threshold_walk(engine.t_of(64.0 - RunPassage.DOOR_BEATS), engine.t_of(64.0), journey.threshold_of(engine.node_id, to0)):
				_journey_apply(a)
	if engine.exit_pending() and _passage_swap < 0.0 and engine.phase_beat_at(t) >= 64.0 - RunPassage.CLOSE_BEATS and t >= 0.0:
		var to := engine.selected_route()
		if not data.nodes.has(to) or _run_world_of(to) != _run_world_of(engine.node_id):  # another world, or out of this run (a portal, an ending's way back): the frame closes
			_passage_swap = engine.t_of(64.0)
	if _passage_swap >= 0.0 and audio_t > _passage_swap + RunPassage.OPEN_BEATS * engine.beat_s + 0.5:
		_passage_swap = -1.0
	_passage.set_aperture(RunPassage.aperture(audio_t, _passage_swap, engine.beat_s))


func _exit_pose() -> Dictionary:
	var st: StoryStage = stages[active_world]["stage"]
	if st.player == null:
		return {}
	var pose := st.screen_pose(st.player.pose_at(hud.now_t))  # (a screenshot's RW_STORY_CAM stands the drawn camera elsewhere: the hotspots follow it)
	return {"cam": pose["cam"], "yaw": float(pose["yaw"]) + (0.0 if st.cam_framed() else st.free_look.offset), "pitch": float(pose.get("pitch", 0.0))}


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
		var wid := str(p.get("world", data.nodes[str(p["node"])]["world"] if data.nodes.has(str(p["node"])) else ""))
		if worlds_seen.is_empty() or worlds_seen[worlds_seen.size() - 1] != wid:
			worlds_seen.append(wid)
	return {"nodes": phase_log.map(func(p: Dictionary) -> String: return str(p["node"])), "laps": lap_log.map(func(l: Dictionary) -> String: return str(l["node"])), "worlds_seen": worlds_seen, "rail": rails, "moves": moves, "glances": looks, "strolls": walks, "worlds": stages.keys(),
		"energy": snappedf(engine.energy, 0.1), "reached": Session.run_progress.reached_ids(), "minigames": minigames.log.size(), "tracks": track_log}


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
			if not data.nodes.has(str(opt["to"])):
				continue
			var w := _world_of(str(opt["to"]))
			if not stages.has(w):
				_build_stage(w)
				return
		for pw in _portal_worlds(engine.node_id):  # a path portal in this room: its first world is built here too (one build per guard), never at the handoff behind the closed frame
			if not stages.has(pw[0]):
				_build_stage(pw[0], pw[1])
				return


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
		if str(ev["kind"]) in ["phase_start", "block_result", "lap_start"] and trial_state == "" and not minigames.active() and not (_claim_id != "" and str(ev["kind"]) == "block_result") and not (_mg.holds_rail() and str(ev["kind"]) == "block_result"):  # the journey first: the stage already holds its actions when the scene reacts
			for a in journey.on_event(ev, engine):
				_journey_apply(a)
		if str(ev["kind"]) != "judge" and str(ev["kind"]) != "cues":
			event_log.append(ev)
		if director != null:
			director.on_event(ev)  # (before the audio: the director decides the music of a scene change)
		if audio != null:
			audio.on_event(ev)
		match str(ev["kind"]):
			"judge":
				_on_judge_event(ev["event"], float(Time.get_ticks_msec()) / 1000.0)
				minigames.on_judge(ev["event"], float(ev["t"]))  # minigames: an overlay activity (the race) hears the pads (H4.2)
			"cues":
				pad_view.refresh()
				note_lane.refresh()
			"phase_start":
				_on_phase_start(ev)
			"lap_start":
				_on_lap_start(ev)
			"tempo":
				_on_tempo(ev)
			"track_start", "track_lap", "track_last_lap", "track_extend", "track_end":
				_on_track_event(ev)
			"mix":
				_on_mix(ev)
			"reveal":
				hud.caption("BASS ENTERS", "good", float(ev["t"]))
			"block_result":
				_on_block_result(ev)
				minigames.on_block_result(bool(ev["passed"]), float(ev["t"]))  # minigames
				minigames.on_block(ev)  # minigames: an overlay activity hears the block results (H4.2)
			"route_window":
				if trial_state == "":
					_open_routes(ev)
			"hotspot_commit":
				_on_hotspot_commit(ev)
			"cast":
				_on_cast(ev)
			"path_handoff":
				_handoff = ev
			"route_commit":
				_close_routes(ev)
			"depleted":
				hud.caption("THE CROWD DRIFTS AWAY", "bad", float(ev["t"]), 2.4)
				_end_fade(float(ev["t"]), float(ev["fade_s"]))
			"run_over":
				minigames.on_run_over(float(ev["t"]))  # minigames
				_over_at = float(Time.get_ticks_msec()) / 1000.0 + (0.4 if not virtual_mode else 0.0)
				_ended = true if virtual_mode else _ended
				Session.run_result = {"node": ev["node"], "phases": int(ev.get("scenes", ev["phase"])), "energy": ev["energy"], "reason": "the crowd left", "start": engine.node_id, "path": run_path}
				if virtual_mode:
					Session.run_progress.run_ended(int(ev.get("scenes", ev["phase"])))
					print("RUN over at phase %d (%s)" % [int(ev.get("scenes", ev["phase"])), str(ev["node"])])
					print("RUN summary ", JSON.stringify(summary()))
					if OS.get_environment("RW_STORY_QUIT") == "1":
						get_tree().quit()
	if not _handoff.is_empty():  # the run left this engine's world on a downbeat: the other run takes over (after this batch of events is done)
		var handoff := _handoff
		_handoff = {}
		_path_swap(handoff)


func _on_phase_start(ev: Dictionary) -> void:
	var node: Dictionary = data.nodes[str(ev["node"])]
	var world := str(node["map"])
	var t0 := float(ev["t"])
	_rave_enter(str(ev["node"]), t0)
	phase_log.append({"phase": ev["phase"], "node": ev["node"], "t": t0, "world": str(node["world"]), "path": run_path})
	_sel_t.clear()
	_refused.clear()
	_react_t.clear()
	choice_request_id = 0
	choice_request_of = ""
	_bassment_pick = {}
	_claim_id = ""
	_claim_to = ""
	if int(ev["phase"]) > 1 or trial_state == "":
		_commit_view = {}
	if run_path != "":
		Session.run_progress.path_enter(run_path, str(node["world"]))  # a path's worlds are saved apart from the main run's levels
	else:
		Session.run_progress.enter(str(node["world"]))  # "reached" is per world: a restart begins at the world's entry scene
	var first := int(ev["phase"]) == 1
	var world_key := "%s/%s" % [run_path, node["world"]]
	var world_changed := not first and world_key != _run_world
	if world_changed or first:
		hud.show_title("%s   LEVEL %d" % [str(node["world_title"]).to_upper(), int(ev["phase"])], str(node["title"]).to_upper(), t0)
	else:
		hud.show_title(str(node["world_title"]).to_upper(), str(node["title"]).to_upper(), t0)
	if world_changed and _passage_swap < 0.0:
		_passage_swap = t0  # the route changed in the last two beats: the frame opens from shut on the new world
	if world != active_world and not race_host.owns_stage():  # (the race's street stays on through the race scene's phase starts)
		_show_world(world)
	_run_world = world_key
	_gate.visible = str(node.get("trial_gate", "")) != "" and trial_state == ""  # the wizard only waits in the Warehouse
	_prewarm_routes(str(ev["node"]))
	var rec: Dictionary = stages[world]
	var st: StoryStage = rec["stage"]
	var wp := str(node["waypoint"])
	if first and wp != "" and wp != str(rec["waypoint"]):  # starting on a level whose home is not the map's start: walk there during the countdown
		_journey_apply({"world": world, "t0": t0 - 4.0 * engine.beat_s, "action": "player_move", "args": {"to": wp, "bars": 3.0, "style": "walk"}})
		rec["waypoint"] = wp
	_apply_pieces(st, node.get("pieces", {}), t0, true)  # the scene's own set pieces: those it lists are on from its downbeat, every other piece of the stage is off
	_stage_action(st, "lights_low_pulse", t0)
	if not first:
		_stage_action(st, "room_swell", t0)  # a new room: its lamps rise over two beats from the downbeat (the title card is gone: the light says "somewhere new")
	if int(ev["phase"]) == 1:
		_stage_action(st, "doors_open", t0)


## The next lap of the same scene (docs/CONTINUOUS_RUN.md "Two laps"): nothing is rebuilt or reset, the room, its lamps, set pieces, rail and people go on; only the log and the touch state start over.
func _on_lap_start(ev: Dictionary) -> void:
	lap_log.append({"phase": int(ev["phase"]), "lap": int(ev["lap"]), "laps": int(ev["laps"]), "node": str(ev["node"]), "t": float(ev["t"]), "stage": int(ev["stage"])})
	_track_stay_phase = -1
	for id in _sel_t.keys():  # (a pick held across the lap keeps its touch time: selection is open for the whole scene)
		if hotspots == null or str(id) != hotspots.selected:
			_sel_t.erase(id)
	_commit_view = {}


## A scene at another tempo begins (a track scene, or the scene after one): every cached beat length follows (the stages' dancers and lights, the hotspot views, the card table), as at a path hand-off.
func _on_tempo(ev: Dictionary) -> void:
	var bpm := float(ev["bpm"])
	for w in stages:
		(stages[w]["stage"] as StoryStage).set_tempo(bpm)
		if stages[w].has("hotspot_view"):
			(stages[w]["hotspot_view"] as HotspotView).beat_s = float(ev["beat_s"])
	if card_table != null:
		card_table.beat_s = float(ev["beat_s"])


## The track scenes played, for the walks (summary "tracks"): {node, track, entry_bar, planned (laps at entry), laps (played), doors_from_lap, left_early, extended, bpm, end, seconds}.
func _on_track_event(ev: Dictionary) -> void:
	if str(ev["kind"]) == "track_start":
		track_log.append({"node": str(ev["node"]), "track": str(ev["track"]), "entry_bar": int(ev["entry_bar"]), "planned": int(ev["laps"]), "laps": 1, "doors_from_lap": int(ev["doors_from_lap"]),
			"left_early": false, "extended": 0, "bpm": snappedf(float(ev["bpm"]), 0.0001), "t": float(ev["t"])})
		return
	if track_log.is_empty():
		return
	var cur: Dictionary = track_log[track_log.size() - 1]
	match str(ev["kind"]):
		"track_lap":
			cur["laps"] = int(ev["lap"])
		"track_last_lap":
			cur["left_early"] = true
		"track_extend":
			cur["extended"] = int(cur["extended"]) + 1
		"track_end":
			cur["end"] = str(ev["reason"])
			cur["seconds"] = snappedf(float(ev["t"]) - float(cur["t"]), 0.001)


## Hands one journey action {world, t0, action, args} to its world's stage and keeps it in the log.
## The Space rave (SpaceRaveHost): a scene starts / every frame.
func _rave_enter(node_id: String, t0: float) -> void:
	rave_host.progress = Session.run_progress
	rave_host.track_audio = audio.track if audio != null else null
	rave_host.beat_s = engine.beat_s
	rave_host.phase_t0_fn = func() -> float: return engine.phase_t0
	rave_host.apply_fn = func(a: Dictionary) -> void:
		a["world"] = str(data.nodes[node_id]["map"])
		_journey_apply(a)
	rave_host.enter(node_id, t0)


func _rave_step(t: float) -> void:
	if not rave_host.in_rave:
		return
	var act: MinigameActivity = minigames.activity if minigames.active() else null
	rave_host.step(t, act.state() if act != null else {})


## A touch in the room while a view-less activity is seated (the bass knob's world region): over the knob thing's screen rect (ruling 38).
func rave_hit(local: Vector2, area: Vector2) -> String:
	if not (minigames.activity is BassKnobActivity) or not stages.has(active_world):
		return ""
	var st: StoryStage = stages[active_world]["stage"]
	var r: Variant = st.thing_screen_rect("bass_knob")
	if r != null and st.size.x > 0.0 and st.size.y > 0.0:  # (stage px to the area's)
		var k := Vector2(area.x / st.size.x, area.y / st.size.y)
		r = Rect2((r as Rect2).position * k, (r as Rect2).size * k)
	return SpaceRaveHost.hit_rect(local, r)


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


## Switches the set pieces of the stage `st` (a thing of the map with `"piece"`): spec {on: [...], off: [...]} at song time t. With `reset` every piece of the stage the spec does not turn on goes off first
## (a new scene: the last one's storm or tables must not linger).
func _apply_pieces(st: StoryStage, spec: Dictionary, t: float, reset := false) -> void:
	var on: Array = spec.get("on", [])
	if reset:
		for pid in st._piece_ids:
			if str(pid) not in on:
				_stage_action(st, "piece_off", t, {"piece": str(pid)})
	for pid in on:
		_stage_action(st, "piece_on", t, {"piece": str(pid)})
	for pid in spec.get("off", []):
		_stage_action(st, "piece_off", t, {"piece": str(pid)})
	if not spec.is_empty():
		piece_log.append({"t": t, "on": on.duplicate(), "off": (spec.get("off", []) as Array).duplicate()})


## A scene's block staging (`block_fx`): what a block's result does at the boundary after it, docs/CONTINUOUS_RUN.md "Paths". Pieces are switched and cast lines acted from the boundary.
func _block_fx(ev: Dictionary) -> void:
	if trial_state != "" or not data.nodes.has(str(ev["node"])):
		return
	var b := int(ev["block"])
	var side := "pass" if bool(ev["passed"]) else "miss"
	var tb := engine.t_of(float((b + 1) * int(engine.timing("block_beats"))))
	for fx in data.nodes[str(ev["node"])].get("block_fx", []):
		if int(fx["block"]) != b or not (fx as Dictionary).has(side) or int(fx.get("lap", 1)) != int(ev.get("lap", 1)):  # (an entry without `lap` is the scene's first lap)
			continue
		var eff: Dictionary = fx[side]
		if eff.has("pieces") and stages.has(active_world):
			_apply_pieces(stages[active_world]["stage"], eff["pieces"], tb)
		var has_flag := func(f: String) -> bool: return hotspots != null and hotspots.has_flag(f)
		for line in eff.get("cast", []):
			if not RunActing.conditions_hold(line, engine.energy, has_flag):
				continue
			_on_cast({"t": tb, "beat": float((b + 1) * int(engine.timing("block_beats"))), "actor": str(line["actor"]), "act": str(line["act"]), "face": str(line.get("face", "")),
				"look_at": str(line.get("look_at", "")), "beats": float(line.get("beats", RunActing.HOLD_BEATS)), "source": "block", "name": ""})


func _on_block_result(ev: Dictionary) -> void:
	_block_fx(ev)
	var t := float(ev["t"]) + 0.2
	if bool(ev["passed"]):
		if int(ev["block"]) < 3:
			if DevText.on():
				pad_view.show_status("Nice: the mix moves on", Color(0.7, 1.0, 0.8), float(Time.get_ticks_msec()) / 1000.0)
	else:
		hud.caption("HOLDING THE MIX: HAVE ANOTHER GO", "bad", t, 2.2)
		if DevText.on():
			pad_view.show_status("Missed it: same cues again", Color(1.0, 0.75, 0.55), float(Time.get_ticks_msec()) / 1000.0)


func _end_fade(_t: float, seconds: float) -> void:
	var tw := create_tween()
	tw.tween_interval(maxf(_t - hud.now_t, 0.0))
	tw.tween_property(hud, "fade", 1.0, maxf(seconds, 0.2))


# --- the acting contract: cast lines and outcome acts ----------------------------------------------------------------------------

## The crowd (StoryCrowd) of the active stage that holds person `actor`; null when nobody of that id stands in the shown world.
func _crowd_of(actor: String, world: String = "") -> StoryCrowd:
	var w := world if world != "" and stages.has(world) else active_world
	if not stages.has(w):
		return null
	var st: StoryStage = stages[w]["stage"]
	for rid in st.crowds:
		if (st.crowds[rid] as StoryCrowd).actors.has(actor):
			return st.crowds[rid]
	return null


## A cast line came due (RunEngine "cast"): the named person does the act from the line's own time (song time, so a late frame changes nothing).
func _on_cast(ev: Dictionary) -> void:
	if trial_state != "":
		return
	var world := ""
	if str(ev["source"]) == "cinematic":  # a setback's cast acts in the world the cinematic belongs to
		var cin: Dictionary = data.cfg.get("cinematics", {}).get(str(ev["name"]), {})
		world = str(data.worlds.get(str(cin.get("world", "")), {}).get("map", ""))
	var t0 := float(ev["t"])
	if str(ev.get("piece", "")) != "":  # a set piece of the scene's world (cast line `piece` + `op`)
		var pw := world if world != "" else active_world
		var pst: StoryStage = _build_stage(pw)["stage"]
		_stage_action(pst, "piece_" + str(ev["op"]), t0, {"piece": str(ev["piece"]), "bars": 2.0})
		cast_log.append({"t": t0, "beat": float(ev["beat"]), "piece": str(ev["piece"]), "op": str(ev["op"]), "source": str(ev["source"]), "applied": true})
		return
	var c := _crowd_of(str(ev["actor"]), world)
	if str(ev["source"]) != "cinematic" and not bool(ev.get("hide", false)) and _touched_actor() == str(ev["actor"]):  # the person the player has touched keeps the touch's act (a scene's own beat on them would undo it)
		cast_log.append({"t": t0, "beat": float(ev["beat"]), "actor": str(ev["actor"]), "act": str(ev["act"]), "face": str(ev["face"]), "look_at": str(ev["look_at"]), "source": str(ev["source"]), "applied": false,
			"held_by_touch": true})
		return
	if bool(ev.get("hide", false)):  # a person who is not in this scene (a companion lost on the road)
		var hid := c != null and c.hide_actor(str(ev["actor"]))
		cast_log.append({"t": t0, "beat": float(ev["beat"]), "actor": str(ev["actor"]), "hide": true, "source": str(ev["source"]), "applied": hid})
		return
	if c != null:
		c.ensure_present(str(ev["actor"]))  # a person of a later group (the traitor and the guards of the grove) is in the scene from the beat that names them
	var applied := c != null and c.direct_actor(str(ev["actor"]), str(ev["act"]), str(ev["face"]), t0, t0 + float(ev["beats"]) * engine.beat_s, str(ev["look_at"]), "cast")
	cast_log.append({"t": t0, "beat": float(ev["beat"]), "actor": str(ev["actor"]), "act": str(ev["act"]), "face": str(ev["face"]), "look_at": str(ev["look_at"]), "source": str(ev["source"]), "applied": applied})


## The person of the hotspot the player has touched in this phase's window, until its commit ("" when none is selected).
func _touched_actor() -> String:
	if hotspots == null or hotspots.selected == "":
		return ""
	var h := hotspots.get_hotspot(hotspots.selected)
	return RunActing.actor_of(h) if RunActing.has_acting(h) else ""


## A hotspot committed: its person plays the outcome's acts (the `committed` flash, then `success` or `failure`, then what follows) from the commit's song time. A hotspot with no `acting` block does
## nothing here (the view stands its person down, as it always did).
func _act_outcome(out: Dictionary, t: float) -> void:
	var h := hotspots.get_hotspot(str(out["hotspot"]))
	if h.is_empty() or not RunActing.has_acting(h):
		return
	var who := RunActing.actor_of(h)
	var chain := RunActing.outcome_chain(h, bool(out["success"]), t, engine.beat_s, _commit_leaves_scene(out))
	if who == "" or chain.is_empty():
		return
	var c := _crowd_of(who)
	if c != null:
		c.direct_chain(who, chain, "outcome")
	acting_log.append({"t": t, "hotspot": str(out["hotspot"]), "actor": who, "success": bool(out["success"]), "acts": chain.map(func(s: Dictionary) -> String: return str(s["act"]))})


## Whether the scene a hotspot commits in is left at the coming downbeat: its route (the outcome's, else the one the phase will take) is another scene, another world or out of this run.
func _commit_leaves_scene(out: Dictionary) -> bool:
	var to := str(out.get("route", ""))
	if to == "":
		to = engine.selected_route()
	return to != "" and to != engine.node_id


# --- routes ---------------------------------------------------------------------------------------------------------------

func _open_routes(ev: Dictionary) -> void:  # the hotspot window: the world is the menu, nothing to build
	if audio != null:
		for o in ev["options"]:
			if data.nodes.has(str(o["to"])):  # (an ending's way back is no scene)
				audio.preload_pack(str(data.nodes[str(o["to"])]["audio"]))
		audio.track.prefetch_for(data, engine.node_id, _path_cache, main_data)  # the stems of the track scenes this scene can lead to, on worker threads
	_track_stay_phase = engine.phase_n if ev.has("track") and not bool(ev.get("last", true)) else -1
	if not ev.has("track"):  # (no riser or fall sounds over a track)
		hud.caption("RISER" if str(ev["effect"]) == "riser" else "FALL", "info", float(ev["t"]), 2.0)


func _close_routes(_ev: Dictionary) -> void:
	hud.route_hint = ""


func _unhandled_key_input(event: InputEvent) -> void:  # desktop: 1 to 8 pick the choices on show, in order (INTERACTION_DESIGN.md 2.6: up to eight choices)
	if hotspots == null or not (event is InputEventKey) or not event.pressed or event.echo or trial_state != "":
		return
	var kc := (event as InputEventKey).keycode
	if kc >= KEY_1 and kc <= KEY_8:
		var shown := hotspots.shown(engine.block, selection_open())
		if kc - KEY_1 < shown.size():
			hotspot_select(str(shown[kc - KEY_1]["id"]))


# --- hotspots -------------------------------------------------------------------------------------------------------------

## What the hotspot view draws and the taps hit: [{hotspot, state, t_state}] for the hotspots on show now, plus the one that has just committed (it stays for its flash) and one that has just
## refused a tap (it recoils for HotspotView.REFUSE_S). SELECTION IS OPEN FOR THE WHOLE SCENE (INTERACTION_DESIGN.md 2.2, N2.1): every available choice is on show while the port's
## selection_open() holds, from the scene's first beat to the lock, in every lap; not only in the engine's route window.
func hotspot_items() -> Array:
	var out: Array = []
	if hotspots == null or trial_state != "" or engine == null or minigames.active():  # minigames: the table's view owns the touches
		return out
	var now: float = hud.now_t
	for h in hotspots.shown(engine.block, selection_open()):
		var id := str(h["id"])
		var sel := id == hotspots.selected
		var it := {"hotspot": h, "state": "selected" if sel else "available", "t_state": float(_sel_t.get(id, 0.0)) if sel else 0.0, "t_commit": _t_commit_of(h),
			"finished": HotspotContract.finished_look(h, hotspots.has_flag)}  # a portal whose path has been finished (plan D10)
		if _refused.has(id) and now - float(_refused[id]["t"]) < HotspotView.REFUSE_S:
			it["state"] = "refused"
			it["t_state"] = float(_refused[id]["t"])
		out.append(it)
	for id in _refused.keys():  # a refusal of a choice that is no longer on show (a tap on a door in the lock window): drawn on its own for its moment
		var rf: Dictionary = _refused[id]
		if now - float(rf["t"]) >= HotspotView.REFUSE_S:
			_refused.erase(id)
		elif not out.any(func(e: Dictionary) -> bool: return str(e["hotspot"]["id"]) == str(id)):
			out.append({"hotspot": rf["hotspot"], "state": "refused", "t_state": float(rf["t"]), "t_commit": float(rf["t"])})
	if not _commit_view.is_empty():
		if hud.now_t - float(_commit_view["t"]) < (HotspotView.FLASH_S + HotspotView.SETTLE_S) * 1.05:
			out.append({"hotspot": _commit_view["hotspot"], "state": "committed", "t_state": float(_commit_view["t"]), "t_commit": float(_commit_view["t"]), "success": bool(_commit_view.get("success", true))})
		else:
			_commit_view = {}
	return out


## The table's players follow its hotspot: on show, touched, judged, seated (RunCardTable.mood_of, a pure function of these and song time).
func _card_table_feed(t: float) -> void:
	if card_table == null:
		return
	var entry := {}
	for e in hotspot_items():
		if str(e["state"]) != "committed" and RunCardTable.is_table(e["hotspot"]):
			entry = e
	var last := {}
	for i in range(hotspot_log.size() - 1, -1, -1):
		var l: Dictionary = hotspot_log[i]
		if str(l["kind"]) == "commit" and hotspots != null and RunCardTable.is_table(hotspots.get_hotspot(str(l["hotspot"]))):
			last = {"t": float(l["t"]), "success": bool(l["success"])}
			break
	card_table.set_mood(RunCardTable.mood_of(entry, last, minigames.state, t, engine.beat_s), t)  # (A8b: no close-up to give way to; seated, the activity directs the players)


## Song time of the decision that will judge a selection of `h`: its window's next decision beat. A final-window choice commits at the lock of the next departure boundary (the port's
## lock_t(next_boundary_t()): a pick on a path scene's first lap waits for the last lap's), else the last block's decision of this lap.
func _t_commit_of(h: Dictionary) -> float:
	if RunHotspots.window_of(h) == "final" and director != null:
		var lt := director.lock_t(director.next_boundary_t())
		if is_finite(lt):
			return lt
	var b := 3 if RunHotspots.window_of(h) == "final" else mini(engine.block, 3)
	return engine.t_of(float(b * int(engine.timing("block_beats"))) + engine._decision_beat())


## The choice the world stages now (HotspotView.choice_fn, docs/CHOICE_CLARITY.md): the scene's staged options, the current one (the touched one, else the default), the commit,
## where the player is going, and when each was last touched. Empty in the Bassment (TrialScene stages its own) and before the run is under way.
func choice_state() -> Dictionary:
	if hotspots == null or engine == null or trial_state != "" or _ended:
		return {}
	var cur := hotspots.current_id(engine.block)
	var dest := hotspots.destination(engine.block)
	if _track_stay_phase == engine.phase_n and engine.window_open and hotspots.committed == "" and not engine._exit_touched():  # a track scene's open lap before the last: nothing touched means staying, so no door is the way
		cur = ""
		dest = engine.node_id
	return {"staged": hotspots.staged(engine.block), "current": cur, "committed": hotspots.committed, "dest": dest,
		"default": str(hotspots.default_hotspot().get("id", "")), "touched": _sel_t, "changed_t": _choice_changed_t()}


func _choice_changed_t() -> float:  # the last touch or commit of this scene's choice
	var t := -INF
	for id in _sel_t:
		t = maxf(t, float(_sel_t[id]))
	if not _commit_view.is_empty():
		t = maxf(t, float(_commit_view["t"]))
	return t


## The player (or the bot) touches a hotspot by id. Allowed while selection is open (selection_open(): from the scene's first beat until the lock) and the hotspot is on show; the selection can
## be changed with one more touch until then (the old pick deselects in the same frame), and it is held until the commit at the next departure boundary. Touching the selected choice again keeps
## it (assumption A1) and thumps it once more. A touch while the transition is locked is refused (the object recoils once, show_refused). Returns whether it is selected.
func hotspot_select(id: String) -> bool:
	if hotspots == null or _ended or trial_state != "" or minigames.active():  # minigames: nothing is selected while seated
		return false
	if not selection_open():
		if not hotspots.get_hotspot(id).is_empty():
			show_refused(id, &"locked")
		return false
	var prev := hotspots.selected
	var same := id != "" and prev == id
	var again := same and str(hotspots.get_hotspot(id)["look"]["selected"]) == "claim"  # a repeat touch keeps the claim as it is
	var ok := hotspots.select(id, engine.block, true)
	if ok:
		if not again:
			_sel_t[id] = hud.now_t
		_on_select_walk(hotspots.get_hotspot(id), hud.now_t)
		if str(_commit_view.get("id", "")) == id:  # touched again while its last outcome still shows (a table that can be touched again)
			_commit_view = {}
		_refused.erase(id)
		hotspot_log.append({"kind": "select", "t": hud.now_t, "hotspot": id, "block": engine.block, "phase": engine.phase_n, "lap": engine.lap, "beat": engine.phase_beat_at(hud.now_t),
			"again": same, "from": prev})
		if not same:
			_choice_picked(id, prev)
	return ok


## Whether a choice may be touched now: the port's selection_open() (true from the scene's first beat until each lock point, false from the lock to the boundary), and no excursion or activity
## owning the touches. Without a port (never in the game) the engine's route window decides, as before N2.1.
func selection_open() -> bool:
	if engine == null or trial_state != "" or _ended:
		return false
	if director != null:
		return director.selection_open()
	return engine.window_open


# --- THE ROUTER SEAM (work package N2.2) --------------------------------------------------------------------------------------
# N2.1 keeps today's commit: the pick is RunHotspots.selected, committed by the engine at the lock of the departure lap and taken by the director as an observed lock. N2.2 routes a pick through
# the port instead, here and nowhere else:
#   choice_request_fn = func(hotspot_id: String) -> int: return router.submit(port(), hotspot_id)   # every new pick; 0 = refused at once (the pick is undone, the object recoils)
#   choice_cancel_fn  = func(request_id: int) -> bool: return port().cancel(request_id)             # hotspot_deselect(), when the player withdraws a pick
#   port().request_closed -> choice_closed(hotspot_id_of(request id), reason)                       # replaced: nothing to do; cancelled / unavailable: the object deselects (and recoils)
# Quest entrances are never gated by rhythm (lead ruling 15): that is N2.2's routing, not this seam.
var choice_request_fn: Callable = Callable()  # (hotspot id) -> request id (> 0), or 0 when the port refused at once
var choice_cancel_fn: Callable = Callable()  # (request id) -> bool
var choice_request_id := 0  # the port's id of the current pick (0: none, or N2.1 without the router)
var choice_request_of := ""  # the hotspot that request is for


## A new pick (not a repeat touch of the selected one). With N2.2's router wired the port is asked; a refusal at once puts the previous pick back and the object recoils.
func _choice_picked(id: String, prev: String) -> void:
	if not choice_request_fn.is_valid():
		return
	var rid := int(choice_request_fn.call(id))
	if rid > 0:
		choice_request_id = rid
		choice_request_of = id
		return
	if rid < 0:  # N2.2: a pick the port does not carry (the wizard, a seat at a table, a hub's Bassment entrance held here): it takes the one slot, so a pending request is withdrawn
		var old := choice_request_id
		choice_request_id = 0
		choice_request_of = id
		if old > 0 and choice_cancel_fn.is_valid():
			choice_cancel_fn.call(old)
		return
	hotspots.selected = prev  # the port kept the previous request (a refusal at once replaces nothing)
	show_refused(id, director.last_refusal() if director != null else &"unavailable")


## The player withdraws the pick (no gesture does this in N2.1, assumption A1: a second touch keeps it; N2.2 or a later design may add one). The scene's default applies again.
func hotspot_deselect(id: String) -> bool:
	if hotspots == null or not selection_open() or not hotspots.deselect(id):
		return false
	_sel_t.erase(id)
	if str(_bassment_pick.get("hotspot", "")) == id:
		_bassment_pick = {}
	hotspot_log.append({"kind": "deselect", "t": hud.now_t, "hotspot": id, "phase": engine.phase_n})
	if choice_cancel_fn.is_valid() and choice_request_of == id and choice_request_id > 0:
		choice_cancel_fn.call(choice_request_id)
	choice_request_id = 0
	choice_request_of = ""
	return true


## The port closed the request of `id` (N2.2's request_closed handler): &"replaced" changes nothing here (the new pick is already selected); &"cancelled" and &"unavailable" deselect it, and an
## unavailable destination recoils (INTERACTION_DESIGN.md 2.3, 2.4).
func choice_closed(id: String, reason: StringName) -> void:
	if reason == &"replaced" or hotspots == null:
		return
	if hotspots.deselect(id):
		_sel_t.erase(id)
		hotspot_log.append({"kind": "closed", "t": hud.now_t, "hotspot": id, "reason": str(reason), "phase": engine.phase_n})
	if choice_request_of == id:
		choice_request_id = 0
		choice_request_of = ""
	if reason == &"unavailable":
		show_refused(id, reason)


# --- THE ROUTER IN THE RUN (work package N2.2; docs/narrative/N2_2_ROUTER.md) ------------------------------------------------------------------------
# The QuestRouter (src/narrative/) is made at every run start with the game's graph (NarrativeGraph.cached()) and a store on the run save (NarrativeRunStore: the `narrative` key of
# user://story_run.json), loaded (an old save is migrated), started on the run's first scene and attached to the port. Then:
#   a pick (hotspot_select -> _choice_picked -> _route_pick): router.destination_for + port.request + router.hold. A quest entrance or return is a destination like any other (kind quest_entry /
#     quest_return, no on_miss: never gated by rhythm); the wizard, a seat at a table and an object the graph does not know stay on today's commit; a hub's Bassment entrance is held here;
#   switched (the director) -> router.commit (the only change of the route state, saved) -> router.committed -> _on_route_committed (the quest's flags restored, a "keep:" flag saved);
#   request_closed -> router.discard and _on_port_closed -> choice_closed (the pick deselects);
#   the Bassment (ruling 20, not behind the port): a hub's entrance is armed at the lap's lock (_on_lock_point), the trial begins on the boundary (trial_begin_now: the router's commit for
#     the hatch, commit_legacy for the wizard), its passages are committed as the dungeon moves (_trial_route_sync) and the way out lands on the checkpoint (trial_leave). These are the
#     commits not made on `switched`: the declared exception, extended to the whole Bassment until the director accepts "bassment/*".
# The router is off (the run behaves as in N2.1) with RW_NARRATIVE=0, with RW_PATH_REMAP (a remapped path is outside the graph), in a path the graph does not know (the stub), or if the
# graph does not load (a warning; the game goes on).
var router: QuestRouter  # null when off
var route_log: Array = []  # [{kind: start | switched | bassment_enter | bassment_passage | bassment_leave | leave_request, t, ...}]: every route state change, for the tests and the walks
var _bassment_pick: Dictionary = {}  # {hotspot, dest}: a hub's Bassment entrance picked (held here: the port refuses "bassment/*"); armed at the lock
var _trial_entry: Dictionary = {}  # how the dungeon is being entered: {way: "legacy" (the wizard) | "hatch" | "direct", object, dest}
var _trial_start_passage := -1  # the passage a hatch entry starts on (the router's: the saved passage of an unfinished visit)
var _trial_passage_seen := -1
var _trial_items: Array = []  # the items carried in the dungeon now (the router stores them on the way out, as "item:<id>" flags)
var _keep_unsaved := false  # a "keep:" flag set at a lock waits for the next `switched` to be saved
var _main_cache: RunData  # the main run's data read for a return when the run began inside a path


func _router_wanted() -> bool:
	if OS.get_environment("RW_NARRATIVE") == "0" or OS.get_environment("RW_PATH_REMAP") != "":
		return false
	return run_path == "" or NarrativeGraph.SHIPPED_PATHS.has(run_path)


## The router of this run: graph, store, load (with the old-save migration), the run's start, the port. Called once in _ready, after the run's flags are set.
func _setup_router(start: String) -> void:
	if not _router_wanted() or director == null:
		return
	var g := NarrativeGraph.cached()
	if not g.is_valid():
		push_warning("narrative graph not valid, the router is off: %s" % "; ".join(PackedStringArray(g.errors.slice(0, 3))))
		return
	var store := NarrativeRunStore.new(Session.run_progress)
	router = QuestRouter.new(g, store)
	router.flags_source = _route_flags
	router.load_state(store.extra())
	var first := ("main" if run_path == "" else run_path) + "/" + start
	var res := router.start_run(first)
	_restore_flags(res.get("restore_flags", []))
	router.attach(port())
	router.committed.connect(_on_route_committed)
	port().request_closed.connect(_on_port_closed)
	choice_request_fn = _route_pick
	choice_cancel_fn = func(rid: int) -> bool: return port().cancel(rid)
	hotspots.ungated_quest_routes = true
	route_log.append({"kind": "start", "t": 0.0, "scene": first, "closed_on_load": router.state.closed_on_load, "state": router.state.to_dict(), "errors": router.errors.duplicate()})


## The run's flags as the router reads them: this run's, the kept ones, and the items carried in the dungeon ("item:<id>").
func _route_flags() -> Dictionary:
	var out: Dictionary = Session.run_progress.run_flags.duplicate()
	out.merge(Session.run_progress.flags)
	for it in _trial_items:
		out["item:" + str(it)] = true
	return out


## A quest's own flags, saved when it was left, are set again when it is entered (a re-entered Ember keeps ember_no_vial). Items are the dungeon's (trial_begin_now).
func _restore_flags(names: Array) -> void:
	for f in names:
		if not str(f).begins_with("item:"):
			Session.run_progress.run_flags[str(f)] = true


func _after_route_commit(res: Dictionary) -> void:
	if bool(res.get("saved", false)):
		_keep_unsaved = false
	elif _keep_unsaved:
		Session.run_progress.save()
		_keep_unsaved = false


## choice_request_fn: a new pick. > 0 the port's request id; 0 refused at once; -1 not carried by the port (today's commit carries it, or the Bassment entrance held here).
func _route_pick(id: String) -> int:
	_bassment_pick = {}
	var h := hotspots.get_hotspot(id)
	if h.is_empty() or RunHotspots.window_of(h) != "final":  # the wizard (early window, outside the port: ruling 15) and a seat at a table (an activity, never a route)
		return -1
	var dest := router.destination_for(id)
	if dest.is_empty():
		return -1  # (an object the graph does not know: today's commit; the director observes it)
	if str(dest["path"]) == "bassment":
		_bassment_pick = {"hotspot": id, "dest": dest}
		if audio != null:
			audio.preload_pack(str(tdata.raw["music"]["audio"]))  # (silent preparation; the dungeon's zone is built at the lock)
		return -1
	var rid := port().request(dest)
	if rid <= 0:
		return 0
	router.hold(rid, dest)
	return rid


## request_closed: the pick of that request is withdrawn (replaced: nothing to do).
func _on_port_closed(id: int, reason: StringName) -> void:
	if id > 0 and id == choice_request_id:
		choice_closed(choice_request_of, reason)


## After every switch (QuestRouter.committed): the entered quest's flags come back, a "keep:" flag set at the lock is saved (the router's save wrote it, else a save here).
func _on_route_committed(id: int, landed: Dictionary, res: Dictionary) -> void:
	_restore_flags(res.get("restore_flags", []))
	_after_route_commit(res)
	route_log.append({"kind": "switched", "t": hud.now_t if hud != null else 0.0, "id": id, "landed": str(landed.get("id", "")), "fallback": bool(landed.get("fallback", false)),
		"kind_of": str(landed.get("kind", "")), "result": res, "state": router.state.to_dict()})


## The scene of the main run a way back lands on: the checkpoint (the hub of the location the quest was entered from), "" without a router.
func _return_start() -> String:
	if router == null:
		return ""
	var cp := router.state.checkpoint if router.state.checkpoint != "" else router.graph.hub_of_location(router.state.location)
	return cp.trim_prefix("main/") if cp.begins_with("main/") else ""


## The pause menu's "Leave this path" through the port: on a departure lap while selection is open, the hidden leave is requested like a pick (it replaces the player's pick, which deselects)
## and locks at this lap's end. Otherwise (a lap before the last, or after the lock) it is today's leave (force_leave at beat 61) and the hand-off lands on the checkpoint (_path_swap).
func _route_leave_now() -> bool:
	if not selection_open() or not engine.is_departure_lap():
		return false
	var dest := router.destination_for(str(NarrativeGraph.HIDDEN_VIA["pause_menu_leave"]))
	if dest.is_empty():
		return false
	var rid := port().request(dest)
	if rid <= 0:
		return false
	router.hold(rid, dest)
	if hotspots.selected != "":
		_sel_t.erase(hotspots.selected)
		hotspots.selected = ""
	_bassment_pick = {}
	choice_request_id = rid
	choice_request_of = ""
	route_log.append({"kind": "leave_request", "t": hud.now_t, "id": rid, "dest": str(dest["id"])})
	return true


## The engine's lock point, before the director's say: a hub's Bassment entrance committed here (engine.choice "bassment") arms the dungeon for this boundary (it is never gated: the
## hotspot commits as a success whatever the block), the director is told (&"armed": nothing locks), and the engine never reaches its commit (its updates stop short of the boundary).
func _on_lock_point(info: Dictionary, dir_hook: Callable) -> Variant:
	if engine != null and HotspotContract.is_dungeon_route(engine.choice) and trial_state == "":
		if bool(info.get("departure", false)) and not bool(info.get("hold", false)) and _arm_trial_at_lap_end(float(info["t"]), float(info["boundary_t"])):
			dir_hook.call(info)  # (armed: the director locks nothing and keeps its count of laps)
			return {}
		var fallback_route := engine.default_route()  # (cannot go: the scene's default exit, never a crash on a route the engine does not know)
		engine.take_route(fallback_route)
		info = info.duplicate()
		info["route"] = fallback_route
		info["leaving"] = fallback_route != engine.node_id
	if router != null and bool(info.get("final", false)) and bool(info.get("chosen", false)) and not bool(info.get("leaving", false)) and director.state() != TransitionPort.State.PENDING:
		return {}  # (the player's own choice keeps the scene, a seat at a table: the router's default, set for the port, must not take the run away from it; as before N2.2)
	return dir_hook.call(info) if dir_hook.is_valid() else {}


## The hub's Bassment entrance taken at the lap's end: the dungeon takes the pads on the guard 3.25 beats before the boundary (as the wizard's entry does) and begins on the boundary. The music
## hand-off is a cut (TrialScene brings its pack in on the downbeat, as today).
func _arm_trial_at_lap_end(t_lock: float, boundary_t: float) -> bool:
	if trial == null or trial_state != "":
		return false
	var dest: Dictionary = _bassment_pick.get("dest", {})
	if dest.is_empty() and router != null:
		dest = router.destination_for(str(_bassment_pick.get("hotspot", "")))
	var passage := tdata.start
	if str(dest.get("node", "")).is_valid_int():
		passage = int(str(dest["node"]))
	trial_state = "armed"
	if director != null:
		director.excursion(&"armed")
	_trial_g1 = -1.0
	_trial_g2 = boundary_t - 3.25 * engine.beat_s
	trial_entry_t = boundary_t
	_trial_start_passage = passage
	_trial_entry = {"way": "hatch", "object": str(_bassment_pick.get("hotspot", "")), "dest": dest}
	_bassment_pick = {}
	_gate.visible = false
	if audio != null:
		audio.preload_pack(str(tdata.raw["music"]["audio"]))
	trial.build_zone(tdata.zone_of_passage(passage))
	trial_log.append({"kind": "armed", "t": t_lock, "g1": -1.0, "g2": _trial_g2, "entry": trial_entry_t, "beat": engine.phase_beat_at(t_lock), "way": "hatch", "passage": passage})
	return true


## The route state as the dungeon begins: the wizard's commit_legacy, the hatch's held destination, a direct launch's passage. Returns commit()'s result.
func _route_enter_bassment(way: String, start_passage: int) -> Dictionary:
	var res: Dictionary = {}
	if router.state.quest == "bassment":
		return res
	if way == "legacy" and str(_trial_entry.get("object", "")) != "":
		res = router.commit_legacy(str(_trial_entry["object"]))
	elif way == "hatch" and not (_trial_entry.get("dest", {}) as Dictionary).is_empty():
		res = router.commit(0, _trial_entry["dest"])
	else:
		var p := start_passage if start_passage >= 0 else tdata.start
		res = router.commit(0, {"id": "bassment/%d" % p, "path": "bassment", "node": str(p), "kind": &"quest_entry", "quest": "bassment"})
	_after_route_commit(res)
	route_log.append({"kind": "bassment_enter", "t": hud.now_t, "way": way, "result": res, "state": router.state.to_dict()})
	return res


## While the dungeon runs: a new passage is committed to the route state (the dungeon has no port: ruling 20), and the items held are kept for the way out.
func _trial_route_sync() -> void:
	if (trial_state != "in" and trial_state != "leaving") or trial == null or trial.engine == null or trial.engine.flow == null:
		return
	_trial_items = (trial.engine.flow.flags as Array).duplicate()
	var p := int(trial.engine.flow.passage)
	if p == _trial_passage_seen:
		return
	_trial_passage_seen = p
	if router == null or router.state.quest != "bassment":
		return
	var res := router.commit(0, {"id": "bassment/%d" % p, "path": "bassment", "node": str(p), "kind": &"scene", "quest": "bassment"})
	_after_route_commit(res)
	route_log.append({"kind": "bassment_passage", "t": hud.now_t, "passage": p, "result": res, "state": router.state.to_dict()})


## The F3 line's bedsit part: the compass letter and the theme the facing leads to; "" outside the bedsit path (src/bedsit/bedsit_nav.gd).
func _bedsit_debug() -> String:
	return BedsitNav.debug_line(Session.run_progress.data, run_path == BedsitNav.PATH_ID)


## The F3 line's route part (NARRATIVE_GRAPH.md 7.1, the developer overlay line): location, quest and checkpoint.
func _route_debug() -> String:
	if router == null:
		return ""
	var st := router.state
	return "  route %s quest %s cp %s" % [st.location, st.quest if st.quest != "" else "-", st.checkpoint if st.checkpoint != "" else "-"]


## A choice did not take a touch: it recoils once (HotspotView.REFUSE_S) and the selection stays as it was. Logged as "refused" with the reason (&"locked", or the port's).
func show_refused(id: String, reason: StringName) -> void:
	var h := hotspots.get_hotspot(id) if hotspots != null else {}
	if h.is_empty():
		return
	_refused[id] = {"t": hud.now_t, "reason": reason, "hotspot": h}
	hotspot_log.append({"kind": "refused", "t": hud.now_t, "hotspot": id, "reason": str(reason), "phase": engine.phase_n})


# --- reactive objects (INTERACTION_DESIGN.md 2.1, 2.5) ------------------------------------------------------------------------

## The scene's reactive objects for the view and the taps: [{hotspot (the normalised reactive row), state: "idle" | "reacting", t_state}]. Empty in the Bassment and while seated.
func reactive_items() -> Array:
	var out: Array = []
	if hotspots == null or trial_state != "" or engine == null or minigames.active():
		return out
	for r in hotspots.reactives():
		var id := str(r["id"])
		var t0 := float(_react_t.get(id, -INF))
		out.append({"hotspot": r, "state": "reacting" if hud.now_t - t0 < HotspotView.REACT_S else "idle", "t_state": t0 if is_finite(t0) else 0.0})
	return out


## A reactive object is touched: it reacts (in every state of the scene, the lock included) and nothing else happens: no selection change, no port call, no route.
func reactive_tap(id: String) -> bool:
	if hotspots == null or _ended or trial_state != "" or minigames.active():
		return false
	var out := hotspots.react(id)
	if out.is_empty():
		return false
	_react_t[id] = hud.now_t
	hotspot_log.append({"kind": "react", "t": hud.now_t, "reactive": id, "reaction": str(out["reaction"]), "phase": engine.phase_n})
	return true


## The touch itself moves the camera when the hotspot has an `on_select` cinematic (the table: the walk to the chair starts now); touching anything else gives the rail back.
func _on_select_walk(h: Dictionary, t: float) -> void:
	var id := str(h["id"])
	if _claim_id == id:
		return
	if _claim_id != "":
		_back_to_rail(t)
		_claim_id = ""
		_claim_to = ""
	if not h.has("on_select") or journey == null or journey.rail == null:
		return
	var spec := HotspotContract.resolve_cinematic(h, h["on_select"], data.cfg.get("cinematics", {}))
	if spec.is_empty():
		return
	for a in journey.hotspot_actions(spec, t, engine, _look_by, true):
		_journey_apply(a)
	_claim_id = id
	for st in spec.get("steps", []):
		if st.has("move") and st.has("to"):
			_claim_to = str(st["to"])
	_claim_frame(t, _t_commit_of(h))


## While a claim stands the camera tips down so the table is in the picture (the glances overlap to hold the tip until the decision), and the glances queued for the walk's time are dropped:
## an ambient glance must not swing the table out of the picture.
func _claim_frame(t: float, t_commit: float) -> void:
	if not stages.has(active_world):
		return
	var pl: StoryPlayer = (stages[active_world]["stage"] as StoryStage).player
	if pl == null:
		return
	pl.release_faces(t, 2.0 * engine.beat_s)  # the head held on the window's hotspots (the look-pass window camera) lets go: the table is what the touch is about
	var span := 4.0 * engine.beat_s
	pl._glances = pl._glances.filter(func(g: Dictionary) -> bool: return float(g["t1"]) <= t or float(g["t0"]) >= t_commit + span)
	for k in int(ceil(maxf(t_commit - t, 0.0) / span)) + 1:
		_journey_apply({"world": active_world, "t0": t + float(k) * span, "action": "player_look", "args": {"by": 0.0, "pitch": CLAIM_TIP, "bars": 2.0}})


## The camera goes back to the rail: the rail starts again from here and the camera walks to the scene's home waypoint over two bars (also what is left of a minigame does).
func _back_to_rail(t: float) -> void:
	var j: RunJourney = journey
	if j.rail == null or not stages.has(active_world):
		return
	j.rail.restart_here()
	var wp := str(data.nodes[engine.node_id].get("waypoint", ""))
	if wp != "":
		_journey_apply({"world": active_world, "t0": t, "action": "player_move", "args": {"to": wp, "bars": 2.0, "style": "walk"}})
	_journey_apply({"world": active_world, "t0": t, "action": "player_role", "args": {"role": "dancer"}})
	if engine.window_open and t < engine.t_of(3.0 * float(engine.timing("block_beats")) + 12.0):  # the last block's window: the head frames the window's hotspots again (the camera the touch took away)
		var pts := _window_face(engine.node_id, "")
		if not pts.is_empty():
			var fa: Dictionary = journey.window_face(pts, t, engine)
			fa["world"] = active_world
			_journey_apply(fa)


## True when a world-state flag is set (this run's or a kept discovery).
func run_flag_set(name: String) -> bool:
	return Session.run_progress.has_flag(name)


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
	if minigames.active():  # minigames: the activity's view decides what was touched
		var target := _mg.hit(pos - rect.position, rect.size)
		if target != "":
			hotspot_log.append({"kind": "minigame_tap", "t": hud.now_t, "target": target, "ok": minigames.tap(target, hud.now_t)})
		return target
	if _pause_btn != null and _pause_btn.visible and _pause_btn.get_global_rect().has_point(pos):  # (the pause button is HUD, never a touch region: INTERACTION_DESIGN.md 7.1)
		return ""
	var st: StoryStage = stages[active_world]["stage"]
	var pose := _exit_pose()
	if st.map == null or pose.is_empty():
		return ""
	var widths := HotspotView.thing_widths(st)
	var at := pos - rect.position
	var items := hotspot_items().filter(func(e: Dictionary) -> bool: return str(e["state"]) != "committed")
	var id := HotspotView.hit(HotspotView.layout(items, st.map, st.crowds, pose, rect.size, true, widths), at)  # (the object itself is touchable: its visual bounds plus 24 px)
	if id != "":  # a choice wins over a reactive object where they overlap (assumption A7)
		return id if hotspot_select(id) else ""
	if not selection_open():  # the lock: a touch on one of the choices still standing in the room is refused once (it recoils), the transition stays as it is
		var staged: Array = hotspots.staged(engine.block).map(func(h: Dictionary) -> Dictionary: return {"hotspot": h, "state": "available", "t_state": 0.0})
		var sid := HotspotView.hit(HotspotView.layout(staged, st.map, st.crowds, pose, rect.size, true, widths), at)
		if sid != "":
			show_refused(sid, &"locked")
			return ""
	var reacts := reactive_items()
	if not reacts.is_empty():
		var lay := HotspotView.layout(reacts, st.map, st.crowds, pose, rect.size, true, widths).filter(func(e: Dictionary) -> bool: return not bool(e["edge"]))  # (only a reactive object in view)
		var rid := HotspotView.hit(lay, at)
		if rid != "":
			reactive_tap(rid)
			return ""
	hotspot_log.append({"kind": "tap_miss", "t": hud.now_t, "pos": pos})
	return ""


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
	dispatch_tap(pos)


## The one tap dispatcher (CONTRACTS.md 5, hook H5.5): every tap that reaches the scene (a pad press the lane input took never does) has exactly one owner,
## ContractShapes.tap_owner of its area (the pause button, the pad strip, the stage area), the seated activity's mode, the scene's world regions and the Bassment.
## The strip is the activity's controls while a replace activity owns it (the pads are refused meanwhile, `_on_button_pressed`); the stage is the activity's view
## or, for an overlay activity, its four regions; a world choice is never touched while an activity is seated. Returns the owner ("" for a tap no one owns).
func dispatch_tap(pos: Vector2) -> String:
	var t: float = hud.now_t if hud != null else 0.0
	var area := _tap_area(pos)
	var mode := minigames.input_mode(t) if minigames != null else -1
	var trial_on := trial_state == "in" and trial != null and trial.active  # inside the Bassment the same touch is the dungeon's
	var owner := ContractShapes.tap_owner(area, mode, not world_regions.is_empty() and mode < 0, trial_on)
	var target := ""
	match owner:
		"trial":
			trial.hotspot_tap(pos)
		"activity_controls":
			target = _mg.control_tap(pos, t)
		"world_regions":
			if mode == ActivityMode.Mode.OVERLAY:
				target = _mg.region_tap(pos, t)
			elif _stage_host != null:
				var at := (pos - _stage_host.global_position) / _stage_host.size
				target = ContractShapes.region_at(world_regions, at) if ContractShapes.regions(world_regions).is_empty() else ""
				if target != "":
					world_region_tapped.emit(target, t)
		"activity_view", "hotspots":
			target = hotspot_tap(pos)
	input_log.append({"t": t, "area": area, "owner": owner, "target": target})
	return owner


## The area a tap falls in: "hud" (the pause button), "strip" (the pad strip, or a pad's grown rect), else "stage".
func _tap_area(pos: Vector2) -> String:
	if _pause_btn != null and _pause_btn.visible and _pause_btn.get_global_rect().has_point(pos):
		return "hud"
	if pad_view != null:
		if pad_view.get_global_rect().has_point(pos):
			return "strip"
		for p in pad_view.button_rects():
			if (pad_view.button_rects()[p] as Rect2).has_point(pos):
				return "strip"
	return "stage"


func _on_hotspot_commit(ev: Dictionary) -> void:
	var out: Dictionary = ev["outcome"]
	var t := float(ev["t"])
	hotspot_log.append({"kind": "commit", "t": t, "hotspot": str(out["hotspot"]), "success": bool(out["success"]), "route": str(out["route"]), "window": str(out["window"]), "tapped": bool(out["tapped"]),
		"energy": float(ev["energy"]), "phase": int(ev["phase"]), "node": str(ev["node"]), "continued": bool(out["continued"]), "flags": out["flags_set"]})
	var claim_to := _claim_to if _claim_id == str(out["hotspot"]) else ""
	if _claim_id == str(out["hotspot"]):  # the walk the touch started ends here: a failure gives the camera back to the rail (the last block's door walk takes it on from where it stands)
		_claim_id = ""
		_claim_to = ""
		if not bool(out["success"]) and not bool(out["continued"]):
			_back_to_rail(t)
	_commit_view = {"id": str(out["hotspot"]), "t": t, "hotspot": hotspots.get_hotspot(str(out["hotspot"])), "success": bool(out["success"])}
	if hotspots.persist_dirty:
		if router != null:
			_keep_unsaved = true  # a "keep:" flag is saved at `switched`, not at the lock (NARRATIVE_GRAPH.md 3.2 rule 7): the router's save writes it
		else:
			Session.run_progress.save()
		hotspots.persist_dirty = false
	_act_outcome(out, t)
	if not (out.get("pieces", {}) as Dictionary).is_empty() and stages.has(active_world):
		_apply_pieces(stages[active_world]["stage"], out["pieces"], t)
	if str(out.get("activity", "")) != "" and bool(out["success"]):  # minigames: sit down on the next downbeat; the run stays here and no door walk starts
		var aid := str(out["activity"])  # H4.3: in a rave the request is built from data (the theme's keys merged into the config, the station's pose to come back to)
		var theme := Session.run_progress.rave_theme() if Session.run_progress != null else ""
		var req := RunMinigameHost.build_request(aid, minigames.config_of(aid), theme, RunMinigameHost.theme_data_of(theme), engine.node_id, str(data.nodes[engine.node_id].get("waypoint", "")))
		minigames.request(aid, t, engine.t_of(float((int(ev["block"]) + 1) * int(engine.timing("block_beats")))), _mg.exits_for(engine.node_id), req)
		_door_phase = engine.phase_n
	if not (out["cinematic"] as Dictionary).is_empty():
		_hotspot_cinematic(out, t, claim_to)
	if str(out["window"]) == "early" and bool(out["success"]) and HotspotContract.is_trial_route(str(out["route"])):
		_trial_entry = {"way": "legacy", "object": str(out["hotspot"])}  # (the wizard: committed to the route state when the trial begins, commit_legacy)
		trial_launcher.call()  # the wizard's way in: the walk to the hatch is scheduled by arm_trial on the next cue-free guard


## An outcome's cinematic is rail actions (RunJourney.hotspot_actions): steps of role, look and move. The move replaces the door walk only when the scene simply continues by its default exit;
## when the outcome names a route the door walk toward it is the camera's move.
func _hotspot_cinematic(out: Dictionary, t: float, claim_to := "") -> void:
	var spec: Dictionary = out["cinematic"]
	if claim_to != "":  # the camera is already walking to (or standing at) that waypoint: no second walk
		spec = spec.duplicate(true)
		for st in spec.get("steps", []):
			if str(st.get("to", "")) == claim_to:
				st.erase("move")
				st.erase("to")
	var move_ok := bool(out["continued"]) or str(out["window"]) == "early" or bool(out.get("stays", false))
	var steps_move := false
	for st in spec.get("steps", []):
		steps_move = steps_move or (st.has("move") and st.has("to"))
	for a in journey.hotspot_actions(spec, t, engine, _look_by, move_ok):
		_journey_apply(a)
	if move_ok and steps_move and str(out["window"]) == "final":
		_door_phase = engine.phase_n  # the cinematic is the move: no door walk is latched for this phase


## What the camera holds in the picture for the hotspot window of `node_id` (RunJourney.face_fn): the window's hotspots as points [x, z, 1 for the default, height], which StoryPlayer's `face`
## look frames from wherever the rail is (StoryPlayer.best_facing); [] when there is nothing to frame.
func _window_face(node_id: String, _place: String) -> Array:
	if hotspots == null or not stages.has(active_world) or node_id != engine.node_id:
		return []
	var st: StoryStage = stages[active_world]["stage"]
	if st.map == null:
		return []
	var pts: Array = []
	for h in hotspots.shown(3, true):
		if RunHotspots.window_of(h) != "final":
			continue
		var r := HotspotView.resolve(h["anchor"], st.map, st.crowds)
		if bool(r["ok"]):
			var p: Vector3 = r["pos"]
			pts.append([p.x, p.z, 1.0 if bool(h["default"]) else 0.0, p.y])
	return pts


## The turn (degrees, relative to the rail's facing now, which a glance is added to) toward an actor, thing or waypoint of the scene's map; NAN when it cannot be placed.
func _look_by(target: String) -> float:
	if not stages.has(active_world):
		return NAN
	var st: StoryStage = stages[active_world]["stage"]
	if st.map == null or st.player == null:
		return NAN
	var full := st.player.pose_at(hud.now_t)
	var pose := {"cam": full["cam"], "yaw": float(full.get("rail_yaw", full["yaw"])) + st.free_look.offset}
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
	if _mg != null and _mg.owns_strip():  # a replace activity's controls own the strip: no pad is pressed (H5.6; the lane input is off too)
		input_log.append({"t": hud.now_t, "area": "strip", "owner": "activity_controls", "target": "", "refused_pad": button})
		return
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
	if audio != null:
		audio.track.note_pause(clock.judge_time())  # (a hold the pause ends mutes nothing)
	engine.judge.pause_interrupt(clock.judge_time())
	lane_input.clear()
	lane_input.enabled = false
	_pause_panel.visible = true
	_dim.visible = true
	if _leave_btn != null:
		_leave_btn.visible = run_path != ""  # (the way back to the Warehouse is offered inside a path only)
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


## The pause menu's "Leave this path": the game goes on, and at the end of this phase the way back to the Warehouse is taken.
func _leave_path() -> void:
	request_path_leave()
	_resume()


## Restart the level the player is on, with fresh energy and its authored opening.
func _retry() -> void:
	if audio != null:
		audio.stop()
	Session.run_start_node = _run_world_of(engine.node_id)  # a restart begins at the world's entry scene (its id is the world's id)
	Session.run_start_path = run_path
	if not playtest.is_empty():  # a debug start restarts the scene being played, with the same options
		PlaytestMode.prepare("main" if run_path == "" else run_path, engine.node_id)
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
	if PlaytestMode.active:  # a debug-started run that the crowd left: back to the scene list, not the retry screen
		PlaytestMode.back_to_list(get_tree())
		return
	get_tree().change_scene_to_file("res://src/run/run_over.tscn")


## Debug / playtest: leave this scene for the scene list (the pause panel's "Back to scene list", and the end of a scene when "continue the run" is off).
func _playtest_back() -> void:
	event_log.append({"kind": "playtest_back", "t": clock.audio_time() if clock != null else 0.0, "phase": engine.phase_n, "node": engine.node_id})
	_ended = true
	if virtual_mode:
		return
	if audio != null:
		audio.stop()
	PlaytestMode.back_to_list(get_tree())


func _playtest_save_note() -> void:
	if playtest_overlay == null or _pause_note == null or _pause_note.text.strip_edges() == "":
		return
	playtest_overlay.record("note", _pause_note.text.strip_edges())
	_pause_note.text = ""
	_pause_note.placeholder_text = "Saved to the playtest notes"


# --- paths: the tempo handoff ----------------------------------------------------------------------------------------------------

## The pause menu's "Leave this path" (or a test): the way back to the Warehouse is taken at the end of this phase (from beat 61, once its route is settled), through the passage frame.
func request_path_leave() -> bool:
	if run_path == "" or trial_state != "":
		return false
	if router != null and _route_leave_now():
		return true
	path_leave_requested = true
	return true


## The engine handed the run off ("path_handoff": a portal committed, or an ending's way back) on the downbeat `ev.t`. The other run takes over on that downbeat:
##  * the clock stream becomes the 64-beat silent loop of its tempo (RunAudio, one scheduled item, song time stays one unbroken line);
##  * its own RunEngine begins at its start scene (a path: `start_node`; the Warehouse: "warehouse") on drums alone, the crowd's energy and the phase count carried on, its beat grid starting on the downbeat;
##  * the pads, the note lane, the HUD, the hotspots and the journey follow the new engine; the stages take the new tempo; the passage frame, closed over the last two beats, opens on the new room.
## The old phase's voices fade through the usual phase change. A path that cannot be loaded does not strand the run: the Warehouse goes on by its default exit.
func _path_swap(ev: Dictionary) -> void:
	var t_swap := float(ev["t"])
	var entering := HotspotContract.is_path_route(str(ev["route"]))
	var new_data: RunData
	if entering:
		new_data = _path_cache[str(ev["target"])] if _path_cache.has(str(ev["target"])) else RunData.load_path(str(ev["target"]))
	else:
		new_data = main_data if main_data != null else (_main_cache if _main_cache != null else RunData.load_default())
	var start := ""
	if not new_data.errors.is_empty() or (entering and new_data.path_id == ""):
		push_error("run path '%s' cannot be played: %s" % [str(ev.get("target", "")), "; ".join(PackedStringArray(new_data.errors))])
		path_log.append({"kind": "failed", "t": t_swap, "path": str(ev.get("target", "")), "errors": new_data.errors})
		new_data = data  # stay in this run: its default exit takes the player on
		start = engine.default_route() if data.nodes.has(engine.default_route()) else data.start_node()
	elif entering:
		start = new_data.start_node()
		if OS.get_environment("RW_RUN_PATH_START") != "" and new_data.nodes.has(OS.get_environment("RW_RUN_PATH_START")):
			start = OS.get_environment("RW_RUN_PATH_START")
	else:
		start = main_data.start_node() if main_data != null else new_data.start_node()
		start = "warehouse" if new_data.nodes.has("warehouse") else start
	if start != "" and str(ev.get("start", "")) != "" and new_data.nodes.has(str(ev["start"])) and new_data != data:  # a destination the director locked names the scene of the other run
		start = str(ev["start"])
	elif not entering and new_data != data and new_data.nodes.has(_return_start()):  # (N2.2) a way back the port did not carry (an ending's default exit, the pause menu's leave late in a lap) lands on the checkpoint too
		start = _return_start()
	var swap_clock := new_data != data
	var before := {"bpm": float(data.cfg["timing"]["bpm"]), "beat_s": engine.beat_s}
	var prev_path := run_path
	if swap_clock:
		if audio != null:
			audio.schedule_clock_swap(new_data, t_swap)
		if entering:
			main_data = data
		elif str(ev.get("ending", "")) != "" and prev_path != "":
			Session.run_progress.path_ending(prev_path, str(ev["ending"]))
		data = new_data
		run_path = data.path_id
		if run_path == "":
			main_data = data
	var carried := float(ev["energy"])
	engine = RunEngine.new(data)
	hotspots = RunHotspots.new(data, Session.run_progress.run_flags, Session.run_progress.flags)
	hotspots.preselect = bool((data.cfg.get("choice", {}) as Dictionary).get("preselect", false)) or OS.get_environment("RW_CHOICE_PRESELECT") == "1"  # (an owner decision, off: touch only in the window; the env turns it on for a strip)
	hotspots.ungated_quest_routes = router != null
	engine.hotspots = hotspots
	_wire_track_audio()
	_wire_director()
	engine.arrive(start, t_swap, carried, int(ev["phase"]), int(ev.get("lap_extra", 0)))
	journey = RunJourney.new(data)
	proxy.level = engine.level
	for w in stages:
		(stages[w]["stage"] as StoryStage).set_tempo(float(data.cfg["timing"]["bpm"]))
		if stages[w].has("hotspot_view"):
			(stages[w]["hotspot_view"] as HotspotView).beat_s = engine.beat_s
	pad_view.setup(engine.level, clock)
	pad_view.holding_fn = engine.judge.hold_progress
	pad_view.progress_fn = engine.progress_at
	note_lane.setup(engine.level, clock, pad_view)
	note_lane.state_fn = engine.judge.cue_state
	hud.engine = engine
	hud.data = data
	if trial != null:
		trial.retarget(data)
	_door_phase = -1
	_commit_view = {}
	_sel_t.clear()
	_last_guard_key = -1
	_bot_pressed.clear()
	_bot_released.clear()
	path_log.append({"kind": "enter" if entering else "leave", "t": t_swap, "path": run_path if entering else prev_path, "to": start, "bpm_before": before["bpm"], "bpm_after": float(data.cfg["timing"]["bpm"]),
		"beat_s_before": before["beat_s"], "beat_s_after": engine.beat_s, "energy": carried, "phase": int(ev["phase"]), "ending": str(ev.get("ending", ""))})
	print("RUN %s at t=%.3f: %s -> %s (%.0f -> %.0f BPM, energy %.0f)" % ["entered path " + run_path if entering else "left the path", t_swap, str(ev["from"]), start, before["bpm"], float(data.cfg["timing"]["bpm"]), carried])
	_handle(engine.update(t_swap))


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
	if director != null:
		director.excursion(&"armed")  # (the Bassment is not behind the port: nothing locks before the dungeon takes the run)
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
		trial_begin_now(trial_entry_t, _trial_start_passage, false)


func trial_begin_now(entry_t: float, start_passage: int, direct: bool) -> void:
	if not direct:
		_close_routes({})
		hud.fade_out()
		_gate.visible = false
	trial_state = "in"
	if director != null:
		director.excursion(&"enter")
	if trial.bot == "":
		trial.bot = str(_bot.get("policy", "")) if str(_bot.get("policy", "")) in ["perfect", "none"] else ""
	var carried: Array = []
	var way := str(_trial_entry.get("way", "direct" if direct else "legacy"))
	if router != null:
		var res := _route_enter_bassment(way, start_passage)
		if bool(res.get("applied", false)) and router.state.quest == "bassment":
			start_passage = int(router.state.current_scene().trim_prefix("bassment/"))
			for f in res.get("restore_flags", []):
				carried.append(str(f).trim_prefix("item:"))
	_trial_items = carried.duplicate()
	trial.begin(entry_t, start_passage, direct, carried)
	_trial_passage_seen = trial.engine.flow.passage if trial.engine != null else -1
	engine.phase_n += 1
	trial_log.append({"kind": "entered", "t": hud.now_t, "entry": entry_t, "way": way, "passage": _trial_passage_seen, "carried": carried})


## Left by a death, the victory or the back key: on the downbeat `t_swap` the frame opens on the Warehouse at the hatch, its pack re-enters and the run begins a fresh phase.
func trial_leave(t_swap: float, reason: String) -> void:
	_trial_route_sync()  # (the last passage and the items held, before the dungeon's engine goes)
	trial.deactivate()
	trial_state = ""
	_trial_start_passage = -1
	if director != null:
		director.excursion(&"leave")
	var node := "warehouse" if data.nodes.has("warehouse") else engine.node_id
	var back := _return_start() if router != null and router.state.quest == "bassment" else ""
	if back != "" and data.nodes.has(back):  # (N2.2) the way out of the Bassment lands on the checkpoint: the hub of the location it was entered from
		node = back
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
	trial_log.append({"kind": "left", "t": t_swap, "reason": reason, "to": node})
	if router != null and router.state.quest == "bassment":
		var res := router.commit(0, {"id": "main/" + node, "path": "main", "node": node, "kind": &"quest_return", "quest": "bassment"})
		_after_route_commit(res)
		route_log.append({"kind": "bassment_leave", "t": t_swap, "landed": "main/" + node, "reason": reason, "result": res, "state": router.state.to_dict()})
		port().set_default(router.default_destination())
	_trial_items = []
	_trial_entry = {}
	print("TRIAL left (%s) on the downbeat t=%.3f; the run resumes at phase %d, energy %.1f" % [reason, t_swap, engine.phase_n, engine.energy])
	if OS.get_environment("RW_STORY_QUIT") == "1" and OS.get_environment("RW_TRIAL_LEAVE_QUIT") == "1":
		get_tree().quit()
