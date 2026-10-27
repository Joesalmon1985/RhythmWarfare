extends TestCase
## Judgement rules (PRD section 4, acceptance A01 and A02).

const BPM := 174.0
const TPB := 960


static func _level_with(notes: Array) -> Level:
	var d := {
		"schema_version": 1, "level_id": "t", "bpm": BPM, "time_signature": [4, 4], "ticks_per_beat": TPB,
		"song_offset_ms": 0, "duration_ticks": 3840 * 64, "seed": 1,
		"stems": {"kick": "a.ogg", "snare": "b.ogg", "bass": "c.ogg", "other": "d.ogg"},
		"sections": [{"id": "all", "start_tick": 0, "length_bars": 64}],
		"notes": notes, "enemy_events": [],
	}
	var errors: Array = []
	var warnings: Array = []
	var level := LevelLoader.parse(d, "/none", errors, warnings)
	assert(errors.is_empty(), str(errors))
	return level


static func _beat(n: int) -> int:
	return n * TPB


func test_ten_kicks_ten_snares_award_exactly() -> void:
	var notes := []
	for i in 10:
		notes.append({"id": "k%d" % i, "tick": _beat(i * 2), "lane": "kick", "type": "tap"})
		notes.append({"id": "s%d" % i, "tick": _beat(i * 2 + 1), "lane": "snare", "type": "tap"})
	var level := _level_with(notes)
	var j := Judge.new()
	j.setup(level.notes)
	for n in level.notes:
		var r := j.press(int(n["button"]), n["time"] + 0.010)
		assert_eq(r["kind"], "perfect", n["id"])
	j.update(level.duration_seconds())
	assert_eq(j.rewards["kick"], 10)
	assert_eq(j.rewards["snare"], 10)
	assert_eq(j.rewards["bass"], 0)
	assert_eq(j.misses, 0)
	assert_eq(j.combo, 20)
	var rewards := 0
	for ev in j.drain_events():
		if ev.get("reward", false):
			rewards += 1
	assert_eq(rewards, 20, "one reward event per note")


func test_miss_and_stray_award_nothing() -> void:
	var level := _level_with([
		{"id": "k0", "tick": _beat(4), "lane": "kick", "type": "tap"},
		{"id": "k1", "tick": _beat(8), "lane": "kick", "type": "tap"},
	])
	var j := Judge.new()
	j.setup(level.notes)
	var stray := j.press(1, 0.1)
	assert_eq(stray["kind"], "stray")
	j.press(1, level.notes[0]["time"] + 0.02)
	assert_eq(j.combo, 1)
	j.update(level.notes[1]["time"] + 0.2)
	assert_eq(j.misses, 1)
	assert_eq(j.combo, 0, "a miss breaks the combo")
	assert_eq(j.rewards["kick"], 1)
	assert_eq(j.strays, 1)
	assert_near(j.accuracy(), 0.5, 0.0001)


func test_window_boundaries() -> void:
	var level := _level_with([
		{"id": "a", "tick": _beat(4), "lane": "kick", "type": "tap"},
		{"id": "b", "tick": _beat(8), "lane": "kick", "type": "tap"},
		{"id": "c", "tick": _beat(12), "lane": "kick", "type": "tap"},
		{"id": "d", "tick": _beat(16), "lane": "kick", "type": "tap"},
	])
	var j := Judge.new()
	j.setup(level.notes)
	var t: float = level.notes[0]["time"]
	assert_eq(j.press(1, t + 0.045)["kind"], "perfect", "45 ms late is still Perfect")
	t = level.notes[1]["time"]
	assert_eq(j.press(1, t - 0.046)["kind"], "good", "46 ms early is Good")
	t = level.notes[2]["time"]
	assert_eq(j.press(1, t + 0.100)["kind"], "good", "100 ms late is still Good")
	t = level.notes[3]["time"]
	assert_eq(j.press(1, t - 0.101)["kind"], "stray", "101 ms early matches nothing")
	assert_eq(j.press(1, t)["kind"], "perfect", "the note is still there after the stray")
	assert_eq(j.rewards["kick"], 4)


