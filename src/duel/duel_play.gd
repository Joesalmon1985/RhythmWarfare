class_name DuelPlay
extends Control
## The wizard duel on screen. Two wizards, one song, the same notes at the same time: every two bars each player's phrase is judged
## on their own phone and, if it passed, casts a spell at the other wizard (DuelEngine); the two results meet in a DuelMatch that lands
## the spells and keeps health. Over wifi the opponent's results arrive as messages (DuelNetwork); alone, a DuelBot plays the Apprentice
## (or the Adept or the Archmage) in-process through the very same engine and match.
##
## Scripted runs: RW_DUEL_SOLO=1 (no network), RW_DUEL_SKILL=apprentice|adept|archmage (the rival), RW_DUEL_BOT=perfect|apprentice|adept|archmage
## (plays this wizard), RW_DUEL_VIRTUAL=1 (no audio: song time follows the wall clock, for headless runs), RW_DUEL_QUIT=1 (leave when it ends).
## The end prints one `DUEL_RESULT {...}` line.

const SOLO_SKILLS := ["apprentice", "adept", "archmage"]
const SKILL_TITLES := {"apprentice": "The Apprentice", "adept": "The Adept", "archmage": "The Archmage"}
const HANDSHAKE_TIMEOUT_S := 20.0
const MENU := "res://src/scenes/main_menu.tscn"
const LOBBY := "res://src/duel/duel_lobby.tscn"

static var solo_skill := "apprentice"  # who the lone player faces (set by the lobby)

var rules: DuelRules
var rdata: RunData
var engine: DuelEngine
var duel: DuelMatch
var stage: DuelStage
var pad_view: StoryPadView
var note_lane: StoryNoteLane
var lane_input: LaneInput
var audio: RunAudio
var clock: SongClock
var proxy: StoryRun
var virtual_mode := false
var solo := false
var bot: DuelBot  # plays this wizard (scripted runs)
var opp_engine: DuelEngine  # solo: the rival's side
var opp_bot: DuelBot
var phase := "sync"  # sync | countdown | play | over
var ended := false
var trace: Array = []  # what happened, for scripted checks
var leave_launcher: Callable = func(where: String) -> void: get_tree().change_scene_to_file(where)

var _pressed_pad: Dictionary = {}
var _wait_since := 0.0
var _go_at_usec := 0
var _start_usec := 0
var _loaded_peer := false
var _sync_since := 0.0
var _sent := {}  # phrase -> wall time my result was sent
var _end_ev: Dictionary = {}
var _end_shown := false
var _end_wall := 0.0
var _panel: PanelContainer
var _end_label: Label
var _rematch_btn: Button
var _my_rematch := false
var _opp_rematch := false
var _last_t := 0.0
var _quit_after := false
var _names: Array = ["You", "Rival"]
var _opp_skill := "apprentice"


