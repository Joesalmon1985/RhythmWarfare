extends SceneTree
## Camera clearance (docs/art/VISUAL_AUDIT.md F5 and F16, package A5): does the run camera ever stare into a wall from arm's length?
##
##     bash tools/dev/godot.sh --headless --path . -s tools/art/camera_clearance.gd -- [--step 0.5] [--only <regex on scene id>] [--doc before|after] [--dump file.csv] [--direct-all]
##
## Plays every scene of the main run and of the three paths, for every way the player comes into it, on the real rail camera and casts a row of rays across the picture
## at every sample (tools/art/camera_clearance_check.gd: what is checked and the thresholds). Prints the failing poses (scene, entry, beat range, pose kind,
## distances, the wall) and a count per world; --doc <label> also writes them into docs/art/CAMERA_CLEARANCE.md between `<!-- clearance:<label> -->` markers; --dump writes
## every sample as CSV. Exits 1 when any pose fails. tests/test_camera_clearance.gd runs the same check.

const DOC := "res://docs/art/CAMERA_CLEARANCE.md"


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame  # (the game's classes compile once the autoloads are in: the check is loaded here, not at parse time)
	var CC: GDScript = load("res://tools/art/camera_clearance_check.gd")
	var args := OS.get_cmdline_user_args()
	var step := 0.5
	var only := ""
	var doc := ""
	var dump_path := ""
	var direct_all := false  # also start every scene on its own (RW_RUN_START, what tools/art/audit_capture.sh shoots), not only the run's first
	var i := 0
	while i < args.size():
		match args[i]:
			"--step":
				step = float(args[i + 1])
				i += 1
			"--only":
				only = args[i + 1]
				i += 1
			"--doc":
				doc = args[i + 1]
				i += 1
			"--search":  # a dev aid for whoever fixes a scene: tries small changes of its glances, strolls and places and prints those that pass: --search <scene id>
				_search(CC, args[i + 1])
				quit(0)
				return
			"--waypoints":  # the clearance of every waypoint of a map at its own yaw and turned by `turns` (a survey for whoever places a rail): --waypoints <map id>
				_survey(CC, args[i + 1])
				quit(0)
				return
			"--direct-all":
				direct_all = true
			"--dump":
				dump_path = args[i + 1]
				i += 1
		i += 1
	var t_start := Time.get_ticks_msec()
	var dump: Array = ["scene,entry,from,beat,centre,share,kind,transit,what"] if dump_path != "" else []
	var rows: Array = CC.check_all(step, only, dump, direct_all)
	var total := 0
	for r in rows:
		total += (r["fails"] as Array).size()
		for er in r["errors"]:
			print("  journey error %s (%s): %s" % [r["scene"], r["entry"], er])
	var tab: String = CC.table(rows)
	var sm: String = CC.summary(rows)
	var exc_n := 0
	for r in rows:
		exc_n += (r.get("excepted", []) as Array).size()
	var exc: String = CC.table(rows, "excepted")
	print(tab)
	print("")
	print(sm)
	if exc_n > 0:
		print("")
		print("Accepted exceptions (%d poses, tools/art/camera_clearance_check.gd EXCEPTIONS):" % exc_n)
		print(exc)
	print("camera clearance: %d failing poses, %d scene entries, step %.2f beats, %.1f s" % [total, rows.size(), step, (Time.get_ticks_msec() - t_start) / 1000.0])
	if dump_path != "":
		var f := FileAccess.open(dump_path, FileAccess.WRITE)
		f.store_string("\n".join(dump.slice(0)) + "\n")
		f.close()
	if doc != "":
		var extra := "" if exc_n == 0 else "\n\nAccepted exceptions (%d poses):\n\n%s" % [exc_n, exc]
		_write_doc(doc, "%s\n\n%s\n\n%d failing poses over %d scene entries (step %.2f beats).%s" % [sm, tab, total, rows.size(), step, extra])
	quit(1 if total > 0 else 0)


## Fails of scene `id` (every entry, every phase) and of the door walks that start where its rail ends, with the scene's rail replaced by `rail`.
static func _eval(CC: GDScript, cases: Array, data: RunData, id: String, rail: Dictionary) -> int:
	var keep: Dictionary = data.nodes[id]["rail"]
	data.nodes[id]["rail"] = rail
	var n := 0
	for c in cases:
		for ph in ([1] if str(c["entry"]["kind"]) == "direct" else CC.PHASES):
			var run: Dictionary = CC.play(data, str(c["id"]), c["entry"], ph)
			run["id"] = c["id"]
			n += (CC.check_run(run, 1.0)["fails"] as Array).size()
	data.nodes[id]["rail"] = keep
	return n


static func _scaled(list: Array, k: float, keys: Array) -> Array:
	var out: Array = []
	for g in list:
		var h: Dictionary = (g as Dictionary).duplicate()
		for key in keys:
			if h.has(key):
				h[key] = snappedf(float(h[key]) * k, 0.1)
		out.append(h)
	return out


## The waypoints of `m` in `room` (all rooms when "") whose own pose and a 30-degree turn either way pass the check.
static func _open_waypoints(CC: GDScript, m: StoryMap, room: String) -> Array:
	var out: Array = []
	for wid in m.waypoints:
		var w: Dictionary = m.waypoints[wid]
		if room != "" and m.room_of(str(w["sector"])) != room:
			continue
		var ok := true
		for dy in [-30.0, 0.0, 30.0]:
			ok = ok and not CC.fails(CC.clearance(m, {"cam": Vector3(w["at"].x, float(m.sector(str(w["sector"]))["floor"]) + m.eye_height, w["at"].y), "yaw": float(w["yaw"]) + dy, "pitch": 0.0, "sector": w["sector"]}))
		if ok:
			out.append(wid)
	out.sort()
	return out


