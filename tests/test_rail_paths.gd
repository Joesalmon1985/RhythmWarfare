extends TestCase
## Continuous rail paths (docs/story/HEIGHTS_AND_PATHS.md): a player_move may follow a polyline of waypoints (`via`, or `path`) over its bars, turning gently toward where it walks,
## the eye following the floor under it (a step up, a level portal); a leg may hold still at its end (`hold_bars`: no bob, no drift, no glance); a choice viewpoint holds for the
## whole choice window. StoryRailCheck rejects a leg through a wall, a drop or a void, and a choice viewpoint with no hold. The song clock stays the driver: the pose is a pure
## function of song time, the same at any step.

const FX := preload("res://tests/fixtures/story_heights_fixture.gd")
const BPM := 120.0  # a bar is 2 s


func _map() -> StoryMap:
	var d: Dictionary = FX.data()
	d["waypoints"].append({"id": "c0", "at": [-3, 6], "yaw": 0, "sector": "closet"})
	var m := StoryMap.from_dict(d)
	assert_eq(m.errors, [], "the heights map builds")
	return m


func _player(m: StoryMap, drift := false) -> StoryPlayer:
	var p := StoryPlayer.new()
	p.setup(m, BPM)
	p.drift_on = drift
	p.reduced = true
	return p


func _move(p: StoryPlayer, t0: float, args: Dictionary) -> void:
	p.apply_action({"t0": t0, "action": "player_move", "args": args, "bar": 0.0, "block": "", "source": "test"})


func test_a_polyline_move_walks_its_waypoints_over_its_bars() -> void:
	var m := _map()
	var p := _player(m)
	_move(p, 2.0, {"to": "c1", "via": ["s1", "c0"], "style": "walk", "bars": 4.0})
	assert_eq(p.errors, [], "every leg is a clean trace")
	assert_eq(p.pose_at(1.0)["pos"], m.waypoint("w0")["at"], "nothing moves before the move's time")
	var end := p.pose_at(10.0)
	assert_true((end["pos"] as Vector2).distance_to(m.waypoint("c1")["at"]) < 1e-4, "arrived at c1 when its 4 bars end: %s" % str(end["pos"]))
	assert_near(absf(wrapf(float(end["yaw"]) - float(m.waypoint("c1")["yaw"]), -180.0, 180.0)), 0.0, 0.01, "facing c1's yaw")
	assert_eq(end["sector"], "closet")
	var through: Dictionary = {}
	for k in 241:
		var pose := p.pose_at(2.0 + 8.0 * float(k) / 240.0)
		through[str(pose["sector"])] = true
		var pos: Vector2 = pose["pos"]
		assert_true(m.sector_at(pos) != "", "always inside the map (%s)" % str(pos))
	assert_eq(through.keys(), ["west", "step", "closet"], "west, up the step, through the door into the closet")
	for wid in ["s1", "c0"]:  # the walker passes over each via point
		var best := INF
		for k in 481:
			best = minf(best, (p.pose_at(2.0 + 8.0 * float(k) / 480.0)["pos"] as Vector2).distance_to(m.waypoint(wid)["at"]))
		assert_true(best < 0.05, "passes %s (%.3f m)" % [wid, best])


func test_turns_are_gentle_and_face_the_way_ahead() -> void:
	var m := _map()
	var p := _player(m)
	_move(p, 0.0, {"to": "c1", "via": ["s1", "c0"], "style": "walk", "bars": 4.0})
	var prev := float(p.pose_at(0.0)["yaw"])
	var worst := 0.0
	for k in range(1, 241):
		var y := float(p.pose_at(8.0 * float(k) / 240.0)["yaw"])
		worst = maxf(worst, absf(wrapf(y - prev, -180.0, 180.0)))
		prev = y
	assert_true(worst < 4.0, "no step of 1/30 s turns more than 4 degrees (%.2f)" % worst)
	var mid := p.pose_at(4.6)  # on the leg up through the closet door (facing +z: yaw 180)
	assert_true(absf(wrapf(float(mid["yaw"]) - 180.0, -180.0, 180.0)) < 45.0, "mid-way the camera faces the way it walks: %.1f" % float(mid["yaw"]))
	assert_eq(float(p.pose_at(8.0 * 0.3)["pitch"]), 0.0, "the head stays level: the pads stay readable")


