extends TestCase
## The transition seam of stage M1.6 outside the conformance cases: the audio's silence report (RunAudio.prepare_transition / outgoing_silent), the planner's rows, the track audio's
## pins, and the director wired into the run scene (RunPlay, virtual clock): every scene change of an ordinary run goes through the port, in order, while the run is the run of before.

const Fx := preload("res://tests/fixtures/track_scenes/track_scene_fixtures.gd")


# --- the planner -----------------------------------------------------------------------------------------------------------------

func test_the_m1_planner_cuts_and_defers_only_an_unready_track_once() -> void:
	var out := {"kind": &"track", "node": "x", "path": "main", "bpm": 175.0, "boundary_t": 100.0}
	var inc := {"kind": &"track", "node": "y", "path": "main", "bpm": 172.0, "ordinary_bpm": 174.0}
	var meta := {"fade_s": 0.6, "carry_beats": 16.0, "carry_gain": 0.5}
	var p := TransitionPlanner.plan(out, inc, meta, {"state": "ready", "may_defer": true})
	assert_eq(p["mode"], &"cut")
	assert_false(bool(p["fallback"]))
	assert_near(float(p["incoming_bpm"]), 172.0, 1e-9, "a ready track scene plays at the track's tempo")
	assert_near(float(p["complete_t"]), 100.6, 1e-9)
	assert_eq(int(p["blend_beats"]), 0)
	assert_eq(TransitionPlanner.plan(out, inc, meta, {"state": "loading", "may_defer": true}), {"defer": &"not_ready"}, "row 1: loading, may defer, not yet deferred")
	var p2 := TransitionPlanner.plan(out, inc, meta, {"state": "loading", "may_defer": true, "deferred_once": true})
	assert_eq(p2["mode"], &"cut", "row 2: still loading after the deferral")
	assert_true(bool(p2["fallback"]))
	assert_near(float(p2["incoming_bpm"]), 174.0, 1e-9, "it plays as an ordinary scene, at the run's tempo")
	assert_eq(p2["recipe"]["incoming"], &"ordinary")
	assert_true(bool(TransitionPlanner.plan(out, inc, meta, {"state": "failed", "may_defer": true})["fallback"]), "a failed load: cut, ordinary")
	assert_false(TransitionPlanner.plan(out, inc, meta, {"state": "loading", "may_defer": false}).has("defer"), "the engine's own route never defers")
	var lo := {"kind": &"ordinary", "node": "x", "bpm": 174.0, "boundary_t": 10.0, "family": "f"}
	var li := {"kind": &"ordinary", "node": "y", "bpm": 174.0, "ordinary_bpm": 174.0, "family": "f"}
	var pc := TransitionPlanner.plan(lo, li, meta, {"state": ""})
	assert_true(bool(pc["recipe"]["carry"]), "two loop scenes of one family: the bass may carry")
	assert_near(float(pc["complete_t"]), 10.0 + 16.0 * 60.0 / 174.0 + 0.6, 1e-9, "complete_t covers the carried bass and its fade")
	li["family"] = "g"
	assert_near(float(TransitionPlanner.plan(lo, li, meta, {"state": ""})["complete_t"]), 10.6, 1e-9, "no carry across families")


# --- the audio's silence report ---------------------------------------------------------------------------------------------------

