extends TestCase
## The Space rave (docs/briefs/BEDSIT_RAVES_BRIEF.md sections 3 and 4): its map and rail data, the bedsit's north route into it, the way home, and puzzle one: the bass stem is locked on
## entry, freed only by the bass_knob activity, on a bar line with the transport continuous, kept for the run.

const Fx := preload("res://tests/fixtures/track_scenes/track_scene_fixtures.gd")
const TMP := "user://test_space_rave.json"

var _made: Array = []


func _theme() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string("res://content/raves/space.json"))


func _progress() -> RunProgress:
	for f in [TMP, TMP + ".tmp"]:
		if FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	var p := RunProgress.load_data(TMP, "user://none.json")
	p.run_started()
	return p


# --- the map and its rails

func test_the_map_loads_clean_and_nobody_stands_in_the_void() -> void:
	var m := StoryMap.load_chapter("space_rave")
	assert_eq(m.errors, [], "the map builds")
	var voids := 0
	for s in m.sectors:
		if bool(s.get("void", false)):
			voids += 1
	assert_eq(voids, 1, "one central void")
	for w in m.waypoints:
		assert_false(bool(m.sector(str(m.waypoints[w]["sector"])).get("void", false)), "waypoint %s is not in the void" % w)
	var rails := 0
	for w in m.resolved_walls():
		if str(w.get("kind", "")) == "railing" and not bool(w.get("implicit", false)):
			rails += 1
	assert_true(rails >= 12, "a railing on every void edge (%d)" % rails)
	assert_true(float(m.sector("stage")["floor"]) > float(m.sector("r6")["floor"]), "the stage is up on a dais")


func test_the_rails_and_routes_check_clean_with_holds() -> void:
	var d := RunData.load_path("bedsit")
	assert_eq(d.errors, [])
	var m := StoryMap.load_chapter("space_rave")
	var problems: Array = []
	for id in ["space_rave", "space_stage", "space_cloakroom", "space_bar", "space_race"]:
		var n: Dictionary = d.nodes[id]
		problems.append_array(StoryRailCheck.check_rail(m, id, str(n["waypoint"]), n["rail"]))
	assert_eq(problems, [], "check_rail_paths: 0 problems on the space nodes")
	var hub: Dictionary = (d.nodes["space_rave"]["rail"]["good"] as Array)[0]
	assert_true(bool(hub["choice"]) and float(hub["hold_bars"]) >= 8.0, "the hub is a choice viewpoint holding 8 bars")
	var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/maps/space_rave.json"))
	assert_true(raw["waypoints"].any(func(w: Dictionary) -> bool: return w["id"] == "hub_view" and bool(w.get("choice_view", false))), "hub_view is a choice_view waypoint")
	var routes: Dictionary = _theme()["routes"]
	for rid in routes:
		var r: Dictionary = routes[rid]
		assert_eq(ContractShapes.route(r), [], "route %s has the contract shape" % rid)
		var from := str(r["from"])
		for leg in r["legs"]:
			var args := {"to": str(leg["to"]), "via": leg.get("via", []), "style": str(leg["style"]), "bars": float(leg["bars"])}
			assert_eq(StoryRailCheck.check_move(m, from, args, rid), [], "%s leg to %s is a clean walk" % [rid, leg["to"]])
			assert_true(float(leg["hold_bars"]) >= 1.0, "each leg holds still after the move")
			from = str(leg["to"])
		assert_true(float(r["legs"][r["legs"].size() - 1]["hold_bars"]) >= 4.0, "%s ends in a choice-window hold" % rid)
	var stage: Array = d.nodes["space_stage"]["rail"]["good"]
	assert_eq(stage[stage.size() - 1]["to"], "deck_view", "the stage route ends at the deck")
	assert_true(float(stage[stage.size() - 1]["hold_bars"]) >= 4.0)


