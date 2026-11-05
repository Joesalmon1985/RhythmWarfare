extends SceneTree
## Checks story maps and their chapter files:  godot --headless --path . -s tools/story/check_map.gd -- <map id> ...
## Each map loads without errors (geometry, textures, waypoints, homes) and its chapter file (content/story/<id>.json) validates against it. Exit code 1 on any problem.


func _initialize() -> void:
	var bad := 0
	for id in OS.get_cmdline_user_args():
		var errs: Array = []
		var m := StoryMap.load_chapter(str(id))
		errs.append_array(m.errors)
		var loaded := StoryData.load_file("res://content/story/%s.json" % id)  # (a path's map: the chapter file a world of its run.json names in `story`)
		errs.append_array(loaded["errors"])
		if m.errors.is_empty() and loaded["data"] != null:
			m.validate_chapter((loaded["data"] as StoryData).raw)
			errs.append_array(m.errors)
		print("%s: %d sectors, %d waypoints, %d things, %d lights, %s" % [id, m.sectors.size(), m.waypoints.size(), m.things.size(), m.lights.size(), "OK" if errs.is_empty() else "%d problem(s)" % errs.size()])
		for e in errs:
			print("  ERROR ", e)
		bad += errs.size()
	quit(1 if bad > 0 else 0)
