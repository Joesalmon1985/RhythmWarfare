extends TestCase
## Battle simulation: production (A01, A03), air lifecycle and limits (A05, A06), repair fixtures (A07),
## enemy gates (A08) and outcomes (A11).

const LEVEL_RULES := {
	"airfield_limit": 5, "aircraft_limit": 5, "initial_airfields": 0, "tank_per_kick": 1, "infantry_per_snare": 5,
	"repair_budget_credits_per_side": 5000, "song_end_result": "defeat",
}


static func _sim(level_rules: Dictionary = LEVEL_RULES) -> BattleSim:
	var sim := BattleSim.new()
	sim.setup(Rules.load_default(), level_rules, 27)
	return sim


static func _run(sim: BattleSim, ticks: int) -> void:
	for i in ticks:
		sim.tick()


static func _find(sim: BattleSim, side: int, role: String) -> BattleSim.Ent:
	for e in sim.entities:
		if e.alive and e.side == side and e.role == role:
			return e
	return null


static func _kill(sim: BattleSim, e: BattleSim.Ent) -> void:
	sim._damage(e, e.hp, null)


func test_initial_layout_is_mirrored() -> void:
	var sim := _sim()
	for side in 2:
		for role in ["main", "factory", "barracks", "power", "turret", "aa", "sam", "wall"]:
			assert_true(_find(sim, side, role) != null, "side %d has %s" % [side, role])
		assert_eq(sim.pads_alive(side), 0, "no initial airfields")
	var pm := sim.main_base(0)
	var em := sim.main_base(1)
	assert_near(pm.x + em.x, float(sim.width), 0.001, "main bases mirror across the centre")
	assert_eq(sim.outcome, "")


func test_a01_ten_kicks_ten_snares() -> void:
	var sim := _sim()
	for i in 10:
		assert_eq(sim.produce(0, "kick")["result"], "queued")
		assert_eq(sim.produce(0, "snare")["result"], "queued")
	_run(sim, 60 * 25)  # a minute: everything leaves the exit queue (units walk off and fight)
	var tanks := 0
	var inf := 0
	for ev in sim.drain_events():
		if ev["kind"] == "spawned" and ev["side"] == 0:
			if ev["role"] == "tank":
				tanks += 1
			else:
				inf += 1
	assert_eq(tanks, 10)
	assert_eq(inf, 50)
	assert_eq(sim.stats["produced"][0]["tank"], 10)
	assert_eq(sim.stats["produced"][0]["infantry"], 50)
	assert_eq(sim.stats["produced"][1]["tank"], 0, "the enemy got nothing")


func test_a03_destroyed_producer_blocks_only_its_lane() -> void:
	var sim := _sim()
	var factory := _find(sim, 0, "factory")
	sim.produce(0, "kick")
	_run(sim, 10)
	assert_eq(sim.count_alive(0, BattleSim.Kind.UNIT), 1)
	_kill(sim, factory)
	assert_false(sim.producer_alive(0, "factory"))
	assert_eq(sim.produce(0, "kick")["result"], "no_factory")
	assert_eq(sim.produce(0, "snare")["result"], "queued", "barracks still produces")
	assert_true(sim.producer_alive(1, "factory"), "the enemy factory is untouched")
	_run(sim, 30)
	assert_true(sim.count_alive(0, BattleSim.Kind.UNIT) >= 1, "existing tank keeps fighting")
	var lost := false
	for ev in sim.drain_events():
		if ev["kind"] == "producer_lost" and ev["side"] == 0 and ev["role"] == "factory":
			lost = true
	assert_true(lost, "producer_lost event emitted")


func test_a05_bass_builds_five_pads_then_five_aircraft_then_busy() -> void:
	var sim := _sim()
	for i in 5:
		var r := sim.produce(0, "bass")
		assert_eq(r["result"], "pad_built", "action %d builds a pad" % i)
		assert_true(r["aircraft_created"])
		assert_true(r["launched"], "a new aircraft is ready and launches")
	assert_eq(sim.pads_alive(0), 5)
	assert_eq(sim.live_aircraft(0), 5)
	var busy := sim.produce(0, "bass")
	assert_eq(busy["result"], "air_busy", "all five are flying")
	assert_eq(sim.live_aircraft(0), 5, "never more than five aircraft")
	assert_eq(sim.pads_alive(0), 5, "never more than five pads")
	assert_eq(sim.stats["air_busy"][0], 1)


