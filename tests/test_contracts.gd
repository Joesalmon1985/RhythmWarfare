extends TestCase
## The shared contracts of the bedsit-raves and Doom-worlds streams (docs/parallel-development/CONTRACTS.md): every fixture in src/contracts/fixtures/
## fits its shape, the pure functions both streams must agree on give the documented answers, and the stem lock (the one engine hook built with the
## contracts) keeps a locked stem silent whatever the mix says and brings it back without a restart.


func _fx(name: String) -> Dictionary:
	var d: Variant = ContractShapes.load_fixture(name)
	assert_true(typeof(d) == TYPE_DICTIONARY, "fixture %s loads as a dictionary" % name)
	return d if typeof(d) == TYPE_DICTIONARY else {}


func _ok(errors: Array, what: String) -> void:
	assert_eq(errors, [], what)


# --- 1. scene entry and exit

func test_scene_entry_and_exit_shapes() -> void:
	var d := _fx("scene_entry.json")
	assert_eq((d["entries"] as Array).size(), 4)
	for en in d["entries"]:
		_ok(ContractShapes.scene_entry(en), "entry %s" % en["scene_id"])
	for ex in d["exits"]:
		_ok(ContractShapes.scene_exit(ex), "exit %s" % ex["route"])
	assert_false(ContractShapes.scene_entry({"scene_id": "x", "theme": "jungle", "arrival_pose": "a", "entered_from": {}, "transition": "world"}).is_empty(), "an unknown theme is refused")
	assert_false(ContractShapes.scene_entry({"scene_id": "x", "theme": "", "arrival_pose": {"at": [1]}, "entered_from": {}, "transition": "world"}).is_empty(), "a bad pose is refused")
	assert_false(ContractShapes.scene_exit({"route": "home", "transition": "teleport", "threshold": "d"}).is_empty(), "transition is world or passage")


# --- 2. theme selection

func test_bedsit_themes_fixed_mapping() -> void:
	var d := _fx("bedsit_themes.json")
	_ok(ContractShapes.bedsit_themes(d), "bedsit themes")
	_ok(ContractShapes.regions(d["regions"]), "bedsit regions")
	for f in ContractShapes.FIXED_FACINGS:
		assert_eq(RaveSave.theme_of(f, d), ContractShapes.FIXED_FACINGS[f], "facing %s" % f)
	var bad := d.duplicate(true)
	bad["facings"]["N"] = "magic"
	bad["facings"]["S"] = "space"
	assert_false(ContractShapes.bedsit_themes(bad).is_empty(), "the mapping is fixed by the brief")


func test_turning_wraps_and_bottom_stays() -> void:
	for start in RaveSave.FACINGS:
		var f: String = start
		for i in 4:
			f = RaveSave.turn(f, 1)
		assert_eq(f, start, "four right turns return to %s" % start)
		for i in 4:
			f = RaveSave.turn(f, -1)
		assert_eq(f, start, "four left turns return to %s" % start)
		assert_eq(RaveSave.turn(start, 0), start, "bottom keeps the facing")
	assert_eq(RaveSave.turn("N", -1), "W")
	assert_eq(RaveSave.turn("W", 1), "N")
	assert_eq(RaveSave.turn("N", 1), "E")


func test_theme_data_shape() -> void:
	var d := _fx("theme_space.json")
	_ok(ContractShapes.theme_data(d), "space theme data")
	var bad := d.duplicate(true)
	(bad["ingredients"] as Array).pop_back()
	assert_false(ContractShapes.theme_data(bad).is_empty(), "exactly four ingredients")
	var bad2 := d.duplicate(true)
	bad2["cloakroom_symbols"][1]["icon"] = bad2["cloakroom_symbols"][0]["icon"]
	assert_false(ContractShapes.theme_data(bad2).is_empty(), "four visually distinct symbols")
	var bad3 := d.duplicate(true)
	bad3["props"] = (bad3["props"] as Array).filter(func(p: Dictionary) -> bool: return str(p["role"]) != "race_entrance")
	assert_false(ContractShapes.theme_data(bad3).is_empty(), "every rave has a race entrance")


# --- 3. rail destinations and arrival poses

