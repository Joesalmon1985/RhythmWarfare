extends TestCase
## The run's save (levels reached on entry, migration from the old chapter save, corrupt files), RunData validation and the clock loop.


func _tmp(name: String) -> String:
	return "user://test_run_%s.json" % name


func _rm(path: String) -> void:
	for p in [path, path + ".tmp", path + ".corrupt"]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)


func test_a_level_is_reached_when_it_is_entered() -> void:
	var path := _tmp("reach")
	_rm(path)
	var p := RunProgress.load_data(path, "user://none.json")
	assert_true(p.is_reached("warehouse"), "the first level is always open")
	assert_false(p.is_reached("mothership"))
	assert_true(p.enter("mothership"), "new")
	assert_false(p.enter("mothership"), "not new the second time")
	var again := RunProgress.load_data(path, "user://none.json")
	assert_true(again.is_reached("mothership"), "saved on entry")
	assert_eq(int(again.data["reached"]["mothership"]["entries"]), 2)
	_rm(path)


func test_the_old_chapter_save_is_read_once_and_never_touched() -> void:
	var old := _tmp("old")
	var path := _tmp("new")
	_rm(old)
	_rm(path)
	var f := FileAccess.open(old, FileAccess.WRITE)
	f.store_string(JSON.stringify({"version": 1, "levels": {"night_one": {"plays": 3}, "hospital": {"plays": 1}, "mental_hospital": {"plays": 0}}}))
	f.close()
	var before := FileAccess.get_file_as_string(old)
	var p := RunProgress.load_data(path, old)
	assert_true(p.is_reached("hospital"))
	assert_false(p.is_reached("ward"), "a chapter that was never played is not carried over")
	var mig: Array = p.migrated.duplicate()
	mig.sort()
	assert_eq(mig, ["hospital", "warehouse"])
	assert_true(p.migration_note().contains("carried over"))
	assert_eq(FileAccess.get_file_as_string(old), before, "the old save is untouched")
	var second := RunProgress.load_data(path, old)
	assert_eq(second.migrated, [], "migrated only once: the new save exists now")
	assert_true(second.is_reached("hospital"))
	_rm(old)
	_rm(path)


func test_an_unreadable_save_is_set_aside() -> void:
	var path := _tmp("bad")
	_rm(path)
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string("{ not json")
	f.close()
	var p := RunProgress.load_data(path, "user://none.json")
	assert_true(p.recovered_from_corrupt)
	assert_true(FileAccess.file_exists(path + ".corrupt"))
	assert_true(p.is_reached("warehouse"))
	_rm(path)


func test_the_clock_loop_is_exactly_64_beats() -> void:
	var s := RunAudio.silent_loop(64, 174)
	assert_eq(s.loop_end, 64 * 3000)
	assert_near(s.get_length(), 64.0 * 60.0 / 174.0, 1e-9, "no rounding in the grid the song clock reads")


func _write_json(path: String, v: Variant) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(v))
	f.close()


func _bad_run(mutate: Callable) -> RunData:
	var run: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RunData.RUN_PATH))
	mutate.call(run)
	var rp := "user://test_run_bad_run.json"
	_write_json(rp, run)
	var d := RunData.load_files(rp, RunData.MUSIC_PATH, RunData.PACKS_DIR)
	DirAccess.remove_absolute(rp)
	return d


func _scene(run: Dictionary, id: String) -> Dictionary:
	for n in run["nodes"]:
		if n["id"] == id:
			return n
	return {}


func _has(list: Array, needle: String) -> bool:
	return list.any(func(e: String) -> bool: return e.contains(needle))


func test_run_data_rejects_broken_routes_and_sibling_charts() -> void:
	var good := RunData.load_default()
	assert_eq(good.errors, [])
	assert_eq(good.warnings.filter(func(w: String) -> bool: return w.contains("cannot be reached")), [], "every scene is reachable")
	var d := _bad_run(func(run: Dictionary) -> void: (_scene(run, "mothership.exit")["next"] as Array).resize(1))  # a world exit keeps one route (its second world and its way back to the hub gone)
	assert_true(_has(d.errors, "at least 2 routes"), str(d.errors))
	# the siblings of the Warehouse floor: plain scenes (audio/chart named) so the charts are the test's own, whatever the shipped arrangements play
	var mp := "user://test_run_bad_music.json"
	var lock_warned: Array = []
	for pair in [["lv1_warehouse_v1", "lv1_warehouse_v1"], ["lv1_warehouse_v1", "lv1_warehouse_v2"]]:
		var bad_music: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(RunData.MUSIC_PATH))
		for n in bad_music["nodes"]:
			var want: String = {"warehouse.bar": pair[0], "warehouse.balcony": pair[1]}.get(str(n["id"]), "")
			if want != "":
				for k in ["arrangement", "slot", "alternates"]:
					n.erase(k)
				n["audio"] = want
				n["chart"] = want
		_write_json(mp, bad_music)
		var d2 := RunData.load_files(RunData.RUN_PATH, mp, RunData.PACKS_DIR)
		assert_eq(d2.errors, [])
		lock_warned.append(d2.warnings.any(func(e: String) -> bool: return e.begins_with("scene warehouse:") and e.contains("route lock")))
	assert_eq(lock_warned, [false, true], "the bar's sibling charting the bar's pack: no route lock between them; a different pack: flagged")
	assert_true(good.warnings.any(func(e: String) -> bool: return e.begins_with("scene warehouse.exit:") and e.contains("route lock")), "the world exits chart different packs: the route lock applies")
	DirAccess.remove_absolute(mp)


