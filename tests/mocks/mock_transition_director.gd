class_name MockTransitionDirector
extends TransitionPort
## Virtual-clock implementation of TransitionPort for tests (INTEGRATION_CONTRACT.md section 8).
## No audio, no engine, no scene tree: advance(dt) moves song_time() and emits every signal in order.
##
## Model (the readings chosen where the contract is open; see also the notes in tests/port_conformance.gd):
##  - A scene has `laps` laps of 64 beats at its own tempo. Laps are numbered from 0. A departure lap is a lap
##    index >= doors_from_lap; the boundary of a departure lap is the end of that lap; its lock point is
##    lock_lead_beats before it. Lock points exist only on departure laps, so doors_closed is never emitted.
##  - The final lap is index max(laps - 1, doors_from_lap). With nothing pending at its lock point the default
##    is locked under a fresh id, or, if the default is {} (or a blend is still running), the scene gets one more lap.
##  - A block is 8 beats (the engine's block). when == &"soonest" takes the first block boundary in a departure
##    lap that is at least lock_lead_beats after the request; a deferral moves it by one block.
##  - request() of a destination in fail_load_ids returns an id and acknowledges it; the request is then closed
##    &"unavailable" on the next advance() (loading takes time). Other requests get destination_ready then, except
##    not_ready_ids, which become ready when they are deferred.
##  - On a switch tempo_changed is emitted (if the tempo differs), then switched, then, when the blend is over,
##    completed (the same call when blend_beats == 0). begin_scene() clears the default (set on every scene entry).
##  - A transition that locks while a blend still runs is deferred with &"blending" (any number of times).

const BEATS_PER_LAP := 64.0
const BLOCK_BEATS := 8.0

## Destinations (by "id") that close as &"unavailable" shortly after request().
var fail_load_ids: Array[String] = []
## Destinations deferred once with &"not_ready"; they then lock with mode &"cut".
var not_ready_ids: Array[String] = []
## Destinations that fail after the lock: the switch lands on fallback_dest with fallback = true.
var fail_after_lock_ids: Array[String] = []
var fallback_dest: Dictionary = {"id": "main/fallback", "path": "main", "node": "fallback", "kind": &"scene", "quest": ""}
## Beats of the incoming scene over which the outgoing music fades; completed fires that long after switched.
var blend_beats: int = 0
## Take "on_miss" of the request's destination when it has one.
var miss_last_block := false
var lock_lead_beats := 3.5
## Optional per-destination scene data: {"main/b": {"bpm": 140.0, "laps": 2, "doors_from_lap": 1}}. Missing
## keys (and unknown destinations) use the constructor's values.
var scene_specs: Dictionary = {}
## Every signal emitted: {"signal": StringName, "args": Array, "t": float}.
var log: Array[Dictionary] = []

var _t := 0.0
var _bpm := 174.0
var _laps := 4
var _doors := 2
var _scene_start := 0.0
var _scene_dest: Dictionary = {}
var _def_bpm := 174.0
var _def_laps := 4
var _def_doors := 2
var _default_dest: Dictionary = {}
var _next_id := 1
var _refusal: StringName = &""
## The one slot: {id, dest, state, ready, soonest, boundary, nr_done, load_pending, taken, plan}, or {}.
var _req: Dictionary = {}
## Switched but not completed: {id, landed, complete_t}, or {}.
var _trans: Dictionary = {}


func _init(bpm_ := 174.0, laps_ := 4, doors_from_lap_ := 2, lock_lead_beats_ := 3.5) -> void:
	_def_bpm = bpm_
	_def_laps = laps_
	_def_doors = doors_from_lap_
	lock_lead_beats = lock_lead_beats_
	_bpm = bpm_
	begin_scene({"id": "main/start", "path": "main", "node": "start", "kind": &"scene", "quest": ""}, bpm_, laps_, doors_from_lap_)


## ---------------------------------------------------------------- scene and clock

## Start a scene at the current song time. Called by the mock on a switch and by a test for the first scene.
func begin_scene(dest: Dictionary, scene_bpm: float, laps: int, doors_from_lap: int) -> void:
	var changed := not is_equal_approx(scene_bpm, _bpm)
	_scene_dest = dest
	_bpm = scene_bpm
	_laps = laps
	_doors = doors_from_lap
	_scene_start = _t
	_default_dest = {}
	if changed:
		_log_emit(&"tempo_changed", [_bpm, beat_s(), _t])
		tempo_changed.emit(_bpm, beat_s(), _t)


## Move the virtual clock by dt seconds, emitting everything that happens on the way, in order.
func advance(dt: float) -> void:
	var target := _t + maxf(dt, 0.0)
	var guard := 0
	while guard < 10000:
		guard += 1
		_resolve_loads()
		var ev := _next_event(target)
		if ev.is_empty():
			break
		_t = maxf(_t, float(ev["t"]))
		var kind: String = ev["kind"]
		if kind == "switch":
			_do_switch()
		elif kind == "complete":
			_do_complete()
		else:
			_do_lock(float(ev["b"]))
	_t = maxf(_t, target)
	_resolve_loads()


