extends TestCase
## StoryPlayer, StoryFreeLook and StoryProjector: the rail camera is a pure function of song time (the same at any step, after a restart, with
## actions arriving out of order), paths run through portals inside their sectors, arrival faces the waypoint, the free look clamps and eases back,
## and the pinhole projection is consistent.

const BPM := 174.0


func _player() -> StoryPlayer:
	var p := StoryPlayer.new()
	p.setup(StoryMap.load_chapter("night_one"), BPM)
	return p


func _act(t0: float, action: String, args: Dictionary) -> Dictionary:
	return {"t0": t0, "bar": 1.0, "action": action, "args": args, "block": "", "source": "block"}


func _journey(p: StoryPlayer) -> void:
	var b := p.bar_s()
	p.apply_action(_act(8.0 * b, "player_move", {"to": "booth", "style": "walk", "bars": 4.0}))
	p.apply_action(_act(20.0 * b, "player_move", {"to": "floor_edge", "style": "stagger", "bars": 3.0}))
	p.apply_action(_act(30.0 * b, "player_look", {"at": "steps", "bars": 2.0}))
	p.apply_action(_act(40.0 * b, "player_move", {"to": "cubicle", "style": "run", "bars": 4.0}))


func test_starts_at_the_start_waypoint_as_a_dancer() -> void:
	var p := _player()
	var pose := p.pose_at(0.0)
	var w := p.map.start_waypoint()
	assert_eq(pose["pos"], w["at"])
	assert_eq(pose["sector"], "floor")
	assert_eq(pose["role"], "dancer")
	assert_near(float(pose["ground"]), 0.0, 1e-6)
	assert_near((pose["cam"] as Vector3).y, 1.6, 0.1, "eye height plus a small dance bob")
	assert_false(pose["moving"])


func test_move_arrives_at_the_waypoint_facing_it() -> void:
	var p := _player()
	_journey(p)
	var b := p.bar_s()
	var after := p.pose_at(12.0 * b + 0.01)
	var booth := p.map.waypoint("booth")
	assert_true((after["pos"] as Vector2).distance_to(booth["at"]) < 0.001, "arrived: %s" % str(after["pos"]))
	assert_near(absf(wrapf(float(after["yaw"]) - float(booth["yaw"]), -180.0, 180.0)), 0.0, 0.01, "facing the waypoint's yaw")
	assert_eq(after["sector"], "booth")
	assert_near(float(after["ground"]), 1.1, 0.001, "standing on the booth floor")
	assert_false(after["moving"])
	assert_true(p.pose_at(10.0 * b)["moving"], "mid move")
	assert_eq(p.pose_at(10.0 * b)["style"], "walk")
	var before := p.pose_at(8.0 * b - 0.01)
	assert_eq(before["pos"], p.map.start_waypoint()["at"], "nothing moves before the move's time")


func test_path_runs_through_portals_inside_sectors() -> void:
	var p := _player()
	_journey(p)
	var b := p.bar_s()
	var seen := {}
	var t := 0.0
	while t < 46.0 * b:
		var pose := p.pose_at(t)
		var at: Vector2 = pose["pos"]
		var sec := p.map.sector_at(at)
		assert_true(sec != "", "at t=%.2f the camera is inside the map (%s)" % [t, str(at)])
		if sec != str(pose["sector"]):  # exactly on a portal line either side is fine
			assert_true(p.map.neighbors(sec).has(str(pose["sector"])), "t=%.2f sector %s vs %s" % [t, sec, pose["sector"]])
		seen[pose["sector"]] = true
		t += 0.05
	for s in ["floor", "steps", "riser", "booth", "corridor", "toilets", "cubicle_b"]:
		assert_true(seen.has(s), "passed through " + s)
	assert_false(seen.has("bar"), "never took a detour through the bar")


func test_the_floor_rises_smoothly_up_the_steps() -> void:
	var p := _player()
	p.apply_action(_act(0.0, "player_move", {"to": "booth", "style": "climb", "bars": 4.0}))
	var prev := 0.0
	var peak := 0.0
	var t := 0.0
	var end := 4.0 * p.bar_s()
	while t <= end:
		var g := float(p.pose_at(t)["ground"])
		assert_true(absf(g - prev) < 0.06, "no jump in floor height (%.3f to %.3f at t=%.2f)" % [prev, g, t])
		prev = g
		peak = maxf(peak, g)
		t += 0.02
	assert_near(peak, 1.1, 0.001)
	assert_near(float(p.pose_at(end)["ground"]), 1.1, 0.001)


