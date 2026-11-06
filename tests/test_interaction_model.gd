extends TestCase
## Work package N2.1 (docs/parallel-development/INTERACTION_DESIGN.md section 2, 3.5, 3.6): the pure parts of selection open for the whole scene. The cap of choices is 8 (a 9th is refused, a hub may
## allow 10), the smallest touch target is 88 px (72 now fails; the Bassment keeps 72), the touch region is built on screen from the object's visual bounds plus at most 24 px, a pick is held across
## a lap until the departure lap commits it, and reactive objects are a list of their own that never routes, never counts in the cap and never changes the pick.

const TMP := "user://test_interaction_model"


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


func _wh(extra: Dictionary, id: String) -> Dictionary:  # a raw warehouse hotspot row (as the data files hold them)
	var h := {"id": "warehouse.t." + id, "world": "warehouse", "scene": "warehouse", "map": "night_one", "anchor": {"waypoint": "to_bar"}, "kind": "exit", "on_success": {"route": "warehouse.bar"},
		"on_failure": {"route": "warehouse.balcony"}, "default": false}
	for k in extra:
		h[k] = extra[k]
	return h


func _ctx() -> Dictionary:
	return {"where": "t", "map": "night_one", "world": "warehouse", "routes": ["warehouse.bar", "warehouse.balcony"], "default_route": "warehouse.bar"}


func _load_with(hotspots: Array, reactives: Array) -> RunData:
	DirAccess.make_dir_recursive_absolute(TMP)
	var f := FileAccess.open(TMP + "/warehouse.json", FileAccess.WRITE)
	f.store_string(JSON.stringify({"world": "warehouse", "hotspots": hotspots, "reactives": reactives}))
	f.close()
	return RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, -1, RunData.ARRANGEMENTS_DIR, TMP)


func _clean() -> void:
	for f in DirAccess.get_files_at(TMP):
		DirAccess.remove_absolute(TMP + "/" + f)


func _errs(d: RunData, needle: String) -> bool:
	return d.errors.any(func(e: String) -> bool: return e.contains(needle))


# --- the cap and the smallest target ----------------------------------------------------------------------------------------

func test_eight_choices_fit_a_ninth_is_refused_and_a_hub_may_allow_ten() -> void:
	assert_eq(HotspotContract.MAX_PER_SCENE, 8, "the cap of choices is 8 (lead ruling 1)")
	assert_eq(HotspotContract.MAX_PER_HUB, 10, "a hub may allow 10 (lead ruling 16)")
	var list: Array = [HotspotContract.normalize(_wh({"default": true}, "d"), "warehouse", "night_one")]
	for i in 7:
		list.append(HotspotContract.normalize(_wh({}, "c%d" % i), "warehouse", "night_one"))
	var errors: Array = []
	HotspotContract.validate_scene(list, _ctx(), errors)
	assert_eq(errors, [], "eight choices fit")
	list.append(HotspotContract.normalize(_wh({}, "c9"), "warehouse", "night_one"))
	errors = []
	HotspotContract.validate_scene(list, _ctx(), errors)
	assert_true(errors.any(func(e: String) -> bool: return e.contains("9 hotspots are available at the start; a scene shows 2 to 8")), "a ninth is refused: %s" % str(errors))
	var hub := _ctx()
	hub["max_available"] = 10
	errors = []
	HotspotContract.validate_scene(list, hub, errors)
	assert_eq(errors, [], "a hub's own max_hotspots of 10 lets nine stand")


