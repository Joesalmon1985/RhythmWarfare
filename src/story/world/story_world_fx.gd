class_name StoryWorldFx
extends Node3D
## The light show in the 3D world: moving-head beams, spot pools and cones, haze bands, the LED wall, the LED floor tiles, ripples and the circle ring, the disco ball's
## dots, woofer glow and confetti, all unshaded additive quads or small animated textures. Every number comes from StoryLight (pure functions of song time and the
## stage's actions); nothing here advances on frame counts, the animated textures refresh on song-time steps (so a pause freezes them and a restart replays them).

const BEAM_LEN_PAD := 0.1
const LED_W := 48  # the wall texture is 3 m wide: the 2 m wall segments show its first 32 columns, where the ending words are centred
const LED_H := 32
const LED_WORD_W := 32
const LED_HZ := 12.0
const TILE_HZ := 20.0
const GLYPHS := {  # 3 x 5 pixel letters for the ending word on the LED wall
	"A": "010101111101101", "C": "111100100100111", "D": "110101101101110", "E": "111100110100111", "G": "111100101101111", "H": "101101111101101",
	"I": "111010010010111", "K": "101101110101101", "N": "111101101101101", "O": "111101101101111", "R": "110101110101101", "T": "111010010010010",
	"U": "101101101101111", "Y": "101101010010010", "!": "010010010000010", " ": "000000000000000",
}

var stage: StoryStage
var map: StoryMap
var assets: StoryAssets
var world: StoryWorld
var _beams: Array = []  # {pivot, mats, len}
var _cones: Array = []
var _pools: Array = []
var _haze: Array = []
var _rings: Array = []  # 3 ripples + the circle ring: {node, mat}
var _dots: Array = []
var _glows: Array = []  # {node, mat}
var _tiles: MeshInstance3D
var _tile_img: Image
var _tile_tex: ImageTexture
var _tile_mat: StandardMaterial3D
var _tile_key := -1
var _tile_rand: PackedFloat32Array
var _tile_w := 0
var _tile_h := 0
var _tile_origin := Vector2.ZERO
var _led_img: Image
var _led_tex: ImageTexture
var _led_key := -1
var _confetti: MultiMeshInstance3D
var _floor_y := 0.0
var _floor_box := Rect2()
var _ceil_y := 3.4
var _fixtures: Array = []
var _ring_tex: ImageTexture
var _ball_shown := true


func build(p_stage: StoryStage, p_map: StoryMap, p_assets: StoryAssets, p_world: StoryWorld) -> void:
	stage = p_stage
	map = p_map
	assets = p_assets
	world = p_world
	name = "LightShow"
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for sec in map.sectors:
		if "dance_floor" in (sec["flags"] as Array):
			_floor_y = float(sec["floor"])
			_ceil_y = float(sec["ceiling"])
			for q in (sec["poly"] as PackedVector2Array):
				lo = Vector2(minf(lo.x, q.x), minf(lo.y, q.y))
				hi = Vector2(maxf(hi.x, q.x), maxf(hi.y, q.y))
	if lo.x < hi.x:
		_floor_box = Rect2(lo, hi - lo)
	for t in map.things:
		if str(t.get("sprite", "")) == "fixture":
			var sec: Dictionary = map.sector(str(t["sector"]))
			_fixtures.append({"at": Vector3(t["at"].x, float(sec["floor"]) + float(t.get("y", 3.0)), t["at"].y), "ground": float(sec["floor"])})
	_ring_tex = _make_ring_texture()
	_build_beams()
	_build_pools_and_cones()
	_build_haze()
	_build_tiles()
	_build_led()
	_build_rings()
	_build_dots()
	_build_glows()
	_build_confetti()


# --- construction ------------------------------------------------------------------------------------------------------------

func _add_mat(tex: Texture2D, col := Color.WHITE) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	m.albedo_texture = tex
	m.albedo_color = col
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	return m


func _tex(id: String) -> Texture2D:
	var s: Dictionary = assets.sprite(id)
	return s.get("tex", null)


