class_name StoryWorld
extends Node3D
## The 3D room of a chapter (docs/STORY_25D_PLAN.md section 2), built from a StoryMap: a floor and a ceiling polygon per sector, a quad per wall segment
## (portals get a lower and an upper part where the neighbouring floor is higher or ceiling lower), billboard things, an optional sky cylinder. Everything is
## unshaded, nearest-filtered and flat: the Doom look comes from the low internal resolution (StoryLowRes) and from light that is a per-sector colour,
## not a real light. A sector's light and tint are functions of song time (light_of), written each frame to that sector's materials.
## The builder needs no renderer to run (headless tests build it); pixels only appear when it sits in a viewport.

const FOG_COLOR := Color(0.03, 0.02, 0.08)
const FOG_DENSITY := 0.035
const WALL_SHADE_X := 0.82  # walls facing along x are a little darker than those facing along z: the old engines' cheap fake of a light direction
const CEIL_SHADE := 0.8

var map: StoryMap
var assets: StoryAssets
var errors: Array = []
var env: Environment
var _tex: Dictionary = {}  # texture name -> Texture2D
var _metres: Dictionary = {}  # texture name -> metres per repeat
var _sector_nodes: Dictionary = {}  # sector id -> {node: MeshInstance3D, mats: Array[StandardMaterial3D]}
var _thing_nodes: Array = []  # {node: MeshInstance3D, mat, thing: Dictionary, base_scale: Vector3, base_y: float}
var _sky: MeshInstance3D
var _sky_follow := true
var triangle_count := 0
var _mats_by_tex: Dictionary = {}  # texture name -> Array of the StandardMaterial3D showing it (animated surfaces swap their texture)


func build(p_map: StoryMap, p_assets: StoryAssets) -> void:
	map = p_map
	assets = p_assets
	var man: Dictionary = assets.manifest.get("textures", {}) if assets != null else {}
	for name in map.textures:
		_metres[name] = 2.0
		for k in man:  # the manifest knows each tile's size in metres
			if str(man[k]["file"]) == str(map.textures[name]):
				_metres[name] = float(man[k].get("metres", 2.0))
		_tex[name] = _load_tex(str(map.textures[name]))
	var by_sector: Dictionary = {}
	for s in map.sectors:
		by_sector[s["id"]] = {}
	for s in map.sectors:
		_add_flat(by_sector[s["id"]], s, true)
		_add_flat(by_sector[s["id"]], s, false)
	for w in map.resolved_walls():
		_add_wall(by_sector[w["sector"]], w)
	for s in map.sectors:
		_make_sector_mesh(s, by_sector[s["id"]])
	for t in map.things:
		_make_thing(t)
	_make_sky()
	env = _make_environment()


func _load_tex(file: String) -> Texture2D:
	var path := "res://assets/story/%s/%s" % [map.art, file]
	var t: Texture2D = null
	if ResourceLoader.exists(path):
		t = load(path) as Texture2D
	if t == null:
		errors.append("texture %s could not be loaded" % path)
		var img := Image.create(8, 8, false, Image.FORMAT_RGB8)
		img.fill(Color(1, 0, 1))
		t = ImageTexture.create_from_image(img)
	return t


func _make_environment() -> Environment:
	var e := Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = FOG_COLOR
	e.ambient_light_source = Environment.AMBIENT_SOURCE_DISABLED
	e.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	e.fog_enabled = true
	e.fog_light_color = FOG_COLOR
	e.fog_density = float(OS.get_environment("RW_STORY_FOG")) if OS.has_environment("RW_STORY_FOG") else FOG_DENSITY  # RW_STORY_FOG=0 turns the fog off
	return e


# --- geometry -------------------------------------------------------------------------------------------------------------------------

func _group(g: Dictionary, tex: String) -> Dictionary:
	if not g.has(tex):
		g[tex] = {"v": PackedVector3Array(), "uv": PackedVector2Array(), "c": PackedColorArray(), "i": PackedInt32Array()}
	return g[tex]


func _add_flat(g: Dictionary, s: Dictionary, floor_side: bool) -> void:
	var tex := str(s["floor_tex"] if floor_side else s["ceil_tex"])
	if tex == "" or tex == "sky":
		return
	var poly: PackedVector2Array = s["poly"]
	var tris := Geometry2D.triangulate_polygon(poly)
	var y := float(s["floor"] if floor_side else s["ceiling"])
	var m: float = _metres.get(tex, 2.0)
	var d := _group(g, tex)
	var base: int = d["v"].size()
	var shade := 1.0 if floor_side else CEIL_SHADE
	for p in poly:
		d["v"].append(Vector3(p.x, y, p.y))
		d["uv"].append(Vector2(p.x / m, p.y / m))
		d["c"].append(Color(shade, shade, shade))
	for k in range(0, tris.size(), 3):
		d["i"].append_array([base + tris[k], base + tris[k + 1], base + tris[k + 2]] if floor_side else [base + tris[k], base + tris[k + 2], base + tris[k + 1]])


