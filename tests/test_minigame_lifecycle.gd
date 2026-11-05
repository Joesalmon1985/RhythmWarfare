extends TestCase
## The minigame lifecycle layer, pure: RunEngine.hold (the run stays at its scene while a minigame lives), the hotspot contract's `activity` key and per-scene cap, RunHotspots' activity
## outcome, and MinigameController (registry, request, seating on the downbeat, the failed-block rule, interruptions, the finish and determinism) with a fake activity.

const FAKE := "res://tests/fixtures/fake_minigame.gd"
const TMP := "user://test_minigame_registry"


# --- helpers ------------------------------------------------------------------------------------------------------------------

func _engine() -> RunEngine:
	var d := RunData.load_default()
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.begin("warehouse")
	return e


## Plays perfectly (every cue pressed on time, but the (phase, block) pairs in `miss`) until phase `until_phase` has started; `per_frame.call(engine, t)` runs before each update.
func _drive(e: RunEngine, until_phase: int, per_frame: Callable, miss: Array = []) -> Array:
	var events: Array = []
	var t := 0.0
	var pressed := {}
	var released := {}
	var guard := 0
	while e.phase_n < until_phase and not e.over and guard < 200000:
		guard += 1
		per_frame.call(e, t)
		events.append_array(e.update(t))
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			var skip := false
			for m in miss:
				if int(n["phase"]) == int(m[0]) and int(n["block"]) == int(m[1]):
					skip = true
			if skip:
				continue
			if not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]))
			if pressed.has(i) and n["type"] == "hold" and not released.has(i) and float(n["end_time"]) <= t:
				released[i] = true
				e.release(int(n["pad"]), float(n["end_time"]))
		t += 1.0 / 60.0
	return events


func _of_kind(events: Array, kind: String) -> Array:
	return events.filter(func(ev: Dictionary) -> bool: return str(ev["kind"]) == kind)


func _controller(wallet: Variant = null) -> MinigameController:
	var e := RunEngine.new(RunData.load_default())
	var c := MinigameController.new(e, wallet, 12345)
	c.register("fake", FakeMinigame)
	return c


# --- the engine's hold ----------------------------------------------------------------------------------------------------------

func test_hold_false_changes_nothing_two_runs_give_the_same_events() -> void:
	var a := _drive(_engine(), 4, func(_e: RunEngine, _t: float) -> void: pass)
	var e2 := _engine()
	assert_false(e2.hold, "off by default")
	var b := _drive(e2, 4, func(e: RunEngine, _t: float) -> void: e.hold = false)
	assert_eq(JSON.stringify(a), JSON.stringify(b), "an explicit false is the same run")
	var nodes: Array = _of_kind(a, "phase_start").map(func(ev: Dictionary) -> String: return str(ev["node"]))
	assert_true(nodes.size() >= 3 and nodes[0] == "warehouse" and nodes[1] != "warehouse", "the run leaves the scene as always: %s" % str(nodes))
	assert_eq(_of_kind(a, "hotspot_commit").size(), 3, "one commit per phase")


func test_held_phases_stay_at_the_scene_and_keep_charting_judging_and_timing() -> void:
	var e := _engine()
	var events := _drive(e, 5, func(en: RunEngine, t: float) -> void:
		en.hold = true
		if en.phase_n == 2 and en.phase_beat_at(t) > 50.0:
			en.hotspots.select("warehouse.exit_balcony", en.block, en.window_open))
	assert_eq(e.node_id, "warehouse")
	assert_eq(e.phase_n, 5, "phase_n advanced")
	var starts := _of_kind(events, "phase_start")
	assert_true(starts.size() >= 4, "the starts of phases 1 to 5")
	for i in starts.size():
		assert_eq(starts[i]["node"], "warehouse", "phase %d stays" % (i + 1))
		if i > 0:
			assert_eq(starts[i]["from"], "warehouse")
			assert_near(float(starts[i]["t"]) - float(starts[i - 1]["t"]), 64.0 * e.beat_s, 1e-9, "exactly 64 beats on")
	var commits := _of_kind(events, "route_commit")
	assert_eq(commits.size(), 4)
	for c in commits:
		assert_eq(c["to"], c["from"], "route_commit to == from")
	assert_eq(_of_kind(events, "hotspot_commit").size(), 0, "no hotspot commits while held (a selection is ignored)")
	var cues := _of_kind(events, "cues")
	for p in range(1, 5):
		for b in range(0, 4):
			assert_true(cues.any(func(c: Dictionary) -> bool: return int(c["phase"]) == p and int(c["block"]) == b and int(c["count"]) > 0), "cues of phase %d block %d" % [p, b])
	var results := _of_kind(events, "block_result")
	assert_eq(results.size(), 16, "four judged blocks per phase")
	assert_true(float((results[0] as Dictionary)["energy"]) != 60.0, "energy keeps moving")
	assert_true(e.level.notes.size() > 40, "notes keep being charted")


