extends TestCase
## Geography worlds (docs/engine/GEOGRAPHY_WORLDS.md, CONTRACTS.md 1, hook H1.6): a world flagged "geography" is a place in a map of places. Its one scene stays by its `down`
## loop and leads to the entry scene of other geography worlds in any direction and at any depth; picking a route out walks the route's polyline (rail.routes[dir]) to its
## threshold by the boundary, the passage frame shuts, the stage swaps and the arrival walks home. The fixture (tests/fixtures/geography) is merged into the main run the way the
## Doom overlay is: the main run's own worlds keep every rule they had.

const FIX := "res://tests/fixtures/geography"
const TMP := "user://test_geography"
const BEAT := 60.0 / 174.0
const TMP_SAVE := "user://test_geography_save.json"


func _read(path: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _write(path: String, v: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(v, "\t"))
	f.close()


## The main run with the fixture's worlds, scenes and music added (`mutate(run, music)` changes them before they are written and loaded).
func _data(tag: String, mutate: Callable = Callable()) -> RunData:
	var run := _read(RunData.RUN_PATH)
	var music := _read(RunData.MUSIC_PATH)
	var fr := _read(FIX + "/run.json")
	var fm := _read(FIX + "/music.json")
	run["worlds"] = (run["worlds"] as Array) + (fr["worlds"] as Array)
	run["nodes"] = (run["nodes"] as Array) + (fr["nodes"] as Array)
	music["nodes"] = (music["nodes"] as Array) + (fm["nodes"] as Array)
	if mutate.is_valid():
		mutate.call(run, music)
	var dir := TMP + "/" + tag
	_write(dir + "/run.json", run)
	_write(dir + "/music.json", music)
	return RunData.load_files(dir + "/run.json", dir + "/music.json", RunData.PACKS_DIR, 1, RunData.ARRANGEMENTS_DIR, dir + "/hotspots")


func _node(run: Dictionary, id: String) -> Dictionary:
	for n in run["nodes"]:
		if str(n["id"]) == id:
			return n
	return {}


func _has(errors: Array, needle: String) -> bool:
	return errors.any(func(e: Variant) -> bool: return str(e).contains(needle))


func _of(events: Array, kind: String) -> Array:
	return events.filter(func(ev: Dictionary) -> bool: return str(ev["kind"]) == kind)


# --- validation -----------------------------------------------------------------------------------------------------------------

func test_the_fixture_validates_and_the_main_run_is_unchanged() -> void:
	var d := _data("ok")
	assert_eq(d.errors, [], "the main run plus three one-scene geography worlds validates")
	for id in ["geo_floor", "geo_bar", "geo_lounge"]:
		assert_true(d.is_geography(id), "%s is a geography world" % id)
		assert_eq(RunRail.validate(id, d.nodes[id]["rail"]), [], "the rail of %s is clean (its route moves included)" % id)
		assert_true(d.leaves_world(id) and d._terminal(id), "%s's only scene leaves the world" % id)
		assert_eq(d.entry_of(id), id)
	assert_false(d.is_geography("warehouse"), "the main run's worlds are not geography worlds")
	assert_eq(int(d.nodes["geo_bar"]["depth"]), 2, "a world keeps its depth (the home cards, the tier)")
	assert_eq(RunData.load_default().errors, [], "the main run alone validates as before")


func test_the_route_moves_are_walkable_on_their_maps() -> void:
	var d := _data("walk")
	for id in ["geo_floor", "geo_bar", "geo_lounge"]:
		var n: Dictionary = d.nodes[id]
		var m := StoryMap.load_chapter(str(n["map"]), false)
		assert_eq(m.errors, [], "map %s loads" % n["map"])
		assert_eq(StoryRailCheck.check_rail(m, id, str(n["waypoint"]), n["rail"]), [], "the rail of %s walks" % id)
		var routes: Dictionary = n["rail"]["routes"]
		for k in routes:
			var mv: Dictionary = routes[k]
			for from in [str(n["waypoint"]), str(n["rail"]["good"][0]["to"])]:  # from home and from the top of the good rail (where a route window finds the player)
				var args := {"to": str(mv["to"]), "via": mv.get("via", []), "style": str(mv.get("style", "walk")), "bars": float(mv.get("bars", 3.0))}
				assert_eq(StoryRailCheck.check_move(m, from, args, "%s %s from %s" % [id, k, from]), [], "the %s move of %s walks from %s" % [k, id, from])


func test_geography_rules_reject_what_they_must() -> void:
	var to_non_entry := _data("non_entry", func(run: Dictionary, music: Dictionary) -> void:
		var side: Dictionary = _node(run, "geo_bar").duplicate(true)
		side["id"] = "geo_bar.side"
		side["scene"] = "side"
		side["entry"] = false
		side["next"] = [{"to": "geo_bar", "dir": "down", "label": "back", "loop": true}, {"to": "geo_floor", "dir": "up", "label": "floor"}]
		run["nodes"].append(side)
		music["nodes"].append({"id": "geo_bar.side", "audio": "dd_part2", "chart": "dd_part2", "treatment": "none"})
		_node(run, "geo_floor")["next"][1]["to"] = "geo_bar.side")
	assert_true(_has(to_non_entry.errors, "geography scene geo_floor: the route to geo_bar.side must lead to the entry scene of world geo_bar"), str(to_non_entry.errors))
	var no_stay := _data("no_stay", func(run: Dictionary, _m: Dictionary) -> void:
		(_node(run, "geo_lounge")["next"] as Array).remove_at(0))
	assert_true(_has(no_stay.errors, "geography scene geo_lounge needs its stay"), str(no_stay.errors))
	var out_of_map := _data("out_of_map", func(run: Dictionary, _m: Dictionary) -> void:
		_node(run, "geo_lounge")["next"][2]["to"] = "mothership")
	assert_true(_has(out_of_map.errors, "geo_lounge: the route to mothership leads out of the map of places"), str(out_of_map.errors))
	var bad_move := _data("bad_move", func(run: Dictionary, _m: Dictionary) -> void:
		_node(run, "geo_bar")["place"]["rail"]["routes"]["up"]["bars"] = 0
		_node(run, "geo_bar")["place"]["rail"]["routes"]["left"]["via"] = ["no_such_waypoint"])
	assert_true(_has(bad_move.errors, "rail.routes.up lasts 0.0 bars"), str(bad_move.errors))
	assert_true(_has(bad_move.errors, "waypoint 'no_such_waypoint' is not in map mothership"), str(bad_move.errors))
	# without the flag the same worlds fall under the old rules: a world exit goes one level deeper
	var flat := _data("flat", func(run: Dictionary, _m: Dictionary) -> void:
		for w in run["worlds"]:
			(w as Dictionary).erase("geography"))
	assert_true(_has(flat.errors, "exit scene geo_bar (depth 2): route to geo_floor at depth 1"), str(flat.errors))
	# a non-geography world still lets only its exit scene leave (unchanged)
	var main_bad := _data("main_bad", func(run: Dictionary, _m: Dictionary) -> void:
		(_node(run, "warehouse")["next"] as Array).append({"to": "mothership", "dir": "left", "label": "out"})
		_node(run, "warehouse")["place"]["rail"]["exits"]["left"] = "door")
	assert_true(_has(main_bad.errors, "scene warehouse: the route to mothership leaves the world, only the exit scene may"), str(main_bad.errors))


# --- the threshold and the walk ------------------------------------------------------------------------------------------------

func test_the_threshold_falls_back_to_the_route_move() -> void:
	var d := _data("thr")
	var j := RunJourney.new(d)
	assert_eq(j.threshold_of("geo_floor", "geo_bar"), "to_balcony", "up: rail.routes.up's `to`")
	assert_eq(j.threshold_of("geo_floor", "geo_lounge"), "to_bar", "right: rail.routes.right's `to`")
	assert_eq(j.threshold_of("geo_bar", "geo_lounge"), "deck_edge")
	assert_eq(j.threshold_of("geo_floor", "geo_floor"), "", "the stay has no threshold")
	assert_eq(j.threshold_move("geo_floor", "geo_bar")["via"], ["floor_edge"])
	assert_eq(j.threshold_of("warehouse.exit", "mothership"), "", "a main-run exit without thresholds or route moves: none (unchanged)")
	d.nodes["geo_floor"]["thresholds"] = {"geo_bar": "floor_edge"}
	assert_eq(j.threshold_of("geo_floor", "geo_bar"), "floor_edge", "an explicit threshold wins")


func test_the_threshold_walk_plays_the_polyline_and_ends_by_the_boundary() -> void:
	var d := _data("poly")
	var e := RunEngine.new(d)
	e.begin("geo_floor")
	var j := RunJourney.new(d)
	j.look_heralds = false
	j.on_event({"kind": "phase_start", "node": "geo_floor", "t": 0.0, "phase": 1}, e)
	var t_walk := e.t_of(64.0 - RunPassage.DOOR_BEATS)
	var t_b := e.t_of(64.0)
	var walk := j.threshold_leave(t_walk, t_b, "geo_floor", "geo_bar")
	assert_eq(walk.size(), 1)
	var a: Dictionary = walk[0]["args"]
	assert_eq(walk[0]["action"], "player_move")
	assert_eq(a["to"], "to_balcony")
	assert_eq(a["via"], ["floor_edge"], "the route's polyline")
	assert_true(bool(a["threshold"]))
	assert_eq(str(walk[0]["world"]), "night_one", "in the world being left")
	assert_true(float(walk[0]["t0"]) + float(a["bars"]) * j.rail.bar_s() <= t_b + 1e-9, "at the threshold by the boundary")
	assert_false(a.has("hold_bars"), "no time for the hold in the last beats")
	# with time to spare the move keeps its own bars and its hold
	var early := j.threshold_leave(e.t_of(16.0), t_b, "geo_floor", "geo_bar")
	assert_near(float(early[0]["args"]["bars"]), 3.0, 1e-6, "the route's 3 bars")
	assert_near(float(early[0]["args"]["hold_bars"]), 1.0, 1e-6, "and its hold of one bar")
	# a route with no move and no threshold: no walk (the frame alone, as before)
	assert_eq(j.threshold_leave(t_walk, t_b, "geo_floor", "geo_floor"), [])


## The run driven the way RunPlay drives it (the engine's events into the journey, the lock handler's walk at beat 61 of the last block), with a perfect player and a route per phase.
func _drive(d: RunData, start: String, picks: Array, until_phase: int) -> Dictionary:
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.begin(start)
	var j := RunJourney.new(d)
	j.look_heralds = false
	var events: Array = []
	var actions: Array = []
	var pressed := {}
	var door_phase := -1
	var t := 0.0
	while e.phase_n < until_phase and not e.over and t < 900.0:
		if e.window_open and e.choice == "" and e.phase_n - 1 < picks.size() and e.selected_route() != str(picks[e.phase_n - 1]):
			e.choose(str(picks[e.phase_n - 1]))
		if e.window_open and door_phase != e.phase_n and e.phase_beat_at(t) >= 64.0 - RunPassage.DOOR_BEATS:  # RunPlay._update_passage
			door_phase = e.phase_n
			var to0 := e.selected_route()
			if d.nodes.has(to0) and to0 != e.node_id and str(d.nodes[to0]["world"]) != str(d.nodes[e.node_id]["world"]):
				actions.append_array(j.threshold_leave(e.t_of(64.0 - RunPassage.DOOR_BEATS), e.t_of(64.0), e.node_id, to0))
		for ev in e.update(t):
			events.append(ev)
			actions.append_array(j.on_event(ev, e))
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			if not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]))
				if n["type"] == "hold":
					e.release(int(n["pad"]), float(n["end_time"]))
		t += 1.0 / 60.0
	return {"engine": e, "journey": j, "events": events, "actions": actions}