func test_pose_is_the_same_at_any_step_after_restart_and_out_of_order() -> void:
	var a := _player()
	_journey(a)
	var samples: Array = []
	for k in 60:
		var t := float(k) * 0.77
		var pose := a.pose_at(t)
		samples.append([pose["cam"], pose["yaw"], pose["roll"], pose["sector"]])
	# a restart: reset and schedule again, in the opposite order
	var b := _player()
	b.reset()
	var order := [3, 2, 1, 0]
	var acts: Array = []
	var bs := b.bar_s()
	acts.append(_act(8.0 * bs, "player_move", {"to": "booth", "style": "walk", "bars": 4.0}))
	acts.append(_act(20.0 * bs, "player_move", {"to": "floor_edge", "style": "stagger", "bars": 3.0}))
	acts.append(_act(30.0 * bs, "player_look", {"at": "steps", "bars": 2.0}))
	acts.append(_act(40.0 * bs, "player_move", {"to": "cubicle", "style": "run", "bars": 4.0}))
	for i in order:
		b.apply_action(acts[i])
	for k in 60:
		var t := float(k) * 0.77
		var pose := b.pose_at(t)
		assert_eq([pose["cam"], pose["yaw"], pose["roll"], pose["sector"]], samples[k], "t=%.2f same whatever the order" % t)
	# stepping time forward at 30 fps, 60 fps and a ragged step never changes the pose at a given time (it is stateless)
	for step in [1.0 / 30.0, 1.0 / 60.0, 0.0137]:
		var t := 0.0
		var last := {}
		while t < 25.0:
			last = a.pose_at(t)
			t += step
		var direct := a.pose_at(t - step)
		assert_eq(last["cam"], direct["cam"])
	assert_true(a.errors.is_empty(), str(a.errors))


func test_a_move_interrupting_a_move_is_continuous() -> void:
	var p := _player()
	var b := p.bar_s()
	p.apply_action(_act(0.0, "player_move", {"to": "booth", "style": "walk", "bars": 4.0}))
	p.apply_action(_act(2.0 * b, "player_move", {"to": "corridor", "style": "run", "bars": 3.0}))
	var t0 := 2.0 * b
	var before := p.pose_at(t0 - 0.001)
	var after := p.pose_at(t0 + 0.001)
	assert_true((before["pos"] as Vector2).distance_to(after["pos"]) < 0.05, "the second move picks up where the first was")
	assert_true(absf(float(before["ground"]) - float(after["ground"])) < 0.05)
	var end := p.pose_at(5.0 * b + 0.01)
	assert_eq(end["sector"], "corridor")
	assert_true(p.errors.is_empty(), str(p.errors))


func test_unknown_targets_are_reported_not_fatal() -> void:
	var p := _player()
	p.apply_action(_act(1.0, "player_move", {"to": "nowhere", "bars": 2.0}))
	assert_false(p.errors.is_empty())
	var pose := p.pose_at(5.0)
	assert_eq(pose["pos"], p.map.start_waypoint()["at"], "it stays put")
	assert_false(p.apply_action(_act(1.0, "doors_open", {})), "other actions are not the player's")


func test_look_turns_to_face_a_waypoint_and_holds() -> void:
	var p := _player()
	var b := p.bar_s()
	p.apply_action(_act(2.0 * b, "player_look", {"at": "corridor", "bars": 2.0}))
	assert_true(p.look_active(3.0 * b))
	assert_false(p.look_active(5.0 * b))
	var y := float(p.pose_at(5.0 * b)["yaw"])
	var from: Vector2 = p.map.start_waypoint()["at"]
	var to: Vector2 = p.map.waypoint("corridor")["at"]
	var want := rad_to_deg(atan2(-(to.x - from.x), -(to.y - from.y)))
	assert_near(absf(wrapf(y - want, -180.0, 180.0)), 0.0, 0.01, "facing the corridor")
	assert_eq(p.pose_at(5.0 * b)["pos"], from, "turning the head does not move the player")
	assert_near(float(p.pose_at(100.0 * b)["yaw"]), y, 1e-6, "the look holds")
	p.apply_action(_act(20.0 * b, "player_look", {"yaw": 0.0, "bars": 1.0}))
	assert_near(float(p.pose_at(25.0 * b)["yaw"]), 0.0, 1e-6)


