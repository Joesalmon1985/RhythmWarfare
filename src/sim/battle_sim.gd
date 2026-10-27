class_name BattleSim
extends RefCounted
## Deterministic, fixed-step battle simulation (PRD sections 5 to 7) that behaves like OpenRA Red Alert
## (docs/OPENRA_BEHAVIOUR_SPEC.md). One tick = 40 ms, the OpenRA tick, so the imported weapon reloads, speeds,
## turn rates and repair cadence apply unchanged. Positions are in cells (floats), damage and health are OpenRA
## integers. No scene nodes: the view reads `entities` after each tick; production comes from judgement (side 0)
## and the authored enemy schedule (side 1); both sides' units are commanded by BotAi (the Rush AI squad logic).
##
## Order inside one tick (PRD section 9): production requested this tick was applied against the building state
## at its start; then spawn queues, the bots, units, aircraft, building weapons, projectiles, repair, outcome.

const TICK_S := 0.04
const TICKS_PER_SECOND := 25
const SIDES := 2
const SPAWN_INTERVAL_TICKS := 3
const EXIT_BLOCK_RADIUS := 0.55
const REPATH_TICKS := 50
const BLOCKED_WAIT_TICKS := 40
const AIR_LAND_RADIUS := 0.3
const RANGE_MARGIN := 1.0           # AttackFollow RangeMargin 1c0 against moving targets
const ATTACK_MOVE_NEAR_ENOUGH := 8.0
const PRONE_TICKS := 50
const SCAN_MIN := 3
const SCAN_MAX := 8
const WORLD := 1024.0

enum Kind { UNIT, BUILDING, AIRCRAFT }
enum Air { READY, SORTIE, RETURNING, LANDING, REARMING, WAITING, DEAD }

## One actor in the world.
class Ent:
	var id := 0
	var kind := Kind.UNIT
	var actor := ""      # actor id (1tnk, e1, heli, hpad...)
	var role := ""       # roster role (tank, infantry, aircraft, pad, main, factory, barracks, power, wall, turret, sam)
	var side := 0
	var x := 0.0
	var y := 0.0
	var hp := 0
	var max_hp := 0
	var armor := "None"
	var alive := true
	var heading := 0.0   # radians, screen space (0 = +x, clockwise positive because y points down)
	var turret_heading := 0.0
	var speed := 0.0     # cells per tick on clear terrain
	var turn_speed := TAU  # radians per tick for the body (infantry: instant)
	var turret_turn := TAU
	var weapons: Array = []  # [{name, def, cooldown, burst_left, burst_timer}]
	var target := -1
	var scan_timer := 0
	var stuck := 0
	var radius := 0.3
	var is_defence := false
	var moving := false
	var firing := 0        # ticks left to show the shooting pose
	var prone_ticks := 0
	var crushes_infantry := false
	var crushes_walls := false
	var target_types: Array = []
	# orders (from BotAi)
	var order := "idle"    # idle | move | attack_move | attack
	var order_pos := Vector2.ZERO
	var order_target := -1
	var resume_attack_move := false
	var squad := -1
	var wait_ticks := 0
	# buildings
	var cx := 0
	var cy := 0
	var w := 1
	var h := 1
	var slot := -1
	var path := PackedVector2Array()
	var path_index := 0
	var path_goal := Vector2i(-1, -1)
	var repath := 0
	var repair_ticks := 0
	var repairing := false
	var value := 0
	# aircraft
	var air := Air.READY
	var ammo := 0
	var ammo_max := 0
	var rearm_timer := 0
	var ready_since := 0

	func center() -> Vector2:
		return Vector2(x, y)

	func airborne() -> bool:
		return kind == Kind.AIRCRAFT and air in [Air.SORTIE, Air.RETURNING, Air.LANDING, Air.WAITING]

	func targetable_as() -> String:
		return "AirborneActor" if airborne() else "GroundActor"

	func is_mobile() -> bool:
		return kind != Kind.BUILDING

	func cell() -> Vector2i:
		return Vector2i(int(floor(x)), int(floor(y)))


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
var slots: Array = []     # per side: Array of {pad: id|-1, aircraft: id|-1, used: bool, origin}
var spawn_queue: Array = []  # per side: pending unit roles
var producer_ids: Array = []  # per side: role -> id
var stats: Dictionary = {}
var projectiles: Array = []  # {weapon, kind, from, to, damage, speed, x, y, tx, ty, heading, age, types}
var bots: Array = []      # BotAi per side
var rng := RandomNumberGenerator.new()
var _blocked: Dictionary = {}  # Vector2i -> building id, or -1 for terrain
var _grid: Dictionary = {}     # Vector2i -> Array[int] unit ids (rebuilt each tick)
var _astar_foot := AStarGrid2D.new()   # infantry: walls block
var _astar_track := AStarGrid2D.new()  # tracked vehicles: sandbag walls are crushed, not avoided
var _next_id := 1
var _airfield_limit := 5
var _aircraft_limit := 5
var _tank_per_kick := 1
var _infantry_per_snare := 5


