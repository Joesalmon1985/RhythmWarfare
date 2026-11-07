class_name BarDraw
extends RefCounted
## The bar's ingredient sprites, drawn procedurally (no art files): 64 x 64 pixel images, one distinct silhouette per ingredient AND its own colour, with a dark outline, a few dark
## marks and a light edge. PLACEHOLDERS: nothing under art/reference/standard/ exists for the bar yet; the owner's art replaces `texture` per ingredient id later.
## `texture(shape, color)` is cached; the shapes are listed in BarData.SHAPES.

const SIZE := 64
static var _cache: Dictionary = {}


static func texture(shape: String, color: Color) -> ImageTexture:
	var key := "%s|%s" % [shape, color.to_html(false)]
	if not _cache.has(key):
		_cache[key] = ImageTexture.create_from_image(image(shape, color))
	return _cache[key]


## The 64 px image of `shape` filled with `color`.
static func image(shape: String, color: Color) -> Image:
	var def := _def(shape)
	var add: Array = def["add"]
	var cut: Array = def.get("cut", [])
	var mark: Array = def.get("mark", [])
	var inside := PackedByteArray()
	inside.resize(SIZE * SIZE)
	for y in SIZE:
		for x in SIZE:
			var p := Vector2(x + 0.5, y + 0.5)
			var v := false
			for poly: PackedVector2Array in add:
				if Geometry2D.is_point_in_polygon(p, poly):
					v = true
					break
			if v:
				for poly: PackedVector2Array in cut:
					if Geometry2D.is_point_in_polygon(p, poly):
						v = false
						break
			inside[y * SIZE + x] = 1 if v else 0
	var img := Image.create(SIZE, SIZE, false, Image.FORMAT_RGBA8)
	var edge := Color(color.darkened(0.7), 1.0)
	var dark := Color(color.darkened(0.5), 1.0)
	var light := Color(color.lightened(0.45), 1.0)
	for y in SIZE:
		for x in SIZE:
			if inside[y * SIZE + x] == 0:
				continue
			var c := color
			if _out(inside, x - 2, y - 2) or _out(inside, x - 2, y - 1) or _out(inside, x - 1, y - 2):
				c = light
			var p := Vector2(x + 0.5, y + 0.5)
			for poly: PackedVector2Array in mark:
				if Geometry2D.is_point_in_polygon(p, poly):
					c = dark
					break
			if _out(inside, x - 1, y) or _out(inside, x + 1, y) or _out(inside, x, y - 1) or _out(inside, x, y + 1):
				c = edge
			img.set_pixel(x, y, Color(c, 1.0))
	return img


static func _out(inside: PackedByteArray, x: int, y: int) -> bool:
	return x < 0 or y < 0 or x >= SIZE or y >= SIZE or inside[y * SIZE + x] == 0


static func _c(cx: float, cy: float, r: float, n := 20) -> PackedVector2Array:
	return _e(cx, cy, r, r, n)


static func _e(cx: float, cy: float, rx: float, ry: float, n := 24) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in n:
		var a := TAU * float(i) / float(n)
		out.append(Vector2(cx + cos(a) * rx, cy + sin(a) * ry))
	return out


static func _r(x0: float, y0: float, x1: float, y1: float) -> PackedVector2Array:
	return PackedVector2Array([Vector2(x0, y0), Vector2(x1, y0), Vector2(x1, y1), Vector2(x0, y1)])


static func _p(pts: Array) -> PackedVector2Array:
	var out := PackedVector2Array()
	for q: Array in pts:
		out.append(Vector2(float(q[0]), float(q[1])))
	return out


static func _star(cx: float, cy: float, ro: float, ri: float, n := 5) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in n * 2:
		var a := -PI * 0.5 + PI * float(i) / float(n)
		var r := ro if i % 2 == 0 else ri
		out.append(Vector2(cx + cos(a) * r, cy + sin(a) * r))
	return out


static func _ring_arc(cx: float, cy: float, r_out: float, r_in: float, a0: float, a1: float, n := 18) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in n + 1:
		var a := lerpf(a0, a1, float(i) / float(n))
		out.append(Vector2(cx + cos(a) * r_out, cy + sin(a) * r_out))
	for i in n + 1:
		var a := lerpf(a1, a0, float(i) / float(n))
		out.append(Vector2(cx + cos(a) * r_in, cy + sin(a) * r_in))
	return out


