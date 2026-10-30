extends TestCase
## The defense battle: outcome rules, waves without producers, groups and the defense-point cycle, recipes
## resolved through the slot (never the button), producer gating and determinism.


func _level(pack: String, chart := "") -> Level:
	var loaded := LevelLoader.load_pack(TestCase.project_path("songs/" + pack), {"chart_id": chart})
	assert_eq(loaded["errors"], [])
	return loaded["level"]


func _match(level: Level) -> Match:
	var m := Match.new()
	m.setup(level, null, true)
	return m


func _rules() -> Rules:
	return Rules.load_default("openra_mvp_01", "defense_01")


func _core(sim: BattleSim) -> BattleSim.Ent:
	return sim.get_entity(int(sim.objectives[0]["ent"]))


## Press every note of a level in time order (each hit exact), optionally skipping some slots.
func _play(m: Match, level: Level, until: float = INF, skip_slots: Array = []) -> void:
	for n in level.notes:
		if n["time"] > until:
			break
		m.advance(n["time"])
		if skip_slots.has(n["slot_id"]):
			continue
		m.press(int(n["button"]), n["time"], 1)
		if n["type"] == "hold":
			m.advance(n["end_time"] - 0.02)
			m.release(int(n["button"]), n["end_time"] - 0.01, 1)
	m.advance(minf(until, level.duration_seconds()))


func test_there_is_no_enemy_base_and_no_instant_victory() -> void:
	var sim := BattleSim.new()
	sim.setup(_rules(), {}, 1)
	assert_true(sim.defense)
	assert_eq(sim.outcome, "", "an empty enemy side is not a win")
	assert_true(sim.main_base(1) == null)
	assert_false(sim.producer_alive(1, "barracks"))
	assert_eq(sim.objectives.size(), 1)
	assert_eq(sim.objectives[0]["id"], "command_core")
	assert_eq(sim.defense_points.size(), 3)
	for i in 100:
		sim.tick()
	assert_eq(sim.outcome, "")
	for e in sim.entities:
		assert_eq(e.side, 0, "only the player's buildings exist")


func test_survival_wins_with_enemies_alive_and_loss_is_immediate() -> void:
	var sim := BattleSim.new()
	sim.setup(_rules(), {}, 1)
	var u := sim.spawn_wave_unit("e1", "top", "defense_2", "command_core")
	assert_true(u != null)
	for i in 50:
		sim.tick()
	assert_true(u.alive)
	sim.end_by_song()
	assert_eq(sim.outcome, "victory")
	assert_eq(sim.outcome_reason, "survived")
	# a destroyed core is a defeat at the next tick, whatever else is going on
	var sim2 := BattleSim.new()
	sim2.setup(_rules(), {}, 1)
	var core := _core(sim2)
	sim2._damage(core, core.max_hp + 1, null)
	assert_eq(sim2.outcome, "")
	sim2.tick()
	assert_eq(sim2.outcome, "defeat")
	assert_eq(sim2.outcome_reason, "objective_destroyed:command_core")
	var again: BattleSim = sim2
	again.end_by_song()
	assert_eq(again.outcome, "defeat", "the survival win never overwrites a loss")


func test_same_tick_tie_resolves_as_a_defeat() -> void:
	var level := _level("first_watch")
	var m := _match(level)
	_play(m, level, level.duration_seconds() - 1.0)  # perfect play holds the base
	assert_eq(m.outcome, "")
	var core := _core(m.sim)
	m.sim._damage(core, core.max_hp + 1, null)  # destroyed in the last second, before the deadline tick resolves
	m.advance(level.duration_seconds() + 0.5)
	assert_eq(m.outcome, "defeat")
	assert_eq(m.outcome_reason, "objective_destroyed:command_core")
	# and survival resolves exactly at duration_ticks, not later
	var m2 := _match(level)
	_play(m2, level, level.duration_seconds() - 0.001)
	assert_eq(m2.outcome, "")
	m2.advance(level.duration_seconds() + 0.5)
	assert_eq(m2.outcome, "victory")
	assert_eq(m2.sim_ticks, int(floor(level.duration_seconds() / BattleSim.TICK_S)), "nothing is simulated past the deadline tick")


