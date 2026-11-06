class_name StoryLaneShade
extends Control
## A soft dark column behind each pad's falling-note lane so cues stay readable over the lit club without hiding the crowd.

var pad_view: PadView
var strength := 0.3  # darkest alpha, just above the pads
static var draw_usec := 0


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	var t0 := Time.get_ticks_usec()
	_draw_shade()
	draw_usec += Time.get_ticks_usec() - t0


func _draw_shade() -> void:
	if pad_view == null:
		return
	var inv := get_global_transform_with_canvas().affine_inverse()
	var rects := pad_view.pad_rects_global()
	for pad in rects:
		var r: Rect2 = rects[pad]
		var p: Vector2 = inv * r.position
		var bottom := p.y
		var steps := 12
		for layer in 3:  # three nested columns: a soft horizontal falloff instead of a hard-edged band
			var col_w := r.size.x * (0.78 + 0.13 * float(layer))
			var x := p.x + (r.size.x - col_w) * 0.5
			var k := [0.5, 0.3, 0.2][layer] as float
			for i in steps:
				var y0 := lerpf(0.0, bottom, float(i) / steps)
				var y1 := lerpf(0.0, bottom, float(i + 1) / steps)
				var u := float(i + 1) / steps
				var a := strength * k * u * u
				draw_rect(Rect2(x, y0, col_w, y1 - y0 + 1.0), Color(0.01, 0.0, 0.06, a))
