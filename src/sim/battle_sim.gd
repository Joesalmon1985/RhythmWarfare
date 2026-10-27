class_name BattleSim
extends RefCounted
## Deterministic, fixed-step battle simulation (PRD sections 5 to 7). One tick = 40 ms, the OpenRA tick, so the
## imported weapon reloads, speeds and repair cadence apply unchanged. Positions are in cells (floats), damage and
## health are OpenRA integers. No scene nodes: the view reads `entities` after each tick, the game feeds it
## production actions from judgement (side 0) and the authored enemy schedule (side 1).
##
## Order inside one tick (PRD section 9): production already requested this tick was applied against the building
## state at its start; then spawn queues, unit and aircraft behaviour, building weapons, repair, deaths and the outcome.

const TICK_S := 0.04
const TICKS_PER_SECOND := 25
const SIDES := 2
const SPAWN_INTERVAL_TICKS := 3
const EXIT_BLOCK_RADIUS := 0.55
const TARGET_RESCAN_TICKS := 5
const ACQUIRE_EXTRA_CELLS := 3.0
const WALL_STUCK_TICKS := 20
const AIR_STANDOFF := 3.5
const AIR_LAND_RADIUS := 0.3
const FACING_FRAMES := 32

enum Kind { UNIT, BUILDING, AIRCRAFT }
enum Air { READY, SORTIE, RETURNING, LANDING, REARMING, WAITING, DEAD }

## One actor in the world.
class Ent:
	var id := 0
	var kind := Kind.UNIT
	var actor := ""      # actor id (1tnk, e1, heli, hpad...)
	var role := ""       # roster role (tank, infantry, aircraft, pad, main, factory, barracks, power, wall, turret, aa, sam)
	var side := 0
	var x := 0.0
	var y := 0.0
	var hp := 0
	var max_hp := 0
	var armor := "None"
	var alive := true
	var heading := 0.0   # radians, screen space (0 = +x, clockwise positive because y points down)
	var turret_heading := 0.0
	var speed := 0.0     # cells per tick
	var weapons: Array = []  # [{name, def, cooldown, burst_left, burst_timer}]
	var target := -1
	var rescan := 0
	var stuck := 0
	var radius := 0.3
	var is_defence := false
	# buildings
	var cx := 0           # footprint origin cell
	var cy := 0
	var w := 1
	var h := 1
	var slot := -1        # air slot index for pads and aircraft
	var repair_ticks := 0
	var repairing := false
	var value := 0
	# aircraft
	var air := Air.READY
	var ammo := 0
	var ammo_max := 0
	var rearm_timer := 0
	var ready_since := 0
	var moving := false

	func center() -> Vector2:
		return Vector2(x, y)

	func targetable_as() -> String:
		if kind == Kind.AIRCRAFT and air in [Air.SORTIE, Air.RETURNING, Air.LANDING, Air.WAITING]:
			return "AirborneActor"
		return "GroundActor"


var rules: Rules
var seed_value := 0
var tick_count := 0
var entities: Array[Ent] = []
var by_id: Dictionary = {}
var width := 28
var height := 10
var outcome := ""        # "", "victory", "defeat"
var outcome_reason := ""
var events: Array = []
var credits: Array[int] = [0, 0]
var slots: Array = []     # per side: Array of {pad: id|-1, aircraft: id|-1, used: bool}
var spawn_queue: Array = []  # per side: {"tank": [count], "infantry": [...]} as arrays of pending unit roles
var producer_ids: Array = []  # per side: role -> id
var stats: Dictionary = {}
var _blocked: Dictionary = {}  # Vector2i -> building id
var _grid: Dictionary = {}     # Vector2i -> Array[int] unit ids (rebuilt each tick)
var _next_id := 1
var _rng := RandomNumberGenerator.new()
var _airfield_limit := 5
var _aircraft_limit := 5
var _tank_per_kick := 1
var _infantry_per_snare := 5


