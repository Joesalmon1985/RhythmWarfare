class_name StoryWorld
extends Node3D
## The 3D room of a chapter (docs/STORY_25D_PLAN.md section 2), built from a StoryMap: a floor and a ceiling polygon per sector, a quad per wall segment
## (portals get a lower and an upper part where the neighbouring floor is higher or ceiling lower), billboard things, an optional sky at infinity. Everything is
## unshaded, nearest-filtered and flat: the Doom look comes from the low internal resolution (StoryLowRes) and from light that is a per-sector colour,
## not a real light. A sector's light and tint are functions of song time (light_of), written each frame to that sector's materials.
## The builder needs no renderer to run (headless tests build it); pixels only appear when it sits in a viewport.

const FOG_COLOR := Color(0.03, 0.02, 0.08)
const FOG_DENSITY := 0.035
const WALL_SHADE_X := 0.82  # walls facing along x are a little darker than those facing along z: the old engines' cheap fake of a light direction
const CEIL_SHADE := 0.8
const LIGHT_CELL := 1.2  # metres: surfaces a light reaches are cut into cells of this size so the pool of light has a shape
const LIT_AMBIENT := 0.62  # a sector with lights keeps this much of the flat light away from them (its `ambient` overrides)
const MIN_GAIN := 0.5  # no sector reads as black: the light multiplier never falls below this (the fog and the ending fades are separate)
const SHADOW_COLOR := Color(0.05, 0.045, 0.08, 0.55)  # a floor prop's contact shadow (style guide section 8): the shadow ink at 55 %
const SHADOW_SIZE := Vector2(0.9, 0.3)  # its ellipse, as a share of the billboard's width (about 1.1 x 0.35 of the drawn footprint)
const SKY_TEXELS_AROUND := 1024.0  # a sky strip is drawn so that this many texels wrap the horizon (style guide section 7): a 1024-wide strip once, a 256-wide one four times
const SKY_HORIZON := 0.76  # the strip's row at eye level, as a fraction of its height from the top (the old 80 m cylinder put it here; map `sky.horizon` overrides)
const SKY_FADE := 8.0  # texels over which the strip's top row dissolves into the zenith colour
const DECAL_GAP := 0.006  # metres a wall decal stands off its wall (no z-fighting at 90 m with a 24-bit depth buffer and the 0.15 m near plane)
const VOID_HAZE := 0.9  # how far the bottom of a void goes toward the haze colour (docs/story/HEIGHTS_AND_PATHS.md)
const VOID_DARK := 0.3  # the haze colour's brightness: the fog colour scaled to its brightest channel, times this
const RAIL_PREFIX := "~rail:"  # a texture group of railing strips (a cut-out material)
const SKY_SHADER := """
shader_type sky;
// StoryWorld's sky at infinity: the map's sky strip looked up by the view direction alone (StoryWorld.sky_params).
uniform sampler2D strip : filter_nearest, repeat_enable;
uniform vec2 size = vec2(256.0, 64.0);
uniform float texel_rad = 0.006136;
uniform float horizon_px = 48.64;
uniform float fade_px = 8.0;
uniform vec3 zenith = vec3(0.03, 0.02, 0.08);
const float BAYER[16] = float[](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);

void sky() {
	if (AT_CUBEMAP_PASS) {
		COLOR = zenith;
	} else {
		vec3 d = normalize(EYEDIR);
		float az = atan(d.x, -d.z);
		float el = asin(clamp(d.y, -1.0, 1.0));
		int x = int(mod(floor(az / texel_rad), size.x));
		float v = horizon_px - el / texel_rad;
		int y = int(clamp(floor(v), 0.0, size.y - 1.0));
		vec3 c = texelFetch(strip, ivec2(x, y), 0).rgb;
		if (v < 0.0) {
			ivec2 p = ivec2(FRAGCOORD.xy);
			float b = (BAYER[(p.y % 4) * 4 + (p.x % 4)] + 0.5) / 16.0;
			c = clamp(-v / fade_px, 0.0, 1.0) > b ? zenith : c;
		}
		COLOR = c;
	}
}
"""

var map: StoryMap
var assets: StoryAssets
var errors: Array = []
var env: Environment
var _tex: Dictionary = {}  # texture name -> Texture2D
var _metres: Dictionary = {}  # texture name -> metres per repeat
var _sector_nodes: Dictionary = {}  # sector id -> {node: MeshInstance3D, mats: Array[StandardMaterial3D]}
var _thing_nodes: Array = []  # {node: MeshInstance3D, mat, thing: Dictionary, base_scale: Vector3, base_y: float}
var _decal_nodes: Array = []  # {node: MeshInstance3D (a child of its sector's node), mat, decal: Dictionary}: wall pictures, scenery only (never billboards, people or hotspots)
var _sky: Sky  # the map's sky at infinity (the environment's background; null: the map has no sky)
var _sky_mat: ShaderMaterial
var _sky_tex: Dictionary = {}  # sky name ("" = the map's own) -> Texture2D (the map sky's `by_name`: the camera sector's `sky` picks one)
var _sky_shown: Texture2D
var _atmo := ""  # the atmosphere last set (a sector id), so a frame in the same sector does nothing
var _sky_follow := true
var triangle_count := 0
var faces: Array = []  # every vertical face drawn: {sector (whose mesh holds it), portal, kind: wall | step | lip | cliff | railing, y0, y1, tex, a, b} (the tests read it)
var shadow_count := 0  # floor props with a contact shadow
var _anim_sectors: Dictionary = {}  # sectors that show an animated surface (their colour is rewritten every frame, the animation builds on it)
var _last_col: Dictionary = {}  # sector id -> the colour last written to its materials
var _vis: Dictionary = {}  # sector id -> portal depth: only these are drawn and updated (empty: all)
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
		if str(w.get("kind", "")) == "railing" and not bool(w.get("implicit", false)):
			_add_railing(by_sector, w)
	for s in map.sectors:
		_make_sector_mesh(s, by_sector[s["id"]])
	for t in map.things:
		_make_thing(t)
	for d in map.decals:
		_make_decal(d)
	_make_shadows()
	_make_sky()
	env = _make_environment()


