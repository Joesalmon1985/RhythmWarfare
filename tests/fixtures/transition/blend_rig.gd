extends RefCounted
## The whole transition engine on a virtual clock, for the M2.4 and M2.5 tests: a real RunEngine, the real TransitionDirector (and TransitionPlanner.plan_full when `modes` is 1), a real
## RunAudio with its RunTrackAudio playing synthetic fixture packs (tests/fixtures/track_scenes/track_scene_fixtures.gd), wired exactly as RunPlay wires them. No audio is judged here: the
## players run on the Dummy driver, but the song time is the rig's own, every scheduled item runs on its own song time, and the track audio's playhead readings (position_fn) are perfect
## unless `lags` makes the muted starts land late.
##
## The run: synthetic scenes tx0, tx1, ... (copies of the Warehouse floor's node, no hotspots, no cast), scene i's only route going to scene i + 1 (the last back to tx0), each a TRACK SCENE
## of its own fixture pack through RunTrackScenes (the real plan, with RunTrackScenes.add_transition_meta). A scripted player presses every cue `offset` seconds off its time.
## chain: [{track: id, spec: Fx.write_pack spec (written when given), entry: assignment fields over {laps: 2, doors_from_lap: 2}}], one per scene.

const Fx := preload("res://tests/fixtures/track_scenes/track_scene_fixtures.gd")
const FRAME := 1.0 / 60.0

var data: RunData
var engine: RunEngine
var director: TransitionDirector
var audio: RunAudio
var ids: Array = []
var offset := 0.0
var events: Array = []  # every engine event
var grades: Array = []  # [{t (song time of the press or miss), kind, cue_t, scene, phase}]
var frames: Array = []  # [{t, tails: [{track, rate, volume_db, gains {key: g}, hp_on, delay_on, cutoff}], groups}] when `sample` is set
var sample := false
var t := 0.0
var lags: Array = []  # landing lags of the muted starts (s), in turn; [] lands every start exactly
var _pressed := {}
var _scan := 0
var _lag_k := 0
var _sim := {}  # group transport -> {gp, start, fresh}


func _init(tree: SceneTree, chain: Array, modes := 1, start_t := 0.0) -> void:
	data = RunData.load_default()
	var tmpl: Dictionary = data.nodes["warehouse"]
	for i in chain.size():
		ids.append("tx%d" % i)
	for i in chain.size():
		var edge: Dictionary = (tmpl["next"][0] as Dictionary).duplicate(true)
		edge["to"] = ids[(i + 1) % ids.size()]
		var n: Dictionary = tmpl.duplicate(true)
		n["id"] = ids[i]
		n["title"] = ids[i]
		n["next"] = [edge]
		n["cast"] = []
		n.erase("trial_gate")
		data.nodes[ids[i]] = n
		data.node_order.append(ids[i])
	var scenes := {}
	for i in chain.size():
		var c: Dictionary = chain[i]
		if c.has("spec"):
			Fx.write_pack(str(c["track"]), c["spec"])
		var ent := {"track": str(c["track"]), "laps": 2, "doors_from_lap": 2}
		ent.merge(c.get("entry", {}), true)
		scenes[ids[i]] = ent
	RunTrackScenes.load_for(data, Fx.write_scenes({"main": scenes}), Fx.root())
	audio = RunAudio.new()
	tree.root.add_child(audio)
	audio.configure(data)
	audio.track.period_override = 0.01
	audio.track.position_fn = _positions
	engine = RunEngine.new(data)
	director = TransitionDirector.new()
	director.modes_override = modes
	director.attach(engine, data)
	director.ready_fn = audio.track.is_ready
	director.load_fn = func(d: RunData, node: String) -> String: return audio.track.request_scene(d, node, true)
	director.release_fn = audio.track.release_pins
	director.recipe_fn = audio.prepare_transition
	audio.outgoing_silent.connect(director.on_outgoing_silent)
	director.audio_reports_silence = true
	engine.track_gate = director.track_gate
	audio.track.notes_fn = func() -> Array: return engine.level.notes
	audio.track.prepare(data, ids[0])
	engine.begin(ids[0])
	t = start_t
	_feed(engine.update(t - 0.001))
	audio.track.start_with_clock()


func free_all() -> void:
	if is_instance_valid(audio):
		audio.stop()
		audio.free()
	Fx.clear()


## The simulated audio thread's readings for a muted start: it lands lags[k] late (k counting every start and restart), then moves at its pitch_scale.
func _positions(g: Dictionary) -> Array:
	var tr: TrackTransport = g["transport"]
	var s: Dictionary = _sim.get(tr, {})
	if s.is_empty() or absf(float(s["start"]) - tr.start_at) > 1e-12:
		var lag := float(lags[_lag_k % lags.size()]) if not lags.is_empty() else 0.0
		_lag_k += 1
		s = {"start": tr.start_at, "gp": tr.start_at - lag, "x": t}
		_sim[tr] = s
		return []
	var gp := float(s["gp"]) + (t - float(s["x"])) * tr.player.pitch_scale
	s["gp"] = gp
	s["x"] = t
	return [t, gp]