func setup(p_rules: Rules, level_rules: Dictionary, p_seed: int) -> void:
	rules = p_rules
	seed_value = p_seed
	_rng.seed = p_seed
	_airfield_limit = int(level_rules.get("airfield_limit", 5))
	_aircraft_limit = int(level_rules.get("aircraft_limit", 5))
	_tank_per_kick = int(level_rules.get("tank_per_kick", 1))
	_infantry_per_snare = int(level_rules.get("infantry_per_snare", 5))
	var budget := int(level_rules.get("repair_budget_credits_per_side", 5000))
	credits = [budget, budget]
	var bf := rules.battlefield
	width = int(bf.get("width", 28))
	height = int(bf.get("height", 10))
	stats = {"produced": [{"tank": 0, "infantry": 0, "aircraft": 0, "pad": 0}, {"tank": 0, "infantry": 0, "aircraft": 0, "pad": 0}],
		"lost": [{}, {}], "air_busy": [0, 0], "blocked": [{}, {}]}
	slots = [[], []]
	spawn_queue = [[], []]
	producer_ids = [{}, {}]
	for side in SIDES:
		for i in _airfield_limit:
			slots[side].append({"pad": -1, "aircraft": -1, "used": false, "origin": Vector2i.ZERO})
	var initial_pads := int(level_rules.get("initial_airfields", 0))
	for side in SIDES:
		for b in bf.get("buildings", []):
			var role := str(b["role"])
			var bw := int(b.get("w", 1))
			var bh := int(b.get("h", 1))
			var bx := int(b["x"])
			var by := int(b["y"])
			if side == 1:
				bx = width - bx - bw
			if role == "pad":
				var slot := int(b.get("slot", 0))
				if slot >= _airfield_limit:
					continue
				slots[side][slot]["origin"] = Vector2i(bx, by)
				if slot < initial_pads:
					_build_pad(side, slot)
				continue
			var e := _spawn_building(side, role, bx, by, bw, bh)
			if role in ["main", "factory", "barracks"]:
				producer_ids[side][role] = e.id
	_check_outcome()


func drain_events() -> Array:
	var out := events
	events = []
	return out


func get_entity(id: int) -> Ent:
	return by_id.get(id)


func producer_alive(side: int, role: String) -> bool:
	var e: Ent = by_id.get(producer_ids[side].get(role, -1))
	return e != null and e.alive


func pads_alive(side: int) -> int:
	var n := 0
	for s in slots[side]:
		var p: Ent = by_id.get(s["pad"])
		if p != null and p.alive:
			n += 1
	return n


func pads_ever_built(side: int) -> bool:
	for s in slots[side]:
		if s["used"]:
			return true
	return false


func live_aircraft(side: int) -> int:
	var n := 0
	for s in slots[side]:
		var a: Ent = by_id.get(s["aircraft"])
		if a != null and a.alive:
			n += 1
	return n


func main_base(side: int) -> Ent:
	return by_id.get(producer_ids[side].get("main", -1))


## A rhythm production action (PRD section 4 rewards and section 5 air priority). Returns what happened.
func produce(side: int, action: String) -> Dictionary:
	if not outcome.is_empty():
		return {"action": action, "result": "ended"}
	match action:
		"kick":
			if not producer_alive(side, "factory"):
				_count_blocked(side, action)
				return {"action": action, "result": "no_factory"}
			for i in _tank_per_kick:
				spawn_queue[side].append("tank")
			stats["produced"][side]["tank"] += _tank_per_kick
			return {"action": action, "result": "queued", "count": _tank_per_kick}
		"snare":
			if not producer_alive(side, "barracks"):
				_count_blocked(side, action)
				return {"action": action, "result": "no_barracks"}
			for i in _infantry_per_snare:
				spawn_queue[side].append("infantry")
			stats["produced"][side]["infantry"] += _infantry_per_snare
			return {"action": action, "result": "queued", "count": _infantry_per_snare}
		"bass":
			return _bass_action(side)
	return {"action": action, "result": "unknown"}


func _count_blocked(side: int, action: String) -> void:
	var b: Dictionary = stats["blocked"][side]
	b[action] = int(b.get(action, 0)) + 1


