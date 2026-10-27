extends SceneTree
## Scripted screenshots for verification (needs a window, not --headless):
##   godot --path . -s tools/shoot.gd -- <scene.tscn> <out_dir> <step> [<step> ...]
## step = <frame>:shot[:name] | <frame>:keydown:<KEY> | <frame>:keyup:<KEY> | <frame>:touch:<x>,<y> | <frame>:release:<x>,<y>
## Frames count from the scene's first processed frame. The last step is followed by quit.

var _steps: Array = []
var _out := ""
var _frame := 0
var _scene_path := ""
var _loaded := false


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() < 3:
		push_error("usage: scene out_dir step...")
		quit(2)
		return
	_scene_path = args[0]
	_out = args[1]
	DirAccess.make_dir_recursive_absolute(_out)
	for s in args.slice(2):
		var parts: PackedStringArray = s.split(":")
		_steps.append({"frame": int(parts[0]), "kind": parts[1], "arg": parts[2] if parts.size() > 2 else ""})
	_steps.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["frame"] < b["frame"])


func _process(_delta: float) -> bool:
	if not _loaded:
		_loaded = true
		change_scene_to_file(_scene_path)
		return false
	_frame += 1
	while not _steps.is_empty() and _steps[0]["frame"] <= _frame:
		var step: Dictionary = _steps.pop_front()
		_do(step)
	if _steps.is_empty():
		quit(0)
	return false


func _do(step: Dictionary) -> void:
	match step["kind"]:
		"shot":
			var img := root.get_viewport().get_texture().get_image()
			var name: String = step["arg"] if not str(step["arg"]).is_empty() else "frame_%04d" % _frame
			var path := _out.path_join(name + ".png")
			img.save_png(path)
			print("shot ", path)
		"keydown", "keyup":
			var ev := InputEventKey.new()
			ev.keycode = OS.find_keycode_from_string(step["arg"])
			ev.physical_keycode = ev.keycode
			ev.pressed = step["kind"] == "keydown"
			Input.parse_input_event(ev)
		"touch", "release":
			var xy: PackedStringArray = str(step["arg"]).split(",")
			var ev := InputEventScreenTouch.new()
			ev.index = 0
			ev.position = Vector2(float(xy[0]), float(xy[1]))
			ev.pressed = step["kind"] == "touch"
			Input.parse_input_event(ev)
