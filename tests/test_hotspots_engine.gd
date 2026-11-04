extends TestCase
## The hotspot engine (RunHotspots) alone and inside RunEngine: availability from flags and energy, selection and change until the commit, the commit at the last decision beat (the route lock),
## success and failure outcomes, the default exit, world state, and determinism at 30 fps, 60 fps and a variable frame step with scripted taps at song times.


func _h(id: String, extra: Dictionary = {}) -> Dictionary:
	var h := {"id": id, "scene": "s", "kind": "exit", "anchor": {"waypoint": "x"}, "on_success": {"route": "to_" + id}, "on_failure": {"route": "to_default"}}
	for k in extra:
		h[k] = extra[k]
	return HotspotContract.normalize(h, "w", "m")


func _engine_for(list: Array, run_flags: Dictionary = {}, flags: Dictionary = {}) -> RunHotspots:
	var d := RunData.new()
	d.hotspots = {"s": list}
	var hs := RunHotspots.new(d, run_flags, flags)
	hs.begin_scene("s", 60.0)
	return hs


func _basic() -> Array:
	return [_h("a", {"default": true, "on_success": {"route": "to_default"}}), _h("b"), _h("c", {"kind": "object", "on_success": {"flags_set": ["got_c"], "energy": 5}, "on_failure": {"flags_set": ["lost_c"], "energy": -4}})]


func test_availability_reads_flags_and_energy() -> void:
	var rf := {}
	var hs := _engine_for([_h("a", {"default": true}), _h("needs", {"available": {"flags_all": ["key"]}}), _h("hidden", {"available": {"flags_none": ["seen"]}}), _h("tired", {"available": {"energy_min": 70}})], rf)
	var ids := func() -> Array: return hs.shown(3, true).map(func(h: Dictionary) -> String: return str(h["id"]))
	assert_eq(ids.call(), ["a", "hidden"], "no key, not seen, energy 60 < 70")
	rf["key"] = true
	assert_eq(ids.call(), ["a", "needs", "hidden"])
	hs.flags["keep:seen"] = true
	rf["seen"] = true
	assert_eq(ids.call(), ["a", "needs"], "a flag (run or persistent) hides a flags_none hotspot")
	hs.energy = 80.0
	assert_eq(ids.call(), ["a", "needs", "tired"])


func test_windows_the_final_window_opens_with_the_route_window_and_the_early_one_is_the_wizards() -> void:
	var hs := _engine_for([_h("a", {"default": true}), _h("wiz", {"kind": "character", "on_success": {"route": "trial:1"}})])
	assert_eq(hs.shown(0, false).size(), 1, "block 0: only the wizard (early)")
	assert_eq(hs.shown(0, false)[0]["id"], "wiz")
	assert_eq(hs.shown(2, false).size(), 0, "blocks 3 and on: the early window is shut, the final one not yet open")
	assert_eq(hs.shown(3, true).map(func(h: Dictionary) -> String: return str(h["id"])), ["a"])
	assert_false(hs.select("a", 1, false), "the final hotspot cannot be selected before the window opens")
	assert_true(hs.select("wiz", 1, false))
	assert_false(hs.select("wiz", 2, false), "too late to arm the Bassment")


func test_selection_changes_until_the_commit_and_cannot_select_what_is_not_shown() -> void:
	var hs := _engine_for(_basic() + [_h("gated", {"available": {"flags_all": ["k"]}})])
	assert_false(hs.select("gated", 3, true), "an unavailable hotspot cannot be touched")
	assert_false(hs.select("nope", 3, true))
	assert_eq(hs.state_of("b", 3, true), "available")
	assert_true(hs.select("b", 3, true))
	assert_eq(hs.state_of("b", 3, true), "selected")
	assert_true(hs.select("c", 3, true), "change your mind")
	assert_eq(hs.state_of("b", 3, true), "available")
	assert_eq(hs.state_of("c", 3, true), "selected")
	assert_true(hs.select_route("to_b", 3, true))
	assert_eq(hs.selected, "b")
	assert_true(hs.select_index(2, 3, true))
	assert_eq(hs.selected, "c")
	assert_false(hs.select_index(7, 3, true))
	var out := hs.commit_final(true)
	assert_eq(hs.state_of("c", 3, true), "committed")
	assert_false(hs.select("b", 3, true), "nothing can be selected after the commit")
	assert_eq(out["hotspot"], "c")


