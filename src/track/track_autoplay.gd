class_name TrackAutoplay
extends RefCounted
## Scripted play for track mode, the same policies as the play screen's RW_AUTOPLAY: "perfect" presses every cue on
## its time and releases a hold at its tail; "accuracy:<0..1>" plays each cue with that probability (a fixed seed, so
## a run repeats); "none" plays nothing. The actions are one time-ordered list, so the result does not depend on the
## frame rate.

var policy := ""
var probability := 1.0
var _actions: Array = []  # [time, order (0 release, 1 press), pad]
var _next := 0


## True for a policy string the game understands ("perfect", "none", "accuracy:<f>").
static func is_valid_policy(text: String) -> bool:
	return text == "perfect" or text == "none" or (text.begins_with("accuracy:") and text.substr(9).is_valid_float())


## The probability a policy plays a cue with.
static func probability_of(text: String) -> float:
	if text.begins_with("accuracy:"):
		return clampf(float(text.substr(9)), 0.0, 1.0)
	return 0.0 if text == "none" else 1.0


## `skip` (optional, (cue: Dictionary) -> bool) leaves out the cues it picks, for tests that need one exact miss.
func setup(game_cues: Array, p_policy: String, skip: Callable = Callable()) -> void:
	policy = p_policy
	probability = probability_of(p_policy)
	_actions.clear()
	_next = 0
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	for c in game_cues:
		if rng.randf() >= probability or (skip.is_valid() and bool(skip.call(c))):
			continue
		_actions.append([float(c["time"]), 1, int(c["pad"])])
		if c["type"] == "hold":
			_actions.append([float(c["end_time"]), 0, int(c["pad"])])
	_actions.sort_custom(func(a: Array, b: Array) -> bool:
		if a[0] != b[0]:
			return a[0] < b[0]
		return a[1] < b[1])


## Performs every action due by song time `t` on `game`, each at its own time.
func step(game: TrackGame, t: float) -> void:
	while _next < _actions.size() and float(_actions[_next][0]) <= t:
		var a: Array = _actions[_next]
		if a[1] == 1:
			game.press(int(a[2]), float(a[0]), 1)
		else:
			game.release(int(a[2]), float(a[0]), 1)
		_next += 1
