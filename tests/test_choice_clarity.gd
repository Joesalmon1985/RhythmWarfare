extends TestCase
## Choice clarity (docs/CHOICE_CLARITY.md): in every branching scene exactly one option is CURRENT at any time, the default is current at the start, a touch makes the touched option
## current and the old one stops being it, the commit takes the current option, the staging of every shipped hotspot validates, and the view's state is the same at any frame step.

const BEAT := 60.0 / 174.0
const TMP_SAVE := "user://test_choice_clarity_save.json"
const RUNS := ["", "gospel", "squadron", "ember"]

var _saved: RunProgress


func _h(id: String, extra: Dictionary = {}) -> Dictionary:
	var h := {"id": id, "scene": "s", "kind": "exit", "anchor": {"waypoint": "x"}, "on_success": {"route": "to_" + id}, "on_failure": {"route": "to_default"}}
	for k in extra:
		h[k] = extra[k]
	return HotspotContract.normalize(h, "w", "m")


func _engine_for(list: Array) -> RunHotspots:
	var d := RunData.new()
	d.hotspots = {"s": list}
	var hs := RunHotspots.new(d, {}, {})
	hs.begin_scene("s", 60.0)
	return hs


func _data(run: String) -> RunData:
	return RunData.load_default() if run == "" else RunData.load_path(run)


# --- the pure model ----------------------------------------------------------------------------------------------------------

func test_the_default_is_current_and_a_touch_moves_current_until_the_commit_takes_it() -> void:
	var hs := _engine_for([_h("a", {"default": true}), _h("b"), _h("c", {"kind": "object", "anchor": {"actor": "p"}, "on_success": {"energy": 5}})])
	assert_eq(hs.current_id(0), "a", "the default is current from the first beat")
	assert_eq(hs.destination(0), "to_a")
	assert_eq(hs.staged(0).size(), 3, "every option is staged before its window")
	assert_true(hs.select("b", 3, true))
	assert_eq(hs.current_id(3), "b", "a touch makes it current")
	assert_eq(hs.destination(3), "to_b")
	assert_true(hs.select("c", 3, true))
	assert_eq(hs.current_id(3), "c")
	assert_eq(hs.destination(3), "to_a", "an option with no route of its own goes on by the default way: the default door stays open")
	assert_true(hs.select("c", 3, true), "touching the current option again changes nothing")
	assert_eq(hs.current_id(3), "c")
	var out := hs.commit_final(true)
	assert_eq(str(out["hotspot"]), "c", "the commit takes the current option")
	assert_eq(hs.current_id(3), "c", "after the commit the committed one stays current")
	assert_eq(hs.destination(3), "to_a")
	var roles := ChoiceStaging.roles(hs.staged(3), hs.current_id(3), hs.committed, hs.destination(3))
	assert_eq(roles["c"]["role"], "committed")
	assert_eq(roles["a"]["role"], "declined")
	assert_true(bool(roles["a"]["open"]), "the default door is the way out after an object")


func test_untouched_the_default_commits_as_before() -> void:
	var hs := _engine_for([_h("a", {"default": true}), _h("b")])
	var out := hs.commit_final(false)
	assert_eq(str(out["hotspot"]), "a")
	assert_false(bool(out["tapped"]), "nothing tapped: the default exit whatever the performance (unchanged)")
	assert_true(bool(out["success"]))


func test_touch_rules_are_unchanged_unless_preselect() -> void:
	var hs := _engine_for([_h("a", {"default": true}), _h("b")])
	assert_false(hs.select("b", 0, false), "before the window a final option cannot be touched (the route window rule)")
	assert_eq(hs.current_id(0), "a")
	hs.preselect = true
	assert_true(hs.select("b", 0, false), "the owner's preselect option: touchable from the first beat")
	assert_eq(hs.current_id(0), "b")


