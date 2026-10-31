class_name DefenseAi
extends RefCounted
## Order logic for the one-sided defense (missions). Side 0 groups hold their defense point: they stand there,
## fight what comes within weapon range, and when a fight drags them past the leash they drop it and walk home
## (the limited pursuit). Side 1 wave units attack-move via their defense point and then to their objective,
## fighting what they meet on the way. The duel's Rush AI (bot_ai.gd) is not involved.

const THINK_EVERY := 5  # ticks between order checks
const HOME_TOLERANCE := 1.6
const VIA_REACHED := 3.0  # a crowd around the via point never gets within a cell of its centre
const SORTIE_CELLS := 16.0  # how far from home defenders go after an enemy shelling their point from beyond the leash

var sim: BattleSim


func setup(p_sim: BattleSim) -> void:
	sim = p_sim


func tick() -> void:
	if sim.tick_count % THINK_EVERY != 0:
		return
	for e in sim.entities:
		if not e.alive or e.kind != BattleSim.Kind.UNIT:
			continue
		if e.side == 0 and e.group >= 0:
			_defender(e)
		elif e.side == 1:
			_attacker(e)


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
	var obj: BattleSim.Ent = sim.get_entity(e.objective)
	if e.stage == 0 and (e.via == Vector2.ZERO or e.center().distance_to(e.via) <= VIA_REACHED):
		e.stage = 1
		if obj != null and obj.alive:
			e.order = "attack_move"
			e.order_pos = obj.center()
		return
	if e.stage == 0:
		if e.order == "idle":
			e.order = "attack_move"
			e.order_pos = e.via
		return
	if obj != null and obj.alive and e.order == "idle":
		e.order = "attack_move"
		e.order_pos = obj.center()
