extends RefCounted
## The real TransitionDirector on a real RunEngine, on a virtual clock, for the conformance cases (tests/port_conformance.gd, run by tests/test_port_real.gd) and the director's own
## tests. No audio, no scene tree: advance(dt) steps the engine in frames of at most 1/60 s, feeds every event to the director (as RunPlay._handle does) and steps it (as RunPlay._advance).
##
## The run: the main run's data with synthetic scenes added (each a copy of the Warehouse floor's node, its only route to "dflt", no cast lines), every one a TRACK SCENE with a synthetic
## plan (no pack, no audio: the engine charts one tap per block from it) of the opts' tempo, laps and doors_from_lap, so departure laps exist before the last lap. A scripted player hits
## every cue (or misses the cues of every lap's last block, &"miss_last_block"). The engine has no hotspots, so nothing leaves a lap on its own but the final lap's default exit.
##
## The loader is a stand-in for RunTrackAudio (load_fn / ready_fn): "ready" for every scene, "loading" for ever for &"not_ready_ids" (whose gate then says false: the scene plays as an
## ordinary one). &"fail_load_ids" are destinations the run has no scene for (the director's own validation refuses them). &"fail_after_lock_ids" are staged by sending the engine
## to "fallback" right after the director locked them (as RunPlay._path_swap does when a path cannot be loaded). &"blend_beats" > 0 is refused: the M1 director only cuts.

const NODES := ["start", "a", "b", "c", "d", "dflt", "late", "good", "slow", "doomed", "fallback", "hit", "miss",
	"n0", "n1", "n2", "n3", "n4", "n5", "n6", "n7", "n8", "n9", "m0", "m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8", "m9"]
const FRAME := 1.0 / 60.0
const TRACK_LAPS := 24  # the synthetic track's length, in laps after its entry bar (no wrap in any case)

var data: RunData
var engine: RunEngine
var director: TransitionDirector
var opts: Dictionary
var not_ready_ids: Array[String] = []
var fail_after_lock_ids: Array[String] = []
var miss_last_block := false
var events: Array = []  # every engine event fed to the director
var _t := 0.0
var _pressed: Dictionary = {}
var _scan := 0
var _divert := ""  # a route the engine is sent to on the next frame (fail_after_lock_ids)


func _init(p_opts: Dictionary) -> void:
	opts = p_opts
	data = RunData.load_default()
	var tmpl: Dictionary = data.nodes["warehouse"]
	var edge: Dictionary = (tmpl["next"][0] as Dictionary).duplicate(true)
	edge["to"] = "dflt"
	for id in NODES:
		var n: Dictionary = tmpl.duplicate(true)
		n["id"] = id
		n["title"] = id
		n["next"] = [edge.duplicate(true)]
		n["cast"] = []
		n.erase("trial_gate")
		data.nodes[id] = n
		if not data.node_order.has(id):
			data.node_order.append(id)
	data.track_scenes = RunTrackScenes.new()
	for id in NODES:
		set_scene(id, float(opts["bpm"]), int(opts["laps"]), int(opts["doors_from_lap"]))
	engine = RunEngine.new(data)
	director = TransitionDirector.new()
	director.ready_fn = func(p: Dictionary) -> bool: return not not_ready_ids.has("main/" + str(p.get("dir", "")).trim_prefix("fx/"))
	director.load_fn = func(d: RunData, node: String) -> String:
		if d.track_scenes == null or d.track_scenes.plan_of(node).is_empty():
			return ""
		return "loading" if not_ready_ids.has("main/" + node) else "ready"
	director.attach(engine, data)
	engine.track_gate = director.track_gate
	director.locked.connect(_on_locked)
	engine.begin("start")
	_feed(engine.update(0.0))
	director.step(0.0)
	director.set_default({})


## The synthetic track plan of scene `id` (what RunTrackPlan.compute gives, with one tap on beat 4 of every block and no pack).
func set_scene(id: String, bpm: float, laps: int, doors: int) -> void:
	var beat := 60.0 / bpm
	var lap_s := 64.0 * beat
	var entry_t := 64.0 * beat
	var cues: Array = []
	for k in TRACK_LAPS * 4:
		cues.append({"t": entry_t + (float(k) * 16.0 + 4.0) * beat, "pad": 1 + k % 4, "dur": 0.0, "conf": 0.9, "voice": "drums"})
	data.track_scenes._plans[id] = {"track": "fx_" + id, "dir": "fx/" + id, "bpm": bpm, "beat_s": beat, "bar_s": 4.0 * beat, "lap_s": lap_s, "first_downbeat_s": 0.0,
		"duration_s": entry_t + float(TRACK_LAPS) * lap_s, "entry": "drop", "entry_bar": 16, "entry_t": entry_t, "laps": laps, "max_laps": laps,
		"doors_from_lap": mini(maxi(doors, 1), laps), "chart": "normal", "cues": cues, "index": 0, "pack": null}


func advance(dt: float) -> void:
	var target := _t + maxf(dt, 0.0)
	while _t < target - 1e-12:
		var nt := minf(_t + FRAME, target)
		_play_until(nt)
		if _divert != "":
			engine.take_route(_divert)
			_divert = ""
		_feed(engine.update(nt))
		director.step(nt)
		_t = nt


func switch(name: StringName, value: Variant) -> bool:
	match name:
		&"fail_load_ids":
			for id in (value as Array):  # (the rig's run has no such scene: the director's validation is what refuses them)
				var parts := str(id).split("/")
				if parts.size() == 2 and parts[0] == "main" and data.nodes.has(parts[1]):
					return false
			return true
		&"not_ready_ids":
			not_ready_ids.assign(value)
		&"fail_after_lock_ids":
			fail_after_lock_ids.assign(value)
		&"miss_last_block":
			miss_last_block = bool(value)
		&"blend_beats":
			return int(value) == 0  # (cut only in M1: a blend is stage M2's)
		&"scene_specs":
			for id in (value as Dictionary):
				var spec: Dictionary = value[id]
				var node := str(id).trim_prefix("main/")
				if not data.nodes.has(node):
					return false
				set_scene(node, float(spec.get("bpm", opts["bpm"])), int(spec.get("laps", opts["laps"])), int(spec.get("doors_from_lap", opts["doors_from_lap"])))
		_:
			return false
	return true


func _feed(evs: Array) -> void:
	for ev in evs:
		events.append(ev)
		director.on_event(ev)


func _on_locked(_id: int, dest: Dictionary, _b: float, _plan: Dictionary) -> void:
	if fail_after_lock_ids.has(str(dest.get("id", ""))):
		_divert = "fallback"  # the destination fails after the lock: on the next frame (after the lock point) the run is sent on by another scene


## The scripted player: every cue due by `t` is hit on its time (the cues of a lap's last block are let go with miss_last_block).
func _play_until(t: float) -> void:
	var notes: Array = engine.level.notes
	for i in range(_scan, notes.size()):
		var n: Dictionary = notes[i]
		if float(n["time"]) > t:
			continue
		if _pressed.has(i):
			continue
		_pressed[i] = true
		if miss_last_block and int(n["block"]) == 3:
			continue
		engine.press(int(n["pad"]), float(n["time"]))
	while _scan < notes.size() and _pressed.has(_scan):
		_scan += 1
