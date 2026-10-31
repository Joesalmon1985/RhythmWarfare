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
const SPLASH_MIN_SPREAD := 0.2       # warheads with a smaller Spread (rifles, cannons) hit one actor only
const SPLASH_FALLOFF := [100, 37, 14, 5, 0]  # SpreadDamage Falloff defaults at 0, 1, 2, 3, 4 x Spread

enum Kind { UNIT, BUILDING, AIRCRAFT }
enum Air { READY, SORTIE, RETURNING, LANDING, REARMING, WAITING, DEAD }

## One actor in the world.
class Ent:
	var id := 0
	var kind := Kind.UNIT
	var actor := ""      # actor id (1tnk, jeep, e1, e3, heli, hpad, pbox...)
	var role := ""       # roster role: tank (any war-factory vehicle), infantry (any barracks unit), aircraft, pad, main,
	                     # factory, barracks, power, dome, depot, wall (sandbag), brick (brick wall), turret, pillbox, sam
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
	var crushes_walls := false        # sandbags (Locomotor Crushes: wall)
	var crushes_heavy_walls := false  # brick walls (Crushes: heavywall; only the mammoth tank)
	var has_turret := true            # AttackTurreted: aims with the turret; otherwise the body turns to aim
	var target_types: Array = []
	var hits_ground := false  # any weapon valid against GroundActor (precomputed at spawn)
	var hits_air := false     # any weapon valid against AirborneActor
	var is_wall := false
	# orders (from BotAi)
	var order := "idle"    # idle | move | attack_move | attack
	var order_pos := Vector2.ZERO
	var order_target := -1
	var resume_attack_move := false
	var squad := -1
	var wait_ticks := 0
	# defense mode (DefenseAi): a player unit belongs to a production group holding a defense point; an enemy
	# wave unit walks via a defense point to an objective
	var group := -1
	var home := Vector2.ZERO
	var leash := 6.0
	var objective := -1      # entity id of the objective a wave unit is attacking
	var via := Vector2.ZERO
	var defenses_only := false  # wave units fight units, defensive structures and their objective, not every building
	var socket := -1           # mission defenses: index into BattleSim.sockets
	var reinforced := false    # a capacity reward raised this defense's health once
	var stage := 0           # wave route stage: 0 walking to the via point, 1 walking to the objective
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
var spawn_queue: Array = []  # per side: pending units [{role, actor}]
var producer_ids: Array = []  # per side: role -> id
var stats: Dictionary = {}
var projectiles: Array = []  # {weapon, kind, from, to, damage, speed, x, y, tx, ty, heading, age, types}
var bots: Array = []      # BotAi per side (duel only)
## Defense mode (data/battlefields/defense_01.json): one base, required objectives, defense points, wave entries.
var defense := false
var objectives: Array = []       # [{id, role, ent: entity id, required}]
var defense_points: Array = []   # [{id, pos: Vector2}]
var entries: Dictionary = {}     # entry id -> Vector2
var defense_ai: DefenseAi
var groups: Dictionary = {}      # group id -> {point, size, units: Array[int], side}
var leash_cells := 6.0
## Missions (schema 3): prepared sockets for rewarded buildings and the rewards waiting for their construction delay.
var sockets: Array = []          # [{id, point, order, x, y, ent: entity id or -1, reserved: bool}]
var sockets_per_point := 5
var pending_rewards: Array = []  # [{id, ready_tick, start_tick, kind, reward, point, socket, label}] in ready order
var units_per_point := 6
var reinforce_factor := 1.5
var _reward_seq := 0
var _group_seq := 0
## Missions: wave units attack defensive structures on their way (schema 2 waves ignored every building but their goal).
var waves_fight_defenses := false
var profile: Dictionary = {"grid_spawn": 0, "bots": 0, "units": 0, "aircraft": 0, "buildings": 0, "entity_loop_overhead": 0, "projectiles_repair": 0, "ticks": 0, "move": 0, "engage": 0, "scan": 0}
var rng := RandomNumberGenerator.new()
var _blocked: Dictionary = {}  # Vector2i -> building id, or -1 for terrain
var _grid: Dictionary = {}     # Vector2i -> Array[int] unit ids (rebuilt each tick)
var _grid_side: Array = [{}, {}]  # per side: Vector2i -> Array[int] unit ids (rebuilt each tick)
var _aim_count: Dictionary = {}  # entity id -> how many enemies currently target it (rebuilt each tick)
var _static_targets: Array = []  # alive buildings and aircraft (rebuilt each tick; they are few)
var _astar_foot := AStarGrid2D.new()   # infantry: walls block
var _astar_track := AStarGrid2D.new()  # tracked vehicles: sandbag walls are crushed, not avoided
var _next_id := 1
var _airfield_limit := 5
var _aircraft_limit := 5
var _tank_per_kick := 1
var _infantry_per_snare := 5
var _vehicle_cycle: Array = []    # roster vehicle_cycle: the actor each successive kick produces, round robin
var _infantry_pattern: Array = [] # roster infantry_pattern: each snare takes the next infantry_per_snare entries
var _vehicle_index: Array[int] = [0, 0]
var _infantry_index: Array[int] = [0, 0]


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
	_vehicle_cycle = []
	for a in rules.vehicle_cycle:
		if rules.actors.has(str(a)):
			_vehicle_cycle.append(str(a))
	if _vehicle_cycle.is_empty():
		_vehicle_cycle = [rules.actor_id_for_role("tank")]
	_infantry_pattern = []
	for a in rules.infantry_pattern:
		if rules.actors.has(str(a)):
			_infantry_pattern.append(str(a))
	if _infantry_pattern.is_empty():
		_infantry_pattern = [rules.actor_id_for_role("infantry")]
	_vehicle_index = [0, 0]
	_infantry_index = [0, 0]
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
		"units": [{}, {}], "lost": [{}, {}], "air_busy": [0, 0], "blocked": [{}, {}], "squads": [0, 0], "rushes": [0, 0], "flees": [0, 0]}
	slots = [[], []]
	spawn_queue = [[], []]
	producer_ids = [{}, {}]
	for side in SIDES:
		for i in _airfield_limit:
			slots[side].append({"pad": -1, "aircraft": -1, "used": false, "origin": Vector2i.ZERO})
	var initial_pads := int(level_rules.get("initial_airfields", 0))
	defense = str(bf.get("mode", "")) == "defense"
	objectives = []
	defense_points = []
	entries = {}
	groups = {}
	defense_ai = null
	leash_cells = float(bf.get("leash_cells", 6.0))
	for side in (1 if defense else SIDES):
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
	if defense:
		for o in bf.get("objectives", []):
			var ent: Ent = by_id.get(producer_ids[0].get(str(o["role"]), -1))
			if ent == null:
				for e in entities:
					if e.role == str(o["role"]) and e.side == 0:
						ent = e
						break
			objectives.append({"id": str(o["id"]), "role": str(o["role"]), "ent": ent.id if ent != null else -1, "required": bool(o.get("required", true))})
		var hp_override: Dictionary = level_rules.get("objective_hp", {})
		var required: Array = level_rules.get("required_objectives", [])
		if not required.is_empty():
			for o in objectives:
				o["required"] = required.has(o["id"]) or o["id"] == "command_core"
		for o in objectives:  # a level may give its objective less health than the OpenRA building (balance data)
			var ent: Ent = by_id.get(o["ent"])
			if ent != null and hp_override.has(o["id"]):
				ent.hp = int(hp_override[o["id"]])
				ent.max_hp = ent.hp
		for dp in bf.get("defense_points", []):
			defense_points.append({"id": str(dp["id"]), "pos": Vector2(float(dp["x"]) + 0.5, float(dp["y"]) + 0.5)})
		for en in bf.get("entries", []):
			entries[str(en["id"])] = Vector2(float(en["x"]) + 0.5, float(en["y"]) + 0.5)
		sockets = []
		pending_rewards = []
		_reward_seq = 0
		_group_seq = 0
		waves_fight_defenses = bf.has("sockets")
		sockets_per_point = int(level_rules.get("sockets_per_point", 5))
		var caps: Dictionary = MissionRules.data().get("capacity", {})
		units_per_point = int(level_rules.get("units_per_point", caps.get("units_per_point", 6)))
		reinforce_factor = float(caps.get("reinforce_factor", 1.5))
		for sk in bf.get("sockets", []):
			if int(sk["order"]) < sockets_per_point:
				sockets.append({"id": str(sk["id"]), "point": int(sk["point"]), "order": int(sk["order"]), "x": int(sk["x"]), "y": int(sk["y"]), "ent": -1, "reserved": false})
		for wl in level_rules.get("walls", []):  # mission cover: [x, y] cells of sandbag walls (never on a route; the build checks)
			_spawn_building(0, "wall", int(wl[0]), int(wl[1]), 1, 1)
		for pb in level_rules.get("prebuilt", []):  # defenses standing at the start: {"reward": "pillbox", "socket": "s1_1"}
			for i in sockets.size():
				if sockets[i]["id"] == str(pb["socket"]):
					_build_at_socket(i, str(MissionRules.reward(str(pb["reward"])).get("role", "pillbox")))
		defense_ai = DefenseAi.new()
		defense_ai.setup(self)
	else:
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
			var vehicles: Array = []
			for i in _tank_per_kick:
				var actor: String = _vehicle_cycle[_vehicle_index[side] % _vehicle_cycle.size()]
				_vehicle_index[side] += 1
				spawn_queue[side].append({"role": "tank", "actor": actor})
				vehicles.append(actor)
			stats["produced"][side]["tank"] += _tank_per_kick
			return {"action": action, "result": "queued", "count": _tank_per_kick, "actors": vehicles}
		"snare":
			if not producer_alive(side, "barracks"):
				_count_blocked(side, action)
				return {"action": action, "result": "no_barracks"}
			var squad: Array = []
			for i in _infantry_per_snare:
				var actor: String = _infantry_pattern[_infantry_index[side] % _infantry_pattern.size()]
				_infantry_index[side] += 1
				spawn_queue[side].append({"role": "infantry", "actor": actor})
				squad.append(actor)
			stats["produced"][side]["infantry"] += _infantry_per_snare
			return {"action": action, "result": "queued", "count": _infantry_per_snare, "actors": squad}
		"bass":
			return _bass_action(side)
	return {"action": action, "result": "unknown"}


