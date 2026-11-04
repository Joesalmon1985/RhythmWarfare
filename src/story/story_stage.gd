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
var _ambient: Dictionary = {}  # ids of the extra rooms' own pieces
var energy := 45.0
var t_now := 0.0

var _root: Node2D
var views: Dictionary = {}  # room id -> StoryView
var current_view := "main"
var moving_camera := false  # the chapter has extra rooms: the camera walks and turns between them (Night One stays fixed)
var _cam: Dictionary = {}  # the move in progress or last made: {from, to, style, t0, t1, dir}
var _main_palette := ""  # the main room's light when the camera last left it
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

## The 2.5D world (docs/STORY_25D_PLAN.md): a chapter with a map file gets a StoryWorld seen through a low-res viewport by the player's rail camera.
## Until the crowd bridge (WP4) the 2D crowd is still drawn over it in design space and the old 2D room art and light effects are hidden.
var map: StoryMap
var player: StoryPlayer  # the rail camera and the journey (roles, queasy, sick); also exists without nodes (tests)
var lowres: StoryLowRes
var world: StoryWorld
var free_look := StoryFreeLook.new()
var world_active := false


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
		if vid != "main":
			for pc in assets.pieces(str(vid)):
				_ambient[str(pc["id"])] = true
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


## Give the stage a map: the player's rail always; with `with_nodes` also the 3D world behind the crowd (needs no renderer to build).
func attach_world(p_map: StoryMap, with_nodes := true) -> void:
	map = p_map
	player = StoryPlayer.new()
	player.setup(map, bpm)
	player.reduced = reduced
	if not with_nodes:
		return
	lowres = StoryLowRes.new()
	lowres.name = "World3D"
	lowres.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(lowres)
	move_child(lowres, 0)  # behind the 2D crowd
	world = StoryWorld.new()
	world.name = "World"
	world.build(map, assets)
	lowres.attach(world)
	world_active = true
	mouse_filter = Control.MOUSE_FILTER_STOP  # the stage area takes the head-turn drag; the pad strip below is another control


func _process(delta: float) -> void:
	if not world_active:
		return
	var axis := 0.0
	if Input.is_key_pressed(KEY_Q):
		axis += 1.0
	if Input.is_key_pressed(KEY_E):
		axis -= 1.0
	free_look.set_key_axis(axis)
	free_look.update(delta, player.look_active(t_now))


func _gui_input(event: InputEvent) -> void:
	if not world_active:
		return
	if event is InputEventMouseMotion and (event.button_mask & MOUSE_BUTTON_MASK_LEFT) != 0:
		free_look.drag(event.relative.x)
	elif event is InputEventScreenDrag:
		free_look.drag(event.relative.x)
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT and not event.pressed:
		free_look.release()
	elif event is InputEventScreenTouch and not event.pressed:
		free_look.release()


## The waypoints the journey has been sent to, in order (what a playtest compares with the authored expectation).
func journey() -> Array:
	var out: Array = []
	for a in action_log:
		if str(a["action"]) == "player_move":
			out.append(str(a["args"].get("to", "")))
	return out


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
	var ambient: bool = _ambient.has(id)  # a room's own pieces are on whenever that room is shown, unless the script says otherwise
	if st.is_empty():
		return {"visible": ambient, "alpha": 1.0 if ambient else 0.0, "pulse": 0.0}
	var on_t: float = st.get("on_t", -INF if ambient else INF)
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
	if player != null:
		player.reset()
	free_look.reset()
	_cam = {}
	_cam_fx = []
	_main_palette = ""
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
		v.crowd.lit_id = v.crowd.hero_id() if is_active("spot_hero", t) or is_active("spot_circle", t) else ""
		v.crowd.set_time(t)
		v.crowd.update(t, p_energy)
		v.redraw_fx()
		if v.layers.has("riser"):
			var sp: Sprite2D = v.layers["riser"]
			var up := _riser_level(t)
			var lift := riser_lift(t)
			sp.visible = up > 0.01
			sp.modulate = Color(1, 1, 1, up)
			if not sp.has_meta("base_y"):
				sp.set_meta("base_y", sp.position.y)
			sp.position.y = float(sp.get_meta("base_y")) - lift
			var rl: Array = assets.anchor("riser", [], id)
			v.crowd.riser_lift = lift
			if rl.size() >= 2:
				v.crowd.riser_pos = Vector2(float(rl[0]), float(rl[1]) - 6.0)
	_apply_camera(t)
	_cam_overlay.queue_redraw()
	if player != null:
		player.reduced = reduced
		if world_active:
			_update_world(t, p_energy, shown)
	queue_redraw()


