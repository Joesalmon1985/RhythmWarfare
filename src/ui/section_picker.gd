class_name SectionPicker
extends RefCounted
## Which defense point (section) a tap on the battle area picks: the nearest one by horizontal distance.


## Index into `point_xs` of the entry nearest to `tap_x`; the lower index wins a tie. -1 for an empty array.
static func index_for(tap_x: float, point_xs: Array) -> int:
	var best := -1
	var best_d := INF
	for i in point_xs.size():
		var d := absf(float(point_xs[i]) - tap_x)
		if d < best_d:
			best_d = d
			best = i
	return best
