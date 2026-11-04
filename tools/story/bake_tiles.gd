extends SceneTree
## Bakes the 2.5D world's texture tiles from the chapter's own SVG art (assets/story/<chapter>/source/*.svg).
## Run headless:  godot --headless --path . -s tools/story/bake_tiles.gd -- night_one
## (tools/story/build_assets.py does this for you after the SVGs exist.)  The SVGs are rasterised with Godot's
## Image.load_svg_from_string, a region is cropped out, and it is resampled to 64 or 128 px. Nothing is random:
## the same SVGs give the same bytes. Where the art has no counterpart (the toilets) the tile is derived from the
## chapter palette with plain fills, or a hue-shifted crop of an existing door.
## Output: assets/story/<chapter>/textures/<id>.png  (RGB, square; `thing_*` billboards RGBA; `sky_*` 256 x 64 wraps once around the world).
## A chapter's recipes are the method `_<chapter>()` below; crops are in the art's design space (backdrop 1280 x 720; the hospital and the ward backdrops are
## wider, see their notes).

const OUT_SIZE := 64


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var chapter := "night_one" if args.is_empty() else String(args[0])
	var recipes: Dictionary = {}
	if has_method("_" + chapter):
		recipes = call("_" + chapter)
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
		if not String(id).begins_with("thing_"):  # billboard sprites keep their alpha; every other tile is opaque RGB
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
		# the lit toilet sign over the corridor: a green plate with two pictogram figures (no font needed), rasterised from an inline SVG
		"thing_sign_wc": func(s, c): return _sign_wc(),
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


# ---- more helpers: view backdrops, round billboards, sky strips ---------------------------------------------------

func _view(src: String, cache: Dictionary, name: String) -> Image:
	return _svg(src, cache, "views/%s.svg" % name, 0.5)


## a crop made round (transparent outside the circle), for a billboard such as the reactor core
func _round(im: Image, size: int = 128) -> Image:
	var out := _fit(im, size)
	out.convert(Image.FORMAT_RGBA8)
	var c := (size - 1) * 0.5
	for y in size:
		for x in size:
			var d := Vector2(x - c, y - c).length() / (size * 0.5)
			var col := out.get_pixel(x, y)
			col.a = clampf((1.0 - d) * 12.0, 0.0, 1.0)
			out.set_pixel(x, y, col)
	return out


## a crop whose near-black pixels become transparent (a prop cut out of its backdrop)
func _keyed(im: Image, size: int = 128, lo: float = 0.12) -> Image:
	var out := _fit(im, size)
	out.convert(Image.FORMAT_RGBA8)
	for y in size:
		for x in size:
			var col := out.get_pixel(x, y)
			col.a = clampf((maxf(col.r, maxf(col.g, col.b)) - lo) * 6.0, 0.0, 1.0)
			out.set_pixel(x, y, col)
	return out


## a 256 x 64 sky strip that wraps once around the world: a vertical gradient, deterministic stars and discs [[x, y, radius, Color]]
func _sky(top: Color, bottom: Color, stars: int, seed_v: int, discs: Array = [], star_col: Color = Color(1, 1, 1)) -> Image:
	var im := Image.create(256, 64, false, Image.FORMAT_RGBA8)
	for y in 64:
		var c := top.lerp(bottom, float(y) / 63.0)
		im.fill_rect(Rect2i(0, y, 256, 1), c)
	var r := seed_v
	for i in stars:
		r = (r * 1103515245 + 12345) & 0x7fffffff
		var x := r % 256
		r = (r * 1103515245 + 12345) & 0x7fffffff
		var y := (r % 56)
		im.set_pixel(x, y, star_col.lerp(Color(1, 1, 1), 0.5) if i % 3 == 0 else star_col * 0.75)
	for d in discs:
		var cx: int = d[0]
		var cy: int = d[1]
		var rad: int = d[2]
		var col: Color = d[3]
		for y in range(maxi(cy - rad, 0), mini(cy + rad + 1, 64)):
			for x in range(cx - rad, cx + rad + 1):
				var dd := Vector2(x - cx, y - cy).length()
				if dd <= rad:
					var shade := 1.0 - 0.45 * clampf((float(x - cx) + float(y - cy) * 0.5) / float(rad) * 0.5 + 0.5, 0.0, 1.0)
					im.set_pixel(posmod(x, 256), y, col * shade)
	return im


