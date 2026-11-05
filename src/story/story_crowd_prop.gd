class_name StoryCrowdProp
extends Node2D
## A flat thing standing in the crowd's overlay in the 2.5D world: a rear-row silhouette or an occluder (a speaker stack, a door frame). The crowd places it
## from the projector each frame and sorts it with the dancers by distance, so a stack nearer than a dancer draws over them. `items` is a list of
## [Texture2D, Rect2, Color] drawn as they are (feet-origin coordinates).

var items: Array = []
var kind := "occluder"  # "occluder" or "silhouette"
var depth := 0.0  # metres along the view axis (the crowd's sort key)
var sector := ""
var drawer := Callable()  # (prop) -> void: draws it instead of `items` (the run's animated card table, src/run/run_card_table.gd)


func _draw() -> void:
	if drawer.is_valid():
		drawer.call(self)
		return
	for it in items:
		draw_texture_rect(it[0], it[1], false, it[2])
