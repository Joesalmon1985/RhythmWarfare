extends SceneTree
## The touch-coverage audit (docs/parallel-development/coverage/baseline.md): how much of the visible world can the player touch, and for how much of the play time.
## Every scene of the main run and of the three paths is played on the virtual clock (perfect bot, no taps, an isolated save, no track scenes) and SAMPLED AT EVERY BEAT of active play. At each
## sample the hotspots really on show and selectable (RunPlay.hotspot_items, the list the taps use) are laid out with _HV.layout from the live camera exactly as RunPlay.hotspot_tap
## does (rects = true, the stage host's size), and the union of their touch regions (ring circle + touch rectangle, what HotspotView.hit accepts) is measured over the WORLD RECTANGLE.
##   godot --headless --path . -s tools/run/coverage_audit.gd -- [--run=main|gospel|squadron|ember|all] [--scene=<id filter>] [--aspect=16:9|20:9] [--pad=30|36|42] [--out=<file>]
## Prints "COVDEF {...}" (the definitions), then one "COV {...}" JSON line per scene (also appended to --out). tools/run/coverage_audit.py summarises the lines.
##
## ACTIVE PLAY (printed in COVDEF too): every beat k = 0, 1, 2 ... of the scene from its first downbeat (the count-in before it is not play), over ALL laps of the scene, up to the last lap's
## beat 60 (the last lap's beats 61 to 63 are the door walk / the world-change close: the camera walks to the doorway, the choice has committed, nothing is selectable: excluded). A sample where
## nothing is selectable counts as 0%. Not reached by this bot, so not in the samples: minigames, the Bassment (trials), cinematics (no tap starts any); if one were active the sample is dropped.
## WORLD RECTANGLE: the stage host (full width, above the pad strip) minus the HUD zones (the crowd meter and mix-stage blocks top left, the route-window bar along the stage's bottom edge).
## Rasterisation: exact in x (interval union per row), rows every 2 px in y (230 rows at 36% pads): within about 1% of the true union.

const PAD_SIZES: Array = [0.30, 0.36, 0.42]  # = Session.PAD_SIZES (an autoload cannot be named from a SceneTree script)
const STEP := 1.0 / 30.0
const ROW := 2.0
const PERSON_W := 0.6  # metres: a person's body width for the visual box (approximation; the height is _SC.HERO_M)
const SIGN_W := 0.8
const SIGN_H := 1.6
const NEAR_D := 0.4  # the layout's own "on screen" depth

# the game classes are loaded at runtime (after the autoloads exist): naming them here would compile story_stage.gd before Session is registered (7 SCRIPT ERROR lines)
var _HV: Variant = null
var _SP: Variant = null
var _CS: Variant = null
var _SC: Variant = null
var _RP: Variant = null
var _RPG: Variant = null
var _queue: Array = []
var _cur: Dictionary = {}
var _host: Control = null
var _scene: Node = null
var _frames := 0
var _out_path := ""
var _out: FileAccess = null
var _view := Vector2(1280, 720)
var _pad_idx := 1
var _aspect := "16:9"
# per scene
var _inited := false
var _t0 := 0.0
var _k := 0
var _idx0 := 0
var _hud_zones: Array = []
var _world := Vector2.ZERO
var _rows := 0
var _world_area := 0.0
var _things: Array = []
var _hs: Dictionary = {}
var _s: Dictionary = {}  # the sample arrays