func test_the_hub_leads_to_five_places_and_the_stations_loop_back() -> void:
	var d := RunData.load_path("bedsit")
	var theme := _theme()
	for k in ["stage", "cloakroom", "bar", "race"]:
		assert_true((theme["activities"] as Dictionary).has(k), "an activity id per station: %s" % k)
	var next: Array = d.nodes["space_rave"]["next"].map(func(e: Dictionary) -> String: return str(e["to"]))
	for to in ["space_stage", "space_cloakroom", "space_bar", "space_race", "bedsit"]:
		assert_true(to in next, "the hub leads to %s" % to)
	for id in ["space_cloakroom", "space_bar", "space_race"]:
		assert_true(bool(d.nodes[id].get("placeholder", false)), "%s is a placeholder" % id)
		assert_true(d.nodes[id]["next"].any(func(e: Dictionary) -> bool: return str(e["to"]) == "space_rave" and bool(e.get("loop", false))), "%s loops back to the ring" % id)
	assert_eq(ContractShapes.theme_data(theme), [], "content/raves/space.json has the contract-2 shape")


# --- the way in and the way home

func test_the_bedsit_north_route_lands_in_the_real_space_rave_and_home_comes_back_north() -> void:
	var save := {}
	var r := BedsitNav.press(save, "top")
	assert_eq(r["route"], "space_rave")
	var d := RunData.load_path("bedsit")
	var n: Dictionary = d.nodes["space_rave"]
	assert_false(bool(n.get("placeholder", false)), "a real node now")
	assert_eq(n["world"], "space_rave")
	assert_eq((n["rail"] as Dictionary)["arrive"], "space_arrive", "an arrival pose")
	var home: Dictionary = ((n["next"] as Array).filter(func(e: Dictionary) -> bool: return str(e["to"]) == "bedsit"))[0]
	assert_eq(home["dir"], "up")
	assert_eq(d.nodes["bedsit"]["bedsit"]["facings"]["N"]["waypoint"], "bedsit_n")
	var m := StoryMap.load_chapter("bedsit", false)
	assert_near(float(m.waypoint("bedsit_n")["yaw"]), 0.0, 0.001, "facing north")
	assert_eq(BedsitNav.facing_of(save), "N", "the rave does not change the facing the player comes home to")
	assert_eq(_theme()["home"]["route"], "home")


# --- the knob