# ---- The Mothership -----------------------------------------------------------------------------------------------

func _mothership() -> Dictionary:
	return {
		# the deck (backdrop.svg): hull panelling, the planet window, the LED screen box, the door, the bottle shelf, hex floor, truss and neon trim
		"wall_hull": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(8, 34, 120, 90))),
		"wall_planet": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(816, 56, 124, 150))),
		"wall_led": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(450, 134, 380, 90))),
		"wall_speaker": func(s, c): return _fit(_svg(s, c, "speaker_l.svg", 1.0)),
		"wall_door": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(278, 134, 84, 130))),
		"wall_shelf": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(936, 136, 76, 130))),
		"floor_hex": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(200, 310, 400, 130))),
		"floor_dais": func(s, c): return _rows(_svg(s, c, "riser.svg", 1.0)),
		"ceil_hull": func(s, c): return _rows(_crop(_bd(s, c), Rect2i(120, 2, 880, 22))),
		"trim": func(s, c): return _rows(_crop(_bd(s, c), Rect2i(360, 226, 580, 30))),
		# the gallery: gold panelling, the purple lounge floor, the arch, a sofa
		"wall_gold": func(s, c): return _fit(_crop(_view(s, c, "gallery_backdrop"), Rect2i(60, 30, 200, 220))),
		"floor_lounge": func(s, c): return _fit(_crop(_view(s, c, "gallery_backdrop"), Rect2i(380, 480, 360, 230))),
		"wall_arch": func(s, c): return _fit(_crop(_view(s, c, "gallery_backdrop"), Rect2i(580, 136, 110, 114))),
		"wall_sofa": func(s, c): return _fit(_crop(_view(s, c, "gallery_backdrop"), Rect2i(60, 230, 260, 230))),
		# the reactor: coolant tubes, the grating, the hazard stripe, the core as a round billboard
		"wall_tube": func(s, c): return _fit(_crop(_view(s, c, "reactor_backdrop"), Rect2i(60, 20, 100, 360))),
		"floor_grate": func(s, c): return _fit(_crop(_view(s, c, "reactor_backdrop"), Rect2i(240, 560, 560, 130))),
		"ceil_hazard": func(s, c): return _rows(_crop(_view(s, c, "reactor_backdrop"), Rect2i(0, 0, 1280, 26))),
		"thing_core": func(s, c): return _round(_crop(_view(s, c, "reactor_backdrop"), Rect2i(540, 30, 180, 180))),
		# the bridge: console banks, the blue floor, the window on the stars
		"wall_console": func(s, c): return _fit(_crop(_view(s, c, "bridge_backdrop"), Rect2i(20, 20, 180, 170))),
		"floor_bridge": func(s, c): return _fit(_crop(_view(s, c, "bridge_backdrop"), Rect2i(120, 520, 1000, 150))),
		"wall_window": func(s, c): return _fit(_crop(_view(s, c, "bridge_backdrop"), Rect2i(330, 30, 600, 150))),
		# the medical bay has no art of its own: palette fills; the hatch is the deck door turned grey
		"med_tile": func(s, c): return _med_tile(),
		"med_floor": func(s, c): return _med_floor(),
		"wall_hatch": func(s, c): return _tint(_fit(_crop(_bd(s, c), Rect2i(278, 134, 84, 130))), Color(0.75, 0.9, 1.0)),
		"sky_space": func(s, c): return _sky(Color(0.02, 0.02, 0.09), Color(0.13, 0.07, 0.3), 110, 11, [[70, 30, 18, Color(0.95, 0.55, 0.6)], [180, 18, 5, Color(0.85, 0.9, 1.0)]]),
	}


