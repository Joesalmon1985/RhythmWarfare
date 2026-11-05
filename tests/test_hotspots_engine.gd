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
	assert_eq(r["nodes"][1], "warehouse.balcony", "tapped the balcony, missed the last block: the same door again (a stagger and -5 energy)")
	assert_false(bool((r["commits"] as Array)[0]["success"]))
	var ok := _play(func(_i: int) -> float: return 1.0 / 60.0, [{"beat": 52.0, "route": "warehouse.balcony"}])
	assert_true(float(r["energy"]) < float(ok["energy"]), "the miss cost energy (the block's and the hotspot's)")
	r = _play(func(_i: int) -> float: return 1.0 / 60.0, [], [[1, 3]])
	assert_eq(r["nodes"][1], "warehouse.bar", "no tap, a miss: still the default, not a punishment")
	assert_true(bool((r["log"] as Array)[0]["defaulted"]))


func test_an_object_hotspot_sets_flags_and_energy_and_the_scene_continues_by_the_default() -> void:
	var rf := {}
	var r := _play(func(_i: int) -> float: return 1.0 / 60.0, [{"beat": 52.0, "id": "warehouse.dancer"}], [], 2, rf)
	assert_true(rf.has("wh_circle"), "the success flag is set")
	assert_eq(r["nodes"][1], "warehouse.bar", "continued by the default exit")
	var c: Dictionary = (r["commits"] as Array)[0]
	assert_true(bool(c["success"]))
	rf = {}
	r = _play(func(_i: int) -> float: return 1.0 / 60.0, [{"beat": 52.0, "id": "warehouse.dancer"}], [[1, 3]], 2, rf)
	assert_false(rf.has("wh_circle"), "a miss: no circle")


func test_the_same_taps_give_the_same_outcomes_at_any_frame_step() -> void:
	var taps := [{"beat": 50.0, "route": "warehouse.bar"}, {"beat": 55.0, "route": "warehouse.balcony"}, {"beat": 56.5, "id": "warehouse.dancer"}]
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


## Every shipped hotspot of the seven run worlds resolves both ways through the engine: success and failure each give an outcome whose route (when it names one) is a route of the scene or the
## Bassment's first passage, whose flags are applied to the right store, and an object or feature that names no route continues by the scene's default exit (the coverage matrix's S and F columns).
func test_every_shipped_hotspot_resolves_its_success_and_failure_outcomes() -> void:
	var d := RunData.load_default()
	assert_true(d.errors.is_empty())
	var n := 0
	for node_id in d.nodes:
		var routes: Array = (d.nodes[node_id]["next"] as Array).map(func(o: Dictionary) -> String: return str(o["to"]))
		for h in d.hotspots_of(node_id):
			for success in [true, false]:
				var run_flags := {}
				var flags := {}
				for f in (h["available"]["flags_all"] as Array):
					run_flags[str(f)] = true
				var hs := RunHotspots.new(d, run_flags, flags)
				hs.begin_scene(node_id, 60.0)
				var out: Dictionary
				if RunHotspots.window_of(h) == "early":
					hs.selected = str(h["id"])
					out = hs.on_block(0, success)
				else:
					hs.selected = str(h["id"])
					out = hs.commit_final(success)
				assert_false(out.is_empty(), "%s resolves (%s)" % [h["id"], str(success)])
				var r := str(out["route"])
				if r != "":
					assert_true(r in routes or HotspotContract.is_trial_route(r), "%s %s: route %s is a route of %s" % [h["id"], str(success), r, node_id])
				for f in out["flags_set"]:
					assert_true(run_flags.has(str(f)) or flags.has(str(f)), "%s: flag %s is applied" % [h["id"], f])
				n += 1
	assert_true(n >= 254, "every hotspot both ways (%d)" % n)


# --- the acting contract rides on the hotspots without changing them (stage 1b) ---------------------------------------------------

func test_an_acting_block_changes_no_outcome_and_the_outcome_chain_follows_the_result() -> void:
	var acting := {"actor": "g07", "available": {"act": "beckon", "face": "plea", "look_at": "camera"}, "selected": {"act": "nod", "face": "relief"},
		"committed": {"act": "point", "face": "resolve"}, "success": {"act": "cheer", "face": "cheer"}, "failure": {"act": "shake_head", "face": "doubt", "then": {"act": "stare", "face": "sad"}}}
	var plain := _engine_for([_h("a", {"default": true}), _h("b", {"kind": "character", "anchor": {"actor": "g07"}})])
	for success in [true, false]:
		var p := _engine_for([_h("a", {"default": true}), _h("b", {"kind": "character", "anchor": {"actor": "g07"}})])
		var q := _engine_for([_h("a", {"default": true}), _h("b", {"kind": "character", "anchor": {"actor": "g07"}, "acting": acting})])
		p.select("b", 3, true)
		q.select("b", 3, true)
		var op := p.commit_final(success)
		var oq := q.commit_final(success)
		for k in ["hotspot", "success", "route", "energy", "flags_set", "continued"]:
			assert_eq(oq[k], op[k], "%s: acting leaves the outcome's %s alone" % [str(success), k])
		var chain := RunActing.outcome_chain(q.get_hotspot("b"), success, 100.0, 0.34)
		assert_true(chain.size() >= 2, "a committed act then the result's")
		assert_eq(str(chain[chain.size() - 1 if success else chain.size() - 2]["act"]), "cheer" if success else "shake_head")
		for i in range(1, chain.size()):
			assert_near(float(chain[i]["from"]), float(chain[i - 1]["until"]), 1.0e-9, "end to end")
	assert_true(RunActing.outcome_chain(plain.get_hotspot("b"), true, 0.0, 0.3).is_empty(), "no block, no chain")


