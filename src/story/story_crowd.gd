class_name StoryCrowd
extends Node2D
## The crowd on the fixed dance floor: rigged dancers (StoryCharacter) and cheap rear silhouettes, placed on the art's floor rows
## by depth, y-sorted, and driven by the crowd energy plus authored directives. Everything is a pure function of song time and
## the (deterministic) actions the director emits, so it pauses, restarts and fast-forwards exactly.
##
## Per dancer the state is: walking (arrival/exit), else an active directive (clap, cheer, look, ...), else the mood from the
## crowd energy plus the dancer's own threshold (so they react at different levels): sad < idle < dance < cheer.

const SIL_UP_E := 66.0
const NO_END := 1.0e9
const CHAR_SCALE := 0.8  # the art's front row is a 260 to 300 px dancer: 0.8 keeps the room visible behind a crowd of 30

var assets: StoryAssets
var view := "main"  # the room this crowd lives in (actors and silhouettes with that `view`)
var data: StoryData
var bpm := 174.0
var reduced := false
var energy := 45.0
var glow_on := false
var lit_id := ""  # the dancer a followspot is on (drawn a touch brighter)
var riser_pos := Vector2(-9999, -9999)  # where a performer stands on the riser, and how high it has lifted them
var riser_lift := 0.0
var actors: Dictionary = {}  # id -> {node, data, home: Vector2, pos: Vector2, present, depth, move: {}, dir: {}, thresh, scale}
var _order: Array = []
var _sils: Array = []
var _rng := RandomNumberGenerator.new()
var _floor_scale := 1.0
var door_pos := Vector2(160, 330)
var circle_c := Vector2(640, 380)
var circle_r := Vector2(200, 60)
var _ending := ""
var _flinch_until := -1.0
var glow_colors: Array = [Color(0.4, 1.0, 0.95), Color(1.0, 0.4, 0.85), Color(1.0, 0.8, 0.3)]

## The 2.5D world (StoryMap, docs/STORY_25D_PLAN.md): with a map attached positions are ground coordinates [x, z] in metres instead of design pixels, every
## actor's feet are projected through StoryProjector from the camera pose the stage hands over, dancers are sorted by distance and culled by sector visibility.
const HERO_M := 1.7  # a dancer is this tall in the world
const NEAR_FADE := Vector2(0.7, 1.3)  # dancers closer than this (m) to the eye fade out so a passer-by never fills the screen
const OPEN_GAP := 0.42
const POSE_RATE := 45.0
var map: StoryMap
var world_mode := false
var cam_pose: Dictionary = {}  # {cam: Vector3, yaw}
var view_size := Vector2(480, 170)
var vis_sectors: Dictionary = {}  # sector id -> portal depth, from StoryMap.visible_sectors; empty = everything visible
var tint_fn := Callable()  # sector id -> Color, the light a prop is seen in
var circle_open := Vector2(0, -1)
var riser_spot := Vector2.ZERO
var floor_x := Vector2(-6.5, 6.5)  # the dance floor's x range, for waves
var door_slots: Array = []
var props: Array = []  # StoryCrowdProp nodes (silhouettes and occluders)
var drawn := 0  # actors drawn last frame (a probe for the tests and the profiler)
var _pose_key := ""
var _order_key := ""


func setup(p_assets: StoryAssets, p_data: StoryData) -> void:
	assets = p_assets
	data = p_data
	_rng.seed = 4242
	var dw: Array = assets.anchor("doorway", [], view)
	if dw.size() < 4:  # a room without a doorway: arrivals walk in from the left edge
		dw = [-40, 280, 40, 0]
	door_pos = Vector2(float(dw[0]) + float(dw[2]) * 0.5, float(dw[1]) + float(dw[3]))
	var cc: Array = assets.anchor("circle_centre", [640, 380], view)
	circle_c = Vector2(float(cc[0]), float(cc[1]))
	var cr: Array = assets.anchor("circle_radii", [200, 60], view)
	circle_r = Vector2(float(cr[0]), float(cr[1]))
	var n := 0
	for a in data.actors:
		if str(a.get("view", "main")) != view:
			continue
		var rig := assets.rig(str(a["archetype"]), str(a["variant"]), str(a.get("art", "")))
		if rig.is_empty():
			continue
		var c := StoryCharacter.new()
		c.name = str(a["id"])
		c.setup(assets, rig, str(a["id"]), 1000 + n)
		c.glow = bool(a.get("glow", false)) or (n % 4 == 0)
		c.glow_color = glow_colors[n % glow_colors.size()]
		add_child(c)
		var present := str(a["group"]) == "core"
		actors[str(a["id"])] = {"node": c, "data": a, "home": _home_of(a), "pos": _home_of(a), "present": present, "move": {}, "dir": {},
			"thresh": float(a.get("thresh", 0.0)), "alpha": 1.0 if present else 0.0, "stay": false, "vanish": {}}
		n += 1
	_order = actors.keys()
	for s in data.silhouettes:
		if str(s.get("view", "main")) != view:
			continue
		var shape: Dictionary = assets.manifest.get("silhouettes", {}).get(str(s["shape"]), {})
		if shape.is_empty():
			continue
		if not s.has("x"):  # a world-only chapter: the map places its silhouettes (attach_map)
			continue
		var f := assets.floor_at(float(s["depth"]), view)
		_sils.append({"idle": assets._entry(shape.get("idle", {})), "up": assets._entry(shape.get("up", {})), "x": float(s["x"]),
			"y": float(f["y"]), "scale": float(f["scale"]) * 0.95, "group": str(s["group"]), "thresh": float(s["thresh"]),
			"present": str(s["group"]) == "core", "alpha": 1.0 if str(s["group"]) == "core" else 0.0, "ph": _rng.randf()})
	_resort()


