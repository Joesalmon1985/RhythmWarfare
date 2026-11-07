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
	for id in ["doom_warehouse", "doom_balcony", "doom_warehouse.bar", "doom_warehouse.chill", "doom_warehouse.return", "warehouse"]:
		assert_true(on.nodes.has(id), "flag on: scene %s" % id)
	var hs: Array = on.hotspots.get("doom_warehouse", [])
	assert_eq(hs.size(), 4, "the three guides and the stay hotspot")
	var routes := []
	for h in hs:
		routes.append(str((h["on_success"] as Dictionary).get("route", "")))
	routes.sort()
	assert_eq(routes, ["doom_balcony", "doom_warehouse", "doom_warehouse.bar", "doom_warehouse.chill"], "ahead, left (the bar stand-in: the real Bar is the world doom_bar), right (the chill-out stand-in: the real lounge is the world doom_lounge), and stay on the floor")


# --- the rail as polyline moves with holds, and the railing (docs/story/HEIGHTS_AND_PATHS.md) ---------------------------------------------------------------------------------

const DOOM_NODES := ["doom_warehouse", "doom_balcony", "doom_warehouse.bar", "doom_warehouse.chill", "doom_warehouse.return"]  # the Warehouse world scenes (its map); the Booth, Bar and Lounge worlds are tested below
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
	assert_true(seen > 40, "the loop looked at %d waypoint uses" % seen)


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
const BOOTH_NODES := ["doom_booth", "doom_booth.mothership", "doom_booth.balcony", "doom_booth.dock", "doom_booth.return"]
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
	assert_eq(dests, ["doom_booth", "doom_booth.balcony", "doom_booth.dock", "doom_booth.mothership"], "booth: ahead, left, right and stay")


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
	assert_true(desk >= 1, "booth: the desk's edge carries the railing (%d)" % desk)
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
const BAR_NODES := ["doom_bar", "doom_bar.booth", "doom_bar.floor", "doom_bar.chill", "doom_bar.return"]
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
	for e in on.nodes["doom_warehouse.return"]["next"]:
		back.append(str(e["to"]))
	assert_true(back.has("doom_bar"), "the Warehouse's exit scene leads on to the Copper Bar")
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
	assert_eq(routes, ["doom_bar", "doom_bar.booth", "doom_bar.chill", "doom_bar.floor"], "ahead, left, right and stay")


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
const LOUNGE_NODES := ["doom_lounge", "doom_lounge.dock", "doom_lounge.bar", "doom_lounge.floor", "doom_lounge.return"]


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
	assert_eq(routes["doom_lounge.exit_dock"], "doom_lounge.dock", "ahead: the Dock")
	assert_eq(routes["doom_lounge.exit_bar"], "doom_lounge.bar", "left: the Bar")
	assert_eq(routes["doom_lounge.exit_floor"], "doom_lounge.floor", "right: the Floor")
	assert_eq(routes["doom_lounge.exit_stay"], "doom_lounge", "bottom: stay")
	var back := []
	for e in on.nodes["doom_warehouse.return"]["next"]:
		back.append(str(e["to"]))
	assert_true(back.has("doom_lounge"), "the Warehouse's exit scene leads on to the lounge world")


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
	assert_true(seen > 40, "the loop looked at %d waypoint uses" % seen)


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


# --- the Mothership (docs/doom/scenes/mothership.md): a separate block, its own constants -------------------------------------------------------------------------------------------

const MS_MAP := "doom_mothership"
const MS_GUIDES := ["ms_guide_underworld", "ms_guide_booth", "ms_guide_dock"]
const MS_HOLD_PLACES := ["ms_ref", "ms_hub_view", "ms_stair_view", "ms_bridge_view"]
const MS_NODES := ["doom_mothership", "doom_mothership.underworld", "doom_mothership.booth", "doom_mothership.dock", "doom_mothership.return"]
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
	assert_eq(dests, ["doom_mothership", "doom_mothership.booth", "doom_mothership.dock", "doom_mothership.underworld"], "mothership: ahead, left, right and stay")


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
				if not m.is_void(other):
					open_to_void += 1
					assert_eq(str(m.floor_change(other, str(s["id"]))["kind"]), "void", "mothership: the open edge to the void %s is a void crossing (the rail never takes it)" % s["id"])
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
