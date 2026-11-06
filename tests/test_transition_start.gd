extends TestCase
## The group start fix (stage M2.4, docs/music/TRANSITIONS_BUILT.md "The start"): a track scene entered through a lock starts early and MUTED, is pulled onto the clock by a small pitch_scale
## while muted (a feedback loop on its playhead against the clock's), plays at exactly 1.0 from two mix periods before T, is unmuted just before T and adopted by the engine's track_start.
## The audio thread is simulated here (RunTrackAudio.position_fn): a group lands `lag` seconds late, as WASAPI lands it 8.0 or 18.7 ms late, and its playhead advances by its pitch_scale.

const Fx := preload("res://tests/fixtures/track_scenes/track_scene_fixtures.gd")

var _made: Array = []


func _cleanup() -> void:
	for a in _made:
		if is_instance_valid(a):
			(a as RunAudio).stop()
			(a as RunAudio).free()
	_made.clear()
	Fx.clear()


## A RunAudio whose track audio holds the decoded pack of scene "warehouse.bar" (track "in_b").
func _setup() -> Dictionary:
	Fx.clear()
	Fx.write_pack("in_b", {"bpm": 172.0, "bars": 128, "cue_bars": [20, 100], "sections": [["d1", "drop", 32, 96]]})
	Fx.write_pack("out_a", {"bpm": 175.0, "bars": 128, "cue_bars": [20, 100], "sections": [["d1", "drop", 32, 96]]})
	var d := Fx.main_data({"main": {"warehouse": {"track": "out_a"}, "warehouse.bar": {"track": "in_b"}}})
	var a := RunAudio.new()
	tree.root.add_child(a)
	a.configure(d)
	_made.append(a)
	a.track.period_override = 0.01
	assert_eq(a.track.request_scene(d, "warehouse.bar"), "loading")
	for _i in 400:
		a.track._poll()
		if not a.track.cached().values().has("loading"):
			break
		OS.delay_msec(5)
	return {"a": a, "d": d, "plan": d.track_scenes.plan_of("warehouse.bar")}


func _recipe(plan: Dictionary, mode := &"cut") -> Dictionary:
	return {"mode": mode, "fade_s": 0.6, "tail_s": 0.6, "incoming": &"track",
		"in": {"node": "warehouse.bar", "track": str(plan["track"]), "dir": str(plan["dir"]), "entry_t": float(plan["entry_t"]), "beat_s": float(plan["beat_s"]), "bpm": float(plan["bpm"])}}


## Steps the track audio from t0 to t1 in frames of `dt`. The simulated audio thread lands every (re)start of the group lags[k] late (k counting the starts) and moves its playhead at its
## pitch_scale per frame. Returns the frames [x, volume_db, pitch_scale].
func _sim(a: RunAudio, t0: float, t1: float, lags: Array, dt := 1.0 / 60.0) -> Array:
	var sim := {"x": t0, "gp": NAN, "start": NAN, "k": 0, "fresh": true}
	a.track.position_fn = func(_g: Dictionary) -> Array:
		if is_nan(float(sim["gp"])) or bool(sim["fresh"]):
			return []  # (not mixed yet)
		return [float(sim["x"]), float(sim["gp"])]
	var frames: Array = []
	var t := t0
	while t < t1:
		a.track.step(t, 0.0)
		var g: Dictionary = {}
		for x in a.track._groups:
			if str(x["track"]) == "in_b":
				g = x
		if not g.is_empty():
			var tr: TrackTransport = g["transport"]
			frames.append([t, tr.player.volume_db, tr.player.pitch_scale])
			var sa := tr.start_at
			if is_nan(float(sim["start"])) or absf(sa - float(sim["start"])) > 1e-12:  # (re)started in this frame, on the song time t of the call: it lands lags[k] late
				sim["start"] = sa
				sim["gp"] = sa - float(lags[mini(int(sim["k"]), lags.size() - 1)])
				sim["k"] = int(sim["k"]) + 1
				sim["fresh"] = true
			else:
				sim["fresh"] = false
			sim["gp"] = float(sim["gp"]) + dt * tr.player.pitch_scale
		t += dt
		sim["x"] = t
	return frames