## The producer building an actor needs: its OpenRA production queue decides (vehicles need the war factory,
## infantry the barracks, aircraft a pad). Empty for anything not produced by a building.
func producer_role_for(actor: String) -> String:
	match str(rules.actors.get(actor, {}).get("queue", "")):
		"Infantry":
			return "barracks"
		"Vehicle":
			return "factory"
		"Aircraft":
			return "pad"
	return ""


## Defense mode: queue one production group (a recipe step) for the player. Every unit needs its producer alive;
## otherwise nothing is queued and the caller must not advance any counter. The group walks to its defense point
## (`point` indexes defense_points) and stays together there.
func produce_group(side: int, units: Array, group_id: int, point: int) -> Dictionary:
	if not outcome.is_empty():
		return {"result": "ended"}
	var expanded: Array = []
	for u in units:
		for i in int(u["count"]):
			expanded.append(str(u["actor"]))
	for actor in expanded:
		var role := producer_role_for(actor)
		if role.is_empty() or not rules.actors.has(actor):
			return {"result": "unknown_actor", "actor": actor}
		if not producer_alive(side, role):
			_count_blocked(side, "group_" + role)
			return {"result": "no_producer", "missing": role, "actor": actor}
	var idx := point % defense_points.size()
	var pt: Dictionary = defense_points[idx]
	groups[group_id] = {"point": idx, "size": expanded.size(), "units": [], "side": side}
	var k := 0
	for actor in expanded:
		var ang := float(k) / float(maxi(expanded.size(), 1)) * TAU + 0.6
		var ring := 0.7 + 0.5 * float(k % 2)
		var home: Vector2 = pt["pos"] + Vector2(cos(ang), sin(ang)) * ring
		var role := "infantry" if producer_role_for(actor) == "barracks" else "tank"
		spawn_queue[side].append({"role": role, "actor": actor, "group": group_id, "home": home})
		k += 1
		stats["produced"][side]["infantry" if role == "infantry" else "tank"] += 1
	return {"result": "queued", "group_id": group_id, "point": idx, "point_id": pt["id"], "actors": expanded}


