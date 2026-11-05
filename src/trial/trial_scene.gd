class_name TrialScene
extends Control
## The Bassment inside the run scene (docs/TRIAL_OPENING.md). The run's RunPlay hosts it: it owns the TrialEngine (the pads, the clock and RunAudio are the host's and never restart),
## one StoryStage per zone (each a 2.5D map from content/story/maps/bassment_<zone>.json, built ahead during a cue-free guard and swapped through the passage frame on a downbeat),
## the camera on rails between the passages' waypoints, the passage text as a caption band across the top (narrative only: no choice is ever written; off during play, see `_gate_text`: the creatures act what it said), the choices as hotspots in the
## room while the four-bar window is open (an exit lit where it lies, a creature standing in the room, an object, a feature; the default one brighter; tap to select, tap again to change,
## keys 1 to 4 on a desktop), creatures as billboard figures with idle, attack and struck poses, and the tableaux of a death and of the victory. Everything is a function of song time.
## The hotspot data is content/trial/hotspots.json (TrialHotspots); the lights and the hit test are the run's own HotspotView (one per zone stage, inside its low-res picture), fed by `hotspot_items`.

const OUTCOME_S := 1.1
const SCENE_TEXT := Color(0.93, 0.92, 1.0)
const FIGURES := {  # creature -> {size (m tall), lift (m above the floor), dist (m in front of the passage waypoint)}
	"lampmoth": {"size": 1.7, "lift": 0.7, "dist": 2.6}, "cable_eel": {"size": 1.9, "lift": 0.9, "dist": 3.4}, "barrel_knight": {"size": 2.0, "lift": 0.0, "dist": 2.8},
	"mildew_mother": {"size": 2.0, "lift": 0.0, "dist": 2.8}, "mirror_twin": {"size": 1.9, "lift": 0.0, "dist": 2.8}, "bouncer": {"size": 2.5, "lift": 0.0, "dist": 3.0},
	"rat_king": {"size": 1.7, "lift": 0.0, "dist": 2.6}, "furnace_imp": {"size": 1.4, "lift": 0.0, "dist": 2.4}, "gargoyle": {"size": 3.0, "lift": 0.4, "dist": 3.4},
	"echo": {"size": 2.0, "lift": 0.0, "dist": 3.0},
}

var host: Node  # the RunPlay
var tdata: TrialData
var rdata: RunData
var engine: TrialEngine
var active := false
var ended := false
var bot := ""  # "perfect" | "none" | "no_fights" | ""
var trace: Array = []
var zone_stages: Dictionary = {}  # zone -> {stage: StoryStage, map: StoryMap}
var zone := ""  # the zone whose stage is shown ("" before the first swap)
var direct := false
var origin := 0.0
var left_t := -1.0  # song time of the downbeat the dungeon is left on (-1: not leaving)
var leave_reason := ""
var swap_t := -1.0  # the downbeat the shown zone changes on
var build_log: Array = []

var _assets: StoryAssets
var _stage_host: Control
var _title: Label
const PANEL_W := 0.95  # the text panel is a band across the top, so the room stays visible below it
var _panel: PanelContainer
var _desc: Label
var _news: Label
var _msg: Label
var _tag: Label
var _timer_bar: ColorRect
var _choice_layer: Control
var hotspots: TrialHotspots
var _items: Array = []  # the open window's hotspots: [{hs, index}] (index into the engine's choices)
var _sel_t: Dictionary = {}  # choice index -> song time it was selected
var _commit_view: Dictionary = {}  # {index, hs, zone, t}: the committed hotspot stays drawn for a moment (the flash)
var _flash: ColorRect
var _fade: ColorRect
var _outcome := {}
var _pending: Dictionary = {}  # a passage waiting for the zone swap or an outcome animation
var _swap_zone := ""
var _swap_wp := ""
var _passage_n := -1
var _last_exit := ""
var _last_wp := ""
var _fig: Dictionary = {}  # {node, mat, id, st, pos, sec, spec}
var _fig_pose := ""
var _script_choices: PackedStringArray = PackedStringArray()
var _script_taps := false  # RW_TRIAL_TAPS: the scripted picks are real taps through the hit test (hotspot centres), not direct picks
var _script_i := 0
var _script_pick_at := -1.0
var _script_pick := -1
var _until := -1
var _pressed: Dictionary = {}
var _released: Dictionary = {}
var _last_t := 0.0
var _beat_s := 60.0 / 174.0
var _dark_t0 := -1.0
var _dark_kind := ""
var _guard_key := -1
var _last_area := Vector2.ZERO
var _ap_t := -1.0  # the downbeat the passage frame is working round (closing, then opening)


## The run's data changed under the dungeon (a path's tempo handoff, RunPlay._path_swap): the Bassment plays on whichever run is the Warehouse's again.
func retarget(p_rdata: RunData) -> void:
	rdata = p_rdata
	_beat_s = 60.0 / float(rdata.cfg["timing"]["bpm"])


