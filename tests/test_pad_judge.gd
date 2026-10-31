extends TestCase
## PadJudge (missions, PRD section 15): nearest-cue matching inside the accept window, grades, strays, one cue per
## press, held pads, hold coverage, pause and deterministic resolution times.


## A cue as the mission loader builds it. hold_s > 0 makes a hold ending hold_s after its onset.
func _cue(pad: int, time: float, hold_s: float = 0.0, seq: int = 0) -> Dictionary:
	var tick := int(round(time * 2784.0))
	var dur := int(round(hold_s * 2784.0))
	return {"id": "c%d_%d" % [pad, tick], "tick": tick, "time": time, "end_tick": tick + dur, "end_time": time + hold_s,
		"type": "hold" if hold_s > 0.0 else "tap", "duration_ticks": dur, "pad": pad, "family": "kick", "seq": seq}


func _judge(cues: Array, sequences: Array = []) -> PadJudge:
	var j := PadJudge.new()
	j.setup(cues, sequences)
	return j


func test_windows_come_from_the_rules_file() -> void:
	var j := _judge([])
	assert_near(j.perfect_s, 0.045, 1e-9)
	assert_near(j.great_s, 0.090, 1e-9)
	assert_near(j.accept_s, 0.140, 1e-9)
	assert_near(j.complete_s, 0.15, 1e-9)


func test_grades_at_45_90_and_140_ms_either_side() -> void:
	var cues := []
	for k in 8:
		cues.append(_cue(1, 1.0 + float(k)))
	var j := _judge(cues)
	var offsets := [0.044, -0.044, 0.046, -0.089, 0.091, -0.139, 0.0, -0.141]
	var expect := ["perfect", "perfect", "great", "great", "ok", "ok", "perfect", "stray"]
	for k in 8:
		var r := j.press(1, 1.0 + float(k) + offsets[k])
		assert_eq(r["kind"], expect[k], "press %+.3f s from the onset" % offsets[k])
		if r["kind"] != "stray":
			assert_near(float(r["delta_ms"]), offsets[k] * 1000.0, 0.01, "delta in ms")
			assert_eq(int(r["index"]), k)
	assert_eq([j.perfect, j.great, j.ok, j.strays], [3, 2, 2, 1])
	j.update(9.5)
	assert_eq(j.misses, 1, "the cue the stray could not reach misses")
	assert_near(j.accuracy(), 7.0 / 8.0, 1e-6)


func test_press_takes_the_nearest_unresolved_cue_of_its_pad() -> void:
	var j := _judge([_cue(1, 1.0), _cue(1, 1.2), _cue(4, 1.1)])
	var r := j.press(1, 1.12)  # 120 ms after cue 0, 80 ms before cue 1
	assert_eq(int(r["index"]), 1, "nearest wins over the earlier cue")
	assert_eq(r["kind"], "great")
	assert_false(j.is_resolved(2), "a pad-1 press never touches pad 4")
	j.update(1.15)
	assert_true(j.is_resolved(0))
	assert_eq(j.credit[0], 0.0, "the skipped cue misses")


func test_stray_is_counted_and_attributed_to_its_sequence() -> void:
	var seqs := [{"index": 0, "start_time": 0.0, "end_time": 2.0}, {"index": 1, "start_time": 2.0, "end_time": 4.0}]
	var j := _judge([_cue(1, 1.0, 0.0, 0), _cue(1, 3.0, 0.0, 1)], seqs)
	assert_eq(j.press(1, 0.5)["kind"], "stray", "nothing in reach")
	assert_eq(j.press(2, 1.0)["kind"], "stray", "a pad with no cue at all")
	var r := j.press(3, 3.5)
	assert_eq(r["kind"], "stray")
	assert_eq(int(r["seq"]), 1)
	assert_eq(j.strays, 3)
	assert_eq(j.strays_by_seq, {0: 2, 1: 1})
	assert_eq(j.press(9, 1.0)["kind"], "ignored", "an unknown pad is no input")
	assert_eq(j.strays, 3)
	assert_eq(j.combo, 0, "a stray breaks the combo")


