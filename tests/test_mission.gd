extends TestCase
## Schema 3 missions: loading a selection, cues on pads, sequences, rewards scheduled through the simulation.


func _load(pack: String, options: Dictionary = {}) -> Level:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + pack), options)
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


func test_mission_one_loads_with_pads_sequences_and_rewards() -> void:
	var level := _load("m01_first_watch")
	assert_true(level.is_mission())
	assert_eq(level.notes.size(), 64, "32 bars x kick + snare")
	assert_eq(level.sequences.size(), 8)
	assert_eq(str(level.sequences[0]["reward"]), "pillbox", "the first drum sequence rewards one pillbox")
	var pads := {}
	for n in level.notes:
		pads[int(n["pad"])] = true
	assert_eq(pads.keys(), [1, 4], "kick on pad 1, snare on pad 4")
	assert_eq(level.selection, {"kick_sound": ["kick_march"]})
	assert_eq(level.stems.size(), 3, "kick, snare and accompaniment stems")


func test_selection_changes_stems_and_cues() -> void:
	var a := _load("m02_second_pulse")
	var b := _load("m02_second_pulse", {"selection": {"groove": ["groove_straight"], "snare_sound": ["snare_crack"]}})
	assert_true(a.notes.size() > b.notes.size(), "the push groove has the extra kick")
	assert_eq(b.selection["snare_sound"], ["snare_crack"])
	var differ := false
	for k in a.stems:
		if a.stems[k] != b.stems.get(k, ""):
			differ = true
	assert_true(differ)
	var bad := _load("m02_second_pulse", {"selection": {"groove": ["groove_watch"]}})
	assert_eq(bad.selection["groove"], ["groove_push"], "an option outside the pool falls back to the default")


func test_perfect_play_passes_every_sequence_and_builds() -> void:
	var level := _load("m01_first_watch")
	var m := Match.new()
	m.setup(level)
	_play(m, level, func(_i: int, _n: Dictionary) -> bool: return true)
	var r := m.result()
	assert_eq(r["sequences_passed"], 8)
	assert_eq(r["grades"]["sharp"], 8)
	assert_eq(r["built"], 6, "six pillboxes")
	assert_eq(r["units"], 2, "two rocket soldiers")
	assert_true(m.sim.defense_count() > 0)


func test_no_input_fails_every_sequence_and_builds_nothing() -> void:
	var level := _load("m01_first_watch")
	var m := Match.new()
	m.setup(level)
	_play(m, level, func(_i: int, _n: Dictionary) -> bool: return false)
	var r := m.result()
	assert_eq(r["sequences_passed"], 0)
	assert_eq(r["built"], 0)
	assert_eq(m.sim.defense_count(), 0)


func test_bass_mission_holds_on_the_voice_pad() -> void:
	var level := _load("m03_hold_the_line")
	var holds := 0
	for n in level.notes:
		if n["family"] == "bass":
			assert_eq(int(n["pad"]), 2, "bass voice 1 is pad 2")
			if n["type"] == "hold":
				holds += 1
		var ph := level.phase_at(int(n["tick"]))
		assert_eq(str(ph["mode"]), "bass" if n["family"] == "bass" else "drums", "cues only in their family's phases")
	assert_true(holds > 20)
	var m := Match.new()
	m.setup(level, null, false)  # rhythm only: every sequence resolves whatever the battle does
	_play(m, level, func(_i: int, _n: Dictionary) -> bool: return true)
	assert_eq(m.result()["sequences_passed"], level.sequences.size())
