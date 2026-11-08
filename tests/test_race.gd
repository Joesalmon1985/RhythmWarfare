extends TestCase
## The street race (docs/briefs/BEDSIT_RAVES_BRIEF.md sections 8 to 10, docs/bedsit/RACE.md): the course and its map, the simulation (determinism, safe responses, rhythm AND driving
## change the finish, bounded penalties, a reachable finish, pause), the things in the world, the view at 16:9 and 20:9, and the whole run: the hangar -> the race -> the hub,
## with the save recorded.

const Bot := preload("res://tests/fixtures/race_bot.gd")
const Driver := preload("res://tests/fixtures/space_run_driver.gd")
const BEAT := 60.0 / 174.0


func _race_data() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string("res://content/races/space.json"))


# --- the course and the map --------------------------------------------------------------------------------------------------------

func test_the_course_file_and_its_map_load_clean_with_every_lane_waypoint() -> void:
	var c := RaceCourse.load_id("race_space")
	assert_eq(c.errors, [], "the course has contract 8's shape")
	assert_eq(c.lane_count(), 3, "three lanes")
	assert_near(c.length_m, 2200.0, 0.01)
	var m := StoryMap.load_chapter("race_space")
	assert_eq(m.errors, [], "the map builds (sectors convex, portals meet, things and waypoints inside)")
	var wps: Array = c.lane_waypoints()
	assert_eq(wps.size(), 3, "lane waypoints for every lane")
	var n := 0
	for k in wps.size():
		for wid: String in wps[k]:
			n += 1
			assert_true(m.has_waypoint(wid), "%s is a waypoint of the map" % wid)
			if not m.has_waypoint(wid):
				continue
			var w := m.waypoint(wid)
			assert_true(str(w["sector"]).begins_with("rd_"), "%s stands on the road" % wid)
			var raw: Dictionary = {}
			for r: Dictionary in m.raw["waypoints"]:
				if str(r["id"]) == wid:
					raw = r
			var p: Dictionary = c.point(float(raw["s"]), c.lane_x(float(k)))
			assert_true((p["at"] as Vector2).distance_to(w["at"]) < 0.01, "%s is the course's lane %d point" % [wid, k])
	assert_true(n >= 3 * 70, "a waypoint per lane per piece (%d)" % n)
	for wid in ["race_grid", "race_finish"]:
		assert_true(m.has_waypoint(wid), wid)
	# the contract's reference point (the dense centreline) agrees with the analytic course
	for s: float in [0.0, 333.0, 700.0, 1234.5, 1999.0, 2200.0]:
		var a: Vector2 = c.point(s, c.lane_x(2.0))["at"]
		var b: Vector2 = ContractShapes.course_point(c.raw, 2.0, s)["at"]
		assert_true(a.distance_to(b) < 0.6, "course_point and RaceCourse.point agree at %.0f m (%.3f)" % [s, a.distance_to(b)])
		assert_eq(m.sector_at(a), c.road_at(s), "the road sector at %.0f m" % s)
	assert_true(m.things.any(func(t: Dictionary) -> bool: return str(t["id"]) == "finish_gantry"), "a finish gantry")
	assert_true(m.decals.size() > 20 and m.lights.size() > 40, "window and neon decals, lamps (%d decals, %d lights)" % [m.decals.size(), m.lights.size()])


func test_the_activity_config_is_the_contracts_overlay_race() -> void:
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/race.json"))
	assert_eq(ContractShapes.activity_config(cfg), [], "activity_config")
	assert_eq(ActivityMode.of_config(cfg), ActivityMode.Mode.OVERLAY)
	assert_true("race" in MinigameController.registered_ids(), "registered")
	var theme: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/raves/space.json"))
	assert_eq(str(theme["race"]["course"]), "race_space", "the Space rave names its course")
	var req := RunMinigameHost.build_request("race", cfg, "space", theme, "space_race", "hangar_view")
	assert_eq(ContractShapes.activity_request(req), [])
	assert_eq(str(req["return_pose"]), "hangar_view", "the race comes back to the hangar")