func test_a_floor_bar_floor_cycle_walks_out_cuts_and_arrives() -> void:
	var d := _data("cycle")
	var r := _drive(d, "geo_floor", ["geo_bar", "geo_floor", "geo_lounge"], 4)
	var ev: Array = r["events"]
	var j: RunJourney = r["journey"]
	var e: RunEngine = r["engine"]
	var phases: Array = _of(ev, "phase_start")
	assert_eq(phases.map(func(p: Dictionary) -> String: return str(p["node"])), ["geo_floor", "geo_bar", "geo_floor", "geo_lounge"], "Floor, Bar, Floor again, Lounge")
	var commits: Array = _of(ev, "route_commit")
	assert_eq(commits.size(), 3)
	assert_true(commits.all(func(c: Dictionary) -> bool: return not bool(c["same_world"])), "every route left its world (same_world false)")
	assert_eq(phases.map(func(p: Dictionary) -> int: return int(p["depth"])), [1, 2, 1, 2], "depth 2 back to depth 1 is fine")
	var acts: Array = r["actions"]
	var maps := ["night_one", "mothership", "night_one", "underworld"]
	var homes := ["floor_centre", "deck_centre", "floor_centre", "arena_floor"]
	var arrives := ["door", "deck_gallery_door", "door", "arena_edge"]
	var wants := [["to_balcony", ["floor_edge"]], ["deck_reactor_door", ["deck_gallery_door"]], ["to_bar", ["floor_bar"]]]
	for k in 3:
		var t_b := float(phases[k + 1]["t"])
		var walks := acts.filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_move" and bool((a["args"] as Dictionary).get("threshold", false)) and absf(float(a["t0"]) - (t_b - RunPassage.DOOR_BEATS * BEAT)) < 0.01)
		assert_eq(walks.size(), 1, "one threshold walk out of phase %d" % (k + 1))
		if walks.size() != 1:
			continue
		var w: Dictionary = walks[0]
		assert_eq(str(w["world"]), maps[k], "walked in the world being left (%d)" % (k + 1))
		assert_eq(w["args"]["to"], wants[k][0], "to the route's threshold (%d)" % (k + 1))
		assert_eq(w["args"]["via"], wants[k][1], "along its polyline (%d)" % (k + 1))
		assert_true(float(w["t0"]) + float(w["args"]["bars"]) * BEAT * 4.0 <= t_b + 1e-6, "there by the boundary (%d)" % (k + 1))
		# then the arrival in the next world: a cut to its doorway in the guard, the walk home
		var next_acts := acts.filter(func(a: Dictionary) -> bool: return str(a["world"]) == maps[k + 1] and float(a["t0"]) >= t_b - 3.0 * BEAT and float(a["t0"]) <= t_b + 0.01)
		var cut := next_acts.filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_move" and bool((a["args"] as Dictionary).get("cut", false)))
		assert_eq(cut.map(func(a: Dictionary) -> String: return str(a["args"]["to"])), [arrives[k + 1]], "the cut to the doorway of %s" % maps[k + 1])
		var home := next_acts.filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_move" and not bool((a["args"] as Dictionary).get("cut", false)))
		assert_eq(home.map(func(a: Dictionary) -> String: return str(a["args"]["to"])), [homes[k + 1]], "the walk home in %s" % maps[k + 1])
		assert_true(float(w["t0"]) < float(cut[0]["t0"]) if not cut.is_empty() else false, "the walk out starts before the cut (%d)" % (k + 1))
	assert_eq(j.world, "underworld")
	assert_eq(j.run_world, "geo_lounge")
	assert_eq(e.node_id, "geo_lounge")
	# the save: one entry per world, a world re-entered is no new one
	var prog := RunProgress.load_data("user://test_geography_prog.json", "user://none.json")
	var fresh: Array = phases.map(func(p: Dictionary) -> bool: return prog.enter(str(d.nodes[str(p["node"])]["world"])))
	assert_eq(fresh, [true, true, false, true], "the Floor re-entered is already reached")
	for wid in ["geo_floor", "geo_bar", "geo_lounge"]:
		assert_true(prog.reached_ids().has(wid))
	if FileAccess.file_exists("user://test_geography_prog.json"):
		DirAccess.remove_absolute("user://test_geography_prog.json")


