extends TestCase
## The mission maps (defense_02 for missions 2 and 3, village_01 for mission 1; PRD section 15): centred base, entries outside the visible window, sockets inside it,
## wave units walking in unseen, rewarded units leaving the compound; and combat on a sockets battlefield (waves fight
## rewarded defenses, ignore other buildings, and every fight between them resolves).

## Battle areas in px: the viewport is at least 1280 wide (stretch canvas_items, aspect expand, 1280x720 base) and the
## battle takes the top (1 - pad share) of it, pad share 0.30 / 0.36 / 0.42 (Session.PAD_SIZES, default 0.36):
## 16:9 default pads, 16:9 large pads, a wide phone (1600x720) and 4:3 (1280x960).
const AREAS := [Vector2(1280, 461), Vector2(1280, 418), Vector2(1600, 461), Vector2(1280, 614)]
const MIN_OUTSIDE_CELLS := 3.0
const PACKS := ["m01_first_watch", "m02_second_pulse", "m03_hold_the_line"]
const MAPS := {"defense_02": "main", "village_01": "barracks"}  # battlefield -> the role of its first objective


func _rules(bf: String = "defense_02") -> Rules:
	return Rules.load_default("openra_mvp_01", bf)


func _sim(level_rules: Dictionary = {}, bf: String = "defense_02") -> BattleSim:
	var sim := BattleSim.new()
	sim.setup(_rules(bf), level_rules, 1)
	return sim


func _window(area_px: Vector2, bf: Dictionary) -> Rect2:
	return BattleView.window_rect(area_px / float(SpriteBank.RA_CELL_PX), Vector2(float(bf["width"]), float(bf["height"])), bf.get("view", {}))


func _distance_outside(r: Rect2, p: Vector2) -> float:
	return maxf(maxf(r.position.x - p.x, p.x - r.end.x), maxf(r.position.y - p.y, p.y - r.end.y))


func _point(sim: BattleSim, id: String) -> Vector2:
	for dp in sim.defense_points:
		if dp["id"] == id:
			return dp["pos"]
	return Vector2(-1, -1)


## A rewarded building on the first socket of an approach (built on the next tick).
func _defense(sim: BattleSim, reward: String, point: int) -> BattleSim.Ent:
	var r := sim.schedule_reward(reward, sim.tick_count + 1, point)
	assert_eq(int(r["point"]), point)
	sim.tick()
	return sim.get_entity(int(sim.sockets[int(r["socket"])]["ent"]))


func test_map_is_larger_than_the_window_and_the_base_is_centred() -> void:
	for map in MAPS:
		var bf := _rules(map).battlefield
		var sim := _sim({}, map)
		var core: BattleSim.Ent = sim.get_entity(int(sim.objectives[0]["ent"]))
		assert_eq(core.role, MAPS[map], "%s: the first objective" % map)
		for area in AREAS:
			var w := _window(area, bf)
			assert_true(float(bf["width"]) > w.size.x + 2.0 * MIN_OUTSIDE_CELLS and float(bf["height"]) > w.size.y + 2.0 * MIN_OUTSIDE_CELLS, "%s: map larger than the window %s" % [map, str(area)])
			assert_true(core.center().distance_to(w.get_center()) <= 1.0, "%s: the objective is at the centre of the window %s" % [map, str(area)])
			for dp in sim.defense_points:
				assert_true(w.grow(-1.0).has_point(dp["pos"]), "%s: %s is at least a cell inside the window %s" % [map, dp["id"], str(area)])
			assert_true(w.position.x >= 0.0 and w.position.y >= 0.0 and w.end.x <= float(bf["width"]) and w.end.y <= float(bf["height"]))


func test_every_entry_is_outside_the_window_and_none_is_below() -> void:
	for map in MAPS:
		var bf := _rules(map).battlefield
		var ids := []
		for en in bf["entries"]:
			ids.append(str(en["id"]))
			var p := Vector2(float(en["x"]) + 0.5, float(en["y"]) + 0.5)
			for area in AREAS:
				var w := _window(area, bf)
				assert_true(_distance_outside(w, p) >= MIN_OUTSIDE_CELLS, "%s: entry %s is %.1f cells outside the window %s" % [map, en["id"], _distance_outside(w, p), str(area)])
			assert_true(p.y <= float(bf["view"]["center"][1]) + 2.0, "%s: no entry below the base" % map)
		ids.sort()
		assert_eq(ids, ["left", "right", "top"])


