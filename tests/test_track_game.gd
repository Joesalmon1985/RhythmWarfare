extends TestCase
## TrackGame on the fixture (120 BPM, so a beat is 0.5 s and the idle limit is 4 s). The fixture's cues, by pad:
##   1 drums: 1 2 3 4 6 7 8 9 10        2 lead: 1.5 2.5 3.5, hold 4.5 to 5.5, 6.5 7.5 8.5 9.5
##   3 pads:  1 2, hold 3 to 4, 10      4 bass: 1.5 2.5 4.5 5.5 6.5 7.5 8.5 9.5
## The accept window is 0.14 s, so a missed cue mutes at its time plus 0.14.

const WINDOW := 0.14


func _kinds(events: Array) -> Array:
	var out: Array = []
	for e in events:
		out.append(e["kind"])
	return out


func test_fixture_cue_counts() -> void:
	var g := TrackTestKit.game()
	assert_eq(g.cues.size(), 29)
	assert_eq(g.muted_keys(), [])
	assert_eq(TrackTestKit.game("easy").cues.size(), 6)


func test_a_missed_cue_mutes_that_voice_at_cue_plus_window_and_no_other() -> void:
	var g := TrackTestKit.game()
	g.press(3, 1.0)  # the pads cue of the chord is hit, the drums cue is not
	g.advance(1.0 + WINDOW - 0.001)
	assert_eq(g.muted_keys(), [], "still inside the window")
	g.advance(1.0 + WINDOW + 0.001)
	assert_eq(g.muted_keys(), ["drums"], "only the voice that missed")
	var mutes := TrackTestKit.events_of(g, "mute")
	assert_eq(mutes.size(), 1)
	assert_near(float(mutes[0]["time"]), 1.0 + WINDOW, 1e-9)
	assert_eq(mutes[0]["voice"], "drums")
	assert_eq(mutes[0]["reason"], "miss")
	assert_eq(TrackTestKit.events_of(g, "miss").size(), 1)
	assert_true(g.is_muted(1) and not g.is_muted(2) and not g.is_muted(3) and not g.is_muted(4))


func test_the_next_hit_restores_the_voice() -> void:
	var g := TrackTestKit.game()
	g.press(3, 1.0)
	g.press(2, 1.5)
	g.press(4, 1.5)
	g.advance(1.9)
	assert_eq(g.muted_keys(), ["drums"])
	var r := g.press(1, 2.0)  # the drums' next cue
	assert_eq(r["kind"], "perfect")
	assert_eq(g.muted_keys(), [], "hit restores")
	var restores := TrackTestKit.events_of(g, "restore")
	assert_eq(restores.size(), 1)
	assert_near(float(restores[0]["time"]), 2.0, 1e-9)
	assert_eq(restores[0]["reason"], "hit")
	var hit: Dictionary = TrackTestKit.events_of(g, "hit", 1)[0]
	assert_eq(hit["grade"], "perfect")


func test_a_late_hit_still_restores_and_grades() -> void:
	var g := TrackTestKit.game()
	g.press(3, 1.0)
	g.advance(1.5)  # drums missed at 1.14
	assert_true(g.is_muted(1))
	var r := g.press(1, 2.0 + 0.1)  # great or ok: still a hit
	assert_true(r["kind"] in ["great", "ok"], str(r["kind"]))
	assert_false(g.is_muted(1))


