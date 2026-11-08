extends TestCase
## Weather (package A9, hook H10, docs/engine/WEATHER.md): the map's `weather` key and the sectors' `rain` / `wet` are validated; rain falls only where a sector is open (or says
## rain: true); density is the streak count; the rain runs on the stage's clock (a pause freezes it); it is drawn in the 3D world inside the stage's low-res viewport (never over
## the HUD); and a map without weather renders exactly as before (a pixel comparison against a frame captured before the weather code, when a renderer is present).

const F := preload("res://tests/fixtures/weather_frame.gd")


func _sq(x0: float, z0: float, x1: float, z1: float) -> Array:
	return [[x0, z0], [x1, z0], [x1, z1], [x0, z1]]


## Four sectors in a row along x: an open yard (sky), a roofed shed, a roofed porch that lets rain in (rain: true), an open deck kept dry (rain: false), and a painted-sky
## ceiling (*_sky, the converted Doom maps) at the end.
func _yard(weather: Variant = {"rain": 1.0}) -> Dictionary:
	var d := {"textures": {"w": "textures/w.png", "dk_ceil_sky": "textures/s.png"}, "start": "a",
		"sectors": [{"id": "yard", "polygon": _sq(0, 0, 4, 4), "floor": 0, "ceiling": 6, "ceil_tex": "sky", "wall_tex": "w"},
			{"id": "shed", "polygon": _sq(4, 0, 8, 4), "floor": 0, "ceiling": 3, "wall_tex": "w"},
			{"id": "porch", "polygon": _sq(8, 0, 12, 4), "floor": 0, "ceiling": 3, "wall_tex": "w", "rain": true},
			{"id": "deck", "polygon": _sq(12, 0, 16, 4), "floor": 0, "ceiling": 6, "ceil_tex": "sky", "wall_tex": "w", "rain": false},
			{"id": "street", "polygon": _sq(16, 0, 20, 4), "floor": 0, "ceiling": 6, "ceil_tex": "dk_ceil_sky", "wall_tex": "w"}],
		"walls": [{"from": [4, 1], "to": [4, 3], "sector": "yard", "portal": "shed"}, {"from": [8, 1], "to": [8, 3], "sector": "shed", "portal": "porch"},
			{"from": [12, 1], "to": [12, 3], "sector": "porch", "portal": "deck"}, {"from": [16, 1], "to": [16, 3], "sector": "deck", "portal": "street"}],
		"waypoints": [{"id": "a", "at": [2, 2], "yaw": 0, "sector": "yard"}], "homes": [], "things": []}
	if weather != null:
		d["weather"] = weather
	return d


func _errs(d: Dictionary) -> String:
	return " | ".join(PackedStringArray(StoryMap.from_dict(d).errors))


## Night One's own map with weather on it: the dance floor opened to the rain (rain: true), wet.
func _night_one_wet(rain: float, wet := -1.0) -> Dictionary:
	var d: Dictionary = (JSON.parse_string(FileAccess.get_file_as_string(StoryMap.PATH % "night_one")) as Dictionary).duplicate(true)
	d["weather"] = {"rain": rain, "wind": 10.0, "drips": [{"at": [-6.5, 6.0], "h": 3.0}, {"at": [6.5, 6.0], "h": 3.0}]}
	for s in d["sectors"]:
		if str(s["id"]) == "floor":
			s["rain"] = true
			if wet >= 0.0:
				s["wet"] = wet
	return d


func _stage(map_dict: Dictionary = {}, reduced := false) -> StoryStage:
	OS.set_environment("RW_STORY_CAM", "floor_edge")
	var run := StoryRun.create({})
	var stage := StoryStage.new()
	stage.size = Vector2(1280, 460)
	stage.reduced = reduced
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_default(), run.data, run)
	var m: StoryMap = stage.map if map_dict.is_empty() else StoryMap.from_dict(map_dict, "night_one")
	assert_true(m.errors.is_empty(), "the test map is clean: %s" % str(m.errors))
	stage.attach_world(m, true)
	stage.update(0.0, 50.0)  # (a stage freed before its first update leaves the next stage's first frames different: drawn once, it does not)
	OS.set_environment("RW_STORY_CAM", "")
	return stage


