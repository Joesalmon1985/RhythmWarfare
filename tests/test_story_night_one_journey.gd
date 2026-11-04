extends TestCase
## WP6: Night One's authored journey (docs/STORY_25D_PLAN.md 4.2). Under the perfect, sloppy (seed 2) and none policies the places the player is sent to match the
## authored lists, the camera is inside a valid room at every bar, the journey is the same at any frame step, no authored move warns about a dense note run, the
## role badge, the pad strip's skin and the result screen's journey line follow the roles.

const BAD := ["floor_edge", "corridor", "cubicle", "floor_edge", "door"]


func _stage_with(log: Array) -> StoryStage:
	var run := StoryRun.create({})
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_default(), run.data, run)
	for a in log:
		stage.apply(a)
	return stage


func _played(policy: String, seed_value: int, step: float) -> Dictionary:
	var r := StoryRun.autoplay(policy, step, seed_value)
	r["stage"] = _stage_with(r["log"])
	return r


func test_perfect_play_goes_dancer_to_stage_to_dj() -> void:
	var r := _played("perfect", 1, 1.0 / 60.0)
	var stage: StoryStage = r["stage"]
	assert_eq(r["ending"], "legendary_set")
	assert_eq(stage.journey(), ["steps", "stage", "balcony", "booth", "booth"], "the climb, the balcony and the booth, and the legendary ending's tableau in the booth")
	assert_eq(r["journey"]["places"], ["steps", "stage", "balcony", "booth", "booth"])
	assert_eq(r["journey"]["roles"], ["dancer", "on_stage", "dj"])
	assert_eq(r["journey"]["name"], "Dancer > On stage > DJ")
	stage.free()


func test_none_play_goes_dancer_to_the_toilets_and_out() -> void:
	var r := _played("none", 1, 1.0 / 60.0)
	var stage: StoryStage = r["stage"]
	assert_eq(r["ending"], "lost_the_floor")
	assert_eq(stage.journey(), BAD, "the floor edge, the corridor, the cubicle, back to the floor edge and the door")
	assert_eq(r["journey"]["roles"], ["dancer", "queasy", "sick", "recovered", "out"])
	assert_eq(r["journey"]["name"], "Dancer > Feeling rough > Sick in the cubicle > Recovered > Out cold")
	stage.free()


func test_sloppy_seed_three_takes_the_bad_branches_and_ends_on_the_steps() -> void:  # seed 3 since Night One plays the recorded Warehouse cues (seed 2 now takes the good branches)
	var r := _played("sloppy", 3, 1.0 / 60.0)
	var stage: StoryStage = r["stage"]
	assert_eq(r["ending"], "good_night")
	assert_eq(stage.journey(), ["steps", "stage", "corridor", "cubicle", "floor_edge", "steps", "stage_edge"], "a good night after the toilets ends at the stage edge, facing the floor")
	stage.free()


func test_the_journey_is_the_same_at_any_frame_step() -> void:
	var base := _played("accuracy:0.8", 1, 1.0 / 60.0)
	for step in [1.0 / 30.0, 0.0]:
		var other := _played("accuracy:0.8", 1, step)
		assert_eq(other["journey"], base["journey"], "step %.4f" % step)
		assert_eq((other["stage"] as StoryStage).journey(), (base["stage"] as StoryStage).journey())
		(other["stage"] as StoryStage).free()
	(base["stage"] as StoryStage).free()


func test_the_camera_is_inside_a_room_at_every_bar_and_the_role_follows_the_badge() -> void:
	for policy in ["perfect", "none"]:
		var r := _played(policy, 1, 1.0 / 60.0)
		var stage: StoryStage = r["stage"]
		var bar_s := stage.bar_s()
		for bar in range(0, 132):
			var t := float(bar) * bar_s
			var pose := stage.player.pose_at(t)
			assert_true(stage.map.sector_at(pose["pos"]) != "", "%s bar %d: the camera stands in a room" % [policy, bar])
			assert_eq(pose["role"], stage.player.role_at(t))
		assert_eq(StoryHud.role_badge(stage.player.role_at(10.0 * bar_s)), "DANCER", "bar 10: still dancing")
		stage.free()
	var good := _played("perfect", 1, 1.0 / 60.0)
	var gs: StoryStage = good["stage"]
	assert_eq(StoryHud.role_badge(gs.player.role_at(44.0 * gs.bar_s())), "ON STAGE")
	assert_eq(StoryHud.role_badge(gs.player.role_at(100.0 * gs.bar_s())), "DJ")
	gs.free()
	var bad := _played("none", 1, 1.0 / 60.0)
	var bs: StoryStage = bad["stage"]
	assert_eq(StoryHud.role_badge(bs.player.role_at(40.0 * bs.bar_s())), "FEELING ROUGH")
	assert_eq(StoryHud.role_badge(bs.player.role_at(130.0 * bs.bar_s())), "OUT COLD")
	bs.free()