func _quad(size: Vector2, mat: Material, offset := Vector3.ZERO) -> MeshInstance3D:
	var q := QuadMesh.new()
	q.size = size
	var mi := MeshInstance3D.new()
	mi.mesh = q
	mi.material_override = mat
	mi.position = offset
	mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	return mi


func _build_beams() -> void:
	var tex := _tex("beam")
	if tex == null:
		return
	for f in _fixtures:
		var pivot := Node3D.new()
		pivot.position = f["at"]
		add_child(pivot)
		var len: float = float(f["at"].y) - float(f["ground"]) + BEAM_LEN_PAD
		var mat := _add_mat(tex)
		for k in 2:  # two crossed planes read as a cone from any side
			var mi := _quad(Vector2(2.0, len), mat, Vector3(0, -len * 0.5, 0))
			mi.rotation_degrees.y = 90.0 * k
			pivot.add_child(mi)
		_beams.append({"pivot": pivot, "mat": mat, "len": len})


func _build_pools_and_cones() -> void:
	var pool := _tex("spot_pool")
	for i in 3:
		if pool != null:
			var mat := _add_mat(pool)
			var mi := _quad(Vector2(2.0, 2.0), mat)
			mi.rotation_degrees.x = -90.0
			mi.visible = false
			add_child(mi)
			_pools.append({"node": mi, "mat": mat})
	var beam := _tex("beam")
	for i in 3:
		if beam != null:
			var pivot := Node3D.new()
			var mat2 := _add_mat(beam)
			var mi2 := _quad(Vector2(1.0, 1.0), mat2, Vector3(0, -0.5, 0))
			var mi3 := _quad(Vector2(1.0, 1.0), mat2, Vector3(0, -0.5, 0))
			mi3.rotation_degrees.y = 90.0
			pivot.add_child(mi2)
			pivot.add_child(mi3)
			pivot.visible = false
			add_child(pivot)
			_cones.append({"pivot": pivot, "mat": mat2, "quads": [mi2, mi3]})


func _build_haze() -> void:
	for k in 2:
		var tex := _tex("haze_a" if k == 0 else "haze_b")
		if tex == null or _floor_box.size.x <= 0.0:
			continue
		var mat := _add_mat(tex)
		mat.albedo_color = Color(0.7, 0.75, 1.0, 0.0)
		var mi := _quad(_floor_box.size + Vector2(2, 2), mat)
		mi.rotation_degrees.x = -90.0
		mi.position = Vector3(_floor_box.get_center().x, _floor_y + 1.5 + 0.7 * k, _floor_box.get_center().y)
		mat.uv1_scale = Vector3(2.5, 2.0, 1.0)
		add_child(mi)
		_haze.append({"mat": mat, "k": k})


func _build_tiles() -> void:
	if _floor_box.size.x <= 0.0:
		return
	_tile_w = int(ceil(_floor_box.size.x))
	_tile_h = int(ceil(_floor_box.size.y))
	_tile_origin = _floor_box.position
	_tile_img = Image.create(_tile_w, _tile_h, false, Image.FORMAT_RGBA8)
	_tile_tex = ImageTexture.create_from_image(_tile_img)
	_tile_mat = _add_mat(_tile_tex)
	_tile_mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	_tile_mat.albedo_color = Color.WHITE
	_tiles = _quad(Vector2(_tile_w, _tile_h), _tile_mat)
	_tiles.rotation_degrees.x = -90.0
	_tiles.position = Vector3(_tile_origin.x + _tile_w * 0.5, _floor_y + 0.015, _tile_origin.y + _tile_h * 0.5)
	add_child(_tiles)
	_tile_rand = PackedFloat32Array()
	for j in _tile_h:
		for i in _tile_w:
			_tile_rand.append(fposmod(sin(float(i * 31 + j * 17) * 12.9898) * 43758.5453, 1.0))


func _build_led() -> void:
	_led_img = Image.create(LED_W, LED_H, false, Image.FORMAT_RGBA8)
	_led_img.fill(Color(0.015, 0.012, 0.05))
	_led_tex = ImageTexture.create_from_image(_led_img)
	world.set_texture_override("wall_led", _led_tex)