func test_route_shape_and_rail_actions() -> void:
	var r := _fx("route_space_to_stage.json")
	_ok(ContractShapes.route(r), "route")
	var bar_s := 4.0 * 60.0 / 174.0
	var acts := ContractShapes.route_actions(r, 10.0, bar_s)
	assert_eq(acts.size(), 3)
	for a in acts:
		assert_eq(a["action"], "player_move")
	assert_near(float(acts[0]["t0"]), 10.0, 1e-9)
	assert_near(float(acts[1]["t0"]), 10.0 + 3.0 * bar_s, 1e-9, "move 2 bars, hold 1, then the next leg")
	assert_near(float(acts[2]["t0"]), 10.0 + 6.0 * bar_s, 1e-9)
	assert_eq(acts[2]["args"]["to"], "stage_deck_view")
	var cin := ContractShapes.route_as_cinematic(r)
	assert_eq((cin["steps"] as Array).size(), 3)
	assert_eq(cin["steps"][1]["look_at"], "deck")
	for k in (cin["steps"][0] as Dictionary):
		assert_true(str(k) in HotspotContract.CINEMATIC_KEYS, "cinematic key %s is one HotspotContract knows" % k)


func test_route_holds_at_choice_viewpoint() -> void:
	var r := _fx("route_space_to_stage.json")
	var short := r.duplicate(true)
	short["legs"][-1]["hold_bars"] = 2
	assert_false(ContractShapes.route(short).is_empty(), "a choice viewpoint holds at least a block")
	var drift := r.duplicate(true)
	drift["legs"][0].erase("hold_bars")
	assert_false(ContractShapes.route(drift).is_empty(), "every leg says how long it holds")
	var quick := r.duplicate(true)
	quick["legs"][0]["bars"] = 1
	assert_false(ContractShapes.route(quick).is_empty(), "legs are 2 to 4 bars (RunRail.pick_bars)")
	var nowindow := r.duplicate(true)
	nowindow["arrive"].erase("hold")
	assert_false(ContractShapes.route(nowindow).is_empty(), "the hold covers the window")


# --- 4. activity entry, results and exit

func test_activity_configs() -> void:
	for f in ["activity_cloakroom.json", "activity_bar.json", "activity_race.json", "activity_bass.json"]:
		_ok(ContractShapes.activity_config(_fx(f)), f)
	assert_eq(ActivityMode.of_config(_fx("activity_cloakroom.json")), ActivityMode.Mode.REPLACE)
	assert_eq(ActivityMode.of_config(_fx("activity_bar.json")), ActivityMode.Mode.REPLACE)
	assert_eq(ActivityMode.of_config(_fx("activity_race.json")), ActivityMode.Mode.OVERLAY)
	var bj: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/blackjack.json"))
	assert_eq(ActivityMode.of_config(bj), ActivityMode.Mode.RHYTHM, "the blackjack table names no mode: rhythm, as today")
	var bad := _fx("activity_cloakroom.json")
	bad["controls"] = 3
	assert_false(ContractShapes.activity_config(bad).is_empty(), "2 or 4 controls in the pad strip")
	var bad2 := _fx("activity_cloakroom.json")
	bad2["fall_at"] = 3
	assert_false(ContractShapes.activity_config(bad2).is_empty(), "no fall outside rhythm mode")


func test_activity_requests_and_results() -> void:
	var d := _fx("activity_request_result.json")
	for q in d["requests"]:
		_ok(ContractShapes.activity_request(q), "request %s" % q["activity_id"])
	for r in d["results"]:
		_ok(ContractShapes.activity_result(r), "result %s" % r["activity_id"])
	assert_false(ContractShapes.activity_result({"activity_id": "bar", "completed": "yes", "score": 1, "flags_to_set": [], "reason": "done"}).is_empty())