func test_the_audio_reports_silence_after_the_outgoing_fade() -> void:
	var d := RunData.load_default()
	var a := RunAudio.new()
	tree.root.add_child(a)
	a.configure(d)
	var heard: Array = []
	a.outgoing_silent.connect(func(bt: float) -> void: heard.append(bt))
	a._begin_phase({"kind": "phase_start", "node": "warehouse", "t": 0.0, "phase": 1, "treatment": "none", "audio": d.nodes["warehouse"]["audio"]}, 0.0, 0.0, 0.0)
	a._groups[0]["voices"]["drums"]["gain"] = 1.0
	var t := 64.0 * a.beat_s
	a.prepare_transition(t, {"mode": &"cut", "fade_s": 0.6, "tail_s": 0.6})
	a.check_silence(t - 1.0)
	assert_eq(heard, [], "nothing before the boundary's phase began")
	a._run({"t": t, "kind": "phase", "ev": {"kind": "phase_start", "node": "warehouse.bar", "t": t, "phase": 2, "treatment": "none", "audio": d.nodes["warehouse.bar"]["audio"]}}, t, 0.0)
	a.check_silence(t)
	assert_eq(heard, [], "the old group is fading")
	assert_true(a.outgoing_sounding())
	a._started = true
	a._process(0.3)
	assert_eq(heard, [], "half way through the 0.6 s fade")
	a._process(0.31)
	assert_eq(heard, [t], "silent once the fade is over: reported with the boundary time")
	assert_eq(str(a.transition_log[a.transition_log.size() - 1]["kind"]), "silent")
	a._started = false
	a.stop()
	a.queue_free()


# --- the track audio's pins ---------------------------------------------------------------------------------------------------------

func test_a_pinned_destination_survives_the_doors_opening() -> void:
	Fx.clear()
	var dir_a := Fx.write_pack("seam_a", Fx.go_back_spec())
	var dir_b := Fx.write_pack("seam_b", Fx.go_back_spec())
	var ta := RunTrackAudio.new()
	tree.root.add_child(ta)
	var pa := {"dir": dir_a, "track": "seam_a", "pack": TrackPack.load_pack(dir_a, false)["pack"]}
	var pb := {"dir": dir_b, "track": "seam_b", "pack": TrackPack.load_pack(dir_b, false)["pack"]}
	ta._pinned[dir_a] = true
	ta._request(pa)
	ta._retain([pb])
	var guard := 0
	while ta.cached().values().has("loading") and guard < 2000:  # (the decodes done, so that letting go is not deferred to their end)
		guard += 1
		OS.delay_msec(5)
		ta._poll()
	assert_true(ta.cached().has(dir_a), "the pinned pack is kept when another scene's routes are prefetched")
	assert_true(ta.cached().has(dir_b))
	ta.release_pins()
	ta._retain([pb])
	assert_false(ta.cached().has(dir_a), "after release_pins the ordinary rule lets it go")
	for id in ta._tasks.duplicate():
		WorkerThreadPool.wait_for_task_completion(int(id))
	ta._tasks.clear()
	ta.queue_free()
	Fx.clear()


# --- the director in the run scene ---------------------------------------------------------------------------------------------------

func _run_scene(start: String) -> Dictionary:
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	Session.run_start_node = start
	var host := Control.new()
	host.size = Vector2(844, 390)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = Vector2(844, 390)
	return {"host": host, "scene": scene}


func _end_run(d: Dictionary, saved: RunProgress, path: String) -> void:
	(d["host"] as Control).queue_free()
	Session.run_progress = saved
	DirAccess.remove_absolute(path)
	OS.set_environment("RW_RUN_VIRTUAL", "")
	OS.set_environment("RW_RUN_BOT", "")


