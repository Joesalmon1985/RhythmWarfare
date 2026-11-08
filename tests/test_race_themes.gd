extends TestCase
## The street race for every rave (docs/bedsit/RACE.md, per-theme table): the shared race checks run for Space, Magic, Dinos and Transport. The simulation reads only data, so each theme's
## course, map, race data and theme-file hook are checked, a race is simulated with the bot (finish, bounded, safe responses), and a real run is played: hub -> hangar -> race -> hub with
## the `raves.<theme>.race` record saved. (The Space-specific numbers stay in tests/test_race.gd.)

const Bot := preload("res://tests/fixtures/race_bot.gd")
const Driver := preload("res://tests/fixtures/space_run_driver.gd")

# theme -> [scene id prefix, the course id]
const THEMES := {"space": ["space", "race_space"], "magic": ["magic", "race_magic"], "dinos": ["dino", "race_dinos"], "transport": ["transport", "race_transport"]}
const SPACE_KINDS := ["braking_car", "rival_opening", "blocked_lane", "narrowing"]


func _json(path: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func test_every_theme_has_race_data_with_the_same_rules_and_its_own_course() -> void:
	var space := _json("res://content/races/space.json")
	for theme: String in THEMES:
		var d := _json("res://content/races/%s.json" % theme)
		var prefix: String = THEMES[theme][0]
		assert_eq(str(d["id"]), theme, "%s: id" % theme)
		assert_eq(str(d["course"]), THEMES[theme][1], "%s: its own course" % theme)
		assert_eq(str(d["stage_world"]), THEMES[theme][1], "%s: its own street" % theme)
		assert_eq(str(d["scene"]), "%s_race" % prefix, "%s: the race scene is the rave's race entrance" % theme)
		assert_eq(str(d["return_hotspot"]), "%s_race.back" % prefix, "%s: the way back" % theme)
		for key in ["timing", "speed", "outcomes"]:
			assert_eq(d[key], space[key], "%s: the same %s as Space (the rules are the same)" % [theme, key])
		assert_eq(d["rivals"], space["rivals"], "%s: the same three rivals' paces" % theme)
		assert_eq((d["situations"] as Array).map(func(s: Dictionary) -> String: return str(s["kind"])), SPACE_KINDS, "%s: the same four situations" % theme)
		var rave := _json("res://content/raves/%s.json" % theme)
		assert_eq(str(rave["race"]["course"]), THEMES[theme][1], "%s: the theme file names the theme's course" % theme)
		var cfg := _json("res://content/minigames/race.json")
		assert_eq(ContractShapes.activity_request(RunMinigameHost.build_request("race", cfg, theme, rave, "%s_race" % prefix, "hangar_view")), [], "%s: the activity request" % theme)


func test_every_course_and_street_loads_clean_with_every_lane_waypoint() -> void:
	for theme: String in THEMES:
		var c := RaceCourse.load_id(str(THEMES[theme][1]))
		assert_eq(c.errors, [], "%s: the course has contract 8's shape" % theme)
		assert_eq(c.lane_count(), 3, "%s: three lanes" % theme)
		assert_near(c.length_m, 2200.0, 0.01)
		var m := StoryMap.load_chapter(str(THEMES[theme][1]))
		assert_eq(m.errors, [], "%s: the street builds (sectors convex, portals meet)" % theme)
		var n := 0
		var wps: Array = c.lane_waypoints()
		for k in wps.size():
			for wid: String in wps[k]:
				n += 1
				assert_true(m.has_waypoint(wid) and str(m.waypoint(wid)["sector"]).begins_with("rd_"), "%s: %s is on the road" % [theme, wid])
		assert_true(n >= 3 * 70, "%s: a waypoint per lane per piece (%d)" % [theme, n])
		for s: float in [0.0, 400.0, 1000.0, 1700.0, 2200.0]:
			var a: Vector2 = c.point(s, c.lane_x(2.0))["at"]
			var b: Vector2 = ContractShapes.course_point(c.raw, 2.0, s)["at"]
			assert_true(a.distance_to(b) < 0.6, "%s: course_point and RaceCourse.point agree at %.0f m" % [theme, s])
			assert_eq(m.sector_at(a), c.road_at(s), "%s: the road sector at %.0f m" % [theme, s])
		assert_true(m.things.any(func(t: Dictionary) -> bool: return str(t["id"]) == "finish_gantry"), "%s: a finish gantry" % theme)
		assert_true(m.lights.size() > 40, "%s: lamps and lit signs (%d lights)" % [theme, m.lights.size()])
		var art := "res://assets/story/%s/sprites/dash.png" % str(THEMES[theme][1])
		assert_true(FileAccess.file_exists(art) or ResourceLoader.exists(art), "%s: its own dash sheet" % theme)


func test_the_courses_differ_from_each_other() -> void:
	var ends := {}
	for theme: String in THEMES:
		var c := RaceCourse.load_id(str(THEMES[theme][1]))
		var p: Vector2 = c.point(c.length_m, 0.0)["at"]
		ends[theme] = snappedf(p.x, 1.0) + snappedf(p.y, 1.0) * 10007.0
	assert_eq(ends.values().size(), 4)
	var uniq := {}
	for v: float in ends.values():
		uniq[v] = true
	assert_eq(uniq.size(), 4, "four different courses (finish points %s)" % str(ends))


func test_a_race_on_every_theme_finishes_with_safe_responses_and_bounded_penalties() -> void:
	for theme: String in THEMES:
		var best := Bot.play(Bot.make(7, theme), "best", 1.0)
		assert_true(best.finished(), "%s: finishes (%s)" % [theme, str(Bot.summary(best))])
		assert_eq(ContractShapes.activity_result(best.result()), [], "%s: the result has the contract's shape" % theme)
		assert_true(best.race_time() >= 55.0 and best.race_time() <= 95.0, "%s: ordinary good play takes 55 to 95 s (%.1f)" % [theme, best.race_time()])
		var rhythm_only := Bot.play(Bot.make(7, theme), "none", 1.0)
		assert_true(rhythm_only.finished() and rhythm_only.race_time() > best.race_time() + 3.0, "%s: no driving is slower (%.1f vs %.1f)" % [theme, rhythm_only.race_time(), best.race_time()])
		var poor := Bot.play(Bot.make(7, theme), "best", 0.6)
		assert_true(poor.finished() and poor.race_time() > best.race_time() + 5.0, "%s: poor rhythm is slower (%.1f vs %.1f)" % [theme, poor.race_time(), best.race_time()])
		var worst := Bot.play(Bot.make(7, theme), "worst", 0.0)
		assert_true(worst.finished() and worst.race_time() < worst.max_s, "%s: the worst play still finishes inside the bound (%.0f s)" % [theme, worst.race_time()])
		var again := Bot.play(Bot.make(7, theme), "best", 1.0)
		assert_eq(Bot.summary(again), Bot.summary(best), "%s: deterministic" % theme)
		for kind: String in SPACE_KINDS:
			var data := _json("res://content/races/%s.json" % theme)
			for s: Dictionary in data["situations"]:
				s["weight"] = 1.0 if str(s["kind"]) == kind else 0.0
			var a := Bot.play(Bot.make(5, theme, null, {"race_data": data}), "dither", 1.0)
			assert_true(a.finished(), "%s %s: finishes" % [theme, kind])
			for sit: Dictionary in a.sits:
				assert_true("bottom" in RaceActivity.safe_responses(sit), "%s %s from lane %d: bottom is safe" % [theme, kind, sit["lane"]])
				assert_true(str(sit.get("result", "")) in RaceActivity.SAFE, "%s %s: the dithering driver is safe" % [theme, kind])


func _region_at(sc: Node, dir: String) -> Vector2:
	var layer: RunActivityInput = sc._mg.regions_layer
	return (layer.rects()[ContractShapes.REGIONS.find(dir)] as Rect2).get_center()


func _run_a_race(theme: String) -> void:
	var prefix: String = THEMES[theme][0]
	var course: String = THEMES[theme][1]
	var dr := Driver.new()
	dr.start(tree, Vector2(1280, 720), "%s_rave" % prefix)
	var sc: Node = dr.scene
	var prog: RunProgress = Session.run_progress
	assert_true(dr.select("%s_rave.race" % prefix), "%s: the pilot is chosen in the hub" % theme)
	assert_true(dr.in_node("%s_race" % prefix), "%s: the race entrance (%s)" % [theme, dr.node()])
	var d := RunData.load_path("bedsit")
	assert_false(bool(d.nodes["%s_race" % prefix].get("placeholder", false)), "%s: the race entrance is a real scene" % theme)
	assert_true(sc.stages.has(course), "%s: the street was built on entering" % theme)
	assert_true(dr.select("%s_race.race" % prefix), "%s: the racer is chosen" % theme)
	assert_true(dr.seated(), "%s: the race seats" % theme)
	var a: RaceActivity = dr.act()
	assert_true(a != null, "%s: it is the race" % theme)
	if a == null:
		dr.finish()
		return
	assert_eq(a.theme, theme, "%s: the race reads the theme's data" % theme)
	dr.step()
	assert_eq(str(sc.active_world), course, "%s: the street is the stage on the seat's downbeat" % theme)
	assert_true(sc.pad_view.visible and sc.hud.visible, "%s: the pads and the HUD stay" % theme)
	var taps := 0
	var guard := 0
	while dr.mg().state != "" and guard < 9000:
		var sit := a.cur
		if not sit.is_empty() and str(sit["selected"]) == "" and dr.t() - float(sit["t_spawn"]) > 0.5:
			assert_eq(sc.dispatch_tap(_region_at(sc, Bot.best_dir(sit))), "world_regions", "%s: a stage tap is the driver's" % theme)
			taps += 1
		dr.step()
		guard += 1
	assert_true(taps >= 5, "%s: the regions drove the car (%d taps)" % [theme, taps])
	assert_true(a.judged_count() > 50, "%s: the pads were judged during the race (%d)" % [theme, a.judged_count()])
	assert_true(a.finished(), "%s: the race finished (%s)" % [theme, str(a.state())])
	assert_eq(str(sc.active_world), "%s_rave" % prefix, "%s: the rave is back" % theme)
	var rec: Dictionary = prog.data["raves"][theme]["race"]
	assert_eq(int(rec["runs"]), 1, "%s: the race is recorded" % theme)
	assert_eq(int(rec["wins"]), 1 if a.position == 1 else 0, "%s: won as it finished (position %d)" % [theme, a.position])
	assert_near(float(rec["best"]), a.race_time(), 0.01, "%s: its time" % theme)
	assert_true(dr.in_node("%s_rave" % prefix, 90.0), "%s: back to the hub (%s)" % [theme, dr.node()])
	assert_true(dr.select("%s_rave.race" % prefix), "%s: and the race can be run again" % theme)
	assert_true(dr.in_node("%s_race" % prefix, 60.0), "%s: the entrance again" % theme)
	assert_true(dr.select("%s_race.race" % prefix) and dr.seated(), "%s: seated again" % theme)
	dr.finish()


func test_a_whole_race_in_the_run_on_space() -> void:
	_run_a_race("space")


func test_a_whole_race_in_the_run_on_magic() -> void:
	_run_a_race("magic")


func test_a_whole_race_in_the_run_on_dinos() -> void:
	_run_a_race("dinos")


func test_a_whole_race_in_the_run_on_transport() -> void:
	_run_a_race("transport")
