extends SceneTree
## Writes the bar's PLACEHOLDER sprite sheets (nothing under art/reference/standard/ exists for the bar yet) into assets/story/bar_test/sprites/:
##   bar_glass_<theme>.png   6 frames of 64 x 96 side by side: empty, 1, 2, 3 layers (the theme's ingredient colours in order), overflow, tipped
##   bar_order_<theme>.png   4 frames of 128 x 128: the order bubble with ingredient 0..3's silhouette
##   godot --headless --path . -s tools/minigames/make_bar_sheets.gd
const OUT := "res://assets/story/bar_test/sprites/"
const GW := 64
const GH := 96


func _init() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	for theme in ["space", "magic", "dinos", "transport"]:
		var ings: Array = BarData.resolve({}, theme)["ingredients"]
		_glass_sheet(theme, ings).save_png(ProjectSettings.globalize_path(OUT + "bar_glass_%s.png" % theme))
		_order_sheet(theme, ings).save_png(ProjectSettings.globalize_path(OUT + "bar_order_%s.png" % theme))
		print("sheets ", theme)
	quit(0)


func _fill(img: Image, poly: PackedVector2Array, col: Color) -> void:
	var r := Rect2i(Vector2i(poly[0]), Vector2i.ZERO)
	for p in poly:
		r = r.expand(Vector2i(p))
	for y in range(maxi(r.position.y, 0), mini(r.end.y + 1, img.get_height())):
		for x in range(maxi(r.position.x, 0), mini(r.end.x + 1, img.get_width())):
			if Geometry2D.is_point_in_polygon(Vector2(x + 0.5, y + 0.5), poly):
				img.set_pixel(x, y, col)


func _glass_poly(o: Vector2, rot: float, top: float, bottom: float, hw_top := 26.0, hw_bot := 20.0) -> PackedVector2Array:
	var pts := [Vector2(-hw_top, top), Vector2(hw_top, top), Vector2(hw_bot, bottom), Vector2(-hw_bot, bottom)]
	var out := PackedVector2Array()
	for p: Vector2 in pts:
		out.append(o + p.rotated(rot))
	return out


func _glass_sheet(_theme: String, ings: Array) -> Image:
	var img := Image.create(GW * 6, GH, false, Image.FORMAT_RGBA8)
	for f in 6:
		var o := Vector2(GW * f + GW * 0.5, GH - 6.0)
		var rot := 0.0
		var layers := 0
		var spill := false
		if f >= 1 and f <= 3:
			layers = f
		elif f == 4:
			layers = 3
			spill = true
		elif f == 5:
			layers = 1
			rot = 1.75
			o = Vector2(GW * f + 44.0, GH - 22.0)
		var h := 80.0
		_fill(img, _glass_poly(o, rot, -h, 0.0, 27.0, 21.0), Color(0.12, 0.14, 0.2, 1.0))
		_fill(img, _glass_poly(o, rot, -h + 2.0, -2.0, 25.0, 19.0), Color(0.78, 0.9, 1.0, 1.0))
		for i in layers:
			var y0 := -4.0 - 22.0 * float(i)
			var y1 := y0 - 22.0
			_fill(img, _glass_poly(o, rot, y1, y0, 24.0 - 0.03 * (-y1), 24.0 - 0.03 * (-y0)), (ings[i]["color"] as Color))
		if spill:
			_fill(img, PackedVector2Array([o + Vector2(24, -h), o + Vector2(31, -h), o + Vector2(28, -4), o + Vector2(24, -4)]), Color(0.9, 0.2, 0.2))
			_fill(img, PackedVector2Array([o + Vector2(-16, -h - 2), o + Vector2(16, -h - 2), o + Vector2(20, -h + 6), o + Vector2(-20, -h + 6)]), Color(0.9, 0.2, 0.2))
	return img


func _order_sheet(_theme: String, ings: Array) -> Image:
	var img := Image.create(128 * 4, 128, false, Image.FORMAT_RGBA8)
	for f in 4:
		var x0 := 128 * f
		_fill(img, PackedVector2Array([Vector2(x0 + 4, 4), Vector2(x0 + 124, 4), Vector2(x0 + 124, 100), Vector2(x0 + 4, 100)]), Color(0.05, 0.04, 0.08))
		_fill(img, PackedVector2Array([Vector2(x0 + 7, 7), Vector2(x0 + 121, 7), Vector2(x0 + 121, 97), Vector2(x0 + 7, 97)]), Color(0.98, 0.97, 0.92))
		_fill(img, PackedVector2Array([Vector2(x0 + 20, 100), Vector2(x0 + 44, 100), Vector2(x0 + 24, 124)]), Color(0.05, 0.04, 0.08))
		_fill(img, PackedVector2Array([Vector2(x0 + 24, 98), Vector2(x0 + 40, 98), Vector2(x0 + 26, 117)]), Color(0.98, 0.97, 0.92))
		var spr := BarDraw.image(str(ings[f]["shape"]), ings[f]["color"])
		img.blend_rect(spr, Rect2i(0, 0, 64, 64), Vector2i(x0 + 32, 18))
	return img