func _ready() -> void:
	theme = UiStyle.theme()
	rules = DuelRules.load_default()
	rdata = RunData.load_default()
	if not rules.errors.is_empty() or not rdata.errors.is_empty():
		_fatal("The duel data is invalid:\n" + "\n".join(PackedStringArray(rules.errors + rdata.errors)))
		return
	virtual_mode = OS.get_environment("RW_DUEL_VIRTUAL") == "1"
	_quit_after = OS.get_environment("RW_DUEL_QUIT") == "1"
	solo = OS.get_environment("RW_DUEL_SOLO") == "1" or DuelNetwork.state != DuelNetwork.State.CONNECTED
	_opp_skill = OS.get_environment("RW_DUEL_SKILL") if OS.get_environment("RW_DUEL_SKILL") != "" else solo_skill
	if not SOLO_SKILLS.has(_opp_skill):
		_opp_skill = "apprentice"
	engine = DuelEngine.new(rules, rdata)
	engine.begin()
	duel = DuelMatch.new(rules)
	var seed_value := int(OS.get_environment("RW_DUEL_SEED")) if OS.get_environment("RW_DUEL_SEED") != "" else int(Time.get_ticks_usec() % 100000)
	var bot_skill := OS.get_environment("RW_DUEL_BOT")
	if bot_skill != "":
		bot = DuelBot.from_skill(rules, bot_skill if SOLO_SKILLS.has(bot_skill) else "archmage", seed_value + 1)
		if bot_skill == "perfect":
			bot.hit = 1.0
			bot.sigma_ms = 0.0
			bot.strays = 0.0
	if solo:
		opp_engine = DuelEngine.new(rules, rdata)
		opp_engine.begin()
		opp_bot = DuelBot.from_skill(rules, _opp_skill, seed_value + 2)
		_names = [DuelNetwork.my_name if DuelNetwork.my_name != "" else "You", SKILL_TITLES[_opp_skill]]
	else:
		_names = [DuelNetwork.my_name, DuelNetwork.opp_name if DuelNetwork.opp_name != "" else "Rival"]
	proxy = StoryRun.new()
	proxy.level = engine.level
	proxy.crowd = CrowdController.new()
	if virtual_mode:
		clock = SongClock.new(null)
	else:
		audio = RunAudio.new()
		add_child(audio)
		audio.configure(rdata)
		clock = SongClock.new(audio)
		clock.calibration_ms = Session.calibration_ms
		var m: Dictionary = rules.cfg["music"]
		audio.on_event({"kind": "phase_start", "node": "duel", "phase": 1, "t": 0.0, "treatment": m["treatment"], "audio": m["audio"]})
		audio.on_event({"kind": "mix", "t": 0.0001, "gains": {"drums": 1.0, "bass": 0.7, "other": 0.55}})
		audio.on_event({"kind": "reveal", "t": 0.0002})
	_build_layout()
	_sync_since = _wall()
	if solo:
		_begin_countdown(0.6)
	else:
		DuelNetwork.send({"t": "loaded", "r": DuelNetwork.round_no})
		_check_handshake()


func _fatal(message: String) -> void:
	push_error(message)
	var l := Label.new()
	l.text = message
	l.set_anchors_preset(Control.PRESET_FULL_RECT)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(l)
	ended = true


func _wall() -> float:
	return float(Time.get_ticks_msec()) / 1000.0


# --- layout ---------------------------------------------------------------------------------------------------------------------

func _build_layout() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bg := ColorRect.new()
	bg.color = Color(0.02, 0.02, 0.06)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	var pad_share: float = Session.PAD_SIZES[clampi(Session.pad_size, 0, 2)]
	var split := 1.0 - pad_share
	stage = DuelStage.new()
	stage.name = "Stage"
	stage.anchor_right = 1.0
	stage.anchor_bottom = split
	stage.setup(rules.max_hp10(), float(rules.cfg["timing"]["flight_s"]), int(rules.cfg["power"]["streak_cap"]))
	stage.backdrop = load("res://assets/trial/scenes/stacks.png") as Texture2D
	stage.wizard = load("res://assets/trial/art/wizard.png") as Texture2D
	stage.names = _names
	stage.reduced_effects = Session.reduced_effects
	add_child(stage)
	var assets := StoryAssets.load_art("night_one")
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
	var deck := StoryDeck.new()
	deck.setup(assets, proxy, null)
	deck.reduced = Session.reduced_effects
	pad_view.deck_under = deck.draw_under
	pad_view.deck_over = deck.draw_over
	pad_view.setup_skin(deck)
	add_child(pad_view)
	var shade := StoryLaneShade.new()
	shade.pad_view = pad_view
	shade.strength = 0.5 if Session.high_contrast else 0.3
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)
	note_lane = StoryNoteLane.new()
	note_lane.glow_tex = assets.sprite("glow").get("tex", null)
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
	lane_input.button_pressed.connect(func(b: int, touch: int) -> void:
		if phase == "play" or phase == "countdown":
			engine.press(b, clock.judge_time(), touch))
	lane_input.button_released.connect(func(b: int, touch: int) -> void:
		if phase == "play" or phase == "countdown":
			engine.release(b, clock.judge_time(), touch))
	_build_end_panel()
	stage.banner = "Waiting for the other wizard..." if not solo else ""
	stage.banner_color = Color(0.8, 0.85, 1.0)


