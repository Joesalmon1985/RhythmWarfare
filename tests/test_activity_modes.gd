extends TestCase
## Activity modes (CONTRACTS.md 4 and 5; hooks H5.1 to H5.6, H4.1, H4.2): a REPLACE activity suspends the rhythm from its seat (no cue charted, the charted ones
## withdrawn, its blocks neutral: no miss, no energy, no wobble, no rail step) and judging resumes on the boundary ContractShapes.resume_boundary computes, with a
## lead-in; its controls own the pad strip meanwhile (a strip tap reaches them, a pad press is refused). An OVERLAY activity keeps the pads and hears the judge events
## and block results. A RHYTHM activity (the blackjack table) is unchanged.

const BEAT := 60.0 / 174.0
const TMP_SAVE := "user://test_activity_modes_save.json"
const RACE := "res://tests/fixtures/stub_race_activity.gd"
const REPLACE_CFG := {"id": "fake_replace", "mode": "replace", "controls": 2, "control_ids": ["same", "different"], "lead_in_beats": 4.0, "wobble_at": 0, "fall_at": 0}
const OVERLAY_CFG := {"id": "stub_race", "mode": "overlay", "controls": 0, "wobble_at": 0, "fall_at": 0}

var _saved: RunProgress


# --- pure: the engine and the controller -------------------------------------------------------------------------------------

func _engine() -> RunEngine:
	var d := RunData.load_default()
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.begin("warehouse")
	return e


## Advances the engine and the controller together to `t_end` (60 frames a second): `per_frame.call(e, c, t)` first; the events reach the controller as RunPlay
## hands them on; every cue is pressed on time when `plays.call(t)` is true, a withdrawn cue never.
func _drive(e: RunEngine, c: MinigameController, t_end: float, per_frame: Callable, plays: Callable) -> Array:
	var events: Array = []
	var pressed := {}
	var released := {}
	var t := 0.0
	while t < t_end and not e.over:
		per_frame.call(e, c, t)
		var evs := e.update(t)
		for ev: Dictionary in evs:
			match str(ev["kind"]):
				"judge":
					c.on_judge(ev["event"], float(ev["t"]))
				"block_result":
					c.on_block_result(bool(ev["passed"]), float(ev["t"]))
					c.on_block(ev)
		events.append_array(evs)
		c.update(t)
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			if pressed.has(i) or float(n["time"]) > t:
				continue
			pressed[i] = bool(plays.call(float(n["time"]))) and not e.judge.is_withdrawn(i)
			if pressed[i]:
				e.press(int(n["pad"]), float(n["time"]))
		for i in pressed:
			var n: Dictionary = e.level.notes[i]
			if pressed[i] and n["type"] == "hold" and not released.has(i) and float(n["end_time"]) <= t:
				released[i] = true
				e.release(int(n["pad"]), float(n["end_time"]))
		t += 1.0 / 60.0
	return events


func _of_kind(events: Array, kind: String) -> Array:
	return events.filter(func(ev: Dictionary) -> bool: return str(ev["kind"]) == kind)


func _block_t0(e: RunEngine, ev: Dictionary) -> float:
	return float(ev["t"]) - e._decision_beat() * e.beat_s


## A replace activity requested at beat 29 (seat: beat 32, block 2) that is done at `done_beat`; the player plays nothing while it is seated and everything else.
func _replace_run(done_beat: float, t_end_beats: float) -> Dictionary:
	var e := _engine()
	var c := MinigameController.new(e, null, 7)
	c.register("fake_replace", FakeMinigame, REPLACE_CFG)
	var st := {"seat_energy": -1.0}
	var ev := _drive(e, c, t_end_beats * BEAT, func(en: RunEngine, ct: MinigameController, t: float) -> void:
		if t >= 29.0 * BEAT and ct.started == 0:
			assert_true(ct.request("fake_replace", t, 32.0 * BEAT), "requested")
		if ct.state == "active" and t >= done_beat * BEAT:
			(ct.activity as FakeMinigame).finish_now = true
		if st["seat_energy"] < 0.0 and t >= 32.0 * BEAT:
			st["seat_energy"] = en.energy,
		func(tc: float) -> bool: return tc < 32.0 * BEAT or tc >= done_beat * BEAT)
	return {"e": e, "c": c, "events": ev, "seat_energy": float(st["seat_energy"])}


