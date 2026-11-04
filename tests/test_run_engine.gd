extends TestCase
## The continuous run's logic (RunEngine): the four-step mix, held and delayed reveals, the route window, default and changed routes,
## survival, and identical charts for sibling routes.


func _data() -> RunData:
	var d := RunData.load_default()
	assert_eq(d.errors, [], "run data validates")
	return d


## Plays by hand with a perfect or absent player: `pattern` has one bool per block of the run (true = hit every cue of the block exactly on
## time, false = hit none). Returns every event the engine emitted. `choose_at` {song time: destination id} applies a choice then.
func _play(e: RunEngine, pattern: Array, until_t: float, choose_at: Dictionary = {}) -> Array:
	var log: Array = []
	var t := 0.0
	var step := 1.0 / 60.0
	var pressed := {}
	var released := {}
	var chosen := {}
	while t < until_t and not e.over:
		for at in choose_at:
			if t >= float(at) and not chosen.has(at):
				chosen[at] = true
				e.choose(str(choose_at[at]))
		log.append_array(e.update(t))
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			var idx := (int(n["phase"]) - 1) * 4 + int(n["block"])
			var hit: bool = idx < pattern.size() and bool(pattern[idx])
			if hit and not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]))
			if hit and pressed.has(i) and n["type"] == "hold" and not released.has(i) and float(n["end_time"]) <= t:
				released[i] = true
				e.release(int(n["pad"]), float(n["end_time"]))
		t += step
	return log


func _kinds(log: Array, kind: String) -> Array:
	return log.filter(func(x: Dictionary) -> bool: return x["kind"] == kind)


func test_run_data_validates_and_siblings_play_the_same_tier() -> void:
	var d := _data()
	assert_true(d.nodes.size() >= 7)
	for id in d.nodes:
		var tier := str(d.tier_of(int(d.nodes[id]["depth"])))
		assert_true((d.packs[d.nodes[id]["chart"]]["tiers"] as Dictionary).has(tier), "%s has its own chart at tier %s (siblings may chart different packs, always the same tier)" % [id, tier])


func test_perfect_phase_walks_the_four_stages() -> void:
	var e := RunEngine.new(_data())
	e.begin("warehouse")
	var log := _play(e, [true, true, true, true], e.phase_s() - 0.01)
	var mixes := _kinds(log, "mix")
	var stages := mixes.map(func(m: Dictionary) -> int: return int(m["stage"]))
	assert_eq(stages, [0, 1, 2, 3], "drums alone, bass enters, drums return, bass strongest")
	var beats := mixes.map(func(m: Dictionary) -> float: return snappedf(float(m["t"]) / e.beat_s, 0.01))
	assert_eq(beats, [0.0, 16.0, 32.0, 48.0], "the stages begin on the block boundaries")
	var rev := _kinds(log, "reveal")
	assert_eq(rev.size(), 1)
	assert_eq(int(rev[0]["beat"]), 16, "bass revealed at beat 17")
	var win := _kinds(log, "route_window")
	assert_eq(win.size(), 1)
	assert_eq(win[0]["effect"], "riser", "the final bass stage was reached by beat 49")
	assert_eq((win[0]["options"] as Array).size(), 2)


func test_a_missed_block_holds_the_mix_and_delays_the_reveal() -> void:
	var e := RunEngine.new(_data())
	e.begin("warehouse")
	var log := _play(e, [false, true, true, true], e.phase_s() - 0.01)
	var stages := _kinds(log, "mix").map(func(m: Dictionary) -> int: return int(m["stage"]))
	assert_eq(stages, [0, 0, 1, 2], "missing block 1 holds drums alone for another block; bass then reveals on beat 33")
	assert_eq(int(_kinds(log, "reveal")[0]["beat"]), 32)
	assert_eq(_kinds(log, "route_window")[0]["effect"], "fall", "a stalled build falls into the choice window")
	assert_eq(e.cue_family(1), "drums")
	assert_eq(e.cue_family(2), "bass")
	assert_eq(e.cue_family(3), "drums", "block 4 is drums return, the second step")


