class_name StoryWeather
extends Node3D
## Weather in the 3D world (hook H10, docs/engine/WEATHER.md): rain streaks, drips at the eaves and a wet floor's gloss. Built by StoryStage beside the light show (StoryWorldFx)
## only when the map has weather (StoryMap.has_weather), so a dry map draws exactly what it drew before.
##
## Rain: one MultiMesh of thin quads (RAIN_MAX x the map's rain), all their motion in the vertex shader. Each streak has a fixed world anchor (a hash of its index); the
## shader wraps the anchors into a box ahead of the camera (BOX, BOX_AHEAD), so streaks stay put in the world as the camera moves and the ones that leave the box come back
## at its far side (re-seeded). They fall with song time (`song_t`, set from the stage's clock: a pause freezes them, a restart replays them) at FALL_SPEED, slanted by the
## map's wind. A low-res light map over the ground plane (one texel per LIGHT_CELL m) carries, per texel, the lamps' light at eye height there (lamp_light: the map's
## lights with the falloff the world is baked with, hue kept: the sodium and the moon) and whether rain falls there (StoryMap.rain_open: alpha 0 under a roof); the shader reads it per vertex, so a streak
## takes the colour of the practicals around it and a streak under a roof is collapsed to nothing. The camera sector's song-time light multiplies it.
## Drips: a second MultiMesh with the same shader in drip mode, DRIPS_PER drops per authored eave, each falling from the eave to the floor on a song-time period.
## Gloss: one MultiMesh of floor quads, one per practical whose mirror point lies on a wet floor: a stretched, broken highlight where a mirror would show the lamp
## (the mirror point between the eye and the lamp's foot), smeared toward the eye. It is a fake: no real reflection, nothing of the sprites or the walls is mirrored.

const RAIN_MAX := 420  # streaks at rain 1 (one draw call; ~840 triangles)
const REDUCED_SHARE := 0.5  # reduced effects keeps this share of the streaks
const BOX := Vector3(13.0, 7.5, 13.0)  # metres: the box of rain kept around the view
const BOX_AHEAD := 5.5  # the box's centre this far ahead of the eye (most streaks are in the frustum)
const BOX_LOW := 2.0  # the box's bottom this far below the eye (rain over the floor, not deep under it)
const FALL_SPEED := 9.0  # m/s
const STREAK_LEN := 0.55  # metres
const STREAK_W := 0.022  # metres (never thinner than one low-res pixel: the shader widens far streaks)
const NEAR_FADE := Vector2(0.7, 1.6)  # metres: a streak fades in over this range from the eye (none smear across the lens)
const FAR_FADE := Vector2(10.0, 15.0)
const LIGHT_CELL := 0.5  # metres per texel of the light map (coarser on a big map: at most LIGHT_MAX texels a side)
const LIGHT_MAX := 192
const LIGHT_SCALE := 1.5  # the light map stores lamp_light / this (an RGBA8 texture); lamp_light's brightest channel is at most this
const SECTOR_FULL := 1.5  # StoryWorld.light_of of a sector at light 1 (its gain clamps at 1.6): the rain takes the camera sector's light over this
const LAMP_Y := 1.6  # metres over the floor the light map's lamp light is taken at (eye height: the streaks most seen)
const RAIN_COL := Color(0.62, 0.68, 0.82)  # the streak's own colour before the light: a cool grey (the moon's side)
const RAIN_ALPHA := 0.55
const DRIPS_PER := 2
const DRIP_LEN := 0.09
const GLOSS_MAX := 24
const GLOSS_K := 0.42  # a gloss band's brightness: lamp colour x strength / 2.5 x wet x this
const GLOSS_REACH := 22.0  # metres: lamps farther than this from the eye cast no gloss

