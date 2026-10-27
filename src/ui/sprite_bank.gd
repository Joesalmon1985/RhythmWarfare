class_name SpriteBank
extends RefCounted
## OpenRA sprite sequences (assets/openra/sequences.json, produced by tools/extract_openra.py from mods/ra/sequences)
## with lazy texture loading. Frames are native Red Alert pixels: assets/openra/<file>-NNNN.png, NNNN = frame index
## inside that file. Every sequence carries a resolved frame_table[facing_block][frame].
##
## Facings (sequences.json facing_notes): OpenRA angles are 1024 per turn, 0 = north, counter-clockwise. The block
## for N facings is Util.IndexFacing; 32-facing Red Alert vehicle and turret art uses the classic ranges table.

const SEQUENCES := "res://assets/openra/sequences.json"
const CATALOGUE := "res://assets/openra/catalogue.json"
const RA_CELL_PX := 24.0
const TICK_MS := 40.0
const CLASSIC_RANGES := [20, 56, 88, 132, 156, 184, 212, 240, 268, 296, 324, 352, 384, 416, 452, 488, 532, 568, 604, 644,
	668, 696, 724, 752, 780, 808, 836, 864, 896, 928, 964, 1000]

var images: Dictionary = {}
var shadow_index := 4
var remap_ramp: Array = []
var _textures: Dictionary = {}
var _missing: Dictionary = {}


func load() -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(SEQUENCES)) if FileAccess.file_exists(SEQUENCES) else null
	if typeof(parsed) == TYPE_DICTIONARY:
		images = parsed.get("images", {})
		shadow_index = int(parsed.get("shadow_index", 4))
	else:
		push_warning("sequences.json missing: run tools/extract_openra.py")
	var cat: Variant = JSON.parse_string(FileAccess.get_file_as_string(CATALOGUE)) if FileAccess.file_exists(CATALOGUE) else null
	if typeof(cat) == TYPE_DICTIONARY:
		remap_ramp = cat.get("remap_ramp_rgb", [])


func has_sequence(image: String, seq: String) -> bool:
	return images.has(image) and images[image].get("sequences", {}).has(seq)


func sequence(image: String, seq: String) -> Dictionary:
	if not images.has(image):
		return {}
	return images[image].get("sequences", {}).get(seq, {})


## First sequence name that exists for the image, in preference order ("" if none).
func pick(image: String, names: Array) -> String:
	for n in names:
		if has_sequence(image, str(n)):
			return str(n)
	return ""


## Number of animation frames per facing block.
func length(image: String, seq: String) -> int:
	var s := sequence(image, seq)
	if s.is_empty():
		return 0
	var table: Array = s.get("frame_table", [])
	if not table.is_empty():
		return (table[0] as Array).size()
	return int(s.get("length", 1))


func facings(image: String, seq: String) -> int:
	return int(sequence(image, seq).get("facings", 1))


## Milliseconds per frame of the sequence (OpenRA Tick, default 40 ms).
func tick_ms(image: String, seq: String) -> float:
	return float(sequence(image, seq).get("tick", TICK_MS))


## Screen heading (radians, 0 = +x, y down) to an OpenRA angle (0..1023, 0 = north, counter-clockwise).
static func wangle(heading: float) -> int:
	return int(posmod(int(round(768.0 - rad_to_deg(heading) * 1024.0 / 360.0)), 1024))


## Util.IndexFacing: step = 1024 / N; block = ((angle + step / 2) & 1023) / step.
static func index_facing(angle: int, n: int) -> int:
	if n <= 1:
		return 0
	var step := 1024 / n
	return ((angle + step / 2) & 1023) / step


## OpenRA.Mods.Cnc.Util.ClassicIndexFacing for 32-facing Red Alert art.
static func classic_index_facing(angle: int, n: int) -> int:
	if n != 32:
		return index_facing(angle, n)
	for i in CLASSIC_RANGES.size():
		if angle < int(CLASSIC_RANGES[i]):
			return i
	return 0


func facing_block(image: String, seq: String, heading: float) -> int:
	var s := sequence(image, seq)
	var n := int(s.get("facings", 1))
	if n <= 1:
		return 0
	var a := wangle(heading)
	var block := classic_index_facing(a, n) if bool(s.get("classic_facings", false)) else index_facing(a, n)
	if bool(s.get("reverse_facings", false)):
		block = (n - block) % n
	return block


## Frame index inside the file for (heading, animation index).
func frame_number(image: String, seq: String, heading: float, anim: int) -> int:
	var s := sequence(image, seq)
	if s.is_empty():
		return -1
	var table: Array = s.get("frame_table", [])
	if table.is_empty():
		return int(s.get("start", 0)) + anim
	var block := clampi(facing_block(image, seq, heading), 0, table.size() - 1)
	var row: Array = table[block]
	if row.is_empty():
		return -1
	return int(row[anim % row.size()])


## Frame index by explicit block and animation index (walls use the adjacency mask as the frame).
func frame_at(image: String, seq: String, block: int, anim: int) -> int:
	var s := sequence(image, seq)
	var table: Array = s.get("frame_table", [])
	if table.is_empty():
		return -1
	var row: Array = table[clampi(block, 0, table.size() - 1)]
	return int(row[clampi(anim, 0, row.size() - 1)]) if not row.is_empty() else -1


func path_for_frame(image: String, seq: String, n: int) -> String:
	if n < 0:
		return ""
	return "res://assets/openra/%s-%04d.png" % [str(sequence(image, seq).get("file", image)), n]


func texture_for(image: String, seq: String, heading: float, anim: int) -> Texture2D:
	var path := path_for_frame(image, seq, frame_number(image, seq, heading, anim))
	return texture(path) if not path.is_empty() else null


func texture_frame(image: String, seq: String, n: int) -> Texture2D:
	var path := path_for_frame(image, seq, n)
	return texture(path) if not path.is_empty() else null


func texture(path: String) -> Texture2D:
	if _textures.has(path):
		return _textures[path]
	var tex: Texture2D = null
	if ResourceLoader.exists(path):
		tex = load(path)
	elif not _missing.has(path):
		_missing[path] = true
		push_warning("missing sprite " + path)
	_textures[path] = tex
	return tex


## Sequence pixel offset (x, y); z is ignored by the 2D renderer.
func offset(image: String, seq: String) -> Vector2:
	var o: Variant = sequence(image, seq).get("offset", [0, 0, 0])
	if typeof(o) == TYPE_ARRAY and o.size() >= 2:
		return Vector2(float(o[0]), float(o[1]))
	return Vector2.ZERO


func flip_x(image: String, seq: String) -> bool:
	return bool(sequence(image, seq).get("flip_x", false))


## Wall frame (OpenRA WithWallSpriteBody.cs lines 62-69): same wall type to the north (0,-1) = 1, east (+1,0) = 2,
## south (0,+1) = 4, west (-1,0) = 8.
static func wall_mask(north: bool, east: bool, south: bool, west: bool) -> int:
	return (1 if north else 0) | (2 if east else 0) | (4 if south else 0) | (8 if west else 0)
