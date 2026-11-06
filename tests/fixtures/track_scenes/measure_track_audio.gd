extends SceneTree
## A measurement, not a test: a real track scene played in real time through RunAudio and RunTrackAudio, with the engine driven from the song clock by a perfect player (every cue tapped on its
## time) and the transition seam wired as RunPlay wires it (TransitionDirector on the engine, RunAudio.outgoing_silent -> completed). Needs packs: RW_TRACKS_DIR=<packs folder> on the command
## line (never in the suite). Prints one MEASURE line per figure:
##   audio   the driver, the mix rate, the output latency the engine reports, the mix period seen from the main thread
##   load    the first scene's stems decoded on a worker thread (ms), then every other pack decoded once (ms each), and the static memory with 1, 2 and 3 packs held
##   entry   the worst frame (wall time between frames) within half a second of each track scene's start, and the time the start item itself took
##   frames  the worst frames of the run with what happened in them (engine events, track audio log entries, packs taken or let go, process time, memory and object counts)
##   sync    the track group's playhead against the song clock: (track position - clock position) - (track_t0 - t0), sampled every frame from 2 s after the start; max, mean and the drift per 100 s
##   seam    every transition the director locked, its `completed`, and whether RunAudio.outgoing_silent reported it (or the director's grace timer did)
## Name the audio driver with the figures: the Dummy driver mixes in 88.5 ms chunks on a thread, a device driver in 5 to 20 ms.
##   godot --audio-driver Dummy --path . -s tests/fixtures/track_scenes/measure_track_audio.gd
## Options (environment): RW_MEASURE_S seconds to play (default 100); RW_RUN_START the scene (default warehouse); RW_MEASURE_LEAVE=n leave every track scene at the end of lap n (its first open
## lap from n on: the default route is chosen, so two scene changes fit in 100 s); RW_MEASURE_PACKS=a,b two more scenes whose packs are held from the start (memory with 2 and 3 packs);
## RW_MEASURE_MUTE=1 the Master bus muted (nothing reaches the speakers; a capture is taken before it); RW_MEASURE_CAPTURE=<folder> the RunTrack bus is recorded with AudioEffectCapture,
## with the clock position and the capture's frame count read together under AudioServer.lock every frame, for tests/fixtures/track_scenes/analyse_track_capture.py (cue time against the audio itself).

var data: RunData
var audio: RunAudio
var engine: RunEngine
var director: TransitionDirector
var _t_end := 100.0
var _last_us := 0
var _frames: Array = []  # [song t, frame ms, process ms, what]
var _starts: Array = []  # song t of each track start
var _dev: Array = []  # [song t, deviation s]
var _start_cost_us := 0
var _mem0 := 0
var _next_cue := 0
var _cost_t := 0.0
var _leave := 0
var _cap: AudioEffectCapture
var _cap_dir := ""
var _cap_buf := PackedVector2Array()
var _cap_rows: Array = []  # [clock position, pushed frames since the start]
var _cap_pushed0 := 0
var _chunks: Array = []
var _log_n := 0
var _load_n := 0
var _mem_last := 0
var _obj_last := 0
var _scenes: Array = []


func _initialize() -> void:
	_t_end = float(OS.get_environment("RW_MEASURE_S")) if OS.has_environment("RW_MEASURE_S") else 100.0
	_leave = int(OS.get_environment("RW_MEASURE_LEAVE")) if OS.has_environment("RW_MEASURE_LEAVE") else 0
	_cap_dir = OS.get_environment("RW_MEASURE_CAPTURE") if OS.has_environment("RW_MEASURE_CAPTURE") else ""
	Engine.max_fps = 60 if OS.has_environment("RW_MEASURE_CAPTURE") else Engine.max_fps
	data = RunData.load_default()
	printerr("measure: data loaded, %d errors" % data.errors.size())
	if data.track_scenes == null:
		print("MEASURE none: no track scenes (set RW_TRACKS_DIR)")
		quit(1)
		return
	audio = RunAudio.new()
	root.add_child(audio)
	if OS.get_environment("RW_MEASURE_MUTE") == "1":
		AudioServer.set_bus_mute(0, true)


