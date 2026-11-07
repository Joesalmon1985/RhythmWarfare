extends SceneTree
## Frame time of a story map at a camera pose (docs/story/HEIGHTS_AND_PATHS.md, the budget): builds the map's StoryWorld in a scene, stands the camera at a pose and turns it
## slowly (half a degree a frame, so the visible set is worked out again every frame, as on a walk), and times N frames:
##   * vis: the two portal walks StoryStage does each frame the camera moves (the crowd's and the geometry's, StoryMap.visible_sectors);
##   * world: StoryWorld.set_visible_sectors + StoryWorld.update (the song-time light of every drawn sector and thing);
##   * frame: the whole frame, process callback to process callback.
## and counts what would be drawn: visible sectors, their triangles, their surfaces (one draw call each) and the visible billboards. Mean and p95 in ms.
##   godot --headless --audio-driver Dummy --path . -s tools/art/frame_time.gd -- --map=<id> [--wp=<waypoint> | --pose=x:z:yaw] [--frames=300] [--mode=flood|clip|none]
##   ... --synthetic=<rooms per side>x<pieces per room side> (a generated map of rooms cut into pieces with doors and steps: 5x4 is 400 pieces)
## Headless the dummy renderer draws nothing: these are CPU figures on this desktop ("desktop, headless"), never phone figures. The counts are what a GPU would get.

var _args := {}
var _map: StoryMap
var _world: Node3D
var _cam: Camera3D
var _frame := -1
var _n := 300
var _pos := Vector2.ZERO
var _yaw := 0.0
var _sec := ""
var _last_us := 0
var _ms_frame: Array = []
var _ms_vis: Array = []
var _ms_world: Array = []
var _counts := {"sectors": 0.0, "tris": 0.0, "surfaces": 0.0, "things": 0.0}
var _tri_of: Dictionary = {}
var _surf_of: Dictionary = {}


func _initialize() -> void:
	for a in OS.get_cmdline_user_args():
		var kv := str(a).trim_prefix("--").split("=", true, 1)
		_args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	_n = int(_args.get("frames", "300"))
	if _args.has("synthetic"):
		var dims := str(_args["synthetic"]).split("x")
		_map = StoryMap.from_dict(synthetic(int(dims[0]), int(dims[1])), "mothership")
		_map.art = "mothership"
	else:
		_map = StoryMap.load_chapter(str(_args.get("map", "mothership")))
	if not _map.errors.is_empty():
		print("FRAMETIME map errors: ", _map.errors.slice(0, 5))
		quit(1)
		return
	if _args.has("mode") and str(_args["mode"]) != "none":
		_map.vis_mode = str(_args["mode"])
	var wp := _map.waypoint(str(_args.get("wp", _map.start_id)))
	_pos = wp.get("at", Vector2.ZERO)
	_yaw = float(wp.get("yaw", 0.0))
	_sec = str(wp.get("sector", ""))
	if _args.has("pose"):
		var q := str(_args["pose"]).split(":")
		_pos = Vector2(float(q[0]), float(q[1]))
		_yaw = float(q[2])
		_sec = _map.sector_at(_pos)
	_world = load("res://src/story/world/story_world.gd").new()  # (by path: a SceneTree script compiles before the autoloads)
	_world.build(_map, StoryAssets.load_art(_map.art))
	root.add_child(_world)
	_cam = Camera3D.new()
	root.add_child(_cam)
	for s in _map.sectors:
		var mi: MeshInstance3D = _world.sector_node(str(s["id"]))
		var tris := 0
		for k in (mi.mesh as ArrayMesh).get_surface_count():
			tris += ((mi.mesh as ArrayMesh).surface_get_arrays(k)[Mesh.ARRAY_INDEX] as PackedInt32Array).size() / 3
		_tri_of[str(s["id"])] = tris
		_surf_of[str(s["id"])] = (mi.mesh as ArrayMesh).get_surface_count()


