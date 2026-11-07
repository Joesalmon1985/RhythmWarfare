## (no class_name: the tests preload it)
extends MinigameActivity
## A world-staged activity for the engine tests (CONTRACTS.md 10, package A8): no view (make_view null), a `things()` method the host reads every frame, and people and
## feedback asked of the WorldThings port it is handed as ctx["world"]. Two pictogram controls. It finishes when told to (`finish_now`) or when an exit is pressed.

const CRATE := "engine_test_crate"  # tools/engine/make_thing_sheets.py (PLACEHOLDER art)

var world: Object = null
var finish_now := false
var now := 0.0
var taps: Array = []


func setup(ctx: Dictionary) -> void:
	super.setup(ctx)
	world = ctx.get("world", null)


func begin(t: float) -> void:
	super.begin(t)
	now = t
	if world != null:
		world.people("b01", "raise_glass", t, 0.0)
		world.people("nobody_here", "happy", t, 0.0)  # (an actor this room does not cast: a no-op)
		world.feedback("staged_crate", "tick", t)


func update(t: float) -> void:
	now = t


func tap(target: String, t: float) -> bool:
	taps.append(target)
	if world != null:
		world.feedback("staged_crate", "tick" if target == "same" else "cross", t)
	if target == "exit":
		request_leave(t)
	return true


func is_done() -> bool:
	return _done or finish_now


func done_reason() -> String:
	return _reason if _done else ("done" if finish_now else "")


func things() -> Array:
	if not began or is_done():
		return []
	return [{"id": "staged_crate", "sprite": CRATE, "at": [0.0, 2.0], "sector": "floor", "size": [0.8, 0.8], "frame": int(floorf(now / beat_s)) % 4}]


func controls() -> Array:
	return [{"id": "same", "label": "", "pictogram": "same"}, {"id": "different", "label": "", "pictogram": "different"}]


func make_view() -> Control:
	return null
