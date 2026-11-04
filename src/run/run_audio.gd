class_name RunAudio
extends StemTransport
## The continuous run's sound. One silent looping clock stream of exactly 64 beats (the SongClock reads its playhead, so the beat grid
## is one unbroken line through every room and world); each phase's voices (drums, bass, synth, riser or fall) are separate players
## started on the clock at the moments the engine names, with the player's start offset compensated by how late the call is, so a voice
## sits on the grid to within a mix chunk and never drifts (every loop is a whole number of frames long). Bass and Synth are started
## together at the reveal and then keep running whatever the foreground is; the drums run from the phase downbeat.
##
## Gains ramp smoothly towards targets the mix stages set; a treatment (filter, distortion, reverb) is a set of effects on that phase's own
## drum and bass buses (two sets of buses alternate, so the previous phase rings out untouched). Streams are loaded ahead on a thread.

const BUS_PAIRS := [["RunDrumsA", "RunBassA"], ["RunDrumsB", "RunBassB"]]

var cfg: Dictionary
var data: RunData
var beat_s := 60.0 / 174.0
var voice_log: Array = []  # {voice, node, target, lateness_ms, from} for every voice started (tests and the sync check read it)

var _clock_stream: AudioStreamWAV
var _schedule: Array = []  # {t, kind, ...} sorted by t
var _groups: Array = []  # active phase groups: {phase, voices: {name: {player, gain, target}}, buses: [drums, bass]}
var _ramp_s := 0.35
var _fade_s := 0.6
var _requested: Dictionary = {}
var _started := false
var _effect_players: Array = []


func configure(p_data: RunData) -> void:
	data = p_data
	cfg = data.cfg
	beat_s = 60.0 / float(cfg["timing"]["bpm"])
	_ramp_s = float(cfg["mix"]["ramp_s"])
	_fade_s = float(cfg["mix"]["phase_fade_s"])
	loop_seconds = float(cfg["timing"]["phase_beats"]) * beat_s
	_clock_stream = silent_loop(int(cfg["timing"]["phase_beats"]), int(cfg["timing"]["bpm"]))
	if player != null:  # added to the tree before configure()
		player.stream = _clock_stream
	for pair in BUS_PAIRS:
		for b in pair:
			if AudioServer.get_bus_index(b) < 0:
				AudioServer.add_bus()
				var i := AudioServer.bus_count - 1
				AudioServer.set_bus_name(i, b)
				AudioServer.set_bus_send(i, AudioServer.get_bus_name(ensure_music_bus()))


## A silent mono 8-bit loop of exactly `beats` beats: the mix rate is chosen so a beat is a whole number of frames, so the loop has no rounding.
static func silent_loop(beats: int, bpm: int) -> AudioStreamWAV:
	var rate := 8700 if bpm == 174 else 8000  # 60/174 s * 8700 = 3000 frames per beat
	var frames_per_beat := int(round(60.0 / float(bpm) * float(rate)))
	var n := frames_per_beat * beats
	var s := AudioStreamWAV.new()
	s.format = AudioStreamWAV.FORMAT_8_BITS
	s.mix_rate = rate
	s.stereo = false
	var d := PackedByteArray()
	d.resize(n)
	d.fill(0)
	s.data = d
	s.loop_mode = AudioStreamWAV.LOOP_FORWARD
	s.loop_begin = 0
	s.loop_end = n
	return s


func _ready() -> void:
	super._ready()
	if _clock_stream != null:
		player.stream = _clock_stream


func start() -> void:
	_fade_master = 1.0
	_fade_target = 1.0
	_wraps = 0
	_last_raw = 0.0
	_started = true
	player.play(0.0)


func pause() -> void:
	player.stream_paused = true
	for g in _groups:
		for v in g["voices"].values():
			(v["player"] as AudioStreamPlayer).stream_paused = true
	for p in _effect_players:
		if is_instance_valid(p):
			(p as AudioStreamPlayer).stream_paused = true


func resume() -> void:
	player.stream_paused = false
	for g in _groups:
		for v in g["voices"].values():
			(v["player"] as AudioStreamPlayer).stream_paused = false
	for p in _effect_players:
		if is_instance_valid(p):
			(p as AudioStreamPlayer).stream_paused = false


func stop() -> void:
	super.stop()
	for g in _groups:
		for v in g["voices"].values():
			(v["player"] as AudioStreamPlayer).stop()
	_groups.clear()
	_schedule.clear()


## Song time of the sound reaching the listener (what SongClock computes while playing).
func now_t() -> float:
	return playback_position() + AudioServer.get_time_since_last_mix() - AudioServer.get_output_latency()


# --- engine events -> scheduled audio ---------------------------------------------------------------------------------------

