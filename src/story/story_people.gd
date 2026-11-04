class_name StoryPeople
extends RefCounted
## The chapter's baked people (docs/STORY_25D_ART_DIRECTION.md 2.E): assets/story/<chapter>/people/people.json (the frame table and, per actor, the frames of
## each state, facing and level of detail), its indexed pages and the palette, from tools/story/art/people_sheets.py. One ShaderMaterial (story_people.gdshader)
## draws every person of the chapter; `light_img` holds the light each actor stands in (one texel per palette row), refreshed by the stage every frame.
## Loaded once per chapter and shared (the tests build many stages). Missing files: `ok()` is false and the crowd keeps the live rig.

const FIELDS := 9  # page, x, y, w, h, pivot_x, pivot_y, hand_x, hand_y
const FACINGS := ["front", "side", "back"]
static var _cache: Dictionary = {}

var art := ""
var h0 := 112.0
var lods: Array = [1, 2, 4]
var frames := PackedInt32Array()
var actors: Dictionary = {}
var pages: Array = []  # Texture2D
var material: ShaderMaterial
var light_img: Image
var light_tex: ImageTexture
var rows := 1
var _light_dirty := false


static func for_assets(assets: StoryAssets) -> StoryPeople:
	if assets == null or assets.manifest.is_empty():
		return null
	var key := assets.art
	if _cache.has(key):
		return _cache[key]
	var p := StoryPeople.new()
	if not p._load(assets):
		p = null
	_cache[key] = p
	return p


func ok() -> bool:
	return not actors.is_empty()


static var _prep: Dictionary = {}  # art -> {thread: Thread, images: Array}


## One page as an R8 image (decoded from the imported texture; safe to call off the main thread).
static func _decode_page(path: String) -> Image:
	var src: Texture2D = load(path) if ResourceLoader.exists(path) else null
	var im: Image = src.get_image() if src != null else null
	if im != null and im.get_format() != Image.FORMAT_R8:
		im.convert(Image.FORMAT_R8)
	return im


static func _decode_job(root: String, file: String, job: Dictionary) -> void:
	var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(root + file))
	if typeof(doc) != TYPE_DICTIONARY:
		return
	for f in doc.get("pages", []):
		(job["images"] as Array).append(_decode_page(root + str(f)))


## Decodes the people pages of a chapter's art on a worker thread so that building its stage later only has to upload them (the run builds the next world's stage during
## a cue-free guard, where decoding a dozen 2048-pixel pages on the main thread stalled it for a second). Safe to call twice; `for_assets` joins the thread when it needs the pages.
static func prewarm(assets: StoryAssets) -> void:
	if assets == null or assets.manifest.is_empty() or _cache.has(assets.art) or _prep.has(assets.art) or OS.has_environment("RW_STORY_RIG"):
		return
	var sec: Dictionary = assets.manifest.get("people", {})
	if sec.is_empty() or not FileAccess.file_exists(assets.root + str(sec.get("file", ""))):
		return
	var job := {"thread": Thread.new(), "images": []}
	_prep[assets.art] = job
	(job["thread"] as Thread).start(_decode_job.bind(assets.root, str(sec["file"]), job))


static func _take_prepared(art_id: String) -> Array:
	if not _prep.has(art_id):
		return []
	var job: Dictionary = _prep[art_id]
	_prep.erase(art_id)
	(job["thread"] as Thread).wait_to_finish()
	return job["images"]


func _load(assets: StoryAssets) -> bool:
	art = assets.art
	var sec: Dictionary = assets.manifest.get("people", {})
	if sec.is_empty() or OS.has_environment("RW_STORY_RIG"):
		return false
	var path := assets.root + str(sec.get("file", ""))
	if not FileAccess.file_exists(path):
		return false
	var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(doc) != TYPE_DICTIONARY:
		return false
	h0 = float(doc.get("h0", 112))
	lods = doc.get("lods", [1, 2, 4])
	frames = PackedInt32Array(doc.get("frames", []))
	actors = doc.get("actors", {})
	var prepared := _take_prepared(art)  # page images a worker thread has already decoded (prewarm), else decoded here
	var k := 0
	for f in doc.get("pages", []):  # as R8 textures: the compatibility renderer does not hand an imported L8 texture's value to the shader as is
		var im: Image = prepared[k] if k < prepared.size() else _decode_page(assets.root + str(f))
		k += 1
		if im == null:
			pages.append(null)
			continue
		pages.append(ImageTexture.create_from_image(im))
	var pal: Texture2D = assets.texture(str(doc.get("palette", "")))
	for a in actors:
		rows = maxi(rows, int(actors[a]["row"]) + 1)
	light_img = Image.create(maxi(rows, 1), 1, false, Image.FORMAT_RGBA8)
	light_img.fill(Color(0.5, 0.5, 0.5))
	light_tex = ImageTexture.create_from_image(light_img)
	material = ShaderMaterial.new()
	material.shader = load("res://src/story/story_people.gdshader")
	material.set_shader_parameter("palette", pal)
	material.set_shader_parameter("light_tex", light_tex)
	return not actors.is_empty()


func entry(actor_id: String) -> Dictionary:
	return actors.get(actor_id, {})


## The light an actor stands in (song-time light of their sector times the lamps around them), stored halved so 2.0 fits.
func set_light(row: int, c: Color) -> void:
	if light_img == null or row < 0 or row >= rows:
		return
	light_img.set_pixel(row, 0, Color(clampf(c.r * 0.5, 0.0, 1.0), clampf(c.g * 0.5, 0.0, 1.0), clampf(c.b * 0.5, 0.0, 1.0)))
	_light_dirty = true


func flush_light() -> void:
	if _light_dirty and light_tex != null:
		light_tex.update(light_img)
		_light_dirty = false


func set_fog(c: Color) -> void:
	if material != null:
		material.set_shader_parameter("fog_color", Vector3(c.r, c.g, c.b))