# --- the simulation ----------------------------------------------------------------------------------------------------------------

func test_the_same_inputs_give_the_same_race_whatever_the_frame_rate() -> void:
	var a := Bot.play(Bot.make(7), "best", 0.8)
	var b := Bot.play(Bot.make(7), "best", 0.8)
	assert_eq(Bot.summary(a), Bot.summary(b), "same seed, same play: same race")
	assert_eq(a.log, b.log, "the same log, step for step")
	var c := Bot.play(Bot.make(7), "best", 0.8, 1.0 / 47.0)
	assert_eq(Bot.summary(c), Bot.summary(a), "47 frames a second instead of 60: the same race")
	var d := Bot.play(Bot.make(8), "best", 0.8)
	assert_true(a.log.filter(func(x: Dictionary) -> bool: return x["kind"] == "spawn").map(func(x: Dictionary) -> String: return x["sit"]) != \
		d.log.filter(func(x: Dictionary) -> bool: return x["kind"] == "spawn").map(func(x: Dictionary) -> String: return x["sit"]), "another seed, other situations")


func test_every_situation_has_a_safe_response_from_every_lane() -> void:
	var kinds := {}
	var multi := 0
	for kind: String in ["braking_car", "rival_opening", "blocked_lane", "narrowing"]:
		var data := _race_data()
		for s: Dictionary in data["situations"]:
			s["weight"] = 1.0 if str(s["kind"]) == kind else 0.0
		for seed in [3, 5, 9]:
			var a := Bot.play(Bot.make(seed, "space", null, {"race_data": data}), "dither", 1.0)
			assert_true(a.finished(), "%s seed %d: finishes" % [kind, seed])
			for sit: Dictionary in a.sits:
				var safe := RaceActivity.safe_responses(sit)
				kinds[str(sit["kind"]) + "@" + str(sit["lane"])] = true
				assert_true("bottom" in safe, "%s from lane %d: bottom is safe (%s)" % [sit["kind"], sit["lane"], str(sit["outcomes"])])
				assert_eq((sit["outcomes"] as Dictionary).keys().size(), 4, "every region has an outcome")
				if safe.size() >= 2:
					multi += 1
				assert_true(str(sit.get("result", "")) in RaceActivity.SAFE, "the dithering driver (best in the last half second) is safe: %s %s" % [sit["kind"], sit.get("result", "")])
	for k in ["braking_car@1", "blocked_lane@1", "narrowing@1"]:
		assert_true(kinds.has(k), "%s was generated" % k)
	assert_true(kinds.keys().any(func(k: String) -> bool: return k.begins_with("rival_opening")), "a rival opening was generated (%s)" % str(kinds.keys()))
	assert_true(kinds.keys().any(func(k: String) -> bool: return k.ends_with("@0") or k.ends_with("@2")), "and from an edge lane (%s)" % str(kinds.keys()))
	assert_true(multi > 10, "several valid responses where the road allows (%d)" % multi)