func _init() -> void:
	OS.set_environment("RW_RUN_TRACKS", "0")
	var which := "all"
	var filt := ""
	for a in OS.get_cmdline_user_args():
		var s := str(a)
		if s.begins_with("--run="):
			which = s.substr(6)
		elif s.begins_with("--scene="):
			filt = s.substr(8)
		elif s.begins_with("--aspect="):
			_aspect = s.substr(9)
		elif s.begins_with("--pad="):
			_pad_idx = {"30": 0, "36": 1, "42": 2}.get(s.substr(6), 1)
		elif s.begins_with("--out="):
			_out_path = s.substr(6)
	_view = Vector2(1600, 720) if _aspect == "20:9" else Vector2(1280, 720)
	var runs: Array = ["main", "gospel", "squadron", "ember"] if which == "all" else Array(which.split(","))
	for r in runs:
		var path := "res://content/run/run.json" if r == "main" else "res://content/paths/%s/run.json" % r
		var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
		for n in (doc as Dictionary)["nodes"]:
			if filt != "" and not str(n["id"]).contains(filt):
				continue
			_queue.append({"path": "" if r == "main" else r, "run": r, "scene": str(n["id"])})
	if _out_path != "":
		DirAccess.make_dir_recursive_absolute(_out_path.get_base_dir())
		_out = FileAccess.open(_out_path, FileAccess.WRITE)
	var pad_share: float = PAD_SIZES[_pad_idx]
	print("COVDEF " + JSON.stringify({"aspect": _aspect, "view": [_view.x, _view.y], "pad_pct": int(round(pad_share * 100.0)), "row_px": ROW,
		"active_play": "beats k=0.. of the scene from its first downbeat, all laps, to the last lap's beat 60; count-in, the last lap's beats 61-63 (door walk), minigames, trials excluded; nothing selectable = 0%",
		"world": "stage host (full width, above the pads) minus HUD zones (crowd meter + mix-stage blocks top left; route-window bar on the stage's bottom edge)",
		"touch": "union of ring circle + touch_rect of every hotspot in RunPlay.hotspot_items (not committed), as HotspotView.layout(rects=true) places them and HotspotView.hit accepts them",
		"choice": "touch union of hotspots whose on_success.route is non-empty and not the scene itself",
		"visual": "vis_hs: union of the drawn object boxes of the hotspots on show (map thing quad, person 0.6 x 1.7 m, staged door width_m x height_m); vis_all: all billboard things (opaque ones) + all present people of the stage; soft glows, set pieces hidden, props of the choice art not included"}))


func _process(_d: float) -> bool:
	_frames += 1
	if _HV == null:
		_HV = load("res://src/run/hotspot_view.gd")
		_SP = load("res://src/story/world/story_projector.gd")
		_CS = load("res://src/run/choice_staging.gd")
		_SC = load("res://src/story/story_crowd.gd")
		_RP = load("res://src/run/run_passage.gd")
		_RPG = load("res://src/run/run_progress.gd")
	if _scene == null:
		if _queue.is_empty():
			if _out != null:
				_out.close()
			quit(0)
			return false
		_start(_queue.pop_front())
		return false
	if _frames < 4 or not _scene.stages.has(_scene.active_world):
		return false
	var eng: Object = _scene.engine
	if not _inited:
		_init_scene()
	var target: float = _t0 + float(_k) * eng.beat_s
	var t: float = _scene._vt
	while t < target - 1.0e-9:
		t = minf(t + STEP, target)
		_scene._vt = t
		_scene._step_virtual(t)
	var pb: float = eng.phase_beat_at(t)
	var done: bool = eng.scene_index() != _idx0 or (eng.lap >= eng.laps and pb >= 64.0 - _RP.DOOR_BEATS - 0.001) or _k > 64 * (eng.laps + 4) + 10
	if done:
		_finish(eng, _k > 64 * (eng.laps + 4) + 10)
		return false
	_sample(eng, t)
	_k += 1
	return false


func _start(q: Dictionary) -> void:
	var session: Node = root.get_node("Session")
	session.set("run_progress", _RPG.load_data("user://coverage_audit_save.json", "user://none.json"))
	session.set("pad_size", _pad_idx)
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_TAPS", "none")
	OS.set_environment("RW_RUN_START", str(q["scene"]))
	OS.set_environment("RW_RUN_PATH", str(q["path"]))
	session.set("run_start_node", "")
	_host = Control.new()
	_host.size = _view
	root.add_child(_host)
	_scene = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	_host.add_child(_scene)
	_scene.size = _view
	_cur = {"run": q["run"], "scene": q["scene"], "aspect": _aspect, "pad_pct": int(round(float(PAD_SIZES[_pad_idx]) * 100.0))}
	_inited = false
	_frames = 0


