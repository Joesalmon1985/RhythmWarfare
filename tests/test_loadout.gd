extends TestCase
## The loadout: resolving a wanted loadout against the library and the unlocks, compatibility per slot, reward cycles,
## and what a loadout does to a mission (cues, stems, gain program, sequence rewards) on the fixture library and pack.

const LIB := "tests/fixtures/library_fixture/index.json"
const PACK := "tests/fixtures/pack_v4"
const PRESETS := "data/campaign/loadouts.json"
const REAL := "songs/library/index.json"


func _index() -> LibraryIndex:
	return LibraryIndex.load_from(TestCase.project_path(LIB))


func _all(idx: LibraryIndex) -> Array:
	return MissionLoader.everything(idx)


func _lo(idx: LibraryIndex, changes: Dictionary = {}) -> Dictionary:
	var d: Dictionary = idx.defaults.duplicate()
	for k in changes:
		d[k] = changes[k]
	return d


func _mission(changes: Dictionary = {}, unlocked: Variant = null, warnings: Array = []) -> Level:
	var idx := _index()
	var opts := {"library": idx, "loadout": _lo(idx, changes)}
	if unlocked != null:
		opts["unlocked"] = unlocked
	var loaded := LevelLoader.load_pack(TestCase.project_path(PACK), opts)
	assert_eq(loaded["errors"], [], str(changes))
	warnings.append_array(loaded["warnings"])
	return loaded["level"]


func test_slots_order() -> void:
	assert_eq(Loadout.SLOTS, ["groove", "fill", "kick_sound", "snare_sound", "bass", "bass_sound", "backing"])


func test_resolve_defaults_and_valid_picks_are_kept() -> void:
	var idx := _index()
	var w: Array = []
	assert_eq(Loadout.resolve(idx, [], {}, w), idx.defaults, "nothing wanted: the defaults")
	assert_eq(w, [], "and no warnings")
	var want := {"groove": "groove_b", "fill": "", "kick_sound": "kick_a", "snare_sound": "snare_a", "bass": "bass_line_2", "bass_sound": "bass_c", "backing": "acc_a"}
	assert_eq(Loadout.resolve(idx, _all(idx), want, w), want)
	assert_eq(w, [])
	var with_fill := {"groove": "groove_a", "fill": "fill_a", "kick_sound": "kick_a", "snare_sound": "snare_b", "bass": "bass_line_1", "bass_sound": "bass_b", "backing": "acc_b"}
	assert_eq(Loadout.resolve(idx, _all(idx), with_fill, w), with_fill, "a fill that plays the picked sounds stays")
	assert_eq(w, [])


func test_resolve_falls_back_with_a_warning_per_slot() -> void:
	var idx := _index()
	var w: Array = []
	var got := Loadout.resolve(idx, _all(idx), _lo(idx, {"bass_sound": "bass_c"}), w)
	assert_eq(got["bass_sound"], "bass_a", "a bass sound the line does not play falls back to the default")
	assert_eq(w.size(), 1)
	assert_contains(w[0], "bass_sound")
	w = []
	got = Loadout.resolve(idx, _all(idx), _lo(idx, {"groove": "no_such_groove"}), w)
	assert_eq(got["groove"], "groove_a")
	assert_eq(w.size(), 1)
	w = []
	got = Loadout.resolve(idx, _all(idx), {"groove": "groove_b", "kick_sound": "kick_b", "snare_sound": "snare_b"}, w)
	assert_eq(got["groove"], "groove_b")
	assert_eq(got["kick_sound"], "kick_a", "groove B only plays kick A: the default fits")
	assert_eq(got["snare_sound"], "snare_a")
	assert_eq(w.size(), 2)
	w = []
	got = Loadout.resolve(idx, _all(idx), {"bass": "bass_line_2", "bass_sound": "bass_a", "backing": "acc_b"}, w)
	assert_eq(got["bass_sound"], "bass_c", "the default bass sound does not fit line 2: the first one that does")
	assert_eq(got["backing"], "acc_a", "the backing in another key falls back to the default")
	assert_eq(w.size(), 2)


func test_a_fill_never_costs_a_chosen_sound() -> void:
	var idx := _index()
	var w: Array = []
	var got := Loadout.resolve(idx, _all(idx), _lo(idx, {"fill": "fill_a", "kick_sound": "kick_b"}), w)
	assert_eq(got["kick_sound"], "kick_b", "the chosen kick sound stays")
	assert_eq(got["fill"], "", "the fill that does not play it goes")
	assert_eq(w.size(), 1)