func _make_ring_texture() -> ImageTexture:
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	for y in n:
		for x in n:
			var d := Vector2(x - n * 0.5 + 0.5, y - n * 0.5 + 0.5).length() / (n * 0.5)
			var a := clampf(1.0 - absf(d - 0.9) / 0.07, 0.0, 1.0)
			img.set_pixel(x, y, Color(1, 1, 1, a))
	return ImageTexture.create_from_image(img)


func _build_rings() -> void:
	for i in 4:
		var mat := _add_mat(_ring_tex)
		var mi := _quad(Vector2(2.0, 2.0), mat)
		mi.rotation_degrees.x = -90.0
		mi.visible = false
		add_child(mi)
		_rings.append({"node": mi, "mat": mat})


func _build_dots() -> void:
	var tex := _tex("glow")
	if tex == null:
		return
	for i in 10:
		var mat := _add_mat(tex)
		var mi := _quad(Vector2(0.5, 0.5), mat)
		mi.rotation_degrees.x = -90.0
		mi.visible = false
		add_child(mi)
		_dots.append({"node": mi, "mat": mat})


func _build_glows() -> void:
	var tex := _tex("glow")
	if tex == null:
		return
	for t in map.things:
		if str(t.get("sprite", "")) == "woofer":
			var sec: Dictionary = map.sector(str(t["sector"]))
			var mat := _add_mat(tex)
			mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
			var mi := _quad(Vector2(2.4, 2.4), mat)
			mi.position = Vector3(t["at"].x, float(sec["floor"]) + float(t.get("y", 0.8)), t["at"].y + 0.05)
			add_child(mi)
			_glows.append({"node": mi, "mat": mat})


func _build_confetti() -> void:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var q := QuadMesh.new()
	q.size = Vector2(0.1, 0.14)
	mm.mesh = q
	mm.instance_count = 70
	mm.visible_instance_count = 0
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_confetti = MultiMeshInstance3D.new()
	_confetti.multimesh = mm
	_confetti.material_override = mat
	_confetti.visible = false
	add_child(_confetti)


# --- per frame ---------------------------------------------------------------------------------------------------------------

func update(t: float) -> void:
	_update_beams(t)
	_update_spots(t)
	_update_haze(t)
	_update_floor(t)
	_update_led(t)
	_update_dots(t)
	_update_glows(t)
	_update_confetti(t)
	if stage.ball_on() != _ball_shown:
		_ball_shown = stage.ball_on()
		world.set_thing_visible("disco_ball", _ball_shown)


func _update_beams(t: float) -> void:
	var a := StoryLight.beam_alpha(stage, t)
	var e := StoryLight.e01(stage)
	for i in _beams.size():
		var b: Dictionary = _beams[i]
		var pivot: Node3D = b["pivot"]
		pivot.visible = a > 0.01
		if not pivot.visible:
			continue
		pivot.rotation = Vector3(0.12 * sin(float(i) * 1.7 + t * 0.2), 0.0, StoryLight.fixture_angle(stage, i, t))
		pivot.scale = Vector3(0.9 + 0.5 * e, 1.0, 0.9 + 0.5 * e)  # both crossed planes widen together
		(b["mat"] as StandardMaterial3D).albedo_color = Color(StoryLight.pal(stage, i), a)