func setup(p_rules: Rules, level_rules: Dictionary, p_seed: int) -> void:
	rules = p_rules
	seed_value = p_seed
	rng.seed = p_seed
	_airfield_limit = int(level_rules.get("airfield_limit", 5))
	_aircraft_limit = int(level_rules.get("aircraft_limit", 5))
	_tank_per_kick = int(level_rules.get("tank_per_kick", 1))
	_infantry_per_snare = int(level_rules.get("infantry_per_snare", 5))
	var budget := int(level_rules.get("repair_budget_credits_per_side", 5000))
	credits = [budget, budget]
	var bf := rules.battlefield
	width = int(bf.get("width", 28))
	height = int(bf.get("height", 10))
	for g in [_astar_foot, _astar_track]:
		g.region = Rect2i(0, 0, width, height)
		g.cell_size = Vector2(1, 1)
		g.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
		g.default_compute_heuristic = AStarGrid2D.HEURISTIC_OCTILE
		g.default_estimate_heuristic = AStarGrid2D.HEURISTIC_OCTILE
		g.update()
	_blocked.clear()
	for c in rules.terrain_blocked():
		if c.x >= 0 and c.y >= 0 and c.x < width and c.y < height:
			_blocked[c] = -1
			_astar_foot.set_point_solid(c, true)
			_astar_track.set_point_solid(c, true)
	stats = {"produced": [{"tank": 0, "infantry": 0, "aircraft": 0, "pad": 0}, {"tank": 0, "infantry": 0, "aircraft": 0, "pad": 0}],
		"lost": [{}, {}], "air_busy": [0, 0], "blocked": [{}, {}], "squads": [0, 0], "rushes": [0, 0], "flees": [0, 0]}
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
	bots = []
	for side in SIDES:
		var bot := BotAi.new()
		bot.setup(self, side, p_seed * 7 + side)
		bots.append(bot)
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


func count_alive(side: int, kind: int) -> int:
	var n := 0
	for e in entities:
		if e.alive and e.side == side and e.kind == kind:
			n += 1
	return n


func mirrored(p: Vector2, side: int) -> Vector2:
	return Vector2(width - p.x, p.y) if side == 1 else p


# ---------------------------------------------------------------- production

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
		elif a.air == Air.WAITING:
			a.air = Air.RETURNING
		var launched := false
		if a != null and a.air == Air.READY:
			_launch(a)
			launched = true
		return {"action": "bass", "result": "pad_built", "slot": candidate, "aircraft_created": created, "launched": launched}
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
	var best: Ent = null
	for i in side_slots.size():
		var a: Ent = by_id.get(side_slots[i]["aircraft"])
		if a != null and a.alive and a.air == Air.READY:
			if best == null or a.ready_since < best.ready_since:
				best = a
	if best != null:
		_launch(best)
		return {"action": "bass", "result": "sortie", "slot": best.slot}
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
	a.speed = float(def.get("speed", 149)) / WORLD
	a.turn_speed = _wangle_to_rad(16)
	a.radius = 0.4
	a.ammo_max = int(rules.aircraft.get("ammo", 8))
	a.ammo = a.ammo_max
	a.air = Air.READY
	a.ready_since = tick_count
	a.heading = 0.0 if side == 0 else PI
	a.weapons = _make_weapons(def)
	a.target_types = ["GroundActor", "Vehicle"]
	entities.append(a)
	by_id[a.id] = a
	slots[side][slot]["aircraft"] = a.id
	stats["produced"][side]["aircraft"] += 1
	events.append({"kind": "aircraft_created", "side": side, "slot": slot, "id": a.id})
	return a


