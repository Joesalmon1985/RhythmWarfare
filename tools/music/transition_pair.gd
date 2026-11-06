extends SceneTree
## One scene change between two recorded tracks, played through the real engine, TransitionDirector, TransitionPlanner, RunAudio and RunTrackAudio (wired as RunPlay wires them), in real
## time on the real audio driver. Track A's scene is cut down to its last lap (the last 16 bars it plays in the game, from the same track time); at its end the run goes into track B's scene,
## which plays on for RW_PAIR_AFTER_BARS bars (default 20: past its first drop). A perfect player taps every cue. Needs RW_TRACKS_DIR (the packs folder) in the environment.
## Used by tools/dev/hear_transition.sh (with sound, for the owner's ear) and for the M2.4 / M2.5 measurements (muted, captured; tools/music/analyse_transition_pair.py).
##   RW_PAIR_A, RW_PAIR_B     the two track ids (required)
##   RW_RUN_TRANSITIONS=cut   every scene change a cut (to compare); =full every mode (the default here, whatever the game's default)
##   RW_PAIR_MUTE=1           the Master bus muted: nothing reaches the speakers (the capture is taken before it)
##   RW_PAIR_CAPTURE=<folder> RunTrackA, RunTrackB (after their effects) and RunTrack before and after its limiter recorded with AudioEffectCapture, with the clock position and every capture's
##                            frame count read together under AudioServer.lock every frame; written with the director's lock, the recipe and per-frame tail gains for the analysis
##   RW_PAIR_TAIL_DB=<dB>     the tail's level from T instead of the planner's TAIL_GAIN_DB (headroom trials)
## Prints PAIR lines: the plan chosen (mode, rate, cents, W, complete_t, drop_t) and the transition's log.

var data: RunData
var audio: RunAudio
var engine: RunEngine
var director: TransitionDirector
var _t_end := 0.0
var _started := false
var _next_cue := 0
var _caps: Dictionary = {}  # label -> AudioEffectCapture
var _bufs: Dictionary = {}
var _pushed0: Dictionary = {}
var _rows: Array = []
var _cap_dir := ""
var _tails: Array = []  # [song t, {key: gain}, pitch_scale, volume_db, cutoff]
var _frames: Array = []  # [song t, frame ms]
var _last_us := 0
var _mem: Array = []  # [song t, static MB]
var _a := ""
var _b := ""


func _initialize() -> void:
	_a = OS.get_environment("RW_PAIR_A")
	_b = OS.get_environment("RW_PAIR_B")
	if _a == "" or _b == "" or OS.get_environment("RW_TRACKS_DIR") == "":
		printerr("transition_pair: set RW_PAIR_A, RW_PAIR_B and RW_TRACKS_DIR")
		quit(2)
		return
	_cap_dir = OS.get_environment("RW_PAIR_CAPTURE")
	Engine.max_fps = 60  # (frames as the game has them, not a busy loop)
	if OS.get_environment("RW_PAIR_MUTE") == "1":
		AudioServer.set_bus_mute(0, true)
	data = RunData.load_default()
	var tmpl: Dictionary = data.nodes["warehouse"]
	for pair in [["hear_a", "hear_b"], ["hear_b", "hear_a"]]:
		var n: Dictionary = tmpl.duplicate(true)
		var edge: Dictionary = (tmpl["next"][0] as Dictionary).duplicate(true)
		edge["to"] = pair[1]
		n["id"] = pair[0]
		n["title"] = pair[0]
		n["next"] = [edge]
		n["cast"] = []
		n.erase("trial_gate")
		data.nodes[pair[0]] = n
		data.node_order.append(pair[0])
	var json := "user://transition_pair_scenes.json"
	var root := RunTrackScenes.packs_root()
	_write(json, {"hear_a": {"track": _a}, "hear_b": {"track": _b}})
	RunTrackScenes.load_for(data, json, root)
	var pa := data.track_scenes.plan_of("hear_a")
	if pa.is_empty() or data.track_scenes.plan_of("hear_b").is_empty():
		printerr("transition_pair: no pack for %s or %s in %s" % [_a, _b, root])
		quit(2)
		return
	var last_bar := int(pa["entry_bar"]) + 16 * (int(pa["laps"]) - 1)  # the last lap of A's scene as the game plays it
	print("PAIR %s: its scene enters at bar %d for %d laps; played here from bar %d (its last lap), %.2f BPM" % [_a, int(pa["entry_bar"]), int(pa["laps"]), last_bar, float(pa["bpm"])])
	_write(json, {"hear_a": {"track": _a, "start_bar": last_bar, "laps": 1}, "hear_b": {"track": _b}})
	RunTrackScenes.load_for(data, json, root)


static func _write(path: String, scenes: Dictionary) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify({"format": RunTrackScenes.FORMAT, "defaults": {}, "paths": {"main": scenes}}))
	f.close()


