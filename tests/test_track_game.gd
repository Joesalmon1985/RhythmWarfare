extends TestCase
## TrackGame and the focus logic on the fixture (120 BPM, so a beat is 0.5 s and the idle limit is 4 s). The fixture's
## focus: drums 0 to 4 s, lead 4 to 8 s, a gap to 9 s, bass 9 to 16 s. Its cues (pad):
##   drums: 1.0 (1 and 3 together), 1.5 (2), 2.0 (1), 2.5 (2), 3.0 (1 and 3), 3.5 (2)
##   lead:  4.5 (1), 5.0 (2), 5.5 (3), 6.0 (4), hold 6.5 to 7.9 (3), 7.0 (1), 7.5 (2)
##   bass:  9.5 (1), 10.0 (2), 10.5 (1), 11.0 (2), 11.5 (1), hold 12.0 to 13.0 (2), 13.5 (1), 14.0 (2), 14.5 (1), 15.0 (2)
## The accept window is 0.14 s, so a missed cue mutes at its time plus 0.14.

const WINDOW := 0.14


func _of_voice(voice: String) -> Callable:
	return func(c: Dictionary) -> bool: return c["voice"] == voice


func _events_for(g: TrackGame, kind: String, voice: String) -> Array:
	var out: Array = []
	for e in g.log:
		if e["kind"] == kind and e.get("voice", "") == voice:
			out.append(e)
	return out


func test_fixture_cue_counts() -> void:
	var g := TrackTestKit.game()
	assert_eq(g.cues.size(), 25)
	assert_eq(g.muted_keys(), [])
	assert_eq(g.voices.size(), 3)
	assert_eq(TrackTestKit.game("easy").cues.size(), 7)


# ---- focus state (plain logic, no game) ----

func _focus() -> TrackFocus:
	return TrackTestKit.fixture_pack().focus_state()


func test_focus_inside_a_stretch() -> void:
	var f := _focus()
	assert_eq(f.voice_at(2.0), "drums")
	assert_eq(f.voice_at(0.0), "drums", "a stretch includes its start")
	assert_eq(f.voice_at(4.0), "lead", "at a boundary the later stretch is current")
	assert_eq(f.voice_at(3.999), "drums")
	assert_eq(f.voice_at(12.0), "bass")
	assert_eq(f.next_stretch(2.0)["voice"], "lead")
	assert_near(f.beats_until_next(2.0), 4.0, 1e-9)
	assert_eq(f.stretch_at(5.0)["voice"], "lead")
	assert_eq(f.index_at(5.0), 1)


func test_focus_in_a_gap() -> void:
	var f := _focus()
	assert_eq(f.voice_at(8.0), "", "a stretch excludes its end")
	assert_eq(f.voice_at(8.5), "")
	assert_eq(f.stretch_at(8.5), {})
	assert_eq(f.next_stretch(8.5)["voice"], "bass")
	assert_near(f.beats_until_next(8.5), 1.0, 1e-9)
	var a := f.announcement(8.5)
	assert_true(bool(a["showing"]))
	assert_eq(a["voice"], "bass")
	assert_eq(a["count"], 1)


func test_focus_before_the_first_stretch_and_after_the_last() -> void:
	var f := _focus()
	assert_eq(f.voice_at(-1.0), "")
	assert_near(f.beats_until_next(-1.0), 2.0, 1e-9)
	var a := f.announcement(-1.0)
	assert_true(bool(a["showing"]), "the countdown shows what is first")
	assert_eq(a["voice"], "drums")
	assert_eq(a["count"], 2)
	assert_eq(f.voice_at(16.0), "")
	assert_eq(f.voice_at(20.0), "")
	assert_eq(f.next_stretch(15.0), {})
	assert_near(f.beats_until_next(15.0), -1.0, 1e-9)
	assert_false(bool(f.announcement(15.0)["showing"]), "nothing follows the last stretch")
	assert_false(bool(f.announcement(20.0)["showing"]))