func test_a_hold_let_go_early_mutes_and_a_kept_hold_does_not() -> void:
	# let go: the lead's hold 4.5 to 5.5 released at 4.8
	var g := TrackTestKit.game("", 4.4)
	g.press(2, 4.5)
	assert_eq(g.press(2, 4.5)["kind"], "ignored", "a second press on a held pad is ignored")
	g.release(2, 4.8)
	assert_true(g.is_muted(2), "let go early")
	var mute: Dictionary = TrackTestKit.events_of(g, "mute", 2)[0]
	assert_near(float(mute["time"]), 4.8, 1e-9)
	assert_eq(mute["reason"], "let_go")
	assert_eq(TrackTestKit.events_of(g, "hold_let_go", 2).size(), 1)
	# kept to the tail
	var k := TrackTestKit.game("", 4.4)
	k.press(2, 4.5)
	k.release(2, 5.5)
	k.advance(5.6)
	assert_false(k.is_muted(2), "a hold kept to its tail")
	assert_eq(TrackTestKit.events_of(k, "hold_kept", 2).size(), 1)
	assert_eq(TrackTestKit.events_of(k, "mute", 2).size(), 0)
	# kept by never letting go: the tail completes it
	var h := TrackTestKit.game("", 4.4)
	h.press(2, 4.5)
	h.advance(5.6)
	assert_false(h.is_muted(2))
	assert_eq(TrackTestKit.events_of(h, "hold_kept", 2).size(), 1)
	# released within the tolerance of the tail (0.1 s early) still counts as kept
	var n := TrackTestKit.game("", 4.4)
	n.press(2, 4.5)
	n.release(2, 5.4)
	assert_false(n.is_muted(2))


func test_a_let_go_hold_restores_on_the_next_hit() -> void:
	var g := TrackTestKit.game("", 4.4)
	g.press(2, 4.5)
	g.release(2, 4.8)
	assert_true(g.is_muted(2))
	g.press(2, 6.5)
	assert_false(g.is_muted(2))
	assert_eq(TrackTestKit.events_of(g, "restore", 2)[0]["reason"], "hit")


func test_a_missed_hold_mutes_like_a_missed_tap() -> void:
	var g := TrackTestKit.game("", 4.4)
	g.advance(4.5 + WINDOW + 0.001)
	assert_true(g.is_muted(2))
	assert_near(float(TrackTestKit.events_of(g, "mute", 2)[0]["time"]), 4.64, 1e-9)


func test_idle_restore_fires_at_the_right_time_and_not_before() -> void:
	# miss the pads' hold at 3.0: muted at 3.14; the next pads cue is at 10.0, 6.86 s (13.7 beats) away, so it comes back
	# 8 beats (4 s) after the mute, at 7.14
	var g := TrackTestKit.game()
	TrackTestKit.run(g, "perfect", 7.13, 1.0 / 60.0, func(c: Dictionary) -> bool: return c["pad"] == 3 and c["t"] == 3.0)
	assert_true(g.is_muted(3), "still muted just before the idle limit")
	g.advance(7.15)
	assert_false(g.is_muted(3))
	var restore: Dictionary = TrackTestKit.events_of(g, "restore", 3)[0]
	assert_near(float(restore["time"]), 3.0 + WINDOW + 4.0, 1e-9)
	assert_eq(restore["reason"], "idle")
	# the restore time does not depend on how coarse the frames are
	var coarse := TrackTestKit.game()
	TrackTestKit.run(coarse, "perfect", 9.5, 0.7, func(c: Dictionary) -> bool: return c["pad"] == 3 and c["t"] == 3.0)
	assert_near(float(TrackTestKit.events_of(coarse, "restore", 3)[0]["time"]), 7.14, 1e-9)


func test_no_idle_restore_when_the_next_cue_is_near() -> void:
	# miss the pads cue at 2.0: the next one (the hold at 3.0) is 1 s away, so the voice stays muted until it is hit
	var g := TrackTestKit.game()
	TrackTestKit.run(g, "perfect", 2.9, 1.0 / 60.0, func(c: Dictionary) -> bool: return c["pad"] == 3 and c["t"] == 2.0)
	assert_true(g.is_muted(3))
	assert_eq(TrackTestKit.events_of(g, "restore", 3).size(), 0)
	g.press(3, 3.0)
	assert_false(g.is_muted(3))
	assert_eq(TrackTestKit.events_of(g, "restore", 3)[0]["reason"], "hit")


func test_idle_restore_with_no_cue_left() -> void:
	# a pack with a 2 beat idle limit (1 s): miss the last pads cue at 10.0 and it comes back at 11.14
	var p := TrackTestKit.fixture_pack()
	p.restore_after_idle_beats = 2.0
	var g := TrackTestKit.game("", 0.0, p)
	TrackTestKit.run(g, "perfect", 11.1, 1.0 / 60.0, func(c: Dictionary) -> bool: return c["pad"] == 3 and c["t"] == 10.0)
	assert_true(g.is_muted(3))
	g.advance(11.2)
	assert_false(g.is_muted(3))
	assert_near(float(TrackTestKit.events_of(g, "restore", 3)[0]["time"]), 11.14, 1e-9)