func test_weather_validation() -> void:
	assert_eq(_errs(_yard()), "", "a clean map with rain")
	assert_eq(_errs(_yard(null)), "", "a clean map without weather")
	var m := StoryMap.from_dict(_yard({"rain": 0.5, "wind": -20, "drips": [{"at": [6, 2], "h": 2.8}]}))
	assert_eq(m.weather["rain"], 0.5)
	assert_eq(m.weather["wind"], -20.0)
	assert_eq((m.weather["drips"] as Array).size(), 1)
	assert_eq(str(m.weather["drips"][0]["sector"]), "shed", "a drip knows its sector")
	assert_true(StoryMap.from_dict(_yard(null)).weather.is_empty(), "no key: no weather")
	var cases := [
		[{"rain": 1.5}, "rain is 0..1"], [{"rain": -0.1}, "rain is 0..1"], [{"rain": "lots"}, "rain is 0..1"],
		[{"rain": 1, "wind": 75}, "wind is"], [{"rain": 1, "wind": "east"}, "wind is"],
		[{"rain": 1, "drips": {"at": [1, 1]}}, "drips is a list"], [{"rain": 1, "drips": [{"at": [1, 1], "h": 0}]}, "h is metres"],
		[{"rain": 1, "drips": [{"at": [1, 1]}]}, "h is metres"], [{"rain": 1, "drips": [{"at": [99, 1], "h": 2}]}, "lies in no sector"],
		[{"rain": 1, "drips": [{"at": [1], "h": 2}]}, "a point is [x, z]"], [{"rain": 1, "snow": 1}, "unknown key snow"], ["heavy", "weather: an object"],
	]
	for c in cases:
		assert_contains(_errs(_yard(c[0])), c[1], "weather %s is rejected" % str(c[0]))
	var bad := _yard()
	bad["sectors"][1]["rain"] = "yes"
	assert_contains(_errs(bad), "sector shed: rain is true or false")
	bad = _yard()
	bad["sectors"][1]["wet"] = 1.4
	assert_contains(_errs(bad), "sector shed: wet is 0..1")
	bad = _yard()
	bad["sectors"][1]["wet"] = "damp"
	assert_contains(_errs(bad), "sector shed: wet is 0..1")


