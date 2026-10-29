extends TestCase
## Balance guard rails for the three shipped levels, run through the same harness as tools/balance.sh (one seed each;
## the full seeds 1-3 tables are in docs/BALANCE.md). Acceptance: perfect play survives, no input loses.


func _run(pack: String, chart: String, policy: String, seed: int) -> Dictionary:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + pack), {"chart_id": chart})
	assert_eq(loaded["errors"], [])
	var level: Level = loaded["level"]
	level.seed = level.seed * 10 + seed
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var m := Match.new()
	m.setup(level)
	var harness: Script = load("res://tools/autoplay.gd")
	return harness.run(m, level, policy, rng)


func test_level_one_perfect_survives_and_no_input_loses() -> void:
	var perfect := _run("first_watch", "level_01.campaign", "perfect", 1)
	assert_eq(perfect["outcome"], "victory")
	assert_eq(perfect["reason"], "survived")
	assert_true(float(perfect["objective_hp"]["command_core"]["hp"]) > 0.5 * float(perfect["objective_hp"]["command_core"]["max"]), "the core is healthy")
	assert_eq(perfect["groups"], 64)
	var none := _run("first_watch", "level_01.campaign", "none", 1)
	assert_eq(none["outcome"], "defeat")
	assert_eq(none["reason"], "objective_destroyed:command_core")
	assert_true(none["outcome_time_s"] < 44.0, "lost before the song ends")


func test_levels_two_and_three_no_input_loses_perfect_survives() -> void:
	for spec in [["second_pulse", "level_02.campaign"], ["hold_the_line", "level_03.campaign"]]:
		var none := _run(spec[0], spec[1], "none", 2)
		assert_eq(none["outcome"], "defeat", spec[0] + " no input")
		var perfect := _run(spec[0], spec[1], "perfect", 2)
		assert_eq(perfect["outcome"], "victory", spec[0] + " perfect")
		assert_true(perfect["accuracy"] == 1.0)


func test_waves_in_the_packs_match_the_tuned_wave_files() -> void:
	for n in [1, 2, 3]:
		var file: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/campaign/waves/level_0%d.json" % n))
		var pack: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(TestCase.project_path("songs/%s/level.json" % ["first_watch", "second_pulse", "hold_the_line"][n - 1])))
		assert_eq(pack["waves"].size(), file["waves"].size())
		assert_eq(JSON.stringify(pack["waves"]), JSON.stringify(file["waves"]), "level %d waves are the tuned ones (rerun build_defense_pack.py --waves-only)" % n)
		assert_eq(JSON.stringify(pack["rules"]), JSON.stringify(file["rules"]))
