extends TestCase
## Schema 3 missions: loading a selection, cues on pads, sequences, rewards scheduled through the simulation.


const BUILT := 9
const UNITS := 18  # squads delivered: 11 rifle + 7 grenadier rewards, all within the 14-per-point capacity under perfect play


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
	assert_eq(level.notes.size(), 10 * 18 + 6 * 12, "ten drum phases of 10 kicks and 8 snares, six bass phases of 12 taps")
	assert_eq(level.sequences.size(), 32, "128 bars in four-bar sequences")
	assert_eq(str(level.sequences[0]["reward"]), "pillbox", "the first drum sequence rewards one pillbox")
	var pads := {}
	var bass_pads := {}
	var bass_ticks := []
	for n in level.notes:
		pads[int(n["pad"])] = true
		if n["family"] == "bass":
			assert_eq(str(n["type"]), "tap", "every bass cue is a tap")
			bass_pads[int(n["pad"])] = true
			bass_ticks.append(int(n["tick"]))
	var used := pads.keys()
	used.sort()
	assert_eq(used, [1, 2, 3, 4], "kick on pad 1, snare on pad 4, bass spread over the pads by pitch")
	assert_true(bass_pads.size() >= 3, "the bass uses at least three pads (%d)" % bass_pads.size())
	assert_eq(bass_ticks.size(), 72, "six bass phases of 12 taps")
	bass_ticks.sort()
	for i in range(1, bass_ticks.size()):
		assert_true(bass_ticks[i] - bass_ticks[i - 1] >= 1440, "bass cues are at least 1440 ticks apart")
	assert_eq(level.selection, {"groove": ["groove_half_time"], "bass": ["bass_sub_line"], "bass_voice": ["bass_sub_deep"], "accompaniment": ["acc_hats_driving"]})
	assert_eq(level.stems.size(), 4, "kick, snare, bass and backing stems")


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
	assert_eq(r["sequences_passed"], 32)
	assert_eq(r["grades"]["sharp"], 32)
	assert_eq(r["outcome"], "victory")
	assert_eq(r["built"], BUILT, "three sockets per point: only nine pillboxes fit, later pillbox rewards repair")
	assert_eq(r["units"], UNITS, "rifle and grenadier squads of three")
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
