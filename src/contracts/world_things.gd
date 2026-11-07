class_name WorldThings
extends RefCounted
## The port an activity stages itself through (CONTRACTS.md 10, ruling 38): its things, its people, its feedback, its set pieces. The host (the stage, engine package A8) hands one to
## the activity in `setup` as ctx["world"]; this class is the RECORDING STUB the tests and tools use, and it fixes the signatures. NOTE: the cloakroom branch (wip/play-cloakroom) is writing
## the same file; this copy was made from the brief's signatures (`set_things(arr)`, `people(id, state, t0, dur)`, `feedback(thing, kind, t)`) before the merge. Keep the cloakroom's
## on a conflict and add `piece_on`, `piece_off` and `piece_pulse` below to it if it lacks them (the bar's shelf glasses are pieces turned on as drinks are served).
##
## People states the host's crowd knows: idle, look, cheer, clap, hands_up, waiting, happy, impatient, and the bar's frown and raise_glass.

var things: Array = []  # the last set_things (each {id, sprite, at, sector, size, frame, ...})
var things_log: Array = []  # [{t?, things}] one entry per set_things that changed anything
var people_log: Array = []  # [{id, state, t0, dur}]
var feedback_log: Array = []  # [{thing, kind, t}]
var piece_log: Array = []  # [{piece, op: on | off | pulse, t, bars?}]


func set_things(arr: Array) -> void:
	if arr == things:
		return
	things = arr.duplicate(true)
	things_log.append(things)


func people(id: String, state: String, t0: float, dur: float = 0.0) -> void:
	people_log.append({"id": id, "state": state, "t0": t0, "dur": dur})


func feedback(thing: String, kind: String, t: float) -> void:
	feedback_log.append({"thing": thing, "kind": kind, "t": t})


func piece_on(piece: String, t: float) -> void:
	piece_log.append({"piece": piece, "op": "on", "t": t})


func piece_off(piece: String, t: float) -> void:
	piece_log.append({"piece": piece, "op": "off", "t": t})


func piece_pulse(piece: String, t: float, bars: float = 2.0) -> void:
	piece_log.append({"piece": piece, "op": "pulse", "t": t, "bars": bars})


## The last state a person was directed to ("" never).
func state_of(id: String) -> String:
	for i in range(people_log.size() - 1, -1, -1):
		if str(people_log[i]["id"]) == id:
			return str(people_log[i]["state"])
	return ""
