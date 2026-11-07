extends TestCase
## World-staged activities (CONTRACTS.md 10, ruling 38, package A8): an activity's things are drawn by the stage in the room (H8.1: at depth, culled by sector, lit like the
## crowd, sorted with it), they move and change frame, their screen point is the projection's; its people play per-activity states (or the named fallback); its feedback marks
## animate and run out in song time; its controls morph out of the pads over the beat before the seat and back over the beat after the hand-back, never leaving the strip
## empty; and in a run an activity with no view at all stages itself through the port it is handed.

const BEAT := 60.0 / 174.0
const CRATE := "engine_test_crate"  # 2 x 2 cells (sidecar grid), PLACEHOLDER art
const GLASS := "engine_test_glass"  # 3 cells in a row, no sidecar (the grid is inferred)
const STRIP := Vector2(1280, 460)  # the stage area of a 1280 x 720 window (the pads take the rest)
const REPLACE_CFG := {"id": "staged", "mode": "replace", "controls": 2, "control_ids": ["same", "different"], "lead_in_beats": 4.0, "wobble_at": 0, "fall_at": 0}
const TMP_SAVE := "user://test_world_things_save.json"
const STAGED := preload("res://tests/fixtures/staged_activity.gd")

var _saved: RunProgress


func _stage(size := STRIP) -> StoryStage:
	var run := StoryRun.create({})
	var stage := StoryStage.new()
	stage.size = size
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_default(), run.data, run)
	stage.attach_world(stage.map, true)
	stage.lowres.size = size
	stage.lowres._fit()
	return stage


func _look_from(stage: StoryStage, wp: String, t := 2.0) -> void:
	stage.player.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": wp, "bars": 0.01, "cut": true}})
	stage.update(t, 60.0)


func _crate(at: Vector2, sector: String, frame: Variant = 0, size := [1.0, 1.0]) -> Dictionary:
	return {"id": "crate", "sprite": CRATE, "at": [at.x, at.y], "sector": sector, "size": size, "frame": frame}


func test_a_thing_in_a_sector_is_drawn_at_depth_tall_enough_and_inside_the_strip() -> void:
	var stage := _stage()
	_look_from(stage, "floor_centre")  # (0, 6.5) looking toward -z
	stage.set_things([_crate(Vector2(0.0, 0.5), "floor")])  # 6 m ahead, 1 m tall
	stage.update(2.0, 60.0)
	var dyn: StoryDynamicThings = stage.world.dynamic
	assert_eq(dyn.errors, [], "the sheet loads")
	assert_eq(dyn.drawn, 1, "drawn")
	assert_true(dyn.get_parent() == stage.crowd.get_parent(), "it stands in the crowd's overlay inside the low-res viewport")
	var r: Variant = stage.thing_screen_rect("crate")
	assert_true(r != null, "it has a screen rect")
	if r == null:
		stage.free()
		return
	var rr: Rect2 = r
	print("  crate 1 m at 6 m: stage rect %s" % str(rr))
	assert_true(Rect2(Vector2.ZERO, STRIP).encloses(rr), "inside the stage strip")
	assert_true(rr.size.y >= 48.0, "at least 48 px tall at 1280 x 720 (%.1f)" % rr.size.y)
	assert_near(rr.size.x, rr.size.y, 2.0, "a 1 x 1 m thing is square on screen")
	# the screen point is the projection's: the centre of the box from its feet to its top
	var pose := {"cam": stage.player.pose_at(2.0)["cam"], "yaw": float(stage.player.pose_at(2.0)["yaw"]), "pitch": float(stage.player.pose_at(2.0).get("pitch", 0.0))}
	var sub := Vector2(stage.lowres.sub.size)
	var lo := StoryProjector.project(Vector3(0.0, 0.0, 0.5), pose, sub)
	var hi := StoryProjector.project(Vector3(0.0, 1.0, 0.5), pose, sub)
	var want := ((lo["screen"] as Vector2) + (hi["screen"] as Vector2)) * 0.5
	assert_true((stage.world.thing_screen_point("crate") as Vector2).distance_to(want) < 0.75, "the low-res screen point is the projected centre (%s vs %s)" % [str(stage.world.thing_screen_point("crate")), str(want)])
	assert_true((stage.thing_screen_point("crate") as Vector2).distance_to(want * stage.lowres_scale()) < 2.0, "and in stage pixels, scaled")
	# z-sorted with the crowd: its node takes a place in the one far-to-near order
	var node := dyn.node_of("crate")
	assert_true(node.visible and node.z_index >= 1, "sorted with the people (z %d)" % node.z_index)
	stage.free()


