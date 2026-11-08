extends TestCase
## A void split into convex wedges is one pit (docs/story/HEIGHTS_AND_PATHS.md, StoryMap._find_voids / _group_void_tops): every wedge's `void_top`, where its depth haze starts, is
## the lowest floor of the rim around the whole connected group of void sectors, never a sibling wedge at its own depth. A void with no void next to it keeps the old rule (the
## lowest floor around it). Fixture: tests/fixtures/split_void_fixture.gd.

const FX := preload("res://tests/fixtures/split_void_fixture.gd")
const HEIGHTS := preload("res://tests/fixtures/story_heights_fixture.gd")


func test_the_fixture_builds() -> void:
	var m := StoryMap.from_dict(FX.data())
	assert_eq(m.errors, [], "the split-void map builds")
	for id in ["w1", "w2", "w3", "well"]:
		assert_true(m.is_void(id), "%s is a void" % id)


func test_every_wedge_of_a_split_void_takes_the_rim_floor() -> void:
	var m := StoryMap.from_dict(FX.data())
	for id in ["w1", "w2", "w3"]:
		assert_near(float(m.sector(id)["void_top"]), 0.5, 1e-6, "%s: the haze starts at the rim's lowest floor (the walkway), not at a sibling wedge's -8 m" % id)


func test_an_unsplit_void_is_unchanged() -> void:
	var m := StoryMap.from_dict(FX.data())
	assert_near(float(m.sector("well")["void_top"]), 0.5, 1e-6, "the well: the lowest floor around it, as before")
	var h := StoryMap.from_dict(HEIGHTS.data())
	assert_near(float(h.sector("pit_n")["void_top"]), 0.3, 1e-6, "the heights fixture's marked pit, as before")
	assert_near(float(h.sector("pit_s")["void_top"]), 0.3, 1e-6, "and its pit by depth, as before")
	assert_near(float(h.sector("west")["void_top"]), 0.3, 1e-6, "a sector that is no void keeps its value (the old rule: the step beside it)")


func test_the_split_wedges_are_hazed_like_the_whole_pit() -> void:
	var m := StoryMap.from_dict(FX.data())
	var w := StoryWorld.new()
	w.build(m, null)
	assert_eq(w.errors, [], "every tile loads")
	for id in ["w1", "w2", "w3"]:
		assert_near(w.haze_at(m.sector(id), 0.5), 0.0, 1e-6, "%s: no haze at the rim" % id)
		assert_near(w.haze_at(m.sector(id), -8.0), StoryWorld.VOID_HAZE, 1e-6, "%s: full haze at the pit's floor (the haze is on)" % id)
		assert_near(w.haze_at(m.sector(id), -3.75), w.haze_at(m.sector("w1"), -3.75), 1e-6, "%s: hazed the same as its siblings, one pit" % id)
	w.free()