func _load_tex(file: String) -> Texture2D:
	var path := file if file.begins_with("res://") else "res://assets/story/%s/%s" % [map.art, file]
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
	var fc: Color = Color.html(str(map.fog["color"])) if map.fog.has("color") else FOG_COLOR
	e.background_color = fc
	e.fog_light_color = fc
	e.fog_density = float(OS.get_environment("RW_STORY_FOG")) if OS.has_environment("RW_STORY_FOG") else float(map.fog.get("density", FOG_DENSITY))  # RW_STORY_FOG=0 turns the fog off
	if _sky != null:  # the sky sectors' open ceilings show the sky at infinity, unfogged
		e.background_mode = Environment.BG_SKY
		e.sky = _sky
		e.reflected_light_source = Environment.REFLECTION_SOURCE_DISABLED
		e.fog_sky_affect = 0.0
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
	var y := float(s["floor"] if floor_side else s["ceiling"])
	var m: float = _metres.get(tex, 2.0)
	var d := _group(g, tex)
	var shade := 1.0 if floor_side else CEIL_SHADE
	var lit := _lights_of(s)
	if not lit.is_empty():  # cut the surface into cells and light each vertex
		var lo := Vector2(INF, INF)
		var hi := Vector2(-INF, -INF)
		for p in poly:
			lo = lo.min(p)
			hi = hi.max(p)
		var gx := floorf(lo.x / LIGHT_CELL) * LIGHT_CELL
		while gx < hi.x:
			var gz := floorf(lo.y / LIGHT_CELL) * LIGHT_CELL
			while gz < hi.y:
				var cell := PackedVector2Array([Vector2(gx, gz), Vector2(gx + LIGHT_CELL, gz), Vector2(gx + LIGHT_CELL, gz + LIGHT_CELL), Vector2(gx, gz + LIGHT_CELL)])
				for piece in Geometry2D.intersect_polygons(poly, cell):
					if absf(StoryMap._signed_area(piece)) < 0.001:
						continue
					var base2: int = d["v"].size()
					var ptri := Geometry2D.triangulate_polygon(piece)
					for q in piece:
						d["v"].append(Vector3(q.x, y, q.y))
						d["uv"].append(Vector2(q.x / m, q.y / m))
						d["c"].append(_hazed(_vertex_light(Vector3(q.x, y, q.y), shade, s, lit), s, y))
					for k in range(0, ptri.size(), 3):
						d["i"].append_array([base2 + ptri[k], base2 + ptri[k + 1], base2 + ptri[k + 2]] if floor_side else [base2 + ptri[k], base2 + ptri[k + 2], base2 + ptri[k + 1]])
				gz += LIGHT_CELL
			gx += LIGHT_CELL
		return
	var tris := Geometry2D.triangulate_polygon(poly)
	var base: int = d["v"].size()
	var flat := _hazed(_flat_shade(s, shade), s, y)
	for p in poly:
		d["v"].append(Vector3(p.x, y, p.y))
		d["uv"].append(Vector2(p.x / m, p.y / m))
		d["c"].append(flat)
	for k in range(0, tris.size(), 3):
		d["i"].append_array([base + tris[k], base + tris[k + 1], base + tris[k + 2]] if floor_side else [base + tris[k], base + tris[k + 2], base + tris[k + 1]])