func _launch(a: Ent) -> void:
	a.air = Air.SORTIE
	a.target = -1
	a.order = "idle"
	a.order_target = -1
	a.scan_timer = 0
	if bots.size() > a.side:
		bots[a.side].on_launch(a.id)
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
	e.turret_turn = _wangle_to_rad(48 if role == "turret" else 120)
	e.target_types = ["GroundActor", "Structure"] + (["Defense"] if e.is_defence else []) + (["Wall", "NoAutoTarget"] if role == "wall" else [])
	entities.append(e)
	by_id[e.id] = e
	for i in bw:
		for j in bh:
			var c := Vector2i(bx + i, by + j)
			_blocked[c] = e.id
			if c.x >= 0 and c.y >= 0 and c.x < width and c.y < height:
				_astar_foot.set_point_solid(c, true)
				if role != "wall":
					_astar_track.set_point_solid(c, true)
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
	e.speed = float(def.get("speed", 50)) / WORLD
	if role == "infantry":
		e.radius = 0.18
		e.turn_speed = TAU  # AlwaysTurnInPlace with TurnSpeed 512: instant
		e.target_types = ["GroundActor", "Infantry"]
	else:
		e.radius = 0.42
		e.turn_speed = _wangle_to_rad(20)
		e.turret_turn = _wangle_to_rad(28)
		e.crushes_infantry = true
		e.crushes_walls = true
		e.target_types = ["GroundActor", "Vehicle"]
	e.heading = 0.0 if side == 0 else PI
	e.turret_heading = e.heading
	e.weapons = _make_weapons(def)
	e.scan_timer = rng.randi_range(SCAN_MIN, SCAN_MAX - 1)
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


static func _wangle_to_rad(units_per_tick: int) -> float:
	return float(units_per_tick) / 1024.0 * TAU


# ---------------------------------------------------------------- tick

func tick() -> void:
	if not outcome.is_empty():
		return
	tick_count += 1
	_rebuild_grid()
	_process_spawn_queues()
	for bot in bots:
		bot.tick()
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
	_projectiles_step()
	_repair_step()
	_check_outcome()


func _rebuild_grid() -> void:
	_grid.clear()
	for e in entities:
		if e.alive and e.kind == Kind.UNIT:
			var key := e.cell()
			if not _grid.has(key):
				_grid[key] = []
			_grid[key].append(e.id)


func _process_spawn_queues() -> void:
	if tick_count % SPAWN_INTERVAL_TICKS != 0:
		return
	var exits: Dictionary = rules.battlefield.get("exits", {})
	var rally_cfg: Array = rules.battlefield.get("rally", [12, 5])
	for side in SIDES:
		var q: Array = spawn_queue[side]
		if q.is_empty():
			continue
		var role: String = q[0]
		var producer := "factory" if role == "tank" else "barracks"
		if not producer_alive(side, producer):
			q.pop_front()
			_count_blocked(side, "queued_" + role)
			continue
		var ex: Array = exits.get(producer, [8, 4])
		var exit_pos := mirrored(Vector2(float(ex[0]) + 0.5, float(ex[1]) + 0.5), side)
		var lane_offset := float((tick_count / SPAWN_INTERVAL_TICKS) % 3 - 1) * 0.3
		var at := exit_pos + Vector2(0.0, lane_offset)
		if _occupied_near(at, EXIT_BLOCK_RADIUS):
			continue  # keep the award in the physical queue; never discard it
		q.pop_front()
		var u := _spawn_unit(side, role, at)
		# leave the factory for the rally point (OpenRA RallyPoint), with a little spread
		var rally := mirrored(Vector2(float(rally_cfg[0]) + 0.5, float(rally_cfg[1]) + 0.5), side)
		rally += Vector2(rng.randf_range(-1.5, 1.5), rng.randf_range(-3.0, 3.0))
		u.order = "move"
		u.order_pos = Vector2(clampf(rally.x, 0.5, width - 0.5), clampf(rally.y, 0.5, height - 0.5))


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


# ---------------------------------------------------------------- targeting (AutoTarget, spec 3.3)

func can_hit(shooter: Ent, target: Ent) -> bool:
	var tt := target.targetable_as()
	for w in shooter.weapons:
		if tt in w["def"].get("valid_targets", []):
			return true
	return false


func max_range(e: Ent) -> float:
	var r := 0.0
	for w in e.weapons:
		r = maxf(r, float(w["def"].get("range", 0.0)))
	return r


func max_range_vs(e: Ent, t: Ent) -> float:
	var r := 0.0
	var tt := t.targetable_as()
	for w in e.weapons:
		if tt in w["def"].get("valid_targets", []):
			r = maxf(r, float(w["def"].get("range", 0.0)))
	return r