func test_focus_announcement_starts_8_beats_ahead() -> void:
	var f := _focus()
	# the change from lead to bass (at 9.0, after a gap) is announced from 5.0
	assert_false(bool(f.announcement(4.0)["showing"]), "10 beats ahead")
	assert_false(bool(f.announcement(4.999)["showing"]), "just over 8 beats ahead")
	var a := f.announcement(5.0)
	assert_true(bool(a["showing"]), "exactly 8 beats ahead")
	assert_eq(a["voice"], "bass")
	assert_eq(a["count"], 8)
	assert_near(float(a["beats"]), 8.0, 1e-9)
	assert_eq(f.announcement(5.5)["count"], 7)
	assert_eq(f.announcement(5.6)["count"], 7, "a part beat counts as the whole beat still to go")
	assert_eq(f.announcement(7.9)["count"], 3)
	assert_eq(f.announcement(8.9)["count"], 1)
	# drums to lead (no gap, different voice): announced from 0.0 (4.0 - 8 beats)
	assert_true(bool(f.announcement(0.0)["showing"]))
	assert_eq(f.announcement(0.0)["voice"], "lead")
	assert_eq(f.announcement(0.0)["count"], 8)
	assert_eq(f.announcement(3.9)["count"], 1)
	assert_false(bool(f.announcement(4.0)["showing"]) and f.announcement(4.0)["voice"] == "lead", "the lead is current from 4.0")


func test_focus_same_voice_announces_only_after_a_gap() -> void:
	var f := TrackFocus.new()
	f.setup([{"start_s": 0.0, "end_s": 4.0, "voice": "a"}, {"start_s": 4.0, "end_s": 8.0, "voice": "a"}, {"start_s": 8.0, "end_s": 12.0, "voice": "b"}], 120.0)
	assert_false(bool(f.announcement(1.0)["showing"]), "the same voice carries straight on")
	assert_true(bool(f.announcement(5.0)["showing"]))
	assert_eq(f.announcement(5.0)["voice"], "b")
	assert_eq(f.announcement(5.0)["count"], 6)
	var g := TrackFocus.new()
	g.setup([{"start_s": 0.0, "end_s": 4.0, "voice": "a"}, {"start_s": 6.0, "end_s": 10.0, "voice": "a"}], 120.0)
	assert_false(bool(g.announcement(1.9)["showing"]), "more than 8 beats ahead")
	assert_true(bool(g.announcement(2.5)["showing"]), "the same voice again after a gap is still announced")
	assert_eq(g.announcement(2.5)["voice"], "a")
	assert_eq(g.announcement(2.5)["count"], 7)
	assert_false(bool(g.announcement(7.0)["showing"]))
	# the tempo sets the beat
	var h := TrackFocus.new()
	h.setup([{"start_s": 0.0, "end_s": 10.0, "voice": "a"}, {"start_s": 10.0, "end_s": 20.0, "voice": "b"}], 60.0)
	assert_near(h.beat_s(), 1.0, 1e-9)
	assert_false(bool(h.announcement(1.9)["showing"]))
	assert_true(bool(h.announcement(2.0)["showing"]))


func test_game_exposes_the_focus() -> void:
	var g := TrackTestKit.game()
	assert_eq(g.focus_voice(5.0), "lead")
	assert_eq(g.focus_voice(8.5), "")
	assert_eq(g.label_of("bass"), "Bass")


# ---- mutes: per voice, by the cue's voice ----

func test_a_missed_cue_mutes_that_cues_voice_at_cue_plus_window() -> void:
	var g := TrackTestKit.game()
	g.press(3, 1.0)  # the hat of the chord at 1.0 is played, the kick is not
	g.advance(1.0 + WINDOW - 0.001)
	assert_eq(g.muted_keys(), [], "still inside the window")
	g.advance(1.0 + WINDOW + 0.001)
	assert_eq(g.muted_keys(), ["drums"], "only the voice of the missed cue")
	var mutes := TrackTestKit.events_of(g, "mute")
	assert_eq(mutes.size(), 1)
	assert_near(float(mutes[0]["time"]), 1.0 + WINDOW, 1e-9)
	assert_eq(mutes[0]["voice"], "drums")
	assert_eq(mutes[0]["reason"], "miss")
	assert_eq(TrackTestKit.events_of(g, "miss").size(), 1)
	assert_true(g.is_muted("drums") and not g.is_muted("lead") and not g.is_muted("bass"))
	assert_false(g.is_muted("no_such_voice"))