func test_the_eye_follows_the_floor_up_a_step() -> void:
	var m := _map()
	var p := _player(m)
	_move(p, 0.0, {"to": "e1", "via": ["s1", "b1"], "style": "walk", "bars": 4.0})
	assert_eq(p.errors, [])
	assert_near((p.pose_at(0.0)["cam"] as Vector3).y, 1.6, 1e-4, "on the walkway")
	assert_near((p.pose_at(8.0)["cam"] as Vector3).y, 1.9, 1e-4, "0.3 m up on the far walkway")
	var lo := INF
	var hi := -INF
	var prev := 1.6
	for k in 241:
		var y := (p.pose_at(8.0 * float(k) / 240.0)["cam"] as Vector3).y
		lo = minf(lo, y)
		hi = maxf(hi, y)
		assert_true(y >= prev - 1e-4, "the eye never dips on the way up")
		prev = y
	assert_near(lo, 1.6, 1e-4)
	assert_near(hi, 1.9, 1e-4, "never higher than the step (the bridge over the void is level)")
	assert_eq(StoryRailCheck.check_move(m, "w0", {"to": "e1", "via": ["s1", "b1"], "style": "walk", "bars": 4.0}, "test"), [], "the check passes it")


func test_the_same_pose_at_any_step_and_after_a_restart() -> void:
	var m := _map()
	var a := _player(m)
	_move(a, 0.0, {"to": "c1", "via": ["s1", "c0"], "bars": 3.0})
	var b := _player(m)
	_move(b, 0.0, {"to": "c1", "path": ["s1", "c0", "c1"], "bars": 3.0})
	for t in [0.0, 0.7, 2.31, 4.5, 5.99, 7.0]:
		assert_eq(a.pose_at(t)["cam"], b.pose_at(t)["cam"], "`path` is `via` plus `to` (t %.2f)" % t)
	var before: Vector3 = a.pose_at(3.3)["cam"]
	a.reset()
	_move(a, 0.0, {"to": "c1", "via": ["s1", "c0"], "bars": 3.0})
	assert_eq(a.pose_at(3.3)["cam"], before, "a restart plays the same")


func test_a_hold_stands_still() -> void:
	var m := _map()
	var p := StoryPlayer.new()
	p.setup(m, BPM)  # bob and drift on: the hold must still be still
	_move(p, 0.0, {"to": "e1", "via": ["s1", "b1"], "bars": 2.0, "hold_bars": 2.0})
	var cam0: Vector3 = p.pose_at(4.0 + 0.5)["cam"]
	for k in 60:
		var t := 4.0 + 0.5 + 3.0 * float(k) / 60.0  # inside the hold, clear of its eased edges
		var pose := p.pose_at(t)
		assert_eq(pose["cam"], cam0, "no bob, no drift during the hold (t %.2f)" % t)
		assert_near(float(pose["still"]), 1.0, 1e-6)
	assert_true(float(p.pose_at(10.0)["still"]) < 1e-6, "after the hold the room moves again")
	var q := StoryPlayer.new()
	q.setup(m, BPM)
	q.apply_action({"t0": 1.0, "action": "player_hold", "args": {"bars": 2.0}})
	q.apply_action({"t0": 1.0, "action": "player_look", "args": {"by": 30.0, "bars": 2.0}})
	assert_near(float(q.pose_at(3.0)["yaw"]), float(q.pose_at(1.5)["yaw"]), 1e-6, "a glance inside a hold is held off")