func _home_of(a: Dictionary) -> Vector2:
	if not a.has("x"):  # placed by the map (attach_map)
		return Vector2.ZERO
	var f := assets.floor_at(float(a["depth"]), view)
	return Vector2(float(a["x"]), float(f["y"]))


## Put the crowd in the 3D world: homes, the door, the circle and the riser come from the map (metres), the rear silhouettes and occluders become props.
func attach_map(p_map: StoryMap) -> void:
	map = p_map
	world_mode = true
	var door := map.spot("door")
	door_pos = door.get("at", Vector2.ZERO)
	door_slots = door.get("slots", [])
	var circ := map.spot("circle")
	circle_c = circ.get("at", Vector2.ZERO)
	circle_r = circ.get("radii", Vector2(3.0, 1.8))
	circle_open = circ.get("open", Vector2(0, -1))
	riser_spot = map.spot("riser").get("at", Vector2.ZERO)
	var lo := INF
	var hi := -INF
	for sec in map.sectors:
		if "dance_floor" in (sec["flags"] as Array):
			for q in (sec["poly"] as PackedVector2Array):
				lo = minf(lo, q.x)
				hi = maxf(hi, q.x)
	if lo < hi:
		floor_x = Vector2(lo, hi)
	for id in actors:
		var a: Dictionary = actors[id]
		var h: Dictionary = map.home(str(id))
		if h.is_empty():
			continue
		a["home"] = h["at"]
		a["pos"] = h["at"]
		a["sec"] = str(h["sector"])
		a["k"] = HERO_M / maxf(float((a["node"] as StoryCharacter).rig.get("height", 260.0)), 1.0)
	for pr in props:
		remove_child(pr)
		pr.queue_free()
	props = []
	_sils = _sils.filter(func(x: Dictionary) -> bool: return not x.has("node"))
	for s in data.silhouettes:
		var sp: Dictionary = map.silhouettes.get(str(s["id"]), {})
		var shape: Dictionary = assets.manifest.get("silhouettes", {}).get(str(s["shape"]), {})
		if sp.is_empty() or shape.is_empty():
			continue
		var pn := StoryCrowdProp.new()
		pn.kind = "silhouette"
		pn.name = "Sil_" + str(s["id"])
		add_child(pn)
		props.append(pn)
		_sils.append({"idle": assets._entry(shape.get("idle", {})), "up": assets._entry(shape.get("up", {})), "at": sp["at"], "sector": str(sp["sector"]), "group": str(s["group"]),
			"thresh": float(s["thresh"]), "present": str(s["group"]) == "core", "alpha": 1.0 if str(s["group"]) == "core" else 0.0, "ph": _rng.randf(), "node": pn})
	for o in map.occluders:
		var tex: Texture2D = assets.texture("textures/%s.png" % str(o["sprite"])) if assets != null else null
		if tex == null and assets != null:
			var file := str(map.textures.get(str(o["sprite"]), ""))
			tex = assets.texture(file)
		var pn2 := StoryCrowdProp.new()
		pn2.kind = "occluder"
		pn2.name = "Occ_" + str(o["id"])
		pn2.set_meta("def", o)
		pn2.set_meta("tex", tex)
		add_child(pn2)
		props.append(pn2)
	reset()


func _xv(a: Dictionary) -> int:  # a stable per-dancer number for the little variations in the mood (design x in the 2D rooms)
	return int(a["data"]["x"]) if a["data"].has("x") else int(640.0 + (a["home"] as Vector2).x * 65.0)


func reset() -> void:
	for id in actors:
		var a: Dictionary = actors[id]
		a["present"] = str(a["data"]["group"]) == "core"
		a["alpha"] = 1.0 if a["present"] else 0.0
		a["pos"] = a["home"]
		a["move"] = {}
		a["dir"] = {}
		a["stay"] = false
		a["vanish"] = {}
		(a["node"] as StoryCharacter).sync = false
	for s in _sils:
		s["present"] = s["group"] == "core"
		s["alpha"] = 1.0 if s["present"] else 0.0
	glow_on = false
	_last_t = -INF
	_ending = ""
	_flinch_until = -1.0
	_order_key = ""
	_resort()


func present_count() -> int:
	var n := 0
	for id in actors:
		if actors[id]["present"] and float(actors[id]["alpha"]) > 0.05:
			n += 1
	for s in _sils:
		if s["present"] and float(s["alpha"]) > 0.05:
			n += 1
	return n


