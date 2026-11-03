class_name StoryFxLayer
extends Node2D
## A thin canvas layer that asks StoryFx to draw one pass: "base" (under the crowd), "add" (additive light over it) or "norm"
## (haze, confetti, dimming, vignette).

var fx: StoryFx
var mode := "base"


func _ready() -> void:
	if mode == "add" or mode == "base_add":
		var m := CanvasItemMaterial.new()
		m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
		material = m


func _draw() -> void:
	if fx == null or fx.stage == null:
		return
	match mode:
		"base":
			fx.draw_base(self)
		"base_add":
			fx.draw_base_add(self)
		"add":
			fx.draw_add(self)
		"norm":
			fx.draw_norm(self)
