extends TestCase
## Campaign progress (save version 3): the ladder, library item unlocks, the one global loadout, results, the unlock-all
## switch, a corrupt save and the migrations of version 1 (instrument loadouts) and version 2 (per-mission selections).

const SAVE := "user://test_campaign_save.json"


func _fresh(unlock: int = 0) -> Campaign:
	for suffix in ["", ".bad", ".v1", ".v2", ".tmp"]:
		if FileAccess.file_exists(SAVE + suffix):
			DirAccess.remove_absolute(SAVE + suffix)
	return Campaign.load_data(SAVE, unlock)


func _win(level_id: String, number: int) -> Dictionary:
	return {"mode": "mission", "outcome": "victory", "battle": true, "play_mode": "campaign", "progression": true, "level_id": level_id,
		"campaign_level": number, "accuracy": 0.9, "sequences": 8, "sequences_passed": 7, "best_combo": 12,
		"objective_hp": {"command_core": {"hp": 30000, "max": 60000}}}


func _library_built() -> bool:
	return not LibraryIndex.load_default().is_empty()


func _write_save(text: String) -> void:
	var f := FileAccess.open(SAVE, FileAccess.WRITE)
	f.store_string(text)
	f.close()


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


func test_the_default_loadout_ships_in_mission_one_and_no_id_is_listed_twice() -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(Campaign.DATA_PATH))
	var presets: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(TestCase.project_path("data/campaign/loadouts.json")))
	var first: Array = data["levels"][0]["new_options"]
	for slot in Loadout.SLOTS:
		var id := str(presets["default"][slot])
		if not id.is_empty():
			assert_true(first.has(id), "mission 1 lists the default %s" % id)
	var seen := {}
	for l in data["levels"]:
		for id in l["new_options"]:
			assert_false(seen.has(id), "%s is listed by one mission only" % id)
			seen[id] = int(l["number"])


func test_unlocked_items_follow_the_ladder() -> void:
	var c := _fresh()
	var first: Array = c.level_data(1)["new_options"]
	var got := c.unlocked_items()
	assert_eq(got.size(), first.size(), "only mission 1's items at the start")
	for id in first:
		assert_true(got.has(id))
	assert_false(got.has("groove_push"), "mission 2's items are locked")
	c.record_result(_win("level_01", 1))
	got = c.unlocked_items()
	assert_true(got.has("groove_push") and got.has("snare_crack"), "clearing mission 1 opens mission 2's items")
	assert_false(got.has("bass_patrol"), "but not mission 3's")
	var dev := _fresh(1)
	if _library_built():
		var index := LibraryIndex.load_default()
		assert_eq(dev.unlocked_items().size(), index.clips.size() + index.sounds.size(), "unlock-all offers the whole library")
	else:
		print("  note: the library is not built; the unlock-all list is not compared with it")


func test_item_lock_says_what_unlocks_an_item() -> void:
	var c := _fresh()
	assert_eq(c.item_lock("kick_half_time"), "", "mission 1's items are open")
	assert_eq(c.item_lock("groove_half_time"), "")
	assert_eq(c.item_lock("snare_crack"), "Clear First Watch to unlock")
	assert_eq(c.item_lock("bass_patrol"), "Clear Second Pulse to unlock")
	assert_eq(c.item_lock("not_in_the_campaign_at_all"), "Not in the campaign")
	c.record_result(_win("level_01", 1))
	assert_eq(c.item_lock("snare_crack"), "")
	assert_eq(c.item_lock("bass_patrol"), "Clear Second Pulse to unlock", "one clear opens one mission's items")
	var dev := _fresh(1)
	assert_eq(dev.item_lock("bass_hollow"), "", "unlock-all offers everything")