func test_every_scene_change_of_the_run_goes_through_the_port_in_order() -> void:
	var saved := Session.run_progress
	Session.run_progress = RunProgress.load_data("user://test_seam_save.json", "user://none.json")
	var d := _run_scene("")
	var scene: Node = d["scene"]
	var port: TransitionPort = scene.port()
	assert_true(port is TransitionDirector, "the run scene's port is the real director")
	var dir: TransitionDirector = port
	while scene.phase_log.size() < 4 and scene._vt < 600.0:
		scene._vt += 1.0 / 30.0
		scene._step_virtual(scene._vt)
	var t_end: float = scene._vt + 8.0  # (the last transition's fade, or its carried bass: 16 beats and the fade)
	while scene._vt < t_end:
		scene._vt += 1.0 / 30.0
		scene._step_virtual(scene._vt)
	var phases: Array = scene.phase_log
	assert_true(phases.size() >= 4, "four scenes played")
	var sw: Array = dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"switched")
	assert_eq(sw.size(), phases.size() - 1, "one switch per scene change")
	for i in sw.size():
		var landed: Dictionary = (sw[i]["args"] as Array)[1]
		assert_eq(str(landed["id"]), "main/" + str(phases[i + 1]["node"]), "switch %d lands on the scene the run entered" % i)
		assert_false(bool(landed.get("fallback", false)))
		assert_near(float((sw[i]["args"] as Array)[2]), float(phases[i + 1]["t"]), 1e-9, "on its downbeat")
	var names: Array = dir.log.map(func(e: Dictionary) -> StringName: return e["signal"]).filter(func(n: StringName) -> bool: return n != &"tempo_changed")
	var want: Array = []
	for i in sw.size():
		want.append_array([&"request_acknowledged", &"locked", &"switched", &"completed"])
	assert_eq(names.slice(0, want.size()), want, "acknowledged, locked, switched, completed, scene after scene")
	for e in dir.log.filter(func(x: Dictionary) -> bool: return x["signal"] == &"locked"):
		var la: Array = e["args"]
		assert_true(float(e["t"]) >= dir.lock_t(float(la[2])) - 1e-9 and float(e["t"]) <= dir.lock_t(float(la[2])) + 1.0 / 30.0 + 1e-6, "locked in the frame of the lock point")
		assert_eq((la[3] as Dictionary)["mode"], &"cut")
	_end_run(d, saved, "user://test_seam_save.json")


# --- one transition per destination and boundary (MUSIC_TRANSITIONS.md 8.3) ------------------------------------------------------------

## A geography exit's tap gives its route_commit before the lap's lock point (RunEngine.tap_commit, ruling 39: `t` is the boundary), and the lock point then reports the same route as the
## engine's own exit (_nothing_pending: leaving and chosen). The director locks once: one id, one `locked`. A genuinely new destination at that boundary still locks anew.
func test_a_tapped_exit_and_its_lock_point_lock_one_transition() -> void:
	var rig: RefCounted = (load("res://tests/fixtures/transition/director_rig.gd") as GDScript).new({"bpm": 174.0, "laps": 1, "doors_from_lap": 1, "lock_lead_beats": 3.5})
	var dir: TransitionDirector = rig.get("director")
	var eng: RunEngine = rig.get("engine")
	var ids: Array = []
	dir.locked.connect(func(id: int, _d: Dictionary, _b: float, _p: Dictionary) -> void: ids.append(id))
	var b := eng.t_of(eng.timing("phase_beats"))
	dir.on_event({"kind": "route_commit", "from": eng.node_id, "to": "a", "chosen": true, "t": b, "at": b - 8.0 * eng.beat_s, "tapped": true})
	assert_eq(ids.size(), 1, "the tap's route_commit locks the transition")
	var info := {"t": b - 3.5 * eng.beat_s, "boundary_t": b, "node": eng.node_id, "lap": 1, "laps": 1, "final": true, "departure": true, "passed": true, "hold": false, "track": true,
		"leaving": true, "route": "a", "chosen": true}
	dir._on_lock_point(info)
	assert_eq(ids, [1], "the lock point at the same boundary for the same destination emits no second locked")
	assert_eq(dir.lock_log.size(), 1, "one lock, one RUN transition line")
	assert_eq(dir.current().get("id", -1), 1, "the request is the first one, still locked")
	assert_eq(dir.state(), TransitionPort.State.LOCKED)
	info["route"] = "b"
	dir._on_lock_point(info)
	assert_eq(ids, [1, 2], "another destination at that boundary is a new lock, as before")
	assert_eq(str((dir.current().get("dest", {}) as Dictionary).get("id", "")), "main/b")