func test_resolve_honours_unlocks_and_defaults_are_always_unlocked() -> void:
	var idx := _index()
	var w: Array = []
	var got := Loadout.resolve(idx, [], _lo(idx, {"groove": "groove_b"}), w)
	assert_eq(got["groove"], "groove_a", "a locked groove falls back to the default")
	assert_eq(w.size(), 1)
	w = []
	got = Loadout.resolve(idx, ["groove_b"], _lo(idx, {"groove": "groove_b"}), w)
	assert_eq(got["groove"], "groove_b")
	assert_eq(w, [])
	got = Loadout.resolve(idx, [], _lo(idx, {"fill": "fill_a"}), w)
	assert_eq(got["fill"], "", "a locked fill is dropped")
	got = Loadout.resolve(idx, ["fill_a"], _lo(idx, {"fill": "fill_a"}), w)
	assert_eq(got["fill"], "fill_a")
	got = Loadout.resolve(idx, ["kick_b", "snare_b"], _lo(idx, {"kick_sound": "kick_b", "snare_sound": "snare_b"}), [])
	assert_eq(got["kick_sound"], "kick_b")
	assert_eq(got["snare_sound"], "snare_b")


func test_compatibility_per_slot() -> void:
	var idx := _index()
	var d := _lo(idx)
	assert_eq(idx.compatible("groove", d), ["groove_a", "groove_b"])
	assert_eq(idx.compatible("bass", d), ["bass_line_1", "bass_line_2"])
	assert_eq(idx.compatible("kick_sound", d), ["kick_a", "kick_b"])
	assert_eq(idx.compatible("snare_sound", d), ["snare_a", "snare_b"])
	assert_eq(idx.compatible("kick_sound", _lo(idx, {"groove": "groove_b"})), ["kick_a"])
	assert_eq(idx.compatible("snare_sound", _lo(idx, {"groove": "groove_b"})), ["snare_a"])
	assert_eq(idx.compatible("fill", d), ["", "fill_a"])
	assert_eq(idx.compatible("fill", _lo(idx, {"kick_sound": "kick_b"})), [""], "no fill plays Kick B")
	assert_eq(idx.compatible("fill", _lo(idx, {"snare_sound": "snare_b"})), ["", "fill_a"])
	assert_eq(idx.compatible("kick_sound", _lo(idx, {"fill": "fill_a"})), ["kick_a"], "with a fill equipped only the sounds it plays")
	assert_eq(idx.compatible("bass_sound", d), ["bass_a", "bass_b"])
	assert_eq(idx.compatible("bass_sound", _lo(idx, {"bass": "bass_line_2"})), ["bass_c"])
	assert_eq(idx.compatible("backing", d), ["acc_a", "acc_b"], "C# minor line: the C# minor backing and the keyless one")
	assert_eq(idx.compatible("backing", _lo(idx, {"bass": "bass_line_2"})), ["acc_a"], "F minor line: only the keyless one")
	assert_eq(idx.compatible("nonsense", d), [])


func test_is_valid() -> void:
	var idx := _index()
	assert_true(Loadout.is_valid(idx, idx.defaults))
	assert_false(Loadout.is_valid(idx, _lo(idx, {"bass_sound": "bass_c"})))
	assert_false(Loadout.is_valid(idx, _lo(idx, {"fill": "nope"})))
	var short := idx.defaults.duplicate()
	short.erase("backing")
	assert_false(Loadout.is_valid(idx, short), "a slot is missing")


func test_reward_cycles() -> void:
	var idx := _index()
	assert_eq(Loadout.reward_cycle(idx, "kick_a"), ["rifle_squad", "rifle_squad", "grenadier_squad"], "2:1 expands in order")
	assert_eq(Loadout.reward_cycle(idx, "kick_b"), ["pillbox"])
	assert_eq(Loadout.reward_cycle(idx, "snare_b"), ["repair"], "a sound that produces nothing repairs")
	assert_eq(Loadout.reward_cycle(idx, "no_such_sound"), ["repair"])