func min_range_vs(e: Ent, t: Ent) -> float:
	var r := INF
	var tt := t.targetable_as()
	for w in e.weapons:
		if tt in w["def"].get("valid_targets", []):
			r = minf(r, float(w["def"].get("min_range", 0.0)))
	return 0.0 if r == INF else r


## Distance from a shooter to a target's nearest edge (buildings) or centre (units), in cells.
func range_to(e: Ent, t: Ent) -> float:
	var d := e.center().distance_to(t.center())
	if t.kind == Kind.BUILDING:
		# distance to the footprint rectangle (HitShape edge)
		var dx := maxf(maxf(t.cx - e.x, 0.0), e.x - (t.cx + t.w))
		var dy := maxf(maxf(t.cy - e.y, 0.0), e.y - (t.cy + t.h))
		d = sqrt(dx * dx + dy * dy)
	return d


func target_valid(e: Ent, t: Ent) -> bool:
	return t != null and t.alive and t.side != e.side and can_hit(e, t)


## AutoTarget scan: the closest enemy inside the weapon range that a weapon is valid against; walls never
## (NoAutoTarget); stance AttackAnything (both sides are bots) includes structures.
func scan_for_target(e: Ent, radius: float) -> int:
	var best := -1
	var best_d := INF
	for o in entities:
		if not o.alive or o.side == e.side or o.id == e.id:
			continue
		if o.role == "wall" or not can_hit(e, o):
			continue
		var d := range_to(e, o)
		if d <= radius and d < best_d:
			best = o.id
			best_d = d
	return best


# ---------------------------------------------------------------- ground units (spec 3.4, 3.5, 5)

func _unit_step(e: Ent) -> void:
	_tick_weapons(e)
	if e.firing > 0:
		e.firing -= 1
	if e.prone_ticks > 0:
		e.prone_ticks -= 1
	if e.wait_ticks > 0:
		e.wait_ticks -= 1
	e.scan_timer -= 1
	var t: Ent = by_id.get(e.target)
	if t != null and not target_valid(e, t):
		t = null
		e.target = -1
		if e.order == "attack":
			e.order = "attack_move" if e.resume_attack_move else "idle"
	# explicit attack order
	if e.order == "attack":
		var ot: Ent = by_id.get(e.order_target)
		if target_valid(e, ot):
			t = ot
			e.target = ot.id
		else:
			e.order = "attack_move" if e.resume_attack_move else "idle"
	# auto-targeting while idle or attack-moving (AttackAnything, AllowMove): closest enemy within weapon range.
	# Deviation from OpenRA: a unit whose target has walked out of range also re-scans, and prefers an enemy that
	# is already in range over chasing; it keeps mass battles from dissolving into everyone chasing everyone.
	if e.scan_timer <= 0 and e.order != "move" and (t == null or range_to(e, t) > max_range_vs(e, t)):
		e.scan_timer = rng.randi_range(SCAN_MIN, SCAN_MAX - 1)
		var found := scan_for_target(e, max_range(e))
		if found >= 0:
			t = by_id[found]
			e.target = found
	if t != null:
		_engage(e, t)
		if e.moving and e.role != "infantry":
			_opportunity_fire(e, t)
		return
	e.firing = 0
	match e.order:
		"move", "attack_move":
			if e.center().distance_to(e.order_pos) <= 0.6:
				e.order = "idle"
				e.moving = false
				e.path = PackedVector2Array()
			else:
				_move_toward(e, e.order_pos)
		_:
			e.moving = false
			if e.turret_heading != e.heading and e.kind == Kind.UNIT and e.role != "infantry":
				e.turret_heading = _turn(e.turret_heading, e.heading, e.turret_turn)  # realign (RealignDelay ignored)


## Attack or chase a target: stop and fire when inside range, otherwise close in (no leash).
func _engage(e: Ent, t: Ent) -> void:
	var d := range_to(e, t)
	var rmax := max_range_vs(e, t)
	var rmin := min_range_vs(e, t)
	var mobile_target := t.is_mobile() and e.is_mobile()
	var approach := rmax
	if mobile_target:
		approach = clampf(rmax - RANGE_MARGIN, minf(rmin + RANGE_MARGIN, rmax), maxf(rmax - RANGE_MARGIN, rmin))
	var in_range := d <= rmax and d >= rmin
	if in_range:
		e.moving = false
		e.path = PackedVector2Array()
		var aim := (t.center() - e.center()).angle()
		if e.role == "infantry":
			e.heading = aim
			e.turret_heading = aim
		else:
			e.turret_heading = _turn(e.turret_heading, aim, e.turret_turn)
		var aligned := absf(angle_difference(e.turret_heading, aim)) < 0.02 or e.role == "infantry"
		if aligned:
			for w in e.weapons:
				var def: Dictionary = w["def"]
				if t.targetable_as() in def.get("valid_targets", []) and d <= float(def["range"]) and d >= float(def.get("min_range", 0.0)):
					_fire(e, w, t)
		return
	# close in: path toward the target (chase without a leash), stopping `approach` short of a moving one
	var goal := t.center()
	if t.kind == Kind.BUILDING:
		goal = Vector2(clampf(e.x, t.cx, t.cx + t.w), clampf(e.y, t.cy, t.cy + t.h))
	elif d > approach and approach > 0.5:
		goal = t.center() + (e.center() - t.center()).normalized() * (approach - 0.3)
	_move_toward(e, goal, true)