func test_a_thing_is_culled_when_its_sector_is_out_of_sight() -> void:
	var stage := _stage()
	_look_from(stage, "floor_centre")
	var hidden := ""
	for s: Dictionary in stage.map.sectors:
		if not stage._vis.has(str(s["id"])):
			hidden = str(s["id"])
			break
	assert_true(hidden != "", "some sector is out of sight from the floor's centre")
	var poly: PackedVector2Array = stage.map.sector(hidden)["poly"]
	var c := Vector2.ZERO
	for p in poly:
		c += p
	c /= float(poly.size())
	stage.set_things([_crate(c, hidden), {"id": "seen", "sprite": CRATE, "at": [0.0, 1.5], "sector": "floor", "size": [1.0, 1.0], "frame": 0}])
	stage.update(2.0, 60.0)
	assert_eq(stage.world.dynamic.drawn, 1, "only the one in a visible sector is drawn")
	assert_false(stage.world.dynamic.node_of("crate").visible, "the thing in %s is culled" % hidden)
	assert_true(stage.thing_screen_point("crate") == null, "no screen point when culled")
	assert_true(stage.thing_screen_point("seen") != null)
	stage.free()


func test_a_thing_moves_with_at_and_changes_frame() -> void:
	var stage := _stage()
	_look_from(stage, "floor_centre")
	stage.set_things([_crate(Vector2(-1.0, 1.0), "floor", 0)])
	stage.update(2.0, 60.0)
	var p0: Vector2 = stage.thing_screen_point("crate")
	var dyn: StoryDynamicThings = stage.world.dynamic
	var reg0: Rect2 = dyn.node_of("crate").region
	assert_eq(reg0, Rect2(0, 0, 64, 64), "frame 0: the first cell of the 2 x 2 sheet")
	stage.set_things([_crate(Vector2(1.0, 1.0), "floor", [1, 1])])  # moved 2 m to the right, open and lit
	stage.update(2.1, 60.0)
	var p1: Vector2 = stage.thing_screen_point("crate")
	assert_true(p1.x > p0.x + 20.0, "moved right on screen (%s -> %s)" % [str(p0), str(p1)])
	assert_eq(dyn.node_of("crate").region, Rect2(64, 64, 64, 64), "frame [1, 1]: row 1, column 1")
	stage.set_things([_crate(Vector2(1.0, 1.0), "floor", 2)])
	stage.update(2.2, 60.0)
	assert_eq(dyn.node_of("crate").region, Rect2(0, 64, 64, 64), "frame 2 (row-major): row 1, column 0")
	# a sheet without a sidecar: the grid from the thing's aspect (3 cells of 48 x 72 for a 2:3 thing)
	stage.set_things([{"id": "glass", "sprite": GLASS, "at": [0.0, 2.0], "sector": "floor", "size": [0.2, 0.3], "frame": 2, "y": 1.0, "anchor": "center"}])
	stage.update(2.3, 60.0)
	assert_eq(dyn.node_of("glass").region, Rect2(96, 0, 48, 72), "inferred grid 3 x 1, frame 2")
	assert_false(is_instance_valid(dyn.node_of("crate")) and dyn.node_of("crate") != null, "a thing left out of the list is gone")
	# `y` with the centre anchor lifts it: its centre stands 1 m above the floor
	var r: Rect2 = stage.world.thing_screen_rect("glass")
	var pose: Dictionary = stage.player.pose_at(2.3)
	var c1 := StoryProjector.project(Vector3(0.0, 1.0, 2.0), {"cam": pose["cam"], "yaw": pose["yaw"], "pitch": pose.get("pitch", 0.0)}, Vector2(stage.lowres.sub.size))
	assert_true(r.get_center().distance_to(c1["screen"]) < 0.75, "the centre anchor puts its centre at y (%s vs %s)" % [str(r.get_center()), str(c1["screen"])])
	stage.set_things([])
	stage.update(2.4, 60.0)
	assert_eq(dyn.drawn, 0, "[] clears")
	stage.free()