func test_every_socket_is_inside_the_window_on_every_screen_and_pad_size() -> void:
	for map in MAPS:
		var bf := _rules(map).battlefield
		assert_eq(bf["sockets"].size(), 15, "%s: five per approach" % map)
		for area in AREAS:
			var w := _window(area, bf)
			for sk in bf["sockets"]:
				var c := Vector2(float(sk["x"]) + 0.5, float(sk["y"]) + 0.5)
				assert_true(w.has_point(c), "%s: socket %s at %s is inside the window %s (%s)" % [map, sk["id"], str(c), str(area), str(w)])


func test_wave_units_spawn_unseen_and_walk_into_the_window_and_on_to_their_point() -> void:
	for map in MAPS:
		var w := _window(AREAS[0], _rules(map).battlefield)
		var objective := "command_core" if map == "defense_02" else "barracks"
		for pair in [["left", "defense_1"], ["top", "defense_2"], ["right", "defense_3"]]:
			for actor in ["e1", "jeep"]:
				var sim := _sim({}, map)
				var u := sim.spawn_wave_unit(actor, pair[0], pair[1], objective)
				assert_true(u != null)
				assert_false(w.has_point(u.center()), "%s: %s spawns outside the window at %s" % [map, actor, pair[0]])
				var point := _point(sim, pair[1])
				var seen := -1
				var at_point := -1
				for t in 25 * 40:
					sim.tick()
					if seen < 0 and w.has_point(u.center()):
						seen = t
					if at_point < 0 and u.center().distance_to(point) <= sim.leash_cells:
						at_point = t
					if seen >= 0 and at_point >= 0:
						break
				assert_true(seen > 25, "%s: %s from %s walks for over a second before it can be seen (tick %d)" % [map, actor, pair[0], seen])
				assert_true(at_point > 0, "%s: %s from %s reaches its defense point" % [map, actor, pair[0]])


func test_rewarded_units_leave_the_compound_to_their_defense_point() -> void:
	var sim := _sim()
	for actor in ["e3", "jeep", "e1", "1tnk", "e3", "jeep"]:
		assert_eq(sim.schedule_reward(actor, 1)["kind"], "unit")
	for t in 25 * 45:
		sim.tick()
	var per := [0, 0, 0]
	assert_eq(sim.groups.size(), 6, "one group per unit reward")
	for gid in sim.groups:
		var g: Dictionary = sim.groups[gid]
		var home: Vector2 = sim.defense_points[g["point"]]["pos"]
		for id in g["units"]:
			per[int(g["point"])] += 1
			assert_true(sim.get_entity(id).center().distance_to(home) < 3.5, "group %d reached defense point %d" % [gid, g["point"]])
	assert_eq(per, [2, 2, 2])


## Each pack names its battlefield (level.json "battlefield"); its waves reference that map's entries, points and objectives.
func test_mission_packs_use_their_own_battlefield_and_all_three_approaches() -> void:
	for pack in PACKS:
		var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + pack))
		var level: Level = loaded["level"]
		var expected := "village_01" if pack == "m01_first_watch" else "defense_02"
		assert_eq(level.battlefield, expected, pack)
		var raw: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(TestCase.project_path("songs/" + pack + "/level.json")))
		assert_eq(str(raw["battlefield"]), level.battlefield, "%s: level.json names the map the loader resolved" % pack)
		var bf := _rules(level.battlefield).battlefield
		var entries := {}
		for en in bf["entries"]:
			entries[str(en["id"])] = true
		var points := {}
		for dp in bf["defense_points"]:
			points[str(dp["id"])] = true
		var objectives := {}
		for o in bf["objectives"]:
			objectives[str(o["id"])] = true
		var used := {}
		var used_points := {}
		for w in level.waves:
			used[str(w["entry"])] = true
			used_points[str(w["via_defense_point"])] = true
			assert_true(entries.has(str(w["entry"])) and points.has(str(w["via_defense_point"])) and objectives.has(str(w["target_objective"])), "%s %s references the map" % [pack, w["id"]])
		assert_eq(used.size(), 3, "%s uses every approach" % pack)
		assert_eq(used_points.size(), points.size(), "%s uses every defense point" % pack)


