extends SceneTree
## Bakes the 2.5D world's texture tiles from the chapter's own SVG art (assets/story/<chapter>/source/*.svg).
## Run headless:  godot --headless --path . -s tools/story/bake_tiles.gd -- night_one
## (tools/story/build_assets.py does this for you after the SVGs exist.)  The SVGs are rasterised with Godot's
## Image.load_svg_from_string, a region is cropped out, and it is resampled to 64 or 128 px. Nothing is random:
## the same SVGs give the same bytes. Where the art has no counterpart (the toilets) the tile is derived from the
## chapter palette with plain fills, or a hue-shifted crop of an existing door.
## Output: assets/story/<chapter>/textures/<id>.png  (RGB, square).

const OUT_SIZE := 64


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var chapter := "night_one" if args.is_empty() else String(args[0])
	var recipes: Dictionary = _night_one() if chapter == "night_one" else {}
	if recipes.is_empty():
		push_error("bake_tiles: no recipes for chapter " + chapter)
		quit(1)
		return
	var dir := "res://assets/story/%s/textures" % chapter
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(dir))
	for fn in DirAccess.get_files_at(dir):
		if fn.ends_with(".png"):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(dir + "/" + fn))
	var src := "res://assets/story/%s/source/" % chapter
	var cache := {}
	var ids: Array = recipes.keys()
	ids.sort()
	for id in ids:
		var im: Image = recipes[id].call(src, cache)
		im.convert(Image.FORMAT_RGB8)
		var err := im.save_png(ProjectSettings.globalize_path("%s/%s.png" % [dir, id]))
		if err != OK:
			push_error("bake_tiles: cannot write " + id)
			quit(1)
			return
		print("tile %s %dx%d" % [id, im.get_width(), im.get_height()])
	quit(0)


# ---- helpers -------------------------------------------------------------------------------------------------

func _svg(src: String, cache: Dictionary, file: String, scale: float) -> Image:
	var key := "%s@%s" % [file, scale]
	if not cache.has(key):
		var im := Image.new()
		var err := im.load_svg_from_string(FileAccess.get_file_as_string(src + file), scale)
		if err != OK or im.is_empty():
			push_error("bake_tiles: cannot rasterise " + file)
		im.convert(Image.FORMAT_RGBA8)
		cache[key] = im
	return cache[key]


## the backdrop in its 1280 x 720 design space
func _bd(src: String, cache: Dictionary) -> Image:
	return _svg(src, cache, "backdrop.svg", 0.5)


func _crop(im: Image, r: Rect2i) -> Image:
	return im.get_region(r)


## stretch the crop to a square tile
func _fit(im: Image, size: int = OUT_SIZE) -> Image:
	var out := Image.new()
	out.copy_from(im)
	out.resize(size, size, Image.INTERPOLATE_LANCZOS)
	return out


## scale the crop to the tile width and repeat it down the tile (for strips: truss, trim, plinth)
func _rows(im: Image, size: int = OUT_SIZE) -> Image:
	var h := maxi(2, int(round(float(im.get_height()) * size / im.get_width())))
	var strip := Image.new()
	strip.copy_from(im)
	strip.resize(size, h, Image.INTERPOLATE_LANCZOS)
	strip.convert(Image.FORMAT_RGBA8)
	var out := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var y := 0
	while y < size:
		out.blit_rect(strip, Rect2i(0, 0, size, h), Vector2i(0, y))
		y += h
	return out


func _tint(im: Image, mul: Color, add: Color = Color(0, 0, 0, 0)) -> Image:
	var out := Image.new()
	out.copy_from(im)
	out.convert(Image.FORMAT_RGBA8)
	for y in out.get_height():
		for x in out.get_width():
			var c := out.get_pixel(x, y)
			out.set_pixel(x, y, Color(clampf(c.r * mul.r + add.r, 0, 1), clampf(c.g * mul.g + add.g, 0, 1), clampf(c.b * mul.b + add.b, 0, 1), 1.0))
	return out


## swap channels (r,g,b) -> a permutation, used to turn the violet door teal without new art
func _hue_swap(im: Image) -> Image:
	var out := Image.new()
	out.copy_from(im)
	out.convert(Image.FORMAT_RGBA8)
	for y in out.get_height():
		for x in out.get_width():
			var c := out.get_pixel(x, y)
			out.set_pixel(x, y, Color(c.b * 0.55, minf(1.0, c.r * 0.7 + c.b * 0.5), minf(1.0, c.b * 0.9 + c.g * 0.3), 1.0))
	return out


