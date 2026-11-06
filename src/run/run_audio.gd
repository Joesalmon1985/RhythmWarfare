class_name RunAudio
extends StemTransport
## The continuous run's sound. One silent looping clock stream of exactly 64 beats (the SongClock reads its playhead, so the beat grid
## is one unbroken line through every room and world); each phase's voices (drums, bass, synth, riser or fall) are separate players
## started on the clock at the moments the engine names, with the player's start offset compensated by how late the call is, so a voice
## sits on the grid to within a mix chunk and never drifts (every loop is a whole number of frames long). Bass and Synth are started
## together at the reveal and then keep running whatever the foreground is; the drums run from the phase downbeat.
##
## A scene may play several LAPS (docs/CONTINUOUS_RUN.md "Two laps"): the next lap is no phase change here. The engine's `lap_start` event schedules nothing: the voices simply go on (every loop tiles a lap), the gains stay
## where the stage mix put them, and a bass first revealed on the lap's downbeat is the ordinary `reveal` item.
##
## A scene may play an ARRANGEMENT (content/music/arrangements, resolved by RunData into node.sections): two 8-bar sections or one 16-bar over its 64-beat phase.
## A section switch is another scheduled item on the same grid: at the section's first beat the previous section's voices stop and the new pack's voices start with the same
## lateness compensation as a phase start (drums from the section downbeat; bass and synth too once the bass has been revealed), so a voice group per section, no restart of
## the clock, no gap. The section's mix recipe scales the phase mix (stage gain x recipe gain); the phase mix stays the gameplay.
##
## A PATH (content/paths/<id>, docs/CONTINUOUS_RUN.md "Paths") runs at its own tempo. Its start is a TEMPO HANDOFF: on the downbeat the clock stream is swapped (`schedule_clock_swap`): the 64-beat silent loop of
## the path's tempo replaces the old one, the song time stays one unbroken line (`song_base` becomes the downbeat, the wrap count restarts), the new engine's first phase starts on the same downbeat, and the old
## phase's voices fade out through the usual fade of a phase change. The way back is the same swap in reverse.
##
## Gains ramp smoothly towards targets the mix stages set; a treatment (filter, distortion, reverb) is a set of effects on that phase's own
## drum and bass buses (two sets of buses alternate, so the previous phase rings out untouched). Streams are loaded ahead on a thread.

## THE BASS BUS AND THE RUN'S LEVEL (docs/HANDOVER.md "Audio polish"): the bass voice alone plays through a tone bus per pair (high-pass, low shelf, a soft WAVESHAPE saturation and a post gain from the scene's
## resolved `bass_bus`, so it reads on a phone speaker that cannot play the sub) and then into the pair's bass bus with the synth (the treatment); every run bus ends in `RunMix`, whose volume is `mix.gain_db`
## (the run's level: a path may sit lower or higher than the 174 run). A scene's bass may CARRY into the next scene's drums-alone block (`mix.carry_bass`) when the two play the same music family.
const BUS_PAIRS := [["RunDrumsA", "RunBassA"], ["RunDrumsB", "RunBassB"]]
const TONE_BUSES := ["RunBassToneA", "RunBassToneB"]  # the bass voice of pair k, before RunBassA/B
const MIX_BUS := "RunMix"

var cfg: Dictionary
var data: RunData
var beat_s := 60.0 / 174.0
var voice_log: Array = []  # {voice, node, target, lateness_ms, from} for every voice started (tests and the sync check read it)

var _clock_stream: AudioStreamWAV
var _schedule: Array = []  # {t, kind, ...} sorted by t, then by the order they were added (a clock swap goes before the phase that starts on it)
var _seq := 0
var clock_log: Array = []  # [{t, bpm, beat_s, from, frames_per_beat, rate}] every clock swap (tests and the recording check read it)
var _groups: Array = []  # active phase groups: {phase, voices: {name: {player, gain, target}}, buses: [drums, bass]}
var _ramp_s := 0.35
var _dip := false  # a hotspot outcome's music "dip" is live: the non-drum voices aim lower (mix.dip_gain) until it ends
const DIP_GAIN := 0.35  # the defaults when run.json `mix` has no dip_gain / dip_beats (the values before the audio polish)
const DIP_BEATS := 8.0  # how long the dip lasts, from the commit's beat
var _fade_s := 0.6
var _requested: Dictionary = {}
var _started := false
var _effect_players: Array = []
var track: RunTrackAudio  # TRACK SCENES (docs/RUN_TRACK_SCENES.md "Audio"): a whole recorded track under a track scene instead of its loops (src/run/run_track_audio.gd); every event is handed to it