## AttackFollow OpportunityFire: a turreted unit on the move fires at the closest enemy inside its range even
## while it is chasing something else (no PersistentTargeting bookkeeping; the scan is cheap enough per tick).
func _opportunity_fire(e: Ent, chasing: Ent) -> void:
	var found := scan_for_target(e, max_range(e))
	if found < 0 or found == chasing.id:
		return
	var o: Ent = by_id[found]
	var d := range_to(e, o)
	var aim := (o.center() - e.center()).angle()
	e.turret_heading = _turn(e.turret_heading, aim, e.turret_turn)
	if absf(angle_difference(e.turret_heading, aim)) < 0.02:
		for w in e.weapons:
			var def: Dictionary = w["def"]
			if o.targetable_as() in def.get("valid_targets", []) and d <= float(def["range"]) and d >= float(def.get("min_range", 0.0)):
				_fire(e, w, o)


static func _turn(current: float, desired: float, step: float) -> float:
	var diff := angle_difference(current, desired)
	if absf(diff) <= step:
		return desired
	return current + signf(diff) * step


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


## One round leaves the weapon. Instant-hit weapons damage now; bullets fly to where the target is and hit it
## if it is still there (within a cell); missiles home. Damage is applied on impact, as OpenRA does.
func _shot(e: Ent, w: Dictionary, t: Ent) -> void:
	if e.kind == Kind.AIRCRAFT:
		if e.ammo <= 0:
			return
		e.ammo -= 1
	var def: Dictionary = w["def"]
	var total := 0
	var types: Array = []
	for wh in def.get("warheads", []):
		if wh.get("type", "") != "SpreadDamage":
			continue
		if not (t.targetable_as() in wh.get("valid_targets", ["GroundActor"])):
			continue
		total += Rules.damage_versus(wh, t.armor)
		types = wh.get("damage_types", types)
	var aim := t.center()
	e.turret_heading = (aim - e.center()).angle()
	e.firing = 6
	events.append({"kind": "shot", "from": e.id, "to": t.id, "weapon": w["name"], "x": e.x, "y": e.y, "tx": aim.x, "ty": aim.y, "heading": e.turret_heading})
	var speed := float(def.get("projectile_speed", 0)) / WORLD
	var kind := str(def.get("projectile", "InstantHit"))
	if kind == "InstantHit" or speed <= 0.0:
		_impact(t, total, e, w["name"], aim, true)
		return
	projectiles.append({
		"weapon": w["name"], "kind": kind, "from": e.id, "to": t.id, "damage": total, "speed": speed,
		"x": e.x, "y": e.y, "tx": aim.x, "ty": aim.y, "heading": e.turret_heading, "age": 0,
	})


func _projectiles_step() -> void:
	var keep := []
	for p in projectiles:
		p["age"] = int(p["age"]) + 1
		var t: Ent = by_id.get(p["to"])
		if str(p["kind"]) == "Missile" and t != null and t.alive:
			p["tx"] = t.x
			p["ty"] = t.y
		var pos := Vector2(float(p["x"]), float(p["y"]))
		var goal := Vector2(float(p["tx"]), float(p["ty"]))
		var to := goal - pos
		var dist := to.length()
		if dist <= float(p["speed"]) or int(p["age"]) > 200:
			p["x"] = goal.x
			p["y"] = goal.y
			var shooter: Ent = by_id.get(p["from"])
			var hit: bool = t != null and t.alive and (str(p["kind"]) == "Missile" or range_to_point(t, goal) <= 1.0)
			_impact(t if hit else null, int(p["damage"]), shooter, str(p["weapon"]), goal, hit)
			continue
		var step: Vector2 = to / dist * float(p["speed"])
		p["x"] = pos.x + step.x
		p["y"] = pos.y + step.y
		p["heading"] = step.angle()
		keep.append(p)
	projectiles = keep


