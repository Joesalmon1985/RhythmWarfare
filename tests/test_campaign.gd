extends TestCase
## Campaign progress: first clears, unlocks, replays, practice, corrupt saves and loadouts.

const PATH := "user://test_campaign.json"


func _clean() -> void:
	for suffix in ["", ".bad", ".tmp"]:
		if FileAccess.file_exists(PATH + suffix):
			DirAccess.remove_absolute(PATH + suffix)


func _win(level_id: String, accuracy := 0.9, core := 0.8) -> Dictionary:
	return {"mode": "defense", "progression": true, "play_mode": "campaign", "battle": true, "outcome": "victory", "level_id": level_id,
		"accuracy": accuracy, "best_combo": 30, "objective_hp": {"command_core": {"hp": int(core * 1000), "max": 1000}}}


func test_fresh_state_only_level_one_open() -> void:
	_clean()
	var c := Campaign.load_data(PATH, 0)
	assert_true(c.is_unlocked(1))
	assert_false(c.is_unlocked(2))
	assert_false(c.is_unlocked(3))
	assert_eq(c.levels.size(), 10)
	assert_eq(c.caps, {"kick": 2.0, "snare": 2.0, "bass": 3.0})
	assert_true(c.is_playable(3) and not c.is_playable(4))
	assert_true(c.unlocked_profiles().has("kick_march"))
	assert_true(c.unlocked_profiles().has("snare_guard"))
	assert_false(c.unlocked_profiles().has("kick_armour"), "level 2's profile comes with level 2")
	assert_false(FileAccess.file_exists(PATH), "nothing is written until something is cleared")


func test_first_clear_unlocks_next_level_and_its_profiles_and_persists() -> void:
	_clean()
	var c := Campaign.load_data(PATH, 0)
	var r := c.record_result(_win("level_01"))
	assert_true(r["first_clear"])
	assert_eq(r["unlocked_level"], 2)
	assert_eq(r["unlocked_title"], "Second Pulse")
	assert_eq(r["new_profiles"], ["kick_armour"])
	assert_true(r["saved"])
	assert_true(c.is_unlocked(2))
	assert_true(c.unlocked_profiles().has("kick_armour"))
	assert_false(c.is_unlocked(3))
	assert_false(FileAccess.file_exists(PATH + ".tmp"), "the temp file is moved into place")
	var again := Campaign.load_data(PATH, 0)
	assert_true(again.is_cleared("level_01"))
	assert_true(again.is_unlocked(2))
	assert_true(again.unlocked_profiles().has("kick_armour"))
	assert_false(again.recovered_from_corrupt)
	var r2 := c.record_result(_win("level_02"))
	assert_eq(r2["unlocked_level"], 3)
	assert_eq(r2["new_profiles"], ["bass_patrol"])
	_clean()


func test_replays_never_reset_and_only_improve_bests() -> void:
	_clean()
	var c := Campaign.load_data(PATH, 0)
	c.record_result(_win("level_01", 0.9, 0.8))
	c.record_result(_win("level_02", 0.8, 0.5))
	var replay := c.record_result(_win("level_01", 0.7, 0.4))
	assert_false(replay["first_clear"])
	assert_eq(replay["unlocked_level"], 0, "a replay unlocks nothing new")
	assert_eq(replay["new_profiles"], [])
	var rec: Dictionary = c.progress["cleared"]["level_01"]
	assert_eq(int(rec["clears"]), 2)
	assert_near(float(rec["best_accuracy"]), 0.9, 0.0001)
	assert_near(float(rec["best_core_hp"]), 0.8, 0.0001)
	c.record_result(_win("level_01", 0.95, 0.9))
	assert_near(float(c.progress["cleared"]["level_01"]["best_accuracy"]), 0.95, 0.0001)
	# a defeat on a cleared level changes nothing
	var lost := _win("level_01")
	lost["outcome"] = "defeat"
	assert_true(c.record_result(lost).is_empty())
	assert_true(c.is_cleared("level_01") and c.is_unlocked(2) and c.is_unlocked(3))
	assert_true(c.unlocked_profiles().has("bass_patrol"))
	_clean()


func test_practice_and_rhythm_only_runs_write_nothing() -> void:
	_clean()
	var c := Campaign.load_data(PATH, 0)
	var practice := _win("level_02")
	practice["progression"] = false
	practice["play_mode"] = "practice"
	assert_true(c.record_result(practice).is_empty())
	var rhythm := _win("level_01")
	rhythm["battle"] = false
	rhythm["outcome"] = "complete"
	assert_true(c.record_result(rhythm).is_empty())
	var rhythm_win := _win("level_01")
	rhythm_win["battle"] = false
	assert_true(c.record_result(rhythm_win).is_empty(), "no battle, no clear")
	var wrong_mode := _win("level_01")
	wrong_mode["play_mode"] = "practice"
	assert_true(c.record_result(wrong_mode).is_empty())
	assert_false(c.is_cleared("level_01"))
	assert_false(FileAccess.file_exists(PATH), "no save file appeared")
	_clean()