## Defense mode: one enemy wave unit appears at an entry (no producer, no queue) and sets off for its objective via
## a defense point. Returns the entity, or null when the entry cell is occupied (the caller retries next tick).
func spawn_wave_unit(actor: String, entry: String, via_point: String, objective_id: String) -> Ent:
	if not entries.has(entry) or not rules.actors.has(actor):
		return null
	var at := _free_spawn_cell(entries[entry], 3)
	if at.x < 0.0:
		return null
	var role := "infantry" if producer_role_for(actor) == "barracks" else "tank"
	var u := _spawn_unit(1, role, at, actor)
	u.defenses_only = true
	u.order = "idle"
	u.stage = 0
	for dp in defense_points:
		if dp["id"] == via_point:
			u.via = dp["pos"]
	for o in objectives:
		if o["id"] == objective_id:
			u.objective = int(o["ent"])
	stats["produced"][1]["infantry" if role == "infantry" else "tank"] += 1
	return u


# ---------------------------------------------------------------- mission rewards (schema 3)

## Queue one sequence reward (data/campaign/rules.json "rewards") for `ready_tick`. The placement is chosen now, so the
## view can show what is being prepared and where: a building takes the first free socket of the approach with the
## fewest defenses (ties: `hint_point`, the approach of the next wave, then the lowest index); a unit holds the point
## with the fewest defenders. At capacity (no free socket, or every point at units_per_point) the reward becomes a
## repair of that approach, or a reinforcement when nothing is damaged. Returns what was scheduled.
func schedule_reward(reward_id: String, ready_tick: int, hint_point: int = -1) -> Dictionary:
	if not outcome.is_empty():
		return {"result": "ended"}
	var def := MissionRules.reward(reward_id)
	var kind := str(def.get("type", ""))
	var entry := {"id": _reward_seq, "ready_tick": maxi(ready_tick, tick_count + 1), "start_tick": tick_count, "reward": reward_id,
		"kind": kind, "point": -1, "socket": -1, "label": str(def.get("name", reward_id)), "capacity": false}
	_reward_seq += 1
	if kind == "build":
		var pt := _pick_point(hint_point, true)
		if pt >= 0:
			for i in sockets.size():
				if int(sockets[i]["point"]) == pt and _socket_free(i):
					sockets[i]["reserved"] = true
					entry["point"] = pt
					entry["socket"] = i
					entry["role"] = str(def.get("role", "pillbox"))
					break
		if entry["socket"] < 0:
			_as_capacity(entry, hint_point)
	elif kind == "unit":
		var pt := _pick_point(hint_point, false)
		if pt >= 0:
			entry["point"] = pt
			entry["actor"] = str(def.get("actor", "e1"))
		else:
			_as_capacity(entry, hint_point)
	elif kind == "repair":
		entry["point"] = _most_damaged_point(hint_point)
	else:
		return {"result": "unknown_reward", "reward": reward_id}
	pending_rewards.append(entry)
	pending_rewards.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["ready_tick"] < b["ready_tick"] or (a["ready_tick"] == b["ready_tick"] and a["id"] < b["id"]))
	var out := entry.duplicate()
	out["result"] = "scheduled"
	events.append({"kind": "reward_scheduled", "entry": out})
	return out


func _as_capacity(entry: Dictionary, hint_point: int) -> void:
	entry["capacity"] = true
	entry["kind"] = "repair"
	entry["point"] = _most_damaged_point(hint_point)
	entry["label"] = "Repair crew"


## The defense point that most live wave units are still walking towards, -1 when none is on its way.
func approaching_point() -> int:
	var counts: Array = []
	counts.resize(defense_points.size())
	counts.fill(0)
	for e in entities:
		if e.alive and e.side == 1 and e.defenses_only and e.stage == 0:
			for i in defense_points.size():
				if defense_points[i]["pos"] == e.via:
					counts[i] += 1
	var best := -1
	for i in counts.size():
		if counts[i] > 0 and (best < 0 or counts[i] > counts[best]):
			best = i
	return best


## Defenses (live or reserved) at an approach.
func defenses_at(point: int) -> int:
	var n := 0
	for i in sockets.size():
		if int(sockets[i]["point"]) == point and not _socket_free(i):
			n += 1
	return n