func test_a_hit_on_any_pad_for_the_voice_restores_it() -> void:
	# restored by the snare cue (pad 2)
	var g := TrackTestKit.game()
	g.advance(1.2)  # the chord at 1.0 missed: drums muted
	assert_eq(g.muted_keys(), ["drums"])
	var r := g.press(2, 1.5)
	assert_eq(r["kind"], "perfect")
	assert_eq(g.muted_keys(), [], "a hit restores")
	var restores := TrackTestKit.events_of(g, "restore")
	assert_eq(restores.size(), 1)
	assert_near(float(restores[0]["time"]), 1.5, 1e-9)
	assert_eq(restores[0]["reason"], "hit")
	assert_eq(restores[0]["voice"], "drums")
	assert_eq(TrackTestKit.events_of(g, "hit")[0]["grade"], "perfect")
	# restored by the hat cue (pad 3), after the kick and snare cues before it were missed
	var h := TrackTestKit.game()
	h.advance(2.9)
	assert_true(h.is_muted("drums"))
	assert_eq(h.press(3, 3.0)["kind"], "perfect")
	assert_false(h.is_muted("drums"))
	# restored by the kick cue (pad 1)
	var k := TrackTestKit.game()
	k.advance(1.9)
	assert_eq(k.press(1, 2.0)["kind"], "perfect")
	assert_false(k.is_muted("drums"))


func test_a_late_hit_still_restores_and_grades() -> void:
	var g := TrackTestKit.game()
	g.advance(1.5)
	assert_true(g.is_muted("drums"))
	var r := g.press(1, 2.0 + 0.1)  # great or ok: still a hit
	assert_true(r["kind"] in ["great", "ok"], str(r["kind"]))
	assert_false(g.is_muted("drums"))


func test_a_wrong_pad_press_does_not_play_the_cue() -> void:
	var g := TrackTestKit.game()
	# the cues at 1.0 are on pads 1 and 3; pad 4 is the wrong pad and pad 2 has nothing near
	assert_eq(g.press(4, 1.0)["kind"], "stray")
	assert_eq(g.press(2, 1.02)["kind"], "stray")
	assert_eq(g.total_hits(), 0)
	assert_eq(g.total_strays(), 2)
	g.advance(1.0 + WINDOW - 0.001)
	assert_eq(g.muted_keys(), [], "the cues are still open until their window closes")
	g.advance(1.0 + WINDOW + 0.001)
	assert_eq(g.total_misses(), 2, "both cues of the chord were missed")
	assert_eq(g.muted_keys(), ["drums"])
	# a wrong pad near a lone cue does not restore a silent voice either
	g.press(3, 1.5)  # the snare cue at 1.5 is pad 2
	assert_true(g.is_muted("drums"))
	assert_eq(g.press(2, 1.5)["kind"], "perfect", "the right pad does")
	assert_false(g.is_muted("drums"))


func test_a_press_with_no_cue_near_costs_nothing() -> void:
	var g := TrackTestKit.game()
	assert_eq(g.press(2, 0.3)["kind"], "stray", "nothing cued yet")
	g.press(1, 1.0)
	g.press(3, 1.0)
	assert_eq(g.press(1, 1.25)["kind"], "stray", "a quarter of a second from the nearest cue")
	assert_eq(g.muted_keys(), [])
	assert_eq(g.total_misses(), 0)
	assert_eq(g.total_hits(), 2)
	assert_eq(TrackTestKit.events_of(g, "stray").size(), 2)
	var gap := TrackTestKit.game("", 8.2)
	assert_eq(gap.press(4, 8.5)["kind"], "stray", "in the gap")
	assert_eq(gap.muted_keys(), [])
	assert_eq(gap.total_strays(), 1)
	# a stray on a muted voice does not bring it back, and strays alone mute nothing
	var m := TrackTestKit.game()
	m.advance(1.2)
	assert_eq(m.muted_keys(), ["drums"])
	m.press(4, 1.25)
	assert_true(m.is_muted("drums"), "a stray does not bring a voice back")
	var clean := TrackTestKit.game()
	for t in [0.2, 0.4, 0.6, 0.8]:
		clean.press(1, t)
		clean.press(3, t + 0.05)
	assert_eq(clean.muted_keys(), [])
	assert_eq(clean.total_strays(), 8)


