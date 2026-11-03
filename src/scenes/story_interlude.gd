extends Control
## The cutscene between chapters, on the same fixed camera as the club the player just left: Night One's stage in its ending tableau
## with a scripted event (an alien ship taking the whole rave, or the floor giving way), then the next chapter. Silent; no judging.
## Skip with Esc or a tap.

var stage: StoryStage
var fx: StoryInterludeFx
var _def: Dictionary
var _t0 := 0.0
var _done_events := {}
var _caption: Label
var _caption_until := 0.0
var _caption_from := 0.0
var _go := false
var _run: StoryRun
var _skip_hint: Label


func _ready() -> void:
	theme = UiStyle.theme()
	var info := Session.story_interlude
	if info.is_empty() and OS.has_environment("RW_STORY_INTERLUDE"):  # screenshots: open a cutscene directly
		var nm := OS.get_environment("RW_STORY_INTERLUDE")
		info = {"name": nm, "from": "night_one", "to": "mothership" if nm == "abduction" else "underworld",
			"ending": "good_night" if nm == "abduction" else "lost_the_floor"}
		Session.story_interlude = info
	_def = StoryChapters.interlude(str(info.get("name", "")))
	var chapters := StoryChapters.load_default()
	var from_entry := chapters.chapter(str(info.get("from", "night_one")))
	_run = StoryRun.create({"loadout": Session.loadout(), "library": Session.library(), "unlocked": Session.campaign.unlocked_items()}, str(from_entry["data"]))
	if _def.is_empty() or not _run.errors.is_empty():
		_next()
		return
	var from_assets := StoryAssets.load_art(_run.data.art)
	var to_assets := StoryAssets.load_art(str(_def["art"]))
	var bg := ColorRect.new()
	bg.color = Color.BLACK
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	stage = StoryStage.new()
	stage.set_anchors_preset(Control.PRESET_FULL_RECT)
	stage.desk_y = 720.0  # the whole 1280 x 720 club, no desk
	add_child(stage)
	stage.setup(from_assets, _run.data, _run)
	stage.reduced = Session.reduced_effects
	var ending := str(info.get("ending", "good_night"))
	stage.apply({"t0": 0.0, "bar": 1.0, "action": "ending", "args": {"ending": ending}, "block": "closing_tableau", "source": "ending"})
	stage.crowd.set_time(0.0)
	for id in stage.crowd.actors:  # the whole room is on the floor for the cutscene
		stage.crowd.actors[id]["present"] = true
		stage.crowd.actors[id]["alpha"] = 1.0
	fx = StoryInterludeFx.new()
	fx.assets = to_assets
	fx.kind = str(info.get("name", "abduction"))
	fx.events = _def["events"]
	stage.add_overlay(fx)
	_caption = Label.new()
	_caption.add_theme_font_size_override("font_size", 30)
	_caption.add_theme_color_override("font_color", Color(1.0, 0.95, 1.0))
	_caption.add_theme_color_override("font_outline_color", Color(0.02, 0.0, 0.12))
	_caption.add_theme_constant_override("outline_size", 10)
	var cap_box := StoryStyle.panel_box(StoryStyle.MAGENTA if str(info.get("name", "")) == "abduction" else StoryStyle.AMBER)
	cap_box.content_margin_top = 10
	cap_box.content_margin_bottom = 12
	cap_box.bg_color = Color(0.03, 0.01, 0.1, 0.7)
	_caption.add_theme_stylebox_override("normal", cap_box)
	_caption.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_caption.offset_top = 40
	_caption.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(_caption)
	_skip_hint = StoryStyle.note("Esc to skip", Color(1, 1, 1, 0.45), 14)
	_skip_hint.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_skip_hint.offset_left = -140
	_skip_hint.offset_top = -34
	add_child(_skip_hint)
	_t0 = float(Time.get_ticks_msec()) / 1000.0
	if OS.has_environment("RW_STORY_INTERLUDE_T"):  # screenshots: jump the cutscene clock
		_t0 -= float(OS.get_environment("RW_STORY_INTERLUDE_T"))


func _process(_delta: float) -> void:
	if stage == null or _go:
		return
	var t := float(Time.get_ticks_msec()) / 1000.0 - _t0
	fx.t = t
	for e in _def["events"]:
		if t >= float(e["t"]) and not _done_events.has(e):
			_done_events[e] = true
			_run_event(e, t)
	stage.update(t, 12.0 if stage.tableau() == "lost" else 55.0)
	fx.queue_redraw()
	_caption.modulate.a = clampf(_caption_until - t, 0.0, 1.0) * clampf((t - _caption_from) / 0.4, 0.0, 1.0)
	_caption.visible = _caption.modulate.a > 0.01 and _caption.text != ""
	if t >= float(_def["duration"]) and OS.get_environment("RW_STORY_INTERLUDE_HOLD") != "1":
		_next()


func _run_event(e: Dictionary, t: float) -> void:
	match str(e["do"]):
		"caption":
			_caption.text = str(e["text"])
			_caption_from = t
			_caption_until = t + float(e.get("dur", 2.5))
		"dim":
			stage.apply({"t0": t, "bar": 1.0, "action": "beams_off", "args": {}, "block": "", "source": "block"})
			stage.apply({"t0": t, "bar": 1.0, "action": "lights_low_pulse", "args": {}, "block": "", "source": "block"})
		"look_up", "panic":
			stage.crowd.set_ending("")
			stage.crowd.direct(stage.crowd.present_ids(), "look" if str(e["do"]) == "look_up" else "sad", t, float(e.get("dur", 5.0)), false, 0.05)
		"lift_crowd":
			stage.crowd.set_ending("")
			stage.crowd.direct(stage.crowd.present_ids(), "hands_up", t, float(e["dur"]) + 1.0, false, 0.05)
			stage.crowd.vanish_all(t, float(e["dur"]) - 1.0, -300.0)
		"sink_crowd":
			stage.crowd.vanish_all(t, float(e["dur"]) - 1.0, 70.0)


func _next() -> void:
	if _go:
		return
	_go = true
	get_tree().change_scene_to_file.call_deferred("res://src/scenes/story_play.tscn")


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel") or (event is InputEventScreenTouch and event.pressed):
		_next()
		get_viewport().set_input_as_handled()
