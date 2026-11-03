extends TestCase
## Schema 4 missions on the real packs and library: loading with a loadout, cues on pads, sequences, rewards scheduled
## through the simulation. (tests/test_loadout.gd checks the loader's rules on the fixture library.)


func _load(pack: String, loadout: Dictionary = {}) -> Level:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + pack), {"loadout": loadout})
	assert_eq(loaded["errors"], [], pack)
	return loaded["level"]


## Plays every cue at its exact time (holds to their tail) through Match.advance in 1/60 s frames.
func _play(m: Match, level: Level, hit: Callable) -> void:
	var t := 0.0
	var next := 0
	var holding := {}
	while m.outcome.is_empty() and t < level.duration_seconds() + 0.5:
		for pad in holding.keys():
			if t >= holding[pad]:
				m.release(pad, holding[pad], 1)
				holding.erase(pad)
		while next < level.notes.size() and float(level.notes[next]["time"]) <= t:
			var n: Dictionary = level.notes[next]
			if hit.call(next, n):
				m.press(int(n["pad"]), float(n["time"]), 1)
				if n["type"] == "hold":
					holding[int(n["pad"])] = float(n["end_time"])
			next += 1
		for pad in holding.keys():
			if t >= holding[pad]:
				m.release(pad, holding[pad], 1)
				holding.erase(pad)
		m.advance(t)
		t += 1.0 / 60.0


func test_mission_one_loads_with_the_default_loadout() -> void:
	var idx := LibraryIndex.load_default()
	assert_false(idx.is_empty(), "the loop library is built (python tools/content/build.py)")
	var level := _load("m01_first_watch")
	if level == null:
		return
	assert_true(level.is_mission())
	assert_eq(level.loadout, idx.defaults, "no loadout asked: the library defaults")
	assert_eq(level.duration_ticks, 128 * 3840, "128 bars")
	assert_eq(level.sections.size(), 16, "sixteen eight-bar phases")
	assert_eq(level.sequences.size(), 64, "128 bars in two-bar sequences")
	assert_eq(level.sequence_bars, 2)
	var drum_phases := 0
	var bass_phases := 0
	for s in level.sections:
		if s["mode"] == "drums":
			drum_phases += 1
		else:
			bass_phases += 1
	var per_drum_phase: int = idx.cues("groove_half_time", "kick").size() + idx.cues("groove_half_time", "snare").size()
	assert_eq(level.notes.size(), drum_phases * per_drum_phase + bass_phases * idx.cues("bass_sub_line", "bass").size(), "the loops' cues tiled over the phases")
	assert_eq(str(level.sequences[0]["reward"]), str(Loadout.reward_cycle(idx, "kick_half_time")[0]), "the first drum sequence pays the kick sound's first reward")
	assert_eq(str(level.sequences[1]["reward"]), str(Loadout.reward_cycle(idx, "snare_backbeat")[0]), "the second pays the snare sound's")
	var pads := {}
	var bass_pads := {}
	for n in level.notes:
		pads[int(n["pad"])] = true
		if n["family"] == "bass":
			bass_pads[int(n["pad"])] = true
	var used := pads.keys()
	used.sort()
	assert_eq(used, [1, 2, 3, 4], "kick on pad 1, snare on pad 4, bass spread over the pads")
	assert_true(bass_pads.size() >= 2, "the bass line uses more than one pad (%d)" % bass_pads.size())
	assert_eq(level.stems.keys(), ["kick", "snare", "bass", "other"], "kick, snare, bass and backing loops")
	for key in level.stems:
		assert_true(FileAccess.file_exists(level.stems[key]), level.stems[key])
		assert_true(int(level.stem_loop_bars[key]) in [8, 16])
	assert_eq(level.voice_name("kick_half_time"), idx.name("kick_half_time"))
	assert_eq(level.gain_program.size(), 128)


