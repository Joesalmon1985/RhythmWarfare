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
	print(tab)
	print("")
	print(sm)
	print("camera clearance: %d failing poses, %d scene entries, step %.2f beats, %.1f s" % [total, rows.size(), step, (Time.get_ticks_msec() - t_start) / 1000.0])
	if dump_path != "":
		var f := FileAccess.open(dump_path, FileAccess.WRITE)
		f.store_string("\n".join(dump.slice(0)) + "\n")
		f.close()
	if doc != "":
		_write_doc(doc, "%s\n\n%s\n\n%d failing poses over %d scene entries (step %.2f beats)." % [sm, tab, total, rows.size(), step])
	quit(1 if total > 0 else 0)


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
