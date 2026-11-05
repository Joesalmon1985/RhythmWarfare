class_name StoryStage
extends Control
## A chapter's stage in the 2.5D world (docs/STORY_25D_PLAN.md): the map, the player's rail camera, one crowd per room, the 3D world and its light show, and the authored actions
## the director sends. Every effect is a function of song time (the audio clock) and of action start times; nothing here advances on frame counts.

const NO_END := 1.0e9
const SWELL_BEATS := 2.0  # a new room's lamps rise over this many beats from its downbeat
const SWELL_FROM := 0.55  # ... from this share of their light
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
var motion := 0  # camera motion: 0 full, 1 reduced, 2 none (Session.effective_story_motion); reduced effects imply at least 1
var lines := 0  # internal resolution lines for the low-res world (0: the default, or RW_STORY_LINES)
var high_contrast := false
var palette := "low"
var palettes: Dictionary = {}  # name -> Array[Color] (the chapter's own, else PALETTES)
var _pieces: Dictionary = {}  # id -> {on_t, off_t, pulse_t, bars}
var _ambient: Dictionary = {}  # ids of the extra rooms' own pieces
var energy := 45.0
var t_now := 0.0

var crowds: Dictionary = {}  # room id -> StoryCrowd: one per room that holds actors (the actors' `view`)
var current_view := "main"  # the room whose crowd the authored crowd actions direct: the room the player last walked into
var _main_palette := ""  # the main room's light when the camera last left it
var _act := {}  # active timed effects: name -> {t0, t1, args}
var _beam_mode := "sweep"
var _beam_since := 0.0
var _led_mode := "eq"
var _woofer_pump := false
var _ball_on := false
var _ending := ""
var _lean := ""
var _flicker_until := -1.0
var action_log: Array = []

## The world: the map, the rail camera, and (with nodes) the 3D scene seen through a low-res viewport.
var map: StoryMap
var player: StoryPlayer  # the rail camera and the journey (roles, queasy, sick); also exists without nodes (tests)
var lowres: StoryLowRes
var world: StoryWorld
var free_look := StoryFreeLook.new()
var world_active := false
var fx3d: StoryWorldFx  # the light show in the 3D world (beams, pools, haze, LED, tiles, ...)
var _overlay: CanvasLayer
var _vis: Dictionary = {}
var _vis_geo: Dictionary = {}
var _vis_sec := ""
var _vis_pos := Vector2(1e9, 1e9)
var _vis_yaw := 1e9
var _vis_size := Vector2.ZERO
var _world_ctx: Dictionary = {}
var _piece_ids: Array = []  # the set pieces the map shows as things


func setup(p_assets: StoryAssets, p_data: StoryData, p_run: StoryRun) -> void:
	assets = p_assets
	data = p_data
	run = p_run
	bpm = run.level.bpm
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	clip_contents = true
	palettes = PALETTES.duplicate()
	for k in data.palettes:
		var cols: Array = []
		for hex in data.palettes[k]:
			cols.append(Color.html(str(hex)))
		if not cols.is_empty():
			palettes[k] = cols
	for vid in assets.view_ids():  # a room's own pieces are on whenever the show is in that room, unless the script says otherwise
		if vid != "main":
			for pc in assets.pieces(str(vid)):
				_ambient[str(pc["id"])] = true
	for vid in StoryMap.crowd_rooms(data.raw):
		var c := StoryCrowd.new()
		c.name = "Crowd_" + str(vid)
		c.view = str(vid)
		c.bpm = bpm
		c.glow_colors = glow_colors()
		c.setup(assets, data)
		crowds[str(vid)] = c
		add_child(c)
	current_view = "main"
	if not FileAccess.file_exists(StoryMap.PATH % data.id):
		push_error("story map missing for chapter " + data.id)
	else:  # the crowd and the rail camera exist even without a renderer
		var m := StoryMap.load_chapter(data.id)
		m.validate_chapter(data.raw)
		if m.errors.is_empty():
			attach_world(m, false)
		else:
			push_error("story map rejected: " + "; ".join(PackedStringArray(m.errors)))
	reset()


## The tempo changed (a path at its own tempo took the clock, RunPlay): every beat-timed thing of the stage follows. Animations are functions of song time, so they jump to the new beat on the swap, behind the
## closed passage frame.
func set_tempo(p_bpm: float) -> void:
	bpm = p_bpm
	for id in crowds:
		(crowds[id] as StoryCrowd).bpm = p_bpm
	if player != null:
		player.bpm = p_bpm


