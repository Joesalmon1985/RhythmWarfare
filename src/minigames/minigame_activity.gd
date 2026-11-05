class_name MinigameActivity
extends RefCounted
## The base class of a minigame that runs inside the continuous run (docs/BLACKJACK_INTEGRATION.md section 5.3). A subclass overrides what it needs; every default is safe and inert.
##
## The host (MinigameController, driven by RunPlay) sets the activity up once, calls `begin` when the player is seated, advances it with `update` every frame, forwards touches with `tap`,
## tells it about the rhythm with `set_wobble` and `interrupt`, and resumes the adventure when `is_done()` turns true. An activity is a pure function of the taps so far and song time: it
## holds no clock of its own and never reads the judge. `make_view()` is the only place a node may be made, and pure tests never call it.

var wallet: Variant = null  # the run's RunWallet (may be null in tests)
var rng_seed := 0
var beat_s := 60.0 / 174.0
var config: Dictionary = {}
var began := false
var wobble := 0
var _done := false
var _reason := ""


## `ctx`: {"wallet": RunWallet or null, "seed": int, "beat_s": float, "config": Dictionary (the whole content/minigames/<id>.json)}.
func setup(ctx: Dictionary) -> void:
	wallet = ctx.get("wallet", null)
	rng_seed = int(ctx.get("seed", 0))
	beat_s = float(ctx.get("beat_s", beat_s))
	config = ctx.get("config", {})


## The player is seated at song time `t`.
func begin(_t: float) -> void:
	began = true


## Advance to song time `t`.
func update(_t: float) -> void:
	pass


## Ids of what may be touched now, e.g. ["bet", "exit"].
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
