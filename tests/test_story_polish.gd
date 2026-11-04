extends TestCase
## The Story Campaign's presentation layer: the deck skin keeps PadView's geometry and the note skin keeps NoteLane's, the dancers'
## poses are beat-locked and genuinely synchronised in group moves, fades and depth order do not depend on the frame rate, the hero
## gets seen (lifted on the riser, an open-fronted dance circle), and the overlay cards run on song time.


func _rig(assets: StoryAssets, arch: String) -> Dictionary:
	var rig: Dictionary = (assets.manifest["archetypes"][arch]["variants"]["a"] as Dictionary).duplicate()
	rig["joints"] = assets.manifest["archetypes"][arch]["joints"]
	return rig


func test_skinned_pads_keep_the_pad_geometry() -> void:
	var run := StoryRun.create({})
	var clock := SongClock.new(null)
	for sz in [Vector2(1280, 259), Vector2(1280, 216), Vector2(1600, 302), Vector2(1024, 330)]:
		var plain := PadView.new()
		var skin := StoryPadView.new()
		for pv in [plain, skin]:
			pv.size = sz
			pv.setup(run.level, clock)
			tree.root.add_child(pv)
		var a := plain._pad_rects()
		var b := skin._pad_rects()
		for pad in range(1, 5):
			assert_eq(b[pad], a[pad], "pad %d rectangle at %s" % [pad, str(sz)])
		assert_eq(skin.button_rects(), plain.button_rects(), "touch rectangles at %s" % str(sz))
		plain.free()
		skin.free()


func test_skinned_notes_cross_the_pad_centre_on_the_beat() -> void:
	var level := Level.new()
	level.notes = [{"time": 1.0, "end_time": 1.0, "type": "tap", "pad": 1, "family": "kick"}]
	var plain := NoteLane.new()
	var skin := StoryNoteLane.new()
	var pads := {1: Rect2(100, 500, 80, 80)}
	for lane in [plain, skin]:
		lane.setup(level, null, null)
		lane.travel_s = 1.2
	for now in [0.2, 0.7, 1.0]:
		assert_eq(skin.visible_notes(now, pads), plain.visible_notes(now, pads), "the same notes at the same places at %.1f" % now)
	var at_hit: Rect2 = skin.visible_notes(1.0, pads)[0]["rect"]
	var head_centre_y := at_hit.end.y - at_hit.size.x * 0.5  # the skin centres its tile on the pad-sized square's centre
	assert_near(head_centre_y, (pads[1] as Rect2).get_center().y, 1e-3, "the tile's centre is on the pad's centre at the hit time")
	plain.free()
	skin.free()


func test_group_moves_are_truly_synchronised() -> void:
	var assets := StoryAssets.load_default()
	var dancers: Array = []
	var k := 0
	for arch in ["groover", "ponytail", "hoodie", "curly", "bob", "punk"]:
		var c := StoryCharacter.new()
		c.setup(assets, _rig(assets, arch), arch, 100 + k * 37)
		dancers.append(c)
		k += 1
	var styles := {}
	for c in dancers:
		styles[(c as StoryCharacter).style] = true
	assert_true(styles.size() >= 2, "the dancers do not all share one style")
	for st in ["cheer", "clap", "dance", "hands_up", "footwork"]:
		for beats in [3.0, 3.37, 5.5, 9.81]:
			var ref: Dictionary = {}
			for c in dancers:
				(c as StoryCharacter).sync = true
				var p := (c as StoryCharacter).sample(st, beats, 0.7)
				if ref.is_empty():
					ref = p
				else:
					assert_eq(p, ref, "%s at beat %.2f is identical for every synchronised dancer" % [st, beats])
	var free_differs := false
	for c in dancers:
		(c as StoryCharacter).sync = false
	var p0 := (dancers[0] as StoryCharacter).sample("dance", 3.37, 0.7)
	for c in dancers:
		if (c as StoryCharacter).sample("dance", 3.37, 0.7) != p0:
			free_differs = true
	assert_true(free_differs, "outside a group move the floor is not in lockstep")
	for c in dancers:
		(c as StoryCharacter).free()


func test_jumps_crouch_before_they_leave_the_floor() -> void:
	var assets := StoryAssets.load_default()
	var c := StoryCharacter.new()
	c.setup(assets, _rig(assets, "punk"), "p", 5)
	c.sync = true
	var crouch := c.sample("cheer", 0.05, 0.8)  # just after the jump's downbeat
	var air := c.sample("cheer", 0.86, 0.8)  # mid-air
	assert_true(float(crouch["squash"]) > 0.0 and float(crouch["jump"]) == 0.0, "anticipation: a crouch on the ground first")
	assert_true(float(air["jump"]) > 10.0 and float(air["squash"]) < 0.0, "then up and stretched")
	c.free()