func state_counts() -> Dictionary:
	var out := {}
	for id in actors:
		var a: Dictionary = actors[id]
		if a["present"]:
			var st: String = (a["node"] as StoryCharacter).state
			out[st] = int(out.get(st, 0)) + 1
	return out


func _resort() -> void:
	if world_mode:
		return  # the world sorts by distance every frame (_sort_world)
	_order.sort_custom(_nearer)
	for i in _order.size():
		move_child(actors[_order[i]]["node"], i)


## Depth order: further back (smaller feet y) first; ties broken by x then id, so equal rows never swap places between frames.
func _nearer(x: String, y: String) -> bool:
	var px: Vector2 = actors[x]["pos"]
	var py: Vector2 = actors[y]["pos"]
	if not is_equal_approx(px.y, py.y):
		return px.y < py.y
	if not is_equal_approx(px.x, py.x):
		return px.x < py.x
	return x < y


# --- per frame -------------------------------------------------------------------------------------------------------

func update(t: float, p_energy: float) -> void:
	energy = p_energy
	var e01 := clampf(energy / 100.0, 0.0, 1.0)
	var need_sort := false
	drawn = 0
	if t < _last_t:  # a restart: fades start over
		_last_t = t
	var dt := clampf(t - _last_t, 0.0, 0.25) if _last_t > -INF else 0.0
	_last_t = t
	var fade := dt * (FADE_PER_S * (0.8 if reduced else 1.0))
	for id in _order:
		var a: Dictionary = actors[id]
		var c: StoryCharacter = a["node"]
		var mv: Dictionary = a["move"]
		var walking := false
		c.walk_dir = 0.0
		if not mv.is_empty():
			var u := clampf((t - float(mv["t0"])) / maxf(float(mv["t1"]) - float(mv["t0"]), 0.001), 0.0, 1.0)
			if t >= float(mv["t0"]):
				var ue := u * u * (3.0 - 2.0 * u)
				var dx: float
				if mv.has("path"):
					var along := _along(mv, ue)
					a["pos"] = along[0]
					dx = _screen_dx(along[1])
				else:
					a["pos"] = (mv["from"] as Vector2).lerp(mv["to"], ue)
					dx = ((mv["to"] as Vector2).x - (mv["from"] as Vector2).x) / 60.0
				walking = u < 1.0
				need_sort = true
				c.walk_dir = clampf(dx, -1.0, 1.0) * sin(PI * clampf(u * 1.4, 0.0, 1.0)) if walking else 0.0
				if u >= 1.0:
					a["move"] = {}
					if mv.get("hide_after", false):
						a["present"] = false
					if mv.has("then"):
						a["dir"] = mv["then"]
		var vis_target := 1.0 if a["present"] else 0.0
		a["alpha"] = move_toward(float(a["alpha"]), vis_target, fade)  # song-time fade: the same at any frame rate
		c.visible = float(a["alpha"]) > 0.01
		if not c.visible:
			continue
		var vn: Dictionary = a["vanish"]
		var vu := 0.0
		if not vn.is_empty() and t >= float(vn["t0"]):
			vu = clampf((t - float(vn["t0"])) / maxf(float(vn["t1"]) - float(vn["t0"]), 0.001), 0.0, 1.0)
		var lit := 1.13 if id == lit_id else 1.0  # the followspot's dancer stands out from the crowd
		var alpha := float(a["alpha"]) * (1.0 - clampf((vu - 0.55) / 0.45, 0.0, 1.0))
		if world_mode:
			if not _place_world(a, c, vu):
				c.visible = false  # behind a wall, out of view or too close: not drawn, not posed
				continue
			alpha *= float(a["near"])
			drawn += 1
		else:
			var depth_scale := _scale_at((a["pos"] as Vector2).y) * CHAR_SCALE
			var lift := 0.0
			if riser_lift > 0.0 and (a["pos"] as Vector2).distance_to(riser_pos) < 30.0:
				lift = riser_lift
			c.position = (a["pos"] as Vector2) + Vector2(sin(vu * 9.0 + float(a["thresh"])) * 6.0 * vu, float(vn.get("dy", 0.0)) * vu * vu - lift)
			c.scale = Vector2(depth_scale, depth_scale) * (1.0 - 0.5 * vu) * (1.0 + 0.35 * lift / 72.0)  # a raised performer reads bigger
		c.modulate = Color(lit, lit, lit * 0.97, alpha)
		c.reduced = reduced
		c.glow_on = glow_on and c.glow
		var dir: Dictionary = a["dir"]
		var st := _mood_state(a, e01)
		c.sync = false
		if walking:
			st = "walk"
		elif not dir.is_empty() and t < float(dir["until"]) and t >= float(dir.get("from", -1.0)):
			st = str(dir["state"])
			c.sync = bool(dir.get("sync", false))
		elif not dir.is_empty() and t >= float(dir["until"]):
			a["dir"] = {}
		if st != c.state:
			c.state = st
		if world_mode:  # the dancers animate at up to POSE_RATE a second of song time (the redraw is the cost); position and scale still follow the camera every frame
			var pt := float(a.get("pose_t", -1.0e9))
			if t >= pt and t - pt < 1.0 / POSE_RATE:
				continue
			a["pose_t"] = t
		c.update_pose(t, bpm, e01)
	for s in _sils:
		s["alpha"] = move_toward(float(s["alpha"]), 1.0 if s["present"] else 0.0, fade)
		var up_target := 1.0 if energy + float(s["thresh"]) > SIL_UP_E or _ending == "legendary" else 0.0
		s["upw"] = move_toward(float(s.get("upw", up_target)), up_target, dt * 3.0)
	if world_mode:
		_update_props()
		_sort_world()

	elif need_sort:
		_resort()
	queue_redraw()


