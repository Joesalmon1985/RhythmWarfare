class_name QuestRouter
extends RefCounted
## Turns a tapped object into a Destination for the TransitionPort and applies the result to the route state (INTEGRATION_CONTRACT.md sections 3 to 5;
## NARRATIVE_GRAPH.md section 3.2, the transaction rule).
##
##   var dest := router.destination_for("hospital.enter_gospel")   # a Destination dictionary, or {} (last_refusal says why)
##   var id := port.request(dest)
##   router.hold(id, dest)                                          # or in one call: var id := router.submit(port, "hospital.enter_gospel")
##   ...request_closed(id, reason)  ->  router.discard(id)          # replaced, cancelled, unavailable: the committed state is not touched
##   ...deferred(id, ...)           ->  router.on_deferred(id)      # the request stays pending, the change is kept
##   ...switched(id, landed, t)     ->  router.commit(id, landed)   # the ONLY place the committed route state changes (it saves)
##   port.set_default(router.default_destination())                 # on every scene entry
## attach(port) connects the three signals and sets the default for you.
##
## The change a request would make is computed when the destination is built and held in `state.pending` against the request id. commit() applies the
## change for the scene really entered: the held change when it is for that scene and still current, else a change computed from `landed` (a fallback
## landing, or a default that locked under a fresh id).
##
## Quest entry records the entry origin and the checkpoint (the hub of the location entered from); a return lands on the checkpoint; re-entry resumes at
## the start of the scene left; a completed quest restarts at its first scene and keeps `completed`.

## Where the route state is saved: an object with save(narrative: Dictionary) -> bool and load() -> Dictionary (NarrativeMemoryStore is one), or a Callable
## taking the dictionary. null: nothing is saved.
var store: Variant = null
var graph: NarrativeGraph
var state: RouteState
## The run's flags that are set now ({name: true}); the caller keeps them up to date. flags_source, when valid, is called instead and returns the same.
var run_flags: Dictionary = {}
var flags_source: Callable = Callable()
## Sentences for the developer: a landing on a scene the graph does not know, a failed save, a repaired save.
var errors: Array = []
## Why the last destination_for() returned {}: &"no_such_object", &"legacy", &"unresolved".
var last_refusal: StringName = &""
var save_failures := 0

var _candidate: Dictionary = {}
var _port: TransitionPort = null


func _init(p_graph: NarrativeGraph, p_store: Variant = null) -> void:
	graph = p_graph
	store = p_store
	state = _fresh_state()


func _fresh_state() -> RouteState:
	var s := RouteState.new()
	s.history_limit = maxi(int(graph.settings.get("history_limit", RouteState.DEFAULT_HISTORY_LIMIT)), 8)
	s.location = graph.location_of(graph.start)
	s.history = [graph.start]
	return s


## ---------------------------------------------------------------- run start and load

## Begins a run on the start scene. Quest progress is kept (it belongs to the player, not the run); everything else is reset. Saves.
func start_run() -> void:
	var fresh := _fresh_state()
	fresh.quest_progress = state.quest_progress.duplicate(true)
	fresh.revision = state.revision + 1
	fresh.newer_than_known = state.newer_than_known
	state = fresh
	_save()


## Loads the route state from the store. `extra` is the rest of the save ({"paths": ...}): when the store holds nothing, a quest whose path already has
## endings starts as completed. A damaged or inconsistent value is repaired (history back at the start, bad progress scenes dropped) and a sentence is added
## to `errors`. Returns the loaded state.
func load_state(extra: Dictionary = {}) -> RouteState:
	var narrative: Dictionary = {}
	if store != null and typeof(store) == TYPE_OBJECT and (store as Object).has_method("load"):
		var v: Variant = (store as Object).call("load")
		if typeof(v) == TYPE_DICTIONARY:
			narrative = v
	var limit := maxi(int(graph.settings.get("history_limit", RouteState.DEFAULT_HISTORY_LIMIT)), 8)
	var s := RouteState.from_dict(narrative, graph.start, limit)
	if narrative.is_empty():
		var path_of := {}
		for q in graph.quest_ids():
			path_of[q] = (graph.quest_meta.get(q, {}) as Dictionary).get("path", q)
		s.migrate_from_paths(extra.get("paths"), path_of)
	var errs := s.invariant_errors(graph)
	if not errs.is_empty():
		errors.append("the saved route state was repaired (%s)" % "; ".join(PackedStringArray(errs)))
		_repair(s)
	s.revision = state.revision + 1
	_candidate = {}
	state = s
	return s