func _med_tile() -> Image:
	var im := _filled(64, Color("#9ac8c0"))
	for j in 4:
		for i in 4:
			_rect(im, Rect2i(i * 16 + 1, j * 16 + 1, 14, 14), Color("#a8d2ca") if (i + j) % 2 == 0 else Color("#90bdb6"))
			_rect(im, Rect2i(i * 16 + 1, j * 16 + 1, 14, 1), Color("#d8f0ea"))
	for k in 4:
		_rect(im, Rect2i(0, k * 16, 64, 1), Color("#4a6e72"))
		_rect(im, Rect2i(k * 16, 0, 1, 64), Color("#4a6e72"))
	return im


func _med_floor() -> Image:
	var im := _filled(64, Color("#52707a"))
	for j in 4:
		for i in 4:
			if (i + j) % 2 == 1:
				_rect(im, Rect2i(i * 16, j * 16, 16, 16), Color("#425e68"))
	_frame(im, Rect2i(0, 0, 64, 64), Color("#33505a"))
	return im


func _sign_wc() -> Image:
	var svg := """<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">
<rect x="6" y="22" width="116" height="84" rx="10" fill="#0e6b4a" stroke="#baffd8" stroke-width="5"/>
<circle cx="40" cy="48" r="9" fill="#e8fff2"/><rect x="29" y="60" width="22" height="30" rx="5" fill="#e8fff2"/><rect x="33" y="88" width="6" height="12" fill="#e8fff2"/><rect x="42" y="88" width="6" height="12" fill="#e8fff2"/>
<circle cx="88" cy="48" r="9" fill="#e8fff2"/><path d="M88 58 L102 92 L74 92 Z" fill="#e8fff2"/><rect x="82" y="90" width="5" height="12" fill="#e8fff2"/><rect x="90" y="90" width="5" height="12" fill="#e8fff2"/>
<rect x="63" y="38" width="2" height="60" fill="#baffd8"/></svg>"""
	var im := Image.new()
	im.load_svg_from_string(svg, 1.0)
	im.convert(Image.FORMAT_RGBA8)
	return im



# ---- The Ward (mental_hospital) -------------------------------------------------------------------------------------
## Its backdrops are 1536 x 752 and drawn at design position (-128, -32): `_wc` crops in design coordinates.

func _wc(im: Image, r: Rect2i) -> Image:
	return im.get_region(Rect2i(r.position.x + 128, r.position.y + 32, r.size.x, r.size.y))


func _blank(size: int = 128) -> Image:
	return Image.create(size, size, false, Image.FORMAT_RGBA8)