func test_the_smallest_target_is_88_px_and_72_now_fails_but_the_bassment_keeps_72() -> void:
	assert_eq(HotspotContract.MIN_PX, 88.0)
	assert_eq(HotspotContract.normalize({"id": "x"}, "w", "m")["min_px"], 88.0, "a hotspot without its own min_px gets 88")
	for px in [72, 87]:
		var errors: Array = []
		HotspotContract._validate_one(HotspotContract.normalize(_wh({"min_px": px}, "a"), "warehouse", "night_one"), "h", _ctx(), errors)
		assert_true(errors.any(func(e: String) -> bool: return e.contains("min_px must be at least 88")), "%d px is refused: %s" % [px, str(errors)])
	var ok: Array = []
	HotspotContract._validate_one(HotspotContract.normalize(_wh({"min_px": 88}, "a"), "warehouse", "night_one"), "h", _ctx(), ok)
	assert_false(ok.any(func(e: String) -> bool: return e.contains("min_px")), "88 px passes")
	var bassment := _ctx()
	bassment["min_px_floor"] = HotspotContract.BASSMENT_MIN_PX
	var b: Array = []
	HotspotContract._validate_one(HotspotContract.normalize(_wh({"min_px": 72}, "a"), "warehouse", "night_one"), "h", bassment, b)
	assert_false(b.any(func(e: String) -> bool: return e.contains("min_px")), "the Bassment keeps its 72 px (lead ruling 20)")
	assert_eq(TrialData.load_default().errors, [], "the shipped Bassment still loads")


func test_every_shipped_run_and_path_loads_with_the_new_floor() -> void:
	for run in ["", "gospel", "squadron", "ember"]:
		var d := RunData.load_default() if run == "" else RunData.load_path(run)
		assert_eq(d.errors, [], "%s loads clean" % (run if run != "" else "main"))
		for sid in d.hotspots:
			for h in d.hotspots[sid]:
				assert_true(float(h["min_px"]) >= 88.0, "%s is at least 88 px" % h["id"])


# --- the touch region: the object plus at most 24 px -------------------------------------------------------------------------

func test_the_touch_rectangle_is_the_visual_grown_by_24_and_at_least_88() -> void:
	var view := Vector2(1280, 460.8)
	var big := HotspotView.touch_rect_of(Rect2(400, 100, 200, 300), 88.0, view)
	assert_eq(big, Rect2(376, 76, 248, 348), "a large object: its bounds plus 24 px each side")
	var small := HotspotView.touch_rect_of(Rect2(600, 200, 20, 30), 88.0, view)
	assert_near(small.size.x, 88.0, 1e-4, "a small object: widened to 88 px")
	assert_near(small.size.y, 88.0, 1e-4)
	assert_near(small.get_center().x, 610.0, 1e-4, "about its middle")
	var mid := HotspotView.touch_rect_of(Rect2(600, 200, 60, 30), 88.0, view)
	assert_near(mid.size.x, 108.0, 1e-4, "60 + 48: the margin alone gives the size")
	assert_near(mid.size.y, 88.0, 1e-4, "30 + 48 = 78 is widened to 88")
	var edge := HotspotView.touch_rect_of(Rect2(0, 420, 60, 40.8), 88.0, view)
	assert_true(edge.position.x >= 0.0 and edge.end.y <= view.y + 1e-4, "kept inside the view, never over the pads below it: %s" % str(edge))
	assert_near(edge.size.x, 108.0, 1e-4, "moved in, not cut")
	assert_near(edge.size.y, 88.8, 1e-4)