func test_staying_is_the_down_loop() -> void:
	var d := _data("stay")
	var r := _drive(d, "geo_bar", [], 3)
	var phases: Array = _of(r["events"], "phase_start")
	assert_eq(phases.map(func(p: Dictionary) -> String: return str(p["node"])), ["geo_bar", "geo_bar", "geo_bar"], "nothing chosen: the default route is the stay")
	assert_true((r["actions"] as Array).all(func(a: Dictionary) -> bool: return not bool((a["args"] as Dictionary).get("threshold", false))), "no threshold walk")
	assert_true(_of(r["events"], "route_commit").all(func(c: Dictionary) -> bool: return bool(c["same_world"])))


# --- the real run scene ------------------------------------------------------------------------------------------------------

func _scene(d: RunData, routes: String, start: String) -> Dictionary:
	var saved := Session.run_progress
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", routes)
	OS.set_environment("RW_RUN_START", start)
	Session.run_start_node = ""
	var script: GDScript = load("res://src/run/run_play.gd")
	script.set("data_for_test", d)
	var host := Control.new()
	host.size = Vector2(1152, 648)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = host.size
	return {"host": host, "scene": scene, "saved": saved}


func _free(s: Dictionary) -> void:
	Session.run_progress = s["saved"]
	if FileAccess.file_exists(TMP_SAVE):
		DirAccess.remove_absolute(TMP_SAVE)
	(s["host"] as Control).queue_free()
	OS.set_environment("RW_RUN_VIRTUAL", "")
	OS.set_environment("RW_RUN_BOT", "")
	OS.set_environment("RW_RUN_ROUTES", "")
	OS.unset_environment("RW_RUN_START")


