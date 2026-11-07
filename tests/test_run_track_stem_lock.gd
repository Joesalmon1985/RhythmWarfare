extends TestCase
## The bass lock on a track scene (CONTRACTS.md 7, hooks H7.1 and H7.2): RunTrackAudio locks the stems the host names on the group it makes, so the gain program and
## a miss restore cannot bring them in; an unlock scheduled for a bar line ramps the stem in from that song time and the group's playhead never restarts.

const Fx := preload("res://tests/fixtures/track_scenes/track_scene_fixtures.gd")

var _made: Array = []


func _audio(d: RunData) -> RunAudio:
	var a := RunAudio.new()
	tree.root.add_child(a)
	a.configure(d)
	_made.append(a)
	return a


func _cleanup() -> void:
	for a in _made:
		if is_instance_valid(a):
			(a as RunAudio).stop()
			(a as RunAudio).free()
	_made.clear()
	Fx.clear()


func _pump(a: RunAudio, t: float) -> void:
	for path in a._requested:
		for _i in 400:
			if ResourceLoader.load_threaded_get_status(str(path)) != ResourceLoader.THREAD_LOAD_IN_PROGRESS:
				break
			OS.delay_msec(5)
	while not a._schedule.is_empty() and float(a._schedule[0]["t"]) <= t:
		var item: Dictionary = a._schedule.pop_front()
		a._run(item, float(item["t"]), 0.0)
	while not a.track._schedule.is_empty() and float(a.track._schedule[0]["t"]) <= t:
		var it: Dictionary = a.track._schedule.pop_front()
		a.track.run_item(it, float(it["t"]), 0.0)
	a.track.step(t, 0.0)


## Plays perfectly until song time `t_end`; `at(e, t)` each frame.
func _run(e: RunEngine, a: RunAudio, t_end: float, at: Callable, from := -0.5) -> float:
	var t := from
	var pressed := {}
	while t < t_end and not e.over:
		at.call(e, t)
		for ev in e.update(t):
			a.on_event(ev)
		_pump(a, t)
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			if not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
				e.release(int(n["pad"]), float(n["end_time"]) if n["type"] == "hold" else float(n["time"]) + 0.06, int(n["pad"]))
		t += 1.0 / 30.0
	return t


func test_a_locked_bass_stays_silent_through_the_mix_and_unlocks_on_a_bar_without_a_restart() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", Fx.go_back_spec())
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}})
	assert_eq(d.errors, [])
	var a := _audio(d)
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.track_gate = a.track.is_ready
	a.track.notes_fn = func() -> Array: return e.level.notes
	a.track.prepare(d, "warehouse")
	a.track.lock_stems("acuna_go_back", ["bass"])  # (the host, entering a rave whose bass is not fixed: before the scene starts)
	e.begin("warehouse")
	assert_true(e.is_track_scene())
	var t := _run(e, a, 20.0 * e.beat_s, func(_e: RunEngine, _t: float) -> void: pass)
	var g: Dictionary = a.track._live()
	assert_false(g.is_empty(), "the group plays")
	var tr: TrackTransport = g["transport"]
	assert_true(tr.is_stem_locked("bass"), "locked on the group it made (H7.1)")
	assert_eq(tr.stem_target("bass"), 0.0, "silent")
	assert_eq(tr.stem_gain("bass"), 0.0)
	assert_eq(tr.stem_target("drums"), 1.0, "the drums play")
	tr.apply_program({"drums": true, "bass": true, "backing": true}, true)  # (a gain program and a miss restore)
	tr.set_stem_muted("bass", false)
	assert_eq(tr.stem_gain("bass"), 0.0, "neither the program nor a restore lifts the lock")
	# the bass is fixed at beat 21.3: the unlock lands on the next bar line, beat 24
	var t_fixed := 21.3 * e.beat_s
	var t_u := ContractShapes.unlock_time(t_fixed, e.phase_t0, e.beat_s, "bar")
	assert_near(t_u, 24.0 * e.beat_s, 1e-9)
	var start0: Array = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "start")
	var unlocked := [false]
	t = _run(e, a, 23.9 * e.beat_s, func(_e: RunEngine, tt: float) -> void:
		if tt >= t_fixed and not unlocked[0]:
			unlocked[0] = true
			a.track.unlock_stem_at("bass", t_u, 2.0 * e.beat_s), t)
	assert_true(tr.is_stem_locked("bass"), "still locked until the bar line")
	assert_eq(tr.stem_target("bass"), 0.0)
	t = _run(e, a, 26.0 * e.beat_s, func(_e: RunEngine, _t: float) -> void: pass, t)
	var un: Array = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "unlock")
	assert_eq(un.size(), 1, "one unlock")
	assert_near(float(un[0]["t"]), t_u, 1e-9, "on the bar line (H7.2)")
	assert_near(float(un[0]["ramp_s"]), 2.0 * e.beat_s, 1e-9, "ramped over two beats")
	assert_eq(int(un[0]["groups"]), 1)
	assert_false(tr.is_stem_locked("bass"))
	assert_eq(tr.stem_target("bass"), 1.0, "the mix may use it now")
	assert_near(float(tr._ramp.get("bass", 0.0)), 2.0 * e.beat_s, 1e-9, "it rises over the unlock's ramp, not at once")
	assert_eq(a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "start").size(), start0.size(), "no new start")
	assert_eq(a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) in ["seek", "stop"]), [], "no seek, no stop: the playhead goes on")
	assert_true(a.track._live()["transport"] == tr, "the same group")
	assert_eq(a.track.stem_locks.get("acuna_go_back", []), [], "later groups of the track are made unlocked")
	_cleanup()


func test_without_a_lock_nothing_changes() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", Fx.go_back_spec())
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}})
	var a := _audio(d)
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.track_gate = a.track.is_ready
	a.track.notes_fn = func() -> Array: return e.level.notes
	a.track.prepare(d, "warehouse")
	e.begin("warehouse")
	_run(e, a, 8.0 * e.beat_s, func(_e: RunEngine, _t: float) -> void: pass)
	var tr: TrackTransport = a.track._live()["transport"]
	assert_false(tr.is_stem_locked("bass"))
	assert_eq(tr.stem_target("bass"), 1.0)
	_cleanup()
