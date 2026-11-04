extends Control
## The Deathtrap Dungeon opening: a fixed illustrated scene, a short description and floating choices over the top of the four pads. The only inputs are the
## choices and the pads. Selecting a choice starts a short rhythm phrase on the audio clock (RunAudio, the same WAV/MIDI packs and PadJudge as the run); a pass
## shows the consequence and the next passage's choices, a failed phrase can be retried, and a fight plays an outcome animation first.
##
## Scripted play: RW_TRIAL_VIRTUAL=1 (no audio, a stepped clock), RW_TRIAL_BOT=perfect|none|no_fights (perfect plays every phrase, no_fights every phrase but the fights), RW_TRIAL_CHOICES=0,1,0 (the choice
## indexes picked in turn), RW_TRIAL_UNTIL=<passage> (quit when reached with RW_STORY_QUIT=1).

const COUNTDOWN_S := 1.2
const OUTCOME_S := 1.6
const SCENE_TEXT := Color(0.93, 0.92, 1.0)

var tdata: TrialData
var rdata: RunData
var flow: TrialFlow
var audio: RunAudio
var clock: SongClock
var level := Level.new()
var judge := PadJudge.new()
var phrase := TrialPhrase.new()
var pad_view: StoryPadView
var note_lane: StoryNoteLane
var lane_input: LaneInput
var proxy: StoryRun
var virtual_mode := false
var transport: StemTransport:  # the names the recording harness (tools/story/record_music.gd) looks for
	get:
		return audio
var event_log: Array:
	get:
		return trace
var bot := ""  # "perfect" | "none" | ""
var exit_launcher: Callable = func(_where: String) -> void: pass  # set in _ready; tests replace it
var mode := "scene"  # scene | lead | phrase | outcome | ended
var trace: Array = []  # [{kind, ...}] what happened, for scripted checks

var _stage_host: Control
var _pic: TextureRect
var _shade: ColorRect
var _flash: ColorRect
var _title: Label
var _panel: PanelContainer
var _desc: Label
var _news: Label
var _msg: Label
var _choice_layer: Control
var _buttons: Array = []
var _base_pos: Array = []
var _enemy: TextureRect
var _enemy_id := ""
var _outcome := {}
var _vt := -COUNTDOWN_S
var _phase_counter := 0
var _pressed: Dictionary = {}
var _released: Dictionary = {}
var _script_choices: PackedStringArray = PackedStringArray()
var _script_i := 0
var _scene_since := 0.0
var _until := -1
var _last_t := 0.0
var _beat_s := 60.0 / 174.0
var _selected_choice: Dictionary = {}
var _selected_enc := ""


func _ready() -> void:
	theme = UiStyle.theme()
	tdata = TrialData.load_default()
	rdata = RunData.load_default()
	if not tdata.errors.is_empty() or not rdata.errors.is_empty():
		_fatal("The Trial data is invalid:\n" + "\n".join(PackedStringArray(tdata.errors + rdata.errors)))
		return
	virtual_mode = OS.get_environment("RW_TRIAL_VIRTUAL") == "1"
	if bot == "":
		bot = OS.get_environment("RW_TRIAL_BOT")
	if OS.has_environment("RW_TRIAL_CHOICES"):
		_script_choices = OS.get_environment("RW_TRIAL_CHOICES").split(",")
	if OS.has_environment("RW_TRIAL_UNTIL"):
		_until = int(OS.get_environment("RW_TRIAL_UNTIL"))
	exit_launcher = func(where: String) -> void:
		Session.run_start_node = "warehouse" if where == "warehouse" else ""
		get_tree().change_scene_to_file("res://src/run/run_play.tscn")
	_beat_s = 60.0 / float(rdata.cfg["timing"]["bpm"])
	flow = TrialFlow.new(tdata)
	_setup_judge()
	if virtual_mode:
		clock = SongClock.new(null)
	else:
		audio = RunAudio.new()
		add_child(audio)
		audio.configure(rdata)
		clock = SongClock.new(audio)
		clock.calibration_ms = Session.calibration_ms
	_build_layout()
	_ambient(0.0)
	if virtual_mode:
		_step_virtual(_vt)
	else:
		clock.begin_countdown(COUNTDOWN_S)
	_show_passage()


func _fatal(message: String) -> void:
	push_error(message)
	var l := Label.new()
	l.text = message
	l.set_anchors_preset(Control.PRESET_FULL_RECT)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(l)
	mode = "ended"


