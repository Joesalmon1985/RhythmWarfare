class_name StoryStage
extends Control
## The fixed nightclub, seen from the DJ's position: a 1280 x 720 design space drawn from the art manifest and fitted so the
## desk-top line (design y = DESK_Y) sits on the top of the pad strip. Static layers, a moving-head light rig with beams, haze,
## floor effects, the LED screen, woofers, the riser, the crowd, and the authored actions the director sends. Every effect is a
## function of song time (the audio clock) and of action start times; nothing here advances on frame counts.

var desk_y := 460.0  # design y of the desk-top line; a full-screen cutscene stage uses 720
const DESK_Y := 460.0
const DESIGN := Vector2(1280, 720)
const NO_END := 1.0e9
const PALETTES := {
	"low": [Color(0.35, 0.3, 0.9), Color(0.6, 0.25, 0.8)],
	"cool": [Color(0.2, 0.85, 1.0), Color(0.55, 0.35, 1.0)],
	"warm": [Color(1.0, 0.7, 0.25), Color(1.0, 0.35, 0.65)],
	"rave": [Color(1.0, 0.25, 0.8), Color(0.2, 1.0, 0.9), Color(0.7, 0.4, 1.0), Color(1.0, 0.85, 0.3)],
}

var assets: StoryAssets
var data: StoryData
var run: StoryRun
var bpm := 174.0
var reduced := false
var high_contrast := false
var palette := "low"
var palettes: Dictionary = {}  # name -> Array[Color] (the chapter's own, else PALETTES)
var _pieces: Dictionary = {}  # id -> {on_t, off_t, pulse_t, bars}
var energy := 45.0
var t_now := 0.0

var _root: Node2D
var views: Dictionary = {}  # room id -> StoryView
var current_view := "main"
var moving_camera := false  # the chapter has extra rooms: the camera walks and turns between them (Night One stays fixed)
var _cam: Dictionary = {}  # the move in progress or last made: {from, to, style, t0, t1, dir}
var _cam_fx: Array = []  # camera_look / camera_push windows: {kind, t0, t1, amount}
var _cam_overlay: Node2D
var _act := {}  # active timed effects: name -> {t0, t1, args}
var _beam_mode := "sweep"
var _beam_since := 0.0
var _led_mode := "eq"
var _woofer_pump := false
var _ball_on := false
var _ending := ""
var _lean := ""
var _flicker_until := -1.0
var _scale := 1.0
var area_h := 460.0
var action_log: Array = []


func setup(p_assets: StoryAssets, p_data: StoryData, p_run: StoryRun) -> void:
	assets = p_assets
	data = p_data
	run = p_run
	bpm = run.level.bpm
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	_root = Node2D.new()
	_root.name = "Design"
	add_child(_root)
	palettes = PALETTES.duplicate()
	for k in data.palettes:
		var cols: Array = []
		for hex in data.palettes[k]:
			cols.append(Color.html(str(hex)))
		if not cols.is_empty():
			palettes[k] = cols
	for vid in assets.view_ids():
		var v := StoryView.new()
		_root.add_child(v)
		v.build(self, assets, data, str(vid))
		views[str(vid)] = v
	current_view = "main"
	moving_camera = views.size() > 1
	_cam_overlay = StoryCameraOverlay.new()
	_cam_overlay.stage = self
	_root.add_child(_cam_overlay)
	resized.connect(_fit)
	_fit()
	reset()


## The crowd of the room the camera is in (the one the authored actions direct).
var crowd: StoryCrowd:
	get:
		return (views[current_view] as StoryView).crowd


func _all_fx(method: String, args: Array) -> void:
	for id in views:
		((views[id] as StoryView).fx as Object).callv(method, args)


func _set_glow(on: bool) -> void:
	for id in views:
		(views[id] as StoryView).crowd.glow_on = on


func glow_colors() -> Array:
	var rv: Array = palettes.get("rave", PALETTES["rave"])
	return [rv[0], rv[mini(1, rv.size() - 1)], rv[mini(3, rv.size() - 1)]]


func _fit() -> void:
	if _root == null:
		return
	area_h = maxf(size.y, 1.0)
	_scale = maxf(size.x / DESIGN.x, area_h / desk_y)
	_root.scale = Vector2(_scale, _scale)
	_root.position = Vector2((size.x - DESIGN.x * _scale) * 0.5, area_h - desk_y * _scale)


