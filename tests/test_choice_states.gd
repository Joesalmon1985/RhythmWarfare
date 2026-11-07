extends TestCase
## Package A7 (lead ruling 35b, contract 9, docs/art/CHOICE_STATES.md): a choice shows its state (idle, available, selected, committed, declined, cost) with its own artwork,
## never a ring. The state machine per run event (ChoiceState), the frames and the light of each state (ChoiceShow), every shipped hotspot's `show` (the tables' declaration
## and the contract's ChoiceThing), the answer to a tap within 0.1 s in the real run scene, the commit at the boundary, and nothing drawn over the world with RINGS off.

const BEAT := 60.0 / 174.0
const TMP_SAVE := "user://test_choice_states_save.json"
const RUNS := ["", "gospel", "squadron", "ember"]

var _saved: RunProgress


func _h(id: String, extra: Dictionary = {}) -> Dictionary:
	var h := {"id": id, "scene": "s", "kind": "exit", "anchor": {"waypoint": "x"}, "on_success": {"route": "to_" + id}, "on_failure": {"route": "to_default"}}
	for k in extra:
		h[k] = extra[k]
	return HotspotContract.normalize(h, "w", "m")


func _c(staged: Array, current: String, committed := "", touched: Dictionary = {}, changed := -INF) -> Dictionary:
	return {"staged": staged, "current": current, "committed": committed, "dest": "", "default": "a", "touched": touched, "changed_t": changed}


func _item(h: Dictionary, state: String, extra: Dictionary = {}) -> Dictionary:
	var e := {"hotspot": h, "state": state, "t_state": 0.0}
	e.merge(extra, true)
	return e


# --- the state machine ---------------------------------------------------------------------------------------------------------

func test_the_state_machine_follows_the_runs_events() -> void:
	var a := _h("a", {"default": true})
	var b := _h("b")
	var st := [a, b]
	var cs := ChoiceState.new()
	var on := [_item(a, "available"), _item(b, "available")]
	var s := cs.update(_c(st, "a"), 0.5, on)
	assert_eq(s["a"]["state"], "selected", "the default is the current choice from the first beat: what happens if nothing more is done")
	assert_eq(s["b"]["state"], "available")
	assert_false(is_finite(float(s["b"]["t_state"])), "first seen: already in its state (no swing at the scene's start)")
	s = cs.update(_c(st, "b", "", {"b": 1.0}, 1.0), 1.03, [_item(a, "available"), _item(b, "selected")])
	assert_eq(s["b"]["state"], "selected", "a touch selects at once")
	assert_near(float(s["b"]["t_state"]), 1.0, 1e-6, "stamped with the touch's song time, not the frame's")
	assert_eq(s["b"]["prev"], "available")
	assert_eq(s["a"]["state"], "available", "the old pick is available again in the same frame")
	s = cs.update(_c(st, "b", "", {"b": 1.0}, 1.0), 20.0, [])
	assert_eq(s["b"]["state"], "selected", "through the lock the pick stays selected")
	assert_eq(s["a"]["state"], "declined", "after the lock the others step back")
	assert_near(float(s["a"]["t_state"]), 20.0, 1e-6)
	s = cs.update(_c(st, "b", "b", {"b": 1.0}, 21.0), 21.01, [_item(b, "committed", {"t_state": 21.0, "success": true})])
	assert_eq(s["b"]["state"], "committed", "the commit at the boundary")
	assert_near(float(s["b"]["t_state"]), 21.0, 1e-6, "at the commit's time")
	assert_eq(s["a"]["state"], "declined")
	s = cs.update(_c([a], "a"), 30.0, [])
	assert_false(s.has("b"), "an option no longer staged is forgotten (idle)")
	# a failed commit is a cost
	var cs2 := ChoiceState.new()
	cs2.update(_c(st, "b", "", {"b": 1.0}, 1.0), 1.0, [_item(a, "available"), _item(b, "selected")])
	s = cs2.update(_c(st, "b", "b", {"b": 1.0}, 21.0), 21.0, [_item(b, "committed", {"t_state": 21.0, "success": false})])
	assert_eq(s["b"]["state"], "cost", "a wrong one costs")
	assert_eq(s["a"]["state"], "declined")
	# without items nothing is inferred about the lock
	var cs3 := ChoiceState.new()
	s = cs3.update(_c(st, "a"), 2.0)
	assert_eq(s["b"]["state"], "available", "no items: the lock is not inferred")
	assert_true(ChoiceState.window_closed_of({"window_closed": true}, null), "a snapshot that says the lock has passed is believed")


