extends TestCase
## Mission 1 (the village) on the loop library: the form, the pads and names of the default loadout, the village fight
## under perfect play for the default and two other loadouts, and no input losing.

const PACK := "m01_first_watch"
const MODES := "DDBDBDDBDBDBDDBD"  # D = drums, B = bass


func _load(loadout: Dictionary = {}) -> Level:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + PACK), {"loadout": loadout})
	assert_eq(loaded["errors"], [], str(loadout))
	return loaded["level"]


func _run(level: Level, policy: String) -> Dictionary:
	var harness: Script = load("res://tools/autoplay.gd")
	var m := Match.new()
	m.setup(level)
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	return harness.run_mission(m, level, policy, rng)


func test_form_pads_names_and_intros() -> void:
	var level := _load()
	if level == null:
		return
	var idx := LibraryIndex.load_default()
	assert_eq(level.duration_ticks, 128 * 3840, "128 bars")
	assert_eq(level.sections.size(), 16, "sixteen eight-bar phases")
	var modes := []
	for s in level.sections:
		modes.append(str(s["mode"])[0].to_upper())
	assert_eq("".join(PackedStringArray(modes)), MODES, "four acts of 32 bars: drums and bass alternating")
	assert_eq(level.sections[0]["pads"], {"1": {"family": "kick", "ref": "kick_half_time"}, "4": {"family": "snare", "ref": "snare_backbeat"}})
	assert_eq(level.sections[2]["pads"]["1"], {"family": "bass", "ref": "bass_sub_deep"}, "bass phases play the bass sound on every pad")
	assert_eq(level.voice_name("kick_half_time"), idx.name("kick_half_time"), "the pad label is the sound's name")
	assert_eq(level.voice_name("bass_sub_deep"), idx.name("bass_sub_deep"))
	assert_true(level.intros.size() >= 1, "the teaching lines are there")
	assert_eq(level.intro, "Tap a pad as its note lands on it.")
	assert_eq(level.waves.size(), 25, "25 waves")
	assert_eq(int(level.base.get("civilians", 0)), 10, "ten villagers")
	assert_eq(level.battlefield, "village_01")
	assert_eq(level.sequences.size(), 64)


func test_perfect_play_wins_the_village_for_three_loadouts() -> void:
	var heavy: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(TestCase.project_path("data/campaign/loadouts.json")))["heavy"]
	var loadouts := {"default": {}, "rolling + reese": {"groove": "groove_rolling", "bass": "bass_reese_line"}, "heavy": heavy}
	for label in loadouts:
		var level := _load(loadouts[label])
		if level == null:
			continue
		var r := _run(level, "perfect")
		assert_eq(r["outcome"], "victory", label)
		assert_eq(r["sequences_passed"], 64, label + " every sequence passes")
		assert_eq(int(r["villagers_total"]), 10)
		assert_true(int(r["villagers_lost"]) <= 4, label + " most villagers live (%d of %d)" % [int(r["villagers_lost"]), int(r["villagers_total"])])
		var total := 0
		var killed := 0
		for w in r["waves"].values():
			total += int(w["total"])
			killed += int(w["killed"])
		# balance (3 Nov 2026, night): the default loadout destroys at least 90% of the 278 enemies; the other loadouts
		# send fewer vehicles and more infantry into repairs and are only held to a clear majority (heavy: about 77 to 85%)
		var share := 0.9 if label == "default" else 0.6
		assert_true(float(killed) >= share * float(total), label + " most enemies destroyed (%d of %d)" % [killed, total])
		var planned := 0
		for w in level.waves:
			for grp in w["groups"]:
				planned += int(grp["count"])
		assert_eq(total, planned, label + " the harness saw every planned enemy")
		assert_true(total >= 100, label + " a long fight (%d enemies)" % total)


func test_no_input_loses() -> void:
	var level := _load()
	if level == null:
		return
	var r := _run(level, "none")
	assert_eq(r["outcome"], "defeat")
	assert_eq(r["built"], 0)
	assert_eq(r["units"], 0)
	assert_true(float(r["outcome_time_s"]) < level.duration_seconds(), "the barracks falls before the song ends")