func test_map_things_and_pieces_have_screen_points_too() -> void:
	var stage := _stage()
	_look_from(stage, "floor_centre")
	var any := ""
	for t: Dictionary in stage.map.things:
		if not t.has("piece") and stage._vis.has(str(t["sector"])):
			any = str(t["id"])
			if stage.world.thing_screen_point(any) != null:
				break
	assert_true(any != "" and stage.world.thing_screen_point(any) != null, "a map thing in sight has a screen point (%s)" % any)
	assert_true(stage.world.thing_screen_point("no_such_thing") == null, "unknown: null")
	stage.free()


func test_people_states_resolve_to_rows_or_a_named_fallback() -> void:
	var stage := _stage()
	var c: StoryCrowd = null
	var id := ""
	for rid in stage.crowds:
		if (stage.crowds[rid] as StoryCrowd).actors.has("b01"):
			c = stage.crowds[rid]
			id = "b01"
	assert_true(c != null, "the Warehouse has its barman b01")
	if c == null:
		stage.free()
		return
	var ch: StoryCharacter = c.actors[id]["node"]
	var table := []
	for st: String in StoryCrowd.ACTIVITY_STATES:
		var r := c.resolve_state(id, st)
		table.append("%s -> %s%s%s" % [st, r["state"], ("@" + str(r["face"])) if str(r["face"]) != "" else "", " (fallback)" if bool(r["fallback"]) else ""])
		if ch.uses_sheet():
			assert_true((ch.sheet["states"] as Dictionary).has(str(r["state"])), "%s resolves to a row the sheet has (%s)" % [st, r["state"]])
		else:
			assert_true(str(r["state"]) in StoryCharacter.STATES, "%s resolves to a rig state (%s)" % [st, r["state"]])
		var cands: Array = (StoryCrowd.ACTIVITY_STATES[st] as Array).map(func(x: Array) -> String: return str(x[0]))
		assert_true(str(r["state"]) in cands, "%s: the resolution is one of its named candidates" % st)
	print("  b01 (%s): %s" % ["sheet" if ch.uses_sheet() else "rig", ", ".join(PackedStringArray(table))])
	for st: String in ["idle", "look", "cheer", "clap", "hands_up"]:
		var r2 := c.resolve_state(id, st)
		var has_it: bool = (ch.sheet["states"] as Dictionary).has(st) if ch.uses_sheet() else st in StoryCharacter.STATES
		if has_it:
			assert_eq(str(r2["state"]), st, "a crowd state the sheet has plays as it is: %s" % st)
		else:
			assert_true(bool(r2["fallback"]) and str(r2["state"]) in (StoryCrowd.CROWD_FALLBACKS[st] as Array).map(func(x: Array) -> String: return str(x[0])), "%s: a named fallback (%s)" % [st, r2["state"]])
		table.append("%s -> %s" % [st, r2["state"]])
	print("  b01 crowd states: %s" % ", ".join(PackedStringArray(table.slice(StoryCrowd.ACTIVITY_STATES.size()))))
	var plain := c.resolve_state("c01", "clap")
	assert_true(not plain.is_empty(), "a dancer resolves too: clap -> %s" % str(plain.get("state", "")))
	# directing through the stage: forced, timed, then back to their own life
	var res := stage.people(id, "raise_glass", 10.0, 2.0)
	assert_eq(str(res["state"]), str(c.resolve_state(id, "raise_glass")["state"]))
	assert_eq(c.directing(id, 10.5), "activity", "directed by the activity")
	assert_eq(c.directing(id, 12.5), "", "for dur seconds only")
	stage.people(id, "waiting", 13.0, 0.0)
	assert_eq(c.directing(id, 500.0), "activity", "dur 0: until told otherwise")
	assert_eq(stage.people("nobody_here", "happy", 1.0, 0.0), {}, "an unknown actor is a no-op")
	stage.free()


