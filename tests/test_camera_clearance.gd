extends TestCase
## The run camera never stares into a wall from arm's length (docs/art/VISUAL_AUDIT.md F5 and F16, docs/art/CAMERA_CLEARANCE.md): every scene of the main run and of the three
## paths, entered every way the player can come into it (the run's start, the passage from another world, the door walk from each scene before it), is played on the real rail
## camera with the perfect bot and the default exit, and at one sample a beat no pose may have the centre of the picture and more than half its width on a wall nearer than
## 2.5 m (tools/art/camera_clearance_check.gd; the tool tools/art/camera_clearance.gd samples twice a beat and writes the table). A scene added later is checked too.

const CC := preload("res://tools/art/camera_clearance_check.gd")


func test_no_scene_pose_stares_into_a_wall() -> void:
	var rows: Array = CC.check_all(1.0)
	var scenes := {}
	var samples := 0
	for r in rows:
		scenes["%s/%s" % [r["path"], r["scene"]]] = true
		samples += int(r["samples"])
		for er in r["errors"]:
			fail("%s (%s): journey error %s" % [r["scene"], r["entry"], er])
		for f in r["fails"]:
			fail("%s%s (%s%s) beats %.1f to %.1f, %s: the centre %.2f m and %d%% of the picture's width on a wall nearer than %.1f m (%s)" % [
				"" if str(r["path"]) == "" else str(r["path"]) + ": ", r["scene"], r["entry"], "" if str(r["from"]) == "" else " from " + str(r["from"]),
				float(f["from_b"]), float(f["to_b"]), f["kind"], float(f["centre"]), roundi(100.0 * float(f["share"])), CC.FRAME_M, f["what"]])
	assert_true(scenes.size() >= 82, "every scene of the run and the three paths is checked (%d)" % scenes.size())
	assert_true(samples > 5000, "the scenes are sampled every beat (%d samples)" % samples)


## The rays themselves: a wall face-on at 1 m fails, the same wall at 4 m and a corridor's side walls seen along it do not.
func test_the_rays_see_a_near_wall_and_not_a_corridor() -> void:
	var m := StoryMap.from_dict({"id": "box", "start": "a", "sectors": [
		{"id": "room", "polygon": [[-5, -10], [5, -10], [5, 10], [-5, 10]], "floor": 0, "ceiling": 3},
		{"id": "hall", "polygon": [[-1, 10], [1, 10], [1, 30], [-1, 30]], "floor": 0, "ceiling": 3}],
		"walls": [{"sector": "room", "from": [1, 10], "to": [-1, 10], "portal": "hall"}],
		"waypoints": [{"id": "a", "at": [0, 0], "yaw": 0, "sector": "room"}]})
	assert_eq(m.errors, [], "the test map builds")
	var near := CC.clearance(m, {"cam": Vector3(0, 1.6, -9.0), "yaw": 0.0, "pitch": 0.0, "sector": "room"})
	assert_true(CC.fails(near), "facing the end wall from 1 m: %.2f m, %.0f%%" % [float(near["centre"]), 100.0 * float(near["share"])])
	assert_near(float(near["centre"]), 1.0, 0.06, "the centre ray meets the wall a metre ahead")
	var far := CC.clearance(m, {"cam": Vector3(0, 1.6, -6.0), "yaw": 0.0, "pitch": 0.0, "sector": "room"})
	assert_false(CC.fails(far), "the same wall from 4 m")
	var hall := CC.clearance(m, {"cam": Vector3(0, 1.6, 12.0), "yaw": 180.0, "pitch": 0.0, "sector": "hall"})
	assert_false(CC.fails(hall), "looking down a 2 m corridor: its side walls recede (%.2f m, %.0f%%)" % [float(hall["centre"]), 100.0 * float(hall["share"])])
	var up := CC.clearance(m, {"cam": Vector3(0, 1.6, 0.0), "yaw": 0.0, "pitch": 40.0, "sector": "room"})
	assert_true(float(up["centre"]) < 2.5, "a look up meets the ceiling (%.2f m)" % float(up["centre"]))
