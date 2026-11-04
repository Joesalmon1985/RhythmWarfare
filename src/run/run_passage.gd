class_name RunPassage
extends RefCounted
## The world swap as a walk through a doorway, as pure functions of song time: the picture closes to a lit doorway over the last beats of a phase and opens again on
## the new world over the first beats of the next one. The music does not care: the swap itself is still the downbeat.

const MIN_OPEN := 0.16  # the doorway's size when the frame is shut, as a share of the stage view
const CLOSE_BEATS := 2.0
const OPEN_BEATS := 2.5


static func _smooth(u: float) -> float:
	u = clampf(u, 0.0, 1.0)
	return u * u * (3.0 - 2.0 * u)


## 1 = the whole view, MIN_OPEN = shut to the doorway. `t_swap` is the downbeat the swap happens on; a negative one means no passage is under way.
static func aperture(t: float, t_swap: float, beat_s: float, close_beats := CLOSE_BEATS, open_beats := OPEN_BEATS) -> float:
	if t_swap < 0.0:
		return 1.0
	var close_s := close_beats * beat_s
	var open_s := open_beats * beat_s
	if t < t_swap - close_s:
		return 1.0
	if t < t_swap:
		return lerpf(1.0, MIN_OPEN, _smooth((t - (t_swap - close_s)) / maxf(close_s, 1.0e-6)))
	if t < t_swap + open_s:
		return lerpf(MIN_OPEN, 1.0, _smooth((t - t_swap) / maxf(open_s, 1.0e-6)))
	return 1.0


## The doorway rectangle inside a view of `size` for an aperture: centred, a little low, with the floor line fixed.
static func doorway(size: Vector2, a: float) -> Rect2:
	var u := clampf((a - MIN_OPEN) / (1.0 - MIN_OPEN), 0.0, 1.0)
	var w := lerpf(size.x * MIN_OPEN * 0.8, size.x, u)
	var h := lerpf(size.y * 0.5, size.y, u)
	var floor_y := lerpf(size.y * 0.86, size.y, u)
	return Rect2(Vector2((size.x - w) * 0.5, floor_y - h), Vector2(w, h))
