extends TestCase
## The crowd bridge (WP4): the 2D crowd standing in the 2.5D world. Homes project onto the screen from the waypoints, dancers sort by distance, sectors out of
## sight are culled, the crowd directives resolve to map positions inside the rooms, walks follow the doors, occluders draw over dancers behind them, all without a renderer.

const VIEW := Vector2(480, 170)


func _stage() -> StoryStage:
	var run := StoryRun.create({})
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_default(), run.data, run)
	return stage


func _pose_of(map: StoryMap, wid: String) -> Dictionary:
	var w: Dictionary = map.waypoint(wid)
	return {"cam": Vector3(w["at"].x, map.eye_y(str(w["sector"])), w["at"].y), "yaw": float(w["yaw"])}


func _look_from(stage: StoryStage, wid: String, t: float) -> void:
	var map := stage.map
	var pose := _pose_of(map, wid)
	var w: Dictionary = map.waypoint(wid)
	stage.crowd.set_camera(pose, VIEW, map.visible_sectors(w["at"], float(w["yaw"]), str(w["sector"]), VIEW.x / VIEW.y))
	stage.crowd.set_time(t)
	stage.crowd.update(t, 60.0)


func test_the_night_one_stage_gets_its_map_and_the_crowd_stands_in_it() -> void:
	var stage := _stage()
	assert_true(stage.map != null and stage.player != null and stage.crowd.world_mode, "a chapter with a map is a world chapter even headless")
	var c: StoryCrowd = stage.crowd
	for id in c.actors:
		var h: Dictionary = stage.map.home(str(id))
		assert_eq(c.actors[id]["home"], h["at"], "%s stands at its map home" % id)
		assert_eq(stage.map.sector_at(c.actors[id]["pos"]), h["sector"], "%s is inside its sector" % id)
	assert_eq(c.door_pos, stage.map.spot("door")["at"])
	assert_eq(c.circle_c, stage.map.spot("circle")["at"])
	stage.free()


func test_homes_project_onto_the_screen_from_the_waypoints_that_face_the_floor() -> void:
	var map := StoryMap.load_chapter("night_one")
	var seen := {}
	for wid in map.waypoints:
		var pose := _pose_of(map, str(wid))
		for aid in map.homes:
			var h: Dictionary = map.homes[aid]
			var pr := StoryProjector.project_ground(h["at"].x, h["at"].y, float(map.sector(str(h["sector"]))["floor"]), pose, VIEW)
			if pr["visible"]:
				seen[aid] = true
				assert_true(float(pr["scale"]) > 0.0 and (pr["screen"] as Vector2).y > VIEW.y * 0.5 - 1.0 or float(pr["depth"]) > 30.0,
					"%s from %s: feet below the horizon (the ground is below the eye)" % [aid, wid])
				assert_true((pr["screen"] as Vector2).y < VIEW.y * 1.5, "%s from %s is not absurdly low" % [aid, wid])
	for aid in map.homes:
		assert_true(seen.has(aid), "%s is on screen from at least one waypoint" % aid)
	var from_start := 0
	for aid in map.homes:
		var h2: Dictionary = map.homes[aid]
		if str(h2["sector"]) == "floor" and StoryProjector.project_ground(h2["at"].x, h2["at"].y, 0.0, _pose_of(map, "floor_centre"), VIEW)["visible"]:
			from_start += 1
	assert_true(from_start >= 10, "the dancer at floor_centre sees most of the floor (%d)" % from_start)


func test_no_dancer_stands_within_a_metre_of_a_waypoint() -> void:
	var map := StoryMap.load_chapter("night_one")
	for aid in map.homes:
		for wid in map.waypoints:
			assert_true((map.homes[aid]["at"] as Vector2).distance_to(map.waypoints[wid]["at"]) > 1.0, "%s is clear of %s" % [aid, wid])


func test_dancers_sort_far_to_near() -> void:
	var stage := _stage()
	var c: StoryCrowd = stage.crowd
	_look_from(stage, "floor_centre", 2.0)
	var order := c.drawn_order()
	assert_true(order.size() >= 8, "the core crowd is drawn (%d)" % order.size())
	var prev_z := -INF
	for id in order:  # the camera looks along -z: a smaller z is further and is drawn first
		var z := float((c.actors[id]["pos"] as Vector2).y)
		assert_true(z >= prev_z - 1.0e-4, "%s is drawn after something further" % id)
		prev_z = z
	# nearer is later, whatever the ids
	c.actors["c01"]["pos"] = Vector2(0.0, 4.9)
	c.actors["c01"]["sec"] = "floor"
	c.actors["c10"]["pos"] = Vector2(0.4, 5.1)
	c.actors["c10"]["sec"] = "floor"
	_look_from(stage, "floor_centre", 2.0)
	var o2 := c.drawn_order()
	assert_true(o2.find("c10") > o2.find("c01"), "the nearer dancer is drawn over the further one")
	stage.free()