func test_a_named_cinematics_cast_is_carried_by_its_outcome_and_a_cinematic_without_cast_is_unchanged() -> void:
	var named := {"c.with": {"world": "w", "steps": [{"move": "walk", "to": "x"}], "cast": [{"actor": "g07", "at_beat": 1, "act": "nod"}]}, "c.without": {"world": "w", "steps": [{"move": "walk", "to": "x"}]}}
	var with := HotspotContract.resolve_cinematic({}, {"cinematic": "c.with"}, named)
	assert_eq(with["steps"].size(), 1)
	assert_eq(with["cast"].size(), 1)
	assert_eq(with["world"], "w")
	var without := HotspotContract.resolve_cinematic({}, {"cinematic": "c.without"}, named)
	assert_eq(without.keys(), ["steps"], "exactly as before: steps and nothing else")


## The coverage matrix, extended: every shipped hotspot still resolves both ways, and when it acts, its outcome chain is made of real acts and faces in order (the validator also ran at load).
func test_every_shipped_hotspots_acting_is_playable_both_ways() -> void:
	var d := RunData.load_default()
	assert_eq(d.errors, [])
	var acted := 0
	for node_id in d.nodes:
		for h in d.hotspots_of(node_id):
			for success in [true, false]:
				var hs := RunHotspots.new(d, {}, {})
				hs.begin_scene(node_id, 60.0)
				for f in (h["available"]["flags_all"] as Array):
					hs.run_flags[str(f)] = true
				hs.selected = str(h["id"])
				var out := hs.on_block(0, success) if RunHotspots.window_of(h) == "early" else hs.commit_final(success)
				assert_false(out.is_empty(), "%s resolves" % h["id"])
				if RunActing.has_acting(h):
					acted += 1
					var t := 50.0
					for seg in RunActing.outcome_chain(h, success, t, 0.345):
						assert_true(str(seg["act"]) in HotspotContract.ACTS, "%s: %s is an act" % [h["id"], seg["act"]])
						assert_true(str(seg["face"]) == "" or str(seg["face"]) in HotspotContract.FACES)
						assert_true(float(seg["from"]) >= t - 1.0e-9 and float(seg["until"]) > float(seg["from"]), "%s: segments run forward" % h["id"])
						t = float(seg["until"])
	assert_true(acted >= 0, "(%d acted outcomes; the five worlds' acting is stage 1d)" % acted)


func test_the_validator_checks_a_hotspots_acting_block() -> void:
	var errors: Array = []
	var ok := _h("a", {"kind": "character", "anchor": {"actor": "g07"}, "acting": {"available": {"act": "beckon", "face": "plea", "look_at": "camera"}}, "default": true})
	ok["map"] = "night_one"
	HotspotContract.validate_scene([ok, _two("b")], {"where": "t", "map": "night_one", "world": "w", "routes": ["to_a", "to_b", "to_default"], "default_route": "to_a"}, errors)
	assert_false(_any(errors, "acting"), "a good block passes: %s" % str(errors))
	for bad in [{"available": {"act": "moonwalk"}}, {"available": {"act": "nod", "face": "smug"}}, {"actor": "nobody", "available": {"act": "nod"}}, {"mood": {"act": "nod"}},
			{"success": {"act": "nod", "then": {"act": "bow", "face": "smug"}}}, {"available": {"act": "nod", "look_at": "the_moon"}}, {"available": "nod"}]:
		errors = []
		var h := _h("a", {"kind": "character", "anchor": {"actor": "g07"}, "acting": bad, "default": true})
		h["map"] = "night_one"
		HotspotContract.validate_scene([h, _two("b")], {"where": "t", "map": "night_one", "world": "w", "routes": ["to_a", "to_b", "to_default"], "default_route": "to_a"}, errors)
		assert_true(_any(errors, "acting"), "refused: %s" % str(bad))
	errors = []
	var thing := _h("a", {"kind": "object", "anchor": {"thing": "wizard_floor"}, "acting": {"available": {"act": "beckon"}}, "default": true})
	thing["map"] = "night_one"
	HotspotContract.validate_scene([thing, _two("b")], {"where": "t", "map": "night_one", "world": "w", "routes": ["to_a", "to_b", "to_default"], "default_route": "to_a"}, errors)
	assert_true(_any(errors, "acting needs an actor"), "a hotspot on a thing must name its person")
	errors = []
	var fig := _h("a", {"kind": "encounter", "anchor": {"thing": "wizard_floor"}, "acting": {"figure": "bouncer", "available": {"act": "block", "face": "anger"}}, "default": true})
	fig["map"] = "night_one"
	HotspotContract.validate_scene([fig, _two("b")], {"where": "t", "map": "night_one", "world": "w", "routes": ["to_a", "to_b", "to_default"], "default_route": "to_a", "default_any_kind": true, "figures": ["bouncer"]}, errors)
	assert_false(_any(errors, "acting"), "a creature's figure passes where creatures exist: %s" % str(errors))
	errors = []
	HotspotContract.validate_scene([fig, _two("b")], {"where": "t", "map": "night_one", "world": "w", "routes": ["to_a", "to_b", "to_default"], "default_route": "to_a", "default_any_kind": true}, errors)
	assert_true(_any(errors, "not a creature here"), "and not in the run")


func _two(id: String) -> Dictionary:
	var h := _h(id)
	h["map"] = "night_one"
	return h


func _any(errors: Array, needle: String) -> bool:
	for e in errors:
		if str(e).contains(needle):
			return true
	return false
