extends TestCase
## The track transport: the fixture's five stems play as one stream on one player, keep the pack's gains, and a mute
## and restore only ramps a stem's gain (one playhead, a monotonic clock). Runs on the headless audio driver, which
## mixes in real time, so only structure and monotonic time are asserted, not sound.


func _transport(pack: TrackPack) -> TrackTransport:
	var t := TrackTransport.new()
	tree.root.add_child(t)
	assert_eq(t.load_pack_streams(pack), "")
	return t


func test_one_stream_one_player_with_pack_gains() -> void:
	var pack := TrackTestKit.fixture_pack()
	var t := _transport(pack)
	assert_eq(t.stem_keys, ["drums", "lead", "pads", "bass", "backing"])
	assert_eq(t.sync_stream.stream_count, 5)
	var players := 0
	for c in t.get_children():
		if c is AudioStreamPlayer:
			players += 1
	assert_eq(players, 1, "one player carries every stem")
	assert_near(t.pack_gain("pads"), 0.8, 1e-9)
	assert_near(t.effective_gain("pads"), 0.8, 1e-9)
	assert_near(t.effective_gain("drums"), 1.0, 1e-9)
	t.set_stem_muted("pads", true)
	assert_eq(t.stem_target("pads"), 0.0)
	t.queue_free()


func test_mute_and_restore_keep_one_playhead() -> void:
	var pack := TrackTestKit.fixture_pack()
	var t := _transport(pack)
	var clock := SongClock.new(t)
	clock.begin_countdown(0.0)
	await tree.process_frame
	clock.tick()
	assert_eq(clock.state, SongClock.State.PLAYING)
	var last := -INF
	var cycles := 0
	for i in 90:
		await tree.process_frame
		var now := clock.audio_time()
		if now < last:
			fail("song clock moved backwards: %f after %f" % [now, last])
		last = now
		if i % 3 == 0:
			for key in ["drums", "lead", "pads", "bass"]:
				t.set_stem_muted(key, not t.is_stem_muted(key))
			cycles += 1
	assert_true(cycles >= 20)
	assert_true(t.is_playing(), "still playing after the mute cycles")
	assert_false("backing" in ["drums"] and t.is_stem_muted("backing"))
	assert_false(t.is_stem_muted("backing"), "backing never muted")
	# a mute ramps the gain to silence and back to the pack gain without stopping the stream
	for key in ["drums", "lead", "pads", "bass"]:
		t.set_stem_muted(key, true)
	await tree.create_timer(0.3).timeout
	for key in ["drums", "lead", "pads", "bass"]:
		assert_eq(t.stem_gain(key), 0.0, "%s silent" % key)
	assert_eq(t.stem_gain("backing"), 1.0, "backing untouched")
	assert_true(t.is_playing())
	t.set_stem_muted("pads", false)
	await tree.create_timer(0.3).timeout
	assert_eq(t.stem_gain("pads"), 1.0)
	assert_near(t.effective_gain("pads"), 0.8, 1e-9, "restored to the pack gain")
	var after := clock.audio_time()
	assert_true(after >= last, "time kept going: %f then %f" % [last, after])
	t.stop()
	t.queue_free()