func _mental_hospital() -> Dictionary:
	return {
		# the day room (backdrop.svg): mint wall, purple dado, the blackboard, a door, the checkered floor, ceiling tiles, a window
		"wall_mint": func(s, c): return _fit(_wc(_bd(s, c), Rect2i(250, 70, 60, 110))),
		"wall_dado": func(s, c): return _rows(_wc(_bd(s, c), Rect2i(330, 196, 640, 56))),
		"wall_led": func(s, c): return _fit(_wc(_bd(s, c), Rect2i(490, 70, 300, 84))),
		"wall_door": func(s, c): return _fit(_wc(_bd(s, c), Rect2i(330, 138, 72, 124))),
		"wall_speaker": func(s, c): return _fit(_svg(s, c, "speaker_l.svg", 1.0)),
		"wall_window": func(s, c): return _fit(_wc(_bd(s, c), Rect2i(1130, 20, 110, 200))),
		"floor_check": func(s, c): return _fit(_wc(_bd(s, c), Rect2i(100, 300, 360, 110))),
		"ceil_tile": func(s, c): return _rows(_wc(_bd(s, c), Rect2i(200, 0, 920, 40))),
		"floor_dais": func(s, c): return _rows(_svg(s, c, "riser.svg", 1.0)),
		# the corridor: painted doors on both sides, the wooden floor, ceiling tubes, the lit double doors at the end
		"wall_cdoor": func(s, c): return _fit(_wc(_view(s, c, "corridor_backdrop"), Rect2i(100, 60, 240, 380))),
		"wall_cdoor2": func(s, c): return _fit(_wc(_view(s, c, "corridor_backdrop"), Rect2i(880, 120, 360, 280))),
		"floor_wood": func(s, c): return _fit(_wc(_view(s, c, "corridor_backdrop"), Rect2i(240, 410, 800, 140))),
		"ceil_pale": func(s, c): return _rows(_wc(_view(s, c, "corridor_backdrop"), Rect2i(0, 0, 1280, 40))),
		"wall_end": func(s, c): return _fit(_wc(_view(s, c, "corridor_backdrop"), Rect2i(550, 120, 160, 150))),
		# the art room: the pinned paintings, the big window, the floor
		"wall_art": func(s, c): return _fit(_wc(_view(s, c, "art_backdrop"), Rect2i(1010, 90, 140, 130))),
		"wall_awindow": func(s, c): return _fit(_wc(_view(s, c, "art_backdrop"), Rect2i(410, 70, 460, 150))),
		"floor_art": func(s, c): return _fit(_wc(_view(s, c, "art_backdrop"), Rect2i(260, 260, 760, 200))),
		# the courtyard: garden-wall brick, paving, the arched door
		"wall_brick": func(s, c): return _fit(_wc(_view(s, c, "courtyard_backdrop"), Rect2i(340, 130, 580, 110))),
		"wall_archdoor": func(s, c): return _fit(_wc(_view(s, c, "courtyard_backdrop"), Rect2i(370, 100, 80, 110))),
		"floor_paving": func(s, c): return _fit(_wc(_view(s, c, "courtyard_backdrop"), Rect2i(200, 300, 920, 170))),
		# the treatment room and the quiet room have no art of their own: cold green tile, dark linoleum, padded panels
		"tx_tile": func(s, c): return _tx_tile(Color("#7fa08c"), Color("#6a8c78"), Color("#2c4438")),
		"tx_floor": func(s, c): return _tx_floor(),
		"pad_tile": func(s, c): return _pad_tile(),
		# a night sky through bars, with a moon
		"sky_moon": func(s, c): return _bars(_sky(Color(0.015, 0.04, 0.05), Color(0.07, 0.14, 0.13), 90, 23, [[190, 16, 9, Color(0.92, 0.96, 0.85)]], Color(0.8, 0.95, 0.9))),
		# billboards drawn from rectangles: a surgical lamp, a steel table, an iron bed, an easel
		"thing_lamp": func(s, c): return _th_lamp(),
		"thing_table": func(s, c): return _th_table(),
		"thing_bed": func(s, c): return _th_bed(),
		"thing_easel": func(s, c): return _th_easel(),
		"thing_chair": func(s, c): return _th_chair(Color("#6a7a70"), Color("#3c463f")),
	}


func _tx_tile(a: Color, b: Color, grout: Color) -> Image:
	var im := _filled(64, a)
	for j in 4:
		for i in 4:
			_rect(im, Rect2i(i * 16 + 1, j * 16 + 1, 14, 14), a if (i + j) % 2 == 0 else b)
			_rect(im, Rect2i(i * 16 + 1, j * 16 + 1, 14, 1), a.lightened(0.25))
	for k in 4:
		_rect(im, Rect2i(0, k * 16, 64, 1), grout)
		_rect(im, Rect2i(k * 16, 0, 1, 64), grout)
	return im


func _tx_floor() -> Image:
	var im := _filled(64, Color("#3d5246"))
	for j in 4:
		for i in 4:
			if (i + j) % 2 == 1:
				_rect(im, Rect2i(i * 16, j * 16, 16, 16), Color("#34473c"))
	_frame(im, Rect2i(0, 0, 64, 64), Color("#26362d"))
	return im