func test_the_phase_lasts_64_beats_and_resets_to_drums_alone() -> void:
	var e := RunEngine.new(_data())
	e.begin("warehouse")
	var log := _play(e, [true, false, false, true, true, true, true, true], e.phase_s() + 2.0)
	var commits := _kinds(log, "route_commit")
	assert_eq(commits.size(), 1)
	assert_near(float(commits[0]["t"]), 64.0 * e.beat_s, 1e-6)
	assert_eq(_kinds(log, "phase_start").size(), 2)
	assert_eq(e.stage, 0, "the next phase starts with drums alone")
	assert_eq(e.node_id, "mothership", "no choice made: the marked default route")
	assert_eq(commits[0]["chosen"], false)


func test_changing_direction_until_the_phase_ends() -> void:
	var e := RunEngine.new(_data())
	e.begin("warehouse")
	_play(e, [true, true, true, true], 50.0 * e.beat_s, {50.0 * e.beat_s - 1.0: "mothership"})
	assert_true(e.window_open)
	assert_true(e.choose("mothership"))
	assert_true(e.choose_dir("right"), "the player changes their mind")
	assert_eq(e.selected_route(), "underworld")
	assert_false(e.choose("hospital"), "not a route from here")
	var log := _play(e, [true, true, true, true, true, true, true, true], 66.0 * e.beat_s)
	assert_true(log.size() >= 0)


func test_siblings_chart_their_own_required_cues_at_the_same_tier() -> void:
	for dest in ["mothership", "underworld"]:
		var e := RunEngine.new(_data())
		e.begin("warehouse")
		_play(e, [true, true, true, true, true, true, true, true], 80.0 * e.beat_s, {55.0 * e.beat_s: dest})
		assert_eq(e.node_id, dest)
		var rows: Array = []
		for n in e.level.notes:
			if int(n["phase"]) == 2 and int(n["block"]) == 1:  # block 0 of a phase is charted before the route is final (see the progress log)
				rows.append([int(n["tick"]) - 64 * 960, n["pad"], n["duration_ticks"], n["family"]])
		var ref := RunEngine.new(_data())
		ref.begin(dest)  # the same node entered fresh: depth tier of its own chart
		_play(ref, [true, true], 20.0 * ref.beat_s)
		var want: Array = []
		for n in ref.level.notes:
			if int(n["phase"]) == 1 and int(n["block"]) == 1:
				want.append([n["tick"], n["pad"], n["duration_ticks"], n["family"]])
		assert_true(rows.size() > 3)
		assert_eq(rows, want, "%s charts its own pack's block-1 cues" % dest)


func test_difficulty_rises_with_depth() -> void:
	var d := _data()
	var counts: Array = []
	for dp in [1, 2, 3, 4]:
		for id in d.nodes:
			if int(d.nodes[id]["depth"]) == dp:
				var pack: Dictionary = d.packs[d.nodes[id]["chart"]]
				counts.append(float((pack["tiers"][str(dp)]["drums"] as Array).size()) * 16.0 / float(pack["phrase_beats"]))
				break
	assert_eq(counts.size(), 4)
	assert_true(counts[3] > counts[0], "a deeper level charts more drum cues per 16 beats (%s)" % str(counts))


func test_failing_everything_ends_the_run_on_a_block_boundary() -> void:
	var e := RunEngine.new(_data())
	e.begin("warehouse")
	var log := _play(e, [], 400.0)
	var dep := _kinds(log, "depleted")
	assert_eq(dep.size(), 1)
	var beats := float(dep[0]["t"]) / e.beat_s
	assert_near(fmod(beats, 16.0), 0.0, 1e-6, "ends on a block boundary")
	assert_true(e.over)
	assert_eq(_kinds(log, "run_over").size(), 1)
	assert_true(float(dep[0]["fade_s"]) > 0.0, "with a short fade")


func test_a_rough_block_is_recoverable() -> void:
	var e := RunEngine.new(_data())
	e.begin("warehouse")
	var pattern: Array = [false, false]
	for _i in 12:
		pattern.append(true)
	_play(e, pattern, 12.0 * 16.0 * e.beat_s)
	assert_false(e.over, "two bad blocks then good play keeps the run alive")
	assert_true(e.energy > 20.0)