func test_a_replace_activity_over_seven_blocks_costs_nothing_and_judging_resumes_on_the_boundary() -> void:
	var r := _replace_run(133.0, 170.0)
	var e: RunEngine = r["e"]
	var c: MinigameController = r["c"]
	var events: Array = r["events"]
	var b1 := ContractShapes.resume_boundary(133.0 * BEAT, 128.0 * BEAT, BEAT, 16, e._decision_beat(), 4.0)
	assert_near(b1, 144.0 * BEAT, 1e-6, "done at beat 133 (phase 3 block 0): the next block, not yet charted, more than a bar on")
	var suspend: Array = c.log.filter(func(l: Dictionary) -> bool: return l["kind"] == "suspend")
	assert_eq(suspend.size(), 1, "the request suspended the rhythm")
	assert_true(int(suspend[0]["withdrawn"]) > 0, "the seat block's cues, already charted at the request, were withdrawn: %d" % int(suspend[0]["withdrawn"]))
	assert_eq(e.judge.misses, 0, "zero misses: nothing was played while seated and nothing counted")
	assert_true(e.judge.withdrawn > 0)
	var seated: Array = _of_kind(events, "block_result").filter(func(b: Dictionary) -> bool: return _block_t0(e, b) >= 32.0 * BEAT - 1e-6 and _block_t0(e, b) < b1 - 1e-6)
	assert_eq(seated.size(), 7, "blocks 2 and 3 of phase 1, phase 2, block 0 of phase 3")
	for b: Dictionary in seated:
		assert_true(bool(b.get("suspended", false)) and bool(b.get("neutral", false)), "suspended and neutral: phase %d block %d" % [b["phase"], b["block"]])
		assert_near(float(b["energy"]), float(r["seat_energy"]), 1e-9, "zero energy change: phase %d block %d" % [b["phase"], b["block"]])
		assert_eq(int(b["next_stage"]), int(b["stage"]), "no stage step")
	var empty: Array = _of_kind(events, "cues").filter(func(q: Dictionary) -> bool: return bool(q.get("suspended", false)))
	assert_eq(empty.size(), 6, "no cue charted for a seated block (the seat block's were charted before the request, then withdrawn)")
	assert_true(empty.all(func(q: Dictionary) -> bool: return int(q["count"]) == 0))
	assert_true(_of_kind(events, "judge").all(func(j: Dictionary) -> bool: return str(j["event"]["kind"]) != "miss"), "no miss event")
	assert_eq(c.log.filter(func(l: Dictionary) -> bool: return l["kind"] in ["wobble", "interrupt"]).size(), 0, "no wobble, no fall")
	assert_eq(_of_kind(events, "hotspot_commit").size(), 0, "no forced route")
	assert_true(_of_kind(events, "phase_start").all(func(p: Dictionary) -> bool: return str(p["node"]) == "warehouse"), "the run stays at its scene")
	# the boundary
	var res: Array = c.log.filter(func(l: Dictionary) -> bool: return l["kind"] == "resume")
	assert_eq(res.size(), 1)
	assert_near(float(res[0]["at"]), b1, 1e-9, "the controller resumes on ContractShapes.resume_boundary")
	assert_near(c.lead_in_s, 4.0 * BEAT, 1e-9, "a bar of lead-in")
	var fin: Array = c.log.filter(func(l: Dictionary) -> bool: return l["kind"] == "finished")
	assert_eq(fin.size(), 1)
	assert_near(float(fin[0]["t"]), b1, 1e-9, "the hold is released on the boundary")
	assert_false(e.hold)
	assert_eq(c.state, "")
	var first: Array = _of_kind(events, "block_result").filter(func(b: Dictionary) -> bool: return absf(_block_t0(e, b) - b1) < 1e-6)
	assert_eq(first.size(), 1, "the block on the boundary was decided")
	assert_false(bool(first[0].get("suspended", false)), "and judged")
	assert_true(bool(first[0]["passed"]) and float(first[0]["credit"]) > 0.99, "played and passed")
	assert_true(_of_kind(events, "cues").any(func(q: Dictionary) -> bool: return int(q["phase"]) == 3 and int(q["block"]) == 1 and int(q["count"]) > 0), "its cues were charted")
	assert_true(float(first[0]["energy"]) > float(r["seat_energy"]), "energy moves again")
	assert_eq(c.last_result["activity_id"], "fake_replace", "the result was read")
	assert_true(ContractShapes.activity_result(c.last_result).is_empty(), "and has the contract's shape: %s" % str(ContractShapes.activity_result(c.last_result)))


