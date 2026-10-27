extends TestCase
## Four-stem transport and song clock (A09 structural checks, A10 pause behaviour). Runs on the headless
## audio driver, which mixes in real time; device output latency and audible alignment need the phone.


func test_mute_cycles_keep_one_playhead_and_clock_monotonic() -> void:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/test_16"))
	assert_eq(loaded["errors"], [])
	if loaded["level"] == null:
		return
	var level: Level = loaded["level"]
	var transport := StemTransport.new()
	tree.root.add_child(transport)
	assert_eq(transport.load_level(level), "")
	var clock := SongClock.new(transport)
	clock.begin_countdown(0.0)
	await tree.process_frame
	clock.tick()
	assert_eq(clock.state, SongClock.State.PLAYING)
	var last := -INF
	var wall0 := Time.get_ticks_usec()
	var cycles := 0
	var worst_jump := 0.0
	for i in 120:
		await tree.process_frame
		var t := clock.audio_time()
		if t < last:
			fail("song clock moved backwards: %f after %f" % [t, last])
		if i > 0:
			worst_jump = maxf(worst_jump, t - last)
		last = t
		# a mute/unmute cycle on every stem, every other frame: must never stop or restart playback
		if i % 2 == 0:
			for key in StemTransport.STEM_ORDER:
				transport.set_stem_muted(key, not transport.is_stem_muted(key))
			cycles += 1
	var wall := float(Time.get_ticks_usec() - wall0) / 1_000_000.0
	assert_true(cycles >= 50, "ran %d mute cycles" % cycles)
	assert_true(transport.is_playing(), "still playing after the cycles")
	assert_true(last > 0.5, "audio advanced (%.3f s)" % last)
	assert_near(last, wall, 0.25, "audio clock tracks wall time (%.3f vs %.3f s)" % [last, wall])
	assert_true(worst_jump < 0.25, "no jump larger than a quarter second (worst %.3f)" % worst_jump)
	# gains settle to their targets after the 30 ms ramp
	for key in StemTransport.STEM_ORDER:
		transport.set_stem_muted(key, false)
	for i in 6:
		await tree.process_frame
	for key in StemTransport.STEM_ORDER:
		assert_near(transport.stem_gain(key), 1.0, 0.001, "%s restored" % key)
	# pause freezes the clock; resume re-anchors without going backwards
	clock.pause()
	var frozen := clock.audio_time()
	for i in 10:
		await tree.process_frame
	assert_eq(clock.audio_time(), frozen, "frozen while paused")
	assert_true(transport.is_paused())
	clock.resume()
	for i in 5:
		await tree.process_frame
	assert_true(clock.audio_time() >= frozen, "no backwards jump across resume")
	transport.stop()
	transport.queue_free()


func test_stem_lengths_equal_in_both_packs() -> void:
	for pack in ["songs/test_16", "songs/level_01"]:
		var loaded := LevelLoader.load_pack(TestCase.project_path(pack))
		if loaded["level"] == null:
			fail("%s rejected: %s" % [pack, loaded["errors"]])
			continue
		var level: Level = loaded["level"]
		var lo: float = INF
		var hi: float = -INF
		for key in level.stem_lengths:
			lo = minf(lo, level.stem_lengths[key])
			hi = maxf(hi, level.stem_lengths[key])
		assert_true(hi - lo < 0.005, "%s stems within 5 ms (%.4f)" % [pack, hi - lo])