func test_a_voice_that_is_not_the_focus_is_never_muted() -> void:
	# miss everything the drums are asked to play, play every other cue perfectly: only the drums ever go silent
	var g := TrackTestKit.run(TrackTestKit.game(), "perfect", 5.0, 1.0 / 60.0, _of_voice("drums"))
	assert_eq(g.muted_keys(), ["drums"], "during the lead stretch only the drums are silent (and not by the lead)")
	TrackTestKit.run(g, "perfect", 16.0, 1.0 / 60.0, _of_voice("drums"))
	g.finish(16.0)
	assert_eq(_events_for(g, "mute", "lead").size(), 0)
	assert_eq(_events_for(g, "mute", "bass").size(), 0)
	assert_eq(TrackTestKit.voice(g.summary(), "lead")["sounding_share"], 1.0)
	assert_eq(TrackTestKit.voice(g.summary(), "bass")["sounding_share"], 1.0)
	# in any run, every mute is caused by a cue of that same voice
	for policy in ["none", "accuracy:0.5", "accuracy:0.8"]:
		var r := TrackTestKit.run(TrackTestKit.game(), policy, 16.0)
		r.finish(16.0)
		for e in r.log:
			if e["kind"] == "mute":
				assert_eq(r.cues[int(_miss_or_letgo_cue(r, e))]["voice"], e["voice"], "%s: a mute comes from the voice's own cue" % policy)
			if e["kind"] in ["hit", "miss"]:
				assert_eq(r.cues[int(e["cue"])]["voice"], e["voice"], "%s: the event names the cue's voice" % policy)


## The cue behind a mute event: the miss or let-go event at the same time and voice.
func _miss_or_letgo_cue(g: TrackGame, mute: Dictionary) -> int:
	for e in g.log:
		if e["kind"] in ["miss", "hold_let_go"] and e["voice"] == mute["voice"] and float(e["time"]) == float(mute["time"]):
			return int(e["cue"])
	fail("no miss behind the mute at %f" % float(mute["time"]))
	return 0


func test_backing_never_mutes() -> void:
	var g := TrackTestKit.game()
	TrackTestKit.run(g, "none", 16.0)
	g.finish(16.0)
	for e in g.log:
		assert_true(e.get("voice", "drums") != "backing", "no event for the backing")
	assert_false("backing" in g.muted_keys())
	assert_eq(g.voices.size(), 3, "backing is not one of the game's voices")


# ---- holds ----

func test_a_hold_let_go_early_mutes_and_a_kept_hold_does_not() -> void:
	# let go: the lead's hold 6.5 to 7.9 released at 6.8
	var g := TrackTestKit.game("", 6.4)
	g.press(3, 6.5)
	assert_eq(g.press(3, 6.5)["kind"], "ignored", "a second press on a held pad is ignored")
	g.release(3, 6.8)
	assert_true(g.is_muted("lead"), "let go early")
	var mute: Dictionary = _events_for(g, "mute", "lead")[0]
	assert_near(float(mute["time"]), 6.8, 1e-9)
	assert_eq(mute["reason"], "let_go")
	assert_eq(_events_for(g, "hold_let_go", "lead").size(), 1)
	assert_eq(_events_for(g, "hit", "lead").size(), 1, "a hold let go is a hit plus a let go, not a miss")
	assert_eq(g.total_misses(), 0)
	# kept to the tail
	var k := TrackTestKit.game("", 6.4)
	k.press(3, 6.5)
	k.press(1, 7.0)
	k.press(2, 7.5)
	k.release(3, 7.9)
	k.advance(8.0)
	assert_false(k.is_muted("lead"), "a hold kept to its tail")
	assert_eq(_events_for(k, "hold_kept", "lead").size(), 1)
	assert_eq(_events_for(k, "mute", "lead").size(), 0)
	# kept by never letting go: the tail completes it
	var h := TrackTestKit.game("", 6.4)
	h.press(3, 6.5)
	h.press(1, 7.0)
	h.press(2, 7.5)
	h.advance(8.0)
	assert_false(h.is_muted("lead"))
	assert_eq(_events_for(h, "hold_kept", "lead").size(), 1)
	# released within the tolerance of the tail (0.1 s early) still counts as kept
	var n := TrackTestKit.game("", 6.4)
	n.press(3, 6.5)
	n.press(1, 7.0)
	n.press(2, 7.5)
	n.release(3, 7.8)
	assert_false(n.is_muted("lead"))