func test_one_press_cannot_satisfy_two_notes_and_repeats_do_nothing() -> void:
	var level := _level_with([
		{"id": "a", "tick": 0, "lane": "snare", "type": "tap"},
		{"id": "b", "tick": 240, "lane": "snare", "type": "tap"},  # 86 ms later: both inside one window
	])
	var j := Judge.new()
	j.setup(level.notes)
	var first := j.press(4, 0.03)
	assert_eq(first["note_id"], "a", "nearest note wins")
	assert_eq(j.rewards["snare"], 1)
	var second := j.press(4, 0.03)
	assert_eq(second["note_id"], "b", "a second distinct press takes the next note, never the same one")
	var third := j.press(4, 0.03)
	assert_eq(third["kind"], "stray", "no third note exists")
	assert_eq(j.rewards["snare"], 2)


func test_hold_rewards_once_on_completion_only() -> void:
	var level := _level_with([
		{"id": "h", "tick": _beat(4), "lane": "bass", "type": "hold", "duration_ticks": _beat(4)},
	])
	var j := Judge.new()
	j.setup(level.notes)
	var start: float = level.notes[0]["time"]
	var end: float = level.notes[0]["end_time"]
	var b := int(level.notes[0]["button"])
	assert_eq(b, 2, "a bass note without a button defaults to an inner button")
	var r := j.press(b, start + 0.01, 3)
	assert_eq(r["kind"], "hold_start")
	j.update(start + 0.5)
	assert_eq(j.rewards["bass"], 0, "nothing while holding")
	assert_true(j.active_hold_progress(b) > 0.0)
	assert_eq(j.press(b, start + 0.6, 4)["kind"], "ignored", "a second finger on the button does nothing")
	j.update(end + 0.3)
	assert_eq(j.rewards["bass"], 1, "one action at the tail")
	j.update(end + 5.0)
	assert_eq(j.rewards["bass"], 1, "holding longer adds nothing")
	assert_eq(j.release(b, end + 5.0, 3)["kind"], "none")


func test_hold_release_tolerance() -> void:
	var level := _level_with([
		{"id": "h1", "tick": _beat(4), "lane": "bass", "type": "hold", "duration_ticks": _beat(4)},
		{"id": "h2", "tick": _beat(12), "lane": "bass", "type": "hold", "duration_ticks": _beat(4)},
	])
	var j := Judge.new()
	j.setup(level.notes)
	var s1: float = level.notes[0]["time"]
	var e1: float = level.notes[0]["end_time"]
	var b1 := int(level.notes[0]["button"])
	var b2 := int(level.notes[1]["button"])
	assert_true(b1 != b2, "bass notes without buttons alternate between the inner buttons")
	j.press(b1, s1, 1)
	assert_eq(j.release(b1, e1 - 0.050, 1)["kind"], "hold_release_ok", "50 ms early is inside tolerance")
	assert_eq(j.rewards["bass"], 0, "the reward waits for the scheduled tail")
	j.update(e1)
	assert_eq(j.rewards["bass"], 1)
	var s2: float = level.notes[1]["time"]
	var e2: float = level.notes[1]["end_time"]
	j.press(b2, s2, 1)
	assert_eq(j.release(b2, e2 - 0.070, 1)["kind"], "hold_fail", "70 ms early fails")
	j.update(e2 + 1.0)
	assert_eq(j.rewards["bass"], 1, "a failed hold grants nothing")
	assert_eq(j.misses, 1)
	assert_eq(j.combo, 0)


func test_unavailable_lane_excluded_from_misses() -> void:
	var level := _level_with([
		{"id": "k0", "tick": _beat(0), "lane": "kick", "type": "tap"},
		{"id": "k1", "tick": _beat(8), "lane": "kick", "type": "tap"},
		{"id": "s1", "tick": _beat(8), "lane": "snare", "type": "tap"},
	])
	var j := Judge.new()
	j.setup(level.notes)
	j.press(1, 0.0)
	j.set_lane_available("kick", false)
	assert_eq(j.press(1, level.notes[1]["time"])["kind"], "inert")
	j.update(level.duration_seconds())
	assert_eq(j.misses, 1, "only the snare counts as a miss")
	assert_eq(j.state_of(1), Judge.State.UNAVAILABLE)
	assert_near(j.accuracy(), 0.5, 0.0001, "earned accuracy is kept, unavailable notes are excluded")
	j.set_lane_available("bass", false)
	assert_true(j.is_lane_available("bass"), "bass can never be made unavailable")


