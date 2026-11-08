extends SceneTree
## Writes the test scene's sprite sheets (PLACEHOLDER art, from CloakroomArt): tests/fixtures/cloakroom_scene/assets/story/cloak_test/sprites/
##   cloak_symbols_<theme>.png  256 x 128: the theme's four symbols across; row 0 the tag's, row 1 the same faded (the previous symbol)
##   cloak_coat.png             256 x 288: four colours across; row 0 hanging on the rail, row 1 carried by the customer, row 2 handed over (tilted)
## godot --headless --path . -s tools/minigames/make_cloakroom_fixture.gd

const OUT := "res://tests/fixtures/cloakroom_scene/assets/story/cloak_test/sprites/"
const COATS := [Color("e8503a"), Color("3fa0ff"), Color("ffd93d"), Color("3fe89a")]


func _init() -> void:
	for th: String in CloakroomArt.DEFAULTS:
		var sheet := Image.create(256, 128, false, Image.FORMAT_RGBA8)
		var ids: Array = CloakroomArt.DEFAULTS[th]
		for k in 4:
			var img := CloakroomArt.symbol_image(ids[k])
			sheet.blit_rect(img, Rect2i(0, 0, 64, 64), Vector2i(k * 64, 0))
			var faded := img.duplicate() as Image
			for y in 64:
				for x in 64:
					var c := faded.get_pixel(x, y)
					faded.set_pixel(x, y, Color(c.r, c.g, c.b, c.a * 0.5))
			sheet.blit_rect(faded, Rect2i(0, 0, 64, 64), Vector2i(k * 64, 64))
		sheet.save_png(OUT + "cloak_symbols_%s.png" % th)
	var coat := Image.create(256, 288, false, Image.FORMAT_RGBA8)
	for row in 3:
		for col in 4:
			_coat(coat, Vector2i(col * 64, row * 96), COATS[col], row)
	coat.save_png(OUT + "cloak_coat.png")
	_piece("cloak_counter", Vector2i(256, 64), Color("5a5f8a"))
	_piece("cloak_rail", Vector2i(256, 128), Color("c0c0c8"))
	_piece("cloak_tag_board", Vector2i(64, 64), Color("f6f1e4"))
	print("fixture sprites written")
	quit(0)


## A plain map piece: a filled slab with a dark one-pixel edge (the counter, the rail's uprights and bar, the tag board).
func _piece(name: String, sz: Vector2i, c: Color) -> void:
	var img := Image.create(sz.x, sz.y, false, Image.FORMAT_RGBA8)
	for y in sz.y:
		for x in sz.x:
			if name == "cloak_rail" and not (y < 6 or x < 8 or x >= sz.x - 8):
				continue
			var edge := x == 0 or y == 0 or x == sz.x - 1 or y == sz.y - 1
			img.set_pixel(x, y, Color("1a1626") if edge else (c.darkened(0.2) if y > sz.y - 6 else c))
	img.save_png(OUT + name + ".png")


func _coat(img: Image, o: Vector2i, c: Color, row: int) -> void:
	var top := 8 if row == 0 else 30
	var h := 70 if row == 0 else 46
	var ang := 0.0 if row < 2 else 0.5
	var cx := 32.0
	var cy := float(top) + float(h) * 0.5
	for y in 96:
		for x in 64:
			var dx := float(x) - cx
			var dy := float(y) - cy
			var u := dx * cos(ang) + dy * sin(ang)
			var v := -dx * sin(ang) + dy * cos(ang)
			var half := 11.0 + (v + float(h) * 0.5) / float(h) * 9.0
			var inside := v >= -float(h) * 0.5 and v <= float(h) * 0.5 and absf(u) <= half
			if inside:
				var edge := absf(u) > half - 2.0 or v < -float(h) * 0.5 + 2.0 or v > float(h) * 0.5 - 2.0
				img.set_pixel(o.x + x, o.y + y, Color("1a1626") if edge else (c.darkened(0.25) if absf(u) < 1.5 else c))
	if row == 0:  # (the hanger)
		for x in range(20, 44):
			var yy := 8 - int(absf(float(x) - 32.0) * 0.25)
			img.set_pixel(o.x + x, o.y + yy, Color("c0c0c8"))
		for y in range(0, 8):
			img.set_pixel(o.x + 32, o.y + y, Color("c0c0c8"))
