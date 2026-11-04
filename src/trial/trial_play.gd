extends Control
## The Bassment, the wizard's dungeon under the club. The rhythm game never stops: cues fall on the four pads the whole time (TrialEngine charts them in 16-beat blocks from a pack on the
## run's audio clock). Over a fixed illustrated scene a short description and floating choices appear; the player has four bars to choose and, if they do not, the
## default (marked in the data) is taken. A chosen option is played as a rhythm phrase; a pass shows the consequence and the next choices, a failed phrase can be retried,
## and a fight plays an outcome animation. The only inputs are the choices and the pads.
##
## Scripted play: RW_TRIAL_VIRTUAL=1 (no audio, a stepped clock); RW_TRIAL_BOT=perfect|none|no_fights (no_fights plays every cue except a fight's);
## RW_TRIAL_CHOICES=0,d,1 (the pick made in each window in turn; d or empty = no pick, let the default apply); RW_TRIAL_UNTIL=<passage> with RW_STORY_QUIT=1.

const OUTCOME_S := 1.1
const SCENE_TEXT := Color(0.93, 0.92, 1.0)

var tdata: TrialData
var rdata: RunData
var engine: TrialEngine
var audio: RunAudio
var clock: SongClock
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
var bot := ""  # "perfect" | "none" | "no_fights" | ""
var exit_launcher: Callable = func(_where: String) -> void: pass  # set in _ready; tests replace it
var trace: Array = []  # [{kind, ...}] what happened, for scripted checks
var ended := false

var _stage_host: Control
var _pic: TextureRect
var _shade: ColorRect
var _flash: ColorRect
var _title: Label
var _panel: PanelContainer
var _desc: Label
var _news: Label
var _msg: Label
var _tag: Label
var _timer_bar: ColorRect
var _timer_label: Label
var _choice_layer: Control
var _buttons: Array = []
var _base_pos: Array = []
var _enemy: TextureRect
var _enemy_id := ""
var _outcome := {}
var _pending_passage := {}
var _vt := 0.0
var _pressed: Dictionary = {}
var _released: Dictionary = {}
var _script_choices: PackedStringArray = PackedStringArray()
var _script_i := 0
var _script_pick_at := -1.0
var _script_pick := -1
var _until := -1
var _exit_at := -1.0
var _last_t := 0.0
var _beat_s := 60.0 / 174.0


func _ready() -> void:
	theme = UiStyle.theme()
	tdata = TrialData.load_default()
	rdata = RunData.load_default()
	if not tdata.errors.is_empty() or not rdata.errors.is_empty():
		_fatal("The dungeon data is invalid:\n" + "\n".join(PackedStringArray(tdata.errors + rdata.errors)))
		return
	virtual_mode = OS.get_environment("RW_TRIAL_VIRTUAL") == "1"
	if bot == "":
		bot = OS.get_environment("RW_TRIAL_BOT")
	if OS.get_environment("RW_TRIAL_CHOICES") != "":
		_script_choices = OS.get_environment("RW_TRIAL_CHOICES").split(",")
	if OS.get_environment("RW_TRIAL_UNTIL") != "":
		_until = int(OS.get_environment("RW_TRIAL_UNTIL"))
	exit_launcher = func(where: String) -> void:
		Session.run_start_node = "warehouse" if where == "warehouse" else ""
		get_tree().change_scene_to_file("res://src/run/run_play.tscn")
	_beat_s = 60.0 / float(rdata.cfg["timing"]["bpm"])
	engine = TrialEngine.new(tdata, rdata)
	engine.begin(int(OS.get_environment("RW_TRIAL_START")) if OS.get_environment("RW_TRIAL_START") != "" else -1)
	proxy = StoryRun.new()
	proxy.level = engine.level
	proxy.crowd = CrowdController.new()
	_vt = -engine.count_in_s()
	if virtual_mode:
		clock = SongClock.new(null)
	else:
		audio = RunAudio.new()
		add_child(audio)
		audio.configure(rdata)
		clock = SongClock.new(audio)
		clock.calibration_ms = Session.calibration_ms
		var m: Dictionary = tdata.raw["music"]
		audio.on_event({"kind": "phase_start", "node": "trial", "phase": 1, "t": 0.0, "treatment": m["treatment"], "audio": m["audio"]})
		audio.on_event({"kind": "mix", "t": 0.0001, "gains": {"drums": 1.0, "bass": 0.45, "other": 0.45}})
		audio.on_event({"kind": "reveal", "t": 0.0002})
	_build_layout()
	_handle(engine.update(_vt))
	if virtual_mode:
		_step_virtual(_vt)
	else:
		clock.begin_countdown(engine.count_in_s())


