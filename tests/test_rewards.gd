extends TestCase
## Mission rewards in BattleSim (PRD section 15): one reward per passed sequence after its grade delay, valid socket
## placement, the fewest-defenses approach first, capacity (repair, then reinforce once), unit rewards per point and
## the dead-producer fallback; a failed sequence schedules nothing.

const AREA_16_9 := Vector2(1280, 461)  # 16:9, default pads; every screen is checked socket by socket in test_mission_layout.gd


func _sim(per_point: int = 5, seed_value: int = 1) -> BattleSim:
	var sim := BattleSim.new()
	sim.setup(Rules.load_default("openra_mvp_01", "defense_02"), {"sockets_per_point": per_point}, seed_value)
	return sim


## Ticks the sim n times and returns the reward_done events it produced.
func _tick(sim: BattleSim, n: int) -> Array:
	var out: Array = []
	for i in n:
		sim.tick()
		for ev in sim.drain_events():
			if ev["kind"] == "reward_done":
				out.append(ev)
	return out


func _socket_ent(sim: BattleSim, i: int) -> BattleSim.Ent:
	return sim.get_entity(int(sim.sockets[i]["ent"]))


## m01 with the cues of sequence 0 pressed at `offset` (s) and nothing else, frame by frame at 60 fps up to `until`.
func _m01_seq0(offset: float) -> Match:
	var level: Level = LevelLoader.load_pack(TestCase.project_path("songs/m01_first_watch"))["level"]
	var m := Match.new()
	m.setup(level)
	var cues: Array = []
	for n in level.notes:
		if int(n["seq"]) == 0:
			cues.append(n)
	var t := 0.0
	var k := 0
	while m.reward_log.is_empty() and t < 10.0:
		t += 1.0 / 60.0
		while k < cues.size() and float(cues[k]["time"]) + offset <= t:
			var at := float(cues[k]["time"]) + offset
			m.press(int(cues[k]["pad"]), at, 1)
			m.release(int(cues[k]["pad"]), at + 0.05, 1)
			k += 1
		m.advance(t)
	return m


func _pillboxes(sim: BattleSim) -> int:
	var n := 0
	for e in sim.entities:
		if e.alive and e.side == 0 and e.role == "pillbox":
			n += 1
	return n


func test_first_passed_drum_sequence_of_m01_builds_one_pillbox_after_the_grade_delay() -> void:
	for c in [[0.0, "sharp", 0.5], [0.1, "loose", 3.0]]:
		var m := _m01_seq0(float(c[0]))
		assert_eq(m.reward_log.size(), 1, "only sequence 0 has resolved")
		var e: Dictionary = m.reward_log[0]
		assert_eq([e["sequence"], e["reward"], e["passed"], e["grade"], e["result"], e["kind"]], [0, "pillbox", true, c[1], "scheduled", "build"])
		var ready := float(e["ready_time"])
		assert_near(ready - float(e["resolve_time"]), float(c[2]), 1e-9, "%s delay" % c[1])
		assert_eq(m.sim.pending_rewards.size(), 1)
		var sk := int(m.sim.pending_rewards[0]["socket"])
		assert_true(sk >= 0 and m.sim.sockets[sk]["reserved"], "the socket is chosen and reserved at resolve time")
		assert_eq(int(m.sim.sockets[sk]["point"]), int(e["point"]))
		m.advance(ready - 0.06)
		assert_eq(m.sim.defense_count(), 0, "nothing stands before the delay ends (%s)" % c[1])
		assert_eq(_pillboxes(m.sim), 0)
		m.advance(ready + 0.06)
		assert_eq(m.sim.defense_count(), 1, "the pillbox stands once the delay ends (%s)" % c[1])
		assert_eq(_pillboxes(m.sim), 1, "exactly one")
		var pb := _socket_ent(m.sim, sk)
		assert_true(pb != null and pb.role == "pillbox" and pb.side == 0)
		assert_eq([pb.cx, pb.cy], [int(m.sim.sockets[sk]["x"]), int(m.sim.sockets[sk]["y"])], "on its socket")