func test_commit_success_failure_and_default() -> void:
	var hs := _engine_for(_basic())
	hs.select("b", 3, true)
	var ok := hs.commit_final(true)
	assert_eq([ok["success"], ok["route"], ok["tapped"]], [true, "to_b", true])
	hs.begin_scene("s", 60.0)
	hs.select("b", 3, true)
	var bad := hs.commit_final(false)
	assert_eq([bad["success"], bad["route"]], [false, "to_default"], "a miss takes the failure route")
	hs.begin_scene("s", 60.0)
	var none := hs.commit_final(false)
	assert_eq([none["hotspot"], none["route"], none["tapped"], none["defaulted"]], ["a", "to_default", false, true], "nothing tapped: the default exit even after a miss")
	hs.begin_scene("s", 60.0)
	hs.select("c", 3, true)
	var obj := hs.commit_final(true)
	assert_eq(obj["route"], "to_default", "an object with no route continues by the default exit")
	assert_true(obj["continued"])
	assert_eq(obj["energy"], 5.0)


func test_outcomes_set_world_state_per_run_and_persistent() -> void:
	var rf := {}
	var pf := {}
	var hs := _engine_for([_h("a", {"default": true}), _h("o", {"kind": "object", "on_success": {"flags_set": ["drink", "keep:met_dj"]}, "on_failure": {"flags_set": ["spill"]}})], rf, pf)
	hs.select("o", 3, true)
	hs.commit_final(true)
	assert_true(rf.has("drink") and not rf.has("keep:met_dj"), "a plain flag lasts the run")
	assert_true(pf.has("keep:met_dj"), "a keep: flag persists")
	assert_true(hs.persist_dirty)
	hs.begin_scene("s", 60.0)
	hs.select("o", 3, true)
	assert_false(hs.select("o", 3, true), "a successful non-repeatable object is spent for the run")
	var rf2 := {}
	var hs2 := _engine_for([_h("a", {"default": true}), _h("o", {"kind": "object", "on_success": {"flags_set": ["drink"]}, "on_failure": {"flags_set": ["spill"]}})], rf2)
	hs2.select("o", 3, true)
	hs2.commit_final(false)
	assert_true(rf2.has("spill") and not rf2.has("drink"))
	hs2.begin_scene("s", 60.0)
	assert_true(hs2.select("o", 3, true), "a failed one can be tried again")
	var hs3 := _engine_for([_h("a", {"default": true}), _h("o", {"kind": "object", "repeatable": true, "on_success": {"flags_set": ["drink"]}})])
	hs3.select("o", 3, true)
	hs3.commit_final(true)
	hs3.begin_scene("s", 60.0)
	assert_true(hs3.select("o", 3, true), "a repeatable one stays")
	var hs4 := _engine_for([_h("a", {"default": true}), _h("e", {"on_success": {"route": "to_e"}, "available": {"once": true}})])
	hs4.select("e", 3, true)
	hs4.commit_final(true)
	hs4.begin_scene("s", 60.0)
	assert_false(hs4.select("e", 3, true), "once: used up by any commit")