func test_the_states_are_the_contracts_states() -> void:
	var a := _h("a", {"default": true})
	var b := _h("b")
	for case in [["a", "", true, false], ["b", "", true, false], ["a", "a", true, false], ["b", "a", false, false], ["b", "", true, true]]:
		var c := _c([a, b], "a", str(case[1]))
		var want := ContractShapes.choice_state(str(case[0]), true, "a" if str(case[1]) == "" else "", str(case[1]), bool(case[2]), bool(case[3]))
		assert_eq(ChoiceState.state_in(str(case[0]), c, bool(case[2]), bool(case[3])), want, "the run's words give the contract's state %s" % str(case))
	assert_eq(ChoiceState.state_in("z", _c([a, b], "a")), "idle", "not staged: idle")


# --- the frames, the light and the sound of each state -------------------------------------------------------------------------

func test_a_door_lights_opens_spills_and_shuts() -> void:
	var sh := ChoiceShow.of(_h("a"))
	assert_eq(sh["archetype"], "door")
	assert_eq(sh["light"], "lamp")
	assert_eq(sh["floor_light"], "spill")
	var av := ChoiceShow.look(sh, "available", 5.0, BEAT, "", 5.0)
	var se := ChoiceShow.look(sh, "selected", 5.0, BEAT, "available", 5.0)
	var co := ChoiceShow.look(sh, "committed", 5.0, BEAT, "selected", 5.0)
	var de := ChoiceShow.look(sh, "declined", 5.0, BEAT, "selected", 5.0)
	var cost := ChoiceShow.look(sh, "cost", 0.1, BEAT, "selected", 5.0)
	assert_eq(av["frame"], "door_1", "available: ajar")
	assert_eq(se["frame"], "door_2", "selected: swung open")
	assert_eq(co["frame"], "door_3", "committed: wide")
	assert_eq(de["frame"], "door_0", "declined: shut")
	assert_eq(ChoiceShow.look(sh, "declined", 0.05, BEAT, "selected", 5.0)["frame"], "door_1", "it closes through ajar over a quarter second")
	assert_eq(ChoiceShow.look(sh, "cost", 1.0, BEAT, "selected", 5.0)["frame"], "door_0", "a cost: it shuts")
	assert_true(float(av["lamp"]) > 0.5 and float(se["lamp"]) > float(av["lamp"]), "the lamp is lit, and brighter when selected (%.2f, %.2f)" % [av["lamp"], se["lamp"]])
	assert_near(float(de["lamp"]), 0.0, 1e-6, "declined: the lamp goes out")
	assert_true(float(co["floor"]) > float(se["floor"]) and float(se["floor"]) > float(av["floor"]) and float(av["floor"]) > 0.0, "the floor light grows: available, selected, committed spill")
	assert_true(bool(cost["flicker"]) and (cost["tint"] as Color).r > 0.9 and (cost["tint"] as Color).g < 0.5, "a cost flickers red")
	assert_true(absf(float((cost["pose"] as Dictionary)["dx"])) > 0.0, "and the door shakes")
	var lamps := {}
	for k in 16:  # the flicker: on and off on the eighth beats over the cost's two beats
		lamps[ChoiceShow.look(sh, "cost", float(k) * BEAT * 0.125, BEAT, "selected", 5.0)["lamp"]] = true
	assert_true(lamps.size() >= 2, "the cost's lamp flickers (%s)" % str(lamps.keys()))
	var mid := ChoiceShow.look(sh, "selected", 0.1, BEAT, "available", 5.0)
	assert_true(float(mid["lamp"]) > float(av["lamp"]) and float(mid["lamp"]) < float(se["lamp"]), "the lamp brightens over the quarter second (%.2f at 0.1 s)" % mid["lamp"])
	assert_eq(se["sound"], "choice_door_open")
	assert_eq(co["sound"], "choice_commit")
	assert_eq(cost["sound"], "choice_cost")
	assert_eq(ChoiceShow.look(sh, "available", 0.0, BEAT, "", 0.0, true, 0.1)["flicker"], true, "a refused tap flickers")