static func range_to_point(t: Ent, p: Vector2) -> float:
	if t.kind == Kind.BUILDING:
		var dx := maxf(maxf(t.cx - p.x, 0.0), p.x - (t.cx + t.w))
		var dy := maxf(maxf(t.cy - p.y, 0.0), p.y - (t.cy + t.h))
		return sqrt(dx * dx + dy * dy)
	return t.center().distance_to(p)


func _impact(t: Ent, damage: int, by: Ent, weapon: String, at: Vector2, hit: bool) -> void:
	events.append({"kind": "impact", "weapon": weapon, "x": at.x, "y": at.y, "hit": hit, "target": t.id if t != null else -1})
	if hit and t != null:
		_damage(t, damage, by)


func _damage(t: Ent, amount: int, by: Ent) -> void:
	if amount <= 0 or not t.alive:
		return
	if t.role == "infantry":
		# TakeCover: every roster weapon carries TriggerProne and Prone50Percent
		if t.prone_ticks > 0:
			amount = amount / 2
		t.prone_ticks = PRONE_TICKS
	t.hp -= amount
	events.append({"kind": "hit", "id": t.id, "amount": amount, "x": t.x, "y": t.y})
	if t.kind == Kind.BUILDING and t.role != "wall" and t.hp < t.max_hp and not t.repairing:
		_start_repair(t)
	if by != null and by.alive and by.side != t.side:
		# return fire: an idle unit shot from anywhere turns on its attacker (AllowMove: it will walk there)
		if t.kind == Kind.UNIT and t.target < 0 and t.order in ["idle", "move"] and can_hit(t, by):
			t.target = by.id
		if t.kind == Kind.BUILDING and t.role != "wall" and not by.airborne():
			bots[t.side].respond_to_attack(by.id)
	if t.hp <= 0:
		t.hp = 0
		_kill(t, by)


func _start_repair(b: Ent) -> void:
	if credits[b.side] <= 0:
		return
	b.repairing = true
	b.repair_ticks = 0


func _kill(t: Ent, by: Ent, crushed: bool = false) -> void:
	t.alive = false
	t.repairing = false
	var lost: Dictionary = stats["lost"][t.side]
	lost[t.role] = int(lost.get(t.role, 0)) + 1
	events.append({"kind": "destroyed", "id": t.id, "side": t.side, "role": t.role, "x": t.x, "y": t.y, "by": by.id if by != null else -1, "crushed": crushed})
	if t.kind == Kind.BUILDING:
		for i in t.w:
			for j in t.h:
				var c := Vector2i(t.cx + i, t.cy + j)
				_blocked.erase(c)
				if c.x >= 0 and c.y >= 0 and c.x < width and c.y < height:
					_astar_foot.set_point_solid(c, false)
					_astar_track.set_point_solid(c, false)
		if t.role == "pad":
			var s: Dictionary = slots[t.side][t.slot]
			var a: Ent = by_id.get(s["aircraft"])
			if a != null and a.alive and a.air in [Air.READY, Air.REARMING]:
				_kill(a, by)
			events.append({"kind": "pad_lost", "side": t.side, "slot": t.slot, "pads_alive": pads_alive(t.side)})
		elif t.role in ["factory", "barracks", "main"]:
			events.append({"kind": "producer_lost", "side": t.side, "role": t.role})
	elif t.kind == Kind.AIRCRAFT:
		events.append({"kind": "aircraft_lost", "side": t.side, "slot": t.slot, "id": t.id})


# ---------------------------------------------------------------- movement (spec 5)

func _grid_for(e: Ent) -> AStarGrid2D:
	return _astar_track if e.crushes_walls else _astar_foot


func _cell_of(p: Vector2) -> Vector2i:
	return Vector2i(clampi(int(floor(p.x)), 0, width - 1), clampi(int(floor(p.y)), 0, height - 1))


