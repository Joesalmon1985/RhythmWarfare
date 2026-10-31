extends TestCase
## SequenceTracker (PRD section 15): resolution timing, pass threshold, exactly-once results, precision grades, strays,
## mashing, holds; and determinism of the whole mission (frame rate, pause, retry) through Match.

const HARNESS := "res://tools/autoplay.gd"
const SEQ_S := 2.5


## n sequences of 8 taps each: sequence s covers [s * 2.5, (s + 1) * 2.5), taps every 0.25 s alternating pads 1 and 4.
func _level(n: int) -> Level:
	var level := Level.new()
	level.schema_version = 3
	level.sequence_threshold = 0.6
	for s in n:
		var t0 := float(s) * SEQ_S
		level.sequences.append({"index": s, "start_time": t0, "end_time": t0 + SEQ_S, "start_tick": s * 6960, "end_tick": (s + 1) * 6960,
			"reward": "pillbox", "mode": "drums"})
		for k in 8:
			var t := t0 + 0.25 * float(k + 1)
			level.notes.append({"id": "c%d" % level.notes.size(), "tick": int(t * 2784.0), "time": t, "end_tick": int(t * 2784.0), "end_time": t,
				"type": "tap", "duration_ticks": 0, "pad": 1 if k % 2 == 0 else 4, "family": "kick" if k % 2 == 0 else "snare", "seq": s})
	return level


## Plays a level: offset_of(i) returns the press offset (s) of cue i, or null to skip it. strays: [[pad, time]].
## Updates at 60 fps and returns every tracker result in the order it appeared.
func _run(level: Level, offset_of: Callable, strays: Array = []) -> Array:
	var j := PadJudge.new()
	j.setup(level.notes, level.sequences)
	var tr := SequenceTracker.new()
	tr.setup(level, j)
	var inputs: Array = []
	for i in level.notes.size():
		var off: Variant = offset_of.call(i)
		if off != null:
			var n: Dictionary = level.notes[i]
			var at := float(n["time"]) + float(off)
			inputs.append([int(n["pad"]), at, float(n["end_time"]) + 0.02 if n["type"] == "hold" else at + 0.05])
	for s in strays:
		inputs.append([int(s[0]), float(s[1]), float(s[1]) + 0.05])
	inputs.sort_custom(func(a: Array, b: Array) -> bool: return a[1] < b[1])
	var ups: Array = []  # [pad, time]
	var out: Array = []
	var t := 0.0
	var k := 0
	var end := float(level.sequences.size()) * SEQ_S + 1.0
	while t < end:
		t += 1.0 / 60.0
		while true:
			var next_down := float(inputs[k][1]) if k < inputs.size() else INF
			var next_up := INF
			var u := -1
			for x in ups.size():
				if float(ups[x][1]) < next_up:
					next_up = float(ups[x][1])
					u = x
			if minf(next_down, next_up) > t:
				break
			if next_up <= next_down:
				j.release(int(ups[u][0]), next_up)
				ups.remove_at(u)
			else:
				j.press(int(inputs[k][0]), next_down)
				ups.append([int(inputs[k][0]), float(inputs[k][2])])
				k += 1
		j.update(t)
		out.append_array(tr.update())
		out.append_array(tr.update())  # a second call in the same frame returns nothing new
	return out


func test_sequence_resolves_only_when_its_last_cue_is_final_at_the_latest_resolution_time() -> void:
	var level := _level(1)
	var j := PadJudge.new()
	j.setup(level.notes, level.sequences)
	var tr := SequenceTracker.new()
	tr.setup(level, j)
	for i in 7:
		j.press(int(level.notes[i]["pad"]), float(level.notes[i]["time"]))
		assert_eq(tr.update(), [], "cue %d of 8: not yet" % i)
	j.update(2.0)
	assert_eq(tr.update(), [], "the last cue is due now: never before it is judged")
	j.update(2.139)
	assert_eq(tr.update(), [], "still inside its window")
	j.update(2.15)
	var got := tr.update()
	assert_eq(got.size(), 1)
	assert_near(float(got[0]["resolve_time"]), 2.14, 1e-9, "at the miss time of the last cue, not at the frame")
	assert_true(got[0]["passed"], "7 of 8")
	# a hold that ends after the last onset sets the resolution time
	var h := _level(1)
	h.notes[2]["type"] = "hold"
	h.notes[2]["end_time"] = 2.4
	h.notes[2]["pad"] = 2
	var r := _run(h, func(_i: int) -> Variant: return 0.0)
	assert_eq(r.size(), 1)
	assert_true(r[0]["passed"])
	assert_true(float(r[0]["resolve_time"]) > 2.0, "resolved after the hold's release, not at the last onset")