func _add_wall(g: Dictionary, w: Dictionary) -> void:
	var s: Dictionary = map.sector(str(w["sector"]))
	var a: Vector2 = w["a"]
	var b: Vector2 = w["b"]
	var floor_y := float(s["floor"])
	var ceil_y := float(s["ceiling"])
	var parts: Array = []  # [y0, y1, tex, kind]
	if str(w["portal"]) == "":
		parts.append([floor_y, ceil_y, str(w["tex"]), "wall"])
	else:  # a portal: the step face below the opening where the floor beyond is higher (a void's cliff), the lip above it where the ceiling beyond is lower
		var o: Dictionary = map.sector(str(w["portal"]))
		if float(o["floor"]) > floor_y + 1.0e-4:
			parts.append([floor_y, float(o["floor"]), str(w["lower_tex"]), "cliff" if bool(s.get("void", false)) else "step"])
		if float(o["ceiling"]) < ceil_y - 1.0e-4:
			parts.append([float(o["ceiling"]), ceil_y, str(w["upper_tex"]), "lip"])
	var along := (b - a).length()
	var dir := (b - a) / along
	var shade := WALL_SHADE_X if absf(dir.y) > absf(dir.x) else 1.0  # a wall running along z faces along x
	for part in parts:
		var tex := str(part[2])
		if tex == "" or tex == "sky":
			continue
		faces.append({"sector": str(w["sector"]), "portal": str(w["portal"]), "kind": str(part[3]), "y0": float(part[0]), "y1": float(part[1]), "tex": tex, "a": a, "b": b})
		var m: float = _metres.get(tex, 2.0)
		var d := _group(g, tex)
		var base: int = d["v"].size()
		var y0 := float(part[0])
		var y1 := float(part[1])
		var u0 := 0.0
		var u1 := along / m
		var lit := _lights_of(s)
		if not lit.is_empty():  # a lit wall is a grid of cells so a lamp's pool climbs it
			var nu := maxi(int(ceilf(along / LIGHT_CELL)), 1)
			var nv := maxi(int(ceilf((y1 - y0) / LIGHT_CELL)), 1)
			for iv in nv + 1:
				for iu in nu + 1:
					var fu := float(iu) / float(nu)
					var fv := float(iv) / float(nv)
					var pt := a.lerp(b, fu)
					var yy := lerpf(y0, y1, fv)
					d["v"].append(Vector3(pt.x, yy, pt.y))
					d["uv"].append(Vector2(lerpf(u0, u1, fu), (y1 - yy) / m))
					d["c"].append(_hazed(_vertex_light(Vector3(pt.x, yy, pt.y), shade, s, lit), s, yy))
			for iv in nv:
				for iu in nu:
					var i00 := base + iv * (nu + 1) + iu
					var i10 := i00 + 1
					var i01 := i00 + nu + 1
					var i11 := i01 + 1
					d["i"].append_array([i00, i10, i11, i00, i11, i01])
			continue
		d["v"].append_array([Vector3(a.x, y0, a.y), Vector3(b.x, y0, b.y), Vector3(b.x, y1, b.y), Vector3(a.x, y1, a.y)])
		d["uv"].append_array([Vector2(u0, (y1 - y0) / m), Vector2(u1, (y1 - y0) / m), Vector2(u1, 0.0), Vector2(u0, 0.0)])
		var flat := _flat_shade(s, shade)
		if bool(s.get("void", false)):  # a void's faces fade into the haze with depth (bottom, bottom, top, top)
			d["c"].append_array([_hazed(flat, s, y0), _hazed(flat, s, y0), _hazed(flat, s, y1), _hazed(flat, s, y1)])
		else:
			for k in 4:
				d["c"].append(flat)
		d["i"].append_array([base, base + 1, base + 2, base, base + 2, base + 3])


## A railing (docs/story/HEIGHTS_AND_PATHS.md): a cut-out strip along a portal from the higher floor up `rail_h` metres, in the higher sector's mesh (its light, its lamps).
## The tile spans the railing's height (v 0 to 1) and repeats along it at its own aspect.
func _add_railing(by_sector: Dictionary, w: Dictionary) -> void:
	var s: Dictionary = map.sector(str(w["sector"]))
	var o: Dictionary = map.sector(str(w["portal"]))
	var hs: Dictionary = o if float(o["floor"]) > float(s["floor"]) else s
	var tex := str(w["rail_tex"])
	if not _tex.has(tex):
		return
	var a: Vector2 = w["a"]
	var b: Vector2 = w["b"]
	var y0 := maxf(float(s["floor"]), float(o["floor"]))
	var y1 := minf(y0 + float(w["rail_h"]), minf(float(s["ceiling"]), float(o["ceiling"])))
	if y1 <= y0 + 0.01:
		return
	var t2d: Texture2D = _tex[tex]
	var along := (b - a).length()
	var u1 := along / maxf((y1 - y0) * float(t2d.get_width()) / maxf(float(t2d.get_height()), 1.0), 0.01)
	var d := _group(by_sector[str(hs["id"])], RAIL_PREFIX + tex)
	var base: int = d["v"].size()
	d["v"].append_array([Vector3(a.x, y0, a.y), Vector3(b.x, y0, b.y), Vector3(b.x, y1, b.y), Vector3(a.x, y1, a.y)])
	d["uv"].append_array([Vector2(0.0, 1.0), Vector2(u1, 1.0), Vector2(u1, 0.0), Vector2(0.0, 0.0)])
	var lit := _lights_of(hs)
	for q in [Vector3(a.x, y0, a.y), Vector3(b.x, y0, b.y), Vector3(b.x, y1, b.y), Vector3(a.x, y1, a.y)]:
		d["c"].append(_flat_shade(hs, 1.0) if lit.is_empty() else _vertex_light(q, 1.0, hs, lit))
	d["i"].append_array([base, base + 1, base + 2, base, base + 2, base + 3])
	faces.append({"sector": str(hs["id"]), "portal": str(w["portal"]) if hs == s else str(w["sector"]), "kind": "railing", "y0": y0, "y1": y1, "tex": tex, "a": a, "b": b})


## How far toward the haze a point at height y of sector s is: 0 outside voids and at the walkway's level, VOID_HAZE at the void's floor.
func haze_at(s: Dictionary, y: float) -> float:
	if not bool(s.get("void", false)):
		return 0.0
	var top := float(s.get("void_top", s["floor"]))
	var span := maxf(top - float(s["floor"]), 0.1)
	return clampf((top - y) / span, 0.0, 1.0) * VOID_HAZE


## Colour c taken `f` of the way toward the haze: the map's fog colour scaled to its brightest channel, at VOID_DARK brightness (a multiplier: the light still breathes on it).
func haze_color(c: Color, f: float) -> Color:
	var fc: Color = Color.html(str(map.fog["color"])) if map.fog.has("color") else FOG_COLOR
	var mx := maxf(maxf(fc.r, fc.g), maxf(fc.b, 0.001))
	var target := Color(fc.r / mx, fc.g / mx, fc.b / mx) * VOID_DARK
	return Color(c.r * lerpf(1.0, target.r, f), c.g * lerpf(1.0, target.g, f), c.b * lerpf(1.0, target.b, f), c.a)


func _hazed(c: Color, s: Dictionary, y: float) -> Color:
	if not bool(s.get("void", false)):
		return c
	return haze_color(c, haze_at(s, y))