func _fatal(message: String) -> void:
	push_error(message)
	var l := Label.new()
	l.text = message
	l.set_anchors_preset(Control.PRESET_FULL_RECT)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	add_child(l)
	ended = true


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
	_tag = Label.new()
	_tag.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_tag.add_theme_color_override("font_color", Color(0.75, 0.8, 1.0, 0.8))
	_tag.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_tag.add_theme_constant_override("outline_size", 4)
	_stage_host.add_child(_tag)
	_timer_bar = ColorRect.new()
	_timer_bar.color = Color(1.0, 0.82, 0.5, 0.9)
	_timer_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_choice_layer.add_child(_timer_bar)
	_timer_label = Label.new()
	_timer_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_timer_label.add_theme_color_override("font_color", Color(1, 0.95, 0.8))
	_timer_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_timer_label.add_theme_constant_override("outline_size", 5)
	_timer_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_choice_layer.add_child(_timer_label)
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
		if not ended:
			engine.press(b, clock.judge_time(), touch))
	lane_input.button_released.connect(func(b: int, touch: int) -> void:
		if not ended:
			engine.release(b, clock.judge_time(), touch))
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
	_timer_label.add_theme_font_size_override("font_size", fs)
	_tag.add_theme_font_size_override("font_size", int(fs * 0.8))
	_tag.position = Vector2(w * 0.025, h - fs * 1.7)
	_msg.add_theme_font_size_override("font_size", int(fs * 1.9))
	_panel.position = Vector2(w * 0.025, h * 0.03 + fs * 2.2)
	var es := minf(h * 0.55, w * 0.3)
	_enemy.size = Vector2(es, es)
	_enemy.pivot_offset = _enemy.size * 0.5
	_enemy.position = Vector2(w * 0.74 - es * 0.5, h * 0.12)
	_fit_panel()
	_place_choices()


func _fit_panel() -> void:
	_panel.custom_minimum_size = Vector2(_stage_host.size.x * 0.5, 0)
	_panel.size = Vector2(_stage_host.size.x * 0.5, 0)
	_shrink_panel.call_deferred()  # the labels wrap once the width is known: take the height they then ask for


func _shrink_panel() -> void:
	if _panel != null:
		_panel.size = Vector2(_stage_host.size.x * 0.5, 0)
		await get_tree().process_frame  # the wrapped labels ask for their real height one frame later
		if _panel != null:
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
	var bar_h := maxf(h * 0.02, 6.0)
	var y0 := h - total - h * 0.06 - bar_h - fs * 1.6
	_base_pos.clear()
	for i in n:
		var b: Button = _buttons[i]
		b.size = Vector2(bw, bh)
		b.add_theme_font_size_override("font_size", int(fs * 1.05))
		var p := Vector2(w * 0.975 - bw, y0 + i * (bh + gap))
		_base_pos.append(p)
		b.position = p
	_timer_bar.size = Vector2(bw, bar_h)
	_timer_bar.position = Vector2(w * 0.975 - bw, h - h * 0.06 - bar_h)
	_timer_label.size = Vector2(bw, fs * 1.4)
	_timer_label.position = Vector2(w * 0.975 - bw, h - h * 0.06 - bar_h - fs * 1.5)


func _texture(path: String) -> Texture2D:
	return load(path) as Texture2D


# --- events ----------------------------------------------------------------------------------------------------------------

func _handle(events: Array) -> void:
	for ev in events:
		match str(ev["kind"]):
			"judge":
				_on_judge_event(ev["event"])
				continue
			"cues":
				pad_view.refresh()
				note_lane.refresh()
			"mix":
				if audio != null:
					audio.on_event(ev)
			"passage":
				if _outcome.is_empty():
					_show_passage(ev)
				else:
					_pending_passage = ev
			"window_open":
				_open_window(ev)
			"phrase":
				_on_phrase(ev)
			"commit":
				_on_commit(ev)
			"result":
				_on_result(ev)
			"exit":
				_on_exit(ev)
		trace.append(ev)