func test_the_early_window_commits_at_the_next_block_decision_and_expires() -> void:
	var hs := _engine_for([_h("a", {"default": true}), _h("wiz", {"kind": "character", "repeatable": true, "on_success": {"route": "trial:1"}, "on_failure": {"flags_set": ["shrug"]}})])
	assert_eq(hs.on_block(0, true), {}, "nothing selected, nothing commits")
	hs.select("wiz", 0, false)
	var miss := hs.on_block(0, false)
	assert_eq([miss["success"], miss["route"], miss["window"]], [false, "", "early"])
	assert_true(hs.has_flag("shrug"))
	assert_eq(hs.state_of("wiz", 1, false), "available", "repeatable: he waits again after a miss")
	hs.select("wiz", 1, false)
	var ok := hs.on_block(1, true)
	assert_eq(ok["route"], "trial:1")
	assert_eq(hs.state_of("wiz", 1, false), "committed")
	var hs2 := _engine_for([_h("a", {"default": true}), _h("wiz", {"kind": "character", "on_success": {"route": "trial:1"}})])
	hs2.select("wiz", 1, false)
	assert_eq(hs2.on_block(2, true), {}, "block 3 is too late")
	assert_eq(hs2.selected, "", "and the selection lapses")


# --- inside the run engine ---------------------------------------------------------------------------------------------------

## Plays the Warehouse floor perfectly (except the listed blocks) on a given frame step with taps at song times: [{beat, route | id}]. Returns what happened.
func _play(step: Callable, taps: Array, miss: Array = [], until_phase := 2, run_flags: Dictionary = {}, start := "warehouse") -> Dictionary:
	var d := RunData.load_default()
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, run_flags, {})
	e.begin(start)
	var t := 0.0
	var pressed := {}
	var released := {}
	var done := {}
	var commits: Array = []
	var nodes: Array = [start]
	var guard := 0
	while e.phase_n < until_phase and not e.over and guard < 200000:
		guard += 1
		for i in taps.size():
			var tp: Dictionary = taps[i]
			if not done.has(i) and t >= e.t_of(float(tp["beat"])) and int(tp.get("phase", 1)) == e.phase_n:
				done[i] = true
				if tp.has("route"):
					e.hotspots.select_route(str(tp["route"]), e.block, e.window_open)
				else:
					e.hotspots.select(str(tp["id"]), e.block, e.window_open)
		for ev in e.update(t):
			if str(ev["kind"]) == "hotspot_commit":
				commits.append({"hotspot": ev["outcome"]["hotspot"], "success": ev["outcome"]["success"], "route": ev["outcome"]["route"], "t": snappedf(float(ev["t"]), 0.0001), "energy": snappedf(float(ev["energy"]), 0.001)})
			if str(ev["kind"]) == "phase_start" and int(ev["phase"]) > 1:
				nodes.append(str(ev["node"]))
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
		t += float(step.call(guard))
	return {"commits": commits, "nodes": nodes, "energy": snappedf(e.energy, 0.001), "engine": e, "log": e.hotspots.log}


func test_a_tap_commits_at_the_last_decision_beat_and_the_route_follows() -> void:
	var r := _play(func(_i: int) -> float: return 1.0 / 60.0, [{"beat": 50.0, "route": "warehouse.balcony"}])
	assert_eq(r["nodes"], ["warehouse", "warehouse.balcony"], "a perfect last block: the tapped exit")
	var c: Dictionary = (r["commits"] as Array)[0]
	var e: RunEngine = r["engine"]
	var dec := e.timing("decision_beat")
	assert_true(float(c["t"]) >= e.beat_s * (48.0 + dec) - 0.001 and float(c["t"]) <= e.beat_s * (48.0 + 13.0), "committed at the last block's decision beat, in the cue-free guard before beat 61: %s" % str(c["t"]))
	assert_true(float(c["t"]) < e.beat_s * 61.0, "before the door walk starts")


func test_changing_the_tap_counts_until_the_commit_and_a_late_tap_does_not() -> void:
	var r := _play(func(_i: int) -> float: return 1.0 / 60.0, [{"beat": 49.5, "route": "warehouse.bar"}, {"beat": 56.0, "route": "warehouse.balcony"}])
	assert_eq(r["nodes"][1], "warehouse.balcony", "the second tap replaced the first")
	r = _play(func(_i: int) -> float: return 1.0 / 60.0, [{"beat": 49.5, "route": "warehouse.balcony"}, {"beat": 62.0, "route": "warehouse.bar"}])
	assert_eq(r["nodes"][1], "warehouse.balcony", "a tap after the commit changes nothing")


