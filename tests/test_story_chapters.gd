extends TestCase
## The chapter graph (Night One -> Mothership on success, Underworld on failure), unlocks from the saves, and every chapter's own
## data, endings and determinism under scripted skill levels. Art-dependent checks live in test_story_stage.

const CHAPTERS := {
	"night_one": {"bars": 128, "top": "legendary_set", "mid": "good_night", "low": "lost_the_floor", "seqs": 64},
	"mothership": {"bars": 80, "top": "galactic_headliner", "mid": "honoured_guest", "low": "beamed_home", "seqs": 40},
	"underworld": {"bars": 64, "top": "resident_dj", "mid": "survived_the_show", "low": "devoured", "seqs": 32},
}


func _path(id: String) -> String:
	return StoryChapters.load_default().chapter(id)["data"]


func test_registry_routes_success_to_the_mothership_and_failure_to_the_underworld() -> void:
	var c := StoryChapters.load_default()
	assert_eq(c.chapters.size(), 3)
	assert_eq(c.route("night_one", "legendary_set")["to"], "mothership")
	assert_eq(c.route("night_one", "good_night")["to"], "mothership")
	assert_eq(c.route("night_one", "lost_the_floor")["to"], "underworld")
	assert_eq(c.route("night_one", "legendary_set")["interlude"], "abduction")
	assert_eq(c.route("night_one", "lost_the_floor")["interlude"], "descent")
	for id in ["mothership", "underworld"]:
		assert_true(c.available(id), id + " ships")
	for name in ["abduction", "descent"]:
		var it := StoryChapters.interlude(name)
		assert_false(it.is_empty(), name)
		assert_true((it["events"] as Array).size() >= 5, name + " is a staged sequence")
		for e in it["events"]:
			assert_true(float(e["t"]) < float(it["duration"]), "%s event %s inside the cutscene" % [name, e["do"]])


func test_unlocks_follow_the_endings_in_the_saves() -> void:
	var c := StoryChapters.load_default()
	var path := "user://story_test_unlock.json"
	DirAccess.remove_absolute(path)
	var p := StoryProgress.load_data(path)
	assert_true(c.unlocked("night_one", p))
	assert_false(c.unlocked("mothership", p))
	assert_false(c.unlocked("underworld", p))
	p.record("night_one", {"energy": 10.0, "accuracy": 0.4, "best_combo": 1, "sequences_passed": 3, "ending": "lost_the_floor", "ending_rank": 0, "branches": []})
	assert_false(c.unlocked("mothership", p), "a failure does not open the ship")
	assert_true(c.unlocked("underworld", p), "a failure opens the underworld")
	p.record("night_one", {"energy": 90.0, "accuracy": 0.95, "best_combo": 20, "sequences_passed": 63, "ending": "legendary_set", "ending_rank": 2, "branches": []})
	assert_true(c.unlocked("mothership", p))
	assert_eq(p.level_record("night_one")["best_ending"], "legendary_set", "the best ending is kept by rank")
	p.record("night_one", {"energy": 10.0, "accuracy": 0.4, "best_combo": 1, "sequences_passed": 3, "ending": "lost_the_floor", "ending_rank": 0, "branches": []})
	assert_eq(p.level_record("night_one")["best_ending"], "legendary_set", "a worse run does not lower the best")
	DirAccess.remove_absolute(path)


func test_each_chapter_validates_and_matches_its_music() -> void:
	for id in CHAPTERS:
		var loaded := StoryData.load_file(_path(id))
		assert_eq(loaded["errors"], [], id)
		var d: StoryData = loaded["data"]
		assert_eq(d.duration_bars, CHAPTERS[id]["bars"], id)
		assert_eq(d.blocks.size(), CHAPTERS[id]["bars"] / 8, id + " blocks")
		assert_true(d.decisions.size() >= 3, id + " has at least three authored good/bad moments")
		assert_eq(d.ending_order.size(), 3)
		assert_true(d.actors.size() >= 24, id + " crowd")
		var run := StoryRun.create({}, _path(id))
		assert_eq(run.errors, [], id + " plays its music pack at its full length")
		assert_eq(run.level.sequences.size(), CHAPTERS[id]["seqs"], id)


func test_chapter_endings_under_perfect_mixed_and_no_input() -> void:
	for id in CHAPTERS:
		var spec: Dictionary = CHAPTERS[id]
		var top := StoryRun.autoplay("perfect", 1.0 / 60.0, 1, {}, _path(id))
		assert_eq(top["ending"], spec["top"], id + " perfect")
		assert_eq(top["sequences_passed"], spec["seqs"])
		var none := StoryRun.autoplay("none", 1.0 / 60.0, 1, {}, _path(id))
		assert_eq(none["ending"], spec["low"], id + " no input plays the whole song and loses")
		assert_eq(none["sequences_total"], spec["seqs"])
		assert_true(none["run"].finished)
		var mid := StoryRun.autoplay("sloppy", 1.0 / 60.0, 2, {}, _path(id))
		assert_eq(mid["ending"], spec["mid"], id + " mixed play")
		for policy in ["perfect", "none", "sloppy"]:
			var r := StoryRun.autoplay(policy, 1.0 / 60.0, 1, {}, _path(id))
			var covered: Dictionary = r["run"].director.blocks_with_actions()
			for b in r["run"].data.blocks:
				assert_true(covered.has(b["id"]), "%s/%s: block %s fires an action" % [id, policy, b["id"]])


func test_chapter_frame_steps_are_deterministic() -> void:
	for id in ["mothership", "underworld"]:
		var a := StoryRun.autoplay("beginner", 1.0 / 60.0, 3, {}, _path(id))
		var b := StoryRun.autoplay("beginner", 1.0 / 30.0, 3, {}, _path(id))
		var c := StoryRun.autoplay("beginner", 0.0, 3, {}, _path(id))
		var sig := func(r: Dictionary) -> String:
			var parts: Array = []
			for x in r["log"]:
				parts.append("%s@%.4f" % [x["action"], float(x["t0"])])
			return "|".join(PackedStringArray(parts)) + str(r["ending"]) + str(r["energy_curve"])
		assert_eq(sig.call(b), sig.call(a), id + " 30 vs 60")
		assert_eq(sig.call(c), sig.call(a), id + " variable vs 60")