func _quad(cells: Array) -> Image:
	var out := Image.create(128, 128, false, Image.FORMAT_RGBA8)
	for i in 4:
		var c: Image = _fit(cells[i], 64)
		c.convert(Image.FORMAT_RGBA8)
		out.blit_rect(c, Rect2i(0, 0, 64, 64), Vector2i((i % 2) * 64, (i / 2) * 64))
	for k in [0, 63, 64, 127]:  # the glowing grid lines between the LED cells
		out.fill_rect(Rect2i(0, k, 128, 1), Color("#6a7ae0"))
		out.fill_rect(Rect2i(k, 0, 1, 128), Color("#6a7ae0"))
	return out


func _filled(size: int, base: Color) -> Image:
	var im := Image.create(size, size, false, Image.FORMAT_RGBA8)
	im.fill(base)
	return im


func _rect(im: Image, r: Rect2i, c: Color) -> void:
	im.fill_rect(r, c)


func _frame(im: Image, r: Rect2i, c: Color) -> void:
	im.fill_rect(Rect2i(r.position.x, r.position.y, r.size.x, 1), c)
	im.fill_rect(Rect2i(r.position.x, r.end.y - 1, r.size.x, 1), c)
	im.fill_rect(Rect2i(r.position.x, r.position.y, 1, r.size.y), c)
	im.fill_rect(Rect2i(r.end.x - 1, r.position.y, 1, r.size.y), c)


# ---- Night One recipes: each is a Callable(src_dir, cache) -> Image --------------------------------------------

func _night_one() -> Dictionary:
	return {
		# walls: the back wall's panelling, plinth and LED screen, the woofer cabinet, the bottle shelf, the entrance doors
		"wall_brick": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(368, 62, 66, 152))),
		"wall_panel": func(s, c): return _rows(_crop(_bd(s, c), Rect2i(450, 223, 380, 34))),
		"wall_led": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(446, 98, 388, 118))),
		"wall_speaker": func(s, c): return _fit(_svg(s, c, "speaker_l.svg", 1.0)),
		"wall_bar": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(856, 112, 148, 98))),
		"bar_front": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(852, 206, 154, 54))),
		"wall_door": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(272, 116, 92, 146))),
		# trim and ceiling: the truss and the neon plinth line
		"trim": func(s, c): return _rows(_crop(_bd(s, c), Rect2i(272, 213, 740, 52))),
		"ceil_truss": func(s, c): return _rows(_crop(_bd(s, c), Rect2i(60, 16, 170, 28))),
		# floors: four cells of the LED floor, the riser top, the dark floor border
		"floor_led": func(s, c): return _quad([
			_crop(_bd(s, c), Rect2i(505, 458, 128, 42)), _crop(_bd(s, c), Rect2i(648, 458, 128, 42)),
			_crop(_bd(s, c), Rect2i(540, 412, 96, 28)), _crop(_bd(s, c), Rect2i(646, 412, 96, 28))]),
		"floor_stage": func(s, c): return _rows(_svg(s, c, "riser.svg", 1.0)),
		"floor_dark": func(s, c): return _tint(_fit(_crop(_bd(s, c), Rect2i(352, 462, 100, 40))), Color(0.7, 0.7, 0.8)),
		"floor_carpet": func(s, c): return _tint(_fit(_crop(_bd(s, c), Rect2i(212, 466, 90, 34))), Color(0.75, 0.6, 0.7)),
		# the toilets have no art of their own: palette fills, and the entrance door turned teal for the cubicles
		"toilet_tile": func(s, c): return _toilet_tile(),
		"toilet_floor": func(s, c): return _toilet_floor(),
		"cubicle_door": func(s, c): return _hue_swap(_fit(_crop(_bd(s, c), Rect2i(272, 116, 92, 146)))),
	}


func _toilet_tile() -> Image:
	var im := _filled(64, Color("#6a9aa8"))
	for j in 4:
		for i in 4:
			_rect(im, Rect2i(i * 16 + 1, j * 16 + 1, 14, 14), Color("#78a8b4") if (i + j) % 2 == 0 else Color("#6492a0"))
			_rect(im, Rect2i(i * 16 + 1, j * 16 + 1, 14, 1), Color("#a8d0d8"))
	for k in 4:
		_rect(im, Rect2i(0, k * 16, 64, 1), Color("#2d4a56"))
		_rect(im, Rect2i(k * 16, 0, 1, 64), Color("#2d4a56"))
	return im


func _toilet_floor() -> Image:
	var im := _filled(64, Color("#5a7a8c"))
	for j in 4:
		for i in 4:
			if (i + j) % 2 == 1:
				_rect(im, Rect2i(i * 16, j * 16, 16, 16), Color("#46647a"))
	_frame(im, Rect2i(0, 0, 64, 64), Color("#344e60"))
	return im