# --- authored light sources, baked once into vertex colours ------------------------------------------------------------------------------

var _lights_cache: Dictionary = {}


func _lights_of(s: Dictionary) -> Array:
	var id := str(s["id"])
	if not _lights_cache.has(id):
		_lights_cache[id] = map.lights_reaching(id)
	return _lights_cache[id]


## The flat vertex colour of a surface in a sector with no lights: its shade, scaled by an authored `ambient`.
func _flat_shade(s: Dictionary, shade: float) -> Color:
	var amb := float(s.get("ambient", -1.0))
	var v := shade * (amb if amb >= 0.0 else 1.0)
	return Color(v, v, v)


## The vertex colour at world point p in sector s: the flat shade times the sector's ambient (lower where lights are, so they stand out) plus each light's colour with a
## squared falloff over its radius (and a cone, for a window's shape or a doorway's spill). Static: song-time light multiplies it by the sector's albedo each frame.
func _vertex_light(p: Vector3, shade: float, s: Dictionary, lit: Array) -> Color:
	var amb := float(s.get("ambient", -1.0))
	var base := shade * (amb if amb >= 0.0 else LIT_AMBIENT)
	var col := Color(base, base, base)
	for l in lit:
		var at: Vector2 = l["at"]
		var ly := float(map.sector(str(l["sector"]))["floor"]) + float(l["y"])
		var d := Vector3(p.x - at.x, p.y - ly, p.z - at.y)
		var dist := d.length()
		var r := float(l["radius"])
		if dist >= r:
			continue
		var f := 1.0 - dist / r
		f *= f
		if l.has("cone"):
			var cone: Dictionary = l["cone"]
			var dir := map.forward_of_yaw(float(cone["yaw"]))
			var flat := Vector2(d.x, d.z)
			if flat.length() > 0.05:
				var cosang := flat.normalized().dot(dir)
				var outer := cos(deg_to_rad(float(cone["angle"])))
				f *= clampf((cosang - outer) / maxf(1.0 - outer, 0.01) * 2.0, 0.0, 1.0)
		var lc: Color = l["color"]
		var k := f * float(l["strength"])
		col.r += lc.r * k
		col.g += lc.g * k
		col.b += lc.b * k
	return Color(minf(col.r, 1.0), minf(col.g, 1.0), minf(col.b, 1.0))


## The static light a figure standing at ground point `pos` in sector `sid` gets from the lamps around it (the same falloff the surfaces are baked with, at chest
## height), relative to the flat light of a sector without lamps (1.0). The song-time light of the sector multiplies it.
func figure_light(pos: Vector2, sid: String) -> Color:
	var s := map.sector(sid)
	if s.is_empty():
		return Color.WHITE
	var lit := _lights_of(s)
	if lit.is_empty():
		var v := _flat_shade(s, 1.0).r
		return Color(v, v, v)
	var c := _vertex_light(Vector3(pos.x, float(s.get("floor", 0.0)) + 1.2, pos.y), 1.0, s, lit)
	return Color(minf(c.r * 1.25, 1.4), minf(c.g * 1.25, 1.4), minf(c.b * 1.25, 1.4))


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
		var real := str(tex).trim_prefix(RAIL_PREFIX)
		var mat := _material(_tex[real])
		if str(tex).begins_with(RAIL_PREFIX):  # a railing: a cut-out (alpha scissor, nearest, no blending, no sorting)
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
			mat.alpha_scissor_threshold = 0.5
		mesh.surface_set_material(mesh.get_surface_count() - 1, mat)
		mats.append(mat)
		for an in map.animated:
			if str(an.get("tex", "")) == real:
				_anim_sectors[str(s["id"])] = true
		if not _mats_by_tex.has(real):
			_mats_by_tex[real] = []
		_mats_by_tex[real].append(mat)
	var mi := MeshInstance3D.new()
	mi.name = "Sector_" + str(s["id"])
	mi.mesh = mesh
	mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	add_child(mi)
	_sector_nodes[str(s["id"])] = {"node": mi, "mats": mats}


## The choice layer's poses of map things (docs/CHOICE_CLARITY.md): thing id -> {tex?: Texture2D, dx, dy, sx, sy}; an id not here is drawn as the map says.
var thing_pose: Dictionary = {}


func _make_thing(t: Dictionary) -> void:
	var spr: Dictionary = assets.sprite(str(t["sprite"])) if assets != null else {}
	var tex: Texture2D = spr.get("tex", null)
	var blend := str(t.get("blend", ""))
	if t.has("piece") and assets != null:  # a set piece of the chapter's art, shown while the show has switched it on (StoryStage.piece_state)
		var pd := assets.piece(str(t["piece"]))
		if not pd.is_empty():
			tex = assets.texture(str(pd["file"]))
			if blend == "":
				blend = str(pd.get("blend", "mix"))
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
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST  # a cut-out keeps its pixels (style guide section 7: nothing bilinear in the picture)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	mat.alpha_scissor_threshold = 0.5
	if blend == "add" or blend == "mix":  # soft art (glows, banners, sunbeams): alpha blended, never written to the depth buffer
		mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR  # (soft art stays soft: the only soft-edged things allowed)
		mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
		if blend == "add":
			mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
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
	if t.has("piece"):
		mi.visible = false
	var lamp := Color.WHITE  # the lamps around it, as the walls beside it get them (style guide section 5: one light model); soft art and `emissive` things give light, not take it
	if blend == "" and not bool(t.get("emissive", false)):
		lamp = _thing_light(at, y, sec)
	_thing_nodes.append({"node": mi, "mat": mat, "thing": t, "base_y": y, "add": blend == "add", "tex0": tex, "h": h, "w": w, "base_x": at.x, "lamp": lamp, "floor": float(sec["floor"]),
		"grounded": blend == "" and not t.has("piece") and not t.has("y") and str(t.get("anim", "none")) not in ["bob", "sway"]})