func configure(p_data: RunData) -> void:
	data = p_data
	cfg = data.cfg
	retarget(p_data)
	tempo_free = p_data.track_scenes != null or tempo_free
	if tempo_free:
		_clock_stream = free_clock()
		loop_seconds = float(_clock_stream.loop_end) / float(_clock_stream.mix_rate)
	else:
		loop_seconds = float(cfg["timing"]["phase_beats"]) * beat_s
		_clock_stream = silent_loop(int(cfg["timing"]["phase_beats"]), int(cfg["timing"]["bpm"]))
	if player != null:  # added to the tree before configure()
		player.stream = _clock_stream
	_ensure_bus(MIX_BUS, AudioServer.get_bus_name(ensure_music_bus()))
	for pair in BUS_PAIRS:
		for b in pair:
			_ensure_bus(str(b), MIX_BUS)
	for k in 2:
		_ensure_bus(str(TONE_BUSES[k]), str(BUS_PAIRS[k][1]))
	apply_mix_level()
	if track != null:
		track.configure(cfg)


## A bus that sends to `send`, after it in the bus list (a bus can only send to one mixed after it, i.e. with a lower index).
static func _ensure_bus(bus_name: String, send: String) -> void:
	if AudioServer.get_bus_index(bus_name) < 0:
		AudioServer.add_bus()
		AudioServer.set_bus_name(AudioServer.bus_count - 1, bus_name)
	if AudioServer.get_bus_index(bus_name) < AudioServer.get_bus_index(send):
		AudioServer.move_bus(AudioServer.get_bus_index(bus_name), AudioServer.bus_count)
	AudioServer.set_bus_send(AudioServer.get_bus_index(bus_name), send)


## The run's level (`mix.gain_db`) on RunMix: a plain bus volume (linear, no delay, so the clock and the sound stay where they were).
func apply_mix_level() -> void:
	var i := AudioServer.get_bus_index(MIX_BUS)
	if i >= 0:
		AudioServer.set_bus_volume_db(i, float(cfg.get("mix", {}).get("gain_db", 0.0)))


func dip_gain() -> float:
	return float(cfg.get("mix", {}).get("dip_gain", DIP_GAIN))


func dip_beats() -> float:
	return float(cfg.get("mix", {}).get("dip_beats", DIP_BEATS))


## The run's tempo and mix settings come from `p_data` (the main run's, or a path's after a handoff). Nothing is started or stopped: the clock stream (and `loop_seconds`) is swapped by `schedule_clock_swap`.
func retarget(p_data: RunData) -> void:
	data = p_data
	cfg = data.cfg
	beat_s = 60.0 / float(cfg["timing"]["bpm"])
	_ramp_s = float(cfg["mix"]["ramp_s"])
	_fade_s = float(cfg["mix"]["phase_fade_s"])
	if track != null:
		track.configure(cfg)


## The clock's mix rate for a tempo: one where a beat is a whole number of frames (60 / bpm * rate is an integer), so a 64-beat loop has no rounding at all. 174, 124, 140 and 145 BPM have the rates
## the paths were planned with (8700, 8680, 8400, 8700); any other whole tempo gets the smallest rate from 8000 Hz up whose beat is whole.
const CLOCK_RATES := {174: 8700, 124: 8680, 140: 8400, 145: 8700}


static func clock_rate(bpm: int) -> int:
	if CLOCK_RATES.has(bpm):
		return int(CLOCK_RATES[bpm])
	var g := _gcd(bpm, 60)
	var step := bpm / g  # rate * 60 / bpm is whole exactly when the rate is a multiple of bpm / gcd(bpm, 60)
	return ((8000 + step - 1) / step) * step