func test_done_after_a_decision_beat_resumes_one_block_later_and_the_strip_comes_back_a_bar_early() -> void:
	var r := _replace_run(141.0, 175.0)
	var e: RunEngine = r["e"]
	var c: MinigameController = r["c"]
	var res: Array = c.log.filter(func(l: Dictionary) -> bool: return l["kind"] == "resume")
	assert_near(float(res[0]["at"]), 160.0 * BEAT, 1e-9, "beat 141 is after block 1's chart (140.75): the block after")
	assert_eq(e.judge.misses, 0)
	var first: Array = _of_kind(r["events"], "block_result").filter(func(b: Dictionary) -> bool: return int(b["phase"]) == 3 and int(b["block"]) == 2)
	assert_false(bool(first[0].get("suspended", false)), "phase 3 block 2 judged")
	var prev: Array = _of_kind(r["events"], "block_result").filter(func(b: Dictionary) -> bool: return int(b["phase"]) == 3 and int(b["block"]) == 1)
	assert_true(bool(prev[0].get("suspended", false)), "phase 3 block 1 (charted empty before the activity was done) is still neutral")
	# owns_strip: from the seat to a bar before the boundary (checked on a fresh controller in the same state)
	var c2 := MinigameController.new(null)
	c2.register("fake_replace", FakeMinigame, REPLACE_CFG)
	c2.request("fake_replace", 0.0, 1.0)
	assert_false(c2.owns_strip(0.5), "not before the seat")
	c2.update(1.0)
	assert_true(c2.owns_strip(1.0), "seated: the controls own the strip")
	assert_eq(c2.input_mode(1.0), ActivityMode.Mode.REPLACE)
	assert_eq((c2.activity.controls() as Array).map(func(x: Dictionary) -> String: return str(x["id"])), ["same", "different"], "controls() from the config")


func test_a_rhythm_activity_is_unchanged_and_an_overlay_activity_hears_the_pads() -> void:
	# rhythm (no mode key: the blackjack table): no suspension, the failed blocks wobble and drop the player as ever
	var e := _engine()
	var c := MinigameController.new(e, null, 7)
	c.register("fake", FakeMinigame, {})
	var ev := _drive(e, c, 120.0 * BEAT, func(_en: RunEngine, ct: MinigameController, t: float) -> void:
		if t >= 29.0 * BEAT and ct.started == 0:
			ct.request("fake", t, 32.0 * BEAT),
		func(tc: float) -> bool: return tc < 32.0 * BEAT)
	assert_eq(c.mode, ActivityMode.Mode.RHYTHM)
	assert_eq(c.log.filter(func(l: Dictionary) -> bool: return l["kind"] == "suspend").size(), 0, "no suspension")
	assert_eq(e.suspended_span(), [INF, INF])
	assert_true(e.judge.misses > 0, "the cues are judged")
	assert_true(_of_kind(ev, "block_result").all(func(b: Dictionary) -> bool: return not b.has("suspended")))
	assert_true(c.log.any(func(l: Dictionary) -> bool: return l["kind"] == "interrupt" and l["reason"] == "fall"), "three failed blocks drop the player")
	# overlay: the pads play on and are judged, the activity hears them, failed blocks never wobble
	var e2 := _engine()
	var c2 := MinigameController.new(e2, null, 7)
	c2.register("stub_race", load(RACE), OVERLAY_CFG)
	var ev2 := _drive(e2, c2, 120.0 * BEAT, func(_en: RunEngine, ct: MinigameController, t: float) -> void:
		if t >= 29.0 * BEAT and ct.started == 0:
			ct.request("stub_race", t, 32.0 * BEAT),
		func(tc: float) -> bool: return tc < 64.0 * BEAT)
	var race: MinigameActivity = c2.activity
	assert_eq(c2.mode, ActivityMode.Mode.OVERLAY)
	assert_eq(c2.state, "active", "still racing")
	assert_eq(e2.suspended_span(), [INF, INF], "no suspension")
	assert_true((race.get("judged") as Array).size() > 10, "judge events reach the activity")
	assert_true((race.get("judged") as Array).all(func(j: Dictionary) -> bool: return float(j["t"]) >= 32.0 * BEAT), "only once seated")
	var seated: Array = _of_kind(ev2, "block_result").filter(func(b: Dictionary) -> bool: return float(b["t"]) >= 32.0 * BEAT)
	assert_eq((race.get("blocks") as Array).size(), seated.size(), "every block result once seated")
	assert_true(seated.any(func(b: Dictionary) -> bool: return not bool(b["passed"])), "some failed")
	assert_eq((race.get("wobbles") as Array).size(), 0, "never a wobble")
	assert_eq(c2.log.filter(func(l: Dictionary) -> bool: return l["kind"] == "interrupt").size(), 0, "never a fall")
	assert_true(float(seated[-1]["energy"]) < float(seated[0]["energy"]), "energy still moves (penalties active)")
	race.set("finish_now", true)
	c2.update(121.0 * BEAT)
	assert_eq(c2.state, "", "an overlay activity finishes at once, as a rhythm one does")
	assert_true(ContractShapes.activity_result(c2.last_result).is_empty(), "race result shape: %s" % str(ContractShapes.activity_result(c2.last_result)))


