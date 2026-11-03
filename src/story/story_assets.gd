class_name StoryAssets
extends RefCounted
## The art manifest (assets/story/night_one/manifest.json, written by tools/story/build_assets.py) and a texture cache. The
## runtime reads only what the manifest names (tools/story/ART_CONTRACT.md). Missing files degrade to "not drawn", never a crash.

const ROOT := "res://assets/story/night_one/"
const MANIFEST := ROOT + "manifest.json"

var manifest: Dictionary = {}
var errors: Array = []
var _tex: Dictionary = {}


static func load_default() -> StoryAssets:
	var a := StoryAssets.new()
	if not FileAccess.file_exists(MANIFEST):
		a.errors.append("art manifest missing: " + MANIFEST)
		return a
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	if typeof(parsed) != TYPE_DICTIONARY:
		a.errors.append("art manifest is not a JSON object")
		return a
	a.manifest = parsed
	return a


func ok() -> bool:
	return not manifest.is_empty()


func texture(file: String) -> Texture2D:
	if file.is_empty():
		return null
	if _tex.has(file):
		return _tex[file]
	var path := ROOT + file
	var t: Texture2D = null
	if ResourceLoader.exists(path):
		t = load(path) as Texture2D
	if t == null:
		errors.append("missing texture " + file)
	_tex[file] = t
	return t


## A sprite entry ({file, pivot, px_scale}) as {tex, pivot: Vector2, scale: float}.
func sprite(id: String) -> Dictionary:
	var s: Dictionary = manifest.get("sprites", {}).get(id, {})
	return _entry(s)


func _entry(s: Dictionary) -> Dictionary:
	if s.is_empty():
		return {}
	var piv: Array = s.get("pivot", [0, 0])
	return {"tex": texture(str(s.get("file", ""))), "pivot": Vector2(float(piv[0]), float(piv[1])), "scale": float(s.get("px_scale", 1.0))}


func archetype_ids() -> Array:
	return manifest.get("archetypes", {}).keys()


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
