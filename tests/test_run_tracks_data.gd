extends TestCase
## Track scenes, the data (docs/RUN_TRACK_SCENES.md "Data"): content/run/track_scenes.json read and checked (errors as sentences), packs looked up in a folder, the run's seed picking between a scene's
## track and its alternates reproducibly and skipping missing packs, a refused pack, and a scene whose pack is missing (or with RW_RUN_TRACKS=0) playing exactly as today.

const Fx := preload("res://tests/fixtures/track_scenes/track_scene_fixtures.gd")
const Recorder := preload("res://tests/fixtures/track_scenes/baseline_recorder.gd")


func _has(errors: Array, needle: String) -> bool:
	for e in errors:
		if str(e).contains(needle):
			return true
	return false


func test_the_file_is_checked_and_its_errors_are_sentences() -> void:
	var d := RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, 7)
	var path := Fx.SCENES_JSON
	var fa := FileAccess.open(path, FileAccess.WRITE)
	fa.store_string(JSON.stringify({"format": "rhythm_warfare.track_scenes.v0", "defaults": {"entry": "drop9", "max_laps": 0, "start_bar": 3, "speed": 2},
		"paths": {"main": {"nowhere": {"track": "a"}, "warehouse": {"track": "Bad-Id", "laps": 20, "doors_from_lap": 0, "colour": "red",
			"alternates": [{"track": "ok_one", "alternates": []}, 5]}, "warehouse.bar": {"track": "fine_one", "entry": "drop2", "chart": "hard"}}, "atlantis": {}}}))
	fa.close()
	var ts := RunTrackScenes.load_for(d, path, Fx.root())
	var errs := d.errors
	assert_true(_has(errs, "format is 'rhythm_warfare.track_scenes.v0' but must be 'rhythm_warfare.track_scenes.v1'"), str(errs))
	assert_true(_has(errs, "defaults: entry 'drop9' is not one of drop1, drop2, start"))
	assert_true(_has(errs, "defaults: max_laps must be a whole number of 1 or more"))
	assert_true(_has(errs, "start_bar belongs to a scene, not to the defaults"))
	assert_true(_has(errs, "defaults.speed is not a field"))
	assert_true(_has(errs, "paths.atlantis is neither \"main\" nor a path under content/paths"))
	assert_true(_has(errs, "paths.main scene nowhere: there is no such scene in this run"))
	assert_true(_has(errs, "scene warehouse: track 'Bad-Id' must be a track id"))
	assert_true(_has(errs, "scene warehouse: 'colour' is not a field of a scene entry"))
	assert_true(_has(errs, "scene warehouse: doors_from_lap must be a whole number of 1 or more"))
	assert_true(_has(errs, "scene warehouse alternate 1: 'alternates' is not a field of an alternate"))
	assert_true(_has(errs, "scene warehouse alternate 2: must be an object"))
	assert_true(ts.errors.size() == errs.size(), "every problem is the run's error too")
	assert_false(ts.has_entry("warehouse"), "a broken entry is not used")
	assert_true(ts.has_entry("warehouse.bar"), "a good one is")
	var d2 := RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, 7)
	fa = FileAccess.open(path, FileAccess.WRITE)
	fa.store_string(JSON.stringify({"format": RunTrackScenes.FORMAT, "defaults": {"max_laps": 6}, "paths": {"main": {"warehouse": {"track": "x", "laps": 7}}, "gospel": {"jordan": {"track": "y"}}}}))
	fa.close()
	RunTrackScenes.load_for(d2, path, Fx.root())
	assert_true(_has(d2.errors, "scene warehouse: laps 7 is more than max_laps 6"), str(d2.errors))
	assert_eq(d2.errors.size(), 1, "another path's scenes are that path's business")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(path))


