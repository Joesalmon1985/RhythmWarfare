class_name RunExitsView
extends Control
## The room's exits, lit while the route window is open: a glowing doorway at the waypoint that leads toward each candidate world (projected with the stage's own
## camera, so it sits in the room), or an arrow at the screen edge on the side it lies when it is out of sight. The touch arrows are still the controls.

var items: Array = []  # [{dir, glyph, at: Vector2 (x, z), ground: float, chosen: bool}]
var pose_fn: Callable  # () -> {cam: Vector3, yaw, pitch}
var now_fn: Callable  # () -> song time
var beat_s := 60.0 / 174.0
var fade_from := 0.0  # song time the window opened (the lights come up over one beat)


func _process(_d: float) -> void:
	if visible:
		queue_redraw()


## Screen-space placement of one exit for a camera pose: {visible, screen, scale} or, out of sight, {visible: false, side: -1 or 1}.
static func place(at: Vector2, ground: float, pose: Dictionary, view: Vector2) -> Dictionary:
	var p := StoryProjector.project(Vector3(at.x, ground, at.y), pose, view)
	if p["visible"] and float(p["depth"]) > 0.4:
		return {"visible": true, "screen": p["screen"], "scale": p["scale"]}
	var cam: Vector3 = pose["cam"]
	var d := Vector2(at.x - cam.x, at.y - cam.z)
	var side := 1.0 if d.dot(StoryProjector.right(float(pose["yaw"]))) >= 0.0 else -1.0
	return {"visible": false, "side": side}


func _draw() -> void:
	if items.is_empty() or not pose_fn.is_valid():
		return
	var pose: Dictionary = pose_fn.call()
	if pose.is_empty():
		return
	var t := float(now_fn.call()) if now_fn.is_valid() else 0.0
	var up := clampf((t - fade_from) / beat_s, 0.0, 1.0)
	var pulse := 0.65 + 0.35 * sin(t / beat_s * PI)
	var font := ThemeDB.fallback_font
	for it in items:
		var col := Color(1.0, 0.9, 0.5) if bool(it["chosen"]) else Color(0.6, 0.85, 1.0)
		col.a = (0.9 if bool(it["chosen"]) else 0.7) * up
		var pl := place(it["at"], float(it["ground"]), pose, size)
		var glyph := str(it["glyph"])
		if bool(pl["visible"]):
			var s := float(pl["scale"])
			var w := clampf(1.1 * s, 18.0, size.x * 0.25)
			var h := clampf(2.1 * s, 32.0, size.y * 0.6)
			var base: Vector2 = pl["screen"]
			var r := Rect2(base.x - w * 0.5, base.y - h, w, h)
			draw_rect(r.grow(w * 0.25), Color(col.r, col.g, col.b, 0.12 * pulse * up))
			draw_rect(r, Color(col.r, col.g, col.b, 0.34 * pulse * up))
			draw_rect(r, col, false, 3.0)
			draw_string(font, Vector2(r.position.x, r.position.y - 6.0), glyph, HORIZONTAL_ALIGNMENT_CENTER, w, int(clampf(h * 0.28, 16.0, 40.0)), col)
		else:
			var side := float(pl["side"])
			var x := size.x - 34.0 if side > 0.0 else 34.0
			var y := size.y * 0.55 + (-30.0 if str(it["dir"]) == "up" else 30.0 if str(it["dir"]) == "right" else 0.0)
			var pts := PackedVector2Array([Vector2(x + side * 14.0, y), Vector2(x - side * 12.0, y - 18.0), Vector2(x - side * 12.0, y + 18.0)])
			draw_colored_polygon(pts, Color(col.r, col.g, col.b, col.a * pulse))
			draw_string(font, Vector2(x - 12.0, y + 38.0), glyph, HORIZONTAL_ALIGNMENT_CENTER, 24.0, 18, col)