func song_time() -> float:
	return _t


func beat_s() -> float:
	return 60.0 / _bpm


func bpm() -> float:
	return _bpm


func lap_beat() -> float:
	var lb := fmod(_t - _scene_start, _lap_s()) / beat_s()
	if lb < 0.0 or lb >= BEATS_PER_LAP - 1e-6:
		return 0.0
	return lb


func next_boundary_t() -> float:
	if not _req.is_empty() and (int(_req["state"]) == State.LOCKED or bool(_req["soonest"])):
		return float(_req["boundary"])
	return _lap_end(_cand_lap())


func lock_t(boundary_t: float) -> float:
	return boundary_t - lock_lead_beats * beat_s()


func selection_open() -> bool:
	return _req.is_empty() or int(_req["state"]) != State.LOCKED


func state() -> int:
	if not _req.is_empty():
		return int(_req["state"])
	if not _trans.is_empty():
		return State.SWITCHED
	return State.NONE


func current() -> Dictionary:
	if not _req.is_empty():
		return {"id": _req["id"], "dest": _req["dest"], "state": _req["state"], "ready": _req["ready"]}
	if not _trans.is_empty():
		return {"id": _trans["id"], "dest": _trans["landed"], "state": State.SWITCHED, "ready": true}
	return {}


func last_refusal() -> StringName:
	return _refusal


## ---------------------------------------------------------------- requests

func request(dest: Dictionary) -> int:
	if not _req.is_empty() and int(_req["state"]) == State.LOCKED:
		return _refuse(&"locked")
	if not _valid(dest):
		return _refuse(&"invalid")
	if not _req.is_empty():
		_close(&"replaced")
	var id := _next_id
	_next_id += 1
	_refusal = &""
	var when_v := StringName(str(dest.get("when", "lap_end")))
	_req = {"id": id, "dest": dest.duplicate(true), "state": State.PENDING, "ready": false, "soonest": when_v == &"soonest",
		"boundary": INF, "nr_done": false, "load_pending": true, "taken": {}, "plan": {}}
	if bool(_req["soonest"]):
		_req["boundary"] = _soonest_boundary()
	_log_emit(&"request_acknowledged", [id, true, &""])
	request_acknowledged.emit(id, true, &"")
	return id


func cancel(id: int) -> bool:
	if _req.is_empty() or int(_req["state"]) != State.PENDING or int(_req["id"]) != id:
		return false
	_close(&"cancelled")
	return true


func set_default(dest: Dictionary) -> void:
	_default_dest = dest.duplicate(true)


## ---------------------------------------------------------------- internals

func _lap_s() -> float:
	return BEATS_PER_LAP * beat_s()


func _lap_of(t: float) -> int:
	return int(floor((t - _scene_start) / _lap_s() + 1e-9))


func _lap_end(k: int) -> float:
	return _scene_start + float(k + 1) * _lap_s()


func _final_lap() -> int:
	return maxi(_laps - 1, _doors)


## The departure lap whose lock point is the next one to come.
func _cand_lap() -> int:
	var k := maxi(_lap_of(_t), _doors)
	while _t >= lock_t(_lap_end(k)):
		k += 1
	return k


func _soonest_boundary() -> float:
	var blk := BLOCK_BEATS * beat_s()
	var k := ceili((_t + lock_lead_beats * beat_s() - _scene_start) / blk - 1e-9)
	k = maxi(k, int(float(_doors) * BEATS_PER_LAP / BLOCK_BEATS) + 1)
	return _scene_start + float(k) * blk


func _valid(dest: Dictionary) -> bool:
	for key in ["id", "path", "node"]:
		if not dest.has(key) or str(dest[key]).is_empty():
			return false
	if not dest.has("kind"):
		return false
	return StringName(str(dest["kind"])) in [&"scene", &"quest_entry", &"quest_return"]


func _refuse(reason: StringName) -> int:
	_refusal = reason
	_log_emit(&"request_acknowledged", [0, false, reason])
	request_acknowledged.emit(0, false, reason)
	return 0


func _close(reason: StringName) -> void:
	var id := int(_req["id"])
	_req = {}
	_log_emit(&"request_closed", [id, reason])
	request_closed.emit(id, reason)


func _spec_for(dest: Dictionary) -> Dictionary:
	var spec: Dictionary = {"bpm": _def_bpm, "laps": _def_laps, "doors_from_lap": _def_doors}
	var own: Variant = scene_specs.get(str(dest.get("id", "")), null)
	if own is Dictionary:
		spec.merge(own, true)
	return spec


func _blending() -> bool:
	return not _trans.is_empty() and _t < float(_trans["complete_t"])