func test_a06_aircraft_lifecycle_and_grounded_until_next_bass() -> void:
	# one slot only, so a later bass action cannot be spent on building another pad
	var rules := LEVEL_RULES.duplicate()
	rules["airfield_limit"] = 1
	rules["aircraft_limit"] = 1
	var sim := _sim(rules)
	sim.produce(0, "bass")
	var a: BattleSim.Ent = sim.get_entity(sim.slots[0][0]["aircraft"])
	assert_eq(a.air, BattleSim.Air.SORTIE)
	assert_eq(a.ammo, 8)
	# fly until out of ammo (it attacks the enemy base) or get shot down; cap at 90 s
	var t := 0
	while a.alive and a.air == BattleSim.Air.SORTIE and t < 90 * 25:
		sim.tick()
		t += 1
	if not a.alive:
		fail("aircraft was shot down before spending its ammo; adjust AA placement (ammo left %d)" % a.ammo)
		return
	assert_eq(a.ammo, 0, "returns only when empty")
	assert_eq(a.air, BattleSim.Air.RETURNING)
	t = 0
	while a.air != BattleSim.Air.REARMING and t < 60 * 25:
		sim.tick()
		t += 1
	assert_eq(a.air, BattleSim.Air.REARMING, "landed on its pad")
	_run(sim, 8 * 50 + 5)
	assert_eq(a.air, BattleSim.Air.READY, "rearmed after 8 x 50 ticks")
	assert_eq(a.ammo, 8)
	_run(sim, 200)
	assert_eq(a.air, BattleSim.Air.READY, "rearming alone never launches")
	var r := sim.produce(0, "bass")
	assert_eq(r["result"], "sortie")
	assert_eq(a.air, BattleSim.Air.SORTIE)


func test_a05_pad_destroyed_with_parked_aircraft_and_rebuild_does_not_duplicate() -> void:
	var sim := _sim()
	sim.produce(0, "bass")
	var a: BattleSim.Ent = sim.get_entity(sim.slots[0][0]["aircraft"])
	var pad: BattleSim.Ent = sim.get_entity(sim.slots[0][0]["pad"])
	# airborne aircraft survives its pad
	_kill(sim, pad)
	assert_true(a.alive, "airborne aircraft continues its sortie")
	assert_eq(sim.pads_alive(0), 0)
	var r := sim.produce(0, "bass")
	assert_eq(r["result"], "pad_built")
	assert_eq(r["slot"], 0, "the destroyed used slot is rebuilt first")
	assert_false(r["aircraft_created"], "no clone while the aircraft lives")
	assert_eq(sim.live_aircraft(0), 1)
	# parked aircraft dies with its pad
	var sim2 := _sim()
	sim2.produce(0, "bass")
	var b: BattleSim.Ent = sim2.get_entity(sim2.slots[0][0]["aircraft"])
	b.air = BattleSim.Air.READY
	_kill(sim2, sim2.get_entity(sim2.slots[0][0]["pad"]))
	assert_false(b.alive, "parked aircraft destroyed with its pad")
	assert_eq(sim2.live_aircraft(0), 0)
	var r2 := sim2.produce(0, "bass")
	assert_eq(r2["result"], "pad_built")
	assert_true(r2["aircraft_created"], "a replacement is created once the old one is gone")
	assert_eq(sim2.live_aircraft(0), 1)


func test_a07_repair_fixture_matches_openra_arithmetic() -> void:
	var sim := _sim()
	var weap := _find(sim, 0, "factory")  # value 2000, HP 150000, Wood
	assert_eq(weap.max_hp, 150000)
	assert_eq(weap.value, 2000)
	sim._damage(weap, 10000, null)
	assert_true(weap.repairing, "repair starts automatically on damage")
	var credits_before: int = sim.credits[0]
	sim.tick()
	assert_eq(weap.hp, 140700, "first step on the next tick restores RepairStep 700")
	assert_eq(sim.credits[0], credits_before - 1, "cost = max(1, 700*20*2000/(150000*100)) = 1")
	_run(sim, 24)
	assert_eq(weap.hp, 140700, "24 ticks of interval pass without a step")
	sim.tick()
	assert_eq(weap.hp, 141400, "second step on tick 26")
	_run(sim, 25 * 12)
	assert_eq(weap.hp, 149800, "14 steps of 700")
	_run(sim, 25)
	assert_eq(weap.hp, 150000, "last step is capped to the missing 200 HP")
	assert_false(weap.repairing, "stops at maximum health")
	assert_eq(sim.credits[0], credits_before - 15, "fifteen charged steps")
	_run(sim, 50)
	assert_eq(weap.hp, 150000, "never exceeds max")


