extends TestCase
## The centred-base layout: the map is larger than the window the player sees, the base sits in the middle of it,
## every entry lies outside it so wave units walk on, and the wave schedule still fits the song.

const AREAS := [Vector2(1280, 480), Vector2(1707, 480), Vector2(960, 640)]  # 16:9, 21:9 and 4:3 (the battle area is never shorter than 480 px)
const MIN_OUTSIDE_CELLS := 3.0


func _rules() -> Rules:
	return Rules.load_default("openra_mvp_01", "defense_01")


func _window(area_px: Vector2, bf: Dictionary) -> Rect2:
	return BattleView.window_rect(area_px / float(SpriteBank.RA_CELL_PX), Vector2(float(bf["width"]), float(bf["height"])), bf.get("view", {}))


func _distance_outside(r: Rect2, p: Vector2) -> float:
	return maxf(maxf(r.position.x - p.x, p.x - r.end.x), maxf(r.position.y - p.y, p.y - r.end.y))


func test_map_is_larger_than_the_window_and_the_base_is_centred() -> void:
	var bf := _rules().battlefield
	for area in AREAS:
		var w := _window(area, bf)
		assert_true(float(bf["width"]) > w.size.x + 2.0 * MIN_OUTSIDE_CELLS and float(bf["height"]) > w.size.y + 2.0 * MIN_OUTSIDE_CELLS, "map larger than the window %s" % str(area))
		var sim := BattleSim.new()
		sim.setup(_rules(), {}, 1)
		var core: BattleSim.Ent = sim.get_entity(int(sim.objectives[0]["ent"]))
		assert_true(core.center().distance_to(w.get_center()) <= 1.0, "the core is at the centre of the window %s" % str(area))
		for dp in sim.defense_points:
			assert_true(w.has_point(dp["pos"]) and w.grow(-2.0).has_point(dp["pos"]), "%s is well inside the window" % dp["id"])
		assert_true(w.position.x >= 0.0 and w.position.y >= 0.0 and w.end.x <= float(bf["width"]) and w.end.y <= float(bf["height"]))


func test_every_entry_is_outside_the_window_and_none_is_below() -> void:
	var rules := _rules()
	var bf := rules.battlefield
	var ids := []
	for en in bf["entries"]:
		ids.append(str(en["id"]))
		var p := Vector2(float(en["x"]) + 0.5, float(en["y"]) + 0.5)
		for area in AREAS:
			var w := _window(area, bf)
			assert_false(w.has_point(p), "entry %s is not visible" % en["id"])
			assert_true(_distance_outside(w, p) >= MIN_OUTSIDE_CELLS, "entry %s is %.1f cells outside the window %s" % [en["id"], _distance_outside(w, p), str(area)])
		assert_true(p.y <= float(bf["view"]["center"][1]) + 2.0, "no entry below the base (the lane is there)")
	ids.sort()
	assert_eq(ids, ["left", "right", "top"])


func test_wave_units_spawn_unseen_and_walk_into_the_window_and_on_to_their_point() -> void:
	var rules := _rules()
	var w := _window(AREAS[0], rules.battlefield)
	for pair in [["left", "defense_1"], ["top", "defense_2"], ["right", "defense_3"]]:
		for actor in ["e1", "jeep"]:
			var sim := BattleSim.new()
			sim.setup(_rules(), {}, 1)
			var u := sim.spawn_wave_unit(actor, pair[0], pair[1], "command_core")
			assert_true(u != null)
			assert_false(w.has_point(u.center()), "%s spawns outside the window at %s" % [actor, pair[0]])
			var seen := -1
			var at_point := -1
			var point: Vector2 = Vector2.ZERO
			for dp in sim.defense_points:
				if dp["id"] == pair[1]:
					point = dp["pos"]
			for t in 25 * 40:
				sim.tick()
				if seen < 0 and w.has_point(u.center()):
					seen = t
				if at_point < 0 and u.center().distance_to(point) <= BattleSim.new().leash_cells:
					at_point = t
				if seen >= 0 and at_point >= 0:
					break
			assert_true(seen > 25, "%s from %s walks for over a second before it can be seen (tick %d)" % [actor, pair[0], seen])
			assert_true(at_point > 0, "%s from %s reaches its defense point" % [actor, pair[0]])
			assert_true(u.alive)


func test_production_leaves_the_compound_to_every_defense_point() -> void:
	var sim := BattleSim.new()
	sim.setup(_rules(), {}, 1)
	for i in 6:
		assert_eq(sim.produce_group(0, [{"actor": "e1", "count": 2}, {"actor": "jeep", "count": 1}], i + 1, i)["result"], "queued")
	for t in 25 * 45:
		sim.tick()
	for gid in sim.groups:
		var g: Dictionary = sim.groups[gid]
		assert_eq(g["units"].size(), 3)
		var home: Vector2 = sim.defense_points[g["point"]]["pos"]
		for id in g["units"]:
			assert_true(sim.get_entity(id).center().distance_to(home) < 3.5, "group %d reached defense point %d" % [gid, g["point"]])


func test_waves_make_first_contact_after_the_opening_bars_and_the_last_arrives_before_the_end() -> void:
	var rules := _rules()
	var entries := {}
	for en in rules.battlefield["entries"]:
		entries[str(en["id"])] = Vector2(float(en["x"]) + 0.5, float(en["y"]) + 0.5)
	var points := {}
	for dp in rules.battlefield["defense_points"]:
		points[str(dp["id"])] = Vector2(float(dp["x"]) + 0.5, float(dp["y"]) + 0.5)
	for pack in ["first_watch", "second_pulse", "hold_the_line"]:
		var level: Level = LevelLoader.load_pack(TestCase.project_path("songs/" + pack))["level"]
		var tps: float = level.bpm * float(level.ticks_per_beat) / 60.0
		var opening_s: float = 4.0 * float(level.ticks_per_bar()) / tps
		var duration_s: float = float(level.duration_ticks) / tps
		var first := INF
		var last := 0.0
		var entries_used := {}
		for w in level.waves:
			entries_used[str(w["entry"])] = true
			var d: float = entries[w["entry"]].distance_to(points[w["via_defense_point"]])
			for g in w["groups"]:
				var cps := float(rules.actors[g["actor"]]["speed"]) / 1024.0 * 25.0
				first = minf(first, float(w["start_tick"]) / tps + d / cps)
				last = maxf(last, (float(w["start_tick"]) + float(g["count"] - 1) * float(g["spawn_spacing_ticks"])) / tps + d / cps)
		assert_true(first > opening_s, "%s: first contact at %.1f s is after the opening bars (%.1f s)" % [pack, first, opening_s])
		assert_true(last < duration_s, "%s: the last unit reaches its point at %.1f s, before the song ends (%.1f s)" % [pack, last, duration_s])
		assert_true(entries_used.size() == 3, "%s uses all three approaches" % pack)
