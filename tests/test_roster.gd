extends TestCase
## Unit variety and the fortified base: kicks walk the roster's vehicle cycle, snares produce mixed squads,
## actor rules decide crushing and turrets, wide warheads splash, brick walls stop light tanks, and the base
## layout carries the new defences on both sides.

const LEVEL_RULES := {
	"airfield_limit": 5, "aircraft_limit": 5, "initial_airfields": 0, "tank_per_kick": 1, "infantry_per_snare": 5,
	"repair_budget_credits_per_side": 500, "song_end_result": "defeat",
}


static func _sim() -> BattleSim:
	var sim := BattleSim.new()
	sim.setup(Rules.load_default(), LEVEL_RULES, 3)
	return sim


static func _spawned(sim: BattleSim, side: int) -> Array:
	var out := []
	for ev in sim.drain_events():
		if ev["kind"] == "spawned" and ev["side"] == side:
			out.append(ev["actor"])
	return out


func test_kicks_follow_the_vehicle_cycle_and_snares_mix_the_squad() -> void:
	var sim := _sim()
	var cycle: Array = sim.rules.vehicle_cycle
	assert_true(cycle.size() >= 6, "the roster cycles through several vehicle types")
	for i in cycle.size():
		var r := sim.produce(0, "kick")
		assert_eq(r["result"], "queued")
		assert_eq(r["actors"], [cycle[i]], "kick %d" % i)
	var squad: Array = sim.produce(0, "snare")["actors"]
	assert_eq(squad.size(), 5)
	assert_eq(squad, sim.rules.infantry_pattern.slice(0, 5), "the first snare takes the first five infantry")
	var distinct := {}
	for a in squad:
		distinct[a] = true
	assert_true(distinct.size() >= 2, "a squad mixes infantry types")
	for i in 60 * 25:
		sim.tick()
	var actors := _spawned(sim, 0)
	assert_eq(actors.size(), cycle.size() + 5, "everything queued was spawned")
	for a in cycle:
		assert_true(actors.has(a), "a %s was spawned" % a)
	var units: Dictionary = sim.stats["units"][0]
	var expected_e1 := 0
	for a in squad:
		if a == "e1":
			expected_e1 += 1
	assert_eq(int(units.get("e1", 0)), expected_e1, "the spawned riflemen match the squad pattern")
	assert_eq(sim.stats["produced"][0]["tank"], cycle.size(), "every vehicle still counts as a kick reward")
	assert_eq(sim.stats["produced"][1]["tank"], 0)


func test_actor_rules_decide_crushing_turrets_and_class() -> void:
	var sim := _sim()
	var jeep := sim._spawn_unit(0, "tank", Vector2(20.5, 10.5), "jeep")
	var tank := sim._spawn_unit(0, "tank", Vector2(21.5, 10.5), "1tnk")
	var mammoth := sim._spawn_unit(0, "tank", Vector2(22.5, 10.5), "4tnk")
	var arty := sim._spawn_unit(0, "tank", Vector2(23.5, 10.5), "arty")
	var rocket := sim._spawn_unit(0, "infantry", Vector2(24.5, 10.5), "e3")
	assert_false(jeep.crushes_walls, "a wheeled jeep crushes nothing")
	assert_false(jeep.crushes_infantry)
	assert_true(jeep.has_turret)
	assert_true(tank.crushes_walls and tank.crushes_infantry)
	assert_false(tank.crushes_heavy_walls, "a light tank cannot crush brick")
	assert_true(mammoth.crushes_heavy_walls, "the mammoth tank crushes brick walls")
	assert_false(arty.has_turret, "artillery aims with its hull")
	assert_near(sim.min_range_vs(arty, tank), 4.0, 0.001, "artillery keeps its minimum range")
	assert_true(rocket.hits_air and rocket.hits_ground, "a rocket soldier shoots at both air and ground")
	assert_near(rocket.radius, 0.18, 0.001, "a foot locomotor makes it infantry")
	assert_true(rocket.target_types.has("Infantry"))