func test_mode_rules_match_the_brief() -> void:
	var rh := ActivityMode.rules(ActivityMode.Mode.RHYTHM)
	var rp := ActivityMode.rules(ActivityMode.Mode.REPLACE)
	var ov := ActivityMode.rules(ActivityMode.Mode.OVERLAY)
	assert_eq(rp["pads"], "replaced")
	assert_false(rp["judging"], "replace: no note judging")
	assert_false(rp["energy"], "replace: no energy loss")
	assert_false(rp["wobble_fall"], "replace: no wobble or fall")
	assert_eq(rp["resume"], "boundary")
	assert_eq(ov["pads"], "active")
	assert_true(ov["judging"] and ov["energy"] and ov["rhythm_to_activity"], "racing: pads judged, penalties active, rhythm feeds the speed")
	assert_false(ov["wobble_fall"], "racing: a run of misses slows, it does not throw the player out")
	assert_eq(rh["wobble_fall"], true, "rhythm mode is today's blackjack rule")
	for r in [rh, rp, ov]:
		assert_eq(r["rail"], "held")
		assert_eq(r["route"], "held")
	assert_eq(ActivityMode.parse("nonsense"), -1)


func test_resume_boundary() -> void:
	var bs := 60.0 / 174.0
	assert_near(ContractShapes.resume_boundary(5.0 * bs, 0.0, bs), 16.0 * bs, 1e-9, "done early in a block: the next block, not yet charted")
	assert_near(ContractShapes.resume_boundary(12.5 * bs, 0.0, bs), 32.0 * bs, 1e-9, "under a bar of lead-in: one more block")
	assert_near(ContractShapes.resume_boundary(13.0 * bs, 0.0, bs), 32.0 * bs, 1e-9, "after the decision beat the next block is already charted (empty)")
	assert_near(ContractShapes.resume_boundary(60.0 * bs, 0.0, bs), 64.0 * bs, 1e-9, "the next phase's first block, exactly a bar ahead")
	assert_near(ContractShapes.resume_boundary(61.0 * bs, 0.0, bs), 80.0 * bs, 1e-9, "across a phase boundary")
	for i in 64:
		var td := float(i) * 0.97 * bs
		var b := ContractShapes.resume_boundary(td, 0.0, bs)
		assert_true(b - td >= 4.0 * bs - 1e-9, "at least a bar of lead-in")
		assert_true(b - td <= 36.0 * bs, "never more than two blocks and a bar")


# --- 5. input ownership

func test_one_owner_per_tap() -> void:
	var d := _fx("input_ownership.json")
	_ok(ContractShapes.regions(d["regions"]), "regions")
	for row in d["rows"]:
		var mode := ActivityMode.parse(row["mode"]) if str(row["mode"]) != "" else -1
		var strip := ContractShapes.tap_owner("strip", mode, bool(row["regions_on"]))
		assert_eq(strip, "activity_controls" if row["pads"] == "replaced" else "pads", "%s: the pad strip" % row["situation"])
		assert_eq(ContractShapes.tap_owner("stage", mode, bool(row["regions_on"])), row["stage"], "%s: the stage" % row["situation"])
		assert_eq(ContractShapes.tap_owner("hud", mode, bool(row["regions_on"])), "hud")
		if mode >= 0:
			assert_eq(ActivityMode.rules(mode)["strip_input"], strip, "%s: the rules agree" % row["situation"])
	assert_eq(ContractShapes.tap_owner("strip", -1, false, true), "trial", "the Bassment owns its touches")
	assert_eq(ContractShapes.region_at(d["regions"], Vector2(0.5, 0.1)), "top")
	assert_eq(ContractShapes.region_at(d["regions"], Vector2(0.5, 0.9)), "bottom")
	assert_eq(ContractShapes.region_at(d["regions"], Vector2(0.05, 0.5)), "left")
	assert_eq(ContractShapes.region_at(d["regions"], Vector2(0.95, 0.5)), "right")
	assert_eq(ContractShapes.region_at(d["regions"], Vector2(0.5, 0.55)), "", "the middle is no one's")
	var overl: Dictionary = d["regions"].duplicate(true)
	overl["top"] = [0.0, 0.0, 1.0, 0.5]
	assert_false(ContractShapes.regions(overl).is_empty(), "regions never overlap")


# --- 6. puzzle progression