## Greedy: the best change of the strolls and glances first, then of each good place, then of the arrival; prints each stage's best few.
static func _search(CC: GDScript, id: String) -> void:
	var cases: Array = []
	var data: RunData = null
	for sc in CC.scenes():
		for entry in sc["entries"]:
			if str(sc["id"]) == id or (str(entry["kind"]) == "door" and str(entry["from"]) == id):
				if data == null or sc["data"] == data:
					data = sc["data"]
					cases.append({"id": sc["id"], "entry": entry})
	if data == null:
		print("no scene %s" % id)
		return
	var rail0: Dictionary = (data.nodes[id]["rail"] as Dictionary).duplicate(true)
	var m: StoryMap = CC.map_of(str(data.nodes[id]["map"]))
	var base := _eval(CC, cases, data, id, rail0)
	print("%s: %d failing poses as it is (%d cases)" % [id, base, cases.size()])
	if base == 0:
		return
	var gl0: Array = rail0["glances"]
	var st0: Array = rail0["strolls"]
	var nt: Array = []
	for x in st0:
		var y: Dictionary = (x as Dictionary).duplicate()
		y.erase("turn")
		nt.append(y)
	var strolls := {"as is": st0, "no turn": nt, "no turn, half": _scaled(nt, 0.5, ["fwd", "right"])}
	var glances := {"as is": gl0, "half": _scaled(gl0, 0.5, ["by", "pitch"])}
	var best := {"n": base, "rail": rail0, "what": "as is"}
	var stage := func(label: String, cands: Dictionary) -> void:
		var res: Array = []
		for k in cands:
			var n := _eval(CC, cases, data, id, cands[k])
			res.append([n, k])
			if n < int(best["n"]):
				best["n"] = n
				best["rail"] = cands[k]
				best["what"] = k
		res.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
		print("  %s: %s" % [label, ", ".join(res.slice(0, 5).map(func(r: Array) -> String: return "%s %d" % [r[1], r[0]]))])
	var c1 := {}
	for sk in strolls:
		for lk in glances:
			if sk == "as is" and lk == "as is":
				continue
			var r := rail0.duplicate(true)
			r["strolls"] = strolls[sk]
			r["glances"] = glances[lk]
			c1["strolls %s, glances %s" % [sk, lk]] = r
	stage.call("strolls/glances", c1)
	if int(best["n"]) > 0:
		var open := _open_waypoints(CC, m, "")
		var r0: Dictionary = best["rail"]
		var w0 := str(best["what"])
		var c2 := {}
		var good: Array = r0["good"]
		for i in good.size():
			var room := m.room_of(str(m.waypoint(str(good[i]["to"])).get("sector", "")))
			for wid in _open_waypoints(CC, m, room):
				if wid == good[i]["to"]:
					continue
				var r := r0.duplicate(true)
				r["good"][i]["to"] = wid
				c2["%s; good[%d] -> %s" % [w0, i, wid]] = r
		if good.size() > 1:
			var r := r0.duplicate(true)
			r["good"] = good.slice(0, good.size() - 1)
			c2["%s; last good left out" % w0] = r
		var arr := str(r0.get("arrive", ""))
		if arr != "":
			var room := m.room_of(str(m.waypoint(arr).get("sector", "")))
			for wid in _open_waypoints(CC, m, room):
				if wid != arr:
					var r := r0.duplicate(true)
					r["arrive"] = wid
					c2["%s; arrive -> %s" % [w0, wid]] = r
		stage.call("places", c2)
	print("  BEST %d: %s" % [best["n"], best["what"]])


static func _survey(CC: GDScript, map_id: String) -> void:
	var m: StoryMap = CC.map_of(map_id)
	var ids: Array = m.waypoints.keys()
	ids.sort()
	print("waypoint                 sector          x       z     yaw   centre/near-share at yaw-30 | yaw | yaw+30")
	for wid in ids:
		var w: Dictionary = m.waypoints[wid]
		var cells: Array = []
		for dy in [-30.0, 0.0, 30.0]:
			var c: Dictionary = CC.clearance(m, {"cam": Vector3(w["at"].x, float(m.sector(str(w["sector"]))["floor"]) + m.eye_height, w["at"].y), "yaw": float(w["yaw"]) + dy, "pitch": 0.0, "sector": w["sector"]})
			cells.append("%5.1f/%3d%%%s" % [minf(float(c["centre"]), 99.0), roundi(100.0 * float(c["share"])), "!" if CC.fails(c) else " "])
		print("%-24s %-12s %7.2f %7.2f %6.0f   %s" % [wid, w["sector"], w["at"].x, w["at"].y, float(w["yaw"]), " | ".join(cells)])


## Writes `body` between `<!-- clearance:<label> -->` and `<!-- /clearance:<label> -->` in the doc (added at the end when the markers are missing).
static func _write_doc(label: String, body: String) -> void:
	var path := ProjectSettings.globalize_path(DOC)
	var txt := FileAccess.get_file_as_string(path) if FileAccess.file_exists(path) else "# Camera clearance\n"
	var a := "<!-- clearance:%s -->" % label
	var b := "<!-- /clearance:%s -->" % label
	var block := "%s\n%s\n%s" % [a, body, b]
	var ia := txt.find(a)
	var ib := txt.find(b)
	if ia >= 0 and ib > ia:
		txt = txt.substr(0, ia) + block + txt.substr(ib + b.length())
	else:
		txt = txt.rstrip("\n") + "\n\n" + block + "\n"
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(txt)
	f.close()