const SHADER := """
shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never, skip_vertex_transform, fog_disabled, shadows_disabled;
// StoryWeather: rain streaks (drip_mode false) or eave drips (drip_mode true); every position is a function of song_t (the stage's clock).
uniform float song_t = 0.0;
uniform vec3 cam = vec3(0.0);
uniform vec3 box_lo = vec3(0.0);
uniform vec3 box = vec3(13.0, 7.5, 13.0);
uniform vec2 wind = vec2(0.0);  // metres sideways per metre fallen (x, z)
uniform float fall_speed = 9.0;
uniform float streak_len = 0.55;
uniform float streak_w = 0.022;
uniform float px_per_m = 0.004;  // one low-res pixel's size per metre of distance
uniform vec2 near_fade = vec2(0.7, 1.6);
uniform vec2 far_fade = vec2(10.0, 15.0);
uniform sampler2D light_map : filter_nearest, repeat_disable;
uniform vec2 map_lo = vec2(0.0);
uniform vec2 map_size = vec2(1.0);
uniform float light_scale = 1.5;
uniform vec3 rain_col = vec3(0.62, 0.68, 0.82);
uniform vec3 sector_col = vec3(1.0);
uniform float rain_alpha = 0.55;
uniform bool drip_mode = false;

uint pcg(uint v) {
	uint state = v * 747796405u + 2891336453u;
	uint word = ((state >> ((state >> 28u) + 4u)) ^ state) * 277803737u;
	return (word >> 22u) ^ word;
}

float h01(uint v) {
	return float(pcg(v)) / 4294967295.0;
}

void vertex() {
	uint id = uint(INSTANCE_ID);
	vec3 p;
	vec3 dir = normalize(vec3(wind.x, -1.0, wind.y));
	float len = streak_len;
	float a = rain_alpha;
	vec4 L;
	if (drip_mode) {
		vec4 d = INSTANCE_CUSTOM;  // (x, eave y, z, drop height)
		float period = 0.55 + 0.9 * h01(id * 3u + 1u);
		float u = fract(song_t / period + h01(id * 3u + 2u));
		float fall = 0.5 * 9.8 * (u * period) * (u * period);
		p = vec3(d.x, d.y - fall, d.z);
		dir = vec3(0.0, -1.0, 0.0);
		len = 0.04 + 0.05 * min(fall, 1.0);
		a = fall < d.w ? 0.8 : 0.0;
		L = textureLod(light_map, (p.xz - map_lo) / map_size, 0.0);
	} else {
		vec3 anchor = vec3(h01(id * 3u), h01(id * 3u + 1u), h01(id * 3u + 2u)) * 977.0;
		float f = song_t * fall_speed;
		anchor += vec3(wind.x * f, -f, wind.y * f);
		p = box_lo + mod(anchor - box_lo, box);
		vec2 uv = (p.xz - map_lo) / map_size;
		L = textureLod(light_map, uv, 0.0);
		if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) {
			L = vec4(0.0);
		}
		a *= L.a;
	}
	float dist = length(p - cam);
	a *= smoothstep(near_fade.x, near_fade.y, dist) * (1.0 - smoothstep(far_fade.x, far_fade.y, dist));
	vec3 lit = L.rgb * light_scale;
	vec3 to_cam = normalize(cam - p);
	vec3 side = normalize(cross(dir, to_cam));
	float w = max(streak_w, dist * px_per_m);
	vec3 world = p + side * VERTEX.x * w + dir * (-VERTEX.y) * len;
	if (a <= 0.001) {
		world = cam - vec3(0.0, 100.0, 0.0);  // collapsed (and behind the near plane's reach): no area, no fill
	}
	COLOR = vec4((rain_col * 0.3 + lit * 0.9) * sector_col, a);  // a faint cool streak everywhere, the lamps' own colour near them (the sodium and the moon)
	VERTEX = (VIEW_MATRIX * vec4(world, 1.0)).xyz;
	NORMAL = vec3(0.0, 0.0, 1.0);
}

void fragment() {
	ALBEDO = COLOR.rgb;
	ALPHA = clamp(COLOR.a * mix(0.15, 1.0, UV.y), 0.0, 1.0);  // UV.y 0 at the top (the tail, faint), 1 at the falling head
}
"""

var stage: StoryStage
var map: StoryMap
var world: StoryWorld
var rain := 0.0  # the map's rain, after reduced effects (the share of RAIN_MAX drawn)
var song_t := 0.0  # the song time the weather was last drawn at (the stage's clock)
var rain_mm: MultiMeshInstance3D
var drip_mm: MultiMeshInstance3D
var gloss_mm: MultiMeshInstance3D
var light_img: Image
var light_tex: ImageTexture
var map_lo := Vector2.ZERO
var map_size := Vector2.ONE
var cell := LIGHT_CELL
var _shader: Shader
var _rain_mat: ShaderMaterial
var _drip_mat: ShaderMaterial
var _gloss_mat: StandardMaterial3D
var _gloss_lights: Array = []  # {at: Vector2, y: absolute, foot_y, color, k}
var gloss_shown := 0  # gloss bands drawn last frame (the tests read it)
var _wind := Vector2.ZERO