func test_save_v3_fixture_and_migration() -> void:
	_ok(ContractShapes.save_v3(_fx("save_v3.json")), "save v3")
	var v2 := _fx("save_v2.json")
	assert_false(ContractShapes.save_v3(v2).is_empty(), "a v2 save is not v3")
	var fixed := RaveSave.migrate(v2)
	assert_true(fixed.has("raves") and fixed.has("bedsit_facing"))
	_ok(ContractShapes.save_v3(v2), "migrated v2")
	assert_eq(v2["bedsit_facing"], "N")
	assert_eq(v2["rave_theme"], "")
	assert_eq(int(v2["wallet"]["pence"]), 2000, "v2 keys are kept")
	assert_eq(v2["paths"]["gospel"]["reached"], ["galilee"])
	assert_eq(RaveSave.migrate(v2), [], "migrating twice changes nothing")


func test_new_run_and_progress() -> void:
	var d := _fx("save_v3.json")
	assert_true(RaveSave.puzzle_done(d, "space", "bass_fixed"))
	RaveSave.new_run(d)
	assert_eq(d["bedsit_facing"], "N", "a new run faces north")
	assert_eq(d["rave_theme"], "")
	for t in RaveSave.THEMES:
		for p in RaveSave.PUZZLES:
			assert_false(RaveSave.puzzle_done(d, t, p), "%s.%s cleared by a new run" % [t, p])
	assert_eq(int(d["raves"]["space"]["race"]["wins"]), 2, "race records outlive the run")
	assert_true(RaveSave.apply_flag(d, "rave.space.cloakroom_done"))
	assert_false(RaveSave.apply_flag(d, "rave.space.cloakroom_done"), "set once")
	assert_false(RaveSave.apply_flag(d, "wh_drink"), "not a rave flag")
	assert_false(RaveSave.apply_flag(d, "rave.jungle.bar_done"))
	assert_true(RaveSave.puzzle_done(d, "space", "cloakroom_done"))
	assert_false(RaveSave.puzzle_done(d, "magic", "cloakroom_done"), "per theme")
	RaveSave.record_race(d, "magic", true, 80.0)
	RaveSave.record_race(d, "magic", false, 70.0)
	RaveSave.record_race(d, "magic", false, 0.0)
	assert_eq(d["raves"]["magic"]["race"], {"wins": 1, "runs": 3, "best": 70.0})
	_ok(ContractShapes.save_v3(d), "still a v3 save")


# --- 7. bass unlocking

func test_bass_lock_fixture_and_unlock_time() -> void:
	var d := _fx("bass_lock.json")
	_ok(ContractShapes.bass_lock(d), "bass lock")
	var bs := 60.0 / 174.0
	assert_near(ContractShapes.unlock_time(5.0 * bs, 0.0, bs), 8.0 * bs, 1e-9, "the next bar line")
	assert_near(ContractShapes.unlock_time(7.9 * bs, 0.0, bs), 12.0 * bs, 1e-9, "too close to the bar line: the one after")
	assert_near(ContractShapes.unlock_time(5.0 * bs, 0.0, bs, "block"), 16.0 * bs, 1e-9)


func test_stem_lock_holds_against_the_mix_and_unlocks_without_restart() -> void:
	var pack := TrackTestKit.fixture_pack()
	var t := TrackTransport.new()
	tree.root.add_child(t)
	t.set_stem_locked("bass", true)  # before the load, as the rave's track group does
	assert_eq(t.load_pack_streams(pack), "")
	assert_true(t.is_stem_locked("bass"))
	assert_eq(t.stem_target("bass"), 0.0, "locked: silent from the first sample")
	assert_eq(t.stem_gain("bass"), 0.0)
	assert_eq(t.stem_target("drums"), 1.0, "other stems untouched")
	t.apply_program({"bass": true}, true)
	t.set_stem_muted("bass", false)
	assert_eq(t.stem_target("bass"), 0.0, "neither the gain program nor a restore lifts the lock")
	assert_eq(t.stem_gain("bass"), 0.0)
	t.start()
	for i in 6:
		await tree.process_frame
	var before := t.playback_position()
	t.set_stem_locked("bass", false, 0.15)
	assert_false(t.is_stem_locked("bass"))
	assert_eq(t.stem_target("bass"), 1.0, "unlocked: the mix may use it")
	await tree.process_frame
	await tree.process_frame
	var mid := t.stem_gain("bass")
	assert_true(mid < 1.0, "it ramps in (%f), it does not jump" % mid)
	await tree.create_timer(0.4).timeout
	assert_near(t.stem_gain("bass"), 1.0, 1e-6, "fully in after the ramp")
	assert_true(t.is_playing(), "the stream was never stopped")
	assert_true(t.playback_position() >= before, "the playhead went on: no restart")
	t.set_stem_muted("bass", true)
	assert_eq(t.stem_target("bass"), 0.0, "once unlocked the ordinary mute rules apply")
	t.set_stem_locked("bass", true)
	t.set_stem_muted("bass", false)
	assert_eq(t.stem_target("bass"), 0.0, "locked again: silent")
	t.queue_free()


