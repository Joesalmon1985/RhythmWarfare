class_name RunWorldPort
extends WorldThings
## The run's WorldThings (CONTRACTS.md 10): what an activity is handed as ctx["world"] in a run. Every call is recorded as the stub records it, then carried out by the
## host (RunMinigameHost): the things reach the active world's stage, the people its crowd, the feedback the host's feedback layer, the pieces the stage's piece switches.

var host: RefCounted  # RunMinigameHost (untyped: the two refer to each other)


func _init(p_host: RefCounted = null) -> void:
	host = p_host


func set_things(arr: Array) -> void:
	super.set_things(arr)
	if host != null:
		host.call("set_things", arr)


func people(id: String, state: String, t0: float, dur: float = 0.0) -> void:
	super.people(id, state, t0, dur)
	if host != null:
		host.call("people", id, state, t0, dur)


func feedback(thing: String, kind: String, t: float) -> void:
	super.feedback(thing, kind, t)
	if host != null:
		host.call("feedback", thing, kind, t)


func piece_on(piece: String, t: float) -> void:
	super.piece_on(piece, t)
	_piece("piece_on", piece, t, {})


func piece_off(piece: String, t: float) -> void:
	super.piece_off(piece, t)
	_piece("piece_off", piece, t, {})


func piece_pulse(piece: String, t: float, bars: float = 2.0) -> void:
	super.piece_pulse(piece, t, bars)
	_piece("piece_pulse", piece, t, {"bars": bars})


func _piece(action: String, piece: String, t: float, extra: Dictionary) -> void:
	if host != null:
		var args := {"piece": piece}
		args.merge(extra)
		host.call("stage_action", {"t0": t, "action": action, "args": args})