func test_failed_sequence_schedules_nothing() -> void:
	var m := _m01_seq0(0.3)  # every press a stray: sequence 0 fails
	assert_eq(m.reward_log.size(), 1)
	assert_eq(m.reward_log[0]["result"], "failed")
	assert_false(m.reward_log[0].has("ready_time"))
	assert_eq(m.sim.pending_rewards, [])
	m.advance(12.0)
	for ev in m.drain_events():
		assert_true(ev["kind"] != "reward_scheduled" and ev["kind"] != "reward_done", "no reward event at all")
	assert_eq(m.sim.defense_count(), 0)
	assert_eq(m.sim.count_alive(0, BattleSim.Kind.UNIT), 0)


func test_placements_are_on_sockets_off_the_routes_and_inside_the_window() -> void:
	var sim := _sim(5)
	var bf: Dictionary = sim.rules.battlefield
	var route := {}
	for pair in [["left", 0], ["top", 1], ["right", 2]]:
		var from := Vector2i(sim.entries[pair[0]].floor())
		var to := Vector2i(sim.defense_points[pair[1]]["pos"].floor())
		for g in [sim._astar_foot, sim._astar_track]:
			var path: Array[Vector2i] = g.get_id_path(from, to)
			assert_true(path.size() > 5, "a route from %s" % pair[0])
			for c in path:
				route[c] = true
	for i in 15:
		assert_eq(sim.schedule_reward("pillbox", 1)["kind"], "build")
	_tick(sim, 2)
	assert_eq(sim.defense_count(), 15)
	var cells := {}
	var ids := {}
	for i in sim.sockets.size():
		var sk: Dictionary = sim.sockets[i]
		var e := _socket_ent(sim, i)
		assert_true(e != null and e.alive and e.socket == i, "socket %s holds its building" % sk["id"])
		var src: Dictionary = bf["sockets"][i]
		assert_eq([e.cx, e.cy, sk["id"]], [int(src["x"]), int(src["y"]), str(src["id"])], "a defense_02 socket")
		var c := Vector2i(e.cx, e.cy)
		assert_false(route.has(c), "%s is not on a route cell" % sk["id"])
		assert_false(cells.has(c) or ids.has(e.id), "one building per socket")
		cells[c] = true
		ids[e.id] = true
		var w := BattleView.window_rect(AREA_16_9 / float(SpriteBank.RA_CELL_PX), Vector2(float(bf["width"]), float(bf["height"])), bf.get("view", {}))
		assert_true(w.has_point(e.center()), "%s inside the 16:9 window" % sk["id"])
	for pt in 3:
		assert_eq(sim.defenses_at(pt), 5)
	var extra := sim.schedule_reward("pillbox", sim.tick_count + 1)
	assert_true(extra["capacity"], "the sixteenth building is a capacity reward")
	assert_eq(extra["kind"], "repair")
	# a mission that opens two sockets per approach
	var small := _sim(2)
	assert_eq(small.sockets.size(), 6)
	var built := 0
	for i in 9:
		var r := small.schedule_reward("turret", 1)
		if r["kind"] == "build":
			built += 1
			assert_true(int(small.sockets[int(r["socket"])]["order"]) < 2, "only the opened sockets")
	assert_eq(built, 6)
	_tick(small, 2)
	for pt in 3:
		assert_eq(small.defenses_at(pt), 2, "never more than sockets_per_point at approach %d" % pt)


func test_fewest_defenses_approach_first_ties_go_to_the_next_wave() -> void:
	var sim := _sim(5)
	var points := []
	for hint in [2, 2, 2, 1, -1, 0]:
		points.append(int(sim.schedule_reward("pillbox", 5, hint)["point"]))
	assert_eq(points, [2, 0, 1, 1, 0, 2], "fewest first; ties go to the hint, then the lowest index")
	_tick(sim, 6)
	sim._damage(_socket_ent(sim, 0), 999999, null)  # approach 0 loses one
	_tick(sim, 1)
	assert_eq(int(sim.schedule_reward("pillbox", sim.tick_count + 1, 2)["point"]), 0, "the weakened approach is refilled first")