func _bass_action(side: int) -> Dictionary:
	var side_slots: Array = slots[side]
	# 1. a slot whose building is missing: destroyed previously-used slots first, then never-used ones
	var candidate := -1
	for i in side_slots.size():
		var s: Dictionary = side_slots[i]
		var pad: Ent = by_id.get(s["pad"])
		if (pad == null or not pad.alive) and s["used"]:
			candidate = i
			break
	if candidate < 0:
		for i in side_slots.size():
			var s: Dictionary = side_slots[i]
			var pad: Ent = by_id.get(s["pad"])
			if pad == null or not pad.alive:
				candidate = i
				break
	if candidate >= 0:
		var pad := _build_pad(side, candidate)
		var s: Dictionary = side_slots[candidate]
		var a: Ent = by_id.get(s["aircraft"])
		var created := false
		if a == null or not a.alive:
			if live_aircraft(side) < _aircraft_limit:
				a = _spawn_aircraft(side, candidate, pad)
				created = true
			else:
				a = null
		else:
			# reconnect: an orphan waiting for its pad comes home to rearm or launches if it is ready
			if a.air == Air.WAITING:
				a.air = Air.RETURNING
		var launched := false
		if a != null and a.air == Air.READY:
			_launch(a)
			launched = true
		return {"action": "bass", "result": "pad_built", "slot": candidate, "aircraft_created": created, "launched": launched}
	# 2. an intact slot that has lost its aircraft
	for i in side_slots.size():
		var s: Dictionary = side_slots[i]
		var a: Ent = by_id.get(s["aircraft"])
		if a == null or not a.alive:
			if live_aircraft(side) >= _aircraft_limit:
				break
			var pad: Ent = by_id.get(s["pad"])
			var na := _spawn_aircraft(side, i, pad)
			_launch(na)
			return {"action": "bass", "result": "aircraft_replaced", "slot": i, "launched": true}
	# 3. launch the longest-waiting ready aircraft (ties by slot index)
	var best: Ent = null
	for i in side_slots.size():
		var a: Ent = by_id.get(side_slots[i]["aircraft"])
		if a != null and a.alive and a.air == Air.READY:
			if best == null or a.ready_since < best.ready_since:
				best = a
	if best != null:
		_launch(best)
		return {"action": "bass", "result": "sortie", "slot": best.slot}
	# 4. everything is busy
	stats["air_busy"][side] += 1
	events.append({"kind": "air_busy", "side": side})
	return {"action": "bass", "result": "air_busy"}


func _build_pad(side: int, slot: int) -> Ent:
	var s: Dictionary = slots[side][slot]
	var o: Vector2i = s["origin"]
	var pad := _spawn_building(side, "pad", o.x, o.y, 2, 2)
	pad.slot = slot
	s["pad"] = pad.id
	s["used"] = true
	stats["produced"][side]["pad"] += 1
	events.append({"kind": "pad_built", "side": side, "slot": slot, "id": pad.id, "pads_alive": pads_alive(side)})
	return pad


func _spawn_aircraft(side: int, slot: int, pad: Ent) -> Ent:
	var def := rules.actor_for_role("aircraft")
	var a := Ent.new()
	a.id = _next_id
	_next_id += 1
	a.kind = Kind.AIRCRAFT
	a.actor = rules.actor_id_for_role("aircraft")
	a.role = "aircraft"
	a.side = side
	a.slot = slot
	a.x = pad.x
	a.y = pad.y
	a.hp = int(def.get("hp", 12000))
	a.max_hp = a.hp
	a.armor = str(def.get("armor", "Light"))
	a.speed = float(def.get("speed", 149)) / 1024.0
	a.radius = 0.4
	a.ammo_max = int(rules.aircraft.get("ammo", 8))
	a.ammo = a.ammo_max
	a.air = Air.READY
	a.ready_since = tick_count
	a.heading = 0.0 if side == 0 else PI
	a.weapons = _make_weapons(def)
	entities.append(a)
	by_id[a.id] = a
	slots[side][slot]["aircraft"] = a.id
	stats["produced"][side]["aircraft"] += 1
	events.append({"kind": "aircraft_created", "side": side, "slot": slot, "id": a.id})
	return a


func _launch(a: Ent) -> void:
	a.air = Air.SORTIE
	a.target = -1
	a.rescan = 0
	events.append({"kind": "sortie", "side": a.side, "slot": a.slot, "id": a.id})


