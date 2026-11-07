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
		assert_eq(bool(d.nodes[id].get("placeholder", false)), id == "space_race", "%s: only the hangar is still a placeholder" % id)
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

## A stage of the Space rave's world (the real map, the Mothership's art) over a stage area of `size` px, as the run builds it.
func _stage(size: Vector2) -> StoryStage:
	var run := StoryRun.create({}, "res://content/story/space_rave.json")
	var stage := StoryStage.new()
	stage.size = size
	tree.root.add_child(stage)
	stage.setup(StoryAssets.load_art("mothership"), run.data, run)
	stage.attach_world(stage.map, true)
	stage.lowres.size = size
	stage.lowres._fit()
	return stage


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
	var stage := _stage(Vector2(1280, 460))
	stage.player.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": "deck_view", "bars": 0.01, "cut": true}})
	var a := _knob(60.0 / 174.0)
	stage.set_things(a.things())
	stage.update(2.0, 60.0)
	var r: Variant = stage.thing_screen_rect("bass_knob")
	assert_true(r != null, "the knob is in the picture from the deck")
	if r != null:
		var rr: Rect2 = r
		assert_true(Rect2(Vector2.ZERO, stage.size).encloses(rr) and rr.size.y >= 48.0, "inside the strip and at least 48 px tall (%s)" % str(rr))
		assert_eq(SpaceRaveHost.hit_rect(rr.get_center(), rr), "knob")
		assert_eq(SpaceRaveHost.hit_rect(rr.get_center() + Vector2(300, 0), rr), "")
	assert_eq(SpaceRaveHost.hit_rect(Vector2(10, 10), null), "", "no rect (not drawn): no region")
	stage.free()


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


# --- the generator keeps the activity blocks of themes.json (integration step 1)

func test_themes_json_keeps_the_cloakroom_and_bar_blocks_and_the_generator_merges_them() -> void:
	var t: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/bedsit/themes.json"))
	for block in ["cloakroom", "bar"]:
		assert_true(t.has(block), "themes.json has the %s block" % block)
		for th in ["space", "magic", "dinos", "transport"]:
			assert_true((t[block] as Dictionary).has(th), "%s.%s" % [block, th])
	var src := FileAccess.get_file_as_string("res://tools/run/make_bedsit.py")
	assert_true(src.contains("merge_themes(themes_json()"), "the writer merges instead of overwriting")
	var out: Array = []
	var code := OS.execute("python3", ["-I", "-c", "import sys,json,pathlib;sys.path.insert(0,sys.argv[1]);import make_bedsit as m;print(sorted(m.merge_themes(m.themes_json(),pathlib.Path(sys.argv[2])).keys()))",
			ProjectSettings.globalize_path("res://tools/run"), ProjectSettings.globalize_path("res://content/bedsit/themes.json")], out)
	if code == 0:
		assert_true(str(out[0]).contains("'bar'") and str(out[0]).contains("'cloakroom'"), "a regeneration keeps both blocks: %s" % str(out))


# --- the whole rave in the real run scene (integration: ruling 38, contract 10) ---------------------------------------------------------------------

const Driver := preload("res://tests/fixtures/space_run_driver.gd")


