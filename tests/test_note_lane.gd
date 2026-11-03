extends TestCase
## NoteLane (falling notes): the shape geometry (a note lands on its pad at the hit time, a hold is a bar whose bottom
## lands at the press time) and which notes are listed at a song time, with their judge state.

const TRAVEL_S := 1.2
const PAD := Rect2(100.0, 500.0, 80.0, 80.0)
const TRAVEL_PX := 580.0  # the pad's bottom edge: distance from the screen top to the pad's bottom


func _cue(pad: int, time: float, hold_s: float = 0.0) -> Dictionary:
	return {"time": time, "end_time": time + hold_s, "type": "hold" if hold_s > 0.0 else "tap", "pad": pad, "family": "kick"}


func _pads() -> Dictionary:
	return {1: Rect2(100.0, 500.0, 80.0, 80.0), 2: Rect2(200.0, 500.0, 80.0, 80.0),
		3: Rect2(600.0, 500.0, 80.0, 80.0), 4: Rect2(700.0, 500.0, 80.0, 80.0)}


func _lane(cues: Array) -> NoteLane:
	var level := Level.new()
	level.notes = cues
	var lane := NoteLane.new()
	lane.level = level
	lane.setup(level, null, null)
	lane.travel_s = TRAVEL_S
	return lane


func _indexes(list: Array) -> Array:
	var out := []
	for v in list:
		out.append(int(v["index"]))
	out.sort()
	return out


func test_note_lands_on_its_pad_at_the_hit_time() -> void:
	assert_eq(NoteLane.shape_rect(PAD, 0.0, 0.0, TRAVEL_S, TRAVEL_PX), PAD)
	assert_eq(NoteLane.shape_rect(PAD, 0.0, 0.0, TRAVEL_S, TRAVEL_PX).size, PAD.size, "size never changes for a tap")


func test_note_enters_at_the_screen_top() -> void:
	var r := NoteLane.shape_rect(PAD, TRAVEL_S, 0.0, TRAVEL_S, TRAVEL_PX)
	assert_true(r.end.y <= 0.0 + 1e-3, "the whole note is above the screen at dt = travel_s")
	assert_near(r.end.y, 0.0, 1e-3)
	assert_near(r.position.x, PAD.position.x, 1e-9, "it falls straight down")


func test_fall_is_linear_in_time() -> void:
	var y0 := NoteLane.shape_rect(PAD, 0.0, 0.0, TRAVEL_S, TRAVEL_PX).position.y
	var y1 := NoteLane.shape_rect(PAD, 0.3, 0.0, TRAVEL_S, TRAVEL_PX).position.y
	var y2 := NoteLane.shape_rect(PAD, 0.6, 0.0, TRAVEL_S, TRAVEL_PX).position.y
	assert_near(y0 - y1, y1 - y2, 1e-3, "equal steps in time are equal steps in y")
	assert_near(y0 - y1, 0.3 / TRAVEL_S * TRAVEL_PX, 1e-3)
	var after := NoteLane.shape_rect(PAD, -0.1, 0.0, TRAVEL_S, TRAVEL_PX).position.y
	assert_near(after - y0, 0.1 / TRAVEL_S * TRAVEL_PX, 1e-3, "after the hit time it keeps falling at the same speed")


func test_hold_bar_ends_where_a_tap_would_and_is_longer_by_its_length() -> void:
	var hold_s := 0.5
	for dt in [0.0, 0.4, 1.0, -0.2]:
		var tap := NoteLane.shape_rect(PAD, dt, 0.0, TRAVEL_S, TRAVEL_PX)
		var bar := NoteLane.shape_rect(PAD, dt, hold_s, TRAVEL_S, TRAVEL_PX)
		assert_near(bar.end.y, tap.end.y, 1e-3, "the bottom edge is where the tap would be (dt %.1f)" % dt)
		assert_near(bar.size.y, PAD.size.y + hold_s / TRAVEL_S * TRAVEL_PX, 1e-3, "height = pad + hold length")
		assert_near(bar.position.x, PAD.position.x, 1e-9)
		assert_near(bar.size.x, PAD.size.x, 1e-9)


