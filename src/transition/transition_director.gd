class_name TransitionDirector
extends TransitionPort
## The real TransitionPort (docs/parallel-development/INTEGRATION_CONTRACT.md): it turns a requested destination into a scene change at a lap's boundary, on the run's engine.
## Stage M1.6 built it in `&"cut"` mode only. Stage M2.4 (docs/music/TRANSITIONS_BUILT.md) gives the planner its full inputs (_full_inputs), plans every mode when TransitionPlanner says so
## (RW_RUN_TRANSITIONS=cut turns them off; a path hand-off is always a cut), and hands the audio the recipe with the incoming plan; the wiring below is M1's. Stage M2 replaced the planner and the audio recipe it hands to the audio
## class, not this wiring. docs/parallel-development/MUSIC_TRANSITIONS.md section 12 lists what this file and its hooks leave in place.
##
## HOW IT SITS ON THE RUN (contract section 7)
##   attach(engine, data)        RunPlay, on every engine it makes (the run's start, a path hand-off): the engine's `lock_hook` and `track_gate` come here.
##   on_event(ev)                RunPlay._handle hands it every engine event, in order, before RunAudio.on_event. It reads route_commit and phase_start (the switch).
##   step(t)                     RunPlay._advance, every frame (also in the Bassment): the song time, readiness, and `completed`.
##   on_outgoing_silent(T)       RunAudio.outgoing_silent: the outgoing music of the boundary T is silent -> `completed`.
##   excursion(kind)             RunPlay: &"armed" (the wizard was chosen), &"enter" (the Bassment has the pads), &"leave" (back on the run). The Bassment is not behind the port in M1
##                               (lead ruling 20): it is entered and left as today, always a cut; nothing locks while it is armed or entered, a pending request is closed &"cancelled".
##   The lock point is the engine's: the last block's decision of each lap (beat 60.5 of 64), RunEngine._lock_point -> _on_lock_point here, after the hotspots' commit and before the next
##   scene is charted. The director answers with the engine's own exit (today's choice mechanism), its destination (RunEngine.take_route) or one more lap (RunEngine.extend_one_lap).
##
## TODAY'S CHOICE MECHANISM GOES THROUGH IT. Nobody calls request() in M1 (the narrative wiring, N2.2, will). At each lock point where the engine leaves on its own (a hotspot's outcome, a
## plain choose(), the pause menu's leave, or the scene's default exit on its final lap), the director takes that route as the transition: a fresh id is acknowledged and locked (the
## contract's default rule), the planner makes the plan, the audio gets the recipe, `switched` comes with the next scene's phase_start, `completed` when the outgoing music is silent.
## The engine's choice is left exactly as it was, so the run is the run of before, event for event. Once a request is pending, its destination wins at the lock; once set_default() has
## been called in a scene, the default (or, for {}, one more lap) replaces the scene's own default exit on its final lap, but a route the player chose through the engine still goes.
##
## READINGS OF THE CONTRACT CHOSEN HERE
##  - Laps count from 1; departure laps are a track scene's laps from doors_from_lap and every scene's last lap; lock points are only those of departure laps (no &"doors_closed").
##  - `when == &"soonest"` is taken as `&"lap_end"`: the engine leaves a scene only at a lap's end, and the Bassment entrance, the one user of "soonest", is not behind the port (ruling 20).
##  - An unresolvable destination (no such scene in the run or the path it names, the Bassment) is refused at once with &"unavailable" (ruling 13). A track scene whose pack fails to
##    load is not unavailable: it plays as an ordinary scene (planner row 2).
##  - A switch clears the default back to "unset" (the engine's own default exit), not to {}: a narrative side that forgets to set it again never strands the player.
##  - A route changed after the lock outside the port (the pause menu's leave at beat 61, a late choose()) lands where the engine went: `landed` carries fallback = true. A scene change
##    with no lock at all (the pause menu's leave on a lap that is no departure lap) is acknowledged and locked late, at the boundary itself.