static func _gcd(a: int, b: int) -> int:
	return a if b == 0 else _gcd(b, a % b)


## Frames in one beat of the clock loop at `bpm` (a whole number by construction).
static func frames_per_beat(bpm: int) -> int:
	return int(round(60.0 / float(bpm) * float(clock_rate(bpm))))


## THE TEMPO-FREE CLOCK (track scenes on, M1.4): one silent loop at the mix rate itself (48,000 Hz here), FREE_FRAMES long, never swapped. A clock stream at another rate is resampled with a
## truncated fixed-point step: the 8,700 Hz loop runs 7.7e-5 slow against a 48 kHz stem (measured on the Dummy driver, 40 s: 7.7 ms per 100 s), which a whole recorded track playing for up to
## 176 s without a restart would hear as 13 ms of drift between its cues and its audio. At the mix rate the step is exactly 1, so song time and the track's playhead advance together, sample for
## sample. Nothing reads the loop's length but the wrap counting (StemTransport.playback_position), so it need not be a whole number of beats: every tempo (a float) is just a beat length on
## the engine's grid, and neither a track scene nor a path hand-off swaps the stream (song time never jumps). With track scenes off the run keeps its per-tempo loops exactly as before.
const FREE_FRAMES := 1 << 20  # 21.85 s at 48 kHz
var tempo_free := false


static func free_clock() -> AudioStreamWAV:
	var rate := int(AudioServer.get_mix_rate())
	var s := AudioStreamWAV.new()
	s.format = AudioStreamWAV.FORMAT_8_BITS
	s.mix_rate = rate
	s.stereo = false
	var d := PackedByteArray()
	d.resize(FREE_FRAMES)
	d.fill(0)
	s.data = d
	s.loop_mode = AudioStreamWAV.LOOP_FORWARD
	s.loop_begin = 0
	s.loop_end = FREE_FRAMES
	return s


## A silent mono 8-bit loop of exactly `beats` beats: the mix rate is chosen so a beat is a whole number of frames, so the loop has no rounding.
static func silent_loop(beats: int, bpm: int) -> AudioStreamWAV:
	var rate := clock_rate(bpm)  # 60/174 s * 8700 = 3000 frames per beat
	var fpb := frames_per_beat(bpm)
	var n := fpb * beats
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
	track = RunTrackAudio.new()
	track.name = "TrackAudio"
	track.run_audio = self
	add_child(track)
	if cfg != null and not cfg.is_empty():
		track.configure(cfg)


func start() -> void:
	_fade_master = 1.0
	_fade_target = 1.0
	_wraps = 0
	_last_raw = 0.0
	_dip = false
	_started = true
	player.play(0.0)
	if track != null:
		track.start_with_clock()


## Pause and resume set every player in one AudioServer.lock, so the clock, the track groups (a tail and the incoming one in a blend) and the loops stop and go on in the same mix chunk.
func pause() -> void:
	AudioServer.lock()
	_pause_all()
	AudioServer.unlock()


func resume() -> void:
	AudioServer.lock()
	_resume_all()
	AudioServer.unlock()


func _pause_all() -> void:
	player.stream_paused = true
	for g in _groups:
		for v in g["voices"].values():
			(v["player"] as AudioStreamPlayer).stream_paused = true
	for p in _effect_players:
		if is_instance_valid(p):
			(p as AudioStreamPlayer).stream_paused = true
	if track != null:
		track.pause()


func _resume_all() -> void:
	player.stream_paused = false
	for g in _groups:
		for v in g["voices"].values():
			(v["player"] as AudioStreamPlayer).stream_paused = false
	for p in _effect_players:
		if is_instance_valid(p):
			(p as AudioStreamPlayer).stream_paused = false
	if track != null:
		track.resume()


func stop() -> void:
	super.stop()
	for g in _groups:
		for v in g["voices"].values():
			(v["player"] as AudioStreamPlayer).stop()
	_groups.clear()
	_schedule.clear()
	_watch.clear()
	if track != null:
		track.stop()


