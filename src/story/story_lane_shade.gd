class_name StoryLaneShade
extends Control
## A soft dark column behind each pad's falling-note lane so cues stay readable over the lit club without hiding the crowd.

var pad_view: PadView


func _process(_delta: float) -> void:
	queue_redraw()


func _draw() -> void:
	if pad_view == null:
		return
	var inv := get_global_transform_with_canvas().affine_inverse()
	var rects := pad_view.pad_rects_global()
	for pad in rects:
		var r: Rect2 = rects[pad]
		var p: Vector2 = inv * r.position
		var col_w := r.size.x * 0.96
		var x := p.x + (r.size.x - col_w) * 0.5
		var top := 0.0
		var bottom := p.y
		var steps := 10
		for i in steps:
			var y0 := lerpf(top, bottom, float(i) / steps)
			var y1 := lerpf(top, bottom, float(i + 1) / steps)
			var a := lerpf(0.0, 0.34, float(i + 1) / steps)
			draw_rect(Rect2(x, y0, col_w, y1 - y0 + 1.0), Color(0.01, 0.0, 0.06, a))