func test_a_figure_beckons_steps_toward_gestures_steps_back_or_recoils() -> void:
	var person := ChoiceShow.of(_h("p", {"kind": "character", "anchor": {"actor": "g07"}}))
	assert_eq(person["archetype"], "figure")
	var want := {"available": "beckon", "selected": "step_toward", "committed": "gesture", "declined": "step_back", "cost": "recoil"}
	for s in want:
		assert_eq(ChoiceShow.look(person, s, 3.0, BEAT, "", 3.0)["frame"], want[s], "%s: %s" % [s, want[s]])
	assert_eq(ChoiceShow.look(person, "available", 3.0, BEAT, "", 3.0)["motion"], "beckon")
	var gate := ChoiceShow.of(_h("q", {"kind": "secret", "anchor": {"pos": [0, 1, 0]}, "herald": {"quest": "gospel", "at": [1, 1], "toward": [0, 0], "gate": true}}))
	assert_eq([gate["archetype"], gate["light"], gate["floor_light"]], ["door", "gate", "pool"], "a quest entrance: its gate is the lamp, its pool the floor light")
	var no_gate := ChoiceShow.of(_h("r", {"kind": "secret", "anchor": {"pos": [0, 1, 0]}, "herald": {"quest": "squadron", "at": [1, 1], "toward": [0, 0]}}))
	assert_eq([no_gate["light"], no_gate["floor_light"]], ["none", "pool"], "an entrance without a gate: its pool")
	# the herald's own pose per state
	assert_eq(StoryHeralds.pose_of("selected", {}, 0.0, BEAT)["frame"], StoryHeralds.POINT_FRAME, "selected: the point")
	assert_true(float(StoryHeralds.pose_of("selected", {}, 0.0, BEAT)["scale"]) > 1.0, "a step toward")
	assert_true(float(StoryHeralds.pose_of("declined", {}, 0.0, BEAT)["scale"]) < 1.0 and float(StoryHeralds.pose_of("declined", {}, 0.0, BEAT)["light"]) < 1.0, "declined: a step back into the dark")
	assert_eq(StoryHeralds.pose_of("available", {}, BEAT, BEAT)["frame"], StoryHeralds.frame_of(BEAT, BEAT), "available: the gesture loop")


func test_an_object_shows_with_its_own_light() -> void:
	var o := ChoiceShow.of(_h("o", {"kind": "object", "anchor": {"thing": "sofa"}}))
	assert_eq([o["archetype"], o["light"]], ["object", "self"])
	var av := ChoiceShow.look(o, "available", 3.0, BEAT, "", 3.0)
	var se := ChoiceShow.look(o, "selected", 3.0, BEAT, "", 3.0)
	assert_eq(av["frame"], "self")
	assert_true(ChoiceShow.self_light(float(se["lamp"])) > ChoiceShow.self_light(float(av["lamp"])), "brighter when selected")
	var pulse := {}
	for k in 8:
		pulse[snappedf(float(ChoiceShow.look(o, "available", 3.0, BEAT, "", float(k) * BEAT * 0.125)["lamp"]), 0.001)] = true
	assert_true(pulse.size() >= 3, "available: its light pulses on the beat")
	assert_eq(ChoiceShow.of(_h("o2", {"kind": "object", "anchor": {"pos": [0, 1, 0]}}))["light"], "lamp", "with no thing of its own: a lamp over the spot")


func test_a_hotspots_own_show_block_is_merged_and_validated() -> void:
	var h := _h("a", {"show": {"set": "warehouse", "states": {"selected": {"light": {"tint": "#ff0000"}}}}})
	var sh := ChoiceShow.of(h)
	assert_eq(sh["set"], "warehouse")
	assert_eq(str(sh["states"]["selected"]["light"]["tint"]), "#ff0000", "a state's light merged key by key")
	assert_eq(str(sh["states"]["selected"]["light"]["lamp"]), "open", "the rest kept")
	assert_eq(sh["states"]["selected"]["frames"], ["door_2"])
	var idx := HotspotContract.map_index("night_one")
	var bad := [[{"archetype": "dragon"}, "show.archetype"], [{"colour": 1}, "not a field"], [{"states": {"maybe": {}}}, "not a state"],
		[{"states": {"selected": {"frames": ["ring_big"]}}}, "drawn symbol"], [{"states": {"selected": {"frames": ["door_9"]}}}, "not a door frame"],
		[{"states": {"selected": {"motion": "fly"}}}, "motion"], [{"states": {"selected": {"light": {"lamp": "blue"}}}}, "light.lamp"],
		[{"states": {"selected": {"light": {"floor_glow": 2}}}}, "floor_glow"], [{"light": "torch_nowhere"}, "show.light"]]
	for c in bad:
		var errors: Array = []
		var hh := _h("a", {"show": c[0]})
		ChoiceShow.validate(hh, "h", idx, errors)
		assert_true(errors.any(func(e: String) -> bool: return e.contains(str(c[1]))), "%s is reported: %s" % [str(c[0]), str(errors)])