func test_bob_is_locked_to_the_beat() -> void:
	var p := _player()
	var b := p.bar_s()
	p.apply_action(_act(0.0, "player_move", {"to": "booth", "style": "walk", "bars": 4.0}))
	var beat := 60.0 / BPM
	# footfalls land on the beat: the eye is lowest on integer beats and highest between them (compare at nearly the same u)
	var t_mid := 2.0 * b
	var n := roundf(t_mid / beat)
	var low := float(p.pose_at(n * beat)["cam"].y) - float(p.pose_at(n * beat)["ground"])
	var high := float(p.pose_at((n + 0.5) * beat)["cam"].y) - float(p.pose_at((n + 0.5) * beat)["ground"])
	assert_true(high > low + 0.02, "the eye dips on the beat (%.3f vs %.3f)" % [low, high])
	# the same phase two beats later gives the same bob at the same moment of the move's envelope (period of the footfalls)
	var a1 := p.pose_at(n * beat)
	var a2 := p.pose_at((n + 2.0) * beat)
	assert_true(absf(float(a1["roll"]) - float(a2["roll"])) < 0.2)
	# styles differ
	var q := _player()
	q.apply_action(_act(0.0, "player_move", {"to": "booth", "style": "stagger", "bars": 4.0}))
	var rolls := 0.0
	var walk_rolls := 0.0
	var t := b
	while t < 3.0 * b:
		rolls = maxf(rolls, absf(float(q.pose_at(t)["roll"])))
		walk_rolls = maxf(walk_rolls, absf(float(p.pose_at(t)["roll"])))
		t += 0.02
	assert_true(rolls > walk_rolls * 2.0, "stagger rolls more than walking (%.2f vs %.2f)" % [rolls, walk_rolls])


func test_reduced_motion_keeps_the_path_and_drops_the_bob() -> void:
	var a := _player()
	var r := _player()
	r.reduced = true
	var b := a.bar_s()
	for p in [a, r]:
		p.apply_action(_act(0.0, "player_move", {"to": "booth", "style": "run", "bars": 4.0}))
		p.apply_action(_act(0.0, "fx_queasy", {"amount": 1.0, "bars": 1.0}))
	for k in 40:
		var t := float(k) * 0.2
		assert_eq(a.pose_at(t)["pos"], r.pose_at(t)["pos"], "same path")
		assert_near(float(r.pose_at(t)["roll"]), 0.0, 1e-9, "no roll")
		assert_near((r.pose_at(t)["cam"] as Vector3).y, float(r.pose_at(t)["ground"]) + 1.6, 1e-6, "no bob")
	assert_true(absf(float(a.pose_at(2.0 * b)["roll"])) > 0.0)


func test_roles_queasy_and_sick_follow_song_time() -> void:
	var p := _player()
	var b := p.bar_s()
	p.apply_action(_act(10.0 * b, "player_role", {"role": "queasy"}))
	p.apply_action(_act(30.0 * b, "player_role", {"role": "sick"}))
	p.apply_action(_act(40.0 * b, "player_role", {"role": "recovered"}))
	assert_eq(p.role_at(0.0), "dancer")
	assert_eq(p.role_at(10.0 * b), "queasy")
	assert_eq(p.role_at(35.0 * b), "sick")
	assert_eq(p.role_at(50.0 * b), "recovered")
	p.apply_action(_act(12.0 * b, "fx_queasy", {"amount": 0.6, "bars": 4.0}))
	assert_near(p.queasy_at(11.0 * b), 0.0, 1e-9)
	assert_near(p.queasy_at(14.0 * b), 0.3, 1e-6, "half way, eased")
	assert_near(p.queasy_at(40.0 * b), 0.6, 1e-9, "held")
	p.apply_action(_act(32.0 * b, "fx_queasy", {"amount": 0.0, "bars": 2.0}))
	assert_near(p.queasy_at(40.0 * b), 0.0, 1e-9, "eased back")
	p.apply_action(_act(30.0 * b, "sick_beat", {"bars": 4.0}))
	assert_near(p.sick_at(29.0 * b), 0.0, 1e-9)
	assert_true(p.sick_at(32.0 * b) > 0.99, "head down mid beat")
	assert_near(p.sick_at(34.5 * b), 0.0, 1e-9)
	var low := (p.pose_at(32.0 * b)["cam"] as Vector3).y
	var up := (p.pose_at(36.0 * b)["cam"] as Vector3).y
	assert_true(up - low > 0.4, "the eye drops with the head")


