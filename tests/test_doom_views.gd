extends TestCase
## The Doom Warehouse pilot (docs/doom/scenes/warehouse.md, docs/doom/LAUNCH.md): the authored map, the overlay behind RW_DOOM_WORLDS, and the choice viewpoint.
## The view test projects the three guides from the reference viewpoint at 16:9 (a 1280 x 720 window: the stage strip is 1280 x 460, the pads below it) and at 20:9 (1600 x 720)
## and checks that each stands inside the picture, clear of the others, the HUD's corners and the pad strip. It cannot see walls: occlusion is checked by eye in the shots
## (tools/doom/shoot_scene.sh, docs/shots/doom/warehouse/).

const MAP_ID := "doom_warehouse"
const ASPECTS := {"16:9": Vector2(1280.0, 460.0), "20:9": Vector2(1600.0, 460.0)}
const HUD_BOXES := [Rect2(0, 0, 345, 100)]
const GUIDES := ["wh_guide_stage", "wh_guide_bar", "wh_guide_lounge"]
const HOLD_PLACES := ["wh_ref", "wh_fence", "wh_plinths", "wh_platform"]
const CHOICE_REF_HOLD := 8.0
const MIN_GUIDE_PX := 60.0  # the farthest guide (the stage's) must still be this tall in the 460 px stage strip


func _map() -> StoryMap:
	return StoryMap.load_chapter(MAP_ID, true)


func _pose_at(m: StoryMap, wp: String, world := MAP_ID) -> Dictionary:
	var p := StoryPlayer.new()
	p.setup(m, 174.0)
	p.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": wp, "bars": 0.01, "cut": true}, "world": world})
	return p.pose_at(2.0)


func _thing(m: StoryMap, id: String) -> Dictionary:
	for t in m.things:
		if str(t["id"]) == id:
			return t
	return {}


func _rect(m: StoryMap, id: String, pose: Dictionary, view: Vector2) -> Rect2:
	var t := _thing(m, id)
	var at: Vector2 = t["at"]
	var floor_y := float(m.sector(str(t["sector"]))["floor"])
	var lo := StoryProjector.project(Vector3(at.x, floor_y, at.y), pose, view)
	var hi := StoryProjector.project(Vector3(at.x, floor_y + float(t["size"]), at.y), pose, view)
	if float(lo["depth"]) < StoryProjector.NEAR:
		return Rect2()
	var half := 0.25 * float(t["size"]) * float(lo["scale"])
	var a: Vector2 = lo["screen"]
	var b: Vector2 = hi["screen"]
	return Rect2(minf(a.x, b.x) - half, minf(a.y, b.y), 2.0 * half, absf(a.y - b.y))


func test_the_authored_map_loads_with_every_waypoint_route_and_hold() -> void:
	var m := _map()
	assert_true(m != null and m.errors.is_empty(), "the map loads clean: %s" % str(m.errors if m != null else "null"))
	if m == null:
		return
	var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % MAP_ID))
	assert_true(bool((doc["doom"] as Dictionary).get("approximate", false)), "still flagged approximate")
	var routes: Dictionary = doc["scene"]["routes"]
	for k in ["ahead", "left", "right", "stay", "arrive", "stumble"]:
		assert_true(routes.has(k), "route %s exists" % k)
		for wid in routes[k]:
			assert_true(m.has_waypoint(str(wid)), "route %s: waypoint %s exists" % [k, wid])
	var holds := {}
	for w in doc["waypoints"]:
		holds[str(w["id"])] = float(w.get("hold_bars", 0.0))
	assert_true(float(holds["wh_ref"]) >= CHOICE_REF_HOLD, "the reference viewpoint holds at least 8 bars")
	for id in HOLD_PLACES:
		assert_true(float(holds[id]) > 0.0, "%s is a choice viewpoint with hold_bars" % id)
	assert_true(float((_pose_at(m, "wh_ref")["pos"] as Vector2).distance_to(m.waypoint("wh_ref")["at"])) < 0.05, "the camera stands at the reference viewpoint")


func test_the_three_guides_are_in_frame_apart_and_off_the_pad_strip_from_the_reference_viewpoint() -> void:
	var m := _map()
	if m == null:
		fail("map did not load")
		return
	var pose := _pose_at(m, "wh_ref")
	for asp in ASPECTS:
		var view: Vector2 = ASPECTS[asp]
		var rects := {}
		for g in GUIDES:
			var r := _rect(m, g, pose, view)
			rects[g] = r
			var inside := r.intersection(Rect2(Vector2.ZERO, view)).get_area()
			assert_true(r.get_area() > 0.0 and inside >= 0.95 * r.get_area(), "%s %s: inside the picture (%s)" % [asp, g, str(r)])
			assert_true(r.end.y <= view.y, "%s %s: its feet are above the pad strip" % [asp, g])
			assert_true(r.size.y >= MIN_GUIDE_PX, "%s %s: at least %d px tall at the reference viewpoint (%.0f)" % [asp, g, int(MIN_GUIDE_PX), r.size.y])
			for b in HUD_BOXES:
				assert_false(r.intersects(b), "%s %s: clear of the HUD's corner" % [asp, g])
			print("  %s %-16s rect %s" % [asp, g, str(r)])
		for i in GUIDES.size():
			for j in range(i + 1, GUIDES.size()):
				assert_false((rects[GUIDES[i]] as Rect2).intersects(rects[GUIDES[j]]), "%s: %s and %s do not overlap" % [asp, GUIDES[i], GUIDES[j]])


func test_no_guide_stands_too_near_a_place_the_camera_stands() -> void:
	var m := _map()
	if m == null:
		fail("map did not load")
		return
	for g in GUIDES:
		var at: Vector2 = _thing(m, g)["at"]
		for wid in m.waypoints:
			if str(wid) in ["wh_stage_top", "wh_bar_door", "wh_lounge_door"]:
				continue  # (the thresholds: the camera ends its approach near the guide on purpose, 1.5 m or more)
			assert_true((m.waypoints[wid]["at"] as Vector2).distance_to(at) >= 1.5, "%s is at least 1.5 m from %s" % [g, wid])
		for wid in ["wh_stage_top", "wh_bar_door", "wh_lounge_door"]:
			assert_true((m.waypoints[wid]["at"] as Vector2).distance_to(at) >= 1.2 or not (m.waypoints[wid]["at"] as Vector2).distance_to(at) < 3.0, "%s is not on top of %s" % [g, wid])


func test_the_overlay_is_off_by_default_and_loads_clean_when_the_flag_is_set() -> void:
	OS.set_environment("RW_DOOM_WORLDS", "")
	var off := RunData.load_default()
	assert_false(off.nodes.has("doom_warehouse"), "flag off: no doom scene")
	assert_true(off.nodes.has("warehouse"), "flag off: the legacy campaign is there")
	OS.set_environment("RW_DOOM_WORLDS", "1")
	var on := RunData.load_default()
	OS.set_environment("RW_DOOM_WORLDS", "")
	assert_true(on.errors.is_empty(), "flag on: the run loads clean: %s" % str(on.errors))
	for id in ["doom_warehouse", "warehouse"]:
		assert_true(on.nodes.has(id), "flag on: scene %s" % id)
	for id in ["doom_warehouse.balcony", "doom_warehouse.bar", "doom_warehouse.chill", "doom_warehouse.return"]:
		assert_false(on.nodes.has(id), "flag on: the stand-in %s is gone (the Warehouse is one geography scene)" % id)
	var hs: Array = on.hotspots.get("doom_warehouse", [])
	assert_eq(hs.size(), 4, "the three guides and the stay hotspot")
	var routes := []
	for h in hs:
		routes.append(str((h["on_success"] as Dictionary).get("route", "")))
	routes.sort()
	assert_eq(routes, ["doom_balcony", "doom_bar", "doom_lounge", "doom_warehouse"], "ahead the Balcony, left the Bar, right the Chill-out (the worlds' entry scenes), and stay on the floor")


# --- the whole overlay: eight one-scene geography worlds, routed by the brief's table (docs/briefs/DOOM_WORLDS_BRIEF.md) -------------------------------------------------------------

const DOOM_TABLE := {  # world -> [ahead (up), left, right]; "Floor" is doom_warehouse, "Chill-out" doom_lounge
	"doom_warehouse": ["doom_balcony", "doom_bar", "doom_lounge"],
	"doom_bar": ["doom_booth", "doom_warehouse", "doom_lounge"],
	"doom_balcony": ["doom_mothership", "doom_warehouse", "doom_booth"],
	"doom_lounge": ["doom_dock", "doom_bar", "doom_warehouse"],
	"doom_booth": ["doom_mothership", "doom_balcony", "doom_dock"],
	"doom_dock": ["doom_mothership", "doom_warehouse", "doom_underworld"],
	"doom_mothership": ["doom_underworld", "doom_booth", "doom_dock"],
	"doom_underworld": ["doom_mothership", "doom_warehouse", "doom_dock"],
}


func test_the_overlay_is_one_geography_graph_per_the_brief_table() -> void:
	var on := _doom_run()
	assert_eq(on.errors, [], "the overlay loads clean")
	var doom: Array = on.nodes.keys().filter(func(k: Variant) -> bool: return str(k).begins_with("doom_"))
	doom.sort()
	var want: Array = DOOM_TABLE.keys()
	want.sort()
	assert_eq(doom, want, "eight Doom scenes, one per world, no stand-in and no return scene")
	var j := RunJourney.new(on)
	for w in DOOM_TABLE:
		var n: Dictionary = on.nodes[w]
		assert_true(on.is_geography(w) and str(n["world"]) == w and bool(n["entry"]), "%s: the entry scene of its geography world" % w)
		assert_eq(int(n["depth"]), 1 if w == "doom_warehouse" else 2, "%s: depth" % w)
		var by_dir := {}
		for e in n["next"]:
			by_dir[str(e["dir"])] = e
		assert_eq(by_dir.size(), 4, "%s: the stay and three routes out" % w)
		var stay: Dictionary = by_dir.get("down", {})
		assert_true(str(stay.get("to", "")) == w and bool(stay.get("loop", false)), "%s: down is the stay loop" % w)
		var outs := []
		for d in ["up", "left", "right"]:
			outs.append(str((by_dir.get(d, {}) as Dictionary).get("to", "")))
		assert_eq(outs, DOOM_TABLE[w], "%s: up / left / right per the table" % w)
		var rail: Dictionary = n["rail"]
		for i in 3:
			var to: String = outs[i]
			var d: String = ["up", "left", "right"][i]
			assert_true(on.nodes.has(to) and bool(on.nodes[to]["entry"]) and on.is_geography(to) and to != w, "%s %s: %s is another world's entry scene" % [w, d, to])
			assert_eq(j.threshold_of(w, to), str(rail["exits"][d]), "%s %s: the threshold is the route move's end, the doorway" % [w, d])
			assert_eq(str(rail["routes"][d]["to"]), str(rail["exits"][d]), "%s %s: the route move ends at rail.exits.%s" % [w, d, d])
		var dests := []
		for h in on.hotspots.get(w, []):
			dests.append(str((h["on_success"] as Dictionary).get("route", "")))
		dests.sort()
		var wd: Array = (DOOM_TABLE[w] as Array) + [w]
		wd.sort()
		assert_eq(dests, wd, "%s: the guides lead to the three worlds, the stay hotspot stays" % w)
	var seen := {"doom_warehouse": true}
	var todo := ["doom_warehouse"]
	while not todo.is_empty():
		var w: String = todo.pop_back()
		for e in on.nodes[w]["next"]:
			var to := str(e["to"])
			if not seen.has(to):
				seen[to] = true
				todo.append(to)
	assert_eq(seen.size(), 8, "every world is reachable from the Warehouse floor: %s" % str(seen.keys()))


# --- the rail as polyline moves with holds, and the railing (docs/story/HEIGHTS_AND_PATHS.md) ---------------------------------------------------------------------------------

const DOOM_NODES := ["doom_warehouse"]  # the Warehouse world: one geography scene (its map); the other worlds are tested below
const REVEAL_HOLD := 2.0


func _doom_run() -> RunData:
	OS.set_environment("RW_DOOM_WORLDS", "1")
	var on := RunData.load_default()
	OS.set_environment("RW_DOOM_WORLDS", "")
	return on


func _moves_of(rail: Dictionary) -> Array:
	var out: Array = []
	for k in ["good", "bad"]:
		for p in rail[k]:
			out.append(p)
	for k in rail["routes"]:
		out.append(rail["routes"][k])
	return out


func test_the_rail_data_validates_and_every_route_is_a_via_polyline_with_holds() -> void:
	var on := _doom_run()
	for id in DOOM_NODES:
		var rail: Dictionary = on.nodes[id]["rail"]
		assert_eq(RunRail.validate(id, rail), [], "%s: RunRail.validate" % id)
		var routes: Dictionary = rail["routes"]
		for k in ["up", "left", "right", "stumble", "arrive"]:
			assert_true(routes.has(k) and typeof(routes[k]) == TYPE_DICTIONARY and routes[k].has("to"), "%s: route %s is a move" % [id, k])
		for k in ["up", "left", "right", "stumble"]:
			assert_true(typeof(routes[k].get("via")) == TYPE_ARRAY and not (routes[k]["via"] as Array).is_empty(), "%s: route %s has via waypoints" % [id, k])
			assert_true(float(routes[k].get("hold_bars", 0.0)) > 0.0 or k == "stumble", "%s: route %s holds at its end" % [id, k])
		for p in rail["good"]:
			assert_true(float(p.get("hold_bars", 0.0)) >= REVEAL_HOLD, "%s: good place %s holds at least %d bars" % [id, p["to"], int(REVEAL_HOLD)])
	var good: Array = on.nodes["doom_warehouse"]["rail"]["good"]
	assert_eq(good.size(), 4, "the stay loop has four places")
	for i in 3:
		assert_eq(float(good[i]["hold_bars"]), REVEAL_HOLD, "reveal viewpoint %s holds 2 bars" % good[i]["to"])
		assert_false(bool(good[i].get("choice", false)), "reveal viewpoint %s is not a choice viewpoint" % good[i]["to"])
	assert_eq(str(good[3]["to"]), "wh_ref", "the loop ends at the reference viewpoint")
	assert_true(bool(good[3].get("choice", false)), "wh_ref is a choice viewpoint")
	assert_eq(float(good[3]["hold_bars"]), 8.0, "wh_ref holds 8 bars")
	assert_true(float(good[3]["hold_bars"]) >= RunRail.CHOICE_HOLD_BARS, "the choice viewpoint holds at least the whole choice window")
	assert_true(on.nodes["doom_warehouse"]["rail"]["routes"]["up"]["via"].size() >= 3, "ahead is a polyline of several legs")