## Defenders holding a point, counting those queued and those still being prepared.
func units_at(point: int) -> int:
	var n := 0
	for e in entities:
		if e.alive and e.side == 0 and e.kind == Kind.UNIT and e.group >= 0 and groups.has(e.group) and int(groups[e.group]["point"]) == point:
			n += 1
	for q in spawn_queue[0]:
		if q.has("group") and groups.has(int(q["group"])) and int(groups[int(q["group"])]["point"]) == point:
			n += 1
	for p in pending_rewards:
		if p["kind"] == "unit" and int(p["point"]) == point:
			n += 1
	return n


func _socket_free(i: int) -> bool:
	var sk: Dictionary = sockets[i]
	if sk["reserved"]:
		return false
	var e: Ent = by_id.get(int(sk["ent"]))
	return e == null or not e.alive


func _pick_point(hint_point: int, building: bool) -> int:
	var best := -1
	var best_n := 1 << 30
	for pt in defense_points.size():
		var n := defenses_at(pt) if building else units_at(pt)
		var room := false
		if building:
			for i in sockets.size():
				if int(sockets[i]["point"]) == pt and _socket_free(i):
					room = true
					break
		else:
			room = n < units_per_point
		if not room:
			continue
		if n < best_n or (n == best_n and pt == hint_point and best != hint_point):
			best = pt
			best_n = n
	return best


## The approach whose defenses miss the most health; `hint_point` (or the first) when nothing is damaged.
func _most_damaged_point(hint_point: int) -> int:
	var best := hint_point if hint_point >= 0 else 0
	var worst := 0
	for pt in defense_points.size():
		var missing := 0
		for i in sockets.size():
			var e: Ent = by_id.get(int(sockets[i]["ent"]))
			if int(sockets[i]["point"]) == pt and e != null and e.alive:
				missing += e.max_hp - e.hp
		if missing > worst:
			worst = missing
			best = pt
	return best


func _build_at_socket(i: int, role: String) -> Ent:
	var sk: Dictionary = sockets[i]
	var e := _spawn_building(0, role, int(sk["x"]), int(sk["y"]), 1, 1)
	e.socket = i
	sk["ent"] = e.id
	sk["reserved"] = false
	return e


## Rewards whose construction delay has run out take effect at the start of the tick.
func _process_rewards() -> void:
	while not pending_rewards.is_empty() and int(pending_rewards[0]["ready_tick"]) <= tick_count:
		var p: Dictionary = pending_rewards.pop_front()
		var done := {"kind": "reward_done", "reward": p["reward"], "point": p["point"], "label": p["label"], "id": p["id"], "capacity": p["capacity"]}
		match str(p["kind"]):
			"build":
				var e := _build_at_socket(int(p["socket"]), str(p["role"]))
				done["result"] = "built"
				done["x"] = e.x
				done["y"] = e.y
				done["entity"] = e.id
			"unit":
				_group_seq += 1
				var res := produce_group(0, [{"actor": p["actor"], "count": 1}], _group_seq, int(p["point"]))
				done["result"] = "unit" if res["result"] == "queued" else str(res["result"])
				if res["result"] != "queued":
					done.merge(_repair_point(int(p["point"])), true)
			_:
				done.merge(_repair_point(int(p["point"])), true)
		events.append(done)


## Repair every damaged defense of an approach to full (the most damaged approach when this one is whole); when nothing
## is damaged, reinforce the oldest defense that was never reinforced (+50% health). Returns {result, point, count}.
func _repair_point(point: int) -> Dictionary:
	var pt := point
	var damaged: Array = []
	for i in sockets.size():
		var e: Ent = by_id.get(int(sockets[i]["ent"]))
		if e != null and e.alive and e.hp < e.max_hp and int(sockets[i]["point"]) == pt:
			damaged.append(e)
	if damaged.is_empty():
		pt = _most_damaged_point(point)
		for i in sockets.size():
			var e: Ent = by_id.get(int(sockets[i]["ent"]))
			if e != null and e.alive and e.hp < e.max_hp and int(sockets[i]["point"]) == pt:
				damaged.append(e)
	if not damaged.is_empty():
		for e in damaged:
			e.hp = e.max_hp
			e.repairing = false
		return {"result": "repaired", "point": pt, "count": damaged.size()}
	var oldest: Ent = null
	for i in sockets.size():
		var e: Ent = by_id.get(int(sockets[i]["ent"]))
		if e != null and e.alive and not e.reinforced and (oldest == null or e.id < oldest.id):
			oldest = e
	if oldest != null:
		oldest.reinforced = true
		oldest.max_hp = int(round(float(oldest.max_hp) * reinforce_factor))
		oldest.hp = oldest.max_hp
		return {"result": "reinforced", "point": sockets[oldest.socket]["point"], "count": 1, "x": oldest.x, "y": oldest.y}
	return {"result": "full_strength", "point": pt, "count": 0}


## Live rewarded defenses.
func defense_count() -> int:
	var n := 0
	for i in sockets.size():
		var e: Ent = by_id.get(int(sockets[i]["ent"]))
		if e != null and e.alive:
			n += 1
	return n

func objective_hp(id: String) -> int:
	for o in objectives:
		if o["id"] == id:
			var e: Ent = by_id.get(o["ent"])
			return e.hp if e != null and e.alive else 0
	return 0


func objective_max_hp(id: String) -> int:
	for o in objectives:
		if o["id"] == id:
			var e: Ent = by_id.get(o["ent"])
			return e.max_hp if e != null else 1
	return 1


