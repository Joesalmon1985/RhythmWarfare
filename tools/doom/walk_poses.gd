extends SceneTree
## The camera poses along a Doom scene's polyline moves, for tools/doom/shoot_scene.py walk (docs/doom/scenes/warehouse.md):
##   godot --headless --audio-driver Dummy --path . -s tools/doom/walk_poses.gd -- doom_warehouse ahead|left|right|stay [run.json [node]]
## `ahead` is the scene's rail.routes.up move from the node's home; `stay` is the good rail from home, move after move with each place's hold_bars. Prints
##   WALK <route> <i> t=<s> @<x>:<z>:<yaw>:<pitch>:<eye y> sector=<id> ground=<floor> above=<eye over the local floor> still=<0..1>
## one line per frame (12 frames: evenly in time along `ahead`; the third, the two thirds and the end of each leg of `stay`), then
##   HOLD <place> <bars> moved=<metres the camera moves between the middle and the end of the hold> turned=<degrees>
## for every hold of the route, and `MOVE <place> via=<n> length=<m>` for every move. The player runs with the idle drift off and the bob on, as in play.



func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var map_id := str(args[0]) if args.size() > 0 else "doom_warehouse"
	var route := str(args[1]) if args.size() > 1 else "ahead"
	var run_path := str(args[2]) if args.size() > 2 else "res://content/run/doom/run.json"
	var node_id := str(args[3]) if args.size() > 3 else "doom_warehouse"  # the scene's node (the Copper Bar passes doom_bar)
	var run: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(run_path))
	var node: Dictionary = {}
	for n in run["nodes"]:
		if str(n["id"]) == node_id:
			node = n
	var home := str(node["place"]["waypoint"])
	var rail: Dictionary = node["place"]["rail"]
	var m := StoryMap.load_chapter(map_id, false)
	if not m.errors.is_empty():
		print("map errors: ", m.errors)
		quit(1)
		return
	var moves: Array = []
	if route in ["ahead", "left", "right"]:  # a route walk: rail.routes.up (ahead), .left or .right from the node's home
		var fr: Array = []
		for k in 12:
			fr.append(float(k) / 11.0)
		moves.append({"spec": rail["routes"][{"ahead": "up", "left": "left", "right": "right"}[route]], "from": home, "frames": fr})
	else:
		var from := home
		for g in rail["good"]:
			moves.append({"spec": g, "from": from, "frames": [1.0 / 3.0, 2.0 / 3.0, 1.0]})
			from = str(g["to"])
	var p := StoryPlayer.new()
	p.setup(m, 174.0)
	p.start_at = home
	p.reset()
	p.drift_on = false
	var t := 0.0
	var plans: Array = []
	for mv in moves:
		var spec: Dictionary = mv["spec"]
		var a := {"to": str(spec["to"]), "style": str(spec.get("style", "walk")), "bars": float(spec.get("bars", 3.0))}
		if spec.has("via"):
			a["via"] = spec["via"]
		if spec.has("hold_bars"):
			a["hold_bars"] = spec["hold_bars"]
		p.apply_action({"t0": t, "action": "player_move", "args": a})
		var t1 := t + float(a["bars"]) * p.bar_s()
		plans.append({"t0": t, "t1": t1, "hold": float(spec.get("hold_bars", 0.0)), "to": str(spec["to"]), "frames": mv["frames"], "via": (spec.get("via", []) as Array).size()})
		t = t1 + float(spec.get("hold_bars", 0.0)) * p.bar_s()
	var idx := 0
	for pl in plans:
		var ev := p.move_plan(float(pl["t0"]) + 0.01)
		var len_m := 0.0
		if not ev.is_empty() and ev.has("cum"):
			len_m = float((ev["cum"] as Array).back())
		print("MOVE %s via=%d length=%.1f" % [pl["to"], int(pl["via"]), len_m])
		for f in pl["frames"]:
			var tt: float = float(pl["t0"]) + float(f) * (float(pl["t1"]) - float(pl["t0"]))
			var pose := p.pose_at(tt)
			var cam: Vector3 = pose["cam"]
			var pos: Vector2 = pose["pos"]
			var above := cam.y - StoryRailCheck.stair_floor(m, ev, StoryPlayer.distance_at(ev, minf(tt, float(pl["t1"]))), str(pose["sector"])) if not ev.is_empty() else 0.0
			print("WALK %s %d t=%.2f @%.3f:%.3f:%.1f:%.1f:%.3f sector=%s ground=%.3f above=%.2f still=%.2f" % [route, idx, tt, pos.x, pos.y, float(pose["yaw"]), float(pose["pitch"]), cam.y, str(pose["sector"]), float(pose["ground"]), above, float(pose.get("still", 0.0))])
			idx += 1
		if float(pl["hold"]) > 0.0:
			var h0 := float(pl["t1"]) + 0.5 * float(pl["hold"]) * p.bar_s()
			var h1 := float(pl["t1"]) + float(pl["hold"]) * p.bar_s() - 0.01
			var a0 := p.pose_at(h0)
			var a1 := p.pose_at(h1)
			var moved := (a0["cam"] as Vector3).distance_to(a1["cam"])
			var turned := absf(angle_difference(deg_to_rad(float(a0["yaw"])), deg_to_rad(float(a1["yaw"])))) * 180.0 / PI
			print("HOLD %s %.1f moved=%.4f turned=%.3f" % [pl["to"], float(pl["hold"]), moved, turned])
	quit(0)