func test_every_via_waypoint_exists_and_stands_in_a_walkable_piece() -> void:
	var on := _doom_run()
	var m := _map()
	if m == null:
		fail("map did not load")
		return
	var reach := m.reachable_from(str(m.start_waypoint()["sector"]))
	var seen := 0
	for id in DOOM_NODES:
		var rail: Dictionary = on.nodes[id]["rail"]
		for mv in _moves_of(rail):
			var ids: Array = (mv.get("via", []) as Array).duplicate()
			ids.append(mv["to"])
			if mv.has("from"):
				ids.append(mv["from"])
			for wid in ids:
				assert_true(m.has_waypoint(str(wid)), "%s: waypoint %s exists" % [id, wid])
				if not m.has_waypoint(str(wid)):
					continue
				var w := m.waypoint(str(wid))
				var sid := str(w["sector"])
				seen += 1
				assert_true(m.inside(w["at"], sid, StoryMap.WAYPOINT_MARGIN), "%s: %s lies inside its piece %s with the margin" % [id, wid, sid])
				assert_false(m.is_void(sid), "%s: %s is not in a void" % [id, wid])
				assert_true(reach.has(sid), "%s: %s stands in a piece a walker reaches" % [id, wid])
				assert_true(float(m.sector(sid)["ceiling"]) - float(m.sector(sid)["floor"]) >= m.eye_height + 0.1, "%s: %s has room for the eye" % [id, wid])
	assert_true(seen > 25, "the loop looked at %d waypoint uses" % seen)


func test_check_rail_paths_reports_no_problem_for_the_warehouse() -> void:
	var on := _doom_run()
	var m := _map()
	if m == null:
		fail("map did not load")
		return
	for id in DOOM_NODES:
		var node: Dictionary = on.nodes[id]
		var errs := StoryRailCheck.check_rail(m, id, str(node["waypoint"]), node["rail"])
		assert_eq(errs, [], "%s: check_rail_paths finds nothing" % id)
	var moves := StoryRailCheck.rail_moves("doom_warehouse", "wh_ref", on.nodes["doom_warehouse"]["rail"])
	var named := 0
	for mv in moves:
		if str(mv["where"]).contains(" route "):
			named += 1
	assert_eq(named, 5, "the five routes (up, left, right, stumble, arrive) are checked as moves")


func test_the_railing_replaces_the_solid_ledge_and_the_map_keys_are_set() -> void:
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % MAP_ID))
	assert_eq(float(doc["max_step"]), 0.5, "max_step 0.5")
	assert_eq(str(doc["visibility"]["mode"]), "clip", "visibility mode clip")
	assert_true((doc["textures"] as Dictionary).has("wh_railing"), "the railing tile is one of the map's textures")
	var im := Image.load_from_file(ProjectSettings.globalize_path("res://assets/story/doom_warehouse/textures/wh_railing.png"))
	assert_true(im != null and im.get_width() == 128 and im.detect_alpha() != Image.ALPHA_NONE, "the railing tile is 128 px and has an alpha channel")
	var sec := {}
	for s in doc["sectors"]:
		sec[str(s["id"])] = s
	var ledge := 0
	var pit := 0
	for w in doc["walls"]:
		if str(w.get("kind", "")) != "railing":
			continue
		assert_eq(str(w["tex"]), "wh_railing", "a railing names the lattice tile")
		assert_eq(float(w["height"]), 1.0, "a railing is 1 m")
		var a: Dictionary = sec[str(w["sector"])]
		var b: Dictionary = sec[str(w["portal"])]
		var pair := [int(a["doom_sector"]), int(b["doom_sector"])]
		pair.sort()
		if pair == [9, 10]:
			ledge += 1
		elif minf(float(a["floor"]), float(b["floor"])) <= -2.0:
			pit += 1
	assert_eq(ledge, 6, "the ledge round the dance floor is six railing walls")
	assert_true(pit > 0, "the pits' rims carry railings (%d)" % pit)
	var m := _map()
	var closed_ledge := 0
	for p in m.portals():
		var ends := [str(p["a"]).split("_")[0], str(p["b"]).split("_")[0]]
		ends.sort()
		if bool(p["blocked"]) and ends == ["10", "9"]:
			closed_ledge += 1
	assert_true(closed_ledge >= 6, "the ledge portals are closed to walkers")


# --- the DJ Booth (docs/doom/scenes/booth.md): a separate block, its own constants -------------------------------------------------------------------------------------------

const BOOTH_MAP := "doom_booth"
const BOOTH_GUIDES := ["bt_guide_mothership", "bt_guide_balcony", "bt_guide_dock"]
const BOOTH_HOLD_PLACES := ["bt_ref", "bt_hatch_view", "bt_window_view", "bt_dock_view"]
const BOOTH_NODES := ["doom_booth"]
const BOOTH_EXITS := ["bt_hatch", "bt_bal_top", "bt_dock_in"]


func _booth_map() -> StoryMap:
	return StoryMap.load_chapter(BOOTH_MAP, true)


func _booth_pose(m: StoryMap, wp: String) -> Dictionary:
	var p := StoryPlayer.new()
	p.setup(m, 174.0)
	p.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": wp, "bars": 0.01, "cut": true}, "world": BOOTH_MAP})
	return p.pose_at(2.0)


func test_booth_map_loads_with_routes_holds_and_the_reference_viewpoint() -> void:
	var m := _booth_map()
	assert_true(m != null and m.errors.is_empty(), "the booth map loads clean: %s" % str(m.errors if m != null else "null"))
	if m == null:
		return
	var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % BOOTH_MAP))
	assert_true(bool((doc["doom"] as Dictionary).get("approximate", false)), "booth: still flagged approximate")
	var routes: Dictionary = doc["scene"]["routes"]
	for k in ["ahead", "left", "right", "stay", "arrive", "stumble"]:
		assert_true(routes.has(k), "booth route %s exists" % k)
		for wid in routes[k]:
			assert_true(m.has_waypoint(str(wid)), "booth route %s: waypoint %s exists" % [k, wid])
	var holds := {}
	for w in doc["waypoints"]:
		holds[str(w["id"])] = float(w.get("hold_bars", 0.0))
	assert_true(float(holds["bt_ref"]) >= CHOICE_REF_HOLD, "the booth's reference viewpoint holds at least 8 bars")
	for id in BOOTH_HOLD_PLACES:
		assert_true(float(holds[id]) > 0.0, "%s has hold_bars" % id)
	assert_true(float((_booth_pose(m, "bt_ref")["pos"] as Vector2).distance_to(m.waypoint("bt_ref")["at"])) < 0.05, "the camera stands at the booth's reference viewpoint")


func test_booth_three_guides_are_in_frame_apart_and_off_the_pad_strip_from_the_reference_viewpoint() -> void:
	var m := _booth_map()
	if m == null:
		fail("booth map did not load")
		return
	var pose := _booth_pose(m, "bt_ref")
	for asp in ASPECTS:
		var view: Vector2 = ASPECTS[asp]
		var rects := {}
		for g in BOOTH_GUIDES:
			var r := _rect(m, g, pose, view)
			rects[g] = r
			var inside := r.intersection(Rect2(Vector2.ZERO, view)).get_area()
			assert_true(r.get_area() > 0.0 and inside >= 0.95 * r.get_area(), "booth %s %s: inside the picture (%s)" % [asp, g, str(r)])
			assert_true(r.end.y <= view.y, "booth %s %s: its feet are above the pad strip" % [asp, g])
			assert_true(r.size.y >= MIN_GUIDE_PX, "booth %s %s: at least %d px tall (%.0f)" % [asp, g, int(MIN_GUIDE_PX), r.size.y])
			for b in HUD_BOXES:
				assert_false(r.intersects(b), "booth %s %s: clear of the HUD's corner" % [asp, g])
			print("  booth %s %-20s rect %s" % [asp, g, str(r)])
		for i in BOOTH_GUIDES.size():
			for j in range(i + 1, BOOTH_GUIDES.size()):
				assert_false((rects[BOOTH_GUIDES[i]] as Rect2).intersects(rects[BOOTH_GUIDES[j]]), "booth %s: %s and %s do not overlap" % [asp, BOOTH_GUIDES[i], BOOTH_GUIDES[j]])


func test_booth_guides_keep_their_distance_from_the_camera_places() -> void:
	var m := _booth_map()
	if m == null:
		fail("booth map did not load")
		return
	for g in BOOTH_GUIDES:
		var at: Vector2 = _thing(m, g)["at"]
		for wid in m.waypoints:
			var d: float = (m.waypoints[wid]["at"] as Vector2).distance_to(at)
			if str(wid) in BOOTH_EXITS:
				assert_true(d >= 1.2, "booth: %s is not on top of %s (%.1f m)" % [g, wid, d])
			else:
				assert_true(d >= 1.5, "booth: %s is at least 1.5 m from %s (%.1f m)" % [g, wid, d])


func test_booth_overlay_world_nodes_hotspots_and_rail_validate() -> void:
	var on := _doom_run()
	assert_true(on.errors.is_empty(), "booth: the run loads clean with the flag: %s" % str(on.errors))
	for id in BOOTH_NODES:
		assert_true(on.nodes.has(id), "booth: scene %s" % id)
	assert_true(on.nodes.has("doom_warehouse"), "the warehouse pilot is still there beside the booth")
	for id in BOOTH_NODES:
		var rail: Dictionary = on.nodes[id]["rail"]
		assert_eq(RunRail.validate(id, rail), [], "%s: RunRail.validate" % id)
		var routes: Dictionary = rail["routes"]
		for k in ["up", "left", "right", "stumble", "arrive"]:
			assert_true(routes.has(k) and routes[k].has("to"), "%s: route %s is a move" % [id, k])
		for k in ["up", "left", "right", "stumble"]:
			assert_false((routes[k].get("via", []) as Array).is_empty(), "%s: route %s has via waypoints" % [id, k])
		for k in ["up", "left", "right"]:
			assert_true(float(routes[k].get("hold_bars", 0.0)) > 0.0, "%s: route %s holds at its threshold" % [id, k])
	var good: Array = on.nodes["doom_booth"]["rail"]["good"]
	assert_eq(good.size(), 4, "booth: the stay loop has four places")
	for i in 3:
		assert_eq(float(good[i]["hold_bars"]), REVEAL_HOLD, "booth: reveal viewpoint %s holds 2 bars" % good[i]["to"])
		assert_false(bool(good[i].get("choice", false)), "booth: reveal viewpoint %s is not a choice viewpoint" % good[i]["to"])
	assert_eq(str(good[3]["to"]), "bt_ref", "booth: the loop ends at the reference viewpoint")
	assert_true(bool(good[3].get("choice", false)) and float(good[3]["hold_bars"]) >= RunRail.CHOICE_HOLD_BARS, "booth: bt_ref is a choice viewpoint holding the whole window")
	var hs: Array = on.hotspots.get("doom_booth", [])
	assert_eq(hs.size(), 4, "booth: three guides and the stay hotspot")
	var dests := []
	for h in hs:
		dests.append(str((h["on_success"] as Dictionary).get("route", "")))
		assert_true(h.has("show"), "booth: hotspot %s declares show" % h["id"])
		if str(h["id"]) != "doom_booth.exit_stay":
			assert_eq(str((h["show"] as Dictionary)["archetype"]), "figure", "booth: %s is a figure (a guide, no ring)" % h["id"])
	dests.sort()
	assert_eq(dests, ["doom_balcony", "doom_booth", "doom_dock", "doom_mothership"], "booth: ahead the Mothership, left the Balcony, right the Dock, and stay")


func test_booth_every_via_stands_in_a_walkable_piece_and_check_rail_paths_finds_nothing() -> void:
	var on := _doom_run()
	var m := _booth_map()
	if m == null:
		fail("booth map did not load")
		return
	var reach := m.reachable_from(str(m.start_waypoint()["sector"]))
	for id in BOOTH_NODES:
		var node: Dictionary = on.nodes[id]
		for mv in _moves_of(node["rail"]):
			var ids: Array = (mv.get("via", []) as Array).duplicate()
			ids.append(mv["to"])
			if mv.has("from"):
				ids.append(mv["from"])
			for wid in ids:
				assert_true(m.has_waypoint(str(wid)), "%s: waypoint %s exists" % [id, wid])
				if not m.has_waypoint(str(wid)):
					continue
				var sid := str(m.waypoint(str(wid))["sector"])
				assert_true(m.inside(m.waypoint(str(wid))["at"], sid, StoryMap.WAYPOINT_MARGIN) and reach.has(sid) and not m.is_void(sid), "%s: %s stands in a walkable piece" % [id, wid])
		assert_eq(StoryRailCheck.check_rail(m, id, str(node["waypoint"]), node["rail"]), [], "%s: check_rail_paths finds nothing" % id)