## A wall decal (docs/art/WALL_DECALS.md): a quad flat against its wall, facing the map's resolved normal (StoryMap._place_decals), DECAL_GAP off the wall. It is a child of its
## sector's node (hidden with it) and its material sits in the sector's list, so it takes the sector's song-time light exactly as the wall does; its vertex colours are the
## wall's own baked light at those points (the wall's shade and lamps, interpolated on the wall's light cells), white when `emissive`. Opaque pass, nearest, alpha scissor.
func _make_decal(d: Dictionary) -> void:
	var spr: Dictionary = assets.sprite(str(d["sprite"])) if assets != null else {}
	var tex: Texture2D = spr.get("tex", null)
	if tex == null and _tex.has(str(d["sprite"])):
		tex = _tex[str(d["sprite"])]
	if tex == null:
		errors.append("decal %s: no sprite %s" % [d["id"], d["sprite"]])
		return
	var sid := str(d["sector"])
	if not d.has("normal") or not _sector_nodes.has(sid):
		return
	var s: Dictionary = map.sector(sid)
	var h := float(d["size"])
	var w := h * float(tex.get_width()) / float(tex.get_height())
	var n: Vector2 = d["normal"]
	var right := Vector2(n.y, -n.x)  # the viewer's right, facing the wall
	var base: Vector2 = d["base"]
	var y0 := float(s["floor"]) + float(d["y"])
	var wall: Dictionary = d["wall"]
	var us: Array = [0.0, w]  # the quad is cut where the wall's light cells are, so the lamps' pools on it follow the wall's
	var vs: Array = [0.0, h]
	if not wall.is_empty() and not _lights_of(s).is_empty() and not bool(d.get("emissive", false)):
		var a: Vector2 = wall["a"]
		var along := ((wall["b"] as Vector2) - a).length()
		var dirw := ((wall["b"] as Vector2) - a) / along
		var nu := maxi(int(ceilf(along / LIGHT_CELL)), 1)
		var t0 := (base - right * w * 0.5 - a).dot(dirw)
		var t1 := (base + right * w * 0.5 - a).dot(dirw)
		for k in nu + 1:
			var tk := along * float(k) / float(nu)
			if tk > minf(t0, t1) + 1.0e-3 and tk < maxf(t0, t1) - 1.0e-3:
				us.append((tk - t0) / (t1 - t0) * w)
		var fy := float(s["floor"])
		var nv := maxi(int(ceilf((float(s["ceiling"]) - fy) / LIGHT_CELL)), 1)
		for k in nv + 1:
			var yk := lerpf(fy, float(s["ceiling"]), float(k) / float(nv)) - y0
			if yk > 1.0e-3 and yk < h - 1.0e-3:
				vs.append(yk)
	us.sort()
	vs.sort()
	var v := PackedVector3Array()
	var uv := PackedVector2Array()
	var cols := PackedColorArray()
	var idx := PackedInt32Array()
	for yv in vs:
		for xu in us:
			v.append(Vector3(float(xu) - w * 0.5, float(yv), 0.0))
			uv.append(Vector2(float(xu) / w, 1.0 - float(yv) / h))
			var g := base + right * (float(xu) - w * 0.5)
			cols.append(_decal_light(d, s, Vector3(g.x, y0 + float(yv), g.y)))
	var nu2 := us.size()
	for iv in vs.size() - 1:
		for iu in nu2 - 1:
			var i00 := iv * nu2 + iu
			idx.append_array([i00, i00 + 1, i00 + nu2 + 1, i00, i00 + nu2 + 1, i00 + nu2])
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = v
	arrays[Mesh.ARRAY_TEX_UV] = uv
	arrays[Mesh.ARRAY_COLOR] = cols
	arrays[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var mat := _material(tex)
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR  # hard alpha: drawn in the walls' opaque pass, no blending over the wall
	mat.alpha_scissor_threshold = 0.5
	mesh.surface_set_material(0, mat)
	var mi := MeshInstance3D.new()
	mi.name = "Decal_" + str(d["id"])
	mi.mesh = mesh
	mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var off := base + n * DECAL_GAP
	mi.transform = Transform3D(Basis(Vector3(right.x, 0.0, right.y), Vector3.UP, Vector3(n.x, 0.0, n.y)), Vector3(off.x, y0, off.y))
	(_sector_nodes[sid]["node"] as Node3D).add_child(mi)
	(_sector_nodes[sid]["mats"] as Array).append(mat)
	_decal_nodes.append({"node": mi, "mat": mat, "decal": d, "w": w, "h": h})


## The baked light of the wall behind a decal at world point p: the wall's flat shade, or its lamp light interpolated on its light cells as _add_wall bakes and draws it
## (a decal placed by `yaw` alone takes the lamp light at the point). White when emissive (the sector's song-time light still multiplies it, as for an emissive billboard).
func _decal_light(d: Dictionary, s: Dictionary, p: Vector3) -> Color:
	if bool(d.get("emissive", false)):
		return Color.WHITE
	var n: Vector2 = d["normal"]
	var shade := WALL_SHADE_X if absf(n.x) > absf(n.y) else 1.0  # (a wall running along z faces along x)
	var lit := _lights_of(s)
	if lit.is_empty():
		return _flat_shade(s, shade)
	var wall: Dictionary = d["wall"]
	if wall.is_empty():
		return _vertex_light(p, shade, s, lit)
	var a: Vector2 = wall["a"]
	var b: Vector2 = wall["b"]
	var along := (b - a).length()
	var y0 := float(s["floor"])
	var y1 := float(s["ceiling"])
	var nu := maxi(int(ceilf(along / LIGHT_CELL)), 1)
	var nv := maxi(int(ceilf((y1 - y0) / LIGHT_CELL)), 1)
	var fu := clampf((Vector2(p.x, p.z) - a).dot((b - a) / along) / along, 0.0, 1.0) * float(nu)
	var fv := clampf((p.y - y0) / (y1 - y0), 0.0, 1.0) * float(nv)
	var iu := mini(int(fu), nu - 1)
	var iv := mini(int(fv), nv - 1)
	var fx := fu - float(iu)
	var fz := fv - float(iv)
	var c00 := _wall_cell_light(a, b, y0, y1, nu, nv, iu, iv, shade, s, lit)
	var c11 := _wall_cell_light(a, b, y0, y1, nu, nv, iu + 1, iv + 1, shade, s, lit)
	if fx >= fz:  # the wall cell's two triangles: (00, 10, 11) and (00, 11, 01)
		var c10 := _wall_cell_light(a, b, y0, y1, nu, nv, iu + 1, iv, shade, s, lit)
		return c00 + (c10 - c00) * fx + (c11 - c10) * fz
	var c01 := _wall_cell_light(a, b, y0, y1, nu, nv, iu, iv + 1, shade, s, lit)
	return c00 + (c01 - c00) * fz + (c11 - c01) * fx


## The baked light at the wall's light-cell corner (ku, kv) (the vertices _add_wall makes).
func _wall_cell_light(a: Vector2, b: Vector2, y0: float, y1: float, nu: int, nv: int, ku: int, kv: int, shade: float, s: Dictionary, lit: Array) -> Color:
	var pt := a.lerp(b, float(ku) / float(nu))
	return _vertex_light(Vector3(pt.x, lerpf(y0, y1, float(kv) / float(nv)), pt.y), shade, s, lit)


## The static light at a billboard's centre (at most chest height): the flat shade of a sector without lamps, else the ambient plus the lamps' pools, the same falloff the
## surfaces around it are baked with. The song-time light of the sector multiplies it.
func _thing_light(at: Vector2, y: float, s: Dictionary) -> Color:
	var lit := _lights_of(s)
	if lit.is_empty():
		var v := _flat_shade(s, 1.0).r
		return Color(v, v, v)
	return _vertex_light(Vector3(at.x, minf(y, float(s["floor"]) + 1.2), at.y), 1.0, s, lit)


## Contact shadows (style guide section 8): a flat ellipse on the floor under every billboard that stands on it (no `y`, not soft art, not a set piece, not floating),
## all in one mesh, drawn over the floor and under everything standing on it.
func _make_shadows() -> void:
	var v := PackedVector3Array()
	var cols := PackedColorArray()
	var idx := PackedInt32Array()
	const SEG := 14
	for th in _thing_nodes:
		if not bool(th["grounded"]):
			continue
		var t: Dictionary = th["thing"]
		var at: Vector2 = t["at"]
		var rx := float(th["w"]) * SHADOW_SIZE.x * 0.5
		var rz := float(th["w"]) * SHADOW_SIZE.y * 0.5
		var y := float(th["floor"]) + 0.015
		var base := v.size()
		v.append(Vector3(at.x, y, at.y))
		cols.append(SHADOW_COLOR)
		for k in SEG:
			var a := TAU * float(k) / float(SEG)
			v.append(Vector3(at.x + cos(a) * rx, y, at.y + sin(a) * rz))
			cols.append(SHADOW_COLOR)
		for k in SEG:
			idx.append_array([base, base + 1 + k, base + 1 + (k + 1) % SEG])
	if idx.is_empty():
		return
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = v
	arrays[Mesh.ARRAY_COLOR] = cols
	arrays[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.vertex_color_use_as_albedo = true
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.render_priority = -1
	mesh.surface_set_material(0, mat)
	var mi := MeshInstance3D.new()
	mi.name = "Shadows"
	mi.mesh = mesh
	add_child(mi)
	shadow_count = idx.size() / (3 * SEG)


func _make_sky() -> void:
	if map.sky.is_empty() or str(map.sky.get("tex", "")) == "":
		return
	_sky_tex[""] = _load_tex(str(map.sky["tex"]))
	var by_name: Variant = map.sky.get("by_name", {})
	if typeof(by_name) == TYPE_DICTIONARY:
		for nm in by_name:
			_sky_tex[str(nm)] = _load_tex(str(by_name[nm]))
	var sh := Shader.new()
	sh.code = SKY_SHADER
	_sky_mat = ShaderMaterial.new()
	_sky_mat.shader = sh
	_sky = Sky.new()
	_sky.sky_material = _sky_mat
	_sky.radiance_size = Sky.RADIANCE_SIZE_32  # nothing is lit by the sky (ambient and reflections are off): the smallest cubemap, and the shader skips its work there
	_sky.process_mode = Sky.PROCESS_MODE_QUALITY
	_show_sky("")


## The sky at infinity (style guide sections 4 and 7, audit F7): a sky sector draws no ceiling, and the background there is the map's sky strip wrapped around the
## horizon, looked up by the direction of the view only, so it never converges like a roof, never ends at a wall top and never moves when the eye walks. The strip
## (W x H texels) wraps the horizon `repeats` times (map `sky.repeats`; default SKY_TEXELS_AROUND / W, so a 1024-wide strip wraps once and a 256-wide one four times):
## one texel is 360 / (W x repeats) degrees both ways, about 2.4 internal pixels at 360 lines for the target 1024 texels around. Row `horizon` x H (map `sky.horizon`, a fraction
## from the top, default SKY_HORIZON) sits at eye level; above the strip the top row fades over SKY_FADE texels (ordered dither) into the strip's zenith colour; below it the
## bottom row continues. A pure function of the view direction: the same frame at the same song time.
func sky_params(tex: Texture2D) -> Dictionary:
	var w := maxi(tex.get_width(), 1) if tex != null else 256
	var h := maxi(tex.get_height(), 1) if tex != null else 64
	var reps := maxi(int(map.sky.get("repeats", 0)), 0)
	if reps == 0:
		reps = maxi(int(round(SKY_TEXELS_AROUND / float(w))), 1)
	var hz := clampf(float(map.sky.get("horizon", SKY_HORIZON)), 0.0, 1.0)
	return {"w": w, "h": h, "repeats": reps, "texel_deg": 360.0 / float(w * reps), "horizon_px": hz * float(h)}


func _show_sky(nm: String) -> void:
	if _sky_mat == null:
		return
	var tex: Texture2D = _sky_tex.get(nm, _sky_tex.get("", null))
	if tex == _sky_shown and _sky_shown != null:
		return
	_sky_shown = tex
	var sp := sky_params(tex)
	_sky_mat.set_shader_parameter("strip", tex)
	_sky_mat.set_shader_parameter("size", Vector2(float(sp["w"]), float(sp["h"])))
	_sky_mat.set_shader_parameter("texel_rad", deg_to_rad(float(sp["texel_deg"])))
	_sky_mat.set_shader_parameter("horizon_px", float(sp["horizon_px"]))
	_sky_mat.set_shader_parameter("fade_px", SKY_FADE)
	var z := _zenith_of(tex)
	_sky_mat.set_shader_parameter("zenith", Vector3(z.r, z.g, z.b))


## The mean colour of the strip's top two rows: what the sky is above the strip.
static func _zenith_of(tex: Texture2D) -> Color:
	var im: Image = tex.get_image() if tex != null else null
	if im == null:
		return FOG_COLOR
	if im.is_compressed():
		im.decompress()
	var acc := Color(0, 0, 0)
	var n := 0
	for y in mini(2, im.get_height()):
		for x in im.get_width():
			var c := im.get_pixel(x, y)
			acc.r += c.r
			acc.g += c.g
			acc.b += c.b
			n += 1
	return Color(acc.r / n, acc.g / n, acc.b / n) if n > 0 else FOG_COLOR


## The sky and the haze of the sector the camera is in (a map may hold a night room and a dawn one): the sector's `sky` names one of the map sky's `by_name`, its `fog` replaces the map's.
func set_atmosphere(sec: Dictionary) -> void:
	var sid := str(sec.get("id", ""))
	if sid == _atmo or sid == "":
		return
	_atmo = sid
	_show_sky(str(sec.get("sky", "")))
	if env != null:
		var fg: Dictionary = sec.get("fog", {})
		var fc: Color = Color.html(str(fg["color"])) if fg.has("color") else (Color.html(str(map.fog["color"])) if map.fog.has("color") else FOG_COLOR)
		env.background_color = fc
		env.fog_light_color = fc
		if not OS.has_environment("RW_STORY_FOG"):
			env.fog_density = float(fg.get("density", map.fog.get("density", FOG_DENSITY)))


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
			var pcol: Color = (pal[bar % pal.size()] as Color).lerp(pal[(bar + 1) % pal.size()], clampf(fposmod(beats / 4.0, 1.0) * 2.0 - 1.0, 0.0, 1.0))
			tint = tint.lerp(pcol, clampf(float(ctx.get("palette_weight", 1.0)), 0.0, 1.0))  # the sector's own tint wins outside the club
		base *= 0.75 + 0.5 * energy
		base += 0.12 * pulse * (0.4 + energy)
	elif "booth" in flags or "stage_steps" in flags:
		base += 0.06 * pulse * (0.4 + energy)
	var col := Color(1, 1, 1).lerp(tint, 0.55) * clampf(base * 1.5, MIN_GAIN, 1.6)
	if bool(ctx.get("flicker", false)):
		col *= 0.55 + 0.45 * absf(sin(t * 37.0))
	var strobe := float(ctx.get("strobe", 0.0))
	if strobe > 0.0:
		col = col.lerp(Color(2, 2, 2), strobe)
	var swell := float(ctx.get("swell_gain", 1.0))  # a new room's lamps rising (StoryStage "room_swell")
	if swell != 1.0:  # (below 1 on the downbeat, a flare above 1 a beat later)
		col *= swell
	col.a = 1.0
	return col


## The sectors that can be seen (StoryMap.visible_sectors, deeper than the crowd's): the others are hidden and not lit this frame (their materials keep the last colour,
## which is what they show the moment they come back into view and are refreshed before the next draw).
func set_visible_sectors(vis: Dictionary) -> void:
	_vis = vis
	for id in _sector_nodes:  # (only the nodes whose state changes are touched: a map of hundreds of pieces walks this every frame the camera moves)
		var on := vis.is_empty() or vis.has(id)
		var mi: MeshInstance3D = _sector_nodes[id]["node"]
		if mi.visible != on:
			mi.visible = on


func update(t: float, ctx: Dictionary) -> void:
	var bpm := float(ctx.get("bpm", 174.0))
	var beats := t * bpm / 60.0
	var pulse := pow(1.0 - fposmod(beats, 1.0), 3.0)
	var sector_cols := {}  # each sector's light once a frame: the things standing in it reuse it
	for id in _sector_nodes:
		if not _vis.is_empty() and not _vis.has(id):
			continue
		var col := light_of(map.sector(str(id)), t, ctx)
		sector_cols[id] = col
		var last: Color = _last_col.get(id, Color(-1, -1, -1))
		if absf(col.r - last.r) + absf(col.g - last.g) + absf(col.b - last.b) < 0.004 and not _anim_sectors.has(id):
			continue  # a sector whose light has not changed leaves its materials alone (most of them, most of the time)
		_last_col[id] = col
		for m in _sector_nodes[id]["mats"]:
			(m as StandardMaterial3D).albedo_color = col
	for an in map.animated:  # lava, reactor glass, window daylight, courtyard bulbs: a scroll, a pulse, a flicker or a texture swap on every surface showing the tile
		var st := StoryLight.surface_anim(an, t, bpm)
		var mats: Array = _mats_by_tex.get(str(an["tex"]), [])
		var frames: Array = an.get("frames", [])
		for m in mats:
			var sm: StandardMaterial3D = m
			sm.uv1_offset = Vector3(st["offset"].x, st["offset"].y, 0.0)
			sm.albedo_color = (sm.albedo_color.lerp(Color(1, 1, 1, 1), float(st["bright"])) * float(st["gain"])).clamp()
			if not frames.is_empty() and _tex.has(str(frames[int(st["frame"])])):
				sm.albedo_texture = _tex[str(frames[int(st["frame"])])]
	var pieces: Dictionary = ctx.get("pieces", {})
	for th in _thing_nodes:
		var t_def: Dictionary = th["thing"]
		var node: MeshInstance3D = th["node"]
		if not _vis.is_empty() and not _vis.has(str(t_def["sector"])):
			if node.visible:
				node.visible = false
				th["culled"] = true
			continue
		if th.get("culled", false):
			th["culled"] = false
			if not t_def.has("piece"):
				node.visible = true  # only hidden for being out of sight: back (pieces decide below; the show's own switches, like the disco ball, are applied after this)
		var col: Color = sector_cols.get(str(t_def["sector"]), Color.WHITE) * (th["lamp"] as Color)
		var sc := 1.0
		var dy := 0.0
		var alpha := 1.0
		if t_def.has("piece"):
			var ps: Dictionary = pieces.get(str(t_def["piece"]), {})
			node.visible = bool(ps.get("visible", false))
			alpha = float(ps.get("alpha", 0.0))
			sc = 1.0 + 0.06 * float(ps.get("pulse", 0.0))
			if th["add"]:
				col = Color(1, 1, 1, 1)
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
				alpha *= 0.6 + 0.4 * absf(sin(t * 29.0))
		var sx := 1.0
		var sy := 1.0
		var dx := 0.0
		var tp: Dictionary = thing_pose.get(str(t_def["id"]), {})  # the choice layer's pose of an option's billboard (ChoiceStaging: a texture and a motion per state)
		if not tp.is_empty():
			sx = float(tp.get("sx", 1.0))
			sy = float(tp.get("sy", 1.0))
			dx = float(tp.get("dx", 0.0))
			dy += float(tp.get("dy", 0.0)) - float(th["h"]) * sc * (1.0 - sy) * 0.5  # (the feet stay on the floor)
		var want_tex: Texture2D = tp.get("tex", null) if tp.get("tex", null) != null else th.get("tex0", null)
		if want_tex != null and (th["mat"] as StandardMaterial3D).albedo_texture != want_tex:
			(th["mat"] as StandardMaterial3D).albedo_texture = want_tex
			th["key"] = Vector4.INF
		var key := Vector4(col.r + col.g * 3.0 + col.b * 7.0 + dx * 13.0, sc + sx * 10.0 + sy * 100.0, dy, alpha)  # unchanged since the last frame (a lamp in a steady room): leave the node alone
		if key == th.get("key", Vector4.INF):
			continue
		th["key"] = key
		node.scale = Vector3(sc * sx, sc * sy, sc)
		node.position.y = float(th["base_y"]) + dy
		if not tp.is_empty() or th.has("posed"):
			node.position.x = float(th["base_x"]) + dx
			th["posed"] = true
		(th["mat"] as StandardMaterial3D).albedo_color = Color(col.r, col.g, col.b, alpha)


## The camera moved (the sky is at infinity and needs nothing; kept for the callers).
func follow(_cam: Vector3) -> void:
	pass


## An animated surface: every wall or floor showing the map texture `name` shows `tex` instead (the LED wall).
func set_texture_override(name: String, tex: Texture2D) -> void:
	for m in _mats_by_tex.get(name, []):
		(m as StandardMaterial3D).albedo_texture = tex


## Show or hide a billboard thing by its map id (the disco ball is only there once it is switched on).
func set_thing_visible(id: String, on: bool) -> void:
	for th in _thing_nodes:
		if str(th["thing"]["id"]) == id or str(th["thing"]["id"]).begins_with(id + "_"):
			(th["node"] as Node3D).visible = on


func sector_node(id: String) -> MeshInstance3D:
	return _sector_nodes[id]["node"] if _sector_nodes.has(id) else null


func thing_count() -> int:
	return _thing_nodes.size()


## The wall decals drawn (scenery: not in thing_count, the billboard list or anything the hotspots and the figure cap read).
func decal_count() -> int:
	return _decal_nodes.size()


func decal_node(id: String) -> MeshInstance3D:
	for dn in _decal_nodes:
		if str(dn["decal"]["id"]) == id:
			return dn["node"]
	return null