func test_staging_defaults_by_archetype() -> void:
	assert_eq(ChoiceStaging.of(_h("a"))["archetype"], "door")
	assert_eq(ChoiceStaging.of(_h("a"))["door"], "drawn", "a doorway point gets a drawn door")
	assert_eq(ChoiceStaging.of(_h("a", {"anchor": {"thing": "crack"}}))["door"], "bars", "a doorway that is a thing of the map gets boards across it")
	var p := ChoiceStaging.of(_h("p", {"kind": "character", "anchor": {"actor": "g07"}}))
	assert_eq(p["archetype"], "person")
	assert_eq(p["actor"], "g07")
	assert_eq(p["current"]["act"], "beckon")
	assert_eq(p["current"]["face"], "happy")
	assert_eq(p["other"]["face"], "sad", "the other people still invite, sadly")
	assert_eq(p["other"]["look_at"], "camera")
	var own := ChoiceStaging.of(_h("p", {"kind": "character", "anchor": {"actor": "g07"}, "staging": {"other": {"act": "beckon"}}}))
	assert_eq(own["other"]["act"], "beckon", "a hotspot's own block is merged over the defaults")
	assert_eq(own["other"]["face"], "sad")
	assert_eq(ChoiceStaging.of(_h("o", {"kind": "object", "anchor": {"thing": "sofa"}}))["archetype"], "object")
	assert_eq(ChoiceStaging.of(_h("f", {"kind": "feature", "anchor": {"thing": "lamp"}}))["archetype"], "feature")


func test_lamps_and_doors_use_shape_as_well_as_colour() -> void:
	var door := ChoiceStaging.of(_h("a"))
	assert_eq(ChoiceStaging.lamp_of(door, "current", true), "go")
	assert_eq(ChoiceStaging.lamp_of(door, "other", false), "stop")
	assert_eq(ChoiceProps.door_frame(ChoiceStaging.open_amount(true, 10.0, BEAT)), "door_3", "open")
	assert_eq(ChoiceProps.door_frame(ChoiceStaging.open_amount(false, 10.0, BEAT)), "door_0", "shut")
	assert_true(ChoiceStaging.open_amount(true, 0.5 * BEAT, BEAT) > 0.2 and ChoiceStaging.open_amount(true, 0.5 * BEAT, BEAT) < 0.8, "it swings within a beat")
	for n in ["door_0", "door_1", "door_2", "door_3", "bars", "lamp_go", "lamp_stop", "spill", "wizard_happy", "wizard_sad"]:
		assert_true(ChoiceProps.tex(n) != null, "the art %s is there" % n)


func test_the_validator_names_bad_staging() -> void:
	var idx := HotspotContract.map_index("night_one")
	var bad := [[{"archetype": "dragon"}, "staging.archetype"], [{"door": "portcullis"}, "staging.door"], [{"current": {"act": "fly"}}, "act 'fly'"],
		[{"current_tex": "nothing_here"}, "current_tex"], [{"touch": {"w": 0, "h": 2}}, "staging.touch"], [{"colour": "red"}, "not a field"],
		[{"states": {"current": [{"piece": "no_such_piece", "op": "on"}]}}, "not a piece"], [{"states": {"maybe": []}}, "not a state"],
		[{"states": {"other": [{"actor": "nobody_here", "act": "nod"}]}}, "no home"], [{"states": {"current": [{"what": 1}]}}, "a step is"],
		[{"states": {"current": [{"lamp": "blue"}]}}, "lamp 'blue'"], [{"door": "pieces"}, "needs open_piece"]]
	for c in bad:
		var errors: Array = []
		ChoiceStaging.validate({"staging": c[0]}, "h", idx, errors)
		assert_true(errors.any(func(e: String) -> bool: return e.contains(str(c[1]))), "%s is reported: %s" % [str(c[0]), str(errors)])
	var good: Array = []
	ChoiceStaging.validate({"staging": {"archetype": "custom", "states": {"current": [{"actor": "g07", "act": "beckon", "face": "happy"}, {"thing": "wizard_floor", "tex": "wizard_happy", "motion": "beckon"},
		{"prop": "lamp_go", "at": [0, 2, 0]}, {"lamp": "go"}], "other": [{"lamp": "stop"}]}}}, "h", idx, good)
	assert_eq(good, [], "a custom staging of steps validates")