func test_one_press_resolves_at_most_one_cue() -> void:
	var j := _judge([_cue(1, 1.0), _cue(1, 1.172)])
	var r := j.press(1, 1.086)  # inside the accept window of both
	assert_true(r.has("index"))
	var resolved := int(j.is_resolved(0)) + int(j.is_resolved(1))
	assert_eq(resolved, 1, "one press, one cue")
	assert_eq(j.accepted(), 1)
	j.update(1.4)
	assert_eq(j.accepted(), 1)
	assert_eq(j.misses, 1, "the other cue still needs its own press")
	var k := _judge([_cue(1, 1.0), _cue(1, 1.172)])
	k.press(1, 1.08)  # nearer the first cue
	k.release(1, 1.1)
	assert_eq(k.press(1, 1.17)["kind"], "perfect", "a second press takes the second cue")
	assert_eq(k.accepted(), 2)


func test_second_finger_on_a_held_pad_is_ignored() -> void:
	var j := _judge([_cue(2, 1.0, 1.0)])
	assert_eq(j.press(2, 1.0, 1)["kind"], "hold_start")
	assert_true(j.is_holding(2))
	assert_eq(j.press(2, 1.3, 2)["kind"], "ignored")
	assert_eq(j.strays, 0, "the second finger is not a stray either")
	assert_eq(j.release(2, 1.4, 2)["kind"], "ignored", "lifting the second finger does not end the hold")
	assert_true(j.is_holding(2))
	var r := j.release(2, 1.95, 1)
	assert_eq(r["kind"], "hold_complete")
	assert_eq(j.credit[0], 1.0)


func test_re_press_at_a_hold_tail_completes_it_first() -> void:
	var j := _judge([_cue(2, 1.0, 0.8), _cue(2, 1.82)])
	j.press(2, 1.0, 1)
	var r := j.press(2, 1.72, 2)  # 80 ms before the tail, without lifting the first finger
	assert_true(j.is_resolved(0))
	assert_eq(j.credit[0], 1.0, "inside the tolerance the hold is complete")
	assert_near(j.resolved_at[0], 1.72, 1e-9)
	assert_eq(j.holds_complete, 1)
	assert_eq(int(r["index"]), 1, "and the same press takes the next cue")
	assert_eq(r["kind"], "ok")


func test_held_pads_never_act_as_repeated_taps() -> void:
	var j := _judge([_cue(1, 1.0), _cue(1, 1.3), _cue(1, 1.6)])
	j.press(1, 1.0, 1)  # pressed and never lifted
	assert_false(j.is_holding(1), "a tap leaves nothing active")
	j.update(2.0)
	assert_eq(j.accepted(), 1)
	assert_eq(j.misses, 2, "keeping a finger down earns nothing more")
	var h := _judge([_cue(2, 1.0, 0.5), _cue(2, 1.7)])
	h.press(2, 1.0, 1)
	h.update(2.0)  # held through the tail and past the next cue
	assert_eq(h.credit[0], 1.0)
	assert_eq(h.credit[1], 0.0, "the held finger does not tap the following cue")


func test_hold_coverage_complete_partial_and_still_held() -> void:
	var cases := [[1.86, 1.0, "hold_complete"], [1.84, 0.84, "hold_partial"], [1.5, 0.5, "hold_partial"], [1.1, 0.1, "hold_partial"]]
	for c in cases:
		var j := _judge([_cue(3, 1.0, 1.0)])
		j.press(3, 1.0)
		var r := j.release(3, float(c[0]))
		assert_eq(r["kind"], c[2], "released at %.2f" % c[0])
		assert_near(j.credit[0], float(c[1]), 1e-4, "coverage when released at %.2f" % c[0])
		assert_near(j.resolved_at[0], float(c[0]), 1e-9)
	var late := _judge([_cue(3, 1.0, 1.0)])
	late.press(3, 1.1)
	late.release(3, 1.5)
	assert_near(late.credit[0], 0.5, 1e-4, "coverage is measured from the onset")
	var held := _judge([_cue(3, 1.0, 1.0)])
	held.press(3, 0.95)
	held.update(1.99)
	assert_false(held.is_resolved(0))
	held.update(2.3)
	assert_eq(held.credit[0], 1.0, "still held at the tail: complete")
	assert_near(held.resolved_at[0], 2.0, 1e-9, "resolved at the tail, not at the frame")
	assert_eq(held.release(3, 2.4)["kind"], "none")