func test_the_three_activity_nodes_exist_with_their_holds_hotspots_and_things_in_the_rooms_sectors() -> void:
	var d := RunData.load_path("bedsit")
	var m := StoryMap.load_chapter("space_rave")
	var themes: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/bedsit/themes.json"))
	var want := {"space_cloakroom": ["cloak_hold", "cloak_counter", "cloakroom"], "space_bar": ["bar_hold", "bar_counter", "bar"]}
	for id: String in want:
		var n: Dictionary = d.nodes[id]
		assert_false(bool(n.get("placeholder", false)), "%s is a real scene" % id)
		var good: Array = n["rail"]["good"]
		assert_eq(str(good[good.size() - 1]["to"]), want[id][0], "%s: the route from the hub ends at the hold" % id)
		assert_true(float(good[good.size() - 1]["hold_bars"]) >= 4.0, "%s: a hold for the activity" % id)
		var hold: Dictionary = m.waypoint(str(want[id][0]))
		var sec := str(hold["sector"])
		assert_eq(sec, "r7" if id == "space_cloakroom" else "r5", "the hold stands in the ring just outside the alcove, facing it")
		var rows: Array = (d.hotspots[id] as Array).filter(func(h: Dictionary) -> bool: return (h["on_success"] as Dictionary).has("activity"))
		assert_eq(rows.size(), 1, "%s: one hotspot carries the activity" % id)
		assert_eq(str(rows[0]["on_success"]["activity"]), want[id][2])
		assert_eq(str(rows[0]["anchor"]["thing"]), want[id][1], "anchored on the counter")
		assert_true(m.things.any(func(t: Dictionary) -> bool: return str(t["id"]) == want[id][1]), "the counter is a map thing")
		# the things the activity declares stand in the alcove's sector, inside its polygon
		var layout: Dictionary = (themes["cloakroom" if id == "space_cloakroom" else "bar"]["space"] as Dictionary)["layout"]
		assert_eq(str(layout["sector"]), "cloak" if id == "space_cloakroom" else "bar")
		var poly: PackedVector2Array = m.sector(str(layout["sector"]))["poly"]
		var pts: Array = []
		if id == "space_cloakroom":
			pts.append_array(layout["customer_slots"])
			for k in ["attendant_at", "rail_at", "symbol_at", "prev_at"]:
				pts.append(layout[k])
			var r0: Array = layout["rail_at"]
			var st: Array = layout["rail_step"]
			pts.append([float(r0[0]) + 7.0 * float(st[0]), float(r0[1]) + 7.0 * float(st[1])])
		else:
			for k in ["customer_at", "customer_glass_at", "glass_at", "bubble_at"]:
				pts.append(layout[k])
		for p: Array in pts:
			assert_true(Geometry2D.is_point_in_polygon(Vector2(float(p[0]), float(p[1])), poly), "%s: %s is inside the %s" % [id, str(p), str(layout["sector"])])
	# the customers, the attendant, the bartender and the DJ are crowd actors of those rooms, with homes there
	var story: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/story/space_rave.json"))
	var actors := (story["actors"] as Array).map(func(a: Dictionary) -> String: return str(a["id"]))
	var homes: Dictionary = m.homes
	var slots: Array = (themes["cloakroom"]["space"]["layout"] as Dictionary)["customer_slots"]
	for k in 8:
		assert_true(("customer_%d" % k) in actors and homes.has("customer_%d" % k), "customer_%d is a crowd actor with a home" % k)
		assert_eq(str(homes["customer_%d" % k]["sector"]), "cloak")
		assert_true((homes["customer_%d" % k]["at"] as Vector2).distance_to(Vector2(float(slots[k][0]), float(slots[k][1]))) < 0.05, "customer_%d's home is its slot in the layout" % k)
	for id in ["attendant", "bartender", "customer", "dj"]:
		assert_true(id in actors and homes.has(id), "%s is a crowd actor with a home" % id)
	assert_eq(str(homes["customer"]["sector"]), "bar")
	assert_eq(str(homes["attendant"]["sector"]), "cloak")
	assert_eq(str(homes["bartender"]["sector"]), "bar")
	# the pieces the activities switch are pieces of the map; the sheets have their sidecars
	for p in ["cloak_lamp", "bar_shelf_1", "bar_shelf_2", "bar_shelf_3", "bar_shelf_4"]:
		assert_true(m.things.any(func(t: Dictionary) -> bool: return str(t.get("piece", "")) == p), "%s is a map piece" % p)
	for sheet in ["cloak_coat", "cloak_symbols_space", "bar_glass_space", "bar_order_space", "sr_knob"]:
		var base := "res://assets/story/mothership/sprites/%s" % sheet
		assert_true(FileAccess.file_exists(base + ".png") and FileAccess.file_exists(base + ".json"), "%s has its sheet and its grid sidecar" % sheet)
		var g: Variant = JSON.parse_string(FileAccess.get_file_as_string(base + ".json"))
		assert_true(typeof(g) == TYPE_DICTIONARY and (g as Dictionary).has("grid"), "%s: {grid}" % sheet)


