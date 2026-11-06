extends TestCase
## M2.5, drift and hit windows through transitions, on a virtual clock with fixture packs (tests/fixtures/transition/blend_rig.gd). Ten transitions in a row (blends, a half-time blend,
## echo-outs and cuts at seven tempos), every muted start landing 18.7 or 8.0 ms late as WASAPI lands them: each group is corrected to within 0.1 ms before it is heard (one mix chunk is
## 10 ms), with no trend, and every cue of every scene sits where its group's audio has that moment of the track (exact). Then the judge: a cue inside a blend is judged on the incoming grid with
## the same windows as anywhere: a perfect player scores perfect through every transition, and early and late players score exactly as they do with every change a cut.

const Rig := preload("res://tests/fixtures/transition/blend_rig.gd")

const TEMPOS := [174.0, 171.0, 175.0, 177.0, 172.0, 88.0, 174.0, 140.0, 176.0, 173.0, 174.5]


func _chain(tempos: Array, tag: String) -> Array:
	var c: Array = []
	for i in tempos.size():
		c.append({"track": "%s_%d" % [tag, i], "spec": Rig.spec(float(tempos[i]))})
	return c


func test_ten_transitions_in_a_row_keep_cue_time_and_audio_time_together() -> void:
	var rig: RefCounted = Rig.new(tree, _chain(TEMPOS, "dr"), 1)
	rig.lags = [0.0187, 0.008, 0.0187, 0.0187, 0.008]
	rig.run_transitions(10, 4000.0)
	var dir: TransitionDirector = rig.director
	assert_eq(rig.signals(&"completed").size(), 10, "ten transitions completed")
	var modes := {}
	for l in dir.lock_log:
		modes[str((l["plan"] as Dictionary)["mode"])] = int(modes.get(str((l["plan"] as Dictionary)["mode"]), 0)) + 1
	print("DRIFT modes over ten transitions: ", modes)
	assert_true(modes.has("blend") and modes.has("echo_out") and modes.has("halftime_blend"), "several modes among them")
	var corr: Array = rig.audio.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "corrected")
	assert_eq(corr.size(), 10, "every incoming group started early and muted")
	var res: Array = []
	for c in corr:
		assert_true(absf(float(c["err_ms"])) > 7.9, "it landed late (%.2f ms)" % float(c["err_ms"]))
		assert_true(absf(float(c["final_ms"])) < 0.1, "and was corrected before it was heard: %.4f ms left (a mix chunk is 10 ms)" % float(c["final_ms"]))
		res.append(float(c["final_ms"]))
	var slope := (float(res[res.size() - 1]) - float(res[0])) / float(res.size() - 1)
	assert_true(absf(slope) < 0.5, "no trend over the ten (%.4f ms per transition)" % slope)
	# every cue: its song time against the moment its group plays that track time
	var starts: Array = rig.audio.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) in ["start", "seek"])
	var worst := 0.0
	var n := 0
	for note in rig.engine.level.notes:
		var tm := float(note["time"])
		var s: Dictionary = {}
		for x in starts:
			if float(x["t"]) <= tm + 1e-9:
				s = x
		if s.is_empty():
			continue
		var audio_t := float(s["t"]) + (float(note["track_t"]) - float(s["track_t"]))
		worst = maxf(worst, absf(tm - audio_t))
		n += 1
	assert_true(n > 300, "%d cues checked" % n)
	assert_true(worst < 1e-6, "every cue on its group's audio (worst %.9f s)" % worst)
	# song time: monotonic and continuous through every switch
	var sw: Array = rig.signals(&"switched")
	for e in sw:
		assert_near(float(e["t"]), float((e["args"] as Array)[2]), 1e-9)
	rig.free_all()


func _grades(offset: float, modes: int) -> Dictionary:
	var rig: RefCounted = Rig.new(tree, _chain([174.0, 171.0, 175.0, 140.0, 172.0], "ht%d" % modes), modes)
	rig.offset = offset
	rig.run_transitions(4, 2000.0)
	var counts := {}
	var in_blend := {}
	var windows: Array = []
	for l in rig.director.lock_log:
		windows.append([float(l["boundary"]), float((l["plan"] as Dictionary)["complete_t"])])
	var t_last := float(windows[windows.size() - 1][0]) + 8.0  # (the same span of play in both runs: a blend completes later than a cut, and the run stops at the 4th completed)
	while rig.t < t_last + 1.0:
		rig.advance(0.25)
	for g in rig.grades:
		if float(g["cue_t"]) >= t_last:
			continue
		counts[g["kind"]] = int(counts.get(g["kind"], 0)) + 1
		for w in windows:
			if float(g["cue_t"]) >= float(w[0]) and float(g["cue_t"]) < float(w[1]):
				in_blend[g["kind"]] = int(in_blend.get(g["kind"], 0)) + 1
	var mode_list: Array = rig.director.lock_log.map(func(l: Dictionary) -> String: return str((l["plan"] as Dictionary)["mode"]))
	rig.free_all()
	return {"all": counts, "in_blend": in_blend, "modes": mode_list}


func test_the_judge_through_transitions_is_the_judge_mid_scene() -> void:
	for off in [0.0, -0.03, 0.03, -0.07, 0.07]:
		var full := _grades(off, 1)
		var cut := _grades(off, 0)
		assert_true((full["modes"] as Array).has("blend") and (full["modes"] as Array).has("echo_out"), "blends and an echo-out: %s" % str(full["modes"]))
		assert_eq(cut["modes"], ["cut", "cut", "cut", "cut"])
		assert_eq(full["all"], cut["all"], "offset %+.0f ms: the same grades with transitions as with cuts" % (off * 1000.0))
		assert_true(int((full["in_blend"] as Dictionary).values().reduce(func(a: int, b: int) -> int: return a + b, 0)) > 20, "cues inside the blends were judged")
		var want := "perfect" if absf(off) <= 0.045 else "great"
		assert_eq((full["all"] as Dictionary).keys(), [want], "offset %+.0f ms: every cue %s, inside a blend too (%s)" % [off * 1000.0, want, str(full["all"])])
