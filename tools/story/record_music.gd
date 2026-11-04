extends SceneTree
## Plays the real story_play scene (real StemTransport, real SongClock, scripted input) and records what comes out of the
## Music bus, so the mix can be checked against the cues. Writes <out>.wav (the Music bus, 16-bit stereo) and <out>.json
## (the clock log: wall seconds since recording started, song time, stem gains, transport loop wraps).
##
##   RW_STORY_CHAPTER=night_one RW_AUTOPLAY=perfect godot --headless --path . -s tools/story/record_music.gd -- <out_base> <song_seconds>
##
## It runs in real time (the dummy audio driver mixes against the wall clock), so <song_seconds> of music takes that long.
## tools/story/check_music.py compares the recording with the cue list.

var _out := "user://music_check"
var _scene_path := "res://src/scenes/story_play.tscn"
var _until := 40.0
var _scene: Node
var _rec: AudioEffectRecord
var _t0 := 0
var _log: Array = []
var _next_log := 0.0
var _started_wall := -1.0
var _frames := 0


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		_out = args[0]
	if args.size() > 1:
		_until = float(args[1])
	if args.size() > 2:
		_scene_path = args[2]
	if OS.get_environment("RW_AUTOPLAY") == "":
		OS.set_environment("RW_AUTOPLAY", "perfect")
	var bus := StemTransport.ensure_music_bus()
	_rec = AudioEffectRecord.new()
	_rec.format = AudioStreamWAV.FORMAT_16_BITS
	AudioServer.add_bus_effect(bus, _rec)
	_rec.set_recording_active(true)
	_t0 = Time.get_ticks_usec()
	_scene = (load(_scene_path) as PackedScene).instantiate()
	root.add_child(_scene)


func _wall() -> float:
	return float(Time.get_ticks_usec() - _t0) / 1_000_000.0


func _process(_delta: float) -> bool:
	_frames += 1
	var clock: SongClock = _scene.get("clock")
	var transport: StemTransport = _scene.get("transport")
	if clock == null or transport == null:
		return false
	if _started_wall < 0.0 and clock.state == SongClock.State.PLAYING:
		_started_wall = _wall()
	var st := clock.audio_time() if clock.state == SongClock.State.PLAYING else -1.0
	if _wall() >= _next_log and st >= 0.0:
		_next_log = _wall() + 0.5
		var gains := {}
		if transport.has_method("gains"):
			gains = transport.call("gains")
		for k in transport.stem_keys:
			gains[k] = snappedf(transport.stem_gain(k), 0.01)
		_log.append({"wall": snappedf(_wall(), 0.001), "song": snappedf(st, 0.001), "playhead": snappedf(transport.player.get_playback_position(), 0.001), "gains": gains})
	if st >= _until or _wall() > _until + 30.0:
		_finish(transport)
		return true
	return false


func _finish(transport: StemTransport) -> void:
	_rec.set_recording_active(false)
	var wav: AudioStreamWAV = _rec.get_recording()
	var path := _out + ".wav"
	if wav != null:
		wav.save_to_wav(path)
	var f := FileAccess.open(_out + ".json", FileAccess.WRITE)
	f.store_string(JSON.stringify({"started_wall": _started_wall, "t0_usec": _t0, "frames": _frames, "stems": transport.stem_keys, "loop_seconds": transport.loop_seconds, "voices": transport.get("voice_log") if transport.get("voice_log") != null else [], "events": _scene.get("event_log") if _scene.get("event_log") != null else [], "phases": _scene.get("phase_log") if _scene.get("phase_log") != null else [],
		"mix_rate": AudioServer.get_mix_rate(), "output_latency": AudioServer.get_output_latency(), "log": _log}, "\t"))
	f.close()
	print("recorded ", path, " ", "no audio" if wav == null else str(wav.get_length()) + " s", ", song start at wall ", _started_wall)