func _repair(s: RouteState) -> void:
	for q in s.quest_progress.keys():
		var sc := str((s.quest_progress[q] as Dictionary).get("scene", ""))
		if not graph.quest_ids().has(q):
			s.quest_progress.erase(q)
		elif sc != "" and (not graph.resolves(sc) or graph.quest_of(sc) != str(q)):
			(s.quest_progress[q] as Dictionary)["scene"] = ""
	s.quest = ""
	s.entry_origin = ""
	s.checkpoint = ""
	s.history = [graph.start]
	s.location = graph.location_of(graph.start)


func attach(port: TransitionPort) -> void:
	detach()
	_port = port
	port.request_closed.connect(_on_request_closed)
	port.switched.connect(_on_switched)
	port.deferred.connect(_on_deferred)
	port.set_default(default_destination())


func detach() -> void:
	if _port != null:
		_port.request_closed.disconnect(_on_request_closed)
		_port.switched.disconnect(_on_switched)
		_port.deferred.disconnect(_on_deferred)
		_port = null


func _on_request_closed(id: int, _reason: StringName) -> void:
	discard(id)


func _on_deferred(id: int, _next_boundary_t: float, _reason: StringName) -> void:
	on_deferred(id)


func _on_switched(id: int, landed: Dictionary, _t: float) -> void:
	commit(id, landed)
	if _port != null:
		_port.set_default(default_destination())


## ---------------------------------------------------------------- what the player can do here

## The previous scene a `back` option leads to: the scene before this one in the history when it is a possible predecessor, else the first possible
## predecessor; "" when the scene has none.
func previous_for(scene_id: String) -> String:
	var preds := graph.predecessors(scene_id)
	if preds.is_empty():
		return ""
	if scene_id == state.current_scene() and state.history.size() >= 2 and preds.has(state.history[state.history.size() - 2]):
		return str(state.history[state.history.size() - 2])
	return str(preds[0])


## The objects the player can choose in the current scene: [{object, to (the graph id, "$checkpoint" for a return), kind, legacy}], under the run's flags.
func options() -> Array:
	var cur := state.current_scene()
	var out: Array = []
	for e in graph.choices_from(cur, _flags(), previous_for(cur)):
		out.append({"object": e["via"], "to": e["to"], "kind": e["kind"], "legacy": _is_legacy(e)})
	return out


static func _is_legacy(e: Dictionary) -> bool:
	return bool(e.get("legacy", false)) or str(e.get("transition", "")) == "legacy_mid_scene"


## True when the object in the current scene is an entrance that stays outside the port (the wizard): it is committed by commit_legacy() when the trial begins.
func is_legacy_object(object_id: String, scene_id: String = "") -> bool:
	var scene := scene_id if scene_id != "" else state.current_scene()
	for e in graph.edges_from(scene):
		if e["via"] == object_id and _is_legacy(e):
			return true
	return false


## ---------------------------------------------------------------- building a request

## The Destination for a tapped object (hotspot id) of `scene_id` (default: the current scene), or {} (see last_refusal). A quest entry resumes at the saved scene
## of an unfinished quest; a return is aimed at the checkpoint; a scene edge that has a miss twin carries it as `on_miss`; quest entries and returns never do.
func destination_for(object_id: String, scene_id: String = "") -> Dictionary:
	last_refusal = &""
	_candidate = {}
	var scene := scene_id if scene_id != "" else state.current_scene()
	var built := _build(scene, object_id, false)
	if built.is_empty():
		return {}
	_candidate = {"dest": built, "changes": _changes_for(built, scene)}
	return built.duplicate(true)