func design_to_global(p: Vector2) -> Vector2:
	return global_position + _root.position + p * _scale


## A cutscene overlay in design space (above the crowd and the lights).
func add_overlay(node: Node2D) -> void:
	_root.add_child(node)


func palette_colors() -> Array:
	return palettes.get(palette, PALETTES["low"])


## Set-piece state at song time t: {visible, alpha, pulse} (a chapter piece switched by piece_on / piece_off / piece_pulse).
func piece_state(id: String, t: float) -> Dictionary:
	var st: Dictionary = _pieces.get(id, {})
	if st.is_empty():
		return {"visible": false, "alpha": 0.0, "pulse": 0.0}
	var on_t: float = st.get("on_t", INF)
	var off_t: float = st.get("off_t", INF)
	var vis := t >= on_t and t < off_t
	var a := 0.0
	if vis:
		a = clampf((t - on_t) / 0.8, 0.0, 1.0)
	elif t >= off_t and t < off_t + 0.8 and t >= on_t:
		a = 1.0 - (t - off_t) / 0.8
	var pulse := 0.0
	if st.has("pulse_t") and t >= float(st["pulse_t"]) and t < float(st["pulse_t"]) + float(st.get("pulse_len", 2.0)):
		pulse = 1.0 - (t - float(st["pulse_t"])) / float(st.get("pulse_len", 2.0))
	return {"visible": vis or a > 0.0, "alpha": a, "pulse": pulse}


func reset() -> void:
	_pieces = {}
	_act = {}
	_beam_mode = "sweep"
	_beam_since = 0.0
	_led_mode = "eq"
	_woofer_pump = false
	_ball_on = false
	_ending = ""
	_lean = ""
	_flicker_until = -1.0
	palette = "low"
	action_log = []
	_cam = {}
	_cam_fx = []
	current_view = "main"
	for id in views:
		(views[id] as StoryView).reset()
		(views[id] as StoryView).visible = id == "main"


func is_active(name: String, t: float) -> bool:
	if not _act.has(name):
		return false
	var a: Dictionary = _act[name]
	return t >= float(a["t0"]) and t < float(a["t1"])


## 0..1 progress of an active effect (or -1).
func progress(name: String, t: float) -> float:
	if not _act.has(name):
		return -1.0
	var a: Dictionary = _act[name]
	if t < float(a["t0"]) or t >= float(a["t1"]):
		return -1.0
	return (t - float(a["t0"])) / maxf(float(a["t1"]) - float(a["t0"]), 0.001)


func since(name: String, t: float) -> float:
	return t - float(_act[name]["t0"]) if _act.has(name) else INF


func bar_s() -> float:
	return 4.0 * 60.0 / bpm


func update(t: float, p_energy: float) -> void:
	t_now = t
	energy = p_energy
	var shown := _visible_views(t)
	for id in views:
		var v: StoryView = views[id]
		v.visible = id in shown
		if not v.visible:
			continue
		v.crowd.reduced = reduced
		v.crowd.set_time(t)
		v.crowd.update(t, p_energy)
		v.redraw_fx()
		if v.layers.has("riser"):
			var sp: Sprite2D = v.layers["riser"]
			var up := _riser_level(t)
			sp.visible = up > 0.01
			sp.modulate = Color(1, 1, 1, up)
	_apply_camera(t)
	_cam_overlay.queue_redraw()
	queue_redraw()


# --- the moving camera (chapters with extra rooms) ------------------------------------------------------------------------------------
## The rooms on screen at song time t: the room being left until its move begins, both during it, the new one after.

func _visible_views(t: float) -> Array:
	if _cam.is_empty():
		return [current_view]
	if t < float(_cam["t0"]):
		return [_cam["from"]]
	if t < float(_cam["t1"]):
		return [_cam["from"], _cam["to"]]
	return [_cam["to"]]


## 0..1 progress of the camera move at t, or -1 when none is under way.
func camera_progress(t: float) -> float:
	if _cam.is_empty() or t < float(_cam["t0"]) or t >= float(_cam["t1"]):
		return -1.0
	return (t - float(_cam["t0"])) / maxf(float(_cam["t1"]) - float(_cam["t0"]), 0.001)