func test_early_release_never_makes_a_later_cue_unavailable() -> void:
	var j := _judge([_cue(2, 1.0, 1.0), _cue(2, 2.2), _cue(2, 2.6, 0.6)])
	j.press(2, 1.0)
	j.release(2, 1.3)
	assert_near(j.credit[0], 0.3, 1e-4)
	assert_eq(j.press(2, 2.21)["kind"], "perfect", "the next tap is still there")
	j.release(2, 2.25)
	assert_eq(j.press(2, 2.6)["kind"], "hold_start", "and so is the next hold")
	j.release(2, 3.2)
	assert_eq(j.credit[2], 1.0)
	assert_eq(j.misses, 0)
	assert_eq([j.holds_complete, j.holds_partial], [1, 1])


func test_pause_interrupt_ends_a_hold_with_its_coverage_so_far() -> void:
	var j := _judge([_cue(2, 1.0, 1.0), _cue(4, 1.2, 1.0)])
	j.press(2, 1.0, 1)
	j.press(4, 1.2, 2)
	j.pause_interrupt(1.4)
	assert_false(j.is_holding(2))
	assert_false(j.is_holding(4))
	assert_near(j.credit[0], 0.4, 1e-4)
	assert_near(j.credit[1], 0.2, 1e-4)
	assert_near(j.resolved_at[0], 1.4, 1e-9)
	assert_eq(j.holds_partial, 2)
	assert_eq(j.release(2, 1.5, 1)["kind"], "none", "the finger lifted after the pause changes nothing")
	j.update(3.0)
	assert_near(j.credit[0], 0.4, 1e-4, "and the tail passing later does not complete it")


func test_misses_resolve_at_onset_plus_accept() -> void:
	var j := _judge([_cue(1, 1.0), _cue(2, 1.5, 0.5)])
	j.update(1.139)
	assert_false(j.is_resolved(0), "still inside the window")
	j.update(1.141)
	assert_true(j.is_resolved(0))
	assert_near(j.resolved_at[0], 1.14, 1e-9)
	j.update(5.0)
	assert_near(j.resolved_at[1], 1.64, 1e-9, "an unstarted hold misses the same way")
	assert_eq(j.credit[1], 0.0)
	var miss_events := 0
	for ev in j.drain_events():
		if ev["kind"] == "miss":
			miss_events += 1
			assert_near(float(ev["time"]), float(j.notes[int(ev["index"])]["time"]) + 0.14, 1e-9)
	assert_eq(miss_events, 2)


func test_resolved_at_does_not_depend_on_the_update_rate() -> void:
	var cues := [_cue(1, 0.5), _cue(4, 0.8), _cue(2, 1.0, 0.9), _cue(1, 1.4), _cue(4, 2.2), _cue(3, 2.5, 0.7), _cue(1, 3.0)]
	var inputs := [[1, 0.52, true], [1, 0.6, false], [2, 1.03, true], [1, 1.37, true], [1, 1.45, false], [2, 1.6, false],
		[3, 2.48, true], [4, 2.9, true], [4, 2.95, false]]  # cues 1, 4 and 6 missed, a stray on pad 4, hold 2 released early, hold 5 held past its tail
	var results := []
	for step in [1.0 / 60.0, 1.0 / 30.0, 0.25, 10.0]:
		var j := _judge(cues)
		var t := 0.0
		var k := 0
		while t < 4.0:
			t += step
			while k < inputs.size() and float(inputs[k][1]) <= t:
				if inputs[k][2]:
					j.press(int(inputs[k][0]), float(inputs[k][1]))
				else:
					j.release(int(inputs[k][0]), float(inputs[k][1]))
				k += 1
			j.update(t)
		results.append([j.resolved_at, j.credit, j.misses, j.holds_complete, j.holds_partial])
	for i in range(1, results.size()):
		assert_eq(results[i], results[0], "update pattern %d resolves like 60 fps" % i)
	assert_near(results[0][0][1], 0.94, 1e-9)
	assert_near(results[0][0][5], 3.2, 1e-9)