func test_pass_at_threshold_five_of_eight_passes_four_fails() -> void:
	var hits := [5, 4, 8]
	var r := _run(_level(3), func(i: int) -> Variant: return 0.0 if i % 8 < hits[i / 8] else null)
	assert_eq(r.size(), 3)
	assert_eq([r[0]["passed"], r[1]["passed"], r[2]["passed"]], [true, false, true])
	assert_near(float(r[0]["credit"]), 0.625, 1e-6)
	assert_near(float(r[1]["credit"]), 0.5, 1e-6)
	assert_eq(r[1]["grade"], "", "a failure has no grade")
	assert_eq(float(r[1]["delay_s"]), 0.0)
	assert_eq(r[2]["grade"], "sharp", "the sequence after a failure resolves normally")


func test_each_sequence_resolves_exactly_once_in_order() -> void:
	var r := _run(_level(4), func(i: int) -> Variant: return 0.0 if i % 3 != 0 else null)
	var order := []
	for x in r:
		order.append(int(x["index"]))
	assert_eq(order, [0, 1, 2, 3], "repeated updates return every sequence once")


func test_precision_grades_set_the_delay() -> void:
	var offsets := [0.0, 0.05, 0.1, -0.05]
	var r := _run(_level(4), func(i: int) -> Variant: return offsets[i / 8])
	var expect := [["sharp", 0.5], ["steady", 1.5], ["loose", 3.0], ["steady", 1.5]]
	for s in 4:
		assert_true(r[s]["passed"])
		assert_eq(r[s]["grade"], expect[s][0], "offset %.0f ms" % (offsets[s] * 1000.0))
		assert_near(float(r[s]["delay_s"]), float(expect[s][1]), 1e-9)
		assert_near(float(r[s]["mean_abs_ms"]), absf(offsets[s]) * 1000.0, 0.01)


func test_strays_push_the_grade_down_but_never_fail_an_accepted_sequence() -> void:
	var strays := [[3, 2.5 + 1.1], [3, 2.5 + 1.6]]
	for k in 30:
		strays.append([3, 5.0 + 0.3 + 0.055 * float(k)])  # all before the last cue (7.0) resolves the sequence
	var r := _run(_level(3), func(i: int) -> Variant: return 0.03 if i < 16 else 0.0, strays)
	assert_eq([r[0]["strays"], r[1]["strays"], r[2]["strays"]], [0, 2, 30])
	assert_eq(r[0]["grade"], "sharp", "30 ms")
	assert_eq(r[1]["grade"], "steady", "30 ms + 2 strays x 25 / 8")
	assert_true(r[2]["passed"], "every cue accepted: strays cannot fail it")
	assert_eq(r[2]["grade"], "loose", "0 ms + 30 strays x 25 / 8")


func test_mashing_never_earns_sharp_or_steady() -> void:
	var level: Level = LevelLoader.load_pack(TestCase.project_path("songs/m01_first_watch"))["level"]
	var m := Match.new()
	m.setup(level, null, false)
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var r: Dictionary = load(HARNESS).run_mission(m, level, "mash", rng)
	assert_eq(r["grades"]["sharp"], 0)
	assert_eq(r["grades"]["steady"], 0)
	assert_eq(int(r["grades"]["loose"]) + int(r["grades"]["failed"]), 8)
	assert_true(int(r["strays"]) > 100, "mashing is mostly strays")


func test_long_hold_sequences_earn_exactly_one_reward_like_tap_sequences() -> void:
	var level: Level = LevelLoader.load_pack(TestCase.project_path("songs/m03_hold_the_line"))["level"]
	var holds_in := {}
	for n in level.notes:
		if n["type"] == "hold":
			holds_in[int(n["seq"])] = int(holds_in.get(int(n["seq"]), 0)) + 1
	var m := Match.new()
	m.setup(level)
	var rng := RandomNumberGenerator.new()
	rng.seed = 3
	load(HARNESS).run_mission(m, level, "perfect", rng)
	var per_seq := {}
	for e in m.reward_log:
		per_seq[int(e["sequence"])] = int(per_seq.get(int(e["sequence"]), 0)) + 1
	var bass := 0
	for s in level.sequences:
		var idx := int(s["index"])
		if not m.tracker.results[idx].is_empty() and float(m.tracker.results[idx]["resolve_time"]) < m.outcome_time:
			assert_eq(per_seq.get(idx, 0), 1, "sequence %d (%s) logs one reward" % [idx, s["mode"]])
		if s["mode"] == "bass" and per_seq.get(idx, 0) == 1:
			bass += 1
			assert_true(int(holds_in.get(idx, 0)) > 0, "bass sequence %d is made of holds" % idx)
	assert_true(bass >= 2, "bass (hold) sequences were rewarded")
	for e in m.reward_log:
		if e["passed"]:
			assert_eq(e["result"], "scheduled")


# --- determinism ------------------------------------------------------------------------------------------------