const BEATS_PER_LAP := 64.0

## ---------------------------------------------------------------- wiring (RunPlay, or a test rig)

var engine: RunEngine
var data: RunData
## (out, inc, meta, ready) -> Plan with "recipe", or {"defer": reason}. TransitionPlanner.plan in M1; M2 assigns its own.
var planner: Callable
## (data: RunData, node: String) -> String: starts loading a scene's track stems (pinned) and returns "" (no track scene), loading, ready, failed or none. RunTrackAudio.request_scene.
var load_fn: Callable = Callable()
## () -> void: the pinned packs may go (RunTrackAudio.release_pins).
var release_fn: Callable = Callable()
## (track plan) -> bool: whether a track scene's stems are in memory (RunTrackAudio.is_ready); the engine's track gate goes through track_gate() below.
var ready_fn: Callable = Callable()
## (boundary_t: float, recipe: Dictionary) -> void: the audio class learns the recipe of a locked transition (RunAudio.prepare_transition).
var recipe_fn: Callable = Callable()
## (path key: String) -> RunData or null: "main" gives the main run's data, a path id that path's (RunPlay's portal cache).
var path_data_fn: Callable = Callable()
## True when RunAudio.outgoing_silent is connected to on_outgoing_silent: `completed` waits for it (at most silence_grace_s past plan.complete_t). False (virtual runs, tests):
## `completed` comes when song time reaches plan.complete_t.
var audio_reports_silence := false
var silence_grace_s := 2.0
## -1: the planner's own switch (TransitionPlanner.modes_enabled, set by _init in the game); 0: cut only; 1: every mode. Tests and tools set it per director.
var modes_override := -1

## Every signal emitted: {signal, args, t}; every lock: {id, t, boundary, dest, plan, recipe, observed, late}; every switch {id, t, landed, committed_to}.
var log: Array[Dictionary] = []
var lock_log: Array = []
var switch_log: Array = []

var _now := 0.0
var _bpm := 0.0
var _next_id := 1
var _refusal: StringName = &""
## The one slot: {id, dest, state, ready, nr_done, observed, taken, plan, boundary, route, lock_dir, lock_track_ok, committed_to}, or {}.
var _req: Dictionary = {}
## Switched, not completed: {id, landed, boundary, complete_t, silent}, or {}.
var _trans: Dictionary = {}
var _early_silence: Dictionary = {}  # boundary -> true: silence reported before the switch was seen
var _default: Dictionary = {}
var _default_set := false
var _armed := false
var _away := false
var _seen_scene := false


func _init() -> void:
	planner = func(o: Dictionary, i: Dictionary, m: Dictionary, r: Dictionary) -> Dictionary: return TransitionPlanner.plan(o, i, m, r)
	TransitionPlanner.modes_enabled = TransitionPlanner.game_default()


## ---------------------------------------------------------------- wiring calls

## The run's engine (again after a path hand-off: RunPlay makes a new one). Its lock point asks this director; `data` is the engine's run.
func attach(p_engine: RunEngine, p_data: RunData) -> void:
	engine = p_engine
	data = p_data
	engine.lock_hook = _on_lock_point
	if _bpm <= 0.0:
		_bpm = 60.0 / engine.beat_s


## The engine's track gate (RunEngine.track_gate): the destination this director locked plays as a track scene exactly when its plan said so; any other plan asks ready_fn as before.
func track_gate(plan: Dictionary) -> bool:
	var ans := bool(ready_fn.call(plan)) if ready_fn.is_valid() else true
	if not _req.is_empty() and int(_req["state"]) == State.LOCKED and str(_req.get("lock_dir", "")) != "" and str(plan.get("dir", "")) == str(_req["lock_dir"]):
		return bool(_req["lock_track_ok"])
	return ans