func _pad_tile() -> Image:
	var im := _filled(64, Color("#b4c0b4"))
	for j in 2:
		for i in 2:
			_rect(im, Rect2i(i * 32 + 2, j * 32 + 2, 28, 28), Color("#c4d0c2"))
			_rect(im, Rect2i(i * 32 + 15, j * 32 + 15, 2, 2), Color("#6c7a6c"))
	for k in 2:
		_rect(im, Rect2i(0, k * 32, 64, 2), Color("#7a8a7a"))
		_rect(im, Rect2i(k * 32, 0, 2, 64), Color("#7a8a7a"))
	return im


## dark bars over a sky strip (a barred window: the sky of the courtyard)
func _bars(im: Image) -> Image:
	for x in range(0, 256, 20):
		im.fill_rect(Rect2i(x, 0, 3, 64), Color(0.01, 0.02, 0.02))
	return im


func _th_lamp() -> Image:
	var im := _blank()
	im.fill_rect(Rect2i(62, 0, 5, 44), Color("#8a9690"))
	for y in range(40, 100):
		var w := int(46.0 * sqrt(maxf(1.0 - pow((y - 70.0) / 30.0, 2.0), 0.0)))
		im.fill_rect(Rect2i(64 - w, y, w * 2, 1), Color("#d8e4dc") if y < 90 else Color("#fff6c8"))
	im.fill_rect(Rect2i(40, 92, 48, 6), Color("#fff6c8"))
	return im


func _th_table() -> Image:
	var im := _blank()
	im.fill_rect(Rect2i(8, 56, 112, 12), Color("#c6d2cc"))
	im.fill_rect(Rect2i(8, 66, 112, 3), Color("#7a8a84"))
	im.fill_rect(Rect2i(18, 69, 8, 56), Color("#8a9690"))
	im.fill_rect(Rect2i(102, 69, 8, 56), Color("#8a9690"))
	im.fill_rect(Rect2i(14, 52, 100, 4), Color("#a8b8b0"))
	return im


func _th_bed() -> Image:
	var im := _blank()
	im.fill_rect(Rect2i(6, 34, 5, 70), Color("#4a5048"))
	im.fill_rect(Rect2i(117, 48, 5, 56), Color("#4a5048"))
	im.fill_rect(Rect2i(6, 70, 116, 6), Color("#4a5048"))
	im.fill_rect(Rect2i(11, 56, 106, 16), Color("#c8d4c4"))
	im.fill_rect(Rect2i(11, 50, 24, 10), Color("#e8efe4"))
	im.fill_rect(Rect2i(14, 76, 4, 28), Color("#4a5048"))
	im.fill_rect(Rect2i(108, 76, 4, 28), Color("#4a5048"))
	return im


func _th_chair(seat: Color, frame: Color) -> Image:
	var im := _blank()
	im.fill_rect(Rect2i(34, 30, 60, 50), seat)
	im.fill_rect(Rect2i(34, 30, 60, 5), frame)
	im.fill_rect(Rect2i(28, 80, 72, 12), seat)
	im.fill_rect(Rect2i(28, 90, 72, 3), frame)
	im.fill_rect(Rect2i(32, 92, 6, 34), frame)
	im.fill_rect(Rect2i(90, 92, 6, 34), frame)
	return im


func _th_bench() -> Image:
	var im := _blank()
	im.fill_rect(Rect2i(4, 56, 120, 8), Color("#7a5a38"))
	im.fill_rect(Rect2i(4, 74, 120, 10), Color("#8a6a42"))
	im.fill_rect(Rect2i(4, 82, 120, 3), Color("#4a3620"))
	im.fill_rect(Rect2i(12, 85, 8, 38), Color("#2c3038"))
	im.fill_rect(Rect2i(108, 85, 8, 38), Color("#2c3038"))
	im.fill_rect(Rect2i(12, 56, 6, 30), Color("#2c3038"))
	im.fill_rect(Rect2i(110, 56, 6, 30), Color("#2c3038"))
	return im