## True while a unit of this role waits in the physical spawn queue (the building shows its production overlay).
func queue_has(side: int, role: String) -> bool:
	for q in spawn_queue[side]:
		if q["role"] == role:
			return true
	return false


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
	_weapon_flags(a)
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
	e.is_defence = role in ["turret", "aa", "sam", "pillbox", "flame"]
	e.radius = maxf(bw, bh) * 0.5
	e.weapons = _make_weapons(def)
	_weapon_flags(e)
	e.is_wall = role in ["wall", "brick"]
	e.has_turret = def.get("abilities", {}).has("AttackTurreted")
	e.heading = 0.0 if side == 0 else PI
	e.turret_heading = e.heading
	e.turret_turn = _wangle_to_rad(48 if role == "turret" else 120)
	e.target_types = ["GroundActor", "Structure"] + (["Defense"] if e.is_defence else []) + (["Wall", "NoAutoTarget"] if e.is_wall else [])
	entities.append(e)
	by_id[e.id] = e
	for i in bw:
		for j in bh:
			var c := Vector2i(bx + i, by + j)
			_blocked[c] = e.id
			if c.x >= 0 and c.y >= 0 and c.x < width and c.y < height:
				_astar_foot.set_point_solid(c, true)
				if role != "wall":
					_astar_track.set_point_solid(c, true)  # sandbags are crushed, not avoided; brick walls block everyone
	return e


## A ground unit of a specific actor. Its class (infantry or vehicle), what it crushes and whether it aims with a
## turret come from the actor's OpenRA locomotor and traits, so a jeep, an artillery piece and a mammoth tank all
## behave as their rules say.
func _spawn_unit(side: int, role: String, at: Vector2, actor: String = "") -> Ent:
	if actor.is_empty():
		actor = rules.actor_id_for_role(role)
	var def: Dictionary = rules.actors.get(actor, {})
	var e := Ent.new()
	e.id = _next_id
	_next_id += 1
	e.kind = Kind.UNIT
	e.actor = actor
	e.role = role
	e.side = side
	e.x = at.x
	e.y = at.y
	e.hp = int(def.get("hp", 1000))
	e.max_hp = e.hp
	e.armor = str(def.get("armor", "None"))
	e.speed = float(def.get("speed", 50)) / WORLD
	var locomotor := str(def.get("locomotor", "foot" if role == "infantry" else "tracked"))
	var crushes: Array = rules.locomotors.get(locomotor, {}).get("crushes", [])
	e.has_turret = def.get("abilities", {}).has("AttackTurreted")
	if locomotor == "foot":
		e.radius = 0.18
		e.turn_speed = TAU  # AlwaysTurnInPlace with TurnSpeed 512: instant
		e.has_turret = false
		e.target_types = ["GroundActor", "Infantry"]
	else:
		e.radius = 0.42
		e.turn_speed = _wangle_to_rad(20)
		e.turret_turn = _wangle_to_rad(28)
		e.crushes_infantry = "infantry" in crushes
		e.crushes_walls = "wall" in crushes
		e.crushes_heavy_walls = "heavywall" in crushes
		e.target_types = ["GroundActor", "Vehicle"]
	e.heading = 0.0 if side == 0 else PI
	e.turret_heading = e.heading
	e.weapons = _make_weapons(def)
	_weapon_flags(e)
	e.scan_timer = rng.randi_range(SCAN_MIN, SCAN_MAX - 1)
	entities.append(e)
	by_id[e.id] = e
	var units: Dictionary = stats["units"][side]
	units[actor] = int(units.get(actor, 0)) + 1
	events.append({"kind": "spawned", "side": side, "role": role, "actor": actor, "id": e.id})
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
	if tick_count % 250 == 0:
		_compact()
	var t0 := Time.get_ticks_usec()
	_rebuild_grid()
	_process_rewards()
	_process_spawn_queues()
	var t1 := Time.get_ticks_usec()
	for bot in bots:
		bot.tick()
	if defense_ai != null:
		defense_ai.tick()
	var t2 := Time.get_ticks_usec()
	var tu := 0
	var ta := 0
	var tb := 0
	for e in entities:
		if not e.alive:
			continue
		var ts := Time.get_ticks_usec()
		match e.kind:
			Kind.UNIT:
				_unit_step(e)
				tu += Time.get_ticks_usec() - ts
			Kind.AIRCRAFT:
				_aircraft_step(e)
				ta += Time.get_ticks_usec() - ts
			Kind.BUILDING:
				_building_step(e)
				tb += Time.get_ticks_usec() - ts
	var t3 := Time.get_ticks_usec()
	_projectiles_step()
	_repair_step()
	_check_outcome()
	var t4 := Time.get_ticks_usec()
	profile["grid_spawn"] += t1 - t0
	profile["bots"] += t2 - t1
	profile["units"] += tu
	profile["aircraft"] += ta
	profile["buildings"] += tb
	profile["entity_loop_overhead"] += (t3 - t2) - tu - ta - tb
	profile["projectiles_repair"] += t4 - t3
	profile["ticks"] += 1


## Drop dead units and aircraft from the entity list (dead buildings stay: the view draws their ruins).
func _compact() -> void:
	var keep: Array[Ent] = []
	for e in entities:
		if e.alive or e.kind == Kind.BUILDING:
			keep.append(e)
		else:
			by_id.erase(e.id)
	entities = keep