func test_booth_railing_visibility_decals_and_the_art_are_in_the_map() -> void:
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % BOOTH_MAP))
	assert_eq(float(doc["max_step"]), 0.5, "booth: max_step 0.5")
	assert_eq(str(doc["visibility"]["mode"]), "clip", "booth: visibility mode clip")
	var textures: Dictionary = doc["textures"]
	for k in ["bt_rail", "bt_window"]:
		assert_true(textures.has(k), "booth: %s is one of the map's textures" % k)
		var im := Image.load_from_file(ProjectSettings.globalize_path("res://assets/story/doom_booth/textures/%s.png" % k))
		assert_true(im != null and im.get_width() == 128 and im.detect_alpha() != Image.ALPHA_NONE, "booth: %s is a 128 px tile with an alpha channel" % k)
	var desk := 0
	var window := 0
	for w in doc["walls"]:
		if str(w.get("kind", "")) != "railing":
			continue
		assert_true(bool(w.get("blocked", false)), "booth: a railing is shut to walkers")
		if str(w["tex"]) == "bt_rail":
			desk += 1
		elif str(w["tex"]) == "bt_window":
			window += 1
	assert_eq(desk, 0, "booth: stage D polish: the desk stands on the floor as the painting's big foreground desk, no handrail before it (%d)" % desk)
	assert_true(window >= 1, "booth: the window onto the balcony is the mesh railing (%d)" % window)
	var decals := 0
	var lit := 0
	for t in doc["things"]:
		if str(t.get("kind", "")) == "decal":
			decals += 1
			if bool(t.get("emissive", false)):
				lit += 1
	assert_true(decals >= 8 and lit >= 5, "booth: wall decals (%d), the LEDs and screens emissive (%d)" % [decals, lit])
	for g in BOOTH_GUIDES:
		var stem: String = g.trim_prefix("bt_guide_")
		for st in ["idle_0", "available_0", "selected_0", "committed_0"]:
			assert_true(textures.has("guide_%s_%s" % [stem, st]), "booth: guide sprite %s_%s" % [stem, st])


# --- the Copper Bar (docs/doom/scenes/bar.md): its own world and map, the same checks -------------------------------------------------------------------------------------------

const BAR_ID := "doom_bar"
const BAR_GUIDES := ["wb_guide_booth", "wb_guide_floor", "wb_guide_chill"]
const BAR_NODES := ["doom_bar"]
const BAR_THRESHOLDS := ["wb_booth_door", "wb_floor_door", "wb_chill_door"]


func _bar() -> StoryMap:
	return StoryMap.load_chapter(BAR_ID, true)


func test_the_bar_map_loads_clean_with_every_route_waypoint_and_hold() -> void:
	var m := _bar()
	assert_true(m != null and m.errors.is_empty(), "the bar loads clean: %s" % str(m.errors if m != null else "null"))
	if m == null:
		return
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % BAR_ID))
	assert_true(bool((doc["doom"] as Dictionary).get("approximate", false)), "still flagged approximate")
	var routes: Dictionary = doc["scene"]["routes"]
	for k in ["ahead", "left", "right", "stay", "arrive", "stumble"]:
		assert_true(routes.has(k), "route %s exists" % k)
		for wid in routes[k]:
			assert_true(m.has_waypoint(str(wid)), "route %s: waypoint %s exists" % [k, wid])
	var holds := {}
	for w in doc["waypoints"]:
		holds[str(w["id"])] = float(w.get("hold_bars", 0.0))
	assert_true(float(holds["wb_ref"]) >= CHOICE_REF_HOLD, "the reference viewpoint holds at least 8 bars")
	for id in ["wb_ref", "wb_bridge", "wb_counter", "wb_way"]:
		assert_true(float(holds[id]) > 0.0, "%s has hold_bars" % id)
	assert_true((_pose_at(m, "wb_ref", BAR_ID)["pos"] as Vector2).distance_to(m.waypoint("wb_ref")["at"]) < 0.05, "the camera stands at the reference viewpoint")
	var yaw := float(m.waypoint("wb_ref")["yaw"])
	assert_true(absf(yaw) < 1.0, "the reference viewpoint looks north along the passage, as the painting does (yaw %.1f)" % yaw)


func test_the_bar_choice_viewpoint_shows_the_three_guides_in_frame_apart_and_off_the_pad_strip() -> void:
	var m := _bar()
	if m == null:
		fail("map did not load")
		return
	var pose := _pose_at(m, "wb_ref", BAR_ID)
	for asp in ASPECTS:
		var view: Vector2 = ASPECTS[asp]
		var rects := {}
		for g in BAR_GUIDES:
			var r := _rect(m, g, pose, view)
			rects[g] = r
			var inside := r.intersection(Rect2(Vector2.ZERO, view)).get_area()
			assert_true(r.get_area() > 0.0 and inside >= 0.95 * r.get_area(), "%s %s: inside the picture (%s)" % [asp, g, str(r)])
			assert_true(r.end.y <= view.y, "%s %s: its feet are above the pad strip" % [asp, g])
			assert_true(r.size.y >= MIN_GUIDE_PX, "%s %s: at least %d px tall (%.0f)" % [asp, g, int(MIN_GUIDE_PX), r.size.y])
			for b in HUD_BOXES:
				assert_false(r.intersects(b), "%s %s: clear of the HUD's corner" % [asp, g])
			print("  %s %-16s rect %s" % [asp, g, str(r)])
		for i in BAR_GUIDES.size():
			for j in range(i + 1, BAR_GUIDES.size()):
				assert_false((rects[BAR_GUIDES[i]] as Rect2).intersects(rects[BAR_GUIDES[j]]), "%s: %s and %s do not overlap" % [asp, BAR_GUIDES[i], BAR_GUIDES[j]])


func test_no_bar_guide_stands_in_a_wall_or_near_a_place_the_camera_stands() -> void:
	var m := _bar()
	if m == null:
		fail("map did not load")
		return
	for g in BAR_GUIDES:
		var t := _thing(m, g)
		var at: Vector2 = t["at"]
		assert_true(m.inside(at, str(t["sector"]), 0.2), "%s stands inside its piece, 0.2 m from its edges" % g)
		assert_false(m.is_void(str(t["sector"])), "%s is not in a void" % g)
		for wid in m.waypoints:
			var d: float = (m.waypoints[wid]["at"] as Vector2).distance_to(at)
			if str(wid) in BAR_THRESHOLDS:
				assert_true(d >= 1.2, "%s is at least 1.2 m from threshold %s" % [g, wid])
			elif not str(wid).begins_with("wb_v_"):
				assert_true(d >= 1.5, "%s is at least 1.5 m from %s" % [g, wid])
	var own := {"wb_booth_door": "wb_guide_booth", "wb_floor_door": "wb_guide_floor", "wb_chill_door": "wb_guide_chill"}
	for th in own:  # each threshold is toward its own guide: the nearest of the three guides to it is its own
		var p: Vector2 = m.waypoints[th]["at"]
		var best := ""
		var bd := 1e9
		for g in BAR_GUIDES:
			var dd := p.distance_to(_thing(m, g)["at"])
			if dd < bd:
				bd = dd
				best = g
		assert_eq(best, own[th], "threshold %s is nearest its own guide" % th)


func test_the_bar_overlay_loads_clean_with_its_world_nodes_and_figure_hotspots() -> void:
	var on := _doom_run()
	assert_true(on.errors.is_empty(), "flag on: the run loads clean: %s" % str(on.errors))
	for id in BAR_NODES:
		assert_true(on.nodes.has(id), "scene %s" % id)
	var back := []
	for e in on.nodes["doom_warehouse"]["next"]:
		back.append(str(e["to"]))
	assert_true(back.has("doom_bar"), "the Warehouse floor leads straight to the Copper Bar")
	var hs: Array = on.hotspots.get("doom_bar", [])
	assert_eq(hs.size(), 4, "three guides and the stay hotspot")
	var routes := []
	var m := _bar()
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % BAR_ID))
	var lights := {}
	for t in doc["things"]:
		if str(t.get("kind", "")) == "light":
			lights[str(t["id"])] = true
	for h in hs:
		routes.append(str((h["on_success"] as Dictionary).get("route", "")))
		if str(h["id"]).ends_with("exit_stay"):
			continue
		var show: Dictionary = h.get("show", {})
		assert_eq(str(show.get("archetype", "")), "figure", "%s is shown by a figure" % h["id"])
		var lamp := str(show.get("light", ""))
		assert_true(lights.has(lamp), "%s: its lamp %s is a light of the map" % [h["id"], lamp])
		assert_false(_thing(m, str((h["anchor"] as Dictionary)["thing"])).is_empty(), "%s: its guide is a thing of the map" % h["id"])
	routes.sort()
	assert_eq(routes, ["doom_bar", "doom_booth", "doom_lounge", "doom_warehouse"], "ahead the Booth, left the Floor, right the Chill-out, and stay")


func test_the_bar_rail_data_validates_and_every_route_is_a_via_polyline_with_holds() -> void:
	var on := _doom_run()
	for id in BAR_NODES:
		var rail: Dictionary = on.nodes[id]["rail"]
		assert_eq(RunRail.validate(id, rail), [], "%s: RunRail.validate" % id)
		var routes: Dictionary = rail["routes"]
		for k in ["up", "left", "right", "stumble", "arrive"]:
			assert_true(routes.has(k) and typeof(routes[k]) == TYPE_DICTIONARY and routes[k].has("to"), "%s: route %s is a move" % [id, k])
		for k in ["up", "left", "right", "stumble"]:
			assert_true(typeof(routes[k].get("via")) == TYPE_ARRAY and not (routes[k]["via"] as Array).is_empty(), "%s: route %s has via waypoints" % [id, k])
			assert_true(float(routes[k].get("hold_bars", 0.0)) > 0.0 or k == "stumble", "%s: route %s holds at its end" % [id, k])
		for p in rail["good"]:
			assert_true(float(p.get("hold_bars", 0.0)) >= REVEAL_HOLD, "%s: good place %s holds at least %d bars" % [id, p["to"], int(REVEAL_HOLD)])
	var good: Array = on.nodes["doom_bar"]["rail"]["good"]
	assert_eq(good.size(), 4, "the stay loop has four places")
	for i in 3:
		assert_eq(float(good[i]["hold_bars"]), REVEAL_HOLD, "reveal viewpoint %s holds 2 bars" % good[i]["to"])
		assert_false(bool(good[i].get("choice", false)), "reveal viewpoint %s is not a choice viewpoint" % good[i]["to"])
	assert_eq(str(good[3]["to"]), "wb_ref", "the loop ends at the reference viewpoint")
	assert_true(bool(good[3].get("choice", false)) and float(good[3]["hold_bars"]) == 8.0, "wb_ref is a choice viewpoint that holds 8 bars")
	var exits: Dictionary = on.nodes["doom_bar"]["rail"]["exits"]
	for k in ["up", "left", "right"]:
		assert_true(BAR_THRESHOLDS.has(str(exits[k])), "exit %s is a threshold" % k)


func test_every_bar_waypoint_stands_in_a_walkable_piece_and_check_rail_paths_finds_nothing() -> void:
	var on := _doom_run()
	var m := _bar()
	if m == null:
		fail("map did not load")
		return
	var reach := m.reachable_from(str(m.start_waypoint()["sector"]))
	for id in BAR_NODES:
		var node: Dictionary = on.nodes[id]
		for mv in _moves_of(node["rail"]):
			var ids: Array = (mv.get("via", []) as Array).duplicate()
			ids.append(mv["to"])
			if mv.has("from"):
				ids.append(mv["from"])
			for wid in ids:
				assert_true(m.has_waypoint(str(wid)), "%s: waypoint %s exists" % [id, wid])
				if not m.has_waypoint(str(wid)):
					continue
				var w := m.waypoint(str(wid))
				var sid := str(w["sector"])
				assert_true(m.inside(w["at"], sid, StoryMap.WAYPOINT_MARGIN), "%s: %s lies inside its piece with the margin" % [id, wid])
				assert_false(m.is_void(sid), "%s: %s is not in a void" % [id, wid])
				assert_true(reach.has(sid), "%s: %s stands in a piece a walker reaches" % [id, wid])
		assert_eq(StoryRailCheck.check_rail(m, id, str(node["waypoint"]), node["rail"]), [], "%s: check_rail_paths finds nothing" % id)
	var named := 0
	for mv in StoryRailCheck.rail_moves("doom_bar", "wb_ref", on.nodes["doom_bar"]["rail"]):
		if str(mv["where"]).contains(" route "):
			named += 1
	assert_eq(named, 5, "the five routes (up, left, right, stumble, arrive) are checked as moves")


func test_the_bar_has_its_railing_visibility_and_step_keys_set() -> void:
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % BAR_ID))
	assert_eq(float(doc["max_step"]), 0.5, "max_step 0.5")
	assert_eq(str(doc["visibility"]["mode"]), "clip", "visibility mode clip")
	assert_true((doc["textures"] as Dictionary).has("bar_railing"), "the railing tile is one of the map's textures")
	var im := Image.load_from_file(ProjectSettings.globalize_path("res://assets/story/doom_bar/textures/bar_railing.png"))
	assert_true(im != null and im.get_width() == 128 and im.detect_alpha() != Image.ALPHA_NONE, "the railing tile is 128 px and has an alpha channel")
	var sec := {}
	for s in doc["sectors"]:
		sec[str(s["id"])] = s
	var rails := 0
	for w in doc["walls"]:
		if str(w.get("kind", "")) != "railing":
			continue
		rails += 1
		assert_eq(str(w["tex"]), "bar_railing", "a railing names the copper lattice")
		assert_eq(float(w["height"]), 1.0, "a railing is 1 m")
		var a: Dictionary = sec[str(w["sector"])]
		var b: Dictionary = sec[str(w["portal"])]
		assert_true(absf(float(a["floor"]) - float(b["floor"])) > 0.5, "a railing stands where there is a drop")
		assert_true(minf(float(a["floor"]), float(b["floor"])) <= -0.9, "a railing is along the channel")
	assert_true(rails >= 6, "the channel's banks carry railings (%d)" % rails)
	var m := _bar()
	var steps := 0
	for p in m.portals():
		if bool(p["blocked"]):
			continue
		var d := absf(float(m.sector(str(p["a"]))["floor"]) - float(m.sector(str(p["b"]))["floor"]))
		if d > 0.0 and d <= 0.5 + 1e-6:
			steps += 1
	assert_true(steps >= 8, "the stairs, the bar's step and the nook's steps are open steps within max_step (%d)" % steps)
	var lights := 0
	var decals := 0
	for t in doc["things"]:
		if str(t.get("kind", "")) == "light":
			lights += 1
		if str(t.get("kind", "")) == "decal":
			decals += 1
	assert_true(lights >= 12 and decals >= 20, "practical lights (%d) and decals (%d) are authored" % [lights, decals])