func _show_passage(ev: Dictionary) -> void:
	var p := engine.flow.current()
	_pic.texture = _texture(str(tdata.scenes[str(p["scene"])]["file"]))
	_title.text = str(p["title"]).to_upper()
	_desc.text = str(p["text"])
	_desc.visible = true
	var news := str(ev.get("failure", "")) if str(ev.get("failure", "")) != "" else str(ev.get("consequence", ""))
	_news.text = news
	_news.visible = news != ""
	_panel.visible = true
	_fit_panel()
	_enemy.visible = false
	_enemy_id = ""
	_msg.text = ""
	_shade.color = Color(0, 0, 0, 0.0)
	_tag.text = _tag_text()
	var pk := str(ev.get("passage_kind", p.get("kind", "normal")))
	if pk == "death":
		_msg.text = "YOU DIED"
		_msg.add_theme_color_override("font_color", Color(1.0, 0.45, 0.4))
		_shade.color = Color(0.2, 0, 0, 0.35)
	elif pk == "victory":
		_msg.text = "VICTORY"
		_msg.add_theme_color_override("font_color", Color(1.0, 0.95, 0.6))
	if _until > 0 and engine.flow.passage == _until:
		print("TRIAL reached passage %d" % engine.flow.passage)
		if OS.get_environment("RW_STORY_QUIT") == "1":
			get_tree().quit()


## The line at the bottom of the scene: the zone, and the items the player carries.
func _tag_text() -> String:
	var t := tdata.zone_name(engine.flow.passage)
	if not engine.flow.flags.is_empty():
		var names: Array = engine.flow.flags.map(func(f: Variant) -> String: return str(tdata.items.get(str(f), f)))
		t += "  ·  carrying " + ", ".join(PackedStringArray(names))
	return t


func _open_window(ev: Dictionary) -> void:
	for b in _buttons:
		b.queue_free()
	_buttons.clear()
	var cs := engine.choices()
	for i in cs.size():
		var b := Button.new()
		b.theme = StoryStyle.theme()
		b.focus_mode = Control.FOCUS_NONE
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.set_meta("index", i)
		b.set_meta("label", ("Try again: " if i == engine.flow.retry_index else "") + str(cs[i]["label"]))
		b.pressed.connect(func() -> void: pick(i))
		_choice_layer.add_child(b)
		_buttons.append(b)
	_choice_layer.visible = true
	_place_choices()
	_sync_buttons()
	_script_pick = -1
	_script_pick_at = -1.0
	if _script_i < _script_choices.size():
		var tok := _script_choices[_script_i].strip_edges()
		_script_i += 1
		if tok != "" and tok != "d":
			_script_pick = int(tok)
			_script_pick_at = float(ev["t"]) + 1.0
	_enemy.visible = false
	_panel.visible = true
	_desc.visible = true


func _sync_buttons() -> void:
	var def := engine.default_index()
	for i in _buttons.size():
		var b: Button = _buttons[i]
		var tag := ""
		if engine.selected >= 0:
			tag = "   [CHOSEN]" if i == engine.selected else ""
		elif i == def:
			tag = "   [DEFAULT]"
		b.text = str(b.get_meta("label")) + tag
		var on := (engine.selected == i) or (engine.selected < 0 and i == def)
		b.modulate = Color(1.0, 0.95, 0.6) if on else Color(0.85, 0.88, 1.0, 0.92)


## The player picks (or changes their pick) in the open window: a tap on a floating choice, or a script.
func pick(i: int) -> void:
	if engine != null and engine.select(i):
		trace.append({"kind": "pick", "choice": i, "t": _last_t})
		_sync_buttons()


func _on_commit(ev: Dictionary) -> void:
	_choice_layer.visible = false
	for b in _buttons:
		b.queue_free()
	_buttons.clear()
	if bool(ev["defaulted"]):
		var label := str(ev.get("label", ""))
		_news.text = "The moment passes: " + (label if label != "" else "you drift on") + "."
		_news.visible = true


func _on_phrase(ev: Dictionary) -> void:
	_news.visible = false  # the scene is left clear for the phrase; only a fight keeps its intro line
	_panel.visible = false
	_desc.visible = false
	var enc := str(ev["encounter"])
	if enc != "":
		var e: Dictionary = tdata.encounters[enc]
		_enemy.texture = _texture(str(e["portrait"]))
		_enemy.modulate = Color.html(str(e["tint"])) if e.has("tint") else Color.WHITE
		_enemy.visible = true
		_enemy_id = enc
		_news.text = str(e["intro"])
		_news.visible = true
		_panel.visible = true
		_fit_panel()
	_msg.text = ""


func _on_result(ev: Dictionary) -> void:
	_msg.text = ""
	if bool(ev["fight"]):
		_outcome = {"t0": float(ev["t"]), "kind": str(ev["outcome"])}
		_msg.text = "DEFEATED!" if str(ev["outcome"]) == "win" else ("BEATEN" if bool(ev.get("defeated", false)) else "HURT!")
		_msg.add_theme_color_override("font_color", Color(0.6, 1.0, 0.8) if str(ev["outcome"]) == "win" else Color(1.0, 0.55, 0.45))
	else:
		_msg.text = "WELL PLAYED" if str(ev["result"]) == "pass" else "MISSED: TRY AGAIN"
		_msg.add_theme_color_override("font_color", Color(0.6, 1.0, 0.8) if str(ev["result"]) == "pass" else Color(1.0, 0.7, 0.5))