## Whether a map gets a weather node at all (StoryStage): rain or an authored wet floor.
static func wanted(m: StoryMap) -> bool:
	return m != null and m.has_weather()


func build(p_stage: StoryStage, p_map: StoryMap, p_world: StoryWorld) -> void:
	stage = p_stage
	map = p_map
	world = p_world
	name = "Weather"
	rain = clampf(float(map.weather.get("rain", 0.0)), 0.0, 1.0) * (REDUCED_SHARE if stage != null and stage.reduced else 1.0)
	var wd := deg_to_rad(float(map.weather.get("wind", 0.0)))
	_wind = Vector2(tan(wd), 0.0)
	_build_light_map()
	_shader = Shader.new()
	_shader.code = SHADER
	_build_rain()
	_build_drips()
	_build_gloss()


# --- construction ----------------------------------------------------------------------------------------------------------------------

## The ground-plane light map: rgb = the lamps' light on a figure there (/ LIGHT_SCALE), a = 1 where rain falls (an open sector), 0 under a roof or outside the map.
func _build_light_map() -> void:
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	for s in map.sectors:
		for q in (s["poly"] as PackedVector2Array):
			lo = Vector2(minf(lo.x, q.x), minf(lo.y, q.y))
			hi = Vector2(maxf(hi.x, q.x), maxf(hi.y, q.y))
	if lo.x == INF:
		lo = Vector2.ZERO
		hi = Vector2.ONE
	cell = maxf(LIGHT_CELL, maxf(hi.x - lo.x, hi.y - lo.y) / float(LIGHT_MAX))
	var w := maxi(int(ceil((hi.x - lo.x) / cell)), 1)
	var h := maxi(int(ceil((hi.y - lo.y) / cell)), 1)
	map_lo = lo
	map_size = Vector2(w, h) * cell
	light_img = Image.create(w, h, false, Image.FORMAT_RGBA8)
	light_img.fill(Color(0, 0, 0, 0))
	for s in map.sectors:  # each sector paints the texels whose centres it holds (its bounding box only: cheap on a map of hundreds of pieces)
		var poly: PackedVector2Array = s["poly"]
		if poly.size() < 3:
			continue
		var sid := str(s["id"])
		var open := 1.0 if map.rain_open(sid) else 0.0
		var plo := Vector2(INF, INF)
		var phi := Vector2(-INF, -INF)
		for q in poly:
			plo = Vector2(minf(plo.x, q.x), minf(plo.y, q.y))
			phi = Vector2(maxf(phi.x, q.x), maxf(phi.y, q.y))
		for j in range(maxi(int(floor((plo.y - lo.y) / cell)), 0), mini(int(ceil((phi.y - lo.y) / cell)), h)):
			for i in range(maxi(int(floor((plo.x - lo.x) / cell)), 0), mini(int(ceil((phi.x - lo.x) / cell)), w)):
				var p := lo + Vector2(i + 0.5, j + 0.5) * cell
				if not Geometry2D.is_point_in_polygon(p, poly):
					continue
				var c := lamp_light(p, s)
				light_img.set_pixel(i, j, Color(c.r / LIGHT_SCALE, c.g / LIGHT_SCALE, c.b / LIGHT_SCALE, open))
	light_tex = ImageTexture.create_from_image(light_img)


var _lamps_of: Dictionary = {}  # sector id -> map.lights_reaching (cached)


## The lamps' light on the air at ground point p of sector s, LAMP_Y above its floor: each light's colour x strength with the squared falloff StoryWorld bakes the surfaces with (cones
## ignored: rain under a window's cone is lit as if the lamp shone all round). Unclamped per channel and scaled down as a whole when its brightest channel passes LIGHT_SCALE,
## so a streak by a sodium lamp stays orange (StoryWorld.figure_light clamps each channel, which turns a strong lamp white).
func lamp_light(p: Vector2, s: Dictionary) -> Color:
	var sid := str(s["id"])
	if not _lamps_of.has(sid):
		_lamps_of[sid] = map.lights_reaching(sid)
	var y := float(s.get("floor", 0.0)) + LAMP_Y
	var col := Color(0, 0, 0)
	for l in _lamps_of[sid]:
		var at: Vector2 = l["at"]
		var ly := float(map.sector(str(l["sector"])).get("floor", 0.0)) + float(l["y"])
		var dist := Vector3(p.x - at.x, y - ly, p.y - at.y).length()
		var r := float(l["radius"])
		if dist >= r:
			continue
		var f := 1.0 - dist / r
		var lc: Color = l["color"]
		var k := f * f * float(l["strength"])
		col = Color(col.r + lc.r * k, col.g + lc.g * k, col.b + lc.b * k)
	var mx := maxf(col.r, maxf(col.g, col.b))
	if mx > LIGHT_SCALE:
		col = col * (LIGHT_SCALE / mx)
	return Color(col.r, col.g, col.b, 1.0)