## The crowd of the room the camera is in (the one the authored actions direct).
var crowd: StoryCrowd:
	get:
		return crowds[current_view]


## Give the stage a map: the player's rail always; with `with_nodes` also the 3D world behind the crowd (needs no renderer to build).
func attach_world(p_map: StoryMap, with_nodes := true) -> void:
	if map != p_map:
		map = p_map
		player = StoryPlayer.new()
		player.setup(map, bpm)
		player.reduced = reduced
		for id in crowds:  # every room of the chapter has its own crowd in the same world (a room holds the actors whose `view` it is)
			(crowds[id] as StoryCrowd).attach_map(map)
	if not with_nodes or world_active:
		return
	lowres = StoryLowRes.new()
	if lines > 0 and not OS.has_environment("RW_STORY_LINES"):
		lowres.lines = lines
	lowres.name = "World3D"
	lowres.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(lowres)
	move_child(lowres, 0)  # behind the 2D crowd
	for t in map.things:
		if t.has("piece") and str(t["piece"]) not in _piece_ids:
			_piece_ids.append(str(t["piece"]))
	world = StoryWorld.new()
	world.name = "World"
	world.build(map, assets)
	lowres.attach(world)
	lowres.set_vignette(assets.sprite("vignette").get("tex", null))
	lowres.dither = Session.story_dither and not reduced
	if OS.has_environment("RW_STORY_DITHER"):
		lowres.dither = OS.get_environment("RW_STORY_DITHER") == "1"
	var fogc := Color.html(str(map.fog.get("color", "#08051a")))
	lowres.clamp_lo = fogc.darkened(0.55)  # the chapter's shadow: nothing in the picture is darker than its fog in deep shadow
	lowres.clamp_hi = Color(1, 1, 1).lerp(fogc.lightened(0.6), 0.12)
	_overlay = lowres.add_overlay(crowds["main"], "Crowd")  # the 2D crowds are drawn inside the low-res viewport, so dancers pixelate like the world
	for id in crowds:
		var c: StoryCrowd = crowds[id]
		if c.get_parent() != _overlay:
			c.get_parent().remove_child(c)
			_overlay.add_child(c)
	fx3d = StoryWorldFx.new()
	world.add_child(fx3d)
	fx3d.build(self, map, assets, world)
	for id in crowds:
		(crowds[id] as StoryCrowd).tint_fn = func(sec: String) -> Color: return world.light_of(map.sector(sec), t_now, _world_ctx)
		(crowds[id] as StoryCrowd).light_fn = _figure_light
	var ppl: StoryPeople = (crowds["main"] as StoryCrowd).people
	if ppl != null:
		ppl.set_fog(Color.html(str(map.fog.get("color", "#08051a"))).darkened(0.35))
	world_active = true
	var hide := OS.get_environment("RW_STORY_HIDE").split(",")  # profiling aid: RW_STORY_HIDE=crowd,world,fx hides those parts to measure what each costs
	if "crowd" in hide:
		_overlay.visible = false
	if "world" in hide:
		world.visible = false
	if "fx" in hide:
		fx3d.visible = false
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


## The drop's haze burst start times and the two-bar results (passed or not), kept here so the 3D light (StoryLight) reads them too.
var _bursts: Array = []
var _pulses: Array = []


func fx_bursts() -> Array:
	return _bursts


func fx_pulses() -> Array:
	return _pulses


func _haze_burst(t0: float) -> void:
	_bursts.append(t0)


func _set_glow(on: bool) -> void:
	for id in crowds:
		(crowds[id] as StoryCrowd).glow_on = on


func glow_colors() -> Array:
	var rv: Array = palettes.get("rave", PALETTES["rave"])
	return [rv[0], rv[mini(1, rv.size() - 1)], rv[mini(3, rv.size() - 1)]]


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
	_bursts = []
	_pulses = []
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
	_main_palette = ""
	current_view = "main"
	for id in crowds:
		(crowds[id] as StoryCrowd).reset()


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


## The room's light gain at song time `t`: the swell of a new room (SWELL_FROM of the light on its downbeat, easing up to all of it over SWELL_BEATS beats), 1 when no swell is under way.
func swell_gain(t: float) -> float:
	var u := progress("room_swell", t)
	if u < 0.0:
		return 1.0
	return lerpf(SWELL_FROM, 1.0, 1.0 - pow(1.0 - u, 2.0))