## The room the camera shows at song time t (the target once a move has finished or is past half way).
func view_at(t: float) -> String:
	var u := camera_progress(t)
	if _cam.is_empty() or t < float(_cam["t0"]):
		return str(_cam.get("from", current_view))
	return str(_cam["to"]) if u < 0.0 or u >= 0.5 else str(_cam["from"])


func _apply_camera(t: float) -> void:
	var u := camera_progress(t)
	var beats := t * bpm / 60.0
	for id in views:
		var v: StoryView = views[id]
		if not v.visible:
			continue
		var pivot := v.vanish
		var s := 1.0
		var off := Vector2.ZERO
		var rot := 0.0
		var a := 1.0
		if moving_camera and u >= 0.0:
			var e := u * u * (3.0 - 2.0 * u)
			var style := str(_cam["style"])
			var bump := sin(u * PI)
			var bob := Vector2(0.0, sin(u * TAU * 3.0) * 6.0 * bump)
			var roll := 0.012 * sin(u * TAU * 3.0) * bump
			if reduced:
				bob = Vector2.ZERO
				roll = 0.0
			if style == "turn_left" or style == "turn_right" or style == "turn":
				var dir := -1.0 if style == "turn_left" else 1.0
				if id == _cam["from"]:
					off = Vector2(-dir * DESIGN.x * 0.92 * e, 0.0) + bob
					s = 1.0 - 0.05 * e
					rot = roll
				else:
					off = Vector2(dir * DESIGN.x * 0.92 * (1.0 - e), 0.0) + bob
					s = 0.95 + 0.05 * e
					rot = roll
			else:  # walk / step: a dolly forward
				if id == _cam["from"]:
					s = lerpf(1.0, 2.4, e * e)
					a = 1.0 - clampf((u - 0.4) / 0.6, 0.0, 1.0)
				else:
					s = lerpf(0.55, 1.0, e)
					a = clampf(u * 2.2, 0.0, 1.0)
				off = bob
				rot = roll
		elif moving_camera and id == current_view:
			if not reduced:  # first-person breathing: a slow sway and a small bob on the beat
				off = Vector2(sin(beats * 0.25 * PI) * 3.0, absf(sin(beats * 0.5 * PI)) * -2.0)
				rot = 0.004 * sin(beats * 0.125 * PI)
		if moving_camera and id == current_view or id == str(_cam.get("to", "")):
			for f in _cam_fx:
				if t >= float(f["t0"]) and t < float(f["t1"]):
					var fu: float = (t - float(f["t0"])) / maxf(float(f["t1"]) - float(f["t0"]), 0.001)
					var env := sin(fu * PI)
					if f["kind"] == "look":
						off.x += float(f["amount"]) * env
					else:
						s *= 1.0 + float(f["amount"]) * env
		var rp := (pivot * s).rotated(rot)
		v.scale = Vector2(s, s)
		v.rotation = rot
		v.position = pivot - rp + off
		v.modulate = Color(1, 1, 1, a)
	if moving_camera and u >= 0.0 and str(_cam["style"]) not in ["turn_left", "turn_right", "turn"]:
		var to_v: StoryView = views[_cam["to"]]
		var from_v: StoryView = views[_cam["from"]]
		if to_v.get_index() > from_v.get_index():
			_root.move_child(to_v, from_v.get_index())  # the room we are walking out of stays in front while it fades


## The passage frame the camera walks through and speed lines, drawn over the rooms during a forward move.
func draw_camera_overlay(ci: CanvasItem) -> void:
	var u := camera_progress(t_now)
	if u < 0.0 or not moving_camera:
		return
	var style := str(_cam["style"])
	if style in ["turn_left", "turn_right", "turn"]:
		return
	var vp: Vector2 = (views[_cam["from"]] as StoryView).vanish
	var env := sin(u * PI)
	if not reduced:
		for i in 28:
			var ang := TAU * float(i) / 28.0 + 0.1
			var r0 := 120.0 + 140.0 * u
			ci.draw_line(vp + Vector2.from_angle(ang) * r0, vp + Vector2.from_angle(ang) * (r0 + 380.0 * env), Color(1, 1, 1, 0.12 * env), 2.0)
	var pf := assets.sprite("passage_frame")
	if style == "step" and not pf.is_empty() and pf["tex"] != null:
		var k := lerpf(0.4, 3.6, pow(u, 1.6)) * float(pf["scale"])
		ci.draw_set_transform(vp, 0.0, Vector2(k, k))
		ci.draw_texture(pf["tex"], -pf["pivot"], Color(1, 1, 1, clampf(sin(clampf((u - 0.05) / 0.85, 0.0, 1.0) * PI) * 1.5, 0.0, 1.0)))
		ci.draw_set_transform_matrix(Transform2D.IDENTITY)