func _th_column() -> Image:
	var im := _blank()
	im.fill_rect(Rect2i(40, 0, 48, 128), Color("#3a2630"))
	im.fill_rect(Rect2i(46, 0, 8, 128), Color("#5a3a48"))
	im.fill_rect(Rect2i(78, 0, 10, 128), Color("#241418"))
	im.fill_rect(Rect2i(30, 0, 68, 12), Color("#5a3a48"))
	im.fill_rect(Rect2i(30, 116, 68, 12), Color("#5a3a48"))
	return im


func _th_anvil() -> Image:
	var im := _blank()
	im.fill_rect(Rect2i(14, 50, 100, 20), Color("#3c3c44"))
	im.fill_rect(Rect2i(4, 56, 18, 8), Color("#3c3c44"))
	im.fill_rect(Rect2i(14, 50, 100, 4), Color("#6a6a74"))
	im.fill_rect(Rect2i(48, 70, 32, 26), Color("#2c2c34"))
	im.fill_rect(Rect2i(32, 96, 64, 24), Color("#34343c"))
	im.fill_rect(Rect2i(40, 40, 30, 10), Color("#ff6a20"))
	return im


func _th_easel() -> Image:
	var im := _blank()
	im.fill_rect(Rect2i(36, 20, 56, 46), Color("#f0e8cc"))
	im.fill_rect(Rect2i(44, 30, 14, 14), Color("#e0604a"))
	im.fill_rect(Rect2i(62, 40, 18, 18), Color("#4a90d0"))
	im.fill_rect(Rect2i(32, 66, 64, 3), Color("#8a5a30"))
	im.fill_rect(Rect2i(46, 66, 4, 60), Color("#8a5a30"))
	im.fill_rect(Rect2i(78, 66, 4, 60), Color("#8a5a30"))
	im.fill_rect(Rect2i(62, 62, 4, 64), Color("#6a4220"))
	return im


# ---- The Underworld -----------------------------------------------------------------------------------------------

