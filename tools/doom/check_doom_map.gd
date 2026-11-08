extends SceneTree
## Loads converted Doom maps into StoryMap and reports its errors (tools/story/check_map.gd also wants a chapter file, which a Doom map does not have):
##   godot --headless --audio-driver Dummy --path . -s tools/doom/check_doom_map.gd -- doom_warehouse doom_bar ...
## Exit code 1 on any error. Count "SCRIPT ERROR" lines in the output too: the runner can print success on parse errors.


func _initialize() -> void:
	var bad := 0
	for id in OS.get_cmdline_user_args():
		var m := StoryMap.load_chapter(str(id))
		var walls := m.resolved_walls().size()
		var portals := m.portals().size()
		var reach := m.reachable_from(str(m.waypoints[m.start_id]["sector"])).size() if m.waypoints.has(m.start_id) else 0
		print("%s: %d sectors, %d walls, %d portals, %d reachable, %s" % [id, m.sectors.size(), walls, portals, reach, "OK" if m.errors.is_empty() else "%d problem(s)" % m.errors.size()])
		for e in m.errors.slice(0, 30):
			print("  ERROR ", e)
		bad += m.errors.size()
	quit(1 if bad > 0 else 0)
