class_name StoryAssets
extends RefCounted
## The art manifest (assets/story/night_one/manifest.json, written by tools/story/build_assets.py) and a texture cache. The
## runtime reads only what the manifest names (tools/story/ART_CONTRACT.md). Missing files degrade to "not drawn", never a crash.

const BASE := "res://assets/story/"
const DEFAULT_ART := "night_one"

var root := BASE + DEFAULT_ART + "/"
var art := DEFAULT_ART
var manifest: Dictionary = {}
var errors: Array = []
var extra: StoryAssets = null  # another art set whose archetypes this chapter may borrow (the human ravers of Night One)
var _tex: Dictionary = {}


static func load_default() -> StoryAssets:
	return load_art(DEFAULT_ART)


## One chapter's art folder (assets/story/<art>/manifest.json). Chapters other than Night One also see Night One's human dancers.
static func load_art(art_dir: String, with_shared := true) -> StoryAssets:
	var a := StoryAssets.new()
	a.art = art_dir
	a.root = BASE + art_dir + "/"
	var path := a.root + "manifest.json"
	if not FileAccess.file_exists(path):
		a.errors.append("art manifest missing: " + path)
		return a
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY:
		a.errors.append("art manifest is not a JSON object")
		return a
	a.manifest = parsed
	if with_shared and art_dir != DEFAULT_ART:
		a.extra = load_art(DEFAULT_ART, false)
	return a


## The rig of an archetype variant (joints and height merged in), from this set or the shared one. {} when unknown.
func rig(archetype: String, variant: String, source := "") -> Dictionary:
	var owner: StoryAssets = self
	if source == DEFAULT_ART and art != DEFAULT_ART and extra != null:
		owner = extra
	elif not manifest.get("archetypes", {}).has(archetype) and extra != null:
		owner = extra
	var ad: Dictionary = owner.manifest.get("archetypes", {}).get(archetype, {})
	var r: Dictionary = (ad.get("variants", {}).get(variant, {}) as Dictionary).duplicate()
	if r.is_empty():
		return {}
	r["joints"] = ad.get("joints", {})
	r["height"] = ad.get("height", 260)
	r["_assets"] = owner
	return r


## Pack every dancer part and face of the chapter's rigs into one texture atlas (rig parts are many small SVG textures: drawn separately each one is its own draw call, 40 dancers
## are some 500 of them a frame; from one atlas the canvas batches them). Call it once before any StoryCharacter is built (the playing scene does; headless tests do not need it).
## `texture(file)` then hands out AtlasTextures of the shared sheet, so nothing else changes. Deterministic: files are packed in sorted order, shelf by shelf.
const ATLAS_W := 4096
const ATLAS_PAD := 2


func build_rig_atlas() -> void:
	if not _atlas_done and not manifest.is_empty() and not OS.has_environment("RW_STORY_NOATLAS"):
		_atlas_done = true
		var files: Array = []
		for aid in manifest.get("archetypes", {}):
			for vid in manifest["archetypes"][aid].get("variants", {}):
				var v: Dictionary = manifest["archetypes"][aid]["variants"][vid]
				for p in v.get("parts", []):
					if str(p.get("file", "")) not in files:
						files.append(str(p["file"]))
				for k in v.get("faces", {}):
					if str(v["faces"][k].get("file", "")) not in files:
						files.append(str(v["faces"][k]["file"]))
		files.sort()
		var imgs: Dictionary = {}
		var x := 0
		var y := 0
		var row_h := 0
		var rects: Dictionary = {}
		for f in files:
			var t: Texture2D = texture(f)
			if t == null:
				continue
			var im := t.get_image()
			if im == null:
				continue
			if im.is_compressed():
				im.decompress()
			im.convert(Image.FORMAT_RGBA8)
			if x + im.get_width() + ATLAS_PAD > ATLAS_W:
				x = 0
				y += row_h + ATLAS_PAD
				row_h = 0
			imgs[f] = im
			rects[f] = Rect2i(x, y, im.get_width(), im.get_height())
			x += im.get_width() + ATLAS_PAD
			row_h = maxi(row_h, im.get_height())
		var h := 1
		while h < y + row_h:
			h *= 2
		if h > 8192 or imgs.is_empty():
			return
		var atlas := Image.create(ATLAS_W, h, false, Image.FORMAT_RGBA8)
		for f in imgs:
			atlas.blit_rect(imgs[f], Rect2i(Vector2i.ZERO, imgs[f].get_size()), (rects[f] as Rect2i).position)
		var tex := ImageTexture.create_from_image(atlas)
		for f in rects:
			var at := AtlasTexture.new()
			at.atlas = tex
			at.region = Rect2(rects[f])
			_tex[f] = at
		atlas_size = Vector2i(ATLAS_W, h)
	if extra != null:
		extra.build_rig_atlas()


var _atlas_done := false
var atlas_size := Vector2i.ZERO


func ok() -> bool:
	return not manifest.is_empty()


func texture(file: String) -> Texture2D:
	if file.is_empty():
		return null
	if _tex.has(file):
		return _tex[file]
	var path := root + file
	var t: Texture2D = null
	if ResourceLoader.exists(path):
		t = load(path) as Texture2D
	if t == null:
		errors.append("missing texture " + file)
	_tex[file] = t
	return t


## A sprite entry ({file, pivot, px_scale}) as {tex, pivot: Vector2, scale: float}.
func sprite(id: String) -> Dictionary:
	var s: Dictionary = manifest.get("stage", {}).get("sprites", {}).get(id, manifest.get("sprites", {}).get(id, {}))
	if s.is_empty() and extra != null and bool(manifest.get("borrow_sprites", false)):  # a path's art world (assets/story/airfield ...) borrows Night One's light and deck sprites
		return extra.sprite(id)
	return _entry(s)


func _entry(s: Dictionary) -> Dictionary:
	if s.is_empty():
		return {}
	var piv: Array = s.get("pivot", [0, 0])
	return {"tex": texture(str(s.get("file", ""))), "pivot": Vector2(float(piv[0]), float(piv[1])), "scale": float(s.get("px_scale", 1.0))}


func archetype_ids() -> Array:
	return manifest.get("archetypes", {}).keys()


func piece(id: String) -> Dictionary:
	for p in all_pieces():
		if str(p.get("id", "")) == id:
			return p
	return {}


func pieces(view_id := "main") -> Array:
	if view_id == "main":
		return manifest.get("stage", {}).get("pieces", [])
	return view(view_id).get("pieces", [])


func all_pieces() -> Array:
	var out: Array = []
	for v in view_ids():
		out.append_array(pieces(str(v)))
	return out


## An interlude sprite (assets/story/<chapter>/manifest.json "interlude").
func interlude_sprite(id: String) -> Dictionary:
	return _entry(manifest.get("interlude", {}).get("sprites", {}).get(id, {}))


func interlude_anchor(key: String, default: Variant = null) -> Variant:
	return manifest.get("interlude", {}).get("anchors", {}).get(key, default)


func layer(id: String) -> Dictionary:  # the backdrop layer is the Story Campaign menu's thumbnail
	for l in manifest.get("stage", {}).get("layers", []):
		if str(l.get("id", "")) == id:
			return l
	return {}


## The rooms of a chapter that own set pieces (manifest stage.views, each {id, pieces}); "main" is the first room.
func view_ids() -> Array:
	var out: Array = ["main"]
	for v in manifest.get("stage", {}).get("views", []):
		out.append(str(v["id"]))
	return out


func view(id: String) -> Dictionary:
	for v in manifest.get("stage", {}).get("views", []):
		if str(v["id"]) == id:
			return v
	return {}