func on_event(ev: Dictionary) -> void:
	match str(ev.get("kind", "")):
		"route_commit":
			_on_route_commit(ev)
		"phase_start":
			_on_phase_start(ev)


func step(t: float) -> void:
	_set_now(t)
	_poll_ready()
	if _trans.is_empty():
		return
	var due := float(_trans["complete_t"])
	if bool(_trans.get("silent", false)) or (not audio_reports_silence and _now >= due - 1e-9):
		_complete("")
	elif audio_reports_silence and _now >= due + silence_grace_s:
		_complete("no silence report")


func on_outgoing_silent(boundary_t: float) -> void:
	if not _trans.is_empty() and absf(float(_trans["boundary"]) - boundary_t) < 1e-4:
		_complete("")
	else:
		_early_silence[snappedf(boundary_t, 1e-4)] = true


func excursion(kind: StringName) -> void:
	match kind:
		&"armed":
			_armed = true
		&"enter":
			_armed = false
			_away = true
			if not _req.is_empty() and int(_req["state"]) == State.PENDING:
				_close(&"cancelled")
			elif not _req.is_empty() and int(_req["state"]) == State.LOCKED:  # (cannot happen while arm precedes the lock point; a locked transition still switches and completes)
				var id := int(_req["id"])
				var landed: Dictionary = {"id": "bassment/entrance", "path": "bassment", "node": "entrance", "kind": &"quest_entry", "quest": "", "fallback": true}
				_req = {}
				_trans = {"id": id, "landed": landed, "boundary": _now, "complete_t": _now, "silent": true}
				_emit_switched(id, landed, _now)
				_complete("the Bassment took the boundary")
		&"leave":
			_armed = false
			_away = false


## ---------------------------------------------------------------- requests (the port)

func request(dest: Dictionary) -> int:
	if not _req.is_empty() and int(_req["state"]) == State.LOCKED:
		return _refuse(&"locked")
	if not _valid(dest):
		return _refuse(&"invalid")
	if engine == null or _away or _resolve(dest).is_empty():
		return _refuse(&"unavailable")
	if not _req.is_empty():
		_close(&"replaced")
	var id := _next_id
	_next_id += 1
	_refusal = &""
	_req = {"id": id, "dest": dest.duplicate(true), "state": State.PENDING, "ready": false, "nr_done": false, "observed": false, "ready_emitted": false}
	_log_emit(&"request_acknowledged", [id, true, &""])
	request_acknowledged.emit(id, true, &"")
	_load(dest)
	if dest.get("on_miss", null) is Dictionary:
		_load(dest["on_miss"])
	_poll_ready()
	return id


func cancel(id: int) -> bool:
	if _req.is_empty() or int(_req["state"]) != State.PENDING or int(_req["id"]) != id:
		return false
	_close(&"cancelled")
	return true


func set_default(dest: Dictionary) -> void:
	_default = dest.duplicate(true)
	_default_set = true
	if not _default.is_empty():
		_load(_default)


func current() -> Dictionary:
	if not _req.is_empty():
		return {"id": _req["id"], "dest": _req["dest"], "state": _req["state"], "ready": _req["ready"]}
	if not _trans.is_empty():
		return {"id": _trans["id"], "dest": _trans["landed"], "state": State.SWITCHED, "ready": true}
	return {}


func state() -> int:
	if not _req.is_empty():
		return int(_req["state"])
	if not _trans.is_empty():
		return State.SWITCHED
	return State.NONE


func last_refusal() -> StringName:
	return _refusal


## ---------------------------------------------------------------- the clock

func song_time() -> float:
	return _now


func beat_s() -> float:
	return engine.beat_s if engine != null else 60.0 / maxf(_bpm, 1.0)


func bpm() -> float:
	return 60.0 / beat_s()


func lap_beat() -> float:
	if engine == null or _away or _now < engine.phase_t0:
		return 0.0
	var lb := fposmod(_now - engine.phase_t0, BEATS_PER_LAP * engine.beat_s) / engine.beat_s
	return 0.0 if lb >= BEATS_PER_LAP - 1e-6 else lb


