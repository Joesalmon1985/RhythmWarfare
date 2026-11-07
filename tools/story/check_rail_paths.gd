extends SceneTree
## Checks the rail paths of the run's scenes against their maps (StoryRailCheck, docs/story/HEIGHTS_AND_PATHS.md): every move a scene's rail can make (up the good rail,
## down and back along the bad one, the drop from a good place to the bad rail, the arrival) stays inside walkable pieces crossing only portals open to walkers, never crosses a
## wall, a railing, a void or a floor change that is not a step for its style, keeps the eye within 1.4 to 1.8 m of the local floor at every sample, and every choice viewpoint
## holds for the whole choice window.
##   godot --headless --path . -s tools/story/check_rail_paths.gd -- [run.json paths ...] [--node=<id filter>]
## No paths: content/run/run.json and every content/paths/*/run.json. Prints "RAILCHECK <file> <node>: OK" or its errors; exit code 1 on any error.


func _initialize() -> void:
	var files: Array = []
	var filt := ""
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--node="):
			filt = str(a).trim_prefix("--node=")
		else:
			files.append(str(a))
	if files.is_empty():
		files.append("res://content/run/run.json")
		for d in DirAccess.get_directories_at("res://content/paths"):
			if FileAccess.file_exists("res://content/paths/%s/run.json" % d):
				files.append("res://content/paths/%s/run.json" % d)
	var bad := 0
	var checked := 0
	var maps := {}
	for f in files:
		var run: Variant = JSON.parse_string(FileAccess.get_file_as_string(str(f)))
		if typeof(run) != TYPE_DICTIONARY:
			print("RAILCHECK %s: not a JSON object" % f)
			bad += 1
			continue
		var world_map := {}
		for w in run.get("worlds", []):
			world_map[str(w["id"])] = str(w.get("map", ""))
		for n in run.get("nodes", []):
			var id := str(n.get("id", ""))
			var place: Dictionary = n.get("place", {})
			if filt != "" and not id.contains(filt) or not place.has("rail"):
				continue
			var mid := str(world_map.get(str(n.get("world", "")), ""))
			if not maps.has(mid):
				maps[mid] = StoryMap.load_chapter(mid, false)
			var m: StoryMap = maps[mid]
			var errs: Array = m.errors.duplicate() if not m.errors.is_empty() else StoryRailCheck.check_rail(m, id, str(place.get("waypoint", "")), place["rail"])
			checked += 1
			print("RAILCHECK %s %s (%s): %s" % [str(f).get_file() if str(f).contains("/run/") else str(f).get_base_dir().get_file(), id, mid, "OK" if errs.is_empty() else "%d problem(s)" % errs.size()])
			for e in errs:
				print("  ERROR ", e)
			bad += errs.size()
	print("RAILCHECK %d scenes, %d problem(s)" % [checked, bad])
	quit(1 if bad > 0 else 0)