func test_a_second_miss_while_muted_moves_the_idle_deadline() -> void:
	# miss the pads cues at 2.0 and the hold at 3.0: the mute at 2.14 has the 3.0 cue near, the miss at 3.14 starts the 4 s wait
	var g := TrackTestKit.game()
	TrackTestKit.run(g, "perfect", 8.0, 1.0 / 60.0, func(c: Dictionary) -> bool: return c["pad"] == 3 and c["t"] in [2.0, 3.0])
	assert_eq(TrackTestKit.events_of(g, "mute", 3).size(), 1)
	assert_near(float(TrackTestKit.events_of(g, "restore", 3)[0]["time"]), 3.14 + 4.0, 1e-9)


func test_backing_never_mutes() -> void:
	var g := TrackTestKit.game()
	TrackTestKit.run(g, "none", 12.0)
	g.finish(12.0)
	for e in g.log:
		assert_true(e.get("voice", "drums") != "backing", "no event for the backing")
	assert_false("backing" in g.muted_keys())
	assert_eq(g.voices.size(), 4, "backing is not one of the game's voices")


func test_stray_presses_cost_nothing() -> void:
	var g := TrackTestKit.game()
	assert_eq(g.press(2, 0.3)["kind"], "stray", "nothing cued yet")
	g.press(1, 1.0)
	g.press(3, 1.0)
	assert_eq(g.press(1, 1.5)["kind"], "stray", "half a second from the nearest drums cue")
	assert_eq(g.muted_keys(), [])
	assert_eq(g.total_misses(), 0)
	assert_eq(g.total_hits(), 2)
	assert_eq(TrackTestKit.events_of(g, "stray").size(), 2)
	# a stray on a muted pad does not restore it, and none of it mutes anything by itself
	var m := TrackTestKit.game()
	m.advance(1.2)  # drums and pads missed at 1.14
	assert_eq(m.muted_keys(), ["drums", "pads"])
	m.press(1, 1.5)
	assert_true(m.is_muted(1), "a stray does not bring a voice back")
	var clean := TrackTestKit.game()
	for t in [0.2, 0.4, 0.6, 0.8]:
		clean.press(1, t)
		clean.press(3, t + 0.05)
	assert_eq(clean.muted_keys(), [])
	assert_eq(clean.total_strays(), 8)


func test_perfect_autoplay_hits_everything_and_mutes_nothing() -> void:
	var g := TrackTestKit.game()
	TrackTestKit.run(g, "perfect", 12.0)
	g.finish(12.0)
	var s := g.summary()
	assert_eq(s["cues"], 29)
	assert_eq(s["hits"], 29)
	assert_eq(s["misses"], 0)
	assert_eq(TrackTestKit.events_of(g, "mute").size(), 0)
	assert_eq(TrackTestKit.events_of(g, "restore").size(), 0)
	for v in s["voices"]:
		assert_eq(v["sounding_share"], 1.0, str(v["key"]))
		assert_eq(v["hits"]["perfect"], v["cues"], "every hit perfect: %s" % v["key"])
	assert_eq(TrackTestKit.events_of(g, "hold_kept").size(), 2, "both holds kept")