static func _def(shape: String) -> Dictionary:
	match shape:
		"swirl":  # nebula syrup: a round bottle with a spiral
			var marks: Array = []
			for i in 16:
				var t := float(i) / 15.0
				var a := t * 2.6 * PI
				marks.append(_c(32.0 + cos(a) * t * 17.0, 34.0 + sin(a) * t * 17.0, 2.4, 8))
			return {"add": [_c(32, 36, 24), _r(26, 4, 38, 20)], "mark": marks}
		"comet":
			return {"add": [_c(42, 22, 15), _p([[34, 10], [56, 30], [4, 60]])], "mark": [_c(44, 20, 3, 8), _p([[24, 36], [30, 38], [14, 52]])]}
		"star":
			return {"add": [_star(32, 34, 29, 12)], "mark": [_c(32, 34, 4, 8)]}
		"crescent":
			return {"add": [_c(30, 32, 27)], "cut": [_c(44, 26, 22)], "mark": [_c(20, 40, 2.5, 8)]}
		"rainbow":
			var arcs: Array = [_ring_arc(32, 46, 21, 18, PI, TAU), _ring_arc(32, 46, 14, 12, PI, TAU)]
			return {"add": [_ring_arc(32, 46, 29, 8, PI, TAU)], "mark": arcs}
		"cloud":
			return {"add": [_c(20, 38, 14), _c(34, 28, 17), _c(48, 38, 13), _r(20, 38, 48, 54)], "mark": [_c(26, 36, 2.5, 8), _c(40, 28, 3, 8), _c(46, 42, 2, 8)]}
		"gem":
			return {"add": [_p([[32, 6], [56, 24], [32, 58], [8, 24]])], "mark": [_r(8, 24, 56, 26), _p([[32, 26], [34, 26], [34, 50], [32, 50]])]}
		"spiky":
			return {"add": [_e(32, 38, 19, 24), _p([[14, 30], [3, 22], [14, 42]]), _p([[50, 30], [61, 22], [50, 42]]), _p([[24, 16], [20, 2], [31, 13]]), _p([[40, 16], [44, 2], [33, 13]])],
				"mark": [_c(26, 34, 2, 6), _c(38, 42, 2, 6), _c(30, 50, 2, 6), _c(38, 28, 2, 6)]}
		"leaf":
			return {"add": [_p([[32, 3], [48, 15], [53, 34], [44, 51], [32, 61], [20, 51], [11, 34], [16, 15]])], "mark": [_r(31, 10, 33, 56), _p([[32, 24], [44, 18], [44, 20], [33, 27]]), _p([[32, 38], [20, 32], [20, 34], [31, 41]])]}
		"flame":
			return {"add": [_p([[32, 2], [40, 18], [53, 34], [52, 50], [42, 60], [22, 60], [12, 50], [11, 34], [22, 22], [26, 28], [30, 14]])], "mark": [_c(32, 46, 8, 10)]}
		"hex":
			return {"add": [_c(32, 32, 28, 6)], "mark": [_c(30, 36, 3, 8), _c(37, 30, 2, 6), _c(26, 26, 2, 6)]}
		"egg":
			return {"add": [_e(32, 40, 20, 22), _e(32, 26, 15, 21)], "mark": [_c(26, 32, 2, 6), _c(38, 44, 2.5, 8), _c(30, 50, 2, 6)]}
		"can":
			return {"add": [_r(16, 8, 48, 58)], "mark": [_r(16, 26, 48, 38), _r(26, 8, 38, 12)]}
		"ring":
			var dots: Array = []
			for i in 12:
				var a := TAU * float(i) / 12.0
				dots.append(_c(32.0 + cos(a) * 21.0, 32.0 + sin(a) * 21.0, 2.2, 6))
			return {"add": [_c(32, 32, 29)], "cut": [_c(32, 32, 11)], "mark": dots}
		"shaker":
			return {"add": [_p([[18, 20], [46, 20], [52, 58], [12, 58]]), _e(32, 14, 14, 10)], "mark": [_r(14, 38, 50, 46), _c(27, 13, 1.8, 6), _c(32, 10, 1.8, 6), _c(37, 13, 1.8, 6)]}
		"lemon":
			return {"add": [_e(32, 34, 26, 19), _p([[62, 34], [52, 26], [52, 42]]), _p([[2, 34], [12, 26], [12, 42]])], "mark": [_r(16, 33, 48, 35), _c(24, 26, 2, 6), _c(40, 42, 2, 6)]}
	return {"add": [_c(32, 32, 26)]}