func test_mission_sequences_follow_the_instruments() -> void:
	var level := _mission()
	assert_eq(level.sequences.size(), 16, "four phases of eight bars in two-bar sequences")
	assert_eq(level.sequence_bars, 2)
	var rewards := []
	for s in level.sequences:
		rewards.append(str(s["reward"]))
	var r := "rifle_squad"
	var g := "grenadier_squad"
	# drum sequences alternate kick (cycle r r g) and snare (g); bass sequences take the bass cycle (r); each cycle advances per use
	assert_eq(rewards, [r, g, r, g, g, g, r, g, r, r, r, r, r, g, g, g])
	for s in level.sequences:
		assert_eq(str(s["mode"]), "bass" if int(s["phase"]) == 2 else "drums")
		assert_eq(int(s["end_tick"]) - int(s["start_tick"]), 2 * 3840)
	var other := _mission({"kick_sound": "kick_b", "snare_sound": "snare_b", "bass_sound": "bass_b"})
	var seen := {}
	for s in other.sequences:
		var k := "%s:%s" % [s["mode"], s["reward"]]
		seen[k] = int(seen.get(k, 0)) + 1
	assert_eq(seen, {"drums:pillbox": 6, "drums:repair": 6, "bass:turret": 4}, "kick B builds pillboxes, snare B repairs, bass B builds turrets")


func test_mission_cues_tile_the_groove_and_the_bass_line() -> void:
	var level := _mission()
	assert_true(level.is_mission())
	assert_eq(level.notes.size(), 3 * 32 + 10, "three drum phases of 16 kicks and 16 snares, one bass phase of 10 cues (8 taps and 2 holds)")
	var first: Dictionary = level.notes[0]
	assert_eq([int(first["tick"]), str(first["family"]), int(first["pad"]), str(first["voice"]), str(first["type"])], [0, "kick", 1, "kick_a", "tap"])
	assert_eq(int(level.notes[1]["tick"]), 960)
	assert_eq(str(level.notes[1]["family"]), "snare")
	assert_eq(int(level.notes[1]["pad"]), 4)
	var prev := -1
	for n in level.notes:
		assert_true(int(n["tick"]) >= prev, "sorted by tick")
		prev = int(n["tick"])
		assert_true(int(n["seq"]) >= 0, "every cue is in a sequence")
		var ph := level.phase_at(int(n["tick"]))
		assert_eq(str(ph["mode"]), "bass" if n["family"] == "bass" else "drums", "cues only in their family's phases")
		assert_near(float(n["time"]), float(n["tick"]) * 60.0 / (174.0 * 960.0), 0.0001)
	var holds := []
	for n in level.notes:
		if n["type"] == "hold":
			holds.append(int(n["tick"]))
			assert_eq(int(n["end_tick"]), int(n["tick"]) + 1920)
	assert_eq(holds, [2 * 30720 + 2 * 3840 + 1920, 2 * 30720 + 5 * 3840 + 1920], "the bass holds of bars 3 and 6 of the bass phase")
	assert_eq(int(level.notes[level.notes.size() - 1]["phase"]), 3)
	var groove_b := _mission({"groove": "groove_b"})
	assert_eq(groove_b.notes.size(), 3 * 16 + 10, "groove B is sparser")


func test_a_fill_replaces_bar_eight_of_every_drum_phase() -> void:
	var level := _mission({"fill": "fill_a"})
	assert_eq(level.loadout["fill"], "fill_a")
	assert_eq(level.notes.size(), 3 * 32 + 10, "the fill has as many cues in bar 8 as the groove")
	for phase_start in [0, 30720, 3 * 30720]:
		var in_bar8 := []
		for n in level.notes:
			if int(n["tick"]) >= phase_start + 7 * 3840 and int(n["tick"]) < phase_start + 8 * 3840:
				in_bar8.append([int(n["tick"]) - phase_start - 7 * 3840, str(n["family"]), int(n["pad"])])
		assert_eq(in_bar8, [[0, "kick", 1], [960, "kick", 1], [1920, "kick", 1], [2880, "snare", 4]], "bar 8 of the phase at %d" % phase_start)
	var bass_bar8 := 0
	for n in level.notes:
		if n["family"] == "bass" and int(n["tick"]) >= 2 * 30720 + 7 * 3840:
			bass_bar8 += 1
	assert_eq(bass_bar8, 1, "a bass phase has no fill")