func _add_wall(g: Dictionary, w: Dictionary) -> void:
	var s: Dictionary = map.sector(str(w["sector"]))
	var a: Vector2 = w["a"]
	var b: Vector2 = w["b"]
	var floor_y := float(s["floor"])
	var ceil_y := float(s["ceiling"])
	var parts: Array = []  # [y0, y1, tex]
	if str(w["portal"]) == "":
		parts.append([floor_y, ceil_y, str(w["tex"])])
	else:
		var o: Dictionary = map.sector(str(w["portal"]))
		if float(o["floor"]) > floor_y + 1.0e-4:
			parts.append([floor_y, float(o["floor"]), str(w["lower_tex"])])
		if float(o["ceiling"]) < ceil_y - 1.0e-4:
			parts.append([float(o["ceiling"]), ceil_y, str(w["upper_tex"])])
	var along := (b - a).length()
	var dir := (b - a) / along
	var shade := WALL_SHADE_X if absf(dir.y) > absf(dir.x) else 1.0  # a wall running along z faces along x
	for part in parts:
		var tex := str(part[2])
		if tex == "" or tex == "sky":
			continue
		var m: float = _metres.get(tex, 2.0)
		var d := _group(g, tex)
		var base: int = d["v"].size()
		var y0 := float(part[0])
		var y1 := float(part[1])
		var u0 := 0.0
		var u1 := along / m
		d["v"].append_array([Vector3(a.x, y0, a.y), Vector3(b.x, y0, b.y), Vector3(b.x, y1, b.y), Vector3(a.x, y1, a.y)])
		d["uv"].append_array([Vector2(u0, (y1 - y0) / m), Vector2(u1, (y1 - y0) / m), Vector2(u1, 0.0), Vector2(u0, 0.0)])
		for k in 4:
			d["c"].append(Color(shade, shade, shade))
		d["i"].append_array([base, base + 1, base + 2, base, base + 2, base + 3])


func _material(tex: Texture2D) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.albedo_texture = tex
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	m.vertex_color_use_as_albedo = true
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	return m


func _make_sector_mesh(s: Dictionary, groups: Dictionary) -> void:
	var mesh := ArrayMesh.new()
	var mats: Array = []
	var names := groups.keys()
	names.sort()
	for tex in names:
		var d: Dictionary = groups[tex]
		var arrays: Array = []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = d["v"]
		arrays[Mesh.ARRAY_TEX_UV] = d["uv"]
		arrays[Mesh.ARRAY_COLOR] = d["c"]
		arrays[Mesh.ARRAY_INDEX] = d["i"]
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
		triangle_count += (d["i"] as PackedInt32Array).size() / 3
		var mat := _material(_tex[tex])
		mesh.surface_set_material(mesh.get_surface_count() - 1, mat)
		mats.append(mat)
		if not _mats_by_tex.has(tex):
			_mats_by_tex[tex] = []
		_mats_by_tex[tex].append(mat)
	var mi := MeshInstance3D.new()
	mi.name = "Sector_" + str(s["id"])
	mi.mesh = mesh
	mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	add_child(mi)
	_sector_nodes[str(s["id"])] = {"node": mi, "mats": mats}


func _make_thing(t: Dictionary) -> void:
	var spr: Dictionary = assets.sprite(str(t["sprite"])) if assets != null else {}
	var tex: Texture2D = spr.get("tex", null)
	if tex == null and _tex.has(str(t["sprite"])):
		tex = _tex[str(t["sprite"])]
	if tex == null:
		errors.append("thing %s: no sprite %s" % [t["id"], t["sprite"]])
		return
	var h := float(t.get("size", 1.0))
	var w := h * float(tex.get_width()) / float(tex.get_height())
	var q := QuadMesh.new()
	q.size = Vector2(w, h)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.albedo_texture = tex
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	mat.alpha_scissor_threshold = 0.5
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	var mi := MeshInstance3D.new()
	mi.name = "Thing_" + str(t["id"])
	mi.mesh = q
	mi.material_override = mat
	var sec: Dictionary = map.sector(str(t["sector"]))
	var at: Vector2 = t["at"]
	var y := float(sec["floor"]) + float(t.get("y", h * 0.5))
	mi.position = Vector3(at.x, y, at.y)
	add_child(mi)
	_thing_nodes.append({"node": mi, "mat": mat, "thing": t, "base_y": y})


func _make_sky() -> void:
	if map.sky.is_empty() or str(map.sky.get("tex", "")) == "":
		return
	var tex := _load_tex(str(map.sky["tex"]))
	var cyl := CylinderMesh.new()
	cyl.top_radius = 80.0
	cyl.bottom_radius = 80.0
	cyl.height = 70.0
	cyl.cap_top = false
	cyl.cap_bottom = false
	cyl.radial_segments = 24
	var mat := _material(tex)
	mat.disable_fog = true
	mat.no_depth_test = false
	_sky = MeshInstance3D.new()
	_sky.name = "Sky"
	_sky.mesh = cyl
	_sky.material_override = mat
	_sky.position.y = 20.0
	add_child(_sky)