# --- 8. race environment

func test_race_course_shape_and_points() -> void:
	var d := _fx("race_course.json")
	_ok(ContractShapes.race_course(d), "race course")
	var p0 := ContractShapes.course_point(d, 0.0, 0.0)
	assert_true((p0["at"] as Vector2).is_equal_approx(Vector2(-1.8, 0.0)), "lane 0 is left of the centreline (facing -z)")
	assert_near(float(p0["yaw"]), 0.0, 1e-6, "yaw 0 looks along -z")
	var p1 := ContractShapes.course_point(d, 1.0, 100.0)
	assert_true((p1["at"] as Vector2).is_equal_approx(Vector2(1.8, -100.0)))
	var mid := ContractShapes.course_point(d, 0.5, 300.0)
	assert_true((mid["at"] as Vector2).is_equal_approx(Vector2(0.0, -300.0)), "a lane change passes the centre")
	var bend := ContractShapes.course_point(d, 0.5, 600.0 + 10.0)
	assert_true(float(bend["yaw"]) < 0.0, "the gentle right bend turns the yaw (%f)" % float(bend["yaw"]))
	var bad := d.duplicate(true)
	bad["camera"]["max_roll_deg"] = 10.0
	assert_false(ContractShapes.race_course(bad).is_empty(), "no roll that makes the pads hard to read")
	assert_false(ContractShapes.vehicle({"id": "x", "kind": "plane", "sprite": "s", "lane": 0, "distance_m": 1, "brake": false}).is_empty())


# --- 9. choice states

func test_choice_states_shape_and_sequence() -> void:
	var d := _fx("choice_states.json")
	for th in d["things"]:
		_ok(ContractShapes.choice_thing(th), "choice thing %s" % th["thing"])
	var ring := (d["things"][0] as Dictionary).duplicate(true)
	ring["states"]["selected"]["frames"] = ["ui/green_ring"]
	assert_false(ContractShapes.choice_thing(ring).is_empty(), "no drawn ring")
	var same := (d["things"][0] as Dictionary).duplicate(true)
	same["states"]["selected"] = same["states"]["available"].duplicate(true)
	assert_false(ContractShapes.choice_thing(same).is_empty(), "selected must look different from available")
	var gone := (d["things"][0] as Dictionary).duplicate(true)
	(gone["states"] as Dictionary).erase("cost")
	assert_false(ContractShapes.choice_thing(gone).is_empty(), "every state is drawn")
	assert_eq(ContractShapes.choice_state("a", false, "", ""), "idle")
	assert_eq(ContractShapes.choice_state("a", true, "", ""), "available")
	assert_eq(ContractShapes.choice_state("a", true, "a", ""), "selected")
	assert_eq(ContractShapes.choice_state("b", true, "a", ""), "available", "another selection leaves the rest available")
	assert_eq(ContractShapes.choice_state("a", true, "a", "", true, true), "selected", "selected through the lock")
	assert_eq(ContractShapes.choice_state("b", true, "a", "", true, true), "declined", "after the lock the others step back")
	assert_eq(ContractShapes.choice_state("a", true, "a", "a", true), "committed")
	assert_eq(ContractShapes.choice_state("a", true, "a", "a", false), "cost", "a wrong one shows its cost")
	assert_eq(ContractShapes.choice_state("b", true, "a", "a"), "declined")
