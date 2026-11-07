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
	for id in ["doom_warehouse", "doom_balcony", "doom_bar", "doom_lounge", "doom_warehouse.return", "warehouse"]:
		assert_true(on.nodes.has(id), "flag on: scene %s" % id)
	var hs: Array = on.hotspots.get("doom_warehouse", [])
	assert_eq(hs.size(), 4, "the three guides and the stay hotspot")
	var routes := []
	for h in hs:
		routes.append(str((h["on_success"] as Dictionary).get("route", "")))
	routes.sort()
	assert_eq(routes, ["doom_balcony", "doom_lounge", "doom_warehouse", "doom_warehouse.bar"], "ahead, left (the bar stand-in: the real Bar is its own world, reached from the return scene), right, and stay on the floor")


# --- the rail as polyline moves with holds, and the railing (docs/story/HEIGHTS_AND_PATHS.md) ---------------------------------------------------------------------------------

const DOOM_NODES := ["doom_warehouse", "doom_balcony", "doom_warehouse.bar", "doom_lounge", "doom_warehouse.return"]  # the Warehouse world scenes (its map)
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