func test_pose_follows_the_beat_without_lag() -> void:
	var assets := StoryAssets.load_default()
	var c := StoryCharacter.new()
	c.setup(assets, _rig(assets, "bob"), "b", 9)
	c.state = "dance"
	var t := 0.0
	while t < 2.0:
		c.update_pose(t, 174.0, 0.6)
		t += 1.0 / 60.0
	var target := c.sample("dance", t * 174.0 / 60.0, 0.6)
	c.update_pose(t, 174.0, 0.6)
	for key in StoryCharacter.POSE_KEYS:
		assert_near(float(c.cur[key]), float(target[key]), 1e-5, "%s is on the beat, not trailing it" % key)
	c.state = "cheer"  # a change cross-fades from the pose on screen
	var before := float(c.cur["arm_l"])
	c.update_pose(t + 1.0 / 60.0, 174.0, 0.6)
	assert_true(absf(float(c.cur["arm_l"]) - before) < 0.6, "no snap on a state change")
	c.update_pose(t + StoryCharacter.BLEND_S + 0.05, 174.0, 0.6)
	var cheer := c.sample("cheer", (t + StoryCharacter.BLEND_S + 0.05) * 174.0 / 60.0, 0.6)
	assert_near(float(c.cur["arm_l"]), float(cheer["arm_l"]), 1e-5, "and lands on the new state's live pose")
	c.free()


func _crowd_stage() -> Dictionary:
	var run := StoryRun.create({})
	var assets := StoryAssets.load_default()
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(assets, run.data, run)
	return {"run": run, "stage": stage}


func test_arrival_fades_are_frame_rate_independent() -> void:
	var alphas: Array = []
	for fps in [30.0, 60.0, 144.0]:
		var ctx := _crowd_stage()
		var stage: StoryStage = ctx["stage"]
		stage.update(0.0, 50.0)
		stage.apply({"t0": 0.0, "bar": 1.0, "action": "bring_in", "args": {"group": "early"}, "block": "", "source": "block"})
		var t := 0.0
		while t < 0.2 - 1e-9:
			t = minf(t + 1.0 / fps, 0.2)
			stage.update(t, 50.0)
		alphas.append(float(stage.crowd.actors["e01"]["alpha"]))
		stage.free()
	assert_near(alphas[0], alphas[1], 1e-4, "30 and 60 fps fade alike")
	assert_near(alphas[1], alphas[2], 1e-4, "60 and 144 fps fade alike")
	assert_true(alphas[0] > 0.3 and alphas[0] < 1.0, "a fade, not a pop: %.2f" % alphas[0])


func test_depth_order_is_stable_for_equal_distances() -> void:
	var ctx := _crowd_stage()
	var stage: StoryStage = ctx["stage"]
	var crowd := stage.crowd
	for id in crowd.actors:  # everybody on one row, one metre apart in x: the same distance order whichever way the frame ran
		crowd.actors[id]["pos"] = Vector2(-2.0 + float(str(id).hash() % 5) * 1.0, 3.0)
		crowd.actors[id]["sec"] = "floor"
	stage.update(2.0, 50.0)
	var first := crowd.drawn_order()
	for i in 5:
		stage.update(2.0, 50.0)
		assert_eq(crowd.drawn_order(), first, "a re-sort never swaps dancers standing on the same row")
	stage.free()


func test_the_circle_opens_towards_the_dj_and_the_riser_lifts_the_hero() -> void:
	var ctx := _crowd_stage()
	var stage: StoryStage = ctx["stage"]
	var crowd := stage.crowd
	crowd.bring_in("early", 0.0, 0.1)
	stage.update(1.0, 60.0)
	crowd.circle_form(1.0, 0.5)
	stage.update(3.0, 60.0)
	for id in crowd.ids_of("circle"):
		if not crowd.actors[id]["present"]:
			continue
		var d: Vector2 = (crowd.actors[id]["pos"] as Vector2) - crowd.circle_c
		var ang := atan2(d.y / crowd.circle_r.y, d.x / crowd.circle_r.x)
		assert_true(absf(angle_difference(ang, crowd.circle_open.angle())) > 0.35, "%s keeps the front of the circle clear" % id)
	var bar_s := stage.bar_s()
	stage.apply({"t0": 4.0, "bar": 1.0, "action": "riser_up", "args": {}, "block": "", "source": "block"})
	stage.apply({"t0": 4.0, "bar": 1.0, "action": "hero_solo", "args": {"bars": 6}, "block": "", "source": "block"})
	var t := 4.0
	while t < 4.0 + StoryStage.RISER_BOARD_S + bar_s * 1.2:
		t += 1.0 / 30.0
		stage.update(t, 80.0)
	var hero: StoryCharacter = crowd.hero_node()
	var hid := crowd.hero_id()
	assert_near(stage.riser_lift(t), StoryStage.RISER_LIFT, 0.01, "the riser is up")
	assert_eq(crowd.actors[hid]["sec"], "riser", "the hero has walked up onto the riser")
	assert_true((crowd.actors[hid]["pos"] as Vector2).distance_to(crowd.riser_spot) < 0.05, "and stands on its spot")
	assert_eq(hero.state, "solo", "and dances the solo")
	stage.apply({"t0": t, "bar": 1.0, "action": "riser_down", "args": {}, "block": "", "source": "block"})
	stage.update(t + bar_s * 0.5, 80.0)
	assert_true(stage.riser_lift(t + bar_s * 0.5) > 0.0 and stage.riser_lift(t + bar_s * 0.5) < StoryStage.RISER_LIFT, "it sinks over a bar")
	assert_near(stage.riser_lift(t + bar_s * 1.01), 0.0, 0.01)
	stage.free()