## Cell-grid pathfinding with waypoint following. Tracked vehicles turn in place (TurnSpeed 20) before moving;
## infantry turn instantly. Vehicles crush enemy infantry and sandbags they drive onto.
func _move_toward(e: Ent, goal: Vector2, keep_turret: bool = false) -> void:
	var p := e.center()
	if p.distance_to(goal) < 0.08:
		e.moving = false
		e.path = PackedVector2Array()
		return
	if e.wait_ticks > 0:
		e.moving = false
		return
	var goal_cell := _cell_of(goal)
	e.repath -= 1
	if e.path.is_empty() or e.path_goal != goal_cell or e.repath <= 0 or e.stuck > BLOCKED_WAIT_TICKS:
		_plan_path(e, goal_cell)
	if e.path.is_empty():
		e.moving = false
		e.stuck += 1
		_separate(e)
		return
	var waypoint: Vector2 = e.path[e.path_index]
	var to := waypoint - p
	var dist := to.length()
	var dir := to / dist if dist > 0.0001 else Vector2.RIGHT
	var desired := dir.angle()
	if e.turn_speed < TAU and absf(angle_difference(e.heading, desired)) > 0.05:
		e.heading = _turn(e.heading, desired, e.turn_speed)
		if not keep_turret:
			e.turret_heading = e.heading
		e.moving = false
		return
	e.heading = desired
	if not keep_turret:
		e.turret_heading = e.heading
	var speed := e.speed * (0.5 if e.prone_ticks > 0 else 1.0)
	var step := dir * minf(speed, dist)
	if _try_step(e, step):
		e.stuck = 0
		e.moving = true
		if e.center().distance_to(waypoint) < 0.05:
			e.path_index += 1
			if e.path_index >= e.path.size():
				e.path = PackedVector2Array()
	else:
		e.stuck += 1
		e.moving = false
	_separate(e)


func _plan_path(e: Ent, goal_cell: Vector2i) -> void:
	e.path_goal = goal_cell
	e.repath = REPATH_TICKS
	e.stuck = 0
	var grid := _grid_for(e)
	var from := _cell_of(e.center())
	var to := goal_cell
	if grid.is_point_solid(to):
		to = _nearest_open_cell(grid, to, from)
	if grid.is_point_solid(from):
		from = _nearest_open_cell(grid, from, to)
	var cells := grid.get_point_path(from, to, true)
	e.path = PackedVector2Array()
	e.path_index = 0
	for c in cells:
		e.path.append(Vector2(c.x + 0.5, c.y + 0.5))
	if e.path.size() > 1 and e.center().distance_to(e.path[0]) < 0.6:
		e.path_index = 1
	if e.path.size() <= e.path_index:
		e.path = PackedVector2Array()


func _nearest_open_cell(grid: AStarGrid2D, target: Vector2i, from: Vector2i) -> Vector2i:
	var best := target
	var best_d := INF
	for r in range(1, 8):
		for dx in range(-r, r + 1):
			for dy in range(-r, r + 1):
				if absi(dx) != r and absi(dy) != r:
					continue
				var c := Vector2i(target.x + dx, target.y + dy)
				if c.x < 0 or c.y < 0 or c.x >= width or c.y >= height or grid.is_point_solid(c):
					continue
				var d := float((c - from).length_squared()) + float(r) * 0.01
				if d < best_d:
					best_d = d
					best = c
		if best_d < INF:
			return best
	return best


func _try_step(e: Ent, step: Vector2) -> bool:
	var nx := e.x + step.x
	var ny := e.y + step.y
	if nx < 0.2 or nx > width - 0.2 or ny < 0.2 or ny > height - 0.2:
		return false
	var cell := Vector2i(int(floor(nx)), int(floor(ny)))
	var blocker_id: int = int(_blocked.get(cell, -2))
	if blocker_id != -2:
		var blocker: Ent = by_id.get(blocker_id)
		if blocker != null and blocker.alive and blocker.role == "wall" and e.crushes_walls and blocker.side != e.side:
			_kill(blocker, e, true)  # tracked vehicles crush sandbags
		else:
			return false
	e.x = nx
	e.y = ny
	if e.crushes_infantry:
		for id in _neighbours(e.center()):
			var o: Ent = by_id[id]
			if o.alive and o.side != e.side and o.role == "infantry" and o.center().distance_to(e.center()) < 0.35:
				_kill(o, e, true)
	return true


## Soft separation. A unit on the move slips past stationary friends (OpenRA packs five infantry into a cell and
## nudges idle blockers aside), so the rear ranks of a squad reach the fight instead of queueing behind the front.
func _separate(e: Ent) -> void:
	var p := e.center()
	var push := Vector2.ZERO
	for id in _neighbours(p):
		if id == e.id:
			continue
		var o: Ent = by_id[id]
		var d := p - o.center()
		var min_d := e.radius + o.radius
		if o.side == e.side and e.moving:
			min_d *= 0.5 if o.moving else 0.25
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


# ---------------------------------------------------------------- buildings with weapons

