extends TestCase
## Figures doing things (docs/STORY_25D_ART_DIRECTION.md 2.C): every sector of every chapter authors its activities for every mood band, nobody dances off a dance floor
## or in the quiet band, activities are valid and have analytic poses, pairs face each other, watchers face their target, the fun beats of each chapter are in place.

const CHAPTERS := ["night_one", "mothership", "underworld", "hospital", "mental_hospital"]


func _stage(id: String) -> StoryStage:
	var run := StoryRun.create({}, "res://content/story/%s.json" % id)
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_art(run.data.art), run.data, run)
	return stage


func test_every_sector_authors_activities_for_every_band() -> void:
	for id in CHAPTERS:
		var m := StoryMap.load_chapter(id)
		assert_true(m.errors.is_empty(), "%s: %s" % [id, str(m.errors)])
		for s in m.sectors:
			var acts: Dictionary = s["activities"]
			assert_true(bool(acts.get("authored", false)), "%s/%s authors its own activities" % [id, s["id"]])
			for band in StoryMap.BANDS:
				var l := m.activities_of(str(s["id"]), band)
				assert_false(l.is_empty(), "%s/%s has activities for %s" % [id, s["id"], band])
				for n in l:
					assert_true(str(n) in StoryCharacter.ACTIVITIES, "%s/%s: %s is an activity" % [id, s["id"], n])
					if str(n) == "dance":
						assert_true(StoryMap._any_in(s["flags"], StoryMap.DANCE_FLAGS) and band != "quiet", "%s/%s: dance only on a dance floor or stage, never in the quiet band" % [id, s["id"]])


func test_validation_rejects_dancing_off_the_dance_floor_and_in_the_quiet_band() -> void:
	var base := {"textures": {}, "start": "a", "sectors": [{"id": "a", "polygon": [[0, 0], [4, 0], [4, 4], [0, 4]], "floor": 0, "ceiling": 3, "flags": ["dance_floor"],
		"activities": {"quiet": ["dance"], "dancing": ["dance"], "hype": ["dance"]}}], "walls": [], "waypoints": [{"id": "a", "at": [2, 2], "yaw": 0, "sector": "a"}], "homes": [], "things": []}
	assert_true(" ".join(PackedStringArray(StoryMap.from_dict(base).errors)).contains("never in the quiet band"), "quiet dance rejected")
	base["sectors"][0]["activities"] = {"quiet": ["stand"], "dancing": ["dance"], "hype": ["dance"]}
	assert_eq(StoryMap.from_dict(base).errors, [])
	base["sectors"][0]["flags"] = []
	assert_true(" ".join(PackedStringArray(StoryMap.from_dict(base).errors)).contains("only for dance_floor"), "dance off the floor rejected")
	base["sectors"][0]["activities"] = {"quiet": ["stand"], "dancing": ["moonwalk"], "hype": ["stand"]}
	assert_true(" ".join(PackedStringArray(StoryMap.from_dict(base).errors)).contains("unknown activity"), "unknown activity rejected")
	base["sectors"][0]["activities"] = {"quiet": ["stand"]}
	assert_true(" ".join(PackedStringArray(StoryMap.from_dict(base).errors)).contains("non-empty list"), "all three bands required")


func test_nobody_dances_off_the_floor_or_in_the_quiet_band_and_everyone_has_a_pick_in_every_band() -> void:
	for id in CHAPTERS:
		var stage := _stage(id)
		for rid in stage.crowds:
			var crowd: StoryCrowd = stage.crowds[rid]
			for aid in crowd.actors:
				var a: Dictionary = crowd.actors[aid]
				for band in StoryMap.BANDS:
					var act := crowd.pick_activity(a, band)
					assert_true(act in StoryCharacter.ACTIVITIES, "%s %s: %s in %s is an activity" % [id, aid, act, band])
					if act == "dance":
						assert_true(str(a["lock"]) != "" or (band != "quiet" and crowd._dancing_here(a)), "%s %s dances in %s off the dance floor or in the quiet band" % [id, aid, band])
				assert_eq(crowd.pick_activity(a, "dancing"), crowd.pick_activity(a, "dancing"), "the pick is stable (never random per frame)")
		stage.free()