func update(t: float, p_energy: float) -> void:
	t_now = t
	energy = p_energy
	var pose: Dictionary = {}
	if player != null:
		player.reduced = reduced or motion >= 1
		player.cut = motion >= 2
		pose = player.pose_at(t)
		if _cam_override != "":
			pose = _override_pose(pose)
		var size := Vector2(lowres.sub.size) if lowres != null else Vector2(480, 170)
		var look_off := 0.0 if _cam_override.begins_with("actor:") else free_look.offset  # (a screenshot framed on a person is not turned away by the player's look at a touch)
		var ppose := {"cam": pose["cam"], "yaw": float(pose["yaw"]) + look_off, "pitch": float(pose.get("pitch", 0.0))}
		var cpos := Vector2(pose["pos"])
		if _vis_sec != str(pose["sector"]) or _vis_pos.distance_to(cpos) > 0.01 or absf(_vis_yaw - float(ppose["yaw"])) > 0.25 or not _vis_size.is_equal_approx(size):
			_vis_sec = str(pose["sector"])  # the portal walk only reruns when the camera has really moved or turned
			_vis_pos = cpos
			_vis_yaw = float(ppose["yaw"])
			_vis_size = size
			_vis = map.visible_sectors(cpos, _vis_yaw, _vis_sec, size.x / maxf(size.y, 1.0))
			_vis_geo = map.visible_sectors(cpos, _vis_yaw, _vis_sec, size.x / maxf(size.y, 1.0), 7)  # the geometry is drawn deeper than the crowd is (long sightlines)
			if world_active:
				world.set_visible_sectors(_vis_geo)
				world.set_atmosphere(map.sector(_vis_sec))
		for id in crowds:
			(crowds[id] as StoryCrowd).set_camera(ppose, size, _vis)
	_sec_light = {}
	if world_active:  # the world first: the figures are lit by this frame's light
		_update_world(t, p_energy, pose)
	for id in crowds:  # every room's crowd lives on; only the camera decides what is seen
		var c: StoryCrowd = crowds[id]
		c.reduced = reduced
		c.lit_id = c.hero_id() if is_active("spot_hero", t) or is_active("spot_circle", t) else ""
		c.set_time(t)
		c.update(t, p_energy)
	_order_crowds()
	var ppl: StoryPeople = (crowds["main"] as StoryCrowd).people if crowds.has("main") else null
	if ppl != null:
		ppl.flush_light()
	queue_redraw()


## Screenshot aid: RW_STORY_CAM=<waypoint>[,<extra yaw degrees>[,<pitch degrees>]] stands the camera at a waypoint whatever the journey says, or RW_STORY_CAM=actor:<id>[:<metres>[:<pitch>]] in front of a person (tools/run/capture.sh --acting), or RW_STORY_CAM=@<x>:<z>:<yaw>[:<pitch>]
## at an absolute ground point (any sector). The crowd of the camera's room is then the one the authored crowd actions direct, so the room is populated the way a visit would find it.
var _cam_override: String = OS.get_environment("RW_STORY_CAM")
var _cam_actor_at: Variant = null  # (the standpoint chosen for RW_STORY_CAM=actor:...)


