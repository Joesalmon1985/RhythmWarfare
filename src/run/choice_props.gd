class_name ChoiceProps
extends Node3D
## The choice layer's props in the world (docs/CHOICE_CLARITY.md): billboards from assets/run/choice stood at an option's anchor with depth like the map's things (a door that
## swings open or shut, two boards across a doorway, a round green or square red lamp, a spill of light on the floor, any prop a `states` step names). HotspotView owns one per
## stage, adds it under the stage's StoryWorld and sets every prop each frame from ChoiceStaging; a prop not set in a frame is hidden.

const DOOR_FRAMES := 4

var _nodes: Dictionary = {}  # key -> {node: MeshInstance3D, mat, size: Vector2}
var _seen: Dictionary = {}
static var _tex: Dictionary = {}


static func tex(name: String) -> Texture2D:
	if not _tex.has(name):
		var p := ChoiceStaging.ART_DIR + name + ".png"
		_tex[name] = load(p) if ResourceLoader.exists(p) else null
	return _tex[name]


func begin_frame() -> void:
	_seen = {}


func end_frame() -> void:
	for k in _nodes:
		if not _seen.has(k):
			(_nodes[k]["node"] as MeshInstance3D).visible = false


## Stand prop `key` (a name unique in the stage) with texture `tex_name`, its bottom centre at `foot` (world), `height` metres tall; `ground`: a flat quad on the floor instead of a
## standing billboard; `light`: brightness (1 lit by itself, a lamp; under 1 a thing in the room's light); `alpha` 0..1.
func put(key: String, tex_name: String, foot: Vector3, height: float, light := 0.85, alpha := 1.0, ground := false) -> void:
	var t := tex(tex_name)
	if t == null:
		return
	_seen[key] = true
	var rec: Dictionary = _nodes.get(key, {})
	var w := height * float(t.get_width()) / float(t.get_height())
	if rec.is_empty() or (rec["ground"] as bool) != ground:
		if not rec.is_empty():
			(rec["node"] as Node).queue_free()
		var q := QuadMesh.new()
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		if ground:
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
			mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
		else:
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
			mat.alpha_scissor_threshold = 0.5
			mat.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
		var mi := MeshInstance3D.new()
		mi.name = "Choice_" + key.replace(".", "_")
		mi.mesh = q
		mi.material_override = mat
		if ground:
			mi.rotation = Vector3(-PI * 0.5, 0.0, 0.0)
		add_child(mi)
		rec = {"node": mi, "mat": mat, "ground": ground}
		_nodes[key] = rec
	var mi2: MeshInstance3D = rec["node"]
	var mat2: StandardMaterial3D = rec["mat"]
	(mi2.mesh as QuadMesh).size = Vector2(w, height)
	mat2.albedo_texture = t
	mat2.albedo_color = Color(light, light, light, alpha)
	mi2.position = foot + (Vector3(0.0, 0.02, 0.0) if ground else Vector3(0.0, height * 0.5, 0.0))
	mi2.visible = alpha > 0.01


## The door frame for an opening amount 0..1: door_0 (shut) .. door_3 (wide).
static func door_frame(open_k: float) -> String:
	return "door_%d" % clampi(int(round(open_k * float(DOOR_FRAMES - 1))), 0, DOOR_FRAMES - 1)


func shown_keys() -> Array:
	var out: Array = []
	for k in _nodes:
		if (_nodes[k]["node"] as MeshInstance3D).visible:
			out.append(k)
	return out


func frame_of(key: String) -> String:
	if not _nodes.has(key):
		return ""
	var t: Texture2D = (_nodes[key]["mat"] as StandardMaterial3D).albedo_texture
	return t.resource_path.get_file().get_basename() if t != null else ""