## Feeds an engine event (phase_start, mix, reveal, route_window, depleted, run_over); everything is scheduled at the event's own song time.
func on_event(ev: Dictionary) -> void:
	match str(ev["kind"]):
		"phase_start":
			_schedule_add({"t": float(ev["t"]), "kind": "phase", "ev": ev})
		"mix":
			_schedule_add({"t": float(ev["t"]), "kind": "mix", "gains": ev["gains"]})
		"reveal":
			_schedule_add({"t": float(ev["t"]), "kind": "reveal"})
		"route_window":
			_schedule_add({"t": float(ev["t"]), "kind": "effect", "name": ev["effect"]})
		"depleted":
			_schedule_add({"t": float(ev["t"]), "kind": "fade", "seconds": float(ev["fade_s"])})


func _schedule_add(item: Dictionary) -> void:
	_schedule.append(item)
	_schedule.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["t"]) < float(b["t"]))


## Loads a pack's loops ahead of need (a thread); call for every candidate destination as soon as the route window opens.
func preload_pack(pack_id: String) -> void:
	if not data.packs.has(pack_id):
		return
	for key in (data.packs[pack_id]["stems"] as Dictionary):
		var path := _stem_path(pack_id, str(key))
		if not _requested.has(path) and not ResourceLoader.has_cached(path):
			_requested[path] = true
			ResourceLoader.load_threaded_request(path)
	for k in ["riser", "fall"]:
		var ep := str(cfg["effects"][k])
		if not _requested.has(ep) and not ResourceLoader.has_cached(ep):
			_requested[ep] = true
			ResourceLoader.load_threaded_request(ep)


func _stem_path(pack_id: String, key: String) -> String:
	var p: Dictionary = data.packs[pack_id]
	return str(p["dir"]).path_join(str(p["stems"][key]))


func _load(path: String) -> AudioStream:
	if _requested.has(path) and not ResourceLoader.has_cached(path):
		return ResourceLoader.load_threaded_get(path) as AudioStream
	return load(path) as AudioStream


func _loop_copy(path: String) -> AudioStream:
	var src := _load(path)
	var s: AudioStream = src.duplicate() if src != null else null
	if s is AudioStreamWAV:
		var w := s as AudioStreamWAV
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_begin = 0
		w.loop_end = int(round(w.get_length() * float(w.mix_rate)))
	return s


# --- per frame -----------------------------------------------------------------------------------------------------------------

func _process(delta: float) -> void:
	if not _started or player.stream_paused:
		return
	var now := now_t()
	var ttnm := AudioServer.get_time_to_next_mix()
	while not _schedule.is_empty() and float(_schedule[0]["t"]) <= now + ttnm:
		var item: Dictionary = _schedule.pop_front()
		_run(item, now, ttnm)
	var step := delta / maxf(_ramp_s, 0.01)
	var drop: Array = []
	for g in _groups:
		var all_silent := true
		for name in g["voices"]:
			var v: Dictionary = g["voices"][name]
			v["gain"] = move_toward(float(v["gain"]), float(v["target"]), step if not g["fading"] else delta / maxf(_fade_s, 0.01))
			(v["player"] as AudioStreamPlayer).volume_db = _to_db(float(v["gain"]) * (1.0 - float(g.get("duck", 0.0))))
			if float(v["gain"]) > 0.0001 or float(v["target"]) > 0.0:
				all_silent = false
		if g["fading"] and all_silent:
			drop.append(g)
	for g in drop:
		for v in g["voices"].values():
			(v["player"] as AudioStreamPlayer).stop()
			(v["player"] as AudioStreamPlayer).queue_free()
		_groups.erase(g)
	if _fade_master != _fade_target:
		_fade_master = move_toward(_fade_master, _fade_target, _fade_speed * delta)
		for g in _groups:
			g["duck"] = 1.0 - _fade_master


func _run(item: Dictionary, now: float, ttnm: float) -> void:
	match str(item["kind"]):
		"phase":
			_begin_phase(item["ev"], float(item["t"]), now, ttnm)
		"mix":
			var g := _live_group()
			if g.is_empty():
				return
			var gains: Dictionary = item["gains"]
			for name in gains:
				if g["voices"].has(name):
					g["voices"][name]["target"] = float(gains[name])
			g["mix"] = gains
		"reveal":
			var g2 := _live_group()
			if g2.is_empty():
				return
			_start_voice(g2, "bass", float(item["t"]), now, ttnm)
			_start_voice(g2, "other", float(item["t"]), now, ttnm)
			var gains2: Dictionary = g2.get("mix", {})
			for name in ["bass", "other"]:
				g2["voices"][name]["target"] = float(gains2.get(name, 0.0))
		"effect":
			var path := str(cfg["effects"][str(item["name"])])
			var s := _load(path)
			if s != null:
				var p := AudioStreamPlayer.new()
				p.bus = AudioServer.get_bus_name(ensure_music_bus())
				p.stream = s
				p.volume_db = float(cfg["effects"]["gain_db"])
				add_child(p)
				var from := maxf(now + ttnm - float(item["t"]), 0.0)
				p.play(from)
				p.finished.connect(p.queue_free)
				_effect_players.append(p)
				voice_log.append({"voice": str(item["name"]), "node": "", "target": float(item["t"]), "lateness_ms": from * 1000.0, "from": from})
		"fade":
			fade_out(float(item["seconds"]))


