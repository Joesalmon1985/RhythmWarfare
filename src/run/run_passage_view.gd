class_name RunPassageView
extends Control
## Draws RunPassage's frame over the stage: black round a doorway whose size is the aperture, with light spilling through it while it is small.

var aperture := 1.0
var spill := Color(1.0, 0.92, 0.75)


func set_aperture(a: float) -> void:
	if absf(a - aperture) > 1.0e-4:
		aperture = a
		queue_redraw()


func _draw() -> void:
	if aperture >= 0.999:
		return
	var r := RunPassage.doorway(size, aperture)
	var black := Color(0.01, 0.01, 0.02, 1.0)
	draw_rect(Rect2(0, 0, size.x, r.position.y), black)
	draw_rect(Rect2(0, r.end.y, size.x, size.y - r.end.y), black)
	draw_rect(Rect2(0, r.position.y, r.position.x, r.size.y), black)
	draw_rect(Rect2(r.end.x, r.position.y, size.x - r.end.x, r.size.y), black)
	var glow := clampf((1.0 - aperture) / (1.0 - RunPassage.MIN_OPEN), 0.0, 1.0)
	draw_rect(r, Color(spill.r, spill.g, spill.b, 0.28 * glow))
	draw_rect(r, Color(spill.r, spill.g, spill.b, 0.55 * glow), false, 3.0)