# --- village_01 (mission 1) -----------------------------------------------------------------------------------------

func test_village_barracks_is_the_only_required_objective_and_sits_inside_the_window() -> void:
	var bf := _rules("village_01").battlefield
	assert_eq(bf["objectives"].size(), 1, "one objective")
	assert_eq([bf["objectives"][0]["id"], bf["objectives"][0]["role"], bf["objectives"][0]["required"]], ["barracks", "barracks", true])
	var sim := _sim({}, "village_01")
	assert_eq(sim.objectives.size(), 1)
	assert_eq(sim.primary_objective_id(), "barracks")
	var barracks: BattleSim.Ent = sim.get_entity(int(sim.objectives[0]["ent"]))
	assert_eq([barracks.role, barracks.alive], ["barracks", true])
	for area in AREAS:
		var w := _window(area, bf)
		assert_true(w.grow(-3.0).has_point(barracks.center()), "the barracks is well inside the window %s" % str(area))
	for e in sim.entities:
		assert_true(e.role != "core" and e.role != "power" and e.role != "dome" and e.role != "factory", "no command core, power plant, radar or factory (%s)" % e.role)


func test_village_houses_and_civilians_are_inside_the_compound() -> void:
	var bf := _rules("village_01").battlefield
	var x0 := 1000.0
	var y0 := 1000.0
	var x1 := -1.0
	var y1 := -1.0
	for b in bf["buildings"]:
		if str(b["role"]) == "brick":
			x0 = minf(x0, float(b["x"]))
			y0 = minf(y0, float(b["y"]))
			x1 = maxf(x1, float(b["x"]))
			y1 = maxf(y1, float(b["y"]))
	var compound := Rect2(x0 + 1.0, y0 + 1.0, x1 - x0 - 1.0, y1 - y0 - 1.0)  # the cells strictly inside the wall rectangle
	var houses := 0
	var actors := {}
	for b in bf["buildings"]:
		if str(b["role"]) != "village":
			continue
		houses += 1
		actors[str(b["actor"])] = true
		var cell := Vector2(float(b["x"]), float(b["y"]))
		assert_true(compound.has_point(cell) and compound.has_point(cell + Vector2(1.0, 1.0)), "house %s at %s is inside the walls %s" % [b["actor"], str(cell), str(compound)])
	assert_eq(houses, 10)
	for a in ["v01", "v02", "v03", "v04", "v05", "v06", "v07", "v08"]:
		assert_true(actors.has(a), "%s is used" % a)
	assert_eq(bf["civilians"].size(), 10)
	var r: Array = bf["wander"]["rect"]
	for c in bf["civilians"]:
		assert_true(compound.has_point(Vector2(float(c["x"]), float(c["y"]))), "civilian %s starts inside the walls" % c["actor"])
	assert_true(compound.has_point(Vector2(float(r[0]), float(r[1]))) and compound.has_point(Vector2(float(r[2]), float(r[3]))), "the wander rectangle is inside the walls")
	var sim := _sim({}, "village_01")
	assert_eq(sim.civilians_alive(), 10, "ten civilians stand in the sim")
	var sim_houses := 0
	for e in sim.entities:
		if e.civilian and e.kind == BattleSim.Kind.BUILDING:
			sim_houses += 1
			assert_true(compound.has_point(e.center()), "house %d centre is inside the walls" % e.id)
	assert_eq(sim_houses, 10)


# --- combat on a sockets battlefield ------------------------------------------------------------------------------

func test_waves_fight_defenses_only_where_the_battlefield_has_sockets() -> void:
	assert_true(_sim().waves_fight_defenses)
	var old := BattleSim.new()
	old.setup(_rules("defense_01"), {}, 1)
	assert_false(old.waves_fight_defenses)