# --- every shipped scene -----------------------------------------------------------------------------------------------------

func test_every_shipped_staging_validates_and_every_branching_scene_has_exactly_one_current() -> void:
	var n_scenes := 0
	for run in RUNS:
		var d := _data(run)
		assert_eq(d.errors, [], "%s loads clean with its staging" % (run if run != "" else "main"))
		for nid in d.nodes:
			var hs := RunHotspots.new(d, {}, {})
			hs.begin_scene(str(nid), 60.0)
			for block in [0, 3]:
				var st := hs.staged(block)
				if st.size() < 2:
					continue
				n_scenes += 1 if block == 3 else 0
				var cur := hs.current_id(block)
				var def := str(hs.default_hotspot().get("id", ""))
				assert_eq(cur, def, "%s: the default is current at the start" % nid)
				var roles := ChoiceStaging.roles(st, cur, "", hs.destination(block))
				var n_cur := 0
				var n_open := 0
				for id in roles:
					n_cur += 1 if roles[id]["role"] == "current" else 0
					n_open += 1 if bool(roles[id]["open"]) else 0
				assert_eq(n_cur, 1, "%s block %d: exactly one current" % [nid, block])
				assert_true(n_open <= 1, "%s: at most one door open" % nid)
				# a touch on each other option on show makes it the only current one, and the commit takes it
				if block == 3:
					for h in hs.shown(3, true):
						if str(h["id"]) == def or RunHotspots.window_of(h) == "any":  # (a place to sit, the card table, is no option of the choice: staged() leaves it out)
							continue
						var hs2 := RunHotspots.new(d, {}, {})
						hs2.begin_scene(str(nid), 60.0)
						assert_true(hs2.select(str(h["id"]), 3, true), "%s: %s can be touched" % [nid, h["id"]])
						var r2 := ChoiceStaging.roles(hs2.staged(3), hs2.current_id(3), "", hs2.destination(3))
						assert_eq(r2[str(h["id"])]["role"], "current", "%s: the touched one is current" % h["id"])
						assert_eq(r2[def]["role"], "other", "%s: the default is not current any more" % h["id"])
						var out := hs2.commit_final(true)
						assert_eq(str(out["hotspot"]), str(h["id"]), "%s: the commit takes the current option" % h["id"])
	assert_true(n_scenes >= 80, "every branching scene of the four runs was checked (%d)" % n_scenes)


func test_every_trial_hotspot_staging_validates() -> void:
	var t := TrialHotspots.load_default()
	assert_eq(t.errors, [], "the Bassment's hotspots load clean")


# --- the real scene ----------------------------------------------------------------------------------------------------------

func _scene(start := "") -> Dictionary:
	_saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	if start != "":
		OS.set_environment("RW_RUN_START", start)
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
	OS.unset_environment("RW_RUN_START")


func _run_to(scene: Node, t_end: float, step := 1.0 / 30.0) -> void:
	var t: float = scene._vt
	while t < t_end:
		t = minf(t + step, t_end)
		scene._vt = t
		scene._step_virtual(t)


func _snap(scene: Node) -> Dictionary:
	var hv: HotspotView = scene.stages[scene.active_world]["hotspot_view"]
	return hv.refresh_choice(float(scene.hud.now_t))


func _role(snap: Dictionary, id: String) -> String:
	return str(((snap.get("options", {}) as Dictionary).get(id, {}) as Dictionary).get("role", ""))