func _init_scene() -> void:
	_inited = true
	var eng: Object = _scene.engine
	var host: Control = _scene._stage_host
	_world = host.size
	_rows = int(floor(_world.y / ROW))
	_t0 = float(eng.scene_t0)
	_k = maxi(0, int(ceil((0.0 - _t0) / eng.beat_s - 1.0e-9)))
	_idx0 = eng.scene_index()
	_hs = {}
	_s = {"k": [], "lap": [], "n": [], "touch": [], "choice": [], "vis_hs": [], "vis_all": [], "tgt": []}
	var sz: Vector2 = _scene.size
	var fs := int(clampf(sz.y * 0.045, 14.0, 28.0))  # RunHud._draw's own numbers
	var bar := Rect2(14.0, 14.0 + fs * 1.1, minf(sz.x * 0.28, 320.0), fs * 0.55)
	var py := bar.end.y + fs * 0.7
	var sh: float = _world.y
	var bar_h := maxf(sh * 0.014, 4.0)
	_hud_zones = [Rect2(bar.position, Vector2(bar.size.x, py + fs * 0.42 - bar.position.y)), Rect2(sz.x * 0.025, sh - bar_h - 2.0, sz.x * 0.95, bar_h)]
	_world_area = _covered([], true, true)
	var st: Object = _scene.stages[_scene.active_world]["stage"]
	_things = []
	var nodes := {}
	var aspect_known := 0
	if st.world != null:
		for th in st.world._thing_nodes:
			nodes[str((th["thing"] as Dictionary)["id"])] = th
	for t in st.map.things:
		var tid := str(t["id"])
		var h := float(t.get("size", 1.0))
		var w := h
		var soft := false
		var node: Variant = null
		if nodes.has(tid):
			var mi: MeshInstance3D = nodes[tid]["node"]
			node = mi
			if mi.mesh is QuadMesh:
				w = (mi.mesh as QuadMesh).size.x
				aspect_known += 1
			var mat := mi.material_override as BaseMaterial3D
			soft = mat != null and mat.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA
		var fl := float(st.map.sector(str(t["sector"])).get("floor", 0.0))
		var at: Vector2 = t["at"]
		_things.append({"id": tid, "x": at.x, "z": at.y, "yc": fl + float(t.get("y", h * 0.5)), "w": w, "h": h, "soft": soft, "node": node})
	_cur["things"] = [st.map.things.size(), aspect_known]
	_cur["hud"] = _hud_zones.map(func(r: Rect2) -> Array: return [snappedf(r.position.x, 0.1), snappedf(r.position.y, 0.1), snappedf(r.size.x, 0.1), snappedf(r.size.y, 0.1)])
	_cur["world"] = [_world.x, _world.y]
	_cur["world_area"] = int(_world_area)
	_cur["laps"] = eng.laps
	_cur["t0"] = snappedf(_t0, 0.001)


# --- measuring ---------------------------------------------------------------------------------------------------------------