# --- the run scene ------------------------------------------------------------------------------------------------------------

func _scene(bot: String) -> Dictionary:
	_saved = Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", bot)
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.set_environment("RW_RUN_TAPS", "none")
	OS.set_environment("RW_MINIGAME_TAPS", "")
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
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_TAPS", "RW_MINIGAME_TAPS"]:
		OS.set_environment(k, "")


func _run_to(scene: Node, t_end: float) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func _arm(scene: Node, id: String, script: Variant, cfg: Dictionary) -> void:
	scene.minigames.register(id, script, cfg)
	for h in scene.data.hotspots["warehouse"]:
		if h["id"] == "warehouse.dancer":
			h["on_success"] = {"activity": id}


func test_in_the_scene_a_replace_activity_owns_the_strip_and_the_run_resumes_on_the_boundary() -> void:
	# the bot plays phase 1, nothing in phase 2 and block 0 of phase 3 (the activity owns the strip there), then everything again
	var d := _scene("blocks:1111" + "00000" + "111111111111")
	var scene: Node = d["scene"]
	_arm(scene, "fake_replace", FakeMinigame, REPLACE_CFG)
	_run_to(scene, 49.5 * BEAT)
	assert_true(scene.hotspot_select("warehouse.dancer"))
	# before the seat the strip is the pads'
	var pad1: Rect2 = scene.pad_view.button_rects()[1]
	var pad4: Rect2 = scene.pad_view.button_rects()[4]
	assert_eq(scene.dispatch_tap(pad1.get_center()), "pads", "no activity: a strip tap is the pads'")
	var host: Control = scene._stage_host
	var stage_pt := host.global_position + host.size * 0.5
	assert_eq(scene.dispatch_tap(stage_pt), "hotspots", "no activity: a stage tap is the world's")
	scene.hotspot_select("warehouse.dancer")  # (that tap may have selected something else)
	assert_eq(scene.hotspots.selected, "warehouse.dancer")
	_run_to(scene, 64.5 * BEAT)
	var mg: MinigameController = scene.minigames
	assert_eq(mg.state, "active", "seated on the downbeat")
	assert_eq(mg.mode, ActivityMode.Mode.REPLACE)
	var fake := mg.activity as FakeMinigame
	fake.taken = ["same", "different", "exit"]
	var e: RunEngine = scene.engine
	var misses0: int = e.judge.misses
	var energy0: float = e.energy
	var moves0: int = (scene.journey_log as Array).size()
	# the controls stand in the strip
	assert_true(scene._mg.owns_strip(), "the controls own the strip")
	assert_false(scene.pad_view.visible, "the pads are hidden")
	assert_false(scene.note_lane.visible, "the note lane is hidden")
	assert_false(scene.lane_input.enabled, "the lane input is off")
	var layer: RunActivityInput = scene._mg.controls_layer
	assert_true(layer != null and layer.ids == ["same", "different"], "two controls")
	assert_true(layer.get_parent() == scene and layer.get_index() < scene.hud.get_index(), "over the strip, under the HUD")
	# a strip tap reaches the controls, never a pad
	var strays0: int = e.judge.strays
	assert_eq(scene.dispatch_tap(pad1.get_center()), "activity_controls")
	assert_eq(scene.dispatch_tap(pad4.get_center()), "activity_controls")
	var taps: Array = fake.calls.filter(func(x: Dictionary) -> bool: return x["call"] == "tap").map(func(x: Dictionary) -> String: return str(x["target"]))
	assert_eq(taps, ["same", "different"], "the left pair is 'same', the right pair 'different'")
	scene._on_button_pressed(1, 0)  # (a pad press that got through anyway: refused)
	assert_eq(e.judge.strays, strays0, "no pad was pressed")
	assert_true((scene.input_log as Array).any(func(x: Dictionary) -> bool: return int(x.get("refused_pad", 0)) == 1), "the refusal is logged")
	# a stage tap is the activity view's, never a world choice
	var sel0: String = scene.hotspots.selected
	assert_eq(scene.dispatch_tap(stage_pt), "activity_view")
	assert_eq(scene.hotspots.selected, sel0, "no world choice")
	# the activity is done at beat 133: judging resumes on beat 144, the strip comes back at 140
	_run_to(scene, 133.0 * BEAT)
	fake.finish_now = true
	_run_to(scene, 134.0 * BEAT)
	assert_eq(mg.state, "resuming")
	assert_near(mg.resume_t, 144.0 * BEAT, 1e-6)
	assert_true(scene._mg.owns_strip(), "the controls stay until the lead-in")
	assert_true(scene.engine.hold)
	_run_to(scene, 140.2 * BEAT)
	assert_false(scene._mg.owns_strip(), "a bar before the boundary the pads are back")
	assert_true(scene.pad_view.visible and scene.note_lane.visible and scene.lane_input.enabled, "pads, notes and lane input restored")
	assert_eq(scene.dispatch_tap(pad1.get_center()), "pads")
	assert_true(mg.active() and scene.engine.hold, "still held until the boundary")
	var seated_moves: Array = (scene.journey_log as Array).slice(moves0).filter(func(a: Dictionary) -> bool: return str(a["action"]) in ["player_move", "player_walk"])
	assert_eq(seated_moves.size(), 0, "no rail step while the activity owned the scene")
	assert_eq(e.judge.misses, misses0, "zero misses while seated (the bot played nothing)")
	assert_near(e.energy, energy0, 1e-9, "zero energy loss")
	_run_to(scene, 160.0 * BEAT)
	assert_eq(mg.state, "")
	assert_false(scene.engine.hold)
	var fin: Dictionary = mg.log.filter(func(l: Dictionary) -> bool: return l["kind"] == "finished")[0]
	assert_near(float(fin["t"]), 144.0 * BEAT, 1e-6, "released on the boundary")
	var blocks: Array = (scene.event_log as Array).filter(func(x: Dictionary) -> bool: return x["kind"] == "block_result" and int(x["phase"]) == 3 and int(x["block"]) == 1)
	assert_eq(blocks.size(), 1)
	assert_false(bool(blocks[0].get("suspended", false)), "the first block after the boundary is judged")
	assert_true(bool(blocks[0]["passed"]), "and the bot passed it")
	var back: Array = (scene.journey_log as Array).slice(moves0).filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_move")
	assert_true(back.size() >= 1 and absf(float(back[0]["t0"]) - 144.0 * BEAT) < 0.05, "back to the rail on the boundary: %s" % str(back.slice(0, 1)))
	_free(d)