func test_layout_builds_the_touch_region_from_the_object_on_screen() -> void:
	var m := StoryMap.load_chapter("night_one")
	var w: Dictionary = m.waypoint("floor_centre")
	var pose := {"cam": Vector3((w["at"] as Vector2).x, m.eye_height, (w["at"] as Vector2).y), "yaw": float(w["yaw"]), "pitch": 0.0}
	var view := Vector2(1280, 460.8)
	var ents: Array = []
	for t in m.things:
		ents.append({"hotspot": HotspotContract.normalize({"id": "thing_" + str(t["id"]), "kind": "object", "anchor": {"thing": str(t["id"])}, "on_success": {"energy": 1}}, "warehouse", "night_one"), "state": "available"})
	ents.append({"hotspot": HotspotContract.normalize({"id": "door", "kind": "exit", "anchor": {"waypoint": "to_bar"}, "on_success": {"route": "x"}}, "warehouse", "night_one"), "state": "available"})
	ents.append({"hotspot": HotspotContract.normalize({"id": "spot", "kind": "object", "anchor": {"pos": [0.0, 1.0, 2.0]}, "on_success": {"energy": 1}}, "warehouse", "night_one"), "state": "available"})
	var lay := HotspotView.layout(ents, m, {}, pose, view, true)
	var with_rect := 0
	for e in lay:
		if bool(e["edge"]):
			assert_true(float(e["radius_px"]) * 2.0 >= 88.0 - 1e-3, "%s: an edge beacon is 88 px" % e["id"])
			continue
		var vis: Rect2 = e.get("visual_rect", Rect2())
		if not e.has("touch_rect"):
			assert_true(float(e["radius_px"]) * 2.0 >= 88.0 - 1e-3, "%s: nothing drawn there: the ring's circle, at least 88 px" % e["id"])
			continue
		with_rect += 1
		var tr: Rect2 = e["touch_rect"]
		assert_eq(float(e["radius_px"]), 0.0, "%s: no circle beyond the object" % e["id"])
		assert_true(tr.size.x >= 88.0 - 1e-3 and tr.size.y >= 88.0 - 1e-3, "%s: at least 88 px both ways: %s" % [e["id"], str(tr.size)])
		assert_true(Rect2(Vector2.ZERO, view).encloses(tr), "%s: inside the view" % e["id"])
		assert_true(tr.size.x <= maxf(vis.size.x + 48.0, 88.0) + 1e-3 and tr.size.y <= maxf(vis.size.y + 48.0, 88.0) + 1e-3, "%s: no bigger than the object plus 24 px a side (or 88): %s over %s" % [e["id"], str(tr), str(vis)])
		assert_eq(HotspotView.hit([e], tr.get_center()), str(e["id"]), "%s: a tap in its middle hits it" % e["id"])
	assert_true(with_rect >= 3, "several things of the floor were laid out from their drawn bounds (%d)" % with_rect)
	var spot: Array = lay.filter(func(e: Dictionary) -> bool: return str(e["id"]) == "spot")
	if not spot.is_empty() and not bool(spot[0]["edge"]):
		assert_false(spot[0].has("touch_rect"), "an empty spot has no invisible rectangle (INTERACTION_DESIGN.md 3.6)")


# --- the held pick ---------------------------------------------------------------------------------------------------------------

func test_a_pick_made_in_the_first_block_is_held_and_commits_once_at_the_last_decision() -> void:
	var hs := _engine_for([_h("a", {"default": true}), _h("b"), _h("c")])
	assert_false(hs.select("b", 0, false), "the engine's own route window rule is unchanged")
	assert_true(hs.select("b", 0, true), "selection open: a choice is touchable in block 0")
	assert_eq(hs.current_id(0), "b")
	for b in 3:
		assert_eq(hs.on_block(b, true), {}, "block %d: a final choice does not commit before the last block" % b)
		assert_eq(hs.selected, "b", "held through block %d" % b)
	assert_true(hs.select("c", 3, true), "changed in the last block")
	var out := hs.commit_final(true)
	assert_eq(str(out["hotspot"]), "c", "the last pick commits")
	assert_eq(hs.log.size(), 1, "once")
	assert_false(hs.select("b", 3, true), "nothing is touched after the commit")


func test_a_track_scenes_lap_before_the_doors_open_keeps_the_pick_for_the_next_lap() -> void:
	var hs := _engine_for([_h("a", {"default": true}), _h("b")])
	assert_true(hs.select("b", 1, true))
	hs.begin_lap(55.0)
	assert_eq(hs.selected, "b", "the pick waits for the next departure boundary (contract: a request on a lap that is not a departure lap stays pending)")
	assert_eq(hs.committed, "")
	assert_true(hs.deselect("b"), "N2.2's request_closed can withdraw it")
	assert_eq(hs.current_id(0), "a", "and the default is current again")
	assert_false(hs.deselect("b"))


# --- reactive objects ---------------------------------------------------------------------------------------------------------