## Feeds a planned input list through Match with the given frame pattern (seconds per frame, cycled) until `until`.
## pause_at >= 0 calls pause_interrupt at that song time (in input order).
func _drive(level: Level, plan: Array, pattern: Array, until: float, pause_at: float = -1.0) -> Match:
	var events := plan.duplicate()
	if pause_at >= 0.0:
		var at := events.size()
		for i in events.size():
			if float(events[i]["t"]) > pause_at:
				at = i
				break
		events.insert(at, {"t": pause_at, "pause": true})
	var m := Match.new()
	m.setup(level)
	var down := {}
	var t := -0.5
	var k := 0
	var f := 0
	while m.outcome.is_empty() and t < until:
		t += float(pattern[f % pattern.size()])
		f += 1
		while k < events.size() and float(events[k]["t"]) <= t:
			var e: Dictionary = events[k]
			k += 1
			if e.has("pause"):
				m.pause_interrupt(float(e["t"]))
			elif e["down"] and not down.get(e["pad"], false):
				down[e["pad"]] = true
				m.press(int(e["pad"]), float(e["t"]), int(e["pad"]))
			elif not e["down"] and down.get(e["pad"], false):
				down[e["pad"]] = false
				m.release(int(e["pad"]), float(e["t"]), int(e["pad"]))
		m.advance(t)
	m.advance(until)
	return m


func _summary(m: Match) -> Array:
	var rows := []
	for e in m.reward_log:
		rows.append([e["sequence"], e["grade"], e["resolve_time"], e.get("ready_time", -1.0), e.get("point", -1), e["result"]])
	return [rows, m.sim.tick_count, m.sim.count_alive(0, BattleSim.Kind.UNIT), m.sim.count_alive(1, BattleSim.Kind.UNIT),
		m.sim.defense_count(), m.sim.objective_hp("command_core"), m.outcome, m.pad_judge.credit, m.pad_judge.resolved_at]


func _plan(level: Level, seed_value: int) -> Array:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	return load(HARNESS).plan_inputs(level, "beginner", rng)


func test_same_inputs_give_the_same_rewards_at_60_30_fps_and_uneven_frames() -> void:
	for pack in ["m01_first_watch", "m03_hold_the_line"]:
		var level: Level = LevelLoader.load_pack(TestCase.project_path("songs/" + pack))["level"]
		var plan := _plan(level, 11)
		var until := minf(level.duration_seconds(), 36.0)
		var base := _summary(_drive(level, plan, [1.0 / 60.0], until))
		assert_true(base[0].size() >= 4, "%s: enough sequences resolved to compare" % pack)
		var passed := 0
		for e in base[0]:
			if e[5] != "failed":
				passed += 1
		assert_true(passed >= 2, "%s: the beginner plan earns rewards" % pack)
		assert_eq(_summary(_drive(level, plan, [1.0 / 30.0], until)), base, "%s at 30 fps" % pack)
		assert_eq(_summary(_drive(level, plan, [0.013, 0.029, 0.007, 0.041, 0.022], until)), base, "%s with uneven frames" % pack)


func test_pause_mid_hold_is_deterministic() -> void:
	var level: Level = LevelLoader.load_pack(TestCase.project_path("songs/m03_hold_the_line"))["level"]
	var plan := _plan(level, 5)
	var pause_at := -1.0
	for n in level.notes:
		if n["type"] == "hold" and float(n["time"]) > 12.0:
			pause_at = (float(n["time"]) + float(n["end_time"])) * 0.5
			break
	assert_true(pause_at > 0.0)
	var a := _drive(level, plan, [1.0 / 60.0], 30.0, pause_at)
	var b := _drive(level, plan, [1.0 / 30.0], 30.0, pause_at)
	var c := _drive(level, plan, [0.017, 0.031, 0.009], 30.0, pause_at)
	assert_eq(_summary(b), _summary(a), "pause at 30 fps")
	assert_eq(_summary(c), _summary(a), "pause with uneven frames")
	assert_true(a.pad_judge.holds_partial >= 1, "the pause cut a hold short")


func test_retry_with_a_fresh_load_reproduces_the_run() -> void:
	var path := TestCase.project_path("songs/m01_first_watch")
	var l1: Level = LevelLoader.load_pack(path)["level"]
	var a := _summary(_drive(l1, _plan(l1, 21), [1.0 / 60.0], 30.0))
	var l2: Level = LevelLoader.load_pack(path)["level"]
	var b := _summary(_drive(l2, _plan(l2, 21), [1.0 / 60.0], 30.0))
	assert_eq(b, a)
	var l3: Level = LevelLoader.load_pack(path)["level"]
	var c := _summary(_drive(l3, _plan(l3, 22), [1.0 / 60.0], 30.0))
	assert_true(c != a, "a different seed is a different run (the comparison is not vacuous)")
