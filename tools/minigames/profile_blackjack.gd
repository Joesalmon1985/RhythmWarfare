extends SceneTree
## The blackjack table's per-frame cost, measured: the REAL BlackjackActivity and BlackjackView in a SubViewport (640 x 230, and 320 x 115 for the low-detail moments), driven through
## representative moments of a seated hand, a few hundred frames each, then a compact table and quit. Needs a window (not --headless):
##   godot --path . --disable-vsync --resolution 640x230 -s tools/minigames/profile_blackjack.gd [-- <frames per moment> [<moment name filter>]]
## Per moment it reports, over the rendered frames (the first few of each moment skipped as warm-up):
##   draw   the view's layers' drawing (the picture's GDScript drawing, only for the layers redrawn that frame; the whole picture for a view drawn in one piece), microseconds, mean and p95
##   proc   the view's `_process` (fetch the snapshot, pose, prepare every layer's spec and queue the changed ones), microseconds, mean; it includes `state()`
##   state  the activity's `state()` alone, microseconds, mean
##   upd    the activity's `update(t)`, microseconds, mean
##   rcpu   the SubViewport's measured render time on the CPU (the renderer walking the canvas commands), milliseconds, mean
##   calls / prims / objs   Performance RENDER_TOTAL_DRAW_CALLS_IN_FRAME, RENDER_TOTAL_PRIMITIVES_IN_FRAME and RENDER_TOTAL_OBJECTS_IN_FRAME, mean
##   mem    the net change of static memory across the drawing (bytes, mean): what a frame's drawing leaves allocated (the canvas commands it recorded)
## Then, per moment, the five layers that cost most: mean microseconds per frame and the share of frames that redrew them.
## Song time moves by a fixed step per frame inside each moment (the moment's span over the frame count), so the same arguments give the same pictures.
## The timing wraps the view from outside (its drawing callable and its snapshot callable), so the game code carries no profiling switches.

const BEAT := 60.0 / 174.0
const WARMUP := 8

## name, size, seed, wallet (pence), taps {beat: target}, wobble [[beat, level]], fall beat (-1 none), from and to (beats after sitting), reduced, high contrast.
const MOMENTS := [
	{"name": "sitting", "seed": 3, "from": 0.2, "to": 1.4},
	{"name": "pockets_money", "seed": 3, "from": 2.0, "to": 4.0},
	{"name": "await_bet", "seed": 3, "from": 4.1, "to": 4.95},
	{"name": "bet_flight", "seed": 3, "taps": {5.0: "bet"}, "from": 5.0, "to": 6.5},
	{"name": "dealing", "seed": 3, "taps": {5.0: "bet"}, "from": 6.5, "to": 9.4},
	{"name": "player_turn", "seed": 3, "taps": {5.0: "bet"}, "from": 9.6, "to": 12.9},
	{"name": "others", "seed": 3, "taps": {5.0: "bet", 13.0: "hand"}, "from": 13.0, "to": 17.0},
	{"name": "settle_pay", "seed": 3, "taps": {5.0: "bet", 13.0: "hand"}, "from": 21.6, "to": 23.6},
	{"name": "loss_sweep", "seed": 5, "taps": {5.0: "bet", 13.0: "hand"}, "from": 23.6, "to": 25.6},
	{"name": "broke", "seed": 3, "wallet": 300, "from": 4.2, "to": 7.0},
	{"name": "wobble", "seed": 3, "taps": {5.0: "bet"}, "wobble": [[9.0, 1]], "from": 10.0, "to": 13.0},
	{"name": "fall", "seed": 3, "taps": {5.0: "bet"}, "fall": 10.0, "from": 10.0, "to": 13.5},
	{"name": "leaving", "seed": 3, "taps": {5.0: "bet", 13.0: "hand", 27.0: "exit"}, "from": 27.0, "to": 30.0},
	{"name": "low_await_bet", "size": Vector2(320, 115), "seed": 3, "from": 4.1, "to": 4.95},
	{"name": "low_player_turn", "size": Vector2(320, 115), "seed": 3, "taps": {5.0: "bet"}, "from": 9.6, "to": 12.9},
	{"name": "low_settle_pay", "size": Vector2(320, 115), "seed": 3, "taps": {5.0: "bet", 13.0: "hand"}, "from": 21.6, "to": 23.6},
]

