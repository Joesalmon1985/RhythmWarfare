extends SceneTree
## THROWAWAY (stage M2.1, the transition spike; docs/music/TRANSITION_SPIKE.md). Plays the experiments of a list (tools/music/spike/make_experiments.py) on the real audio driver and
## records every group's own bus with AudioEffectCapture, so tools/music/spike/analyse_spike.py can measure the alignment, the clicks and the limiter numerically. NOTHING reaches the
## speakers: the spike buses send to a muted sink and the Master bus is muted too (a capture sits before a bus's volume and mute, so it still hears everything).
##   RW_SPIKE_LIST=<experiments.json> RW_SPIKE_OUT=<folder> godot --audio-driver WASAPI --path . -s tools/music/spike/transition_spike.gd
## Per experiment it writes <name>.<bus>.f32 (interleaved stereo float32 from the capture's first frame after the experiment began) and <name>.json (the log).
## The tail is group A (bus SpikeA: PitchShift, HighPass, Delay, Capture), the incoming group B (bus SpikeB: Capture); both send to SpikeSum (Capture pre, HardLimiter -0.3 dB, Capture post).
## Song time is a silent 48 kHz clock loop, as RunAudio's tempo-free clock; items are scheduled with RunAudio's rule (now = position + since last mix - output latency; due when t <= now +
## time to next mix; a group starts as far into its track as the call is late).

const FREE_FRAMES := 1 << 20
const BUSES := ["SpikeA", "SpikeB", "SpikeSumPre", "SpikeSumPost"]

var exps: Array = []
var out_dir := ""
var idx := -1
var e: Dictionary = {}
var phase := ""  # load, run, done
var clock: AudioStreamPlayer
var pa: AudioStreamPlayer
var pb: AudioStreamPlayer
var sa: AudioStreamSynchronized
var sb: AudioStreamSynchronized
var caps: Dictionary = {}  # bus label -> AudioEffectCapture
var bufs: Dictionary = {}  # label -> PackedVector2Array
var pushed0: Dictionary = {}
var fx: Dictionary = {}  # pitch, hp, delay
var bus_a := -1
var clock_wraps := 0
var clock_last := 0.0
var T := 0.0
var started_b := false
var floor_done := false
var flog: Array = []  # per frame
var events: Array = []
var gains_log: Array = []
var pause_state := {}
var wall0 := 0
var seg := -1
var seg_t0 := 0
var mem: Dictionary = {}
var stems_a: Array = []
var stems_b: Array = []
var last_us := 0


func _initialize() -> void:
	Engine.max_fps = 60  # (the game runs at the display rate; the spike must not spin a core)
	exps = JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("RW_SPIKE_LIST")))
	out_dir = OS.get_environment("RW_SPIKE_OUT")
	var only := OS.get_environment("RW_SPIKE_ONLY")
	if only != "":
		exps = exps.filter(func(x: Dictionary) -> bool: return str(x["name"]) in only.split(","))
	FileAccess.open(out_dir.path_join("pid.txt"), FileAccess.WRITE).store_string(str(OS.get_process_id()))
	print("SPIKE driver %s mix_rate %d output_latency %.2f ms pid %d" % [AudioServer.get_driver_name(), AudioServer.get_mix_rate(), AudioServer.get_output_latency() * 1000.0, OS.get_process_id()])
	_buses()
	AudioServer.set_bus_mute(0, true)


func _bus(name: String, send: String) -> int:
	AudioServer.add_bus()
	var i := AudioServer.bus_count - 1
	AudioServer.set_bus_name(i, name)
	AudioServer.set_bus_send(i, send)
	return i


func _cap(i: int, label: String) -> void:
	var c := AudioEffectCapture.new()
	c.buffer_length = 2.0
	AudioServer.add_bus_effect(i, c)
	caps[label] = c


