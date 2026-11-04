extends TestCase
## Story Campaign logic with no scenes: chapter data, the crowd energy model, the director's determinism and timing, the three
## endings under perfect / no / mixed input, sequence fidelity against the original mission run, and the save isolation.


func _load_data() -> StoryData:
	var loaded := StoryData.load_file()
	assert_eq(loaded["errors"], [], "night_one.json validates")
	return loaded["data"]


func test_chapter_data_is_complete() -> void:
	var d := _load_data()
	if d == null:
		return
	assert_eq(d.blocks.size(), 16, "sixteen eight-bar blocks")
	assert_eq(d.duration_bars, 128)
	assert_true(d.decisions.size() >= 3, "at least three intermediate decisions")
	assert_eq(d.ending_order.size(), 3, "three endings")
	var archetypes := {}
	for a in d.actors:
		archetypes[a["archetype"]] = true
	assert_eq(archetypes.size(), 6, "six archetypes in the roster")
	assert_true(d.actors.size() + d.silhouettes.size() >= 24 and d.actors.size() + d.silhouettes.size() <= 64, "a crowd of 24 to 64")
	for k in 16:
		assert_eq(int(d.blocks[k]["start_bar"]), 1 + 8 * k)
		var b: Dictionary = d.blocks[k]
		var has := not (b["events"] as Array).is_empty()
		for dec in d.decisions:
			if dec["block"] == b["id"]:
				has = true
		assert_true(has, "block %s has an authored action" % b["id"])


func test_validation_rejects_unknown_references() -> void:
	var d := _load_data()
	var errors: Array = []
	d.blocks[0]["events"].append({"at_bar": 4, "action": "no_such_action"})
	d.blocks[1]["events"].append({"at_bar": 129, "action": "led_eq"})
	d.blocks[2]["events"].append({"at_bar": 20, "action": "bring_in", "group": "ghosts"})
	d.validate(errors)
	assert_true(errors.size() >= 3, "unknown action, action past the song and unknown group are all reported: %s" % str(errors))


func test_energy_model_and_bands() -> void:
	var d := _load_data()
	var c := CrowdController.new()
	c.setup(d)
	assert_eq(c.energy, 45.0)
	assert_eq(c.band(), "dancing")
	c.apply({"index": 0, "passed": true, "grade": "sharp", "resolve_time": 1.0})
	assert_eq(c.energy, 49.0, "sharp +4")
	c.apply({"index": 1, "passed": true, "grade": "steady", "resolve_time": 2.0})
	assert_eq(c.energy, 52.0, "steady +3")
	c.apply({"index": 2, "passed": true, "grade": "loose", "resolve_time": 3.0})
	assert_eq(c.energy, 54.0, "loose +2")
	c.apply({"index": 3, "passed": false, "grade": "", "resolve_time": 4.0})
	assert_eq(c.energy, 49.0, "failure -5")
	assert_eq(c.apply({"index": 3, "passed": false, "grade": "", "resolve_time": 4.0}), 0.0, "a sequence counts exactly once")
	assert_eq(c.energy, 49.0)
	for i in 30:
		c.apply({"index": 10 + i, "passed": true, "grade": "sharp", "resolve_time": 5.0 + i})
	assert_eq(c.energy, 100.0, "clamped at 100")
	assert_eq(c.band(), "euphoric")
	for i in 30:
		c.apply({"index": 100 + i, "passed": false, "grade": "", "resolve_time": 50.0 + i})
	assert_eq(c.energy, 0.0, "clamped at 0")
	assert_eq(c.band(), "quiet")
	assert_eq(d.band_of(29.0), "quiet")
	assert_eq(d.band_of(30.0), "dancing")
	assert_eq(d.band_of(64.0), "dancing")
	assert_eq(d.band_of(65.0), "hype")
	assert_eq(d.band_of(85.0), "euphoric")


func test_decision_dead_band_keeps_the_previous_branch() -> void:
	var d := _load_data()
	var c := CrowdController.new()
	c.setup(d)
	var rule := {"id": "x", "rule": {"energy_min": 55, "recent_sequences": 4, "recent_pass_min": 0.5, "smooth": 4, "dead_band": 4}}
	# four sequences averaging 56: inside the dead band, first decision defaults to good
	for i in 4:
		c.history.append({"index": i, "passed": true, "grade": "steady", "energy": 56.0, "delta": 0.0, "resolve_time": float(i)})
	assert_eq(c.decide(rule, 4)["outcome"], "good", "no earlier branch: the dead band reads good")
	c.decisions_log.append({"id": "prev", "outcome": "bad", "kind": ""})
	assert_eq(c.decide(rule, 4)["outcome"], "bad", "inside the dead band the previous bad outcome stands")
	c.history.clear()
	for i in 4:
		c.history.append({"index": i, "passed": true, "grade": "sharp", "energy": 70.0, "delta": 0.0, "resolve_time": float(i)})
	assert_eq(c.decide(rule, 4)["outcome"], "good", "well above the band is good")
	c.history.clear()
	for i in 4:
		c.history.append({"index": i, "passed": i == 0, "grade": "sharp", "energy": 70.0, "delta": 0.0, "resolve_time": float(i)})
	assert_eq(c.decide(rule, 4)["outcome"], "bad", "a poor recent pass rate is bad even with high energy")