func test_quiet_band_screenshot_rule_fewer_than_half_dance_off_the_floor() -> void:
	for id in CHAPTERS:
		var stage := _stage(id)
		for band in StoryMap.BANDS:
			var off := 0
			var dancing := 0
			for rid in stage.crowds:
				var crowd: StoryCrowd = stage.crowds[rid]
				for aid in crowd.actors:
					var a: Dictionary = crowd.actors[aid]
					if crowd._dancing_here(a):
						continue
					off += 1
					if crowd.pick_activity(a, band) == "dance":
						dancing += 1
			assert_true(off == 0 or dancing * 2 < off, "%s %s: of %d people off the dance floors %d dance" % [id, band, off, dancing])
		stage.free()


func test_every_activity_has_a_finite_analytic_pose() -> void:
	var c := StoryCharacter.new()
	for act in StoryCharacter.ACTIVITIES:
		for beats in [0.0, 1.3, 7.7, 100.25]:
			var p := c.sample(str(act), beats, 0.6)
			for k in StoryCharacter.POSE_KEYS:
				assert_true(is_finite(float(p[k])), "%s %s is finite" % [act, k])
			assert_eq(p, c.sample(str(act), beats, 0.6), "%s is a pure function of the beat" % act)
	var lie := c.sample("lie", 3.0, 0.5)
	assert_true(absf(float(lie["roll"])) > 1.2, "lying down is a roll of the body")
	c.free()


func test_pairs_face_each_other_and_a_lone_chatter_falls_back() -> void:
	var stage := _stage("night_one")
	var crowd: StoryCrowd = stage.crowds["main"]
	crowd.update(1.0, 40.0)
	crowd.update(1.1, 40.0)
	var s02: Dictionary = crowd.actors["s02"]
	var s03: Dictionary = crowd.actors["s03"]
	assert_eq(s02["partner"], "s03", "the two chatting on the sofas are a pair")
	assert_eq(s03["partner"], "s02")
	assert_true(s02["node"].chat_role != s03["node"].chat_role, "one talks while the other listens")
	crowd.set_camera({"cam": Vector3(10, 1.6, 12), "yaw": 180.0}, Vector2(480, 170), {})
	crowd.update(1.2, 40.0)
	assert_true(float(s02["node"].toward) * float(s03["node"].toward) < 0.0, "they face opposite ways on the screen, towards each other")
	crowd.actors["s03"]["lock"] = "stand"
	crowd.update(1.3, 40.0)  # the change is noticed, the pairs are rebuilt on the next frame
	crowd.update(1.4, 40.0)
	assert_eq(crowd.actors["s02"]["partner"], "", "a lone chatter has no partner")
	assert_eq(crowd.actors["s02"]["node"].state, "stand", "and stands instead")
	stage.free()


func test_watchers_turn_towards_their_target() -> void:
	var stage := _stage("night_one")
	var crowd: StoryCrowd = stage.crowds["main"]
	crowd.set_camera({"cam": Vector3(0, 1.6, 6.5), "yaw": 0.0}, Vector2(480, 170), {})
	crowd.update(1.0, 40.0)
	crowd.update(1.1, 40.0)
	var v03: Dictionary = crowd.actors["v03"]  # on the balcony, watching floor_centre (to its right when facing -z from the floor)
	assert_eq(v03["node"].state, "watch")
	assert_true(float(v03["node"].toward) > 0.0, "the balcony watcher faces the floor, to the right of the screen")
	stage.free()


func test_locked_fun_characters_ignore_the_band_and_the_directives() -> void:
	var stage := _stage("night_one")
	var crowd: StoryCrowd = stage.crowds["main"]
	crowd.direct(crowd.present_ids(), "clap", 0.0, 100.0, true)
	crowd.update(1.0, 90.0)
	crowd.update(1.1, 90.0)
	assert_eq(crowd.actors["d01"]["node"].state, "check", "the door staff keeps checking tickets in a euphoric room")
	assert_eq(crowd.actors["d01"]["node"].held, "tickets")
	assert_eq(crowd.actors["s01"]["node"].state, "sleep", "the sleeper sleeps through the clap")
	stage.free()