func test_releasing_the_hold_mid_phase_returns_the_scene_to_normal() -> void:
	var e := _engine()
	var events := _drive(e, 4, func(en: RunEngine, t: float) -> void:
		en.hold = en.phase_n == 1 or (en.phase_n == 2 and en.phase_beat_at(t) < 30.0))
	var starts := _of_kind(events, "phase_start").map(func(ev: Dictionary) -> String: return str(ev["node"]))
	assert_eq(starts.slice(0, 3), ["warehouse", "warehouse", "warehouse.bar"], "phase 1 held, phase 2 released at beat 30: it ends by the default route")
	var commits := _of_kind(events, "hotspot_commit")
	assert_eq(commits.size(), 2, "phase 2 and phase 3 commit")
	assert_eq(int(commits[0]["phase"]), 2, "the window opened normally in phase 2")
	assert_eq(str(commits[0]["outcome"]["route"]), "warehouse.bar")


func test_releasing_after_the_lock_keeps_the_next_phase_here_and_the_one_after_leaves() -> void:
	var e := _engine()
	var events := _drive(e, 4, func(en: RunEngine, t: float) -> void:
		en.hold = en.phase_n == 1 and en.phase_beat_at(t) < 62.0)
	var starts := _of_kind(events, "phase_start").map(func(ev: Dictionary) -> String: return str(ev["node"]))
	assert_eq(starts.slice(0, 3), ["warehouse", "warehouse", "warehouse.bar"], "released at beat 62, after the lock: the next phase is still this scene, the one after leaves")
	assert_eq(_of_kind(events, "hotspot_commit")[0]["phase"], 2, "phase 1 committed nothing")
	assert_eq((_of_kind(events, "route_commit")[0] as Dictionary)["to"], "warehouse")


# --- the contract -----------------------------------------------------------------------------------------------------------

func _hs(id: String, extra: Dictionary = {}) -> Dictionary:
	var h := {"id": "warehouse.t." + id, "world": "warehouse", "scene": "warehouse", "map": "night_one", "anchor": {"waypoint": "to_bar"}, "kind": "object", "on_success": {"flags_set": ["x"]},
		"on_failure": {"energy": -3}, "default": false}
	for k in extra:
		h[k] = extra[k]
	return h


func _scene_list(extra_objects: Array) -> Array:
	var list: Array = [_hs("a", {"kind": "exit", "default": true, "on_success": {"route": "warehouse.bar"}, "on_failure": {"route": "warehouse.bar"}}),
		_hs("b", {"kind": "exit", "anchor": {"waypoint": "to_balcony"}, "on_success": {"route": "warehouse.balcony"}, "on_failure": {"route": "warehouse.balcony"}})]
	list.append_array(extra_objects)
	return list


func _validate(list: Array, extra_ctx: Dictionary = {}) -> Array:
	var errors: Array = []
	var ctx := {"where": "scene warehouse", "map": "night_one", "world": "warehouse", "routes": ["warehouse.bar", "warehouse.balcony"], "start_energy": 60.0, "default_route": "warehouse.bar"}
	for k in extra_ctx:
		ctx[k] = extra_ctx[k]
	HotspotContract.validate_scene(list.map(func(h: Dictionary) -> Dictionary: return HotspotContract.normalize(h, "warehouse", "night_one")), ctx, errors)
	return errors


func _has(errors: Array, needle: String) -> bool:
	return errors.any(func(e: String) -> bool: return e.contains(needle))