func test_reactive_objects_load_apart_never_count_in_the_cap_and_never_route() -> void:
	var hs_rows := [_wh({"default": true}, "a"), _wh({"anchor": {"waypoint": "to_balcony"}, "on_success": {"route": "warehouse.balcony"}, "on_failure": {"route": "warehouse.bar"}}, "b")]
	var rx: Array = []
	for i in 9:
		rx.append({"id": "warehouse.r%d" % i, "scene": "warehouse", "anchor": {"thing": "disco_ball"}, "reaction": ["flare", "pulse", "shake", "squash"][i % 4]})
	rx.append({"id": "warehouse.rflag", "scene": "warehouse", "anchor": {"pos": [0.0, 1.0, 2.0]}, "reaction": "flare", "touch": {"w": 1.0, "h": 1.5}, "effect": {"flags_set": ["wh_poked"]}})
	var d := _load_with(hs_rows, rx)
	assert_eq(d.errors, [], "two choices and ten reactive objects: nothing over the cap")
	assert_eq(d.hotspots_of("warehouse").size(), 2, "the reactive objects are not hotspots")
	assert_eq(d.reactives_of("warehouse").size(), 10)
	var r0: Dictionary = d.reactives_of("warehouse")[0]
	assert_true(HotspotContract.is_reactive(r0))
	assert_false(bool(r0["default"]), "never a default")
	assert_eq(r0["on_success"], {}, "no outcome")
	var hs := RunHotspots.new(d, {}, {})
	hs.begin_scene("warehouse", 60.0)
	assert_false(hs.shown(0, true).any(func(h: Dictionary) -> bool: return HotspotContract.is_reactive(h)), "never on show as a choice")
	assert_false(hs.select("warehouse.r0", 3, true), "never selectable")
	assert_true(hs.select("warehouse.t.b", 0, true))
	var out := hs.react("warehouse.rflag")
	assert_eq(str(out["reaction"]), "flare")
	assert_eq(hs.selected, "warehouse.t.b", "a reaction leaves the pick alone")
	assert_true(hs.has_flag("wh_poked"), "its optional effect sets a per-run flag (assumption A5)")
	assert_eq(hs.react("warehouse.t.b"), {}, "a choice is not a reactive object")
	var c := hs.commit_final(true)
	assert_eq(str(c["hotspot"]), "warehouse.t.b", "the commit is the choice's")
	var hs2 := RunHotspots.new(d, {}, {})
	hs2.begin_scene("warehouse", 60.0)
	hs2.react("warehouse.r1")
	assert_eq(str(hs2.commit_final(true)["hotspot"]), "warehouse.t.a", "reacting only: the scene's default exit, as if nothing was tapped")
	_clean()


func test_the_validator_names_bad_reactive_rows() -> void:
	var hs_rows := [_wh({"default": true}, "a"), _wh({"anchor": {"waypoint": "to_balcony"}, "on_success": {"route": "warehouse.balcony"}, "on_failure": {"route": "warehouse.bar"}}, "b")]
	var cases := [
		[{"on_success": {"route": "warehouse.bar"}}, "'on_success' is not a field"],
		[{"route": "warehouse.bar"}, "'route' is not a field"],
		[{"default": true}, "'default' is not a field"],
		[{"reaction": "explode"}, "reaction 'explode'"],
		[{"anchor": {"waypoint": "to_bar"}}, "anchor must be exactly one of"],
		[{"anchor": {"thing": "no_such"}}, "anchor thing 'no_such'"],
		[{"effect": {"flags_set": ["keep:x"]}}, "must be a per-run flag"],
		[{"effect": {"energy": 5}}, "effect may only be"],
		[{"touch": {"w": 0, "h": 1}}, "touch must be"],
		[{"id": "warehouse.t.a"}, "id missing or duplicated"],
	]
	for c in cases:
		var row := {"id": "warehouse.rx", "scene": "warehouse", "anchor": {"thing": "disco_ball"}, "reaction": "flare"}
		for k in c[0]:
			row[k] = c[0][k]
		var d := _load_with(hs_rows, [row])
		assert_true(_errs(d, str(c[1])), "'%s' is reported: %s" % [c[1], str(d.errors)])
	var other := _load_with(hs_rows, [{"id": "x", "scene": "mothership", "anchor": {"thing": "disco_ball"}, "reaction": "flare"}])
	assert_true(_errs(other, "is not a scene of world warehouse"), str(other.errors))
	_clean()