## (in the first frame: the nodes are in the tree only now)
func _setup() -> void:
	var start := OS.get_environment("RW_RUN_START") if OS.has_environment("RW_RUN_START") else "warehouse"
	_mem0 = OS.get_static_memory_usage()
	printerr("measure: configure")
	audio.configure(data)
	print("MEASURE audio driver %s, mix rate %d, output latency reported %.2f ms (read at the start; RunAudio.now_t subtracts it)" % [AudioServer.get_driver_name(), AudioServer.get_mix_rate(), AudioServer.get_output_latency() * 1000.0])
	engine = RunEngine.new(data)
	engine.hotspots = RunHotspots.new(data, {}, {})
	director = TransitionDirector.new()
	director.attach(engine, data)
	director.ready_fn = audio.track.is_ready
	director.load_fn = func(d: RunData, node: String) -> String: return audio.track.request_scene(d, node, true)
	director.release_fn = audio.track.release_pins
	director.recipe_fn = audio.prepare_transition
	audio.outgoing_silent.connect(director.on_outgoing_silent)
	director.audio_reports_silence = true
	engine.track_gate = director.track_gate
	audio.track.notes_fn = func() -> Array: return engine.level.notes
	printerr("measure: prepare ", start, " ", str(data.track_scenes.plan_of(start).get("track", "(no track)")))
	var m_before := OS.get_static_memory_usage()
	var ms := audio.track.prepare(data, start)
	var m1 := OS.get_static_memory_usage()
	print("MEASURE memory static %+.1f MB for the first scene's stems in memory (1 pack)" % [float(m1 - m_before) / 1048576.0])
	print("MEASURE load first scene %s: %.1f ms (worker thread, waited for before the start)" % [start, ms])
	var extra := OS.get_environment("RW_MEASURE_PACKS").split(",", false) if OS.has_environment("RW_MEASURE_PACKS") else PackedStringArray()
	var held := 1
	for node in extra:
		var st := audio.track.request_scene(data, node, true)
		var t0 := Time.get_ticks_msec()
		while st == "loading" and Time.get_ticks_msec() - t0 < 30000:
			OS.delay_msec(20)
			st = audio.track.state_of(data.track_scenes.plan_of(node))
		if st == "ready":
			held += 1
			print("MEASURE memory static %+.1f MB with %d packs held (%s added)" % [float(OS.get_static_memory_usage() - m_before) / 1048576.0, held, str(data.track_scenes.plan_of(node).get("track", node))])
	audio.track.release_pins()
	engine.begin(start)
	audio.track.warm([data])  # (as RunPlay does: the scene plans on a worker thread)
	for ev in engine.update(-0.001):
		_feed(ev)
	if _cap_dir != "":
		var b := AudioServer.get_bus_index(RunTrackAudio.BUS)
		_cap = AudioEffectCapture.new()
		_cap.buffer_length = 2.0
		AudioServer.add_bus_effect(b, _cap, 0)  # (before the limiter: the stems as summed)
	AudioServer.lock()
	if _cap != null:
		_cap.clear_buffer()
		_cap_pushed0 = _cap.get_pushed_frames()
	audio.start()
	AudioServer.unlock()
	_mem_last = OS.get_static_memory_usage()
	_obj_last = int(Performance.get_monitor(Performance.OBJECT_COUNT))


func _feed(ev: Dictionary) -> void:
	director.on_event(ev)  # (before the audio, as RunPlay._handle)
	audio.on_event(ev)