## Whether rain falls at ground point p by the light map (what the shader reads): the texel's alpha.
func rain_at(p: Vector2) -> bool:
	var q := (p - map_lo) / cell
	var i := int(floor(q.x))
	var j := int(floor(q.y))
	if i < 0 or j < 0 or i >= light_img.get_width() or j >= light_img.get_height():
		return false
	return light_img.get_pixel(i, j).a > 0.5


func _material(drip: bool) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = _shader
	m.set_shader_parameter("light_map", light_tex)
	m.set_shader_parameter("map_lo", map_lo)
	m.set_shader_parameter("map_size", map_size)
	m.set_shader_parameter("light_scale", LIGHT_SCALE)
	m.set_shader_parameter("rain_col", Vector3(RAIN_COL.r, RAIN_COL.g, RAIN_COL.b))
	m.set_shader_parameter("box", BOX)
	m.set_shader_parameter("wind", _wind)
	m.set_shader_parameter("fall_speed", FALL_SPEED)
	m.set_shader_parameter("streak_len", STREAK_LEN if not drip else DRIP_LEN)
	m.set_shader_parameter("streak_w", STREAK_W)
	m.set_shader_parameter("near_fade", NEAR_FADE if not drip else Vector2(0.3, 0.6))
	m.set_shader_parameter("far_fade", FAR_FADE)
	m.set_shader_parameter("rain_alpha", RAIN_ALPHA)
	m.set_shader_parameter("drip_mode", drip)
	return m


func _mm_node(mm: MultiMesh, mat: Material, nm: String) -> MultiMeshInstance3D:
	var mi := MultiMeshInstance3D.new()
	mi.name = nm
	mi.multimesh = mm
	mi.material_override = mat
	mi.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.custom_aabb = AABB(Vector3(-1.0e4, -1.0e4, -1.0e4), Vector3(2.0e4, 2.0e4, 2.0e4))  # the shader moves every vertex: never frustum-culled on the instances' own transforms
	add_child(mi)
	return mi


func _build_rain() -> void:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	var q := QuadMesh.new()
	q.size = Vector2.ONE
	mm.mesh = q
	mm.instance_count = int(round(RAIN_MAX * rain))  # density is the instance count (rain 0: none drawn)
	for i in mm.instance_count:
		mm.set_instance_transform(i, Transform3D.IDENTITY)
	_rain_mat = _material(false)
	rain_mm = _mm_node(mm, _rain_mat, "Rain")
	rain_mm.visible = mm.instance_count > 0


func _build_drips() -> void:
	var drips: Array = map.weather.get("drips", [])
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	var q := QuadMesh.new()
	q.size = Vector2.ONE
	mm.mesh = q
	mm.instance_count = drips.size() * DRIPS_PER if rain > 0.0 else 0  # a dry night has no drips
	for k in mm.instance_count:
		var d: Dictionary = drips[k / DRIPS_PER]
		var at: Vector2 = d["at"]
		var fy := float(map.sector(str(d["sector"])).get("floor", 0.0))
		mm.set_instance_transform(k, Transform3D.IDENTITY)
		mm.set_instance_custom_data(k, Color(at.x + 0.12 * float(k % DRIPS_PER) - 0.06, fy + float(d["h"]), at.y, float(d["h"])))
	_drip_mat = _material(true)
	drip_mm = _mm_node(mm, _drip_mat, "Drips")
	drip_mm.visible = mm.instance_count > 0


