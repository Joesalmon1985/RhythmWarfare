extends TestCase
## The mission map (defense_02, PRD section 15): centred base, entries outside the visible window, sockets inside it,
## wave units walking in unseen, rewarded units leaving the compound; and combat on a sockets battlefield (waves fight
## rewarded defenses, ignore other buildings, and every fight between them resolves).

## Battle areas in px: the viewport is at least 1280 wide (stretch canvas_items, aspect expand, 1280x720 base) and the
## battle takes the top (1 - pad share) of it, pad share 0.30 / 0.36 / 0.42 (Session.PAD_SIZES, default 0.36):
## 16:9 default pads, 16:9 large pads, a wide phone (1600x720) and 4:3 (1280x960).
const AREAS := [Vector2(1280, 461), Vector2(1280, 418), Vector2(1600, 461), Vector2(1280, 614)]
const MIN_OUTSIDE_CELLS := 3.0
const PACKS := ["m01_first_watch", "m02_second_pulse", "m03_hold_the_line"]


func _rules(bf: String = "defense_02") -> Rules:
	return Rules.load_default("openra_mvp_01", bf)


func _sim(level_rules: Dictionary = {}) -> BattleSim:
	var sim := BattleSim.new()
	sim.setup(_rules(), level_rules, 1)
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
	var bf := _rules().battlefield
	var sim := _sim()
	var core: BattleSim.Ent = sim.get_entity(int(sim.objectives[0]["ent"]))
	for area in AREAS:
		var w := _window(area, bf)
		assert_true(float(bf["width"]) > w.size.x + 2.0 * MIN_OUTSIDE_CELLS and float(bf["height"]) > w.size.y + 2.0 * MIN_OUTSIDE_CELLS, "map larger than the window %s" % str(area))
		assert_true(core.center().distance_to(w.get_center()) <= 1.0, "the core is at the centre of the window %s" % str(area))
		for dp in sim.defense_points:
			assert_true(w.grow(-1.0).has_point(dp["pos"]), "%s is at least a cell inside the window %s" % [dp["id"], str(area)])
		assert_true(w.position.x >= 0.0 and w.position.y >= 0.0 and w.end.x <= float(bf["width"]) and w.end.y <= float(bf["height"]))


func test_every_entry_is_outside_the_window_and_none_is_below() -> void:
	var bf := _rules().battlefield
	var ids := []
	for en in bf["entries"]:
		ids.append(str(en["id"]))
		var p := Vector2(float(en["x"]) + 0.5, float(en["y"]) + 0.5)
		for area in AREAS:
			var w := _window(area, bf)
			assert_true(_distance_outside(w, p) >= MIN_OUTSIDE_CELLS, "entry %s is %.1f cells outside the window %s" % [en["id"], _distance_outside(w, p), str(area)])
		assert_true(p.y <= float(bf["view"]["center"][1]) + 2.0, "no entry below the base")
	ids.sort()
	assert_eq(ids, ["left", "right", "top"])


func test_every_socket_is_inside_the_window_on_every_screen_and_pad_size() -> void:
	var bf := _rules().battlefield
	assert_eq(bf["sockets"].size(), 15, "five per approach")
	for area in AREAS:
		var w := _window(area, bf)
		for sk in bf["sockets"]:
			var c := Vector2(float(sk["x"]) + 0.5, float(sk["y"]) + 0.5)
			assert_true(w.has_point(c), "socket %s at %s is inside the window %s (%s)" % [sk["id"], str(c), str(area), str(w)])


func test_wave_units_spawn_unseen_and_walk_into_the_window_and_on_to_their_point() -> void:
	var w := _window(AREAS[0], _rules().battlefield)
	for pair in [["left", "defense_1"], ["top", "defense_2"], ["right", "defense_3"]]:
		for actor in ["e1", "jeep"]:
			var sim := _sim()
			var u := sim.spawn_wave_unit(actor, pair[0], pair[1], "command_core")
			assert_true(u != null)
			assert_false(w.has_point(u.center()), "%s spawns outside the window at %s" % [actor, pair[0]])
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
			assert_true(seen > 25, "%s from %s walks for over a second before it can be seen (tick %d)" % [actor, pair[0], seen])
			assert_true(at_point > 0, "%s from %s reaches its defense point" % [actor, pair[0]])


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


func test_mission_packs_use_defense_02_and_all_three_approaches() -> void:
	var bf := _rules().battlefield
	var entries := {}
	for en in bf["entries"]:
		entries[str(en["id"])] = true
	var points := {}
	for dp in bf["defense_points"]:
		points[str(dp["id"])] = true
	var objectives := {}
	for o in bf["objectives"]:
		objectives[str(o["id"])] = true
	for pack in PACKS:
		var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + pack))
		var level: Level = loaded["level"]
		assert_eq(level.battlefield, "defense_02", pack)
		var used := {}
		for w in level.waves:
			used[str(w["entry"])] = true
			assert_true(entries.has(str(w["entry"])) and points.has(str(w["via_defense_point"])) and objectives.has(str(w["target_objective"])), "%s %s references the map" % [pack, w["id"]])
		assert_eq(used.size(), 3, "%s uses every approach" % pack)


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