## Binds the change computed for `dest` to the request id the port returned. Returns false (and holds nothing) when the id is 0, i.e. the port refused.
func hold(id: int, dest: Dictionary) -> bool:
	if id <= 0 or dest.is_empty():
		_candidate = {}
		return false
	var changes: Dictionary
	if not _candidate.is_empty() and (_candidate["dest"] as Dictionary)["id"] == dest["id"]:
		changes = _candidate["changes"]
	else:
		changes = _changes_for(dest, state.current_scene())
	state.pending = {"id": id, "dest": dest.duplicate(true), "changes": changes}
	_candidate = {}
	return true


## destination_for + port.request + hold. Returns the request id, or 0 when there is no such object or the port refused (last_refusal says why).
func submit(port: TransitionPort, object_id: String) -> int:
	var dest := destination_for(object_id)
	if dest.is_empty():
		return 0
	var id := port.request(dest)
	if id == 0:
		last_refusal = port.last_refusal()
		_candidate = {}
		return 0
	hold(id, dest)
	return id


## The destination for port.set_default(): the scene's default exit, else its automatic route, else {} (the scene goes on for another lap).
func default_destination() -> Dictionary:
	var scene := state.current_scene()
	var fset := _flags()
	var chosen: Dictionary = {}
	for e in graph.edges_from(scene):
		var c: Dictionary = e["condition"]
		if c.get("default", false) and ["on_pass", "take", "win_or_take"].has(c.get("outcome", "")) and not e.get("hidden", false) \
				and e["kind"] != "quest_return" and not _is_legacy(e) and _flags_ok(e, fset):
			chosen = e
			break
	if chosen.is_empty():
		for e in graph.edges_from(scene):
			if (e["condition"] as Dictionary).get("auto", false):
				chosen = e
				break
	if chosen.is_empty():
		return {}
	return _build(scene, str(chosen["via"]), true)


func _build(scene: String, object_id: String, allow_auto: bool) -> Dictionary:
	var fset := _flags()
	var prev := previous_for(scene)
	var primary: Dictionary = {}
	var twin: Dictionary = {}
	for e in graph.edges_from(scene):
		if e["via"] != object_id:
			continue
		var c: Dictionary = e["condition"]
		if c.get("auto", false) and not allow_auto:
			continue
		if not _flags_ok(e, fset):
			continue
		if c.get("previous_scene", false) and e["to"] != prev:
			continue
		var outcome := str(c.get("outcome", ""))
		if outcome == "on_miss":
			if twin.is_empty():
				twin = e
		elif not NarrativeGraph.MISS_OUTCOMES.has(outcome) and primary.is_empty():
			primary = e
	if primary.is_empty():
		last_refusal = &"no_such_object"
		return {}
	if _is_legacy(primary):
		last_refusal = &"legacy"
		return {}
	var dest := _dest_of(primary)
	if dest.is_empty():
		last_refusal = &"unresolved"
		return {}
	if dest["kind"] == &"scene" and not twin.is_empty() and twin["kind"] == "scene":
		var miss := _dest_of(twin)
		if not miss.is_empty() and miss["id"] != dest["id"]:
			dest["on_miss"] = miss
	return dest


## The Destination dictionary of one edge ({} when it cannot be resolved).
func _dest_of(e: Dictionary) -> Dictionary:
	var kind := str(e["kind"])
	var target := str(e["to"])
	var quest_id := ""
	if kind == "quest_entry":
		quest_id = str(e.get("quest", graph.quest_of(target)))
		target = _entry_target(quest_id, target)
	elif kind == "quest_return":
		quest_id = state.quest if state.quest != "" else graph.quest_of(str(e["from"]))
		if target == NarrativeGraph.CHECKPOINT:
			target = state.checkpoint if state.checkpoint != "" else graph.hub_of_location(state.location)
	if target == "" or not graph.resolves(target):
		return {}
	var parts := target.split("/", true, 1)
	return {"id": target, "path": parts[0], "node": parts[1], "kind": StringName(kind), "quest": quest_id, "when": &"lap_end"}