func setup(p_host: Node, p_tdata: TrialData, p_rdata: RunData) -> void:
	host = p_host
	tdata = p_tdata
	rdata = p_rdata
	_beat_s = 60.0 / float(rdata.cfg["timing"]["bpm"])
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_stage_host = host._stage_host
	_build_ui()
	visible = false
	hotspots = TrialHotspots.load_default()
	if OS.get_environment("RW_TRIAL_CHOICES") != "":
		_script_choices = OS.get_environment("RW_TRIAL_CHOICES").split(",")
	elif OS.get_environment("RW_TRIAL_TAPS") != "":  # one token per window, ";" or "," between them: a choice index to tap, or "d" for no tap
		_script_choices = OS.get_environment("RW_TRIAL_TAPS").replace(";", ",").split(",")
		_script_taps = true
	if OS.get_environment("RW_TRIAL_UNTIL") != "":
		_until = int(OS.get_environment("RW_TRIAL_UNTIL"))
	_assets = StoryAssets.load_art("bassment")


# --- ui ----------------------------------------------------------------------------------------------------------------------

func _build_ui() -> void:
	var split := 1.0 - float(Session.PAD_SIZES[clampi(Session.pad_size, 0, 2)])
	var area := Control.new()  # everything of the dungeon's overlay lives over the stage area
	area.name = "Area"
	area.anchor_right = 1.0
	area.anchor_bottom = split
	area.clip_contents = true
	area.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(area)
	_fade = ColorRect.new()
	_fade.color = Color(0, 0, 0, 0)
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	area.add_child(_fade)
	_title = Label.new()
	_title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_title.add_theme_color_override("font_color", Color(1.0, 0.82, 0.5))
	_title.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_title.add_theme_constant_override("outline_size", 6)
	area.add_child(_title)
	_panel = PanelContainer.new()
	var box := StoryStyle.panel_box(StoryStyle.EDGE)
	box.bg_color.a = 0.6
	_panel.add_theme_stylebox_override("panel", box)
	_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	area.add_child(_panel)
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
	area.add_child(_choice_layer)
	_tag = Label.new()
	_tag.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_tag.add_theme_color_override("font_color", Color(0.75, 0.8, 1.0, 0.85))
	_tag.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_tag.add_theme_constant_override("outline_size", 4)
	area.add_child(_tag)
	_timer_bar = ColorRect.new()
	_timer_bar.color = Color(1.0, 0.82, 0.5, 0.9)
	_timer_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_choice_layer.add_child(_timer_bar)
	_msg = Label.new()
	_msg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_msg.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_msg.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.95))
	_msg.add_theme_constant_override("outline_size", 8)
	_msg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	area.add_child(_msg)
	_flash = ColorRect.new()
	_flash.color = Color(1, 1, 1, 0)
	_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	area.add_child(_flash)
	area.resized.connect(_layout)


func _area() -> Control:
	return get_node("Area") as Control


func _fs() -> int:
	return int(clampf(_area().size.y * 0.05, 11.0, 22.0))


func _layout() -> void:
	var w := _area().size.x
	var h := _area().size.y
	if w <= 0.0:
		return
	var fs := _fs()
	_title.add_theme_font_size_override("font_size", int(fs * 1.3))
	_title.position = Vector2(w * 0.025, h * 0.03)
	_desc.add_theme_font_size_override("font_size", fs)
	_news.add_theme_font_size_override("font_size", fs)
	_tag.add_theme_font_size_override("font_size", int(fs * 0.8))
	_tag.position = Vector2(w * 0.025, h - fs * 1.7)
	_msg.add_theme_font_size_override("font_size", int(fs * 1.9))
	_panel.position = Vector2(w * 0.025, h * 0.03 + fs * 2.2)
	_fit_panel()
	_place_choices()


func _fit_panel() -> void:
	var w := _area().size.x * PANEL_W
	_panel.custom_minimum_size = Vector2(w, 0)
	_panel.size = Vector2(w, 0)
	_shrink_panel.call_deferred()


func _shrink_panel() -> void:
	if _panel != null and is_inside_tree():
		_panel.size = Vector2(_area().size.x * PANEL_W, 0)


## The four-bar window is a thin bar along the bottom of the picture (no text): it empties as the bars run out.
func _place_choices() -> void:
	var w := _area().size.x
	var h := _area().size.y
	var bar_h := maxf(h * 0.014, 4.0)
	_timer_bar.size = Vector2(w * 0.95, bar_h)
	_timer_bar.pivot_offset = Vector2.ZERO
	_timer_bar.position = Vector2(w * 0.025, h - bar_h - 2.0)


# --- zones -------------------------------------------------------------------------------------------------------------------

func has_zone(z: String) -> bool:
	return zone_stages.has(z)


