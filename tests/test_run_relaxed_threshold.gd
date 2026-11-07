extends TestCase
## Contract 1's engine hooks: a relaxed node (the bedsit, H1.7) never drains energy and never forces a departure; a world exit by a threshold (H1.6) walks to the
## threshold spot first and the world transition follows on the boundary.


func _drive(e: RunEngine, until_phase: int, plays: bool, per_frame: Callable = Callable()) -> Array:
	var events: Array = []
	var t := 0.0
	var pressed := {}
	while e.phase_n < until_phase and not e.over and t < 600.0:
		if per_frame.is_valid():
			per_frame.call(e, t)
		events.append_array(e.update(t))
		if plays:
			for i in e.level.notes.size():
				var n: Dictionary = e.level.notes[i]
				if not pressed.has(i) and float(n["time"]) <= t:
					pressed[i] = true
					e.press(int(n["pad"]), float(n["time"]))
					if n["type"] == "hold":
						e.release(int(n["pad"]), float(n["end_time"]))
		t += 1.0 / 60.0
	return events


func _of(events: Array, kind: String) -> Array:
	return events.filter(func(ev: Dictionary) -> bool: return str(ev["kind"]) == kind)


func test_a_relaxed_node_never_drains_energy_and_never_forces_a_departure() -> void:
	var d := RunData.load_default()
	d.nodes["warehouse"]["relaxed"] = true
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.begin("warehouse")
	assert_true(e.relaxed())
	var ev := _drive(e, 5, false)  # nothing played for four whole phases: 16 failed blocks (seven end an ordinary run)
	assert_false(e.over, "the run is not over")
	assert_eq(_of(ev, "depleted").size(), 0)
	var results := _of(ev, "block_result")
	assert_true(results.size() >= 16)
	assert_true(results.all(func(b: Dictionary) -> bool: return not bool(b["passed"])), "every block failed")
	assert_true(results.all(func(b: Dictionary) -> bool: return float(b["energy"]) >= 60.0 - 1e-9), "and none cost energy")
	assert_true(_of(ev, "phase_start").all(func(p: Dictionary) -> bool: return str(p["node"]) == "warehouse"), "no departure by default: the scene stays")
	assert_true(_of(ev, "route_commit").all(func(c: Dictionary) -> bool: return str(c["to"]) == "warehouse"))
	# a choice still leaves
	var e2 := RunEngine.new(d)
	e2.begin("warehouse")
	var ev2 := _drive(e2, 3, true, func(en: RunEngine, t: float) -> void:
		if en.window_open and en.choice == "":
			en.choose("warehouse.bar"))
	var nodes: Array = _of(ev2, "phase_start").map(func(p: Dictionary) -> String: return str(p["node"]))
	assert_eq(nodes.slice(0, 2), ["warehouse", "warehouse.bar"], "a chosen route is taken")
	assert_false(e2.relaxed(), "the next scene is an ordinary one")
	# an ordinary node is unchanged
	var d3 := RunData.load_default()
	var e3 := RunEngine.new(d3)
	e3.begin("warehouse")
	var ev3 := _drive(e3, 3, false)
	assert_true(float(_of(ev3, "block_result")[0]["energy"]) < 60.0, "elsewhere a failed block costs energy as ever")
	assert_eq(str(_of(ev3, "phase_start")[1]["node"]), "warehouse.bar", "and the default route is taken")


func test_a_world_exit_walks_to_the_threshold_then_transitions() -> void:
	var d := RunData.load_default()
	var e := RunEngine.new(d)
	e.begin("warehouse")
	var j := RunJourney.new(d)
	j.look_heralds = false
	j.on_event({"kind": "phase_start", "node": "warehouse", "t": 0.0, "phase": 1}, e)
	d.nodes["warehouse"]["thresholds"] = {"mothership": "wh_threshold"}
	assert_eq(j.threshold_of("warehouse", "mothership"), "wh_threshold")
	assert_eq(j.threshold_of("warehouse", "warehouse.bar"), "", "a route without a threshold: none")
	var t_walk := e.t_of(64.0 - RunPassage.DOOR_BEATS)
	var t_b := e.t_of(64.0)
	var walk := j.threshold_walk(t_walk, t_b, "wh_threshold", 2.0)
	assert_eq(walk.size(), 1)
	assert_eq(walk[0]["action"], "player_move")
	assert_eq(walk[0]["args"]["to"], "wh_threshold")
	var arrive := float(walk[0]["t0"]) + float(walk[0]["args"]["bars"]) * j.rail.bar_s()
	assert_true(arrive <= t_b + 1e-9, "at the threshold by the boundary (%.3f <= %.3f)" % [arrive, t_b])
	# the transition: the next world's scene starts on the boundary, after the walk
	var other := ""
	for id in d.nodes:
		if str(d.nodes[id]["world"]) != str(d.nodes["warehouse"]["world"]):
			other = str(id)
			break
	assert_true(other != "")
	var trans := j.on_event({"kind": "phase_start", "node": other, "t": t_b, "phase": 2}, e)
	var seq: Array = walk + trans
	assert_eq(str(seq[0]["action"]), "player_move")
	assert_eq(str(seq[0]["world"]), str(d.nodes["warehouse"]["map"]), "the walk is in the world being left")
	assert_true(trans.all(func(a: Dictionary) -> bool: return str(a["world"]) == str(d.nodes[other]["map"])), "then the new world's actions")
	assert_true(float(walk[0]["t0"]) < trans.map(func(a: Dictionary) -> float: return float(a["t0"])).min(), "the walk starts before anything of the new world")
	assert_eq(j.threshold_walk(t_b, t_b, "x"), [], "no time left: no walk")