func test_missing_everything_mutes_every_voice_for_the_expected_share() -> void:
	# hand-worked: a voice is silent from its first cue + 0.14 s. Drums, lead and bass never have a gap over 4 s, so they
	# stay silent to 12 s; the pads rest 4 to 10 s: muted 1.14 to 7.14 (the idle restore after the 3.0 hold is missed),
	# sounding again to 10.14, then muted to the end.
	for policy in ["none", "accuracy:0"]:
		var g := TrackTestKit.run(TrackTestKit.game(), policy, 12.0)
		g.finish(12.0)
		var s := g.summary()
		assert_eq(s["hits"], 0, policy)
		assert_eq(s["misses"], 29, policy)
		assert_near(float(TrackTestKit.voice(s, "drums")["sounding_share"]), 1.0 - (12.0 - 1.14) / 12.0, 0.0002, policy)
		assert_near(float(TrackTestKit.voice(s, "lead")["sounding_share"]), 1.0 - (12.0 - 1.64) / 12.0, 0.0002, policy)
		assert_near(float(TrackTestKit.voice(s, "bass")["sounding_share"]), 1.0 - (12.0 - 1.64) / 12.0, 0.0002, policy)
		assert_near(float(TrackTestKit.voice(s, "pads")["sounding_share"]), 1.0 - ((7.14 - 1.14) + (12.0 - 10.14)) / 12.0, 0.0002, policy)
		assert_eq(g.muted_keys().size(), 4, "every voice ends muted: %s" % policy)


func test_summary_numbers_add_up() -> void:
	var g := TrackTestKit.run(TrackTestKit.game(), "accuracy:0.5", 12.0)
	g.finish(12.0)
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
	assert_eq(cues, 29)
	assert_true(hits > 0 and misses > 0, "a half-accurate run has both")
	# muted seconds agree with the event log
	var muted_by_pad := {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
	var since := {}
	for e in g.log:
		if e["kind"] == "mute":
			since[e["pad"]] = float(e["time"])
		elif e["kind"] == "restore":
			muted_by_pad[e["pad"]] += float(e["time"]) - float(since[e["pad"]])
			since.erase(e["pad"])
	for pad in since:
		muted_by_pad[pad] += 12.0 - float(since[pad])
	for v in s["voices"]:
		assert_near(float(v["muted_s"]), muted_by_pad[int(v["pad"])], 0.002, str(v["key"]))
		assert_near(float(v["sounding_share"]), 1.0 - muted_by_pad[int(v["pad"])] / 12.0, 0.0002)


func test_same_inputs_same_event_log_at_any_frame_rate() -> void:
	var a := TrackTestKit.run(TrackTestKit.game(), "accuracy:0.6", 12.0, 1.0 / 60.0)
	var b := TrackTestKit.run(TrackTestKit.game(), "accuracy:0.6", 12.0, 1.0 / 60.0)
	var c := TrackTestKit.run(TrackTestKit.game(), "accuracy:0.6", 12.0, 1.0 / 23.0)
	var d := TrackTestKit.run(TrackTestKit.game(), "accuracy:0.6", 12.0, 0.9)
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
	assert_true(expected < 29 and expected > 0)
	g.advance(5.0)
	g.advance(5.4)
	assert_eq(g.total_misses(), 0, "nothing before the start is missed")
	assert_eq(g.muted_keys(), [], "nothing muted by the skipped cues")
	TrackTestKit.run(g, "none", 12.0)
	g.finish(12.0)
	var s := g.summary()
	assert_eq(s["misses"], expected)
	assert_eq(s["cues"], expected)
	assert_near(float(s["start_s"]), 5.0, 1e-9)
	# the sounding share is over the time played (5 to 12 s)
	assert_near(float(TrackTestKit.voice(s, "drums")["sounding_share"]), 1.0 - (12.0 - 6.14) / 7.0, 0.0003)
	var p := TrackTestKit.run(TrackTestKit.game("", 5.0), "perfect", 12.0)
	p.finish(12.0)
	assert_eq(p.summary()["hits"], expected)


func test_pause_does_not_mute_a_hold_in_progress() -> void:
	var g := TrackTestKit.game("", 4.4)
	g.press(2, 4.5)
	g.pause(4.8)
	assert_false(g.is_muted(2), "a pause is not a mistake")
	assert_false(g.judge.is_holding(2))


func test_chart_choice() -> void:
	var g := TrackTestKit.game("easy")
	assert_eq(g.chart_name, "easy")
	TrackTestKit.run(g, "perfect", 12.0)
	g.finish(12.0)
	assert_eq(g.summary()["hits"], 6)
	assert_eq(TrackTestKit.game().chart_name, "normal", "the default chart when none is named")