## Builds the stage of a zone (hidden): the map, the rail camera, the lit 3D world seen through the low-res view. The run does this in a cue-free guard.
func build_zone(z: String) -> Dictionary:
	if zone_stages.has(z):
		return zone_stages[z]
	var t0 := Time.get_ticks_usec()
	var mid := tdata.zone_map(z)
	var sd := StoryData.new()
	sd.id = mid
	sd.art = "bassment"
	sd.title = str(tdata.zones[z]["name"])
	sd.raw = {"id": mid, "art": "bassment", "title": sd.title}
	var st := StoryStage.new()
	st.name = "Zone_" + z
	st.set_anchors_preset(Control.PRESET_FULL_RECT)
	st.reduced = Session.reduced_effects
	st.high_contrast = Session.high_contrast
	st.motion = Session.effective_story_motion()
	st.lines = StoryLowRes.LINE_CHOICES[clampi(Session.story_lines, 0, 2)]
	st.visible = false
	st.process_mode = Node.PROCESS_MODE_DISABLED
	_stage_host.add_child(st)
	host.proxy.data = sd
	host.proxy.crowd.setup(sd)
	st.setup(_assets, sd, host.proxy)
	if st.map != null:
		st.attach_world(st.map, true)
	var rec := {"stage": st, "map": st.map}
	if st.lowres != null:  # the hotspots are drawn inside the picture, above the room, by the run's own view
		var hv := HotspotView.new()
		hv.name = "Hotspots"
		hv.stage = st
		hv.beat_s = _beat_s
		hv.items_fn = func() -> Array: return _view_items(z)
		hv.pose_fn = _exit_pose
		hv.now_fn = func() -> float: return _last_t
		hv.reduced = Session.reduced_effects
		hv.high_contrast = Session.high_contrast
		hv.glow_tex = _assets.sprite("glow").get("tex", null)
		var warm: Array = st.palettes.get("warm", [])
		if not warm.is_empty():
			hv.tint = (warm[0] as Color).lerp(Color(1.0, 0.9, 0.6), 0.55)
		hv.set_anchors_preset(Control.PRESET_FULL_RECT)
		var layer := st.lowres.add_overlay(hv, "Hotspots")
		layer.layer = 2
		rec["hotspot_view"] = hv
	zone_stages[z] = rec
	build_log.append({"zone": z, "ms": snappedf(float(Time.get_ticks_usec() - t0) / 1000.0, 0.1)})
	return rec


func _stage(z: String) -> StoryStage:
	return (zone_stages[z]["stage"] as StoryStage) if zone_stages.has(z) else null


func _map(z: String) -> StoryMap:
	return zone_stages[z]["map"] if zone_stages.has(z) else null


func _show_zone(z: String) -> void:
	for k in zone_stages:
		var s: StoryStage = zone_stages[k]["stage"]
		s.visible = (k == z)
		s.process_mode = Node.PROCESS_MODE_INHERIT if k == z else Node.PROCESS_MODE_DISABLED
	zone = z
	_drop_figure()
	if z != "" and host != null:
		host.hide_run_stage()
	_trim_stages()


func _trim_stages() -> void:  # keep the shown zone and the two most recent others
	if zone_stages.size() <= 4:
		return
	for k in zone_stages.keys():
		if k != zone and k != _swap_zone and zone_stages.size() > 4 and k != "hatch":
			(zone_stages[k]["stage"] as StoryStage).queue_free()
			zone_stages.erase(k)


func _act(z: String, name: String, t0: float, args: Dictionary = {}) -> void:
	var st := _stage(z)
	if st != null:
		st.apply({"t0": t0, "action": name, "args": args, "bar": 0.0, "block": "trial", "source": "trial"})


func _move(z: String, wp: String, t0: float, bars: float, style := "walk") -> void:
	if wp != "" and _map(z) != null and _map(z).has_waypoint(wp):
		_act(z, "player_move", t0, {"to": wp, "bars": maxf(bars, 0.25), "style": style})


func _exit_pose() -> Dictionary:
	var st := _stage(zone)
	if st == null or st.player == null:
		return {}
	var pose := st.player.pose_at(_last_t)
	return {"cam": pose["cam"], "yaw": float(pose["yaw"]) + st.free_look.offset, "pitch": float(pose.get("pitch", 0.0))}


# --- begin and the frame loop ----------------------------------------------------------------------------------------------------

## Starts the dungeon. `p_origin` is the downbeat of the clock it begins on; `p_direct`: no walk-in, the first zone is simply shown (a launch straight into the dungeon).
func begin(p_origin: float, start_passage: int, p_direct: bool) -> void:
	origin = p_origin
	direct = p_direct
	ended = false
	active = true
	left_t = -1.0
	swap_t = -1.0
	trace = []
	zone = ""
	_passage_n = -1
	_last_exit = ""
	_pending = {}
	_outcome = {}
	_dark_t0 = -1.0
	_ap_t = -1.0
	_script_i = 0
	engine = TrialEngine.new(tdata, rdata)
	engine.begin(start_passage, origin)
	visible = true
	_rebind_pads()
	var m: Dictionary = tdata.raw["music"]
	var a: RunAudio = host.audio
	if a != null:  # the dungeon's pack enters on the downbeat exactly as a world's music does on a swap
		var ph: int = host.engine.phase_n + 1
		a.on_event({"kind": "phase_start", "node": "trial", "phase": ph, "t": origin, "treatment": m["treatment"], "audio": m["audio"]})
		a.on_event({"kind": "mix", "t": origin + 0.0001, "gains": {"drums": 1.0, "bass": 0.45, "other": 0.45}})
		a.on_event({"kind": "reveal", "t": origin + 0.0002})
	var z0 := str(tdata.passage(engine.flow.passage)["zone"])
	build_zone(z0)
	if direct:
		_show_zone(z0)
	_layout()
	_handle(engine.update(origin - engine.count_in_s() - 0.001))
	_handle(engine.update(origin - engine.count_in_s()))


func _rebind_pads() -> void:
	var pv: StoryPadView = host.pad_view
	var nl: StoryNoteLane = host.note_lane
	pv.setup(engine.level, host.clock)
	pv.holding_fn = engine.judge.hold_progress
	pv.progress_fn = engine.progress_at
	nl.setup(engine.level, host.clock, pv)
	nl.state_fn = engine.judge.cue_state
	pv.energy_fn = func() -> float: return host.engine.energy