func test_wide_warheads_splash_with_falloff_and_narrow_ones_do_not() -> void:
	assert_eq(BattleSim.splash_percent(0.0, 0.416), 100)
	assert_eq(BattleSim.splash_percent(0.416, 0.416), 37)
	assert_eq(BattleSim.splash_percent(0.832, 0.416), 14)
	assert_eq(BattleSim.splash_percent(2.0, 0.416), 0, "nothing beyond four spreads")
	var sim := _sim()
	var shooter := sim._spawn_unit(0, "tank", Vector2(20.5, 10.5), "arty")
	var a := sim._spawn_unit(1, "tank", Vector2(30.5, 10.5), "1tnk")
	var b := sim._spawn_unit(1, "tank", Vector2(30.5, 10.8), "1tnk")
	var far := sim._spawn_unit(1, "infantry", Vector2(33.5, 10.5), "e1")
	var friend := sim._spawn_unit(0, "infantry", Vector2(30.5, 10.2), "e1")
	sim._rebuild_grid()
	sim._impact(a, sim._damage_against(sim.rules.weapon("155mm"), a), shooter, "155mm", a.center(), true)
	assert_true(a.hp < a.max_hp, "the aimed-at tank is hit")
	assert_true(b.hp < b.max_hp, "the tank beside it is hit by the splash")
	assert_true(b.hp > a.hp, "farther from the burst means less damage")
	assert_eq(far.hp, far.max_hp, "three cells away is outside the burst")
	assert_eq(friend.hp, friend.max_hp, "splash never hurts the shooter's own side")
	var sim2 := _sim()
	var rifle := sim2._spawn_unit(0, "infantry", Vector2(20.5, 10.5), "e1")
	var c := sim2._spawn_unit(1, "infantry", Vector2(25.5, 10.5), "e1")
	var d := sim2._spawn_unit(1, "infantry", Vector2(25.5, 10.7), "e1")
	sim2._rebuild_grid()
	sim2._impact(c, sim2._damage_against(sim2.rules.weapon("M1Carbine"), c), rifle, "M1Carbine", c.center(), true)
	assert_true(c.hp < c.max_hp)
	assert_eq(d.hp, d.max_hp, "a rifle round hits one soldier only")


func test_fortified_base_on_both_sides() -> void:
	var sim := _sim()
	for side in 2:
		var roles := {}
		for e in sim.entities:
			if e.side == side and e.kind == BattleSim.Kind.BUILDING:
				roles[e.role] = int(roles.get(e.role, 0)) + 1
		assert_eq(int(roles.get("brick", 0)), 10, "side %d brick wall" % side)
		assert_eq(int(roles.get("wall", 0)), 12, "side %d sandbags" % side)
		assert_eq(int(roles.get("pillbox", 0)), 2, "side %d pillboxes" % side)
		assert_eq(int(roles.get("turret", 0)), 2, "side %d gun turrets" % side)
		assert_eq(int(roles.get("sam", 0)), 2, "side %d SAM sites" % side)
		assert_eq(int(roles.get("power", 0)), 3, "side %d power plants" % side)
		assert_eq(int(roles.get("dome", 0)), 1, "side %d radar dome" % side)
		assert_eq(int(roles.get("depot", 0)), 1, "side %d service depot" % side)
	# a pillbox is armed and the brick wall is a wall that only the mammoth tank can crush
	var pbox: BattleSim.Ent = null
	var brick: BattleSim.Ent = null
	for e in sim.entities:
		if e.side == 1 and e.role == "pillbox":
			pbox = e
		if e.side == 1 and e.role == "brick":
			brick = e
	assert_true(pbox != null and not pbox.weapons.is_empty(), "the pillbox has its Vulcan")
	assert_false(pbox.has_turret, "the pillbox fires without a turret")
	assert_true(brick.is_wall)
	assert_true(brick.target_types.has("NoAutoTarget"), "walls are never auto-targeted")
	var tank := sim._spawn_unit(0, "tank", Vector2(brick.x - 1.0, brick.y), "1tnk")
	tank.heading = 0.0
	assert_false(sim._try_step(tank, Vector2(1.0, 0.0)), "a light tank cannot drive through brick")
	assert_true(brick.alive)
	var mammoth := sim._spawn_unit(0, "tank", Vector2(brick.x - 1.0, brick.y), "4tnk")
	assert_true(sim._try_step(mammoth, Vector2(1.0, 0.0)), "the mammoth tank crushes it")
	assert_false(brick.alive)


func test_production_queue_tells_the_view_which_building_is_busy() -> void:
	var sim := _sim()
	assert_false(sim.queue_has(0, "tank"))
	sim.produce(0, "kick")
	sim.produce(0, "snare")
	assert_true(sim.queue_has(0, "tank"))
	assert_true(sim.queue_has(0, "infantry"))
	assert_false(sim.queue_has(1, "tank"))
	for i in 25 * 5:
		sim.tick()
	assert_false(sim.queue_has(0, "tank"), "the queue drains")