func _spawn_building(side: int, role: String, bx: int, by: int, bw: int, bh: int) -> Ent:
	var def := rules.actor_for_role(role)
	var e := Ent.new()
	e.id = _next_id
	_next_id += 1
	e.kind = Kind.BUILDING
	e.actor = rules.actor_id_for_role(role)
	e.role = role
	e.side = side
	e.cx = bx
	e.cy = by
	e.w = bw
	e.h = bh
	e.x = bx + bw * 0.5
	e.y = by + bh * 0.5
	e.hp = int(def.get("hp", 10000))
	e.max_hp = e.hp
	e.armor = str(def.get("armor", "Wood"))
	e.value = int(def.get("cost", 0))
	e.is_defence = role in ["turret", "aa", "sam"]
	e.radius = maxf(bw, bh) * 0.5
	e.weapons = _make_weapons(def)
	e.heading = 0.0 if side == 0 else PI
	e.turret_heading = e.heading
	entities.append(e)
	by_id[e.id] = e
	for i in bw:
		for j in bh:
			_blocked[Vector2i(bx + i, by + j)] = e.id
	return e


func _spawn_unit(side: int, role: String, at: Vector2) -> Ent:
	var def := rules.actor_for_role(role)
	var e := Ent.new()
	e.id = _next_id
	_next_id += 1
	e.kind = Kind.UNIT
	e.actor = rules.actor_id_for_role(role)
	e.role = role
	e.side = side
	e.x = at.x
	e.y = at.y
	e.hp = int(def.get("hp", 1000))
	e.max_hp = e.hp
	e.armor = str(def.get("armor", "None"))
	e.speed = float(def.get("speed", 50)) / 1024.0
	e.radius = 0.2 if role == "infantry" else 0.4
	e.heading = 0.0 if side == 0 else PI
	e.turret_heading = e.heading
	e.weapons = _make_weapons(def)
	entities.append(e)
	by_id[e.id] = e
	events.append({"kind": "spawned", "side": side, "role": role, "id": e.id})
	return e


func _make_weapons(def: Dictionary) -> Array:
	var out := []
	for name in def.get("armaments", []):
		var w := rules.weapon(str(name))
		if w.is_empty():
			continue
		out.append({"name": str(name), "def": w, "cooldown": 0, "burst_left": 0, "burst_timer": 0})
	return out


## Advance one tick.
func tick() -> void:
	if not outcome.is_empty():
		return
	tick_count += 1
	_rebuild_grid()
	_process_spawn_queues()
	for e in entities:
		if not e.alive:
			continue
		match e.kind:
			Kind.UNIT:
				_unit_step(e)
			Kind.AIRCRAFT:
				_aircraft_step(e)
			Kind.BUILDING:
				_building_step(e)
	_repair_step()
	_check_outcome()


func _rebuild_grid() -> void:
	_grid.clear()
	for e in entities:
		if e.alive and e.kind == Kind.UNIT:
			var key := Vector2i(int(floor(e.x)), int(floor(e.y)))
			if not _grid.has(key):
				_grid[key] = []
			_grid[key].append(e.id)


func _process_spawn_queues() -> void:
	if tick_count % SPAWN_INTERVAL_TICKS != 0:
		return
	var exits: Dictionary = rules.battlefield.get("exits", {})
	for side in SIDES:
		var q: Array = spawn_queue[side]
		if q.is_empty():
			continue
		var role: String = q[0]
		var producer := "factory" if role == "tank" else "barracks"
		if not producer_alive(side, producer):
			# the producer died after the award: the award stays queued and would spawn if... it cannot. Drop it,
			# recorded, because nothing can ever build it (PRD: dead producers stop production).
			q.pop_front()
			_count_blocked(side, "queued_" + role)
			continue
		var ex: Array = exits.get(producer, [8, 4])
		var exit_x := float(ex[0]) + 0.5
		if side == 1:
			exit_x = width - exit_x
		var exit_pos := Vector2(exit_x, float(ex[1]) + 0.5)
		var lane_offset := float((tick_count / SPAWN_INTERVAL_TICKS) % 3 - 1) * 0.3
		var at := exit_pos + Vector2(0.0, lane_offset)
		if _occupied_near(at, EXIT_BLOCK_RADIUS):
			continue  # keep the award in the physical queue; never discard it
		q.pop_front()
		_spawn_unit(side, role, at)


func _occupied_near(p: Vector2, r: float) -> bool:
	for id in _neighbours(p):
		var e: Ent = by_id[id]
		if e.center().distance_to(p) < r:
			return true
	return false