func _all_rows() -> Array:
	var out: Array = []
	for run in RUNS:
		var d := RunData.load_default() if run == "" else RunData.load_path(run)
		assert_eq(d.errors, [], "%s loads clean with its show blocks" % (run if run != "" else "main"))
		for sid in d.hotspots:
			out.append_array(d.hotspots[sid])
	var t := TrialHotspots.load_default()
	assert_eq(t.errors, [], "the Bassment's hotspots load clean")
	return out


func test_every_shipped_hotspot_declares_its_show_and_it_is_a_valid_choice_thing() -> void:
	var n := 0
	var by := {}
	for h in _all_rows():
		n += 1
		assert_true(h.has("show"), "%s declares its show (tools/run/apply_staging.py)" % h["id"])
		var sh := ChoiceShow.of(h)
		by[sh["archetype"]] = int(by.get(sh["archetype"], 0)) + 1
		if str((h.get("show", {}) as Dictionary).get("set", "")) == "":
			assert_eq(ChoiceShow.archetype_of(h), ChoiceShow.default_archetype(h), "%s: the tables' declaration is the default of its archetype" % h["id"])
		if sh["archetype"] == "none":
			continue
		var errs := ContractShapes.choice_thing(ChoiceShow.choice_thing(h))
		assert_eq(errs, [], "%s is a valid ChoiceThing (contract 9)" % h["id"])
	print("  show archetypes over %d rows: %s" % [n, str(by)])
	assert_true(n >= 300, "every row of the four runs (%d)" % n)
	assert_true(int(by.get("door", 0)) > 150 and int(by.get("figure", 0)) > 40 and int(by.get("object", 0)) > 50, "doors, figures and objects all shipped: %s" % str(by))


func test_the_return_door_and_the_gates_are_doors_by_default() -> void:
	for h in _all_rows():
		var id := str(h["id"])
		if id.ends_with(".return"):
			assert_eq(ChoiceShow.of(h)["archetype"], "door", "%s: the way home is a door" % id)
			assert_eq(ChoiceShow.of(h)["set"], "warehouse", "the Warehouse's own door")
			var steps: Dictionary = (h.get("staging", {}) as Dictionary).get("states", {})
			assert_true(steps.is_empty(), "%s: no lamp prop stood over it any more" % id)
		var hb: Variant = h.get("herald", null)
		if typeof(hb) == TYPE_DICTIONARY and not (hb as Dictionary).has("self"):
			assert_eq(ChoiceShow.of(h)["archetype"], "door", "%s: a quest entrance shows as its gate" % id)


# --- the real scene ----------------------------------------------------------------------------------------------------------

func _scene() -> Dictionary:
	_saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	Session.run_start_node = ""
	var host := Control.new()
	host.size = Vector2(1152, 648)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = Vector2(1152, 648)
	return {"host": host, "scene": scene}


func _free(d: Dictionary) -> void:
	Session.run_progress = _saved
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	(d["host"] as Control).queue_free()
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES"]:
		OS.set_environment(k, "")


func _run_to(scene: Node, t_end: float, step := 1.0 / 30.0) -> void:
	var t: float = scene._vt
	while t < t_end:
		t = minf(t + step, t_end)
		scene._vt = t
		scene._step_virtual(t)


func _hv(scene: Node) -> HotspotView:
	return scene.stages[scene.active_world]["hotspot_view"]


