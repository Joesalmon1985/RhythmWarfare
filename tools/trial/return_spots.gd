extends SceneTree
## Where each Bassment passage's way back (tools/trial/returns.py) can stand: from the passage's camera (its waypoint, its yaw, the 844 x 215 strip tests/test_trial.gd lays the
## hotspots out in) every free waypoint of the room and a grid of spots ahead in the camera's sector are tried as the return's anchor, with the passage's other hotspots; a spot
## passes when every hotspot then has a place and can be hit at its centre. Writes {passage: {"wp": id} | {"at": [x, z], "sector": s}} for returns.py (the first passing waypoint
## nearest 6 m ahead, else the first passing grid spot). A survey; the game does not read it.
##
##     bash tools/dev/godot.sh --headless --path . -s tools/trial/return_spots.gd -- <out.json>

const VIEW := Vector2(844.0, 215.0)


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	var TD: GDScript = load("res://src/trial/trial_data.gd")
	var TH: GDScript = load("res://src/trial/trial_hotspots.gd")
	var HV: GDScript = load("res://src/run/hotspot_view.gd")
	var out_path := OS.get_cmdline_user_args()[0] if not OS.get_cmdline_user_args().is_empty() else "user://return_spots.json"
	var d = TD.load_default()
	var hot = TH.load_default()
	var res := {}
	var bad := 0
	var cams := {}  # map id -> {waypoint: true} the passages' own standpoints: a return never stands where another passage's camera does
	for n0 in d.passages:
		var p0: Dictionary = d.passages[n0]
		if not cams.has(str(p0["map"])):
			cams[str(p0["map"])] = {}
		cams[str(p0["map"])][str(p0["waypoint"])] = true
	for n in d.passages:
		var p: Dictionary = d.passages[n]
		var ret := -1
		for i in (p["choices"] as Array).size():
			if bool(p["choices"][i].get("return", false)):
				ret = i
		if ret < 0:
			continue
		var m = TD.map_of(str(p["map"]))
		var w: Dictionary = m.waypoint(str(p["waypoint"]))
		var at: Vector2 = w["at"]
		var pose := {"cam": Vector3(at.x, float(m.sector(str(w["sector"])).get("floor", 0.0)) + m.eye_height, at.y), "yaw": float(w["yaw"]), "pitch": 0.0}
		var vis: Array = hot.visible(int(n), d.items.keys())
		var mine := {}
		var others: Array = []
		var used := {str(p["waypoint"]): true}
		for it in vis:
			var hs: Dictionary = it["hs"]
			if int(hs.get("choice", -1)) == ret:
				mine = hs
			else:
				others.append(hs)
				if (hs["anchor"] as Dictionary).has("waypoint"):
					used[str(hs["anchor"]["waypoint"])] = true
		if mine.is_empty():
			continue
		var fwd := StoryProjector.forward(float(w["yaw"]))
		var rgt := StoryProjector.right(float(w["yaw"]))
		var cands: Array = []
		for wid in m.waypoints:
			if used.has(str(wid)) or (cams[str(p["map"])] as Dictionary).has(str(wid)) or str(wid).begins_with("way_up_") and str(wid) != "way_up_%d" % int(n):
				continue
			var wa: Vector2 = m.waypoints[wid]["at"]
			if wa.distance_to(at) < 1.0:
				continue
			cands.append({"anchor": {"waypoint": str(wid)}, "key": {"wp": str(wid)}, "score": absf((wa - at).dot(fwd) - 6.0) + absf((wa - at).dot(rgt)) * 0.5})
		cands.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return float(a["score"]) < float(b["score"]))
		var grid: Array = []
		for dd in [6.0, 5.0, 7.0, 4.5, 8.0, 9.0, 10.0, 11.0, 3.5]:
			for l in [2.0, -2.0, 3.0, -3.0, 1.0, -1.0, 4.0, -4.0, 0.0, 1.5, -1.5, 2.5, -2.5, 5.0, -5.0]:
				var g: Vector2 = at + fwd * dd + rgt * l
				if m.sector_at(g) != str(w["sector"]) or StoryMap._dist_to_boundary(g, m.sector(str(w["sector"]))["poly"]) < 0.6:
					continue
				var near := false
				for wid in m.waypoints:
					if str(wid) != "way_up_%d" % int(n):
						near = near or (m.waypoints[wid]["at"] as Vector2).distance_to(g) < 1.5
				if near:
					continue
				grid.append({"anchor": {"pos": [snappedf(g.x, 0.01), float(m.sector(str(w["sector"]))["floor"]), snappedf(g.y, 0.01)]}, "key": {"at": [snappedf(g.x, 0.01), snappedf(g.y, 0.01)], "sector": str(w["sector"])}})
		var base_entries: Array = []
		for o in others:
			base_entries.append({"hotspot": o, "state": "available"})
		var base_n: int = (HV.layout(base_entries, m, {}, pose, VIEW) as Array).size()  # (a passage whose own choices do not all lay out today keeps that: the return only must not make it worse)
		var found := {}
		for c in cands + grid:
			var h := mine.duplicate(true)
			h["anchor"] = c["anchor"]
			var entries: Array = [{"hotspot": h, "state": "available"}]
			for o in others:
				entries.append({"hotspot": o, "state": "available"})
			var lay: Array = HV.layout(entries, m, {}, pose, VIEW)
			var me_lay: Array = lay.filter(func(e: Dictionary) -> bool: return str(e["id"]) == str(h["id"]))
			if lay.size() != base_n + 1 or me_lay.is_empty():
				continue
			var hits := 0
			for e in lay:
				if HV.hit(lay, e["centre"]) == str(e["id"]):
					hits += 1
			if hits >= maxi(lay.size() - 1, 1) and HV.hit(lay, me_lay[0]["centre"]) == str(h["id"]):
				found = c["key"]
				break
		if found.is_empty():
			bad += 1
			print("passage %d: no spot" % int(n))
		else:
			res[str(int(n))] = found
	var f := FileAccess.open(out_path, FileAccess.WRITE)
	f.store_string(JSON.stringify(res, " "))
	f.close()
	print("return spots: %d passages, %d without a spot" % [res.size(), bad])
	quit(0)
