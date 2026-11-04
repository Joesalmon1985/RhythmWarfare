class_name StoryFreeLook
extends RefCounted
## The player's free look: a head turn of up to plus or minus MAX_DEG degrees away from the rail's facing, set by a mouse or touch drag on the stage
## area or by the Q / E keys, easing back to centre once let go. It is player input (wall-clock dt), not part of the song-time rail, and it
## never touches the pad strip. While an authored player_look is under way the offset is pulled to zero faster.

const MAX_DEG := 60.0
const RETURN_RATE := 2.2  # per second: the offset decays by exp(-rate * dt) once released (frame-rate independent)
const LOOK_RETURN_RATE := 7.0
const KEY_DEG_PER_S := 100.0
const DRAG_DEG_PER_PX := 0.12

var offset := 0.0  # degrees, positive turns left (the same sign as yaw)
var dragging := false
var key_axis := 0.0  # -1 (E, right) .. +1 (Q, left)


## A drag of dx screen pixels to the right turns the head right (negative yaw).
func drag(dx_px: float) -> void:
	dragging = true
	offset = clampf(offset - dx_px * DRAG_DEG_PER_PX, -MAX_DEG, MAX_DEG)


func release() -> void:
	dragging = false


func set_key_axis(axis: float) -> void:
	key_axis = clampf(axis, -1.0, 1.0)


func update(dt: float, authored_look_active := false) -> void:
	if absf(key_axis) > 0.0:
		offset = clampf(offset + key_axis * KEY_DEG_PER_S * dt, -MAX_DEG, MAX_DEG)
	elif not dragging:
		var rate := LOOK_RETURN_RATE if authored_look_active else RETURN_RATE
		offset *= exp(-rate * dt)
		if absf(offset) < 0.01:
			offset = 0.0
	elif authored_look_active:
		offset *= exp(-LOOK_RETURN_RATE * dt)


func reset() -> void:
	offset = 0.0
	dragging = false
	key_axis = 0.0