func test_perfect_play_reaches_the_legendary_set() -> void:
	var r := StoryRun.autoplay("perfect")
	assert_false(r.has("errors"), str(r.get("errors", "")))
	assert_eq(r["ending"], "legendary_set")
	assert_eq(r["sequences_passed"], 64)
	assert_eq(r["sequences_total"], 64)
	assert_eq(r["energy"], 100.0)
	for b in r["branches"]:
		if b["id"] != "win_back":
			assert_eq(b["outcome"], "good", str(b["id"]))


func test_no_input_plays_the_whole_song_and_loses_the_floor() -> void:
	var r := StoryRun.autoplay("none")
	assert_eq(r["ending"], "lost_the_floor")
	assert_eq(r["sequences_total"], 64, "every sequence is judged: no early termination")
	assert_eq(r["sequences_passed"], 0)
	assert_eq(r["energy"], 0.0)
	var run: StoryRun = r["run"]
	assert_true(run.finished)
	var last := 0.0
	for a in r["log"]:
		last = maxf(last, float(a["t0"]))
	assert_true(last >= run.level.duration_seconds() - 0.01, "the closing tableau still arrives at the song's end")
	for b in r["branches"]:
		if b["id"] != "win_back":
			assert_eq(b["outcome"], "bad", str(b["id"]))


func test_mixed_play_supports_the_middle_ending_and_recovers() -> void:
	var r := StoryRun.autoplay("sloppy", 1.0 / 60.0, 2)
	assert_eq(r["ending"], "good_night")
	assert_true(r["sequences_passed"] > 30 and r["sequences_passed"] < 64)
	var curve: Array = r["energy_curve"]
	var low := 100.0
	var rose := false
	for i in curve.size():
		low = minf(low, float(curve[i]))
		if i > 0 and float(curve[i]) > float(curve[i - 1]):
			rose = true
	assert_true(rose, "energy recovers after misses")
	assert_true(r["energy"] >= 40.0)


func test_endings_hold_across_seeded_mixes() -> void:
	var weak := StoryRun.autoplay("accuracy:0.5", 1.0 / 60.0, 1)
	assert_eq(weak["ending"], "lost_the_floor")
	var strong := StoryRun.autoplay("accuracy:0.95", 1.0 / 60.0, 1)
	assert_eq(strong["ending"], "legendary_set")


func _signature(r: Dictionary) -> String:
	var parts: Array = []
	for a in r["log"]:
		parts.append("%s@%.4f:%s" % [a["action"], float(a["t0"]), str(a["args"].get("outcome", ""))])
	return "|".join(PackedStringArray(parts)) + "#%s/%s/%s" % [r["ending"], str(r["energy"]), str(r["energy_curve"])]


func test_frame_step_does_not_change_actions_branches_or_energy() -> void:
	var a := StoryRun.autoplay("beginner", 1.0 / 60.0, 3)
	var b := StoryRun.autoplay("beginner", 1.0 / 30.0, 3)
	var c := StoryRun.autoplay("beginner", 0.0, 3)  # a variable step pattern
	assert_eq(_signature(b), _signature(a), "30 fps vs 60 fps")
	assert_eq(_signature(c), _signature(a), "variable steps vs 60 fps")
	assert_eq(b["ending"], a["ending"])


func test_every_block_fires_a_visual_action_in_every_kind_of_run() -> void:
	for policy in ["perfect", "none", "sloppy"]:
		var r := StoryRun.autoplay(policy)
		var run: StoryRun = r["run"]
		var covered := run.director.blocks_with_actions()
		for b in run.data.blocks:
			assert_true(covered.has(b["id"]), "%s: block %s has a fired action" % [policy, b["id"]])


func test_actions_are_exact_ticks_and_follow_their_sequences() -> void:
	var r := StoryRun.autoplay("beginner", 1.0 / 60.0, 1)
	var run: StoryRun = r["run"]
	var duration := run.level.duration_seconds()
	for a in r["log"]:
		assert_true(float(a["t0"]) <= duration + 0.5, "no action after the song: %s" % a["action"])
		if a["source"] == "block":
			var expect := run.director.bar_time(float(a["bar"]))
			assert_near(float(a["t0"]), expect, 0.0001, "%s fires at its bar's exact song time" % a["action"])
	var seen := {}
	for d in run.crowd.decisions_log:
		assert_false(seen.has(d["id"]), "a decision fires once")
		seen[d["id"]] = true
		var need := run.director.required_sequences(float(d["bar"]))
		var last_resolve := float(run.crowd.history[need - 1]["resolve_time"])
		assert_true(float(d["fired_t"]) >= last_resolve - 0.0001, "%s waits for its sequences to be final" % d["id"])
		assert_true(float(d["fired_t"]) >= run.director.bar_time(float(d["bar"])) - 0.0001)
	var ids := {}
	for h in run.crowd.history:
		assert_false(ids.has(h["index"]), "each sequence reaches the crowd once")
		ids[h["index"]] = true
	assert_eq(run.crowd.history.size(), 64)


