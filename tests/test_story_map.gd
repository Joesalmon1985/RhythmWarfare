extends TestCase
## StoryMap: the Night One map loads clean, the rules reject broken maps (one test per rule), portal routing, and the chapter cross-checks.


func _sq(x0: float, z0: float, x1: float, z1: float) -> Array:
	return [[x0, z0], [x1, z0], [x1, z1], [x0, z1]]


func _two_rooms() -> Dictionary:
	return {"textures": {"w": "textures/w.png"}, "start": "a",
		"sectors": [{"id": "a", "polygon": _sq(0, 0, 4, 4), "floor": 0, "ceiling": 3, "wall_tex": "w"},
			{"id": "b", "polygon": _sq(4, 0, 8, 4), "floor": 0.5, "ceiling": 3, "wall_tex": "w"}],
		"walls": [{"from": [4, 1], "to": [4, 3], "sector": "a", "portal": "b"}],
		"waypoints": [{"id": "a", "at": [2, 2], "yaw": 0, "sector": "a"}, {"id": "b", "at": [6, 2], "yaw": 90, "sector": "b"}],
		"homes": [], "things": []}


func _errs(d: Dictionary) -> String:
	return " | ".join(PackedStringArray(StoryMap.from_dict(d).errors))


func test_night_one_map_is_clean() -> void:
	var m := StoryMap.load_chapter("night_one")
	assert_true(m.errors.is_empty(), str(m.errors))
	var data := StoryData.load_file()
	m.validate_chapter(data["data"].raw)
	assert_true(m.errors.is_empty(), str(m.errors))
	for w in ["floor_centre", "floor_edge", "steps", "stage", "booth", "corridor", "cubicle", "door"]:
		assert_true(m.has_waypoint(w), "waypoint " + w)
	assert_eq(m.homes.size(), 30, "a home for every actor")
	for room in ["entrance", "floor", "steps", "riser", "booth", "bar", "corridor", "toilets", "cubicle_a", "cubicle_b"]:
		assert_false(m.sector(room).is_empty(), "sector " + room)
	assert_true(m.sector("riser")["floor"] > m.sector("steps")["floor"] and m.sector("steps")["floor"] > m.sector("floor")["floor"], "stage steps climb")


func test_resolved_walls_close_every_room() -> void:
	var m := StoryMap.load_chapter("night_one")
	var by_sector := {}
	for w in m.resolved_walls():
		by_sector[w["sector"]] = float(by_sector.get(w["sector"], 0.0)) + (w["a"] as Vector2).distance_to(w["b"])
		assert_true(str(w["tex"]) != "" and m.textures.has(str(w["tex"])), "wall has a known texture")
	for s in m.sectors:  # explicit, mirrored and filled walls together cover the whole perimeter
		var per := 0.0
		var poly: PackedVector2Array = s["poly"]
		for i in poly.size():
			per += poly[i].distance_to(poly[(i + 1) % poly.size()])
		assert_near(float(by_sector[s["id"]]), per, 0.01, "sector %s is walled all round" % s["id"])
	var mirror := false
	for w in m.resolved_walls():
		if w["sector"] == "riser" and w["portal"] == "steps" and w.get("implicit", false):
			mirror = true
	assert_true(mirror, "a portal is seen from the other side too")


func test_two_room_map_is_valid() -> void:
	assert_eq(_errs(_two_rooms()), "")


func test_rejects_bad_polygon() -> void:
	var d := _two_rooms()
	d["sectors"][0]["polygon"] = [[0, 0], [4, 4], [4, 0], [0, 4]]  # a bow tie
	assert_true(_errs(d).contains("not simple"), _errs(d))
	d = _two_rooms()
	d["sectors"][0]["polygon"] = [[0, 0], [4, 0], [4, 4], [2, 1], [0, 4]]  # concave, simple
	assert_true(_errs(d).contains("not convex"), _errs(d))
	d = _two_rooms()
	d["sectors"][0]["polygon"] = [[0, 0], [4, 0]]
	assert_true(_errs(d).contains("3 points"), _errs(d))
	d = _two_rooms()
	d["sectors"][0]["polygon"] = [[0, 0], [4, 0], [8, 0]]
	assert_true(_errs(d).contains("no area"), _errs(d))
	d = _two_rooms()
	d["sectors"][0]["ceiling"] = -1
	assert_true(_errs(d).contains("ceiling"), _errs(d))