## One frame at judge time `t` / audio time `audio_t`.
func update(t: float, audio_t: float) -> void:
	_last_t = audio_t
	if not active or ended and left_t < 0.0:
		return
	if not size.is_equal_approx((host as Control).size):
		size = (host as Control).size
	if not _area().size.is_equal_approx(_last_area):
		_last_area = _area().size
		_layout()
	_bot_step(t)
	_handle(engine.update(t))
	if _script_pick >= 0 and audio_t >= _script_pick_at:
		if _script_taps:
			if not _view_items(zone).is_empty():  # (the finger waits for the room: the lights come up after a zone swap)
				var hit := tap_centre(_script_pick)
				print("TRIAL tap %d -> %d" % [_script_pick, hit])
				_script_pick = -1
		else:
			pick(_script_pick)
			_script_pick = -1
	_prebuild_in_guard(t)
	if swap_t >= 0.0 and audio_t >= swap_t:
		_do_swap()
	var swapping := swap_t >= 0.0 or left_t >= 0.0
	host._passage.set_aperture(RunPassage.aperture(audio_t, _ap_t, _beat_s))
	if _ap_t >= 0.0 and swap_t < 0.0 and left_t < 0.0 and audio_t > _ap_t + RunPassage.OPEN_BEATS * _beat_s + 0.3:
		_ap_t = -1.0
	if not _outcome.is_empty():
		_animate_outcome(audio_t)
	var st := _stage(zone)
	if st != null:
		st.update(audio_t, 40.0)
	_animate_figure(audio_t)
	var open := engine.window_open and swap_t < 0.0 and zone != "" and left_t < 0.0 and _pending.is_empty()
	_choice_layer.visible = open
	if open:
		var span := float(TrialEngine.BLOCK_BEATS) * _beat_s
		_timer_bar.scale = Vector2(clampf(engine.window_left(t) / span, 0.0, 1.0), 1.0)
	_panel.visible = _panel.visible and not swapping
	_gate_text()
	_update_dark(audio_t)
	if left_t >= 0.0 and audio_t >= left_t and not ended:
		ended = true
		host.trial_leave(left_t, leave_reason)


## No text during play (docs/THREE_PATHS_AND_FACES_PLAN.md D3): the title, the caption band (what happened, what you carry), the zone tag and the big banners (YOU DIED, VICTORY, DEFEATED) stay hidden
## unless RW_DEV_TEXT=1. The labels keep their text (the tests and the debug view read it); the creature's acts, the light and the fade tell it instead.
func _gate_text() -> void:
	if DevText.on():
		return
	_title.visible = false
	_panel.visible = false
	_tag.visible = false
	_msg.visible = false


func _update_dark(t: float) -> void:
	if _dark_t0 < 0.0:
		_fade.color = Color(0, 0, 0, 0)
		return
	var k := clampf((t - _dark_t0) / (6.0 * _beat_s), 0.0, 1.0)
	if _dark_kind == "death":
		_fade.color = Color(0.1, 0.0, 0.0, k * 0.78)
	else:  # the victory: a flash of daylight settling to a warm glow
		_fade.color = Color(1.0, 0.92, 0.7, clampf(0.85 - k * 0.8, 0.0, 0.85))


## Candidate zones are built in the cue-free guard (the last 3 beats of a block), one per guard, so a swap never builds on the downbeat.
func _prebuild_in_guard(t: float) -> void:
	if host.virtual_mode or engine == null:
		return
	var beat := (t - origin) / _beat_s
	var in_block := fmod(maxf(beat, 0.0), 16.0)
	var key := int(floor(maxf(beat, 0.0) / 16.0))
	if in_block >= 12.6 and in_block < 15.0 and key != _guard_key:
		_guard_key = key
		for c in engine.choices():
			if c.get("to", null) == null:
				continue
			var z := str(tdata.passage(int(c["to"]))["zone"])
			if not zone_stages.has(z):
				build_zone(z)
				break


func _do_swap() -> void:
	var z := _swap_zone
	var wp := _swap_wp
	var t0 := swap_t
	build_zone(z)
	swap_t = -1.0
	_show_zone(z)
	_move(z, wp, t0, 2.0)
	_swap_zone = ""
	if not _pending.is_empty():
		var ev := _pending
		_pending = {}
		_show_passage(ev)


func next_boundary(t: float) -> float:
	var k: float = ceil((t - origin) / (16.0 * _beat_s) - 1.0e-6)
	return origin + k * 16.0 * _beat_s


# --- engine events -----------------------------------------------------------------------------------------------------------

func _handle(events: Array) -> void:
	for ev in events:
		match str(ev["kind"]):
			"judge":
				host.on_judge(ev["event"])
				continue
			"cues":
				host.pad_view.refresh()
				host.note_lane.refresh()
			"mix":
				if host.audio != null:
					host.audio.on_event(ev)
			"passage":
				_on_passage(ev)
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


