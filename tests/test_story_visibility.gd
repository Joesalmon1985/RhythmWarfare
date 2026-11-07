extends TestCase
## Which pieces of a map are drawn (StoryMap.visible_sectors, docs/story/HEIGHTS_AND_PATHS.md): the hand-made maps keep the portal flood; a map in "clip" mode (every map of
## CLIP_FROM sectors or more) narrows the view window at every portal, so a room behind a solid wall is not drawn even when a doorway beyond the first one points at it.
##
##   z -8 +------- far -------+
##     -4 +-------- hall --------------------+
##      0 +--door--+   (4..6)    +--door to side (14..16)
##        |  room  |   wall at x=10   | side |
##     10 +--------+                  +------+
##        0       10                  20

const AREA := 2.8  # the run's picture is wide: about 480 x 170


func _data(mode: String) -> Dictionary:
	return {"start": "a", "visibility": {"mode": mode},
		"sectors": [
			{"id": "room", "polygon": [[0, 0], [10, 0], [10, 10], [0, 10]], "floor": 0, "ceiling": 3},
			{"id": "side", "polygon": [[10, 0], [20, 0], [20, 10], [10, 10]], "floor": 0, "ceiling": 3},
			{"id": "hall", "polygon": [[0, -4], [20, -4], [20, 0], [0, 0]], "floor": 0, "ceiling": 3},
			{"id": "far", "polygon": [[0, -8], [20, -8], [20, -4], [0, -4]], "floor": 0, "ceiling": 3}],
		"walls": [
			{"sector": "room", "from": [4, 0], "to": [6, 0], "portal": "hall"},
			{"sector": "side", "from": [14, 0], "to": [16, 0], "portal": "hall"},
			{"sector": "hall", "from": [4, -4], "to": [6, -4], "portal": "far"}],
		"waypoints": [{"id": "a", "at": [5, 8], "yaw": 0, "sector": "room"}]}


func test_a_room_behind_a_wall_is_not_drawn() -> void:
	var m := StoryMap.from_dict(_data("clip"))
	assert_eq(m.errors, [], "the test map builds")
	var vis := m.visible_sectors(Vector2(5, 8), 0.0, "room", AREA)
	assert_true(vis.has("room") and vis.has("hall"), "the room and the hall through its door: %s" % str(vis))
	assert_true(vis.has("far"), "the room beyond the hall, straight through both doors")
	assert_false(vis.has("side"), "the side room, behind the room's solid east wall, is not drawn")
	var old := StoryMap.from_dict(_data("flood"))
	assert_true(old.visible_sectors(Vector2(5, 8), 0.0, "room", AREA).has("side"), "the flood takes it (its door is in the view cone, though not seen through the room's door)")


func test_turning_and_walking_change_what_is_seen() -> void:
	var m := StoryMap.from_dict(_data("clip"))
	var back := m.visible_sectors(Vector2(5, 8), 180.0, "room", AREA)
	assert_eq(back.keys(), ["room"], "facing away from the door only the room")
	var at_door := m.visible_sectors(Vector2(5, 0.5), 0.0, "room", AREA)
	assert_true(at_door.has("hall") and at_door.has("far"), "in the doorway")
	var hall := m.visible_sectors(Vector2(10, -2), -90.0, "hall", AREA)
	assert_true(hall.has("side"), "from the hall, looking toward the side room's door")
	assert_false(hall.has("room"), "and not the room behind it")


func test_depth_and_far_limits() -> void:
	var d := _data("clip")
	d["visibility"] = {"mode": "clip", "depth": 1}
	var m := StoryMap.from_dict(d)
	var vis := m.visible_sectors(Vector2(5, 8), 0.0, "room", AREA)
	assert_true(vis.has("hall") and not vis.has("far"), "depth 1 stops after one portal")
	d["visibility"] = {"mode": "clip", "far": 9.0}
	m = StoryMap.from_dict(d)
	vis = m.visible_sectors(Vector2(5, 8), 0.0, "room", AREA)
	assert_true(vis.has("hall") and not vis.has("far"), "a portal 12 m away is past a 9 m far limit")


func test_big_maps_clip_and_small_maps_flood() -> void:
	assert_eq(StoryMap.load_chapter("mothership").vis_mode, "flood", "a hand-made map keeps the flood (drawn exactly as before)")
	var d := {"start": "a", "sectors": [], "walls": [], "waypoints": [{"id": "a", "at": [0.5, 0.5], "yaw": 0, "sector": "c0_0"}]}
	for i in 8:
		for j in 12:
			d["sectors"].append({"id": "c%d_%d" % [i, j], "polygon": [[i, j], [i + 1, j], [i + 1, j + 1], [i, j + 1]], "floor": 0, "ceiling": 3})
			if i < 7:
				d["walls"].append({"sector": "c%d_%d" % [i, j], "from": [i + 1, j], "to": [i + 1, j + 1], "portal": "c%d_%d" % [i + 1, j]})
			if j < 11:
				d["walls"].append({"sector": "c%d_%d" % [i, j], "from": [i, j + 1], "to": [i + 1, j + 1], "portal": "c%d_%d" % [i, j + 1]})
	d["waypoints"][0]["at"] = [0.5, 0.5]
	var m := StoryMap.from_dict(d)
	assert_eq(m.errors, [], "a grid of 96 pieces builds")
	assert_eq(m.vis_mode, "clip", "64 pieces or more clip by default")
	var vis := m.visible_sectors(Vector2(4.5, 11.5), 0.0, "c4_11", AREA)
	assert_true(vis.has("c4_0"), "an open hall cut into pieces is seen to its far end (deeper than the flood's 7)")
	assert_eq(int(vis.get("c4_0", -1)), 11, "eleven portals deep")
	assert_false(vis.has("c4_11") == false or vis.has("c7_11"), "its own piece, and not the pieces beside it out of the view cone (%d drawn)" % vis.size())