func _rebuild_grid() -> void:
	_grid.clear()
	_grid_side[0].clear()
	_grid_side[1].clear()
	_aim_count.clear()
	_static_targets.clear()
	for e in entities:
		if not e.alive:
			continue
		if e.target >= 0:
			_aim_count[e.target] = int(_aim_count.get(e.target, 0)) + 1
		if e.kind == Kind.UNIT:
			var key := e.cell()
			if not _grid.has(key):
				_grid[key] = []
			_grid[key].append(e.id)
			var gs: Dictionary = _grid_side[e.side]
			if not gs.has(key):
				gs[key] = []
			gs[key].append(e.id)
		else:
			_static_targets.append(e)


func _process_spawn_queues() -> void:
	if tick_count % SPAWN_INTERVAL_TICKS != 0:
		return
	var exits: Dictionary = rules.battlefield.get("exits", {})
	var rally_cfg: Array = rules.battlefield.get("rally", [12, 5])
	for side in SIDES:
		var q: Array = spawn_queue[side]
		if q.is_empty():
			continue
		var role: String = q[0]["role"]
		var producer := "factory" if role == "tank" else "barracks"
		if not producer_alive(side, producer):
			q.pop_front()
			_count_blocked(side, "queued_" + role)
			continue
		var ex: Array = exits.get(producer, [8, 4])
		var exit_pos := mirrored(Vector2(float(ex[0]) + 0.5, float(ex[1]) + 0.5), side)
		# OpenRA's Exit spawns on the exit cell or the nearest free cell beside it; the award waits in the
		# physical queue only while every cell around the exit is occupied (never discarded)
		var at := _free_spawn_cell(exit_pos, 2)
		if at.x < 0.0:
			continue
		var entry: Dictionary = q.pop_front()
		var u := _spawn_unit(side, role, at, str(entry.get("actor", "")))
		if entry.has("group"):
			u.group = int(entry["group"])
			u.home = entry["home"]
			u.leash = leash_cells
			if groups.has(u.group):
				groups[u.group]["units"].append(u.id)
			u.order = "move"
			u.order_pos = u.home
			continue
		# leave the factory for the rally point (OpenRA RallyPoint), with a little spread
		var rally := mirrored(Vector2(float(rally_cfg[0]) + 0.5, float(rally_cfg[1]) + 0.5), side)
		rally += Vector2(rng.randf_range(-1.5, 1.5), rng.randf_range(-3.0, 3.0))
		u.order = "move"
		u.order_pos = Vector2(clampf(rally.x, 0.5, width - 0.5), clampf(rally.y, 0.5, height - 0.5))


func _free_spawn_cell(exit_pos: Vector2, max_radius: int) -> Vector2:
	if not _occupied_near(exit_pos, EXIT_BLOCK_RADIUS):
		return exit_pos
	for r in range(1, max_radius + 1):
		for dx in range(-r, r + 1):
			for dy in range(-r, r + 1):
				if absi(dx) != r and absi(dy) != r:
					continue
				var c := Vector2(exit_pos.x + dx, exit_pos.y + dy)
				var cell := Vector2i(int(floor(c.x)), int(floor(c.y)))
				if cell.x < 0 or cell.y < 0 or cell.x >= width or cell.y >= height or _blocked.has(cell):
					continue
				if not _occupied_near(c, EXIT_BLOCK_RADIUS):
					return c
	return Vector2(-1, -1)


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
	return shooter.hits_air if target.airborne() else shooter.hits_ground


static func _weapon_flags(e: Ent) -> void:
	e.hits_ground = false
	e.hits_air = false
	for w in e.weapons:
		var vt: Array = w["def"].get("valid_targets", [])
		if "GroundActor" in vt:
			e.hits_ground = true
		if "AirborneActor" in vt:
			e.hits_air = true


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
	elif e.kind == Kind.BUILDING and waves_fight_defenses:
		# missions only (deviation): a defense measures from its own footprint edge, as its attackers measure to it,
		# so a flame tower and a rifleman of equal range trade fire instead of the rifleman out-reaching the tower
		var dx := maxf(maxf(e.cx - t.x, 0.0), t.x - (e.cx + e.w))
		var dy := maxf(maxf(e.cy - t.y, 0.0), t.y - (e.cy + e.h))
		d = sqrt(dx * dx + dy * dy)
	return d


func target_valid(e: Ent, t: Ent) -> bool:
	return t != null and t.alive and t.side != e.side and can_hit(e, t)


## AutoTarget scan: the closest enemy inside the weapon range that a weapon is valid against; walls never
## (NoAutoTarget); stance AttackAnything (both sides are bots) includes structures.
## Deviation: a target already aimed at by many friends counts as a little farther away, so a hundred units do
## not all shoot the same rifleman while the rest of the enemy stands untouched (overkill).
func scan_for_target(e: Ent, radius: float) -> int:
	var best := -1
	var best_score := INF
	var side := e.side
	var ex := e.x
	var ey := e.y
	var r2 := radius * radius
	if e.hits_ground:
		var enemy_grid: Dictionary = _grid_side[1 - side]
		var r := int(ceil(radius))
		var cx := int(floor(ex))
		var cy := int(floor(ey))
		for i in range(-r, r + 1):
			for j in range(-r, r + 1):
				var list: Array = enemy_grid.get(Vector2i(cx + i, cy + j), [])
				for id in list:
					var o: Ent = by_id[id]
					var ddx: float = o.x - ex
					var ddy: float = o.y - ey
					var d2 := ddx * ddx + ddy * ddy
					if d2 > r2:
						continue
					var score := sqrt(d2) + 0.4 * minf(float(_aim_count.get(o.id, 0)), 8.0)
					if score < best_score:
						best = o.id
						best_score = score
	for o in _static_targets:
		if o.side == side or not o.alive or o.is_wall:
			continue
		if e.defenses_only and o.kind == Kind.BUILDING and o.id != e.objective and not (o.is_defence and waves_fight_defenses):
			continue
		if not (e.hits_air if o.airborne() else e.hits_ground):
			continue
		var d := range_to(e, o)
		if d > radius:
			continue
		var score := d + 0.4 * minf(float(_aim_count.get(o.id, 0)), 8.0)
		if score < best_score:
			best = o.id
			best_score = score
	return best