func advance(dt: float) -> void:
	var target := t + dt
	while t < target - 1e-12:
		var nt := minf(t + FRAME, target)
		_play_until(nt)
		t = nt
		_feed(engine.update(t))
		while not audio._schedule.is_empty() and float(audio._schedule[0]["t"]) <= t:
			var item: Dictionary = audio._schedule.pop_front()
			audio._run(item, float(item["t"]), 0.0)
		audio.track.step(t, 0.0)
		audio.check_silence(t)
		director.step(t)
		if sample:
			_sample()


func _feed(evs: Array) -> void:
	for ev in evs:
		events.append(ev)
		director.on_event(ev)
		audio.on_event(ev)
		if str(ev["kind"]) == "route_window":
			audio.track.prefetch_for(data, engine.node_id)
			wait_loads()
		elif str(ev["kind"]) == "judge":
			var je: Dictionary = ev["event"]
			if str(je.get("kind", "")) in ["perfect", "great", "ok", "miss"]:
				var idx := int(je.get("index", -1))
				var n: Dictionary = engine.level.notes[idx] if idx >= 0 and idx < engine.level.notes.size() else {}
				grades.append({"t": float(je.get("time", ev["t"])), "kind": str(je["kind"]), "cue_t": float(n.get("time", -1.0)), "scene": engine.node_id, "phase": int(n.get("phase", -1))})


func wait_loads() -> void:
	for _i in 2000:
		audio.track._poll()
		if not audio.track.cached().values().has("loading"):
			return
		OS.delay_msec(2)


func _play_until(tt: float) -> void:
	var notes: Array = engine.level.notes
	for i in range(_scan, notes.size()):
		var n: Dictionary = notes[i]
		if float(n["time"]) + offset > tt:
			continue
		if _pressed.has(i):
			continue
		_pressed[i] = true
		engine.press(int(n["pad"]), float(n["time"]) + offset, int(n["pad"]))
		engine.release(int(n["pad"]), (float(n["end_time"]) if str(n["type"]) == "hold" else float(n["time"]) + 0.06) + offset, int(n["pad"]))
	while _scan < notes.size() and _pressed.has(_scan):
		_scan += 1


func _sample() -> void:
	var tails: Array = []
	for g in audio.track._groups:
		if (g.get("tail", {}) as Dictionary).is_empty():
			continue
		var tr: TrackTransport = g["transport"]
		var gains := {}
		for k in tr.stem_keys:
			gains[str(k)] = tr.tail_gain(str(k))
		var bus := AudioServer.get_bus_index(str(RunTrackAudio.SLOT_BUSES[int(g["slot"])]))
		tails.append({"track": str(g["track"]), "rate": tr.player.pitch_scale, "volume_db": tr.player.volume_db, "gains": gains, "slot": int(g["slot"]),
			"hp_on": AudioServer.is_bus_effect_enabled(bus, RunTrackAudio.FX_HIGHPASS), "delay_on": AudioServer.is_bus_effect_enabled(bus, RunTrackAudio.FX_DELAY),
			"cutoff": (AudioServer.get_bus_effect(bus, RunTrackAudio.FX_HIGHPASS) as AudioEffectHighPassFilter).cutoff_hz, "T": float((g["tail"] as Dictionary)["T"])})
	var groups: Array = []
	for g in audio.track._groups:
		var tr2: TrackTransport = g["transport"]
		groups.append({"track": str(g["track"]), "pending": bool(g.get("pending", false)), "fading": bool(g["fading"]), "volume_db": tr2.player.volume_db, "rate": tr2.player.pitch_scale})
	frames.append({"t": t, "tails": tails, "groups": groups, "song_time": director.song_time()})


## Runs until `n` transitions have completed (or max_s of song time).
func run_transitions(n: int, max_s := 2000.0) -> void:
	while t < max_s and signals(&"completed").size() < n:
		advance(0.25)


func signals(name: StringName) -> Array:
	return director.log.filter(func(e: Dictionary) -> bool: return e["signal"] == name)


## A synthetic pack spec at `bpm`: `bars` long, its first drop at bar `drop` (so the scene enters at drop - 16), a tap on every 2nd beat from bar 8 on, drums, bass, backing stems.
static func spec(bpm: float, drop := 32, bars := 128, extra := {}) -> Dictionary:
	var s := {"bpm": bpm, "first_downbeat_s": 0.05, "bars": bars, "cue_bars": [8, bars - 4], "step_beats": 2, "other": true,
		"sections": [["intro", "intro", 0, drop], ["drop1", "drop", drop, mini(drop + 48, bars)], ["outro", "outro", mini(drop + 48, bars), bars]]}
	s.merge(extra, true)
	return s