func test_feedback_marks_animate_in_song_time_and_expire() -> void:
	for k: String in RunActivityFeedback.KINDS:
		var d := RunActivityFeedback.beats_of(k)
		assert_true(RunActivityFeedback.look(k, -0.01).is_empty(), "%s: nothing before it starts" % k)
		assert_false(RunActivityFeedback.look(k, 0.0).is_empty(), "%s: shown at once" % k)
		assert_true(RunActivityFeedback.look(k, d).is_empty(), "%s: gone after %.1f beats" % [k, d])
		assert_true(float(RunActivityFeedback.look(k, d * 0.95)["alpha"]) < float(RunActivityFeedback.look(k, d * 0.1)["alpha"]), "%s: fades" % k)
	assert_eq(RunActivityFeedback.beats_of("tick"), 1.0, "a tick lasts a beat")
	var pops := [0.0, 0.1, 0.2, 0.5].map(func(b: float) -> float: return float(RunActivityFeedback.look("tick", b)["scale"]))
	assert_true(float(pops[2]) > float(pops[0]) and float(pops[2]) > float(pops[3]), "a tick pops: grows then settles %s" % str(pops))
	var shakes := [0.05, 0.1, 0.15, 0.2].map(func(b: float) -> float: return absf(float(RunActivityFeedback.look("cross", b)["dx"])))
	assert_true(shakes.max() > 0.05, "a cross shakes %s" % str(shakes))
	assert_eq(float(RunActivityFeedback.look("cross", 0.1, true)["dx"]), 0.0, "reduced effects: no shake")
	assert_true(float(RunActivityFeedback.look("glow", 0.6)["radius"]) > float(RunActivityFeedback.look("glow", 0.0)["radius"]), "a glow swells")
	var fb := RunActivityFeedback.new()
	fb.beat_s = BEAT
	fb.entries = [{"thing": "a", "kind": "tick", "t": 1.0}, {"thing": "b", "kind": "glow", "t": 1.0}]
	fb.prune(1.0 + 1.2 * BEAT)
	assert_eq(fb.entries.map(func(e: Dictionary) -> String: return str(e["thing"])), ["b"], "the tick ran out after a beat, the glow still swells")
	fb.prune(1.0 + 1.6 * BEAT)
	assert_eq(fb.entries.size(), 0, "and then the glow")
	fb.free()


# --- the controls' morph --------------------------------------------------------------------------------------------------------------

func _morph_rig(n: int) -> Dictionary:
	var pv := StoryPadView.new()
	pv.size = Vector2(1280, 260)
	tree.root.add_child(pv)
	var layer := RunActivityInput.new()
	layer.kind = "controls"
	for i in n:
		layer.ids.append("c%d" % i)
		layer.specs.append({"id": "c%d" % i, "label": "", "pictogram": ["same", "different", "star", "drop"][i]})
	layer.pad_view = pv
	layer.beat_s = BEAT
	layer.t_in = 10.0
	layer.t_out = 30.0
	pv.slot_fn = layer.slot
	return {"pv": pv, "layer": layer}


