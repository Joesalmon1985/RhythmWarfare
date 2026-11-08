extends SceneTree
## Where a main-run scene's way back to its hub (`<scene>.to_hub`) and a hub's link to its partner (`<hub>.to_<partner>`) may stand (the shared wiring step): plays every main-run scene
## as the player comes into it (tools/art/camera_clearance_check.gd: the run's journey, the perfect bot, the window's look), samples the camera in the route window, and judges the
## door's spot: in the narrowest picture we ship at the window's samples, no wall between the eye and the door, clear of the other choices' anchors and of the room's walls. Where it
## fails it searches the room for a better spot. A survey for whoever sets tools/run/make_scenes.py BACK_SPOTS; the game does not read it.
##
##     bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/run/hub_door_spots.gd -- [--only <regex>] [--out file.json]

const WIN_BEATS := [50.0, 52.0, 54.0, 56.0, 58.0, 60.0]


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	var CC: GDScript = load("res://tools/art/camera_clearance_check.gd")
	var H: GDScript = load("res://tools/run/hub_door_spots_check.gd")
	var args := OS.get_cmdline_user_args()
	var only := ""
	var out_path := ""
	var i := 0
	while i < args.size():
		match args[i]:
			"--only":
				only = args[i + 1]
				i += 1
			"--out":
				out_path = args[i + 1]
				i += 1
		i += 1
	var rx: RegEx = RegEx.create_from_string(only) if only != "" else null
	var report := {}
	var bad := 0
	for sc in CC.scenes():
		var data = sc["data"]
		if data.is_path():
			continue
		var id := str(sc["id"])
		if rx != null and rx.search(id) == null:
			continue
		var node: Dictionary = data.nodes[id]
		var door := ""
		var dir := ""
		for e in node["next"]:
			if bool(e.get("to_hub", false)) or bool(e.get("hub_link", false)):
				dir = str(e["dir"])
				door = "%s.%s" % [id, "to_hub" if bool(e.get("to_hub", false)) else "to_" + str(e["to"])]
		if door == "":
			continue
		var m = CC.map_of(str(node["map"]))
		var entries: Array = sc["entries"]
		var poses: Array = []
		for en in entries:
			var run: Dictionary = CC.play(data, id, en, 2)
			var p = run["player"]
			for b in WIN_BEATS:
				poses.append(p.pose_at(float(run["t0"]) + float(b) * float(run["beat"])))
		var others: Array = H.others_of(data, id, door, m)
		var wp := str(node["rail"]["exits"][dir])
		var at: Vector2 = m.waypoint(wp)["at"]
		var res: Dictionary = H.judge(m, at, poses, others)
		var entry := {"door": door, "ok": res["ok"], "why": res["why"], "xz": [snappedf(at.x, 0.01), snappedf(at.y, 0.01)]}
		if not bool(res["ok"]):
			var best: Dictionary = H.search(m, poses, others, str(m.waypoint(wp)["sector"]))
			entry["best"] = best
			if best.is_empty():
				bad += 1
		report[id] = entry
		print("%s %-22s %-34s (%.2f, %.2f) %s%s" % ["ok  " if bool(res["ok"]) else "FAIL", id, door, at.x, at.y, ", ".join(PackedStringArray(res["why"])),
			"" if not entry.has("best") else ("  best=" + (str(entry["best"]["xz"]) + " seen " + str(entry["best"]["seen"]) if not (entry["best"] as Dictionary).is_empty() else "none"))])
	if out_path != "":
		var fh := FileAccess.open(out_path, FileAccess.WRITE)
		fh.store_string(JSON.stringify(report, " "))
		fh.close()
	print("doors judged: %d, without a spot: %d" % [report.size(), bad])
	quit(0)