func _setup_judge() -> void:
	level.mode = "defense"
	level.bpm = float(rdata.cfg["timing"]["bpm"])
	level.ticks_per_beat = 960
	level.beats_per_bar = 4
	level.sequence_threshold = tdata.raw.get("pass_credit", 0.6)
	var w: Dictionary = rdata.cfg["judgement"]["windows_ms"]
	judge.perfect_s = float(w["perfect"]) / 1000.0
	judge.great_s = float(w["great"]) / 1000.0
	judge.accept_s = float(w["accept"]) / 1000.0
	judge.complete_s = float(rdata.cfg["judgement"]["hold_complete_s"])
	judge.setup(level.notes, [])
	phrase.setup(level, judge, level.bpm, float(tdata.raw.get("pass_credit", 0.6)))
	proxy = StoryRun.new()
	proxy.level = level
	proxy.crowd = CrowdController.new()


# --- layout ---------------------------------------------------------------------------------------------------------------

func _build_layout() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bg := ColorRect.new()
	bg.color = Color(0.02, 0.02, 0.06)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	var pad_share: float = Session.PAD_SIZES[clampi(Session.pad_size, 0, 2)]
	var split := 1.0 - pad_share
	_stage_host = Control.new()
	_stage_host.name = "Scene"
	_stage_host.anchor_right = 1.0
	_stage_host.anchor_bottom = split
	_stage_host.clip_contents = true
	_stage_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_stage_host)
	_pic = TextureRect.new()
	_pic.set_anchors_preset(Control.PRESET_FULL_RECT)
	_pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_pic.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	_pic.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_pic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stage_host.add_child(_pic)
	_shade = ColorRect.new()
	_shade.color = Color(0, 0, 0, 0.0)
	_shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stage_host.add_child(_shade)
	_enemy = TextureRect.new()
	_enemy.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_enemy.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
	_enemy.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_enemy.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_enemy.visible = false
	_stage_host.add_child(_enemy)
	_title = Label.new()
	_title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_title.add_theme_color_override("font_color", Color(1.0, 0.82, 0.5))
	_title.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_title.add_theme_constant_override("outline_size", 6)
	_stage_host.add_child(_title)
	_panel = PanelContainer.new()
	_panel.add_theme_stylebox_override("panel", StoryStyle.panel_box(StoryStyle.EDGE))
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stage_host.add_child(_panel)
	var pv := VBoxContainer.new()
	pv.add_theme_constant_override("separation", 4)
	pv.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_panel.add_child(pv)
	_news = Label.new()
	_news.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_news.add_theme_color_override("font_color", Color(0.55, 1.0, 0.85))
	_news.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pv.add_child(_news)
	_desc = Label.new()
	_desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_desc.add_theme_color_override("font_color", SCENE_TEXT)
	_desc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pv.add_child(_desc)
	_choice_layer = Control.new()
	_choice_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	_choice_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stage_host.add_child(_choice_layer)
	_msg = Label.new()
	_msg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_msg.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_msg.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.95))
	_msg.add_theme_constant_override("outline_size", 8)
	_msg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stage_host.add_child(_msg)
	_flash = ColorRect.new()
	_flash.color = Color(1, 1, 1, 0)
	_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stage_host.add_child(_flash)
	# the pads: the same skin as the run
	var assets := StoryAssets.load_art("night_one")
	pad_view = StoryPadView.new()
	pad_view.name = "Pads"
	pad_view.anchor_top = split
	pad_view.anchor_right = 1.0
	pad_view.anchor_bottom = 1.0
	pad_view.setup(level, clock)
	pad_view.high_contrast = Session.high_contrast
	pad_view.reduced_effects = Session.reduced_effects
	pad_view.show_keys = Session.show_keys
	pad_view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pad_view.clip_contents = true
	pad_view.show_reward = false
	pad_view.holding_fn = judge.hold_progress
	pad_view.progress_fn = func(_t: float) -> Dictionary: return phrase.progress() if mode == "phrase" and phrase.count > 0 else {}
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
	note_lane.setup(level, clock, pad_view)
	note_lane.travel_s = Session.cue_lead_in_s
	note_lane.high_contrast = Session.high_contrast
	note_lane.reduced_effects = Session.reduced_effects
	note_lane.state_fn = judge.cue_state
	add_child(note_lane)
	lane_input = LaneInput.new()
	add_child(lane_input)
	lane_input.rect_provider = pad_view.button_rects
	lane_input.button_pressed.connect(func(b: int, touch: int) -> void:
		if mode == "phrase":
			judge.press(b, clock.judge_time(), touch))
	lane_input.button_released.connect(func(b: int, touch: int) -> void:
		if mode == "phrase":
			judge.release(b, clock.judge_time(), touch))
	_stage_host.resized.connect(_layout)
	_layout()