func _setup() -> void:
	audio = RunAudio.new()
	root.add_child(audio)
	audio.configure(data)
	engine = RunEngine.new(data)
	engine.hotspots = RunHotspots.new(data, {}, {})
	director = TransitionDirector.new()
	director.modes_override = 0 if OS.get_environment("RW_RUN_TRANSITIONS") == "cut" else 1
	if OS.get_environment("RW_PAIR_TAIL_DB") != "":
		var db := float(OS.get_environment("RW_PAIR_TAIL_DB"))
		director.planner = func(o: Dictionary, i: Dictionary, m: Dictionary, r: Dictionary) -> Dictionary:
			var p := TransitionPlanner.plan(o, i, m, r)
			if p.has("recipe"):
				(p["recipe"] as Dictionary)["tail_gain_db"] = db
			return p
	director.attach(engine, data)
	director.ready_fn = audio.track.is_ready
	director.load_fn = func(d: RunData, node: String) -> String: return audio.track.request_scene(d, node, true)
	director.release_fn = audio.track.release_pins
	director.recipe_fn = audio.prepare_transition
	audio.outgoing_silent.connect(director.on_outgoing_silent)
	director.audio_reports_silence = true
	engine.track_gate = director.track_gate
	audio.track.notes_fn = func() -> Array: return engine.level.notes
	audio.track.prepare(data, "hear_a")
	var st := audio.track.request_scene(data, "hear_b", true)
	var t0 := Time.get_ticks_msec()
	while st == "loading" and Time.get_ticks_msec() - t0 < 30000:
		OS.delay_msec(10)
		st = audio.track.state_of(data.track_scenes.plan_of("hear_b"))
	engine.begin("hear_a")
	var pb := data.track_scenes.plan_of("hear_b")
	_t_end = float(data.track_scenes.plan_of("hear_a")["lap_s"]) + float(OS.get_environment("RW_PAIR_AFTER_BARS") if OS.get_environment("RW_PAIR_AFTER_BARS") != "" else "20") * float(pb["bar_s"])
	for ev in engine.update(-0.001):
		_feed(ev)
	if _cap_dir != "":
		DirAccess.make_dir_recursive_absolute(_cap_dir)
		for name in RunTrackAudio.SLOT_BUSES:
			_cap(str(name), str(name), -1)
		_cap("RunTrackPre", RunTrackAudio.BUS, 0)
		_cap("RunTrackPost", RunTrackAudio.BUS, -1)
		var pf := FileAccess.open(_cap_dir.path_join("pid.txt"), FileAccess.WRITE)
		pf.store_string(str(OS.get_process_id()))
		pf.close()
	AudioServer.lock()
	for label in _caps:
		(_caps[label] as AudioEffectCapture).clear_buffer()
		_pushed0[label] = (_caps[label] as AudioEffectCapture).get_pushed_frames()
	audio.start()
	AudioServer.unlock()
	print("PAIR start: %s (last lap) into %s, %.1f s, transitions %s, driver %s, output latency %.2f ms" % [_a, _b, _t_end, "cut only" if director.modes_override == 0 else "every mode",
		AudioServer.get_driver_name(), AudioServer.get_output_latency() * 1000.0])


func _cap(label: String, bus_name: String, at: int) -> void:
	var c := AudioEffectCapture.new()
	c.buffer_length = 2.0
	var b := AudioServer.get_bus_index(bus_name)
	AudioServer.add_bus_effect(b, c, at)
	_caps[label] = c
	_bufs[label] = PackedVector2Array()


func _feed(ev: Dictionary) -> void:
	director.on_event(ev)
	audio.on_event(ev)
	if str(ev["kind"]) == "route_window":
		audio.track.prefetch_for(data, engine.node_id)


func _process(_d: float) -> bool:
	if data == null:
		return true
	if not _started:
		_started = true
		_setup()
		return false
	var now_us := Time.get_ticks_usec()
	if not _caps.is_empty():
		AudioServer.lock()
		var row := [audio.playback_position()]
		for label in _caps:
			row.append((_caps[label] as AudioEffectCapture).get_pushed_frames() - int(_pushed0[label]))
		AudioServer.unlock()
		_rows.append(row)
		for label in _caps:
			var c: AudioEffectCapture = _caps[label]
			var n := c.get_frames_available()
			if n > 0:
				_bufs[label].append_array(c.get_buffer(n))
	var t := audio.now_t()
	while _next_cue < engine.level.notes.size() and float(engine.level.notes[_next_cue]["time"]) <= t:
		var n: Dictionary = engine.level.notes[_next_cue]
		engine.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
		engine.release(int(n["pad"]), float(n["end_time"]) if str(n["type"]) == "hold" else float(n["time"]) + 0.05, int(n["pad"]))
		_next_cue += 1
	for ev in engine.update(t):
		_feed(ev)
	director.step(t)
	for g in audio.track._groups:
		if not (g.get("tail", {}) as Dictionary).is_empty():
			var tr: TrackTransport = g["transport"]
			var gains := {}
			for k in tr.stem_keys:
				gains[str(k)] = tr.tail_gain(str(k))
			_tails.append([t, gains, tr.player.pitch_scale, tr.player.volume_db])
	if _last_us > 0:
		_frames.append([t, float(now_us - _last_us) / 1000.0])
	_last_us = now_us
	if _frames.size() % 30 == 0:
		_mem.append([t, float(OS.get_static_memory_usage()) / 1048576.0])
	if t >= _t_end:
		_report()
		return true
	return false