func _build_gloss() -> void:
	for s in map.sectors:
		if map.wet_of(str(s["id"])) > 0.0:
			_any_wet = true
	for l in map.lights:  # the practicals that can shine on a wet floor
		var sec := map.sector(str(l["sector"]))
		var fy := float(sec.get("floor", 0.0))
		_gloss_lights.append({"at": l["at"], "y": fy + float(l["y"]), "foot_y": fy, "color": l["color"], "k": clampf(float(l["strength"]) / 2.5, 0.0, 1.0) * clampf(float(l["radius"]) / 6.0, 0.3, 1.0)})
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_colors = true
	var q := QuadMesh.new()
	q.size = Vector2.ONE
	q.orientation = PlaneMesh.FACE_Y
	mm.mesh = q
	mm.instance_count = GLOSS_MAX
	mm.visible_instance_count = 0
	_gloss_mat = StandardMaterial3D.new()
	_gloss_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_gloss_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_gloss_mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	_gloss_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	_gloss_mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	_gloss_mat.vertex_color_use_as_albedo = true
	_gloss_mat.disable_fog = true
	_gloss_mat.albedo_texture = _gloss_texture()
	_gloss_mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR
	gloss_mm = MultiMeshInstance3D.new()
	gloss_mm.name = "Gloss"
	gloss_mm.multimesh = mm
	gloss_mm.material_override = _gloss_mat
	gloss_mm.gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	gloss_mm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	gloss_mm.visible = false
	add_child(gloss_mm)


## A gloss band: soft across, broken into ripples along its length (rows of uneven brightness), brightest at the mirror point (v = 0.25) and fading toward the eye (v = 1).
static func _gloss_texture() -> ImageTexture:
	var w := 16
	var h := 64
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	for y in h:
		var v := (float(y) + 0.5) / float(h)
		var along := smoothstep(0.0, 0.25, v) * (1.0 - smoothstep(0.3, 1.0, v) * 0.85)
		var row := 0.45 + 0.55 * fposmod(sin(float(y) * 12.9898) * 43758.5453, 1.0)  # the ripples
		for x in w:
			var u := (float(x) + 0.5) / float(w) * 2.0 - 1.0
			var across := exp(-u * u * 3.5) * (0.8 + 0.4 * fposmod(sin(float(x * 7 + y * 13) * 4.1) * 931.7, 1.0) * (1.0 - absf(u)))
			img.set_pixel(x, y, Color(1, 1, 1, clampf(along * row * across, 0.0, 1.0)))
	return ImageTexture.create_from_image(img)


# --- per frame -------------------------------------------------------------------------------------------------------------------------

## Draw the weather at song time t from the stage's camera (lowres.camera). Everything is a function of t and the camera: a paused song holds every streak still.
func update(t: float, cam_node: Camera3D, sector_light: Color, vis: Dictionary = {}) -> void:
	song_t = t
	var cam := cam_node.position
	var fwd3 := -cam_node.transform.basis.z
	var fwd := Vector3(fwd3.x, 0.0, fwd3.z)
	fwd = fwd.normalized() if fwd.length() > 1.0e-4 else Vector3(0, 0, -1)
	var centre := cam + fwd * BOX_AHEAD
	var lo := Vector3(centre.x - BOX.x * 0.5, cam.y - BOX_LOW, centre.z - BOX.z * 0.5)
	var px := 2.0 * tan(deg_to_rad(StoryProjector.FOV_V * 0.5)) / maxf(float(stage.lowres.sub.size.y) if stage != null and stage.lowres != null else 360.0, 1.0)
	var sc := Vector3(sector_light.r, sector_light.g, sector_light.b) / SECTOR_FULL  # the camera sector's song-time light, as a share of a full-bright sector's (it breathes with the room)
	for m: ShaderMaterial in [_rain_mat, _drip_mat]:
		m.set_shader_parameter("song_t", t)
		m.set_shader_parameter("cam", cam)
		m.set_shader_parameter("box_lo", lo)
		m.set_shader_parameter("px_per_m", px)
		m.set_shader_parameter("sector_col", sc)
	_update_gloss(t, cam, vis)


func _update_gloss(t: float, cam: Vector3, vis: Dictionary) -> void:
	if not _any_wet:
		return
	var mm := gloss_mm.multimesh
	var key := Vector3(snappedf(cam.x, 0.02), snappedf(cam.y, 0.02), snappedf(cam.z, 0.02))
	if key != _gloss_key or vis.size() != _gloss_vis_n:  # the bands only move with the eye: placed again when it moves, only their shimmer otherwise
		_gloss_key = key
		_gloss_vis_n = vis.size()
		_place_gloss(cam, vis)
	for n in gloss_shown:
		var b: Dictionary = _gloss_bands[n]
		var shimmer := 0.85 + 0.15 * sin(t * 5.3 + float(b["i"]) * 1.7)  # the rain on the puddle (song time: frozen on pause)
		var c: Color = b["col"]
		mm.set_instance_color(n, Color(c.r * shimmer, c.g * shimmer, c.b * shimmer, 1.0))


