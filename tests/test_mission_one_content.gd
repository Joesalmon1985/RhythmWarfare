extends TestCase
## Mission 1 built from the owner's recordings: every combination of its four choices loads with the exact selection,
## a bass sound follows its bass line, pads carry the bound sound names, both teaching lines are there, and perfect
## play wins with every sequence passed and every wave destroyed for every groove and bass line.

const PACK := "m01_first_watch"
const GROOVES := ["groove_half_time", "groove_double_step", "groove_rolling"]
const BASS := {"bass_sub_line": ["bass_sub_bright", "bass_sub_deep", "bass_sub_pure", "bass_sub_wide", "bass_sub_warm"],
	"bass_reese_line": ["bass_reese_dark", "bass_reese_deep", "bass_reese_soft", "bass_reese_round"]}
const MODES := "DDBDBDDBDBDBDDBD"  # D = drums, B = bass
const BACKING := ["acc_hats_driving", "acc_hats_busy", "acc_hats_offbeat"]


func _load(selection: Dictionary = {}, warnings: Array = []) -> Level:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + PACK), {"selection": selection})
	assert_eq(loaded["errors"], [], str(selection))
	warnings.append_array(loaded["warnings"])
	return loaded["level"]


func test_every_combination_loads_with_its_own_stems_and_cues() -> void:
	var seen := {}
	var combos := 0
	for g in GROOVES:
		for b in BASS:
			for v in BASS[b]:
				for a in BACKING:
					var sel := {"groove": [g], "bass": [b], "bass_voice": [v], "accompaniment": [a]}
					var level := _load(sel)
					if level == null:
						continue
					combos += 1
					assert_eq(level.selection, sel, "the selection is kept as made")
					assert_eq(level.stems.size(), 4, "kick, snare, bass and backing stems")
					var key := "|".join(PackedStringArray(level.stems.values()))
					assert_false(seen.has(key), "each combination plays its own set of files")
					seen[key] = true
					for path in level.stems.values():
						assert_true(FileAccess.file_exists(path), path)
					assert_eq(level.placeholder_stems, 0, "nothing is placeholder")
	assert_eq(combos, 81, "3 grooves x 9 bass recordings x 3 backing tracks")


func test_a_bass_sound_follows_its_bass_line() -> void:
	var warnings: Array = []
	var level := _load({"bass": ["bass_reese_line"], "bass_voice": ["bass_sub_deep"]}, warnings)
	assert_eq(level.selection["bass"], ["bass_reese_line"])
	assert_eq(level.selection["bass_voice"], ["bass_reese_dark"], "a Sub recording cannot play the Reese line: the first Reese recording stands in")
	assert_true(warnings.size() > 0, "and the loader says so")
	var other := _load({"bass_voice": ["bass_reese_dark"]})
	assert_eq(other.selection["bass"], ["bass_sub_line"], "the clip pick wins")
	assert_eq(other.selection["bass_voice"], ["bass_sub_deep"], "the default recording fits the default line")
	var choices: Array = level.choices
	var voice: Dictionary = choices[2]
	assert_eq(str(voice["depends_on"]), "bass")
	assert_true(MissionLoader.option_fits(voice, "bass_sub_pure", "bass_sub_line"))
	assert_false(MissionLoader.option_fits(voice, "bass_sub_pure", "bass_reese_line"))
	var picks := {"bass": ["bass_reese_line"], "bass_voice": ["bass_sub_pure"]}
	MissionLoader.fit_dependents(choices, picks, [])
	assert_eq(picks["bass_voice"], ["bass_reese_dark"], "the setup screen's refit gives the same answer")