func test_corrupt_save_is_kept_aside_and_replaced() -> void:
	_clean()
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	f.store_string("{ this is not json")
	f.close()
	var c := Campaign.load_data(PATH, 0)
	assert_true(c.recovered_from_corrupt)
	assert_true(FileAccess.file_exists(PATH + ".bad"), "the damaged file is kept")
	assert_false(FileAccess.file_exists(PATH))
	assert_true(c.is_unlocked(1) and not c.is_unlocked(2))
	assert_true(c.record_result(_win("level_01"))["saved"])
	assert_false(Campaign.load_data(PATH, 0).recovered_from_corrupt)
	# a well-formed file of the wrong shape is also treated as corrupt
	_clean()
	f = FileAccess.open(PATH, FileAccess.WRITE)
	f.store_string('{"version": 1, "cleared": 5}')
	f.close()
	assert_true(Campaign.load_data(PATH, 0).recovered_from_corrupt)
	_clean()


func test_loadouts_are_stored_per_level_and_validated() -> void:
	_clean()
	var c := Campaign.load_data(PATH, 0)
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/hold_the_line"))
	var level: Level = loaded["level"]
	var defaults := c.loadout_for(level.level_id, level.loadout_default, level.loadout_active_slots)
	assert_eq(defaults, {"kick_1": "kick_march", "kick_2": "kick_armour", "snare_1": "snare_guard", "bass_1": "bass_patrol"})
	# profiles that are not unlocked yet cannot be used
	assert_contains(c.validate_loadout(level, defaults), "locked")
	c.record_result(_win("level_01"))
	c.record_result(_win("level_02"))
	assert_eq(c.validate_loadout(level, defaults), [], "after two clears the default loadout is complete")
	# duplicate profile within a family
	var dup := defaults.duplicate()
	dup["kick_2"] = "kick_march"
	assert_contains(c.validate_loadout(level, dup), "equipped twice")
	# wrong family
	var wrong := defaults.duplicate()
	wrong["bass_1"] = "snare_guard"
	assert_contains(c.validate_loadout(level, wrong), "takes a bass instrument")
	# a required slot may not be left empty (the chart cannot be shortened by removing a part)
	var missing := defaults.duplicate()
	missing.erase("snare_1")
	assert_contains(c.validate_loadout(level, missing), "required slot snare_1")
	# an unlocked profile with no render for this song is rejected with its reason
	c.record_result(_win("level_03"))
	var norender := defaults.duplicate()
	norender["snare_1"] = "snare_crack"
	assert_contains(c.validate_loadout(level, norender), "no render")
	# a stored loadout comes back from disk, and a stored locked profile falls back to the default
	c.store_loadout(level.level_id, {"kick_1": "kick_armour", "kick_2": "kick_march", "snare_1": "snare_guard", "bass_1": "bass_patrol"})
	var reloaded := Campaign.load_data(PATH, 0)
	assert_eq(reloaded.loadout_for(level.level_id, level.loadout_default, level.loadout_active_slots)["kick_1"], "kick_armour")
	reloaded.progress["loadouts"][level.level_id]["bass_1"] = "bass_command"
	assert_eq(reloaded.loadout_for(level.level_id, level.loadout_default, level.loadout_active_slots)["bass_1"], "bass_patrol")
	_clean()


func test_loader_applies_the_chosen_loadout_to_the_stems() -> void:
	var path := TestCase.project_path("songs/second_pulse")
	var swapped := LevelLoader.load_pack(path, {"loadout": {"kick_1": "kick_armour"}})
	assert_eq(swapped["errors"], [])
	var level: Level = swapped["level"]
	assert_eq(level.loadout["kick_1"], "kick_armour")
	assert_true(str(level.stems["kick_1"]).contains("kick_1__kick_armour"))
	assert_true(str(level.stems["kick_2"]).contains("kick_2__kick_armour"))
	var bad := LevelLoader.load_pack(path, {"loadout": {"snare_1": "snare_crack"}})
	assert_contains(bad["errors"], "no render")
	var bad_slot := LevelLoader.load_pack(path, {"loadout": {"bass_1": "bass_patrol"}})
	assert_contains(bad_slot["errors"], "does not use")


func test_unlock_all_opens_levels_and_profiles_per_level_without_touching_the_save() -> void:
	_clean()
	var c := Campaign.load_data(PATH, 1)
	assert_true(c.unlock_all)
	assert_true(c.is_unlocked(1) and c.is_unlocked(2) and c.is_unlocked(3))
	assert_false(c.is_unlocked(4), "unplayable levels stay closed")
	assert_true(c.unlocked_profiles(1).has("snare_guard") and not c.unlocked_profiles(1).has("kick_armour"), "level 1 offers only level 1 profiles")
	assert_true(c.unlocked_profiles(2).has("kick_armour") and not c.unlocked_profiles(2).has("bass_patrol"))
	assert_true(c.unlocked_profiles(3).has("bass_patrol"))
	assert_false(c.progress["unlocked_profiles"].has("bass_patrol"), "the stored unlocks do not follow the switch")
	var level: Level = LevelLoader.load_pack(TestCase.project_path("songs/hold_the_line"))["level"]
	assert_eq(c.validate_loadout(level, level.loadout_default), [], "the level 3 default loadout is valid straight away")
	# clears and bests still save
	var r := c.record_result(_win("level_03"))
	assert_true(r["saved"])
	assert_true(Campaign.load_data(PATH, 0).is_cleared("level_03"))
	assert_false(Campaign.load_data(PATH, 0).is_unlocked(2), "with the switch off the ladder is unchanged")
	_clean()
	var off := Campaign.load_data(PATH, 0)
	assert_false(off.unlock_all)
	assert_false(off.is_unlocked(2))
