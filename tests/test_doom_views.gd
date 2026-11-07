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


func _pose_at(m: StoryMap, wp: String) -> Dictionary:
	var p := StoryPlayer.new()
	p.setup(m, 174.0)
	p.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": wp, "bars": 0.01, "cut": true}, "world": MAP_ID})
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
	assert_eq(routes, ["doom_balcony", "doom_bar", "doom_lounge", "doom_warehouse"], "ahead, left, right, and stay on the floor")