func test_rhythm_and_driving_both_change_the_finish() -> void:
	for seed in [7, 23]:
		var both := Bot.play(Bot.make(seed), "best", 1.0)
		var rhythm_only := Bot.play(Bot.make(seed), "none", 1.0)
		var driving_only := Bot.play(Bot.make(seed), "best", 0.6)
		assert_true(both.finished() and rhythm_only.finished() and driving_only.finished(), "all three finish")
		assert_eq(both.position, 1, "seed %d: perfect rhythm and driving wins (%s)" % [seed, str(Bot.summary(both))])
		assert_true(bool(both.result()["race"]["won"]))
		assert_true(rhythm_only.position > 1 and rhythm_only.race_time() > both.race_time() + 5.0, "perfect rhythm, no driving: loses (%s)" % str(Bot.summary(rhythm_only)))
		assert_true(driving_only.position > 1 and driving_only.race_time() > both.race_time() + 8.0, "perfect driving, poor rhythm: loses (%s)" % str(Bot.summary(driving_only)))
		assert_true(int(rhythm_only.state()["contacts"]) >= 5, "no driving: visible contacts")
		var t_q: Array = [1.0, 0.8, 0.6].map(func(q: float) -> float: return Bot.play(Bot.make(seed), "best", q).race_time())
		assert_true(t_q[0] < t_q[1] and t_q[1] < t_q[2], "better rhythm, faster (%s)" % str(t_q))
		var t_d: Array = ["best", "none", "worst"].map(func(d: String) -> float: return Bot.play(Bot.make(seed), d, 0.8).race_time())
		assert_true(t_d[0] < t_d[1] and t_d[1] <= t_d[2], "better driving, faster (%s)" % str(t_d))
	var ordinary := Bot.play(Bot.make(11), "best", 0.8)
	assert_true(ordinary.race_time() >= 60.0 and ordinary.race_time() <= 90.0, "ordinary play takes 60 to 90 s (%.1f)" % ordinary.race_time())


func test_penalties_are_bounded_and_the_worst_play_still_finishes() -> void:
	var a := Bot.make(7)
	a.begin(0.0)
	var t := 0.0
	var vmin := INF
	var drops: Array = []
	var last_v := 0.0
	var next_note := 0.0
	while not a.is_done() and t < 400.0:
		t += 1.0 / 60.0
		while next_note <= t:
			a.on_judge({"kind": "miss", "time": next_note}, next_note)
			next_note += BEAT / 4.0
		a.update(t)
		if not a.cur.is_empty() and str(a.cur["selected"]) == "":
			a.tap("region:" + Bot.best_dir(a.cur, true), t)
		var v := float(a.player["v"])
		if t > a.t_go + 2.5 and not a.finished():
			vmin = minf(vmin, v)
			if v < last_v - 1.0:
				drops.append(v / last_v)
		last_v = v
	assert_true(a.finished(), "the worst play finishes (%.1f s)" % a.race_time())
	assert_true(a.race_time() < a.max_s, "inside the bound (%.0f s)" % a.max_s)
	assert_true(vmin >= a.v_min - 0.01, "never below the minimum travelling speed (%.2f >= %.2f)" % [vmin, a.v_min])
	assert_true(drops.all(func(k: float) -> bool: return k >= 0.5 - 1e-6), "no single knock takes more than half the speed (%s)" % str(drops))
	assert_true(int(a.state()["contacts"]) >= 10, "and every contact counted (%d)" % int(a.state()["contacts"]))
	assert_true(a.position >= 1 and a.position <= 4)
	var r := a.result()
	assert_eq(ContractShapes.activity_result(r), [], "the result has the contract's shape")
	assert_false(bool(r["race"]["won"]))


func test_pause_freezes_the_deadlines_and_the_race() -> void:
	var a := Bot.make(7)
	a.begin(0.0)
	var t := 0.0
	while a.cur.is_empty() and t < 30.0:
		t += 1.0 / 60.0
		a.update(t)
	assert_false(a.cur.is_empty(), "a situation is open")
	var dead := float(a.cur["t_dead"])
	var snap := a.state()
	for i in 600:  # ten seconds of frames with the song paused: song time stands still
		a.update(t)
	assert_eq(float(a.cur["t_dead"]), dead, "the deadline did not move")
	assert_eq(a.state(), snap, "nothing moved")
	a.tap("region:bottom", t)
	while t < dead + 0.2:
		t += 1.0 / 60.0
		a.update(t)
	var res: Array = a.log.filter(func(x: Dictionary) -> bool: return x["kind"] == "resolve")
	assert_eq(res.size(), 1)
	assert_true(absf(float(res[0]["t"]) - dead) <= a.dt + 1e-6, "resolved at the deadline in song time (%.4f vs %.4f)" % [float(res[0]["t"]), dead])
	assert_eq(str(res[0]["dir"]), "bottom")
	var plain := Bot.play(Bot.make(7), "best", 0.8)
	var paused := Bot.play(Bot.make(7), "best", 0.8, 1.0 / 60.0, [[10.0, 300], [33.3, 120], [50.0, 900]])
	assert_eq(Bot.summary(paused), Bot.summary(plain), "three pauses change nothing in the race")