## Song time of the sound reaching the listener (what SongClock computes while playing).
func now_t() -> float:
	return playback_position() + AudioServer.get_time_since_last_mix() - AudioServer.get_output_latency()


# --- engine events -> scheduled audio ---------------------------------------------------------------------------------------

## Feeds an engine event (phase_start, mix, reveal, route_window, depleted, run_over); everything is scheduled at the event's own song time.
func on_event(ev: Dictionary) -> void:
	if track != null:
		track.on_event(ev)
	match str(ev["kind"]):
		"phase_start":
			_schedule_add({"t": float(ev["t"]), "kind": "phase", "ev": ev})
			if ev.has("track"):  # a track scene: the track plays (RunTrackAudio), no loops start; the scene before fades as at any phase change
				return
			var secs: Array = (data.nodes.get(str(ev["node"]), {}) as Dictionary).get("sections", [])  # (the Bassment's phase_start names node "trial", which is no scene of the run: no sections)
			for i in range(1, secs.size()):
				_schedule_add({"t": float(ev["t"]) + float(secs[i]["start_beat"]) * beat_s, "kind": "section", "phase": int(ev["phase"]), "index": i, "section": secs[i]})
			for sec in secs:
				preload_pack(str(sec["pack"]))
		"mix":
			_schedule_add({"t": float(ev["t"]), "kind": "mix", "gains": ev["gains"]})
		"reveal":
			_schedule_add({"t": float(ev["t"]), "kind": "reveal"})
		"hotspot_commit":  # outcome music "dip": the bass and synth sink for a couple of bars, the drums carry on (the gain ramps do the easing)
			if str((ev["outcome"] as Dictionary).get("music", "")) == "dip":
				_schedule_add({"t": float(ev["t"]), "kind": "dip", "on": true})
				_schedule_add({"t": float(ev["t"]) + dip_beats() * beat_s, "kind": "dip", "on": false})
		"route_window":
			if not ev.has("track"):  # (no riser or fall over a recorded track: they are cut for the loops, and would sound on every open lap)
				_schedule_add({"t": float(ev["t"]), "kind": "effect", "name": ev["effect"]})
		"depleted":
			_schedule_add({"t": float(ev["t"]), "kind": "fade", "seconds": float(ev["fade_s"])})


func _schedule_add(item: Dictionary) -> void:
	item["seq"] = _seq
	_seq += 1
	_schedule.append(item)
	_schedule.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["t"]) < float(b["t"]) if float(a["t"]) != float(b["t"]) else int(a["seq"]) < int(b["seq"]))


## The tempo handoff: on the downbeat `t` (song time) the clock stream becomes the 64-beat silent loop of `p_data`'s tempo. Call it before the new engine's events are fed (`retarget` is done here, so that
## the new phase's sections are scheduled on the new beat).
func schedule_clock_swap(p_data: RunData, t: float) -> void:
	retarget(p_data)
	_schedule_add({"t": t, "kind": "clock", "bpm": int(p_data.cfg["timing"]["bpm"]), "beats": int(p_data.cfg["timing"]["phase_beats"])})


## Loads a pack's loops ahead of need (a thread); call for every candidate destination as soon as the route window opens.
func preload_pack(pack_id: String, from_data: RunData = null) -> void:
	var d := from_data if from_data != null else data  # (a portal's path: its start pack is loaded ahead from the path's own data)
	if not d.packs.has(pack_id):
		return
	for key in (d.packs[pack_id]["stems"] as Dictionary):
		var path := _stem_path(pack_id, str(key), d)
		if not _requested.has(path) and not ResourceLoader.has_cached(path):
			_requested[path] = true
			ResourceLoader.load_threaded_request(path)
	for k in ["riser", "fall"]:
		var ep := str(cfg["effects"][k])
		if not _requested.has(ep) and not ResourceLoader.has_cached(ep):
			_requested[ep] = true
			ResourceLoader.load_threaded_request(ep)


