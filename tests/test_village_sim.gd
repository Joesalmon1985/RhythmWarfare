extends TestCase
## The village in BattleSim / DefenseAi / Match (plan "Mission 1: the village level", package B): civilians as side-0
## entities that are scenery for every count, never targeted or repaired by the player's side, that flee and die;
## wave target classes with their fall-through; start units; squad rewards; the active section.
## Runs on tests/fixtures/village_test.json (defense_02's compound with a barracks in the middle, four houses, four
## civilians). Civilian actors and squad rewards that the art and content packages add are injected when missing.

const FIXTURE := "res://tests/fixtures/village_test.json"
const START_ALL := [
	{"actor": "e1", "count": 5, "point": "defense_1"},
	{"actor": "e1", "count": 5, "point": "defense_2"},
	{"actor": "e1", "count": 5, "point": "defense_3"},
]


func _rules() -> Rules:
	var r := Rules.load_default("openra_mvp_01", "defense_02")
	r.battlefield = JSON.parse_string(FileAccess.get_file_as_string(FIXTURE))
	for a in ["tecn", "c1", "c2"]:
		if not r.actors.has(a):
			var d: Dictionary = r.actors["e1"].duplicate(true)
			d["armaments"] = []
			d["hp"] = 2500
			r.actors[a] = d
	for i in range(1, 9):
		var v := "v%02d" % i
		if not r.actors.has(v):
			r.actors[v] = {"name": v, "hp": 40000, "armor": "Wood", "speed": 0, "cost": 0, "building": {"dimensions": "2,2"}, "armaments": []}
	return r


func _ensure_rewards() -> void:
	var rw: Dictionary = MissionRules.data()["rewards"]
	if not rw.has("rifle_squad"):
		rw["rifle_squad"] = {"type": "unit", "actor": "e1", "count": 3, "name": "Rifle squad"}
	if not rw.has("grenadier_squad"):
		rw["grenadier_squad"] = {"type": "unit", "actor": "e2", "count": 3, "name": "Grenadier squad"}


func _sim(level_rules: Dictionary = {}, seed_value: int = 1) -> BattleSim:
	_ensure_rewards()
	var sim := BattleSim.new()
	sim.setup(_rules(), level_rules, seed_value)
	return sim


## Ticks n times and returns every event produced.
func _tick(sim: BattleSim, n: int) -> Array:
	var out: Array = []
	for i in n:
		sim.tick()
		out.append_array(sim.drain_events())
	return out


func _civs(sim: BattleSim) -> Array:
	var out: Array = []
	for e in sim.entities:
		if e.civilian and e.kind == BattleSim.Kind.UNIT:
			out.append(e)
	return out


func _houses(sim: BattleSim) -> Array:
	var out: Array = []
	for e in sim.entities:
		if e.civilian and e.kind == BattleSim.Kind.BUILDING:
			out.append(e)
	return out


func _barracks(sim: BattleSim) -> BattleSim.Ent:
	return sim.get_entity(int(sim.producer_ids[0]["barracks"]))


## A side-1 wave unit of a target class, moved to `at` (stage 0, idle, like a fresh spawn).
func _raider(sim: BattleSim, cls: String, at: Vector2, actor: String = "e1") -> BattleSim.Ent:
	var u := sim.spawn_wave_unit(actor, "left", "defense_1", "barracks", cls)
	assert_true(u != null, "the entry is free")
	u.x = at.x
	u.y = at.y
	return u


func _defenders(sim: BattleSim) -> Array:
	var out: Array = []
	for e in sim.entities:
		if e.alive and e.side == 0 and e.kind == BattleSim.Kind.UNIT and not e.civilian:
			out.append(e)
	return out


# ---------------------------------------------------------------- setup