func _sample(eng: Object, t: float) -> void:
	var run: Node = _scene
	var st: Object = run.stages[run.active_world]["stage"]
	if run.trial_state != "" or run.minigames.active():
		_cur["dropped"] = int(_cur.get("dropped", 0)) + 1
		return
	var items: Array = (run.hotspot_items() as Array).filter(func(e: Dictionary) -> bool: return str(e["state"]) != "committed")
	var pose: Dictionary = run._exit_pose()
	var lay: Array = []
	if not pose.is_empty() and not items.is_empty():
		lay = _HV.layout(items, st.map, st.crowds, pose, _world, true)
	var all_shapes: Array = []
	var choice_shapes: Array = []
	var hs_boxes: Array = []
	var tgt_min := INF
	var pads: Array = []
	var host: Control = run._stage_host
	var pr: Dictionary = run.pad_view.button_rects()
	for p in pr:
		var r: Rect2 = pr[p]
		pads.append(Rect2(r.position - host.global_position, r.size))
	for e in lay:
		var h: Dictionary = e["hotspot"]
		var id := str(e["id"])
		var shapes := _shapes_of(e)
		all_shapes.append_array(shapes)
		var route := str((h.get("on_success", {}) as Dictionary).get("route", ""))
		var is_choice := route != "" and route != str(eng.node_id)
		if is_choice:
			choice_shapes.append_array(shapes)
		var rec: Dictionary = _hs.get(id, {})
		if rec.is_empty():
			var an: Dictionary = h["anchor"]
			rec = {"kind": str(h.get("kind", "")), "anchor": str(an.keys()[0]) if not an.is_empty() else "", "arch": _CS.archetype_of(h), "choice": is_choice, "route": route, "n": 0, "edge": 0, "noobj": 0,
				"ratio": 0.0, "ratio_lin": 0.0, "tgt": INF, "pad": 0, "tarea": 0.0, "varea": 0.0, "radius_m": float(h["radius_m"])}
		rec["n"] = int(rec["n"]) + 1
		var tg := _target_px(e)
		rec["tgt"] = minf(float(rec["tgt"]), tg)
		tgt_min = minf(tgt_min, tg)
		for pad in pads:
			if _hits_rect(e, pad):
				rec["pad"] = int(rec["pad"]) + 1
				break
		if bool(e["edge"]):
			rec["edge"] = int(rec["edge"]) + 1
		else:
			var box := _hotspot_box(h, e, st, pose)
			if box.get_area() <= 1.0:
				rec["noobj"] = int(rec["noobj"]) + 1
			else:
				hs_boxes.append(box)
				var ta := _covered(shapes, false)
				var ratio := ta / box.get_area()
				if ratio > float(rec["ratio"]):
					rec["ratio"] = ratio
					rec["tarea"] = ta
					rec["varea"] = box.get_area()
				var lin := 0.0
				var tb := _bounds_of(shapes)
				lin = maxf(tb.size.x / maxf(box.size.x, 1.0), tb.size.y / maxf(box.size.y, 1.0))
				rec["ratio_lin"] = maxf(float(rec["ratio_lin"]), lin)
		_hs[id] = rec
	var vis_all: Array = []
	if not pose.is_empty():
		vis_all = _all_boxes(st, pose)
	_s["k"].append(_k)
	_s["lap"].append(eng.lap)
	_s["n"].append(lay.size())
	_s["touch"].append(int(round(_covered(all_shapes, true) / _world_area * 1000.0)))
	_s["choice"].append(int(round(_covered(choice_shapes, true) / _world_area * 1000.0)))
	_s["vis_hs"].append(int(round(_covered(_rect_shapes(hs_boxes), true) / _world_area * 1000.0)))
	_s["vis_all"].append(int(round(_covered(_rect_shapes(vis_all), true) / _world_area * 1000.0)))
	_s["tgt"].append(int(round(tgt_min)) if tgt_min < INF else -1)


func _finish(eng: Object, guard: bool) -> void:
	_cur["samples"] = (_s["k"] as Array).size()
	_cur["last_k"] = _k - 1
	_cur["guard"] = guard
	for key in _s:
		_cur[key] = _s[key]
	var hs := {}
	for id in _hs:
		var r: Dictionary = _hs[id]
		hs[id] = {"kind": r["kind"], "anchor": r["anchor"], "arch": r["arch"], "choice": r["choice"], "route": r["route"], "n": r["n"], "edge": r["edge"], "noobj": r["noobj"], "pad": r["pad"],
			"ratio": snappedf(float(r["ratio"]), 0.01), "ratio_lin": snappedf(float(r["ratio_lin"]), 0.01), "tgt": snappedf(float(r["tgt"]), 0.1) if float(r["tgt"]) < INF else -1.0,
			"tarea": int(r["tarea"]), "varea": int(r["varea"]), "radius_m": r["radius_m"]}
	_cur["hs"] = hs
	var line := JSON.stringify(_cur)
	print("COV " + line)
	if _out != null:
		_out.store_line(line)
		_out.flush()
	_host.queue_free()
	_scene = null
	_host = null