func test_waves_spawn_without_producers_by_time_regardless_of_input() -> void:
	var level := _level("first_watch")
	var m := _match(level)
	var w1: Dictionary = level.waves[0]
	var start := level.tick_to_seconds(int(w1["start_tick"]))
	m.advance(start - 0.1)
	assert_eq(m.wave_stats["wave_01"]["spawned"], 0)
	m.advance(start + 3.0)
	var total := 0
	for g in w1["groups"]:
		total += int(g["count"])
	assert_eq(m.wave_stats["wave_01"]["spawned"], total, "the whole first wave has spawned with no input at all")
	assert_true(m.wave_stats["wave_01"]["first_spawn_s"] >= start)
	assert_eq(m.sim.stats["produced"][1]["infantry"] + m.sim.stats["produced"][1]["tank"], total)
	assert_true(m.production_log.is_empty(), "no player production happened")
	# the same plan with perfect play spawns the same enemies at the same times
	var m2 := _match(level)
	_play(m2, level, start + 3.0)
	assert_eq(m2.wave_stats["wave_01"]["spawned"], total)
	assert_eq(m2.wave_stats["wave_01"]["first_spawn_s"], m.wave_stats["wave_01"]["first_spawn_s"])


func test_practice_chart_has_no_waves() -> void:
	var level := _level("second_pulse", "level_02.practice")
	var m := _match(level)
	m.advance(40.0)
	assert_true(m.upcoming_wave().is_empty())
	assert_eq(m.sim.count_alive(1, BattleSim.Kind.UNIT), 0, "practice spawns no enemies")
	assert_false(level.progression)


func test_groups_round_robin_and_failed_queues_do_not_advance_the_point() -> void:
	var sim := BattleSim.new()
	sim.setup(_rules(), {}, 1)
	var rifles := [{"actor": "e1", "count": 2}]
	for i in 6:
		var res := sim.produce_group(0, rifles, i + 1, i)
		assert_eq(res["result"], "queued")
		assert_eq(res["point"], i % 3)
	for i in 400:
		sim.tick()
	# members of a group share its point and stand near its home
	for gid in sim.groups:
		var g: Dictionary = sim.groups[gid]
		assert_eq(g["units"].size(), 2)
		var home: Vector2 = sim.defense_points[g["point"]]["pos"]
		for id in g["units"]:
			var e: BattleSim.Ent = sim.get_entity(id)
			assert_true(e.center().distance_to(home) < 3.5, "group %d unit near point %d" % [gid, g["point"]])
	# a dead barracks queues nothing
	var barracks: BattleSim.Ent = sim.get_entity(sim.producer_ids[0]["barracks"])
	sim._damage(barracks, barracks.max_hp + 1, null)
	var before := sim.groups.size()
	assert_eq(sim.produce_group(0, rifles, 99, 0)["result"], "no_producer")
	assert_eq(sim.groups.size(), before)
	assert_eq(sim.produce_group(0, [{"actor": "jeep", "count": 1}], 100, 0)["result"], "queued", "the war factory still works")


func test_match_cycles_points_per_successful_group_and_logs_group_ids() -> void:
	var level := _level("first_watch")
	var m := _match(level)
	_play(m, level, 12.0)
	var points: Array = []
	var ids: Array = []
	for e in m.production_log:
		assert_eq(e["result"], "queued")
		points.append(e["point"])
		ids.append(e["group_id"])
		assert_true(e.has("slot_id") and e.has("profile_id") and e.has("units"))
	assert_true(points.size() > 10)
	for i in points.size():
		assert_eq(points[i], i % 3, "round robin")
		assert_eq(ids[i], i + 1, "group ids count up")
	assert_eq(m.point_cursor, points.size())


func test_recipe_is_resolved_through_the_slot_not_the_button() -> void:
	var level := _level("second_pulse")
	var m := _match(level)
	_play(m, level, 30.0)
	var k1_buttons := {}
	var k2_seq: Array = []
	for e in m.production_log:
		if e["slot_id"] == "kick_1":
			assert_eq(e["units"], ["e1", "e1"], "March Kick always makes two riflemen")
			k1_buttons[e["button"]] = true
		elif e["slot_id"] == "kick_2":
			k2_seq.append(e["units"][0])
			assert_eq(e["units"].size(), 1)
		elif e["slot_id"] == "snare_1":
			assert_eq(e["units"], ["jeep"], "Guard Snare makes a jeep")
	assert_true(k2_seq.size() >= 4)
	for i in k2_seq.size():
		assert_eq(k2_seq[i], "1tnk" if i % 2 == 0 else "jeep", "Armour Kick alternates light tank and jeep")
	# the same kick slot on two different buttons produces the same thing
	var m2 := _match(level)
	var synth: Array = []
	for i in 6:
		var tick := 2000 + i * 2000
		synth.append({"id": "s%d" % i, "tick": tick, "time": level.tick_to_seconds(tick), "end_tick": tick, "end_time": level.tick_to_seconds(tick),
			"button": 1 if i % 2 == 0 else 3, "type": "tap", "duration_ticks": 0, "slot_id": "kick_1", "part_id": "kick_1", "source_note_id": "k:%d" % i,
			"family": "kick", "lane": "kick"})
	m2.level.notes = synth
	m2.judge.setup(synth)
	for n in synth:
		m2.advance(n["time"])
		m2.press(int(n["button"]), n["time"], 1)
	m2.advance(synth[5]["time"] + 0.5)
	assert_eq(m2.production_log.size(), 6)
	var btns := {}
	for e in m2.production_log:
		assert_eq(e["units"], ["e1", "e1"])
		btns[e["button"]] = true
	assert_eq(btns.keys().size(), 2, "buttons 1 and 3 both produced the same group")