func test_setup_builds_the_village_and_counts_stay_clean() -> void:
	var sim := _sim()
	assert_eq(_civs(sim).size(), 4)
	assert_eq(_houses(sim).size(), 4)
	assert_eq([sim.stats["civilians_total"], sim.stats["civilians_lost"], sim.stats["houses_total"], sim.stats["houses_lost"]], [4, 0, 4, 0])
	assert_eq(sim.civilians_alive(), 4)
	assert_eq(sim.houses_alive(), 4)
	assert_eq(sim.count_alive(0, BattleSim.Kind.UNIT), 0, "civilians are not an army")
	assert_eq(sim.count_alive(1, BattleSim.Kind.UNIT), 0)
	for c in _civs(sim):
		assert_eq(c.side, 0, "civilians are side-0 entities, there is no third side")
		assert_true(c.weapons.is_empty() and not c.hits_ground and not c.hits_air, "unarmed")
		assert_eq(c.group, -1)
		assert_near(c.speed, c.civ_speed * 0.6, 1e-9, "wander at 60 % speed")
	for h in _houses(sim):
		assert_eq([h.side, h.role, h.is_defence, h.w, h.h], [0, "village", false, 2, 2])
		assert_true(h.actor.begins_with("v0"), "the actor override names the house")
	assert_eq(sim.civ_rng.seed, 1 * 13 + 5, "civilians have their own rng")
	assert_true(sim.events.is_empty(), "setup leaves no events behind")
	assert_eq(sim.objectives.size(), 1)
	assert_eq(sim.objectives[0]["id"], "barracks")
	assert_true(_barracks(sim) != null and _barracks(sim).role == "barracks")
	assert_eq(sim.primary_objective_id(), "barracks")
	var exit_pos := Vector2(39.5, 22.5)
	assert_true(sim.village_spots.size() > 100, "a wander area of some size")
	for s in sim.village_spots:
		assert_false(sim._blocked.has(Vector2i(int(floor(s.x)), int(floor(s.y)))), "spots are free cells")
		assert_true(s.distance_to(exit_pos) > 2.0, "none near the barracks exit")
		assert_true(s.x >= 30.0 and s.x <= 49.0 and s.y >= 17.0 and s.y <= 25.0, "inside the wander rect")
	assert_eq([sim.wander_radius, sim.flee_radius], [5.0, 6.0])


func test_unknown_civilian_actor_falls_back_to_e1_stats() -> void:
	var r := _rules()
	r.actors.erase("c1")
	r.battlefield["civilians"] = [{"actor": "c1", "x": 38, "y": 18}]
	var sim := BattleSim.new()
	sim.setup(r, {}, 1)
	var c: Array = _civs(sim)
	assert_eq(c.size(), 1)
	assert_eq(c[0].actor, "c1", "the sprite name is kept")
	assert_eq(c[0].hp, int(r.actors["e1"]["hp"]), "e1's health")
	assert_true(c[0].weapons.is_empty(), "and never e1's rifle")


func test_the_combat_rng_does_not_depend_on_civilians() -> void:
	var with_civs := _sim({}, 7)
	var r := _rules()
	r.battlefield["civilians"] = []
	var without := BattleSim.new()
	without.setup(r, {}, 7)
	assert_eq(with_civs.rng.randi(), without.rng.randi(), "same combat rng stream with and without civilians")


# ---------------------------------------------------------------- start units

func test_start_units_hold_their_points_in_their_own_groups() -> void:
	var sim := _sim({"start_units": START_ALL})
	var d := _defenders(sim)
	assert_eq(d.size(), 15)
	assert_eq(sim.count_alive(0, BattleSim.Kind.UNIT), 15, "civilians do not add to it")
	assert_eq(sim.groups.size(), 3)
	for pt in 3:
		assert_eq(sim.units_at(pt), 5, "five at point %d" % pt)
	assert_true(sim.events.is_empty())
	for u in d:
		assert_true(u.group >= 0 and sim.groups.has(u.group))
		assert_eq(u.order, "idle")
		assert_eq(u.leash, sim.leash_cells)
		var pt: Vector2 = sim.defense_points[int(sim.groups[u.group]["point"])]["pos"]
		assert_true(u.center().distance_to(pt) < 1.5, "stands on its point")
		assert_eq(u.home, u.center(), "and that is its home")
	_tick(sim, 150)
	for u in _defenders(sim):
		var pt: Vector2 = sim.defense_points[int(sim.groups[u.group]["point"])]["pos"]
		assert_true(u.center().distance_to(pt) < 2.5, "they hold")
		assert_eq(u.order, "idle")
	# two entries on one point are two groups with different rings
	var two := _sim({"start_units": [{"actor": "e1", "count": 2, "point": "defense_2"}, {"actor": "e1", "count": 2, "point": "defense_2"}]})
	assert_eq(two.groups.size(), 2)
	assert_eq(two.units_at(1), 4)
	var homes := {}
	for u in _defenders(two):
		homes[u.home] = true
	assert_eq(homes.size(), 4, "no two defenders share a place")


# ---------------------------------------------------------------- civilians vs the two sides