func test_loadout_is_global_remembered_and_saved_atomically() -> void:
	var c := _fresh()
	var picked := {"groove": "groove_half_time", "fill": "", "kick_sound": "kick_half_time", "snare_sound": "snare_backbeat", "bass": "bass_sub_line", "bass_sound": "bass_sub_pure", "backing": "acc_hats_busy"}
	c.store_loadout(picked)
	var again := Campaign.load_data(SAVE, 0)
	assert_eq(again.progress["loadout"], picked, "stored as made")
	assert_eq(int(again.progress["version"]), 3)
	assert_false(FileAccess.file_exists(SAVE + ".tmp"))
	assert_false(again.progress.has("selections"), "no per-mission selections any more")
	if not _library_built():
		print("  note: the library is not built; the resolved loadout is not checked")
		return
	assert_eq(again.loadout(), picked, "a valid, unlocked loadout reads back unchanged")
	var locked := _fresh()
	locked.store_loadout({"groove": "groove_twostep", "fill": "fill_snare_run", "kick_sound": "kick_siege", "snare_sound": "snare_clap", "bass": "bass_octaves", "bass_sound": "bass_command", "backing": "acc_iron"})
	var w: Array = []
	assert_eq(locked.loadout(w), LibraryIndex.load_default().defaults, "locked picks fall back to the defaults on read")
	assert_true(w.size() > 0, "and say so")
	var dev := _fresh(1)
	dev.store_loadout(locked.progress["loadout"])
	assert_eq(dev.loadout()["groove"], "groove_twostep", "unlock-all lets every pick stand")
	assert_eq(_fresh().loadout(), LibraryIndex.load_default().defaults, "a fresh save plays the defaults")


func test_corrupt_save_is_kept_aside_and_replaced() -> void:
	_fresh()
	_write_save("{not json")
	var c := Campaign.load_data(SAVE, 0)
	assert_true(c.recovered_from_corrupt)
	assert_true(FileAccess.file_exists(SAVE + ".bad"))
	assert_eq(c.progress["cleared"], {})


func test_version_two_save_keeps_its_clears_and_gets_the_default_loadout() -> void:
	_fresh()
	_write_save(FileAccess.get_file_as_string(TestCase.project_path("tests/fixtures/save_v2.json")))
	var c := Campaign.load_data(SAVE, 0)
	assert_eq(c.migrated_from, 2)
	assert_false(c.recovered_from_corrupt)
	assert_eq(int(c.progress["version"]), 3)
	assert_eq(int(c.progress["cleared"]["level_01"]["clears"]), 4, "clears carry over")
	assert_near(float(c.progress["cleared"]["level_02"]["best_accuracy"]), 0.74, 0.001)
	assert_eq(str(c.progress["last_played"]), "level_02")
	assert_false(c.progress.has("selections"), "the per-mission selections are dropped")
	assert_eq(c.progress["loadout"], LibraryIndex.load_default().defaults, "the loadout starts as the defaults")
	assert_true(c.is_unlocked(3), "mission 3 stays open")
	assert_true(FileAccess.file_exists(SAVE + ".v2"), "the old file is kept")
	var reread := Campaign.load_data(SAVE, 0)
	assert_eq(reread.migrated_from, 0, "migrated once, then read as version 3")
	assert_eq(int(reread.progress["cleared"]["level_02"]["clears"]), 1)


func test_version_one_save_is_migrated_through_both_steps() -> void:
	_fresh()
	var v1 := {"version": 1, "cleared": {"level_01": {"clears": 3, "best_accuracy": 0.92, "best_combo": 40, "best_core_hp": 0.8},
		"level_02": {"clears": 1, "best_accuracy": 0.7, "best_combo": 10, "best_core_hp": 0.4}},
		"unlocked_profiles": ["kick_march", "snare_guard", "kick_armour"],
		"loadouts": {"level_03": {"kick_1": "kick_armour", "snare_1": "snare_guard", "kick_2": "kick_march", "bass_1": "bass_reese"}}}
	_write_save(JSON.stringify(v1))
	var c := Campaign.load_data(SAVE, 0)
	assert_eq(c.migrated_from, 1)
	assert_false(c.recovered_from_corrupt)
	assert_eq(int(c.progress["version"]), Campaign.SAVE_VERSION)
	assert_eq(int(c.progress["cleared"]["level_01"]["clears"]), 3, "clears carry over")
	assert_near(float(c.progress["cleared"]["level_01"]["best_accuracy"]), 0.92, 0.001)
	assert_true(c.is_unlocked(3), "mission 3 stays open after the migration")
	assert_eq(c.progress["loadout"], LibraryIndex.load_default().defaults)
	assert_false(c.progress.has("selections"))
	assert_true(FileAccess.file_exists(SAVE + ".v1"), "the old file is kept")
	var reread := Campaign.load_data(SAVE, 0)
	assert_eq(reread.migrated_from, 0)
	assert_eq(int(reread.progress["cleared"]["level_02"]["clears"]), 1)