func _stem_path(pack_id: String, key: String, from_data: RunData = null) -> String:
	var p: Dictionary = (from_data if from_data != null else data).packs[pack_id]
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
	if track != null:
		track.step(now, ttnm)
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
	check_silence(now)


func _run(item: Dictionary, now: float, ttnm: float) -> void:
	match str(item["kind"]):
		"clock":
			_swap_clock(item, now, ttnm)
		"phase":
			_begin_phase(item["ev"], float(item["t"]), now, ttnm)
			_arm_watch(float(item["t"]))
		"section":
			_switch_section(item, now, ttnm)
		"mix":
			var g := _live_group()
			if g.is_empty():
				return
			var gains: Dictionary = item["gains"]
			for name in gains:
				if g["voices"].has(name):
					g["voices"][name]["target"] = _target_gain(g, name, gains)
			g["mix"] = gains
		"reveal":
			var g2 := _live_group()
			if g2.is_empty():
				return
			_start_voice(g2, "bass", float(item["t"]), now, ttnm)
			_start_voice(g2, "other", float(item["t"]), now, ttnm)
			var gains2: Dictionary = g2.get("mix", {})
			for name in ["bass", "other"]:
				if g2["voices"].has(name):
					g2["voices"][name]["target"] = _target_gain(g2, name, gains2)
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
		"dip":
			_dip = bool(item["on"])
			for g3 in _groups:
				if bool(g3.get("carry", false)):  # a carried bass sinks and comes back like the live voices
					g3["voices"]["bass"]["target"] = _carry_target()
					continue
				if g3["fading"]:
					continue
				for name in g3["voices"]:
					if float(g3["voices"][name]["target"]) > 0.0:  # a voice that is muted (not revealed yet, mixed out) stays so
						g3["voices"][name]["target"] = _target_gain(g3, name, g3.get("mix", {}))
		"fade":
			fade_out(float(item["seconds"]))
		"carry_end":
			_end_carry()


## Replaces the clock stream on the downbeat: the new loop starts as far in as the call is late, the song time restarts counting from the downbeat (so it stays one unbroken line), the old tempo's
## phase fades through the next `phase` item exactly as in a world change.
func _swap_clock(item: Dictionary, now: float, ttnm: float) -> void:
	var t := float(item["t"])
	var bpm := int(item["bpm"])
	if tempo_free:  # the clock knows no tempo: the hand-off changes the run's level only, song time goes on untouched
		apply_mix_level()
		clock_log.append({"period": 0.0, "t": t, "bpm": bpm, "beat_s": 60.0 / float(bpm), "from": 0.0, "frames_per_beat": 0, "rate": _clock_stream.mix_rate, "loop_seconds": loop_seconds, "tempo_free": true})
		return
	_clock_stream = silent_loop(int(item["beats"]), bpm)
	var from := maxf(now + ttnm - t, 0.0)
	# The new stream's position is reported, like every stream's, as of the END of the last mixed chunk, and its first chunk starts at `from`: after the first mix it reads from + one mix period, a
	# period ahead of the old line (measured: 88.5 ms with the dummy driver, the "88 ms jump" of the first in-path phase change, which the clock then carried into every cue and voice of
	# the new run). The song time stays one unbroken line only if the base is lowered by that period (docs/paths/gospel.md "The Stage 2 audio finding").
	var period := mix_period(ttnm)
	song_base = t - period
	loop_seconds = float(item["beats"]) * 60.0 / float(bpm)  # (the old loop's length is kept until now: its last wrap, at this very downbeat, is counted with it)
	_wraps = 0
	_last_raw = 0.0
	player.stream = _clock_stream
	player.play(from)
	player.stream_paused = false
	apply_mix_level()  # the other run's level, from its downbeat
	clock_log.append({"period": period, "t": t, "bpm": bpm, "beat_s": 60.0 / float(bpm), "from": from, "frames_per_beat": frames_per_beat(bpm), "rate": clock_rate(bpm), "loop_seconds": loop_seconds})