func test_the_controls_morph_out_of_the_pads_at_the_boundary_and_back() -> void:
	for n in [2, 4]:
		var rig := _morph_rig(n)
		var pv: StoryPadView = rig["pv"]
		var layer: RunActivityInput = rig["layer"]
		var rects: Dictionary = pv._pad_rects()
		var slot := func(pad: int, t: float) -> Dictionary: return layer.slot(pad, rects[pad], t)
		for pad in [1, 2, 3, 4]:
			assert_true((slot.call(pad, 10.0 - BEAT) as Dictionary).is_empty(), "%d controls, boundary minus a beat: pad %d is the pad" % [n, pad])
			assert_true((slot.call(pad, 30.0 + BEAT) as Dictionary).is_empty(), "%d controls, end boundary plus a beat: pad %d is the pad again" % [n, pad])
		for pad in ([1, 3] if n == 2 else [1, 2, 3, 4]):
			var at: Dictionary = slot.call(pad, 10.0)
			assert_near(float(at.get("mix", 0.0)), 1.0, 1e-6, "%d controls, at the boundary: slot %d is the control" % [n, pad])
			assert_true((at.get("glyph", Callable()) as Callable).is_valid(), "%d controls: slot %d carries the pictogram" % [n, pad])
			assert_near(float(at["scale"]), 1.0, 1e-6, "the pulse is over at the boundary")
			var mid: Dictionary = slot.call(pad, 10.0 - 0.5 * BEAT)
			assert_true(float(mid["mix"]) > 0.3 and float(mid["mix"]) < 0.7, "half way through the beat the glyphs cross-fade (%.2f)" % float(mid["mix"]))
			assert_true(float(mid["scale"]) > 1.03, "with a scale pulse")
			assert_near(float((slot.call(pad, 20.0) as Dictionary)["mix"]), 1.0, 1e-6, "controls while seated")
			assert_near(float((slot.call(pad, 30.0) as Dictionary)["mix"]), 1.0, 1e-6, "still the control on the hand-back boundary")
			assert_true(float((slot.call(pad, 30.0 + 0.5 * BEAT) as Dictionary)["mix"]) < 0.7, "fading back")
		if n == 2:
			var wide: Rect2 = (rects[1] as Rect2).merge(rects[2])
			assert_eq((slot.call(1, 12.0) as Dictionary)["rect"], wide, "two controls: the left pair is one slot")
			assert_true(bool((slot.call(2, 12.0) as Dictionary).get("skip", false)), "drawn once, by its first pad")
			assert_false((slot.call(2, 10.0 - 0.5 * BEAT) as Dictionary).has("glyph"), "the second pad of a pair only fades its own glyph")
		# never a frame with an empty slot: every pad is the pad, or a control, or merged into its pair's control that is drawn
		var t := 10.0 - 2.0 * BEAT
		var empty := 0
		while t < 30.0 + 2.0 * BEAT:
			for pad in [1, 2, 3, 4]:
				var s: Dictionary = slot.call(pad, t)
				if bool(s.get("skip", false)):
					var prim := 1 if pad <= 2 else 3
					var ps: Dictionary = slot.call(prim, t)
					if ps.is_empty() or bool(ps.get("skip", false)):
						empty += 1
				elif not s.is_empty() and float(s["mix"]) <= 0.0:
					empty += 1
			t += 1.0 / 60.0
		assert_eq(empty, 0, "%d controls: no frame where a slot shows neither pad nor control" % n)
		assert_true(layer.drawn_by_pads(), "the pads draw the controls (the layer draws nothing of its own)")
		pv.free()
		layer.free()