func test_the_warehouse_floor_stages_the_choice_from_the_first_beat_and_swaps_on_a_touch() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_run_to(scene, 2.0 * BEAT)
	var s := _snap(scene)
	assert_eq(str(s["current"]), "warehouse.exit_bar", "the default is current at beat 2")
	assert_eq(_role(s, "warehouse.wizard"), "other", "the wizard waits, sad")
	assert_eq(_role(s, "warehouse.dancer"), "other")
	assert_true(bool(s["options"]["warehouse.exit_bar"]["open"]), "the default door stands open")
	assert_false(bool(s["options"]["warehouse.exit_balcony"]["open"]), "the other door is shut")
	var hv: HotspotView = scene.stages[scene.active_world]["hotspot_view"]
	var world: StoryWorld = (scene.stages[scene.active_world]["stage"] as StoryStage).world
	assert_true(scene.hotspot_select("warehouse.wizard"), "the wizard is touchable in the early window")
	_run_to(scene, 4.5 * BEAT)
	s = _snap(scene)
	assert_eq(str(s["current"]), "warehouse.wizard")
	assert_eq(_role(s, "warehouse.exit_bar"), "other", "the old current is not current any more")
	assert_false(bool(s["options"]["warehouse.exit_bar"]["open"]), "going with the wizard: no door of the room is the way")
	assert_true(world.thing_pose.has("wizard_floor"), "the wizard's billboard is posed")
	assert_eq(world.thing_pose["wizard_floor"].get("tex", null), ChoiceProps.tex("wizard_happy"), "the current wizard beckons, happy")
	if hv.props != null:
		var frames := {}
		for k in hv.props.shown_keys():
			frames[k] = hv.props.frame_of(k)
		assert_eq(frames.get("warehouse.exit_bar#door", ""), "door_0", "the bar door has swung shut within a beat: %s" % str(frames))
		assert_eq(frames.get("warehouse.exit_bar#lamp", ""), "lamp_stop")
	_free(d)


func test_in_the_window_a_touch_swaps_the_doors_and_the_commit_takes_the_current_one() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	_run_to(scene, 50.0 * BEAT)
	assert_eq(str(_snap(scene)["current"]), "warehouse.exit_bar")
	assert_true(scene.hotspot_select("warehouse.exit_balcony"))
	_run_to(scene, 52.0 * BEAT)
	var s := _snap(scene)
	assert_eq(_role(s, "warehouse.exit_balcony"), "current")
	assert_eq(_role(s, "warehouse.exit_bar"), "other")
	assert_true(bool(s["options"]["warehouse.exit_balcony"]["open"]))
	assert_true(float(s["options"]["warehouse.exit_balcony"]["open_k"]) > 0.99, "open within a beat")
	assert_true(float(s["options"]["warehouse.exit_bar"]["open_k"]) < 0.01, "and the other shut")
	assert_true(scene.hotspot_select("warehouse.exit_bar"), "back to A")
	_run_to(scene, 61.0 * BEAT)
	s = _snap(scene)
	assert_eq(str(s["committed"]), "warehouse.exit_bar", "the commit takes the current option")
	assert_eq(_role(s, "warehouse.exit_bar"), "committed")
	assert_eq(_role(s, "warehouse.exit_balcony"), "declined")
	_free(d)


func test_the_choice_state_is_the_same_at_any_frame_step() -> void:
	var snaps: Array = []
	for step in [1.0 / 30.0, 1.0 / 60.0, 0.11]:
		var d := _scene()
		var scene: Node = d["scene"]
		_run_to(scene, 50.0 * BEAT, step)
		scene.hotspot_select("warehouse.exit_balcony")
		_run_to(scene, 50.6 * BEAT, step)
		var s := _snap(scene)
		var o: Dictionary = s["options"]
		snaps.append([str(s["current"]), snappedf(float(o["warehouse.exit_balcony"]["open_k"]), 0.05), str(o["warehouse.exit_bar"]["role"]), str(o["warehouse.exit_bar"]["lamp"])])
		_free(d)
	assert_eq(snaps[0], snaps[1], "30 and 60 fps")
	assert_eq(snaps[0][0], snaps[2][0], "a ragged step: the same current")
	assert_eq(snaps[0][2], snaps[2][2])
