extends TestCase
## WP5: the light show as numbers. StoryLight is a pure function of song time and the stage's action state (the same maths the 2D StoryFx drew), StoryWorldFx puts it
## into the 3D world, the post-process reads StoryLight.post_state, reduced effects softens it, the ending fades, and the sick beat ducks the stems.


func _stage(nodes := false) -> StoryStage:
	var run := StoryRun.create({})
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_default(), run.data, run)
	if nodes:
		stage.attach_world(stage.map, true)
	return stage


func _act(stage: StoryStage, t0: float, action: String, args := {}) -> void:
	stage.apply({"t0": t0, "bar": 1.0, "action": action, "args": args, "block": "", "source": "block"})


func test_beams_follow_energy_mode_and_reduced_effects() -> void:
	var stage := _stage()
	stage.update(5.0, 20.0)
	var low := StoryLight.beam_intensity(stage, 5.0)
	stage.update(5.0, 90.0)
	var high := StoryLight.beam_intensity(stage, 5.0)
	assert_true(high > low * 2.0, "a loud room has stronger beams (%.2f vs %.2f)" % [high, low])
	_act(stage, 6.0, "beams_off")
	assert_true(StoryLight.beam_intensity(stage, 6.1) > 0.0 and StoryLight.beam_intensity(stage, 7.0) == 0.0, "beams_off fades the rig out over 0.6 s")
	_act(stage, 20.0, "beams_fan")
	var a_fan := StoryLight.fixture_angle(stage, 0, 21.0)
	_act(stage, 30.0, "beams_cross")
	assert_true(not is_equal_approx(a_fan, StoryLight.fixture_angle(stage, 0, 31.0)), "each cue has its own swing")
	stage.reduced = true
	var calm_a := StoryLight.fixture_angle(stage, 2, 31.0)
	_act(stage, 40.0, "beams_sweep")
	assert_near(StoryLight.fixture_angle(stage, 2, 41.0), calm_a - 0.0, 0.3, "reduced effects keeps one calm fan whatever the cue")
	stage.free()


func test_the_light_is_a_function_of_song_time_only() -> void:
	var stage := _stage()
	_act(stage, 4.0, "lights_rave")
	_act(stage, 6.0, "beams_fan")
	stage.update(10.0, 70.0)
	var first := [StoryLight.beam_alpha(stage, 10.0), StoryLight.fixture_angle(stage, 3, 10.0), StoryLight.haze_alpha(stage, 10.0), StoryLight.dim_at(stage, 10.0)]
	for t in [3.0, 17.0, 10.0]:  # asking about other times and coming back changes nothing
		StoryLight.beam_alpha(stage, t)
	assert_eq([StoryLight.beam_alpha(stage, 10.0), StoryLight.fixture_angle(stage, 3, 10.0), StoryLight.haze_alpha(stage, 10.0), StoryLight.dim_at(stage, 10.0)], first)
	stage.free()


func test_strobe_is_a_short_flash_on_a_drop_and_never_when_reduced() -> void:
	var stage := _stage()
	_act(stage, 10.0, "bass_reveal")
	assert_eq(StoryLight.strobe_at(stage, 9.9), 0.0)
	assert_true(StoryLight.strobe_at(stage, 10.02) > 0.2, "a flash at the drop")
	assert_eq(StoryLight.strobe_at(stage, 10.6), 0.0, "gone within half a second")
	assert_true(StoryLight.bloom_at(stage, 10.5) > 0.0 and StoryLight.bloom_at(stage, 12.0) == 0.0, "the bloom swells and is over within 1.6 s")
	stage.reduced = true
	assert_eq(StoryLight.strobe_at(stage, 10.02), 0.0, "reduced effects: no strobe")
	stage.free()


func test_mood_dimming_and_the_ending_fade() -> void:
	var stage := _stage()
	stage.update(5.0, 90.0)
	var bright := StoryLight.dim_at(stage, 5.0)
	stage.update(5.0, 10.0)
	var dull := StoryLight.dim_at(stage, 5.0)
	assert_true(dull > bright, "a quiet room is darker")
	assert_eq(StoryLight.fade_at(stage, 100.0), 0.0, "no fade before an ending")
	_act(stage, 100.0, "ending", {"ending": "lost_the_floor"})
	assert_eq(stage.tableau(), "lost")
	assert_near(StoryLight.dim_at(stage, 100.5), 0.4, 0.2, "a lost night is dim")
	assert_true(StoryLight.fade_at(stage, 100.0) == 0.0 and StoryLight.fade_at(stage, 102.0) > 0.2, "it sinks over four seconds")
	assert_near(StoryLight.fade_at(stage, 110.0), 0.55, 1e-6, "to a floor of 0.55")
	assert_true(StoryLight.post_state(stage, 110.0)["dim"] > StoryLight.post_state(stage, 100.0)["dim"], "the post-process darkens with it")
	var legendary := _stage()
	_act(legendary, 100.0, "ending", {"ending": "legendary_set"})
	assert_eq(legendary.tableau(), "legendary")
	assert_eq(StoryLight.fade_at(legendary, 110.0), 0.0, "a legendary night stays bright")
	assert_eq(StoryLight.led_word(legendary), ["ENCORE!"])
	assert_eq(StoryLight.led_word(stage), ["GOOD", "NIGHT"])
	stage.free()
	legendary.free()


