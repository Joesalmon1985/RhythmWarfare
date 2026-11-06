extends SceneTree
## A measurement, not a test: a real track scene played in real time through RunAudio and RunTrackAudio, with the engine driven from the song clock (no pads: cues are missed, voices mute and
## come back, which changes nothing measured here). Needs packs: RW_TRACKS_DIR=<packs folder> on the command line (never in the suite). Prints one MEASURE line per figure:
##   load    the first scene's stems decoded on a worker thread (ms), then every other pack decoded once (ms each), and the static memory before and after
##   entry   the worst frame (wall time between frames) within half a second of each track scene's start, and the time the start item itself took
##   sync    the track group's playhead against the song clock: (track position - clock position) - (track_t0 - t0), sampled every frame from 2 s after the start; max, mean and the drift per 100 s
## Name the audio driver with the figures: the Dummy driver mixes in 88.5 ms chunks on a thread, a device driver in 5 to 20 ms.
##   godot --audio-driver Dummy --path . -s tests/fixtures/track_scenes/measure_track_audio.gd     (RW_MEASURE_S: seconds to play, default 100; RW_RUN_START: the scene, default warehouse)

var data: RunData
var audio: RunAudio
var engine: RunEngine
var _t_end := 100.0
var _last_us := 0
var _frames: Array = []  # [song t, frame ms]
var _starts: Array = []  # song t of each track start
var _dev: Array = []  # [song t, deviation s]
var _start_cost_us := 0
var _mem0 := 0
var _next_cue := 0
var _cost_t := 0.0


func _initialize() -> void:
	_t_end = float(OS.get_environment("RW_MEASURE_S")) if OS.has_environment("RW_MEASURE_S") else 100.0
	data = RunData.load_default()
	printerr("measure: data loaded, %d errors" % data.errors.size())
	if data.track_scenes == null:
		print("MEASURE none: no track scenes (set RW_TRACKS_DIR)")
		quit(1)
		return
	audio = RunAudio.new()
	root.add_child(audio)


## (in the first frame: the nodes are in the tree only now)
func _setup() -> void:
	var start := OS.get_environment("RW_RUN_START") if OS.has_environment("RW_RUN_START") else "warehouse"
	_mem0 = OS.get_static_memory_usage()
	printerr("measure: configure")
	audio.configure(data)
	engine = RunEngine.new(data)
	engine.hotspots = RunHotspots.new(data, {}, {})
	engine.track_gate = audio.track.is_ready
	audio.track.notes_fn = func() -> Array: return engine.level.notes
	printerr("measure: prepare ", start, " ", str(data.track_scenes.plan_of(start).get("track", "(no track)")))
	var m_before := OS.get_static_memory_usage()
	var ms := audio.track.prepare(data, start)
	print("MEASURE memory static %+.1f MB for the first scene's stems in memory" % [float(OS.get_static_memory_usage() - m_before) / 1048576.0])
	print("MEASURE load first scene %s: %.1f ms (worker thread, waited for before the start), mix rate %d, driver %s" % [start, ms, AudioServer.get_mix_rate(), AudioServer.get_driver_name() if AudioServer.has_method("get_driver_name") else "?"])
	engine.begin(start)
	audio.track.warm([data])  # (as RunPlay does: the scene plans on a worker thread)
	for ev in engine.update(-0.001):
		audio.on_event(ev)
	audio.start()


func _process(_delta: float) -> bool:
	if audio == null:
		return true
	if engine == null:
		_setup()
		return false
	var now_us := Time.get_ticks_usec()
	var t := audio.now_t()
	if _frames.size() % 120 == 0:
		printerr("measure: frame %d song t %.2f clock playing %s pos %.3f" % [_frames.size(), t, str(audio.player.playing), audio.player.get_playback_position()])
	if _last_us > 0:
		_frames.append([t, float(now_us - _last_us) / 1000.0])
	_last_us = now_us
	var t0 := Time.get_ticks_usec()
	while _next_cue < engine.level.notes.size() and float(engine.level.notes[_next_cue]["time"]) <= t:  # a perfect player (taps on the cue's time; a hold held to its end), so the run goes on
		var n: Dictionary = engine.level.notes[_next_cue]
		engine.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
		engine.release(int(n["pad"]), float(n["end_time"]) if str(n["type"]) == "hold" else float(n["time"]) + 0.05, int(n["pad"]))
		_next_cue += 1
	for ev in engine.update(t):
		audio.on_event(ev)
		if str(ev["kind"]) == "track_start":
			_starts.append(float(ev["t"]))
		if str(ev["kind"]) == "route_window":
			audio.track.prefetch_for(data, engine.node_id)
	var cost := Time.get_ticks_usec() - t0
	if cost > _start_cost_us:
		_start_cost_us = cost
		_cost_t = t
	var g := audio.track.live()
	if not g.is_empty() and t > float(g["t0"]) + 2.0 and float(g["position"]) >= 0.0:
		var clock_pos := audio.playback_position()
		_dev.append([t, (float(g["position"]) - clock_pos) - (float(g["track_t0"]) - float(g["t0"])), float(g["t0"])])
	if t >= _t_end:
		_report()
		return true
	return false


func _report() -> void:
	for l in audio.track.load_log:
		print("MEASURE load %s: %.1f ms for %d stems (%s)" % [l["track"], float(l["ms"]), int(l["stems"]), "ok" if bool(l["ok"]) else str(l["error"])])
	print("MEASURE memory static %+.1f MB with the packs in memory (%d cached)" % [float(OS.get_static_memory_usage() - _mem0) / 1048576.0, audio.track.cached().size()])
	for s in _starts:
		var worst := 0.0
		for f in _frames:
			if absf(float(f[0]) - float(s)) <= 0.5:
				worst = maxf(worst, float(f[1]))
		print("MEASURE entry at t=%.3f: worst frame %.1f ms within 0.5 s" % [float(s), worst])
	var worst_f: Array = [0.0, 0.0]
	for f in _frames:
		if float(f[1]) > float(worst_f[1]):
			worst_f = f
	print("MEASURE worst frame %.1f ms at song t=%.2f" % [float(worst_f[1]), float(worst_f[0])])
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
	print("MEASURE track log ", JSON.stringify(audio.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) in ["start", "seek", "end", "not_ready", "unloaded"])))
	audio.stop()
	quit()
