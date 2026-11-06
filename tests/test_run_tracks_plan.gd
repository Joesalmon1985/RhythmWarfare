extends TestCase
## Track scenes: the scene plan (docs/RUN_TRACK_SCENES.md "The scene plan"), RunTrackPlan.compute as a pure function: the entry bar, the laps, the doors, the chart and the lap boundaries, with the
## contract's worked example ("Go Back") built from a synthetic pack with the same numbers, and the edge cases.

const Fx := preload("res://tests/fixtures/track_scenes/track_scene_fixtures.gd")


## A pack's facts without a pack: `bars` long at `bpm`, sections [[id, role, first bar, end bar]].
func _info(bpm: float, bars: float, sections: Array, fd := 0.0, intensity := {}, charts := {"normal": [], "easy": []}, default_chart := "normal") -> Dictionary:
	var bar := 240.0 / bpm
	var secs: Array = []
	for s in sections:
		secs.append({"id": s[0], "role": s[1], "start_s": fd + float(s[2]) * bar, "end_s": fd + float(s[3]) * bar})
	return {"id": "t", "dir": "/x/t", "bpm": bpm, "first_downbeat_s": fd, "duration_s": fd + bars * bar, "sections": secs, "intensity": intensity, "charts": charts, "default_chart": default_chart}


func test_the_worked_example_go_back() -> void:
	Fx.clear()
	var dir := Fx.write_pack("acuna_go_back", Fx.go_back_spec())
	var res := TrackPack.load_pack(dir, false)
	assert_eq(res["errors"], [], "the synthetic Go Back is a valid pack")
	if res["pack"] == null:
		return
	var p := RunTrackPlan.compute(RunTrackPlan.info_of(res["pack"]), {"track": "acuna_go_back"})
	assert_false(p.has("error"))
	var beat := 60.0 / 174.0032
	assert_near(float(p["bpm"]), 174.0032, 1e-9, "the track's own tempo")
	assert_near(float(p["beat_s"]), beat, 1e-12)
	assert_eq(int(p["entry_bar"]), 40, "drop1 at bar 56 minus the 16-bar lead-in")
	assert_eq(int(round(float(p["half_bar"]))), 108, "half-way through 298.6 s is bar 108")
	assert_eq(int(p["laps"]), 4, "round((108 - 40) / 16) = 4 laps")
	assert_eq(str(p["laps_rule"]), "half")
	assert_near(float(p["entry_t"]), 0.0013 + 40.0 * 4.0 * beat, 1e-9, "scene time 0 is the downbeat of bar 40")
	assert_near(float(p["lap_s"]) * 4.0, 88.0, 0.5, "the scene lasts 88 s")
	assert_near(float(p["end_t"]), 0.0013 + 104.0 * 4.0 * beat, 1e-9, "bars 40 to 104 of the track")
	var bounds: Array = p["lap_scene_t"]
	assert_eq(bounds.size(), 5)
	for k in 5:
		assert_near(float(bounds[k]), float(k) * 64.0 * beat, 1e-9, "lap boundary %d at %d x 64 beats" % [k, k])
	assert_near(float(bounds[2]), 44.0, 0.2, "the player can leave after 44 s,")
	assert_near(float(bounds[3]), 66.0, 0.3, "66 s")
	assert_near(float(bounds[4]), 88.0, 0.4, "or, by default, 88 s")
	assert_eq(int(p["doors_from_lap"]), 2, "doors open from lap 2")
	assert_eq(str(p["chart"]), "normal")
	assert_eq((p["cues"] as Array).size(), (res["pack"] as TrackPack).charts["normal"].size())
	Fx.clear()