func _neighbours(p: Vector2) -> Array:
	var out := []
	var cxi := int(floor(p.x))
	var cyi := int(floor(p.y))
	for i in range(-1, 2):
		for j in range(-1, 2):
			var list: Array = _grid.get(Vector2i(cxi + i, cyi + j), [])
			out.append_array(list)
	return out


func _enemy_main_pos(side: int) -> Vector2:
	var m := main_base(1 - side)
	if m != null:
		return m.center()
	return Vector2(width - 2.0 if side == 0 else 2.0, height * 0.5)


func _target_classes(e: Ent) -> Array:
	return [0, 1, 2]  # units, defences, other buildings


## Priority: nearest enemy unit or aircraft, then nearest defence, then nearest other building (walls last, only
## when stuck). Weapons' target filters decide what can be hit at all.
func _acquire(e: Ent, acquire_range: float, include_walls: bool) -> int:
	var best := -1
	var best_class := 99
	var best_d := INF
	var p := e.center()
	for o in entities:
		if not o.alive or o.side == e.side or o.id == e.id:
			continue
		if not _can_hit(e, o):
			continue
		var cls := 2
		if o.kind != Kind.BUILDING:
			cls = 0
		elif o.is_defence:
			cls = 1
		elif o.role == "wall":
			if not include_walls:
				continue
			cls = 3
		var d := p.distance_to(o.center()) - (o.radius if o.kind == Kind.BUILDING else 0.0)
		var limit := acquire_range if cls == 0 else maxf(_max_range(e), 0.5) + (ACQUIRE_EXTRA_CELLS if cls == 1 else 0.0)
		if d > limit:
			continue
		if cls < best_class or (cls == best_class and d < best_d):
			best = o.id
			best_class = cls
			best_d = d
	return best


func _can_hit(shooter: Ent, target: Ent) -> bool:
	var tt := target.targetable_as()
	for w in shooter.weapons:
		if tt in w["def"].get("valid_targets", []):
			return true
	return false


func _max_range(e: Ent) -> float:
	var r := 0.0
	for w in e.weapons:
		r = maxf(r, float(w["def"].get("range", 0.0)))
	return r


func _unit_step(e: Ent) -> void:
	e.rescan -= 1
	var t: Ent = by_id.get(e.target)
	if t != null and not t.alive:
		t = null
		e.target = -1
	if e.rescan <= 0 or t == null:
		e.rescan = TARGET_RESCAN_TICKS
		var found := _acquire(e, _max_range(e) + ACQUIRE_EXTRA_CELLS, e.stuck > WALL_STUCK_TICKS)
		if found >= 0 and (t == null or found != t.id):
			var cand: Ent = by_id[found]
			# keep a current unit target unless the new one is a unit too (units always outrank buildings)
			if t == null or t.kind == Kind.BUILDING or cand.kind != Kind.BUILDING:
				e.target = found
				t = cand
	_tick_weapons(e)
	if t != null:
		var tp := t.center()
		var d := e.center().distance_to(tp) - (t.radius if t.kind == Kind.BUILDING else 0.0)
		var in_range := false
		for w in e.weapons:
			if t.targetable_as() in w["def"].get("valid_targets", []) and d <= float(w["def"]["range"]):
				in_range = true
				_fire(e, w, t)
		if in_range:
			e.moving = false
			e.turret_heading = (tp - e.center()).angle()
			return
		_move_toward(e, tp)
		return
	_move_toward(e, _enemy_main_pos(e.side))


func _tick_weapons(e: Ent) -> void:
	for w in e.weapons:
		if w["cooldown"] > 0:
			w["cooldown"] -= 1
		if w["burst_timer"] > 0:
			w["burst_timer"] -= 1


func _fire(e: Ent, w: Dictionary, t: Ent) -> void:
	var def: Dictionary = w["def"]
	if e.kind == Kind.AIRCRAFT and e.ammo <= 0:
		return
	if w["burst_left"] > 0:
		if w["burst_timer"] > 0:
			return
		w["burst_left"] -= 1
		w["burst_timer"] = int(def.get("burst_delay", 5))
		_shot(e, w, t)
		if w["burst_left"] == 0:
			w["cooldown"] = int(def.get("reload", 20))
		return
	if w["cooldown"] > 0:
		return
	var burst := int(def.get("burst", 1))
	w["burst_left"] = burst - 1
	w["burst_timer"] = int(def.get("burst_delay", 5))
	_shot(e, w, t)
	if w["burst_left"] == 0:
		w["cooldown"] = int(def.get("reload", 20))