func test_the_selection_can_change_until_the_deadline_and_the_current_one_is_resolved() -> void:
	var w := WorldThings.new()
	var a := Bot.make(7, "space", w)
	a.begin(0.0)
	var t := 0.0
	while a.cur.is_empty() and t < 30.0:
		t += 1.0 / 60.0
		a.update(t)
	var dead := float(a.cur["t_dead"])
	assert_near(dead - float(a.cur["t_spawn"]), 4.0, 0.001, "about four seconds to decide (configurable)")
	for dir in ["left", "right", "top", "bottom"]:
		assert_true(a.tap("region:" + dir, t), "region %s taken" % dir)
		assert_eq(str(a.cur["selected"]), dir, "the selection is now %s" % dir)
		assert_true(w.feedback_log.size() > 0 and float(w.feedback_log[w.feedback_log.size() - 1]["t"]) == t, "immediate feedback in the world")
		var things := a.things()
		var dash: Dictionary = things.filter(func(x: Dictionary) -> bool: return x["id"] == "race_dash")[0]
		var row := int((dash["frame"] as Array)[0])
		assert_eq(row, {"left": 1, "right": 2, "top": 0, "bottom": 3}[dir], "the car leans or brakes at once (%s)" % dir)
		assert_eq(things.any(func(x: Dictionary) -> bool: return x["id"] == "race_choice"), dir != "bottom" and not (dir == "left" and int(a.player["lane_to"]) == 0) \
			and not (dir == "right" and int(a.player["lane_to"]) == 2), "the chosen opening is lit on the road (%s)" % dir)
		t += 0.5
		a.update(t)
	assert_true(things_have(a.things(), "race_gauge"), "the countdown gauge is on the dash")
	a.tap("region:right", dead - 0.05)
	while t < dead + 0.1:
		t += 1.0 / 60.0
		a.update(t)
	var res: Array = a.log.filter(func(x: Dictionary) -> bool: return x["kind"] == "resolve")
	assert_eq(str(res[0]["dir"]), "right", "the selection held at the deadline is the one resolved")
	a.tap("region:left", t)
	assert_eq(str(res[0]["dir"]), "right", "a tap after the deadline changes nothing")
	assert_true(w.feedback_log.any(func(f: Dictionary) -> bool: return str(f["kind"]) in ["tick", "cross"] and absf(float(f["t"]) - float(res[0]["t"])) < 1e-6), "a tick or a cross on the thing")
	# no selection at all: the deadline resolves top (continue)
	var b := Bot.play(Bot.make(7), "none", 1.0)
	assert_true(b.sits.all(func(s: Dictionary) -> bool: return str(s["resolved_dir"]) == "top"), "no choice is top")


func things_have(arr: Array, id: String) -> bool:
	return arr.any(func(x: Dictionary) -> bool: return str(x["id"]) == id)


# --- the view (contract 10) --------------------------------------------------------------------------------------------------------

func _stage(size: Vector2) -> StoryStage:
	var sd: StoryData = StoryData.load_file("res://content/story/race_space.json")["data"]
	var run := StoryRun.create({}, "res://content/story/space_rave.json")  # (a run with a level for the tempo; the race's data in it, as RaceStageHost does with the run's proxy)
	run.data = sd
	run.crowd.setup(sd)
	var stage := StoryStage.new()
	stage.size = size
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_art(sd.art), sd, run)
	stage.attach_world(stage.map, true)
	stage.lowres.size = size
	stage.lowres._fit()
	return stage


