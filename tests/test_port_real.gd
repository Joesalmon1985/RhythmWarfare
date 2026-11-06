extends TestCase
## The TransitionPort conformance cases (tests/port_conformance.gd) on the REAL director (TransitionDirector, `&"cut"` mode, stage M1.6) driving a real RunEngine on a virtual clock
## (tests/fixtures/transition/director_rig.gd), through the same factory shape as tests/test_port_mock.gd.
##
## Run here (14 of 15): 1 to 11, 13, 14 and 15. Case 14 (and the blend_beats of cases 1, 4 and 10) is staged by the rig as a blend of that many beats (director_rig._stage_blend).
## Not run, waiting for stage M2 or N2.2:
##   case 12 (`when == &"soonest"`): the engine leaves a scene only at a lap's end, never at a block boundary inside one; its only user, the Bassment entrance, is not behind the port
##           (lead ruling 20). The director takes "soonest" as "lap_end" (test_soonest_is_taken_at_the_lap_end below).

const Conf := preload("res://tests/port_conformance.gd")
const Rig := preload("res://tests/fixtures/transition/director_rig.gd")


static func _factory() -> Callable:
	return func(opts: Dictionary) -> Dictionary:
		var rig: RefCounted = Rig.new(opts)
		return {"port": rig.director, "advance": rig.advance, "switch": rig.switch, "rig": rig}


## Runs one case; it must skip nothing.
func _run_case(fn: Callable) -> void:
	Conf.skipped.clear()
	fn.call(self, _factory())
	assert_eq(Conf.skipped.size(), 0, "the real director's rig provides every switch this case needs; skipped: %s" % str(Conf.skipped))


func test_case_01_lifecycle() -> void:
	_run_case(Conf.case_01_lifecycle)


func test_case_02_replace() -> void:
	_run_case(Conf.case_02_replace)


func test_case_03_cancel_before_lock() -> void:
	_run_case(Conf.case_03_cancel_before_lock)


func test_case_04_refused_after_lock() -> void:
	_run_case(Conf.case_04_refused_after_lock)


func test_case_05_request_off_departure_lap() -> void:
	_run_case(Conf.case_05_request_off_departure_lap)


func test_case_06_default_locks() -> void:
	_run_case(Conf.case_06_default_locks)


func test_case_07_empty_default_stays() -> void:
	_run_case(Conf.case_07_empty_default_stays)


func test_case_08_unavailable() -> void:
	_run_case(Conf.case_08_unavailable)


func test_case_09_not_ready_defers_once() -> void:
	_run_case(Conf.case_09_not_ready_defers_once)


func test_case_10_failure_after_lock() -> void:
	_run_case(Conf.case_10_failure_after_lock)


func test_case_11_on_miss() -> void:
	_run_case(Conf.case_11_on_miss)


func test_case_13_clock_and_tempo() -> void:
	_run_case(Conf.case_13_clock_and_tempo)


func test_case_15_ids_increase() -> void:
	_run_case(Conf.case_15_ids_increase)


func test_case_14_blending_defers() -> void:
	_run_case(Conf.case_14_blending_defers)  # (stage M2.4: the rig stages a blend of 250 beats on the real director)


# --- the director's own readings, on the same rig ----------------------------------------------------------------------------------

func _rig() -> RefCounted:
	return Rig.new(Conf.OPTS.duplicate())


func _d(node: String, extra := {}) -> Dictionary:
	var d := {"id": "main/" + node, "path": "main", "node": node, "kind": &"scene", "quest": "", "when": &"lap_end"}
	d.merge(extra, true)
	return d


func _names(dir: TransitionDirector) -> Array:
	return dir.log.map(func(e: Dictionary) -> StringName: return e["signal"])


func test_every_plan_is_a_cut_with_exactly_the_contracts_keys() -> void:
	var rig := _rig()
	var dir: TransitionDirector = rig.director
	var id := dir.request(_d("a"))
	var guard := 0
	while not dir.log.any(func(e: Dictionary) -> bool: return e["signal"] == &"completed") and guard < 4000:
		guard += 1
		rig.advance(0.05)
	var locks: Array = dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"locked")
	assert_eq(locks.size(), 1)
	var plan: Dictionary = (locks[0]["args"] as Array)[3]
	var keys: Array = plan.keys()
	keys.sort()
	var want: Array = TransitionPlanner.plan_keys()
	want.sort()
	assert_eq(keys, want, "the Plan has the contract's keys and no recipe")
	assert_eq(plan["mode"], &"cut")
	assert_eq(int(plan["blend_beats"]), 0)
	assert_false(bool(plan["fallback"]))
	var b := float((locks[0]["args"] as Array)[2])
	assert_near(float(plan["complete_t"]), b + float(rig.data.cfg["mix"]["phase_fade_s"]), 1e-9, "complete_t = T + mix.phase_fade_s (a track scene into a track scene: no carried bass)")
	assert_near(float(plan["outgoing_bpm"]), 174.0, 1e-9)
	assert_near(float(plan["incoming_bpm"]), 174.0, 1e-9)
	var comp: Array = dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"completed")
	assert_near(float(comp[0]["t"]), float(plan["complete_t"]), 1.0 / 60.0 + 1e-9, "completed when the cut's fade is over (no audio: on the clock)")
	assert_eq(dir.lock_log[0]["recipe"]["mode"], &"cut", "the recipe goes to the audio, apart from the plan")
	assert_true(id > 0)