func test_queasy_and_sick_reach_the_post_process_and_reduced_effects_switches_the_warp_off() -> void:
	var stage := _stage()
	var b := stage.bar_s()
	_act(stage, 10.0 * b, "fx_queasy", {"amount": 0.6, "bars": 2.0})
	_act(stage, 14.0 * b, "sick_beat", {"bars": 4.0})
	assert_eq(StoryLight.post_state(stage, 5.0 * b)["queasy"], 0.0)
	assert_near(StoryLight.post_state(stage, 13.0 * b)["queasy"], 0.6, 1e-4, "the illness look settles at the authored amount")
	assert_true(StoryLight.post_state(stage, 16.0 * b)["sick"] > 0.9, "head down in the sick beat")
	assert_true(StoryLight.post_state(stage, 16.0 * b)["dim"] > StoryLight.post_state(stage, 5.0 * b)["dim"] * 0.8 - 1.0e-6)
	stage.reduced = true
	var r := StoryLight.post_state(stage, 13.0 * b)
	assert_eq(r["queasy"], 0.0, "reduced effects: no warp, chroma split or desaturation")
	assert_true(r["vignette"] <= 0.15 + 1e-6, "and no breathing vignette")
	assert_eq(r["strobe"], 0.0)
	stage.free()


func test_led_floor_ripples_out_of_the_circle_on_a_drop() -> void:
	var stage := _stage()
	_act(stage, 10.0, "bass_reveal")
	stage.update(10.0, 80.0)
	var c := stage.crowd.circle_c
	var fx := stage.crowd.floor_x
	var near_ring := StoryLight.tile_alpha(stage, 11.0, 0, 0, 0.9, c + Vector2(5.0 * 1.0, 0), c, fx)  # the front is 5 m out after a second
	var far_off := StoryLight.tile_alpha(stage, 11.0, 0, 0, 0.9, c + Vector2(0.5, 0), c, fx)
	assert_true(near_ring > far_off, "the ripple front is brighter than the middle")
	stage.reduced = true
	assert_true(StoryLight.tile_alpha(stage, 11.0, 3, 3, 0.2, c + Vector2(1, 1), c, fx) <= 0.85)
	stage.free()


func test_spots_follow_the_hero_the_circle_and_the_sweep() -> void:
	var stage := _stage()
	assert_eq(StoryLight.spots(stage, 5.0).size(), 0)
	_act(stage, 5.0, "spotlight_hero")
	var s := StoryLight.spots(stage, 6.0)
	assert_eq(s.size(), 1)
	assert_eq(s[0]["at"], stage.crowd.actors[stage.crowd.hero_id()]["pos"], "the pool stays on the hero")
	_act(stage, 5.0, "spotlight_sweep")
	assert_eq(StoryLight.spots(stage, 6.0).size(), 2)
	stage.free()


func test_confetti_falls_for_five_seconds() -> void:
	var stage := _stage()
	_act(stage, 10.0, "confetti")
	assert_eq(StoryLight.confetti(stage, 9.0, 70).size(), 0)
	var early := StoryLight.confetti(stage, 10.5, 70)
	assert_true(early.size() > 20)
	assert_eq(StoryLight.confetti(stage, 16.0, 70).size(), 0, "over after five seconds")
	stage.reduced = true
	assert_true(StoryLight.confetti(stage, 10.5, 70).size() <= 24)
	stage.free()


func test_world_fx_builds_in_the_world_and_stands_still_when_time_does() -> void:
	var stage := _stage(true)
	assert_true(stage.fx3d != null)
	assert_eq(stage.fx3d._beams.size(), 6, "one beam per fixture of the map")
	assert_true(stage.fx3d._led_tex != null)
	_act(stage, 1.0, "disco_ball_on")
	_act(stage, 1.0, "led_bars")
	_act(stage, 1.0, "lights_rave")
	stage.update(12.0, 80.0)
	var img1: Image = stage.fx3d._led_img.duplicate()
	var tiles1: Image = stage.fx3d._tile_img.duplicate()
	stage.update(12.0, 80.0)
	stage.update(12.001, 80.0)
	assert_eq(stage.fx3d._led_img.get_data(), img1.get_data(), "a paused clock does not move the LED wall")
	assert_eq(stage.fx3d._tile_img.get_data(), tiles1.get_data(), "or the floor tiles")
	stage.update(14.0, 80.0)
	assert_true(stage.fx3d._led_img.get_data() != img1.get_data(), "and they move with song time")
	stage.update(12.0, 80.0)  # a restart replays the same picture
	assert_eq(stage.fx3d._led_img.get_data(), img1.get_data())
	_act(stage, 20.0, "ending", {"ending": "legendary_set"})
	stage.update(21.0, 80.0)
	var words := StoryLight.led_word(stage)
	assert_eq(words, ["ENCORE!"])
	stage.free()


func test_the_sick_beat_ducks_the_stems_and_nothing_else_changes() -> void:
	var tr := StemTransport.new()
	tr._low_keys = {"kick": true}
	assert_eq(tr.effective_gain("bass_a"), 1.0, "no duck: the mix is exactly as before")
	tr.set_duck(1.0)
	assert_near(tr.effective_gain("kick"), 0.45, 1e-6, "the low stems stay, quieter")
	assert_near(tr.effective_gain("lead"), 0.1, 1e-6, "the rest fall away: a muffled mix")
	tr.set_duck(0.0)
	assert_eq(tr.effective_gain("lead"), 1.0)
	tr.free()