func test_a_locked_track_scene_starts_early_muted_and_is_pulled_onto_the_clock() -> void:
	# the same lag every time (WASAPI's two values, and an early one), the two alternating, and lags that never repeat (the restarts give up: the rate takes the rest)
	for lags in [[0.0187], [0.008], [-0.004], [0.0187, 0.008, 0.0187, 0.0187, 0.0187], [0.0187] + range(40).map(func(k: int) -> float: return 0.009 + 0.0013 * k)]:
		var lag := float(lags[0])
		var s := _setup()
		var a: RunAudio = s["a"]
		var plan: Dictionary = s["plan"]
		var T := 100.0
		a.track.prepare_transition(T, _recipe(plan))
		var frames := _sim(a, T - 1.2, T + 0.2, lags)
		var pre: Array = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "prestart")
		assert_eq(pre.size(), 1, "one early start")
		assert_near(float(pre[0]["from"]), float(plan["entry_t"]) - 1.2, 1e-9, "from the entry time less the lead: on the clock if it landed on time")
		assert_eq(int(pre[0]["slot"]), 0, "the free slot")
		for f in frames:
			if float(f[0]) < T - 0.01 - 0.02 - 1e-9:
				assert_true(float(f[1]) <= -79.9, "muted before T (t=%.3f)" % float(f[0]))
			if float(f[0]) >= T - 2.0 * 0.01 - 0.02 + 1e-9:
				assert_eq(float(f[2]), 1.0, "at exactly 1.0 from two mix periods before T (t=%.3f)" % float(f[0]))
			if float(f[0]) >= T:
				assert_near(float(f[1]), 0.0, 1e-9, "heard from T")
		var corr: Array = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "corrected")
		assert_eq(corr.size(), 1)
		assert_near(float(corr[0]["err_ms"]), -lag * 1000.0, 1e-6, "the start error is read from the playhead")
		assert_true(absf(float(corr[0]["final_ms"])) < 0.1, "absorbed while muted (lag %.1f ms, left %.4f ms)" % [lag * 1000.0, float(corr[0]["final_ms"])])
		assert_true(float(corr[0]["rate_min"]) >= 1.0 - RunTrackAudio.CORRECT_MAX_RATE - 1e-9 and float(corr[0]["rate_max"]) <= 1.0 + RunTrackAudio.CORRECT_MAX_RATE + 1e-9, "a small rate")
		if lags.size() <= 5:
			assert_true(bool(corr[0]["landed"]), "landed by restarts (lags %s)" % str(lags))
			assert_eq([float(corr[0]["rate_min"]), float(corr[0]["rate_max"])], [1.0, 1.0], "never rate-changed")
			assert_true(int(corr[0]["restarts"]) <= (1 if lags.size() == 1 else 4), "restarts %d" % int(corr[0]["restarts"]))
		else:
			assert_true(float(corr[0]["rate_min"]) < 1.0 or float(corr[0]["rate_max"]) > 1.0, "restarts gave up: the rate took the rest")
		# the engine's track_start at T adopts it: no second group
		var n_before := a.track.active_group_count()
		a.track.run_item({"t": T, "kind": "start", "ev": {"t": T, "node": "warehouse.bar", "track": "in_b", "dir": str(plan["dir"]), "track_t": float(plan["entry_t"]), "beat_s": float(plan["beat_s"])}}, T + 0.02, 0.0)
		assert_eq(a.track.active_group_count(), n_before, "adopted, not started again")
		var st: Array = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "start")
		assert_eq(st.size(), 1)
		assert_true(bool(st[0]["prepared"]))
		assert_eq(str(a.track.live().get("track", "")), "in_b", "the live group")
		_cleanup()


func test_a_lock_too_close_to_the_boundary_starts_at_t_by_the_lateness_rule() -> void:
	var s := _setup()
	var a: RunAudio = s["a"]
	var plan: Dictionary = s["plan"]
	var T := 50.0
	a.track.prepare_transition(T, _recipe(plan))
	a.track.step(T - 0.1, 0.0)
	assert_eq(a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "prestart"), [], "0.1 s is too short to measure and correct")
	a.track.run_item({"t": T, "kind": "start", "ev": {"t": T, "node": "warehouse.bar", "track": "in_b", "dir": str(plan["dir"]), "track_t": float(plan["entry_t"]), "beat_s": float(plan["beat_s"])}}, T + 0.01, 0.005)
	var st: Array = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "start")
	assert_eq(st.size(), 1)
	assert_false(bool(st[0]["prepared"]))
	assert_near(float(st[0]["from"]), float(plan["entry_t"]) + 0.015, 1e-9, "today's rule")
	_cleanup()