func _on_passage(ev: Dictionary) -> void:
	if OS.get_environment("RW_TRIAL_TRACE") == "1":
		print("TRIAL t=%.2f passage %d (%s)" % [float(ev["t"]), int(ev["passage"]), str(tdata.passage(int(ev["passage"]))["zone"])])
	var p := engine.flow.current()
	var z := str(p["zone"])
	var t := float(ev["t"])
	var moved := int(ev["passage"]) != _passage_n
	var first := _passage_n < 0
	_passage_n = int(ev["passage"])
	var wp := str(p.get("waypoint", ""))
	if first and direct:
		_show_passage(ev)
		_move(z, wp, t, 0.5)
		_last_wp = wp
		return
	if z != zone or first:
		swap_t = next_boundary(maxf(t, origin))
		_ap_t = swap_t
		if not first:
			var span := (swap_t - t) / (4.0 * _beat_s)
			_move(zone, _last_exit, t, span)
		_swap_zone = z
		_swap_wp = wp
		_pending = ev
		build_zone(z)
	elif moved:
		var bars := 1.5
		if _last_exit != "":
			_move(z, _last_exit, t, bars)
		_move(z, wp, t + bars * 4.0 * _beat_s, bars)
		_show_passage(ev)
	else:
		_show_passage(ev)
	_last_wp = wp


func _fail_look(t: float) -> void:
	_act(zone, "fx_queasy", t, {"amount": 0.7, "bars": 1.5})
	_act(zone, "player_look", t, {"by": 12.0, "bars": 1.0})


func _show_passage(ev: Dictionary) -> void:
	var p := engine.flow.current()
	_title.text = str(p["title"]).to_upper()
	_desc.text = str(p["text"])
	_desc.visible = true
	var news := str(ev.get("failure", "")) if str(ev.get("failure", "")) != "" else str(ev.get("consequence", ""))
	_news.text = news
	_news.visible = news != ""
	_panel.visible = true
	_fit_panel()
	_msg.text = ""
	_tag.text = _tag_text()
	_sync_figure()
	var pk := str(ev.get("passage_kind", p.get("kind", "normal")))
	var t := float(ev["t"])
	if pk == "death":
		_msg.text = "YOU DIED"
		_msg.add_theme_color_override("font_color", Color(1.0, 0.45, 0.4))
		_dark_t0 = t
		_dark_kind = "death"
		_act(zone, "player_look", t, {"pitch": -22.0, "bars": 2.0})
		_act(zone, "fx_queasy", t, {"amount": 0.5, "bars": 3.0})
	elif pk == "victory":
		_msg.text = "VICTORY"
		_msg.add_theme_color_override("font_color", Color(1.0, 0.95, 0.6))
		_dark_t0 = t
		_dark_kind = "victory"
		_act(zone, "player_look", t, {"pitch": 12.0, "bars": 2.0})
	else:
		_dark_t0 = -1.0
	if _until > 0 and engine.flow.passage == _until:
		print("TRIAL reached passage %d" % engine.flow.passage)
		print("TRIAL ", host.frame_stats())
		if OS.get_environment("RW_STORY_QUIT") == "1" and OS.get_environment("RW_TRIAL_LEAVE_QUIT") != "1":
			host.get_tree().quit()


func _tag_text() -> String:
	var t := tdata.zone_name(engine.flow.passage)
	if not engine.flow.flags.is_empty():
		var names: Array = engine.flow.flags.map(func(f: Variant) -> String: return str(tdata.items.get(str(f), f)))
		t += "  ·  carrying " + ", ".join(PackedStringArray(names))
	return t


func _open_window(ev: Dictionary) -> void:
	_items = hotspots.visible(engine.flow.passage, engine.flow.flags)
	_choice_layer.visible = true
	_place_choices()
	if _outcome.is_empty():
		_sync_figure()
	_commit_view = {}
	_sel_t = {}
	_script_pick = -1
	_script_pick_at = -1.0
	if _script_i < _script_choices.size():
		var tok := _script_choices[_script_i].strip_edges()
		_script_i += 1
		if tok != "" and tok != "d":
			_script_pick = int(tok)
			_script_pick_at = float(ev["t"]) + 1.0
	if _outcome.is_empty() and _pending.is_empty():
		_panel.visible = true
		_desc.visible = true


## What the hotspot view of zone `z` draws and a tap hits: [{index, hotspot, state, t_state}] for the open window's hotspots (once the passage's zone is the one on screen: after a zone swap the lights
## come up in the new room), plus the one that has just committed (it stays for its flash). `hotspot` is the contract's hotspot; its `default` is true only while nothing is picked (the default is
## brighter until the player chooses).
func _view_items(z: String) -> Array:
	var out: Array = []
	if engine == null or not active:
		return out
	if z == zone and engine.window_open and not _items.is_empty() and tdata.zone_of_passage(engine.flow.passage) == z:
		var def := engine.default_index()
		for it in _items:
			var h: Dictionary = (it["hs"] as Dictionary).duplicate()
			var i := int(it["index"])
			h["default"] = i == def and engine.selected < 0
			var sel := i == engine.selected
			out.append({"index": i, "hotspot": h, "state": "selected" if sel else "available", "t_state": float(_sel_t.get(i, 0.0)) if sel else 0.0})
	if not _commit_view.is_empty() and str(_commit_view["zone"]) == z:
		if _last_t - float(_commit_view["t"]) < 2.0 * _beat_s:
			out.append({"index": int(_commit_view["index"]), "hotspot": _commit_view["hs"], "state": "committed", "t_state": float(_commit_view["t"])})
		else:
			_commit_view = {}
	return out


## The lights of the open window (what the hotspot view shows now): [{index, hotspot, state, t_state}].
func hotspot_items() -> Array:
	return _view_items(zone)


func hotspot_of(index: int) -> Dictionary:
	for it in _items:
		if int(it["index"]) == index:
			return it["hs"]
	return {}


