class_name SpriteBank
extends RefCounted
## The OpenRA sprite catalogue (assets/openra/catalogue.json) with lazy texture loading and frame selection.
## Red Alert frames run counter-clockwise from north; screen headings are radians with 0 = +x and y down.

const CATALOGUE := "res://assets/openra/catalogue.json"
const RA_CELL_PX := 24.0

var items: Dictionary = {}
var remap_ramp: Array = []
var _textures: Dictionary = {}


func load() -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(CATALOGUE))
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("catalogue.json unreadable")
		return
	remap_ramp = parsed.get("remap_ramp_rgb", [])
	for it in parsed.get("items", []):
		items[str(it["id"])] = it


func item(actor: String) -> Dictionary:
	return items.get("openra." + actor, {})


func texture(path: String) -> Texture2D:
	if _textures.has(path):
		return _textures[path]
	var tex: Texture2D = load(path) if ResourceLoader.exists(path) else null
	_textures[path] = tex
	return tex


static func frame_path(prefix: String, index: int) -> String:
	return "res://assets/openra/%s-%04d.png" % [prefix, index]


## Facing frame index (0..facings-1) for a screen heading, counter-clockwise from north like the RA sheets.
static func facing_index(heading: float, facings: int) -> int:
	var compass_cw := fposmod(rad_to_deg(heading) + 90.0, 360.0)
	var ccw := fposmod(360.0 - compass_cw, 360.0)
	return int(round(ccw / 360.0 * facings)) % facings


## Textures for a building state ("idle", "damaged", "make", "active"), with fallbacks.
func building_frames(actor: String, state: String) -> Array:
	var it := item(actor)
	var states: Dictionary = it.get("states", {})
	if states.has(state):
		return states[state].get("files", [])
	if state == "damaged":
		if it.has("damaged_frame"):
			return [frame_path(str(it["prefix"]), int(it["damaged_frame"]))]
		return building_frames(actor, "idle")
	if states.has("idle"):
		return states["idle"].get("files", [])
	var frames: Array = it.get("frames_godot", [])
	return [frames[0]] if not frames.is_empty() else []


func state_fps(actor: String, state: String) -> int:
	var states: Dictionary = item(actor).get("states", {})
	return int(states.get(state, {}).get("fps", 0))


## Sprite sheet size in RA pixels for a building state (width, height), used to scale onto the cell grid.
func building_size(actor: String, state: String) -> Vector2:
	var it := item(actor)
	var states: Dictionary = it.get("states", {})
	if states.has(state):
		return Vector2(float(states[state].get("width", 24)), float(states[state].get("height", 24)))
	if states.has("idle"):
		return Vector2(float(states["idle"].get("width", 24)), float(states["idle"].get("height", 24)))
	return Vector2(float(it.get("width", 24)), float(it.get("height", 24)))