# --- THE CHILL-OUT LOUNGE (docs/doom/scenes/lounge.md): its own block, its own map (doom_lounge) and world (doom_lounge) ----------------------------------------------------
# The octagonal hub on MAP08 Tricks and Traps: the reference viewpoint lg_ref on the south walkway, the Dock guide ahead (the rain street, N), the Bar guide left (NW arch), the Floor guide right
# (NE blue passage). Same view test as the Warehouse's: the guides inside the 16:9 and 20:9 picture, apart, off the pad strip, tall enough; and, because a projection cannot see walls, a
# sightline test from the camera to each guide against the solid walls.

const LMAP_ID := "doom_lounge"
const LGUIDES := ["lg_guide_dock", "lg_guide_bar", "lg_guide_floor"]
const LTHRESHOLDS := ["lg_ahead_door", "lg_bar_door", "lg_floor_door"]
const LHOLD_PLACES := ["lg_ref", "lg_west", "lg_north", "lg_east"]
const LOUNGE_NODES := ["doom_lounge"]


func _lmap() -> StoryMap:
	return StoryMap.load_chapter(LMAP_ID, true)


func _lpose_at(m: StoryMap, wp: String) -> Dictionary:
	var p := StoryPlayer.new()
	p.setup(m, 174.0)
	p.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": wp, "bars": 0.01, "cut": true}, "world": LMAP_ID})
	return p.pose_at(2.0)


func test_lounge_map_loads_clean_with_every_waypoint_route_hold_and_the_wall_art() -> void:
	var m := _lmap()
	assert_true(m != null and m.errors.is_empty(), "the lounge map loads clean: %s" % str(m.errors if m != null else "null"))
	if m == null:
		return
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % LMAP_ID))
	assert_true(bool((doc["doom"] as Dictionary).get("approximate", false)), "still flagged approximate")
	var routes: Dictionary = doc["scene"]["routes"]
	for k in ["ahead", "left", "right", "stay", "arrive", "stumble"]:
		assert_true(routes.has(k), "route %s exists" % k)
		for wid in routes[k]:
			assert_true(m.has_waypoint(str(wid)), "route %s: waypoint %s exists" % [k, wid])
	var holds := {}
	for w in doc["waypoints"]:
		holds[str(w["id"])] = float(w.get("hold_bars", 0.0))
	assert_true(float(holds["lg_ref"]) >= CHOICE_REF_HOLD, "the reference viewpoint holds at least 8 bars")
	for id in LHOLD_PLACES:
		assert_true(float(holds[id]) > 0.0, "%s is a viewpoint with hold_bars" % id)
	assert_true(float((_lpose_at(m, "lg_ref")["pos"] as Vector2).distance_to(m.waypoint("lg_ref")["at"])) < 0.05, "the camera stands at the reference viewpoint")
	# the keys the Doom renderer wants, the exposure and the wall art
	assert_eq(float(doc["max_step"]), 0.5, "max_step 0.5")
	assert_eq(str(doc["visibility"]["mode"]), "clip", "visibility mode clip")
	assert_true(doc.has("fog") and float(doc["fog"]["density"]) > 0.0, "the map has its fog")
	assert_true(m.decals.size() >= 20, "wall art: %d decals (studded panels, sconces, bottle shelf, record, bead curtains)" % m.decals.size())
	var tex: Dictionary = doc["textures"]
	for k in tex:
		var path := str(tex[k])
		if not path.begins_with("res://"):
			path = "res://assets/story/%s/%s" % [str(doc["art"]), path]
		assert_true(FileAccess.file_exists(path) or ResourceLoader.exists(path), "texture %s exists (%s)" % [k, path])
	for who in ["dock", "bar", "floor"]:
		for st in ["idle_0", "available_0", "available_4", "selected_1", "committed_1"]:
			assert_true(tex.has("guide_%s_%s" % [who, st]), "guide %s has its %s sprite" % [who, st])
	var steps_ok := true
	var room := {}  # piece id -> the room's name (the authoring writes `room_name`)
	for s in doc["sectors"]:
		room[str(s["id"])] = str(s.get("room_name", ""))
	for p in m.portals():
		if str(room[str(p["a"])]) == "left_counter" or str(room[str(p["b"])]) == "left_counter":
			continue  # (the bar counter is a 1.1 m island shut to walkers; the map loader wants it reachable, so one dead-end portal stays open: tools/doom/author_lounge.py barriers)
		if not bool(p["blocked"]):
			var fa := float(m.sector(str(p["a"]))["floor"])
			var fb := float(m.sector(str(p["b"]))["floor"])
			if absf(fa - fb) > 0.5 + 1.0e-6:
				steps_ok = false
	assert_true(steps_ok, "every portal a walker can use changes the floor by at most max_step")


func test_lounge_three_guides_are_in_frame_apart_and_off_the_pad_strip_from_the_reference_viewpoint() -> void:
	var m := _lmap()
	if m == null:
		fail("map did not load")
		return
	var pose := _lpose_at(m, "lg_ref")
	for asp in ASPECTS:
		var view: Vector2 = ASPECTS[asp]
		var rects := {}
		for g in LGUIDES:
			var r := _rect(m, g, pose, view)
			rects[g] = r
			var inside := r.intersection(Rect2(Vector2.ZERO, view)).get_area()
			assert_true(r.get_area() > 0.0 and inside >= 0.95 * r.get_area(), "%s %s: inside the picture (%s)" % [asp, g, str(r)])
			assert_true(r.end.y <= view.y, "%s %s: its feet are above the pad strip" % [asp, g])
			assert_true(r.size.y >= MIN_GUIDE_PX, "%s %s: at least %d px tall at the reference viewpoint (%.0f)" % [asp, g, int(MIN_GUIDE_PX), r.size.y])
			for b in HUD_BOXES:
				assert_false(r.intersects(b), "%s %s: clear of the HUD's corner" % [asp, g])
			print("  lounge %s %-14s rect %s" % [asp, g, str(r)])
		for i in LGUIDES.size():
			for j in range(i + 1, LGUIDES.size()):
				assert_false((rects[LGUIDES[i]] as Rect2).intersects(rects[LGUIDES[j]]), "%s: %s and %s do not overlap" % [asp, LGUIDES[i], LGUIDES[j]])


func test_lounge_each_guide_is_seen_from_the_reference_viewpoint_no_solid_wall_between() -> void:
	var m := _lmap()
	if m == null:
		fail("map did not load")
		return
	var cam: Vector2 = m.waypoint("lg_ref")["at"]
	for g in LGUIDES:
		var at: Vector2 = _thing(m, g)["at"]
		var hit := ""
		for w in m.resolved_walls():
			if str(w["portal"]) != "":
				continue  # (an opening, a step or a sofa: the eye passes over or through)
			if Geometry2D.segment_intersects_segment(cam, at, w["a"], w["b"]) != null:
				hit = "%s-%s" % [str(w["a"]), str(w["b"])]
				break
		assert_eq(hit, "", "%s: the sightline from lg_ref stays clear of solid walls" % g)


func test_lounge_no_guide_stands_too_near_a_place_the_camera_stands() -> void:
	var m := _lmap()
	if m == null:
		fail("map did not load")
		return
	for g in LGUIDES:
		var at: Vector2 = _thing(m, g)["at"]
		for wid in m.waypoints:
			if str(wid) in LTHRESHOLDS:
				assert_true((m.waypoints[wid]["at"] as Vector2).distance_to(at) >= 1.2, "%s is at least 1.2 m from the threshold %s" % [g, wid])
			else:
				assert_true((m.waypoints[wid]["at"] as Vector2).distance_to(at) >= 1.5, "%s is at least 1.5 m from %s" % [g, wid])


func test_lounge_overlay_has_its_world_scenes_hotspots_and_the_floor_reaches_it_through_its_exit() -> void:
	var on := _doom_run()
	assert_true(on.errors.is_empty(), "flag on: the run loads clean: %s" % str(on.errors))
	for id in LOUNGE_NODES:
		assert_true(on.nodes.has(id), "flag on: scene %s" % id)
		assert_eq(str(on.nodes[id]["map"]), LMAP_ID, "%s stands on the lounge map" % id)
	assert_true(bool(on.nodes["doom_lounge"]["entry"]) and str(on.nodes["doom_lounge"]["world"]) == "doom_lounge", "doom_lounge is the entry scene of its world")
	var hs: Array = on.hotspots.get("doom_lounge", [])
	assert_eq(hs.size(), 4, "the three guides and the stay hotspot")
	var routes := {}
	for h in hs:
		routes[str(h["id"])] = str((h["on_success"] as Dictionary).get("route", ""))
	assert_eq(routes["doom_lounge.exit_dock"], "doom_dock", "ahead: the Dock")
	assert_eq(routes["doom_lounge.exit_bar"], "doom_bar", "left: the Bar")
	assert_eq(routes["doom_lounge.exit_floor"], "doom_warehouse", "right: the Floor")
	assert_eq(routes["doom_lounge.exit_stay"], "doom_lounge", "bottom: stay")
	var back := []
	for e in on.nodes["doom_warehouse"]["next"]:
		back.append(str(e["to"]))
	assert_true(back.has("doom_lounge"), "the Warehouse floor leads straight to the lounge world")


func test_lounge_rail_data_validates_and_every_route_is_a_via_polyline_with_holds() -> void:
	var on := _doom_run()
	for id in LOUNGE_NODES:
		var rail: Dictionary = on.nodes[id]["rail"]
		assert_eq(RunRail.validate(id, rail), [], "%s: RunRail.validate" % id)
		var routes: Dictionary = rail["routes"]
		for k in ["up", "left", "right", "stumble", "arrive"]:
			assert_true(routes.has(k) and typeof(routes[k]) == TYPE_DICTIONARY and routes[k].has("to"), "%s: route %s is a move" % [id, k])
		for k in ["up", "left", "right", "stumble"]:
			assert_true(typeof(routes[k].get("via")) == TYPE_ARRAY and not (routes[k]["via"] as Array).is_empty(), "%s: route %s has via waypoints" % [id, k])
			assert_true(float(routes[k].get("hold_bars", 0.0)) > 0.0 or k == "stumble", "%s: route %s holds at its end" % [id, k])
		for p in rail["good"]:
			assert_true(float(p.get("hold_bars", 0.0)) >= REVEAL_HOLD, "%s: good place %s holds at least %d bars" % [id, p["to"], int(REVEAL_HOLD)])
	var good: Array = on.nodes["doom_lounge"]["rail"]["good"]
	assert_eq(good.size(), 4, "the stay loop has four places")
	for i in 3:
		assert_eq(float(good[i]["hold_bars"]), REVEAL_HOLD, "reveal viewpoint %s holds 2 bars" % good[i]["to"])
		assert_false(bool(good[i].get("choice", false)), "reveal viewpoint %s is not a choice viewpoint" % good[i]["to"])
	assert_eq(str(good[3]["to"]), "lg_ref", "the loop ends at the reference viewpoint")
	assert_true(bool(good[3].get("choice", false)) and float(good[3]["hold_bars"]) == 8.0, "lg_ref is a choice viewpoint holding 8 bars")
	assert_true(float(good[3]["hold_bars"]) >= RunRail.CHOICE_HOLD_BARS, "the choice viewpoint holds at least the whole choice window")
	assert_true(on.nodes["doom_lounge"]["rail"]["routes"]["up"]["via"].size() >= 4, "ahead is a polyline of several legs")


func test_lounge_every_via_waypoint_exists_and_stands_in_a_walkable_piece() -> void:
	var on := _doom_run()
	var m := _lmap()
	if m == null:
		fail("map did not load")
		return
	var reach := m.reachable_from(str(m.start_waypoint()["sector"]))
	var seen := 0
	for id in LOUNGE_NODES:
		for mv in _moves_of(on.nodes[id]["rail"]):
			var ids: Array = (mv.get("via", []) as Array).duplicate()
			ids.append(mv["to"])
			if mv.has("from"):
				ids.append(mv["from"])
			for wid in ids:
				assert_true(m.has_waypoint(str(wid)), "%s: waypoint %s exists" % [id, wid])
				if not m.has_waypoint(str(wid)):
					continue
				var w := m.waypoint(str(wid))
				var sid := str(w["sector"])
				seen += 1
				assert_true(m.inside(w["at"], sid, StoryMap.WAYPOINT_MARGIN), "%s: %s lies inside its piece %s with the margin" % [id, wid, sid])
				assert_false(m.is_void(sid), "%s: %s is not in a void" % [id, wid])
				assert_true(reach.has(sid), "%s: %s stands in a piece a walker reaches" % [id, wid])
				assert_true(float(m.sector(sid)["ceiling"]) - float(m.sector(sid)["floor"]) >= m.eye_height + 0.1, "%s: %s has room for the eye" % [id, wid])
	assert_true(seen > 30, "the loop looked at %d waypoint uses" % seen)


