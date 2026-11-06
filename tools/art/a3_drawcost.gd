extends SceneTree
## The draw cost of the falling notes and the pad strip on a busy scene of the real run (package A3 of docs/art/VISUAL_AUDIT.md).
## Needs a window (the worlds are rendered). Loads src/run/run_play.tscn (start it on a busy scene with RW_RUN_START, the bot playing,
## RW_RUN_VIRTUAL=1), waits WARM frames, then alternates blocks of BLOCK frames with the UI layers shown and hidden (the nodes "Pads",
## "Notes" and the lane shade under the run scene) and prints the median CPU time per frame of each: process (where the _draw callbacks
## run) and the viewport's render CPU time. The difference is what those layers cost.
##   godot --path . --resolution 1280x720 -s tools/art/a3_drawcost.gd -- [blocks]
## Frame pacing is off (vsync disabled, no fps cap) so the numbers are work, not waiting.

const WARM := 240
const BLOCK := 90

var _frame := 0
var _loaded := false
var _blocks := 8
var _on: Array = []
var _off: Array = []
var _ron: Array = []
var _roff: Array = []
var _layers: Array = []
var _shown := true
var _usec0 := {}
var _counted := 0


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() > 0:
		_blocks = int(args[0])
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	Engine.max_fps = 0


func _process(_delta: float) -> bool:
	if not _loaded:
		_loaded = true
		change_scene_to_file("res://src/run/run_play.tscn")
		return false
	_frame += 1
	if _frame == WARM:
		var scene := current_scene
		for n in ["Pads", "Notes"]:
			var node := scene.find_child(n, true, false)
			if node != null:
				_layers.append(node)
		for c in scene.get_children():
			if c is StoryLaneShade:
				_layers.append(c)
		RenderingServer.viewport_set_measure_render_time(root.get_viewport_rid(), true)
		print("DRAWCOST layers: ", _layers.map(func(x: Node) -> String: return x.name))
		_usec0 = {"pads": StoryPadView.draw_usec, "notes": StoryNoteLane.draw_usec, "shade": StoryLaneShade.draw_usec}
	if _frame <= WARM:
		return false
	var k := (_frame - WARM - 1) / BLOCK
	if k >= _blocks * 2:
		_report()
		quit(0)
		return false
	var want := k % 2 == 0
	if want != _shown:
		_shown = want
		for l in _layers:
			(l as CanvasItem).visible = want
	if _shown:
		_counted += 1
	if (_frame - WARM - 1) % BLOCK < 10:
		return false  # let a toggle settle
	var p := Performance.get_monitor(Performance.TIME_PROCESS) * 1000.0
	var r := RenderingServer.viewport_get_measured_render_time_cpu(root.get_viewport_rid()) + RenderingServer.get_frame_setup_time_cpu()
	(_on if _shown else _off).append(p)
	(_ron if _shown else _roff).append(r)
	return false


func _median(a: Array) -> float:
	if a.is_empty():
		return 0.0
	var s := a.duplicate()
	s.sort()
	return float(s[s.size() / 2])


func _report() -> void:
	var po := _median(_on)
	var pf := _median(_off)
	var ro := _median(_ron)
	var rf := _median(_roff)
	var n := maxf(float(_counted), 1.0)
	print("DRAWCOST draw_us_per_frame pads %.1f notes %.1f shade %.1f (over %d shown frames)" % [(StoryPadView.draw_usec - int(_usec0["pads"])) / n,
		(StoryNoteLane.draw_usec - int(_usec0["notes"])) / n, (StoryLaneShade.draw_usec - int(_usec0["shade"])) / n, _counted])
	print("DRAWCOST process_ms shown %.3f hidden %.3f delta %.3f | render_cpu_ms shown %.3f hidden %.3f delta %.3f | frames %d/%d" % [po, pf, po - pf, ro, rf, ro - rf, _on.size(), _off.size()])