# --- the 2.5D world: walking routes, projection, props, sorting --------------------------------------------------------------------------

## Where a walker is along its route (eased fraction u of the route length) and the direction it is heading.
func _along(mv: Dictionary, u: float) -> Array:
	var pts: PackedVector2Array = mv["path"]
	var cum: PackedFloat32Array = mv["cum"]
	var total := float(cum[cum.size() - 1])
	if total < 1.0e-6 or pts.size() < 2:
		return [pts[pts.size() - 1], Vector2.ZERO]
	var d := u * total
	var i := 1
	while i < pts.size() - 1 and d > float(cum[i]):
		i += 1
	var seg := float(cum[i]) - float(cum[i - 1])
	var k := clampf((d - float(cum[i - 1])) / maxf(seg, 1.0e-6), 0.0, 1.0)
	return [pts[i - 1].lerp(pts[i], k), (pts[i] - pts[i - 1]).normalized()]


## A ground heading as a sideways screen speed (-1 left .. 1 right) from the current camera, for the walk cycle's lean.
func _screen_dx(heading: Vector2) -> float:
	if cam_pose.is_empty():
		return heading.x
	return heading.dot(StoryProjector.right(float(cam_pose["yaw"])))


func set_camera(pose: Dictionary, size: Vector2, visible_secs: Dictionary) -> void:
	cam_pose = pose
	view_size = size
	vis_sectors = visible_secs
	var cam: Vector3 = pose["cam"]
	_eye = cam
	_fwd = StoryProjector.forward(float(pose["yaw"]))
	_rgt = StoryProjector.right(float(pose["yaw"]))
	_focal = StoryProjector.focal_px(size.y)


var _eye := Vector3.ZERO  # the camera, unpacked once a frame for the per-dancer projection
var _fwd := Vector2.ZERO
var _rgt := Vector2.ZERO
var _focal := 1.0


func _ground_of(sec: String) -> float:
	return float(map.sector(sec).get("floor", 0.0)) if sec != "" else 0.0


## Project one dancer: set its node's position and scale, `near` (a fade for a passer-by at the eye) and `depth`. False when it should not be drawn.
func _place_world(a: Dictionary, c: StoryCharacter, vu: float) -> bool:
	if cam_pose.is_empty():
		return false
	var pos: Vector2 = a["pos"]
	var sec: String = str(a.get("sec", ""))
	if not a["move"].is_empty():  # a walker may have crossed into another sector
		var now := map.sector_at(pos)
		if now != "":
			sec = now
			a["sec"] = now
	if not vis_sectors.is_empty() and not vis_sectors.has(sec):
		return false
	var rel := pos - Vector2(_eye.x, _eye.z)  # the pinhole projection of StoryProjector.project_ground, inlined: it runs for every dancer every frame
	var depth := rel.dot(_fwd)
	a["depth"] = depth
	if depth < StoryProjector.NEAR:
		return false
	var ppm := _focal / depth  # pixels per metre at this distance
	var feet := Vector2(view_size.x * 0.5 + ppm * rel.dot(_rgt), view_size.y * 0.5 + ppm * (_eye.y - _ground_of(sec)))
	var tall := HERO_M * ppm  # the dancer's height on screen: close ones have their feet below the edge but their body in view
	if feet.x < -view_size.x * 0.25 or feet.x > view_size.x * 1.25 or feet.y - tall > view_size.y or feet.y < -view_size.y * 0.25:
		return false
	a["near"] = clampf((depth - NEAR_FADE.x) / (NEAR_FADE.y - NEAR_FADE.x), 0.0, 1.0)
	if float(a["near"]) <= 0.0:
		return false
	var pr := {"scale": ppm, "screen": feet}
	var sc: float = ppm * float(a["k"]) * (1.0 - 0.5 * vu)
	var vn: Dictionary = a["vanish"]
	var dy := float(vn.get("dy", 0.0)) * vu * vu * float(a["k"]) * float(pr["scale"])
	c.position = (pr["screen"] as Vector2) + Vector2(sin(vu * 9.0 + float(a["thresh"])) * 6.0 * vu * sc, dy)
	c.scale = Vector2(sc, sc)
	return true