func test_the_run_plays_hub_cloakroom_hub_bar_stage_knob_and_home_with_the_save_flags_set() -> void:
	var dr := Driver.new()
	dr.start(tree, Vector2(1280, 720), "space_rave")
	var sc: Node = dr.scene
	var prog: RunProgress = Session.run_progress
	assert_eq(dr.node(), "space_rave")
	# --- the cloakroom
	assert_true(dr.select("space_rave.cloakroom"), "the attendant is chosen in the hub")
	assert_true(dr.in_node("space_cloakroom"), "the route leads to the cloakroom scene (%s)" % dr.node())
	assert_true(dr.select("space_cloakroom.cloakroom"), "the counter is chosen")
	assert_true(dr.seated(), "the cloakroom seats")
	var cloak: Variant = dr.act()
	assert_true(cloak is CloakroomActivity, "it is the cloakroom")
	var layer: RunActivityInput = sc._mg.controls_layer
	assert_true(layer != null and layer.ids == ["same", "different"], "two controls in the pad slots")
	var guard := 0
	while dr.mg().state == "active" and guard < 3000:
		dr.cloak_bot()
		dr.step()
		guard += 1
	assert_true(prog.puzzle_done("space", "cloakroom_done"), "the cloakroom flag is set in the save")
	assert_true(dr.until(func() -> bool: return dr.mg().state == "", 30.0), "the strip is handed back")
	assert_true(dr.select("space_cloakroom.back"), "the way back to the ring is chosen")
	assert_true(dr.in_node("space_rave", 60.0), "leaving returns to the hub (%s)" % dr.node())
	assert_true(prog.has_flag("space_cloakroom_done"), "and the activity's hotspot is gone for the run")
	# --- the bar
	assert_true(dr.select("space_rave.bar"), "the bartender is chosen in the hub")
	assert_true(dr.in_node("space_bar"), "the route leads to the bar scene (%s)" % dr.node())
	assert_true(dr.select("space_bar.bar"), "the counter is chosen")
	assert_true(dr.seated(), "the bar seats")
	assert_true(dr.act() is BarActivity)
	guard = 0
	while dr.mg().state == "active" and guard < 6000:
		dr.bar_bot()
		dr.step()
		guard += 1
	assert_true(prog.puzzle_done("space", "bar_done"), "the bar flag is set in the save")
	assert_true(dr.until(func() -> bool: return dr.mg().state == "", 30.0))
	assert_true(dr.select("space_bar.back"))
	assert_true(dr.in_node("space_rave", 60.0), "back in the hub (%s)" % dr.node())
	# --- the stage and the knob
	assert_true(dr.select("space_rave.stage"))
	assert_true(dr.in_node("space_stage"), "the stage (%s)" % dr.node())
	assert_true(dr.select("space_stage.deck"))
	assert_true(dr.seated(), "the deck seats the knob")
	assert_true(dr.act() is BassKnobActivity)
	for i in 3:
		var kp: Variant = dr.knob_point()
		assert_true(kp != null, "the knob is in the picture")
		if kp == null:
			break
		assert_eq(sc.dispatch_tap(kp), "activity_view", "the tap is the room's")
		dr.run_for(1.0)
	assert_true(prog.puzzle_done("space", "bass_fixed") or dr.until(func() -> bool: return prog.puzzle_done("space", "bass_fixed"), 10.0), "the bass is fixed in the save")
	assert_true(dr.until(func() -> bool: return dr.mg().state == "", 30.0))
	# --- home
	assert_true(dr.select("space_stage.home"))
	assert_true(dr.in_node("bedsit", 60.0), "home is the bedsit (%s)" % dr.node())
	for p in ["bass_fixed", "cloakroom_done", "bar_done"]:
		assert_true(prog.puzzle_done("space", p), "saved: %s" % p)
	dr.finish()


# --- the three-moment view test (contract 10): the things at the hold, in the real map ------------------------------------------------------------

const BEAT := 60.0 / 174.0