func next_boundary_t() -> float:
	if not _req.is_empty() and int(_req["state"]) == State.LOCKED:
		return float(_req["boundary"])
	if engine == null or _away or engine.level == null:
		return INF
	var lap_s := _lap_s()
	var k := maxi(engine.lap, engine.first_departure_lap())
	var end_k := engine.phase_t0 + float(k - engine.lap + 1) * lap_s
	var guard := 0
	while _now >= lock_t(end_k) - 1e-9 and guard < 1000:
		guard += 1
		end_k += lap_s
	return end_k


func lock_t(boundary_t: float) -> float:
	var lead := engine.lock_lead_beats() if engine != null else 3.5
	return boundary_t - lead * beat_s()


func selection_open() -> bool:
	return engine != null and not _away and (_req.is_empty() or int(_req["state"]) != State.LOCKED)


## ---------------------------------------------------------------- the lock point (RunEngine._lock_point)

func _on_lock_point(info: Dictionary) -> Dictionary:
	_set_now(float(info["t"]))
	var b := float(info["boundary_t"])
	if _away:
		return {}
	var pending := not _req.is_empty() and int(_req["state"]) == State.PENDING
	if _armed:  # the run leaves to the Bassment before this boundary (RunPlay.arm_trial): nothing locks
		if pending and bool(info["departure"]):
			_defer(b, &"held")
		return {}
	if pending:
		if not bool(info["departure"]):
			return {}  # (no lock point on this lap: the request waits for a departure lap)
		if bool(info["hold"]):
			_defer(b, &"held")  # a minigame holds the scene; this does not use up the request's one not_ready deferral
			return {}
		if not _trans.is_empty():
			_defer(b, &"blending")
			return {"extend": true}
		var taken: Dictionary = _req["dest"]
		var miss: Variant = taken.get("on_miss", null)
		if not bool(info["passed"]) and miss is Dictionary and not (miss as Dictionary).is_empty() and not _resolve(miss).is_empty():
			taken = (miss as Dictionary).duplicate(true)
		var res := _resolve(taken)
		if res.is_empty():  # (the destination no longer resolves: the run changed under it)
			_close(&"unavailable")
			return _nothing_pending(info, b)
		var pl := _plan_for(res, b, true, bool(_req["nr_done"]))
		if pl.has("defer"):
			_req["nr_done"] = true
			_defer(b, StringName(str(pl["defer"])))
			return {"extend": true}
		_lock(taken, res, pl, b, false, false)
		return {"route": str(res["route"]), "start": str(res["start"])}
	return _nothing_pending(info, b)


func _nothing_pending(info: Dictionary, b: float) -> Dictionary:
	if bool(info["hold"]):
		return {}
	if bool(info["leaving"]) and bool(info["chosen"]):
		_observe(str(info["route"]), b, false)  # the player's route, through today's choice mechanism
		return {}
	if bool(info["final"]):
		if _default_set:
			if _default.is_empty() or not _trans.is_empty():
				return {"extend": true}  # stay one more lap, without a signal (contract rule 8, ruling 14)
			var res := _resolve(_default)
			if not res.is_empty():
				var id := _next_id
				_next_id += 1
				_req = {"id": id, "dest": _default.duplicate(true), "state": State.PENDING, "ready": true, "nr_done": false, "observed": false, "ready_emitted": true}
				_log_emit(&"request_acknowledged", [id, true, &""])
				request_acknowledged.emit(id, true, &"")
				_lock(_req["dest"], res, _plan_for(res, b, false, true), b, false, false)
				return {"route": str(res["route"]), "start": str(res["start"])}
			push_warning("transition director: the default destination %s does not resolve; the scene's own default exit is taken" % str(_default.get("id", "")))
		if bool(info["leaving"]):
			_observe(str(info["route"]), b, false)  # the scene's own default exit
	return {}