func _update_world(t: float, p_energy: float, shown: Array) -> void:
	var pose := player.pose_at(t)
	lowres.apply_pose(pose, free_look.offset)
	world.update(t, {"bpm": bpm, "palette": palette_colors(), "energy": p_energy, "flicker": flickering(t), "strobe": 0.0, "woofer_pump": _woofer_pump})
	for id in shown:  # the old room art and light drawing give way to the 3D world; the crowd stays (until WP4)
		var v: StoryView = views[id]
		v.far.visible = false
		v.near.visible = false
		v.top.visible = false
		for l in v.fx_layers:
			l.visible = false


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
		var cam := _view_cam(str(id), t, u, beats)
		var pivot := v.vanish
		var mk := func(f: float) -> Transform2D: return _cam_xf(pivot, cam, f)
		var xf: Transform2D = mk.call(1.0)
		v.transform = xf
		v.modulate = Color(1, 1, 1, float(cam["a"]))
		v.set_parallax(xf, mk)
	if moving_camera and u >= 0.0 and not _is_turn():
		var to_v: StoryView = views[_cam["to"]]
		var from_v: StoryView = views[_cam["from"]]
		if to_v.get_index() > from_v.get_index():
			_root.move_child(to_v, from_v.get_index())  # the room we are walking out of stays in front while it fades


func _is_turn() -> bool:
	return str(_cam.get("style", "")) in ["turn_left", "turn_right", "turn"]


## One room's camera at song time t: {s (dolly scale about the room's vanishing point), slide (a pan, scaled by parallax), bob
## (the walker's head, not parallaxed), rot (roll), a (opacity)}. Steps land on the beat: the head bob and roll follow the song.
func _view_cam(id: String, t: float, u: float, beats: float) -> Dictionary:
	var s := 1.0
	var slide := Vector2.ZERO
	var bob := Vector2.ZERO
	var rot := 0.0
	var a := 1.0
	if moving_camera and u >= 0.0:
		var e := u * u * (3.0 - 2.0 * u)
		var bump := sin(u * PI)  # the walk starts and ends at rest
		var step := sin(PI * beats)  # one footfall per beat
		if not reduced:
			bob = Vector2(2.5 * step * bump, -7.0 * absf(step) * bump)
			rot = 0.008 * step * bump
		var style := str(_cam["style"])
		if _is_turn():
			var dir := -1.0 if style == "turn_left" else 1.0
			if id == _cam["from"]:
				slide = Vector2(-dir * DESIGN.x * 0.92 * e, 0.0)
				s = 1.0 - 0.05 * bump
			else:
				slide = Vector2(dir * DESIGN.x * 0.92 * (1.0 - e), 0.0)
				s = 1.0 - 0.05 * bump
			rot += dir * 0.015 * bump  # lean into the turn
		elif style == "step":  # walk up to a doorway and through it (StoryCameraOverlay draws the frame)
			if id == _cam["from"]:
				var ua := clampf(u / 0.45, 0.0, 1.0)
				s = lerpf(1.0, 1.7, ua * ua)
				a = 1.0 - clampf((u - 0.22) / 0.2, 0.0, 1.0)
			else:
				var ub := clampf((u - 0.3) / 0.7, 0.0, 1.0)
				s = lerpf(0.72, 1.0, ub * ub * (3.0 - 2.0 * ub))
				a = clampf((u - 0.1) / 0.2, 0.0, 1.0)
		else:  # walk: a dolly forward, the next room resolving out of the vanishing point
			if id == _cam["from"]:
				s = lerpf(1.0, 2.0, e * e)
				a = 1.0 - clampf((u - 0.35) / 0.4, 0.0, 1.0)
			else:
				s = lerpf(0.6, 1.0, e)
				a = clampf((u - 0.15) / 0.4, 0.0, 1.0)
	elif moving_camera and id == current_view and not reduced:  # first-person breathing: a slow sway and a small bob on the beat
		bob = Vector2(sin(beats * 0.25 * PI) * 3.0, absf(sin(beats * 0.5 * PI)) * -2.0)
		rot = 0.004 * sin(beats * 0.125 * PI)
	if moving_camera and id == current_view or id == str(_cam.get("to", "")):
		for f in _cam_fx:
			if t >= float(f["t0"]) and t < float(f["t1"]):
				var fu: float = (t - float(f["t0"])) / maxf(float(f["t1"]) - float(f["t0"]), 0.001)
				var env := sin(fu * PI)
				env = env * env * (3.0 - 2.0 * env)  # eased in and out, no corner at the ends
				if f["kind"] == "look":
					slide.x += float(f["amount"]) * env
					s = maxf(s, 1.0 + absf(slide.x) / 640.0)  # swell enough that the slid room never shows its edge
				else:
					s *= 1.0 + float(f["amount"]) * env
	return {"s": s, "slide": slide, "bob": bob, "rot": rot, "a": a}


