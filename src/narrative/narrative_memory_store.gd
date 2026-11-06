class_name NarrativeMemoryStore
extends RefCounted
## A store for QuestRouter that keeps the `narrative` save value in memory: tests use it, so that nothing is written to the player's real save.
## The store interface is two methods: save(narrative: Dictionary) -> bool and load() -> Dictionary ({} when there is nothing saved).
## The real store (a later step, N2.2) writes the `narrative` key of user://story_run.json through RunProgress.save(), which writes a temporary file and renames it.

var saved: Dictionary = {}
var saves := 0
## Set to make the next save fail (returns false, keeps the old value), to test a failed write.
var fail_next := false
## Every saved value, as JSON text, oldest first.
var history: Array = []


func save(narrative: Dictionary) -> bool:
	if fail_next:
		fail_next = false
		return false
	saved = narrative.duplicate(true)
	saves += 1
	history.append(JSON.stringify(narrative, "", true))
	return true


func load() -> Dictionary:
	return saved.duplicate(true)
