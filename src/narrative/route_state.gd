class_name RouteState
extends RefCounted
## Where the player is on the narrative graph, and what they have done in each quest (docs/parallel-development/NARRATIVE_GRAPH.md section 3).
##
## There is a COMMITTED copy (every field but `pending`; this is what is saved) and at most one PENDING change (`pending`, memory only), held by
## QuestRouter against a request id. Only QuestRouter.commit() changes the committed copy, and only from the scene the player really landed on.
##
## Save format: the `narrative` key of user://story_run.json (to_dict / from_dict), version 1.

const VERSION := 1
const DEFAULT_HISTORY_LIMIT := 32

var location := ""  # the current mainline location; it does not change while a quest runs
var quest := ""  # the quest the player is in now, or ""
var entry_origin := ""  # the scene whose object started the current quest, or ""
var checkpoint := ""  # where a return lands: the hub of the location of entry_origin, or ""
## quest id -> {scene: String, completed: bool, visits: int, flags: [String] (paths) or items: [String] (the Bassment)}
var quest_progress: Dictionary = {}
var history: Array = []  # scene ids, newest last; the last is the current scene
var history_limit := DEFAULT_HISTORY_LIMIT
## Memory only, never saved: {} or {id: int, dest: Dictionary, changes: {dest id: change}}. Set and cleared by QuestRouter.
var pending: Dictionary = {}
## Counts the commits of this object (memory only): a held change is stale when it was computed at another revision.
var revision := 0
## True when the loaded save carried a `narrative` key of a newer version: it was ignored, and must not be overwritten.
var newer_than_known := false
## True when the loaded save was written in the middle of a quest and was closed on load (the player starts on the checkpoint hub).
var closed_on_load := false


func current_scene() -> String:
	return str(history.back()) if not history.is_empty() else ""


func in_quest() -> bool:
	return quest != ""


## The progress of a quest; a quest never entered reads as {scene: "", completed: false, visits: 0}.
func progress_of(quest_id: String) -> Dictionary:
	if quest_progress.has(quest_id):
		return quest_progress[quest_id]
	return {"scene": "", "completed": false, "visits": 0}


## The progress dictionary of a quest, created when missing.
func progress_for_write(quest_id: String) -> Dictionary:
	if not quest_progress.has(quest_id):
		quest_progress[quest_id] = {"scene": "", "completed": false, "visits": 0}
	return quest_progress[quest_id]


func push_history(scene_id: String) -> void:
	history.append(scene_id)
	while history.size() > history_limit:
		history.pop_front()


## A copy of the committed fields (not `pending`, not `revision`).
func copy() -> RouteState:
	var s := RouteState.new()
	s.location = location
	s.quest = quest
	s.entry_origin = entry_origin
	s.checkpoint = checkpoint
	s.quest_progress = quest_progress.duplicate(true)
	s.history = history.duplicate()
	s.history_limit = history_limit
	s.revision = revision
	s.newer_than_known = newer_than_known
	s.closed_on_load = closed_on_load
	return s


## Takes over the committed fields of `other` (a held change being applied). `pending` is untouched.
func adopt(other: RouteState) -> void:
	location = other.location
	quest = other.quest
	entry_origin = other.entry_origin
	checkpoint = other.checkpoint
	quest_progress = other.quest_progress.duplicate(true)
	history = other.history.duplicate()
	revision += 1


## The committed fields as JSON text with sorted keys: two states are the same committed state when these are equal.
func snapshot() -> String:
	return JSON.stringify(to_dict(), "", true)


## The value of the save's `narrative` key.
func to_dict() -> Dictionary:
	var progress := {}
	for q in quest_progress:
		var p: Dictionary = quest_progress[q]
		var out := {"scene": str(p.get("scene", "")), "completed": bool(p.get("completed", false)), "visits": int(p.get("visits", 0))}
		for key in ["flags", "items"]:
			if p.has(key):
				out[key] = (p[key] as Array).duplicate()
		progress[str(q)] = out
	return {"version": VERSION, "location": location, "quest": quest, "entry_origin": entry_origin, "checkpoint": checkpoint,
		"quest_progress": progress, "history": history.duplicate()}