## The scene a quest entry lands on: the saved scene of an unfinished quest, else the quest's first scene.
func _entry_target(quest_id: String, default_entry: String) -> String:
	var p := state.progress_of(quest_id)
	var sc := str(p.get("scene", ""))
	if sc != "" and not bool(p.get("completed", false)) and graph.resolves(sc) and graph.quest_of(sc) == quest_id:
		return sc
	return default_entry


## ---------------------------------------------------------------- the transaction

## `deferred`: the request stays pending, the change is kept. Nothing to do; here so that every port signal has its handler.
func on_deferred(_id: int) -> void:
	pass


## `request_closed` (replaced, cancelled, unavailable): drops the held change of that request. The committed state is never touched. True if one was dropped.
func discard(id: int) -> bool:
	if not state.pending.is_empty() and int(state.pending["id"]) == id:
		state.pending = {}
		return true
	return false


## `switched`: applies the change for the scene really entered (`landed`) to the committed state and saves it. The held change is used when it is for that
## scene, still current and not a fallback; otherwise the change is computed from `landed`. Returns {applied, recomputed, entered, left, restore_flags, saved, reason}:
## `restore_flags` are the run flags to set again (the flags the quest saved when it was left), `entered` / `left` the quest ids.
func commit(id: int, landed: Dictionary) -> Dictionary:
	var result := {"applied": false, "recomputed": false, "entered": "", "left": "", "restore_flags": [], "saved": false, "reason": ""}
	var land_id := str(landed.get("id", ""))
	var held := not state.pending.is_empty() and int(state.pending["id"]) == id
	if not graph.resolves(land_id):
		errors.append("request %d landed on '%s', which is not in the narrative graph: the route state was left as it was" % [id, land_id])
		result["reason"] = "unknown_scene"
		if held:
			state.pending = {}
		return result
	var change: Dictionary = {}
	if held and not bool(landed.get("fallback", false)):
		var ch: Dictionary = (state.pending["changes"] as Dictionary).get(land_id, {})
		if not ch.is_empty() and int(ch["base_rev"]) == state.revision:
			change = ch
	if change.is_empty():
		change = _make_change(land_id, state.current_scene())
		result["recomputed"] = true
	if held:
		state.pending = {}
	state.adopt(change["next"])
	var info: Dictionary = change["info"]
	if str(info["left"]) != "":  # the flags of the quest are those of the moment it was left
		_store_quest_flags(state, str(info["left"]))
	result["applied"] = true
	result["entered"] = info["entered"]
	result["left"] = info["left"]
	result["restore_flags"] = info["restore"]
	result["saved"] = _save()
	return result


## The wizard's entrance is outside the port: the trial begins at once, and the change is committed then (the one commit not made on `switched`, a declared
## exception). Lands on the quest's entry or saved scene. Returns the same dictionary as commit().
func commit_legacy(object_id: String) -> Dictionary:
	var scene := state.current_scene()
	for e in graph.edges_from(scene):
		if e["via"] == object_id and _is_legacy(e) and e["kind"] == "quest_entry" and _flags_ok(e, _flags()):
			var dest := _dest_of(e)
			if not dest.is_empty():
				return commit(0, dest)
	return {"applied": false, "recomputed": false, "entered": "", "left": "", "restore_flags": [], "saved": false, "reason": "no_legacy_object"}


func _changes_for(dest: Dictionary, scene: String) -> Dictionary:
	var out := {}
	out[str(dest["id"])] = _make_change(str(dest["id"]), scene)
	if dest.has("on_miss"):
		var miss: Dictionary = dest["on_miss"]
		out[str(miss["id"])] = _make_change(str(miss["id"]), scene)
	return out


func _make_change(land_id: String, from_scene: String) -> Dictionary:
	var next := state.copy()
	var info := _apply_landing(next, land_id, from_scene)
	return {"base_rev": state.revision, "land": land_id, "from": from_scene, "next": next, "info": info}