func test_a_missing_pack_or_track_scenes_off_play_exactly_as_today() -> void:
	Fx.clear()
	var plain := RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, 7)
	var want := Recorder._record(plain, "warehouse", 3, -1, false)
	var missing := Fx.main_data({"main": {"warehouse": {"track": "not_here", "alternates": [{"track": "nor_this"}]}, "warehouse.bar": {"track": "gone_too"}}})
	assert_eq(missing.errors, [])
	assert_true(missing.track_scenes != null)
	assert_false(missing.track_scenes.is_track_scene("warehouse"), "no pack present: not a track scene")
	var got := Recorder._record(missing, "warehouse", 3, -1, false)
	assert_eq(got.size(), want.size())
	var same := got.size() == want.size()
	for i in mini(got.size(), want.size()):
		if str(got[i]) != str(want[i]):
			same = false
			assert_eq(str(got[i]), str(want[i]), "line %d" % i)
			break
	assert_true(same, "a scene whose packs are all missing plays event for event as today")
	# RW_RUN_TRACKS=0: nothing is attached even with the switch on
	Fx.write_pack("acuna_go_back", Fx.go_back_spec())
	RunTrackScenes.enabled = 1
	RunTrackScenes.packs_dir_override = Fx.root()
	RunTrackScenes.json_path_override = Fx.write_scenes({"main": {"warehouse": {"track": "acuna_go_back"}}})
	OS.set_environment("RW_RUN_TRACKS", "0")
	var off := RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, 7)
	assert_true(off.track_scenes == null, "RW_RUN_TRACKS=0: no track scenes")
	var got_off := Recorder._record(off, "warehouse", 3, -1, false)
	assert_eq(got_off, want, "and the run is today's")
	OS.unset_environment("RW_RUN_TRACKS")
	var on := RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, 7)
	assert_true(on.track_scenes != null, "with the switch on, RunData.load_files attaches them")
	assert_true(on.track_scenes.is_track_scene("warehouse"), "and the warehouse plays the track")
	assert_eq(on.track_scenes.packs_dir, Fx.root())
	RunTrackScenes.enabled = -1
	RunTrackScenes.packs_dir_override = ""
	RunTrackScenes.json_path_override = ""
	assert_true(RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, 7).track_scenes == null, "the switch back to automatic: off under the test runner")
	Fx.clear()


func test_alternates_are_picked_by_the_seed_reproducibly_and_missing_packs_are_skipped() -> void:
	Fx.clear()
	for id in ["alt_a", "alt_b", "alt_c"]:
		Fx.write_pack(id, Fx.go_back_spec())
	var entry := {"warehouse": {"track": "alt_a", "alternates": [{"track": "alt_missing"}, {"track": "alt_b", "entry": "drop2"}, {"track": "alt_c", "laps": 2}]}}
	var seen := {}
	for s in range(1, 41):
		var d := Fx.main_data({"main": entry}, s)
		var p := d.track_scenes.plan_of("warehouse")
		var again := Fx.main_data({"main": entry}, s).track_scenes.plan_of("warehouse")
		assert_eq(str(p["track"]), str(again["track"]), "seed %d: the same seed, the same track" % s)
		var cands := d.track_scenes.candidates("warehouse")
		assert_eq(cands.map(func(c: Dictionary) -> String: return str(c["track"])), ["alt_a", "alt_b", "alt_c"], "the missing alternate is skipped")
		var want := absi(("%d:%s" % [s, "warehouse"]).hash()) % 3
		assert_eq(int(p["pick"]), want, "picked as a scene's arrangement alternates are")
		assert_eq(str(p["track"]), str(cands[want]["track"]))
		seen[str(p["track"])] = true
		if str(p["track"]) == "alt_b":
			assert_eq(str(p["entry"]), "drop2", "an alternate's own fields apply")
			assert_eq(int(p["index"]), 2, "its place in the file (the track is 0)")
		if str(p["track"]) == "alt_c":
			assert_eq(int(p["laps"]), 2)
	assert_eq(seen.size(), 3, "over 40 seeds every present candidate is picked")
	RunData.arrangement_override = 1
	assert_eq(str(Fx.main_data({"main": entry}, 3).track_scenes.plan_of("warehouse")["track"]), "alt_b", "the playtest override picks the second present candidate")
	RunData.arrangement_override = -1
	Fx.clear()


func test_a_refused_pack_is_skipped_with_a_warning() -> void:
	Fx.clear()
	var dir := Fx.write_pack("broken_one", Fx.go_back_spec())
	var fa := FileAccess.open(dir.path_join("track.json"), FileAccess.WRITE)
	fa.store_string("{\"format\": \"rhythm_warfare.track.v2\", \"id\": \"broken_one\"}")
	fa.close()
	Fx.write_pack("good_one", Fx.go_back_spec())
	var d := Fx.main_data({"main": {"warehouse": {"track": "broken_one"}, "warehouse.bar": {"track": "broken_one", "alternates": [{"track": "good_one"}]}}})
	assert_eq(d.errors, [], "a pack on the machine is not the run data's error")
	assert_false(d.track_scenes.is_track_scene("warehouse"), "a refused pack: an ordinary scene")
	assert_true(_has(d.track_scenes.warnings, "scene warehouse: the pack of track broken_one is refused"), str(d.track_scenes.warnings))
	assert_eq(str(d.track_scenes.plan_of("warehouse.bar")["track"]), "good_one", "the next candidate takes the turn")
	var plan := d.track_scenes.plan_of("warehouse.bar")
	assert_true(plan["pack"] is TrackPack, "the plan carries the loaded pack")
	assert_eq((plan["pack"] as TrackPack).dir, Fx.root().path_join("good_one"))
	assert_true((plan["pack"] as TrackPack).streams.is_empty(), "with no stem decoded (the audio's business)")
	Fx.clear()
