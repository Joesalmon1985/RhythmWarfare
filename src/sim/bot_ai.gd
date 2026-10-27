class_name BotAi
extends RefCounted
## OpenRA's "Rush AI" SquadManagerBotModule and squad state machines (docs/OPENRA_BEHAVIOUR_SPEC.md sections 1
## and 2), ported for one side. Production is not its job (the music does that); it gathers the units it is given,
## forms attack squads, rushes, protects the base and runs the air squad. Deviations from commit e7e9e4ad are
## noted inline: the fuzzy attack-or-flee comparison is the crisp approximation from the spec, and the air
## squad's approach-safety test uses the intended semantics (the source has the comparison inverted).

# Rush AI uses SquadSize 20 + Random(30), paced for a half-hour match. An 88-second song needs waves every few
# seconds, so the squad threshold is scaled down to 10 + Random(10); everything else keeps the engine's values.
const SQUAD_SIZE := 10
const SQUAD_SIZE_RANDOM_BONUS := 10
const ASSIGN_ROLES_INTERVAL := 50
const RUSH_INTERVAL := 600
const ATTACK_FORCE_INTERVAL := 75
const MINIMUM_ATTACK_FORCE_DELAY := 0
const RUSH_ATTACK_SCAN_RADIUS := 15.0
const PROTECT_UNIT_SCAN_RADIUS := 15.0
const IDLE_SCAN_RADIUS := 10.0
const DANGER_SCAN_RADIUS := 10.0
const ATTACK_SCAN_RADIUS := 12.0
const PROTECTION_SCAN_RADIUS := 8.0
const STUCK_TICKS := 63
const RESPOND_COOLDOWN := 30
const MISSILE_UNIT_MULTIPLIER := 3
const PROTECTION_TYPES := ["main", "factory", "barracks", "power", "dome", "depot", "pad", "turret", "pillbox", "sam"]

class Squad:
	var id := 0
	var type := "assault"  # assault | rush | protection | air
	var units: Array[int] = []
	var state := "idle"
	var target := -1
	var target_pos := Vector2.ZERO
	var leader := -1
	var last_leader_cell := Vector2i(-99, -99)
	var last_target := -1
	var last_updated := 0
	var backoff := 4
	var lattice_index := 0

var sim: BattleSim
var side := 0
var rng := RandomNumberGenerator.new()
var squads: Array[Squad] = []
var idle_pool: Array[int] = []
var active: Dictionary = {}  # unit id -> true
var _next_squad := 1
var _rush_ticks := 0
var _assign_ticks := 0
var _attack_force_ticks := 0
var _min_attack_delay := 0
var _respond_cooldown := 0
var _protect_from := -1
var _lattice: Array = []