## The rules of NARRATIVE_GRAPH.md 3.4, applied to `s` for a landing on `land` made from `from_scene`.
func _apply_landing(s: RouteState, land: String, from_scene: String) -> Dictionary:
	var info := {"entered": "", "left": "", "restore": []}
	if not graph.is_mainline(land):
		var qn := graph.quest_of(land)
		if s.quest == "":  # entering a quest from the scene the object was in
			var org := from_scene
			if graph.location_of(org) == "":  # not a mainline scene (a fallback from nowhere): enter from the hub of the current location
				org = graph.hub_of_location(s.location)
			s.quest = qn
			s.entry_origin = org
			s.location = graph.location_of(org)
			s.checkpoint = graph.hub_of_location(s.location)
			_enter(s, qn, info)
		elif s.quest != qn:  # a fallback from one quest into another: the origin and the checkpoint stay
			_leave(s, from_scene, info)
			s.quest = qn
			_enter(s, qn, info)
		var prog := s.progress_for_write(qn)
		if graph.ending_of(land) != "death":  # a death passage is not saved: a re-entry resumes alive, at the passage before it
			prog["scene"] = land
		if graph.is_completion(land):
			prog["completed"] = true
	else:
		if s.quest != "":  # a return (or a fallback out of the quest)
			_leave(s, from_scene, info)
			s.quest = ""
			s.entry_origin = ""
			s.checkpoint = ""
		s.location = graph.location_of(land)
	s.push_history(land)
	return info


func _enter(s: RouteState, quest_id: String, info: Dictionary) -> void:
	var prog := s.progress_for_write(quest_id)
	prog["visits"] = int(prog.get("visits", 0)) + 1
	info["entered"] = quest_id
	var names: Array = prog.get(_flag_key(quest_id), [])
	var restore: Array = []
	for n in names:
		restore.append((str(graph.flag_prefixes(quest_id)[0]) + str(n)) if _is_items(quest_id) else str(n))
	info["restore"] = restore


func _leave(s: RouteState, from_scene: String, info: Dictionary) -> void:
	var prog := s.progress_for_write(s.quest)
	if graph.quest_of(from_scene) == s.quest and graph.ending_of(from_scene) != "death":
		prog["scene"] = from_scene
	_store_quest_flags(s, s.quest)
	info["left"] = s.quest


func _is_items(quest_id: String) -> bool:
	return str((graph.quest_meta.get(quest_id, {}) as Dictionary).get("system", "path")) == "trial"


func _flag_key(quest_id: String) -> String:
	return "items" if _is_items(quest_id) else "flags"


## Saves the run flags that belong to a quest (its prefixes; for the Bassment the "item:" flags, without the prefix) into its progress.
func _store_quest_flags(s: RouteState, quest_id: String) -> void:
	var names: Array = []
	var prefixes: Array = graph.flag_prefixes(quest_id)
	for f in _flags():
		for pre in prefixes:
			if str(f).begins_with(str(pre)):
				names.append(str(f).substr(str(pre).length()) if _is_items(quest_id) else str(f))
				break
	names.sort()
	s.progress_for_write(quest_id)[_flag_key(quest_id)] = names


## ---------------------------------------------------------------- flags and saving

func _flags() -> Dictionary:
	if flags_source.is_valid():
		return NarrativeGraph.flag_set(flags_source.call())
	return NarrativeGraph.flag_set(run_flags)


static func _flags_ok(e: Dictionary, fset: Dictionary) -> bool:
	var c: Dictionary = e["condition"]
	for f in c.get("flags_all", []):
		if not fset.has(str(f)):
			return false
	for f in c.get("flags_none", []):
		if fset.has(str(f)):
			return false
	return true


## Saves the committed state through the store. False when there is no store to write to, the build must not overwrite a newer save, or the write failed.
func _save() -> bool:
	if store == null or state.newer_than_known:
		return false
	var d := state.to_dict()
	var ok := true
	if typeof(store) == TYPE_CALLABLE:
		var r: Variant = (store as Callable).call(d)
		ok = typeof(r) != TYPE_BOOL or bool(r)
	elif typeof(store) == TYPE_OBJECT and (store as Object).has_method("save"):
		ok = bool((store as Object).call("save", d))
	if not ok:
		save_failures += 1
		errors.append("the route state could not be saved (the committed state in memory is kept)")
	return ok