func test_run_data_validates_the_world_graphs() -> void:
	var d := _bad_run(func(run: Dictionary) -> void: _scene(run, "warehouse.booth")["entry"] = true)
	assert_true(_has(d.errors, "exactly one entry scene"), str(d.errors))
	d = _bad_run(func(run: Dictionary) -> void: _scene(run, "warehouse.exit")["exit_scene"] = false)
	assert_true(_has(d.errors, "exactly one exit scene"), str(d.errors))
	d = _bad_run(func(run: Dictionary) -> void: (_scene(run, "hospital.garden")["next"] as Array)[0]["to"] = "hospital.corridor")  # a cycle without a loop mark
	assert_true(_has(d.errors, "a cycle"), str(d.errors))
	d = _bad_run(func(run: Dictionary) -> void: (_scene(run, "hospital.garden")["next"] as Array)[0]["to"] = "hospital")  # back to the entry without the mark
	assert_true(_has(d.errors, "must be marked"), str(d.errors))
	d = _bad_run(func(run: Dictionary) -> void:
		var n := _scene(run, "hospital_late.exit")
		(n["next"] as Array)[0].erase("loop"))  # the late exit loops to its own world: only with the mark
	assert_true(_has(d.errors, "loop"), str(d.errors))
	d = _bad_run(func(run: Dictionary) -> void: (_scene(run, "warehouse.chill")["next"] as Array)[0]["to"] = "mothership")  # a middle scene leaving the world
	assert_true(_has(d.errors, "only the exit scene may"), str(d.errors))
	d = _bad_run(func(run: Dictionary) -> void: (_scene(run, "warehouse.exit")["next"] as Array)[0]["to"] = "hospital")  # a world exit skipping a depth
	assert_true(_has(d.errors, "one level deeper"), str(d.errors))
	d = _bad_run(func(run: Dictionary) -> void: (_scene(run, "warehouse.bar")["place"]["rail"]["good"] as Array)[0]["to"] = "nowhere_at_all")
	assert_true(_has(d.errors, "nowhere_at_all"), str(d.errors))
	d = _bad_run(func(run: Dictionary) -> void: (_scene(run, "warehouse.bar")["place"]["rail"]["exits"] as Dictionary).erase("right"))  # a route without a doorway
	assert_true(_has(d.errors, "no exit doorway"), str(d.errors))
	d = _bad_run(func(run: Dictionary) -> void: _scene(run, "warehouse.bar")["world"] = "nonexistent")
	assert_true(_has(d.errors, "not in run.json worlds"), str(d.errors))


func test_the_route_map_covers_seven_worlds_on_five_maps() -> void:
	var d := RunData.load_default()
	assert_eq(d.world_order.size(), 7)
	var maps := {}
	for id in d.nodes:
		maps[d.nodes[id]["map"]] = true
	assert_eq(maps.keys().size(), 5)
	for m in ["night_one", "mothership", "underworld", "hospital", "mental_hospital"]:
		assert_true(maps.has(m), m)
	for w in d.world_order:
		var scenes := d.scenes_of(str(w))
		assert_true(scenes.size() >= 3, "%s has %d scenes" % [w, scenes.size()])
		assert_eq(d.entry_of(str(w)), str(w), "the entry scene's id is the world's id: the save's reached ids")
	for id in d.nodes:
		var n: Dictionary = d.nodes[id]
		assert_true((n["next"] as Array).size() >= (2 if bool(n["exit_scene"]) else 1), "%s offers arrows" % id)
		assert_eq(int(n["depth"]), int(d.worlds[str(n["world"])]["depth"]), "depth stays per world")
	assert_eq(d.nodes["hospital_late.exit"]["next"][0]["to"], "hospital_late", "the last depth loops onward")
	assert_true(bool(d.nodes["hospital_late.exit"]["next"][0]["loop"]))
	assert_true(bool(d.nodes["ward_late.exit"]["next"][0]["loop"]))


## The routes between hubs (the shared wiring step; RunData._validate_hub_route): a hub's link to its partner and every scene's way back to its hub load clean; a link to a hub of
## another depth, a way back without its loop mark, a way back from one world into a later one and a hub route as the default are refused.
func test_run_data_accepts_the_hub_routes_and_refuses_bad_ones() -> void:
	var good := RunData.load_default()
	assert_eq(good.errors, [])
	var links := 0
	var backs := 0
	for id in good.nodes:
		for e in good.nodes[id]["next"]:
			links += 1 if bool(e.get("hub_link", false)) else 0
			backs += 1 if bool(e.get("to_hub", false)) else 0
	assert_eq(links, 4, "four hub links: Mothership and Underworld, Hospital and Ward, both ways")
	assert_eq(backs, 31, "a way back to the hub from every main-run scene that is not a hub")
	var d := _bad_run(func(run: Dictionary) -> void:
		for e in _scene(run, "mothership")["next"]:
			if bool(e.get("hub_link", false)):
				e["to"] = "hospital")
	assert_true(_has(d.errors, "partner hubs are at the same depth"), str(d.errors))
	d = _bad_run(func(run: Dictionary) -> void:
		for e in _scene(run, "warehouse.bar")["next"]:
			if bool(e.get("to_hub", false)):
				e.erase("loop"))
	assert_true(_has(d.errors, "must be marked \"loop\""), str(d.errors))
	d = _bad_run(func(run: Dictionary) -> void:
		for e in _scene(run, "hospital.garden")["next"]:
			if bool(e.get("to_hub", false)):
				e["to"] = "hospital_late"
				e.erase("loop"))
	assert_true(_has(d.errors, "leaves for another world"), str(d.errors))
	d = _bad_run(func(run: Dictionary) -> void: (_scene(run, "warehouse.bar")["next"] as Array).reverse())
	assert_true(_has(d.errors, "cannot be the scene's first (default) route"), str(d.errors))