func _update_spots(t: float) -> void:
	var spots := StoryLight.spots(stage, t)
	var ground := _floor_y + 0.02
	for i in _pools.size():
		var node: MeshInstance3D = _pools[i]["node"]
		node.visible = i < spots.size()
		if node.visible:
			var sp: Dictionary = spots[i]
			var at: Vector2 = sp["at"]
			node.position = Vector3(at.x, _ground_at(at, ground) + 0.02, at.y + 0.2)
			node.scale = Vector3(float(sp["size"]), float(sp["size"]) * 0.7, 1.0)
			(_pools[i]["mat"] as StandardMaterial3D).albedo_color = sp["color"]
	for i in _cones.size():
		var c: Node3D = _cones[i]["pivot"]
		c.visible = i < spots.size()
		if not c.visible:
			continue
		var at2: Vector2 = spots[i]["at"]
		var tgt := Vector3(at2.x, _ground_at(at2, ground) + 0.05, at2.y)
		var top := Vector3(at2.x * 0.5, _ceil_y - 0.1, at2.y - 3.0)
		var up := (top - tgt).normalized()
		var x := up.cross(Vector3(0, 0, 1)).normalized()
		var z := x.cross(up).normalized()
		c.transform = Transform3D(Basis(x, up, z), top)
		var len := top.distance_to(tgt)
		for q in _cones[i]["quads"]:
			(q as MeshInstance3D).scale = Vector3(1.6, len, 1.0)
			(q as MeshInstance3D).position = Vector3(0, -len * 0.5, 0)
		var col := Color(1.0, 0.93, 0.75, 0.16 if stage.reduced else 0.24)
		(_cones[i]["mat"] as StandardMaterial3D).albedo_color = col


func _ground_at(p: Vector2, fallback: float) -> float:
	var sid := map.sector_at(p)
	return float(map.sector(sid).get("floor", fallback)) if sid != "" else fallback


func _update_haze(t: float) -> void:
	var a := StoryLight.haze_alpha(stage, t)
	for h in _haze:
		var m: StandardMaterial3D = h["mat"]
		m.albedo_color = Color(0.7, 0.75, 1.0, a)
		m.uv1_offset = Vector3(fposmod(t * (0.004 + 0.003 * float(h["k"])), 1.0), 0.0, 0.0)


func _update_floor(t: float) -> void:
	if _tiles == null:
		return
	var key := int(floor(t * TILE_HZ))
	var circle := stage.crowd.circle_c
	if key != _tile_key:
		_tile_key = key
		var tq := float(key) / TILE_HZ
		var glow := StoryLight.floor_glow(stage, tq)
		var gcol := StoryLight.pal(stage, 0)
		var fx := stage.crowd.floor_x
		var ctx := StoryLight.tile_context(stage, tq)
		for j in _tile_h:
			for i in _tile_w:
				var h := _tile_rand[j * _tile_w + i]
				var p := Vector2(_tile_origin.x + float(i) + 0.5, _tile_origin.y + float(j) + 0.5)
				var a := StoryLight.tile_alpha_ctx(ctx, i, j, h, p, circle, fx)
				var col := StoryLight.pal(stage, int(h * 8.0))
				if a < 0.01:
					_tile_img.set_pixel(i, j, Color(gcol, clampf(glow, 0.0, 0.5)))
				else:
					_tile_img.set_pixel(i, j, Color(col.lerp(gcol, 0.2), clampf(a + glow, 0.0, 0.9)))
		_tile_tex.update(_tile_img)
	var rt := -1.0
	for name in ["floor_ripple", "bass_reveal"]:
		if stage.is_active(name, t):
			rt = stage.progress(name, t)
	var cr := stage.crowd.circle_r
	for k in 3:
		var ring: Dictionary = _rings[k]
		var node: MeshInstance3D = ring["node"]
		node.visible = rt >= 0.0
		if node.visible:
			var q := fposmod(rt * 2.0 + float(k) / 3.0, 1.0)
			node.position = Vector3(circle.x, _floor_y + 0.03, circle.y)
			node.scale = Vector3(q * 2.0 * cr.x * 1.6 + 0.1, q * 2.0 * cr.y * 1.6 + 0.1, 1.0)
			(ring["mat"] as StandardMaterial3D).albedo_color = Color(StoryLight.pal(stage, k), (1.0 - q) * 0.7)
	var rn: MeshInstance3D = _rings[3]["node"]
	rn.visible = stage.is_active("circle", t)
	if rn.visible:
		var pulse := 0.5 + 0.5 * StoryLight.kick(stage, t)
		rn.position = Vector3(circle.x, _floor_y + 0.03, circle.y)
		rn.scale = Vector3(cr.x * 2.24, cr.y * 2.24, 1.0)
		(_rings[3]["mat"] as StandardMaterial3D).albedo_color = Color(StoryLight.pal(stage, 0), 0.35 + 0.3 * pulse)