## The transform of a layer at parallax factor f (1 = the dancers' depth): dolly and pan scaled by f, bob and roll shared.
func _cam_xf(pivot: Vector2, cam: Dictionary, f: float) -> Transform2D:
	var s := 1.0 + (float(cam["s"]) - 1.0) * f
	var rot := float(cam["rot"])
	var rp := (pivot * s).rotated(rot)
	return Transform2D(rot, Vector2(s, s), 0.0, pivot - rp + (cam["slide"] as Vector2) * f + (cam["bob"] as Vector2))


## Over the rooms during a move: a step's doorway frame growing past the camera, a turn's corner pillar hiding the seam between
## the two rooms, and faint speed lines (none with reduced effects).
func draw_camera_overlay(ci: CanvasItem) -> void:
	var u := camera_progress(t_now)
	if u < 0.0 or not moving_camera:
		return
	var style := str(_cam["style"])
	var bump := sin(u * PI)
	if _is_turn():
		var dir := -1.0 if style == "turn_left" else 1.0
		var e := u * u * (3.0 - 2.0 * u)
		var from_edge := DESIGN.x * 0.5 + dir * DESIGN.x * 0.5 - dir * DESIGN.x * 0.92 * e  # the old room's trailing edge
		var to_edge := DESIGN.x * 0.5 - dir * DESIGN.x * 0.5 + dir * DESIGN.x * 0.92 * (1.0 - e)  # the new room's leading edge
		var x := (from_edge + to_edge) * 0.5
		var half := 150.0
		for k in 12:  # a soft dark pillar: the corner we turn round
			var w := half * (1.0 - float(k) / 12.0)
			ci.draw_rect(Rect2(x - w, -40.0, w * 2.0, DESIGN.y + 80.0), Color(0.01, 0.0, 0.04, 0.11))
		ci.draw_line(Vector2(x - half * 0.35, -40.0), Vector2(x - half * 0.35, DESIGN.y), Color(1.0, 0.3, 0.75, 0.25), 2.0)
		ci.draw_line(Vector2(x + half * 0.35, -40.0), Vector2(x + half * 0.35, DESIGN.y), Color(0.3, 0.9, 1.0, 0.25), 2.0)
		if not reduced:
			for i in 14:
				var y := 30.0 + float(i) * 31.0
				var len := (80.0 + 60.0 * fposmod(float(i) * 0.37, 1.0)) * bump
				var x0 := fposmod(float(i) * 173.0 - dir * u * 900.0, DESIGN.x)
				ci.draw_line(Vector2(x0, y), Vector2(x0 - dir * len, y), Color(1, 1, 1, 0.06 * bump), 2.0)
		return
	var vp: Vector2 = (views[_cam["from"]] as StoryView).vanish
	if not reduced:
		for i in 28:
			var ang := TAU * float(i) / 28.0 + 0.1
			var r0 := 120.0 + 140.0 * u
			ci.draw_line(vp + Vector2.from_angle(ang) * r0, vp + Vector2.from_angle(ang) * (r0 + 380.0 * bump), Color(1, 1, 1, 0.1 * bump), 2.0)
	var pf := assets.sprite("passage_frame")
	if style == "step" and not pf.is_empty() and pf["tex"] != null:
		# the doorway: first a frame ahead around the vanishing point, covering the screen edges by the time the old room has gone,
		# then it sweeps past the camera as we step through into the new room
		var k: float
		if u < 0.4:
			var ua := u / 0.4
			k = lerpf(1.35, 2.05, ua * ua * (3.0 - 2.0 * ua))
		else:
			var ub := (u - 0.4) / 0.6
			k = lerpf(2.05, 5.5, ub * ub)
		var centre := vp.lerp(DESIGN * 0.5, clampf(u / 0.4, 0.0, 1.0))
		var al := clampf(u / 0.12, 0.0, 1.0) * (1.0 - clampf((u - 0.78) / 0.22, 0.0, 1.0))
		ci.draw_set_transform(centre, 0.0, Vector2(k, k) * float(pf["scale"]))
		ci.draw_texture(pf["tex"], -pf["pivot"], Color(1, 1, 1, al))
		ci.draw_set_transform_matrix(Transform2D.IDENTITY)


