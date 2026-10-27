extends TestCase
## Song-pack validation (PRD section 9).


static func _base() -> Dictionary:
	return {
		"schema_version": 1, "level_id": "x", "title": "X", "bpm": 174, "time_signature": [4, 4], "ticks_per_beat": 960,
		"song_offset_ms": 0, "duration_ticks": 3840 * 4, "seed": 1,
		"stems": {"kick": "audio/k.ogg", "snare": "audio/s.ogg", "bass": "audio/b.ogg", "other": "audio/o.ogg"},
		"sections": [{"id": "a", "start_tick": 0, "length_bars": 2}, {"id": "b", "start_tick": 7680, "length_bars": 2}],
		"notes": [
			{"id": "n1", "tick": 0, "lane": "kick", "type": "tap"},
			{"id": "n2", "tick": 960, "lane": "snare", "type": "tap"},
			{"id": "n3", "tick": 1920, "lane": "bass", "type": "hold", "duration_ticks": 1920},
		],
		"enemy_events": [{"id": "e1", "tick": 0, "action": "kick"}, {"id": "e2", "tick": 960, "action": "snare"}],
	}


func _errors_for(d: Dictionary) -> Array:
	var errors: Array = []
	var warnings: Array = []
	LevelLoader.parse(d, "/pack", errors, warnings)
	return errors


func test_valid_definition_parses() -> void:
	var errors: Array = []
	var warnings: Array = []
	var level := LevelLoader.parse(_base(), "/pack", errors, warnings)
	assert_eq(errors, [])
	assert_eq(level.notes.size(), 3)
	assert_eq(level.enemy_events.size(), 2)
	assert_eq(level.stems["kick"], "/pack/audio/k.ogg")
	assert_eq(level.notes[2]["end_tick"], 3840)
	assert_near(level.notes[2]["end_time"], level.tick_to_seconds(3840), 0.000001)


func test_rejections() -> void:
	var d := _base()
	d["schema_version"] = 2
	assert_contains(_errors_for(d), "schema_version")
	d = _base()
	d["stems"].erase("other")
	assert_contains(_errors_for(d), "stem 'other' is required")
	d = _base()
	d["stems"]["kick"] = "../outside.ogg"
	assert_contains(_errors_for(d), "escapes the pack root")
	d = _base()
	d["notes"].append({"id": "n1", "tick": 3000, "lane": "kick", "type": "tap"})
	assert_contains(_errors_for(d), "duplicated")
	d = _base()
	d["notes"][0]["lane"] = "hat"
	assert_contains(_errors_for(d), "unsupported lane")
	d = _base()
	d["enemy_events"][0]["action"] = "nuke"
	assert_contains(_errors_for(d), "unsupported action")
	d = _base()
	d["notes"][0]["tick"] = -1
	assert_contains(_errors_for(d), "negative tick")
	d = _base()
	d["notes"][2]["duration_ticks"] = 0
	assert_contains(_errors_for(d), "must be positive")
	d = _base()
	d["notes"][2]["duration_ticks"] = 3840 * 4
	assert_contains(_errors_for(d), "ends beyond the song end")
	d = _base()
	d["notes"][0]["type"] = "hold"
	d["notes"][0]["duration_ticks"] = 10
	assert_contains(_errors_for(d), "only allowed on the bass lane")
	d = _base()
	d["sections"][1]["start_tick"] = 7000
	assert_contains(_errors_for(d), "contiguous")
	d = _base()
	d["sections"][1]["length_bars"] = 1
	assert_contains(_errors_for(d), "duration_ticks is")
	d = _base()
	d["notes"].append({"id": "n4", "tick": 0, "lane": "kick", "type": "tap"})
	assert_contains(_errors_for(d), "share button 1")
	d = _base()
	d["notes"].append({"id": "n4", "tick": 2400, "lane": "bass", "type": "tap", "button": 2})
	assert_contains(_errors_for(d), "starts inside hold")
	d = _base()
	d["notes"].append({"id": "n4", "tick": 2400, "lane": "kick", "type": "tap", "button": 2})
	assert_contains(_errors_for(d), "kick notes are played on button 1")
	d = _base()
	d["notes"].append({"id": "n4", "tick": 2400, "lane": "bass", "type": "tap", "button": 5})
	assert_contains(_errors_for(d), "button must be 1..4")
	d = _base()
	d["notes"].append({"id": "n4", "tick": 1920, "lane": "bass", "type": "tap", "button": 1})
	d["notes"].append({"id": "n5", "tick": 1920, "lane": "kick", "type": "tap"})
	assert_contains(_errors_for(d), "share button 1")
	d = _base()
	d["enemy_events"].append({"id": "e3", "tick": 10, "action": "kick"})
	assert_contains(_errors_for(d), "out of order")
	d = _base()
	d["enemy_events"].append({"id": "e3", "tick": 3840 * 4, "action": "kick"})
	assert_contains(_errors_for(d), "beyond the song end")


func test_three_touch_chord_is_flagged_for_review() -> void:
	var d := _base()
	d["notes"].append({"id": "n4", "tick": 2880, "lane": "kick", "type": "tap"})
	d["notes"].append({"id": "n5", "tick": 2880, "lane": "snare", "type": "tap"})
	var errors: Array = []
	var warnings: Array = []
	LevelLoader.parse(d, "/pack", errors, warnings)
	assert_eq(errors, [])
	assert_contains(warnings, "three-touch chord")


func test_real_packs_load_with_aligned_stems() -> void:
	for pack in ["songs/test_16", "songs/level_01"]:
		var path := TestCase.project_path(pack)
		if not FileAccess.file_exists(path.path_join("level.json")):
			fail("pack missing: %s" % path)
			continue
		var r := LevelLoader.load_pack(path)
		assert_eq(r["errors"], [], pack)
		if r["level"] != null:
			var level: Level = r["level"]
			assert_true(level.notes.size() > 0, "%s has notes" % pack)
			assert_true(level.stem_lengths.size() == 4, "%s decoded four stems" % pack)
			assert_true(level.stem_lengths["kick"] >= level.duration_seconds(), "%s stems cover the chart" % pack)