## A transition the engine makes on its own, taken through the port: a fresh id, acknowledged and locked (the contract's default rule). `late`: there was no lock point before it.
func _observe(route: String, b: float, late: bool) -> void:
	if not _trans.is_empty():
		_complete("a new lock came first")  # (keeps completed before the next locked; cut transitions are long silent by then)
	var dest := _dest_of_route(route)
	var res := _resolve(dest)
	if res.is_empty():
		res = {"route": route, "start": "", "data": data, "node": str(dest["node"])}
	var id := _next_id
	_next_id += 1
	_req = {"id": id, "dest": dest, "state": State.PENDING, "ready": true, "nr_done": false, "observed": true, "ready_emitted": true}
	_log_emit(&"request_acknowledged", [id, true, &""])
	request_acknowledged.emit(id, true, &"")
	_lock(dest, res, _plan_for(res, b, false, true), b, true, late)


func _lock(taken: Dictionary, res: Dictionary, pl: Dictionary, b: float, observed: bool, late: bool) -> void:
	var recipe: Dictionary = (pl.get("recipe", {}) as Dictionary).duplicate(true)
	var plan: Dictionary = pl.duplicate(true)
	plan.erase("recipe")
	var inc_plan := _track_plan(res["data"], str(res["node"]))
	recipe["boundary_t"] = b
	if StringName(str(recipe.get("incoming", &"ordinary"))) == &"track" and not inc_plan.is_empty():  # (the audio starts the incoming group early and muted from these: RunTrackAudio)
		recipe["in"] = {"node": str(res["node"]), "track": str(inc_plan["track"]), "dir": str(inc_plan["dir"]), "entry_t": float(inc_plan["entry_t"]), "beat_s": float(inc_plan["beat_s"]),
			"bpm": float(inc_plan["bpm"])}
	if engine.is_track_scene():
		recipe["out"] = {"node": engine.node_id, "track": str(engine.track["track"]), "dir": str(engine.track.get("dir", ""))}
	_req["state"] = State.LOCKED
	_req["taken"] = taken.duplicate(true)
	_req["plan"] = plan
	_req["boundary"] = b
	_req["route"] = str(res["route"])
	_req["lock_dir"] = str(inc_plan.get("dir", ""))
	_req["lock_track_ok"] = StringName(str(recipe.get("incoming", &"ordinary"))) == &"track"
	_req["committed_to"] = ""
	var id := int(_req["id"])
	lock_log.append({"id": id, "t": _now, "boundary": b, "dest": str(taken.get("id", "")), "route": str(res["route"]), "plan": plan, "recipe": recipe, "observed": observed, "late": late})
	if not RunTrackScenes._under_test_runner():  # (MUSIC_TRANSITIONS.md 8.3: one line per transition; the walks list the modes from it)
		print("RUN transition id=%d %s->%s mode=%s fallback=%s reason=%s bpm=%.4f->%.4f rate=%.6f W=%d T=%.3f complete=%.3f drop=%s" % [id, engine.node_id, str(res["node"]), str(plan.get("mode", "")),
			str(plan.get("fallback", false)), str(recipe.get("reason", "-")), float(plan.get("outgoing_bpm", 0.0)), float(plan.get("incoming_bpm", 0.0)), float(recipe.get("rate", 1.0)),
			int(recipe.get("window_bars", 0)), b, float(plan.get("complete_t", b)), "%.3f" % float(recipe["drop_t"]) if recipe.has("drop_t") else "-"])
	if recipe_fn.is_valid():
		recipe_fn.call(b, recipe)
	_log_emit(&"locked", [id, _req["taken"], b, plan])
	locked.emit(id, _req["taken"], b, plan)


## ---------------------------------------------------------------- the switch