func test_in_the_scene_an_overlay_activity_gets_the_four_regions_and_the_pads_stay() -> void:
	var d := _scene("perfect")
	var scene: Node = d["scene"]
	_arm(scene, "stub_race", load(RACE), OVERLAY_CFG)
	_run_to(scene, 49.5 * BEAT)
	assert_true(scene.hotspot_select("warehouse.dancer"))
	_run_to(scene, 66.0 * BEAT)
	var mg: MinigameController = scene.minigames
	assert_eq(mg.state, "active")
	var race: MinigameActivity = mg.activity
	assert_true(scene._mg.regions_layer != null, "the regions layer is up")
	assert_false(scene._mg.owns_strip())
	assert_true(scene.pad_view.visible and scene.lane_input.enabled, "the pads stay")
	var host: Control = scene._stage_host
	assert_eq(scene.dispatch_tap(host.global_position + Vector2(host.size.x * 0.05, host.size.y * 0.5)), "world_regions")
	assert_eq(scene.dispatch_tap(host.global_position + Vector2(host.size.x * 0.5, host.size.y * 0.1)), "world_regions")
	var pad1: Rect2 = scene.pad_view.button_rects()[1]
	assert_eq(scene.dispatch_tap(pad1.get_center()), "pads", "the strip is the pads'")
	assert_eq((race.get("taps") as Array).map(func(x: Dictionary) -> String: return str(x["target"])), ["region:left", "region:top"])
	_run_to(scene, 100.0 * BEAT)
	assert_true((race.get("judged") as Array).size() > 5, "the bot's judge events reach the race through RunPlay")
	assert_true((race.get("blocks") as Array).size() >= 2, "and the block results")
	race.set("finish_now", true)
	_run_to(scene, 101.0 * BEAT)
	assert_eq(mg.state, "")
	assert_true(scene._mg.regions_layer == null, "the regions go with it")
	_free(d)



