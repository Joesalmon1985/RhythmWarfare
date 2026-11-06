extends SceneTree
## A measurement, not a test: the REAL run scene (src/run/run_play.tscn) in real time on the real audio driver, with the RunTrack bus captured (before its limiter) and the Master bus muted, in the
## format tests/fixtures/track_scenes/analyse_track_capture.py reads (cue time against the audio itself, per track group). Made for the scene changes that do not go through a lock: the way into
## the Bassment and back (RW_TRIAL_ENTER=1 arms the wizard at once, RW_TRIAL_LEAVE_AT=<song s> leaves the dungeon, RW_TRIAL_BOT=perfect plays it). Needs RW_TRACKS_DIR on the command line.
##   RW_MEASURE_S seconds of song time to play (default 120); RW_MEASURE_CAPTURE=<folder> (required); RW_RUN_START, RW_RUN_BOT (default perfect) as for the game.

var _scene: Node
var _host: Control
var _cap: AudioEffectCapture
var _buf := PackedVector2Array()
var _rows: Array = []
var _pushed0 := 0
var _dir := ""
var _t_end := 120.0
var _frames := 0


func _initialize() -> void:
	_dir = OS.get_environment("RW_MEASURE_CAPTURE")
	_t_end = float(OS.get_environment("RW_MEASURE_S")) if OS.has_environment("RW_MEASURE_S") else 120.0
	if _dir == "" or OS.get_environment("RW_TRACKS_DIR") == "":
		printerr("measure_run_play: set RW_MEASURE_CAPTURE and RW_TRACKS_DIR")
		quit(2)
		return
	if not OS.has_environment("RW_RUN_BOT"):
		OS.set_environment("RW_RUN_BOT", "perfect")
	DirAccess.make_dir_recursive_absolute(_dir)
	AudioServer.set_bus_mute(0, true)
	_host = Control.new()
	_host.size = Vector2(1280, 720)
	root.add_child(_host)
	_scene = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	_host.add_child(_scene)


func _process(_d: float) -> bool:
	if _scene == null:
		return true
	var audio: RunAudio = _scene.get("audio")
	if audio == null:
		return false
	if _cap == null:
		_cap = AudioEffectCapture.new()
		_cap.buffer_length = 2.0
		AudioServer.add_bus_effect(AudioServer.get_bus_index(RunTrackAudio.BUS), _cap, 0)
		_pushed0 = _cap.get_pushed_frames()
		return false
	AudioServer.lock()
	_rows.append([audio.playback_position(), _cap.get_pushed_frames() - _pushed0])
	AudioServer.unlock()
	var n := _cap.get_frames_available()
	if n > 0:
		_buf.append_array(_cap.get_buffer(n))
	_frames += 1
	if audio.now_t() >= _t_end:
		_report(audio)
		return true
	return false


func _report(audio: RunAudio) -> void:
	var groups: Array = audio.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) in ["start", "seek"])
	var dirs := {}
	for x in groups:
		for c in audio.track.load_log:
			if str(c["track"]) == str(x["track"]):
				dirs[str(x["track"])] = str(c["dir"])
	var f := FileAccess.open(_dir.path_join("run_track.f32"), FileAccess.WRITE)
	f.store_buffer(_buf.to_byte_array())
	f.close()
	FileAccess.open(_dir.path_join("run_track.json"), FileAccess.WRITE).store_string(JSON.stringify({"rows": _rows, "log": groups, "dirs": dirs, "driver": AudioServer.get_driver_name(),
		"output_latency": AudioServer.get_output_latency(), "discarded": _cap.get_discarded_frames(), "scenes": []}))
	for x in audio.track.log:
		if str(x["kind"]) in ["start", "prestart", "corrected", "final_start", "orphan", "end"]:
			var y: Dictionary = x.duplicate()
			y.erase("stems")
			y.erase("gains")
			print("MEASURE track ", JSON.stringify(y))
	for x in _scene.get("trial_log"):
		print("MEASURE trial ", JSON.stringify(x))
	print("MEASURE capture %d frames of RunTrack, driver %s" % [_buf.size(), AudioServer.get_driver_name()])
	audio.stop()
	quit()
