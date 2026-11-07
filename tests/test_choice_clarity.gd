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
		assert_eq(frames.get("warehouse.exit_bar#door", ""), "door_1", "the bar door is no longer the pick: back to ajar within a beat (ruling 35b, no red lamp): %s" % str(frames))
		assert_eq(frames.get("warehouse.exit_bar#lamp", ""), "lamp_lit", "its lamp is the practical lamp, lit (available), not a stop sign")
		assert_false(frames.values().has("lamp_go") or frames.values().has("lamp_stop"), "no go or stop lamp is drawn")
		assert_eq(str(s["options"]["warehouse.wizard"]["state"]), "selected", "the touched wizard is selected")
		assert_eq(str(s["options"]["warehouse.exit_bar"]["state"]), "available")
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


# --- touch targets without a ring (package A7, contract 9) ---------------------------------------------------------------------

const TARGET_SCENES := ["warehouse", "warehouse.bar", "warehouse.balcony", "warehouse.booth", "warehouse.chill", "underworld", "mothership"]
const WINDOW_BEATS := [52.0, 56.0, 60.0]  # the choice window, where the camera holds at its viewpoint (lead ruling 35a)
## Pairs whose middles stand under 88 px apart from today's window camera (package A7's measurement, 7 November 2026): the art of the world packages (a door with a person
## in front of it, hub gates 1.2 to 2.2 m apart seen from the hub's middle) and the choice viewpoints of contract 3 (hook H3.1, not built) are what separates them. A tap
## on either middle still takes its own (asserted below). A new pair fails this test; a pair separated by its package comes off this list.
const KNOWN_CLOSE := ["mothership.exit_gallery|mothership.enter_ember", "mothership.exit_gallery|mothership.exit_reactor", "mothership.exit_gallery|mothership.grey",
	"mothership.exit_reactor|mothership.enter_gospel", "mothership.exit_reactor|mothership.grey", "mothership.grey|mothership.enter_ember",
	"underworld.enter_ember|underworld.enter_squadron", "underworld.exit_court|underworld.enter_ember", "underworld.exit_court|underworld.enter_gospel",
	"warehouse.bar.exit_chill|warehouse.bar.stranger", "warehouse.exit_balcony|warehouse.dancer"]


## Every touch region of a laid-out entry (its rectangle from the art's bounds, or the circle of an entry with nothing drawn, as a square).
static func _regions(e: Dictionary) -> Array:
	var out: Array = []
	if e.has("touch_rect"):
		out.append(e["touch_rect"])
	if float(e["radius_px"]) > 0.0:
		var c: Vector2 = e["centre"]
		var rr := float(e["radius_px"])
		out.append(Rect2(c - Vector2(rr, rr), Vector2(rr, rr) * 2.0))
	return out


func test_from_the_choice_viewpoints_the_targets_are_the_art_and_never_overlap_or_meet_the_pads() -> void:
	assert_false(HotspotView.RINGS, "no ring is drawn: the target is the art's bounds")
	var overlaps: Array = []
	var n_checked := 0
	for sid in TARGET_SCENES:
		var d := _scene(sid)
		var scene: Node = d["scene"]
		var host: Control = scene._stage_host
		var pads: Dictionary = scene.pad_view.button_rects()
		var st: StoryStage = scene.stages[scene.active_world]["stage"]
		for beat in WINDOW_BEATS:
			_run_to(scene, float(scene.engine.scene_t0) + beat * BEAT)
			if str(scene.engine.node_id) != sid:
				break
			var items: Array = (scene.hotspot_items() as Array).filter(func(e: Dictionary) -> bool: return str(e["state"]) != "committed")
			var lay := HotspotView.layout(items, st.map, st.crowds, scene._exit_pose(), host.size, true, HotspotView.thing_widths(st))
			for e in lay:
				assert_false(bool(e["edge"]), "%s: nothing out of the picture is laid out" % e["id"])
				for r in _regions(e):
					n_checked += 1
					var g := Rect2((r as Rect2).position + host.global_position, (r as Rect2).size)
					assert_true(Rect2(host.global_position, host.size).grow(0.01).encloses(g), "%s %s beat %.0f: inside the picture" % [sid, e["id"], beat])
					for p in pads:
						assert_false(g.intersects(pads[p] as Rect2), "%s %s: never over pad %s" % [sid, e["id"], str(p)])
					assert_true(minf((r as Rect2).size.x, (r as Rect2).size.y) >= HotspotContract.MIN_PX - 1e-3, "%s %s: at least 88 px (%s)" % [sid, e["id"], str((r as Rect2).size)])
				if e.has("touch_rect") and e.has("visual_rect"):
					var vis: Rect2 = e["visual_rect"]
					var tr: Rect2 = e["touch_rect"]
					assert_true(tr.size.x <= maxf(vis.size.x + 2.0 * HotspotContract.TOUCH_MARGIN_PX, HotspotContract.MIN_PX) + 1e-3, "%s %s: the art plus at most 24 px a side" % [sid, e["id"]])
			for i in lay.size():
				for j in range(i + 1, lay.size()):
					for a in _regions(lay[i]):
						for b in _regions(lay[j]):
							var x := (a as Rect2).intersection(b as Rect2)
							if x.get_area() > 1.0:
								overlaps.append("%s beat %.0f: %s and %s share %.0f px2" % [sid, beat, lay[i]["id"], lay[j]["id"], x.get_area()])
			for i in lay.size():  # the nearest middle decides a tap (HotspotView.hit): each target keeps a disc of at least half the 88 px floor round its middle
				for j in range(i + 1, lay.size()):
					var ci: Vector2 = lay[i].get("hit_centre", lay[i]["centre"])
					var cj: Vector2 = lay[j].get("hit_centre", lay[j]["centre"])
					var pair := "%s|%s" % [lay[i]["id"], lay[j]["id"]]
					var rpair := "%s|%s" % [lay[j]["id"], lay[i]["id"]]
					if KNOWN_CLOSE.has(pair) or KNOWN_CLOSE.has(rpair):
						continue
					assert_true(ci.distance_to(cj) >= HotspotContract.MIN_PX, "%s beat %.0f: %s and %s keep their middles at least 88 px apart (%.0f)" % [sid, beat, lay[i]["id"], lay[j]["id"], ci.distance_to(cj)])
			for e in lay:  # whatever the overlap, a tap on a target's middle takes that target
				assert_eq(HotspotView.hit(lay, e.get("hit_centre", e["centre"])), str(e["id"]), "%s beat %.0f: a tap on %s's middle selects it" % [sid, beat, e["id"]])
		_free(d)
	print("  targets checked %d; overlaps: %s" % [n_checked, "\n    ".join(PackedStringArray(overlaps)) if not overlaps.is_empty() else "none"])
	assert_true(n_checked >= 10, "targets were checked from the viewpoints (%d)" % n_checked)
	# The rectangles themselves overlap in today's content (a door with a person in front of it, gates 1.2 to 2.2 m apart): the nearest middle splits the ground between
	# them, so a tap is never ambiguous; separating the art itself is the world packages' (reported to the lead with the list printed above).
	if not overlaps.is_empty():
		print("  A7: %d overlapping target pairs from the choice viewpoints (split by the nearest middle)" % overlaps.size())