func _update_led(t: float) -> void:
	var hz := LED_HZ * (0.5 if stage.reduced else 1.0)
	var key := int(floor(t * hz))
	if key == _led_key:
		return
	_led_key = key
	var tq := float(key) / hz
	var e := StoryLight.e01(stage)
	var b := StoryLight.beats(stage, tq) * (0.5 if stage.reduced else 1.0)
	var kp := 0.0 if stage.reduced else StoryLight.kick(stage, tq)
	var mode := stage.led_mode()
	var dim := StoryLight.led_dim(stage)
	var c0 := StoryLight.pal(stage, 0)
	var c1 := StoryLight.pal(stage, 1)
	var off := Color(0.03, 0.025, 0.09)
	var word: Array = StoryLight.led_word(stage)
	_led_img.fill(Color(0.015, 0.012, 0.05))
	if word.is_empty():
		var cols := LED_W / 4  # one LED cell is 3 x 3 pixels with a dark pixel of grid after it: work per cell, not per pixel
		var rows := LED_H / 4
		for cj in rows:
			var v := (float(cj) + 0.5) / float(rows)
			for ci in cols:
				var val := StoryLight.led_value(mode, (float(ci) + 0.5) / float(cols), v, ci, b, e, kp)
				var col2 := off if val < 0.05 else (c0.lerp(c1, v).lightened(0.08 * val) * (dim * (0.3 + 0.7 * val))).clamp()
				_led_img.fill_rect(Rect2i(ci * 4, cj * 4, 3, 3), col2)
	else:
		var col := (c0.lightened(0.55) * (dim * (0.85 + 0.15 * kp))).clamp()
		var y0 := (LED_H - word.size() * 6) / 2
		for li in word.size():
			var line: String = word[li]
			var x0 := (LED_WORD_W - line.length() * 4 + 1) / 2
			for ci in line.length():
				var g: String = GLYPHS.get(line[ci], GLYPHS[" "])
				for gy in 5:
					for gx in 3:
						if g[gy * 3 + gx] == "1":
							_led_img.set_pixel(clampi(x0 + ci * 4 + gx, 0, LED_W - 1), clampi(y0 + li * 6 + gy, 0, LED_H - 1), col)
	_led_tex.update(_led_img)


func _update_dots(t: float) -> void:
	var on := stage.ball_on() and not stage.reduced and not stage.high_contrast and _floor_box.size.x > 0.0
	var b := StoryLight.beats(stage, t)
	for i in _dots.size():
		var node: MeshInstance3D = _dots[i]["node"]
		node.visible = on
		if not on:
			continue
		var ang := float(i) * 0.9 + b * 0.05
		var c := _floor_box.get_center()
		var r := 0.15 + 0.85 * fposmod(float(i) * 0.137, 1.0)
		node.position = Vector3(c.x + cos(ang) * r * _floor_box.size.x * 0.45, _floor_y + 0.025, c.y + sin(ang * 1.3) * r * _floor_box.size.y * 0.4)
		(_dots[i]["mat"] as StandardMaterial3D).albedo_color = Color(StoryLight.pal(stage, i), 0.5)


func _update_glows(t: float) -> void:
	var k := StoryLight.woofer_glow(stage, t)
	for g in _glows:
		(g["node"] as MeshInstance3D).visible = k > 0.02
		(g["mat"] as StandardMaterial3D).albedo_color = Color(StoryLight.pal(stage, 1), 0.45 * k)


func _update_confetti(t: float) -> void:
	var list := StoryLight.confetti(stage, t, 70)
	_confetti.visible = not list.is_empty()
	var mm := _confetti.multimesh
	mm.visible_instance_count = list.size()
	for i in list.size():
		var c: Dictionary = list[i]
		var pos := Vector3(_floor_box.position.x + float(c["u"]) * _floor_box.size.x + float(c["sway"]), _floor_y + float(c["y"]),
			_floor_box.position.y + float(c["v"]) * _floor_box.size.y)
		mm.set_instance_transform(i, Transform3D(Basis(), pos))
		mm.set_instance_color(i, Color(c["color"], c["alpha"]))