# rows: the union length of the shapes (circles {c, r} and rects {rect}) in px^2, rows every ROW px; `use_hud`: HUD zones taken off (and with no shapes: the world area itself)
func _covered(shapes: Array, use_hud: bool, full := false) -> float:
	var total := 0.0
	var zones: Array = _hud_zones if use_hud else []
	if shapes.is_empty() and not full:
		return 0.0
	for i in _rows:
		var y := (float(i) + 0.5) * ROW
		if full:
			total += _row_len(Vector2(0.0, _world.x), y, zones) * ROW
			continue
		var iv: Array = []
		for s in shapes:
			if s.has("rect"):
				var r: Rect2 = s["rect"]
				if y >= r.position.y and y < r.end.y:
					iv.append(Vector2(maxf(r.position.x, 0.0), minf(r.end.x, _world.x)))
			else:
				var c: Vector2 = s["c"]
				var rad: float = s["r"]
				var dy := y - c.y
				if absf(dy) < rad:
					var hw := sqrt(rad * rad - dy * dy)
					iv.append(Vector2(maxf(c.x - hw, 0.0), minf(c.x + hw, _world.x)))
		if iv.is_empty():
			continue
		iv.sort_custom(func(a: Vector2, b: Vector2) -> bool: return a.x < b.x)
		var a0: float = (iv[0] as Vector2).x
		var b0: float = (iv[0] as Vector2).y
		for j in range(1, iv.size()):
			var v: Vector2 = iv[j]
			if v.x <= b0:
				b0 = maxf(b0, v.y)
			else:
				total += _row_len(Vector2(a0, b0), y, zones) * ROW
				a0 = v.x
				b0 = v.y
		total += _row_len(Vector2(a0, b0), y, zones) * ROW
	return total


# the length of the interval a..b outside the HUD zones that cover row y (the zones do not overlap each other)
func _row_len(iv: Vector2, y: float, zones: Array) -> float:
	var len := maxf(iv.y - iv.x, 0.0)
	for z in zones:
		var r: Rect2 = z
		if y >= r.position.y and y < r.end.y:
			len -= maxf(minf(iv.y, r.end.x) - maxf(iv.x, r.position.x), 0.0)
	return maxf(len, 0.0)


func _shapes_of(e: Dictionary) -> Array:
	var out: Array = [{"c": e["centre"], "r": float(e["radius_px"])}]
	if e.has("touch_rect"):
		var r: Rect2 = e["touch_rect"]
		if r.size.x > 0.0 and r.size.y > 0.0:
			out.append({"rect": r})
	return out


func _rect_shapes(boxes: Array) -> Array:
	var out: Array = []
	for b in boxes:
		out.append({"rect": b})
	return out


func _bounds_of(shapes: Array) -> Rect2:
	var rb := Rect2()
	var first := true
	for s in shapes:
		var r: Rect2
		if s.has("rect"):
			r = s["rect"]
		else:
			var c: Vector2 = s["c"]
			var rad: float = s["r"]
			r = Rect2(c - Vector2(rad, rad), Vector2(rad, rad) * 2.0)
		rb = r if first else rb.merge(r)
		first = false
	return rb


## The side of the target: the larger of the ring's diameter and the shorter side of the touch rectangle (a tap can land in either).
func _target_px(e: Dictionary) -> float:
	var d := 2.0 * float(e["radius_px"])
	if e.has("touch_rect"):
		var r: Rect2 = e["touch_rect"]
		d = maxf(d, minf(r.size.x, r.size.y))
	return d