## The screen placement of the open window's hotspots in the stage area: HotspotView.layout (the same pure function the view draws with).
func hotspot_layout() -> Array:
	var st := _stage(zone)
	var pose := _exit_pose()
	var rect := _stage_rect()
	if st == null or st.map == null or pose.is_empty() or rect.size.x <= 1.0:
		return []
	return HotspotView.layout(hotspot_items().filter(func(e: Dictionary) -> bool: return str(e["state"]) != "committed"), st.map, st.crowds, pose, rect.size)


func _stage_rect() -> Rect2:
	var sh: Control = host._stage_host
	return Rect2(sh.global_position, sh.size)


## A touch or click at `pos` (viewport coordinates): only the stage area counts and never a point over a pad (RunPlay hands the touches here while the dungeon is in). The nearest hotspot within
## its projected radius, at least min_px wide, is picked. Returns the choice index hit (-1 for a tap on nothing).
func hotspot_tap(pos: Vector2) -> int:
	if not active or engine == null or not engine.window_open:
		return -1
	var rect := _stage_rect()
	if not rect.has_point(pos):
		return -1
	var rects: Dictionary = host.pad_view.button_rects()
	for p in rects:
		if (rects[p] as Rect2).has_point(pos):
			return -1
	var id := HotspotView.hit(hotspot_layout(), pos - rect.position)
	if id == "":
		return -1
	for it in _items:
		if str((it["hs"] as Dictionary)["id"]) == id:
			pick(int(it["index"]))
			return int(it["index"])
	return -1


## A finger on the centre of hotspot `index` through the same hit test (a script's or a test's tap). Returns the index hit (-1 when it cannot be reached).
func tap_centre(index: int) -> int:
	var rect := _stage_rect()
	var want := str(hotspot_of(index).get("id", ""))
	for e in hotspot_layout():
		if want == str(e["id"]):
			return hotspot_tap((e["centre"] as Vector2) + rect.position)
	return -1


## Bars left of the open window (4 down to 1; 0 when none).
func bars_left() -> int:
	if engine == null or not engine.window_open:
		return 0
	return int(ceil(engine.window_left(_last_t) / (4.0 * _beat_s)))


## The player picks (or changes their pick) in the open window: a tap on a hotspot, a key, or a script.
func pick(i: int) -> void:
	if engine != null and engine.select(i):
		trace.append({"kind": "pick", "choice": i, "t": _last_t})
		_sel_t[i] = _last_t


func _unhandled_key_input(event: InputEvent) -> void:
	if active and event is InputEventKey and event.pressed and not event.echo and engine != null and engine.window_open:
		var k := (event as InputEventKey).keycode
		if k >= KEY_1 and k <= KEY_4 and k - KEY_1 < _items.size():
			pick(k - KEY_1)


func _on_commit(ev: Dictionary) -> void:
	_choice_layer.visible = false
	var cs := engine.flow.choices()
	var i := int(ev["choice"])
	var hs := hotspot_of(i)
	if not hs.is_empty():  # the committed hotspot flashes for a moment
		_commit_view = {"index": i, "hs": hs, "zone": zone, "t": float(ev["t"])}
	_items = []
	_last_exit = ""
	if i >= 0 and i < cs.size():
		_last_exit = str(cs[i].get("exit_wp", ""))
	if _last_exit != "" and zone != "":  # the head turns to the way it takes
		_act(zone, "player_look", float(ev["t"]), {"at": _last_exit, "bars": 1.0})
	if bool(ev["defaulted"]):
		var label := str(ev.get("label", ""))
		_news.text = "The moment passes: " + (label if label != "" else "you drift on") + "."
		_news.visible = true
	# the next zone is built in this cue-free guard
	var cs2 := cs
	if i >= 0 and i < cs2.size() and cs2[i].get("to", null) != null and not host.virtual_mode:
		var z := str(tdata.passage(int(cs2[i]["to"]))["zone"])
		if not zone_stages.has(z):
			build_zone(z)


func _on_phrase(ev: Dictionary) -> void:
	_news.visible = false
	_panel.visible = false
	_desc.visible = false
	var enc := str(ev["encounter"])
	if enc != "" and not _stage(zone) == null:
		var e: Dictionary = tdata.encounters[enc]
		if _fig.is_empty() or str(_fig["id"]) != enc:  # (it already stands in the room: the creature is the hotspot that was tapped)
			_spawn_figure(enc, float(ev["t"]))
		_news.text = str(e["intro"])
		_news.visible = true
		_panel.visible = true
		_fit_panel()
	_msg.text = ""


func _on_result(ev: Dictionary) -> void:
	_msg.text = ""
	var t := float(ev["t"])
	if bool(ev["fight"]):
		_outcome = {"t0": t, "kind": str(ev["outcome"])}
		_msg.text = "DEFEATED!" if str(ev["outcome"]) == "win" else ("BEATEN" if bool(ev.get("defeated", false)) else "HURT!")
		_msg.add_theme_color_override("font_color", Color(0.6, 1.0, 0.8) if str(ev["outcome"]) == "win" else Color(1.0, 0.55, 0.45))
		if str(ev["outcome"]) != "win":
			_fail_look(t)
	else:
		_msg.text = "WELL PLAYED" if str(ev["result"]) == "pass" else "MISSED: TRY AGAIN"
		_msg.add_theme_color_override("font_color", Color(0.6, 1.0, 0.8) if str(ev["result"]) == "pass" else Color(1.0, 0.7, 0.5))
		if str(ev["result"]) != "pass":
			_fail_look(t)