func test_a_let_go_hold_restores_on_the_next_hit() -> void:
	var g := TrackTestKit.game("", 6.4)
	g.press(3, 6.5)
	g.release(3, 6.8)
	assert_true(g.is_muted("lead"))
	g.press(1, 7.0)  # the lead's next cue
	assert_false(g.is_muted("lead"))
	assert_eq(_events_for(g, "restore", "lead")[0]["reason"], "hit")


func test_a_missed_hold_mutes_like_a_missed_tap() -> void:
	var g := TrackTestKit.game("", 6.4)
	g.advance(6.5 + WINDOW + 0.001)
	assert_true(g.is_muted("lead"))
	assert_near(float(_events_for(g, "mute", "lead")[0]["time"]), 6.64, 1e-9)


func test_pause_does_not_mute_a_hold_in_progress() -> void:
	var g := TrackTestKit.game("", 6.4)
	g.press(3, 6.5)
	g.pause(6.8)
	assert_false(g.is_muted("lead"), "a pause is not a mistake")
	assert_false(g.judge.is_holding(3))


# ---- the idle restore, per voice ----

func test_idle_restore_after_the_focus_has_moved_on() -> void:
	# the last drums cue (3.5) is missed: muted at 3.64 just before the focus moves to the lead at 4.0; the drums have no
	# cue left, so they come back 8 beats (4 s) after the mute, at 7.64, while the lead is the focus
	var g := TrackTestKit.game()
	TrackTestKit.run(g, "perfect", 7.63, 1.0 / 60.0, func(c: Dictionary) -> bool: return c["voice"] == "drums" and c["t"] == 3.5)
	assert_true(g.is_muted("drums"), "still muted just before the idle limit")
	assert_eq(g.focus_voice(7.63), "lead")
	g.advance(7.65)
	assert_false(g.is_muted("drums"))
	var restore: Dictionary = _events_for(g, "restore", "drums")[0]
	assert_near(float(restore["time"]), 3.5 + WINDOW + 4.0, 1e-9)
	assert_eq(restore["reason"], "idle")
	# the restore time does not depend on how coarse the frames are
	var coarse := TrackTestKit.game()
	TrackTestKit.run(coarse, "perfect", 9.5, 0.7, func(c: Dictionary) -> bool: return c["voice"] == "drums" and c["t"] == 3.5)
	assert_near(float(_events_for(coarse, "restore", "drums")[0]["time"]), 7.64, 1e-9)


func test_idle_restore_works_per_voice_when_two_voices_are_silent() -> void:
	# drums silent from 3.64 (back at 7.64), lead silent from its last cue 7.5 + 0.14 (back at 11.64): each on its own clock
	var g := TrackTestKit.game()
	TrackTestKit.run(g, "perfect", 16.0, 1.0 / 60.0, func(c: Dictionary) -> bool: return (c["voice"] == "drums" and c["t"] == 3.5) or (c["voice"] == "lead" and c["t"] == 7.5))
	assert_near(float(_events_for(g, "restore", "drums")[0]["time"]), 7.64, 1e-9)
	assert_near(float(_events_for(g, "restore", "lead")[0]["time"]), 11.64, 1e-9)
	assert_eq(_events_for(g, "mute", "bass").size(), 0)
	assert_eq(g.muted_keys(), [])


func test_no_idle_restore_when_the_voices_next_cue_is_near() -> void:
	# miss the kick at 2.0: the next drums cue (2.5) is half a second away, so the voice stays muted until it is hit
	var g := TrackTestKit.game()
	TrackTestKit.run(g, "perfect", 2.4, 1.0 / 60.0, func(c: Dictionary) -> bool: return c["voice"] == "drums" and c["t"] == 2.0)
	assert_true(g.is_muted("drums"))
	assert_eq(TrackTestKit.events_of(g, "restore").size(), 0)
	g.press(2, 2.5)
	assert_false(g.is_muted("drums"))
	assert_eq(TrackTestKit.events_of(g, "restore")[0]["reason"], "hit")


func test_idle_restore_with_a_shorter_limit() -> void:
	# a pack with a 2 beat idle limit (1 s): miss the last bass cue at 15.0 and it comes back at 16.14
	var p := TrackTestKit.fixture_pack()
	p.restore_after_idle_beats = 2.0
	var g := TrackTestKit.game("", 0.0, p)
	TrackTestKit.run(g, "perfect", 11.0, 1.0 / 60.0, func(c: Dictionary) -> bool: return c["voice"] == "drums" and c["t"] == 3.5)
	assert_near(float(_events_for(g, "restore", "drums")[0]["time"]), 3.64 + 1.0, 1e-9)