func test_rain_falls_only_where_the_sector_is_open() -> void:
	var m := StoryMap.from_dict(_yard())
	assert_true(m.rain_open("yard"), "an open sky ceiling: rain")
	assert_false(m.rain_open("shed"), "a roof: no rain inside")
	assert_true(m.rain_open("porch"), "a roofed sector that says rain: true")
	assert_false(m.rain_open("deck"), "an open sector that says rain: false")
	assert_true(m.rain_open("street"), "a painted-sky ceiling (*_sky) is open")
	assert_eq(m.wet_of("yard"), 1.0, "an open sector is as wet as the rain")
	assert_eq(m.wet_of("shed"), 0.0, "a roofed one is dry")
	var dry := StoryMap.from_dict(_yard(null))
	for sid in ["yard", "shed", "porch", "street"]:
		assert_false(dry.rain_open(sid), "a dry map rains nowhere (%s)" % sid)
	assert_false(dry.has_weather(), "nothing to draw on a dry map")
	assert_false(StoryMap.from_dict(_yard({"rain": 0})).rain_open("yard"), "rain 0: none")
	var authored := _yard({"rain": 0.6})
	authored["sectors"][1]["wet"] = 0.3
	var am := StoryMap.from_dict(authored)
	assert_eq(am.wet_of("shed"), 0.3, "an authored wet wins (a spill under the roof)")
	assert_eq(am.wet_of("yard"), 0.6)
	# the light map the shader reads: rain texels exactly over the open sectors; every streak drawn over a roof is collapsed
	var w := StoryWeather.new()
	w.build(null, m, null)
	for p in [Vector2(2, 2), Vector2(10, 2), Vector2(18, 2)]:
		assert_true(w.rain_at(p), "rain at %s" % p)
	for p in [Vector2(6, 2), Vector2(14, 2), Vector2(30, 2), Vector2(2, -3)]:
		assert_false(w.rain_at(p), "no rain at %s" % p)
	var shown := {}
	for lo in [Vector3(0.0, -2.0, -4.0), Vector3(8.0, -2.0, -4.0)]:  # two boxes over the row (the maths the shader runs)
		for i in w.rain_mm.multimesh.instance_count:
			for t in [0.0, 1.3, 7.7]:
				var p3 := w.streak_pos(i, t, lo)
				if w.rain_at(Vector2(p3.x, p3.z)):
					shown[m.sector_at(Vector2(p3.x, p3.z))] = true
	assert_true(shown.has("yard") and shown.has("porch") and shown.has("street"), "streaks fall in the open sectors: %s" % str(shown.keys()))
	assert_false(shown.has("shed") or shown.has("deck"), "none inside the roofed shed or the dry deck")
	w.free()


func test_density_scales_the_streak_count() -> void:
	var counts: Array = []
	for r in [0.0, 0.25, 0.5, 1.0]:
		var w := StoryWeather.new()
		w.build(null, StoryMap.from_dict(_yard({"rain": r, "drips": [{"at": [6, 2], "h": 2.5}]})), null)
		counts.append(w.rain_mm.multimesh.instance_count)
		assert_eq(w.drip_mm.multimesh.instance_count, 0 if r == 0.0 else StoryWeather.DRIPS_PER, "drips only while it rains (rain %.2f)" % r)
		assert_eq(w.rain_mm.visible, r > 0.0)
		w.free()
	assert_eq(counts, [0, int(round(StoryWeather.RAIN_MAX * 0.25)), int(round(StoryWeather.RAIN_MAX * 0.5)), StoryWeather.RAIN_MAX], "streaks = RAIN_MAX x rain")
	var reduced := _stage(_night_one_wet(1.0), true)
	assert_eq(reduced.weather.rain_mm.multimesh.instance_count, int(round(StoryWeather.RAIN_MAX * StoryWeather.REDUCED_SHARE)), "reduced effects halves the rain")
	reduced.free()


func test_the_rain_runs_on_the_stage_clock() -> void:
	var stage := _stage(_night_one_wet(1.0))
	var w := stage.weather
	assert_true(w != null and w.get_parent() == stage.world, "the weather lives in the 3D world")
	assert_false(w.is_processing() or w.is_physics_processing(), "nothing advances on frames")
	stage.update(10.0, 50.0)
	var lo := w.box_lo()
	var before: Array = []
	for i in 8:
		before.append(w.streak_pos(i, w.song_t, lo))
	var gloss_before := w.gloss_mm.multimesh.get_instance_color(0) if w.gloss_shown > 0 else Color()
	for f in 5:  # a paused song: frames pass, the clock does not (RunPlay keeps calling update with the held time, or not at all)
		await tree.process_frame
		stage.update(10.0, 50.0)
	assert_eq(w.song_t, 10.0)
	assert_eq(w.box_lo(), lo)
	var after: Array = []
	for i in 8:
		after.append(w.streak_pos(i, w.song_t, w.box_lo()))
	assert_eq(after, before, "paused: every streak holds still")
	if w.gloss_shown > 0:
		assert_eq(w.gloss_mm.multimesh.get_instance_color(0), gloss_before, "the puddle shimmer holds too")
	assert_eq(float((w.rain_mm.material_override as ShaderMaterial).get_shader_parameter("song_t")), 10.0, "the shader's clock is the stage's")
	stage.update(10.25, 50.0)
	var moved := 0
	for i in 8:
		if not (w.streak_pos(i, w.song_t, w.box_lo()) as Vector3).is_equal_approx(before[i]):
			moved += 1
	assert_eq(moved, 8, "the song moves on: the rain falls")
	stage.update(10.0, 50.0)
	assert_eq(w.streak_pos(3, w.song_t, w.box_lo()), before[3], "a restart replays the same rain")
	stage.free()


