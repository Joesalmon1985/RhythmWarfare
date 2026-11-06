class_name NarrativeRunStore
extends RefCounted
## The game's store for QuestRouter (work package N2.2): the route state is the `narrative` key of the run save, user://story_run.json, written by RunProgress.save()
## (a temporary file, then a rename: atomic). Its own `version` is inside the value (RouteState.VERSION); the file's version stays 2, as when `paths` was added.
## The store interface is QuestRouter's: save(narrative: Dictionary) -> bool and load() -> Dictionary ({} when the save has no `narrative` key yet: an old save, migrated by
## QuestRouter.load_state from its `paths`).

const KEY := "narrative"

var progress: RunProgress
var saves := 0


func _init(p_progress: RunProgress) -> void:
	progress = p_progress


func save(narrative: Dictionary) -> bool:
	if progress == null:
		return false
	progress.data[KEY] = narrative.duplicate(true)
	var ok := progress.save()
	if ok:
		saves += 1
	return ok


func load() -> Dictionary:
	if progress == null:
		return {}
	var v: Variant = progress.data.get(KEY, null)
	return (v as Dictionary).duplicate(true) if typeof(v) == TYPE_DICTIONARY else {}


## The rest of the save the migration reads (QuestRouter.load_state's `extra`): {"paths": ...}.
func extra() -> Dictionary:
	return {"paths": progress.paths.duplicate(true) if progress != null else {}}