func test_pictograms_come_from_the_controls_own_hook_or_the_helper() -> void:
	var seen := []
	var ci := Control.new()
	tree.root.add_child(ci)
	var two := func(c: CanvasItem, r: Rect2) -> void: seen.append(["two", r])
	var three := func(c: CanvasItem, r: Rect2, a: float) -> void: seen.append(["three", a])
	assert_true(ControlPictograms.draw(ci, {"draw": two}, Rect2(0, 0, 10, 10), 1.0, Color.WHITE, true), "the control's own draw(ci, rect)")
	assert_true(ControlPictograms.draw(ci, {"draw": three}, Rect2(0, 0, 10, 10), 0.5, Color.WHITE, true), "or draw(ci, rect, alpha)")
	assert_eq(seen, [["two", Rect2(0, 0, 10, 10)], ["three", 0.5]])
	for nm in ["same", "different", "circle", "square", "diamond", "triangle", "star", "drop", "bottle", "leaf", "bolt"]:
		assert_true(nm in ControlPictograms.SHAPES, "a built-in %s" % nm)
	assert_false(ControlPictograms.draw(ci, {"id": "x", "label": "X"}, Rect2(0, 0, 10, 10), 1.0, Color.WHITE, true), "no pictogram: the caller falls back to the label")
	ci.free()


# --- in a run: an activity with no view stages itself --------------------------------------------------------------------------------

func _scene() -> Dictionary:
	_saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_TAPS", "none")
	OS.set_environment("RW_MINIGAME_TAPS", "")
	Session.run_start_node = ""
	var host := Control.new()
	host.size = Vector2(1280, 720)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = Vector2(1280, 720)
	return {"host": host, "scene": scene}


func _free(d: Dictionary) -> void:
	Session.run_progress = _saved
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	(d["host"] as Control).queue_free()
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_TAPS", "RW_MINIGAME_TAPS"]:
		OS.set_environment(k, "")


func _run_to(scene: Node, t_end: float, each := Callable()) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)
		if each.is_valid():
			each.call(t)


func test_in_a_run_an_activity_without_a_view_stages_things_people_feedback_and_controls() -> void:
	var d := _scene()
	var scene: Node = d["scene"]
	scene.minigames.register("staged", STAGED, REPLACE_CFG)
	for h in scene.data.hotspots["warehouse"]:
		if h["id"] == "warehouse.dancer":
			h["on_success"] = {"activity": "staged"}
	_run_to(scene, 49.5 * BEAT)
	assert_true(scene.hotspot_select("warehouse.dancer"))
	var mg: MinigameController = scene.minigames
	var host: RunMinigameHost = scene._mg
	# the morph starts a beat before the seat (beat 64): the strip is still the pads' to play
	_run_to(scene, 63.2 * BEAT)
	assert_eq(mg.state, "entering")
	assert_true(host.controls_layer != null, "the controls layer stands a beat before the seat (the morph)")
	assert_false(host.owns_strip(), "but the pads still own the taps")
	assert_true(scene.lane_input.enabled and scene.note_lane.visible)
	_run_to(scene, 64.5 * BEAT)
	assert_eq(mg.state, "active")
	var act: Variant = mg.activity
	assert_true(act.world is RunWorldPort, "the activity was handed the run's port as ctx[\"world\"]")
	assert_true(host.view == null, "no view: make_view returned null")
	assert_true(host.owns_strip() and not scene.lane_input.enabled, "seated: the controls own the strip")
	assert_true(scene.pad_view.visible, "the pads stay drawn: they show the controls")
	var st: StoryStage = host.active_stage()
	assert_eq(st.world.dynamic.things.map(func(x: Dictionary) -> String: return str(x["id"])), ["staged_crate"], "its things() reach the active stage every frame")
	var people: Array = host.mode_log.filter(func(l: Dictionary) -> bool: return str(l["kind"]) == "people")
	assert_eq(people.size(), 2, "two people calls")
	assert_eq(str(people[0]["id"]), "b01")
	assert_true(str(people[0]["played"]) != "", "the barman plays raise_glass or its fallback (%s)" % str(people[0]["played"]))
	assert_eq(str(people[1]["played"]), "", "an unknown actor is a no-op")
	assert_true(host.feedback_layer != null and host.feedback_layer.entries.size() >= 1, "a feedback mark from the seat")
	assert_true(host.feedback_layer.get_parent() is CanvasLayer and host.feedback_layer.get_parent().get_parent() == st.lowres.sub, "drawn in the stage's low-res viewport")
	# a control press reaches the activity and its feedback is drawn
	var pad1: Rect2 = scene.pad_view.button_rects()[1]
	assert_eq(scene.dispatch_tap(pad1.get_center()), "activity_controls")
	assert_eq(act.taps, ["same"])
	assert_eq(str(host.feedback_layer.entries[-1]["kind"]), "tick")
	# done at beat 133: the strip is handed back at beat 140 (a lead-in before 144) and the morph back is over by 141
	_run_to(scene, 133.0 * BEAT)
	act.finish_now = true
	_run_to(scene, 134.0 * BEAT)
	assert_eq(mg.state, "resuming")
	assert_eq(st.world.dynamic.things.size(), 0, "a done activity's things are gone (its things() is empty)")
	_run_to(scene, 140.5 * BEAT)
	assert_false(host.owns_strip(), "handed back")
	assert_true(host.controls_layer != null, "the morph back runs for a beat")
	_run_to(scene, 141.2 * BEAT)
	assert_true(host.controls_layer == null, "and is over a beat after the hand-back")
	assert_false((scene.pad_view.slot_fn as Callable).is_valid(), "the slots are the pads' again")
	_run_to(scene, 146.0 * BEAT)
	assert_eq(mg.state, "")
	assert_true(host.mode_log.any(func(l: Dictionary) -> bool: return str(l["kind"]) == "things_off"), "the stage got [] when it ended")
	var kinds: Array = host.mode_log.map(func(l: Dictionary) -> String: return str(l["kind"])).filter(func(k: String) -> bool: return k in ["morph_in", "controls_on", "controls_off", "morph_out"])
	assert_eq(kinds, ["morph_in", "controls_on", "controls_off", "morph_out"], "the strip's life in order")
	_free(d)