func _buses() -> void:
	var sink := _bus("SpikeSink", "Master")
	AudioServer.set_bus_mute(sink, true)
	var sum := _bus("SpikeSum", "SpikeSink")
	_cap(sum, "SpikeSumPre")
	var lim := AudioEffectHardLimiter.new()
	lim.ceiling_db = -0.3
	AudioServer.add_bus_effect(sum, lim)
	_cap(sum, "SpikeSumPost")
	bus_a = _bus("SpikeA", "SpikeSum")
	var ps := AudioEffectPitchShift.new()
	AudioServer.add_bus_effect(bus_a, ps)  # 0
	var hp := AudioEffectHighPassFilter.new()
	hp.cutoff_hz = 20.0
	AudioServer.add_bus_effect(bus_a, hp)  # 1
	var dl := AudioEffectDelay.new()
	AudioServer.add_bus_effect(bus_a, dl)  # 2
	_cap(bus_a, "SpikeA")  # 3
	fx = {"pitch": ps, "hp": hp, "delay": dl}
	for k in 3:
		AudioServer.set_bus_effect_enabled(bus_a, k, false)
	var b := _bus("SpikeB", "SpikeSum")
	_cap(b, "SpikeB")
	_bus("SpikeClock", "SpikeSink")
	clock = AudioStreamPlayer.new()
	clock.bus = "SpikeClock"
	var s := AudioStreamWAV.new()
	s.format = AudioStreamWAV.FORMAT_8_BITS
	s.mix_rate = int(AudioServer.get_mix_rate())
	var d := PackedByteArray()
	d.resize(FREE_FRAMES)
	s.data = d
	s.loop_mode = AudioStreamWAV.LOOP_FORWARD
	s.loop_end = FREE_FRAMES
	clock.stream = s
	pa = AudioStreamPlayer.new()
	pa.bus = "SpikeA"
	pb = AudioStreamPlayer.new()
	pb.bus = "SpikeB"


func _group(pack: Dictionary, into: Array) -> AudioStreamSynchronized:
	var g := AudioStreamSynchronized.new()
	var st: Array = pack["stems"]
	g.stream_count = st.size()
	into.clear()
	for i in st.size():
		var stream := AudioStreamOggVorbis.load_from_file(str(pack["dir"]).path_join(str(st[i]["stem"])))
		g.set_sync_stream(i, stream)
		g.set_sync_stream_volume(i, linear_to_db(float(st[i]["gain"])))
		into.append(str(st[i]["key"]))
	return g


func clock_pos() -> float:
	var raw := clock.get_playback_position()
	if raw + 1.0 < clock_last:
		clock_wraps += 1
	clock_last = raw
	return raw + clock_wraps * float(FREE_FRAMES) / AudioServer.get_mix_rate()


func _process(_d: float) -> bool:
	if clock.get_parent() == null:
		root.add_child(clock)
		root.add_child(pa)
		root.add_child(pb)
	if phase == "" or phase == "done":
		if phase == "done":
			_finish()
		idx += 1
		if idx >= exps.size():
			print("SPIKE all done")
			return true
		e = exps[idx]
		_load()
		return false
	if phase == "run":
		_run()
	return false


func _load() -> void:
	var m0 := OS.get_static_memory_usage()
	var t0 := Time.get_ticks_usec()
	sa = _group(e["out"], stems_a)
	var t1 := Time.get_ticks_usec()
	var m1 := OS.get_static_memory_usage()
	sb = _group(e["inc"], stems_b) if e.has("inc") else null
	var m2 := OS.get_static_memory_usage()
	mem = {"one_pack_mb": float(m1 - m0) / 1048576.0, "two_packs_mb": float(m2 - m0) / 1048576.0, "load_ms_a": float(t1 - t0) / 1000.0, "load_ms_b": float(Time.get_ticks_usec() - t1) / 1000.0}
	pa.stream = sa
	pa.pitch_scale = 1.0
	pa.volume_db = 0.0
	pb.stream = sb
	pb.volume_db = 0.0
	pb.pitch_scale = 1.0
	for k in 3:
		AudioServer.set_bus_effect_enabled(bus_a, k, false)
	(fx["hp"] as AudioEffectHighPassFilter).cutoff_hz = 20.0
	flog = []
	events = []
	gains_log = []
	started_b = false
	floor_done = false
	pause_state = {"n": 0, "paused": false, "next": 0.0}
	seg = -1
	T = float(e.get("pre_s", 3.0))
	clock_wraps = 0
	clock_last = 0.0
	# everything starts in one call: the clock and the outgoing group share their first mix (RunTrackAudio.start_with_clock)
	AudioServer.lock()
	for label in caps:
		(caps[label] as AudioEffectCapture).clear_buffer()
		pushed0[label] = (caps[label] as AudioEffectCapture).get_pushed_frames()
		bufs[label] = PackedVector2Array()
	clock.play(0.0)
	var mode := str(e["mode"])
	if mode != "cpu":
		pa.play(float(e["out_t_at_T"]) - T)
	AudioServer.unlock()
	events.append({"kind": "start_a", "from": float(e["out_t_at_T"]) - T, "t": 0.0})
	wall0 = Time.get_ticks_usec()
	last_us = 0
	print("SPIKE start %s (%s) load %.0f ms + %.0f ms, static memory +%.1f MB one pack, +%.1f MB two" % [e["name"], mode, mem["load_ms_a"], mem["load_ms_b"], mem["one_pack_mb"], mem["two_packs_mb"]])
	phase = "run"