func setup(p_sim: BattleSim, p_side: int, p_seed: int) -> void:
	sim = p_sim
	side = p_side
	rng.seed = p_seed
	_rush_ticks = rng.randi_range(RUSH_INTERVAL - RUSH_INTERVAL / 20, RUSH_INTERVAL + RUSH_INTERVAL / 20)
	_assign_ticks = rng.randi_range(0, ASSIGN_ROLES_INTERVAL)
	_attack_force_ticks = rng.randi_range(0, ATTACK_FORCE_INTERVAL)
	_min_attack_delay = 0
	_respond_cooldown = RESPOND_COOLDOWN
	# AirIdleState lattice: a shuffled grid of probe points 10 cells apart over the map
	var cols := int(ceil(float(sim.width) / DANGER_SCAN_RADIUS))
	var rows := int(ceil(float(sim.height) / DANGER_SCAN_RADIUS))
	for i in cols * rows:
		_lattice.append(i)
	for i in range(_lattice.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp = _lattice[i]
		_lattice[i] = _lattice[j]
		_lattice[j] = tmp


func _unit(id: int) -> BattleSim.Ent:
	var e: BattleSim.Ent = sim.get_entity(id)
	return e if e != null and e.alive and e.side == side else null


func _is_ground_unit(e: BattleSim.Ent) -> bool:
	return e.kind == BattleSim.Kind.UNIT


## ModularBot forwards every damage event on our actors; the manager arms one protection response at a time.
func respond_to_attack(attacker_id: int) -> void:
	if _respond_cooldown > 0:
		return
	var attacker: BattleSim.Ent = sim.get_entity(attacker_id)
	if attacker == null or not attacker.alive or attacker.side == side or attacker.airborne():
		return
	_respond_cooldown = RESPOND_COOLDOWN
	_protect_from = attacker_id


func tick() -> void:
	var now := sim.tick_count
	for s in squads:
		var keep: Array[int] = []
		for id in s.units:
			if _unit(id) != null:
				keep.append(id)
		s.units = keep
	squads = squads.filter(func(s: Squad) -> bool: return not s.units.is_empty())
	var pool: Array[int] = []
	for id in idle_pool:
		if _unit(id) != null:
			pool.append(id)
	idle_pool = pool
	_rush_ticks -= 1
	if _rush_ticks <= 0:
		_rush_ticks = RUSH_INTERVAL
		_try_rush()
	# squad updates are spread across the interval: each squad ticks once per ATTACK_FORCE_INTERVAL
	for s in squads:
		if (now + s.id * 7) % ATTACK_FORCE_INTERVAL == 0:
			_update_squad(s)
	_assign_ticks -= 1
	if _assign_ticks <= 0:
		_assign_ticks = ASSIGN_ROLES_INTERVAL
		_find_new_units()
	_min_attack_delay -= 1
	if _min_attack_delay <= 0:
		_min_attack_delay = MINIMUM_ATTACK_FORCE_DELAY
		_create_attack_force()
	if _respond_cooldown == RESPOND_COOLDOWN and _protect_from >= 0:
		_protect_own(_protect_from)
		_protect_from = -1
	if _respond_cooldown > 0:
		_respond_cooldown -= 1


func _find_new_units() -> void:
	for e in sim.entities:
		if not e.alive or e.side != side or e.kind != BattleSim.Kind.UNIT or active.has(e.id):
			continue
		active[e.id] = true
		idle_pool.append(e.id)


func _create_attack_force() -> void:
	var n := SQUAD_SIZE + rng.randi_range(0, SQUAD_SIZE_RANDOM_BONUS - 1)
	if idle_pool.size() >= n:
		var s := _new_squad("assault")
		s.units = idle_pool.duplicate()
		idle_pool.clear()
		for id in s.units:
			var e := _unit(id)
			if e != null:
				e.squad = s.id
		sim.stats["squads"][side] += 1


func _new_squad(type: String) -> Squad:
	var s := Squad.new()
	s.id = _next_squad
	_next_squad += 1
	s.type = type
	s.last_updated = sim.tick_count
	squads.append(s)
	return s


# ---------------------------------------------------------------- helpers (spec 1.2)

## Enemies a given unit could attack: alive, other side, not a husk, not airborne (IgnoredEnemyTargetTypes), has a
## valid weapon against them, and not a wall (deviation per spec flag 10).
func _find_enemies(candidates: Array, source: BattleSim.Ent) -> Array:
	var out := []
	for o in candidates:
		if o == null or not o.alive or o.side == side or o.airborne() or o.is_wall:
			continue
		if source != null and not sim.can_hit(source, o):
			continue
		out.append(o)
	return out


func _enemies_in_circle(centre: Vector2, radius: float, source: BattleSim.Ent) -> Array:
	var near := []
	for o in sim.entities:
		if o.alive and o.side != side and o.center().distance_to(centre) <= radius:
			near.append(o)
	return _find_enemies(near, source)


func _closest_enemy(source: BattleSim.Ent, radius: float = INF) -> BattleSim.Ent:
	var best: BattleSim.Ent = null
	var best_d := INF
	for o in _find_enemies(sim.entities, source):
		var d := source.center().distance_to(o.center())
		if d <= radius and d < best_d:
			best = o
			best_d = d
	return best


## Deviation from the closest-enemy rule (spec 1.4): assault and rush squads are sent at the enemy construction
## yard, the way TryToRushAttack does, fighting whatever they meet within AttackScanRadius on the way. With
## continuous music-driven production a "closest enemy" is always being spawned next to the enemy wall, so the
## engine rule never let a winning army walk the last ten cells.
func _attack_objective(source: BattleSim.Ent) -> BattleSim.Ent:
	var cy: BattleSim.Ent = sim.main_base(1 - side)
	if cy != null and cy.alive and source != null and sim.can_hit(source, cy):
		return cy
	return _closest_enemy(source)


func _squad_centre(s: Squad) -> Vector2:
	var sum := Vector2.ZERO
	var n := 0
	for id in s.units:
		var e := _unit(id)
		if e != null:
			sum += e.center()
			n += 1
	return sum / n if n > 0 else Vector2.ZERO


func _elect_leader(s: Squad) -> BattleSim.Ent:
	var c := _squad_centre(s)
	var best: BattleSim.Ent = null
	var best_d := INF
	for id in s.units:
		var e := _unit(id)
		if e != null and e.center().distance_to(c) < best_d:
			best = e
			best_d = e.center().distance_to(c)
	s.leader = best.id if best != null else -1
	return best


func _leader(s: Squad) -> BattleSim.Ent:
	var e := _unit(s.leader)
	return e if e != null else _elect_leader(s)


func _target_valid(s: Squad, unit: BattleSim.Ent) -> bool:
	var t: BattleSim.Ent = sim.get_entity(s.target)
	if t == null or not t.alive or t.side == side or t.airborne():
		return false
	return unit != null and sim.can_hit(unit, t)


func _set_target(s: Squad, t: BattleSim.Ent) -> void:
	s.target = t.id if t != null else -1
	if t != null:
		s.target_pos = t.center()


func _random_own_building() -> Vector2:
	var own := []
	for e in sim.entities:
		if e.alive and e.side == side and e.kind == BattleSim.Kind.BUILDING and not e.is_wall:
			own.append(e)
	if own.is_empty():
		return sim.mirrored(Vector2(5.0, sim.height * 0.5), side)
	var b: BattleSim.Ent = own[rng.randi_range(0, own.size() - 1)]
	return b.center()


func _order_attack_move(ids: Array, pos: Vector2) -> void:
	for id in ids:
		var e := _unit(id)
		if e == null:
			continue
		e.order = "attack_move"
		e.order_pos = pos
		e.resume_attack_move = true
		if e.target < 0:
			e.path = PackedVector2Array()


func _order_move(ids: Array, pos: Vector2) -> void:
	for id in ids:
		var e := _unit(id)
		if e == null:
			continue
		e.order = "move"
		e.order_pos = pos
		e.order_target = -1
		e.target = -1
		e.resume_attack_move = false
		e.path = PackedVector2Array()


func _order_stop(id: int) -> void:
	var e := _unit(id)
	if e != null:
		e.order = "idle"
		e.path = PackedVector2Array()


func _busy_attack(e: BattleSim.Ent) -> bool:
	return e.target >= 0 and e.role == "infantry"  # BusyAttack only recognises the infantry Attack activity


## Crisp approximation of AttackOrFleeFuzzy.Default (spec 1.6).
func _can_attack(own: Array, enemies: Array, rush: bool) -> bool:
	if own.is_empty():
		return false
	var own_hp := _health_pct(own)
	var enemy_hp := _health_pct(enemies)
	var power := _relative_power(own, enemies)
	var speed := _relative_speed(own, enemies)
	if rush and own_hp >= 70:
		return power > 112
	if own_hp >= 70:
		return true
	if own_hp > 40:
		if enemy_hp < 30:
			return true
		if power >= 95:
			return true
		if speed <= 80:
			return true
		return false
	return enemy_hp < 60 and power >= 95 and speed <= 105


static func _health_pct(actors: Array) -> int:
	var hp := 0
	var max_hp := 0
	for e in actors:
		hp += e.hp
		max_hp += e.max_hp
	return 100 if max_hp == 0 else hp * 100 / max_hp


static func _relative_power(own: Array, enemies: Array) -> int:
	var a := 0
	var b := 0
	for e in own:
		a += BattleSim.attack_power(e)
	for e in enemies:
		b += BattleSim.attack_power(e)
	if enemies.is_empty() or b == 0:
		return 999
	if a == 0:
		return 0
	return clampi(a * 100 / b, 0, 999)


static func _relative_speed(own: Array, enemies: Array) -> int:
	var a := 0.0
	var na := 0
	var b := 0.0
	var nb := 0
	for e in own:
		if e.is_mobile():
			a += e.speed
			na += 1
	for e in enemies:
		if e.is_mobile():
			b += e.speed
			nb += 1
	if na == 0:
		return 0
	if nb == 0 or b == 0.0:
		return 999
	return clampi(int((a / na) / (b / nb) * 100.0), 0, 999)


func _units_of(s: Squad) -> Array:
	var out := []
	for id in s.units:
		var e := _unit(id)
		if e != null:
			out.append(e)
	return out


## StateBase.ShouldFlee: around the squad centre, never flee near an own building; otherwise ask the comparison.
## Deviation: the own side of the comparison is every friendly ground unit inside the danger circle, not only this
## squad, so several squads fighting side by side do not each conclude they are outnumbered and leave piecemeal.
func _should_flee(s: Squad, own: Array, rush: bool) -> bool:
	var c := _squad_centre(s)
	for e in sim.entities:
		if e.alive and e.side == side and e.kind == BattleSim.Kind.BUILDING and not e.is_wall and e.center().distance_to(c) <= DANGER_SCAN_RADIUS:
			return false
	var enemies := []
	var friends := []
	for o in sim.entities:
		if not o.alive or o.airborne() or o.center().distance_to(c) > DANGER_SCAN_RADIUS:
			continue
		if o.side != side and not o.weapons.is_empty():
			enemies.append(o)
		elif o.side == side and o.kind == BattleSim.Kind.UNIT:
			friends.append(o)
	if enemies.is_empty():
		return false
	return not _can_attack(friends if friends.size() > own.size() else own, enemies, rush)


# ---------------------------------------------------------------- ground squads (spec 1.4, 1.5)

func _update_squad(s: Squad) -> void:
	match s.type:
		"air":
			_update_air(s)
		"protection":
			_update_protection(s)
		_:
			_update_ground(s)


func _stuck_check(s: Squad, leader: BattleSim.Ent) -> bool:
	var now := sim.tick_count
	if leader.cell() != s.last_leader_cell:
		s.last_leader_cell = leader.cell()
		s.last_updated = now
	if s.target != s.last_target:
		s.last_target = s.target
		s.last_updated = now
	return now > s.last_updated + STUCK_TICKS


func _update_ground(s: Squad) -> void:
	var own := _units_of(s)
	if own.is_empty():
		return
	var rush := s.type == "rush"
	match s.state:
		"idle":
			var leader := _elect_leader(s)
			var t := _attack_objective(leader)
			_set_target(s, t)
			if t == null:
				return
			var enemies := _enemies_in_circle(s.target_pos, IDLE_SCAN_RADIUS, leader)
			if enemies.is_empty() or _can_attack(own, enemies, rush):
				_order_attack_move(s.units, s.target_pos)
				s.state = "attack_move"
				s.last_updated = sim.tick_count
			else:
				_flee(s)
		"attack_move":
			var leader := _leader(s)
			if not _target_valid(s, leader):
				leader = _elect_leader(s)
				var t := _attack_objective(leader)
				_set_target(s, t)
				if t == null:
					_flee(s)
					return
			if _stuck_check(s, leader):
				s.state = "idle"
				return
			var radius := float(own.size()) / 3.0
			var stragglers := []
			for e in own:
				if e.id != leader.id and e.center().distance_to(leader.center()) > radius:
					stragglers.append(e.id)
			if not stragglers.is_empty():
				_order_stop(leader.id)
				_order_attack_move(stragglers, leader.center())
			else:
				var t := _closest_enemy(leader, ATTACK_SCAN_RADIUS)
				if t != null:
					_set_target(s, t)
					s.state = "attack"
				else:
					_order_attack_move(s.units, s.target_pos)
			if _should_flee(s, own, rush):
				_flee(s)
		"attack":
			var leader := _leader(s)
			if not _target_valid(s, leader):
				# the fight is over: carry on towards the objective instead of hunting the next closest unit
				leader = _elect_leader(s)
				var t := _attack_objective(leader)
				_set_target(s, t)
				if t == null:
					_flee(s)
					return
				_order_attack_move(s.units, s.target_pos)
				s.state = "attack_move"
				return
			if _stuck_check(s, leader):
				s.state = "idle"
				return
			var t: BattleSim.Ent = sim.get_entity(s.target)
			s.target_pos = t.center()
			# GroundUnitsAttackState orders an AttackMove towards the target for every unit not already fighting
			var free := []
			for e in own:
				if not _busy_attack(e):
					free.append(e.id)
			_order_attack_move(free, s.target_pos)
			if _should_flee(s, own, rush):
				_flee(s)


## GroundUnitsFleeState: everyone walks to a random own building and the squad dissolves back into the idle pool.
func _flee(s: Squad) -> void:
	_order_move(s.units, _random_own_building())
	sim.stats["flees"][side] += 1
	for id in s.units:
		active.erase(id)
		var e := _unit(id)
		if e != null:
			e.squad = -1
	s.units.clear()


func _update_protection(s: Squad) -> void:
	var own := _units_of(s)
	if own.is_empty():
		return
	var leader := _leader(s)
	if not _target_valid(s, leader):
		var t := _closest_enemy(leader, PROTECTION_SCAN_RADIUS)
		_set_target(s, t)
		if t == null:
			_flee(s)
			return
	var t: BattleSim.Ent = sim.get_entity(s.target)
	s.target_pos = t.center()
	_order_attack_move(s.units, s.target_pos)


# ---------------------------------------------------------------- rush and protection (spec 1.3)

func _try_rush() -> void:
	var ground_troops := idle_pool.size()
	for s in squads:
		if s.type != "air":
			ground_troops += s.units.size()
	if ground_troops < SQUAD_SIZE or idle_pool.is_empty():
		return
	var probe := _unit(idle_pool[rng.randi_range(0, idle_pool.size() - 1)])
	if probe == null:
		return
	var enemy_cy: BattleSim.Ent = sim.main_base(1 - side)
	if enemy_cy == null or not enemy_cy.alive:
		return
	var defenders := []
	for o in _enemies_in_circle(enemy_cy.center(), RUSH_ATTACK_SCAN_RADIUS, probe):
		if not o.weapons.is_empty() and o.kind != BattleSim.Kind.AIRCRAFT:
			defenders.append(o)
	var idle_units := []
	for id in idle_pool:
		var e := _unit(id)
		if e != null:
			idle_units.append(e)
	if not _can_attack(idle_units, defenders, true):
		return
	var target: BattleSim.Ent = enemy_cy if defenders.is_empty() else defenders[rng.randi_range(0, defenders.size() - 1)]
	for s in squads:
		_set_target(s, target)
	var rush: Squad = null
	for s in squads:
		if s.type == "rush":
			rush = s
	if rush == null:
		rush = _new_squad("rush")
		_set_target(rush, target)
	for id in idle_pool:
		rush.units.append(id)
		var e := _unit(id)
		if e != null:
			e.squad = rush.id
	idle_pool.clear()
	sim.stats["rushes"][side] += 1


func _protect_own(attacker_id: int) -> void:
	var attacker: BattleSim.Ent = sim.get_entity(attacker_id)
	if attacker == null or not attacker.alive or attacker.side == side or attacker.airborne():
		return
	for s in squads:
		if s.units.is_empty():
			continue
		var first := _unit(s.units[0])
		if first != null and sim.can_hit(first, attacker) and first.center().distance_to(attacker.center()) <= PROTECT_UNIT_SCAN_RADIUS:
			_set_target(s, attacker)
	var protect: Squad = null
	for s in squads:
		if s.type == "protection":
			protect = s
	if protect == null:
		protect = _new_squad("protection")
		protect.state = "attack"
		_set_target(protect, attacker)
	var remaining: Array[int] = []
	for id in idle_pool:
		var e := _unit(id)
		if e != null and sim.can_hit(e, attacker):
			protect.units.append(id)
			e.squad = protect.id
		else:
			remaining.append(id)
	idle_pool = remaining
	if not protect.units.is_empty() and not _target_valid(protect, _unit(protect.units[0])):
		_set_target(protect, attacker)


# ---------------------------------------------------------------- air squad (spec 2)

func _air_squad() -> Squad:
	for s in squads:
		if s.type == "air":
			return s
	var s := _new_squad("air")
	return s


## Called by the simulation when an aircraft takes off: it joins the air squad.
func on_launch(id: int) -> void:
	var s := _air_squad()
	if not s.units.has(id):
		s.units.append(id)


func _airborne_units(s: Squad) -> Array:
	var out := []
	for id in s.units:
		var a := _unit(id)
		if a != null and a.air == BattleSim.Air.SORTIE:
			out.append(a)
	return out


func _count_anti_air(actors: Array) -> int:
	var n := 0
	for o in actors:
		if o.kind == BattleSim.Kind.AIRCRAFT or o.weapons.is_empty():
			continue
		for w in o.weapons:
			if "AirborneActor" in w["def"].get("valid_targets", []):
				n += 1
				break
	return n


func _enemies_near(pos: Vector2, radius: float) -> Array:
	var out := []
	for o in sim.entities:
		if o.alive and o.side != side and not o.airborne() and not o.is_wall and o.center().distance_to(pos) <= radius:
			out.append(o)
	return out


## NearToPosSafely: true (and a random enemy there) when the AA count times three is below our squad size.
func _near_to_pos_safely(count: int, pos: Vector2) -> Dictionary:
	var near := _enemies_near(pos, DANGER_SCAN_RADIUS)
	if near.is_empty():
		return {"safe": true, "enemy": null}
	if _count_anti_air(near) * MISSILE_UNIT_MULTIPLIER < count:
		return {"safe": true, "enemy": near[rng.randi_range(0, near.size() - 1)]}
	return {"safe": false, "enemy": null}


func _air_should_flee(s: Squad, units: Array) -> bool:
	var c := _squad_centre(s)
	for e in sim.entities:
		if e.alive and e.side == side and e.kind == BattleSim.Kind.BUILDING and not e.is_wall and e.center().distance_to(c) <= DANGER_SCAN_RADIUS:
			return false
	var enemies := _enemies_near(c, DANGER_SCAN_RADIUS)
	return _count_anti_air(enemies) * MISSILE_UNIT_MULTIPLIER > units.size()


func _find_defenseless_target(s: Squad, units: Array) -> BattleSim.Ent:
	if _lattice.is_empty():
		return null
	var cols := int(ceil(float(sim.width) / DANGER_SCAN_RADIUS))
	var centre := _squad_centre(s)
	for attempt in 3:
		var idx: int = _lattice[s.lattice_index % _lattice.size()]
		s.lattice_index = (s.lattice_index + 1) % _lattice.size()
		var pos := Vector2((idx % cols) * DANGER_SCAN_RADIUS + DANGER_SCAN_RADIUS * 0.5, (idx / cols) * DANGER_SCAN_RADIUS + DANGER_SCAN_RADIUS * 0.5)
		# approach line check (intended semantics: skip when the path carries too much anti-air)
		var on_line := []
		for o in sim.entities:
			if o.alive and o.side != side and not o.airborne() and _dist_to_segment(o.center(), centre, pos) <= 5.0:
				on_line.append(o)
		if _count_anti_air(on_line) * MISSILE_UNIT_MULTIPLIER >= units.size():
			continue
		var probe := _near_to_pos_safely(units.size(), pos)
		if probe["safe"] and probe["enemy"] != null:
			s.lattice_index = rng.randi_range(0, _lattice.size() - 1)
			return probe["enemy"]
	return null


static func _dist_to_segment(p: Vector2, a: Vector2, b: Vector2) -> float:
	var ab := b - a
	var len2 := ab.length_squared()
	if len2 <= 0.0001:
		return p.distance_to(a)
	var t := clampf((p - a).dot(ab) / len2, 0.0, 1.0)
	return p.distance_to(a + ab * t)


func _update_air(s: Squad) -> void:
	var units := _airborne_units(s)
	if units.is_empty():
		return
	match s.state:
		"idle":
			if _air_should_flee(s, units):
				s.state = "flee"
				_update_air(s)
				return
			var e := _find_defenseless_target(s, units)
			if e == null:
				return
			_set_target(s, e)
			s.state = "attack"
		"attack":
			var leader := _unit(units[0].id)
			if not _target_valid(s, leader):
				var t := _closest_enemy(leader)
				_set_target(s, t)
				if t == null:
					s.state = "flee"
					_update_air(s)
					return
			var t: BattleSim.Ent = sim.get_entity(s.target)
			var closest: BattleSim.Ent = units[0]
			for a in units:
				if a.center().distance_to(t.center()) < closest.center().distance_to(t.center()):
					closest = a
			if not _near_to_pos_safely(units.size(), closest.center())["safe"]:
				s.state = "flee"
				_update_air(s)
				return
			for a in units:
				if a.ammo <= 0:
					continue
				if sim.can_hit(a, t):
					a.order = "attack"
					a.order_target = t.id
		"flee":
			for a in units:
				a.order = "move"
				a.order_pos = _random_own_building()
				a.order_target = -1
			s.state = "idle"