func _on_route_commit(ev: Dictionary) -> void:
	if _away:
		return
	var to := str(ev["to"])
	if not _req.is_empty() and int(_req["state"]) == State.LOCKED:
		_req["committed_to"] = to
		return
	if to == str(ev["from"]):
		return  # a hold or a one-lap extension re-enters the scene: it goes on
	if not _req.is_empty():
		_close(&"cancelled")  # (the engine left before the request's lock point: only the pause menu's leave does that)
	_set_now(float(ev["t"]))
	_observe(to, float(ev["t"]), true)


func _on_phase_start(ev: Dictionary) -> void:
	if _away:
		return
	if not _req.is_empty() and int(_req["state"]) == State.LOCKED:
		_switch(ev)
		return
	var nb := 60.0 / engine.beat_s  # a scene began without a lock: the run's first scene, the return from the Bassment, a re-entry
	if _seen_scene and not is_equal_approx(nb, _bpm):
		_bpm = nb
		_log_emit(&"tempo_changed", [nb, 60.0 / nb, float(ev["t"])])
		tempo_changed.emit(nb, 60.0 / nb, float(ev["t"]))
	_bpm = nb
	_seen_scene = true


func _switch(ev: Dictionary) -> void:
	var t := float(ev["t"])
	_set_now(t)
	var id := int(_req["id"])
	var taken: Dictionary = _req["taken"]
	var here := _path_key(data)
	var node := str(ev["node"])
	var landed: Dictionary
	if str(taken.get("id", "")) == here + "/" + node:
		landed = taken.duplicate(true)
	else:  # the scene really entered is not the one locked (a path that could not be loaded, a route changed after the lock)
		landed = _mk(here, node)
		landed["kind"] = taken.get("kind", &"scene")
		landed["quest"] = taken.get("quest", "")
		landed["fallback"] = true
	var plan: Dictionary = _req["plan"]
	var boundary := float(_req["boundary"])
	switch_log.append({"id": id, "t": t, "landed": str(landed["id"]), "fallback": bool(landed.get("fallback", false)), "committed_to": str(_req.get("committed_to", ""))})
	_req = {}
	_trans = {"id": id, "landed": landed, "boundary": boundary, "complete_t": maxf(float(plan["complete_t"]), t), "silent": _early_silence.has(snappedf(boundary, 1e-4))}
	_early_silence.clear()
	_default = {}
	_default_set = false
	if release_fn.is_valid():
		release_fn.call()
	var nb := 60.0 / engine.beat_s
	if not is_equal_approx(nb, _bpm):
		_bpm = nb
		_log_emit(&"tempo_changed", [nb, 60.0 / nb, t])
		tempo_changed.emit(nb, 60.0 / nb, t)
	_seen_scene = true
	_emit_switched(id, landed, t)
	if bool(_trans["silent"]):
		_complete("")


func _emit_switched(id: int, landed: Dictionary, t: float) -> void:
	_log_emit(&"switched", [id, landed, t])
	switched.emit(id, landed, t)


func _complete(note: String) -> void:
	if _trans.is_empty():
		return
	var id := int(_trans["id"])
	if note != "":
		print("TRANSITION completed id=%d at t=%.3f: %s" % [id, _now, note])
	_trans = {}
	_log_emit(&"completed", [id])
	completed.emit(id)


## ---------------------------------------------------------------- planning