func test_at_capacity_a_build_repairs_its_approach_then_reinforces_the_oldest_once() -> void:
	var sim := _sim(1)
	for i in 3:
		sim.schedule_reward("pillbox", 1)
	_tick(sim, 2)
	var b0 := _socket_ent(sim, 0)
	var b1 := _socket_ent(sim, 1)
	var b2 := _socket_ent(sim, 2)
	var full := b0.max_hp
	b1.hp = b1.max_hp / 2
	b2.hp = b2.max_hp - 100
	var r := sim.schedule_reward("pillbox", sim.tick_count + 2, 0)
	assert_true(r["capacity"])
	assert_eq([r["kind"], r["point"], r["label"]], ["repair", 1, "Repair crew"], "the most damaged approach")
	var done := _tick(sim, 3)
	assert_eq(done.size(), 1)
	assert_eq([done[0]["result"], done[0]["point"]], ["repaired", 1])
	assert_eq(b1.hp, b1.max_hp, "healed to full")
	assert_eq(b2.hp, b2.max_hp - 100, "another approach is not touched")
	sim.schedule_reward("turret", sim.tick_count + 1, 0)
	assert_eq(_tick(sim, 2)[0]["point"], 2)
	assert_eq(b2.hp, b2.max_hp)
	# nothing damaged: reinforce the oldest defense, once each
	sim.schedule_reward("pillbox", sim.tick_count + 1, 1)
	done = _tick(sim, 2)
	assert_eq(done[0]["result"], "reinforced")
	assert_true(b0.reinforced)
	assert_eq(b0.max_hp, int(round(full * 1.5)), "+50 % health")
	assert_eq(b0.hp, b0.max_hp)
	sim.schedule_reward("pillbox", sim.tick_count + 1, 1)
	_tick(sim, 2)
	assert_eq(b0.max_hp, int(round(full * 1.5)), "never twice")
	assert_true(b1.reinforced, "the next oldest")
	assert_eq(sim.defense_count(), 3)


func test_unit_rewards_hold_points_and_at_six_everywhere_become_repairs() -> void:
	var sim := _sim(5)
	assert_eq(sim.units_per_point, 6)
	var per := [0, 0, 0]
	for i in 18:
		var r := sim.schedule_reward("e3", 1 + i)
		assert_eq(r["kind"], "unit")
		per[int(r["point"])] += 1
	assert_eq(per, [6, 6, 6], "the point with the fewest defenders each time")
	var over := sim.schedule_reward("e1", 30, 1)
	assert_true(over["capacity"])
	assert_eq(over["kind"], "repair")
	_tick(sim, 25 * 20)
	var e3 := 0
	for e in sim.entities:
		if e.alive and e.side == 0 and e.kind == BattleSim.Kind.UNIT:
			assert_eq(e.actor, "e3")
			e3 += 1
	assert_eq(e3, 18, "every unit reward produced one unit, the capacity one none")
	for pt in 3:
		assert_eq(sim.units_at(pt), 6)


func test_unit_reward_with_a_dead_producer_becomes_a_repair() -> void:
	var sim := _sim(5)
	sim.schedule_reward("pillbox", 1)
	_tick(sim, 2)
	var pb: BattleSim.Ent = null
	for i in sim.sockets.size():
		if _socket_ent(sim, i) != null:
			pb = _socket_ent(sim, i)
	pb.hp = pb.max_hp / 3
	var barracks: BattleSim.Ent = sim.get_entity(sim.producer_ids[0]["barracks"])
	sim._damage(barracks, barracks.max_hp + 1, null)
	assert_false(barracks.alive)
	var r := sim.schedule_reward("e3", sim.tick_count + 2)
	assert_eq(r["kind"], "unit")
	var done := _tick(sim, 3)
	assert_eq(done.size(), 1)
	assert_eq(done[0]["result"], "repaired", "no barracks: the reward repairs instead of vanishing")
	assert_eq(pb.hp, pb.max_hp)
	_tick(sim, 50)
	assert_eq(sim.count_alive(0, BattleSim.Kind.UNIT), 0, "and no unit appears")
	assert_eq(sim.stats["produced"][0]["infantry"], 0)
