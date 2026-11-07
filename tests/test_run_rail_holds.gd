extends TestCase
## Holds (CONTRACTS.md 3, ruling 35a; hook H3) on the one rail hold implementation (docs/story/HEIGHTS_AND_PATHS.md: RunRail._move_to's hold_bars, _in_hold,
## at_choice, RunJourney's player_hold): a route leg moves, then holds still for its hold_bars (the move carries them; no player_move, no glance, no stroll and no
## rail step inside the route's holds); a choice viewpoint holds still through the window (a player_hold, no glance, no stroll, no face turn).

const BEAT := 60.0 / 174.0


func _journey() -> Dictionary:
	var d := RunData.load_default()
	var e := RunEngine.new(d)
	e.begin("warehouse")
	var j := RunJourney.new(d)
	j.look_heralds = false
	j.on_event({"kind": "phase_start", "node": "warehouse", "t": 0.0, "phase": 1}, e)
	return {"d": d, "e": e, "j": j}


func _camera(list: Array) -> Array:
	return list.filter(func(a: Dictionary) -> bool: return str(a["action"]) in ["player_move", "player_walk", "player_look"])


func test_route_legs_move_then_hold_and_nothing_moves_the_camera_inside_a_hold() -> void:
	var w := _journey()
	var e: RunEngine = w["e"]
	var j: RunJourney = w["j"]
	var r: Dictionary = ContractShapes.load_fixture("route_space_to_stage.json")
	var bar := j.rail.bar_s()
	var t0 := e.t_of(12.75)
	var quiet: Array = []  # (the chart's density must not shorten a leg here: compare with the contract's own times)
	var acts := j.hotspot_actions(ContractShapes.route_as_cinematic(r), t0, e, Callable(), true)
	var moves := acts.filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_move")
	var want := ContractShapes.route_actions(r, t0, bar)
	assert_eq(moves.size(), 3, "one move per leg")
	var holds: Array = []  # [move end, hold end]
	for i in moves.size():
		var bars := float(moves[i]["args"]["bars"])
		assert_eq(moves[i]["args"]["to"], want[i]["args"]["to"])
		if bars == float(want[i]["args"]["bars"]):
			assert_near(float(moves[i]["t0"]), float(want[i]["t0"]), 1e-6, "leg %d starts after the previous leg's move and hold (route_actions)" % i)
		assert_near(float(moves[i]["args"].get("hold_bars", 0.0)), float(r["legs"][i]["hold_bars"]), 1e-9, "leg %d's move carries its hold (StoryPlayer stands still)" % i)
		var m_end := float(moves[i]["t0"]) + bars * bar
		holds.append([m_end, m_end + float(r["legs"][i]["hold_bars"]) * bar])
	assert_near(j.rail.busy_until, float(holds[2][1]), 1e-6, "the rail is held until the last leg's hold is over")
	assert_near(j.rail.hold_from, float(holds[0][0]), 1e-6, "from the first leg's hold on")
	# what else would move the camera meanwhile: the ambient glance and stroll of every block, and the rail's steps at the decisions
	var other: Array = []
	for b in 4:
		other.append_array(j.rail.ambient(e.t_of(float(b) * 16.0), 1, b, quiet))
		var t_dec := e.t_of(float(b) * 16.0 + 12.75)
		if t_dec > j.rail.hold_from and t_dec < j.rail.busy_until:
			var st := j.rail.step(true, t_dec, quiet)
			assert_eq(st, [], "no rail step inside the hold (block %d)" % b)
			assert_eq(str(j.rail.visited[-1]["kind"]), "hold")
	for a: Dictionary in _camera(acts + other):
		for h: Array in holds:
			assert_false(float(a["t0"]) > float(h[0]) + 1e-6 and float(a["t0"]) < float(h[1]) - 1e-6, "%s at %.3f is inside the hold %.3f..%.3f" % [a["action"], float(a["t0"]), h[0], h[1]])
	assert_true(not other.is_empty(), "the blocks after the hold have their glance again")
	# after the hold the rail steps again
	var later := float(holds[2][1]) + 1.0
	assert_false(j.rail._in_hold(later, 0.0))
	assert_true(j.rail.step(true, later, quiet).size() > 0, "a pass after the hold steps the rail")