func test_lounge_check_rail_paths_reports_no_problem() -> void:
	var on := _doom_run()
	var m := _lmap()
	if m == null:
		fail("map did not load")
		return
	for id in LOUNGE_NODES:
		var node: Dictionary = on.nodes[id]
		assert_eq(StoryRailCheck.check_rail(m, id, str(node["waypoint"]), node["rail"]), [], "%s: check_rail_paths finds nothing" % id)
	var named := 0
	for mv in StoryRailCheck.rail_moves("doom_lounge", "lg_ref", on.nodes["doom_lounge"]["rail"]):
		if str(mv["where"]).contains(" route "):
			named += 1
	assert_eq(named, 5, "the five routes (up, left, right, stumble, arrive) are checked as moves")


# --- THE LOADING DOCK (docs/doom/scenes/dock.md): its own block, its own map (doom_dock) and world (doom_dock) --------------------------------------------------------------------
# MAP13 Downtown, invented from the painting: the reference viewpoint dk_ref on the concrete apron looking up the wet street, the Floor guide left (the club door), the Mothership guide ahead (the
# street's end), the Underworld guide right (the furnace in the yard). The same checks as the Booth's, plus a sightline test from the camera to each guide against the solid walls.

const DK_MAP := "doom_dock"
const DK_GUIDES := ["dk_guide_mothership", "dk_guide_floor", "dk_guide_underworld"]
const DK_HOLD_PLACES := ["dk_ref", "dk_street_view", "dk_door_view", "dk_yard_view"]
const DK_NODES := ["doom_dock"]
const DK_EXITS := ["dk_moth", "dk_floor_door", "dk_under"]


func _dk_map() -> StoryMap:
	return StoryMap.load_chapter(DK_MAP, true)


func _dk_pose(m: StoryMap, wp: String) -> Dictionary:
	var p := StoryPlayer.new()
	p.setup(m, 174.0)
	p.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": wp, "bars": 0.01, "cut": true}, "world": DK_MAP})
	return p.pose_at(2.0)


func test_dock_map_loads_with_routes_holds_and_the_reference_viewpoint() -> void:
	var m := _dk_map()
	assert_true(m != null and m.errors.is_empty(), "the dock map loads clean: %s" % str(m.errors if m != null else "null"))
	if m == null:
		return
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % DK_MAP))
	assert_true(bool((doc["doom"] as Dictionary).get("approximate", false)), "dock: still flagged approximate")
	var routes: Dictionary = doc["scene"]["routes"]
	for k in ["ahead", "left", "right", "stay", "arrive", "stumble"]:
		assert_true(routes.has(k), "dock route %s exists" % k)
		for wid in routes[k]:
			assert_true(m.has_waypoint(str(wid)), "dock route %s: waypoint %s exists" % [k, wid])
	var holds := {}
	for w in doc["waypoints"]:
		holds[str(w["id"])] = float(w.get("hold_bars", 0.0))
	assert_true(float(holds["dk_ref"]) >= CHOICE_REF_HOLD, "the dock's reference viewpoint holds at least 8 bars")
	for id in DK_HOLD_PLACES:
		assert_true(float(holds[id]) > 0.0, "%s has hold_bars" % id)
	for id in DK_EXITS:
		assert_true(float(holds[id]) > 0.0, "the threshold %s holds" % id)
	assert_true(float((_dk_pose(m, "dk_ref")["pos"] as Vector2).distance_to(m.waypoint("dk_ref")["at"])) < 0.05, "the camera stands at the dock's reference viewpoint")
	assert_eq(float(doc["max_step"]), 0.5, "dock: max_step 0.5")
	assert_eq(str(doc["visibility"]["mode"]), "clip", "dock: visibility mode clip")
	assert_true(doc.has("fog") and float(doc["fog"]["density"]) > 0.0, "dock: the map has its fog")


func test_dock_three_guides_are_in_frame_apart_and_off_the_pad_strip_from_the_reference_viewpoint() -> void:
	var m := _dk_map()
	if m == null:
		fail("dock map did not load")
		return
	var pose := _dk_pose(m, "dk_ref")
	for asp in ASPECTS:
		var view: Vector2 = ASPECTS[asp]
		var rects := {}
		for g in DK_GUIDES:
			var r := _rect(m, g, pose, view)
			rects[g] = r
			var inside := r.intersection(Rect2(Vector2.ZERO, view)).get_area()
			assert_true(r.get_area() > 0.0 and inside >= 0.95 * r.get_area(), "dock %s %s: inside the picture (%s)" % [asp, g, str(r)])
			assert_true(r.end.y <= view.y, "dock %s %s: its feet are above the pad strip" % [asp, g])
			assert_true(r.size.y >= MIN_GUIDE_PX, "dock %s %s: at least %d px tall (%.0f)" % [asp, g, int(MIN_GUIDE_PX), r.size.y])
			for b in HUD_BOXES:
				assert_false(r.intersects(b), "dock %s %s: clear of the HUD's corner" % [asp, g])
			print("  dock %s %-22s rect %s" % [asp, g, str(r)])
		for i in DK_GUIDES.size():
			for j in range(i + 1, DK_GUIDES.size()):
				assert_false((rects[DK_GUIDES[i]] as Rect2).intersects(rects[DK_GUIDES[j]]), "dock %s: %s and %s do not overlap" % [asp, DK_GUIDES[i], DK_GUIDES[j]])


func test_dock_each_guide_is_seen_from_the_reference_viewpoint_no_solid_wall_between() -> void:
	var m := _dk_map()
	if m == null:
		fail("dock map did not load")
		return
	var cam: Vector2 = m.waypoint("dk_ref")["at"]
	for g in DK_GUIDES:
		var at: Vector2 = _thing(m, g)["at"]
		var hit := ""
		for w in m.resolved_walls():
			if str(w["portal"]) != "":
				continue  # (an opening, a kerb: the eye passes over or through)
			if Geometry2D.segment_intersects_segment(cam, at, w["a"], w["b"]) != null:
				hit = "%s-%s" % [str(w["a"]), str(w["b"])]
				break
		assert_eq(hit, "", "dock %s: the sightline from dk_ref stays clear of solid walls" % g)


func test_dock_guides_keep_their_distance_from_the_camera_places() -> void:
	var m := _dk_map()
	if m == null:
		fail("dock map did not load")
		return
	for g in DK_GUIDES:
		var at: Vector2 = _thing(m, g)["at"]
		for wid in m.waypoints:
			var d: float = (m.waypoints[wid]["at"] as Vector2).distance_to(at)
			if str(wid) in DK_EXITS:
				assert_true(d >= 1.2, "dock: %s is not on top of %s (%.1f m)" % [g, wid, d])
			else:
				assert_true(d >= 1.5, "dock: %s is at least 1.5 m from %s (%.1f m)" % [g, wid, d])


func test_dock_overlay_world_nodes_hotspots_and_rail_validate() -> void:
	var on := _doom_run()
	assert_true(on.errors.is_empty(), "dock: the run loads clean with the flag: %s" % str(on.errors))
	for id in DK_NODES:
		assert_true(on.nodes.has(id), "dock: scene %s" % id)
		assert_eq(str(on.nodes[id]["map"]), DK_MAP, "dock: %s stands on the dock map" % id)
	assert_true(bool(on.nodes["doom_dock"]["entry"]) and str(on.nodes["doom_dock"]["world"]) == "doom_dock", "doom_dock is the entry scene of its world")
	assert_true(on.nodes.has("doom_booth") and on.nodes.has("doom_lounge"), "the earlier worlds are still there beside the dock")
	for id in DK_NODES:
		var rail: Dictionary = on.nodes[id]["rail"]
		assert_eq(RunRail.validate(id, rail), [], "%s: RunRail.validate" % id)
		var routes: Dictionary = rail["routes"]
		for k in ["up", "left", "right", "stumble", "arrive"]:
			assert_true(routes.has(k) and routes[k].has("to"), "%s: route %s is a move" % [id, k])
		for k in ["up", "left", "right", "stumble"]:
			assert_false((routes[k].get("via", []) as Array).is_empty(), "%s: route %s has via waypoints" % [id, k])
		for k in ["up", "left", "right"]:
			assert_true(float(routes[k].get("hold_bars", 0.0)) > 0.0, "%s: route %s holds at its threshold" % [id, k])
		var ex: Dictionary = rail["exits"]
		assert_eq([str(ex["up"]), str(ex["left"]), str(ex["right"])], DK_EXITS, "%s: rail.exits name the three thresholds" % id)
		var dirs := ["up", "left", "right"]
		for i in 3:
			assert_eq(str(routes[dirs[i]]["to"]), DK_EXITS[i], "%s: the route's move ends at the threshold" % id)
	var good: Array = on.nodes["doom_dock"]["rail"]["good"]
	assert_eq(good.size(), 4, "dock: the stay loop has four places")
	for i in 3:
		assert_eq(float(good[i]["hold_bars"]), REVEAL_HOLD, "dock: reveal viewpoint %s holds 2 bars" % good[i]["to"])
		assert_false(bool(good[i].get("choice", false)), "dock: reveal viewpoint %s is not a choice viewpoint" % good[i]["to"])
	assert_eq(str(good[3]["to"]), "dk_ref", "dock: the loop ends at the reference viewpoint")
	assert_true(bool(good[3].get("choice", false)) and float(good[3]["hold_bars"]) >= RunRail.CHOICE_HOLD_BARS, "dock: dk_ref is a choice viewpoint holding the whole window")
	var hs: Array = on.hotspots.get("doom_dock", [])
	assert_eq(hs.size(), 4, "dock: three guides and the stay hotspot")
	var dests := []
	for h in hs:
		dests.append(str((h["on_success"] as Dictionary).get("route", "")))
		assert_true(h.has("show"), "dock: hotspot %s declares show" % h["id"])
		if str(h["id"]) != "doom_dock.exit_stay":
			assert_eq(str((h["show"] as Dictionary)["archetype"]), "figure", "dock: %s is a figure (a guide, no ring)" % h["id"])
	dests.sort()
	assert_eq(dests, ["doom_dock", "doom_mothership", "doom_underworld", "doom_warehouse"], "dock: ahead the Mothership, left the Floor, right the Underworld, and stay")


func test_dock_every_via_stands_in_a_walkable_piece_and_check_rail_paths_finds_nothing() -> void:
	var on := _doom_run()
	var m := _dk_map()
	if m == null:
		fail("dock map did not load")
		return
	var reach := m.reachable_from(str(m.start_waypoint()["sector"]))
	for id in DK_NODES:
		var node: Dictionary = on.nodes[id]
		for mv in _moves_of(node["rail"]):
			var ids: Array = (mv.get("via", []) as Array).duplicate()
			ids.append(mv["to"])
			if mv.has("from"):
				ids.append(mv["from"])
			for wid in ids:
				assert_true(m.has_waypoint(str(wid)), "%s: waypoint %s exists" % [id, wid])
				if not m.has_waypoint(str(wid)):
					continue
				var sid := str(m.waypoint(str(wid))["sector"])
				assert_true(m.inside(m.waypoint(str(wid))["at"], sid, StoryMap.WAYPOINT_MARGIN) and reach.has(sid) and not m.is_void(sid), "%s: %s stands in a walkable piece" % [id, wid])
		assert_eq(StoryRailCheck.check_rail(m, id, str(node["waypoint"]), node["rail"]), [], "%s: check_rail_paths finds nothing" % id)


func test_dock_walls_decals_lights_and_the_art_are_in_the_map() -> void:
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % DK_MAP))
	var textures: Dictionary = doc["textures"]
	for k in textures:
		var path := "res://assets/story/%s/%s" % [str(doc["art"]), str(textures[k])]
		assert_true(FileAccess.file_exists(path) or ResourceLoader.exists(path), "dock: texture %s exists (%s)" % [k, path])
	var decals := 0
	var lit := 0
	var lights := 0
	for t in doc["things"]:
		match str(t.get("kind", "")):
			"decal":
				decals += 1
				if bool(t.get("emissive", false)):
					lit += 1
			"light":
				lights += 1
	assert_true(decals >= 15 and lit >= 8, "dock: wall decals (%d), the lit windows, towers and neon emissive (%d)" % [decals, lit])
	assert_true(lights >= 12, "dock: light things (%d: sodium, blue spill, furnace, violet)" % lights)
	for k in ["dk_wall_brick", "dk_wall_shutter", "dk_floor_asphalt", "dk_floor_conc", "dk_furnace", "dk_van", "dk_bollard", "dk_fence"]:
		assert_true(textures.has(k), "dock: %s is one of the map's textures" % k)
	for g in DK_GUIDES:
		var stem: String = g.trim_prefix("dk_guide_")
		for st in ["idle_0", "available_0", "selected_0", "committed_0"]:
			assert_true(textures.has("guide_%s_%s" % [stem, st]), "dock: guide sprite %s_%s" % [stem, st])
	var steps_ok := true
	var m := _dk_map()
	if m != null:
		for p in m.portals():
			if not bool(p["blocked"]) and absf(float(m.sector(str(p["a"]))["floor"]) - float(m.sector(str(p["b"]))["floor"])) > 0.5 + 1.0e-6:
				steps_ok = false
	assert_true(steps_ok, "dock: every portal a walker can use changes the floor by at most max_step")


# --- THE UNDERWORLD (docs/doom/scenes/underworld.md): its own block, its own map (doom_underworld) and world (doom_underworld) -----------------------------------------------------
# MAP29 The Living End as a basalt plateau over a lava abyss: the reference viewpoint uw_ref, the Mothership guide up the ledge ahead, the Floor guide at the cave mouth left, the Dock guide on the
# shelf right. The same checks as the Booth's, plus a sightline test from the camera to each guide against the solid walls, and the abyss: every abyss sector is a void, no waypoint is in it,
# every portal onto it is a closed railing (but one dead end the map loader needs for reachability).