func test_entry_rules_drop2_start_and_overrides() -> void:
	var info := _info(174.0, 216.0, [["intro", "intro", 0, 48], ["d1", "drop", 56, 96], ["b", "breakdown", 96, 152], ["d2", "drop", 160, 208]])
	var p2 := RunTrackPlan.compute(info, {"track": "t", "entry": "drop2"})
	assert_eq(int(p2["entry_bar"]), 144, "drop2: the second drop minus the lead-in")
	assert_eq(int(p2["laps"]), 4, "drop2: the whole laps before the last 2 bars ((216 - 2 - 144) / 16 = 4)")
	assert_eq(str(p2["laps_rule"]), "drop2")
	var only := _info(174.0, 216.0, [["d1", "drop", 56, 96]])
	assert_eq(int(RunTrackPlan.compute(only, {"track": "t", "entry": "drop2"})["entry_bar"]), 40, "drop2 with one drop falls back to drop1")
	var ps := RunTrackPlan.compute(info, {"track": "t", "entry": "start"})
	assert_eq(int(ps["entry_bar"]), 0)
	assert_eq(int(ps["laps"]), 7, "start: the end nearest half-way (bar 108: 7 laps end at 112)")
	var cap := RunTrackPlan.compute(info, {"track": "t", "entry": "start", "max_laps": 5})
	assert_eq(int(cap["laps"]), 5, "never more than max_laps")
	var sb := RunTrackPlan.compute(info, {"track": "t", "start_bar": 100})
	assert_eq(int(sb["entry_bar"]), 100, "start_bar overrides the entry")
	assert_eq(int(sb["laps"]), 2, "at least 2 laps (half-way is behind the entry)")
	var lp := RunTrackPlan.compute(info, {"track": "t", "laps": 3, "doors_from_lap": 5})
	assert_eq(int(lp["laps"]), 3, "laps overrides")
	assert_eq(str(lp["laps_rule"]), "override")
	assert_eq(int(lp["doors_from_lap"]), 3, "fewer laps than doors_from_lap: the doors open on the last")
	var lead := RunTrackPlan.compute(info, {"track": "t", "lead_in_bars": 8})
	assert_eq(int(lead["entry_bar"]), 48)
	var ch := RunTrackPlan.compute(info, {"track": "t", "chart": "hard"})
	assert_eq(str(ch["chart"]), "normal", "a chart the pack lacks falls back to its default_chart")
	assert_eq(str(RunTrackPlan.compute(info, {"track": "t", "chart": "easy"})["chart"]), "easy")


func test_no_drop_an_early_drop_and_a_short_track() -> void:
	var loud := _info(170.0, 200.0, [["intro", "intro", 0, 32], ["a", "other", 32, 64], ["b", "breakdown", 64, 120], ["c", "other", 120, 200]], 0.0, {"intro": -20.0, "a": -2.0, "b": -9.0, "c": -4.0})
	assert_eq(int(RunTrackPlan.compute(loud, {"track": "t"})["entry_bar"]), 16, "no drop: the loudest section (a, bar 32) minus the lead-in")
	var longest := _info(170.0, 200.0, [["intro", "intro", 0, 32], ["a", "other", 32, 64], ["b", "breakdown", 64, 140], ["o", "outro", 140, 200]])
	assert_eq(int(RunTrackPlan.compute(longest, {"track": "t"})["entry_bar"]), 48, "no intensities: the longest section that is not an intro or outro (b, bar 64)")
	var bare := _info(170.0, 200.0, [])
	assert_eq(int(RunTrackPlan.compute(bare, {"track": "t"})["entry_bar"]), 0, "no sections: bar 0")
	var early := _info(174.0, 120.0, [["d1", "drop", 8, 40]])
	var pe := RunTrackPlan.compute(early, {"track": "t"})
	assert_eq(int(pe["entry_bar"]), 0, "a drop in the first 16 bars: the entry is not below bar 0")
	assert_eq(int(pe["laps"]), 4, "half-way (bar 60) is nearest the end of lap 4 (bar 64)")
	var short := _info(174.0, 26.0, [["d1", "drop", 20, 26]])
	var psh := RunTrackPlan.compute(short, {"track": "t", "lead_in_bars": 0})
	assert_eq(int(psh["entry_bar"]), 10, "too near the end for a lap (bar 20 of 26): the entry moves back so one lap fits (26 - 16)")
	assert_eq(int(psh["laps"]), 1, "never past the end of the audio, even below the usual 2 laps")
	assert_eq(int(psh["doors_from_lap"]), 1, "and its one lap has the doors")
	assert_true(RunTrackPlan.compute(_info(174.0, 15.5, []), {"track": "t"}).has("error"), "fewer than 16 bars: no scene")
	var fit := _info(174.0, 70.0, [["d1", "drop", 20, 70]])
	var pf := RunTrackPlan.compute(fit, {"track": "t", "laps": 9})
	assert_eq(int(pf["laps"]), 4, "an override is still cut to the audio ((70 - 4) / 16 = 4 laps)")
	var offs := _info(175.0, 230.0, [["d1", "drop", 31, 71]], 31.5733)
	var po := RunTrackPlan.compute(offs, {"track": "t"})
	assert_eq(int(po["entry_bar"]), 15, "bars count from the first downbeat")
	assert_near(float(po["entry_t"]), 31.5733 + 15.0 * 240.0 / 175.0, 1e-9)