## The planner's inputs for a transition at boundary `b` into the resolved destination `res`.
func _plan_for(res: Dictionary, b: float, may_defer: bool, deferred_once: bool) -> Dictionary:
	var in_data: RunData = res["data"]
	var node := str(res["node"])
	var tp := _track_plan(in_data, node)
	var here_node: Dictionary = data.nodes.get(engine.node_id, {})
	var in_node: Dictionary = in_data.nodes.get(node, {})
	var out := {"kind": &"track" if engine.is_track_scene() else &"ordinary", "node": engine.node_id, "path": _path_key(data), "bpm": 60.0 / engine.beat_s, "boundary_t": b,
		"family": str(here_node.get("family", "")) if not engine.is_track_scene() else ""}
	var in_bpm := float(in_data.cfg["timing"]["bpm"])
	var inc := {"kind": &"track" if not tp.is_empty() else &"ordinary", "node": node, "path": _path_key(in_data), "bpm": float(tp.get("bpm", in_bpm)), "ordinary_bpm": in_bpm,
		"family": str(in_node.get("family", ""))}
	var mix: Dictionary = in_data.cfg.get("mix", {})
	var carry: Dictionary = mix.get("carry_bass", {})
	var meta := {"fade_s": float(mix.get("phase_fade_s", 0.6)), "carry_beats": float(carry.get("beats", 16.0)), "carry_gain": float(carry.get("gain", 0.0)) if in_data == data else 0.0}
	_full_inputs(out, inc, meta, b, tp)
	if in_data != data:
		meta["modes_enabled"] = false  # a path hand-off (into a path or back to the main run) is always a cut (the brief of M2.4, after ruling 20)
	elif modes_override >= 0:
		meta["modes_enabled"] = modes_override == 1
	var state := ""
	if not tp.is_empty():
		state = str(load_fn.call(in_data, node)) if load_fn.is_valid() else ("ready" if not ready_fn.is_valid() or bool(ready_fn.call(tp)) else "none")
	var pl: Variant = planner.call(out, inc, meta, {"state": state, "may_defer": may_defer, "deferred_once": deferred_once})
	if typeof(pl) != TYPE_DICTIONARY or ((pl as Dictionary).get("mode", null) == null and not (pl as Dictionary).has("defer")):
		push_error("transition director: the planner gave no plan; cut")
		return TransitionPlanner._cut(out, inc, meta, b, true)
	return pl


## The planner's inputs between two track scenes (TransitionPlanner's header, stage M2.4), from the engine and the two scene plans (RunTrackScenes.add_transition_meta made the metadata off
## the frame): the outgoing track, its length, where it is at T, its grid origin, its section at T, its stems; the incoming track, its entry and drop bars; both sidecars and grid flags.
## A plan without that metadata (a synthetic one) counts as a steady grid with no sidecar.
func _full_inputs(out: Dictionary, inc: Dictionary, meta: Dictionary, b: float, tp: Dictionary) -> void:
	if engine.is_track_scene():
		var op: Dictionary = engine.track
		out["track"] = str(op.get("track", ""))
		out["duration_s"] = float(op.get("duration_s", 0.0))
		out["track_t_at_T"] = engine.track_t_at(b)
		out["first_downbeat_s"] = float(op.get("first_downbeat_s", 0.0))
		var pack: Variant = op.get("pack", null)
		out["section_role"] = ""
		if pack is TrackPack:
			var tt := float(out["track_t_at_T"])
			for s in (pack as TrackPack).sections:
				if tt >= float(s["start_s"]) - 1e-6 and tt < float(s["end_s"]):
					out["section_role"] = str(s.get("role", ""))
			out["stem_keys"] = (pack as TrackPack).stems_in_order().map(func(s: Dictionary) -> String: return str(s["key"]))
		meta["out"] = op.get("sidecar", {})
		meta["out_state"] = str(op.get("sidecar_state", "missing"))
		meta["out_grid_ok"] = bool(op.get("grid_ok", true))
	if not tp.is_empty():
		inc["track"] = str(tp.get("track", ""))
		inc["entry_bar"] = int(tp.get("entry_bar", 0))
		inc["drop_bar"] = int(tp.get("drop_bar", -1))
		meta["in"] = tp.get("sidecar", {})
		meta["in_state"] = str(tp.get("sidecar_state", "missing"))
		meta["in_grid_ok"] = bool(tp.get("grid_ok", true))


static func _track_plan(d: RunData, node: String) -> Dictionary:
	return d.track_scenes.plan_of(node) if d != null and d.track_scenes != null and d.nodes.has(node) else {}


## ---------------------------------------------------------------- destinations