func _override_pose(pose: Dictionary) -> Dictionary:
	var at := Vector2.ZERO
	var yaw := 0.0
	var pitch := 0.0
	var sec := ""
	if _cam_override.begins_with("actor:"):  # RW_STORY_CAM=actor:<id>[:<metres>[:<pitch>]]: the camera stands that far from the person (their current place), on the side the rail's camera stands, facing them
		var q := _cam_override.substr(6).split(":")
		var found: Variant = _person_pos(q[0])
		if found == null:
			return pose
		var ap: Vector2 = found
		var dist := float(q[1]) if q.size() > 1 else 2.4
		if _cam_actor_at != null and ((_cam_actor_at as Vector2).distance_to(ap) > dist * 1.7 or (_cam_actor_at as Vector2).distance_to(ap) < dist * 0.55):
			_cam_actor_at = null  # (a person who walks off, or into the camera: stand somewhere new)
		if _cam_actor_at == null:  # chosen once, so the picture holds still while the rail moves: the standpoint with the clearest line to the person (nobody between), nearest to the side the rail's camera stood on
			var base := ((pose["pos"] as Vector2) - ap).angle() if pose.has("pos") else 0.0
			var room := map.room_of(map.sector_at(ap))
			var others: Array = []
			for rid in crowds:
				for oid in (crowds[rid] as StoryCrowd).actors:
					if str(oid) != q[0]:
						others.append(((crowds[rid] as StoryCrowd).actors[oid] as Dictionary)["pos"])
			var first: Variant = null  # (the clearest standpoint seen, when none is clear enough)
			var first_clear := -1.0
			for same_only in [true, false]:  # the person's own sector first (a balcony's edge, a booth), then any sector of the room
				for k in [1.0, 0.8, 0.65, 0.5]:
					for da in [0.0, 0.4, -0.4, 0.8, -0.8, 1.2, -1.2, 1.6, -1.6, 2.2, -2.2, PI]:  # nearest the rail's side first
						var p: Vector2 = ap + Vector2.from_angle(base + da) * dist * k
						var psec := map.sector_at(p)
						if psec == "" or map.room_of(psec) != room or (same_only and psec != map.sector_at(ap)):
							continue
						var clear := 9.0
						for o in others:
							clear = minf(clear, Geometry2D.get_closest_point_to_segment(o, p, ap).distance_to(o))
						if clear > first_clear:
							first_clear = clear
							first = p
						if clear >= 0.6:  # nobody stands between the camera and the person
							_cam_actor_at = p
							break
					if _cam_actor_at != null:
						break
				if _cam_actor_at != null:
					break
			if _cam_actor_at == null:
				_cam_actor_at = first
		if _cam_actor_at == null:
			return pose
		at = _cam_actor_at
		yaw = rad_to_deg(atan2(-(ap.x - at.x), -(ap.y - at.y)))
		pitch = float(q[2]) if q.size() > 2 else -3.0
		sec = map.sector_at(at)
	elif _cam_override.begins_with("@"):
		var q := _cam_override.substr(1).split(":")
		if q.size() < 3:
			return pose
		at = Vector2(float(q[0]), float(q[1]))
		yaw = float(q[2])
		pitch = float(q[3]) if q.size() > 3 else 0.0
		sec = map.sector_at(at)
	else:
		var parts := _cam_override.split(",")
		var w := map.waypoint(parts[0])
		if w.is_empty():
			return pose
		sec = str(w["sector"])
		at = w["at"]
		yaw = float(w["yaw"]) + (float(parts[1]) if parts.size() > 1 else 0.0)
		pitch = float(parts[2]) if parts.size() > 2 else 0.0
	if sec == "":
		return pose
	var out := pose.duplicate()
	var ground := float(map.sector(sec).get("floor", 0.0))
	out["pos"] = at
	out["sector"] = sec
	out["ground"] = ground
	out["yaw"] = yaw
	out["pitch"] = pitch
	out["cam"] = Vector3(at.x, ground + map.eye_height, at.y)
	out["roll"] = 0.0
	out["moving"] = false
	var room := map.room_of(sec)
	if crowds.has(room):
		current_view = room
	return out


## Where a person is now on the ground (a person of any room's crowd), or null.
func _person_pos(id: String) -> Variant:
	for rid in crowds:
		var c := crowds[rid] as StoryCrowd
		if c.actors.has(id):
			return c.actors[id]["pos"]
	return null


## One draw order for every visible figure of every room, far to near by distance from the eye (z_index of the 2D nodes in the shared overlay): a dancer seen through a doorway
## is behind or in front of this room's dancers by true distance. The crowds' own shadow blobs (z 0) stay under everyone.
func _order_crowds() -> void:
	var keys: Array = []
	var nodes: Array = []
	for id in crowds:
		for it in (crowds[id] as StoryCrowd).sort_items:
			nodes.append(it[1])
			keys.append((int(it[0]) << 12) | (nodes.size() - 1))
	keys.sort()
	for i in keys.size():
		(nodes[int(keys[i]) & 4095] as CanvasItem).z_index = 1 + i


var _sec_light: Dictionary = {}


