extends TestCase
## The route lock: block 0 of the next phase is charted from the selected route at the last block's decision, so a route with another chart pack can no longer be chosen
## after it (a route with the same pack still can), and a pick made before the lock gets its own scene's cues. It holds between sibling scenes inside a world (the gallery and
## the reactor play different variants of the Lv2 set) exactly as between sibling worlds (the Mothership and the Underworld at the Warehouse's exit).


## The deck offers the gallery (Lv2 Alien Spaceship (1)) or the reactor (Lv2 Alien Spaceship (3)): two charts. The two scenes are plain (audio/chart named) here so the pair
## differs whichever arrangements and per-run seed the shipped music.json has; every other scene is as shipped.
func _data_with_two_charts() -> RunData:
	var music: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RunData.MUSIC_PATH))
	for n in music["nodes"]:
		var pack: String = {"mothership.gallery": "lv2_alien_spaceship_v1", "mothership.reactor": "lv2_alien_spaceship_v3"}.get(str(n["id"]), "")
		if pack != "":
			for k in ["arrangement", "slot", "alternates"]:
				n.erase(k)
			n["audio"] = pack
			n["chart"] = pack
	var path := "user://test_run_lock_music.json"
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(music, "\t"))
	f.close()
	var d := RunData.load_files(RunData.RUN_PATH, path, RunData.PACKS_DIR)
	DirAccess.remove_absolute(path)
	return d


func _play(e: RunEngine, until_t: float, picks: Dictionary) -> void:
	var t := 0.0
	var pressed := {}
	var released := {}
	var done := {}
	while t < until_t and not e.over:
		for at in picks:
			if t >= float(at) and not done.has(at):
				done[at] = true
				e.choose(str(picks[at]))
		e.update(t)
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			if not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]))
			if pressed.has(i) and n["type"] == "hold" and not released.has(i) and float(n["end_time"]) <= t:
				released[i] = true
				e.release(int(n["pad"]), float(n["end_time"]))
		t += 1.0 / 60.0


func _block0(e: RunEngine, phase: int) -> Array:
	var rows: Array = []
	for n in e.level.notes:
		if int(n["phase"]) == phase and int(n["block"]) == 0:
			rows.append([int(n["tick"]) - (phase - 1) * 64 * 960, n["pad"], n["duration_ticks"], n["family"]])
	return rows


func test_a_pick_before_the_lock_gets_its_own_scenes_first_block() -> void:
	var d := _data_with_two_charts()
	assert_true(str(d.nodes["mothership.gallery"]["chart"]) != str(d.nodes["mothership.reactor"]["chart"]))
	var e := RunEngine.new(d)
	e.begin("mothership")
	_play(e, 70.0 * e.beat_s, {55.0 * e.beat_s: "mothership.reactor"})
	assert_eq(e.node_id, "mothership.reactor")
	var ref := RunEngine.new(_data_with_two_charts())
	ref.begin("mothership.reactor")
	_play(ref, 1.0, {})
	var want := _block0(ref, 1)
	assert_true(want.size() > 3)
	assert_eq(_block0(e, 2), want, "the chosen scene's recording is charted, not the default route's")
	var e2 := RunEngine.new(_data_with_two_charts())
	e2.begin("mothership")
	_play(e2, 70.0 * e2.beat_s, {})
	assert_eq(e2.node_id, "mothership.gallery")
	assert_true(_block0(e2, 2) != want, "the default route charts the default scene's pack")


func test_after_the_lock_only_routes_with_the_same_chart_can_be_chosen() -> void:
	var e := RunEngine.new(_data_with_two_charts())
	e.begin("mothership")
	_play(e, 59.0 * e.beat_s, {})
	assert_false(e.route_locked, "free until the last decision")
	assert_true(e.route_allowed("mothership.reactor"))
	_play(e, 61.0 * e.beat_s, {})
	assert_true(e.route_locked)
	assert_false(e.route_allowed("mothership.reactor"), "another chart pack is refused")
	assert_false(e.choose("mothership.reactor"))
	assert_false(e.choose_dir("up"))
	assert_eq(e.selected_route(), "mothership.gallery", "the default stays")
	assert_true(e.choose("mothership.gallery"), "the same pack is still fine")
	# sibling scenes that chart the same pack are never locked out
	var d := _data_with_two_charts()
	d.nodes["mothership.reactor"]["chart"] = d.nodes["mothership.gallery"]["chart"]
	d.nodes["mothership.reactor"]["audio"] = d.nodes["mothership.gallery"]["audio"]
	var same := RunEngine.new(d)
	same.begin("mothership")
	_play(same, 61.0 * same.beat_s, {})
	assert_true(same.route_locked)
	assert_true(same.route_allowed("mothership.reactor"), "the same pack: free after the lock")
	assert_true(same.choose("mothership.reactor"))
	assert_eq(same.selected_route(), "mothership.reactor")


func test_the_lock_holds_between_sibling_worlds_at_the_exit_scene() -> void:
	var e := RunEngine.new(RunData.load_default())
	e.begin("warehouse.exit")
	_play(e, 59.0 * e.beat_s, {})
	assert_false(e.route_locked)
	_play(e, 61.0 * e.beat_s, {})
	assert_true(e.route_locked)
	var same_pack: bool = str(e.data.nodes["underworld"]["chart"]) == str(e.data.nodes[e.default_route()]["chart"])
	assert_eq(e.route_allowed("underworld"), same_pack, "allowed only when the underworld charts the locked pack")
	assert_eq(e.choose("underworld"), same_pack)
	assert_true(e.choose(e.default_route()), "the default route is always fine")


func test_a_single_route_window_has_one_arrow_and_it_is_the_default() -> void:
	var e := RunEngine.new(RunData.load_default())
	e.begin("warehouse.chill")
	var opts := e.options()
	assert_eq(opts.size(), 1)
	assert_true(bool(opts[0]["default"]))
	assert_true(bool(opts[0]["in_world"]), "a path inside the world")
	assert_eq(opts[0]["title"], "The Door", "an in-world route names the room")
	var ex := RunEngine.new(RunData.load_default())
	ex.begin("warehouse.exit")
	for o in ex.options():
		assert_false(bool(o["in_world"]), "an exit scene leads to other worlds")
	assert_eq(ex.options()[0]["title"], "The Mothership", "a world exit names the world")