## Moments of a race: the approach to a situation (with the chosen opening lit and the countdown), an overtake, a contact, the finish.
func _moments() -> Array:
	var out: Array = []
	var a := Bot.make(7)
	a.begin(0.0)
	var t := 0.0
	var shot := {}
	var next_note := 0.0
	while not a.is_done() and t < 200.0:
		t += 1.0 / 60.0
		while next_note <= t:
			a.on_judge({"kind": "perfect", "time": next_note}, next_note)
			next_note += BEAT / 4.0
		a.update(t)
		if not a.cur.is_empty():
			var sit := a.cur
			var left := float(sit["t_dead"]) - t
			if str(sit["selected"]) == "" and t - float(sit["t_spawn"]) > 0.6:
				var want := Bot.best_dir(sit, int(sit["n"]) == 2)  # (the third situation is driven into, for the contact)
				a.tap("region:" + want, t)
			if left < 1.2 and not shot.has("approach") and str(sit["selected"]) in ["left", "right", "top"]:
				shot["approach"] = true
				out.append(["approach", t, a.things(), a.camera_pose(t), str(sit["subject"])])
		for e: Dictionary in a.log:
			if e["kind"] == "resolve" and not shot.has(str(e["outcome"])) and t - float(e["t"]) > 0.25 and t - float(e["t"]) < 0.3:
				shot[str(e["outcome"])] = true
				out.append([str(e["outcome"]), t, a.things(), a.camera_pose(t), ""])
		if a.finished() and not shot.has("finish") and t > a.finish_t - 1.0:
			shot["finish"] = true
			out.append(["finish", t, a.things(), a.camera_pose(t), ""])
	return out


func test_the_race_things_stand_inside_the_stage_strip_at_16_9_and_20_9() -> void:
	var moments := _moments()
	var names := moments.map(func(m: Array) -> String: return str(m[0]))
	for want in ["approach", "contact", "finish"]:
		assert_true(want in names, "a %s moment (%s)" % [want, str(names)])
	for sz: Vector2 in [Vector2(1280, 460), Vector2(1600, 460)]:
		var stage := _stage(sz)
		for mo: Array in moments:
			var pose: Dictionary = mo[3]
			stage.pose_fn = func(_t: float) -> Dictionary: return pose
			stage.set_things(mo[2])
			stage.update(float(mo[1]), 60.0)
			assert_eq(stage.world.dynamic.errors, [], "%s: the sheets load" % mo[0])
			var check := ["race_dash", "race_speedo"]
			if str(mo[0]) == "approach":
				check += ["race_gauge", "race_choice", str(mo[4])]
			for id: String in check:
				if not things_have(mo[2], id):
					continue
				var r: Variant = stage.thing_screen_rect(id)
				assert_true(r != null, "%s %s %s: drawn" % [str(sz), mo[0], id])
				if r == null:
					continue
				var rr: Rect2 = r
				assert_true(Rect2(Vector2(-1, -1), sz + Vector2(2, 2)).encloses(rr), "%s %s %s: inside the strip (%s)" % [str(sz), mo[0], id, str(rr)])
				assert_true(rr.size.y >= (14.0 if id == "race_choice" else 48.0), "%s %s %s: tall enough (%.1f)" % [str(sz), mo[0], id, rr.size.y])
			var dr: Variant = stage.thing_screen_rect("race_dash")
			if dr != null:
				assert_true((dr as Rect2).size.y <= sz.y * 0.36 and (dr as Rect2).end.y >= sz.y * 0.9, "%s %s: the bonnet is the bottom third at most (%s)" % [str(sz), mo[0], str(dr)])
		stage.free()


# --- the whole run: the hangar, the race, the hub ----------------------------------------------------------------------------------

func _region_at(sc: Node, dir: String) -> Vector2:
	var layer: RunActivityInput = sc._mg.regions_layer
	return (layer.rects()[ContractShapes.REGIONS.find(dir)] as Rect2).get_center()