func _cloak_moments() -> Array:
	CloakroomSession.reset()
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/cloakroom.json"))
	var a := CloakroomActivity.new()
	a.setup({"seed": 7, "beat_s": BEAT, "config": cfg, "request": {"theme": "space"}, "world": WorldThings.new()})
	a.begin(0.0)
	var out: Array = []
	a.update(1.0 * BEAT)
	out.append(["demonstration", 1.0 * BEAT, a.things()])
	var t := 11.0 * BEAT
	a.update(t)
	for i in 3:
		a.tap(a.expected[a.answers.size()], t)
		t += 1.2
		a.update(t)
	out.append(["mid-way", t, a.things()])
	var guard := 0
	while str(a.state()["phase"]) != "payoff" and guard < 40:
		if str(a.state()["phase"]) == "await":
			a.tap(a.expected[a.answers.size()], t)
		t += 0.6
		a.update(t)
		guard += 1
	out.append(["payoff", t, a.things()])
	CloakroomSession.reset()
	return out


func _bar_moments() -> Array:
	BarActivity.forget_all()
	var cfg: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/minigames/bar.json"))
	var a := BarActivity.new()
	a.setup({"seed": 7, "beat_s": BEAT, "config": cfg, "wallet": null, "request": {"theme": "space"}})
	a.begin(0.0)
	var out: Array = []
	var t := 0.0
	var wrong_done := false
	var shot_demo := false
	var shot_mistake := false
	var guard := 0
	while str(a.state()["phase"]) != "payoff" and guard < 4000:
		t += 0.05
		a.update(t)
		var s := a.state()
		if str(s["phase"]) == "demo" and not shot_demo:
			shot_demo = true
			out.append(["demonstration", t, a.things()])
		if str(s["phase"]) == "input":
			var rec: Array = s["recipe"]
			var pos := int(s["pos"])
			if not wrong_done and pos == 0:
				wrong_done = true
				a.tap("ing:%d" % ((int(rec[0]) + 1) % 4), t)
				a.update(t + 0.05)
				out.append(["mistake", t + 0.05, a.things()])
				shot_mistake = true
			elif fmod(t, 0.5) < 0.05 and pos < rec.size():
				a.tap("ing:%d" % int(rec[pos]), t)
		guard += 1
	out.append(["payoff", t, a.things()])
	BarActivity.forget_all()
	return out


func test_every_thing_of_each_activity_is_inside_the_strip_and_at_least_48_px_tall_at_the_hold_in_three_moments() -> void:
	var cases := {"cloak_hold": _cloak_moments(), "bar_hold": _bar_moments()}
	cases["deck_view"] = [["stuck", 1.0, _knob(BEAT).things()]]
	var freed := _knob(BEAT)
	freed.tap("knob", 1.0)
	freed.tap("knob", 2.0)
	freed.tap("knob", 3.0)
	freed.update(7.0)
	cases["deck_view"].append(["free", 7.0, freed.things()])
	for sz: Vector2 in [Vector2(1280, 460), Vector2(1600, 460)]:
		var stage := _stage(sz)
		for hold: String in cases:
			stage.player.apply_action({"t0": 0.0, "action": "player_move", "args": {"to": hold, "bars": 0.01, "cut": true}})
			var moments: Array = cases[hold]
			assert_true(moments.size() >= 2, "%s: moments shot" % hold)
			for mo: Array in moments:
				stage.set_things(mo[2])
				stage.update(float(mo[1]), 60.0)
				assert_eq(stage.world.dynamic.errors, [], "%s %s: the sheets load" % [hold, mo[0]])
				assert_true((mo[2] as Array).size() >= 1, "%s %s: something to see" % [hold, mo[0]])
				for th: Dictionary in mo[2]:
					var r: Variant = stage.thing_screen_rect(str(th["id"]))
					assert_true(r != null, "%s %s %s %s: drawn" % [str(sz), hold, mo[0], th["id"]])
					if r == null:
						continue
					var rr: Rect2 = r
					assert_true(Rect2(Vector2.ZERO, sz).encloses(rr), "%s %s %s %s: inside the strip (%s)" % [str(sz), hold, mo[0], th["id"], str(rr)])
					assert_true(rr.size.y >= 48.0, "%s %s %s %s: at least 48 px tall (%.1f)" % [str(sz), hold, mo[0], th["id"], rr.size.y])
		stage.free()