func _process(_delta: float) -> bool:
	if audio == null:
		return true
	if engine == null:
		_setup()
		return false
	var now_us := Time.get_ticks_usec()
	if _cap != null:
		AudioServer.lock()
		_cap_rows.append([audio.playback_position(), _cap.get_pushed_frames() - _cap_pushed0])
		AudioServer.unlock()
		var n := _cap.get_frames_available()
		if n > 0:
			_cap_buf.append_array(_cap.get_buffer(n))
	_chunks.append(AudioServer.get_time_since_last_mix() + AudioServer.get_time_to_next_mix())
	var t := audio.now_t()
	if _frames.size() % 600 == 0:
		printerr("measure: frame %d song t %.2f clock playing %s pos %.3f" % [_frames.size(), t, str(audio.player.playing), audio.player.get_playback_position()])
	var what: Array = []
	var t0 := Time.get_ticks_usec()
	while _next_cue < engine.level.notes.size() and float(engine.level.notes[_next_cue]["time"]) <= t:  # a perfect player (taps on the cue's time; a hold held to its end), so the run goes on
		var n: Dictionary = engine.level.notes[_next_cue]
		engine.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
		engine.release(int(n["pad"]), float(n["end_time"]) if str(n["type"]) == "hold" else float(n["time"]) + 0.05, int(n["pad"]))
		_next_cue += 1
	for ev in engine.update(t):
		_feed(ev)
		var k := str(ev["kind"])
		if k not in ["judge", "cue", "tick"]:
			what.append(k)
		if k == "track_start":
			_starts.append(float(ev["t"]))
		if k == "phase_start":
			_scenes.append([float(ev["t"]), str(ev.get("node", "")), str(ev.get("track", ""))])
		if k == "route_window":
			audio.track.prefetch_for(data, engine.node_id)
			what.append("prefetch")
			if _leave > 0 and not engine.track_info().is_empty() and int(ev.get("lap", 0)) >= _leave:
				engine.choose(str(ev["default"]))
	director.step(t)
	var cost := Time.get_ticks_usec() - t0
	if cost > _start_cost_us:
		_start_cost_us = cost
		_cost_t = t
	for i in range(_log_n, audio.track.log.size()):
		var k2 := str(audio.track.log[i]["kind"])
		if k2 not in ["mute", "restore"]:
			what.append("track:" + k2)
	_log_n = audio.track.log.size()
	for i in range(_load_n, audio.track.load_log.size()):
		what.append("decoded:" + str(audio.track.load_log[i]["track"]))
	_load_n = audio.track.load_log.size()
	var mem := OS.get_static_memory_usage()
	var obj := int(Performance.get_monitor(Performance.OBJECT_COUNT))
	if mem - _mem_last < -4 * 1048576 or mem - _mem_last > 4 * 1048576:
		what.append("memory %+.0f MB" % (float(mem - _mem_last) / 1048576.0))
	if obj != _obj_last:
		what.append("objects %+d" % (obj - _obj_last))
	_mem_last = mem
	_obj_last = obj
	if _last_us > 0:
		_frames.append([t, float(now_us - _last_us) / 1000.0, Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0, what, float(cost) / 1000.0])
	_last_us = now_us
	var g := audio.track.live()
	if not g.is_empty() and t > float(g["t0"]) + 2.0 and float(g["position"]) >= 0.0:
		var clock_pos := audio.playback_position()
		_dev.append([t, (float(g["position"]) - clock_pos) - (float(g["track_t0"]) - float(g["t0"])), float(g["t0"])])
	if t >= _t_end:
		_report()
		return true
	return false