func test_a07_repair_stops_without_funds_and_walls_never_repair() -> void:
	var sim := _sim()
	sim.credits[0] = 3
	var weap := _find(sim, 0, "factory")
	sim._damage(weap, 10000, null)
	_run(sim, 25 * 10)
	assert_eq(weap.hp, 140000 + 2100, "three paid steps only")
	assert_eq(sim.credits[0], 0)
	var wall := _find(sim, 0, "wall")
	sim.credits[0] = 1000
	sim._damage(wall, 1000, null)
	_run(sim, 100)
	assert_eq(wall.hp, wall.max_hp - 1000, "walls are not RepairableBuilding")
	# destroyed buildings never come back
	var barr := _find(sim, 0, "barracks")
	_kill(sim, barr)
	_run(sim, 100)
	assert_false(barr.alive)
	assert_false(sim.producer_alive(0, "barracks"))


func test_a07_pad_repair_cost_rounds_up_to_one() -> void:
	var sim := _sim()
	sim.produce(0, "bass")
	var pad: BattleSim.Ent = sim.get_entity(sim.slots[0][0]["pad"])
	assert_eq(pad.max_hp, 80000)
	assert_eq(pad.value, 500)
	sim._damage(pad, 700, null)
	var c: int = sim.credits[0]
	sim.tick()
	assert_eq(pad.hp, 80000)
	assert_eq(sim.credits[0], c - 1, "700*20*500/(80000*100) = 0.875 -> max(1, 0) = 1")


func test_a08_enemy_actions_obey_the_same_gates() -> void:
	var sim := _sim()
	assert_eq(sim.produce(1, "kick")["result"], "queued")
	_kill(sim, _find(sim, 1, "factory"))
	assert_eq(sim.produce(1, "kick")["result"], "no_factory", "a scheduled tank cannot bypass a destroyed factory")
	for i in 5:
		sim.produce(1, "bass")
	assert_eq(sim.pads_alive(1), 5)
	assert_eq(sim.produce(1, "bass")["result"], "air_busy", "the cap binds the enemy too")


func test_a11_outcomes() -> void:
	var sim := _sim()
	_kill(sim, sim.main_base(1))
	assert_eq(sim.outcome, "", "outcomes resolve at the end of the step, after all damage")
	sim.tick()
	assert_eq(sim.outcome, "victory")
	var sim2 := _sim()
	_kill(sim2, sim2.main_base(0))
	sim2.tick()
	assert_eq(sim2.outcome, "defeat")
	assert_eq(sim2.outcome_reason, "main_base_destroyed")
	var sim3 := _sim()
	sim3.main_base(0).hp = 1
	sim3.main_base(1).hp = 1
	sim3._damage(sim3.main_base(1), 1, null)
	sim3._damage(sim3.main_base(0), 1, null)
	sim3.tick()
	assert_eq(sim3.outcome, "defeat", "mutual destruction in one step is a loss")
	assert_eq(sim3.outcome_reason, "mutual_destruction")
	var sim4 := _sim()
	sim4.end_by_song()
	assert_eq(sim4.outcome, "defeat")
	assert_eq(sim4.outcome_reason, "song_end")
	assert_eq(sim4.produce(0, "kick")["result"], "ended", "no production after the outcome")


func test_determinism_same_seed_same_trace() -> void:
	var a := _sim()
	var b := _sim()
	for sim in [a, b]:
		for i in 6:
			sim.produce(0, "kick")
			sim.produce(1, "snare")
		sim.produce(0, "bass")
		sim.produce(1, "bass")
		_run(sim, 25 * 40)
	assert_eq(a.tick_count, b.tick_count)
	assert_eq(a.entities.size(), b.entities.size())
	for i in a.entities.size():
		assert_eq(a.entities[i].hp, b.entities[i].hp, "entity %d hp" % i)
		assert_near(a.entities[i].x, b.entities[i].x, 0.0, "entity %d x" % i)
	assert_true(a.count_alive(0, BattleSim.Kind.UNIT) < 6 or a.count_alive(1, BattleSim.Kind.UNIT) < 30, "forty seconds of combat killed something")