func _on_exit(ev: Dictionary) -> void:
	var t := float(ev["t"])
	_msg.text = ""
	leave_reason = str(ev["reason"])
	left_t = next_boundary(t + 1.0e-6)
	_ap_t = left_t
	var span := (left_t - t) / (4.0 * _beat_s)
	_move(zone, _last_exit, t, span)
	_choice_layer.visible = false
	_items = []


# --- creatures ---------------------------------------------------------------------------------------------------------------

func _drop_figure() -> void:
	if not _fig.is_empty() and is_instance_valid(_fig["node"]):
		(_fig["node"] as Node).queue_free()
	_fig = {}
	_fig_pose = ""


func figure_spot(z: String, wp_id: String, dist: float) -> Dictionary:
	var m := _map(z)
	var w: Dictionary = m.waypoint(wp_id)
	var at: Vector2 = w["at"]
	var fwd := m.forward_of_yaw(float(w["yaw"]))
	var d := dist
	while d >= 1.2:
		var p := at + fwd * d
		var sid := m.sector_at(p)
		if sid != "" and m.inside(p, sid, 0.5):
			return {"pos": p, "sec": sid}
		d -= 0.4
	return {"pos": at + fwd * 1.2, "sec": str(w["sector"])}


## The creature of the open window stands in the room as its hotspot (tap it to fight): spawned when a window opens on a passage with a fight on offer, dropped when the passage
## has none. Never mid-phrase, mid-outcome or mid-swap.
func _sync_figure() -> void:
	if engine == null or not engine.window_open or swap_t >= 0.0 or zone == "" or not _outcome.is_empty():
		return
	var want := ""
	for c in engine.choices():
		if str(c.get("encounter", "")) != "":
			want = str(c["encounter"])
			break
	if want == "":
		if not _fig.is_empty():
			_drop_figure()
	elif _fig.is_empty() or str(_fig["id"]) != want:
		_spawn_figure(want, _last_t)


func _spawn_figure(enc: String, t: float) -> void:
	_drop_figure()
	var st := _stage(zone)
	if st == null or st.world == null or not FIGURES.has(enc):
		return
	var spec: Dictionary = FIGURES[enc]
	var wp := str(engine.flow.current().get("waypoint", ""))
	var spot := figure_spot(zone, wp, float(spec["dist"]))
	var tex := _assets.texture("textures/fig_%s_idle.png" % enc)
	var q := QuadMesh.new()
	var h := float(spec["size"])
	q.size = Vector2(h, h)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_texture = tex
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	var mi := MeshInstance3D.new()
	mi.name = "Figure_" + enc
	mi.mesh = q
	mi.material_override = mat
	st.world.add_child(mi)
	_fig = {"node": mi, "mat": mat, "id": enc, "pos": spot["pos"], "sec": spot["sec"], "spec": spec, "t0": t, "stage": st, "acting": _figure_acting(enc)}
	_fig_pose = "idle"
	_animate_figure(t)


func figure_pose() -> String:
	return _fig_pose


## The `acting` block of the hotspot whose creature this is (content/trial/hotspots.json, authored by tools/trial/make_hotspots.py's table), looked up in the passage on show.
func _figure_acting(enc: String) -> Dictionary:
	if engine == null:
		return {}
	for h in tdata.hotspots.get(engine.flow.passage, []):
		if typeof(h.get("acting", null)) == TYPE_DICTIONARY and str(h["acting"].get("figure", "")) == enc:
			return {"block": h["acting"], "choice": int(h.get("choice", -1))}
	return {}


## What the creature is doing at song time `t`: {act, u (beats since it began)}: its `available` act while it waits, `selected` once the player has tapped it or the fight is on, `success` when it is
## beaten, `failure` when it beats the player. An empty act when it has no acting block.
func figure_act_at(t: float) -> Dictionary:
	return _figure_act(t)


func _figure_act(t: float) -> Dictionary:
	var none := {"act": "", "u": 0.0}
	if _fig.is_empty() or (_fig["acting"] as Dictionary).is_empty():
		return none
	var block: Dictionary = _fig["acting"]["block"]
	var phase := "available"
	var t0 := float(_fig["t0"])
	if not _outcome.is_empty():
		phase = "success" if str(_outcome["kind"]) == "win" else "failure"
		t0 = float(_outcome["t0"])
	elif engine != null and (engine.selected == int(_fig["acting"]["choice"]) or not engine.window_open):
		phase = "selected"
		t0 = maxf(float(_sel_t.get(int(_fig["acting"]["choice"]), t0)), t0)
	var spec: Variant = block.get(phase, block.get("available", {}))
	if typeof(spec) != TYPE_DICTIONARY:
		return none
	return {"act": str((spec as Dictionary).get("act", "")), "u": maxf(t - t0, 0.0) / _beat_s}

