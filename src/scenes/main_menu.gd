extends Control
## Home, the title screen: the menu over a live view of the Warehouse floor (lead ruling 29), in the chapters menu's neon style
## (StoryStyle), so the two menus are one style. Play (the continuous run from the first level), Story chapters (the finished chapter
## campaign, with its own saves), Start from a reached level, the Wizard Duel, Settings; the developer tools stay behind one small button,
## shown only in the editor or with RW_DEV=1.
##
## The floor is the run's own Warehouse stage (StoryStage: the world, the crowd and the light show, no pads, no notes, no HUD) built two
## frames after the menu is on screen (the neon backdrop shows until then and the picture fades in), its song clock running at a third of
## real time so the crowd moves slowly. No audio is started: the stage has no sound of its own and the run's audio engine is not made here.
## Reduced effects or no camera motion: one still frame. Without a display (the tests) the backdrop stays alone.

const RUN_SCENE := "res://src/run/run_play.tscn"
const CHAPTERS_SCENE := "res://src/scenes/story_campaign.tscn"
const LEVELS_SCENE := "res://src/run/run_levels.tscn"
const SETTINGS_SCENE := "res://src/scenes/settings.tscn"
const DUEL_SCENE := "res://src/duel/duel_lobby.tscn"
const FLOOR_CHAPTER := "night_one"
const FLOOR_RATE := 0.33  # song seconds per real second: the crowd at a third of its speed
const FLOOR_START := 40.0  # song seconds: the floor already full and lit
const FADE_S := 1.2
const FLOOR_CAM := "stage,0,-6"  # a map waypoint, extra yaw, pitch (StoryStage's camera override)
const FLOOR_LIGHTS := ["lights_rave", "beams_fan", "led_wave", "glowsticks_on", "woofer_pump_on"]

var _box: VBoxContainer
var _title: Label
var _buttons: Array = []  # [chapters, reached, duel, settings, debug, play] (Play last)
var _floor: StoryStage
var _floor_host: Control
var _floor_t := FLOOR_START
var _floor_still := false
var _floor_age := 0.0


## A short window (a phone held sideways) gets a smaller title, tighter gaps and lower buttons so all four fit.
func _fit() -> void:
	var compact := size.y > 0.0 and size.y < 520.0
	_title.add_theme_font_size_override("font_size", 40 if compact else 60)
	_box.add_theme_constant_override("separation", 8 if compact else StoryStyle.GAP)
	for b in _buttons:
		(b as Button).custom_minimum_size.y = (56.0 if b == _buttons[_buttons.size() - 1] else 48.0) if compact else (76.0 if b == _buttons[_buttons.size() - 1] else 60.0)


func _ready() -> void:
	PlaytestMode.end_session()  # (Debug / Playtest ends when home is shown: the real progress comes back)
	theme = StoryStyle.theme()
	var bg := StoryStyle.Backdrop.new()
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)
	_floor_host = Control.new()
	_floor_host.name = "Floor"
	_floor_host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_floor_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_floor_host.clip_contents = true
	_floor_host.modulate.a = 0.0
	add_child(_floor_host)
	var veil := _Veil.new()  # darkens the middle behind the menu so the buttons read over the bright floor
	veil.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	veil.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(veil)
	var centre := CenterContainer.new()
	centre.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(centre)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", StoryStyle.GAP)
	box.custom_minimum_size = Vector2(460, 0)
	centre.add_child(box)
	_box = box
	_title = StoryStyle.title("RHYTHM WARFARE", 60, StoryStyle.TEXT, StoryStyle.MAGENTA)
	box.add_child(_title)
	var prog := Session.run_progress
	var play := UiStyle.button("Play", func() -> void:
		Session.run_start_node = ""
		get_tree().change_scene_to_file(RUN_SCENE), 0, 76)
	play.add_theme_font_size_override("font_size", 30)
	play.set_meta("scene", RUN_SCENE)
	box.add_child(play)
	var chapters := UiStyle.button("Story chapters", func() -> void: get_tree().change_scene_to_file(CHAPTERS_SCENE))
	chapters.set_meta("scene", CHAPTERS_SCENE)
	box.add_child(chapters)
	var reached := UiStyle.button("Start from a reached level", func() -> void: get_tree().change_scene_to_file(LEVELS_SCENE))
	reached.set_meta("scene", LEVELS_SCENE)
	reached.disabled = prog.reached_ids().is_empty()
	box.add_child(reached)
	var settings := UiStyle.button("Settings", func() -> void: get_tree().change_scene_to_file(SETTINGS_SCENE))
	settings.set_meta("scene", SETTINGS_SCENE)
	var duel := UiStyle.button("Wizard Duel (wifi)", func() -> void: get_tree().change_scene_to_file(DUEL_SCENE))
	duel.set_meta("scene", DUEL_SCENE)
	box.add_child(duel)
	var tail := HBoxContainer.new()  # Settings and the Debug / Playtest list share a row (the six buttons still fit a phone held sideways)
	tail.add_theme_constant_override("separation", StoryStyle.GAP)
	box.add_child(tail)
	settings.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tail.add_child(settings)
	var debug := UiStyle.button("Debug / Playtest" + (" (on)" if OS.get_environment("RW_DEBUG") == "1" else ""), func() -> void: PlaytestMode.open_list(get_tree()))
	debug.set_meta("scene", PlaytestMode.LIST_SCENE)
	debug.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	debug.add_theme_color_override("font_color", StoryStyle.CYAN.lightened(0.3))
	tail.add_child(debug)
	for b in [chapters, reached, duel, settings, debug]:
		_buttons.append(b)
	_buttons.append(play)
	resized.connect(_fit)
	_fit()
	var note := prog.migration_note()
	if note != "":
		box.add_child(StoryStyle.note(note, StoryStyle.GOOD, 16))
	if prog.recovered_from_corrupt:
		box.add_child(StoryStyle.note("Saved progress was unreadable and has been reset (the old file is kept beside it).", StoryStyle.WARN, 16))
	play.grab_focus()
	if OS.has_feature("editor") or OS.get_environment("RW_DEV") == "1":
		var dev := UiStyle.button("Developer", func() -> void: get_tree().change_scene_to_file("res://src/scenes/developer.tscn"), 150, 44)
		dev.add_theme_font_size_override("font_size", 16)
		dev.anchor_left = 1.0
		dev.anchor_right = 1.0
		dev.anchor_top = 1.0
		dev.anchor_bottom = 1.0
		dev.offset_left = -176 - UiStyle.safe_margins(self).y
		dev.offset_right = -26 - UiStyle.safe_margins(self).y
		dev.offset_top = -62
		dev.offset_bottom = -18
		add_child(dev)
	if DisplayServer.get_name() != "headless" and OS.get_environment("RW_TITLE_FLOOR") != "0":
		_build_floor_later()