func test_player_side_never_targets_or_repairs_civilians() -> void:
	var sim := _sim({"start_units": START_ALL})
	# a rifleman and a pillbox right beside the civilians, and an enemy with nothing else to shoot at
	sim.schedule_reward("pillbox", 1, 0)
	var civs := _civs(sim)
	var rifleman: BattleSim.Ent = _defenders(sim)[0]
	rifleman.x = (civs[0] as BattleSim.Ent).x + 1.0
	rifleman.y = (civs[0] as BattleSim.Ent).y
	var ids := {}
	for c in civs:
		ids[c.id] = true
	for h in _houses(sim):
		ids[h.id] = true
	_raider(sim, "core", Vector2(20.5, 21.5))
	for i in 200:
		sim.tick()
		for e in sim.entities:
			if e.alive and e.side == 0 and e.target >= 0:
				assert_false(ids.has(e.target), "side 0 never aims at the village")
	# damaged houses never repair themselves; the barracks does
	var sim2 := _sim()
	var house: BattleSim.Ent = _houses(sim2)[0]
	var raider := _raider(sim2, "civilians", Vector2(10.5, 10.5))
	sim2._damage(house, 9000, raider)
	sim2._damage(_barracks(sim2), 9000, raider)
	assert_false(house.repairing, "no auto repair for a house")
	assert_true(_barracks(sim2).repairing, "control: the barracks does")
	var hp := house.hp
	_tick(sim2, 300)
	assert_eq(house.hp, hp, "and its health never comes back")
	assert_true(_barracks(sim2).hp > _barracks(sim2).max_hp - 9000)
	# a reward repair crew does not touch civilians either
	sim2.schedule_reward("repair", sim2.tick_count + 1)
	_tick(sim2, 3)
	assert_eq(house.hp, hp)


func test_class_filter_and_civilian_bias_in_scan_for_target() -> void:
	var sim := _sim({"start_units": [{"actor": "e1", "count": 1, "point": "defense_1"}]})
	var civ: BattleSim.Ent = _civs(sim)[0]
	var rifle: BattleSim.Ent = _defenders(sim)[0]
	var house: BattleSim.Ent = _houses(sim)[0]
	var barracks := _barracks(sim)
	civ.x = 36.5
	civ.y = 20.5
	rifle.x = 36.5
	rifle.y = 17.5
	var results := {}
	for cls in ["defenses", "civilians", "core"]:
		var u := _raider(sim, cls, Vector2(36.5, 18.5))  # 1 from the rifleman, 2 from the civilian
		sim._rebuild_grid()
		var found := sim.scan_for_target(u, 6.0)
		results[cls] = found
		u.alive = false
	assert_eq(results["defenses"], rifle.id, "a defender is nearer and a civilian costs +2")
	assert_eq(results["core"], rifle.id)
	rifle.x = 36.5
	rifle.y = 16.6  # 1.9 away: the civilian (2.0 - 1) now wins for a village raider only
	var u2 := _raider(sim, "civilians", Vector2(36.5, 18.5))
	sim._rebuild_grid()
	assert_eq(sim.scan_for_target(u2, 6.0), civ.id, "a raider after the village prefers civilians")
	u2.alive = false
	var u3 := _raider(sim, "defenses", Vector2(36.5, 18.5))
	sim._rebuild_grid()
	assert_eq(sim.scan_for_target(u3, 6.0), rifle.id)
	u3.alive = false
	# buildings: houses only for civilians, the objective only for core
	var civs_all := _civs(sim)
	for cls in ["defenses", "civilians", "core"]:
		var u := _raider(sim, cls, Vector2(36.5, 20.5))
		for c in civs_all:
			c.alive = false
		rifle.alive = false
		sim._rebuild_grid()
		var found := sim.scan_for_target(u, 12.0)
		var want := -1
		if cls == "civilians":
			want = house.id
		elif cls == "core":
			want = barracks.id
		assert_eq(found, want, "class %s" % cls)
		u.alive = false
		for c in civs_all:
			c.alive = true
		rifle.alive = true
	# nothing the player owns can scan the village: same side
	sim._rebuild_grid()
	assert_eq(sim.scan_for_target(rifle, 12.0), -1, "no enemy on the field, and its own side is never a target")