func _process(_delta: float) -> bool:
	_frame += 1
	var now := Time.get_ticks_usec()
	if _frame > 30 and _frame <= 30 + _n:
		_ms_frame.append((now - _last_us) / 1000.0)
	_last_us = now
	if _frame > 30 + _n:
		_report()
		return true
	var yaw := _yaw + 0.5 * float(_frame % 240) - 60.0  # a slow sweep of 120 degrees around the pose's facing
	var t := float(_frame) / 60.0
	var t0 := Time.get_ticks_usec()
	var vis: Dictionary = {}
	var vis_geo: Dictionary = {}
	if str(_args.get("mode", "")) != "none":
		vis = _map.visible_sectors(_pos, yaw, _sec, 480.0 / 170.0)
		vis_geo = _map.visible_sectors(_pos, yaw, _sec, 480.0 / 170.0, 7)
	var t1 := Time.get_ticks_usec()
	_world.set_visible_sectors(vis_geo)
	_world.update(t, {"bpm": 174.0, "energy": 60.0, "palette": [Color(1, 0.3, 0.8), Color(0.2, 1, 0.9)]})
	var t2 := Time.get_ticks_usec()
	_cam.position = Vector3(_pos.x, float(_map.sector(_sec).get("floor", 0.0)) + _map.eye_height, _pos.y)
	_cam.rotation_degrees = Vector3(0, yaw, 0)
	if _frame > 30:
		_ms_vis.append((t1 - t0) / 1000.0)
		_ms_world.append((t2 - t1) / 1000.0)
		var drawn: Array = vis_geo.keys() if not vis_geo.is_empty() else _tri_of.keys()
		_counts["sectors"] += drawn.size()
		for sid in drawn:
			_counts["tris"] += _tri_of[sid]
			_counts["surfaces"] += _surf_of[sid]
		var things := 0
		for th in _world._thing_nodes:
			if (th["node"] as Node3D).visible:
				things += 1
		_counts["things"] += things
		vis.size()
	return false


static func _stats(a: Array) -> String:
	if a.is_empty():
		return "-"
	var s := a.duplicate()
	s.sort()
	var sum := 0.0
	for v in s:
		sum += float(v)
	return "mean %.3f p95 %.3f" % [sum / s.size(), float(s[int(s.size() * 0.95)])]


func _report() -> void:
	var n := maxf(_ms_vis.size(), 1)
	print("FRAMETIME %s mode=%s pieces=%d frames=%d (desktop, headless) | frame %s ms | vis %s ms | world %s ms | drawn: %.1f sectors, %.0f triangles, %.1f surfaces, %.1f billboards" % [
		_args.get("synthetic", _args.get("map", "?")), _args.get("mode", _map.vis_mode), _map.sectors.size(), _ms_frame.size(), _stats(_ms_frame), _stats(_ms_vis), _stats(_ms_world),
		_counts["sectors"] / n, _counts["tris"] / n, _counts["surfaces"] / n, _counts["things"] / n])
	quit(0)


## A generated map of `rooms` x `rooms` rooms, each cut into `pieces` x `pieces` square pieces of 2 m (open portals inside a room), rooms joined by one door piece per shared
## side, floors stepping by 0.2 m from room to room (Mothership tiles).
static func synthetic(rooms: int, pieces: int) -> Dictionary:
	var tex := {"w": "textures/wall_hull.png", "f": "textures/floor_grate.png", "c": "textures/ceil_hull.png", "s": "textures/floor_dais.png"}
	var sectors: Array = []
	var walls: Array = []
	var n := rooms * pieces
	var floor_of := func(i: int, j: int) -> float: return 0.2 * float(((i / pieces) + (j / pieces)) % 3)
	for i in n:
		for j in n:
			var x := float(i) * 2.0
			var z := float(j) * 2.0
			sectors.append({"id": "p%d_%d" % [i, j], "polygon": [[x, z], [x + 2, z], [x + 2, z + 2], [x, z + 2]], "floor": floor_of.call(i, j), "ceiling": 3.5,
				"floor_tex": "f", "ceil_tex": "c", "wall_tex": "w", "step_tex": "s"})
			var mid := pieces / 2
			if i + 1 < n and ((i + 1) % pieces != 0 or j % pieces == mid):
				walls.append({"sector": "p%d_%d" % [i, j], "from": [x + 2, z], "to": [x + 2, z + 2], "portal": "p%d_%d" % [i + 1, j]})
			if j + 1 < n and ((j + 1) % pieces != 0 or i % pieces == mid):
				walls.append({"sector": "p%d_%d" % [i, j], "from": [x, z + 2], "to": [x + 2, z + 2], "portal": "p%d_%d" % [i, j + 1]})
	return {"textures": tex, "sectors": sectors, "walls": walls, "start": "a", "waypoints": [{"id": "a", "at": [float(n) + 1.0, float(n) + 1.0], "yaw": 0, "sector": "p%d_%d" % [n / 2, n / 2]}]}