func _run_to(scene: Node, t_end: float) -> void:
	var t: float = scene._vt
	while t < t_end:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func test_the_run_scene_walks_the_route_then_swaps_the_world_and_back() -> void:
	var d := _data("scene")
	assert_eq(d.errors, [])
	var s := _scene(d, "up,up", "geo_floor")  # the Floor: up is the Bar; the Bar: up is the Floor
	var scene: Node = s["scene"]
	assert_true(scene.engine != null and scene.data == d, "the scene plays the fixture's data")
	_run_to(scene, 60.0 * BEAT)
	assert_eq(scene.engine.selected_route(), "geo_bar", "the scripted tap is on the way up")
	_run_to(scene, 63.9 * BEAT)
	var walks: Array = (scene.journey_log as Array).filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_move" and bool((a["args"] as Dictionary).get("threshold", false)))
	assert_eq(walks.size(), 1, "the lock handler walked to the threshold")
	if walks.size() == 1:
		assert_near(float(walks[0]["t0"]), 61.0 * BEAT, 0.01, "from beat 61")
		assert_eq(walks[0]["args"]["via"], ["floor_edge"], "along the route's polyline")
		assert_eq(str(walks[0]["world"]), "night_one")
	var st: StoryStage = scene.stages["night_one"]["stage"]
	assert_true((st.player.pose_at(64.0 * BEAT)["pos"] as Vector2).distance_to(st.map.waypoint("to_balcony")["at"]) < 0.05, "at the threshold on the boundary")
	assert_true(scene._passage.aperture < 0.3, "the frame shut to the doorway before the swap (%f)" % scene._passage.aperture)
	assert_eq(scene.active_world, "night_one")
	_run_to(scene, 64.4 * BEAT)
	assert_eq(scene.engine.node_id, "geo_bar")
	assert_eq(scene.active_world, "mothership", "the stage swapped on the downbeat")
	var bar: StoryStage = scene.stages["mothership"]["stage"]
	_run_to(scene, 76.0 * BEAT)
	assert_true((bar.player.pose_at(76.0 * BEAT)["pos"] as Vector2).distance_to(bar.map.waypoint("deck_centre")["at"]) < 0.05, "the arrival walked home in the Bar")
	assert_eq(scene._passage.aperture, 1.0, "the frame is open again")
	_run_to(scene, 128.4 * BEAT)
	assert_eq(scene.engine.node_id, "geo_floor", "back to the Floor")
	assert_eq(scene.active_world, "night_one", "the stage swapped back")
	assert_true(scene.stages["night_one"]["stage"] == st, "the Floor's stage was kept, not rebuilt")
	var reached: Array = Session.run_progress.reached_ids()
	assert_true(reached.has("geo_floor") and reached.has("geo_bar"), "both worlds reached: %s" % str(reached))
	_free(s)