func _riser_level(t: float) -> float:
	if _act.has("riser_up") and t >= float(_act["riser_up"]["t0"]) and (not _act.has("riser_down") or float(_act["riser_down"]["t0"]) < float(_act["riser_up"]["t0"])):
		return clampf((t - float(_act["riser_up"]["t0"])) / bar_s(), 0.0, 1.0)
	if _act.has("riser_down") and t >= float(_act["riser_down"]["t0"]):
		return 1.0 - clampf((t - float(_act["riser_down"]["t0"]) - bar_s()) / (0.5 * bar_s()), 0.0, 1.0)
	return 0.0


func riser_level(t: float) -> float:
	return _riser_level(t)


const RISER_LIFT := 72.0  # design px the riser raises its performer above the crowd's heads


## How high the riser stands at t: it waits for the performer to step on (RISER_BOARD_S), rises over a bar, and sinks over the
## bar after riser_down before it fades.
func riser_lift(t: float) -> float:
	var up := 0.0
	if _act.has("riser_up") and t >= float(_act["riser_up"]["t0"]) + RISER_BOARD_S:
		var u := clampf((t - float(_act["riser_up"]["t0"]) - RISER_BOARD_S) / bar_s(), 0.0, 1.0)
		up = u * u * (3.0 - 2.0 * u)
	if _act.has("riser_down") and t >= float(_act["riser_down"]["t0"]) and (not _act.has("riser_up") or float(_act["riser_down"]["t0"]) >= float(_act["riser_up"]["t0"])):
		var d := clampf((t - float(_act["riser_down"]["t0"])) / bar_s(), 0.0, 1.0)
		up = 1.0 - d * d * (3.0 - 2.0 * d)
	return up * RISER_LIFT


const RISER_BOARD_S := 2.2


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
			crowd.hero_to(crowd.actors[crowd.hero_id()]["home"] if crowd.hero_id() != "" else Vector2(640, 380), t0 + bar_s(), 2.0)
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
			crowd.hero_to(Vector2(crowd.circle_c.x, crowd.circle_c.y + 18.0), t0, 2.5,
				{"state": "solo" if energy >= 40.0 else "dance", "from": 0.0, "until": t0 + 6.0 * bar_s(), "sync": false})
			_act["spot_circle"] = {"t0": t0, "t1": t0 + 6.0 * bar_s()}
		"hero_solo":
			var h := crowd.hero_id()
			if h != "":
				var rl: Array = assets.anchor("riser", [crowd.circle_c.x, crowd.circle_c.y - 20.0, 260], current_view)
				crowd.walk_to(h, Vector2(float(rl[0]), float(rl[1]) - 6.0), t0, 2.0, {"state": "solo" if energy >= 40.0 else "dance", "from": 0.0, "until": t0 + dur, "sync": false})
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
			crowd.direct(crowd.ids_of("circle"), "cheer", t0 + 1.5, 4.0 * bar_s(), true)
			crowd.hero_to(Vector2(crowd.circle_c.x, crowd.circle_c.y + 18.0), t0, 1.5, {"state": "solo", "from": 0.0, "until": t0 + 6.0 * bar_s(), "sync": false})
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
				if current_view == "main":
					_main_palette = palette  # remembered for the way back
				current_view = to
				var hint := (views[to] as StoryView).palette_hint
				if to == "main" and _main_palette != "" and not args.has("keep_palette"):
					palette = _main_palette
				elif hint != "" and palettes.has(hint) and not args.has("keep_palette"):  # the room's own light, unless the script says otherwise
					palette = hint
		"player_move", "player_look", "player_role", "fx_queasy", "sick_beat":
			if player != null:  # the journey needs a map; a chapter without one keeps its 2D camera and ignores these
				player.apply_action(a)
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
			if not st3.has("on_t") and not _ambient.has(str(args["piece"])):  # a room's own pieces are already on: a pulse keeps them on
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