func _on_exit(ev: Dictionary) -> void:
	_exit_at = float(ev["t"]) + 1.2
	_msg.text = ""
	if audio != null:
		audio.on_event({"kind": "depleted", "t": float(ev["t"]), "fade_s": 1.0})


func _animate_outcome(t: float) -> void:
	var k := clampf((t - float(_outcome["t0"])) / OUTCOME_S, 0.0, 1.0)
	var enc: Dictionary = tdata.encounters.get(_enemy_id, {})
	var win := str(_outcome["kind"]) == "win"
	if win:
		if k > 0.12:
			_enemy.texture = _texture(str(enc["portrait_hit"]))
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
		_outcome = {}
		_layout()
		if not _pending_passage.is_empty():
			_show_passage(_pending_passage)
			_pending_passage = {}


# --- frame loop ------------------------------------------------------------------------------------------------------------

func _process(delta: float) -> void:
	if engine == null or clock == null or ended and not virtual_mode:
		return
	if virtual_mode:
		_vt += 1.0 / 30.0
		_step_virtual(_vt)
		return
	clock.tick()
	if clock.state == SongClock.State.PLAYING or clock.state == SongClock.State.COUNTDOWN:
		_advance(clock.judge_time(), clock.audio_time(), delta)


func _step_virtual(t: float) -> void:
	clock.state = SongClock.State.PAUSED
	clock._frozen = t
	_advance(t, t, 1.0 / 30.0)


## One frame at song time `t` (judge time) / `audio_t` (what is heard). Tests drive it directly.
func _advance(t: float, audio_t: float, _delta: float) -> void:
	_last_t = audio_t
	if ended:
		return
	_bot_step(t)
	_handle(engine.update(t))
	if _script_pick >= 0 and audio_t >= _script_pick_at:
		pick(_script_pick)
		_script_pick = -1
	if not _outcome.is_empty():
		_animate_outcome(audio_t)
	var open := engine.window_open
	_choice_layer.visible = open
	if open:
		for i in _buttons.size():  # the choices float
			var b: Button = _buttons[i]
			b.position = (_base_pos[i] as Vector2) + Vector2(0.0, sin(audio_t * 1.7 + float(i) * 1.3) * _stage_host.size.y * 0.012)
		var span := float(TrialEngine.BLOCK_BEATS) * _beat_s
		var left := engine.window_left(t)
		_timer_bar.scale = Vector2(clampf(left / span, 0.0, 1.0), 1.0)
		var bars := int(ceil(left / (4.0 * _beat_s)))
		_timer_label.text = "%d bar%s to choose" % [bars, "" if bars == 1 else "s"]
	_shade.color = Color(0, 0, 0, 0.30 if engine.kind == "phrase" else 0.0)
	if _enemy.visible and _outcome.is_empty():
		_enemy.position.y = _stage_host.size.y * 0.12 + sin(audio_t * 3.0) * _stage_host.size.y * 0.015
	note_lane.queue_redraw()
	if _exit_at >= 0.0 and audio_t >= _exit_at:
		ended = true
		if audio != null:
			audio.stop()
		exit_launcher.call(engine.exit_to)


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


## RW_TRIAL_BOT plays the charted cues exactly on time ("perfect"), none of them ("none"), or all but a fight's ("no_fights").
func _bot_step(t: float) -> void:
	if bot == "" or bot == "none":
		return
	var notes := engine.level.notes
	for i in range(maxi(notes.size() - 300, 0), notes.size()):
		var n: Dictionary = notes[i]
		if bot == "no_fights" and str(n.get("enc", "")) != "":
			continue
		if not _pressed.has(i) and float(n["time"]) <= t:
			_pressed[i] = true
			engine.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
			pad_view.button_down[int(n["pad"])] = true
		if _pressed.has(i) and not _released.has(i):
			var end_t := float(n["end_time"]) if n["type"] == "hold" else float(n["time"]) + 0.08
			if end_t <= t:
				_released[i] = true
				engine.release(int(n["pad"]), end_t, int(n["pad"]))
				pad_view.button_down[int(n["pad"])] = false


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") and not ended:  # the system back key leaves the dungeon; it is not a game input
		ended = true
		if audio != null:
			audio.stop()
		exit_launcher.call("warehouse")
		get_viewport().set_input_as_handled()