func _building_step(b: Ent) -> void:
	if b.weapons.is_empty():
		return
	_tick_weapons(b)
	if b.firing > 0:
		b.firing -= 1
	b.scan_timer -= 1
	var t: Ent = by_id.get(b.target)
	if t != null and (not target_valid(b, t) or range_to(b, t) > max_range(b)):
		t = null
		b.target = -1
	if t == null and b.scan_timer <= 0:
		b.scan_timer = rng.randi_range(SCAN_MIN, SCAN_MAX - 1)
		var found := scan_for_target(b, max_range(b))
		if found >= 0:
			b.target = found
			t = by_id[found]
	if t == null:
		return
	_engage(b, t)


# ---------------------------------------------------------------- aircraft (spec 2, 3.6)

func _aircraft_step(a: Ent) -> void:
	_tick_weapons(a)
	if a.firing > 0:
		a.firing -= 1
	var s: Dictionary = slots[a.side][a.slot]
	var pad: Ent = by_id.get(s["pad"])
	var pad_ok := pad != null and pad.alive
	match a.air:
		Air.READY:
			return
		Air.REARMING:
			if not pad_ok:
				return
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
				a.order = "idle"
				events.append({"kind": "returning", "side": a.side, "slot": a.slot, "id": a.id})
				return
			var t: Ent = by_id.get(a.order_target) if a.order == "attack" else null
			if t != null and not target_valid(a, t):
				t = null
				a.order = "idle"
				a.order_target = -1
			a.target = t.id if t != null else -1
			if t == null:
				# no order: hover where the air squad put us (flee spot) or hold over the forward position
				var hold: Vector2 = a.order_pos if a.order == "move" else mirrored(Vector2(float(rules.battlefield.get("air_hold", [12, 5])[0]) + 0.5, float(rules.battlefield.get("air_hold", [12, 5])[1]) + 0.5), a.side)
				_fly_toward(a, hold, 0.4)
				return
			var d := range_to(a, t)
			var rmax := max_range_vs(a, t)
			var rmin := min_range_vs(a, t)
			if t.is_mobile():
				rmax = maxf(rmax - RANGE_MARGIN, rmin + 0.2)
			if d > rmax:
				_fly_toward(a, t.center(), rmax)
			elif d < rmin:
				_fly_toward(a, a.center() + (a.center() - t.center()).normalized(), 0.0)
			else:
				var aim := (t.center() - a.center()).angle()
				a.heading = _turn(a.heading, aim, a.turn_speed)
				if absf(angle_difference(a.heading, aim)) <= _wangle_to_rad(80):
					for w in a.weapons:
						var def: Dictionary = w["def"]
						if t.targetable_as() in def.get("valid_targets", []) and d <= float(def["range"]) and d >= float(def.get("min_range", 0.0)):
							_fire(a, w, t)
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
			if pad_ok:
				a.air = Air.RETURNING
				return
			var wait: Array = rules.battlefield.get("air_wait", [1, 5])
			_fly_toward(a, mirrored(Vector2(float(wait[0]) + 0.5, float(wait[1]) + 0.5), a.side), 0.3)


func _fly_toward(a: Ent, goal: Vector2, stop_within: float) -> bool:
	var to := goal - a.center()
	var dist := to.length()
	if dist <= stop_within:
		return true
	var step := minf(a.speed, dist - stop_within)
	var dir := to / dist
	a.heading = _turn(a.heading, dir.angle(), a.turn_speed)
	a.x += dir.x * step  # CanSlide: moves along the desired direction while the body rotates
	a.y += dir.y * step
	a.moving = true
	return a.center().distance_to(goal) <= stop_within


# ---------------------------------------------------------------- repair and outcome

## OpenRA RepairableBuilding at the pinned commit: every RepairInterval ticks restore min(RepairStep, missing HP),
## charging max(1, hp * RepairPercent * value / (MaxHP * 100)) with integer arithmetic; when the side cannot pay,
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


## Weapon power as AttackOrFleeFuzzy computes it (spec 1.6).
static func attack_power(e: Ent) -> int:
	var power := 0
	for w in e.weapons:
		var def: Dictionary = w["def"]
		var burst := int(def.get("burst", 1))
		var total_reload := int(def.get("reload", 20)) + clampi(int(def.get("burst_delay", 5)) * (burst - 1), 1, 200)
		for wh in def.get("warheads", []):
			if wh.get("type", "") == "SpreadDamage":
				power += int(wh.get("damage", 0)) * burst / total_reload * 100
	return power