func test_civilian_flees_an_enemy_and_calms_down() -> void:
	var sim := _sim()
	var civ: BattleSim.Ent = _civs(sim)[0]
	civ.order = "idle"
	var enemy := _raider(sim, "core", civ.center() + Vector2(0.0, -3.0))
	enemy.weapons = []  # an unarmed intruder: only the fear is under test
	enemy.hits_ground = false
	enemy.wait_ticks = 1000000
	var d0 := civ.center().distance_to(enemy.center())
	_tick(sim, 10)
	assert_eq(civ.civ_state, "flee")
	assert_eq(civ.order, "move")
	assert_eq(civ.speed, civ.civ_speed, "it runs at full speed")
	var spot: Vector2 = civ.order_pos
	for s in sim.village_spots:
		assert_true(s.distance_to(enemy.center()) <= spot.distance_to(enemy.center()) + 0.001, "the spot farthest from the threat")
	_tick(sim, 50)
	assert_true(civ.center().distance_to(enemy.center()) > d0 + 1.0, "it ran away (%.2f from %.2f)" % [civ.center().distance_to(enemy.center()), d0])
	sim._kill(enemy, null)
	_tick(sim, 60)
	assert_eq(civ.civ_state, "wander", "calm again once the enemy is gone")
	assert_near(civ.speed, civ.civ_speed * 0.6, 1e-9)


func test_civilians_wander_at_a_walk_near_home() -> void:
	var sim := _sim()
	var start := {}
	for c in _civs(sim):
		start[c.id] = c.center()
	for i in 600:
		sim.tick()
		for c in _civs(sim):
			assert_true(c.center().distance_to(c.civ_home) <= sim.wander_radius + 2.5, "stays about its home")
			assert_eq(c.civ_state, "wander")
	var walked := 0
	for c in _civs(sim):
		if c.center().distance_to(start[c.id]) > 0.3:
			walked += 1
	assert_true(walked >= 1, "somebody took a walk in 24 s")


func test_shot_civilians_and_houses_are_counted_apart() -> void:
	var sim := _sim({"start_units": START_ALL})
	var army_lost_before: Dictionary = sim.stats["lost"][0].duplicate()
	# an enemy rifleman standing among the civilians with the village as his class: somebody dies
	var civ: BattleSim.Ent = _civs(sim)[0]
	var raider := _raider(sim, "civilians", civ.center() + Vector2(2.0, 0.0))
	raider.stage = 1
	var dead: Array = []
	for i in 1500:
		sim.tick()
		for ev in sim.drain_events():
			if ev["kind"] == "destroyed" and ev["civilian"]:
				dead.append(ev)
		if not dead.is_empty():
			break
	assert_true(not dead.is_empty(), "a flee-and-die civilian within 60 s")
	assert_eq(dead[0]["ekind"], "unit")
	assert_eq(dead[0]["side"], 0)
	assert_true(dead[0]["actor"] in ["tecn", "c1"], "the event names the actor")
	assert_eq(sim.stats["civilians_lost"], dead.size())
	assert_eq(sim.stats["lost"][0], army_lost_before, "never counted as the player's losses")
	assert_eq(sim.civilians_alive(), 4 - dead.size())
	assert_eq(sim.count_alive(0, BattleSim.Kind.UNIT), 15, "the army count did not move")
	# houses
	var house: BattleSim.Ent = _houses(sim)[0]
	var bld := sim.count_alive(0, BattleSim.Kind.BUILDING)
	sim._damage(house, house.max_hp + 1, raider)
	var evs := sim.drain_events()
	var kills := evs.filter(func(ev): return ev["kind"] == "destroyed")
	assert_eq(kills.size(), 1)
	assert_eq([kills[0]["civilian"], kills[0]["ekind"], kills[0]["role"], kills[0]["actor"]], [true, "building", "village", house.actor])
	assert_eq([sim.stats["houses_lost"], sim.houses_alive()], [1, 3])
	assert_eq(sim.count_alive(0, BattleSim.Kind.BUILDING), bld, "houses are not the player's buildings either")
	assert_false(sim.stats["lost"][0].has("village"))
	var hit := evs.filter(func(ev): return ev["kind"] == "hit")
	assert_eq([hit[0]["side"], hit[0]["role"], hit[0]["civilian"]], [0, "village", true])


func test_event_fields_for_the_view() -> void:
	var sim := _sim({"start_units": [{"actor": "e1", "count": 1, "point": "defense_1"}]})
	var rifle: BattleSim.Ent = _defenders(sim)[0]
	rifle.x = 20.5
	rifle.y = 21.5
	_raider(sim, "defenses", Vector2(22.5, 21.5))
	var shot: Dictionary = {}
	var hit: Dictionary = {}
	var gone: Dictionary = {}
	for i in 300:
		for ev in _tick(sim, 1):
			if ev["kind"] == "shot" and shot.is_empty():
				shot = ev
			elif ev["kind"] == "hit" and hit.is_empty():
				hit = ev
			elif ev["kind"] == "destroyed" and gone.is_empty():
				gone = ev
		if not gone.is_empty():
			break
	assert_true(not shot.is_empty() and shot.has("actor") and shot.has("side"), "shot carries actor and side")
	assert_eq(shot["actor"], "e1")
	assert_true(not hit.is_empty() and hit.has("side") and hit.has("role") and hit.has("civilian"))
	assert_true(not gone.is_empty())
	assert_eq([gone["civilian"], gone["ekind"], gone["actor"]], [false, "unit", "e1"])
	# the spawned event says whether it is a civilian
	var r := _rules()
	var s2 := BattleSim.new()
	s2.setup(r, {}, 1)
	var u := s2.spawn_wave_unit("e1", "left", "defense_1", "barracks")
	var spawned := s2.drain_events().filter(func(ev): return ev["kind"] == "spawned")
	assert_eq(spawned.size(), 1)
	assert_eq(spawned[0]["civilian"], false)
	assert_true(u != null)