func test_activity_is_accepted_in_on_success_and_carried_through_normalize() -> void:
	var table := _hs("table", {"on_success": {"activity": "fake"}})
	assert_eq(_validate(_scene_list([table]), {"activities": ["fake"]}), [], "valid")
	assert_eq(_validate(_scene_list([table])), [], "valid with no registry given")
	assert_eq(HotspotContract.normalize(table, "warehouse", "night_one")["on_success"]["activity"], "fake", "normalize leaves it alone")


func test_activity_is_rejected_in_on_failure_with_a_route_empty_or_unknown() -> void:
	assert_true(_has(_validate(_scene_list([_hs("t", {"on_failure": {"activity": "fake"}})]), {"activities": ["fake"]}), "only allowed in on_success"))
	assert_true(_has(_validate(_scene_list([_hs("t", {"on_success": {"activity": "fake", "route": "warehouse.bar"}})]), {"activities": ["fake"]}), "cannot be combined with a route"))
	assert_true(_has(_validate(_scene_list([_hs("t", {"on_success": {"activity": "nope"}})]), {"activities": ["fake"]}), "not a registered minigame"))
	assert_true(_has(_validate(_scene_list([_hs("t", {"on_success": {"activity": ""}})])), "non-empty string"))
	assert_true(_has(_validate(_scene_list([_hs("t", {"on_success": {"activity": "fake"}})]), {"activities": []}), "not a registered minigame"), "an empty registry knows nothing")


func test_a_scene_may_raise_its_cap_and_the_default_stays_four() -> void:
	var five := _scene_list([_hs("c"), _hs("d"), _hs("e")])
	assert_eq(five.size(), 5)
	assert_true(_has(_validate(five), "available at the start"), "five hotspots break the default cap of 4")
	assert_eq(_validate(five, {"max_available": 5}), [], "max_available 5 allows five")
	assert_true(_has(_validate(five, {"max_available": 4}), "available at the start"))


# --- RunHotspots ------------------------------------------------------------------------------------------------------------

func _hotspot_engine(repeatable: bool) -> RunHotspots:
	var exit_h := HotspotContract.normalize({"id": "a", "scene": "s", "kind": "exit", "anchor": {"waypoint": "x"}, "default": true, "on_success": {"route": "to_default"}, "on_failure": {"route": "to_default"}}, "w", "m")
	var table := HotspotContract.normalize({"id": "table", "scene": "s", "kind": "object", "anchor": {"waypoint": "x"}, "repeatable": repeatable, "on_success": {"activity": "fake"}, "on_failure": {"energy": -4}}, "w", "m")
	var d := RunData.new()
	d.hotspots = {"s": [exit_h, table]}
	var hs := RunHotspots.new(d, {}, {})
	hs.begin_scene("s", 60.0)
	return hs


func test_an_activity_outcome_stays_at_the_scene() -> void:
	var hs := _hotspot_engine(true)
	assert_true(hs.select("table", 3, true))
	var out := hs.commit_final(true)
	assert_eq(out["activity"], "fake")
	assert_eq(out["route"], "s", "the scene itself")
	assert_true(bool(out["stays"]))
	assert_false(bool(out["continued"]))
	assert_false(hs.spent.has("table"), "a repeatable table is not used up")
	hs.begin_scene("s", 60.0)
	assert_true(hs.is_shown("table", 3, true), "available again in a later phase")


func test_a_missed_last_block_is_the_failure_outcome_without_the_activity() -> void:
	var hs := _hotspot_engine(true)
	hs.select("table", 3, true)
	var out := hs.commit_final(false)
	assert_eq(out["activity"], "")
	assert_false(bool(out["stays"]))
	assert_eq(out["route"], "to_default", "the dealer waves you off: the default exit")
	assert_true(bool(out["continued"]))


func test_a_table_that_is_not_repeatable_is_used_up_once_sat_at() -> void:
	var hs := _hotspot_engine(false)
	hs.select("table", 3, true)
	hs.commit_final(true)
	assert_true(hs.spent.has("table"))


# --- the controller -----------------------------------------------------------------------------------------------------------