func test_clockwise_polygons_are_normalised() -> void:
	var d := _two_rooms()
	d["sectors"][0]["polygon"] = [[0, 0], [0, 4], [4, 4], [4, 0]]
	var m := StoryMap.from_dict(d)
	assert_eq(m.errors.size(), 0, str(m.errors))
	var poly: PackedVector2Array = m.sector("a")["poly"]
	assert_true(StoryMap._signed_area(poly) > 0.0, "stored counter-clockwise")


func test_rejects_overlapping_sectors() -> void:
	var d := _two_rooms()
	d["sectors"][1]["polygon"] = _sq(3, 0, 7, 4)
	d["walls"] = []
	assert_true(_errs(d).contains("overlap"), _errs(d))
	d = _two_rooms()
	d["sectors"][1]["polygon"] = _sq(0, 0, 4, 4)
	d["walls"] = []
	assert_true(_errs(d).contains("overlap"), "identical rooms: " + _errs(d))


func test_rejects_bad_walls_and_portals() -> void:
	var d := _two_rooms()
	d["walls"][0]["to"] = [4, 5]  # runs past the room's edge
	assert_true(_errs(d).contains("not on one edge"), _errs(d))
	d = _two_rooms()
	d["walls"][0]["portal"] = "nowhere"
	assert_true(_errs(d).contains("no sector on the other side"), _errs(d))
	d = _two_rooms()
	d["sectors"][1]["polygon"] = _sq(4, 1, 8, 3)  # b no longer holds the portal's whole span? it does (4,1)-(4,3)
	assert_eq(_errs(d), "")
	d["sectors"][1]["polygon"] = _sq(4, 1.5, 8, 3)
	assert_true(_errs(d).contains("does not lie on one of its edges"), _errs(d))
	d = _two_rooms()
	d["walls"].append({"from": [4, 2], "to": [4, 3.5], "sector": "b", "portal": "a"})
	assert_true(_errs(d).contains("declared twice") or _errs(d).contains("overlap"), _errs(d))
	d = _two_rooms()
	d["walls"][0]["tex"] = "missing"
	assert_true(_errs(d).contains("unknown texture"), _errs(d))
	d = _two_rooms()
	d["walls"].append({"from": [0, 0], "to": [3, 0], "sector": "a"})
	d["walls"].append({"from": [2, 0], "to": [4, 0], "sector": "a"})
	assert_true(_errs(d).contains("overlap"), _errs(d))


func test_rejects_points_outside_their_sector() -> void:
	var d := _two_rooms()
	d["waypoints"][0]["at"] = [6, 2]
	assert_true(_errs(d).contains("waypoint a"), _errs(d))
	d = _two_rooms()
	d["waypoints"][0]["at"] = [0.1, 2]  # inside, but hugging the wall
	assert_true(_errs(d).contains("margin"), _errs(d))
	d = _two_rooms()
	d["homes"] = [{"actor": "x", "sector": "a", "at": [9, 9]}]
	assert_true(_errs(d).contains("home x"), _errs(d))
	d = _two_rooms()
	d["homes"] = [{"actor": "x", "sector": "a", "at": [0.1, 2]}]
	assert_true(_errs(d).contains("margin"), _errs(d))
	d = _two_rooms()
	d["things"] = [{"id": "t", "kind": "billboard", "sprite": "s", "at": [9, 9], "sector": "a", "y": 1, "size": 1, "anim": "none"}]
	assert_true(_errs(d).contains("thing t"), _errs(d))
	d = _two_rooms()
	d["things"] = [{"id": "t", "kind": "billboard", "sprite": "s", "at": [1, 1], "y": 1, "size": 1, "anim": "wobble"}]
	assert_true(_errs(d).contains("unknown anim"), _errs(d))
	d = _two_rooms()
	d["waypoints"].append({"id": "a", "at": [1, 1], "yaw": 0, "sector": "a"})
	assert_true(_errs(d).contains("duplicated"), _errs(d))


func test_rejects_unreachable_sector() -> void:
	var d := _two_rooms()
	d["walls"] = []
	assert_true(_errs(d).contains("cannot be reached"), _errs(d))


