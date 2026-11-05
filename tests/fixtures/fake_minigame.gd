class_name FakeMinigame
extends MinigameActivity
## A scripted activity for the lifecycle tests: it records every call the host makes and finishes when told to (`finish_now`), when it is asked to leave, or when it is interrupted.
## A door of the room ("exit:<route>", when listed in `taken`) leaves by that route; the plain "exit" leaves by none.

var calls: Array = []  # [{call, t, ...}]
var taken: Array = ["bet", "exit"]  # the targets it accepts
var finish_now := false
var with_view := false
var last_update := -1.0
var ctx_seen: Dictionary = {}


func setup(ctx: Dictionary) -> void:
	super.setup(ctx)
	ctx_seen = ctx
	with_view = bool(config.get("with_view", with_view))
	calls.append({"call": "setup"})


func begin(t: float) -> void:
	super.begin(t)
	calls.append({"call": "begin", "t": t})


func update(t: float) -> void:
	last_update = t


func targets() -> Array:
	return taken


func tap(target: String, t: float) -> bool:
	calls.append({"call": "tap", "target": target, "t": t})
	if target == "exit":  # the plain way out: get up, the room decides
		request_leave(t)
		return true
	if target.begins_with("exit:") and target in taken:
		leave_route = exit_route(target)
		request_leave(t)
		return true
	return target in taken


func set_wobble(level: int, t: float) -> void:
	super.set_wobble(level, t)
	calls.append({"call": "wobble", "level": level, "t": t})


func request_leave(t: float) -> void:
	calls.append({"call": "leave", "t": t})
	_finish("left")


func interrupt(reason: String, t: float) -> void:
	calls.append({"call": "interrupt", "reason": reason, "t": t})
	_finish(reason)


func is_done() -> bool:
	return _done or finish_now


func done_reason() -> String:
	return _reason if _done else ("host" if finish_now else "")


func make_view() -> Control:
	return FakeMinigameView.new() if with_view else null


func count(call: String) -> int:
	var n := 0
	for c in calls:
		if str(c["call"]) == call:
			n += 1
	return n