func _knob(beat_s: float) -> BassKnobActivity:
	var a := BassKnobActivity.new()
	a.setup({"beat_s": beat_s, "config": JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/bass_knob.json"))})
	a.begin(0.0)
	return a


func test_the_knob_resists_twice_and_the_third_touch_frees_it() -> void:
	var bs := 60.0 / 174.0
	var a := _knob(bs)
	assert_eq(a.state()["frame"], BassKnobActivity.FRAME_STUCK)
	assert_true(a.tap("knob", 1.0))
	a.update(1.0 + 0.1 * bs)
	assert_eq(a.state()["frame"], BassKnobActivity.FRAME_STRAIN, "straining after the first touch")
	assert_true(absf(a.wobble_at(1.0 + 0.2 * bs)) > 0.0, "a visible wobble")
	a.update(1.0 + 2.0 * bs)
	assert_eq(a.state()["frame"], BassKnobActivity.FRAME_STUCK)
	assert_true(a.tap("knob", 2.0))
	assert_false(a.state()["freed"], "two touches: still stuck")
	assert_true(a.tap("knob", 3.0))
	a.update(3.0 + 0.1)
	assert_true(a.state()["freed"])
	assert_eq(a.state()["frame"], BassKnobActivity.FRAME_FREE)
	a.update(3.0 + 2.0 * bs)
	assert_eq(a.state()["frame"], BassKnobActivity.FRAME_UP)
	assert_false(a.is_done())
	assert_eq(a.result()["flags_to_set"], [], "nothing set before it is done")
	a.update(3.0 + 4.0 * bs)
	assert_true(a.is_done())
	var res := a.result()
	assert_true(bool(res["completed"]))
	assert_true("rave.space.bass_fixed" in res["flags_to_set"])
	assert_eq((a.things() as Array)[0]["id"], "bass_knob", "the knob is a thing of the room (ruling 38)")
	assert_true(a.make_view() == null, "no overlay view")


func test_leaving_before_it_is_free_completes_nothing() -> void:
	var a := _knob(0.3)
	a.tap("knob", 1.0)
	a.request_leave(2.0)
	assert_true(a.is_done())
	assert_false(bool(a.result()["completed"]))
	assert_eq(a.result()["flags_to_set"], [])


func test_the_knob_is_touched_through_a_world_region_over_its_screen_point() -> void:
	var m := StoryMap.load_chapter("space_rave")
	var wp: Dictionary = m.waypoint("deck_view")
	var at: Vector2 = wp["at"]
	var pose := {"cam": Vector3(at.x, float(m.sector("stage")["floor"]) + 1.6, at.y), "yaw": float(wp["yaw"]), "pitch": 0.0}
	var area := Vector2(844, 250)
	var pr: Dictionary = StoryProjector.project(Vector3(0.0, 1.74, -25.12), pose, area)
	assert_true(bool(pr["visible"]), "the knob is in the picture from the deck")
	assert_eq(SpaceRaveHost.hit(pr["screen"], area, pose), "knob")
	assert_eq(SpaceRaveHost.hit(pr["screen"] + Vector2(300, 0), area, pose), "")


# --- the bass lock

func _audio(d: RunData) -> RunAudio:
	var a := RunAudio.new()
	tree.root.add_child(a)
	a.configure(d)
	_made.append(a)
	return a


func _cleanup() -> void:
	for a in _made:
		if is_instance_valid(a):
			(a as RunAudio).stop()
			(a as RunAudio).free()
	_made.clear()
	Fx.clear()


func _pump(a: RunAudio, t: float) -> void:
	for path in a._requested:
		for _i in 400:
			if ResourceLoader.load_threaded_get_status(str(path)) != ResourceLoader.THREAD_LOAD_IN_PROGRESS:
				break
			OS.delay_msec(5)
	while not a._schedule.is_empty() and float(a._schedule[0]["t"]) <= t:
		var item: Dictionary = a._schedule.pop_front()
		a._run(item, float(item["t"]), 0.0)
	while not a.track._schedule.is_empty() and float(a.track._schedule[0]["t"]) <= t:
		var it: Dictionary = a.track._schedule.pop_front()
		a.track.run_item(it, float(it["t"]), 0.0)
	a.track.step(t, 0.0)


func _run(e: RunEngine, a: RunAudio, t_end: float, from := -0.5) -> float:
	var t := from
	var pressed := {}
	while t < t_end and not e.over:
		for ev in e.update(t):
			a.on_event(ev)
		_pump(a, t)
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			if not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
				e.release(int(n["pad"]), float(n["end_time"]) if n["type"] == "hold" else float(n["time"]) + 0.06, int(n["pad"]))
		t += 1.0 / 30.0
	return t


func _count(a: RunAudio, kind: String) -> int:
	return a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == kind).size()


func test_the_bass_is_locked_on_entry_freed_by_the_knob_on_a_bar_line_without_a_restart_and_kept() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", Fx.go_back_spec())
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}})
	assert_eq(d.errors, [])
	var a := _audio(d)
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.track_gate = a.track.is_ready
	a.track.notes_fn = func() -> Array: return e.level.notes
	a.track.prepare(d, "warehouse")
	var prog := _progress()
	var host := SpaceRaveHost.new()
	host.progress = prog
	host.track_audio = a.track
	host.track = "acuna_go_back"
	host.beat_s = e.beat_s
	host.phase_t0_fn = func() -> float: return e.phase_t0
	var stage_log: Array = []
	host.apply_fn = func(act: Dictionary) -> void: stage_log.append(act)
	host.enter("space_rave", 0.0)  # (before the scene starts, as the engine's phase_start does it)
	assert_true(host.locked, "locked on entry: bass_fixed is false")
	assert_eq(prog.rave_theme(), "space")
	assert_true(stage_log.any(func(x: Dictionary) -> bool: return x["action"] == "crowd_cap" and float(x["args"]["cap"]) <= 25.0), "the crowd is capped quiet")
	assert_true(stage_log.any(func(x: Dictionary) -> bool: return x["action"] == "piece_off"), "the stage lights are down")
	e.begin("warehouse")
	host.beat_s = e.beat_s
	var t := _run(e, a, 20.0 * e.beat_s)
	var tr: TrackTransport = a.track._live()["transport"]
	assert_true(tr.is_stem_locked("bass"))
	assert_eq(tr.stem_gain("bass"), 0.0)
	var starts0 := _count(a, "start")
	var act := _knob(e.beat_s)
	var t_fixed := 21.3 * e.beat_s
	for tt in [18.5 * e.beat_s, 20.0 * e.beat_s]:
		act.tap("knob", tt)
		host.step(tt, act.state())
	assert_true(tr.is_stem_locked("bass"), "two touches: the bass stays locked")
	assert_eq(host.unlock_t, -1.0)
	act.tap("knob", t_fixed)
	act.update(t_fixed)
	host.step(t_fixed, act.state())
	var t_u := host.unlock_t
	assert_near(t_u, 24.0 * e.beat_s, 1e-6, "the next bar line (beat 24)")
	assert_true(stage_log.any(func(x: Dictionary) -> bool: return x["action"] == "piece_on" and absf(float(x["t0"]) - t_u) < 1e-9), "the stage lights come up on the same line")
	assert_true(stage_log.any(func(x: Dictionary) -> bool: return x["action"] == "crowd_cap" and float(x["args"]["cap"]) >= 100.0 and absf(float(x["t0"]) - t_u) < 1e-9), "the crowd dances from the same line")
	t = _run(e, a, 23.9 * e.beat_s, t)
	assert_true(tr.is_stem_locked("bass"), "still locked until the bar line")
	t = _run(e, a, 26.0 * e.beat_s, t)
	var un: Array = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "unlock")
	assert_eq(un.size(), 1)
	assert_near(float(un[0]["t"]), t_u, 1e-9)
	assert_near(float(un[0]["ramp_s"]), 4.0 * e.beat_s, 1e-9, "a one-bar ramp")
	assert_false(tr.is_stem_locked("bass"))
	assert_eq(_count(a, "start"), starts0, "no restart")
	assert_eq(_count(a, "seek") + _count(a, "stop"), 0, "the transport position is continuous: no seek")
	assert_true(a.track._live()["transport"] == tr)
	act.update(t_fixed + 4.0 * e.beat_s)
	assert_true(act.is_done())
	for f in act.result()["flags_to_set"]:
		prog.apply_activity_flag(str(f))
	assert_true(prog.puzzle_done("space", "bass_fixed"))
	host.leave(32.0 * e.beat_s)
	assert_eq(prog.rave_theme(), "")
	var locks_before: int = host.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "lock").size()
	host.enter("space_stage", 40.0 * e.beat_s)
	assert_false(host.locked, "re-entering the stage does not lock the bass again")
	assert_eq(host.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "lock").size(), locks_before)
	assert_false(tr.is_stem_locked("bass"))
	assert_true(prog.has_flag("space_bass_fixed"), "the deck's hotspot is hidden by its run flag")
	_cleanup()


func test_the_dev_flag_starts_with_the_bass_fixed() -> void:
	OS.set_environment("RW_SPACE_BASS_FIXED", "1")
	var prog := _progress()
	var host := SpaceRaveHost.new()
	host.progress = prog
	host.enter("space_rave", 0.0)
	OS.set_environment("RW_SPACE_BASS_FIXED", "")
	assert_false(host.locked)
	assert_true(prog.puzzle_done("space", "bass_fixed"))


func test_a_scene_that_is_not_the_rave_is_left_alone() -> void:
	var host := SpaceRaveHost.new()
	host.progress = _progress()
	host.enter("bedsit", 0.0)
	assert_false(host.in_rave)
	assert_eq(host.log, [])