func _live_group() -> Dictionary:
	for i in range(_groups.size() - 1, -1, -1):
		if not _groups[i]["fading"]:
			return _groups[i]
	return {}


func _begin_phase(ev: Dictionary, t: float, now: float, ttnm: float) -> void:
	for g in _groups:
		g["fading"] = true
		for v in g["voices"].values():
			v["target"] = 0.0
	var pair: Array = BUS_PAIRS[int(ev["phase"]) % 2]
	_apply_treatment(pair, str(ev["treatment"]))
	var group := {"phase": int(ev["phase"]), "node": str(ev["node"]), "voices": {}, "fading": false, "pack": str(ev["audio"]), "buses": pair, "duck": 1.0 - _fade_master}
	_groups.append(group)
	_start_voice(group, "drums", t, now, ttnm)
	group["voices"]["drums"]["gain"] = 0.0
	group["voices"]["drums"]["target"] = 1.0
	group["mix"] = cfg["stages"][0]["gains"]


func _start_voice(group: Dictionary, name: String, t: float, now: float, ttnm: float) -> void:
	if group["voices"].has(name):
		return
	var path := _stem_path(str(group["pack"]), name)
	var s := _loop_copy(path)
	if s == null:
		push_error("run audio: cannot load " + path)
		return
	var p := AudioStreamPlayer.new()
	p.bus = str((group["buses"] as Array)[0 if name == "drums" else 1]) if name != "other" else AudioServer.get_bus_name(ensure_music_bus())
	if name == "other":
		p.bus = str((group["buses"] as Array)[1])
	p.stream = s
	p.volume_db = SILENT_DB
	add_child(p)
	var from := maxf(now + ttnm - t, 0.0)  # started a little late: begin that far into the loop so it sits on the grid
	p.play(from)
	group["voices"][name] = {"player": p, "gain": 0.0, "target": 0.0, "origin_t": t}
	voice_log.append({"voice": name, "node": str(group["node"]), "target": t, "lateness_ms": from * 1000.0, "from": from})


## A treatment is a few effects per bus: lowpass / highpass (Hz), distort (drive 0..1), reverb (wet 0..1).
func _apply_treatment(pair: Array, name: String) -> void:
	var tr: Dictionary = cfg["treatments"].get(name, {})
	for k in 2:
		var bus := AudioServer.get_bus_index(str(pair[k]))
		while AudioServer.get_bus_effect_count(bus) > 0:
			AudioServer.remove_bus_effect(bus, 0)
		var fx: Dictionary = tr.get("drums" if k == 0 else "bass", {})
		if fx.has("highpass"):
			var hp := AudioEffectHighPassFilter.new()
			hp.cutoff_hz = float(fx["highpass"])
			AudioServer.add_bus_effect(bus, hp)
		if fx.has("lowpass"):
			var lp := AudioEffectLowPassFilter.new()
			lp.cutoff_hz = float(fx["lowpass"])
			AudioServer.add_bus_effect(bus, lp)
		if fx.has("distort"):
			var ds := AudioEffectDistortion.new()
			ds.mode = AudioEffectDistortion.MODE_OVERDRIVE
			ds.drive = clampf(float(fx["distort"]), 0.0, 1.0)
			ds.post_gain = -3.0
			AudioServer.add_bus_effect(bus, ds)
		if fx.has("reverb"):
			var rv := AudioEffectReverb.new()
			rv.wet = clampf(float(fx["reverb"]), 0.0, 1.0)
			rv.dry = 1.0
			AudioServer.add_bus_effect(bus, rv)


## Gains the player currently hears per voice of the newest phase (for tests and the debug line).
func gains() -> Dictionary:
	var g := _live_group()
	var out := {}
	if not g.is_empty():
		for k in g["voices"]:
			out[k] = float(g["voices"][k]["gain"])
	return out


func voice_origin(name: String) -> float:
	var g := _live_group()
	return float(g["voices"][name]["origin_t"]) if not g.is_empty() and g["voices"].has(name) else -1.0


func active_phase_count() -> int:
	return _groups.size()
