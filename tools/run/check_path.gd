extends SceneTree
## Loads a path's run data and prints every error and warning:  godot --headless --path . -s tools/run/check_path.gd -- <path id> ...
func _initialize() -> void:
	var bad := 0
	for id in OS.get_cmdline_user_args():
		var d := RunData.load_path(str(id))
		print("%s: %d scenes, %d worlds, %d errors, %d warnings" % [id, d.nodes.size(), d.worlds.size(), d.errors.size(), d.warnings.size()])
		for e in d.errors:
			print("  ERROR ", e)
		for w in d.warnings:
			print("  warn ", w)
		bad += d.errors.size()
	quit(1 if bad > 0 else 0)