## Reads a `narrative` value. Tolerant: a missing or malformed value gives the default state (empty, history at `start_scene`); unknown keys are dropped;
## a version newer than this build's is ignored (newer_than_known); a save written in the middle of a quest is closed (the player starts on the checkpoint).
static func from_dict(d: Variant, start_scene: String = "", limit: int = DEFAULT_HISTORY_LIMIT) -> RouteState:
	var s := RouteState.new()
	s.history_limit = maxi(limit, 8)
	if typeof(d) != TYPE_DICTIONARY or (d as Dictionary).is_empty():
		s._start_at(start_scene)
		return s
	var data: Dictionary = d
	if int(data.get("version", VERSION)) > VERSION:
		s.newer_than_known = true
		s._start_at(start_scene)
		return s
	s.location = str(data.get("location", ""))
	s.quest = str(data.get("quest", ""))
	s.entry_origin = str(data.get("entry_origin", ""))
	s.checkpoint = str(data.get("checkpoint", ""))
	if typeof(data.get("quest_progress")) == TYPE_DICTIONARY:
		for q in (data["quest_progress"] as Dictionary):
			if typeof(data["quest_progress"][q]) != TYPE_DICTIONARY:
				continue
			var p: Dictionary = data["quest_progress"][q]
			var out := {"scene": str(p.get("scene", "")), "completed": bool(p.get("completed", false)), "visits": maxi(int(p.get("visits", 0)), 0)}
			for key in ["flags", "items"]:
				if typeof(p.get(key)) == TYPE_ARRAY:
					var names: Array = []
					for x in p[key]:
						names.append(str(x))
					out[key] = names
			s.quest_progress[str(q)] = out
	if typeof(data.get("history")) == TYPE_ARRAY:
		for x in data["history"]:
			s.history.append(str(x))
		while s.history.size() > s.history_limit:
			s.history.pop_front()
	if s.quest != "":  # quit in the middle of a quest: closed on load, all progress kept
		s.closed_on_load = true
		var back_to := s.checkpoint
		s.quest = ""
		s.entry_origin = ""
		s.checkpoint = ""
		if back_to != "":
			s.push_history(back_to)
	if s.history.is_empty():
		s._start_at(start_scene)
	return s


func _start_at(scene_id: String) -> void:
	history.clear()
	if scene_id != "":
		history.append(scene_id)


## Migration for a save without a `narrative` key: a quest whose path already has endings starts as completed.
func migrate_from_paths(paths: Variant, path_of_quest: Dictionary) -> void:
	if typeof(paths) != TYPE_DICTIONARY:
		return
	for q in path_of_quest:
		var info: Variant = (paths as Dictionary).get(str(path_of_quest[q]))
		if typeof(info) == TYPE_DICTIONARY:
			var ends: Variant = (info as Dictionary).get("endings")
			if (typeof(ends) == TYPE_ARRAY and not (ends as Array).is_empty()) or (typeof(ends) == TYPE_DICTIONARY and not (ends as Dictionary).is_empty()):
				progress_for_write(str(q))["completed"] = true


## The invariants of NARRATIVE_GRAPH.md 3.1 against a graph, as sentences (empty when they all hold).
func invariant_errors(g: NarrativeGraph) -> Array:
	var errs: Array = []
	if (quest == "") != (entry_origin == "") or (quest == "") != (checkpoint == ""):
		errs.append("quest, entry_origin and checkpoint are not all empty or all set")
	var cur := current_scene()
	if history.size() > history_limit:
		errs.append("the history has %d entries, more than the limit %d" % [history.size(), history_limit])
	if cur == "" or not g.resolves(cur):
		errs.append("the current scene '%s' is not in the graph" % cur)
		return errs
	if quest != "":
		var org := g.location_of(entry_origin)
		if org == "":
			errs.append("the entry origin %s is not a mainline scene" % entry_origin)
		elif checkpoint != g.hub_of_location(org):
			errs.append("the checkpoint %s is not the hub of the entry origin's location %s" % [checkpoint, org])
		if location != org:
			errs.append("the location %s changed during the quest (the entry origin is in %s)" % [location, org])
		if g.quest_of(cur) != quest:
			errs.append("the current scene %s is not in the current quest %s" % [cur, quest])
	else:
		if not g.is_mainline(cur):
			errs.append("no quest is set, but the current scene %s is a quest scene" % cur)
		elif g.location_of(cur) != location:
			errs.append("the location %s does not match the current scene %s" % [location, cur])
	for q in quest_progress:
		var sc := str((quest_progress[q] as Dictionary).get("scene", ""))
		if sc != "" and (not g.resolves(sc) or g.quest_of(sc) != str(q)):
			errs.append("the saved scene '%s' of %s is not a scene of that quest" % [sc, q])
	return errs