func test_a_choice_viewpoint_holds_still_through_the_window() -> void:
	var w := _journey()
	var e: RunEngine = w["e"]
	var j: RunJourney = w["j"]
	var rail := j.rail
	var quiet: Array = []
	# not a choice viewpoint: the window block has its (clamped) glance as before
	rail.pos = rail.good.size()
	var before := rail.ambient(e.t_of(48.0), 1, 3, quiet)
	assert_true(before.any(func(a: Dictionary) -> bool: return str(a["action"]) == "player_look"), "as today: a glance in the window block")
	(rail.good[rail.good.size() - 1] as Dictionary)["choice"] = true
	assert_true(rail.at_choice())
	assert_eq(rail.ambient(e.t_of(48.0), 1, 3, quiet), [], "at a choice viewpoint the window block has no glance and no stroll")
	assert_true(rail.ambient(e.t_of(16.0), 1, 1, quiet).size() > 0, "the blocks before the window keep theirs")
	var pts := [[0.0, -5.0, true, 1.0], [2.0, -5.0, false, 1.0]]
	j.face_fn = func(_n: String, _p: String) -> Array: return pts
	# standing there already when block 2 is decided: the window is held still, nothing turns or strolls
	var out := j.on_event({"kind": "block_result", "block": 2, "passed": true, "t": e.t_of(44.75), "phase": 1, "node": "warehouse"}, e)
	var hold := out.filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_hold")
	assert_eq(hold.size(), 1, "a player_hold for the window")
	assert_near(float(hold[0]["t0"]), e.t_of(RunJourney.FACE_TURN_BEAT), 1e-9, "from beat 49")
	assert_near(float(hold[0]["t0"]) + float(hold[0]["args"]["bars"]) * rail.bar_s(), e.t_of(RunJourney.FACE_RELEASE_BEAT), 1e-6, "to the commit (60.5)")
	assert_eq(_camera(out), [], "no move, no face turn, no glance, no stroll for the window")
	# walking there at block 2: the walk lands before the window opens, then the hold
	rail.pos = rail.good.size() - 1
	var out2 := j.on_event({"kind": "block_result", "block": 2, "passed": true, "t": e.t_of(44.75), "phase": 1, "node": "warehouse"}, e)
	var mv := out2.filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_move")
	assert_eq(mv.size(), 1, "the rail walks to the viewpoint")
	var arrive := float(mv[0]["t0"]) + float(mv[0]["args"]["bars"]) * rail.bar_s()
	assert_true(arrive <= e.t_of(RunJourney.FACE_TURN_BEAT) + 1e-6, "and is there when the window opens (%.3f <= %.3f)" % [arrive, e.t_of(RunJourney.FACE_TURN_BEAT)])
	assert_eq(out2.filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_hold").size(), 1, "then holds still")
	assert_eq(out2.filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_walk" or str(a["action"]) == "player_look"), [], "no face turn, no glance, no stroll")


func test_rail_data_names_choice_viewpoints() -> void:
	var r := RunRail.new()
	r.setup("x", {"waypoint": "home", "rail": {"good": [{"to": "a", "choice": true, "hold_bars": 3.0}], "bad": [{"to": "b"}], "glances": [{"by": 10.0}], "strolls": [{"fwd": 1.0}]}}, 174.0)
	assert_false(r.at_choice(), "home is no choice viewpoint")
	r.pos = 1
	assert_true(r.at_choice(), "a place with choice: true is")
	r.hold_from = 1.0
	r.busy_until = 5.0
	assert_true(r._in_hold(2.0, 0.0))
	r.reset()
	assert_false(r._in_hold(2.0, 0.0), "a restart drops the hold")
