extends TestCase
## Campaign progress (save version 2): the ladder, option unlocks, selections, results, the unlock-all switch, a corrupt
## save and the migration of a version 1 save from the instrument-loadout build.

const SAVE := "user://test_campaign_save.json"


func _fresh(unlock: int = 0) -> Campaign:
	for suffix in ["", ".bad", ".v1", ".tmp"]:
		if FileAccess.file_exists(SAVE + suffix):
			DirAccess.remove_absolute(SAVE + suffix)
	return Campaign.load_data(SAVE, unlock)


func _win(level_id: String, number: int) -> Dictionary:
	return {"mode": "mission", "outcome": "victory", "battle": true, "play_mode": "campaign", "progression": true, "level_id": level_id,
		"campaign_level": number, "accuracy": 0.9, "sequences": 8, "sequences_passed": 7, "best_combo": 12,
		"objective_hp": {"command_core": {"hp": 30000, "max": 60000}}}


func test_normal_progression_is_the_shipped_default() -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(Campaign.DATA_PATH))
	assert_false(bool(data["unlock_all"]), "the finished campaign ships with normal progression")
	assert_eq(data["levels"].size(), 10)


func test_ladder_opens_one_mission_per_clear() -> void:
	var c := _fresh()
	assert_true(c.is_unlocked(1))
	assert_false(c.is_unlocked(2))
	var rec := c.record_result(_win("level_01", 1))
	assert_true(rec["first_clear"])
	assert_eq(rec["unlocked_level"], 2)
	assert_true(c.is_unlocked(2))
	assert_false(c.is_unlocked(3))
	var again := c.record_result(_win("level_01", 1))
	assert_false(again["first_clear"], "a replay never resets anything")
	assert_eq(int(c.progress["cleared"]["level_01"]["clears"]), 2)


func test_defeat_practice_and_rhythm_only_record_nothing() -> void:
	var c := _fresh()
	var lose := _win("level_01", 1)
	lose["outcome"] = "defeat"
	assert_eq(c.record_result(lose), {})
	var practice := _win("level_01", 1)
	practice["play_mode"] = "practice"
	practice["progression"] = false
	assert_eq(c.record_result(practice), {})
	var no_battle := _win("level_01", 1)
	no_battle["battle"] = false
	assert_eq(c.record_result(no_battle), {})
	assert_false(c.is_cleared("level_01"))


func test_options_unlock_with_their_mission_and_defaults_are_always_open() -> void:
	var c := _fresh()
	assert_eq(c.option_lock(2, "snare_guard", ["snare_guard"]), "")
	assert_contains(c.option_lock(2, "snare_crack", ["snare_guard"]), "First Watch", "says what unlocks it")
	c.record_result(_win("level_01", 1))
	assert_eq(c.option_lock(2, "snare_crack", ["snare_guard"]), "")
	var dev := _fresh(1)
	assert_eq(dev.option_lock(5, "snare_crack", []), "", "unlock-all offers everything")
	assert_true(dev.is_unlocked(3))


func test_selection_is_remembered_and_saved_atomically() -> void:
	var c := _fresh()
	c.store_selection("level_02", {"groove": ["groove_straight"]})
	var again := Campaign.load_data(SAVE, 0)
	assert_eq(again.selection_for("level_02"), {"groove": ["groove_straight"]})
	assert_eq(str(again.progress["last_played"]), "level_02")
	assert_false(FileAccess.file_exists(SAVE + ".tmp"))


func test_corrupt_save_is_kept_aside_and_replaced() -> void:
	_fresh()
	var f := FileAccess.open(SAVE, FileAccess.WRITE)
	f.store_string("{not json")
	f.close()
	var c := Campaign.load_data(SAVE, 0)
	assert_true(c.recovered_from_corrupt)
	assert_true(FileAccess.file_exists(SAVE + ".bad"))
	assert_eq(c.progress["cleared"], {})


func test_version_one_save_is_migrated_not_reset() -> void:
	_fresh()
	var v1 := {"version": 1, "cleared": {"level_01": {"clears": 3, "best_accuracy": 0.92, "best_combo": 40, "best_core_hp": 0.8},
		"level_02": {"clears": 1, "best_accuracy": 0.7, "best_combo": 10, "best_core_hp": 0.4}},
		"unlocked_profiles": ["kick_march", "snare_guard", "kick_armour"],
		"loadouts": {"level_03": {"kick_1": "kick_armour", "snare_1": "snare_guard", "kick_2": "kick_march", "bass_1": "bass_reese"}}}
	var f := FileAccess.open(SAVE, FileAccess.WRITE)
	f.store_string(JSON.stringify(v1))
	f.close()
	var c := Campaign.load_data(SAVE, 0)
	assert_eq(c.migrated_from, 1)
	assert_false(c.recovered_from_corrupt)
	assert_eq(int(c.progress["version"]), Campaign.SAVE_VERSION)
	assert_eq(int(c.progress["cleared"]["level_01"]["clears"]), 3, "clears carry over")
	assert_near(float(c.progress["cleared"]["level_01"]["best_accuracy"]), 0.92, 0.001)
	assert_true(c.is_unlocked(3), "mission 3 stays open after the migration")
	assert_eq(c.selection_for("level_03"), {"kick_sound": ["kick_armour"], "snare_sound": ["snare_guard"], "bass_voice": ["bass_reese"]})
	assert_true(FileAccess.file_exists(SAVE + ".v1"), "the old file is kept")
	var reread := Campaign.load_data(SAVE, 0)
	assert_eq(reread.migrated_from, 0, "migrated once, then read as version 2")
	assert_eq(int(reread.progress["cleared"]["level_02"]["clears"]), 1)


func test_migrated_selection_loads_in_the_mission() -> void:
	var v2 := Campaign.migrate_v1({"version": 1, "cleared": {}, "unlocked_profiles": [], "loadouts": {"level_03": {"bass_1": "bass_reese", "kick_1": "kick_heavy"}}})
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/m03_hold_the_line"), {"selection": v2["selections"]["level_03"]})
	assert_eq(loaded["errors"], [])
	var level: Level = loaded["level"]
	assert_eq(level.selection["bass_voice"], ["bass_reese"])
	assert_eq(level.selection["kick_sound"], ["kick_march"], "a sound the mission does not offer falls back to the default")