func _riser_level(t: float) -> float:
	if _act.has("riser_up") and t >= float(_act["riser_up"]["t0"]) and (not _act.has("riser_down") or float(_act["riser_down"]["t0"]) < float(_act["riser_up"]["t0"])):
		return clampf((t - float(_act["riser_up"]["t0"])) / bar_s(), 0.0, 1.0)
	if _act.has("riser_down") and t >= float(_act["riser_down"]["t0"]):
		return 1.0 - clampf((t - float(_act["riser_down"]["t0"])) / bar_s(), 0.0, 1.0)
	return 0.0


func riser_level(t: float) -> float:
	return _riser_level(t)


func woofer_pump() -> bool:
	return _woofer_pump


func ball_on() -> bool:
	return _ball_on


func beam_mode() -> String:
	return _beam_mode


func beam_since() -> float:
	return _beam_since


func led_mode() -> String:
	return _led_mode


func ending() -> String:
	return _ending


## The staged tableau of the ending reached ("legendary" / "good" / "lost" or "").
func tableau() -> String:
	return data.tableau_of(_ending) if _ending != "" else ""


func lean_tableau() -> String:
	return data.tableau_of(_lean) if _lean != "" else ""


func lean() -> String:
	return _lean


func flickering(t: float) -> bool:
	return t < _flicker_until


