extends Control
## Review frames of the `sectioned` cutscene (coming to on the ward) at a frozen cutscene time, so a screenshot shows exactly that
## moment however long the first frames take (the live scene's clock is wall time):
##   RW_T=<seconds> RW_FROM=underworld|mothership|night_one godot --path . -s tools/shoot.gd -- res://tools/story/preview_sectioned.tscn /tmp/out 20:shot:name
## It builds the room being left (in its closing tableau, like src/scenes/story_interlude.gd), replays the scene-side events (dim, fade_crowd,
## captions) up to RW_T and draws StoryInterludeFx with the mental_hospital art at RW_T.

var stage: StoryStage
var fx: StoryInterludeFx
var caption: Label
var t := 0.0


func _ready() -> void:
	t = float(OS.get_environment("RW_T")) if OS.has_environment("RW_T") else 8.0
	var from := OS.get_environment("RW_FROM") if OS.has_environment("RW_FROM") else "underworld"
	var def := StoryChapters.interlude("sectioned")
	var chapters := StoryChapters.load_default()
	var run := StoryRun.create({}, str(chapters.chapter(from)["data"]))
	set_anchors_preset(Control.PRESET_FULL_RECT)
	size = Vector2(1280, 720)
	var bg := ColorRect.new()
	bg.color = Color.BLACK
	bg.size = size
	add_child(bg)
	stage = StoryStage.new()
	stage.size = size
	stage.desk_y = 570.0
	add_child(stage)
	stage.setup(StoryAssets.load_art(run.data.art), run.data, run)
	var ending := "devoured" if from == "underworld" else ("beamed_home" if from == "mothership" else "lost_the_floor")
	stage.apply({"t0": 0.0, "bar": 1.0, "action": "ending", "args": {"ending": ending}, "block": "closing_tableau", "source": "ending"})
	stage.crowd.set_time(0.0)
	for id in stage.crowd.actors:
		stage.crowd.actors[id]["present"] = true
		stage.crowd.actors[id]["alpha"] = 1.0
	fx = StoryInterludeFx.new()
	fx.assets = StoryAssets.load_art(str(def["art"]))
	fx.kind = "sectioned"
	fx.events = def["events"]
	stage.add_overlay(fx)
	caption = Label.new()
	caption.add_theme_font_size_override("font_size", 30)
	caption.add_theme_color_override("font_color", Color(1.0, 0.95, 1.0))
	caption.add_theme_color_override("font_outline_color", Color(0.02, 0.0, 0.12))
	caption.add_theme_constant_override("outline_size", 10)
	var box := StoryStyle.panel_box(StoryStyle.AMBER)
	box.bg_color = Color(0.03, 0.01, 0.1, 0.7)
	box.content_margin_top = 10
	box.content_margin_bottom = 12
	caption.add_theme_stylebox_override("normal", box)
	caption.set_anchors_preset(Control.PRESET_CENTER_TOP)  # as the live scene: centred at the top, as wide as its text
	caption.offset_top = 40
	caption.grow_horizontal = Control.GROW_DIRECTION_BOTH
	caption.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	add_child(caption)
	var shown := ""
	var until := 0.0
	var step := 0.0
	while step <= t:  # replay the scene-side events and the crowd up to t on a fixed step
		for e in def["events"]:
			if float(e["t"]) > step - 1.0 / 30.0 and float(e["t"]) <= step:
				match str(e["do"]):
					"caption":
						shown = str(e["text"])
						until = float(e["t"]) + float(e.get("dur", 2.5))
					"dim":
						stage.apply({"t0": step, "bar": 1.0, "action": "beams_off", "args": {}, "block": "", "source": "block"})
						stage.apply({"t0": step, "bar": 1.0, "action": "lights_low_pulse", "args": {}, "block": "", "source": "block"})
					"fade_crowd":
						stage.crowd.set_ending("")
						stage.crowd.vanish_all(float(e["t"]), float(e.get("dur", 3.0)), 0.0, 0.05)
		stage.update(step, 12.0)
		step += 1.0 / 30.0
	stage.update(t, 12.0)
	caption.text = shown if t < until else ""
	caption.visible = caption.text != ""
	fx.t = t
	fx.queue_redraw()


func _process(_delta: float) -> void:
	stage.update(t, 12.0)
	fx.t = t
	fx.queue_redraw()