## The shot's set-up (tools/engine/shoot_things.gd, docs/shots/engine/things/): two things and a directed barman in the Warehouse bar, seen from inside its door at 16:9 and
## 20:9. Headless, so it checks the projected rects; the pixels are in the sheet.
func test_the_shot_setup_frames_two_things_and_the_barman_at_both_aspects() -> void:
	for sz: Vector2 in [Vector2(1280, 460), Vector2(1600, 460)]:
		OS.set_environment("RW_STORY_CAM", "@7.3:3.1:-90:-4")
		var stage := _stage(sz)
		OS.set_environment("RW_STORY_CAM", "")
		stage.people("b01", "raise_glass", 0.0, 0.0)
		stage.set_things([{"id": "crate", "sprite": CRATE, "at": [10.6, 4.0], "sector": "bar", "size": [0.6, 0.6], "frame": 1},
			{"id": "glass", "sprite": GLASS, "at": [10.4, 2.6], "sector": "bar", "size": [0.2, 0.3], "frame": 2, "y": 1.05, "anchor": "center"}])
		stage.update(4.0, 60.0)
		for id in ["crate", "glass"]:
			var r: Variant = stage.thing_screen_rect(id)
			assert_true(r != null and Rect2(Vector2.ZERO, sz).encloses(r), "%s %s: inside the stage strip (%s)" % [str(sz), id, str(r)])
		assert_true((stage.thing_screen_rect("crate") as Rect2).size.y >= 48.0, "%s: the crate is at least 48 px tall" % str(sz))
		var barman := stage.crowd if stage.crowd.actors.has("b01") else null
		for rid in stage.crowds:
			if (stage.crowds[rid] as StoryCrowd).actors.has("b01"):
				barman = stage.crowds[rid]
		assert_true(barman != null and ((barman as StoryCrowd).actors["b01"]["node"] as Node2D).visible, "%s: the directed barman is drawn" % str(sz))
		assert_eq((barman as StoryCrowd).directing("b01", 4.0), "activity")
		stage.free()