func test_defaults_cues_pads_and_names() -> void:
	var level := _load()
	assert_eq(level.selection, {"groove": ["groove_half_time"], "bass": ["bass_sub_line"], "bass_voice": ["bass_sub_deep"], "accompaniment": ["acc_hats_driving"]})
	assert_eq(level.duration_ticks, 128 * 3840, "128 bars")
	assert_eq(level.sequences.size(), 32, "four-bar sequences")
	assert_eq(str(level.sequences[0]["reward"]), "pillbox")
	assert_eq(level.sections.size(), 16, "sixteen eight-bar phases")
	var modes := []
	for s in level.sections:
		modes.append(str(s["mode"])[0].to_upper())
	assert_eq("".join(PackedStringArray(modes)), MODES, "four acts of 32 bars: drums and bass alternating")
	assert_eq(level.notes.size(), 10 * 18 + 6 * 12, "10 kicks and 8 snares per drum phase x 10, 12 Sub Line taps x 6")
	var pads := {}
	var bass_pads := {}
	var bass_ticks := []
	var taps := 0
	for n in level.notes:
		pads[int(n["pad"])] = true
		var ph := level.phase_at(int(n["tick"]))
		assert_eq(str(ph["mode"]), "bass" if n["family"] == "bass" else "drums", "only one family is cued per phase")
		if n["family"] == "bass":
			assert_eq(str(n["type"]), "tap", "every Sub Line note is a tap")
			assert_eq(int(n.get("duration_ticks", 0)), 0, "a tap has no tail")
			bass_pads[int(n["pad"])] = true
			bass_ticks.append(int(n["tick"]))
			taps += 1
	var used := pads.keys()
	used.sort()
	assert_eq(used, [1, 2, 3, 4], "kick on pad 1, snare on pad 4, the bass spreads over the pads by pitch")
	assert_true(bass_pads.size() >= 3, "the bass line uses at least three pads (%d)" % bass_pads.size())
	assert_eq(taps, 72, "six bass phases of 12 taps")
	bass_ticks.sort()
	for i in range(1, bass_ticks.size()):
		assert_true(bass_ticks[i] - bass_ticks[i - 1] >= 1440, "consecutive bass cues are at least 1440 ticks apart (%d)" % (bass_ticks[i] - bass_ticks[i - 1]))
	assert_eq(level.voice_name("bound:groove#1:kick"), "Half-Time Kick", "the pad label is the bound sound's name")
	assert_eq(level.voice_name("bound:groove#1:snare"), "Backbeat Snare")
	assert_eq(level.voice_name("bass_voice#1"), "Deep Sub")
	var rolling := _load({"groove": ["groove_rolling"]})
	assert_eq(rolling.voice_name("bound:groove#1:kick"), "Rolling Kick")
	assert_eq(rolling.notes.size(), 10 * 24 + 6 * 12, "16 kicks and 8 snares per drum phase in the Rolling groove")
	assert_eq(level.intros.size(), 2, "the drum intro and the bass intro")
	assert_eq(int(level.intros[1]["bar"]), 16)
	assert_eq(level.intro, "Tap a pad as its ring closes onto it.")


func test_perfect_play_wins_with_every_sequence_and_every_wave_destroyed_for_every_groove_and_line() -> void:
	var harness: Script = load("res://tools/autoplay.gd")
	for g in GROOVES:
		for b in BASS:
			var level := _load({"groove": [g], "bass": [b]})
			if level == null:
				continue
			var m := Match.new()
			m.setup(level)
			var rng := RandomNumberGenerator.new()
			rng.seed = 1
			var r: Dictionary = harness.run_mission(m, level, "perfect", rng)
			var label := "%s + %s" % [g, b]
			assert_eq(r["outcome"], "victory", label)
			assert_eq(r["sequences_passed"], 32, label + " every sequence passes")
			assert_eq(r["built"], 9, label + " three sockets per point: nine pillboxes")
			assert_true(int(r["units"]) >= 15, label + " squads arrive (%d)" % int(r["units"]))
			assert_eq(int(r["villagers_total"]), 10)
			assert_true(int(r["villagers_lost"]) <= 4, label + " most villagers live (%d of %d)" % [int(r["villagers_lost"]), int(r["villagers_total"])])
			var total := 0
			var killed := 0
			for w in r["waves"].values():
				total += int(w["total"])
				killed += int(w["killed"])
				assert_true(float(w["cleared_s"]) >= 0.0, label + " wave cleared")
			assert_eq(killed, total, label + " every enemy destroyed")
			var planned := 0
			for w in level.waves:
				for grp in w["groups"]:
					planned += int(grp["count"])
			assert_eq(level.waves.size(), 25, "25 waves")
			assert_eq(total, planned, label + " the harness saw every planned enemy")
			assert_true(total >= 100, label + " a long fight (%d enemies)" % total)


func test_no_input_loses() -> void:
	var harness: Script = load("res://tools/autoplay.gd")
	var level := _load()
	var m := Match.new()
	m.setup(level)
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	var r: Dictionary = harness.run_mission(m, level, "none", rng)
	assert_eq(r["outcome"], "defeat")
	assert_eq(r["built"], 0)
	assert_eq(r["units"], 0)
	assert_true(float(r["outcome_time_s"]) < level.duration_seconds(), "the barracks falls before the song ends")