func _now() -> float:
	return clock_pos() + AudioServer.get_time_since_last_mix() - AudioServer.get_output_latency()


func _cosf(x: float) -> float:
	return cos(PI * 0.5 * clampf(x, 0.0, 1.0))


## The tail's gain for stem `key` at song time t (MUSIC_TRANSITIONS.md 4.3).
func _tail_gain(key: String, t: float) -> float:
	if t < T:
		return 1.0
	var b := (t - T) / float(e["bar_in"])
	var mode := str(e["mode"])
	var kind := "bass" if key == "bass" else ("linger" if key in ["other", "vocals"] else "rhythm")
	if mode == "blend":
		match kind:
			"bass":
				return _cosf(b)
			"rhythm":
				return _cosf(b / 2.0)
			_:
				return 1.0 if b < 2.0 else _cosf((b - 2.0) / (float(e["W"]) - 2.0))
	if mode == "echo_out":
		if kind == "linger":
			return _cosf(b)
		return _cosf(b / 0.125)
	return 1.0


func _drain() -> void:
	for label in caps:
		var c: AudioEffectCapture = caps[label]
		var n := c.get_frames_available()
		if n > 0:
			bufs[label].append_array(c.get_buffer(n))


func _run() -> void:
	var now_us := Time.get_ticks_usec()
	AudioServer.lock()
	var cp := clock_pos()
	var row := [float(now_us - wall0) / 1e6, cp, pa.get_playback_position() if pa.playing else -1.0, pb.get_playback_position() if pb.playing else -1.0]
	for label in BUSES:
		row.append((caps[label] as AudioEffectCapture).get_pushed_frames() - int(pushed0[label]))
	AudioServer.unlock()
	row.append(float(now_us - last_us) / 1000.0 if last_us > 0 else 0.0)
	last_us = now_us
	flog.append(row)
	_drain()
	var mode := str(e["mode"])
	if mode == "cpu":
		_cpu_segments()
		return
	var now := _now()
	var ttnm := AudioServer.get_time_to_next_mix()
	# pauses (Q1): from T + 3 s, pause everything for 0.3 s of wall time, play 0.7 s, ten times
	var np := int(e.get("pauses", 0))
	if np > 0 and int(pause_state["n"]) < np and now > T + 3.0:
		var w := float(now_us - wall0) / 1e6
		if not bool(pause_state["paused"]) and w >= float(pause_state["next"]):
			for p in [clock, pa, pb]:
				p.stream_paused = true
			pause_state["paused"] = true
			pause_state["next"] = w + 0.3
			events.append({"kind": "pause", "wall": w, "t": now})
		elif bool(pause_state["paused"]) and w >= float(pause_state["next"]):
			AudioServer.lock()
			for p in [clock, pa, pb]:
				p.stream_paused = false
			AudioServer.unlock()
			pause_state["paused"] = false
			pause_state["n"] = int(pause_state["n"]) + 1
			pause_state["next"] = w + 0.7
			events.append({"kind": "resume", "wall": w, "t": now})
	if bool(pause_state["paused"]):
		return
	# the boundary: the incoming group starts on T at its entry time, late by as much as the call is late; the tail's rate and effects switch in the same pass
	if not started_b and T <= now + ttnm:
		var late := maxf(now + ttnm - T, 0.0)
		if mode != "identity":
			pb.play(float(e["in_entry_t"]) + late)
		pa.pitch_scale = float(e["rate"])
		if bool(e.get("pitch_shift", false)):
			(fx["pitch"] as AudioEffectPitchShift).pitch_scale = 1.0 / float(e["rate"])
			AudioServer.set_bus_effect_enabled(bus_a, 0, true)
		if mode == "blend":
			AudioServer.set_bus_effect_enabled(bus_a, 1, true)
		if mode == "echo_out" and bool(e.get("effects", true)):
			var dl: AudioEffectDelay = fx["delay"]
			dl.dry = 1.0
			dl.tap1_active = false
			dl.tap2_active = false
			dl.feedback_active = true
			dl.feedback_delay_ms = 0.75 * float(e["beat_out"]) * 1000.0
			dl.feedback_level_db = linear_to_db(0.4)
			AudioServer.set_bus_effect_enabled(bus_a, 2, true)
			AudioServer.set_bus_effect_enabled(bus_a, 1, true)
		started_b = true
		events.append({"kind": "boundary", "t": T, "now": now, "ttnm": ttnm, "late": late, "clock_pos": cp, "since": AudioServer.get_time_since_last_mix(), "from_b": float(e.get("in_entry_t", 0.0)) + late})
	# the tail's gains, every frame, as functions of song time
	if mode in ["blend", "echo_out"] and not floor_done:
		var g: Array = []
		for i in stems_a.size():
			var gl := _tail_gain(str(stems_a[i]), now) * float(e["out"]["stems"][i]["gain"])
			sa.set_sync_stream_volume(i, maxf(linear_to_db(maxf(gl, 1e-6)), -80.0) if gl > 0.001 else -80.0)
			g.append(gl)
		gains_log.append([now, g])
		if now >= T:
			var b := (now - T) / float(e["bar_in"])
			var hp: AudioEffectHighPassFilter = fx["hp"]
			if mode == "blend":
				hp.cutoff_hz = 20.0 * pow(250.0 / 20.0, clampf(b / 4.0, 0.0, 1.0))
			elif bool(e.get("effects", true)):
				hp.cutoff_hz = 200.0 * pow(2000.0 / 200.0, clampf(b / float(e["W"]), 0.0, 1.0))
	# the hard floor at complete_t: the tail player stops and its bus effects go off (echo repeats included)
	if mode in ["blend", "echo_out"] and not floor_done and now >= T + float(e["complete_s"]):
		pa.volume_db = -80.0
		pa.stop()
		for k in 3:
			AudioServer.set_bus_effect_enabled(bus_a, k, false)
		floor_done = true
		events.append({"kind": "floor", "t": now})
	if now >= T + float(e["post_s"]):
		phase = "done"