func test_a_tap_answers_within_a_tenth_of_a_second_and_the_commit_waits_for_the_boundary() -> void:
	assert_false(HotspotView.RINGS, "the rings are off")
	var d := _scene()
	var scene: Node = d["scene"]
	_run_to(scene, 50.0 * BEAT)
	var hv := _hv(scene)
	var s := hv.refresh_choice(float(scene.hud.now_t))
	assert_eq(str(s["options"]["warehouse.exit_balcony"]["state"]), "available")
	var before: Dictionary = s["options"]["warehouse.exit_balcony"]["look"]
	var t0: float = scene.hud.now_t
	var n_cues := hv.cues.size()
	assert_true(scene.hotspot_select("warehouse.exit_balcony"))
	_run_to(scene, t0 + 0.1)  # (the frames of the next tenth of a second)
	s = hv.refresh_choice(float(scene.hud.now_t))
	var o: Dictionary = s["options"]["warehouse.exit_balcony"]
	assert_eq(str(o["state"]), "selected", "selected within 0.1 s of the tap")
	assert_near(float(o["t_state"]), t0, 1e-6, "the state is stamped at the tap")
	var lk: Dictionary = o["look"]
	assert_true(str(lk["frame"]) != str(before["frame"]), "a new frame within 0.1 s (%s -> %s)" % [before["frame"], lk["frame"]])
	assert_true(float(lk["lamp"]) > float(before["lamp"]) and float(lk["floor"]) > float(before["floor"]), "its lamp and its floor light rising")
	assert_eq(hv.props.frame_of("warehouse.exit_balcony#door"), "door_2", "the door prop has swung")
	var new_cues := hv.cues.slice(n_cues)
	assert_true(new_cues.any(func(c: Dictionary) -> bool: return str(c["hotspot"]) == "warehouse.exit_balcony" and str(c["sound"]) == "choice_door_open" and absf(float(c["t"]) - t0) < 1e-6),
		"its cue at the tap: %s" % str(new_cues))
	assert_eq(str(s["options"]["warehouse.exit_bar"]["state"]), "available", "the default is no longer the pick: ajar again")
	assert_eq(str(s["committed"]), "", "nothing commits on the tap")
	var t := float(scene.hud.now_t)
	while t < 64.5 * BEAT and str(s.get("committed", "")) == "":
		t += 1.0 / 30.0
		_run_to(scene, t)
		s = hv.refresh_choice(float(scene.hud.now_t))
	assert_eq(str(s.get("committed", "")), "warehouse.exit_balcony", "the commit at the boundary takes the pick")
	var c: Dictionary = s["options"]["warehouse.exit_balcony"]
	assert_eq(str(c["state"]), "committed")
	var commits := (scene.hotspot_log as Array).filter(func(e: Dictionary) -> bool: return str(e["kind"]) == "commit")
	assert_false(commits.is_empty(), "the run logged its commit")
	if not commits.is_empty():
		assert_near(float(c["t_state"]), float(commits[-1]["t"]), 1e-6, "committed at the run's commit (the lock of the boundary), as today")
	assert_true(float(c["t_state"]) > t0 + 2.0, "not at the tap (%.2f vs %.2f)" % [c["t_state"], t0])
	assert_eq(str(s["options"]["warehouse.exit_bar"]["state"]), "declined", "the other door shuts")
	assert_eq(hv.props.frame_of("warehouse.exit_balcony#door"), "door_3", "wide open")
	_free(d)


func test_no_ring_is_drawn_and_no_mark_or_go_stop_lamp_stands_in_the_world() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_run_to(scene, 4.0 * BEAT)
	var hv := _hv(scene)
	scene.hotspot_select("warehouse.exit_balcony")
	_run_to(scene, 5.0 * BEAT)
	hv.queue_redraw()
	await tree.process_frame
	await tree.process_frame
	assert_eq(hv.drawn_kinds, {}, "the view's canvas draws no ring, pool, beacon or claim")
	assert_eq(hv._lay, [], "nothing is laid out for drawing")
	assert_true(hv.props != null and not hv.props.shown_keys().is_empty(), "the choice props stand")
	for k in hv.props.shown_keys():
		assert_false(hv.props.frame_of(k) in ["lamp_go", "lamp_stop"], "%s is no go or stop lamp" % k)
	if hv.heralds != null:
		for id in hv.heralds._recs:
			var mp: Variant = (hv.heralds._recs[id] as Dictionary).get("mark", null)
			if mp != null and is_instance_valid(mp):
				assert_true(str((mp as Node).name).begins_with("HeraldGate_"), "%s: the gate and pool, no mark" % id)
			assert_false((hv.heralds.drawn.get(id, {}) as Dictionary).has("mark"), "%s: no mark drawn" % id)
	var src := FileAccess.get_file_as_string("res://src/run/hotspot_view.gd")
	assert_true(src.contains("const RINGS := false"), "the old look is behind one constant, off")
	_free(d)