func _underworld() -> Dictionary:
	return {
		# the arena (backdrop.svg): brick wall, bone pillars, the hellmouth, the bottle shelf, the checker floor, spikes, dais
		"wall_arena": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(360, 100, 170, 120))),
		"wall_speaker": func(s, c): return _fit(_svg(s, c, "speaker_l.svg", 1.0)),
		"wall_hellmouth": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(530, 90, 220, 170))),
		"wall_bone": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(250, 40, 40, 220))),
		"wall_shelf": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(850, 120, 170, 140))),
		"floor_checker": func(s, c): return _fit(_crop(_bd(s, c), Rect2i(260, 320, 400, 120))),
		"floor_dais": func(s, c): return _rows(_svg(s, c, "riser.svg", 1.0)),
		"ceil_spikes": func(s, c): return _rows(_crop(_bd(s, c), Rect2i(120, 0, 1000, 50))),
		"trim": func(s, c): return _rows(_crop(_bd(s, c), Rect2i(300, 250, 700, 30))),
		# the court: columns, stained windows, the throne, obsidian checks, the red carpet
		"wall_court": func(s, c): return _fit(_crop(_view(s, c, "court_backdrop"), Rect2i(60, 40, 120, 300))),
		"wall_column": func(s, c): return _fit(_crop(_view(s, c, "court_backdrop"), Rect2i(170, 30, 70, 330))),
		"wall_throne": func(s, c): return _fit(_crop(_view(s, c, "court_backdrop"), Rect2i(540, 40, 200, 240))),
		"floor_obsidian": func(s, c): return _fit(_crop(_view(s, c, "court_backdrop"), Rect2i(40, 480, 320, 220))),
		"floor_carpet": func(s, c): return _fit(_crop(_view(s, c, "court_backdrop"), Rect2i(500, 540, 280, 160))),
		"ceil_court": func(s, c): return _tint(_rows(_crop(_view(s, c, "court_backdrop"), Rect2i(100, 0, 1000, 40))), Color(0.8, 0.7, 0.8)),
		# the pit: lava, the stone causeway, cave rock, the fortress
		"lava": func(s, c): return _fit(_crop(_view(s, c, "pit_backdrop"), Rect2i(100, 540, 400, 160))),
		"floor_causeway": func(s, c): return _fit(_crop(_view(s, c, "pit_backdrop"), Rect2i(200, 380, 300, 100))),
		"wall_cave": func(s, c): return _fit(_crop(_view(s, c, "pit_backdrop"), Rect2i(20, 60, 120, 240))),
		"wall_fortress": func(s, c): return _fit(_crop(_view(s, c, "pit_backdrop"), Rect2i(540, 100, 220, 160))),
		# the furnace: steel plates, its iron face, glowing channel floor, dark steel floor, pipes; the cage bars have no art
		"wall_plate": func(s, c): return _fit(_crop(_view(s, c, "furnace_backdrop"), Rect2i(30, 100, 120, 300))),
		"wall_face": func(s, c): return _fit(_crop(_view(s, c, "furnace_backdrop"), Rect2i(360, 40, 540, 220))),
		"floor_orange": func(s, c): return _fit(_crop(_view(s, c, "furnace_backdrop"), Rect2i(300, 340, 360, 300))),
		"floor_steel": func(s, c): return _fit(_crop(_view(s, c, "furnace_backdrop"), Rect2i(0, 420, 200, 280))),
		"ceil_pipes": func(s, c): return _rows(_crop(_view(s, c, "furnace_backdrop"), Rect2i(0, 0, 1280, 60))),
		"wall_bars": func(s, c): return _cage_bars(),
		"thing_column": func(s, c): return _th_column(),
		"thing_anvil": func(s, c): return _th_anvil(),
		"sky_hell": func(s, c): return _sky(Color(0.12, 0.02, 0.03), Color(0.85, 0.28, 0.06), 40, 23, [[60, 40, 14, Color(0.9, 0.3, 0.1)], [170, 46, 22, Color(0.5, 0.1, 0.05)]], Color(1.0, 0.6, 0.3)),
	}


func _cage_bars() -> Image:
	var im := _filled(64, Color("#2a1410"))
	for k in 6:
		_rect(im, Rect2i(k * 11 + 3, 0, 4, 64), Color("#6a4a40"))
		_rect(im, Rect2i(k * 11 + 3, 0, 1, 64), Color("#a07a68"))
	_rect(im, Rect2i(0, 8, 64, 3), Color("#6a4a40"))
	_rect(im, Rect2i(0, 52, 64, 3), Color("#6a4a40"))
	return im


# ---- The Hospital (a night ward: every wall and floor tile is cooled to moonlight; the backdrops are 1580 wide, design x = image x - 150) ----

func _night(im: Image, mul: Color = Color(0.55, 0.66, 1.0)) -> Image:
	return _tint(im, mul)


