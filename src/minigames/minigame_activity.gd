class_name MinigameActivity
extends RefCounted
## The base class of a minigame that runs inside the continuous run (docs/BLACKJACK_INTEGRATION.md section 5.3). A subclass overrides what it needs; every default is safe and inert.
##
## The host (MinigameController, driven by RunPlay) sets the activity up once, calls `begin` when the player is seated, advances it with `update` every frame, forwards touches with `tap`,
## tells it about the rhythm with `set_wobble` and `interrupt`, and resumes the adventure when `is_done()` turns true. An activity is a pure function of the taps so far and song time: it
## holds no clock of its own and never reads the judge. `make_view()` is the only place a node may be made, and pure tests never call it.
##
## The room's ways out (`exits`, handed over in `setup` by the host): one entry per exit of the scene the player sat down in, the default first, each
## {id (the exit hotspot), route (the destination node), scene, world (the destination's), dir, default, tint, light}. An activity offers one target per exit, "exit:<route>", where it would
## offer a plain "exit"; with no exits it offers the plain "exit" (get up, the room decides). The bare "exit" is always accepted as the default exit. The door the player left by is
## `leave_route` ("" none); the host carries it out once the activity is done (`done_route`).

var wallet: Variant = null  # the run's RunWallet (may be null in tests)
var rng_seed := 0
var beat_s := 60.0 / 174.0
var config: Dictionary = {}
var began := false
var wobble := 0
var exits: Array = []  # the room's ways out (see above), read-only
var leave_route := ""  # the route of the door the player chose to leave by ("" none)
var _done := false
var _reason := ""
var _exit_ids: Array = ["exit"]


## `ctx`: {"wallet": RunWallet or null, "seed": int, "beat_s": float, "config": Dictionary (the whole content/minigames/<id>.json), "exits": Array (optional, see above)}.
func setup(ctx: Dictionary) -> void:
	wallet = ctx.get("wallet", null)
	rng_seed = int(ctx.get("seed", 0))
	beat_s = float(ctx.get("beat_s", beat_s))
	config = ctx.get("config", {})
	exits = normalize_exits(ctx.get("exits", []))
	_exit_ids = []
	for e: Dictionary in exits:
		_exit_ids.append("exit:" + str(e["route"]))
	if _exit_ids.is_empty():
		_exit_ids.append("exit")
	_exit_ids.make_read_only()


## The exits as a clean, read-only list: entries without a route or repeating one are dropped, at most four are kept, the default is first.
static func normalize_exits(list: Variant) -> Array:
	var out: Array = []
	if typeof(list) != TYPE_ARRAY:
		return out
	var seen := {}
	for e: Variant in list:
		if typeof(e) != TYPE_DICTIONARY or str((e as Dictionary).get("route", "")) == "" or seen.has(str(e["route"])):
			continue
		var d: Dictionary = e
		seen[str(d["route"])] = true
		var n := {"id": str(d.get("id", "")), "route": str(d["route"]), "scene": str(d.get("scene", "")), "world": str(d.get("world", "")), "dir": str(d.get("dir", "")),
			"default": bool(d.get("default", false)), "tint": str(d.get("tint", "")), "light": float(d.get("light", 0.5))}
		n.make_read_only()
		if bool(n["default"]):
			out.push_front(n)
		else:
			out.append(n)
	for i in range(1, out.size()):  # one default at most: the first
		if bool(out[i]["default"]):
			var n: Dictionary = out[i].duplicate()
			n["default"] = false
			n.make_read_only()
			out[i] = n
	out = out.slice(0, 4)
	out.make_read_only()
	return out


## True for a target that gets the player up: "exit" or "exit:<route>".
static func is_exit_target(target: String) -> bool:
	return target == "exit" or target.begins_with("exit:")


## The exit targets on offer: "exit:<route>" per exit, or the plain "exit" when the room gave none. Read-only.
func exit_targets() -> Array:
	return _exit_ids


## The exit target `target` stands for: the bare "exit" is the default exit's when the room has exits; anything else is itself.
func exit_alias(target: String) -> String:
	if target == "exit" and not exits.is_empty():
		return "exit:" + str(exits[0]["route"])
	return target


## The route an exit target leads to ("" for the plain "exit", or a target that is not an exit of this room).
func exit_route(target: String) -> String:
	var id := exit_alias(target)
	if not id.begins_with("exit:"):
		return ""
	var r := id.substr(5)
	for e: Dictionary in exits:
		if str(e["route"]) == r:
			return r
	return ""


## The route to carry out once done: the door the player left by, only when they left by choice ("" otherwise).
func done_route() -> String:
	return leave_route if _done and _reason == "left" else ""


## The player is seated at song time `t`.
func begin(_t: float) -> void:
	began = true


## Advance to song time `t`.
func update(_t: float) -> void:
	pass


## Ids of what may be touched now, e.g. ["bet", "exit"] (or ["bet", "exit:<route>", ...] when the room has exits).
func targets() -> Array:
	return []


## A touch on a target; false when it is not touchable now (the default has nothing to touch).
func tap(_target: String, _t: float) -> bool:
	return false


## 0 steady, 1 wobbling (two failed blocks in a row).
func set_wobble(level: int, _t: float) -> void:
	wobble = level


## The player chose to get up.
func request_leave(_t: float) -> void:
	_finish("left")


## Not the player's choice: "fall" | "run_over" | "host". Unresolved stakes are refunded by the subclass.
func interrupt(reason: String, _t: float) -> void:
	_finish(reason)


## The leaving or falling animation has finished: the host may resume the adventure.
func is_done() -> bool:
	return _done


## "left" | "fall" | "run_over" | "host" ("" until done).
func done_reason() -> String:
	return _reason


## A snapshot for the view and the tests.
func state() -> Dictionary:
	return {"began": began, "wobble": wobble, "done": _done, "reason": _reason}


## The presentation node (null in pure tests); the host mounts it in the low-res viewport (see RunPlay `_mount_minigame_view` for the properties it sets).
func make_view() -> Control:
	return null


func _finish(reason: String) -> void:
	if not _done:
		_done = true
		_reason = reason