func test_the_run_enters_the_race_from_the_hangar_races_and_returns_to_the_hub_with_the_save_recorded() -> void:
	var dr := Driver.new()
	dr.start(tree, Vector2(1280, 720), "space_rave")
	var sc: Node = dr.scene
	var prog: RunProgress = Session.run_progress
	assert_false(prog.puzzle_done("space", "bass_fixed") or prog.puzzle_done("space", "cloakroom_done"), "no task done: the race is open anyway")
	assert_true(dr.select("space_rave.race"), "the pilot is chosen in the hub")
	assert_true(dr.in_node("space_race"), "the hangar (%s)" % dr.node())
	var host: RaceStageHost = sc.race_host
	assert_true(sc.stages.has("race_space"), "the street was built on entering the hangar")
	assert_eq(str(sc.active_world), "space_rave", "the rave is still shown")
	assert_true(dr.select("space_race.race"), "the racer is chosen")
	assert_true(dr.seated(), "the race seats")
	var a: RaceActivity = dr.act()
	assert_true(a != null, "it is the race")
	dr.step()
	assert_true(host.owning and str(sc.active_world) == "race_space", "the street is the stage on the seat's downbeat")
	assert_true(sc.pad_view.visible and sc.hud.visible, "the pads and the HUD stay")
	var layer: RunActivityInput = sc._mg.regions_layer
	assert_true(layer != null, "the four driving regions stand over the stage area")
	if layer == null:
		dr.finish()
		return
	for rr: Rect2 in layer.rects():
		for pr: Rect2 in (sc.pad_view.button_rects() as Dictionary).values():
			assert_false(rr.intersects(pr), "a driving region never covers a pad (%s, %s)" % [str(rr), str(pr)])
	var swaps := host.log.filter(func(x: Dictionary) -> bool: return x["kind"] == "swap_in")
	assert_eq(swaps.size(), 1)
	assert_true(absf(float(swaps[0]["t"]) - dr.mg().seat_t) < 0.05, "swapped on the seat")
	var taps := 0
	var guard := 0
	var phases_before: int = sc.engine.phase_n
	while dr.mg().state != "" and guard < 9000:
		var sit := a.cur
		if not sit.is_empty() and str(sit["selected"]) == "" and dr.t() - float(sit["t_spawn"]) > 0.5:
			var owner: String = sc.dispatch_tap(_region_at(sc, Bot.best_dir(sit)))
			assert_eq(owner, "world_regions", "a stage tap is the driver's")
			taps += 1
		if guard % 300 == 0 and dr.mg().state == "active":
			assert_eq(str(sc.active_world), "race_space", "the street stays through the phase starts")
		dr.step()
		guard += 1
	assert_true(taps >= 5, "the regions drove the car (%d taps)" % taps)
	assert_true(sc.engine.phase_n > phases_before, "the music went on through phases")
	assert_true(a.judged_count() > 50, "the pads were judged and heard by the race (%d)" % a.judged_count())
	assert_true(a.finished(), "the race finished (%s)" % str(a.state()))
	assert_eq(str(sc.active_world), "space_rave", "the rave is back")
	assert_false(host.owning)
	var rec: Dictionary = prog.data["raves"]["space"]["race"]
	assert_eq(int(rec["runs"]), 1, "the race is recorded")
	assert_eq(int(rec["wins"]), 1 if a.position == 1 else 0, "won as it finished (position %d)" % a.position)
	assert_near(float(rec["best"]), a.race_time(), 0.01, "its time")
	assert_eq(str(prog.rave_theme()), "space", "the theme is kept")
	assert_false(prog.puzzle_done("space", "bass_fixed"), "the puzzles untouched")
	assert_true(dr.in_node("space_rave", 90.0), "back to the hub (%s)" % dr.node())
	assert_true(dr.select("space_rave.race"), "and the race can be run again")
	assert_true(dr.in_node("space_race", 60.0))
	assert_true(dr.select("space_race.race"), "the racer again")
	assert_true(dr.seated(), "seated again")
	dr.step()
	assert_eq(str(sc.active_world), "race_space", "the same street")
	dr.finish()