var _any_wet := false
var _gloss_key := Vector3.INF
var _gloss_vis_n := -1
var _gloss_bands: Array = []  # the bands placed for the current eye: {i (the light's index), col}


func _place_gloss(cam: Vector3, vis: Dictionary) -> void:
	var mm := gloss_mm.multimesh
	var n := 0
	_gloss_bands = []
	var eye := Vector2(cam.x, cam.z)
	for i in _gloss_lights.size():
		if n >= GLOSS_MAX:
			break
		var gl: Dictionary = _gloss_lights[i]
		var foot: Vector2 = gl["at"]
		var d := foot.distance_to(eye)
		if d > GLOSS_REACH or d < 0.8:
			continue
		var e := cam.y - float(gl["foot_y"])  # the eye's height over the lamp's floor
		var hgt := float(gl["y"]) - float(gl["foot_y"])
		if e <= 0.1 or hgt <= 0.1:
			continue
		var hit := eye + (foot - eye) * (e / (e + hgt))  # where a mirror floor shows the lamp
		var sid := map.sector_at(hit)
		if sid == "" or (not vis.is_empty() and not vis.has(sid)):
			continue
		var wet := map.wet_of(sid)
		if wet <= 0.0:
			continue
		var along := (hit - eye).normalized()  # from the eye toward the lamp
		var side := Vector2(-along.y, along.x)
		var length := clampf(eye.distance_to(hit) * 0.75, 0.8, 4.0)
		var width := 0.3 + 0.25 * float(gl["k"])
		var centre := hit - along * (length * 0.5 - length * 0.25)  # the band runs from just past the mirror point toward the eye (v = 0.25 at the mirror point)
		var fy := float(map.sector(sid).get("floor", 0.0)) + 0.012
		var basis := Basis(Vector3(side.x, 0, side.y) * width, Vector3.UP, Vector3(-along.x, 0, -along.y) * length)  # +z of the quad (v = 1) toward the eye
		mm.set_instance_transform(n, Transform3D(basis, Vector3(centre.x, fy, centre.y)))
		var c: Color = gl["color"]
		var k := float(gl["k"]) * wet * GLOSS_K
		_gloss_bands.append({"i": i, "col": Color(c.r * k, c.g * k, c.b * k)})
		n += 1
	mm.visible_instance_count = n
	gloss_shown = n
	gloss_mm.visible = n > 0


# --- the shader's maths on the CPU (the tests check placement with it) -----------------------------------------------------------------

static func _pcg(v: int) -> int:
	var state := (v * 747796405 + 2891336453) & 0xFFFFFFFF
	var word := ((((state >> ((state >> 28) + 4)) ^ state) & 0xFFFFFFFF) * 277803737) & 0xFFFFFFFF
	return ((word >> 22) ^ word) & 0xFFFFFFFF


static func _h01(v: int) -> float:
	return float(_pcg(v)) / 4294967295.0


## Where streak `i` is at song time t for a box whose low corner is `lo` (the shader's rain branch, in GDScript).
func streak_pos(i: int, t: float, lo: Vector3) -> Vector3:
	var anchor := Vector3(_h01(i * 3), _h01(i * 3 + 1), _h01(i * 3 + 2)) * 977.0
	var f := t * FALL_SPEED
	anchor += Vector3(_wind.x * f, -f, _wind.y * f)
	return lo + Vector3(fposmod(anchor.x - lo.x, BOX.x), fposmod(anchor.y - lo.y, BOX.y), fposmod(anchor.z - lo.z, BOX.z))


## The box's low corner the last update used (the shader's box_lo).
func box_lo() -> Vector3:
	return _rain_mat.get_shader_parameter("box_lo")


## Draw calls this node adds when everything is on screen: rain, drips, gloss (each one MultiMesh, one surface).
func draw_calls() -> int:
	return int(rain_mm.visible) + int(drip_mm.visible) + int(gloss_mm.visible)
