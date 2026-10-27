extends Control
## Result screen: outcome, accuracy, misses, best combo and battle duration. Retry resets everything.


func _ready() -> void:
	var r := Session.last_result
	var outcome := str(r.get("outcome", "incomplete"))
	$Box/Outcome.text = {"victory": "VICTORY", "defeat": "DEFEAT"}.get(outcome, "SONG COMPLETE")
	$Box/Title.text = str(r.get("level", ""))
	var rewards: Dictionary = r.get("rewards", {})
	$Box/Stats.text = "Accuracy %.1f%%  (%d notes judged)\nPerfect %d   Good %d   Misses %d   Stray %d\nBest combo %d\nTanks %d   Infantry %d   Air actions %d\nDuration %d:%02d" % [
		float(r.get("accuracy", 0.0)) * 100.0, int(r.get("judged", 0)),
		int(r.get("perfect", 0)), int(r.get("good", 0)), int(r.get("misses", 0)), int(r.get("strays", 0)),
		int(r.get("best_combo", 0)),
		int(rewards.get("kick", 0)), int(rewards.get("snare", 0)) * 5, int(rewards.get("bass", 0)),
		int(r.get("duration_s", 0.0)) / 60, int(r.get("duration_s", 0.0)) % 60]
	$Box/Retry.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://src/scenes/play.tscn"))
	$Box/Menu.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	$Box/Retry.grab_focus()
