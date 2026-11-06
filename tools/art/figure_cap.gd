extends SceneTree
## The figure size cap check (docs/art/STYLE_GUIDE.md section 7, audit F1(b) and F8): no person is drawn larger than 1.25 internal pixels per pixel of the finest level of
## their sheet. Every scene of the main run and of the three paths is played on the virtual clock (perfect bot, default exits, an isolated save, no track scenes) from its
## start to the first moment of the next scene, and EVERY STEP (1/30 s of song time) every person drawn by every crowd of the active stage is measured:
##   mag = |node scale| x rig height / sheet h0 x min(sheet lods)      (internal pixels per sheet pixel; the same number StoryCrowd keeps as `mag`)
## The measure reads the drawn nodes only, so it works on any version of StoryCrowd (before and after the cap). Heralds and the card table are props, not counted.
##   godot --headless --path . -s tools/art/figure_cap.gd -- [--run=main|gospel|squadron|ember|all] [--scene=<id filter>] [--cap=1.25] [--out=<file>]
## Prints one "FIGCAP {...}" JSON line per scene: samples, person-frames drawn, the largest mag, person-frames over the cap, a histogram of mag (<=1, 1-1.25, 1.25-2, 2-3, >3)
## and, when the crowd keeps them, the frames' sums of people held back at the cap and dissolved inside it. Then "FIGCAP_TOTAL {...}". Exit code 1 when anyone was over the cap.

const STEP := 1.0 / 30.0
const BANDS: Array = [1.0, 1.25, 2.0, 3.0]

var _queue: Array = []
var _cur: Dictionary = {}
var _host: Control = null
var _scene: Node = null
var _frames := 0
var _out: FileAccess = null
var _cap := 1.25
var _inited := false
var _idx0 := 0
var _t := 0.0
var _steps := 0
var _total := {"scenes": 0, "drawn": 0, "over": 0, "max": 0.0, "hist": [0, 0, 0, 0, 0], "held": 0, "gone": 0, "worst": ""}


func _init() -> void:
	OS.set_environment("RW_RUN_TRACKS", "0")
	var which := "all"
	var filt := ""
	var out_path := ""
	for a in OS.get_cmdline_user_args():
		var s := str(a)
		if s.begins_with("--run="):
			which = s.substr(6)
		elif s.begins_with("--scene="):
			filt = s.substr(8)
		elif s.begins_with("--cap="):
			_cap = float(s.substr(6))
		elif s.begins_with("--out="):
			out_path = s.substr(6)
	var runs: Array = ["main", "gospel", "squadron", "ember"] if which == "all" else Array(which.split(","))
	for r in runs:
		var path := "res://content/run/run.json" if r == "main" else "res://content/paths/%s/run.json" % r
		var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
		for n in (doc as Dictionary)["nodes"]:
			if filt != "" and not str(n["id"]).contains(filt):
				continue
			_queue.append({"path": "" if r == "main" else r, "run": r, "scene": str(n["id"])})
	if out_path != "":
		DirAccess.make_dir_recursive_absolute(out_path.get_base_dir())
		_out = FileAccess.open(out_path, FileAccess.WRITE)


func _process(_d: float) -> bool:
	_frames += 1
	if _scene == null:
		if _queue.is_empty():
			print("FIGCAP_TOTAL " + JSON.stringify(_total))
			if _out != null:
				_out.store_line(JSON.stringify(_total))
				_out.close()
			quit(1 if int(_total["over"]) > 0 else 0)
			return false
		_start(_queue.pop_front())
		return false
	if _frames < 4 or not _scene.stages.has(_scene.active_world):
		return false
	var eng: Object = _scene.engine
	if not _inited:
		_inited = true
		_idx0 = eng.scene_index()
		_t = maxf(float(eng.scene_t0) - 0.5, float(_scene._vt))
	for i in 20:  # 20 steps a frame
		_t += STEP
		_scene._vt = _t
		_scene._step_virtual(_t)
		_steps += 1
		if eng.scene_index() != _idx0 or _steps > 30 * 60 * 6:
			_finish()
			return false
		_sample()
	return false


func _start(q: Dictionary) -> void:
	var session: Node = root.get_node("Session")
	var rpg: Variant = load("res://src/run/run_progress.gd")
	session.set("run_progress", rpg.load_data("user://figure_cap_save.json", "user://none.json"))
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_TAPS", "none")
	OS.set_environment("RW_RUN_START", str(q["scene"]))
	OS.set_environment("RW_RUN_PATH", str(q["path"]))
	session.set("run_start_node", "")
	_host = Control.new()
	_host.size = Vector2(1280, 720)
	root.add_child(_host)
	_scene = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	_host.add_child(_scene)
	_scene.size = Vector2(1280, 720)
	_cur = {"run": q["run"], "scene": q["scene"], "samples": 0, "drawn": 0, "over": 0, "max": 0.0, "max_at": -1.0, "max_who": "", "hist": [0, 0, 0, 0, 0], "held": 0, "gone": 0}
	_inited = false
	_frames = 0
	_steps = 0


func _sample() -> void:
	var run: Node = _scene
	if run.trial_state != "":
		return
	var st: Object = run.stages[run.active_world]["stage"]
	_cur["samples"] = int(_cur["samples"]) + 1
	for cid in st.crowds:
		var crowd: Object = st.crowds[cid]
		if "cap_held" in crowd:
			_cur["held"] = int(_cur["held"]) + int(crowd.cap_held)
			_cur["gone"] = int(_cur["gone"]) + int(crowd.cap_gone)
		for id in crowd.actors:
			var c: Object = crowd.actors[id]["node"]
			if not c.visible or not c.is_visible_in_tree():
				continue
			var ppl: Object = c.people
			var h0 := 112.0
			var lmin := 1.0
			if ppl != null:
				h0 = float(ppl.h0)
				for l in ppl.lods:
					lmin = minf(lmin, float(l))
			var mag: float = absf(c.scale.x) * float(c.rig.get("height", 260.0)) / h0 * lmin
			_cur["drawn"] = int(_cur["drawn"]) + 1
			var b := 0
			while b < BANDS.size() and mag > float(BANDS[b]) + 1.0e-3:
				b += 1
			_cur["hist"][b] = int(_cur["hist"][b]) + 1
			if mag > _cap + 1.0e-3:
				_cur["over"] = int(_cur["over"]) + 1
			if mag > float(_cur["max"]):
				_cur["max"] = mag
				_cur["max_at"] = snappedf(_t, 0.01)
				_cur["max_who"] = str(id)


func _finish() -> void:
	_cur["max"] = snappedf(float(_cur["max"]), 0.001)
	var line := JSON.stringify(_cur)
	print("FIGCAP " + line)
	if _out != null:
		_out.store_line(line)
		_out.flush()
	_total["scenes"] = int(_total["scenes"]) + 1
	for k in ["drawn", "over", "held", "gone"]:
		_total[k] = int(_total[k]) + int(_cur[k])
	for i in 5:
		_total["hist"][i] = int(_total["hist"][i]) + int(_cur["hist"][i])
	if float(_cur["max"]) > float(_total["max"]):
		_total["max"] = _cur["max"]
		_total["worst"] = "%s/%s %s at %.2f s" % [_cur["run"], _cur["scene"], _cur["max_who"], float(_cur["max_at"])]
	_host.queue_free()
	_scene = null
	_host = null