func test_mission_stems_loops_and_gain_program() -> void:
	var level := _mission()
	assert_eq(level.stems.keys(), ["kick", "snare", "bass", "other"])
	assert_eq(level.stem_family, {"kick": "kick", "snare": "snare", "bass": "bass", "other": "other"})
	for k in level.stems:
		assert_true(FileAccess.file_exists(level.stems[k]), level.stems[k])
		assert_eq(int(level.stem_loop_bars[k]), 8)
	assert_true(str(level.stems["kick"]).ends_with("groove_a__kick__kick_a.wav"))
	assert_true(str(level.stems["bass"]).ends_with("bass_line_1__bass__bass_a.wav"))
	assert_eq(level.gain_program.size(), 16 * 2, "one program per bar")
	assert_eq(level.audible_stems(0), ["kick", "snare", "other"], "drums phase")
	assert_eq(level.audible_stems(7), ["kick", "snare", "other"], "no fill: bar 8 plays the groove")
	assert_eq(level.audible_stems(16), ["bass", "other"], "bass phase")
	assert_eq(level.audible_stems(24), ["kick", "snare", "other"])
	assert_eq(level.audible_stems(999), ["kick", "snare", "other"], "past the end holds the last bar")
	var fill := _mission({"fill": "fill_a"})
	assert_eq(fill.stems.keys(), ["kick", "snare", "fill_kick", "fill_snare", "bass", "other"])
	assert_eq(fill.stem_family["fill_kick"], "kick")
	assert_eq(fill.stem_family["fill_snare"], "snare")
	assert_eq(fill.audible_stems(6), ["kick", "snare", "other"])
	assert_eq(fill.audible_stems(7), ["fill_kick", "fill_snare", "other"], "bar 8: the fill loops replace the groove")
	assert_eq(fill.audible_stems(8), ["kick", "snare", "other"])
	assert_eq(fill.audible_stems(23), ["bass", "other"], "no fill in a bass phase")
	assert_eq(fill.audible_stems(31), ["fill_kick", "fill_snare", "other"])


func test_mission_pads_names_and_unlock_filtering() -> void:
	var level := _mission()
	var drums: Dictionary = level.sections[0]["pads"]
	assert_eq(drums, {"1": {"family": "kick", "ref": "kick_a"}, "4": {"family": "snare", "ref": "snare_a"}})
	var bass: Dictionary = level.sections[2]["pads"]
	assert_eq(bass.keys(), ["1", "2", "3", "4"])
	assert_eq(bass["3"], {"family": "bass", "ref": "bass_a"})
	assert_eq(level.voice_name("kick_a"), "Fixture Kick A")
	assert_eq(level.voice_name("groove_b"), "Fixture Groove B")
	assert_eq(level.title, "Fixture Mission")
	assert_eq(level.waves.size(), 3)
	var w: Array = []
	var locked := _mission({"groove": "groove_b", "fill": "fill_a"}, ["kick_a"], w)
	assert_eq(locked.loadout["groove"], "groove_a", "a locked groove is replaced")
	assert_eq(locked.loadout["fill"], "")
	assert_true(w.size() >= 2, "and the loader says so")
	var open := _mission({"groove": "groove_b"}, ["groove_b"])
	assert_eq(open.loadout["groove"], "groove_b")


func test_old_schema_packs_are_rejected() -> void:
	var dir := "user://test_loadout_old_pack"
	DirAccess.make_dir_recursive_absolute(dir)
	var f := FileAccess.open(dir + "/level.json", FileAccess.WRITE)
	f.store_string(JSON.stringify({"schema_version": 3, "level_id": "old"}))
	f.close()
	var loaded := LevelLoader.load_pack(dir)
	assert_true(loaded["level"] == null)
	assert_contains(loaded["errors"], "rebuild the packs")
	DirAccess.remove_absolute(dir + "/level.json")
	DirAccess.remove_absolute(dir)


func test_missing_library_is_an_error_not_a_crash() -> void:
	var empty := LibraryIndex.load_from(TestCase.project_path("tests/fixtures/none/index.json"))
	var loaded := LevelLoader.load_pack(TestCase.project_path(PACK), {"library": empty})
	assert_true(loaded["level"] == null)
	assert_contains(loaded["errors"], "library")


func test_presets_are_valid_against_the_real_library_when_built() -> void:
	var presets: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(TestCase.project_path(PRESETS)))
	for name in ["default", "village", "heavy"]:
		assert_true(presets.has(name), "preset " + name)
		for slot in Loadout.SLOTS:
			assert_true(presets[name].has(slot), "%s has %s" % [name, slot])
	assert_eq(presets["default"], presets["village"])
	if not FileAccess.file_exists(TestCase.project_path(REAL)):
		print("  note: songs/library/index.json is not built yet; presets are not checked against it")
		return
	var idx := LibraryIndex.load_from(TestCase.project_path(REAL))
	for name in presets:
		if name in ["format", "note"]:
			continue
		assert_true(Loadout.is_valid(idx, presets[name]), "preset %s is a valid loadout in the real library" % name)
	assert_eq(presets["default"], idx.defaults, "the default preset is the library's default loadout")