func _hospital() -> Dictionary:
	return {
		# the private room (backdrop.svg): wallpaper and nightstand, the window, the wooden floor, skirting
		"wall_ward": func(s, c): return _night(_fit(_crop(_bd(s, c), Rect2i(970, 170, 180, 90)))),
		"wall_window": func(s, c): return _night(_fit(_crop(_bd(s, c), Rect2i(1280, 30, 140, 220))), Color(0.45, 0.6, 1.0)),
		"floor_wood": func(s, c): return _night(_fit(_crop(_bd(s, c), Rect2i(250, 300, 500, 140)))),
		"trim": func(s, c): return _night(_rows(_crop(_bd(s, c), Rect2i(250, 440, 500, 24)))),
		"wall_curtain": func(s, c): return _curtain(),
		# the corridor: ward doors, the checked floor, ceiling tiles, the nurses' station (kept warm)
		"wall_door": func(s, c): return _night(_fit(_crop(_view(s, c, "corridor_backdrop"), Rect2i(260, 80, 190, 290))), Color(0.6, 0.7, 1.0)),
		"floor_check": func(s, c): return _night(_fit(_crop(_view(s, c, "corridor_backdrop"), Rect2i(450, 460, 600, 200)))),
		"ceil_tile": func(s, c): return _night(_rows(_crop(_view(s, c, "corridor_backdrop"), Rect2i(270, 20, 800, 40)))),
		"wall_station": func(s, c): return _tint(_fit(_crop(_view(s, c, "corridor_backdrop"), Rect2i(600, 90, 160, 190))), Color(0.95, 0.85, 0.75)),
		# the cafeteria: counter, vending machine, the red and cream floor
		"wall_counter": func(s, c): return _night(_fit(_crop(_view(s, c, "cafeteria_backdrop"), Rect2i(580, 220, 420, 80))), Color(0.8, 0.85, 1.0)),
		"wall_vending": func(s, c): return _tint(_fit(_crop(_view(s, c, "cafeteria_backdrop"), Rect2i(490, 130, 100, 140))), Color(0.85, 0.9, 1.0)),
		"floor_cafe": func(s, c): return _night(_fit(_crop(_view(s, c, "cafeteria_backdrop"), Rect2i(450, 360, 600, 160)))),
		# the garden: the brick building, a hedge, flagstones
		"wall_brick": func(s, c): return _night(_fit(_crop(_view(s, c, "garden_backdrop"), Rect2i(500, 40, 540, 120)))),
		"wall_hedge": func(s, c): return _night(_fit(_crop(_view(s, c, "garden_backdrop"), Rect2i(470, 210, 200, 50))), Color(0.5, 0.75, 0.9)),
		"floor_stone": func(s, c): return _night(_fit(_crop(_view(s, c, "garden_backdrop"), Rect2i(290, 360, 800, 120)))),
		# no art of their own: the quiet corridor's dim panels and lino, the television
		"wall_quiet": func(s, c): return _quiet_wall(),
		"floor_lino": func(s, c): return _lino(),
		"wall_tv": func(s, c): return _tv(),
		"thing_chair": func(s, c): return _th_chair(Color("#5a78a8"), Color("#2c3c5c")),
		"thing_bench": func(s, c): return _th_bench(),
		"sky_night": func(s, c): return _sky(Color(0.01, 0.02, 0.08), Color(0.07, 0.11, 0.27), 90, 5, [[200, 18, 4, Color(0.98, 0.95, 0.78)]]),
	}


func _curtain() -> Image:
	var im := _filled(64, Color("#5a78a8"))
	for i in 8:
		_rect(im, Rect2i(i * 8, 0, 3, 64), Color("#6a88b8"))
		_rect(im, Rect2i(i * 8 + 5, 0, 1, 64), Color("#3a5480"))
	_rect(im, Rect2i(0, 0, 64, 2), Color("#8fa8c8"))
	return im


func _quiet_wall() -> Image:
	var im := _filled(64, Color("#3c4e60"))
	for k in 4:
		_rect(im, Rect2i(k * 16, 0, 1, 64), Color("#2a3848"))
	_rect(im, Rect2i(0, 40, 64, 24), Color("#324454"))
	_rect(im, Rect2i(0, 40, 64, 1), Color("#52687c"))
	return im


func _lino() -> Image:
	var im := _filled(64, Color("#30445a"))
	for j in 4:
		for i in 4:
			if (i + j) % 2 == 0:
				_rect(im, Rect2i(i * 16, j * 16, 16, 16), Color("#385068"))
	_frame(im, Rect2i(0, 0, 64, 64), Color("#22344a"))
	return im


func _tv() -> Image:
	var im := _filled(64, Color("#2a3448"))
	_rect(im, Rect2i(6, 10, 52, 36), Color("#0c1020"))
	_rect(im, Rect2i(8, 12, 48, 32), Color("#3a6ab0"))
	_rect(im, Rect2i(8, 12, 48, 6), Color("#6a9ae0"))
	_rect(im, Rect2i(26, 48, 12, 6), Color("#1a2234"))
	return im