func test_wave_units_ignore_buildings_that_are_neither_defenses_nor_their_objective() -> void:
	var sim := _sim()
	var plant: BattleSim.Ent = null
	for e in sim.entities:
		if e.role == "power":
			plant = e
	var u := sim.spawn_wave_unit("e1", "left", "defense_1", "command_core")
	var spot := Vector2(-1, -1)
	for dx in range(-3, 4):  # a free cell within two cells of the power plant
		for dy in range(-3, 4):
			var c := Vector2i(plant.cx + dx, plant.cy + dy)
			var p := Vector2(c) + Vector2(0.5, 0.5)
			if spot.x < 0.0 and not sim._blocked.has(c) and sim.range_to(u, plant) >= 0.0 and BattleSim.range_to_point(plant, p) <= 2.0:
				spot = p
	assert_true(spot.x >= 0.0, "a free cell next to the power plant")
	u.x = spot.x
	u.y = spot.y
	sim.tick()
	assert_true(sim.range_to(u, plant) <= sim.max_range(u), "the power plant is in range")
	assert_true(sim.scan_for_target(u, sim.max_range(u)) != plant.id, "a wave unit does not pick the power plant")
	u.defenses_only = false
	assert_true(sim.scan_for_target(u, sim.max_range(u)) >= 0, "(without the rule it would shoot a building)")
	u.defenses_only = true
	var hp := plant.hp
	for t in 25 * 6:
		sim.tick()
	assert_eq(plant.hp, hp, "the power plant is never shot")


func test_wave_units_target_and_destroy_a_rewarded_defense_in_their_path() -> void:
	var sim := _sim()
	var pb := _defense(sim, "pillbox", 0)
	assert_true(pb != null and pb.is_defence)
	var attackers: Array = []
	var targeted := false
	for t in 25 * 120:
		if attackers.size() < 3 and t % 20 == 0:
			var u := sim.spawn_wave_unit("1tnk", "left", "defense_1", "command_core")
			if u != null:
				attackers.append(u)
		sim.tick()
		for u in attackers:
			if u.alive and u.target == pb.id:
				targeted = true
		if not pb.alive:
			break
	assert_true(targeted, "the tanks target the pillbox on their way")
	assert_false(pb.alive, "and destroy it")
	assert_eq(sim.defense_count(), 0)
	assert_true(sim.sockets[int(pb.socket)]["ent"] == pb.id and sim._socket_free(int(pb.socket)), "its socket is free again")


## One fight between a rewarded defense and a few wave units: the number of ticks until one side is dead, or -1.
func _duel(defense: String, actor: String, count: int, max_ticks: int) -> Dictionary:
	var sim := _sim()
	var d := _defense(sim, defense, 0)
	var units: Array = []
	var kills_by_defense := 0
	for t in max_ticks:
		if units.size() < count and t % 15 == 0:
			var u := sim.spawn_wave_unit(actor, "left", "defense_1", "command_core")
			if u != null:
				units.append(u)
		sim.tick()
		for ev in sim.drain_events():
			if ev["kind"] == "destroyed" and int(ev["by"]) == d.id:
				kills_by_defense += 1
		var alive := 0
		for u in units:
			if u.alive:
				alive += 1
		if units.size() == count and (alive == 0 or not d.alive):
			return {"ticks": t, "defense_alive": d.alive, "units_alive": alive, "kills": kills_by_defense}
	return {"ticks": -1, "defense_alive": d.alive, "units_alive": -1, "kills": kills_by_defense}


func test_a_pillbox_kills_riflemen_and_the_fight_resolves() -> void:
	var r := _duel("pillbox", "e1", 4, 25 * 120)
	assert_true(int(r["ticks"]) >= 0, "4 riflemen vs a pillbox: one side is dead within 120 s (%s)" % str(r))
	assert_true(int(r["kills"]) >= 1, "the pillbox kills riflemen (%s)" % str(r))


func test_a_light_tank_against_a_pillbox_resolves() -> void:
	var r := _duel("pillbox", "1tnk", 1, 25 * 120)
	assert_true(int(r["ticks"]) >= 0, "1 light tank vs a pillbox: one side is dead within 120 s (%s)" % str(r))
	var t := _duel("turret", "e1", 3, 25 * 120)
	assert_true(int(t["ticks"]) >= 0, "3 riflemen vs a turret resolves too (%s)" % str(t))