const UW_MAP := "doom_underworld"
const UW_GUIDES := ["uw_guide_mothership", "uw_guide_floor", "uw_guide_dock"]
const UW_HOLD_PLACES := ["uw_ref", "uw_ledge_view", "uw_cave_view", "uw_stair_view"]
const UW_NODES := ["doom_underworld"]
const UW_EXITS := ["uw_gate", "uw_cave_in", "uw_shelf_end"]


func _uw_map() -> StoryMap:
	return StoryMap.load_chapter(UW_MAP, true)


func _uw_pose(m: StoryMap, wp: String) -> Dictionary:
	var p := StoryPlayer.new()
	p.setup(m, 174.0)
	p.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": wp, "bars": 0.01, "cut": true}, "world": UW_MAP})
	return p.pose_at(2.0)


func test_underworld_map_loads_with_routes_holds_and_the_reference_viewpoint() -> void:
	var m := _uw_map()
	assert_true(m != null and m.errors.is_empty(), "the underworld map loads clean: %s" % str(m.errors if m != null else "null"))
	if m == null:
		return
	var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % UW_MAP))
	assert_true(bool((doc["doom"] as Dictionary).get("approximate", false)), "underworld: still flagged approximate")
	assert_eq(float(doc["max_step"]), 0.5, "underworld: max_step 0.5")
	assert_eq(str(doc["visibility"]["mode"]), "clip", "underworld: visibility mode clip")
	var routes: Dictionary = doc["scene"]["routes"]
	for k in ["ahead", "left", "right", "stay", "arrive", "stumble"]:
		assert_true(routes.has(k), "underworld route %s exists" % k)
		for wid in routes[k]:
			assert_true(m.has_waypoint(str(wid)), "underworld route %s: waypoint %s exists" % [k, wid])
	var holds := {}
	for w in doc["waypoints"]:
		holds[str(w["id"])] = float(w.get("hold_bars", 0.0))
	assert_true(float(holds["uw_ref"]) >= CHOICE_REF_HOLD, "the underworld's reference viewpoint holds at least 8 bars")
	for id in UW_HOLD_PLACES:
		assert_true(float(holds[id]) > 0.0, "%s has hold_bars" % id)
	for id in UW_EXITS:
		assert_true(float(holds[id]) > 0.0, "the threshold %s holds" % id)
	assert_true(float((_uw_pose(m, "uw_ref")["pos"] as Vector2).distance_to(m.waypoint("uw_ref")["at"])) < 0.05, "the camera stands at the underworld's reference viewpoint")


func test_underworld_three_guides_are_in_frame_apart_and_off_the_pad_strip_from_the_reference_viewpoint() -> void:
	var m := _uw_map()
	if m == null:
		fail("underworld map did not load")
		return
	var pose := _uw_pose(m, "uw_ref")
	# round 2: the choice hold at uw_ref carries a steady pitch (the run's rail place `pitch`, docs/engine/GEOGRAPHY_WORLDS.md): the guides are checked at the PITCHED pose the window holds
	var good: Array = _doom_run().nodes["doom_underworld"]["rail"]["good"]
	var pitch := float((good[3] as Dictionary).get("pitch", 0.0))
	assert_true(pitch <= -10.0 and pitch >= -35.0, "underworld: uw_ref holds a downward pitch over the lava (%.1f)" % pitch)
	pose["pitch"] = pitch
	for asp in ASPECTS:
		var view: Vector2 = ASPECTS[asp]
		var rects := {}
		for g in UW_GUIDES:
			var r := _rect(m, g, pose, view)
			rects[g] = r
			var inside := r.intersection(Rect2(Vector2.ZERO, view)).get_area()
			assert_true(r.get_area() > 0.0 and inside >= 0.95 * r.get_area(), "underworld %s %s: inside the picture (%s)" % [asp, g, str(r)])
			assert_true(r.end.y <= view.y, "underworld %s %s: its feet are above the pad strip" % [asp, g])
			assert_true(r.size.y >= MIN_GUIDE_PX, "underworld %s %s: at least %d px tall (%.0f)" % [asp, g, int(MIN_GUIDE_PX), r.size.y])
			for b in HUD_BOXES:
				assert_false(r.intersects(b), "underworld %s %s: clear of the HUD's corner" % [asp, g])
			print("  underworld %s %-22s rect %s" % [asp, g, str(r)])
		for i in UW_GUIDES.size():
			for j in range(i + 1, UW_GUIDES.size()):
				assert_false((rects[UW_GUIDES[i]] as Rect2).intersects(rects[UW_GUIDES[j]]), "underworld %s: %s and %s do not overlap" % [asp, UW_GUIDES[i], UW_GUIDES[j]])


func test_underworld_each_guide_is_seen_from_the_reference_viewpoint_no_solid_wall_between() -> void:
	var m := _uw_map()
	if m == null:
		fail("underworld map did not load")
		return
	var cam: Vector2 = m.waypoint("uw_ref")["at"]
	for g in UW_GUIDES:
		var at: Vector2 = _thing(m, g)["at"]
		var hit := ""
		for w in m.resolved_walls():
			if str(w["portal"]) != "":
				continue  # (an opening, a step or a railing: the eye passes over or through)
			if Geometry2D.segment_intersects_segment(cam, at, w["a"], w["b"]) != null:
				hit = "%s-%s" % [str(w["a"]), str(w["b"])]
				break
		assert_eq(hit, "", "%s: the sightline from uw_ref stays clear of solid walls" % g)


func test_underworld_guides_keep_their_distance_from_the_camera_places() -> void:
	var m := _uw_map()
	if m == null:
		fail("underworld map did not load")
		return
	for g in UW_GUIDES:
		var at: Vector2 = _thing(m, g)["at"]
		for wid in m.waypoints:
			var d: float = (m.waypoints[wid]["at"] as Vector2).distance_to(at)
			if str(wid) in UW_EXITS:
				assert_true(d >= 1.2, "underworld: %s is not on top of %s (%.1f m)" % [g, wid, d])
			else:
				assert_true(d >= 1.5, "underworld: %s is at least 1.5 m from %s (%.1f m)" % [g, wid, d])


func test_underworld_overlay_world_nodes_hotspots_and_rail_validate() -> void:
	var on := _doom_run()
	assert_true(on.errors.is_empty(), "underworld: the run loads clean with the flag: %s" % str(on.errors))
	for id in UW_NODES:
		assert_true(on.nodes.has(id), "underworld: scene %s" % id)
	assert_true(on.nodes.has("doom_warehouse") and on.nodes.has("doom_booth"), "the warehouse and the booth are still there beside the underworld")
	for id in UW_NODES:
		var rail: Dictionary = on.nodes[id]["rail"]
		assert_eq(RunRail.validate(id, rail), [], "%s: RunRail.validate" % id)
		var routes: Dictionary = rail["routes"]
		for k in ["up", "left", "right", "stumble", "arrive"]:
			assert_true(routes.has(k) and routes[k].has("to"), "%s: route %s is a move" % [id, k])
		for k in ["up", "left", "right", "stumble"]:
			assert_false((routes[k].get("via", []) as Array).is_empty(), "%s: route %s has via waypoints" % [id, k])
		for k in ["up", "left", "right"]:
			assert_true(float(routes[k].get("hold_bars", 0.0)) > 0.0, "%s: route %s holds at its threshold" % [id, k])
		assert_eq([str(routes["up"]["to"]), str(routes["left"]["to"]), str(routes["right"]["to"])], UW_EXITS, "%s: the thresholds are the exits' waypoints" % id)
	var good: Array = on.nodes["doom_underworld"]["rail"]["good"]
	assert_eq(good.size(), 4, "underworld: the stay loop has four places")
	for i in 3:
		assert_eq(float(good[i]["hold_bars"]), REVEAL_HOLD, "underworld: reveal viewpoint %s holds 2 bars" % good[i]["to"])
		assert_false(bool(good[i].get("choice", false)), "underworld: reveal viewpoint %s is not a choice viewpoint" % good[i]["to"])
	assert_eq(str(good[3]["to"]), "uw_ref", "underworld: the loop ends at the reference viewpoint")
	assert_true(bool(good[3].get("choice", false)) and float(good[3]["hold_bars"]) >= RunRail.CHOICE_HOLD_BARS, "underworld: uw_ref is a choice viewpoint holding the whole window")
	var hs: Array = on.hotspots.get("doom_underworld", [])
	assert_eq(hs.size(), 4, "underworld: three guides and the stay hotspot")
	var dests := []
	for h in hs:
		dests.append(str((h["on_success"] as Dictionary).get("route", "")))
		assert_true(h.has("show"), "underworld: hotspot %s declares show" % h["id"])
		if str(h["id"]) != "doom_underworld.exit_stay":
			assert_eq(str((h["show"] as Dictionary)["archetype"]), "figure", "underworld: %s is a figure (a guide, no ring)" % h["id"])
	dests.sort()
	assert_eq(dests, ["doom_dock", "doom_mothership", "doom_underworld", "doom_warehouse"], "underworld: ahead the Mothership, left the Floor, right the Dock, and stay")


func test_underworld_every_via_stands_in_a_walkable_piece_and_check_rail_paths_finds_nothing() -> void:
	var on := _doom_run()
	var m := _uw_map()
	if m == null:
		fail("underworld map did not load")
		return
	var reach := m.reachable_from(str(m.start_waypoint()["sector"]))
	for id in UW_NODES:
		var node: Dictionary = on.nodes[id]
		for mv in _moves_of(node["rail"]):
			var ids: Array = (mv.get("via", []) as Array).duplicate()
			ids.append(mv["to"])
			if mv.has("from"):
				ids.append(mv["from"])
			for wid in ids:
				assert_true(m.has_waypoint(str(wid)), "%s: waypoint %s exists" % [id, wid])
				if not m.has_waypoint(str(wid)):
					continue
				var sid := str(m.waypoint(str(wid))["sector"])
				assert_true(m.inside(m.waypoint(str(wid))["at"], sid, StoryMap.WAYPOINT_MARGIN) and reach.has(sid) and not m.is_void(sid), "%s: %s stands in a walkable piece" % [id, wid])
		assert_eq(StoryRailCheck.check_rail(m, id, str(node["waypoint"]), node["rail"]), [], "%s: check_rail_paths finds nothing" % id)


func test_underworld_the_abyss_is_a_void_shut_by_railings_and_the_art_is_in_the_map() -> void:
	var m := _uw_map()
	if m == null:
		fail("underworld map did not load")
		return
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % UW_MAP))
	var abyss := {}
	var lava_floor := 0.0
	for s in doc["sectors"]:
		if str(s.get("room_name", "")).begins_with("abyss"):
			abyss[str(s["id"])] = true
			lava_floor = float(s["floor"])
			assert_true(m.is_void(str(s["id"])), "underworld: abyss piece %s is a void" % s["id"])
			assert_true(float(s["floor"]) <= -3.0, "underworld: abyss piece %s lies below the paths" % s["id"])
	assert_true(abyss.size() >= 3, "underworld: the abyss has pieces (%d)" % abyss.size())
	# round 2: the lava SHORE (behind the tower, at the lava's level, not a void) makes the abyss group's void_top the lava itself, so the depth haze leaves the lake glowing;
	# for the rim count it is part of the lake (its edges onto the abyss are level, not a rim)
	var shore := 0
	for s in doc["sectors"]:
		if str(s.get("room_name", "")) == "lavashore":
			shore += 1
			abyss[str(s["id"])] = true
			assert_false(m.is_void(str(s["id"])), "underworld: the lava shore is not a void")
			assert_eq(float(s["floor"]), lava_floor, "underworld: the lava shore lies at the lava's level")
	assert_eq(shore, 1, "underworld: one lava shore piece")
	for s in doc["sectors"]:
		if str(s.get("room_name", "")).begins_with("abyss"):
			assert_eq(float(m.sector(str(s["id"])).get("void_top", 99.0)), lava_floor, "underworld: abyss piece %s has void_top at the lava (no depth haze on the lake)" % s["id"])
	for w in m.waypoints.values():
		assert_false(abyss.has(str(w["sector"])), "underworld: no waypoint stands in the abyss or on the shore")
	var rim := 0
	var open_rim := 0
	for w in doc["walls"]:
		if not w.get("portal"):
			continue
		if abyss.has(str(w["sector"])) != abyss.has(str(w["portal"])):
			if str(w.get("kind", "")) == "railing":
				rim += 1
				assert_true(bool(w.get("blocked", false)) and str(w["tex"]) == "uw_rail" and float(w["height"]) >= 0.9, "underworld: a rim railing is shut, the chain tile, at least 0.9 m")
			else:
				open_rim += 1
	assert_true(rim >= 10, "underworld: the rim of the abyss carries railings (%d)" % rim)
	assert_true(open_rim <= 1, "underworld: at most one open rim portal (the map's dead end), found %d" % open_rim)
	var textures: Dictionary = doc["textures"]
	var im := Image.load_from_file(ProjectSettings.globalize_path("res://assets/story/doom_underworld/textures/uw_rail.png"))
	assert_true(im != null and im.get_width() == 128 and im.detect_alpha() != Image.ALPHA_NONE, "underworld: uw_rail is a 128 px tile with an alpha channel")
	var decals := 0
	var lit := 0
	for t in doc["things"]:
		if str(t.get("kind", "")) == "decal":
			decals += 1
			if bool(t.get("emissive", false)):
				lit += 1
	assert_true(decals >= 4 and lit >= 3, "underworld: wall decals (%d), the lava falls emissive (%d)" % [decals, lit])
	for g in UW_GUIDES:
		var stem: String = g.trim_prefix("uw_guide_")
		for st in ["idle_0", "available_0", "selected_0", "committed_0"]:
			assert_true(textures.has("guide_%s_%s" % [stem, st]), "underworld: guide sprite %s_%s" % [stem, st])
			assert_true(FileAccess.file_exists("res://assets/story/doom_underworld/textures/guide_%s_%s.png" % [stem, st]), "underworld: the file guide_%s_%s.png exists" % [stem, st])