func _fs() -> int:
	return int(clampf(_stage_host.size.y * 0.052, 11.0, 22.0))


func _layout() -> void:
	if _stage_host == null:
		return
	var w := _stage_host.size.x
	var h := _stage_host.size.y
	var fs := _fs()
	_title.add_theme_font_size_override("font_size", int(fs * 1.35))
	_title.position = Vector2(w * 0.025, h * 0.03)
	_desc.add_theme_font_size_override("font_size", fs)
	_news.add_theme_font_size_override("font_size", fs)
	_msg.add_theme_font_size_override("font_size", int(fs * 1.9))
	_panel.position = Vector2(w * 0.025, h * 0.03 + fs * 2.2)
	_panel.custom_minimum_size = Vector2(w * 0.5, 0)
	_panel.size = Vector2(w * 0.5, 10)
	var es := minf(h * 0.55, w * 0.3)
	_enemy.size = Vector2(es, es)
	_enemy.pivot_offset = _enemy.size * 0.5
	_enemy.position = Vector2(w * 0.74 - es * 0.5, h * 0.12)
	_place_choices()


func _fit_panel() -> void:
	_panel.custom_minimum_size = Vector2(_stage_host.size.x * 0.5, 0)
	_panel.size = Vector2(_stage_host.size.x * 0.5, 0)
	_panel.reset_size.call_deferred()
	_panel.size = Vector2(_stage_host.size.x * 0.5, 0)


func _place_choices() -> void:
	var w := _stage_host.size.x
	var h := _stage_host.size.y
	var fs := _fs()
	var bw := minf(w * 0.42, 460.0)
	var bh := clampf(h * 0.17, 46.0, 84.0)
	var n := _buttons.size()
	var gap := bh * 0.25
	var total := n * bh + (n - 1) * gap
	var y0 := h - total - h * 0.06
	_base_pos.clear()
	for i in n:
		var b: Button = _buttons[i]
		b.size = Vector2(bw, bh)
		b.add_theme_font_size_override("font_size", int(fs * 1.05))
		var p := Vector2(w * 0.975 - bw, y0 + i * (bh + gap))
		_base_pos.append(p)
		b.position = p


# --- passage ---------------------------------------------------------------------------------------------------------------

func _texture(path: String) -> Texture2D:
	return load(path) as Texture2D


func _show_passage() -> void:
	var p := flow.current()
	_pic.texture = _texture(str(tdata.scenes[str(p["scene"])]["file"]))
	_title.text = str(p["title"]).to_upper()
	_desc.text = str(p["text"])
	var news := ""
	if flow.failure != "":
		news = flow.failure
	elif flow.consequence != "":
		news = flow.consequence
	_news.text = news
	_news.visible = news != ""
	_msg.text = ""
	_shade.color = Color(0, 0, 0, 0.0)
	_enemy.visible = false
	_enemy_id = ""
	for b in _buttons:
		b.queue_free()
	_buttons.clear()
	var cs := flow.choices()
	for i in cs.size():
		var c: Dictionary = cs[i]
		var b := Button.new()
		b.theme = StoryStyle.theme()
		b.focus_mode = Control.FOCUS_NONE
		b.text = ("Try again: " if i == flow.retry_index else "") + str(c["label"])
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.set_meta("index", i)
		b.pressed.connect(func() -> void: pick(i))
		_choice_layer.add_child(b)
		_buttons.append(b)
	_place_choices()
	_desc.visible = true
	_fit_panel()
	_panel.visible = true
	_choice_layer.visible = true
	mode = "scene"
	_scene_since = _last_t
	trace.append({"kind": "passage", "passage": flow.passage})
	if _until > 0 and flow.passage == _until:
		print("TRIAL reached passage %d" % flow.passage)
		if OS.get_environment("RW_STORY_QUIT") == "1":
			get_tree().quit()


## The player selects choice `i` (a tap on a floating choice, or a script).
func pick(i: int) -> void:
	if mode != "scene" or flow == null:
		return
	var r := flow.select(i)
	match str(r["kind"]):
		"phrase":
			_begin_attempt(r)
		"move":
			trace.append({"kind": "move", "passage": flow.passage})
			_show_passage()
		"exit":
			mode = "ended"
			trace.append({"kind": "exit", "to": str(r["exit"])})
			if audio != null:
				audio.stop()
			exit_launcher.call(str(r["exit"]))


# --- the phrase ------------------------------------------------------------------------------------------------------------

func _now() -> float:
	return _vt if virtual_mode else clock.audio_time()