func test_pause_voids_active_hold() -> void:
	var level := _level_with([
		{"id": "h", "tick": _beat(4), "lane": "bass", "type": "hold", "duration_ticks": _beat(4)},
	])
	var j := Judge.new()
	j.setup(level.notes)
	j.press(int(level.notes[0]["button"]), level.notes[0]["time"], 1)
	j.void_active_holds()
	j.update(level.duration_seconds())
	assert_eq(j.rewards["bass"], 0)
	assert_eq(j.misses, 0)
	assert_eq(j.state_of(0), Judge.State.VOID)
	assert_eq(j.judged_count(), 0)


func test_tick_arithmetic_matches_prd() -> void:
	var level := _level_with([])
	assert_near(level.tick_to_seconds(3840), 1.37931, 0.00001, "one bar at 174 BPM")
	assert_near(level.tick_to_seconds(245760), 88.2759, 0.001, "64 bars")
	assert_eq(level.seconds_to_tick(level.tick_to_seconds(12345)), 12345)
	level.song_offset_ms = 250
	assert_near(level.tick_to_seconds(0), 0.25, 0.00001, "song offset shifts every event")


func test_buttons_kick_left_snare_right_bass_anywhere() -> void:
	var level := _level_with([
		{"id": "k", "tick": _beat(0), "lane": "kick", "type": "tap"},
		{"id": "b1", "tick": _beat(2), "lane": "bass", "type": "tap", "button": 1},
		{"id": "b2", "tick": _beat(3), "lane": "bass", "type": "tap", "button": 2},
		{"id": "b3", "tick": _beat(4), "lane": "bass", "type": "tap", "button": 3},
		{"id": "b4", "tick": _beat(5), "lane": "bass", "type": "hold", "duration_ticks": _beat(2), "button": 4},
		{"id": "s", "tick": _beat(8), "lane": "snare", "type": "tap"},
	])
	assert_eq(int(level.notes[0]["button"]), 1, "kick is button 1")
	assert_eq(int(level.notes[5]["button"]), 4, "snare is button 4")
	var j := Judge.new()
	j.setup(level.notes)
	assert_eq(j.press(4, level.notes[0]["time"])["kind"], "stray", "the kick is not on button 4")
	assert_eq(j.press(1, level.notes[0]["time"])["kind"], "perfect")
	for i in range(1, 4):
		assert_eq(j.press(int(level.notes[i]["button"]), level.notes[i]["time"])["kind"], "perfect", level.notes[i]["id"])
	assert_eq(j.press(4, level.notes[4]["time"], 7)["kind"], "hold_start", "a bass hold on button 4")
	j.update(level.notes[4]["end_time"] + 0.1)
	assert_eq(j.press(4, level.notes[5]["time"])["kind"], "perfect", "button 4 goes back to the snare after the hold")
	assert_eq(j.rewards, {"kick": 1, "snare": 1, "bass": 4})


func test_dead_lane_press_on_shared_button_is_inert_but_bass_still_plays() -> void:
	var level := _level_with([
		{"id": "k0", "tick": _beat(0), "lane": "kick", "type": "tap"},
		{"id": "b0", "tick": _beat(4), "lane": "bass", "type": "tap", "button": 1},
		{"id": "k1", "tick": _beat(8), "lane": "kick", "type": "tap"},
	])
	var j := Judge.new()
	j.setup(level.notes)
	j.set_lane_available("kick", false)
	assert_eq(j.press(1, level.notes[0]["time"])["kind"], "inert", "a dead kick note swallows the press without a stray")
	assert_eq(j.press(1, level.notes[1]["time"])["kind"], "perfect", "a bass note on button 1 still plays")
	j.update(level.duration_seconds())
	assert_eq(j.strays, 0)
	assert_eq(j.misses, 0, "unavailable kick notes are not misses")
	assert_eq(j.rewards, {"kick": 0, "snare": 0, "bass": 1})