func test_same_bass_slot_produces_its_group_on_every_button() -> void:
	var level := _level("hold_the_line")
	var m := _match(level)
	_play(m, level, level.duration_seconds())
	var buttons := {}
	var count := 0
	for e in m.production_log:
		if e["slot_id"] == "bass_1" and e["result"] == "queued":
			count += 1
			buttons[e["button"]] = true
			assert_eq(e["units"], ["e1", "e1", "e3"], "Patrol Sub: two riflemen and a rocket soldier")
	assert_eq(count, 29, "one group per completed hold")
	assert_eq(buttons.keys().size(), 4, "the same slot worked on buttons 1 to 4")


func test_unavailable_slot_is_inert_muted_and_restored_in_place() -> void:
	var level := _level("first_watch")
	var m := _match(level)
	m.advance(2.0)
	var barracks: BattleSim.Ent = m.sim.get_entity(m.sim.producer_ids[0]["barracks"])
	m.sim._damage(barracks, barracks.max_hp + 1, null)
	m.advance(2.1)
	assert_false(m.slot_available["kick_1"], "March Kick needs the barracks")
	assert_true(m.slot_available["snare_1"], "Guard Snare needs the war factory")
	assert_true(m.stems_muted["kick_1"])
	assert_false(m.stems_muted["snare_1"])
	assert_false(m.stems_muted["other"])
	var counter_before := int(m.slot_counter["kick_1"])
	var log_before := m.production_log.size()
	for n in level.notes:
		if n["slot_id"] == "kick_1" and n["time"] > 3.0 and n["time"] < 8.0:
			m.advance(n["time"])
			m.press(int(n["button"]), n["time"], 1)
	m.advance(8.5)
	assert_eq(int(m.slot_counter["kick_1"]), counter_before, "an unavailable slot never advances its counter")
	for e in m.production_log.slice(log_before):
		assert_true(e["slot_id"] != "kick_1")
	for i in level.notes.size():
		var n: Dictionary = level.notes[i]
		if n["slot_id"] == "kick_1" and n["time"] > 3.0 and n["time"] < 8.0:
			assert_eq(m.judge.state_of(i), Judge.State.UNAVAILABLE, "note %s is inert, not a miss" % n["id"])
	# producers return (test hook): the slot comes back and its stem is unmuted
	barracks.alive = true
	barracks.hp = barracks.max_hp
	m.advance(8.6)
	assert_true(m.slot_available["kick_1"])
	assert_false(m.stems_muted["kick_1"])
	# a focus change (bass mode) never mutes anything
	for key in m.stems_muted:
		assert_false(m.stems_muted[key] and key == "other")


func test_defense_run_is_deterministic() -> void:
	var level := _level("first_watch")
	var a := _match(level)
	var b := _match(level)
	_play(a, level, 30.0)
	_play(b, level, 30.0)
	assert_eq(a.production_log, b.production_log)
	assert_eq(a.sim.tick_count, b.sim.tick_count)
	assert_eq(a.sim.objective_hp("command_core"), b.sim.objective_hp("command_core"))
	assert_eq(a.sim.count_alive(0, BattleSim.Kind.UNIT), b.sim.count_alive(0, BattleSim.Kind.UNIT))
	assert_eq(a.sim.count_alive(1, BattleSim.Kind.UNIT), b.sim.count_alive(1, BattleSim.Kind.UNIT))


func test_waves_reference_known_entries_points_objectives_and_actors() -> void:
	var rules := _rules()
	for pack in ["first_watch", "second_pulse", "hold_the_line"]:
		var level := _level(pack)
		assert_eq(DefenseLoader.validate_battlefield(level, rules.battlefield, rules.actors), [], pack)
	var level := _level("first_watch")
	level.waves[0]["entry"] = "nowhere"
	level.waves[0]["groups"][0]["actor"] = "zzz"
	var errors := DefenseLoader.validate_battlefield(level, rules.battlefield, rules.actors)
	assert_contains(errors, "unknown entry")
	assert_contains(errors, "unknown actor")