func test_streaks_stay_inside_the_stage_strip() -> void:
	var stage := _stage(_night_one_wet(1.0))
	stage.update(6.0, 50.0)
	await tree.process_frame
	stage.update(6.0, 50.0)
	var w := stage.weather
	assert_true(w.get_viewport() == stage.lowres.sub, "drawn in the stage's low-res 3D viewport (not a canvas overlay)")
	var n: Node = w
	while n != null:
		assert_false(n is CanvasLayer, "no canvas layer between the rain and the world")
		n = n.get_parent()
	assert_true(stage.clip_contents and stage.lowres.clip_contents, "the stage clips its picture to its own rect (the pads and HUD are outside it)")
	var cam := stage.lowres.camera
	var sub := Rect2(Vector2.ZERO, Vector2(stage.lowres.sub.size))
	var strip := Rect2(Vector2.ZERO, stage.size)
	var k := stage.lowres_scale()
	var seen := 0
	var lo := w.box_lo()
	for i in w.rain_mm.multimesh.instance_count:
		var p := w.streak_pos(i, 6.0, lo)
		if not w.rain_at(Vector2(p.x, p.z)) or cam.is_position_behind(p):
			continue
		var sp := cam.unproject_position(p)
		if sub.has_point(sp):
			seen += 1
			assert_true(strip.has_point(sp * k), "a streak at %s lands at %s, inside the strip" % [p, sp * k])
	assert_true(seen > 20, "the rain is in view over the open floor (%d streaks)" % seen)
	assert_eq(w.draw_calls(), 3, "rain, drips and gloss: three draw calls")
	assert_true(w.gloss_shown > 0, "the wet floor shows the practicals' gloss (%d bands)" % w.gloss_shown)
	stage.free()
	var dry := _stage(_night_one_wet(1.0, 0.0))
	dry.update(6.0, 50.0)
	assert_eq(dry.weather.gloss_shown, 0, "wet 0: no gloss")
	dry.free()


func test_a_map_without_weather_renders_as_before() -> void:
	if DisplayServer.get_name() == "headless":
		print("  (test_weather: the pixel comparison needs a renderer; run without --headless to make it)")
	else:
		var base := Image.load_from_file(ProjectSettings.globalize_path(F.BASELINE))
		var now: Image = await F.shoot(tree)
		assert_true(now != null, "a frame was drawn")
		if now != null:
			base.convert(Image.FORMAT_RGB8)
			assert_eq(now.get_size(), base.get_size())
			var diff := 0
			if now.get_data() != base.get_data():
				for y in now.get_height():
					for x in now.get_width():
						if now.get_pixel(x, y) != base.get_pixel(x, y):
							diff += 1
			assert_eq(diff, 0, "Night One's low-res frame is the baseline's, pixel for pixel")
			print("  (test_weather: Night One's low-res frame %s differs from the baseline in %d pixels)" % [str(now.get_size()), diff])
	var stage := _stage()
	assert_true(stage.weather == null, "no weather node on Night One")
	var found := 0
	for c in stage.world.find_children("*", "", true, false):
		if c is StoryWeather or (c is MultiMeshInstance3D and str(c.name) in ["Rain", "Drips", "Gloss"]):
			found += 1
	assert_eq(found, 0, "nothing of the weather in the world")
	stage.free()