func test_free_look_clamps_and_eases_back() -> void:
	var f := StoryFreeLook.new()
	f.drag(-100000.0)  # a huge drag to the left
	assert_near(f.offset, 60.0, 1e-9, "clamped at +60")
	f.drag(100000.0)
	assert_near(f.offset, -60.0, 1e-9, "clamped at -60")
	f.release()
	var o0 := f.offset
	f.update(1.0 / 60.0)
	assert_true(absf(f.offset) < absf(o0), "eases toward centre once released")
	for k in 600:
		f.update(1.0 / 60.0)
	assert_near(f.offset, 0.0, 0.01, "back to centre")
	# frame-rate independent
	var a := StoryFreeLook.new()
	var b := StoryFreeLook.new()
	a.offset = 40.0
	b.offset = 40.0
	for k in 60:
		a.update(1.0 / 60.0)
	for k in 30:
		b.update(1.0 / 30.0)
	assert_near(a.offset, b.offset, 1e-6, "the same after one second at 60 and 30 fps")
	# keys
	var k := StoryFreeLook.new()
	k.set_key_axis(1.0)
	for i in 120:
		k.update(1.0 / 60.0)
	assert_near(k.offset, 60.0, 1e-9, "Q clamps at +60")
	k.set_key_axis(-1.0)
	for i in 240:
		k.update(1.0 / 60.0)
	assert_near(k.offset, -60.0, 1e-9, "E clamps at -60")
	k.set_key_axis(0.0)
	k.dragging = true
	k.update(1.0)
	assert_near(k.offset, -60.0, 1e-9, "a held drag does not ease back")
	# an authored look pulls the offset back faster
	var s := StoryFreeLook.new()
	var n := StoryFreeLook.new()
	s.offset = 50.0
	n.offset = 50.0
	s.update(0.2, true)
	n.update(0.2, false)
	assert_true(s.offset < n.offset)


func test_projector_geometry() -> void:
	var vp := Vector2(480, 270)
	var pose := {"cam": Vector3(0, 1.6, 6), "yaw": 0.0}
	var ahead := StoryProjector.project(Vector3(0, 1.6, 0), pose, vp)
	assert_true(ahead["visible"])
	assert_near((ahead["screen"] as Vector2).x, 240.0, 0.001)
	assert_near((ahead["screen"] as Vector2).y, 135.0, 0.001)
	assert_near(float(ahead["depth"]), 6.0, 1e-6)
	var right := StoryProjector.project(Vector3(1, 1.6, 0), pose, vp)
	assert_true((right["screen"] as Vector2).x > 240.0, "+x is to the right when looking down -z")
	var feet := StoryProjector.project_ground(0, 0, 0.0, pose, vp)
	assert_true((feet["screen"] as Vector2).y > 135.0, "the ground is below the horizon")
	var near := StoryProjector.project_ground(0, 3, 0.0, pose, vp)
	assert_true((near["screen"] as Vector2).y > (feet["screen"] as Vector2).y, "nearer feet are lower on screen")
	assert_true(float(near["scale"]) > float(feet["scale"]), "and larger")
	assert_false(StoryProjector.project(Vector3(0, 1, 7), pose, vp)["visible"], "behind the camera")
	# turning left 90 degrees faces -x: a point at -x is dead ahead, +z is now to the right? (left turn: +z is to the left side behind)
	var left := {"cam": Vector3(0, 1.6, 0), "yaw": 90.0}
	var p2 := StoryProjector.project(Vector3(-5, 1.6, 0), left, vp)
	assert_near((p2["screen"] as Vector2).x, 240.0, 0.001)
	var p3 := StoryProjector.project(Vector3(-5, 1.6, -1), left, vp)
	assert_true((p3["screen"] as Vector2).x > 240.0, "-z is on the right when facing -x")
	# round trip
	var g := StoryProjector.project_ground(2.0, 1.0, 0.3, pose, vp)
	var back: Variant = StoryProjector.unproject_ground(g["screen"], 0.3, pose, vp)
	assert_true(back != null and (back as Vector2).distance_to(Vector2(2.0, 1.0)) < 0.001, "unproject inverts project")
	assert_true(StoryProjector.unproject_ground(Vector2(240, 50), 0.0, pose, vp) == null, "above the horizon")
	assert_eq(StoryProjector.draw_order([1.0, 5.0, 3.0, 5.0]), [1, 3, 2, 0], "far to near, ties by index")


func test_projector_matches_the_renderers_camera() -> void:
	var vp := SubViewport.new()
	vp.size = Vector2i(480, 270)
	tree.root.add_child(vp)
	var cam := Camera3D.new()
	cam.fov = StoryProjector.FOV_V
	cam.keep_aspect = Camera3D.KEEP_HEIGHT
	cam.near = StoryProjector.NEAR
	vp.add_child(cam)
	cam.position = Vector3(1.0, 1.7, 4.0)
	cam.rotation_degrees = Vector3(0, 35, 0)
	var pose := {"cam": cam.position, "yaw": 35.0}
	for w in [Vector3(-2, 0, -3), Vector3(3, 1.2, -1), Vector3(0, 2, -6)]:
		var mine := StoryProjector.project(w, pose, Vector2(480, 270))
		if not cam.is_position_behind(w) and mine["visible"]:
			var theirs := cam.unproject_position(w)
			assert_true(theirs.distance_to(mine["screen"]) < 0.5, "%s: engine %s vs mine %s" % [w, theirs, mine["screen"]])
	vp.queue_free()