# --- the Mothership (docs/doom/scenes/mothership.md): a separate block, its own constants -------------------------------------------------------------------------------------------

const MS_MAP := "doom_mothership"
const MS_GUIDES := ["ms_guide_underworld", "ms_guide_booth", "ms_guide_dock"]
const MS_HOLD_PLACES := ["ms_ref", "ms_hub_view", "ms_stair_view", "ms_bridge_view"]
const MS_NODES := ["doom_mothership"]
const MS_EXITS := ["ms_uw_hatch", "ms_booth_hatch", "ms_dock_in"]


func _ms_map() -> StoryMap:
	return StoryMap.load_chapter(MS_MAP, true)


func _ms_pose(m: StoryMap, wp: String) -> Dictionary:
	var p := StoryPlayer.new()
	p.setup(m, 174.0)
	p.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": wp, "bars": 0.01, "cut": true}, "world": MS_MAP})
	return p.pose_at(2.0)


func test_mothership_map_loads_with_routes_holds_and_the_reference_viewpoint() -> void:
	var m := _ms_map()
	assert_true(m != null and m.errors.is_empty(), "the mothership map loads clean: %s" % str(m.errors if m != null else "null"))
	if m == null:
		return
	var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % MS_MAP))
	assert_true(bool((doc["doom"] as Dictionary).get("approximate", false)), "mothership: still flagged approximate")
	var routes: Dictionary = doc["scene"]["routes"]
	for k in ["ahead", "left", "right", "stay", "arrive", "stumble"]:
		assert_true(routes.has(k), "mothership route %s exists" % k)
		for wid in routes[k]:
			assert_true(m.has_waypoint(str(wid)), "mothership route %s: waypoint %s exists" % [k, wid])
	var holds := {}
	for w in doc["waypoints"]:
		holds[str(w["id"])] = float(w.get("hold_bars", 0.0))
	assert_true(float(holds["ms_ref"]) >= CHOICE_REF_HOLD, "the mothership's reference viewpoint holds at least 8 bars")
	for id in MS_HOLD_PLACES:
		assert_true(float(holds[id]) > 0.0, "%s has hold_bars" % id)
	for id in MS_EXITS:
		assert_true(float(holds[id]) > 0.0, "the threshold %s holds" % id)
	assert_true(float((_ms_pose(m, "ms_ref")["pos"] as Vector2).distance_to(m.waypoint("ms_ref")["at"])) < 0.05, "the camera stands at the mothership's reference viewpoint")


func test_mothership_three_guides_are_in_frame_apart_and_off_the_pad_strip_from_the_reference_viewpoint() -> void:
	var m := _ms_map()
	if m == null:
		fail("mothership map did not load")
		return
	var pose := _ms_pose(m, "ms_ref")
	# round 2: the choice hold at ms_ref carries a steady pitch (the run's rail place `pitch`): the guides are checked at the PITCHED pose the window holds
	var good: Array = _doom_run().nodes["doom_mothership"]["rail"]["good"]
	var pitch := float((good[3] as Dictionary).get("pitch", 0.0))
	assert_true(pitch <= -8.0 and pitch >= -35.0, "mothership: ms_ref holds a downward pitch over the pool (%.1f)" % pitch)
	pose["pitch"] = pitch
	for asp in ASPECTS:
		var view: Vector2 = ASPECTS[asp]
		var rects := {}
		for g in MS_GUIDES:
			var r := _rect(m, g, pose, view)
			rects[g] = r
			var inside := r.intersection(Rect2(Vector2.ZERO, view)).get_area()
			assert_true(r.get_area() > 0.0 and inside >= 0.95 * r.get_area(), "mothership %s %s: inside the picture (%s)" % [asp, g, str(r)])
			assert_true(r.end.y <= view.y, "mothership %s %s: its feet are above the pad strip" % [asp, g])
			assert_true(r.size.y >= MIN_GUIDE_PX, "mothership %s %s: at least %d px tall (%.0f)" % [asp, g, int(MIN_GUIDE_PX), r.size.y])
			for b in HUD_BOXES:
				assert_false(r.intersects(b), "mothership %s %s: clear of the HUD's corner" % [asp, g])
			print("  mothership %s %-22s rect %s" % [asp, g, str(r)])
		for i in MS_GUIDES.size():
			for j in range(i + 1, MS_GUIDES.size()):
				assert_false((rects[MS_GUIDES[i]] as Rect2).intersects(rects[MS_GUIDES[j]]), "mothership %s: %s and %s do not overlap" % [asp, MS_GUIDES[i], MS_GUIDES[j]])


func test_mothership_each_guide_is_seen_from_the_reference_viewpoint_no_solid_wall_between() -> void:
	var m := _ms_map()
	if m == null:
		fail("mothership map did not load")
		return
	var cam: Vector2 = m.waypoint("ms_ref")["at"]
	for g in MS_GUIDES:
		var at: Vector2 = _thing(m, g)["at"]
		var hit := ""
		for w in m.resolved_walls():
			if str(w["portal"]) != "":
				continue  # (an opening, a stair step or the railing round the void: the eye passes over or through)
			if Geometry2D.segment_intersects_segment(cam, at, w["a"], w["b"]) != null:
				hit = "%s-%s" % [str(w["a"]), str(w["b"])]
				break
		assert_eq(hit, "", "mothership %s: the sightline from ms_ref stays clear of solid walls" % g)


func test_mothership_guides_keep_their_distance_from_the_camera_places() -> void:
	var m := _ms_map()
	if m == null:
		fail("mothership map did not load")
		return
	for g in MS_GUIDES:
		var at: Vector2 = _thing(m, g)["at"]
		for wid in m.waypoints:
			var d: float = (m.waypoints[wid]["at"] as Vector2).distance_to(at)
			if str(wid) in MS_EXITS:
				assert_true(d >= 1.2, "mothership: %s is not on top of %s (%.1f m)" % [g, wid, d])
			else:
				assert_true(d >= 1.5, "mothership: %s is at least 1.5 m from %s (%.1f m)" % [g, wid, d])


func test_mothership_overlay_world_nodes_hotspots_and_rail_validate() -> void:
	var on := _doom_run()
	assert_true(on.errors.is_empty(), "mothership: the run loads clean with the flag: %s" % str(on.errors))
	for id in MS_NODES:
		assert_true(on.nodes.has(id), "mothership: scene %s" % id)
	assert_true(on.nodes.has("doom_warehouse"), "the warehouse pilot is still there beside the mothership")
	for id in MS_NODES:
		var rail: Dictionary = on.nodes[id]["rail"]
		assert_eq(RunRail.validate(id, rail), [], "%s: RunRail.validate" % id)
		var routes: Dictionary = rail["routes"]
		for k in ["up", "left", "right", "stumble", "arrive"]:
			assert_true(routes.has(k) and routes[k].has("to"), "%s: route %s is a move" % [id, k])
		for k in ["up", "left", "right", "stumble"]:
			assert_false((routes[k].get("via", []) as Array).is_empty(), "%s: route %s has via waypoints" % [id, k])
		for k in ["up", "left", "right"]:
			assert_true(float(routes[k].get("hold_bars", 0.0)) > 0.0, "%s: route %s holds at its threshold" % [id, k])
			assert_eq(str(routes[k]["to"]), str((rail["exits"] as Dictionary)[k]), "%s: route %s ends at rail.exits.%s (the doorway)" % [id, k, k])
	var good: Array = on.nodes["doom_mothership"]["rail"]["good"]
	assert_eq(good.size(), 4, "mothership: the stay loop has four places")
	for i in 3:
		assert_eq(float(good[i]["hold_bars"]), REVEAL_HOLD, "mothership: reveal viewpoint %s holds 2 bars" % good[i]["to"])
		assert_false(bool(good[i].get("choice", false)), "mothership: reveal viewpoint %s is not a choice viewpoint" % good[i]["to"])
	assert_eq(str(good[3]["to"]), "ms_ref", "mothership: the loop ends at the reference viewpoint")
	assert_true(bool(good[3].get("choice", false)) and float(good[3]["hold_bars"]) >= RunRail.CHOICE_HOLD_BARS, "mothership: ms_ref is a choice viewpoint holding the whole window")
	var hs: Array = on.hotspots.get("doom_mothership", [])
	assert_eq(hs.size(), 4, "mothership: three guides and the stay hotspot")
	var dests := []
	for h in hs:
		dests.append(str((h["on_success"] as Dictionary).get("route", "")))
		assert_true(h.has("show"), "mothership: hotspot %s declares show" % h["id"])
		if str(h["id"]) != "doom_mothership.exit_stay":
			assert_eq(str((h["show"] as Dictionary)["archetype"]), "figure", "mothership: %s is a figure (a guide, no ring)" % h["id"])
	dests.sort()
	assert_eq(dests, ["doom_booth", "doom_dock", "doom_mothership", "doom_underworld"], "mothership: ahead the Underworld, left the Booth, right the Dock, and stay")


func test_mothership_every_via_stands_in_a_walkable_piece_and_check_rail_paths_finds_nothing() -> void:
	var on := _doom_run()
	var m := _ms_map()
	if m == null:
		fail("mothership map did not load")
		return
	var reach := m.reachable_from(str(m.start_waypoint()["sector"]))
	for id in MS_NODES:
		var node: Dictionary = on.nodes[id]
		for mv in _moves_of(node["rail"]):
			var ids: Array = (mv.get("via", []) as Array).duplicate()
			ids.append(mv["to"])
			if mv.has("from"):
				ids.append(mv["from"])
			for wid in ids:
				assert_true(m.has_waypoint(str(wid)), "%s: waypoint %s exists" % [id, wid])
				if not m.has_waypoint(str(wid)):
					continue
				var sid := str(m.waypoint(str(wid))["sector"])
				assert_true(m.inside(m.waypoint(str(wid))["at"], sid, StoryMap.WAYPOINT_MARGIN) and reach.has(sid) and not m.is_void(sid), "%s: %s stands in a walkable piece (not in the void)" % [id, wid])
		assert_eq(StoryRailCheck.check_rail(m, id, str(node["waypoint"]), node["rail"]), [], "%s: check_rail_paths finds nothing" % id)


func test_mothership_the_void_is_shut_by_railings_visibility_decals_and_the_art_are_in_the_map() -> void:
	var m := _ms_map()
	if m == null:
		fail("mothership map did not load")
		return
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % MS_MAP))
	assert_eq(float(doc["max_step"]), 0.5, "mothership: max_step 0.5")
	assert_eq(str(doc["visibility"]["mode"]), "clip", "mothership: visibility mode clip")
	var textures: Dictionary = doc["textures"]
	assert_true(textures.has("ms_rail"), "mothership: ms_rail is one of the map's textures")
	var im := Image.load_from_file(ProjectSettings.globalize_path("res://assets/story/doom_mothership/textures/ms_rail.png"))
	assert_true(im != null and im.get_width() == 128 and im.detect_alpha() != Image.ALPHA_NONE, "mothership: ms_rail is a 128 px tile with an alpha channel")
	var rails := 0
	for w in doc["walls"]:
		if str(w.get("kind", "")) != "railing":
			continue
		rails += 1
		assert_true(bool(w.get("blocked", false)), "mothership: a railing is shut to walkers")
		assert_eq(str(w["tex"]), "ms_rail", "mothership: the railing is the balustrade tile")
	assert_true(rails >= 24, "mothership: the void's rim, the platform's edge and the bridge's sides are railings (%d)" % rails)
	# the void: sectors the player cannot enter; every portal into one is a railing, bar the one the loader's reachability rule keeps open
	var voids := 0
	var open_to_void := 0
	for s in m.sectors:
		if not m.is_void(str(s["id"])):
			continue
		voids += 1
		assert_true(float(s["floor"]) <= -3.0, "mothership: the void %s lies far below the walk" % s["id"])
		for p in m.portals():
			if (str(p["a"]) == str(s["id"]) or str(p["b"]) == str(s["id"])) and not bool(p["blocked"]):
				var other := str(p["b"]) if str(p["a"]) == str(s["id"]) else str(p["a"])
				if not m.is_void(other) and absf(float(m.sector(other)["floor"]) - float(s["floor"])) > 0.01:  # (round 2: the pool shore, at the pool's own level, is part of the pool)
					open_to_void += 1
					assert_eq(str(m.floor_change(other, str(s["id"]))["kind"]), "void", "mothership: the open edge to the void %s is a void crossing (the rail never takes it)" % s["id"])
		assert_eq(float(s.get("void_top", 99.0)), float(s["floor"]), "mothership: void %s has void_top at the pool (the pool shore: no depth haze darkens the pool)" % s["id"])
	# round 2: the POOL SHORE: one wedge of the pool at the pool's level that is not a void (StoryMap's split-void void_top is then the pool, the engine haze leaves it glowing);
	# its one edge onto the walk is the drop the loader needs, and the rail never takes a drop
	var shore := 0
	for s in m.sectors:
		if not m.is_void(str(s["id"])) and float(s["floor"]) <= -3.0:
			shore += 1
			for p in m.portals():
				if (str(p["a"]) == str(s["id"]) or str(p["b"]) == str(s["id"])) and not bool(p["blocked"]):
					var other := str(p["b"]) if str(p["a"]) == str(s["id"]) else str(p["a"])
					if not m.is_void(other):
						open_to_void += 1
						assert_eq(str(m.floor_change(other, str(s["id"]))["kind"]), "drop", "mothership: the open edge onto the pool shore is a drop (the rail never takes it)")
	assert_eq(shore, 1, "mothership: one pool shore piece")
	assert_true(voids >= 10, "mothership: the void is made of marked sectors (%d)" % voids)
	assert_true(open_to_void <= 1, "mothership: at most one unrailed edge into the void (%d)" % open_to_void)
	for wid in m.waypoints:
		assert_false(m.is_void(str(m.waypoints[wid]["sector"])), "mothership: waypoint %s is not in the void" % wid)
	var decals := 0
	var lit := 0
	for t in doc["things"]:
		if str(t.get("kind", "")) == "decal":
			decals += 1
			if bool(t.get("emissive", false)):
				lit += 1
	assert_true(decals >= 8 and lit >= 5, "mothership: wall decals (%d), the windows and lamps emissive (%d)" % [decals, lit])
	for g in MS_GUIDES:
		var stem: String = g.trim_prefix("ms_guide_")
		for st in ["idle_0", "available_0", "selected_0", "committed_0"]:
			assert_true(textures.has("guide_%s_%s" % [stem, st]), "mothership: guide sprite %s_%s" % [stem, st])


