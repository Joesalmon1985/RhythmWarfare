extends TestCase
## Night One plays the recorded Beat Shaper "Lv1 Warehouse" stems (songs/story_n1_warehouse, written by
## tools/content/import_recorded.py): three WAV loops of exactly eight bars, the recording's 87 BPM mapped to two game beats
## per source beat on the 174 BPM grid, kick/snare/bass cues derived from the matching MIDI, bass notes as holds.

const PACK := "res://songs/story_n1_warehouse"
const SOURCE_BPM := 87.0


func _level() -> Level:
	var lr := LevelLoader.load_pack(PACK, {})
	assert_eq(lr["errors"], [], "the Warehouse pack loads")
	return lr["level"]


func test_night_one_points_at_the_warehouse_pack() -> void:
	var d: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/night_one.json"))
	assert_eq(str(d["music_pack"]), PACK)
	var run := StoryRun.create({})
	assert_eq(run.errors, [])
	assert_true(run.level.recorded, "the level plays recorded stems")


func test_three_stems_of_exactly_eight_bars() -> void:
	var level := _level()
	if level == null:
		return
	assert_eq(level.stems.keys(), ["drums", "bass", "other"])
	var want := 8.0 * 4.0 * 60.0 / 174.0  # 8 bars = 16 source beats at 87 BPM = 11.0345 s
	assert_near(want, 16.0 * 60.0 / SOURCE_BPM, 1e-9, "16 beats at 87 is 32 beats at 174")
	for key in level.stems:
		var s := LevelLoader.load_stream(level.stems[key]) as AudioStreamWAV
		assert_true(s != null, "%s decodes as a WAV" % key)
		if s == null:
			continue
		assert_eq(s.mix_rate, 48000, "%s is not resampled" % key)
		assert_near(s.get_length(), want, 1.0 / 48000.0, "%s is one loop long, tails folded in" % key)
		assert_eq(int(level.stem_loop_bars[key]), 8)
	var lengths := []
	for key in level.stem_lengths:
		lengths.append(snappedf(float(level.stem_lengths[key]), 0.000001))
	assert_eq(lengths.count(lengths[0]), lengths.size(), "unequal source lengths are equalised, so the stems cannot drift apart")


func test_loop_streams_loop_the_whole_file() -> void:
	var level := _level()
	if level == null:
		return
	var t := StemTransport.new()
	tree.root.add_child(t)
	assert_eq(t.load_level(level), "")
	assert_near(t.loop_seconds, 8.0 * 4.0 * 60.0 / 174.0, 1.0 / 48000.0)
	for key in level.stems:
		var s := LevelLoader.load_stream(level.stems[key]) as AudioStreamWAV
		StemTransport._set_loop(s)
		assert_eq(s.loop_mode, AudioStreamWAV.LOOP_FORWARD)
		assert_eq(s.loop_end, int(round(s.get_length() * 48000.0)), "%s loops over its whole length" % key)
	t.queue_free()


func test_cues_sit_on_the_87_bpm_beats_and_repeat_every_loop() -> void:
	var level := _level()
	if level == null:
		return
	var loop_s := 8.0 * 4.0 * 60.0 / 174.0
	for n in level.notes:
		var src_beat := float(int(n["tick"]) % (8 * level.ticks_per_bar())) / (2.0 * level.ticks_per_beat)  # source beats into the loop
		var loops := int(n["tick"]) / (8 * level.ticks_per_bar())
		assert_near(float(n["time"]), float(loops) * loop_s + src_beat * 60.0 / SOURCE_BPM, 1e-6, "cue %s time" % n["id"])
	# the same cue pattern in every eight-bar loop of a drums phase (loops 0, 1 and 3 are drums, 2 is bass in the first 32 bars)
	var by_loop := {}
	for n in level.notes:
		var loop_i := int(n["tick"]) / (8 * level.ticks_per_bar())
		var key := "%s:%d" % [n["family"], int(n["tick"]) % (8 * level.ticks_per_bar())]
		if not by_loop.has(loop_i):
			by_loop[loop_i] = {}
		by_loop[loop_i][key] = true
	for loop_i in by_loop:
		var sections := level.phase_at(loop_i * 8 * level.ticks_per_bar())
		assert_true(by_loop[loop_i].size() > 0, "loop %d (%s) has cues" % [loop_i, sections.get("mode", "")])


func test_cue_counts_and_pads_come_from_the_midi() -> void:
	var level := _level()
	if level == null:
		return
	var rec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(PACK + "/level.json"))["recorded_music"]
	var cues: Dictionary = rec["cues"]
	assert_eq(cues["kick"].size(), 13)
	assert_eq(cues["snare"].size(), 19)
	assert_eq(cues["bass"].size(), 4)
	for c in cues["kick"]:
		assert_eq(int(c[2]), 1, "kick on pad 1")
	for c in cues["snare"]:
		assert_eq(int(c[2]), 4, "snare on pad 4")
	var pads := []
	for c in cues["bass"]:
		pads.append(int(c[2]))
	assert_eq(pads, [2, 1, 2, 3], "bass pads follow pitch E D E C: D lowest, C highest")
	# the first notes of the source MIDI: kick on beat 0, kick on beat 1.25, snare on beat 0.75 (x2 game beats, 960 ticks each)
	assert_eq(int(cues["kick"][0][0]), 0)
	assert_eq(int(cues["kick"][1][0]), 2400)
	assert_eq(int(cues["snare"][0][0]), 1440)


func test_bass_cues_are_holds_that_end_inside_their_sequence() -> void:
	var level := _level()
	if level == null:
		return
	var holds := 0
	for n in level.notes:
		if n["family"] != "bass":
			continue
		assert_eq(n["type"], "hold")
		holds += 1
		assert_true(int(n["duration_ticks"]) >= 480, "a playable hold")
		assert_true(int(n["seq"]) >= 0)
		assert_true(int(n["end_tick"]) <= int(level.sequences[int(n["seq"])]["end_tick"]), "%s ends inside its sequence" % n["id"])
	assert_true(holds > 0, "the form has bass phases")


func test_stems_follow_the_phases_and_a_miss_mutes_the_drum_mix() -> void:
	var run := StoryRun.create({})
	assert_eq(run.errors, [])
	var level := run.level
	var tpb := level.ticks_per_bar()
	for bar in level.bar_count():
		var mode := str(level.phase_at(bar * tpb)["mode"])
		var on := level.audible_stems(bar)
		assert_true("other" in on, "the Synth backing plays throughout (bar %d)" % bar)
		assert_eq("drums" in on, mode == "drums", "drums only in drum phases (bar %d)" % bar)
		assert_eq("bass" in on, mode == "bass", "bass only in bass phases (bar %d)" % bar)
	var m := run.match_ref
	m._set_family("kick", true, 0.0)
	assert_true(bool(m.stems_muted["drums"]), "a missed kick silences the drum recording")
	assert_true(m.family_muted("snare"), "which carries the snare as well")
	m._set_family("snare", false, 0.1)
	assert_false(bool(m.stems_muted["drums"]), "a hit on either brings it back")
	assert_false(bool(m.stems_muted["other"]), "the backing never mutes")
