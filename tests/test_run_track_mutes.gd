extends TestCase
## Track scenes, the mute rule (RunTrackMutes, docs/RUN_TRACK_SCENES.md "Audio"): a miss or a hold let go early mutes the cue's voice, the next hit restores it, a voice comes back by itself 8 beats
## after the mute when no cue of it falls within them, every mute restarts that wait, backing and ordinary cues never mute, a hold ended by the pause mutes nothing.

const BEAT := 0.5


## A track cue of `voice` at song time `t` (the fields RunEngine._chart_track_block gives).
func _cue(t: float, voice: String, pad := 1) -> Dictionary:
	return {"time": t, "end_time": t, "pad": pad, "voice": voice, "track_t": t + 100.0, "type": "tap"}


func _m() -> RunTrackMutes:
	var m := RunTrackMutes.new()
	m.setup(["drums", "bass"], BEAT, 8.0)
	return m


func _ev(kind: String, i: int, t: float) -> Dictionary:
	return {"kind": kind, "index": i, "time": t, "pad": 1}


func test_a_miss_mutes_the_voice_and_the_next_hit_restores_it() -> void:
	var notes := [_cue(1.0, "drums"), _cue(2.0, "drums"), _cue(2.5, "bass")]
	var m := _m()
	var ch := m.on_judge(_ev("miss", 0, 1.14), notes)
	assert_eq(ch.size(), 1)
	assert_eq(str(ch[0]["kind"]), "mute")
	assert_eq(str(ch[0]["voice"]), "drums")
	assert_eq(str(ch[0]["reason"]), "miss")
	assert_true(m.is_muted("drums"))
	assert_false(m.is_muted("bass"), "only that cue's voice")
	assert_eq(m.on_judge(_ev("perfect", 2, 2.5), notes), [], "a hit of another voice restores nothing")
	assert_true(m.is_muted("drums"))
	ch = m.on_judge(_ev("great", 1, 2.02), notes)
	assert_eq(ch.size(), 1)
	assert_eq(str(ch[0]["kind"]), "restore")
	assert_eq(str(ch[0]["reason"]), "hit")
	assert_false(m.is_muted("drums"))
	assert_eq(m.advance(100.0, notes), [], "no idle restore is left pending after a hit")


func test_a_hold_started_restores_and_a_hold_let_go_mutes() -> void:
	var notes := [_cue(1.0, "bass"), _cue(2.0, "bass")]
	var m := _m()
	m.on_judge(_ev("miss", 0, 1.14), notes)
	var ch := m.on_judge({"kind": "hold_start", "grade": "ok", "index": 1, "time": 2.05, "pad": 1}, notes)
	assert_eq(str(ch[0]["kind"]), "restore", "a hold started is a hit")
	ch = m.on_judge({"kind": "hold_partial", "index": 1, "time": 2.6, "pad": 1, "coverage": 0.4}, notes)
	assert_eq(ch.size(), 1)
	assert_eq(str(ch[0]["reason"]), "let_go")
	assert_true(m.is_muted("bass"))
	assert_eq(m.on_judge({"kind": "hold_complete", "index": 1, "time": 3.0, "pad": 1}, notes), [], "a hold kept changes nothing")


func test_a_muted_voice_comes_back_after_8_beats_when_no_cue_of_it_is_near() -> void:
	var notes := [_cue(1.0, "drums"), _cue(1.0 + 10.0 * BEAT, "drums")]
	var m := _m()
	m.on_judge(_ev("miss", 0, 1.14), notes)
	assert_eq(m.advance(1.14 + 8.0 * BEAT - 0.01, notes), [], "not before 8 beats")
	var ch := m.advance(1.14 + 8.0 * BEAT + 0.2, notes)
	assert_eq(ch.size(), 1)
	assert_eq(str(ch[0]["reason"]), "idle")
	assert_near(float(ch[0]["t"]), 1.14 + 8.0 * BEAT, 1e-9, "stamped at its deadline, whatever the frame")
	assert_false(m.is_muted("drums"))


func test_a_muted_voice_waits_for_a_hit_when_its_next_cue_is_within_8_beats() -> void:
	var notes := [_cue(1.0, "drums"), _cue(1.0 + 6.0 * BEAT, "drums")]
	var m := _m()
	m.on_judge(_ev("miss", 0, 1.14), notes)
	assert_eq(m.advance(50.0, notes), [], "a cue 6 beats on: only a hit brings it back")
	assert_true(m.is_muted("drums"))


func test_every_mute_restarts_the_wait_and_idle_restores_come_before_a_later_event() -> void:
	var notes := [_cue(1.0, "drums"), _cue(3.0, "drums"), _cue(20.0, "bass")]
	var m := _m()
	m.on_judge(_ev("miss", 0, 1.14), notes)
	m.on_judge(_ev("miss", 1, 3.14), notes)
	assert_eq(m.advance(1.14 + 8.0 * BEAT + 0.01, notes), [], "the second miss restarted the wait")
	var ch := m.on_judge(_ev("perfect", 2, 20.0), notes)  # (a bass hit long after: the drums' idle restore is made first, at its own time)
	assert_eq(ch.size(), 1)
	assert_eq(str(ch[0]["voice"]), "drums")
	assert_near(float(ch[0]["t"]), 3.14 + 8.0 * BEAT, 1e-9)


func test_backing_ordinary_cues_and_a_paused_hold_never_mute() -> void:
	var notes := [_cue(1.0, "backing"), {"time": 2.0, "end_time": 2.0, "pad": 1, "voice": "drums", "type": "tap"}, _cue(3.0, "drums")]
	var m := _m()
	assert_eq(m.on_judge(_ev("miss", 0, 1.14), notes), [], "backing is no voice")
	assert_eq(m.on_judge(_ev("miss", 1, 2.14), notes), [], "a loop cue (no track_t) is not the track's")
	m.ignore_let_go_at(3.3)
	assert_eq(m.on_judge({"kind": "hold_partial", "index": 2, "time": 3.3, "pad": 1}, notes), [], "the pause ended the hold")
	assert_eq(m.on_judge({"kind": "hold_partial", "index": 2, "time": 3.4, "pad": 1}, notes).size(), 1, "a real let-go still mutes")
	assert_eq(m.muted_keys(), ["drums"])