# --- THE BALCONY (docs/doom/scenes/balcony.md): its own block, its own map (doom_balcony) and world (doom_balcony) -----------------------------------------------------------

const BC_MAP := "doom_balcony"
const BC_GUIDES := ["bc_guide_mothership", "bc_guide_floor", "bc_guide_booth"]
const BC_HOLD_PLACES := ["bc_ref", "bc_bridge_view", "bc_stair_view", "bc_cabin_view"]
const BC_NODES := ["doom_balcony"]
const BC_EXITS := ["bc_bridge_end", "bc_stair_foot", "bc_cabin_in"]


func _bc_map() -> StoryMap:
	return StoryMap.load_chapter(BC_MAP, true)


func _bc_pose(m: StoryMap, wp: String) -> Dictionary:
	var p := StoryPlayer.new()
	p.setup(m, 174.0)
	p.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": wp, "bars": 0.01, "cut": true}, "world": BC_MAP})
	return p.pose_at(2.0)


func test_balcony_map_loads_clean_with_routes_holds_and_the_reference_viewpoint() -> void:
	var m := _bc_map()
	assert_true(m != null and m.errors.is_empty(), "the balcony map loads clean: %s" % str(m.errors if m != null else "null"))
	if m == null:
		return
	var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % BC_MAP))
	assert_true(bool((doc["doom"] as Dictionary).get("approximate", false)), "balcony: still flagged approximate")
	var routes: Dictionary = doc["scene"]["routes"]
	for k in ["ahead", "left", "right", "stay", "arrive", "stumble"]:
		assert_true(routes.has(k), "balcony route %s exists" % k)
		for wid in routes[k]:
			assert_true(m.has_waypoint(str(wid)), "balcony route %s: waypoint %s exists" % [k, wid])
	var holds := {}
	for w in doc["waypoints"]:
		holds[str(w["id"])] = float(w.get("hold_bars", 0.0))
	assert_true(float(holds["bc_ref"]) >= CHOICE_REF_HOLD, "the balcony's reference viewpoint holds at least 8 bars")
	for id in BC_HOLD_PLACES:
		assert_true(float(holds[id]) > 0.0, "%s has hold_bars" % id)
	for id in BC_EXITS:
		assert_true(float(holds[id]) > 0.0, "the threshold %s holds" % id)
	assert_true(float((_bc_pose(m, "bc_ref")["pos"] as Vector2).distance_to(m.waypoint("bc_ref")["at"])) < 0.05, "the camera stands at the balcony's reference viewpoint")
	var voids := 0
	for s in m.sectors:
		if bool(s.get("void", false)):
			voids += 1
	assert_eq(voids, 4, "the four pits round the roof are voids")


func test_balcony_three_guides_are_in_frame_apart_and_off_the_pad_strip_from_the_reference_viewpoint() -> void:
	var m := _bc_map()
	if m == null:
		fail("balcony map did not load")
		return
	var pose := _bc_pose(m, "bc_ref")
	for asp in ASPECTS:
		var view: Vector2 = ASPECTS[asp]
		var rects := {}
		for g in BC_GUIDES:
			var r := _rect(m, g, pose, view)
			rects[g] = r
			var inside := r.intersection(Rect2(Vector2.ZERO, view)).get_area()
			assert_true(r.get_area() > 0.0 and inside >= 0.95 * r.get_area(), "balcony %s %s: inside the picture (%s)" % [asp, g, str(r)])
			assert_true(r.end.y <= view.y, "balcony %s %s: its feet are above the pad strip" % [asp, g])
			assert_true(r.size.y >= MIN_GUIDE_PX, "balcony %s %s: at least %d px tall (%.0f)" % [asp, g, int(MIN_GUIDE_PX), r.size.y])
			for b in HUD_BOXES:
				assert_false(r.intersects(b), "balcony %s %s: clear of the HUD's corner" % [asp, g])
			print("  balcony %s %-22s rect %s" % [asp, g, str(r)])
		for i in BC_GUIDES.size():
			for j in range(i + 1, BC_GUIDES.size()):
				assert_false((rects[BC_GUIDES[i]] as Rect2).intersects(rects[BC_GUIDES[j]]), "balcony %s: %s and %s do not overlap" % [asp, BC_GUIDES[i], BC_GUIDES[j]])


func test_balcony_each_guide_is_seen_from_the_reference_viewpoint_no_solid_wall_between() -> void:
	var m := _bc_map()
	if m == null:
		fail("balcony map did not load")
		return
	var cam: Vector2 = m.waypoint("bc_ref")["at"]
	for g in BC_GUIDES:
		var at: Vector2 = _thing(m, g)["at"]
		var hit := ""
		for w in m.resolved_walls():
			if str(w["portal"]) != "":
				continue  # (an opening, a step, a railing or a drop: the eye passes over or through)
			if Geometry2D.segment_intersects_segment(cam, at, w["a"], w["b"]) != null:
				hit = "%s-%s" % [str(w["a"]), str(w["b"])]
				break
		assert_eq(hit, "", "%s: the sightline from bc_ref stays clear of solid walls" % g)


func test_balcony_guides_keep_their_distance_from_the_camera_places() -> void:
	var m := _bc_map()
	if m == null:
		fail("balcony map did not load")
		return
	for g in BC_GUIDES:
		var at: Vector2 = _thing(m, g)["at"]
		for wid in m.waypoints:
			var d: float = (m.waypoints[wid]["at"] as Vector2).distance_to(at)
			if str(wid) in BC_EXITS:
				assert_true(d >= 1.2, "balcony: %s is not on top of %s (%.1f m)" % [g, wid, d])
			else:
				assert_true(d >= 1.5, "balcony: %s is at least 1.5 m from %s (%.1f m)" % [g, wid, d])


func test_balcony_overlay_world_nodes_hotspots_and_rail_validate() -> void:
	var on := _doom_run()
	assert_true(on.errors.is_empty(), "balcony: the run loads clean with the flag: %s" % str(on.errors))
	for id in BC_NODES:
		assert_true(on.nodes.has(id), "balcony: scene %s" % id)
	assert_false(on.nodes.has("doom_warehouse.balcony"), "the Warehouse's balcony stand-in is gone: its guide leads to the world doom_balcony")
	assert_true(str(on.nodes["doom_balcony"]["world"]) == "doom_balcony" and bool(on.nodes["doom_balcony"]["entry"]), "balcony: doom_balcony is the entry of the world doom_balcony")
	for id in BC_NODES:
		var rail: Dictionary = on.nodes[id]["rail"]
		assert_eq(RunRail.validate(id, rail), [], "%s: RunRail.validate" % id)
		var routes: Dictionary = rail["routes"]
		for k in ["up", "left", "right", "stumble", "arrive"]:
			assert_true(routes.has(k) and routes[k].has("to"), "%s: route %s is a move" % [id, k])
		for k in ["up", "left", "right", "stumble"]:
			assert_false((routes[k].get("via", []) as Array).is_empty(), "%s: route %s has via waypoints" % [id, k])
		for k in ["up", "left", "right"]:
			assert_true(float(routes[k].get("hold_bars", 0.0)) > 0.0, "%s: route %s holds at its threshold" % [id, k])
		assert_eq([str(routes["up"]["to"]), str(routes["left"]["to"]), str(routes["right"]["to"])], BC_EXITS, "%s: the route moves end at the thresholds" % id)
		assert_eq([str(rail["exits"]["up"]), str(rail["exits"]["left"]), str(rail["exits"]["right"])], BC_EXITS, "%s: rail.exits are the doorways" % id)
	var good: Array = on.nodes["doom_balcony"]["rail"]["good"]
	assert_eq(good.size(), 4, "balcony: the stay loop has four places")
	for i in 3:
		assert_eq(float(good[i]["hold_bars"]), REVEAL_HOLD, "balcony: reveal viewpoint %s holds 2 bars" % good[i]["to"])
		assert_false(bool(good[i].get("choice", false)), "balcony: reveal viewpoint %s is not a choice viewpoint" % good[i]["to"])
	assert_eq(str(good[3]["to"]), "bc_ref", "balcony: the loop ends at the reference viewpoint")
	assert_true(bool(good[3].get("choice", false)) and float(good[3]["hold_bars"]) >= RunRail.CHOICE_HOLD_BARS, "balcony: bc_ref is a choice viewpoint holding the whole window")
	var hs: Array = on.hotspots.get("doom_balcony", [])
	assert_eq(hs.size(), 4, "balcony: three guides and the stay hotspot")
	var dests := []
	for h in hs:
		dests.append(str((h["on_success"] as Dictionary).get("route", "")))
		assert_true(h.has("show"), "balcony: hotspot %s declares show" % h["id"])
		if str(h["id"]) != "doom_balcony.exit_stay":
			assert_eq(str((h["show"] as Dictionary)["archetype"]), "figure", "balcony: %s is a figure (a guide, no ring)" % h["id"])
	dests.sort()
	assert_eq(dests, ["doom_balcony", "doom_booth", "doom_mothership", "doom_warehouse"], "balcony: ahead the Mothership, left the Floor, right the Booth, and stay")
	var labels := []
	for n in on.nodes["doom_balcony"]["next"]:
		labels.append(str(n["label"]))
	var all_labels := " ".join(labels)
	assert_true(all_labels.contains("mothership") and all_labels.contains("floor") and all_labels.contains("booth"), "balcony: the route labels name the destinations")


func test_balcony_every_via_stands_in_a_walkable_piece_and_check_rail_paths_finds_nothing() -> void:
	var on := _doom_run()
	var m := _bc_map()
	if m == null:
		fail("balcony map did not load")
		return
	var reach := m.reachable_from(str(m.start_waypoint()["sector"]))
	for id in BC_NODES:
		var node: Dictionary = on.nodes[id]
		for mv in _moves_of(node["rail"]):
			var ids: Array = (mv.get("via", []) as Array).duplicate()
			ids.append(mv["to"])
			if mv.has("from"):
				ids.append(mv["from"])
			for wid in ids:
				assert_true(m.has_waypoint(str(wid)), "%s: waypoint %s exists" % [id, wid])
				if not m.has_waypoint(str(wid)):
					continue
				var sid := str(m.waypoint(str(wid))["sector"])
				assert_true(m.inside(m.waypoint(str(wid))["at"], sid, StoryMap.WAYPOINT_MARGIN) and reach.has(sid) and not m.is_void(sid), "%s: %s stands in a walkable piece" % [id, wid])
		assert_eq(StoryRailCheck.check_rail(m, id, str(node["waypoint"]), node["rail"]), [], "%s: check_rail_paths finds nothing" % id)


func test_balcony_railing_voids_decals_and_the_art_are_in_the_map() -> void:
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/%s.json" % BC_MAP))
	assert_eq(float(doc["max_step"]), 0.5, "balcony: max_step 0.5")
	assert_eq(str(doc["visibility"]["mode"]), "clip", "balcony: visibility mode clip")
	var textures: Dictionary = doc["textures"]
	assert_true(textures.has("bc_rail"), "balcony: bc_rail is one of the map's textures")
	var im := Image.load_from_file(ProjectSettings.globalize_path("res://assets/story/doom_balcony/textures/bc_rail.png"))
	assert_true(im != null and im.get_width() == 128 and im.detect_alpha() != Image.ALPHA_NONE, "balcony: bc_rail is a 128 px tile with an alpha channel")
	var rails := 0
	for w in doc["walls"]:
		if str(w.get("kind", "")) != "railing":
			continue
		assert_true(bool(w.get("blocked", false)), "balcony: a railing is shut to walkers")
		rails += 1
	assert_true(rails >= 12, "balcony: the deck, stair, bridge and platform edges carry the railing (%d)" % rails)
	var decals := 0
	var lit := 0
	for t in doc["things"]:
		if str(t.get("kind", "")) == "decal":
			decals += 1
			if bool(t.get("emissive", false)):
				lit += 1
	assert_true(decals >= 8 and lit >= 5, "balcony: wall decals (%d), the glow and graffiti emissive (%d)" % [decals, lit])
	for g in BC_GUIDES:
		var stem: String = g.trim_prefix("bc_guide_")
		for st in ["idle_0", "available_0", "selected_0", "committed_0"]:
			assert_true(textures.has("guide_%s_%s" % [stem, st]), "balcony: guide sprite %s_%s" % [stem, st])
			assert_true(FileAccess.file_exists("res://assets/story/doom_balcony/textures/guide_%s_%s.png" % [stem, st]), "balcony: guide file %s_%s exists" % [stem, st])