func _update_props() -> void:
	if cam_pose.is_empty():
		return
	var beats := _t_now * bpm / 60.0
	var rise := sin(PI * fposmod(beats, 1.0))
	var tint := Color(0.55, 0.6, 0.85).lerp(Color(0.78, 0.76, 1.0), clampf((energy - 20.0) / 30.0, 0.0, 1.0))
	for pn in props:
		var p: StoryCrowdProp = pn
		p.items = []
		p.depth = 1.0e9
		if p.kind == "occluder":
			var o: Dictionary = p.get_meta("def")
			var tex: Texture2D = p.get_meta("tex")
			var sec := str(o["sector"])
			var at: Vector2 = o["at"]
			if tex == null or (not vis_sectors.is_empty() and not vis_sectors.has(sec)):
				p.visible = false
				continue
			var pr := StoryProjector.project_ground(at.x, at.y, _ground_of(sec), cam_pose, view_size)
			p.visible = bool(pr["visible"])
			if not p.visible:
				continue
			var w := float(o["width"]) * float(pr["scale"])
			var h := float(o["height"]) * float(pr["scale"])
			var col: Color = tint_fn.call(sec) if tint_fn.is_valid() else Color.WHITE
			p.position = pr["screen"]
			p.depth = float(pr["depth"])
			p.items = [[tex, Rect2(-w * 0.5, -h, w, h), col]]
			p.queue_redraw()
		else:
			pass
	for s in _sils:
		if not s.has("node"):
			continue
		var p2: StoryCrowdProp = s["node"]
		var al := float(s["alpha"])
		p2.items = []
		p2.depth = 1.0e9
		var sec2 := str(s["sector"])
		if al < 0.02 or (not vis_sectors.is_empty() and not vis_sectors.has(sec2)):
			p2.visible = false
			continue
		var at2: Vector2 = s["at"]
		var pr2 := StoryProjector.project_ground(at2.x, at2.y, _ground_of(sec2), cam_pose, view_size)
		p2.visible = bool(pr2["visible"])
		if not p2.visible:
			continue
		var sway := sin((beats * 0.25 + float(s["ph"])) * TAU) * (2.0 + energy * 0.05)
		var bob := rise * (1.0 + energy * 0.07) * clampf((energy - 25.0) / 15.0, 0.0, 1.0)
		var upw := float(s.get("upw", 0.0))
		var k := float(pr2["scale"]) * HERO_M / 260.0
		p2.position = (pr2["screen"] as Vector2) + Vector2(sway * k, -bob * k)
		p2.depth = float(pr2["depth"])
		for j in 2:
			var ent: Dictionary = s["up"] if j == 1 else s["idle"]
			var wgt := upw if j == 1 else 1.0 - upw
			if wgt < 0.01 or ent.is_empty() or ent["tex"] == null:
				continue
			var kk: float = k * float(ent["scale"])
			var tx: Texture2D = ent["tex"]
			p2.items.append([tx, Rect2(-(ent["pivot"] as Vector2) * kk, Vector2(tx.get_width(), tx.get_height()) * kk), Color(tint, al * wgt)])
		p2.queue_redraw()


## Painter's order, far to near: dancers, silhouettes and occluders together by distance along the view axis (ties by name so equal depths never swap).
func _sort_world() -> void:
	var nodes: Array = []
	var keys: Array = []  # (4000 m - depth) in millimetres shifted left 10 bits, plus the item's index: a plain integer sort, far first, ties in the fixed index order
	for id in _order:
		var a: Dictionary = actors[id]
		var c: StoryCharacter = a["node"]
		nodes.append(c)
		keys.append(((4000000 - int(clampf(float(a.get("depth", 0.0)), 0.0, 3999.0) * 1000.0)) << 10 if c.visible else 0) | (nodes.size() - 1))
	for pn in props:
		nodes.append(pn)
		keys.append(((4000000 - int(clampf((pn as StoryCrowdProp).depth, 0.0, 3999.0) * 1000.0)) << 10 if pn.visible else 0) | (nodes.size() - 1))
	keys.sort()
	for i in keys.size():
		var n: Node = nodes[int(keys[i]) & 1023]
		if get_child(i) != n:
			move_child(n, i)


## The ids of the dancers drawn this frame, far to near (what the tests check).
func drawn_order() -> Array:
	var out: Array = []
	for ch in get_children():
		if ch is StoryCharacter and (ch as StoryCharacter).visible:
			out.append((ch as StoryCharacter).actor_id)
	return out


var _rows_cache: Variant = null


func _scale_at(y: float) -> float:
	if _rows_cache == null:
		_rows_cache = assets.anchor("floor_rows", [], view)
	var rows: Array = _rows_cache
	if rows.is_empty():
		return 0.55 + clampf((y - 300.0) / 140.0, 0.0, 1.0) * 0.45
	if y <= float(rows[0]["y"]):
		return float(rows[0]["scale"])
	for i in range(1, rows.size()):
		if y <= float(rows[i]["y"]):
			var u := (y - float(rows[i - 1]["y"])) / maxf(float(rows[i]["y"]) - float(rows[i - 1]["y"]), 0.001)
			return lerpf(float(rows[i - 1]["scale"]), float(rows[i]["scale"]), u)
	return float(rows[rows.size() - 1]["scale"])


