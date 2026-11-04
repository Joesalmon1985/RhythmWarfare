class_name RunJourney
extends RefCounted
## Turns the run engine's events into the player's journey: one RunRail per node (kept across a loop, restarted for a new node), the glance and stroll of every
## block, and the walk through the doorway into a new world. Pure logic: events in, stage actions out ({world, t0, action, args}). The run scene hands them to the
## stages; the playtests feed the same events and read the same log, so what they check is what the player sees.

var data: RunData
var rail: RunRail
var node_id := ""
var world := ""
var log: Array = []  # [{phase, block, node, place, kind, role, pos}] one per block decision
var actions: Array = []  # every action emitted, with its world


func _init(p_data: RunData) -> void:
	data = p_data


func on_event(ev: Dictionary, engine: RunEngine) -> Array:
	var out: Array = []
	match str(ev["kind"]):
		"phase_start":
			out = _phase_start(ev, engine)
		"block_result":
			out = _block_result(ev, engine)
	actions.append_array(out)
	return out


func _tag(list: Array, w: String) -> Array:
	var out: Array = []
	for a in list:
		var b: Dictionary = (a as Dictionary).duplicate()
		b["world"] = w
		out.append(b)
	return out


func _phase_start(ev: Dictionary, engine: RunEngine) -> Array:
	var id := str(ev["node"])
	var node: Dictionary = data.nodes[id]
	var w := str(node["world"])
	var t0 := float(ev["t"])
	var first := int(ev["phase"]) == 1
	var changed := w != world
	var out: Array = []
	if id != node_id:  # a loop ("round again") keeps the player where the rail has got to
		rail = RunRail.new()
		rail.setup(id, node, float(data.cfg["timing"]["bpm"]))
	if first:
		out.append({"t0": t0, "action": "player_role", "args": {"role": "dancer"}})
	elif changed:
		out.append_array(rail.arrival(t0, engine.level.notes))
	out.append_array(rail.ambient(t0, int(ev["phase"]), 0, engine.level.notes))
	node_id = id
	world = w
	return _tag(out, w)


func _block_result(ev: Dictionary, engine: RunEngine) -> Array:
	var b := int(ev["block"])
	var notes := engine.level.notes
	var out: Array = rail.step(bool(ev["passed"]), float(ev["t"]), notes)
	var last: Dictionary = rail.visited[rail.visited.size() - 1]
	log.append({"phase": int(ev["phase"]), "block": b, "node": str(ev["node"]), "place": last["place"], "kind": last["kind"], "role": last["role"], "pos": last["pos"]})
	if b < 3:  # the glance and the stroll of the next block
		out.append_array(rail.ambient(engine.t_of(float(b + 1) * engine.timing("block_beats")), int(ev["phase"]), b + 1, notes))
	return _tag(out, world)