## The length of one audio mix chunk as it is now (time since the last mix plus the time to the next one): 5.9 ms to 20 ms on a device, 88.5 ms with the dummy driver of the headless recordings.
func mix_period(ttnm: float) -> float:
	return clampf(AudioServer.get_time_since_last_mix() + ttnm, 0.0, 0.25)


func _live_group() -> Dictionary:
	for i in range(_groups.size() - 1, -1, -1):
		if not _groups[i]["fading"]:
			return _groups[i]
	return {}


func _begin_phase(ev: Dictionary, t: float, now: float, ttnm: float) -> void:
	var prev := _live_group()
	_end_carry()  # (a carry still running from the phase before is over)
	for g in _groups:
		g["fading"] = true
		for v in g["voices"].values():
			v["target"] = 0.0
	if ev.has("track"):  # a track scene: the loops of the scene before fade out, nothing starts here (no carried bass either)
		return
	var node: Dictionary = data.nodes.get(str(ev["node"]), {})  # ({} for the Bassment, node "trial": its pack and treatment come with the event, no bass bus, no sections, no family)
	var family := str(node.get("family", ""))
	# the previous scene's bass carries on under this scene's drums-alone block when both play one music family (same key and sound): it fades out at the carry's end, as this scene's own bass enters
	var carry: Dictionary = cfg.get("mix", {}).get("carry_bass", {})
	if not prev.is_empty() and prev["voices"].has("bass") and float(carry.get("gain", 0.0)) > 0.0 and family != "" and str(prev.get("family", "")) == family:
		prev["carry"] = true
		prev["voices"]["bass"]["target"] = _carry_target()
		_schedule_add({"t": t + float(carry.get("beats", 16.0)) * beat_s, "kind": "carry_end"})
	var k := (int(ev["phase"]) - int(ev.get("lap_extra", 0))) % 2  # (scenes alternate the two bus pairs; the extra laps of a scene stay on the pair it began on)
	var pair: Array = BUS_PAIRS[k]
	_apply_treatment(pair, str(ev["treatment"]))
	_apply_bass_bus(str(TONE_BUSES[k]), node.get("bass_bus", {}))
	var secs: Array = node.get("sections", [])
	var group := {"phase": int(ev["phase"]), "node": str(ev["node"]), "voices": {}, "fading": false, "pack": str(ev["audio"]), "buses": pair, "tone": str(TONE_BUSES[k]), "duck": 1.0 - _fade_master,
		"section": 0, "recipe": secs[0]["gains"] if not secs.is_empty() else {}, "family": family}
	_groups.append(group)
	_start_voice(group, "drums", t, now, ttnm)
	group["voices"]["drums"]["gain"] = 0.0
	group["mix"] = cfg["stages"][0]["gains"]
	group["voices"]["drums"]["target"] = _target_gain(group, "drums", group["mix"])


## The gain a voice aims at: the phase mix's gain for it times the section's recipe gain (1 when the scene has no arrangement; the bass's recipe gain is lifted to `mix.recipe_bass_floor`).
func _target_gain(group: Dictionary, name: String, gains: Dictionary) -> float:
	var rg := float((group.get("recipe", {}) as Dictionary).get(name, 1.0))
	if name == "bass":
		rg = maxf(rg, float(cfg.get("mix", {}).get("recipe_bass_floor", 0.0)))
	return float(gains.get(name, 0.0)) * rg * (dip_gain() if _dip and name != "drums" else 1.0)


## The carried bass's gain (`mix.carry_bass.gain`, dipped with the rest while a dip is live).
func _carry_target() -> float:
	return float(cfg.get("mix", {}).get("carry_bass", {}).get("gain", 0.0)) * (dip_gain() if _dip else 1.0)


## The carried bass fades out (at its scheduled end, or when another phase begins).
func _end_carry() -> void:
	for g in _groups:
		if bool(g.get("carry", false)):
			g["carry"] = false
			for v in g["voices"].values():
				v["target"] = 0.0


