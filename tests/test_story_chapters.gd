extends TestCase
## The chapter graph (Night One -> Mothership on success, Underworld on failure), unlocks from the saves, and every chapter's own
## data, endings and determinism under scripted skill levels. Art-dependent checks live in test_story_stage.

const CHAPTERS := {
	"night_one": {"bars": 128, "top": "legendary_set", "mid": "good_night", "low": "lost_the_floor", "seqs": 64},
	"mothership": {"bars": 80, "top": "galactic_headliner", "mid": "honoured_guest", "low": "beamed_home", "seqs": 40},
	"underworld": {"bars": 64, "top": "resident_dj", "mid": "survived_the_show", "low": "devoured", "seqs": 32},
	"hospital": {"bars": 56, "top": "family_celebration", "mid": "on_the_mend", "low": "quiet_ward", "seqs": 28},
	"mental_hospital": {"bars": 64, "top": "star_of_the_ward", "mid": "group_activity", "low": "lights_out", "seqs": 32},
}


func _path(id: String) -> String:
	return StoryChapters.load_default().chapter(id)["data"]


func test_registry_routes_success_to_the_mothership_and_failure_to_the_underworld() -> void:
	var c := StoryChapters.load_default()
	assert_eq(c.chapters.size(), 5)
	assert_eq(c.route("night_one", "legendary_set")["to"], "mothership")
	assert_eq(c.route("night_one", "good_night")["to"], "mothership")
	assert_eq(c.route("night_one", "lost_the_floor")["to"], "underworld")
	assert_eq(c.route("night_one", "legendary_set")["interlude"], "abduction")
	assert_eq(c.route("night_one", "lost_the_floor")["interlude"], "descent")
	for id in ["mothership", "underworld"]:
		assert_true(c.available(id), id + " ships")
		assert_eq(c.route(id, "galactic_headliner" if id == "mothership" else "resident_dj")["to"], "hospital", id + ": success wakes you in the hospital")
		assert_eq(c.route(id, "honoured_guest" if id == "mothership" else "survived_the_show")["to"], "hospital")
		assert_eq(c.route(id, "beamed_home" if id == "mothership" else "devoured")["to"], "mental_hospital", id + ": failure comes to on the ward")
		assert_eq(c.route(id, "beamed_home" if id == "mothership" else "devoured")["interlude"], "sectioned")
	assert_eq(c.route("hospital", "family_celebration"), {}, "the story ends here for now")
	for name in ["abduction", "descent", "awakening", "sectioned"]:
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
	assert_false(c.unlocked("hospital", p) or c.unlocked("mental_hospital", p), "the waking chapters need a second chapter first")
	p.record("mothership", {"energy": 70.0, "accuracy": 0.8, "best_combo": 5, "sequences_passed": 30, "ending": "honoured_guest", "ending_rank": 1, "branches": []})
	assert_true(c.unlocked("hospital", p))
	assert_false(c.unlocked("mental_hospital", p))
	p.record("underworld", {"energy": 0.0, "accuracy": 0.2, "best_combo": 1, "sequences_passed": 2, "ending": "devoured", "ending_rank": 0, "branches": []})
	assert_true(c.unlocked("mental_hospital", p))
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


func _has_art(id: String) -> bool:
	var d: StoryData = StoryData.load_file(_path(id))["data"]
	return FileAccess.file_exists(StoryAssets.BASE + d.art + "/manifest.json")


func test_chapter_art_matches_the_chapter_data() -> void:
	for id in CHAPTERS:
		if not _has_art(id):
			continue
		var d: StoryData = StoryData.load_file(_path(id))["data"]
		var a := StoryAssets.load_art(d.art)
		assert_true(a.ok(), id)
		var errs: Array = []
		d.validate_art(a, errs)
		assert_eq(errs, [], id + " art")
	var m := StoryAssets.load_art("mothership")
	assert_eq(m.view_ids(), ["main", "gallery", "reactor", "bridge"])
	var u := StoryAssets.load_art("underworld")
	assert_eq(u.view_ids(), ["main", "court", "pit", "furnace"])
	assert_eq(StoryAssets.load_art("night_one").view_ids(), ["main"], "Night One keeps its one fixed room")
	if _has_art("hospital"):
		assert_eq(StoryAssets.load_art("hospital").view_ids(), ["main", "corridor", "cafeteria", "garden"])
	if _has_art("mental_hospital"):
		assert_eq(StoryAssets.load_art("mental_hospital").view_ids(), ["main", "corridor", "art_room", "courtyard"])


func _camera_route(id: String, policy: String) -> Dictionary:
	var run := StoryRun.create({}, _path(id))
	var assets := StoryAssets.load_art(run.data.art)
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(assets, run.data, run)
	var harness: Script = load("res://tools/autoplay.gd")
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	var plan: Array = harness.plan_inputs(run.level, policy, rng)
	var k := 0
	var t := -1.0
	var shown: Array = []
	var min_present := 999
	var down := {}
	while t < run.level.duration_seconds() + 6.0:
		t += 1.0 / 30.0
		while k < plan.size() and float(plan[k]["t"]) <= t:
			var e: Dictionary = plan[k]
			if e["down"]:
				down[e["pad"]] = e["id"]
				run.match_ref.press(int(e["pad"]), float(e["t"]), int(e["pad"]))
			elif down.get(e["pad"], null) == e["id"]:
				down.erase(e["pad"])
				run.match_ref.release(int(e["pad"]), float(e["t"]), int(e["pad"]))
			k += 1
		var r := run.step(t)
		for ev in r["events"]:
			if ev["kind"] == "sequence":
				stage.on_sequence(ev["result"], float(ev["result"]["resolve_time"]))
		for a in r["actions"]:
			stage.apply(a)
		stage.update(t, run.crowd.energy)
		var vv: String = stage.current_view  # the crowd directions follow the room the player walked into
		if shown.is_empty() or shown[shown.size() - 1] != vv:
			shown.append(vv)
		if t > 1.0:
			min_present = mini(min_present, stage.crowd.present_count())
	var out := {"route": shown, "min_present": min_present, "ending": stage.ending(), "stage": stage}
	return out


func test_the_camera_walks_the_authored_route_and_every_room_is_populated() -> void:
	# the rooms with a crowd the player walks into, by skill (the medical bay, the quiet corridor and the cage have no crowd of their own)
	var expect := {"mothership": {"perfect": ["main", "gallery", "reactor", "bridge"], "none": ["main", "gallery"]},
		"underworld": {"perfect": ["main", "court", "pit"], "none": ["main", "furnace"]},
		"hospital": {"perfect": ["main", "corridor", "cafeteria", "garden"], "none": ["main"]},
		"mental_hospital": {"perfect": ["main", "corridor", "art_room", "courtyard"], "none": ["main"]}}
	for id in expect:
		if not _has_art(id):
			continue
		for policy in ["perfect", "none"]:
			var r := _camera_route(id, policy)
			assert_eq(r["route"], expect[id][policy], "%s (%s): the crowd directions follow the player through the rooms in order" % [id, policy])
			assert_true(r["min_present"] >= 8, "%s (%s): the room the camera is in is never empty (%d)" % [id, policy, r["min_present"]])
			assert_true(str(r["ending"]) != "", "%s (%s): the closing tableau happens" % [id, policy])
			(r["stage"] as StoryStage).queue_free()
