extends "res://tools/story/preview_art.gd"
## Review sheets for the mothership's extra views (stage.views) with the crowd rig and the view's own pieces.
##   RW_VIEW    = main (default) | gallery | reactor | bridge        which room to compose
##   RW_PREVIEW = stage (crowd, beams, pieces) | stage_low | set (bare room) | pieces (piece sheet) | passage (passage_frame at 2x over the room)
##   godot --path . -s tools/shoot.gd -- res://tools/story/preview_views.tscn /tmp/shots 30:shot:name   (see tools/story/shoot_views.sh)

var _applied := false
var _front: Array = []


func _ready() -> void:
	if not OS.has_environment("RW_CHAPTER"):
		OS.set_environment("RW_CHAPTER", "mothership")
	if not OS.has_environment("RW_PREVIEW"):
		OS.set_environment("RW_PREVIEW", "stage")
	if OS.get_environment("RW_PREVIEW") == "passage":
		OS.set_environment("RW_PREVIEW", "set")
		_passage = true
	super._ready()


var _passage := false


func _apply_view() -> void:
	if _applied:
		return
	_applied = true
	var id := OS.get_environment("RW_VIEW") if OS.has_environment("RW_VIEW") else "main"
	if id == "main":
		return
	var st: Dictionary = M["stage"]
	var view: Dictionary = {}
	for v in st["views"]:
		if v["id"] == id:
			view = v
	if view.is_empty():
		push_error("no view " + id)
		return
	var ns: Dictionary = st.duplicate(true)
	var layers: Array = []
	for L in view["layers"]:
		if L.get("z", "behind") == "front":
			_front.append(L)
		else:
			layers.append(L)
	for L in st["layers"]:
		if L["id"] == "desk_top":
			layers.append(L)
	ns["layers"] = layers
	var A: Dictionary = st["anchors"].duplicate(true)
	A["woofers"] = []
	for k in view["anchors"]:
		A[k] = view["anchors"][k]
	ns["anchors"] = A
	ns["pieces"] = view["pieces"]
	ns["sprites"].erase("door_open")
	M["stage"] = ns
	print("view ", id, " layers ", layers.size(), " front ", _front.size(), " pieces ", ns["pieces"].size())


func _stage(low: bool, deck_only := false, empty := false) -> void:
	_apply_view()
	super._stage(low, deck_only, empty)
	for L in _front:
		var s := Sprite2D.new()
		s.texture = tex(L["file"])
		s.centered = false
		s.position = Vector2(L["pos"][0], L["pos"][1])
		s.scale = Vector2(L["size"][0] / s.texture.get_width(), L["size"][1] / s.texture.get_height())
		s.z_as_relative = false
		s.z_index = 1600
		add_child(s)
	if _passage:
		var d: Dictionary = M["stage"]["sprites"]["passage_frame"]
		var s := Sprite2D.new()
		s.texture = tex(d["file"])
		s.centered = false
		var k := float(d["px_scale"]) * 2.0
		s.scale = Vector2(k, k)
		s.position = Vector2(640, 360) - Vector2(d["pivot"][0], d["pivot"][1]) * k
		s.z_as_relative = false
		s.z_index = 3000
		add_child(s)


func _pieces(where: String) -> void:
	for p in M.get("stage", {}).get("pieces", []):
		if p["z"] != where:
			continue
		var s := _piece_sprite(p, p.get("blend", "") == "add")
		s.z_index = -2450 if where == "behind" else 1700
		add_child(s)


func _pieces_sheet() -> void:
	_apply_view()
	var x := 10.0
	var y := 20.0
	var rowh := 0.0
	for p in M["stage"]["pieces"]:
		var k := float(p["px_scale"])
		var sz := Vector2(p["size"][0], p["size"][1])
		if x + sz.x > 1270:
			x = 10.0
			y += rowh + 30
			rowh = 0.0
		var back := ColorRect.new()
		back.color = Color(0.05, 0.03, 0.1)
		back.position = Vector2(x, y)
		back.size = sz
		back.z_index = -3000
		back.z_as_relative = false
		add_child(back)
		var s := _piece_sprite(p, p.get("blend", "") == "add")
		s.position = Vector2(x, y)
		s.z_index = 0
		add_child(s)
		_label("%s (%s, %s, %s)" % [p["id"], p["anim"], p["z"], p.get("blend", "mix")], Vector2(x, y + sz.y + 2), 12)
		x += sz.x + 16
		rowh = maxf(rowh, sz.y)
