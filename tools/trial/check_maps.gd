extends SceneTree
## Checks the Bassment's zone maps and layouts:  godot --headless --path . -s tools/trial/check_maps.gd [-- <zone> ...]
## For each zone (default: all): content/story/maps/bassment_<zone>.json loads without errors, has 2 to 4 sectors, a start waypoint and every texture it names; if
## content/trial/layout/<zone>.json exists, every passage of the zone has a waypoint of the map and one exit waypoint per choice. Prints a line per zone; exit code 0 when sound.


func _initialize() -> void:
	var d := TrialData.load_default()
	var zones: Array = OS.get_cmdline_user_args() if not OS.get_cmdline_user_args().is_empty() else d.zones.keys()
	var bad := 0
	for z in zones:
		var errs: Array = []
		var mid := "bassment_" + str(z)
		var m := StoryMap.load_chapter(mid)
		errs.append_array(m.errors)
		if m.errors.is_empty():
			if m.sectors.size() < 2 or m.sectors.size() > 4:
				errs.append("%d sectors (2 to 4 wanted)" % m.sectors.size())
			var lp := "res://content/trial/layout/%s.json" % z
			if FileAccess.file_exists(lp):
				var lay: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(lp))
				for n in d.passages:
					var p: Dictionary = d.passages[n]
					if str(p["zone"]) != str(z):
						continue
					var e: Dictionary = (lay.get("passages", {}) as Dictionary).get(str(n), {})
					if e.is_empty():
						errs.append("layout: passage %d missing" % n)
						continue
					if not m.has_waypoint(str(e.get("waypoint", ""))):
						errs.append("layout: passage %d waypoint '%s' is not in the map" % [n, e.get("waypoint", "")])
					var ex: Array = e.get("exits", [])
					if ex.size() != (p["choices"] as Array).size():
						errs.append("layout: passage %d has %d exits for %d choices" % [n, ex.size(), (p["choices"] as Array).size()])
					for x in ex:
						if not m.has_waypoint(str(x)):
							errs.append("layout: passage %d exit '%s' is not a waypoint of the map" % [n, x])
		print("%s: %d sectors, %d waypoints, %d things, %d lights, %s" % [mid, m.sectors.size(), m.waypoints.size(), m.things.size(), m.lights.size(), "OK" if errs.is_empty() else "%d problem(s)" % errs.size()])
		for e in errs:
			print("  ERROR ", e)
		bad += errs.size()
	# the hotspots (content/trial/hotspots.json): one per choice, every anchor a waypoint or a thing of its zone's map, the creature markers inside a room with room to stand
	var hot := TrialHotspots.load_default()
	var herrs := hot.validate(d)
	for z in d.zones:
		var m2 := TrialData.map_of("bassment_" + str(z))
		for t in m2.things:
			if str(t["id"]).begins_with("hs_") and not m2.inside(t["at"], str(t["sector"]), 0.4):
				herrs.append("marker %s of %s is not 0.4 m inside its sector" % [t["id"], z])
	print("hotspots: %d (%s), %s" % [hot.count(), hot.kinds(), "OK" if herrs.is_empty() else "%d problem(s)" % herrs.size()])
	for e in herrs:
		print("  ERROR ", e)
	bad += herrs.size()
	quit(0 if bad == 0 else 1)