func _hits_rect(e: Dictionary, pad: Rect2) -> bool:
	var c: Vector2 = e["centre"]
	var near := Vector2(clampf(c.x, pad.position.x, pad.end.x), clampf(c.y, pad.position.y, pad.end.y))
	if near.distance_to(c) < float(e["radius_px"]) - 0.5:
		return true
	if e.has("touch_rect"):
		var r: Rect2 = e["touch_rect"]
		var ov := r.intersection(pad)
		return ov.size.x > 0.5 and ov.size.y > 0.5
	return false


# --- visual bounds -----------------------------------------------------------------------------------------------------------

## A box standing at (x, z) from y0 up to y1 metres, w metres wide, on screen, clipped to the view; empty when behind the camera or out of view.
func _stand_box(x: float, z: float, y0: float, y1: float, w: float, pose: Dictionary) -> Rect2:
	var p0: Dictionary = _SP.project(Vector3(x, y0, z), pose, _world)
	var p1: Dictionary = _SP.project(Vector3(x, y1, z), pose, _world)
	if float(p0["depth"]) < NEAR_D or float(p1["depth"]) < NEAR_D:
		return Rect2()
	var sc := float(p0["scale"])
	var a: Vector2 = p0["screen"]
	var b: Vector2 = p1["screen"]
	var r := Rect2(Vector2(a.x - w * sc * 0.5, minf(a.y, b.y)), Vector2(w * sc, absf(a.y - b.y)))
	return r.intersection(Rect2(Vector2.ZERO, _world))


func _thing_box(th: Dictionary, pose: Dictionary) -> Rect2:
	var h: float = th["h"]
	var yc: float = th["yc"]
	return _stand_box(float(th["x"]), float(th["z"]), yc - h * 0.5, yc + h * 0.5, float(th["w"]), pose)


func _person_box(a: Dictionary, st: Object, pose: Dictionary) -> Rect2:
	var p: Vector2 = a["pos"]
	var fl := float(st.map.sector(str(a.get("sec", ""))).get("floor", 0.0))
	return _stand_box(p.x, p.y, fl, fl + _SC.HERO_M, PERSON_W, pose)


## The drawn object of a hotspot: the person it anchors on, the thing of the map, the staged door (width_m x height_m) of an exit, a sign post; empty for an anchor with nothing drawn on it
## (a waypoint or an empty spot with no staged door, a light).
func _hotspot_box(h: Dictionary, e: Dictionary, st: Object, pose: Dictionary) -> Rect2:
	var an: Dictionary = h["anchor"]
	var stg: Dictionary = _CS.of(h)
	var w: Vector3 = e["world"]
	var gy: float = e["ground_y"]
	if str(stg.get("archetype", "")) == "door":
		match str(stg.get("door", "drawn")):
			"drawn":
				return _stand_box(w.x, w.z, gy, gy + float(stg.get("height_m", 2.4)), float(stg.get("width_m", 1.2)), pose)
			"sign":
				return _stand_box(w.x, w.z, gy, gy + SIGN_H, SIGN_W, pose)
			"none", "pieces":
				return Rect2()
	if an.has("actor"):
		for rid in st.crowds:
			var c: Object = st.crowds[rid]
			if c.actors.has(str(an["actor"])):
				return _person_box(c.actors[str(an["actor"])], st, pose)
		return Rect2()
	if an.has("thing"):
		for th in _things:
			if str(th["id"]) == str(an["thing"]):
				return _thing_box(th, pose)
	return Rect2()


func _all_boxes(st: Object, pose: Dictionary) -> Array:
	var out: Array = []
	for th in _things:
		if bool(th["soft"]):
			continue
		var nd: Variant = th["node"]
		if nd != null and is_instance_valid(nd) and not (nd as Node3D).visible:
			continue
		var b := _thing_box(th, pose)
		if b.get_area() > 1.0:
			out.append(b)
	for rid in st.crowds:
		var c: Object = st.crowds[rid]
		for aid in c.actors:
			var a: Dictionary = c.actors[aid]
			if not bool(a.get("present", true)):
				continue
			var b := _person_box(a, st, pose)
			if b.get_area() > 1.0:
				out.append(b)
	return out
