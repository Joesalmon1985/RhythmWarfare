extends TestCase
## The run save, version 3 (CONTRACTS.md 6, hook H6.1): version 2 and 3 files load (RaveSave.migrate fills the bedsit raves' keys), anything else is set aside as
## before; a new run resets the per-run keys (facing north, no rave, every puzzle unsolved) and keeps the race records; an activity's flags and a race land in the save.

const TMP := "user://test_run_progress_v3.json"


func _rm(p: String) -> void:
	for f in [p, p + ".corrupt", p + ".tmp"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)


func _write_fixture(name: String) -> void:
	_rm(TMP)
	var f := FileAccess.open(TMP, FileAccess.WRITE)
	f.store_string(FileAccess.get_file_as_string(ContractShapes.FIXTURES + name))
	f.close()


func _disk() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(TMP))


func test_a_version_2_save_loads_migrates_and_is_written_back_as_version_3() -> void:
	_write_fixture("save_v2.json")
	var p := RunProgress.load_data(TMP, "user://none.json")
	assert_false(p.recovered_from_corrupt, "a version 2 save is not set aside")
	assert_eq(p.loaded_version, 2)
	assert_eq(int(p.data["version"]), 3, "migrated in memory")
	assert_true(ContractShapes.save_v3(p.data).is_empty(), "the contract's shape: %s" % str(ContractShapes.save_v3(p.data)))
	assert_eq(p.bedsit_facing(), "N")
	assert_eq(p.rave_theme(), "")
	for th in RaveSave.THEMES:
		for pz in RaveSave.PUZZLES:
			assert_false(p.puzzle_done(th, pz), "%s %s unsolved" % [th, pz])
	assert_true(p.is_reached("warehouse") and int(p.data["runs"]) == 4 and p.flags.has("keep:wh_saw_star"), "version 2's progress is kept")
	assert_eq(p.paths, {"gospel": {"reached": ["galilee"], "endings": []}})
	assert_eq(p.wallet.balance_pence(), 2000)
	assert_eq(int(p.data["seed"]), 12345)
	assert_eq(int(_disk()["version"]), 2, "the file is untouched until the next save")
	p.save()
	var d := _disk()
	assert_eq(int(d["version"]), 3, "written back as version 3")
	assert_true(ContractShapes.save_v3(d).is_empty())
	var again := RunProgress.load_data(TMP, "user://none.json")
	assert_eq(again.loaded_version, 3)
	assert_eq(again.rave_fixed, [], "nothing more to migrate")
	_rm(TMP)


func test_a_version_3_save_keeps_its_raves_and_a_new_run_keeps_only_the_race_records() -> void:
	_write_fixture("save_v3.json")
	var p := RunProgress.load_data(TMP, "user://none.json")
	assert_false(p.recovered_from_corrupt)
	assert_eq(p.loaded_version, 3)
	assert_eq(p.rave_fixed, [], "a whole version 3 save needs nothing")
	assert_eq(p.bedsit_facing(), "E")
	assert_eq(p.rave_theme(), "space")
	assert_true(p.puzzle_done("space", "bass_fixed") and p.puzzle_done("space", "cloakroom_done") and not p.puzzle_done("space", "bar_done"))
	p.run_started()
	var d := _disk()
	assert_eq(int(d["version"]), 3)
	assert_eq(str(d["bedsit_facing"]), "N", "a new run faces north")
	assert_eq(str(d["rave_theme"]), "", "in no rave")
	for th in RaveSave.THEMES:
		for pz in RaveSave.PUZZLES:
			assert_false(bool(d["raves"][th][pz]), "%s %s cleared by the new run" % [th, pz])
	assert_eq(int(d["raves"]["space"]["race"]["wins"]), 2, "race records are kept across runs (ruling 37)")
	assert_eq(int(d["raves"]["space"]["race"]["runs"]), 3)
	assert_near(float(d["raves"]["space"]["race"]["best"]), 71.5, 1e-6)
	assert_near(float(d["raves"]["dinos"]["race"]["best"]), 88.0, 1e-6)
	assert_eq(int(d["runs"]), 6, "the run count goes on")
	assert_true(p.flags.has("keep:wh_saw_star"), "discoveries are kept")
	_rm(TMP)


func test_activity_flags_races_facing_and_theme_are_saved() -> void:
	_rm(TMP)
	var p := RunProgress.load_data(TMP, "user://none.json")
	assert_eq(int(p.data["version"]), 3, "a fresh save is version 3")
	assert_true(ContractShapes.save_v3(p.data).is_empty())
	assert_true(p.set_bedsit_facing("W"))
	assert_false(p.set_bedsit_facing("X"), "only N, E, S, W")
	assert_true(p.set_rave_theme("transport"))
	assert_false(p.set_rave_theme("disco"))
	assert_true(p.apply_activity_flag("rave.transport.bar_done"))
	assert_false(p.apply_activity_flag("rave.transport.bar_done"), "once")
	assert_false(p.apply_activity_flag("rave.disco.bar_done"), "an unknown theme sets nothing")
	assert_true(p.apply_activity_flag("cloak_seen"), "any other name is an ordinary run flag")
	assert_true(p.has_flag("cloak_seen"))
	p.record_race("transport", true, 66.0)
	p.record_race("transport", false, 70.0)
	var q := RunProgress.load_data(TMP, "user://none.json")
	assert_eq(q.bedsit_facing(), "W")
	assert_eq(q.rave_theme(), "transport")
	assert_true(q.puzzle_done("transport", "bar_done"))
	assert_false(q.has_flag("cloak_seen"), "a run flag is not saved")
	assert_eq(int(q.data["raves"]["transport"]["race"]["wins"]), 1)
	assert_eq(int(q.data["raves"]["transport"]["race"]["runs"]), 2)
	assert_near(float(q.data["raves"]["transport"]["race"]["best"]), 66.0, 1e-6)
	_rm(TMP)


func test_other_versions_are_still_set_aside() -> void:
	for v in [1, 4]:
		_rm(TMP)
		var f := FileAccess.open(TMP, FileAccess.WRITE)
		f.store_string(JSON.stringify({"version": v, "reached": {}, "runs": 1}))
		f.close()
		var p := RunProgress.load_data(TMP, "user://none.json")
		assert_true(p.recovered_from_corrupt, "version %d is set aside" % v)
		assert_true(FileAccess.file_exists(TMP + ".corrupt"))
		assert_eq(int(p.data["version"]), 3, "and a fresh version 3 save starts")
	_rm(TMP)