func test_the_check_rejects_a_wall_a_drop_a_void_and_a_choice_without_hold() -> void:
	var m := _map()
	var wall := StoryRailCheck.check_move(m, "s1", {"to": "c1", "via": [], "path": [], "style": "walk"}, "t")
	assert_eq(wall, [], "a plain move takes the portal route: no wall")
	var through := StoryRailCheck.check_move(m, "w0", {"to": "c1", "via": ["s1"], "style": "walk"}, "t")
	assert_true(" ".join(PackedStringArray(through)).contains("wall"), "a straight leg from the step to the closet's far corner crosses the walkway's wall: %s" % str(through))
	var drop := StoryRailCheck.check_move(m, "e1", {"to": "h1", "style": "walk"}, "t")
	assert_true(" ".join(PackedStringArray(drop)).contains("drop"), "1.2 m up is a drop for a walk: %s" % str(drop))
	assert_eq(StoryRailCheck.check_move(m, "e1", {"to": "h1", "style": "climb"}, "t"), [], "and a climb takes it")
	var d: Dictionary = FX.data()
	d["waypoints"].append({"id": "pit_side", "at": [2, -2.0], "yaw": 0, "sector": "bridge"})
	var rail := StoryRailCheck.check_move(m, "s1", {"to": "e1", "via": ["b1"], "style": "walk"}, "t")
	assert_eq(rail, [], "along the bridge between its railings")
	var tr := m.trace_segment(Vector2(2, 0), Vector2(2, 3), "bridge")
	assert_true(" ".join(PackedStringArray(tr["errors"])).contains("railing"), "over the railing: %s" % str(tr["errors"]))
	var tr2 := m.trace_segment(Vector2(-3, 2), Vector2(1, 3), "step")
	assert_true(" ".join(PackedStringArray(tr2["errors"])).contains("void"), "off the step into the pit: %s" % str(tr2["errors"]))
	var ok := m.trace_segment(Vector2(-8, 0), Vector2(9, 0), "west")
	assert_eq(ok["errors"], [], "straight across west, the step, the bridge and the east walkway")
	assert_eq(ok["sectors"], ["west", "step", "bridge", "east"])
	var no_hold := StoryRailCheck.check_rail(m, "t", "w0", {"good": [{"to": "s1", "choice": true}], "bad": [{"to": "w0"}]})
	assert_true(" ".join(PackedStringArray(no_hold)).contains("choice viewpoint"), "a choice viewpoint with no hold is an error: %s" % str(no_hold))
	var held := StoryRailCheck.check_rail(m, "t", "w0", {"good": [{"to": "s1", "choice": true, "hold_bars": RunRail.CHOICE_HOLD_BARS}], "bad": [{"to": "e1", "via": ["s1", "b1"]}]})
	assert_eq(held, [], "held for the whole window, and the bad leg back along its via is clean")
	assert_true(" ".join(PackedStringArray(RunRail.validate("t", {"good": [{"to": "s1", "choice": true}], "bad": [{"to": "w0"}], "glances": [{}], "strolls": [{}]}))).contains("choice"), "RunRail.validate says so too")


func test_the_rail_emits_via_and_hold_and_a_choice_window_is_still() -> void:
	var r := RunRail.new()
	r.setup("t", {"waypoint": "w0", "rail": {"good": [{"to": "e1", "via": ["s1", "b1"], "bars": 3, "hold_bars": 1}, {"to": "h1", "style": "climb", "choice": true, "hold_bars": 3}],
		"bad": [{"to": "c1", "via": ["s1"]}], "glances": [{"by": 10, "bars": 2}], "strolls": [{"fwd": 1, "bars": 2}]}}, BPM)
	var acts := r.step(true, 10.0, [])
	var mv: Dictionary = acts.filter(func(a: Dictionary) -> bool: return a["action"] == "player_move")[0]
	assert_eq(mv["args"]["via"], ["s1", "b1"], "the leg's via goes to the player")
	assert_eq(float(mv["args"]["hold_bars"]), 1.0, "and its hold")
	assert_near(r.busy_until, 10.0 + 4.0 * 2.0, 1e-6, "busy through the move and the hold (no stroll in it)")
	var win := r.step(true, 30.0, [], 31.0)  # the decision before a choice window that starts a second later
	var mv2: Dictionary = win.filter(func(a: Dictionary) -> bool: return a["action"] == "player_move")[0]
	assert_true(float(mv2["t0"]) + float(mv2["args"]["bars"]) * r.bar_s() <= 31.0 + 1e-6, "the walk to a choice viewpoint lands by the window")
	assert_true(r.at_choice(), "standing on a choice viewpoint")
	var amb := r.ambient(40.0, 1, 3, [])
	assert_true(amb.filter(func(a: Dictionary) -> bool: return a["action"] in ["player_look", "player_walk"]).is_empty(), "no glance and no stroll on a choice viewpoint")