func test_nothing_tapped_takes_the_default_exit_and_a_miss_in_the_last_block_takes_the_failure_route() -> void:
	var r := _play(func(_i: int) -> float: return 1.0 / 60.0, [])
	assert_eq(r["nodes"][1], "warehouse.bar", "the default")
	r = _play(func(_i: int) -> float: return 1.0 / 60.0, [{"beat": 52.0, "route": "warehouse.balcony"}], [[1, 3]])
	assert_eq(r["nodes"][1], "warehouse.bar", "tapped the balcony, missed the last block: the failure route (the bar)")
	assert_false(bool((r["commits"] as Array)[0]["success"]))
	var ok := _play(func(_i: int) -> float: return 1.0 / 60.0, [{"beat": 52.0, "route": "warehouse.balcony"}])
	assert_true(float(r["energy"]) < float(ok["energy"]), "the miss cost energy (the block's and the hotspot's)")
	r = _play(func(_i: int) -> float: return 1.0 / 60.0, [], [[1, 3]])
	assert_eq(r["nodes"][1], "warehouse.bar", "no tap, a miss: still the default, not a punishment")
	assert_true(bool((r["log"] as Array)[0]["defaulted"]))


func test_an_object_hotspot_sets_flags_and_energy_and_the_scene_continues_by_the_default() -> void:
	var rf := {}
	var r := _play(func(_i: int) -> float: return 1.0 / 60.0, [{"beat": 52.0, "id": "warehouse.floor.dancer"}], [], 2, rf)
	assert_true(rf.has("danced_with"), "the success flag is set")
	assert_eq(r["nodes"][1], "warehouse.bar", "continued by the default exit")
	var c: Dictionary = (r["commits"] as Array)[0]
	assert_true(bool(c["success"]))
	rf = {}
	r = _play(func(_i: int) -> float: return 1.0 / 60.0, [{"beat": 52.0, "id": "warehouse.floor.dancer"}], [[1, 3]], 2, rf)
	assert_true(rf.has("stumbled") and not rf.has("danced_with"), "a miss: the failure flag")


func test_the_same_taps_give_the_same_outcomes_at_any_frame_step() -> void:
	var taps := [{"beat": 50.0, "route": "warehouse.bar"}, {"beat": 55.0, "route": "warehouse.balcony"}, {"beat": 56.5, "id": "warehouse.floor.dancer"}]
	var fns := {
		"30": func(_i: int) -> float: return 1.0 / 30.0,
		"60": func(_i: int) -> float: return 1.0 / 60.0,
		"variable": func(i: int) -> float: return [0.007, 0.033, 0.016, 0.051, 0.011][i % 5],
	}
	var results: Array = []
	for k in fns:
		var rf := {}
		var r := _play(fns[k], taps, [[1, 1]], 3, rf)
		results.append([r["nodes"], (r["commits"] as Array).map(func(c: Dictionary) -> Array: return [c["hotspot"], c["success"], c["route"]]), r["energy"], rf.keys()])
	assert_eq(results[0], results[1], "30 fps and 60 fps agree")
	assert_eq(results[0], results[2], "and a variable frame step")
	assert_true((results[0][1] as Array).size() >= 2, "more than one commit was exercised")


func test_run_flags_clear_each_run_and_keep_flags_persist_in_the_save() -> void:
	var path := "user://test_hotspots_flags.json"
	for f in [path, path + ".tmp"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	var p := RunProgress.load_data(path, "user://none.json")
	assert_true(p.set_flag("drink"))
	assert_true(p.set_flag("keep:met_dj"))
	assert_false(p.set_flag("drink"), "already set")
	assert_true(p.has_flag("drink") and p.has_flag("keep:met_dj"))
	var again := RunProgress.load_data(path, "user://none.json")
	assert_true(again.has_flag("keep:met_dj"), "the discovery was saved")
	assert_false(again.has_flag("drink"), "the per-run flag was not")
	p.run_started()
	assert_false(p.has_flag("drink"), "a new run clears the run flags")
	assert_true(p.has_flag("keep:met_dj"))
	for f in [path, path + ".tmp"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