func _shot(e: Ent, w: Dictionary, t: Ent) -> void:
	if e.kind == Kind.AIRCRAFT:
		if e.ammo <= 0:
			return
		e.ammo -= 1
	var def: Dictionary = w["def"]
	var total := 0
	for wh in def.get("warheads", []):
		if wh.get("type", "") != "SpreadDamage":
			continue
		if not (t.targetable_as() in wh.get("valid_targets", ["GroundActor"])):
			continue
		total += Rules.damage_versus(wh, t.armor)
	e.turret_heading = (t.center() - e.center()).angle()
	events.append({"kind": "shot", "from": e.id, "to": t.id, "weapon": w["name"], "x": e.x, "y": e.y, "tx": t.x, "ty": t.y})
	_damage(t, total, e)


func _damage(t: Ent, amount: int, by: Ent) -> void:
	if amount <= 0 or not t.alive:
		return
	t.hp -= amount
	events.append({"kind": "hit", "id": t.id, "amount": amount, "x": t.x, "y": t.y})
	if t.kind == Kind.BUILDING and t.role != "wall" and t.hp < t.max_hp and not t.repairing:
		_start_repair(t)
	if t.hp <= 0:
		t.hp = 0
		_kill(t, by)


func _start_repair(b: Ent) -> void:
	if credits[b.side] <= 0:
		return
	b.repairing = true
	b.repair_ticks = 0


func _kill(t: Ent, by: Ent) -> void:
	t.alive = false
	t.repairing = false
	var lost: Dictionary = stats["lost"][t.side]
	lost[t.role] = int(lost.get(t.role, 0)) + 1
	events.append({"kind": "destroyed", "id": t.id, "side": t.side, "role": t.role, "x": t.x, "y": t.y, "by": by.id if by != null else -1})
	if t.kind == Kind.BUILDING:
		for i in t.w:
			for j in t.h:
				_blocked.erase(Vector2i(t.cx + i, t.cy + j))
		if t.role == "pad":
			# a parked aircraft dies with its pad; an airborne one is orphaned and keeps flying
			var s: Dictionary = slots[t.side][t.slot]
			var a: Ent = by_id.get(s["aircraft"])
			if a != null and a.alive and a.air in [Air.READY, Air.REARMING]:
				_kill(a, by)
			events.append({"kind": "pad_lost", "side": t.side, "slot": t.slot, "pads_alive": pads_alive(t.side)})
		elif t.role in ["factory", "barracks", "main"]:
			events.append({"kind": "producer_lost", "side": t.side, "role": t.role})
	elif t.kind == Kind.AIRCRAFT:
		events.append({"kind": "aircraft_lost", "side": t.side, "slot": t.slot, "id": t.id})


func _move_toward(e: Ent, goal: Vector2) -> void:
	var p := e.center()
	var to := goal - p
	if to.length() < 0.05:
		e.moving = false
		return
	var dir := to.normalized()
	var step := dir * e.speed
	var moved := _try_step(e, step)
	if not moved:
		var perp := Vector2(-dir.y, dir.x)
		if (e.id % 2 == 0) == (e.side == 0):
			perp = -perp
		moved = _try_step(e, perp * e.speed) or _try_step(e, -perp * e.speed)
	if moved:
		e.stuck = 0
		e.heading = step.angle()
		e.turret_heading = e.heading
		e.moving = true
	else:
		e.stuck += 1
		e.moving = false
	_separate(e)


func _try_step(e: Ent, step: Vector2) -> bool:
	var nx := e.x + step.x
	var ny := e.y + step.y
	if nx < 0.2 or nx > width - 0.2 or ny < 0.2 or ny > height - 0.2:
		return false
	var cell := Vector2i(int(floor(nx)), int(floor(ny)))
	if _blocked.has(cell):
		return false
	e.x = nx
	e.y = ny
	return true