func test_request_enter_begin_at_the_seat_time_then_active() -> void:
	var c := _controller()
	assert_true(c.request("fake", 10.0, 12.0))
	assert_eq(c.state, "entering")
	assert_true(c.engine.hold, "the run is held from the request")
	assert_true(c.active())
	var a := c.activity as FakeMinigame
	c.update(11.99)
	assert_eq(a.count("begin"), 0, "not before the seat time")
	assert_eq(c.state, "entering")
	c.update(12.01)
	assert_eq(a.count("begin"), 1)
	assert_eq(float(a.calls[1]["t"]), 12.0, "begin is given the seat time exactly")
	assert_eq(c.state, "active")
	assert_near(a.last_update, 12.01, 1e-9, "and the activity is advanced")


func test_unknown_ids_and_a_second_request_are_refused() -> void:
	var c := _controller()
	assert_false(c.request("nope", 1.0, 2.0))
	assert_eq(c.state, "")
	assert_false(c.engine.hold, "a refused request holds nothing")
	assert_true(c.request("fake", 1.0, 2.0))
	assert_false(c.request("fake", 1.5, 2.0), "one at a time")


func test_two_failed_blocks_wobble_a_pass_steadies_and_three_fall_once() -> void:
	var c := _controller()
	c.request("fake", 0.0, 1.0)
	var a := c.activity as FakeMinigame
	c.update(1.0)
	c.on_block_result(false, 2.0)
	assert_eq(a.count("wobble"), 0, "one miss is nothing")
	c.on_block_result(false, 3.0)
	assert_eq(a.wobble, 1, "two in a row wobble")
	c.on_block_result(true, 4.0)
	assert_eq(a.wobble, 0, "a pass steadies")
	c.on_block_result(false, 5.0)
	c.on_block_result(false, 6.0)
	assert_eq(a.wobble, 1, "the count restarted after the pass")
	c.on_block_result(false, 7.0)
	assert_eq(a.count("interrupt"), 1)
	assert_eq(a.calls.filter(func(x: Dictionary) -> bool: return x["call"] == "interrupt")[0]["reason"], "fall")
	c.on_block_result(false, 8.0)
	assert_eq(a.count("interrupt"), 1, "exactly once")
	assert_eq(c.state, "leaving")


func test_the_thresholds_come_from_the_activitys_config() -> void:
	var c := _controller()
	c.register("tight", FakeMinigame, {"wobble_at": 1, "fall_at": 2})
	c.request("tight", 0.0, 1.0)
	var a := c.activity as FakeMinigame
	c.update(1.0)
	c.on_block_result(false, 2.0)
	assert_eq(a.wobble, 1)
	c.on_block_result(false, 3.0)
	assert_eq(a.count("interrupt"), 1)


func test_results_before_begin_and_after_done_are_ignored() -> void:
	var c := _controller()
	c.request("fake", 0.0, 10.0)
	var a := c.activity as FakeMinigame
	c.on_block_result(false, 1.0)
	c.on_block_result(false, 2.0)
	c.on_block_result(false, 3.0)
	assert_eq(a.count("wobble") + a.count("interrupt"), 0, "nothing counts while entering")
	c.update(10.0)
	a.finish_now = true
	c.update(10.5)
	assert_eq(c.state, "")
	c.on_block_result(false, 11.0)
	c.on_block_result(false, 12.0)
	c.on_block_result(false, 13.0)
	assert_eq(a.count("interrupt"), 0, "nothing counts once it is over")
	assert_false(c.tap("bet", 14.0))


func test_run_over_interrupts_a_seated_player_and_drops_an_unseated_one() -> void:
	var c := _controller()
	c.request("fake", 0.0, 1.0)
	var a := c.activity as FakeMinigame
	c.update(1.0)
	c.on_run_over(5.0)
	assert_eq(a.calls[a.calls.size() - 1], {"call": "interrupt", "reason": "run_over", "t": 5.0})
	c.update(5.1)
	assert_eq(c.state, "", "the interrupted activity reports done")
	assert_false(c.engine.hold)
	assert_eq((c.log[c.log.size() - 1] as Dictionary)["reason"], "run_over")
	var c2 := _controller()
	c2.request("fake", 0.0, 10.0)
	var b := c2.activity as FakeMinigame
	c2.on_run_over(5.0)
	assert_eq(b.count("interrupt"), 0, "never seated: nothing to refund, never begun")
	assert_eq(b.count("begin"), 0)
	assert_eq(c2.state, "")
	assert_false(c2.engine.hold)


