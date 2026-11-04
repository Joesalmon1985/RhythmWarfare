extends "res://tools/story/preview_chapter.gd"
## Review sheets for the mental_hospital chapter: everything preview_chapter.gd does (chars, close, stage, set, pieces, passage, RW_VIEW=corridor|art_room|courtyard),
## plus its own `interlude` sheets (the underworld one in preview_chapter.gd is chapter specific):
##   RW_PREVIEW=interlude        the fluoro wash, tunnel vignette, flicker tubes and the closed ward door over Night One's club
##   RW_PREVIEW=interlude_flood  the ward door swung open (frame + leaf + open leaf) over the day room, a lit tube above
##   godot --path . -s tools/shoot.gd -- res://tools/story/preview_mh.tscn /tmp/shots 30:shot:name      (RW_CHAPTER defaults to mental_hospital)


func _ready() -> void:
	if not OS.has_environment("RW_CHAPTER"):
		OS.set_environment("RW_CHAPTER", "mental_hospital")
	super._ready()


func _spr(id: String, pos: Vector2, mul := Vector2.ONE, z := 0, mod := Color.WHITE) -> Sprite2D:
	var d: Dictionary = M["interlude"]["sprites"][id]
	var s := Sprite2D.new()
	s.texture = tex(d["file"])
	s.centered = false
	var k := float(d["px_scale"])
	s.scale = Vector2(k, k) * mul
	s.position = pos - Vector2(d["pivot"][0], d["pivot"][1]) * s.scale
	s.modulate = mod
	s.z_as_relative = false
	s.z_index = z
	if d.get("blend", "mix") == "add":
		var mat := CanvasItemMaterial.new()
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		s.material = mat
	add_child(s)
	return s


func _interlude(open := false) -> void:
	var chap_root := ROOT
	var chap: Dictionary = M
	if open:  # the new room: the day room itself (this chapter's main view)
		_stage(true, false, true)
	else:  # the old room: Night One's club
		ROOT = "res://assets/story/night_one/"
		M = JSON.parse_string(FileAccess.get_file_as_string(ROOT + "manifest.json"))
		_tcache.clear()
		_stage(false)
		ROOT = chap_root
		M = chap
		_tcache.clear()
	var A: Dictionary = M["interlude"]["anchors"]
	var dc: Array = A["door_centre"]
	var foot := Vector2(dc[0], dc[1])
	if open:
		# the frame stands in front; the leaf is shown swung open at the left jamb
		_spr("cell_door_frame", foot, Vector2.ONE * 1.0, 2200)
		_spr("cell_door_open", foot + Vector2(-94, 0), Vector2.ONE, 2210)
		_spr("flicker_tube", Vector2(640, 40), Vector2.ONE, 2300, Color(0.8, 1.0, 0.92, 0.9))
		_label("door swung open over the day room", Vector2(10, 4), 14)
		return
	_spr("tunnel_vignette", Vector2(640, 360), Vector2.ONE, 2100, Color(1, 1, 1, 0.9))
	_spr("fluoro_wash", Vector2(640, 360), Vector2.ONE, 2150, Color(1, 1, 1, 0.45))
	for p in A["tube_row"]:
		_spr("flicker_tube", Vector2(p[0], p[1]), Vector2.ONE, 2300, Color(0.8, 1.0, 0.92, 0.95))
	_spr("cell_door", foot, Vector2.ONE, 2200)
	_label("interlude: tunnel vignette, fluoro wash, tubes, ward door over Night One", Vector2(10, 4), 14)
