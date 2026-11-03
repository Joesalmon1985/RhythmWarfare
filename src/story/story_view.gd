class_name StoryView
extends Node2D
## One room of a chapter (the "main" stage or an extra view of a chapter with a moving camera): its static layers, effects passes and
## crowd, in the 1280 x 720 design space. The stage moves, scales and fades these nodes to walk or turn the camera between rooms.

var id := "main"
var assets: StoryAssets
var stage: StoryStage
var fx: StoryFx
var crowd: StoryCrowd
var layers: Dictionary = {}  # layer id -> Sprite2D
var fx_layers: Array = []
var vanish := Vector2(640, 130)  # where a dolly out of this room pushes toward
var palette_hint := ""


func build(p_stage: StoryStage, p_assets: StoryAssets, p_data: StoryData, view_id: String) -> void:
	stage = p_stage
	assets = p_assets
	id = view_id
	name = "View_" + id
	var v: Dictionary = assets.view(id)
	palette_hint = str(v.get("palette_hint", ""))
	var vp: Array = assets.anchor("vanish", [640, 130], id)
	vanish = Vector2(float(vp[0]), float(vp[1]))
	var front: Array = []
	for l in assets.view_layers(id):
		var tex := assets.texture(str(l.get("file", "")))
		if tex == null:
			continue
		var sp := Sprite2D.new()
		sp.name = str(l["id"])
		sp.centered = false
		sp.texture = tex
		var size: Array = l.get("size", [tex.get_width(), tex.get_height()])
		sp.position = Vector2(float(l["pos"][0]), float(l["pos"][1]))
		sp.scale = Vector2(float(size[0]) / tex.get_width(), float(size[1]) / tex.get_height())
		if id == "main" and str(l["id"]) == "desk_top":
			continue  # the pad strip draws the desk
		layers[str(l["id"])] = sp
		if str(l.get("z", "behind")) == "front":
			front.append(sp)
		else:
			add_child(sp)
	fx = StoryFx.new()
	fx.stage = stage
	fx.view = id
	fx.setup(assets)
	_add_fx("base")
	_add_fx("base_add")
	crowd = StoryCrowd.new()
	crowd.name = "Crowd"
	crowd.view = id
	crowd.bpm = stage.bpm
	add_child(crowd)
	crowd.glow_colors = stage.glow_colors()
	crowd.setup(assets, p_data)
	fx.crowd = crowd
	for sp in front:
		add_child(sp)
	_add_fx("add")
	_add_fx("norm")


func _add_fx(mode: String) -> void:
	var l := StoryFxLayer.new()
	l.name = "Fx_" + mode
	l.fx = fx
	l.mode = mode
	add_child(l)
	fx_layers.append(l)


func redraw_fx() -> void:
	for l in fx_layers:
		l.queue_redraw()


func reset() -> void:
	crowd.reset()
	fx.reset()
	if layers.has("riser"):
		(layers["riser"] as Sprite2D).visible = false