## The bass bus of a pair: high-pass, low shelf, a soft WAVESHAPE saturation (pre and post gain) from the scene's resolved `bass_bus` (RunData.BASS_BUS_DEFAULT); nothing when it is not enabled.
## tools/run/measure_mix.py models the same chain offline (docs/HANDOVER.md "Audio polish").
static func _apply_bass_bus(bus_name: String, bb: Dictionary) -> void:
	var bus := AudioServer.get_bus_index(bus_name)
	if bus < 0:
		return
	while AudioServer.get_bus_effect_count(bus) > 0:
		AudioServer.remove_bus_effect(bus, 0)
	if not bool(bb.get("enabled", false)):
		return
	if float(bb.get("highpass_hz", 0.0)) > 0.0:
		var hp := AudioEffectHighPassFilter.new()
		hp.cutoff_hz = float(bb["highpass_hz"])
		hp.resonance = 0.5
		AudioServer.add_bus_effect(bus, hp)
	if absf(float(bb.get("shelf_db", 0.0))) > 0.0:
		var sh := AudioEffectLowShelfFilter.new()
		sh.cutoff_hz = float(bb.get("shelf_hz", 100.0))
		sh.resonance = 0.5
		sh.gain = db_to_linear(float(bb["shelf_db"]))
		AudioServer.add_bus_effect(bus, sh)
	if float(bb.get("drive", 0.0)) > 0.0 or absf(float(bb.get("pre_gain_db", 0.0))) > 0.0 or absf(float(bb.get("gain_db", 0.0))) > 0.0:
		var ds := AudioEffectDistortion.new()
		ds.mode = AudioEffectDistortion.MODE_WAVESHAPE
		ds.drive = float(bb.get("drive", 0.0))
		ds.pre_gain = float(bb.get("pre_gain_db", 0.0))
		ds.post_gain = float(bb.get("gain_db", 0.0))
		ds.keep_hf_hz = float(bb.get("keep_hf_hz", 16000.0))
		AudioServer.add_bus_effect(bus, ds)


## The scheduled start of section `index` of the live phase: the old section's voices stop and the new pack's start in the same mix chunk, at the gains the phase mix and the new
## recipe give (no ramp: a switch on the grid is a cut, the loops are whole bars). The bass and synth follow only when the bass has been revealed in the phase.
func _switch_section(item: Dictionary, now: float, ttnm: float) -> void:
	var old := _live_group()
	if old.is_empty() or int(old["phase"]) != int(item["phase"]):
		return  # the phase is already over (a pause that skipped it, a run that ended)
	var sec: Dictionary = item["section"]
	var group := {"phase": old["phase"], "node": old["node"], "voices": {}, "fading": false, "pack": str(sec["pack"]), "buses": old["buses"], "tone": old.get("tone", ""), "duck": old.get("duck", 0.0),
		"section": int(item["index"]), "recipe": sec["gains"], "mix": old.get("mix", {}), "family": old.get("family", "")}
	var had_bass: bool = old["voices"].has("bass")
	for v in old["voices"].values():
		(v["player"] as AudioStreamPlayer).stop()
		(v["player"] as AudioStreamPlayer).queue_free()
	_groups.erase(old)
	_groups.append(group)
	var t := float(item["t"])
	var names: Array = ["drums", "bass", "other"] if had_bass else ["drums"]
	for name in names:
		_start_voice(group, name, t, now, ttnm)
		if group["voices"].has(name):
			var tg := _target_gain(group, name, group["mix"])
			group["voices"][name]["gain"] = tg
			group["voices"][name]["target"] = tg


func _start_voice(group: Dictionary, name: String, t: float, now: float, ttnm: float) -> void:
	if group["voices"].has(name):
		return
	var path := _stem_path(str(group["pack"]), name)
	var s := _loop_copy(path)
	if s == null:
		push_error("run audio: cannot load " + path)
		return
	var p := AudioStreamPlayer.new()
	p.bus = str((group["buses"] as Array)[0 if name == "drums" else 1])  # drums onto the pair's drum bus, the synth onto its bass bus (the treatment)
	if name == "bass" and str(group.get("tone", "")) != "":
		p.bus = str(group["tone"])  # the bass through its tone bus first (which sends to the pair's bass bus)
	p.stream = s
	p.volume_db = SILENT_DB
	add_child(p)
	var from := maxf(now + ttnm - t, 0.0)  # started a little late: begin that far into the loop so it sits on the grid
	p.play(from)
	group["voices"][name] = {"player": p, "gain": 0.0, "target": 0.0, "origin_t": t}
	voice_log.append({"voice": name, "node": str(group["node"]), "target": t, "lateness_ms": from * 1000.0, "from": from, "section": int(group.get("section", 0)), "pack": str(group["pack"])})


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


