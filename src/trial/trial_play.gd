extends Control
## Launch straight into the Bassment: the dungeon now lives inside the run scene (src/run/run_play.gd hosts src/trial/trial_scene.gd), so this scene only asks for it and hands over.
## RW_TRIAL_START, RW_TRIAL_BOT, RW_TRIAL_CHOICES, RW_TRIAL_UNTIL and RW_TRIAL_VIRTUAL still work (docs/TRIAL_OPENING.md).


func _ready() -> void:
	Session.trial_direct = true
	if OS.get_environment("RW_TRIAL_VIRTUAL") == "1":
		OS.set_environment("RW_RUN_VIRTUAL", "1")
	get_tree().change_scene_to_file.call_deferred("res://src/run/run_play.tscn")
