class_name DefenseAi
extends RefCounted
## Order logic for the one-sided defense (missions). Side 0 groups hold their defense point: they stand there,
## fight what comes within weapon range, and when a fight drags them past the leash they drop it and walk home
## (the limited pursuit). Side 1 wave units attack-move via their defense point and then to their objective,
## fighting what they meet on the way. The duel's Rush AI (bot_ai.gd) is not involved.
##
## Missions with a village add two things. A wave unit carries a target class: "defenses" goes for the defenders and
## defences of its via point, "civilians" for the village, "core" (the default, the original behaviour) for its
## objective; a class with nothing left falls through to the next (defenses, civilians, core) and never back.
## Civilians (side 0, `civilian`) wander between village spots and run from enemies that come within the flee radius.

const THINK_EVERY := 5  # ticks between order checks
const HOME_TOLERANCE := 1.6
const VIA_REACHED := 3.0  # a crowd around the via point never gets within a cell of its centre
const SORTIE_CELLS := 16.0  # how far from home defenders go after an enemy shelling their point from beyond the leash

var sim: BattleSim
var _defense_left: Array = []  # per defense point: living defenders (group units and defences on its sockets)
var _civ_left := 0             # living civilians (units and houses)
var _enemies: Array = []       # living side-1 units this think


func setup(p_sim: BattleSim) -> void:
	sim = p_sim


func tick() -> void:
	if sim.tick_count % THINK_EVERY != 0:
		return
	_refresh_counts()
	for e in sim.entities:
		if not e.alive or e.kind != BattleSim.Kind.UNIT:
			continue
		if e.side == 0:
			if e.civilian:
				_civilian(e)
			elif e.group >= 0:
				_defender(e)
		elif e.side == 1:
			_attacker(e)


## Counts used by this think's orders: defenders per point, civilians left, the enemies on the field.
func _refresh_counts() -> void:
	_defense_left.resize(sim.defense_points.size())
	_defense_left.fill(0)
	_civ_left = 0
	_enemies.clear()
	for e in sim.entities:
		if not e.alive:
			continue
		if e.side == 1:
			if e.kind == BattleSim.Kind.UNIT:
				_enemies.append(e)
		elif e.civilian:
			_civ_left += 1
		else:
			var pt := _defense_point_of(e)
			if pt >= 0:
				_defense_left[pt] += 1


## The defense point a side-0 defender (a group unit or a defence on a socket) belongs to, -1 for anything else.
func _defense_point_of(o: BattleSim.Ent) -> int:
	if o.side != 0 or o.civilian or not o.alive:
		return -1
	if o.kind == BattleSim.Kind.UNIT:
		if o.group >= 0 and sim.groups.has(o.group):
			return int(sim.groups[o.group]["point"])
	elif o.kind == BattleSim.Kind.BUILDING:
		if o.is_defence and o.socket >= 0 and o.socket < sim.sockets.size():
			return int(sim.sockets[o.socket]["point"])
	return -1


func _defender(e: BattleSim.Ent) -> void:
	var d := e.center().distance_to(e.home)
	var t: BattleSim.Ent = sim.get_entity(e.target)
	if t != null and t.alive and d <= SORTIE_CELLS and _shelling(t, e):
		return  # a sortie: keep after it
	if e.target < 0 and (e.order == "idle" or e.order == "move"):
		var s := _shelling_enemy(e)
		if s != null:
			e.order = "attack"
			e.order_target = s.id
			e.target = s.id
			e.resume_attack_move = false
			return
	if d > e.leash:
		# pursuit limit: forget the target and go back (a unit on a move order does not auto-target)
		e.target = -1
		e.order = "move"
		e.order_pos = e.home
		e.resume_attack_move = false
		return
	if e.order == "idle" and e.target < 0 and d > HOME_TOLERANCE:
		e.order = "move"
		e.order_pos = e.home


## Whether enemy `o` is hitting something of ours near `e`'s home while standing beyond the leash (artillery and
## rocket launchers outrange the defenses; without this the defenders would watch them shell the point all game).
func _shelling(o: BattleSim.Ent, e: BattleSim.Ent) -> bool:
	if o.side != 1 or o.kind != BattleSim.Kind.UNIT:
		return false
	var v: BattleSim.Ent = sim.get_entity(o.target)
	if v == null or not v.alive or v.side != 0 or v.center().distance_to(e.home) > e.leash:
		return false
	var od := o.center().distance_to(e.home)
	return od > e.leash and od <= SORTIE_CELLS


## The first (entity order, deterministic) enemy shelling this defender's point, or null.
func _shelling_enemy(e: BattleSim.Ent) -> BattleSim.Ent:
	for o in sim.entities:
		if o.alive and _shelling(o, e):
			return o
	return null


func _attacker(e: BattleSim.Ent) -> void:
	if e.order != "idle" and e.order != "attack_move":
		return
	_advance_class(e)
	if e.stage == 0:
		if e.via == Vector2.ZERO or e.center().distance_to(e.via) <= VIA_REACHED:
			e.stage = 1
			_head_for_goal(e, true)
		elif e.order == "idle":
			e.order = "attack_move"
			e.order_pos = e.via
		return
	_head_for_goal(e, false)


