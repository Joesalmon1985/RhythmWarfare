class_name WorldThings
extends RefCounted
## The port an activity stages itself through (CONTRACTS.md 10, ruling 38): its things, its people, its feedback, its set pieces. The host hands one to the activity in
## `setup` as ctx["world"] (MinigameController.world_port: the run's RunWorldPort, which extends this class and forwards every call to the stage); this class itself is the
## RECORDING STUB the tests and tools use, and it fixes the signatures:
##   set_things(arr)              the activity's dynamic things now: [{id, sprite, at: [x, z], sector, size: [w_m, h_m], frame, y?, anchor?, grid?}] (replaces the last list;
##                                StoryWorld.set_dynamic_things / StoryDynamicThings say what each key means). An activity may instead implement `things() -> Array`: the host
##                                then reads it every frame while it is seated.
##   people(id, state, t0, dur)   direct crowd actor `id` into `state` (waiting | happy | impatient | frown | beckon | raise_glass, or any crowd state: idle, look, cheer, clap,
##                                hands_up) from song time t0 for dur seconds (0: until changed); StoryCrowd.ACTIVITY_STATES gives the sheet fallbacks
##   feedback(thing, kind, t)     a short in-world cue at a thing's screen point, kind tick | cross | glow, drawn by the host (RunActivityFeedback); `thing` is a dynamic thing,
##                                a map thing or a piece
##   piece_on / piece_off / piece_pulse(piece, t[, bars])   a map piece of the scene switched (StoryStage.apply piece_on / piece_off / piece_pulse)
## Everything is recorded so a test reads what the activity asked for. (Engine package A8 wrote this file; the cloakroom and bar branches wrote copies from the same
## signatures: this one is their union.)

var things: Array = []  # the current list
var things_log: Array = []  # every set_things call that changed the list (a copy), in order
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