func test_a_loadout_changes_stems_and_cues() -> void:
	var a := _load("m02_second_pulse")
	var b := _load("m02_second_pulse", {"groove": "groove_straight", "kick_sound": "kick_march", "snare_sound": "snare_crack"})
	if a == null or b == null:
		return
	assert_eq(b.loadout["groove"], "groove_straight")
	assert_eq(b.loadout["snare_sound"], "snare_crack")
	assert_true(a.notes.size() != b.notes.size(), "another groove has other cues (%d vs %d)" % [a.notes.size(), b.notes.size()])
	for k in ["kick", "snare"]:
		assert_true(a.stems[k] != b.stems[k], "%s plays another loop" % k)
	assert_eq(a.stems["bass"], b.stems["bass"], "the bass loop is the same")
	var rewards_a := []
	var rewards_b := []
	for s in a.sequences:
		rewards_a.append(s["reward"])
	for s in b.sequences:
		rewards_b.append(s["reward"])
	assert_true(rewards_a != rewards_b, "other instruments pay other rewards")
	var bad := _load("m02_second_pulse", {"groove": "no_such_groove"})
	assert_eq(bad.loadout["groove"], LibraryIndex.load_default().defaults["groove"], "an unknown pick falls back to the default")


func test_perfect_play_passes_every_sequence_and_builds() -> void:
	var level := _load("m01_first_watch")
	if level == null:
		return
	var m := Match.new()
	m.setup(level)
	_play(m, level, func(_i: int, _n: Dictionary) -> bool: return true)
	var r := m.result()
	assert_eq(r["sequences_passed"], 64)
	assert_eq(r["grades"]["sharp"], 64)
	assert_eq(r["outcome"], "victory")
	assert_true(int(r["built"]) >= 1, "the snare sound builds pillboxes (%d)" % int(r["built"]))
	assert_true(int(r["units"]) > 0, "the kick and bass sounds send units (%d)" % int(r["units"]))
	assert_true(m.sim.defense_count() > 0)
	assert_eq(r["loadout"], level.loadout, "the result carries the loadout it was played with")


func test_no_input_fails_every_sequence_and_builds_nothing() -> void:
	var level := _load("m01_first_watch")
	if level == null:
		return
	var m := Match.new()
	m.setup(level)
	_play(m, level, func(_i: int, _n: Dictionary) -> bool: return false)
	var r := m.result()
	assert_eq(r["sequences_passed"], 0)
	assert_eq(r["built"], 0)
	assert_eq(m.sim.defense_count(), 0)


func test_bass_phases_cue_only_bass_and_drum_phases_only_drums() -> void:
	var level := _load("m03_hold_the_line")
	if level == null:
		return
	var bass_cues := 0
	for n in level.notes:
		var ph := level.phase_at(int(n["tick"]))
		assert_eq(str(ph["mode"]), "bass" if n["family"] == "bass" else "drums", "cues only in their family's phases")
		if n["family"] == "bass":
			bass_cues += 1
			assert_true(int(n["pad"]) >= 1 and int(n["pad"]) <= 4)
	assert_true(bass_cues > 0)
	var m := Match.new()
	m.setup(level, null, false)  # rhythm only: every sequence resolves whatever the battle does
	_play(m, level, func(_i: int, _n: Dictionary) -> bool: return true)
	assert_eq(m.result()["sequences_passed"], level.sequences.size())


func test_the_match_emits_the_gain_program_each_bar() -> void:
	var level := TestCase.fixture_level({"fill": "fill_a"})
	var m := Match.new()
	m.setup(level, null, false)
	var programs := []
	var t := -0.5
	while t < 16.0:
		m.advance(t)
		for ev in m.drain_events():
			if ev["kind"] == "program":
				programs.append(ev)
		t += 1.0 / 30.0
	var bar_s := 3840.0 / 2784.0  # seconds per bar at 174 BPM
	assert_eq(programs.size(), int(16.0 / bar_s) + 1, "one program per bar, the first one at the first frame")
	assert_eq(int(programs[0]["bar"]), 0)
	assert_eq(programs[0]["on"], level.gain_program[0])
	assert_eq(programs[7]["on"], level.gain_program[7], "bar 8 plays the fill loops")
	assert_true(programs[7]["on"]["fill_kick"])
	assert_false(programs[7]["on"]["kick"])
	var seen := {}
	for p in programs:
		assert_false(seen.has(int(p["bar"])), "each bar once")
		seen[int(p["bar"])] = true
