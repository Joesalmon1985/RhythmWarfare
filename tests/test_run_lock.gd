extends TestCase
## The route lock: block 0 of the next phase is charted from the selected route at the last block's decision, so a route with another chart pack can no longer be chosen
## after it (a route with the same pack still can), and a pick made before the lock gets its own world's cues.


func _data_with_two_charts() -> RunData:
	var d := RunData.load_default()
	d.nodes["underworld"]["chart"] = "lv1_warehouse_v1"  # a sibling that charts another pack than the mothership
	return d


func _play(e: RunEngine, until_t: float, picks: Dictionary) -> void:
	var t := 0.0
	var pressed := {}
	var released := {}
	var done := {}
	while t < until_t and not e.over:
		for at in picks:
			if t >= float(at) and not done.has(at):
				done[at] = true
				e.choose(str(picks[at]))
		e.update(t)
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			if not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]))
			if pressed.has(i) and n["type"] == "hold" and not released.has(i) and float(n["end_time"]) <= t:
				released[i] = true
				e.release(int(n["pad"]), float(n["end_time"]))
		t += 1.0 / 60.0


func _block0(e: RunEngine, phase: int) -> Array:
	var rows: Array = []
	for n in e.level.notes:
		if int(n["phase"]) == phase and int(n["block"]) == 0:
			rows.append([int(n["tick"]) - (phase - 1) * 64 * 960, n["pad"], n["duration_ticks"], n["family"]])
	return rows


func test_a_pick_before_the_lock_gets_its_own_worlds_first_block() -> void:
	var d := _data_with_two_charts()
	var e := RunEngine.new(d)
	e.begin("warehouse")
	_play(e, 70.0 * e.beat_s, {55.0 * e.beat_s: "underworld"})
	assert_eq(e.node_id, "underworld")
	var ref := RunEngine.new(_data_with_two_charts())
	ref.begin("underworld")
	_play(ref, 1.0, {})
	var want := _block0(ref, 1)
	assert_true(want.size() > 3)
	assert_eq(_block0(e, 2), want, "the chosen world's recording is charted, not the default route's")
	var e2 := RunEngine.new(_data_with_two_charts())
	e2.begin("warehouse")
	_play(e2, 70.0 * e2.beat_s, {})
	assert_eq(e2.node_id, "mothership")
	assert_true(_block0(e2, 2) != want, "the default route charts the default world's pack")


func test_after_the_lock_only_routes_with_the_same_chart_can_be_chosen() -> void:
	var e := RunEngine.new(_data_with_two_charts())
	e.begin("warehouse")
	_play(e, 59.0 * e.beat_s, {})
	assert_false(e.route_locked, "free until the last decision")
	assert_true(e.route_allowed("underworld"))
	_play(e, 61.0 * e.beat_s, {})
	assert_true(e.route_locked)
	assert_false(e.route_allowed("underworld"), "another chart pack is refused")
	assert_false(e.choose("underworld"))
	assert_false(e.choose_dir("right"))
	assert_eq(e.selected_route(), "mothership", "the default stays")
	assert_true(e.choose("mothership"), "the same pack is still fine")
	var same := RunEngine.new(RunData.load_default())  # when both routes play one pack nothing is ever refused
	same.begin("warehouse")
	_play(same, 61.0 * same.beat_s, {})
	assert_true(same.route_locked)
	assert_true(same.choose("underworld"))