func _report() -> void:
	var cs := _chunks.duplicate()
	cs.sort()
	print("MEASURE audio mix period seen from the main thread (time since last mix + time to next): median %.2f ms, max %.2f ms" % [cs[cs.size() / 2] * 1000.0, cs[-1] * 1000.0])
	for l in audio.track.load_log:
		print("MEASURE load %s: %.1f ms for %d stems (%s)" % [l["track"], float(l["ms"]), int(l["stems"]), "ok" if bool(l["ok"]) else str(l["error"])])
	print("MEASURE memory static %+.1f MB with the packs in memory (%d cached)" % [float(OS.get_static_memory_usage() - _mem0) / 1048576.0, audio.track.cached().size()])
	print("MEASURE scenes ", JSON.stringify(_scenes))
	for s in _starts:
		var worst := 0.0
		for f in _frames:
			if absf(float(f[0]) - float(s)) <= 0.5:
				worst = maxf(worst, float(f[1]))
		print("MEASURE entry at t=%.3f: worst frame %.1f ms within 0.5 s" % [float(s), worst])
	var by_ms := _frames.duplicate()
	by_ms.sort_custom(func(a: Array, b: Array) -> bool: return float(a[1]) > float(b[1]))
	for i in mini(8, by_ms.size()):
		var f: Array = by_ms[i]
		print("MEASURE frame %.1f ms at song t=%.3f: process %.1f ms, the measure's own engine and audio-event work %.2f ms, in it: %s" % [float(f[1]), float(f[0]), float(f[2]), float(f[4]), ", ".join(f[3])])
	var all := _frames.map(func(f: Array) -> float: return float(f[1]))
	all.sort()
	if not all.is_empty():
		print("MEASURE frames %d: median %.1f ms, p99 %.1f ms, max %.1f ms; the frame with the most engine and audio-event work %.2f ms (at t=%.2f)" % [all.size(), all[all.size() / 2], all[int(all.size() * 0.99)], all[all.size() - 1], float(_start_cost_us) / 1000.0, _cost_t])
	var by_group := {}
	for d in _dev:
		by_group.get_or_add(float(d[2]), []).append(d)
	for g0 in by_group:
		var ds: Array = by_group[g0]
		if ds.size() < 3:
			continue
		var mx := 0.0
		var sum := 0.0
		for d in ds:
			mx = maxf(mx, absf(float(d[1])))
			sum += float(d[1])
		var a: Array = ds[0]
		var b: Array = ds[ds.size() - 1]
		var slope := (float(b[1]) - float(a[1])) / maxf(float(b[0]) - float(a[0]), 0.001) * 100.0
		print("MEASURE sync group from t=%.2f: %d samples over %.1f s: max |track - clock| %.2f ms, mean %.2f ms, drift %.3f ms per 100 s" % [float(g0), ds.size(), float(b[0]) - float(a[0]), mx * 1000.0, sum / ds.size() * 1000.0, slope * 1000.0])
	for l in director.lock_log:
		print("MEASURE seam lock id=%d at t=%.3f boundary %.3f to %s mode %s complete_t %.3f" % [int(l["id"]), float(l["t"]), float(l["boundary"]), str(l["dest"]), str((l["plan"] as Dictionary).get("mode", "")), float((l["plan"] as Dictionary).get("complete_t", 0.0))])
	for x in director.log:
		if str(x["signal"]) in ["switched", "completed"]:
			print("MEASURE seam %s %s at t=%.3f" % [str(x["signal"]), JSON.stringify(x["args"]), float(x["t"])])
	for x in audio.transition_log:
		print("MEASURE seam audio ", JSON.stringify(x))
	print("MEASURE track log ", JSON.stringify(audio.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) in ["start", "seek", "end", "not_ready", "unloaded"])))
	if _cap != null:
		var f := FileAccess.open(_cap_dir.path_join("run_track.f32"), FileAccess.WRITE)
		f.store_buffer(_cap_buf.to_byte_array())
		f.close()
		var groups: Array = []
		for x in audio.track.log:
			if str(x["kind"]) in ["start", "seek"]:
				groups.append(x)
		var plans := {}
		for x in groups:
			var dir := ""
			for c in audio.track.load_log:
				if str(c["track"]) == str(x["track"]):
					dir = str(c["dir"])
			plans[str(x["track"])] = dir
		FileAccess.open(_cap_dir.path_join("run_track.json"), FileAccess.WRITE).store_string(JSON.stringify({"rows": _cap_rows, "log": groups, "dirs": plans, "driver": AudioServer.get_driver_name(),
			"output_latency": AudioServer.get_output_latency(), "discarded": _cap.get_discarded_frames(), "scenes": _scenes}))
		print("MEASURE capture %d frames of the RunTrack bus written (discarded %d)" % [_cap_buf.size(), _cap.get_discarded_frames()])
	audio.stop()
	quit()
