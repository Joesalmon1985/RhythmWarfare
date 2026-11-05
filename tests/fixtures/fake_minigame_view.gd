class_name FakeMinigameView
extends Control
## The smallest view the host accepts: it answers `hit` with "bet" in the left half of the stage area and "exit" in the right half, and keeps what the host set on it.

var now_fn: Callable
var beat_s := 0.0
var screen_size := Vector2.ZERO
var state_fn: Callable
var hits: Array = []


func hit(local_pos: Vector2) -> String:
	hits.append(local_pos)
	if screen_size == Vector2.ZERO or local_pos.x < 0.0 or local_pos.y < 0.0 or local_pos.x > screen_size.x or local_pos.y > screen_size.y:
		return ""
	return "bet" if local_pos.x < screen_size.x * 0.5 else "exit"
