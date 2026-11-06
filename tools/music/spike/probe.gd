extends SceneTree
## THROWAWAY (M2.1 spike). Does a capture of a bus work on the real driver with nothing reaching the speakers, and what do the audio classes offer?
##   godot --audio-driver WASAPI --path . -s tools/music/spike/probe.gd      (RW_PROBE_STEM: an .ogg to play for 2 s)

var _p: AudioStreamPlayer
var _cap: AudioEffectCapture
var _frames := 0
var _n := 0
var _sum2 := 0.0
var _chunks: Array = []
var _t0 := 0


func _initialize() -> void:
	print("PROBE driver ", AudioServer.get_driver_name() if AudioServer.has_method("get_driver_name") else "?", " mix_rate ", AudioServer.get_mix_rate(), " output_latency_ms ", AudioServer.get_output_latency() * 1000.0)
	print("PROBE project buffer setting ", ProjectSettings.get_setting("audio/driver/output_latency", "?"))
	for cls in ["AudioStreamInteractive", "AudioStreamSynchronized", "AudioStreamPlaybackInteractive", "AudioEffectCapture", "AudioEffectPitchShift", "AudioStreamPlayer"]:
		var props: Array = ClassDB.class_get_property_list(cls, true).map(func(p: Dictionary) -> String: return str(p["name"]))
		var meths: Array = ClassDB.class_get_method_list(cls, true).map(func(m: Dictionary) -> String: return str(m["name"]))
		print("PROBE class ", cls, " props ", props, " methods ", meths)
	print("PROBE AudioStreamInteractive constants ", ClassDB.class_get_integer_constant_list("AudioStreamInteractive", true))
	AudioServer.add_bus()
	var sink := AudioServer.bus_count - 1
	AudioServer.set_bus_name(sink, "ProbeSink")
	AudioServer.set_bus_mute(sink, true)
	AudioServer.add_bus()
	var b := AudioServer.bus_count - 1
	AudioServer.set_bus_name(b, "Probe")
	AudioServer.set_bus_send(b, "ProbeSink")
	_cap = AudioEffectCapture.new()
	_cap.buffer_length = 1.0
	AudioServer.add_bus_effect(b, _cap)
	AudioServer.set_bus_mute(0, true)


func _process(_d: float) -> bool:
	if _p == null:
		_p = AudioStreamPlayer.new()
		_p.bus = "Probe"
		root.add_child(_p)
		_p.stream = AudioStreamOggVorbis.load_from_file(OS.get_environment("RW_PROBE_STEM"))
		_p.play(60.0)
		_t0 = Time.get_ticks_msec()
		return false
	_chunks.append(AudioServer.get_time_since_last_mix() + AudioServer.get_time_to_next_mix())
	var n := _cap.get_frames_available()
	if n > 0:
		var buf := _cap.get_buffer(n)
		for v in buf:
			_sum2 += v.x * v.x
		_n += n
	if Time.get_ticks_msec() - _t0 > 2000:
		_p.stop()
		var cs := _chunks.duplicate()
		cs.sort()
		print("PROBE captured %d frames (%.3f s) in 2 s, rms %.4f, pushed %d discarded %d, chunk median %.2f ms max %.2f ms, output_latency_ms %.2f" % [_n, _n / AudioServer.get_mix_rate(), sqrt(_sum2 / maxf(_n, 1)),
			_cap.get_pushed_frames() if _cap.has_method("get_pushed_frames") else -1, _cap.get_discarded_frames() if _cap.has_method("get_discarded_frames") else -1, cs[cs.size() / 2] * 1000.0, cs[-1] * 1000.0, AudioServer.get_output_latency() * 1000.0])
		return true
	return false