func test_sectors_out_of_sight_are_culled() -> void:
	var stage := _stage()
	var c: StoryCrowd = stage.crowd
	var map := stage.map
	var w: Dictionary = map.waypoint("floor_centre")
	var vis := map.visible_sectors(w["at"], 0.0, "floor", VIEW.x / VIEW.y)
	assert_eq(vis["floor"], 0)
	assert_true(vis.has("steps"), "the stage steps are straight ahead")
	assert_false(vis.has("toilets") or vis.has("cubicle_a"), "the toilets are far behind walls")
	# in a cubicle, looking away from everything: the floor crowd is not drawn at all
	_look_from(stage, "cubicle", 2.0)
	assert_eq(c.drawn, 0, "nobody is drawn from the cubicle")
	for id in c.actors:
		assert_false((c.actors[id]["node"] as StoryCharacter).visible and str(c.actors[id]["sec"]) == "floor")
	# the door sees through its portal: gatherers in the entrance are drawn from the door waypoint facing the room
	var d: Dictionary = map.waypoint("door")
	var vd := map.visible_sectors(d["at"], 0.0, "entrance", VIEW.x / VIEW.y)
	assert_true(vd.has("floor"), "from the door looking into the club the floor is one portal away")
	assert_false(map.visible_sectors(d["at"], 180.0, "entrance", VIEW.x / VIEW.y).has("floor"), "and not when facing the street")
	stage.free()


func test_visible_sectors_looks_two_portals_deep_at_most() -> void:
	var map := StoryMap.load_chapter("night_one")
	var w: Dictionary = map.waypoint("steps")
	var vis := map.visible_sectors(w["at"], 0.0, "steps", 2.0, 2)
	assert_true(vis.has("riser") and vis.has("booth"), "up the steps: the riser, then the booth")
	assert_eq(map.visible_sectors(w["at"], 0.0, "steps", 2.0, 1).has("booth"), false, "one portal deep stops at the riser")


func test_directive_targets_resolve_to_places_inside_the_rooms() -> void:
	var stage := _stage()
	var c: StoryCrowd = stage.crowd
	var map := stage.map
	var b := stage.bar_s()
	c.bring_in("early", 0.0)
	c.gather_at_door("gatherers", 0.0)
	c.bring_in("peak", 0.0)
	c.gatherers_enter(10.0, true)
	c.circle_form(20.0)
	c.hero_to(c.centre_spot(), 20.0)
	c.step_back_some(30.0)
	c.regroup(40.0)
	c.walk_to("c01", c.solo_spot(), 50.0, 2.0)
	for id in c.actors:
		var mv: Dictionary = c.actors[id]["move"]
		if mv.is_empty():
			continue
		assert_true(mv.has("path"), "%s walks a route through the doors" % id)
		assert_true(map.sector_at(mv["to"]) != "", "%s: target %s is inside a room" % [id, mv["to"]])
	# sample the whole crowd while it moves: nobody is ever outside every sector (walking through a wall)
	var t := 0.0
	var bad := 0
	while t < 60.0:
		stage.update(t, 60.0)
		for id in c.actors:
			if c.actors[id]["present"] and map.sector_at(c.actors[id]["pos"]) == "" and bool(c.actors[id]["node"].visible):
				bad += 1
		t += 0.1
	assert_eq(bad, 0, "no dancer is ever inside a wall while walking")
	assert_true(b > 0.0)
	stage.free()


func test_gatherers_wait_at_the_door_and_come_in_to_their_homes() -> void:
	var stage := _stage()
	var c: StoryCrowd = stage.crowd
	c.gather_at_door("gatherers", 0.0)
	stage.update(10.0, 50.0)
	for id in c.ids_of("gatherers"):
		var slot := int(c.actors[id]["data"].get("door_slot", 0))
		assert_eq(c.actors[id]["pos"], c.door_slots[slot], "%s waits in its door slot" % id)
		assert_eq(stage.map.sector_at(c.actors[id]["pos"]), "entrance")
	c.gatherers_enter(12.0, true)
	stage.update(30.0, 50.0)
	for id in c.ids_of("gatherers"):
		assert_true((c.actors[id]["pos"] as Vector2).distance_to(c.actors[id]["home"]) < 0.01, "%s reached the floor" % id)
		assert_eq(c.actors[id]["sec"], "floor")
	c.gatherers_enter(40.0, false)
	stage.update(60.0, 50.0)
	var stayed := 0
	for id in c.ids_of("gatherers"):
		if not bool(c.actors[id]["data"].get("stays_on_bad", false)):
			stayed += 1
			assert_true((c.actors[id]["pos"] as Vector2).distance_to(stage.map.home(str(id))["side"]) < 0.01, "%s waits at the edge of the floor" % id)
	assert_true(stayed >= 3, "some of them leave to the side on a bad night")
	stage.free()


func test_the_circle_is_a_ring_inside_the_floor_open_towards_the_stage() -> void:
	var stage := _stage()
	var c: StoryCrowd = stage.crowd
	c.bring_in("early", 0.0, 0.1)
	stage.update(1.0, 60.0)
	c.circle_form(1.0, 0.5)
	stage.update(3.0, 60.0)
	var n := 0
	for id in c.ids_of("circle"):
		if not c.actors[id]["present"]:
			continue
		n += 1
		var p: Vector2 = c.actors[id]["pos"]
		assert_eq(stage.map.sector_at(p), "floor")
		var d := (p - c.circle_c)
		assert_near(pow(d.x / c.circle_r.x, 2.0) + pow(d.y / c.circle_r.y, 2.0), 1.0, 1e-3, "%s stands on the ring" % id)
		assert_true(d.normalized().dot(c.circle_open) < 0.95, "%s leaves the opening clear" % id)
	assert_true(n >= 10)
	stage.free()