func test_a_second_miss_while_muted_moves_the_idle_deadline() -> void:
	# miss the drums cues at 3.0 (two) and 3.5: the mute at 3.14 has cues near, the miss at 3.64 starts the 4 s wait
	var g := TrackTestKit.game()
	TrackTestKit.run(g, "perfect", 8.0, 1.0 / 60.0, func(c: Dictionary) -> bool: return c["voice"] == "drums" and c["t"] >= 3.0)
	assert_eq(_events_for(g, "mute", "drums").size(), 1)
	assert_near(float(_events_for(g, "restore", "drums")[0]["time"]), 3.64 + 4.0, 1e-9)


# ---- statistics ----

func test_perfect_autoplay_hits_everything_and_mutes_nothing() -> void:
	var g := TrackTestKit.game()
	TrackTestKit.run(g, "perfect", 16.0)
	g.finish(16.0)
	var s := g.summary()
	assert_eq(s["cues"], 25)
	assert_eq(s["hits"], 25)
	assert_eq(s["misses"], 0)
	assert_eq(s["strays"], 0)
	assert_eq(TrackTestKit.events_of(g, "mute").size(), 0)
	assert_eq(TrackTestKit.events_of(g, "restore").size(), 0)
	for v in s["voices"]:
		assert_eq(v["sounding_share"], 1.0, str(v["key"]))
		assert_eq(v["muted_s"], 0.0)
		assert_eq(v["hits"]["perfect"], v["cues"], "every hit perfect: %s" % v["key"])
	assert_eq(TrackTestKit.events_of(g, "hold_kept").size(), 2, "both holds kept")
	assert_eq(TrackTestKit.voice(s, "drums")["cues"], 8)
	assert_eq(TrackTestKit.voice(s, "lead")["cues"], 7)
	assert_eq(TrackTestKit.voice(s, "bass")["cues"], 10)
	assert_eq(TrackTestKit.voice(s, "lead")["holds"], 1)
	assert_eq(TrackTestKit.voice(s, "lead")["kind"], "pitched")


func test_playing_nothing_gives_the_hand_worked_muted_share_per_voice() -> void:
	# a voice is silent from its first cue + 0.14 s until its idle restore after the last miss
	#  drums: 1.14 to 7.64 (last cue 3.5, so back 4 s after 3.64): 6.5 s silent
	#  lead:  4.64 to 11.64 (last cue 7.5, back 4 s after 7.64): 7.0 s silent
	#  bass:  9.64 to the end (last cue 15.0, the restore would be at 19.14): 6.36 s silent
	for policy in ["none", "accuracy:0"]:
		var g := TrackTestKit.run(TrackTestKit.game(), policy, 16.0)
		g.finish(16.0)
		var s := g.summary()
		assert_eq(s["hits"], 0, policy)
		assert_eq(s["misses"], 25, policy)
		assert_near(float(TrackTestKit.voice(s, "drums")["muted_s"]), 6.5, 0.002, policy)
		assert_near(float(TrackTestKit.voice(s, "lead")["muted_s"]), 7.0, 0.002, policy)
		assert_near(float(TrackTestKit.voice(s, "bass")["muted_s"]), 6.36, 0.002, policy)
		assert_near(float(TrackTestKit.voice(s, "drums")["sounding_share"]), 1.0 - 6.5 / 16.0, 0.0002, policy)
		assert_near(float(TrackTestKit.voice(s, "lead")["sounding_share"]), 1.0 - 7.0 / 16.0, 0.0002, policy)
		assert_near(float(TrackTestKit.voice(s, "bass")["sounding_share"]), 1.0 - 6.36 / 16.0, 0.0002, policy)
		assert_eq(g.muted_keys(), ["bass"], "only the bass is still silent at the end: %s" % policy)