func test_done_releases_the_hold_and_logs_finished_with_the_reason() -> void:
	var c := _controller()
	c.request("fake", 0.0, 1.0)
	var a := c.activity as FakeMinigame
	c.update(1.0)
	assert_true(c.engine.hold)
	a.finish_now = true
	c.update(2.0)
	assert_false(c.engine.hold)
	assert_eq(c.state, "")
	assert_false(c.active())
	assert_eq(c.activity, null)
	assert_eq(c.log[c.log.size() - 1], {"kind": "finished", "reason": "host", "t": 2.0})
	assert_true(c.request("fake", 3.0, 4.0), "a new one may start")


func test_taps_are_forwarded_only_while_seated_and_leaving_through_the_exit_finishes() -> void:
	var c := _controller()
	c.request("fake", 0.0, 5.0)
	var a := c.activity as FakeMinigame
	assert_false(c.tap("bet", 1.0), "not while entering")
	assert_eq(a.count("tap"), 0)
	c.update(5.0)
	assert_true(c.tap("bet", 6.0))
	assert_false(c.tap("zzz", 7.0), "an untouchable target is refused by the activity")
	assert_eq(a.count("tap"), 2)
	assert_true(c.tap("exit", 8.0))
	c.update(8.1)
	assert_eq(c.state, "")
	assert_eq((c.log[c.log.size() - 1] as Dictionary)["reason"], "left")


func test_the_same_calls_give_the_same_log() -> void:
	var run := func() -> String:
		var c := _controller()
		c.request("fake", 1.0, 2.0)
		c.update(2.5)
		c.tap("bet", 3.0)
		c.on_block_result(false, 4.0)
		c.on_block_result(false, 5.0)
		c.on_block_result(true, 6.0)
		c.tap("exit", 7.0)
		c.update(7.5)
		return JSON.stringify(c.log)
	assert_eq(run.call(), run.call())


func test_the_seed_is_stable_derived_per_start_and_overridable_by_the_environment() -> void:
	OS.unset_environment("RW_MINIGAME_SEED")
	var c1 := _controller()
	c1.request("fake", 0.0, 1.0)
	var c2 := _controller()
	c2.request("fake", 0.0, 1.0)
	assert_eq(c1.last_seed, c2.last_seed, "same run seed, same first seed")
	assert_eq(int((c1.activity as FakeMinigame).ctx_seen["seed"]), c1.last_seed, "handed to the activity")
	(c1.activity as FakeMinigame).finish_now = true
	c1.update(1.0)
	var first := c1.last_seed
	c1.request("fake", 2.0, 3.0)
	assert_true(c1.last_seed != first, "the second start derives another")
	var c3 := MinigameController.new(RunEngine.new(RunData.load_default()), null, 999)
	c3.register("fake", FakeMinigame)
	c3.request("fake", 0.0, 1.0)
	assert_true(c3.last_seed != first, "another run seed, another stream")
	OS.set_environment("RW_MINIGAME_SEED", "4242")
	var c4 := _controller()
	c4.request("fake", 0.0, 1.0)
	OS.unset_environment("RW_MINIGAME_SEED")
	assert_eq(c4.last_seed, 4242, "the environment wins")
	assert_eq(int((c4.activity as FakeMinigame).ctx_seen["seed"]), 4242)


func test_the_registry_reads_json_files_and_a_missing_directory_is_empty() -> void:
	assert_eq(MinigameController.registered_ids("res://content/no_such_minigames_dir"), [])
	var c := MinigameController.new(null)
	c.load_registry("res://content/no_such_minigames_dir")
	assert_false(c.request("fake", 0.0, 1.0), "nothing registered")
	DirAccess.make_dir_recursive_absolute(TMP)
	var f := FileAccess.open(TMP + "/table.json", FileAccess.WRITE)
	f.store_string(JSON.stringify({"id": "table", "script": FAKE, "fall_at": 5}))
	f.close()
	assert_eq(MinigameController.registered_ids(TMP), ["table"])
	c.load_registry(TMP)
	assert_true(c.request("table", 0.0, 1.0), "the script path is loaded")
	assert_eq(int((c.activity as FakeMinigame).config["fall_at"]), 5, "the whole JSON is the activity's config")
	DirAccess.remove_absolute(TMP + "/table.json")
	DirAccess.remove_absolute(TMP)
	assert_true(c.request("fake", 0.0, 1.0) == false, "one at a time still")