static func _path_key(d: RunData) -> String:
	return "main" if d == null or d.path_id == "" else d.path_id


static func _mk(p: String, n: String) -> Dictionary:
	return {"id": "%s/%s" % [p, n], "path": p, "node": n, "kind": &"scene", "quest": "", "when": &"lap_end"}


func _path_data(key: String) -> RunData:
	if path_data_fn.is_valid():
		var v: Variant = path_data_fn.call(key)
		if v is RunData:
			return v
	return null


## The engine route of a destination: {route, start, data, node}, or {} when the run cannot go there (the Bassment is not behind the port in M1).
func _resolve(dest: Dictionary) -> Dictionary:
	if data == null:
		return {}
	var here := _path_key(data)
	var p := str(dest.get("path", ""))
	var n := str(dest.get("node", ""))
	if p == "" or n == "" or p == "bassment":
		return {}
	if p == here:
		return {"route": n, "start": "", "data": data, "node": n} if data.nodes.has(n) else {}
	if here == "main":
		var pd := _path_data(p)
		if pd != null and pd.errors.is_empty() and pd.path_id == p and pd.nodes.has(n):
			return {"route": HotspotContract.PATH_PREFIX + p, "start": n, "data": pd, "node": n}
		return {}
	if p == "main":
		var md := _path_data("main")
		if md != null and md.errors.is_empty() and md.nodes.has(n):
			return {"route": RunEngine.LEAVE_ROUTE, "start": n, "data": md, "node": n}
	return {}


## The Destination of a route the engine takes on its own.
func _dest_of_route(route: String) -> Dictionary:
	var here := _path_key(data)
	if data.nodes.has(route):
		return _mk(here, route)
	if HotspotContract.is_path_route(route):
		var pid := HotspotContract.path_of(route)
		var pd := _path_data(pid)
		return _mk(pid, pd.start_node() if pd != null and pd.errors.is_empty() else "")
	if HotspotContract.is_run_route(route):
		return _mk("main", "warehouse")
	return _mk(here, route)


func _valid(dest: Dictionary) -> bool:
	for key in ["id", "path", "node"]:
		if not dest.has(key) or str(dest[key]).is_empty():
			return false
	if not dest.has("kind"):
		return false
	return StringName(str(dest["kind"])) in [&"scene", &"quest_entry", &"quest_return"]


## ---------------------------------------------------------------- loading

func _load(dest: Dictionary) -> void:
	if not load_fn.is_valid():
		return
	var res := _resolve(dest)
	if not res.is_empty() and not _track_plan(res["data"], str(res["node"])).is_empty():
		load_fn.call(res["data"], str(res["node"]))


## destination_ready once the pending request's music is in memory (at once for a scene without a track).
func _poll_ready() -> void:
	if _req.is_empty() or int(_req["state"]) != State.PENDING or bool(_req["ready_emitted"]):
		return
	var res := _resolve(_req["dest"])
	if res.is_empty():
		return
	var tp := _track_plan(res["data"], str(res["node"]))
	var ok := tp.is_empty() or not load_fn.is_valid() or str(load_fn.call(res["data"], str(res["node"]))) == "ready"
	if ok:
		_req["ready"] = true
		_req["ready_emitted"] = true
		var id := int(_req["id"])
		_log_emit(&"destination_ready", [id])
		destination_ready.emit(id)


## ---------------------------------------------------------------- internals

func _lap_s() -> float:
	return BEATS_PER_LAP * engine.beat_s


func _set_now(t: float) -> void:
	_now = maxf(_now, t)


func _defer(b: float, reason: StringName) -> void:
	var id := int(_req["id"])
	var nb := b + _lap_s()
	_log_emit(&"deferred", [id, nb, reason])
	deferred.emit(id, nb, reason)


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


func _log_emit(sig: StringName, args: Array) -> void:
	log.append({"signal": sig, "args": args, "t": _now})