func test_the_engine_s_own_default_exit_goes_through_the_port() -> void:
	# Nothing requested and no default set: the final lap leaves by the scene's own default exit (today's run), and the director reports it as a transition under a fresh id.
	var rig := _rig()
	var dir: TransitionDirector = rig.director
	dir._default_set = false  # (as in the game before the narrative side sets defaults)
	var lap := 64.0 * dir.beat_s()
	var guard := 0
	while dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"completed").is_empty() and guard < 8000:
		guard += 1
		rig.advance(0.05)
	assert_eq(_names(dir), [&"request_acknowledged", &"locked", &"switched", &"completed"], "acknowledged and locked at the final lap's lock point, then the usual")
	var la: Array = dir.log[1]["args"]
	assert_eq(str((la[1] as Dictionary)["id"]), "main/dflt", "the scene's default exit")
	assert_near(float(la[2]), 4.0 * lap, 1e-6, "at the end of the final lap")
	assert_near(float(dir.log[1]["t"]), 4.0 * lap - 3.5 * dir.beat_s(), 1e-6, "at its lock point")
	assert_true(bool(dir.lock_log[0]["observed"]), "logged as the engine's own route")
	assert_eq(rig.engine.node_id, "dflt")


func test_a_request_wins_over_the_engines_route_and_the_hold_defers_it() -> void:
	var rig := _rig()
	var dir: TransitionDirector = rig.director
	var lap := 64.0 * dir.beat_s()
	rig.engine.hold = true
	var id := dir.request(_d("b"))
	rig.advance(2.0 * lap + 0.5)
	var defs: Array = dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"deferred")
	assert_eq(defs.size(), 1, "the lock point of lap 2 passes while a minigame holds the scene")
	assert_eq((defs[0]["args"] as Array)[2], &"held")
	assert_eq(dir.state(), TransitionPort.State.PENDING)
	rig.engine.hold = false
	var guard := 0
	while dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"switched").is_empty() and guard < 4000:
		guard += 1
		rig.advance(0.05)
	var sw: Array = dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"switched")
	assert_eq(sw.size(), 1)
	assert_eq(int((sw[0]["args"] as Array)[0]), id)
	assert_near(float((sw[0]["args"] as Array)[2]), 3.0 * lap, 1e-6, "the next departure lap, lap 3")
	assert_eq(rig.engine.node_id, "b", "the engine went where the port was asked to go")
	var tll: Array = rig.events.filter(func(ev: Dictionary) -> bool: return str(ev["kind"]) == "track_last_lap")
	assert_eq(tll.size(), 1, "the open lap became the last, as a touched exit makes it")


func test_a_completion_held_back_defers_the_next_lock_as_blending() -> void:
	var rig := _rig()
	var dir: TransitionDirector = rig.director
	dir.audio_reports_silence = true  # (as with audio: completed waits for the silence report)
	dir.silence_grace_s = 1.0e9
	var a := dir.request(_d("a"))
	var guard := 0
	while dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"switched").is_empty() and guard < 4000:
		guard += 1
		rig.advance(0.05)
	var b := dir.request(_d("b"))
	var lap := 64.0 * dir.beat_s()
	rig.advance(2.0 * lap)
	var defs: Array = dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"deferred")
	assert_true(defs.size() >= 1, "deferred while the last transition has not completed")
	for e in defs:
		assert_eq((e["args"] as Array)[2], &"blending")
	assert_eq(dir.state(), TransitionPort.State.PENDING)
	var t_b: float = float((dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"switched")[0]["args"] as Array)[2])
	dir.on_outgoing_silent(t_b)
	assert_eq(_names(dir).count(&"completed"), 1, "the silence report completes the first")
	guard = 0
	while dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"locked").size() < 2 and guard < 4000:
		guard += 1
		rig.advance(0.05)
	var locks: Array = dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"locked")
	assert_eq(int((locks[1]["args"] as Array)[0]), b, "then the second locks")
	assert_true(a > 0)


func test_soonest_is_taken_at_the_lap_end() -> void:
	var rig := _rig()
	var dir: TransitionDirector = rig.director
	var lap := 64.0 * dir.beat_s()
	var id := dir.request(_d("a", {"when": &"soonest"}))
	assert_true(id > 0, "accepted")
	assert_near(dir.next_boundary_t(), 2.0 * lap, 1e-6, "the first departure lap's end, not a block boundary")


func test_the_bassment_and_unknown_scenes_are_refused_at_once() -> void:
	var rig := _rig()
	var dir: TransitionDirector = rig.director
	assert_eq(dir.request({"id": "bassment/1", "path": "bassment", "node": "1", "kind": &"quest_entry", "quest": "bassment"}), 0)
	assert_eq(dir.last_refusal(), &"unavailable", "the Bassment is not behind the port in M1 (ruling 20)")
	assert_eq(dir.request({"id": "gospel/jordan", "path": "gospel", "node": "jordan", "kind": &"quest_entry", "quest": "gospel"}), 0, "no path data given to this rig")
	assert_eq(dir.request({"id": "x"}), 0)
	assert_eq(dir.last_refusal(), &"invalid")
	assert_eq(dir.state(), TransitionPort.State.NONE)


func test_the_excursion_closes_a_pending_request_and_nothing_locks_meanwhile() -> void:
	var rig := _rig()
	var dir: TransitionDirector = rig.director
	var lap := 64.0 * dir.beat_s()
	var id := dir.request(_d("a"))
	dir.excursion(&"armed")
	rig.advance(2.0 * lap - 1.0)
	assert_eq(_names(dir).count(&"locked"), 0, "armed: the lock point passes without a lock")
	assert_eq((dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"deferred")[0]["args"] as Array)[2], &"held")
	dir.excursion(&"enter")
	assert_eq((dir.log[dir.log.size() - 1]["args"] as Array), [id, &"cancelled"], "the pending request is closed when the Bassment takes the run")
	assert_false(dir.selection_open())
	assert_eq(dir.request(_d("b")), 0, "no request is taken in the Bassment")
	dir.excursion(&"leave")
	assert_true(dir.selection_open())