# ---------------------------------------------------------------- wave classes

func test_defenses_wave_falls_through_to_civilians_then_core_and_never_back() -> void:
	var sim := _sim({"start_units": [{"actor": "e1", "count": 3, "point": "defense_1"}]})
	var u := _raider(sim, "defenses", Vector2(5.5, 5.5))
	u.stage = 1
	u.via = Vector2.ZERO
	_tick(sim, 5)
	assert_eq(u.class_now, "defenses", "defenders still stand at its point")
	var g := sim.get_entity(u.goal)
	assert_true(g != null and not g.civilian and g.side == 0 and g.group >= 0, "its goal is a defender of its point")
	assert_eq(u.order, "attack_move")
	for d in _defenders(sim):
		sim._kill(d, null)
	_tick(sim, 5)
	assert_eq(u.class_now, "civilians", "nothing left at its point: the village")
	g = sim.get_entity(u.goal)
	assert_true(g != null and g.civilian and g.alive, "its goal is now a civilian or a house")
	assert_eq(u.target_class, "defenses", "the authored class is kept")
	# a defender at another point does not pull it back
	sim.produce_group(0, [{"actor": "e1", "count": 1}], 90, 0)
	_tick(sim, 100)
	assert_true(sim.units_at(0) >= 1)
	assert_eq(u.class_now, "civilians", "never back to defenses")
	for c in _civs(sim):
		sim._kill(c, null)
	for h in _houses(sim):
		sim._kill(h, null)
	_tick(sim, 5)
	assert_eq(u.class_now, "core")
	assert_eq(u.goal, _barracks(sim).id)
	assert_eq(u.order_pos, _barracks(sim).center())
	_tick(sim, 5)
	assert_eq(u.class_now, "core", "and core is the end")


func test_defenses_class_ignores_other_points_defenders() -> void:
	var sim := _sim({"start_units": [{"actor": "e1", "count": 2, "point": "defense_2"}]})
	var u := _raider(sim, "defenses", Vector2(5.5, 5.5))  # via defense_1: nobody there
	u.stage = 1
	u.via = Vector2.ZERO
	_tick(sim, 5)
	assert_eq(u.class_now, "civilians", "its own approach is empty even though another point is held")


func test_wave_without_a_target_behaves_as_core() -> void:
	var sim := _sim({"start_units": START_ALL})
	var u := sim.spawn_wave_unit("e1", "left", "defense_1", "barracks")
	assert_eq([u.target_class, u.class_now], ["core", "core"])
	assert_eq(u.via_point, 0)
	assert_eq(u.objective, _barracks(sim).id)
	u.x = 30.5
	u.y = 20.5
	u.via = Vector2.ZERO
	u.stage = 0
	_tick(sim, 5)
	assert_eq([u.stage, u.goal, u.order], [1, _barracks(sim).id, "attack_move"], "straight on to the objective")
	assert_eq(u.order_pos, _barracks(sim).center())
	# and a bad class name is core too
	var v := sim.spawn_wave_unit("e1", "top", "defense_2", "barracks", "nonsense")
	assert_eq(v.class_now, "core")


# ---------------------------------------------------------------- rewards: squads and the active section