func test_summary_numbers_add_up() -> void:
	var g := TrackTestKit.run(TrackTestKit.game(), "accuracy:0.5", 16.0)
	g.press(1, 0.3)  # a stray
	g.finish(16.0)
	var s := g.summary()
	var cues := 0
	var hits := 0
	var misses := 0
	for v in s["voices"]:
		var grades: int = int(v["hits"]["perfect"]) + int(v["hits"]["great"]) + int(v["hits"]["ok"])
		assert_eq(grades, v["hit_total"], "grades add up: %s" % v["key"])
		assert_eq(int(v["hit_total"]) + int(v["misses"]), int(v["cues"]), "every cue hit or missed: %s" % v["key"])
		assert_true(float(v["sounding_share"]) >= 0.0 and float(v["sounding_share"]) <= 1.0)
		cues += int(v["cues"])
		hits += int(v["hit_total"])
		misses += int(v["misses"])
	assert_eq(cues, s["cues"])
	assert_eq(hits, s["hits"])
	assert_eq(misses, s["misses"])
	assert_eq(cues, 25)
	assert_eq(s["strays"], 1)
	assert_true(hits > 0 and misses > 0, "a half-accurate run has both")
	# muted seconds agree with the event log, voice by voice
	var muted_by_voice := {}
	var since := {}
	for e in g.log:
		if e["kind"] == "mute":
			since[e["voice"]] = float(e["time"])
		elif e["kind"] == "restore":
			muted_by_voice[e["voice"]] = float(muted_by_voice.get(e["voice"], 0.0)) + float(e["time"]) - float(since[e["voice"]])
			since.erase(e["voice"])
	for voice in since:
		muted_by_voice[voice] = float(muted_by_voice.get(voice, 0.0)) + 16.0 - float(since[voice])
	for v in s["voices"]:
		var m: float = float(muted_by_voice.get(v["key"], 0.0))
		assert_near(float(v["muted_s"]), m, 0.002, str(v["key"]))
		assert_near(float(v["sounding_share"]), 1.0 - m / 16.0, 0.0002)


func test_same_inputs_same_event_log_at_any_frame_rate() -> void:
	var a := TrackTestKit.run(TrackTestKit.game(), "accuracy:0.6", 16.0, 1.0 / 60.0)
	var b := TrackTestKit.run(TrackTestKit.game(), "accuracy:0.6", 16.0, 1.0 / 60.0)
	var c := TrackTestKit.run(TrackTestKit.game(), "accuracy:0.6", 16.0, 1.0 / 23.0)
	var d := TrackTestKit.run(TrackTestKit.game(), "accuracy:0.6", 16.0, 0.9)
	assert_true(a.log.size() > 20)
	assert_eq(a.log, b.log, "the same run twice")
	assert_eq(a.log, c.log, "a different frame rate")
	assert_eq(a.log, d.log, "very coarse frames")


func test_start_part_way_skips_earlier_cues_without_missing_them() -> void:
	var g := TrackTestKit.game("", 5.0)
	var expected := 0
	for c in TrackTestKit.fixture_pack().charts["normal"]:
		if float(c["t"]) >= 5.0:
			expected += 1
	assert_eq(g.cues.size(), expected)
	assert_eq(expected, 16)
	g.advance(5.0)
	g.advance(5.1)
	assert_eq(g.total_misses(), 0, "nothing before the start is missed")
	assert_eq(g.muted_keys(), [], "nothing muted by the skipped cues")
	TrackTestKit.run(g, "none", 16.0)
	g.finish(16.0)
	var s := g.summary()
	assert_eq(s["misses"], expected)
	assert_eq(s["cues"], expected)
	assert_near(float(s["start_s"]), 5.0, 1e-9)
	# the sounding share is over the time played (5 to 16 s): the lead is silent 5.14 to 11.64
	assert_near(float(TrackTestKit.voice(s, "lead")["sounding_share"]), 1.0 - (11.64 - 5.14) / 11.0, 0.0003)
	assert_eq(TrackTestKit.voice(s, "drums")["sounding_share"], 1.0, "the drums have no cues after 5 s")
	var p := TrackTestKit.run(TrackTestKit.game("", 5.0), "perfect", 16.0)
	p.finish(16.0)
	assert_eq(p.summary()["hits"], expected)


func test_chart_choice() -> void:
	var g := TrackTestKit.game("easy")
	assert_eq(g.chart_name, "easy")
	TrackTestKit.run(g, "perfect", 16.0)
	g.finish(16.0)
	assert_eq(g.summary()["hits"], 7)
	assert_eq(TrackTestKit.game().chart_name, "normal", "the default chart when none is named")