## Ground units from the spatial grid within `radius` cells, plus every building and aircraft (few of each).
func _candidates_near(p: Vector2, radius: float) -> Array:
	var out: Array = []
	var r := int(ceil(radius))
	var cx := int(floor(p.x))
	var cy := int(floor(p.y))
	for i in range(-r, r + 1):
		for j in range(-r, r + 1):
			var list: Array = _grid.get(Vector2i(cx + i, cy + j), [])
			for id in list:
				out.append(by_id[id])
	out.append_array(_static_targets)
	return out


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
		var ts0 := Time.get_ticks_usec()
		var found := scan_for_target(e, max_range(e))
		profile["scan"] += Time.get_ticks_usec() - ts0
		if found >= 0:
			t = by_id[found]
			e.target = found
	if t != null:
		var ts := Time.get_ticks_usec()
		_engage(e, t)
		if e.moving and e.has_turret:
			_opportunity_fire(e, t)
		profile["engage"] += Time.get_ticks_usec() - ts
		return
	e.firing = 0
	match e.order:
		"move", "attack_move":
			if e.center().distance_to(e.order_pos) <= 0.6:
				e.order = "idle"
				e.moving = false
				e.path = PackedVector2Array()
			else:
				var ts := Time.get_ticks_usec()
				_move_toward(e, e.order_pos)
				profile["move"] += Time.get_ticks_usec() - ts
		_:
			e.moving = false
			if e.turret_heading != e.heading and e.kind == Kind.UNIT and e.has_turret:
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
		elif e.has_turret:
			e.turret_heading = _turn(e.turret_heading, aim, e.turret_turn)
		elif e.kind == Kind.UNIT:
			e.heading = _turn(e.heading, aim, e.turn_speed)  # AttackFrontal: the whole vehicle turns to face the target
			e.turret_heading = e.heading
		else:
			e.turret_heading = aim  # a pillbox fires in any direction
		var aligned := absf(angle_difference(e.turret_heading, aim)) < 0.02 or e.role == "infantry"
		if aligned:
			for w in e.weapons:
				var def: Dictionary = w["def"]
				if t.targetable_as() in def.get("valid_targets", []) and d <= float(def["range"]) and d >= float(def.get("min_range", 0.0)):
					_fire(e, w, t)
		return
	if not e.is_mobile():
		return
	# close in: path toward the target (chase without a leash), stopping `approach` short of a moving one;
	# artillery and rocket launchers inside their minimum range back away instead
	var goal := t.center()
	if d < rmin:
		var away := (e.center() - t.center()).normalized()
		if away == Vector2.ZERO:
			away = Vector2.RIGHT if e.side == 1 else Vector2.LEFT
		goal = e.center() + away * (rmin - d + 0.5)
		goal = Vector2(clampf(goal.x, 0.5, width - 0.5), clampf(goal.y, 0.5, height - 0.5))
	elif t.kind == Kind.BUILDING:
		goal = Vector2(clampf(e.x, t.cx, t.cx + t.w), clampf(e.y, t.cy, t.cy + t.h))
	elif d > approach and approach > 0.5:
		goal = t.center() + (e.center() - t.center()).normalized() * (approach - 0.3)
	_move_toward(e, goal, true)


## AttackFollow OpportunityFire: a turreted unit on the move fires at the closest enemy inside its range even
## while it is chasing something else (no PersistentTargeting bookkeeping; the scan is cheap enough per tick).
func _opportunity_fire(e: Ent, chasing: Ent) -> void:
	if (tick_count + e.id) % 3 != 0:
		return
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
	var total := _damage_against(def, t)
	var aim := t.center()
	e.turret_heading = (aim - e.center()).angle()
	if not e.has_turret and e.kind == Kind.UNIT:
		e.heading = e.turret_heading
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


## Damage of every SpreadDamage warhead of a weapon against one actor's armour, at the centre of the burst.
func _damage_against(def: Dictionary, t: Ent) -> int:
	var total := 0
	for wh in def.get("warheads", []):
		if wh.get("type", "") != "SpreadDamage":
			continue
		if not (t.targetable_as() in wh.get("valid_targets", ["GroundActor"])):
			continue
		total += Rules.damage_versus(wh, t.armor)
	return total


## Largest Spread (cells) among a weapon's damage warheads; below SPLASH_MIN_SPREAD the round hits one actor.
static func weapon_spread(def: Dictionary) -> float:
	var spread := 0.0
	for wh in def.get("warheads", []):
		if wh.get("type", "") == "SpreadDamage":
			spread = maxf(spread, float(wh.get("spread", 0.0)))
	return spread


## SpreadDamage falloff: 100% at the burst, then the Falloff table at every further Spread of distance.
static func splash_percent(distance: float, spread: float) -> int:
	if spread <= 0.0:
		return 100 if distance <= 0.0 else 0
	var k := distance / spread
	var i := int(floor(k))
	if i >= SPLASH_FALLOFF.size() - 1:
		return 0
	var a := float(SPLASH_FALLOFF[i])
	var b := float(SPLASH_FALLOFF[i + 1])
	return int(round(a + (b - a) * (k - float(i))))


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