var _frames := 300
var _filter := ""
var _moments: Array = []
var _mi := -1
var _i := 0
var _sub: SubViewport
var _view: BlackjackView
var _activity: BlackjackActivity
var _m: Dictionary = {}
var _t := 0.0
var _done_taps: Dictionary = {}
var _samples: Dictionary = {}
var _rows: Array = []
var _draw_us := 0
var _state_us := 0
var _mem := 0
var _pending := false
var _per_layer: Dictionary = {}  # layer name -> [microseconds, redraws] over the moment


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() >= 1:
		_frames = maxi(20, int(args[0]))
	if args.size() >= 2:
		_filter = args[1]
	for m: Dictionary in MOMENTS:
		if _filter == "" or str(m["name"]).contains(_filter):
			_moments.append(m)
	_sub = SubViewport.new()
	_sub.transparent_bg = false
	_sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(_sub)
	var show := TextureRect.new()
	show.texture = _sub.get_texture()
	root.add_child(show)
	RenderingServer.viewport_set_measure_render_time(_sub.get_viewport_rid(), true)


func _process(_delta: float) -> bool:
	if _pending:
		_collect()
	if _mi < 0 or _i >= _frames:
		if _mi >= 0:
			_finish_moment()
		_mi += 1
		if _mi >= _moments.size():
			_print_table()
			quit(0)
			return false
		_start_moment(_moments[_mi])
	_step_frame()
	return false


func _start_moment(m: Dictionary) -> void:
	_m = m
	_i = 0
	_done_taps = {}
	_per_layer = {}
	_samples = {"draw": [], "proc": [], "state": [], "upd": [], "rcpu": [], "calls": [], "prims": [], "objs": [], "mem": []}
	if _view != null:
		_view.queue_free()
	var size: Vector2 = m.get("size", Vector2(640, 230))
	_sub.size = Vector2i(size)
	var wallet := RunWallet.new()
	if m.has("wallet"):
		wallet.spend(wallet.balance_pence())
		wallet.add(int(m["wallet"]))
	var cfg: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/blackjack.json"))
	_activity = BlackjackActivity.new()
	_activity.setup({"wallet": wallet, "seed": int(m.get("seed", 3)), "beat_s": BEAT, "config": cfg})
	_activity.begin(0.0)
	_view = _activity.make_view() as BlackjackView
	_view.now_fn = func() -> float: return _t
	_view.state_fn = func() -> Dictionary:
		var s0 := Time.get_ticks_usec()
		var snap := _activity.state()
		_state_us += Time.get_ticks_usec() - s0
		return snap
	_view.beat_s = BEAT
	_view.reduced = bool(m.get("reduced", false))
	_view.high_contrast = bool(m.get("hc", false))
	_view.screen_size = size * 2.0
	_view.size = size
	_view.set_process(false)
	_sub.add_child(_view)
	var pic: Variant = _view.get("_pic")
	if (pic as Object).get("fn") is Callable:  # a view drawn in one piece (before the layers): wrap its single drawing callable
		_wrap_paint(pic as Object, "picture")
	for layer: Node in (pic as Node).get_children():  # every layer's drawing, summed per frame and kept per layer
		_wrap_paint(layer, str(layer.name))
	_t = 0.0
	var from := float(m["from"]) * BEAT
	while _t < from:
		_advance(minf(_t + 1.0 / 60.0, from))


func _wrap_paint(layer: Object, lname: String) -> void:
	var paint: Callable = layer.get("fn")
	if not paint.is_valid():
		return
	if paint.get_argument_count() == 1:
		layer.set("fn", func(ci: Control) -> void:
			var d0 := Time.get_ticks_usec()
			var m0 := OS.get_static_memory_usage()
			paint.call(ci)
			_draw_us += Time.get_ticks_usec() - d0
			_mem += OS.get_static_memory_usage() - m0)
	else:
		layer.set("fn", func(ci: Control, spec: Array) -> void:
			var m0 := OS.get_static_memory_usage()
			var d0 := Time.get_ticks_usec()
			paint.call(ci, spec)
			var d := Time.get_ticks_usec() - d0
			_draw_us += d
			_mem += OS.get_static_memory_usage() - m0
			if _i > WARMUP:
				var acc: Array = _per_layer.get(lname, [0, 0])
				_per_layer[lname] = [int(acc[0]) + d, int(acc[1]) + 1])


