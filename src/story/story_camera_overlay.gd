class_name StoryCameraOverlay
extends Node2D
## Draws the camera move's own effects over the rooms: the passage frame the camera walks through and the rush of speed lines.

var stage: StoryStage


func _draw() -> void:
	if stage != null:
		stage.draw_camera_overlay(self)