## The authored actions. `a` = {t0, bar, action, args, block, source}.
func apply(a: Dictionary) -> void:
	var t0 := float(a["t0"])
	var act := str(a["action"])
	var args: Dictionary = a["args"]
	var bars := float(args.get("bars", 2.0))
	var dur := bars * bar_s()
	action_log.append(a)
	match act:
		"doors_open":
			_act["doors_open"] = {"t0": t0, "t1": t0 + 6.0 * bar_s()}
			_all_fx("door_spill", [t0])
		"lights_low_pulse":
			palette = "low"
		"lights_warm":
			palette = "warm"
		"lights_cool":
			palette = "cool"
		"lights_rave":
			palette = "rave"
		"beams_sweep", "beams_fan", "beams_cross", "beams_off":
			_beam_mode = act.trim_prefix("beams_")
			_beam_since = t0
		"bass_reveal":
			_act["bass_reveal"] = {"t0": t0, "t1": t0 + 4.0 * bar_s()}
			if palette == "low":
				palette = "cool"
			_all_fx("haze_burst", [t0])
			crowd.direct(crowd.present_ids(), "dance", t0, 3.0 * bar_s())
		"haze_burst":
			_all_fx("haze_burst", [t0])
		"led_eq", "led_rings", "led_bars", "led_wave":
			_led_mode = act.trim_prefix("led_")
		"disco_ball_on":
			_ball_on = true
		"woofer_pump_on":
			_woofer_pump = true
		"woofer_pump_off":
			_woofer_pump = false
		"spotlight_hero":
			_act["spot_hero"] = {"t0": t0, "t1": t0 + 8.0 * bar_s()}
		"spotlight_sweep":
			_act["spot_sweep"] = {"t0": t0, "t1": t0 + 4.0 * bar_s()}
		"spotlight_off":
			_act.erase("spot_hero")
			_act.erase("spot_sweep")
			_act.erase("spot_circle")
		"riser_up":
			_act["riser_up"] = {"t0": t0, "t1": NO_END}
			_act.erase("riser_down")
		"riser_down":
			_act["riser_down"] = {"t0": t0, "t1": NO_END}
			crowd.hero_to(crowd.actors[crowd.hero_id()]["home"] if crowd.hero_id() != "" else Vector2(640, 380), t0, 2.0)
		"confetti":
			_act["confetti"] = {"t0": t0, "t1": t0 + 5.0}
		"glowsticks_on":
			_set_glow(true)
		"glowsticks_off":
			_set_glow(false)
		"light_wave":
			_act["light_wave"] = {"t0": t0, "t1": t0 + dur}
			crowd.wave(t0, dur * 0.8, 1.2, "cheer")
		"floor_ripple":
			_act["floor_ripple"] = {"t0": t0, "t1": t0 + dur}
			crowd.wave(t0, dur * 0.7, 1.4, "dance")
		"rave_peak":
			_act["rave_peak"] = {"t0": t0, "t1": t0 + dur}
			palette = "rave"
			_beam_mode = "sweep"
			_beam_since = t0
			crowd.direct(crowd.present_ids(), "dance", t0, dur, true)
		"front_row_sway":
			crowd.direct(_front_ids(), "dance" if energy > 30.0 else "idle", t0, dur)
		"clap_sync":
			crowd.direct(crowd.present_ids(), "clap", t0, dur, true)
		"wave_across":
			crowd.wave(t0, dur * 0.85, 1.3, "cheer")
		"jump_sync":
			crowd.direct(crowd.present_ids(), "cheer", t0, dur, true)
		"hands_up_all":
			crowd.direct(crowd.present_ids(), "hands_up", t0, dur)
		"look_around":
			crowd.direct(crowd.present_ids(), "look", t0, dur)
		"applause":
			crowd.direct(crowd.present_ids(), "clap", t0, 2.0 * bar_s())
		"group_footwork":
			var ids: Array = crowd.present_ids() if str(args.get("group", "all")) == "all" else crowd.ids_of(str(args["group"]))
			crowd.direct(ids, "footwork", t0, dur, true)
		"circle_form":
			crowd.circle_form(t0)
			_act["circle"] = {"t0": t0, "t1": NO_END}
		"hero_center":
			crowd.hero_to(Vector2(crowd.circle_c.x, crowd.circle_c.y + 18.0), t0, 2.5)
			_act["spot_circle"] = {"t0": t0, "t1": t0 + 6.0 * bar_s()}
		"hero_solo":
			var h := crowd.hero_id()
			if h != "":
				var rl: Array = assets.anchor("riser", [crowd.circle_c.x, crowd.circle_c.y - 20.0, 260], current_view)
				crowd.walk_to(h, Vector2(float(rl[0]), float(rl[1]) - 6.0), t0, 2.0, {"state": "dance", "from": 0.0, "until": t0 + dur, "sync": false})
		"bring_in":
			crowd.bring_in(str(args["group"]), t0)
		"gather_at_door":
			crowd.gather_at_door(str(args["group"]), t0)
		"regroup":
			crowd.regroup(t0)
			_act.erase("circle")
		"ending_lean":
			_lean = str(args.get("ending", ""))
		"new_dancers_enter":
			crowd.gatherers_enter(t0, true)
			palette = "warm"
		"dancers_step_back":
			crowd.gatherers_enter(t0, false)
			crowd.step_back_some(t0)
		"circle_spotlight_cheer":
			_act["spot_circle"] = {"t0": t0, "t1": t0 + 6.0 * bar_s()}
			_act["burst"] = {"t0": t0, "t1": t0 + 4.0 * bar_s()}
			crowd.hero_to(Vector2(crowd.circle_c.x, crowd.circle_c.y + 18.0), t0, 1.5)
			crowd.direct(crowd.ids_of("circle"), "cheer", t0 + 1.5, 4.0 * bar_s(), true)
			_act["confetti"] = {"t0": t0, "t1": t0 + 4.0}
		"circle_breaks_awkward":
			_act["spot_circle"] = {"t0": t0, "t1": t0 + 2.0 * bar_s()}
			_act["flicker"] = {"t0": t0, "t1": t0 + 2.0 * bar_s()}
			crowd.circle_scatter(t0, true)
			crowd.direct(crowd.present_ids(), "look", t0, 3.0 * bar_s())
		"drop_synchronised_jump":
			_act["bass_reveal"] = {"t0": t0, "t1": t0 + 4.0 * bar_s()}
			_act["light_wave"] = {"t0": t0, "t1": t0 + 2.0 * bar_s()}
			_act["burst"] = {"t0": t0, "t1": t0 + 4.0 * bar_s()}
			palette = "rave"
			_woofer_pump = true
			_beam_mode = "fan"
			_beam_since = t0
			_all_fx("haze_burst", [t0])
			crowd.direct(crowd.present_ids(), "cheer", t0, 4.0 * bar_s(), true)
		"drop_stumble":
			_flicker_until = t0 + 2.0 * bar_s()
			_beam_mode = "off"
			_beam_since = t0
			palette = "low"
			crowd.direct(crowd.present_ids(), "look", t0, 2.0 * bar_s())
			crowd.direct(crowd.present_ids(), "dance", t0 + 2.0 * bar_s(), 2.0 * bar_s())
		"final_chant":
			_set_glow(true)
			palette = "rave"
			_act["burst"] = {"t0": t0, "t1": t0 + 4.0 * bar_s()}
			crowd.direct(crowd.present_ids(), "hands_up", t0, 6.0 * bar_s())
		"final_flicker":
			_flicker_until = t0 + 4.0 * bar_s()
			palette = "low"
			crowd.direct(crowd.present_ids(), "look", t0, 2.0 * bar_s())
			crowd.step_back_some(t0)
		"winback_cheer":
			_act["burst"] = {"t0": t0, "t1": t0 + 3.0 * bar_s()}
			crowd.direct(crowd.present_ids(), "cheer", t0, 3.0 * bar_s())
			_act["spot_sweep"] = {"t0": t0, "t1": t0 + 4.0 * bar_s()}
		"move_to":
			var to := str(args.get("view", "main"))
			if views.has(to) and moving_camera and to != current_view:
				_cam = {"from": current_view, "to": to, "style": str(args.get("style", "walk")), "t0": t0, "t1": t0 + float(args.get("bars", 2.0)) * bar_s()}
				current_view = to
		"camera_look":
			_cam_fx.append({"kind": "look", "t0": t0, "t1": t0 + dur, "amount": float(args.get("dx", 90.0))})
		"camera_push":
			_cam_fx.append({"kind": "push", "t0": t0, "t1": t0 + dur, "amount": float(args.get("zoom", 0.12))})
		"piece_on":
			var st: Dictionary = _pieces.get(str(args["piece"]), {})
			st["on_t"] = t0
			st.erase("off_t")
			_pieces[str(args["piece"])] = st
		"piece_off":
			var st2: Dictionary = _pieces.get(str(args["piece"]), {})
			st2["off_t"] = t0
			_pieces[str(args["piece"])] = st2
		"piece_pulse":
			var st3: Dictionary = _pieces.get(str(args["piece"]), {})
			if not st3.has("on_t"):
				st3["on_t"] = t0
			st3["pulse_t"] = t0
			st3["pulse_len"] = maxf(float(args.get("bars", 2.0)) * bar_s(), 0.5)
			_pieces[str(args["piece"])] = st3
		"ending":
			_ending = str(args["ending"])
			for vid in views:
				(views[vid] as StoryView).crowd.set_ending(_ending)
			_act["ending"] = {"t0": t0, "t1": NO_END}
			match data.tableau_of(_ending):
				"legendary":
					palette = "rave"
					_set_glow(true)
					_beam_mode = "fan"
					_woofer_pump = true
					_act["confetti"] = {"t0": t0, "t1": t0 + 8.0}
					_act["burst"] = {"t0": t0, "t1": NO_END}
					_act["spot_hero"] = {"t0": t0, "t1": NO_END}
				"good":
					palette = "warm"
					_set_glow(true)
					_beam_mode = "sweep"
				_:
					palette = "low"
					_set_glow(false)
					_beam_mode = "off"
					_act.erase("spot_hero")
					_act.erase("spot_circle")
			_beam_since = t0


func _front_ids() -> Array:
	var out: Array = []
	for id in crowd.present_ids():
		if str(crowd.actors[id]["data"].get("role", "")) in ["front", "hero"]:
			out.append(id)
	return out


## The two-bar result: a local reaction now; the persistent mood is the energy.
func on_sequence(result: Dictionary, t0: float) -> void:
	crowd.react(bool(result["passed"]), str(result["grade"]), t0)
	_all_fx("pulse", [bool(result["passed"]), t0])
