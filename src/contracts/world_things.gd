class_name WorldThings
extends RefCounted
## The interface an activity drives the room through (CONTRACTS.md 10, ruling 38), until the engine's StoryWorld.set_dynamic_things (package A8) lands. The host gives an activity
## an object with these three methods (`ctx["world"]`); this class is the recording stand-in the tests use, and the shape the real adapter must answer:
##   set_things(arr)               the activity's dynamic things now: [{id, sprite, at: [x, z], sector, size: [w_m, h_m], frame, y?, anchor?}] (replaces the last list)
##   people(id, state, t0, dur)    direct the crowd actor `id` (customer, customer_<k>, attendant) into `state` (waiting | happy | impatient | clap | hands_up | idle) from song time t0 for dur seconds (0: until changed)
##   piece_on/off(piece, t), piece_pulse(piece, t, bars)   switch a map piece's lit state (StoryStage piece_on/piece_off/piece_pulse) at song time t
##   feedback(thing, kind, t)      a short in-world cue attached to a thing or piece: kind tick | cross | glow; the host draws it at the thing's screen point
## Everything is recorded in arrays so a test reads what the activity asked for.

var things: Array = []  # the current list
var things_log: Array = []  # every set_things call (a copy of the list), in order
var people_log: Array = []  # [{id, state, t0, dur}]
var feedback_log: Array = []  # [{thing, kind, t}]
var piece_log: Array = []  # [{piece, op: on | off | pulse, t, bars?}] (the bar's shelf glasses: piece_on per served drink, piece_pulse at the payoff)


func set_things(arr: Array) -> void:
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


## The last state asked of actor `id` ("" none yet).
func state_of(id: String) -> String:
	for i in range(people_log.size() - 1, -1, -1):
		if str(people_log[i]["id"]) == id:
			return str(people_log[i]["state"])
	return ""


func thing(id: String) -> Dictionary:
	for t: Dictionary in things:
		if str(t["id"]) == id:
			return t
	return {}
