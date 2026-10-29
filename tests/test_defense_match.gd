extends TestCase
## Schema 2 match behaviour that does not need the battle: rewards per slot, one reward per hold, inert slots,
## practice charts, and the generic stem transport with five streams.


func _level(pack: String, chart := "") -> Level:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + pack), {"chart_id": chart})
	assert_eq(loaded["errors"], [])
	return loaded["level"]


func _play_all(m: Match, level: Level, skip_slot := "") -> void:
	for n in level.notes:
		if n["slot_id"] != skip_slot:
			m.press(int(n["button"]), n["time"], 1)
			if n["type"] == "hold":
				m.advance(n["end_time"] - 0.03)
				m.release(int(n["button"]), n["end_time"] - 0.01, 1)
		m.advance(n["end_time"] + 0.02)


func test_hold_gives_one_reward_at_the_tail_and_chart_has_no_uncharted_notes() -> void:
	var level := _level("hold_the_line")
	var m := Match.new()
	m.setup(level, null, false)
	var hold: Dictionary = {}
	for n in level.notes:
		if n["type"] == "hold":
			hold = n
			break
	m.press(int(hold["button"]), hold["time"], 1)
	m.advance(hold["time"] + 0.01)
	assert_eq(int(m.judge.rewards.get("bass_1", 0)), 0, "no reward while held")
	m.advance(hold["end_time"] - 0.5)
	assert_eq(int(m.judge.rewards.get("bass_1", 0)), 0, "still none mid-hold")
	m.release(int(hold["button"]), hold["end_time"] - 0.01, 1)
	m.advance(hold["end_time"] + 0.05)
	assert_eq(int(m.judge.rewards.get("bass_1", 0)), 1, "exactly one reward at the tail")
	m.advance(hold["end_time"] + 5.0)
	assert_eq(int(m.judge.rewards.get("bass_1", 0)), 1, "no repeated income")
	# every note belongs to an equipped playable slot: accompaniment parts produce no prompts or misses
	for n in level.notes:
		assert_true(level.loadout_active_slots.has(n["slot_id"]))
		assert_true(n["family"] != "other")


func test_rhythm_only_run_ends_at_duration_not_at_audio_end() -> void:
	var level := _level("first_watch")
	var m := Match.new()
	m.setup(level, null, false)
	_play_all(m, level)
	assert_eq(m.outcome, "", "still running after the last note")
	assert_true(m.judge.misses == 0 and m.judge.accuracy() == 1.0)
	m.advance(level.duration_seconds() - 0.001)
	assert_eq(m.outcome, "")
	m.advance(level.duration_seconds())
	assert_eq(m.outcome, "complete", "ends at duration_ticks; the stems' tail bar does not extend it")
	var r := m.result()
	assert_eq(r["mode"], "defense")
	assert_eq(int(r["rewards"]["kick_1"]), 32)
	assert_eq(int(r["rewards"]["snare_1"]), 32)


func test_unavailable_slot_is_inert_and_excluded_from_accuracy() -> void:
	var level := _level("second_pulse")
	var m := Match.new()
	m.setup(level, null, false)
	m.judge.set_slot_available("kick_2", false)
	_play_all(m, level)
	var kick2 := 0
	for n in level.notes:
		if n["slot_id"] == "kick_2":
			kick2 += 1
	assert_eq(kick2, 16)
	assert_eq(m.judge.judged_count(), level.notes.size() - kick2, "inert notes are not counted")
	assert_eq(m.judge.misses, 0)
	assert_eq(int(m.judge.rewards.get("kick_2", 0)), 0)
	assert_eq(int(m.judge.rewards["kick_1"]), 40)


func test_practice_chart_is_flagged_and_judges_like_the_campaign_chart() -> void:
	var level := _level("second_pulse", "level_02.practice")
	assert_eq(level.play_mode, "practice")
	var m := Match.new()
	m.setup(level, null, false)
	_play_all(m, level)
	m.advance(level.duration_seconds())
	var r := m.result()
	assert_false(r["progression"], "practice never feeds progression")
	assert_eq(r["chart_id"], "level_02.practice")
	assert_eq(m.judge.judged_count(), 80)


func test_transport_plays_and_mutes_every_stream_of_a_five_stem_level() -> void:
	var level := _level("hold_the_line")
	var transport := StemTransport.new()
	tree.root.add_child(transport)
	assert_eq(transport.load_level(level), "")
	assert_eq(transport.stem_keys.size(), 5)
	assert_eq(transport.sync_stream.stream_count, 5)
	var clock := SongClock.new(transport)
	clock.begin_countdown(0.0)
	await tree.process_frame
	clock.tick()
	var last := -INF
	for i in 60:
		await tree.process_frame
		var t := clock.audio_time()
		if t < last:
			fail("clock moved backwards")
		last = t
		if i % 3 == 0:
			for key in transport.stem_keys:
				transport.set_stem_muted(key, not transport.is_stem_muted(key))
	assert_true(transport.is_playing())
	for key in transport.stem_keys:
		transport.set_stem_muted(key, false)
	for i in 10:
		await tree.process_frame
	for key in transport.stem_keys:
		assert_near(transport.stem_gain(key), 1.0, 0.001, "gain restored for " + key)
	transport.stop()
	transport.queue_free()