func test_squad_reward_makes_three_units_at_the_active_point() -> void:
	var sim := _sim({"units_per_point": 14})
	sim.active_point = 1
	var r := sim.schedule_reward("rifle_squad", 5)
	assert_eq([r["kind"], r["point"], r["count"], r["capacity"]], ["unit", 1, 3, false])
	assert_eq(sim.units_at(1), 3, "the pending squad already counts")
	var done: Array = []
	for ev in _tick(sim, 5 * 25):
		if ev["kind"] == "reward_done":
			done.append(ev)
	assert_eq(done.size(), 1)
	assert_eq([done[0]["result"], done[0]["actor"], done[0]["count"], done[0]["point"]], ["unit", "e1", 3, 1])
	var mine := _defenders(sim)
	assert_eq(mine.size(), 3)
	var gid: int = mine[0].group
	for u in mine:
		assert_eq(u.actor, "e1")
		assert_eq(u.group, gid, "one group")
		assert_eq(int(sim.groups[u.group]["point"]), 1)
	assert_eq(sim.units_at(1), 3)
	assert_eq(sim.stats["produced"][0]["infantry"], 3)
	var homes := {}
	for u in mine:
		homes[u.home] = true
	assert_eq(homes.size(), 3)


func test_squad_rewards_count_a_single_unit_reward_as_one() -> void:
	var sim := _sim()
	var r := sim.schedule_reward("e1", 5)
	assert_eq(r["count"], 1)
	assert_eq(sim.units_at(int(r["point"])), 1)
	var ev := _tick(sim, 5).filter(func(e): return e["kind"] == "reward_done")
	assert_eq([ev[0]["actor"], ev[0]["count"]], ["e1", 1])


func test_active_point_overrides_placement_and_falls_back_when_full() -> void:
	var sim := _sim({"units_per_point": 6, "sockets_per_point": 2})
	# buildings: the active point first while a socket is free
	sim.active_point = 2
	var pts := []
	for i in 3:
		pts.append(int(sim.schedule_reward("pillbox", 1, 0)["point"]))
	assert_eq(pts.slice(0, 2), [2, 2], "both sockets of the active point")
	assert_true(pts[2] != 2, "then the old rule: the approach with the fewest defenses")
	# units: squads of three fill the active point to six, the third squad goes elsewhere
	var sim2 := _sim({"units_per_point": 6})
	sim2.active_point = 2
	var squads := []
	for i in 3:
		squads.append(int(sim2.schedule_reward("rifle_squad", 1, 1)["point"]))
	assert_eq(squads.slice(0, 2), [2, 2])
	assert_true(squads[2] != 2, "a full section sends the squad elsewhere")
	assert_eq(sim2.units_at(2), 6)
	# a squad needs room for all three
	var sim3 := _sim({"units_per_point": 6})
	sim3.active_point = 0
	sim3.schedule_reward("e1", 1)
	sim3.schedule_reward("e1", 1)
	sim3.schedule_reward("e1", 1)
	sim3.schedule_reward("e1", 1)
	assert_eq(sim3.units_at(0), 4)
	var fall := sim3.schedule_reward("rifle_squad", 1, 0)
	assert_eq(fall["kind"], "unit")
	assert_true(int(fall["point"]) != 0, "four held plus three would be seven")
	# no active point: the old placement (fewest defenders, ties to the hint)
	var sim4 := _sim()
	assert_eq(sim4.active_point, -1)
	assert_eq(int(sim4.schedule_reward("rifle_squad", 1, 2)["point"]), 2)
	assert_eq(int(sim4.schedule_reward("rifle_squad", 1, 2)["point"]), 0)
	# everywhere full: a capacity repair
	var sim5 := _sim({"units_per_point": 3})
	for i in 3:
		sim5.schedule_reward("rifle_squad", 1)
	var last := sim5.schedule_reward("rifle_squad", 1)
	assert_true(last["capacity"] and last["kind"] == "repair")


func test_start_units_count_towards_the_unit_cap() -> void:
	var sim := _sim({"start_units": START_ALL, "units_per_point": 8})
	sim.active_point = 0
	assert_eq(int(sim.schedule_reward("rifle_squad", 1)["point"]), 0, "5 + 3 = 8 fits")
	assert_true(int(sim.schedule_reward("rifle_squad", 1)["point"]) != 0, "8 + 3 does not")


# ---------------------------------------------------------------- outcome

func test_barracks_death_is_defeat_and_the_village_alone_is_not() -> void:
	var sim := _sim()
	for c in _civs(sim):
		sim._kill(c, null)
	for h in _houses(sim):
		sim._kill(h, null)
	_tick(sim, 3)
	assert_eq(sim.outcome, "", "a razed village does not lose the level")
	assert_eq(sim.civilians_alive(), 0)
	var b := _barracks(sim)
	sim._damage(b, b.max_hp, null)
	sim.tick()
	assert_eq(sim.outcome, "defeat")
	assert_eq(sim.outcome_reason, "objective_destroyed:barracks")
	var sim2 := _sim({"objective_hp": {"barracks": 1234}})
	assert_eq(sim2.objective_hp("barracks"), 1234)
	sim2.end_by_song()
	assert_eq(sim2.outcome, "victory", "surviving the song is the win")


