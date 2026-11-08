extends SceneTree
## Checks the rail paths of the run's scenes against their maps (StoryRailCheck, docs/story/HEIGHTS_AND_PATHS.md): every move a scene's rail can make (up the good rail,
## down and back along the bad one, the drop from a good place to the bad rail, the arrival) stays inside walkable pieces crossing only portals open to walkers, never crosses a
## wall, a railing, a void or a floor change that is not a step for its style, keeps the eye within 1.4 to 1.8 m of the local floor at every sample, and every choice viewpoint
## holds for the whole choice window.
## Every walk-out (a route of rail.routes whose `next` entry leads to another world) is measured from the scene's choice viewpoint (else its home) along its authored leg and given
## the pace it would get (LEAD_RULINGS 42: at most 3 m/s, 2 to 8 bars, RunRail.walk_off_bars):
##   "  WALKOFF <dir> <from> -> <to>: <m> m, <bars> bars at <bpm> bpm, <m/s> m/s"
## and a leg that would need more than 8 bars at 3 m/s is flagged (a warning, not an error: the scene must shorten the leg or add a hold):
##   "  WARN walk-off <dir> <from> -> <to>: <m> m needs <n> bars at 3.0 m/s, more than 8 (the scene must shorten the leg or add a hold)"
##   godot --headless --path . -s tools/story/check_rail_paths.gd -- [run.json paths ...] [--node=<id filter>] [--bpm=<bpm>]
## No paths: content/run/run.json and every content/paths/*/run.json. Prints "RAILCHECK <file> <node>: OK" or its errors; exit code 1 on any error. The tempo is the file's
## timing.bpm, else 174 (a fixture merged into the main run), or --bpm.


func _initialize() -> void:
	var files: Array = []
	var filt := ""
	var bpm_arg := -1.0
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--node="):
			filt = str(a).trim_prefix("--node=")
		elif str(a).begins_with("--bpm="):
			bpm_arg = float(str(a).trim_prefix("--bpm="))
		else:
			files.append(str(a))
	if files.is_empty():
		files.append("res://content/run/run.json")
		for d in DirAccess.get_directories_at("res://content/paths"):
			if FileAccess.file_exists("res://content/paths/%s/run.json" % d):
				files.append("res://content/paths/%s/run.json" % d)
	var bad := 0
	var checked := 0
	var warned := 0
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
		var bpm := bpm_arg if bpm_arg > 0.0 else float((run.get("timing", {}) as Dictionary).get("bpm", 174.0))
		var world_of := {}
		for n0 in run.get("nodes", []):
			world_of[str(n0.get("id", ""))] = str(n0.get("world", ""))
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
			if m.errors.is_empty():
				warned += _walk_offs(m, n, place, world_of, bpm)
	print("RAILCHECK %d scenes, %d problem(s), %d walk-off warning(s)" % [checked, bad, warned])
	quit(1 if bad > 0 else 0)



## The walk-outs of scene `n` (StoryRailCheck.walk_offs): each one's length and pace (the header's WALKOFF line); returns how many were flagged (more than 8 bars at 3 m/s).
func _walk_offs(m: StoryMap, n: Dictionary, place: Dictionary, world_of: Dictionary, bpm: float) -> int:
	var flagged := 0
	for w in StoryRailCheck.walk_offs(m, n, place, world_of, bpm):
		if float(w["length"]) < 0.0:
			print("  WALKOFF %s %s -> %s: the length is unknown (a waypoint is missing)" % [w["dir"], w["from"], w["to"]])
			continue
		print("  WALKOFF %s %s -> %s: %.1f m, %d bars at %.0f bpm, %.2f m/s, from %s (worst case of %d rail places; choice place %s)" % [w["dir"], w["from"], w["to"], float(w["length"]), int(w["bars"]), bpm, float(w["pace"]), "the choice place" if str(w["from"]) == str(w["choice"]) else "the longest", int(w["places"]), w["choice"]])
		if bool(w["warn"]):
			flagged += 1
			print("  WARN walk-off %s %s -> %s: %.1f m needs %d bars at %.1f m/s, more than %d (the scene must shorten the leg or add a hold)" % [w["dir"], w["from"], w["to"], float(w["length"]), int(w["need"]), RunRail.WALK_PACE_MAX, int(RunRail.WALK_OFF_BARS_MAX)])
	return flagged