func _mood_state(a: Dictionary, e01: float) -> String:
	var ee := energy + float(a["thresh"])
	if _ending != "":
		return _ending_state(a, ee)
	if ee < 18.0:
		return "sad"
	if ee < 32.0:
		return "idle"
	if ee < 70.0:
		return "dance"
	if ee < 88.0:
		return "dance" if (_xv(a) / 40) % 3 != 0 else "cheer"
	return "cheer"


func _ending_state(a: Dictionary, ee: float) -> String:
	match _ending:
		"legendary":
			return "cheer" if _xv(a) % 3 != 0 else "hands_up"
		"good":
			return "clap" if _xv(a) % 2 == 0 else "dance"
		_:
			return "sad" if _xv(a) % 3 != 0 else ("clap" if _xv(a) % 6 == 0 else "look")


func _draw() -> void:
	if world_mode:
		_draw_blobs()
		return
	var e := energy
	var beats := _t_now * bpm / 60.0
	var rise := sin(PI * fposmod(beats, 1.0))  # the rear rows bounce on the beat like the dancers in front
	var tint := Color(0.55, 0.6, 0.85).lerp(Color(0.78, 0.76, 1.0), clampf((e - 20.0) / 30.0, 0.0, 1.0))
	for s in _sils:
		var al := float(s["alpha"])
		if al < 0.02:
			continue
		var sway := sin((beats * 0.25 + float(s["ph"])) * TAU) * (2.0 + e * 0.05)
		var bob := rise * (1.0 + e * 0.07) * clampf((e - 25.0) / 15.0, 0.0, 1.0)
		var upw := float(s.get("upw", 0.0))
		for k in 2:  # idle and hands-up cross-fade instead of popping
			var ent: Dictionary = s["up"] if k == 1 else s["idle"]
			var w := upw if k == 1 else 1.0 - upw
			if w < 0.01 or ent.is_empty() or ent["tex"] == null:
				continue
			var sc := float(s["scale"]) * float(ent["scale"])
			draw_set_transform(Vector2(float(s["x"]) + sway, float(s["y"]) - bob), 0.0, Vector2(sc, sc))
			draw_texture(ent["tex"], -ent["pivot"], Color(tint, al * w))
	draw_set_transform_matrix(Transform2D.IDENTITY)
	_draw_shadows()


## A soft contact shadow under every dancer (drawn before the dancers, which are this node's children), smaller and lighter while
## they are in the air, so feet sit on the floor instead of floating over it.
func _draw_shadows() -> void:
	if _shadow.is_empty():
		_shadow = assets.sprite("glow")
	if _shadow.is_empty() or _shadow["tex"] == null:
		return
	var tex: Texture2D = _shadow["tex"]
	for id in _order:
		var a: Dictionary = actors[id]
		var c: StoryCharacter = a["node"]
		if not c.visible or c.modulate.a < 0.05:
			continue
		var air := clampf(float(c.cur.get("jump", 0.0)) / 30.0, 0.0, 1.0)
		var w := 92.0 * c.scale.x * (1.0 - 0.35 * air)
		var feet := c.position + Vector2(float(c.cur.get("sway_x", 0.0)) * c.scale.x, 0.0)
		draw_texture_rect(tex, Rect2(feet - Vector2(w * 0.5, w * 0.13), Vector2(w, w * 0.26)), false,
			Color(0.0, 0.0, 0.04, 0.55 * c.modulate.a * (1.0 - 0.5 * air)))


## Flat contact shadows in the world: one dark ellipse under each drawn dancer (smaller in the air), drawn first so every dancer and prop covers them.
func _draw_blobs() -> void:
	for id in _order:
		var a: Dictionary = actors[id]
		var c: StoryCharacter = a["node"]
		if not c.visible or c.modulate.a < 0.05:
			continue
		var air := clampf(float(c.cur.get("jump", 0.0)) / 30.0, 0.0, 1.0)
		var ppm: float = c.scale.x * float(c.rig.get("height", 260.0)) / HERO_M  # pixels per metre at this dancer
		var r := 0.42 * ppm * (1.0 - 0.35 * air)
		draw_set_transform(c.position + Vector2(float(c.cur.get("sway_x", 0.0)) * c.scale.x, 0.0), 0.0, Vector2(1.0, 0.3))
		draw_circle(Vector2.ZERO, maxf(r, 1.0), Color(0.0, 0.0, 0.04, 0.5 * c.modulate.a * (1.0 - 0.5 * air)))
	draw_set_transform_matrix(Transform2D.IDENTITY)


var _shadow: Dictionary = {}


var _t_now := 0.0
var _last_t := -INF
const FADE_PER_S := 3.0  # arrivals and exits fade over a third of a second of song time


func set_time(t: float) -> void:
	_t_now = t


# --- actions ---------------------------------------------------------------------------------------------------------

func ids_of(group: String) -> Array:
	if data.groups.has(group):
		return data.groups[group].filter(func(i: Variant) -> bool: return actors.has(str(i)))
	var out: Array = []
	for id in actors:
		if str(actors[id]["data"]["group"]) == group:
			out.append(id)
	return out


func present_ids() -> Array:
	var out: Array = []
	for id in _order:
		if actors[id]["present"]:
			out.append(id)
	return out