func test_chapter_cross_checks() -> void:
	var d := _two_rooms()
	d["homes"] = [{"actor": "p1", "sector": "a", "at": [1, 1]}, {"actor": "ghost", "sector": "b", "at": [6, 2]}]
	var m := StoryMap.from_dict(d)
	assert_eq(m.errors.size(), 0, str(m.errors))
	var chapter := {"actors": [{"id": "p1"}, {"id": "p2"}], "blocks": [{"id": "blk", "events": [
		{"at_bar": 3, "action": "player_move", "to": "b", "style": "walk", "bars": 2},
		{"at_bar": 5, "action": "x", "else": "player_move", "to": "nowhere"},
		{"at_bar": 7, "action": "player_look", "at": "p1"}, {"at_bar": 8, "action": "player_look", "at": "who"},
		{"at_bar": 9, "action": "player_role", "role": "dj"}, {"at_bar": 10, "action": "player_role", "role": "pilot"},
		{"at_bar": 11, "action": "player_move", "to": "a", "style": "teleport"}]}],
		"decisions": [{"id": "d", "good": [{"action": "player_move", "to": "ghostroom"}], "bad": []}]}
	m.validate_chapter(chapter)
	var all := " | ".join(PackedStringArray(m.errors))
	assert_true(all.contains("actor p2 has no home"), all)
	assert_true(all.contains("home ghost is not an actor"), all)
	assert_true(all.contains("to nowhere is not a waypoint"), all)
	assert_true(all.contains("player_look at who"), all)
	assert_true(all.contains("unknown role pilot"), all)
	assert_true(all.contains("unknown move style teleport"), all)
	assert_true(all.contains("to ghostroom is not a waypoint"), all)
	assert_false(all.contains("to b is not"), "valid moves pass")
	assert_eq(StoryMap.journey_actions(chapter).size(), 8)


func test_routes_through_portals_and_is_deterministic() -> void:
	var m := StoryMap.load_chapter("night_one")
	var from: Vector2 = m.waypoint("floor_centre")["at"]
	var to: Vector2 = m.waypoint("booth")["at"]
	var r := m.route(from, "floor", to, "booth")
	assert_true(r["points"].size() >= 4, "floor, steps, riser, booth: %s" % str(r["points"]))
	assert_eq(r["sectors"], ["floor", "steps", "riser", "booth"])
	assert_eq(r["points"][0], from)
	assert_eq(r["points"][r["points"].size() - 1], to)
	assert_true(float(r["length"]) >= from.distance_to(to) - 0.01)
	assert_eq(m.route(from, "floor", to, "booth")["points"], r["points"], "same route every time")
	# to the cubicle: floor > corridor > toilets > cubicle_b
	var c := m.route(from, "floor", m.waypoint("cubicle")["at"], "cubicle_b")
	assert_eq(c["sectors"], ["floor", "corridor", "toilets", "cubicle_b"])
	# the same sector is a straight line; an unknown one has no route
	assert_eq(m.route(from, "floor", Vector2(0, 0), "floor")["points"].size(), 2)
	assert_eq(m.route(from, "floor", Vector2(0, 0), "mars")["points"].size(), 0)
	# every leg stays inside its sector (the sectors are convex)
	for k in r["sectors"].size():
		var a: Vector2 = r["points"][k]
		var b: Vector2 = r["points"][k + 1]
		assert_eq(m.sector_at((a + b) * 0.5), r["sectors"][k], "leg %d lies in %s" % [k, r["sectors"][k]])


func test_every_waypoint_is_routable_from_the_start() -> void:
	var m := StoryMap.load_chapter("night_one")
	var s := m.start_waypoint()
	for w in m.waypoints:
		var t: Dictionary = m.waypoints[w]
		var r := m.route(s["at"], s["sector"], t["at"], t["sector"])
		assert_true(r["points"].size() >= 2, "route to " + str(w))
	assert_eq(m.sector_at(Vector2(-100, 100)), "")
	assert_eq(m.sector_at(Vector2(0, 6)), "floor")


func test_forward_of_yaw() -> void:
	var m := StoryMap.from_dict(_two_rooms())
	assert_near(m.forward_of_yaw(0).y, -1.0, 1e-6)
	assert_near(m.forward_of_yaw(180).y, 1.0, 1e-6)
	assert_near(m.forward_of_yaw(90).x, -1.0, 1e-6)
