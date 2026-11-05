extends SceneTree
## The choice-clarity audit's measuring half (docs/CHOICE_CLARITY.md): every branching scene of the main run and of the paths is played on the virtual clock (perfect bot, no taps, an
## isolated save) and, at a few beats, every one of its hotspots (whatever its flags) is placed with HotspotView.layout from the camera the player really has: on screen or an edge beacon,
## how big its thing is on screen, and whether its person is in the room. One JSON object per scene on stdout, prefixed "AUDIT ".
##   godot --headless --path . -s tools/run/choice_audit.gd -- [main|gospel|squadron|ember|all] [scene id filter]
## tools/run/choice_audit.py reads the lines and writes the audit tables.

const BEATS := [4.0, 30.0, 50.0, 56.0]
const VIEW := Vector2(1152, 648)

var _queue: Array = []  # [{path, scene}]
var _cur: Dictionary = {}
var _host: Control = null
var _scene: Node = null
var _beat_i := 0
var _rows: Dictionary = {}
var _frames := 0


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var which := str(args[0]) if args.size() > 0 else "all"
	var filt := str(args[1]) if args.size() > 1 else ""
	var runs := ["main", "gospel", "squadron", "ember"] if which == "all" else [which]
	for r in runs:
		var path := "res://content/run/run.json" if r == "main" else "res://content/paths/%s/run.json" % r
		var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
		for n in (doc as Dictionary)["nodes"]:
			if filt != "" and not str(n["id"]).contains(filt):
				continue
			_queue.append({"path": "" if r == "main" else r, "run": r, "scene": str(n["id"])})


func _process(_d: float) -> bool:
	_frames += 1
	if _scene == null:
		if _queue.is_empty():
			quit(0)
			return false
		_start(_queue.pop_front())
		return false
	if _frames < 3:  # (the scene builds its stage in its first frames)
		return false
	var beat_s: float = _scene.engine.beat_s
	var target := float(BEATS[_beat_i]) * beat_s
	var t: float = _scene._vt
	while t < target:
		t += 1.0 / 30.0
		_scene._vt = t
		_scene._step_virtual(t)
	_measure(str(BEATS[_beat_i]))
	_beat_i += 1
	if _beat_i >= BEATS.size():
		print("AUDIT " + JSON.stringify(_cur))
		_host.queue_free()
		_scene = null
		_host = null
	return false


func _start(q: Dictionary) -> void:
	var session: Node = root.get_node("Session")
	session.set("run_progress", RunProgress.load_data("user://choice_audit_save.json", "user://none.json"))
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_TAPS", "none")
	OS.set_environment("RW_RUN_START", str(q["scene"]))
	OS.set_environment("RW_RUN_PATH", str(q["path"]))
	session.set("run_start_node", "")
	_host = Control.new()
	_host.size = VIEW
	root.add_child(_host)
	_scene = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	_host.add_child(_scene)
	_scene.size = VIEW
	_cur = {"run": q["run"], "scene": q["scene"], "at": {}}
	_beat_i = 0
	_frames = 0


func _measure(label: String) -> void:
	var out := {"node": str(_scene.engine.node_id), "hotspots": {}, "beat": snappedf(float(_scene.engine.phase_beat_at(_scene._vt)), 0.1), "block": int(_scene.engine.block), "window": bool(_scene.engine.window_open)}
	if not _scene.stages.has(_scene.active_world):
		_cur["at"][label] = out
		return
	var st: StoryStage = _scene.stages[_scene.active_world]["stage"]
	var pose: Dictionary = _scene._exit_pose()
	var hv: HotspotView = _scene.stages[_scene.active_world].get("hotspot_view", null)
	var view: Vector2 = hv.size if hv != null and hv.size.x > 1.0 else VIEW
	var entries: Array = []
	for h in _scene.data.hotspots_of(str(_cur["scene"])):
		entries.append({"hotspot": h, "state": "available"})
	var lay := HotspotView.layout(entries, st.map, st.crowds, pose, view)
	var placed := {}
	for e in lay:
		placed[str(e["id"])] = e
	for en in entries:
		var h: Dictionary = en["hotspot"]
		var id := str(h["id"])
		var r := {"resolved": placed.has(id)}
		if placed.has(id):
			var e: Dictionary = placed[id]
			r["edge"] = bool(e["edge"])
			r["px_per_m"] = snappedf(float(e["scale"]), 0.1) if not bool(e["edge"]) else 0.0
			r["depth_m"] = snappedf(float(e["depth"]), 0.1)
			r["x"] = snappedf((e["centre"] as Vector2).x / view.x, 0.01)
		var aid := RunActing.actor_of(h)
		if aid != "":
			var present := false
			for rid in st.crowds:
				var c: StoryCrowd = st.crowds[rid]
				if c.actors.has(aid):
					present = true
			r["actor_present"] = present
		out["hotspots"][id] = r
	out["shown"] = (_scene.hotspots.shown(_scene.engine.block, _scene.engine.window_open) as Array).map(func(x: Dictionary) -> String: return str(x["id"]))
	_cur["at"][label] = out
