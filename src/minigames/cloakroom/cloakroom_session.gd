class_name CloakroomSession
extends RefCounted
## The cloakroom's progress between visits, kept for the run in this process (CONTRACTS.md 4: "leaving mid-task keeps the activity's in-progress state in memory for
## the run (RaveSession), keyed by theme + activity"). RaveSession does not exist yet, so this static store stands in for it: the controller builds a NEW activity object
## for every request, so the state cannot live in the activity. `key` is "<theme>/cloakroom". HOOK: the host calls `reset()` when a run starts (or RaveSession adopts this
## dictionary); a finished cloakroom clears its own entry, a run that ends clears it too.

static var _store: Dictionary = {}


static func save(key: String, snapshot: Dictionary) -> void:
	_store[key] = snapshot.duplicate(true)


static func load_state(key: String) -> Dictionary:
	return (_store[key] as Dictionary).duplicate(true) if _store.has(key) else {}


static func has(key: String) -> bool:
	return _store.has(key)


static func clear(key: String) -> void:
	_store.erase(key)


static func reset() -> void:
	_store.clear()