func _separate(e: Ent) -> void:
	var p := e.center()
	var push := Vector2.ZERO
	for id in _neighbours(p):
		if id == e.id:
			continue
		var o: Ent = by_id[id]
		var d := p - o.center()
		var min_d := e.radius + o.radius
		var len := d.length()
		if len < min_d and len > 0.0001:
			push += d / len * (min_d - len) * 0.5
		elif len <= 0.0001:
			push += Vector2(0.0, 0.01 * (1 if e.id % 2 == 0 else -1))
	if push != Vector2.ZERO:
		var nx := clampf(e.x + push.x, 0.2, width - 0.2)
		var ny := clampf(e.y + push.y, 0.2, height - 0.2)
		if not _blocked.has(Vector2i(int(floor(nx)), int(floor(ny)))):
			e.x = nx
			e.y = ny


func _building_step(b: Ent) -> void:
	if b.weapons.is_empty():
		return
	_tick_weapons(b)
	b.rescan -= 1
	var t: Ent = by_id.get(b.target)
	if t != null and (not t.alive or not _can_hit(b, t) or b.center().distance_to(t.center()) > _max_range(b)):
		t = null
		b.target = -1
	if t == null and b.rescan <= 0:
		b.rescan = TARGET_RESCAN_TICKS
		var found := _acquire(b, _max_range(b), false)
		if found >= 0:
			b.target = found
			t = by_id[found]
	if t == null:
		return
	var d := b.center().distance_to(t.center())
	for w in b.weapons:
		var def: Dictionary = w["def"]
		if t.targetable_as() in def.get("valid_targets", []) and d <= float(def["range"]) and d >= float(def.get("min_range", 0.0)):
			_fire(b, w, t)


func _aircraft_step(a: Ent) -> void:
	_tick_weapons(a)
	var s: Dictionary = slots[a.side][a.slot]
	var pad: Ent = by_id.get(s["pad"])
	var pad_ok := pad != null and pad.alive
	match a.air:
		Air.READY:
			return
		Air.REARMING:
			if not pad_ok:
				return  # unreachable: the pad's death kills a parked aircraft
			a.rearm_timer += 1
			if a.rearm_timer >= int(rules.aircraft.get("rearm_delay_ticks", 50)):
				a.rearm_timer = 0
				a.ammo = mini(a.ammo_max, a.ammo + int(rules.aircraft.get("rearm_count", 1)))
				if a.ammo >= a.ammo_max:
					a.air = Air.READY
					a.ready_since = tick_count
					events.append({"kind": "aircraft_ready", "side": a.side, "slot": a.slot, "id": a.id})
			return
		Air.SORTIE:
			if a.ammo <= 0:
				a.air = Air.RETURNING
				a.target = -1
				events.append({"kind": "returning", "side": a.side, "slot": a.slot, "id": a.id})
				return
			a.rescan -= 1
			var t: Ent = by_id.get(a.target)
			if t != null and not t.alive:
				t = null
				a.target = -1
			if t == null or a.rescan <= 0:
				a.rescan = TARGET_RESCAN_TICKS
				var found := _acquire_air(a)
				if found >= 0:
					a.target = found
					t = by_id[found]
			if t == null:
				# nothing to attack: hold over the forward position and wait
				var hold: Array = rules.battlefield.get("air_hold", [12, 5])
				var hx := float(hold[0]) + 0.5
				if a.side == 1:
					hx = width - hx
				_fly_toward(a, Vector2(hx, float(hold[1]) + 0.5), 0.3)
				return
			var tp := t.center()
			var d := a.center().distance_to(tp)
			var fired := false
			for w in a.weapons:
				var def: Dictionary = w["def"]
				if t.targetable_as() in def.get("valid_targets", []) and d <= float(def["range"]) and d >= float(def.get("min_range", 0.0)):
					_fire(a, w, t)
					fired = true
			if not fired and d > AIR_STANDOFF:
				_fly_toward(a, tp, AIR_STANDOFF)
			else:
				a.heading = (tp - a.center()).angle()
		Air.RETURNING:
			if not pad_ok:
				a.air = Air.WAITING
				events.append({"kind": "orphaned", "side": a.side, "slot": a.slot, "id": a.id})
				return
			if _fly_toward(a, pad.center(), AIR_LAND_RADIUS):
				a.air = Air.LANDING
		Air.LANDING:
			if not pad_ok:
				a.air = Air.WAITING
				return
			a.x = pad.x
			a.y = pad.y
			a.air = Air.REARMING
			a.rearm_timer = 0
			events.append({"kind": "landed", "side": a.side, "slot": a.slot, "id": a.id})
		Air.WAITING:
			# pad gone: wait visibly on our own side until a bass action rebuilds it (then RETURNING)
			if pad_ok:
				a.air = Air.RETURNING
				return
			var wait: Array = rules.battlefield.get("air_wait", [1, 5])
			var wx := float(wait[0]) + 0.5
			if a.side == 1:
				wx = width - wx
			_fly_toward(a, Vector2(wx, float(wait[1]) + 0.5), 0.3)