func _advance(t: float) -> int:
	_t = t
	var taps: Dictionary = _m.get("taps", {})
	for b: float in taps:
		if not _done_taps.has(b) and _t >= b * BEAT:
			_done_taps[b] = true
			_activity.tap(str(taps[b]), b * BEAT)
	for w: Array in _m.get("wobble", []):
		if not _done_taps.has("w%s" % w[0]) and _t >= float(w[0]) * BEAT:
			_done_taps["w%s" % w[0]] = true
			_activity.set_wobble(int(w[1]), float(w[0]) * BEAT)
	var fall := float(_m.get("fall", -1.0))
	if fall >= 0.0 and not _done_taps.has("fall") and _t >= fall * BEAT:
		_done_taps["fall"] = true
		_activity.interrupt("fall", fall * BEAT)
	var u0 := Time.get_ticks_usec()
	_activity.update(_t)
	return Time.get_ticks_usec() - u0


func _step_frame() -> void:
	var from := float(_m["from"]) * BEAT
	var to := float(_m["to"]) * BEAT
	var upd := _advance(from + (to - from) * float(_i) / float(_frames))
	_state_us = 0
	_draw_us = 0
	_mem = 0
	var p0 := Time.get_ticks_usec()
	_view._process(0.0)
	var proc := Time.get_ticks_usec() - p0
	if _i >= WARMUP:
		_samples["upd"].append(upd)
		_samples["proc"].append(proc)
		_samples["state"].append(_state_us)
	_pending = _i >= WARMUP
	_i += 1


## Called on the next frame: the drawing and the render of the frame stepped last time have happened.
func _collect() -> void:
	_pending = false
	_samples["draw"].append(_draw_us)
	_samples["mem"].append(_mem)
	_samples["rcpu"].append(RenderingServer.viewport_get_measured_render_time_cpu(_sub.get_viewport_rid()))
	_samples["calls"].append(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	_samples["prims"].append(Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
	_samples["objs"].append(Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME))


func _finish_moment() -> void:
	if _pending:
		_pending = false  # the last frame's drawing is not collected (the moment changes before it renders)
		for k in ["proc", "state", "upd"]:
			(_samples[k] as Array).pop_back()
	_rows.append({"name": _m["name"], "phase": str(_activity.state()["phase"]), "draw": _mean(_samples["draw"]), "draw95": _p95(_samples["draw"]), "proc": _mean(_samples["proc"]),
		"state": _mean(_samples["state"]), "upd": _mean(_samples["upd"]), "rcpu": _mean(_samples["rcpu"]), "calls": _mean(_samples["calls"]), "prims": _mean(_samples["prims"]),
		"objs": _mean(_samples["objs"]), "mem": _mean(_samples["mem"]), "layers": _top_layers()})


## The layers that cost most over the moment: name, mean microseconds per frame, and the share of frames that redrew it.
func _top_layers() -> String:
	var names := _per_layer.keys()
	names.sort_custom(func(a: String, b: String) -> bool: return int(_per_layer[a][0]) > int(_per_layer[b][0]))
	var n := float(maxi(1, _samples["draw"].size()))
	var parts: Array = []
	for k: String in names.slice(0, 5):
		parts.append("%s %d us %d%%" % [k, roundi(float(_per_layer[k][0]) / n), roundi(100.0 * float(_per_layer[k][1]) / n)])
	return ", ".join(parts)


static func _mean(a: Array) -> float:
	if a.is_empty():
		return 0.0
	var s := 0.0
	for v in a:
		s += float(v)
	return s / a.size()


static func _p95(a: Array) -> float:
	if a.is_empty():
		return 0.0
	var b := a.duplicate()
	b.sort()
	return float(b[int(b.size() * 0.95)])


func _print_table() -> void:
	print("PROFILE %d frames per moment (%d warm-up skipped)" % [_frames, WARMUP])
	print("%-16s %-11s %8s %8s %8s %7s %7s %6s %7s %8s %6s %7s" % ["moment", "phase", "draw_us", "draw_p95", "proc_us", "state", "upd_us", "rcpu", "calls", "prims", "objs", "mem_B"])
	var tot := 0.0
	for r: Dictionary in _rows:
		tot += float(r["draw"]) + float(r["proc"]) + float(r["upd"])
		print("%-16s %-11s %8.0f %8.0f %8.0f %7.0f %7.1f %6.3f %7.1f %8.0f %6.0f %7.0f" % [r["name"], r["phase"], r["draw"], r["draw95"], r["proc"], r["state"], r["upd"], r["rcpu"], r["calls"], r["prims"], r["objs"], r["mem"]])
	for r: Dictionary in _rows:
		print("LAYERS %-16s %s" % [r["name"], r["layers"]])
	print("PROFILE mean script us per frame over moments (draw + proc + upd): %.0f" % (tot / maxf(1.0, _rows.size())))