func _animate_figure(t: float) -> void:
	if _fig.is_empty() or not is_instance_valid(_fig["node"]):
		return
	var st: StoryStage = _fig["stage"]
	var spec: Dictionary = _fig["spec"]
	var m: StoryMap = st.map
	var pos: Vector2 = _fig["pos"]
	var floor_y := float(m.sector(str(_fig["sec"])).get("floor", 0.0))
	var h := float(spec["size"])
	var pose := "idle"
	var sc_x := 1.0
	var sc_y := 1.0
	var y := floor_y + float(spec["lift"]) + h * 0.5 + sin(t * 2.2) * 0.04
	var sc := 1.0 + 0.03 * pow(1.0 - fposmod(t / _beat_s, 1.0), 3.0)
	var alpha := clampf((t - float(_fig["t0"])) / _beat_s, 0.0, 1.0)  # steps out of the dark over a beat
	var p3 := Vector3(pos.x, y, pos.y)
	if not _outcome.is_empty():
		var k := clampf((t - float(_outcome["t0"])) / OUTCOME_S, 0.0, 1.0)
		if str(_outcome["kind"]) == "win":
			pose = "struck"
			sc *= 1.0 - 0.5 * k * k
			p3.y -= (h * 0.5) * k * k
			alpha *= 1.0 - clampf((k - 0.45) * 1.9, 0.0, 1.0)
		else:
			var lunge := sin(k * PI)
			pose = "attack" if lunge > 0.2 else "idle"
			var cam: Vector3 = st.player.pose_at(t)["cam"]
			var dir := (Vector2(cam.x, cam.z) - pos).normalized()
			p3.x += dir.x * lunge * 1.1
			p3.z += dir.y * lunge * 1.1
			sc *= 1.0 + lunge * 0.35
	var act := _figure_act(t)
	var mo := RunActing.figure_motion(str(act["act"]), float(act["u"])) if str(act["act"]) != "" else {}
	if not mo.is_empty():  # the creature's body language (its `acting` in content/trial/hotspots.json): a motion on the billboard, towards the player and sideways to the view
		var cam2: Vector3 = st.player.pose_at(t)["cam"]
		var to_cam := (Vector2(cam2.x, cam2.z) - pos).normalized()
		p3.x += to_cam.x * float(mo["dz"]) + to_cam.y * float(mo["dx"])
		p3.z += to_cam.y * float(mo["dz"]) - to_cam.x * float(mo["dx"])
		p3.y += float(mo["dy"])
		sc_x = float(mo["sx"])
		sc_y = float(mo["sy"])
	if pose != _fig_pose:
		if OS.get_environment("RW_TRIAL_TRACE") == "1":
			print("TRIAL figure pose ", pose)
		_fig_pose = pose
		(_fig["mat"] as StandardMaterial3D).albedo_texture = _assets.texture("textures/fig_%s_%s.png" % [_fig["id"], pose])
	var node: MeshInstance3D = _fig["node"]
	node.position = p3
	node.scale = Vector3(sc * sc_x, sc * sc_y, sc)
	var col := Color.WHITE
	if st.world != null:
		col = st.world.figure_light(pos, str(_fig["sec"])) * 1.0
	(_fig["mat"] as StandardMaterial3D).albedo_color = Color(col.r, col.g, col.b, alpha)


func _animate_outcome(t: float) -> void:
	var k := clampf((t - float(_outcome["t0"])) / OUTCOME_S, 0.0, 1.0)
	if str(_outcome["kind"]) == "win":
		_flash.color = Color(1, 1, 1, clampf(0.55 - k * 4.0, 0.0, 0.55))
	else:
		_flash.color = Color(1.0, 0.1, 0.05, clampf(sin(k * PI * 2.0) * 0.32, 0.0, 0.32))
	if k >= 1.0:
		var won := str(_outcome["kind"]) == "win"
		_flash.color = Color(1, 1, 1, 0)
		_outcome = {}
		if won:
			_drop_figure()
			_sync_figure()
		if not _pending.is_empty() and swap_t < 0.0:
			var ev := _pending
			_pending = {}
			_show_passage(ev)


# --- the scripted player ------------------------------------------------------------------------------------------------------

## RW_TRIAL_BOT plays the charted cues exactly on time ("perfect"), none of them ("none"), or all but a fight's ("no_fights").
func _bot_step(t: float) -> void:
	if bot == "" or bot == "none" or engine == null:
		return
	var notes := engine.level.notes
	for i in range(maxi(notes.size() - 300, 0), notes.size()):
		var n: Dictionary = notes[i]
		if bot == "no_fights" and str(n.get("enc", "")) != "":
			continue
		if not _pressed.has(i) and float(n["time"]) <= t:
			_pressed[i] = true
			engine.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
			host.pad_view.button_down[int(n["pad"])] = true
		if _pressed.has(i) and not _released.has(i):
			var end_t := float(n["end_time"]) if n["type"] == "hold" else float(n["time"]) + 0.08
			if end_t <= t:
				_released[i] = true
				engine.release(int(n["pad"]), end_t, int(n["pad"]))
				host.pad_view.button_down[int(n["pad"])] = false


## The system back key: the dungeon is left at the next decision tick, by the same walk back up the hatch.
func request_leave() -> void:
	if engine != null and active and left_t < 0.0:
		engine.leave_requested = true


func deactivate() -> void:
	active = false
	visible = false
	_drop_figure()
	_dark_t0 = -1.0
	_fade.color = Color(0, 0, 0, 0)
	_flash.color = Color(1, 1, 1, 0)
	_commit_view = {}
	_items = []
	_choice_layer.visible = false
	for k in zone_stages:
		var s: StoryStage = zone_stages[k]["stage"]
		s.visible = false
		s.process_mode = Node.PROCESS_MODE_DISABLED
	zone = ""
	_pressed = {}
	_released = {}