func direct(ids: Array, state: String, t0: float, seconds: float, sync := false, stagger := 0.0) -> void:
	var k := 0
	for id in ids:
		if not actors.has(id):
			continue
		var a: Dictionary = actors[id]
		if not a["present"]:
			continue
		a["dir"] = {"state": state, "from": t0 + float(k) * stagger, "until": t0 + seconds + float(k) * stagger, "sync": sync}
		k += 1


## A wave of `state` travelling left to right across the room over `seconds`, each dancer holding it for `hold` seconds.
func wave(t0: float, seconds: float, hold: float, state := "cheer") -> void:
	for id in present_ids():
		var a: Dictionary = actors[id]
		var u := clampf(float((a["pos"] as Vector2).x) / 1280.0, 0.0, 1.0)
		if world_mode:
			u = clampf((float((a["pos"] as Vector2).x) - floor_x.x) / maxf(floor_x.y - floor_x.x, 0.001), 0.0, 1.0)
		a["dir"] = {"state": state, "from": t0 + u * seconds, "until": t0 + u * seconds + hold, "sync": false}


func walk_to(id: String, to: Vector2, t0: float, seconds: float, then: Dictionary = {}, hide_after := false) -> void:
	if not actors.has(id):
		return
	var a: Dictionary = actors[id]
	a["move"] = {"from": a["pos"], "to": to, "t0": t0, "t1": t0 + seconds, "then": then, "hide_after": hide_after}
	if world_mode:  # walk the sector graph (through the doors), never through a wall
		var from: Vector2 = a["pos"]
		var from_sec := map.sector_at(from)
		var to_sec := map.sector_at(to)
		var pts := PackedVector2Array([from, to])
		if from_sec != "" and to_sec != "":
			var r := map.route(from, from_sec, to, to_sec)
			if (r["points"] as PackedVector2Array).size() >= 2:
				pts = r["points"]
		var cum := PackedFloat32Array([0.0])
		for i in range(1, pts.size()):
			cum.append(cum[i - 1] + pts[i - 1].distance_to(pts[i]))
		a["move"]["path"] = pts
		a["move"]["cum"] = cum


func bring_in(group: String, t0: float, seconds := 4.0, from_door := true) -> void:
	var k := 0
	for id in ids_of(group):
		var a: Dictionary = actors[id]
		if a["present"] and a["move"].is_empty():
			continue
		a["present"] = true
		var start: Vector2 = door_pos + Vector2(float(k % 3) * (0.3 if world_mode else 10.0), 0.0)
		if str(a["data"].get("enter_from", "doorway")) == "side":
			start = _side_start(a)
		a["pos"] = start
		a["alpha"] = 0.0
		walk_to(id, a["home"], t0 + float(k) * 0.45, seconds)
		k += 1
	for s in _sils:
		if s["group"] == group:
			s["present"] = true


## Where someone coming in from the side starts: the left or right door of the room, by which side their place is on.
func _side_start(a: Dictionary) -> Vector2:
	if world_mode:
		return map.spot("side_l" if (a["home"] as Vector2).x < 0.0 else "side_r").get("at", door_pos)
	return Vector2(-60.0 if (a["home"] as Vector2).x < 640.0 else 1340.0, (a["home"] as Vector2).y)


## Where a person waiting outside the door stands (door_slot indexes the map's door slots; design pixels in the 2D rooms).
func _door_wait(a: Dictionary, k: int) -> Vector2:
	var slot := int(a["data"].get("door_slot", k))
	if world_mode and not door_slots.is_empty():
		return door_slots[slot % door_slots.size()]
	return door_pos + Vector2(float(slot % 4) * 34.0 - 10.0, 24.0 + float(slot / 4) * 22.0)


func gather_at_door(group: String, t0: float) -> void:
	var k := 0
	for id in ids_of(group):
		var a: Dictionary = actors[id]
		a["present"] = true
		var wait := _door_wait(a, k)
		a["pos"] = door_pos
		a["alpha"] = 0.0
		walk_to(id, wait, t0 + float(k) * 0.5, 2.5, {"state": "look", "from": 0.0, "until": NO_END})
		k += 1
	for s in _sils:
		if s["group"] == group:
			s["present"] = true
	_resort()


func gatherers_enter(t0: float, all := true) -> void:
	var k := 0
	for id in ids_of("gatherers"):
		var a: Dictionary = actors[id]
		if all or bool(a["data"].get("stays_on_bad", false)):
			if not a["present"]:  # never gathered at the door (or a room without one): they walk in now, visibly
				a["present"] = true
				a["alpha"] = 0.0
				a["pos"] = door_pos + Vector2(float(k % 3) * (0.3 if world_mode else 10.0), 0.0)
				if str(a["data"].get("enter_from", "doorway")) == "side" or (door_pos.x < 0.0 and not world_mode):
					a["pos"] = _side_start(a)
			walk_to(id, a["home"], t0 + float(k) * 0.35, 4.0)
			a["dir"] = {}
		elif not a["present"]:
			k += 1
			continue  # a dancer who never showed up does not appear just to leave
		else:
			var side: Vector2 = map.home(str(id)).get("side", a["home"]) if world_mode else Vector2(float(a["data"].get("side_x", 60.0)), float(assets.floor_at(float(a["data"].get("side_depth", 0.4)), view)["y"]))
			walk_to(id, side, t0 + float(k) * 0.35, 3.0, {"state": "look", "from": 0.0, "until": NO_END})
		k += 1
	if all:
		for s in _sils:
			if s["group"] == "gatherers":
				s["present"] = true