func _build_floor_later() -> void:
	await get_tree().process_frame  # the menu is drawn and answers first; the floor is built behind it
	await get_tree().process_frame
	if not is_inside_tree():
		return
	_floor_still = Session.reduced_effects or Session.effective_story_motion() >= 2
	_floor = _make_floor()
	if _floor != null:
		_floor.update(_floor_t, 70.0)


## The Warehouse stage as the run builds it (StoryStage over the chapter's data and art, the 3D world attached), every dancer on the floor.
func _make_floor() -> StoryStage:
	var entry := StoryChapters.load_default().chapter(FLOOR_CHAPTER)
	if entry.is_empty():
		return null
	var loaded := StoryData.load_file(str(entry["data"]))
	var sd: StoryData = loaded["data"]
	if sd == null:
		return null
	var assets := StoryAssets.load_art(sd.art)
	var proxy := StoryRun.new()  # what the stage reads: the tempo and the crowd's energy (no music pack, no audio)
	proxy.level = Level.new()
	proxy.level.bpm = 174.0
	proxy.crowd = CrowdController.new()
	proxy.data = sd
	proxy.crowd.setup(sd)
	proxy.crowd.energy = 70.0
	var st := StoryStage.new()
	st.name = "WarehouseFloor"
	st.set_anchors_preset(Control.PRESET_FULL_RECT)
	st.mouse_filter = Control.MOUSE_FILTER_IGNORE
	st.reduced = Session.reduced_effects
	st.motion = 2  # the camera stays where it stands
	st.lines = StoryLowRes.LINE_CHOICES[clampi(Session.story_lines, 0, 2)]
	_floor_host.add_child(st)
	st.setup(assets, sd, proxy)
	if st.map != null:
		st.attach_world(st.map, true)
	st.set("_cam_override", FLOOR_CAM)  # (the screenshot aid's standpoint: the DJ riser looking out over the floor)
	for action in FLOOR_LIGHTS:  # the light show of a full night, held
		st.apply({"t0": FLOOR_START - 1.0, "bar": 1.0, "action": action, "args": {"bars": 100000}, "block": "", "source": "block"})
	for id in st.crowds:  # a full floor: everybody who comes in during the night is already there
		var c: StoryCrowd = st.crowds[id]
		for aid in c.actors:
			var a: Dictionary = c.actors[aid]
			if str(a["lock"]) == "":
				a["present"] = true
				a["alpha"] = 1.0
	return st


func _process(delta: float) -> void:
	if _floor == null:
		return
	_floor_age += delta
	_floor_host.modulate.a = 1.0 if _floor_still else clampf(_floor_age / FADE_S, 0.0, 1.0)
	if _floor_still:
		return
	_floor_t += delta * FLOOR_RATE
	_floor.update(_floor_t, 70.0)


## A soft dark band behind the menu column (the floor stays bright at the sides), drawn once.
class _Veil:
	extends Control

	func _ready() -> void:
		resized.connect(queue_redraw)

	func _draw() -> void:
		var w := size.x
		var steps := 24
		for i in steps:
			var u := (float(i) + 0.5) / float(steps)
			var d := absf(u - 0.5) * 2.0  # 0 in the middle, 1 at the edges
			var a := 0.62 * (1.0 - d * d) + 0.12
			draw_rect(Rect2(w * float(i) / float(steps), 0, w / float(steps) + 1.0, size.y), Color(0.02, 0.01, 0.06, a))
