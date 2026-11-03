extends TestCase
## The loop library index (songs/library/index.json, contract rhythm_warfare.library.v1). The fixture checks always run;
## the checks on the real library run once tools/content/build.py has written it and are skipped with a note before that.

const FIXTURE := "tests/fixtures/library_fixture/index.json"
const REAL := "songs/library/index.json"


func _fixture() -> LibraryIndex:
	var idx := LibraryIndex.load_from(TestCase.project_path(FIXTURE))
	assert_eq(idx.error, "", "the fixture index loads")
	return idx


func test_fixture_lookups() -> void:
	var idx := _fixture()
	assert_eq(idx.clips.size(), 7)
	assert_eq(idx.sounds.size(), 7)
	assert_eq(idx.kind("groove_a"), "groove")
	assert_eq(idx.kind("fill_a"), "fill")
	assert_eq(idx.kind("kick_a"), "sound")
	assert_eq(idx.kind("nothing"), "")
	assert_eq(idx.name("groove_a"), "Fixture Groove A")
	assert_eq(idx.name("kick_b"), "Fixture Kick B")
	assert_eq(idx.name("unknown_id"), "unknown_id", "an unknown id names itself")
	assert_eq(idx.produces("kick_a").size(), 2)
	assert_eq(idx.produces("snare_b"), [])
	assert_eq(idx.produces("nothing"), [])
	assert_eq(idx.defaults["groove"], "groove_a")
	assert_eq(idx.cues("groove_a", "kick").size(), 16)
	assert_eq(idx.clip_bars("groove_a"), 8)


func test_fixture_loop_paths_exist_and_are_absolute() -> void:
	var idx := _fixture()
	for clip in idx.clips:
		var c: Dictionary = idx.clips[clip]
		for part in c["parts"]:
			var sounds: Array = c["sounds"].get(part, [""])
			for s in sounds:
				var path := idx.loop_path(clip, part, str(s))
				assert_false(path.is_empty(), "%s %s %s has a loop" % [clip, part, s])
				assert_true(FileAccess.file_exists(path), path)
				assert_true(path.is_absolute_path(), "an absolute path: " + path)
	assert_eq(idx.loop_path("groove_a", "kick", "kick_a") == idx.loop_path("groove_a", "kick", "kick_b"), false, "each sound has its own file")
	assert_eq(idx.loop_path("groove_a", "kick", "snare_a"), "", "a sound the clip does not play has no loop")
	assert_eq(idx.loop_path("nothing", "kick", "kick_a"), "")
	assert_false(idx.loop_path("acc_b", "other", "").is_empty(), "a backing's only loop is found without a sound id")


func test_missing_index_is_an_empty_library() -> void:
	var idx := LibraryIndex.load_from(TestCase.project_path("tests/fixtures/no_such_library/index.json"))
	assert_true(idx.is_empty())
	assert_false(idx.error.is_empty())
	assert_eq(idx.compatible("groove", {}), [])


func test_real_library_when_built() -> void:
	if not FileAccess.file_exists(TestCase.project_path(REAL)):
		print("  note: songs/library/index.json is not built yet; the real-library checks are skipped")
		return
	var idx := LibraryIndex.load_from(TestCase.project_path(REAL))
	assert_eq(idx.error, "")
	assert_eq(idx.loop_bars, 8)
	assert_near(idx.bpm, 174.0, 0.001)
	assert_eq(idx.ticks_per_beat, 960)
	assert_true(Loadout.is_valid(idx, idx.defaults), "the default loadout is compatible")
	assert_eq(idx.defaults["fill"], "")
	for clip in idx.clips:
		var c: Dictionary = idx.clips[clip]
		var kind := str(c["kind"])
		assert_true(kind in ["groove", "fill", "bass", "backing"], "%s has a known kind" % clip)
		assert_true(int(c["bars"]) in [8, 16], "%s is 8 or 16 bars" % clip)
		for part in c["parts"]:
			if kind != "backing":
				assert_true((c["cues"].get(part, []) as Array).size() > 0, "%s part %s has cues" % [clip, part])
				for cue in c["cues"][part]:
					assert_true(int(cue[0]) >= 0 and int(cue[0]) < int(c["bars"]) * 3840, "%s cue inside the loop" % clip)
					assert_true(int(cue[2]) >= 1 and int(cue[2]) <= 4, "%s cue pad 1 to 4" % clip)
			var sounds: Array = c["sounds"].get(part, [])
			if sounds.is_empty():
				sounds = [""]
			for s in sounds:
				var path := idx.loop_path(clip, str(part), str(s))
				assert_true(not path.is_empty() and FileAccess.file_exists(path), "loop of %s %s %s exists (%s)" % [clip, part, s, path])
				if kind != "backing":
					assert_true(idx.sounds.has(str(s)), "%s plays a sound the index knows (%s)" % [clip, s])
	for s in idx.sounds:
		assert_true(str(idx.sounds[s]["family"]) in ["kick", "snare", "bass", "other"], "%s has a family" % s)
		for p in idx.produces(s):
			assert_false(MissionRules.reward(str(p["reward"])).is_empty(), "%s produces a known reward (%s)" % [s, p["reward"]])
	for fill in idx.clips_of("fill"):
		for cue in idx.cues(fill, "kick") + idx.cues(fill, "snare"):
			assert_true(int(cue[0]) >= 7 * 3840 and int(cue[0]) < 8 * 3840, "a fill's cues sit in bar 8 (%s)" % fill)