func step_back_some(t0: float) -> void:
	for id in ids_of("core"):
		var a: Dictionary = actors[id]
		if float(a["thresh"]) >= 4.0:
			var out: Vector2 = a["home"]
			if world_mode:
				out.x = clampf(out.x + (-1.4 if out.x < 0.0 else 1.4), floor_x.x + 0.5, floor_x.y - 0.5)
			else:
				out.x += (-90.0 if out.x < 640.0 else 90.0)
			walk_to(id, out, t0, 2.5, {"state": "look", "from": 0.0, "until": t0 + 9.0})


func regroup(t0: float) -> void:
	for id in actors:
		var a: Dictionary = actors[id]
		if a["present"] and (a["pos"] as Vector2).distance_to(a["home"]) > (0.1 if world_mode else 4.0):
			walk_to(id, a["home"], t0, 2.5)


func circle_form(t0: float, seconds := 3.5) -> void:
	var ids := ids_of("circle").filter(func(i: Variant) -> bool: return actors[str(i)]["present"])
	var n := maxi(ids.size(), 1)
	var gap := OPEN_GAP  # radians kept clear either side of the front: the circle opens towards the DJ so its centre stays in view
	var open_ang := PI * 0.5 if not world_mode else circle_open.angle()  # the 2D rooms open towards the viewer (down the screen); the world towards the map's `open`
	for k in ids.size():
		var ang := open_ang + gap + (TAU - 2.0 * gap) * float(k) / float(maxi(n - 1, 1))
		var pos := circle_c + Vector2(cos(ang) * circle_r.x, sin(ang) * circle_r.y)
		walk_to(str(ids[k]), pos, t0 + float(k) * 0.12, seconds, {"state": "dance", "from": 0.0, "until": NO_END})
	_resort()


func circle_scatter(t0: float, awkward := true) -> void:
	for id in ids_of("circle"):
		var a: Dictionary = actors[id]
		if not a["present"]:
			continue
		var out: Vector2 = a["home"]
		walk_to(id, out, t0, 3.0, {"state": "look" if awkward else "dance", "from": 0.0, "until": t0 + 8.0})


func hero_to(pos: Vector2, t0: float, seconds := 2.5, then: Dictionary = {}) -> void:
	for id in actors:
		if str(actors[id]["data"].get("role", "")) == "hero":
			walk_to(id, pos, t0, seconds, then)
			return


## The room is carried away (an abduction lifts, hellfire sinks): everyone present rises or falls by `dy` px over `seconds`, shrinking and fading.
func vanish_all(t0: float, seconds: float, dy: float, stagger := 0.12) -> void:
	var k := 0
	for id in _order:
		var a: Dictionary = actors[id]
		if not a["present"]:
			continue
		a["vanish"] = {"t0": t0 + float(k) * stagger, "t1": t0 + float(k) * stagger + seconds, "dy": dy}
		k += 1


## Where the hero stands in the middle of the circle, and where a soloist stands on the riser (world: the map's spots; 2D rooms: the art's anchors).
func centre_spot() -> Vector2:
	return circle_c if world_mode else circle_c + Vector2(0.0, 18.0)


func solo_spot() -> Vector2:
	if world_mode:
		return riser_spot
	var rl: Array = assets.anchor("riser", [circle_c.x, circle_c.y - 20.0, 260], view)
	return Vector2(float(rl[0]), float(rl[1]) - 6.0)


func hero_node() -> StoryCharacter:
	for id in actors:
		if str(actors[id]["data"].get("role", "")) == "hero":
			return actors[id]["node"]
	return null


func hero_id() -> String:
	for id in actors:
		if str(actors[id]["data"].get("role", "")) == "hero":
			return id
	return ""


func set_ending(key: String) -> void:
	_ending = data.tableau_of(key) if key != "" else ""
	for id in actors:
		actors[id]["dir"] = {}


## The two-bar result's local reaction (the persistent mood is the energy): a share of the room cheers or looks uncertain.
func react(passed: bool, grade: String, t0: float) -> void:
	var ids := present_ids()
	var share: float = float({"sharp": 0.6, "steady": 0.45, "loose": 0.3}.get(grade, 0.0)) if passed else 0.45
	for k in ids.size():
		if _rng.randf() > share:
			continue
		var a: Dictionary = actors[ids[k]]
		if passed:
			a["dir"] = {"state": "cheer" if energy > 45.0 else "dance", "from": t0, "until": t0 + 1.4, "sync": false}
		else:
			a["dir"] = {"state": "look" if energy > 25.0 else "sad", "from": t0, "until": t0 + 1.6, "sync": false}