func _resolve_loads() -> void:
	if _req.is_empty() or not bool(_req["load_pending"]):
		return
	_req["load_pending"] = false
	var dest_id := str((_req["dest"] as Dictionary)["id"])
	if fail_load_ids.has(dest_id):
		_close(&"unavailable")
	elif not not_ready_ids.has(dest_id):
		_req["ready"] = true
		var id := int(_req["id"])
		_log_emit(&"destination_ready", [id])
		destination_ready.emit(id)


## The earliest event at or before target: {"t", "kind": switch | complete | lock, "b"}, or {}. Ties: switch,
## complete, lock.
func _next_event(target: float) -> Dictionary:
	var best: Dictionary = {}
	var best_t := INF
	var locked := not _req.is_empty() and int(_req["state"]) == State.LOCKED
	if locked:
		best = {"t": float(_req["boundary"]), "kind": "switch"}
		best_t = float(best["t"])
	if not _trans.is_empty() and float(_trans["complete_t"]) < best_t:
		best = {"t": float(_trans["complete_t"]), "kind": "complete"}
		best_t = float(best["t"])
	if not locked:
		var b := next_boundary_t()
		var lt := maxf(lock_t(b), _t)
		if lt < best_t:
			best = {"t": lt, "kind": "lock", "b": b}
			best_t = lt
	if best.is_empty() or best_t > target:
		return {}
	return best


func _do_lock(b: float) -> void:
	if not _req.is_empty() and int(_req["state"]) == State.PENDING:
		var id := int(_req["id"])
		if _blending():
			_defer(id, b, &"blending")
		elif not_ready_ids.has(str((_req["dest"] as Dictionary)["id"])) and not bool(_req["nr_done"]):
			_req["nr_done"] = true
			_req["ready"] = true
			_defer(id, b, &"not_ready")
		else:
			_lock_request(b)
		return
	var lap := int(round((b - _scene_start) / _lap_s())) - 1
	if lap < _final_lap():
		return
	if _default_dest.is_empty() or _blending():
		_laps = lap + 2
		return
	var id2 := _next_id
	_next_id += 1
	_req = {"id": id2, "dest": _default_dest.duplicate(true), "state": State.PENDING, "ready": true, "soonest": false,
		"boundary": b, "nr_done": false, "load_pending": false, "taken": {}, "plan": {}}
	_log_emit(&"request_acknowledged", [id2, true, &""])
	request_acknowledged.emit(id2, true, &"")
	if not _req.is_empty() and int(_req["id"]) == id2 and int(_req["state"]) == State.PENDING:
		_lock_request(b)


func _defer(id: int, b: float, reason: StringName) -> void:
	if bool(_req["soonest"]):
		_req["boundary"] = b + BLOCK_BEATS * beat_s()
	var nb := next_boundary_t()
	_log_emit(&"deferred", [id, nb, reason])
	deferred.emit(id, nb, reason)


func _lock_request(b: float) -> void:
	var dest: Dictionary = _req["dest"]
	var taken: Dictionary = dest
	var miss: Variant = dest.get("on_miss", null)
	if miss_last_block and miss is Dictionary and not (miss as Dictionary).is_empty():
		taken = miss
	var forced_cut := bool(_req["nr_done"])
	var spec := _spec_for(taken)
	var cut := forced_cut or blend_beats <= 0
	var in_beat_s := 60.0 / float(spec["bpm"])
	var blend := 0 if cut else blend_beats
	var plan: Dictionary = {
		"mode": &"cut" if cut else &"blend", "fallback": forced_cut,
		"outgoing_bpm": _bpm, "incoming_bpm": float(spec["bpm"]),
		"blend_beats": blend, "complete_t": b + float(blend) * in_beat_s,
	}
	_req["state"] = State.LOCKED
	_req["boundary"] = b
	_req["taken"] = taken
	_req["plan"] = plan
	var id := int(_req["id"])
	_log_emit(&"locked", [id, taken, b, plan])
	locked.emit(id, taken, b, plan)


func _do_switch() -> void:
	var id := int(_req["id"])
	var taken: Dictionary = _req["taken"]
	var plan: Dictionary = _req["plan"]
	var landed: Dictionary = taken.duplicate(true)
	if fail_after_lock_ids.has(str(taken["id"])):
		landed = fallback_dest.duplicate(true)
		landed["fallback"] = true
	_req = {}
	var spec := _spec_for(landed)
	begin_scene(landed, float(spec["bpm"]), int(spec["laps"]), int(spec["doors_from_lap"]))
	_trans = {"id": id, "landed": landed, "complete_t": maxf(float(plan["complete_t"]), _t)}
	_log_emit(&"switched", [id, landed, _t])
	switched.emit(id, landed, _t)


func _do_complete() -> void:
	var id := int(_trans["id"])
	_trans = {}
	_log_emit(&"completed", [id])
	completed.emit(id)


func _log_emit(sig: StringName, args: Array) -> void:
	log.append({"signal": sig, "args": args, "t": _t})
