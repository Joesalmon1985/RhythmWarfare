extends TestCase
## Runs the 15 TransitionPort conformance cases (tests/port_conformance.gd) on MockTransitionDirector.

const Conf := preload("res://tests/port_conformance.gd")


static func _factory() -> Callable:
	return func(opts: Dictionary) -> Dictionary:
		var m := MockTransitionDirector.new(float(opts["bpm"]), int(opts["laps"]), int(opts["doors_from_lap"]), float(opts["lock_lead_beats"]))
		var sw := func(name: StringName, value: Variant) -> bool:
			match name:
				&"fail_load_ids":
					m.fail_load_ids.assign(value)
				&"not_ready_ids":
					m.not_ready_ids.assign(value)
				&"fail_after_lock_ids":
					m.fail_after_lock_ids.assign(value)
				&"miss_last_block":
					m.miss_last_block = bool(value)
				&"blend_beats":
					m.blend_beats = int(value)
				&"scene_specs":
					m.scene_specs = (value as Dictionary).duplicate(true)
				_:
					return false
			return true
		return {"port": m, "advance": m.advance, "switch": sw, "mock": m}


## Runs one case and checks that the mock skipped nothing.
func _run_case(fn: Callable) -> void:
	Conf.skipped.clear()
	fn.call(self, _factory())
	assert_eq(Conf.skipped.size(), 0, "the mock provides every switch; skipped: %s" % str(Conf.skipped))


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


func test_case_12_soonest() -> void:
	_run_case(Conf.case_12_soonest)


func test_case_13_clock_and_tempo() -> void:
	_run_case(Conf.case_13_clock_and_tempo)


func test_case_14_blending_defers() -> void:
	_run_case(Conf.case_14_blending_defers)


func test_case_15_ids_increase() -> void:
	_run_case(Conf.case_15_ids_increase)


## Mock-only: the log holds every signal with its time, in emission order, and the constructor defaults are the contract's.
func test_mock_log_and_defaults() -> void:
	var m := MockTransitionDirector.new()
	assert_near(m.bpm(), 174.0, 1e-9)
	assert_near(m.lock_lead_beats, 3.5, 1e-9)
	assert_eq(m.state(), TransitionPort.State.NONE)
	assert_true(m.current().is_empty())
	assert_eq(m.request({"id": "x"}), 0, "malformed destination refused")
	assert_eq(m.last_refusal(), &"invalid")
	var id := m.request({"id": "main/a", "path": "main", "node": "a", "kind": &"scene"})
	assert_eq(id, 1)
	for i in 4000:
		m.advance(0.05)
	var names: Array = []
	for e in m.log:
		names.append(e["signal"])
		assert_true(e.has("args") and e.has("t"))
	assert_eq(names, [&"request_acknowledged", &"request_acknowledged", &"destination_ready", &"locked", &"switched", &"completed"])
	assert_near(float(m.log[3]["t"]), m.lock_t(float(m.log[3]["args"][2])), 1e-9, "log times are exact event times")