func _ambient(t: float) -> void:
	_phase_counter += 1
	_schedule_group(t, {"drums": 0.0, "bass": 0.0, "other": 0.5})


func _schedule_group(t: float, gains: Dictionary) -> void:
	if audio == null:
		return
	var m: Dictionary = tdata.raw["music"]
	audio.on_event({"kind": "phase_start", "node": "trial", "phase": _phase_counter, "t": t, "treatment": m["treatment"], "audio": m["audio"]})
	audio.on_event({"kind": "mix", "t": t + 0.0001, "gains": gains})
	audio.on_event({"kind": "reveal", "t": t + 0.0002})


func _begin_attempt(r: Dictionary) -> void:
	var spec: Dictionary = r["phrase"]
	var t_now := _now()
	var lead := float(tdata.raw.get("lead_beats", 4))
	var q := ceilf(t_now / _beat_s + lead) * _beat_s
	var pack: Dictionary = rdata.packs[str(tdata.raw["music"]["chart"])]
	judge.update(t_now)
	var n := phrase.start(pack, spec, q)
	pad_view.refresh()
	note_lane.refresh()
	_phase_counter += 1
	var fam_gains := {"drums": 1.0, "bass": 0.0, "other": 0.45} if str(spec["family"]) == "drums" else {"drums": 0.5, "bass": 1.0, "other": 0.45}
	_schedule_group(q, fam_gains)
	_selected_choice = r["choice"]
	_selected_enc = str(r["encounter"])
	_choice_layer.visible = false
	_news.visible = false
	_msg.text = ""
	if _selected_enc != "":
		var enc: Dictionary = tdata.encounters[_selected_enc]
		_enemy.texture = _texture(str(enc["portrait"]))
		_enemy.visible = true
		_enemy_id = _selected_enc
		_news.text = str(enc["intro"])
		_news.visible = true
	_desc.visible = false  # during a phrase the scene is left clear: only the fight's intro line stays
	_panel.visible = _news.visible
	_fit_panel()
	mode = "lead"
	trace.append({"kind": "attempt", "passage": flow.passage, "choice": flow.selected, "start": q, "cues": n, "family": spec["family"], "tier": spec["tier"]})


func _end_attempt(res: Dictionary) -> void:
	var r := flow.phrase_done(bool(res["passed"]), float(res["credit"]))
	trace.append({"kind": "result", "result": r["kind"], "credit": res["credit"], "fight": r["fight"]})
	var t_after := ceilf((_now() + 0.3) / _beat_s) * _beat_s
	_phase_counter += 1
	_schedule_group(t_after, {"drums": 0.0, "bass": 0.0, "other": 0.5})
	if bool(r["fight"]):
		_outcome = {"t0": _now(), "kind": str(r["outcome"])}
		mode = "outcome"
		_msg.text = "FLY DOWN!" if str(r["outcome"]) == "win" else "STUNG!"
		_msg.add_theme_color_override("font_color", Color(0.6, 1.0, 0.8) if str(r["outcome"]) == "win" else Color(1.0, 0.55, 0.45))
		return
	_show_passage()


func _animate_outcome(t: float) -> void:
	var k := clampf((t - float(_outcome["t0"])) / OUTCOME_S, 0.0, 1.0)
	var enc: Dictionary = tdata.encounters.get(_enemy_id, {})
	var win := str(_outcome["kind"]) == "win"
	if win:
		_enemy.texture = _texture(str(enc["portrait_hit"])) if k > 0.12 else _enemy.texture
		_enemy.rotation = k * TAU * 1.5
		_enemy.position.y = _stage_host.size.y * 0.12 + k * k * _stage_host.size.y * 0.7
		_enemy.modulate = Color(1, 1, 1, 1.0 - clampf((k - 0.5) * 2.0, 0.0, 1.0))
		_flash.color = Color(1, 1, 1, clampf(0.7 - k * 4.0, 0.0, 0.7))
	else:
		var lunge := sin(k * PI)
		_enemy.scale = Vector2.ONE * (1.0 + lunge * 0.6)
		_enemy.position = Vector2(_stage_host.size.x * 0.74 - _enemy.size.x * 0.5 - lunge * _stage_host.size.x * 0.25, _stage_host.size.y * 0.12 + lunge * _stage_host.size.y * 0.1)
		_flash.color = Color(1.0, 0.1, 0.05, clampf(sin(k * PI * 2.0) * 0.35, 0.0, 0.35))
		_stage_host.position.x = sin(k * 40.0) * 6.0 * (1.0 - k)
	if k >= 1.0:
		_enemy.rotation = 0.0
		_enemy.scale = Vector2.ONE
		_enemy.modulate = Color.WHITE
		_flash.color = Color(1, 1, 1, 0)
		_stage_host.position = Vector2.ZERO
		_layout()
		_show_passage()