func test_count_alive_ignores_civilian_deaths() -> void:
	var sim := _sim({"start_units": START_ALL})
	var units := sim.count_alive(0, BattleSim.Kind.UNIT)
	var bld := sim.count_alive(0, BattleSim.Kind.BUILDING)
	sim._kill(_civs(sim)[0], null)
	sim._kill(_houses(sim)[0], null)
	assert_eq(sim.count_alive(0, BattleSim.Kind.UNIT), units)
	assert_eq(sim.count_alive(0, BattleSim.Kind.BUILDING), bld)
	assert_eq(sim.civilians_alive(), 3)
	sim._kill(_defenders(sim)[0], null)
	assert_eq(sim.count_alive(0, BattleSim.Kind.UNIT), units - 1)


# ---------------------------------------------------------------- Match

func _match(extra_waves: Array = []) -> Match:
	var level := Level.new()
	level.schema_version = 4
	level.mode = "defense"
	level.level_id = "village_test"
	level.title = "Village test"
	level.bpm = 174.0
	level.ticks_per_beat = 960
	level.duration_ticks = 2784 * 40
	level.seed = 3
	level.rules = {"start_units": START_ALL, "units_per_point": 14}
	level.waves = [
		{"id": "w1", "start_tick": 2784 * 10, "entry": "left", "via_defense_point": "defense_1", "target_objective": "barracks", "target": "civilians",
			"groups": [{"actor": "e1", "count": 2, "spawn_spacing_ticks": 100}, {"actor": "e1", "count": 1, "target": "core"}]},
		{"id": "w2", "start_tick": 2784 * 20, "entry": "right", "via_defense_point": "defense_3", "target_objective": "barracks",
			"groups": [{"actor": "e1", "count": 2}]},
	]
	_ensure_rewards()
	var m := Match.new()
	m.setup(level, _rules())
	return m


func _events_of(evs: Array, kind: String) -> Array:
	return evs.filter(func(e): return e["kind"] == kind)


func test_match_waves_carry_target_classes_and_warn_once_at_eight_seconds() -> void:
	var m := _match()
	assert_eq(m.upcoming_wave()["target"], "civilians")
	assert_eq(m.upcoming_wave()["entry"], "left")
	m.advance(1.9)
	assert_eq(_events_of(m.drain_events(), "wave_warning").size(), 0, "not yet")
	m.advance(2.2)
	var warn := _events_of(m.drain_events(), "wave_warning")
	assert_eq(warn.size(), 1)
	assert_eq([warn[0]["wave"], warn[0]["entry"]], ["w1", "left"])
	assert_near(float(warn[0]["in_s"]), 7.9, 0.15)
	m.advance(9.0)
	assert_eq(_events_of(m.drain_events(), "wave_warning").size(), 0, "once per wave")
	m.advance(10.5)
	var classes := []
	for e in m.sim.entities:
		if e.alive and e.side == 1:
			classes.append(e.target_class)
	classes.sort()
	assert_eq(classes, ["civilians", "civilians", "core"], "wave target with a group override")
	assert_eq(m.upcoming_wave()["target"], "core", "a wave without a target is core")
	m.advance(12.5)
	var w2 := _events_of(m.drain_events(), "wave_warning")
	assert_eq(w2.size(), 1)
	assert_eq(w2[0]["wave"], "w2")
	m.advance(21.0)
	for e in m.sim.entities:
		if e.alive and e.side == 1 and e.actor == "e1" and e.x > 60.0:
			assert_eq(e.target_class, "core")


func test_match_active_point_suggestion_and_section_event() -> void:
	var m := _match()
	assert_eq(m.suggest_point(), 0, "the next wave comes through defense_1")
	assert_false(m.set_active_point(7))
	assert_false(m.set_active_point(-2))
	assert_eq(m.sim.active_point, -1)
	assert_true(m.set_active_point(1))
	assert_eq(m.sim.active_point, 1)
	var sec := _events_of(m.drain_events(), "section")
	assert_eq(sec.size(), 1)
	assert_eq([sec[0]["point"], sec[0]["id"]], [1, "defense_2"])
	assert_true(m.set_active_point(1), "a second tap on it is still a tap")
	assert_eq(_events_of(m.drain_events(), "section").size(), 1)
	m.advance(15.0)  # w1 has spawned: the point most enemies walk towards
	assert_eq(m.suggest_point(), 0)
	m.advance(35.0)  # no wave left: the active section, else the emptiest
	assert_eq(m.suggest_point(), 1)
	m.set_active_point(-1)
	assert_true(m.suggest_point() >= 0)
	# a reward goes to the section that was tapped
	var m2 := _match()
	m2.set_active_point(2)
	var res := m2.sim.schedule_reward("rifle_squad", 100, m2.suggest_point())
	assert_eq(res["point"], 2)


