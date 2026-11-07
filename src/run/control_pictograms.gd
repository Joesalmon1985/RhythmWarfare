class_name ControlPictograms
extends RefCounted
## The pictograms of an activity's controls in the pad slots (CONTRACTS.md 10: pictograms, no words): flat silhouettes in the slot's own light with an ink drop shadow,
## drawn by RunActivityInput into the pad view's canvas. One hook, in this order:
##   draw: Callable(canvas_item, rect) or (canvas_item, rect, alpha)   the activity draws its own (CloakroomArt.draw_pictogram, BarDraw)
##   icon: "res://...png"                                              a texture, centred, about 62 % of the slot's short side
##   pictogram (else shape) + color                                    a built-in silhouette (SHAPES), tinted by the control's colour (the slot's light)
## draw() answers false when the control has none of these (the caller then draws its label).

const SHAPES := ["same", "different", "circle", "square", "diamond", "triangle", "star", "drop", "bottle", "leaf", "bolt",
	"gem", "hex", "egg", "lemon", "spiky", "crescent", "moon", "ring", "swirl", "comet", "flame", "cloud", "rainbow", "can", "shaker", "box", "left", "right", "knob"]


static func draw(ci: CanvasItem, spec: Dictionary, face: Rect2, a: float, base: Color, lit: bool) -> bool:
	var d: Variant = spec.get("draw", null)
	if d is Callable and (d as Callable).is_valid():
		var cb: Callable = d
		if cb.get_argument_count() >= 3:
			cb.call(ci, face, a)
		else:
			cb.call(ci, face)
		return true
	var icon := str(spec.get("icon", ""))
	if icon.begins_with("res://") and ResourceLoader.exists(icon):
		var tex := load(icon) as Texture2D
		if tex != null:
			var side := minf(face.size.x, face.size.y) * 0.62
			ci.draw_texture_rect(tex, Rect2(face.get_center() - Vector2(side, side) * 0.5, Vector2(side, side)), false, Color(1, 1, 1, a))
			return true
	var name := str(spec.get("pictogram", ""))
	if name == "":
		name = str(spec.get("shape", ""))
	if name == "" or name not in SHAPES:
		return false
	var col: Color = base.lightened(0.45 if lit else 0.1)
	if spec.has("color"):
		col = (Color.from_string(str(spec["color"]), col) if typeof(spec["color"]) == TYPE_STRING else spec["color"] as Color).lerp(Color.WHITE, 0.15 if lit else 0.0)
	col.a = a * (1.0 if lit else 0.6)
	var ink := Color(0.02, 0.0, 0.08, 0.55 * a)
	var c := face.get_center() + Vector2(0, face.size.y * 0.04)
	var s := minf(face.size.x, face.size.y) * 0.2
	shape(ci, name, c + Vector2(0, maxf(2.0, s * 0.08)), s, ink)  # a drop shadow, then the shape
	shape(ci, name, c, s, col)
	return true