## The light a figure stands in: `song` the sector's song-time light (cached per frame), else the static light of the lamps around the ground point.
func _figure_light(sec: String, pos: Vector2, song: bool) -> Color:
	if not world_active:
		return Color.WHITE
	if not song:
		return world.figure_light(pos, sec)
	if not _sec_light.has(sec):
		_sec_light[sec] = world.light_of(map.sector(sec), t_now, _world_ctx) if not _world_ctx.is_empty() else Color.WHITE
	return _sec_light[sec]


func _update_world(t: float, p_energy: float, pose: Dictionary) -> void:
	lowres.apply_pose(pose, 0.0 if _cam_override.begins_with("actor:") else free_look.offset)
	var pcs := {}
	for pid in _piece_ids:
		pcs[pid] = piece_state(str(pid), t)
	_world_ctx = {"bpm": bpm, "palette": palette_colors(), "energy": p_energy, "flicker": flickering(t), "strobe": StoryLight.strobe_at(self, t), "woofer_pump": _woofer_pump, "pieces": pcs, "palette_weight": map.palette_weight, "swell_gain": swell_gain(t)}
	world.update(t, _world_ctx)
	fx3d.update(t)
	lowres.apply_post(StoryLight.post_state(self, t), StoryLight.pal(self, 0).lightened(0.3))


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
		"room_swell":
			_act["room_swell"] = {"t0": t0, "t1": t0 + SWELL_BEATS * bar_s() / 4.0}
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
			_haze_burst(t0)
			crowd.direct(crowd.present_ids(), "dance", t0, 3.0 * bar_s())
		"haze_burst":
			_haze_burst(t0)
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
			if crowd.hero_id() != "":
				crowd.hero_to(crowd.actors[crowd.hero_id()]["home"], t0 + bar_s(), 2.0)
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
			crowd.hero_to(crowd.centre_spot(), t0, 2.5,
				{"state": "solo" if energy >= 40.0 else "dance", "from": 0.0, "until": t0 + 6.0 * bar_s(), "sync": false})
			_act["spot_circle"] = {"t0": t0, "t1": t0 + 6.0 * bar_s()}
		"hero_solo":
			var h := crowd.hero_id()
			if h != "":
				crowd.walk_to(h, crowd.solo_spot(), t0, 2.0, {"state": "solo" if energy >= 40.0 else "dance", "from": 0.0, "until": t0 + dur, "sync": false})
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
			crowd.hero_to(crowd.centre_spot(), t0, 1.5, {"state": "solo", "from": 0.0, "until": t0 + 6.0 * bar_s(), "sync": false})
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
			_haze_burst(t0)
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
		"player_move", "player_walk", "player_look", "player_role", "fx_queasy", "sick_beat":
			if player != null:  # the journey needs a map; a chapter without one keeps its 2D camera and ignores these
				player.apply_action(a)
				if act == "player_move":
					_enter_room(str(args.get("to", "")), args)
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
			for ja in data.ending_journey(_ending, t0, bar_s()):  # where the player ends up in this ending's tableau
				apply(ja)
			for vid in crowds:
				(crowds[vid] as StoryCrowd).set_ending(_ending)
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


## The authored crowd actions (bring_in, circle_form, hero_center ...) direct the crowd of the room the player is heading for; a room without a crowd
## of its own (the medical bay) leaves them with the last room that has one. The room's own light comes with the player, unless the move says keep_palette.
func _enter_room(waypoint: String, args: Dictionary) -> void:
	var w := map.waypoint(waypoint)
	if w.is_empty():
		return
	var room := map.room_of(str(w["sector"]))
	if room == current_view or not crowds.has(room):
		return
	if current_view == "main":
		_main_palette = palette
	current_view = room
	var hint := str(map.rooms.get(room, {}).get("palette", ""))
	if room == "main" and _main_palette != "" and not args.has("keep_palette"):
		palette = _main_palette
	elif hint != "" and palettes.has(hint) and not args.has("keep_palette"):
		palette = hint


func _front_ids() -> Array:
	var out: Array = []
	for id in crowd.present_ids():
		if str(crowd.actors[id]["data"].get("role", "")) in ["front", "hero"]:
			out.append(id)
	return out


## The two-bar result: a local reaction now; the persistent mood is the energy.
func on_sequence(result: Dictionary, t0: float) -> void:
	crowd.react(bool(result["passed"]), str(result["grade"]), t0)
	if _pulses.size() > 6:
		_pulses.pop_front()
	_pulses.append({"t0": t0, "passed": bool(result["passed"])})