func test_overlay_cards_run_on_song_time() -> void:
	var hud := StoryHud.new()
	hud.show_act("ACT II", "FINDING THE GROOVE", 10.0)
	hud.set_time(9.9)
	assert_eq(hud._vis(10.0, StoryHud.ACT_HOLD), 0.0, "not before its time")
	hud.set_time(11.0)
	assert_eq(hud._vis(10.0, StoryHud.ACT_HOLD), 1.0, "held")
	hud.set_time(10.0 + StoryHud.ACT_HOLD + StoryHud.OUT_S + 0.01)
	assert_eq(hud._vis(10.0, StoryHud.ACT_HOLD), 0.0, "gone after its hold and fade")
	hud.free()


func test_new_dancers_enter_visibly_even_without_gathering_first() -> void:
	var ctx := _crowd_stage()
	var stage: StoryStage = ctx["stage"]
	stage.update(0.0, 60.0)
	var ids := stage.crowd.ids_of("gatherers")
	assert_false(ids.is_empty())
	for id in ids:
		assert_false(stage.crowd.actors[id]["present"], "%s starts off the floor" % id)
	stage.apply({"t0": 1.0, "bar": 33.0, "action": "new_dancers_enter", "args": {}, "block": "", "source": "decision"})
	var t := 1.0
	while t < 10.0:
		t += 1.0 / 30.0
		stage.update(t, 60.0)
	for id in ids:
		var a: Dictionary = stage.crowd.actors[id]
		assert_true(a["present"] and float(a["alpha"]) > 0.99, "%s came onto the floor" % id)
		assert_true((a["pos"] as Vector2).distance_to(a["home"]) < 1.0, "%s reached their place" % id)
	stage.free()


func test_a_caption_ends_when_the_camera_leaves_the_room() -> void:
	var hud := StoryHud.new()
	hud.show_toast("The guests streamed in.", "good", 20.0)
	hud.cut_toast(22.0)
	hud.set_time(21.0)
	assert_eq(hud._vis(20.0, float(hud._toast["hold"])), 1.0)
	hud.set_time(22.0 + StoryHud.OUT_S + 0.01)
	assert_eq(hud._vis(20.0, float(hud._toast["hold"])), 0.0, "gone once the move has begun")
	hud.free()


func test_room_pieces_stay_lit_through_a_pulse_and_doorless_rooms_enter_from_the_edge() -> void:
	var run := StoryRun.create({}, "res://content/story/mothership.json")
	if not run.errors.is_empty():
		fail("mothership chapter: %s" % str(run.errors))
		return
	var assets := StoryAssets.load_art(run.data.art)
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	tree.root.add_child(stage)
	stage.setup(assets, run.data, run)
	var ambient := ""
	for vid in assets.view_ids():
		if vid != "main" and not assets.pieces(str(vid)).is_empty():
			ambient = str(assets.pieces(str(vid))[0]["id"])
			break
	assert_true(ambient != "", "the chapter has a room with its own pieces")
	stage.apply({"t0": 5.0, "bar": 1.0, "action": "piece_pulse", "args": {"piece": ambient, "bars": 1}, "block": "", "source": "block"})
	var st := stage.piece_state(ambient, 5.05)
	assert_true(st["visible"] and is_equal_approx(float(st["alpha"]), 1.0), "a pulse does not switch a room's own piece off and on: %s" % str(st))
	assert_true(float(st["pulse"]) > 0.9, "but it does pulse")
	for vid in stage.views:
		var v: StoryView = stage.views[vid]
		if stage.map != null:
			continue  # a chapter in the world places its door in the map (spot "door"), checked by test_story_map
		if (assets.anchor("doorway", [], str(vid)) as Array).size() < 4:
			assert_true(v.crowd.door_pos.x < 0.0, "%s has no doorway: arrivals walk in from the left edge" % vid)
	stage.free()