# --- the request from data (H4.3) and the result (H4.1) ------------------------------------------------------------------------

func test_the_request_is_built_from_the_activity_and_theme_data() -> void:
	var theme: Dictionary = ContractShapes.load_fixture("theme_space.json")
	var cloak: Dictionary = ContractShapes.load_fixture("activity_cloakroom.json")
	var req := RunMinigameHost.build_request("cloakroom", cloak, "space", theme, "rave.space", "space_floor")
	assert_true(ContractShapes.activity_request(req).is_empty(), "the contract's shape: %s" % str(ContractShapes.activity_request(req)))
	assert_eq(req["mode"], "replace")
	assert_eq(req["return_pose"], "cloak_view", "back to the station's choice viewpoint")
	assert_eq(req["config"]["cloakroom_symbols"], theme["cloakroom_symbols"], "the theme's keys merged into the config")
	assert_eq(req["config"]["customers"], theme["customers"])
	assert_eq(req["config"]["flags_on_complete"], ["rave.space.cloakroom_done"], "{theme} filled in")
	assert_eq(cloak["flags_on_complete"], ["rave.{theme}.cloakroom_done"], "the registered config is not changed")
	var race := RunMinigameHost.build_request("race", ContractShapes.load_fixture("activity_race.json"), "space", theme, "rave.space", "space_floor")
	assert_eq(req["scene_id"], "rave.space")
	assert_eq(race["return_pose"], "race_door", "the race comes back to its entrance")
	assert_eq(race["mode"], "overlay")
	assert_eq(RunMinigameHost.build_request("blackjack", {"id": "blackjack"}, "", {}, "warehouse", "wh_floor"), {}, "outside a rave: no request, the registered config as ever")
	# the controller seats the activity with the request's config
	var c := MinigameController.new(null)
	c.register("fake_replace", FakeMinigame, REPLACE_CFG)
	var r2 := {"activity_id": "fake_replace", "mode": "replace", "theme": "space", "scene_id": "rave.space", "return_pose": "x", "config": REPLACE_CFG.merged({"coats": 3})}
	assert_true(c.request("fake_replace", 0.0, 1.0, [], r2))
	assert_eq(int(c.activity.config["coats"]), 3, "the merged config reaches the activity")
	assert_eq((c.activity as FakeMinigame).ctx_seen["request"], r2, "and the request itself")
	assert_eq(c.request_info, r2)


func test_the_default_result_and_the_save_it_reaches() -> void:
	var a := MinigameActivity.new()
	a.setup({"config": {"id": "bass_knob"}})
	assert_eq(a.controls(), [], "no controls by default (the pads stay)")
	a.interrupt("host", 0.0)
	var r := a.result()
	assert_true(ContractShapes.activity_result(r).is_empty(), str(ContractShapes.activity_result(r)))
	assert_eq(r["activity_id"], "bass_knob")
	assert_false(bool(r["completed"]))
	assert_eq(r["reason"], "host")
	# the host applies the flags and the race to the save
	var saved: RunProgress = Session.run_progress
	var path := "user://test_activity_modes_result.json"
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)
	Session.run_progress = RunProgress.load_data(path, "user://none.json")
	var host := RunMinigameHost.new(Control.new())
	host.apply_result({"activity_id": "race", "completed": true, "score": 1, "flags_to_set": ["rave.space.bass_fixed", "met_the_dj"], "reason": "done",
		"race": {"won": true, "position": 1, "time_s": 72.5}}, "space")
	var q := RunProgress.load_data(path, "user://none.json")
	assert_true(q.puzzle_done("space", "bass_fixed"), "the puzzle flag is saved")
	assert_true(Session.run_progress.has_flag("met_the_dj"), "an ordinary flag is a run flag")
	assert_eq(int(q.data["raves"]["space"]["race"]["wins"]), 1, "the race is recorded")
	Session.run_progress = saved
	DirAccess.remove_absolute(path)