# --- light, a function of song time ------------------------------------------------------------------------------------------------------

## The colour multiplying a sector's surfaces at song time t. ctx: {bpm, palette: Array[Color], energy 0..100, flicker: bool, strobe: 0..1}.
## Base light is the sector's authored level; it breathes with the beat and with the crowd's energy; the tint comes from the sector's own colour,
## and on the dance floor from the stage palette (one colour per bar). The wall and ceiling bake in their own flat shade (vertex colour).
static func light_of(s: Dictionary, t: float, ctx: Dictionary) -> Color:
	var bpm := float(ctx.get("bpm", 174.0))
	var beats := t * bpm / 60.0
	var energy := clampf(float(ctx.get("energy", 45.0)) / 100.0, 0.0, 1.0)
	var pulse := pow(1.0 - fposmod(beats, 1.0), 3.0)  # a kick on every beat
	var base := float(s["light"])
	var flags: Array = s.get("flags", [])
	var tint: Color = s["tint"]
	var pal: Array = ctx.get("palette", [])
	if "dance_floor" in flags or "stage" in flags:
		if not pal.is_empty():
			var bar := int(floor(beats / 4.0))
			tint = (pal[bar % pal.size()] as Color).lerp(pal[(bar + 1) % pal.size()], clampf(fposmod(beats / 4.0, 1.0) * 2.0 - 1.0, 0.0, 1.0))
		base *= 0.75 + 0.5 * energy
		base += 0.12 * pulse * (0.4 + energy)
	elif "booth" in flags or "stage_steps" in flags:
		base += 0.06 * pulse * (0.4 + energy)
	var col := Color(1, 1, 1).lerp(tint, 0.55) * clampf(base * 1.5, 0.05, 1.6)
	if bool(ctx.get("flicker", false)):
		col *= 0.55 + 0.45 * absf(sin(t * 37.0))
	var strobe := float(ctx.get("strobe", 0.0))
	if strobe > 0.0:
		col = col.lerp(Color(2, 2, 2), strobe)
	col.a = 1.0
	return col


func update(t: float, ctx: Dictionary) -> void:
	var bpm := float(ctx.get("bpm", 174.0))
	var beats := t * bpm / 60.0
	var pulse := pow(1.0 - fposmod(beats, 1.0), 3.0)
	for id in _sector_nodes:
		var col := light_of(map.sector(str(id)), t, ctx)
		for m in _sector_nodes[id]["mats"]:
			(m as StandardMaterial3D).albedo_color = col
	for th in _thing_nodes:
		var t_def: Dictionary = th["thing"]
		var node: MeshInstance3D = th["node"]
		var sec: Dictionary = map.sector(str(t_def["sector"]))
		var col := light_of(sec, t, ctx)
		var sc := 1.0
		var dy := 0.0
		var alpha := 1.0
		match str(t_def.get("anim", "none")):
			"pump":
				sc = 1.0 + (0.1 * pulse if bool(ctx.get("woofer_pump", false)) else 0.02 * pulse)
			"pulse":
				sc = 1.0 + 0.08 * pulse
			"bob":
				dy = 0.05 * sin(beats * PI * 0.5)
			"sway":
				dy = 0.02 * sin(beats * PI * 0.25)
			"rotate":
				sc = 1.0 + 0.03 * sin(beats * PI * 0.5)
			"flicker":
				alpha = 0.6 + 0.4 * absf(sin(t * 29.0))
		node.scale = Vector3(sc, sc, sc)
		node.position.y = float(th["base_y"]) + dy
		(th["mat"] as StandardMaterial3D).albedo_color = Color(col.r, col.g, col.b, alpha)


## Keep the sky centred on the camera.
func follow(cam: Vector3) -> void:
	if _sky != null:
		_sky.position = Vector3(cam.x, 20.0, cam.z)


## An animated surface: every wall or floor showing the map texture `name` shows `tex` instead (the LED wall).
func set_texture_override(name: String, tex: Texture2D) -> void:
	for m in _mats_by_tex.get(name, []):
		(m as StandardMaterial3D).albedo_texture = tex


## Show or hide a billboard thing by its map id (the disco ball is only there once it is switched on).
func set_thing_visible(id: String, on: bool) -> void:
	for th in _thing_nodes:
		if str(th["thing"]["id"]) == id:
			(th["node"] as Node3D).visible = on


func sector_node(id: String) -> MeshInstance3D:
	return _sector_nodes[id]["node"] if _sector_nodes.has(id) else null


func thing_count() -> int:
	return _thing_nodes.size()
