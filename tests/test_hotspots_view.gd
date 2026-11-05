extends TestCase
## Hotspot projection and hit testing (HotspotView.layout / hit): anchors project through StoryProjector, a touch target is at least min_px wide, the nearest hotspot within its radius wins,
## and an anchor out of sight is still a touchable beacon at the edge of the picture.


func _entry(id: String, anchor: Dictionary, extra: Dictionary = {}) -> Dictionary:
	var h := {"id": id, "scene": "s", "kind": "exit", "anchor": anchor, "on_success": {"route": "x"}}
	for k in extra:
		h[k] = extra[k]
	return {"hotspot": HotspotContract.normalize(h, "warehouse", "night_one"), "state": "available", "t_state": 0.0}


func _pose_at(map: StoryMap, wp: String) -> Dictionary:
	var w: Dictionary = map.waypoint(wp)
	return {"cam": Vector3((w["at"] as Vector2).x, map.eye_height, (w["at"] as Vector2).y), "yaw": float(w["yaw"]), "pitch": 0.0}


func test_anchors_resolve_to_world_points() -> void:
	var m := StoryMap.load_chapter("night_one")
	var th := HotspotView.resolve({"thing": "bar_glow"}, m, {})
	assert_true(bool(th["ok"]))
	assert_near((th["pos"] as Vector3).x, 10.0, 0.001)
	assert_near((th["pos"] as Vector3).y, 1.8, 0.001, "a thing's y is above its floor")
	var wp := HotspotView.resolve({"waypoint": "to_bar"}, m, {})
	assert_true(bool(wp["ok"]))
	assert_true(float((wp["pos"] as Vector3).y) > float(wp["ground"]), "a doorway's centre is above the floor")
	var ps := HotspotView.resolve({"pos": [0.0, 1.2, 6.0]}, m, {})
	assert_true(bool(ps["ok"]))
	assert_near((ps["pos"] as Vector3).y, float(ps["ground"]) + 1.2, 0.001)
	assert_false(bool(HotspotView.resolve({"thing": "nope"}, m, {})["ok"]))
	assert_false(bool(HotspotView.resolve({"actor": "c01"}, m, {})["ok"]), "no crowd: an actor cannot be placed")


func test_a_touch_target_is_never_under_min_px_and_stays_inside_the_view() -> void:
	var m := StoryMap.load_chapter("night_one")
	var view := Vector2(844, 240)
	var pose := _pose_at(m, "floor_centre")
	var ents := [_entry("a", {"waypoint": "to_bar"}), _entry("b", {"waypoint": "to_balcony"}), _entry("c", {"thing": "disco_ball"}), _entry("far", {"pos": [0.0, 1.0, -8.0]}, {"radius_m": 0.05})]
	var lay := HotspotView.layout(ents, m, {}, pose, view)
	assert_eq(lay.size(), 4)
	for e in lay:
		assert_true(float(e["radius_px"]) * 2.0 >= 72.0 - 0.001, "%s is at least 72 px wide (%s)" % [e["id"], str(float(e["radius_px"]) * 2.0)])
		var c: Vector2 = e["centre"]
		assert_true(c.x >= 0.0 and c.x <= view.x and c.y >= 0.0 and c.y <= view.y, "%s is on screen: %s" % [e["id"], str(c)])
		assert_eq(HotspotView.hit(lay, c), str(e["id"]), "a tap on its centre hits it")


func test_the_nearest_hotspot_within_its_radius_wins_and_a_miss_hits_nothing() -> void:
	var lay := [
		{"id": "a", "centre": Vector2(100, 100), "radius_px": 40.0},
		{"id": "b", "centre": Vector2(160, 100), "radius_px": 40.0},
	]
	assert_eq(HotspotView.hit(lay, Vector2(120, 100)), "a", "inside both: the nearer centre")
	assert_eq(HotspotView.hit(lay, Vector2(140, 100)), "b")
	assert_eq(HotspotView.hit(lay, Vector2(100, 190)), "", "outside every radius")
	assert_eq(HotspotView.hit([], Vector2(1, 1)), "")


func test_an_anchor_out_of_sight_is_a_beacon_at_the_edge_that_can_still_be_touched() -> void:
	var m := StoryMap.load_chapter("night_one")
	var view := Vector2(844, 240)
	var pose := _pose_at(m, "stage")  # looking at the back wall; the bar is off to the side
	pose["yaw"] = 0.0
	var ents := [_entry("bar", {"thing": "bar_glow"}), _entry("behind", {"pos": [0.0, 1.0, 12.0]})]
	var lay := HotspotView.layout(ents, m, {}, pose, view)
	var edge := 0
	for e in lay:
		if bool(e["edge"]):
			edge += 1
			var c: Vector2 = e["centre"]
			assert_true(c.x < view.x * 0.2 or c.x > view.x * 0.8, "a beacon sits at a side of the picture: %s" % str(c))
			assert_true(c.x >= 0.0 and c.x <= view.x and c.y >= 0.0 and c.y <= view.y)
			assert_eq(HotspotView.hit(lay, c), str(e["id"]), "and a tap there selects it")
	assert_true(edge >= 1, "at least one anchor is out of sight from the stage")


func test_the_projection_is_the_stage_camera() -> void:
	var m := StoryMap.load_chapter("night_one")
	var view := Vector2(800, 400)
	var pose := _pose_at(m, "floor_centre")
	var lay := HotspotView.layout([_entry("a", {"pos": [0.0, 1.6, 0.0]})], m, {}, pose, view)
	var want := StoryProjector.project(lay[0]["world"], pose, view)
	assert_eq(lay[0]["centre"], want["screen"], "the layout is StoryProjector's")
	var big := HotspotView.layout([_entry("a", {"pos": [0.0, 1.6, 0.0]})], m, {}, pose, view * 2.0)
	assert_near((big[0]["centre"] as Vector2).x, (lay[0]["centre"] as Vector2).x * 2.0, 0.5, "it scales with the view, so the low-res draw and the screen hit test agree")


func test_light_tint_keeps_the_hue_at_full_brightness() -> void:
	for c in [Color(1.0, 0.7, 0.25), Color(0.2, 0.3, 0.9), Color(0.5, 0.5, 0.45), Color(0.9, 0.1, 0.6)]:
		var t := HotspotView.light_tint(c)
		assert_near(t.v, 1.0, 1e-4, "every world's lights are as bright")
		assert_true(t.s >= 0.35 - 1e-4 and t.s <= 0.6 + 1e-4, "and pale enough to read as light (%.2f)" % t.s)
		if c.s > 0.2:
			assert_near(absf(wrapf(t.h - c.h, -0.5, 0.5)), 0.0, 1e-3, "in the world's own hue")
