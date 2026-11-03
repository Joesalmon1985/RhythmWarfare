extends TestCase
## Stem transport and song clock (A09 structural checks, A10 pause behaviour), and the looping mission transport: loop
## flags, longest loop first, an unwrapped song position, song_base for practice, and the gain program combined with
## the miss mutes. Runs on the headless audio driver, which mixes in real time; device output latency and audible
## alignment need the phone.

const LOOP_HALF := "tests/fixtures/transport/loop_half.wav"  # 0.5 s
const LOOP_ONE := "tests/fixtures/transport/loop_one.wav"  # 1.0 s


## A mission-shaped level on the two short loops: "kick" loops every 0.5 s, "bass" every 1.0 s.
func _loop_level(program: Array = []) -> Level:
	var level := Level.new()
	level.schema_version = 4
	level.stems = {"kick": TestCase.project_path(LOOP_HALF), "bass": TestCase.project_path(LOOP_ONE)}
	level.stem_loop_bars = {"kick": 1, "bass": 2}
	level.gain_program = program
	return level


func _transport() -> StemTransport:
	var t := StemTransport.new()
	Engine.get_main_loop().root.add_child(t)
	return t


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


func test_loops_are_set_and_ordered_longest_first() -> void:
	var transport := _transport()
	var level := _loop_level()
	assert_eq(transport.load_level(level), "")
	assert_eq(transport.stem_keys, ["bass", "kick"], "the longest loop is the first substream")
	assert_near(transport.loop_seconds, 1.0, 0.01, "loop_seconds is the longest loop")
	for i in transport.stem_keys.size():
		var stream := transport.sync_stream.get_sync_stream(i) as AudioStreamWAV
		assert_true(stream != null)
		assert_eq(stream.loop_mode, AudioStreamWAV.LOOP_FORWARD, "%s loops" % transport.stem_keys[i])
		assert_eq(stream.loop_begin, 0)
		assert_eq(stream.loop_end, int(round(stream.get_length() * stream.mix_rate)), "the loop ends at the last sample")
	# stems with no loop length (the duel) are left as they are and the transport reports no loop
	var duel := LevelLoader.load_pack(TestCase.project_path("songs/test_16"))
	if duel["level"] != null:
		var plain := _transport()
		assert_eq(plain.load_level(duel["level"]), "")
		assert_eq(plain.loop_seconds, 0.0)
		for i in plain.stem_keys.size():
			var ogg := plain.sync_stream.get_sync_stream(i) as AudioStreamOggVorbis
			assert_false(ogg.loop, "duel stems do not loop")
		plain.queue_free()
	transport.queue_free()


func test_position_grows_past_the_loop_length() -> void:
	var transport := _transport()
	assert_eq(transport.load_level(_loop_level()), "")
	var clock := SongClock.new(transport)
	clock.begin_countdown(0.0)
	await tree.process_frame
	clock.tick()
	assert_eq(clock.state, SongClock.State.PLAYING)
	var wall0 := Time.get_ticks_usec()
	var last := -INF
	var raw_last := 0.0
	var raw_dropped := false
	var raw_max := 0.0
	while float(Time.get_ticks_usec() - wall0) / 1_000_000.0 < 2.6:
		await tree.process_frame
		var t := clock.audio_time()
		assert_true(t >= last, "the clock never moves backwards (%f after %f)" % [t, last])
		last = t
		var raw := transport.player.get_playback_position()
		if raw < raw_last - 0.25:
			raw_dropped = true
		raw_last = raw
		raw_max = maxf(raw_max, raw)
	var wall := float(Time.get_ticks_usec() - wall0) / 1_000_000.0
	# the finding, whichever it is: does AudioStreamPlayer.get_playback_position() wrap over looping substreams?
	print("  FINDING: raw get_playback_position over looping AudioStreamSynchronized %s (raw max %.3f s, loop %.3f s, ran %.3f s, wraps counted %d)" % [
		"WRAPS at the loop length" if raw_dropped else "keeps growing past the loop length", raw_max, transport.loop_seconds, wall, transport._wraps])
	assert_true(last > 2.0, "the song position passed two loop lengths (%.3f s)" % last)
	assert_near(last, wall, 0.3, "and tracks wall time (%.3f vs %.3f s)" % [last, wall])
	assert_eq(raw_dropped, transport._wraps > 0, "the transport unwraps exactly when the raw position wraps")
	assert_true(transport.is_playing(), "looping stems never finish")
	transport.stop()
	transport.queue_free()


func test_start_inside_a_later_loop_keeps_song_time() -> void:
	var transport := _transport()
	assert_eq(transport.load_level(_loop_level()), "")
	transport.start_at = 3.25  # practice of a later phase: three loops and a quarter in
	var clock := SongClock.new(transport)
	clock.begin_countdown(0.0)
	await tree.process_frame
	clock.tick()
	assert_near(transport.song_base, 3.0, 0.001, "song_base is the whole loops before the start")
	for i in 20:
		await tree.process_frame
	var t := clock.audio_time()
	assert_true(t >= 3.25 and t < 3.9, "song time continues from the start second (%.3f)" % t)
	transport.stop()
	transport.queue_free()


func test_gain_program_and_miss_mutes_combine() -> void:
	var transport := _transport()
	var program: Array = [{"kick": false, "bass": true}, {"kick": true, "bass": false}]
	assert_eq(transport.load_level(_loop_level(program)), "")
	assert_eq(transport.stem_target("kick"), 1.0, "everything sounds before a program")
	transport.start()  # the first bar's program applies from the first sample
	assert_eq(transport.stem_target("kick"), 0.0)
	assert_eq(transport.stem_target("bass"), 1.0)
	assert_eq(transport.stem_gain("kick"), 0.0, "snapped, not ramped")
	assert_false(transport.is_stem_muted("kick"), "a program is not a miss mute")
	transport.apply_program({"kick": true, "bass": false})
	assert_eq(transport.stem_target("kick"), 1.0)
	assert_eq(transport.stem_target("bass"), 0.0)
	transport.set_stem_muted("kick", true)
	assert_eq(transport.stem_target("kick"), 0.0, "programmed on but muted by a miss: silent")
	assert_true(transport.is_stem_muted("kick"))
	transport.apply_program({"kick": true})
	assert_eq(transport.stem_target("kick"), 0.0, "a new bar does not undo a miss mute")
	transport.set_stem_muted("bass", true)
	transport.apply_program({"bass": true})
	assert_eq(transport.stem_target("bass"), 0.0, "bass is programmed on again but still muted")
	transport.set_stem_muted("bass", false)
	assert_eq(transport.stem_target("bass"), 1.0)
	transport.set_stem_muted("kick", false)
	assert_eq(transport.stem_target("kick"), 1.0)
	transport.apply_program({"kick": false})
	transport.set_stem_muted("kick", false)
	assert_eq(transport.stem_target("kick"), 0.0, "a hit does not override the program")
	for i in 8:  # the 30 ms ramp
		await tree.process_frame
	assert_near(transport.stem_gain("kick"), 0.0, 0.001)
	assert_near(transport.stem_gain("bass"), 1.0, 0.001)
	transport.apply_program({"unknown_stem": true})  # ignored, never an error
	assert_true(transport.is_playing())
	transport.stop()
	transport.queue_free()