func test_sequence_results_match_the_original_mission_run() -> void:
	var lr := LevelLoader.load_pack("res://songs/m01_first_watch", {})
	var level: Level = lr["level"]
	var harness: Script = load("res://tools/autoplay.gd")
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	var original := Match.new()
	original.setup(level)  # the campaign's own rules, battle on
	harness.run_mission(original, level, "beginner", rng)
	var s := StoryRun.autoplay("beginner", 1.0 / 60.0, 5)
	var run: StoryRun = s["run"]
	var a: Array = original.tracker.results
	var b: Array = run.match_ref.tracker.results
	assert_eq(a.size(), b.size())
	for i in mini(a.size(), b.size()):
		assert_eq(bool(b[i]["passed"]), bool(a[i]["passed"]), "sequence %d outcome" % i)
		assert_eq(str(b[i]["grade"]), str(a[i]["grade"]), "sequence %d grade" % i)
		assert_near(float(b[i]["credit"]), float(a[i]["credit"]), 0.0001, "sequence %d credit" % i)
	assert_eq(s["sequences_passed"], original.tracker.passed_count())


func test_restart_resets_energy_and_branches() -> void:
	var r := StoryRun.autoplay("perfect")
	var run: StoryRun = r["run"]
	assert_true(run.crowd.energy > 90.0)
	run.reset()
	assert_eq(run.crowd.energy, 45.0)
	assert_eq(run.crowd.history.size(), 0)
	assert_eq(run.crowd.decisions_log.size(), 0)
	assert_eq(run.director.fired.size(), 0)
	assert_false(run.finished)
	run.step(0.0)  # replays from the start: the first action is the same
	assert_true(run.director.fired.size() >= 1)
	assert_eq(run.director.fired[0]["action"], "lights_low_pulse")


func test_no_story_activity_touches_the_military_campaign_save() -> void:
	var campaign_path := "user://campaign.json"
	var before := FileAccess.get_file_as_string(campaign_path) if FileAccess.file_exists(campaign_path) else ""
	var path := "user://story_test_save.json"
	DirAccess.remove_absolute(path)
	var p := StoryProgress.load_data(path)
	var r := StoryRun.autoplay("perfect")
	var s: Dictionary = r["run"].summary()
	var rec := p.record("night_one", s)
	assert_eq(rec["plays"], 1)
	assert_eq(rec["best_ending"], "legendary_set")
	var again := StoryProgress.load_data(path)
	assert_eq(again.level_record("night_one")["best_ending"], "legendary_set", "the record round-trips")
	var after := FileAccess.get_file_as_string(campaign_path) if FileAccess.file_exists(campaign_path) else ""
	assert_eq(after, before, "user://campaign.json is untouched")
	DirAccess.remove_absolute(path)


func test_corrupt_story_save_is_set_aside() -> void:
	var path := "user://story_test_corrupt.json"
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string("{ not json")
	f.close()
	var p := StoryProgress.load_data(path)
	assert_true(p.recovered_from_corrupt)
	assert_eq(p.data["levels"], {})
	assert_true(FileAccess.file_exists(path + ".corrupt"), "the unreadable file is kept beside it")
	p.record("night_one", {"energy": 10.0, "accuracy": 0.5, "best_combo": 3, "sequences_passed": 5, "ending": "lost_the_floor", "branches": []})
	assert_eq(StoryProgress.load_data(path).level_record("night_one")["plays"], 1)
	DirAccess.remove_absolute(path)
	DirAccess.remove_absolute(path + ".corrupt")


func test_story_uses_the_global_loadout() -> void:
	var heavy: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/campaign/loadouts.json"))["heavy"]
	var a := StoryRun.create({"loadout": {}})
	var b := StoryRun.create({"loadout": heavy})
	assert_eq(a.errors, [])
	assert_eq(b.errors, [])
	assert_eq(a.level.loadout, Loadout.resolve(LibraryIndex.load_default(), MissionLoader.everything(LibraryIndex.load_default()), {}, []), "default loadout")
	assert_true(a.level.stems != b.level.stems or a.level.notes.size() != b.level.notes.size(), "a different loadout plays different stems or cues")
	assert_eq(a.level.sequences.size(), 64)
