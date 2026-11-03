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
	return _entry(s)


func _entry(s: Dictionary) -> Dictionary:
	if s.is_empty():
		return {}
	var piv: Array = s.get("pivot", [0, 0])
	return {"tex": texture(str(s.get("file", ""))), "pivot": Vector2(float(piv[0]), float(piv[1])), "scale": float(s.get("px_scale", 1.0))}


func archetype_ids() -> Array:
	return manifest.get("archetypes", {}).keys()


func piece(id: String) -> Dictionary:
	for p in manifest.get("stage", {}).get("pieces", []):
		if str(p.get("id", "")) == id:
			return p
	return {}


func pieces() -> Array:
	return manifest.get("stage", {}).get("pieces", [])


## An interlude sprite (assets/story/<chapter>/manifest.json "interlude").
func interlude_sprite(id: String) -> Dictionary:
	return _entry(manifest.get("interlude", {}).get("sprites", {}).get(id, {}))


func interlude_anchor(key: String, default: Variant = null) -> Variant:
	return manifest.get("interlude", {}).get("anchors", {}).get(key, default)


func layer(id: String) -> Dictionary:
	for l in manifest.get("stage", {}).get("layers", []):
		if str(l.get("id", "")) == id:
			return l
	return {}


func anchor(key: String, default: Variant = null) -> Variant:
	return manifest.get("stage", {}).get("anchors", {}).get(key, default)


## Floor row interpolation: depth 0 (back) to 1 (front) -> {y, scale}.
func floor_at(depth: float) -> Dictionary:
	var rows: Array = anchor("floor_rows", [])
	if rows.is_empty():
		return {"y": 300.0 + depth * 140.0, "scale": 0.55 + depth * 0.45}
	var f := clampf(depth, 0.0, 1.0) * float(rows.size() - 1)
	var i := mini(int(floor(f)), rows.size() - 2)
	var u := f - float(i)
	var a: Dictionary = rows[i]
	var b: Dictionary = rows[i + 1]
	return {"y": lerpf(float(a["y"]), float(b["y"]), u), "scale": lerpf(float(a["scale"]), float(b["scale"]), u)}
