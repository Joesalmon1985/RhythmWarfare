extends TestCase
## The run's save (levels reached on entry, migration from the old chapter save, corrupt files), RunData validation and the clock loop.


func _tmp(name: String) -> String:
	return "user://test_run_%s.json" % name


func _rm(path: String) -> void:
	for p in [path, path + ".tmp", path + ".corrupt"]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)


func test_a_level_is_reached_when_it_is_entered() -> void:
	var path := _tmp("reach")
	_rm(path)
	var p := RunProgress.load_data(path, "user://none.json")
	assert_true(p.is_reached("warehouse"), "the first level is always open")
	assert_false(p.is_reached("mothership"))
	assert_true(p.enter("mothership"), "new")
	assert_false(p.enter("mothership"), "not new the second time")
	var again := RunProgress.load_data(path, "user://none.json")
	assert_true(again.is_reached("mothership"), "saved on entry")
	assert_eq(int(again.data["reached"]["mothership"]["entries"]), 2)
	_rm(path)


func test_the_old_chapter_save_is_read_once_and_never_touched() -> void:
	var old := _tmp("old")
	var path := _tmp("new")
	_rm(old)
	_rm(path)
	var f := FileAccess.open(old, FileAccess.WRITE)
	f.store_string(JSON.stringify({"version": 1, "levels": {"night_one": {"plays": 3}, "hospital": {"plays": 1}, "mental_hospital": {"plays": 0}}}))
	f.close()
	var before := FileAccess.get_file_as_string(old)
	var p := RunProgress.load_data(path, old)
	assert_true(p.is_reached("hospital"))
	assert_false(p.is_reached("ward"), "a chapter that was never played is not carried over")
	var mig: Array = p.migrated.duplicate()
	mig.sort()
	assert_eq(mig, ["hospital", "warehouse"])
	assert_true(p.migration_note().contains("carried over"))
	assert_eq(FileAccess.get_file_as_string(old), before, "the old save is untouched")
	var second := RunProgress.load_data(path, old)
	assert_eq(second.migrated, [], "migrated only once: the new save exists now")
	assert_true(second.is_reached("hospital"))
	_rm(old)
	_rm(path)


func test_an_unreadable_save_is_set_aside() -> void:
	var path := _tmp("bad")
	_rm(path)
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string("{ not json")
	f.close()
	var p := RunProgress.load_data(path, "user://none.json")
	assert_true(p.recovered_from_corrupt)
	assert_true(FileAccess.file_exists(path + ".corrupt"))
	assert_true(p.is_reached("warehouse"))
	_rm(path)


func test_the_clock_loop_is_exactly_64_beats() -> void:
	var s := RunAudio.silent_loop(64, 174)
	assert_eq(s.loop_end, 64 * 3000)
	assert_near(s.get_length(), 64.0 * 60.0 / 174.0, 1e-9, "no rounding in the grid the song clock reads")


func test_run_data_rejects_broken_routes_and_sibling_charts() -> void:
	var good := RunData.load_default()
	assert_eq(good.errors, [])
	assert_eq(good.warnings.filter(func(w: String) -> bool: return w.contains("cannot be reached")), [], "every level is reachable")
	var bad_run: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RunData.RUN_PATH))
	(bad_run["nodes"][1]["next"] as Array).remove_at(1)  # mothership keeps one route
	var rp := "user://test_run_bad_run.json"
	var f := FileAccess.open(rp, FileAccess.WRITE)
	f.store_string(JSON.stringify(bad_run))
	f.close()
	var d := RunData.load_files(rp, RunData.MUSIC_PATH, RunData.PACKS_DIR)
	assert_true(d.errors.any(func(e: String) -> bool: return e.contains("at least two routes")), str(d.errors))
	var bad_music: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RunData.MUSIC_PATH))
	for n in bad_music["nodes"]:
		if n["id"] == "underworld":
			n["chart"] = "lv2_alien_spaceship_v2"  # a sibling with its own chart
	var mp := "user://test_run_bad_music.json"
	f = FileAccess.open(mp, FileAccess.WRITE)
	f.store_string(JSON.stringify(bad_music))
	f.close()
	var d2 := RunData.load_files(RunData.RUN_PATH, mp, RunData.PACKS_DIR)
	assert_true(d2.warnings.any(func(e: String) -> bool: return e.contains("siblings no longer share one chart")), str(d2.warnings))  # siblings may differ: a warning
	DirAccess.remove_absolute(rp)
	DirAccess.remove_absolute(mp)


func test_the_route_map_reaches_all_five_worlds() -> void:
	var d := RunData.load_default()
	var worlds := {}
	for id in d.nodes:
		worlds[d.nodes[id]["world"]] = true
	assert_eq(worlds.keys().size(), 5)
	for w in ["night_one", "mothership", "underworld", "hospital", "mental_hospital"]:
		assert_true(worlds.has(w), w)
	for id in d.nodes:
		assert_true((d.nodes[id]["next"] as Array).size() >= 2, "%s offers at least two arrows" % id)
	assert_eq(d.nodes["hospital_late"]["next"][0]["to"], "hospital_late", "the last depth loops onward")