static func shape(ci: CanvasItem, name: String, c: Vector2, s: float, k: Color) -> void:
	match name:
		"same":  # two identical squares joined by a bar
			ci.draw_rect(Rect2(c + Vector2(-1.6, -0.55) * s, Vector2(1.1, 1.1) * s), k)
			ci.draw_rect(Rect2(c + Vector2(0.5, -0.55) * s, Vector2(1.1, 1.1) * s), k)
			ci.draw_rect(Rect2(c + Vector2(-0.5, -0.12) * s, Vector2(1.0, 0.24) * s), k)
		"different":  # a square and a triangle apart
			ci.draw_rect(Rect2(c + Vector2(-1.7, -0.55) * s, Vector2(1.1, 1.1) * s), k)
			ci.draw_colored_polygon(PackedVector2Array([c + Vector2(1.1, -0.65) * s, c + Vector2(1.75, 0.6) * s, c + Vector2(0.45, 0.6) * s]), k)
		"star", "spiky":
			var pts := PackedVector2Array()
			var spikes := 5 if name == "star" else 8
			for i in spikes * 2:
				var rr := s * (1.15 if i % 2 == 0 else (0.5 if name == "star" else 0.7))
				pts.append(c + Vector2.from_angle(-PI * 0.5 + PI * float(i) / float(spikes)) * rr)
			ci.draw_colored_polygon(pts, k)
		"gem", "diamond":
			ci.draw_colored_polygon(PackedVector2Array([c + Vector2(0, -1.2) * s, c + Vector2(1.0, -0.2) * s, c + Vector2(0, 1.2) * s, c + Vector2(-1.0, -0.2) * s]), k)
		"hex":
			var hp := PackedVector2Array()
			for i in 6:
				hp.append(c + Vector2.from_angle(PI / 6.0 + TAU * float(i) / 6.0) * s * 1.1)
			ci.draw_colored_polygon(hp, k)
		"egg", "lemon", "drop":
			var ep := PackedVector2Array()
			for i in 20:
				var ang := TAU * float(i) / 20.0
				var v := Vector2(cos(ang) * 0.85, sin(ang) * 1.1)
				if name == "drop" and v.y < 0.0:
					v.x *= 1.0 + v.y * 0.8
				ep.append(c + v * s)
			ci.draw_colored_polygon(ep, k)
		"crescent", "moon":
			var cp := PackedVector2Array()
			for i in 13:
				cp.append(c + Vector2.from_angle(PI * 0.35 + PI * 1.3 * float(i) / 12.0) * s * 1.05)
			for i in 13:
				cp.append(c + Vector2(0.35, -0.2) * s + Vector2.from_angle(PI * 1.65 - PI * 1.3 * float(i) / 12.0) * s * 0.75)
			ci.draw_colored_polygon(cp, k)
		"ring", "swirl":
			ci.draw_arc(c, s * 0.9, 0.0, TAU if name == "ring" else TAU * 0.8, 24, k, maxf(2.0, s * 0.32))
			if name == "swirl":
				ci.draw_arc(c, s * 0.4, PI, TAU * 1.3, 16, k, maxf(2.0, s * 0.28))
		"comet", "flame":
			ci.draw_circle(c + Vector2(0.45, -0.45) * s, s * 0.6, k)
			ci.draw_colored_polygon(PackedVector2Array([c + Vector2(0.0, -0.9) * s, c + Vector2(1.0, 0.0) * s, c + Vector2(-1.1, 1.1) * s]), k)
		"cloud", "rainbow":
			for v: Vector2 in [Vector2(-0.6, 0.15), Vector2(0.0, -0.25), Vector2(0.6, 0.15)]:
				ci.draw_circle(c + v * s, s * 0.6, k)
		"leaf":
			ci.draw_colored_polygon(PackedVector2Array([c + Vector2(-1.0, 0.8) * s, c + Vector2(-0.6, -0.6) * s, c + Vector2(1.0, -1.0) * s, c + Vector2(0.6, 0.4) * s]), k)
		"can", "shaker":
			ci.draw_rect(Rect2(c + Vector2(-0.6, -1.1) * s, Vector2(1.2, 2.2) * s), k)
		"square", "box":
			ci.draw_rect(Rect2(c - Vector2(0.9, 0.9) * s, Vector2(1.8, 1.8) * s), k)
		"left", "right":
			var dx := -1.0 if name == "left" else 1.0
			ci.draw_colored_polygon(PackedVector2Array([c + Vector2(dx * 1.1, 0) * s, c + Vector2(-dx * 0.7, -1.0) * s, c + Vector2(-dx * 0.7, 1.0) * s]), k)
		"circle":
			ci.draw_circle(c, s * 1.0, k)
		"triangle":
			ci.draw_colored_polygon(PackedVector2Array([c + Vector2(0, -1.1) * s, c + Vector2(1.1, 0.9) * s, c + Vector2(-1.1, 0.9) * s]), k)
		"bottle":
			ci.draw_rect(Rect2(c + Vector2(-0.6, -0.3) * s, Vector2(1.2, 1.5) * s), k)
			ci.draw_colored_polygon(PackedVector2Array([c + Vector2(-0.6, -0.3) * s, c + Vector2(-0.22, -0.75) * s, c + Vector2(0.22, -0.75) * s, c + Vector2(0.6, -0.3) * s]), k)
			ci.draw_rect(Rect2(c + Vector2(-0.22, -1.25) * s, Vector2(0.44, 0.55) * s), k)
		"bolt":
			ci.draw_colored_polygon(PackedVector2Array([c + Vector2(0.3, -1.2) * s, c + Vector2(-0.8, 0.15) * s, c + Vector2(-0.05, 0.15) * s, c + Vector2(-0.35, 1.2) * s,
				c + Vector2(0.8, -0.2) * s, c + Vector2(0.05, -0.2) * s]), k)
		"knob":
			ci.draw_arc(c, s * 0.85, 0.0, TAU, 24, k, maxf(2.0, s * 0.3))
			ci.draw_rect(Rect2(c + Vector2(-0.14, -1.05) * s, Vector2(0.28, 0.8) * s), k)
		_:
			ci.draw_circle(c, s * 0.7, k)