# --- frame loop ------------------------------------------------------------------------------------------------------------

func _process(delta: float) -> void:
	if flow == null or clock == null or mode == "ended" and not virtual_mode:
		return
	if virtual_mode:
		_vt += 1.0 / 30.0
		_step_virtual(_vt)
		return
	clock.tick()
	if clock.state == SongClock.State.PLAYING:
		_advance(clock.judge_time(), clock.audio_time(), delta)


func _step_virtual(t: float) -> void:
	clock.state = SongClock.State.PAUSED
	clock._frozen = t
	_advance(t, t, 1.0 / 30.0)


## Advances the scene by one frame at song time `t` (judge time) / `audio_t` (what is heard). Tests drive it directly.
func _advance(t: float, audio_t: float, _delta: float) -> void:
	_last_t = audio_t
	_bot_step(t)
	var res := judge.drain_events()
	for ev in res:
		_on_judge_event(ev)
	if mode == "lead" and audio_t >= phrase.t0 - 0.05:
		mode = "phrase"
	if mode == "lead" or mode == "phrase":
		var count := phrase.t0 - audio_t
		_msg.text = ("%s\n%s" % [str(_selected_choice.get("label", "")), str(ceili(count / _beat_s))]) if count > _beat_s * 0.5 and mode == "lead" else (str(tdata.phrases[str(_selected_choice["phrase"])]["label"]).to_upper() if mode == "phrase" else "")
		_msg.add_theme_color_override("font_color", Color(1, 1, 1, 0.9))
		var r := phrase.update(t)
		if not r.is_empty() and (mode == "phrase"):
			_end_attempt(r)
	elif mode == "outcome":
		_animate_outcome(audio_t)
	else:
		judge.update(t)
	var f := 0.0
	for i in _buttons.size():  # the choices float
		var b: Button = _buttons[i]
		b.position = (_base_pos[i] as Vector2) + Vector2(0.0, sin(audio_t * 1.7 + float(i) * 1.3) * _stage_host.size.y * 0.012)
		f += 1.0
	_shade.color = Color(0, 0, 0, 0.35 if mode == "phrase" or mode == "lead" else 0.0)
	if _enemy.visible and mode in ["lead", "phrase"]:
		_enemy.position.y = _stage_host.size.y * 0.12 + sin(audio_t * 3.0) * _stage_host.size.y * 0.015
	note_lane.queue_redraw()
	if mode == "scene" and _script_i < _script_choices.size() and audio_t - _scene_since > 1.0:
		var idx := int(_script_choices[_script_i])
		_script_i += 1
		pick(idx)


func _on_judge_event(ev: Dictionary) -> void:
	var pad: int = int(ev.get("pad", 0))
	var wall := float(Time.get_ticks_msec()) / 1000.0
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


## RW_TRIAL_BOT: plays the attempt's cues exactly on time ("perfect") or none of them ("none").
func _bot_step(t: float) -> void:
	if bot not in ["perfect", "no_fights"] or mode not in ["lead", "phrase"]:
		return
	if bot == "no_fights" and _selected_enc != "":
		return  # plays everything except the fights (to see the lost-fight animation)
	for i in range(phrase.first, phrase.first + phrase.count):
		var n: Dictionary = level.notes[i]
		if not _pressed.has(i) and float(n["time"]) <= t:
			_pressed[i] = true
			judge.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
			pad_view.button_down[int(n["pad"])] = true
		if _pressed.has(i) and not _released.has(i):
			var end_t := float(n["end_time"]) if n["type"] == "hold" else float(n["time"]) + 0.08
			if end_t <= t:
				_released[i] = true
				judge.release(int(n["pad"]), end_t, int(n["pad"]))
				pad_view.button_down[int(n["pad"])] = false


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") and mode != "ended":  # the system back key leaves the dungeon; it is not a game input
		mode = "ended"
		if audio != null:
			audio.stop()
		exit_launcher.call("warehouse")
		get_viewport().set_input_as_handled()


func _notification(what: int) -> void:
	if (what == NOTIFICATION_APPLICATION_FOCUS_OUT or what == NOTIFICATION_APPLICATION_PAUSED) and mode in ["lead", "phrase"] and bot == "":
		# a phrase cannot be paused: losing focus abandons the attempt and offers the same choices again
		judge.pause_interrupt(clock.judge_time())
		phrase.done = true
		flow.phrase_done(false, 0.0)
		_show_passage()
