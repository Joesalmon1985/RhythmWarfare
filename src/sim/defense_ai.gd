class_name DefenseAi
extends RefCounted
## Order logic for the one-sided defense (schema 2). Side 0 groups hold their defense point: they stand there,
## fight what comes within weapon range, and when a fight drags them past the leash they drop it and walk home
## (the limited pursuit). Side 1 wave units attack-move via their defense point and then to their objective,
## fighting what they meet on the way. The duel's Rush AI (bot_ai.gd) is not involved.

const THINK_EVERY := 5  # ticks between order checks
const HOME_TOLERANCE := 1.6
const VIA_REACHED := 3.0  # a crowd around the via point never gets within a cell of its centre

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