# --- the transition seam (stage M1.6; docs/parallel-development/MUSIC_TRANSITIONS.md section 12, item 4) -----------------------------------------------------------------
## TransitionDirector hands the audio the recipe of each transition it locks (`prepare_transition`, at the lock point) and hears back when the outgoing music is silent
## (`outgoing_silent`, carrying the boundary time), which is when it emits `completed`. The M1 recipe is always `cut`: the scene change itself is today's code (_begin_phase fades every
## loop group over mix.phase_fade_s from the boundary, RunTrackAudio fades a track group on track_end or on the next phase_start), so the recipe is recorded and only the silence is
## watched. Stage M2 executes its own recipes here (a tail group, its rate, its fades and its hard floor at complete_t) and reports silence the same way.
signal outgoing_silent(boundary_t: float)

var transition_log: Array = []  # {kind: prepare | silent, t (the boundary), at (song time), mode, ...} for the tests and the walks
var _watch: Array = []  # [{t (boundary), recipe, armed}]: armed when the phase that starts on the boundary has begun


## The director locked a transition at boundary `boundary_t` with this recipe (TransitionPlanner: {mode, fade_s, tail_s, carry, incoming}).
## Stage M2.4: the recipe also carries `in` (the incoming track scene: node, track, dir, entry_t, beat_s) and `out`; the track audio starts the incoming group early and muted and, for
## blend, halftime_blend and echo_out, plays the outgoing group on as the tail (RunTrackAudio.prepare_transition).
func prepare_transition(boundary_t: float, recipe: Dictionary) -> void:
	_watch.append({"t": boundary_t, "recipe": recipe.duplicate(true), "armed": false})
	transition_log.append({"kind": "prepare", "t": boundary_t, "mode": str(recipe.get("mode", "")), "tail_s": float(recipe.get("tail_s", 0.0)), "incoming": str(recipe.get("incoming", "")),
		"rate": float(recipe.get("rate", 1.0)), "window_bars": int(recipe.get("window_bars", 0)), "complete_t": float(recipe.get("complete_t", boundary_t + float(recipe.get("tail_s", 0.0)))),
		"drop_t": float(recipe.get("drop_t", -1.0)), "reason": str(recipe.get("reason", "")), "in": str((recipe.get("in", {}) as Dictionary).get("track", "")),
		"out": str((recipe.get("out", {}) as Dictionary).get("track", ""))})
	if track != null:
		track.prepare_transition(boundary_t, recipe)


func _arm_watch(t: float) -> void:
	for w in _watch:
		if absf(float(w["t"]) - t) < 1e-4:
			w["armed"] = true


## Something of the outgoing music still sounds: a loop group fading out (or a carried bass), or a track group fading.
func outgoing_sounding() -> bool:
	for g in _groups:
		if bool(g["fading"]):
			return true
	return track != null and track.fading_count() > 0


## Reports every armed transition whose outgoing music has gone (called every frame; tests call it with their own clock).
func check_silence(now: float) -> void:
	if _watch.is_empty():
		return
	for w in _watch.duplicate():
		if not bool(w["armed"]) and now > float(w["t"]) + 30.0:
			_watch.erase(w)  # (its phase never began: the Bassment took the boundary, or the run ended)
			continue
		if bool(w["armed"]) and not outgoing_sounding():
			_watch.erase(w)
			transition_log.append({"kind": "silent", "t": float(w["t"]), "at": now, "mode": str((w["recipe"] as Dictionary).get("mode", ""))})
			outgoing_silent.emit(float(w["t"]))