## A round arrives. Weapons with a wide Spread (grenades, artillery, rockets, flame) burst where they land and hurt
## every enemy inside four Spreads with the falloff table, whether or not the aimed-at actor is still there;
## narrow weapons damage the aimed-at actor only. Deviation from OpenRA: splash never hurts the shooter's own
## side (friendly fire inside a bot-driven blob only punished the side with more artillery).
func _impact(t: Ent, damage: int, by: Ent, weapon: String, at: Vector2, hit: bool) -> void:
	events.append({"kind": "impact", "weapon": weapon, "x": at.x, "y": at.y, "hit": hit, "target": t.id if t != null else -1})
	var def := rules.weapon(weapon)
	var spread := weapon_spread(def)
	if spread < SPLASH_MIN_SPREAD or by == null:
		if hit and t != null:
			_damage(t, damage, by)
		return
	var radius := spread * float(SPLASH_FALLOFF.size() - 1)
	var air_burst := t != null and t.airborne()
	var targets := _candidates_near(at, radius)
	if hit and t != null:
		targets.append(t)  # the aimed-at actor counts even before it is in this tick's grid
	var seen := {}
	for o in targets:
		if seen.has(o.id) or not o.alive or o.side == by.side or o.is_wall:
			continue
		seen[o.id] = true
		if o.airborne() != air_burst:
			continue
		var d := range_to_point(o, at)
		if d > radius:
			continue
		var pct := splash_percent(d, spread)
		if pct <= 0:
			continue
		var amount := (_damage_against(def, o) if o != t else damage) * pct / 100
		if amount > 0:
			_damage(o, amount, by)


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
	if t.kind == Kind.BUILDING and not t.is_wall and t.hp < t.max_hp and not t.repairing:
		_start_repair(t)
	if by != null and by.alive and by.side != t.side:
		# return fire: an idle unit shot from anywhere turns on its attacker (AllowMove: it will walk there)
		if t.kind == Kind.UNIT and t.target < 0 and t.order in ["idle", "move"] and can_hit(t, by):
			t.target = by.id
		if t.kind == Kind.BUILDING and not t.is_wall and not by.airborne() and bots.size() > t.side:
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
		var crushable := blocker != null and blocker.alive and blocker.side != e.side and blocker.is_wall and ((blocker.role == "wall" and e.crushes_walls) or (blocker.role == "brick" and e.crushes_heavy_walls))
		if crushable:
			_kill(blocker, e, true)  # tracked vehicles crush sandbags; only the mammoth tank crushes brick
		else:
			return false
	e.x = nx
	e.y = ny
	if e.crushes_infantry:
		var enemy_grid: Dictionary = _grid_side[1 - e.side]
		var c := e.cell()
		for i in range(-1, 2):
			for j in range(-1, 2):
				for id in enemy_grid.get(Vector2i(c.x + i, c.y + j), []):
					var o: Ent = by_id[id]
					if o.alive and o.role == "infantry" and o.center().distance_to(e.center()) < 0.35:
						_kill(o, e, true)
	return true


## Soft separation. A unit on the move slips past stationary friends (OpenRA packs five infantry into a cell and
## nudges idle blockers aside), so the rear ranks of a squad reach the fight instead of queueing behind the front.
func _separate(e: Ent) -> void:
	if (tick_count + e.id) % 2 == 1:
		return
	var p := e.center()
	var push := Vector2.ZERO
	var checked := 0
	var cxi := int(floor(p.x))
	var cyi := int(floor(p.y))
	for i in range(-1, 2):
		for j in range(-1, 2):
			var list: Array = _grid.get(Vector2i(cxi + i, cyi + j), [])
			for id in list:
				if id == e.id:
					continue
				checked += 1
				if checked > 12:
					break
				var o: Ent = by_id[id]
				var d := p - o.center()
				var min_d := e.radius + o.radius
				if o.side == e.side and e.moving:
					min_d *= 0.5 if o.moving else 0.25
				var len := d.length()
				if len < min_d and len > 0.0001:
					push += d / len * (min_d - len)
				elif len <= 0.0001:
					push += Vector2(0.0, 0.02 * (1 if e.id % 2 == 0 else -1))
	if push != Vector2.ZERO:
		# A column pressing into a wall opening must not be shoved back by its own rear ranks: a moving unit only
		# takes the sideways part of the crowd push, and no push ever exceeds half a step, so the front keeps
		# walking while the mass spreads along the wall (OpenRA cells simply hold five infantry each).
		if e.moving:
			var forward := Vector2(cos(e.heading), sin(e.heading))
			var along := push.dot(forward)
			if along < 0.0:
				push -= forward * along
		var cap := maxf(e.speed * 0.5, 0.01)
		if push.length() > cap:
			push = push.normalized() * cap
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
	if defense:
		for o in objectives:
			var ent: Ent = by_id.get(o["ent"])
			if o["required"] and (ent == null or not ent.alive):
				outcome = "defeat"
				outcome_reason = "objective_destroyed:%s" % o["id"]
				events.append({"kind": "outcome", "outcome": outcome, "reason": outcome_reason, "tick": tick_count})
				return
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
	if defense:
		_check_outcome()  # an objective lost in the final tick still wins over the survival
		if outcome.is_empty():
			outcome = "victory"
			outcome_reason = "survived"
			events.append({"kind": "outcome", "outcome": outcome, "reason": outcome_reason, "tick": tick_count})
		return
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