## The class in force only ever falls through: defenses -> civilians -> core, when nothing of the class is left on the
## unit's approach (defenses: at its via point; civilians: anywhere).
func _advance_class(e: BattleSim.Ent) -> void:
	if e.class_now == "defenses":
		var left := 0
		if e.via_point >= 0 and e.via_point < _defense_left.size():
			left = int(_defense_left[e.via_point])
		else:
			for n in _defense_left:
				left += int(n)
		if left == 0:
			e.class_now = "civilians"
	if e.class_now == "civilians" and _civ_left == 0:
		e.class_now = "core"


## Stage 1: attack-move to the goal of the class in force. The goal is picked again only when it died or the unit
## stands idle (or `force` at the moment it leaves the via point).
func _head_for_goal(e: BattleSim.Ent, force: bool) -> void:
	var g: BattleSim.Ent = sim.get_entity(e.goal)
	if g == null or not g.alive or e.order == "idle":
		g = _pick_goal(e)
		e.goal = g.id if g != null else -1
		force = true
	if g == null or not force:
		return
	e.order = "attack_move"
	e.order_pos = g.center()


## The nearest live thing of the class in force: a defender or defence of the via point, a civilian (unit or house), or
## the objective.
func _pick_goal(e: BattleSim.Ent) -> BattleSim.Ent:
	if e.class_now == "core":
		var obj: BattleSim.Ent = sim.get_entity(e.objective)
		return obj if obj != null and obj.alive else null
	var best: BattleSim.Ent = null
	var best_d := INF
	for o in sim.entities:
		if not o.alive or o.side != 0:
			continue
		if e.class_now == "civilians":
			if not o.civilian:
				continue
		else:
			var pt := _defense_point_of(o)
			if pt < 0 or (e.via_point >= 0 and pt != e.via_point):
				continue
		var d := e.center().distance_squared_to(o.center())
		if d < best_d:
			best_d = d
			best = o
	return best


# ---------------------------------------------------------------- civilians

## Wander and flee. A civilian walks between village spots near its home at 60 % speed, resting 40 to 150 ticks in
## between; an enemy unit within the flee radius sends it running (full speed) to the spot farthest from that enemy,
## and it calms down a few checks after the last threat has gone.
func _civilian(e: BattleSim.Ent) -> void:
	var threat := _nearest_threat(e)
	if threat != null:
		e.civ_calm = 0
		if e.civ_state != "flee" or e.order == "idle" or e.order_pos.distance_to(threat.center()) <= sim.flee_radius:
			e.order = "move"
			e.order_pos = _flee_spot(e, threat.center())
		e.civ_state = "flee"
		e.speed = e.civ_speed
		return
	if e.civ_state == "flee":
		e.civ_calm += 1
		if e.civ_calm >= 3:
			e.civ_state = "wander"
			e.speed = e.civ_speed * 0.6
			e.civ_rest = sim.civ_rng.randi_range(40, 150)
		return
	if e.order != "idle":
		return
	e.civ_rest -= THINK_EVERY
	if e.civ_rest > 0:
		return
	e.civ_rest = sim.civ_rng.randi_range(40, 150)
	var near: Array[Vector2] = []
	for s in sim.village_spots:
		if s.distance_to(e.civ_home) <= sim.wander_radius:
			near.append(s)
	var pool: Array[Vector2] = near if not near.is_empty() else sim.village_spots
	if pool.is_empty():
		return
	e.order = "move"
	e.order_pos = pool[sim.civ_rng.randi_range(0, pool.size() - 1)]


func _nearest_threat(e: BattleSim.Ent) -> BattleSim.Ent:
	var best: BattleSim.Ent = null
	var best_d := sim.flee_radius * sim.flee_radius
	for o in _enemies:
		var d := e.center().distance_squared_to(o.center())
		if d <= best_d:
			best_d = d
			best = o
	return best


## The village spot farthest from the threat (the nearest to the civilian among equals); without a village, straight away.
func _flee_spot(e: BattleSim.Ent, from: Vector2) -> Vector2:
	if sim.village_spots.is_empty():
		var away := (e.center() - from).normalized()
		if away == Vector2.ZERO:
			away = Vector2.RIGHT
		var p := e.center() + away * (sim.flee_radius + 2.0)
		return Vector2(clampf(p.x, 0.5, sim.width - 0.5), clampf(p.y, 0.5, sim.height - 0.5))
	var best := sim.village_spots[0]
	var best_d := -1.0
	var best_self := INF
	for s in sim.village_spots:
		var d := s.distance_squared_to(from)
		var ds := s.distance_squared_to(e.center())
		if d > best_d + 0.01 or (absf(d - best_d) <= 0.01 and ds < best_self):
			best_d = d
			best_self = ds
			best = s
	return best