func _report() -> void:
	for l in director.lock_log:
		var r: Dictionary = l["recipe"]
		var p: Dictionary = l["plan"]
		print("PAIR mode %s (fallback %s, reason %s): %s -> %s, %.4f -> %.4f BPM, tail rate %.6f (%+.1f cents), W %d bars, T %.3f, complete_t %.3f, drop_t %s, tail %.1f dB" % [str(p["mode"]),
			str(p["fallback"]), str(r.get("reason", "-")), _a, _b, float(p["outgoing_bpm"]), float(p["incoming_bpm"]), float(r.get("rate", 1.0)), float(r.get("cents", 0.0)),
			int(r.get("window_bars", 0)), float(l["boundary"]), float(p["complete_t"]), "%.3f" % float(r["drop_t"]) if r.has("drop_t") else "-", float(r.get("tail_gain_db", 0.0))])
	for x in director.log:
		if str(x["signal"]) in ["locked", "tempo_changed", "switched", "completed"]:
			print("PAIR signal %s at t=%.3f" % [str(x["signal"]), float(x["t"])])
	for x in audio.track.log:
		if str(x["kind"]) in ["prestart", "corrected", "start", "tail", "floor", "orphan", "end"]:
			var y: Dictionary = x.duplicate()
			y.erase("stems")
			y.erase("gains")
			print("PAIR track ", JSON.stringify(y))
	var fr := _frames.map(func(f: Array) -> float: return float(f[1]))
	fr.sort()
	if not fr.is_empty():
		var T := float(director.lock_log[0]["boundary"]) if not director.lock_log.is_empty() else 0.0
		var worst_T := 0.0
		for f in _frames:
			if absf(float(f[0]) - T) <= 0.5:
				worst_T = maxf(worst_T, float(f[1]))
		print("PAIR frames %d: median %.1f ms, p99 %.1f ms, max %.1f ms; worst within 0.5 s of T %.1f ms" % [fr.size(), fr[fr.size() / 2], fr[int(fr.size() * 0.99)], fr[fr.size() - 1], worst_T])
	if not _mem.is_empty():
		var mx := 0.0
		for m in _mem:
			mx = maxf(mx, float(m[1]))
		print("PAIR memory static: start %.1f MB, max %.1f MB, end %.1f MB" % [float(_mem[0][1]), mx, float(_mem[_mem.size() - 1][1])])
	if _cap_dir != "":
		for label in _caps:
			var f := FileAccess.open(_cap_dir.path_join(label + ".f32"), FileAccess.WRITE)
			f.store_buffer((_bufs[label] as PackedVector2Array).to_byte_array())
			f.close()
		var pa := data.track_scenes.plan_of("hear_a")
		var pb := data.track_scenes.plan_of("hear_b")
		var stems := func(p: Dictionary) -> Array: return (p["pack"] as TrackPack).stems_in_order().map(func(s: Dictionary) -> Dictionary: return {"key": s["key"], "stem": s["stem"], "gain": s["gain"]})
		var info := {"labels": _caps.keys(), "rows": _rows, "driver": AudioServer.get_driver_name(), "output_latency": AudioServer.get_output_latency(), "tails": _tails, "frames": _frames, "mem": _mem,
			"lock": director.lock_log.map(func(l: Dictionary) -> Dictionary: return {"boundary": l["boundary"], "plan": l["plan"], "recipe": l["recipe"]}),
			"track_log": audio.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) != "mute" and str(x["kind"]) != "restore"),
			"a": {"track": _a, "dir": str(pa["dir"]), "bpm": float(pa["bpm"]), "fd": float(pa["first_downbeat_s"]), "stems": stems.call(pa)},
			"b": {"track": _b, "dir": str(pb["dir"]), "bpm": float(pb["bpm"]), "fd": float(pb["first_downbeat_s"]), "stems": stems.call(pb), "entry_t": float(pb["entry_t"])}}
		var jf := FileAccess.open(_cap_dir.path_join("pair.json"), FileAccess.WRITE)
		jf.store_string(JSON.stringify(info))
		jf.close()
		print("PAIR capture written to %s (%d frames each)" % [_cap_dir, (_bufs[RunTrackAudio.BUS + "Pre"] as PackedVector2Array).size() if _bufs.has(RunTrackAudio.BUS + "Pre") else 0])
	audio.stop()
	quit()