## CPU (the process's CPU time is sampled from outside by tools/music/spike/cpu_sampler.py): segments of seg_s seconds, each logged with its wall time.
func _cpu_segments() -> void:
	var w := float(Time.get_ticks_usec() - wall0) / 1e6
	var n := int(floor(w / float(e["seg_s"])))
	if n == seg:
		return
	seg = n
	var names := ["clock only", "one group (4 stems)", "two groups (4 + 5 stems)", "two groups, tail pitch_scale", "plus PitchShift on the tail bus", "plus HighPass and Delay", "end"]
	events.append({"kind": "segment", "n": n, "name": names[mini(n, names.size() - 1)], "unix": Time.get_unix_time_from_system(), "wall": w})
	print("SPIKE cpu segment %d %s at unix %.3f" % [n, names[mini(n, names.size() - 1)], Time.get_unix_time_from_system()])
	match n:
		1:
			pa.play(float(e["out_t_at_T"]))
		2:
			pb.play(float(e["in_entry_t"]))
		3:
			pa.pitch_scale = float(e["rate"])
		4:
			(fx["pitch"] as AudioEffectPitchShift).pitch_scale = 1.0 / float(e["rate"])
			AudioServer.set_bus_effect_enabled(bus_a, 0, true)
		5:
			AudioServer.set_bus_effect_enabled(bus_a, 1, true)
			AudioServer.set_bus_effect_enabled(bus_a, 2, true)
		6:
			phase = "done"


func _finish() -> void:
	_drain()
	pa.stop()
	pb.stop()
	clock.stop()
	var name := str(e["name"])
	for label in BUSES:
		if str(e["mode"]) == "cpu":
			break
		var f := FileAccess.open(out_dir.path_join("%s.%s.f32" % [name, label]), FileAccess.WRITE)
		f.store_buffer((bufs[label] as PackedVector2Array).to_byte_array())
		f.close()
	var discarded := {}
	for label in caps:
		discarded[label] = (caps[label] as AudioEffectCapture).get_discarded_frames()
	var log := {"exp": e, "T": T, "events": events, "frames": flog, "gains": gains_log, "mem": mem, "discarded": discarded, "mix_rate": AudioServer.get_mix_rate(),
		"output_latency": AudioServer.get_output_latency(), "driver": AudioServer.get_driver_name(), "stems_a": stems_a, "stems_b": stems_b}
	FileAccess.open(out_dir.path_join(name + ".json"), FileAccess.WRITE).store_string(JSON.stringify(log))
	var ft := flog.map(func(r: Array) -> float: return float(r[r.size() - 1]))
	ft.sort()
	print("SPIKE done %s: %d frames, worst frame %.1f ms, captured %d frames on A, discarded %s" % [name, flog.size(), ft[-1] if not ft.is_empty() else 0.0, (bufs["SpikeA"] as PackedVector2Array).size(), str(discarded)])
	pa.stream = null
	pb.stream = null
	sa = null
	sb = null
	for label in bufs:
		bufs[label] = PackedVector2Array()