func _build_end_panel() -> void:
	_panel = PanelContainer.new()
	_panel.add_theme_stylebox_override("panel", UiStyle.panel_box())
	_panel.visible = false
	_panel.set_anchors_preset(Control.PRESET_CENTER)
	_panel.anchor_left = 0.5
	_panel.anchor_right = 0.5
	_panel.anchor_top = 0.28
	_panel.anchor_bottom = 0.28
	_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	add_child(_panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	box.custom_minimum_size = Vector2(420, 0)
	_panel.add_child(box)
	_end_label = Label.new()
	_end_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_end_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(_end_label)
	_rematch_btn = UiStyle.button("Rematch", _on_rematch, 0, 56)
	box.add_child(_rematch_btn)
	box.add_child(UiStyle.button("Leave", func() -> void: _leave(false), 0, 56))


# --- handshake and countdown -------------------------------------------------------------------------------------------------------

func _check_handshake() -> void:
	if phase != "sync" or solo:
		return
	if DuelNetwork.role == "host" and _loaded_peer and _go_at_usec == 0:
		DuelNetwork.send({"t": "go", "r": DuelNetwork.round_no})
		_go_at_usec = Time.get_ticks_usec() + int(DuelNetwork.one_way_s() * 1_000_000.0)  # the other phone hears "go" half a round trip from now


func _begin_countdown(extra_wait: float = 0.0) -> void:
	phase = "countdown"
	stage.banner = ""
	if virtual_mode:
		_start_usec = Time.get_ticks_usec() + int(extra_wait * 1_000_000.0)
	else:
		clock.begin_countdown(engine.count_in_s() + extra_wait)
	trace.append({"kind": "countdown", "wall": _wall()})


# --- frame ----------------------------------------------------------------------------------------------------------------------

func _process(_delta: float) -> void:
	if engine == null or clock == null or ended:
		return
	if not solo:
		_pump_network()
	match phase:
		"sync":
			if not solo and _wall() - _sync_since > HANDSHAKE_TIMEOUT_S:
				stage.banner = "No answer from the other wizard"
				_finish_leave_soon()
				return
			if not solo and DuelNetwork.role == "host" and _go_at_usec != 0 and Time.get_ticks_usec() >= _go_at_usec:
				_begin_countdown()
		"countdown", "play":
			var t: float
			var audio_t: float
			if virtual_mode:
				t = float(Time.get_ticks_usec() - _start_usec) / 1_000_000.0 - engine.count_in_s()
				audio_t = t
				clock.state = SongClock.State.PAUSED
				clock._frozen = t
			else:
				clock.tick()
				t = clock.judge_time()
				audio_t = clock.audio_time()
			_advance(t, audio_t)
		"over":
			_over_step()


func _advance(t: float, audio_t: float) -> void:
	_last_t = audio_t
	if t >= 0.0 and phase == "countdown":
		phase = "play"
	_banner_for(t)
	if not duel.finished:
		if bot != null:
			for a in bot.step(engine, t):
				pad_view.button_down[int(a["pad"])] = bool(a["down"])
		if solo:
			opp_bot.step(opp_engine, t)
			for ev in opp_engine.update(t):
				if str(ev["kind"]) == "result":
					_on_result(1, ev)
		for ev in engine.update(t):
			match str(ev["kind"]):
				"judge":
					_on_judge_event(ev["event"] as Dictionary)
				"result":
					_on_result(0, ev)
	else:
		engine.update(t)
	stage.phrase_text = "" if phase == "countdown" else "Phrase %d  ·  tier %d  ·  %s" % [engine.phrase_at(t) + 1, rules.tier_of(engine.phrase_at(t)), "drums" if rules.family_of(engine.phrase_at(t)) == "drums" else "bass"]
	if _waiting_for_opponent():
		stage.sub_banner = "waiting for %s..." % str(_names[1])
	elif phase == "play" and t < 1.2:
		stage.sub_banner = ""
	note_lane.queue_redraw()
	if duel.finished and phase != "over" and stage.pending_spells() == 0:
		_enter_over()


func _banner_for(t: float) -> void:
	if phase == "countdown" or (phase == "play" and t < 0.9):
		var cin := engine.count_in_s()
		if t < 0.0:
			var k := int(ceil(-t / (cin / 3.0)))
			stage.banner = str(clampi(k, 1, 3))
			stage.banner_color = Color(1.0, 0.9, 0.55)
		else:
			stage.banner = "CAST!"
			stage.banner_color = Color(1.0, 0.6, 0.35)
		stage.sub_banner = "same notes, same time. pass a phrase to cast." if t < 0.0 else ""
	elif not duel.finished and phase == "play":
		if stage.banner in ["CAST!", "1", "2", "3"]:
			stage.banner = ""
			stage.sub_banner = ""


func _waiting_for_opponent() -> bool:
	if solo or duel.finished or phase != "play":
		return false
	for j in _sent:
		if j >= duel.phrase and _wall() - float(_sent[j]) > 0.8:
			return true
	return false


## One of the two wizards finished a phrase.
func _on_result(side: int, res: Dictionary) -> void:
	var j := int(res["j"])
	if side == 0:
		_sent[j] = _wall()
		if not solo:
			var msg := res.duplicate()
			msg["t"] = "res"
			msg["r"] = DuelNetwork.round_no
			msg.erase("kind")
			DuelNetwork.send(msg)
		trace.append({"kind": "mine", "j": j, "cast": res["cast"], "power10": res["power10"], "credit": res["credit"]})
	for ev in duel.submit(side, j, res):
		_on_match_event(ev)


func _on_match_event(ev: Dictionary) -> void:
	match str(ev["kind"]):
		"phrase":
			var res: Array = ev["results"]
			stage.streak = [int((res[0] as Dictionary).get("streak", 0)), int((res[1] as Dictionary).get("streak", 0))]
			stage.add_phrase(ev)
			_sent.erase(int(ev["j"]))
			trace.append({"kind": "phrase", "j": ev["j"], "hp10": ev["hp10"], "spells": (ev["spells"] as Array).size()})
		"sudden_death":
			stage.sub_banner = "SUDDEN DEATH"
			stage.banner = "SUDDEN DEATH"
			stage.banner_color = Color(1.0, 0.4, 0.4)
		"end":
			_end_ev = ev
			engine.stopped = true
			if opp_engine != null:
				opp_engine.stopped = true
			var w := int(ev["winner"])
			if w >= 0:
				stage.knock_out(1 - w)
			trace.append({"kind": "end", "winner": w, "reason": ev["reason"], "hp10": ev["hp10"]})
			print("DUEL_RESULT ", JSON.stringify({"winner": w, "reason": ev["reason"], "hp10": ev["hp10"], "phrases": duel.phrase, "casts": duel.casts, "role": DuelNetwork.role, "solo": solo,
				"credit": [snappedf(duel.total_credit[0], 0.001), snappedf(duel.total_credit[1], 0.001)]}))


func _pump_network() -> void:
	for msg in DuelNetwork.drain():
		var kind := str(msg.get("t", ""))
		if kind == "closed" or kind == "bye":
			if not duel.finished:
				for ev in duel.forfeit(1):
					_on_match_event(ev)
				stage.sub_banner = "%s left the duel" % str(_names[1])
			continue
		if int(msg.get("r", DuelNetwork.round_no)) != DuelNetwork.round_no:
			continue  # a message of an earlier duel
		match kind:
			"loaded":
				_loaded_peer = true
				_check_handshake()
			"go":
				if phase == "sync" and DuelNetwork.role == "join":
					_begin_countdown()
			"res":
				_on_result(1, msg)
			"rematch":
				_opp_rematch = true
				_maybe_rematch()


func _on_judge_event(ev: Dictionary) -> void:
	var pad: int = int(ev.get("pad", 0))
	var wall := _wall()
	match ev["kind"]:
		"perfect":
			pad_view.show_feedback(pad, "PERFECT", Color(1.0, 0.95, 0.6), wall)
		"great", "good", "ok":
			pad_view.show_feedback(pad, "GREAT", Color(0.7, 0.95, 0.7), wall)
		"hold_start":
			pad_view.show_feedback(pad, "HOLD", Color(0.75, 0.85, 1.0), wall)
		"hold_complete":
			pad_view.flash_complete(pad, wall)
		"miss", "hold_fail":
			pad_view.show_feedback(pad, "MISS", Color(1.0, 0.5, 0.45), wall)


# --- the end ----------------------------------------------------------------------------------------------------------------------

func _enter_over() -> void:
	phase = "over"
	_end_wall = _wall()
	var w := int(_end_ev["winner"])
	var reason := str(_end_ev["reason"])
	if w == 0:
		stage.banner = "YOU WIN"
		stage.banner_color = Color(1.0, 0.88, 0.4)
	elif w == 1:
		stage.banner = "YOU LOSE"
		stage.banner_color = Color(1.0, 0.45, 0.4)
	else:
		stage.banner = "DRAW"
		stage.banner_color = Color(0.85, 0.9, 1.0)
	stage.sub_banner = {"ko": "knocked out", "time": "the song ended with more health left", "sudden": "sudden death", "draw": "both fell together", "forfeit": "the other wizard left"}.get(reason, "")
	if _quit_after:
		_finish_leave_soon()


func _over_step() -> void:
	if _end_shown or _wall() - _end_wall < 1.4:
		return
	_end_shown = true
	var hp: Array = _end_ev["hp10"]
	var mine := engine.results.filter(func(r: Dictionary) -> bool: return bool(r["cast"])).size()
	_end_label.text = "%s  %.1f  –  %.1f  %s\nspells cast %d of %d phrases" % [str(_names[0]), float(hp[0]) / 10.0, float(hp[1]) / 10.0, str(_names[1]), mine, engine.results.size()]
	_end_label.add_theme_font_size_override("font_size", 22)
	_panel.visible = true
	if str(_end_ev["reason"]) == "forfeit":
		_rematch_btn.disabled = true
	_rematch_btn.grab_focus()


func _on_rematch() -> void:
	if solo:
		_reload()
		return
	_my_rematch = true
	_rematch_btn.disabled = true
	_rematch_btn.text = "Waiting for %s..." % str(_names[1])
	DuelNetwork.send({"t": "rematch", "r": DuelNetwork.round_no})
	_maybe_rematch()


func _maybe_rematch() -> void:
	if _my_rematch and _opp_rematch:
		DuelNetwork.round_no += 1
		_reload()


func _reload() -> void:
	ended = true
	if audio != null:
		audio.stop()
	get_tree().reload_current_scene.call_deferred()


func _leave(_forfeit: bool) -> void:
	ended = true
	if audio != null:
		audio.stop()
	if not solo:
		DuelNetwork.close("left")
	leave_launcher.call(MENU)


func _finish_leave_soon() -> void:
	ended = true
	if audio != null:
		audio.stop()
	await get_tree().create_timer(0.6).timeout
	if not solo:
		DuelNetwork.close("left")
	if _quit_after or OS.get_environment("RW_DUEL_QUIT") == "1":
		get_tree().quit()
	else:
		leave_launcher.call(MENU)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") and not ended:
		get_viewport().set_input_as_handled()
		_leave(true)