func test_an_occluder_draws_over_a_dancer_behind_it_and_under_one_in_front() -> void:
	var stage := _stage()
	var c: StoryCrowd = stage.crowd
	var map := stage.map
	var stack: Dictionary = map.occluders[0]
	var at: Vector2 = stack["at"]
	stage.attach_world(map, false)
	var behind := Vector2(at.x, at.y - 1.5)
	var front := Vector2(at.x + 0.1, at.y + 2.0)
	c.actors["c01"]["pos"] = behind
	c.actors["c01"]["sec"] = "floor"
	c.actors["c10"]["pos"] = front
	c.actors["c10"]["sec"] = "floor"
	_look_from(stage, "floor_centre", 2.0)
	var occ: StoryCrowdProp
	for p in c.props:
		if p.kind == "occluder" and p.name == "Occ_" + str(stack["id"]):
			occ = p
	assert_true(occ != null)
	if occ == null:
		stage.free()
		return
	assert_true(occ.visible, "the stack is in view from the start")
	var i_occ := occ.get_index()
	assert_true(i_occ > (c.actors["c01"]["node"] as Node).get_index(), "a dancer behind the stack is drawn before it (covered)")
	assert_true(i_occ < (c.actors["c10"]["node"] as Node).get_index(), "a dancer in front of it is drawn over it")
	stage.free()


func test_projected_scale_follows_distance() -> void:
	var stage := _stage()
	var c: StoryCrowd = stage.crowd
	c.actors["c01"]["pos"] = Vector2(0.0, 2.0)
	c.actors["c01"]["sec"] = "floor"
	c.actors["c10"]["pos"] = Vector2(0.3, -1.0)
	c.actors["c10"]["sec"] = "floor"
	_look_from(stage, "floor_centre", 2.0)
	var near: StoryCharacter = c.actors["c01"]["node"]
	var far: StoryCharacter = c.actors["c10"]["node"]
	var ppm_near := near.scale.x * float(near.rig.get("height", 260.0))  # pixels per metre, whatever the rig's own size
	var ppm_far := far.scale.x * float(far.rig.get("height", 260.0))
	assert_near(ppm_near / ppm_far, 7.5 / 4.5, 0.02, "pixels per metre fall off with distance")
	assert_true(near.position.y > far.position.y, "and stands lower on the screen")
	stage.free()


func test_a_dancer_at_the_eye_fades_out() -> void:
	var stage := _stage()
	var c: StoryCrowd = stage.crowd
	c.actors["c01"]["pos"] = Vector2(0.0, 6.0)  # half a metre in front of the dancer at floor_centre
	c.actors["c01"]["sec"] = "floor"
	_look_from(stage, "floor_centre", 2.0)
	assert_false((c.actors["c01"]["node"] as StoryCharacter).visible, "too close to draw")
	stage.free()


func test_map_rejects_bad_spots_and_silhouettes() -> void:
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/night_one.json"))
	raw["spots"]["circle"]["radii"] = [9.0, 2.0]
	var m := StoryMap.from_dict(raw, "night_one", false)
	assert_true(m.errors.any(func(e: Variant) -> bool: return "circle leaves" in str(e)), "a circle wider than its room is rejected")
	var raw2: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/night_one.json"))
	raw2["silhouettes"][0]["at"] = [50, 50]
	var m2 := StoryMap.from_dict(raw2, "night_one", false)
	assert_false(m2.errors.is_empty(), "a silhouette outside every sector is rejected")
	var raw3: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/night_one.json"))
	raw3["occluders"][0]["sprite"] = "nonexistent"
	assert_false(StoryMap.from_dict(raw3, "night_one", false).errors.is_empty(), "an occluder needs one of the map's textures")


func test_night_one_chapter_file_has_no_design_space_numbers() -> void:
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/night_one.json"))
	for a in raw["actors"]:
		for k in ["x", "depth", "side_x", "side_depth"]:
			assert_false(a.has(k), "actor %s has no %s: the map places it" % [a["id"], k])
	for s in raw["silhouettes"]:
		assert_false(s.has("x") or s.has("depth"), "silhouette %s is placed by the map" % s["id"])


func test_the_dj_in_the_booth_sees_the_floor_crowd_three_portals_away() -> void:
	var stage := _stage()
	_look_from(stage, "booth", 2.0)
	assert_true(stage.crowd.drawn >= 5, "the booth looks over the riser and steps onto the floor (%d drawn)" % stage.crowd.drawn)
	var w: Dictionary = stage.map.waypoint("booth")
	assert_true(stage.map.visible_sectors(w["at"], float(w["yaw"]), "booth", VIEW.x / VIEW.y).has("floor"))
	stage.free()