func test_match_result_reports_villagers_and_the_primary_objective() -> void:
	var m := _match()
	m.advance(0.5)
	var r := m.result()
	assert_eq([r["villagers_total"], r["villagers_lost"], r["houses_total"], r["houses_lost"]], [4, 0, 4, 0])
	assert_eq(r["primary_objective"], "barracks")
	assert_eq(r["primary_objective_name"], "Barracks")
	assert_true(r["objective_hp"].has("barracks"))
	m.sim._kill(_civs(m.sim)[0], null)
	m.sim._kill(_houses(m.sim)[0], null)
	m.advance(1.0)
	r = m.result()
	assert_eq([r["villagers_lost"], r["houses_lost"]], [1, 1])
	assert_eq(m.wave_stats["w1"]["killed"], 0, "village losses are not wave kills")


# ---------------------------------------------------------------- units fight what they meet on the way home

## Ticks until a reward unit exists and returns it (null when none shows up within `max_ticks`).
func _first_reward_unit(sim: BattleSim, max_ticks: int) -> BattleSim.Ent:
	for i in max_ticks:
		_tick(sim, 1)
		var mine := _defenders(sim)
		if not mine.is_empty():
			return mine[0]
	return null


func test_reward_unit_fights_an_enemy_it_meets_on_the_way_to_its_point() -> void:
	var sim := _sim()
	var r := sim.schedule_reward("e1", 1, 0)
	assert_eq(r["point"], 0)
	var u := _first_reward_unit(sim, 200)
	assert_true(u != null, "the reward unit leaves the barracks")
	if u == null:
		return
	assert_eq(u.order, "attack_move", "reward units fight on the way")
	assert_true(u.center().distance_to(u.home) > u.leash, "it starts beyond its leash")
	# a stationary, harmless-to-order enemy rifleman about 3 cells off the straight path to the point
	var dir := (u.home - u.center()).normalized()
	var mid := u.center() + dir * (u.center().distance_to(u.home) * 0.5)
	var foe := _raider(sim, "core", mid + Vector2(-dir.y, dir.x) * 3.0)
	foe.order = "hold"  # neither DefenseAi nor the move code takes it away
	u.hp = u.max_hp * 20  # the fight is about the walk, not about who wins it
	var start_hp := foe.hp
	var shot := false
	var closest := INF
	for i in 25 * 60:
		_tick(sim, 1)
		if foe.alive and foe.hp < start_hp:
			shot = true
		closest = minf(closest, u.center().distance_to(u.home))
		if shot and u.center().distance_to(u.home) <= DefenseAi.HOME_TOLERANCE:
			break
	assert_true(shot or not foe.alive, "the unit fired at the enemy it passed")
	assert_true(u.alive)
	assert_true(u.center().distance_to(u.home) <= DefenseAi.HOME_TOLERANCE, "and still arrived at its point (%f)" % u.center().distance_to(u.home))


func test_defender_beyond_the_leash_walks_home_without_chasing_a_target_out_of_range() -> void:
	var sim := _sim({"start_units": START_ALL})
	var u: BattleSim.Ent = _defenders(sim)[0]
	# 10 cells from home (beyond the 6-cell leash) with an enemy 9 cells further out, beyond a rifle's reach
	var away := Vector2(0, 1)
	u.x = u.home.x + away.x * 10.0
	u.y = u.home.y + away.y * 10.0
	var foe := _raider(sim, "core", u.center() + away * 9.0)
	foe.order = "hold"
	foe.speed = 0.0
	u.target = foe.id
	u.order = "attack_move"
	u.order_pos = u.home
	assert_true(sim.range_to(u, foe) > sim.max_range_vs(u, foe), "the target is out of weapon range")
	var worst := u.center().distance_to(u.home)
	for i in 25 * 20:
		_tick(sim, 1)
		var d := u.center().distance_to(u.home)
		assert_true(d <= worst + 0.02, "the distance to home never grows (%f > %f at tick %d)" % [d, worst, i])
		worst = minf(worst, d)
		if d <= DefenseAi.HOME_TOLERANCE:
			break
	assert_true(u.center().distance_to(u.home) <= 6.0, "it came back inside the leash")