func test_a_muted_start_for_a_scene_that_is_not_entered_goes() -> void:
	var s := _setup()
	var a: RunAudio = s["a"]
	var plan: Dictionary = s["plan"]
	var T := 80.0
	a.track.prepare_transition(T, _recipe(plan))
	_sim(a, T - 1.2, T - 0.5, [0.01])
	assert_eq(a.track.active_group_count(), 1)
	a.track.on_event({"kind": "phase_start", "t": T, "node": "warehouse.other", "phase": 3})  # (an ordinary scene began instead: a fallback)
	a.track.step(T, 0.0)
	var orph: Array = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "orphan")
	assert_eq(orph.size(), 1, "the muted group is let go")
	assert_eq(a.track.live(), {}, "nothing plays as the scene")
	_cleanup()


func test_groups_alternate_between_the_two_slot_buses_into_the_limited_track_bus() -> void:
	var s := _setup()
	var a: RunAudio = s["a"]
	for name in RunTrackAudio.SLOT_BUSES:
		var i := AudioServer.get_bus_index(str(name))
		assert_true(i >= 0, "%s exists" % name)
		assert_eq(str(AudioServer.get_bus_send(i)), RunTrackAudio.BUS)
		assert_true(AudioServer.get_bus_effect(i, RunTrackAudio.FX_HIGHPASS) is AudioEffectHighPassFilter)
		assert_true(AudioServer.get_bus_effect(i, RunTrackAudio.FX_DELAY) is AudioEffectDelay)
		assert_false(AudioServer.is_bus_effect_enabled(i, RunTrackAudio.FX_HIGHPASS), "effects off until a tail needs them")
		assert_false(AudioServer.is_bus_effect_enabled(i, RunTrackAudio.FX_DELAY))
	var plan: Dictionary = s["plan"]
	var ev := {"t": 0.0, "node": "warehouse.bar", "track": "in_b", "dir": str(plan["dir"]), "track_t": float(plan["entry_t"]), "beat_s": float(plan["beat_s"])}
	a.track.run_item({"t": 0.0, "kind": "start", "ev": ev}, 0.0, 0.0)
	ev["t"] = 30.0
	a.track.run_item({"t": 30.0, "kind": "start", "ev": ev}, 30.0, 0.0)
	var st: Array = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "start")
	assert_eq([int(st[0]["slot"]), int(st[1]["slot"])], [0, 1], "the second group takes the other slot")
	_cleanup()


func test_an_entry_at_the_start_of_the_audio_is_probed_then_started_at_t_with_the_lag_taken_off() -> void:
	# entry bar 0 (loadstar_dr_karg_original_mix, measured on WASAPI): no audio before the entry to start early from. A muted probe learns the landing lag; the real start is at T.
	var s := _setup()
	var a: RunAudio = s["a"]
	var r := _recipe(s["plan"])
	(r["in"] as Dictionary)["entry_t"] = 0.0024
	var T := 60.0
	a.track.prepare_transition(T, r)
	var frames := _sim(a, T - 1.2, T + 0.1, [0.0187, 0.008, 0.0187, 0.0187])
	var pre: Array = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "prestart")
	assert_true(bool(pre[0]["probe"]), "a probe")
	var fs: Array = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "final_start")
	assert_eq(fs.size(), 1, "one real start")
	assert_near(float(fs[0]["comp_ms"]), 18.7, 1e-6, "with the lag the probes landed with")
	assert_true(float(fs[0]["at"]) >= T - 0.0187 - 1e-9 and float(fs[0]["at"]) <= T + 1.0 / 60.0, "at T (%.4f)" % float(fs[0]["at"]))
	for f in frames:
		if float(f[0]) < float(fs[0]["at"]) - 1e-9:
			assert_true(float(f[1]) <= -79.9, "the probe is never heard")
	var corr: Array = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "corrected")
	assert_eq(corr.size(), 1)
	assert_true(absf(float(corr[0]["final_ms"])) < 0.1, "it landed on the clock (%.4f ms)" % float(corr[0]["final_ms"]))
	_cleanup()