func test_visible_notes_window_and_indexes() -> void:
	var lane := _lane([_cue(1, 2.0), _cue(2, 3.0), _cue(3, 3.5), _cue(4, 5.0)])
	var v := lane.visible_notes(2.0, _pads())  # at the first cue's hit time
	assert_eq(_indexes(v), [0, 1], "cue 1 is on its pad, cue 2 is 1.0 s away (inside travel_s 1.2), cue 3 at 1.5 s is not")
	assert_eq(v[0]["state"], "pending")
	assert_eq(v[0]["rect"], _pads()[1], "at dt 0 the note is the pad")
	assert_eq(int(v[0]["pad"]), 1)
	assert_near(float(v[1]["dt"]), 1.0, 1e-9)
	assert_eq(_indexes(lane.visible_notes(2.0 - TRAVEL_S - 0.01, _pads())), [], "nothing before travel_s")
	assert_eq(_indexes(lane.visible_notes(0.9, _pads())), [0], "a note appears when dt < travel_s")
	assert_eq(_indexes(lane.visible_notes(2.3, _pads())), [1], "the first cue is gone after the window; cue 3 is 1.2 s away, not yet inside")
	assert_eq(lane.visible_notes(9.0, _pads()), [], "everything is over")
	assert_eq(_indexes(lane.visible_notes(2.0, _pads())), [0, 1], "going back in time rescans from the start")
	lane.free()


func test_hit_notes_vanish_at_the_hit_time_and_misses_fall_on() -> void:
	var lane := _lane([_cue(1, 2.0), _cue(2, 2.0), _cue(3, 2.0), _cue(4, 4.0)])
	var states := {0: "hit", 1: "miss", 2: "pending", 3: "pending"}
	lane.state_fn = func(i: int) -> String: return states[i]
	assert_eq(_indexes(lane.visible_notes(1.95, _pads())), [0, 1, 2], "a hit note still draws before its time")
	var v := lane.visible_notes(2.05, _pads())
	assert_eq(_indexes(v), [1, 2], "the hit one is gone once dt < 0; the miss and the pending one are listed")
	for e in v:
		assert_eq(e["state"], states[int(e["index"])])
	assert_eq(_indexes(lane.visible_notes(2.24, _pads())), [1, 2], "a miss is listed until 0.25 s after its time")
	assert_eq(_indexes(lane.visible_notes(2.26, _pads())), [], "and then gone")
	var rect: Rect2 = lane.visible_notes(2.1, _pads())[0]["rect"]
	assert_near(rect.position.y, _pads()[2].position.y + 0.1 / TRAVEL_S * 580.0, 1e-3, "a missed note keeps falling")
	lane.free()


func test_hold_stays_listed_until_its_end_and_a_hit_hold_is_gone_early() -> void:
	var lane := _lane([_cue(1, 2.0, 1.0), _cue(2, 2.0, 1.0)])
	var states := {0: "pending", 1: "hit"}
	lane.state_fn = func(i: int) -> String: return states[i]
	var v := lane.visible_notes(2.8, _pads())
	assert_eq(_indexes(v), [0], "a held (pending) bar passes through the pad; a completed one is gone")
	assert_true(v[0]["hold"])
	assert_near(float(v[0]["end_dt"]), 0.2, 1e-9)
	assert_eq(_indexes(lane.visible_notes(3.2, _pads())), [0], "visible until the end plus 0.25 s")
	assert_eq(_indexes(lane.visible_notes(3.3, _pads())), [])
	assert_near((v[0]["rect"] as Rect2).size.y, 80.0 + 1.0 / TRAVEL_S * 580.0, 1e-3)
	lane.free()


func test_duel_notes_without_a_state_function_are_pending_then_gone() -> void:
	var lane := _lane([{"time": 2.0, "end_time": 2.0, "type": "tap", "button": 3, "lane": "snare", "tick": 0}])
	assert_eq(lane.visible_notes(1.5, _pads())[0]["state"], "pending")
	assert_eq(_indexes(lane.visible_notes(2.1, _pads())), [0], "still pending inside the accept window")
	assert_eq(_indexes(lane.visible_notes(2.15, _pads())), [], "gone after it")
	lane.free()
