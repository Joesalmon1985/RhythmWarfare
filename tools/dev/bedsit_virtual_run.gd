extends SceneTree
## The headless, virtual-clock equivalent of tools\dev\play_bedsit.cmd, driven by taps through RunPlay.dispatch_tap (the one dispatcher): start facing north, tap right (east,
## the Dinosaurs), tap right (south, Magic and unicorns), tap top (the wardrobe), into the Magic rave, take its way home (magic_rave.home), back in the bedsit: the facing is the
## saved one. Prints BEDSIT lines (on stderr: unbuffered). A scratch save (user://bedsit_virtual_run_save.json), never the real one.
##   RW_AUDIO_WORK=... bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/dev/bedsit_virtual_run.gd

const SAVE := "user://bedsit_virtual_run_save.json"

var scene: Control
var host: Control


func _session() -> Node:  # (the autoload by path: a -s script compiles before the autoloads are known by name)
	return root.get_node("Session")


func _initialize() -> void:
	_setup.call_deferred()  # (after the autoloads' _ready, which would load the default save over ours)


func _setup() -> void:
	for f in [SAVE, SAVE + ".tmp"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	_session().run_progress = RunProgress.load_data(SAVE, "user://none.json")
	for kv in [["RW_RUN_VIRTUAL", "1"], ["RW_RUN_BOT", "perfect"], ["RW_RUN_TAPS", "none"], ["RW_RUN_PATH", "bedsit"], ["RW_BEDSIT", "1"]]:
		OS.set_environment(kv[0], kv[1])
	host = Control.new()
	host.size = Vector2(1152, 648)
	root.add_child(host)
	scene = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = Vector2(1152, 648)
	_run.call_deferred()


func _say(what: String) -> void:
	var pose: Dictionary = scene._exit_pose()
	printerr("BEDSIT t=%7.2f node %-12s facing %s save %s yaw %7.2f  %s%s" % [float(scene._vt), str(scene.engine.node_id), str(scene.bedsit.facing),
		_session().run_progress.bedsit_facing(), float(pose.get("yaw", NAN)), what, BedsitNav.debug_line(_session().run_progress.data, scene.bedsit.active)])


func _step_to(t_end: float) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func _until(t_max: float, stop: Callable) -> bool:
	var t: float = scene._vt
	while t < t_max and not stop.call():
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)
	return stop.call()


func _tap(region: String) -> void:
	var at := {"left": Vector2(0.1, 0.5), "right": Vector2(0.9, 0.5), "bottom": Vector2(0.5, 0.86), "top": Vector2(0.5, 0.2)}
	var sh: Control = scene._stage_host
	var owner: String = scene.dispatch_tap(sh.global_position + sh.size * (at[region] as Vector2))
	_say("tap %s -> owner %s target %s" % [region, owner, str((scene.input_log as Array).back()["target"])])


func _run() -> void:
	var bar: float = 4.0 * float(scene.engine.beat_s)
	var phase: float = 64.0 * float(scene.engine.beat_s)
	_step_to(1.0 * bar)
	_say("start")
	_tap("right")
	_step_to(scene._vt + bar + 0.1)
	_say("one bar later")
	_tap("right")
	_step_to(scene._vt + bar + 0.1)
	_say("one bar later")
	_until(scene._vt + phase, func() -> bool: return scene.selection_open())
	_tap("top")
	_say("selected %s" % scene.hotspots.selected)
	var ok := _until(scene._vt + 6.0 * phase, func() -> bool: return str(scene.engine.node_id) == "magic_rave")
	_say("in the rave: %s" % ok)
	_until(scene._vt + phase, func() -> bool: return scene.selection_open())
	_say("way home picked: %s" % scene.hotspot_select("magic_rave.home"))
	ok = _until(scene._vt + 6.0 * phase, func() -> bool: return str(scene.engine.node_id) == "bedsit")
	_step_to(scene._vt + 0.2)
	_say("home: %s" % ok)
	var file: String = _session().run_progress.path
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(file)) if FileAccess.file_exists(file) else null
	var on_disk := str((parsed as Dictionary).get("bedsit_facing", "?")) if typeof(parsed) == TYPE_DICTIONARY else "(no file at %s)" % file
	printerr("BEDSIT save file %s bedsit_facing %s; homecoming facing %s; %s" % [file, on_disk, str(scene.bedsit.facing),
		"OK" if str(scene.bedsit.facing) == "S" and on_disk == "S" else "MISMATCH"])
	host.queue_free()
	await process_frame
	for f in [SAVE, SAVE + ".tmp"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	quit()