## Aircraft priorities: frontline enemy units first, then forward defences, then other buildings; never walls.
func _acquire_air(a: Ent) -> int:
	var best := -1
	var best_class := 99
	var best_score := INF
	var front_x := _enemy_main_pos(a.side).x
	for o in entities:
		if not o.alive or o.side == a.side:
			continue
		if o.role == "wall" or not _can_hit(a, o):
			continue
		var cls := 2
		if o.kind != Kind.BUILDING:
			cls = 0
		elif o.is_defence:
			cls = 1
		# "forward" means nearest to our side: smallest distance from our own base line
		var forwardness := absf(o.x - front_x)
		var score := -forwardness + a.center().distance_to(o.center()) * 0.25
		if cls < best_class or (cls == best_class and score < best_score):
			best = o.id
			best_class = cls
			best_score = score
	return best


func _fly_toward(a: Ent, goal: Vector2, stop_within: float) -> bool:
	var to := goal - a.center()
	var dist := to.length()
	if dist <= stop_within:
		return true
	var step := minf(a.speed, dist)
	var dir := to / dist
	a.x += dir.x * step
	a.y += dir.y * step
	a.heading = dir.angle()
	a.moving = true
	return a.center().distance_to(goal) <= stop_within


## OpenRA RepairableBuilding at the pinned commit: every RepairInterval ticks restore min(RepairStep, missing HP),
## charging max(1, hp * RepairPercent * value / (MaxHP * 100)) with long integer arithmetic; when the side cannot pay,
## retry next tick; stop at full health. Activation is automatic (MVP adaptation), walls never repair.
func _repair_step() -> void:
	var interval := int(rules.repair.get("repair_interval", 24))
	var step := int(rules.repair.get("repair_step", 700))
	var percent := int(rules.repair.get("repair_percent", 20))
	for b in entities:
		if not b.alive or b.kind != Kind.BUILDING or not b.repairing:
			continue
		if b.repair_ticks > 0:
			b.repair_ticks -= 1
			continue
		var hp_to_repair := mini(step, b.max_hp - b.hp)
		if hp_to_repair <= 0:
			b.repairing = false
			continue
		var cost := maxi(1, int((hp_to_repair * percent * b.value) / (b.max_hp * 100)))
		if credits[b.side] < cost:
			b.repair_ticks = 1
			b.repairing = credits[b.side] > 0
			continue
		credits[b.side] -= cost
		b.hp += hp_to_repair
		events.append({"kind": "repaired", "id": b.id, "amount": hp_to_repair, "cost": cost})
		if b.hp >= b.max_hp:
			b.hp = b.max_hp
			b.repairing = false
			continue
		b.repair_ticks = interval


func _check_outcome() -> void:
	if not outcome.is_empty():
		return
	var player_main := main_base(0)
	var enemy_main := main_base(1)
	var player_dead := player_main == null or not player_main.alive
	var enemy_dead := enemy_main == null or not enemy_main.alive
	if player_dead:
		outcome = "defeat"
		outcome_reason = "mutual_destruction" if enemy_dead else "main_base_destroyed"
	elif enemy_dead:
		outcome = "victory"
		outcome_reason = "enemy_main_base_destroyed"
	if not outcome.is_empty():
		events.append({"kind": "outcome", "outcome": outcome, "reason": outcome_reason, "tick": tick_count})


## The song ended without a decision.
func end_by_song() -> void:
	if outcome.is_empty():
		outcome = "defeat"
		outcome_reason = "song_end"
		events.append({"kind": "outcome", "outcome": outcome, "reason": outcome_reason, "tick": tick_count})


func count_alive(side: int, kind: int) -> int:
	var n := 0
	for e in entities:
		if e.alive and e.side == side and e.kind == kind:
			n += 1
	return n