func test_no_authored_move_warns_about_a_dense_run() -> void:
	var run := StoryRun.create({})
	for w in run.warnings:
		assert_false("player_move" in str(w), "no warning on load: " + str(w))
	assert_true(run.director.warnings.is_empty(), str(run.director.warnings))
	for loadout in [{}, {"difficulty": "hard"}]:
		var r2 := StoryRun.create(loadout)
		for w in r2.director.warnings:
			assert_false("overlaps a dense note run" in str(w), str(w))


func test_the_pad_strip_is_the_dancers_rail_until_the_role_is_on_stage() -> void:
	var r := _played("perfect", 1, 1.0 / 60.0)
	var stage: StoryStage = r["stage"]
	var b := stage.bar_s()
	var p := stage.player
	assert_near(p.deck_mix_at(0.0), 0.0, 1e-6, "a dancer's strip")
	assert_near(p.deck_mix_at(30.0 * b), 0.0, 1e-6)
	var t_on := 0.0
	for x in p._roles:
		if str(x["role"]) == "on_stage":
			t_on = float(x["t0"])
	assert_true(t_on > 30.0 * b)
	assert_true(p.deck_mix_at(t_on + 0.75) > 0.3 and p.deck_mix_at(t_on + 0.75) < 0.7, "a cross-fade over 1.5 s of song time")
	assert_near(p.deck_mix_at(t_on + 2.0), 1.0, 1e-6, "the DJ deck")
	assert_eq(p.deck_mix_at(t_on + 0.75), p.deck_mix_at(t_on + 0.75), "a pure function of time")
	var deck := StoryDeck.new()
	deck.setup(StoryAssets.load_default(), r["run"], stage)
	assert_near(deck.deck_mix(0.0), 0.0, 1e-6)
	assert_near(deck.deck_mix(t_on + 3.0), 1.0, 1e-6)
	stage.free()


func test_motion_settings_calm_the_camera() -> void:
	var stage := _stage_with([])
	var b := stage.bar_s()
	var t := 2.0 * b + 0.3
	stage.apply({"t0": 2.0 * b, "bar": 1.0, "action": "player_move", "args": {"to": "steps", "style": "walk", "bars": 4.0}, "block": "", "source": "block"})
	stage.motion = 0
	stage.update(t, 50.0)
	var full := stage.player.pose_at(t)
	stage.motion = 1
	stage.update(t, 50.0)
	var calm := stage.player.pose_at(t)
	assert_true(absf(float(full["roll"])) > 0.0 and is_equal_approx(float(calm["roll"]), 0.0), "reduced motion: no roll")
	stage.motion = 2
	stage.update(2.0 * b + 1.0, 50.0)
	assert_eq(stage.player.pose_at(2.0 * b + 1.0)["pos"], stage.map.waypoint("floor_centre")["at"], "no motion: the camera waits and cuts")
	assert_eq(stage.player.pose_at(2.0 * b + 4.5 * b)["pos"], stage.map.waypoint("steps")["at"], "and arrives")
	stage.motion = 0
	stage.reduced = true
	stage.update(t, 50.0)
	assert_true(is_equal_approx(float(stage.player.pose_at(t)["roll"]), 0.0), "reduced effects imply reduced motion")
	stage.free()
	Session.reduced_effects = true
	assert_eq(Session.effective_story_motion(), 1)
	Session.reduced_effects = false
	Session.story_motion = 2
	assert_eq(Session.effective_story_motion(), 2)
	Session.story_motion = 0
	assert_eq(StoryLowRes.LINE_CHOICES[Session.story_lines], 360, "360p is the default internal resolution")
